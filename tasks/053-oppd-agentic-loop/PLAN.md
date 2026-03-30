# PLAN: oppd Phase 3 agentic 자율 루핑 + 병렬 실행 설계

> 작성일: 2026-03-30
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `~/.opal/skills/opal-pilot-project-dev/SKILL.md` | oppd 오케스트레이터 (Phase 1~3 파이프라인) | O — Phase 2 세분화 원칙, Phase 3 자동 루핑 + 병렬 실행 추가 |
| `~/.opal/skills/opal-pilot-project-dev/references/roadmap-guide.md` | 로드맵 수립 가이드 (태스크 분할 원칙, 구조) | O — 자동 테스트 가능성 기준, 의존성 그래프 강화 |
| `~/.opal/skills/opal-pilot-dev/SKILL.md` | opd Full Task 오케스트레이터 | X — 내부 QA Gate 유지, oppd 레벨 변경만 |
| `~/.opal/skills/opal-pilot-dev-short/SKILL.md` | opds Short Task 오케스트레이터 | X — 동일 |
| `~/.opal/references/opal-harness.md` | 하네스 공통 인프라 (Guards, Gates, State) | O — 병렬 실행 관련 State 확장 |
| `~/.opal/agents/opal-task-agent/AGENT.md` | 범용 워커 에이전트 | X — 기존 구조 유지 |
| `~/.opal/agents/opal-task-qa-agent/AGENT.md` | QA 워커 에이전트 | X — 기존 구조 유지 |
| `~/.opal/agents/op-dev-test-agent/AGENT.md` | Test 워커 에이전트 | X — 기존 구조 유지 |

### 현재 상태

**oppd Phase 2 (로드맵 수립)**:
- 태스크 분할 원칙: 독립 실행 가능 단위, 의존성 방향(하위→상위), 1~3일 분량, 스킬 판단
- roadmap-guide.md: 이미 "병렬 가능한 태스크를 식별한다" 원칙이 있고, 실행 컬럼에 `▶ 병렬 X` 그룹 표기 존재
- **부재**: "자동 테스트 가능성" 기준 없음. 각 태스크에 lint/build/test로 검증 가능한 완료 기준이 명시되지 않음

**oppd Phase 3 (태스크 실행)**:
- 현재: 순차 실행만 (`for each 태스크 in ROADMAP`)
- opd/opds 내부에 QA Gate 존재: 워커 완료 → QA 에이전트 → PM Gate → 사용자 보고
- op-dev-test-agent: TEST-SCENARIO.md 기반 동적 검증, 판정(All Pass / Partial Fail / Critical Fail)
- **부재**: 자동 재시도 루프 없음. 테스트 실패 시 사용자가 직접 판단. 병렬 실행 메커니즘 없음

**하네스 (opal-harness.md)**:
- Guards: 구현 금지 원칙, Git 사전 점검, 디스패치 의무 원칙, 커밋 규칙
- Gates: 단계 게이트(사용자 승인), QA Gate, PM Gate, 체크리스트 검증 게이트
- State: STATE.md 공통 템플릿, 세션 복원
- **부재**: 병렬 실행 시 STATE.md 동시 갱신 전략 없음. 자동 루핑 관련 규칙 없음

**Agent 도구 활용**:
- opal-task-agent: 서브에이전트로 디스패치 가능 (Agent 도구)
- 현재 oppd에서는 순차 디스패치만 수행
- Agent 도구로 여러 서브에이전트를 병렬 디스패치할 수 있는 플랫폼 기능 존재

### 영향 범위

| 영향 대상 | 영향 내용 |
|----------|----------|
| oppd SKILL.md | Phase 2 세분화 원칙 추가, Phase 3 루프 + 병렬 로직 대폭 변경 |
| roadmap-guide.md | 태스크 분할 기준 강화, 완료 기준 템플릿 추가 |
| opal-harness.md | 병렬 실행 State 확장, 자동 루핑 Guards 추가 |
| opd/opds SKILL.md | **변경 없음** — 내부 QA Gate 유지, oppd 상위 레벨에서 루핑 |
| 워커/QA/Test 에이전트 | **변경 없음** — 기존 인터페이스 그대로 활용 |

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| 1 | `~/.opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` | 자동 검증 루핑 전략 상세 가이드 |
| 2 | `~/.opal/skills/opal-pilot-project-dev/references/parallel-execution-guide.md` | 병렬 실행 전략 상세 가이드 |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 3 | `~/.opal/references/opal-harness.md` | 병렬 실행 State 확장 + 자동 루핑 Guards 추가 |
| 4 | `~/.opal/skills/opal-pilot-project-dev/references/roadmap-guide.md` | 태스크 분할 기준 강화 (자동 테스트 가능성, 완료 기준 템플릿, 의존성 그래프) |
| 5 | `~/.opal/skills/opal-pilot-project-dev/SKILL.md` | Phase 2 세분화 원칙 반영 + Phase 3 자동 루핑/병렬 실행 반영 |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| (없음) | | |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | 하네스 확장 (병렬 State + 루핑 Guards) | opal-harness.md | 중 |
| 2 | 자동 검증 루핑 가이드 신규 작성 | verification-loop-guide.md | 중 |
| 3 | 병렬 실행 가이드 신규 작성 | parallel-execution-guide.md | 중 |
| 4 | 로드맵 가이드 강화 | roadmap-guide.md | 중 |
| 5 | oppd SKILL.md Phase 2 + Phase 3 반영 | SKILL.md | 상 |

