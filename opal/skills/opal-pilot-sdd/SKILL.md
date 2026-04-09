---
name: opal-pilot-sdd
description: |
  **SDD(Spec-Driven Development) 오케스트레이터**. 명세 기반 개발을 5단계 파이프라인으로 수행한다.
  기능 단위로 SPEC.md(SSOT) 작성 → PM 직접 검증 + TEST-SCENARIOS.md 작성 → 아키텍처 설계 + ACT 분해 → 반복 실행 → 완료.
  반드시 이 스킬을 사용해야 하는 상황: "opal-pilot-sdd", "opsdd".
  단일 태스크 개발은 opds/opd를, 범용 작업은 opp를 사용한다.
triggers:
  - "opal-pilot-sdd"
  - "opsdd"
  - "SDD 개발"
  - "명세 기반 개발"
version: 2.0.0
---

# opal-pilot-sdd (SDD 오케스트레이터)

명세(SPEC.md)를 SSOT로 삼아 검증 → 설계 → ACT 분해 → 반복 실행까지 5단계 파이프라인으로 관리한다.
EXECUTE-LOOP에서 `opal-sdd-action-agent`에 단일 디스패치하며, PM이 전체를 조율한다.

## Harness

모드: SDD Task (TASK → SPEC → REVIEW → DESIGN → EXECUTE-LOOP → DONE)
> 부트스트랩에서 로드되지 않은 경우: `~/.opal/references/opal-harness.md`를 Read한다.

**[MUST]** 스킬 시작 즉시 모드에 따라 서브 하네스를 Read한다. 이 단계를 건너뛰면 안 된다:
- `--agentic` 플래그 있음 → `~/.opal/references/opal-harness-agentic.md`를 Read한다
- `--agentic` 없음 (기본) → `~/.opal/references/opal-harness-interactive.md`를 Read한다

---

## 5단계 파이프라인 요약

```
WHAT 단계
─────────────────────────────────────────────────────────
Phase 0: TASK      PM 직접    TASK.md 생성 (메타데이터)
Phase 1: SPEC      워커       op-sdd-spec → SPEC.md
                              PM Gate → 사용자 Gate
Phase 2: REVIEW    PM 직접    구조 검증 (S-1~S-6) → TEST-SCENARIOS.md 작성
                              → FR↔TS 커버리지 확인 → 사용자 Gate
── WHAT 완료 / 기준 확정 ──────────────────────────────────
HOW 단계
─────────────────────────────────────────────────────────
Phase 3: DESIGN    워커       op-sdd-plan → SPEC-PLAN.md (아키텍처 + ACT 분해)
                              PM Gate → 사용자 Gate
Phase 4: EXECUTE   ACT 루프   사용자 Gate → opal-sdd-action-agent 디스패치
                              → 결과 수신 → DONE.md
Phase 5: DONE      PM 직접    전체 ACT DONE + 전체 TS Green 확인
                              → 사용자 Gate
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

모든 산출물을 `tasks/{NNN}-{feature}/` 단일 루트에 통합한다.

```
tasks/{NNN}-{feature}/
├── TASK.md                  # Phase 0 — 메타데이터
├── SPEC.md                  # Phase 1 — 기능 명세 SSOT (FR/NFR/제약조건)
├── TEST-SCENARIOS.md        # Phase 2 — SPEC 기반 테스트 기준 + ACT별 TS 매핑
├── SPEC-PLAN.md             # Phase 3 — 아키텍처 설계 + ACT 분해 + 병렬/순서 의존관계
├── STATE.md                 # 전체 진행 상태 (Phase + ACT 목록 상태 통합 관리)
├── DONE.md                  # Phase 5 — 최종 완료 확인
└── actions/
    ├── ACT-001-{name}/
    │   ├── PLAN.md          # op-dev-plan 산출물
    │   ├── TEST.md          # op-dev-execute 산출물 (TS 실행 결과)
    │   └── DONE.md          # PM 작성 (ACT 완료 확인)
    └── ACT-002-{name}/
        └── ...
