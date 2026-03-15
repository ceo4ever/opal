---
name: task-flow-agent
description: |
  task-flow 파이프라인의 각 단계(RESEARCH/PLAN/TODO/EXECUTE)를 실행하는 워커 스킬.
  Antigravity에서는 서브 에이전트 기능이 없으므로, 메인 에이전트가 이 SKILL.md를 Read하고 지시에 따라 직접 실행한다.
  가이드의 프로세스 자체는 서브 에이전트 실행과 동일하다.
---

# task-flow 워커 에이전트 (폴백 모드)

> **실행 방식**: Antigravity에서는 서브 에이전트가 지원되지 않으므로, 메인 에이전트가 이 파일을 Read한 후 아래 프로세스를 직접 수행한다. 컨텍스트 격리 이점은 없으나, 동일한 절차와 규칙이 적용된다.

## 역할

- 오케스트레이터(알투)로부터 지시받은 단계(RESEARCH / PLAN / TODO / EXECUTE)를 수행
- 산출물(.md)을 작성하거나 코드를 구현/수정
- 완료 시 결과를 오케스트레이터에 반환

## 실행 프로세스

1. 오케스트레이터 프롬프트에서 **단계**, **태스크 폴더 경로**, **가이드 경로**를 확인한다
2. 프로젝트 CLAUDE.md(또는 프로젝트 설정 파일)를 읽어 코드 컨벤션을 파악한다
3. 해당 단계의 `references/` 가이드를 읽고 프로세스를 따른다
4. 이전 단계 산출물이 있으면 읽어서 컨텍스트를 확보한다
5. 산출물을 작성하거나 코드를 구현한다
6. 완료 시 결과를 반환한다

## 단계별 가이드 매핑

| 단계 | 가이드 파일 | 산출물 |
|------|-----------|--------|
| RESEARCH | references/research-guide.md | RESEARCH.md |
| PLAN (Full) | references/plan-guide.md (Full Task 섹션) | PLAN.md |
| PLAN (Short) | references/plan-guide.md (Short Task 섹션) | PLAN.md |
| TODO | references/todo-guide.md | TODO.md |
| EXECUTE | references/execute-guide.md | 코드 변경 |

## 반환 형식

완료 시 아래 정보를 반환한다:

- **artifact_path**: 생성/수정한 산출물 경로
- **summary**: 핵심 요약 (3~5줄)
- **status**: `success` | `blocked`
- **blockers**: 블로커 목록 (있는 경우)
- **changed_files**: 변경 파일 목록 (EXECUTE 시)

## 실행 규칙

1. 가이드의 프로세스를 순서대로 따른다 -- 임의 생략 금지
2. 산출물은 지정된 경로에 작성한다
3. 프로젝트 CLAUDE.md의 코드 컨벤션을 준수한다
4. 블로커 발생 시 즉시 `status: blocked`로 반환한다
5. **QA 에이전트는 호출하지 않는다** -- 오케스트레이터가 별도 호출

## STATE.md 갱신 책임

EXECUTE 단계에서 워커(또는 메인 에이전트가 폴백 실행 시)가 STATE.md를 갱신한다:

- **Step 완료 시**: `진행: Step N/M 완료` 업데이트
- **블로커 발생 시**: `상태: 블로커` + `블로커` 섹션 업데이트
- **의사결정 시**: `의사결정 로그`에 행 추가

비-EXECUTE 단계(RESEARCH, PLAN, TODO)에서는 STATE.md를 갱신하지 않는다 (오케스트레이터가 관리).

갱신 방법: Edit 도구(write_file)로 해당 섹션만 교체 (1회 수준 오버헤드).

---

## EXECUTE 단계 추가 규칙

### 단순 모드

- Step 순서대로 직접 실행한다
- 각 Step 완료 시 TODO.md(Full) 또는 PLAN.md(Short)의 체크박스를 갱신한다
- Part B QA 체크리스트를 인라인으로 검증한다

### 복잡 모드

- Antigravity에서는 내부 서브 에이전트를 실행할 수 없으므로, 메인 에이전트가 Part C 토폴로지의 배치 순서에 따라 직접 순차 실행한다
- `execute-guide.md`의 프롬프트 구성은 참조하되, 메인 에이전트가 직접 수행하는 폴백 방식으로 실행한다
