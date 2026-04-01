# TODO: task-flow 워커 에이전트 실행 모델

> 작성일: 2026-03-14 | 참조: TASK.md, RESEARCH.md, PLAN.md

## Part A: 실행 체크리스트

> 총 16개 Step | 실행 모드: 복잡

### Step 1: 워커 에이전트 파일 생성 — Claude Code
- [x] 완료
- **파일**: `agents/claude/task-flow-agent/AGENT.md` (신규)
- **작업 내용**:
  - YAML frontmatter 작성: `name: task-flow-agent`, `description`에 워커 역할 기술, `model: inherit`
  - 본문 구조: 역할, 실행 프로세스(6단계), 단계별 가이드 매핑 테이블, 반환 형식(artifact_path/summary/status/blockers/changed_files), 실행 규칙(5개), EXECUTE 단계 추가 규칙(단순/복잡 모드)
  - PLAN.md 3.3절의 Claude 에이전트 스케치를 기반으로 작성
  - 핵심 규칙: "QA 에이전트는 호출하지 않는다 — 오케스트레이터가 별도 호출"
- **완료 기준**: `agents/claude/task-flow-agent/AGENT.md` 파일이 존재하고, YAML frontmatter + 본문(역할/프로세스/매핑/반환/규칙) 구조가 완비
- **테스트**: 파일 존재 확인, frontmatter name 필드가 `task-flow-agent`인지 확인
- **실행 방법**: direct
- **의존**: 없음

### Step 2: 워커 에이전트 파일 생성 — Cursor
- [x] 완료
- **파일**: `agents/cursor/task-flow-agent.md` (신규)
- **작업 내용**:
  - YAML frontmatter: `name: task-flow-agent`, `description`, `model: inherit`, `readonly: false`
  - Gemini CLI 호환 필드 추가: `tools` 배열(`read_file`, `write_file`, `grep_search`, `shell`, `list_directory`), `max_turns: 50`, `timeout_mins: 30`
  - 본문은 Step 1 Claude 버전과 동일한 핵심 내용을 플랫 파일 포맷으로 작성
  - Cursor/Gemini CLI 모두 플랫 파일 + YAML frontmatter 포맷이므로 동일 파일 재활용
- **완료 기준**: `agents/cursor/task-flow-agent.md` 파일이 존재하고, Claude 버전과 핵심 내용(역할/반환 형식/실행 규칙)이 동일
- **테스트**: Claude 버전과 교차 비교하여 핵심 내용 일치 확인
- **실행 방법**: direct
- **의존**: Step 1

### Step 3: 워커 에이전트 파일 생성 — Antigravity
- [x] 완료
- **파일**: `agents/antigravity/task-flow-agent/SKILL.md` (신규)
- **작업 내용**:
  - YAML frontmatter: `name: task-flow-agent`, `description`에 "메인 에이전트가 이 SKILL.md를 Read하고 지시에 따라 직접 실행" 폴백 패턴 명시
  - 본문은 동일한 핵심 내용이나, "서브 에이전트로 실행"이 아닌 "메인 에이전트가 Read 후 직접 수행"하는 폴백 구조 명시
- **완료 기준**: `agents/antigravity/task-flow-agent/SKILL.md` 파일이 존재하고, 폴백 패턴이 명시되어 있음
- **테스트**: 3개 플랫폼 파일 간 핵심 내용(역할/반환 형식/실행 규칙) 교차 비교 (T6)
- **실행 방법**: direct
- **의존**: Step 1

### Step 4: SKILL.md 재구성 — 워크플로우 개요 다이어그램 교체
- [x] 완료
- **파일**: `skills/task-flow/SKILL.md`
- **작업 내용**:
  - "워크플로우 개요" 섹션의 플로우 다이어그램을 오케스트레이터-워커 다이어그램으로 교체
  - 기존: `[RESEARCH] → [QA] → 검토` → 변경: `[워커: RESEARCH] → [QA] → 검토`
  - Full Task / Short Task 양쪽 다이어그램 모두 워커 디스패치 표현으로 변경
  - "핵심 규칙" 문구에 "오케스트레이터가 워커를 디스패치하여 실행" 추가
