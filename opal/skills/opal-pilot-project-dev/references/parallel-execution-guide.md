# 병렬 실행 가이드 (Parallel Execution Guide)

> opal-pilot-project-dev Phase 3에서 의존성 없는 액션을 동시 실행할 때 참조하는 전략/절차 지침.
> ROADMAP.md에 병렬 그룹이 존재하는 경우 이 가이드를 따른다.

---

## 1. 개요

### 목적

병렬은 1차 목표가 아니라 **세분화의 파생 효과**다. 액션을 단일 책임으로 잘게 나눌수록 파일·모듈 겹침이 줄어(충돌↓) 동시 실행 가능한 액션이 자연히 늘어난다(병렬↑). 즉 **세분화↑ → 충돌↓ → 병렬↑**로 속도가 따라온다. 각 액션을 독립된 git worktree에서 격리 실행하고, 완료 후 순차 머지하여 통합한다.

### 적용 범위

- oppd Phase 3 — 액션 실행 단계
- ROADMAP.md에 `▶ 병렬` 그룹이 존재하는 경우
- 2개 이상의 액션이 동일 의존성 레벨에 위치하고, 파일 충돌이 없는 경우

### 전제 조건

- git worktree 지원 환경 (git 2.5+)
- Agent 도구로 서브에이전트 병렬 디스패치 가능한 플랫폼
- 미지원 시 Fallback (섹션 8 참조)

---

## 2. 의존성 그래프 분석

### 2-1. ROADMAP.md에서 그래프 구축

ROADMAP.md 액션 테이블의 "의존성" 컬럼에서 인접 리스트(adjacency list)를 생성한다.

**액션 테이블 예시**:

| # | 액션 | 스킬 | 의존성 | 우선순위 | 검증 명령 |
|---|------|------|--------|---------|----------|
| A01 | 프로젝트 초기 셋업 | opds | - | Must | `npm run lint:fix && npm run build` |
| A02 | DB 스키마 설계 | opd | A01 | Must | `npm run lint:fix && npm run build && npm test` |
| A03 | 인증/인가 API | opd | A01 | Must | `npm run lint:fix && npm run build && npm test` |
| A04 | 사용자 프로필 UI | opdw | A02, A03 | Must | `npm run lint:fix && npm run build && npm test` |

**인접 리스트 생성 규칙**:

- 의존성 방향: 피의존 -> 의존 (A01 -> A02는 "A02가 A01에 의존")
- `-` (의존성 없음)인 액션은 루트 노드로 분류
- 위 예시의 인접 리스트:
  ```
  A01 -> [A02, A03]
  A02 -> [A04]
  A03 -> [A04]
  A04 -> []
  ```

### 2-2. 병렬 그룹 판별 알고리즘

위상 정렬(topological sort)로 동일 레벨의 액션을 식별하고, 병렬 그룹으로 묶는다.

