# PROBE-BASELINE — 세션 상속 baseline 실측 (AC-1 1차 증거)

> 측정 시각: 2026-09-19 17:44 KST
> 측정 세션: 워크트리 전용 agentic 세션 (orca 런처 기동, `ORCA_WORKTREE_ID` 설정됨)
> 측정 위치: `/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_999`
> 측정 방법: PM이 실제 세션의 Bash 경계와 공개 CLI만 사용 (테스트 내부 주입 없음)

## 1. 측정 결과

| # | 관측 지점 | 값 | 판정 |
|---|-----------|-----|------|
| P-1 | 부모 세션 ID (`CLAUDE_CODE_SESSION_ID`) | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` | 존재 |
| P-2 | Bash **쉘 변수** `OPAL_SESSION_ID` (`echo`) | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` | 존재 |
| P-3 | Bash **export 여부** (`typeset -p OPAL_SESSION_ID`) | `typeset OPAL_SESSION_ID=...` — `-x` 없음 | **미export** |
| P-4 | 자식 프로세스 상속 (`sh -c 'echo $OPAL_SESSION_ID'`) | `unset` | **상속 실패** |
| P-5 | venv python에서 `state_tool._current_session_id()` | `None` | **상속 실패** |
| P-6 | `state-tool advance` stderr | `{"warning":"ownership_session_id_missing", ...}` | **claim 미수행** |
| P-7 | run-log `actor.session_id` (`run.started`·`state.changed` 2건) | `null` | **미기록** |
| P-8 | `run/.runtime/owner.json` `claim_source` | `session_start` (17:39:29 claim, 이후 heartbeat만) | **승격 안 됨** |
| P-9 | `owner.json.owner_session_id` | `4e1a2aa2-...` (SessionStart hook 경유로는 정상) | 존재 |
| P-10 | `CLAUDE_ENV_FILE` (Bash 경계) | unset | 어댑터 경계에서만 존재 |

## 2. 판정 — TASK.md Problem 가설의 수정

TASK.md는 "`OPAL_SESSION_ID`가 Bash subprocess에 전달되지 않는다"를 문제로 세웠다.
실측은 한 단계 더 좁은 지점을 가리킨다.

- 변수는 **Bash 쉘까지는 도달한다**(P-2). SessionStart hook의 env 파일 append 경로는 동작하고 있다.
- 그러나 `export`되지 않아(P-3) **Bash가 띄우는 자식 프로세스에는 전달되지 않는다**(P-4, P-5).
- `state-tool`은 자식 프로세스이므로 `OPAL_SESSION_ID`를 못 읽고(P-5), lease claim을 건너뛰며(P-6),
  run-log `actor.session_id`를 `null`로 남긴다(P-7).
- 그 결과 lease의 `claim_source`가 `session_start`에 머물러(P-8) Stop evaluator의 **강제 후보 자격이
  성립하지 않는다**(`passive_ownership` 진단 경로 — `.opal/brain/pages/concept/stop-force-requires-state-transition-claim.md`).

즉 고장 지점은 "부모→Bash 전달"이 아니라 **"Bash→자식 프로세스 export 경계"** 한 곳이다.

## 3. 1차 원인 후보 (PLAN에서 확정할 것)

`opal/tools/ownership-tool/ownership_tool/session_start_hook.py:89-97` `_append_session_id()`가
env 파일에 `OPAL_SESSION_ID=<id>\n`을 쓴다 — `export` 키워드가 없다.
소비자 쉘이 이 파일을 `source`하면 zsh/bash에서 **비export 파라미터**가 만들어지고, P-3 관측과 일치한다.

단, env 파일 포맷을 플랫폼(Claude Code)이 `KEY=VALUE`로 파싱해 주입하는 계약일 수도 있으므로,
`export` 접두 추가가 포맷 계약 위반이 되는지는 PLAN이 실제 env 파일 소비 경로를 확인해 확정한다.
이 판정 없이 수정하면 C-3("hook 자식 프로세스 안의 단순 export를 해결로 인정하지 않는다")에 걸린다.

## 4. 이 문서의 경계

- AC-1이 요구하는 "수정 전 baseline 한 증거 묶음"의 1차분이다. AC-4의 evaluator 판정(실제 Stop hook
  stdin 봉투)은 아직 측정하지 않았다 — EXECUTE에서 같은 프로브로 수행한다.
- 측정만 수행했고 어떤 파일도 수정하지 않았다.

