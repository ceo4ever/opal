# DONE: OPAL 범용 E2E 하네스 구현 (제안서 태스크 2~9)

> 완료일: 2026-09-13 12:15 | 스킬: //oppl --agentic --wt | 브랜치: `feat/OP-TASK-127`
> **종료 성격: 사용자 지시에 의한 조기 종료.** Loop 2 종료조건(`done-check all_done`) 충족이 아니다.

## 결과

Loop 1(설계 수렴)을 완주해 PRD·TRD·CONTRACT·BACKLOG·surfaces.json을 확정하고 캡틴 승인으로 잠갔다. Loop 2(실행 수렴)에서 백로그 16건 중 **2건(T01·T02)을 완주**했고, 나머지 14건은 백로그에 보존한 채 중단했다.

중단 사유는 결함이나 차단이 아니라 **수행 방식 재검토**다. oppl Loop 2는 태스크마다 `opal-loop-action-agent`가 내부 4축을 비동기로 띄우고 부모가 반환하는 구조여서, 태스크당 감시–재개 왕복이 10회 안팎 발생하고 그때마다 컨텍스트가 재적재된다. T02는 서브에이전트 토큰 328K를 소비했는데 실제 산출물은 셸 스크립트 2개 수정과 테스트 1개였다. 남은 14건은 TRD §6이 파일 단위 변경 지점까지 확정해 둔 잘 정의된 구현 태스크이므로, 수렴 루프가 아니라 Dev 파이프라인이 적합하다는 판단이다(캡틴 판정).

## 확정 산출물 (Loop 1)

| 문서 | 크기 | 내용 |
|---|---|---|
| `PRD.md` | 258행 | 요구사항 26건(R-1~R-19 기능 / NR-1~NR-7 비기능), TASK AC-1~14·C-1~8 전건 역추적, 제안서 §14 태스크 2~9 매핑 |
| `TRD.md` | 672행 | 기술 결정 TD-1~TD-19, 현행 구조 실측, 컴포넌트별 변경 지점(D5 백로그 입력), 위험 RK-1~RK-8 |
| `CONTRACT.md` | 1,000행+ | §A 스키마 15종 · §B 시그니처 · §C 경계 10절 · §D 기계검증 MV-01~MV-42 · §E 루브릭 6축 앵커 · §F TD/R 역추적 |
| `surfaces.json` | 40표면 | cli 7 · driver-op 8 · executor-op 8 · http 17. 전 표면 `auth: none`, `origins` 선언 |
| `BACKLOG.md` / `backlog.json` | 16태스크 | 표면 커버리지 `all_covered: true`, 병렬 그룹 g2·g3 + 통합 태스크 2건 |
| `QA-SPEC-DESIGN-2026-09-12T21-56.md` | — | D6 Evaluator 1·2회차 판정 기록 |

## 구현 완료 태스크

### T01 — 실행 스켈레톤 (주소 주입·CORS 포함, FE→BE 관통)

**변경 파일**: `dashboard/frontend/src/lib/api.ts`(수정) · `dashboard/frontend/src/vite-env.d.ts`(신설) · `dashboard/frontend/.env.development`(신설) · `dashboard/backend/main.py`(수정) · `dashboard/backend/tests/test_cors_env.py`(신설) · `dashboard/frontend/src/lib/api-base-url.test.ts`·`api-env-files.test.ts`(신설) · `opal/tools/test-tool/lib/e2e/{__init__,ports,process,runtime}.py`(신설 478행) · `opal/tools/test-tool/tests/test_e2e_skeleton.py`(신설)

**검증**: 시나리오 8/8 pass · `fidelity-check all_met` (`real-usage`) · test-tool 88 passed(baseline 84+4, 회귀 0) · vitest 161 passed · typecheck exit 0 · `git status` 전후 동일(저장소 `dist/` 미생성) · 사용자 7823 Console 200 유지

**real-usage 실증**: Playwright MCP 프로파일을 타 세션이 점유(사용자 소유 → C-2로 종료 불가)해 디스크의 `chrome-headless-shell`을 CDP로 직접 구동(설치 0건). 관측값 — CORS 주입 포트 == vite 실제 바인딩 포트, `Network.responseReceived {url: 127.0.0.1:50016/api/dashboard, status: 200}`.

