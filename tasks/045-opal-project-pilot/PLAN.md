# PLAN: opal-project-pilot 오케스트레이터 + 범용 단계 스킬 신규 개발

> 작성일: 2026-03-29
> 입력: TASK.md
> 출력: PLAN.md

## 1. 코드 분석

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `skills/opal-pilot-dev-short/SKILL.md` | 참조 오케스트레이터 (Short Task) | 에이전트 참조 업데이트 |
| `skills/opal-pilot-dev/SKILL.md` | 참조 오케스트레이터 (Full Task) | 에이전트 참조 업데이트 |
| `skills/opal-pilot-dev-wireframe/SKILL.md` | 참조 오케스트레이터 (Wireframe) | 에이전트 참조 업데이트 |
| `skills/op-dev-plan/SKILL.md` | 참조 단계 스킬 (구조 참고) | 변경 없음 |
| `skills/op-dev-execute/SKILL.md` | 참조 단계 스킬 (구조 참고) | 변경 없음 |
| `agents/op-dev-agent/AGENT.md` | 리네이밍 대상 워커 에이전트 | 폴더 이동 + 내용 수정 |
| `opal/core/references/agents.md` | 에이전트 레지스트리 (소스) | 업데이트 |
| `~/.opal/references/opal-skills-registry.json` | 스킬 레지스트리 JSON | 신규 스킬 등록 |
| `scripts/install-mac.sh` | 배포 스크립트 | 변경 불필요 (동적 배포) |
| `CLAUDE.md` | 프로젝트 개요 | 구조도 업데이트 |
| `README.md` | 프로젝트 README | 구조도 업데이트 |
| `docs/CONVENTIONS.md` | 네이밍 규칙 | 약어 추가 |
| `docs/ARCHITECTURE.md` | 아키텍처 문서 | 구조도 업데이트 |
| `~/.opal/references/opal-harness.md` | 하네스 (공통 인프라) | 용어 테이블에 opp 추가 |
| `skills/op-dev-analysis/SKILL.md` | 실행 주체 참조 | 에이전트 참조 업데이트 |
| `skills/op-dev-test-scenario/SKILL.md` | 실행 주체 참조 | 에이전트 참조 업데이트 |
| `agents/op-dev-test-agent/AGENT.md` | op-dev-agent 참조 | 에이전트 참조 업데이트 |
| `agents/op-task-qa-agent/AGENT.md` | QA 에이전트 | 확인 필요 |

### 현재 구현

**오케스트레이터 패턴**: 모든 opal-pilot-* 오케스트레이터는 동일한 구조를 따른다:
- YAML frontmatter (name, description, triggers)
- Harness 참조 (`~/.opal/references/opal-harness.md`)
- STEP별 워커 디스패치 (스킬 경로, 태스크 폴더, 이전 산출물, model 지정)
- QA Gate / PM Gate
- STATE.md 도메인 치환값
- 변경이력

**단계 스킬 패턴**: op-dev-plan, op-dev-execute는 아래 구조:
- YAML frontmatter
- 실행 컨텍스트 (워커 에이전트에서 실행)
- 페르소나 참조
- 입력/출력 명세
- 프로세스 (Step 1~N)
- 가드레일/품질 체크리스트
- references/ 에 상세 가이드, personas/ 에 페르소나

**워커 에이전트 (op-dev-agent)**: 범용 워커로, 오케스트레이터가 전달한 스킬 SKILL.md를 Read하고 프로세스를 따른다. model 오버라이드 테이블로 단계별 모델을 지정한다.

**install-mac.sh**: `agents/` 디렉토리를 동적으로 순회하여 `~/.opal/agents/`에 배포한다. 폴더명 기반이므로 폴더만 변경하면 배포가 자동 반영된다.

### 영향 범위