- **완료 기준**: 다이어그램에 "(워커)" 또는 "[워커: ...]" 표현이 포함되어 있고, TASK만 알투 직접 수행으로 표시
- **테스트**: 다이어그램이 PLAN.md 3.1절의 Full/Short 흐름과 일치하는지 확인 (S1, S2)
- **실행 방법**: direct
- **의존**: 없음

### Step 5: SKILL.md 재구성 — 오케스트레이터-워커 실행 모델 신규 섹션
- [x] 완료
- **파일**: `skills/task-flow/SKILL.md`
- **작업 내용**:
  - "모드 판별 규칙" 섹션과 "QA 에이전트 호출 규칙" 섹션 사이에 신규 섹션 "오케스트레이터-워커 실행 모델" 삽입
  - 하위 섹션 6개 작성:
    1. **오케스트레이터(알투)의 역할**: TASK 직접 수행, 워커 디스패치, QA/Planner/Test 호출, 게이트 중계, 상태 추적
    2. **워커 에이전트 정의**: 에이전트 이름 `task-flow-agent`, 6개 플랫폼별 탐색 경로, 워커의 역할(코드 읽기/분석, 산출물 작성, 코드 구현)
    3. **워커 디스패치 규칙**: 디스패치 시점, 프롬프트 구성법(PLAN.md 3.4절 워커 프롬프트 템플릿 전체 포함), 전달 정보, 단계별 이전 산출물 매핑 테이블
    4. **워커 결과 수신**: 반환 형식(artifact_path/summary/status/blockers), 성공 시 QA 호출 → 사용자 보고, 블로커 시 사용자 중계
    5. **워커 연속성 (Resume)**: resume 가능 시 분기(동일 워커 이어서 수행), resume 불가 시 분기(새 워커에 산출물 경로 전달), 플랫폼별 resume 지원 테이블, resume 가능 단계 쌍 + 가치 테이블
    6. **크로스 플랫폼 폴백**: 서브 에이전트 도구 사용 불가 시 오케스트레이터가 에이전트 파일 Read → 직접 실행, 플랫폼별 정리 테이블(Claude Code/Cursor/Gemini CLI/Antigravity)
- **완료 기준**: 6개 하위 섹션이 모두 존재하고, 워커 프롬프트 템플릿이 PLAN.md 3.4절과 일치
- **테스트**: 워커 에이전트 탐색 경로가 실제 파일 위치(Step 1~3)와 일치 (T1), 프롬프트 템플릿이 워커 에이전트 파일의 실행 프로세스와 정합 (T2)
- **실행 방법**: direct
- **의존**: Step 1, 2, 3

### Step 6: SKILL.md 재구성 — QA/Planner/Test 호출 주체 명확화
- [x] 완료
- **파일**: `skills/task-flow/SKILL.md`
- **작업 내용**:
  - "QA 에이전트 호출 규칙" 섹션: "서브 에이전트(Task 도구)로 호출" → "오케스트레이터가 서브 에이전트(Task 도구)로 호출"로 변경. 호출 맵 자체는 변경 없음
  - "Planner 에이전트 호출 규칙" 섹션: TODO 워커 완료 후 오케스트레이터가 복잡 모드 판정 → Planner 호출로 흐름 명확화. "TODO 워커가 Part A+B + 복잡도 판별 결과를 반환 → 오케스트레이터가 판정 확인 → 복잡 시 Planner 호출 → Part C 추가" 흐름 기술
  - "Test 에이전트 호출 규칙" 섹션: EXECUTE 워커 완료 후 오케스트레이터가 Test 호출로 명확화
- **완료 기준**: 3개 에이전트 호출 섹션 모두에 "오케스트레이터가" 호출 주체로 명시
- **테스트**: PLAN.md 3.11절의 호출 주체 결정과 일치하는지 확인
- **실행 방법**: direct
- **의존**: Step 5

