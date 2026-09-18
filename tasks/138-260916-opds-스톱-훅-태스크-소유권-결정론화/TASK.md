---
template: sdlc-v2
---

# TASK: `--wt` 전용 세션·Stop 훅 태스크 소유권 결정론화

## Problem

현재 `--wt`는 OPAL worktree와 canonical task path를 만들지만 별도 Claude 세션을 실행하지 않는다. 허브에서 시작한 세션은 계속 허브 cwd를 사용하므로, worktree별 1:1 실행·소유권과 Stop 판정을 보장할 수 없다.

현재 global Claude Stop hook은 `cwd`와 상위 디렉터리의 `tasks/*/state.json`을 스캔하고 `updated_at`이 가장 최근인 태스크 하나를 선택한다. 이 방식에는 다음 결함이 있다.

- registry canonical이 active worktree를 가리키는데 허브에 같은 task folder의 진행 중 사본이 남으면, 허브 Stop hook이 그 사본을 자기 태스크로 오인한다. Task 132가 실제 반례다.
- 허브에 여러 Claude 세션이 있으면 다른 세션이 소유한 단독 허브 태스크도 현재 세션을 차단한다.
- hub lease writer가 명시적 activate/resume/handoff만 기다리면 실제 자동 발화 지점이 없어 모든 허브 태스크가 무소유 판정으로 떨어진다.
- `stop_hook_active` 재진입을 무조건 통과시키면 상태가 실제로 진전됐는지 확인할 수 없고, 반대로 매번 재평가해 차단하면 동일 상태로 무진행 반복한다.
- 전체 `state.json` hash를 fingerprint로 사용하면 timestamp·run-log 기록만 바뀌어도 진행으로 오판해 같은 의미 상태를 다시 차단한다.
- 같은 worktree에 수동으로 연 두 번째 세션은 handoff receipt가 없어 소유권 획득 시도 자체가 발생하지 않으며, resolver의 foreign owner 처리도 정의돼 있지 않다.
- 새로 제안한 실행 소유권 lifecycle의 저장 위치와 기존 registry `attribution_state` 관계가 없으면 한 태스크에 서로 어긋날 수 있는 두 lifecycle이 생긴다.
- OPAL Stop hook은 이미 global `~/.claude/settings.json`에 설치되는데 worktree project settings에도 materialize하면 중복 실행된다.

실행 모델은 다음 관계를 명시적으로 지원해야 한다.

- 허브 실행: 한 세션이 여러 허브 태스크 lease를 가질 수 있다(`task:session = N:1`).
- worktree 실행: 한 전용 세션은 하나의 worktree와 canonical task만 소유한다(`worktree:session = 1:1`).
- 허브 세션 전체에 `session_id -> exactly one task`를 강제하지 않는다.

## Proposed outcome

1. `worktree-tool`이 worktree 생성, registry와 canonical task path의 단일 소유자로 남는다.
2. `--wt`는 worktree 생성 후 필요한 project 권한·설정을 준비하고 canonical task handoff payload를 생성한 뒤 worktree cwd의 전용 Claude 세션을 실행한다. OPAL Stop hook은 global 단일 owner를 유지하며 project/worktree settings에 복제하지 않는다.
3. Orca 환경에서는 이미 생성된 OPAL worktree에 터미널을 연결해 Claude TUI를 실행한다. Orca가 중복 checkout/worktree를 만들지 않는다.
4. 비-Orca 환경에서는 구성된 terminal launcher를 사용하고, launcher가 없으면 `opal-agent --provider claude --cwd <worktree_root>`를 비대화형 fallback으로 사용한다. 지속형 TUI와 one-shot/resume 실행을 구분한다.
5. launch receipt와 handoff prompt 제출 receipt가 모두 확인된 뒤에만 worktree 세션으로 소유권을 이전한다. 이전 후 허브 PM은 해당 태스크의 writer가 되지 않는다.
6. worktree Stop resolver는 registry ownership record의 exact canonical task 하나만 평가한다.
7. Claude `SessionStart`가 session ID와 cwd를 ownership coordinator에 등록한다. worktree 세션은 registry exact canonical task에 자동 claim을 시도하고, 허브 세션은 canonical task가 확정되는 pilot activation·state init·첫 상태 전이 경계에서 별도 PM 호출 없이 lease를 자동 claim한다.
8. 허브 Stop resolver는 허브 직계 태스크를 스캔한 뒤 registry와 hub runtime lease를 대조한다. active worktree canonical의 허브 동명 사본은 `worktree_owned_shadow`로 분류해 강제 후보에서 제외하고, 다른 live session lease도 제외한다. 현재 세션 lease가 정확히 하나면 평가하고 복수면 전체를 PM 판단 입력으로 반환하며, 무소유 후보도 PM 판단 입력에 포함한다. 같은 worktree의 비소유 세션은 `foreign_owner`로 진단하고 Stop을 통과시킨다.
9. Stop hook이 차단한 뒤 재진입하면 세션별 semantic decision fingerprint를 비교한다. 동일 fingerprint의 무진행 재차단은 허용하지 않고, 파이프라인 상태·registry·lease의 의미 상태가 바뀐 경우에만 새 판정을 수행한다.
10. 등록된 전용 worktree의 체크포인트 커밋은 모드별로 수행한다. `agentic`은 검증된 안정 경계에서 자율 커밋하고, `semi-agentic`과 `interactive`은 기존 사용자 Gate가 승인한 범위에서만 커밋한다.
11. worktree는 `completed_unmerged`까지 진행한다. `main`·기본 브랜치 commit/merge, push, 배포, 귀속 최종화와 worktree 제거는 사용자 승인 후 허브에서 수행한다.

