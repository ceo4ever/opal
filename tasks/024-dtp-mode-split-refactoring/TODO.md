# TODO: dev-task-pilot 모드별 스킬/에이전트 분리 리팩토링

> 작성일: 2026-03-21 | 참조: TASK.md, ANALYSIS.md, PLAN.md

## Part A: 실행 체크리스트

> 총 12개 Step | 실행 모드: 복잡

---

### Step 1: modes/dev-full.md 작성
- [x] 완료
- **파일**: `skills/dev-task-pilot/modes/dev-full.md`
- **작업 내용**: Full Task 파이프라인 상세 문서 작성. 기존 SKILL.md의 "Full Task 경로" 섹션(STEP 2~5, ~300줄)을 독립 파일로 추출하여 재구성. TASK → ANALYSIS → PLAN → TODO → EXECUTE의 각 단계별 워커 디스패치 프롬프트 형식, 이전 산출물, 참조 가이드, 완료 시 호출 에이전트 정리.
- **완료 기준**: 파일이 생성되고, STEP 2~5의 각 단계별 워커 디스패치 정보가 완전히 포함됨
- **테스트**: 파일 존재 확인 + 섹션 내용 검증 (STEP 2~5 모두 포함, 에이전트명 갱신됨)
- **실행 방법**: direct
- **의존**: 없음

---

### Step 2: modes/dev-short.md 작성
- [x] 완료
- **파일**: `skills/dev-task-pilot/modes/dev-short.md`
- **작업 내용**: Short Task 파이프라인 상세 문서 작성. 기존 SKILL.md의 "Short Task 경로" 섹션(STEP 2~4, ~250줄)을 독립 파일로 추출. TASK → PLAN(통합) → TEST-SCENARIO → EXECUTE의 단계별 워커 디스패치 정보 정리.
- **완료 기준**: 파일이 생성되고, STEP 2~4(PLAN 통합, TEST-SCENARIO, EXECUTE)의 워커 디스패치 정보가 포함됨
- **테스트**: 파일 존재 확인 + 섹션 내용 검증 (Short Task 전용 단계 모두 포함)
- **실행 방법**: direct
- **의존**: 없음

---

### Step 3: modes/wireframe-ui.md 작성
- [x] 완료
- **파일**: `skills/dev-task-pilot/modes/wireframe-ui.md`
- **작업 내용**: Wireframe UI 파이프라인 신규 문서 작성(신규). TASK → WIREFRAME → EXECUTE → QA의 4단계 파이프라인 정의. 각 단계별 워커 디스패치, 스킬 호출(wireframe-builder, ui-designer), QA 에이전트 호출 규칙 포함. PLAN.md의 3.4 섹션 내용 기반.
- **완료 기준**: 파일이 생성되고, TASK(오케스트레이터 직접)/WIREFRAME/EXECUTE/QA의 4개 단계가 완전히 정의됨
- **테스트**: 파일 존재 확인 + 섹션 내용 검증 (입력물 분류 로직, 스킬 호출, QA 기준 명시)
- **실행 방법**: direct
- **의존**: 없음

---

### Step 4: references/wireframe-task-guide.md 작성
- [x] 완료
- **파일**: `skills/dev-task-pilot/references/wireframe-task-guide.md`
- **작업 내용**: Wireframe UI TASK 단계 가이드 신규 작성. 오케스트레이터가 직접 수행하는 Wireframe TASK 단계의 프로세스(목표 확인 → 입력물 분류 → TASK.md 작성 → 보고). PLAN.md의 3.5 섹션 기반. 입력물 상태별 판별 테이블 포함.
- **완료 기준**: 파일이 생성되고, 4단계 프로세스(목표 확인/입력물 분류/TASK.md 작성/보고)가 완전히 기술됨
- **테스트**: 파일 존재 확인 + 내용 검증 (입력물 분류 테이블, TASK.md 템플릿, 보고 형식)
- **실행 방법**: direct
- **의존**: 없음

---

