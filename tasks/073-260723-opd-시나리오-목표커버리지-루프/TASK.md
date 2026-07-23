# TASK: TEST-SCENARIO 목표-커버리지 루브릭 게이트 루프 (공유 컴포넌트, opd 선적용)

> 작성일: 2026-07-23 | 작업 유형: 개선 | 적용 스킬: opd | 모드: semi-agentic
> 입력: 사용자 요청 (2026-07-23 대화 — 070 회고에서 도출된 TEST-SCENARIO 근거 결함)
> 출력: TASK.md

## 작업 목표

TEST-SCENARIO 단계를 **"태스크 목표의 최종 달성을 검증하는가"**로 재정의하고, 루브릭 채점 기반의 **작은 수렴 루프**(작성 → 커버리지 도구 게이트 → 독립 평가자 루브릭 채점 → 미달 시 재작성)를 **공유 컴포넌트**로 구현한다. 1차는 opd에 선적용하며 공유 컴포넌트·정규화 계약을 완성한다.

## 배경

- 070에서 핵심 목표("`--row`→key 채택")가 라이브에 반영 안 된 채 완료 처리됐고, 캡틴이 배포 후 테스트에서 지적했다.
- 근본 원인: TEST-SCENARIO가 PLAN §리스크 가설 표(파괴 관점)만을 도출 엔진으로 쓰고(`~/.opal/skills/op-dev-test-scenario/references/test-scenario-guide.md:13,20-29`), 목표 달성(채택 관점)이 도출·커버리지 게이트에 없다.
- 커버리지 완전성 검사(§4)가 AC·가설 커버리지만 재고 목표 커버리지를 재지 않아 거짓 초록불을 준다(`op-dev-test-scenario/SKILL.md:160-163`).

## 배경 분석 (대화에서 도출)

- 시나리오 작성 pilot은 5종이며 방식이 상이: opd(전용 스킬)·opds(PLAN 흡수)·opsdd(REVIEW PM직접+액션에이전트)·oppl(test-tool scenario-* json)·oppd(액션에이전트 내부).
- 미작성 5종(opp·opdw·opgc·opwt·opdd)은 대상 아님.
- 방식이 흩어져 있어 한 스킬에 박으면 확산 불가 → **정규화 계약 기반 공유 컴포넌트** 필요.
- 재사용 가능 자산: `opal-evaluator-agent`(oppl 설계검토 verdict-only·readonly), `test-tool scenario-*`/coverage-check 패턴, oppl 루프 종료조건.

## 확정된 설계 방향 (대화에서 합의)

1. **작은 수렴 루프**: Producer(작성) → 도구 게이트(커버리지 결정론) → Evaluator(루브릭 판단) → 종료조건 판정 → 재작성 or 탈출.
2. **루브릭 6축**: ① 목표 달성(사용자/운영 계층 검증 시나리오 존재) ② 요구 커버(TASK R·AC) ③ 기능 커버(PLAN F) ④ 리스크 커버(PLAN H) ⑤ 채택/잔존(교체형=구형 잔존0) ⑥ 경계/부정. ②③④=도구 결정론, ①⑤⑥=평가자 판단.
3. **독립 평가자(QA성 게이트)**: 자체검증·PM Gate 아님 — 작성자(PM+캡틴)와 채점자 분리해 self-confirming 차단. 매 반복 유지.
4. **종료조건 3종**: 수렴(커버리지 누락0 AND 루브릭 임계이상) / 반복상한 MAX / 무진전(연속2회 gaps·점수 개선없음) → 캡틴 에스컬레이션.
5. **공유 컴포넌트 = 재사용+최소신규**: 규칙 SSOT 신규 1(`references/harness/scenario-gate.md`) + test-tool 확장(신규 도구 아님) + evaluator 재사용(신규 에이전트 아님) + 얇은 단계 스킬 신규 1(`op-scenario-gate`, 단일 호출 지점). **새 오케스트레이터 pilot 없음**.
6. **상류 동반**: op-task AC 패턴에 "교체형 목표=잔존/채택 기준" 의무 추가(루브릭 ①축이 채점 가능하도록).
7. **범위 1차**: opd 선적용 + 공유 컴포넌트·계약 완성. 확산(oppl→opds/opsdd→oppd)은 후속.
8. **자기적용 검증**: 이 태스크의 TEST-SCENARIO가 루프를 실제로 돌려 누락을 잡는지 실증.

## 명확화 결과

> TASK 4요소를 잠근다. 각 요소는 확정값 또는 명시적 "N/A: <사유>"로 채운다.

