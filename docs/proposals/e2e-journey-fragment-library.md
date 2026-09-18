# 제안: `//e2e` operator와 여정·조각 라이브러리

> 상태: 검토 | 작성: 알투(PM) | 작성일: 2026-09-15 | 확정 반영: 2026-09-18
> 선행본: `docs/proposals/archives/opal-e2e-harness.md`(적용완료, 태스크 125·127) — 그 구현에서 실측된 제약이 이 제안의 근거다
> 발단: 태스크 127(E2E 하네스 구현) 수행 중 캡틴 제기 — "TEST-SCENARIO+TEST가 이미 긴 단계인데 E2E까지 넣으면 더 느려진다"

## 1. 문제

E2E를 기존 TEST 단계에 끼워 넣으면 태스크마다 시나리오를 **처음부터 새로 쓰고** 매번 **전수 재실행**한다. 느려지는 원인은 호출 시점이 아니라 이 둘이다.

여기에 태스크 127에서 **실측으로 확인된 제약** 둘이 더해진다.

| # | 실측 사실 | 귀결 |
|---|---|---|
| 1 | `test-scenario.json`은 `scenario-lock` 이후 spec존 변경이 불가하고, `scenario-init`을 다시 부르면 `red_confirmed`가 전건 초기화되어 잠금이 영구 차단된다 | **태스크 캡슐 안에는 사후에 E2E 시나리오를 추가할 수 없다.** 프로젝트 레벨 저장소가 선택이 아니라 필연이다 |
| 2 | `e2e run`은 `--scenario <id>`로 id만 받아 `test-scenario.json`에서 찾을 뿐이고, 시나리오를 만드는 수단이 없다 | 작성은 전부 도구 **밖**에서 사람·PM이 해야 한다. 발동층이 없다 |

태스크 127에서 AC-4·AC-9·S-26·S-27을 검증할 때 전부 임시 폴더에 fixture 시나리오를 따로 만들어 돌린 이유가 이것이다.

## 2. 해법 요약

| 축 | 내용 |
|---|---|
| 발동 | **`opal-e2e`** operator 스킬(alias `//e2e`) — 단계 파이프라인·워커 디스패치 없음. `//opbr`·`//oppm`·`//opas`와 같은 유형 |
| 모드 | `author`(대화로 작성) · `import`(TEST-SCENARIO.md 변환) · `run`(실행) · `status`(조회) |
| 저장 | 3폴더 — **추적 여부가 폴더로 갈린다**(§3) |
| 재사용 | **조각(fragment)** — 이름 붙은 step 시퀀스 + 파라미터 + **사후 조건** |
| 범위 축소 | **신선도 키** — `(여정 해시, 조각 해시, surface_id, 대상 commit)` |
| 확장 | **선언형 driver wrapper** — 새 브라우저는 JSON 한 장(§7) |
| 협동 | 기존 `collaborative` profile·`awaiting_human`(exit 20)·resume token 재사용. 신규 구현 없음 |

## 3. 폴더 구성 — 가르는 축은 **git 추적 여부**다

```
docs/e2e/                      ← 추적. 사람 소유, 리뷰 대상
  README.md                    조각 목록 인덱스·작성 규칙
  fragments/                   재사용 블록 (그 자체로는 목적이 아닌 것)
    login.md  logout.md  add-to-cart.md  seed-fixture.md
  journeys/                    사용자 여정 (사용자가 달성하려는 것)
    login-to-checkout.md  guest-browse.md

.opal/e2e/                     ← 추적. OPAL 설정
  drivers/                     선언형 driver 매니페스트 (§7)
    ego-lite.json  agent-browser.json  cmux.json
  order.json                   후보 우선순위 — 코드 상수 대신 여기서 재정의

.e2e/                          ← **전량 git 무시**. 버려도 되는 것만
  freshness.json               신선도 원장
  scratch/                     일회성·초안 (버리는 게 기본값)
  artifacts/<run-id>/          실행 산출물 (보존 정책: 최근 N개)

(태스크)/e2e/                   ← 태스크 작업 공간. CLOSE에서 docs/e2e/로 승격
```

### 왜 이렇게 나누나

