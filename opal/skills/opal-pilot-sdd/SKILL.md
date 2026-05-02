---
name: opal-pilot-sdd
description: |
  **SDD(Spec-Driven Development) 오케스트레이터**. 명세 기반 개발을 6단계 파이프라인으로 수행한다.
  기능 단위로 SPEC.md(SSOT) 작성 → PM 직접 검증 + TEST-SCENARIOS.md 작성 → 아키텍처 설계 + ACT 분해 → 반복 실행 → E2E 검증 → 완료.
  반드시 이 스킬을 사용해야 하는 상황: "opal-pilot-sdd", "opsdd".
  단일 태스크 개발은 opds/opd를, 범용 작업은 opp를 사용한다.
triggers:
  - "opal-pilot-sdd"
  - "opsdd"
  - "SDD 개발"
  - "명세 기반 개발"
version: 2.5.0
---

# opal-pilot-sdd (SDD 오케스트레이터)

명세(SPEC.md)를 SSOT로 삼아 검증 → 설계 → ACT 분해 → 반복 실행 → E2E 검증까지 6단계 파이프라인으로 관리한다.
EXECUTE-LOOP에서 `opal-sdd-action-agent`에 단일 디스패치하며, PM이 전체를 조율한다.

## Harness

모드: SDD Task (TASK → SPEC → REVIEW → DESIGN → EXECUTE-LOOP → VERIFY → CLOSE)
> 부트스트랩에서 로드되지 않은 경우: `~/.opal/references/opal-harness.md`를 Read한다.

**[MUST]** 스킬 시작 즉시 모드에 따라 서브 하네스를 Read한다. 이 단계를 건너뛰면 안 된다:
- `--agentic` 플래그 있음 → `~/.opal/references/opal-harness-agentic.md`를 Read한다
- `--agentic` 없음 (기본) → `~/.opal/references/opal-harness-interactive.md`를 Read한다

> **[MUST]** 산출물 작성·검증 시 `opal/core/references/harness/citation-rules.md`를 Read하여 규칙(근거 제시 원칙 / 트랙별 매트릭스 / [MUST] 토큰 / 영역 간 용어 일관성 / decision_required 계약)을 준수한다.

---

## 6단계 파이프라인 요약

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
Phase 5: VERIFY    PM 직접    Playwright E2E → TEST-SCENARIOS.md 추적 매트릭스 갱신
                              → 전체 TS Green 확인 → 사용자 Gate (= CLOSE 진입 게이트)
Phase 6: CLOSE     PM 직접    최종 확인 → DONE.md 생성
                              → State Gate
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
├── DONE.md                  # Phase 6 — 최종 완료 확인
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
**핵심 제약**: {[MUST] <문서명> §N: <인용문> 형식으로 원문 인용 필수 항목. 요약 허용 항목은 일반 목록}
```
**에이전트**: opal-task-agent | **model**: advanced

**Gate**:
  → **State Gate** → **PM Gate** → 사용자 Gate (QA Gate 없음 — 다음 Phase에서 PM이 직접 검증)

State Gate 시 state-tool 호출 (R-10: gate-pass 금지 — mark 4회 개별 호출 필수):

```
~/.opal/tools/state-tool/run.sh mark <task-path> --row 6 --done   # State Gate
~/.opal/tools/state-tool/run.sh mark <task-path> --row 7 --done   # PM Gate
~/.opal/tools/state-tool/run.sh mark <task-path> --row 8 --done   # State Gate
~/.opal/tools/state-tool/run.sh mark <task-path> --row 9 --done --owner user --note '캡틴 확인: SPEC 완료'
```

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
**핵심 제약**: {[MUST] <문서명> §N: <인용문> 형식으로 원문 인용 필수 항목. 요약 허용 항목은 일반 목록}
```
**에이전트**: opal-task-agent | **model**: advanced

**Gate**:
  → **State Gate** → **PM Gate** → 사용자 Gate (QA Gate 없음 — 설계 + ACT 분해는 PM 판단)

State Gate 시 state-tool 호출 (R-10: gate-pass 금지 — mark 4회 개별 호출 필수):