### Step 5: references/wireframe-qa-guide.md 작성
- [x] 완료
- **파일**: `skills/dev-task-pilot/references/wireframe-qa-guide.md`
- **작업 내용**: Wireframe UI QA 가이드 신규 작성. dtp-qa-wireframe-agent가 WIREFRAME 단계(W-1~W-5 검증)와 EXECUTE 단계(E-1~E-6 검증)에서 사용하는 QA 기준 문서. PLAN.md의 3.6 섹션 기반. 두 시점별 검증 항목 테이블 포함.
- **완료 기준**: 파일이 생성되고, WIREFRAME 단계(W-1~W-5)와 EXECUTE 단계(E-1~E-6) 검증 항목이 완전히 기술됨
- **테스트**: 파일 존재 확인 + 내용 검증 (두 시점 검증 항목 모두 포함, QA 문서 출력 형식 명시)
- **실행 방법**: direct
- **의존**: 없음

---

### Step 6: Claude 에이전트 7개 생성 (dtp-dev-full-agent, dtp-dev-short-agent, dtp-wireframe-ui-agent, dtp-qa-dev-agent, dtp-qa-wireframe-agent, dtp-action-plan-agent, dtp-dev-test-agent)
- [x] 완료
- **파일**:
  - `agents/claude/dtp-dev-full-agent/AGENT.md`
  - `agents/claude/dtp-dev-short-agent/AGENT.md`
  - `agents/claude/dtp-wireframe-ui-agent/AGENT.md`
  - `agents/claude/dtp-qa-dev-agent/AGENT.md`
  - `agents/claude/dtp-qa-wireframe-agent/AGENT.md`
  - `agents/claude/dtp-action-plan-agent/AGENT.md`
  - `agents/claude/dtp-dev-test-agent/AGENT.md`
- **작업 내용**: Claude 플랫폼용 7개 에이전트 생성. 기존 dtp-agent/dtp-qa/dtp-planner/dtp-test를 기반으로 모드별 분리 및 리네임 수행. 각 에이전트의 Frontmatter(name, description, model, color 등) + 실행 프로세스 정의. PLAN.md의 3.7 섹션 명세 기반.
- **완료 기준**: 7개 파일이 모두 생성되고, 각 에이전트의 Frontmatter와 역할/입출력이 명확히 정의됨
- **테스트**: 파일 존재 확인 + 에이전트명 검증 (dtp-dev-full-agent, dtp-dev-short-agent 등 신규 이름 확인) + Frontmatter 필드 완전성 검증
- **실행 방법**: sub-agent (복잡 모드 Part C 토폴로지에 따라 병렬 생성 가능)
- **의존**: Step 1-5 완료

---

### Step 7: Cursor 에이전트 7개 생성 (플랫 파일)
- [x] 완료
- **파일**:
  - `agents/cursor/dtp-dev-full-agent.md`
  - `agents/cursor/dtp-dev-short-agent.md`
  - `agents/cursor/dtp-wireframe-ui-agent.md`
  - `agents/cursor/dtp-qa-dev-agent.md`
  - `agents/cursor/dtp-qa-wireframe-agent.md`
  - `agents/cursor/dtp-action-plan-agent.md`
  - `agents/cursor/dtp-dev-test-agent.md`
- **작업 내용**: Cursor 플랫폼용 7개 에이전트 생성. Claude 버전의 내용과 동일하되, 플랫 파일(.md) 형식으로 작성. Frontmatter 필드: name, description, model, readonly, tools, max_turns, timeout_mins 포함.
- **완료 기준**: 7개 .md 파일이 생성되고, Claude 버전과 동일한 에이전트 정의 포함
- **테스트**: 파일 존재 확인 + Frontmatter 필드 완전성 검증 (Cursor 포맷)
- **실행 방법**: sub-agent (복잡 모드 Part C 토폴로지에 따라 병렬 생성 가능)
- **의존**: Step 6 완료

---

### Step 8: Antigravity 에이전트 7개 생성 (SKILL.md 형식)
- [x] 완료
- **파일**:
  - `agents/antigravity/dtp-dev-full-agent/SKILL.md`
  - `agents/antigravity/dtp-dev-short-agent/SKILL.md`
  - `agents/antigravity/dtp-wireframe-ui-agent/SKILL.md`
  - `agents/antigravity/dtp-qa-dev-agent/SKILL.md`
  - `agents/antigravity/dtp-qa-wireframe-agent/SKILL.md`
  - `agents/antigravity/dtp-action-plan-agent/SKILL.md`
  - `agents/antigravity/dtp-dev-test-agent/SKILL.md`
