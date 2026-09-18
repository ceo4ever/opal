# ownership-tool

태스크 소유권 판정의 런타임 저장소와 폐쇄 enum 계약을 소유하는 도구다. 현재 구현 범위는
코어(W-1)까지이며 CLI 표면과 hook 어댑터는 후속 Work item이 채운다.

## 패키지 레이아웃 (PLAN D-19)

```
opal/tools/ownership-tool/
├── run.sh                  # OPAL .venv 래퍼 (CLI 미구현 — not_implemented 반환)
├── README.md
├── ownership_tool/         # 파이썬 패키지
│   ├── __init__.py
│   ├── ownership_core.py   # 경로·스키마·lock·registry 어댑터·세션 ID 해석
│   ├── decisions.py        # D-3 폐쇄 enum과 구조화 판정 결과
│   └── claude_adapter.py   # 플랫폼 고유 env 변수명 격리 (D-18, C-15)
└── tests/
    ├── conftest.py         # tool-dir을 sys.path에 삽입
    └── fixtures/
```

`ownership-tool`은 하이픈 디렉터리라 패키지명이 될 수 없으므로 `ownership_tool/` 하위 패키지를 둔다.
테스트는 `from ownership_tool import decisions` 형태로 import하며 `tests/conftest.py`가 경로를 잇는다.

## 런타임 저장소 3경로 (PLAN D-5)

| 저장소 | 경로 | 스키마 |
|---|---|---|
| 세션 registry | `<project_root>/.opal/run/.runtime/sessions/<session_id>.json` | `SessionRecord{session_id, cwd, started_at, heartbeat_at, expires_at, status}` |
| hub task lease | `<canonical_task_path>/run/.runtime/owner.json` | `LeaseRecord{task_path, owner_session_id, generation, claimed_at, heartbeat_at, lease_expires_at, status}` |
| stop receipt | `<project_root>/.opal/run/.runtime/stop-guard/<session_id>.json` | `StopReceipt{session_id, fingerprint, decision_kind, decided_at, block_count}` |

경로 계산 함수는 각각 `session_registry_path()`·`hub_lease_path()`·`stop_receipt_path()`다.
세 경로 모두 `.gitignore`의 `.opal/*`(:2)와 `tasks/**/run/.runtime/`(:49)로 이미 추적 제외이므로
gitignore 추가 편집이 필요 없다.

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

## 세션 ID 해석 (PLAN D-18)

`resolve_session_id(env, payload)` 순서:

1. `env["OPAL_SESSION_ID"]`
2. `claude_adapter.session_id_from_env(env)` — 플랫폼 고유 변수명은 이 어댑터 한 곳에만 둔다
3. hook 봉투 `payload["session_id"]`

`ownership_core`에는 플랫폼 고유 변수명이 등장하지 않는다.

## 폐쇄 enum (PLAN D-3)

`decisions.validate(result)`는 아래 목록 밖 값과 필수 키(`decision_kind`·`diagnostics`·
`candidates`·`evidence`) 누락을 `False`로 거부한다.

| enum | 값 |
|---|---|
| `DECISION_KINDS` (7) | `allow_complete` · `allow_await_user` · `allow_inactive` · `allow_no_progress_same_fingerprint` · `allow_block_cap_reached` · `block_continue` · `defer_to_pm` |
| `DIAGNOSTICS` (10) | `no_owned_task` · `multiple_hub_tasks` · `worktree_owned_shadow` · `foreign_owner` · `invalid_registry` · `invalid_state` · `launch_failed` · `no_progress_same_fingerprint` · `lease_expired` · `foreign_owner_bash_unclassified` |

## 테스트

```bash
~/.opal/.venv/bin/python -m pytest opal/tools/ownership-tool/tests -q
```