```

**순번 채번**: tasks/ 내 기존 최대 번호 + 1 (`{NNN}` 3자리 0-패딩).

---

## Phase 0: TASK

harness "4. TASK 공통 프로세스" 참조. 다음 단계명: SPEC.

**TASK.md 추가 필드**:
- `feature: {기능명}` — 간결한 기능 식별자 (kebab-case)

**base_path 설정**: `tasks/{NNN}-{feature}/` 를 TASK 공통 프로세스의 base_path로 지정한다.
하네스 §4 저장 경로 규칙에 따라 이 경로에 TASK.md + STATE.md가 생성된다.

---

## Phase 1: SPEC

워커를 디스패치하여 SPEC.md를 작성한다.

**디스패치 프롬프트**:
```
[WORKER] op-sdd-spec 스킬을 수행하라.
**스킬 경로**: {op-sdd-spec/SKILL.md 탐색 경로}
**태스크 폴더**: tasks/{NNN}-{feature}/
**프로젝트 컨텍스트**: {docs/PROJECT.md + 매칭 참조 문서}
**하네스 Guards**: 구현 금지. SPEC.md 외 파일 생성 금지.
**참조 문서**: {관련 문서 경로}
```
**에이전트**: opal-task-agent | **model**: advanced

**Gate**:
  → **State Gate** (하네스 §3 참조 — STATE.md 갱신 확인)
  → **PM Gate** → 사용자 Gate (QA Gate 없음 — 다음 Phase에서 PM이 직접 검증)

> SPEC.md 상세 구조: `references/spec-guide.md` 참조

---

## Phase 2: REVIEW

PM이 직접 SPEC.md를 검증하고 TEST-SCENARIOS.md를 작성한다. **워커 디스패치 없음.**

**REVIEW 흐름**:

```
1. 구조 검증 (PM 직접, 빠르게)
   verify-guide.md 참조 — S-1~S-6 항목 체크

2. TEST-SCENARIOS.md 작성 (PM 직접)
   SPEC.md의 각 FR → AC → TS 도출
   이 과정에서 의미적/도메인 검증(M-1~M-6, D-1~D-2) 자연스럽게 수행

3. FR↔TS 커버리지 확인 (PM 직접)
   커버 안 된 FR → SPEC.md 보완 또는 TS 추가
```

**산출물**: `tasks/{NNN}-{feature}/TEST-SCENARIOS.md`

**REVIEW Fail 처리**: 구조 검증 Fail 또는 커버리지 갭 해소 불가 → Phase 1(SPEC)을 재실행한다.

**Gate**: 사용자 Gate

> REVIEW 상세: `references/verify-guide.md` 참조

---

## Phase 3: DESIGN

워커를 디스패치하여 SPEC-PLAN.md(아키텍처 설계 + ACT 분해)를 작성한다.

**디스패치 프롬프트**:
```
[WORKER] op-sdd-plan 스킬을 수행하라.
**스킬 경로**: {op-sdd-plan/SKILL.md 탐색 경로}
**태스크 폴더**: tasks/{NNN}-{feature}/
**이전 산출물**: {SPEC.md 경로}, {TEST-SCENARIOS.md 경로}
**REVIEW 검증 메모**: {구조 검증 Warning 등 REVIEW 결과 요약}
**프로젝트 컨텍스트**: {docs/PROJECT.md + 매칭 참조 문서}
**하네스 Guards**: 구현 금지. SPEC-PLAN.md 외 파일 생성 금지.
**참조 문서**: {관련 문서 경로}
```
**에이전트**: opal-task-agent | **model**: advanced

**Gate**:
  → **State Gate** (하네스 §3 참조 — STATE.md 갱신 확인)
  → **PM Gate** → 사용자 Gate (QA Gate 없음 — 설계 + ACT 분해는 PM 판단)

> SPEC-PLAN.md 상세 구조: `references/spec-plan-guide.md` 참조

---

## Phase 4: EXECUTE-LOOP

SPEC-PLAN.md의 의존 순서대로 ACT를 반복 실행한다. 각 ACT는 `opal-sdd-action-agent`에 단일 디스패치하여 자율 완주한다.

### ACT 실행 순서

1. **사용자 Gate**: ACT 시작 전 승인 (interactive 모드)
2. **opal-sdd-action-agent 디스패치**: ACT 폴더 생성 + PLAN + EXECUTE + VERIFY 루프 자율 완주
3. **결과 수신**: status 확인
4. **Pass/Fail 판정**: Pass → DONE.md 작성 | Fail → 재시도 루프
5. **STATE.md 갱신**: ACT 상태 + TS 상태 갱신

### 재시도 루프

`status: failed` 반환 시 오류 컨텍스트를 주입하여 opal-sdd-action-agent를 재디스패치한다.
하네스 §1 자동 루핑 제약 준수 (unit/integration 최대 3회).

### 병렬 실행

의존관계 없는 ACT는 worktree 격리 + 병렬 디스패치:
- worktree 경로: `.worktrees/{NNN}-ACT-{NNN}/`
- 결과 수집 → 순차 머지 → 통합 테스트 → worktree 정리

### 상태 갱신

ACT 완료마다 STATE.md 갱신 (하네스 §3 State Gate 기준 적용):
- ACT 상태: ⬜ 대기 → 🔄 진행 중 → ✅/❌
- TS 상태: Red → Green/Fail

**State Gate**: ACT 완료 후 STATE.md 갱신 → **State Gate** (하네스 §3 참조 — STATE.md 갱신 확인) → PM Gate 진입

### Gate

- **interactive**: 각 ACT 시작 전 사용자 Gate (opal-sdd-action-agent 디스패치 승인) + 완료마다 사용자 Gate
- **agentic**: PM이 ACT 간 Gate를 자율 통과

> EXECUTE-LOOP 상세: `references/execute-loop-guide.md` 참조

---

## Phase 5: DONE

모든 ACT 완료 후 최종 검증을 수행한다.

1. 전체 TS Green 확인 (TEST-SCENARIOS.md)
2. 전체 ACT DONE.md 존재 확인
3. PM Gate → 사용자 Gate
4. DONE.md 생성

---

## STATE.md 도메인 치환값

| 필드 | 값 |
|------|------|
| 모드 | SDD Task |
| 단계 목록 | TASK / SPEC / REVIEW / DESIGN / EXECUTE-LOOP / DONE |
| 산출물 목록 | TASK.md, SPEC.md, TEST-SCENARIOS.md, SPEC-PLAN.md, actions/ACT-{N}/, DONE.md |
| 태스크 경로 | tasks/{NNN}-{feature}/ |

### STATE.md 구조

```markdown
# STATE: {기능명} SDD 개발

