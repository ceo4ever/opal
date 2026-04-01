# PLAN: task-flow 워커 에이전트 실행 모델

> 작성일: 2026-03-14 | 참조: TASK.md, RESEARCH.md

## 1. 구현 범위

### 신규 생성 파일

| # | 파일 경로 | 역할 |
|---|----------|------|
| N1 | `agents/claude/task-flow-agent/AGENT.md` | Claude Code 워커 에이전트 정의 |
| N2 | `agents/cursor/task-flow-agent.md` | Cursor 워커 에이전트 정의 |
| N3 | `agents/antigravity/task-flow-agent/SKILL.md` | Antigravity 워커 에이전트 (폴백용 SKILL) |

### 수정 파일

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| M1 | `skills/task-flow/SKILL.md` (638줄) | 오케스트레이터-워커 모델로 전면 재구성. 워커 디스패치 섹션 신규, 각 STEP에 워커 위임 규칙 추가, 다중 태스크 섹션 신규 |
| M2 | `skills/task-flow/references/execute-guide.md` (213줄) | 기존 "단순 모드=직접 실행" → "워커가 실행" 구조로 변경. 복잡 모드의 서브 에이전트 프롬프트를 워커 내부 서브 에이전트 구조로 정리 |
| M3 | `skills/task-flow/references/research-guide.md` (119줄) | 워커 컨텍스트에서 실행된다는 프리앰블 추가. 가이드 자체 프로세스는 변경 없음 |
| M4 | `skills/task-flow/references/plan-guide.md` (185줄) | 워커 컨텍스트에서 실행된다는 프리앰블 추가. Full/Short 모두 동일 |
| M5 | `skills/task-flow/references/todo-guide.md` (174줄) | 워커 컨텍스트에서 실행된다는 프리앰블 추가. "실행 방법" 필드의 sub-agent 설명을 워커 모델에 맞게 갱신 |
| M6 | `CLAUDE.md` | Core Workflow 섹션에 오케스트레이터-워커 모델 반영 |
| M7 | `scripts/install-mac.sh` | 워커 에이전트 파일 배포 추가 (에이전트 수 3→4 표기 갱신) |

### 영향 확인 (변경 없지만 검증 필요)

| # | 파일 경로 | 확인 사항 |
|---|----------|----------|
| V1 | `skills/task-flow/references/execute-plan-guide.md` | Part C 토폴로지가 워커 모델과 충돌 없는지 확인 (EXECUTE 워커 내부에서 서브 에이전트를 디스패치하는 구조이므로, 기존 그대로 유효) |
| V2 | `agents/claude/task-flow-qa/AGENT.md` | 호출 주체가 "메인 에이전트 → 오케스트레이터"로 명칭만 변경될 뿐, 에이전트 자체 변경 없음 |
| V3 | `agents/claude/task-flow-planner/AGENT.md` | 호출 시점(TODO 워커 내부 vs 오케스트레이터)에 따른 호환성 확인 |
| V4 | `agents/claude/task-flow-test/AGENT.md` | EXECUTE 워커 내부에서 호출되는 구조와의 호환성 확인 |
| V5 | `opal/core/references/agents.md` | 워커 에이전트 추가 시 레지스트리 갱신 필요 여부 확인 |

## 2. 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | 워커 에이전트 파일 생성 (Claude) | N1 | 높음 |
| 2 | 워커 에이전트 파일 생성 (Cursor) | N2 | 중간 |
| 3 | 워커 에이전트 파일 생성 (Antigravity) | N3 | 중간 |
| 4 | SKILL.md 전면 재구성 | M1 | 높음 |
| 5 | execute-guide.md 워커 기반 전환 | M2 | 높음 |
| 6 | research-guide.md 워커 프리앰블 추가 | M3 | 낮음 |
| 7 | plan-guide.md 워커 프리앰블 추가 | M4 | 낮음 |
| 8 | todo-guide.md 워커 프리앰블 갱신 | M5 | 낮음 |
| 9 | CLAUDE.md Core Workflow 업데이트 | M6 | 중간 |
| 10 | install-mac.sh 배포 규칙 갱신 | M7 | 낮음 |
| 11 | 영향 파일 교차 검증 | V1~V5 | 낮음 |

