# PLAN: opal-pilot-sdd (opsdd) 오케스트레이터 스킬 설계

> 작성일: 2026-04-05
> 입력: TASK.md (v2, 2026-04-05)
> 출력: PLAN.md

## 1. 현황 조사

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `~/.opal/skills/opal-pilot-dev/SKILL.md` | opd 오케스트레이터 — EXECUTE-LOOP에서 재활용 대상 | 없음 (참조만) |
| `~/.opal/skills/opal-pilot-dev-short/SKILL.md` | opds 오케스트레이터 — EXECUTE-LOOP에서 재활용 대상 | 없음 (참조만) |
| `~/.opal/skills/opal-pilot-project/SKILL.md` | opp 오케스트레이터 — EXECUTE-LOOP에서 재활용 대상 | 없음 (참조만) |
| `~/.opal/skills/opal-pilot-project-dev/SKILL.md` | oppd — agentic 패턴, 병렬 실행, 검증 루프 참조 대상 | 없음 (참조만) |
| `~/.opal/references/opal-harness.md` | 하네스 공통 규칙 | 없음 (opsdd가 준수) |
| `~/.opal/references/opal-harness-interactive.md` | interactive 모드 Gates | 없음 (opsdd가 준수) |
| `~/.opal/references/opal-harness-agentic.md` | agentic 모드 규칙 | 없음 (opsdd가 준수) |
| `~/.opal/references/agents.md` | 에이전트 레지스트리 | 수정 — 신규 에이전트 등록 |
| `~/.opal/references/skills.md` | 스킬 레지스트리 | 수정 — 신규 스킬 등록 |
| `~/.opal/references/opal-model-mapping.md` | 모델 매핑 | 없음 (기존 레벨 활용) |
| `~/.opal/agents/opal-task-action-agent/AGENT.md` | 액션 에이전트 — EXECUTE-LOOP agentic 패턴 참조 | 없음 (참조만) |
| `docs/PROJECT.md` | 프로젝트 정의 | 수정 — opsdd 관련 컴포넌트 등록 |
| `docs/ARCHITECTURE.md` | 시스템 아키텍처 | 수정 — opsdd 컴포넌트 반영 |
| `docs/CONVENTIONS.md` | 코드 컨벤션 | 수정 — opsdd 약어 등록 |
| `tasks/080-opp-opsdd-design-proposal/opsdd-제안서_v1_260405.md` | 초안 제안서 | 없음 (입력 자료) |
| `tasks/080-opp-opsdd-design-proposal/opsdd-리서치_v1_260405.md` | SDD 리서치 | 없음 (입력 자료) |

### 현재 상태

#### 기존 오케스트레이터 파이프라인 구조

| 오케스트레이터 | 파이프라인 | 특징 |
|--------------|----------|------|
| opds | TASK → PLAN+TEST-SCENARIO → EXECUTE | 3단계, 단일 태스크 경량 |
| opd | TASK → ANALYSIS → PLAN+TEST-SCENARIO → EXECUTE | 4단계, 단일 태스크 풀스펙 |
| opp | TASK → PLAN → EXECUTE | 3단계, 범용 (TEST-SCENARIO 없음) |
| oppd | (PRD/TRD via opwt) → WBS → 액션 루프 (opal-task-action-agent) | 3 Phase, 프로젝트 전체 라이프사이클 |

#### 기존 에이전트 구조

| 에이전트 | model | 역할 |
|---------|-------|------|
| opal-task-agent | standard | 범용 워커 — 단계 스킬 실행 |
| opal-task-qa-agent | light | QA 워커 — qa_skill 동적 실행 |
| op-dev-test-agent | standard | 테스트 실행 + 판정 |
| opal-task-action-agent | advanced | oppd Phase 3 액션 자율 실행 |

#### 기존 스킬의 워커 디스패치 패턴

모든 오케스트레이터가 `[WORKER]` 마커 + 하네스 Guards + 참조 문서 주입 패턴을 공유함.
oppd의 opal-task-action-agent는 6단계 자율 파이프라인(PLAN→QA→TEST-SCENARIO→EXECUTE→VERIFY→TEST)을 수행하며, 검증 루핑(L1~L3b)을 에이전트 내부에서 관리함.

#### SDD 방법론 분석 결과

- **Kiro**: Requirements → Design → Tasks 3단계, EARS 표기법
- **spec-kit**: spec → plan → tasks/ + constitution.md, 불변 원칙 별도 관리
- **cc-sdd**: specs/{feature}/ + steering/, 멀티 에이전트 지원
- **핵심 가치**: 명세=SSOT, 검증 선행, 양방향 추적성(AC↔테스트↔태스크↔코드)
- **함정 대응**: Spec Theater(기능 단위 제한), Spec/Code Drift(코드 우선 + opi), Over-specification(기능 개발 전용), Waterfall 회귀(즉시 반영 허용)

#### TASK.md 확정 설계 방향 요약

1. **C안**: TASK=진입점(행정), SPEC=실질적 SSOT
2. **두 세계 분리**: specs/(SDD 세계) + tasks/(OPAL 세계)
3. **7단계 파이프라인**: SPEC → SPEC-VERIFY → SPEC-PLAN → TASKS → TASKS-VERIFY → EXECUTE-LOOP → DONE
4. **EXECUTE-LOOP에서 기존 opal-pilot 재활용**
5. **tasks.md가 상태 관리**: 추적 매트릭스 + 의존관계 + 태스크별 상태

### 영향 범위

| 범위 | 변경 내용 |
|------|----------|
| 신규 오케스트레이터 SKILL.md | opal-pilot-sdd (opsdd) — 7단계 파이프라인 |
| 신규 단계 스킬 4개 | op-sdd-spec, op-sdd-verify, op-sdd-plan, op-sdd-tasks |
| 에이전트 레지스트리 | agents.md에 신규 에이전트 등록 (필요 시) |
| 스킬 레지스트리 | skills.md에 opsdd + 4개 단계 스킬 등록 |
| 프로젝트 문서 | PROJECT.md, ARCHITECTURE.md, CONVENTIONS.md 갱신 |
| 기존 컴포넌트 | **변경 없음** — 하네스, 기존 오케스트레이터, 기존 에이전트 모두 유지 |

---

## 2. 구현 계획

### 핵심 설계

이하에서 opsdd의 상세 설계를 기술한다. 이 설계에 따라 각 파일을 작성한다.

---

### D1. 파이프라인 전체 흐름 (R1)

