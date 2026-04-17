---
@header
module: tasks/123-260417-opp-citation-rules
layer: task
description: 산출물 인용 위치 추적 하네스 — TASK/ANALYSIS/PLAN에 문서 인용 의무 규칙 적용
---

# TASK: 산출물 인용 위치 추적 하네스 (Citation Rules)

> 작성일: 2026-04-17 | 작업 유형: 개선 | 적용 스킬: opp | 모드: interactive
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

TASK/ANALYSIS/PLAN 산출물에 설계 결정의 근거 문서 + 위치를 인용하는 규칙을 필수 하네스로 도입한다.
사람과 AI 모두 인용을 통해 원본 문서를 즉시 탐색할 수 있게 한다.

## 배경

현재 워커는 문서를 읽고 설계를 작성하지만, 산출물(TASK.md / ANALYSIS.md / PLAN.md)에 어떤 문서의 어느 위치를 근거로 결정했는지 기록하지 않는다.

- **사람**: 설계 결정의 근거를 역추적할 수 없고, 원본 문서를 찾아가는 데 시간이 걸린다
- **AI**: 다음 단계에서 같은 문서를 다시 찾아야 하며, 인용 위치가 없으면 섹션을 직접 탐색해야 한다

## 배경 분석 (대화에서 도출)

### 현재 인용 처리 현황

| 레이어 | 현황 |
|--------|------|
| PM → 워커 주입 | `[MUST] 문서명 §N: 원문` 형식 존재 (`opal-pm.md §3 Step 3`) |
| TASK.md 산출물 | 인용 위치 없음 — "관련 문서" 경로 목록만 있음 |
| ANALYSIS.md 산출물 | 인용 위치 없음 |
| PLAN.md 산출물 | 인용 위치 없음 — §8 기술 컨텍스트에 스킬명만 기록 |
| plan-guide.md | 인용 기록 지시 없음 |
| 하네스 모듈 | citation 전용 모듈 없음 |

### 요구사항 핵심

- 설계 결정에 근거 문서 + 위치(섹션/줄 번호) 인용
- 인용 형식은 PLAN 단계에서 설계 (현재 미확정)
- 사람이 빠르게 원본 접근 가능
- AI가 파일 경로를 인식하여 직접 Read 가능
- 필수 하네스 규칙으로 적용 (베스트 에포트 아님)

## 확정된 설계 방향 (대화에서 합의)

1. **적용 범위**: TASK / ANALYSIS / PLAN 3단계 모두 적용
2. **의무 수준**: 필수 하네스 (optional 아님)
3. **인용 형식**: PLAN 단계에서 설계 후 확정 — 사람+AI 모두 탐색 가능한 형식
4. **하네스 모듈**: 신규 `harness/citation-rules.md` 모듈로 분리

## 요구사항

### R-1. 하네스 citation-rules 모듈 신설
- **무엇을**: `harness/citation-rules.md` 파일 신규 생성
- **어디에**: `opal/core/references/harness/citation-rules.md`
- **왜**: 하네스 §2 모듈 구조에 따라 인용 규칙을 독립 모듈로 관리
- **AC**: 파일이 존재하고, 인용 형식 정의 / 적용 시점 / 의무 수준 / 사람+AI 탐색 가이드가 포함되어 있다

### R-2. opal-harness.md §2 모듈 테이블에 citation-rules 등록
- **무엇을**: §2 하네스 모듈 테이블에 citation-rules 행 추가
- **어디에**: `opal/core/references/opal-harness.md` §2
- **왜**: 하네스 모듈 SSOT 테이블에 등록되어야 로드 규칙이 활성화됨
- **AC**: §2 테이블에 citation-rules 행이 있고, 로드 조건 / 적용 주체 / 적용 시점이 명시되어 있다

### R-3. op-task TASK.md 출력 형식에 인용 필드 추가
- **무엇을**: TASK.md "관련 문서" 섹션을 인용 테이블 형식으로 확장
- **어디에**: `opal/skills/op-task/SKILL.md` TASK.md 템플릿
- **왜**: TASK 단계에서 참조한 문서의 위치를 워커가 기록하도록 의무화
- **AC**: TASK.md 템플릿에 문서명/경로/섹션/인용 내용 컬럼이 있는 테이블 구조가 포함되어 있다