> **순서 근거**: 워커 에이전트 파일(N1~N3)을 먼저 확정해야 SKILL.md에서 참조 경로와 호출 규칙을 정확히 기술할 수 있다. SKILL.md(M1)가 핵심 허브이므로 references 가이드(M2~M5)보다 선행한다.

## 3. 핵심 설계

### 3.1 오케스트레이터-워커 아키텍처 개요

```
변경 후 모델:

┌──────────────────────────────────────────────────────┐
│ 오케스트레이터 (알투)                                    │
│                                                      │
│ [TASK 직접] → 디스패치 → 게이트 → 디스패치 → ... → 보고    │
│                 │          ↕          │               │
│              워커(격리)   사용자     워커(격리)           │
│              RESEARCH              PLAN              │
│              코드 Read             설계 Write          │
│              → .md 반환            → .md 반환          │
│                                                      │
│ QA/Planner/Test: 오케스트레이터가 직접 호출              │
└──────────────────────────────────────────────────────┘
```

**Full Task 흐름:**
```
알투: TASK.md 작성 (직접) → 사용자 검토
알투: → [워커: RESEARCH] → RESEARCH.md 반환
알투: → [QA 에이전트] → QA-RESEARCH.md → 사용자 검토
알투: → [워커: PLAN] → PLAN.md 반환
알투: → [QA 에이전트] → QA-PLAN.md → 사용자 검토
알투: → [워커: TODO] → TODO.md 반환 → 사용자 검토(승인)
알투: → [워커: EXECUTE] → 코드 변경 반환
알투: → [QA 에이전트] → QA-EXECUTE.md → 완료 보고
```

**Short Task 흐름:**
```
알투: TASK.md 작성 (직접) → 사용자 검토
알투: → [워커: PLAN(통합)] → PLAN.md 반환
알투: → [QA 에이전트] → QA-PLAN.md → 사용자 검토(승인)
알투: → [워커: EXECUTE] → 코드 변경 반환
알투: → [QA 에이전트] → QA-EXECUTE.md → 완료 보고
```

### 3.2 변경 후 SKILL.md 구조

현재 SKILL.md의 구조를 유지하면서, 오케스트레이터-워커 모델 관련 섹션을 삽입한다.