| 요소 | 확정값 | 미확정 | 의존 사실 |
|------|--------|--------|----------|
| 목표 | TEST-SCENARIO를 목표-달성 검증으로 재정의 + 루브릭 채점 작은 수렴 루프를 공유 컴포넌트로 구현, opd 선적용 | - | test-scenario-guide.md:13, SKILL.md:160-163 |
| 범위 | 포함: scenario-gate.md(SSOT)·test-tool 커버리지 확장·evaluator 루브릭 모드·op-scenario-gate 단계스킬·opd STEP3.5 접합·op-task AC 패턴·자기적용. 제외: 새 pilot/tool/agent, 나머지 4 pilot 확산, 미작성 5 pilot | - (확정: 1차 opd 선적용만, opds/opsdd/oppl/oppd 확산은 후속) | 대화 §5·§7 |
| 제약 | ~/.opal 직접수정 금지 / Producer≠Evaluator 매반복 / 기계축=결정론·판단축=평가자 / 루프 경계 필수(MAX=3·무진전 연속2회) / 커밋·install 지시시만 / 072(타세션) 파일충돌 회피 | - (확정: 아래 파라미터 잠금) | 하네스 §1 루핑상한 |
| 완료기준 | 아래 요구사항 AC + 자기적용 음성통제(목표 미커버 시나리오 누락 시 루프 FAIL→재작성 유도) 실증 | - | - |

**파라미터 잠금 확정** (2026-07-23, agentic PM DECISION — 캡틴 `//opd --agentic` 승인, 직전 권고안 그대로 채택):
- 반복 상한 MAX = 3
- 커버리지 누락 = 0 (hard gate — 미달 시 즉시 FAIL)
- 루브릭 판단축(①목표달성·⑤채택/잔존·⑥경계/부정) 각 ≥ 1점 (0점 축 없음) AND 평균 ≥ 1.5점 (2점 척도, 0~2)
- 무진전 = 연속 2회 gaps·점수 개선 없음 → 캡틴 에스컬레이션
- 확산 범위 = 1차 opd 선적용만, opds/opsdd/oppl/oppd 확산은 후속 태스크

## 요구사항

- [ ] **R-1 scenario-gate 규칙 SSOT 신설** — `opal/core/references/harness/scenario-gate.md`: 루브릭 6축 정의 + 루프 프로세스 + 정규화 계약(입력=목표·R·F·H·시나리오 / 출력=누락·점수·gaps). AC: 6축·3종료조건·계약이 문서화되고 op-dev-test-scenario가 이를 참조.
- [ ] **R-2 test-tool 커버리지 서브명령 확장** — 요구(R)·기능(F)·가설(H) ↔ 시나리오 매핑 누락을 결정론 판정. AC: 누락 시 FAIL+미매핑 목록, 완전 시 ok. 신규 도구 아님(test-tool 확장).
- [ ] **R-3 opal-evaluator-agent 시나리오 루브릭 모드** — 판단축(목표달성·채택·경계) verdict-only·readonly 채점. AC: 점수+gaps 구조화 반환, 작성자와 분리.
- [ ] **R-4 op-scenario-gate 단계 스킬 신설** — 커버리지 도구 → 평가자 → verdict+gaps 반환 + 재작성 루프 컨트롤(종료조건 3종). AC: 5 pilot이 단일 호출로 재사용 가능, 경계 있는 종료.
- [ ] **R-5 opd STEP 3.5 접합** — TEST-SCENARIO 작성 후 op-scenario-gate 통과해야 EXECUTE 진입. AC: 게이트 미통과 시 EXECUTE 차단.
- [ ] **R-6 op-task AC 패턴 보강(상류)** — 교체형 목표 감지 시 AC에 잔존0·채택 기준 의무. AC: op-task/SKILL.md AC 가이드에 패턴 추가.
- [ ] **R-7 단위 테스트** — R-2 test-tool 신규 서브명령 테스트 코드 + 회귀 0. AC: 전체 스위트 PASS.
- [ ] **R-8 자기적용 실증** — 이 태스크 TEST-SCENARIO에서 목표-커버 시나리오를 의도적으로 누락시켰을 때 루프가 FAIL→재작성 유도(음성 통제) + 정상 수렴 둘 다 실증.

## 제약 조건

- `~/.opal/` 직접 수정 금지 — 프로젝트 소스만, install 별도.
- Producer≠Evaluator 매 반복 유지 (self-confirming 차단).
- 루프 무한 차단: 종료조건 3종 필수, 하네스 §1 루핑 상한과 정합.
- 타 세션 072(state-tool STATE.md 다음액션)와 파일 접점 주의 — 충돌 회피.
- 커밋·install은 사용자 명시 지시 시만. 변경이력·@header 규칙 준수.

## 기술 스택

- Python(test-tool 확장), 기존 test-tool·evaluator-agent·harness 참조 체계, Markdown(SSOT·스킬)

## 관련 문서

| # | 유형 | 문서 | 경로 | 참조 이유 |
|---|------|------|------|----------|
| D-1 | 설계 | op-dev-test-scenario SKILL | `~/.opal/skills/op-dev-test-scenario/SKILL.md` | 접합 대상·현행 근거 |
| D-2 | 설계 | test-scenario-guide | `~/.opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | 도출 엔진 결함 근거 |
| D-3 | 설계 | opal-evaluator-agent | `opal/agents/opal-evaluator-agent/AGENT.md` | 재사용 대상(루브릭 모드) |
| D-4 | 소스 | test-tool | `opal/tools/test-tool/` | 커버리지 서브명령 확장 대상 |
| D-5 | 설계 | 070 DONE·AGENTIC-LOG | `tasks/070-260720-opd-태스크스텝-키주소-1차/` | 결함 사례·회고 근거 |
| D-6 | 설계 | opal-pilot-dev SKILL | `opal/skills/opal-pilot-dev/SKILL.md` | STEP 3.5 접합 |
