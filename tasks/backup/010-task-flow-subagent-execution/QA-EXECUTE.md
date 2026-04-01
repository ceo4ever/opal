# QA: EXECUTE -- task-flow 워커 에이전트 실행 모델

> 검토일: 2026-03-14 | 판정: ⚠️ Needs Revision

## 1. 요약

task-flow 파이프라인을 오케스트레이터-워커 아키텍처로 전환하는 작업이 완료되었다. SKILL.md를 중심으로 워커 디스패치 규칙, 프롬프트 템플릿, resume 연속성, 크로스 플랫폼 폴백이 체계적으로 기술되었고, 3개 플랫폼(Claude Code/Cursor/Antigravity)에 동일한 핵심 내용의 에이전트 파일이 생성되었다. references/ 가이드 4개 모두에 워커 컨텍스트 프리앰블이 추가되었고, QA 호출 주체가 "오케스트레이터"로 일관되게 변경되었다. 다만 Gemini CLI 에이전트 배포 경로가 SKILL.md 탐색 경로와 CLAUDE.md 배포 구조에 반영되지 않은 누락이 발견되었다.

## 2. 검증 결과

### E-1 ~ E-7: EXECUTE 기본 검증

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| E-1 | 체크리스트 갱신 완료 | ✅ | TODO.md Part A의 16개 Step 모두 `[x] 완료` 상태 |
| E-2 | 완료 기준 충족 | ✅ | 각 Step의 완료 기준이 실제 산출물에서 확인됨 |
| E-3 | 파일 변경 정합성 | ✅ | 변경 파일 11개(신규 3 + 수정 8)가 PLAN.md 목록(N1~N3, M1~M7, V5)과 일치. agents.md 수정은 V5 항목으로 계획됨 |
| E-4 | 코드 컨벤션 준수 | ✅ | 한국어 본문, 영어 기술 용어 병기, kebab-case 파일명(`task-flow-agent`), 플랫폼별 에이전트 포맷(Claude=디렉토리/AGENT.md, Cursor=플랫 파일, Antigravity=디렉토리/SKILL.md) 준수 |
| E-5 | 테스트 결과 확인 | ⚠️ | 마크다운 문서 수정이므로 코드 테스트 해당 없음. 문서 정합성 검증은 아래 T1~T7에서 수행 |
| E-6 | 블로커 해결 여부 | ✅ | 블로커 발생 없음 |
| E-7 | QA 체크리스트 충족 | ⚠️ | Part B 항목 중 T1에서 누락 발견 (아래 상세) |

### T1 ~ T7: 기능 테스트

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| T1 | SKILL.md 워커 에이전트 탐색 경로 vs 실제 파일 위치 | ⚠️ | 6개 탐색 경로 중 5개 정확. `~/.gemini/agents/task-flow-agent.md` 누락 -- install-mac.sh가 Cursor 에이전트를 `~/.gemini/agents/`에 배포하지만, SKILL.md 탐색 경로에는 이 경로가 없음. Gemini CLI에서 네이티브 에이전트로 인식되려면 이 경로가 포함되어야 함 |
| T2 | SKILL.md 워커 프롬프트 템플릿 vs 워커 에이전트 파일 | ✅ | 프롬프트의 실행 규칙 5개(가이드 따르기, 산출물 저장, 반환, 블로커 반환, QA 미호출)가 에이전트 파일의 실행 규칙과 일치. 반환 형식(artifact_path/summary/status/blockers)도 일치 |
| T3 | references/ 가이드 프리앰블 vs SKILL.md 워커 모델 | ✅ | 4개 가이드(research/plan/todo/execute) 모두 동일한 프리앰블 포함. QA 호출 안내도 "오케스트레이터가 호출, 워커는 미호출"로 일관 |
| T4 | CLAUDE.md Core Workflow vs SKILL.md | ⚠️ | 흐름도, 모드 판별, QA 호출 맵, 적응적 실행 설명이 SKILL.md와 일치. 단, 배포 구조 다이어그램에서 `~/.gemini/agents/` 경로가 누락됨. 또한 OPAL references 설명에서 "에이전트 목록 (3개)"가 갱신되지 않음 (실제 4개) |
| T5 | install-mac.sh 워커 에이전트 배포 | ✅ | Claude: `install_dir`이 `agents/claude/` 전체 복사 (task-flow-agent 포함). Cursor: 동일. Antigravity: 루프가 `agents/antigravity/*/` 자동 복사. Gemini CLI: Cursor 에이전트 → `~/.gemini/agents/` 복사 로직 추가. 에이전트 수 라벨 4개로 갱신 |
| T6 | 3개 플랫폼 에이전트 파일 핵심 내용 동일 | ✅ | 역할(3항목), 실행 프로세스(6단계), 가이드 매핑 테이블(5행), 반환 형식(5필드), 실행 규칙(5개), EXECUTE 추가 규칙(단순/복잡)이 3개 파일에서 동일. Cursor에 Gemini CLI 호환 필드(tools/max_turns/timeout_mins) 추가, Antigravity에 폴백 설명 추가 -- 플랫폼 차이만 존재 |
| T7 | 기존 QA/Planner/Test 에이전트 호환성 | ✅ | 3개 에이전트 파일 미변경(최종 수정일 기준 확인). 호출 인터페이스(입력: stage/task_path/artifact_path, 출력: QA-{단계}.md) 변경 없음. SKILL.md에서 호출 주체만 "오케스트레이터"로 명확화 |