```
## 구현 금지 원칙                            (기존 유지)

## 워크플로우 개요                            (변경 — 오케스트레이터-워커 다이어그램)
  - 기존 플로우 다이어그램을 워커 디스패치 다이어그램으로 교체
  - "알투가 직접 수행" → "알투가 워커를 디스패치" 표현으로 변경

## 모드 판별 규칙                             (기존 유지)

## ★ 오케스트레이터-워커 실행 모델 (신규 섹션)
  ### 오케스트레이터(알투)의 역할
    - TASK 단계 직접 수행 (사용자 지시 구조화)
    - 워커 디스패치 및 결과 수신
    - QA/Planner/Test 에이전트 호출
    - 게이트 체크포인트에서 사용자 중계
    - 태스크 상태 추적 및 보고
  ### 워커 에이전트 정의
    - 에이전트 이름: task-flow-agent
    - 탐색 경로 (6개 플랫폼별 경로)
    - 워커의 역할: 코드 읽기/분석, 산출물 작성, 코드 구현/수정
  ### 워커 디스패치 규칙
    - 디스패치 시점: 각 단계 시작 시 (RESEARCH/PLAN/TODO/EXECUTE)
    - 프롬프트 구성법 (§3.4 워커 프롬프트 템플릿 참조)
    - 전달 정보: 단계, 태스크 경로, 이전 산출물 경로, 가이드 경로
  ### 워커 결과 수신
    - 반환 형식: artifact_path, summary, status, blockers
    - 성공 시: QA 호출 → 사용자 보고
    - 블로커 시: 사용자에게 블로커 중계
  ### 워커 연속성 (Resume)
    - resume 가능 시: 동일 워커를 이어서 다음 단계 수행
    - resume 불가 시: 새 워커에 이전 산출물(.md) 경로 전달
    - 플랫폼별 resume 지원: Claude Code(O), Cursor(O), Gemini(X), Antigravity(X)
  ### 크로스 플랫폼 폴백
    - 서브 에이전트 도구 사용 불가 시: 오케스트레이터가 워커 에이전트 파일을 Read하고 직접 실행
    - references/ 가이드는 실행 주체와 무관하게 동일 적용

## QA 에이전트 호출 규칙                      (기존 유지 + 호출 주체=오케스트레이터 명시)
  - "서브 에이전트(Task 도구)로 호출" → "오케스트레이터가 서브 에이전트로 호출"
  - QA 호출 맵 변경 없음

## Planner 에이전트 호출 규칙                  (기존 유지 + 호출 주체 명확화)
  - TODO 워커 완료 후 복잡 모드 판정 시, 오케스트레이터가 Planner 호출
  - 또는: TODO 워커 내부에서 Planner 호출 (Claude Code/Cursor 중첩 가능 시)
  - Cursor 중첩 불가 → 오케스트레이터가 호출하는 것을 기본 규칙으로

## Test 에이전트 호출 규칙                     (기존 유지 + 호출 주체 명확화)
  - EXECUTE 워커 완료 후, 오케스트레이터가 Test 호출

## 작업 유형 판별                              (기존 유지)
## 산출물 저장 구조                            (기존 유지)
## 프로젝트 컨텍스트 로딩                      (기존 유지)
## 사전 점검: Git 커밋 확인                    (기존 유지)

## STEP 1: TASK                              (기존 유지 — 알투가 직접 수행)

## STEP 2~5 Full Task 경로                   (변경)
  각 STEP에 "워커 디스패치" 블록 추가:
  ### STEP 2 (Full): RESEARCH
    - 기존: "TASK.md의 요구사항을 바탕으로 분석한다"
    - 변경: "오케스트레이터가 RESEARCH 워커를 디스패치한다"
    - 워커 디스패치 블록: 단계=RESEARCH, 이전 산출물=TASK.md, 가이드=research-guide.md
    - 워커 완료 시: 오케스트레이터가 QA 호출 → 사용자 보고
  ### STEP 3 (Full): PLAN
    - 워커 디스패치 블록: 단계=PLAN, 이전 산출물=TASK.md+RESEARCH.md, 가이드=plan-guide.md
    - resume 가능 시: RESEARCH 워커를 이어서 PLAN 수행
  ### STEP 4 (Full): TODO
    - 워커 디스패치 블록: 단계=TODO, 이전 산출물=TASK.md+RESEARCH.md+PLAN.md, 가이드=todo-guide.md
    - 복잡 모드 판정 시: 오케스트레이터가 Planner 호출 → Part C 추가
  ### STEP 5 (Full): EXECUTE
    - 워커 디스패치 블록: 단계=EXECUTE, 이전 산출물=TODO.md(+Part C), 가이드=execute-guide.md
    - 워커 완료 시: 오케스트레이터가 Test 호출(복잡 모드) → QA 호출 → 사용자 보고

## STEP 2~3 Short Task 경로                  (변경)
  ### STEP 2 (Short): PLAN(통합)
    - 워커 디스패치 블록: 단계=PLAN-SHORT, 이전 산출물=TASK.md, 가이드=plan-guide.md (Short 섹션)
  ### STEP 3 (Short): EXECUTE
    - 워커 디스패치 블록: 단계=EXECUTE-SHORT, 이전 산출물=PLAN.md, 가이드=execute-guide.md

## 게이트 체크포인트 규칙                      (기존 유지)

## ★ 다중 태스크 실행 (신규 섹션)
  ### 동시 실행 모델
    - 알투가 태스크 A 검토 대기 중 태스크 B 워커 디스패치 가능
    - 각 워커는 독립 컨텍스트 → 태스크 간 간섭 없음
    - run_in_background 활용 (Claude Code)
  ### 태스크 상태 추적
    - 각 태스크의 현재 단계, 워커 상태(진행 중/대기/완료), 블로커 여부
    - tasks/ 폴더의 산출물 존재 여부로 상태 복원 가능
  ### 통합 보고
    - 사용자 요청 시 전체 태스크 상태를 한 번에 보고
  ### 파일 충돌 경고
    - 여러 태스크의 EXECUTE 워커가 같은 파일을 수정하려 할 때 경고

## 실행 모드                                   (기존 유지 + 다중 태스크 예시 추가)
```

### 3.3 워커 에이전트 파일 설계

3개 플랫폼에 동일한 핵심 내용을 플랫폼별 포맷으로 작성한다.

#### 에이전트 이름 결정: `task-flow-agent`

기존 에이전트 네이밍 패턴(`task-flow-{역할}`)을 따른다. task-flow-qa(QA), task-flow-planner(설계), task-flow-test(검증)와 나란히, `task-flow-agent`는 실행 에이전트로서의 범용 역할을 나타낸다.