## Affected users and systems

- `//task --wt`를 실행하는 PM과 사용자
- `worktree-tool` registry/meta schema와 canonical resolver
- hub task runtime lease와 Stop fingerprint runtime store
- `state-tool`, run-log, task lifecycle과 pipeline templates
- `harness/guards.md` 커밋 규칙, `harness/task-process.md`, agentic·semi-agentic·interactive 모드 계약, `opal-self-pm` 권한 포인터와 `docs/CONVENTIONS.md`
- Claude Code global settings installer와 SessionStart·PreToolUse·PostToolUse·Stop·SessionEnd hook source
- Orca terminal/worktree integration
- 비-Orca terminal launcher와 `opal-agent` Claude adapter
- 설치 소스와 배포 산출물의 동등성 검사

## Runtime ownership and lifecycle

### Worktree registry SSOT

worktree 실행·귀속 lifecycle의 영속 SSOT는 `<hub_root>/.opal-worktrees/.meta/task_<NNN>.json`이며 `worktree-tool`만 쓴다. 별도 독립 lifecycle 파일을 만들지 않는다.

| 파생 단계 | `execution_ownership.state` | 기존 `attribution_state` |
|---|---|---|
| `hub_owned` | `hub_owned` | 키 부재 |
| `session_launching` | `session_launching` | 키 부재 |
| `worktree_session_owned` | `worktree_session_owned` | 키 부재 |
| `completed_unmerged` | `released` | `completed_unmerged` |
| `hub_finalize` | `released` | `attribution_pending` |
| `closed` | `released` | `closed` |

`execution_ownership`은 최소 `state`, `owner_session_id`, `adapter`, `adapter_handle`, `generation`, launch/prompt receipt와 실패 사유를 가진다. 두 축은 한 registry lock과 atomic replace 안에서 허용 조합으로만 전이한다. launch 또는 prompt 제출 실패는 `launch_failed`를 기록하고 generation을 증가시켜 `hub_owned + attribution key absent`로 원자 복귀한다.

### Hub task lease

허브 태스크의 세션 lease는 추적 제외 경로 `<canonical_task>/run/.runtime/owner.json`에 저장한다. 최소 `task_path`, `owner_session_id`, `generation`, `claimed_at`, `heartbeat_at`, `lease_expires_at`, `status`를 가지며 전용 ownership coordinator가 lock과 atomic replace로 갱신한다.

`SessionStart`는 hook payload의 session ID와 cwd를 coordinator에 등록하고, Claude가 제공하는 `CLAUDE_ENV_FILE`에 현재 세션 전용 `OPAL_SESSION_ID`를 영속해 이후 Bash에서 호출되는 pilot·state-tool이 같은 ID를 전달받게 한다. worktree cwd가 registry exact canonical task로 해석되면 세션 시작 시 자동 claim을 시도한다. 기존 live owner가 있으면 이전하지 않고 `foreign_owner`로 거부한다. 허브에서는 세션 시작만으로 태스크를 추측하지 않으며, canonical task가 확정되는 pilot activation·`state-tool init`·첫 상태 전이 중 최초 경계가 `OPAL_SESSION_ID`로 현재 session lease를 자동 생성한다. 이 자동 경로는 PM의 별도 activate 호출을 요구하지 않는다.

