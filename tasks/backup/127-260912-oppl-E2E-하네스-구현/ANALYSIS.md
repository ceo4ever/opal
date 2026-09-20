---
template: sdlc-v2
---
# ANALYSIS: OPAL 범용 E2E 하네스 구현 (제안서 태스크 3~9)

> 입력: [TASK.md](TASK.md) | 조사 기준: worktree `task_127`(브랜치 `feat/OP-TASK-127`), 확인 시점 2026-09-14. `test-tool` baseline `~/.opal/.venv/bin/python -m pytest` 재실행 결과 88 passed(TASK.md C-9 기준선과 일치).

## Findings

| 질문 | 확인한 사실 | 근거 | 설계에 미치는 영향 |
|---|---|---|---|
| Q1 T01 골격 경계 | `lib/e2e/`에는 `__init__.py`·`ports.py`·`process.py`·`runtime.py` 4파일만 존재. `target.py`·`orchestrator.py`는 미신설. `ports.py`는 `find_free_port(host)` 단일 함수뿐이며 lock/lease/stale 흔적 0건. `process.py`는 `spawn_process_group`·`pid_alive`·`process_group_members`·`terminate_process_group`(플랫폼 분기 유일 지점)을 이미 보유. `runtime.py`는 `start_backend`·`start_frontend`·`wait_healthy`·`stop_all`을 보유하나 포트 인자는 호출자가 넘긴 값을 그대로 씀(자체 임대 없음) | `opal/tools/test-tool/lib/e2e/ports.py:18`(`find_free_port` 유일 def), `process.py:31-185`(전체 def 목록), `runtime.py:41-241`(전체 def 목록) | T03은 `target.py`·`orchestrator.py` 신설과 `ports.py`에 allocator lock·lease record·stale 회수 **추가**(치환 아님)로 범위가 정확히 TRD §6.2와 일치. `process.py`/`runtime.py`는 재사용 대상이지 변경 대상이 아니다 — PLAN Work item에 "T01 산출물 수정"을 넣지 않는다 |
| Q2 e2e_adapter 계약 보존 지점 | mode A 주석이 `e2e_adapter.py:21`("mode A — --surface 미전달(신규 surface 강제), B/C 재사용 금지")에 실재. `build_verdict` 호출은 217행에서 시작, `"assertion_results": []`는 222행 — TRD가 지목한 217-225와 일치하며 이 호출은 구조적으로 `pass`를 낼 assertion 근거가 없다. cmux 에러 어휘는 `FALLBACK_CODES` 상수로 정규화되며 `~/.opal/tools/cmux-tool`이 실제로 내는 `not_in_cmux`/`cmux_not_installed`와 이름이 일치(cmux-tool `lib/dispatch.sh:46,54`) | `e2e_adapter.py:1-40`(header·mode A 주석), `:217-222`(`build_verdict` 호출부), `~/.opal/tools/cmux-tool/lib/dispatch.sh:46,54` | TRD §2.2 주장은 현재도 유효. T06(cmux driver 이전)에서 이관 시 mode A 주석·`FALLBACK_CODES` 이름 그대로 보존해야 cmux-tool 쪽 변경 없이 계약이 성립한다 |
| Q3 Playwright 인벤토리 재확인 | 9개 area 중 실측 가능한 지점 전건 존재 확인. `test_tool.py:56,221`에 "playwright" 문구 실재(TRD 인용과 정확히 일치). `resolver.py`의 playwright 후보 블록은 두 곳(TRD "106-112/156-162"와 근접 — 실측 108-113·158-163)에 실재. `test-tools-schema.yaml:140,220`, `templates/test-tools.yaml:130` 일치. `tool-scan/tests/test_tool_scan.py:843-880`에 "playwright 폴백" 문구를 정규식(`playwright.*fallback\|fallback.*playwright\|playwright.*폴백\|폴백.*playwright`)으로 강제하는 assert 실재(TS-040) — 이 테스트를 먼저 갱신하지 않으면 RED가 된다는 TRD 경고가 유효 | `test_tool.py:56,221`, `resolver.py:107-119,157-169`(grep -n 실측), `test-tools-schema.yaml:140,220`, `opal/templates/test-tools.yaml:130`, `tool-scan/tests/test_tool_scan.py:843,860,873-880` | T13(9 area + A-1~A-7) 분해가 그대로 유효. A-2(강제 테스트 선-갱신)는 작업 순서 제약으로 PLAN에 명시 필요 |
| Q4 Playwright 설치·진단 실측 | `opal/tools/requirements.txt:28-29`에 `playwright>=1.40.0` 기본 의존성 실재. `scripts/install-mac.sh`에 Chromium 자동 설치(1704-1736행대, TRD "1700-1732"와 근접) 및 실행권한 부여(1293-1297행대)·MCP cache 디렉토리 생성(2025-2026행대) 실재. `windows.ps1:1031-1045`에 Chromium 안내 로직 실재. `doctor/lib/checks.sh:179-183,293`에 playwright를 "옵션" 의존성 및 공식 MCP 4종 분모(`context7,playwright,shadcn,sequential-thinking`)에 포함하는 로직 실재 | `requirements.txt:28-29`, `install-mac.sh:1293-1297,1704-1736,2025-2026`, `windows.ps1:1031-1045`, `doctor/lib/checks.sh:179-183,268,293` | T14(기본 설치 제거)가 건드릴 지점 확정. AC-12 회귀 판정 대상은 `doctor` 의존성 카운트·MCP 등록 목록·`web-to-markdown` 폴백 경로 3곳이며, 전부 "옵션 취급으로 전환"이지 "완전 삭제"가 아니므로 `doctor` 출력 문구 변경이 AC-12 회귀 검증의 실제 관측 대상이다 |
| Q5 agent-browser·Orca·cmux 로컬 가용성(읽기 전용) | `/Applications/Orca.app/Contents/Resources/agent-browser-darwin-arm64` 존재, 실행 시 `agent-browser 0.27.0` 출력(버전 조회만 수행, 브라우저·프로필 미기동). PATH에 독립 `agent-browser`·`cmux` 바이너리는 없음(`which` 둘 다 not found). `~/.opal/tools/cmux-tool/lib/dispatch.sh:46,54`가 `not_in_cmux`/`cmux_not_installed` JSON 에러를 발행하는 코드로 실재 확인 | 명령 실행 결과(버전 조회, `which agent-browser`/`which cmux` 실패), `~/.opal/tools/cmux-tool/lib/dispatch.sh:46,54` | 현재 로컬 환경은 cmux 부재 → `provider_unavailable` 전환 경로(AC-5)가 실제로 타는 환경이다. Orca 내장 agent-browser 바이너리명이 플랫폼 접미사(`agent-browser-darwin-arm64`)를 갖는 점은 T05/T07 driver가 바이너리 경로를 하드코딩하지 않고 Orca 설치 위치에서 해석해야 함을 의미(플랫폼 분기는 어댑터 계층 원칙과 일치). Q-2·Q-3(agent-browser launch-scope·증적 수집 가능 여부)은 여전히 미확인 — probe 실측이 필요하며 이는 실행 단계(E3) 소관으로 착수 판단을 바꾸지 않는다(TASK.md Open questions와 일치) |
| Q6 console.sh AC-15 구현 지점 | `stop` 판정표(220-277행)는 판정 #1(레코드 없음)·#2(파싱 실패/`_console_pid_sane` 실패)·#3(`app_dir` 불일치)·#4(`kill -0` 실패=stale)·#5/#6(생존=SIGTERM+폴링) 6분기이며 **`started_at`을 전혀 읽지 않는다**(234-236행 로컬 변수에 `rec_pid`·`rec_app_dir`만 선언). `started_at`은 오직 `status` 표시 분기(298-316행)에서 `console_read_pid_field`로 읽혀 `_console_pid_value_unsafe` 안전성 검사(313행)에만 쓰이고 부팅 시각과 비교되지 않는다 — archive/README.md의 "기록만 되고 어디서도 읽히지 않는다"는 표현은 정확히는 "읽히지만 stale 판정에는 미사용"으로 정정 필요 | `console.sh:220-277`(stop 판정표 전체), `:234-236`(rec_pid/rec_app_dir만 선언), `:298-316`(status 분기의 `rec_started_at` 읽기·안전성 검사만) | AC-15 구현 지점은 `stop` 판정표의 판정 #3(identity 일치, 251행)과 #4(`kill -0`, 253행) 사이다 — `rec_started_at`을 `stop` 분기에도 파싱하고 시스템 부팅 시각(macOS `sysctl -n kern.boottime` 파싱 / Linux `/proc/stat`의 `btime` 또는 `uptime -s`)과 비교해 이전이면 무조건 stale 처리한다. ISO8601 문자열 파싱이 macOS(`date -j -f`)와 Linux(`date -d`)에서 다르므로 **이 비교 로직이 유일한 신규 플랫폼 분기 지점**이다. `console.sh`는 이미 `open`에서 `command -v open/xdg-open` 분기를 갖고 있어 같은 파일 내 인라인 분기 선례가 있다 |
| Q7 backlog.json 승계 가능성 | T03~T16 전 항목이 `depends_on: None`(명시적 의존 그래프 없음, 순서는 TASK.md C-4의 제안서 §14 순서로만 암묵 고정). `covers`의 합집합이 `surfaces.json` 40개 표면 id와 정확히 1:1(양방향 차집합 0) — 승계 가능. T04(`covers: e2e-status, e2e-clean`)와 T10(`covers: human-executor-handoff, human-executor-resume, e2e-resume`)은 둘 다 `test_tool.py`의 `e2e` 서브파서를 확장하는데, 현재 `test_tool.py`에는 `resolve/check/unit/integration` 4개 서브파서만 있고 `e2e` 서브파서 자체가 아직 없다(T03이 최초 신설) — 따라서 충돌은 "동시 수정"이 아니라 "T03→{T04, T10} 순차 확장"이며 T04·T10 사이에도 같은 파일을 건드리므로 두 태스크를 서로 순차 배치해야 병합 충돌이 없다 | `archive/backlog.json`(전 태스크 `depends_on` 필드 null), `surfaces.json`↔`backlog.json` covers 교집합/차집합 스크립트 검증(양쪽 0), `test_tool.py:204-221`(현재 서브파서 4개, `e2e` 없음) | PLAN Work items는 backlog.json T03~T16을 그대로 항목 단위로 승계하되, 의존 그래프를 `depends_on: null` 그대로 두지 말고 최소한 "T03 선행" + "T04/T10 상호 순차"를 PLAN이 명시적으로 추가해야 한다. 이는 재분해가 아니라 순서 필드 보강이다 |

