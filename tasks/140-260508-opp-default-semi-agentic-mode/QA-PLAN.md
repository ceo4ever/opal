# QA: PLAN — `--semi-agentic` 모드 도입 + 전체 pilot 기본 모드 변경

> 검토일: 2026-05-09 | 판정: **Pass**

## 1. 요약

PLAN.md는 OPAL 하네스에 `semi-agentic`이라는 세 번째 모드를 신설하고 전체 pilot 7종의 기본 모드로 채택하기 위한 상세한 구현 설계서이다. 설계는 TASK.md의 8개 요구사항(F-1~F-8)과 5개 미확정 사항(U-1~U-5)을 모두 반영하고 있으며, 각 단계별 의존관계, 완료 기준, 테스트 방법이 명시되어 있다. 신규 하네스 파일(opal-harness-semi-agentic.md), 공통 하네스 3종 갱신, state-tool Python 코드 확장, pilot 7종 SKILL.md 일괄 갱신 등 18개의 변경사항이 9개 Step으로 분해되어 있으며, 모든 [MUST] 토큰이 원문 인용 형식을 따르고 있다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| GP-1 | 즉시 실행 가능성 | **Pass** | 9개 Step이 순차/병렬 관계와 agent 필드(8개는 opal-task-agent, 1개는 PM 직접)를 모두 명시. 각 Step의 완료 기준, 테스트 방법, 의존 관계가 명확함. |
| GP-2 | 의존성 순서 | **Pass** | §3 실행 체크리스트 위상 순서가 정확 — Step 1(신규 하네스) → Step 2~5(병렬, SSOT 참조) → Step 6(7파일 일괄) → Step 7(메모리) → Step 8~9(검증/PM검토). 순환 의존 없음. |
| GP-3 | TASK 반영도 | **Pass** | TASK.md의 모든 요구사항 F-1~F-8이 §3 Step에 매핑됨(F-1→Step 1, F-2→Step 6, F-3→Step 5, F-4→Step 4 및 §2 N-1, F-5→Step 2~4, F-6→Step 3, F-7→Step 7, F-8→Step 1~7 전체). 미확정 사항 U-1~U-5도 모두 결정(D-DEC-1~D-DEC-7)하여 §2에 명시. |
| GP-4 | 파일 목록 완전성 | **Pass** | 신규(N-1, N-2) 2개 + 수정(M-1~M-19) 18개 = 총 20개 파일이 명시. 각 파일의 변경 내용이 구체적으로 기술되고, 영역별로 누락 없음(하네스 3종, 부트스트랩 4종, op-task, state-tool 2종, pilot 7종, 메모리 2종, PM 검토 3종). |
| GP-5 | 설계 구체성 | **Pass** | 신규 하네스(N-1) 9개 섹션 구조 완전 명시 / 각 파일(M-1~M-19)의 변경 내용이 현재 라인/필드명 기준으로 상세 기술 / Python 코드 변경(M-16)은 상수명, 조건식, 에러 코드 포함 구체적 기술 / 각 Step 완료 기준이 테스트 가능한 형태(예: "grep -c semi-agentic 결과 ≥5"). |
| GP-6 | 체크리스트 커버리지 | **Pass** | §3 실행 체크리스트 9개 Step에서 §4 QA 체크리스트로 F1-1~F1-3(하네스), F2-1~F2-5(모드 분기), F3-1~F3-5(pilot 7종), F4-1~F4-3(state-tool), Q-1~Q-6(공통)이 명시되어 있어 Step별 검증 항목이 명확. |
| **인용 규칙 준수** | **Pass** | 모든 [MUST] 토큰이 원문 인용 형식(e.g., `[MUST] 'docs/CONVENTIONS.md' §구현 규칙 — Guards: "..."`)을 따름. TASK.md 요구사항/결정 인용이 `(→ TASK.md L{줄번호})`/`(D-DEC-N)` 형식으로 명시. 부록 "참조 인용 일람"에서 모든 [MUST] 항목과 코드/줄번호 인용이 일괄 정리. citation-rules.md §2 포맷 준수. |
| **하네스 Guards 준수** | **Pass** | PLAN.md가 코드/설정 파일 작성을 포함하지 않음(산출물 문서만, Step 8은 검증만) / CLOSE 진입 게이트 규칙이 새 모드(semi-agentic)에도 명시적으로 유지(§2 N-1 §6 / M-3 M-16 변경사항 / 부록 [MUST] 인용) / §3 실행 체크리스트의 모든 Step이 agent 필드를 가지며 8개는 opal-task-agent, 1개는 PM 직접으로 명시. |
| **변경이력 규칙** | **Pass** | §3 Step 1~7의 완료 기준에 변경이력 표 행 추가가 명시(e.g., Step 1 "변경이력 표 v1.0 행 포함", Step 2 "각 파일에 변경이력 행 추가(일시 KST + 태스크 번호 140)"). 각 M-N 파일 변경사항에 "변경이력 행: `| v{X.Y} | YYYY-MM-DD HH:mm | ... (140) |`" 형식으로 기재. 프로젝트 컨벤션 `docs/CONVENTIONS.md` §변경이력 작성 의무 준수(KST + semver + 괄호 태스크 번호). |
| **배포 경계 준수** | **Pass** | PLAN.md §3 Step 1~6의 모든 변경 대상 파일이 프로젝트 소스(`opal/core/`, `opal/skills/`, `opal/tools/`)임. `~/.opal/` 직접 편집 없음(배포 후 파일만 검증). Step 8에서 install 재배포 절차 명시. `.opal/MEMORY.md` 메모리 파일도 메모리 영역(프로젝트 의존 파일) 내 신규 파일로 명시적으로 생성(N-2). `.opal/AGENT.md` 갱신도 "도메인 지식" 표 및 "확정 기준" 표 행 추가(M-18) — PM 직접 관리 파일로 합리적. |
| **state-tool SSOT 준수** | **Pass** | PLAN.md에서 STATE.md 마크다운 직접 편집을 지시하는 곳 없음. M-16 (M-16 상수 신설 / 에러 코드 추가 / 조건식 확장) 모두 state-tool run.sh 내부 로직(Python 코드)으로만 명시. AGENTIC-LOG.md 생성(D-DEC-7)도 "pilot SKILL.md의 EXECUTE 진입 절차에 명시(state-tool 외부) — state-tool은 STATE.md/state.json만 관리하므로 AGENTIC-LOG는 PM 책임 영역"으로 명확히 구분. |
| **Step별 완성도** | **Pass** | 모든 Step(1~9)이 (입력 / 작업 내용 / 완료 기준 / 테스트 / 의존 / agent 필드)를 갖춤. 특히 Step 1~7의 완료 기준은 파일 존재, 필드값 변경, 변경이력 행, 매칭 카운트 등 검증 가능한 형태로 명시. Step 8은 6단계 검증 절차 + 재 로드, Step 9는 PM 영향 검토. |
| **모드 경계 명시** | **Pass** | TASK.md 표 L24-31 PLAN에서 결정사항으로 반영(§1 표 "배경 분석" 복제 + D-DEC-1~D-DEC-2에서 각 pilot별 정의). N-1 §3 모드 경계 표에 7개 pilot 모두 명시(opp/opd/opds: PLAN 사용자 확인 / opdw: WIREFRAME / opwt: PLAN 간략 / oppd: Phase 2 WBS / opsdd: Phase 3 DESIGN). 각 pilot SKILL.md 갱신 시 이 표 인용 지시(M-9~M-15 "D-DEC-1"/"D-DEC-2" 명시). |
| **롤백 전략** | **Pass** | §6에서 R-1(코어 변경 위험) 대응의 롤백 전략이 명시 — 발동 조건(6단계 검증 실패), 절차(git revert), 재검증, 재시도 규칙 포함. R-2~R-9의 리스크 9개도 각각 영향+대응 기술. |
| **semi-agentic vs interactive 모드 분리** | **Pass** | TASK.md "배경" 절 L14-18 "두 모드의 자율 시작점 비교" 표가 PLAN.md §1 "배경 조사" 표로 복제되어 명확히 분리(interactive: 모든 단계 사용자 / semi-agentic: PLAN까지 사용자 / agentic: 모두 자율). 부록 [MUST] 인용 마지막 항목이 평문 설명 — "본 PLAN은 EXECUTE 단계에서 워커에게 디스패치된다. PM은 §3 ... Step별 `agent` 필드(... Step 9는 PM 직접)에 따라 디스패치한다." |

