#!/usr/bin/env python3
"""OPD2 artifact gates. Python standard library only; no model verdicts fabricated."""
import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
STAGES = ('INTENT', 'DESIGN', 'PLAN', 'BUILD', 'VERIFY', 'REVIEW', 'RELEASE', 'OBSERVE', 'CLOSED')
ARTIFACTS = {'INTENT': 'intent', 'DESIGN': 'spec', 'PLAN': 'plan'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def stamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False).encode()


def read(path):
    return json.loads(Path(path).read_text())


def atomic(path, value):
    path = Path(path)
    fd, temp = tempfile.mkstemp(prefix='.opd2-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as out:
            out.write(value)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def validate(value, schema, at='$'):
    """Closed subset used by our schemas; unknown validation keywords fail closed."""
    supported = {'$schema', 'title', 'description', 'type', 'required', 'properties',
                 'additionalProperties', 'items', 'minItems', 'minLength', 'enum', 'minimum'}
    require(not set(schema) - supported, f'unsupported schema keyword: {set(schema) - supported}')
    types = {'object': dict, 'array': list, 'string': str, 'integer': int, 'boolean': bool}
    if 'type' in schema:
        require(type(value) is types[schema['type']], f'{at}: expected {schema["type"]}')
    if 'enum' in schema:
        require(value in schema['enum'], f'{at}: unsupported value')
    if isinstance(value, dict):
        require(set(schema.get('required', [])) <= value.keys(), f'{at}: missing required fields')
        props = schema.get('properties', {})
        if schema.get('additionalProperties') is False:
            require(not value.keys() - props.keys(), f'{at}: unknown fields')
        for key, item in value.items():
            if key in props:
                validate(item, props[key], f'{at}.{key}')
    if isinstance(value, list):
        require(len(value) >= schema.get('minItems', 0), f'{at}: too few items')
        for i, item in enumerate(value):
            validate(item, schema.get('items', {}), f'{at}[{i}]')
    if isinstance(value, str):
        require(len(value.strip()) >= schema.get('minLength', 0), f'{at}: empty value')
    if type(value) is int and 'minimum' in schema:
        require(value >= schema['minimum'], f'{at}: below minimum')


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.PIPE)


def snapshot(repo, task):
    """All Git-visible tracked/untracked files, including modes; task artifacts excluded."""
    result = {}
    for raw in git(repo, 'ls-files', '-z', '--cached', '--others', '--exclude-standard').split(b'\0'):
        if not raw:
            continue
        name = os.fsdecode(raw)
        path = Path(repo) / name
        if path.is_relative_to(task):
            continue
        if path.is_symlink():
            value = ('symlink:' + os.readlink(path)).encode()
        elif path.is_file():
            value = str(path.stat().st_mode & 0o777).encode() + b':' + path.read_bytes()
        elif not path.exists():
            value = b'deleted'
        else:
            raise ValueError(f'unsupported repository entry (submodule?): {name}')
        result[name] = digest(value)
    return result


