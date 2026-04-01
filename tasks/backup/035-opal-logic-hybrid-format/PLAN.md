# PLAN: opal-logic 하이브리드 포맷 PoC

> 작성일: 2026-03-28
> 입력: TASK.md
> 출력: PLAN.md

## 1. 코드 분석

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `skills/dtp-todo/SKILL.md` | 실행 체크리스트 확장 스킬 — 복잡도 판별 로직(76~91행) | 수정 |
| `skills/otp-dev/SKILL.md` | Full Task 오케스트레이터 — 파이프라인 정의(28~36행) + 6개 STEP 디스패치(40~176행) | 수정 |
| `skills/dtp-qa/SKILL.md` | QA 검증 스킬 — 가이드 로딩 분기(43~52행) + 판정 기준(150~156행) | 수정 |
| `skills/otp-dev-short/SKILL.md` | Short Task 오케스트레이터 — 에스컬레이션 규칙(132~151행) | 수정 |
| `opal/core/AGENT.md` | 글로벌 에이전트 정의 — 행동 규칙 섹션 | 수정 |
| `skills/opal-logic/SCHEMA.md` | opal-logic 스키마 정의 문서 | 신규 |

### 현재 구현

**dtp-todo (복잡도 판별)**:
- Step 4에서 5가지 기준(Step 수, 변경 파일 수, 모듈 범위, 작업 유형, 외부 의존성)의 마크다운 테이블로 서술
- "하나라도 복잡 모드 기준에 해당하면 복잡 모드 적용" — OR 논리가 자연어로만 표현됨
- 결과: 단순 모드(direct) vs 복잡 모드(Part C 진행)

**otp-dev (파이프라인 + 디스패치)**:
- 파이프라인: `dtp-task → dtp-analysis → [QA] → dtp-plan → [QA] → dtp-todo → dtp-test-scenario → dtp-execute → [Test]`
- 각 STEP이 독립 섹션으로 서술, 디스패치 프롬프트 템플릿/모델/후속 동작이 마크다운으로 분산
- STATE.md 관리 섹션에 이벤트별 갱신 규칙이 테이블로 존재
- 상태 전이 규칙이 암묵적 (섹션 순서 = 전이 순서)

**dtp-qa (가이드 로딩 + 판정)**:
- Step 1: stage → 가이드 파일 매핑이 4행 마크다운 테이블
- Step 2: stage + mode → 읽어야 하는 파일 목록이 5행 마크다운 테이블
- 판정: `Critical >= 1 OR Warning >= 3` → Needs Revision, 그 외 Pass — 2행 테이블

**otp-dev-short (에스컬레이션)**:
- 3가지 조건(변경 파일 >= 10, 다단계 기술 의사결정, 다중 모듈 연쇄 영향)의 마크다운 테이블
- OR 판정이 자연어 설명에 내재

**AGENT.md (메타 지시)**:
- "행동 규칙" 섹션에 쌍슬래시 커맨드, 주도성, 기억과 학습, 보고 형식이 존재
- opal-logic 관련 지시 없음 — 추가 필요

### 영향 범위

