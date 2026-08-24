---
name: op-dev-qa
description: |
  **Dev 문서 QA 검증 기준 라이브러리**. 문서 QA(요구사항→설계 검토)는 별도 QA Gate 단계를 두지 않고 PM Gate가 직접 수행하며, PM이 PM Gate 문서검증 시 이 스킬의 검증 기준(공통 검증 원칙·단계별 검증 ID·QA-{단계}.md 형식)을 참조한다.
  참조 시점: PM Gate 문서검증 시. 단계에 따라 qa-dev-guide 또는 qa-wireframe-guide를 참조한다.
  검증 대상 입력: 검증 대상 산출물 경로 + 단계명. 선택 입력: TASK.md. 산출 형식: QA-{단계}.md (PM이 검증 결과 기록 시 사용).
---

# op-dev-qa — Dev 문서 QA 검증 기준

## 실행 컨텍스트

- **참조 주체**: PM Gate 문서검증을 수행하는 PM (오케스트레이터). 별도 QA 에이전트 디스패치 없이 PM이 본 스킬의 검증 기준을 참조한다.
- **역할**: 동작 검증(TEST / TEST-SCENARIO / verify, 독립·불변 영역)과 무관한 **문서 QA(요구사항→설계 검토)** 의 검증 기준을 제공한다.
- **검증 입력**: 검증 대상 산출물 경로 + `stage` (단계명)
- **검증 산출 형식**: `tasks/{NNN}-{태스크명}/QA-{단계}.md` (PM이 검증 결과를 기록할 때 사용)

> **[MUST]** 산출물 작성·검증 시 `opal/core/references/harness/citation-rules.md`를 Read하여 규칙(근거 제시 원칙 / 트랙별 매트릭스 / [MUST] 토큰 / 영역 간 용어 일관성 / decision_required 계약)을 준수한다.

## 페르소나

```
Read ~/.opal/skills/op-dev-qa/personas/qa-engineer.md
```

페르소나 파일이 없으면 다음 역할을 따른다:
- 시니어 QA 엔지니어
- 산출물 작성자와 독립된 관점에서 객관적으로 검토한다
- 사용자가 전체 문서를 읽지 않아도 되는 수준의 요약을 제공한다

## 입력

PM Gate 문서검증 시 PM이 다루는 검증 대상 정보:

| 입력 | 설명 |
|------|------|
| `stage` | 검토 대상 단계 (`ANALYSIS` / `PLAN` / `WIREFRAME` / `EXECUTE-UI`) |
| `mode` | 태스크 모드 (`full` / `short` / `wireframe-ui`) |
| `task_path` | 태스크 폴더 경로 |
| `artifact_path` | 검증 대상 산출물 경로 |
| `changed_files` | 변경된 코드 파일 목록 (EXECUTE-UI 시 필수) |

## 프로세스

### Step 1. 단계별 가이드 로딩

단계명에 따라 참조 가이드를 결정한다:

| 단계 | 가이드 |
|------|--------|
| ANALYSIS | `Read ~/.opal/skills/op-dev-qa/references/qa-dev-guide.md` |
| PLAN | `Read ~/.opal/skills/op-dev-qa/references/qa-dev-guide.md` |
| WIREFRAME | `Read ~/.opal/skills/op-dev-qa/references/qa-wireframe-guide.md` |
| EXECUTE-UI | `Read ~/.opal/skills/op-dev-qa/references/qa-wireframe-guide.md` |

### Step 2. 산출물 읽기

검증 대상 산출물과 이전 단계 산출물을 모두 읽는다.

| 현재 단계 | 읽어야 하는 파일 |
|-----------|----------------|
| ANALYSIS (Full) | ANALYSIS.md + TASK.md |
| PLAN (Full) | PLAN.md + ANALYSIS.md + TASK.md |
| PLAN (Short) | PLAN.md + TASK.md |
| WIREFRAME | wireframe.md + TASK.md |
| EXECUTE-UI | wireframe.md + changed_files + TASK.md |

### Step 3. 품질 검증

가이드의 검증 기준에 따라 항목별 검증을 수행한다.

### Step 4. 체크리스트 갱신

QA 검증 결과를 바탕으로 해당 시점의 체크리스트를 Read하고, 검증 통과 항목을 `[x]`로 갱신한다.

| 현재 단계 | 갱신 대상 | 갱신 내용 |
|-----------|----------|----------|
| ANALYSIS | TASK.md 요구사항 체크박스 | ANALYSIS가 커버하는 요구사항 → `[x]` |
| PLAN | TASK.md 요구사항 체크박스 | PLAN.md가 커버하는 요구사항 → `[x]` |
| EXECUTE-UI | PLAN.md §3 실행 체크리스트 + §4 QA 체크리스트 | 검증 통과 항목 → `[x]` |

**갱신 규칙**:
- 검증을 통과한 항목만 `[x]`로 갱신한다
- 검증 실패(Fail) 항목은 `[ ]` 유지 + QA 리포트에 사유 기재
- Warning 항목은 `[x]`로 갱신하되 QA 리포트에 비고 기재
- EXECUTE 단계에서 TEST-SCENARIO 결과도 체크리스트 갱신에 반영한다

### Step 5. 판정

검증 결과를 종합하여 판정한다:
- **Pass** -- 지적 사항 없음 또는 경미한 수준. 다음 단계 진행 가능.
- **Needs Revision** -- 수정이 필요한 항목 존재. 지적 사항 해결 후 진행 권장.

