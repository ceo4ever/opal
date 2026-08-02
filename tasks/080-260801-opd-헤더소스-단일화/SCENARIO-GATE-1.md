# SCENARIO GATE 1 — 판단축 채점 (scenario-rubric)

> 실행 일시: 2026-08-01T13:36:58Z | phase: `scenario-rubric` | iteration: 1
> scenario_source: `tasks/080-260801-opd-헤더소스-단일화/TEST-SCENARIO.md`
> 채점 주체: opal-evaluator-agent (Evaluator) ≠ 작성 주체: 알투(PM) + 캡틴 (Producer)
> 기준 SSOT: `opal/core/references/harness/scenario-gate.md` §2 판단축 3종 · §5-1 종료조건

## 0. 판정 범위

| 축 | 판정 주체 | 본 보고서 |
|----|----------|----------|
| ① 목표 달성 | opal-evaluator-agent | **채점** |
| ② 요구 커버 | test-tool (결정론) | 채점 안 함 — `scenario-coverage-check` exit 0 (requirements 13 / features 7 / hypotheses 14 / scenarios 22, `all_covered: true`) |
| ③ 기능 커버 | test-tool (결정론) | 채점 안 함 (동상) |
| ④ 리스크 커버 | test-tool (결정론) | 채점 안 함 (동상) |
| ⑤ 채택/잔존 | opal-evaluator-agent | **채점** |
| ⑥ 경계/부정 | opal-evaluator-agent | **채점** |

> [MUST] `scenario-gate.md` §2 — 판정 주체 분리. 결정론 축을 재채점하지 않았다.
> CONTRACT.md 부재(opd 1차 접합) — `scenario-rubric`은 Phase 2(CONTRACT 루브릭절 병합) 비적용 트랙이므로 판정에 영향 없음.

---

## 1. 판단축별 판정

### ① 목표 달성 — **2점**

**태스크 목표**: "`headerSource` 한 키가 code-scan의 조회·작성 판정·검증 전 경로를 지배하게 하고, `scopes` 객체 형식(include/exclude)으로 혼재 디렉토리를 지원한다" (TASK.md §명확화 결과)

**근거**

S-19(`TEST-SCENARIO.md:415-428`)가 목표를 **직접·운영 계층에서** 검증한다. 프록시 지표가 아니라 목표 문장 그 자체를 대상으로 선언했고(`| 대상 | **태스크 목표 그 자체**`), 운영자가 실제로 밟는 순서 `discover → scaffold → target → validate → scan`을 **실 CLI 연속 호출**로 관통한다(M1, mock 0건).

목표 문장의 세 계열이 **한 모드(`manifest`) 아래에서 모두** 확인된다 — 이것이 1점과 2점을 가르는 지점이다:

| 목표 문장 요소 | S-19의 검증 지점 | 판정 |
|--------------|----------------|------|
| 조회 지배 | (e) `scan --json` 결과에 인라인 유래 필드 0건 = 두 소스 혼재 0건 | 충족 |
| 작성 판정 지배 | (b) `scaffold` 매니페스트가 include 집합과 정확히 일치 · (c) `target`이 A=`manifest`/형제=`out_of_scope` | 충족 |
| 검증 지배 | (d) `validate` `ok: true` — 형제 미등재를 위반으로 안 잡음 | 충족 |
| 혼재 디렉토리 지원 | `mixed-scope` 픽스처 = `svc/shared/`에 서비스 A 1파일 + B 3파일, include로 A만 지정 | 충족 |
| 보강⑤ (도구 추측 금지) | (a) `discover` 산출물의 `include`가 빈 배열로 남음 | 충족 |

070 사건형 결함("애초에 그 시나리오가 존재하지 않았다")은 **재발하지 않았다.** S-19는 매핑 표의 형식적 완전성이 아니라 목표 달성 자체를 겨냥한 독립 시나리오이며, 결정론 축이 통과시킨 매핑과 별개로 실체가 있다.

**2점을 유지한 이유 / 1점으로 내리지 않은 이유**