---

# 5. `--wt` + Orca 최초 실사용 경로 baseline (AC-9~AC-14 1차 증거)

> 측정 시각: 2026-09-19 17:52 KST · 측정 주체: 워크트리 전용 세션 PM (읽기 전용)
> 원천: 허브 registry `/.opal-worktrees/.meta/task_999.json` · 워크트리 `.opal/task-ownership.json` · git · 프로세스 env

## 5.1 launcher / prompt receipt (AC-9)

| 필드 | 값 | 판정 |
|---|---|---|
| `execution_ownership.adapter` | `orca` | 존재 |
| `execution_ownership.adapter_handle` | `term_216541d9-ed40-48bf-b5f1-54ee21a8f28f` | 존재 |
| `launch_receipt.launched_at` | `2026-09-19T08:39:27.966926+00:00` | 존재 |
| `launch_receipt.reported_cwd` | `.../.opal-worktrees/task_999` | `worktree_root`와 **일치** |
| `prompt_receipt.prompt_id` | `451a5b33401bbc7a` | 존재 |
| `prompt_receipt.submitted_at` | `2026-09-19T08:39:27.966926+00:00` | 존재 |
| `execution_ownership.state` | `worktree_session_owned` | 정상 전이 |
| `execution_ownership.generation` | `2` | 역행 없음 |
| `execution_ownership.failure_reason` | `null` | 복귀 없음 |

→ **AC-9·AC-14 1차 만족.** launcher 체인(adapter → launcher_core → ownership-set → registry)은 실사용에서 정상 동작했다.

## 5.2 새 터미널의 워크트리 인식 (AC-10)

| 관측 | 값 | 판정 |
|---|---|---|
| 세션 cwd / `git rev-parse --show-toplevel` | `.../.opal-worktrees/task_999` | `worktree_root` 일치 |
| `ORCA_WORKTREE_ID` | `ce5d0068-...::/.../task_999` | Orca 터미널 실기동 확인 |
| 현재 git 브랜치 | `feat/OP-TASK-999` | registry `branch` 일치 |
| `.opal/task-ownership.json` 6필드 | registry 발급값과 전건 일치 | 사본 배달 정상 |

→ **AC-10 만족.** 발급값 사본 경로(`worktree-locates-hub-by-issued-copy`)가 실사용에서 성립한다.

## 5.3 초기 prompt 제출 → 단계 진행 (AC-11)

- 세션이 부트 브리핑에서 `state.json`을 읽어 `999 · TASK · 모드 agentic`으로 재개했다.
- 같은 세션에서 `state-tool mark task.task_md --done`(17:41:41)과 `advance plan.plan_md`(17:44:18)가 실행됐고 run-log에 `state.changed`가 적재됐다.
- **단, 그 run-log 사건의 `actor.session_id`는 `null`이다**(§1 P-7) — "이 세션이 전진시켰다"는 사실이 기록에 남지 않는다.

→ **AC-11 부분 만족.** 진행은 이어졌으나 *귀속 증거*가 비어 있다. §1의 export 결함과 같은 뿌리다.

## 5.4 registry ↔ lease 불일치의 원인·영향 (AC-12)

**관측된 불일치**

| 저장소 | 필드 | 값 |
|---|---|---|
| 허브 registry meta | `execution_ownership.owner_session_id` | `null` |
| 태스크 lease | `run/.runtime/owner.json.owner_session_id` | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` |

**(a) 각 필드의 writer**
- registry `owner_session_id` — `worktree-tool ownership-set`만 쓴다(`worktree_tool.py:1791` `cmd_ownership_set`, `:1880-1882`). launcher가 이 CLI를 subprocess로 경유한다(`worktree-launcher/README.md:109-112`).
- lease `owner_session_id` — `ownership_tool.lease.claim()`이 쓴다. SessionStart hook(`claim_source=session_start`)과 state-tool 상태 전이(`claim_source=state_transition`)가 호출자다.

**(b) 부트 이후 registry 쪽을 채우는 주체**
- **존재하지 않는다.** launcher는 터미널을 띄우는 시점에 아직 태어나지 않은 세션의 ID를 알 수 없어 `owner_session_id=None`으로 `worktree_session_owned`를 기록한다(현행 테스트가 이 값을 `None`으로 단언한다 — `worktree-launcher/tests/test_launcher_core.py:81,110,143`).
- 워크트리 세션이 부트한 뒤 registry에 자기 ID를 등록하는 경로가 어느 훅·도구에도 없다. SessionStart hook은 **lease만** claim하고 registry는 읽기 전용으로만 다룬다(`.opal/brain/pages/entity/ownership-tool.md` §"registry는 읽기 전용이다").

**(c) `checkpoint`에 미치는 영향 — 구조적 차단**

`worktree_tool.py:2107-2123`:

```python
session_id = os.environ.get("OPAL_SESSION_ID")
...
if not session_id or block.get("owner_session_id") != session_id:
    err_response("checkpoint_ownership_denied", reason="foreign_owner", ...)
