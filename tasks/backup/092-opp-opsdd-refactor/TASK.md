# TASK: opsdd 스킬 개선 — 폴더 통합 + 단계 경량화

> 작성일: 2026-04-07 | 작업 유형: 개선 | 적용 스킬: opp | 모드: interactive
> 입력: 사용자 요청 + 이미지(specs/002, tasks/024 분리 현황)
> 출력: PLAN.md (개선 방향 설계)

## 작업 목표

opsdd 스킬의 세 가지 문제를 해결한다:
1. 모든 산출물을 `specs/` 하나로 통합 (tasks/ 혼재 제거)
2. EXECUTE-LOOP에서 기존 pilot 스킬(opds/opd) 연동 문제 해결
3. Verify 단계 간소화 + 토큰 효율화

## 배경

현재 opsdd는 `specs/{NNN}/`과 `tasks/{NNN}-opsdd-*/` 두 곳에 산출물이 분산된다.
이미지 기준: `specs/002-member-management-api/tasks/` + `tasks/024-opsdd-member-management-api/`가 동시 존재.
- specs/tasks 폴더는 스킬이 자동 생성하지 않아 캡틴이 수동 생성함
- 기존 pilot 스킬(opds 등)이 자체적으로 `tasks/` 루트에 폴더를 만들어 경로 충돌
- Verify Phase가 2회 + DONE 검증까지 3회 → 토큰 과다 소비

## 확정된 설계 방향 (대화에서 합의)

1. **specs/ 단일 루트**: TASK.md, STATE.md, DONE.md 포함 모든 산출물을 `specs/{NNN}/` 안에
2. **tasks/ 루트 폴더 미생성**: opsdd 실행 시 `tasks/` 루트에 폴더를 만들지 않음
3. **Verify 간소화**: 토큰 효율화 방향으로 단계 축소 검토

## 요구사항

- [ ] **현재 폴더 구조 문제 분석**
  - 무엇을: tasks/ 루트 폴더가 생기는 원인, specs/tasks/ 자동 생성 안 되는 원인 파악
  - AC: 원인과 수정 지점이 명확히 식별됨

- [ ] **신규 폴더 구조 설계**
  - 무엇을: specs/ 단일 루트 기준 전체 구조 재설계
  - AC: TASK.md/STATE.md/DONE.md 포함 모든 산출물 경로가 specs/{NNN}/ 안에 정의됨

- [ ] **EXECUTE-LOOP pilot 미실행 원인 분석 + 해결 방향**
  - 무엇을: opds/opd를 서브 오케스트레이터로 디스패치하면 이 스킬들이 자체 TASK 단계에서 tasks/ 루트에 폴더를 생성하려 함. task_folder를 specs/로 지정해도 pilot 스킬 내부 로직이 이를 따르지 않아 실행 자체가 안 됨. 이 구조적 문제의 해결 방향 설계
  - AC: EXECUTE-LOOP에서 각 태스크가 specs/{NNN}/tasks/T{N}/ 경로에서 실제로 실행되는 방법이 명시됨

- [ ] **Verify 단계 간소화 설계**
  - 무엇을: SPEC-VERIFY + TASKS-VERIFY 현재 비용 분석, 간소화 방향 제안
  - AC: 단계 수 또는 게이트 수 감소 방향과 품질 트레이드오프가 명시됨

- [ ] **수정 파일 목록 확정**
  - AC: 수정할 파일(SKILL.md, 단계 스킬들)과 각 변경 내용이 명시됨

## 제약 조건

- ~/.opal/ 직접 수정 금지 (소스 경로만 수정)
- 기존 specs/ 구조의 핵심(SPEC.md SSOT 원칙)은 유지
- 이번 태스크는 설계 검토 → PLAN.md가 주 산출물 (구현은 다음 태스크)

## 기술 스택

- Markdown

## 관련 문서

- `opal/skills/opal-pilot-sdd/SKILL.md`
- `opal/skills/op-sdd-spec/SKILL.md`
- `opal/skills/op-sdd-verify/SKILL.md`
- `opal/skills/op-sdd-plan/SKILL.md`
- `opal/skills/op-sdd-tasks/SKILL.md`
