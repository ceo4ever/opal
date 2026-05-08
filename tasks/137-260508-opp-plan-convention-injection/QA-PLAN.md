# QA: PLAN — PLAN 워커 컨벤션 [MUST] 인용 강제 — 사전 주입 강화

> 검토일: 2026-05-08 | 판정: **Pass**

---

## 1. 요약

PLAN.md는 태스크 137 (컨벤션 [MUST] 인용 강제 사전 주입)의 설계 단계 산출물로, 4개 잠재 적용 지점에 대한 정밀 분석을 수행하여 채택/부분 채택/비채택 결정을 근거와 함께 제시한다. 변경 5개 파일(dispatch-process.md, op-task-plan SKILL+plan-guide, op-dev-plan SKILL, opal-plan-agent AGENT), 6단계 실행 체크리스트, 하위 호환성 명시, 136과의 책임 분리 및 시너지 설계를 포함한다. TASK.md R-1~R-6 요구사항이 모두 구현 계획 및 QA 체크리스트에 명확히 매핑되어 있다.

---

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| GP-1 | 즉시 실행 가능성 | **Pass** | 5개 파일의 변경 위치(줄번호), 변경 내용(단어/포맷), 완료 기준이 모두 구체적 명시. SSOT 1곳(D-1) 변경으로 4개 오케스트레이터 자동 전파되는 참조 구조 명확. |
| GP-2 | 의존성 순서 | **Pass** | Step 1~5는 5개 파일 모두 독립(상호 의존 없음) → Phase 1 병렬 실행 가능. Step 6(통합 검증)은 Phase 2로 순차. 의존 관계 표 및 비고 명시. |
| GP-3 | TASK 반영 | **Pass** | R-1: PM 디스패치 측(D-1 Step 3) / R-2: PLAN 에이전트 측(D-2 행동 규칙) / R-3: PLAN.md 산출물 검증(D-3/D-4 품질 체크리스트) / R-4: 인용 규약 결정(citation-rules.md 비채택 근거) / R-5: 하위 호환 명시 / R-6: 적용 지점 결정 근거 → 모두 §2.1~§2.5에 1:1 매핑. §4 QA 체크리스트에서 R-1~R-6 명시적 검증 항목. |
| GP-4 | 파일 목록 완전성 | **Pass** | PLAN §1.2 관련 파일 테이블에서 변경 필요 파일(M-1~M-5: 5개) + 변경 없음 파일(citation-rules, opal-pilot-*, docs/CONVENTIONS) 명확 구분. 신규 생성 0개, 삭제 0개, 수정 5개. 각 파일별 변경 이유(근거 줄번호) 기재. |
| GP-5 | 설계 구체성 | **Pass** | §2.3 파일 변경 계획에서 M-1~M-5 각각의 정확한 변경 위치(파일경로, 섹션명, 기존 텍스트), 추가/변경할 텍스트(포맷 포함), 변경 근거 명시. §2.5 핵심 설계 M-1~M-5에서 변경 전·후 비교, citation-rules 포맷 준수 확인, 의도 설명. |
| GP-6 | 체크리스트 커버리지 | **Pass** | §3 실행 체크리스트: 총 6개 Step으로 TASK.md 요구사항 R-1~R-6을 완전 분해. Step 1: R-1(PM 측). Step 2-4: R-3(QA 검증 3곳). Step 5: R-2(에이전트 측). Step 6: R-5(하위 호환) + R-4(비채택 결정). §4 QA 체크리스트(기능+일관성+문서 품질) 10+3+3 = 16개 항목. |
| C-1 | TASK R-1 검증 (PM 디스패치 강제) | **Pass** | §2.1 #1 결정: "채택 (SSOT 1순위)". M-1 변경(dispatch-process.md §Step 3): (a) 인용 의무 규칙 표에 컨벤션 명시, (b) 예시 섹션에 컨벤션 인용 예시, (c) 워커 컨텍스트 주입 템플릿에 "핵심 제약" 필드 컨벤션 항목, (d) 하위 호환 명시. §4 R-1 항목 3개(표/예시/템플릿+영향 범위 자동 전파) 모두 검증. |
| C-2 | TASK R-2 검증 (PLAN 에이전트 강제) | **Pass** | §2.1 #2 결정: "부분 채택 — 보조 강화". M-5 변경(opal-plan-agent AGENT.md §행동 규칙): "[MUST] 자체 로드한 `docs/CONVENTIONS.md`... PLAN.md에 [MUST] 포맷으로 인용" 1행 추가. SKILL.md citation-rules trigger가 이미 인용을 강제하므로 중복 안전망으로 해석. §4 R-2 항목(AGENT.md 행동 규칙) 검증. |
| C-3 | TASK R-3 검증 (PLAN.md 산출물 검증) | **Pass** | §2.1 #3 결정: "채택 (QA 자동 검출 1순위)". M-2/M-3/M-4 변경: op-task-plan(SKILL.md+plan-guide.md 2곳), op-dev-plan(SKILL.md 1곳) 품질 체크리스트에 컨벤션 [MUST] 인용 검증 항목 추가. 3곳 동일 텍스트(양쪽 동기화 필요). §4 R-3 항목 3개(op-task-plan+plan-guide, op-dev-plan) 모두 명시. |
| C-4 | TASK R-4 검증 (citation-rules §2.5 결정) | **Pass** | §2.1 #4 결정: "비채택". 근거: (a) §2.5 헤더가 "개발 트랙" 한정이며 컨벤션 [MUST]는 비개발 트랙에서도 강제(트랙 매트릭스 충돌) (b) 기존 6종 토큰이 컨벤션 [MUST] 90% 커버 (c) §2.4 일반 포맷으로 충분. 비채택 사유를 §리스크 R-T3에 명시(형식 불일치 리스크 대응). §4 R-4 항목(citation-rules 변경 없음 + 비채택 사유) 검증. |
| C-5 | TASK R-5 검증 (하위 호환 명문화) | **Pass** | 5개 변경 지점 모두 "`docs/CONVENTIONS.md` 부재 시 자동 스킵" 명시. M-1(D-1 §Step 3): "`docs/CONVENTIONS.md` 부재 시... Step 2 문서 선별에서 제외됨". M-2/M-3/M-4(SKILL.md 품질 체크리스트): "(CONVENTIONS.md 부재 프로젝트는 자동 스킵)". M-5(AGENT.md): "(CONVENTIONS.md 부재 시 자동 스킵 — §자체 로드 문서 룰 상속)". §1.4 영향 범위에서 "변경 없이 그대로 작동하는 파일" / "영향 받지 않는 흐름" 구분. §리스크 R-T1에서 시뮬레이션 계획 명시. §4 R-5 항목(5개 지점 모두 명시) 검증. |
| C-6 | TASK R-6 검증 (적용 지점 결정 근거) | **Pass** | §2.1 "잠재 적용 지점 4개 채택 결정 (R-6)" 표: #1~#4 각각의 결정(채택/부분 채택/비채택) + 근거 명시. #1: "채택(SSOT 1순위)" + "opal-pilot-* SKILL.md는 이를 참조하므로..." #2: "부분 채택 — 보조 강화" + "SKILL.md citation-rules trigger가 이미..." #3: "채택(QA 자동 검출)" + "op-task-qa / op-dev-qa가 SKILL.md 품질..." #4: "비채택" + "(a) §2.5 헤더가...(b) 6종 토큰...(c) §2.4로 충분". 최소 변경 정합성 설명. §4 R-6 항목(결정 근거 표) 검증. |
| C-7 | 136(사후 검증)과의 책임 분리 | **Pass** | §2.2 "136(사후 검증 B)과 책임 분리 + 시너지" 표: 검사 시점(PLAN Gate vs EXECUTE Gate) / 검사 대상(PLAN.md vs changed_files) / 메커니즘(워커 인용 의무 vs opal-convention-checker) 모두 분리 명시. 시너지 설명: "A 통과 → PLAN.md 컨벤션 박힘 → EXECUTE 워커 준수 코드 생산 → B는 위반 0건 정상 / A 누락 시 B가 안전망". 충돌 검증: "136 산출물 pm-review-gate.md §13 트리거는 EXECUTE 단계만 / 본 태스크 변경은 PLAN 단계 이전 → 충돌 없음". |
| C-8 | citation-rules.md §2.4 [MUST] 포맷 준수 | **Pass** | M-1: "카탈로그 항목 자체를 [MUST] 포맷으로 박을 필요는 없음 — 표 자체가 SSOT" (표 정의로 충분). M-2/M-3/M-4: "[MUST] 'docs/CONVENTIONS.md' §N: <원문>" 포맷 명시. M-5: "[MUST] 자체 로드한..." 포맷 재해석 여지 강제 규칙으로 기재. 포맷 규정 위반 없음. |
| C-9 | SSOT 참조 구조 일관성 | **Pass** | opal-pilot-{project,dev,dev-short,dev-wireframe} SKILL.md에서 "핵심 제약" 필드가 D-1(dispatch-process.md)을 참조 → D-1 SSOT 1곳 수정으로 4개 오케스트레이터 자동 전파. PLAN §2.1 #1 ("SSOT 1순위" 이유) + §2.5 M-1 ("의도" 섹션 "참조 구조 활용") 명시. 추가 수정 불필요(opal-pilot-* SKILL.md 변경 없음). |
| C-10 | 136 §13 (pm-review-gate.md)과 충돌 재검증 | **Pass** | §1.3 D-11 (pm-review-gate.md §13): "§13 '컨벤션 자동 진단'은 **EXECUTE 단계 PM Gate**에서 워커 반환 `changed_files`를 대상으로... PLAN.md 자체는 검사 대상이 아님" 명시. → "본 태스크(A)는 PLAN.md 작성 시점 사전 차단 / 136(B)는 EXECUTE 결과 사후 검출. 검사 시점·대상·메커니즘 모두 분리 → 충돌하지 않으며 이중 안전망 시너지 형성". §리스크 R-T2 대응. |
| D-1 | 참조 문서 테이블 완전성 | **Pass** | §1.1 참조 문서 테이블 D-1~D-13 (13개 항목). TASK.md D-1~D-10 보존 + D-11(pm-review-gate.md 사후 검증), D-12(op-task-plan plan-guide.md), D-13(opal-pilot-project SKILL.md PLAN 디스패치) 추가. 각 항목의 유형(설계)/경로/참조 이유 명시. citation-rules.md §3.1 포맷(유형/경로(URL)/참조 이유) 준수. |
| D-2 | 핵심 설계 인라인 인용 | **Pass** | §2.5 M-1~M-5 각 섹션에서 변경 근거 인용 기재. 예: M-1 "(→ D-1 §Step 3)", M-5 "(→ D-2 §행동 규칙)". M-1에서 citation-rules.md 포맷 설명 "표 정의로 충분". M-2~M-4에서 "[MUST] 'docs/CONVENTIONS.md' §N: <원문>" 포맷 예시 및 설명. |
| D-3 | 재해석 여지 규칙 적용 | **Pass** | M-1·M-5는 신설 의무(강제 규칙) → [MUST] 포맷 또는 표 정의로 기재. M-1은 SSOT dispatch-process 표 형태(원문 인용 필수 카탈로그). M-5는 AGENT.md 행동 규칙으로 [MUST] 포맷 박음. citation-rules.md §2.4 "재해석 여지가 있는 금지사항·강제 규칙은 [MUST] 접두사 + 원문 인용" 준수. |
| D-4 | 문서 품질 (언어/네이밍) | **Pass** | 한국어 본문 + 영어 코드/경로/필드명 규칙 준수. 예: "§Step 3 인용 의무 카탈로그", "`opal/core/references/pm/dispatch-process.md`", "`[MUST] CONVENTIONS.md`" 혼용. kebab-case 파일 네이밍 확인: dispatch-process.md, op-task-plan, plan-guide.md, opal-plan-agent 모두 준수. 신규 파일 없음(해당 없음). |
| D-5 | 리스크 분석 완전성 | **Pass** | §5 리스크 및 대응 5개 항목(R-T1~R-T5). R-T1: `docs/CONVENTIONS.md` 부재 시 자동 스킵 검증. R-T2: 136과 시점 분리 명시. R-T3: citation-rules 비채택 형식 통일. R-T4: M-5 중복 검증. R-T5: 3곳 양쪽 동기화 추적. 각 리스크의 영향/대응 명시. |

