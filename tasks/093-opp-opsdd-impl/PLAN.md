# PLAN: opsdd 스킬 구현 — 092 설계 기반

> 작성일: 2026-04-07
> 입력: tasks/092-opp-opsdd-refactor/PLAN.md §8 구현 체크리스트
> 출력: PLAN.md (참조형)

## 참조 계획

이 태스크는 사전 설계 태스크(092)의 PLAN.md §8을 그대로 실행 계획으로 사용한다.

**구현 체크리스트 원본**: `tasks/092-opp-opsdd-refactor/PLAN.md` §8

---

## 구현 범위 요약

| Step | 작업 | 대상 파일 |
|------|------|---------|
| 1 | 폴더 구조 통합 + base_path 조건부 | `opal-harness.md`, `opal-pilot-sdd/SKILL.md` |
| 2 | EXECUTE-LOOP 재작성 | `opal-pilot-sdd/SKILL.md`, `execute-loop-guide.md` |
| 3 | REVIEW Phase + Verify 간소화 | `opal-pilot-sdd/SKILL.md`, `op-sdd-verify/SKILL.md`, `verify-guide.md` |
| 4 | 단계 스킬 수정 | `op-sdd-plan/SKILL.md`, `op-sdd-tasks/SKILL.md`(삭제), `op-sdd-spec/SKILL.md` |
| 5 | 검증 | 전체 흐름 검토 |

## QA 체크리스트

### 기능 테스트
- [x] 5단계 파이프라인(TASK→SPEC→REVIEW→DESIGN→EXECUTE→DONE)이 SKILL.md에 일관되게 반영됨
- [x] tasks/ 단일 루트 구조가 모든 스킬에 반영됨
- [x] base_path 조건부 처리 — 기존 오케스트레이터(opp, opds 등) 동작 영향 없음
- [x] EXECUTE-LOOP에서 op-dev-plan + op-dev-execute 직접 디스패치 명시됨
- [x] op-sdd-tasks 참조가 opal-pilot-sdd/SKILL.md에서 완전히 제거됨

### 일관성 테스트
- [x] op-sdd-verify가 워커 스킬 → PM 레퍼런스로 역할 변경됨 (디스패치 프롬프트 없음)
- [x] op-sdd-plan이 ACT 분해까지 포함하는 SPEC-PLAN.md를 출력하도록 수정됨
- [x] execute-loop-guide.md의 재시도 횟수가 하네스 §1 루핑 제약과 연결됨

### 문서 품질
- [x] 모든 수정 파일의 변경이력에 버전 추가됨
- [x] `~/.opal/` 경로 직접 수정 없음 (소스 경로만 수정)
