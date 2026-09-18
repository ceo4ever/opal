# ANALYSIS: 분석 코어 공유 SSOT 신설

> 작성일: 2026-08-22
> 입력: TASK.md
> 출력: ANALYSIS.md

## 확정 입력 판정

TASK.md에는 `[결정]` 16건(지시서 표기 "15건"과 1건 불일치 — 지시서 오기로 판단, 원문 16건 전건 판정), `[사실]` 6건이 있다.

**판정 규칙(2분리, B-3)**: `[결정]`은 소유자 권한 행사이므로 근거 등급 판정 대상이 아니다(`opal/core/references/harness/citation-rules.md:455` §9(f) "결정은 등급 판정 대상이 아니다") — 기본 판정값은 `해당없음(결정)`이며, 결정 문장에 **사실 오류가 내재**된 경우에만 `수정필요`/`사실오류`로 강등한다(재설계는 여전히 하지 않는다). `[사실]`은 재도출 금지 대상이 아니므로(`opal/skills/op-dev-analysis/SKILL.md:30`) E1~E4로 대조 확인해 `유효(대조 확인)`/`수정필요`/`사실오류`로 판정한다.

| 항목 | 판정 | 근거 |
|------|------|------|
| [결정] A 지식 선조회 3단 | 해당없음(결정) | - |
| [결정] C 체크리스트·템플릿 SSOT 수렴 | 해당없음(결정) | - |
| [결정] D MCP 목록 복제 제거 | 해당없음(결정) | - |
| [결정] F 기술 컨텍스트 SSOT 승격 | 해당없음(결정) | - |
| [결정] G 분석 질문 Q표(권장) | 해당없음(결정) | - |
| [결정] H 핸드오프 표 고정 섹션화 | 해당없음(결정) | - |
| [결정] I 원문 덤프 차단 배선 | 해당없음(결정) | - |
| [결정] E ANALYSIS PM Gate 보강 | 해당없음(결정) | - |
| [결정] J plan-guide.md 동일 개정(opds 경로) | 해당없음(결정) | 내재 사실 확인: opds는 `op-dev-plan`을 그대로 디스패치한다(`opal/skills/opal-pilot-dev-short/SKILL.md:45`) — 대상 파일 특정에 사실 오류 없음 |
| [결정] K TASK 확정 사실 재확인 면제(도구 판정) | 해당없음(결정) | - |
| [결정] L PLAN의 ANALYSIS 확정 승계 | 해당없음(결정) | - |
| [결정] 배치(harness/analysis-core.md) | 해당없음(결정) | 내재 사실 확인: `_shared/` 대안이 신규 탐색 경로 규칙을 요구한다는 전제에 사실 오류 없음 — `docs/CONVENTIONS.md` 네이밍 규칙에 `_shared/` 계열 폴더 규약 부재 확인 |
| [결정] 역할 분리(절차/형식) | 해당없음(결정) | - |
| [결정] B 흡수(증분=A 하위 규칙) | 해당없음(결정) | - |
| [결정] 목표 달성 측정(재생성 1회 대조) | 해당없음(결정) | - |
| [결정] 임계 기준(baseline 대비 감소) | 해당없음(결정) | - |
| [사실] evidence-check 라우터·exit 0 | 유효(대조 확인) | 원천 대조: `opal/tools/state-tool/state_tool.py:2621`·`opal/tools/state-tool/state_tool.py:2630`·`opal/tools/state-tool/state_tool.py:2639`(3개 반환 경로 전부 `sys.exit(0)`)·`opal/tools/state-tool/state_tool.py:2554`(`confirmed_ratio` 산출). 사본 대조: `opal/tools/state-tool/README.md:267-304` — 도구의 현행 동작은 원천(코드)으로 판정하고 README는 보조로만 인용한다 |
| [사실] 파싱 대상 = 명확화 결과 표만 | 유효(대조 확인) | 대조 대상: `opal/tools/state-tool/state_tool.py:2517-2527`(confirmed_col_idx/dependency_col_idx가 `## 명확화 결과` 표 헤더에서만 탐색) |
| [사실] ANALYSIS는 [결정]만 면제, [사실]은 재확인 대상 | 유효(대조 확인) | 대조 대상: `opal/skills/op-dev-analysis/SKILL.md:30` 원문 일치 |
| [사실] PLAN 재사용 지시 위치·강도 | 유효(대조 확인) | 대조 대상: `opal/skills/op-dev-plan/references/plan-guide.md:88`(헤딩만)·`opal/skills/op-dev-plan/references/plan-guide.md:104`("간략 작성", MUST 아님)·`opal/skills/op-dev-plan/references/plan-guide.md:115`(헤딩만) |
| [사실] brain 선별·stale 스냅샷 | 유효(대조 확인) | 대조 대상: `opal/core/references/opal-pm.md:243-244` 원문 일치 |
| [사실] E5 단독 인용 금지 | 유효(대조 확인) | 대조 대상: `opal/core/references/harness/citation-rules.md:451` 원문 일치 |

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | 인용 규칙 | `opal/core/references/harness/citation-rules.md` | 원문 금지(§2.2)·근거 등급(§9)·E5 단독 금지(§9(e)) 판정 |
| D-2 | 설계 | 하네스 | `opal/core/references/opal-harness.md` | §2 모듈 표 형식·행 추가 규칙(Q7) |
| D-3 | 소스 | state-tool 본체 | `opal/tools/state-tool/state_tool.py` | evidence-check 파서 확장 지점(Q3·Q4) |
| D-4 | 소스 | state-tool 테스트 | `opal/tools/state-tool/tests/test_state_tool.py:4225-4260` | 기존 계약 제약(4열 고정) 확인 |
| D-5 | 소스 | state-tool README | `opal/tools/state-tool/README.md:260-304` | evidence-check 반환 계약 원문 |
| D-6 | 설계 | opd 오케스트레이터 | `opal/skills/opal-pilot-dev/SKILL.md` | STEP 2 디스패치 프롬프트 슬롯(R-5) |
| D-7 | 설계 | opd pipeline.json | `opal/skills/opal-pilot-dev/references/pipeline.json` | analysis.pm_gate checklist 현황(Q5) |
| D-8 | 설계 | Dev QA 가이드 | `opal/skills/op-dev-qa/references/qa-dev-guide.md` | R/P 번호 체계 원본(Q6) |
| D-9 | 설계 | op-dev-qa 스킬 | `opal/skills/op-dev-qa/SKILL.md:118-121` | R/P 번호 거울 사본(Q6) |
| D-10 | 설계 | 분석 코어 4파일 | `op-dev-analysis/SKILL.md`·`analysis-guide.md`·`tech-context-guide.md`·`op-dev-plan/plan-guide.md` | Q1·Q2 이관·중복 조사 대상 |
| D-11 | 설계 | opds 오케스트레이터 | `opal/skills/opal-pilot-dev-short/SKILL.md:45` | opds가 op-dev-plan을 그대로 쓰는지 확인([결정]J 판정 근거) |
| D-12 | 설계 | MCP 레지스트리 | `opal/core/references/mcps.md` | 등록 MCP 4종 확인(R-3 사실오류 방지) |
| D-13 | 설계 | PM 디스패치 프로세스 | `opal/core/references/pm/dispatch-process.md:120-129` | code-scan 사전 조회 PM 규범(선조회 3단 근거) |
| D-14 | 설계 | opal-pm | `opal/core/references/opal-pm.md:238-247` | brain 파생 스냅샷 특성([사실] 재확인) |
| E5 동반 | 지식 | brain concept 5건 | `.opal/brain/pages/concept/{new-ssot-pointer-not-value-copy,loop-upper-bound-ssot-pattern,template-precedence-over-prose-norms,analysis-drift-pm-cross-verify-lesson,evidence-tier-asis-tobe-jurisdiction}.md` | 기존 결정·교훈 승계(D-1~D-14 E1~E4 동반, §9(e) 준수) |

