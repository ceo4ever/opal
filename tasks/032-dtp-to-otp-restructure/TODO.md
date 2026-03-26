# TODO: dev-task-pilot 컴포지션 아키텍처 전환

> 작성일: 2026-03-26 | 참조: PLAN.md
> 입력: PLAN.md
> 출력: TODO.md

## Part A: 실행 체크리스트

PLAN.md §2 의존 순서 기반. Step 1 선행 → Step 2~9 병렬 가능 → Step 10~12 순차 → Step 13~16 순차.

---

### Step 1: 페르소나 6개 작성

PLAN.md §3.3 기반. 각 파일은 Principles + 행동 규칙만 포함 (활용 스킬/MCP는 SKILL.md 책임).

| # | 파일 | 콘텐츠 소스 |
|---|------|-----------|
| 1-1 | `skills/dtp-task/personas/service-planner.md` | §3.3 Service Planner |
| 1-2 | `skills/dtp-analysis/personas/application-architect.md` | §3.3 Application Architect |
| 1-3 | `skills/dtp-plan/personas/software-architect.md` | §3.3 Software Architect |
| 1-4 | `skills/dtp-todo/personas/software-architect.md` | 1-3과 동일 내용 복사 |
| 1-5 | `skills/dtp-test-scenario/personas/qa-engineer.md` | §3.3 QA Engineer |
| 1-6 | `skills/dtp-execute/personas/frontend-engineer.md` | §3.3 Frontend Engineer |
| 1-7 | `skills/dtp-execute/personas/backend-engineer.md` | §3.3 Backend Engineer |
| 1-8 | `skills/dtp-wireframe/personas/service-planner.md` | 1-1과 동일 내용 복사 |
| 1-9 | `skills/dtp-qa/personas/qa-engineer.md` | 1-5와 동일 내용 복사 |

- [ ] 1-1: service-planner.md
- [ ] 1-2: application-architect.md
- [ ] 1-3: software-architect.md
- [ ] 1-4: software-architect.md (dtp-todo, 1-3 복사)
- [ ] 1-5: qa-engineer.md
- [ ] 1-6: frontend-engineer.md
- [ ] 1-7: backend-engineer.md
- [ ] 1-8: service-planner.md (dtp-wireframe, 1-1 복사)
- [ ] 1-9: qa-engineer.md (dtp-qa, 1-5 복사)

---

### Step 2: dtp-task 스킬

PLAN.md §3.4 dtp-task 기반. 콘텐츠 소스: 기존 `skills/dev-task-pilot/SKILL.md` §STEP 1 + `references/wireframe-task-guide.md`.

| # | 파일 | 설명 |
|---|------|------|
| 2-1 | `skills/dtp-task/SKILL.md` (~150줄) | TASK.md 작성 프로세스, frontmatter, 활용 스킬(interview), 산출물 형식 |
| 2-2 | `skills/dtp-task/references/task-guide.md` | TASK.md 작성 규칙 상세 (기존 SKILL.md §STEP 1 이관) |

- [ ] 2-1: SKILL.md
- [ ] 2-2: task-guide.md

---

### Step 3: dtp-analysis 스킬

PLAN.md §3.4 dtp-analysis 기반. 콘텐츠 소스: 기존 `references/analysis-guide.md` + 기술 컨텍스트 3곳 통합.

| # | 파일 | 설명 |
|---|------|------|
| 3-1 | `skills/dtp-analysis/SKILL.md` (~200줄) | 입력 계약, 프로세스(tech-context → analysis), 활용 MCP(context7), 산출물 형식 |
| 3-2 | `skills/dtp-analysis/references/analysis-guide.md` | 분석 프로세스 상세 (기존 이관, 기술 컨텍스트 부분 분리) |
| 3-3 | `skills/dtp-analysis/references/tech-context-guide.md` | 신규: 기술 스택 로딩 통합 (프로젝트 문서 확인 → 스택 식별 → 스킬/MCP 매핑) |

- [ ] 3-1: SKILL.md
- [ ] 3-2: analysis-guide.md
- [ ] 3-3: tech-context-guide.md (신규)

---

### Step 4: dtp-plan 스킬

PLAN.md §3.4 dtp-plan 기반. 콘텐츠 소스: 기존 `references/plan-guide.md` (Full+Short 통합 → 입력 기반 분기).

| # | 파일 | 설명 |
|---|------|------|
| 4-1 | `skills/dtp-plan/SKILL.md` (~250줄) | 입력 계약, ANALYSIS.md 유무 분기, 활용 스킬/MCP(기술 스택별), 산출물 형식 |
| 4-2 | `skills/dtp-plan/references/plan-guide.md` | 통합 PLAN 가이드 (ANALYSIS 존재/미존재 분기, 설계 프로세스) |

- [ ] 4-1: SKILL.md
- [ ] 4-2: plan-guide.md

---

### Step 5: dtp-todo 스킬

