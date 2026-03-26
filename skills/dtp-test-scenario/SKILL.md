---
name: dtp-test-scenario
description: |
  **테스트 시나리오 작성 단계 스킬**. TASK.md와 PLAN.md를 기반으로 기능·엣지 케이스·통합 시나리오를 도출하고, 테스트 도구를 사전 결정한다.
  반드시 이 스킬을 사용해야 하는 상황: 오케스트레이터(dtp-dev, dtp-dev-short)가 TEST-SCENARIO 단계를 디스패치할 때.
  필수 입력: TASK.md + PLAN.md. 선택 입력: TODO.md. 보장 출력: TEST-SCENARIO.md.
---

# dtp-test-scenario — 테스트 시나리오 작성

## 실행 컨텍스트

- **호출자**: 오케스트레이터(dtp-dev, dtp-dev-short)가 TEST-SCENARIO 단계를 디스패치
- **실행 주체**: 워커 에이전트 (dtp-dev-agent)
- **입력**: `tasks/{NNN}-{태스크명}/TASK.md` + `PLAN.md` (선택: `TODO.md`)
- **출력**: `tasks/{NNN}-{태스크명}/TEST-SCENARIO.md`

## 페르소나

```
Read ~/.opal/skills/dtp-test-scenario/personas/qa-engineer.md
```

페르소나 파일이 없으면 다음 역할을 따른다:
- 시니어 QA 엔지니어
- 기능·경계값·통합 관점에서 빈틈 없이 시나리오를 도출한다
- 설계 빈틈을 발견하면 즉시 피드백한다

## 프로세스

### Step 1. 테스트 시나리오 가이드 로딩

```
Read ~/.opal/skills/dtp-test-scenario/references/test-scenario-guide.md
```

가이드에 따라 컨텍스트 확인 → 도구 사전 결정 → 시나리오 도출 → 작성 → 설계 검증을 순서대로 수행한다.

### Step 2. TEST-SCENARIO.md 작성

가이드의 프로세스(Step 1~5)를 따라 시나리오를 도출하고 아래 통일 형식으로 작성한다.

## 활용 스킬

| 스킬 | 용도 | 사용 시점 |
|------|------|----------|
| anthropics/webapp-testing | Playwright E2E 테스트 패턴 참조 | E2E 시나리오 도출 시 |
| openai/security-best-practices | 보안 테스트 시나리오 참조 | 보안 시나리오 도출 시 |

## 역할 분배

| 구성요소 | 담당 | 시점 |
|---------|------|------|
| 대상 (뭘 테스트할지) | dtp-dev-agent | PLAN/TODO 완료 후, EXECUTE 전 |
| 조건 (어떤 입력/상태) | dtp-dev-agent | 동일 |
| 기대 결과 (성공 기준) | dtp-dev-agent | 동일 |
| 도구 (어떤 도구로 테스트할지) | dtp-dev-agent | 동일 -- `.opal/test-tools.yaml` 기반 |
| 실행 명령/결과/상세 | dtp-test | EXECUTE 완료 후 |
| 코드 품질/보안/회귀/판정 | dtp-test | EXECUTE 완료 후 |

## TEST-SCENARIO.md 통일 형식

```markdown
# TEST SCENARIO: {태스크 제목}

> 작성일: YYYY-MM-DD | 상태: {작성 완료 / 실행 완료}

## 시나리오 목록

### S-1: {시나리오 제목}

| 항목 | 내용 |
|------|------|
| 대상 | {테스트 대상 기능/변경점} |
| 조건 | {입력, 사전 상태, 환경} |
| 기대 결과 | {성공 기준} |
| 도구 | {dtp-agent가 결정} |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

## 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | _{채움}_ | _{채움}_ | _{채움}_ |
| 2 | 타입 체크 | _{채움}_ | _{채움}_ | _{채움}_ |
| 3 | 포맷터 | _{채움}_ | _{채움}_ | _{채움}_ |

## 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | _{채움}_ | _{채움}_ |
| 2 | .gitignore 확인 | _{채움}_ | _{채움}_ |

## 회귀 테스트

| # | 테스트 스위트 | 결과 | 상세 |
|---|-------------|------|------|
| 1 | _{채움}_ | _{채움}_ | _{채움}_ |

## 판정

**_{dtp-test가 채움: All Pass / Partial Fail / Critical Fail}_ -- _{판정 근거}_**

## 설계 피드백

{시나리오 작성 과정에서 발견한 PLAN/TODO의 빈틈. 없으면 "없음"}
```

## 저장 경로

```
tasks/{NNN}-{태스크명}/TEST-SCENARIO.md
```

기존 TEST-SCENARIO.md가 있으면 version-mgr 규칙에 따라 버전 관리한다.

## 시나리오 작성 체크리스트

TEST-SCENARIO.md 작성 후 자체 검증한다:

- [ ] TASK.md의 모든 요구사항에 대해 시나리오가 존재하는가
- [ ] 각 시나리오의 기대 결과가 구체적이고 검증 가능한가
- [ ] dtp-agent 담당 필드(대상/조건/기대 결과/도구)를 작성하고, dtp-test 담당 필드(실행 명령/결과/상세)는 비워두었는가
- [ ] `.opal/test-tools.yaml` 또는 프로젝트 설정 파일을 참조하여 도구를 결정했는가
- [ ] 문서 전용 태스크인 경우 스킵 규칙을 적용했는가
- [ ] 설계 빈틈 발견 시 피드백 섹션에 기록했는가

## 완료 후 동작

워커는 QA를 직접 호출하지 않는다. TEST-SCENARIO.md 작성이 완료되면 결과를 오케스트레이터에 반환한다.

**반환 형식**:
```
TEST-SCENARIO 완료: tasks/{NNN}-{태스크명}/TEST-SCENARIO.md
```
