# QA: EXECUTE — PLAN 워커 컨벤션 [MUST] 인용 강제 — 사전 주입 강화

> 검토일: 2026-05-08 | 판정: **Pass**

---

## 1. 요약

PLAN 단계에서 설계한 5개 파일 수정이 완료되었으며, 5개 파일 모두에서 컨벤션 [MUST] 인용 관련 항목이 정확하게 추가되었다. 

- dispatch-process.md §Step 3 카탈로그 + 워커 컨텍스트 템플릿: "컨벤션" 키워드 3곳 명시
- op-task-plan SKILL.md + plan-guide.md + op-dev-plan SKILL.md: 품질 체크리스트에 동일 항목 추가 (3개 파일)
- opal-plan-agent AGENT.md: 행동 규칙에 [MUST] 의무 항목 추가

하위 호환성(CONVENTIONS.md 부재 시 자동 스킵) 및 136과의 책임 분리(PLAN 단계 vs EXECUTE 단계) 모두 명시되어 있다. citation-rules.md §2.5 비채택 결정도 PLAN.md에 명확하게 기록되어 있다.

---

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| §3-1 | Step 1: dispatch-process.md §Step 3 카탈로그·예시·템플릿 갱신 | Pass | grep: "컨벤션" 4줄, "CONVENTIONS" 3줄 (라인 54, 86, 91, 142). 하위 호환 명시(라인 101) |
| §3-2 | Step 2: op-task-plan SKILL.md 품질 체크리스트 추가 | Pass | grep: "CONVENTIONS" 2줄 (라인 65, 201). 변경이력 v1.4 추가(라인 213). 텍스트 포맷 정확 |
| §3-3 | Step 3: op-task-plan plan-guide.md 품질 체크리스트 추가 | Pass | grep: "CONVENTIONS" 2줄 (라인 21, 160). 변경이력 v1.2 추가(라인 178). 라인 160 텍스트가 라인 201(SKILL.md)과 동일 |
| §3-4 | Step 4: op-dev-plan SKILL.md 품질 체크리스트 추가 | Pass | grep: "CONVENTIONS" 2줄 (라인 402, 438). 변경이력 v2.5 추가(라인 453). 라인 438 텍스트가 op-task-plan과 동일 |
| §3-5 | Step 5: opal-plan-agent AGENT.md 행동 규칙 추가 | Pass | grep: "컨벤션" 2줄 (라인 39, 103). 행동 규칙 라인 90에 [MUST] 형식의 의무 항목 신설. 변경이력 v1.1 추가(라인 103) |
| §3-6 | Step 6: 통합 검증 — 하위 호환 + 136 §13 충돌 검토 | Pass | 하위 호환: 5개 파일 모두 "자동 스킵" 명시 확인. 136 충돌: pm-review-gate.md 라인 47-62 §13 읽음 — EXECUTE 단계 changed_files 대상이므로 본 태스크 PLAN 단계 PLAN.md 자체와 시점·대상·메커니즘 모두 분리. 충돌 0건 |
| R-1 | PM 디스패치 측 강제 (카탈로그+예시+템플릿) | Pass | dispatch-process.md 라인 54 카탈로그, 라인 62 예시, 라인 91 템플릿 모두 "컨벤션" 명시 |
| R-2 | PLAN 에이전트 측 강제 | Pass | opal-plan-agent AGENT.md 라인 90 행동 규칙에 [MUST] 의무 항목 신설 |
| R-3 | PLAN.md 산출물 측 검증 (3개 SKILL 파일) | Pass | op-task-plan SKILL.md 라인 201, plan-guide.md 라인 160, op-dev-plan SKILL.md 라인 438에 동일 체크리스트 항목 |
| R-4 | citation-rules.md §2.5 비채택 결정 | Pass | citation-rules.md 변경 없음. PLAN.md §2.1 표에 비채택 근거 명시(라인 139): (a) 트랙 매트릭스 충돌 (b) 6종 토큰 사실상 커버 (c) §2.4 일반 포맷으로 충분 |
| R-5 | 하위 호환 (5개 지점 모두) | Pass | dispatch-process.md 라인 101, SKILL.md 라인 201, plan-guide.md 라인 160, op-dev-plan SKILL.md 라인 438, AGENT.md 라인 90 모두 "자동 스킵" 또는 "부재 시" 명시 |
| R-6 | 적용 지점 결정 근거 명시 | Pass | PLAN.md §2.1 표(라인 134-139)에 #1·#2·#3·#4 채택/비채택 결정 근거 정리 |

---

## 3. 상세 검증

### 3.1 Step 1: dispatch-process.md

**변경 확인**:
- 라인 54: "코드 컨벤션의 [MUST]/금지/네이밍 규칙 (`docs/CONVENTIONS.md` 등)" 추가 (카탈로그 표 "원문 인용 필수" 행)
- 라인 62: `[MUST] CONVENTIONS.md §3.1: API 응답은 camelCase를 사용한다. 직렬화 시 snake_case 금지.` (예시 추가)
- 라인 91: 워커 컨텍스트 템플릿의 "## 핵심 제약" 예시에 컨벤션 항목 추가
- 라인 101: 하위 호환 안내 "`docs/CONVENTIONS.md` 부재 시 본 항목은 자연 스킵 (Step 2 문서 선별에서 제외됨)"
- 라인 142: 변경이력 v1.1 추가 (137 태스크 명시)

**포맷 준수**: [MUST] 형식 정확, citation-rules.md §2.4 준수. SSOT 역할 명확 (opal-pilot-project/dev/dev-short/dev-wireframe 디스패치 프롬프트가 본 SSOT 참조).

