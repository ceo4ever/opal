<!-- @header {"module":"PLAN","layer":"task-record","domain":"oppl","description":"T02 Console 프로세스 소유권 — PID 레코드 기반 start/stop/status 전환과 광역 pkill 2지점 제거의 구현 계약·Work items·시나리오 설계.","task":"127-T02"} -->

# PLAN: T02 Console 프로세스 소유권

> 입력: [TASK.md](../../TASK.md), [CONTRACT.md](../../CONTRACT.md), [TRD.md](../../TRD.md), [backlog.json T02](../../backlog.json), [surfaces.json](../../surfaces.json)
> 선행: [T01 DONE.md](../T01-실행-스켈레톤/DONE.md)
> 작성: 2026-09-12 23:53 KST · **개정 2026-09-13 00:4x KST (G ① `fail` 반영 — [QA-SPEC.md](QA-SPEC.md) F-1~F-9·F-11)**

## Approach

`opal-cli console`의 프로세스 소유권 판정을 **프로세스 이름 패턴 → PID 레코드 identity**로 바꾼다. 종료 대상 식별의 유일한 근거를 `$OPAL_HOME/run/console.pid`(CONTRACT §A.13 `CONTRACT.md:411-424`)로 옮기고, 광역 `pkill -f "dashboard.backend.main:app"`를 `opal/tools/opal-cli/lib/console.sh:88`과 `scripts/install-mac.sh:1844` **두 지점 모두**에서 제거한다(`TRD.md:237` RK-1 "어느 하나라도 남기면 완화되지 않는다").

범위는 3파일이다 — `console.sh` 수정, `install-mac.sh` 폴백 1블록 수정, `scripts/tests/test_console_ownership.sh` 신설. 하네스(`opal/tools/test-tool/lib/e2e/**`)는 **건드리지 않는다**. TRD TD-5의 "하네스 쪽 대칭 규칙"(`TRD.md:238-239`)은 T01이 이미 충족했다 — `console.pid` 참조 0건, 프로세스 그룹 회수 구현 완료(T01 `DONE.md` §검증 결과 기계검증절).

본 PLAN은 `TEST-SCENARIO.md`·`test-scenario.json`을 생성하지 않는다(`op-dev-plan` 실행 계약). §Test scenario design은 T2(RED) 단계 입력으로서의 **설계 지시**이며, 디스패치가 요구한 `required_fidelity`·`surface_ref`에 더해 G ① 지적을 반영해 **실행 순서·픽스처 수명주기·RED 관측 수단·`red_required`**까지 시나리오별로 확정한다.

### G ① 개정 요약

