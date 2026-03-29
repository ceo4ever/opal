---
name: op-task-qa
description: |
  **QA 검증 단계 스킬**. 산출물의 품질을 검증하여 QA 리포트를 생성한다. 단계에 따라 qa-dev-guide 또는 qa-wireframe-guide를 참조한다.
  반드시 이 스킬을 사용해야 하는 상황: 오케스트레이터가 QA 검증을 디스패치할 때.
  필수 입력: 검증 대상 산출물 경로 + 단계명. 선택 입력: TASK.md. 보장 출력: QA-{단계}.md.
---

# op-task-qa — QA 검증

## 실행 컨텍스트

- **호출자**: 오케스트레이터가 QA 검증을 디스패치
- **실행 주체**: QA 전용 워커 에이전트 (op-task-qa-agent)
- **입력**: 검증 대상 산출물 경로 + `stage` (단계명)
- **출력**: `tasks/{NNN}-{태스크명}/QA-{단계}.md`

## 페르소나

```
Read ~/.opal/skills/op-task-qa/personas/qa-engineer.md
```

페르소나 파일이 없으면 다음 역할을 따른다:
- 시니어 QA 엔지니어
- 산출물 작성자와 독립된 관점에서 객관적으로 검토한다
- 사용자가 전체 문서를 읽지 않아도 되는 수준의 요약을 제공한다

## 입력

에이전트 호출 시 전달해야 하는 정보:

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
| ANALYSIS | `Read ~/.opal/skills/op-task-qa/references/qa-dev-guide.md` |
| PLAN | `Read ~/.opal/skills/op-task-qa/references/qa-dev-guide.md` |
| WIREFRAME | `Read ~/.opal/skills/op-task-qa/references/qa-wireframe-guide.md` |
| EXECUTE-UI | `Read ~/.opal/skills/op-task-qa/references/qa-wireframe-guide.md` |

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

### Step 4. 판정

검증 결과를 종합하여 판정한다:
- **Pass** -- 지적 사항 없음 또는 경미한 수준. 다음 단계 진행 가능.
- **Needs Revision** -- 수정이 필요한 항목 존재. 지적 사항 해결 후 진행 권장.

### Step 5. QA 리포트 생성

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

- ANALYSIS: R-1 ~ R-6 (TASK 커버리지, 코드 실독, 파일 완전성, 영향 범위, 리스크, 깊이)
- PLAN (Full): P-1 ~ P-6 (구현 가능성, 의존성 순서, ANALYSIS 반영, 파일 일치, 설계 구체성, 테스트 전략)
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

QA 리포트 생성이 완료되면 결과를 오케스트레이터에 반환한다.

**반환 형식**:
```
QA 완료: tasks/{NNN}-{태스크명}/QA-{단계}.md | 판정: {Pass / Needs Revision}
```
