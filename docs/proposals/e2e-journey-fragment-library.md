# 제안: E2E 여정·조각 라이브러리와 `//e2e` operator

> 상태: 미적용 제안 | 작성: PM | 작성일: 2026-09-15
> 발단: 태스크 127(E2E 하네스 구현) 수행 중 캡틴 제기 — "TEST-SCENARIO+TEST가 이미 긴 단계인데 E2E까지 넣으면 더 느려진다"

## 1. 문제

E2E를 기존 TEST 단계에 끼워 넣으면 태스크마다 시나리오를 **처음부터 새로 쓰고** 매번 **전수 재실행**한다. 느려지는 원인은 호출 시점이 아니라 이 둘이다.

추가로 태스크 127에서 실측된 구조적 제약이 있다 — `test-scenario.json`은 RED 동결 후 spec존 변경이 불가하다(`scenario-init` 재호출 시 `red_confirmed` 전건 초기화). **태스크 캡슐 안에는 사후에 E2E 시나리오를 추가할 수 없다.** 프로젝트 레벨 저장소가 선택이 아니라 필연인 이유다.

## 2. 해법 요약

| 축 | 내용 |
|---|---|
| 발동 | `//e2e` operator 스킬(단계 파이프라인·워커 디스패치 없음 — `//opbr`·`//oppm`·`//opas`와 같은 유형) |
| 저장 | `docs/e2e/`(사람 소유 명세) + `.opal/e2e/`(도구 소유 실행 스펙·원장) 2층 |
| 재사용 | **조각(fragment)** — 이름 붙은 step 시퀀스 + 파라미터 + 사후 조건 |
| 범위 축소 | **신선도 키** — `(여정 해시, 조각 해시, surface_id, 대상 commit)` |
| 협동 | 기존 `collaborative` profile·`awaiting_human`(exit 20)·resume token 재사용 |

## 3. 폴더 구성

```
docs/e2e/                         # 사람이 쓰고 읽는다. PROJECT.md 레지스트리에 등재
  README.md                       # 작성 규칙·조각 목록 인덱스
  fragments/                      # 재사용 블록 — 여정이 아니라 조각
    login.md                      # 로그인 5-step + 사후 조건
    logout.md
    add-to-cart.md
    seed-fixture.md               # setup 성격(step_role=setup)
  journeys/                       # 사용자 여정 — 조각을 조립한다
    login-to-checkout.md
    guest-browse.md
    admin-task-board.md
  surfaces/                       # 여정↔표면 매핑(선택). surfaces.json은 여전히 SSOT
    README.md

.opal/e2e/                        # 도구 소유. 손편집 금지
  fragments.json                  # docs/e2e/fragments/*.md 에서 시드
  journeys.json                   # docs/e2e/journeys/*.md 에서 시드
  freshness.json                  # 신선도 원장 — 무엇이 어느 commit에서 green이었나
```

**실행 산출물은 어느 쪽에도 두지 않는다** — OS 임시 경로 또는 `OPAL_E2E_ARTIFACT_DIR`이다(태스크 127 C-5). `.opal/e2e/`에는 스펙과 원장만 둔다. 그러지 않으면 저장소가 증적으로 부풀고 `git status`가 더러워진다.

**나누는 기준**: `fragments/`는 **그 자체로는 목적이 아닌 것**(로그인, 장바구니 담기, 픽스처 시드), `journeys/`는 **사용자가 달성하려는 것**(로그인해서 결제까지). 조각은 여정을 참조하지 않고 여정만 조각을 참조한다 — 단방향이라 순환이 생기지 않는다.

**파일 단위**: 태스크 단위로 나누지 않는다. 태스크가 끝나면 고아가 되어 누적 스위트가 되지 않는다. 여정 단위·조각 단위로 나눈다.

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
postconditions:                           # [MUST] 없으면 채택 불가
  - {verifier: url,      expected: "/dashboard",  match: equals}
  - {verifier: dom_text, target: ".user-name", expected: "{id_ref}", match: equals}