## Change boundary

| 경로·인터페이스 | 역할 | 변경 영향 |
|---|---|---|
| `opal/tools/test-tool/lib/e2e/target.py`, `orchestrator.py`(신설), `ports.py`(확장) | Runtime Manager(T03) | 신규 파일 추가 + 기존 `find_free_port` 곁에 lock/lease 함수 추가. `process.py`·`runtime.py`는 소비만(변경 없음) |
| `opal/tools/test-tool/test_tool.py` | `e2e` 서브파서·`ERROR_CODES` | T03이 최초 신설, T04·T08·T10이 순차 확장 — 병합 순서가 회귀 경계다. 기존 4개 서브파서(`resolve/check/unit/integration`) 무변경 유지 필요 |
| `opal/tools/test-tool/lib/e2e_adapter.py:129-231` | cmux 실행 경로 | T08(driver 이전) 시 mode A 주석(21행)·`FALLBACK_CODES` 어휘·`build_verdict` 호출 계약 보존, 로직만 `drivers/cmux.py`로 이관 |
| `opal/tools/test-tool/lib/e2e_contract.py`, `lib/scenario.py` | 판정·시나리오 SSOT | C-1에 의해 **변경 0** — 본 분석에서도 두 파일에 대한 수정 근거 발견 없음(소비 지점만 존재) |
| `opal/tools/opal-cli/lib/console.sh:220-277`(stop), `:298-316`(status) | PID 소유권 판정 | AC-15 삽입 지점은 stop 판정표 #3↔#4 사이 1곳. status 분기는 이미 `started_at` 표시만 하므로 변경 불요 |
| `opal/tools/requirements.txt`, `scripts/install-mac.sh`, `scripts/install/windows.ps1`, `opal/tools/doctor/lib/checks.sh` | Playwright 기본 설치·진단 | 완전 삭제가 아니라 옵션/opt-in 전환 — `doctor` 의존성 카운트·MCP 목록 문구가 AC-12 회귀 관측점 |
| `opal/tools/tool-scan/tests/test_tool_scan.py:843-880` | 회귀 테스트 | T13 착수 전 **선-갱신 필수**(현재 문구 강제 상태로는 T13 나머지 변경이 RED를 유발) |