**에이전트 리네이밍 영향**: op-dev-agent를 참조하는 파일이 다수 존재:
- 오케스트레이터: opal-pilot-dev, opal-pilot-dev-short (직접 참조 없음 -- 하네스가 에이전트 탐색 경로를 정의)
- 단계 스킬: op-dev-analysis, op-dev-execute, op-dev-test-scenario (실행 주체 기술)
- 에이전트: op-dev-test-agent (op-dev-agent 필드 참조)
- 레지스트리: agents.md, opal-skills-registry.json
- 문서: CLAUDE.md, README.md, docs/ARCHITECTURE.md, docs/CONVENTIONS.md
- .opal/AGENT.md (워커 예시)

**하위 호환**: 기존 op-dev-* 파이프라인이 opal-task-agent로 리네이밍된 에이전트를 사용해도 동작해야 한다. 오케스트레이터는 하네스의 에이전트 탐색 경로로 에이전트를 찾으므로, 폴더명과 에이전트 레지스트리만 업데이트하면 된다.

**신규 컴포넌트**: opal-project-pilot, op-plan, op-execute는 완전 신규이므로 기존 코드에 영향 없음.

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| N1 | `skills/opal-project-pilot/SKILL.md` | 범용 오케스트레이터 (opp) |
| N2 | `skills/op-plan/SKILL.md` | 범용 계획 스킬 |
| N3 | `skills/op-plan/references/plan-guide.md` | 범용 계획 가이드 |
| N4 | `skills/op-plan/personas/generalist-architect.md` | 범용 분석/설계 페르소나 |
| N5 | `skills/op-execute/SKILL.md` | 범용 실행 스킬 |
| N6 | `skills/op-execute/references/execute-guide.md` | 범용 실행 가이드 |
| N7 | `skills/op-execute/personas/generalist-executor.md` | 범용 실행 페르소나 |
| N8 | `agents/opal-task-agent/AGENT.md` | 리네이밍된 범용 워커 에이전트 |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| M1 | `opal/core/references/agents.md` | op-dev-agent → opal-task-agent 리네이밍, 신규 에이전트 설명 추가 |
| M2 | `skills/op-dev-analysis/SKILL.md` | 실행 주체: op-dev-agent → opal-task-agent |
| M3 | `skills/op-dev-execute/SKILL.md` | 실행 주체: op-dev-agent → opal-task-agent |
| M4 | `skills/op-dev-test-scenario/SKILL.md` | op-dev-agent → opal-task-agent (실행 주체 + 담당 필드) |
| M5 | `skills/op-dev-test-scenario/references/test-scenario-guide.md` | op-dev-agent → opal-task-agent |
| M6 | `agents/op-dev-test-agent/AGENT.md` | op-dev-agent → opal-task-agent |
| M7 | `CLAUDE.md` | 소스 구조도에 신규 컴포넌트 추가, op-dev-agent → opal-task-agent |
| M8 | `README.md` | 에이전트 테이블 + 구조도 업데이트 |
| M9 | `docs/CONVENTIONS.md` | opp 약어 추가, 에이전트 네이밍 예시 업데이트 |
| M10 | `docs/ARCHITECTURE.md` | 아키텍처 다이어그램 + 에이전트 테이블 업데이트 |
| M11 | `.opal/AGENT.md` | 워커 설명에서 op-dev-agent → opal-task-agent |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| D1 | `agents/op-dev-agent/AGENT.md` | opal-task-agent로 대체 |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | 범용 워커 에이전트 생성 (리네이밍) | N8 | 보통 |
| 2 | 레거시 에이전트 삭제 | D1 | 쉬움 |
| 3 | 범용 계획 스킬 생성 | N2, N3, N4 | 어려움 |
| 4 | 범용 실행 스킬 생성 | N5, N6, N7 | 어려움 |
| 5 | 오케스트레이터 생성 | N1 | 보통 |
| 6 | 에이전트 레지스트리 업데이트 | M1 | 쉬움 |
| 7 | 기존 스킬 에이전트 참조 업데이트 | M2, M3, M4, M5 | 쉬움 |
| 8 | 기존 에이전트 참조 업데이트 | M6 | 쉬움 |
| 9 | 프로젝트 문서 업데이트 | M7, M8, M9, M10, M11 | 보통 |

