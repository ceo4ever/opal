# PLAN: Short Task 기본 모드 전환 및 판별 조건 개선

> 작성일: 2026-03-15 | 모드: Short Task | 참조: TASK.md

## 1. 코드 분석

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `skills/task-flow/SKILL.md` | task-flow 스킬 본체 — 모드 판별 규칙, 에스컬레이션 규칙, 워크플로우 개요 등 | O |
| `CLAUDE.md` | 프로젝트 루트 컨벤션 — Core Workflow 모드 판별 설명 | O |

### 현재 구현

**SKILL.md — 모드 판별 규칙 (63~91행)**

현재 Short Task 진입 조건은 5개 AND 조건:

| # | 조건 | 판별 방법 |
|---|------|----------|
| 1 | 예상 변경 파일 ≤3개 | TASK.md 요구사항에서 추정 |
| 2 | 예상 Step 수 ≤5개 | 요구사항 분해 시 추정 |
| 3 | 단일 모듈 범위 | 요구사항이 하나의 모듈/레이어에 한정 |
| 4 | 외부 의존성 없음 | 새 API, 패키지, 도구 불필요 |
| 5 | 작업 유형 적합 | 버그 수정, 단순 기능 수정, 설정 변경, 문서 수정 |

**하나라도 미충족하면 Full Task** → 대부분의 작업이 Full로 빠지는 원인.

에스컬레이션 규칙: Short 진행 중 `Step > 5 또는 변경 파일 > 3` 시 Full 전환 제안.

사용자 오버라이드: "Full로 해줘" / "Short로 해줘"로 강제 가능.

**CLAUDE.md — 모드 판별 (183행)**

```
**모드 판별**: TASK 단계에서 자동 판별 (변경 파일 ≤3, Step ≤5, 단일 모듈, 외부 의존성 없음 → Short Task). 사용자가 오버라이드 가능.
```

**SKILL.md — 워크플로우 개요 다이어그램, Short Task 부제 (177행, CLAUDE.md)**

- SKILL.md 11행 description: `Short Task: TASK → PLAN(통합) → EXECUTE (간단한 버그 수정, 설정 변경 등)`
- CLAUDE.md 177행: `### Short Task (간단한 버그 수정, 설정 변경 등)`

이들 부제/설명도 Short가 "간단한 작업 전용"이라는 뉘앙스를 주므로 수정 필요.

### 영향 범위

- **SKILL.md 내부 참조**: 모드 판별 규칙 → TASK 단계 보고 형식 (446~464행), 에스컬레이션 규칙 (86~91행), Short Task 경로 에스컬레이션 확인 (691~697행)
- **CLAUDE.md 내부 참조**: 모드 판별 한 줄 설명 (183행), Short Task 부제 (177행)
- **다른 파일 영향 없음**: plan-guide.md, execute-guide.md, research-guide.md, todo-guide.md, 에이전트 파일들은 모드 판별 로직을 참조하지 않으므로 변경 불필요

## 2. 구현 계획

### 변경 파일

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `skills/task-flow/SKILL.md` | 모드 판별 규칙 역전 + 에스컬레이션 규칙 갱신 + 부제/설명 수정 |
| 2 | `CLAUDE.md` | 모드 판별 설명 동기화 + Short Task 부제 수정 |

### 핵심 설계

#### 변경 1: SKILL.md — 모드 판별 규칙 섹션 전면 교체

**Before** (63~91행 전체):
```
## 모드 판별 규칙

### Short Task 진입 조건
... (5개 AND 조건) ...
**하나라도 미충족하면 Full Task.**

### 사용자 오버라이드
...

### 에스컬레이션 규칙
Short Task 진행 중 PLAN 작성 시 복잡도가 예상보다 높아진 경우:
- Step 수 > 5 또는 변경 파일 > 3 → 에스컬레이션 제안
- 사용자 승인 시 Full Task로 전환 (TASK.md 유지, RESEARCH부터 시작)
```

