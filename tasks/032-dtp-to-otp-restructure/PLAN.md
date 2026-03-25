# PLAN: dev-task-pilot 컴포지션 아키텍처 전환

> 작성일: 2026-03-26 | 참조: TASK.md, ANALYSIS.md
> 입력: TASK.md, ANALYSIS.md
> 출력: PLAN.md

## 1. 구현 범위

### 신규 생성 파일

#### 단계 스킬 (8개 × SKILL.md + references + personas)

| # | 스킬 | SKILL.md | references/ | personas/ |
|---|------|----------|------------|-----------|
| 1 | dtp-task | 신규 | task-guide.md | service-planner.md |
| 2 | dtp-analysis | 신규 | analysis-guide.md, tech-context-guide.md | application-architect.md |
| 3 | dtp-plan | 신규 | plan-guide.md | software-architect.md |
| 4 | dtp-todo | 신규 | todo-guide.md, execute-plan-guide.md | software-architect.md |
| 5 | dtp-test-scenario | 신규 | test-scenario-guide.md | qa-engineer.md |
| 6 | dtp-execute | 신규 | execute-guide.md, checkpoint-guide.md | frontend-engineer.md, backend-engineer.md |
| 7 | dtp-wireframe | 신규 | (wireframe-builder 위임) | service-planner.md |
| 8 | dtp-qa | 신규 | qa-dev-guide.md, qa-wireframe-guide.md | qa-engineer.md |

#### 오케스트레이터 스킬 (3개 × SKILL.md만)

| # | 스킬 | SKILL.md |
|---|------|----------|
| 9 | dtp-dev | 신규 (Full Task 파이프라인) |
| 10 | dtp-dev-short | 신규 (Short Task 파이프라인) |
| 11 | dtp-dev-wf | 신규 (Wireframe UI 파이프라인) |

#### 에이전트 (3개)

| # | 에이전트 | AGENT.md |
|---|---------|----------|
| 12 | dtp-worker | 신규 (범용 워커) |
| 13 | dtp-qa-worker | 신규 (QA 워커) |
| 14 | dtp-test-worker | 신규 (Test 워커) |

### 수정 파일

| # | 파일 | 변경 |
|---|------|------|
| 15 | `opal/core/references/skills.md` | dtp 스킬 11개 등록, 기존 dev-task-pilot 제거 |
| 16 | `opal/core/references/agents.md` | dtp 에이전트 3개 등록, 기존 dtp-*-agent 제거 |
| 17 | `~/.opal/references/skills.md` | 배포 레지스트리 동기화 |
| 18 | `~/.opal/references/agents.md` | 배포 레지스트리 동기화 |
| 19 | `CLAUDE.md` | 소스 구조 갱신 |
| 20 | `.opal/MEMORY.md` | 작업 히스토리 갱신 |

---

## 2. 구현 순서

의존 순서: 단계 스킬 (독립) → 오케스트레이터 (단계 스킬 경로 참조) → 에이전트 (스킬 참조) → 레지스트리 → 프로젝트 문서

| 순서 | 작업 | 의존 |
|------|------|------|
| 1 | 페르소나 6개 작성 | 없음 |
| 2 | dtp-task (SKILL.md + references + personas) | 페르소나 |
| 3 | dtp-analysis | 페르소나 |
| 4 | dtp-plan | 페르소나 |
| 5 | dtp-todo | 페르소나 |
| 6 | dtp-test-scenario | 페르소나 |
| 7 | dtp-execute | 페르소나 |
| 8 | dtp-wireframe | 페르소나 |
| 9 | dtp-qa | 페르소나 |
| 10 | dtp-dev (오케스트레이터) | 단계 스킬 1-9 |
| 11 | dtp-dev-short (오케스트레이터) | 단계 스킬 1-9 |
| 12 | dtp-dev-wf (오케스트레이터) | 단계 스킬 1-9 |
| 13 | dtp-worker, dtp-qa-worker, dtp-test-worker | 오케스트레이터 |
| 14 | 레지스트리 갱신 (소스 + 배포) | 전체 스킬/에이전트 |
| 15 | CLAUDE.md, .opal/MEMORY.md | 레지스트리 |

> 순서 2-9는 상호 독립 — 병렬 실행 가능.

---

## 3. 핵심 설계

