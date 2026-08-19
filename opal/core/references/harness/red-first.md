---
module: red-first
role: RED-first TDD 트랙 규칙 SSOT
load: TEST-SCENARIO 작성·EXECUTE 진입 시
상속: opal/core/PRINCIPLES.md (헌법) §4 — 원칙 자체는 헌법이 SSOT
---

# RED-first 트랙 — TDD RED→GREEN 규칙

> **행동 원칙 자체는 `opal/core/PRINCIPLES.md`(헌법)가 SSOT다.**
> 이 문서는 헌법 §4의 RED-first 트랙 운용 규칙만 정의한다.

---

## 0. 상속

[MUST] 헌법 §4(`~/.opal/PRINCIPLES.md:35-40`) 상속. 헌법 원칙을 재서술하지 않는다.

---

## 1. RED→GREEN 순서

[MUST] RED 단계에서 실패 테스트 코드를 작성·실행하여 실패(exit code≠0)를 증거로 기록한 뒤 GREEN(구현) 진입. RED 증거 없이 GREEN 진입 금지.

---

## 1.5 적용 기준 (하이브리드 자동분기)

**RED-first 강제** (self-confirming 위험 높음):
- 비즈니스 로직
- DB 스키마·마이그레이션
- API 계약
- 인증·인가
- 버그 수정(회귀 방지)

**구현 후 시나리오 검증 허용** (탐색·시각):
- 탐색적 프로토타입
- UI 화면·컴포넌트
- 행위 불변 리팩터
- 설정·문서

**판단 주체**: PM이 변경 영역으로 판단(TEST-SCENARIO 작성 시점). 모호하면 RED-first 기본(안전측).

**공통 불변**: 어느 트랙이든 ① 테스트 코드 산출물 ② 작성자≠구현자 ③ TEST 단계 검증을 유지한다.

**state-tool 연동**: RED-first 트랙 → `verify --red-check` ON / 구현-후-검증 트랙 → 기존 동작(`--red-check` OFF). 이 분기로 opt-in 구조가 정책을 그대로 집행.

---

## 1.6 목표계열 선작성 트랙 (PLAN 병렬)

본 트랙의 목적은 **도출 엔진의 관점 편향 차단**이다 — PLAN.md를 읽지 않은 상태에서 목표로부터 시나리오를 도출해, 리스크 가설(파괴 관점)에 갇혀 목표 달성(채택 관점) 시나리오가 누락되는 070 실패모드를 구조적으로 막는다.

**wall-clock 단축은 본 트랙의 목적이 아니다.** 선작성 소요가 PLAN 워커 실행 구간에 숨는 만큼의 절감은 있으나, PLAN 확정 후 보강 라운드에서 정정 비용이 발생하여 순 절감은 작다.

> **근거 — 095 자기적용 실측**: `tasks/095-260819-opds-시나리오-목표계열-선작성/DONE.md` §자기적용 실측 — 최초 적용 태스크(095)에서 PLAN 워커 소요 18분 30초 중 선작성 5분이 숨었으나 보강이 8분으로 늘어 순 절감은 약 7%에 그쳤고, 반면 선작성 고유 시나리오 3건(채택 검증·음성통제·목표 달성)이 PLAN 유래 도출(TS-001~029)에서 **대응 0건**으로 확인되어 품질 이득이 실측됐다.

따라서 효율을 기대해 본 트랙을 켜지 말고, **관점 편향 위험이 실재하는 태스크**(교체형 목표·핵심 목표가 파괴 관점으로 환원되지 않는 태스크)에서 켠다.

**(a) 선작성 가능 입력 3종 (TASK 유래)**

| # | 입력 | 원천 | 대응 루브릭 축 | 근거 |
|---|------|------|--------------|------|
| 1 | 목표 문장 | TASK.md §작업 목표 | ① 목표 달성 | `opal/core/references/harness/scenario-gate.md` §3 정규화 계약 `goal` |
| 2 | 요구사항 R 전체 목록 | TASK.md §요구사항 | ② 요구 커버 | 동 §3 `requirements` |
| 3 | (교체형 목표인 경우) 채택/잔존 기준 | TASK.md | ⑤ 채택/잔존 | 동 §2 ⑤ |

이 3종 **밖의 입력을 선작성에 쓰지 않는다** — 특히 PLAN.md를 읽지 않는다(PLAN 관점 오염 차단).

게이트 정규화 계약에서 `goal`·`requirements`는 TASK 유래이고 `features`·`hypotheses`만 PLAN 유래다 — 이 경계가 선작성 가능 범위의 계약적 근거다 (→ `opal/core/references/harness/scenario-gate.md` §3).

계열↔축 매핑과 도출 절차는 `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` §작성 프로세스 Step 1이 SSOT다.

**(b) [MUST] PLAN 확정 후 ③④축 보강 필수**

[MUST] 선작성 초안만으로 TEST-SCENARIO 작성을 종료하지 않는다. PLAN.md 확정 후 PLAN 유래 계열(`features` F-NNN · `hypotheses` H-N)을 도출 입력에 추가하여 루브릭 ③기능커버·④리스크커버를 보강한다.

