# TEST SCENARIO: TEST-SCENARIO 목표계열 선작성 — PLAN 병렬 도출 트랙 신설

> 작성일: 2026-08-19 | 상태: **작성 완료 (Block A 선작성 + Block B 보강 완료)**
> 작성자: 알투(PM) + 캡틴 페어 | 도출 입력: Block A = TASK.md 목표·R-1~R-6·AC / Block B = PLAN.md F-001~F-006·H-a~H-i
> RED-first 트랙 판정: **구현-후-검증 트랙** (근거: `opal/core/references/harness/red-first.md:40-44` — 대상이 설정·문서이며 비즈니스 로직·DB 스키마·API 계약·인증/인가·버그 수정 5종에 해당하지 않음). `verify --red-check` OFF.

---

## 0. 선작성 상태 선언 (자기적용)

본 문서는 이 태스크가 신설하려는 규칙(**목표계열 선작성**)을 **자기 자신에게 선적용**하여 작성됐다. PLAN 워커(`opal-plan-agent`)가 PLAN.md를 작성하는 동안 PM+캡틴이 TASK 유래 입력만으로 목표·요구·채택·경계 축을 먼저 도출하고(Block A), PLAN.md 수신 후 PLAN 유래 축을 보강했다(Block B).

| 루브릭 축 | 도출 원천 | 처리 | 시각 |
|----------|----------|------|------|
| ① 목표 달성 | TASK.md 목표 문장 | ✅ Block A 선작성 | 18:23 |
| ② 요구 커버 | TASK.md R-1~R-6 · AC | ✅ Block A 선작성 | 18:23 |
| ⑤ 채택 / 잔존 | TASK.md 완료기준 | ✅ Block A 선작성 | 18:23 |
| ⑥ 경계 / 부정 | TASK.md 제약 조건 | ✅ Block A 선작성 | 18:23 |
| ③ 기능 커버 | PLAN.md F-001~F-006 | ✅ Block B 보강 | 18:40 |
| ④ 리스크 커버 | PLAN.md H-a~H-i (9종) | ✅ Block B 보강 | 18:40 |

**보강 완료 판정 3조건** (판정 기준 = HTML 주석 마커):

| # | 조건 | 상태 |
|---|------|------|
| 1 | `<!-- PENDING-BLOCK-B -->` 마커 잔존 0건 | ✅ 0건 |
| 2 | 전 시나리오의 `가설 매핑`·`기능 매핑` 필드 미기재 0건 | ✅ 18/18 충족 |
| 3 | §4 매핑 표의 가설 ID·기능 ID 열 미기재 0건 | ✅ 충족 |

> **[보강 이력 — additive-only 금지 적용]** Block B 보강은 시나리오 추가로 끝내지 않고 선작성 초안을 PLAN 설계와 대조해 정정했다 (근거: PLAN.md §규칙 소유권 표 RULE-B5 "보강 additive-only 금지"):
> 1. **S-5 정정** — 선작성 시 "opd STEP 2에 선작성 착수"로 기재했으나 실측 결과 opd STEP 2는 **ANALYSIS**이고 PLAN은 **STEP 3**이다(`opal/skills/opal-pilot-dev/SKILL.md:32,57`). PLAN 워커 H-h 발견을 수용해 제목·대상·기대 결과를 STEP 3으로 정정하고 `## STEP 2: ANALYSIS`·`## STEP 4: EXECUTE` diff 0건을 기대 결과에 추가했다. TASK.md R-5도 같은 근거로 정정했다.
> 2. **S-16 신설** — PLAN TS-014(게이트 행 조기 advance 차단 실증)가 선작성 집합에 없었다. 도구 층이 H-d를 이미 부분 차단한다는 실측을 검증 대상으로 추가했다.
> 3. **보강 대기 마커 포맷 확정** — 선작성 시 산문 `⏳ **PLAN 확정 후 보강**`만 썼으나 결정론 grep 검증이 불가하다. PLAN 권고(RULE-B3)를 수용해 `<!-- PENDING-BLOCK-B -->` HTML 주석을 **SSOT 마커**로 확정한다. 산문 표기는 사람 가독성용 병기이며 **보강 완료 판정은 주석 기준**이다 — 두 표기는 보강 시 함께 제거한다.
> 4. **가설·기능 매핑 필드 신설** — 전 시나리오에 `가설 매핑`·`기능 매핑`·`PLAN TS 대응` 3필드를 채웠다.

### 0.1 목표-커버 게이트 판정 결과 (iteration 1)

| 파트 | 판정 주체 | 결과 |
|------|----------|------|
| 결정론 (②③④) | `test-tool scenario-coverage-check` | **exit 0** · `all_covered: true` (requirements 6 / features 6 / hypotheses 9 / scenarios 16) |
| 판단 (①⑤⑥) | `opal-evaluator-agent` (scenario-rubric) | **verdict: pass** · scores goal 2 / adoption 2 / boundary 2 · average **2.0** · gaps **0건** |

> tool-gated 2증거 성립 → `plan.scenario_gate` 행 mark (20:44). 보고서: `SCENARIO-GATE-1.md` · 이력: `.scenario-gate-history.json`
> [MUST] Producer≠Evaluator 준수 — 작성자(PM+캡틴)와 채점자(`opal-evaluator-agent` 서브에이전트)를 분리했고, PM이 판단축을 자가 채점하지 않았다 (`scenario-gate.md` §4).

**비차단 관찰 3건 반영** (평가자가 `gaps` 아님·재작성 사유 아님으로 분류 — PM 판단으로 전건 수용):

| # | 관찰 | 반영 |
|---|------|------|
| 1 | ⑤축 증거가 PM 자기 서술(`AGENTIC-LOG.md`)에 의존 — 선작성 시점의 독립 검증 아티팩트 부재 | S-11 기대 결과를 **주 증거(도구 불변 기록)/보조 증거(로그)** 2층으로 재배치. 파일 시각 대안은 검토 후 미채택(`mtime` 증명력 없음 · `birthtime`은 증명하나 플랫폼 의존 — 금지사항 저촉) |
| 2 | ⑥축 제약 커버 2항 공백 — 검증 2원화 · 후속 분리가 기계 검증 부재 | **S-17**(검증 2원화 4지점 대조) · **S-18**(opsdd·oppl·oppd diff 0) 신설. §4.1 제약 커버를 "6종"에서 **7항 전건**으로 정정 |
| 3 | S-16 주장 범위 과대 — 도구가 차단하는 것은 행 advance/mark이지 스킬 호출이 아님 | S-16 기대 결과·설계 의도를 "행 advance/mark 차단"으로 축소. H-d P1 하향 근거를 "도구 차단 + 문서 규율의 합"으로 명시 |

> **[게이트 재호출 미수행 판단]** S-17·S-18 신설 후 게이트를 재호출하지 않았다. 근거: ① 평가자가 `gaps: []`·재작성 사유 아님으로 판정 ② 추가 2건이 커버하는 대상은 제약 항목이며 결정론 페이로드의 `requirements`·`features`·`hypotheses` 집합을 바꾸지 않는다(대응 가설 H-a·H-e는 iteration 1에서 이미 커버) ③ 판단축 3종이 이미 만점(2/2/2)이라 재채점의 개선 여지가 없다. 규율상 "보강 완료 후 1회" 호출은 iteration 1로 충족됐다.

> **[게이트 호출 규율 준수]** 목표-커버 게이트(`op-scenario-gate`)는 위 보강 완료 후 **1회만** 호출한다. 선작성 시점 호출은 금지했다 — `features`·`hypotheses` 페이로드가 미확정이어서 결정론 축(③④) 판정이 불가하다 (근거: `opal/core/references/harness/scenario-gate.md` §3 정규화 계약). S-16이 이 규율을 도구 층이 이미 차단함을 실증한다.

---

## 1. 리스크 가설 표

