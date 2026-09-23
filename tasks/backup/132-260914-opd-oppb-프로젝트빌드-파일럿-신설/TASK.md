---
template: sdlc-v2
---
# TASK: OPPB 프로젝트 빌드 Pilot 신설

## Problem

규모 있는 프로젝트를 실행할 때 현행 프로젝트 Pilot(OPPD)은 PM이 대화를 재개해야만 워커 결과가 회수된다. 사용자가 계속 붙어 있어야 진행되므로 게이트 사이 무인 실행이 성립하지 않는다.

또한 액션마다 전체 문서 파이프라인(PLAN·QA·TEST-SCENARIO·EXECUTE·VERIFY·TEST)과 별도 worktree·branch를 만들어, 실제 구현보다 준비·정리 비용이 커진다. 분할 단위도 레이어 중심이라 사용자가 끝까지 쓸 수 있는 기능 단위로 완결되지 않는다.

수렴형 프로젝트는 OPPL이 담당하지만, **이미 확정된 실행 계약을 무인으로 소화하는 Pilot**은 없다.

## Proposed outcome

`//oppb`를 호출하면 프로젝트 worktree 하나에서 capability 단위 미니 태스크가 연속 실행되고, 사용자는 §11이 정한 게이트에서만 호출된다.

사용자가 관찰하는 결과는 다음과 같다.

- INTENT 승인 이후 CLOSE 직전까지 재촉·강제 재개 없이 진행된다.
- 충돌하지 않는 capability 두 개가 실제로 동시에 실행된다.
- 미니 태스크마다 worktree·branch·OPAL 번호·문서 파이프라인이 생기지 않는다.
- 각 capability는 accepted 전에 독립 검증 증거를 남긴다.
- MEMORY·brain은 프로젝트 완료 후 한 번만 반영된다.

기존 `//oppd`·`//oppl`·`//opsdd`는 동작이 바뀌지 않는다.

## Affected users and systems

- 대상 사용자: OPAL로 규모 있는 프로젝트를 실행하는 소유자.
- 신규 자산: `opal-pilot-project-build`(alias `oppb`) 스킬과 `pipeline.json`, `oppb-runtime-tool`, `opal-capability-agent`.
- 확장 자산: `opal-agent`(공용 attempt runtime), `opal-plan-agent`(project-slice profile), `opal-evaluator-agent`(acceptance phase), `opal-test-agent`, `op-gc-security`·`op-gc-convention` 호출 adapter, `op-scenario-gate` normalizer.
- 동기화 대상: `opal-skills-registry.json`, `agents.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md`, 설치·배포 스크립트.
- 범위 제외: OPPD 폐기, `opal-task-action-agent` 제거, OPPD 대비 성능 benchmark. 실사용 판정 뒤 별도 태스크가 소유한다.

## Constraints

- C-1: 제안서 `docs/proposals/opal-oppb-project-build-pilot.md`를 설계 SSOT로 삼고, 본문과 어긋나는 구현을 하지 않는다. 변경이 필요하면 제안서를 먼저 고친다.
- C-2: `//oppd`·`//oppl`·`//opsdd`의 스킬·상태·회귀를 변경하지 않는다. 기존 에이전트·레지스트리 항목을 제거하지 않는다.
- C-3: `opal-agent` 확장은 하위 호환을 유지한다. OPPL의 기존 호출 경로가 그대로 동작해야 한다.
- C-4: `~/.opal/` 배포 파일을 직접 수정하지 않는다. 프로젝트 소스를 수정한 뒤 install로 배포한다.
- C-5: 플랫폼 분기(Claude/Cursor/Gemini)를 로직에 넣지 않고 어댑터 계층에만 둔다.
- C-6: 파이프라인 행 상태 변경은 `state-tool`로만 수행한다. `state.json`·`STATE.md` 직접 편집을 하지 않는다.
- C-7: Work item 그룹 G1~G5의 선후 의존을 지킨다. 앞 그룹의 공개 API와 회귀가 통과한 뒤 다음 그룹을 시작한다.
- C-8: 각 그룹 경계에서 회귀 통과 시 허브로 중간 merge하여 main과의 장기 분기를 만들지 않는다.
- C-9: 커밋은 소유자가 명시 요청할 때만 수행한다.