### 3.1 공통: SKILL.md frontmatter 규격

모든 dtp-* 스킬은 skill-creator 표준을 따른다:

```yaml
---
name: dtp-{stage}
description: |
  **{한줄 요약}**. {스킬이 하는 일}.
  반드시 이 스킬을 사용해야 하는 상황: {트리거 키워드}.
  {입출력 계약 요약}.
---
```

### 3.2 공통: 산출물 헤더 규격

모든 산출물(.md)은 입출력 계약을 헤더에 명시한다:

```markdown
# {단계}: {태스크 제목}

> 작성일: YYYY-MM-DD
> 입력: {필수 입력 파일}, {선택 입력 파일}
> 출력: {이 파일}, {부속 파일}
```

### 3.3 페르소나 설계

각 페르소나 파일 구조:

```markdown
# {페르소나명}

## Principles
1. {원칙 1}
2. {원칙 2}
...

## 행동 규칙
- {규칙 1}
- {규칙 2}
...
```

#### Service Planner (서비스 기획자)
- **Principles**: 사용자 관점 우선, 요구사항 완전성 검증, 비즈니스 가치 기반 우선순위, 모호함 발견 즉시 질문, 엣지 케이스 선제 도출
- **행동 규칙**: 요구사항 누락 시 추측하지 않고 질문, 기술 용어를 비즈니스 언어로 번역, 사용자 시나리오로 요구사항 검증
- **보유 스킬**: dtp-task, dtp-wireframe
- **활용 스킬**: interview (요구사항 불명확 시)

#### Application Architect (앱 아키텍트)
- **Principles**: 코드는 반드시 실제로 읽는다 (추측 금지), 의존성 방향을 항상 추적, 변경 영향 범위를 과소평가하지 않음, 기술 부채를 식별하고 기록, 데이터 흐름을 끝까지 추적
- **행동 규칙**: Glob/Grep/Read로 실제 코드 확인 후 분석, 호출 체인 역추적, 테스트 커버리지 현황 파악
- **보유 스킬**: dtp-analysis
- **활용 스킬/MCP**: context7 (라이브러리 최신 문서), skills.md 기술 스택 매핑 참조

#### Software Architect (SW 아키텍트)
- **Principles**: 설계는 즉시 구현 가능해야 함 (코딩에 바로 들어갈 수 있는 수준), 의존성 방향은 하위→상위, 트레이드오프를 명시적으로 기록, 프로젝트 기존 패턴을 존중, 데이터 모델링 시 정규화/인덱싱/마이그레이션 고려
- **행동 규칙**: 함수 시그니처와 타입까지 명세, 구현 순서의 의존성 검증, 기존 아키텍처와의 정합성 확인
- **보유 스킬**: dtp-plan, dtp-todo
- **활용 스킬/MCP**: 기술 스택별 추천 스킬 (아래 3.4 참조), context7, shadcn MCP

#### QA Engineer (QA 엔지니어)
- **Principles**: 정상 경로만 테스트하면 안 됨 (엣지 케이스 필수), 테스트는 구체적이고 검증 가능해야 함, 회귀 리스크를 항상 고려, 보안 검증을 기본 포함, 도구 기반 자동화 우선
- **행동 규칙**: 각 요구사항에 대해 최소 2개 시나리오 (정상 + 엣지), 기대 결과를 수치/조건으로 명시, test-tools.yaml 레지스트리 참조
- **보유 스킬**: dtp-test-scenario, dtp-qa
- **활용 스킬**: getsentry/code-review (코드 리뷰 관점), openai/security-best-practices (보안), anthropics/webapp-testing (Playwright E2E)

#### Frontend Engineer (FE 엔지니어)
- **Principles**: 컴포넌트는 단일 책임, 접근성(a11y) 기본 준수, 불필요한 재렌더링 방지, shadcn/ui Critical Rules 준수, 반응형 레이아웃 기본
- **행동 규칙**: ui-designer 스킬 패턴 참조, shadcn MCP로 컴포넌트 조회 후 구현, 기존 프로젝트 컴포넌트 재사용 우선
- **보유 스킬**: dtp-execute
- **활용 스킬/MCP**: ui-designer (plan-driven 모드), vercel-labs/react-best-practices, vercel-labs/shadcn, vercel-labs/next-best-practices, vercel-labs/composition-patterns, anthropics/frontend-design, shadcn MCP, context7

