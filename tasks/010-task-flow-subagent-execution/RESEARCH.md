# RESEARCH: task-flow 워커 에이전트 실행 모델

> 작성일: 2026-03-14 | 참조: TASK.md

## 1. 기존 코드 분석

### 관련 파일 목록

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `skills/task-flow/SKILL.md` | 메인 스킬 (638줄) — 전체 파이프라인 정의 | 수정 (대폭) |
| `skills/task-flow/references/execute-guide.md` | EXECUTE 상세 가이드 (213줄) | 수정 (대폭) |
| `skills/task-flow/references/research-guide.md` | RESEARCH 상세 가이드 (119줄) | 수정 (워커 참조 추가) |
| `skills/task-flow/references/plan-guide.md` | PLAN 상세 가이드 (185줄) | 수정 (워커 참조 추가) |
| `skills/task-flow/references/todo-guide.md` | TODO 상세 가이드 (174줄) | 수정 (워커 참조 추가) |
| `skills/task-flow/references/execute-plan-guide.md` | Part C 설계 가이드 (194줄) | 변경 없음 |
| `agents/claude/task-flow-qa/AGENT.md` | QA 에이전트 | 변경 없음 |
| `agents/claude/task-flow-planner/AGENT.md` | Planner 에이전트 | 변경 없음 |
| `agents/claude/task-flow-test/AGENT.md` | Test 에이전트 | 변경 없음 |
| `CLAUDE.md` | Core Workflow 설명 | 수정 (부분) |

### 현재 실행 모델: "알투가 모든 걸 직접 수행"

```
현재 모델:
┌─────────────────────────────────────────────┐
│ 알투 (메인 에이전트)                            │
│                                             │
│ TASK → RESEARCH → PLAN → TODO → EXECUTE     │
│   ↕         ↕        ↕       ↕        ↕     │
│ 사용자    사용자    사용자   사용자    사용자     │
│                                             │
│ [코드 읽기] [분석] [설계] [코드 수정] [테스트]   │
│ ← 모두 알투의 컨텍스트에 축적                    │
└─────────────────────────────────────────────┘
```

**컨텍스트 소모 분석:**

| 단계 | 컨텍스트 소모 | 주요 원인 |
|------|-------------|----------|
| TASK | 낮음 | 사용자 지시 구조화 |
| RESEARCH | **높음** | 코드 파일 다수 Read, Grep, 분석 |
| PLAN | 중간 | RESEARCH 결과 기반 설계 |
| TODO | 낮음 | PLAN 기반 분해 |
| EXECUTE | **매우 높음** | 코드 Read/Edit/Write, 테스트 실행 |

→ RESEARCH와 EXECUTE가 컨텍스트의 대부분을 소모. 이 두 단계를 워커로 격리하면 효과가 가장 큼.

### 현재 서브 에이전트 패턴 (복잡 모드)

execute-guide.md:70-94에 이미 서브 에이전트 프롬프트 템플릿이 존재:
```
## 역할 / ## 담당 작업 / ## 컨텍스트 / ## 스킬 / ## 실행 규칙
```

이 템플릿을 확장하여 전체 단계(RESEARCH, PLAN, TODO, EXECUTE)의 워커 프롬프트로 일반화할 수 있음.

### 현재 QA/Planner/Test 에이전트 호출 구조

```
SKILL.md에서 정의된 호출 시점:
  RESEARCH 완료 → QA 호출 (서브 에이전트)
  PLAN 완료 → QA 호출 (서브 에이전트)
  TODO 복잡 모드 → Planner 호출 (서브 에이전트)
  EXECUTE 완료 → Test 호출 (복잡 모드), QA 호출 (서브 에이전트)
```

**핵심**: QA/Planner/Test는 이미 서브 에이전트. 워커 모델에서도 동일하게 호출 가능.
- 워커가 산출물 작성 완료 → 워커가 QA 서브 에이전트 호출 → QA 결과와 함께 오케스트레이터에 반환
- 또는: 워커가 산출물 작성 완료 → 오케스트레이터가 QA 서브 에이전트 호출

## 2. 영향 범위

### 직접 영향