- **하위 호환 보장**: 기존 마크다운 서술을 제거하지 않으므로, opal-logic 블록을 해석하지 못하는 에이전트도 기존 서술로 동작 가능
- **opal-logic 블록이 없는 스킬**: dtp-task, dtp-analysis, dtp-plan, dtp-execute, dtp-test-scenario 등은 영향 없음
- **AGENT.md 변경**: 모든 세션에서 로드되므로 opal-logic 해석 메타 지시가 전역 적용됨
- **install-mac.sh**: skills/opal-logic/ 디렉토리를 ~/.opal/skills/로 배포하려면 설치 스크립트에 등록 필요 (이번 범위 밖이나 리스크로 기록)

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| 1 | `skills/opal-logic/SCHEMA.md` | opal-logic 6가지 type 스키마 정의 문서 |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 2 | `skills/dtp-todo/SKILL.md` | Step 4 복잡도 판별 테이블 직후에 decision-matrix YAML 블록 추가 |
| 3 | `skills/otp-dev/SKILL.md` | 파이프라인 섹션 뒤에 state-machine + dispatch-map YAML 블록 추가 |
| 4 | `skills/dtp-qa/SKILL.md` | Step 1 가이드 로딩 테이블 뒤에 conditional-load, 판정 기준 뒤에 decision-matrix 블록 추가 |
| 5 | `skills/otp-dev-short/SKILL.md` | 에스컬레이션 규칙 테이블 뒤에 decision-matrix YAML 블록 추가 |
| 6 | `opal/core/AGENT.md` | 행동 규칙 섹션에 "opal-logic 블록 해석" 서브섹션 추가 |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | 스키마 정의 문서 작성 (6가지 type의 구조, 필수/선택 필드, 예제) | `skills/opal-logic/SCHEMA.md` | 보통 |
| 2 | AGENT.md에 opal-logic 해석 메타 지시 추가 | `opal/core/AGENT.md` | 쉬움 |
| 3 | dtp-todo에 decision-matrix 블록 추가 | `skills/dtp-todo/SKILL.md` | 쉬움 |
| 4 | otp-dev에 state-machine + dispatch-map 블록 추가 | `skills/otp-dev/SKILL.md` | 보통 |
| 5 | dtp-qa에 conditional-load + decision-matrix 블록 추가 | `skills/dtp-qa/SKILL.md` | 쉬움 |
| 6 | otp-dev-short에 decision-matrix 블록 추가 | `skills/otp-dev-short/SKILL.md` | 쉬움 |

**순서 근거**: 스키마(1)가 모든 YAML 블록의 기반이므로 먼저 작성. AGENT.md(2)는 해석 규칙이므로 스킬 수정 전에 정의. 이후 각 스킬 수정(3~6)은 독립적이므로 순서가 유연하나, 가장 명확한 dtp-todo → 가장 복잡한 otp-dev → 나머지 순으로 진행.

### 핵심 설계

#### opal-logic 블록 형식

마크다운 코드 블록 내에 YAML로 배치한다. 태그 형식으로 type을 선언한다:

````markdown
```yaml #opal-logic:{type}
id: {고유 식별자}
description: {블록 설명}
# ... type별 필드
```
````

#### 6가지 type 스키마 요약

**conditional-load**: 조건에 따라 파일 Read
```yaml
# 필수: id, description, conditions (배열)
# conditions[].when: 조건식
# conditions[].load: 로드할 파일 경로
# default_load: 기본 로드 (선택)
```

**decision-matrix**: 다중 기준 판정 (OR/AND)
```yaml
# 필수: id, description, operator (or/and), criteria (배열)
# criteria[].name: 기준명
# criteria[].condition: 조건식
# result.true: 판정 결과 (조건 충족)
# result.false: 판정 결과 (조건 미충족)
```

**input-priority**: 입력 소스 우선순위
```yaml
# 필수: id, description, sources (배열, 우선순위순)
# sources[].name: 소스명
# sources[].path: 경로 패턴
# sources[].fallback: 다음 소스 지시
```

**state-machine**: 파이프라인 상태 전이
```yaml
# 필수: id, description, initial, states (객체)
# states.{name}.transitions (배열)
# transitions[].event: 전이 트리거
# transitions[].target: 대상 상태
# transitions[].guard: 전이 조건 (선택)
```

**dispatch-map**: 오케스트레이터 디스패치 규칙
```yaml
# 필수: id, description, stages (배열)
# stages[].name: 단계명
# stages[].skill: 실행 스킬
# stages[].agent: 실행 에이전트 (선택)
# stages[].model: 사용 모델
# stages[].inputs: 입력 목록
# stages[].output: 산출물
# stages[].post_actions: 후속 동작 (배열)
```