### Step 7: SKILL.md 재구성 — Full Task STEP 2~5에 워커 디스패치 규칙 추가
- [x] 완료
- **파일**: `skills/task-flow/SKILL.md`
- **작업 내용**:
  - **STEP 2 (Full) RESEARCH**: "TASK.md의 요구사항을 바탕으로 분석한다" → "오케스트레이터가 RESEARCH 워커를 디스패치한다". 워커 디스패치 블록 추가(단계=RESEARCH, 이전 산출물=TASK.md, 가이드=research-guide.md). "워커 완료 시: 오케스트레이터가 QA 호출 → 사용자 보고" 명시. QA 호출 안내를 "오케스트레이터가 QA 호출"로 변경
  - **STEP 3 (Full) PLAN**: 워커 디스패치 블록 추가(단계=PLAN, 이전 산출물=TASK.md+RESEARCH.md, 가이드=plan-guide.md). resume 가능 시: RESEARCH 워커를 이어서 PLAN 수행. QA 호출 안내 변경
  - **STEP 4 (Full) TODO**: 워커 디스패치 블록 추가(단계=TODO, 이전 산출물=TASK.md+RESEARCH.md+PLAN.md, 가이드=todo-guide.md). 복잡 모드 분기: "워커가 Part A+B + 복잡도 판별 결과 반환 → 오케스트레이터가 판정 확인 → 복잡 시 Planner 호출"
  - **STEP 5 (Full) EXECUTE**: 워커 디스패치 블록 추가(단계=EXECUTE, 이전 산출물=TODO.md(+Part C), 가이드=execute-guide.md). 복잡 모드 + 중첩 불가 시 폴백: "오케스트레이터가 배치별 서브 에이전트 직접 디스패치". 워커 완료 시: 오케스트레이터가 Test(복잡) → QA 호출
- **완료 기준**: Full Task 4개 STEP 모두에 워커 디스패치 블록이 존재하고, 단계별 이전 산출물/가이드가 PLAN.md 3.4절 매핑 테이블과 일치
- **테스트**: Full Task 정상 흐름(S1), 복잡 모드 흐름(S3), Cursor 흐름(S4) 시나리오 워크스루
- **실행 방법**: direct
- **의존**: Step 5, 6

### Step 8: SKILL.md 재구성 — Short Task STEP 2~3에 워커 디스패치 규칙 추가
- [x] 완료
- **파일**: `skills/task-flow/SKILL.md`
- **작업 내용**:
  - **STEP 2 (Short) PLAN(통합)**: "TASK.md를 바탕으로 코드 분석 · 구현 계획 · 실행 체크리스트를 하나의 PLAN.md로 작성한다" → "오케스트레이터가 PLAN(통합) 워커를 디스패치한다". 워커 디스패치 블록(단계=PLAN-SHORT, 이전 산출물=TASK.md, 가이드=plan-guide.md Short 섹션). QA 호출 안내 변경
  - **STEP 3 (Short) EXECUTE**: "PLAN.md가 승인을 받으면 실행" → "오케스트레이터가 EXECUTE 워커를 디스패치한다". 워커 디스패치 블록(단계=EXECUTE-SHORT, 이전 산출물=TASK.md+PLAN.md, 가이드=execute-guide.md). QA 호출 안내 변경
- **완료 기준**: Short Task 2개 STEP 모두에 워커 디스패치 블록이 존재
- **테스트**: Short Task 정상 흐름(S2) 시나리오 워크스루
- **실행 방법**: direct
- **의존**: Step 5, 6