PLAN.md §3.4 dtp-todo 기반. 콘텐츠 소스: 기존 `references/todo-guide.md` + `references/execute-plan-guide.md`.

| # | 파일 | 설명 |
|---|------|------|
| 5-1 | `skills/dtp-todo/SKILL.md` (~200줄) | Part A 상세 분해 + Part B QA + 복잡도 판별 + Part C (기존 dtp-action-plan-agent 흡수) |
| 5-2 | `skills/dtp-todo/references/todo-guide.md` | 체크리스트 분해 규칙 (기존 이관) |
| 5-3 | `skills/dtp-todo/references/execute-plan-guide.md` | 복잡 모드 Part C 설계 (기존 이관) |

- [ ] 5-1: SKILL.md
- [ ] 5-2: todo-guide.md
- [ ] 5-3: execute-plan-guide.md

---

### Step 6: dtp-test-scenario 스킬

PLAN.md §3.4 dtp-test-scenario 기반. 콘텐츠 소스: 기존 `references/test-scenario-guide.md`.

| # | 파일 | 설명 |
|---|------|------|
| 6-1 | `skills/dtp-test-scenario/SKILL.md` (~150줄) | 시나리오 도출, 도구 결정, 활용 스킬(webapp-testing, security-best-practices), 산출물 형식 |
| 6-2 | `skills/dtp-test-scenario/references/test-scenario-guide.md` | 시나리오 작성 규칙 (기존 이관) |

- [ ] 6-1: SKILL.md
- [ ] 6-2: test-scenario-guide.md

---

### Step 7: dtp-execute 스킬

PLAN.md §3.4 dtp-execute 기반. 콘텐츠 소스: 기존 `references/execute-guide.md` + `references/checkpoint-guide.md`.

| # | 파일 | 설명 |
|---|------|------|
| 7-1 | `skills/dtp-execute/SKILL.md` (~250줄) | checklist_source 입력, 페르소나 선택(FE/BE), 가드레일, 활용 스킬/MCP, 산출물 |
| 7-2 | `skills/dtp-execute/references/execute-guide.md` | 실행 규칙 + 가드레일 (기존 이관) |
| 7-3 | `skills/dtp-execute/references/checkpoint-guide.md` | DONE.md 생성 규칙 (기존 이관) |

- [ ] 7-1: SKILL.md
- [ ] 7-2: execute-guide.md
- [ ] 7-3: checkpoint-guide.md

---

### Step 8: dtp-wireframe 스킬

PLAN.md §3.4 dtp-wireframe 기반. 콘텐츠 소스: 기존 `modes/wireframe-ui.md` WIREFRAME 단계.

| # | 파일 | 설명 |
|---|------|------|
| 8-1 | `skills/dtp-wireframe/SKILL.md` (~150줄) | wireframe-builder 위임, 활용 스킬(wireframe-builder, interview), 산출물 |

- [ ] 8-1: SKILL.md

---

### Step 9: dtp-qa 스킬

PLAN.md §3.4 dtp-qa 기반. 콘텐츠 소스: 기존 `agents/dtp-qa-dev-agent/AGENT.md` + `agents/dtp-qa-wireframe-agent/AGENT.md` + `references/wireframe-qa-guide.md`.

| # | 파일 | 설명 |
|---|------|------|
| 9-1 | `skills/dtp-qa/SKILL.md` (~200줄) | 단계별 qa-dev/qa-wireframe 분기, 활용 스킬(code-review, security-best-practices), 산출물 |
| 9-2 | `skills/dtp-qa/references/qa-dev-guide.md` | Full/Short QA 기준 (기존 dtp-qa-dev-agent 이관) |
| 9-3 | `skills/dtp-qa/references/qa-wireframe-guide.md` | Wireframe QA 기준 (기존 dtp-qa-wireframe-agent + wireframe-qa-guide 이관) |

- [ ] 9-1: SKILL.md
- [ ] 9-2: qa-dev-guide.md
- [ ] 9-3: qa-wireframe-guide.md

---

### Step 10: dtp-dev 오케스트레이터

PLAN.md §3.5 dtp-dev 기반. 콘텐츠 소스: 기존 `SKILL.md` 공통 규칙 + `modes/dev-full.md`.

| # | 파일 | 설명 |
|---|------|------|
| 10-1 | `skills/dtp-dev/SKILL.md` (~300줄) | Full Task 파이프라인, 디스패치 프롬프트 템플릿, 공통 규칙, 게이트, STATE.md, QA/Test 호출 |

- [ ] 10-1: SKILL.md

---

### Step 11: dtp-dev-short 오케스트레이터

PLAN.md §3.5 dtp-dev-short 기반. 콘텐츠 소스: 기존 `SKILL.md` 공통 규칙 + `modes/dev-short.md`.

| # | 파일 | 설명 |
|---|------|------|
| 11-1 | `skills/dtp-dev-short/SKILL.md` (~250줄) | Short Task 파이프라인 (ANALYSIS/TODO 생략), 에스컬레이션 규칙 |