### R-4. op-dev-analysis ANALYSIS.md 출력 형식에 인용 필드 추가
- **무엇을**: ANALYSIS.md 각 분석 항목에 인용 위치 기록 필드 추가
- **어디에**: `opal/skills/op-dev-analysis/SKILL.md` ANALYSIS.md 통일 형식
- **왜**: 코드 분석 근거(파일 경로, 줄 번호)와 문서 근거(§N)를 함께 추적
- **AC**: ANALYSIS.md 형식에 분석 근거(코드/문서) 인용 필드가 포함되어 있다

### R-5. op-dev-plan PLAN.md 출력 형식 + plan-guide에 인용 규칙 적용
- **무엇을**: PLAN.md 설계 섹션(§3)에 인라인 인용 + §8에 참조 문서 테이블 추가, plan-guide에 인용 작성 지시 추가
- **어디에**: `opal/skills/op-dev-plan/SKILL.md`, `opal/skills/op-dev-plan/references/plan-guide.md`
- **왜**: 설계 결정의 근거를 섹션 단위로 추적 가능하게 함
- **AC**: PLAN.md §3 설계 섹션에 인용 필드가 있고, §8에 참조 문서 테이블이 있다. plan-guide 3단계에 인용 작성 지시가 포함되어 있다

### R-6. op-task-plan PLAN.md 출력 형식에 인용 규칙 적용
- **무엇을**: op-task-plan의 PLAN.md 형식에도 동일 인용 구조 적용
- **어디에**: `opal/skills/op-task-plan/SKILL.md`
- **왜**: opp 파이프라인 산출물에도 일관된 인용 규칙 적용
- **AC**: op-task-plan PLAN.md 형식에 인용 필드가 포함되어 있다

## 미확정 사항 (PLAN에서 결정)

- **인용 형식 설계**: 인라인 vs 섹션별 테이블 vs 혼합 방식의 구체적 마크다운 표현
  - 조건: 사람이 읽기 쉽고, AI가 파일 경로로 직접 Read 가능해야 함
  - 코드 근거(파일 경로:줄번호)와 문서 근거(§N) 혼용 시 표현 통일 방법
- **의무 수준 세분화**: 단계별(TASK/ANALYSIS/PLAN) 인용 의무가 동일한지, 차등 적용할지

## 제약 조건

- `~/.opal/` 경로 직접 수정 금지 — 소스(`opal/core/`, `opal/skills/`)에서만 수정 (확정 기준 #2)
- 기존 산출물(TASK.md, ANALYSIS.md, PLAN.md) 레거시 파일 소급 변경 불필요
- 인용이 없는 항목(추론/경험 기반 결정)은 인용 생략 허용 — 단, 문서 근거가 있으면 필수

## 기술 스택

- Markdown 문서 (SKILL.md, 하네스 모듈, 가이드)
- OPAL 하네스 모듈 구조 (`harness/` 폴더)

## 관련 문서

| 문서 | 경로 | 참조 이유 |
|------|------|----------|
| 하네스 공통 | `opal/core/references/opal-harness.md` | §2 모듈 테이블 구조 확인 |
| PM 인용 의무 규칙 | `opal/core/references/opal-pm.md` | §3 Step 3 기존 인용 포맷 참조 |
| op-task 스킬 | `opal/skills/op-task/SKILL.md` | TASK.md 현재 형식 |
| op-dev-analysis 스킬 | `opal/skills/op-dev-analysis/SKILL.md` | ANALYSIS.md 현재 형식 |
| op-dev-plan 스킬 | `opal/skills/op-dev-plan/SKILL.md` | PLAN.md 현재 형식 |
| plan-guide | `opal/skills/op-dev-plan/references/plan-guide.md` | 현재 3단계 가이드 |
| op-task-plan 스킬 | `opal/skills/op-task-plan/SKILL.md` | 범용 PLAN 형식 |