### 핵심 설계

#### Step 1: opal-harness.md 확장

**Guards 추가 — 자동 루핑 제약**:
```markdown
### 자동 루핑 제약 (Verification Loop Guards)

자동 검증 루핑은 무한 루프를 방지하기 위해 다음 제약을 준수한다:

| 실패 유형 | 최대 재시도 | 초과 시 동작 |
|----------|-----------|------------|
| lint/format | 제한 없음 (즉시 수정) | - |
| build/type | 2회 | 사용자 에스컬레이션 |
| test | 3회 | 사용자 에스컬레이션 |
| QA 설계/아키텍처 | 0회 | 즉시 사용자 에스컬레이션 |

- 회귀 방지: 자동 수정 후 이전 통과 테스트를 재실행한다. 회귀 발생 시 루프 즉시 중단 + 에스컬레이션
- 사용자 게이트 유지: 루핑은 agentic이지만 최종 확정은 반드시 사용자를 거친다
```

**State 확장 — 병렬 실행 지원**:

> 하네스 `3. State` 섹션의 "STATE.md 공통 템플릿" 아래에 새 하위 섹션으로 추가한다.

```markdown
### 병렬 실행 State

oppd Phase 3에서 병렬 태스크 실행 시 STATE.md를 다음과 같이 확장한다:

## 병렬 실행 현황
| 그룹 | 태스크 | worktree | 브랜치 | 상태 |
|------|--------|----------|--------|------|
```

**상태 값 열거형**:

| 컬럼 | 허용 값 | 설명 |
|------|--------|------|
| 그룹 상태 (그룹 레벨 요약) | `대기` / `진행 중` / `머지 중` / `완료` / `실패` | 병렬 그룹 전체의 진행도 |
| 태스크 상태 (행 레벨) | `대기` / `진행 중` / `검증 중` / `완료` / `실패` / `에스컬레이션` | 개별 태스크 진행도 |

**worktree 컬럼 형식**: 프로젝트 루트 기준 상대 경로 — `.worktrees/{group}-{task}` (예: `.worktrees/A-T2`, `.worktrees/A-T4`)

**그룹 vs 개별 태스크 상태 구분**:
- 병렬 그룹 상태는 태스크 목록 위에 별도 요약 행으로 관리한다:

```markdown
## 병렬 실행 현황

### 그룹 요약
| 그룹 | 태스크 수 | 완료 | 실패 | 그룹 상태 |
|------|----------|------|------|----------|
| A    | 2        | 1    | 0    | 진행 중   |

### 태스크 상세
| 그룹 | 태스크 | worktree            | 브랜치              | 상태    |
|------|--------|---------------------|---------------------|---------|
| A    | T2     | .worktrees/A-T2     | feat/oppd-A-T2      | 완료    |
| A    | T4     | .worktrees/A-T4     | feat/oppd-A-T4      | 진행 중 |
```

**머지 이력 기록**: 병렬 그룹 완료 후 머지 이력을 기록한다:

```markdown
## 머지 이력
| # | 그룹 | 머지 순서 | 충돌 여부 | 통합 테스트 | 머지 시점 |
|---|------|----------|----------|-----------|----------|
| 1 | A    | T2 → T4  | 없음     | Pass      | YYYY-MM-DD HH:mm |
```

**검증 루프 로그 테이블**: 자동 검증 루핑 진행 상황을 추적한다:

```markdown
## 검증 루프 로그
| # | 태스크 | 검증 유형 | 시도 | 결과 | 오류 요약 | 시점 |
|---|--------|----------|------|------|----------|------|
| 1 | T2     | lint     | 1/∞  | Pass | -        | HH:mm |
| 2 | T2     | build    | 1/2  | Fail | TS2345: Property 'x' missing | HH:mm |
| 3 | T2     | build    | 2/2  | Pass | -        | HH:mm |
| 4 | T2     | test     | 1/3  | Fail | 2/15 failed (auth.test) | HH:mm |
| 5 | T2     | test     | 2/3  | Pass | -        | HH:mm |
```

