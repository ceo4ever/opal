# QA: PLAN -- task-flow 워커 에이전트 실행 모델

> 검토일: 2026-03-14 | 판정: ✅ Pass

## 1. 요약

task-flow 파이프라인을 오케스트레이터-워커 아키텍처로 전환하는 구현 계획이다. 알투(오케스트레이터)는 TASK 작성, 게이트 체크포인트 중계, QA/Planner/Test 호출만 담당하고, RESEARCH/PLAN/TODO/EXECUTE는 워커 에이전트(`task-flow-agent`)가 격리된 컨텍스트에서 수행한다.

3개 플랫폼(Claude Code, Cursor, Antigravity) + Gemini CLI에 대한 워커 에이전트 파일을 신규 생성(N1~N3)하고, SKILL.md를 핵심 허브로 전면 재구성(M1)하며, references 가이드에 워커 프리앰블을 추가(M3~M5)하는 구조다. execute-guide.md(M2)는 실행 주체를 "메인 에이전트"에서 "워커"로 변경하고, 복잡 모드의 Cursor 중첩 불가 폴백을 명시한다.

핵심 설계 결정: QA/Planner/Test 모두 오케스트레이터가 호출, resume은 가능하면 활용하되 산출물 기반 복원을 기본으로, 다중 태스크 동시 실행 지원.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| P-1 | 즉시 구현 가능성 | ✅ | 신규 파일 3개의 YAML frontmatter + 본문 구조가 명세됨. SKILL.md 변경 후 구조가 섹션 단위로 기술됨. 워커 프롬프트 템플릿, 반환 형식, 단계별 매핑 테이블 제공. execute-guide.md 변경 포인트 6개가 구체적으로 나열됨 |
| P-2 | 의존성 순서 정합 | ✅ | N1~N3(워커 에이전트 파일) -> M1(SKILL.md) -> M2(execute-guide) -> M3~M5(가이드 프리앰블) -> M6(CLAUDE.md) -> M7(install-mac.sh) -> V1~V5(검증). 워커 정의가 선행되어야 SKILL.md에서 참조 경로를 정확히 기술할 수 있다는 근거가 명시됨 |
| P-3 | RESEARCH 반영 | ✅ | RESEARCH의 6개 제약/리스크(Cursor 중첩 불가, resume 미지원 플랫폼, 다중 태스크 파일 충돌, Gemini max_turns, Antigravity 폴백, 워커 오버헤드)가 모두 PLAN 섹션 6에 대응 방안과 함께 반영됨. RESEARCH의 5개 설계 결정(단계별 워커, TASK 직접, QA 오케스트레이터 호출, resume 전략, 프롬프트 경로 전달)이 PLAN 3.1~3.11에 구체화됨 |
| P-4 | 파일 목록 일치 | ⚠️ | RESEARCH에서 식별한 수정 파일 10개(SKILL.md, execute-guide, research-guide, plan-guide, todo-guide, CLAUDE.md + 신규 3개 에이전트 파일)가 PLAN의 N1~N3, M1~M7에 모두 포함됨. 다만 PLAN에 추가된 M7(`install-mac.sh`)은 RESEARCH에서 명시적으로 언급되지 않았으나, Gemini CLI agents 배포(RESEARCH 5.3, 5.6)에서 암시됨. 또한 V5(`opal/core/references/agents.md`)는 RESEARCH에서 언급되지 않은 영향 파일로 PLAN에서 추가 식별됨 |
| P-5 | 핵심 설계 구체성 | ⚠️ | 워커 에이전트 파일(N1)의 YAML frontmatter와 본문 구조가 상세히 명세됨. 워커 프롬프트 템플릿(3.4)과 반환 형식이 구체적. 그러나 SKILL.md(M1) 변경은 "변경 후 구조" 수준의 목차 명세이며, 각 섹션의 실제 마크다운 텍스트까지는 기술되지 않음. 이 태스크가 마크다운 문서 작성이라는 점을 고려하면, 핵심 섹션(오케스트레이터-워커 실행 모델)의 실제 문구까지 있으면 구현 시 해석 여지가 줄어듦 |
| P-6 | 테스트 전략 커버리지 | ✅ | 문서 정합성 검증 7개(T1~T7) + 시나리오 워크스루 7개(S1~S7)로 구성. TASK의 R1~R7 요구사항이 시나리오에 매핑됨: R1(S1~S5), R2(S1~S3), R3(S7), R4(T2), R5(S6), R6(T7, S3~S5). 코드가 아닌 마크다운 문서 수정 태스크에 적합한 검증 방식 |

## 3. 지적 사항

### 3-1. TASK 제약 조건과의 괴리 (AGENT.md 파일 생성)

- 심각도: 🟡 **Warning**

TASK.md 제약 조건(82줄)에 "워커는 프롬프트 템플릿 기반 동적 서브 에이전트 -- 새로운 AGENT.md 파일 생성 불필요"라고 명시되어 있으나, PLAN은 정식 에이전트 파일 3개(N1~N3)를 신규 생성하는 방향으로 설계했다.