| 지적 | 반영 |
|---|---|
| F-1 (blocker) 시나리오 간 부수효과 의존 | §픽스처 수명주기 규약 신설 — real-usage 시나리오는 **자기 서버를 기동하고 자기가 회수**한다. 순서 의존 0 |
| F-2 (blocker) S-7 vacuous | S-7을 **프로세스 그룹 기동(`set -m`) + `kill -- -<PGID>` + 종료 후 `console stop` 성공 관측 + 사용자 7823 생존 단언**으로 재설계 (D-18) |
| F-3 (blocker) RED 면제 부당 | §RED 관측 규약 신설 — `pkill` argv 스텁(전 stop 시나리오) + `pgrep` 집합 중첩 단언(S-4·S-6). 사용자 Console 무접촉 |
| F-4 `status` 실패 분기 미규정 | D-10 확정 — **양 분기 모두** 레코드 줄 출력, `exit 1`은 레코드 줄 **뒤**로 이동 |
| F-5 S-8 단언 약함 | S-8을 값 일치 + 출력 순서 단언으로 강화 |
| F-6 무커버 분기 | S-11(#2)·S-12(#4)·S-14(#6)·S-13(start ①②③) 신설 |
| F-7 `start` 통합 무증적 | S-10 신설 (mock 정적, `$!` 캡처·인자 전달·`$!` 인라인 제거) |
| F-8 `stopped` 무증적 | D-11 확장 — 전 분기 `stopped=` 값 확정 + S-6이 stdout 단언 |
| F-9 reader/writer 비대칭 | D-2 개정(이스케이프 폐기·문자 제약) + D-12 개정(기동 전 검증) + 픽스처 writer 단일화 |
| F-11 내부 불일치 3건 | W-1 범위·S-2 수용기준·S-4 문구 단언 정정 |
| F-10 | **오판으로 판정, 설계 미변경** — `fidelity:"mock"`은 `scenario.py:224`의 result존 도구 기본값이며 `scenario-mark --fidelity`로만 갱신된다. T4a가 `--fidelity real-usage`를 명시하지 않으면 `scenario-fidelity-check`가 exit 13으로 차단한다 |
| R-5 (`started_at` × `lstart` 대조) | §BLOCKED-3에 PM 판정 권고로 기록. 이번 구현 범위 제외 |

---

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| **D-1. 레코드 경로·필드는 A.13 그대로** | `$opal_home/run/console.pid`에 `pid`(int)·`opal_home`·`app_dir`·`host`·`port`(int)·`started_at`(ISO-8601) **6필드 JSON**. `app_dir`는 항상 `$opal_home/dashboard-server`로 구성한다 | `CONTRACT.md:411-422`. `$OPAL_HOME` 하위 런타임 사용자 데이터 쓰기이므로 배포본 직접 편집 금지의 대상이 아니다(`docs/CONVENTIONS.md:255`, `TRD.md:233`) |
| **D-2. (개정) JSON 입출력은 순수 셸 + 이스케이프 없는 문자 제약** | 쓰기: `printf`로 6필드 JSON을 **이스케이프 없이** 생성한다. 대신 `opal_home`·`app_dir` 값에 `"`·`\`·제어문자(개행·탭 포함)가 하나라도 있으면 **기록을 거부**한다(D-12). 읽기: 필드별 정규식 1건(`grep -o '"pid"[[:space:]]*:[[:space:]]*[0-9]\+'` / `'"app_dir"[[:space:]]*:[[:space:]]*"[^"]*"'`)으로 추출하며 줄 구조에 의존하지 않고 **언이스케이프도 하지 않는다** | G ① F-9(1) 반영. 원안은 writer만 이스케이프하고 reader가 되돌리지 않아, `"`·`\` 포함 경로에서 identity가 영구 불일치(= 그 홈에서 `stop`이 절대 성공하지 못함)하는 무증상 회귀가 있었다. 평가자 권고 (b)를 택한다 — **reader에 언이스케이프를 추가(a)하면 종료 경로의 파싱 코드가 커져 D-3 fail-safe의 추론 가능성이 떨어진다.** 값 범위를 좁히면 reader 정규식이 writer 출력과 **바이트 단위로 대칭**이 되고, 배제되는 경로는 `$OPAL_HOME`으로 실사용되지 않는 병리적 경로뿐이다. python3 신규 의존을 종료 경로에 넣지 않는 판단은 유지한다 — `install-mac.sh:1421`·`:1978`이 `/usr/bin/python3`를 `-x` 가드로 확인해 쓰는 선례가 근거다. JSON 유효성은 테스트가 `python3 -m json.tool`로 검증한다(`scripts/tests/test_console_scan.sh:13` 선례) |
| **D-3. 파싱 실패·필드 부재는 fail-safe — 아무것도 죽이지 않는다** | `pid`가 정수로 추출되지 않거나 `app_dir`가 추출되지 않으면 즉시 경고 분기로 빠지고 `kill`을 호출하지 않는다. 레코드 파일도 지우지 않는다 | `CONTRACT.md:596` "레코드 없음·identity 불일치면 **아무것도 죽이지 않고** 경고로 종료". 파싱 실패는 identity 미확인과 같으므로 동일 처리한다. `TASK.md:36` C-2 |
| **D-4. `stop`의 if/else 분기 구조 보존** | `if <레코드 identity 검증 + 종료 성공>; then success; else warn; fi` — 반환값이 성공/경고를 가르는 현행 골격(`console.sh:88-92`)을 유지하고 **판정 근거만 교체**한다. exit code는 현행과 동일하게 양 분기 모두 0 | 현행 호출자가 `stop`의 비영점 종료를 기대하지 않는다 — `scripts/install-mac.sh:1842`가 `|| true`로 감싸 무시한다. exit 계약을 바꾸면 설치 경로에 회귀가 생긴다 |
| **D-5. 생존 판정은 `kill -0`** | `kill -0 "$pid" 2>/dev/null` 단일 수단. `ps`·`pgrep`·`lsof`·OS 분기 없음 | POSIX 공통이라 플랫폼 조건문이 필요 없다(`docs/CONVENTIONS.md:259-262`). `ps -p <pid> -o command=`로 명령줄을 재확인하는 보강은 **프로세스 이름 패턴 사용**에 해당해 `CONTRACT.md:640`이 금지한다. `started_at` × `ps -o lstart=` 대조는 §BLOCKED-3 |
| **D-6. 종료 신호는 SIGTERM 단독 + 최대 5초 폴링** | `kill "$pid"` 후 `kill -0`로 최대 5초 폴링. 사라지면 success, 5초 후에도 살아 있으면 warn. **SIGKILL 승격 없음** | 현행 `pkill`도 SIGTERM 단독이다(`console.sh:88`). 강제 종료 승격은 계약에 없는 새 행동이며 uvicorn은 SIGTERM에 정상 종료한다. 폴링은 `install-mac.sh:1846-1853`의 기존 3초 health 대기와 중복되지 않는다(그쪽은 포트 해제 대기) |
| **D-7. 레코드 수명주기** | `start`: `mkdir -p "$opal_home/run"` 후 기록(기존 파일 무조건 덮어씀). `stop` 성공: 레코드 **삭제**. `stop` stale: 레코드 **삭제** + warn, kill 호출 0. `stop` identity 불일치·파싱 실패: 레코드 **보존** + warn | 성공·stale 삭제는 다음 `start`의 오판을 막는다. 불일치 레코드는 **우리 것이 아니므로** 지우지 않는다(D-3과 같은 근거) |
| **D-8. `start`의 3분기** | ① 레코드 존재 + `kill -0` 성공 + `app_dir == $opal_home/dashboard-server` → `warn "이미 실행 중 (PID: N)"` + `return 0`. ② 레코드 없음·stale·불일치인데 `$health_url`이 응답 → `warn "PID 레코드 없이 ${host}:${port}가 응답 중 — 이 프로세스는 opal-cli가 소유하지 않습니다"` + **D-9와 동일한 수동 조치 문구**(`lsof -ti tcp:7823` 확인 → 수동 종료 → `opal-cli console start`) + `return 0`(**기동 안 함, 레코드도 쓰지 않음**). ③ 그 외 → D-12 사전 검증 → 기존 전제 점검 → 기동 → 레코드 기록 | ②가 구버전 daemon 케이스다(`TRD.md:235`). 여기서 기동하면 7823 bind 실패로 **즉사한 pid의 레코드**가 남아 이후 `stop`이 stale 경로로만 돌게 되어 더 나쁘다. `return 0` 유지로 현행 health-only 분기의 종료코드(`console.sh:54-57`)를 보존한다. G ① R-4 지적 반영 — ②의 안내 문구를 요약이 아니라 **D-9 원문과 동일 토큰**으로 고정해 S-13이 단언 가능하게 한다 |
| **D-9. `stop`의 레코드 부재 경고에 마이그레이션 안내를 포함한다** | 레코드 부재 분기 출력: `warn "실행 중인 OPAL Console 데몬 레코드를 찾을 수 없습니다: <경로>"` + `info "이 버전은 PID 레코드로 소유 프로세스만 종료합니다. 이전 버전에서 기동한 데몬은 레코드가 없어 종료되지 않습니다 — 'lsof -ti tcp:7823' 로 확인 후 수동 종료하고 'opal-cli console start' 로 재기동하세요."` **단언 토큰: `lsof -ti tcp:7823`** | 계약상 "아무것도 죽이지 않음"은 **기존 사용자 전원에게 업그레이드 직후 1회** 발생한다(H-1). 안내가 없으면 "stop이 안 듣는다"는 무증상 회귀로 보인다. G ① F-11(3) 반영 — 단언 토큰을 `console start` 같은 약한 문자열이 아니라 이 분기에만 등장하는 `lsof -ti tcp:7823`으로 고정한다 |
| **D-10. (개정·확정) `status`는 health 성공·실패 **양 분기 모두** 레코드 줄을 출력하고, exit code만 health가 결정한다** | 출력 순서 고정: ① health success/warn 줄 ② health 성공 시 `echo "$response"`(JSON 원문, 위치 불변) ③ **레코드 줄**(양 분기 공통) ④ health 실패 시에만 `exit 1`. 레코드 있음 → `info "소유 프로세스: pid=<N> app_dir=<경로>"` + `info "opal_home=<경로> host=<H> port=<P> started_at=<T>"`. 없음 → `warn "PID 레코드 없음: <경로> — 이 Console은 opal-cli가 소유하지 않습니다"`. stale → `warn "stale 레코드: pid=<N> (종료됨)"` | G ① F-4 반영. 원안은 "뒤에 덧붙인다"고만 해 **`console.sh:102-104`의 `exit 1`이 레코드 줄보다 먼저 발생**하는 경로를 규정하지 않았다. 그 결과 사용자 Console이 꺼진 환경(CI·신규 머신)에서 S-8이 계약 위반 없이 FAIL한다. `exit 1`을 레코드 출력 뒤로 옮기면 **소유권 관측이 health 가용성에 의존하지 않는다** — R-15 관측 목적(`CONTRACT.md:597`)에 정합하고, exit 의미는 현행과 동일하게 보존된다 |
| **D-11. (확장) 출력 형식은 `key=value` 사람용 라인 — 전 분기 값 확정** | stdout에 JSON을 내지 않는다. `surfaces.json`의 `response_shape` 필드명을 리터럴로 노출한다. `console-stop` 값 계약: 성공 → `stopped=true pid=<N>`. 실패 전 분기 → `stopped=false reason=<사유>`이며 pid를 아는 분기(#4·#5·#6)는 `pid=<N>`, 모르는 분기(#1·#2·#3)는 `pid=-`를 함께 낸다 | G ① F-8 반영 — 원안은 실패 분기의 `reason=`만 정하고 `stopped` 값을 비워 3표면 중 `console-stop`의 핵심 필드가 무증적이었다. `pid=-`는 "미상"을 값으로 표현해 필드가 항상 존재하게 한다. `console` 계열에서 stdout JSON 1줄 계약을 가진 것은 `scan`뿐이다(`console.sh:256` C-6). §BLOCKED-1 참조 |
| **D-12. (개정) writer는 인자 기반 함수 + `start`는 기동 **전** 경로를 검증한다** | `console_write_pid_record <opal_home> <app_dir> <host> <port> <pid>` 신설. 반환 0=성공, 1=값 제약 위반(D-2) 또는 파일 쓰기 실패. **`start`의 거동**: (가) `nohup` **이전**에 `opal_home`·`app_dir`의 문자 제약을 검사하고, 위반이면 `error` + `exit 1`로 **기동하지 않는다**. (나) 기동 후 writer가 그래도 1을 반환하면(mkdir 실패·디스크 만재 등) `warn "PID 레코드를 기록하지 못했습니다 — 이 데몬은 'opal-cli console stop'으로 종료되지 않습니다"` + D-9 동일 수동 조치 문구를 내고 **데몬은 그대로 둔다**(이미 뜬 프로세스를 소유권 판정 없이 죽이지 않는다, D-3) | G ① F-9(2)·F-7 반영. (가)의 근거: 레코드 없이 데몬만 뜨면 그 데몬은 영구히 `stop` 불가가 되어 **H-1과 동일한 상황을 새로 만든다**. 기동 전 차단은 회복 가능하다(사용자가 `OPAL_HOME`을 바꿔 재시도). (나)는 기동 성공 후에는 되돌릴 수 없으므로 안내로 닫는다. writer 분리 자체의 근거는 불변 — `start`는 포트 7823 고정이라(`console.sh:40`, `CONTRACT.md:595` "인자·포트는 불변") 격리 환경에서 실행할 수 없고(C-2), 포트 override 환경변수 도입은 계약 위반이다 |
| **D-13. `install-mac.sh` 폴백은 소스 트리 `opal-cli/run.sh`에 위임한다(구현 중복 0)** | `console_autostart()`의 종료 블록(`scripts/install-mac.sh:1839-1845` — `if` :1841, `pkill` :1844, `fi` :1845)을 `if [[ -x "$opal_cli" ]] → 배포본 위임 / elif [[ -f "$FRAMEWORK_ROOT/opal/tools/opal-cli/run.sh" ]] → OPAL_HOME="$opal_home" bash "$FRAMEWORK_ROOT/opal/tools/opal-cli/run.sh" console stop \|\| true / else → warn 후 아무것도 죽이지 않음` 3분기로 교체 | 폴백의 존재 이유는 **배포본 `~/.opal/bin/opal-cli` 미배포**이지 구현 부재가 아니다 — installer는 항상 소스 트리에서 실행되며 `FRAMEWORK_ROOT`가 검증된 값으로 존재한다(`scripts/install-mac.sh:106-114`). 위임하면 종료 로직이 1벌만 남아 RK-1 재발이 구조적으로 불가능해진다. `\|\| true`로 installer `set -euo pipefail`(`:51`) 하 비중단을 보장한다. (G ① R-3: "이 PLAN에서 가장 잘 설계된 부분" — 변경 없음) |
| **D-14. `started_at` 취득은 `date`(POSIX)** | `date +%Y-%m-%dT%H:%M:%S%z` | 런타임 코드다. `node ~/.opal/tools/date/date.js` 규칙은 에이전트의 문서 기록 시점 규칙이며 배포 셸 스크립트의 런타임 의존으로 옮기지 않는다 |
| **D-15. 하네스·`e2e_contract` 변경 0** | `opal/tools/test-tool/**`, `opal/tools/worktree-tool/**`, `dashboard/**` diff 0 | `CONTRACT.md:616-640` §C.1 무의존. MV-22는 T01이 이미 달성했고 T02는 이를 **깨지 않는 것**으로 충족한다 |
| **D-16. (신설) RED 관측은 `pkill` argv 스텁으로 수행한다** | `console stop`을 호출하는 모든 시나리오의 RED 실행은 **`pkill`을 argv만 기록하는 셸 함수로 오버라이드한 상태에서 `console.sh`를 source하고 `cmd_console stop`을 호출**한다. 단언: argv 로그에 `-f dashboard.backend.main:app`이 기록됨(= 전역 패턴 종료 시도의 실관측) + 어떤 프로세스도 죽지 않음. GREEN 실행은 스텁 없이 `bash opal/tools/opal-cli/run.sh console stop` 서브프로세스로 호출하고, 그때 argv 로그가 **비어 있음**을 함께 단언한다 | G ① F-3 반영. 원안의 "RED 증거 0" 면제는 부당하다고 판정됐다 — 실제로 F-2(구현 전후 동일하게 PASS하는 S-7)를 놓쳤다. 현행 `console.sh:88`의 `pkill`을 실호출하면 사용자 7823 Console을 죽이므로(C-2 위반, RK-1 그 자체) **직접 호출은 여전히 금지**다. 스텁 오버라이드는 전역 패턴 호출을 실관측하면서 아무것도 죽이지 않는 유일한 등가 관측이다. RED와 GREEN의 호출 경로가 다른 비대칭은 GREEN 쪽 argv 로그 공백 단언 + S-1의 정적 0건 단언이 보완한다 |
| **D-17. (신설) 픽스처 레코드의 writer는 단일하다** | 시나리오 픽스처가 만드는 **정상 레코드는 전부 `console_write_pid_record`를 source 호출**해 생성한다. python `json.dump`·수기 JSON 직접 기록을 금지한다. 예외는 **의도적 오염 레코드**(S-11 unreadable)뿐이며, 이때만 `printf`로 직접 작성하고 그 사실을 케이스 주석에 명시한다 | G ① F-9(3) 반영. 픽스처가 두 번째 writer가 되면 `json.dump`의 기본 포맷(`ensure_ascii=True`, 공백)이 우리 `printf` 출력과 바이트가 달라, 정규식 reader의 관용도를 **검증하지 않은 채** 소비하게 된다. 단일 writer는 S-3이 검증한 그 출력 그대로를 S-4~S-8이 소비하도록 만든다 |
| **D-18. (신설) S-7 역방향은 실제 프로세스 그룹 회수를 재현한다 — 하네스를 import하지 않는다** | E2E 역 서버를 `set -m` 구간에서 백그라운드 기동해 **자기 pgid를 갖게** 하고(`ps -o pgid= -p <pid>`로 `pgid == pid` 확인), 종료는 `kill -- -<PGID>`로 그룹 단위 수행한다. T02는 `opal/tools/test-tool/lib/e2e/process.py`를 **import하지 않는다** | G ① F-2 반영. 원안 S-7은 평범한 `kill -TERM <pid>`여서 구현 전후 동일하게 PASS하는 tautology였고, PLAN 기술(`kill -- -<PGID>`)과도 어긋났다. **`terminate_process_group` 호출 여부 판단**: `CONTRACT.md:635`의 무의존은 두 **도구**의 런타임 상호 호출을 금지하며 테스트 하네스는 그 대상이 아니다. 그러나 opal-cli 테스트가 test-tool lib에 import 의존을 만들면 §C.1이 0으로 유지하려는 결합이 테스트 계층으로 되살아나고, T01 모듈 시그니처 변경이 T02 테스트를 깨뜨린다. `set -m`은 `spawn_process_group`(`process.py:78` `start_new_session=True`)과 **동일한 OS 의미론**을 결합 0으로 재현하므로 이쪽을 택한다. macOS에 `setsid` 바이너리가 없다는 점도 `set -m` 선택의 실무 근거다 |

### 변경 후 `stop` 판정표 (구현자 확정 사양 — F-8 반영)

| # | 조건 | kill 호출 | 레코드 파일 | 분기 | stdout(`console-stop` 표면) |
|---|---|---|---|---|---|
| 1 | 레코드 파일 없음 | 없음 | — | warn | `stopped=false pid=- reason=no_record` + D-9 마이그레이션 안내(`lsof -ti tcp:7823`) |
| 2 | 파싱 실패(`pid` 비정수 또는 `app_dir` 부재) | 없음 | 보존 | warn | `stopped=false pid=- reason=unreadable_record` |
| 3 | `app_dir != $opal_home/dashboard-server` | 없음 | 보존 | warn | `stopped=false pid=- reason=identity_mismatch` (관측한 `app_dir` 별도 출력) |
| 4 | identity 일치 + `kill -0` 실패 | 없음 | **삭제** | warn | `stopped=false pid=<N> reason=stale_record` |
| 5 | identity 일치 + 생존 + 5초 내 종료 | `kill <pid>` | **삭제** | **success** | `stopped=true pid=<N>` |
| 6 | identity 일치 + 생존 + 5초 후에도 생존 | `kill <pid>` | 보존 | warn | `stopped=false pid=<N> reason=terminate_timeout` |

---

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. RED 시나리오·테스트 신설 | `opal-test-agent` (T2, mode: red) | `scripts/tests/test_console_ownership.sh` (신설) | §Test scenario design의 **S-1~S-14 전 14건**을 §픽스처 수명주기 규약·§RED 관측 규약에 따라 구현. 배치 관행은 `scripts/tests/test_console_scan.sh`(`:30-34` REPO_ROOT, `:40-60` pass/fail/skip 카운터, `:63-64` `mktemp -d`+`trap`, `:85-90` 캡처 헬퍼, `:553-563` 최종 요약·exit). 구현 전 RED 실관찰 | 없음 | P1 | AC-3, C-2, T02-acc 1~5 |
| W-2. `console.sh` PID 레코드 전환 | `opal-task-agent`(생성자, T3) | `opal/tools/opal-cli/lib/console.sh` | ① `console_record_path`·`console_write_pid_record`(D-12)·`console_read_pid_field`(D-2) 헬퍼 신설 ② `start`(:45-85)를 D-8 3분기로 재구성 + D-12(가) 사전 검증 + 기동 직후 `local pid=$!` 캡처 → writer 5인자 호출 → `pid_record_path=`·`pid=`·`host=`·`port=`·`log_file=` 출력(`surfaces.json:49`). **`:81`의 `$!` 인라인 사용을 `$pid`로 교체**(F-7 — writer 호출 삽입으로 `$!`가 다른 잡을 가리킬 위험 제거) ③ `stop`(:87-93)의 `pkill`(:88) 제거 → 판정표 6분기(D-4 골격·D-11 출력) ④ `status`(:95-106)를 D-10 순서로 재구성(`exit 1`을 레코드 줄 뒤로 이동) ⑤ 파일 헤더 `변경이력` `v1.5` 행 추가(`:22-27` 관행) | W-1 | P2 | AC-3, C-2, C-7, T02-acc 1·2·3·5 |
| W-3. `install-mac.sh` 폴백 `pkill` 제거 | `opal-task-agent`(생성자, T3) | `scripts/install-mac.sh` | `console_autostart()` 종료 블록(`:1839-1845`)을 D-13 3분기로 교체. `pkill -f "dashboard.backend.main:app"`(`:1844`) 삭제. 헤더 `변경이력` `v4.9` 행 추가(`:7-49` 관행) | W-2 | P3 | AC-3, C-7, T02-acc 3 |
| W-4. RED→GREEN 재실행·회귀 확인 | `opal-test-agent` (T4a, 독립 검증) | (코드 변경 없음) | §Release and recovery 검증 명령 전건 실행 + 사용자 7823 Console health 전후 동일 확인 + **`scenario-mark --fidelity real-usage` 명시**(F-10 디스패처 판정 — 누락 시 `scenario-fidelity-check` exit 13) | W-3 | P4 | AC-3, C-2, T02-acc 4 |

**병렬 판단**: W-2와 W-3은 서로 다른 파일이지만 W-3이 W-2의 `stop` 구현에 **위임**하므로(D-13) 실행 그룹을 분리했다. W-1은 RED-first 계약상 구현보다 앞선다.

**문서 변경 대상 없음**: `docs/ARCHITECTURE.md` §OPAL Console은 Console의 역할·포트만 기술하고 종료 수단을 기술하지 않아 이번 구현으로 내용이 달라지지 않는다. `CONTRACT.md`는 수정 금지 대상이다.

---

## Test scenario design

T2(RED) 입력. T02 커버 표면은 `console-start`·`console-stop`·`console-status` 3건이다(`surfaces.json:45-67`).

### 격리 규약 [MUST]

- `SCRATCH="$(mktemp -d)"` + `trap 'cleanup' EXIT`. `cleanup`은 기동한 pid를 전부 `kill` 후 `rm -rf "$SCRATCH"`.
- **`cmd_console start`를 호출하지 않는다** — 포트가 7823 고정이라(`console.sh:40`) 사용자 Console과 충돌한다(`TASK.md:36` C-2). 수용기준 1은 D-12 writer 함수 실행(S-3) + `start` 블록 정적 단언(S-10)으로 나누어 검증한다.
- 서버는 전부 **ephemeral 포트**: `python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1]);s.close()'`. 취득 포트가 `7823`이면 즉시 fail.
- 시나리오별 `OPAL_HOME`은 **케이스 전용 디렉터리**($SCRATCH/<case-id>/console-home/.opal, $SCRATCH/<case-id>/e2e-home/.opal)로 분리한다. 사용자 `~/.opal`을 쓰기 대상으로 삼지 않는다.
- 픽스처: 케이스별로 `mkdir -p <console-home>/.opal/dashboard-server && ln -s "$REPO_ROOT/dashboard" <...>/dashboard-server/dashboard`, `ln -s "$HOME/.opal/.venv" <console-home>/.opal/.venv`(읽기 전용 사용 — T01 `DONE.md` §PM 판정 대상 4의 인터프리터 SSOT 근거).
- 사용자 7823 Console은 **읽기 전용 GET /health만** 접촉한다. 스위트 시작·종료 시 HTTP 코드를 기록하고 동일함을 단언한다. `stop`/`start`/`kill`/`pkill` 대상으로 삼지 않는다.
- 서버 기동은 `uvicorn --app-dir <app_dir> dashboard.backend.main:app --host 127.0.0.1 --port <P>` 로 **실제 ASGI 경로 문자열이 동일**하게 띄운다 — `pkill -f` 오탐의 원인이므로(`CONTRACT.md:601`) 재현 조건으로 유지한다.
- health 준비 대기: 폴링 최대 30초, 초과 시 해당 케이스 `skip`(환경 사유 명시) — silent pass 금지.

### 픽스처 수명주기 규약 [MUST] (F-1)

1. **자급자족**: real-usage 시나리오는 자기 서버를 **자기가 기동하고 자기가 회수**한다. 다른 시나리오가 남긴 서버·레코드·포트를 **전제하지 않는다**.
2. **선행 조건 금지**: 어떤 시나리오도 `kill -0 <다른 케이스의 pid>`를 실행 전제(skip 가드)로 걸지 않는다. 전제 가드는 **자기 케이스가 방금 기동한 pid**에만 허용한다.
3. **케이스 종료 시 회수**: 케이스 말미에 자기 서버를 정리하고(`kill` → 최대 5초 대기), 회수 실패는 `fail`로 기록한다. 전역 `trap`은 2차 안전망일 뿐 1차 수단이 아니다.
4. **순서 독립**: 위 1~3의 결과로 (가)정적 → (나)레코드-only → (다)real-usage 그룹 내부의 **어떤 순서로 실행해도 결과가 같아야 한다**. W-4는 그룹 (다)를 역순으로 1회 더 실행해 순서 독립을 확인한다.
5. **skip 사유 제한**: `skip`은 환경 부재(venv·소스·포트 취득 실패)에만 허용한다. **다른 시나리오의 부수효과로 인한 skip은 결함**이며 `fail`로 처리한다.

### RED 관측 규약 [MUST] (F-3 · D-16)

- RED에서 `console stop`의 실호출(현행 `pkill` 경로)은 **금지**한다 — 사용자 7823 Console을 죽인다(C-2, RK-1).
- 대신 두 가지 비파괴 관측을 쓴다.
  - **(b) `pkill` argv 스텁** — 전 `stop` 시나리오(S-4·S-5·S-6·S-11·S-12·S-14)의 RED 수단. `pkill() { printf '%s\n' "$*" >> "$PKILL_LOG"; return 0; }` 정의 후 `console.sh`를 source하고 `cmd_console stop` 호출. 단언: `$PKILL_LOG`에 `dashboard.backend.main:app`이 기록됨(전역 패턴 종료 시도 실관측), 기동해 둔 프로세스 전부 생존, 사용자 7823 health 불변.
  - **(a) `pgrep` 집합 중첩** — S-4·S-6의 **추가** RED 단언(평가자 명시 요구). 두 서버 기동 상태에서 `pgrep -f "dashboard.backend.main:app"`(kill 0회, 읽기 전용)의 매치 집합이 **P1·P2·사용자 7823 pid를 모두 포함**함을 확인. 오탐 집합 중첩 자체가 RK-1의 사전 실패 증명이다. 사용자 7823 pid는 `lsof -ti tcp:7823`(읽기 전용)로 취득하며 취득 실패 시 그 단언만 `skip`한다.
- GREEN에서는 스텁 없이 `bash opal/tools/opal-cli/run.sh console stop` 서브프로세스로 호출하고, **`$PKILL_LOG`가 비어 있음**을 함께 단언한다(RED/GREEN 호출 경로 비대칭 보완).

### 시나리오 (14건)

**그룹 (가) 정적 — 서버 기동 없음**

| id | 수용기준 | 시나리오 | `required_fidelity` | `surface_ref` | `red_required` |
|---|---|---|---|---|---|
| **S-1** | 3 | `grep -c 'pkill -f "dashboard.backend.main:app"'`가 `console.sh`·`install-mac.sh` 양쪽 **0**. 두 파일에 `pkill`·`pgrep`·`killall` 문자열 0건, `bash -n` 양쪽 exit 0 (MV-21) | `mock` | `console-stop` | **true** — 현행 두 파일에 문자열이 실재하므로 RED FAIL |
| **S-2** | 3 | `grep -rc 'console\.pid' opal/tools/test-tool/`가 0 (MV-22 경계 회귀 감시) | `mock` | `console-stop` | **false** — T01이 이미 달성한 경계의 회귀 감시다. RED 시점 PASS가 정상이며 통과시키려 조작하지 않는다(평가자 R-1도 이 면제만은 타당으로 판정). **표의 수용기준을 `3`으로 확정한다**(F-11②) |
| **S-9** | 3 | `install-mac.sh` `console_autostart` 종료 블록이 D-13 3분기이고 `FRAMEWORK_ROOT/opal/tools/opal-cli/run.sh`에 위임하며 `\|\| true`로 감싸였는지 정적 확인 + `bash -n` | `mock` | `console-stop` | **true** — 현행은 2분기 + `pkill` |
| **S-10** | 1 | **`start` 통합 정적**(F-7): `start` 블록에서 ① `local pid=$!`가 `nohup ... &` **직후 줄**에 온다 ② `console_write_pid_record`가 `"$opal_home" "$dashboard_server" "$host" "$port" "$pid"` 5인자로 호출된다 ③ writer 호출 **이후** `success` 메시지에 `$!`가 등장하지 않는다(`console.sh:81` 인라인 사용 제거) ④ D-12(가) 사전 검증이 `nohup` **이전**에 위치한다 | `mock` | `console-start` | **true** — 현행에 writer 호출·pid 캡처가 없음 |
| **S-13** | 1·2 | **`start` 3분기 정적**(F-6): ① 분기가 레코드 + `kill -0` + `app_dir` 일치를 판정하고 `return 0`한다 ② 분기가 health 응답 시 **`console_write_pid_record` 호출 없이** D-9 동일 토큰(`lsof -ti tcp:7823`)을 출력하고 `return 0`한다 ③ 분기만 기동 경로로 진입한다 | `mock` | `console-start` | **true** — 현행은 health 단일 분기(`console.sh:54-57`) |

> **S-13의 한계 명시**: `start` ①②③의 **실행** 커버는 포트 7823 고정(`CONTRACT.md:595` 불변)과 C-2가 동시에 막는 유일한 사례다. 정적 구조 단언 4개로 대체하며, 이 한계를 DONE.md에 기록한다. H-1(전 사용자 1회 경험)의 실행 검증 공백은 §BLOCKED-2의 PM 판정과 짝을 이룬다.

**그룹 (나) 레코드-only — 서버 기동 없음, 레코드 파일만 조작**

| id | 수용기준 | 시나리오 | `required_fidelity` | `surface_ref` | `red_required` |
|---|---|---|---|---|---|
| **S-3** | 1 | `console.sh` source 후 `console_write_pid_record <console-home>/.opal <console-home>/.opal/dashboard-server 127.0.0.1 <P> <PID>` 호출 → `$OPAL_HOME/run/console.pid` 생성, `python3 -m json.tool` 파싱 성공, 키 집합 정확히 6개, `pid`·`port`가 JSON number, `app_dir == opal_home + "/dashboard-server"`, `started_at`이 ISO-8601 (MV-23). 추가: `"`·개행 포함 경로 인자로 호출 시 **return 1 + 파일 미생성**(D-2·D-12) | `mock` | `console-start` | **true** — 함수 부재로 FAIL |
| **S-11** | 2 | **판정표 #2**: 레코드를 `printf`로 의도적 오염(`"pid": "abc"`, D-17 예외) → `console stop` → `stopped=false pid=- reason=unreadable_record`, **레코드 파일 잔존**, `kill` 0회 | `mock` | `console-stop` | **true** — D-16 (b) 스텁 관측 |
| **S-12** | 2 | **판정표 #4**: identity 일치 + 확실히 죽은 pid(`( exec true ) & p=$!; wait "$p"`로 회수한 pid)로 레코드 기록(D-17 단일 writer) → `console stop` → `stopped=false pid=<N> reason=stale_record` + **레코드 파일 삭제됨** | `mock` | `console-stop` | **true** — D-16 (b) 스텁 관측 |
| **S-14** | 2 | **판정표 #6**: SIGTERM을 무시하는 프로세스(`bash -c 'trap "" TERM; while :; do sleep 1; done'`)를 소유 프로세스로 삼아 레코드 기록 → `console stop` → 약 5초 후 `stopped=false pid=<N> reason=terminate_timeout`, **프로세스 생존**, 레코드 잔존. 종료는 케이스가 `kill -9`로 회수 | `mock` | `console-stop` | **true** — D-16 (b) 스텁 관측 |

> **S-14의 충실도**: 실제 프로세스에 실제 SIGTERM을 보내지만 SUT HTTP 표면을 관통하지 않으므로 `mock`으로 분류한다. D-6의 5초 상한은 이 케이스에서만 관측된다.

**그룹 (다) real-usage — 실제 서버 기동. 각 케이스가 자기 서버를 기동·회수한다**

| id | 수용기준 | 시나리오 | `required_fidelity` | `surface_ref` | `red_required` |
|---|---|---|---|---|---|
| **S-8** | 5 | **status 소유권 노출**(F-1·F-5 반영): **자기 전용** 콘솔 역 서버(P1) 기동 + D-17 writer로 레코드 기록 → `console status` 실행 → ① `pid=<P1의 실제 pid>`·`app_dir=<이 케이스의 console-home>/dashboard-server`·`opal_home=`·`host=127.0.0.1`·`port=<P1>`·`started_at=<기록값>` **값 일치** 단언 ② health JSON 원문 줄이 레코드 줄보다 **앞**인 출력 순서 단언 ③ **사용자 7823 health 성공·실패 어느 쪽이어도 레코드 줄이 출력됨**(D-10) — exit code는 health 코드에 따라 기대값을 분기해 단언 ④ 케이스 말미에 P1 회수 | `real-usage` | `console-status` | **false** — `status`는 `stop`을 호출하지 않아 파괴적 RED 위험이 없고, 현행 `status`에 레코드 줄이 없어 RED FAIL이 자명하다. 스텁 없이 그대로 실행해도 안전하므로 **RED를 실제로 관찰한다**(면제가 아니라 무위험) |
| **S-4** | 2 | **레코드 부재**: 두 서버(콘솔 역 P1, E2E 역 P2) 기동 → 레코드 없이 `console stop` → 두 pid 모두 생존 + 두 health 200, `stopped=false pid=- reason=no_record`, **D-9 토큰 `lsof -ti tcp:7823` 포함**(F-11③) → 케이스가 P1·P2 회수 | `real-usage` | `console-stop` | **true** — D-16 **(a)+(b) 둘 다** 부과 |
| **S-5** | 2 | **identity 불일치**: 두 서버 기동 + 레코드의 `app_dir`를 `<case>/other-home/.opal/dashboard-server`로 기록 → `console stop` → 두 서버 생존, `stopped=false pid=- reason=identity_mismatch`, 레코드 **잔존** → 케이스가 회수 | `real-usage` | `console-stop` | **true** — D-16 (b) |
| **S-6** | 2·4 | **AC-3 정방향(핵심)**: 콘솔 역 P1(app_dir=이 케이스 console-home)과 E2E 역 P2(app_dir=repo `dashboard` 소스 트리, `OPAL_HOME=<case>/e2e-home/.opal`) 동시 기동 → D-17 writer로 P1 레코드 기록 → `console stop`(**stdout 캡처**, F-8) → **P1 종료**(`kill -0` 실패 + health 연결 실패) **AND P2 생존**(`kill -0` + health 200) **AND 레코드 삭제** **AND `stopped=true pid=<P1>` 단언** **AND 사용자 7823 health 코드 불변** (MV-37 정방향) → 케이스가 P2 회수 | `real-usage` | `console-stop` | **true** — D-16 **(a)+(b) 둘 다** 부과 |
| **S-7** | 4 | **AC-3 역방향**(F-2 재설계): 콘솔 역 P1을 통상 기동하고 **E2E 역 P2는 `set -m` 구간에서 기동해 `pgid == pid`를 `ps -o pgid= -p <pid>`로 확인**(D-18) → `kill -- -<P2_PGID>`로 **그룹 단위 종료** → ① P2와 그 그룹 전원 종료 ② **P1 생존 + health 200 + 레코드 파일 잔존** ③ **사용자 `127.0.0.1:7823` Console 생존**을 health 200 **단언**으로 승격(MV-37 역방향 원문, `CONTRACT.md:820`) ④ 그 직후 `console stop`을 실행해 **`stopped=true pid=<P1>`으로 성공** — E2E 그룹 회수가 레코드·identity를 훼손하지 않았음을 T02 코드로 관측(vacuity 제거) | `real-usage` | `console-stop` | **false** — ④의 `stop` 호출을 RED에서 수행하면 현행 `pkill`이 P1·P2·사용자 Console을 함께 죽인다(C-2). 그룹 종료 부분(①②③)은 T02 무관 OS 동작이라 RED 가치가 없다. 대신 ④의 사전 실패 증명은 **S-6의 (a)+(b) RED가 동일 경로로 이미 제공**한다 |

> **사용자 7823 Console 부재 환경**: S-7 ③은 사용자 Console이 애초에 꺼져 있으면 단언 불가다. 이때는 그 단언만 `skip`하고 사유를 기록하되, 스위트 시작 시점 코드(`USER_HEALTH_BEFORE`)와 **동일함**은 항상 단언한다.

**충실도 근거**: acceptance 4(양방향 비간섭)는 두 서버를 실제로 띄우고 실제 `console stop`을 호출해 양쪽 생존을 관측해야만 성립하므로 S-4~S-8을 `real-usage`로 고정했다(모킹·문구 검사 대체 불가). S-1·S-2·S-9·S-10·S-13은 문자열·구조 자체가 계약(MV-21·MV-22·F-7)이고, S-3·S-11·S-12·S-14는 레코드 파일과 CLI 분기만 관찰하므로 `mock`이 적정 충실도다.

### 커버리지 매트릭스 (F-6 폐쇄 확인)

| 대상 | 커버 |
|---|---|
| stop #1 no_record | S-4 |
| stop #2 unreadable_record | **S-11 (신설)** |
| stop #3 identity_mismatch | S-5 |
| stop #4 stale_record + 레코드 삭제 | **S-12 (신설)** |
| stop #5 정상 종료 + `stopped=true` | S-6 (F-8 stdout 단언 추가) |
| stop #6 terminate_timeout (D-6 5초) | **S-14 (신설)** |
| start ① 이미 실행 중 | **S-13 (정적)** |
| start ② 레코드 없이 7823 응답 | **S-13 (정적)** — 실행 커버 불가, 한계 명시 |
| start ③ 정상 기동 + writer 연결 | **S-10 (정적)** + S-3(writer 실행) |
| D-12 값 제약 위반 시 기록 거부 | **S-3 (확장)** |
| D-10 health 실패 분기 레코드 출력 | **S-8 ③ (신설 단언)** |
| MV-21 / MV-22 / MV-23 | S-1 / S-2 / S-3 |
| MV-37 정방향 / 역방향 | S-6 / **S-7 (재설계)** |

---

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. 업그레이드 직후 기존 사용자에겐 레코드가 없다 | `console_autostart`의 "기존 데몬 종료"가 아무것도 죽이지 못하고(판정표 #1), 7823을 구버전 daemon이 계속 점유한다. D-8 ②에 의해 신규 기동도 스킵되어 **업그레이드 후에도 구버전 코드의 Console이 계속 뜬다** | 1회성·비파괴(데이터 손실 없음, health는 계속 200). 사용자가 신규 기능을 못 본다 | 계약이 "아무것도 죽이지 않음"을 MUST로 못박았으므로(`CONTRACT.md:596`) `lsof` 포트 소유자 폴백은 채택하지 않았다. D-9 안내를 `stop`이 출력하고 **D-8 ②가 동일 토큰을 `start`에서도 출력**한다(G ① R-4). 문구 존재는 S-4·S-13이 단언한다 — 원안의 "육안 확인"을 기계 단언으로 승격했다. 실행 경로 검증 공백은 §BLOCKED-2 |
| H-2. PID 재사용 | 레코드의 `pid`가 종료된 뒤 OS가 같은 번호를 재할당하면 `kill -0`+`app_dir` 검사를 통과해 **무관한 프로세스를 종료**할 수 있다 | 낮음(레코드는 `stop` 성공·stale 시 즉시 삭제되어 창이 짧다) | D-7의 즉시 삭제로 창을 최소화한다. **정정(G ① R-5)**: A.13은 `started_at`을 이미 필수 필드로 가지므로 `ps -p <pid> -o lstart=` 대조로 이름 패턴 없이 닫을 수 있다 — "향후 계약 확장"이라는 원안 서술은 부정확했다. 다만 수용기준 1~5의 직접 요구가 아니고 계약 해석 확장이므로 §BLOCKED-3의 PM 판정 대상으로 올린다 |
| H-3. 테스트가 사용자 venv·소스 트리에 의존한다 | `$HOME/.opal/.venv/bin/uvicorn` 또는 `dashboard.backend.main:app` import가 실패하면 그룹 (다)가 전부 실행 불가 | 검증 공백(거짓 통과 아님) | 실패 시 `pass`가 아니라 `skip`으로 사유를 남기고, W-4가 `skip` 0건을 확인 기준으로 삼는다. **부수효과 기인 skip은 `fail`로 처리한다**(수명주기 규약 5) |
| H-4. `$SCRATCH` 서버 기동이 자기 `OPAL_HOME` 하위에 파일을 만든다 | backend가 `console.config.json` 등을 자기 `OPAL_HOME`에 쓸 수 있다 | 없음(전부 `$SCRATCH` 하위, 케이스 회수 + `trap`) | 격리 규약에서 모든 `OPAL_HOME`을 케이스 전용 `$SCRATCH` 하위로 고정 |
| H-5. (신설) `set -m` 부작용 | 테스트 스크립트에서 job control을 켜면 백그라운드 잡의 시그널·터미널 처리가 달라져 다른 케이스에 영향을 줄 수 있다 | 테스트 전용 (제품 코드 무관) | S-7의 기동 구간만 `set -m` … `set +m`으로 **좁게 감싸고**, 직후 `ps -o pgid= -p <pid>`로 `pgid == pid`를 단언해 의도한 효과가 실제로 났는지 확인한다. 효과가 나지 않으면 `fail`(silent degrade 금지) |
| H-6. (신설) RED 스텁의 GREEN 누출 | `pkill` 셸 함수 오버라이드가 GREEN 실행에도 남아 있으면 오탐이 생긴다 | 거짓 통과 위험 | GREEN은 스텁 없는 **서브프로세스**(`run.sh`) 호출로 경로를 분리하고, `$PKILL_LOG` 공백을 함께 단언한다(D-16). 정적 0건 단언(S-1)이 2중 보완 |

---

## Release and recovery

- **적용 순서**: P1(W-1 RED) → P2(W-2 `console.sh`) → P3(W-3 `install-mac.sh`) → P4(W-4 검증). 배포(`./scripts/install-mac.sh`)는 이번 태스크에서 **수행하지 않는다** — 소스 수정만 하고 `~/.opal/` 배포본은 건드리지 않는다(`TASK.md:41` C-7).
- **검증 범위** (verify commands):
  1. `~/.opal/.venv/bin/python -m pytest opal/tools/test-tool/tests -q -rs` → **88 passed, skip 0 유지**(T01 baseline, 회귀 0)
  2. `bash scripts/tests/test_console_ownership.sh` → `verdict: ALL PASS`, FAIL 0 · SKIP 0 (14건)
  3. 같은 스위트를 그룹 (다) 역순 실행 1회 → 결과 동일(수명주기 규약 4)
  4. `bash -n opal/tools/opal-cli/lib/console.sh && bash -n scripts/install-mac.sh` → exit 0
  5. `grep -c 'pkill -f "dashboard.backend.main:app"' opal/tools/opal-cli/lib/console.sh scripts/install-mac.sh || true` → **양쪽 0** (MV-21)
  6. `grep -rn 'console\.pid' opal/tools/test-tool/ || true` → **0건** (MV-22)
  7. `bash scripts/tests/test_console_scan.sh` → 기존 `console` 서브커맨드 회귀 0
  8. `git status --porcelain` 전후 비교 → T02가 만든 산출물이 3파일 + 태스크 문서 외에 없음
  9. 사용자 `127.0.0.1:7823` Console: 스위트 전후 `/health` HTTP 코드 동일
  10. `scenario-mark`에 `--fidelity real-usage`를 S-4~S-8에 대해 명시(누락 시 `scenario-fidelity-check` exit 13)
- **실측 경계**: 그룹 (다)는 케이스당 health 대기 30초 상한, 종료 폴링 5초 상한. S-14는 5초 타임아웃 관측이 목적이므로 케이스 예산을 10초로 둔다. 초과는 `skip`(환경) 또는 `fail`(계약)로 구분 기록한다.
- **실패 시**: 코드 변경은 `console.sh`·`install-mac.sh` 2파일 git revert로 완전 복구된다. 배포본을 수정하지 않으므로 런타임 롤백 절차가 없다. 테스트가 남긴 프로세스는 케이스 회수 → `trap` 순으로 정리하며, 누출 의심 시 `$SCRATCH` 경로와 기록된 pid로만 회수한다(이름 패턴 종료 금지).

---

## BLOCKED

> `CONTRACT.md`는 수정하지 않았다. 아래는 PM 판정 대상 drift·권고 기록이다.

**BLOCKED-1. `surfaces.json` `console-*` `response_shape`의 표현 형식이 계약에 미규정이다.** (오너십 #3 인터페이스 변경 후보)
`console-start` = `{pid_record_path,pid,host,port,log_file}`, `console-stop` = `{stopped,pid,reason}`, `console-status` = `{health,pid,opal_home,app_dir,host,port,started_at}`(`surfaces.json:45-67`)이 **JSON stdout을 요구하는지, 필드 노출만 요구하는지** 미규정이다. `console` 계열에서 stdout JSON 1줄 계약을 가진 것은 `scan`뿐이다(`console.sh:256`, C-6).
→ **진행한 해석(D-11)**: 사람용 라인 유지 + `response_shape`의 모든 필드명을 `key=value` 리터럴로 출력(미상 pid는 `pid=-`). 커버리지 게이트가 JSON 파싱한다면 3표면이 동시에 실패한다. 권고: `CONTRACT.md` §B.4에 "`console` 3서브명령의 stdout은 사람용 라인이며 `response_shape` 필드는 `key=value` 리터럴로 노출한다" 한 줄 보강.

**BLOCKED-2. `start`의 "레코드 없음 + 7823 응답" 기대 동작이 미규정이다.** (오너십 #2 내부 조정)
`TRD.md:235`가 오탐 부재만 말하고 구버전 daemon 케이스를 비워 뒀다.
→ **진행한 해석(D-8 ②)**: 기동하지 않고 D-9 동일 토큰으로 경고 + `return 0`. 근거는 기동 시 bind 실패로 즉사한 pid의 레코드가 남아 `stop`을 영구 stale 경로로 밀어 넣는다는 것이다. **추가 보고**: 이 분기는 포트 7823 고정(`CONTRACT.md:595`)과 C-2가 동시에 막아 **실행 검증이 구조적으로 불가능**하며 S-13의 정적 구조 단언으로만 덮인다. H-1이 전 사용자 1회 경험이므로 계약 본문 고정을 권고한다.

**BLOCKED-3. (신설) PID 재사용 방어 — `started_at` × `ps -p <pid> -o lstart=` 대조.** (평가자 R-5 채택 권고, 디스패처 PM 판정 이관)
A.13이 `started_at`을 이미 필수 필드로 갖고 있으므로, `ps -o lstart=`와 대조하면 **프로세스 이름 패턴 없이**(`CONTRACT.md:640` 무저촉) PID 재사용을 닫을 수 있다. 계약 변경 0·플랫폼 분기 0으로 도입 가능하다.
→ **이번 구현 범위 제외**. 수용기준 1~5의 직접 요구가 아니고, identity 판정 기준을 `app_dir` 단일에서 2요소로 넓히는 **계약 해석 확장**이기 때문이다. H-2로 관리하며 PM 판정을 기다린다.

**BLOCKED-4. (신설) A.13이 경로 문자열의 허용 문자 집합을 규정하지 않는다.** (평가자 §4 추가 지적)
`CONTRACT.md:418-420`은 경로 3필드를 `string(path)`로만 규정한다. D-2의 순수 셸 파서는 사실상 "`"`·`\`·제어문자 없는 경로"를 전제한다.
→ **진행한 해석(D-2·D-12)**: 제약을 **구현 쪽에서 명시적으로 좁히고**(위반 시 기록 거부 + 기동 전 차단), 그 사실을 S-3이 단언한다. 암묵 제약을 명시 제약으로 바꾼 것이므로 계약 위반은 아니나, A.13에 한 줄 명시를 권고한다.

**BLOCKED-5. (기록만) 평가자 F-10은 오판으로 판정됐다.**
`test-scenario.json`의 `fidelity: "mock"`은 `opal/tools/test-tool/lib/scenario.py:224`의 result존 도구 기본값이며 `scenario-mark --fidelity`로만 갱신된다. 사전 오염이 아니므로 재잠금 사유가 아니고 설계를 변경하지 않았다. T4a가 `--fidelity real-usage`를 명시하지 않으면 `scenario-fidelity-check`가 exit 13으로 차단한다(W-4 검증 10).