1. **SKILL.md**: 전체 파이프라인을 "오케스트레이터가 워커를 디스패치하는 모델"로 재구성
2. **execute-guide.md**: 단순/복잡/Short 모든 모드를 워커 기반으로 통일
3. **research-guide.md, plan-guide.md, todo-guide.md**: 각 가이드가 워커 컨텍스트에서 실행된다는 점 명시
4. **CLAUDE.md**: Core Workflow 설명에 오케스트레이터-워커 모델 반영

### 간접 영향 (변경 없음, 검증만)

- **execute-plan-guide.md**: Part C 설계 가이드 — 복잡 모드 전용, 기존 그대로
- **task-flow-qa/planner/test**: 기존 에이전트 — 호출 구조 유지
- **3개 플랫폼 에이전트 파일**: QA 에이전트의 호출 시점/검증 기준 변경 없음

## 3. 핵심 설계 결정사항

### 3.1 워커 단위: 단계별 워커 vs 태스크 전체 워커

**선택지 A**: 단계별 워커 — 각 단계(RESEARCH, PLAN, TODO, EXECUTE)마다 별도 워커 디스패치
```
알투 → [워커: RESEARCH] → 결과 반환 → 사용자 검토
알투 → [워커: PLAN] → 결과 반환 → 사용자 검토
알투 → [워커: TODO] → 결과 반환 → 사용자 검토
알투 → [워커: EXECUTE] → 결과 반환 → QA → 완료
```
- 장점: 게이트 체크포인트와 자연스럽게 맞물림, 각 워커 컨텍스트가 작음
- 단점: 워커 간 컨텍스트 전달 필요 (이전 단계 산출물을 다음 워커에 전달)

**선택지 B**: 태스크 전체 워커 — 하나의 워커가 RESEARCH~EXECUTE 전체 수행
```
알투 → [워커: RESEARCH~EXECUTE 전체] → (중간에 게이트마다 결과 반환?)
```
- 장점: 컨텍스트 이어받기 불필요
- 단점: 워커의 컨텍스트가 결국 현재 알투와 동일하게 커짐 (문제 해결 안 됨). 게이트 체크포인트 구현이 어려움 (워커가 중간에 멈추고 결과를 반환하는 메커니즘 필요)

**선택지 C**: 하이브리드 — 게이트가 없는 연속 단계를 하나의 워커로 묶기
```
Full Task:
  알투 → [워커: RESEARCH] → QA → 사용자 검토
  알투 → [워커: PLAN] → QA → 사용자 검토
  알투 → [워커: TODO] → 사용자 검토
  알투 → [워커: EXECUTE] → QA → 완료

Short Task:
  알투 → [워커: PLAN(통합)] → QA → 사용자 검토
  알투 → [워커: EXECUTE] → QA → 완료
```
- 장점: 게이트 체크포인트와 완벽히 일치, 각 워커 컨텍스트 적정 크기
- 단점: 워커 간 컨텍스트 전달이 필요하지만, 산출물(.md)이 이미 그 역할을 함

**결정: 선택지 C (하이브리드 = 실질적으로 A와 동일)**

이유:
- 각 단계 산출물(.md)이 이미 다음 단계의 입력으로 설계되어 있음 → 별도 컨텍스트 전달 메커니즘 불필요
- 게이트 체크포인트와 자연스럽게 맞물림
- 워커 컨텍스트가 해당 단계에 필요한 만큼만 소모

### 3.2 TASK 단계: 알투가 직접 vs 워커 위임

**결정: 알투가 직접 수행**

이유:
- TASK는 사용자 지시를 구조화하는 단계 — 사용자와의 대화가 핵심
- 코드를 읽지 않으므로 컨텍스트 소모 적음
- 모드 판별 + 사용자 보고가 오케스트레이터의 본질적 역할

### 3.3 QA 호출 주체: 워커 vs 오케스트레이터

**선택지 A**: 워커가 QA 호출
```
워커: RESEARCH.md 작성 → QA 서브에이전트 호출 → QA-RESEARCH.md 생성 → 결과를 오케스트레이터에 반환
```
- 장점: 워커가 QA 결과를 즉시 활용 가능, 오케스트레이터의 추가 작업 없음
- 단점: 워커 컨텍스트에 QA 결과까지 축적