### Step 9: SKILL.md 재구성 — 다중 태스크 실행 신규 섹션
- [x] 완료
- **파일**: `skills/task-flow/SKILL.md`
- **작업 내용**:
  - "게이트 체크포인트 규칙" 섹션 뒤, "실행 모드" 섹션 앞에 "다중 태스크 실행" 신규 섹션 삽입
  - 하위 섹션 4개:
    1. **동시 실행 모델**: 태스크 A 검토 대기 중 태스크 B 워커 디스패치 가능, 독립 컨텍스트, `run_in_background` 활용
    2. **태스크 상태 추적**: 현재 단계/워커 상태/블로커 여부, tasks/ 폴더 산출물로 상태 복원
    3. **통합 보고**: 사용자 요청 시 전체 태스크 상태 일괄 보고
    4. **파일 충돌 경고**: EXECUTE 워커가 같은 파일 수정 시 경고
  - "실행 모드" 섹션에 다중 태스크 예시 추가
- **완료 기준**: "다중 태스크 실행" 섹션이 존재하고 4개 하위 섹션이 모두 포함
- **테스트**: 다중 태스크 동시 실행 시나리오(S6) 워크스루
- **실행 방법**: direct
- **의존**: Step 7, 8

### Step 10: execute-guide.md 워커 기반 전환
- [x] 완료
- **파일**: `skills/task-flow/references/execute-guide.md`
- **작업 내용**:
  - 문서 도입부에 워커 컨텍스트 프리앰블 추가 (PLAN.md 3.8절 공통 프리앰블)
  - **단순 모드**: "메인 에이전트가 Step 순서대로 직접 실행" → "워커가 Step 순서대로 실행"으로 주체 변경
  - **복잡 모드**: "서브 에이전트를 배치하여 실행" → "워커 내부에서 서브 에이전트를 배치하여 실행". 기존 서브 에이전트 프롬프트 구성(70~94줄)은 유지. "복잡 모드 + 중첩 불가 시" 폴백 규칙 추가: Cursor 등에서 워커가 내부 서브 에이전트 호출 불가 → 오케스트레이터가 배치별 서브 에이전트 직접 디스패치
  - **Short Task 모드**: 주체를 "워커가"로 변경
  - **QA 에이전트 호출 섹션**: "QA 에이전트를 호출하여" → "오케스트레이터가 QA 에이전트를 호출하여"로 변경. "워커는 QA를 호출하지 않는다" 안내 추가
  - 체크리스트 갱신 규칙은 기존 그대로 유지 (워커가 갱신)
- **완료 기준**: 모든 실행 모드(단순/복잡/Short)의 주체가 "워커"로 변경되고, QA 호출은 "오케스트레이터"로 명시
- **테스트**: SKILL.md의 EXECUTE 단계 기술과 execute-guide.md가 일관적인지 교차 참조 (T3)
- **실행 방법**: direct
- **의존**: Step 7, 8

### Step 11: research-guide.md 워커 프리앰블 추가
- [x] 완료
- **파일**: `skills/task-flow/references/research-guide.md`
- **작업 내용**:
  - 기존 첫 번째 블록인용("> **Full Task 전용**...") 뒤에 워커 컨텍스트 프리앰블 추가
  - 프리앰블 내용: "이 가이드는 워커 에이전트의 컨텍스트에서 실행된다. 오케스트레이터가 워커를 디스패치하면 워커가 이 가이드를 읽고 따른다. 서브 에이전트 사용 불가 플랫폼에서는 오케스트레이터가 직접 따른다. 프로세스 자체는 실행 주체와 무관하게 동일."
  - 문서 하단 "QA 에이전트 호출 (필수)" 섹션: "오케스트레이터가 QA를 호출한다 — 워커는 QA를 호출하지 않는다" 안내로 변경
  - 나머지 분석 프로세스 본문은 변경 없음
- **완료 기준**: 프리앰블이 추가되고, QA 호출 안내가 오케스트레이터 기준으로 변경
- **테스트**: SKILL.md의 워커 모델 설명과 프리앰블이 일관적인지 확인 (T3)
- **실행 방법**: direct
- **의존**: Step 5