**사전 조회 실행**: `~/.opal/tools/code-scan/run.sh search "analysis-core"` 호출 — 신설 예정 파일이 대상이라 0건은 사전에 정해진 결과였다(검증이 아니라 자기 관측 기록). `~/.opal/tools/code-scan/run.sh depends opal/tools/state-tool/state_tool.py` → 의존 없음, `test_worktree_tool.py`만 역의존.

**폴백 판정(PM 실측 인계, B-4)**: `.opal/code-scan.json`의 `headerSource`는 `inline`이며 `inline`|`manifest`는 상호 배타다(병합 규칙 없음, `opal/tools/code-scan/code-scan.js:567` `resolveHeaderSource`). `~/.opal/tools/code-scan/run.sh validate` coverage는 **29.9%(102/341)**로, `opal/core/references/harness/header-rules.md:129-137` §빈 결과 폴백의 **②분기(30% 미만 → code-scan + Glob/Grep 동시 활용)**에 해당한다. 본 태스크 대상 9개 파일 중 code-scan 인덱스 등재는 `opal-harness.md`·`state_tool.py` 2개뿐이었다(`opal/**/*.md` 213개 중 인덱스 등재 24건과 대비). 즉 이번 조사에서 Grep을 주 도구로 쓴 것은 이탈이 아니라 **§빈 결과 폴백 ②분기 발동 — code-scan + Grep 동시 활용(규범 경로)**이다. `opal/core/references/harness/header-rules.md:139`가 규정하는 폴백 발동 기록은 STATE.md 소관(PM 기재)이며 본 산출물은 반영 사실만 명시한다.

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

| 순서(Tier) | 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|------|----------|-------------|
| 1 | `opal/core/references/harness/analysis-core.md` | 신규 SSOT(지식 선조회·증분·델타·깊이·6영역·의존성/영향범위·체크리스트) | 신규 생성 | - |
| 2 | `opal/core/references/opal-harness.md` | §2 하네스 모듈 표 | 1행 추가(analysis-core.md 존재를 전제) | `opal/core/references/opal-harness.md:99-113` |
| 2 | `opal/skills/op-dev-analysis/SKILL.md` | 확정 입력 소비 규약·체크리스트·저장 형식 | 체크리스트 포인터화 + Q표/핸드오프 표 템플릿 추가 | `opal/skills/op-dev-analysis/SKILL.md:166-179`(체크리스트), `opal/skills/op-dev-analysis/SKILL.md:72-156`(템플릿) |
| 2 | `opal/skills/op-dev-analysis/references/analysis-guide.md` | 파일 탐색·분석 깊이·의존성·영향범위·체크리스트 | 선조회 절차로 §1.1 교체 + 체크리스트 포인터화 | `opal/skills/op-dev-analysis/references/analysis-guide.md:11-24`(Glob/Grep 직행 — PM 규범 충돌), `opal/skills/op-dev-analysis/references/analysis-guide.md:46-65`(깊이 기준), `opal/skills/op-dev-analysis/references/analysis-guide.md:146-163`(체크리스트) |
| 2 | `opal/skills/op-dev-analysis/references/tech-context-guide.md` | MCP 매핑 기준·§6 템플릿 | 미등록 MCP 삭제 + SSOT 포인터 구조로 교체 | `opal/skills/op-dev-analysis/references/tech-context-guide.md:100-105`(MCP 매핑 기준) |
| 2 | `opal/skills/op-dev-plan/references/plan-guide.md` | 6영역 분류·ANALYSIS 재사용 지시·품질 체크리스트 | analysis-core.md 포인터 배선 + 승계 [MUST]화 | `opal/skills/op-dev-plan/references/plan-guide.md:88`,`opal/skills/op-dev-plan/references/plan-guide.md:104`,`opal/skills/op-dev-plan/references/plan-guide.md:115`(재사용 지시), `opal/skills/op-dev-plan/references/plan-guide.md:90-98`(6영역) |
| 3 | `opal/skills/op-dev-qa/references/qa-dev-guide.md` | ANALYSIS R-1~R-6/PLAN P-1~P-7 | 098 규약 검증 축 + 원문덤프 검증 행 추가 | `opal/skills/op-dev-qa/references/qa-dev-guide.md:67-90` |
| 3 | `opal/skills/op-dev-qa/SKILL.md` | R/P 번호 거울 사본 | qa-dev-guide.md와 **동일 시점** 갱신 필요(스코프 외이나 정합 필수, drift 방지) | `opal/skills/op-dev-qa/SKILL.md:118-121` |
| 3 | `opal/skills/opal-pilot-dev/SKILL.md` | STEP 2 디스패치 프롬프트 | Q1~QN 질문 슬롯 추가 | `opal/skills/opal-pilot-dev/SKILL.md:38-50` |
| 3 | `opal/skills/opal-pilot-dev/references/pipeline.json` | `analysis.pm_gate.checklist` | `["-"]` → 실제 항목 배열(Tier2 SKILL.md 판정표 확정 후 채움) | `opal/skills/opal-pilot-dev/references/pipeline.json:9-10` |
| 4a | `opal/tools/state-tool/tests/test_state_tool.py` | 근거 판정 테스트 | 신규 계약 RED 테스트 선(先)작성(RED-first) | `opal/tools/state-tool/tests/test_state_tool.py:4225-4260`(기존 클래스 제약) |
| 4b | `opal/tools/state-tool/state_tool.py` | evidence-check 파서 | `## 확정된 설계 방향` 파싱 확장(4a RED 테스트 통과가 목표, GREEN) | `opal/tools/state-tool/state_tool.py:2228`,`opal/tools/state-tool/state_tool.py:2447`,`opal/tools/state-tool/state_tool.py:2495-2557`,`opal/tools/state-tool/state_tool.py:2560-2639` |