명시적인 resume/handoff/activate receipt는 소유권 이전·복구 override로만 사용한다. 일반 `PostToolUse`의 마지막 세션을 owner로 덮어쓰지 않고, 구조화된 payload가 같은 canonical task를 명시한 경우 기존 lease heartbeat만 갱신한다. 한 session ID가 여러 hub task lease를 소유하는 것은 허용한다. `SessionEnd`/release는 lease를 닫고, SessionEnd가 발화하지 않는 crash·강제 종료는 TTL 만료로 회수하며 만료 lease는 무소유로 분류한다.

### Stop decision receipt

세션별 마지막 차단 receipt는 추적 제외 경로 `<project_root>/.opal/run/.runtime/stop-guard/<session_id>.json`에 lock과 atomic replace로 저장한다. fingerprint는 정렬된 canonical 후보 경로, 각 태스크의 `current_status`, 안정 row key별 `status`·부분 단계, `next_action`·파생 `transition_action`, registry ownership generation과 `attribution_state`, hub lease generation, decision kind를 포함한다. 원시 `state.json` SHA/revision과 `created_at`·`updated_at`·행 timestamp·note·run-log 블록 및 활동 로그는 제외한다.

`stop_hook_active=true` 재진입에서 fingerprint가 직전 차단과 같으면 더 차단하지 않고 `no_progress_same_fingerprint` 진단으로 종료를 허용한다. fingerprint가 달라졌을 때만 다시 차단할 수 있으며 Claude Code의 연속 차단 상한을 넘지 않는다.

## Constraints

