# PLAN: opal-task-action-agent 신규 생성

> 작성일: 2026-03-30
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `~/.opal/agents/opal-task-agent/AGENT.md` | 기존 범용 워커 — 단계 스킬 실행 | 수정 금지 (재사용) |
| `~/.opal/agents/op-dev-test-agent/AGENT.md` | 기존 테스트 에이전트 — TEST-SCENARIO 기반 검증 | 수정 금지 (재사용) |
| `~/.opal/agents/opal-task-qa-agent/AGENT.md` | 기존 QA 워커 — qa_skill 동적 실행 | 수정 금지 (재사용) |
| `~/.opal/skills/opal-pilot-project-dev/SKILL.md` | oppd 현재 Phase 3 구조 (opd/opds 호출) | **수정 필요** |
| `~/.opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` | 자동 검증 루핑 전략 | 수정 불필요 (참조) |
| `~/.opal/skills/opal-pilot-project-dev/references/parallel-execution-guide.md` | 병렬 실행 전략 | 수정 불필요 (참조) |
| `~/.opal/references/opal-harness.md` | 오케스트레이터 공통 하네스 (Guards, Gates, State) | 수정 불필요 (참조) |
| `~/.opal/references/agents.md` | 에이전트 레지스트리 | **수정 필요** |
| `docs/ARCHITECTURE.md` | 시스템 아키텍처 | **수정 필요** |
| `agents/opal-task-agent/AGENT.md` | 소스 저장소 — 범용 워커 | 수정 금지 |
| `opal/skills/opal-pilot-project-dev/SKILL.md` | 소스 저장소 — oppd SKILL.md | **수정 필요** |

### 현재 상태

#### 에이전트 체계

현재 OPAL에는 4개 서브에이전트가 존재한다:

1. **opal-task-agent** (standard) — 범용 워커. 오케스트레이터가 스킬 경로를 전달하면 SKILL.md를 Read하고 프로세스를 따름. QA/Test 호출 안 함. STATE.md는 EXECUTE Step 진행 시에만 갱신.
2. **opal-task-qa-agent** (light) — QA 워커. qa_skill을 전달받아 검증 수행.
3. **op-dev-test-agent** (standard) — TEST-SCENARIO.md 기반 동적 검증. 시나리오별 실행 + 판정.
4. **wtm-agent** (light) — 웹→마크다운 변환.

모든 에이전트는 `AGENT.md` 단일 파일, YAML frontmatter(name, description, model) 포함.

#### oppd Phase 3 현재 구조

oppd SKILL.md v3.0에서 Phase 3 "액션 실행"은 다음과 같다:
- `opd/opds/opdw` 스킬을 호출하여 액션을 실행 (섹션 3-1)
- 자동 검증 루핑 (섹션 3-1a, verification-loop-guide.md 참조)
- 병렬 디스패치 (섹션 3-1b, parallel-execution-guide.md 참조)
- 액션마다 PM 검수 + 사용자 게이트

**문제점**: opd/opds는 내부에 사용자 게이트(단계 승인)가 있어 agentic 완주가 불가능하다. 또한 opd/opds 자체가 오케스트레이터여서 "오케스트레이터가 오케스트레이터를 호출하는" 중첩 패턴이 발생한다.

#### 검증 루핑 가이드

verification-loop-guide.md는 이미 L1~L3b~L4 계층적 검증을 상세히 정의하고 있다:
- L1: lint/format (재시도 무제한)
- L2: build/type (최대 2회)
- L3a: unit/integration (최대 3회)
- L3b: E2E (최대 1회)
- L4: QA Gate
- 회귀 방지 가드 포함
- 에스컬레이션 프로토콜 포함

현재 이 가이드는 **oppd 오케스트레이터가 루프를 관리하고, 워커(opal-task-agent)가 수정을 수행**하는 구조다. 새 에이전트는 이 역할을 자체적으로 수행해야 한다.

#### 병렬 실행 가이드

parallel-execution-guide.md는 worktree 격리 + Agent 병렬 디스패치를 정의한다. 이 가이드는 oppd 레벨에서 사용되며, 새 에이전트는 개별 액션 단위로 실행되므로 병렬 실행은 oppd가 계속 관리한다.

#### opds 파이프라인 (에이전트가 재현할 패턴)

