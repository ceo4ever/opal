<!-- @header {"module":"QA-SPEC","layer":"task-record","domain":"oppl","description":"T02 G(명세 리뷰) 게이트 판정 기록 — opal-evaluator-agent spec-review verdict·루브릭 점수·수정 요구 항목.","task":"127-T02"} -->

# QA-SPEC — T02 Console 프로세스 소유권 (G 명세 리뷰 ①)

| 항목 | 값 |
|---|---|
| phase | `spec-review` (구현 전) |
| 평가자 | `opal-evaluator-agent` (opal-agent 채널, model=advanced, readonly) |
| 생성자 | `opal-task-agent` — **생성자≠평가자(H-9) 유지** |
| 판정 시각 | 2026-09-13 00:16 (KST) |
| **verdict** | **fail** |
| 판정 대상 | `PLAN.md` · `test-scenario.json`(locked, 9건) · `scripts/tests/test_console_ownership.sh` |
| 루브릭 | E.1=3 · E.2=4 · E.3=3 · E.4=4 · E.5=4 · E.6=5 → **E.1·E.3이 3 이하라 fail** |

> 이 문서의 산출 시각이 검증 2원화 순서 evidence의 원천이다 — QA-SPEC(G) < test-scenario.json result `marked_at`(T4a).

---

## Evaluator 판정 원문

## verdict: fail

**참고 — 진입 게이트**: 이 세션은 비대화형이라 `event-loader run.sh verify --event worker.dispatch --receipt ...`가 권한 거부로 실행되지 않았습니다. 디스패처가 제시한 `ok: true`·`verified_document_count: 4`와 receipt JSON의 `documents[].content` 4건(agents.md, pm/dispatch-process.md, pm/context-injection.md, observability)을 직접 Read해 적용하고 진행했습니다. 게이트 자체 실행 불가는 blocker로 올리지 않되 기록합니다. 또한 디스패처 지시대로 파일은 하나도 생성하지 않았습니다(`QA-SPEC.md` 미생성).

---

## 1. 루브릭 축별 점수 (CONTRACT §E, 통과선 전 축 ≥4)

| 축 | 점수 | 근거 |
|---|---:|---|
| E.1 계약 완전성 | **3** | 3표면 모두 `surfaces.json` 등재·D-11로 `response_shape` 환원 시도·BLOCKED-1로 미규정을 정직하게 표시. 그러나 앵커 3의 "**오류 경로** 미규정" 2건이 실재한다 — ① `status`의 health 실패 분기(`console.sh:104` `exit 1`)에서 D-10 레코드 줄을 출력하는지 미규정, ② `stop` 판정표가 실패 분기에 `reason=`만 적고 `console-stop` `response_shape`의 `stopped` 필드(`surfaces.json`)를 어떤 값으로 낼지 미규정 |
| E.2 계약 일관성 | **4** | 125 소유 계약(profile·status·exit) 무접촉, `e2e_contract`·`scenario.py` 무변경, §C.1 무의존 D-15로 명시 유지. E.2 "즉시 감점 사유" 3건(하네스가 `console.pid` 읽기/쓰기, 필드 추가, `infra_error` 전환) 모두 해당 없음. 감점은 명세 내부 정합 3건(F-10, F-11) |
| E.3 설계 정합 | **3** | RK-1 2지점(`console.sh:88` + `install-mac.sh:1844`) 모두 포함 ✓, TD-5 집행 지점 명시 ✓ — 앵커 5의 "여러 집행 지점 전부 포함" 요건은 충족. 그러나 **TD-5가 요구하는 결과의 절반이 시나리오 설계 단계에서 이미 집행되지 않는다**: MV-37 역방향은 S-7이 tautology(F-2), 수용기준 5는 S-8이 구조적으로 실행 불가(F-1), 수용기준 1의 `start` 통합은 무증적(F-7). TRD TD-5가 명시한 "프로세스 그룹 단위 회수"도 S-7이 재현하지 않는다 |
| E.4 drift 필요성 | **4** (drift = **no**) | BLOCKED-1·2 모두 계약 **변경을 요구하지 않고** 해석으로 진행 + `{경로}:{라인}` 실측 인용 제시. 앵커 5의 "오너십 계층 4단계 분류 명시"가 없어 5는 아님 |
| E.5 컨벤션 정신 | **4** | 인용 밀도 높음, `~/.opal/` 미편집(C-7), 플랫폼 분기 0(D-5 근거 = `docs/CONVENTIONS.md:259-262`), 배포 경계 판정(`:255` 런타임 사용자 데이터) 정확, 사용자 자원 판별이 `app_dir` identity라는 **관측 가능한 근거**. 격리 규약이 사용자 7823을 GET /health 읽기 전용으로 못박고 전후 코드 단언까지 둔 것은 앵커 5 수준. 감점은 D-9 안내 원문과 테스트 단언 불일치(F-11) |
| E.6 아키텍처 적합 | **5** | D-15로 `test-tool`/`worktree-tool`/`dashboard` diff 0, 신규 CLI 0, D-13 위임으로 종료 로직 1벌 — RK-1 재발이 구조적으로 불가. §C.1 구조도 소유 배치 준수 |

**verdict 산출**: E.1=3, E.3=3 → CONTRACT §E "어느 한 축이라도 3 이하면 G 게이트를 통과하지 못한다" → **fail**.

---

## 2. 수정 요구 항목

### F-1 (blocker). S-8은 GREEN에서 **구조적으로 실행될 수 없다** — 수용기준 5가 영구 미검증
`test_console_ownership.sh:394`에서 S-7이 `kill -TERM "$P2_PID"`로 P2를 종료한 뒤, S-8이 `:415-416`에서 `kill -0 "$P2_PID"`를 전제 조건으로 걸고 실패 시 `:440` skip한다. RED에서는 S-7이 skip되어 P2가 살아남아 S-8이 FAIL로 관측됐지만(`red_confirmed: true`), **GREEN에서는 S-7이 실제로 실행되어 P2를 죽이므로 S-8은 항상 skip된다.** 결과: 수용기준 5(`console status`가 `pid`·`app_dir` 노출, CONTRACT §B.4 `console status` 행)가 GREEN에서 단 한 번도 검증되지 않으며, PLAN W-4의 완료 기준 "FAIL 0 · SKIP 0"(`PLAN.md:116`)도 달성 불가다.
**수정**: S-8을 S-6/S-7보다 앞에 배치하거나, S-8 전용 서버를 별도로 기동한다. 픽스처 수명주기를 시나리오 순서에 암묵 의존시키지 않는다.