```
~/.opal/tools/state-tool/run.sh mark <task-path> --row 19 --done  # State Gate
~/.opal/tools/state-tool/run.sh mark <task-path> --row 20 --done  # PM Gate
~/.opal/tools/state-tool/run.sh mark <task-path> --row 21 --done  # State Gate
~/.opal/tools/state-tool/run.sh mark <task-path> --row 22 --done --owner user --note '캡틴 확인: DESIGN 완료'
```

> SPEC-PLAN.md 상세 구조: `references/spec-plan-guide.md` 참조

---

## Phase 4: EXECUTE-LOOP

SPEC-PLAN.md의 의존 순서대로 ACT를 반복 실행한다. 각 ACT는 `opal-sdd-action-agent`에 단일 디스패치하여 자율 완주한다.

### ACT 실행 순서

1. **사용자 Gate**: ACT 시작 전 승인 (interactive 모드)
2. **opal-sdd-action-agent 디스패치**: ACT 폴더 생성 + PLAN + EXECUTE + VERIFY 루프 자율 완주
3. **결과 수신**: status 확인
4. **Pass/Fail 판정**: Pass → DONE.md 작성 | Fail → 재시도 루프
5. **state-tool로 STATE.md ACT 행 갱신**: ACT 상태 + TS 상태 갱신

### 재시도 루프

`status: failed` 반환 시 오류 컨텍스트를 주입하여 opal-sdd-action-agent를 재디스패치한다.
하네스 §1 자동 루핑 제약 준수 (unit/integration 최대 3회).

### 병렬 실행

의존관계 없는 ACT는 worktree 격리 + 병렬 디스패치:
- worktree 경로: `.worktrees/{NNN}-ACT-{NNN}/`
- 결과 수집 → 순차 머지 → 통합 테스트 → worktree 정리

### L1/L2 검증 루프 (PM 직접 실행)

PM은 워커가 각 ACT를 완료할 때마다 다음을 직접 실행한다:
- **L1**: `tsc --noEmit` — lint + type check
- **L2**: `pnpm build` — 전체 빌드

Pass → STATE.md ACT 목록 L1 ✅, L2 ✅, 상태 ✅ 갱신
Fail → 워커에 SendMessage로 수정 지시 → 재검증 (L1부터)
L2 2회 초과 실패 → 소유자 에스컬레이션

전체 ACT 완료 후에도 최종 L1 + L2 통합 빌드 확인 필수.

### 상태 갱신

ACT 완료마다 state-tool을 호출하여 STATE.md를 갱신한다 (R-10: gate-pass 금지 — mark 4회 개별 호출 필수):
- ACT 목록 행은 `add-row --after <N> --stage EXECUTE --item 'ACT-{N}: {이름}'` 로 동적 삽입
- ACT 상태 갱신: `mark <task-path> --row <ACT_행N> --done`
- TS 상태, L1/L2: ACT 완료 후 PM 직접 검증 → ACT 목록 내 해당 열 갱신

> **[R-13] ACT 동적 행**: `--rows-acts` 옵션은 미구현. ACT 행은 EXECUTE Phase 진입 후 수동으로 `add-row`로 삽입한다.