- **작업 내용**: Antigravity 플랫폼용 7개 에이전트 생성. Claude 버전 + 폴백 모드 안내 문구 추가. SKILL.md 형식. Frontmatter 필드: name, description, model("gemini-3.1-pro"). 첫 섹션에 "Antigravity에서는 서브 에이전트 미지원" 안내.
- **완료 기준**: 7개 SKILL.md 파일이 생성되고, 폴백 모드 안내 포함
- **테스트**: 파일 존재 확인 + Frontmatter 필드 검증 + 폴백 안내 텍스트 확인
- **실행 방법**: sub-agent (복잡 모드 Part C 토폴로지에 따라 병렬 생성 가능)
- **의존**: Step 6 완료

---

### Step 9: 기존 에이전트 12개 삭제
- [x] 완료
- **파일**:
  - `agents/claude/dtp-agent/` (디렉토리 전체)
  - `agents/claude/dtp-qa/` (디렉토리 전체)
  - `agents/claude/dtp-planner/` (디렉토리 전체)
  - `agents/claude/dtp-test/` (디렉토리 전체)
  - `agents/cursor/dtp-agent.md`
  - `agents/cursor/dtp-qa.md`
  - `agents/cursor/dtp-planner.md`
  - `agents/cursor/dtp-test.md`
  - `agents/antigravity/dtp-agent/` (디렉토리 전체)
  - `agents/antigravity/dtp-qa/` (디렉토리 전체)
  - `agents/antigravity/dtp-planner/` (디렉토리 전체)
  - `agents/antigravity/dtp-test/` (디렉토리 전체)
- **작업 내용**: 기존 에이전트 12개 파일/디렉토리 삭제 (Claude 4개 + Cursor 4개 + Antigravity 4개). Step 6-8에서 생성한 신규 에이전트로 완전히 대체됨.
- **완료 기준**: 12개 파일/디렉토리가 모두 삭제됨 (git rm 사용)
- **테스트**: git 상태 확인 (12개 파일 "deleted" 표시) + ls로 디렉토리 미존재 확인
- **실행 방법**: direct
- **의존**: Step 6-8 완료

---

### Step 10: SKILL.md 리팩토링 (라우터화)
- [x] 완료
- **파일**: `skills/dev-task-pilot/SKILL.md`
- **작업 내용**: SKILL.md를 라우터로 리팩토링. 기존 1039줄 → ~400줄 축약. Full Task 경로 섹션(~300줄) 제거 → modes/dev-full.md 참조로 변경. Short Task 경로 섹션(~250줄) 제거 → modes/dev-short.md 참조로 변경. Wireframe UI 신규 경로 추가 → modes/wireframe-ui.md 참조. 에이전트명 갱신: dtp-agent → {dtp-dev-full/short/wireframe-ui-agent}, dtp-qa → {dtp-qa-dev/wireframe-agent}, dtp-planner → dtp-action-plan-agent, dtp-test → dtp-dev-test-agent.
- **완료 기준**: 리팩토링 완료 후 파일 크기 감소(1039줄 → ~400줄), 에이전트명 모두 갱신, 모드별 워커 디스패치 분기 명확함
- **테스트**: 파일 라인 수 확인 + grep으로 기존 에이전트명 검색(dtp-agent, dtp-qa 없음) + 신규 에이전트명 검색(모두 있음) + 구조 검증(라우터 섹션만 남음)
- **실행 방법**: direct
- **의존**: Step 1-3 완료

---

### Step 11: opal/core/references/agents.md 갱신
- [x] 완료
- **파일**: `opal/core/references/agents.md`
- **작업 내용**: 에이전트 레지스트리 전면 갱신. 기존 4개(dtp-agent, dtp-qa, dtp-planner, dtp-test) → 신규 7개(dtp-dev-full-agent, dtp-dev-short-agent, dtp-wireframe-ui-agent, dtp-qa-dev-agent, dtp-qa-wireframe-agent, dtp-action-plan-agent, dtp-dev-test-agent). 각 에이전트의 역할/호출 시점/입출력 명세 기술. PLAN.md의 3.8 섹션 명세 기반.
- **완료 기준**: 파일이 갱신되고, 신규 7개 에이전트가 모두 기재되고, 기존 4개는 제거됨
- **테스트**: 파일 내용 검증 (7개 에이전트명 모두 포함, 각 역할/호출 시점/입출력 명시)
- **실행 방법**: direct
- **의존**: Step 6-8 완료