### F-2 (blocker). S-7은 T02 코드를 전혀 실행하지 않는 vacuous 테스트 — MV-37 역방향 미집행
`:394`가 하는 일은 테스트 자신이 띄운 pid에 대한 평범한 `kill -TERM "$P2_PID"`다. (a) PLAN S-7이 명시한 하네스 방식 프로세스 그룹 종료(`kill -- -<PGID>`, `PLAN.md:92`)가 아니고, (b) `start_server`(`:120-131`)가 서버를 별도 세션/프로세스 그룹으로 띄우지도 않으며(TRD TD-5 "프로세스 그룹" 항 미재현), (c) `console stop`도 하네스 teardown도 호출하지 않는다. **이 테스트는 T02 구현 전후로 동일하게 PASS한다** — "P2를 죽이면 P1은 안 죽는다"는 OS의 기본 동작이지 검증 대상이 아니다. CONTRACT MV-37의 역방향("E2E 종료 후 `127.0.0.1:7823` health가 계속 응답")과 수용기준 4의 후반부가 실질적으로 무검증 상태다. 덧붙여 S-7의 skip 가드가 `console_stop_unsafe`(`:374`)인 것 자체가 모순이다 — S-7은 `stop`을 호출하지 않으므로 그 가드가 걸릴 이유가 없다.
**수정**: S-7이 실제 하네스 teardown 경로(T01이 구현한 프로세스 그룹 회수)를 호출하도록 하거나, 최소한 서버를 `setsid`/`set -m`로 자기 프로세스 그룹에 띄우고 `kill -- -<PGID>`로 종료해 PLAN 기술과 일치시킨다. 그리고 역방향의 진짜 관측 대상인 **사용자 7823 Console 생존**을 단언 대상으로 승격한다(현재는 `http_code` 동일성만 확인).

### F-3 (blocker). R-1 — S-4~S-7 RED 전면 면제에 안전한 대체 관측이 없다
`console stop` 실호출을 RED에서 회피한 판단 자체는 옳다: 현행 `console.sh:88`의 `pkill -f "dashboard.backend.main:app"`는 시스템 전역이고 사용자 7823 Console이 동일 ASGI 문자열로 떠 있으므로 TASK C-2 위반이자 RK-1 그 자체다. 문제는 **회피를 "RED 증거 0"과 등치시킨 것**이다. C-2를 전혀 건드리지 않는 대체 관측이 최소 둘 존재한다:
- (a) 두 서버 기동 상태에서 `pgrep -f "dashboard.backend.main:app"`(kill 0회, 읽기 전용)의 매치 집합이 P1·P2·사용자 7823 pid를 **모두 포함**함을 단언 — 오탐 집합 중첩이 곧 RK-1의 사전 실패 증명이다.
- (b) `pkill`을 argv만 기록하는 셸 함수로 오버라이드한 뒤 `cmd_console stop`을 source·호출 — 전역 패턴 호출을 실제 관측하되 아무 프로세스도 죽지 않는다.

핵심 AC-3 시나리오 4건에 사전 실패 증명이 없다는 것의 구체적 대가가 바로 F-2다. RED가 있었다면 "구현 전에도 PASS하는 S-7"이 즉시 드러났다. 면제는 **부당**하다고 판정한다.
**수정**: S-4·S-6에 위 (a) 또는 (b)를 `red_required: true`로 부과하고 `test-scenario.json`을 재잠금한다.

### F-4. R-7 — S-8은 환경에 따라 거짓 실패한다 (규정 공백)
`console status`는 `OPAL_HOME`과 무관하게 `health_url = http://127.0.0.1:7823/health` 고정을 조회한다(`console.sh:41,97`). 사용자 Console이 없는 환경에서는 `:102-104`가 warn 후 **`exit 1`로 즉시 종료**하고, D-10은 "레코드 줄을 뒤에 덧붙인다"고만 할 뿐 **실패 분기에서도 출력하는지 규정하지 않는다**. 따라서 CI나 Console 미기동 머신에서 S-8은 계약 위반이 아니라 환경 때문에 FAIL한다. RED 증거(`test-scenario.json` S-8 `red_evidence`)에 사용자의 실제 `{"status":"ok","version":"0.1.0"}`이 찍혀 있는 것이 이 의존을 그대로 보여준다.
**수정**: D-10을 "health 성공·실패 **양 분기 모두** 레코드 줄을 출력하고, exit code만 health가 결정한다"로 확정하고, 시나리오에 사용자 Console 부재 시의 기대 동작을 명시한다. 읽기 전용 접촉이므로 C-2 위반은 아니다.

### F-5. S-8의 단언이 PLAN 설계보다 약하다
테스트는 `grep -q "pid="` 등 **키 이름 존재만** 확인한다(`:426-431`). PLAN S-8은 `pid=<P1 pid>`·`app_dir=<console-home>/dashboard-server`의 **값 일치**와 "health JSON 원문 출력 위치가 레코드 줄보다 앞"인 **순서**를 요구했다(`PLAN.md:93`). 값·순서 단언이 모두 빠져 있어, 엉뚱한 레코드를 출력해도 PASS한다.

### F-6. R-8 — `stop` 판정표 6분기 중 3분기, `start` 3분기 전부가 무커버
| 대상 | 커버 |
|---|---|
| stop #1 no_record | S-4 ✓ |
| stop #2 unreadable_record | **없음** |
| stop #3 identity_mismatch | S-5 ✓ |
| stop #4 stale_record (+ 레코드 삭제) | **없음** |
| stop #5 정상 종료 | S-6 ✓ |
| stop #6 terminate_timeout (D-6 5초 상한) | **없음** |
| start ① 이미 실행 중 / ② 레코드 없이 7823 응답 / ③ 정상 기동 | **전부 없음** |

특히 D-8 ②는 H-1(업그레이드 직후 전 사용자에게 1회 발생, 구버전 Console이 계속 뜸)의 판정 지점인데, 검증 수단이 W-4의 "육안 확인"뿐이다(`PLAN.md:104`). 이 태스크에서 사용자 영향이 가장 큰 경로가 가장 약하게 검증된다. #2·#4는 서버 없이 레코드 파일만 조작하면 `mock` 충실도로 값싸게 커버 가능하므로 면제 사유가 없다.