**선택지 B**: 오케스트레이터가 QA 호출
```
워커: RESEARCH.md 작성 → 오케스트레이터에 반환
오케스트레이터: QA 서브에이전트 호출 → QA-RESEARCH.md → 사용자에게 보고
```
- 장점: 워커는 산출물 작성에만 집중, 오케스트레이터가 QA 결과를 사용자에게 직접 전달
- 단점: 오케스트레이터에 QA 결과 컨텍스트 추가 (하지만 QA 요약은 짧음)

**결정: 선택지 B — 오케스트레이터가 QA 호출**

이유:
- QA 결과는 사용자에게 보고하는 것이 목적 → 오케스트레이터가 하는 게 자연스러움
- 워커는 산출물 작성에만 집중하여 컨텍스트를 절약
- QA 에이전트는 산출물 파일을 직접 Read하므로, 워커의 컨텍스트가 필요 없음

### 3.4 워커 연속성 (Resume)

같은 태스크의 다음 단계에서 이전 워커를 이어서 쓸 수 있는가?

**플랫폼별 지원:**
- Claude Code: Agent 도구의 `resume` 파라미터로 이전 에이전트 컨텍스트 이어받기 가능
- Cursor: 제한적
- Antigravity: 미지원

**결정: resume 가능하면 활용, 불가능하면 산출물 기반 컨텍스트 복원**

```
워커 RESEARCH 완료 → agent_id 반환
사용자 승인 →
  IF resume 가능: 같은 워커를 resume하여 PLAN 수행 (RESEARCH 컨텍스트 보존)
  ELSE: 새 워커에 TASK.md + RESEARCH.md를 전달하여 PLAN 수행
```

이점: resume 가능 시 워커가 코드 분석 결과를 기억하고 있어서 PLAN 품질이 높아짐.

### 3.5 다중 태스크 동시 실행

```
알투 (오케스트레이터):
  ├─ 태스크 A: [워커 A — RESEARCH 진행 중]
  ├─ 태스크 B: [워커 B — EXECUTE 진행 중]
  └─ 태스크 C: 사용자 PLAN 검토 대기 중

사용자: "태스크 C 승인"
알투: → [워커 C — EXECUTE 디스패치]
```

**구현 방법:**
- Claude Code: 백그라운드 에이전트 (`run_in_background: true`) 활용
- 각 워커는 독립 컨텍스트이므로 태스크 간 간섭 없음
- 알투는 각 태스크의 상태(현재 단계, 워커 agent_id, 대기 여부)를 추적

**상태 추적**: 알투가 대화 컨텍스트에서 관리. 태스크가 많아지면 tasks/ 폴더의 산출물 존재 여부로 복원 가능.

### 3.6 워커 프롬프트 템플릿 설계

**공통 구조:**

```
## 역할
task-flow {단계명} 워커: {태스크 제목}

## 태스크 정의
{TASK.md 전문 또는 핵심 요약}

## 이전 단계 산출물 (있는 경우)
{RESEARCH.md, PLAN.md 등의 경로 — 워커가 직접 Read}

## 현재 단계 가이드
{해당 단계의 references/ 가이드 경로 — 워커가 직접 Read}

## 프로젝트 컨벤션
{CLAUDE.md 경로 — 워커가 직접 Read}

## 산출물 저장 경로
{tasks/{NNN}-{name}/{단계}.md}

## 실행 규칙
1. 가이드를 읽고 프로세스를 따른다
2. 산출물을 저장 경로에 작성한다
3. 완료 시 산출물 경로와 요약을 반환한다
4. 블로커 발생 시 즉시 반환한다

## 반환 형식
- artifact_path: 산출물 파일 경로
- summary: 핵심 요약 (3~5줄)
- status: success | blocked
- blockers: [{문제 설명}] (있는 경우)
```

**단계별 차이:**

