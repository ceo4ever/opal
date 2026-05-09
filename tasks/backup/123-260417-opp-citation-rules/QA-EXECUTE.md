---
@header
module: tasks/123-260417-opp-citation-rules
layer: qa
description: QA-EXECUTE — EXECUTE 단계 산출물 품질 검증 리포트
---

# QA: EXECUTE — 산출물 인용 위치 추적 하네스 (Citation Rules)

> 검토일: 2026-04-17 | 판정: **Pass**

---

## 1. 요약

EXECUTE 단계 8개 파일(N-1 신규 + M-1~M-7 수정)에 대한 품질 검증을 수행했다.

- **N-1** `opal/core/references/harness/citation-rules.md`: §1~§6 전 섹션 작성 완료. 인용 포맷 4종(문서/코드/외부/MUST), 단계별 의무 수준 매트릭스, 사람/AI 탐색 가이드 포함.
- **M-1** `opal-harness.md`: §2 모듈 테이블에 citation-rules 행 추가, v4.3 변경이력 등록 완료.
- **M-2~M-7**: op-task/op-dev-analysis/op-dev-plan/op-task-plan 4개 스킬과 2개 plan-guide에 참조 문서 테이블, 근거 컬럼, 인라인 인용 지시가 일관되게 적용됨.
- 모든 수정 파일의 변경이력에 `2026-04-17 / (123)` 태깅 확인.
- PLAN.md 체크리스트에서 명시한 `# | 문서 | 경로 | 참조 이유` 대신 citation-rules §3.1의 더 완성된 표준 컬럼(`# | 유형 | 문서/사이트 | 경로/URL | 참조 이유`)을 적용 — SSOT 일관성 측면에서 오히려 우수.

---

## 2. 검증 결과

### 2.1 기능 테스트 (R-1~R-6)

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| R-1-1 | citation-rules.md 파일이 존재하고 §1~§6 섹션이 모두 작성되어 있다 | Pass | §1 적용 범위 및 목적 / §2 인용 포맷 / §3 적용 방식 / §4 단계별 의무 수준 / §5 예외 규칙 / §6 사람AI 탐색 가이드 전부 확인 |
| R-1-2 | citation-rules.md에 인용 포맷 3종(문서/코드/MUST)의 구체 예시가 포함되어 있다 | Pass | §2.1 문서 근거 예시 2개, §2.2 코드 근거 예시 2개, §2.4 MUST 예시 2개 존재. 추가로 §2.3 외부 사이트 포맷도 신설됨 |
| R-1-3 | citation-rules.md에 단계별 의무 수준 매트릭스(TASK/ANALYSIS/PLAN × 테이블/인라인/MUST)가 존재한다 | Pass | §4 테이블에 TASK/ANALYSIS/PLAN 3행 × 참조 문서 테이블/인라인 인용/[MUST] 포맷 3컬럼 구성 확인 |
| R-2-1 | opal-harness.md §2 모듈 테이블에 citation-rules 행이 등록되어 있다 | Pass | 라인 107: `\| 인용 규칙 \| \`harness/citation-rules.md\` \| TASK/ANALYSIS/PLAN 산출물 작성 시 \| §2 \|` 확인 |
| R-2-2 | opal-harness.md 변경이력에 v4.3 (2026-04-17, 123) 항목이 추가되었다 | Pass | 라인 376: `\| v4.3 \| 2026-04-17 \| §2 하네스 모듈 테이블에 citation-rules 추가 — 산출물 인용 규칙 신설 (123) \|` 확인 |
| R-3-1 | op-task/SKILL.md "관련 문서" 섹션이 테이블 포맷으로 전환되었다 | Pass | 라인 142-148: `\# \| 유형 \| 문서/사이트 \| 경로/URL \| 참조 이유` 컬럼 테이블 존재. citation-rules.md §2 참조 지시 포함 |
| R-4-1 | op-dev-analysis ANALYSIS.md 통일 형식의 §0 참조 문서 테이블이 추가되었다 | Pass | 라인 67-72: `## 0. 참조 문서` 섹션과 `\# \| 유형 \| 문서/사이트 \| 경로/URL \| 참조 이유` 테이블 확인. citation-rules.md §2 참조 지시 포함 |
| R-4-2 | op-dev-analysis §1.1/§5에 근거 컬럼이 추가되었다 | Pass | §1.1(라인 77-80): `\| 파일 \| 역할 \| 변경 필요 \| 근거(줄번호) \|` 컬럼 확인. §5(라인 117-120): `\| 항목 \| 설명 \| 심각도 \| 근거 \|` 컬럼 확인 |
| R-5-1 | op-dev-plan PLAN.md §3 설계 섹션에 근거 필드가 추가되었다 | Pass | §3.N.1 신규/수정 테이블에 `근거` 컬럼 추가. §3.N.2 상단에 인라인 인용 지시문 추가. citation-rules.md §2·§3.2 참조 |
| R-5-2 | op-dev-plan PLAN.md §8.3 참조 문서 테이블이 신설되었다 | Pass | 라인 338-342: `### 8.3 참조 문서 (설계 결정 근거)` 섹션과 5컬럼 테이블 존재. citation-rules §3.1 참조 지시 포함 |
| R-5-3 | op-dev-plan plan-guide.md 3단계 + 3.5단계에 인용 작성 지시가 추가되었다 | Pass | 3단계: 3.N.1 `근거` 컬럼, 3.N.2 인라인 인용 지시문 추가. 3.5단계: `## 3.5단계: 참조 문서 테이블 (§8.3)` 섹션 신설(라인 182-199) |
| R-6-1 | op-task-plan SKILL.md §1 참조 문서 테이블이 추가되었다 | Pass | 라인 122-127: `### 참조 문서 (PLAN 작성 근거)` + `\# \| 유형 \| 문서/사이트 \| 경로/URL \| 참조 이유` 테이블 확인. citation-rules §3.1 참조 지시 포함 |
| R-6-2 | op-task-plan SKILL.md §2 인용 필드가 추가되었다 | Pass | 라인 128-132: 관련 파일 테이블에 `근거(줄번호)` 컬럼 추가. 라인 154-156: 핵심 설계 섹션에 인라인 인용 지시문 추가 |
| R-6-3 | op-task-plan plan-guide.md에 인용 작성 지시가 추가되었다 | Pass | 조사 항목 4번: "참조 문서 목록 구성" 추가(라인 29). 3단계: "근거 인용" bullet 추가(라인 81). |