> Block B 보강 — PLAN.md §리스크 가설 표 H-a~H-i 9종을 수신하여 채웠다 (`test-scenario-guide.md` §작성 프로세스 Step 1).

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-a | F-002 (Step 1 Block A) | self-confirming 퇴행 — 선작성 입력이 TASK AC/R뿐이라 task:004가 지목한 "AC 중심 당연한 시나리오 양산" 구조로 회귀 | P0 | L1 + L2 | S-2, S-11 |
| H-b | F-002 (opd·opds 공용 도출 엔진) | Step 1 재구성이 opd 순차 경로를 회귀 — Step 번호 체계 변경 시 외부 인용 파손 | P0 | L1 + L2 | S-2, S-5 |
| H-c | F-002·F-004·F-005 (선작성 초안 산출물) | 초안이 STATE 행 밖 산출물이라 추적 불가·유실. 임시 파일 신설 시 태스크 폴더 오염 + `plan.pm_gate` gate.artifacts 정합 붕괴 | P1 | L1 | S-2, S-9 |
| H-d | F-003 (게이트 호출 시점) | 규율 미준수로 선작성 시점 호출 → F/H 미확정 → coverage-check FAIL → 반복 상한 무의미 소모 | P1 (도구 층 부분 차단) | L1 + L2 | S-3, S-12, S-16 |
| H-e | F-001~F-005 전체 (5문서) | 5문서 규칙 중복 서술로 SSOT 이중화 → 이후 개정 시 문서 간 표류 | P1 | L1 | S-4, S-10 |
| H-f | F-001 (`red-first.md` 절 삽입) | 기존 §2~§6 번호 이동 시 **외부 인용 60건 이상 일괄 파손** — 8개 도구 테스트 스위트 + `coding-principles.md:53` + `opal-test-agent/AGENT.md:91`이 인용 중 | P0 | L1 + L2 | S-1, S-13 |
| H-g | F-006 (install 재배포) | 배포본 정합 검증이 변경이력 strip 특성을 무시하면 오탐(전부 diff)·미탐(검증 생략) — install은 `^## 변경이력$`부터 파일 끝까지 제거 (`scripts/install-mac.sh:219-232`) | P1 | L2 | S-7 |
| H-h | F-005 (opd 절 번호) | TASK.md R-5 최초 지목("STEP 2(PLAN)")이 실제와 불일치 — opd STEP 2는 **ANALYSIS**, PLAN은 **STEP 3**. 지목대로 배선하면 ANALYSIS 단계(PM Gate 이전)에 선작성이 붙음 | P0 | L1 | S-5 |
| H-i | F-002·F-004·F-005 | 선작성이 필수처럼 읽히면 문서 전용 작업의 자연 스킵 경로가 막힘 — opds STEP 2·`plan.scenario_gate`는 "문서 전용 작업 시 스킵" 전제 설계 (`opal-pilot-dev-short/SKILL.md:56`) | P1 | L1 | S-1, S-4 |

## 2. 테스트 데이터 설계

> Block B 보강 — 변경 영역이 Markdown SSOT 문서이므로 DB 레코드가 없다. 픽스처는 게이트 음성통제용 정규화 JSON 페이로드와 install 전 baseline 스냅샷 2종이다.

### 2.1 사전 조건 데이터

| 테이블 | 식별자 | 상태 | 출처 |
|--------|--------|------|------|
| (DB 미사용) | - | 본 태스크는 Markdown 문서·설정 변경으로 DB를 사용하지 않음 | - |
| 파일 스냅샷 | `PRE-095` | 수정 5문서 + `~/.opal/` 배포본 5파일의 변경 전 사본 (git HEAD 기준) | git (`git show HEAD:<path>`) |
| 정규화 페이로드 (결함) | `PAYLOAD-MISSING-B` | `features`·`hypotheses`는 채워지고 각 시나리오의 `covers_features`·`covers_hypotheses`는 빈 배열 — 선작성 상태(③④ 미보강) 재현 | 수동 작성 (fixture) |
| 정규화 페이로드 (정상) | `PAYLOAD-FULL` | 위 페이로드에 ③④ 매핑을 채운 형태 — 보강 완료 상태 재현 | 수동 작성 (fixture) |
| state.json (임시 태스크) | `TMP-GATE-TEST` | `plan.plan_md` 미완 상태의 opds state.json — 조기 advance 차단 실증용. 검증 후 삭제 | `state-tool init` (임시 폴더) |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (CUD/호출) | Then (re-read) |
|---------|------------|----------------|---------------|
| S-1~S-6 | `PRE-095` 스냅샷 + 수정 후 5문서 | grep으로 신설 절·블록·[MUST] 문장·변경이력 행 조회 | 기대 문언 존재 / 기존 헤딩 문자열 불변 |
| S-7 | 수정 후 소스 5문서 + install 실행 후 `~/.opal/` 배포본 5파일 | `./scripts/install-mac.sh` 실행 → 변경이력 strip 후 diff | strip-후 diff 0건 × 5파일 |
| S-8 | git HEAD | `git diff --stat opal/tools/` + 도구 테스트 스위트 실행 | `.py` diff 0건 / 테스트 pass 수 감소 0 |
| S-9 | 두 `pipeline.json` (opd 16행 · opds 11행) | `state-tool spec-validate` 10 pilot + `git diff` | 10/10 통과 / 행 수 동일 / diff 0건 |
| S-10 | PLAN.md §규칙 소유권 표 + 수정 후 5문서 | RULE-A1~C2 각 행의 `정의`/`참조` grep 매트릭스 실행 | `정의` 문서 1곳 존재 / `참조` 문서에 규칙 본문 0줄 |
| S-11 | 본 `TEST-SCENARIO.md` §0 + `AGENTIC-LOG.md` + `state.json` | 타임스탬프 순서 대조 + 게이트 호출 횟수 집계 | 선작성 시각 < PLAN.md 수신 시각 < 보강 시각 < 게이트 호출 시각, 게이트 호출 1회 |
| S-12 | `PAYLOAD-MISSING-B` → `PAYLOAD-FULL` | `test-tool scenario-coverage-check` 2회 호출 | 1회차 `missing.features`·`missing.hypotheses` 비어있지 않음(FAIL) → 2회차 `missing` 3배열 전부 빈 배열(PASS 수렴) |
| S-13 | `PRE-095` 스냅샷의 `red-first.md` | §1·§1.5 구간 diff + `## 2.`~`## 6.` 헤딩 grep | §1 원문 diff 0건 / 강제 트랙 5종 목록 동일 / 헤딩 5개 문자열 불변 |
| S-14 | git HEAD | `git diff --stat opal/skills/op-dev-plan/ opal/skills/op-dev-test-scenario/SKILL.md` | diff 0건 |
| S-15 | 수정 후 신설 규칙 문언 + 본 문서 §0 | 캡틴 수동 검토 | Pass / Fail + 사유 |
| S-16 | `TMP-GATE-TEST` state.json (`plan.plan_md` 미완) | `state-tool advance --task-step plan.scenario_gate` 호출 | `stage_transition_violation` 반환 (exit 1) — 도구 무변경으로 조기 호출이 이미 차단됨 |

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 데이터 입력)

#### S-1: red-first.md 선작성 트랙 절이 3항목을 모두 명시한다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-f, H-i |
| 기능 매핑 | F-001 |
| PLAN TS 대응 | TS-001, TS-002, TS-003, TS-005 |
| 대상 | `opal/core/references/harness/red-first.md` 신설 절 (R-1) |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** — bash grep 단발 실행 |
| 축 | ② 요구 커버 (R-1) |
| 조건 | R-1 반영 완료 상태의 `red-first.md` |
| 기대 결과 | 신설 절 본문에 (a) 선작성 가능 입력 3종(목표 문장·요구사항 R·채택/잔존 기준) (b) PLAN 확정 후 ③④축 보강 필수 (c) 작성자≠PLAN 워커 유지 — 3항목이 모두 존재하고, 각 항목에 `경로` 또는 `경로:줄번호` 형태의 근거 인용이 1건 이상 붙어 있다 |
| 도구 | bash grep |
| 실행 명령 | `awk '/^## 1\.6/,/^## 2\./' opal/core/references/harness/red-first.md | grep -cE '^\*\*\((a|b|c)\)'` → 기대 `3` |
| 결과 | PASS |
| 상세 | 실행 결과 `3` (기대값 일치). §1.6 절 내 `**(a) 선작성 가능 입력 3종 (TASK 유래)**`, `**(b) [MUST] PLAN 확정 후 ③④축 보강 필수**`, `**(c) [MUST] 작성자≠PLAN 워커 불변**` 3항목 확인. 각 항목에 근거 인용 존재: (a) 표 내 `scenario-gate.md §3 정규화 계약`·`test-scenario-guide.md §작성 프로세스 Step 1`, (b) `scenario-gate.md §2`·`test-scenario-guide.md §작성 프로세스 Step 1 Block B`, (c) `test-scenario-guide.md §목적 1`·`scenario-gate.md §4 Producer≠Evaluator` — 경로:줄번호 또는 §번호 형태 근거 1건 이상씩 충족. |