1점 앵커는 "일부 경로만 확인하고 목표 달성을 참칭"이다. S-19는 세 계열 중 어느 하나도 빠뜨리지 않았으므로 참칭이 아니다. 아래 잔여 관찰은 목표 검증의 **깊이** 문제이지 존재 여부 문제가 아니므로 감점하지 않았다(§3 비차단 관찰 ①②).

---

### ⑤ 채택/잔존 — **1점**

이 태스크는 **교체형**이다. 구형 2종이 제거된다 — `headerSource: auto`(D-3, 완전 제거) · 스코프 키 `readonly`(D-2, 제거 후 `manifest` 동의어 하위호환). 따라서 본 축이 가장 강하게 적용된다.

**`readonly` 잔존 — 검증 충분 (2점 수준)**

| 잔존 지점 | 검증 시나리오 | 판정 |
|----------|-------------|------|
| 소스 코드 | S-13 "소스에 `readonly`를 판정 근거로 쓰는 코드 0건(`note` 문자열 포함)" | 검증됨 |
| 산출물 문서 | S-18 "`readonly` 판정 근거 서술 0건 (deprecated 표기는 허용)" — 8문서 grep | 검증됨 |
| 도구 산출물 | S-13(b) "`discover` 산출물 `scopes[]`에 `readonly` 키 0건" | 검증됨 |
| 픽스처(레거시 자산) | S-13(a) `readonly: true`만 있는 레거시 index → `manifest` 동일 동작 + deprecated 안내 1줄 | 검증됨 |
| 충돌 우선순위 | S-13(c) `readonly` + `headerSource: inline` 동시 → `inline` 승리 + 무시 안내 | 검증됨 |

**`auto` 잔존 — 검증 부족 (1점 수준). 이것이 본 축의 감점 사유다.**

`auto`에 대해 검증되는 것은 **런타임 거부 1종뿐**이다 — S-20(a) `"headerSource": "auto"` → `header_source_invalid` + `detail:"auto"` + 마이그레이션 힌트 + exit 1.

문서 전량 grep 결과, TEST-SCENARIO.md에서 `auto`를 다루는 행은 §1 H-10(골든 근거 서술) · §2.2 S-2/S-20 조건 · §3 S-2/S-20 본문 · §4 F-1 행뿐이며, **`auto`의 자산 잔존을 grep으로 확인하는 시나리오는 0건**이다. `readonly`가 받은 4중 잔존 검사(소스·문서·산출물·픽스처)를 `auto`는 하나도 받지 않는다. 구체적으로:

- **소스 코드**: `code-scan.js:108`의 `USAGE` 문자열이 설정 예시로 `"headerSource": "auto"`를 노출한다(PLAN §2.1.1 표 2행 · §3.1.1 수정 #6이 갱신 대상으로 명시). 갱신 후 `auto` 잔존 0을 확인하는 시나리오가 없다. S-16은 픽스처의 `headerSource` **존재**만 집계하고 값이 `auto`가 아님을 보지 않으며, S-13의 소스 grep은 `readonly` 전용이다.
- **산출물 문서**: `tools.md`·`header-standard.md` §7·`code-scan-management.md`가 현재 3택(`auto` 포함)을 서술한다. S-18의 grep 검사 목록은 `readonly` 판정 근거 · 개인 식별자 · `reason` 값 · `headerSource` 예시 포함 4종이며 **`auto` 서술 잔존 항목이 없다.** 문서에 `auto`가 남아도 S-18은 통과한다.

**추가 결함 — 파기된 계약과 시나리오의 모순 1건**

PLAN §1.5 계약 변경표(`PLAN.md:74`)는 `target` `reason` 도메인을 `header_source_inline`/`header_source_manifest`/`out_of_scope` **3값**으로 확정하고, §3.2.2 (C-bis)(`PLAN.md:619, 809`)가 "실제 조합은 3쌍으로 닫힌다"고 못박는다. S-9는 실제로 `reason: 'out_of_scope'`를 단언한다.

그런데 **S-18의 기대 결과는 "`reason` 2값 표기"** 이고(`TEST-SCENARIO.md:88, 409`, §4 F-3 행 비고도 "reason 2값"), 그 근거인 PLAN Step 11(`PLAN.md:1083`)·TS-053(`PLAN.md:1149`)은 `header-rules.md`에 "`reason`은 이 2값 외를 반환하지 않는다"를 쓰도록 지시한다. 즉 S-18은 **구현이 3값을 반환하는데 문서가 2값 폐쇄 도메인을 선언하는 상태를 통과시킨다.** 077이 남긴 결함(`header-rules.md:25` "이 4값 외를 반환하지 않는다"가 구현과 어긋남 → H-6)과 **동형의 문서·코드 불일치를 새로 고정하는** 시나리오다. 신형 계약의 정확한 채택을 검증해야 할 시나리오가 오히려 부정확한 채택을 승인한다.

**0점이 아닌 이유**: 신형 채택은 광범위하게 검증된다 — S-8(target 2모드) · S-10(scaffold inline no-op) · S-11(validate 2모드 + `result.headerSource` 필드) · S-21(우선순위 3층) · S-4(`scopes` 객체 형식 + 문자열 20종 하위호환) · S-14/S-15(이 저장소 자신의 실채택 + gitignore 예외). 구형 거부도 런타임 수준에서는 성립한다. 따라서 "미검증"(0점)이 아니라 "부분 검증"(1점)이다.

---

### ⑥ 경계/부정 — **2점**

부정·경계 경로가 **정상 경로 대비 충분한 비중**으로 존재한다. dispatcher가 지목한 7개 관점을 전수 대조했다:

| 요구된 부정 경로 | 시나리오 | 판정 |
|----------------|---------|------|
| 미설정 거부 | S-1 — 13커맨드 전량 exit 1 + `header_source_unset` + stderr 3줄 | 존재 |
| `auto` 명시 거부 | S-20(a) | 존재 |
| 깨진 설정 파일 ↔ 미설정 **구분** | S-20(b) `code_scan_config_invalid`로 구분 | 존재 |
| 스코프 양쪽 매칭 모호성 거부 | S-5(b) `scope_ambiguous` exit 1 | 존재 |
| include 탈락 파일 `out_of_scope` | S-9(a) — `{write_to:'none', reason:'out_of_scope'}` + `scope`/`manifest`/`key` **필드 부재**까지 단언 | 존재 (강함) |
| `manifest` 모드 + index 부재 fail-soft | S-12 — stderr 경고 1줄 · exit 0 · stdout JSON 무오염 | 존재 |
| hook 무출력 이탈 | S-2(3케이스) + S-9(b) `write_to !== 'manifest'` 이탈 경로 | 존재 |

추가로 커버된 부정·경계: S-1의 `--help`/`--version` 게이트 이전 예외 · S-7의 오탐/미탐 **양방향**(검출기가 필터로 무력화되지 않음) · S-9(c) 미사용 프로젝트 `out_of_scope` 오발동 0건 · S-13(c) 충돌 우선순위 · S-21의 CLI가 스코프를 못 이기는 음의 단언 · S-15 gitignore 반전.

**주목할 품질 신호**: S-9는 "무엇이 반환되는가"뿐 아니라 "무엇이 **없어야** 하는가"(`scope`/`manifest`/`key` 필드 부재)를 단언한다. S-3도 `_source` 키 0건을 단언한다. 부정 단언(negative assertion)이 설계되어 있다는 것은 경계 축이 형식적으로 채워진 것이 아님을 보여준다.

**2점을 유지한 이유**: 0점 앵커는 "정상 경로만", 2점 앵커는 "경계·부정 경로 시나리오 존재"다. 위 13종 이상은 앵커를 명백히 초과한다. 미커버 3종(§3 비차단 관찰 ③④⑤)은 **무효 입력값 거부**라는 단일 계열의 확장 누락이며, 그 계열의 대표 케이스(`auto`·깨진 JSON)는 이미 커버되어 있다. 계열 자체의 부재가 아니므로 감점하지 않았다.

---

## 2. 자동화 회피 · mock 금지 점검 (감점 사유 없음)

| 점검 | 결과 |
|------|------|
| L3/M3 비중 | 22건 중 1건(S-22)만 M3. 나머지 21건 전량 M1 |
| S-22가 자동화 회피인가 | **아니다.** hook **로직**은 S-2가 stdin 이벤트 주입으로 이미 자동 검증한다(3케이스). S-22가 남긴 것은 실 AI 편집 세션의 PostToolUse 통합 — 테스트 프로세스 내부에서 재현 불가한 영역이다. §3.0 판정표와 S-22 본문("stdin 주입 테스트(S-2)는 hook 로직을 검증하지만 실세션 통합은 검증하지 못한다")이 분리 근거를 명시했고, [SUPERVISOR] 마커 + PM 표준 요청 양식도 첨부되어 있다 |
| M2 면제 | 정당. FE 화면·인증·외부 API 연동 변경 0건(§3.0). 대상은 Node CLI 2개 + 문서 8종 + 테스트 자산 |
| mock/patch/가짜 응답 | 시나리오 본문 grep 결과 **0건**. 전량 실 픽스처(저장소 커밋 자산) + 실 CLI subprocess + 실 `brain-tool` subprocess + `git check-ignore` 실측 |

---

## 3. 잔여 관찰 (비차단 — 점수에 반영하지 않음)

재작성 루프를 다시 돌릴 사유는 아니나, 구현·테스트 단계에서 흡수하면 방어력이 오르는 항목이다.

① **`inline` 모드의 E2E 워크플로 시나리오가 없다.** S-19는 `manifest` 모드만 관통한다. `inline` 측은 S-3(조회)·S-8(target)·S-10(scaffold)·S-11(validate)로 부품 단위 분산 검증된다. "한 키가 전 경로를 지배한다"의 가장 날카로운 형태 — **동일 픽스처에서 `headerSource`만 뒤집으면 5경로가 함께 뒤집힌다** — 를 단일 시나리오로 보이는 대조 케이스는 부재하다. S-11이 `validate` 한 경로에서만 이 대조를 수행한다.

② **`manifest` 모드에서 조회 8커맨드 전량이 실행되지 않는다.** S-3·S-17의 8커맨드 실행·골든 대조는 `legacy-repo`(code-map 부재, `inline`) 기준이다. H-3(`getSearchPaths` 반환 타입 변경 → 조회 8커맨드 전체 경유)은 `inline` 모드에서만 방어된다. S-19는 `manifest`에서 `scan` 1개만 실행한다. 열거 지점(`discoverFiles`)이 S-6의 5지점 교차 비교에 포함되어 부분 완화되나, 나머지 7커맨드의 `manifest` + include 조합 출력은 미확인이다.

③ **CLI 무효값 거부 시나리오 부재.** PLAN §3.1.2 (C) 판정 순서 ③(`PLAN.md:408`)이 `opts.headerSource` 무효 → `header_source_invalid` (`where: 'cli'`) 분기를 정의하나, 이를 겨냥한 시나리오가 없다. S-20은 config의 `auto`만, S-21은 유효값 조합만 다룬다. §6 보안 체크 4번("2택 화이트리스트 검증")에 항목으로만 존재하며 이는 시나리오가 아니다.

④ **077 TS-046 반전이 `auto` 케이스로만 승계됐다.** PLAN §1.5(`PLAN.md:78`)는 077 TS-046(`headerSource:"bogus"` → `auto` 폴백 + exit 0)의 반전을 계약 변경으로 선언하고 "본 PLAN TS-003이 승계"라 했으나, TS-003/S-20이 다루는 값은 `auto`뿐이다. `auto`는 전용 마이그레이션 힌트 경로(⑤ 분기의 특례)이고 임의 무효값은 일반 경로이므로, **일반 무효값 거부 분기가 시나리오로 방어되지 않는다.**

⑤ **`scopes` 객체 형식의 스키마 위반 거부 시나리오 부재.** S-4는 객체 형식이 스키마 검증을 **통과**하는 것만 본다. `include`가 배열이 아닌 경우, `path` 누락 등 위반 입력의 거부는 미검증이다. 기존 `fixtures/schema/` 4종은 index 스키마 위반이며 include/exclude 도메인과 무관하다.

⑥ **정규화 페이로드의 `is_goal_scenario` 플래그가 문서와 불일치한다.** `.scenario-coverage-input.json`은 S-14·S-19·S-22 **3건**을 `is_goal_scenario: true`로 표기했으나, TEST-SCENARIO.md §3·§4가 목표달성 시나리오로 선언한 것은 **S-19 단독**이다(S-14는 소비자 파급, S-22는 hook 실세션). 결정론 축 판정에는 영향이 없으나, 목표 시나리오 수를 부풀리는 표기는 070형 결함을 가리는 방향으로 작동한다. 본 채점은 문서(TEST-SCENARIO.md)를 기준으로 삼아 S-19만 목표 시나리오로 인정했다.

---

## 4. 종합 판정

| 항목 | 값 |
|------|-----|
| ① 목표 달성 (goal) | **2** |
| ⑤ 채택/잔존 (adoption) | **1** |
| ⑥ 경계/부정 (boundary) | **2** |
| 평균 | **1.67** |
| 0점 축 | 없음 |

**임계 대조** (`scenario-gate.md` §5-1): 판단축 각 ≥ 1점 → 충족(최저 1점) · 평균 ≥ 1.5점 → 충족(1.67)

### verdict: **pass**

결정론 축(②③④)이 `scenario-coverage-check` exit 0로 이미 통과했으므로, `scenario-gate.md` §6 tool-gated 집행의 두 증거가 모두 성립한다.

**단, ⑤축 1점은 통과선 최저값이다.** 아래 gaps는 게이트 재루프 사유는 아니나 EXECUTE 진입 전에 흡수할 것을 권고한다 — 특히 gap-2(S-18의 `reason` 2값 문서 계약)는 **시나리오가 잘못된 계약을 승인하는 형태의 결함**이므로 구현 전에 정정하지 않으면 077 H-6과 동형의 문서·코드 불일치가 재생산된다.

### gaps

1. **`auto` 잔존이 자산 계층에서 미검증** — S-20은 `auto` 설정의 **런타임 거부**만 본다. `readonly`가 받은 4중 잔존 검사(S-13 소스 grep · S-18 문서 grep · S-13(b) 산출물 · S-13(a) 픽스처)를 `auto`는 하나도 받지 않는다. 필요한 것: (a) S-18의 grep 목록에 "`auto`를 유효값으로 서술하는 문장 0건" 항목 추가 — 대상은 `tools.md` · `header-standard.md` §7 · `code-scan-management.md`, (b) 소스 잔존 검사 추가 — `code-scan.js`의 `USAGE`(`:108` 설정 예시)와 `DEFAULT_CONFIG`에 `auto` 리터럴 0건.
2. **S-18이 `reason` 도메인을 2값으로 검사하여 구현(3값)과 모순** — S-18 기대 결과의 "`reason` 2값 표기"(`TEST-SCENARIO.md:88, 409`)와 근거 TS-053(`PLAN.md:1149`)은 `header-rules.md`에 "이 2값 외를 반환하지 않는다"를 쓰게 하나, PLAN §1.5(`:74`)·§3.2.2 (C-bis)(`:619, 809`)의 확정 도메인은 `out_of_scope`를 포함한 **3값**이며 S-9가 실제로 이를 단언한다. S-18을 "`reason` 3값(`header_source_inline`/`header_source_manifest`/`out_of_scope`) 표기 + `write_to` 3값(`inline`/`manifest`/`none`) 표기"로 정정해야 한다. 현 상태로 두면 S-18은 문서가 거짓 폐쇄 도메인을 선언한 상태를 통과시킨다.
3. **무효 입력값 거부 계열의 일반 케이스 미커버** — (a) `--header-source <무효값>` CLI 거부(PLAN §3.1.2 (C) ③ `where: 'cli'` 분기, `PLAN.md:408`)와 (b) config의 임의 무효값(`bogus` 등, 077 TS-046 반전 대상, `PLAN.md:78`)이 시나리오로 방어되지 않는다. S-20에 두 케이스를 추가하거나 별도 시나리오로 분리할 것. `auto`는 마이그레이션 힌트가 붙는 특례 경로이므로 일반 무효값 경로를 대신하지 못한다.

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-08-01 13:36 | 최초 채점 — scenario-rubric 판단축 3종(①⑤⑥) 1회차, verdict pass (goal 2 / adoption 1 / boundary 2, 평균 1.67) (080) |