- 병렬 그룹 내 각 태스크는 독립 worktree에서 실행된다
- 오케스트레이터만 STATE.md를 갱신한다 (워커는 자신의 태스크 결과만 반환)
- 동시 갱신 충돌 방지: 오케스트레이터가 순차적으로 결과를 수집하여 갱신

#### Step 2: verification-loop-guide.md

자동 검증 루핑 전략을 상세히 기술하는 레퍼런스 문서.

**문서 목차/섹션 구조**:

```
# 자동 검증 루핑 가이드 (Verification Loop Guide)

## 1. 개요
   - 목적: EXECUTE 스텝마다 즉시 검증하여 오류를 조기 차단
   - 적용 범위: oppd Phase 3 태스크 실행 시

## 2. Layered Verification 모델
   - 계층 정의: lint/format → build/type → test → QA
   - 각 계층의 역할과 실행 순서
   - 계층별 게이트: 하위 계층 통과 후 상위 계층 진행

## 3. 실패 유형별 루핑 전략
   ### 3-1. lint/format 실패
   - 감지: 검증 명령 실행 결과 파싱
   - 자동 수정: 워커에게 오류 메시지 전달 → 즉시 수정 지시
   - 재시도: 제한 없음 (기계적 수정)
   ### 3-2. build/type 실패
   - 감지: 빌드 로그/타입 에러 파싱
   - 자동 수정: 오류 컨텍스트(파일, 라인, 메시지) 전달 → 워커 수정
   - 재시도: 최대 2회
   ### 3-3. test 실패
   - 감지: 테스트 러너 출력 파싱 (실패 테스트명, assertion 메시지)
   - 컨텍스트 전달: 실패 테스트 파일 + 에러 메시지 + 관련 소스 코드
   - 재시도: 최대 3회
   ### 3-4. QA 설계/아키텍처 이슈
   - 즉시 에스컬레이션 (자동 수정 불가)

## 4. 회귀 방지 가드
   - 자동 수정 후 전체 테스트 스위트 재실행
   - 이전 통과 테스트가 실패하면 즉시 루프 중단
   - 회귀 감지 시 에스컬레이션 보고 형식

## 5. 에스컬레이션 프로토콜
   - 루프 한도 초과 시 사용자 보고 형식
   - 회귀 발생 시 사용자 보고 형식
   - STATE.md 검증 루프 로그 기록 형식

## 6. PM 루프 모니터링
   - STATE.md 검증 루프 로그 갱신 시점
   - 루프 진행률 추적 방법
   - 세션 복원 시 루프 상태 재개

## 7. 하네스 참조
   - opal-harness.md "자동 루핑 제약" Guards 링크
```

**구체적 예시 — lint 오류 자동 수정 흐름**:

```
[예시: ESLint 오류 자동 수정]

1. 워커가 EXECUTE Step 완료 → 검증 명령 실행: `npm run lint`
2. 결과: FAIL — 3 errors (no-unused-vars: 2, prefer-const: 1)
3. 오케스트레이터 → 워커에게 자동 수정 지시:
   "lint 오류 3건 수정하라:
    - src/auth/service.ts:15 — no-unused-vars (변수 'temp' 미사용)
    - src/auth/service.ts:42 — no-unused-vars (import 'Logger' 미사용)
    - src/api/handler.ts:8 — prefer-const ('config'를 const로 변경)"
4. 워커 수정 완료 → 재검증: `npm run lint` → PASS
5. 다음 계층(build)으로 진행
```

**구체적 예시 — 테스트 실패 컨텍스트 전달 형식**:

```
[예시: Jest 테스트 실패 → 워커에게 전달하는 컨텍스트]

검증 루프: test 시도 1/3 — FAIL

실패 테스트:
  - src/__tests__/auth.test.ts > AuthService > should validate token
    AssertionError: Expected 'valid' but received 'expired'
    at src/__tests__/auth.test.ts:45:12

관련 소스:
  - src/auth/service.ts (validateToken 메서드)
  - src/auth/types.ts (TokenStatus 타입)

지시: 위 실패 테스트를 분석하고 src/auth/service.ts의 validateToken 로직을 수정하라.
      수정 후 `npm test -- --testPathPattern=auth` 로 해당 테스트만 먼저 확인하라.
```

#### Step 3: parallel-execution-guide.md

병렬 태스크 실행 전략을 상세히 기술하는 레퍼런스 문서.

**문서 목차/섹션 구조**:

```
# 병렬 실행 가이드 (Parallel Execution Guide)

## 1. 개요
   - 목적: 의존성 없는 태스크를 동시 실행하여 개발 속도 향상
   - 적용 범위: oppd Phase 3, ROADMAP에 병렬 그룹이 존재하는 경우

## 2. 의존성 그래프 분석
   ### 2-1. ROADMAP.md에서 그래프 구축
   - 태스크 목록의 "의존성" 컬럼에서 인접 리스트 생성
   - 의존성 방향: 피의존 → 의존 (T1 → T2는 "T2가 T1에 의존")
   ### 2-2. 병렬 그룹 판별 알고리즘
   - 위상 정렬(topological sort) → 동일 레벨 태스크 → 병렬 그룹화
   - 의사코드 (아래 참조)
   ### 2-3. 충돌 검사
   - 동일 파일/모듈 수정 여부 → 병렬 불가 판정
   - worktree 충돌 가능성 검사

## 3. worktree 격리 전략
   ### 3-1. 디렉토리 구조
   - worktree 루트: `{프로젝트}/.worktrees/`
   - 개별 worktree: `.worktrees/{group}-{task}/`
   ### 3-2. 브랜치 네이밍
   - 형식: `feat/oppd-{group}-{task}` (예: feat/oppd-A-T2)
   ### 3-3. worktree 생성/정리 명령
   - 생성: `git worktree add .worktrees/{group}-{task} -b feat/oppd-{group}-{task}`
   - 정리: `git worktree remove .worktrees/{group}-{task}`

## 4. 병렬 디스패치
   - Agent 도구로 여러 워커를 동시 디스패치하는 프롬프트 형식
   - 각 워커에게 worktree 경로를 명시하여 격리 보장
   - 디스패치 후 결과 수집 방법

## 5. 머지 전략
   - 병렬 태스크 완료 후 main 브랜치에 순차 머지
   - 머지 순서: 변경 범위가 작은 것부터
   - 충돌 발생 시 PM 조정 흐름
   - 머지 이력 STATE.md 기록

## 6. 통합 테스트
   - 머지 완료 후 전체 테스트 스위트 실행
   - 통합 실패 시 원인 태스크 식별 → 재수정 루프

## 7. STATE.md 갱신
   - 오케스트레이터 단독 갱신 원칙
   - 그룹 요약 + 태스크 상세 테이블 갱신 시점
   - 머지 이력 기록

## 8. Fallback
   - worktree 미지원 플랫폼 → 순차 실행 폴백
   - Agent 도구 미지원 → 오케스트레이터 직접 순차 디스패치
```

**의존성 그래프 판별 알고리즘 의사코드**:

```
function buildParallelGroups(tasks):
    # 1. 인접 리스트 구축
    graph = {}
    in_degree = {}
    for task in tasks:
        graph[task.id] = []
        in_degree[task.id] = 0
    for task in tasks:
        for dep in task.dependencies:
            graph[dep].append(task.id)
            in_degree[task.id] += 1

    # 2. 위상 정렬 (Kahn's algorithm) — 레벨별 그룹화
    queue = [t for t in in_degree if in_degree[t] == 0]
    levels = []

    while queue:
        # 현재 큐의 모든 태스크는 동일 레벨 → 병렬 후보
        current_level = list(queue)
        levels.append(current_level)
        next_queue = []
        for task_id in current_level:
            for neighbor in graph[task_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    next_queue.append(neighbor)
        queue = next_queue

    # 3. 충돌 검사 — 동일 레벨 내 파일 충돌 시 분리
    parallel_groups = []
    for level in levels:
        if len(level) == 1:
            parallel_groups.append({"type": "sequential", "tasks": level})
        else:
            # 파일 충돌 검사: 동일 파일 수정 태스크는 별도 순차 그룹으로 분리
            conflict_free = splitByFileConflict(level)
            for group in conflict_free:
                if len(group) == 1:
                    parallel_groups.append({"type": "sequential", "tasks": group})
                else:
                    parallel_groups.append({"type": "parallel", "tasks": group})

    return parallel_groups
```

**worktree 사용 예시 — 디렉토리 구조 및 브랜치**:

```
[예시: 병렬 그룹 (A02: DB 스키마, A03: 인증/인가) — A01 완료 후 동시 시작]

# oppd 태스크 + actions 폴더 구조
tasks/053-oppd-my-project/
├── TASK.md
├── STATE.md
└── actions/
    ├── A01-setup/             ← 완료됨
    ├── A02-db-schema/         ← 병렬 실행 대상
    │   ├── TASK.md
    │   └── PLAN.md
    └── A03-auth-api/          ← 병렬 실행 대상
        ├── TASK.md
        └── PLAN.md

# worktree 생성 (프로젝트 루트에서)
git worktree add .worktrees/A02-db-schema -b feat/oppd-A02
git worktree add .worktrees/A03-auth-api -b feat/oppd-A03

# 워커 디스패치: 각 워커에게 worktree + action 경로 전달
Agent(A02-worker, cwd=".worktrees/A02-db-schema",
      task_folder="tasks/053-oppd-my-project/actions/A02-db-schema/")  ← 동시
Agent(A03-worker, cwd=".worktrees/A03-auth-api",
      task_folder="tasks/053-oppd-my-project/actions/A03-auth-api/")   ← 동시

# 완료 후 머지
git merge feat/oppd-A02     # A02 먼저 머지 (변경 범위 작은 것)
npm test                     # 중간 검증
git merge feat/oppd-A03     # A03 머지
npm test                     # 통합 테스트

# 정리
git worktree remove .worktrees/A02-db-schema
git worktree remove .worktrees/A03-auth-api
```

