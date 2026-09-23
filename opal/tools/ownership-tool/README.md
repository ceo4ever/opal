# ownership-tool

태스크 소유권 판정의 런타임 저장소·폐쇄 enum 계약과 플랫폼 hook 어댑터를 소유하는 도구다.
hook 어댑터는 `opal/core/hooks/claude-hooks.json`에 등재돼 Claude Code가 직접 실행한다(등재 지점이 SSOT).
CLI 표면은 `ownership_tool/cli.py`가 소유하며 `run.sh`가 그 진입점에 위임한다.

## 패키지 레이아웃 (PLAN D-19)

```
opal/tools/ownership-tool/
├── run.sh                      # OPAL .venv 래퍼 (ownership_tool.cli에 위임)
├── README.md
├── ownership_tool/             # 파이썬 패키지
│   ├── __init__.py
│   ├── cli.py                  # 공개 CLI 표면 (status·release·handoff·handoff-cancel)
│   ├── ownership_core.py       # 경로·스키마·lock·registry 어댑터·세션 ID 해석
│   ├── decisions.py            # D-3 폐쇄 enum과 구조화 판정 결과
│   ├── claude_adapter.py       # 플랫폼 고유 env 변수명 격리 (D-18, C-15)
│   ├── session_registry.py     # 세션 registry 저장소 기록기
│   ├── lease.py                # hub task lease claim·heartbeat·release·classify
│   ├── resolver.py             # worktree/hub 후보 resolver (registry meta 기반)
│   ├── fingerprint.py          # state 의미 필드 정규화 + SHA-256 fingerprint
│   ├── stop_evaluator.py       # Stop 판정 조립기 (후보 선택은 resolver에 위임)
│   ├── stop_hook.py            # Stop hook 어댑터
│   ├── session_start_hook.py   # SessionStart hook 어댑터
│   ├── pretooluse_guard_hook.py # PreToolUse hook 어댑터 (D-6 가드)
│   ├── heartbeat_hook.py       # PostToolUse hook 어댑터 (lease heartbeat)
│   └── session_end_hook.py     # SessionEnd hook 어댑터 (lease release)
└── tests/
    ├── conftest.py             # tool-dir을 sys.path에 삽입
    └── fixtures/
```

hook 어댑터는 판정 로직을 갖지 않는다 — 봉투 파싱·출력 형식만 소유하고 판정은 `stop_evaluator`·`lease`·
`resolver`가 맡는다. 어떤 실패에서도 세션을 막지 않는 fail-safe(전 경로 예외 삼킴 + exit 0)가 공통 규약이다.

`cli.py`도 같은 경계를 지킨다 — 인자 파싱·경로 절대성 검사·세션 id 해석·출력 형식만 소유하고 상태 전이는
전부 `lease`에 위임한다. hook 어댑터와 달리 사람·도구가 부르는 표면이므로 fail-safe exit 0이 아니라
거부를 0이 아닌 종료코드로 드러낸다.

`ownership-tool`은 하이픈 디렉터리라 패키지명이 될 수 없으므로 `ownership_tool/` 하위 패키지를 둔다.
테스트는 `from ownership_tool import decisions` 형태로 import하며 `tests/conftest.py`가 경로를 잇는다.

## CLI 표면

`run.sh <subcommand> ...`는 `ownership_tool.cli`에 위임하며, 전 경로에서 stdout에 단일 라인 JSON
`{"ok": bool, "command": "ownership-tool", ...}` 1줄만 낸다.

| 서브명령 | 인자 | 동작 |
|---|---|---|
| `status` | `--task-path` | lease 레코드 전문 + 요청 세션 기준 `lease.classify` 결과 + `handoff_*` 필드 |
| `release` | `--task-path` `[--session-id]` | 소유 세션 일치에만 해제 |
| `handoff` | `--task-path` `--to-worktree-root` | `lease.handoff` 위임 |
| `handoff-cancel` | `--task-path` | `lease.handoff_cancel` 위임 |

- 세션 id는 `--session-id` > `ownership_core.resolve_session_id(os.environ, {})` 순이다. 플랫폼 고유
  환경변수명은 `claude_adapter`가 단독으로 소유하고 `cli.py`에는 두지 않는다.
- `release`는 타 세션이 소유한 live lease를 `not_owner`로 거부하고 0이 아닌 종료코드를 내며 레코드를
  쓰지 않는다. 레코드 부재·`released`·만료는 `noop: true` + 종료코드 0이다. 강제 해제 표면은 없다.
- `--task-path`·`--to-worktree-root`의 상대경로는 cwd·task path 조상·워크트리 디렉터리명으로 보정하지
  않고 `path_not_absolute`로 거부한다(`harness/worktree.md` task root 계약).

## 런타임 저장소 3경로 (PLAN D-5)