**순서 근거(Q9 보강 — Tier 표기로 정정)**: 이전 버전은 순서 값이 행 번호와 동일해 정보량이 0이었다(모든 표가 위→아래 순서이므로 "순서=행번호"는 항상 참인 동어반복). §1.3 의존성 맵 기준 **부분 순서(partial order)**만 실재하므로 강제 선형 1~12가 아니라 Tier로 표기한다: Tier1(analysis-core.md 신설, 단독 선행) → Tier2(하네스 표 행 + 3개 스킬 포인터 배선, **Tier1 완료 후 상호 독립·병렬 가능**) → Tier3(qa-dev-guide.md·거울 사본·opd SKILL·pipeline.json — 전부 Tier2의 SKILL.md 확정 입력 판정표 **형식**이 고정된 뒤에만 가능, Tier2의 나머지 3개와는 직접 의존 없음) → Tier4(state-tool 파서, RED-first로 4a가 4b보다 먼저 — 문서 체인과 독립적인 별도 트랙). Tier2가 5개 파일을 묶는 것 자체가 "이 5개는 순차가 아니라 병렬 가능"이라는 정보이며, Tier3가 Tier2 전체가 아니라 그중 SKILL.md 1개에만 의존한다는 점은 근거 열에 명시했다.

### 1.2 아키텍처 패턴

절차 SSOT는 `opal/core/references/harness/*.md`에 두고 오케스트레이터·스킬이 Read로 참조하는 **포인터 패턴**이 프레임워크 전역 규범이다(citation-rules.md, red-first.md, track-routing.md 선례). 산출물 템플릿은 각 스킬 SKILL.md가 소유한다(역할 분리 원칙, [결정] "역할 분리"와 정합).

### 1.3 의존성 맵

`op-dev-analysis/SKILL.md` → (Read) `analysis-guide.md` + `tech-context-guide.md` → (신설 후) `analysis-core.md`. `op-dev-plan/plan-guide.md`는 독립적으로 6영역·재사용 규칙을 소유하며 analysis-core.md 신설 후 포인터로 전환된다. `state_tool.py`의 `cmd_verify`(:2560)는 `_check_evidence_gate`(:2495)에 의존하고, 이는 `_locate_clarification_table`(:2228)·`_evaluate_evidence_item`(:2453)·`_has_decision_tag`(:2447)에 의존한다 — 신규 파서는 이 체인과 병렬로 붙는다(대체 아님).

### 1.4 테스트 현황

`test_state_tool.py`의 `TestT098EvidenceCheck`(:4225)는 mock 금지·실 파일 픽스처 원칙(RED-first)을 따르며, "`## 명확화 결과` 표는 열 4개 고정 — 열 추가는 설계에 없다"는 제약을 클래스 docstring에 명문화하고 있다(:4237-4238). 이는 R-10 구현이 **테이블 열 확장이 아니라 별도 섹션 파서 신설**이어야 함을 뜻한다.

## 2. 외부 조사 결과

해당 없음 — 외부 라이브러리/API 의존 없음(순수 프레임워크 내부 문서·Python 도구 변경).

## 3. 영향 범위

### 3.1 직접 영향

**총 12파일**(§1.1 표 = 실행 대상 확정 목록) — 본 문서 Q6·H-4가 `opal/skills/op-dev-qa/SKILL.md`를 정합 필수로 편입할 것을 지적했고, **TASK.md 범위는 이를 반영해 12파일로 정정 완료**(2026-08-23). 본 문서와 TASK.md 모두 12파일이 기준 수치다.

### 3.2 간접 영향

- opds(`opal-pilot-dev-short`)는 `op-dev-plan`을 그대로 호출하므로 plan-guide.md 개정이 자동 전파된다([결정]J 유효, D-11).
- **`op-task-plan/references/plan-guide.md`는 물리적으로 별도 파일**(179줄, `op-dev-plan/plan-guide.md`의 476줄과 무관)이며 TASK.md 범위(12파일)에도 없다 — 배제가 TASK.md에 명시적 결정으로 기록되었다 — `opp`/`oppd` 경로는 이번 개정의 수혜 대상에서 제외된다(§7 Q8, 리스크 H-3).
- `opal-pilot-sdd` 계열은 `spec-plan-guide.md`라는 별도 가이드를 쓰며 analysis-core.md와 무관.

### 3.3 영향 범위 요약

체크 규칙(통일): 해당하면 `[x]`, 해당 없으면 `[ ]`.

- [ ] DB 스키마 변경 — 해당 없음
- [ ] API 인터페이스 변경 — 해당 없음
- [ ] 설정/환경변수 변경 — 해당 없음(문서·파서 로직만)
- [x] 빌드/배포 파이프라인 변경 — **해당 있음** — `state_tool.py` 소스 변경은 `~/.opal/tools/state-tool/`(배포본)에 반영되려면 `./scripts/install-mac.sh` 재배포가 필요하다. 그런데 TASK.md 제약("배포본 직접 편집 금지, 재배포는 소유자가 수행")과 범위(12파일)는 재배포 실행 자체를 포함하지 않는다 — **해당 있음, 단 범위 제외(미해결)**로 표기한다(H-6).

## 4. 핵심 발견 사항

1. `analysis-core.md`가 흡수해야 할 7항목(R-1 "무엇을") 중 **"지식 선조회 3단"·"델타 탐색 규율"은 현재 프레임워크 어디에도 존재하지 않는 순수 신규 항목**이다(§7 Q1) — 이관이 아니라 신규 저술이 필요하다.
2. `tech-context-guide.md`는 7항목 중 0건과 매칭된다 — analysis-core.md 이관 대상이 아니라 고유 영역(기술스택·MCP)을 유지하며, 이번 태스크에서는 R-3·R-4 범위로만 개정된다.
3. 4파일 전체(SKILL.md·analysis-guide.md·tech-context-guide.md·plan-guide.md) 교차 비교 결과, 정규화 후 20자 이상 완전 일치 줄은 **6건**이다(§7 Q2 재측정 baseline — TASK.md 배경분석의 "6항목" 표기는 표현이 다른 항목을 가리켰을 가능성이 있음, 본 수치를 R-9 baseline으로 채택). 이 중 `plan-guide.md`와 다른 두 파일 사이의 정확 일치는 **0건**이었다 — Q1에서 "축소 중복"이라 본 6번 항목은 개념적 유사성일 뿐 문자열 중복이 아니다.
4. `verify --evidence-check` 확장은 **표 열 추가가 아니라 별도 파서 신설**이 필요하다 — `## 확정된 설계 방향`은 표가 아닌 불릿 리스트이고, 기존 테스트가 "열 4개 고정" 계약을 명문화하고 있다(§1.4, §7 Q3·Q4).
5. `opal/skills/op-dev-qa/SKILL.md:118-121`은 `qa-dev-guide.md`의 R/P 번호를 그대로 복제한 거울 사본이며, 본 문서가 12번째 대상으로 편입할 것을 지적해 TASK.md 범위에 반영됐으며 R-7·R-8·R-11이 qa-dev-guide.md에 행을 추가하면 이 사본도 함께 갱신하지 않으면 즉시 drift가 발생한다(§7 Q6).
6. brain 교훈 3건이 이번 개정의 실행 위험과 직결된다 — (a) 「신규 SSOT 포인터, 수치 복제 금지」(`new-ssot-pointer-not-value-copy`, E5·task:098 DONE §3 동반 E4)는 analysis-core.md가 하네스 루프 상한(`opal/core/references/opal-harness.md:44-59`)·근거 등급표(`opal/core/references/harness/citation-rules.md:420-465`)·MCP 레지스트리(`mcps.md`)의 수치를 복제하지 말고 포인터만 둬야 함을 재확인시킨다. (b)·(c)는 H-7·H-8로 리스크화했다.