#### Step 4: roadmap-guide.md 강화

기존 태스크 분할 원칙에 추가:

- **자동 테스트 가능성 기준 추가**: 분할 원칙 7번으로 "각 태스크의 성공/실패를 lint/build/test로 기계적으로 판정할 수 있는 단위로 분할한다"
- **완료 기준 템플릿**: 각 태스크 행에 `검증 명령` 컬럼 추가 (예: `npm run lint && npm run build && npm test`)
- **의존성 그래프 시각화**: 태스크 목록 아래에 텍스트 기반 의존성 그래프 섹션 추가
- **병렬 그룹 판별 기준 강화**: 동일 파일/모듈 수정 여부 외에, worktree 충돌 가능성까지 검사
- **PM 검수 체크리스트 항목 추가**: "각 태스크에 기계적 검증 가능한 완료 기준이 있는가"
- **actions 폴더 구조 반영**: 로드맵 태스크를 "액션(action)"으로 명명하고, `A{NN}-{name}` 형식으로 채번. 태스크 목록 테이블에 `액션 경로` 컬럼 추가 (예: `actions/A01-db-schema/`)

#### Step 5: oppd SKILL.md 반영

> oppd SKILL.md의 구체적 변경 범위를 섹션별로 명시한다.

**태스크 생성 변경** — 대상 섹션: `## 태스크 생성`:

- 폴더 구조에 `actions/` 디렉토리 추가:
  ```
  tasks/{NNN}-oppd-{프로젝트명}/
  ├── TASK.md
  ├── STATE.md
  ├── DONE.md
  └── actions/              ← 신규
      ├── A01-{액션명}/     ← opd/opds가 사용하는 태스크 폴더
      │   ├── TASK.md
      │   ├── PLAN.md
      │   ├── TEST-SCENARIO.md
      │   └── DONE.md
      ├── A02-{액션명}/
      └── ...
  ```
- TASK.md 절차 테이블의 Phase 3 산출물: `tasks/{N}~{M}` → `actions/A01~A{MM}`로 변경
- `A{NN}`: 2자리 순번, oppd 태스크 스코프 내에서만 유효 (글로벌 채번 불필요)

**Phase 2 변경** — 대상 섹션: `## Phase 2: 로드맵 수립 (PM 직접)`:

- **2-1. 사전 준비** (기존 유지 + 추가):
  - 기존 Read 목록 유지 (`roadmap-guide.md`, `PRD.md`, `TRD.md`, `ARCHITECTURE.md`)
  - Read 목록에 추가: `references/verification-loop-guide.md`, `references/parallel-execution-guide.md`
- **2-2. 태스크 분할** (기존 유지 + 추가):
  - 기존 분할 원칙 1~5 유지
  - **6번 추가**: "각 태스크의 성공/실패를 lint/build/test로 기계적으로 판정할 수 있는 단위로 분할한다 (자동 테스트 가능성)"
  - 기존 스킬 판단 기준 테이블 유지
  - 분할된 태스크를 **"액션(action)"**으로 명명, `A{NN}-{name}` 형식으로 채번
- **2-3. PM 검수** (기존 유지, 변경 없음)
- **2-4. 사용자 확정** (기존 유지 + 태스크 목록 테이블 컬럼 변경):
  - 기존 태스크 목록 테이블을 액션 테이블로 변경:
    ```
    | # | 액션 | 스킬 | 의존성 | 우선순위 | 검증 명령 |
    |---|------|------|--------|---------|----------|
    | A01 | DB 스키마 | //opds | - | Must | npm run lint && npm test |
    | A02 | 인증 API | //opds | A01 | Must | npm run lint && npm test |
    ```
- **2-5. 사용자 확정 후 후속 조치** (기존 유지, 변경 없음)

**Phase 3 변경** — 대상 섹션: `## Phase 3: 태스크 순차 실행 (opd/opds 위임)`:

- 섹션 제목 변경: `## Phase 3: 액션 실행 (opd/opds 위임)` — "태스크 순차" → "액션"
- **3-0. 의존성 최신 검증** (기존 유지, 변경 없음)
- **3-1. 실행 루프** (기존 구조 확장):
  - 기존 순차 전용 루프를 의존성 그래프 기반 실행(순차 + 병렬 혼합)으로 전환
  - opd/opds 호출 시 태스크 폴더로 `actions/A{NN}-{name}/`을 전달 (opd/opds 내부 로직 변경 없음)
  - 자동 검증 루핑을 각 액션 완료 후에 삽입
  - 상세 로직은 아래 3-1a, 3-1b에서 정의
- **3-1a. 자동 검증 루핑** (신규 섹션 추가 — 3-1 하위):
  - 실패 유형별 루핑 전략 요약 (상세는 `references/verification-loop-guide.md` 참조)
  - 회귀 방지 + 에스컬레이션 규칙
  - 하네스 "자동 루핑 제약" Guards 참조
- **3-1b. 병렬 액션 실행** (신규 섹션 추가 — 3-1 하위):
  - worktree 격리 + 병렬 디스패치 요약 (상세는 `references/parallel-execution-guide.md` 참조)
  - 머지 전략 + 통합 테스트 규칙
  - 하네스 "병렬 실행 State" 참조
- **3-2. 액션 시작/완료 보고** (기존 유지, "태스크" → "액션" 용어 변경)
- **3-3. 전체 완료 보고** (기존 유지, 변경 없음)

**STATE.md 템플릿 변경** — 대상 섹션: `## STATE.md 관리`:

- 기존 섹션 전체 유지 (`현재 상태`, `Phase 진행 현황`, `로드맵`, `PM 검수 로그`, `의사결정 로그`)
- **로드맵 섹션 변경**: 태스크 → 액션으로 용어 전환, 경로를 `actions/A{NN}-{name}/`으로 변경:
  ```
  | # | 액션 | 스킬 | actions/ 경로 | 상태 |
  |---|------|------|-------------|------|
  | A01 | DB 스키마 | //opds | actions/A01-db-schema/ | 완료 |
  ```
- **추가 섹션 1**: `## 병렬 실행 현황` — 그룹 요약 + 액션 상세 + 머지 이력 (Step 1에서 정의한 구조)
- **추가 섹션 2**: `## 검증 루프 로그` — 액션별 검증 시도 이력 (Step 1에서 정의한 구조)

**참조 문서 등록** — 대상 섹션: 없음 (스킬 탐색 경로와 별도로 references 링크 추가):

- Phase 2 사전 준비에서 새 가이드 2개 Read 지시
- Phase 3 신규 섹션에서 가이드 참조 링크

---

## 3. 실행 체크리스트

> 총 5개 Step

### Step 1: 하네스 확장 (자동 루핑 Guards + 병렬 State)
- [x] 완료
- **파일**: `~/.opal/references/opal-harness.md`
- **작업 내용**:
  - Guards 섹션에 "자동 루핑 제약 (Verification Loop Guards)" 하위 섹션 추가: 실패 유형별 최대 재시도, 회귀 방지 규칙, 에스컬레이션 조건
  - State 섹션에 "병렬 실행 State" 하위 섹션 추가: 병렬 현황 테이블 구조, 동시 갱신 방지 원칙 (오케스트레이터 단독 갱신)
  - 기존 Guards/Gates/State 규칙 위반 없이 확장만 수행
- **완료 기준**: 하네스에 자동 루핑 Guards와 병렬 State 섹션이 추가되고, 기존 규칙과 충돌 없음
- **테스트**: 기존 Guards/Gates/State 규칙이 그대로 존재하는지 확인. 새 섹션이 기존 원칙("사용자 게이트 유지", "오케스트레이터만 STATE.md 갱신")과 일관성 있는지 확인
- **의존**: 없음

### Step 2: 자동 검증 루핑 가이드 작성
- [x] 완료
- **파일**: `~/.opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md`
- **작업 내용**:
  - Layered Verification 모델 정의 (EXECUTE 스텝마다 즉시 검증 계층)
  - 실패 유형별 루핑 전략 상세 기술 (lint→build→test→QA)
  - 각 유형의 감지 방법, 자동 수정 프로세스, 컨텍스트 전달 방법
  - 회귀 방지 가드: 자동 수정 후 전체 테스트 재실행 흐름
  - 에스컬레이션 프로토콜: 사용자 보고 형식 + STATE.md 기록 형식
  - PM 루프 모니터링: 루프 진행 현황 추적 방법
  - 하네스 Guards에 정의된 재시도 한도 참조
- **완료 기준**: 가이드만 보고 oppd Phase 3에서 자동 검증 루핑을 구현할 수 있을 정도로 상세함
- **테스트**: 하네스 자동 루핑 Guards와 재시도 한도가 일치하는지 확인. 에스컬레이션 시 사용자 게이트가 유지되는지 확인
- **의존**: Step 1 (하네스의 루핑 Guards 참조)