### 3.2 Step 2, 3, 4: SKILL.md 품질 체크리스트 (3개 파일)

**op-task-plan SKILL.md (라인 201)**:
```
- [ ] `docs/CONVENTIONS.md`의 [MUST]/금지/네이밍 규칙 중 PLAN 산출물의 코드 예시·설계 결정에 영향을 주는 항목이 §1 참조 문서 테이블 또는 §2 핵심 설계에 `[MUST] 'docs/CONVENTIONS.md' §N: <원문>` 포맷으로 인용되어 있는가 (CONVENTIONS.md 부재 프로젝트는 자동 스킵 — D-1 §Step 2 문서 선별에서 제외)
```
- 변경이력 v1.4 추가(라인 213)

**op-task-plan plan-guide.md (라인 160)**:
- 동일 항목 추가 (§품질 체크리스트)
- 변경이력 v1.2 추가(라인 178)

**op-dev-plan SKILL.md (라인 438)**:
- 동일 항목 추가 (§품질 체크리스트)
- 변경이력 v2.5 추가(라인 453)

**검증**: 3개 파일의 텍스트가 정확하게 동일하며, 각 파일의 변경이력에 137 태스크 명시. [MUST] 포맷 준수. "자동 스킵" 조건 명시.

### 3.3 Step 5: opal-plan-agent AGENT.md

**변경 확인 (라인 90)**:
```
- [MUST] 자체 로드한 `docs/CONVENTIONS.md`의 [MUST]/금지/네이밍 규칙 중 PLAN 설계에 영향을 주는 항목은 PLAN.md §1 참조 문서 테이블 또는 §2 핵심 설계에 `[MUST] 'docs/CONVENTIONS.md' §N: <원문>` 포맷으로 인용한다 (CONVENTIONS.md 부재 시 자동 스킵 — §자체 로드 문서 "각 파일은 존재하는 경우에만 Read하고, 없으면 스킵한다" 룰 상속).
```
- 변경이력 v1.1 추가(라인 103)

**포맷 준수**: [MUST] 형식 정확. AGENT.md의 §자체 로드 문서(라인 33-46)와 동기화 (부재 시 자동 스킵 구조).

### 3.4 Step 6: 통합 검증

**하위 호환 검증**:
- dispatch-process.md §Step 2 "관련 문서 선별" 단계에서 CONVENTIONS.md가 프로젝트에 없으면 선별되지 않음 → Step 3 의무가 발동하지 않음 ✓
- 5개 파일 모두 명시적으로 "자동 스킵" 또는 "부재 시" 조건 기재 ✓

**136 §13 충돌 검토**:
- 136 pm-review-gate.md §13 "컨벤션 자동 진단": EXECUTE 단계, changed_files 대상
- 본 태스크: PLAN 단계, PLAN.md 자체 대상
- 시점: EXECUTE 후(§13) vs PLAN 후(본 태스크) — 분리 ✓
- 대상: changed_files(실제 코드) vs PLAN.md(설계 문서) — 분리 ✓
- 메커니즘: opal-convention-checker(코드 검사) vs 워커 자체(문서 작성) — 분리 ✓

**시너지**: A(본 태스크 사전 주입) + B(136 사후 검출) = 이중 안전망. A 통과 → PLAN.md에 인용됨 → EXECUTE 워커가 준수 코드 생산 → B는 위반 0건이 정상.

---

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| citation-rules.md | §2.4 [MUST] 포맷 준수 확인 | Pass — 모든 신규 의무가 `[MUST] '경로' §N: <원문>` 형식 |
| dispatch-process.md §Step 2 | 문서 선별 메커니즘 확인 | Pass — CONVENTIONS.md 부재 시 선별 제외 → 후속 Step 3 의무 자동 스킵 |
| pm-review-gate.md §13 | EXECUTE 단계 충돌 검토 | Pass — 시점/대상/메커니즘 모두 분리, 충돌 0건 |
| PLAN.md §2.1 | 적용 지점 채택 결정 근거 | Pass — 4개 지점 채택/비채택 결정이 명확하게 표시됨 |
| PLAN.md §2.2 | 136과 책임 분리 + 시너지 | Pass — 표와 단락에서 명시 |
| PLAN.md §리스크 R-T1~R-T5 | 리스크 대응 책무 | Pass — 5개 리스크와 대응이 구체적으로 기재됨 |

---

## 5. 판정

**Pass**

## 판정 근거

PLAN.md §3 실행 체크리스트 6개 Step 모두 완료되었으며, PLAN.md §4 QA 체크리스트의 R-1 ~ R-6, 일관성 테스트 5개, 문서 품질 5개 항목 모두 통과했다. 

- 5개 변경 파일이 정확하게 수정됨
- 각 파일의 컨벤션 [MUST] 인용 항목이 일관되게 추가됨
- 하위 호환성(CONVENTIONS.md 부재 시 자동 스킵) 보장
- 136(사후 검증)과의 책임 분리 명확
- citation-rules.md §2.4 [MUST] 포맷 준수
- SSOT(dispatch-process.md) 참조 구조로 4개 오케스트레이터에 자동 전파 설계

이중 안전망(사전 주입 A + 사후 검출 B) 구조가 정합하며, PM Gate 다음 단계(EXECUTE)로 진행 가능하다.

---

## 변경이력

| 단계 | 수행 내용 | 완료자 |
|------|----------|--------|
| EXECUTE | 5개 파일 수정 완료 + PLAN.md §3·§4 체크박스 갱신 | QA 워커 |
