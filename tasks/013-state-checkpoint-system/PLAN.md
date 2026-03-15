# PLAN: task-flow STATE.md 체크포인트 시스템 추가

> 작성일: 2026-03-15 | 모드: Short Task | 참조: TASK.md

## 1. 코드 분석

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `skills/task-flow/SKILL.md` | 메인 스킬 정의 — 워크플로우 전체 규칙 | O |
| `skills/task-flow/references/execute-guide.md` | EXECUTE 단계 상세 가이드 | O |
| `agents/claude/task-flow-agent/AGENT.md` | Claude Code 워커 에이전트 정의 | O |
| `agents/cursor/task-flow-agent.md` | Cursor 워커 에이전트 정의 | O |
| `agents/antigravity/task-flow-agent/SKILL.md` | Antigravity 워커 에이전트 (폴백) | O |
| `CLAUDE.md` | 프로젝트 컨벤션 — 산출물 저장 구조 정의 | O |

### 현재 구현

**상태 복원 메커니즘 (기존)**:
- `SKILL.md` 918행 "이어하기" 섹션: `tasks/{NNN}/` 폴더의 산출물 존재 여부로 마지막 완료 단계를 추론
  - 예: RESEARCH.md 있고 PLAN.md 없으면 → PLAN 단계 진입
- 864행: "tasks/ 폴더의 산출물 존재 여부로 상태를 복원할 수 있다"
- 한계: 진행 중 단계의 중간 상태(Step 3/7 완료), 의사결정 로그, 워커 ID, 미반영 사용자 지시 등이 유실됨

**워커 에이전트 실행 흐름**:
- 오케스트레이터가 워커를 디스패치 → 워커가 가이드를 읽고 실행 → 산출물 생성 → 결과 반환
- EXECUTE 시 Step 완료마다 TODO.md(Full) / PLAN.md(Short) 체크박스 갱신
- 현재 체크리스트 갱신만 하고, 별도 상태 파일은 없음

**산출물 저장 구조**:
- Full Task: TASK.md, RESEARCH.md, QA-RESEARCH.md, PLAN.md, QA-PLAN.md, TODO.md, QA-EXECUTE.md, TEST-REPORT.md, DONE.md
- Short Task: TASK.md, PLAN.md, QA-PLAN.md, QA-EXECUTE.md, DONE.md
- STATE.md는 아직 어디에도 정의되지 않음

### 영향 범위

**상위 의존 (STATE.md를 읽는/갱신하는 주체)**:
- 오케스트레이터 (SKILL.md) — 단계 시작/완료 시 STATE.md 갱신, 새 세션 시 STATE.md 읽기
- 워커 에이전트 (3개 플랫폼) — EXECUTE Step 진행 시 STATE.md 갱신
- QA/Planner/Test 에이전트 — 직접 갱신하지 않음 (오케스트레이터가 대리 갱신)

**하위 의존 (STATE.md가 참조하는 것)**:
- 태스크 폴더 내 산출물 파일들 (존재 여부 참조)
- 워커 에이전트 ID (resume 식별용)

**관련 테스트 파일**: 없음 (프로세스 문서 변경)

## 2. 구현 계획

### 변경 파일

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `skills/task-flow/SKILL.md` | STATE.md 갱신/복원 규칙 섹션 추가, 산출물 저장 구조에 STATE.md 추가, "이어하기" 고도화 |
| 2 | `skills/task-flow/references/execute-guide.md` | Step 완료 시 STATE.md 갱신 규칙 추가 |
| 3 | `agents/claude/task-flow-agent/AGENT.md` | 워커의 STATE.md 갱신 책임 명시 |
| 4 | `agents/cursor/task-flow-agent.md` | 동일 — STATE.md 갱신 책임 명시 |
| 5 | `agents/antigravity/task-flow-agent/SKILL.md` | 동일 — STATE.md 갱신 책임 명시 |
| 6 | `CLAUDE.md` | 산출물 저장 구조에 STATE.md 추가 |

### 핵심 설계

#### A. STATE.md 템플릿

```markdown
# STATE: {태스크 제목}

> 최종 갱신: YYYY-MM-DD HH:mm

## 현재 상태
- 모드: {Full Task / Short Task}
- 단계: {TASK / RESEARCH / PLAN / TODO / EXECUTE}
- 진행: {Step N/M 완료 (EXECUTE 시) / 완료 (비-EXECUTE 시)}
- 상태: {진행 중 / 대기 중 / 블로커 / 완료}

## 완료 산출물
| 산출물 | 상태 |
|--------|------|
| TASK.md | {완료 / 미생성} |
| RESEARCH.md | {완료 / 미생성 / 해당없음} |
| PLAN.md | {완료 / 진행 중 / 미생성} |
| TODO.md | {완료 / 미생성 / 해당없음} |
| QA-*.md | {완료 / 미생성} |
| DONE.md | {완료 / 미생성} |

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|

## 사용자 지시 (미반영)
{산출물에 아직 반영되지 않은 사용자 피드백/수정 지시}

## 블로커
{현재 블로커 상황 또는 "없음"}

## 다음 액션
{다음으로 수행할 작업}
```

**워커 정보 필드 제외 근거**: 캡틴의 원안에 `agent_id`, `resume 가능` 필드가 있었으나, 실제로 워커 ID는 플랫폼이 관리하며 STATE.md에 기록해도 세션 간 resume에는 사용되지 않는다. 산출물 존재 여부 + 현재 상태 필드로 복원에 충분하다.

#### B. STATE.md 갱신 규칙 (SKILL.md에 추가)