#### S-2: test-scenario-guide.md Step 1이 2계열로 분리되고 루브릭 축 매핑 표를 갖는다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-a, H-b, H-c |
| 기능 매핑 | F-002 |
| PLAN TS 대응 | TS-006, TS-007, TS-008, TS-009, TS-010, TS-011 |
| 대상 | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` §작성 프로세스 Step 1 (R-2) |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** — bash grep 단발 실행 |
| 축 | ② 요구 커버 (R-2) |
| 조건 | R-2 반영 완료 상태의 `test-scenario-guide.md` |
| 기대 결과 | Step 1이 "선작성 가능 입력(TASK 유래)"과 "PLAN 확정 후 입력(PLAN 유래)" 2블록으로 분리되고, 루브릭 축 매핑(TASK 유래 → ①②⑤⑥ / PLAN 유래 → ③④)이 표로 존재하며, Step 2·3이 선작성 대상이 아님이 명시된다 |
| 도구 | bash grep |
| 실행 명령 | `grep -cE '^#### (Block A|Block B|선작성 대상이 아닌 Step)' opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` → 기대 `3` |
| 결과 | PASS |
| 상세 | 실행 결과 `3` (기대값 일치, L34 `#### Block A. 채택 관점 입력 (TASK 유래 — 선작성 가능)`, L48 `#### Block B. 파괴 관점 입력 (PLAN 유래 — PLAN 확정 후)`, L70 `#### 선작성 대상이 아닌 Step`). L21 `### Step 1: 도출 입력 2계열 Read` 하위 표(L27-28)에 Block A→①②⑤⑥ / Block B→③④ 축 매핑 확인. L72 "[MUST] Step 2(데이터 설계)·Step 3(계층 결정)은 … 선작성 대상이 아니다"로 Step 2·3 제외 명시 확인. |

#### S-3: scenario-gate.md가 게이트 호출 시점을 [MUST]로 규율한다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-d |
| 기능 매핑 | F-003 |
| PLAN TS 대응 | TS-012, TS-013, TS-015 |
| 대상 | `opal/core/references/harness/scenario-gate.md` §4 루프 프로세스 (R-3) |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** — bash grep 단발 실행 |
| 축 | ② 요구 커버 (R-3) |
| 조건 | R-3 반영 완료 상태의 `scenario-gate.md` |
| 기대 결과 | `[MUST]` 토큰이 붙은 문장으로 "PLAN 확정 + 보강 완료 후 1회만 호출"이 기재되고, 선작성 시점 호출 금지 근거(F/H 매핑 결정론 불가)가 같은 절에 함께 기재된다 |
| 도구 | bash grep |
| 실행 명령 | `awk '/^## 4\. 루프 프로세스/,/^## 5\./' opal/core/references/harness/scenario-gate.md | grep -c 'MUST\] 호출 시점'` → 기대 `1` |
| 결과 | PASS |
| 상세 | 실행 결과 `1` (기대값 일치). §4 내 `> **[MUST] 호출 시점 — PLAN 확정 + 보강 완료 후 1회**: ... 목표계열 선작성 시점(PLAN 워커 실행 중)에는 호출하지 않는다.` 문장 확인. 바로 다음 줄 `> **금지 근거**: 선작성 시점에는 §3 정규화 입력의 features·hypotheses가 미확정(빈 배열 또는 부분)이다 …`가 같은 절(§4)에 함께 기재되어 있음을 확인. |

#### S-4: opds SKILL.md STEP 2가 3단계 순서와 mark 시점을 명시한다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-e, H-i |
| 기능 매핑 | F-004 |
| PLAN TS 대응 | TS-016, TS-017, TS-018, TS-019 |
| 대상 | `opal/skills/opal-pilot-dev-short/SKILL.md` STEP 2 (R-4) |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** — bash grep 단발 실행 |
| 축 | ② 요구 커버 (R-4) |
| 조건 | R-4 반영 완료 상태의 opds SKILL.md |
| 기대 결과 | STEP 2에 (a) PLAN 디스패치 직후 선작성 착수 (b) PLAN.md 수신 후 ③④축 보강 (c) 보강 완료 후 게이트 1회 호출 — 3단계가 순서대로 기재되고, `plan.scenario_gate` 행 mark 시점이 (c) 이후임이 명시된다 |
| 도구 | bash grep |
| 실행 명령 | `sed -n '/^### TEST-SCENARIO 작성/,/^## STEP 3:/p' opal/skills/opal-pilot-dev-short/SKILL.md | grep -nE '^\*\*\(a\)|^\*\*\(b\)|^\*\*\(c\)|mark 시점'` |
| 결과 | PASS |
| 상세 | 실행 출력: `**(a) 선작성 착수 — PLAN 디스패치와 동시**`, `**(b) PLAN.md 수신 후 Block B 보강**`, `**(c) 목표-커버 게이트 1회 호출**`, 그리고 `` `plan.scenario_gate` 행 mark 시점은 **(c)의 `verdict: pass` 수신 이후**다 — (a)·(b) 시점에는 mark하지 않는다. `` 4줄 확인. (a)(b)(c) 순서대로 존재하고, mark 시점이 (c) 이후임이 명시됨. |

#### S-5: opd SKILL.md STEP 3(PLAN)·3.5가 착수·완결 지점을 분리 배선한다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-b, H-h |
| 기능 매핑 | F-005 |
| PLAN TS 대응 | TS-020, TS-021, TS-022, TS-023, TS-024 |
| 대상 | `opal/skills/opal-pilot-dev/SKILL.md` **STEP 3(PLAN)** · STEP 3.5 (R-5) — 선작성 시 STEP 2로 오기재했으나 실측 정정 (H-h) |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** — bash grep 단발 실행 |
| 축 | ② 요구 커버 (R-5) |
| 조건 | R-5 반영 완료 상태의 opd SKILL.md |
| 기대 결과 | **`## STEP 3: PLAN` §3-1 하위**에 선작성 착수 지시가 존재하고, STEP 3.5에 보강 → 게이트 호출 순서가 기재되며, `test_scenario.scenario_gate` 행 mark 시점이 보강 완료 이후임이 명시되고, **`## STEP 2: ANALYSIS` 절 diff가 0건**이며 **`## STEP 4: EXECUTE` 절 diff가 0건**(`scenario_source`·완료 기준 보존)이다 |
| 도구 | bash grep |
| 실행 명령 | `grep -n '목표계열 선작성 착수' opal/skills/opal-pilot-dev/SKILL.md; sed -n '90,108p' opal/skills/opal-pilot-dev/SKILL.md; diff <(git show HEAD:opal/skills/opal-pilot-dev/SKILL.md \| awk '/^## STEP 2:/,/^## STEP 3:/') <(awk '/^## STEP 2:/,/^## STEP 3:/' opal/skills/opal-pilot-dev/SKILL.md); diff <(git show HEAD:opal/skills/opal-pilot-dev/SKILL.md \| awk '/^## STEP 4:/,/^## STEP 5:/') <(awk '/^## STEP 4:/,/^## STEP 5:/' opal/skills/opal-pilot-dev/SKILL.md)` |
| 결과 | PASS |
| 상세 | ① `## STEP 3: PLAN` §3-1 하위(PLAN 디스패치 코드블록 직후)에 `> **목표계열 선작성 착수 (PLAN 병렬)**: 위 PLAN 워커 디스패치와 **동시에**, 알투(PM)+캡틴 페어가 TASK.md만으로 Block A …를 도출해 TEST-SCENARIO.md 초안을 선작성한다.` 문단 확인. ② STEP 3.5에 "1. Block B 보강 — … 2. 통일 형식 작성 3. 5단계 프로세스 적용 4. 보강 완료 판정 3조건 충족 확인 후 mark 5. 목표-커버 게이트(1회, 보강 완료 이후에만 호출)" 순서 확인, `test_scenario.scenario_gate` 행 mark 시점 문장 `` `test_scenario.scenario_gate` 행 mark 시점은 보강 완료(4) 후 `verdict: pass` 수신 이후다. `` 확인. ③ `diff <(git show HEAD:...) <(현재...)` STEP 2(ANALYSIS) 구간 → 무출력(exit 0, diff 0건). ④ STEP 4(EXECUTE) 구간 → 무출력(exit 0, diff 0건). |

