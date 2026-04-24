---
name: opal-pilot-project
description: |
  **프로젝트 범용 오케스트레이터**. 문서 작성, 간단한 코드 수정, 설정 변경, 워크플로우 수행 등 프로젝트의 모든 범용 태스크를 3단계 파이프라인으로 수행한다.
  반드시 이 스킬을 사용해야 하는 상황: "opal-pilot-project", "opp".
  코드 개발 태스크는 opal-pilot-dev-short(opds)를, 기획 산출물 세트는 opal-pilot-write-tech(opwt)를 사용한다.
---

# opal-pilot-project (프로젝트 범용 오케스트레이터)

## Harness

모드: Project Task (TASK → PLAN → EXECUTE → CLOSE)
> 부트스트랩에서 로드되지 않은 경우: `~/.opal/references/opal-harness.md`를 Read한다.

**[MUST]** 스킬 시작 즉시 모드에 따라 서브 하네스를 Read한다. 이 단계를 건너뛰면 안 된다:
- `--agentic` 플래그 있음 → `~/.opal/references/opal-harness-agentic.md`를 Read한다
- `--agentic` 없음 (기본) → `~/.opal/references/opal-harness-interactive.md`를 Read한다

> **[MUST]** 산출물 작성·검증 시 `opal/core/references/harness/citation-rules.md`를 Read하여 규칙(근거 제시 원칙 / 트랙별 매트릭스 / [MUST] 토큰 / 영역 간 용어 일관성 / decision_required 계약)을 준수한다.

---

## STEP 1: TASK

harness "4. TASK 공통 프로세스" 참조. 다음 단계명: PLAN.

TASK 완료 → **State Gate** (하네스 §3 참조 — STATE.md 갱신 확인) → 사용자 보고.

---

## STEP 2: PLAN

워커를 디스패치하여 범용 실행 계획을 수립한다.

### PLAN 디스패치

op-task-plan 워커 디스패치. **model**: advanced. 이전 산출물: TASK.md.

탐색 경로:
1. `{프로젝트}/.opal/skills/op-task-plan/SKILL.md`
2. `~/.opal/skills/op-task-plan/SKILL.md`

워커 완료
  → **QA Gate** (op-task-qa — 체크리스트 갱신 포함) → **State Gate**
  → **PM Gate** (체크리스트 갱신 상태 확인 — 하네스 interactive §3 참조. 미갱신 시 QA 재소환) → **State Gate** → 사용자에게 보고.

> **[PM 컨텍스트 주입]** 워커 디스패치 프롬프트의 첫 줄에 `[WORKER]`를 삽입한다. `[WORKER]` 마커가 있으면 워커는 부트스트랩을 생략한다. PM은 디스패치 시 다음을 프롬프트에 포함해야 한다:
> 1. 하네스 Guards 핵심 규칙 (구현 금지 원칙, 커밋 규칙)
> 2. 관련 참조 문서 경로 (docs/PROJECT.md 문서 테이블 기반)
> 3. 기술 스택 연동 지시 (기존 "참조 문서 전달 의무" 통합)

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

> **[PM 컨텍스트 주입]** 디스패치 프롬프트 첫 줄에 `[WORKER]` 삽입. 하네스 Guards 핵심 규칙 + 관련 참조 문서 경로를 포함한다.

### EXECUTE 완료 후

워커가 changed_files를 반환하면:
1. **QA Gate** (op-task-qa) — QA 에이전트 호출 (체크리스트 갱신 포함) → **State Gate**
2. **PM Gate** — QA 결과 + 실행 결과 검토 + **체크리스트 갱신 상태 확인** (하네스 interactive §3 참조). 미갱신 시 QA 에이전트 재소환 → **State Gate**
3. 사용자에게 완료 보고 후 CLOSE 단계 진입 승인 요청

보고 형식:
```
📋 [EXECUTE] 완료 보고
📎 변경 파일: {changed_files}
📎 산출물: {QA-EXECUTE.md 등}
다음 단계(CLOSE)로 넘어갈까요?
```

> TEST-SCENARIO 없음: 범용 작업은 코드 테스트가 불필요하다.

---

## STEP 4: CLOSE

모든 체크리스트 갱신 완료 확인 후 태스크를 마감한다.

1. DONE.md 생성
2. State Gate (하네스 §3 참조)
3. 완료 보고

보고 형식:
```
✅ [CLOSE] 태스크 완료
📎 산출물: tasks/{NNN}-{태스크명}/DONE.md
태스크가 완료되었습니다.
```

> **추가작업**: 태스크 완료 후 추가작업이 필요하면 하네스 §3 "추가작업 프로세스"를 따른다.

---

## STATE.md 도메인 치환값

| 필드 | 값 |
|------|------|
| 모드 | Project Task |
| 단계 목록 | TASK / PLAN / EXECUTE / CLOSE |

**진행 현황 행 예시** (STATE.md 초기 생성 시 이 구조로 작성):