### F-7. R-6 — 수용기준 1의 `start` 통합 경로가 무증적
D-12의 writer 분리 자체는 타당하다: 포트 7823 고정(`console.sh:40`, CONTRACT `:595` "인자·포트는 불변")이라 `start`를 격리 환경에서 실행할 수 없고, 포트 override 환경변수 도입을 거부한 것도 계약 준수로서 옳다. 그러나 **결과적으로 S-3은 함수만 검증하고, `start`가 `nohup ... &` 직후 `$!`를 캡처해 6필드 인자로 writer를 호출한다는 연결은 어떤 시나리오도 관측하지 않는다.** 수용기준 1은 "`console start`가 6필드 레코드를 기록한다"이지 "writer 함수가 기록한다"가 아니다. 추가 위험: 현행 `:81`이 `success "... (PID: $!)"`로 `$!`를 인라인 사용하므로, writer 호출을 삽입하면 `$!`의 의미가 바뀔 수 있다(백그라운드 잡이 새로 생기면).
**수정**: `mock` 충실도의 정적 시나리오를 추가한다 — `start` 블록 안에서 `local pid=$!`가 `nohup ... &` **직후**에 오고, `console_write_pid_record`가 그 `$pid`를 포함한 5인자로 호출되며, 이후 `success` 메시지가 `$!` 대신 `$pid`를 쓴다는 것을 확인한다. R-6의 "start 경로 통합은 미검증으로 남는다"는 지적은 **성립**한다.

### F-8. `console-stop` 표면의 `stopped` 필드가 어디서도 관측되지 않는다
S-6이 `console stop`의 stdout을 `>/dev/null 2>&1`로 버린다(`:356`). D-11이 `response_shape` 필드명의 리터럴 노출(`stopped=`, `pid=`)을 계약으로 삼았으므로(`PLAN.md:33`), 성공 분기의 `stopped=true pid=<N>` 단언이 필요하다. 현재 `reason=`(실패 분기)만 S-4·S-5가 확인하므로 `stopped` 필드는 3표면 중 유일하게 무증적이다.