| 단계 | 이전 산출물 | 가이드 | 산출물 |
|------|-----------|--------|--------|
| RESEARCH | TASK.md | research-guide.md | RESEARCH.md |
| PLAN (Full) | TASK.md, RESEARCH.md | plan-guide.md (Full) | PLAN.md |
| PLAN (Short) | TASK.md | plan-guide.md (Short) | PLAN.md |
| TODO | TASK.md, RESEARCH.md, PLAN.md | todo-guide.md | TODO.md |
| EXECUTE (단순) | TASK.md, PLAN.md/TODO.md | execute-guide.md | 코드 변경 |
| EXECUTE (복잡) | TASK.md, TODO.md (Part C 포함) | execute-guide.md | 코드 변경 |

### 3.7 SKILL.md 구조 변경 (변경 후)

```
기존 SKILL.md 구조:
├── 워크플로우 개요
├── 모드 판별
├── QA/Planner/Test 호출 규칙
├── STEP 1: TASK (알투가 직접)
├── STEP 2~5 Full: RESEARCH/PLAN/TODO/EXECUTE (알투가 직접)
├── STEP 2~3 Short: PLAN/EXECUTE (알투가 직접)
└── 게이트 체크포인트

변경 후 SKILL.md 구조:
├── 워크플로우 개요 (오케스트레이터-워커 다이어그램)
├── 모드 판별 (기존 유지)
├── 오케스트레이터-워커 실행 모델 ★신규
│   ├── 오케스트레이터(알투)의 역할
│   ├── 워커 디스패치 규칙
│   ├── 워커 프롬프트 템플릿
│   ├── 워커 결과 수신 및 처리
│   ├── 워커 연속성 (resume)
│   └── 크로스 플랫폼 폴백
├── QA/Planner/Test 호출 규칙 (기존 유지, 호출 주체=오케스트레이터 명시)
├── STEP 1: TASK (알투가 직접 — 기존 유지)
├── STEP 2~5 Full: 각 단계에 "워커 디스패치" 규칙 추가
├── STEP 2~3 Short: 각 단계에 "워커 디스패치" 규칙 추가
├── 게이트 체크포인트 (기존 유지)
├── 다중 태스크 실행 ★신규
└── 실행 모드 (기존 유지 + 다중 태스크 예시)
```

### 3.8 크로스 플랫폼 폴백

| 플랫폼 | 서브 에이전트 지원 | 워커 실행 방법 | 폴백 |
|--------|------------------|--------------|------|
| Claude Code | Agent/Task 도구 완전 지원 | 워커 디스패치 + resume | — |
| Cursor | Agent 모드 제한적 | 가능한 범위에서 워커 사용 | 직접 실행 |
| Antigravity | 서브 에이전트 미지원 | — | 알투가 직접 실행 (기존 방식) |

**폴백 규칙**: 서브 에이전트(Task/Agent 도구) 사용 불가 시, 알투가 기존 방식대로 직접 실행. references/ 가이드는 "누가 실행하든" 동일하게 적용.

## 4. 핵심 발견 사항

1. **산출물(.md)이 이미 워커 간 컨텍스트 전달 역할을 한다** — RESEARCH.md가 PLAN 워커의 입력, PLAN.md가 TODO 워커의 입력. 별도 컨텍스트 전달 메커니즘 불필요.

2. **references/ 가이드는 변경 최소** — 각 가이드는 "무엇을 어떻게 수행할지"를 정의. 알투가 하든 워커가 하든 절차는 동일. 워커 컨텍스트에서 실행된다는 안내만 추가하면 됨.

3. **QA/Planner/Test 에이전트 변경 불필요** — 이미 서브 에이전트. 호출 주체만 "워커→알투"에서 "오케스트레이터→알투"로 명확화.

4. **SKILL.md 변경이 핵심** — 워크플로우 개요, 실행 모델 섹션 신규, 각 STEP에 워커 디스패치 규칙 추가.

5. **resume 활용이 품질 핵심** — RESEARCH 워커를 resume하여 PLAN을 수행하면, 코드 분석 컨텍스트가 보존되어 설계 품질이 높아짐.

## 5. 크로스 플랫폼 서브 에이전트 상세 분석

### 5.1 Claude Code

