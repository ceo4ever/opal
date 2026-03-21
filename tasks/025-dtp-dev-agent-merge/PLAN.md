# PLAN: dtp-dev-full-agent + dtp-dev-short-agent → dtp-dev-agent 통합

> 작성일: 2026-03-21 | 모드: Short Task | 참조: TASK.md

## 1. 코드 분석

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `agents/claude/dtp-dev-full-agent/AGENT.md` | Full Task 워커 에이전트 정의 | 삭제 |
| `agents/claude/dtp-dev-short-agent/AGENT.md` | Short Task 워커 에이전트 정의 | 삭제 |
| `agents/cursor/dtp-dev-full-agent.md` | Cursor용 Full Task 워커 | 삭제 |
| `agents/cursor/dtp-dev-short-agent.md` | Cursor용 Short Task 워커 | 삭제 |
| `agents/antigravity/dtp-dev-full-agent/` | Antigravity용 Full Task 워커 | 삭제 |
| `agents/antigravity/dtp-dev-short-agent/` | Antigravity용 Short Task 워커 | 삭제 |
| `agents/claude/dtp-dev-agent/AGENT.md` | 통합 워커 에이전트 (신규) | 생성 |
| `agents/cursor/dtp-dev-agent.md` | Cursor용 통합 워커 (신규) | 생성 |
| `agents/antigravity/dtp-dev-agent/SKILL.md` | Antigravity용 통합 워커 (신규) | 생성 |
| `skills/dev-task-pilot/modes/dev-full.md` | Full 파이프라인 — 워커 에이전트명 참조 | 수정 |
| `skills/dev-task-pilot/modes/dev-short.md` | Short 파이프라인 — 워커 에이전트명 참조 | 수정 |
| `skills/dev-task-pilot/SKILL.md` | 오케스트레이터 라우터 — 에이전트 탐색 경로 기술 | 확인 |
| `opal/core/references/agents.md` | OPAL 에이전트 레지스트리 | 수정 |
| `CLAUDE.md` | 프로젝트 에이전트 구조 설명 | 수정 |

### 현재 구현

**dtp-dev-full-agent/AGENT.md 핵심 구조:**
- 역할: ANALYSIS / PLAN / TODO / TEST-SCENARIO / EXECUTE 수행
- 실행 프로세스: 6단계 (공통)
- 단계별 가이드 매핑: Full 전용 5개 단계
- 반환 형식: artifact_path, summary, status, blockers, changed_files (공통)
- 실행 규칙: 6개 항목 — 규칙 6번이 "Short Task 단계는 처리하지 않는다"
- STATE.md 갱신: EXECUTE 단계만 담당 (공통)
- EXECUTE 추가 규칙: 단순 모드 + 복잡 모드 (Full 전용)

**dtp-dev-short-agent/AGENT.md 핵심 구조:**
- 역할: PLAN-SHORT / TEST-SCENARIO / EXECUTE-SHORT 수행
- 실행 프로세스: 6단계 (동일, 공통)
- 단계별 가이드 매핑: Short 전용 3개 단계
- 반환 형식: 동일 (공통)
- 실행 규칙: 6개 항목 — 규칙 6번이 "Full Task 단계는 처리하지 않는다"
- STATE.md 갱신: EXECUTE-SHORT 단계만 담당 (공통과 동일한 패턴)
- EXECUTE 추가 규칙: EXECUTE-SHORT 단계 규칙 (Short 전용)

**공통 비율**: 실행 프로세스, 반환 형식, 실행 규칙 1~5번, STATE.md 갱신 구조가 동일 → 약 90%

**차이점**:
1. 단계별 가이드 매핑 테이블 (Full 5개 vs Short 3개, 겹치는 것: TEST-SCENARIO)
2. 실행 규칙 6번 (상대방 단계 배제 조항)
3. EXECUTE 추가 규칙 섹션 (Full: 단순+복잡 / Short: EXECUTE-SHORT 전용)
4. STATE.md 섹션의 "비-EXECUTE 단계" 열거 목록