#### Backend Engineer (BE 엔지니어)
- **Principles**: API는 RESTful 원칙 준수, 입력은 항상 검증 (시스템 경계), SQL Injection/XSS 등 OWASP Top 10 방어, 에러 핸들링은 레이어별 명확히, 쿼리 N+1 문제 사전 방지
- **행동 규칙**: 모델→DTO→서비스→라우터 레이어 순서, 환경변수로 시크릿 관리, 기존 프로젝트 ORM/쿼리 패턴 따름
- **보유 스킬**: dtp-execute
- **활용 스킬/MCP**: trailofbits/modern-python (Python 프로젝트), context7

### 3.4 단계 스킬별 설계

#### dtp-task

```
skills/dtp-task/
├── SKILL.md (~150줄)
├── references/
│   └── task-guide.md         ← TASK.md 작성 규칙 (기존 SKILL.md §STEP 1 이관)
└── personas/
    └── service-planner.md
```

**SKILL.md 핵심 내용**:
- 사용자 요청을 구조화된 TASK.md로 정리
- 모호한 부분은 질문 (interview 스킬 연동)
- 기술 스택 사전 판별 (package.json, pyproject.toml 등)
- TASK.md 출력 형식 정의

**활용 스킬**:
- `interview` — 요구사항 불명확 시 구조화된 Q&A

**TASK.md 통일 형식**:
```markdown
# TASK: {제목}

> 작성일: YYYY-MM-DD | 작업 유형: {신규/개선/수정/오류/Wireframe UI}
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표
## 배경
## 요구사항
## 제약 조건
## 기술 스택
## 관련 문서
```

#### dtp-analysis

```
skills/dtp-analysis/
├── SKILL.md (~200줄)
├── references/
│   ├── analysis-guide.md     ← 분석 프로세스 (기존 이관, 기술 컨텍스트 부분 분리)
│   └── tech-context-guide.md ← 신규: 기술 스택 로딩 통합 프로세스
└── personas/
    └── application-architect.md
```

**SKILL.md 핵심 내용**:
- 입력 계약: TASK.md (필수), 프로젝트 docs/ (선택)
- 프로세스: tech-context-guide.md → analysis-guide.md 순서
- 출력: ANALYSIS.md

**tech-context-guide.md** (신규, 기존 3곳 중복 통합):
1. 프로젝트 문서 확인 (docs/, .opal/AGENT.md)
2. 기술 스택 식별 (package.json, pyproject.toml, go.mod 등)
3. `~/.opal/references/skills.md` 기술 스택별 추천 스킬 매핑
4. `~/.opal/references/mcps.md` MCP 서버 매핑
5. 결과를 ANALYSIS.md "기술 컨텍스트" 섹션에 기록

**활용 MCP**:
- `context7` — resolve-library-id → query-docs (핵심 라이브러리 최신 문서)

**ANALYSIS.md 통일 형식**:
```markdown
# ANALYSIS: {제목}

> 작성일: YYYY-MM-DD
> 입력: TASK.md
> 출력: ANALYSIS.md

## 1. 기존 코드 분석
## 2. 외부 조사 결과 (해당 시)
## 3. 영향 범위
## 4. 핵심 발견 사항
## 5. 제약/리스크
## 6. 기술 컨텍스트
```

#### dtp-plan

```
skills/dtp-plan/
├── SKILL.md (~250줄)
├── references/
│   └── plan-guide.md         ← 통합 PLAN 가이드 (입력 기반 분기)
└── personas/
    └── software-architect.md
```

**SKILL.md 핵심 내용**:
- 입력 계약: TASK.md (필수), ANALYSIS.md (선택)
- 분기: ANALYSIS.md 있으면 → 설계 집중, 없으면 → 코드 분석 포함
- 출력: PLAN.md (통일 형식), execution-plan.json (FE/BE 시)

**plan-guide.md** (통합, 입력 기반 분기):
- ANALYSIS.md 존재 시: "1. 코드 분석" 섹션을 ANALYSIS.md 참조로 간략 작성
- ANALYSIS.md 미존재 시: "1. 코드 분석" 섹션을 직접 수행 (Full ANALYSIS 수준)
- 이후 설계 프로세스는 동일: 구현 범위 → 구현 순서 → 핵심 설계 → 테스트 전략

