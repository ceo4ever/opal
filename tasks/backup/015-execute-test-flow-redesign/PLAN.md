# PLAN: EXECUTE 후 검증 흐름 재설계 — task-flow-test 중심으로 전환

> 작성일: 2026-03-19 | 모드: Short Task | 참조: TASK.md

## 1. 코드 분석

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `agents/claude/task-flow-test/AGENT.md` | 테스트 에이전트 정의 (Claude) | O — 대폭 재설계 |
| `agents/cursor/task-flow-test.md` | 테스트 에이전트 정의 (Cursor) | O — Claude와 동기화 |
| `agents/antigravity/task-flow-test/SKILL.md` | 테스트 스킬 정의 (Antigravity) | O — Claude와 동기화 |
| `agents/claude/task-flow-qa/AGENT.md` | QA 에이전트 정의 (Claude) | O — EXECUTE 검증 제거 |
| `agents/cursor/task-flow-qa.md` | QA 에이전트 정의 (Cursor) | O — Claude와 동기화 |
| `agents/antigravity/task-flow-qa/SKILL.md` | QA 스킬 정의 (Antigravity) | O — Claude와 동기화 |
| `skills/task-flow/SKILL.md` | 오케스트레이터 스킬 | O — 흐름 재설계 |
| `skills/task-flow/references/execute-guide.md` | EXECUTE 상세 가이드 | O — test 호출 확장 |
| `skills/task-flow/references/execute-plan-guide.md` | 실행 아키텍처 가이드 | O — TEST-SCENARIO 참조 |
| `CLAUDE.md` | 프로젝트 설정 | O — 산출물 구조 갱신 |
| `skills/task-flow/references/test-scenario-guide.md` | 신규: 테스트 시나리오 가이드 | O — 신규 생성 |

### 현재 구현

**EXECUTE 후 검증 흐름 (현재)**:

1. **task-flow-test**: Full Task 복잡 모드에서만 호출. `TODO.md` Part B/C를 입력으로 받아 B-1~B-4 테스트 실행 후 `TEST-REPORT.md` 생성. 입력 파라미터: `task_path`, `todo_path`(또는 `checklist_path`), `changed_files`.

2. **task-flow-qa EXECUTE 검증**: 모든 모드에서 호출. E-1~E-7 체크리스트로 문서 기반 정적 리뷰 수행. `QA-EXECUTE.md` 생성. 입력 파라미터: `stage`, `mode`, `task_path`, `artifact_path`, `changed_files`, `test_report_path`.

3. **SKILL.md 흐름**:
   - QA 호출 맵: EXECUTE에서 Full/Short 모두 QA 호출
   - Test 호출: "Full Task 복잡 모드 전용" 명시 (312행)
   - 산출물 구조: `QA-EXECUTE.md` + `TEST-REPORT.md`(복잡 모드) 포함

4. **execute-guide.md 흐름**:
   - 단순 모드: Step 실행 -> QA 체크리스트 검증 -> QA 에이전트 호출 -> DONE.md
   - 복잡 모드: 서브 에이전트 실행 -> QA 체크리스트 검증 -> test 에이전트 -> QA 에이전트 -> DONE.md
   - Short Task: Step 실행 -> QA 체크리스트 검증 -> QA 에이전트 -> DONE.md
   - 최종 보고 형식에 `QA-EXECUTE.md` 참조

5. **execute-plan-guide.md**: 섹션 4 "테스트 전략 구체화"에서 B-1~B-4 실행 가능 형태로 구체화. `TEST-REPORT.md` 참조 없음, `TEST-SCENARIO.md` 참조 없음.

6. **CLAUDE.md 산출물 구조**: Full Task에 `QA-EXECUTE.md` + `TEST-REPORT.md`(복잡 모드), Short Task에 `QA-EXECUTE.md` 명시.

**테스트 시나리오 작성 (현재 부재)**:
- 테스트 시나리오는 PLAN/TODO의 QA 체크리스트 항목 수준으로만 존재
- 구체적 조건, 기대 결과를 정의하는 독립 산출물 없음
- task-flow-agent가 시나리오를 작성하는 프로세스 없음

### 영향 범위

**직접 영향 (변경 대상)**:
- task-flow-test 에이전트 3개 플랫폼 파일: 입력/출력/프로세스 전면 재설계
- task-flow-qa 에이전트 3개 플랫폼 파일: EXECUTE 관련 섹션 제거
- SKILL.md: QA 호출 맵, Test 호출 규칙, 산출물 구조, 워크플로우 다이어그램
- execute-guide.md: 3개 모드 모두 최종 단계 흐름 변경
- execute-plan-guide.md: 테스트 전략에서 TEST-SCENARIO.md 참조 추가