| 항목 | 내용 |
|------|------|
| **호출 방법** | Agent 도구 (`subagent_type`, `prompt`, `run_in_background`) |
| **파일 읽기/쓰기** | 완전 지원 (Read, Edit, Write, Bash 등 모든 도구) |
| **결과 반환** | 에이전트 완료 시 메시지 반환 |
| **Resume** | `resume` 파라미터로 이전 에이전트 컨텍스트 이어받기 가능 |
| **병렬 실행** | 단일 메시지에서 다중 Agent 호출 + `run_in_background` |
| **중첩** | 서브 에이전트가 또 서브 에이전트 호출 가능 |
| **제한** | 없음 (가장 완전한 지원) |

**워커 실행 전략:**
- Agent 도구로 task-flow-agent 호출 (prompt에 단계/컨텍스트 전달)
- resume로 RESEARCH → PLAN 워커 이어받기 가능
- 다중 태스크 병렬: `run_in_background: true`로 여러 워커 동시 실행

### 5.2 Cursor

출처: https://cursor.com/ko/docs/subagents

| 항목 | 내용 |
|------|------|
| **정의 방법** | `.cursor/agents/*.md` (YAML frontmatter + 마크다운 본문) |
| **호출 방법** | 자동 위임 (description 매칭), `/agent-name 지시`, 자연어 멘션 |
| **파일 읽기/쓰기** | 부모 에이전트 도구 상속. `readonly: true`로 제한 가능 |
| **결과 반환** | 최종 메시지로 결과 반환 (중간 노이즈 필터링) |
| **Resume** | `Resume agent {id}` 로 컨텍스트 이어받기 가능 |
| **병렬 실행** | 다중 Task 도구 동시 호출로 병렬 가능 |
| **중첩** | **불가** — nested subagents not supported |
| **모델 선택** | `model: "fast" \| "inherit" \| specific-id` |
| **백그라운드** | `background: true` 지원 |

**워커 실행 전략:**
- `agents/cursor/task-flow-agent.md` 정의 → Cursor가 서브 에이전트로 자동 인식
- `/task-flow-agent` 또는 자동 위임으로 호출
- resume 가능 → RESEARCH → PLAN 이어받기 가능
- **중첩 불가**: 워커가 QA 서브 에이전트를 호출할 수 없음 → 오케스트레이터가 QA 호출 필수

### 5.3 Gemini CLI

출처: https://geminicli.com/docs/core/subagents/

| 항목 | 내용 |
|------|------|
| **정의 방법** | `.gemini/agents/*.md` (YAML frontmatter + 마크다운 본문) |
| **활성화** | `settings.json`에서 `experimental.enableAgents: true` 필요 |
| **호출 방법** | 메인 에이전트의 도구로 자동 노출, 에이전트 이름으로 호출 |
| **파일 읽기/쓰기** | `tools` 배열에 명시 (`read_file`, `write_file`, `grep_search`, `shell` 등) |
| **결과 반환** | 완료 후 메인 에이전트에 결과 보고 |
| **Resume** | 미지원 (추정) — 매 단계 새 워커 |
| **병렬 실행** | 문서에 언급 없음 |
| **제한** | `max_turns` (기본 15), `timeout_mins` (기본 5분) |
| **YOLO 모드** | 개별 확인 없이 도구 실행 (보안 주의) |

**워커 실행 전략:**
- `.gemini/agents/task-flow-agent.md` 정의 → Gemini CLI가 도구로 자동 노출
- `tools` 배열에 필요 도구 명시: `read_file`, `write_file`, `grep_search`, `shell`
- resume 불가 → 매 단계 새 워커, 산출물(.md) 기반 컨텍스트 전달
- `max_turns: 30`, `timeout_mins: 15` 등으로 복잡한 단계 대응 필요

### 5.4 Antigravity

| 항목 | 내용 |
|------|------|
| **정의 방법** | `.agent/skills/{name}/SKILL.md` (YAML frontmatter) |
| **서브 에이전트** | 네이티브 서브 에이전트 기능 없음 |
| **현재 패턴** | task-flow-qa처럼 SKILL.md를 정의, 메인 에이전트가 Read 후 지시에 따라 실행 |
| **파일 읽기/쓰기** | 메인 에이전트 권한으로 실행 |
| **컨텍스트 격리** | **없음** — 메인 에이전트 컨텍스트에서 직접 실행 |

