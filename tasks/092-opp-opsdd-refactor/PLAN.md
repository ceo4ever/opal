# PLAN: opsdd 스킬 리팩터링

> 작성일: 2026-04-07 | 태스크: 092-opp-opsdd-refactor
> 유형: 설계 검토 (구현 없음 — 개선 방향과 수정 범위 정의)

---

## 1. 현황 분석

### 문제 1: 폴더 혼재 — 두 폴더에 산출물 분산

**현재 구조**:

```
specs/{NNN}-{feature}/            <- SDD 세계 (SPEC, VERIFY, TASKS 등)
tasks/{NNN}-opsdd-{feature}/      <- OPAL 세계 (TASK.md, STATE.md, DONE.md)
```

**핵심 원인**: `op-task/SKILL.md`의 저장 경로 규칙(`tasks/{NNN}-{스킬약어}-{태스크명}/`)이 모든 오케스트레이터에 공통 적용된다. opsdd는 여기에 추가로 `specs/` 경로를 생성해 이원화가 발생한다.

### 문제 2: EXECUTE-LOOP pilot 미실행

**근본 원인**: opds/opd는 독립 오케스트레이터로 설계되어 서브 태스크로 재활용이 불가능하다.

1. opds/opd가 실행되면 내부적으로 하네스 §4 TASK 공통 프로세스를 따른다. `op-task/SKILL.md`가 `tasks/{NNN}-{스킬약어}-{태스크명}/TASK.md`를 **고정 경로**로 생성한다.
2. 디스패치 프롬프트에 `task_folder`를 주입해도 op-task는 이 파라미터를 읽어 오버라이드하는 메커니즘이 없다. 자체 채번해서 `tasks/`에 새 폴더를 만든다.
3. 결과적으로 opds가 상위 opsdd 컨텍스트(SPEC.md 등)를 모른 채 독립 태스크로 분리되거나 실행 자체가 꼬인다.

### 문제 3: Verify 과다 + 토큰 낭비

현재 7단계 파이프라인에서 Gate 수 15+, 워커 디스패치 중복 발생:

- SPEC-VERIFY: 전용 워커 디스패치 + QA Gate + PM Gate + 사용자 Gate
- TASKS-VERIFY: 전용 워커 디스패치 + QA Gate + PM Gate + 사용자 Gate
- DONE: 전체 재검증 + QA Gate

---

## 2. 개념 재정의

| 개념 | 정의 |
|------|------|
| **SDD Task** | 하나의 기능을 SDD 방법론으로 개발하는 단위. SPEC.md가 SSOT |
| **Action** | Task를 구현하는 최소 실행 단위. 독립적으로 PLAN→EXECUTE→TEST→DONE |
| **WHAT** | SPEC.md + TEST-SCENARIOS.md — 무엇을 만들지 확정 |
| **HOW** | SPEC-PLAN.md + actions/ — 어떻게 만들지 설계 + 실행 |

---

## 3. 신규 폴더/문서 구조

```
tasks/
    {NNN}-{feature}/
        TASK.md              # 관리 메타데이터만 (번호, 날짜, 상태, 링크)
        SPEC.md              # 기능 명세 SSOT — FR/NFR/제약조건
        TEST-SCENARIOS.md    # SPEC 기반 테스트 기준 + ACT별 TS 매핑
        SPEC-PLAN.md         # 아키텍처 설계 + ACT 분해 + 병렬/순서 의존관계
        STATE.md             # 전체 진행 상태 (Phase + ACT 목록 상태 통합 관리)
        DONE.md              # 최종 완료 확인
        actions/
            ACT-001-{name}/
                PLAN.md      # 구현 계획 (op-dev-plan 산출물)
                TEST.md      # 해당 TS 실행 결과 (op-dev-qa 산출물)
                DONE.md      # ACT 완료 확인 (PM 작성)
            ACT-002-{name}/
                ...
```