**활용 스킬/MCP** (기술 스택에 따라):

| 프로젝트 기술 | 참조 스킬 | 적용 |
|-------------|----------|------|
| React | vercel-labs/react-best-practices | 컴포넌트 설계 패턴 |
| Next.js | vercel-labs/next-best-practices | RSC, 데이터 패턴 |
| shadcn/ui | vercel-labs/shadcn | 컴포넌트 선택, 폼 구조 |
| Python | trailofbits/modern-python | uv, ruff, async 패턴 |
| UI 설계 | anthropics/frontend-design | UI/UX 참조 |
| MCP | context7, shadcn MCP | 최신 문서, 컴포넌트 조회 |

**PLAN.md 통일 형식**:
```markdown
# PLAN: {제목}

> 작성일: YYYY-MM-DD
> 입력: TASK.md, ANALYSIS.md (선택)
> 출력: PLAN.md, execution-plan.json (FE/BE 시)

## 1. 코드 분석
## 2. 구현 계획
## 3. 실행 체크리스트
## 4. QA 체크리스트
## 5. 기술 컨텍스트
## 6. 리스크 및 대응
```

#### dtp-todo

```
skills/dtp-todo/
├── SKILL.md (~200줄)
├── references/
│   ├── todo-guide.md          ← 체크리스트 분해 규칙 (기존 이관)
│   └── execute-plan-guide.md  ← 복잡 모드 Part C 설계 (기존 이관)
└── personas/
    └── software-architect.md
```

**SKILL.md 핵심 내용**:
- 입력 계약: PLAN.md (필수), ANALYSIS.md (선택)
- PLAN.md의 "3. 실행 체크리스트"를 상세 분해 → Part A
- QA 체크리스트 → Part B
- 복잡도 판별 → 복잡 모드 시 내부에서 Part C 생성 (기존 dtp-action-plan-agent 역할 흡수)
- 출력: TODO.md

**복잡 모드 Part C**: 기존에는 dtp-action-plan-agent를 별도 호출했으나, dtp-todo 내부에서 처리. execute-plan-guide.md를 참조하여 에이전트 토폴로지, 스킬 요구사항, 도구 요구사항을 생성.

#### dtp-test-scenario

```
skills/dtp-test-scenario/
├── SKILL.md (~150줄)
├── references/
│   └── test-scenario-guide.md ← 시나리오 작성 규칙 (기존 이관)
└── personas/
    └── qa-engineer.md
```

**SKILL.md 핵심 내용**:
- 입력 계약: TASK.md + PLAN.md (필수), TODO.md (선택)
- 각 요구사항에 대해 시나리오 도출 (정상 + 엣지)
- 도구 사전 결정: .opal/test-tools.yaml 또는 프로젝트 설정에서 추론
- 출력: TEST-SCENARIO.md

**활용 스킬**:
- `anthropics/webapp-testing` — Playwright E2E 테스트 시나리오 참고
- `openai/security-best-practices` — 보안 테스트 시나리오 참고

#### dtp-execute

```
skills/dtp-execute/
├── SKILL.md (~250줄)
├── references/
│   ├── execute-guide.md       ← 실행 규칙 + 가드레일 (기존 이관)
│   └── checkpoint-guide.md    ← DONE.md 생성 규칙 (기존 이관)
└── personas/
    ├── frontend-engineer.md
    └── backend-engineer.md
```

**SKILL.md 핵심 내용**:
- 입력 계약: checklist_source (경로+섹션, 오케스트레이터 지정), execution-plan.json (선택)
- 페르소나 선택: FE 작업 → frontend-engineer.md, BE 작업 → backend-engineer.md
- 가드레일: 구현 금지 원칙 (PLAN에 없는 파일 수정 금지), 보안 가드레일
- 체크리스트 갱신: checklist_source 파일의 체크박스 실시간 갱신
- 출력: 코드 변경 + changed_files

**활용 스킬/MCP** (FE 작업 시):
- `ui-designer` — plan-driven 모드로 화면 구현
- `vercel-labs/shadcn` — shadcn/ui 프로젝트에서 컴포넌트 패턴
- `vercel-labs/react-best-practices` — React 성능/패턴
- `vercel-labs/composition-patterns` — 재사용 컴포넌트 설계
- `shadcn MCP` — 컴포넌트 검색/조회/설치 명령
- `context7` — 최신 라이브러리 문서

