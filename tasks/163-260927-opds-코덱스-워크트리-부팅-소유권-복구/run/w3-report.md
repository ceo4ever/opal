# W-3 실행 보고

## 결과

- 상태: complete
- 범위: launcher lifecycle, Orca terminal status, recover CLI와 관련 단위 테스트
- 블로커: 없음

## 구현

- 자식의 foreign live lease를 bounded polling으로 확인한 뒤, 관측한 owner를 expected/excluded 원자 비교와 함께 registry owner로 확정한다.
- claim timeout 및 종료 확인 불가 경로는 `recovery_required`로 기록한다. close 뒤 `status == absent`, 실제 시작된 handoff의 cancel, lease 재조회가 모두 확인된 경우에만 `hub_owned`로 복귀한다.
- `recover`는 저장된 handle 또는 worktree 상태를 다시 확인하고 안전할 때만 hub ownership으로 전이한다.
- Orca adapter에 `status`와 `status_worktree`를 추가했다. stale show와 list 부재가 함께 확인될 때만 absent를 보고한다.
- Polling timeout 뒤에는 close 전에 lease를 한 번 더 읽고, 그 시점의 live child claim은 원자 owner 전이로 처리한다.
- `created` 터미널은 close 성공과 absent 확인이 함께 성립할 때만 hub ownership으로 복귀한다. recover도 handoff-cancel 확인 뒤 safe lease classification을 요구한다.
- `recover`와 revert status checks는 registry가 발급한 worktree root만 사용한다. lease 상태는 `ok: true`와 명시 safe classification이 함께 있어야 한다.
- `recover`는 `not_handoff_owner` cancel 결과도 새 lease의 pending handoff·잔존 handoff 필드와 대조한다. 남아 있으면 상태를 바꾸지 않는다.
- Final owner transition response is checked against the observed child lease owner and raises `ownership_postcondition_violated` on a mismatch without a compensating transition.
- Added `launcher.leasePollTimeoutSec` with a code default; CLI passes the effective setting while direct `run()` callers retain the default. A handoff that persisted before its caller failed is detected and cancelled during revert.
- The readiness polling default is 30 seconds, documented in the launcher README. Unit fixtures set a short explicit default because they test transition ordering rather than startup latency.
- Orca recognizes a confirmed operator-closed orphan only when its show evidence and a successful worktree list agree that neither handle nor PTY remains. List failures and identity matches remain `unknown`.
- 기존 ownerless-success 및 무조건 hub rollback 테스트는 새 안전 계약에 맞춰 recovery expectation으로 갱신했다. 새 RED 블록은 변경하지 않았다.

## 검증

```text
/Users/iskang/.opal/.venv/bin/python -m pytest -q \
  opal/tools/worktree-launcher/tests/test_launcher_core.py \
  opal/tools/worktree-launcher/tests/test_adapter_orca.py \
  opal/tools/worktree-launcher/tests/test_adapter_conformance.py \
  opal/tools/worktree-launcher/tests/test_cli.py

146 passed, 3 skipped (launcher focused suite and settings suite)
git diff --check
```

## 변경 파일

- `opal/tools/worktree-launcher/worktree_launcher/launcher_core.py`
- `opal/tools/worktree-launcher/worktree_launcher/cli.py`
- `opal/tools/worktree-launcher/worktree_launcher/adapters/orca.py`
- `opal/tools/worktree-launcher/tests/test_launcher_core.py`
- `opal/tools/worktree-launcher/tests/test_adapter_orca.py`
- `opal/tools/worktree-launcher/README.md`
- `opal/core/references/harness/worktree.md`
