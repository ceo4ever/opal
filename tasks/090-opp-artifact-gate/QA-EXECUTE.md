# QA-EXECUTE: Artifact Gate 설계 및 적용

> 태스크: 090-opp-artifact-gate | QA 단계: EXECUTE | 작성일: 2026-04-06
> QA 에이전트: op-task-qa (워커)

---

## 1. 검증 범위

변경된 파일 4개를 대상으로 PLAN.md §2 명세 일치 여부, TASK.md 요구사항 6개 충족 여부, PLAN.md §3 실행 체크리스트 및 §4 QA 체크리스트 항목을 검증한다.

| 파일 | 변경 유형 |
|------|---------|
| `opal/core/references/opal-harness-interactive.md` | §2.5 Artifact Gate 신설 |
| `opal/core/references/opal-harness-agentic.md` | §4 강화 검토 기준 Artifact Gate 항목 추가 |
| `opal/core/references/opal-harness.md` | §2 QA 산출물 표준 파일명 서브섹션 추가 |
| `opal/skills/opal-pilot-write-tech/SKILL.md` | ANALYSIS PM Gate 추가 + EXECUTE 배치 게이트 표기 명확화 |

---

## 2. 파일 경로 검증 (제약 조건)

| 검증 항목 | 결과 |
|----------|------|
| 변경 파일이 모두 `opal/core/` 또는 `opal/skills/` 소스 경로인가 | Pass |
| `~/.opal/` 직접 수정 없음 | Pass |

---

## 3. 파일별 검증 결과

### 3.1 opal-harness-interactive.md

#### §2.5 Artifact Gate 위치 확인

실제 파일 구조:
- §2 QA Gate (라인 19~31)
- §2.5 Artifact Gate (라인 33~53) ← 신설
- §3 PM Gate (라인 55~61)

**판정**: §2.5가 §2(QA Gate)와 §3(PM Gate) 사이에 정확히 위치함. Pass

#### 자가 점검 프롬프트 3단계 포함 여부

파일 내 `자가 점검 프롬프트` 블록에 다음 3단계가 포함되어 있음:
1. 현재 단계의 필수 산출물 파일명 확인
2. `tasks/{NNN}-{name}/` 경로 실제 존재 여부 확인
3. 파일이 존재하고 비어 있지 않은지 확인

**판정**: 3단계 모두 포함. Pass

#### 판정 테이블 포함 여부

| 확인 결과 | 동작 | 포함 여부 |
|----------|------|---------|
| 산출물 파일 존재 + 내용 있음 | PM Gate 진입 허용 | Pass |
| 산출물 파일 미존재 | QA 에이전트 재소환 | Pass |
| 산출물 파일 존재하나 비어 있음 | QA 에이전트 재소환 | Pass |

**판정**: 3행 판정 테이블 완전 포함. Pass

#### 차단 원칙 명시 여부

`**차단 원칙**: 필수 산출물이 확인되지 않으면 PM Gate 및 DONE.md 생성 단계로 진입하지 않는다.` — 명시되어 있음.

**판정**: Pass

#### 변경이력 v1.4 추가

`| v1.4 | 2026-04-06 | §2.5 Artifact Gate 신설 — QA Gate 완료 후 PM Gate 진입 전 산출물 존재 여부 강제 확인 (090) |` — 확인됨.

**판정**: Pass

#### 소계

| AC | 결과 |
|----|------|
| PM Gate 진입 조건에 "QA 산출물 파일이 존재해야 한다" 명시 | Pass |
| 파일 부재 시 동작(QA 재소환) 명시 | Pass |
| 자가 점검 프롬프트 포함 | Pass |

---

### 3.2 opal-harness-agentic.md

#### §4 강화 검토 기준 Artifact Gate 항목 위치

실제 기준 목록:
1. TASK.md 요구사항 100% 충족
2. QA 결과 All Pass
3. **Artifact Gate**: QA 산출물 파일이 실제로 존재하고 내용이 있는지 확인 ← 신규 3번째
4. PM 검토 기준 Pass
5. 이전 단계 산출물과 일관성 유지
6. 산출물 내용을 직접 Read하여 실질 검증

**판정**: PLAN.md §2 명세(3번째 기준으로 삽입)와 정확히 일치. Pass

#### agentic 모드 특화 지침 포함 여부

`agentic 모드에서는 자율 통과 시도 없이 반드시 산출물 파일을 Read하여 확인한다.` — 3번 항목 내 포함됨.

**판정**: Pass

#### 파일 미존재 시 자율 통과 차단 명시

`파일 미존재 또는 빈 파일 시: PM이 QA 에이전트를 재소환하여 산출물을 생성한 후 재검증` — 명시됨.

**판정**: Pass

