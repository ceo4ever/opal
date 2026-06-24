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
version: 3.5.0
---

# opal-pilot-sdd (SDD 오케스트레이터)

명세(SPEC.md)를 SSOT로 삼아 검증 → 설계 → ACT 분해 → 반복 실행 → E2E 검증까지 6단계 파이프라인으로 관리한다.
EXECUTE-LOOP에서 `opal-sdd-action-agent`에 단일 디스패치하며, PM이 전체를 조율한다.

## Harness

모드: SDD Task (TASK → SPEC → REVIEW → DESIGN → EXECUTE-LOOP → VERIFY → CLOSE)
> 부트스트랩에서 로드되지 않은 경우: `~/.opal/references/opal-harness.md`를 Read한다.

**[MUST]** 스킬 시작 즉시 모드에 따라 서브 하네스를 Read한다. 이 단계를 건너뛰면 안 된다:
- `--interactive` 플래그 → `~/.opal/references/opal-harness-interactive.md`를 Read한다
- `--agentic` 플래그 → `~/.opal/references/opal-harness-agentic.md`를 Read한다
- 모드 플래그 없음 (기본) 또는 `--semi-agentic` → `~/.opal/references/opal-harness-semi-agentic.md`를 Read한다
- 다중 모드 플래그 동시 사용 시 즉시 사용자에게 보고 + state init도 거부 (`mode_flag_conflict`)

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
  → **PM Gate** → 사용자 Gate (QA Gate 없음 — 다음 Phase에서 PM이 직접 검증)

Gate 시 state-tool 호출 (R-10: gate-pass deprecated(014) — mark 개별 호출 필수):

```
~/.opal/tools/state-tool/run.sh mark <task-path> --row 6 --done   # PM Gate
~/.opal/tools/state-tool/run.sh mark <task-path> --row 7 --done --owner user --note '소유자 확인: SPEC 완료'
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
  → **PM Gate** → 사용자 Gate (QA Gate 없음 — 설계 + ACT 분해는 PM 판단)

Gate 시 state-tool 호출 (R-10: gate-pass deprecated(014) — mark 개별 호출 필수):

```
~/.opal/tools/state-tool/run.sh mark <task-path> --row 15 --done  # PM Gate
~/.opal/tools/state-tool/run.sh mark <task-path> --row 16 --done --owner user --note '소유자 확인: DESIGN 완료'
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

ACT 완료마다 state-tool을 호출하여 STATE.md를 갱신한다 (R-10: gate-pass deprecated(014) — mark 개별 호출 필수):
- ACT 목록 행은 `add-row --after <N> --stage EXECUTE --item 'ACT-{N}: {이름}'` 로 동적 삽입
- ACT 상태 갱신: `mark <task-path> --row <ACT_행N> --done`
- TS 상태, L1/L2: ACT 완료 후 PM 직접 검증 → ACT 목록 내 해당 열 갱신

> **[R-13] ACT 동적 행**: `--rows-acts` 옵션은 미구현. ACT 행은 EXECUTE Phase 진입 후 수동으로 `add-row`로 삽입한다.

