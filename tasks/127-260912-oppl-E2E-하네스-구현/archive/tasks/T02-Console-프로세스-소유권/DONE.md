<!-- @header {"module":"DONE","layer":"task-record","domain":"oppl","description":"T02 Console 프로세스 소유권 완료 기록 — 파이프라인 경과·변경 파일·검증 결과·시나리오 판정·보안 조치·PM 판정 대상 잔여 항목.","task":"127-T02"} -->

# DONE — T02 Console 프로세스 소유권

> `opal-cli console`의 기동·종료·상태를 PID 레코드 identity 검증으로 전환하고, 광역 `pkill -f` 패턴 종료를 2지점 모두 제거했다. `TASK.md` AC-3(양방향 비간섭)이 실관측으로 성립한다.

| 항목 | 값 |
|---|---|
| task_id | `T02` |
| area | `공통` |
| 요구 충실도 | `real-usage` — **충족**(`scenario-fidelity-check all_met=true, 14/14`) |
| 시나리오 | 14/14 pass (fail 0 · blocked 0 · awaiting_human 0) / 테스트 케이스 20건 기준 20 PASS · 0 FAIL · 0 SKIP |
| 회귀 | 0건 (`pytest` 88 passed 유지) |
| 사용자 Console 7823 | 전 구간 **200 불변** (C-2 무위반) |
| blocker | 없음 (보안 blocker 1건은 태스크 내에서 해소) |

---

## 파이프라인 경과

| 단계 | 축 | 결과 |
|---|---|---|
| T1 명세·설계 | 생성자(`opal-task-agent`, cold prime) | PLAN.md 25,933B. 설계 쟁점 8건 결론 + BLOCKED 2건 |
| T2 RED 시나리오 | `opal-test-agent`(mode: red) | 테스트 신설. RED 4 FAIL / 1 PASS / 4 SKIP |
| **G 명세 리뷰 ①** | `opal-evaluator-agent`(spec-review) | **fail** — E.1=3, E.3=3. blocker F-1·F-2·F-3 포함 F-1~F-11 |
| T1 재작업 | 생성자(warm resume) | PLAN.md 25,933 → 44,881B. D-16~D-18 신설, 시나리오 9 → 14건 |
| T2 재작업 | `opal-test-agent` | 14건 재작성. RED 14 FAIL, **구현 전 우연 통과 0건** |
| **G 명세 리뷰 ②** | `opal-evaluator-agent` | **pass** — 전 축 ≥4 (E.1 3→4, E.3 3→4, E.4 4→5) |
| T2 국소 시정 | `opal-test-agent` | G2 필수 시정(S-6 GREEN 자기파괴) + 권고 C-1·C-3·C-4 |
| T3 구현 | 생성자(warm resume) | `console.sh`·`install-mac.sh`. **5시간 한도로 1회 중단 후 재개**(아래) |
| T4a 테스트 | `opal-test-agent`(독립) + 디스패처 재검증 | 20 PASS / 0 FAIL / 0 SKIP (2회 일치) |
| T4b 규칙검사 | conv + sec checker | conv blocker 0·major 0·minor 1 / **sec blocker 1 · major 3 · minor 5** |
| T3 보안 재작업 | 생성자(warm resume) | B-1·M-3·M-1·m-4~m-8 수정. 재실행 회귀 0 |
| T4a 재검증 | 디스패처 | 20/20 PASS 유지, 14건 재마킹, `all_met=true` |

**검증 2원화 순서 evidence**: `QA-SPEC.md` G① 2026-09-13 00:16 · G② 00:55 < `test-scenario.json` result `marked_at`(T4a 재마킹). 생성자≠평가자(H-9), RED 작성자≠구현자(`red-first.md` §1.5)를 전 구간 유지했다.

**재설계 루프 1/2 소진** — G 2회차에 pass하여 상한 내 종료.

---

## 변경 파일