| 저장소 | 경로 | 스키마 |
|---|---|---|
| 세션 registry | `<project_root>/.opal/run/.runtime/sessions/<session_id>.json` | `SessionRecord{session_id, cwd, started_at, heartbeat_at, expires_at, status}` |
| hub task lease | `<canonical_task_path>/run/.runtime/owner.json` | `LeaseRecord{task_path, owner_session_id, generation, claimed_at, heartbeat_at, lease_expires_at, status}` |
| stop receipt | `<project_root>/.opal/run/.runtime/stop-guard/<session_id>.json` | `StopReceipt{session_id, fingerprint, decision_kind, decided_at, block_count, pending_decisions}` |

경로 계산 함수는 각각 `session_registry_path()`·`hub_lease_path()`·`stop_receipt_path()`다.
세 경로 모두 `.gitignore`의 `.opal/*`(:2)와 `tasks/**/run/.runtime/`(:49)로 이미 추적 제외이므로
gitignore 추가 편집이 필요 없다.

**`<project_root>`의 출처는 `resolve_project_root()`다**(아래 §실행 루트 해석). 훅 봉투의 `cwd`를
그대로 쓰지 않는다 — `cwd`는 훅 발화 시점의 작업 디렉토리라 에이전트가 하위 디렉토리로 이동한 뒤
턴을 끝내면 그 하위 경로가 되고, 그대로 채택하면 저장소가 그 아래에 생긴다. 단 `.gitignore`의
`.opal/*`는 레포 루트 고정 패턴이라 하위 디렉토리의 `.opal/`은 덮지 않으므로, 그 오염은 곧바로
`git status`에 untracked로 노출된다.

## lock 계약 (PLAN D-7)

- 락 파일은 저장소 파일마다 `<path>.lock` 1개이며 `<task-path>/.opal-task.lock`(run-log/state-tool
  공용, 상한 30s)을 재사용하지 않는다.
- 획득 방식은 `run_log_core._acquire_lock` 패턴 그대로다 —
  `os.open(O_CREAT|O_RDWR|O_NOFOLLOW, 0o600)` → `os.fchmod(0o600)` → `fcntl.flock(LOCK_EX|LOCK_NB)`
  재시도 루프, 부모 디렉터리 `mkdir(mode=0o700)`.
- 재시도 상한은 `DEFAULT_LOCK_TIMEOUT_MS = 2000`ms다.
- 쓰기는 temp 파일 → `os.replace` 원자 교체다. 파일 0600, 디렉터리 0700.
- 상한 초과는 예외가 아니라 `{"ok": false, "error": "lock_timeout", "path": …, "timeout_ms": …}`
  구조화 반환이다.

```python
from ownership_tool import ownership_core as core

path = core.hub_lease_path(canonical_task_path)
result = core.write_json_atomic(path, core.LeaseRecord(task_path=..., owner_session_id=...))
if not result["ok"]:
    ...  # error: lock_timeout | write_failed
loaded = core.read_json(path)   # error: not_found | invalid_json | read_failed
```

## registry meta 읽기 전용 어댑터

`read_registry_meta(hub_root, task_number)`는 `<hub_root>/.opal-worktrees/.meta/task_<NNN>.json`을
읽기만 한다. 발급된 경로를 추측·보정하지 않는다.

- 성공: `{ok: true, allocator_root, task_home, task_folder, task_path, artifact_repo,
  task_ownership_version, attribution_state, execution_ownership, legacy}`
- `task_ownership_version` 부재: `legacy: true`로만 표시한다(거부하지 않는다).
- 파일 부재·손상 JSON·필수 키 누락: 예외가 아니라
  `{"ok": false, "diagnostic": "invalid_registry", "detail": …}`.

필수 키는 `allocator_root`·`task_home`·`task_folder`·`task_path`·`artifact_repo` 5종이며,
`attribution_state`·`execution_ownership`은 키 부재가 정상(active)이다.

## SessionStart hook 부트 계약

### env 파일 줄 포맷

`_append_session_id()`(`ownership_tool/session_start_hook.py:174-190`)는 어댑터가 알려준 env 파일에
`export OPAL_SESSION_ID=<quoted id>` 1줄을 append한다(`:186-187`). 플랫폼은 이 파일을 dotenv로
파싱하지 않고 Bash 도구의 **부모 쉘에서 `source`되는 쉘 프리앰블**로 실행하므로, `KEY=value` 대입만으로는
자식 프로세스가 값을 상속하지 못한다 — `export` 접두가 필요하다. 값은 쉘 메타문자에 안전하도록
`shlex.quote`로 quoting한다. 키 상수는 `SESSION_ID_ENV_LINE_KEY`(`:28`)이고, 파일 미제공
(`env_file_not_provided`)·쓰기 실패(`env_file_write_failed:<...>`)는 진단만 남기고 세션 registry 등록은
유지한다(`:182-190`).