- C-1. Stop hook inline Python은 import 가능한 모듈로 추출하고 독립 테스트가 가능해야 한다.
- C-2. worktree 생성과 registry 갱신은 `worktree-tool`만 수행한다. Orca는 기존 worktree에 terminal을 연결할 뿐 별도 checkout을 만들지 않는다.
- C-3. launcher는 공통 lifecycle과 환경별 adapter로 나눈다. OS·terminal 종류를 암묵적으로 추측하지 않는다.
- C-4. OPAL Stop hook 배포 owner는 global `~/.claude/settings.json`의 `_opal_managed` entry 한 곳이다. project/worktree settings에 OPAL Stop evaluator를 등록하지 않고 기존 비-OPAL hook을 보존한다.
- C-5. worktree project settings는 hook 복제 수단이 아니다. 전용 세션에 필요한 project 권한·일반 설정만 provisioning하며, PLAN에서 sparse cone 확장·안전한 복제·installer 중 실제 필요 범위를 확정한다.
- C-6. worktree resolver는 registry에 저장된 exact canonical task만 사용하고 cwd 문자열, worktree 이름, mtime, `updated_at`, 부모 디렉터리 스캔으로 추론하지 않는다.
- C-7. 허브 resolver는 `<hub_root>/tasks/` 직계 태스크만 스캔한 뒤 registry를 대조한다. registry v2의 active canonical이 다른 worktree에 있고 같은 task folder의 허브 사본이 존재하면 `worktree_owned_shadow`로 분류해 강제 후보에서 제외하되 진단에 남긴다. 이 소비자별 제외가 `worktree.md`의 일반 `task_path_ambiguous` 계약을 조용히 약화하지 않도록 관계를 명시한다.
- C-8. 허브 태스크 소유권은 task별 runtime lease로 판정한다. 다른 live session lease는 제외한다. 현재 session lease가 정확히 1개면 평가하고 복수면 전체를 PM 판단 후보로 반환하며, 무소유·만료 lease도 PM 판단 후보에 포함한다. 어느 복수 후보도 최신순으로 임의 선택하거나 무조건 fail-open 하지 않는다.
- C-9. `SessionStart`가 session ID와 cwd를 coordinator에 자동 등록하고 `CLAUDE_ENV_FILE`을 통해 세션 한정 `OPAL_SESSION_ID`를 이후 Bash 호출에 전달한다. worktree exact canonical task는 SessionStart에 자동 claim하고, 허브 canonical task는 pilot activation·state init·첫 상태 전이의 최초 경계에서 이 ID로 현재 session lease를 자동 생성한다. PM의 별도 명령은 요구하지 않으며 명시적 activate/resume/handoff는 override다. 일반 PostToolUse는 ownership을 생성·이전하지 않고 일치하는 기존 lease heartbeat만 갱신한다.
- C-10. Stop 재진입 무진행의 기계적 정의는 동일 session ID와 동일 semantic decision fingerprint다. fingerprint는 파이프라인 전이에 영향을 주는 의미 필드만 사용하고 원시 파일 hash/revision·시각·note·run-log/activity 변경을 진행으로 간주하지 않는다. 동일 fingerprint는 재차단하지 않고 변경 때만 재평가하며 Claude Code의 문서화된 연속 차단 상한을 준수한다. 별도 고정 3회 상한은 두지 않는다.
- C-11. 정상 완료·사용자 대기·비활성·동일 fingerprint 통과와 `no_owned_task`, `multiple_hub_tasks`, `worktree_owned_shadow`, `foreign_owner`, `invalid_registry`, `invalid_state`, `launch_failed`를 구조화 결과로 구분한다. `foreign_owner`는 현재 Stop을 통과시키되, global `PreToolUse` ownership guard가 등록 worktree의 파일·Git 상태를 바꾸는 도구를 차단한다. 읽기 전용 도구는 허용하고, mutation 폐쇄 목록과 Bash 판정 경계는 PLAN에서 고정한다.
- C-12. worktree lifecycle은 registry meta의 `execution_ownership`과 기존 `attribution_state` 허용 조합으로만 표현하고 `worktree-tool`이 원자적으로 쓴다.
- C-13. launch와 prompt receipt 전에는 handoff owner를 이전하지 않는다. 별도 handoff 없이 수동으로 열린 worktree 세션도 SessionStart에서 자동 claim을 시도하며, 기존 live owner가 있으면 `foreign_owner`로 거부한다. 실패 복귀는 generation 증가와 함께 원자적으로 수행하여 dual writer와 orphan ownership을 남기지 않는다.
- C-14. worktree 세션은 공유 Git objects/refs를 통해 `main` 조회·diff·commit을 수행하되 허브 working tree의 포괄적 읽기/쓰기를 전제로 하지 않는다.
- C-15. Claude session ID, Orca terminal handle 등 adapter 실행 식별자는 canonical ownership과 분리하되 registry lifecycle에서 추적 가능해야 한다.
- C-16. 구현은 설치 소스를 수정하고 installer/sync로 global hook을 배포한다. `~/.opal`과 사용자 settings 산출물을 직접 편집하지 않는다.
- C-17. 등록된 전용 worktree의 `agentic` 세션은 필수 Gate·검증이 통과하고 사용자 판단이 필요한 미해결 사항이 없는 안정 경계에서 소유 변경만 체크포인트 커밋하고 SHA를 lifecycle에 기록한다.
- C-18. `interactive`은 기존 각 단계 사용자 승인 뒤 해당 단계 체크포인트를 커밋한다. `semi-agentic`은 PLAN-equivalent 승인 뒤 명세 체크포인트를 커밋하고, EXECUTE·TEST에서는 자율 커밋하지 않으며, CLOSE 진입 승인 뒤 누적 구현·테스트 체크포인트와 승인된 CLOSE/finalize 범위의 최종 체크포인트를 수행한다. 새 사용자 Gate를 추가하지 않는다.
- C-19. 보정 가능한 이슈는 권한 범위에서 수정·재검증하고 통과하면 사용자 보고로 실행을 끊지 않는다. unresolved 실패, 계약 충돌, 사용자 선택, 재시도 한도 초과만 기존 경계를 따른다.
- C-20. 자율 권한은 소유 worktree branch의 로컬 체크포인트까지다. 허브·`main`·기본 브랜치 commit, merge·push·배포, rebase·reset·amend와 worktree 제거는 모드와 무관하게 사용자 승인 없이는 수행하지 않는다.
- C-21. 하네스 owner 문서와 그 미러(`guards.md`, `task-process.md`, agentic/semi-agentic/interactive 계약, `opal-self-pm`, `docs/CONVENTIONS.md`)는 C-17~C-20과 정합해야 한다.
- C-22. 실제 Claude TUI의 cwd·global hook 적용 확인과 `opal-agent --provider claude --cwd <worktree_root> -p` 경로의 Stop hook·session ID 전달은 수동 E2E로 격리하고, 자동 회귀는 adapter fake process와 캡처된 hook payload fixture로 수행한다.
- C-23. global hook 배포는 SessionStart·PreToolUse ownership guard·PostToolUse·Stop·SessionEnd 이벤트를 함께 관리한다. SessionEnd 누락은 lease TTL로 복구하며 installer/source parity가 다섯 이벤트를 검증한다.