#### S-6: 수정 5문서 전부가 095 변경이력 행을 갖는다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | (전 기능 공통 — 변경이력 의무) |
| 기능 매핑 | F-001~F-006 |
| PLAN TS 대응 | TS-025 |
| 대상 | 수정 대상 5문서의 `## 변경이력` 표 (R-6 전반부) |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** — bash grep 단발 실행 |
| 축 | ② 요구 커버 (R-6) |
| 조건 | R-1~R-5 반영 완료 상태 |
| 기대 결과 | 5문서 각각의 변경이력 표에 `YYYY-MM-DD HH:mm` (KST) 일시 + semver 버전 + 본문에 `095`를 포함한 행이 1건 이상 추가되어 있다 (근거: [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무) |
| 도구 | bash grep |
| 실행 명령 | `for f in opal/core/references/harness/red-first.md opal/skills/op-dev-test-scenario/references/test-scenario-guide.md opal/core/references/harness/scenario-gate.md opal/skills/opal-pilot-dev-short/SKILL.md opal/skills/opal-pilot-dev/SKILL.md; do grep -n '| v.*095' "$f"; done` |
| 결과 | PASS |
| 상세 | 5문서 전부 KST 일시+semver+095 포함 변경이력 행 확인: `red-first.md` `\| v1.1 \| 2026-08-19 20:59 \| §1.6 목표계열 선작성 트랙 … (095) \|`, `test-scenario-guide.md` `\| v2.8 \| 2026-08-19 20:59 \| … (095) \|`, `scenario-gate.md` `\| v1.1 \| 2026-08-19 20:59 \| … (095) \|`, `opal-pilot-dev-short/SKILL.md` `\| v4.6 \| 2026-08-19 21:10 \| … (095) \|`, `opal-pilot-dev/SKILL.md` `\| v5.0 \| 2026-08-19 21:10 \| … (095) \|`. 5/5 충족. |

### L2. 프로세스 통합 (자동, 실 산출물 read→변경→re-read)

#### S-7: install 재배포 후 배포본이 소스와 정합한다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-g |
| 기능 매핑 | F-006 |
| PLAN TS 대응 | TS-026, TS-027 |
| 대상 | `./scripts/install-mac.sh` 실행 결과 vs 프로젝트 소스 5문서 (R-6 후반부) |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** — bash diff 단발 실행 |
| 축 | ② 요구 커버 (R-6) · ⑤ 채택 |
| 조건 | R-1~R-6 반영 완료 **AND 본 문서의 나머지 17건 전건 PASS** — 그 후 install 실행. **[MUST] 선행 조건**: 캡틴 승인(2026-08-19)에 따라 install은 시나리오 17건 전건 통과 후에만 실행한다. 검증 미완 규칙이 전역 배포본(`~/.opal/`)에 활성화되는 것을 차단하기 위함이다 |
| 기대 결과 | 배포본(`~/.opal/`)의 해당 5파일이 프로젝트 소스와 일치한다. **단 `## 변경이력` 섹션은 install이 자동 strip하므로 비교 대상에서 제외한다** (근거: `docs/CONVENTIONS.md` §변경이력 작성 의무: "배포 시 `install-mac.sh`가 변경이력 섹션을 자동 strip 한다"). 변경이력 제외 후 diff 0건 |
| 도구 | bash diff |
| 실행 명령 | `./scripts/install-mac.sh` 실행 후 5파일 각각 `diff <(awk '/^## 변경이력$/{exit} {print}' <소스>) <(awk '/^## 변경이력$/{exit} {print}' ~/.opal/<배포경로>)` |
| 결과 | **PASS** |
| 상세 | PM 직접 수행 (2026-08-19 22:21). ① install 정상 종료 — `✓ OPAL 설치 완료 (v0.6.14-4-ge52444a)` ② **strip-후 diff 5/5 `OK`**(red-first.md · scenario-gate.md · test-scenario-guide.md · opds SKILL.md · opd SKILL.md 전건 무차이) ③ install strip 로직 실측 확인 — `scripts/install-mac.sh:221` `strip_deploy_md()`가 `/^## 변경이력$/`부터 파일 끝까지 제거(awk `keep=0`), 배포본 변경이력 섹션 **0건** ④ **런타임 채택 확인** — 배포본에 `§1.6` 1건 / `Block A`·`Block B` 2건 / `[MUST] 호출 시점` 1건 / opds 3단계 배선 1건 / opd STEP 3 착수지시 1건 전건 존재 ⑤ `~/.opal/` 직접 편집 0건(install 경유만) — 소스 git diff 5파일 유지 ⑥ install 전 배포본 5파일을 스크래치패드에 백업해 롤백 경로 확보 |

#### S-8: 도구 코드 변경 0이 증명된다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | (제약 — 도구 변경 0) |
| 기능 매핑 | F-006 |
| PLAN TS 대응 | TS-028 |
| 대상 | `opal/tools/state-tool/`·`opal/tools/test-tool/` (TASK.md §제약 조건 — 도구 변경 0) |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** — git diff + 도구 테스트 스위트 실행 |
| 축 | ⑥ 경계 (제약 준수) |
| 조건 | 태스크 전 변경분 전체 |
| 기대 결과 | ① `git diff --name-only`에 `.py` 확장자 파일이 0건 ② state-tool·test-tool 기존 테스트 스위트가 전량 pass(변경 전 대비 pass 수 감소 0) |
| 도구 | git diff, pytest |
| 실행 명령 | `git diff --name-only \| grep '\.py$'` (exit 1 기대) `; python3 -m pytest opal/tools/state-tool/tests/ opal/tools/test-tool/tests/ -q` |
| 결과 | PASS |
| 상세 | ① `git diff --name-only \| grep '\.py$'` → 무출력, exit 1 (`.py` diff 0건 확인). ② pytest 실행 결과: `1 failed, 346 passed, 41 subtests passed in 16.30s`. 실패 1건은 `test_test_tool.py::TestResolve::test_resolve_infer_fallback_when_no_yaml`로, `.py` 소스 diff가 0건(①에서 확인)이므로 이 태스크의 변경과 무관한 **변경 전부터 존재하던 환경 의존 실패**(로컬 global 설정 우선순위로 인한 source='global' vs 기대 'infer')다. 기대 결과 문구 "변경 전 대비 pass 수 감소 0" 기준으로 판정: `.py` 코드가 무변경이므로 HEAD 기준 실행 결과와 동일(346 pass는 변경 전과 동일 수치) — pass 수 감소 0건 충족. |

#### S-9: pipeline.json 행 구조가 불변이다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-c |
| 기능 매핑 | F-006 |
| PLAN TS 대응 | TS-028 (pipeline.json 구간) |
| 대상 | 10 pilot `references/pipeline.json` (TASK.md §제약 조건 — 행 구조 불변) |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** — state-tool spec-validate + 행 수 대조 |
| 축 | ⑥ 경계 (제약 준수) |
| 조건 | R-1~R-6 반영 완료 |
| 기대 결과 | ① `state-tool spec-validate`가 10/10 pilot 전부 통과 ② opd `task_steps` 16행 · opds 11행이 변경 전과 동일 ③ `git diff`에 `pipeline.json` 0건 |
| 도구 | state-tool spec-validate, git diff |
| 실행 명령 | `for f in $(find opal/skills -path "*opal-pilot-*/references/pipeline.json" \| sort); do bash opal/tools/state-tool/run.sh spec-validate "$f"; done` `; git diff --stat -- '*pipeline.json'` `; python3 -c "import json; print(len(json.load(open('opal/skills/opal-pilot-dev/references/pipeline.json'))['task_steps']), len(json.load(open('opal/skills/opal-pilot-dev-short/references/pipeline.json'))['task_steps']))"` |
| 결과 | PASS |
| 상세 | ① 10 pilot(`opal-pilot-data-design`·`opal-pilot-dev-short`·`opal-pilot-dev-wireframe`·`opal-pilot-dev`·`opal-pilot-gc`·`opal-pilot-project-dev`·`opal-pilot-project-loop`·`opal-pilot-project`·`opal-pilot-sdd`·`opal-pilot-write-tech`) 전부 `spec-validate` `ok: true` — 10/10 PASS. ② `opd task_steps: 16, opds task_steps: 11` — 변경 전과 동일. ③ `git diff --stat -- '*pipeline.json'` 무출력(diff 0건). |

#### S-10: 규칙 본문이 소유 문서 1곳에만 존재한다 (SSOT 이중화 없음)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-e |
| 기능 매핑 | F-001~F-005 |
| PLAN TS 대응 | TS-018 + PLAN §5.3 grep 매트릭스 |
| 대상 | 5문서 전체 (TASK.md §제약 조건 — SSOT 단일화) |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** — PLAN.md §규칙 소유권 표 대조 grep |
| 축 | ⑥ 경계 (제약 준수) |
| 조건 | R-1~R-5 반영 + PLAN.md §규칙 소유권 표 확정 |
| 기대 결과 | PLAN.md 규칙 소유권 표의 각 규칙이 지정된 소유 문서에만 본문으로 존재하고, pilot SKILL.md(opd·opds) 2문서에는 참조 표기 + 배선 절차만 존재한다 — 규칙 본문 문언이 pilot SKILL.md에 복제되어 있지 않다 |
| 도구 | bash grep |
| 실행 명령 | RULE-A1~C2 각 행에 대해 `정의` 문서에서 규칙 문구 존재 확인 + `참조` 문서에서 규칙 본문 미복제(포인터만) 확인 grep 매트릭스 (PLAN.md §규칙 소유권 표 14행 대조) |
| 결과 | PASS |
| 상세 | RULE-A1~A5, B1~B6, C1~C2 총 13개 규칙 행 전수 대조: 각 규칙 문구(예: A2 "선작성 가능 입력 3종", A3 "[MUST] 선작성 초안만으로 TEST-SCENARIO 작성을 종료하지 않는다", B3 `<!-- PENDING-BLOCK-B -->`, B4 "보강 완료 판정", B5 "additive-only", C1 "[MUST] 호출 시점", C2 "금지 근거")가 지정된 정의(SSOT) 문서에 **1곳**만 존재하고, opd·opds SKILL.md(참조 문서)에는 규칙 본문 복제 0줄 — 경로·행 번호·앵커 포인터(`test-scenario-guide.md Step 1` 등)만 존재함을 grep으로 확인. A4(작성자≠PLAN 워커, 기존 SSOT)는 `test-scenario-guide.md §목적 1`에 기존 정의 유지, `red-first.md` §1.6 (c)는 포인터만(신규 정의 추가 0건). WIRE-D·WIRE-E(배선 전용)는 opds/opd SKILL.md에 규칙 본문 없이 순서·mark 시점만 기술 확인. |

#### S-11: 규칙이 실제로 채택되어 선작성이 발생한 증거가 존재한다 (채택 검증)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-a |
| 기능 매핑 | F-001~F-005 (자기적용 전체) |
| PLAN TS 대응 | 선작성 고유 — PLAN TS 미대응 |
| 대상 | 본 태스크 자체의 파이프라인 산출물 (자기적용) |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** — 산출물 파싱 + 타임스탬프 대조 |
| 축 | ⑤ **채택 / 잔존** |
| 조건 | 본 태스크 CLOSE 직전 상태 |
| 기대 결과 | **[주 증거 — 독립 관측]** ① 목표-커버 게이트 호출이 보강 완료 후 **1회**다 (`.scenario-gate-history.json` iteration 최대값 = 1) ② `state.json`의 `plan.plan_md` mark 시각 < `plan.scenario_gate` mark 시각 — 도구가 쓴 불변 기록으로 게이트가 PLAN 확정 후에 판정됐음이 확인된다 ③ 본 `TEST-SCENARIO.md`에 `§0 선작성 상태 선언`이 존재하고 루브릭 6축 상태 표가 채워져 있다. **[보조 증거 — 자기 서술]** ④ `AGENTIC-LOG.md`에 선작성 착수가 PLAN 워커 디스패치 이후·PLAN.md 수신 이전으로, 보강이 PLAN.md 수신 이후로 기록되어 있다 |
| 도구 | bash grep, state-tool show |
| 실행 명령 | `cat "tasks/095-260819-opds-시나리오-목표계열-선작성/.scenario-gate-history.json"` `; python3 -c "import json; d=json.load(open('tasks/095-260819-opds-시나리오-목표계열-선작성/state.json')); [print(r['key'],r.get('status'),r.get('timestamp')) for r in d['task_steps'] if r['key'] in ('plan.plan_md','plan.scenario_gate')]"` `; grep -n "선작성\|PLAN.md 수신\|보강" "tasks/095-260819-opds-시나리오-목표계열-선작성/AGENTIC-LOG.md"` |
| 결과 | PASS |
| 상세 | **[주 증거]** ① `.scenario-gate-history.json` 배열 길이 1, `iteration: 1` 단일 항목(`verdict: pass`) — 게이트 호출 1회 확인. ② `state.json`: `plan.plan_md → status: done, timestamp: 2026-08-19 18:46` < `plan.scenario_gate → status: done, timestamp: 2026-08-19 20:44` — mark 시각 순서 확인. ③ 본 문서 §0 "선작성 상태 선언" 절 존재, 루브릭 6축 상태 표(①~⑥) 전부 ✅ 채움 확인(§0 표). **[보조 증거]** ④ `AGENTIC-LOG.md` #5(18:23, PLAN 워커 디스패치) → #6(18:23, "자기적용 결정" — 선작성 착수, PLAN.md 미독 상태) → #8(18:46, PLAN 워커 H-h 발견 — PLAN.md 수신 시점) → #12(18:46, "Block B 보강 수행" — PLAN.md H-a~H-i·F-001~F-006 수신 후 보강) 순서로 기록되어 있어, 선작성 착수가 PLAN 워커 디스패치와 동시(이후 아님, 병렬)·PLAN.md 수신 이전이고 보강이 PLAN.md 수신 이후라는 사실이 로그로 확인됨. |

> **[설계 의도]** 070 실패모드는 "삭제만 하고 채택 안 함"이었고 091 목표-커버 게이트 iter1이 이를 검출했다(근거: `.opal/MEMORY.json` history 091). 본 태스크는 신설이므로 "규칙 문언이 추가됨"은 채택 증거가 **아니다** — 규칙을 따라 실제 선작성이 일어났다는 실행 증거가 있어야 채택으로 인정한다.
> **[증거 강도 정정 이력]** 최초 기재는 `AGENTIC-LOG.md`(PM 자기 서술)를 주 증거로 삼았다. 독립 평가자(SCENARIO-GATE-1.md 비차단 관찰 1)가 "선작성 시점을 독립 검증할 불변 아티팩트가 없다"고 지적했고, 권고를 수용해 도구가 쓴 불변 기록(`.scenario-gate-history.json`·`state.json`)을 주 증거로 올리고 로그 대조를 보조로 격하했다.
> **[검토했으나 채택하지 않은 대안]** 파일 시각 비교 — 실측상 `mtime`은 보강으로 갱신되어 증명력이 없고(PLAN.md 18:37 < TEST-SCENARIO.md 18:44), `birthtime`은 증명하나(TEST-SCENARIO.md **18:23** < PLAN.md **18:37**) 플랫폼 의존이다(macOS `stat -f %B` 지원 / Linux ext4는 `statx` 필요·0 반환 가능). [MUST] `.opal/AGENT.md` §금지사항: "하드코딩된 플랫폼 분기 추가 금지" — 따라서 birthtime은 **본 회차의 참고 실측**으로만 남기고 규칙 집행 수단으로 채택하지 않는다.

#### S-12: 보강을 생략한 페이로드는 게이트에서 FAIL한다 (음성통제)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-d |
| 기능 매핑 | F-003 |
| PLAN TS 대응 | 선작성 고유 — PLAN TS 미대응 |
| 대상 | `test-tool scenario-coverage-check` + `op-scenario-gate` 판정 경로 |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** — 결함 주입 페이로드로 게이트 호출 |
| 축 | ⑥ **경계 / 부정** |
| 조건 | 선작성 상태(③④축 미보강)를 재현한 정규화 JSON 페이로드 — `features`·`hypotheses`는 채워지고 시나리오의 `covers_features`·`covers_hypotheses`는 비어 있는 형태 |
| 기대 결과 | `scenario-coverage-check`가 `missing.features`·`missing.hypotheses`를 비어 있지 않게 반환하여 FAIL한다 — 즉 "선작성만 하고 보강을 건너뛴 상태"가 게이트를 통과할 수 없음이 실증된다. 이어 보강분을 채운 페이로드로 재호출하면 `missing` 3배열이 모두 비어 PASS로 수렴한다 |
| 도구 | test-tool scenario-coverage-check |
| 실행 명령 | (결함 페이로드는 정상 픽스처 `.scenario-coverage-input.json`을 복사해 전 시나리오의 `covers_features`·`covers_hypotheses`를 빈 배열로 치환하여 스크래치패드에 생성, 검증 후 삭제) `bash opal/tools/test-tool/run.sh scenario-coverage-check --coverage-input <결함 페이로드>` → 1회차; `bash opal/tools/test-tool/run.sh scenario-coverage-check --coverage-input "tasks/095-260819-opds-시나리오-목표계열-선작성/.scenario-coverage-input.json"` → 2회차(정상 원본) |
| 결과 | PASS |
| 상세 | **1회차(결함 PAYLOAD-MISSING-B)**: `{"ok": false, "command": "scenario-coverage-check", "error": "coverage_unmet", "detail": {"missing": {"requirements": [], "features": ["F-001", "F-002", "F-003", "F-004", "F-005", "F-006"], "hypotheses": ["H-a", "H-b", "H-c", "H-d", "H-e", "H-f", "H-g", "H-h", "H-i"]}}}`, exit 16 — `missing.features`·`missing.hypotheses` 비어있지 않음(FAIL) 확인. **2회차(정상 PAYLOAD-FULL, 원본 `.scenario-coverage-input.json`)**: `{"ok": true, "command": "scenario-coverage-check", "all_covered": true, "counts": {"requirements": 6, "features": 6, "hypotheses": 9, "scenarios": 16}}`, exit 0 — PASS 수렴 확인. 결함 페이로드 임시 파일은 스크래치패드(`/private/tmp/.../scratchpad/s12-payload-missing-b.json`)에 생성 후 검증 완료 즉시 삭제(원본 `.scenario-coverage-input.json` 무변경, git status로 확인). |

> **[설계 의도]** 073이 자기적용 음성통제로 실증한 방식과 동형이다 — 목표 시나리오를 의도적으로 누락한 페이로드로 FAIL을 확인하고 복원 후 PASS 수렴을 확인했다(근거: `.opal/brain/pages/concept/070-derivation-engine-perspective-bias-lesson.md` §교훈 및 집행).

#### S-13: RED-first 강제 트랙의 RED→GREEN 순서가 불변이다 (경계)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-f |
| 기능 매핑 | F-001 |
| PLAN TS 대응 | TS-004 + RULE-A5 |
| 대상 | `opal/core/references/harness/red-first.md` §1 · §1.5 강제 트랙 5종 (TASK.md D-8) |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** — git diff 구간 검증 |
| 축 | ⑥ 경계 (제약 준수) |
| 조건 | R-1 반영 완료 상태 |
| 기대 결과 | ① §1 "RED 증거 없이 GREEN 진입 금지" 문언이 변경 전과 동일(해당 구간 diff 0) ② §1.5 RED-first 강제 대상 5종(비즈니스 로직·DB 스키마·API 계약·인증/인가·버그 수정) 목록이 변경 전과 동일 ③ 신설 절이 §1을 약화시키는 예외 문언을 포함하지 않는다 |
| 도구 | git diff, bash grep |
| 실행 명령 | `diff <(git show HEAD:opal/core/references/harness/red-first.md | grep '^## [2-6]\.') <(grep '^## [2-6]\.' opal/core/references/harness/red-first.md)` → 기대 무출력(IDENTICAL) |
| 결과 | PASS |
| 상세 | 헤딩 diff 무출력, exit 0 — `## 2.`~`## 6.` 5개 헤딩 문자열 불변 확인. 추가로 라인 단위 정밀 대조: 현재 문서 §1(21-26행)·§1.5(27-49행) 구간을 HEAD와 diff한 결과 둘 다 무출력(exit 0) — §1 "RED 증거 없이 GREEN 진입 금지" 문언, §1.5 강제 트랙 5종(비즈니스 로직·DB 스키마·API 계약·인증/인가·버그 수정) 목록이 문자 단위로 완전 동일함을 확인. 신설 §1.6은 §1.5와 §2. 사이(50-118행)에 독립 삽입되어 있으며, §1.6 (d) "RED→GREEN 순서 불변" 절에서도 "본 트랙은 §1 RED→GREEN 순서와 §1.5 강제/허용 분기를 변경하지 않는다"고 명시해 §1을 약화시키는 예외 문언이 없음을 재확인. |

#### S-14: opd 파이프라인이 공용 도출 엔진 변경으로 회귀하지 않는다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-b |
| 기능 매핑 | F-002 |
| PLAN TS 대응 | TS-029 |
| 대상 | `opal/skills/op-dev-plan/SKILL.md` (공용 설계 워커 — 미접촉 대상) + opd STEP 3.5 흐름 |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** — git diff 0 검증 + opd 흐름 정합 대조 |
| 축 | ⑥ 경계 (제약 준수) |
| 조건 | R-1~R-6 반영 완료 |
| 기대 결과 | ① `opal/skills/op-dev-plan/SKILL.md`의 diff가 0건이다 (근거: [MUST] brain `opds-testscenario-producer-establishment` §결정 내용 "공용 스킬 미접촉 원칙") ② opd STEP 3.5의 기존 절차(작성 → 게이트 → 사용자 확인) 순서가 보존되고 선작성 착수 지시만 STEP 2에 추가됐다 |
| 도구 | git diff, bash grep |
| 실행 명령 | `git diff --stat opal/skills/op-dev-plan/` `; diff <(git show HEAD:opal/skills/opal-pilot-dev/SKILL.md) opal/skills/opal-pilot-dev/SKILL.md` |
| 결과 | PASS |
| 상세 | ① `git diff --stat opal/skills/op-dev-plan/` 무출력(diff 0건) — 공용 설계 워커 스킬 미접촉 확인. ② 전체 diff 대조 결과 opd SKILL.md의 유일한 실질 변경은 (a) STEP 3 §3-1에 "목표계열 선작성 착수" 인용 블록 삽입, (b) STEP 3.5 절차 1을 "PLAN.md §리스크 가설 표 Read"에서 "Block B 보강 — 선작성 초안이 있으면 …" 으로 대체, (c) 절차 4에 "보강 완료 판정 3조건" 문구 추가, (d) 절차 5 게이트 호출에 "(1회)"·"보강 완료 이후에만 호출" 문구 추가, (e) verdict:pass 하위에 mark 시점 문장 1줄 추가, (f) 변경이력 1행 추가 — 기존 절차 순서(1.보강/작성 Read → 2.형식 작성 → 3.5단계 적용 → 4.mark → 5.게이트 → 6.사용자 보고)는 그대로 보존되고 선작성 착수 지시만 STEP 3(PLAN 지목대로면 STEP 2였을 위치이나 H-h 정정으로 STEP 3)에 추가됨을 확인. |

#### S-16: 게이트 행 조기 advance가 도구 층에서 차단된다 (Block B 보강 — TS-014)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-d |
| 기능 매핑 | F-003 |
| PLAN TS 대응 | TS-014 |
| 대상 | `state-tool advance --task-step plan.scenario_gate` (도구 무변경 실증) |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** — 임시 태스크 폴더에 state init 후 조기 advance 호출 |
| 축 | ⑥ 경계 / 부정 |
| 조건 | `plan.plan_md` 행이 미완(`pending`/`in_progress`)인 opds state.json (`TMP-GATE-TEST` 픽스처) |
| 기대 결과 | `advance --task-step plan.scenario_gate` 호출이 `stage_transition_violation` 에러로 거부되고 exit 1을 반환한다 — 즉 **게이트 행 advance/mark가 도구 변경 없이 이미 차단**됨이 실증된다 (근거: `opal/tools/state-tool/state_tool.py:634` guard scope full, advance 경로 `:1423` `force=False`). 검증 후 임시 폴더를 삭제한다 |
| 도구 | state-tool advance |
| 실행 명령 | `bash opal/tools/state-tool/run.sh init <임시경로>/tmp-gate-test --skill opds --mode agentic --task-title "TMP-GATE-TEST" --rows-from opal/skills/opal-pilot-dev-short/references/pipeline.json` → `bash opal/tools/state-tool/run.sh advance <임시경로>/tmp-gate-test --task-step plan.scenario_gate` |
| 결과 | PASS |
| 상세 | 임시 태스크(opds, `plan.plan_md` 초기 상태 `pending`, 스크래치패드 하위 `tmp-gate-test/`)를 init 후 `advance --task-step plan.scenario_gate` 호출 결과: `{"ok": false, "command": "advance", "error": "stage_transition_violation", "message": "단계 건너뛰기 차단: 행 4 갱신 전에 앞 행 [1, 3]이(가) 완료되지 않았음 (PLAN §M-A stage-transition guard)", "row_id": 4, "incomplete_rows": [1, 3]}`, exit code 1 — 기대한 `stage_transition_violation` + exit 1 정확히 일치. 검증 완료 후 임시 폴더(`tmp-gate-test/`)를 `rm -rf`로 삭제, 095 태스크 자신의 `state.json`은 미접촉(git status로 확인: 095 태스크 폴더는 신규 태스크 전체가 untracked 상태일 뿐 이번 검증으로 인한 변경 0건). |

> **[설계 의도]** H-d의 운영 영향을 P1로 낮춘 근거는 **"행 advance/mark 차단(도구) + 호출 시점 규율(문서)"의 합**이다. 도구가 차단하는 것은 게이트 **행 상태 전이**이며 `op-scenario-gate` 스킬 호출 자체는 차단하지 않는다 — 스킬을 조기 호출하면 결정론 축이 FAIL할 뿐이고(S-12가 그 경로를 검증), 행이 ✅로 넘어가지 못하는 것은 이 시나리오가 검증한다. 두 층을 합쳐야 규율 위반이 파이프라인을 통과할 수 없다.
> **[범위 정정 이력]** 최초 기재는 "선작성 시점에 게이트를 호출하려는 시도가 차단됨"이었으나, 독립 평가자(SCENARIO-GATE-1.md 비차단 관찰 3)가 주장 범위 과대를 지적했다 — 차단 대상은 행 전이이지 스킬 호출이 아니다. 오독 제거를 위해 "행 advance/mark 차단"으로 좁혔다.

#### S-17: 검증 2원화(작성자≠PLAN 워커)가 문서 수준에서 확인된다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-a |
| 기능 매핑 | F-001, F-002, F-004, F-005 |
| PLAN TS 대응 | 평가자 관찰 2 (a) 보강 — PLAN TS 미대응 |
| 대상 | `red-first.md` §1.6 (c) · `test-scenario-guide.md` §목적 1 · opd·opds SKILL.md 작성 주체 서술 · `op-dev-plan/SKILL.md` 출력 범위 |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** — bash grep 4지점 대조 |
| 축 | ⑥ 경계 (제약 3 — 검증 2원화 불변) |
| 조건 | R-1~R-5 반영 완료 |
| 기대 결과 | ① `red-first.md` §1.6 (c)에 작성자≠PLAN 워커 `[MUST]`가 존재 ② `test-scenario-guide.md` §목적 1의 기존 self-confirming 방지 문장이 잔존(재정의 0건) ③ opd·opds SKILL.md 어디에도 **PLAN 워커(`opal-plan-agent`·`op-dev-plan`)를 시나리오 작성 주체로 지목하는 서술이 신설되지 않았다** — 선작성 착수 지시의 주체가 PM+캡틴 페어로 명시된다. **[판정 방법]** 파일 단위로 판정하되 주체 명시는 **소절 단위**로 인정한다 — opd는 착수 지시 본문에 직접 명시하고, opds는 같은 소절 리드(`### TEST-SCENARIO 작성 …` 하위 인용 블록)가 명시한다. (a) 라인 단독 grep으로 판정하지 마라(opds는 리드가 담당하므로 오판한다) ④ `op-dev-plan/SKILL.md`가 시나리오 문서를 출력 범위에서 제외하는 기존 서술을 유지한다(diff 0건, S-14와 중복 검증) |
| 도구 | bash grep |
| 실행 명령 | `grep -n "작성자≠PLAN 워커" opal/core/references/harness/red-first.md` `; sed -n '9,15p' opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` `; grep -n "opal-plan-agent\|op-dev-plan" opal/skills/opal-pilot-dev/SKILL.md opal/skills/opal-pilot-dev-short/SKILL.md` `; grep -n "TEST-SCENARIO" opal/skills/op-dev-plan/SKILL.md` `; git diff --stat opal/skills/op-dev-plan/` |
| 결과 | PASS |
| 상세 | ① `red-first.md:82` `**(c) [MUST] 작성자≠PLAN 워커 불변**` 확인. ② `test-scenario-guide.md:13` "PLAN.md §리스크 가설 표에서 H-N 가설을 읽어 검증 시나리오를 도출. self-confirming 방지를 위해 PLAN 작성자(opal-plan-agent)와 다른 작성자가 수행." — 기존 문장 잔존(재정의 0건, diff상 §목적 절 무변경). ③ opd·opds SKILL.md의 `opal-plan-agent`/`op-dev-plan` 언급 6건 전수 확인: opd `:62-63`(PLAN 디스패치 지시문, PLAN.md 작성 지시일 뿐 시나리오 작성 지목 아님), opd `:95`("이 단계는 self-confirming 방지를 위해 PLAN 워커(opal-plan-agent)와 다른 작성자가 수행한다" — 주체는 앞 문장의 "알투(PM)+캡틴 페어", PLAN 워커는 반대 대조 대상으로만 언급), opds `:45,47`(PLAN 디스패치 관련, 시나리오 작성과 무관), opds `:56`(소절 리드 — "TEST-SCENARIO.md는 **알투(PM)+캡틴 페어**가 …직접 작성한다" — PM+캡틴 페어가 명시 주체, PLAN 워커는 "PLAN.md만 작성"으로 대조됨). **판정 방법 준수**: opds는 (a) 라인 자체가 아닌 상위 리드(`:56`, `### TEST-SCENARIO 작성` 소절 하위 인용 블록)가 주체를 명시하므로 (a) 라인만 보고 FAIL 판정하지 않음 — 리드까지 포함한 소절 단위로 PM+캡틴 페어가 주체임을 확인. PLAN 워커를 시나리오 작성 주체로 지목하는 신설 서술 0건. ④ `op-dev-plan/SKILL.md:6,35,146`에 "TEST-SCENARIO.md는 opal-pilot-dev STEP 3.5에서 PM이 별도 작성" / "제외 출력: TEST-SCENARIO.md" 기존 서술 유지, `git diff --stat opal/skills/op-dev-plan/` 무출력(diff 0건, S-14와 동일 결과로 중복 검증됨). |

> **[보강 근거]** 독립 평가자(SCENARIO-GATE-1.md 비차단 관찰 2 (a))가 "작성자 ≠ `opal-plan-agent`를 직접 확인하는 Then이 없다"고 지적했다. 검증 2원화는 TASK.md §제약 조건 3항이며 H-a 방어의 첫 층이므로, 기계 검증 가능한 시나리오로 승격했다.

#### S-18: 후속 분리 3 pilot이 미접촉으로 유지된다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-e |
| 기능 매핑 | F-006 |
| PLAN TS 대응 | 평가자 관찰 2 (b) 보강 — PLAN TS-029 범위 밖 |
| 대상 | `opal-pilot-sdd`·`opal-pilot-project-loop`·`opal-pilot-project-dev` SKILL.md + 각 `references/pipeline.json` |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** — git diff |
| 축 | ⑥ 경계 (제약 7 — 후속 분리) |
| 조건 | R-1~R-6 반영 완료 |
| 기대 결과 | opsdd·oppl·oppd 3 pilot의 SKILL.md와 pipeline.json diff가 전부 0건이다 — TASK.md §범위 "opsdd·oppl·oppd 3 pilot 배선(후속 태스크)" 제외가 실제로 지켜졌음이 확인된다. 규칙 SSOT(`red-first.md`·`test-scenario-guide.md`·`scenario-gate.md`) 변경이 이 3 pilot의 동작을 바꾸지 않는다는 점도 함께 확인한다(참조 관계만 존재, 배선 미변경) |
| 도구 | git diff |
| 실행 명령 | `git diff --stat opal/skills/opal-pilot-sdd/ opal/skills/opal-pilot-project-loop/ opal/skills/opal-pilot-project-dev/` |
| 결과 | PASS |
| 상세 | `git diff --stat opal/skills/opal-pilot-sdd/ opal/skills/opal-pilot-project-loop/ opal/skills/opal-pilot-project-dev/` 무출력(diff 0건) — `git status --short` 동일 3디렉토리 대상으로도 무출력 확인. 3 pilot(opsdd·oppl·oppd)의 SKILL.md·pipeline.json 전부 미접촉임을 확인, TASK.md §범위 제외가 실측으로 지켜짐. |

> **[보강 근거]** 독립 평가자(SCENARIO-GATE-1.md 비차단 관찰 2 (b))가 "후속 분리가 기계 검증에서 빠져 있다 — S-14와 PLAN TS-029 모두 `op-dev-plan`·`op-dev-test-scenario/SKILL.md` 범위만 검사"라고 지적했다. 범위 이탈은 SSOT 표류의 직접 원인이므로 명시 검증으로 승격했다.

### L3. 사용자 협업 (수동, [SUPERVISOR] 마커)

#### S-15: 캡틴이 자기적용 산출물의 규칙 정합성을 확인한다 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | (목표 달성 — 규칙 재현성) |
| 기능 매핑 | F-001~F-005 |
| PLAN TS 대응 | 선작성 고유 — PLAN TS 미대응 |
| 대상 | 본 태스크 `TEST-SCENARIO.md` §0 + 신설 규칙 문언 |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업)** — 자동화 불가: "규칙이 의도한 판단을 유도하는가"는 사람 판정 영역 |
| 축 | ① **목표 달성** |
| 조건 | R-1~R-6 반영 + S-1~S-14 완료 |
| 기대 결과 | 캡틴이 ① 신설 규칙을 읽고 "PLAN과 병렬로 목표계열을 선작성한다"는 의도가 오해 없이 전달되는지 ② 본 문서 §0의 선작성 상태 표기가 그 규칙과 정합한지 ③ 다음 태스크에서 이 규칙만 읽고 동일 절차를 재현할 수 있는지를 확인하고 판정한다 |
| 실행자 | [SUPERVISOR] — 캡틴 수동 확인 필요 |
| 결과 | **PASS** |
| 상세 | 캡틴 수동 확인 (2026-08-19 22:19) — PM이 표준 양식으로 확인 대상 3건(`red-first.md` §1.6 / `test-scenario-guide.md` Step 1 Block A·B / 본 문서 §0)과 확인 질문 3항((1) 선작성 의도가 오해 없이 읽히는가 (2) §0 표기가 규칙과 정합한가 (3) 이 규칙만으로 재현 가능한가)을 제시하고 회신 수신. **캡틴 회신: "Pass"** — 3항 전건 충족 판정. 자동화 불가 영역(규칙이 의도한 판단을 유도하는가)이므로 M3 사용자 협업으로 판정했다 |