### Step 12: plan-guide.md 워커 프리앰블 추가
- [x] 완료
- **파일**: `skills/task-flow/references/plan-guide.md`
- **작업 내용**:
  - 문서 도입부("이 가이드는 Full Task와 Short Task 모두에서 참조된다" 뒤)에 워커 컨텍스트 프리앰블 추가 (Step 11과 동일 내용)
  - Full Task PLAN 섹션 하단 QA 호출 안내: 오케스트레이터 기준으로 변경
  - Short Task 섹션 하단 QA 호출 안내: 동일 변경
  - 나머지 계획 수립 프로세스 본문은 변경 없음
- **완료 기준**: 프리앰블 추가 + Full/Short 양쪽 QA 호출 안내 변경
- **테스트**: SKILL.md의 워커 모델 설명과 프리앰블이 일관적인지 확인 (T3)
- **실행 방법**: direct
- **의존**: Step 5

### Step 13: todo-guide.md 워커 프리앰블 + 실행 방법 갱신
- [x] 완료
- **파일**: `skills/task-flow/references/todo-guide.md`
- **작업 내용**:
  - 도입부("> **Full Task 전용**..." 뒤)에 워커 컨텍스트 프리앰블 추가
  - "실행 방법 필드 규칙"의 `sub-agent` 설명을 워커 모델에 맞게 갱신: "복잡 모드에서 워커 내부의 서브 에이전트에 위임 (Part C 토폴로지에 따라 결정)"
  - "승인 요청" 섹션의 "메인 에이전트가 Step 순서대로 직접 실행" → "워커가 Step 순서대로 실행"으로 변경
  - "사용자 보고" 섹션: "TODO.md 작성 완료 후, 사용자에게 직접 보고한다" → 워커가 결과 반환 → 오케스트레이터가 사용자에게 보고하는 흐름으로 변경
- **완료 기준**: 프리앰블 추가 + 실행 방법/승인 요청/보고 흐름이 워커 모델 기준으로 갱신
- **테스트**: SKILL.md TODO 단계 기술과 todo-guide.md가 일관적인지 확인 (T3)
- **실행 방법**: direct
- **의존**: Step 5

### Step 14: CLAUDE.md Core Workflow 섹션 업데이트
- [x] 완료
- **파일**: `CLAUDE.md`
- **작업 내용**:
  - "Core Workflow: task-flow" 섹션 도입부에 오케스트레이터-워커 모델 설명 추가: "알투는 오케스트레이터로서 워커를 디스패치하고, 실제 분석/설계/실행은 워커의 격리된 컨텍스트에서 수행한다"
  - Full Task / Short Task 흐름도에 "(워커)" 표시 추가 (TASK만 직접, 나머지는 워커)
  - "적응적 실행" 문구 갱신: "서브 에이전트가 병렬 실행" → "워커가 디스패치되어 실행, 복잡 모드는 워커 내부에서 서브 에이전트 병렬 실행"
  - "컴포넌트 유형" 테이블의 Agents 행: "`agents/` 3개 x 3 플랫폼" → "`agents/` 4개 x 3 플랫폼"
  - "컴포넌트 간 의존 관계" 목록에 `task-flow-agent` 추가: "task-flow의 각 단계를 독립 컨텍스트에서 실행하는 워커 에이전트"
- **완료 기준**: Core Workflow 설명이 SKILL.md의 오케스트레이터-워커 모델과 일치 (T4)
- **테스트**: CLAUDE.md와 SKILL.md 간 흐름도/용어 교차 참조
- **실행 방법**: direct
- **의존**: Step 4, 5

### Step 15: install-mac.sh 배포 규칙 갱신
- [x] 완료
- **파일**: `scripts/install-mac.sh`
- **작업 내용**:
  - `install_claude()`: 라벨 "에이전트 (3개)" → "에이전트 (4개)"로 갱신 (236줄 부근)
  - `install_cursor()`: 라벨 "에이전트 (3개)" → "에이전트 (4개)"로 갱신 (245줄 부근)
  - `install_antigravity()`: 기존 루프가 `agents/antigravity/*/`을 자동 복사하므로 에이전트 수 라벨 불필요 (변경 없음)
  - **Gemini CLI agents 배포 추가**: `install_antigravity()` 함수 끝에 Cursor 에이전트 파일을 `~/.gemini/agents/`에 복사하는 로직 추가. `mkdir -p "$USER_HOME/.gemini/agents"` → `agents/cursor/*.md`를 복사
