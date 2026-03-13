# TASK: task-flow Full Task / Short Task 듀얼 모드 분리

> 작성일: 2026-03-13 | 작업 유형: 기능 개선

## 작업 목표

task-flow 스킬을 Full Task(기존 5단계)와 Short Task(경량 3단계)로 분리하여, 작업 난이도에 따라 적절한 파이프라인을 선택할 수 있게 한다.

## 배경

현재 task-flow는 모든 작업에 동일한 5단계 파이프라인(TASK→RESEARCH→PLAN→TODO→EXECUTE)을 적용한다. 간단한 버그 수정이나 설정 변경 같은 작업에도 5단계를 모두 거치면 오버헤드가 크다. 반대로 대규모 신규 개발은 기존 파이프라인이 적합하다. 작업 규모에 맞는 2가지 모드를 제공하여 효율을 높인다.

또한 Full Task의 QA/검토 빈도도 조정한다. 현재 매 단계마다 QA + 사용자 검토(5회)를 하지만, TASK와 TODO 단계의 QA는 생략하고 사용자 검토만 수행하는 것으로 간소화한다.

## 요구사항

### R1. Full Task 모드 (기존 개선)

- [ ] R1.1 파이프라인: TASK → RESEARCH → PLAN → TODO → EXECUTE (5단계 유지)
- [ ] R1.2 TASK 단계: QA 생략, 사용자 검토 요청 → 승인 시 RESEARCH 진행
- [ ] R1.3 RESEARCH 단계: QA 수행 후 사용자 검토 요청 → 승인 시 PLAN 진행
- [ ] R1.4 PLAN 단계: QA 수행 후 사용자 검토 요청 → 승인 시 TODO 진행
- [ ] R1.5 TODO 단계: QA 생략, 사용자 검토 요청 → 승인 시 EXECUTE 진행
- [ ] R1.6 EXECUTE 단계: 각 실행 항목 완료 시 TODO.md 체크리스트 `[ ]` → `[x]` 갱신
- [ ] R1.7 EXECUTE 완료 후 QA 수행 → 사용자에게 완료 보고

### R2. Short Task 모드 (신규)

- [ ] R2.1 파이프라인: TASK → PLAN(통합) → EXECUTE (3단계)
- [ ] R2.2 TASK 단계: QA 생략, 사용자 검토 요청 → 승인 시 PLAN 진행
- [ ] R2.3 PLAN(통합): RESEARCH+PLAN+TODO를 하나의 PLAN.md로 통합
  - 코드베이스 분석 (RESEARCH 핵심)
  - 구현 방향 (PLAN 핵심)
  - 실행 체크리스트 (TODO Part A 수준)
  - QA 체크리스트 (TODO Part B 간소화)
- [ ] R2.4 PLAN 단계: QA 수행 후 사용자 검토 요청 → 승인 시 EXECUTE 진행
- [ ] R2.5 EXECUTE 단계: 각 실행 항목 완료 시 PLAN.md 실행 체크리스트 `[ ]` → `[x]` 갱신
- [ ] R2.6 EXECUTE 완료 후 QA 수행 → 사용자에게 완료 보고

### R3. 모드 판별

- [ ] R3.1 TASK 단계에서 모드를 자동 판별하여 사용자에게 제안
- [ ] R3.2 Short Task 진입 조건 (모든 조건 충족 시):
  - 예상 변경 파일 ≤3개
  - 예상 Step 수 ≤5개
  - 단일 모듈 범위
  - 외부 의존성 없음
  - 작업 유형: 버그 수정, 단순 기능 수정, 설정 변경, 문서 수정
- [ ] R3.3 사용자가 모드를 오버라이드할 수 있어야 함
- [ ] R3.4 Short Task 진행 중 복잡도가 예상보다 높으면 Full Task로 에스컬레이션

### R4. 산출물 구조

- [ ] R4.1 Full Task 산출물: TASK.md, RESEARCH.md, QA-RESEARCH.md, PLAN.md, QA-PLAN.md, TODO.md, QA-EXECUTE.md
- [ ] R4.2 Short Task 산출물: TASK.md, PLAN.md, QA-PLAN.md, QA-EXECUTE.md
- [ ] R4.3 기존 산출물 저장 경로(`tasks/{NNN}-{name}/`) 유지

### R5. 파일 변경 범위

- [ ] R5.1 `skills/task-flow/SKILL.md` — 메인 스킬 파일 개선
- [ ] R5.2 `skills/task-flow/references/` — 필요 시 가이드 파일 수정
- [ ] R5.3 `agents/claude/task-flow-qa/AGENT.md` — QA 호출 단계 변경 반영
- [ ] R5.4 `CLAUDE.md` — 워크플로우 개요 업데이트
- [ ] R5.5 3개 플랫폼(claude, cursor, antigravity) 에이전트 파일 동기화

## 제약 조건

- 기존 task-flow의 핵심 원칙(구현 금지 원칙, 게이트 체크포인트 등) 유지
- 기존 에이전트(task-flow-qa, task-flow-planner, task-flow-test)와의 호환성 유지
- 3개 플랫폼(Claude Code, Cursor, Antigravity) 모두 적용 가능한 구조
- references/ 하위 가이드 파일도 모드 분기에 맞게 수정

## 관련 문서

- `skills/task-flow/SKILL.md` — 현행 task-flow 스킬
- `skills/task-flow/references/` — 단계별 상세 가이드
- `agents/claude/task-flow-qa/AGENT.md` — QA 에이전트
- `agents/claude/task-flow-planner/AGENT.md` — Planner 에이전트
- `agents/claude/task-flow-test/AGENT.md` — Test 에이전트