## 5. 제약/리스크

| 항목 | 설명 | 심각도 | 근거 |
|------|------|--------|------|
| H-1 | `## 확정된 설계 방향`은 표가 아닌 불릿 리스트라 `_locate_clarification_table` 재사용 불가 — 신규 파서 함수 저술이 필요해 R-10의 공수가 과소 추정될 수 있다 | Medium | `opal/tools/state-tool/state_tool.py:2228-2268`(표 전용) vs TASK.md §확정된 설계 방향(불릿 서식) |
| H-2 | `confirmed_ratio`의 분모가 "명확화 결과 4요소"에서 "+확정된 설계 방향 N건"으로 늘어나면, 기존 소비자(README 예시·PM 판단 관행)의 암묵적 "4요소" 전제가 깨진다 — 병합형 단일 ratio vs 분리형 두 ratio 중 설계 결정이 PLAN에 필요하다 | Medium | `opal/tools/state-tool/state_tool.py:2554-2557`(len(items) 분모), README.md:288-289 |
| H-3 | `op-task-plan/plan-guide.md`(opp/oppd 경로)가 스코프 밖으로 확인되어, 개정 효과가 opd/opds에는 미치고 opp/oppd에는 미치지 않는 비대칭이 발생한다 — TASK.md에 이 배제가 명시적 결정으로 기록되어 있지 않다 | Low | `opal/skills/op-task-plan/references/plan-guide.md`(179줄, op-dev-plan 사본과 별개 파일) |
| H-4 | `opal/skills/op-dev-qa/SKILL.md:118-121`이 스코프 외 파일이라 R-7·R-8·R-11 실행 시 빠뜨리면 즉시 문서 drift(TASK.md 결정 C가 노리는 것과 반대 결과)가 재발한다 | Medium | `opal/skills/op-dev-qa/SKILL.md:118-121` vs `opal/skills/op-dev-qa/references/qa-dev-guide.md:67-104` |
| H-5 | `analysis-core.md`의 하네스 모듈 표 신규 행에서 "해당 §" 열에 대응할 opal-harness.md 기존 절이 없다(ANALYSIS/PLAN 전용 절이 harness 본문에 없음) — 신규 stub 절 신설 여부를 PLAN이 결정해야 한다 | Low | `opal/core/references/opal-harness.md:99-113`(기존 행 전부 §1~§10 기존 절에 대응) |
| H-6 | TASK.md 제약이 install 재배포를 범위에서 제외했으나 `state_tool.py`는 배포본을 통해 워커에 도달한다 — EXECUTE 완료 후 재배포가 없으면 R-10 파서 확장이 실제 태스크 실행에는 반영되지 않는다(문서만 고쳐지고 도구는 구버전으로 남는 상태) | Medium | TASK.md §제약조건("배포본 직접 편집 금지, 재배포는 소유자가 수행") vs `opal/tools/state-tool/state_tool.py`(변경 대상 소스, 배포 경로 `~/.opal/tools/state-tool/`) |
| H-7 | R-5의 "Q표 권장(강제 아님)" 조항이 SKILL.md 템플릿에 실물 섹션으로 반영되지 않고 산문 서술로만 남으면, 준수율이 0%로 떨어진 실측 선례가 있다 — 산문 규칙은 유도력이 없다 | Medium | brain `template-precedence-over-prose-norms`(E5, task:099 DONE.md §5 회차 1~2 동반 E4 — 동일 회차 산문 0/3 vs 템플릿 3/3) |
| H-8 | 목표 달성 AC-G1~G4(TASK.md §목표 달성 AC, "재생성 1회 대조")가 "문서는 고쳤는데 워커 행동은 그대로"를 검출하려면 PM이 재생성 ANALYSIS.md를 직접 Read해 baseline과 대조해야 한다 — ANALYSIS 산출물 서술을 그대로 신뢰하면 실행 오류로 이어진 선례가 있다 | Low | brain `analysis-drift-pm-cross-verify-lesson`(E5, task:031 DONE.md §특이사항 동반 E4 — ANALYSIS 환각을 PM 미교차검증으로 PLAN이 신뢰해 회귀 발생) |

## 6. 기술 컨텍스트

### 6.1 기술 스택

프로젝트 SSOT: `docs/PROJECT.md`(전체) — 본 태스크 관련 델타만 기재.

| 카테고리 | 기술 | 델타 |
|----------|------|------|
| 문서 | Markdown | OPAL 프레임워크 규범 문서(변경 대상 8건) |
| 코드 | Python 3 | `state_tool.py`(정규식·파서 확장) + `pytest`(RED-first 테스트) |
| 데이터 | JSON | `pipeline.json` checklist 필드 |

### 6.2 추천 스킬

해당 없음 — 프레임워크 자기 참조 작업으로 외부 스킬 불필요.

### 6.3 추천 MCP

해당 없음 — `mcps.md` 등록 4종(shadcn/sequential-thinking/context7/playwright) 모두 본 태스크와 무관.

## 7. 지정 분석 질문 Q1~Q9 답변

### Q1 — analysis-core.md 단독 소유 항목 vs 현재 소재