**변경 포인트**:
- `specs/` 폴더 제거 → `tasks/` 단일 루트로 통합
- `TASK.md` 경량화 — 내용 SSOT는 `SPEC.md`
- `tasks/` 하위 서브폴더 → `actions/` 하위 ACT 구조로 재정의
- `TASKS.md` + `SPEC-PLAN.md(구)` → `SPEC-PLAN.md`로 통합 (아키텍처 + ACT 분해)
- ACT 내부 `STATE.md` 제거 — 상위 `STATE.md`가 전체 ACT 상태 통합 관리
- ACT 병렬/순서 의존관계는 `SPEC-PLAN.md`에서 정의

---

## 4. 신규 파이프라인

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
Phase 4: EXECUTE   ACT 루프   각 ACT 자율 실행
                              op-dev-plan → PM Gate
                              → op-dev-execute → TEST.md → DONE.md
Phase 5: DONE      PM 직접    전체 ACT DONE + 전체 TS Green 확인
                              → 사용자 Gate
```

**현재 대비 개선**:

| 항목 | 현재 | 개선 후 |
|------|------|---------|
| 단계 수 | 7단계 | 5단계 |
| Gate 수 | 15+ | 약 7~8개 |
| SPEC 검증 | 워커 디스패치 + 3 Gate | PM 직접 (0 Gate 추가) |
| TASKS-VERIFY | 워커 디스패치 + 3 Gate | 제거 (DESIGN PM Gate 흡수) |
| EXECUTE-LOOP | opds/opd 위임 (미작동) | op-dev-plan + op-dev-execute 직접 |

---

## 5. REVIEW Phase 상세 — SPEC 검증 방식

TEST-SCENARIOS.md를 작성하는 행위 자체가 SPEC 검증의 실천적 형태다.

- FR이 모호하면 TS를 못 씀 → 즉시 발견
- 경계조건 정의 과정에서 누락 케이스 드러남
- FR 간 모순이 있으면 TS가 충돌 → 즉시 발견

**REVIEW Phase 흐름**:

```
1. 구조 검증 (PM 직접, 빠르게)
   op-sdd-verify 참조 — S-1~S-6 항목 체크
   (섹션 존재, 형식, ID 체계 등 규칙 기반)

2. TEST-SCENARIOS.md 작성 (PM 직접)
   SPEC.md의 각 FR → TS 도출
   이 과정에서 의미적/도메인 검증(M-1~M-6, D-1~D-2) 자연스럽게 수행

3. FR↔TS 커버리지 확인 (PM 직접)
   커버 안 된 FR → SPEC.md 보완 후 재작성
```

**op-sdd-verify 역할 변경**:
- 현재: 워커 스킬 (서브에이전트로 디스패치)
- 변경: PM 레퍼런스 (직접 읽는 체크리스트 가이드, 디스패치 없음)

---

## 6. 서브에이전트 역할 매핑

### Phase별 주체

| 단계 | 주체 | 스킬 |
|------|------|------|
| SPEC.md 작성 | 워커 | `op-sdd-spec` |
| 구조 검증 | PM 직접 | `op-sdd-verify` 참조 |
| TEST-SCENARIOS.md 작성 | PM 직접 | — |
| SPEC-PLAN.md 작성 | 워커 | `op-sdd-plan` (op-sdd-tasks 통합) |
| ACT 실행 루프 | PM 오케스트레이션 | — |
| 모든 Gate 판단 | PM 직접 | — |

### ACT 실행 에이전트 구조

```
PM
 ├── 에이전트 A (op-dev-plan → op-dev-execute) ──► PLAN.md + 구현
 ├── 에이전트 B (op-dev-qa)                    ──► TEST.md
 └── PM 직접                                   ──► DONE.md
