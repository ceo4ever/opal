# TASK: dev-task-pilot 컴포지션 아키텍처 전환

> 작성일: 2026-03-25 | 갱신일: 2026-03-26 | 작업 유형: 리팩토링 (대규모 구조 변경)

## 작업 목표

dev-task-pilot 단일 스킬(SKILL.md + modes/ + references/)을 **컴포지션 아키텍처**로 전면 재구조화한다. 각 파이프라인 단계를 독립 스킬로 분리하고, 오케스트레이터 스킬이 이들을 조합하여 Full Task / Short Task / Wireframe UI 파이프라인을 구성한다.

## 배경

1. **모놀리식 → 컴포지션**: 현재 단일 SKILL.md(443줄) + modes/3개 + references/10개 구조를 단계별 독립 스킬로 분리
2. **모드 자동 감지 제거**: 사용자가 오케스트레이터 스킬(`/dtp-dev`, `/dtp-dev-short`, `/dtp-dev-wf`)을 명시적으로 호출
3. **단계별 독립 실행**: 각 단계 스킬은 필수 입력만 있으면 독립적으로 산출물을 생성 — skill-creator 표준 준수 (자기완결, <500줄)
4. **페르소나 시스템 도입**: 단계별로 다른 전문가 사고방식을 워커에 주입 (6개 페르소나)
5. **기술 컨텍스트 통합**: 3곳에 흩어진 기술 스택 로딩 로직을 tech-context-guide.md로 통합
6. **산출물 형식 개선**: PLAN.md 통일, 입출력 계약 명시, STATE.md 오케스트레이터 전용화

## 요구사항

### R1. 단계 스킬 (Stage Skills) — 8개

각 단계 스킬은 자기완결적이다: SKILL.md + references/ + personas/를 자체 보유. 외부 스킬 참조 없음.

#### R1-1. dtp-task (TASK.md 작성)
- [ ] `skills/dtp-task/SKILL.md`
- [ ] `skills/dtp-task/references/task-guide.md`
- [ ] `skills/dtp-task/personas/service-planner.md`
- 필수 입력: 사용자 요청 (텍스트)
- 보장 출력: TASK.md
- 오케스트레이터가 직접 수행 (사용자 대화형 상호작용)

#### R1-2. dtp-analysis (코드베이스 분석)
- [ ] `skills/dtp-analysis/SKILL.md`
- [ ] `skills/dtp-analysis/references/analysis-guide.md`
- [ ] `skills/dtp-analysis/references/tech-context-guide.md`
- [ ] `skills/dtp-analysis/personas/application-architect.md`
- 필수 입력: TASK.md
- 선택 입력: 프로젝트 docs/
- 보장 출력: ANALYSIS.md

#### R1-3. dtp-plan (구현 계획)
- [ ] `skills/dtp-plan/SKILL.md`
- [ ] `skills/dtp-plan/references/plan-guide.md`
- [ ] `skills/dtp-plan/personas/software-architect.md`
- 필수 입력: TASK.md
- 선택 입력: ANALYSIS.md (있으면 설계 집중, 없으면 분석+설계 통합)
- 보장 출력: PLAN.md (통일 형식, 항상 체크리스트 포함), execution-plan.json (FE/BE 시)

#### R1-4. dtp-todo (실행 체크리스트 확장, Full Task 전용)
- [ ] `skills/dtp-todo/SKILL.md`
- [ ] `skills/dtp-todo/references/todo-guide.md`
- [ ] `skills/dtp-todo/references/execute-plan-guide.md`
- [ ] `skills/dtp-todo/personas/software-architect.md`
- 필수 입력: PLAN.md
- 선택 입력: ANALYSIS.md
- 보장 출력: TODO.md (Part A 상세 분해 + Part B QA + 복잡도 판별 + Part C)

#### R1-5. dtp-test-scenario (테스트 시나리오 작성)
- [ ] `skills/dtp-test-scenario/SKILL.md`
- [ ] `skills/dtp-test-scenario/references/test-scenario-guide.md`
- [ ] `skills/dtp-test-scenario/personas/qa-engineer.md`
- 필수 입력: TASK.md + PLAN.md
- 선택 입력: TODO.md
- 보장 출력: TEST-SCENARIO.md