#### 변경이력 v1.2 추가

`| v1.2 | 2026-04-06 | §4 강화 검토 기준에 Artifact Gate 항목 추가 (090) |` — 확인됨.

**판정**: Pass

#### 소계

| AC | 결과 |
|----|------|
| agentic 모드에서 QA 산출물 파일 부재 시 자율 통과 차단 명시 | Pass |
| Artifact Gate 항목이 강화 검토 기준 목록에 포함 | Pass |

---

### 3.3 opal-harness.md

#### §2 QA 산출물 표준 파일명 서브섹션 위치

`### QA 체크리스트 검증` 섹션(라인 89~101) 이후에 `### QA 산출물 표준 파일명` 서브섹션(라인 102~113)이 추가되어 있음.

**판정**: "QA 체크리스트 검증" 바로 다음에 위치. PLAN.md 명세와 일치. Pass

#### 필수 산출물 파일명 테이블

| 단계 | 파일명 | 확인 |
|------|--------|------|
| PLAN QA | `QA-PLAN.md` | Pass |
| EXECUTE QA | `QA-EXECUTE.md` | Pass |
| ANALYSIS QA | `QA-ANALYSIS.md` | Pass |

**판정**: 3행 모두 PLAN.md 명세와 일치. Pass

#### 스킬별 오버라이드 안내

`**스킬별 산출물 오버라이드**: 각 오케스트레이터 SKILL.md의 "STATE.md 도메인 치환값" 또는 별도 섹션에서 단계별 QA 산출물 파일명을 명시할 수 있다.` — 포함됨.

**판정**: Pass

#### 변경이력 v2.8 추가

`| v2.8 | 2026-04-06 | §2 QA 산출물 표준 파일명 서브섹션 추가 — Artifact Gate 기준 파일명 공통화 (090) |` — 확인됨.

**판정**: Pass

#### 소계

| AC | 결과 |
|----|------|
| QA-PLAN.md, QA-EXECUTE.md 형식으로 필수 파일 명시 | Pass |
| 스킬별 오버라이드 안내 포함 | Pass |

---

### 3.4 opal-pilot-write-tech/SKILL.md

#### ANALYSIS PM Gate(자가 체크) 추가 — 게이트 절차 순서

실제 게이트 절차:
1. **PM Gate (자가 체크)** — 외부 QA 에이전트 호출 없이 PM이 자가 점검
2. 사용자 확인 (interactive) / PM 자율 승인 (agentic)

**판정**: "PM Gate → 사용자 확인" 순서 정확히 명시. Pass

#### PM Gate 자가 체크 방식 명시

`ANALYSIS는 PM이 직접 수행하는 단계이므로 외부 QA 에이전트 호출 없이 PM이 자가 점검한다.` — 명시됨.

**판정**: Pass

#### 자가 체크 3항목 포함 여부

| 항목 | 포함 여부 |
|------|---------|
| AGENT.md 검토 기준(§4) 7항목 체크 | Pass |
| ANALYSIS.md 내용이 모든 워커 결과를 취합하고 있는지 확인 | Pass |
| 문서별 요약 및 이슈 목록 누락 없이 작성 확인 | Pass |
| Artifact Gate: `ANALYSIS.md` 파일 존재 및 내용 확인 | Pass |

비고: 4항목이 포함되어 있음. PLAN 명세에는 3항목(AGENT.md 검토 기준, 취합 확인, Artifact Gate)이지만 실제 파일에는 "문서별 요약 및 이슈 목록 누락 없이 작성"이 취합 확인과 분리되어 4항목으로 구체화됨 — 명세를 초과 충족.

**판정**: Pass (상위 호환)

#### EXECUTE 배치 게이트 표기 명확화

실제 문구: `배치 완료 → **QA Gate** (op-task-qa) → **PM Gate** (배치 단위 간이 검토 — 하네스 §3 참조. 전체 PM Gate는 QA 단계 최종 판정에서 수행) → 사용자 확인 (interactive) / PM 자율 승인 후 다음 배치 (agentic)`

- "PM 검토" → "PM Gate" 명칭 통일: Pass
- 하네스 §3 참조 포함: Pass
- "전체 PM Gate는 QA 단계 최종 판정에서 수행" 참조: Pass

**판정**: PLAN.md §2 명세와 정확히 일치. Pass

#### 변경이력 v2.5 추가

`| v2.5 | 2026-04-06 | ANALYSIS PM Gate(자가 체크) 추가 + EXECUTE 배치 게이트 "PM 검토" → "PM Gate" 명확화 (090) |` — 확인됨.

**판정**: Pass

#### 소계