### registry 부트 owner 등록

lease claim에 성공한 **워크트리** 세션은 이어서 허브 registry의
`execution_ownership.owner_session_id`를 1회 등록한다(`session_start_hook.py:115-171`, 호출 지점
`:247-250`). registry `execution_ownership`의 쓰기는 `worktree-tool ownership-set` CLI 경유만
허용되므로(TASK 999 C-9) 이 모듈은 meta를 **읽기만** 하고 전이는 CLI에 맡긴다 — 파일 쓰기·lock·원자 교체는
`worktree-tool` 소유라 dual writer가 생기지 않는다. 허브 위치는 `resolve_roots`가 준 `allocator_root`만
쓰고 추론하지 않으며, `--generation`은 지정하지 않아 `prior+1` 단조 증가에 맡긴다.

| 조건 | CLI 호출 | 결과 |
|---|---|---|
| `state == worktree_session_owned` ∧ `owner_session_id` 비어 있음 | 1회 (`:154-164`) | `registry_owner_registered: True` |
| `owner_session_id`가 이미 자기 세션 | 0회 (멱등 게이트 `:143-144`) | 진단 없음 |
| `owner_session_id`가 타 세션 | 0회 | 진단 `foreign_registry_owner`(`:145`) |
| `state != worktree_session_owned` | 0회 | 진단 `registry_not_worktree_owned`(`:138-139`) |
| registry 행 부재 | 0회 | 진단 `registry_row_absent`(`:135`, `:149`) |
| CLI 실행 불가·timeout·비정상 종료 | 시도 후 실패 | 진단 `ownership_set_failed` + `ownership_set_detail:<...>`(`:165-170`) |

호출 상한은 45초다(`_OWNERSHIP_SET_TIMEOUT_SEC`, `:43`) — CLI가 registry lock 대기를 자신의
`REGISTRY_LOCK_TIMEOUT_MS=30000`으로 이미 상한하므로 정상 경합은 자르지 않으면서, 멈춘 CLI가 세션 부팅을
막지 않게 한다. 어떤 분기에서도 예외로 새지 않고 구조화 반환하며 전 경로 fail-safe exit 0을 유지한다
(`:274-278`).

## 실행 루트 해석 (PLAN D-30)

`resolve_project_root(payload, env=None)` 순서:

1. `env["OPAL_PROJECT_ROOT"]` — 명시 오버라이드. 실제 디렉토리일 때만 채택한다
2. 봉투 `cwd`부터 **조상으로 올라가며** `.opal/MEMORY.json` 또는 `.opal/AGENT.md`를 **파일로**
   가진 첫 디렉토리
3. 없으면 `None`

이 함수가 어댑터 5종이 공유하는 **유일한 루트 채택 지점**이다. 다른 모듈은 루트를 스스로 만들지 않는다.

### 왜 조상 탐색인가

훅이 쓰는 루트는 `.opal` 설정·state의 저장 위치를 정하는 값이므로 `allocator_root`가 아니라
**`task_root`** 축이다. `task_root`의 결정 방법은 "canonical task path에서 가장 가까운 `.git`·`.opal`
작업본"으로 정의돼 있다 — 계약 원문은 `opal/core/references/harness/worktree.md` §task root와
allocator root 계약이며 여기에 복제하지 않는다. 같은 절의 "조상으로 추론하지 않는다" [MUST]는
`allocator_root` 전용이다. 선례는 `state-tool`의 `task_root()`로, 조상에서 `.opal/MEMORY.json` 앵커를
찾으면서 같은 docstring에 allocator root 제외를 병기한다.

플랫폼 환경변수(`CLAUDE_PROJECT_DIR` 등)는 **쓰지 않는다**. 조상 탐색은 전 플랫폼에서 성립하지만
플랫폼 변수는 그렇지 않아, 루트 해석을 그쪽에 묶으면 단일 실패점이 되고 플랫폼 독립성과 충돌한다.

### 앵커는 마커 파일이다

`.opal/` 디렉토리 존재만으로는 루트로 인정하지 않는다. 훅이 저장소를 잘못 만들던 시기의 오염은
`<하위>/.opal/run/.runtime/…` 형태라 `.opal/` 디렉토리는 있고 마커 파일은 없다. 디렉토리 존재를
앵커로 쓰면 오염된 하위가 루트로 승격돼 결함이 자기증식한다.

### 미해석이면 기록하지 않는다