#### R1-6. dtp-execute (코드 실행)
- [ ] `skills/dtp-execute/SKILL.md`
- [ ] `skills/dtp-execute/references/execute-guide.md`
- [ ] `skills/dtp-execute/references/checkpoint-guide.md`
- [ ] `skills/dtp-execute/personas/frontend-engineer.md`
- [ ] `skills/dtp-execute/personas/backend-engineer.md`
- 필수 입력: checklist_source (오케스트레이터가 경로 + 섹션 지정)
- 선택 입력: execution-plan.json (FE/BE 병렬 시)
- 보장 출력: 코드 변경 + changed_files

#### R1-7. dtp-qa (QA 검증)
- [ ] `skills/dtp-qa/SKILL.md`
- [ ] `skills/dtp-qa/references/qa-dev-guide.md`
- [ ] `skills/dtp-qa/references/qa-wireframe-guide.md`
- [ ] `skills/dtp-qa/personas/qa-engineer.md`
- 필수 입력: 검증 대상 산출물 경로
- 선택 입력: TASK.md (교차 참조)
- 보장 출력: QA-{단계}.md

#### R1-8. dtp-wireframe (와이어프레임 생성)
- [ ] `skills/dtp-wireframe/SKILL.md`
- [ ] `skills/dtp-wireframe/personas/service-planner.md`
- 필수 입력: TASK.md + 입력물 (정책서/이미지/구두 요청)
- 보장 출력: wireframe.md
- wireframe-builder 스킬 호출

### R2. 오케스트레이터 스킬 (Orchestrator Skills) — 3개

각 오케스트레이터는 파이프라인 정의 + 디스패치 규칙만 포함. 단계 스킬 경로를 지정하여 워커에 전달.

#### R2-1. dtp-dev (Full Task 오케스트레이터)
- [ ] `skills/dtp-dev/SKILL.md`
- 파이프라인: `dtp-task → dtp-analysis → dtp-plan → dtp-todo → dtp-test-scenario → dtp-execute → dtp-qa`
- 공통 규칙: 구현 금지 원칙, Git 점검, 게이트 체크포인트, STATE.md 관리
- 트리거: `/dtp-dev`, "Full Task로 해줘"

#### R2-2. dtp-dev-short (Short Task 오케스트레이터)
- [ ] `skills/dtp-dev-short/SKILL.md`
- 파이프라인: `dtp-task → dtp-plan → dtp-test-scenario → dtp-execute → dtp-qa`
- dtp-analysis, dtp-todo 생략 (dtp-plan이 ANALYSIS.md 없이 분석+설계 통합)
- 에스컬레이션 규칙: Full Task 전환 제안 조건 포함
- 트리거: `/dtp-dev-short`, "Short로 해줘"

#### R2-3. dtp-dev-wf (Wireframe UI 오케스트레이터)
- [ ] `skills/dtp-dev-wf/SKILL.md`
- 파이프라인: `dtp-task → dtp-wireframe → dtp-execute → dtp-qa`
- 트리거: `/dtp-dev-wf`, "와이어프레임으로"

### R3. 페르소나 시스템 — 6개

각 단계 스킬이 자체 personas/ 디렉토리에 보유. 파일 내용은 동일하지만 필요한 스킬에만 배치.

| 페르소나 | 핵심 역할 | 보유 스킬 |
|---------|----------|----------|
| **Service Planner** (서비스 기획자) | 요구사항 구조화, 사용자 관점, 우선순위 | dtp-task, dtp-wireframe |
| **Application Architect** (앱 아키텍트) | 코드 구조 분석, 의존성 맵핑, 영향 범위 | dtp-analysis |
| **Software Architect** (SW 아키텍트) | 구현 설계, 기술 의사결정, 데이터 모델링 | dtp-plan, dtp-todo |
| **QA Engineer** (QA 엔지니어) | 테스트 시나리오, 엣지 케이스, 품질 기준 | dtp-test-scenario, dtp-qa |
| **Frontend Engineer** (FE 엔지니어) | 컴포넌트 설계, UX, React/shadcn 패턴 | dtp-execute |
| **Backend Engineer** (BE 엔지니어) | API, 비즈니스 로직, 보안, 쿼리 최적화 | dtp-execute |