**dag**: 의존성 그래프 구성 규칙
```yaml
# 필수: id, description, nodes (배열)
# nodes[].id: 노드 ID
# nodes[].task: 작업 설명
# nodes[].depends_on: 선행 노드 ID 배열
# execution_strategy: sequential / parallel-max / batch
```

#### dtp-todo decision-matrix 블록 설계

88행 "하나라도 복잡 모드 기준에 해당하면..." 문장 뒤에 삽입:

```yaml #opal-logic:decision-matrix
id: todo-complexity
description: TODO 복잡도 판별 — 5기준 OR
operator: or
criteria:
  - name: step_count
    condition: "part_a.steps >= 6"
  - name: file_count
    condition: "part_a.changed_files >= 4"
  - name: module_scope
    condition: "part_a.modules >= 2"
  - name: work_type
    condition: "task.type in [new_feature, large_improvement]"
  - name: external_deps
    condition: "task.new_dependencies > 0"
result:
  true: complex    # Step 5(Part C) 진행
  false: simple    # 모든 Step direct
```

#### otp-dev state-machine 블록 설계

파이프라인 코드 블록 직후에 삽입:

```yaml #opal-logic:state-machine
id: full-task-pipeline
description: Full Task 7단계 파이프라인 상태 전이
initial: TASK
states:
  TASK:
    transitions:
      - event: task_complete
        target: ANALYSIS
  ANALYSIS:
    transitions:
      - event: analysis_complete
        target: ANALYSIS_QA
  ANALYSIS_QA:
    transitions:
      - event: qa_pass
        target: PLAN
      - event: qa_fail
        target: ANALYSIS
  PLAN:
    transitions:
      - event: plan_complete
        target: PLAN_QA
  PLAN_QA:
    transitions:
      - event: qa_pass
        target: TODO
      - event: qa_fail
        target: PLAN
  TODO:
    transitions:
      - event: todo_approved
        target: TEST_SCENARIO
  TEST_SCENARIO:
    transitions:
      - event: scenario_approved
        target: EXECUTE
  EXECUTE:
    transitions:
      - event: execute_complete
        target: TEST
  TEST:
    transitions:
      - event: test_pass
        target: DONE
      - event: test_fail
        target: EXECUTE
  DONE:
    terminal: true
  BLOCKED:
    transitions:
      - event: unblock
        target: "{previous_state}"
```

#### otp-dev dispatch-map 블록 설계

state-machine 블록 바로 뒤에 삽입:

```yaml #opal-logic:dispatch-map
id: full-task-dispatch
description: Full Task 단계별 디스패치 규칙
stages:
  - name: TASK
    skill: dtp-task
    agent: null          # 오케스트레이터 직접 수행
    model: null
    inputs: [user_request]
    output: TASK.md
    post_actions: [create_state_md]
  - name: ANALYSIS
    skill: dtp-analysis
    agent: dtp-worker
    model: haiku
    inputs: [TASK.md]
    output: ANALYSIS.md
    post_actions: [qa, pm_review]
  - name: PLAN
    skill: dtp-plan
    agent: dtp-worker
    model: opus
    inputs: [TASK.md, ANALYSIS.md]
    output: [PLAN.md, "execution-plan.json?"]
    post_actions: [qa, pm_review]
  - name: TODO
    skill: dtp-todo
    agent: dtp-worker
    model: haiku
    inputs: [TASK.md, ANALYSIS.md, PLAN.md]
    output: TODO.md
    post_actions: [user_approval]
  - name: TEST_SCENARIO
    skill: dtp-test-scenario
    agent: dtp-worker
    model: haiku
    inputs: [TASK.md, PLAN.md, TODO.md]
    output: TEST-SCENARIO.md
    post_actions: [user_approval]
  - name: EXECUTE
    skill: dtp-execute
    agent: dtp-worker
    model: sonnet
    inputs: [TODO.md, "execution-plan.json?"]
    output: changed_files
    post_actions: [test, done_md]
```

#### dtp-qa conditional-load 블록 설계