**수정 (2)**
- `opal/tools/opal-cli/lib/console.sh` (+239/-) — 헬퍼 4종 신설(`console_record_path`·`console_write_pid_record`·`console_read_pid_field`·`_console_pid_sane`/`_console_pid_value_unsafe`), `start` D-8 3분기, `stop` 판정표 6분기(**`pkill` 제거**), `status` D-10 양분기. 헤더 변경이력 v1.5
- `scripts/install-mac.sh` (+24/-) — `console_autostart()` 종료 폴백을 D-13 3분기 위임으로 교체(**`pkill` 제거**). 헤더 변경이력 v4.9

**신설 (1)**
- `scripts/tests/test_console_ownership.sh` (875줄) — 양방향 비간섭 회귀 테스트 20케이스. `scripts/tests/test_console_scan.sh` 관행 답습(bash 3.2 호환, `mktemp -d`+`trap`, pass/fail/skip 카운터)

**변경 0 계약 준수**: `opal/tools/test-tool/**`(`e2e_contract.py`·`scenario.py`·`lib/e2e/**`) · `opal/tools/worktree-tool/**` · `dashboard/**` diff 0. `CONTRACT.md` 미수정. `~/.opal/` 배포본 미편집.

---

## 검증 결과 (실제 출력)

| 명령 | 결과 |
|---|---|
| `bash -n opal/tools/opal-cli/lib/console.sh` · `scripts/install-mac.sh` | 양쪽 exit 0 |
| `grep -Ec '\b(pkill\|pgrep\|killall)\b' <두 파일>` | `console.sh:0` / `install-mac.sh:0` — **MV-21 충족** |
| `grep -rc 'console\.pid' opal/tools/test-tool/` | **0건** — MV-22 유지(T01 달성분 회귀 0) |
| `bash scripts/tests/test_console_ownership.sh` | **`PASS: 20 \| FAIL: 0 \| SKIP: 0` → `verdict: ALL PASS`** |
| `cd opal/tools/test-tool && ~/.opal/.venv/bin/python -m pytest tests/ -q` | **`88 passed, 100 subtests passed`** (T01 baseline 회귀 0) |
| `scenario-status` | `locked: true`, `total: 14`, `passed: 14`, `failed: 0`, `red_confirmed_required: 12/12` |
| `scenario-fidelity-check` | **`all_met: true`, `total: 14`, `met: 14`** |
| 사용자 `127.0.0.1:7823` | 매 실행 전후 **200 → 200**, 잔존 pid는 사용자 `8532` 단 1개(고아 0건) |

기계검증절: **MV-21 · MV-22 · MV-23 · MV-37(정·역) 충족.**

---

## AC-3 양방향 실관측 증적 (`real-usage`)

두 서버를 **동일 ASGI 경로 문자열**(`dashboard.backend.main:app`)로 ephemeral 포트에 실제 기동해 관측했다 — 이 문자열 동일성이 `pkill -f` 오탐의 원인이었으므로(CONTRACT:601) 재현 조건으로 유지했다.

**정방향 (S-6, MV-37)** — E2E backend 실행 중 `console stop`
```
P1(콘솔역, app_dir=console-home) + P2(E2E역) 동시 기동 → 정상 레코드 → 실제 console stop
→ P1 종료(kill -0 실패 + health 연결 실패) AND P2 생존(kill -0 성공 + health 200)
  AND 레코드 파일 삭제 AND stdout `stopped=true pid=<P1>` AND 사용자 7823 health 200 불변
```

**역방향 (S-7, MV-37)** — E2E 종료 후 사용자 Console 생존
```
P2를 `set -m`으로 자기 프로세스 그룹에 기동 → `ps -o pgid=`로 pgid==pid 단언
→ kill -- -88407 그룹 종료 → P2 종료, P1 생존 + health 200 + 레코드 잔존, 사용자 7823 health 200
→ ④ 직후 실제 console stop → `stopped=true pid=<P1>` (그룹 회수가 레코드·identity 미훼손)
```

**RK-1 사전 실패 증명 (S-4(a)·S-6(a))**: 두 서버 기동 상태에서 `pgrep -f "dashboard.backend.main:app"`(kill 0회, 읽기 전용)의 매치 집합이 **P1·P2·사용자 Console 8532를 모두 포함**함을 관측했다. 구 구현의 `pkill -f`는 이 집합 전체를 종료했을 것이며, 이것이 AC-3 불성립의 직접 원인이었다.