**State Gate** (ACT 루프 완료 후, EXECUTE 행 #24~#27 처리):

```
~/.opal/tools/state-tool/run.sh mark <task-path> --row 24 --done  # State Gate
~/.opal/tools/state-tool/run.sh mark <task-path> --row 25 --done  # PM Gate
~/.opal/tools/state-tool/run.sh mark <task-path> --row 26 --done  # State Gate
~/.opal/tools/state-tool/run.sh mark <task-path> --row 27 --done --owner user --note '캡틴 확인: EXECUTE 완료'
```

### Gate

- **interactive**: 각 ACT 시작 전 사용자 Gate (opal-sdd-action-agent 디스패치 승인) + 완료마다 사용자 Gate
- **agentic**: PM이 ACT 간 Gate를 자율 통과

> EXECUTE-LOOP 상세: `references/execute-loop-guide.md` 참조

---

## Phase 5: VERIFY

### 개요
- 수행 주체: PM 직접 (워커 디스패치 없음)
- 진입 조건: EXECUTE-LOOP 전체 ACT ✅ + 최종 L2 빌드 Pass
- Gate: State Gate → PM Gate → State Gate → 사용자 Gate

### 수행 절차
1. TEST-SCENARIOS.md의 모든 시나리오를 Playwright E2E로 수행
2. 각 시나리오 Pass/Fail 확인 즉시 TEST-SCENARIOS.md 추적 매트릭스 갱신 (배치 금지)
3. STATE.md TS 현황 요약 갱신 (Green/Red/Fail/Skip 건수)

### 완료 조건
- 전체 TS Green (또는 Skip + 사유 기록)
- State Gate → PM Gate → State Gate → 사용자 확인 순으로 Gate 통과

### Fail 처리
- 해당 ACT 재지시 또는 코드 직접 수정 → 재검증

---

## Phase 6: CLOSE

모든 ACT 완료 및 VERIFY Phase 통과(사용자 확인 = CLOSE 진입 게이트) 후 태스크를 마감한다.

1. 전체 TS Green 확인 (STATE.md TS 현황)
2. 전체 ACT DONE.md 존재 확인
3. DONE.md 생성
4. State Gate:

```
~/.opal/tools/state-tool/run.sh mark <task-path> --row 34 --done  # DONE.md 생성
~/.opal/tools/state-tool/run.sh mark <task-path> --row 35 --done  # State Gate (CLOSE 완료)
```

> **CLOSE 게이트 제약 (§2.16 G-13)**: CLOSE 단계 최초 진입 행(#34)은 `--auto-pass` 적용 불가 (`close_gate_violation`). 반드시 위 명시 호출로 처리한다.

보고 형식:
```
✅ [CLOSE] 태스크 완료
📎 산출물: tasks/{NNN}-{feature}/DONE.md
태스크가 완료되었습니다.
```

> **추가작업**: 태스크 완료 후 추가작업이 필요하면 하네스 §3 "추가작업 프로세스"를 따른다.

---

## STATE.md 도메인 치환값

| 필드 | 값 |
|------|------|
| 모드 | SDD Task |
| 단계 목록 | TASK / SPEC / REVIEW / DESIGN / EXECUTE-LOOP / VERIFY / CLOSE |
| 산출물 목록 | TASK.md, SPEC.md, TEST-SCENARIOS.md, SPEC-PLAN.md, actions/ACT-{N}/, DONE.md |
| 태스크 경로 | tasks/{NNN}-{feature}/ |

> **[SSOT]** `state-tool init` 호출 시 이 섹션의 파이프라인 현황판 행 테이블을 `--rows-from` 옵션으로 참조한다:
>
> ```
> ~/.opal/tools/state-tool/run.sh init <task-path> --skill opsdd --rows-from opal/skills/opal-pilot-sdd/SKILL.md
> ```
>
> state-tool이 이 파일의 "파이프라인 현황판" 테이블(35행)을 읽어 state.json을 초기화한다. 행 데이터를 직접 편집하지 않는다.
>
> **[R-10 비표준 행 구성]** opsdd는 35행 + ACT 동적 행 비표준 구조를 사용한다. `gate-pass`(4-row 일괄) 사용 불가 — `mark` 4회 개별 호출 필수. `gate-pass` 호출 시 `gate_pattern_mismatch` 에러가 반환된다.
>
> **[R-13 ACT 동적 행]** `--rows-acts` 옵션은 미구현. EXECUTE Phase 진입 후 `add-row`로 ACT 행을 수동 삽입한다:
> ```
> ~/.opal/tools/state-tool/run.sh add-row <task-path> --after 23 --stage EXECUTE --item 'ACT-001: {이름}'
> ```

### STATE.md 구조

```markdown
# STATE: {기능명} SDD 개발

> 최종 갱신: YYYY-MM-DD HH:mm

## 현재 상태
- 모드: SDD Task
- Phase: {현재 Phase (TASK/SPEC/REVIEW/DESIGN/EXECUTE-LOOP/VERIFY/CLOSE)}
- 상태: {진행 중 / 완료 / 블로커 / 추가작업중 / 추가작업완료}

## 파이프라인 현황판

> 상태값: ⬜ 대기 / 🔄 진행 중 / ✅ 완료 / ❌ 실패 / - 해당 없음
> **수행 원칙**: 위에서 아래로 순서대로 처리한다. 현재 행이 ✅가 아니면 다음 행으로 진행 불가.

| # | Phase | 항목 | 상태 | 시점 |
|---|-------|------|------|------|
| 1 | TASK | TASK.md 작성 | ⬜ | |
| 2 | TASK | STATE.md 생성 | ⬜ | |
| 3 | TASK | 사용자 확인 | ⬜ | |
| 4 | SPEC | 워커 디스패치 | ⬜ | |
| 5 | SPEC | SPEC.md 생성 | ⬜ | |
| 6 | SPEC | State Gate | ⬜ | |
| 7 | SPEC | PM Gate | ⬜ | |
| 8 | SPEC | State Gate | ⬜ | |
| 9 | SPEC | 사용자 확인 | ⬜ | |
| 10 | REVIEW | 구조 검증 (S-1~S-6) | ⬜ | |
| 11 | REVIEW | TEST-SCENARIOS.md 작성 | ⬜ | |
| 12 | REVIEW | FR↔TS 커버리지 확인 | ⬜ | |
| 13 | REVIEW | State Gate | ⬜ | |
| 14 | REVIEW | PM Gate | ⬜ | |
| 15 | REVIEW | State Gate | ⬜ | |
| 16 | REVIEW | 사용자 확인 | ⬜ | |
| 17 | DESIGN | 워커 디스패치 | ⬜ | |
| 18 | DESIGN | SPEC-PLAN.md 생성 | ⬜ | |
| 19 | DESIGN | State Gate | ⬜ | |
| 20 | DESIGN | PM Gate | ⬜ | |
| 21 | DESIGN | State Gate | ⬜ | |
| 22 | DESIGN | 사용자 확인 | ⬜ | |
| 23 | EXECUTE | ACT 실행 (상세: ACT 목록 참조) | ⬜ | |
| 24 | EXECUTE | State Gate | ⬜ | |
| 25 | EXECUTE | PM Gate | ⬜ | |
| 26 | EXECUTE | State Gate | ⬜ | |
| 27 | EXECUTE | 사용자 확인 | ⬜ | |
| 28 | VERIFY | E2E 테스트 수행 | ⬜ | |
| 29 | VERIFY | TS 전체 Green 확인 | ⬜ | |
| 30 | VERIFY | State Gate | ⬜ | |
| 31 | VERIFY | PM Gate | ⬜ | |
| 32 | VERIFY | State Gate | ⬜ | |
| 33 | VERIFY | 사용자 확인 | ⬜ | |
| 34 | CLOSE | DONE.md 생성 | ⬜ | |
| 35 | CLOSE | State Gate | ⬜ | |

## ACT 목록 (SSOT — EXECUTE Phase 상세)

> DESIGN 완료 후 SPEC-PLAN.md의 ACT를 기반으로 동적 삽입.
> ACT 완료 시 즉시 갱신. SPEC-PLAN.md에는 ACT 상태를 두지 않는다.

| ACT | 이름 | 그룹 | 의존 | 코드 | L1 lint | L2 build | 상태 | 시작 | 완료 |
|-----|------|------|------|------|---------|----------|------|------|------|

> 상태값: ⬜ 대기 / 🔄 진행 중 / ✅ 완료 / ❌ 실패
> L1/L2: ACT 완료 후 PM이 검증 실행. ❌→✅ = 1차 실패 → 수정 → 재통과

## TS 현황 (VERIFY Phase 요약)

> TEST-SCENARIOS.md 추적 매트릭스의 요약. 테스트 수행 시 즉시 갱신.

| 상태 | 건수 |
|------|------|
| Green | 0 |
| Red | 0 |
| Fail | 0 |
| Skip | 0 |

## SPEC 변경 이력

> REVIEW 이후 SPEC.md가 변경된 경우 기록. 변경 추적이 안 되면 TS와 정합성이 깨진다.

| # | 시점 | 변경 내용 | 사유 |
|---|------|----------|------|

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|

## 블로커
없음

## 다음 액션
{다음으로 수행할 작업}
```

---

## PM Gate 점검 목록

| Phase | 산출물 | 체크리스트 위치 |
|-------|-------|----------------|
| SPEC | TASK.md, SPEC.md, QA-SPEC.md | TASK.md 요구사항 |
| DESIGN | SPEC-PLAN.md | - |
| EXECUTE | QA-EXECUTE.md | PLAN.md §3 |

---

## Agentic Mode

opal-harness-agentic.md 참조. `--agentic` 플래그 활성화 시 이 스킬의 차이점만 기술한다.

### 활성화

`//opsdd --agentic {기능 설명}` 형식으로 호출. STATE.md 모드 필드를 `agentic`으로 기록한다:

```
~/.opal/tools/state-tool/run.sh init <task-path> --skill opsdd --mode agentic --rows-from opal/skills/opal-pilot-sdd/SKILL.md
```

### 자율 게이트 흐름

```
TASK (PM 직접)
  → SPEC Gate        -- PM 자율 검토
  → REVIEW           -- PM 직접 수행 (구조검증 + TS작성 + 커버리지)
  → DESIGN Gate      -- PM 자율 검토
  → EXECUTE-LOOP     -- PM 자율 관리 (ACT별 Gate + L1/L2 검증 포함)
  → VERIFY           -- PM 직접 수행 (Playwright E2E + TS 전체 Green 확인 + 사용자 Gate = CLOSE 진입 게이트)
  → CLOSE            -- (사용자 승인 후) DONE.md 생성 + State Gate + 최종 보고
```

- 모든 Phase Gate를 PM이 자율 통과
- EXECUTE-LOOP 진입 = PM이 대행 승인 (구현 금지 원칙의 "실행 허가"를 PM이 판단)
- 자율 통과 시 state-tool `--auto-pass` 호출 (P-8):
  ```
  ~/.opal/tools/state-tool/run.sh mark <task-path> --row N --done --auto-pass --note '<근거>'
  ```
- **CLOSE 단계 최초 진입 행(#34)은 `--auto-pass` 금지** (`close_gate_violation` — §2.16 G-13); 반드시 명시 호출
- R-10 비표준 행 구성: `gate-pass` 금지 — mark 4회 개별 호출 필수 (agentic에서도 동일 적용)
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
| v2.5.0 | 2026-04-10 | R-1 STATE.md 도메인 치환값 → 43행 진행 현황 구조로 교체 + ACT 목록 SSOT + TS 현황 + SPEC 변경이력 섹션 추가; R-2 VERIFY Phase(Phase 5) 신설 + DONE → Phase 6; R-3 EXECUTE-LOOP L1/L2 검증 루프 명시 (105) |
| v2.6.0 | 2026-04-10 | Artifact Gate 제거 + PM Gate 점검 목록 섹션 추가 + 파이프라인 현황판 이름 변경 (106) |
| v2.7.0 | 2026-04-11 | PM Gate 점검 목록 — PLAN-equivalent Phase에 TASK.md 요구사항 추가 (108) |
| v2.8.0 | 2026-04-15 | Phase 1(SPEC)/Phase 3(DESIGN) 디스패치 프롬프트에 `**핵심 제약**:` 필드 추가 — `[MUST] <문서명> §N: <인용문>` 원문 인용 포맷 명시 (120) |
| v2.9.0 | 2026-04-15 | Phase 6 DONE→CLOSE 리네이밍 + 4행→2행 통일 + 단계 목록 갱신 + Agentic Mode 흐름도 갱신 + CLOSE 보고 형식 C안 적용 (121) |
| v3.0.0 | 2026-04-24 | citation-rules 트리거 1줄 주입 — SSOT + Trigger 패턴 (130) |
| v3.1.0 | 2026-05-01 | state-tool 도입 — STATE.md 직접 편집 금지 + `state-tool` 호출 표현 교체 (P-1~P-8 패턴 적용). `--rows-from` SSOT 지시 + R-10 비표준 행 gate-pass 금지 + mark 4회 개별 호출 필수 블록 추가. R-13 ACT 동적 행 `add-row` 임시 가이드. CLOSE State Gate mark 명시 + G-13 제약 추가. agentic `--auto-pass` + CLOSE 진입 게이트 거부 정책 추가 (134) |