- **완료 기준**: Claude/Cursor 에이전트 수 라벨이 4개로 갱신, Gemini CLI agents 배포 로직이 추가
- **테스트**: install-mac.sh 스크립트 로직 검토 — 워커 에이전트가 정상 배포되는지 확인 (T5)
- **실행 방법**: direct
- **의존**: Step 1, 2, 3

### Step 16: 영향 파일 교차 검증 + OPAL 레지스트리 갱신
- [x] 완료
- **파일**: `opal/core/references/agents.md`, 그 외 V1~V5 검증 대상
- **작업 내용**:
  - **V1** `execute-plan-guide.md`: Part C 토폴로지가 워커 모델과 충돌 없는지 확인 (EXECUTE 워커 내부에서 서브 에이전트 디스패치 구조이므로 기존 그대로 유효)
  - **V2** `task-flow-qa/AGENT.md`: 호출 주체가 오케스트레이터로 변경되었을 뿐, 에이전트 자체 인터페이스(입력/출력)는 변경 없음을 확인
  - **V3** `task-flow-planner/AGENT.md`: TODO 워커 완료 후 오케스트레이터가 호출하는 구조와 호환되는지 확인
  - **V4** `task-flow-test/AGENT.md`: EXECUTE 워커 완료 후 오케스트레이터가 호출하는 구조와 호환되는지 확인
  - **V5** `opal/core/references/agents.md`: `task-flow-agent` 항목 추가 (역할: 워커 에이전트, 호출 시점: 각 단계 시작 시, 입력: 단계/태스크 경로/가이드 경로, 출력: 산출물 + 결과 반환)
- **완료 기준**: V1~V4 호환성 확인 완료, agents.md에 task-flow-agent 항목이 추가
- **테스트**: 기존 에이전트 호출 인터페이스 변경 없음 확인 (T7), 3개 플랫폼 파일 핵심 내용 동일 확인 (T6)
- **실행 방법**: direct
- **의존**: Step 1, 2, 3, 5, 6, 7, 8, 10

---

## Part B: QA 체크리스트

### B-1. 기능 테스트

- [ ] T1: SKILL.md의 워커 에이전트 탐색 경로가 실제 파일 위치(`agents/claude/task-flow-agent/AGENT.md`, `agents/cursor/task-flow-agent.md`, `agents/antigravity/task-flow-agent/SKILL.md`)와 일치하는가
- [ ] T2: SKILL.md의 워커 프롬프트 템플릿이 워커 에이전트 파일의 실행 프로세스/반환 형식과 정합하는가
- [ ] T3: references/ 가이드(research/plan/todo/execute)의 프리앰블이 SKILL.md의 워커 모델 설명과 일관적인가
- [ ] T4: CLAUDE.md의 Core Workflow 설명이 SKILL.md의 오케스트레이터-워커 모델과 일치하는가
- [ ] T5: install-mac.sh가 워커 에이전트를 3개 플랫폼 + Gemini CLI에 정상 배포하는가
- [ ] T6: 3개 플랫폼 에이전트 파일의 핵심 내용(역할, 반환 형식, 실행 규칙)이 동일한가
- [ ] T7: 기존 QA/Planner/Test 에이전트 파일과의 호환성 (호출 인터페이스 변경 없음) 확인

### B-2. 시나리오 워크스루