**G 게이트 1회차 fail이 거짓 통과를 차단함**: `start_frontend`에 포트 인자가 없어 CORS 주입 origin과 vite 실제 포트가 어긋날 수 있었고, 그러면 CDP는 200인데 앱 fetch는 차단되는 상태가 pass로 기록될 수 있었다.

### T02 — Console 프로세스 소유권 (PID 레코드 전환, 광역 pkill 2지점 제거)

**변경 파일**: `opal/tools/opal-cli/lib/console.sh`(수정 +239) · `scripts/install-mac.sh`(수정 +24) · `scripts/tests/test_console_ownership.sh`(신설 875행)

**검증**: 비간섭 회귀 20/20 ALL PASS · 시나리오 14/14 pass · `fidelity-check all_met` 14/14(`real-usage`) · `pkill|pgrep|killall` 양쪽 파일 0건(MV-21) · `console.pid` 문자열이 test-tool에 0건(MV-22) · test-tool 88 passed(회귀 0) · `bash -n` 양쪽 exit 0 · 사용자 7823 Console 전 구간 200

**AC-3 양방향 실관측**:
- 정방향(S-6): 동일 ASGI 문자열로 P1·P2 동시 기동 → 실제 `console stop` → P1만 종료, P2 생존, 레코드 삭제, `stopped=true pid=<P1>`, 사용자 7823 불변
- 역방향(S-7): `set -m` 그룹 기동(`pgid==pid` 단언) → `kill -- -<pgid>` → P2 종료, P1 생존 + health 200 + 레코드 잔존

**RK-1 사전 실패 증명**: `pgrep -f 'dashboard.backend.main:app'` 매치 집합에 P1·P2·사용자 Console(8532)이 모두 포함됨을 kill 없이 관측. 격리 `OPAL_HOME`·포트로는 `pkill -f`를 격리할 수 없다는 사실의 직접 증거다.

**보안 blocker B-1 태스크 내 해소**: `"pid": 0` 레코드가 판정표 6분기를 모두 통과해 `kill 0`(호출자 프로세스 그룹 전멸)에 도달하던 결함. `install-mac.sh`가 이 경로를 무인 호출하므로 침묵 종료가 성립했다. 광역 `pkill`을 제거한 자리에 "의도치 않게 광역인 kill"을 남긴 셈이다. `_console_pid_sane`(pid≥2)으로 판정표 #2(`unreadable_record`, kill 0회)에 합류시켰고, 격리 프로세스 그룹에 센티넬을 두고 `pid=0/1/-5/abc` 전건 관측으로 증명했다(센티넬 전건 ALIVE).