- 각 페르소나: principles 5-7개 + 행동 규칙 3-5개 (300-500 토큰)
- 디스패치 프롬프트에 `**페르소나**: {경로}` → 워커가 Read
- TASK 단계는 오케스트레이터 직접 수행 → SKILL.md에 Service Planner 관점 내장

### R4. 산출물 형식 개선

#### R4-1. PLAN.md 통일
- [ ] Full/Short 구분 없이 동일 형식
- [ ] 항상 포함: 코드 분석, 구현 계획, 실행 체크리스트, QA 체크리스트, 기술 컨텍스트
- [ ] ANALYSIS.md 유무에 따라 "코드 분석" 섹션 깊이만 달라짐

#### R4-2. 입출력 계약 명시
- [ ] 각 산출물 헤더에 `> 입력:`, `> 출력:` 필드 추가
- [ ] 후속 스킬이 "이 문서는 뭘 기반으로 만들어졌는지" 알 수 있음

#### R4-3. STATE.md 오케스트레이터 전용
- [ ] 단계 스킬은 STATE.md를 갱신하지 않음
- [ ] 오케스트레이터만 단계 전환 시 STATE.md 갱신
- [ ] EXECUTE 중 Step 진행은 checklist_source 파일 체크박스로 추적

#### R4-4. otp-execute 입력 계약 단일화
- [ ] 오케스트레이터가 `checklist_source` (경로 + 섹션)를 지정
- [ ] otp-execute는 "체크리스트가 어디 있는지" 몰라도 됨

### R5. 에이전트 단순화

기존 6개 전용 에이전트 → 범용 워커 체계로 전환.

- [ ] `agents/dtp-worker/AGENT.md` — 범용 워커: 단계 스킬 SKILL.md를 Read하고 따르는 범용 에이전트
- [ ] `agents/dtp-qa-worker/AGENT.md` — QA 워커: dtp-qa 스킬을 Read하고 검증 수행
- [ ] `agents/dtp-test-worker/AGENT.md` — Test 워커: TEST-SCENARIO.md 기반 동적 검증 (기존 dtp-dev-test-agent 역할)
- [ ] 기존 dtp-action-plan-agent → dtp-todo 스킬 내부에서 처리 (복잡 모드 시 내부 서브에이전트)

### R6. 레지스트리 업데이트

- [ ] `~/.opal/references/skills.md` — dtp 단계 스킬 8개 + 오케스트레이터 3개 등록, **기존 dev-task-pilot 항목 즉시 제거**
- [ ] `~/.opal/references/agents.md` — dtp-worker, dtp-qa-worker, dtp-test-worker 등록, **기존 dtp-*-agent 항목 즉시 제거**
- [ ] `opal/core/references/skills.md` — 소스 레지스트리 동기화
- [ ] `opal/core/references/agents.md` — 소스 레지스트리 동기화

### R7. 동적 검증 (skill-creator 프로세스)

오케스트레이터 스킬 3개에 대해 테스트 프롬프트를 작성하고, TASK→첫 단계까지 실행하여 검증한다.

- [ ] dtp-dev 테스트: "회원가입 기능 개발해줘" → TASK→ANALYSIS 단계까지 검증
- [ ] dtp-dev-short 테스트: "버튼 색상 변경해줘" → TASK→PLAN 단계까지 검증
- [ ] dtp-dev-wf 테스트: "대시보드 와이어프레임 만들어줘" → TASK→WIREFRAME 단계까지 검증
- [ ] 검증 포인트: 트리거 정확성, 디스패치 프롬프트, 페르소나 주입, 가이드 참조 경로

### R8. 프로젝트 문서 갱신

- [ ] `CLAUDE.md` — 소스 구조 갱신 (컴포지션 아키텍처 반영)
- [ ] `.opal/MEMORY.md` — 작업 히스토리 갱신

## 제약 조건

- 기존 `skills/dev-task-pilot/`은 소스에 유지 (안정화 후 별도 태스크로 삭제)
- 기존 `agents/dtp-*-agent/`도 소스에 유지 (동일)
- **레지스트리에서는 기존 항목 즉시 제거** (혼란 방지)
- dtp-doc 스킬은 이번 태스크 범위 밖 (별도 태스크)
- install-mac.sh 변경 불필요 (skills/ 전체 자동 배포)
- 각 스킬은 skill-creator 표준 준수: SKILL.md <500줄, 자기완결, YAML frontmatter