opds(Short Task)는 TASK → PLAN+TEST-SCENARIO → EXECUTE 순서로 진행한다:
- PLAN: op-dev-plan 워커 디스패치 (advanced) → QA Gate → PM Gate
- TEST-SCENARIO: op-dev-test-scenario 워커 디스패치 (light)
- EXECUTE: op-dev-execute 워커 디스패치 (standard) → op-dev-test-agent 호출 → DONE.md

새 에이전트는 이 파이프라인을 **사용자 게이트 없이** 자율적으로 수행해야 한다.

#### 소스 저장소 vs 배포 경로

- 소스: `agents/` → 배포: `~/.opal/agents/`
- 소스: `opal/skills/opal-pilot-project-dev/` → 배포: `~/.opal/skills/opal-pilot-project-dev/`
- 소스: `opal/core/references/agents.md` → 배포: `~/.opal/references/agents.md`

변경은 **소스 저장소**(이 프로젝트)와 **배포 경로**(~/.opal/) 양쪽 모두에 반영해야 한다.

### 영향 범위

| 영향 대상 | 영향 내용 |
|----------|----------|
| oppd Phase 3 | opd/opds 호출 → opal-task-action-agent 디스패치로 전환 |
| agents.md 레지스트리 | 새 에이전트 등록 |
| ARCHITECTURE.md | 에이전트 목록에 추가 |
| 기존 opd/opds | 영향 없음 (수정 금지) |
| 기존 워커/에이전트 | 영향 없음 (수정 금지, 재사용만) |
| 하네스 | 영향 없음 (에이전트는 게이트 비적용) |

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| N1 | `agents/opal-task-action-agent/AGENT.md` | 소스 — 액션 에이전트 정의 |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| M1 | `opal/skills/opal-pilot-project-dev/SKILL.md` | Phase 3 "opd/opds 호출" → "opal-task-action-agent 디스패치"로 전환 |
| M2 | `opal/core/references/agents.md` | opal-task-action-agent 등록 |
| M3 | `docs/ARCHITECTURE.md` | 에이전트 테이블에 opal-task-action-agent 추가 |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| (없음) | | |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | opal-task-action-agent AGENT.md 작성 | N1 | 높음 — 핵심 에이전트 정의 |
| 2 | oppd SKILL.md Phase 3 수정 | M1 | 중간 — 기존 Phase 3 섹션 치환 |
| 3 | agents.md 레지스트리 등록 | M2 | 낮음 — 항목 추가 |
| 4 | ARCHITECTURE.md 갱신 | M3 | 낮음 — 테이블 행 추가 |

### 핵심 설계

#### N1: opal-task-action-agent AGENT.md

새 에이전트의 핵심 설계. 기존 에이전트 패턴(YAML frontmatter + 실행 프로세스 + 결과 반환 형식 + 행동 규칙)을 따른다.

**YAML frontmatter**:
```yaml
name: opal-task-action-agent
description: |
  oppd Phase 3에서 개별 액션을 자율 실행하는 에이전트.
  PLAN → QA → EXECUTE → 검증 루핑(L1~L3b) → TEST → 결과 반환.
  사용자 게이트 없이 agentic하게 파이프라인을 완주한다.
model: advanced
```

**model 선택 근거**: 에이전트 자체가 내부에서 여러 단계를 조율(오케스트레이션)해야 하므로 advanced가 적절하다. 내부 워커 디스패치 시에는 각 단계별 model을 적용한다.

**입력 명세**:
| 파라미터 | 설명 |
|---------|------|
| action_id | 액션 ID (예: A01-db-schema) |
| action_goal | 액션 목표 (ROADMAP.md에서 추출) |
| action_scope | 액션 범위 (변경 대상 파일/모듈) |
| verify_commands | 검증 명령 (lint, build, test) |
| task_folder | 액션 태스크 폴더 경로 (예: tasks/NNN/actions/A01-xxx/) |
| project_root | 프로젝트 루트 경로 |
| project_context | 참조 문서 목록 (docs/PROJECT.md, ARCHITECTURE.md, CONVENTIONS.md) |

**실행 프로세스** (6단계 파이프라인):