---

## 보안 검사 조치 (T4b sec)

**blocker 1건 · major 3건 · minor 5건**이 제기되었고, M-2를 제외한 전건을 태스크 내에서 수정했다.

### B-1 (blocker) — `pid: 0` 레코드가 `kill 0`(호출자 프로세스 그룹 전멸)로 이어짐 → **해소**

디스패처 실측 재현: reader 정규식 `[0-9][0-9]*`가 `0`을 추출 → `-z` 미발동 → `app_dir` 일치 → **`kill -0 0`은 POSIX상 항상 성공** → 판정표 #4 미발동 → 판정표 #5의 `kill 0` = **송신자 프로세스 그룹 전체에 SIGTERM**. writer의 `*[!0-9]*` 검사도 `0`을 통과시켰다. `install-mac.sh`의 무인 위임(`|| true`)이 이 경로를 타므로 설치 중 프로세스 그룹이 단서 없이 종료될 수 있었다.

> 이 결함은 T02가 제거한 것과 **같은 계열**이다 — 광역 `pkill`을 지운 자리에 "의도치 않게 광역인 `kill`"을 남긴 셈이었다.

**수정**: `_console_pid_sane()` 신설(`pid >= 2` && 순수 숫자)을 writer·`start`①·`stop`·`status` 전 지점에 공통 적용. `stop`에서는 **판정표 #2(`unreadable_record`)로 합류**시켜 6분기 계약을 유지했다(새 분기 미생성).

**해소 증거 — 실제 코드·격리 프로세스 그룹에서 부정 케이스 직접 관측** (회귀 시 디스패처 세션이 죽지 않도록 `set -m`으로 자기 프로세스 그룹을 갖는 센티넬을 같은 그룹에 배치):
```
pid=0    | 센티넬=ALIVE | 레코드=present | out=stopped=false pid=- reason=unreadable_record
pid=1    | 센티넬=ALIVE | 레코드=present | out=stopped=false pid=- reason=unreadable_record
pid=-5   | 센티넬=ALIVE | 레코드=present | out=stopped=false pid=- reason=unreadable_record
pid=abc  | 센티넬=ALIVE | 레코드=present | out=stopped=false pid=- reason=unreadable_record
```
센티넬 전건 생존 = **kill 0회**. 사용자 7823은 전후 200.