## 3. 지적 사항

지적 사항 없음. 모든 검증 항목이 Pass 판정.

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md (입력) | F-1~F-8 요구사항 모두 PLAN §3 Step에 매핑 확인 | **Pass** — F-1→Step 1, F-2→Step 6, F-3→Step 5, F-4→Step 4, F-5→Step 2/3/4, F-6→Step 3, F-7→Step 7, F-8→Step 1~7 |
| TASK.md | U-1~U-5 미확정 사항 모두 결정사항(D-DEC-1~D-DEC-7)으로 반영 확인 | **Pass** — U-1(oppd Phase 2) D-DEC-1, U-2(opsdd DESIGN) D-DEC-2, U-3(파일 분기) D-DEC-3, U-4(호환성) D-DEC-4, U-5(state-tool 행 식별) D-DEC-5 |
| docs/CONVENTIONS.md | [MUST] 인용 규칙(§Citation Rules)과 배포 경계(§배포 경계) 준수 | **Pass** — 부록에 10개 [MUST] 항목 원문 인용 + 모든 주장에 근거(경로:줄번호 또는 docs/문서명 §섹션) |
| .opal/AGENT.md | 금지사항(구현 금지/STATE 직접 편집/하네스 우회) 준수 + 프로젝트 컨벤션 준수 | **Pass** — Step 8에서 install 검증만(구현 X), M-16은 state-tool 코드만(STATE.md 마크다운 X), CLOSE 게이트 명시(하네스 우회 X), 모든 Step에 변경이력 행(컨벤션 준수) |