## 기술 스택

- 산출물: Markdown (.md)
- 영향 범위: skills/, agents/, opal/core/references/, CLAUDE.md

## 실행 단계 스케줄

| 단계 | 내용 | 주요 산출물 | 의존 |
|------|------|------------|------|
| **1. ANALYSIS** | 기존 dtp 전체 분석 + 컴포지션 구조 설계 | ANALYSIS.md | TASK |
| **2. PLAN** | 스킬 11개 상세 설계, 산출물 형식, 에이전트 설계 | PLAN.md | ANALYSIS |
| **3. TODO** | 파일 단위 실행 체크리스트, 의존 순서 | TODO.md | PLAN |
| **4. TEST-SCENARIO** | 정적 검증 + 동적 검증 시나리오 | TEST-SCENARIO.md | TODO |
| **5. EXECUTE** | 실제 파일 생성/수정 | 스킬 11개 + 에이전트 3개 + 레지스트리 | TODO |
| **6. QA + TEST** | 구조 검증 + 동적 테스트 + 최종 QA | QA 리포트 + DONE.md | EXECUTE |

## 파일 구조 (목표)

```
skills/
├── dtp-task/                     ← 단계: TASK.md 작성
│   ├── SKILL.md
│   ├── references/
│   │   └── task-guide.md
│   └── personas/
│       └── service-planner.md
│
├── dtp-analysis/                 ← 단계: 코드베이스 분석
│   ├── SKILL.md
│   ├── references/
│   │   ├── analysis-guide.md
│   │   └── tech-context-guide.md
│   └── personas/
│       └── application-architect.md
│
├── dtp-plan/                     ← 단계: 구현 계획
│   ├── SKILL.md
│   ├── references/
│   │   └── plan-guide.md
│   └── personas/
│       └── software-architect.md
│
├── dtp-todo/                     ← 단계: 실행 체크리스트 확장 (Full 전용)
│   ├── SKILL.md
│   ├── references/
│   │   ├── todo-guide.md
│   │   └── execute-plan-guide.md
│   └── personas/
│       └── software-architect.md
│
├── dtp-test-scenario/            ← 단계: 테스트 시나리오
│   ├── SKILL.md
│   ├── references/
│   │   └── test-scenario-guide.md
│   └── personas/
│       └── qa-engineer.md
│
├── dtp-execute/                  ← 단계: 코드 실행
│   ├── SKILL.md
│   ├── references/
│   │   ├── execute-guide.md
│   │   └── checkpoint-guide.md
│   └── personas/
│       ├── frontend-engineer.md
│       └── backend-engineer.md
│
├── dtp-wireframe/                ← 단계: 와이어프레임 생성
│   ├── SKILL.md
│   └── personas/
│       └── service-planner.md
│
├── dtp-qa/                       ← 단계: QA 검증
│   ├── SKILL.md
│   ├── references/
│   │   ├── qa-dev-guide.md
│   │   └── qa-wireframe-guide.md
│   └── personas/
│       └── qa-engineer.md
│
├── dtp-dev/                      ← 오케스트레이터: Full Task
│   └── SKILL.md
│
├── dtp-dev-short/                ← 오케스트레이터: Short Task
│   └── SKILL.md
│
└── dtp-dev-wf/                   ← 오케스트레이터: Wireframe UI
    └── SKILL.md

agents/
├── dtp-worker/AGENT.md           ← 범용 워커
├── dtp-qa-worker/AGENT.md        ← QA 워커
└── dtp-test-worker/AGENT.md      ← Test 워커
```

## 관련 문서

- 기존 스킬: `skills/dev-task-pilot/SKILL.md`
- 기존 에이전트: `agents/dtp-*/AGENT.md` (6개)
- 소스 레지스트리: `opal/core/references/skills.md`, `opal/core/references/agents.md`
- 배포 레지스트리: `~/.opal/references/skills.md`, `~/.opal/references/agents.md`
- 프로젝트 메모리: `.opal/memory/project_otp_doc_plan.md` (dtp-doc 후속 계획)
- skill-creator: `community-skills/anthropics/skill-creator/SKILL.md`