**워커 실행 전략:**
- `agents/antigravity/task-flow-agent/SKILL.md` 정의
- 메인 에이전트가 SKILL.md를 Read하고 지시에 따라 "직접 실행" (폴백)
- 컨텍스트 격리 이점 없음 (플랫폼 한계)
- 단, 워커의 절차/규칙은 SKILL.md에 정의되어 있으므로 일관된 품질은 유지

### 5.5 크로스 플랫폼 비교 요약

| 기능 | Claude Code | Cursor | Gemini CLI | Antigravity |
|------|------------|--------|-----------|-------------|
| 서브 에이전트 | **완전** | **완전** | **지원** | 없음 (폴백) |
| 컨텍스트 격리 | **O** | **O** | **O** | X |
| Resume | **O** | **O** | X | X |
| 중첩 호출 | **O** | **X** | 불확실 | X |
| 병렬 실행 | **O** | **O** | 불확실 | X |
| 백그라운드 | **O** | **O** | X | X |

### 5.6 설계 결정 반영

**QA 호출 주체 = 오케스트레이터 (확정)**

Cursor에서 중첩 서브 에이전트가 불가능하므로, 워커가 QA를 호출하는 구조는 크로스 플랫폼에서 동작하지 않음. 오케스트레이터가 QA를 호출하는 것이 유일한 크로스 플랫폼 호환 방식.

**워커 에이전트 파일 정의 (신규 제안)**

프롬프트 템플릿 기반 동적 워커 대신, **정식 에이전트 파일로 정의**하면 Cursor/Gemini에서 네이티브 서브 에이전트로 인식됨:

```
agents/
├── claude/task-flow-agent/AGENT.md
├── cursor/task-flow-agent.md
├── antigravity/task-flow-agent/SKILL.md

# Gemini용은 install-mac.sh가 배포 시 .gemini/agents/ 에 복사
```

**관련 파일 목록 업데이트:**

| 파일 | 변경 필요 |
|------|----------|
| `agents/claude/task-flow-agent/AGENT.md` | **신규 생성** |
| `agents/cursor/task-flow-agent.md` | **신규 생성** |
| `agents/antigravity/task-flow-agent/SKILL.md` | **신규 생성** |

### 5.7 워커 에이전트 정의 스케치

```yaml
---
name: task-flow-agent
description: |
  task-flow 파이프라인의 각 단계(RESEARCH/PLAN/TODO/EXECUTE)를
  독립 컨텍스트에서 실행하는 워커 에이전트.
  오케스트레이터가 단계, 태스크 경로, 참조 가이드를 전달하면
  해당 단계의 산출물을 작성하거나 코드를 구현한다.
model: inherit
readonly: false
tools:  # Gemini CLI용
  - read_file
  - write_file
  - grep_search
  - shell
  - list_directory
max_turns: 50    # Gemini CLI용
timeout_mins: 30  # Gemini CLI용
---
```

## 6. 제약/리스크

| 리스크 | 영향 | 대응 |
|--------|------|------|
| 워커 컨텍스트에서 CLAUDE.md 컨벤션 무시 | 중간 | 워커 프롬프트에 CLAUDE.md 경로 포함, QA에서 검증 |
| resume 불가 시 워커 간 컨텍스트 손실 | 중간 | 산출물(.md)이 핵심 정보를 담고 있으므로 복원 가능 |
| 다중 태스크 시 파일 충돌 (같은 코드 수정) | 높음 | 태스크별 독립 파일 범위 확인, 충돌 감지 시 사용자에게 경고 |
| Cursor 중첩 불가로 워커→QA 호출 불가 | 높음 | 오케스트레이터가 QA 호출로 통일 (§3.3에서 결정) |
| Gemini CLI max_turns/timeout 초과 | 중간 | 충분한 값 설정 (max_turns: 50, timeout: 30분), 단계별 워커 분리로 작업 크기 제한 |
| Antigravity에서 컨텍스트 격리 불가 | 낮음 | 폴백: 직접 실행. 워커 SKILL.md의 절차는 동일하게 적용 |
| 워커 디스패치 오버헤드 | 낮음 | 컨텍스트 격리 이점이 오버헤드보다 큼 |