## Non-goals and follow-up boundary

- blocker 사유를 폐쇄 목록으로 제한하는 계약과 `state-tool resume`의 원자적 복귀 명령은 별도 후속 태스크다. 이 태스크는 소유권·전용 세션·Stop 재평가를 해결하지만 Task 137의 blocker/resume 사고 전체를 단독 종결하지 않는다.
- 기존 fossil 파일을 삭제·정리하는 작업은 범위 밖이다. 단, active worktree 소유 허브 shadow를 Stop 후보에서 판별·제외하는 기능과 회귀 fixture는 이 태스크 범위다.
- OPAL/Orca 외 GUI terminal 제품별 자동화는 범위에서 제외한다.

## Acceptance criteria

- AC-1. `claude-hooks.json` Stop 항목에는 inline `python -c`가 없고 import 가능한 evaluator 모듈 호출만 존재한다.
- AC-2. global settings에는 `_opal_managed` OPAL Stop evaluator가 정확히 1건 있고 project/worktree settings에는 0건이며 기존 비-OPAL hook은 보존된다.
- AC-3. `--wt` handoff와 registry lifecycle이 canonical task, worktree root, adapter·handle, session ID, generation, launch/prompt receipt, 상태와 실패 사유를 저장한다.
- AC-4. worktree 전용 세션의 launch receipt가 cwd를 worktree root로 보고한다. adapter fake process 자동 통합 테스트와 실제 Claude TUI 수동 E2E 절차를 각각 제공한다.
- AC-5. Orca adapter는 기존 OPAL worktree에 Claude TUI terminal을 생성하고 handoff prompt를 제출하며 중복 worktree를 만들지 않는다.
- AC-6. 비-Orca terminal adapter와 `opal-agent --provider claude --cwd <worktree_root>` fallback이 구분되어 동작하고 fallback session ID를 resume에 사용할 수 있다.
- AC-7. `session_launching -> worktree_session_owned`은 launch와 prompt receipt가 모두 있을 때만 성공한다.
- AC-8. launch 또는 prompt 실패는 `launch_failed`를 기록하고 generation을 증가시켜 `hub_owned`로 원자 복귀하며 dual writer·orphan owner가 없다.
- AC-9. worktree Stop resolver는 registry exact canonical task 하나만 평가하고 경로·mtime·최신 state를 추론하지 않는다.
- AC-10. HUB-FOSSIL-AMBIGUOUS fixture에서 active WT-132 registry와 진행 중 허브 사본이 함께 있어도 허브 사본은 `worktree_owned_shadow`로 제외되고 현재 허브 세션을 차단하지 않는다.
- AC-11. closed attribution의 정상 허브 merge 사본은 shadow로 제외하지 않고 canonical hub task로 판정한다.
- AC-12. SessionStart가 session ID·cwd를 자동 등록하고 `CLAUDE_ENV_FILE`에 세션 한정 `OPAL_SESSION_ID`를 영속한다. worktree exact canonical task는 자동 claim하며, hub canonical task는 pilot activation·state init·첫 상태 전이의 최초 경계에서 같은 ID로 별도 PM 호출 없이 lease를 원자 생성한다. 명시적 activate/resume/handoff는 override이고 PostToolUse는 일치 lease heartbeat만 갱신한다.
- AC-13. HUB-TWO-SESSIONS fixture에서 세션 A 소유 task는 세션 B 후보에서 제외되며, 한 세션이 여러 hub task lease를 가질 수 있다.
- AC-14. 현재 세션 소유 후보가 복수이거나 무소유·만료 hub 후보가 있으면 전체 후보와 근거를 PM에 한 번 전달하며 최신 후보 임의 선택·무조건 fail-open을 하지 않는다.
- AC-15. `stop_hook_active=true` 재진입에서 동일 semantic decision fingerprint는 `no_progress_same_fingerprint`로 통과한다. fingerprint는 `current_status`, 안정 row key별 status·부분 단계, `next_action`·`transition_action`, registry·lease 의미 generation과 decision kind만 사용하고 원시 state hash/revision·timestamp·note·run-log/activity는 제외하며, 의미 상태 변경만 새 차단을 허용하고 문서화된 연속 차단 상한을 준수한다.
- AC-16. 정상 완료·대기·비활성·동일 fingerprint 통과와 모든 C-11 오류·진단 코드가 구분된다.
- AC-17. registry meta의 execution/attribution 허용 조합, 금지 조합, atomic transition과 legacy meta 호환이 계약 테스트를 통과한다.
- AC-18. SAME-WORKTREE-TWO-SESSIONS fixture에서 수동으로 연 두 세션이 SessionStart 자동 claim을 시도하고 첫 세션만 owner가 된다. 두 번째 세션은 `foreign_owner`로 획득이 거부되고 Stop은 비차단 통과하며, 읽기 전용 도구는 허용되지만 파일·Git mutation은 PreToolUse에서 차단된다.
- AC-19. worktree 세션에서 공유 Git refs를 사용한 기준선 조회·diff·commit이 가능하고 허브 working tree write 없이 동작한다.
- AC-20. `agentic` 전용 worktree는 검증된 안정 경계에서 소유 변경만 자율 커밋하고 SHA를 lifecycle에 기록한 뒤 다음 단계로 계속한다.
- AC-21. `interactive`은 기존 단계 승인 뒤 커밋한다. `semi-agentic`은 PLAN 승인 체크포인트, CLOSE 진입 승인 뒤 누적 EXECUTE·TEST 체크포인트와 승인된 CLOSE/finalize 최종 체크포인트만 만들며 EXECUTE·TEST에 새 사용자 Gate를 추가하지 않는다.
- AC-22. 사용자 승인 없이 허브·`main`·기본 브랜치 commit, merge·push·배포, 이력 재작성 또는 worktree 제거를 수행할 수 없다. 사용자 승인 merge 뒤에만 허브 귀속·최종 상태를 처리한다.
- AC-23. 보정 후 검증을 통과한 이슈는 비차단 기록만 남기고 진행하며 unresolved blocker만 기존 에스컬레이션 경계를 따른다.
- AC-24. `guards.md`, `task-process.md`, agentic/semi-agentic/interactive 모드 문서, `opal-self-pm`과 `docs/CONVENTIONS.md`가 AC-20~23과 일치하고 상충하는 자동 커밋 금지 문구가 활성 문서에 없다.
- AC-25. WT-127/132/138, HUB-0, HUB-MULTI, HUB-FOSSIL-AMBIGUOUS, HUB-TWO-SESSIONS, SAME-WORKTREE-TWO-SESSIONS, automatic hub claim, foreign owner, launch 실패, prompt 실패, Stop 동일/의미 변경/로그만 변경 fingerprint와 모드별 commit 시나리오가 fixture 기반 통합 테스트로 검증된다.
- AC-26. resolver, settings installer, SessionStart registration, PreToolUse ownership guard, hub lease, heartbeat·SessionEnd release·TTL recovery, fingerprint store, registry lifecycle, Orca/generic launcher와 Stop 판정 로직의 독립 테스트가 통과한다.
- AC-27. 기존 OPDS 상태 전이, worktree canonical/attribution, hook 병합, installer/source parity 회귀가 통과한다.
- AC-28. global hook source와 installer가 SessionStart·PreToolUse·PostToolUse·Stop·SessionEnd를 배포하고 기존 비-OPAL hook을 보존하며 source/install parity 검증을 통과한다.
- AC-29. 실제 Claude TUI와 `opal-agent --provider claude --cwd <worktree_root> -p` 수동 E2E에서 cwd, session ID 전달, global Stop hook 발화를 각각 확인한다.

## Related documents

- `opal/core/references/harness/worktree.md`
- `opal/core/references/harness/modes.md`
- `opal/core/references/harness/guards.md`
- `opal/core/references/harness/task-process.md`
- `opal/core/references/opal-harness-agentic.md`
- `opal/core/references/opal-harness-semi-agentic.md`
- `opal/core/references/opal-harness-interactive.md`
- `opal/skills/opal-self-pm/SKILL.md`
- `docs/CONVENTIONS.md`
- `opal/core/hooks/claude-hooks.json`
- `.opal/worktree.json`
- `opal/tools/opal-agent/opal_agent.py`
- [Claude Code hooks guide — SessionStart environment persistence and Stop block cap](https://code.claude.com/docs/en/hooks-guide)
