# archive — oppl 수행분 (2026-09-12 21:00 ~ 09-13 12:15)

이 폴더는 태스크 127을 **oppl(2-루프 수렴)로 수행한 기록**이다. 2026-09-14에 파일럿을
**opd**로 전환하면서 캡슐을 교체했고, 그 이전 산출물을 여기 보존한다.

**캡슐 루트의 `PRD.md`·`TRD.md`·`CONTRACT.md`·`surfaces.json`은 archive 대상이 아니다** —
잔여 작업의 살아있는 계약이며 opd 태스크가 그대로 승계한다.

## 왜 전환했나

oppl Loop 2는 백로그 항목마다 태스크당 `opal-loop-action-agent`를 1회 디스패치하고,
그 에이전트가 내부 4축(생성자·Evaluator·test-agent·checker)을 **비동기로** 띄운 뒤
부모가 반환하는 구조다. 자식이 끝나면 PM이 `.exitcode`를 감지해 재개시켜야 하므로
**태스크당 감시–재개 왕복이 10회 안팎** 발생하고, 매 왕복마다 컨텍스트가 재적재된다.

T02는 서브에이전트 토큰 328K를 소비했고 실제 산출물은 셸 스크립트 2개 수정과 테스트
1개였다. 한 번은 PM이 watcher를 걸지 않아 **5시간 16분** 방치되기도 했다.

**oppl 자체의 결함이 아니라 범위 단위를 잘못 잡은 것이 원인이다** — oppl이 전제하는
"얇은 수직 슬라이스"와 달리, 이 태스크의 잔여 14건은 `TRD.md` §6이 파일 단위 변경
지점까지 확정해 둔 **이미 설계된 구현 작업**이다. 수렴 루프가 필요한 미결 문제가 아니다.

## oppl 수행 결과

| 항목 | 값 |
|---|---|
| Loop 1 | 완주 — PRD·TRD·CONTRACT·surfaces.json·BACKLOG 확정, D7 캡틴 승인으로 잠김 |
| Loop 2 백로그 | **2/16 완료** (T01 실행 스켈레톤, T02 Console 프로세스 소유권) |
| 충족 AC | **1/14 — AC-3(Console 양방향 비간섭)만.** AC-13은 T01 범위에서만 확인 |
| 산출 코드 | 292행 수정(`console.sh` +239, `install-mac.sh` +24, FE/BE 주소·CORS) + 신설 8파일 |
| 기준선 | `test-tool` 88 passed(baseline 84+4) · 비간섭 회귀 20/20 · vitest 161 passed |
| 소요 | 약 15시간(대기 포함) |

### 태스크별 산출

| 태스크 | 결과 |
|---|---|
| T01 실행 스켈레톤 | 시나리오 8/8, `real-usage` 충족. Playwright MCP가 타 세션 점유(C-2로 종료 불가)라 디스크의 `chrome-headless-shell`을 CDP로 직접 구동해 실증(설치 0건). **G 1회차 fail이 거짓 통과를 차단** — `start_frontend`에 포트 인자가 없어 CORS 주입 origin과 vite 실제 포트가 어긋나면 CDP는 200인데 앱 fetch는 차단되는 상태가 pass로 기록될 수 있었다 |
| T02 Console 소유권 | 시나리오 14/14, 비간섭 회귀 20/20. `pkill` 2지점 제거(MV-21). **보안 검사가 blocker 1건 적발** — `"pid": 0`이 판정표 6분기를 모두 통과해 `kill 0`(호출자 프로세스 그룹 전멸)에 도달했고 `install-mac.sh`가 이 경로를 무인 호출했다. 광역 `pkill`을 지운 자리에 "의도치 않게 광역인 kill"을 남긴 셈. `_console_pid_sane`(pid≥2)로 해소 |

### 계약 보강 (캡슐 루트 `CONTRACT.md`에 반영됨)