### 핵심 설계

#### opal-project-pilot (opp) 오케스트레이터

```yaml
---
name: opal-project-pilot
description: |
  **범용 프로젝트 오케스트레이터**. 코드도 순수 문서도 아닌 범용 태스크를 3단계 파이프라인으로 수행한다.
  반드시 이 스킬을 사용해야 하는 상황: "opal-project-pilot", "opp".
---
```

- 3단계: TASK → PLAN → EXECUTE
- Harness 준수 (Guards, Gates, State)
- TASK: op-task 스킬 재활용 (하네스 TASK 공통 프로세스)
- PLAN: op-plan 워커 디스패치, model: opus
- EXECUTE: op-execute 워커 디스패치, model: sonnet
- TEST-SCENARIO: 없음 (범용 작업은 코드 테스트 불필요)
- DONE.md 생성
- STATE.md 도메인 치환값: 모드=Project Task, 단계=TASK/PLAN/EXECUTE, 산출물=TASK.md,PLAN.md,QA-*.md,DONE.md

#### op-plan 범용 계획 스킬

```yaml
---
name: op-plan
description: |
  **범용 계획 수립 스킬**. TASK.md를 분석하여 도메인 무관 실행 계획(PLAN.md)을 작성한다.
  반드시 이 스킬을 사용해야 하는 상황: 오케스트레이터(opal-project-pilot)가 PLAN 단계를 디스패치할 때.
---
```

**op-dev-plan과의 핵심 차이점**:

| 항목 | op-dev-plan | op-plan |
|------|------------|---------|
| 도메인 | 코드 개발 (FE/BE) | 도메인 무관 (문서, 코드, 설정 등) |
| ANALYSIS.md 분기 | 있음/없음에 따라 분석 깊이 변동 | 없음 (항상 직접 조사) |
| execution-plan.json | FE/BE 시 생성 | 생성하지 않음 |
| 영역 태그 | [FE]/[BE]/[공통] | 없음 |
| 복잡도 판별 | 단순/복잡 모드 + 실행 아키텍처 | 없음 (항상 direct 실행) |
| 기술 컨텍스트 | 커뮤니티 스킬 + MCP 매칭 | 필요 시 자유 조사 |
| 분석 수단 | Glob/Grep/Read (코드 중심) | 모든 수단 (코드, 문서, 웹검색, 스킬검색 등) |
| 페르소나 | software-architect | generalist-architect (범용 분석/설계) |

**프로세스**:
1. 가이드 로딩 (references/plan-guide.md)
2. 현황 조사 -- 모든 수단 동원 (Glob/Grep/Read, WebSearch, 기존 스킬/문서 참조)
3. 구현 범위 확정 (신규/수정/삭제 파일 테이블)
4. 구현 순서 결정 (의존성 기반)
5. 핵심 설계 (파일별 변경 내용 명세)
6. 실행 체크리스트 작성 (Step별 파일/작업/완료기준/테스트)
7. QA 체크리스트 작성
8. PLAN.md 작성

**PLAN.md 출력 형식** (op-dev-plan 대비 간소화):

```markdown
# PLAN: {제목}

> 작성일: YYYY-MM-DD
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사
### 관련 파일
| 파일 | 역할 | 변경 필요 |
### 현재 상태
{조사 결과 요약}
### 영향 범위
{변경 영향 분석}

## 2. 구현 계획
### 파일 변경 계획
#### 신규 생성 / 수정 / 삭제
### 구현 순서
| 순서 | 작업 | 파일 | 예상 난이도 |
### 핵심 설계
{파일별 변경 내용 명세}

## 3. 실행 체크리스트
> 총 {N}개 Step
### Step 1: {작업 제목}
- [ ] 완료
- **파일**: {대상}
- **작업 내용**: {구체적}
- **완료 기준**: {검증 가능}
- **테스트**: {검증 방법}
- **의존**: {선행 Step 또는 "없음"}

## 4. QA 체크리스트
### 기능 테스트
### 일관성 테스트
### 문서 품질

## 5. 리스크 및 대응
| 리스크 | 영향 | 대응 방안 |
```