**modes/dev-full.md 참조:**
```
> 워커 에이전트: `dtp-dev-full-agent`
```

**modes/dev-short.md 참조:**
```
> 워커 에이전트: `dtp-dev-short-agent`
```

**agents.md 참조:**
- `dtp-dev-full-agent` 섹션 + `dtp-dev-short-agent` 섹션 별도 존재

### 영향 범위

**상위 의존 (이 에이전트를 호출하는 곳):**
- `skills/dev-task-pilot/modes/dev-full.md` — 워커 에이전트명 문자열로 참조
- `skills/dev-task-pilot/modes/dev-short.md` — 워커 에이전트명 문자열로 참조
- `opal/core/references/agents.md` — 에이전트 레지스트리에 등록
- `CLAUDE.md` — agents/ 디렉토리 구조 문서화

**하위 의존 (에이전트가 참조하는 것):**
- `skills/dev-task-pilot/references/` 하위 가이드들 — 에이전트 내에서 경로만 언급, 변경 불필요
- SKILL.md 본문 — 에이전트 탐색 경로 설명이 있으나 에이전트명 명시 없음 (확인 결과 변경 불필요)

**관련 테스트 파일:** 없음 (에이전트 정의 문서 교체)

---

## 2. 구현 계획

### 변경 파일

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `agents/claude/dtp-dev-agent/AGENT.md` | 신규 생성 — Full+Short 통합 워커 에이전트 |
| 2 | `agents/cursor/dtp-dev-agent.md` | 신규 생성 — Cursor용 통합 워커 |
| 3 | `agents/antigravity/dtp-dev-agent/SKILL.md` | 신규 생성 — Antigravity용 통합 워커 |
| 4 | `agents/claude/dtp-dev-full-agent/AGENT.md` | 삭제 |
| 5 | `agents/claude/dtp-dev-short-agent/AGENT.md` | 삭제 |
| 6 | `agents/cursor/dtp-dev-full-agent.md` | 삭제 |
| 7 | `agents/cursor/dtp-dev-short-agent.md` | 삭제 |
| 8 | `agents/antigravity/dtp-dev-full-agent/` | 디렉토리 삭제 |
| 9 | `agents/antigravity/dtp-dev-short-agent/` | 디렉토리 삭제 |
| 10 | `skills/dev-task-pilot/modes/dev-full.md` | 워커 에이전트명 교체: `dtp-dev-full-agent` → `dtp-dev-agent` |
| 11 | `skills/dev-task-pilot/modes/dev-short.md` | 워커 에이전트명 교체: `dtp-dev-short-agent` → `dtp-dev-agent` |
| 12 | `opal/core/references/agents.md` | dtp-dev-full-agent + dtp-dev-short-agent → dtp-dev-agent 1개로 통합 |
| 13 | `CLAUDE.md` | agents/ 구조 설명에서 dtp-dev-full/short-agent 제거, dtp-dev-agent 추가 |

### 핵심 설계

**dtp-dev-agent/AGENT.md 구조 (통합 설계):**

