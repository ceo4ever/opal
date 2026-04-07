---
name: opal-pilot-sdd
description: |
  **SDD(Spec-Driven Development) 오케스트레이터**. 명세 기반 개발을 7단계 파이프라인으로 수행한다.
  기능 단위로 SPEC.md(SSOT) 작성 → 검증 → 설계 → 태스크 분해 → 검증 → 반복 실행 → 완료.
  반드시 이 스킬을 사용해야 하는 상황: "opal-pilot-sdd", "opsdd".
  단일 태스크 개발은 opds/opd를, 범용 작업은 opp를 사용한다.
triggers:
  - "opal-pilot-sdd"
  - "opsdd"
  - "SDD 개발"
  - "명세 기반 개발"
version: 1.0.0
---

# opal-pilot-sdd (SDD 오케스트레이터)

명세(SPEC.md)를 SSOT로 삼아 검증 → 설계 → 태스크 분해 → 반복 실행까지 7단계 파이프라인으로 관리한다.
EXECUTE-LOOP에서 기존 opal-pilot(opds/opd/opp)을 재활용하며, PM이 전체를 조율한다.

## Harness

모드: SDD Task (TASK → SPEC → SPEC-VERIFY → SPEC-PLAN → TASKS → TASKS-VERIFY → EXECUTE-LOOP → DONE)
> 부트스트랩에서 로드되지 않은 경우: `~/.opal/references/opal-harness.md`를 Read한다.

**[MUST]** 스킬 시작 즉시 모드에 따라 서브 하네스를 Read한다. 이 단계를 건너뛰면 안 된다:
- `--agentic` 플래그 있음 → `~/.opal/references/opal-harness-agentic.md`를 Read한다
- `--agentic` 없음 (기본) → `~/.opal/references/opal-harness-interactive.md`를 Read한다

---

## 7단계 파이프라인 요약

```
TASK (하네스 §4 -- PM 직접)
  → Phase 1: SPEC ──────── SPEC.md 작성 (WHAT/WHY)
  → Phase 2: SPEC-VERIFY ── 3계층 검증 + TEST-SCENARIOS.md 도출
  → Phase 3: SPEC-PLAN ──── 아키텍처/설계 수립 (HOW)
  → Phase 4: TASKS ──────── 태스크 분해 + TASKS.md (추적 매트릭스)
  → Phase 5: TASKS-VERIFY ── 커버리지/의존관계 검증
  → Phase 6: EXECUTE-LOOP ── 태스크별 반복 실행 (기존 opds/opd/opp 재활용)
  → Phase 7: DONE ────────── 최종 검증 + DONE.md
```

---

## 사전 조건 체크

`//opsdd` 호출 시 프로젝트 루트의 `docs/PROJECT.md` 존재 여부를 확인한다.

| 조건 | 동작 |
|------|------|
| `docs/PROJECT.md` 존재 | TASK 단계 시작 |
| `docs/PROJECT.md` 미존재 | opi 자동 실행 → 완료 후 opsdd 복귀 |

---

## 폴더 구조

두 세계(SDD + OPAL)를 분리하고 TASK.md의 `spec_path`로 브릿지한다.

```
specs/{NNN}-{feature}/            ← SDD 세계
├── SPEC.md                       # Phase 1
├── VERIFY.md                     # Phase 2, 5 (누적 저널)
├── tests/TEST-SCENARIOS.md       # Phase 2
├── SPEC-PLAN.md                  # Phase 3
├── TASKS.md                      # Phase 4 (추적 매트릭스 + 상태)
└── tasks/T{N}-{name}/            # Phase 6 (태스크별 실행)

tasks/{NNN}-opsdd-{feature}/      ← OPAL 세계
├── TASK.md (spec_path 필드 포함)
├── STATE.md
├── AGENTIC-LOG.md (agentic 시)
└── DONE.md
```

**순번 채번**: specs/ 내 기존 최대 번호 + 1 (`{NNN}` 3자리 0-패딩).

---

## Phase 0: TASK

harness "4. TASK 공통 프로세스" 참조. 다음 단계명: SPEC.

**TASK.md 추가 필드**:
- `spec_path: specs/{NNN}-{feature}/` -- SDD 세계 경로
- `feature: {기능명}` -- 간결한 기능 식별자