**major M-3 해소**: 사전 검증과 writer의 검사 기준이 달라(`"`·`\`만 vs 개행·탭·CR도) 개행 포함 `OPAL_HOME`이면 데몬은 뜨고 레코드만 실패해 종료 불가능한 고아가 생기던 문제. `[[:cntrl:]]` 한 클래스로 통일했다.

**T3 중단·재개 경위**: T3 구현 자식이 `rate_limit_event {status: rejected, five_hour, out_of_credits}`로 exit 2 종료. 환경 차단이지 동일 지점 재실패가 아니므로 하네스 재시도를 소비하지 않고 warm resume으로 이어받았다.

## 계약 보강 (Loop 2 중 확정)

구현이 드러낸 계약 공백을 PM 자율 범위(`contract.md` §4 #2 내부 조정)에서 반영했다.

| 절 | 내용 | 계기 |
|---|---|---|
| §C.10 | `kind: "cli"` 표면의 profile·executor 매핑 — **profile은 호출 수단이 아니라 단언 수단이 결정한다**. `cli` profile·executor는 신설하지 않는다(C-1) | T02 T4a. `surfaces.json`에 `cli` 표면 7개인데 `PROFILES`에 `cli`가 없어 워커가 매번 임의 선택해야 했음 |
| §B.4 | `console-*` 출력은 `key=value`이지 JSON이 아님 + `console-stop` 값 계약(`pid=-`로 미상 표현) | BLOCKED-1 |
| §B.4 | `start`의 "레코드 없음 + 포트 응답"은 아무것도 죽이지 않고 기동도 않고 안내만. 포트 소유자 탐색 폴백 불채택 | BLOCKED-2 |
| §A.13 | 경로·문자열 필드의 허용 문자 집합(`"`·`\`·`[[:cntrl:]]` 금지), writer·start 동일 검사 | BLOCKED-4 |
| §A.13.1 | `pid`는 2 이상의 10진 정수. 위반 시 새 분기 없이 "해석 불가"로 합류 | B-1 |
| §A.15 | driver manifest 스키마(`minimum_version`·`tested_range`·`ci_pin`) | D6 지적 ⑤ |
| §A.8 | capability probe 저장 경로 `probe.json` 확정 | D6 지적 ⑥ |
| §A.1.2 | `candidates[]` 후보 탐색 기록 10필드 + `selected` 0/1개 불변식 | D6 지적 ⑦ |
| MV-19·38 | 결정론 검증 불가 2건을 실행 가능한 검사로 치환 | D6 지적 ⑧ |
| MV-26 | 검사 대상을 오리진 축으로 한정(`allow_headers=["*"]`는 헤더 축, 범위 밖) | T01 drift #2 |
| MV-41·42 | 신설 [MUST] 불변식의 검증 훅 | D6 지적 ⑤⑦ |

## 품질 게이트 실적

| 게이트 | 결과 |
|---|---|
| D6 Evaluator(설계) | 1회차 `fail`(E.3=3, 백로그 의존 역전) → 10건 반영 → 2회차 `pass`(전 축 ≥4, drift=no) |
| T01 G(명세) | 1회차 `fail` → 재작업 → `pass`. 포트 불일치 거짓 통과 차단 |
| T02 G(명세) | 1회차 `fail`(blocker 3건) → 재작업 → 2회차 `pass`. 재설계 루프 1/2 소진 |
| T02 T4b 보안 | blocker 1건(B-1)·major 3건 적발 → 태스크 내 해소 |
| T02 T4b 컨벤션 | blocker 0 / major 0 / minor 1(advisory) |

구현 전 독립 심판이 **거짓 통과 2건과 프로세스 그룹 전멸 결함 1건**을 실제로 걸렀다. 이 프로젝트가 제거하려는 false positive를 스스로 만들지 않은 근거다.

## 잔여 작업 (백로그 보존)

`backlog.json` 14건 — `done-check all_done: false`, `done_count: 2 / total: 16`.

| ID | 우선순위 | 의존 | 내용 |
|---|---|---|---|
| T16 | P0 | T02 | PID 재사용 방어(부팅 시각 기준 stale 판정) + `.oppl-run/` gitignore |
| T03 | P0 | T01,T02 | Runtime Manager — target 해석·포트 임대·SUT 기동·health·소유 정리, `e2e run` |
| T05 | P0 | T03 | Browser driver·session 계약 + driver manifest + 증적·redaction 관문 |
| T06 | P0 | T03 | 판정 부정 검증 — 증적·assertion 누락 시 pass 불가 집행 |
| T09 | P1 | T03 | API executor |
| T10 | P1 | T03 | Human handoff executor |
| T07 | P1 | T05 | agent-browser 공용 driver |
| T08 | P1 | T05 | cmux driver 이전 |
| T04 | P1 | T03,T10 | `e2e status`·`clean` |
| T11 | P1 | T07,T09 | Hybrid profile + surface fidelity gate |
| T12 | P1 | T08,T10,T11 | SUT HTTP 표면 전수 E2E 스위트(통합) |
| T13 | P2 | T07,T08 | Playwright 소비자 이전(9개 area + 추가 7건) |
| T14 | P2 | T13 | Playwright 기본 설치 제거 + clean install 회귀 |
| T15 | P2 | T04,T06,T12,T14 | 전체 통합 검증 AC-1~AC-14 + 문서 갱신 |

**T16이 안전 관점에서 최우선이다.** 이미 배포 경로에 들어간 코드에 "리부팅 후 첫 설치가 임의 사용자 프로세스를 종료할 수 있는" 경로가 남아 있다. 레코드는 `stop` 실행 시에만 삭제되므로 크래시·리부팅 시 무기한 잔존하고, PID 재할당 시 `app_dir`(레코드 자기 필드)은 당연히 일치하며 `kill -0`도 성공해 종료 분기로 직행한다.

## 미해결 / 이월

| # | 항목 | 상태 |
|---|---|---|
| 1 | 남은 14건의 수행 방식 | 캡틴 재검토 중. Loop 1 산출물(CONTRACT·surfaces.json)은 어느 방식에서도 계약 근거로 재사용 가능 |
| 2 | Q-2·Q-3 (Orca launch-scope 격리, 진단 증적 실행 경로) | E3 실측 의존. 계약은 형태만 확정, 값 미확정 상태로 성립 |
| 3 | Q-6·Q-7 (opt-in driver 유지 기간, 과거 브레인 결정 대체 시점) | E4·E6 이후 |
| 4 | 격리 `OPAL_HOME` 생성 주체 | 범위 밖 선언(PRD §4.2). `--target installed`는 미준비 시 입력 오류로 거부 |
| 5 | conv minor 1건(`local pid` 재선언 명명) | advisory, 미수정 |
| 6 | `docs/` 승격(PRD/TRD/CONTRACT) | 보류. 이 저장소 `docs/`는 프레임워크 레지스트리라 태스크 설계 문서 등재는 캡틴 판단 영역 |

## 프레임워크 개선 기록

| # | 발견 | 기록 위치 |
|---|---|---|
| 1 | `scenario-init`이 `locked: true`를 무시하고 덮어써 RED 동결 게이트 우회 가능(`scenario.py:319`). `scenario-red`만 `scenario_already_locked`로 막고 있어 보호가 한쪽 서브명령에만 걸림 | `~/.opal/fw-inbox/20260913-005826-…-scenario-init이-locked-true를-무시하고-덮어써-RED.md` |
| 2 | `backlog-tool`에 `remove-task`가 없고 `init --force`가 기존 태스크를 보존 — D6 지적 반영 시 파일 삭제 후 재생성으로 우회했다 | 본 문서 |
| 3 | `opal-loop-action-agent`의 비동기 축 호출이 부모 반환과 경쟁 — 태스크당 감시–재개 왕복 10회, 매회 컨텍스트 재적재. 이번 중단의 직접 원인 | 본 문서 |
| 4 | 자식 에이전트가 사용량 한도에 걸리면 `.exitcode`=2, `.err.log`="stream 비정상 종료"로만 남아 **설계 실패와 구분 불가**. 이벤트 스트림을 직접 파싱해야 판별됨 | 본 문서 |

## PM 자기 평가

agentic 대행 중 PM 판단 오류 5건이 발생했고 **전건 워커의 실측 반박으로 교정**됐다. AGENTIC-LOG.md #5·#10·#33·#37·그리고 F-3 잘못된 기술 지시가 그것이다. 원인은 (a) `sed` 범위 출력의 첫 행을 시작 줄번호로 오독, (b) 프로세스 생존을 커맨드 문자열 grep으로 추측, (c) 파일 mtime을 진행 신호로 사용, (d) `pkill -f`가 명령줄 패턴으로 전역 매칭한다는 사실 미확인, (e) 재개 지시 시 watcher 미설치(5시간 16분 방치)다.

교정 규칙을 AGENTIC-LOG #12·#34·#38에 남겼다 — 줄번호는 `grep -n`으로만, 프로세스 판정은 PID + `kill -0`과 `.exitcode` 마커로만, 재개 지시와 watcher는 항상 한 쌍으로.

## 제안서 처리

`docs/proposals/opal-e2e-harness.md`는 **`docs/proposals/`에 `검토` 상태로 유지**한다. 잔여 인용 판정은 0건이나(`/archives/`·`/backup/`·`tasks/` 제외 기준) 구현이 2/9이므로 `적용완료` 아카이브 대상이 아니다. 진행 표기를 2/9로 갱신하고 잔여 백로그 위치를 헤더에 명시했다.

## 커밋

수행하지 않았다. 캡틴 지시를 기다린다.
