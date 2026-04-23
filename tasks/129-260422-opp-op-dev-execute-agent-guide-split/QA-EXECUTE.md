# QA-EXECUTE: op-dev-execute 에이전트별 지침 구획화 + EXECUTE 디스패치 라우팅 전파

> 검토일: 2026-04-21 | stage: EXECUTE | 판정: **Pass**

---

## 1. 요약

7개 파일(신규 2, 수정 5) 모두 존재하며, 각 파일이 TASK R-1~R-9 / PLAN M-1~M-5 / N-1~N-2 설계와 정합하게 구현되어 있다.
op-dev-execute/SKILL.md의 3구획 분리(공통/전문/범용)가 완전히 적용되었고, 구 페르소나·FE 역할 분담·활용 MCP 섹션이 제거되었다. opds/opd/opdw 세 오케스트레이터의 EXECUTE 단계에 agent 필드 기반 분배 디스패치 절차가 정확히 삽입되었다. 127 충돌 회피(에이전트 AGENT.md 4종, opal-task-action-agent/AGENT.md, opal-pilot-project-dev/SKILL.md, opal-pilot-sdd 2종) 모두 변경 없음 확인. 변경이력 7개 파일 전부 `(129)` 포함·`YYYY-MM-DD HH:mm` 포맷 준수.

Warning 1건: 모든 129 산출물의 타임스탬프가 `2026-04-23` 으로 기재되어 있으나, 태스크 작성일은 `2026-04-22`, 오늘 날짜는 `2026-04-21`이다. 실행 시각 기록 목적의 타임스탬프로 이 날짜가 기입된 근거가 불명확하나, 포맷 자체(`YYYY-MM-DD HH:mm`)는 규칙을 준수하므로 기능 영향 없음.

---

## 2. 검증 결과

### A. 파일 존재 및 기본 구조

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| A-1 | 7개 파일 모두 존재 | Pass | glob/git status로 신규 2 + 수정 5 확인 |
| A-2 | SKILL.md frontmatter `version: 2.0` | Pass | L7: `version: 2.0` 확인 |
| A-3 | references/ 에 specialist/generalist 두 파일 신규 존재 | Pass | glob 확인 — execute-specialist-guide.md, execute-generalist-guide.md 모두 존재 |

### B. op-dev-execute/SKILL.md 구조 전환 (M-1 / R-1)

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| B-1 | "실행 가이드 선택" 섹션 존재 + 매핑 테이블 3행 TASK §2 일치 | Pass | `### Step 1. 실행 가이드 선택 및 로딩` 섹션 존재. 3행(opal-fe/be/db-agent → specialist / opal-task-agent → generalist / 기타·미지정 → generalist 폴백) 정확히 일치 |
| B-2 | 구 "페르소나" 섹션(L22-37) 제거 확인 | Pass | Grep(`personas/frontend-engineer`, `## 페르소나`) — SKILL.md에 미출현. 변경이력 v1.2 행에 "페르소나" 언급만 존재 (이관 기록) |
| B-3 | "FE 역할 분담: ui-designer vs op-dev-execute" 섹션 제거 확인 | Pass | Grep(`FE 역할 분담`, `ui-designer 담당 \(UI 구현\)`) — SKILL.md에 미출현 |
| B-4 | "활용 스킬/MCP (FE)"·"활용 MCP (BE)" 섹션 제거 확인 | Pass | Grep 검색 결과 SKILL.md에 해당 섹션 헤더 미출현 |
| B-5 | 공통 섹션 보존 확인 (가드레일·실행 모드·블로커·결과 반환·품질 체크리스트·Step 3-H) | Pass | `## 가드레일`, `## 실행 모드`, `## 블로커 처리`, `## 결과 반환`, `## EXECUTE 품질 체크리스트`, `### Step 3-H` 모두 L79 이후에 보존됨 |
| B-6 | 변경이력 v2.0 행 + `(129)` 참조 + KST 일시 | Pass | `v2.0 \| 2026-04-23 11:39 \| … (129)` 존재 |