### S1 ~ S7: 시나리오 워크스루

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| S1 | Full Task 정상 흐름 (Claude Code) | ✅ | SKILL.md STEP 2~5에 워커 디스패치 블록이 명확. 각 단계: 디스패치 → 워커 반환 → QA 호출(해당 시) → 사용자 보고 흐름이 완전히 기술됨 |
| S2 | Short Task 정상 흐름 (Claude Code) | ✅ | STEP 2(Short): PLAN-SHORT 워커 디스패치, STEP 3(Short): EXECUTE-SHORT 워커 디스패치가 명확. 체크리스트 갱신 규칙(PLAN.md 섹션 3)도 유지 |
| S3 | Full Task 복잡 모드 (Claude Code) | ✅ | TODO 워커 → 복잡도 판별 결과 반환 → 오케스트레이터가 Planner 호출 → Part C 추가 → 사용자 승인 → EXECUTE 워커 → 내부 서브 에이전트 배치 → Test → QA 흐름이 SKILL.md + execute-guide.md에 명확히 기술 |
| S4 | Full Task (Cursor) | ✅ | 중첩 불가 시 워커가 `status: blocked, blockers: ["중첩 서브 에이전트 불가"]` 반환 → 오케스트레이터가 배치별 서브 에이전트 직접 디스패치. SKILL.md STEP 5, execute-guide.md 복잡 모드 섹션, 에이전트 파일 복잡 모드 규칙에서 일관되게 기술 |
| S5 | Full Task (Antigravity) | ✅ | 크로스 플랫폼 폴백 규칙이 SKILL.md에 명확: 서브 에이전트 도구 사용 불가 → 에이전트 파일 Read → 직접 실행. Antigravity SKILL.md에도 폴백 패턴 명시 |
| S6 | 다중 태스크 동시 실행 | ✅ | SKILL.md "다중 태스크 실행" 섹션에 동시 실행 모델, 상태 추적, 통합 보고, 파일 충돌 경고 4개 하위 섹션이 모두 존재. 실행 모드 섹션에 다중 태스크 예시도 추가 |
| S7 | resume 시나리오 | ✅ | SKILL.md "워커 연속성" 섹션에 resume 가능/불가 분기, 플랫폼별 지원 테이블, resume 가능 단계 쌍 테이블이 명확. STEP 3(Full)에 "resume 가능 시: RESEARCH 워커를 이어서 PLAN 수행" 구체 기술 |