#### op-execute 범용 실행 스킬

```yaml
---
name: op-execute
description: |
  **범용 실행 스킬**. PLAN.md의 실행 체크리스트를 따라 파일 작성/수정/삭제를 수행한다.
  반드시 이 스킬을 사용해야 하는 상황: 오케스트레이터(opal-project-pilot)가 EXECUTE 단계를 디스패치할 때.
---
```

**op-dev-execute와의 핵심 차이점**:

| 항목 | op-dev-execute | op-execute |
|------|---------------|------------|
| 도메인 | 코드 개발 (FE/BE) | 도메인 무관 |
| 페르소나 | FE/BE 전환 | generalist-executor (단일) |
| execution-plan.json | 지원 | 미사용 |
| ui-designer 연동 | FE 화면 구현 위임 | 없음 |
| 보안 가드레일 | SQL Injection, 하드코딩 시크릿 등 | 없음 (범용이므로) |
| FE/BE 병렬 | 지원 | 없음 (순차 실행) |
| 영역 침범 금지 | FE/BE 워커 분리 | 없음 |
| 실행 모드 | 단순/복잡 (서브에이전트 배치) | 단일 모드 (순차 direct) |

**프로세스**:
1. 실행 가이드 로딩 (references/execute-guide.md)
2. 체크리스트 확인 (PLAN.md 섹션 3)
3. Step 순서대로 실행 (파일 작성/수정/삭제)
4. 체크리스트 갱신 (체크박스 업데이트)
5. QA 체크리스트 자체 검증
6. 결과 반환

**가드레일** (범용 단순화):
- PLAN.md에 없는 파일 생성/수정 금지
- 블로커 발생 시 즉시 중단 + 보고

#### opal-task-agent 에이전트 (리네이밍)

```yaml
---
name: opal-task-agent
description: |
  op/op-dev 단계 스킬을 독립 컨텍스트에서 실행하는 범용 워커 에이전트.
  오케스트레이터가 단계 스킬 경로를 전달하면, 해당 SKILL.md를 Read하고 프로세스를 따른다.
model: sonnet
---
```

기존 op-dev-agent에서 변경:
- name: op-dev-agent → opal-task-agent
- 제목: op-dev-agent (범용 워커) → opal-task-agent (범용 워커)
- model 오버라이드 테이블에 op-plan, op-execute 추가
- 기존 op-dev-* 매핑 유지 (하위 호환)

### 의존성 및 환경 변경

없음. 마크다운 문서와 셸 스크립트만 변경.

### 테스트 전략

- 문서 전용 작업이므로 코드 테스트 없음
- QA 체크리스트로 문서 품질/일관성 검증
- install-mac.sh 실행하여 배포 정상 확인 (수동)

## 3. 실행 체크리스트

> 총 9개 Step

### Step 1: opal-task-agent 에이전트 생성

- [x] 완료
- **파일**: `agents/opal-task-agent/AGENT.md`
- **작업 내용**: op-dev-agent 기반으로 opal-task-agent AGENT.md 작성. name/제목을 opal-task-agent로 변경. model 오버라이드 테이블에 op-plan(opus), op-execute(sonnet) 추가. 기존 op-dev-* 매핑 유지.
- **완료 기준**: AGENT.md가 YAML frontmatter + 실행 프로세스 + model 테이블을 포함
- **테스트**: Read하여 구조 확인
- **의존**: 없음

### Step 2: 레거시 에이전트 삭제

- [x] 완료
- **파일**: `agents/op-dev-agent/` (폴더 전체)
- **작업 내용**: op-dev-agent 폴더 삭제
- **완료 기준**: `agents/op-dev-agent/` 디렉토리 미존재
- **테스트**: `ls agents/` 확인
- **의존**: Step 1