### M-3 (major) — `start` 사전 검증이 자기 주석이 막겠다던 상황을 허용 → **해소**
`console.sh:169`가 `"`·`\`만 검사해, 개행 포함 `OPAL_HOME`이 통과 → 데몬 기동 → writer만 실패 → **레코드 없는 고아 데몬**이 7823을 점유하고 `console stop`으로 종료 불가. **수정**: 사전 검증을 writer와 동일한 `_console_pid_value_unsafe` 호출로 통일하고, 그 함수를 `[[:cntrl:]]` 한 클래스로 정리해 제어문자 전체를 포괄했다.

검증: `newline/tab/cr/quote/backslash/esc → REJECT`, `plain → ACCEPT`. writer가 개행 경로에 `return 1` + 파일 미생성.

> **한계**: M-3의 **런타임 전 경로**는 관측하지 못했다. `start`는 포트 7823이 고정이라, 사용자 Console이 응답하는 환경에서는 분기 ②가 먼저 가로채 분기 ③(사전 검증)에 도달하지 않는다. 사용자 Console을 끄지 않고는 도달할 수 없어(C-2) 함수 단위·정적 구조 검증으로 대체했다.

### M-1 (major) — identity 검증 TOCTOU → **해소**
필드마다 파일을 다시 읽어(`stop` 2회·`status` 6회·`start` 2회), read 사이 레코드가 교체되면 **버전 A의 `app_dir`로 통과시키고 버전 B의 `pid`를 kill** 하는 조합이 성립했다. §A.13이 6필드를 하나의 레코드로 규정한 계약에 어긋난다. **수정**: `console_read_pid_field` 시그니처를 `<record_path>` → `<content>`로 바꾸고 3지점 모두 `cat` 1회 스냅샷에서 전 필드를 추출한다.

### minor 5건 → **전건 수정**
- **m-4**: `console_read_pid_field`의 `$field`가 `sed` 스크립트에 보간 → 진입부 allowlist(`pid|port|opal_home|app_dir|host|started_at`) 추가
- **m-5**: `mkdir -p -m 700`, 레코드 `chmod 600`, 심볼릭 링크 경로 거부 — `docs/SECURITY.md` §3 baseline 정합
- **m-6**: `tmp.$$` 경유 원자적 `mv -f`
- **m-7**: `install-mac.sh` 위임이 stdout 계약 줄을 캡처해 `stopped=false`면 `reason=`을 `warn`으로 승격(`|| true` 비중단 유지)
- **m-8**: `status`의 레코드 유래 값 재검증 — 수기 편집 레코드에 의한 출력 라인 위조(CWE-117) 차단

### conv minor 1건 — **미수정(기록)**
`console.sh:149`의 `local pid=""`(D-8 판정용)와 `:206`의 `local pid=$!`(기동 후 실값)가 같은 함수 스코프에 공존한다. checker가 `disposition: advisory`로 분류했고 동작 오류가 없으며(bash 재선언 허용, 두 용도 분리로 값 오염 없음), **S-10이 `nohup` 직후 `local pid=$!` 리터럴 구조를 단언**하므로 변수명 변경은 잠긴 시나리오를 건드린다. 가독성 이득보다 회귀 위험이 커 보류한다.

---

## PM 판정 대상 (차단 아님)

1. **BLOCKED-1** — `surfaces.json` `console-*` `response_shape`의 표현 형식 미규정(오너십 #3 인터페이스, 영향 슬라이스 `surfaces.json:45-67` 3항목). D-11의 `key=value` 해석은 `console.sh`의 `scan`만 stdout JSON인 선례(C-6)에 근거하나, 커버리지 게이트가 JSON 파싱한다면 3표면이 동시에 실패한다. §B.4 한 줄 보강 권고.
2. **BLOCKED-2** — `start`의 "레코드 없음 + 7823 응답"(구버전 daemon) 기대 동작이 `TRD.md:235`에 공백(오너십 #2). D-8 ②로 해석해 진행했다. H-1이 업그레이드 직후 **전 사용자에게 1회** 발생하고 **실행 검증이 구조적으로 불가능**(포트 고정 × C-2)하므로 계약 본문 고정 권고.
3. **BLOCKED-3 — M-2(PID 재사용) 미수정 + 자기 위험 등급 정정.** `started_at` × `ps -p <pid> -o lstart=` 대조는 identity 판정 기준을 `app_dir` 단일에서 2요소로 넓히는 **계약 해석 확장**이라 이번 범위에서 제외했다(오너십 #2, PM 이관).
   **정정**: PLAN H-2가 "레코드는 `stop` 성공·stale 시 즉시 삭제되어 창이 짧다"를 근거로 위험을 **낮음**으로 평가한 것은 **부정확하다**. 레코드 삭제는 `stop`이 실행될 때에만 일어나므로, 데몬이 크래시·OOM·`kill -9`·**리부팅**으로 사라지면 레코드는 무기한 잔존한다. 리부팅 후 PID 공간은 처음부터 재할당되므로 기록된 pid가 무관한 사용자 프로세스에 재할당될 확률이 높고, 그 경우 `app_dir`(레코드 자기 필드)은 당연히 일치하고 `kill -0`도 성공해 판정표 #5로 직행한다. 이번 변경으로 `install-mac.sh`가 이 경로를 **무인 호출**하므로 리부팅 후 첫 설치 실행이 임의 사용자 프로세스를 종료할 수 있다. `started_at`은 §A.13 필수 필드로 **기록만 되고 어디서도 읽히지 않아** 재료는 이미 있다. 저비용 대안: `started_at`이 시스템 부팅 시각보다 이르면 무조건 stale로 판정(판정표 #4 합류) — `ps` 없이 지배적 원인인 리부팅 경로를 닫는다.
4. **BLOCKED-4** — `CONTRACT.md` §A.13이 경로 필드의 **허용 문자 집합**을 미규정(오너십 #2). D-2·D-12가 암묵 제약을 명시 제약(`"`·`\`·제어문자 포함 시 기록 거부 + 기동 전 차단)으로 승격했다. A.13 한 줄 명시 권고.
5. **BLOCKED-5(기록만)** — G① F-10(`fidelity: "mock"` 사전 오염 주장)은 **오판**이다. `scenario.py:224`의 result존 도구 기본값이고 `scenario-mark --fidelity`로만 갱신되며(`:549`), 게이트는 `result=="pass"`인 시나리오만 fail-closed로 평가한다(`:656-664`). G② 에서 **평가자 본인이 판정을 철회**했다.

