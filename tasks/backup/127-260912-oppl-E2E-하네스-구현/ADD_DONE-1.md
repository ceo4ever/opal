# ADD_DONE-1: Ego Lite driver 흡수

| 항목 | 내용 |
|---|---|
| 추가작업 번호 | ADD-1 |
| 일시 | 2026-09-18 (KST) |
| 사유 | main 병합 시 태스크 129(Ego Lite 브라우저 우선 통합)와 `e2e_adapter.py`에서 정면 충돌. 한쪽을 택하면 상대 작업이 통째로 사라져 병합을 중단하고, Ego Lite를 §B.2 driver 계약으로 흡수하는 통합을 먼저 수행했다 |

## 변경 내용

### 1. `ego_lite.py` driver 신설

`ego-browser-tool`은 8연산 driver가 아니라 `smoke <url> --expect-text <text>` — **open과 텍스트 assert가 융합된 단일 연산**이다. 그 실제 계약에 맞춰 흡수했다.

| 연산 | 구현 |
|---|---|
| `probe` | `run.sh status` **실제 실행**으로 가용성 판정(C-DRV-2 — 바이너리 존재·플랫폼 추정 금지) |
| `open` | 대상 URL **기록만**. 실제 호출은 `assert`에서 한 번 |
| `assert` | `smoke --expect-text` 1회. `dom_text` verifier만 선언 — 도구가 노출하지 않는 verifier를 선언하면 그걸 쓰는 시나리오가 이 후보로 내려와 실행 시점에 깨진다 |
| `close` | no-op. 소유 자원이 없다(`smoke`가 자기 수명을 관리) — 정리 대상이 구조적으로 없다(C-2) |
| `snapshot`·`act`·`wait`·`capture` | **없음을 선언**(`probed:true`·`available:false`, §A.8) |

**[MUST] `open`에서 `smoke`를 부르지 않는다.** 융합 연산을 두 번 부르면 같은 연산이 run 안에서 2회 실행되어 재시도로 관측된다(동결 RED S-27 (d-1)). 융합된 지점에서 한 번만 부른다.

### 2. 후보 순서 — ego-lite를 1순위에 두지 않았다

배치: `agent-browser/orca-managed` → `cmux` → `agent-browser/standalone` → **`ego-lite`** → `playwright(opt-in)`

캡틴 의도는 1순위였으나, 실측 후 **더 나쁜 기본값**으로 판단해 뒤로 옮겼다.

- `ego-lite`는 부분 driver다. 1순위면 UI 조작이 필요한 시나리오에서도 먼저 `selected`되고 실행 도중 `driver_operation_unimplemented`로 `blocked`가 된다 — **더 완전한 driver를 가린다.**
- 현재 후보 게이트는 capability(§A.8.1 6키)만 보고 "이 시나리오가 `act`를 쓰는가"를 표현할 수단이 없다. 그 게이트가 없는 동안은 순서로 방어하는 것이 맞다.
- 대신 `resolve_candidates(candidate_order=...)`를 열어 **프로젝트가 순서를 재정의**할 수 있게 했다. smoke 형태만 도는 프로젝트는 이 수단으로 1순위에 올린다(제안서 §7 `order.json` 접합점).
- 태스크 129가 legacy `integration` 경로에 둔 Ego Lite 우선순위는 **그 경로에서 유지**된다 — 그쪽은 애초에 smoke 전용이다.

### 3. 계약 개정 3곳

`CONTRACT.md` — driver enum 2곳(§A.1.2 `driver`, §A.4 `driver`)에 `ego-lite` 추가, C-DRV-3 기본 순서 개정. **왜 1순위가 아닌지**와 ops 기반 게이트가 생기면 이 제약이 풀린다는 것을 개정 경위에 함께 적었다.

### 4. 순서 의존 단언 제거 (강화)

ego-lite 추가로 8건이 깨졌고, 전부 **순서를 전제한 단언**이었다. 고치면서 순서 무관으로 바꿨다 — 약화가 아니라 강화다.

- `candidates[0][...]` 5곳 → `_record(candidates, driver, session_mode)` (**정체로 찾기**)
- `len(candidates) == 1` → **MV-38 형태**(`infra_error` 원소보다 큰 `order`가 없음). 후보 수가 아니라 C-3의 본뜻을 잰다
- 동결 RED(`test_red_s*.py`)는 **수정 0건** — 순서 재배치로 자연히 원복됐다

**시도했다 되돌린 것**: "주입된 레지스트리를 닫힌 세계로 취급"은 `registry={}`로 모든 후보가 기록되는지 검증하는 테스트와 충돌해 되돌렸다. 기본 레지스트리에서 미등록을 `no_registered_driver`로 남기는 것이 이 태스크에서 driver·executor 미배선을 두 번 놓친 이유를 막는 장치다.

## 변경 파일

- `opal/tools/test-tool/lib/e2e/drivers/ego_lite.py` (신설)
- `opal/tools/test-tool/lib/e2e/drivers/__init__.py` (등록·순서·`candidate_order` 주입)
- `opal/tools/test-tool/lib/e2e/drivers/manifest.json` (ego-lite 버전 게이트)
- `opal/tools/test-tool/tests/test_e2e_drivers.py` (순서 무관 단언)
- `tasks/127-260912-oppl-E2E-하네스-구현/CONTRACT.md` (§A.1.2·§A.4 enum, C-DRV-3)

## 검증 결과

- `~/.opal/.venv/bin/python -m pytest opal/tools/test-tool/tests/ -q` → **424 passed / 0 failed** (334 subtests)
- 등록 driver 4종 확인, 후보 해석 실측 — `agent-browser/orca-managed` selected, 나머지 `not_attempted_after_selection`
- 동결 RED 수정 **0건**(`git diff --name-only HEAD -- tests/test_red_` → 0)
- `git diff --stat lib/e2e_contract.py lib/scenario.py` → **빈 출력**(C-1 유지)
- `ego-browser-tool` 자체 **변경 0** — JSON 출력 계약을 소비만 했다

## 참고

**남은 병합 conflict 8건**은 별개다. `e2e_adapter.py`는 main의 ego 우선순위 체인(legacy `integration`)과 태스크 127의 cmux 이관이 **서로 다른 함수**라 병존 해소가 가능하고, 문서 6건·`install-mac.sh`도 병존이다. ADD-1은 driver 흡수까지이며 병합 자체는 이 문서 범위 밖이다.

**후속 제안**: ego-lite를 안전하게 1순위에 두려면 **ops 기반 후보 게이트**가 필요하다 — 시나리오 step에서 요구 연산(`act`·`wait` 등)을 뽑아 그걸 못 하는 후보를 실행 전에 거르는 장치. `docs/proposals/e2e-journey-fragment-library.md` 열린 쟁점에 추가 대상이다.