Step 1 가이드 로딩 테이블(52행) 직후에 삽입:

```yaml #opal-logic:conditional-load
id: qa-guide-loader
description: 단계별 QA 참조 가이드 선택
conditions:
  - when: "stage in [ANALYSIS, PLAN]"
    load: "~/.opal/skills/dtp-qa/references/qa-dev-guide.md"
  - when: "stage in [WIREFRAME, EXECUTE-UI]"
    load: "~/.opal/skills/dtp-qa/references/qa-wireframe-guide.md"
```

#### dtp-qa decision-matrix 블록 설계

판정 기준 테이블(156행) 직후에 삽입:

```yaml #opal-logic:decision-matrix
id: qa-verdict
description: QA 판정 — Critical/Warning 기반
operator: or
criteria:
  - name: critical_exists
    condition: "count(results, severity == 'critical') >= 1"
  - name: warning_excess
    condition: "count(results, severity == 'warning') >= 3"
result:
  true: needs_revision
  false: pass
```

#### otp-dev-short decision-matrix 블록 설계

에스컬레이션 규칙 테이블(141행) 직후에 삽입:

```yaml #opal-logic:decision-matrix
id: short-escalation
description: Short → Full 에스컬레이션 판정
operator: or
criteria:
  - name: file_count
    condition: "plan.changed_files >= 10"
  - name: tech_decisions
    condition: "plan.requires_architecture_choice == true"
  - name: module_impact
    condition: "plan.impacted_independent_modules >= 3"
result:
  true: escalate_to_full
  false: continue_short
```

#### AGENT.md 메타 지시 설계

"행동 규칙" 섹션 내 "보고 형식" 서브섹션 뒤에 신규 서브섹션 추가:

```markdown
### opal-logic 블록 해석

SKILL.md 내 `yaml #opal-logic:{type}` 코드 블록은 프로세스 규칙의 구조화 선언이다.
이 블록을 만나면:

1. YAML을 파싱하여 조건/규칙을 확인한다
2. 현재 컨텍스트 값으로 규칙을 평가한다
3. 평가 결과에 따라 프로세스를 진행한다
4. `opal-logic-engine` MCP가 있으면 도구로 평가, 없으면 직접 해석