### 회귀 테스트

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| R-1 | 게이트 체크포인트 보고 형식 유지 | ✅ | SKILL.md "게이트 체크포인트 규칙" 섹션의 QA 있는/없는 단계 보고 형식이 변경 없음 |
| R-2 | QA 호출 맵 유지 | ✅ | TASK/TODO 생략, RESEARCH/PLAN/EXECUTE 호출 맵이 그대로 유지. 호출 주체만 "오케스트레이터"로 명확화 |
| R-3 | 복잡도 판별 기준 유지 | ✅ | SKILL.md + todo-guide.md의 복잡도 판별 기준(Step 수, 파일 수, 모듈 범위, 작업 유형, 외부 의존성) 변경 없음 |
| R-4 | 산출물 저장 구조 유지 | ✅ | SKILL.md의 Full/Short 산출물 디렉토리 구조 변경 없음 |
| R-5 | 체크리스트 갱신 규칙 유지 | ✅ | Full: TODO.md 체크박스, Short: PLAN.md 섹션 3 체크박스 갱신 규칙이 SKILL.md + execute-guide.md에서 유지 |
| R-6 | Short Task 에스컬레이션 규칙 유지 | ✅ | SKILL.md의 에스컬레이션 규칙(Step > 5 또는 변경 파일 > 3)이 변경 없음 |

### 코드 품질 (B-4)

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| Q-1 | 한국어 문서, 기술 용어 영어 병기 | ✅ | 모든 변경 파일이 규칙 준수 |
| Q-2 | kebab-case 파일/폴더 명명 | ✅ | `task-flow-agent` 정확 |
| Q-3 | 3개 플랫폼 에이전트 파일 포맷 | ✅ | Claude=디렉토리/AGENT.md, Cursor=플랫 파일, Antigravity=디렉토리/SKILL.md |
| Q-4 | 마크다운 문법 정확성 | ✅ | 헤딩 레벨, 코드 블록, 테이블 정상 |
| Q-5 | install-mac.sh 기존 패턴 일관성 | ✅ | Gemini CLI agents 배포가 기존 antigravity 루프 바로 뒤에 자연스럽게 추가. `mkdir -p` + `for` 루프 패턴이 기존 코드와 일관 |

### 보안 (B-5)

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| SEC-1 | 하드코딩된 토큰/시크릿 없음 | ✅ | 에이전트 파일에 민감 정보 없음 |
| SEC-2 | install-mac.sh 권한 에스컬레이션 없음 | ✅ | 추가된 로직은 사용자 홈 디렉토리 내에서만 작업 |

## 3. 지적 사항

### 🟡 Warning: SKILL.md 워커 에이전트 탐색 경로에 Gemini CLI 네이티브 경로 누락 (T1)

install-mac.sh가 Cursor 에이전트를 `~/.gemini/agents/task-flow-agent.md`에 배포하지만, SKILL.md의 task-flow-agent 탐색 경로 6개에 이 경로가 포함되지 않았다.

현재 탐색 경로의 6번 항목은 `~/.gemini/antigravity/skills/task-flow-agent/SKILL.md`로 Antigravity 폴백 경로만 존재한다. Gemini CLI에서 네이티브 에이전트로 인식되는 `~/.gemini/agents/task-flow-agent.md` 경로를 추가해야 한다.

**수정 제안**: SKILL.md의 task-flow-agent 에이전트 탐색 경로에 `~/.gemini/agents/task-flow-agent.md` 항목을 추가 (Antigravity 폴백 경로 앞에 삽입하여 Gemini CLI 네이티브 경로를 우선).

### 🟡 Warning: CLAUDE.md 배포 구조 다이어그램에 `~/.gemini/agents/` 누락 (T4)

install-mac.sh에서 `~/.gemini/agents/`에 에이전트를 배포하는 로직이 추가되었으나, CLAUDE.md의 배포 구조(사용자 홈) 다이어그램에 이 경로가 반영되지 않았다. 현재 `~/.gemini/` 하위에는 `settings.json`과 `antigravity/`만 표시되어 있다.

**수정 제안**: CLAUDE.md 배포 구조 다이어그램의 `~/.gemini/` 섹션에 `agents/` 디렉토리 항목을 추가.