---

## CONTRACT §C.10 신설 경위

T4a 마킹 중 계약 공백을 발견해 보고했고 **PM이 계약으로 승격**했다. `real-usage` + `pass` 마킹은 `--verdict-json` 구조화 단언을 요구하는데(`scenario.py:533`, fail-closed), 그 게이트가 `validate_pass_requirements`로 넘어가면 `profile`이 `PROFILES` 중 하나여야 하고 `EXECUTOR_MATRIX`의 executor를 요구한다. 그런데 `surfaces.json`의 `console-*` 3표면은 `kind: "cli"`이고 계약에는 `cli` profile도 `cli` executor도 없었다.

디스패처는 `profile: "api"` / `observed_executors: ["api"]`로 기록했다 — 생존·종료 판정의 **실제 관측 수단이 HTTP**이기 때문이다(`console stop`은 행위이지만 단언은 두 서버의 `GET /health` 200/연결 실패로 이루어진다). PM이 이를 채택해 **§C.10**을 신설했다: **profile은 호출 수단이 아니라 단언 수단이 결정한다.** CLI는 actor의 행위이지 검증되는 공개 계약이 아니며, `cli` profile·executor는 신설하지 않는다(`TASK.md` C-1이 125 계약 재정의를 금지). 편의로 `manual`을 고르지 않는다 — `human` executor를 요구하므로 자동 실행 결과에 붙이면 증적이 거짓이 된다. 이 규칙은 `e2e-*` 4표면(T03·T04·T10 소유)에도 적용되어 이후 반복 판단이 사라진다.

---

## 실행 중 특기사항

**T3가 5시간 사용량 한도로 1회 중단 후 재개됨.** 첫 T3 실행이 `exit 2`로 끝났고 `t3.events.jsonl` 마지막 이벤트가 `rate_limit_event → status: rejected, rateLimitType: five_hour, overageDisabledReason: out_of_credits`였다. **동일 지점 재실패가 아니라 환경 차단**이므로 하네스 재시도 상한을 소비하지 않았다. 한도 리셋 후 워커 자기보고가 아닌 **워킹트리 실측**으로 구현 완결을 판정하고(헬퍼·start 3분기·stop 6분기·status 양분기·변경이력 v1.5/v4.9 확인, `bash -n` 양쪽 OK, MV-21 0건, pytest 88 passed) 이어갔다.

**`scenario-conformance` 37건 미검증은 T02 결함이 아니다.** 분모가 프로젝트 전체 `surfaces.json`(40건)이고, T02 커버 3표면(`console-start`·`console-stop`·`console-status`)은 **미검증 목록에 없다**(40 → 37로 정확히 3 감소). 나머지는 T01·T03~T09 소유이며, 분모 전체 스코핑은 Loop 2 종료(L✓) 게이트의 성질이지 태스크 게이트가 아니다(T01 `DONE.md` §PM 판정 대상 2와 동일 사안).

**프레임워크 발견(PM `fw-inbox` 기록됨)**: `scenario-init`이 `locked: true`를 무시하고 덮어쓴다(`scenario.py:319`) — `scenario-red`만 `scenario_already_locked`로 막는다. `scenario-lock`이 변조 방지를 제공하지 않으므로, self-confirming RED 차단(H-7)이 lock 통과 여부에만 의존하면 init 재호출로 우회 가능하다. 이번 태스크에서 우회 목적으로 쓰지 않았고 `test-scenario.json`을 손으로 편집하지도 않았다.