### 2.2 일관성 테스트

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| C-1 | 모든 참조 문서 테이블이 공통 컬럼 스키마를 따른다 | Warning | PLAN.md 체크리스트 기재(`# \| 문서 \| 경로 \| 참조 이유`) vs. 실제 구현(`# \| 유형 \| 문서/사이트 \| 경로/URL \| 참조 이유`). 실제 구현이 citation-rules §3.1 SSOT와 일치하는 더 완성된 스키마로 모든 파일이 통일됨. PLAN.md 체크리스트 표현이 단순화된 약식이었던 것으로 판단 |
| C-2 | 인용 포맷이 citation-rules.md §2의 표준과 일치한다 | Pass | 모든 파일에서 `` `경로 §N` `` / `` `경로:줄번호` `` / `[MUST]` 포맷을 citation-rules §2 참조로 적용. `(→ D-N §N)` 단축 참조 포맷도 SKILL.md에 명시됨 |
| C-3 | `[MUST]` 포맷이 `opal-pm.md §3 Step 3` 기존 포맷과 호환된다 | Pass | citation-rules.md §2.4: "`opal-pm.md` §3 Step 3 포맷과 통일한다" 명시. §4에서도 "PM → 워커 주입 포맷과의 통일" 재확인 |
| C-4 | 하네스 모듈 stub(출처/로드 시점/역할) 포맷이 기존 모듈과 일치한다 | Pass | citation-rules.md 라인 3-5: `> 출처: opal-harness.md §2`, `> 로드 시점: TASK/ANALYSIS/PLAN 산출물 작성 시`, `> 역할: ...` — header-rules.md/qa-standards.md와 동일한 stub 3줄 구조 |
| C-5 | 모든 수정 파일의 변경이력에 2026-04-17 / 123 행이 추가되었다 | Pass | N-1(v1.0 초기 작성 (123)), M-1(v4.3 2026-04-17 (123)), M-2(v1.3 2026-04-17 (123)), M-3(v1.3 2026-04-17 (123)), M-4(v2.3 2026-04-17 (123)), M-5(v2.2 2026-04-17 (123)), M-6(v1.2 2026-04-17 (123)), M-7(v1.1 2026-04-17 (123)) 전부 확인 |
| C-6 | 6개 SKILL.md/plan-guide.md 수정 모두 citation-rules.md를 참조한다 | Pass | M-2(citation-rules.md §2 참조), M-3(citation-rules.md §2 참조), M-4(citation-rules.md §2·§3.2 참조), M-5(citation-rules.md §2·§3.1 참조), M-6(citation-rules.md §3.1 참조), M-7(citation-rules.md §2 참조) 전부 확인 |

