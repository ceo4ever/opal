# TASK: op-scenario-gate 목표-커버 게이트 확산 1차 (opds·opsdd)

> 작성일: 2026-07-23 | 작업 유형: 개선(확산) | 적용 스킬: opd | 모드: 미정(권고 semi-agentic)
> 입력: 073 완료 산출물 + 이 세션 4-pilot 확산 검토 결론
> 출력: TASK.md

## 작업 목표

073에서 구축한 **목표-커버 게이트 공유 컴포넌트**(scenario-gate.md SSOT · op-scenario-gate 스킬 · test-tool scenario-coverage-check · opal-evaluator-agent scenario-rubric phase)를 **opds·opsdd에 확산 적용**한다. 신규 tool/agent/pilot 없이 **pilot별 정규화 변환기 + 게이트 배선만** 추가한다.

## 배경 (이 세션 4-pilot 확산 검토 결론)

| pilot | 판정 | 근거 |
|-------|------|------|
| opds | ✅ 적용(1차) | opd와 동형(마크다운 TEST-SCENARIO, op-dev-plan 흡수). 접합 최저 난도 |
| opsdd | ✅ 적용(1차) | Phase 2 REVIEW가 **PM 자기검증(self-confirming) + 수동 커버리지** → 게이트가 정확히 그 약점을 메움. 접합 지점(PM 직접 작성)이 opd STEP 3.5와 동형 |
| oppd | ⏸ 2차 유예 | 자율·무인이라 가치는 최고이나 action-agent 내부 파이프라인 접합이라 복잡. op-dev-test-scenario(073 fix) 사용으로 부분 완화됨 |
| oppl | ❌ 제외 확정 | 이미 도구-게이트(backlog coverage-check + scenario-conformance) + 독립 평가자(D6·G) + 산출 기반 목표체크 보유. 적용 시 3중 커버리지·SSOT 훼손 |

- 073 사건 근거: 070에서 핵심 목표 검증 시나리오가 도출조차 안 된 채 완료 처리 → 목표-커버 게이트로 tool-gated 집행.

## 명확화 결과

> TASK 4요소를 잠근다.

| 요소 | 확정값 | 미확정 | 의존 사실 |
|------|--------|--------|----------|
| 목표 | op-scenario-gate를 opds·opsdd에 접합. 073 공유 컴포넌트 재사용, pilot별 정규화 변환기 + 게이트 배선만 신규 | - | 073 DONE.md, op-scenario-gate/SKILL.md §Step 2 |
| 범위 | 포함: (opds) op-dev-plan TEST-SCENARIO 작성 지점 게이트 접합 + pipeline 게이트 행 / (opsdd) Phase 2 REVIEW 게이트 접합 + 수동 FR/AC/EC 커버리지→scenario-coverage-check 대체 + PM 자기검증→독립 evaluator / op-scenario-gate Step 2 pilot 변환기(opds·opsdd) 추가. 제외: oppl(제외 확정)·oppd(2차)·새 tool/agent/pilot·scenario-gate.md 규칙 변경 | - (확정: opsdd 커버리지 전면 대체 — 2026-07-23 agentic PM DECISION) | 이 세션 검토 표 |
| 제약 | 073 공유 컴포넌트 재사용(신규 tool/agent/pilot 0) / Producer≠Evaluator·tool-gated 유지 / `~/.opal` 직접수정 금지 / opd 1차 접합 무손상 / opsdd verify-guide 커버리지 대체 시 SPEC 구조검증(S-1~S-6) 존치 / 커밋·install 지시 시만 | - | 073 제약 계승 |
| 완료기준 | 각 pilot에서 게이트 미통과 시 다음 단계 진입 차단 실증 + 자기적용 음성/수렴 실증 + 회귀 0 | - | - |

**미확정 잠금 대상**: opsdd 커버리지 대체 방식 — (권고) verify-guide의 수동 AC/EC 커버리지 확인을 scenario-coverage-check로 **전면 대체**하고 SPEC 구조검증(S-1~S-6, 별개 관심사)은 존치. PLAN 전 캡틴 확정.

## 요구사항