`None`이면 훅 어댑터 `main()`이 **파일 I/O 이전에** 무출력·exit 0으로 종료한다. 루트를 확정하지
못한 상태에서 임의 위치에 쓰는 것보다 미기록이 낫다. 보강 방어선으로 `session_registry.register`와
`fingerprint.save_receipt`도 falsy 루트를 `{"ok": False, "error": "no_project_root"}`로 거부한다.
`state-tool`의 `task_root()`가 `None`일 때 "호출자는 subprocess를 아예 띄우지 말고 조기 반환"하는
것과 같은 계약이다.

## 세션 ID 해석 (PLAN D-18 · task 153)

식별 경로는 호출 주체에 따라 둘로 나뉜다.

| 호출 주체 | 함수 | 순서 |
|---|---|---|
| 훅 5종(SessionStart·SessionEnd·PostToolUse heartbeat·PreToolUse·Stop) | `hook_session_id(payload)` | 봉투 `payload["session_id"]`만. env를 받지 않는다 |
| 일반 CLI(`cli.py`) | `resolve_session_id(env, payload)` | ① `env["OPAL_SESSION_ID"]` ② `claude_adapter.session_id_from_env(env)` ③ 봉투 |

훅이 env를 읽으면 부모 세션의 env를 상속한 자식 Claude CLI의 종료가 부모 lease를 해제하고 부모
registry를 닫는다. 그래서 훅은 이벤트가 스스로 밝힌 신원만 쓴다. 봉투 `session_id`가 없거나 공백·비문자이면
`no_session_id` 진단만 남기고 어떤 파일도 쓰지 않는다(PreToolUse는 차단 없이 통과, Stop은 receipt 미기록).
플랫폼 고유 변수명은 `claude_adapter` 한 곳에만 둔다.

`ownership_core`에는 플랫폼 고유 변수명이 등장하지 않는다.

## Stop 보고 입력과 판정 receipt

Stop 판정은 후보 상태의 `run_log.last_report`가 있으면 그 포인터의 구조화 보고 의도를 우선
사용하고, 없을 때만 기존 상태 기반 전이 추정으로 폴백한다. `last_report`는 `pm.report` 사건의
파생 포인터이며 사건을 대체하지 않는다. 필드와 유효성의 원문은
`docs/run-log/CONTRACT.md` §1.4, 판정 분기는 `ownership_tool/stop_evaluator.py`가 소유한다.

`stop_evaluator`는 project root와 session ID가 해석된 Stop 판정을 receipt의
`pending_decisions`에 추가한다. Stop 임계 경로는
run-log/state-tool 공용 락을 잡거나 기록 조각에 직접 쓰지 않으며, 목록은 최근 32건으로 제한된다.
다음 `state-tool` 기록 커밋이 이 목록을 `stop.decision` 사건으로 변환해 기존
admission→원자 쓰기→drain 경로로 제출한 뒤 성공 항목을 receipt에서 제거한다. append 또는 receipt
갱신에 실패한 항목은 다음 호출에서 다시 처리할 수 있도록 남는다. 정확한 사건 계약과 읽기 진단은
`docs/run-log/CONTRACT.md` §1.2·§1.4·§2.5를 따른다.

`stop_hook.py`는 판정 전에 선택된 태스크를 `state-tool show --format json`으로 한 번만 읽고
(0.75초 상한), 같은 호출에서 만든 UTC 시각과 함께 evaluator에 넘긴다. 이 배선으로 실제 hook에서도
fingerprint·`decided_at`이 채워지고, 상태 진전 없는 반복 Stop은
`allow_no_progress_same_fingerprint` 경로에 도달한다. show 실패·timeout이면 `None`으로 폴백하며
hook의 무출력 exit 0 fail-safe는 유지된다. 구현 위치는 `stop_hook.py`의 `_state_tool_show()`와
`main()`, 판정 위치는 `stop_evaluator.py`의 반복 Stop 가드다.

## 폐쇄 enum (PLAN D-3)

`decisions.validate(result)`는 아래 목록 밖 값과 필수 키(`decision_kind`·`diagnostics`·
`candidates`·`evidence`) 누락을 `False`로 거부한다.

| enum | 값 |
|---|---|
| `DECISION_KINDS` | `allow_complete` · `allow_await_user` · `allow_inactive` · `allow_no_progress_same_fingerprint` · `allow_block_cap_reached` · `block_continue` · `defer_to_pm` |
| `DIAGNOSTICS` | `no_owned_task` · `multiple_hub_tasks` · `worktree_owned_shadow` · `foreign_owner` · `invalid_registry` · `invalid_state` · `launch_failed` · `no_progress_same_fingerprint` · `lease_expired` · `foreign_owner_bash_unclassified` · `passive_ownership` · `no_session_id` |

값 집합의 SSOT는 `ownership_tool/decisions.py`의 두 튜플이며, 위 표는 그 사본이다.

## 테스트

```bash
~/.opal/.venv/bin/python -m pytest opal/tools/ownership-tool/tests -q
```