- [ ] S1: Full Task 정상 흐름 (Claude Code) — 각 단계 워커 디스패치 → QA 호출 → 사용자 보고가 명확히 기술
- [ ] S2: Short Task 정상 흐름 (Claude Code) — PLAN(통합) + EXECUTE 워커 디스패치가 명확
- [ ] S3: Full Task 복잡 모드 (Claude Code) — TODO 워커 → Planner → EXECUTE 워커 → 내부 서브 에이전트 → Test → QA 흐름
- [ ] S4: Full Task (Cursor) — 중첩 불가로 인한 QA/Planner/Test 오케스트레이터 호출이 명확
- [ ] S5: Full Task (Antigravity) — 폴백 규칙이 명확하고 가이드 프로세스가 동일 적용
- [ ] S6: 다중 태스크 동시 실행 — 태스크 간 독립성, 파일 충돌 경고 기술
- [ ] S7: resume 시나리오 — RESEARCH → PLAN 워커 연속성이 명확히 기술

### B-3. 회귀 테스트

- [ ] 기존 게이트 체크포인트 보고 형식이 변경되지 않았는가
- [ ] 기존 QA 호출 맵(RESEARCH/PLAN/EXECUTE에서 호출, TASK/TODO에서 생략)이 유지되는가
- [ ] 기존 복잡도 판별 기준(Step 수, 파일 수, 모듈 범위 등)이 변경되지 않았는가
- [ ] 기존 산출물 저장 구조(Full/Short)가 변경되지 않았는가
- [ ] 기존 체크리스트 갱신 규칙(Full: TODO.md, Short: PLAN.md)이 유지되는가
- [ ] Short Task의 에스컬레이션 규칙이 유지되는가

### B-4. 코드 품질

- [ ] 모든 문서가 한국어로 작성되었는가 (기술 용어 영어 병기)
- [ ] 파일/폴더 명명이 kebab-case를 따르는가 (`task-flow-agent`)
- [ ] 3개 플랫폼 에이전트 파일 포맷이 각 플랫폼 규칙을 따르는가 (Claude=디렉토리/AGENT.md, Cursor=플랫 파일, Antigravity=디렉토리/SKILL.md)
- [ ] SKILL.md 내 마크다운 문법(헤딩 레벨, 코드 블록, 테이블)이 올바른가
- [ ] install-mac.sh 변경이 기존 함수 구조/패턴과 일관적인가

### B-5. 보안

- [ ] 에이전트 파일에 하드코딩된 토큰/시크릿이 없는가
- [ ] install-mac.sh 변경에 권한 에스컬레이션이 없는가

---

## 복잡도 판별

| 기준 | 값 | 판정 |
|------|-----|------|
| Step 수 | 16개 | 복잡 (>5) |
| 변경 파일 수 | 10개 (N1~N3 신규 3 + M1~M7 수정 7) | 복잡 (>3) |
| 모듈 범위 | 다중 (skills, agents, opal, scripts, 루트) | 복잡 |
| 작업 유형 | 대규모 기능 개선 | 복잡 |
| 외부 의존성 | 없음 | 단순 |

**판정: 복잡 모드**

> 4/5 기준이 복잡 모드에 해당. 단, 이 태스크는 마크다운 문서 수정이므로 코드 빌드/테스트 리스크는 낮음. 서브 에이전트 배치 실행보다는 순차 직접 실행이 적합 (문서 간 정합성 유지가 핵심).

---

## Part C: 실행 아키텍처 (복잡 모드 시 task-flow-planner가 생성)

{복잡 모드로 판정되었으나, 이 태스크는 마크다운 문서 수정만 수행하므로 서브 에이전트 배치 실행 대신 단순 순차 실행을 권장한다. Planner가 필요하다고 판단되면 오케스트레이터가 호출한다.}

---

## 승인 요청

> 위 TODO가 사용자의 승인을 받으면 EXECUTE 단계를 시작합니다.
> 이 태스크는 마크다운 문서 수정이므로, 복잡 모드 판정이나 워커가 Step 순서대로 직접 실행합니다.
> 총 16개 Step, 변경 파일 10개 (신규 3 + 수정 7).