## 5. 판정

**Pass**

PLAN.md는 TASK.md의 모든 기능 요구사항(F-1~F-8) 및 미확정 사항(U-1~U-5)을 명확히 설계에 반영하고 있으며, 9개 Step의 순차/병렬 관계와 완료 기준이 검증 가능한 형태로 기술되어 있다. 모든 [MUST] 토큰이 citation-rules.md 원문 인용 형식을 따르며, 하네스 Guards, 배포 경계, state-tool SSOT 등 프로젝트 컨벤션을 모두 준수한다. EXECUTE 단계 진입이 가능한 수준의 완성도를 갖추고 있다.

---

## 체크리스트 갱신 요약

TASK.md 요구사항 체크박스 갱신 결과:

| 요구사항 | 상태 | 근거 |
|---------|------|------|
| F-1 (신규 하네스) | `[x]` | PLAN §2 N-1에서 9개 섹션 구조 완전 설계 |
| F-2 (pilot 7종 모드 분기) | `[x]` | PLAN §2 M-9~M-15에서 각 pilot 모드 분기 규칙 설계 |
| F-3 (state-tool --mode semi-agentic) | `[x]` | PLAN §2 M-16에서 Python 코드 변경 명세 완전 |
| F-4 (AGENTIC-LOG.md EXECUTE 시점) | `[x]` | PLAN §2 D-DEC-7에서 생성 시점 명시 + M-3에 반영 |
| F-5 (부트스트랩 문서 3-way 갱신) | `[x]` | PLAN §2 M-1/M-4/M-5/M-6/M-7/M-8에서 설계 완전 |
| F-6 (state-template.md 모드 필드) | `[x]` | PLAN §2 M-4에서 choices + 기본값 명시 |
| F-7 (메모리/확정 기준) | `[x]` | PLAN §2 N-2/M-18/M-19에서 구조 설계 |
| F-8 (변경이력 모든 파일) | `[x]` | PLAN §3 Step 1~7 모두 변경이력 행 명시 |

---

**QA 검증 완료: 2026-05-09 | 워커: op-task-qa | 모드: 자동 QA**