#### Claude Code: `agents/claude/task-flow-agent/AGENT.md`

```yaml
---
name: task-flow-agent
description: |
  task-flow 파이프라인의 각 단계(RESEARCH/PLAN/TODO/EXECUTE)를
  독립 컨텍스트에서 실행하는 워커 에이전트.
  오케스트레이터가 단계, 태스크 경로, 참조 가이드를 전달하면
  해당 단계의 산출물을 작성하거나 코드를 구현한다.
model: inherit
---
```

본문 구조:
```
# task-flow 워커 에이전트

## 역할
- 오케스트레이터로부터 지시받은 단계(RESEARCH/PLAN/TODO/EXECUTE)를 수행
- 산출물(.md)을 작성하거나 코드를 구현
- 완료 시 결과를 오케스트레이터에 반환

## 실행 프로세스
1. 오케스트레이터 프롬프트에서 단계, 태스크 경로, 가이드 경로를 확인
2. 프로젝트 CLAUDE.md를 읽어 코드 컨벤션 파악
3. 해당 단계의 references/ 가이드를 읽고 프로세스를 따름
4. 이전 단계 산출물이 있으면 읽어서 컨텍스트 확보
5. 산출물을 작성하거나 코드를 구현
6. 완료 시 결과 반환

## 단계별 가이드 매핑
| 단계 | 가이드 파일 | 산출물 |
|------|-----------|--------|
| RESEARCH | references/research-guide.md | RESEARCH.md |
| PLAN (Full) | references/plan-guide.md (Full Task 섹션) | PLAN.md |
| PLAN (Short) | references/plan-guide.md (Short Task 섹션) | PLAN.md |
| TODO | references/todo-guide.md | TODO.md |
| EXECUTE | references/execute-guide.md | 코드 변경 |

## 반환 형식
완료 시 아래 정보를 반환한다:
- **artifact_path**: 생성/수정한 산출물 경로
- **summary**: 핵심 요약 (3~5줄)
- **status**: success | blocked
- **blockers**: 블로커 목록 (있는 경우)
- **changed_files**: 변경 파일 목록 (EXECUTE 시)

## 실행 규칙
1. 가이드의 프로세스를 순서대로 따른다 — 임의 생략 금지
2. 산출물은 지정된 경로에 작성한다
3. 프로젝트 CLAUDE.md의 코드 컨벤션을 준수한다
4. 블로커 발생 시 즉시 status: blocked로 반환한다
5. QA 에이전트는 호출하지 않는다 — 오케스트레이터가 별도 호출

## EXECUTE 단계 추가 규칙
- 단순 모드: Step 순서대로 직접 실행, 각 Step 완료 시 체크박스 갱신
- 복잡 모드: Part C 토폴로지에 따라 내부 서브 에이전트 배치 실행
  - execute-guide.md의 서브 에이전트 프롬프트 구성 규칙을 따름
  - 내부 서브 에이전트는 워커의 컨텍스트 내에서 실행
```

#### Cursor: `agents/cursor/task-flow-agent.md`

```yaml
---
name: task-flow-agent
description: |
  task-flow 파이프라인의 각 단계를 독립 컨텍스트에서 실행하는 워커 에이전트.
model: inherit
readonly: false
---
```

본문은 Claude 버전과 동일한 핵심 내용. 단, Cursor 에이전트 포맷(플랫 파일)에 맞게 작성.

#### Antigravity: `agents/antigravity/task-flow-agent/SKILL.md`

```yaml
---
name: task-flow-agent
description: |
  task-flow 파이프라인의 각 단계를 실행하는 워커 스킬.
  Antigravity에서는 메인 에이전트가 이 SKILL.md를 Read하고 지시에 따라 직접 실행한다.
---
```

본문은 동일한 핵심 내용이나, "서브 에이전트로 실행"이 아닌 "메인 에이전트가 Read 후 직접 수행"하는 폴백 패턴임을 명시.

#### Gemini CLI 배포

Gemini CLI는 `.gemini/agents/*.md` 포맷을 사용한다. `install-mac.sh`에서 Antigravity 설치 시 `agents/antigravity/` → `~/.gemini/antigravity/skills/`로 복사하는 기존 로직이 있으나, Gemini CLI용 별도 에이전트 파일은 `~/.gemini/agents/task-flow-agent.md`에 배포해야 한다.

