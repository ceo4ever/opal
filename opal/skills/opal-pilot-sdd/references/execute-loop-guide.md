# EXECUTE-LOOP 상세 가이드

> opal-pilot-sdd Phase 4: EXECUTE-LOOP의 상세 운영 지침.
> 오케스트레이터(opsdd)가 ACT 단위 반복 실행을 관리할 때 참조한다.
> SKILL.md에서 분리된 상세 내용.

---

## 1. 개요

EXECUTE-LOOP는 SPEC-PLAN.md에 정의된 ACT를 의존 순서에 따라 반복 실행하는 단계다. PM이 루프를 관리하며 각 ACT는 `opal-sdd-action-agent`에 단일 디스패치한다. 에이전트가 ACT 폴더 생성 → PLAN → EXECUTE → VERIFY 루프를 자율 완주한다.

**핵심 원칙**:
- opds/opd 위임 없음 — opal-sdd-action-agent에 단일 디스패치
- 에이전트 내부에서 op-sdd-action-plan + op-dev-execute + VERIFY 루프를 순차 수행
- SPEC-PLAN.md의 의존관계 그래프가 ACT 실행 순서를 결정
- SDD 컨텍스트(SPEC.md, SPEC-PLAN.md, TEST-SCENARIOS.md, AC/TS 매핑)를 디스패치 시 주입
- 재시도 루프: PM 관리, opal-sdd-action-agent 재디스패치

**자동 루핑 제약** (하네스 §1 연동):

| 실패 유형 | 최대 재시도 | 초과 시 동작 |
|----------|-----------|------------|
| lint/format | 제한 없음 (즉시 수정) | — |
| build/type | 2회 | PM이 소유자 에스컬레이션 |
| unit/integration test | 3회 | PM이 소유자 에스컬레이션 |
| E2E test | 1회 | PM이 소유자 에스컬레이션 |
| QA 설계/아키텍처 | 0회 | 즉시 소유자 에스컬레이션 |

---

## 2. ACT별 실행 흐름

```
SPEC-PLAN.md에서 실행 그룹 확인
  → for each Group in execution_order(SPEC-PLAN.md):
      → if Group has single ACT:
          순차 실행 (섹션 3)
      → if Group has multiple independent ACTs:
          병렬 실행 (섹션 4) + worktree 격리
      → Group 완료 후 STATE.md 갱신
      → 다음 Group 진행
```

### 2-1. 단일 ACT 실행 순서

1. **사용자 Gate**: ACT 시작 전 승인 (interactive 모드)
2. **opal-sdd-action-agent 디스패치**: ACT 폴더 생성 + PLAN + EXECUTE + VERIFY 자율 완주 (섹션 5-1 프롬프트 사용)
3. **결과 수신**: status 확인
4. **Pass/Fail 판정**:
   - Pass → DONE.md 작성 → STATE.md 갱신
   - Fail → 재시도 루프 (섹션 6) 또는 에스컬레이션

---

## 3. ACT 폴더 구조

각 ACT는 고유 폴더에서 실행된다.

```
tasks/{NNN}-{feature}/
├── actions/
│   ├── ACT-001-{name}/
│   │   ├── PLAN.md      ← op-dev-plan 산출물
│   │   ├── TEST.md      ← op-dev-execute 산출물 (TS 실행 결과)
│   │   └── DONE.md      ← PM 작성 (ACT 완료 확인)
│   ├── ACT-002-{name}/
│   │   └── ...
│   └── ACT-003-{name}/
│       └── ...
```

**ACT 폴더 네이밍**: `ACT-{NNN}-{name}` (NNN: 3자리 zero-padded, name: kebab-case)

---

## 4. 병렬 실행 패턴

### 4-1. 의존관계 그래프에서 병렬 그룹 빌드

SPEC-PLAN.md의 `실행 그룹` 섹션 또는 `의존관계 그래프`에서 병렬 그룹을 도출한다.