**의사코드** (Kahn's algorithm 기반):

```python
function buildParallelGroups(actions):
    # 1. 인접 리스트 구축
    graph = {}
    in_degree = {}
    for action in actions:
        graph[action.id] = []
        in_degree[action.id] = 0
    for action in actions:
        for dep in action.dependencies:
            graph[dep].append(action.id)
            in_degree[action.id] += 1

    # 2. 위상 정렬 (Kahn's algorithm) — 레벨별 그룹화
    queue = [a for a in in_degree if in_degree[a] == 0]
    levels = []

    while queue:
        current_level = list(queue)
        levels.append(current_level)
        next_queue = []
        for action_id in current_level:
            for neighbor in graph[action_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    next_queue.append(neighbor)
        queue = next_queue

    # 3. 충돌 검사 — 동일 레벨 내 파일 충돌 시 분리
    parallel_groups = []
    for level in levels:
        if len(level) == 1:
            parallel_groups.append({"type": "sequential", "actions": level})
        else:
            conflict_free = splitByFileConflict(level)
            for group in conflict_free:
                if len(group) == 1:
                    parallel_groups.append({"type": "sequential", "actions": group})
                else:
                    parallel_groups.append({"type": "parallel", "actions": group})

    return parallel_groups
```

**위 예시 적용 결과**:

| 레벨 | 액션 | 유형 |
|------|------|------|
| Level 0 | A01 | sequential |
| Level 1 | A02, A03 | parallel |
| Level 2 | A04 | sequential |

### 2-3. 충돌 검사

동일 레벨의 액션이 같은 파일/모듈을 수정하면 병렬 실행이 불가하다. 다음 기준으로 판정한다.

**파일 충돌 판정 기준**:

| 충돌 유형 | 예시 | 판정 |
|----------|------|------|
| 동일 파일 수정 | A02와 A03 모두 `prisma/schema.prisma` 수정 | 병렬 불가 |
| 동일 모듈 디렉토리 | A02와 A03 모두 `src/auth/` 내 파일 수정 | 병렬 불가 |
| 공유 설정 파일 | 두 액션이 동일한 설정 파일(`package.json` 등) 수정 | 병렬 불가 |
| 완전히 다른 경로 | A02는 `src/db/`, A03은 `src/auth/` | 병렬 가능 |

**충돌 검사 수행 시점**: ROADMAP 수립(Phase 2) 단계에서 사전 검사한다.

**충돌 발견 시 처리**:
1. 해당 액션들을 동일 병렬 그룹에서 분리
2. 순차 실행으로 전환하거나, 의존성을 추가하여 실행 순서 강제
3. PM이 ROADMAP.md에 충돌 사유를 주석으로 기록

---

## 3. worktree 격리 전략

### 3-1. 디렉토리 구조

각 병렬 액션은 독립된 git worktree에서 실행한다. worktree는 프로젝트 루트 하위에 생성한다.

```
{프로젝트 루트}/
├── .worktrees/                    # worktree 루트 (gitignore 대상)
│   ├── A02-db-schema/             # A02 액션 전용 worktree
│   └── A03-auth-api/              # A03 액션 전용 worktree
├── tasks/
│   └── {NNN}-{name}/
│       └── actions/
│           ├── A01-setup/
│           ├── A02-db-schema/
│           └── A03-auth-api/
└── src/                           # 메인 작업 디렉토리
```

**규칙**:
- worktree 루트: `{프로젝트 루트}/.worktrees/`
- 개별 worktree: `.worktrees/{action-id}/` (예: `.worktrees/A02-db-schema/`)
- `.worktrees/`는 `.gitignore`에 추가한다
- 각 worktree는 메인 저장소의 전체 파일 트리를 포함하므로 독립적으로 빌드/테스트 가능

### 3-2. 브랜치 네이밍

| 항목 | 형식 | 예시 |
|------|------|------|
| 병렬 액션 브랜치 | `feat/oppd-{action-id}` | `feat/oppd-A02` |
| 베이스 브랜치 | 현재 메인 브랜치 (통상 `main`) | `main` |

### 3-3. worktree 생성/정리 명령

**생성**:

```bash
# worktree 루트 디렉토리 생성 (최초 1회)
mkdir -p .worktrees

# .gitignore에 추가 (최초 1회)
echo ".worktrees/" >> .gitignore

# 개별 worktree 생성 — 베이스 브랜치에서 새 브랜치를 만들어 체크아웃
git worktree add .worktrees/{action-id} -b feat/oppd-{action-id}

# 예시
git worktree add .worktrees/A02-db-schema -b feat/oppd-A02
git worktree add .worktrees/A03-auth-api -b feat/oppd-A03
```

**정리** (머지 완료 후):

```bash
# worktree 제거
git worktree remove .worktrees/{action-id}

# 브랜치 정리 (머지 완료된 브랜치)
git branch -d feat/oppd-{action-id}

# 예시
git worktree remove .worktrees/A02-db-schema
git branch -d feat/oppd-A02
```

**주의사항**:
- worktree 생성 전 메인 브랜치가 최신 상태인지 확인
- worktree 내에서는 해당 브랜치만 체크아웃된 상태이므로 다른 worktree와 간섭 없음
- worktree 제거 전 미커밋 변경이 없는지 확인

---

## 4. 병렬 디스패치

### 4-1. 디스패치 프롬프트 형식

오케스트레이터(oppd)가 Agent 도구를 사용하여 여러 워커를 동시에 디스패치한다. 각 워커에게 worktree 경로와 action 경로를 명시하여 격리를 보장한다.

**디스패치 프롬프트 템플릿**:

```
당신은 opal-task-agent (범용 워커)입니다.

## 작업 환경
- **작업 디렉토리 (cwd)**: {프로젝트 루트}/.worktrees/{action-id}/
- **태스크 폴더**: tasks/{NNN}-{name}/actions/{action-id}/
- **브랜치**: feat/oppd-{action-id}

## 수행할 작업
{action-id}에 정의된 작업을 수행하세요.

## 제약 조건
- 작업 디렉토리(.worktrees/{action-id}/) 내에서만 파일을 수정하세요.
- 다른 worktree나 메인 작업 디렉토리의 파일을 직접 수정하지 마세요.
- 완료 후 검증 명령을 실행하고 결과를 보고하세요.
- 검증 명령: {검증 명령}

## 참조 문서
{관련 문서 경로 목록}
```

### 4-2. 동시 디스패치

병렬 그룹의 모든 액션에 대해 Agent 도구 호출을 **동일 응답 내에서** 병렬로 수행한다.

```
# 오케스트레이터가 한 번의 응답에서 여러 Agent 호출을 수행
Agent(prompt="A02 워커 프롬프트", cwd=".worktrees/A02-db-schema/")
Agent(prompt="A03 워커 프롬프트", cwd=".worktrees/A03-auth-api/")
```

### 4-3. 결과 수집

디스패치된 모든 워커의 결과를 수집한 후 다음을 수행한다:

1. 각 워커의 반환 결과(성공/실패, 산출물, 검증 결과)를 확인
2. `state-tool` 호출 (오케스트레이터만 수행, 머지 이력은 자유 텍스트 영역):
   ```bash
   ~/.opal/tools/state-tool/run.sh mark <task-path> --row <액션_행N> --done --note 'A{NN} 완료'
   ```
   > **[R-10]** oppd 비표준 행 구성 — `gate-pass` 사용 불가. `mark` 개별 호출 필수 (`tasks/134-260501-opp-pipeline-state-tool/PLAN.md` §2.13 G-10, R-10)
3. 실패한 액션이 있으면:
   - 자동 검증 루핑 적용 (verification-loop-guide.md 참조)
   - 루핑 한도 초과 시 사용자 에스컬레이션
4. 모든 액션 성공 시 머지 단계로 진행

---

## 5. 머지 전략

### 5-1. 머지 순서

병렬 액션 완료 후 main 브랜치에 순차적으로 머지한다. 머지 순서는 변경 범위가 작은 것부터 진행하여 충돌 가능성을 최소화한다.

**머지 순서 결정 기준**:

| 우선순위 | 기준 | 근거 |
|---------|------|------|
| 1 | 변경 파일 수가 적은 액션 | 충돌 표면적 최소화 |
| 2 | 다른 액션의 의존 대상이 되는 액션 | 후속 머지의 베이스 안정화 |
| 3 | 핵심 인프라 변경 (스키마, 설정) | 나머지 액션의 기반 |

### 5-2. 머지 절차

```bash
# 1. 메인 브랜치로 이동
git checkout main

# 2. 첫 번째 액션 머지 (변경 범위 작은 순)
git merge feat/oppd-A02

# 3. 머지 후 즉시 검증
{검증 명령}  # 예: npm run lint:fix && npm run build && npm test

# 4. 검증 통과 시 다음 액션 머지
git merge feat/oppd-A03

# 5. 머지 후 즉시 검증
{검증 명령}
```

### 5-3. 충돌 발생 시 처리

머지 중 충돌이 발생하면 오케스트레이터(PM)가 조정한다.

**충돌 해결 흐름**:

1. `git merge --abort`로 머지 취소
2. 충돌 파일과 내용을 분석
3. 판단 기준:
   - **자동 해결 가능** (단순 import 추가 등): PM이 직접 해결 후 머지 재시도
   - **설계 판단 필요**: 사용자에게 에스컬레이션
4. 해결 후 통합 테스트 재실행

### 5-4. 머지 이력 기록

머지 완료 시 STATE.md에 이력을 기록한다 (§7-3 병렬 실행 State 구조 준수).

```markdown
## 머지 이력
| # | 그룹 | 머지 순서 | 충돌 여부 | 통합 테스트 | 머지 시점 |
|---|------|----------|----------|-----------|----------|
| 1 | A    | A02 → A03 | 없음     | Pass      | YYYY-MM-DD HH:mm |
```

---

## 6. 통합 테스트

### 6-1. 전체 테스트 스위트 실행

모든 병렬 액션의 머지가 완료되면 전체 테스트 스위트를 실행한다.

```bash
# 전체 검증 — 프로젝트에 맞는 검증 명령 사용
npm run lint:fix && npm run build && npm test
```

### 6-2. 통합 실패 시 처리

통합 테스트 실패 시 원인 액션을 식별하고 재수정 루프를 수행한다.

**원인 식별 절차**:

1. 실패한 테스트 케이스 확인
2. `git log --oneline` 으로 머지 순서 확인
3. `git bisect` 또는 각 머지 시점의 테스트 결과로 원인 액션 특정
4. 원인 액션의 워커에게 재수정 디스패치

**재수정 루프**:

1. 원인 액션의 worktree를 재생성 (또는 기존 worktree 활용)
2. 해당 워커에게 실패 정보와 함께 재수정 디스패치
3. 수정 완료 후 재머지 + 통합 테스트
4. 자동 루핑 제약(하네스 Guards) 준수 — 최대 재시도 초과 시 사용자 에스컬레이션

---

## 7. STATE.md 갱신

> **[MUST] 파이프라인 행 상태(⬜/🔄/✅) 변경은 `~/.opal/tools/state-tool/run.sh`로만 수행한다. `state.json` 직접 편집 금지 — 현황 조회는 `state-tool show <task-path>`로 한다.**
> — `tasks/134-260501-opp-pipeline-state-tool/TASK.md` F-18 / `PLAN.md` §1.5 M-29 / §3 Step 11 / 094 §3.4.2 표준 문구 A

### 7-1. 갱신 원칙

**오케스트레이터 단독 갱신 원칙**: STATE.md 파이프라인 행은 오케스트레이터(oppd)만 `state-tool` 호출로 갱신한다. 워커는 자신의 작업 결과만 반환하고, STATE.md를 직접 수정하지 않는다.

이 원칙은 병렬 실행에서 동시 쓰기 충돌을 원천 방지한다.

### 7-2. 갱신 시점

| 이벤트 | 갱신 내용 | state-tool 호출 |
|--------|----------|----------------|
| 병렬 그룹 시작 | 그룹 요약 테이블에 그룹 추가, 태스크 상세에 각 액션 `대기` 등록 | `state advance --row <N>` |
| 워커 디스패치 | 해당 액션 상태 -> `진행 중`, worktree/브랜치 정보 기록 | (worktree/브랜치 정보는 자유 텍스트 영역) |
| 워커 완료 (성공) | 해당 액션 상태 -> `완료`, 그룹 요약 완료 카운트 증가 | `state mark --row <N> --done --note 'A{NN} 완료'` |
| 워커 완료 (실패) | 해당 액션 상태 -> `실패`, 블로커 섹션에 사유 기록 | `state block --row <N> --reason '<사유>'` (블로커 섹션은 자유 텍스트 영역) |
| 검증 루프 진행 | 검증 루프 로그 테이블에 시도 이력 추가 | (검증 루프 로그는 자유 텍스트 영역 — state-tool 범위 밖) |
| 머지 완료 | 머지 이력 테이블에 기록, 그룹 상태 -> `머지 중` 또는 `완료` | `state mark --row <N> --done --note '그룹 완료'` (머지 이력은 자유 텍스트 영역) |
| 통합 테스트 통과 | 그룹 상태 -> `완료` | `state mark --row <N> --done` |

### 7-3. 그룹 요약 + 태스크 상세 테이블

이 가이드(§7-2, §7-3)에 정의된 병렬 실행 State 구조를 따른다.

**상태 값 열거형**:

| 컬럼 | 허용 값 | 설명 |
|------|--------|------|
| 그룹 상태 | `대기` / `진행 중` / `머지 중` / `완료` / `실패` | 병렬 그룹 전체의 진행도 |
| 태스크 상태 | `대기` / `진행 중` / `검증 중` / `완료` / `실패` / `에스컬레이션` | 개별 태스크 진행도 |

**worktree 컬럼 형식**: 프로젝트 루트 기준 상대 경로 — `.worktrees/{group}-{task}` (예: `.worktrees/A-T2`)

**STATE.md 병렬 실행 섹션 예시**:

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

## 머지 이력
| # | 그룹 | 머지 순서 | 충돌 여부 | 통합 테스트 | 머지 시점 |
|---|------|----------|----------|-----------|----------|
| 1 | A    | T2 → T4  | 없음     | Pass      | YYYY-MM-DD HH:mm |

## 검증 루프 로그
| # | 태스크 | 검증 유형 | 시도 | 결과 | 오류 요약 | 시점 |
|---|--------|----------|------|------|----------|------|
| 1 | T2     | lint     | 1/∞  | Pass | -        | HH:mm |
| 2 | T2     | build    | 1/2  | Fail | TS2345: Property 'x' missing | HH:mm |
| 3 | T2     | build    | 2/2  | Pass | -        | HH:mm |
```

---

## 8. Fallback

### 8-1. worktree 미지원 플랫폼

git worktree를 사용할 수 없는 환경에서는 순차 실행으로 폴백한다.

**감지 조건**:
- `git worktree list` 명령 실패
- 파일 시스템 제약으로 worktree 생성 불가

**순차 실행 폴백 절차**:

1. 병렬 그룹의 액션을 순차 목록으로 변환
2. 각 액션을 메인 브랜치에서 순서대로 실행
3. 액션 완료마다 커밋하여 롤백 포인트 확보
4. `state-tool` 호출로 fallback 상태 기록:
   ```bash
   ~/.opal/tools/state-tool/run.sh mark <task-path> --row <N> --done --note 'sequential fallback'
   ```

```
# worktree 미지원 시 — 순차 실행
for action in parallel_group.actions:
    execute(action)          # 메인 브랜치에서 직접 실행
    verify(action)           # 검증
    commit(action)           # 완료 커밋
    state mark <task-path> --row <N> --done  # state-tool 호출로 행 갱신
```

### 8-2. Agent 도구 미지원 플랫폼

Agent 도구(서브에이전트 병렬 디스패치)를 사용할 수 없는 환경에서는 오케스트레이터가 직접 순차 디스패치한다.

**감지 조건**:
- Agent 도구가 플랫폼에서 제공되지 않는 경우
- Cursor, Gemini 등 Agent 병렬 호출을 지원하지 않는 경우

**순차 디스패치 폴백 절차**:

1. worktree는 여전히 사용 가능하면 생성 (격리 이점 유지)
2. 오케스트레이터가 각 워커 작업을 하나씩 순차 실행
3. 하나의 액션 완료 후 다음 액션 시작
4. 결과 수집 및 머지는 동일하게 수행

```
# Agent 도구 미지원 시 — worktree는 사용하되 순차 실행
for action in parallel_group.actions:
    create_worktree(action)
    execute_in_worktree(action)   # 오케스트레이터가 직접 순차 실행
    verify(action)
    # 모든 액션 완료 후 머지
merge_all(parallel_group)
```

### 8-3. Fallback 판정 흐름

```
병렬 그룹 실행 시작
  ├─ Agent 도구 사용 가능?
  │   ├─ Yes ─ worktree 사용 가능?
  │   │         ├─ Yes → 완전 병렬 실행 (worktree + Agent 병렬 디스패치)
  │   │         └─ No  → 순차 실행 Fallback (Agent 순차 + 메인 브랜치)
  │   └─ No  ─ worktree 사용 가능?
  │             ├─ Yes → worktree 격리 + 순차 디스패치
  │             └─ No  → 완전 순차 실행 Fallback (메인 브랜치 + 순차)
```

---

## 부록: 전체 흐름 예시

### 시나리오

```
tasks/053-oppd-my-project/
├── TASK.md
├── STATE.md
└── actions/
    ├── A01-setup/
    ├── A02-db-schema/
    └── A03-auth-api/
```

A01 완료 후, A02(DB 스키마)와 A03(인증/인가 API)을 병렬 실행한다.

### 실행 흐름

```bash
# 1. worktree 생성
git worktree add .worktrees/A02-db-schema -b feat/oppd-A02
git worktree add .worktrees/A03-auth-api -b feat/oppd-A03

# 2. 워커 병렬 디스패치
Agent(A02-worker, cwd=".worktrees/A02-db-schema",
      task_folder="tasks/053-oppd-my-project/actions/A02-db-schema/")
Agent(A03-worker, cwd=".worktrees/A03-auth-api",
      task_folder="tasks/053-oppd-my-project/actions/A03-auth-api/")

# 3. 결과 수집 후 머지 (변경 범위 작은 순)
git checkout main
git merge feat/oppd-A02
npm run lint:fix && npm run build && npm test     # 검증
git merge feat/oppd-A03
npm run lint:fix && npm run build && npm test     # 검증

# 4. worktree 정리
git worktree remove .worktrees/A02-db-schema
git worktree remove .worktrees/A03-auth-api
git branch -d feat/oppd-A02
git branch -d feat/oppd-A03
```

### STATE.md 최종 상태

```markdown
## 병렬 실행 현황

### 그룹 요약
| 그룹 | 태스크 수 | 완료 | 실패 | 그룹 상태 |
|------|----------|------|------|----------|
| A    | 2        | 2    | 0    | 완료      |

### 태스크 상세
| 그룹 | 태스크 | worktree                  | 브랜치          | 상태 |
|------|--------|---------------------------|-----------------|------|
| A    | A02    | .worktrees/A02-db-schema  | feat/oppd-A02   | 완료 |
| A    | A03    | .worktrees/A03-auth-api   | feat/oppd-A03   | 완료 |

## 머지 이력
| # | 그룹 | 머지 순서   | 충돌 여부 | 통합 테스트 | 머지 시점         |
|---|------|-----------|----------|-----------|------------------|
| 1 | A    | A02 → A03 | 없음     | Pass      | 2026-03-30 15:00 |
```

---

## 변경이력

| 날짜 | 버전 | 변경내용 |
|------|------|---------|
| 2026-05-01 | R-2 | state-tool 도입 — STATE.md 직접 편집 금지 + `state-tool` 호출 표현 교체. §4-3 결과 수집, §7-1 갱신 원칙, §7-2 갱신 시점 표, §8-1 Fallback 절차에 `state mark`/`state advance`/`state block` 호출 표기 통일. oppd 비표준 행 구성 R-10 명시(gate-pass 금지 — mark 개별 호출). 머지 이력/검증 루프 로그는 자유 텍스트 영역으로 보존 — TASK F-18 / PLAN §1.5 M-29 / §3 Step 11 (134) |
| 2026-06-21 16:05 | R-3 | §1 개요 §목적 재서술 — 병렬은 1차 목표가 아니라 세분화의 파생 효과(세분화↑→충돌↓→병렬↑). 기존 worktree 격리/머지/디스패치 본문 보존 (031) |
| 2026-06-21 | R-4 | `npm run lint` → `npm run lint:fix` 정합 — 액션 예시표(A01~A04), §5-2 머지 검증 예시, §6-1 전체 검증, §8-2 예시 코드 내 lint 명령을 L1 표준(`lint:fix`)으로 교체. watch 금지 규칙은 SSOT 단일 기재 — 재서술 없음 (033) |
| 2026-08-16 13:31 | R-5 | STATE.md 저널화 정합 — §7 MUST 블록을 표준 문구 A로 교체 (094) |