| # | 항목(R-1 "무엇을") | 현재 소재(파일:줄번호) | 이관 성격 |
|---|---------------------|------------------------|----------|
| 1 | 지식 선조회 3단(brain→code-scan→docs→과거 산출물) | 없음(신규) — 상충 지시만 존재: `opal/skills/op-dev-analysis/references/analysis-guide.md:11-24`(Glob/Grep 직행) vs `opal/core/references/pm/dispatch-process.md:120-129`(code-scan 선조회 PM 규범) | 신규 저술 + 기존 상충 지시 교체 |
| 2 | 증분 소비 규율(B 흡수) | 부분 존재: `opal/skills/op-dev-plan/references/plan-guide.md:100-113`(ANALYSIS.md 유무에 따른 "간략 작성"/"Full 수행" 분기) — PLAN 전용, ANALYSIS 자체엔 없음 | 신규 저술(ANALYSIS 측 규율은 없음) |
| 3 | 델타 탐색 규율 | 없음(신규) | 신규 저술 |
| 4 | 분석 깊이 기준 | `opal/skills/op-dev-analysis/references/analysis-guide.md:46-65`(태스크 유형별 표 + 데이터 파이프라인 추가사항) | 이관(그대로 이동) |
| 5 | 관련 파일 맵 6영역 축 | `opal/skills/op-dev-plan/references/plan-guide.md:90-98`(6영역 라벨 정의, PLAN 전용) — ANALYSIS §1.1 템플릿(`opal/skills/op-dev-analysis/SKILL.md:97-101`)엔 영역 축 없음 | PLAN에서 이관 + ANALYSIS 신규 적용 |
| 6 | 의존성/영향 범위 도출 | `opal/skills/op-dev-analysis/references/analysis-guide.md:32-37`(§1.3)·`opal/skills/op-dev-analysis/references/analysis-guide.md:114-134`(§4) / `opal/skills/op-dev-plan/references/plan-guide.md:115-120`(§2.N.3, 구조 유사 — 정확 문자열 중복 아님, §7 Q2 정정) | 이관 + PLAN 측 구조 통합(문자열 dedup 대상 아님) |
| 7 | 품질 체크리스트 | `opal/skills/op-dev-analysis/SKILL.md:166-179`(10항목) ↔ `opal/skills/op-dev-analysis/references/analysis-guide.md:146-163`(9항목, 3분류) | 통합 이관(SSOT 1곳) |

`tech-context-guide.md`는 7항목 전체와 매칭 0건 — 이관 대상 아님.

### Q2 — 4개 파일 간 중복 문장·문단 (R-9 baseline, B-2 확장)

**측정 방법**: `op-dev-analysis/SKILL.md`·`analysis-guide.md`·`tech-context-guide.md`·`op-dev-plan/plan-guide.md` **4파일 전체**를 줄 단위로 정규화(리스트/인용/헤딩 마커·볼드·백틱 제거, 연속 공백 압축) 후, 정규화 결과가 **20자 이상**이면서 **서로 다른 2개 이상 파일**에서 완전 일치하는 줄만 계수한다. 순수 마크다운 표 구분선(`|---|---|` 류, 3건: `opal/skills/op-dev-analysis/SKILL.md:83/193`↔`opal/skills/op-dev-plan/references/plan-guide.md:70`, `opal/skills/op-dev-analysis/SKILL.md:90`↔`opal/skills/op-dev-plan/references/plan-guide.md:205`, `opal/skills/op-dev-analysis/SKILL.md:147`↔`opal/skills/op-dev-analysis/references/tech-context-guide.md:125`)과 citation-rules.md §3.1이 전 산출물에 강제하는 공통 참조표 헤더(`| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |`, 1건: `opal/skills/op-dev-analysis/SKILL.md:89`↔`opal/skills/op-dev-plan/references/plan-guide.md:204`)는 규범이 요구하는 필수 반복 구조이므로 "제거 대상 중복"에서 제외한다(합 4건 별도 계상, R-2/R-9 dedup 비대상).

재현 명령:
```bash
python3 -c "
import re
files = ['opal/skills/op-dev-analysis/SKILL.md','opal/skills/op-dev-analysis/references/analysis-guide.md','opal/skills/op-dev-analysis/references/tech-context-guide.md','opal/skills/op-dev-plan/references/plan-guide.md']
def norm(l):
    l = re.sub(r'^\s*[-*]\s*\[[ xX]\]\s*', '', l.strip())
    l = re.sub(r'^\s*[-*>]\s*', '', l)
    l = re.sub(r'^#+\s*', '', l)
    l = re.sub(r'[*\`]', '', l)
    return re.sub(r'\s+', ' ', l).strip()
idx = {}
for f in files:
    for i, l in enumerate(open(f, encoding='utf-8'), 1):
        n = norm(l)
        if len(n) >= 20:
            idx.setdefault(n, []).append((f, i))
for n, occ in idx.items():
    if len({f for f,_ in occ}) >= 2:
        print(n, occ)
"
```

**결과 — 6건**(표 구분선·참조표 헤더 4건은 위에서 이미 분리 제외):

| 중복 쌍 | 내용(정규화 후) |
|---------|------|
| `opal/skills/op-dev-analysis/SKILL.md:20` ↔ `opal/skills/op-dev-plan/references/plan-guide.md:11` | "[MUST] 산출물에 소스코드 원문 블록을 기재하지 않는다 — ..."(111자, citation-rules 트리거 관용구 — R-2 dedup 비대상) |
| `opal/skills/op-dev-analysis/SKILL.md:170` ↔ `opal/skills/op-dev-analysis/references/analysis-guide.md:151` | "TASK.md의 모든 요구사항이 분석에 반영되었는가" |
| `opal/skills/op-dev-analysis/SKILL.md:171` ↔ `opal/skills/op-dev-analysis/references/analysis-guide.md:152` | "관련 파일 목록이 Glob/Grep으로 실제 확인되었는가 (추측 금지)" |
| `opal/skills/op-dev-analysis/SKILL.md:172` ↔ `opal/skills/op-dev-analysis/references/analysis-guide.md:153` | "의존성 맵이 import/require 기반으로 작성되었는가" |
| `opal/skills/op-dev-analysis/SKILL.md:173` ↔ `opal/skills/op-dev-analysis/references/analysis-guide.md:161` | "영향 범위가 직접+간접 모두 식별되었는가" |
| `opal/skills/op-dev-analysis/SKILL.md:176` ↔ `opal/skills/op-dev-analysis/references/analysis-guide.md:162` | "제약/리스크가 구체적 근거와 함께 기술되었는가" |

**중요 정정**: `plan-guide.md`와 `analysis-guide.md`/`tech-context-guide.md` 사이의 **정확 일치 중복은 0건**이다. Q1 6번에서 "축소 중복"이라 표현한 `opal/skills/op-dev-plan/references/plan-guide.md:115-120`(§2.N.3 영향 범위) ↔ `opal/skills/op-dev-analysis/references/analysis-guide.md:114-134`(§4 영향 범위 분석)는 문장 자체가 다르다(예: "관련 테스트 파일" vs "영향받는 테스트 파일" — 완전 일치 아님) — **개념적 유사성**이지 텍스트 중복이 아니므로 §7 Q1의 해당 행 서술은 "중복"이 아니라 "구조 유사"로 정정한다.