---

## 3. 지적 사항

없음. 모든 검증 항목이 Pass 판정.

---

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md | PLAN.md §2.1 4개 지점 채택 결정이 TASK.md 배경/확정 방향과 정합성 | **Pass** — TASK.md 확정 방향 §1~§4 (사전 주입 한정, 4개 지점 후보 제시, 최소 변경 원칙, 하위 호환) 모두 PLAN §2.1~§2.2에 정확히 반영. 확정 방향 4개를 4개 지점에 1:1 매핑. |
| TASK.md R-1~R-6 | PLAN.md §3 실행 체크리스트 Step 1~6 매핑 | **Pass** — R-1(Step 1)/R-2(Step 5)/R-3(Step 2-4)/R-4(Step 6)/R-5(Step 6)/R-6(Step 1~5 총괄). 각 Step의 완료 기준이 R 요구사항 AC(Acceptance Criteria)를 충족. |
| citation-rules.md | PLAN §2.5 M-1~M-5에서 citation-rules 적용 방식 정합성 | **Pass** — M-1은 SSOT 표 정의(포맷 불필요). M-2~M-4는 품질 체크리스트 항목으로 [MUST] 포맷 지정. M-5는 행동 규칙으로 [MUST] 포맷 명시. §2.4 [MUST] 포맷 "원문 인용" 준수. 비채택 결정(M-5에 citation-rules §2.5 확장 안 함) 정당화. |
| pm-review-gate.md §13 | PLAN §2.2에서 136 사후 검증과 책임 분리 · 시너지 정합성 | **Pass** — pm-review-gate.md §13 "컨벤션 자동 진단" 트리거(EXECUTE 단계 / changed_files 대상)와 본 태스크(PLAN 단계 / PLAN.md 자체) 시점·대상·메커니즘 완전 분리. 본 태스크 변경(M-1~M-5)이 §13 발동 조건 또는 로직 변경 없음 → 충돌 없음 + 이중 안전망 시너지. |
| dispatch-process.md | PLAN §2.5 M-1 변경 계획이 dispatch-process.md 현황 조사와 정합성 | **Pass** — §1.3(1) D-1 현황 조사에서 "`opal/core/references/pm/dispatch-process.md:48-65` '인용 의무 규칙' 표" 확인 → M-1 변경 위치(§Step 3 표 기준 컬럼) 명확. 추가 코드 리딩 확인 완료. |
| op-task-plan SKILL.md | PLAN §2.5 M-2/M-3 변경(품질 체크리스트)이 SKILL.md 현황과 정합성 | **Pass** — §1.3(3) D-3 현황 조사에서 "`opal/skills/op-task-plan/SKILL.md:198-200` 및 `plan-guide.md:157-159` 품질 체크리스트" 확인 → M-2/M-3 위치(마지막 항목 다음) 및 내용(마지막 항목 포맷과 동일) 명확. |
| op-dev-plan SKILL.md | PLAN §2.5 M-4 변경(품질 체크리스트)이 SKILL.md 현황과 정합성 | **Pass** — §1.3(4) D-4 현황 조사에서 "`opal/skills/op-dev-plan/SKILL.md:435-437` 품질 체크리스트" 확인 → M-4 위치(op-task-plan과 대칭) 및 내용 명확. |
| opal-plan-agent AGENT.md | PLAN §2.5 M-5 변경(행동 규칙)이 AGENT.md 현황과 정합성 | **Pass** — §1.3(2) D-2 현황 조사에서 "`opal/agents/opal-plan-agent/AGENT.md:33-46 자체 로드 문서 / :83-89 행동 규칙`" 확인 → M-5 위치(행동 규칙 끝) 및 의도(Read만 강제, PLAN.md 옮김 의무는 미정의 갭) 명확. |