```
TASK (하네스 §4 — PM 직접)
  │
  ▼
Phase 1: SPEC ──────── spec.md 작성
  │                     워커: opal-task-agent → op-sdd-spec
  │                     model: advanced
  │                     [PM Gate] → 사용자 게이트
  │
  ▼
Phase 2: SPEC-VERIFY ── 3계층 검증 + test-scenarios.md 도출
  │                     워커: opal-task-agent → op-sdd-verify (mode=spec)
  │                     model: advanced
  │                     [QA Gate] → [PM Gate] → 사용자 게이트
  │
  ▼
Phase 3: SPEC-PLAN ──── 아키텍처/설계 수립
  │                     워커: opal-task-agent → op-sdd-plan
  │                     model: advanced
  │                     [PM Gate] → 사용자 게이트
  │
  ▼
Phase 4: TASKS ──────── 태스크 분해 + tasks.md
  │                     워커: opal-task-agent → op-sdd-tasks
  │                     model: advanced
  │                     [PM Gate] → 사용자 게이트
  │
  ▼
Phase 5: TASKS-VERIFY ── 커버리지/의존관계 검증
  │                     워커: opal-task-agent → op-sdd-verify (mode=tasks)
  │                     model: standard
  │                     [QA Gate] → [PM Gate] → 사용자 게이트
  │
  ▼
Phase 6: EXECUTE-LOOP ── 태스크별 반복 실행
  │                     오케스트레이터가 루프 관리
  │                     각 태스크 → 기존 opal-pilot (opds/opd/opp) 디스패치
  │                     [태스크별 Gate] → tasks.md 상태 갱신
  │
  ▼
Phase 7: DONE ────────── 최종 검증 + DONE.md
                         전체 TS Green 확인 + 회귀 테스트
                         validate.md 최종 갱신
```

---

### D2. 에이전트 구분 (R2, R12, R13)

| Phase | 수행 주체 | 에이전트 | 단계 스킬 | model |
|-------|----------|---------|----------|-------|
| TASK | PM 직접 | - | op-task (하네스 §4) | - |
| SPEC | 워커 디스패치 | opal-task-agent | op-sdd-spec | advanced |
| SPEC-VERIFY | 워커 디스패치 | opal-task-agent | op-sdd-verify (mode=spec) | advanced |
| SPEC-PLAN | 워커 디스패치 | opal-task-agent | op-sdd-plan | advanced |
| TASKS | 워커 디스패치 | opal-task-agent | op-sdd-tasks | advanced |
| TASKS-VERIFY | 워커 디스패치 | opal-task-agent | op-sdd-verify (mode=tasks) | standard |
| EXECUTE-LOOP | 오케스트레이터 관리 | 기존 에이전트 (아래 D6 참조) | 기존 스킬 재활용 | 기존 매핑 |
| DONE | PM 직접 + QA | opal-task-qa-agent | op-dev-qa (또는 op-task-qa) | light |