```

### 규칙
- **[MUST] 사후 조건이 없는 조각은 등록하지 않는다.** 없으면 로그인이 조용히 실패한 채 뒤 여정이 통과한다.
- **[MUST] 자격증명을 조각에 직접 적지 않는다.** `value_ref`로 환경변수·시크릿 파일만 참조한다. 근거: 태스크 127 실측 — `fill`의 value는 C-6 redaction 대상이 **아니어서** `actions.jsonl`에 원문으로 남는다. 이 구멍을 막는 것이 조각 도입의 **선행 조건**이다.
- **[MUST] 전개 결과는 `actions.jsonl`에 실제 연산 단위로 남긴다.** `login` 한 줄만 남으면 증적이 무엇을 했는지 말하지 못한다.
- `match`는 `equals`를 쓴다. 태스크 127 실측 — `contains`는 `validate_pass_requirements`의 직접 비교(§A.5)에 걸려 `pass`에 도달할 수 없다.

## 5. 신선도 키

구성: `(여정 해시, 참조 조각 해시 집합, surface_id, 대상 commit)`. **휘발성 값(`run_id`·타임스탬프·포트)은 넣지 않는다** — 넣으면 영원히 일치하지 않아 무용지물이다.

재실행 생략은 아래 4개를 **모두** 만족할 때만 허용한다.
1. 대상 commit 동일
2. 여정·조각 해시 동일
3. 이전 결과가 `pass`
4. 증적이 실제로 남아 있음

**[MUST] 생략을 "미실행"이 아니라 "이전 증적 재인용"으로 기록하고 DONE.md에 보이게 남긴다.** 이 장치가 없으면 신선도 키는 검증을 조용히 건너뛰는 가장 세련된 방법이 된다 — 태스크 070 실패모드가 정확히 그 형태였다.

조각 해시가 바뀌면 그 조각을 참조하는 **모든 여정의 신선도가 무효**가 된다. "로그인 절차가 바뀌었으니 로그인을 쓰는 12개 여정만 재실행"이 결정론으로 나온다.

## 6. 발동과 게이트

| 시점 | 동작 |
|---|---|
| 평시 | 캡틴이 `//e2e` 수동 호출 |
| CLOSE 진입 | **조건부** 확인 — 이번 변경이 사용자 접촉 표면을 건드렸을 때만 `real-usage` 증거를 요구 |

새 규범을 만드는 것이 아니다. oppl `verification.md` §1.5.3이 이미 "사용자 접촉 표면·여정은 `real-usage` PASS ≥1 없이 done을 인정하지 않는다"를 [MUST]로 규정한다 — 이 제안은 **있는 규범에 집행 지점을 주는 것**이다. 표면을 건드리지 않은 문서·설정 태스크는 그대로 통과한다.

**비동기 실행은 채택하지 않는다.** "CLOSE를 막지 않고 백그라운드로 돌려 나중에 귀속"은 done 판정이 증거 도착 전에 나가므로 070 실패모드를 재현한다. 느리면 범위를 줄이지, 판정을 앞당기지 않는다.

## 7. 기존 자산과의 접합

| 자산 | 관계 |
|---|---|
| `test-tool e2e run\|resume\|status\|clean` | 실행 주체. 이 제안은 입력을 공급할 뿐 실행 계약을 바꾸지 않는다 |
| `collaborative` profile·`awaiting_human`·resume token | 협동 수행에 그대로 쓴다. 신규 구현 없음 |
| `surfaces.json` | 표면 SSOT. 이 제안이 복제하지 않는다 |
| `scenario-conformance` | 여정 커버리지 판정에 재사용 |
| `CANDIDATE_ORDER`(C-DRV-3) | driver 우선순위. 조각·여정과 무관 |

## 8. 열린 쟁점

| # | 쟁점 | 메모 |
|---|------|------|
| Q-1 | 조각 전개분과 본문 연산의 **중복 판정 충돌** | 동결 RED S-27 (d-1)이 같은 연산 signature 중복을 재시도로 판정한다. 태스크 127에서 `--version` 2회가 실제로 이 규칙에 걸려 browser step runner가 봉쇄됐다가 driver 인스턴스 메모이즈로 해소됐다. 조각이 `navigate`를 포함하고 본문도 `navigate`를 쓰면 재발한다 — **전개분과 본문을 구분 집계**하거나 중복 판정 범위를 명시적으로 좁혀야 한다 |
| Q-2 | 로그인 **세션 재사용** 여부 | 조각과 별개 축이다. 현재 구현은 세션·프로필이 `opal-e2e-{run_id}`라 run마다 새로 만들어진다(`agent_browser.py:334,353`). 지속 프로필을 도입하면 로그인 반복이 사라지지만 **로그인 자체가 미검증**이 된다 — 로그인 여정만 주기적 cold 실행으로 분리하는 보완이 필요하다 |
| Q-3 | `docs/e2e/` → `.opal/e2e/` **시드 도구** | `TEST-SCENARIO.md` → `test-scenario.json` 시드와 같은 형태여야 한다. 태스크 127에서 JSON을 손으로 시드한 결과 4건의 사고(profile null·`server_policy` enum 밖·실행 스펙 부재·재시드 불가)가 났다 — **손편집 경로를 열지 않는 것이 이 구조의 존재 이유다** |
| Q-4 | Ego Lite driver 편입 | `~/.opal/tools/ego-browser-tool`이 이미 JSON 계약을 제공하고 `opal-wtm-agent`가 1순위로 쓴다. E2E 후보 체인에 넣고 1순위로 두려면 `CANDIDATE_ORDER` + C-DRV-3 개정이 동반된다 |
