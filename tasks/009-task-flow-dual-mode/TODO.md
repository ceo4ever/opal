# TODO: task-flow Full Task / Short Task 듀얼 모드 분리

> 작성일: 2026-03-13 | 참조: TASK.md, RESEARCH.md, PLAN.md

## Part A: 실행 체크리스트

> 총 9개 Step | 실행 모드: 단순 (마크다운 파일 수정, 단일 모듈)
> 실행 전략: 3-Batch 병렬 (에이전트 활용)

### 실행 토폴로지

```
Batch 1: [Step 1 — 메인 에이전트 직접] ← 전체 기준 파일
Batch 2: [Step 2, 3, 4, 5, 6, 9 — 서브 에이전트 6개 병렬] ← Step 1에만 의존
Batch 3: [Step 7, 8 — 서브 에이전트 2개 병렬] ← Step 6에 의존
```

---

### Step 1: SKILL.md 전면 재구성

- [x] 완료
- **파일**: `skills/task-flow/SKILL.md`
- **실행 방법**: direct (메인 에이전트)
- **작업 내용**:
  - frontmatter description에 Short Task 언급 추가
  - 워크플로우 개요를 듀얼 모드 다이어그램으로 교체
  - "모드 판별 규칙" 섹션 신규 추가 (Short Task 진입 조건 5개, 오버라이드, 에스컬레이션)
  - STEP 1 TASK: QA 호출 제거 → 사용자 검토만 + 모드 판별/제안
  - Full Task 경로 (STEP 2~5):
    - STEP 2 RESEARCH: QA 호출 + 사용자 검토 (기존 유지)
    - STEP 3 PLAN: QA 호출 + 사용자 검토 (기존 유지)
    - STEP 4 TODO: QA 호출 제거 → 사용자 검토만
    - STEP 5 EXECUTE: 체크리스트 `[ ]`→`[x]` 갱신 규칙 추가, QA 호출 유지
  - Short Task 경로 신규:
    - STEP 2 PLAN(통합): 통합 PLAN 가이드 참조, QA 호출 + 사용자 검토
    - STEP 3 EXECUTE: PLAN.md 체크리스트 `[ ]`→`[x]` 갱신, QA 호출
  - 산출물 저장 구조에 Full/Short 분기 추가
  - 게이트 체크포인트: QA 있는 단계만 QA 요약 포함
  - 실행 모드 예시에 Short Task 예시 추가
- **완료 기준**: SKILL.md가 Full/Short 두 경로를 명확히 분기하고, 각 단계의 QA 호출 여부가 TASK.md R1/R2 요구사항과 일치
- **의존**: 없음

### Step 2: plan-guide.md — Short Task 통합 PLAN 가이드 추가

- [x] 완료
- **파일**: `skills/task-flow/references/plan-guide.md`
- **실행 방법**: sub-agent (Batch 2)
- **작업 내용**:
  - 기존 내용은 "Full Task PLAN" 섹션으로 명시
  - "Short Task 통합 PLAN" 섹션 추가: 코드 분석 + 구현 계획 + 실행 체크리스트 + QA 체크리스트
  - Short Task PLAN.md 출력 템플릿 추가 (PLAN.md 3.4절 참조)
  - Short Task 품질 체크리스트 추가
  - QA 에이전트 호출 안내 (Short Task에서도 PLAN QA 필수)
- **완료 기준**: Short Task 통합 PLAN 템플릿과 가이드가 포함
- **의존**: Step 1

### Step 3: research-guide.md — Full Task 전용 명시

- [x] 완료
- **파일**: `skills/task-flow/references/research-guide.md`
- **실행 방법**: sub-agent (Batch 2)
- **작업 내용**:
  - 파일 상단에 "이 가이드는 Full Task 모드에서 사용된다" 명시
  - Short Task에서는 plan-guide.md의 "코드 분석" 섹션을 참조하라는 안내 추가
- **완료 기준**: Full Task 전용임이 명확히 표시
- **의존**: Step 1

### Step 4: todo-guide.md — Full Task 전용 + 체크박스 통일

- [x] 완료
- **파일**: `skills/task-flow/references/todo-guide.md`
- **실행 방법**: sub-agent (Batch 2)
- **작업 내용**:
  - 파일 상단에 "이 가이드는 Full Task 모드에서 사용된다" 명시
  - Step 항목에 `- [ ] 완료` 체크박스 추가 (기존 `- **상태**: ⬜ 대기` 교체)
  - 상태 표시 규칙 섹션: 이모지 상태(`⬜🔄✅🚫`) 폐지 → 체크박스(`[ ]`/`[x]`) + 블로커 시 인라인 메모
  - TODO.md 출력 형식 템플릿 업데이트
  - QA 에이전트 호출 관련 문구 제거 (TODO QA 생략)
- **완료 기준**: 체크박스 형식 통일, Full Task 전용 명시
- **의존**: Step 1