**활용 스킬/MCP** (BE 작업 시):
- `trailofbits/modern-python` — Python 프로젝트
- `context7` — 최신 프레임워크 문서

#### dtp-wireframe

```
skills/dtp-wireframe/
├── SKILL.md (~150줄)
└── personas/
    └── service-planner.md
```

**SKILL.md 핵심 내용**:
- 입력 계약: TASK.md + 입력물 (정책서/이미지/구두 요청)
- wireframe-builder 스킬에 위임 (탐색 경로로 SKILL.md 찾아 Read)
- 출력: wireframe.md

**활용 스킬**:
- `wireframe-builder` — wireframe.md 생성 위임
- `interview` — 입력물 부족 시 (서비스 목적, 주요 기능, 대상 사용자 불명확)

#### dtp-qa

```
skills/dtp-qa/
├── SKILL.md (~200줄)
├── references/
│   ├── qa-dev-guide.md        ← Full/Short QA 기준 (기존 dtp-qa-dev-agent 이관)
│   └── qa-wireframe-guide.md  ← Wireframe QA 기준 (기존 dtp-qa-wireframe-agent 이관)
└── personas/
    └── qa-engineer.md
```

**SKILL.md 핵심 내용**:
- 입력 계약: 검증 대상 산출물 경로 + 단계명 (필수), TASK.md (선택)
- 단계에 따라 qa-dev-guide 또는 qa-wireframe-guide 참조
- 출력: QA-{단계}.md

**활용 스킬**:
- `getsentry/code-review` — EXECUTE 후 코드 품질 관점
- `openai/security-best-practices` — 보안 검증 관점

### 3.5 오케스트레이터 설계

#### dtp-dev (Full Task)

```
skills/dtp-dev/
└── SKILL.md (~300줄)
```

**SKILL.md 구성**:
1. 트리거 & 스코프 정의
2. 구현 금지 원칙
3. Git 사전 점검
4. 파이프라인 정의:
   ```
   dtp-task → dtp-analysis → [QA] → 검토
     → dtp-plan → [QA] → 검토
     → dtp-todo → 검토
     → dtp-test-scenario → 검토/승인
     → dtp-execute → [Test] → 완료
   ```
5. 디스패치 프롬프트 템플릿 (각 단계별)
6. QA/Test 호출 규칙
7. 게이트 체크포인트 규칙
8. STATE.md 관리 규칙
9. 에스컬레이션: 없음 (이미 Full)

**디스패치 프롬프트 템플릿** (예: ANALYSIS 단계):
```
dtp-analysis 스킬을 수행하라.

**스킬 경로**: {탐색 경로에서 dtp-analysis/SKILL.md}
**태스크 폴더**: {tasks/{NNN}-{name}/}
**이전 산출물**: {TASK.md 경로}
**프로젝트 컨벤션**: {CLAUDE.md 경로}
**산출물 저장 경로**: {ANALYSIS.md 경로}
```

#### dtp-dev-short (Short Task)

```
skills/dtp-dev-short/
└── SKILL.md (~250줄)
```

**파이프라인**:
```
dtp-task → dtp-plan (ANALYSIS.md 없이) → [QA] → 검토
  → dtp-test-scenario → 검토/승인
  → dtp-execute → [Test] → 완료
```

**에스컬레이션 규칙**:
- dtp-plan 결과에서 변경 파일 ≥10개, 다단계 의사결정, 다중 모듈 연쇄 영향 감지 시
- Full Task(dtp-dev)로 전환 제안

#### dtp-dev-wf (Wireframe UI)

```
skills/dtp-dev-wf/
└── SKILL.md (~200줄)
```

**파이프라인**:
```
dtp-task (Wireframe 특화) → dtp-wireframe → [QA: wireframe] → 검토
  → dtp-execute (UI 구현) → [QA: execute-ui] → 완료
```

**dtp-execute에서 ui-designer 연동**:
- wireframe.md + TASK.md의 기술 환경을 입력으로 전달
- ui-designer 스킬의 scaffold 모드 또는 plan-driven 모드 호출

### 3.6 에이전트 설계

#### dtp-worker (범용 워커)