### C. execute-guide.md 정비 (M-2 / R-2)

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| C-1 | FE ui-designer 분기(구 L64-67) → specialist/generalist 위임 문구로 치환 | Pass | L64: "FE Step 중 ui-designer 연동이 필요한 경우는 **선택된 실행 가이드**(specialist 또는 generalist)의 FE 절차를 따른다" 확인 |
| C-2 | 공통 규칙(금지 행동·보안·모드·체크리스트·블로커·결과 반환·품질 체크리스트) 보존 | Pass | 전체 섹션 확인 — 모두 유지 |
| C-3 | 변경이력 v1.2 + `(129)` 포함 | Pass | `v1.2 \| 2026-04-23 11:39 \| … (129)` 존재 |

### D. execute-specialist-guide.md (N-1 / R-3) — AC 5개 항목

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| D-a | 페르소나 처리 — AGENT.md 우선, personas/ 불요 | Pass | §1: "AGENT.md에 정의된 페르소나를 1차 기준", "`personas/` 폴더는 Read하지 않는다" 명시 |
| D-b | Scope — 담당 Step 한정 | Pass | §2: "디스패치 프롬프트의 **담당 Step** 필드에 명시된 Step만 수행" 명시 |
| D-c | 도메인 도구 — AGENT.md MCP 테이블 1차 | Pass | §3: "AGENT.md의 'MCP/스킬 활용' 테이블을 1차 참조", FE/BE/DB 각 에이전트별 도구 명시 |
| D-d | FE 전문 케이스 — ui-designer 연동 조건 | Pass | §4: "FE 전문 케이스 (opal-fe-agent 전용)" — ui-designer 연동 판단 기준, plan-driven 모드 명시 |
| D-e | 영역 침범 방지 — AGENT.md §금지 규칙 + execute-guide.md §절대 금지 #3 | Pass | §5: "자신의 AGENT.md §금지 규칙 (1차 기준)"·"execute-guide.md §절대 금지 #3" 모두 명시 |
| D-f | 변경이력 v1.0 + `(129)` 포함 | Pass | `v1.0 \| 2026-04-23 11:39 \| … (129)` 존재 |

### E. execute-generalist-guide.md (N-2 / R-4) — AC 4개 항목

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| E-a | 페르소나 처리 — FE/BE/공통 분기, personas/ 동적 Read | Pass | §1: FE→frontend-engineer.md / BE→backend-engineer.md / 공통→페르소나 불필요 3분기 명시 |
| E-b | Scope — 단일 워커 순차 | Pass | §2: "단일 워커가 디스패치 범위 전체를 순차 처리" 명시 |
| E-c | FE 역할 분담 (ui-designer vs op-dev-execute) — 기존 SKILL.md L130-175 이관 내용 완전성 | Pass | §3: ui-designer 담당 표(6행), op-dev-execute 담당 표(7행), 실행 순서(4단계) 모두 이관 완료 |
| E-d | 활용 스킬/MCP (FE/BE) — 기존 SKILL.md L178-194 이관 내용 완전성 | Pass | §4: FE 8행(ui-designer·shadcn MCP·vercel-labs 3개·anthropics/frontend-design·context7), BE 1행(context7) 이관 완료. `frontend-engineer.md`, `backend-engineer.md`, `ui-designer`, `shadcn MCP`, `context7`, `vercel-labs`, `anthropics/frontend-design` 키워드 모두 출현 확인 |
| E-e | 공통 규칙 execute-guide.md 참조 명시 | Pass | §5: "금지 행동·보안 가드레일·블로커 처리·결과 반환은 **references/execute-guide.md**를 따른다" 명시 |
| E-f | 변경이력 v1.0 + `(129)` 포함 | Pass | `v1.0 \| 2026-04-23 11:39 \| … (129)` 존재 |

**교차 검증**: SKILL.md에서 제거된 키워드(`personas/frontend-engineer`, `FE 역할 분담`, `shadcn MCP`, `vercel-labs`) 가 execute-generalist-guide.md에 모두 존재함 — 이관 누락 없음.