**R-9 baseline**: **6건**(위 표 전체, `plan-guide.md` 관여 1건 + `SKILL.md`↔`analysis-guide.md` 5건). `tech-context-guide.md`는 어떤 교차 쌍에도 등장하지 않는다(0건, §4 핵심발견 2와 일치). R-9 AC("analysis-core.md ↔ plan-guide.md 간 정규화 후 20자 이상 일치 문장 0건")의 개정 후 목표는 이 6건 중 `plan-guide.md` 관여분(현재 1건, MUST 트리거)이 유지되거나 사라지는지로 판정한다 — 이 1건은 SSOT+Trigger 관용구라 R-9가 노리는 "우발적 복제"가 아니므로 잔존이 AC 위반이 아닐 수 있다는 점을 PLAN이 명시적으로 판단해야 한다.

### Q3 — evidence-check 확장 지점

- 파서 진입점: `cmd_verify`(`opal/tools/state-tool/state_tool.py:2560`) → `--evidence-check` 분기(`opal/tools/state-tool/state_tool.py:2612-2639`).
- 현재 표 탐색 공유 함수: `_locate_clarification_table`(`opal/tools/state-tool/state_tool.py:2228`, `## 명확화 결과` **표** 전용).
- 판정 함수: `_evaluate_evidence_item`(`opal/tools/state-tool/state_tool.py:2453`), 결정 태그 판별: `_has_decision_tag`(`opal/tools/state-tool/state_tool.py:2447`, `[결정]` 문자열 포함 여부만 검사 — 불릿 리스트에도 재사용 가능).
- 통합 함수: `_check_evidence_gate`(`opal/tools/state-tool/state_tool.py:2495-2557`).
- **확장 지점**: `## 확정된 설계 방향`은 표가 아닌 불릿 리스트이므로, `_locate_clarification_table`의 형제 함수(신규, 예: `_locate_confirmed_direction_items`)를 `opal/tools/state-tool/state_tool.py:2268` 직후에 신설하고, `_check_evidence_gate`(`opal/tools/state-tool/state_tool.py:2495`) 또는 그 호출자 `cmd_verify`(`opal/tools/state-tool/state_tool.py:2612`)에서 두 결과를 병합하는 지점이 확장 지점이다. `_has_decision_tag`는 그대로 재사용 가능.

### Q4 — 계약 충돌 3점 점검

| 축 | 충돌 여부 | 근거 |
|----|----------|------|
| (a) exit 0 라우터 계약 | 없음 | evidence_check 분기는 3개 반환 경로 모두 `sys.exit(0)`(`opal/tools/state-tool/state_tool.py:2621`,`opal/tools/state-tool/state_tool.py:2630`,`opal/tools/state-tool/state_tool.py:2639`) — 확장 후에도 동일 패턴 유지 가능 |
| (b) `--clarification-check` 상호 배타 | 없음 | 신규 파싱은 기존 `--evidence-check` 플래그 안에서 처리되므로 `evidence_check_flag_conflict`(`opal/tools/state-tool/state_tool.py:2579-2580`) 로직 재사용, 신규 플래그 불필요 |
| (c) 섹션/표 부재 시 graceful skip | 설계 주의 필요 | `## 확정된 설계 방향`은 표가 아니므로 신규 파서가 **독자적으로** 부재 시 `None` 반환해야 기존 하위호환 정책(`opal/tools/state-tool/state_tool.py:2623-2630`)과 동형 유지됨 — 표 파서에 얹으면 깨진다 |
| `confirmed_ratio` 분모 정의 | **변경됨** | 현재 분모=`len(items)`(명확화 결과 4요소만, `opal/tools/state-tool/state_tool.py:2554-2555`) — 확정된 설계 방향 항목을 병합하면 분모가 커짐(H-2). 병합 방식은 PLAN 결정 필요 |

추가 제약: `opal/tools/state-tool/tests/test_state_tool.py:4237-4238`의 클래스 docstring이 "`## 명확화 결과` 표 열 4개 고정, 열 추가는 설계에 없다"를 명시 — 열 확장이 아닌 별도 섹션 파서로만 구현 가능.

### Q5 — pipeline.json `analysis.pm_gate.checklist` 스키마 제약과 선례

`validate_pipeline_spec`(`opal/tools/state-tool/state_tool.py:1162-1178`)의 검사: `gate.checklist`는 (1) 존재해야 하고 (2) 문자열 배열이어야 하며 (3) 비어있으면 안 된다(`spec_gate_checklist_empty`). 길이·문장 형식 제약은 없다 — 현재값 `["-"]`도 스키마상 유효(placeholder). `spec-validate` 서브커맨드(`cmd_spec_validate`, `opal/tools/state-tool/state_tool.py:1767`)가 CLI로 이 검사를 노출한다.

**타 pilot 8개 checklist 선례** (`plan.pm_gate` 등, 전 파이프라인 실측):
- 짧은 명사구/포인터 형태: `"PLAN.md §4.2"`, `"TASK.md 요구사항"`, `"PLAN.md §리스크 가설 표"`
- 판정 조건 서술형: `"컨벤션 자동 진단 PASS (GC-CONVENTION-*.md Critical/High 0건 — 컨벤션 적용 대상 ≥1건 시 발동)"`
- 항목 수는 1~5개 범위(`opal-pilot-sdd/spec.pm_gate`=1개 ~ `opal-pilot-project-dev/wbs.pm_gate`=5개)

analysis.pm_gate는 이 선례를 따라 "ANALYSIS.md §0/§1/§5" 등 섹션 포인터 + "확정 입력 판정표 완비" 같은 098 규약 검증 조건으로 채우면 정합적이다.

### Q6 — R-N/P-N 번호 체계 소비자

R-1~R-6/P-1~P-7/SP-1~SP-5 개별 번호를 실제로 나열하는 문서는 **`qa-dev-guide.md`(원본, `opal/skills/op-dev-qa/references/qa-dev-guide.md:67-104`)와 `op-dev-qa/SKILL.md`(거울 사본, `opal/skills/op-dev-qa/SKILL.md:118-121`) 2개뿐**이다. `op-task-qa/SKILL.md`·`pm-review-gate.md`·`agents.md`·`opal-task-qa-agent/AGENT.md`는 스킬명("op-dev-qa 참조")만 인용하고 개별 번호는 인용하지 않는다(전수 grep 확인). 따라서 R-7·R-8·R-11이 행을 추가하면 **두 파일을 동시에** 갱신해야 정합이 유지되며(현재도 이 둘은 완전 복제 관계 — 결정 C의 대상), 그 외 문서는 영향받지 않는다.

### Q7 — opal-harness.md §2 모듈 표 필드/탐색 규칙

표 스키마(4열, `opal/core/references/opal-harness.md:99`): `모듈 | 파일 | 로드 시점 | 해당 §`. 탐색 경로는 표 하단 각주(`opal/core/references/opal-harness.md:114`) 1곳에 고정: `{프로젝트}/.opal/references/harness/{file}` → `~/.opal/references/harness/{file}` — 행마다 반복 기재하지 않는다.