class Store:
    def __init__(self, task):
        self.task = Path(task).resolve()
        self.home = self.task / '.sdlc'

    @contextlib.contextmanager
    def lock(self, create=False):
        if create:
            self.home.mkdir(parents=True, exist_ok=True)
        require(self.home.is_dir(), 'task not initialized')
        with (self.home / 'lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            yield

    def events(self):
        path = self.home / 'events.jsonl'
        events = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
        previous = ''
        for index, event in enumerate(events):
            body = {k: v for k, v in event.items() if k != 'hash'}
            require(event['seq'] == index + 1 and event['previous'] == previous
                    and event['hash'] == digest(encoded(body)), 'journal integrity failure')
            previous = event['hash']
        return events

    def state(self):
        events = self.events()
        require(events, 'task not initialized')
        return events[-1]['state']

    def save(self, state, kind, detail):
        events = self.events()
        event = {'seq': len(events) + 1, 'previous': events[-1]['hash'] if events else '',
                 'time': stamp(), 'kind': kind, 'detail': detail, 'state': state}
        event['hash'] = digest(encoded(event))
        events.append(event)
        # One authoritative atomic journal. Snapshot can be rebuilt after a crash.
        atomic(self.home / 'events.jsonl', ''.join(json.dumps(e, ensure_ascii=False) + '\n' for e in events))
        atomic(self.home / 'state.json', json.dumps(state, ensure_ascii=False, indent=2))
        atomic(self.task / 'STATE.md', f'# OPD2 {state["change_id"]}\n\n'
               f'- Stage: {state["stage"]}\n- Mode: {state["mode"]}\n'
               f'- Workspace: {state["workspace"]}\n- Blocked: {state["blocked"] or "none"}\n'
               f'- Evidence runs: {len(state["evidence"])}\n- Rework: {state["retries"]}/3\n'
               '\nSource: .sdlc/events.jsonl (this page is a projection).\n')
        if state['mode'] == 'agentic' or STAGES.index(state['stage']) >= STAGES.index('BUILD'):
            lines = ['# AGENTIC-LOG\n', f'Events: {len(events)}; mode: {state["mode"]}\n',
                     '| # | Time | Event | Detail |', '|---|---|---|---|']
            for item in events:
                detail = json.dumps(item['detail'], ensure_ascii=False).replace('|', '\\|').replace('\n', ' ')
                lines.append(f'| {item["seq"]} | {item["time"]} | {item["kind"]} | {detail} |')
            atomic(self.task / 'AGENTIC-LOG.md', '\n'.join(lines) + '\n')
        return state

    def current_tree(self, state):
        return snapshot(state['repo'], self.task)

    def artifact(self, name):
        doc = self.task / f'{name}.md'
        data = self.task / f'{name}.json'
        require(doc.is_file() and len(doc.read_text().strip()) > 20, f'missing {name}.md')
        value = read(data)
        validate(value, read(ROOT / 'schemas' / f'{name}.schema.json'))
        return value, digest(doc.read_bytes() + b'\0' + encoded(value))

    def chain(self, state):
        for name, expected in state['artifacts'].items():
            require(self.artifact(name)[1] == expected, f'stale artifact: {name}; rewind first')

    def fingerprint(self, state):
        self.chain(state)
        artifacts = dict(state['artifacts'])
        if state['stage'] == 'PLAN':
            artifacts['plan'] = self.artifact('plan')[1]
        return digest(encoded({'tree': self.current_tree(state), 'artifacts': artifacts}))

    def scope(self, state):
        plan, _ = self.artifact('plan')
        current = self.current_tree(state)
        changes = sorted(k for k in state['baseline'].keys() | current.keys()
                         if state['baseline'].get(k) != current.get(k))
        allowed = plan['files']
        for path in allowed:
            require(not Path(path).is_absolute() and '..' not in Path(path).parts and path not in ('', '.'),
                    'scope paths must be exact repository-relative file paths')
        require(not set(changes) - set(allowed), f'scope violation: {sorted(set(changes) - set(allowed))}')
        for name, expected in state.get('protected_tests', {}).items():
            require(current.get(name) == expected, f'protected test changed: {name}')
        return changes

    def approvals(self, state, gate, fingerprint):
        return any(x['gate'] == gate and x['fingerprint'] == fingerprint for x in state['approvals'])

    def evidence(self, state, role):
        plan, _ = self.artifact('plan')
        expected = self.fingerprint(state)
        matches = [e for e in state['evidence'] if e['role'] == role and e['fingerprint'] == expected]
        for command in plan['checks']:
            rows = [e for e in matches if e['argv'] == command]
            require(rows, f'missing successful {role} evidence for {command}')
            row = rows[-1]
            require(row['exit_code'] == 0 and row['stable'], f'latest {role} check failed or changed source')
            log = self.home / row['log']
            require(log.is_file() and digest(log.read_bytes()) == row['log_sha256'], 'evidence log changed')
        return matches

    def advance(self, actor):
        state = self.state()
        require(not state['blocked'], f'blocked: {state["blocked"]}')
        require(state['stage'] != 'CLOSED', 'already closed')
        self.chain(state)
        stage = state['stage']
        if stage in ARTIFACTS:
            name = ARTIFACTS[stage]
            artifact, checksum = self.artifact(name)
            require(artifact['change_id'] == state['change_id'], 'change ID mismatch')
            upstream = {'spec': 'intent', 'plan': 'spec'}.get(name)
            if upstream:
                require(artifact['source_sha256'] == state['artifacts'][upstream], 'source hash mismatch')
                previous, _ = self.artifact(upstream)
                require(previous['risk'] != 'high' or artifact['risk'] == 'high', 'risk downgrade requires new intent')
            require(not artifact['open_questions'], 'unresolved questions')
            if name == 'plan':
                self.scope(state)
                require(artifact['builder'] != artifact['verifier'], 'builder and verifier must differ')
                require(artifact['builder'] != artifact['reviewer'], 'builder and reviewer must differ')
                for check in artifact.get('red_checks', []):
                    entries = [e for e in state['evidence'] if e['role'] == 'red'
                               and e['fingerprint'] == self.fingerprint(state) and e['argv'] == check['argv']]
                    require(entries and entries[-1]['stable'] and entries[-1]['exit_code'] == check['exit_code'],
                            'RED evidence required with expected failure exit')
                    log = self.home / entries[-1]['log']
                    require(log.is_file() and digest(log.read_bytes()) == entries[-1]['log_sha256'], 'RED log changed')
                current = self.current_tree(state)
                state['protected_tests'] = {}
                for path in artifact.get('protected_tests', []):
                    require(path in current, f'protected test missing: {path}')
                    state['protected_tests'][path] = current[path]
            if state['mode'] == 'semi-agentic' or artifact['risk'] == 'high':
                require(self.approvals(state, stage, checksum), 'await_user: artifact approval required')
            state['artifacts'][name] = checksum
        if stage in ('BUILD', 'VERIFY', 'REVIEW', 'RELEASE', 'OBSERVE'):
            self.scope(state)
        if stage == 'BUILD':
            self.evidence(state, 'builder')
        if stage == 'VERIFY':
            self.evidence(state, 'verifier')
        if stage == 'REVIEW':
            self.evidence(state, 'builder')
            self.evidence(state, 'verifier')
            fp = self.fingerprint(state)
            reviews = [r for r in state['reviews'] if r['fingerprint'] == fp]
            require(reviews and reviews[-1]['verdict'] == 'pass', 'latest independent review must pass')
            if state['delivery'] == 'release':
                require(self.approvals(state, 'RELEASE', fp), 'await_user: release approval required')
        if stage in ('RELEASE', 'OBSERVE'):
            fp = self.fingerprint(state)
            kind = 'deployment' if stage == 'RELEASE' else 'observation'
            rows = [e for e in state['evidence'] if e['role'] == kind and e['fingerprint'] == fp]
            require(rows and rows[-1]['exit_code'] == 0 and rows[-1]['stable'], f'{kind} execution evidence required')
            log = self.home / rows[-1]['log']
            require(log.is_file() and digest(log.read_bytes()) == rows[-1]['log_sha256'], 'evidence log changed')
            require(self.approvals(state, stage, fp), f'await_user: {stage} signoff required')
        if (stage == 'REVIEW' and state['delivery'] == 'build') or stage == 'OBSERVE':
            require((self.task / 'DONE.md').is_file(), 'DONE.md required')
            state['stage'] = 'CLOSED'
            state['outcome'] = 'ready_for_merge' if state['delivery'] == 'build' else 'observed'
        else:
            state['stage'] = STAGES[STAGES.index(stage) + 1]
        return self.save(state, 'transition', {'from': stage, 'to': state['stage'], 'actor': actor})


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['init', 'status', 'transition', 'validate-artifacts', 'verify-scope',
                                     'collect-evidence', 'approve', 'review', 'block', 'unblock', 'rewind', 'set-mode'])
    p.add_argument('task', type=Path)
    p.add_argument('--repo', type=Path)
    p.add_argument('--change-id')
    p.add_argument('--mode', choices=['semi-agentic', 'agentic'])
    p.add_argument('--workspace', choices=['hub', 'worktree'], default='worktree')
    p.add_argument('--worktree-receipt', type=Path)
    p.add_argument('--delivery', choices=['build', 'release'], default='build')
    p.add_argument('--actor', default='coordinator')
    p.add_argument('--gate', choices=list(STAGES))
    p.add_argument('--role', choices=['red', 'builder', 'verifier', 'deployment', 'observation'])
    p.add_argument('--argv', help='JSON array, executed without a shell')
    p.add_argument('--timeout', type=int, default=120)
    p.add_argument('--reason')
    p.add_argument('--reference', help='Actual user approval message or protected-system approval ID')
    p.add_argument('--verdict', choices=['pass', 'fail'])
    a = p.parse_args(argv)
    store = Store(a.task)
    try:
        with store.lock(create=a.command == 'init'):
            if a.command == 'init':
                require(not store.events(), 'already initialized')
                require(a.repo and a.change_id, '--repo and --change-id required')
                repo = a.repo.resolve()
                require(Path(os.fsdecode(git(repo, 'rev-parse', '--show-toplevel')).strip()).resolve() == repo,
                        '--repo must be Git root')
                require(store.task != repo and store.task.is_relative_to(repo), 'task must be inside repository')
                receipt = None
                if a.workspace == 'worktree':
                    require(a.worktree_receipt, 'worktree receipt required; no hub fallback')
                    receipt = read(a.worktree_receipt)
                    require(receipt.get('ok') is True and receipt.get('command') in ('create', 'status'), 'bad receipt')
                    require(Path(receipt['task_path']).resolve() == store.task
                            and Path(receipt['worktree_root']).resolve() == repo, 'receipt path mismatch')
                    require(git(repo, 'rev-parse', '--git-dir') != git(repo, 'rev-parse', '--git-common-dir'),
                            'linked worktree required')
                state = {'version': 1, 'skill': 'opd2', 'change_id': a.change_id, 'mode': a.mode or 'agentic',
                         'workspace': a.workspace, 'repo': str(repo), 'delivery': a.delivery, 'stage': 'INTENT',
                         'worktree_receipt': receipt, 'baseline': snapshot(repo, store.task), 'artifacts': {},
                         'approvals': [], 'evidence': [], 'reviews': [], 'retries': 0, 'blocked': None}
                result = store.save(state, 'init', {'actor': a.actor})
            else:
                state = store.state()
                if a.command == 'status':
                    result = state
                elif a.command == 'transition':
                    result = store.advance(a.actor)
                elif a.command == 'validate-artifacts':
                    store.chain(state)
                    result = {name: store.artifact(name)[1] for name in ('intent', 'spec', 'plan')
                              if (store.task / f'{name}.json').exists()}
                elif a.command == 'verify-scope':
                    result = {'changed_files': store.scope(state)}
                elif a.command == 'approve':
                    require(a.reference and a.gate, 'approval reference and gate required')
                    require(a.actor not in ('coordinator', 'builder', 'verifier', 'reviewer'), 'named human approver required')
                    fp = store.artifact(ARTIFACTS[a.gate])[1] if a.gate in ARTIFACTS else store.fingerprint(state)
                    state['approvals'].append({'gate': a.gate, 'fingerprint': fp, 'actor': a.actor,
                                               'reference': a.reference, 'time': stamp()})
                    result = store.save(state, 'approval', state['approvals'][-1])
                elif a.command == 'review':
                    require(state['stage'] == 'REVIEW' and a.verdict and a.reason, 'review stage/verdict/reason required')
                    plan, _ = store.artifact('plan')
                    require(a.actor == plan['reviewer'] and a.actor != plan['builder'], 'reviewer identity mismatch')
                    report = {'actor': a.actor, 'verdict': a.verdict, 'reason': a.reason,
                              'fingerprint': store.fingerprint(state)}
                    state['reviews'].append(report)
                    result = store.save(state, 'review', report)
                elif a.command == 'collect-evidence':
                    require(a.role and a.argv and 0 < a.timeout <= 3600, 'role/argv and bounded timeout required')
                    allowed = {'red': 'PLAN', 'builder': 'BUILD', 'verifier': 'VERIFY', 'deployment': 'RELEASE', 'observation': 'OBSERVE'}
                    require(state['stage'] == allowed[a.role] and not state['blocked'], 'wrong stage or blocked')
                    command = json.loads(a.argv)
                    require(isinstance(command, list) and command and all(isinstance(x, str) for x in command), 'argv array required')
                    plan, _ = store.artifact('plan')
                    if a.role == 'red':
                        require(a.actor == plan['verifier'], 'RED must be observed by verifier')
                        require(command in [c['argv'] for c in plan.get('red_checks', [])], 'RED command not in plan')
                    elif a.role in ('builder', 'verifier'):
                        require(a.actor == plan[a.role], 'evidence actor mismatch')
                        require(command in plan['checks'], 'command not in approved plan')
                    else:
                        require(store.approvals(state, state['stage'], store.fingerprint(state)), 'approval required before external command')
                    before = store.fingerprint(state)
                    store.scope(state)
                    try:
                        run = subprocess.run(command, cwd=state['repo'], capture_output=True,
                                             timeout=a.timeout, check=False)
                        code, output = run.returncode, run.stdout + b'\n--- stderr ---\n' + run.stderr
                    except subprocess.TimeoutExpired as exc:
                        code, output = 124, (exc.stdout or b'') + (exc.stderr or b'') + b'\nTIMEOUT'
                    after = store.fingerprint(state)
                    log = f'evidence-{len(state["evidence"]) + 1}.log'
                    (store.home / log).write_bytes(output)
                    entry = {'role': a.role, 'actor': a.actor, 'argv': command, 'exit_code': code,
                             'fingerprint': after, 'stable': before == after, 'log': log,
                             'log_sha256': digest(output), 'time': stamp()}
                    validate(entry, read(ROOT / 'schemas/evidence.schema.json'))
                    state['evidence'].append(entry)
                    result = store.save(state, 'evidence', entry)
                elif a.command in ('block', 'unblock', 'rewind', 'set-mode'):
                    require(a.reason, 'reason required')
                    if a.command == 'block':
                        state['blocked'] = a.reason
                    elif a.command == 'unblock':
                        require(a.reference, 'resolution reference required')
                        state['blocked'] = None
                    elif a.command == 'set-mode':
                        require(a.mode and a.reference, 'explicit mode and user reference required')
                        state['mode'] = a.mode
                    else:
                        require(a.gate in ('INTENT', 'DESIGN', 'PLAN', 'BUILD'), 'rewind target required')
                        require(STAGES.index(a.gate) <= STAGES.index(state['stage']), 'cannot skip forward')
                        state['retries'] += 1
                        require(state['retries'] <= 3, 'retry limit: new user decision required')
                        for stage, name in ARTIFACTS.items():
                            if STAGES.index(stage) >= STAGES.index(a.gate):
                                state['artifacts'].pop(name, None)
                        state.update(stage=a.gate, evidence=[], reviews=[], approvals=[], blocked=None)
                        state.pop('outcome', None)
                        if a.gate != 'BUILD':
                            state.pop('protected_tests', None)
                    result = store.save(state, a.command, {'actor': a.actor, 'reason': a.reason, 'reference': a.reference})
            current = store.state()
            action = 'complete' if current['stage'] == 'CLOSED' else 'blocked' if current['blocked'] else 'continue'
            print(json.dumps({'ok': True, 'result': result, 'transition_action': action,
                              'report_type': 'decision_request' if action == 'blocked' else 'progress_report',
                              'next_action': current['stage']}, ensure_ascii=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        action = 'await_user' if 'await_user' in str(exc) else 'blocked'
        print(json.dumps({'ok': False, 'error': str(exc), 'transition_action': action,
                          'report_type': 'decision_request'}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    sys.exit(main())