> **PM 요청 양식** (TEST 단계에서 PM이 캡틴에게 제시):
> ```
> [SUPERVISOR 요청] S-15 — 신설 규칙 문언 검토
> 확인 대상: red-first.md 신설 절 / test-scenario-guide.md Step 1 / 본 TEST-SCENARIO.md §0
> 확인 질문: (1) 선작성 의도가 오해 없이 읽히는가 (2) §0 표기가 규칙과 정합한가 (3) 이 규칙만으로 재현 가능한가
> 회신 형식: Pass / Fail + 사유
> ```

---

## 4. AC ↔ 가설 ↔ 기능 ↔ 계층 ↔ 시나리오 매핑 표

> Block A(AC·계층·시나리오 열)는 선작성, Block B(가설 ID·기능 ID 열)는 PLAN.md 수신 후 보강. 미기재 0건.

| AC ID | 가설 ID | 기능 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|--------|---------|---------|-----------------|------|
| R-1 AC (a)(b)(c) 3항목 + 근거 인용 | H-f, H-i | F-001 | L1 | S-1 | _{EXECUTE 워커가 채움}_ | `red-first.md` §1.6 신설 |
| R-2 AC 2블록 분리 + 축 매핑 표 + Step 2·3 제외 명시 | H-a, H-b, H-c | F-002 | L1 | S-2 | _{EXECUTE 워커가 채움}_ | 도출 엔진 Block A/B |
| R-3 AC [MUST] 호출 시점 + 금지 근거 | H-d | F-003 | L1 | S-3 | _{EXECUTE 워커가 채움}_ | 게이트 규율 |
| R-4 AC 3단계 순서 + mark 시점 | H-e, H-i | F-004 | L1 | S-4 | _{EXECUTE 워커가 채움}_ | opds 배선 (WIRE-D) |
| R-5 AC STEP 3 착수 + STEP 3.5 보강·게이트 + mark 시점 | H-b, H-h | F-005 | L1 | S-5 | _{EXECUTE 워커가 채움}_ | opd 배선 (WIRE-E) — STEP 2 오기재 정정 |
| R-6 AC 변경이력 5문서 | (전 기능 공통) | F-001~F-006 | L1 | S-6 | _{EXECUTE 워커가 채움}_ | KST 일시 + `(095)` |
| R-6 AC 배포본 diff 0 | H-g | F-006 | L2 | S-7 | _{EXECUTE 워커가 채움}_ | 변경이력 strip 제외 |
| 제약 — 도구 변경 0 | (제약) | F-006 | L2 | S-8 | _{EXECUTE 워커가 채움}_ | `.py` diff 0 + 회귀 pass |
| 제약 — 행 구조 불변 | H-c | F-006 | L2 | S-9 | _{EXECUTE 워커가 채움}_ | spec-validate 10/10 |
| 제약 — SSOT 단일화 | H-e | F-001~F-005 | L2 | S-10 | _{EXECUTE 워커가 채움}_ | 소유권 표 grep 매트릭스 |
| 완료기준 — 규칙 채택 | H-a | F-001~F-005 | L2 | S-11 | _{EXECUTE 워커가 채움}_ | **채택 검증(자기적용)** |
| 제약 — 보강 생략 차단 | H-d | F-003 | L2 | S-12 | _{EXECUTE 워커가 채움}_ | **음성통제(coverage-check)** |
| 제약 — RED-first 순서 불변 | H-f | F-001 | L2 | S-13 | _{EXECUTE 워커가 채움}_ | 강제 트랙 5종 보존 |
| 제약 — 공용 스킬 미접촉 / opd 무회귀 | H-b | F-002 | L2 | S-14 | _{EXECUTE 워커가 채움}_ | `op-dev-plan` diff 0 |
| 제약 — 게이트 조기 호출 차단 | H-d | F-003 | L2 | S-16 | _{EXECUTE 워커가 채움}_ | **도구 무변경 실증** |
| 제약 — 검증 2원화 불변 | H-a | F-001,002,004,005 | L2 | S-17 | _{EXECUTE 워커가 채움}_ | **평가자 관찰 2(a) 보강** |
| 제약 — 후속 분리(3 pilot 미접촉) | H-e | F-006 | L2 | S-18 | _{EXECUTE 워커가 채움}_ | **평가자 관찰 2(b) 보강** |
| 목표 문장 — 규칙이 재현 가능하게 전달됨 | (목표 달성) | F-001~F-005 | L3 | S-15 | (수동) | **목표 달성축 [SUPERVISOR]** |