- **`.gitignore`가 `.e2e/` 한 줄로 끝난다.** 예외 등록(`!` 규칙) 방식은 새 파생물이 생길 때마다 규칙을 추가해야 하고 한 번 빠뜨리면 조용히 커밋된다. 선례가 정확히 이 꼴이다 — `.oppl-run/`이 `.gitignore:41`에 폴더 단위로 등재돼 있다(태스크 127 AC-16).
- **설정은 팀이 공유해야 재현된다.** "Ego Lite를 1순위로" 가 로컬에만 있으면 다른 사람·CI는 다른 순서로 돌고 "내 환경에선 됐는데"가 생긴다. 그래서 `drivers/`·`order.json`은 `.opal/e2e/`(추적)에 둔다.
- **`.e2e/artifacts/`를 로컬 기본 산출물 경로로 둔다.** 현재 기본값 `${TMPDIR}/opal-e2e-runs`는 실패 시 `/var/folders/...`를 뒤져야 해 원인 추적이 번거롭다. `.e2e/`는 전량 무시이므로 여기 써도 `git status`가 더러워지지 않고 태스크 127 AC-13(저장소 무오염)도 깨지지 않는다. **보존 정책(최근 N개)이 반드시 따라야 한다** — 없으면 디스크가 계속 붇는다.

### 단일 소유 — 같은 내용을 두 벌 두지 않는다

초안에서 제안했던 "`docs/e2e/`(사람) + `.opal/e2e/`(도구 시드 JSON)" 2층 분리는 **철회한다.** 그 분리의 선례인 `TEST-SCENARIO.md` → `test-scenario.json`에는 이유가 있었다 — 후자가 3-SSOT tool-gated 파일이고 RED 동결 의미를 갖는다. `docs/e2e/`에는 그런 잠금이 없으므로, 잠금 없는 2층은 drift 위험과 시드 도구 유지비만 남긴다(PRINCIPLES §2 "단일 용도에 추상화를 만들지 않는다").

**여정·조각은 `docs/e2e/`에 한 벌만 두고 도구가 직접 읽는다.** `.opal/e2e/`·`.e2e/`에는 사람이 편집하지 않는 것(매니페스트·설정·원장·산출물)만 들어간다.

### 나누는 기준

- `fragments/`는 **그 자체로는 목적이 아닌 것**(로그인, 장바구니 담기, 픽스처 시드), `journeys/`는 **사용자가 달성하려는 것**.
- **참조는 단방향이다** — 여정만 조각을 참조하고 조각은 여정을 모른다. 순환이 구조적으로 생기지 않는다.
- 파일은 태스크가 아니라 **여정·조각 단위**로 나눈다. 태스크 단위면 태스크가 끝날 때 고아가 되어 누적 스위트가 되지 않는다.

### 태스크와 일회성

| 경우 | 경로 |
|---|---|
| 태스크 수행 중 | `(태스크)/e2e/`에 작성·실행. 기존 조각을 참고해 재사용한다. **CLOSE에서 실제로 통과한 것만** `docs/e2e/`로 승격하며, 이때 조각화 검토(같은 step 시퀀스가 두 여정에 반복되면 `fragments/`로 추출)를 함께 한다 |
| 태스크 아님(일회성) | **태스크를 강제 생성하지 않는다.** `.e2e/scratch/`에 쓰고 돌린다. "로그인 한 번 돌려보고 싶다"에 태스크 폴더·`state.json`·파이프라인이 붙으면 아무도 쓰지 않는다 |
| 일회성 결과가 코드 수정을 부를 때 | 그때 **태스크 생성을 제안**한다. 태스크 생성은 강제가 아니라 에스컬레이션 경로다 |

## 4. 조각 계약

조각은 매크로가 아니라 **검증되는 블록**이다.

```yaml
id: login
params: [id_ref, pw_ref, entry_url]      # 값이 아니라 참조
steps:
  - {kind: navigate, value: "{entry_url}"}
  - {kind: click,    target: "header a.login"}
  - {kind: fill,     target: "#id", value_ref: "{id_ref}"}
  - {kind: fill,     target: "#pw", value_ref: "{pw_ref}"}
  - {kind: click,    target: "button[type=submit]"}
postconditions:                           # [MUST] 없으면 등록 불가
  - {verifier: url,      expected: "/dashboard",  match: equals}
  - {verifier: dom_text, target: ".user-name", expected: "{id_ref}", match: equals}
```

- **[MUST] 사후 조건이 없는 조각은 등록하지 않는다.** 없으면 로그인이 조용히 실패한 채 뒤 여정이 통과한다. 이것이 조각을 단순 재생 매크로와 다르게 만드는 지점이다.
- **[MUST] 자격증명을 조각에 직접 적지 않는다.** `value_ref`로 환경변수·시크릿 파일만 참조한다. 근거: 태스크 127 실측 — `fill`의 value는 C-6 redaction 대상이 **아니어서** `actions.jsonl`에 원문으로 남는다. **이 구멍을 막는 것이 조각 도입의 선행 조건이다.**
- **[MUST] 전개 결과는 `actions.jsonl`에 실제 연산 단위로 남긴다.** `login` 한 줄만 남으면 증적이 무엇을 했는지 말하지 못한다.
- `match`는 `equals`를 쓴다. 태스크 127 실측 — `contains`는 `validate_pass_requirements`의 직접 비교(§A.5)에 걸려 `pass`에 도달할 수 없다.

