---
name: opal-pilot-project
description: |
  **프로젝트 범용 오케스트레이터**. 문서 작성, 간단한 코드 수정, 설정 변경, 워크플로우 수행 등 프로젝트의 모든 범용 태스크를 3단계 파이프라인으로 수행한다.
  반드시 이 스킬을 사용해야 하는 상황: "opal-pilot-project", "opp".
  코드 개발 태스크는 opal-pilot-dev-short(opds)를, 기획 산출물 세트는 opal-pilot-write-tech(opwt)를 사용한다.
---

# opal-pilot-project (프로젝트 범용 오케스트레이터)

## Harness

모드: Project Task (TASK → PLAN → EXECUTE)
> 부트스트랩에서 로드되지 않은 경우: `~/.opal/references/opal-harness.md`를 Read한다.

---

## STEP 1: TASK

harness "4. TASK 공통 프로세스" 참조. 다음 단계명: PLAN.

---

## STEP 2: PLAN

워커를 디스패치하여 범용 실행 계획을 수립한다.

### PLAN 디스패치

op-task-plan 워커 디스패치. **model**: advanced. 이전 산출물: TASK.md.

탐색 경로:
1. `{프로젝트}/.opal/skills/op-task-plan/SKILL.md`
2. `~/.opal/skills/op-task-plan/SKILL.md`

워커 완료 -> **QA Gate** (op-task-qa) -> **PM Gate** -> 사용자에게 보고.

보고 형식:
```
📋 [PLAN] 완료 보고
📎 산출물: tasks/{NNN}-{태스크명}/PLAN.md
다음 단계(EXECUTE)로 넘어갈까요?
```

**승인 = EXECUTE 시작 허가**

---

## STEP 3: EXECUTE

op-task-execute 워커 디스패치. **model**: standard. checklist_source: PLAN.md 섹션 "3. 실행 체크리스트".

탐색 경로:
1. `{프로젝트}/.opal/skills/op-task-execute/SKILL.md`
2. `~/.opal/skills/op-task-execute/SKILL.md`

### EXECUTE 완료 후

워커가 changed_files를 반환하면:
1. **PM Gate** — .opal/AGENT.md 기준 실행 결과 검토 (리네이밍 잔여, 문서 일관성 등)
2. **DONE.md 생성**
3. 사용자에게 완료 보고

보고 형식:
```
✅ [EXECUTE] 완료 보고
📎 변경 파일: {changed_files}
📎 산출물: tasks/{NNN}-{태스크명}/DONE.md
태스크가 완료되었습니다.
```

> TEST-SCENARIO 없음: 범용 작업은 코드 테스트가 불필요하다.

---

## STATE.md 도메인 치환값

| 필드 | 값 |
|------|------|
| 모드 | Project Task |
| 단계 목록 | TASK / PLAN / EXECUTE |
| 산출물 목록 | TASK.md, PLAN.md, QA-*.md, DONE.md |

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-03-29 | 초기 작성 — opal-pilot-dev-short 기반 범용화 (TEST-SCENARIO 제거, op-task-plan/op-task-execute 사용) |
| v1.1 | 2026-03-29 | op-plan → op-task-plan, op-execute → op-task-execute 리네이밍 반영. EXECUTE 완료 후 PM Gate 추가 |
| v1.2 | 2026-03-29 | model override를 레벨 기반으로 전환 (044) |
| v1.3 | 2026-03-30 | opal-project-pilot → opal-pilot-project 리네이밍 + 정체성 정비 (052) |