- [ ] **R-1 op-scenario-gate Step 2 pilot 변환기 확장** — `pilot=opds`/`pilot=opsdd` 분기 추가. opds=TEST-SCENARIO.md(§1/§4, opd 변환기 재사용), opsdd=TEST-SCENARIOS.md(AC↔TS 매핑) → 정규화 페이로드. AC: 각 pilot 호출 시 `{goal,R[],F[],H[],scenarios[]}` 정확 생성.
- [ ] **R-2 opds 접합 (+ producer 확립)** — (a) **producer 확립**: `opal-pilot-dev-short/SKILL.md` STEP 2 보강 — op-dev-test-scenario 통일 형식을 명시 참조하여 opds가 TEST-SCENARIO.md를 **확실히 생성**하도록 함(발견① 해소, 캡틴 결정 옵션1). **`op-dev-plan/SKILL.md`(opd 공용)은 미접촉 → opd 무영향.** (b) **배선**: opds가 TEST-SCENARIO 작성 후 op-scenario-gate 통과해야 EXECUTE 진입, opds pipeline.json 게이트 행 추가(opd 패턴 동형). AC: opds가 producer_artifact 생성 보장 + 게이트 미통과 시 EXECUTE 진입 구조적 차단.
- [ ] **R-3 opsdd 접합** — Phase 2 REVIEW에서 TEST-SCENARIOS.md 작성 후 op-scenario-gate 호출, verdict:pass 후에만 DESIGN(Phase 3) 진입. **독립 evaluator로 self-confirming 해소**. AC: REVIEW self-confirming 제거 + 게이트 미통과 시 DESIGN 차단.
- [ ] **R-4 opsdd verify-guide 정합** — 수동 FR/AC/EC 커버리지 확인 절을 scenario-coverage-check(결정론)로 대체, SPEC 구조검증(S-1~S-6) 존치. 변경이력 행.
- [ ] **R-5 회귀** — opd 1차 접합·scenario-gate.md·test-tool·evaluator·기존 opds/opsdd 파이프라인 무손상. AC: 전 스위트 PASS + 회귀 0.
- [ ] **R-6 자기적용 실증** — opds·opsdd 각각(또는 대표 1 pilot 실증 + 나머지 계약 검증) 목표 시나리오 누락→FAIL / 복원→PASS 실증.

## 제약 조건

- 신규 컴포넌트 0 — 073 공유 컴포넌트(SSOT/스킬/도구/에이전트 phase) 재사용, pilot 변환기+배선만 추가.
- Producer≠Evaluator·tool-gated 2증거 유지(scenario-gate.md §4·§6 계승).
- `~/.opal/` 직접 수정 금지 — 프로젝트 소스만, install 별도.
- opd 1차 접합·oppl 무변경(제외 확정).
- 커밋·install은 사용자 명시 지시 시만. 변경이력·@header 준수.

## 기술 스택

- Markdown(스킬·SSOT·verify-guide) + pipeline.json(opds), 기존 test-tool·op-scenario-gate·evaluator 재사용. Python 신규 없음(scenario-coverage-check는 073에서 이미 pilot-중립).

## 관련 문서

| # | 유형 | 문서 | 경로 | 참조 이유 |
|---|------|------|------|----------|
| D-1 | 설계 | op-scenario-gate SKILL | `opal/skills/op-scenario-gate/SKILL.md` | Step 2 변환기 확장 대상(pilot 분기) |
| D-2 | 설계 | scenario-gate.md SSOT | `opal/core/references/harness/scenario-gate.md` | 규칙 계승(변경 대상 아님) |
| D-3 | 설계 | 073 DONE | `tasks/073-260723-opd-시나리오-목표커버리지-루프/DONE.md` | 공유 컴포넌트·확산 근거 |
| D-4 | 설계 | opds SKILL | `opal/skills/opal-pilot-dev-short/SKILL.md` | opds 접합 지점 |
| D-5 | 설계 | op-dev-plan SKILL | `opal/skills/op-dev-plan/SKILL.md` | opds가 TEST-SCENARIO 흡수 작성하는 실제 지점 |
| D-6 | 설계 | opsdd SKILL | `opal/skills/opal-pilot-sdd/SKILL.md` | opsdd Phase 2 REVIEW 접합 지점 |
| D-7 | 설계 | opsdd verify-guide | `opal/skills/opal-pilot-sdd/references/verify-guide.md` | 커버리지 대체 대상 |
| D-8 | 설계 | opd 접합 선례 | `opal/skills/opal-pilot-dev/SKILL.md` (STEP 3.5) + `references/pipeline.json` | opds 게이트 행·배선 패턴 동형 참조 |