```
groups = buildParallelGroups(SPEC-PLAN.md["8. ACT 분해"]["실행 그룹"])

for each group in groups:
  if group has single ACT:
    → 순차 실행 (일반 디스패치)
  if group has multiple independent ACTs:
    → worktree 격리 + 병렬 워커 디스패치
    → 결과 수집 → 순차 머지 → 통합 테스트
    → worktree 정리
```

### 4-2. worktree 격리

각 병렬 ACT는 독립된 git worktree에서 실행한다.

**디렉토리 구조**:
```
{프로젝트 루트}/
├── .worktrees/
│   ├── {NNN}-ACT-001/    ← ACT-001 전용 worktree
│   └── {NNN}-ACT-002/    ← ACT-002 전용 worktree
└── tasks/
    └── {NNN}-{feature}/
        └── actions/
            ├── ACT-001-{name}/
            └── ACT-002-{name}/
```

**브랜치 네이밍**: `feat/opsdd-{NNN}-ACT-{NNN}` (예: `feat/opsdd-001-ACT-002`)

**worktree 생성**:
```bash
mkdir -p .worktrees
git worktree add .worktrees/{NNN}-ACT-001 -b feat/opsdd-{NNN}-ACT-001
```

**worktree 정리** (머지 완료 후):
```bash
git worktree remove .worktrees/{NNN}-ACT-001
git branch -d feat/opsdd-{NNN}-ACT-001
```

### 4-3. 병렬 디스패치

병렬 그룹의 모든 ACT에 대해 Agent 도구를 동일 응답 내에서 병렬 호출한다.

각 워커에게 worktree 경로를 명시:
```
**작업 디렉토리**: {프로젝트 루트}/.worktrees/{NNN}-ACT-{NNN}/
**브랜치**: feat/opsdd-{NNN}-ACT-{NNN}
**제약**: 이 worktree 내에서만 파일을 수정하라.
```

### 4-4. 결과 수집과 머지

1. 모든 병렬 워커 완료 대기
2. 변경 범위가 작은 순서대로 main 브랜치에 순차 머지
3. 각 머지 후 즉시 검증 (lint → build → test)
4. 머지 충돌 발생 시 PM이 조정
5. 모든 머지 완료 후 통합 테스트

### 4-5. Fallback

| 환경 | 전략 |
|------|------|
| Agent 도구 + worktree 지원 | 완전 병렬 실행 |
| Agent 도구 없음 + worktree 지원 | worktree 격리 + 순차 디스패치 |
| 둘 다 미지원 | 순차 실행 (메인 브랜치에서 직접) |

---

## 5. 디스패치 프롬프트 템플릿

### 5-1. opal-sdd-action-agent 디스패치

```
[WORKER] opal-sdd-action-agent를 실행하라.

**에이전트 경로**: {opal/agents/opal-sdd-action-agent/AGENT.md 탐색 경로}

**입력 명세**:
- **act_id**: ACT-{NNN}-{name}
- **act_goal**: {SPEC-PLAN.md "8. ACT 분해"에서 해당 ACT의 목표}
- **act_scope**: {해당 ACT의 변경 대상 파일/모듈}
- **ac_mapping**: {해당 ACT의 AC 목록 — 예: AC-01, AC-03}
- **ts_mapping**: {해당 ACT의 TS 목록 — 예: TS-01, TS-02, TS-04}
- **verify_commands**: {lint/build/test 명령어}
- **task_folder**: tasks/{NNN}-{feature}/
- **sdd_context**:
  - SPEC.md: tasks/{NNN}-{feature}/SPEC.md
  - SPEC-PLAN.md: tasks/{NNN}-{feature}/SPEC-PLAN.md
  - TEST-SCENARIOS.md: tasks/{NNN}-{feature}/TEST-SCENARIOS.md
```

### 5-2. opal-sdd-action-agent 재디스패치 (재시도)

재시도 시 이전 실패 컨텍스트를 추가 주입한다.