**간접 영향 (변경 없지만 확인 필요)**:
- `agents/claude/task-flow-agent/AGENT.md`: TEST-SCENARIO.md 작성 책임이 추가되지만, 이는 오케스트레이터가 디스패치 시 프롬프트로 전달하는 방식이므로 에이전트 파일 자체는 변경 불필요 (범용 워커)
- `skills/task-flow/references/todo-guide.md`: TODO.md의 Part B QA 체크리스트 구조는 유지 (task-flow-test가 참조하는 대상이 달라질 뿐)
- `skills/task-flow/references/plan-guide.md`: Short Task PLAN.md 섹션 4 QA 체크리스트도 유지

## 2. 구현 계획

### 변경 파일

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `skills/task-flow/references/test-scenario-guide.md` | **신규**: TEST-SCENARIO.md 작성 가이드 + 템플릿. task-flow-agent가 PLAN/TODO 후 시나리오 1~3 (대상+조건+기대)을 작성하는 프로세스 정의. 문서 전용 태스크 스킵 규칙 포함. |
| 2 | `agents/claude/task-flow-test/AGENT.md` | **대폭 재설계**: (a) 호출 시점을 모든 모드로 확장 (b) 입력을 `TEST-SCENARIO.md`로 변경 (c) 프로세스를 "시나리오 읽기 -> 도구 결정 -> 실행 -> 같은 파일에 결과 채움 -> 판정" 으로 재구성 (d) 출력을 `TEST-REPORT.md` 별도 생성 -> `TEST-SCENARIO.md` 인라인 갱신으로 변경 (e) 커뮤니티 스킬 디스커버리 유지 (f) 모드별 테스트 깊이 유지 (g) 문서 전용 태스크 스킵 규칙 유지 |
| 3 | `agents/cursor/task-flow-test.md` | #2와 동일 내용 (Cursor 포맷: 플랫 파일, description에 "에이전트"→"에이전트") |
| 4 | `agents/antigravity/task-flow-test/SKILL.md` | #2와 동일 내용 (Antigravity 포맷: "에이전트"→"스킬", readonly 없음, 코드 실행 가능 명시) |
| 5 | `agents/claude/task-flow-qa/AGENT.md` | **EXECUTE 검증 제거**: (a) 호출 시점에서 EXECUTE 행 삭제 (b) 입력에서 EXECUTE 추가 입력 삭제 (c) Step 1 산출물 읽기 테이블에서 EXECUTE 행 삭제 (d) EXECUTE 검증 기준 (E-1~E-7) 삭제 (e) 호출 예시에서 EXECUTE 예시 삭제 (f) description 갱신 |
| 6 | `agents/cursor/task-flow-qa.md` | #5와 동일 내용 (Cursor 포맷) |
| 7 | `agents/antigravity/task-flow-qa/SKILL.md` | #5와 동일 내용 (Antigravity 포맷) |
| 8 | `skills/task-flow/SKILL.md` | (a) 워크플로우 다이어그램에 TEST-SCENARIO 단계 추가 (b) QA 호출 맵에서 EXECUTE 행을 "test 호출"로 변경 (c) Test 에이전트 호출 규칙을 "모든 모드"로 확장 + 입력/전달 정보 갱신 (d) 산출물 구조에서 QA-EXECUTE.md 삭제, TEST-REPORT.md 삭제, TEST-SCENARIO.md 추가 (e) Full/Short 실행 흐름에 TEST-SCENARIO 단계 삽입 (f) EXECUTE 완료 후 흐름에서 QA 호출 -> test 호출로 변경 (g) 게이트 체크포인트에서 EXECUTE 보고 형식 갱신 (h) DONE.md 템플릿의 QA 결과 -> 테스트 결과로 갱신 (i) 워커 디스패치 단계별 산출물 매핑에 TEST-SCENARIO 추가 |
| 9 | `skills/task-flow/references/execute-guide.md` | (a) 3개 모드 모두 최종 단계에서 "QA 에이전트 호출 -> QA-EXECUTE.md" 를 "task-flow-test 호출 -> TEST-SCENARIO.md 결과 채움"으로 변경 (b) 최종 보고 형식에서 QA-EXECUTE.md 참조 삭제, TEST-SCENARIO.md 참조 추가 (c) 품질 체크리스트에서 QA-EXECUTE.md 항목 삭제, TEST-SCENARIO.md 항목 추가 (d) QA 에이전트 호출 안내 섹션 삭제 또는 "EXECUTE에서는 test 에이전트가 대체" 명시 |
| 10 | `skills/task-flow/references/execute-plan-guide.md` | 섹션 4 "테스트 전략 구체화" 서두에 TEST-SCENARIO.md 참조 안내 추가 (이미 작성된 시나리오를 기반으로 전략을 구체화한다는 컨텍스트) |
| 11 | `CLAUDE.md` | (a) 산출물 구조에서 QA-EXECUTE.md 삭제, TEST-REPORT.md 삭제 (b) TEST-SCENARIO.md 추가 (Full/Short 모두) (c) QA 호출 설명에서 EXECUTE 제거 (d) 워크플로우 다이어그램 갱신 |