```

두 항이 **각각** 실패한다.
1. `os.environ.get("OPAL_SESSION_ID")` → `None` (§1 P-5, export 누락)
2. `block["owner_session_id"]` → `None` ≠ 실제 세션 ID (registry 미기록)

→ `harness/guards.md` §커밋 규칙이 agentic 워크트리 세션에 허용한 **체크포인트 커밋 예외가 현재 구조적으로 도달 불가능하다.** `.opal-worktrees/.meta/task_999.json`의 `checkpoint_shas`가 `[]`인 것과 정합한다.

→ **AC-12 판정 완료. AC-13은 두 결함을 모두 고친 뒤에만 실증 가능하다.**

## 5.5 이 절의 경계

읽기만 수행했다. `ownership-set`·`checkpoint`를 호출하지 않았고 registry·lease·터미널을 변경하지 않았다.

---

# 6. 실세션 Stop 차단 관측 (PM Gate 증거 축, 비계획 수집)

> 관측 시각: 2026-09-19 20:39 KST · 관측 주체: PM 세션 자신 · 수집 경위: 계획된 프로브가 아니라 **실제로 발생한 사건**

## 6.1 무슨 일이 일어났나

PM이 진행 보고를 마치고 응답을 종료하려 하자, 플랫폼이 등록된 Stop hook을 호출했고 **차단이 발화했다.**

```
OPAL Stop guard: block_continue. 판정 대상 1건 —
task_id=999-260919-opds-세션상속-스톱가드-목업검증 | transition_action=continue |
next_action=EXECUTE 작업 진행 중 · 이 태스크가 아직 transition_action=continue다.
응답을 끝내지 말고 이어서 진행하라.
```

stop-guard receipt: `block_count` **9 → 10**, `decision_kind: block_continue`.

## 6.2 이 관측이 기존 증거와 다른 점

| 축 | W-3·W-5의 프로브 | 이번 관측 |
|---|---|---|
| hook 호출 주체 | 워커가 stdin으로 봉투 주입 | **플랫폼이 실제 Stop 시점에 호출** |
| 봉투 | 워커가 구성 | **플랫폼이 생성** |
| 차단 대상 | 없음(관측만) | **PM의 실제 응답이 실제로 차단됨** |
| 세션 부팅 시점 | 동일(수정 이전) | 동일(수정 이전) |

즉 이 관측은 **호출 경로의 실사용 충실도**에서 기존 증거보다 높다 — 사람이 흉내 낸 봉투가 아니라
플랫폼이 스스로 만든 봉투로, 판정이 실제 집행(응답 종료 차단)까지 이어졌다.

## 6.3 한계 — S-3b·S-4b를 대체하지 않는다

이 세션은 W-1 수정 **이전에** 부팅했으므로 `OPAL_SESSION_ID`가 여전히 미export다.
그럼에도 차단이 성립한 이유는 D-G가 확정한 대로 evaluator가 `ownership_core.resolve_session_id`
(env → 플랫폼 어댑터 → 봉투)로 세션 ID를 얻어 **export 결함의 영향을 받지 않기** 때문이다.

따라서 이 관측이 입증하는 것은 **Stop 차단 경로의 실사용 동작**이지, 수정 후 신규 세션에서의
종단 상속이 아니다. S-3b(실세션 `typeset -x` + 전이)와 S-4b(신규 세션 3값 재현)는
**여전히 미이행**이며 재배포 이후 부팅하는 다음 워크트리 세션에서 확인해야 한다.

## 6.4 부수 사실

lease `claim_source=state_transition`(W-2가 승격)이 유지되고 있어 강제 후보 자격이 성립했다.
`claim_source`가 `session_start`에 머물렀다면 이 차단은 발화하지 않았을 것이다
(`.opal/brain/pages/concept/stop-force-requires-state-transition-claim.md`).
