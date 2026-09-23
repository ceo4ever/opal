---
template: sdlc-v2
---
# PLAN: 모드별 실행 지속성 계약

> 입력: [TASK.md](TASK.md)

## Approach
공통 전이 판정을 먼저 state-tool과 하네스 owner 문서에 세우고, 모든 Pilot이 그 판정을 소비하도록 Pilot 문구와 pipeline CLOSE 구조를 정렬한다. 구현은 source checkout만 수정하며, 설치본은 검증 대상으로만 다룬다.

code-scan 선조회는 전용 domain 결과가 충분하지 않아 `rg`/구조 탐색으로 보강했다. 확인된 핵심 변경 축은 `opal/tools/state-tool/state_tool.py`의 mode/auto-approval/CLOSE 완료 판정, `opal/core/references/harness/*`의 모드·TASK·상태 계약, `opal/skills/opal-pilot-*/**`의 단계 보고 문구와 pipeline JSON, `opal/core/hooks/claude-hooks.json`의 Stop 통지 전용 구조다. `opal/bootstrapper/**`에서는 Stop/resume 연결 후보가 확인되지 않았으므로 변경 대상에서 제외하고, 플랫폼별 실제 집행은 hook/adapter 설치 경로와 비지원 계약 테스트로 한정한다.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| 전이 결과를 단일 vocabulary로 고정 | 전 단계 경계의 실행 결과는 `continue`, `await_user`, `blocked`, `complete` 중 하나다. `progress_report`는 통지일 뿐 전이를 멈추지 않고, `decision_request`만 `await_user`를 만든다. | TASK AC-1/AC-2와 `opal/core/references/opal-harness-agentic.md:66-89`의 agentic 자동 통과 계약을 공통화한다. |
| mode 판정은 state-tool SSOT | `state-tool resolve-mode`가 정한 mode와 전이 helper의 구조화 출력만 다음 행동을 결정한다. 스킬 산문, 보고 문구, project brief는 전이 판정 근거가 아니다. | [MUST] `docs/CONVENTIONS.md` §State 관리: `파이프라인 행 상태(⬜/🔄/✅) 변경은 ~/.opal/tools/state-tool/run.sh로만 수행한다. state.json 직접 편집 금지`; `docs/ARCHITECTURE.md:71`은 resolver 응답을 SSOT로 둔다. |
| 모드별 기본 행동 | interactive는 단계 경계마다 `await_user`; semi-agentic은 Pilot별 autonomy boundary 이전만 `await_user`이고 이후는 예외 없으면 `continue`; agentic은 공통 예외와 CLOSE 진입 외에는 `continue`다. | TASK C-1~C-3. 기존 `can_auto_approve_user_confirmation()`와 `MODE_BOUNDARY_STAGES`는 이 결정을 소비하는 구현 지점이다(`opal/tools/state-tool/state_tool.py:1324-1338`, `:2672-2680`). |
| 공통 예외 | 파괴적·비가역적·외부 영향 행위, 중대한 모호성, 재시도 한도 초과, 사람 전용 검증·권한, CLOSE 진입 승인은 mode와 무관하게 `await_user` 또는 `blocked`다. 커밋은 사용자 명시 요청 전에는 수행하지 않는다. | TASK C-3/C-6, `docs/CONVENTIONS.md:212`, `opal/core/references/opal-harness-agentic.md:153`. |
| Track 변경은 비차단 제안 | `opd`/`opds` 전환 제안은 `progress_report`로 남기고 현재 트랙을 계속한다. 현재 트랙으로 실행 불가능할 때만 `blocked` 또는 `decision_request`를 낸다. | TASK AC-7. `docs/PROJECT.md`의 트랙 라우팅 설명은 자동 전환 금지와 현재 트랙 유지 fail-safe를 이미 가진다. |
| CLOSE 완료는 tail 완료 뒤 | `close.done_md`는 CLOSE의 첫 산출물 행일 뿐 전체 완료가 아니다. DONE.md, 문서 동기화, brain ingest, 회고, worktree finalize/attribution 등 필수·조건부 tail 행이 모두 끝난 뒤 마지막 CLOSE 행만 `complete`/`completed_unmerged`를 만든다. | TASK AC-5. 현재 모든 주요 pipeline JSON은 CLOSE가 `close.done_md` 단일 행이며, state-tool은 CLOSE 마지막 행 완료 즉시 `completed_unmerged`로 둔다(`opal/tools/state-tool/state_tool.py:2773-2786`). |
| 플랫폼 차이는 어댑터만 소유 | 응답 종료 방지나 Stop guard는 플랫폼 어댑터·훅 계층에서만 구현하고, 스킬·에이전트 본문에는 플랫폼 조건문을 넣지 않는다. 지원 불가 플랫폼은 state-tool의 next action/resume 정보로 동일한 재개 계약을 보존한다. | [MUST] `docs/CONVENTIONS.md` §플랫폼 분기 격리: `스킬·에이전트 본문에 플랫폼 조건문을 추가하지 않는다`; Claude Stop hook은 현재 통지만 수행한다(`opal/core/hooks/claude-hooks.json:33-43`). |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. 전이 계약 RED 테스트 | opal-test-agent | `opal/tools/state-tool/tests/test_mode_transition_contract.py`, `scripts/tests/task136_mode_transition_contract.py` | 3 modes x 주요 단계 경계, `progress_report`/`decision_request`, TASK 직후 continue, interruption resume, CLOSE tail resume, oppl 포함 cross-Pilot pipeline conformance를 실패하는 테스트로 고정한다. 구현 전 `state-tool` 공개 CLI와 pipeline JSON fixture만 호출하고 `state.json` 손편집·mock을 쓰지 않는다. | 없음 | P1 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, C-1, C-2, C-3, C-4, C-5 |
| W-2. state-tool 전이 엔진과 CLOSE 완료 판정 | opal-task-agent | `opal/tools/state-tool/state_tool.py`, `opal/tools/state-tool/README.md`, `opal/tools/state-tool/schema/state.schema.json` | `transition_action` 계산 helper와 CLI/JSON 출력 필드를 추가하고, `advance`/`mark`/`show`가 다음 행동을 구조화해서 반환하게 한다. `can_auto_approve_user_confirmation()`은 새 helper를 소비하게 정리하고, CLOSE 마지막 행이 아닌 명시 final row에서만 `complete`/`completed_unmerged`가 되도록 바꾼다. | W-1 | P2 | AC-1, AC-2, AC-4, AC-5, C-1, C-2, C-3, C-4, C-5 |
| W-3. 공통 하네스·Pilot 문구 정합화 | opal-task-agent | `opal/core/references/harness/modes.md`, `opal/core/references/harness/state.md`, `opal/core/references/harness/task-process.md`, `opal/core/references/opal-harness-agentic.md`, `opal/core/references/opal-harness-semi-agentic.md`, `opal/core/references/opal-harness-interactive.md`, `opal/skills/opal-pilot-dev/SKILL.md`, `opal/skills/opal-pilot-dev-short/SKILL.md`, `opal/skills/opal-pilot-dev-wireframe/SKILL.md`, `opal/skills/opal-pilot-project/SKILL.md`, `opal/skills/opal-pilot-write-tech/SKILL.md`, `opal/skills/opal-pilot-data-design/SKILL.md`, `opal/skills/opal-pilot-gc/SKILL.md`, `opal/skills/opal-pilot-sdd/SKILL.md`, `opal/skills/opal-pilot-project-dev/SKILL.md`, `opal/skills/opal-pilot-project-loop/SKILL.md`, `opal/skills/opal-pilot-dev/references/track-routing.md`, `opal/skills/opal-pilot-dev/references/track-escalation.md` | 단계 보고 문구를 `progress_report`와 `decision_request`로 나누고, `task-process.md:83`류의 무조건 승인 요청 표현을 mode-aware 전이 소비로 교체한다. Track 변경은 비차단 제안으로 정리하며, 기존 agentic 자동 전이와 CLOSE 승인 예외가 충돌하지 않게 oppl을 포함한 각 Pilot의 단계 절을 맞춘다. | W-2 | P3 | AC-1, AC-2, AC-7, C-1, C-2, C-3, C-4, C-6 |
| W-4. Pilot pipeline CLOSE tail 행 확장 | opal-task-agent | `opal/skills/opal-pilot-dev/references/pipeline.json`, `opal/skills/opal-pilot-dev/references/pipeline-short.json`, `opal/skills/opal-pilot-dev-wireframe/references/pipeline.json`, `opal/skills/opal-pilot-project/references/pipeline.json`, `opal/skills/opal-pilot-write-tech/references/pipeline.json`, `opal/skills/opal-pilot-data-design/references/pipeline.json`, `opal/skills/opal-pilot-gc/references/pipeline.json`, `opal/skills/opal-pilot-sdd/references/pipeline.json`, `opal/skills/opal-pilot-project-dev/references/pipeline.json`, `opal/skills/opal-pilot-project-loop/references/pipeline.json`, `opal/tools/state-tool/tests/test_state_tool.py` | oppl을 포함한 각 pipeline의 CLOSE를 `DONE.md 생성` 이후 문서 동기화, brain ingest, 회고/개선후보, worktree finalize/attribution, final state row로 분해한다. 조건부 행은 pipeline JSON의 기존 조건 표현을 재사용하고, 마지막 행만 완료 상태를 만들도록 W-2 계약과 맞춘다. CLOSE tail로 행 수가 달라진 Group A 실 pipeline fixture의 기대 row count를 보정한다. | W-2 | P3 | AC-4, AC-5, AC-7, C-5, C-6 |
| W-5. 플랫폼 Stop guard와 설치 산출물 검증 | opal-task-agent | `opal/core/hooks/claude-hooks.json`, `scripts/install-mac.sh`, `scripts/install/windows.ps1`, `scripts/tests/test_archive_contents.sh`, `scripts/tests/test_agent_adapter_fields.sh` | Claude Stop hook에서 `transition_action=continue` 상태의 응답 종료를 감지·경고 또는 재개 안내하도록 연결하고, install 스크립트의 hooks 병합 경로가 해당 source를 배포하는지 검증한다. bootstrapper에는 Stop/resume 구현 지점이 없으므로 변경하지 않으며, Cursor/Gemini/Codex 등 현재 hook 집행 지점이 없는 플랫폼은 state-tool next action/resume 정보를 보존하는 비지원 계약과 테스트로 다룬다. 플랫폼별 조건은 어댑터·설치 계층에만 둔다. | W-2 | P3 | AC-6, AC-7, C-3, C-4, C-6 |
| W-6. 프로젝트 문서와 기존 회귀 정합 정리 | opal-task-agent | `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md`, `docs/PROJECT.md`, `scripts/tests/task134_mode_persistence_contract.py` | 새 전이 계약, CLOSE tail, 플랫폼 어댑터 경계를 프로젝트 문서에 반영한다. 기존 task134 모드 보존 회귀가 신규 전이 계약과 충돌하지 않도록 정합 검증만 수행하고, `scripts/tests/task136_mode_transition_contract.py` 수정 책임은 W-1에만 둔다. | W-3, W-4, W-5 | P4 | AC-1, AC-3, AC-4, AC-6, AC-7, C-4, C-6 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. 기존 in-flight 태스크가 단일 CLOSE 행 pipeline을 보유 | 새 state-tool이 과거 state.json을 닫지 못하거나 완료 판정을 다르게 낼 수 있다. | 진행 중 태스크 CLOSE 차단 또는 next action 혼선 | W-2에서 legacy 단일 CLOSE 행 호환 분기를 두고, W-1/W-6에 기존 fixture 회귀를 포함한다. |
| H-2. Stop guard가 플랫폼별로 지원 수준이 다름 | `continue` 상태에서 실제 응답 종료 방지가 일부 플랫폼에서 동작하지 않을 수 있다. | agentic 실행이 다시 멈춘 것처럼 보일 수 있음 | W-5는 강제 방지가 가능한 곳과 안내/재개 정보 보존만 가능한 곳을 어댑터 계약으로 분리한다. |
| H-3. 문서 문구만 바꾸고 도구 출력이 따라오지 않음 | 산문은 continue라 쓰지만 state-tool next action이 await_user로 남는 drift가 생긴다. | TASK 직후 정지 문제 재발 | W-2를 선행시키고 W-3/W-4는 state-tool 구조화 출력 소비만 허용한다. |

## Release and recovery

- 적용 순서: P1 RED 테스트 작성 후 P2 state-tool 구현, P3 Pilot/문서/어댑터 병렬 정합화, P4 문서·회귀 정리 순서로 진행한다.
- 검증 범위: `~/.opal/tools/state-tool/run.sh verify <task-folder> --plan-contract-check`, `~/.opal/tools/state-tool/run.sh verify <task-folder> --code-scan-citation-check`, 신규 task136 테스트, 기존 `test_mode_resolution.py`/`test_state_tool.py`/`task134_mode_persistence_contract.py`, oppl 포함 전체 Pilot pipeline JSON schema·CLOSE tail conformance 검증, install/archive 관련 스크립트 테스트를 포함한다.
- 실측 경계: agentic 실행의 각 단계 완료 후 state-tool 출력이 `transition_action=continue`이면 PM 응답은 중간 보고 뒤 다음 단계 툴 호출로 이어져야 한다. `await_user`는 `decision_request` 증거가 있을 때만 허용한다.
- 실패 시: source 변경만 되돌릴 수 있게 커밋 없이 작업한다. 설치본 검증이 실패하면 source는 유지하고 install/archive 산출물 갱신 또는 adapter 테스트 보강을 별도 수정으로 처리한다.