```yaml
---
name: dtp-worker
description: |
  dtp 단계 스킬을 독립 컨텍스트에서 실행하는 범용 워커 에이전트.
  오케스트레이터가 단계 스킬 경로를 전달하면, 해당 SKILL.md를 Read하고 프로세스를 따른다.
model: sonnet
---
```

**실행 프로세스**:
1. 오케스트레이터 프롬프트에서 **스킬 경로**, **태스크 폴더**, **이전 산출물**을 확인
2. 스킬 SKILL.md를 Read
3. 스킬의 personas/에서 지정된 페르소나를 Read
4. 스킬의 프로세스를 따라 산출물 생성
5. 결과 반환 (artifact_path, summary, status, blockers, changed_files)

**model 오버라이드** (Claude Code):

| 단계 스킬 | model |
|----------|-------|
| dtp-task | (오케스트레이터 직접, 해당 없음) |
| dtp-analysis | haiku |
| dtp-plan | opus |
| dtp-todo | haiku |
| dtp-test-scenario | haiku |
| dtp-execute | sonnet |
| dtp-wireframe | sonnet |

#### dtp-qa-worker (QA 워커)

```yaml
---
name: dtp-qa-worker
description: dtp-qa 스킬을 독립 컨텍스트에서 실행하는 QA 전용 워커.
model: haiku
readonly: true
---
```

- dtp-qa/SKILL.md를 Read하고, 지정된 산출물을 검증
- readonly: true (코드 수정 없음, 문서 리뷰만)
- 단, Wireframe EXECUTE QA는 빌드/린트 실행이 필요하므로 readonly: false

#### dtp-test-worker (Test 워커)

```yaml
---
name: dtp-test-worker
description: TEST-SCENARIO.md 기반 동적 검증 워커. 코드 실행 + 결과 채움 + 판정.
model: sonnet
readonly: false
---
```

- 기존 dtp-dev-test-agent의 역할 그대로 이관
- TEST-SCENARIO.md를 입력으로, 시나리오 실행 + 결과 기록 + 판정
- 활용 스킬: getsentry/code-review (코드 패턴 검사)

### 3.7 스킬 탐색 경로

모든 단계 스킬 탐색:
1. `{프로젝트}/.opal/skills/dtp-{stage}/SKILL.md`
2. `~/.opal/skills/dtp-{stage}/SKILL.md`

커뮤니티/외부 스킬 탐색:
1. `{프로젝트}/.opal/skills/{skill}/SKILL.md`
2. `~/.opal/skills/{skill}/SKILL.md`
3. `~/.opal/community-skills/{provider}/{skill}/SKILL.md`

### 3.8 기술 스택별 스킬/MCP 활용 매핑

dtp-plan과 dtp-execute에서 ANALYSIS.md(또는 TASK.md)의 기술 스택 정보를 기반으로 아래 스킬/MCP를 참조한다:

| 프로젝트 기술 | 스킬 | MCP | 적용 단계 |
|-------------|------|-----|----------|
| React | vercel-labs/react-best-practices, composition-patterns | context7 | PLAN, EXECUTE |
| Next.js | vercel-labs/next-best-practices + 위 React | context7 | PLAN, EXECUTE |
| shadcn/ui | vercel-labs/shadcn | shadcn MCP, context7 | PLAN, EXECUTE |
| Python | trailofbits/modern-python | context7 | PLAN, EXECUTE |
| FE 설계 | anthropics/frontend-design | - | PLAN |
| UI 구현 | ui-designer | shadcn MCP | EXECUTE |
| 테스트 | anthropics/webapp-testing | - | TEST-SCENARIO |
| 코드 리뷰 | getsentry/code-review | - | QA, TEST |
| 보안 | openai/security-best-practices | - | QA, TEST-SCENARIO |

---

## 4. 의존성 및 환경 변경

- 추가 패키지: 없음 (마크다운 문서 작업)
- install-mac.sh: 변경 불필요 (skills/ 전체 자동 배포)
- 레지스트리: 기존 항목 제거 + 신규 항목 추가 (EXECUTE 마지막에 수행)

---

## 5. 실행 체크리스트