---

## 5. 판정

**Pass**

PLAN.md는 TASK.md R-1~R-6 요구사항을 정밀 분석으로 충족한다. 4개 잠재 적용 지점(D-1~D-5)에 대해 채택/부분 채택/비채택 결정을 근거와 함께 제시했으며, 5개 변경 파일(M-1~M-5)의 정확한 변경 위치·내용·완료 기준을 명시했다. 6단계 실행 체크리스트는 TASK 요구사항 및 citation-rules 포맷 준수를 완전히 분해했다. 하위 호환성(docs/CONVENTIONS.md 부재 시 자동 스킵)을 5개 변경 지점 모두에서 명시했고, 136 (사후 검증)과의 책임 분리 및 시너지를 명확히 설계했다. 체크리스트, 참조 문서, 핵심 설계의 인라인 인용이 citation-rules.md 규칙을 준수한다.

---

## 부록: TASK.md 요구사항 체크리스트 갱신

아래 R-1~R-6 체크박스를 **PLAN.md 검증 완료 기준**에 따라 갱신:

- [x] **R-1: PM 디스패치 측 강제** — PLAN.md §2.5 M-1에서 dispatch-process.md §Step 3 인용 의무 카탈로그에 컨벤션 명시, 예시, 템플릿 항목 추가 명시. 워커 컨텍스트 주입 템플릿에 "핵심 제약" 필드 추가.
- [x] **R-2: PLAN 에이전트 측 강제** — PLAN.md §2.5 M-5에서 opal-plan-agent AGENT.md §행동 규칙에 "[MUST] CONVENTIONS.md [MUST] 항목... PLAN.md에 [MUST] 포맷으로 인용" 의무 신설.
- [x] **R-3: PLAN.md 산출물 측 검증** — PLAN.md §2.5 M-2(op-task-plan SKILL.md), M-3(op-task-plan plan-guide.md), M-4(op-dev-plan SKILL.md)에서 품질 체크리스트에 컨벤션 [MUST] 인용 검증 항목 추가.
- [x] **R-4: 인용 규약 측 토큰 확장 결정** — PLAN.md §2.1 #4에서 citation-rules.md §2.5 토큰 확장 "비채택" 결정 및 근거(트랙 매트릭스 충돌, 6종 토큰 사실상 커버, §2.4로 충분) 명시.
- [x] **R-5: 하위 호환 명문화** — PLAN.md §1.4 영향 범위 + §2.1~§2.5 M-1~M-5 + §리스크 R-T1에서 "`docs/CONVENTIONS.md` 부재 시 자동 스킵" 명시 (5개 변경 지점 전부).
- [x] **R-6: 적용 지점 결정 근거 PLAN.md 기재** — PLAN.md §2.1 "잠재 적용 지점 4개 채택 결정" 표에서 #1~#4 각각의 채택/비채택 + 정밀한 근거 명시.

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-05-08 | 초기 작성 — op-task-qa SKILL.md 기준 PLAN.md 검증 완료 |
