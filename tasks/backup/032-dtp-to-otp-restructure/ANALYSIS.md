# ANALYSIS: dev-task-pilot 컴포지션 아키텍처 전환

> 작성일: 2026-03-25 | 갱신일: 2026-03-26 | 참조: TASK.md
> 입력: TASK.md
> 출력: ANALYSIS.md

## 1. 기존 코드 분석

### 관련 파일 목록

#### 스킬 파일 (14개)

| 파일 | 역할 | 전환 대상 |
|------|------|----------|
| `skills/dev-task-pilot/SKILL.md` (443줄) | 오케스트레이터 (모드 판별, 공통 규칙, 디스패치) | → dtp-dev, dtp-dev-short, dtp-dev-wf (3개 오케스트레이터 분리) |
| `modes/dev-full.md` (391줄) | Full Task 파이프라인 + 디스패치 프롬프트 | → dtp-dev/SKILL.md 베이스 |
| `modes/dev-short.md` (249줄) | Short Task 파이프라인 + 디스패치 프롬프트 | → dtp-dev-short/SKILL.md 베이스 |
| `modes/wireframe-ui.md` (253줄) | Wireframe UI 파이프라인 | → dtp-dev-wf/SKILL.md 베이스 |
| `references/analysis-guide.md` | ANALYSIS 단계 가이드 | → dtp-analysis/references/ |
| `references/plan-guide.md` | PLAN 단계 가이드 (Full+Short 통합) | → dtp-plan/references/ (통합 유지, 입력 기반 분기) |
| `references/todo-guide.md` | TODO 단계 가이드 | → dtp-todo/references/ |
| `references/execute-guide.md` | EXECUTE 단계 가이드 | → dtp-execute/references/ |
| `references/execute-plan-guide.md` | 실행 아키텍처 설계 가이드 | → dtp-todo/references/ |
| `references/test-scenario-guide.md` | TEST-SCENARIO 작성 가이드 | → dtp-test-scenario/references/ |
| `references/checkpoint-guide.md` | 게이트 체크포인트 & DONE.md | → dtp-execute/references/ |
| `references/state-guide.md` | STATE.md 시스템 | → 오케스트레이터 SKILL.md에 내장 (단계 스킬은 STATE 비관여) |
| `references/wireframe-task-guide.md` | Wireframe TASK 가이드 | → dtp-wireframe/references/ 또는 SKILL.md 내장 |
| `references/wireframe-qa-guide.md` | Wireframe QA 기준 | → dtp-qa/references/ |

#### 에이전트 파일 (6개)

| 파일 | 역할 | 전환 대상 |
|------|------|----------|
| `agents/dtp-dev-agent/AGENT.md` | Full/Short 워커 | → `dtp-worker` (범용 워커로 교체) |
| `agents/dtp-wireframe-ui-agent/AGENT.md` | Wireframe 워커 | → `dtp-worker` 로 통합 |
| `agents/dtp-qa-dev-agent/AGENT.md` | Full/Short QA | → `dtp-qa-worker` |
| `agents/dtp-qa-wireframe-agent/AGENT.md` | Wireframe QA | → `dtp-qa-worker` 로 통합 |
| `agents/dtp-action-plan-agent/AGENT.md` | 실행 아키텍처 설계 | → dtp-todo 내부 처리 |
| `agents/dtp-dev-test-agent/AGENT.md` | 코드 동적 검증 | → `dtp-test-worker` |

#### 레지스트리 & 프로젝트 문서

| 파일 | 변경 내용 |
|------|----------|
| `~/.opal/references/skills.md` | dtp 단계 8개 + 오케스트레이터 3개 추가, 기존 dev-task-pilot 즉시 제거 |
| `~/.opal/references/agents.md` | dtp-worker/qa-worker/test-worker 추가, 기존 dtp-*-agent 즉시 제거 |
| `opal/core/references/skills.md` | 소스 레지스트리 동기화 |
| `opal/core/references/agents.md` | 소스 레지스트리 동기화 |
| `CLAUDE.md` | 소스 구조 갱신 |

### 현재 구현 패턴

**모놀리식 구조**: SKILL.md(오케스트레이터) + modes/(파이프라인) + references/(가이드). 워커가 시작하려면 SKILL.md + mode 파일 + 가이드를 순차 Read — 총 700-830줄 로딩.

**컴포지션 전환 후**: 워커가 단계 스킬 SKILL.md(<500줄) + 필요한 reference만 Read. 불필요한 다른 모드/단계 정보를 로드하지 않음.

### 의존성 맵 (현재 → 전환 후)

```
현재:
  SKILL.md → modes/dev-full.md → dtp-dev-agent → references/analysis-guide.md
                                                → references/plan-guide.md
                                                → references/todo-guide.md
                                                → ...

전환 후:
  dtp-dev/SKILL.md (오케스트레이터)
    → dtp-worker + dtp-task/SKILL.md     → TASK.md
    → dtp-worker + dtp-analysis/SKILL.md → ANALYSIS.md
    → dtp-worker + dtp-plan/SKILL.md     → PLAN.md
    → dtp-worker + dtp-todo/SKILL.md     → TODO.md
    → dtp-worker + dtp-test-scenario/SKILL.md → TEST-SCENARIO.md
    → dtp-worker + dtp-execute/SKILL.md  → 코드 변경
    → dtp-qa-worker + dtp-qa/SKILL.md    → QA-*.md
    → dtp-test-worker                    → TEST-SCENARIO.md 결과 채움
```