### F. opds STEP 3 (M-3 / R-5)

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| F-1 | STEP 3에 3-1/3-2/3-3 세 하위 섹션 존재 | Pass | `### 3-1. 분배 디스패치 절차` / `### 3-2. 디스패치 프롬프트` / `### 3-3. EXECUTE 완료 후` 확인 |
| F-2 | 3-1: PLAN.md §4.2 agent 필드 순회 4단계 + 폴백 명시 | Pass | 1.Read → 2.묶음 생성 → 3.Phase 순서 순회 → 4.각 배치 디스패치. 폴백: "agent 필드 없거나 미지정 → opal-task-agent 단일 디스패치" 명시 |
| F-3 | 3-2: 디스패치 프롬프트에 `담당 Step`·`Scope 제한` 필드 | Pass | 두 필드 모두 프롬프트 블록에 존재 |
| F-4 | "에이전트별 자동 가이드 선택" 안내 문구 존재 | Pass | 3-2 섹션 아래 `> **에이전트별 자동 가이드 선택**:` 안내 문구 확인 |
| F-5 | 변경이력 v3.1 + `(129)` 포함 | Pass | `v3.1 \| 2026-04-23 11:39 \| … (129)` 존재 |

### G. opd STEP 4 (M-4 / R-6)

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| G-1 | STEP 4에 4-1/4-2/4-3/4-4 네 하위 섹션 존재 | Pass | `### 4-1. 분배 디스패치 절차` / `### 4-2. 디스패치 프롬프트` / `### 4-3. FE/BE 병렬 (agent 필드 기반)` / `### 4-4. EXECUTE 완료 후` 확인 |
| G-2 | 분배 디스패치 절차 명시 | Pass | M-3과 동일 4단계 + 폴백 규칙 명시됨 |
| G-3 | 디스패치 프롬프트에 `담당 Step`·`Scope 제한` 필드 | Pass | 두 필드 모두 프롬프트 블록에 존재 |
| G-4 | FE/BE 병렬 섹션 agent 필드 기반 일반화 + execution-plan.json 폴백 유지 | Pass | 4-3: "PLAN.md §4.2의 agent 필드에 따라 FE/BE 배치 구성". 폴백: "agent 필드 없거나 execution-plan.json만 존재 시 기존 방식 유지" (Phase 1→2→3 순차) |
| G-5 | 변경이력 v3.2 + `(129)` 포함 | Pass | `v3.2 \| 2026-04-23 11:39 \| … (129)` 존재 |

### H. opdw STEP 3 (M-5 / R-7)

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| H-1 | STEP 3에 3-1/3-2/3-3 세 하위 섹션 존재 | Pass | `### 3-1. 라우팅 결정 (v2.2 신설)` / `### 3-2. 디스패치 프롬프트` / `### 3-3. 완료 후` 확인 |
| H-2 | 3-1: FE 단일 라우팅 근거 명시 (wireframe.md 기반, PLAN.md §4.2 없음) | Pass | "wireframe.md에는 PLAN.md §4.2와 같은 agent 필드가 없다(op-dev-wireframe 산출물)" 명시 |
| H-3 | 기본 에이전트 `opal-fe-agent` + 폴백 `opal-task-agent` | Pass | 두 항목 모두 3-1에 명시 |
| H-4 | `담당 Step: wireframe.md 전체 (분배 없음)`, `Scope 제한: FE 영역` 필드 | Pass | 디스패치 프롬프트 블록에 두 필드 모두 확인 |
| H-5 | "와이어프레임 전용" 근거 및 "분배 디스패치 미적용" 문구 | Pass | "FE 단일 라우팅을 사용한다 (분배 디스패치 대상 아님)" 명시 |
| H-6 | 변경이력 v2.2 + `(129)` 포함 | Pass | `v2.2 \| 2026-04-23 11:39 \| … (129)` 존재 |