### 핵심 설계

#### TEST-SCENARIO.md 템플릿 (신규 가이드에 포함)

```markdown
# TEST SCENARIO: {태스크 제목}

> 작성일: YYYY-MM-DD | 상태: {작성 완료 / 실행 완료}

## 시나리오 목록

### S-1: {시나리오 제목}

| 항목 | 내용 |
|------|------|
| 대상 | {테스트 대상 기능/변경점} |
| 조건 | {입력, 사전 상태, 환경} |
| 기대 결과 | {성공 기준} |
| 도구 | {task-flow-test가 채움: jest, pytest, Playwright 등} |
| 실행 명령 | {task-flow-test가 채움} |
| 결과 | {task-flow-test가 채움: Pass / Fail} |
| 상세 | {task-flow-test가 채움: 에러 메시지 등} |

### S-2: ...

## 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | {채움} | {채움} | {채움} |
| 2 | 타입 체크 | {채움} | {채움} | {채움} |
| 3 | 포맷터 | {채움} | {채움} | {채움} |

## 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | {채움} | {채움} |
| 2 | .gitignore 확인 | {채움} | {채움} |

## 회귀 테스트

| # | 테스트 스위트 | 결과 | 상세 |
|---|-------------|------|------|
| 1 | {채움} | {채움} | {채움} |

## 판정

**{task-flow-test가 채움: All Pass / Partial Fail / Critical Fail}** — {판정 근거}
```

**설계 포인트**:
- task-flow-agent가 작성하는 부분: 시나리오 목록의 대상/조건/기대 결과 (S-1~S-N)
- task-flow-test가 채우는 부분: 도구/실행 명령/결과/상세 + 코드 품질/보안/회귀/판정 전체
- 단일 파일로 계획과 실행 결과를 관리하여, 이전 TEST-REPORT.md의 역할을 흡수

#### task-flow-test 에이전트 재설계

**입력 변경**:
- 기존: `task_path`, `todo_path`/`checklist_path`, `changed_files`, `mode`
- 변경: `task_path`, `scenario_path` (TEST-SCENARIO.md 경로), `changed_files`, `mode`

**프로세스 변경**:
- Step 0: 테스트 스킬 디스커버리 (유지)
- Step 1: TEST-SCENARIO.md 읽기 + 테스트 환경 확인
- Step 2: 각 시나리오(S-1~S-N)에 대해 도구 결정 + 실행 + 결과 기록 (기존 B-1 기능 테스트에 해당)
- Step 3: 회귀 테스트 실행 (유지)
- Step 4: 코드 품질 검사 (유지)
- Step 5: 보안 검사 (유지)
- Step 6: TEST-SCENARIO.md에 결과 채움 + 판정 기록 (기존: TEST-REPORT.md 별도 생성)

**출력 변경**:
- 기존: `TEST-REPORT.md` 신규 생성
- 변경: `TEST-SCENARIO.md` 인라인 갱신 (기존 파일의 빈 칸을 채움)

#### task-flow-qa EXECUTE 제거

**삭제 대상**:
- 호출 시점의 `[EXECUTE 완료] -> QA Agent 호출 -> QA-EXECUTE.md` 행 (Full/Short 모두)
- 입력의 EXECUTE 추가 입력 테이블 (`changed_files`, `test_report_path`)
- Step 1 산출물 읽기 테이블의 EXECUTE 행 2개 (Full/Short)
- EXECUTE 검증 기준 섹션 (E-1~E-7)
- 호출 예시의 EXECUTE 예시 블록
- description에서 "EXECUTE" 관련 문구

**유지 대상**: RESEARCH, PLAN 검증 전체 (변경 없음)

#### SKILL.md 워크플로우 변경

**QA 호출 맵 변경**:

| 단계 | Full Task | Short Task |
|------|-----------|------------|
| TASK | 생략 | 생략 |
| RESEARCH | QA 호출 | (해당 없음) |
| PLAN | QA 호출 | QA 호출 |
| TODO | 생략 | (해당 없음) |
| EXECUTE | **test 호출** | **test 호출** |