## 5. 신선도 키

구성: `(여정 해시, 참조 조각 해시 집합, surface_id, 대상 commit)`. **휘발성 값(`run_id`·타임스탬프·포트)은 넣지 않는다** — 넣으면 영원히 일치하지 않아 무용지물이다.

재실행 생략은 아래 4개를 **모두** 만족할 때만 허용한다.
1. 대상 commit 동일  2. 여정·조각 해시 동일  3. 이전 결과가 `pass`  4. 증적이 실제로 남아 있음

**[MUST] 생략을 "미실행"이 아니라 "이전 증적 재인용"으로 기록하고 DONE.md에 보이게 남긴다.** 이 장치가 없으면 신선도 키는 검증을 조용히 건너뛰는 가장 세련된 방법이 된다 — 태스크 070 실패모드가 정확히 그 형태였다.

조각 해시가 바뀌면 그 조각을 참조하는 **모든 여정의 신선도가 무효**가 된다. "로그인 절차가 바뀌었으니 로그인을 쓰는 12개 여정만 재실행"이 결정론으로 나온다.

> **명명 주의**: OPAL은 `fingerprint`를 이미 두 의미로 쓴다 — `gc-finding-schema.md`(중복 판정 해시)와 `oppl-runtime-tool`(실패 지문). 세 번째 의미를 만들지 않기 위해 이 문서는 **조각(fragment)** 과 **신선도 키(freshness key)** 로 부른다.

## 6. 스킬 — `opal-e2e` (alias `//e2e`)

`opal-brain`(`//opbr`)이 `init`/`ingest`/`query`/`lint` 4모드 라우터인 선례를 그대로 따른다.

| 모드 | 동작 |
|---|---|
| `author` | 캡틴과 대화하며 여정·조각을 작성한다. **끝에 사용자 확인 게이트를 둔다** — 대화로 만든 단언은 사람이 확인하지 않은 채 굳을 수 있다. 자격증명은 `value_ref`로만 받는다 |
| `import` | `TEST-SCENARIO.md`를 읽어 변환한다. 표 형식이라 `kind`·`target`·`verifier`를 담기 비좁으므로 **뽑을 수 있는 것만** 옮기고 나머지는 `author`로 보완하는 2단이다 |
| `run` | `test-tool e2e run`을 호출하고 결과를 해석한다 |
| `status` | 신선도 원장·표면 커버리지·최근 run을 조회한다(읽기 전용) |

**[MUST] 판정은 스킬이 하지 않는다.** 스킬이 시나리오를 쓰고 스스로 돌리고 스스로 합격을 선언하면 **생성자=평가자**가 되어 독립 검증 경계를 깬다. 판정은 `test-tool`의 exit 계약(0/6/7/18/19/20)이 소유하고 스킬은 **호출과 해석만** 한다.

### 발동 시점

| 시점 | 동작 |
|---|---|
| 평시 | 캡틴이 `//e2e` 수동 호출 |
| CLOSE 진입 | **조건부** 확인 — 이번 변경이 사용자 접촉 표면을 건드렸을 때만 `real-usage` 증거를 요구 |

새 규범을 만드는 것이 아니다. oppl `verification.md` §1.5.3이 이미 "사용자 접촉 표면·여정은 `real-usage` PASS ≥1 없이 done을 인정하지 않는다"를 [MUST]로 규정한다 — 이 제안은 **있는 규범에 집행 지점을 주는 것**이다. 표면을 건드리지 않은 문서·설정 태스크는 그대로 통과한다.

**비동기 실행은 채택하지 않는다.** "CLOSE를 막지 않고 백그라운드로 돌려 나중에 귀속"은 done 판정이 증거 도착 전에 나가므로 070 실패모드를 재현한다. 느리면 범위를 줄이지, 판정을 앞당기지 않는다.

## 7. 선언형 driver wrapper — 새 브라우저를 JSON 한 장으로

### ADD-1 실증 — Ego Lite가 1호 사례가 됐다