기존 행 선례:
- `red-first.md`(`opal/core/references/opal-harness.md:111`): 파일=`harness/red-first.md`, 로드 시점="TEST-SCENARIO 작성·EXECUTE 진입 시", 해당 §="§1.5"
- `track-routing.md`(`opal/core/references/opal-harness.md:112`): 파일=`harness/track-routing.md`, 로드 시점="`//opd` 진입 시 트랙 강등 판정 수행 시점(TASK 완료 직후)", 해당 §="§4"

`analysis-core.md` 신규 행은 파일=`harness/analysis-core.md`, 로드 시점="ANALYSIS/PLAN 단계 진입 시"로 채울 수 있으나, "해당 §" 열에 대응할 opal-harness.md 기존 절이 없다(H-5) — 신규 stub 절 번호 부여는 PLAN 결정 사항.

### Q8 — 영향 소비자 전수 조사

- `analysis-guide.md`: `op-dev-analysis` 계열(SKILL.md 자신) 외 참조 0건. (주의: `opal-project-init/references/code-analysis-guide.md`는 **이름이 유사한 완전히 다른 파일**이며 오탐 — grep 부분 문자열 일치로 혼동 주의, `opal/skills/opal-project-init/SKILL.md:452` 등에서 확인)
- `tech-context-guide.md`: `op-dev-analysis` 계열 3파일 외 참조 0건.
- `plan-guide.md`(op-dev-plan 사본, 476줄): op-dev-todo·op-sdd-plan·op-sdd-action-plan·op-task-plan·opal-pilot-sdd 등에서 파일명이 언급되나, **`op-task-plan/references/plan-guide.md`(179줄)는 물리적으로 별도 파일**이다(diff 확인, 헤더부터 상이) — opp/oppd 경로는 이번 개정과 무관(H-3). opds는 `op-dev-plan`을 그대로 쓰므로 자동 커버.
- `opal-pilot-sdd`는 `spec-plan-guide.md`라는 별도 문서를 사용 — analysis-core.md와 무관.
- `opal/agents/**`: `opal-task-agent`·`opal-fe-agent`·`opal-be-agent`·`opal-db-agent`·`opal-plan-agent`·`opal-task-action-agent`·`opal-loop-action-agent`가 `op-dev-analysis`/`op-dev-plan` 스킬명을 컨텍스트 로딩 절차에서 언급하지만, 가이드 파일명을 직접 지정하지 않고 SKILL.md를 통해 간접 참조한다 — SKILL.md만 정합되면 전파됨.
- **파급 파일 목록(스코프 외 추가 필요)**: `opal/skills/op-dev-qa/SKILL.md:118-121`(Q6) — 그 외 신규 발견된 필수 추가 파일 없음.

### Q9 — R-12(목표 달성 실측) 측정 실행 가능성 (opal-grill A축 보강)

**1. baseline 고정 시점/대상**: 3가지 선택지 모두 결함이 있다.
- 현재 파일 그대로 — "고정"이 아니라 이동 표적이다(오늘처럼 PM 보강 지시가 또 오면 baseline이 다시 바뀐다).
- git 특정 커밋 — 아직 커밋되지 않았다(Guards §1 — 사용자 승인 시에만 커밋), "하나의 태스크 = 하나의 커밋" 관행상 ANALYSIS 단계 전용 커밋 시점이 따로 없을 수 있다 / 보강 전 버전 — 이미 3회 Edit로 덮어써졌고 git 미커밋·별도 스냅샷 미보존이라 **물리적으로 복원 불가**(선택지 제외).
- **권고안(확정 아님 — 채택 여부는 PLAN 소관)**: ANALYSIS PM Gate 통과 시점에 `tasks/100-260822-opd-분석코어-공유SSOT/ANALYSIS.baseline.md`로 1회 사본 저장해 고정한다. ※ 본 권고는 2026-08-23 소유자 승인으로 채택되어 사본이 생성됐다 — 채택 사실은 TASK.md R-12 선행조건 ①에 기록돼 있다.

**2. 재생성 절차**

| 항목 | baseline(본 문서) | 재생성 |
|------|------|------|
| 저장 경로 | `tasks/100-260822-opd-분석코어-공유SSOT/ANALYSIS.md` | 별도 경로(예: `.../ANALYSIS-REGEN.md`) — baseline 덮어쓰기 금지 |
| TASK.md 입력 | `tasks/100-260822-opd-분석코어-공유SSOT/TASK.md`(무수정) | 동일 |
| 디스패치 주체 | PM(오케스트레이터) → 워커 | 동일 |
| 프롬프트 | PM이 사전 조회 의무·Q1~Q8·핵심 제약 원문을 **수동 슬롯으로 주입**(본 태스크 최초 디스패치 프롬프트) | 개정된 `opal/skills/op-dev-analysis/SKILL.md`(analysis-core.md 포인터 포함)만 참조하는 **표준 opd STEP 2 디스패치 프롬프트** — 수동 Q표·선조회 슬롯 제거(신 규범 자체 유도력이 측정 대상) |

**3. 오염 변수 처리 — 편향 명시 후 진행(대조 무효 아님)**: baseline은 PM이 선조회·Q표·핸드오프 표를 프롬프트로 직접 주입해 만들었으므로 **천장 효과**(ceiling effect)가 있다 — 개정 규범이 완벽히 작동해도 재생성이 baseline보다 더 나아 보이기 어렵다. AC-G2·AC-G3처럼 "존재/비율"형 지표는 baseline에도 이미 충족돼 있어 개선 증명력이 약하다는 한계를 DONE.md에 명시해야 한다. 완전한 오염 배제(제3의 신규 태스크로 대조군 확보)는 TASK.md 1회 재생성 범위를 넘어서므로 PLAN의 별도 승인 없이는 채택하지 않는다.

**4. AC-G1~G4 판정 명령**

| AC | 판정 명령 | 선행조건 |
|----|-----------|---------|
| AC-G1 | `~/.opal/tools/state-tool/run.sh verify <regen-task-path> --evidence-check`의 `items[].verdict`에 `승계` 값 존재 확인 | **R-10 GREEN 완료 필수** — 현재 `_evaluate_evidence_item`(`opal/tools/state-tool/state_tool.py:2453-2492`)의 verdict는 `확정`/`미확정` 2값뿐, `승계`는 아직 없다 |
| AC-G2 | `grep -Ec "code-scan\|brain" tasks/<regen-task-path>/ANALYSIS.md`(1 이상이면 충족) | 없음 |
| AC-G3 | §7 Q2 코드펜스 계수 방식과 동일한 awk 스크립트(TASK.md 배경분석 (2) 재현 명령)를 baseline·재생성 양쪽에 적용해 비율 비교 | 없음(단 baseline 자체가 코드펜스 1쌍뿐이라 감소 여지가 거의 없음 — 천장 효과) |
| AC-G4 | §7 Q2 재현 스크립트를 ANALYSIS.md·PLAN.md 쌍에 적용해 매칭 수를 baseline 쌍과 비교 | **PLAN.md가 baseline·재생성 양쪽에 존재해야 함** — 본 태스크는 아직 PLAN 단계 진입 전이라 baseline PLAN.md 자체가 없다 |