```
1. PLAN: opal-task-agent 디스패치 (op-dev-plan, model: advanced)
   → PLAN.md 생성
2. QA: opal-task-qa-agent 디스패치 (op-dev-qa)
   → QA-PLAN.md 생성
   → Needs Revision → opal-task-agent에 재지시 (최대 1회)
3. TEST-SCENARIO: opal-task-agent 디스패치 (op-dev-test-scenario, model: light)
   → TEST-SCENARIO.md 생성
4. EXECUTE: opal-task-agent 디스패치 (op-dev-execute, model: standard)
   → 코드 변경 + changed_files 반환
5. VERIFY: 검증 루핑 (L1~L3b)
   → L1(lint) → L2(build) → L3a(unit/integration) → L3b(E2E)
   → 실패 시 opal-task-agent에 수정 지시 (한도 내)
   → 한도 초과/회귀 시 status: failed로 반환
6. TEST: op-dev-test-agent 디스패치
   → TEST-SCENARIO.md 결과 채움 + 판정
   → Critical Fail → status: failed로 반환
```

**검증 루핑 내장 설계**:

에이전트가 자체적으로 검증 루프를 관리한다. verification-loop-guide.md의 전략을 그대로 따르되, "오케스트레이터"의 역할을 이 에이전트가 수행한다.

- L1(lint): 실패 시 opal-task-agent에 수정 디스패치 (제한 없음)
- L2(build): 실패 시 수정 디스패치 (최대 2회)
- L3a(test): 실패 시 수정 디스패치 (최대 3회, 회귀 방지 가드 적용)
- L3b(E2E): 1회 재실행 → 2연속 FAIL → failed 반환 (에스컬레이션은 oppd가 처리)
- 에스컬레이션은 이 에이전트가 직접 사용자에게 보고하지 않고, `status: failed` + 상세 사유를 oppd에 반환한다. oppd가 사용자 에스컬레이션을 담당한다.

**핵심 차이점 (opd/opds vs opal-task-action-agent)**:

| 항목 | opd/opds | opal-task-action-agent |
|------|---------|----------------------|
| 유형 | 오케스트레이터 (SKILL.md) | 에이전트 (AGENT.md) |
| 사용자 게이트 | 매 단계 승인 | 없음 — 결과만 반환 |
| 하네스 적용 | 전체 (Guards, Gates, State) | 부분 (Guards만 — 재시도 한도) |
| STATE.md | 자체 관리 | 관리 안 함 — oppd가 관리 |
| 에스컬레이션 | 사용자에게 직접 | oppd에 결과 반환 → oppd가 사용자에게 |
| 호출 주체 | 사용자 (// 커맨드) | oppd 오케스트레이터 |

**결과 반환 형식**:

```json
{
  "action_id": "A01-db-schema",
  "status": "completed | failed",
  "verdict": "All Pass | Partial Fail | Critical Fail",
  "artifact_path": "tasks/NNN/actions/A01-xxx/",
  "summary": "작업 요약 1-2줄",
  "changed_files": ["변경된 파일 경로 목록"],
  "verification_log": [
    {"layer": "L1", "attempt": "1/∞", "result": "Pass"},
    {"layer": "L2", "attempt": "1/2", "result": "Pass"},
    {"layer": "L3a", "attempt": "1/3", "result": "Pass"}
  ],
  "failure_context": null
}
```

실패 시 `failure_context`에 상세 정보를 포함한다:
```json
{
  "failure_context": {
    "layer": "L3a",
    "attempt": "3/3",
    "error_summary": "2/15 tests failed (auth.test)",
    "last_error": "AssertionError: Expected 'valid' but received 'expired'",
    "regression": false
  }
}
```

**행동 규칙**:
1. 사용자와 직접 상호작용하지 않는다 — 결과만 oppd에 반환
2. STATE.md를 갱신하지 않는다 — oppd의 책임
3. 하네스 Guards의 재시도 한도를 준수한다
4. 회귀 발생 시 즉시 중단하고 failed로 반환한다
5. 기존 워커(opal-task-agent, opal-task-qa-agent, op-dev-test-agent)를 Agent 도구로 디스패치한다
6. 각 워커 디스패치 시 프로젝트 컨텍스트(docs/PROJECT.md, ARCHITECTURE.md, CONVENTIONS.md)를 전달한다
7. 커밋하지 않는다 — oppd가 머지/커밋을 관리

#### M1: oppd SKILL.md Phase 3 수정

Phase 3 섹션에서 opd/opds 호출을 opal-task-action-agent 디스패치로 전환한다.

**주요 변경**:

1. **섹션 3-1 "실행 루프"** 수정:
   - `opd/opds/opdw 스킬 호출` → `opal-task-action-agent 디스패치`
   - 디스패치 프롬프트에 action_id, action_goal, action_scope, verify_commands 포함
   - 에이전트 결과 수신 후 처리 로직 추가 (성공 → PM 검수, 실패 → 에스컬레이션)

2. **섹션 3-1a "자동 검증 루핑"** 수정:
   - "오케스트레이터가 루프를 관리하고 워커가 수정" → "opal-task-action-agent가 자체 루핑 수행"
   - oppd는 에이전트의 verification_log를 STATE.md에 기록만 함

3. **섹션 3-1b "병렬 액션 실행"** 수정:
   - 워커 병렬 디스패치 → opal-task-action-agent 병렬 디스패치
   - 디스패치 프롬프트에 worktree 경로 포함

4. **섹션 3-2 "액션 시작/완료 보고"** 유지 (변경 불필요)

5. **스킬 탐색 경로 섹션** 수정:
   - opd/opds/opdw 탐색 경로 유지 (기존 사용자 직접 호출 시 사용)
   - opal-task-action-agent 탐색 경로 추가

6. **STATE.md 템플릿** 내 Phase 3 상태값 수정:
   - `opd/opds` → `opal-task-action-agent`

**수정하지 않는 부분**:
- Phase 1 (opwt)
- Phase 2 (PM 직접)
- PM 검수 흐름
- STATE.md 기본 구조 (병렬 실행 현황, 검증 루프 로그는 이미 정의됨)

#### M2: agents.md 레지스트리 등록

`## opal-pilot 에이전트` 섹션에 새 항목 추가:

```markdown
### opal-task-action-agent

- **역할**: 액션 에이전트 — oppd Phase 3에서 개별 액션을 자율 실행 (PLAN → QA → EXECUTE → 검증 루핑 → TEST)
- **호출 시점**: oppd Phase 3에서 액션 실행 시 디스패치
- **입력**: action_id, action_goal, action_scope, verify_commands, task_folder, project_context
- **출력**: 액션 결과 (status, verdict, verification_log, changed_files, failure_context)
```

#### M3: ARCHITECTURE.md 갱신

에이전트 테이블에 행 추가:

```markdown
| opal-task-action-agent | advanced | 액션 에이전트 — oppd Phase 3 자율 실행 |
```

서브에이전트 다이어그램에도 추가:

```
│  │  ├─ opal-task-action-agent: oppd Phase 3 액션 자율 실행  │
```

에이전트 수: 4개 → 5개

## 3. 실행 체크리스트

> 총 4개 Step

### Step 1: opal-task-action-agent AGENT.md 작성
- [x] 완료
- **파일**: `agents/opal-task-action-agent/AGENT.md`
- **작업 내용**: 위 핵심 설계(N1)에 따라 AGENT.md 신규 작성. YAML frontmatter + 입력 명세 + 6단계 실행 프로세스 + 검증 루핑 내장 로직 + 결과 반환 형식 + 행동 규칙을 포함한다.
- **완료 기준**: AGENT.md가 존재하고, YAML frontmatter(name, description, model)이 올바르며, 실행 프로세스가 PLAN → QA → EXECUTE → VERIFY → TEST 순서를 포함하고, 결과 반환 형식이 status/verdict/verification_log/failure_context를 포함한다.
- **테스트**: 파일 존재 확인 + YAML frontmatter 파싱 + 프로세스 6단계 포함 여부 + 결과 반환 형식 필드 확인
- **의존**: 없음

### Step 2: oppd SKILL.md Phase 3 수정
- [x] 완료
- **파일**: `opal/skills/opal-pilot-project-dev/SKILL.md`
- **작업 내용**: 위 핵심 설계(M1)에 따라 Phase 3 섹션을 수정한다. 섹션 3-1(실행 루프)에서 opd/opds 호출을 opal-task-action-agent 디스패치로 전환, 섹션 3-1a(검증 루핑)에서 루핑 주체를 에이전트로 변경, 섹션 3-1b(병렬 실행)에서 디스패치 대상을 에이전트로 변경, 스킬 탐색 경로에 에이전트 탐색 경로 추가.
- **완료 기준**: Phase 3에서 "opd/opds 호출" 대신 "opal-task-action-agent 디스패치"가 명시되고, 디스패치 프롬프트에 action_id/action_goal/verify_commands가 포함되며, 검증 루핑은 에이전트 자체 수행으로 변경되고, 에이전트 결과(status/verdict/verification_log) 기반 처리 로직이 존재한다.
- **테스트**: "opal-task-action-agent" 키워드 존재 확인 + Phase 1/2 미변경 확인 + 디스패치 프롬프트 형식 확인
- **의존**: Step 1

### Step 3: agents.md 레지스트리 등록
- [x] 완료
- **파일**: `opal/core/references/agents.md`
- **작업 내용**: 위 핵심 설계(M2)에 따라 "opal-pilot 에이전트" 섹션에 opal-task-action-agent 항목을 추가한다.
- **완료 기준**: agents.md에 `### opal-task-action-agent` 섹션이 존재하고, 역할/호출 시점/입력/출력이 명시되어 있다.
- **테스트**: "opal-task-action-agent" 섹션 존재 확인 + 필수 필드(역할, 호출 시점, 입력, 출력) 포함 확인
- **의존**: Step 1

### Step 4: ARCHITECTURE.md 갱신
- [x] 완료
- **파일**: `docs/ARCHITECTURE.md`
- **작업 내용**: 위 핵심 설계(M3)에 따라 에이전트 테이블에 opal-task-action-agent 행을 추가하고, 서브에이전트 다이어그램에 항목을 추가하고, 에이전트 수(4개→5개)를 갱신한다.
- **완료 기준**: 에이전트 테이블에 opal-task-action-agent 행이 존재하고, 다이어그램에 항목이 포함되며, 에이전트 수가 5개로 갱신되어 있다.
- **테스트**: "opal-task-action-agent" 테이블 행 존재 확인 + 다이어그램 항목 확인 + 에이전트 수 5개 확인
- **의존**: Step 1

## 4. QA 체크리스트

### 기능 테스트
- [ ] AGENT.md가 6단계 파이프라인(PLAN → QA → EXECUTE → VERIFY → TEST → 결과 반환)을 완전히 정의하는가
- [ ] 검증 루핑(L1~L3b)이 verification-loop-guide.md의 재시도 한도와 일치하는가 (lint 무제한, build 2회, test 3회, E2E 1회)
- [ ] 회귀 방지 가드가 명시되어 있는가
- [ ] 실패 시 구조화된 결과(status, verdict, verification_log, failure_context)를 반환하는가
- [ ] oppd SKILL.md Phase 3에서 opal-task-action-agent를 디스패치하는 프롬프트가 정의되어 있는가
- [ ] oppd가 에이전트 결과의 status/verdict에 따라 후속 처리(PM 검수, 에스컬레이션)를 수행하는가
- [ ] 병렬 디스패치 시 worktree 경로가 에이전트에 전달되는가

### 일관성 테스트
- [ ] AGENT.md의 YAML frontmatter가 기존 에이전트(opal-task-agent 등)와 동일한 형식인가
- [ ] 결과 반환 형식이 기존 에이전트의 JSON 구조와 호환되는가 (상위 호환)
- [ ] oppd Phase 1/2가 변경되지 않았는가
- [ ] 기존 opd/opds SKILL.md가 수정되지 않았는가
- [ ] agents.md 항목이 기존 에이전트와 동일한 형식인가
- [ ] ARCHITECTURE.md 에이전트 테이블이 기존 행과 동일한 형식인가
- [ ] 네이밍 컨벤션 준수: `opal-task-action-agent` (opal-task-* 패턴)

### 문서 품질
- [ ] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가
- [ ] kebab-case 파일/폴더 네이밍을 따르는가 (`opal-task-action-agent`)
- [ ] YAML frontmatter가 올바른가 (name, description, model)
- [ ] 변경이력이 포함되어 있는가

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| 에이전트 내부 오케스트레이션이 복잡하여 컨텍스트 윈도우 초과 가능 | 에이전트 실패 | model: advanced로 설정 + 각 단계를 서브에이전트로 분리하여 개별 컨텍스트 사용 |
| 검증 루핑이 에이전트 내부에서 길어지면 시간 초과 가능 | 에이전트 타임아웃 | 하네스 Guards 재시도 한도가 이미 제한하고 있음. 한도 내에서 운영 |
| oppd SKILL.md 수정 시 Phase 1/2를 실수로 변경 | oppd 기존 기능 깨짐 | Phase 3 섹션만 정확히 타겟팅하여 수정. QA에서 Phase 1/2 미변경 확인 |
| 기존 에이전트 결과 형식과 비호환 | oppd 파싱 오류 | 기존 형식(artifact_path, summary, status, changed_files)을 포함하면서 verification_log, failure_context를 확장 |