### Step 5: execute-guide.md — 체크리스트 갱신 규칙

- [x] 완료
- **파일**: `skills/task-flow/references/execute-guide.md`
- **실행 방법**: sub-agent (Batch 2)
- **작업 내용**:
  - "체크리스트 갱신 규칙" 섹션 추가/수정:
    - Full Task: TODO.md `- [ ] 완료` → `- [x] 완료`
    - Short Task: PLAN.md `- [ ] Step N` → `- [x] Step N`
  - 상태 갱신 규칙 섹션: 이모지 상태 테이블 폐지 → 체크박스 갱신으로 교체
  - 단순/복잡 모드 실행 규칙에서 상태 갱신 부분 업데이트
  - Short Task 실행 규칙 추가 (PLAN.md 기반 실행)
- **완료 기준**: Full/Short 모두의 체크리스트 갱신 규칙이 명확
- **의존**: Step 1

### Step 6: QA 에이전트 (claude) 수정

- [x] 완료
- **파일**: `agents/claude/task-flow-qa/AGENT.md`
- **실행 방법**: sub-agent (Batch 2)
- **작업 내용**:
  - 호출 시점 다이어그램을 Full/Short 분기로 변경
  - 입력 필드에 `mode` (`full`/`short`) 추가
  - TASK 검증 기준, TODO 검증 기준: "호출되지 않음 (Full/Short 모두)" 명시
  - Short Task PLAN 검증 기준 추가 (SP-1 ~ SP-5, PLAN.md 3.6절 참조)
  - EXECUTE 검증 기준: 체크박스 갱신 확인 항목 추가
  - 산출물 읽기 테이블에 Short Task 경우 추가 (PLAN.md만 읽기)
- **완료 기준**: Full/Short 모드별 검증 기준이 명확히 분리
- **의존**: Step 1

### Step 7: QA 에이전트 (cursor) 동기화

- [x] 완료
- **파일**: `agents/cursor/task-flow-qa.md`
- **실행 방법**: sub-agent (Batch 3)
- **작업 내용**: Step 6 완성된 claude 버전의 내용을 cursor 포맷으로 동기화
- **완료 기준**: claude 버전과 내용 동일
- **의존**: Step 6

### Step 8: QA 에이전트 (antigravity) 동기화

- [x] 완료
- **파일**: `agents/antigravity/task-flow-qa/SKILL.md`
- **실행 방법**: sub-agent (Batch 3)
- **작업 내용**: Step 6 완성된 claude 버전의 내용을 antigravity 포맷(SKILL.md)으로 동기화
- **완료 기준**: claude 버전과 내용 동일
- **의존**: Step 6

### Step 9: CLAUDE.md Core Workflow 업데이트

- [x] 완료
- **파일**: `CLAUDE.md`
- **실행 방법**: sub-agent (Batch 2)
- **작업 내용**:
  - "Core Workflow: task-flow" 섹션의 다이어그램을 듀얼 모드로 교체
  - 핵심 규칙에 모드 판별 언급 추가
  - 산출물 저장 구조에 Short Task 산출물 추가
- **완료 기준**: CLAUDE.md가 SKILL.md의 듀얼 모드를 정확히 반영
- **의존**: Step 1

---

## Part B: QA 체크리스트

### B-1. 기능 테스트

- [ ] Full Task 파이프라인: TASK(검토)→RESEARCH(QA+검토)→PLAN(QA+검토)→TODO(검토)→EXECUTE(QA+보고) 흐름이 SKILL.md에 일관
- [ ] Short Task 파이프라인: TASK(검토)→PLAN(QA+검토)→EXECUTE(QA+보고) 흐름이 SKILL.md에 일관
- [ ] 모드 판별 조건 5개가 SKILL.md에 정확히 기술
- [ ] 에스컬레이션 규칙이 SKILL.md에 포함
- [ ] Short Task 통합 PLAN 템플릿이 plan-guide.md에 포함
- [ ] 체크박스 갱신 규칙이 execute-guide.md에 Full/Short 모두 기술

### B-2. 회귀 테스트

- [ ] Full Task의 RESEARCH, PLAN 단계 QA 호출 로직이 기존과 동일하게 동작
- [ ] Full Task 복잡 모드의 Planner/Test 에이전트 호출 경로가 변경되지 않음
- [ ] 기존 에이전트(planner, test) 파일이 수정되지 않음
- [ ] execute-plan-guide.md가 수정되지 않음

### B-3. 코드 품질

- [ ] 모든 수정 파일의 마크다운 형식이 올바름
- [ ] QA 에이전트 3개 플랫폼 파일의 핵심 내용이 동일
- [ ] CLAUDE.md의 다이어그램이 SKILL.md와 일치
- [ ] references/ 가이드의 QA 호출 안내가 SKILL.md와 일치