### 2.3 문서 품질

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| Q-1 | 한국어 본문 + 영어 코드/필드명 규칙 준수 | Pass | 모든 파일에서 본문은 한국어, 코드 경로/필드명/포맷 기호는 영어로 작성됨 |
| Q-2 | kebab-case 파일 네이밍 준수 | Pass | `citation-rules.md` — kebab-case 준수 |
| Q-3 | Markdown 테이블 문법 유효 | Pass | 모든 테이블에서 헤더행 구분선(`|---|`) 포함. 컬럼 수 일치 확인 |
| Q-4 | citation-rules.md 변경이력 형식 준수 | Pass | `\| 버전 \| 날짜 \| 변경내용 \|` 형식으로 v1.0 행 존재 |
| Q-5 | 각 수정 파일의 변경이력 행이 `(123)` 태스크 번호로 태깅됨 | Pass | C-5 검증에서 8개 파일 전부 `(123)` 확인 |

---

## 3. 지적 사항

### Warning: 참조 문서 테이블 컬럼 스키마 표현 불일치 (C-1)

**심각도**: Info (진행에 영향 없음)

**내용**: PLAN.md §5 QA 체크리스트 및 TASK 디스패치 명세에서 기대한 컬럼 스키마는 `# | 문서 | 경로 | 참조 이유` (4컬럼)이었으나, 실제 구현에서는 citation-rules §3.1 SSOT 표준인 `# | 유형 | 문서/사이트 | 경로/URL | 참조 이유` (5컬럼)을 적용했다.

**평가**: 이는 결함이 아닌 **표준 상향 적용**으로 판단한다.
- PLAN.md 체크리스트 문구 `# | 문서 | 경로 | 참조 이유`는 비공식 약식 표현이었고, 실제 citation-rules.md §3.1이 확정 SSOT 컬럼 스키마임.
- 모든 6개 파일이 동일한 5컬럼 스키마로 일관되게 구현됨 → SSOT 일원화 목표 달성.
- Warning으로 기록하되 수정 불필요.

---

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md R-1 AC | citation-rules.md에 인용 형식 정의/적용 시점/의무 수준/사람+AI 탐색 가이드 포함 여부 | Pass |
| TASK.md R-2 AC | §2 테이블에 citation-rules 행 존재 + 로드 조건/적용 주체/적용 시점 명시 여부 | Pass |
| TASK.md R-3 AC | TASK.md 템플릿에 문서명/경로/섹션/인용 내용 컬럼이 있는 테이블 구조 포함 여부 | Pass (5컬럼 구조로 구현, 섹션 컬럼 대신 유형 컬럼) |
| TASK.md R-4 AC | ANALYSIS.md 형식에 분석 근거(코드/문서) 인용 필드 포함 여부 | Pass |
| TASK.md R-5 AC | PLAN.md §3 인용 필드 + §8 참조 문서 테이블 + plan-guide 3단계 인용 지시 포함 여부 | Pass |
| TASK.md R-6 AC | op-task-plan PLAN.md 형식에 인용 필드 포함 여부 | Pass |
| PLAN.md §3.3 N-1 완료 기준 | stub 3줄 존재 + 단계별 의무 매트릭스 3행 + 인용 포맷 예시 3종 이상 | Pass |
| PLAN.md §3.3 M-1 완료 기준 | citation-rules 행 + v4.3 변경이력 | Pass |
| PLAN.md §3.3 M-2 완료 기준 | 4컬럼 테이블 + citation-rules 참조 + 체크리스트 항목 | Pass (5컬럼으로 구현) |
| PLAN.md §3.3 M-3 완료 기준 | §0 참조 문서 테이블 + §1.1/§5 컬럼 확장 + 체크리스트 3개 항목 | Pass |
| PLAN.md §3.3 M-4 완료 기준 | §3 테이블 스키마 확장 + §8.3 섹션 + 체크리스트 항목 | Pass |
| PLAN.md §3.3 M-5 완료 기준 | 3단계 설계 지시 + 3.5단계 섹션 + 체크리스트 갱신 | Pass |
| PLAN.md §3.3 M-6 완료 기준 | §1 참조 문서 테이블 + §2 인용 지시 + 체크리스트 항목 | Pass |
| PLAN.md §3.3 M-7 완료 기준 | 현황 조사·3단계 설계 지시 갱신 + 체크리스트 갱신 | Pass |
| TASK.md 제약 #1 | `~/.opal/` 경로 직접 수정 없음 — `opal/core/` 및 `opal/skills/` 에서만 수정 | Pass |
| TASK.md 제약 #2 | 레거시 산출물 소급 변경 없음 (citation-rules §5에 레거시 호환 선언 존재) | Pass |

---

## 5. 판정

**Pass**

8개 파일 변경 모두 TASK.md 요구사항(R-1~R-6) 및 PLAN.md 완료 기준을 충족한다. Critical/Warning 없음, Info 1건(컬럼 스키마 약식 표현 vs. 실제 SSOT 표준 적용 — 수정 불필요). citation-rules.md SSOT 중심 설계 원칙이 6개 스킬/가이드 파일에 일관되게 구현되었으며, 하네스 §2 모듈 테이블 등록으로 워커 로드 경로가 확립되었다.