> 최종 갱신: YYYY-MM-DD HH:mm

## 현재 상태
- 모드: SDD Task
- Phase: {현재 Phase}
- 상태: {진행 중 / 대기 중 / 블로커 / 완료}

## 완료 산출물

> 공통 하네스 §2 "단계별 주요 산출물 표준 파일명" + "QA 산출물 표준 파일명" 참조.
> opsdd는 Phase 기반 독자 구조이므로 진행 현황 행 대신 이 테이블로 산출물을 추적한다.

| 산출물 | 상태 |
|--------|------|
| TASK.md | {⬜ / ✅} |
| SPEC.md | {⬜ / ✅} |
| TEST-SCENARIOS.md | {⬜ / ✅} |
| SPEC-PLAN.md | {⬜ / ✅} |
| EXECUTE-LOOP | {⬜ / ACT-{N}/{M}} |
| DONE.md | {⬜ / ✅} |

## EXECUTE-LOOP 현황

### ACT 목록
| ACT | 이름 | 그룹 | 상태 | 완료일 |
|-----|------|------|------|--------|

### TS 상태
| TS ID | 담당 ACT | 상태 |
|-------|---------|------|

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
  → SPEC Gate        -- PM 자율 검토
  → REVIEW           -- PM 직접 수행 (구조검증 + TS작성 + 커버리지)
  → DESIGN Gate      -- PM 자율 검토
  → EXECUTE-LOOP     -- PM 자율 관리 (ACT별 Gate 포함)
  → DONE             -- PM 자율 완료 + 최종 보고
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
- ACT 간 의존관계 순환이 감지된 경우
- SPEC.md 갱신이 Goals/Non-goals 변경을 수반하는 경우 (스코프 변경)

### AGENTIC-LOG.md 카테고리

| 카테고리 | 기록 내용 |
|----------|----------|
| GATE | Phase Gate + ACT 간 Gate 판단 |
| ERROR | 검증 실패, 회귀 감지 |
| FIX | 워커 재지시 |
| DECISION | ACT 순서/병렬 그룹핑 결정 |
| IMPROVE | SPEC.md 갱신 반영 |
| ESCALATION | 사용자 에스컬레이션 |

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-04-05 | 초기 작성 — 7단계 SDD 파이프라인 오케스트레이터 (080) |
| v2.0 | 2026-04-07 | 7→5단계 파이프라인 재작성. tasks/ 단일 루트 통합. EXECUTE-LOOP를 op-dev-plan+op-dev-execute 직접 디스패치로 전환. SPEC-VERIFY/TASKS-VERIFY 제거 → REVIEW Phase PM 직접 검증으로 통합. op-sdd-tasks 삭제 → op-sdd-plan 통합. ACT 구조 도입 (093) |
| v2.1 | 2026-04-07 | Phase 1 SPEC, Phase 3 DESIGN Gate에 State Gate 참조 추가. Phase 4 EXECUTE-LOOP STATE.md 갱신에 State Gate 기준 명시 (094) |
| v2.2 | 2026-04-07 | Phase 4 ACT 실행 구조 변경 — op-dev-plan+op-dev-execute 이중 디스패치 → opal-sdd-action-agent 단일 디스패치. 사용자 Gate 명시 (095) |
| v2.3 | 2026-04-07 | QA Gate 없는 Phase(SPEC/DESIGN/EXECUTE-LOOP)는 State Gate 단독 구조 유지 확인. 하네스 §3 진행 현황 테이블 적용 (097) |
| v2.4 | 2026-04-09 | STATE.md 완료 산출물 섹션에 공통 하네스 §2 참조 문구 추가 (101) |