- [ ] Step 1: 페르소나 6개 작성
- [ ] Step 2: dtp-task 스킬 작성 (SKILL.md + task-guide.md + service-planner.md)
- [ ] Step 3: dtp-analysis 스킬 작성 (SKILL.md + analysis-guide.md + tech-context-guide.md + application-architect.md)
- [ ] Step 4: dtp-plan 스킬 작성 (SKILL.md + plan-guide.md + software-architect.md)
- [ ] Step 5: dtp-todo 스킬 작성 (SKILL.md + todo-guide.md + execute-plan-guide.md + software-architect.md)
- [ ] Step 6: dtp-test-scenario 스킬 작성 (SKILL.md + test-scenario-guide.md + qa-engineer.md)
- [ ] Step 7: dtp-execute 스킬 작성 (SKILL.md + execute-guide.md + checkpoint-guide.md + frontend-engineer.md + backend-engineer.md)
- [ ] Step 8: dtp-wireframe 스킬 작성 (SKILL.md + service-planner.md)
- [ ] Step 9: dtp-qa 스킬 작성 (SKILL.md + qa-dev-guide.md + qa-wireframe-guide.md + qa-engineer.md)
- [ ] Step 10: dtp-dev 오케스트레이터 작성
- [ ] Step 11: dtp-dev-short 오케스트레이터 작성
- [ ] Step 12: dtp-dev-wf 오케스트레이터 작성
- [ ] Step 13: dtp-worker, dtp-qa-worker, dtp-test-worker 에이전트 작성
- [ ] Step 14: 레지스트리 갱신 (소스 + 배포)
- [ ] Step 15: CLAUDE.md 소스 구조 갱신
- [ ] Step 16: .opal/MEMORY.md 작업 히스토리 갱신

---

## 6. QA 체크리스트

### 기능 검증
- [ ] 각 스킬 SKILL.md가 <500줄인가
- [ ] 각 스킬이 자기완결적인가 (외부 스킬 references 참조 없음)
- [ ] YAML frontmatter가 skill-creator 규격에 맞는가
- [ ] 페르소나가 각 스킬의 personas/에 배치되었는가
- [ ] 오케스트레이터의 디스패치 프롬프트가 올바른 스킬 경로를 참조하는가
- [ ] 각 산출물 형식에 입출력 계약이 명시되었는가

### 정합성 검증
- [ ] 레지스트리에 11개 스킬 + 3개 에이전트가 등록되었는가
- [ ] 레지스트리에서 기존 dev-task-pilot + dtp-*-agent가 제거되었는가
- [ ] CLAUDE.md 소스 구조가 실제 파일과 일치하는가
- [ ] 모든 스킬 탐색 경로가 실제 파일 존재하는가

### 동적 검증
- [ ] dtp-dev 테스트 프롬프트로 TASK→ANALYSIS 파이프라인 검증
- [ ] dtp-dev-short 테스트 프롬프트로 TASK→PLAN 파이프라인 검증
- [ ] dtp-dev-wf 테스트 프롬프트로 TASK→WIREFRAME 파이프라인 검증

---

## 7. 기술 컨텍스트

### 기술 스택
| 영역 | 기술 |
|------|------|
| 산출물 | Markdown (.md) |
| 표준 | skill-creator 패턴 (자기완결, <500줄, Progressive Disclosure) |

### 참조 도구
| 도구 | 적용 |
|------|------|
| skill-creator | SKILL.md 작성 표준 참조 |
| version-mgr | 산출물 버전 태깅 |
| interview | dtp-task에서 요구사항 보강 |
| doc-writer | 문서 표준 규칙 (한국어 본문/영어 코드) |

---

## 8. 리스크 및 대응

| 리스크 | 영향 | 대응 |
|--------|------|------|
| 스킬 수 증가 (1→11) | 관리 복잡도 | 각 스킬이 작고 집중적, 독립 테스트 가능 |
| 페르소나 파일 일부 중복 | 디스크 공간 (미미) | 각 파일 300-500토큰, 독립 진화 가능 |
| 레지스트리 즉시 교체 | 기존 dtp 호출 실패 | 신규 스킬 완성 후 마지막에 교체 |
| 오케스트레이터가 복잡해질 수 있음 | 디스패치 프롬프트 관리 | 템플릿화하여 일관성 유지 |
| 기존 태스크 STATE.md 호환 | 기존 태스크 재개 시 | 기존 태스크는 기존 방식으로 완료, 새 태스크부터 dtp-* |