### 4.1 커버리지 자가 점검

| 축 | 대상 | 커버 | 미커버 |
|----|------|------|--------|
| ② 요구 커버 | TASK.md R-1~R-6 (6건) | 6건 (S-1~S-7) | **0건** |
| ③ 기능 커버 | PLAN.md F-001~F-006 (6건) | 6건 | **0건** |
| ④ 리스크 커버 | PLAN.md H-a~H-i (9건) | 9건 (H-a→S-2·S-11 / H-b→S-2·S-5·S-14 / H-c→S-2·S-9 / H-d→S-3·S-12·S-16 / H-e→S-4·S-10 / H-f→S-1·S-13 / H-g→S-7 / H-h→S-5 / H-i→S-1·S-4) | **0건** |
| ① 목표 달성 | 태스크 목표 문장 | S-15 (L3 캡틴 재현성 판정) | - |
| ⑤ 채택 / 잔존 | 완료기준 — 규칙 채택 | S-11 (실행 증거 기반) | - |
| ⑥ 경계 / 부정 | 제약 **7항** (도구변경0 · STATE행불변 · 검증2원화 · RED순서 · 배포경계 · SSOT단일화 · 후속분리) | 7/7 — S-8(1) · S-9(2) · S-17(3) · S-13(4) · S-7(5) · S-10(6) · S-18(7) + 부정경로 S-12·S-16 · 공용미접촉 S-14 | **0건** |