### Step 3: 병렬 실행 가이드 작성
- [x] 완료
- **파일**: `~/.opal/skills/opal-pilot-project-dev/references/parallel-execution-guide.md`
- **작업 내용**:
  - 의존성 그래프 분석: ROADMAP.md에서 병렬 그룹 판별 로직
  - worktree 격리 전략: `git worktree add` 명령 형식, 브랜치 네이밍, 디렉토리 구조
  - 병렬 디스패치: Agent 도구로 여러 워커 동시 디스패치 프롬프트 형식
  - 머지 전략: 병렬 태스크 완료 후 main 브랜치 순차 머지, 충돌 시 PM 조정
  - 통합 테스트: 머지 후 전체 테스트 스위트 실행
  - STATE.md 동시 갱신: 오케스트레이터 단독 갱신 원칙
  - Fallback: worktree/Agent 도구 미지원 플랫폼에서 순차 실행 폴백
- **완료 기준**: 가이드만 보고 oppd Phase 3에서 병렬 실행을 구현할 수 있을 정도로 상세함
- **테스트**: 하네스 병렬 State 구조와 일치하는지 확인. 플랫폼 독립성 유지되는지 확인 (Fallback 존재). worktree 사용 시 각 워커 독립성 보장되는지 확인
- **의존**: Step 1 (하네스의 병렬 State 참조)

### Step 4: 로드맵 가이드 강화
- [x] 완료
- **파일**: `~/.opal/skills/opal-pilot-project-dev/references/roadmap-guide.md`
- **작업 내용**:
  - 태스크 분할 원칙에 7번 추가: "자동 테스트 가능성 — 성공/실패를 lint/build/test로 기계적으로 판정할 수 있는 단위로 분할"
  - 태스크 목록 테이블에 `검증 명령` 컬럼 추가 (예: `npm run lint && npm run build && npm test`)
  - 의존성 그래프 시각화 섹션 추가 (텍스트 기반 DAG)
  - 병렬 그룹 판별 기준에 "worktree 충돌 가능성" 항목 추가
  - PM 검수 체크리스트에 "각 태스크에 기계적 검증 가능한 완료 기준이 있는가" 항목 추가
  - verification-loop-guide.md, parallel-execution-guide.md 참조 링크 추가
- **완료 기준**: 로드맵 가이드에 자동 테스트 가능성 기준과 검증 명령 컬럼이 추가되고, 기존 내용과 통합됨
- **테스트**: 기존 태스크 분할 원칙 1~6이 그대로 존재하는지 확인. 태스크 목록 예시에 검증 명령 컬럼이 포함되는지 확인. PM 검수 체크리스트에 새 항목 존재 확인
- **의존**: Step 2, Step 3 (가이드 참조 링크 필요)

### Step 5: oppd SKILL.md Phase 2 + Phase 3 반영
- [x] 완료
- **파일**: `~/.opal/skills/opal-pilot-project-dev/SKILL.md`
- **작업 내용**:
  - **태스크 생성 섹션**: 폴더 구조에 `actions/` 디렉토리 추가 + `A{NN}-{name}` 채번 규칙 정의
  - **Phase 2 (2-1. 사전 준비)**: Read 목록에 새 가이드 2개 추가
  - **Phase 2 (2-2. 태스크 분할)**:
    - 기존 분할 원칙 1~5 유지
    - 분할 원칙 6번 추가: "자동 테스트 가능성" 기준
    - 분할된 태스크를 "액션(action)"으로 명명, `A{NN}-{name}` 형식으로 채번
    - 의존성 그래프 작성 의무화
    - 새 레퍼런스 참조: `references/verification-loop-guide.md`, `references/parallel-execution-guide.md`
  - **Phase 2 (2-4. 사용자 확정)**: 태스크 목록 → 액션 테이블로 변경 (`| # | 액션 | 스킬 | 의존성 | 우선순위 | 검증 명령 |`)
  - **Phase 3 섹션 제목**: "태스크 순차 실행" → "액션 실행"으로 변경
  - **Phase 3 (3-1. 실행 루프)**:
    - 순차 전용 → 의존성 그래프 기반 실행 (순차 + 병렬 혼합) 전환
    - opd/opds 호출 시 `actions/A{NN}-{name}/`을 태스크 폴더로 전달
    - 새 섹션 "3-1a. 자동 검증 루핑" 추가
    - 새 섹션 "3-1b. 병렬 액션 실행" 추가
    - 기존 3-2, 3-3 유지 — "태스크" → "액션" 용어 변경
  - **STATE.md 템플릿** (`## STATE.md 관리` 섹션):
    - 기존 섹션 유지, 로드맵 섹션을 액션 테이블로 변경 (`actions/` 경로)
    - 새 섹션 추가: `## 병렬 실행 현황` (그룹 요약 + 액션 상세 + 머지 이력)
    - 새 섹션 추가: `## 검증 루프 로그` (액션별 검증 시도 이력)