이는 RESEARCH 5.6에서 "Cursor/Gemini에서 네이티브 서브 에이전트로 인식되려면 정식 에이전트 파일이 필요하다"는 분석 결과에 기반한 의도적 설계 변경이다. 기술적으로 타당한 결정이지만, TASK.md의 제약 조건을 명시적으로 오버라이드하는 것이므로 사용자 확인이 필요하다.

### 3-2. SKILL.md 변경 상세도

- 심각도: 🔵 **Info**

PLAN 3.2에서 SKILL.md의 "변경 후 구조"가 섹션 목차 + 각 섹션별 변경 요지로 기술되어 있다. 워커 프롬프트 템플릿(3.4), 에이전트 파일(3.3), execute-guide 변경(3.7) 등 핵심 부분은 충분히 구체적이나, SKILL.md의 실제 STEP 2~5 변경 문구("워커 디스패치 블록")는 구조만 제시되어 있다. 구현 시 작성자가 일부 해석해야 할 여지가 있으나, references 가이드와 워커 프롬프트 템플릿이 구체적이므로 실질적 구현에는 충분하다.

### 3-3. Gemini CLI 에이전트 배포: Cursor 파일 재활용

- 심각도: 🔵 **Info**

PLAN 3.3에서 Gemini CLI용 에이전트를 Cursor 파일에서 복사하기로 결정했다. `tools`, `max_turns`, `timeout_mins` 등 Gemini 전용 필드를 Cursor 파일에 포함하고 Cursor가 무시하도록 하는 전략인데, RESEARCH 5.7의 워커 에이전트 스케치에서 이미 이 필드들을 포함한 통합 YAML을 제안하고 있어 일관성이 있다. 다만 Cursor 파일(`agents/cursor/task-flow-agent.md`)의 YAML에 Gemini 전용 필드가 추가된다는 점은 구현 시 명확히 주석 처리하면 좋다.

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md | R1(오케스트레이터-워커 아키텍처): PLAN 3.1~3.6에서 역할 분리, 디스패치 규칙, 다중 태스크 모두 반영 | ✅ |
| TASK.md | R2(단계별 워커 위임): PLAN 3.2의 STEP별 워커 디스패치 블록에서 TASK 직접 + RESEARCH~EXECUTE 워커 위임 반영 | ✅ |
| TASK.md | R3(워커 연속성): PLAN 3.5에서 resume 설계, 단계 쌍별 resume 가치 분석, 플랫폼별 지원 여부 반영 | ✅ |
| TASK.md | R4(워커 프롬프트): PLAN 3.4에서 프롬프트 템플릿, 단계별 매핑 테이블, 반환 형식 모두 정의 | ✅ |
| TASK.md | R5(다중 태스크): PLAN 3.2의 "다중 태스크 실행" 신규 섹션에서 동시 실행 모델, 상태 추적, 파일 충돌 경고 반영 | ✅ |
| TASK.md | R6(호환성 유지): PLAN 3.11에서 QA/Planner/Test 호출 주체 결정, 체크리스트/게이트 규칙 유지 명시 | ✅ |
| TASK.md | R7(파일 변경 범위): PLAN N1~N3, M1~M7에서 TASK의 R7.1~R7.6 모두 커버. R7.5(CLAUDE.md)=M6, R7.6(3개 플랫폼)=N1~N3 | ✅ |
| TASK.md | 제약 조건 "새로운 AGENT.md 파일 생성 불필요" vs PLAN의 N1~N3 신규 생성 | ⚠️ |
| RESEARCH.md | 설계 결정 3.1(단계별 워커) -> PLAN 3.1 아키텍처 개요에 반영 | ✅ |
| RESEARCH.md | 설계 결정 3.3(QA 오케스트레이터 호출) -> PLAN 3.11에서 QA/Planner/Test 모두 오케스트레이터 호출로 확장 | ✅ |
| RESEARCH.md | 설계 결정 5.6(정식 에이전트 파일 제안) -> PLAN N1~N3에서 구체화 | ✅ |
| RESEARCH.md | 변경 필요 파일 목록(섹션 1) -> PLAN 섹션 1 구현 범위에 모두 포함 + install-mac.sh 추가 식별 | ✅ |
| RESEARCH.md | 리스크 6개(섹션 6) -> PLAN 섹션 6에 7개로 확장 반영 (다중 태스크 파일 충돌 + resume 실패 추가) | ✅ |

## 5. 판정

**✅ Pass**

PLAN은 TASK.md의 7개 요구사항 그룹(R1~R7)과 RESEARCH.md의 설계 결정을 빠짐없이 반영하고 있으며, 11개 구현 순서, 핵심 설계 11개 섹션, 테스트 전략 14개 항목으로 충분한 구체성을 갖추고 있다. TASK 제약 조건("AGENT.md 생성 불필요")과의 괴리는 RESEARCH 단계에서 기술적 근거를 바탕으로 의도적으로 변경된 것이므로, 사용자가 이 점을 인지한 상태에서 다음 단계로 진행할 수 있다.