**결정**: Gemini CLI용은 install-mac.sh에서 Cursor 에이전트 파일을 `.gemini/agents/`에 복사하는 로직을 추가한다. Cursor와 Gemini CLI 모두 플랫 파일 + YAML frontmatter 포맷이므로 동일 파일 재활용 가능. 추가 tools/max_turns/timeout_mins 필드는 Gemini CLI가 인식하고 Cursor가 무시하므로 Cursor 파일에 포함해도 무방.

### 3.4 워커 프롬프트 템플릿

오케스트레이터가 워커를 디스패치할 때 전달하는 프롬프트 구조. SKILL.md의 "오케스트레이터-워커 실행 모델" 섹션에 기술한다.

```
## 워커 프롬프트 템플릿

오케스트레이터가 워커를 디스패치할 때, 아래 형식으로 프롬프트를 구성한다:

---
task-flow {단계명} 워커로서 아래 태스크를 수행하라.

**태스크**: {태스크 제목}
**단계**: {RESEARCH | PLAN | PLAN-SHORT | TODO | EXECUTE | EXECUTE-SHORT}
**태스크 폴더**: {tasks/{NNN}-{name}/}

**이전 산출물** (읽어서 컨텍스트를 확보하라):
- {tasks/{NNN}-{name}/TASK.md}
- {tasks/{NNN}-{name}/RESEARCH.md}  ← 해당 시
- {tasks/{NNN}-{name}/PLAN.md}      ← 해당 시
- {tasks/{NNN}-{name}/TODO.md}      ← 해당 시

**단계 가이드** (읽고 프로세스를 따르라):
- {skills/task-flow/references/{guide}.md 의 절대 경로}

**프로젝트 컨벤션** (읽고 규칙을 따르라):
- {프로젝트 루트의 CLAUDE.md 절대 경로}

**산출물 저장 경로**: {tasks/{NNN}-{name}/{산출물}.md}

**실행 규칙**:
1. 가이드를 읽고 프로세스를 따른다
2. 산출물을 저장 경로에 작성한다
3. 완료 시 artifact_path, summary, status를 반환한다
4. 블로커 발생 시 즉시 status: blocked로 반환한다
5. QA 에이전트는 호출하지 않는다
---
```

**단계별 이전 산출물 매핑:**

| 단계 | 이전 산출물 | 가이드 | 산출물 |
|------|-----------|--------|--------|
| RESEARCH | TASK.md | research-guide.md | RESEARCH.md |
| PLAN (Full) | TASK.md, RESEARCH.md | plan-guide.md (Full) | PLAN.md |
| PLAN (Short) | TASK.md | plan-guide.md (Short) | PLAN.md |
| TODO | TASK.md, RESEARCH.md, PLAN.md | todo-guide.md | TODO.md |
| EXECUTE (Full 단순) | TASK.md, TODO.md | execute-guide.md | 코드 변경 |
| EXECUTE (Full 복잡) | TASK.md, TODO.md (Part C 포함) | execute-guide.md | 코드 변경 |
| EXECUTE (Short) | TASK.md, PLAN.md | execute-guide.md | 코드 변경 |

### 3.5 워커 연속성 (Resume) 설계

```
워커 RESEARCH 완료 → 오케스트레이터가 worker_id 기록
사용자 승인 →
  IF resume 가능 (Claude Code / Cursor):
    같은 워커를 resume하여 PLAN 수행
    - RESEARCH 컨텍스트(코드 분석 결과) 보존 → PLAN 품질 향상
    - 추가 전달: "다음 단계는 PLAN이다. plan-guide.md를 읽고 따르라."
  ELSE (Gemini CLI / Antigravity / 새 워커):
    새 워커에 TASK.md + RESEARCH.md 경로 전달
    - 워커가 산출물을 Read하여 컨텍스트 복원
```

**resume 가능 단계 쌍:**
| 이전 단계 | 다음 단계 | resume 가치 | 이유 |
|----------|----------|------------|------|
| RESEARCH → PLAN | 높음 | 코드 분석 컨텍스트 보존으로 설계 품질 향상 |
| PLAN → TODO | 중간 | PLAN 설계 컨텍스트 보존 |
| TODO → EXECUTE | 낮음 | TODO는 문서 분해 단계라 컨텍스트가 가벼움 |