---

### Step 12: CLAUDE.md 갱신
- [x] 완료
- **파일**: `CLAUDE.md` (프로젝트 루트)
- **작업 내용**: CLAUDE.md의 agents/ 섹션 갱신. 에이전트 구조 표를 기존 4개 → 신규 7개로 수정. PLAN.md의 3.9 섹션 내용 기반. 트리 구조로 7개 에이전트 나열 (dtp-dev-full/short/wireframe-ui-agent, dtp-qa-dev/wireframe-agent, dtp-action-plan-agent, dtp-dev-test-agent).
- **완료 기준**: CLAUDE.md의 agents/ 섹션이 갱신되고, 신규 7개 에이전트가 모두 나열됨
- **테스트**: 파일 내용 검증 (에이전트 목록 표 업데이트 확인)
- **실행 방법**: direct
- **의존**: Step 6-8 완료

---

## Part B: QA 체크리스트

### B-1. 기능 테스트

- [ ] Full Task 파이프라인이 ANALYSIS → PLAN → TODO → EXECUTE를 정상 실행하는가?
  - 기존 SKILL.md에서 Full Task 경로 섹션이 modes/dev-full.md로 완벽히 이관되었는가?
  - 각 단계별 워커 디스패치(dtp-dev-full-agent)가 올바르게 작동하는가?

- [ ] Short Task 파이프라인이 PLAN → TEST-SCENARIO → EXECUTE를 정상 실행하는가?
  - 기존 SKILL.md에서 Short Task 경로 섹션이 modes/dev-short.md로 완벽히 이관되었는가?
  - 각 단계별 워커 디스패치(dtp-dev-short-agent)가 올바르게 작동하는가?

- [ ] Wireframe UI 파이프라인이 TASK → WIREFRAME → EXECUTE → QA를 정상 실행하는가?
  - TASK 단계가 오케스트레이터 직접 실행되고, 입력물 분류가 정확하게 작동하는가?
  - WIREFRAME 단계에서 wireframe-builder 스킬이 호출되는가?
  - EXECUTE 단계에서 dtp-wireframe-ui-agent가 ui-designer를 호출하는가?

- [ ] 모드 판별 로직이 정확한가?
  - Full Task 조건(≥10개 파일 변경, 다단계 기술 의사결정)을 만족할 때 Full Task로 판별되는가?
  - Short Task가 기본값으로 작동하는가?
  - Wireframe UI 조건을 만족할 때 Wireframe UI로 판별되는가?

- [ ] 에이전트명 갱신이 완전한가?
  - SKILL.md의 모든 에이전트 참조가 신규 이름으로 업데이트되었는가?
  - dtp-agent → {dtp-dev-full/short/wireframe-ui-agent}, dtp-qa → {dtp-qa-dev/wireframe-agent} 등?

---

### B-2. 회귀 테스트

- [ ] 기존 Full Task 사용자 경험이 변경되지 않았는가?
  - 사용자가 "dev-task-pilot" 호출 → 같은 방식으로 Full Task 진행?
  - 산출물(TASK.md, ANALYSIS.md, PLAN.md, TODO.md, EXECUTE.md) 생성 순서/형식 동일?

- [ ] 기존 Short Task 사용자 경험이 변경되지 않았는가?
  - 사용자가 "dev-task-pilot" 호출 → 같은 방식으로 Short Task 진행?
  - 산출물(TASK.md, PLAN.md, TEST-SCENARIO.md, EXECUTE.md) 생성 순서/형식 동일?

- [ ] 기존 가이드 파일이 보존되었는가?
  - references/analysis-guide.md, plan-guide.md, execute-guide.md, todo-guide.md 등이 수정되지 않았는가?

- [ ] 기존 에이전트 호출 방식이 보존되었는가?
  - 오케스트레이터가 대신 새 에이전트명으로 디스패치하므로, 외부에서 직접 dtp-agent를 호출하지 않으면 문제없는가?

---

### B-3. 코드 품질