### Step 3: op-plan 범용 계획 스킬 생성

- [x] 완료
- **파일**: `skills/op-plan/SKILL.md`, `skills/op-plan/references/plan-guide.md`, `skills/op-plan/personas/generalist-architect.md`
- **작업 내용**: op-dev-plan을 참고하되 도메인 특화 로직(FE/BE 영역 태그, execution-plan.json, 복잡도 판별, 실행 아키텍처, 기술 컨텍스트 스킬 매핑)을 제거한 범용 계획 스킬 작성. 모든 수단을 동원한 현황 조사, 간소화된 PLAN.md 형식, 범용 QA 체크리스트 포함. 페르소나는 generalist-architect (범용 분석/설계 전문가).
- **완료 기준**: SKILL.md + plan-guide.md + generalist-architect.md 3개 파일 존재. SKILL.md가 YAML frontmatter, 프로세스, 출력 형식, 품질 체크리스트를 포함.
- **테스트**: Read하여 op-dev-plan과 비교, FE/BE 특화 로직 미포함 확인
- **의존**: 없음

### Step 4: op-execute 범용 실행 스킬 생성

- [x] 완료
- **파일**: `skills/op-execute/SKILL.md`, `skills/op-execute/references/execute-guide.md`, `skills/op-execute/personas/generalist-executor.md`
- **작업 내용**: op-dev-execute를 참고하되 도메인 특화 로직(FE/BE 페르소나 전환, execution-plan.json, ui-designer 연동, 보안 가드레일, FE/BE 병렬, 실행 모드 분기)을 제거한 범용 실행 스킬 작성. 순차 직접 실행, 범용 가드레일, 체크리스트 갱신 포함. 페르소나는 generalist-executor (범용 실행 전문가).
- **완료 기준**: SKILL.md + execute-guide.md + generalist-executor.md 3개 파일 존재. SKILL.md가 YAML frontmatter, 프로세스, 가드레일, 품질 체크리스트를 포함.
- **테스트**: Read하여 op-dev-execute와 비교, FE/BE 특화 로직 미포함 확인
- **의존**: 없음

### Step 5: opal-project-pilot 오케스트레이터 생성

- [x] 완료
- **파일**: `skills/opal-project-pilot/SKILL.md`
- **작업 내용**: opal-pilot-dev-short를 참고하여 범용 3단계 오케스트레이터 작성. TASK(op-task 재활용) → PLAN(op-plan 워커 디스패치, opus) → EXECUTE(op-execute 워커 디스패치, sonnet). TEST-SCENARIO 없음. 하네스 준수. STATE.md 도메인 치환값 정의.
- **완료 기준**: SKILL.md가 YAML frontmatter, 3단계 파이프라인, STATE.md 치환값, 변경이력을 포함
- **테스트**: Read하여 opal-pilot-dev-short 구조와 비교
- **의존**: Step 3, Step 4

### Step 6: 에이전트 레지스트리 업데이트

- [x] 완료
- **파일**: `opal/core/references/agents.md`
- **작업 내용**: op-dev-agent → opal-task-agent 리네이밍. opal-project-pilot 오케스트레이터의 에이전트 사용 설명 추가.
- **완료 기준**: opal-task-agent 섹션이 존재하고, op-dev-agent 참조가 없음
- **테스트**: Grep으로 op-dev-agent 잔여 확인
- **의존**: Step 1

### Step 7: 기존 스킬의 에이전트 참조 업데이트

- [x] 완료
- **파일**: `skills/op-dev-analysis/SKILL.md`, `skills/op-dev-execute/SKILL.md`, `skills/op-dev-test-scenario/SKILL.md`, `skills/op-dev-test-scenario/references/test-scenario-guide.md`
- **작업 내용**: 각 파일에서 op-dev-agent → opal-task-agent로 치환
- **완료 기준**: 4개 파일에서 op-dev-agent 참조 없음
- **테스트**: Grep으로 skills/ 내 op-dev-agent 잔여 확인
- **의존**: Step 1