**구현**: SKILL.md의 각 STEP에서 "resume 가능 시" 분기를 기술. 실제 resume 여부는 플랫폼의 Agent/Task 도구 지원에 따라 런타임에 결정.

### 3.6 크로스 플랫폼 폴백 설계

```
워커 디스패치 시도:
  1. 서브 에이전트 도구(Agent/Task) 사용 가능?
     → YES: 워커 에이전트를 서브 에이전트로 디스패치
     → NO: 폴백 (2번으로)
  2. 워커 에이전트 파일을 Read → 지시 내용 확인 → 오케스트레이터가 직접 수행
     - 이 경우 컨텍스트 격리 이점은 없으나, 워커의 절차/규칙은 동일하게 적용
```

**플랫폼별 정리:**

| 플랫폼 | 워커 실행 방법 | resume | QA 호출 |
|--------|--------------|--------|---------|
| Claude Code | Agent 도구 → task-flow-agent | 가능 | 오케스트레이터 |
| Cursor | 서브 에이전트 자동 위임 / `/task-flow-agent` | 가능 | 오케스트레이터 |
| Gemini CLI | agents/task-flow-agent.md 자동 노출 | 불가 | 오케스트레이터 |
| Antigravity | 폴백: SKILL.md Read → 직접 실행 | 불가 | 오케스트레이터 |

### 3.7 execute-guide.md 변경 설계

기존 execute-guide.md의 구조를 유지하면서, "메인 에이전트가 직접 실행" → "워커가 실행"으로 주체를 변경한다.

**변경 포인트:**

1. **문서 도입부**: "워커 에이전트 컨텍스트에서 실행되는 가이드" 프리앰블 추가
2. **단순 모드**: "메인 에이전트가 Step 순서대로 직접 실행" → "워커가 Step 순서대로 실행"
3. **복잡 모드**: "서브 에이전트를 배치하여 실행" → "워커 내부에서 서브 에이전트를 배치하여 실행"
   - 복잡 모드의 서브 에이전트 프롬프트 구성(70~94줄)은 기존 그대로 유지
   - 워커가 내부적으로 서브 에이전트를 디스패치하는 구조 (Claude Code만 지원, Cursor 중첩 불가)
4. **Short Task 모드**: "PLAN.md 기반으로 실행" → "워커가 PLAN.md 기반으로 실행"
5. **QA 호출 제거**: 워커는 QA를 호출하지 않음 → "QA 에이전트 호출" 섹션을 "오케스트레이터가 호출" 안내로 변경
6. **체크리스트 갱신**: 워커가 TODO.md/PLAN.md 체크박스를 갱신하는 규칙은 기존 그대로

**복잡 모드 + 크로스 플랫폼 설계 결정:**

Cursor에서 워커(서브 에이전트)가 내부 서브 에이전트(배치 실행)를 호출할 수 없다 (중첩 불가). 이 경우:
- Cursor에서 복잡 모드 EXECUTE 시, 오케스트레이터가 배치별 서브 에이전트를 직접 디스패치
- 또는: 복잡 모드에서는 워커를 거치지 않고 오케스트레이터가 기존 방식대로 서브 에이전트 배치 실행

**결정**: execute-guide.md에 "복잡 모드 + 중첩 불가 시" 폴백 규칙을 명시. SKILL.md의 EXECUTE 단계에서 플랫폼별 분기를 기술.

### 3.8 references/ 가이드 공통 프리앰블

research-guide.md, plan-guide.md, todo-guide.md에 동일한 프리앰블을 추가한다:

```markdown
> **실행 컨텍스트**: 이 가이드는 워커 에이전트의 컨텍스트에서 실행된다.
> 오케스트레이터(알투)가 워커를 디스패치하면, 워커가 이 가이드를 읽고 프로세스를 따른다.
> 서브 에이전트 사용이 불가능한 플랫폼에서는 오케스트레이터가 직접 이 가이드를 따른다.
> 가이드의 프로세스 자체는 실행 주체와 무관하게 동일하다.
```

이 프리앰블 외에 가이드 본문의 프로세스는 변경하지 않는다. "누가 실행하든" 동일한 절차를 따르므로.

### 3.9 CLAUDE.md Core Workflow 섹션 변경

현재 CLAUDE.md의 "Core Workflow: task-flow" 섹션에 오케스트레이터-워커 모델을 반영한다.

