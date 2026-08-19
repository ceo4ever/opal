# DONE: TEST-SCENARIO 목표계열 선작성 — PLAN 병렬 도출 트랙 신설

> 완료일: 2026-08-19 22:30 KST | 태스크: 095 | 파이프라인: opds (agentic)
> 산출물: TASK.md · PLAN.md · TEST-SCENARIO.md · SCENARIO-GATE-1.md · AGENTIC-LOG.md(41 엔트리) · STATE.md · DONE.md

---

## 1. 무엇을 해결했나

캡틴이 "시나리오 작성과 구현을 병렬로" 검토를 요청했다. 실측 결과 그 안은 부적격이었다 — EXECUTE 워커가 `TEST-SCENARIO.md`를 **완료 판정 기준**으로 소비하므로(`opal-pilot-dev/SKILL.md:131-134`) 병렬은 완료기준을 사후에 만드는 것이고, 헌법 §1이 이를 "rationalization"으로 명시 금지한다. `state_tool.py:634` stage-transition guard가 도구 층에서 이미 차단하기도 했다.

이어 캡틴이 제시한 대안 "PLAN하면서 시나리오 만들기"는 순서를 뒤집지 않고 **앞당기는** 방향이라 위반 지점이 없었다. 실측해 보니 도출 입력이 이미 2계열로 갈려 있었다.

| 계열 | 입력 | 원천 | 대응 루브릭 축 |
|------|------|------|--------------|
| 채택 관점 | 목표 문장 · 요구사항 R · 채택/잔존 기준 | TASK.md | ① 목표달성 ② 요구커버 ⑤ 채택·잔존 ⑥ 경계·부정 |
| 파괴 관점 | 리스크 가설 H-N · 기능 F-NNN | PLAN.md | ③ 기능커버 ④ 리스크커버 |

게이트 정규화 계약도 같은 경계였다 — `goal`·`requirements`는 TASK 유래이고 `features`·`hypotheses`만 PLAN 유래다(`scenario-gate.md` §3). 즉 **루브릭 6축 중 4축이 PLAN 없이 도출 가능**하다.

이제 `red-first.md` §1.6이 그 4축을 PLAN 워커 실행과 **병렬 선작성**하는 트랙을 정의하고, `test-scenario-guide.md` Step 1이 Block A/B 절차를, `scenario-gate.md` §4가 게이트 호출 시점을 집행한다.

## 2. 왜 이 설계인가

**효율이 아니라 관점 편향 차단이 목적이다.** 070 사건의 근본 원인은 루브릭 부재가 아니라 "리스크 가설(파괴 관점, H-N)만 도출 입력으로 쓴" 편향이었다(`scenario-gate.md` §1). 편향의 원인이 **PLAN 선행 그 자체**이므로, PLAN을 읽지 않은 상태에서 목표로부터 도출하면 오염이 원천 차단된다.

주요 설계 판단:

- **§1.6 절 번호 고정 (H-f)** — 신설 절을 §1.6(§1.5 직후)에 넣었다. 기존 §2~§6 번호를 밀면 8개 도구 테스트 스위트와 `coding-principles.md:53`·`opal/agents/opal-test-agent/AGENT.md:91`이 인용하는 `red-first.md §2`~`§5` 60건 이상이 일괄 파손된다.
- **공용 스킬 미접촉** — `op-dev-plan/SKILL.md`(opd·opds 공용 설계 워커)를 건드리지 않았다. task:075가 확립한 원칙이며 배선은 오케스트레이터 2문서와 하네스 SSOT에만 넣었다.
- **규칙 소유권 표로 SSOT 이중화 차단** — RULE-A1~C3 각 규칙의 `정의` 문서를 1곳으로 고정하고 pilot SKILL.md는 앵커 포인터만 갖는다(WIRE-D·WIRE-E는 "규칙 본문 0줄").
- **opt-in 유지 (H-i)** — 강제하면 문서 전용 작업의 자연 스킵 경로가 막힌다. §1.6 (f)가 opt-in과 착수 판단 기준을 함께 규정한다.
- **self-confirming 퇴행 방어 3종 (H-a)** — 선작성 구간의 유일 입력이 TASK AC/R이므로 task:004가 지목한 "AC 중심 당연한 시나리오 양산"으로 퇴행할 위험이 있다. 작성자 분리만으로는 불충분하다고 판정하고 ⑥경계·부정 동시 도출 의무 / 보강 additive-only 금지 / 게이트 최종 방어선 유지를 규칙화했다.

## 3. 무엇을 바꿨나