```
---
name: dtp-dev-agent
description: |
  dev-task-pilot Full Task / Short Task 파이프라인의 각 단계를
  독립 컨텍스트에서 실행하는 워커 에이전트.
  오케스트레이터가 단계명(ANALYSIS/PLAN/PLAN-SHORT/TODO/TEST-SCENARIO/EXECUTE/EXECUTE-SHORT)과
  태스크 경로, 참조 가이드를 전달하면 해당 단계의 산출물을 작성하거나 코드를 구현한다.
model: sonnet
color: blue
---

# dev-task-pilot 워커 에이전트

## 역할 (공통)
## 실행 프로세스 (공통 6단계)
## 단계별 가이드 매핑 (Full + Short 통합 테이블)

| 단계 | 가이드 파일 | 산출물 | 권장 모델 |
|------|-----------|--------|----------|
| ANALYSIS | references/analysis-guide.md | ANALYSIS.md | haiku |
| PLAN (Full) | references/plan-guide.md (Full Task 섹션) | PLAN.md | sonnet |
| PLAN-SHORT | references/plan-guide.md (Short Task 섹션) | PLAN.md | sonnet |
| TODO | references/todo-guide.md | TODO.md | haiku |
| TEST-SCENARIO | references/test-scenario-guide.md | TEST-SCENARIO.md | haiku |
| EXECUTE | references/execute-guide.md | 코드 변경 | sonnet |
| EXECUTE-SHORT | references/execute-guide.md | 코드 변경 | sonnet |

## 반환 형식 (공통)
## 실행 규칙 (공통 5개 — 규칙 6번 배제 조항 제거)
## STATE.md 갱신 책임

비-EXECUTE 단계(ANALYSIS, PLAN, PLAN-SHORT, TODO, TEST-SCENARIO)에서는 갱신하지 않음.
EXECUTE 및 EXECUTE-SHORT 단계에서 워커가 갱신.

---

## EXECUTE 단계 추가 규칙

### Full Task: 단순 모드
### Full Task: 복잡 모드
### Short Task (EXECUTE-SHORT)
```

**cursor/dtp-dev-agent.md**: AGENT.md와 동일한 내용을 플랫 파일 형식으로 작성.

**antigravity/dtp-dev-agent/SKILL.md**: AGENT.md와 동일한 내용을 Antigravity 스킬 형식으로 작성.

---

## 3. 실행 체크리스트

- [x] Step 1: 통합 에이전트 생성 (claude) — `agents/claude/dtp-dev-agent/AGENT.md` — Full+Short 통합 내용으로 신규 생성
- [x] Step 2: 통합 에이전트 생성 (cursor, antigravity) — `agents/cursor/dtp-dev-agent.md`, `agents/antigravity/dtp-dev-agent/SKILL.md` — 동일 내용을 플랫폼별 형식으로 생성
- [x] Step 3: 기존 에이전트 삭제 — 6개 파일/디렉토리 삭제 (claude 2개, cursor 2개, antigravity 2개)
- [x] Step 4: 참조 갱신 — `modes/dev-full.md`, `modes/dev-short.md` 워커 에이전트명 교체
- [x] Step 5: 레지스트리 및 문서 갱신 — `agents.md`, `CLAUDE.md` 업데이트

---

## 4. QA 체크리스트

### 기능 테스트

- [ ] dtp-dev-agent/AGENT.md에 Full Task 모든 단계(ANALYSIS, PLAN, TODO, TEST-SCENARIO, EXECUTE)가 명시되어 있는가
- [ ] dtp-dev-agent/AGENT.md에 Short Task 모든 단계(PLAN-SHORT, TEST-SCENARIO, EXECUTE-SHORT)가 명시되어 있는가
- [ ] EXECUTE 추가 규칙에 Full(단순+복잡)과 Short 섹션이 모두 있는가
- [ ] 3개 플랫폼(claude, cursor, antigravity)에 dtp-dev-agent가 생성되었는가

### 회귀 테스트

- [ ] modes/dev-full.md에서 워커 에이전트명이 `dtp-dev-agent`로 변경되었는가
- [ ] modes/dev-short.md에서 워커 에이전트명이 `dtp-dev-agent`로 변경되었는가
- [ ] 기존 dtp-dev-full-agent, dtp-dev-short-agent 파일이 모두 삭제되었는가 (6개)
- [ ] dtp-wireframe-ui-agent는 변경 없이 그대로인가
- [ ] agents.md에서 dtp-dev-full-agent, dtp-dev-short-agent 섹션이 dtp-dev-agent 1개로 통합되었는가

### 코드 품질

- [ ] 통합 AGENT.md에서 한쪽 모드만 배제하는 조항(구 규칙 6번)이 제거되었는가
- [ ] 3개 플랫폼 파일의 내용이 일관성 있게 통일되었는가
- [ ] CLAUDE.md 에이전트 구조 설명이 실제 파일 구조와 일치하는가