태스크 127 ADD-1에서 `ego-lite`를 실제로 driver 계약에 흡수했고, 그 과정에서 이 절의 전제
두 개가 **실측으로 확인됐다.**

| 확인된 사실 | 이 절에 미치는 영향 |
|---|---|
| 새 driver 추가에 실제로 4곳 수정이 필요했다 — `drivers/ego_lite.py`(234줄) · `_BUILTIN_DRIVER_MODULES` · `manifest.json` · `CANDIDATE_ORDER` + **`CONTRACT.md` 3곳 개정**(driver enum 2 + C-DRV-3) | 선언형 wrapper의 동기가 과장이 아니다. 계약 개정까지 끌려 들어간다 |
| **부분 driver가 생긴다** — `ego-browser-tool`의 `smoke`는 open+텍스트 assert 융합이라 `act`·`wait`·`snapshot`·`capture`를 제공하지 않는다 | §A.8.1 capability 6키로는 "이 시나리오가 `act`를 쓰는가"를 표현할 수 없다. **ops 기반 게이트가 없으면 부분 driver를 1순위에 둘 수 없다**(Q-6) |
| 순서를 전제한 단언 8건이 즉시 깨졌다 | 선언형 등록으로 추가 문턱을 낮추면 이 파손이 잦아진다. 단언을 **정체 기반**(`_record(candidates, driver, session_mode)`)·**MV-38 형태**로 쓰는 규칙이 함께 필요하다 |

**이미 열린 접합점**: `resolve_candidates(candidate_order=...)`가 ADD-1에서 구현됐다. 순서는
코드 상수 `CANDIDATE_ORDER`가 **기본값**일 뿐이고 호출자가 재정의할 수 있다. 아래 `order.json`은
그 인자에 파일 입력을 연결하는 작업으로 축소됐다.

### 현재 문제

새 driver 추가에 4곳 수정이 필요하다 — `drivers/<name>.py`(8연산 파이썬) + `_BUILTIN_DRIVER_MODULES` + `manifest.json` + `CANDIDATE_ORDER`(+ C-DRV-3 계약 개정). agent browser 제품이 빠르게 늘고 있는데 시도 비용이 너무 높다.

### 제안

대부분의 agent browser CLI는 **서브명령 이름만 다르다.** 그러면 매니페스트 한 장으로 등록할 수 있다.

```json
{ "driver": "ego-lite", "session_mode": "standalone",
  "binary": {"env": "OPAL_E2E_EGO_BIN", "discover": ["ego", "/Applications/…"]},
  "version": {"argv": ["--version"]}, "minimum_version": "0.1.0", "tested_range": "0.1.x",
  "ops": { "probe":  {"argv": ["session","list"]},
           "open":   {"argv": ["open","{url}"]},
           "act":    {"map": {"click": ["click","{target}"], "fill": ["fill","{target}","{value}"]}},
           "assert": {"argv": ["eval","{script}"], "verifiers": ["dom_text","url","title"]},
           "capture":{"argv": ["screenshot","{path}"]},
           "close":  {"argv": ["tab","close"]} },
  "capabilities": {"screenshot": "probe", "console": "none"} }
```

공용 `DeclarativeDriver`가 이 매니페스트를 읽어 §B.2 8연산을 이행한다. **새 브라우저 = `.opal/e2e/drivers/`에 JSON 한 장.**

- **우선순위도 데이터로**: `.opal/e2e/order.json`을 `resolve_candidates(candidate_order=...)`에 연결한다. **주입 인자와 C-DRV-3의 "기본 순서 + 재정의 가능" 개정은 ADD-1에서 이미 끝났다** — 남은 것은 파일 입력 경로다. 그러면 "새로 넣은 걸 1순위로"가 설정 한 줄이 된다.
- **[MUST] 부분 driver를 1순위에 두려면 Q-6(ops 게이트)이 선행한다.** ADD-1은 그 게이트가 없어 `ego-lite`를 뒤로 배치했다 — 앞에 두면 UI 조작 시나리오에서도 먼저 `selected`되고 실행 도중 `driver_operation_unimplemented`로 `blocked`가 되어 더 완전한 driver를 가린다.
- **탈출구 유지**: 선언형으로 표현 안 되는 driver(특수 프로토콜)는 지금처럼 파이썬 모듈로 둔다. **선언형이 기본, 코드가 예외**인 2단 구조다.
- **전환 조건은 바뀌지 않는다**: 순서를 바꿔도 C-3·`can_try_next_provider()`가 `provider_unavailable`에서만 다음 후보로 넘어가고 `infra_error`·제품 실패에서는 넘어가지 않는다.

