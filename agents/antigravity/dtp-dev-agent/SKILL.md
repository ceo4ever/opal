---
name: dtp-dev-agent
description: |
  **dev-task-pilot 워커 에이전트**. Full Task / Short Task 파이프라인의 각 단계를 실행합니다.
  Antigravity에서는 서브 에이전트 기능이 없으므로, 메인 에이전트가 이 SKILL.md를 Read하고 지시에 따라 직접 실행한다.
model: gemini-3.1-pro
---

# dtp-dev-agent (폴백 모드)

## 실행 방식

Antigravity에서는 서브 에이전트가 지원되지 않으므로, 오케스트레이터가 이 스킬을 Read하여 직접 실행한다.

## 역할

- 오케스트레이터로부터 지시받은 단계를 수행
- Full Task / Short Task 공용 워커
- 산출물(.md)을 작성하거나 코드를 구현/수정
- 완료 시 결과를 오케스트레이터에 반환

## 실행 프로세스

1. 오케스트레이터 프롬프트에서 **단계**, **태스크 폴더 경로**, **가이드 경로**를 확인한다
2. 프로젝트 설정 파일을 읽어 코드 컨벤션을 파악한다
3. 해당 단계의 `references/` 가이드를 읽고 프로세스를 따른다
4. 이전 단계 산출물이 있으면 읽어서 컨텍스트를 확보한다
5. 산출물을 작성하거나 코드를 구현한다
6. 완료 시 결과를 반환한다

## 단계별 가이드 매핑

| 단계 | 가이드 파일 | 산출물 |
|------|-----------|--------|
| ANALYSIS | references/analysis-guide.md | ANALYSIS.md |
| PLAN (Full) | references/plan-guide.md (Full Task 섹션) | PLAN.md |
| PLAN-SHORT | references/plan-guide.md (Short Task 섹션) | PLAN.md |
| TODO | references/todo-guide.md | TODO.md |
| TEST-SCENARIO | references/test-scenario-guide.md | TEST-SCENARIO.md |
| EXECUTE | references/execute-guide.md | 코드 변경 |
| EXECUTE-SHORT | references/execute-guide.md | 코드 변경 |

## 반환 형식

완료 시 아래 정보를 반환한다:

- **artifact_path**: 생성/수정한 산출물 경로
- **summary**: 핵심 요약 (3~5줄)
- **status**: `success` | `blocked`
- **blockers**: 블로커 목록 (있는 경우)
- **changed_files**: 변경 파일 목록 (EXECUTE/EXECUTE-SHORT 시)

## 실행 규칙

1. 가이드의 프로세스를 순서대로 따른다 -- 임의 생략 금지
2. 산출물은 지정된 경로에 작성한다
3. 프로젝트 설정 파일의 코드 컨벤션을 준수한다
4. 블로커 발생 시 즉시 `status: blocked`로 반환한다
5. **QA 에이전트는 호출하지 않는다** -- 오케스트레이터가 별도 호출

## EXECUTE 단계 추가 규칙

### Full Task: 단순 모드

- Step 순서대로 직접 실행한다
- 각 Step 완료 시 TODO.md의 체크박스를 갱신한다
- Part B QA 체크리스트를 인라인으로 검증한다

### Full Task: 복잡 모드

- Antigravity에서는 중첩 서브 에이전트가 불가하므로, 오케스트레이터가 Part C 토폴로지에 따라 직접 배치 실행한다

### Short Task (EXECUTE-SHORT)

- PLAN.md의 체크리스트를 순서대로 직접 실행한다
- 각 Step 완료 시 PLAN.md의 체크박스를 갱신한다
- PLAN.md의 QA 체크리스트를 인라인으로 검증한다