**갱신 주체**: 오케스트레이터 + 워커 (역할 분담)

| 이벤트 | 갱신 주체 | 갱신 내용 |
|--------|----------|----------|
| 태스크 생성 (TASK.md 작성 후) | 오케스트레이터 | STATE.md 초기 생성 |
| 단계 시작 (워커 디스패치) | 오케스트레이터 | `단계`, `상태: 진행 중` 갱신 |
| 단계 완료 (워커 반환) | 오케스트레이터 | `완료 산출물` 테이블 갱신, `상태: 대기 중` |
| EXECUTE Step 완료 | 워커 | `진행: Step N/M 완료` 갱신 |
| 의사결정 발생 | 오케스트레이터/워커 | `의사결정 로그` 행 추가 |
| 블로커 발생 | 워커 | `상태: 블로커`, `블로커` 섹션 갱신 |
| 사용자 피드백 (미반영) | 오케스트레이터 | `사용자 지시 (미반영)` 섹션 갱신 |
| 사용자 피드백 반영 완료 | 오케스트레이터/워커 | `사용자 지시 (미반영)` 클리어 |
| QA 완료 | 오케스트레이터 | `완료 산출물`에 QA 상태 추가 |
| DONE.md 생성 | 오케스트레이터 | `상태: 완료`, 전체 갱신 |

**갱신 방법**: Edit 도구로 해당 섹션만 교체 (1회 Edit 수준 오버헤드)

#### C. STATE.md 복원 프로토콜 (SKILL.md "이어하기" 고도화)

```
사용자: "이어서 해줘" / "XX 태스크 이어하기"
→ 1. tasks/{NNN}-{name}/STATE.md 존재 확인
→ 2-a. 존재 시: STATE.md Read → 현재 상태/단계/진행 파악 → 정확한 지점에서 재개
→ 2-b. 미존재 시: 기존 방식(산출물 존재 여부)으로 마지막 완료 단계 추론 → STATE.md 생성
→ 3. 복원 내용을 사용자에게 보고:
     "📋 태스크 복원: {태스크명}
      단계: {단계} | 진행: {Step N/M} | 상태: {상태}
      미반영 지시: {있음/없음}
      이어서 진행할까요?"
```

#### D. 워커 에이전트 STATE.md 갱신 책임 (3개 플랫폼 에이전트에 추가)

EXECUTE 단계에서 워커가 수행하는 STATE.md 갱신:
- 각 Step 완료 시: `진행: Step N/M 완료` 업데이트
- 블로커 발생 시: `상태: 블로커` + `블로커` 섹션 업데이트
- 의사결정 시: `의사결정 로그`에 행 추가

비-EXECUTE 단계(RESEARCH, PLAN, TODO)에서는 워커가 STATE.md를 갱신하지 않는다 (단계 시작/완료는 오케스트레이터가 관리).

#### E. CLAUDE.md / SKILL.md 산출물 구조 변경

Full Task와 Short Task 모두에 `STATE.md` 추가:
```
tasks/{NNN}-{태스크명}/
├── STATE.md             ← 실시간 상태 추적 (신규)
├── TASK.md
├── ...
```

## 3. 실행 체크리스트

- [x] Step 1: SKILL.md STATE.md 규칙 추가 — `skills/task-flow/SKILL.md` — STATE.md 갱신/복원 규칙 섹션 신설, 산출물 저장 구조에 STATE.md 추가, "이어하기" 섹션 STATE.md 기반으로 고도화
- [x] Step 2: execute-guide.md STATE.md 갱신 규칙 추가 — `skills/task-flow/references/execute-guide.md` — Step 완료 시 STATE.md 갱신 규칙, 블로커 시 STATE.md 갱신 규칙 추가
- [x] Step 3: 워커 에이전트 3개 플랫폼 업데이트 — `agents/claude/task-flow-agent/AGENT.md`, `agents/cursor/task-flow-agent.md`, `agents/antigravity/task-flow-agent/SKILL.md` — STATE.md 갱신 책임 섹션 추가
- [x] Step 4: CLAUDE.md 산출물 구조 갱신 — `CLAUDE.md` — Full Task / Short Task 산출물 저장 구조에 STATE.md 추가

## 4. QA 체크리스트

### 기능 테스트
- [x] STATE.md 템플릿이 TASK.md의 모든 요구사항(단계/Step/의사결정/블로커/사용자 지시)을 커버하는가?
- [x] 갱신 주체(오케스트레이터 vs 워커) 역할 분담이 명확한가?
- [x] 복원 프로토콜이 STATE.md 존재/미존재 두 경우를 모두 처리하는가?
- [x] DONE.md 생성 시 STATE.md가 "완료" 상태로 갱신되는가?

### 회귀 테스트
- [x] 기존 task-flow 워크플로우가 STATE.md 없이도 동작하는가? (하위 호환)
- [x] 기존 "이어하기" 기능이 STATE.md 미존재 시 종전 방식으로 폴백하는가?
- [x] 산출물 저장 구조 변경이 기존 태스크 폴더와 충돌하지 않는가?
- [x] 3개 플랫폼(Claude Code, Cursor, Antigravity) 에이전트 정의가 일관된가?

### 코드 품질
- [x] STATE.md 갱신 오버헤드가 최소화되었는가? (Edit 1회 수준)
- [x] 문서 간 STATE.md 관련 규칙이 일관적인가? (SKILL.md, execute-guide.md, AGENT.md)
- [x] 크로스 플랫폼 호환성이 유지되는가?
- [x] 문서 표준(한국어 본문, 영어 기술 용어)을 따르는가?