**After**:
```
## 모드 판별 규칙

### 기본 모드: Short Task

모든 작업은 Short Task로 시작한다. Short Task는 단계를 줄여 속도를 높이는 것이지, 분석 품질을 낮추는 것이 아니다.

### Full Task 트리거 조건

아래 조건 중 하나라도 해당하면 Full Task를 **제안**한다 (최종 결정은 사용자):

| # | 조건 | 판별 방법 |
|---|------|----------|
| 1 | 사용자 명시 요청 | "Full로 해줘" 등 사용자가 직접 지정 |
| 2 | 예상 변경 파일 ≥10개 | TASK.md 요구사항에서 추정 (대규모 변경) |
| 3 | 다단계 기술 의사결정 필요 | 아키텍처 선택, 기술 스택 비교 등 별도 RESEARCH가 필요한 수준 |
| 4 | 다중 모듈 간 연쇄 영향 | 변경 A가 B, C에 연쇄적으로 영향하여 독립적 분석이 필요 |

**조건 2~4에 해당하면 Full Task를 제안하되, 사용자가 "Short로 해줘"라고 하면 Short로 진행한다.**

### 사용자 오버라이드

사용자가 모드를 지정할 수 있다:
- "Full로 해줘" → Full Task 강제
- "Short로 해줘" → Short Task 강제
- 지정하지 않으면 자동 판별 결과를 따름

### 에스컬레이션 규칙

Short Task 진행 중 PLAN 작성 시 Full Task 조건에 해당하는 상황이 발견된 경우:
- 예상 변경 파일 ≥10개, 다단계 기술 의사결정 필요, 다중 모듈 간 연쇄 영향 중 하나라도 해당 → 에스컬레이션 제안
- 사용자 승인 시 Full Task로 전환 (TASK.md 유지, RESEARCH부터 시작)
```

#### 변경 2: SKILL.md — description 및 부제 수정

- **5행** description의 Short Task 설명:
  - Before: `Short Task: TASK → PLAN(통합) → EXECUTE (간단한 버그 수정, 설정 변경 등)`
  - After: `Short Task: TASK → PLAN(통합) → EXECUTE (기본 모드, 대부분의 작업)`

- **Short Task 경로 에스컬레이션 확인 (691~697행)** 기준 갱신:
  - Before: `Step 수 > 5`, `변경 파일 > 3`, `다중 모듈에 걸치는 변경 발견`
  - After: `예상 변경 파일 ≥10개`, `다단계 기술 의사결정 필요`, `다중 모듈 간 연쇄 영향`

#### 변경 3: CLAUDE.md — 모드 판별 설명 및 부제 동기화

- **177행** Short Task 부제:
  - Before: `### Short Task (간단한 버그 수정, 설정 변경 등)`
  - After: `### Short Task (기본 모드)`

- **165행** Full Task 부제:
  - Before: `### Full Task (복잡하거나 난이도 높은 작업)`
  - After: `### Full Task (대규모 변경, 사용자 요청 시)`

- **183행** 모드 판별 설명:
  - Before: `**모드 판별**: TASK 단계에서 자동 판별 (변경 파일 ≤3, Step ≤5, 단일 모듈, 외부 의존성 없음 → Short Task). 사용자가 오버라이드 가능.`
  - After: `**모드 판별**: 모든 작업은 Short Task로 시작. Full Task 트리거 (변경 파일 ≥10, 다단계 기술 의사결정, 다중 모듈 연쇄 영향) 해당 시 Full을 제안하고 사용자가 결정.`

## 3. 실행 체크리스트

- [x] Step 1: 모드 판별 규칙 역전 — `skills/task-flow/SKILL.md` — "모드 판별 규칙" 섹션(63~91행)을 새 내용으로 교체 (Short 기본, Full 트리거 조건, 에스컬레이션 갱신)
- [x] Step 2: SKILL.md 부제/설명 수정 — `skills/task-flow/SKILL.md` — description(5행)의 Short Task 설명 변경 + 에스컬레이션 확인(691~697행) 기준 갱신
- [x] Step 3: CLAUDE.md 동기화 — `CLAUDE.md` — Full/Short 부제(165, 177행) + 모드 판별 설명(183행) 수정

## 4. QA 체크리스트

### 기능 테스트
- [x] SKILL.md의 모드 판별 규칙이 "Short 기본 + Full 트리거" 구조로 변경되었는가
- [x] Full Task 트리거 조건 4개 (사용자 명시, 파일 ≥10, 다단계 의사결정, 연쇄 영향)가 정확히 기술되었는가
- [x] 에스컬레이션 규칙이 Full Task 트리거 조건(2~4)과 일치하는가
- [x] CLAUDE.md의 모드 판별 설명이 SKILL.md와 동기화되었는가

### 회귀 테스트
- [x] Full Task / Short Task의 산출물 구조, 게이트 체크포인트, QA 호출 규칙이 변경되지 않았는가
- [x] 사용자 오버라이드 기능이 유지되는가
- [x] 워크플로우 다이어그램(42~57행)이 훼손되지 않았는가
- [x] description의 Full Task 설명이 훼손되지 않았는가

### 코드 품질
- [x] 마크다운 테이블 정렬이 올바른가
- [x] 기존 문서 스타일(용어, 어투)과 일관성이 유지되는가
- [x] "제안"과 "강제"의 구분이 명확한가