### [MUST] 적합성 스위트가 반드시 따라야 한다

`test-tool e2e driver-verify --driver <name>`이 8연산 이행을 **실제 실행으로** 검사해야 한다.

근거: 태스크 127에서 `agent_browser`가 `probe`·`open`·`close` **3연산만 구현하고도 자체 테스트 30건을 통과**해 AC-4를 구조적으로 막았다(통합 지점에서만 드러났다). "JSON 한 장으로 추가"를 열면 그 사고가 훨씬 쉬워진다. 등록 문턱을 낮추는 만큼 **이행 검사를 도구가 강제**해야 한다.

## 8. 기존 자산과의 접합

| 자산 | 관계 |
|---|---|
| `test-tool e2e run\|resume\|status\|clean` | 실행·판정 주체. 이 제안은 입력을 공급할 뿐 실행 계약을 바꾸지 않는다 |
| `collaborative` profile·`awaiting_human`·resume token | 협동 수행에 그대로 쓴다. 태스크 127에서 실측 관통 완료(exit 20 → resume → 사람 제출 단독으로는 `fail`) |
| `surfaces.json` | 표면 SSOT. 이 제안이 복제하지 않는다 |
| `scenario-conformance` | 여정 커버리지 판정에 재사용 |
| `FIDELITY_ORDER`(`lib/scenario.py:119`) | 충실도 정의 단일 소유. 이 제안은 참조만 한다 |

## 9. 열린 쟁점

| # | 쟁점 | 메모 |
|---|------|------|
| Q-1 | 조각 전개분과 본문 연산의 **중복 판정 충돌** | 동결 RED S-27 (d-1)이 같은 연산 signature 중복을 재시도로 판정한다. 태스크 127에서 `--version` 2회가 실제로 이 규칙에 걸려 browser step runner가 봉쇄됐다가 driver 인스턴스 메모이즈로 해소됐다. 조각이 `navigate`를 포함하고 본문도 쓰면 재발한다 — **전개분과 본문을 구분 집계**하거나 중복 판정 범위를 좁혀야 한다 |
| Q-2 | 로그인 **세션 재사용** 여부 | 조각과 별개 축이다. 현재 세션·프로필이 `opal-e2e-{run_id}`라 run마다 새로 만들어진다(`agent_browser.py:334,353`). 지속 프로필을 도입하면 로그인 반복이 사라지지만 **로그인 자체가 미검증**이 된다 — 로그인 여정만 주기적 cold 실행으로 분리하는 보완이 필요하다 |
| Q-3 | `.e2e/artifacts/` **보존 정책** | 최근 N개 유지가 기본. N과 용량 상한을 정해야 한다 |
| Q-4 | ~~Ego Lite driver 편입~~ → **해소(ADD-1)** | `drivers/ego_lite.py`로 흡수 완료. `probe`·`open`·`assert`·`close` 구현, 나머지 4연산은 `probed=true`·`available=false`로 없음 선언. 후보 순서는 `agent-browser` → `cmux` → `agent-browser/standalone` → `ego-lite` → `playwright(opt-in)` |
| Q-6 | **ops 기반 후보 게이트** (신설, ADD-1 발) | 시나리오 step에서 요구 연산(`act`·`wait`·`snapshot`·`capture`)을 뽑아 그것을 제공하지 않는 후보를 **실행 전에** 거르는 장치. 현재 게이트는 capability(§A.8.1 6키)만 보고 연산 요구를 표현할 수 없다. **이것이 없으면 부분 driver를 1순위에 둘 수 없고, 선언형 wrapper로 추가 문턱을 낮출 때 부분 driver가 늘어나 위험이 커진다** — §7의 선행 조건이다 |
| Q-7 | **순서 의존 단언 규칙** (신설, ADD-1 발) | 새 후보를 넣자 순서를 전제한 단언 8건이 깨졌다. 정체 기반 조회와 MV-38 형태(`infra_error` 원소보다 큰 `order` 부재)를 테스트 작성 규칙으로 명시해야 선언형 등록이 안전해진다 |
| Q-8 | `.e2e/` **이름 충돌** | 프로젝트가 Playwright·Cypress 설정에 같은 이름을 쓸 가능성. 전량 무시 폴더라 피해는 작다. 걸리면 `.opal-e2e/`가 대안 |
| Q-9 | `import` 모드의 한계 | `TEST-SCENARIO.md`가 표 형식이라 실행 필드를 담기 비좁다. 여정 명세를 표가 아니라 **블록 형식**으로 두는 편이 낫다 |