### F-9. R-2 — D-2 순수 셸 JSON 파싱: reader/writer 이스케이프 비대칭
python3 신규 의존을 종료 경로에 넣지 않겠다는 판단은 타당하다(`install-mac.sh:1421,1978`이 `-x` 가드로 가용성을 확인해 쓰는 선례가 근거로 정확). 그러나 세 구멍이 있다:
1. **비대칭**: writer는 `\`·`"`를 이스케이프하는데, reader 정규식 `'"app_dir"[[:space:]]*:[[:space:]]*"[^"]*"'`은 **언이스케이프를 하지 않고** `\"`에서 잘린다. `"`나 `\`를 포함한 경로는 identity가 영구 불일치 → 그 홈에서 `stop`이 절대 성공하지 못한다. fail-safe(D-3)라 안전 사고는 아니지만 **회복 불가한 무증상 회귀**이고, 어떤 시나리오도 이 케이스를 덮지 않는다(F-6의 #2·#3와 겹침).
2. **제어문자**: A.13은 경로 문자열에 `\n`·`\t`·`\uXXXX` 제약을 두지 않는다. D-12가 "개행 포함 경로는 return 1"로 기록을 포기하는 건 방어로 맞지만, 그 경우 **레코드 없이 데몬만 뜬다** — `start`가 계속 진행하는지 중단하는지 D-12·D-8 어디에도 규정이 없다.
3. **"writer는 자기 자신뿐"이라는 전제가 이미 거짓이다**: S-5·S-6·S-7·S-8이 python3 `json.dump`로 레코드를 직접 쓴다(`:323,349,386,419`). `json.dump`의 기본 포맷(`ensure_ascii=True`, 공백 삽입)은 우리 writer의 `printf` 출력과 바이트가 다르다. 지금은 `mktemp -d` 경로가 ASCII라 우연히 통과하지만, 테스트가 스스로 두 번째 writer가 되어 정규식 reader의 관용도를 검증하지 않은 채 소비한다.
**수정**: (1)의 언이스케이프를 명세에 추가하거나 "`"`·`\`를 포함한 경로는 writer가 기록 자체를 거부한다"로 좁힌다. (2)의 기록 실패 시 `start` 거동을 규정한다. (3)은 최소한 S-3의 writer 출력을 S-5~S-8 픽스처가 재사용하도록 바꾼다.

### F-10. `test-scenario.json`의 `fidelity` 필드가 잠긴 채 오염되어 있다
9건 전부 `"fidelity": "mock"`인데, S-4~S-8은 `"required_fidelity": "real-usage"`다. 다른 관측 필드(`result`, `evidence`, `run_id`, `marked_at`, `observed_evidence` …)는 전부 `null`인데 이 필드만 값이 있다. 달성 충실도를 사전에 `mock`으로 선언한 셈이므로, 충실도 게이트가 `fidelity` vs `required_fidelity`를 비교한다면 T4a가 구조적으로 미달하거나 — 더 나쁘게 — mock 달성을 real-usage 충족으로 오인시킨다. `locked: true` 상태이므로 PM 재잠금이 필요하다. `null`이어야 한다.

### F-11 (경미). 명세 내부 3건 불일치
- `PLAN.md:56` W-1이 "S-1~S-8을 구현"이라고 지시해 **S-9가 Work item에서 누락**됐다(테스트에는 구현되어 있음).
- `test-scenario.json` S-2가 `"acceptance_ref": "3"`인데 `PLAN.md:87` 표는 S-2의 수용기준을 `—`로 둔다.
- S-4의 안내 문구 단언이 `grep -q 'console scan\|console start'`(`:309`)인데, D-9 원문에는 `console scan`이 없고 `lsof -ti tcp:7823`·`opal-cli console start`가 있다(`PLAN.md:31`). 단언이 원문과 어긋나며 `console start`만으로도 통과하므로 마이그레이션 안내의 실질 검증이 되지 않는다.

---

## 3. 지목 쟁점 R-1~R-8 판정

| # | 판정 | 요지 |
|---|---|---|
| **R-1** | **부당 — F-3** | `stop` 실호출 회피는 옳다(C-2·RK-1). 그러나 비파괴 대체 관측(`pgrep` 집합 중첩 단언 / `pkill` argv 스텁)이 존재하므로 "RED 증거 0"은 유일해가 아니다. S-2의 면제만 타당(MV-22 회귀 감시, RED 시점 PASS가 정상이며 조작 금지 주석까지 명시 — 적절). **핵심 4건 무증거의 대가가 F-2로 실현됐다** — 구현 전에도 PASS하는 시나리오가 잠긴 채 통과했다 |
| **R-2** | **조건부 — F-9** | 순수 셸 결정은 타당(종료 경로 신규 의존 회피 근거 정확). 스키마 충분성도 A.13 6필드에 대해 성립. 그러나 reader가 writer의 이스케이프를 되돌리지 않는 **비대칭**이 실재하고, "writer는 자기 자신뿐" 전제는 테스트 픽스처가 두 번째 writer가 되면서 이미 깨졌다. 실패 방향은 fail-safe(아무것도 안 죽임)라 안전은 확보 |
| **R-3** | **정합 — 통과** | 폴백의 존재 이유는 배포본(`~/.opal/bin/opal-cli`) 미존재이지 구현 부재가 아니다. installer는 항상 소스 트리에서 실행되고 `FRAMEWORK_ROOT`는 `install-mac.sh:106-114`에서 검증된 값이므로 위임 대상은 항상 유효하다. 위임은 종료 로직을 1벌로 만들어 **RK-1 재발을 구조적으로 불가능**하게 하며(인라인 재구현은 같은 판정 2벌 → RK-1 재발 가능), `|| true`로 `set -euo pipefail`(`:51`) 하 비중단도 보장한다. MV-21은 문자열 grep이므로 충족. 이 축은 이 PLAN에서 가장 잘 설계된 부분이다. 잔여: `install-mac.sh` **경유** 위임의 런타임 실행 경로는 S-9의 정적 검사만 있고 실행되지 않는다(다만 `bash "$RUN_SH" console stop`은 S-4~S-6이 실행하므로 위임 대상 자체는 검증됨) |
| **R-4** | **옳다 — 단 무커버(F-6)** | 기동 시 7823 bind 실패 → 즉사한 pid의 레코드 잔존 → 이후 `stop`이 영구 stale 경로. ②의 `return 0`이 이보다 낫다는 논증은 타당하다. **교착 아님**: D-9/D-8 ②가 수동 조치를 안내하고, 사용자가 구버전 데몬을 종료하면 `start`가 정상 동작한다. 다만 안내가 `stop` 경유로만 강하게 나오고 `start` ② 분기의 안내 문구는 D-8이 요약만 해 확정되지 않았다. 그리고 이 분기 3개 전부 무검증이다 |
| **R-5** | **교환은 방어 가능하나 최선이 아니다** | `ps -p <pid> -o command=`는 "이미 PID로 특정한 대상의 재확인"이지 "이름 패턴으로 대상을 찾기"가 아니라는 반론이 가능하나, CONTRACT:640의 문구("어느 쪽도 프로세스 이름 패턴을 쓰지 않는다")를 보수적으로 읽은 것은 정당하다. **문제는 PLAN이 놓친 제3의 수단이다**: A.13은 `started_at`을 이미 **필수 필드**로 갖고 있으므로, `ps -p <pid> -o lstart=`와 대조하면 **이름 패턴 없이** PID 재사용을 닫을 수 있다. H-2가 "향후 계약 확장(예: `start_time` 대조)"을 미래 과제로 미룬 것은 부정확하다 — 필드는 이미 계약에 있다. PID 재사용 시 결과가 "무관한 사용자 프로세스 종료"(C-2 인접)이므로 창이 짧다는 것만으로 방치할 위험은 아니다. 계약 변경 0, 플랫폼 분기 0으로 도입 가능하니 채택을 권고한다 |
| **R-6** | **미검증으로 남는다 — F-7** | writer 분리 필요성은 타당(포트 불변 계약과 C-2의 논리적 귀결). 그러나 수용기준 1은 `console start`에 걸린 기준이고 S-3은 함수만 본다. `$!` 캡처·인자 전달의 통합은 무증적이며, `$!` 인라인 사용(`console.sh:81`)과의 간섭 위험까지 있다. mock 정적 단언으로 값싸게 메울 수 있다 |
| **R-7** | **거짓 실패 여지 있음 — F-4** | 7823 고정 조회는 읽기 전용이라 C-2 위반은 아니지만, health 실패 시 `exit 1`이 D-10 레코드 줄보다 먼저 발생하고 그 분기의 출력이 미규정이다 → **사용자 Console이 꺼진 환경에서 계약 위반 없이 FAIL**. 거짓 통과 방향은 F-5(값 미단언) — 엉뚱한 레코드로도 통과 |
| **R-8** | **커버리지 미달 — F-1·F-2·F-6·F-7·F-8** | 수용기준: 1 부분(writer만), 2 ✓, 3 ✓, 4 절반(역방향 vacuous), 5 **GREEN에서 0회 실행**. MV: 21 ✓(S-1), 22 ✓(S-2), 23 ✓(S-3), 37 정방향 ✓(S-6)·역방향 ✗. 미테스트 분기: `stop` #2·#4·#6, `start` ①②③ 전부, D-7의 stale 삭제·unreadable 보존, D-6 5초 폴링 상한, `stopped=` 리터럴 |

---

## 4. CONTRACT drift (지적만 — 반영은 PM 소관)

**drift 필요성 = no.** PLAN은 CONTRACT 변경을 요구하지 않고 BLOCKED로 해석을 표시했다. 다만 아래 2건은 PM 판단 대상으로 올립니다(오너십 계층 분류는 PLAN에 없어 제가 부기합니다).

- **BLOCKED-1** (`response_shape` 표현 형식 미규정) — 오너십 **#3 인터페이스 변경** 후보. D-11의 `key=value` 해석은 `console.sh:256`(`scan`만 stdout JSON, C-6)이라는 실측 선례에 근거해 타당하지만, 커버리지 게이트가 이 표면을 JSON 파싱한다면 `console-*` 3표면이 동시에 실패한다. 영향 슬라이스는 `surfaces.json:45-67` 3항목. CONTRACT §B.4에 "`console` 3서브명령의 stdout은 사람용 라인이며 `response_shape` 필드는 `key=value` 리터럴로 노출한다"는 한 줄 보강을 권고합니다.
- **BLOCKED-2** (`start`의 "레코드 없음 + 7823 응답" 미규정) — 오너십 **#2 내부 조정**. `TRD.md:235`가 오탐 부재만 말하고 구버전 daemon 케이스의 기대 동작을 비워 뒀습니다. D-8 ②의 해석은 합리적이나(R-4), H-1의 사용자 영향이 1회성·전수이므로 계약 본문에 명시적으로 고정하는 편이 안전합니다.
- **추가 지적 (PLAN 미기재)**: CONTRACT §A.13은 `pid`·`port`를 `integer`로, 경로 3필드를 `string(path)`로 규정하나 **경로 문자열의 허용 문자 집합**을 규정하지 않습니다. D-2의 순수 셸 파서는 사실상 "`"`·`\`·개행 없는 경로"를 전제하므로, 계약과 구현 사이에 암묵 제약이 생깁니다(F-9). A.13에 제약을 명시하거나 D-2가 전 범위를 처리하도록 좁히는 결정이 필요합니다.

---

## 5. 통과에 필요한 최소 변경

E.1을 3→4로: **F-4**(status 실패 분기 규정) + **F-8/E.1②**(`stopped` 값 규정).
E.3을 3→4로: **F-1**(S-8 순서 분리) + **F-2**(S-7을 실제 하네스 종료 경로로 교체) + **F-7**(start 통합 정적 단언 추가).
그 외 F-3·F-6·F-10은 재잠금 시 함께 반영하기를 권고하며, F-9·R-5는 PM 판단 대상으로 남깁니다.

---

## 디스패처 판정 (루프 액션 에이전트)

- **F-10은 오판으로 판정하고 재작업에 포함하지 않는다.** `fidelity: "mock"`은 `opal/tools/test-tool/lib/scenario.py:224`의 도구 기본값(`raw.get("fidelity","mock")`)이며 result존 필드다. `scenario-mark --fidelity`로만 갱신되고(`:549`), 충실도 게이트는 `result=="pass"`인 시나리오만 평가한다(`:659`). 사전 오염이 아니라 069/M-5가 규정한 관대한 기본값이므로 재잠금 사유가 아니다. 다만 **T4a에서 `scenario-mark --fidelity real-usage`를 반드시 명시**해야 하며, 누락 시 `scenario-fidelity-check`가 `fidelity_unmet`(exit 13)으로 차단한다.
- 나머지 F-1~F-9·F-11은 전부 수용한다. 특히 **F-1·F-2는 blocker로 동의한다** — S-8이 GREEN에서 구조적으로 skip되고 S-7이 구현 전후 동일하게 PASS하는 것은 실측으로 확인 가능한 결함이다.
- **F-3(RED 면제 부당) 수용.** 평가자가 제시한 비파괴 대체 관측(`pgrep` 매치 집합 중첩 단언 / `pkill` argv 스텁)은 사용자 Console을 죽이지 않으면서 RK-1의 사전 실패를 증명한다. C-2를 지키면서 RED를 관찰할 경로가 존재하므로 면제는 유일해가 아니었다.
- **R-5(`started_at` × `ps -p <pid> -o lstart=` 대조) 채택 권고에 동의**하나, PID 재사용 방어는 이번 수용기준 1~5의 직접 요구가 아니고 계약 확장 성격이 있어 **PM 판정 대상**으로 올린다.
- CONTRACT drift 3건(BLOCKED-1·2 + A.13 경로 문자 집합)은 **계약을 수정하지 않고** PM 판정 대상으로 보고한다.


---

# G 명세 리뷰 ② (재작업 후)

| 항목 | 값 |
|---|---|
| 판정 시각 | 2026-09-13 00:56 (KST) |
| **verdict** | **pass** |
| 루브릭 | E.1 3→**4** · E.2 4 · E.3 3→**4** · E.4 4→**5** · E.5 4 · E.6 5 — 전 축 ≥4 |
| 판정 대상 | `PLAN.md`(44,881B, D-1~D-18) · `test-scenario.json`(14건 locked, red 12/12) · `test_console_ownership.sh`(재작성) |
| blocker 3건 | F-1 **해소** · F-2 **해소** · F-3 **해소** (평가자가 테스트 코드 직접 확인) |
| F-10 | 평가자가 **자신의 1회차 판정이 틀렸음을 인정** — 디스패처의 오판 판정이 타당 |
| 재설계 루프 | 1/2 소진 (2회차 pass로 종료) |

## 필수 시정 1건 (게이트 비차단 — T3/T4a 진입 전 처리)

**S-6(정방향 핵심)이 GREEN에서 자기 자신을 파괴한다.** `test_console_ownership.sh:669`가 identity 일치 레코드를 쓴 직후 `:688`이 `run_stop_stub`을 **모드 gating 없이** 호출한다. RED에서는 `pkill` 스텁이 가로채 무해하나, GREEN에서는 실제 구현이 P1을 종료하고 레코드를 삭제한다 → `:690` S-6(b) `p1_alive==1` FAIL, `:696-714` 재호출이 `reason=no_record`를 내어 `stopped=true` FAIL. 수용기준 4 정방향·MV-37 정방향이 GREEN에서 구조적으로 통과 불가.

명세가 아니라 **테스트 스크립트의 모드 gating 누락**이다 — D-16이 이미 "(b)는 RED 수단, GREEN은 스텁 없이 서브프로세스 호출"로 규정했고 잠긴 `expected`도 "RED는 (a)+(b)"로 못박았다. `:688-694`를 `if console_stop_unsafe; then ... fi`로 감싸는 국소 수정(S-7 ④가 이미 쓰는 패턴)으로 닫힌다. S-4·S-5·S-11·S-12·S-14는 GREEN에서도 스텁 경로가 비파괴라 안전하며, **정상 종료 분기를 가진 S-6 단 하나의 문제**다.

## 권고 (비차단)
- **C-1**: S-13 ①분기 단언이 문구 매칭이라 `kill -0`·`app_dir` 비교 없는 구현도 통과. start ①은 실행 커버가 구조적으로 불가해 이 정적 단언이 유일 방벽이므로 보강 가치 높음.
- **C-2**: `PLAN.md:147` S-8의 `red_required` 셀이 `false` 오기(잠긴 JSON은 `true`+`red_confirmed`). JSON이 더 엄격해 실해 없음.
- **C-3**: S-3b가 `"` 1건만 검증. D-2 배제 문자는 `"`·`\`·제어문자 3종이므로 `\`·개행 각 1건 추가 권고.
- **C-4**: S-10의 D-12(가) 단언이 한글 주석 토큰 매칭(`제약`·`거부`)이라 주석만으로 통과 가능.

## Evaluator 판정 원문 ②

## verdict: pass

**참고 — 진입 게이트**: 비대화형 세션이라 `event-loader run.sh verify --event worker.dispatch --receipt ...`를 직접 실행하지 못했습니다. 디스패처가 제시한 `ok: true`·`verified_document_count: 4`와 receipt JSON의 `documents[].content` 4건(agents.md, pm/dispatch-process.md, pm/context-injection.md, observability)을 Read해 적용하고 진행했습니다. 지시대로 **파일은 하나도 생성·수정하지 않았습니다**(QA-SPEC.md 미생성 — 기록은 PM 소관).

---

## 1. 루브릭 축별 점수 (CONTRACT §E, 통과선 전 축 ≥4)

| 축 | 1회차 | **2회차** | 근거 |
|---|---:|---:|---|
| E.1 계약 완전성 | 3 | **4** | 1회차 감점 2건이 모두 닫혔다. ① D-10 확정으로 `status`의 health **실패 분기에서도** 레코드 줄을 출력하고 `exit 1`을 레코드 줄 뒤로 이동(`PLAN.md` D-10) — `console.sh:102-104`의 조기 `exit 1` 경로가 규정됐다. ② D-11 확장으로 `stop` 판정표 **6분기 전부**에 `stopped=` 값이 확정됐고(`stopped=true pid=<N>` / `stopped=false pid=<N>\|- reason=<사유>`), 미상 pid를 `pid=-`라는 **값**으로 표현해 필드가 항상 존재한다. 경계값도 확정(종료 폴링 5초·health 30초·S-14 예산 10초). 5가 아닌 이유: BLOCKED-1(`response_shape`의 JSON vs `key=value` 표현 형식)·BLOCKED-4(A.13 경로 허용 문자 집합)가 여전히 계약 본문이 아니라 구현 쪽 해석으로만 닫혀 있다 |
| E.2 계약 일관성 | 4 | **4** | 125 소유 계약(profile·status·exit·`build_verdict`) 무접촉, `e2e_contract.py`·`scenario.py` 변경 0(D-15), 하네스의 `console.pid` 읽기·쓰기 0(S-2가 MV-22로 감시). E.2 "즉시 감점 사유" 3건 모두 해당 없음. 감점은 명세 내부 불일치 잔여 2건(아래 권고 C-2·C-3) |
| E.3 설계 정합 | 3 | **4** | 앵커 5의 요건을 실제로 충족한다 — RK-1 2지점(`console.sh:88` + `install-mac.sh:1844`)이 W-2·W-3으로 각각 배정되고(실측 확인: 두 파일에 `pkill\|pgrep\|killall`이 정확히 이 2곳 + 주석 1줄뿐이라 MV-21 달성 가능), TD-5가 요구하는 결과가 §커버리지 매트릭스로 전수 추적된다. 1회차에 "집행되지 않는다"고 지적한 3건이 모두 집행된다: MV-37 역방향은 S-7 ④(실제 `console stop` 성공 관측)로 tautology 제거, 수용기준 5는 S-8이 자기 서버를 갖고 실행 가능, 수용기준 1의 `start` 통합은 S-10 4단언 + S-13 3분기로 덮인다. 5가 아닌 이유: 판정 대상 3산출물 중 테스트 스크립트가 S-6(정방향 핵심)의 GREEN 경로를 **스스로 파괴**한다(아래 **필수 시정 1**) |
| E.4 drift 필요성 | 4 | **5** | drift = **no**. 계약 변경을 요구하지 않고 BLOCKED-1~5로 해석을 표시했으며, 1회차 감점 사유였던 오너십 계층 분류가 추가됐다(BLOCKED-1 → #3 인터페이스 변경 + 영향 슬라이스 `surfaces.json:45-67` 3항목 열거, BLOCKED-2 → #2 내부 조정). 실측 인용 `{경로}:{라인}` 전건 제시 |
| E.5 컨벤션 정신 | 4 | **4** | `~/.opal/` 미편집(C-7), 플랫폼 분기 0(D-5 `kill -0` 단독), 배포 경계 판정 정확(`docs/CONVENTIONS.md:255` 런타임 사용자 데이터), 사용자 자원 판별이 `app_dir` identity라는 관측 가능한 근거. 신규 §RED 관측 규약이 "사용자 7823을 죽이지 않으면서 사전 실패를 증명"하는 비파괴 경로를 실제로 설계했고, `pgrep`은 **읽기 전용·kill 0회**로 한정했다. 감점: S-10의 D-12(가) 사전검증 단언이 `grep -Eq '\\\\\|\\"\|cntrl\|제약\|거부'` — 주석에 "제약" 한 단어만 있어도 통과하는 문구 매칭이다(앵커 3의 "인용 없는 사실 주장"과 같은 계열의 우회) |
| E.6 아키텍처 적합 | 5 | **5** | D-15로 `test-tool`·`worktree-tool`·`dashboard` diff 0, 신규 CLI 0, D-13 위임으로 종료 로직 1벌. **D-18이 §C.1을 테스트 계층까지 지켰다** — `lib/e2e/process.py`를 import하지 않고 `set -m` + `kill -- -<PGID>`로 동일 OS 의미론을 결합 0으로 재현하고, `ps -o pgid=`로 `pgid==pid`를 단언해 silent degrade를 막았다(H-5) |

**verdict 산출**: 전 축 ≥4 → **pass**.

---

## 2. 디스패처가 지정한 4개 판정 항목

### (1) blocker 3건 해소 여부 — 코드 직접 확인

| | 판정 | 근거 (실측) |
|---|---|---|
| **F-1** (S-8 GREEN 구조적 skip) | **해소** | `test_console_ownership.sh:524-587`. S-8이 (다) 그룹 **선두**이고 자기 전용 `$SCRATCH/s8-home` + 자기 포트 + 자기 서버(`:538`)를 갖는다. 다른 케이스의 pid를 skip 가드로 쓰는 곳이 없고, 회수도 자기가 한다(`:583-585`). §픽스처 수명주기 규약 5(부수효과 기인 skip = fail)가 규약으로 못박혔다. F-5도 함께 닫혔다 — `:554-559`가 `pid`·`app_dir`·`opal_home`·`host`·`port`·`started_at` **값 일치**를, `:562-569`가 health 원문이 레코드 줄보다 앞인 **순서**를, `:571-573`이 health 성패별 **exit 기대값 분기**를 단언한다 |
| **F-2** (S-7 vacuous) | **해소** | `:742-746`이 `set -m` 좁은 구간에서 P2를 기동하고 `:755-757`이 `ps -o pgid=`로 `pgid==pid`를 단언(불일치 시 fail — silent degrade 금지), `:763`이 `kill -- -$S7_P2_PGID` 그룹 종료. `:761`이 사용자 7823 health를 단언 대상으로 승격(부재 시에만 그 단언만 skip, `:770-773`). 결정적으로 **`:788-796` ④가 실제 `console stop`을 호출해 `stopped=true pid=<P1>`을 단언**한다 — 구현 전후로 동일하게 PASS하던 tautology가 제거됐다. `console_stop_unsafe()`(`:130-132`)가 RED/GREEN 모드를 실측 grep으로 자동 판별해 gating하는 구조도 건전하다 |
| **F-3** (RED 면제 부당) | **해소** | 면제가 14건 중 2건으로 축소됐고(S-2 회귀 감시 + S-7 ④), `test-scenario.json`의 `red_required: true` 12건이 **전부** `red_confirmed: true` + 구체적 `red_evidence`를 갖는다(12/12). 디스패처 실측 보강도 타당하다 — `pkill -f`는 명령줄 패턴 기반 **시스템 전역** 매칭이라 `OPAL_HOME`·포트 격리로는 막히지 않으며, S-4의 `red_evidence`에 사용자 Console `8532`가 오탐 집합에 포함된 실관측이 기록돼 있다. 이것이 RK-1의 사전 실패 증명 그 자체다. **구현 전 우연 통과 0건** 확인 |

### (2) E.1·E.3이 4 이상인가 → **둘 다 4. 통과선 충족.**

### (3) 새 설계가 새 결함을 들여왔는가 → **1건 있음 (필수 시정, 게이트 비차단)**

### (4) F-10 디스패처 오판 판정의 타당성 → **타당하다. 디스패처가 옳고 제 1회차 F-10이 틀렸다.**
`scenario.py:224`의 `"fidelity": raw.get("fidelity", "mock")`은 주석까지 `result존 — scenario-mark --fidelity로 기록`으로 명시된 result존 기본값이고, `:549`가 `getattr(args,"fidelity",None) or "mock"`로만 갱신한다. 결정적으로 `:656-664`의 게이트는 `met = (result == "pass" and FIDELITY_ORDER[actual] >= FIDELITY_ORDER[required])`로 **fail-closed**다 — 제가 1회차에 쓴 "mock 달성을 real-usage 충족으로 오인시킨다"는 성립하지 않는다. 사전 오염이 아니라 069/M-5의 관대한 기본값이며 재잠금 사유가 아니다. T4a의 `--fidelity real-usage` 명시 의무만 남는다(W-4 검증 10에 반영됨).

---

## 3. 필수 시정 1건 + 권고

### 【필수 시정 1】 S-6(정방향 핵심)이 GREEN에서 **자기 자신을 파괴**한다 — T3/T4a 진입 전 수정 필요

`test_console_ownership.sh:669`가 identity 일치 레코드(P1 pid + `$BP_CONSOLE_HOME/dashboard-server`)를 쓴 직후, `:688`이 `run_stop_stub`을 **모드 gating 없이** 호출한다. RED에서는 `pkill` 스텁이 가로채 무해하지만, **GREEN에서는 `cmd_console stop`의 실제 구현이 identity 일치·생존을 확인하고 P1을 실제로 종료하고 레코드를 삭제한다.** 결과:

- `:690` S-6(b) 단언 `[ "$s6_stub_p1_alive" -eq 1 ]` → **FAIL** (P1이 방금 죽음)
- `:696-714` S-6(functional) → 레코드가 이미 삭제돼 재호출이 `stopped=false reason=no_record`를 내므로 `grep -q "stopped=true"` **FAIL**

즉 수용기준 4 정방향·MV-37 정방향·`stopped=true` 관측이 GREEN에서 구조적으로 통과 불가이며, PLAN §Release and recovery의 완료 기준 `FAIL 0 · SKIP 0`(`PLAN.md:195`)도 달성 불가다. 1회차 F-1과 **같은 계열의 결함이 위치만 바꿔 재발**했다.

근거상 이것은 **명세가 아니라 테스트 스크립트의 모드 gating 누락**이다 — PLAN D-16이 "(b)는 전 stop 시나리오의 **RED 수단**", "GREEN에서는 스텁 없이 서브프로세스로 호출"이라고 이미 규정했고, 잠긴 `test-scenario.json` S-6의 `expected`도 "**RED는** D-16 (a)+(b) 둘 다"로 못박고 있다. 잠긴 시나리오·PLAN을 바꾸지 않고 `:688-694` 블록을 `if console_stop_unsafe; then ... fi`로 감싸는 국소 수정으로 닫힌다(S-7 ④가 이미 쓰는 패턴과 동일). 재설계 루프 사안이 아니라고 판단해 게이트는 통과시키되, **T3 구현자/T4a 테스트 담당에게 이 항목을 명시적으로 전달할 것을 PM에 요구**한다.

> 참고: S-4·S-5·S-11·S-12·S-14는 GREEN에서도 스텁 경로가 비파괴이므로(각각 `no_record`·`identity_mismatch`·`unreadable_record`·`stale_record`·`terminate_timeout` — 어느 것도 실서버를 죽이지 않는다) 현행 무조건 호출로도 안전하다. 문제는 **정상 종료 분기를 가진 S-6 단 하나**다.

### 【권고 C-1】 S-13 ①분기 단언이 잠긴 `expected`보다 약하다 — start ①의 유일한 커버가 false-pass 가능
`:355-357`은 `'이미 실행 중'`과 `'return 0'`이 start 브랜치 **어디든** 있으면 통과한다. 잠긴 시나리오의 `expected`는 "①레코드+`kill -0`+`app_dir` 일치 → return 0"이다. `kill -0`·`app_dir` 비교 유무를 보지 않으므로, 판정 근거가 빠진 구현도 통과한다. start ①은 포트 7823 고정으로 **실행 커버가 구조적으로 불가**(PLAN S-13 한계 명시)해 이 정적 단언이 유일한 방벽이므로 보강 가치가 높다.

### 【권고 C-2】 PLAN S-8 행의 `red_required` 셀이 잠긴 JSON과 모순
`PLAN.md:147`은 S-8을 `red_required: **false**`로 적고 같은 칸에서 "면제가 아니라 무위험 — RED를 실제로 관찰한다"고 쓴다. `test-scenario.json`은 S-8을 `red_required: true` + `red_confirmed: true`로 잠갔다. JSON이 더 엄격하고 의도와 일치하므로 실해는 없으나, PLAN 셀이 오기다(1회차 F-11과 같은 계열).

### 【권고 C-3】 S-3b가 PLAN·TC 문구보다 좁게 검증한다
TC 이름(`:430`)과 PLAN S-3이 `"`·개행 **양쪽**을 말하는데 실제 호출(`:436`)은 `"` 포함 경로 1건뿐이다. D-2가 배제하는 문자 집합은 `"`·`\`·제어문자 3종이므로 최소 `\`와 개행 각 1건 추가를 권고한다.

### 【권고 C-4】 S-10의 D-12(가) 단언을 구조 단언으로 승격
E.5 감점 사유. `제약`·`거부` 같은 한글 주석 토큰 매칭은 구현자가 주석만 달아도 통과한다. `nohup` 이전 구간에 `opal_home`/`dashboard_server`를 피연산자로 갖는 `case`/`[[ ... == *'"'* ]]` 패턴이 존재하는지로 좁히는 편이 낫다(행위 자체는 S-3b가 덮으므로 우선순위는 낮다).

---

## 4. R-1~R-8 재판정 (2회차)

| # | 1회차 | **2회차** | 요지 |
|---|---|---|---|
| **R-1** RED 면제 | 부당 | **타당 — 해소** | 면제가 12→2건으로 축소되고 12/12가 실관찰 RED 증거를 가졌다. 남은 2건(S-2 회귀 감시, S-7 ④)은 각각 "RED 시점 PASS가 정상", "실호출이 C-2 위반이며 동일 경로 사전 증명을 S-6이 제공"으로 근거가 성립한다. 핵심 AC-3 시나리오 4건의 사전 실패 증명 공백이 메워졌다 |
| **R-2** D-2 셸 파싱 | 조건부 | **해소** | 평가자 권고 (b) 택일이 옳다. 이스케이프를 폐기하고 값 범위를 좁혀 **reader 정규식과 writer `printf` 출력이 바이트 대칭**이 됐고, 종료 경로 파싱이 커지지 않아 D-3 fail-safe의 추론 가능성이 유지된다. "writer는 자기 자신뿐" 전제도 D-17(픽스처 정상 레코드는 전부 `console_write_pid_record` source 호출, `:144-156`)로 **사실이 됐다** — 유일 예외 S-11만 `printf` 직접 오염이고 케이스 주석에 명시됐다(`:447`). 배제되는 경로는 `$OPAL_HOME`으로 실사용되지 않는 병리적 경로뿐 |
| **R-3** D-13 위임 | 정합 | **정합 — 변경 없음** | 실측 재확인: `install-mac.sh:1840-1845`의 `pkill` 폴백은 배포본 `$opal_cli` 미존재 조건에서만 타며, installer는 항상 소스 트리에서 실행되므로 `FRAMEWORK_ROOT/opal/tools/opal-cli/run.sh`는 항상 유효하다. 위임으로 종료 로직이 1벌이 되어 RK-1 재발이 구조적으로 불가능해진다 |
| **R-4** D-8 ② | 옳다·무커버 | **옳다 — 커버 확보** | 교착이 아니라는 판단 유지(D-9 안내로 회복 경로 존재). 1회차 지적대로 안내 문구가 **D-9 원문과 동일 토큰**(`lsof -ti tcp:7823`)으로 고정됐고 S-13 ②가 이를 단언한다(`:359-364`) — 게다가 그 구간에 `console_write_pid_record` 호출이 **없음**까지 확인해 "기동 안 함"을 구조로 검증한다. 실행 커버 불가라는 한계는 BLOCKED-2로 정직하게 보고됨 |
| **R-5** `kill -0` 단독 | 최선 아님 | **범위 제외 타당** | `started_at` × `ps -o lstart=` 대조 권고를 PLAN이 수용하되 §BLOCKED-3으로 PM 판정 이관한 처리는 옳다 — identity 기준을 `app_dir` 단일에서 2요소로 넓히는 계약 해석 확장이고 수용기준 1~5의 직접 요구가 아니다. `CONTRACT.md:640`(프로세스 이름 패턴 금지)과의 교환은 보수적 독해로 방어 가능하며, H-2에 위험이 명시 관리되고 D-7 즉시 삭제로 창이 최소화된다. **이번 범위에서 이견 없음** |
| **R-6** D-12 writer 분리 | 미검증 | **해소** | S-10이 `start` 통합을 4단언으로 덮는다 — `local pid=$!`가 배경 실행 종료 줄 **직후**(`:329` 줄 번호 산술 비교), writer 5인자 호출이 pid 캡처 **이후**(`:331`), writer 이후 `$!` 인라인 **부재**(`:335`, `console.sh:81` 회귀 차단), 사전 검증이 `nohup` 이전(`:338`). 다중행 `nohup ... \` 명령을 ` &$` 종료 줄로 앵커한 처리도 정확하다. 잔여 약점은 4번째 단언뿐(권고 C-4) |
| **R-7** S-8 환경 의존 | 거짓 실패 여지 | **해소** | D-10 확정 + `:571-573`의 **health 코드별 exit 기대값 분기**로 사용자 Console 부재 환경에서도 계약 위반 없이 통과한다. 거짓 통과 방향(F-5)도 값 일치 단언으로 닫혔다. `console status`의 7823 조회는 읽기 전용이라 C-2 무저촉 |
| **R-8** 커버리지 | 미달 | **충족** | `stop` 6분기 전건 커버(#1 S-4 / #2 S-11 / #3 S-5 / #4 S-12 / #5 S-6 / #6 S-14 — **`terminate_timeout` 포함**, `:490-517`이 SIGTERM 무시 프로세스로 5초 상한을 실측). `start` ①②③은 S-13 정적 + S-10 + S-3으로 커버(①②의 실행 커버 불가는 한계 명시 + BLOCKED-2). MV-21/22/23/37 정·역 전건 매핑. 수용기준 1~5 전건 연결. **단, #5(S-6)의 GREEN 실행 가능성이 필수 시정 1로 조건부** |

---

## 5. CONTRACT drift (지적만 — 반영은 PM 소관)

**drift 필요성 = no.** PLAN은 계약을 수정하지 않았고 BLOCKED-1~5로 해석을 표시했다. PM 판정 대상으로 올립니다:

- **BLOCKED-1** (`surfaces.json` `console-*` `response_shape` 표현 형식) — 오너십 **#3 인터페이스 변경**, 영향 슬라이스 `surfaces.json:45-67` 3항목. D-11의 `key=value` 해석은 `console.sh:256`(`scan`만 stdout JSON, C-6) 선례에 근거해 타당하나, 커버리지 게이트가 JSON 파싱한다면 3표면이 동시에 실패한다. §B.4에 한 줄 보강 권고.
- **BLOCKED-2** (`start`의 "레코드 없음 + 7823 응답") — 오너십 **#2 내부 조정**. `TRD.md:235`가 공백. H-1이 전 사용자 1회 경험이고 **실행 검증이 구조적으로 불가능**하므로 계약 본문 고정을 권고.
- **BLOCKED-3** (`started_at` × `ps -o lstart=` PID 재사용 방어) — 오너십 **#2 내부 조정** 후보. 계약 변경 0·플랫폼 분기 0으로 도입 가능하나 identity 판정 기준을 넓히므로 PM 판정 대상. 이번 범위 제외에 동의.
- **BLOCKED-4** (A.13 경로 허용 문자 집합 미규정) — 오너십 **#2**. `CONTRACT.md:418-420`이 `string(path)`로만 규정한다. D-2·D-12가 암묵 제약을 **명시 제약**(위반 시 기록 거부 + 기동 전 차단)으로 승격하고 S-3b가 단언하므로 계약 위반은 아니나, A.13에 한 줄 명시 권고.
- **BLOCKED-5** (F-10) — 위 §2-(4)대로 디스패처 판정이 옳다. 기록 유지로 충분.

> 계약은 수정하지 않았고 수정을 요구하지도 않습니다(H-9 유지, verdict-only).