### 기존 버그 (전환 시 수정)

| 위치 | 버그 | 수정 |
|------|------|------|
| dtp-dev-test-agent AGENT.md:52 | `dtp-dev-full-agent`, `dtp-dev-short-agent` 참조 — 존재하지 않는 에이전트명 | 범용 워커 체계로 해소 |
| references/todo-guide.md:68 | `dtp-planner` 약칭 — 정식명 불일치 | dtp-todo 내부 처리로 해소 |
| references/execute-guide.md | `dtp-test` 약칭 — 정식명 불일치 | dtp-test-worker로 통일 |

## 2. 핵심 발견 사항

### F-1. 컴포지션이 중복 문제를 근본적으로 해결

모놀리식에서는 execute-guide.md, checkpoint-guide.md 등을 여러 스킬에 복사해야 했다. 컴포지션에서는 각 가이드가 **해당 단계 스킬에 한 곳만 존재**. otp-dev와 otp-dev-short가 동일한 dtp-execute를 호출하므로 중복 없음.

### F-2. 기술 컨텍스트 3곳 중복 → tech-context-guide.md 통합

현재 analysis-guide.md 0단계 + plan-guide.md 0단계 + SKILL.md TASK 단계에서 중복. → dtp-analysis/references/tech-context-guide.md로 단일화. dtp-plan은 ANALYSIS.md의 기술 컨텍스트 섹션을 참조.

### F-3. PLAN.md 출력 형식 통일

현재 Full PLAN(설계만)과 Short PLAN(분석+설계+체크리스트)이 다른 형식. dtp-plan이 단일 스킬이므로 출력 형식을 통일:
- 항상 포함: 코드 분석, 구현 계획, 실행 체크리스트, QA 체크리스트, 기술 컨텍스트
- ANALYSIS.md 유무에 따라 코드 분석 깊이만 달라짐

### F-4. STATE.md 소유권 단일화

현재 오케스트레이터 + 워커 공동 갱신 → 오케스트레이터 전용으로 변경. 단계 스킬은 STATE.md를 모름. 오케스트레이터가 단계 전환 시마다 갱신.

### F-5. 에이전트 6개 → 3개 범용 워커

단계별 전용 에이전트가 불필요. 범용 워커가 "어떤 단계 스킬의 SKILL.md를 읽고 따르라"는 지시를 받으면 됨. QA와 Test만 역할 특성상 별도 워커.

### F-6. 페르소나 재설계 확정

6개 페르소나: Service Planner, Application Architect, Software Architect, QA Engineer, Frontend Engineer, Backend Engineer. 각 단계 스킬이 자체 personas/에 필요한 파일만 보유.

### F-7. install-mac.sh 변경 불필요

skills/ 전체를 자동 배포하는 기존 로직으로 dtp-* 11개 스킬이 자동 포함.

### F-8. 동적 검증 필요

skill-creator 프로세스(Test Cases → Running → Improving)를 적용하여, 오케스트레이터 3개의 실제 파이프라인 동작을 검증해야 함.

## 3. 영향 범위

### 직접 영향

| 영역 | 신규 생성 | 수정 |
|------|----------|------|
| skills/ | 단계 스킬 8개 + 오케스트레이터 3개 (각각 SKILL.md + references/ + personas/) | - |
| agents/ | dtp-worker, dtp-qa-worker, dtp-test-worker | - |
| 레지스트리 | - | skills.md, agents.md (소스 + 배포 양쪽) |
| 프로젝트 | - | CLAUDE.md 소스 구조 갱신 |

### 간접 영향

| 영역 | 내용 |
|------|------|
| `.opal/MEMORY.md` | 작업 히스토리 갱신 |
| `opal/core/references/` | 소스 레지스트리 동기화 |

## 4. 제약/리스크

| # | 리스크 | 대응 |
|---|--------|------|
| 1 | 스킬 수 증가 (1→11) | 각 스킬이 작고 집중적 (<500줄), 관리 복잡도는 낮음 |
| 2 | 페르소나 파일 일부 중복 | 파일이 작음 (300-500 토큰), 독립 진화 가능성이 이점 |
| 3 | 기존 레지스트리 즉시 교체 | 신규 스킬 완성 후 레지스트리 교체 (EXECUTE 단계 마지막에 수행) |
| 4 | 동적 검증 비용 | TASK→첫 단계까지만 테스트하여 비용 최소화 |
| 5 | 기존 dtp 참조 잔존 | 소스 파일은 유지, 레지스트리에서 제거, 안정화 후 별도 삭제 |

## 5. 기술 컨텍스트

| 영역 | 기술 | 비고 |
|------|------|------|
| 산출물 | Markdown (.md) | 스킬/에이전트/레지스트리 전부 마크다운 |
| 배포 | Bash (scripts/install-mac.sh) | 변경 불필요 |
| 표준 | skill-creator 패턴 | SKILL.md <500줄, 자기완결, Progressive Disclosure |

## 6. 파일 수 요약

| 분류 | 수 | 내용 |
|------|---|------|
| **신규 스킬** | 11개 | 단계 8개 (SKILL.md + references/ + personas/) + 오케스트레이터 3개 (SKILL.md만) |
| **신규 에이전트** | 3개 | dtp-worker, dtp-qa-worker, dtp-test-worker |
| **수정** | 6개 | skills.md ×2, agents.md ×2, CLAUDE.md, .opal/MEMORY.md |
| **유지 (소스)** | 20개 | 기존 dev-task-pilot 14개 + 기존 dtp-*-agent 6개 |