- **완료 기준**: oppd가 Phase 2에서 자동 테스트 가능한 태스크를 분할하고, Phase 3에서 자동 검증 루핑 + 병렬 실행을 수행할 수 있는 프로세스가 정의됨
- **테스트**: Phase 1(opwt 위임) 흐름이 변경되지 않았는지 확인. 기존 PM 검수/사용자 게이트가 유지되는지 확인. STATE.md 템플릿에 새 섹션이 포함되는지 확인. 하네스 Guards/Gates와 충돌 없는지 확인
- **의존**: Step 1, Step 2, Step 3, Step 4 (모든 하위 파일이 먼저 완성되어야 oppd에서 참조 가능)

---

## 4. QA 체크리스트

### 기능 테스트
- [ ] TASK.md 요구사항 A(로드맵 세분화): 자동 테스트 가능성 기준이 roadmap-guide.md와 oppd Phase 2에 반영되었는가
- [ ] TASK.md 요구사항 A: 각 태스크에 lint/build/test 검증 가능한 완료 기준 명시가 가능한 구조인가
- [ ] TASK.md 요구사항 A: 의존성 그래프로 병렬 실행 가능 그룹 식별이 가능한가
- [ ] TASK.md 요구사항 B(자동 검증 루핑): 실패 유형별 루핑 전략이 verification-loop-guide.md에 정의되었는가
- [ ] TASK.md 요구사항 B: EXECUTE 스텝마다 즉시 검증 흐름이 있는가
- [ ] TASK.md 요구사항 B: 회귀 방지 가드가 정의되었는가
- [ ] TASK.md 요구사항 B: PM 루프 모니터링 + 에스컬레이션 흐름이 있는가
- [ ] TASK.md 요구사항 C(병렬 실행): 의존성 그래프 기반 병렬 그룹 판별이 parallel-execution-guide.md에 정의되었는가
- [ ] TASK.md 요구사항 C: worktree 격리 전략이 있는가
- [ ] TASK.md 요구사항 C: 머지 전략 및 충돌 해결이 있는가
- [ ] TASK.md 요구사항 C: STATE.md 동시 갱신 전략이 있는가
- [ ] TASK.md 요구사항 D(스킬/하네스 반영): oppd Phase 2, Phase 3 섹션이 수정되었는가
- [ ] TASK.md 요구사항 D: roadmap-guide.md가 강화되었는가
- [ ] TASK.md 요구사항 D: 하네스에 필요한 확장이 반영되었는가

### 일관성 테스트
- [ ] 하네스 기존 규칙(Guards, Gates, State) 위반이 없는가 — 확장만 수행했는가
- [ ] opd/opds 내부 QA Gate 로직이 변경되지 않았는가
- [ ] 사용자 게이트가 유지되는가 (agentic이지만 최종 확정은 사용자)
- [ ] 무한 루프 방지: 최대 재시도 횟수가 명시되어 있는가
- [ ] 플랫폼 독립성: Claude/Cursor/Gemini 공통으로 동작 가능한가 (worktree 미지원 시 Fallback)
- [ ] 오케스트레이터만 STATE.md 갱신 원칙이 병렬 실행에서도 유지되는가
- [ ] 디스패치 의무 원칙이 유지되는가 (PM이 직접 실행하지 않음)

### 문서 품질
- [ ] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가
- [ ] kebab-case 파일/폴더 네이밍을 따르는가
- [ ] 기존 문서와 톤/형식이 일관되는가
- [ ] 새 가이드의 YAML frontmatter가 올바른가 (해당 시)

---

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| worktree 미지원 플랫폼 | 병렬 실행 불가 | 순차 실행 Fallback 명시 — 플랫폼 독립성 유지 |
| Agent 도구 미지원 플랫폼 | 병렬 디스패치 불가 | 오케스트레이터가 직접 순차 실행하는 Fallback 명시 |
| 자동 수정 루프가 문제를 악화 | 회귀 발생, 코드 품질 저하 | 회귀 방지 가드 + 최대 재시도 한도 + 즉시 에스컬레이션 |
| 병렬 태스크 간 파일 충돌 | 머지 실패 | ROADMAP 단계에서 파일 충돌 사전 검사 + PM 수동 조정 |
| STATE.md 동시 쓰기 충돌 | 상태 불일치 | 오케스트레이터 단독 갱신 원칙으로 충돌 원천 방지 |
| oppd SKILL.md 복잡도 증가 | 가독성/유지보수성 저하 | 상세 로직을 별도 가이드(references/)로 분리, SKILL.md는 흐름만 기술 |