### 🔵 Info: CLAUDE.md OPAL references 에이전트 수 미갱신 (T4)

CLAUDE.md 102줄의 배포 구조에서 `agents.md 에이전트 목록 (3개)`로 표기되어 있으나, agents.md에는 task-flow-agent가 추가되어 실제 4개이다. OPAL references 설명의 에이전트 수를 4개로 갱신하면 정합성이 향상된다.

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md | R1(오케스트레이터-워커 아키텍처) → SKILL.md 신규 섹션으로 구현 | ✅ |
| TASK.md | R2(단계별 워커 위임 범위) → SKILL.md STEP 2~5(Full), STEP 2~3(Short)에 워커 디스패치 블록 | ✅ |
| TASK.md | R3(워커 연속성) → SKILL.md resume 섹션 + 플랫폼별 지원 테이블 | ✅ |
| TASK.md | R4(워커 프롬프트 설계) → SKILL.md 워커 디스패치 규칙 + 프롬프트 템플릿 | ✅ |
| TASK.md | R5(다중 태스크 동시 실행) → SKILL.md 다중 태스크 실행 신규 섹션 | ✅ |
| TASK.md | R6(기존 호환성 유지) → QA/Planner/Test 미변경, 호출 구조 유지, 체크리스트 규칙 유지 | ✅ |
| TASK.md | R7(파일 변경 범위) → 실제 변경 파일이 R7 목록과 일치 (+ agents.md 추가) | ✅ |
| TASK.md | 제약 "워커는 프롬프트 템플릿 기반 동적 서브 에이전트 -- 새로운 AGENT.md 파일 생성 불필요" | ⚠️ |
| RESEARCH.md | 설계 결정 3.3(QA 호출 주체=오케스트레이터) → SKILL.md + 가이드 4개에 반영 | ✅ |
| RESEARCH.md | 설계 결정 3.4(워커 연속성 resume) → SKILL.md resume 섹션에 반영 | ✅ |
| RESEARCH.md | 설계 결정 5.6(워커 에이전트 파일 정의 신규 제안) → 3개 플랫폼 에이전트 파일 생성 | ✅ |
| PLAN.md | N1~N3(신규 파일) → 3개 에이전트 파일 생성 확인 | ✅ |
| PLAN.md | M1~M7(수정 파일) → 7개 파일 수정 + V5(agents.md) 수정 확인 | ✅ |
| PLAN.md | 3.4절 워커 프롬프트 템플릿 → SKILL.md에 동일하게 반영 | ✅ |
| PLAN.md | 3.10절 install-mac.sh 변경 → Gemini CLI agents 배포 + 에이전트 수 라벨 갱신 확인 | ✅ |

**TASK.md 제약 사항 교차 참조 주의**: TASK.md 제약에 "워커는 프롬프트 템플릿 기반 동적 서브 에이전트 -- 새로운 AGENT.md 파일 생성 불필요"라고 명시되어 있으나, RESEARCH.md 5.6절에서 "정식 에이전트 파일로 정의하면 Cursor/Gemini에서 네이티브 서브 에이전트로 인식"이라는 근거로 에이전트 파일 생성을 제안하였고, 이 제안이 PLAN.md에 반영되어 사용자의 승인을 받았다. 따라서 TASK.md 제약과의 불일치는 분석 과정에서 합리적으로 변경된 것으로 판단한다.

## 5. 판정

**⚠️ Needs Revision**

🟡 Warning 2건:
1. SKILL.md 워커 에이전트 탐색 경로에 Gemini CLI 네이티브 경로(`~/.gemini/agents/task-flow-agent.md`)가 누락되어, install-mac.sh 배포 경로와 불일치
2. CLAUDE.md 배포 구조 다이어그램에 `~/.gemini/agents/` 디렉토리가 반영되지 않아, 실제 배포 로직과 문서가 불일치

두 항목 모두 Gemini CLI 플랫폼에서의 에이전트 탐색/배포 정합성에 관한 것으로, 수정 범위가 작고 명확하다. 수정 후 Pass 전환이 가능하다.