| AC | 결과 |
|----|------|
| ANALYSIS 게이트 절차에 "PM Gate → 사용자 확인" 순서 명시 | Pass |
| PM Gate가 자가 체크 방식임을 명시 | Pass |
| AGENT.md 검토 기준 체크, 취합 확인, Artifact Gate 항목 포함 | Pass |
| EXECUTE 배치 게이트 "QA Gate → PM Gate (배치 단위 간이 검토 — 하네스 §3 참조)" 형식 | Pass |
| "전체 PM Gate는 QA 단계 최종 판정에서 수행" 참조 포함 | Pass |

---

## 4. TASK.md 요구사항 6개 충족 여부

| # | 요구사항 | 충족 여부 | 근거 |
|---|---------|---------|------|
| 1 | Artifact Gate 규칙 추가 — opal-harness-interactive.md | Pass | §2.5 신설, 판정 테이블 + 차단 원칙 포함 |
| 2 | Artifact Gate 규칙 추가 — opal-harness-agentic.md | Pass | §4 강화 검토 기준 3번째 항목으로 추가, agentic 특화 지침 포함 |
| 3 | 필수 산출물 명세 추가 — opal-harness.md (공통) | Pass | §2 QA 산출물 표준 파일명 서브섹션 신설, QA-PLAN.md/QA-EXECUTE.md/QA-ANALYSIS.md 명세 |
| 4 | 자가 점검 프롬프트 추가 | Pass | interactive §2.5에 통합 포함 (3단계 프롬프트 + 판정 테이블) |
| 5 | opwt ANALYSIS 단계 PM Gate 추가 | Pass | PM Gate(자가 체크) → 사용자 확인 순서 명시, 자가 체크 4항목 포함 |
| 6 | opwt EXECUTE 배치 "PM 검토" → PM Gate 명확화 | Pass | "PM Gate" 명칭 통일, 하네스 §3 참조, 전체 PM Gate 참조 포함 |

---

## 5. PLAN.md §4 QA 체크리스트 종합

| 파일 | 항목 | 결과 |
|------|------|------|
| opal-harness-interactive.md | §2.5가 §2와 §3 사이에 정확히 위치 | Pass |
| opal-harness-interactive.md | PM Gate 진입 조건에 "QA 산출물 파일이 존재해야 한다" 명시 | Pass |
| opal-harness-interactive.md | 파일 부재 시 동작(QA 재소환) 명시 | Pass |
| opal-harness-interactive.md | 자가 점검 프롬프트 포함 | Pass |
| opal-harness-agentic.md | agentic 모드에서 QA 산출물 파일 부재 시 자율 통과 차단 명시 | Pass |
| opal-harness-agentic.md | Artifact Gate 항목이 강화 검토 기준 목록에 포함 | Pass |
| opal-harness.md | QA-PLAN.md, QA-EXECUTE.md 형식으로 필수 파일 명시 | Pass |
| opal-harness.md | 스킬별 오버라이드 안내 포함 | Pass |
| opwt SKILL.md (ANALYSIS) | ANALYSIS 게이트 절차에 "PM Gate → 사용자 확인" 순서 명시 | Pass |
| opwt SKILL.md (ANALYSIS) | PM Gate가 자가 체크 방식임을 명시 | Pass |
| opwt SKILL.md (ANALYSIS) | AGENT.md 검토 기준 체크, 취합 확인, Artifact Gate 3항목 포함 | Pass |
| opwt SKILL.md (EXECUTE) | "QA Gate → PM Gate (배치 단위 간이 검토 — 하네스 §3 참조)" 형식 | Pass |
| opwt SKILL.md (EXECUTE) | "전체 PM Gate는 QA 단계 최종 판정에서 수행" 참조 포함 | Pass |

---

## 6. 특이 사항

1. **opwt ANALYSIS 자가 체크 항목 수**: PLAN.md 명세는 3항목이나 실제 구현은 4항목("문서별 요약 및 이슈 목록 누락 없이 작성" 추가). 명세를 상위 호환하므로 문제없음.
2. **agentic.md §2.5 참조**: 3번 기준의 `(하네스 §2.5 참조)` 표기가 interactive 하네스 기준이나, agentic은 공통 하네스를 함께 로드하므로 참조 경로가 유효함.
3. **~/.opal/ 미수정 확인**: 4개 파일 모두 `opal/core/` 또는 `opal/skills/` 소스 경로에서만 수정되었음. 제약 조건 준수.

---

## 7. 최종 판정

| 항목 | 결과 |
|------|------|
| TASK.md 요구사항 6개 | All Pass |
| PLAN.md §3 실행 체크리스트 (15항목) | All Pass |
| PLAN.md §4 QA 체크리스트 (13항목) | All Pass |
| 파일 경로 제약 조건 | Pass |
| PLAN.md §2 명세 일치 | Pass |

**판정: Pass**