```
[WORKER] opal-sdd-action-agent를 실행하라. (재시도 {N}차)

**에이전트 경로**: {opal/agents/opal-sdd-action-agent/AGENT.md 탐색 경로}

**입력 명세**:
- **act_id**: ACT-{NNN}-{name}
- **act_goal**: {해당 ACT의 목표}
- **act_scope**: {해당 ACT의 변경 대상 파일/모듈}
- **ac_mapping**: {해당 ACT의 AC 목록}
- **ts_mapping**: {해당 ACT의 TS 목록}
- **verify_commands**: {lint/build/test 명령어}
- **task_folder**: tasks/{NNN}-{feature}/
- **sdd_context**:
  - SPEC.md: tasks/{NNN}-{feature}/SPEC.md
  - SPEC-PLAN.md: tasks/{NNN}-{feature}/SPEC-PLAN.md
  - TEST-SCENARIOS.md: tasks/{NNN}-{feature}/TEST-SCENARIOS.md

**재시도 컨텍스트**:
- **실패한 계층**: {L2 / L3a / L3b}
- **실패한 TS**: {TS-01, TS-02 — 실패 사유}
- **이전 verification_log**: {직전 에이전트 반환 로그}
- **수정 지시**: {구체적 수정 방향}
```

---

## 6. 재시도 루프

에이전트 `status: failed` 반환 시 PM이 재디스패치한다:

```
        ┌──────────────────────────────────────────────────┐
        ↓                                                  │ status: failed
PM → opal-sdd-action-agent 재디스패치 (재시도 컨텍스트 주입)
PM → 결과 수신 (status 확인)
        │ status: completed
        ↓
PM → DONE.md 작성
```

**재시도 규칙**:
- 에이전트 내부 VERIFY 루프 한도 초과 시 PM 레벨 재디스패치로 전환
- 재디스패치 시 실패 계층, 실패 TS, 수정 지시를 주입한다 (섹션 5-2 프롬프트)
- 하네스 §1 자동 루핑 제약 테이블 준수 (unit/integration 최대 3회)
- 최대 재시도 초과 시 PM이 소유자 에스컬레이션

---

## 7. TEST.md 구조

op-dev-execute 워커가 ACT 폴더에 작성하는 테스트 결과 문서.

```markdown
# TEST: ACT-{NNN} {ACT명}

> 작성일: YYYY-MM-DD | SPEC-PLAN.md v{X.Y} 기준

## TS 실행 결과

| TS ID | 설명 | 유형 | 결과 | 비고 |
|-------|------|------|------|------|
| TS-01 | {시나리오명} | unit | Green / Fail | {실패 시 오류 요약} |
| TS-02 | {시나리오명} | integration | Green / Fail | |

## 실행 환경

- 실행 도구: {Jest / Pytest / 등}
- 실행 명령: `{테스트 명령}`

## 실패 상세 (Fail 시)

### TS-{N} 실패

```
{오류 메시지 + 스택 트레이스}
```

- **원인 분석**: {실패 원인}
- **수정 필요**: {수정 방향}

## 종합 판정

- 총 TS: {N}개
- Green: {N}개 / Fail: {N}개
- **판정**: Pass / Fail
```

---

## 8. DONE.md 구조

PM이 ACT 완료 확인 시 작성하는 문서.

```markdown
# DONE: ACT-{NNN} {ACT명}

> 완료일: YYYY-MM-DD

## 완료 확인

- TS 상태: 모두 Green ({N}개)
- 구현 파일: {변경된 파일 목록}
- 재시도 횟수: {N}회 (0회 = 첫 시도 통과)

## 비고

{특이 사항 또는 다음 ACT 주의 사항}
```

---

## 9. STATE.md ACT 상태 관리

상위 STATE.md가 전체 ACT 목록의 상태를 통합 관리한다 (ACT 내부 STATE.md 없음).

### 9-1. ACT 상태 필드

| 상태 | 의미 |
|------|------|
| ⬜ 대기 | 아직 시작 안 함 |
| 🔄 진행 중 | EXECUTE-LOOP에서 실행 중 |
| ✅ 완료 | 모든 TS Green + DONE.md 작성 |
| ❌ 실패 | 최대 재시도 초과 — 에스컬레이션 필요 |

### 9-2. STATE.md EXECUTE-LOOP 섹션 구조

