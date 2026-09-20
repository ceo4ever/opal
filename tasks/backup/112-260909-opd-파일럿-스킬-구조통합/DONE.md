# DONE: 파일럿 전용 스킬 내부화와 Dev Pilot 통합

## Outcome

- `op-sdd-spec`, `op-sdd-plan`, `op-sdd-action-plan`을 `opal-pilot-sdd/internal-skills/` 아래로 이동했다.
- 오래된 `op-sdd-verify` 물리 스킬을 제거하고 현행 REVIEW의 S-1~S-6 검증 계약을 `verify-guide.md`에 유지했다.
- `opal-pilot-dev-short` 물리 구현을 제거하고 `opal-pilot-dev` 하나가 호출 name/alias에 따라 Full과 Short profile을 선택하도록 통합했다.
- `//opd`와 `//opds`, `skill=opd|opds`, Full 16행과 Short 11행 상태 계약을 유지했다.
- Short→Full 승격은 PLAN.md 수신 직후 1회만 판단하며, Full→Short TASK 직후 강등과 왕복 재귀 차단을 보존했다.
- `.opal/`과 `tasks/`는 worktree 밖 허브 고정 데이터로 유지하고 `.opal/worktree.json`의 stale `memory` repo 항목을 제거했다.
- 이번 태스크에서 수정한 Markdown의 수기 누적 변경이력을 제거하고 `docs/CONVENTIONS.md`와 프로젝트 `.opal/AGENT.md`를 `opal-doc-standard.md` §4~§5에 정합했다.

## Verification

- TEST-SCENARIO: 9 PASS, 0 FAIL, 0 BLOCKED. S-6 RED 증거 보존.
- scenario coverage: requirements 15, hypotheses 4, scenarios 9, 누락 0.
- skill registry: valid, errors 0, unregistered 0. `//opd`·`//opds`가 같은 canonical Dev Pilot 경로로 해석되고 `//opsdd` 설명이 현행 pipeline과 일치.
- state-tool: 396 passed, 3 skipped, 111 subtests passed. Full 16행·Short 11행 spec/init 계약 통과.
- 설치 cleanup: 11/11 PASS. archive 11/11 PASS, download contract 26/26 PASS.
- worktree 경계 회귀: 관련 2건 PASS. 전체 suite의 기존 `test_s24` 1건 실패는 Task 111 HEAD에서도 동일 재현되어 본 변경 회귀와 분리.
- 컨벤션 재진단: Critical 0, High 0, Medium 0, Low 0.
- 실제 설치본: source와 관련 파일 `cmp` 일치, nested SDD 3종 존재, 제거 대상 top-level 5종 부재, 설치본 `//opd`·`//opds`·`//opsdd` 해석 통과.
- OPAL Console: 최종 자산 복사 후 수동 재기동, `/health` `status=ok` 확인.

## Operational observation

- 최종 재배포에서 선택적 `console scan $HOME`가 장시간 응답하지 않아 자산 복사 완료를 확인한 뒤 설치 세션을 중단했다.
- 스킬·레지스트리 배포는 완료됐고 Console은 별도 기동으로 복구했다. scan 무응답의 시간 제한·탐색 경계 보강은 후속 프레임워크 개선 후보로 분리한다.

## Artifacts

- `TASK.md`, `ANALYSIS.md`, `PLAN.md`, `TEST-SCENARIO.md`, `test-scenario.json`
- `GC-CONVENTION-260909-184729.md`, `GC-CONVENTION-260909-185436.md`
- `AGENTIC-LOG.md`, `state.json`, `STATE.md`
- source worktree: `/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_112`

## Handoff

- worktree와 브랜치는 커밋·머지되지 않은 상태다.
- 머지 또는 PR 처리 후 worktree-tool로 회수해야 한다.