## Critical assumptions

| 가정 | 확인 방법·결과 | 남은 한계 |
|---|---|---|
| `test-tool` baseline은 88 passed다(C-9) | `~/.opal/.venv/bin/python -m pytest -q` 재실행 — "88 passed, 100 subtests passed" 확인 | 없음 — 실측 완료 |
| cmux/agent-browser 로컬 미설치 상태가 CI·타 개발자 환경과 동일하지 않을 수 있다 | 이 worktree에서 `which cmux`/`which agent-browser` 실패, Orca.app 내장 바이너리만 버전 조회로 확인 | driver 구현은 "가용성 불명" 전제로 설계해야 하며, PLAN이 CI 환경의 cmux/agent-browser 가용성을 별도로 확정하지 않는 한 T07·T08 테스트는 mock 경계에 의존한다 |
| agent-browser의 `--config`·`--allowed-domains`·`console`/`errors`/`network_har` 증적 수집 가능 여부(Q-2, Q-3) | 미실행(브라우저 실행·프로필 접근은 워커 capability 밖, C-2가 사용자 자원 보호를 요구) | TASK.md Open questions와 동일 — 착수 차단 아님, E3 단계 비파괴 probe로 해소 예정(CONTRACT.md §A.8 `probed=false`→`available=false` 보수적 처리로 이미 설계에 반영됨) |
| `console.sh`에 boot-time 비교 분기를 추가해도 CONVENTIONS §플랫폼 분기 격리 위반이 아니다 | `console.sh` `open` 분기(`command -v open/xdg-open`)가 이미 같은 파일 내 플랫폼 분기 선례로 존재함을 확인 | 최종 판단(같은 파일 내 인라인 분기 vs 별도 어댑터 함수로 추출)은 PLAN이 결정 |

## Handoff

- PLAN에서 결정할 것: backlog.json T03~T16을 Work item으로 승계하되 (1) T03을 모든 후속(T04~T16)의 선행으로 명시, (2) T04·T10을 상호 순차 배치(같은 `test_tool.py` `e2e` 서브파서 영역), (3) T13 착수 전 `test_tool_scan.py:843-880` 선-갱신을 별도 순서 제약으로 명시, (4) AC-15 구현을 `console.sh` 인라인 boot-time 비교로 할지 별도 헬퍼 함수로 추출할지 확정.
- 착수 차단: 없음.