- [ ] 11-1: SKILL.md

---

### Step 12: dtp-dev-wf 오케스트레이터

PLAN.md §3.5 dtp-dev-wf 기반. 콘텐츠 소스: 기존 `SKILL.md` 공통 규칙 + `modes/wireframe-ui.md`.

| # | 파일 | 설명 |
|---|------|------|
| 12-1 | `skills/dtp-dev-wf/SKILL.md` (~200줄) | Wireframe UI 파이프라인, ui-designer 연동 |

- [ ] 12-1: SKILL.md

---

### Step 13: 에이전트 3개

PLAN.md §3.6 기반.

| # | 파일 | 설명 |
|---|------|------|
| 13-1 | `agents/dtp-worker/AGENT.md` | 범용 워커: 스킬 Read → 실행, model 오버라이드 테이블 포함 |
| 13-2 | `agents/dtp-qa-worker/AGENT.md` | QA 워커: dtp-qa Read → 검증, readonly: true (기본) |
| 13-3 | `agents/dtp-test-worker/AGENT.md` | Test 워커: TEST-SCENARIO.md 기반 동적 검증 |

- [ ] 13-1: dtp-worker/AGENT.md
- [ ] 13-2: dtp-qa-worker/AGENT.md
- [ ] 13-3: dtp-test-worker/AGENT.md

---

### Step 14: 레지스트리 갱신

PLAN.md §1 수정 파일 기반. 신규 스킬 완성 후 마지막에 교체 (기존 호출 실패 방지).

| # | 파일 | 변경 |
|---|------|------|
| 14-1 | `opal/core/references/skills.md` | dtp 스킬 11개 등록 + 기존 dev-task-pilot 제거 |
| 14-2 | `opal/core/references/agents.md` | dtp 에이전트 3개 등록 + 기존 dtp-*-agent 6개 제거 |
| 14-3 | `~/.opal/references/skills.md` | 14-1과 동기화 |
| 14-4 | `~/.opal/references/agents.md` | 14-2와 동기화 |

- [ ] 14-1: 소스 skills.md
- [ ] 14-2: 소스 agents.md
- [ ] 14-3: 배포 skills.md (동기화)
- [ ] 14-4: 배포 agents.md (동기화)

---

### Step 15: CLAUDE.md 소스 구조 갱신

| # | 파일 | 변경 |
|---|------|------|
| 15-1 | `CLAUDE.md` | 소스 구조 섹션에 dtp 컴포지션 아키텍처 반영 (skills/ 하위 11개, agents/ 하위 3개) |

- [ ] 15-1: CLAUDE.md

---

### Step 16: 프로젝트 메모리 갱신

| # | 파일 | 변경 |
|---|------|------|
| 16-1 | `.opal/MEMORY.md` | 작업 히스토리 #1 단계를 "완료 (커밋해시)" 로 갱신 |

- [ ] 16-1: .opal/MEMORY.md

---

## Part B: QA 체크리스트

PLAN.md §6 기반.

### 기능 검증
- [ ] 각 SKILL.md < 500줄
- [ ] 각 스킬 자기완결 (외부 스킬 references 참조 없음)
- [ ] YAML frontmatter — name(kebab-case), description("반드시 이 스킬을 사용해야 하는 상황:" 패턴)
- [ ] 페르소나가 각 스킬의 personas/에 배치됨
- [ ] 페르소나에 활용 스킬/MCP 없음 (Principles + 행동 규칙만)
- [ ] 오케스트레이터 디스패치 프롬프트가 올바른 스킬 경로 참조
- [ ] 각 산출물 형식에 입출력 계약 명시 (> 입력: / > 출력:)

### 정합성 검증
- [ ] 레지스트리에 11개 스킬 + 3개 에이전트 등록
- [ ] 레지스트리에서 기존 dev-task-pilot + dtp-*-agent 제거
- [ ] CLAUDE.md 소스 구조가 실제 파일과 일치
- [ ] 모든 스킬 탐색 경로에 실제 파일 존재

### 동적 검증
- [ ] dtp-dev: "회원가입 기능 개발해줘" → TASK → ANALYSIS 파이프라인
- [ ] dtp-dev-short: "버튼 색상 변경해줘" → TASK → PLAN 파이프라인
- [ ] dtp-dev-wf: "대시보드 와이어프레임 만들어줘" → TASK → WIREFRAME 파이프라인

---

## 산출물 요약

| 유형 | 수량 | 파일 수 |
|------|------|--------|
| 페르소나 | 6종 (9파일, 3개는 복사) | 9 |
| 단계 스킬 SKILL.md | 8 | 8 |
| 단계 스킬 references | 12 | 12 |
| 오케스트레이터 SKILL.md | 3 | 3 |
| 에이전트 AGENT.md | 3 | 3 |
| 레지스트리 (소스+배포) | 4 | 4 |
| 프로젝트 문서 | 2 | 2 |
| **합계** | | **41** |