**설계 결정 — 신규 에이전트 불필요**:
- 모든 SDD 단계 스킬(op-sdd-spec, op-sdd-verify, op-sdd-plan, op-sdd-tasks)은 기존 **opal-task-agent**가 수행한다.
- opal-task-agent는 범용 워커로서 전달된 SKILL.md를 Read하고 프로세스를 따르는 구조이므로, 신규 스킬만 추가하면 새 에이전트 없이 동작한다.
- 검증(SPEC-VERIFY, TASKS-VERIFY)도 opal-task-agent → op-sdd-verify 디스패치로 처리. 별도 검증 에이전트는 만들지 않는다 (TASK.md 미확정 사항 #3 결정: QA 에이전트와 별개로 opal-task-agent가 op-sdd-verify를 실행).

---

### D3. PM Gate 설계 (R3)

각 Phase 완료 후 게이트를 적용한다:

| 게이트 | 역할 | 적용 Phase |
|--------|------|-----------|
| **QA Gate** | 산출물 품질 검증 (QA 에이전트 호출) | SPEC-VERIFY, TASKS-VERIFY, EXECUTE-LOOP 내, DONE |
| **PM Gate** | 요구사항 충족 + 체크리스트 갱신 상태 확인 | 모든 Phase |
| **사용자 Gate** | 사용자 승인 (interactive) / PM 대행 (agentic) | 모든 Phase |

**QA 스킬 매핑**: Phase에 따라 QA 스킬이 달라진다.

| Phase | QA Gate | 이유 |
|-------|---------|------|
| SPEC | 없음 | 다음 단계(SPEC-VERIFY)가 전문 검증 |
| SPEC-VERIFY | op-task-qa (opal-task-qa-agent) | 검증 수행자 ≠ 검증 리뷰어 원칙 |
| SPEC-PLAN | 없음 | 설계 결정은 PM 판단 + TASKS-VERIFY에서 간접 검증 |
| TASKS | 없음 | 다음 단계(TASKS-VERIFY)가 전문 검증 |
| TASKS-VERIFY | op-task-qa (opal-task-qa-agent) | 검증 수행자 ≠ 검증 리뷰어 원칙 |
| EXECUTE-LOOP 내 각 태스크 | op-dev-qa | 코드 산출물 |
| DONE | op-dev-qa | 최종 검증 |

**원칙**: 전문 검증 단계가 바로 뒤따르면 범용 QA는 생략. 전문 검증의 결과를 별도 에이전트(opal-task-qa-agent)가 리뷰.

**PM Gate 상세** (하네스 interactive §3 참조):
1. TASK.md 요구사항 체크박스 갱신 상태 확인
2. 이전 단계 산출물과 일관성 확인
3. 미갱신 시 QA 에이전트 재소환
4. 통과 후 사용자에게 보고

---

### D4. 폴더 구조 (R5, R6)

```
project-root/
├── specs/                               ← SDD 세계 (프로젝트 레벨)
│   └── {NNN}-{feature-name}/            ← 순번 포함, kebab-case
│       ├── spec.md                      # Phase 1 산출물 — SSOT
│       ├── SPEC-PLAN.md                 # Phase 3 산출물 — 아키텍처/설계 (HOW)
│       ├── tasks.md                     # Phase 4 산출물 — 태스크 분해 + 상태 관리
│       ├── verify.md                    # Phase 2,5 산출물 — 검증 저널 (누적)
│       ├── tests/
│       │   └── test-scenarios.md        # Phase 2 산출물 — AC→테스트 시나리오 (TDD Red)
│       └── tasks/                       # Phase 6 — 태스크별 실행 공간
│           ├── T1-{name}/
│           │   ├── PLAN.md              # op-dev-plan 산출물
│           │   └── changed_files.md     # op-dev-execute 산출물
│           └── T2-{name}/
│               └── ...
│
├── tasks/                               ← OPAL 세계 (상태 관리)
│   └── {NNN}-opsdd-{feature}/
│       ├── TASK.md                      # 하네스 TASK (행정적 진입점)
│       ├── STATE.md                     # 진행 상태 추적
│       ├── AGENTIC-LOG.md              # (agentic 모드 시)
│       └── DONE.md                      # 최종 완료
│
├── src/                                 ← 실제 구현 코드
└── docs/                                ← 프로젝트 문서
```

**순번 채번**: specs/ 내 기존 최대 번호 + 1. `{NNN}` 3자리 0-패딩.

**두 세계의 브릿지**:
- TASK.md에 `spec_path: specs/{NNN}-{feature-name}/` 필드를 포함하여 SDD 세계로 연결
- tasks.md 내 각 태스크에 `task_folder: specs/{NNN}-{feature}/tasks/T{N}-{name}/` 경로를 기록
- STATE.md에서 현재 Phase와 진행 중인 태스크 ID를 추적

---

### D5. spec.md 표준 구조 (R15)

```markdown
# SPEC: {기능명}

> 버전: 1.0 | 작성일: YYYY-MM-DD | 상태: Draft → Verified → Implemented

## 1. Background (배경)
왜 이 기능이 필요한지 (비즈니스 맥락)

## 2. Goals (목표)
이 기능이 달성해야 할 것

## 3. Non-goals (비목표)
명시적으로 범위 밖인 것

## 4. User Stories (사용자 스토리)
- As a {역할}, I want {기능}, so that {가치}

## 5. Functional Requirements (기능 요구사항)
- [FR-01] {기능 요구사항}
- [FR-02] ...

## 6. Acceptance Criteria (수용 기준)
### AC-01: {시나리오명}
- **GIVEN**: {사전 조건}
- **WHEN**: {행위}
- **THEN**: {기대 결과}

### AC-02: ...

## 7. Edge Cases (엣지 케이스)
- [EC-01] {예외 상황} → {기대 동작}

## 8. Non-functional Requirements (비기능 요구사항)
- [NFR-01] {성능/보안/접근성 등}

## 9. Constraints (제약)
기술적·정책적 제약

## 10. Open Questions (미결 사항)
- 없음 ← (SPEC-VERIFY 통과 조건: "없음"이어야 함)
```

**핵심 규칙**:
- AC는 반드시 **GIVEN/WHEN/THEN** 형식 (테스트 시나리오 자동 도출의 기반)
- Open Questions가 하나라도 남아있으면 SPEC-VERIFY로 진행 불가
- 10개 필수 섹션 모두 존재해야 구조적 검증 통과
- AC 최소 3개 이상

---

### D6. EXECUTE-LOOP 설계 (R4, R10, R14)

EXECUTE-LOOP에서 기존 opal-pilot을 재활용한다. tasks.md의 의존관계 순서에 따라 태스크를 순차/병렬 실행한다.

#### 태스크별 실행 흐름 (A안: 기존 opal-pilot 오케스트레이터 중첩 호출)

```
for each task T in dependency_order(tasks.md):
  1. tasks.md의 예상 규모 → 스킬 결정
     - Small/Standard → //opds 호출
     - Large → //opd 호출
     - 비코드 → //opp 호출

  2. 해당 오케스트레이터가 자체 파이프라인 실행:
     - opds: TASK → PLAN+TEST-SCENARIO → EXECUTE → QA
     - opd: TASK → ANALYSIS → PLAN+TEST-SCENARIO → EXECUTE → QA
     - opp: TASK → PLAN → EXECUTE
     - task_folder: specs/{NNN}-{feature}/tasks/T{N}-{name}/

  3. 디스패치 시 SDD 컨텍스트 주입:
     - spec.md 경로 + 해당 태스크의 AC 매핑
     - SPEC-PLAN.md 경로 (설계 참조)
     - test-scenarios.md의 해당 TS 목록
     - "테스트 먼저 작성 후 구현" TDD 지시

  4. 오케스트레이터 완료 후:
     - tasks.md 상태 갱신
     - test-scenarios.md 상태 갱신
     - STATE.md 진행 현황 갱신
```

#### 병렬 실행 (oppd Phase 3 패턴 재활용)

의존관계 없는 태스크는 worktree 격리 + 병렬 디스패치:

```
groups = buildParallelGroups(tasks.md)  # 의존성 그래프 → 실행 그룹

for each group in groups:
  if group has single task:
    → 순차 실행 (위 흐름)
  if group has multiple independent tasks:
    → worktree 생성: .worktrees/{spec-NNN}-T{N}/
    → 병렬 워커 디스패치 (각 worktree에서 독립)
    → 결과 수집 → 순차 머지 → 통합 테스트
    → worktree 정리
```

#### 기존 스킬 재활용 매핑

| EXECUTE-LOOP 내 단계 | 재활용 대상 | 비고 |
|---------------------|-----------|------|
| PLAN | op-dev-plan (opds/opd) | 입력에 spec.md + AC/TS 정보 추가 |
| TEST-SCENARIO | op-dev-test-scenario | 기존 그대로 (Large 태스크만) |
| EXECUTE | op-dev-execute | 기존 그대로 |
| TEST | op-dev-test-agent | 기존 검증 루프 (L1~L3b) |
| QA | op-dev-qa | 기존 그대로 |

---

### D7. --agentic 모드 설계 (R11)

oppd의 agentic 패턴을 참조하여 opsdd의 --agentic 모드를 설계한다.

#### 활성화

```
//opsdd --agentic {기능 설명}
```

#### 자율 게이트 흐름

```
TASK (PM 직접)
  → SPEC Gate         ── PM 자율 검토
  → SPEC-VERIFY Gate  ── PM 자율 검토
  → SPEC-PLAN Gate    ── PM 자율 검토
  → TASKS Gate        ── PM 자율 검토
  → TASKS-VERIFY Gate ── PM 자율 검토
  → EXECUTE-LOOP      ── PM 자율 관리 (태스크별 Gate 포함)
  → DONE              ── PM 자율 완료 + 최종 보고
```

#### PM 대행 의무 (agentic 핵심)

opal-harness-agentic.md §3 적용 + opsdd 고유 강화:

| 의무 | opsdd 적용 |
|------|-----------|
| 판단 기록 의무 | 매 Phase Gate에서 Pass/Fail 근거를 AGENTIC-LOG.md에 기록 |
| 산출물 직접 검증 의무 | spec.md 내용 수준까지 직접 Read하여 검증 |
| 완수 의무 | 모든 AC의 TS가 Green이 될 때까지 루핑 |
| 폴백 승인 의무 | 태스크의 스킬 전환(opds→opd) 시 PM 승인 |

#### Gate 루핑 규칙

opal-harness-agentic.md §5 동일 적용:
```
Gate Fail → 재지시 (루핑 카운트 +1)
  → 3회 이내: 재지시 + AGENTIC-LOG 기록
  → 3회 초과: 심각도 판별
      ├─ Critical → 사용자 에스컬레이션 + STOP
      └─ Normal/Minor → AGENTIC-LOG 기록 + 계속 진행
```

#### EXECUTE-LOOP agentic 모드

EXECUTE-LOOP 내 각 태스크 실행 시:
- **interactive**: 각 태스크 시작/완료마다 사용자 게이트
- **agentic**: PM이 태스크 간 게이트를 자율 통과. 검증 루프도 자율 관리

AGENTIC-LOG.md에 기록할 카테고리:
- `GATE`: Phase 게이트 + 태스크 간 게이트 판단
- `ERROR`: 검증 실패, 회귀 감지
- `FIX`: 워커 재지시
- `DECISION`: 스킬 선택(opds/opd), 병렬 그룹핑
- `IMPROVE`: spec.md 갱신 반영
- `ESCALATION`: 사용자 에스컬레이션

#### opsdd 고유 에스컬레이션 조건

opal-harness-agentic.md §6 공통 기준에 추가:
- spec.md의 Open Questions가 해소되지 않는 경우
- AC 커버리지 갭이 발생하고 자동 해소 불가한 경우
- 태스크 간 의존관계 순환이 감지된 경우
- spec.md 갱신이 Goals/Non-goals 변경을 수반하는 경우 (스코프 변경)

---

### D8. tasks.md 상태 관리 구조 (R7)

```markdown
# Tasks: {기능명}

> spec.md v{X.Y} 기준 | 총 태스크: {N}개

## 추적 매트릭스 (Requirements Traceability Matrix)

| AC | FR | TS | 담당 태스크 | 커버리지 |
|----|----|----|-----------|----------|
| AC-01 | FR-01, FR-02 | TS-01, TS-02 | T1, T2 | ✅ |
| AC-02 | FR-03 | TS-03 | T3 | ✅ |

## 의존관계 그래프

T1 → T2 → T4
T1 → T3 → T4

## 태스크 목록

### T1: {태스크명}
- **범위**: {변경 대상}
- **AC 매핑**: AC-01, AC-02
- **TS 매핑**: TS-01, TS-02
- **의존**: 없음
- **예상 규모**: Small (→ opds)
- **완료 기준**: TS-01, TS-02 Green
- **상태**: ⬜ 대기 / 🔄 진행 중 / ✅ 완료 / ❌ 실패

### T2: ...
```

**상태 열거형**:

| 상태 | 의미 |
|------|------|
| ⬜ 대기 | 아직 시작 안 함 |
| 🔄 진행 중 | EXECUTE-LOOP에서 실행 중 |
| ✅ 완료 | 모든 TS Green |
| ❌ 실패 | 에스컬레이션 필요 |

---

### D9. verify.md 누적 저널 구조 (R17)

```markdown
# Validation Journal: {기능명}

## SPEC 검증 (Phase 2: SPEC-VERIFY)
- 수행일: YYYY-MM-DD
- 워커: opal-task-agent → op-sdd-verify (mode=spec)

### 구조적 검증
| # | 항목 | 결과 | 비고 |
|---|------|------|------|
| 1 | 필수 섹션 10개 존재 | ✅ Pass | |
| 2 | AC 형식 (GIVEN/WHEN/THEN) | ✅ Pass | 5개 AC |
| 3 | Open Questions 해소 | ✅ Pass | 0개 잔존 |
| 4 | AC 최소 3개 | ✅ Pass | |

### 의미적 검증
| # | 항목 | 결과 | 비고 |
|---|------|------|------|
| 1 | Goals ↔ FR ↔ AC 정합 | ✅ Pass | |
| 2 | Non-goals와 Goals 모순 없음 | ✅ Pass | |
| 3 | 제약 조건 실현 가능 | ✅ Pass | |
| 4 | 기존 코드/문서와 충돌 없음 | ⚠️ Warning | {비고} |

### 도메인 검증
| # | 항목 | 결과 | 비고 |
|---|------|------|------|
| 1 | 아키텍처 정합 | ✅ Pass | |
| 2 | 컨벤션 준수 | ✅ Pass | |

### 테스트 시나리오 도출
- 총 시나리오: {N}개 (unit: {n}, integration: {n}, e2e: {n})
- AC 커버리지: {n}% ({n}/{n} AC → {n} 시나리오)

### 판정: {✅ Pass / ⚠️ Pass with Warnings / ❌ Fail}

---

## TASKS 검증 (Phase 5: TASKS-VERIFY)
- 수행일: YYYY-MM-DD
- 워커: opal-task-agent → op-sdd-verify (mode=tasks)

### 검증 항목
| # | 항목 | 결과 | 비고 |
|---|------|------|------|
| 1 | AC 커버리지 (모든 AC ≥1 태스크) | | |
| 2 | TS 커버리지 (모든 TS ≥1 태스크) | | |
| 3 | 의존관계 유효성 (순환 없음) | | |
| 4 | 자기 완결성 | | |
| 5 | 크기 적정성 | | |

### 추적 매트릭스 (최종)
| AC | FR | TS | 담당 태스크 | 커버리지 |
|----|----|----|-----------|----------|

### 판정: {✅ Pass / ❌ Fail}

---

## DONE 검증 (Phase 7)
(Phase 6 완료 시 추가)
```

---

### D10. 문서 계층 관계 (R16)

```
TASK.md (진입점)
  └─→ spec.md (SSOT — 기능 명세, WHAT)
        ├─→ test-scenarios.md (AC → TS 매핑, TDD Red)
        ├─→ SPEC-PLAN.md (아키텍처 설계, HOW)
        │     └─→ tasks.md (태스크 분해 + 상태 관리, BREAKDOWN)
        │           └─→ T{N}/PLAN.md (개별 태스크 실행 계획)
        └─→ verify.md (검증 저널, 누적)
```

**읽기 순서**:
1. TASK.md → spec_path로 SDD 세계 진입
2. spec.md → 기능의 WHAT/WHY
3. test-scenarios.md → HOW TO VERIFY
4. SPEC-PLAN.md → HOW TO DESIGN (아키텍처/기술 결정)
5. tasks.md → HOW TO BUILD (순서 + 의존관계)
6. verify.md → WHAT WAS VERIFIED

---

### D11. 미확정 사항 결정 (TASK.md §6)

| # | 항목 | 결정 | 근거 |
|---|------|------|------|
| 1 | spec.md 갱신 정책 | **즉시 반영 + 변경 이력 기록** | 살아있는 문서. 구현 중 발견 사항은 spec.md에 즉시 반영하되, 변경 이력 섹션에 변경 사유/시점을 기록. Goals/Non-goals 변경 시 agentic 모드에서는 에스컬레이션 |
| 2 | 경량 모드 | **초기에는 전체 7단계만** | 경량 모드 필요 시 나중에 `--light` 플래그 추가. 지금은 복잡도를 늘리지 않음 |
| 3 | 검증 에이전트 | **기존 opal-task-agent가 op-sdd-verify 실행** | 별도 에이전트 불필요. opal-task-agent의 범용 워커 패턴으로 충분 |
| 4 | 테스트 코드 위치 | **시나리오 정의는 specs/tests/, 실제 코드는 프로젝트 tests/** | specs/에는 TDD Red 시나리오 정의, 실제 테스트 코드는 프로젝트 구조에 배치 |
| 5 | oppd 연계 시점 | **opsdd 완성 후 oppd Phase 3 액션 스킬로 등록** | 독립 실행 먼저 안정화, 이후 oppd WBS에서 "기능 개발" 액션 시 opsdd 호출 |

---

### D12. oppd와의 포지셔닝 (R18, R19)

```
oppd: 프로젝트 전체 → PRD/TRD → WBS → 액션 루프
      ├─ 단순 코드 액션 → opds
      ├─ 복잡 코드 액션 → opd
      ├─ 기능 개발 액션 → opsdd (NEW — Phase 3 액션 스킬로 등록)
      └─ 비코드 액션 → opp

opsdd: 기능 단위 → SPEC → VERIFY → SPEC-PLAN → TASKS → VERIFY → 태스크 루프
       ├─ 경량 태스크 → opds 파이프라인
       └─ 복잡 태스크 → opd 파이프라인

opd/opds: 단일 태스크 개발 (spec 없이 TASK에서 바로)
```

**사용 시점 판별**:
- "새 기능을 만들어야 하고, 무엇을 만들지 먼저 정의하고 싶다" → opsdd
- "뭘 해야 하는지 알고 있고, 바로 구현하고 싶다" → opds/opd
- "프로젝트 전체를 처음부터 끝까지" → oppd (내부에서 opsdd 호출 가능)

---

### D13. 신규 스킬 4개 개요 (R12)

#### op-sdd-spec

| 항목 | 내용 |
|------|------|
| 역할 | TASK.md + 프로젝트 컨텍스트 → spec.md 작성 |
| 입력 | TASK.md, docs/PROJECT.md, docs/ARCHITECTURE.md, 코드베이스 |
| 출력 | specs/{NNN}-{feature}/spec.md |
| 페르소나 | spec-writer (명세 작성 전문가 — 신규) |
| 핵심 프로세스 | 1. 프로젝트/코드 분석 → 2. 10섹션 spec.md 작성 → 3. AC는 GIVEN/WHEN/THEN → 4. OQ 해소 확인 |

#### op-sdd-verify

| 항목 | 내용 |
|------|------|
| 역할 | 명세/태스크 검증 (mode=spec / mode=tasks) |
| 입력 (mode=spec) | spec.md + 프로젝트 컨텍스트 |
| 입력 (mode=tasks) | tasks.md + spec.md + test-scenarios.md |
| 출력 (mode=spec) | verify.md (SPEC 검증 섹션) + tests/test-scenarios.md |
| 출력 (mode=tasks) | verify.md (TASKS 검증 섹션 추가) |
| 페르소나 | spec-verifier (검증 전문가 — 신규) |
| 핵심 프로세스 (spec) | 1. 구조적 검증 → 2. 의미적 검증 → 3. 도메인 검증 → 4. 테스트 시나리오 도출 (TDD Red) |
| 핵심 프로세스 (tasks) | 1. AC 커버리지 → 2. TS 커버리지 → 3. 의존관계 유효성 → 4. 자기 완결성 → 5. 크기 적정성 |

#### op-sdd-plan

| 항목 | 내용 |
|------|------|
| 역할 | spec.md + test-scenarios.md → SPEC-PLAN.md 작성 (기능 수준 설계) |
| 입력 | spec.md, test-scenarios.md, 프로젝트 컨텍스트 (ARCHITECTURE.md 등) |
| 출력 | specs/{NNN}-{feature}/SPEC-PLAN.md |
| 페르소나 | system-architect (시스템 아키텍트 — 신규) |
| 핵심 프로세스 | 1. 기존 아키텍처 분석 → 2. 컴포넌트 설계 → 3. 데이터 모델 → 4. API 설계 → 5. 기술 결정 → 6. 제약 반영 확인 |

**참조**: Kiro의 design.md, spec-kit의 plan.md, cc-sdd의 design.md와 동일한 역할

#### op-sdd-tasks

| 항목 | 내용 |
|------|------|
| 역할 | spec.md + SPEC-PLAN.md + test-scenarios.md → tasks.md 작성 (태스크 분해) |
| 입력 | spec.md, SPEC-PLAN.md, test-scenarios.md, 프로젝트 컨텍스트 |
| 출력 | specs/{NNN}-{feature}/tasks.md |
| 페르소나 | task-decomposer (태스크 분해 전문가 — 신규) |
| 핵심 프로세스 | 1. AC/FR 분석 → 2. 태스크 분해 → 3. 추적 매트릭스 작성 → 4. 의존관계 결정 → 5. 스킬 추천 |

---

### D14. STATE.md 도메인 설정

```markdown
# STATE: {기능명} SDD 개발

> 최종 갱신: YYYY-MM-DD HH:mm

## 현재 상태
- 모드: SDD Task
- Phase: {TASK / SPEC / SPEC-VERIFY / SPEC-PLAN / TASKS / TASKS-VERIFY / EXECUTE-LOOP / DONE}
- 진행: {T{N}/{M} (EXECUTE-LOOP 시)}
- 상태: {진행 중 / 대기 중 / 블로커 / 완료}

## 완료 산출물
| 산출물 | 상태 |
|--------|------|
| TASK.md | {⬜ / ✅} |
| spec.md | {⬜ / ✅} |
| verify.md (SPEC) | {⬜ / ✅} |
| test-scenarios.md | {⬜ / ✅} |
| SPEC-PLAN.md | {⬜ / ✅} |
| tasks.md | {⬜ / ✅} |
| verify.md (TASKS) | {⬜ / ✅} |
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

### D15. SPEC-PLAN.md 표준 구조

```markdown
# SPEC-PLAN: {기능명}

> 버전: 1.0 | 작성일: YYYY-MM-DD | spec.md v{X.Y} 기준

## 1. 아키텍처 설계
컴포넌트 구성, 의존관계, 다이어그램

## 2. 데이터 모델
엔티티, 관계, 스키마

## 3. API 설계
엔드포인트, 요청/응답, 인터페이스

## 4. 기술 결정
라이브러리 선택, 패턴 선택, 근거

## 5. 보안 고려사항
인증/인가, 데이터 보호

## 6. 에러 핸들링
예외 처리 전략, 실패 시나리오

## 7. 제약 반영
spec.md Constraints를 설계에 어떻게 반영했는지
```

**Gate**: PM Gate + 사용자 Gate (QA Gate 없음 — 설계 결정은 판단 검토가 중요, 바로 뒤 TASKS-VERIFY에서 AC 커버리지 간접 검증)

---

### D16. opsdd SKILL.md references/ 분리 구조

opsdd 오케스트레이터 SKILL.md는 7 Phase + agentic + oppd 연계로 500줄을 초과할 수 있다. oppd와 동일한 패턴으로 상세 가이드를 references/로 분리한다.

**SKILL.md에 남는 것** (500줄 이내):
- 파이프라인 흐름 요약 (7 Phase 한눈에)
- 각 Phase 디스패치 1~2줄 (스킬명, 에이전트, model, Gate)
- Harness 참조, Agentic Mode 개요
- "상세는 references/xxx-guide.md 참조" 위임

**references/로 분리하는 것**:

```
opal/skills/opal-pilot-sdd/
├── SKILL.md                              ← 파이프라인 뼈대 (500줄 이내)
└── references/
    ├── spec-guide.md                     ← spec.md 작성 가이드 + 10섹션 표준 구조
    ├── spec-plan-guide.md                ← SPEC-PLAN.md 작성 가이드 + 7섹션 표준 구조
    ├── execute-loop-guide.md             ← EXECUTE-LOOP 상세 (루프 관리, 병렬 실행, 스킬 결정 기준, SDD 컨텍스트 주입 프롬프트)
    └── verify-guide.md                   ← 검증 3계층 상세 + verify.md/test-scenarios.md 구조
```

| 가이드 | 내용 | 참조하는 Phase |
|--------|------|--------------|
| spec-guide.md | spec.md 10섹션 구조(D5), AC GIVEN/WHEN/THEN 형식, OQ 해소 규칙 | Phase 1: SPEC |
| spec-plan-guide.md | SPEC-PLAN.md 7섹션 구조(D15), 설계 결정 기록 형식 | Phase 3: SPEC-PLAN |
| execute-loop-guide.md | 태스크별 실행 흐름(D6), 스킬 결정 기준, 병렬 실행 패턴, SDD 컨텍스트 주입 디스패치 프롬프트 템플릿, 상태 갱신 절차 | Phase 6: EXECUTE-LOOP |
| verify-guide.md | 3계층 검증 항목(D3), verify.md 누적 저널 구조(D9), test-scenarios.md 구조, 판정 로직 | Phase 2,5: SPEC-VERIFY, TASKS-VERIFY |

**단계 스킬의 references/ 활용**:
- op-sdd-spec → `references/spec-guide.md` 참조 (오케스트레이터와 공유)
- op-sdd-plan → `references/spec-plan-guide.md` 참조
- op-sdd-verify → `references/verify-guide.md` 참조
- op-sdd-tasks → tasks.md 구조는 스킬 자체에 포함 (분리 불필요)

---

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| 1 | `opal/skills/opal-pilot-sdd/SKILL.md` | opsdd 오케스트레이터 메인 (뼈대) |
| 2 | `opal/skills/opal-pilot-sdd/references/spec-guide.md` | spec.md 작성 가이드 + 표준 구조 |
| 3 | `opal/skills/opal-pilot-sdd/references/spec-plan-guide.md` | SPEC-PLAN.md 작성 가이드 + 표준 구조 |
| 4 | `opal/skills/opal-pilot-sdd/references/execute-loop-guide.md` | EXECUTE-LOOP 상세 (루프, 병렬, 디스패치) |
| 5 | `opal/skills/opal-pilot-sdd/references/verify-guide.md` | 검증 3계층 + verify.md/test-scenarios.md 구조 |
| 6 | `opal/skills/op-sdd-spec/SKILL.md` | SPEC 단계 스킬 |
| 7 | `opal/skills/op-sdd-spec/personas/spec-writer.md` | 명세 작성 페르소나 |
| 8 | `opal/skills/op-sdd-verify/SKILL.md` | VERIFY 단계 스킬 (mode=spec/tasks) |
| 9 | `opal/skills/op-sdd-verify/personas/spec-verifier.md` | 검증 페르소나 |
| 10 | `opal/skills/op-sdd-plan/SKILL.md` | SPEC-PLAN 단계 스킬 |
| 11 | `opal/skills/op-sdd-plan/personas/system-architect.md` | 시스템 아키텍트 페르소나 |
| 12 | `opal/skills/op-sdd-tasks/SKILL.md` | TASKS 단계 스킬 |
| 13 | `opal/skills/op-sdd-tasks/personas/task-decomposer.md` | 태스크 분해 페르소나 |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `docs/PROJECT.md` | 스킬 테이블에 opsdd + 4개 단계 스킬 추가 |
| 2 | `docs/ARCHITECTURE.md` | 오케스트레이터 목록에 opsdd 추가, 스킬 그룹에 op-sdd-* 추가 |
| 3 | `docs/CONVENTIONS.md` | 약어 테이블에 `opsdd: opal-pilot-sdd` 추가, 컴포넌트 네이밍에 `op-sdd-*` 추가 |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| - | 없음 | - |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | 페르소나 4개 작성 | personas/*.md | Low |
| 2 | op-sdd-spec SKILL.md | op-sdd-spec/SKILL.md | Medium |
| 3 | op-sdd-verify SKILL.md | op-sdd-verify/SKILL.md | High |
| 4 | op-sdd-plan SKILL.md | op-sdd-plan/SKILL.md | Medium |
| 5 | op-sdd-tasks SKILL.md | op-sdd-tasks/SKILL.md | Medium |
| 6 | opsdd references/ 4개 | opal-pilot-sdd/references/*.md | Medium |
| 7 | opsdd 오케스트레이터 SKILL.md | opal-pilot-sdd/SKILL.md | High |
| 8 | 프로젝트 문서 갱신 | docs/PROJECT.md, ARCHITECTURE.md, CONVENTIONS.md | Low |

---

## 3. 실행 체크리스트

> 총 10개 Step | Phase 5개
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1     | 1    | 순차 | 기반 페르소나 (후속 의존) |
> | 2     | 2, 3, 4, 5 | 병렬 | 독립 단계 스킬 (각각 다른 파일) |
> | 3     | 6    | 순차 | Step 2,3,4,5 의존 (references/ 가이드) |
> | 4     | 7    | 순차 | Step 6 의존 (오케스트레이터 — references/ 참조) |
> | 5     | 8, 9, 10 | 병렬 | 독립 문서 갱신 |

### Step 1: 페르소나 4개 작성
- [x] 완료
- **파일**: `opal/skills/op-sdd-spec/personas/spec-writer.md`, `opal/skills/op-sdd-verify/personas/spec-verifier.md`, `opal/skills/op-sdd-plan/personas/system-architect.md`, `opal/skills/op-sdd-tasks/personas/task-decomposer.md`
- **작업 내용**: D13의 각 스킬에 대응하는 페르소나를 generalist-architect.md 패턴으로 작성. 원칙/행동 규칙/조사 방식 포함
- **완료 기준**: 4개 페르소나 파일 존재, 각각 원칙 5개 이상 + 행동 규칙 정의
- **테스트**: 파일 존재 확인 + 내용 구조 검증
- **의존**: 없음

### Step 2: op-sdd-spec SKILL.md 작성
- [x] 완료
- **파일**: `opal/skills/op-sdd-spec/SKILL.md`
- **작업 내용**: D5의 spec.md 표준 구조를 산출물로 생성하는 단계 스킬. YAML frontmatter + 입출력 명세 + 프로세스(프로젝트 분석 → 10섹션 spec.md 작성 → AC GIVEN/WHEN/THEN 보장 → OQ 해소 확인) + 품질 체크리스트
- **완료 기준**: SKILL.md 500줄 이하, 필수 섹션(frontmatter/입출력/프로세스/출력형식/품질체크리스트) 완비, spec-writer 페르소나 참조
- **테스트**: SKILL.md Read → 구조 확인
- **의존**: Step 1 (페르소나)

### Step 3: op-sdd-verify SKILL.md 작성
- [x] 완료
- **파일**: `opal/skills/op-sdd-verify/SKILL.md`
- **작업 내용**: D9의 verify.md 저널 구조를 산출물로 생성하는 검증 스킬. mode=spec(3계층 검증 + test-scenarios.md 도출) / mode=tasks(커버리지/의존관계 검증). 판정 로직(Pass/Warning/Fail), 실패 시 재작성 지시 형식 포함
- **완료 기준**: SKILL.md 500줄 이하, mode 분기 로직 명확, 검증 항목 테이블 완비, spec-verifier 페르소나 참조
- **테스트**: SKILL.md Read → mode=spec/tasks 분기 확인
- **의존**: Step 1 (페르소나)

### Step 4: op-sdd-plan SKILL.md 작성
- [x] 완료
- **파일**: `opal/skills/op-sdd-plan/SKILL.md`
- **작업 내용**: D15의 SPEC-PLAN.md 표준 구조를 산출물로 생성하는 설계 스킬. spec.md + test-scenarios.md 기반으로 아키텍처 설계, 데이터 모델, API 설계, 기술 결정을 수립. YAML frontmatter + 입출력 명세 + 프로세스(기존 아키텍처 분석 → 컴포넌트 설계 → 데이터 모델 → API 설계 → 기술 결정 → 제약 반영 확인) + 품질 체크리스트
- **완료 기준**: SKILL.md 500줄 이하, 필수 섹션(frontmatter/입출력/프로세스/출력형식/품질체크리스트) 완비, system-architect 페르소나 참조
- **테스트**: SKILL.md Read → 구조 확인
- **의존**: Step 1 (페르소나)

### Step 5: op-sdd-tasks SKILL.md 작성
- [x] 완료
- **파일**: `opal/skills/op-sdd-tasks/SKILL.md`
- **작업 내용**: D8의 tasks.md 구조를 산출물로 생성하는 태스크 분해 스킬. 추적 매트릭스 작성 + 의존관계 결정 + 스킬 추천(opds/opd) 로직 + 상태 필드 초기화
- **완료 기준**: SKILL.md 500줄 이하, 추적 매트릭스/의존관계/스킬 추천 프로세스 포함, task-decomposer 페르소나 참조
- **테스트**: SKILL.md Read → 구조 확인
- **의존**: Step 1 (페르소나)

### Step 6: opsdd references/ 4개 작성
- [x] 완료
- **파일**: `opal/skills/opal-pilot-sdd/references/spec-guide.md`, `spec-plan-guide.md`, `execute-loop-guide.md`, `verify-guide.md`
- **작업 내용**: D16 references/ 분리 구조에 따라 4개 가이드 작성. spec-guide.md(D5 spec.md 10섹션 표준 + AC 형식), spec-plan-guide.md(D15 SPEC-PLAN.md 7섹션 표준), execute-loop-guide.md(D6 루프 관리 + 병렬 실행 + 스킬 결정 기준 + SDD 컨텍스트 주입 디스패치 프롬프트 템플릿), verify-guide.md(D3+D9 검증 3계층 + verify.md 누적 저널 + test-scenarios.md 구조)
- **완료 기준**: 4개 가이드 파일 존재, 각각 해당 D 섹션 내용을 완전히 포함
- **테스트**: 4개 파일 존재 확인 + 내용 구조 검증
- **의존**: Step 2, 3, 4, 5 (단계 스킬에서 참조하는 구조를 가이드가 상세화)

### Step 7: opal-pilot-sdd SKILL.md 작성
- [x] 완료
- **파일**: `opal/skills/opal-pilot-sdd/SKILL.md`
- **작업 내용**: D1~D16 설계를 반영한 opsdd 오케스트레이터. **SKILL.md는 파이프라인 뼈대만** — 7단계 흐름 요약, 각 Phase 디스패치 1~2줄(스킬명/에이전트/model/Gate), Harness 참조, Agentic Mode 개요. 상세는 `references/xxx-guide.md 참조`로 위임
- **완료 기준**: SKILL.md **500줄 이하**, 7 Phase 각각의 디스패치 + Gate가 1~2줄로 요약, references/ 위임 참조 4건 포함, Agentic Mode 섹션 포함
- **테스트**: SKILL.md Read → 500줄 이내 확인 + 7 Phase 존재 + references/ 참조 4건 확인
- **의존**: Step 6 (references/ 가이드 완료 후)

### Step 8: 프로젝트 문서 갱신 (PROJECT.md + ARCHITECTURE.md)
- [x] 완료
- **파일**: `docs/PROJECT.md`, `docs/ARCHITECTURE.md`
- **작업 내용**: PROJECT.md 스킬 테이블에 opsdd/op-sdd-spec/op-sdd-verify/op-sdd-plan/op-sdd-tasks 추가. ARCHITECTURE.md 오케스트레이터 목록/스킬 그룹에 opsdd 계열 추가
- **완료 기준**: 두 문서에 신규 컴포넌트 5개 등록
- **테스트**: Grep으로 opsdd/op-sdd 존재 확인
- **의존**: Step 7 (오케스트레이터 확정 후)

### Step 9: CONVENTIONS.md 갱신
- [x] 완료
- **파일**: `docs/CONVENTIONS.md`
- **작업 내용**: 약어 테이블에 `opsdd: opal-pilot-sdd` 추가. 컴포넌트 네이밍 체계에 `op-sdd-*: SDD 단계 스킬` 추가. specs/ 폴더 네이밍 규칙(`{NNN}-{feature-name}/`) 추가
- **완료 기준**: 3개 항목(약어, 네이밍, specs 규칙) 반영
- **테스트**: Read → 해당 섹션 존재 확인
- **의존**: Step 7 (오케스트레이터 확정 후)

### Step 10: 스킬/에이전트 레지스트리 갱신
- [x] 완료
- **파일**: `~/.opal/references/skills.md`, `~/.opal/references/agents.md`
- **작업 내용**: skills.md에 opsdd + 4개 단계 스킬(op-sdd-spec, op-sdd-verify, op-sdd-plan, op-sdd-tasks) 등록
- **완료 기준**: 5개 스킬 레지스트리 등록
- **테스트**: Grep으로 op-sdd 존재 확인
- **의존**: Step 7 (오케스트레이터 확정 후)

---

## 4. QA 체크리스트

### 기능 테스트
- [x] R1: 7단계 파이프라인이 SKILL.md에 Phase 1~7으로 명세되어 있는가 — **PASS**
- [x] R2: 각 Phase의 수행 주체(PM 직접 / 워커 디스패치)와 에이전트가 명확한가 — **PASS**
- [x] R3: PM Gate + 사용자 Gate가 모든 Phase에 적용되고, QA Gate가 SPEC-VERIFY/TASKS-VERIFY/EXECUTE-LOOP/DONE에 적용되어 있는가 — **PASS**
- [x] R4: EXECUTE-LOOP에서 opds/opd 호출 방식이 디스패치 프롬프트로 명세되어 있는가 — **PASS**
- [x] R5: specs/ 폴더 구조가 `{NNN}-{feature}/` 순번을 포함하는가 — **PASS**
- [x] R6: specs/(SDD) ↔ tasks/(OPAL) 연결 구조(spec_path)가 정의되어 있는가 — **PASS**
- [x] R7: tasks.md에 추적 매트릭스 + 의존관계 + 상태 열거형이 있는가 — **PASS**
- [x] R8: SPEC-VERIFY에 3계층 검증(구조/의미/도메인) + AC→TS 도출이 있는가 — **PASS**
- [x] R9: TASKS-VERIFY에 AC 커버리지 + 의존관계 유효성 + 자기완결성 검증이 있는가 — **PASS**
- [x] R10: EXECUTE-LOOP에서 L1~L3b 검증 루프가 명세되어 있는가 — **PASS**
- [x] R11: --agentic 모드가 자율 게이트 + AGENTIC-LOG + Gate 루핑으로 설계되어 있는가 — **PASS**
- [x] R12-13: 신규 스킬 4개(op-sdd-spec, op-sdd-verify, op-sdd-plan, op-sdd-tasks)의 에이전트 매핑이 명확한가 — **PASS**
- [x] R20: SPEC-PLAN.md 7섹션 표준 구조(아키텍처/데이터 모델/API/기술 결정/보안/에러/제약)가 정의되어 있는가 — **PASS**
- [x] R14: 기존 스킬 재활용 범위(op-dev-plan, op-dev-execute, op-dev-qa)가 확정되어 있는가 — **PASS** (Warning: opds/opd 통한 간접 재활용)
- [x] R15: spec.md 10섹션 표준 구조가 정의되어 있는가 — **PASS**
- [x] R16: 문서 계층(TASK→spec→tests/tasks→verify)이 명확한가 — **PASS**
- [x] R17: verify.md 누적 저널이 Phase별 섹션 추가 방식인가 — **PASS**
- [~] R18: oppd와의 역할 분담이 정리되어 있는가 — **WARNING** (SKILL.md에 별도 섹션 없음)
- [~] R19: oppd Phase 3 액션 스킬로서의 등록 방안이 있는가 — **WARNING** (의도적 후속 태스크 분리)

### 일관성 테스트
- [x] 신규 스킬 네이밍이 CONVENTIONS.md의 `op-sdd-*` 체계를 따르는가 — **PASS**
- [x] 하네스 변경 없이 기존 Guards/Gates/State를 그대로 활용하는가 — **PASS**
- [x] 기존 에이전트(opal-task-agent)를 추가 변경 없이 재활용하는가 — **PASS**
- [x] 모델 매핑이 opal-model-mapping.md의 light/standard/advanced 레벨을 사용하는가 — **PASS**
- [x] 디스패치 프롬프트가 기존 오케스트레이터의 `[WORKER]` 마커 + Guards + 참조문서 패턴을 따르는가 — **PASS**
- [x] STATE.md 템플릿이 하네스 §3 공통 템플릿 구조를 준수하는가 — **PASS**

### 문서 품질
- [x] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가 — **PASS**
- [x] kebab-case 파일/폴더 네이밍을 따르는가 — **PASS**
- [~] YAML frontmatter가 기존 스킬 패턴을 따르는가 — **WARNING** (워커 스킬 triggers 없음)
- [~] 각 SKILL.md가 500줄 이하인가 — **PASS** (Warning: op-sdd-verify 411줄로 경계선 근접)
- [x] 변경이력 테이블이 포함되어 있는가 — **PASS**

> QA 결과: **Pass with Warnings** (Fail 0, Warning 4) — 상세: `QA-EXECUTE.md`

---

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| SKILL.md 500줄 제한 초과 | opsdd 오케스트레이터는 7 Phase + agentic + oppd 연계로 내용이 많음 | **D16 references/ 분리 구조** 적용 — SKILL.md는 파이프라인 뼈대만, 상세는 references/로 위임 |
| op-sdd-verify의 mode 분기 복잡도 | spec/tasks 두 모드의 검증 항목이 상이하여 스킬이 비대해질 수 있음 | 공통 프로세스(verify.md 갱신)는 통합, 검증 항목만 mode별 분기. 각 mode의 상세는 references/ 활용 |
| EXECUTE-LOOP에서 기존 opds/opd 호출 시 SDD 컨텍스트 유실 | 기존 스킬은 spec.md/AC를 모르므로, 디스패치 프롬프트에 주입하지 않으면 TDD 패턴이 작동 안 함 | 디스패치 프롬프트에 spec.md 경로, AC 매핑, TS 목록, "테스트 먼저 작성" 지시를 명시적으로 포함 |
| specs/ 폴더와 tasks/ 폴더 간 동기화 | 두 세계의 상태가 불일치할 수 있음 | STATE.md가 양쪽 경로를 모두 추적. tasks.md 상태와 STATE.md 상태를 이중 관리 |
| oppd 연계 시 opsdd의 7단계가 oppd Phase 3 액션 내부에서 실행되면 컨텍스트 깊이 과도 | oppd → opsdd → opds로 3중 중첩 | oppd에서 opsdd를 호출할 때는 opsdd의 각 Phase를 개별 액션으로 flatten하거나, opsdd를 oppd와 동격 독립 실행으로 한정. 초기에는 독립 실행만 지원하고 oppd 연계는 후속 태스크로 |