### Step 8: 기존 에이전트의 참조 업데이트

- [x] 완료
- **파일**: `agents/op-dev-test-agent/AGENT.md`
- **작업 내용**: op-dev-agent → opal-task-agent로 치환
- **완료 기준**: op-dev-agent 참조 없음
- **테스트**: Grep으로 agents/ 내 op-dev-agent 잔여 확인
- **의존**: Step 1

### Step 9: 프로젝트 문서 업데이트

- [x] 완료
- **파일**: `CLAUDE.md`, `README.md`, `docs/CONVENTIONS.md`, `docs/ARCHITECTURE.md`, `.opal/AGENT.md`
- **작업 내용**: (1) 소스 구조도에 opal-project-pilot, op-plan, op-execute, opal-task-agent 추가. (2) op-dev-agent → opal-task-agent 치환. (3) CONVENTIONS.md에 opp 약어 추가, 에이전트 네이밍 예시에 opal-task-agent 추가. (4) ARCHITECTURE.md 다이어그램과 에이전트 테이블 업데이트.
- **완료 기준**: 5개 파일에서 op-dev-agent 참조 없음. 신규 컴포넌트가 문서에 반영됨.
- **테스트**: Grep으로 전체 프로젝트에서 op-dev-agent 잔여 확인 (tasks/ 제외)
- **의존**: Step 1, Step 5

## 4. QA 체크리스트

### 기능 테스트
- [x] opal-project-pilot SKILL.md가 3단계 파이프라인(TASK→PLAN→EXECUTE)을 정의하는가
- [x] op-plan SKILL.md가 도메인 무관 계획 수립 프로세스를 정의하는가
- [x] op-execute SKILL.md가 도메인 무관 실행 프로세스를 정의하는가
- [x] opal-task-agent AGENT.md가 op-plan, op-execute를 model 테이블에 포함하는가
- [x] opal-task-agent가 기존 op-dev-* 스킬 매핑을 유지하는가 (하위 호환)

### 일관성 테스트
- [x] op-dev-agent 참조가 tasks/ 외에 남아있지 않은가
- [x] 신규 컴포넌트가 CLAUDE.md, README.md, CONVENTIONS.md, ARCHITECTURE.md에 반영되었는가
- [x] agents.md 레지스트리에 opal-task-agent가 등록되었는가
- [ ] 하네스(opal-harness.md) 용어 테이블에 opp가 추가되었는가 — PLAN 방침: 하네스 수정 없이 opal-project-pilot SKILL.md에서 자체 정의 (리스크 섹션 참조)

### 문서 품질
- [x] 모든 SKILL.md가 YAML frontmatter(name, description)를 포함하는가
- [x] 모든 AGENT.md가 YAML frontmatter(name, description, model)를 포함하는가
- [x] opal-doc-standard v2.0 규칙(헤더, 변경이력)을 준수하는가 — op-plan, op-execute, opal-project-pilot에 변경이력 포함
- [x] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가
- [x] kebab-case 파일/폴더 네이밍을 따르는가

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| op-dev-agent 참조 누락 | 기존 파이프라인 에이전트 탐색 실패 | Grep으로 전체 프로젝트 스캔하여 잔여 참조 치환 |
| op-plan/op-execute 설계 과소 | 범용성 부족으로 특정 작업 유형에서 부적합 | op-dev-plan/op-dev-execute를 참조하되, 도메인 특화 로직만 제거하고 범용 확장 포인트를 남김 |
| install-mac.sh 배포 문제 | 새 에이전트/스킬 미배포 | install-mac.sh가 동적 배포이므로 폴더만 올바르면 자동 반영. 수동 테스트로 확인 |
| 하네스 용어 테이블 업데이트 누락 | opp 약어 미인식 | 하네스는 수정하지 않되, 오케스트레이터 SKILL.md에서 약어를 자체 정의 |