TASK.md 작성 후 specs/{NNN}-{feature}/ 디렉토리를 생성한다.

---

## Phase 1: SPEC

워커를 디스패치하여 SPEC.md를 작성한다.

**디스패치 프롬프트**:
```
[WORKER] op-sdd-spec 스킬을 수행하라.
**스킬 경로**: {op-sdd-spec/SKILL.md 탐색 경로}
**태스크 폴더**: {tasks/{NNN}-opsdd-{feature}/}
**spec_path**: {specs/{NNN}-{feature}/}
**프로젝트 컨텍스트**: {docs/PROJECT.md + 매칭 참조 문서}
**하네스 Guards**: 구현 금지. SPEC.md 외 파일 생성 금지.
**참조 문서**: {관련 문서 경로}
```
**에이전트**: opal-task-agent | **model**: advanced

**Gate**: PM Gate → 사용자 Gate (QA Gate 없음 -- 다음 Phase가 전문 검증)

> SPEC.md 상세 구조: `references/spec-guide.md` 참조

---

## Phase 2: SPEC-VERIFY

워커를 디스패치하여 SPEC.md 3계층 검증 + TEST-SCENARIOS.md를 도출한다.

**디스패치 프롬프트**:
```
[WORKER] op-sdd-verify 스킬을 수행하라.
**스킬 경로**: {op-sdd-verify/SKILL.md 탐색 경로}
**mode**: spec
**태스크 폴더**: {tasks/{NNN}-opsdd-{feature}/}
**spec_path**: {specs/{NNN}-{feature}/}
**이전 산출물**: {SPEC.md 경로}
**프로젝트 컨텍스트**: {docs/PROJECT.md + 매칭 참조 문서}
**하네스 Guards**: SPEC.md 직접 수정 금지. 판정과 피드백만 제공.
**참조 문서**: {관련 문서 경로}
```
**에이전트**: opal-task-agent | **model**: advanced

**Gate**: QA Gate (op-task-qa, opal-task-qa-agent) → PM Gate → 사용자 Gate

검증 수행자(op-sdd-verify) ≠ 검증 리뷰어(opal-task-qa-agent) 원칙 적용.

**산출물**: VERIFY.md (SPEC 검증 섹션), TEST-SCENARIOS.md

> 검증 상세: `references/verify-guide.md` 참조

### SPEC-VERIFY Fail 처리

Fail 시 피드백을 기반으로 Phase 1(SPEC)을 재실행한다. SPEC.md 갱신 후 재검증.

---

## Phase 3: SPEC-PLAN

워커를 디스패치하여 SPEC-PLAN.md(아키텍처/설계)를 작성한다.

**디스패치 프롬프트**:
```
[WORKER] op-sdd-plan 스킬을 수행하라.
**스킬 경로**: {op-sdd-plan/SKILL.md 탐색 경로}
**태스크 폴더**: {tasks/{NNN}-opsdd-{feature}/}
**spec_path**: {specs/{NNN}-{feature}/}
**이전 산출물**: {SPEC.md 경로}, {TEST-SCENARIOS.md 경로}
**프로젝트 컨텍스트**: {docs/PROJECT.md + 매칭 참조 문서}
**하네스 Guards**: 구현 금지. SPEC-PLAN.md 외 파일 생성 금지.
**참조 문서**: {관련 문서 경로}
```
**에이전트**: opal-task-agent | **model**: advanced

**Gate**: PM Gate → 사용자 Gate (QA Gate 없음 -- 설계 결정은 PM 판단, TASKS-VERIFY에서 간접 검증)

> SPEC-PLAN.md 상세 구조: `references/spec-plan-guide.md` 참조

---

## Phase 4: TASKS

워커를 디스패치하여 TASKS.md(태스크 분해 + 추적 매트릭스)를 작성한다.

