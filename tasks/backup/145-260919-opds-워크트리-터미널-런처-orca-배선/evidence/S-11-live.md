# S-11 실물 완주 관측 증거 (AC-3 · AC-5)

> 관측일: 2026-09-19 | 관측자: 알투[PM] | 환경: orca 1.4.205, darwin, 배포본 `~/.opal/tools/worktree-launcher/`

## (1) launcher 정상 경로 — `worktree_session_owned` 전이

명령:

```bash
~/.opal/tools/worktree-launcher/run.sh launch --adapter orca \
  --project-root /Volumes/Data/AIStudio/workspace/ai-framework \
  --task 996 \
  --worktree-root /Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_996
```

응답:

```json
{"ok":true,"command":"launch","status":"worktree_session_owned","failure_reason":null,
 "task":"996","generation":2,"adapter":"orca",
 "adapter_handle":"term_d0c13971-5aea-40d6-b540-6bd7250feb5c",
 "launch_receipt":{"adapter":"orca","adapter_handle":"term_d0c13971-5aea-40d6-b540-6bd7250feb5c",
   "reported_cwd":"/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_996",
   "launched_at":"2026-09-19T06:46:07.725050+00:00"},
 "prompt_receipt":{"prompt_id":"4f3b75739623fe3a","submitted_at":"2026-09-19T06:46:07.725050+00:00"}}
```

registry 직접 조회(`.opal-worktrees/.meta/task_996.json`):

- `execution_ownership.state = worktree_session_owned`
- `adapter = orca`, `generation = 2`
- `launch_receipt` 4키(`adapter`·`adapter_handle`·`launched_at`·`reported_cwd`), `prompt_receipt` 2키 — **둘 다 객체로 기록됨**

`reported_cwd`가 워크트리 루트와 일치한다 → 실물 응답에서 `result.terminal.worktreeId` 디코드가 성립한다(H-1 완화 확인).

## (2) 첫 턴 자기시작 — 사람 입력 0회

`orca terminal read --terminal term_d0c13971-… --json`의 상태줄:

```
Opus 5 (1M context) │ task_996 │ feat/OP-TASK-996* │ 🧠 6%/1M │ … │ 🎯 996
⏵⏵ auto mode on (shift+tab to cycle) · ← for agents
```

- 워크트리 세션이 **자기 태스크 번호(996)와 브랜치(`feat/OP-TASK-996`)를 스스로 인지**했다.
- `Cogitating…` → `running PostToolUse hooks… 0/3 → 3/3` → `Brewed for 1m 10s · done` — 사람 입력 없이 첫 턴이 시작·완료됐고 **OPAL hook 3종이 실제로 발화**했다.
- Orca 탭 제목이 `✳ Task 996 opds 런처 실물완주 검증`으로 잡혔다.
- 설정 `launcher` 블록이 배포본 `~/.opal/setting.json`에 **없는 상태**였다 → 코드 기본값 폴백(D-F) 경로가 실경로에서 성립함을 함께 확인했다.

## 관측된 한계 (이번 AC 밖, 후속 후보)

`execution_ownership.owner_session_id`가 `None`으로 남는다. 허브가 launch 시점에 새 세션의 id를 알 수 없기 때문이다. registry 전이는 receipt 2종만 요구하므로 성공하지만, `worktree-tool checkpoint`의 소유권 검사는 `owner_session_id == OPAL_SESSION_ID`를 요구하므로 **이대로면 워크트리 세션이 자율 체크포인트 커밋 자격을 얻지 못한다.**

## (3) 실패 주입 — `hub_owned` 복귀 + 터미널 0개

목업 `task_995`에 `PATH=/usr/bin:/bin`(orca 미발견)으로 launch:

```json
{"ok":false,"status":"hub_owned","failure_reason":"launch_failed",
 "detail":"launch_receipt_missing","generation":2,
 "terminal_close":{"attempted":false,"reason":"handle_missing"}}
```

registry: `state=hub_owned`, `failure_reason=launch_failed`, `generation=2`, `launch_receipt=None`, `prompt_receipt=None`. 터미널 잔존 **0개**.

> **한계**: 이 경로는 orca 자체가 실행되지 않아 터미널이 만들어진 적이 없다. "이미 만들어진 터미널을 복귀 시 닫는다"는 동작은 live로 유도하지 못했고, S-4 단위 테스트(복귀 5경로 × fake adapter)가 그 증거를 소유한다.

## (4) 회수 — 가드 거부와 스윕 두 경로

**dirty 거부(H-4 확인)**: `task_996`(세션이 태스크 문서를 만들어 dirty) 회수 시도 → `GUARD_DIRTY`로 거부. 이 시점 터미널은 **1개 그대로** — 스윕에 도달하지 않음이 실측됐다.

**스윕 성공(AC-6)**: 클린 워크트리 `task_994`에 터미널 1개를 띄운 뒤 `worktree-tool remove` →

```json
{"ok":true,"removed":["…/task_994"],"forced":false,"bypassed_guards":[],
 "terminals_closed":{"ok":true,"command":"close","adapter":"orca","exit_code":0,
   "scope":"worktree_all","closed":[]}}
```

회수 후 `task_994`·`task_995`·`task_996` 잔존 터미널 **각 0개**.

## 발견 2건 (AC 밖)

1. **`--worktree … --all` 스윕의 `closed`가 항상 비어 있다.** orca가 실제로는 닫으면서 `closed: 0`을 보고한다(raw CLI로도 재현). 따라서 `terminals_closed.closed` 목록을 "닫힌 개수"의 증거로 쓰면 안 되며, 판정은 `terminal list` 재조회로 해야 한다.
2. **실행 중인 에이전트 TUI를 스윕할 때 orca가 비-0을 반환한다.** `task_996`(claude TUI 실행 중) `--force` 회수에서 `close_failed`/`orca_nonzero_exit` 경고가 났지만 **실제로는 닫혔고 회수도 성공**했다(H-5의 비차단 설계가 의도대로 작동). `sleep` 프로세스에서는 exit 0이었다 — TUI 종료 경로 차이로 보이며, 경고가 false negative가 되는 문제다.
