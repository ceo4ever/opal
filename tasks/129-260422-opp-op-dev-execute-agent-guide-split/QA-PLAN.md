# QA: PLAN — op-dev-execute 에이전트별 지침 구획화 + EXECUTE 디스패치 라우팅 전파

> 검토일: 2026-04-21 | 판정: Pass

## 1. 요약

PLAN.md는 op-dev-execute 스킬을 공통(execute-guide.md) / 전문(execute-specialist-guide.md) / 범용(execute-generalist-guide.md) 3구획으로 분리하고, SKILL.md에 에이전트 이름 기반 매핑 테이블을 삽입하는 설계를 완전히 기술했다. 오케스트레이터 3종(opds/opd/opdw)의 EXECUTE 단계에 PLAN.md §4.2 agent 필드 순회 기반 분배 디스패치 절차를 추가하고, sdd는 동작 정합 근거를 들어 변경 없음으로 확정했다. 127 충돌 회피(opal-task-action-agent/AGENT.md, opal-pilot-project-dev/SKILL.md 수정 금지)와 에이전트 AGENT.md 4종 보호 방침이 §1 파일 테이블에 명확히 선언되어 있다. §2 핵심 설계에 실제 파일 내용 블록이 포함되어 있어 즉시 실행 가능 수준의 명세를 갖추고 있다. 열린 이슈 5개(opdw/sdd 경로·specialist 구조·generalist 이관·버전·하위 호환)가 PLAN 내에서 모두 해소되었다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| GP-1 | 즉시 실행 가능성 | Pass | §2에 파일 내용 블록 수준 설계 명세, §3 Step별 완료 기준·테스트·의존 관계 완비 |
| GP-2 | 의존성 순서 | Pass | Phase 1→2→3→4→5 순서, Step 4가 Step 1~3 의존, Step 5~7이 Step 4 의존, Step 8이 Step 1~7 의존으로 명확히 기재 |
| GP-3 | TASK 반영 | Pass | TASK R-1~R-9 모두 §2 구현 계획·§3 실행 체크리스트에 커버됨 |
| GP-4 | 파일 목록 완전성 | Pass | §1 관련 파일 테이블에 신규/수정/유지/금지 파일 전체 열거 (N-1~N-2, M-1~M-5, U-1~U-2) |
| GP-5 | 설계 구체성 | Pass | M-1~M-5, N-1~N-2에 실제 마크다운 코드 블록·테이블이 포함된 설계 명세 |
| GP-6 | 체크리스트 커버리지 | Pass | Step 1~8이 R-1~R-9를 1:1 커버, §4 QA 체크리스트에 일관성/문서 품질 항목 추가 포함 |
| D-1 | 설계 방향 §1 3구획 파일 구조 반영 | Pass | N-1(specialist)/N-2(generalist) 신규, M-1(SKILL.md 매핑 테이블), M-2(guide 공통화) 명시 |
| D-2 | 설계 방향 §2 B안(applied_guide 미도입) | Pass | §2 M-1 "워커 자기 판단 절차" 3단계, `applied_guide` 미도입 근거 명시 (M-3 §3-2 안내 문구) |
| D-3 | 설계 방향 §3 분배 범위(opds/opd/opdw/sdd, oppd 제외) | Pass | M-3(opds)·M-4(opd)·M-5(opdw) 수정, U-1(sdd 변경 없음+근거), oppd는 §1 파일 테이블에서 제외 |
| D-4 | 설계 방향 §4 에이전트 AGENT.md 수정 없음 | Pass | §1 파일 테이블에 opal-fe/be/db/task-agent AGENT.md 모두 ❌ 금지(TASK 제약) 명시 |
| C-1 | 127 충돌 회피 — 금지 파일 명시 | Pass | §1 파일 테이블에 opal-task-action-agent/AGENT.md·opal-pilot-project-dev/SKILL.md ❌ 금지(127 충돌) 명시, §5 리스크에도 재확인 |
| C-2 | 에이전트 AGENT.md 보호 4종 | Pass | opal-fe/be/db/task-agent 4종 모두 §1 파일 테이블에 ❌ 금지 선언 |
| O-1 | 열린 이슈 — opdw/sdd EXECUTE 경로 | Pass | M-5(opdw FE 단일 라우팅+근거), U-1/U-2(sdd 변경 없음+ACT 단위 동작 정합 근거) 해소 |
| O-2 | 열린 이슈 — specialist 세부 구조 | Pass | N-1 §1~§6 실제 파일 내용 블록으로 해소 |
| O-3 | 열린 이슈 — generalist 이관 범위 | Pass | N-2 §1~§5 설계 블록, 기존 SKILL.md L22-37/L130-175/L178-194 이관 명시로 해소 |
| O-4 | 열린 이슈 — 버전 결정 | Pass | M-1 v1.3→v2.0 Major 전환, [MUST] docs/CONVENTIONS.md §변경이력 인용 + 114 선례 근거 |
| O-5 | 열린 이슈 — 하위 호환성 | Pass | §1 "하위 호환성" 섹션(opds/opd 폴백) + M-3 §3-1 폴백 규칙 + M-1 §2 실행 컨텍스트 폴백 양쪽 기재 |
| E-1 | 실행 체크리스트 커버리지 (R-1~R-9) | Pass | Step 1→R-2, Step 2→R-3, Step 3→R-4, Step 4→R-1, Step 5→R-5, Step 6→R-6, Step 7→R-7, U-1/U-2+§4 QA 체크리스트→R-8, Step 8→R-9 전부 커버 |
| E-2 | 의존성 그래프 정합성 | Warning | §3 테이블 표두에 "Phase 4개"라고 명시했으나 실제 테이블은 Phase 5개(Phase 5가 Step 8). 표현 불일치. 실행 순서 자체는 Step 의존 관계로 명확히 보정됨 |
| V-1 | 하위 호환성 — opds/opd 폴백 양쪽 기재 | Pass | M-3 §3-1 폴백, op-dev-execute SKILL.md 실행 컨텍스트 폴백 모두 기재됨 |
| V-2 | 변경이력 semver — v1.3→v2.0 Major 근거 | Pass | §2 M-1 핵심 설계에 [MUST] docs/CONVENTIONS.md §변경이력 인용 + 114 선례 명시, §5 리스크 항목에도 재확인 |
| V-3 | §4 QA 체크리스트 R-N 매핑 | Info | §4 QA 체크리스트의 "일관성 테스트"·"문서 품질" 항목들은 별도 R-N 번호가 없어 Step 8의 완료 기준에 직접 연결되지 않음. 실행 시 §4 항목들이 누락될 위험은 낮으나 추적성 보완 가능 |