## Acceptance criteria

- AC-1: `//oppb` 호출로 P0~P5 파이프라인이 기동되고, `opal-skills-registry.json`에 `oppb` alias·trigger·pipeline이 등재된다.
- AC-2: 기존 OPAL 프로젝트에서 관련 문서가 충분하면 PRD·TRD 신규 생성이 0건이고, 실행 계약은 `INTENT.md` 하나로 확정된다.
- AC-3: 프로젝트 worktree가 1개이고 미니 태스크 worktree·branch가 0개다.
- AC-4: Environment Probe가 ignored 출력을 정책·한정 입력 hash와 함께 봉인하고, 새 command의 안전한 미봉인 출력은 contract revision당 1 batch만 무과금 재실행되며 반복·위험 경로는 `scope_violation`으로 승격된다.
- AC-5: 봉인된 profile에서 비충돌 미니 태스크 두 개가 실제로 동시 실행되고, 동일 tracked/ephemeral write·contract·runtime resource의 동시 lease가 0건이다.
- AC-6: Runner의 Git 상태 변경과 공유 지식 쓰기가 0건이고, 위반 fixture에서 checkpoint가 거부된다.
- AC-7: 검증 실패 candidate에서 project branch·HEAD·공유 index와 다른 Runner lease path hash 변경이 0건이고 `reset --hard` 호출이 0건이다.
- AC-8: 검증 통과 candidate만 expected parent 비교 뒤 fast-forward되고, stale parent candidate 반영이 0건이다.
- AC-9: 미니 태스크 accepted 전에 schema 검증된 독립 검증 증거가 존재하고, Evidence Tool이 schema·code head·scope hash 불일치 증거를 색인 전에 거부한다.
- AC-10: P3 Supervisor start 이후 사용자 게이트까지 PM tick·수동 재촉·강제 resume이 0건이고, process 상한 포화 시 첫 반환 slot이 Verifier에 배정된다.
- AC-11: Supervisor 비정상 종료·재시작 fixture에서 attempt 재부착 또는 수확 후 자동 tick이 재개된다.
- AC-12: contract revision 변경 fixture에서 직접 consumer만 `needs_revalidation`으로 전환되고 무관 태스크 재검증이 0건이다.
- AC-13: cache adapter conformance suite를 통과한 `replayable` fixture에서 같은 parent의 병렬 candidate 두 overlay가 모두 CAS에 남고, 첫 publication 뒤 stale sibling이 cold fallback 없이 replay된다.
- AC-14: 작은 cache cap·만료 retention fixture에서 active node 삭제가 0건이고 closed node가 LRU로 회수되며, 공간 부족 시 cacheless 강등 또는 `disk_budget_exceeded`가 발생한다.
- AC-15: 프로젝트 완료 전 MEMORY·brain 반영이 0건이고, 최종 허브 merge 후 batch가 정확히 1회 수행된다.
- AC-16: fixture 3종을 cold 3회·warm 3회(총 18회) 무인 실행해 수용 시나리오·전체 회귀·보안·컨벤션이 All Pass이고 신규 차단 결함이 0건이다.
- AC-17: cold/warm 최종 tree와 검증 결과가 동일하고 stale cache 오수용이 0건이며, warm이 cold보다 느린 fixture가 0개다.
- AC-18: OPPB 차단 결함을 주입한 fixture에서 `//oppd` 경로가 영향 없이 정상 완주해 복구 계약이 실증된다.
- AC-19: OPPB 도입 전후로 `//oppd`·`//oppl`·`//opsdd`의 스킬·상태·회귀가 무변경이고, 기존 에이전트·레지스트리 항목 제거가 0건이다.
- AC-20: 신규 owner 에이전트는 `opal-capability-agent` 1종뿐이며, 나머지 전문·검증 역할은 제안서 §4.2의 기존 자산을 재사용한다.
- AC-21: `agents.md`·`docs/PROJECT.md`·`docs/ARCHITECTURE.md`·`docs/CONVENTIONS.md`에 신규 스킬·에이전트와 Pilot 선택 기준이 추가되고, 설치 스크립트가 신규 자산을 배포한다.