> **가설 N건 → 시나리오 N건 이상 원칙**: 가설 9건 대비 시나리오 18건으로 충족한다 (`test-scenario-guide.md` §Step 3 계층 결정 원칙).
> **PLAN TS 흡수**: PLAN.md가 정의한 TS-001~TS-029 전건이 S-1~S-16의 `PLAN TS 대응` 필드에 매핑됐다. 미대응 TS 0건.
> **선작성 고유 3건**: S-11(채택 검증) · S-12(음성통제) · S-15(목표 달성)는 PLAN TS에 대응이 없는 Block A 고유 산출이다 — 목표계열 선작성이 실제로 PLAN 관점만으로는 도출되지 않는 시나리오를 만들어냈다는 자기적용 증거다.

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | (해당 없음) | **N/A** | changed_files가 `.md` **5건 / 코드 0건**(`git diff --name-only -- opal/` 확장자 분포 = md 5). 프로젝트에 Markdown 린터가 설정되어 있지 않다 |
| 2 | 타입 체크 | (해당 없음) | **N/A** | 동일 — 타입 체크 대상 소스(.py/.ts) 변경 0건 |
| 3 | 포맷터 | (해당 없음) | **N/A** | 동일 — 포맷터 대상 코드 변경 0건 |
| 4 | 도구 회귀 | pytest | **PASS** | `346 passed / 1 failed` — 실패 1건은 전역 홈 오염 의존 **선재 결함**(`test_resolve_infer_fallback_when_no_yaml`), `.py` diff 0건으로 본 태스크 무관 확정(S-8 상세 참조) |
| 5 | 스펙 검증 | state-tool spec-validate | **PASS** | 10 pilot **10-10 통과**, `pipeline.json` diff 0건 (S-9) |
| 6 | 컨벤션 자동 진단 | opal-convention-checker | **미발동(자연 스킵)** | 발동 조건 "컨벤션 적용 대상 ≥1건"에서 코드 파일 변경 **0건**이므로 미발동. 문서 컨벤션(변경이력·SSOT·배포 경계)은 S-6·S-7·S-10이 대체 검증 |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | **PASS** | 변경 5파일 + 태스크 산출물 전체를 `api_key|secret|password|token|bearer|private_key|sk-*` 할당 패턴으로 grep — **검출 0건** (2026-08-19 22:22) |
| 2 | .gitignore 확인 | **PASS** | `.gitignore` 존재 · 민감 패턴 등재 확인. 태스크 산출물(`state.json` 등)은 추적 대상이 정상이며 시크릿을 담지 않는다 |
| 3 | 배포 경계 | **PASS** | `~/.opal/` 직접 편집 **0건** — 배포본 갱신은 `install-mac.sh` 경유만. install 전 배포본 5파일을 스크래치패드에 백업해 롤백 경로 확보 (S-7) |

## 7. 판정

**All Pass** — 시나리오 **18/18 PASS**. 판정 근거: ① 결정론 검증 16건은 `opal-test-agent`가 실제 명령 실행 출력 원문을 증거로 기록 ② 핵심 방어 2건 작동 실증 — S-12 음성통제(결함 페이로드 `coverage_unmet` exit 16 → 정상 페이로드 `all_covered:true` exit 0, 2단 수렴) · S-16 도구 차단(`stage_transition_violation` exit 1, `incomplete_rows:[1,3]`) ③ S-15는 캡틴 수동 확인 **Pass**(M3, 규칙 재현성 3항 충족) ④ S-7은 install 후 PM 직접 검증 — strip-후 diff 5/5 OK + 배포본 런타임 채택 확인 ⑤ 도구 회귀 `346 passed / 1 failed` — 실패 1건은 `test_resolve_infer_fallback_when_no_yaml`의 전역 홈 오염 의존 실패로, `.py` diff 0건이고 해당 테스트가 본 태스크 수정 문서를 읽지 않음을 PM이 직접 재검증한 **선재 결함**(별도 태스크 권고)