## 3. 지적 사항

### Warning (1건)

**E-2. Phase 카운트 불일치 (Warning)**

- **위치**: PLAN.md §3 실행 체크리스트 테이블 표두
- **내용**: `> 총 8개 Step | Phase 4개` 라고 명시했으나, 바로 아래 테이블에는 Phase 1~5 총 5개가 나열되어 있음 (Phase 5 = Step 8).
- **영향**: 실행 중 오해 소지가 있으나, 각 Step의 의존 관계(`Step 8 의존: Step 1~7 전체`)가 명확하여 실행 순서에는 영향 없음.
- **권장 조치**: `Phase 4개` → `Phase 5개` 또는 테이블 Phase 열 재정리 (EXECUTE 전 수정 권장).

### Info (1건)

**V-3. §4 QA 체크리스트 항목의 R-N 추적 불가 (Info)**

- **위치**: PLAN.md §4 QA 체크리스트 — "일관성 테스트", "문서 품질" 항목
- **내용**: 해당 항목들은 R-N 번호로 연결되지 않아 TASK.md 요구사항 체크박스와 직접 추적이 어려움.
- **영향**: 실행 완료 후 QA 단계에서 별도 점검이 필요하나, 진행 자체는 지장 없음.
- **참고**: 현재 TASK R-9 AC가 "모든 파일의 변경이력 갱신"만 명시하므로, §4 일관성/문서 품질 항목은 QA-EXECUTE 단계에서 별도 점검.

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md §확정된 설계 방향 §1~§4 | PLAN §1 파일 테이블·§2 핵심 설계가 4개 방향 전부 반영 | Pass |
| TASK.md R-1~R-9 | PLAN §3 Step 1~8 + U-1/U-2가 R-1~R-9 전부 커버 | Pass |
| TASK.md §제약 조건 (127 충돌 회피) | PLAN §1 파일 테이블에 금지 명시, §5 리스크에 재확인 | Pass |
| TASK.md §제약 조건 (에이전트 AGENT.md 수정 금지) | PLAN §1 파일 테이블에 4종 ❌ 금지 명시 | Pass |
| TASK.md §제약 조건 (하위 호환) | PLAN §1 하위 호환성 섹션 + M-3 폴백 + M-1 컨텍스트 폴백 양쪽 기재 | Pass |
| docs/CONVENTIONS.md §변경이력 | M-1 v2.0 근거에 [MUST] 인용, §5 리스크 재확인 | Pass |
| TASK.md (열린 이슈 5개) | PLAN에서 O-1~O-5 모두 해소 확인 | Pass |

## 5. 판정

**Pass**

Critical 0건, Warning 1건(Phase 카운트 표현 불일치 — 실행 순서에 영향 없음), Info 1건(§4 QA 체크리스트 R-N 추적성). TASK R-1~R-9가 §3 Step들로 완전히 커버되고, 설계 방향 §1~§4가 모두 PLAN에 반영되었으며, 127 충돌 회피·에이전트 보호·하위 호환성·semver 근거가 적절히 기재되어 있다. EXECUTE 단계 진행 가능.