### Step 6. QA 리포트 생성

검증 결과를 QA-{단계}.md로 작성한다.

## 활용 스킬

| 스킬 | 용도 | 사용 시점 |
|------|------|----------|
| getsentry/code-review | 코드 품질 리뷰 참조 | EXECUTE 후 코드 리뷰 시 |
| openai/security-best-practices | 보안 검증 참조 | 보안 관련 검증 시 |

## 검증 기준 요약

### 공통 검증 원칙

| 원칙 | 설명 |
|------|------|
| 완전성 | 요구사항이 빠짐없이 반영되었는가 |
| 정합성 | 이전 단계 산출물과 일치하는가 |
| 명확성 | 모호하지 않고 구체적인가 |
| 실행 가능성 | 이 산출물만으로 다음 단계를 진행할 수 있는가 |

### Dev 단계별 검증 ID

- ANALYSIS: R-1 ~ R-8 (TASK 커버리지, 코드 실독, 파일 완전성, 영향 범위, 리스크, 깊이, **원문 덤프 차단**, **098 규약 준수**)
  - R-7: 소스코드 원문 블록 0건, 코드펜스는 실행 명령·시그니처로 한정
  - R-8: 확정 입력 판정표 전건 판정 + 근거 등급·관측 스코프·실행 명령 병기
- PLAN (Full): P-1 ~ P-8 (구현 가능성, 의존성 순서, ANALYSIS 반영, 파일 일치, 설계 구체성, 테스트 전략, **기능-QA 커버리지**, **확정 승계 준수**)
  - P-7 (Multi-Feature 모드에서만 필수): 모든 F-NNN이 §5 QA 체크리스트에서 최소 1개 항목으로 커버되는가? 빈틈 발견 시 Fail.
  - P-8: ANALYSIS 핸드오프 표 항목을 재도출 없이 인용, `[MUST] 재도출 금지` 위반 0건
- PLAN (Short): SP-1 ~ SP-5 (코드 분석, 구현 계획, 체크리스트 완전성, QA 항목, Short 적정성)

### Wireframe 단계별 검증 ID

- WIREFRAME: W-1 ~ W-5 (섹션 완전성, 화면 목록, 상세 설계, shadcn 매핑, 구현 가능성)
- EXECUTE-UI: E-1 ~ E-6 (빌드 성공, 린트 통과, 화면 커버리지, 레이아웃 대조, 컴포넌트 대조, 인터랙션 구현)

## QA-{단계}.md 통일 형식

```markdown
# QA: {단계명} — {태스크 제목}

> 검토일: YYYY-MM-DD | 판정: {Pass / Needs Revision}

## 1. 요약
{산출물의 핵심 내용 3~5줄}

## 2. 검증 결과
| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| {ID} | {항목명} | Pass / Warning / Fail | {구체적 근거} |

## 3. 지적 사항
{Warning 또는 Fail 항목에 대한 상세 설명}
{없으면 "지적 사항 없음"}

### 심각도 분류
- Critical: 다음 단계 진행 전 반드시 수정 필요
- Warning: 수정 권장, 사용자 판단에 따라 진행 가능
- Info: 참고 사항, 진행에 영향 없음

## 4. 교차 참조 검증
| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|

## 5. 판정
**{Pass / Needs Revision}**
{판정 근거 1~2줄}
```

## 저장 경로

```
tasks/{NNN}-{태스크명}/QA-{단계}.md
```

예: `QA-ANALYSIS.md`, `QA-PLAN.md`, `QA-WIREFRAME.md`, `QA-EXECUTE-UI.md`

## 판정 기준

| 판정 | 조건 |
|------|------|
| **Pass** | 모든 검증 항목 통과, 또는 Info만 존재 |
| **Needs Revision** | Critical 1개 이상, 또는 Warning 3개 이상 |

## 완료 후 동작

PM Gate 문서검증 결과를 QA-{단계}.md로 기록하면, PM은 PM Gate 판정으로 이를 반영한다.

**기록 형식**:
```
QA: tasks/{NNN}-{태스크명}/QA-{단계}.md | 판정: {Pass / Needs Revision}
```

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | - | 초기 작성 |
| v1.1 | 2026-04-13 13:48 | PLAN (Full) 검증 기준에 P-7 기능-QA 커버리지 추가 — Multi-Feature 모드에서 모든 F-NNN이 §5 QA 체크리스트 최소 1개 항목 커버, 빈틈 발견 시 Fail (114) |
| v1.2 | 2026-04-24 | citation-rules 트리거 1줄 주입 — SSOT + Trigger 패턴 (130) |
| v1.3 | 2026-06-07 | 역할 한정 — "QA Gate 단계 워커"에서 "PM Gate 문서검증 시 PM이 참조하는 검증 기준 라이브러리"로 재정의(description/실행 컨텍스트/입력/반환). 검증 기준 콘텐츠(공통 검증 원칙·단계별 검증 ID·QA-{단계}.md 형식)는 보존. 동작 검증 영역은 불변 (014) |
| v1.4 | 2026-08-23 12:44 | qa-dev-guide.md 거울 사본 번호 범위 동기화 — ANALYSIS: R-1~R-6 → R-1~R-8(원문 덤프 차단·098 규약 준수 추가), PLAN(Full): P-1~P-7 → P-1~P-8(확정 승계 준수 추가). PLAN(Short) SP-1~SP-5는 무변경 (100 EXECUTE Step 7) |