**디스패치 프롬프트**:
```
[WORKER] op-sdd-tasks 스킬을 수행하라.
**스킬 경로**: {op-sdd-tasks/SKILL.md 탐색 경로}
**태스크 폴더**: {tasks/{NNN}-opsdd-{feature}/}
**spec_path**: {specs/{NNN}-{feature}/}
**이전 산출물**: {SPEC.md 경로}, {SPEC-PLAN.md 경로}, {TEST-SCENARIOS.md 경로}
**프로젝트 컨텍스트**: {docs/PROJECT.md + 매칭 참조 문서}
**하네스 Guards**: 구현 금지. TASKS.md 외 파일 생성 금지.
**참조 문서**: {관련 문서 경로}
```
**에이전트**: opal-task-agent | **model**: advanced

**Gate**: PM Gate → 사용자 Gate (QA Gate 없음 -- 다음 Phase가 전문 검증)

---

## Phase 5: TASKS-VERIFY

워커를 디스패치하여 TASKS.md의 커버리지/의존관계를 검증한다.

**디스패치 프롬프트**:
```
[WORKER] op-sdd-verify 스킬을 수행하라.
**스킬 경로**: {op-sdd-verify/SKILL.md 탐색 경로}
**mode**: tasks
**태스크 폴더**: {tasks/{NNN}-opsdd-{feature}/}
**spec_path**: {specs/{NNN}-{feature}/}
**이전 산출물**: {SPEC.md}, {SPEC-PLAN.md}, {TASKS.md}, {TEST-SCENARIOS.md}
**프로젝트 컨텍스트**: {docs/PROJECT.md + 매칭 참조 문서}
**하네스 Guards**: TASKS.md 직접 수정 금지. 판정과 피드백만 제공.
**참조 문서**: {관련 문서 경로}
```
**에이전트**: opal-task-agent | **model**: standard

**Gate**: QA Gate (op-task-qa, opal-task-qa-agent) → PM Gate → 사용자 Gate

**산출물**: VERIFY.md (TASKS 검증 섹션 추가 -- 누적)

> 검증 상세: `references/verify-guide.md` 참조

### TASKS-VERIFY Fail 처리

Fail 시 피드백을 기반으로 Phase 4(TASKS)를 재실행한다. TASKS.md 갱신 후 재검증.

---

## Phase 6: EXECUTE-LOOP

TASKS.md의 의존 순서대로 태스크를 반복 실행한다. 각 태스크는 기존 opal-pilot 오케스트레이터에 위임한다.

### 스킬 결정 기준

| TASKS.md 예상 규모 | 위임 스킬 |
|-------------------|----------|
| Small / Standard | opds (3단계) |
| Large | opd (4단계) |
| 비코드 | opp (3단계) |

### 디스패치 시 SDD 컨텍스트 주입

기존 오케스트레이터 디스패치에 다음을 추가 주입한다:
- SPEC.md 경로 + 해당 태스크의 AC 매핑
- SPEC-PLAN.md 경로 (설계 참조)
- TEST-SCENARIOS.md의 해당 TS 목록
- "테스트 먼저 작성 후 구현" TDD 지시
- task_folder: `specs/{NNN}-{feature}/tasks/T{N}-{name}/`

### 병렬 실행

의존관계 없는 태스크는 worktree 격리 + 병렬 디스패치:
- worktree 경로: `.worktrees/{spec-NNN}-T{N}/`
- 결과 수집 → 순차 머지 → 통합 테스트 → worktree 정리

### 상태 갱신

태스크 완료마다 갱신:
- TASKS.md: 해당 태스크 상태 (⬜→🔄→✅/❌)
- TEST-SCENARIOS.md: 해당 TS 결과
- STATE.md: 진행 현황 (T{N}/{M})

### Gate

- **interactive**: 각 태스크 시작/완료마다 사용자 Gate
- **agentic**: PM이 태스크 간 Gate를 자율 통과

> EXECUTE-LOOP 상세: `references/execute-loop-guide.md` 참조

---

## Phase 7: DONE

모든 태스크 완료 후 최종 검증을 수행한다.

1. 전체 TS Green 확인 (TEST-SCENARIOS.md)
2. VERIFY.md에 DONE 검증 섹션 추가
3. QA Gate (op-dev-qa, opal-task-qa-agent)
4. PM Gate → 사용자 Gate
5. DONE.md 생성

---

## STATE.md 도메인 치환값