**변경 포인트:**

1. **모델 설명 추가**: "알투는 오케스트레이터로서 워커를 디스패치, 실제 분석/설계/실행은 워커의 격리된 컨텍스트에서 수행" 문구 추가
2. **흐름도 업데이트**: 기존 흐름도에 "(워커)" 표시 추가
3. **"적응적 실행" 문구 갱신**: "서브 에이전트가 병렬 실행" → "워커가 디스패치되어 실행, 복잡 모드는 워커 내부에서 서브 에이전트 병렬 실행"
4. **컴포넌트 유형 테이블**: Agents 행에 `task-flow-agent` 추가 → "4개 x 3 플랫폼"

### 3.10 install-mac.sh 변경

현재 install-mac.sh는 `agents/{platform}/` 디렉토리를 통째로 복사한다.

**변경 불필요한 부분:**
- `install_claude`: `install_dir "$FRAMEWORK_ROOT/agents/claude" "$base/agents"` → 워커 에이전트 디렉토리가 `agents/claude/task-flow-agent/`에 추가되면 자동으로 복사됨
- `install_cursor`: `install_dir "$FRAMEWORK_ROOT/agents/cursor" "$base/agents"` → 동일
- `install_antigravity`: `agents/antigravity/*/` 루프 → 동일

**변경 필요한 부분:**
- 에이전트 수 표기: "에이전트 (3개)" → "에이전트 (4개)"로 각 플랫폼 install 함수의 라벨 갱신
- Gemini CLI 에이전트 배포: Cursor 에이전트 파일을 `.gemini/agents/`에도 복사하는 로직 추가 (신규)

```bash
# install-mac.sh 변경 — Gemini CLI agents 배포 추가
install_antigravity() {
    ...
    # 기존: skills + antigravity 에이전트 → ~/.gemini/antigravity/skills/

    # 신규 추가: Cursor 에이전트를 Gemini CLI agents로 복사
    local gemini_agents="$USER_HOME/.gemini/agents"
    mkdir -p "$gemini_agents"
    for agent_file in "$FRAMEWORK_ROOT/agents/cursor"/*.md; do
        if [[ -f "$agent_file" ]]; then
            cp "$agent_file" "$gemini_agents/"
        fi
    done
    success "Gemini CLI agents → $gemini_agents/"
}
```

### 3.11 Planner/Test 에이전트 호출 주체 결정

RESEARCH.md의 설계 결정(QA = 오케스트레이터 호출)을 확장하여 Planner/Test도 동일하게 결정한다.

| 에이전트 | 호출 주체 | 이유 |
|---------|----------|------|
| QA | 오케스트레이터 | Cursor 중첩 불가 대응. QA 결과를 사용자에게 직접 전달 |
| Planner | 오케스트레이터 | TODO 워커 완료 후, 복잡 모드 판정은 오케스트레이터가 수행. Planner 결과(Part C)를 TODO.md에 추가 후 사용자에게 보고 |
| Test | 오케스트레이터 | EXECUTE 워커 완료 후, 복잡 모드의 테스트는 오케스트레이터가 호출. Cursor 중첩 불가 대응 |

**결정**: QA/Planner/Test 모두 오케스트레이터가 호출. 워커는 산출물 작성에만 집중.

**이에 따른 TODO 워커 흐름 변경:**
```
기존: TODO 워커가 Part A+B 작성 → 복잡도 판별 → 복잡 시 Planner 호출 → Part C 추가
변경: TODO 워커가 Part A+B 작성 + 복잡도 판별 결과를 반환
      → 오케스트레이터가 복잡 판정 확인 → 복잡 시 Planner 호출 → Part C 추가
      → 사용자에게 보고
```

## 4. 의존성 및 환경 변경

### 신규 패키지/도구

없음. 이 태스크는 마크다운 문서 수정만 수행한다.

### 환경 설정 변경

없음.

### 플랫폼 요구사항

- Claude Code: Agent/Task 도구 지원 (기존 환경으로 충분)
- Cursor: 서브 에이전트 기능 활성화 필요 (기존 에이전트와 동일 조건)
- Gemini CLI: `experimental.enableAgents: true` 설정 필요 (기존 에이전트와 동일 조건)
- Antigravity: 추가 요구사항 없음 (폴백: 직접 실행)