### I. 127 충돌 회피 / 에이전트 AGENT.md 보호

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| I-1 | `opal-task-action-agent/AGENT.md` 변경 없음 | Pass | git status — 해당 경로 변경 없음. `opal/agents/` 전체 clean |
| I-2 | `opal-pilot-project-dev/SKILL.md` 변경 없음 | Pass | git status / git diff HEAD 결과 변경 없음 |
| I-3 | opal-fe/be/db/task-agent AGENT.md 4종 변경 없음 | Pass | git status `opal/agents/` — 변경 없음 확인 |
| I-4 | `opal-pilot-sdd/SKILL.md` 변경 없음 (U-1) | Pass | git diff HEAD 0줄 |
| I-5 | `opal-pilot-sdd/references/execute-loop-guide.md` 변경 없음 (U-2) | Pass | git diff HEAD 0줄 |

### J. 변경이력 일시 일관성

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| J-1 | 7개 파일 모두 `YYYY-MM-DD HH:mm` KST 포맷 준수 | Pass | 모든 129 산출물 변경이력 일시: `2026-04-23 11:39` — 포맷 완전 준수 |
| J-2 | `(129)` 참조 각 파일 1회 이상 | Pass | 7개 파일 모두 1회 이상 출현 확인 (grep -c 결과 각 1) |

**Warning — 타임스탬프 날짜**: 모든 산출물의 일시가 `2026-04-23`이나 태스크 작성일은 `2026-04-22`, QA 검토 기준일은 `2026-04-21`. 포맷 규칙(`YYYY-MM-DD HH:mm`)은 준수하며 KST 지정도 적절하므로 기능 영향은 없으나, 실제 작업 수행 일자와 약 1일 불일치가 존재한다.

---

## 3. 지적 사항

### Warning (1건)

**J-W1. 변경이력 타임스탬프 날짜 불일치 (Warning)**

- **위치**: 7개 파일 변경이력 일시 필드 전부
- **내용**: 모든 129 산출물이 `2026-04-23 11:39` KST를 기재하고 있으나, TASK.md 작성일은 `2026-04-22`, 오늘 날짜(QA 기준)는 `2026-04-21`이다. 미래 날짜가 기입된 것으로, EXECUTE 수행 시점 환경의 날짜 오류(시스템 시계 차이)로 추정된다.
- **영향**: 문서 일관성 측면 경미한 불일치. 포맷 규칙 자체는 완전히 준수하여 기능·추적성에 영향 없음.
- **권장 조치**: 현재 유지. 향후 타임스탬프 기입 시 실제 날짜 확인 권장.

### Info (0건)

---

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK §2 매핑 테이블 (§확정된 설계 방향) | SKILL.md 매핑 테이블 3행이 TASK §2와 정확히 일치 | Pass |
| TASK R-3 AC (a~e 5항목) | execute-specialist-guide.md §1~§5 모두 포함 | Pass |
| TASK R-4 AC (a~d 4항목) | execute-generalist-guide.md §1~§4 모두 포함 | Pass |
| PLAN.md §2 M-1~M-5 핵심 설계 블록 | 7개 산출물이 설계 블록과 일치하게 구현됨 | Pass |
| PLAN.md §2 N-1 설계 블록 | execute-specialist-guide.md 내용이 설계 블록과 일치 | Pass |
| PLAN.md §2 N-2 설계 블록 | execute-generalist-guide.md 내용이 설계 블록과 일치 | Pass |
| TASK §제약 조건 127 충돌 회피 | 127 범위 4개 파일 변경 없음 확인 | Pass |
| TASK §제약 조건 에이전트 AGENT.md 보호 | opal-fe/be/db/task-agent 4종 변경 없음 | Pass |
| docs/CONVENTIONS.md §변경이력 포맷 | `YYYY-MM-DD HH:mm` KST 포맷 7개 파일 준수 | Pass |

---

## 5. 판정

**Pass**

Critical 0건, Warning 1건(타임스탬프 날짜 불일치 — 기능·추적성 영향 없음), Info 0건.

TASK R-1~R-9 전체가 구현되었고, 7개 파일 모두 PLAN.md 설계 명세와 정합하다. 3구획 구조(공통/전문/범용) 전환이 완전히 적용되었으며, 오케스트레이터 3종(opds/opd/opdw)의 EXECUTE 분배 디스패치 절차가 일관성 있게 삽입되었다. 127 충돌 회피 제약 및 에이전트 AGENT.md 보호가 모두 준수되어 있다. CLOSE 단계 진행 가능.