| 필드 | 값 |
|------|------|
| 모드 | SDD Task |
| 단계 목록 | TASK / SPEC / SPEC-VERIFY / SPEC-PLAN / TASKS / TASKS-VERIFY / EXECUTE-LOOP / DONE |
| 산출물 목록 | TASK.md, SPEC.md, VERIFY.md(SPEC), TEST-SCENARIOS.md, SPEC-PLAN.md, TASKS.md, VERIFY.md(TASKS), EXECUTE-LOOP(T{N}/{M}), DONE.md |
| SDD 경로 | spec_path: specs/{NNN}-{feature}/, task_path: tasks/{NNN}-opsdd-{feature}/ |

### STATE.md 구조

```markdown
# STATE: {기능명} SDD 개발

> 최종 갱신: YYYY-MM-DD HH:mm

## 현재 상태
- 모드: SDD Task
- Phase: {현재 Phase}
- 진행: {T{N}/{M} (EXECUTE-LOOP 시)}
- 상태: {진행 중 / 대기 중 / 블로커 / 완료}

## 완료 산출물
| 산출물 | 상태 |
|--------|------|
| TASK.md | {⬜ / ✅} |
| SPEC.md | {⬜ / ✅} |
| VERIFY.md (SPEC) | {⬜ / ✅} |
| TEST-SCENARIOS.md | {⬜ / ✅} |
| SPEC-PLAN.md | {⬜ / ✅} |
| TASKS.md | {⬜ / ✅} |
| VERIFY.md (TASKS) | {⬜ / ✅} |
| EXECUTE-LOOP | {⬜ / T{N}/{M}} |
| DONE.md | {⬜ / ✅} |

## SDD 경로
- spec_path: specs/{NNN}-{feature}/
- task_path: tasks/{NNN}-opsdd-{feature}/

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|

## 블로커
없음

## 다음 액션
{다음으로 수행할 작업}
```

---

## Agentic Mode

opal-harness-agentic.md 참조. `--agentic` 플래그 활성화 시 이 스킬의 차이점만 기술한다.

### 활성화

`//opsdd --agentic {기능 설명}` 형식으로 호출. STATE.md 모드 필드를 `agentic`으로 기록한다.

### 자율 게이트 흐름

```
TASK (PM 직접)
  → SPEC Gate         -- PM 자율 검토
  → SPEC-VERIFY Gate  -- PM 자율 검토
  → SPEC-PLAN Gate    -- PM 자율 검토
  → TASKS Gate        -- PM 자율 검토
  → TASKS-VERIFY Gate -- PM 자율 검토
  → EXECUTE-LOOP      -- PM 자율 관리 (태스크별 Gate 포함)
  → DONE              -- PM 자율 완료 + 최종 보고
```

- 모든 Phase Gate를 PM이 자율 통과
- EXECUTE-LOOP 진입 = PM이 대행 승인 (구현 금지 원칙의 "실행 허가"를 PM이 판단)
- AGENTIC-LOG.md에 모든 판단/오류/수정/의사결정 기록

### Gate 루핑

opal-harness-agentic.md §5 적용:
- Gate Fail → 재지시 (3회 이내)
- 3회 초과 → 심각도 판별 (Critical → 사용자 에스컬레이션, Normal → 계속 진행)

### opsdd 고유 에스컬레이션 조건

opal-harness-agentic.md §6 공통 기준에 추가:
- SPEC.md의 Open Questions가 해소되지 않는 경우
- AC 커버리지 갭이 발생하고 자동 해소 불가한 경우
- 태스크 간 의존관계 순환이 감지된 경우
- SPEC.md 갱신이 Goals/Non-goals 변경을 수반하는 경우 (스코프 변경)

### AGENTIC-LOG.md 카테고리

| 카테고리 | 기록 내용 |
|----------|----------|
| GATE | Phase Gate + 태스크 간 Gate 판단 |
| ERROR | 검증 실패, 회귀 감지 |
| FIX | 워커 재지시 |
| DECISION | 스킬 선택(opds/opd), 병렬 그룹핑 |
| IMPROVE | SPEC.md 갱신 반영 |
| ESCALATION | 사용자 에스컬레이션 |

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-04-05 | 초기 작성 -- 7단계 SDD 파이프라인 오케스트레이터 (080) |