**하위 호환**: opal-logic 블록이 없는 스킬은 기존 서술형 마크다운만으로 동작한다. opal-logic 블록은 서술형 마크다운을 대체하지 않고 보충한다.
```

### 의존성 및 환경 변경

- 추가 패키지: 없음 (문서 기반 작업)
- 환경 설정 변경: 없음
- install-mac.sh: `skills/opal-logic/` 디렉토리를 `~/.opal/skills/`로 복사하는 항목 추가 필요 (이번 태스크 범위 밖, 후속 태스크로 처리)

### 테스트 전략

| 테스트 종류 | 대상 | 성공 기준 |
|------------|------|----------|
| YAML 문법 검증 | 각 SKILL.md의 opal-logic 블록 | 유효한 YAML로 파싱 가능 |
| 하위 호환 검증 | 수정된 SKILL.md | 기존 마크다운 서술이 그대로 존재 |
| 비영향 검증 | opal-logic 블록 없는 스킬 | dtp-task, dtp-analysis, dtp-plan 등 변경 없음 |
| 스키마 정합성 | 각 블록 vs SCHEMA.md | 블록이 스키마의 필수 필드를 모두 포함 |
| 논리 정확성 | decision-matrix 블록 | OR 조건, 결과값이 기존 서술형 로직과 일치 |

## 3. 실행 체크리스트

- [ ] Step 1: 스키마 문서 생성 -- `skills/opal-logic/SCHEMA.md` -- 6가지 type(conditional-load, decision-matrix, input-priority, state-machine, dispatch-map, dag)의 구조, 필수/선택 필드, 예제를 정의
- [ ] Step 2: AGENT.md 메타 지시 추가 -- `opal/core/AGENT.md` -- 행동 규칙 섹션에 "opal-logic 블록 해석" 서브섹션 추가 (보고 형식 뒤)
- [ ] Step 3: dtp-todo decision-matrix 추가 -- `skills/dtp-todo/SKILL.md` -- Step 4 복잡도 판별 88행 직후에 decision-matrix YAML 블록 삽입
- [ ] Step 4: otp-dev state-machine + dispatch-map 추가 -- `skills/otp-dev/SKILL.md` -- 파이프라인 섹션(36행) 뒤에 state-machine 블록, 이어서 dispatch-map 블록 삽입
- [ ] Step 5: dtp-qa conditional-load + decision-matrix 추가 -- `skills/dtp-qa/SKILL.md` -- Step 1 테이블(52행) 뒤에 conditional-load 블록, 판정 기준 테이블(156행) 뒤에 decision-matrix 블록 삽입
- [ ] Step 6: otp-dev-short decision-matrix 추가 -- `skills/otp-dev-short/SKILL.md` -- 에스컬레이션 규칙 테이블(141행) 뒤에 decision-matrix 블록 삽입
- [ ] Step 7: 전체 YAML 문법 + 하위 호환 검증 -- 모든 수정 파일 -- 기존 마크다운 서술 보존 확인, YAML 파싱 가능 확인

## 4. QA 체크리스트

### 기능 테스트
- [ ] SCHEMA.md가 6가지 type을 모두 정의하는가
- [ ] dtp-todo의 decision-matrix가 5가지 기준 OR을 정확히 표현하는가
- [ ] otp-dev의 state-machine이 파이프라인의 모든 상태 전이를 포함하는가
- [ ] otp-dev의 dispatch-map이 6개 STEP의 스킬/모델/입출력을 정확히 반영하는가
- [ ] dtp-qa의 conditional-load가 4개 stage-guide 매핑을 포함하는가
- [ ] dtp-qa의 decision-matrix가 Critical >= 1 OR Warning >= 3 판정을 표현하는가
- [ ] otp-dev-short의 decision-matrix가 3가지 에스컬레이션 조건 OR을 표현하는가
- [ ] AGENT.md에 opal-logic 해석 지시가 추가되었는가

### 회귀 테스트
- [ ] 기존 마크다운 서술(테이블, 문장)이 그대로 보존되는가 (모든 수정 파일)
- [ ] opal-logic 블록이 없는 스킬(dtp-task, dtp-analysis, dtp-plan, dtp-execute, dtp-test-scenario)에 변경이 없는가
- [ ] AGENT.md의 기존 행동 규칙이 변경되지 않았는가

### 코드 품질
- [ ] 모든 YAML 블록이 유효한 YAML 문법인가
- [ ] opal-logic 블록이 SCHEMA.md의 필수 필드를 모두 포함하는가
- [ ] 블록의 id가 프로젝트 내 유일한가
- [ ] 한국어 주석과 description이 명확한가

## 5. 기술 컨텍스트

### 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 문서 포맷 | Markdown | 해당 없음 (기본) |
| 구조화 데이터 | YAML | 해당 없음 (기본) |

### 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| 해당 없음 | 문서 기반 작업이므로 MCP 불필요 |

## 6. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| YAML 블록이 마크다운 렌더링 시 가독성 저하 | 사람이 SKILL.md를 읽을 때 복잡해 보임 | 블록 전후에 구분선(---) 삽입, 블록 상단에 한국어 주석 추가 |
| opal-logic 블록과 서술형 로직 불일치 | LLM이 상충하는 지시를 받을 수 있음 | 블록은 서술의 정확한 구조화여야 함. QA에서 교차 검증 |
| install-mac.sh에 opal-logic 미등록 | ~/.opal/skills/에 SCHEMA.md 미배포 | 후속 태스크로 설치 스크립트 업데이트 |
| condition 표현식 해석 불일치 | LLM마다 조건식 해석이 다를 수 있음 | 의사코드 수준의 단순 표현식 사용, 자연어 주석 병기 |