**Gate** (ACT 루프 완료 후, EXECUTE 행 #18~#19 처리):

```
~/.opal/tools/state-tool/run.sh mark <task-path> --row 18 --done  # PM Gate
~/.opal/tools/state-tool/run.sh mark <task-path> --row 19 --done --owner user --note '소유자 확인: EXECUTE 완료'
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
- Gate: PM Gate → 사용자 Gate

### 수행 절차
1. TEST-SCENARIOS.md의 모든 시나리오를 Playwright E2E로 수행
2. 각 시나리오 Pass/Fail 확인 즉시 TEST-SCENARIOS.md 추적 매트릭스 갱신 (배치 금지)
3. STATE.md TS 현황 요약 갱신 (Green/Red/Fail/Skip 건수)

### 완료 조건
- 전체 TS Green (또는 Skip + 사유 기록)
- PM Gate → 사용자 확인 순으로 Gate 통과

### Fail 처리
- 해당 ACT 재지시 또는 코드 직접 수정 → 재검증

---

## Phase 6: CLOSE

모든 ACT 완료 및 VERIFY Phase 통과(사용자 확인 = CLOSE 진입 게이트) 후 태스크를 마감한다.

1. 전체 TS Green 확인 (STATE.md TS 현황)
2. 전체 ACT DONE.md 존재 확인
3. DONE.md 생성 후 CLOSE 행 mark:

```
~/.opal/tools/state-tool/run.sh mark <task-path> --row 24 --done  # DONE.md 생성 (CLOSE 완료)
```

> **CLOSE 게이트 제약 (§2.16 G-13)**: CLOSE 단계 최초 진입 행(#24)은 `--auto-pass` 적용 불가 (`close_gate_violation`). 반드시 위 명시 호출로 처리한다.

4. **관련 문서 업데이트** (op-brain-ingest 디스패치 직전 실행):
   - `<프로젝트-루트>/docs/PROJECT.md`의 "프로젝트 문서" 레지스트리와 이번 태스크의 `changed_files`(EXECUTE 산출)를 양쪽 종합하여, 태스크 결과로 내용이 달라진 관련 문서(ARCHITECTURE.md·SPEC·기획서 등)를 식별한다.
   - 갱신 대상이 있으면 PM이 판단하여 직접 수정하거나 적합한 워커를 디스패치해 최신화한다. 갱신 대상이 없으면 자연 스킵(no-op) — CLOSE를 중단시키지 않는다.
   - 목적: brain ingest 이전에 기획·설계 문서를 최신 상태로 만들어 ingest 품질을 보장한다.
5. **op-brain-ingest 디스패치** (DONE.md 생성 직후 실행):
   - `<프로젝트-루트>/.opal/brain/` 존재 여부를 확인한다.
   - **brain이 존재하면**: op-brain-ingest 워커를 디스패치하여 태스크 산출물(DONE.md·SPEC·SPEC-PLAN 결정·신규 엔티티)을 brain에 누적한다.
   - **brain이 없으면**: 자연 스킵(no-op). CLOSE가 막히지 않는다.
   - op-brain-ingest 탐색 경로:
     1. `{프로젝트}/.opal/skills/op-brain-ingest/SKILL.md`
     2. `~/.opal/skills/op-brain-ingest/SKILL.md`
   - 디스패치 입력: 태스크 폴더 경로
   - 워커가 `status: skipped` 또는 `status: completed` 또는 `status: completed_with_errors` 반환 — 어떤 경우도 CLOSE를 중단시키지 않는다.
6. 완료 보고

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
> state-tool이 이 파일의 "파이프라인 현황판" 테이블(24행)을 읽어 state.json을 초기화한다. 행 데이터를 직접 편집하지 않는다.
>
> **[R-10 비표준 행 구성]** opsdd는 24행 + ACT 동적 행 비표준 구조를 사용한다(State Gate 행 제거 후). `gate-pass`는 deprecated(014) — `mark` 개별 호출 필수.
>
> **[R-13 ACT 동적 행]** `--rows-acts` 옵션은 미구현. EXECUTE Phase 진입 후 `add-row`로 ACT 행을 수동 삽입한다 (EXECUTE ACT 실행 행 = #17):
> ```
> ~/.opal/tools/state-tool/run.sh add-row <task-path> --after 17 --stage EXECUTE --item 'ACT-001: {이름}'
> ```

**파이프라인 현황판** (`--rows-from` SSOT 표 — 이 표를 직접 편집하지 않는다):

> 상태값: ⬜ 대기 / 🔄 진행 중 / ✅ 완료 / ❌ 실패 / - 해당 없음
> **수행 원칙**: 위에서 아래로 순서대로 처리한다. 현재 행이 ✅가 아니면 다음 행으로 진행 불가.

| # | Phase | 항목 | 상태 | 시점 |
|---|-------|------|------|------|
| 1 | TASK | TASK.md 작성 | ⬜ | |
| 2 | TASK | STATE.md 생성 | ⬜ | |
| 3 | TASK | 사용자 확인 | ⬜ | |
| 4 | SPEC | 워커 디스패치 | ⬜ | |
| 5 | SPEC | SPEC.md 생성 | ⬜ | |
| 6 | SPEC | PM Gate | ⬜ | |
| 7 | SPEC | 사용자 확인 | ⬜ | |
| 8 | REVIEW | 구조 검증 (S-1~S-6) | ⬜ | |
| 9 | REVIEW | TEST-SCENARIOS.md 작성 | ⬜ | |
| 10 | REVIEW | FR↔TS 커버리지 확인 | ⬜ | |
| 11 | REVIEW | PM Gate | ⬜ | |
| 12 | REVIEW | 사용자 확인 | ⬜ | |
| 13 | DESIGN | 워커 디스패치 | ⬜ | |
| 14 | DESIGN | SPEC-PLAN.md 생성 | ⬜ | |
| 15 | DESIGN | PM Gate | ⬜ | |
| 16 | DESIGN | 사용자 확인 | ⬜ | |
| 17 | EXECUTE | ACT 실행 (상세: ACT 목록 참조) | ⬜ | |
| 18 | EXECUTE | PM Gate | ⬜ | |
| 19 | EXECUTE | 사용자 확인 | ⬜ | |
| 20 | VERIFY | E2E 테스트 수행 | ⬜ | |
| 21 | VERIFY | TS 전체 Green 확인 | ⬜ | |
| 22 | VERIFY | PM Gate | ⬜ | |
| 23 | VERIFY | 사용자 확인 | ⬜ | |
| 24 | CLOSE | DONE.md 생성 | ⬜ | |

### STATE.md 구조

STATE.md 전체 구조 예시 (파이프라인 현황판은 위 SSOT 표를 기준으로 state-tool이 생성):

```
STATE: {기능명} SDD 개발

최종 갱신: YYYY-MM-DD HH:mm

현재 상태
- 모드: SDD Task
- Phase: {현재 Phase (TASK/SPEC/REVIEW/DESIGN/EXECUTE-LOOP/VERIFY/CLOSE)}
- 상태: {진행 중 / 완료 / 블로커 / 추가작업중 / 추가작업완료}

파이프라인 현황판
(위 SSOT 표 기준으로 state-tool이 자동 생성 — 직접 편집 금지)

섹션 목록:
- ACT 목록 (EXECUTE Phase 상세 — DESIGN 완료 후 state-tool add-row로 동적 삽입)
- TS 현황 (VERIFY Phase 요약)
- SPEC 변경 이력
- 의사결정 로그
- 블로커
- 다음 액션
```

---

## PM Gate 점검 목록

| Phase | 산출물 | 체크리스트 위치 |
|-------|-------|----------------|
| SPEC | TASK.md, SPEC.md | TASK.md 요구사항 (QA Gate 없음 — PM 직접 검증) |
| DESIGN | SPEC-PLAN.md | SPEC.md FR↔ACT 분해 정합 |
| EXECUTE | actions/ACT-{N}/DONE.md | SPEC-PLAN.md ACT 완료 기준 |

---

## Agentic / Semi-Agentic 모드

opal-harness-agentic.md / opal-harness-semi-agentic.md 참조. 본 절은 이 스킬의 차이점만 기술한다.

### 기본 모드 (semi-agentic)

기본 호출(`//opsdd {기능 설명}`)은 semi-agentic 모드. DESIGN(Phase 3, PLAN-equivalent)까지 사용자 검토, EXECUTE-LOOP(Phase 4) 이후 PM 자율, CLOSE 진입은 사용자 승인 필수.

**모드 경계** (이 시점부터 PM 자율):
- Phase 3 DESIGN 사용자 Gate 통과 후 → Phase 4 EXECUTE-LOOP 첫 행부터 PM 자율 (D-DEC-2)
- WHAT 단계(SPEC/REVIEW)는 사용자 Gate 유지, DESIGN 작업 행도 사용자 검토 영역 포함

### 명시 모드

| 호출 | 모드 |
|------|------|
| `//opsdd 기능 설명` | semi-agentic (기본) |
| `//opsdd --interactive 기능 설명` | interactive — 모든 단계 사용자 승인 |
| `//opsdd --agentic 기능 설명` | agentic — 모든 단계 PM 자율 (CLOSE 진입 제외) |

### 활성화

STATE.md 모드 필드를 지정하여 기록한다 (기본: `semi-agentic`):

```
~/.opal/tools/state-tool/run.sh init <task-path> --skill opsdd --mode <interactive|semi-agentic|agentic> --rows-from opal/skills/opal-pilot-sdd/SKILL.md
```

### 자율 게이트 흐름 (semi-agentic)

```
TASK (사용자 승인)
  → SPEC Gate        -- 사용자 승인
  → REVIEW           -- 사용자 승인 (구조검증 + TS작성 + 커버리지)
  → DESIGN Gate      -- 사용자 승인 (모드 경계)
  → EXECUTE-LOOP     -- PM 자율 관리 (ACT별 Gate + L1/L2 검증 포함)
  → VERIFY           -- PM 직접 수행 (Playwright E2E + TS 전체 Green 확인 + 사용자 Gate = CLOSE 진입 게이트)
  → CLOSE            -- (사용자 승인 후) DONE.md 생성 + 최종 보고
```

### 자율 게이트 흐름 (agentic)

```
TASK (PM 직접)
  → SPEC Gate        -- PM 자율 검토
  → REVIEW           -- PM 직접 수행 (구조검증 + TS작성 + 커버리지)
  → DESIGN Gate      -- PM 자율 검토
  → EXECUTE-LOOP     -- PM 자율 관리 (ACT별 Gate + L1/L2 검증 포함)
  → VERIFY           -- PM 직접 수행 (Playwright E2E + TS 전체 Green 확인 + 사용자 Gate = CLOSE 진입 게이트)
  → CLOSE            -- (사용자 승인 후) DONE.md 생성 + 최종 보고
```

- agentic: 모든 Phase Gate를 PM이 자율 통과
- EXECUTE-LOOP 진입 = PM이 대행 승인 (구현 금지 원칙의 "실행 허가"를 PM이 판단)
- 자율 통과 시 state-tool `--auto-pass` 호출 (P-8):
  ```
  ~/.opal/tools/state-tool/run.sh mark <task-path> --row N --done --auto-pass --note '<근거>'
  ```
- **CLOSE 단계 최초 진입 행(#24)은 `--auto-pass` 금지** (`agentic_close_gate_requires_user` — §2.16 G-13); 반드시 명시 호출
- R-10 비표준 행 구성: `gate-pass` deprecated(014) — mark 개별 호출 필수 (agentic/semi-agentic에서도 동일 적용)
- AGENTIC-LOG.md에 모든 판단/오류/수정/의사결정 기록

### CLOSE 진입 게이트 (공통)

semi-agentic / agentic 모두 CLOSE 첫 행 `--auto-pass` 거부 (`agentic_close_gate_requires_user`). 소유자 발화 후 직전 사용자 확인 행 `--owner user` mark 필수.

### AGENTIC-LOG.md 생성 시점

- agentic: TASK 시작 시점
- semi-agentic: Phase 4 EXECUTE-LOOP 첫 행 advance 시점에 PM이 생성

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
| v3.2.0 | 2026-05-09 11:22 | 3-way 모드 체계 도입 — semi-agentic 기본 채택 + Agentic/Semi-Agentic 모드 절 확장 + Phase 3 DESIGN 모드 경계 명시(D-DEC-2) + AGENTIC-LOG 생성 시점 분기 + Harness 절 3-way 분기 + state init --mode choices 갱신 (140) |
| v3.3.0 | 2026-05-09 18:30 | 개인 식별자 "캡틴" → "소유자"/"사용자" 치환 — 배포 파일 정체성 누설 정정 (139) |
| v3.4.0 | 2026-06-07 | STATE 행 35→24 재구성 — State Gate 행 11개 제거(stage-transition guard로 이전)+CLOSE State Gate→DONE.md 생성 단일화. gate-pass 금지 문구를 deprecated(014)로 정합 갱신(mark 개별 호출 유지). 본문 Gate 흐름 "State Gate → PM Gate → State Gate → 사용자 Gate" → "PM Gate → 사용자 Gate" 정합화. 각 Phase mark 행번호 재정렬. R-13 add-row `--after 23`→`--after 17`. PM Gate 점검 목록 산출물을 실제 opsdd 산출물로 정정. ACT 폴더 반복·R-10 비표준 구조 보존 (014 Phase 4) |
| v3.4.1 | 2026-06-07 | `--rows-from` 파싱 수정 — STATE.md 구조 예시 인라인 마크다운 헤더(# STATE:, ## 현재 상태, ## 파이프라인 현황판)가 파서 섹션 경계 오인식 유발. SSOT 파이프라인 현황판 표를 `### STATE.md 구조` 앞으로 이동 + 구조 예시를 비-마크다운 헤더 형식으로 교체. `rows_count: 24` 파싱 정상 복구 (014 Phase 4) |
| v3.5.0 | 2026-06-11 19:25 | Phase 6 CLOSE에 op-brain-ingest 디스패치 훅 삽입 — DONE.md 생성 직후 brain 존재 시 워커 디스패치, 부재 시 no-op, CLOSE 비중단. STATE 행 24 불변 (016) |
| v3.5.1 | 2026-06-24 | Phase 6 CLOSE op-brain-ingest 디스패치 직전에 "관련 문서 업데이트" 스텝 삽입 — PROJECT.md 레지스트리 + changed_files 종합으로 관련 문서 최신화 후 ingest (없으면 no-op). 후속 항목 번호 재정렬 (042) |