| 파일 | 변경 | 소유 규칙 |
|------|------|----------|
| `opal/core/references/harness/red-first.md` | **§1.6 신설** (+70) — 리드(목적=품질, 효율 아님) + (a)~(f) | RULE-A1·A2·A3 정의 |
| `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | Step 1 → Block A/B 2계열 재구성 (+51/-5) | RULE-B1~B6 정의 |
| `opal/core/references/harness/scenario-gate.md` | §4에 `[MUST]` 호출 시점 규율 (+7) | RULE-C1·C2 정의 |
| `opal/skills/opal-pilot-dev-short/SKILL.md` | STEP 2 (a)(b)(c) 3단계 배선 (+24/-1) | WIRE-D (규칙 본문 0줄) |
| `opal/skills/opal-pilot-dev/SKILL.md` | STEP 3(PLAN) 착수 + STEP 3.5 보강·게이트 (+16/-13) | WIRE-E (규칙 본문 0줄) |

코드 변경 **0줄**. `opal/tools/**`·`pipeline.json`·`op-dev-plan/SKILL.md`·`op-dev-test-scenario/SKILL.md` 전부 diff 0건.

## 4. 동작 증거

**시나리오 18/18 PASS** (`TEST-SCENARIO.md` §7 판정 All Pass). 미기입 마커 잔존 0건.

| 검증 | 결과 |
|------|------|
| 목표-커버 게이트 iteration 1 | 결정론 `all_covered:true` exit 0 (R6/F6/H9/S16) + 판단축 **2/2/2 평균 2.0 gaps 0** |
| S-12 음성통제 | 결함 페이로드 → `coverage_unmet` exit 16 (features 6·hypotheses 9 누락) → 정상 페이로드 → `all_covered:true` exit 0 **2단 수렴** |
| S-16 도구 차단 | 게이트 행 조기 advance → `stage_transition_violation` exit 1 (`incomplete_rows:[1,3]`) |
| S-7 배포본 정합 | install 후 strip-후 diff **5/5 OK**, 배포본 런타임 채택 5지점 전건 확인 |
| 제약 7항 | 도구 diff 0 · `pipeline.json` diff 0 + spec-validate **10-10** · 검증 2원화 · RED-first 순서 · 배포 경계 · SSOT 단일화 · 후속 3 pilot 미접촉 |
| 도구 회귀 | `346 passed / 1 failed` — 실패 1건은 선재(§7 참조) |

## 5. 자기적용 실측

> **이 섹션은 배포된 `red-first.md` §1.6 리드가 근거로 인용한다.** 트랙의 목적 서술("효율은 목적이 아니다")이 이 수치에 근거한다.

본 태스크는 신설하려는 규칙을 **자기 자신에게 선적용**했다. PLAN 워커가 도는 동안 PM+캡틴이 Block A(①②⑤⑥)를 먼저 도출하고, PLAN.md 수신 후 Block B(③④)를 보강했다.

**시간 실측**

| 구간 | 실측 |
|------|------|
| PLAN 워커 소요 | **18분 30초** (1,109,780ms) |
| Block A 선작성 | 약 **5분** (18:18 디스패치 → 18:23 완료) — PLAN 구간에 완전히 숨음 |
| Block B 보강 | 약 **8분** (18:38 → 18:46) |
| 순 절감 (반사실 추정) | 순차 약 28.5분 vs 병렬 26.5분 → **약 7%** |
| 총 작업량 | 정정 비용으로 약 **3분 증가** |

선작성이 PLAN.md 존재 이전이었음은 파일 birthtime으로도 확인된다 — `TEST-SCENARIO.md` **18:23** < `PLAN.md` **18:37**. (단 birthtime은 플랫폼 의존이라 규칙 집행 수단으로 채택하지 않았다. `mtime`은 보강으로 갱신되어 증명력이 없다.)

**품질 실측 — 반사실 추정이 아니라 대조 결과**

| 관측 | 수치 |
|------|------|
| 선작성 고유 시나리오 | **3건** — S-11(채택 검증) · S-12(음성통제) · S-15(목표 달성) |
| 위 3건에 대응하는 PLAN TS | **0건** (TS-001~029 전건 대조) |
| PLAN TS의 선작성 집합 흡수율 | **29/29** (미대응 0건) |
| AC 되읽기형 시나리오 비율 | 6/16 — **과반 미달** (독립 평가자 판정) |

PLAN이 도출한 TS 29건은 전부 "산출물 검사 / 회귀 테스트" 성격이었고 채택 검증·부정 경로·목표 달성 판정이 없었다. 즉 **PLAN 관점만으로는 그 3건이 도출되지 않는다.**

**대가 — 정정 전파**

선작성 단계의 미검증 전제가 더 멀리 번졌다. TASK.md R-5가 opd 배선 지점을 "STEP 2(PLAN)"로 잘못 지목했고(실제 STEP 2는 ANALYSIS, PLAN은 STEP 3), 그 오류가 디스패치 프롬프트와 선작성 시나리오 S-5로 전파되어 **정정 지점이 4곳**이 됐다. 순차였다면 2곳이었다.

**결론**: 효율 이득은 미미하고(7%) 총 작업량은 늘었다. 품질 이득은 실측됐다(고유 3건). **따라서 이 트랙은 효율 명분이 아니라 관점 편향 차단 명분으로만 켠다** — §1.6 리드와 (f) 착수 판단 기준이 이 결론을 규칙으로 못박았다.

## 6. PM 판단 기록 (agentic)

전체 이력은 `AGENTIC-LOG.md` 41 엔트리. 주요 판단:

- **게이트 판단 13회 전건 Pass / Fail 0** — 매 게이트 산출물을 직접 Read해 재검증했고 워커 보고를 그대로 옮기지 않았다.
- **개선안 B 철회** — "S-11 채택 판정을 파일 시각 비교로 전환"을 캡틴에게 권고했으나 독립 평가자가 `mtime` 증명력 부재를 실측 반증했다. `birthtime`은 증명하나 플랫폼 의존이어서 금지사항에 저촉되므로 철회하고 평가자 권고(독립 관측치 우선)로 대체했다.
- **승인 게이트 과잉 인정** — 개선 A·D 반영에 별도 승인을 요청했으나, 캡틴 지적대로 이는 R-1 AC 범위 내 문구이자 프레임워크-우선 개선 원칙의 대상이므로 PM 자율 영역이었다.
- **install 순서 변경 제기** — `install-mac.sh`가 전역 배포본을 덮어써 검증 미완 규칙이 모든 프로젝트에 즉시 활성화되는 문제를 제기하고 캡틴 승인을 받아 **TEST 전건 통과 후 install**로 순서를 바꿨다(PLAN §4.2 Step 6~8 재구성). `pipeline.json` 행 구조는 불변이므로 제약 위반 없음.
- **워커 중단 대응** — TEST 워커가 API 오류로 조기 종료됐으나 산출물 실측 결과 담당 16건 전건 완료여서 재개하지 않고 PM 교차 검증으로 대체했다(`pm-review-gate.md` §워커 중단 시 산출물 실측 판정).
- **평가자 비차단 관찰 3건 전건 수용** — S-11 증거 2층 재배치 / S-17·S-18 신설(제약 커버 6종→7항) / S-16 주장 범위 축소. 시나리오 16→18건.
- **메타-순환 오탐 방어** — 마커 잔존 판정을 단순 grep으로 하면 마커를 설명하는 문서 자신이 영구 FAIL한다. 034 선례(`state_tool.py:2010,2025` 인라인 백틱 제거)를 근거로 전처리 규정을 RULE-B4에 의무화했다.

## 7. Known Issues

전부 **본 태스크 범위 밖 선재 결함**이며 헌법 §3(인접 코드 개선 금지)에 따라 미접촉했다.

| # | 결함 | 근거 | 권고 |
|---|------|------|------|
| 1 | test-tool 테스트가 전역 홈(`~/.opal/`) 오염에 격리되지 않아 `test_resolve_infer_fallback_when_no_yaml`이 환경 의존 실패(`source='global' != 'infer'`) | `.py` diff 0건 + 해당 테스트가 본 태스크 수정 문서를 읽지 않음을 PM 직접 재검증 | 별도 태스크. 선례 해법 존재 — 083이 code-scan에서 `OPAL_HOME` 주입 + 가짜 홈 5종으로 해소(`.opal/brain/pages/concept/code-scan-opal-home-test-isolation.md`) |
| 2 | `opal-harness.md` §2 하네스 모듈 테이블에 `scenario-gate.md` 미등록 (`red-first.md`만 `:111`에 등록) | PLAN §9 R-12 | 별도 태스크 |
| 3 | `docs/ARCHITECTURE.md:108`이 opds를 "TASK → PLAN → TEST-SCENARIO → EXECUTE"로 서술하나 실제로는 TEST-SCENARIO가 PLAN stage에 흡수(`pipeline.json` 11행, `plan.scenario_gate`) | PLAN §9 R-13 계열 | 별도 태스크 |

미해결 리스크: **없음**. PLAN §9 리스크 13건은 전부 대응책이 적용됐고 시나리오로 검증됐다.

## 8. 파급 — 다음 태스크부터 달라지는 것

- **opd·opds 두 파이프라인에서 선작성 트랙을 켤 수 있다.** opds는 STEP 2 (a)(b)(c), opd는 STEP 3 착수 + STEP 3.5 보강·게이트.
- **켤지 말지가 규칙으로 판단된다.** §1.6 (f) 착수 판단 기준 — PLAN 소요가 선작성 소요보다 길고, 목표가 파괴 관점으로 환원되지 않을 때만 유리하다. **판단이 서지 않으면 순차**가 기본이다.
- **게이트 호출이 1회로 규율된다.** 선작성 시점 호출은 `scenario-gate.md` §4가 금지하고, 게이트 행 조기 advance는 `state_tool.py:634` guard가 차단한다(S-16 실증).
- **보강을 건너뛸 수 없다.** ③④축 미보강 상태는 `scenario-coverage-check`가 `coverage_unmet`으로 거부한다(S-12 실증).
- **선작성 폐기율이 다음 판단의 입력이 된다.** 보강에서 선작성 시나리오가 절반 이상 수정·삭제되면 그 태스크는 선작성 부적격이었다는 신호로 §1.6 (f)가 규정한다.
- **opsdd·oppl·oppd 3 pilot은 미배선** — 규칙 SSOT는 상속되나 배선은 없다. 후속 태스크 대상이다.