구현이 드러낸 공백을 PM 자율 범위(`contract.md` §4 #2)에서 계약에 반영했다 —
§C.10(`kind: "cli"` 표면의 profile 매핑: **호출 수단이 아니라 단언 수단이 결정한다**),
§B.4(`console-*` 출력은 `key=value`, `start`의 "레코드 없음 + 포트 응답" 동작),
§A.13·A.13.1(경로 허용 문자 집합, `pid≥2`), §A.15(driver manifest), §A.8(`probe.json` 경로),
§A.1.2(`candidates[]`), MV-19·26·38·41·42.

## 읽을 때 주의 (함정)

- **`AGENTIC-LOG.md`는 본문이 정확하고 요약표도 갱신돼 있다.** 다만 항목 #5·#10·#33·#37은
  **PM 자신의 오진 기록**이다 — 전건 워커의 실측 반박으로 교정됐고, 교정 규칙은 #12·#34·#38에 있다.
- **`archive/state.oppl.json`의 `current_status: completed_unmerged`를 완료로 읽지 말 것.**
  파이프라인 21행이 전부 ✅이지만 이는 **캡틴 지시에 의한 조기 종료**이고,
  `backlog.json`의 `done-check`는 `all_done: false (2/16)`다. `DONE.md` 상단이 이를 명시한다.
- **`backlog.json`의 T03~T16 14건은 폐기된 목록이 아니다.** opd TASK.md의 Work items 도출
  입력이며, `covers` 필드가 `surfaces.json` 40표면과 1:1로 맞춰져 있다.
- `BACKLOG.md`는 `backlog-tool` 자동 렌더 미러다. opd 전환 후에는 갱신되지 않는다.

## 미해결 안전 결함 (opd 태스크가 승계)

**T16 — PID 재사용 방어.** 이미 브랜치에 들어간 코드에 남아 있다. PID 레코드는 `stop`
실행 시에만 삭제되므로 크래시·OOM·리부팅 시 무기한 잔존하고, 리부팅 후 PID 재할당 시
기록된 pid가 무관한 사용자 프로세스를 가리킨다. 이때 `app_dir`은 레코드 자기 필드라
당연히 일치하고 `kill -0`도 성공해 종료 분기로 직행한다. `install-mac.sh`가 이 경로를
무인 호출하므로 **리부팅 후 첫 설치가 임의 사용자 프로세스를 종료할 수 있다.**

저비용 해법: `started_at`이 시스템 부팅 시각보다 이르면 무조건 stale 판정. `started_at`은
이미 `CONTRACT.md` §A.13 필수 필드로 기록된다. (**ANALYSIS 정정**: `console.sh:304`의 `status` 분기에서
읽히긴 하나 안전성 검사·표시에만 쓰이고 `stop` 판정표는 이 필드를 전혀 파싱하지 않는다 — 즉
"기록만 되고 읽히지 않는다"가 아니라 "읽히되 stale 판정에 미사용"이 정확하다.)

## 프레임워크 개선 기록

| # | 발견 | 기록 |
|---|---|---|
| 1 | `scenario-init`이 `locked: true`를 무시하고 덮어써 RED 동결 게이트 우회 가능(`scenario.py:319`). `scenario-red`만 `scenario_already_locked`로 막고 있어 보호가 한쪽 서브명령에만 걸림 | `~/.opal/fw-inbox/20260913-005826-…-scenario-init이-locked-true를-무시하고-덮어써-RED.md` |
| 2 | `backlog-tool`에 `remove-task`가 없고 `init --force`가 기존 태스크를 보존 — 백로그 재구성 시 파일 삭제 후 재생성으로 우회 | 이 문서 |
| 3 | `opal-loop-action-agent`의 비동기 축 호출이 부모 반환과 경쟁 — 태스크당 감시–재개 왕복 10회 | 이 문서 (전환 직접 원인) |
| 4 | 자식 에이전트가 사용량 한도에 걸리면 `.exitcode`=2, `.err.log`="stream 비정상 종료"로만 남아 **설계 실패와 구분 불가**. 이벤트 스트림의 `rate_limit_event`를 직접 파싱해야 판별됨 | 이 문서 |