근거: [MUST] `opal/core/references/harness/scenario-gate.md` §2: "③ 기능 커버 | PLAN F ↔ 시나리오 매핑 완전 | test-tool(결정론)".

보강 절차와 완료 판정 3조건은 `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` §작성 프로세스 Step 1 Block B가 SSOT다.

**(c) [MUST] 작성자≠PLAN 워커 불변**

[MUST] 선작성 주체는 알투(PM)+캡틴 페어이며 PLAN.md 작성 주체(`opal-plan-agent`)와 분리 유지한다. 도출 시점이 앞당겨져도 이 분리는 변하지 않는다.

근거: [MUST] `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` §목적 1: "self-confirming 방지를 위해 PLAN 작성자(opal-plan-agent)와 다른 작성자가 수행." / 채점 측 분리는 `opal/core/references/harness/scenario-gate.md` §4 Producer≠Evaluator.

**(d) RED→GREEN 순서 불변**

본 트랙은 시나리오 **도출 시점만** 앞당기며 §1 RED→GREEN 순서와 §1.5 강제/허용 분기를 변경하지 않는다. 선작성은 RED 테스트 코드 작성이 아니다 — 마크다운 시나리오 초안 작성이며, RED 테스트 코드 작성 주체는 §2에 따라 `opal-test-agent(mode: red)`로 유지된다.

근거: 본 문서 §1 (동일 문서 자기참조) / TASK.md §확정된 설계 방향 D-8.

**(e) 게이트 호출 금지 구간**

선작성 시점(PLAN 워커 실행 중)에는 목표-커버 게이트를 호출하지 않는다. 호출 시점 규율 SSOT는 `opal/core/references/harness/scenario-gate.md` §4다.

**(f) 트랙 성격 = opt-in (자연 스킵 보존)**

본 트랙은 강제가 아니다. 선작성을 착수하지 않고 PLAN 확정 후 Block A·B를 연속 수행해도 결과는 동등하다(순차 경로 = 현행 동작). 문서 전용 작업 등 TEST-SCENARIO.md 자체가 스킵되는 경로에서는 본 절도 자연 스킵된다.

**착수 판단 기준**:

| 조건 | 판단 |
|------|------|
| PLAN 워커 예상 소요가 선작성 소요보다 **길다** | 선작성 유리 — 선작성이 PLAN 구간에 숨는다 |
| PLAN 워커 예상 소요가 선작성 소요보다 **짧거나 비슷하다** (소규모 태스크) | **순차 권장** — 선작성이 PLAN을 기다리게 만들어 오히려 지연된다 |
| 목표가 파괴 관점(리스크 가설)으로 환원되지 않는다 / 교체형 목표다 | 선작성 유리 — 관점 편향 위험이 실재한다 |
| 목표가 단일 결함 수정이고 검증 관점이 파괴 관점과 사실상 일치한다 | **순차 권장** — 선작성의 품질 이득이 발생하지 않는다 |

예상 소요를 사전에 정확히 알 수 없으므로, **판단이 서지 않으면 순차(현행)를 택한다** — 순차는 결과가 동등하고 정정 전파 위험이 없다.

선작성한 시나리오가 PLAN 확정 후 보강에서 절반 이상 수정·삭제되면, 그 태스크는 선작성 부적격이었다는 신호다 — 다음 태스크의 착수 판단에 반영한다.

근거: 095 실측 — 선작성 단계의 미검증 전제(TASK.md의 오배선 지목)가 시나리오 3곳으로 전파되어 정정 지점이 순차 대비 2곳 늘었다(`tasks/095-260819-opds-시나리오-목표계열-선작성/AGENTIC-LOG.md` #8~#9).

---

## 2. 작성자≠구현자

[MUST] RED 테스트 코드 작성 주체는 EXECUTE 구현 워커(op-dev-execute)와 분리한다. RED 작성은 opal-test-agent(mode: red)가 담당한다.

---

## 3. 테스트 불변성

[MUST] GREEN/fix 루핑 중 RED 테스트 파일 수정 금지. 위반 시 블로커.

> reward hacking 방어: 테스트 약화·삭제·조건 완화로 통과를 유도하는 행위를 차단한다.

---

## 4. 공개 인터페이스 검증

내부 구현/private 결합 금지, 공개 인터페이스·관찰 행위(반환값/exit code/관측 출력)로 검증.

---

## 5. graceful skip

테스트 인프라 부재 프로젝트/문서 전용 태스크는 RED 트랙 자동 우회 금지 — 인프라 부재 시 사용자 에스컬레이션. state-tool RED 게이트는 산출물 부재 시 skip.

---

## 6. STATE 행 정책

RED는 EXECUTE 내부 서브스텝으로 흡수한다. 별도 STATE 행을 추가하지 않는다 (opds 10행/opd 15행 SSOT 보존).

---

## 변경이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-06-09 18:42 | 초기 작성 — RED-first 트랙 SSOT 신설 (016) |
| v1.1 | 2026-08-19 20:59 | §1.6 목표계열 선작성 트랙(PLAN 병렬) 신설 — 선작성 가능 입력 3종·③④축 보강 필수·작성자≠PLAN 워커·RED→GREEN 불변·게이트 호출 금지 구간·opt-in 착수 판단 기준 (095) |