```

- **에이전트 A**: op-dev-plan으로 PLAN.md 작성 후, op-dev-execute로 구현. 같은 디스패치 세션에서 순차 실행.
- **에이전트 B**: op-dev-qa가 TEST-SCENARIOS.md의 해당 TS 기준으로 TEST.md 작성. 에이전트 A와 독립 세션 — 객관적 검증.
- **PM**: TEST.md 확인 후 DONE.md 작성.

### ACT 재시도 루프

TEST 실패 또는 PM 재테스트 요청 시:

```
        ┌──────────────────────────────────────┐
        ↓                                      │ FAIL / 재수정 요청
PM → 에이전트 A' (op-dev-execute만, PLAN.md 재사용)
PM → 에이전트 B  (op-dev-qa 재디스패치) ── TEST.md
        │ PASS
        ↓
PM → DONE.md 확정
```

- 재시도 시 op-dev-plan 불필요 (PLAN.md 이미 존재)
- op-dev-execute에 수정 지시 + 실패한 TS 정보 주입
- PM이 루프 횟수를 관리 (무한 루프 방지)
- 각 디스패치는 독립 세션 — PM이 매 호출마다 컨텍스트(SPEC.md, SPEC-PLAN.md, TEST.md) 주입

**PM이 직접 하는 것**: TASK 정의 / SPEC-REVIEW / Gate 판단 / DONE 확인 / 루프 관리
**워커가 하는 것**: SPEC 작성 / SPEC-PLAN 작성 / ACT PLAN+EXECUTE / ACT TEST

---

## 7. 수정 파일 목록

| # | 파일 | 변경 유형 | 변경 내용 |
|---|------|----------|---------|
| 1 | `opal/skills/opal-pilot-sdd/SKILL.md` | **대폭 수정** | 7→5단계, 폴더 구조 단일화, EXECUTE-LOOP 재작성, SPEC-VERIFY 제거, TASKS-VERIFY 제거 |
| 2 | `opal/skills/opal-pilot-sdd/references/execute-loop-guide.md` | **대폭 수정** | opds/opd → op-dev-plan + op-dev-execute 직접 호출로 전환, ACT 구조 반영 |
| 3 | `opal/skills/opal-pilot-sdd/references/verify-guide.md` | **대폭 수정** | REVIEW Phase PM 직접 검증 가이드로 전환, TASKS-VERIFY 제거 |
| 4 | `opal/skills/op-sdd-verify/SKILL.md` | **변경 없음** | PM이 직접 읽고 체크리스트로 활용. 파일 수정 불필요. opsdd 오케스트레이터에서 디스패치 지시만 제거. |
| 5 | `opal/skills/op-sdd-plan/SKILL.md` | **수정** | op-sdd-tasks 통합 — SPEC-PLAN.md에 ACT 분해까지 포함, 출력 경로 수정 |
| 6 | `opal/skills/op-sdd-tasks/SKILL.md` | **삭제** | op-sdd-plan에 통합 |
| 7 | `opal/skills/op-sdd-spec/SKILL.md` | 소폭 수정 | 출력 경로 tasks/ 기준으로 수정 |
| 8 | `opal/skills/op-task/SKILL.md` | 소폭 수정 | base_path 오버라이드 메커니즘 추가 (opsdd가 tasks/ 경로 직접 지정) |
| 9 | `opal/core/references/opal-harness.md` | 소폭 수정 | §4 TASK 공통 프로세스에 base_path 오버라이드 규칙 추가 |

---

## 8. 구현 체크리스트 (다음 태스크용)

### Step 1: 폴더 구조 통합

- [ ] `op-task/SKILL.md` — base_path 오버라이드 메커니즘 추가
- [ ] `opal-harness.md` §4 — base_path 오버라이드 참조 추가
- [ ] `opal-pilot-sdd/SKILL.md` — 폴더 구조 섹션 신규 구조로 교체
- [ ] `opal-pilot-sdd/SKILL.md` — Phase 0(TASK)에서 base_path=`tasks/{NNN}-{feature}/` 지정

### Step 2: EXECUTE-LOOP 재작성

- [ ] `opal-pilot-sdd/SKILL.md` Phase 4 — opds/opd → op-dev-plan + op-dev-execute 직접 디스패치
- [ ] `opal-pilot-sdd/SKILL.md` Phase 4 — actions/ 구조 반영 (ACT-{NNN}-{name}/)
- [ ] `opal-pilot-sdd/SKILL.md` Phase 4 — ACT 에이전트가 구현 + 테스트 통합 수행 (op-dev-qa 별도 디스패치 제거)
- [ ] `opal-pilot-sdd/SKILL.md` Phase 4 — ACT 재시도 루프 정의 (PM이 관리, op-dev-execute만 재디스패치)
- [ ] `opal-pilot-sdd/SKILL.md` Phase 4 — ACT STATE.md 제거 반영 (상위 STATE.md가 ACT 목록 통합 관리)
- [ ] `execute-loop-guide.md` — 전체 재작성 (ACT 루프 구조, 디스패치 프롬프트 템플릿, 재시도 패턴)

### Step 3: REVIEW Phase + Verify 간소화

- [ ] `opal-pilot-sdd/SKILL.md` Phase 2 → REVIEW (PM 직접) 로 전환
- [ ] `opal-pilot-sdd/SKILL.md` SPEC-VERIFY / TASKS-VERIFY Phase 제거
- [ ] `op-sdd-verify/SKILL.md` — 수정 없음 (PM이 직접 읽고 체크리스트로 활용)
- [ ] `verify-guide.md` — REVIEW Phase PM 직접 검증 가이드로 재작성

### Step 4: 단계 스킬 수정

- [ ] `op-sdd-plan/SKILL.md` — op-sdd-tasks 통합, SPEC-PLAN.md에 ACT 분해 + 병렬/순서 의존관계 포함
- [ ] `op-sdd-tasks/SKILL.md` — 삭제
- [ ] `op-sdd-spec/SKILL.md` — 출력 경로 수정

### Step 5: 검증

- [ ] 신규 5단계 파이프라인 실제 opsdd 호출 테스트
- [ ] 폴더가 tasks/ 단일 루트로 생성되는지 확인
- [ ] EXECUTE-LOOP에서 ACT 에이전트가 actions/ACT-{N}/ 경로에서 구현 + 테스트 통합 수행하는지 확인
- [ ] ACT 재시도 루프 (FAIL → op-dev-execute 재디스패치 → 재테스트) 정상 동작 확인
- [ ] 상위 STATE.md가 ACT 목록 상태를 정확히 반영하는지 확인

---

## 9. 미결 사항

| # | 항목 | 내용 | 권장 |
|---|------|------|------|
| 1 | 비코드 ACT 처리 | 문서/설정 작업 ACT에서 op-dev-plan/op-dev-execute 그대로 쓸지 | 그대로 사용 (범용화) |
| 2 | ACT 병렬 실행 | worktree 격리 패턴을 ACT 단위에도 적용할지 | 유지 |

---

## 10. QA 체크리스트

- [ ] 모든 산출물이 tasks/ 단일 루트에 생성되는지 확인
- [ ] TASK.md 경량화 후 SPEC.md와 역할 중복 없는지 확인
- [ ] SPEC-PLAN.md가 아키텍처 + ACT 분해를 모두 커버하는지 확인
- [ ] TEST-SCENARIOS.md 작성이 SPEC 검증을 실질적으로 대체하는지 확인
- [ ] REVIEW Phase 흐름 (구조검증 → TS작성 → 커버리지확인) 완결성 확인
- [ ] op-sdd-verify 레퍼런스 전환 후 PM이 체크리스트로 활용 가능한지 확인
- [ ] op-dev-plan + op-dev-execute가 TASK 단계 없이 actions/ 경로에서 정상 동작하는지 확인
- [ ] 5단계 파이프라인의 단계 전이(STATE.md)가 정확히 반영되는지 확인
- [ ] agentic 모드에서도 신규 파이프라인 정상 동작하는지 확인
