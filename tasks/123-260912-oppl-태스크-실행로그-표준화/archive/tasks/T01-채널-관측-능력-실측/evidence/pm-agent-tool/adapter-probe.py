#!/usr/bin/env python3
"""pm-agent-tool 축 관측 프로브 (Phase 0 실측용, 읽기·계측 전용).

플랫폼 Agent 도구 호출은 호출측이 프로세스를 감쌀 수 없다. 대신 하네스가 직접 기록하는
세션 산출물(모델이 쓰지 않는 파일)을 외부 프로세스에서 폴링해 아래 4항목을 수집한다.
  1) 시작 식별자   : subagents/agent-<id>.meta.json 의 toolUseId/agentId (하네스 기록)
  2) 중간 사건     : subagents/agent-<id>.jsonl 의 증분 append (완료 알림 이전 수신분)
  3) 종료 봉투     : 호출자 트랜스크립트의 <task-notification> + tasks/<id>.output
  4) 단조 시계 구간: 프로브 자신의 time.monotonic() 차분 (벽시계 차분 아님)
읽기 전용이다. 자기 증거 파일 외에는 아무것도 쓰지 않는다.

usage: adapter-probe.py <out_prefix> <session_dir> <caller_jsonl> <limit_sec> <tasks_dir>
"""
import hashlib, json, os, re, sys, time, datetime, glob


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(65536), b''):
            h.update(c)
    return h.hexdigest()


def main():
    out, sess_dir, caller_jsonl, limit, tasks_dir = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]), sys.argv[5]
    sub = os.path.join(sess_dir, 'subagents')
    baseline = set(glob.glob(os.path.join(sub, '*')))       # 실험 전 이미 있던 파일 = 관측 대상 아님
    base_caller_size = os.path.getsize(caller_jsonl) if os.path.exists(caller_jsonl) else 0
    t0 = time.monotonic()
    start_events, growth, watched, last_n, terminal = [], [], set(), {}, None

    while time.monotonic() - t0 < limit and terminal is None:
        for p in sorted(set(glob.glob(os.path.join(sub, '*'))) - baseline):
            off = round((time.monotonic() - t0) * 1000, 3)
            rec = {'monotonic_offset_ms': off, 'observed_at': utc(), 'kind': 'new_file',
                   'path': os.path.basename(p), 'size': os.path.getsize(p)}
            if p.endswith('.meta.json'):
                try:
                    rec['content'] = json.load(open(p))
                except Exception as e:
                    rec['error'] = str(e)
            if p.endswith('.jsonl'):
                watched.add(p)
            start_events.append(rec)
            baseline.add(p)

        for p in sorted(watched):                            # 새로 생긴 서브에이전트 트랜스크립트만 추적
            try:
                n = sum(1 for _ in open(p, errors='ignore'))
                size = os.path.getsize(p)
            except Exception:
                continue
            if last_n.get(p) != n:
                last_n[p] = n
                growth.append({'monotonic_offset_ms': round((time.monotonic() - t0) * 1000, 3),
                               'observed_at': utc(), 'file': os.path.basename(p),
                               'line_count': n, 'size': size})

        if os.path.exists(caller_jsonl) and os.path.getsize(caller_jsonl) > base_caller_size:
            with open(caller_jsonl, errors='ignore') as f:
                f.seek(base_caller_size)
                chunk = f.read()
            # 관측한 서브에이전트의 식별자 집합 (agentId는 파일명, toolUseId는 meta 본문)
            ids = set()
            for e in start_events:
                m = re.match(r'agent-([0-9a-f]+)\.', e.get('path', ''))
                if m:
                    ids.add(m.group(1))
                tu = (e.get('content') or {}).get('toolUseId')
                if tu:
                    ids.add(tu)
            hit = None
            for m in re.finditer(r'<task-notification>', chunk):
                cand = chunk[m.start():][:1500]
                tid = re.search(r'<task-id>([^<]+)</task-id>', cand)
                tui = re.search(r'<tool-use-id>([^<]+)</tool-use-id>', cand)
                # 배경 Bash 알림 오탐 배제: 관측한 서브에이전트 식별자와 일치할 때만 인정
                if (tid and tid.group(1) in ids) or (tui and tui.group(1) in ids):
                    hit = cand
                    break
            if hit:
                snippet = hit
                terminal = {'monotonic_offset_ms': round((time.monotonic() - t0) * 1000, 3),
                            'observed_at': utc(), 'source_kind': 'task_notification',
                            'raw_snippet': snippet,
                            'snippet_sha256': hashlib.sha256(snippet.encode()).hexdigest(),
                            'output_files': [{'name': os.path.basename(x), 'size': os.path.getsize(x),
                                              'sha256': sha_file(x)}
                                             for x in glob.glob(os.path.join(tasks_dir, '*.output'))
                                             if os.path.getmtime(x) > time.time() - limit - 60]}
        time.sleep(0.25)

    t1 = time.monotonic()
    cut = terminal['monotonic_offset_ms'] if terminal else float('inf')
    meta = {'probe_version': '1.0', 'channel_id': 'pm-agent-tool',
            'watch': {'subagents_dir': sub, 'caller_transcript': caller_jsonl, 'tasks_dir': tasks_dir},
            'start_events': start_events, 'intermediate_growth': growth, 'terminal': terminal,
            'monotonic_span': {'duration_ms': round((t1 - t0) * 1000, 3),
                               'duration_source': 'adapter_monotonic', 'clock': 'time.monotonic'},
            'counts': {'new_files': len(start_events), 'growth_samples': len(growth),
                       'growth_before_terminal': len([g for g in growth if g['monotonic_offset_ms'] < cut])}}
    json.dump(meta, open(out + '.probe.json', 'w'), ensure_ascii=False, indent=2)
    print(json.dumps(meta['counts']))


if __name__ == '__main__':
    sys.exit(main())