## 5. 테스트 전략

### 문서 정합성 검증

이 태스크는 코드가 아닌 마크다운 문서를 수정하므로, 테스트는 문서 간 정합성 검증으로 수행한다.

| # | 검증 항목 | 검증 방법 |
|---|----------|----------|
| T1 | SKILL.md의 워커 에이전트 탐색 경로가 실제 파일 위치와 일치 | 경로 대조 |
| T2 | SKILL.md의 워커 프롬프트 템플릿이 워커 에이전트 파일의 실행 프로세스와 일치 | 교차 참조 |
| T3 | references/ 가이드의 프리앰블이 SKILL.md의 워커 모델 설명과 일관 | 교차 참조 |
| T4 | CLAUDE.md의 Core Workflow 설명이 SKILL.md와 일치 | 교차 참조 |
| T5 | install-mac.sh가 워커 에이전트를 정상 배포하는지 확인 | 스크립트 로직 검토 |
| T6 | 3개 플랫폼 에이전트 파일의 핵심 내용(역할, 반환 형식, 실행 규칙)이 동일 | 교차 비교 |
| T7 | 기존 QA/Planner/Test 에이전트 파일과의 호환성 (호출 인터페이스 변경 없음) | 교차 참조 |

### 시나리오 기반 워크스루

| # | 시나리오 | 확인 포인트 |
|---|---------|-----------|
| S1 | Full Task 정상 흐름 (Claude Code) | 각 단계에서 워커 디스패치 → QA 호출 → 사용자 보고가 문서에 명확히 기술되어 있는가 |
| S2 | Short Task 정상 흐름 (Claude Code) | PLAN(통합) + EXECUTE 워커 디스패치가 명확한가 |
| S3 | Full Task 복잡 모드 (Claude Code) | TODO 워커 → Planner → EXECUTE 워커 → 내부 서브 에이전트 → Test → QA 흐름 |
| S4 | Full Task (Cursor) | 중첩 불가로 인한 QA/Planner/Test 오케스트레이터 호출이 명확한가 |
| S5 | Full Task (Antigravity) | 폴백 규칙이 명확하고, 가이드 프로세스가 동일하게 적용되는가 |
| S6 | 다중 태스크 동시 실행 | 태스크 간 독립성, 파일 충돌 경고가 기술되어 있는가 |
| S7 | resume 시나리오 | RESEARCH → PLAN 워커 연속성이 명확하게 기술되어 있는가 |

## 6. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| SKILL.md 대폭 변경으로 기존 워크플로우 호환성 깨짐 | 높음 | 기존 섹션 구조를 최대한 유지하고 신규 섹션을 삽입하는 방식으로 변경. 게이트 체크포인트, 보고 형식 등 사용자 인터페이스는 변경하지 않음 |
| 워커 프롬프트가 너무 길어서 토큰 낭비 | 중간 | 프롬프트에 파일 내용을 인라인하지 않고 경로만 전달 → 워커가 직접 Read. 프롬프트 자체는 20줄 이내로 유지 |
| Cursor 복잡 모드에서 워커→내부 서브 에이전트 중첩 불가 | 높음 | 복잡 모드 EXECUTE는 오케스트레이터가 직접 배치 디스패치하는 폴백 규칙 명시. execute-guide.md에 "중첩 불가 시" 분기 기술 |
| 3개 플랫폼 에이전트 파일 내용 불일치 | 중간 | 핵심 내용(역할, 반환 형식, 실행 규칙)을 정규화하고, 플랫폼별 차이(frontmatter 필드)만 분리. QA에서 교차 검증 |
| Gemini CLI agents 배포 경로 신규 추가에 따른 install-mac.sh 복잡도 증가 | 낮음 | Cursor 에이전트 파일을 그대로 복사하는 단순 로직. 기존 패턴(install_dir)을 활용 |
| 다중 태스크 시 파일 충돌 | 높음 | SKILL.md에 "EXECUTE 워커 디스패치 전 다른 태스크의 변경 파일 범위 확인" 규칙 명시. 충돌 감지 시 사용자 경고 |
| resume 실패 시 워커 간 컨텍스트 손실 | 중간 | 산출물(.md)이 이미 핵심 정보를 담고 있으므로, 새 워커가 산출물을 Read하면 대부분 복원 가능. resume은 "있으면 좋은" 최적화로 포지셔닝 |