```markdown
## EXECUTE-LOOP 현황

- Phase: EXECUTE-LOOP
- 진행: ACT {현재}/{총 수}
- 상태: 진행 중

### ACT 목록

| ACT | 이름 | 그룹 | 상태 | 완료일 |
|-----|------|------|------|--------|
| ACT-001 | {name} | Group 1 | ✅ 완료 | YYYY-MM-DD |
| ACT-002 | {name} | Group 2 | 🔄 진행 중 | — |
| ACT-003 | {name} | Group 2 | ⬜ 대기 | — |
| ACT-004 | {name} | Group 3 | ⬜ 대기 | — |

### TS 상태

| TS ID | 담당 ACT | 상태 |
|-------|---------|------|
| TS-01 | ACT-001 | Green |
| TS-02 | ACT-001 | Green |
| TS-03 | ACT-002 | Red |
```

### 9-3. 갱신 시점

| 이벤트 | 갱신 내용 |
|--------|----------|
| ACT 시작 | ACT 상태 ⬜ → 🔄 |
| ACT TEST.md 확인 (Pass) | ACT 상태 🔄 → ✅, TS 상태 → Green |
| ACT TEST.md 확인 (Fail) | ACT 상태 유지 🔄, TS 상태 → Fail, 재시도 루프 진입 |
| 최대 재시도 초과 | ACT 상태 🔄 → ❌, 에스컬레이션 |
| DONE.md 작성 | 완료일 기록 |

---

## 10. 전체 흐름 예시

### 시나리오

tasks/001-user-auth/의 SPEC-PLAN.md에 4개 ACT:

```
ACT-001: 데이터 모델 (의존: 없음)
ACT-002: 인증 API (의존: ACT-001)
ACT-003: 세션 관리 (의존: ACT-001)
ACT-004: 통합 테스트 (의존: ACT-002, ACT-003)

실행 그룹:
Group 1 (순차): ACT-001
Group 2 (병렬): ACT-002, ACT-003  ← ACT-001 완료 후
Group 3 (순차): ACT-004            ← ACT-002, ACT-003 완료 후
```

### 실행 순서

```
Group 1 (순차): ACT-001
  → 사용자 Gate (ACT-001 시작 승인)
  → opal-sdd-action-agent 디스패치 (자율 완주: PLAN → EXECUTE → VERIFY)
  → status: completed → DONE.md 작성 → STATE.md 갱신 (ACT-001 ✅)

Group 2 (병렬): ACT-002, ACT-003  ← ACT-001 완료 후
  → worktree 생성: .worktrees/001-ACT-002/, .worktrees/001-ACT-003/
  → 병렬 디스패치 (동일 응답 내):
      ACT-002: opal-sdd-action-agent (worktree: .worktrees/001-ACT-002/)
      ACT-003: opal-sdd-action-agent (worktree: .worktrees/001-ACT-003/)
  → 결과 수집 → 순차 머지 → 통합 테스트
  → DONE.md 작성 x2 → STATE.md 갱신 (ACT-002/003 ✅)

Group 3 (순차): ACT-004  ← ACT-002, ACT-003 완료 후
  → 사용자 Gate (ACT-004 시작 승인)
  → opal-sdd-action-agent 디스패치
  → status: failed (L3a TS-05 3회 초과) → PM 레벨 재시도 루프
    → opal-sdd-action-agent 재디스패치 (1차, 수정 지시 주입) → status: completed
  → DONE.md 작성 → STATE.md 갱신 (ACT-004 ✅)
  → 전체 TS Green 확인 → EXECUTE-LOOP 완료
```

---

## 관련 문서

- `opal-pilot-sdd/SKILL.md` — opsdd 오케스트레이터 메인 (Phase 4: EXECUTE-LOOP 개요)
- `verify-guide.md` — REVIEW Phase PM 직접 검증 가이드
- `spec-guide.md` — SPEC.md 구조 참조
- `spec-plan-guide.md` — SPEC-PLAN.md 구조 (ACT 분해 섹션 포함)
- `~/.opal/references/opal-harness.md` — §1 자동 루핑 제약 (재시도 한도 기준)