```markdown
| # | 단계 | 항목 | 상태 | 시점 |
|---|------|------|------|------|
| 1 | TASK | 작업 | ⬜ | - |
| 2 | TASK | TASK.md 생성 | ⬜ | - |
| 3 | TASK | 사용자 확인 | ⬜ | - |
| 4 | PLAN | 작업 | ⬜ | - |
| 5 | PLAN | PLAN.md 생성 | ⬜ | - |
| 6 | PLAN | QA Gate | ⬜ | - |
| 7 | PLAN | QA-PLAN.md 생성 | ⬜ | - |
| 8 | PLAN | State Gate | ⬜ | - |
| 9 | PLAN | PM Gate | ⬜ | - |
| 10 | PLAN | State Gate | ⬜ | - |
| 11 | PLAN | 사용자 확인 | ⬜ | - |
| 12 | EXECUTE | 작업 | ⬜ | - |
| 13 | EXECUTE | QA Gate | ⬜ | - |
| 14 | EXECUTE | QA-EXECUTE.md 생성 | ⬜ | - |
| 15 | EXECUTE | State Gate | ⬜ | - |
| 16 | EXECUTE | PM Gate | ⬜ | - |
| 17 | EXECUTE | State Gate | ⬜ | - |
| 18 | EXECUTE | 사용자 확인 | ⬜ | - |
| 19 | CLOSE   | DONE.md 생성 | ⬜ | - |
| 20 | CLOSE   | State Gate | ⬜ | - |
```

---

## PM Gate 점검 목록

| Phase | 산출물 | 체크리스트 위치 |
|-------|-------|----------------|
| PLAN | TASK.md, PLAN.md, QA-PLAN.md | TASK.md 요구사항, PLAN.md §3, §4 |
| EXECUTE | QA-EXECUTE.md | PLAN.md §3 |

---

## Agentic Mode

opal-harness-agentic.md 참조. `--agentic` 플래그 활성화 시 이 스킬의 차이점만 기술한다.

### 활성화

`//opp --agentic {작업 설명}` 형식으로 호출. STATE.md 모드 필드를 `agentic`으로 기록한다.

### 자율 게이트 흐름

```
TASK (PM 직접) → PLAN Gate → EXECUTE Gate → CLOSE
                  PM 자율 검토   PM 자율 검토   (사용자 승인 후 자동 진행)
```

- TASK 이후 2개 게이트를 PM이 자율 통과 (CLOSE 진입은 사용자 승인 필수)
- 각 게이트에서 opal-harness-agentic.md "Gate 루핑 규칙" 적용
- AGENTIC-LOG.md에 모든 판단/오류/수정/의사결정 기록

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-03-29 | 초기 작성 — opal-pilot-dev-short 기반 범용화 (TEST-SCENARIO 제거, op-task-plan/op-task-execute 사용) |
| v1.1 | 2026-03-29 | op-plan → op-task-plan, op-execute → op-task-execute 리네이밍 반영. EXECUTE 완료 후 PM Gate 추가 |
| v1.2 | 2026-03-29 | model override를 레벨 기반으로 전환 (044) |
| v1.3 | 2026-03-30 | opal-project-pilot → opal-pilot-project 리네이밍 + 정체성 정비 (052) |
| v1.4 | 2026-03-31 | Agentic Mode 섹션 추가 (057) |
| v1.5 | 2026-03-31 | §7 참조 → opal-harness-agentic.md 참조 전환. EXECUTE 후 QA Gate + QA 체크리스트 갱신 추가 (058) |
| v1.6 | 2026-04-01 | PLAN/EXECUTE 워커 디스패치 서술에 `[WORKER]` 마커 + PM 컨텍스트 주입 지침 추가 (063) |
| v1.7 | 2026-04-02 | PLAN PM Gate에 TASK.md 체크박스 갱신 명시 (072) |
| v1.8 | 2026-04-05 | QA Gate에 체크리스트 갱신 포함 + PM Gate에 갱신 상태 확인 + QA 재소환 절차 추가 (085) |
| v1.9 | 2026-04-05 | EXECUTE 후 추가작업 참조 가이드 추가 — 하네스 §3 추가작업 프로세스 (087) |
| v2.0 | 2026-04-07 | TASK/PLAN/EXECUTE 각 단계 Gate 순서에 State Gate 추가 (094) |
| v2.1 | 2026-04-07 | State Gate를 PM Gate 전 1개 → 각 Gate 직후로 재배치 (097) |
| v2.2 | 2026-04-09 | STATE.md 도메인 치환값 — 진행 현황 행 예시에 산출물 생성 행 추가 (101) |
| v2.3 | 2026-04-10 | Artifact Gate 제거 + PM Gate 점검 목록 섹션 추가 + 파이프라인 현황판 이름 변경 (106) |
| v2.4 | 2026-04-11 | PM Gate 점검 목록 — PLAN-equivalent Phase에 TASK.md 요구사항 추가 (108) |
| v2.5 | 2026-04-15 | STEP 4 CLOSE 단계 신설 + 진행 현황 행 예시 CLOSE 2행 구조 반영 + 보고 형식 C안 적용 (121) |
| v2.6 | 2026-04-24 | citation-rules 트리거 1줄 주입 — SSOT + Trigger 패턴 (130) |