**5. 측정 가능 여부 — 조건부 가능(현재 설계로는 2/4 항목 불가)**: 억지로 4개 전부 가능하다고 쓰지 않는다.
- AC-G2·AC-G3: 지금도 형식적으로 실행 가능하나 천장 효과로 해석력이 약하다.
- AC-G1: R-10 GREEN 완료 전에는 `승계` verdict가 존재하지 않아 **측정 불가**(R-12 서술에 이 선행조건이 명시돼 있지 않다) / AC-G4: baseline PLAN.md가 없어 **현재 측정 불가** — TASK.md R-12 "무엇을"이 "ANALYSIS를 1회 재생성"만 명시하고 PLAN.md 재생성을 언급하지 않아 AC-G4 요구사항과 실행 범위가 어긋난다.
- **대안**: (a) PLAN 단계에서 R-12 범위를 "ANALYSIS+PLAN 2개 재생성"으로 명시 확장(사용자 승인 필요) (b) AC-G1 측정을 R-10 GREEN 확인 이후로 EXECUTE 체크리스트에 선행조건 배선 (c) 이번 회차는 AC-G2·G3만 실측하고 AC-G1·G4는 "측정 불가(선행조건 미충족)"로 DONE.md에 그대로 명시.

## 다음 단계 입력 — PLAN이 재조사 없이 쓸 수 있는 확정값

핸드오프 계약은 "재조사 없이 그대로 쓸 값"이다(B-5) — 아직 PLAN의 설계 판단이 남은 항목은 별도 표로 분리하고, 확정값 표에는 섞지 않는다.

### 확정값

| 항목 | 확정값 | 근거 |
|------|--------|------|
| analysis-core.md 신규 저술 항목 | "지식 선조회 3단"·"델타 탐색 규율"·"증분 소비(ANALYSIS 측)" 3개는 이관 대상 없이 신규 작성 | §7 Q1 |
| analysis-core.md 이관 항목 | "분석 깊이 기준"(`opal/skills/op-dev-analysis/references/analysis-guide.md:46-65`)·"의존성/영향범위"(`opal/skills/op-dev-analysis/references/analysis-guide.md:32-37,114-134`)·"품질 체크리스트"(`opal/skills/op-dev-analysis/SKILL.md:166-179`+`opal/skills/op-dev-analysis/references/analysis-guide.md:146-163` 통합)·"6영역 축"(`opal/skills/op-dev-plan/references/plan-guide.md:90-98`에서 이관) | §7 Q1 |
| tech-context-guide.md 처리 | analysis-core.md 이관 대상 아님, R-3(MCP)·R-4(§6 템플릿)만 독자 개정 | §7 Q1, §4-2 |
| 4파일 교차 중복 baseline(R-9) | 정규화 후 20자 이상 완전 일치 **6건**(`opal/skills/op-dev-analysis/SKILL.md:20`↔`opal/skills/op-dev-plan/references/plan-guide.md:11` 1건 + `opal/skills/op-dev-analysis/SKILL.md:170-176`↔`opal/skills/op-dev-analysis/references/analysis-guide.md:151-162` 5건) — `plan-guide.md`와 `analysis-guide.md`/`tech-context-guide.md` 간 정확 일치는 0건 | §7 Q2 |
| evidence-check 확장 **제약**(확정) | `_locate_clarification_table`은 표 전용이라 `## 확정된 설계 방향`(불릿) 파싱에 재사용 **불가** — 이것은 현행 코드가 강제하는 사실이다 | §7 Q3·Q4 |
| evidence-check 확장 **방식**(권고안, 확정 아님) | 형제 함수(불릿 리스트 파서) 신설 후 `_check_evidence_gate`/`cmd_verify`에서 병합 — **설계 확정은 PLAN 소관**(PLAN PD-1이 분리형 반환으로 확정함) | §7 Q3·Q4 |
| R/P 번호 소비자 | `qa-dev-guide.md` + `opal/skills/op-dev-qa/SKILL.md:118-121` 2곳만 동시 갱신 필요(스코프 외 파일 1개 추가) | §7 Q6, H-4 |
| opp/oppd 커버 여부 | `op-task-plan/plan-guide.md`는 별도 파일이라 이번 개정 미적용 — 의도적 배제인지 TASK.md에 미기재 | §7 Q8, H-3 |
| 구현 순서 | §1.1 순서(Tier) 열 — Tier1(analysis-core.md 신설) → Tier2(harness 표·3스킬·plan-guide.md 포인터화, 병렬 가능) → Tier3(qa-dev-guide.md·거울 사본·opd SKILL·pipeline.json, Tier2의 SKILL.md 확정 후) → Tier4(RED 테스트→GREEN 구현) | §1.1, §1.3 |
| install 재배포 리스크 | `state_tool.py` 변경은 배포본(`~/.opal/tools/state-tool/`) 재배포 전까지 워커에 미반영 — TASK.md 범위가 배포 실행을 제외 | §3.3, H-6 |

### PLAN 결정 필요 (재조사는 불필요하나 설계 판단 남음)

| 항목 | 쟁점 | 근거 |
|------|------|------|
| confirmed_ratio 분모 | 현재 명확화결과 4요소 한정(`len(items)`, `opal/tools/state-tool/state_tool.py:2554`) — `## 확정된 설계 방향` 항목 병합 시 단일 ratio로 합칠지, 두 ratio(명확화결과/확정방향)로 분리 반환할지 PLAN이 결정 | §7 Q4, H-2 |
| harness 모듈 표 "해당 §" | `모듈\|파일\|로드 시점\|해당 §` 4열 중 "해당 §"에 대응할 opal-harness.md 기존 절이 없음 — 신규 stub 절 번호를 신설할지, 빈 값/기존 절 재사용으로 처리할지 PLAN이 결정 | §7 Q7, H-5 |
| pipeline.json checklist 정확한 문구 | 스키마 제약(비어있지 않은 문자열 배열)과 선례 스타일(섹션 포인터/조건 서술)은 확정됐으나, `analysis.pm_gate.checklist`에 넣을 **구체적 항목 문구**는 Tier2 SKILL.md 확정 입력 판정표 최종 형식이 정해진 뒤 PLAN이 확정 | §7 Q5 |
| MUST 트리거 잔존 판정 | `opal/skills/op-dev-analysis/SKILL.md:20`↔`opal/skills/op-dev-plan/references/plan-guide.md:11`(citation-rules 트리거 관용구, 20자 이상 완전 일치 1건)이 analysis-core.md 신설 후에도 남는다 — 이것이 R-9 AC("20자 이상 일치 문장 0건") 위반으로 간주되는지, SSOT+Trigger 관용구 예외로 허용되는지 PLAN이 판단 | §7 Q2 |