- [ ] SKILL.md 리팩토링이 명확한가?
  - 라우터 구조가 간결하고 이해하기 쉬운가?
  - 모드 판별 로직이 중복 없이 명확하게 표현되었는가?
  - 에이전트 탐색 경로가 명확하게 지정되었는가?

- [ ] 모드별 파일(modes/*.md)의 구조가 일관성이 있는가?
  - dev-full.md, dev-short.md, wireframe-ui.md가 유사한 포맷으로 작성되었는가?
  - 각 파일의 STEP 정의가 명확한가?

- [ ] 에이전트 정의가 일관성이 있는가?
  - 7개 에이전트의 Frontmatter 필드가 표준화되었는가?
  - 역할/입출력/실행 프로세스가 명확하고 일관된가?

- [ ] 신규 가이드(wireframe-task-guide.md, wireframe-qa-guide.md)의 품질이 충분한가?
  - 입력물 분류 로직이 명확한가?
  - QA 검증 항목이 검증 가능한가?

- [ ] 파일 명명이 프로젝트 컨벤션을 따르는가?
  - kebab-case 사용 (dtp-dev-full-agent, dtp-qa-dev-agent 등)?

---

### B-4. 보안

- [ ] 기존 에이전트 파일 삭제 시 코드 손실이 없는가?
  - Step 6-8에서 생성한 신규 에이전트에 기존 내용이 완벽히 복사/이관되었는가?
  - git history에 기존 에이전트 내용이 남아있는가?

- [ ] 신규 파일에 민감 정보가 포함되지 않았는가?
  - .env, 인증 파일 경로, API 키 등이 하드코딩되지 않았는가?

- [ ] PLAN.md/ANALYSIS.md/TASK.md 기반의 산출물이 보안 정책을 준수하는가?
  - 기존 Full/Short Task 보안 기준을 Wireframe UI 모드에도 적용했는가?

---

## Part C: 실행 아키텍처 (복잡 모드)

> 본 섹션은 Part A + B 작성 완료 후 dtp-action-plan-agent가 생성한다.

**예상 토폴로지:**
- **그룹 A** (Step 1-5): modes/ 파일 작성 (직렬, 의존 없음) → 병렬 실행 불가, 직렬 진행
  - Step 1: modes/dev-full.md
  - Step 2: modes/dev-short.md
  - Step 3: modes/wireframe-ui.md
  - Step 4: references/wireframe-task-guide.md
  - Step 5: references/wireframe-qa-guide.md

- **그룹 B** (Step 6-8): 에이전트 생성 (병렬 실행 가능, A 완료 후)
  - Step 6: Claude 7개 에이전트 (순차)
  - Step 7: Cursor 7개 에이전트 (순차)
  - Step 8: Antigravity 7개 에이전트 (순차)
  - → 6, 7, 8 병렬 실행 가능

- **그룹 C** (Step 9-12): 정리 및 갱신 (직렬)
  - Step 9: 기존 에이전트 삭제 (B 완료 후)
  - Step 10: SKILL.md 리팩토링
  - Step 11: agents.md 갱신
  - Step 12: CLAUDE.md 갱신

**병렬 실행 전략:**
1. Step 1-5 순차 (문서 작성, 의존성 있음)
2. Step 6-8 병렬 (에이전트 생성, 플랫폼별 독립)
3. Step 9-12 순차 (정리, 순차 의존성 있음)

**예상 소요 시간:**
- Group A: 약 30분 (문서 5개, 각 5-10분)
- Group B: 약 40분 (병렬 실행 시) / 약 60분 (순차)
- Group C: 약 20분 (파일 정리 + 갱신)
- **총 예상**: 약 90분 (병렬 최적화 시) / 120분 (순차)

---

## 승인 요청

> ⚠️ 위 TODO가 사용자의 승인을 받으면 EXECUTE 단계를 시작합니다.
>
> 본 태스크는 **복잡 모드**입니다:
> - Part A: 12개 Step
> - Part B: 4개 기능/회귀/품질/보안 검증 카테고리
> - Part C: 실행 아키텍처 (dtp-action-plan-agent가 생성)
>
> **단순 모드 실행**: 워커가 Step 1-12를 순차 진행합니다.
> **복잡 모드 실행**: 워커가 Part C 토폴로지에 따라 그룹 A(순차) → 그룹 B(병렬) → 그룹 C(순차)로 진행합니다.