**Test 에이전트 호출 규칙 변경**:
- 제목: ~~"(Full Task 복잡 모드 전용)"~~ -> "EXECUTE 완료 후 (모든 모드)"
- 전달 정보: `task_path`, `scenario_path`, `changed_files`, `mode`

**워크플로우 다이어그램**:
- Full: `... -> TODO -> TEST-SCENARIO 작성 -> 사용자 검토/승인 -> EXECUTE -> test 호출 -> DONE`
- Short: `... -> PLAN -> QA -> TEST-SCENARIO 작성 -> 사용자 검토/승인 -> EXECUTE -> test 호출 -> DONE`

#### execute-guide.md 흐름 변경

**단순 모드**: `... -> QA 체크리스트 검증 -> 결과 반환 -> 오케스트레이터: task-flow-test 호출 -> DONE.md -> 완료 보고`
**복잡 모드**: `... -> QA 체크리스트 검증 -> 결과 반환 -> 오케스트레이터: task-flow-test 호출 -> DONE.md -> 완료 보고`
**Short Task**: `... -> QA 체크리스트 검증 -> 결과 반환 -> 오케스트레이터: task-flow-test 호출 -> DONE.md -> 완료 보고`

(3개 모드 모두 동일한 최종 흐름으로 단순화)

## 3. 실행 체크리스트

- [x] Step 1: 신규 가이드 생성 — `skills/task-flow/references/test-scenario-guide.md` — TEST-SCENARIO.md 작성 프로세스 + 템플릿 + 문서 전용 스킵 규칙
- [x] Step 2: task-flow-test 에이전트 재설계 — `agents/claude/task-flow-test/AGENT.md` + `agents/cursor/task-flow-test.md` + `agents/antigravity/task-flow-test/SKILL.md` — 3개 플랫폼 동시 변경
- [x] Step 3: task-flow-qa EXECUTE 제거 — `agents/claude/task-flow-qa/AGENT.md` + `agents/cursor/task-flow-qa.md` + `agents/antigravity/task-flow-qa/SKILL.md` — 3개 플랫폼 동시 변경
- [x] Step 4: 오케스트레이터 스킬 갱신 — `skills/task-flow/SKILL.md` — 워크플로우/호출 규칙/산출물 구조 전면 갱신
- [x] Step 5: 실행 가이드 + 프로젝트 설정 갱신 — `skills/task-flow/references/execute-guide.md` + `skills/task-flow/references/execute-plan-guide.md` + `CLAUDE.md` — 참조 문서 동기화

## 4. QA 체크리스트

### 기능 테스트
- [x] TEST-SCENARIO.md 템플릿이 task-flow-agent(1~3) + task-flow-test(4+실행) 역할 분배를 정확히 반영하는가
- [x] task-flow-test의 입력이 `scenario_path`로 변경되었는가 (3개 플랫폼 모두)
- [x] task-flow-test의 출력이 TEST-SCENARIO.md 인라인 갱신으로 변경되었는가 (TEST-REPORT.md 별도 생성 제거)
- [x] task-flow-qa에서 EXECUTE 관련 내용이 완전히 제거되었는가 (3개 플랫폼 모두)
- [x] SKILL.md 워크플로우 다이어그램이 새 흐름을 반영하는가
- [x] SKILL.md QA 호출 맵에서 EXECUTE 행이 "test 호출"로 변경되었는가
- [x] 문서 전용 태스크 스킵 규칙이 test-scenario-guide.md에 포함되었는가

### 회귀 테스트
- [x] task-flow-qa의 RESEARCH/PLAN 검증 기준이 변경 없이 유지되는가
- [x] Planner 에이전트 호출 규칙(Full Task 복잡 모드 전용)이 변경 없이 유지되는가
- [x] task-flow-test의 커뮤니티 스킬 디스커버리(Step 0)가 유지되는가
- [x] task-flow-test의 모드별 테스트 깊이 차등 적용이 유지되는가
- [x] STATE.md 체크포인트 시스템이 변경 없이 유지되는가

### 코드 품질
- [x] 3개 플랫폼(Claude, Cursor, Antigravity) 파일의 내용이 동일한가 (포맷만 다름)
- [x] 모든 파일에서 QA-EXECUTE.md, TEST-REPORT.md 참조가 완전히 제거되었는가
- [x] 산출물 구조(CLAUDE.md, SKILL.md)에서 TEST-SCENARIO.md가 Full/Short 모두에 포함되었는가
