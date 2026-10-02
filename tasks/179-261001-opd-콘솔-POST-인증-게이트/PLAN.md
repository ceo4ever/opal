---
template: sdlc-v2
---
# PLAN: OPAL Console 상태 변경 API 인증 게이트와 구형 Brain 실행 차단 (Gateway 제안 Phase 0)

> 입력: [TASK.md](TASK.md) | 작성자: PM (ANALYSIS 별도 산출물 없음 — PM 경로, 분석은 아래 Findings에 포함)

## Approach

Console backend 앞단에 **단일 ASGI 인증 미들웨어**를 세우고(Host → Origin → 세션 → CSRF 순 검사), 같은 지점에서 WebSocket handshake도 막는다. 세션은 `opal-cli console open`이 사용자 전용 런타임 디렉터리에 떨어뜨린 1회성 진입 token을 브라우저가 교환해 얻는다. 구형 `claude -p` Brain은 **서버 측 정책 객체 하나**(`legacy_brain_enabled`, 기본 꺼짐)가 결정하며, 이 정책은 HTTP 라우터가 아니라 Registry 진입점과 `claude` 프로세스 spawn 직전에서 집행한다. 프론트엔드는 잠금 화면·교환 부트스트랩·Brain 첫 진입 안내·구형 토글을 얹고, E2E 하네스는 같은 교환 계약으로 격리 SUT에 인증된 상태를 만든다.

실행 순서는 RED 테스트(W-8) → 구현 3갈래 병렬(BE 정책·BE 인증 코어·FE) → 배선·CLI → E2E 접합·문서다. 새 기능은 Phase 1 이후(Gateway·Account·Profile·새 Brain transport)를 건드리지 않는다.

code-scan 조회 결과(`code-scan scan`·`depends`, scope console-be, headerSource inline)로 확인한 변경 경계:

| 모듈 | domain / layer | exports | 소비자(`depends` 역조회) | 이번 변경의 의미 |
|---|---|---|---|---|
| `adapters.opbr_adapter` | console / service | `prime_and_ask`, `extract_json_fence` | `brain_session.py`, `routers/brain.py`, `test_brain.py`, `test_brain_spike.py` | 최종 spawn 단일 지점 — 정책 게이트의 마지막 방어선 |
| `adapters.brain_session` | console / service | `ConversationBrainSession`, `BrainSessionRegistry`, `brain_session_registry` | `main.py`, `routers/brain.py`, `routers/config.py`, `test_brain.py`, `test_routers.py` | Registry 진입점(prime·prewarm·submit·ask·리필) 게이트 |
| `config` | console / config | `load_config`, `ConsoleConfig`, `save_config` 외 | 라우터 6종, `scanner.py`, 테스트 4종 | 추가 함수만 도입, 기존 시그니처 불변 |
| `main` | console / router | `app` | `test_brain.py`(lifespan), `test_main.py`, `test_routers.py` | 미들웨어·CORS·lifespan 선프라임 게이트 배선 |

신규·변경하는 모든 코드 파일의 `@header`는 `harness/header-rules.md`의 현재 사실 규칙을 따른다(description은 이번 변경 후 사실만, 수기 이력 절 금지).

## Findings

### 직접 변경

- 구형 Brain 정책·spawn 게이트: `dashboard/backend/adapters/brain_policy.py`(신규), `dashboard/backend/adapters/opbr_adapter.py`, `dashboard/backend/adapters/brain_session.py`, `dashboard/backend/config.py`
- 인증 코어: `dashboard/backend/auth.py`(신규), `dashboard/backend/entry_token.py`(신규), `dashboard/backend/routers/auth.py`(신규)
- 앱 배선: `dashboard/backend/main.py`, `dashboard/backend/routers/brain.py`, `dashboard/backend/models.py`
- FE: `dashboard/frontend/index.html`, `dashboard/frontend/src/lib/api.ts`, `dashboard/frontend/src/lib/auth.ts`(신규), `dashboard/frontend/src/App.tsx`, `dashboard/frontend/src/components/auth/LockScreen.tsx`(신규), `dashboard/frontend/src/pages/brain/BrainLegacyGate.tsx`(신규), `dashboard/frontend/src/pages/brain/BrainPage.tsx`, `dashboard/frontend/src/pages/settings/SettingsPage.tsx`
- CLI: `opal/tools/opal-cli/lib/console.sh`
- E2E 하네스: `opal/tools/test-tool/lib/e2e/environment.py`, `opal/tools/test-tool/lib/e2e/orchestrator.py`, `opal/tools/test-tool/lib/e2e/executors/api.py`, `opal/tools/test-tool/lib/e2e/redaction.py`, 그리고 프로젝트 E2E 환경 선언과 세션 스크립트(프로젝트 루트의 .opal/e2e 아래 environment.json, console_session.py(신규) — 선행 점 경로는 계약 검사기가 정규화하므로 이 절에서는 백틱 없이 쓴다)
- 테스트(RED 작성 포함, 기존 테스트의 새 계약 갱신 포함): W-8 변경 대상 전체

### 회귀 확인

- 읽기 라우터 6종은 코드 변경 없이 미들웨어의 default-deny로 보호된다: `dashboard/backend/routers/dashboard.py`, `dashboard/backend/routers/projects.py`, `dashboard/backend/routers/tasks.py`, `dashboard/backend/routers/memory.py`, `dashboard/backend/routers/doctor.py`, `dashboard/backend/routers/docs_skills.py`. 세션 없이 호출하면 데이터 없이 거절되고 세션이 있으면 기존 응답이 그대로여야 한다.
- 설정 쓰기 라우터 `dashboard/backend/routers/config.py`는 변경하지 않는다. 미들웨어가 쓰기 전에 거절하고, 구형 Brain 정책이 꺼져 있으면 Registry 게이트가 `prewarm`을 무동작으로 만든다.
- 기존 설정 로딩 테스트 `dashboard/backend/tests/test_config.py`는 수정 없이 통과해야 한다(설정 로더 모듈은 추가 함수만 갖는다).
- CLI 소유권·스캔 회귀 `scripts/tests/test_console_ownership.sh`, `scripts/tests/test_console_scan.sh`는 `open` 외 서브커맨드가 불변임을 확인한다.
- E2E 임대 포트 풀이 사용자 Console 포트를 계속 제외하는지: `opal/tools/test-tool/lib/e2e/ports.py`. 고정 표면 분모 `opal/tools/test-tool/tests/fixtures/e2e-harness/surfaces.json`은 동결 spec이라 수정하지 않는다.
- 데스크톱 셸 `dashboard/frontend/electron/main.cjs`는 이번 범위의 인증 대상이 아니다. 기존과 같은 로딩 경로가 유지되는지만 본다.

### 문서 갱신

- `docs/ARCHITECTURE.md`: Console 절의 "읽기 전용" 표기, 브레인 라우터 엔드포인트 표, 설정 화면 표, CLI `open` 설명을 인증 게이트·진입 계약·구형 Brain 기본 꺼짐에 맞춘다.
- `docs/PROJECT.md`: OPAL Console 컴포넌트 표의 BE·CLI 설명.
- `docs/SECURITY.md`: Console 로컬 인증 경계 절 신설(위협 모델, 보호 범위, GET 점검 결과, 구형 Brain 위험 3종).
- `README.md`: Console 소개 문단의 직접 URL 안내를 `opal-cli console open` 진입으로 바꾼다.
- `opal/tools/opal-cli/README.md`: `console open` 동작 계약.
- `opal/tools/test-tool/README.md`: 환경 선언의 세션 부트스트랩 키.

### 미확인 가정

H-1, H-2, H-3, H-4, H-5 (Risks 참조).

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| D-1. 인증 경계는 ASGI 미들웨어 1개 | `dashboard/backend/auth.py`의 순수 ASGI 미들웨어가 `http`·`websocket` scope를 라우팅 전에 검사한다. 순서는 ① Host ② `/api/` 경로의 Origin ③ 세션 ④ 상태 변경 메서드의 CSRF. 라우터 핸들러는 요청 본문을 읽기 전에 거절된다. `GET`·`HEAD`·`OPTIONS`는 안전 메서드로 CSRF는 요구하지 않지만 세션은 요구한다(CORS preflight는 바깥쪽 CORS 미들웨어가 먼저 응답한다, D-8). | AC-1 "작업 전 거절". 라우터별 Depends는 새 라우터가 추가될 때 누락될 수 있어 default-deny 한 지점이 낫다. 근거: 제안서 §6.2 |
| D-2. default-deny 범위 | `/api/` 하위는 전부 세션 필수. 예외 2종만: `POST /api/auth/exchange`, `GET /api/auth/session`. `/health`와 SPA 정적 자산·`index.html`은 세션 불요(잠금 화면이 로드돼야 함). Host 검사는 모든 경로에 적용한다. | AC-5. 기존 GET 중 프로젝트·설정·태스크·문서를 반환하는 경로를 개별 판정하지 않고 전부 세션 뒤에 둔다. 이것이 Phase 0 제3항의 점검 결과이며 `docs/SECURITY.md`에 기록한다. |
| D-3. Host 허용 | 호스트명이 `127.0.0.1`·`localhost`·`[::1]` 중 하나이거나 환경 변수 `OPAL_CONSOLE_ALLOWED_HOSTS`(쉼표 구분 호스트명, `^[A-Za-z0-9.\-\[\]:]+$` 형식만, 무효 항목은 경고 후 제외)에 있어야 한다. 포트는 비교하지 않는다. 위반은 403 `host_not_allowed`. | DNS rebinding 방어는 호스트명 판정이 핵심이고 포트는 무관. 제안서 §6.2 "loopback 주소와 명시된 Console 호스트" |
| D-4. Origin 허용 | `/api/` 요청에 `Origin`이 있으면 `요청 Host 기준 동일 출처(http://<Host>)` 또는 `CORS_ORIGINS`(기존 개발 2종 + `OPAL_CONSOLE_CORS_ORIGINS`) 중 하나와 문자열 일치해야 한다. 상태 변경 메서드(POST·PUT·PATCH·DELETE)와 WebSocket handshake는 `Origin`이 **없어도** 거절한다(403 `origin_required`). 불일치는 403 `origin_not_allowed`. | 브라우저는 상태 변경 요청에 항상 Origin을 싣는다. 비브라우저 클라이언트(E2E API executor 포함)는 `Origin`을 명시해야 한다. |
| D-5. 세션 | 쿠키 `opal_console_session`: `HttpOnly; SameSite=Strict; Path=/; Max-Age=43200`(12시간 절대 만료). 값은 `secrets.token_urlsafe(32)`, 서버는 SHA-256 해시를 키로 인메모리 저장(프로세스 재시작 시 모든 세션 소멸 → 잠금 화면). `Secure`는 붙이지 않는다(loopback http). 세션 없음·만료는 401 `auth_required`. | C-2: 값을 URL·로그에 남기지 않는다. 재시작 시 소멸은 단순성·안전성 우선 |
| D-6. CSRF | 세션마다 `csrf_token`(`secrets.token_urlsafe(32)`)을 발급한다. 상태 변경 메서드는 헤더 `X-CSRF-Token`이 세션의 값과 `secrets.compare_digest`로 일치해야 한다(불일치 403 `csrf_invalid`). 값은 교환 응답 본문과 `GET /api/auth/session` 응답에만 나온다. | 쿠키(SameSite=Strict)만으로 막지 않고 Origin·CSRF를 독립 방어선으로 둔다. 커스텀 헤더는 교차 출처 단순 요청을 preflight로 몰아낸다. |
| D-7. WebSocket guard | 같은 미들웨어가 `websocket` scope에서 Host·Origin(필수)·세션을 검사하고 실패하면 accept 전에 `websocket.close` code 1008을 보낸다. 현재 WS 라우트는 없고, 새 WS 라우트는 이 guard를 자동으로 받는다. | AC-1은 "추가되는 API와 WebSocket handshake"를 요구한다. |
| D-8. CORS | `allow_credentials=True`로 바꾸되 `allow_origins`는 기존 정확 일치 목록 그대로(와일드카드 금지)다. `allow_headers`는 `Content-Type`, `X-CSRF-Token` 두 값으로 고정하고 메서드는 기존 `GET`·`POST`를 유지한다. 미들웨어 등록 순서는 CORS가 바깥(preflight를 세션 없이 처리), 인증이 안쪽이다. | 개발 모드 FE(5173)→백엔드(7823) 교차 포트에서 쿠키·CSRF 헤더가 전달돼야 한다. SameSite는 포트를 구분하지 않는다. 기존 D-6 단언(`allow_credentials is False`)은 W-8이 새 계약으로 갱신한다. |
| D-9. 진입 token 채널 | `dashboard/backend/entry_token.py`(표준 라이브러리만 사용)가 발급·소비를 소유한다. 디렉터리 `<OPAL_HOME>/run/console-entry/`(`OPAL_HOME` 환경 변수 없으면 `~/.opal`)를 `0700`으로 만들고, 소유자 uid·권한(그룹/타인 비트 없음)·symlink 여부를 확인하지 못하면 발급·소비를 거부한다. 발급은 `secrets.token_urlsafe(32)` token의 SHA-256 16진 이름 파일을 `O_CREAT\|O_EXCL`, `0600`으로 쓰며 내용은 `{"expires_at": <epoch초>}`(기본 TTL 60초, 상한 300초). 소비는 파일을 고유 이름으로 `os.rename`해 원자적으로 1회만 성공시키고 만료·상한 초과·부재·위조를 구별하지 않는 `False`로 돌려준다. 발급 때 만료 파일을 청소한다. CLI: `python -m dashboard.backend.entry_token issue [--ttl N]`는 stdout에 token만 출력한다. | "사용자 전용 0600 런타임 채널"(제안서 §6.2). 파일 방식은 서버 협조 없이 CLI·하네스가 같은 계약으로 발급하고 데몬 재시작과 무관하다. token 원문은 디스크에 남지 않고 해시만 남는다. |
| D-10. 교환 API | `POST /api/auth/exchange` 본문 `{"token": "<진입 token>"}`. 성공 200 `{"authenticated": true, "csrf_token": "<값>"}` + `Set-Cookie`. 실패는 사유를 구별하지 않고 401 `entry_token_invalid`. Origin 필수(D-4)이고 세션·CSRF는 요구하지 않는다. `GET /api/auth/session`은 항상 200 `{"authenticated": false}` 또는 `{"authenticated": true, "csrf_token": "<값>"}`이며 프로젝트·설정·계정 정보를 싣지 않는다. 오류 본문은 `{"error": {"code", "message"}}` 형식이다. | 기존 FE `api.ts`가 이 envelope를 이미 해석한다. |
| D-11. `/health` | 응답에 필드 `auth: "required"`를 추가한다(`{"status","version","auth"}`). 프로젝트·설정·계정 정보는 싣지 않는다. | `console open`이 인증 게이트가 없는 구버전 데몬을 식별하는 근거(H-4). AC-5의 "데몬 상태만"을 넘지 않는다. |
| D-12. `opal-cli console open` | health 확인·기동·재확인(기존 순서 유지) 뒤 ① `/health`에 `auth` 필드가 없으면 구버전으로 판단해 경고·재기동 안내만 출력하고 브라우저를 열지 않으며 실패(return 1) ② 있으면 `PYTHONPATH=<dashboard-server>` + `<OPAL_HOME>/.venv/bin/python`(없으면 `python3`)로 `python -m dashboard.backend.entry_token issue`를 실행해 token을 받고 ③ `http://127.0.0.1:7823/#entry=<token>`을 브라우저 열기 명령에 전달한다. 출력에는 token과 fragment를 쓰지 않고 기본 URL만 쓴다. 발급 실패(venv python과 `python3`가 모두 없는 경우 포함) 시 오류를 출력하고 브라우저를 열지 않으며 비0으로 끝낸다. | AC-2. token은 fragment에만 있어 초기 HTTP 요청·서버 로그·Referrer에 실리지 않는다. |
| D-13. FE 인증 부트스트랩 | `src/lib/auth.ts`가 모듈 단일 Promise로 진입을 한 번만 수행한다(StrictMode 이중 effect 방어). `location.hash`가 `#entry=<token>`이면 **교환 요청을 보내기 전에** `history.replaceState`로 fragment를 제거하고 교환하며, 아니면 `GET /api/auth/session`을 호출한다. 결과가 `authenticated`면 `csrf_token`을 메모리에만 보관한다(storage 금지). `apiClient`는 모든 요청에 `credentials: "include"`를 싣고 GET·HEAD가 아니면 `X-CSRF-Token`을 싣는다. 401 `auth_required` 응답은 인증 상태를 `locked`로 바꾼다. `index.html`에 `<meta name="referrer" content="no-referrer">`. | AC-2, C-2 |
| D-14. 잠금 화면 | `LockScreen`은 API 호출 없이 정적 안내만 보인다: 세션이 없다는 사실과 "터미널에서 `opal-cli console open`을 실행해 다시 여세요", 상태 재확인 버튼 1개. 프로젝트·설정·계정 정보를 렌더링하지 않는다. `App`은 인증 상태가 `authed`일 때만 라우터를 마운트한다. | AC-2 |
| D-15. 구형 Brain 정책 객체 | `adapters/brain_policy.py`의 프로세스 단일 정책이 `legacy_brain_enabled`를 소유한다. 저장 위치는 `console.config.json`의 `legacy_brain_enabled` 키이며 값이 JSON `true`일 때만 켜짐으로 해석한다(키 없음·비불리언·파손은 꺼짐). `prewarm_projects`·업그레이드는 이 값에 영향을 주지 않는다. 값은 프로세스 시작(lifespan)과 첫 사용 때 읽고 이후 변경은 `set_enabled`만 한다. | C-3, AC-3 |
| D-16. spawn 직렬화 | 정책은 하나의 `threading.Lock`으로 ⓐ `set_enabled`와 ⓑ 최종 launch 허가+프로세스 시작을 직렬화한다. `opbr_adapter.prime_and_ask`는 `subprocess.run` 대신 `with policy.spawn_guard(): proc = subprocess.Popen(...)`로 시작한 뒤 `proc.communicate(timeout=...)`을 **락 밖에서** 기다린다(타임아웃은 `kill` 후 기존과 같은 `RuntimeError`). `spawn_guard`는 꺼져 있으면 `LegacyBrainDisabled`(`RuntimeError` 하위)를 던지고, 켜져 있으면 `Popen` 성공 직후 `running_turns`를 1 올리며 turn이 끝나면(`finally`) 내린다. `set_enabled(False)`가 반환된 뒤에는 어떤 경로도 새 프로세스를 시작할 수 없고, 이미 시작된 turn은 끝까지 진행한다. 기존 호출 계약(`shell=False`, `cwd=project_path`, `--allowedTools`, JSON 파싱, 오류 의미)은 보존한다. | AC-3 "끄는 요청이 완료된 뒤 새 프로세스 0회". 락을 `subprocess.run` 전체 구간(최대 180초)에 걸면 끄기 요청이 막히므로 시작 구간만 직렬화한다. |
| D-17. Registry 게이트 | 꺼짐이면 `BrainSessionRegistry.prime`·`ask`·`submit_job`은 `LegacyBrainDisabled`를 던지고, `prewarm`은 로그만 남기고 반환하며, `checkout_warm_handle`은 풀을 비운 뒤 리필을 만들지 않는다. 풀 리필 스레드 `_prime_into_pool`은 시작할 때 정책을 재확인해 꺼짐이면 spawn 없이 종료하되 `_pool_inflight`는 정상 감소시킨다. 어댑터 `spawn_guard`가 마지막 방어선이다(D-16). | 제안서 §8: 게이트는 HTTP 라우터가 아니라 subprocess 실행 경계의 공통 정책 |
| D-18. 구형 Brain API | `GET /api/brain/legacy` → `{"enabled": bool, "running_turns": int}`. `POST /api/brain/legacy` 본문 `{"enabled": bool, "risk_acknowledged": bool}`: 켜기는 `risk_acknowledged`가 JSON `true`가 아니면 400 `risk_not_acknowledged`, 켤 때는 저장 성공 후 메모리에 반영, 끌 때는 메모리 반영 후 저장(저장 실패 시 500이지만 메모리는 꺼진 채 유지)하고 풀 핸들을 폐기한다. 응답은 같은 모양. 꺼진 상태의 `POST /api/brain/prime`·`/api/brain/query`는 라우터가 먼저 403 `legacy_brain_disabled`(envelope)로 답하고, `LegacyBrainDisabled` 경합 예외도 같은 403으로 매핑한다. `GET /api/brain/auth|status|job`은 기존 계약 유지. | AC-3, AC-4 |
| D-19. Brain 첫 진입 화면 | `BrainPage`는 `BrainLegacyGate`로 감싼다. 꺼짐이면 대화 UI와 prime·status 폴링을 마운트하지 않고 다음을 함께 보인다: 새 Brain 출시 전까지 Brain은 기본적으로 사용할 수 없다는 사실, 업그레이드로 기본 꺼짐이 되었다는 안내, 구형 경로 위험 3종(파일 읽기 범위 비제한·임의 Bash 실행 가능·네트워크 유출 가능), 위험 확인 체크박스와 "구형 Brain 켜기" 버튼(체크 전 비활성), "새 경로 출시를 기다린다"는 선택지(아무 동작 없음 안내). 켜진 뒤에는 기존 대화 UI와 `legacy` 배지, "구형 Brain 끄기" 버튼을 보이고 끈 직후 응답의 `running_turns`가 1 이상이면 "진행 중인 N개 질의는 끝까지 진행됩니다"를 표시한다. Settings의 선프라임 토글은 꺼짐일 때 동작하지 않는다는 안내를 덧붙인다. | AC-3 "화면에 표시", AC-4 |
| D-20. E2E 세션 부트스트랩 | `environment.json`에 선택 키 `session_bootstrap`(`{"service", "command", "cwd"?, "env"?, "timeout_s"?}`)을 추가한다. 하네스는 `service`가 health를 통과한 뒤 `command`를 1회 실행하고 stdout JSON `{"headers": {이름: 값}, "browser_entry_fragment": "entry=<token>"}`만 받아들인다(그 밖의 키·비JSON·비0 종료·타임아웃(기본 30초, `timeout_s`로 조정)은 stdout을 싣지 않는 `e2e_session_bootstrap_failed`이며 기존 SUT 기동 실패와 같은 경로로 `infra_error` 종료하고 이미 기동한 서비스는 회수한다). `headers`는 API executor가 모든 요청에 병합하고(스텝 지정 헤더가 우선), fragment는 브라우저 `entry_url` 뒤에 `#`로 붙인다. `x-csrf-token` 헤더와 URL fragment의 `entry` 값은 증적 마스킹 대상에 추가한다. 키가 없는 기존 환경 파일은 동작이 변하지 않는다. | AC-6. 프레임워크 도구가 OPAL Console을 직접 알지 않도록 프로젝트가 선언하는 훅으로 둔다. 기존 선택 키(`secrets`·`data`) 확장 방식과 같다. |
| D-21. E2E SUT 구성 | `.opal/e2e/environment.json`의 backend 환경에 `OPAL_CONSOLE_CORS_ORIGINS={service.frontend.url}`을 넣고 `session_bootstrap`을 선언한다. 부트스트랩 스크립트 `.opal/e2e/console_session.py`는 상속된 `OPAL_HOME`에 `entry_token`으로 token 2개를 발급해 하나는 `--base-url` 백엔드에 직접 교환(`Origin`=base-url)하고 `Cookie`·`X-CSRF-Token`·`Origin` 헤더를 만들며, 다른 하나는 브라우저용 fragment로 돌려준다. 사용자 Console 7823은 임대 풀에서 계속 제외된다. | AC-6 "자체 포트·HOME의 테스트 서버" |
| D-22. 테스트 계약 | 신규 동작 테스트와 기존 테스트의 새 계약 갱신은 W-8이 소유한다. spawn 0회는 `subprocess.Popen` 대체(호출 횟수 단언)로 검증하고 실제 `claude`는 호출하지 않는다. 모든 `TestClient`는 `base_url="http://127.0.0.1:7823"`(Host `127.0.0.1`)로 만든다. 제품 코드는 `testserver` 같은 테스트 전용 Host를 허용하지 않는다. 인증이 필요한 기존 TestClient 테스트는 `dashboard/backend/tests/auth_helpers.py`의 `authed_client(app)`(같은 base_url, 임시 `OPAL_HOME`에 token 발급→교환, 이후 모든 상태 변경 요청에 `Origin: http://127.0.0.1:7823`·`X-CSRF-Token` 자동 부착)를 쓴다. 제품 코드에 인증 우회 스위치를 두지 않는다. | AC-1, C-1 |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-8. RED 테스트와 새 계약 테스트 갱신 | opal-test-agent (red mode) — 아래 테스트 파일 소유 | `dashboard/backend/tests/auth_helpers.py`, `dashboard/backend/tests/test_auth_gate.py`, `dashboard/backend/tests/test_entry_token.py`, `dashboard/backend/tests/test_legacy_brain_policy.py`, `dashboard/backend/tests/test_brain_legacy_api.py`, `dashboard/backend/tests/test_brain.py`, `dashboard/backend/tests/test_brain_spike.py`, `dashboard/backend/tests/test_routers.py`, `dashboard/backend/tests/test_skill_docs.py`, `dashboard/backend/tests/test_cors_env.py`, `dashboard/backend/tests/test_main.py`, `dashboard/backend/tests/test_deploy_smoke.py`, `dashboard/frontend/src/lib/auth.test.ts`, `dashboard/frontend/src/components/auth/LockScreen.test.tsx`, `dashboard/frontend/src/pages/brain/brain-legacy-gate.test.tsx`, `dashboard/frontend/src/pages/brain/brain-navigation-guard.test.tsx`, `scripts/tests/test_console_open.sh`, `opal/tools/test-tool/tests/test_e2e_session_bootstrap.py`, `opal/tools/test-tool/tests/test_e2e_sut_http_surfaces.py` | TEST-SCENARIO의 `구현 전 RED` 시나리오를 D-1~D-22 공개 계약으로 실패하게 작성한다. 신규 파일 8종은 D-1~D-21을 검증하고, 기존 테스트는 새 계약만 반영해 갱신한다: Brain·라우터·스킬 문서 테스트는 `authed_client` 사용, Brain 어댑터 테스트는 `subprocess.run` 대신 `subprocess.Popen` 대체, 기동 선프라임 테스트는 정책 켜짐 전제 명시, CORS 테스트는 `allow_credentials is True`, `test_main.py`·`test_deploy_smoke.py`는 `TestClient`의 기본 Host(`testserver`)가 허용되지 않으므로 `base_url="http://127.0.0.1:7823"`를 지정하도록 바꾸고 단언은 그대로 두며, SUT 스위트는 부트스트랩 인증을 전제로 하고 `sut-brain-prime`·`sut-brain-query` 기대를 403 `legacy_brain_disabled`로, `sut-config-prewarm`은 설정 쓰기만 단언하도록 바꾼다. 갱신된 기존 기대는 구현 중 약화하지 않는다. | 없음 | P1 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, C-1, C-2, C-3 |
| W-1. 구형 Brain 정책과 spawn 게이트 | opal-be-agent — `dashboard/backend/adapters/`·`config.py` 소유 | `dashboard/backend/adapters/brain_policy.py`, `dashboard/backend/adapters/opbr_adapter.py`, `dashboard/backend/adapters/brain_session.py`, `dashboard/backend/config.py` | D-15~D-17 구현. `config.py`에 `load_legacy_brain_enabled()`(키가 JSON `true`일 때만 참)를 추가하고 기존 함수는 변경하지 않는다. `brain_policy.py`에 정책 싱글턴(`is_enabled`·`set_enabled`·`spawn_guard`·`running_turns`·`reload_from_config`)과 `LegacyBrainDisabled`를 둔다. `opbr_adapter.prime_and_ask`를 `Popen`+락 밖 `communicate`로 바꾸고 `brain_session.py`의 Registry·풀 리필 진입점에 게이트를 건다. | W-8 | P2 | AC-3, C-3 |
| W-2. 인증 코어 | opal-be-agent — 신규 3파일 소유 | `dashboard/backend/auth.py`, `dashboard/backend/entry_token.py`, `dashboard/backend/routers/auth.py` | D-1~D-7, D-9, D-10 구현. `entry_token.py`(발급·소비·`python -m ... issue` CLI), `auth.py`(Host·Origin 정책 판정, 세션 저장소, 순수 ASGI 미들웨어 — http와 websocket 모두), `routers/auth.py`(교환·세션 조회 엔드포인트). 앱 등록은 하지 않는다(W-4). | W-8 | P2 | AC-1, AC-2, AC-5, C-1, C-2 |
| W-3. FE 인증 게이트·Brain 첫 진입·구형 토글 | opal-fe-agent — `dashboard/frontend/` 소유 | `dashboard/frontend/index.html`, `dashboard/frontend/src/lib/api.ts`, `dashboard/frontend/src/lib/auth.ts`, `dashboard/frontend/src/App.tsx`, `dashboard/frontend/src/components/auth/LockScreen.tsx`, `dashboard/frontend/src/pages/brain/BrainLegacyGate.tsx`, `dashboard/frontend/src/pages/brain/BrainPage.tsx`, `dashboard/frontend/src/pages/settings/SettingsPage.tsx` | D-13, D-14, D-19 구현. `auth.ts`·`api.ts`·`App.tsx`로 부트스트랩·잠금 전환을 만들고, `BrainPage.tsx`의 기존 구현은 대화 컴포넌트로 보존한 채 `BrainLegacyGate`가 감싸는 구조로 바꾼다(기존 export 헬퍼는 유지). 백엔드 계약은 D-10·D-18을 그대로 따른다. | W-8 | P2 | AC-2, AC-3, AC-4, C-2 |
| W-4. 앱 배선 | opal-be-agent — `main.py`·`routers/brain.py`·`models.py` 소유 | `dashboard/backend/main.py`, `dashboard/backend/routers/brain.py`, `dashboard/backend/models.py` | D-8, D-11, D-18 구현. `main.py`: 인증 미들웨어를 CORS 안쪽에 등록하고 `CORS_ORIGINS`를 전달, `allow_credentials=True`·`allow_headers` 고정(D-8), 인증 라우터 등록, `/health`에 `auth` 필드, lifespan에서 `brain_policy.reload_from_config()` 후 꺼짐이면 `_prewarm_targets` 스레드를 만들지 않음. `routers/brain.py`: `GET·POST /api/brain/legacy`, 꺼짐 시 prime·query 403 envelope, `LegacyBrainDisabled` 매핑, 끄기 시 풀 폐기. `models.py`: 구형 Brain 요청·응답 모델. | W-1, W-2 | P3 | AC-1, AC-3, AC-5, C-1, C-3 |
| W-5. CLI 진입 계약 | opal-task-agent — `console.sh` 소유 | `opal/tools/opal-cli/lib/console.sh` | D-12 구현. `open` 분기에 구버전 판별·token 발급 헬퍼(`_console_issue_entry_token`)·fragment URL 열기를 넣고 다른 서브커맨드·PID 레코드·플랫폼 분기 격리 구조는 유지한다. 출력과 로그에 token을 쓰지 않는다. | W-2 | P3 | AC-2, C-2, C-4 |
| W-6. E2E 하네스 세션 부트스트랩 접합 | opal-task-agent — `opal/tools/test-tool/lib/e2e/`·`.opal/e2e/` 소유 | `opal/tools/test-tool/lib/e2e/environment.py`, `opal/tools/test-tool/lib/e2e/orchestrator.py`, `opal/tools/test-tool/lib/e2e/executors/api.py`, `opal/tools/test-tool/lib/e2e/redaction.py`, `.opal/e2e/environment.json`, `.opal/e2e/console_session.py`, `opal/tools/test-tool/README.md` | D-20, D-21 구현. `environment.py` 스키마·렌더, `orchestrator.py`의 부트스트랩 실행·context 전달·브라우저 `entry_url` fragment, `api.py`의 인증 헤더 병합, `redaction.py`의 마스킹 확장, 프로젝트 선언·스크립트, README의 키 설명. | W-4 | P4 | AC-6, C-2, C-4 |
| W-7. 프로젝트 문서 동기화 | opal-task-agent — 문서 소유 | `docs/ARCHITECTURE.md`, `docs/PROJECT.md`, `docs/SECURITY.md`, `README.md`, `opal/tools/opal-cli/README.md` | "문서 갱신" 6종 중 test-tool README를 제외한 5종을 구현된 계약 기준으로 갱신한다. 수기 누적 이력 절을 만들지 않고(`.opal/AGENT.md` 금지사항) 현재 사실만 쓴다. | W-4, W-5 | P4 | AC-1, AC-2, AC-3, AC-4, AC-5, C-1, C-3, C-4 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. `subprocess.run`→`Popen`+`communicate` 전환 후에도 기존 어댑터 계약(타임아웃 오류 의미·`shell=False`·`cwd`·JSON 파싱·is_error 판정)이 그대로다 | `opbr_adapter.prime_and_ask`의 반환·예외 의미 | 켜진 구형 Brain의 질의 회귀(응답 유실·타임아웃 미처리) | D-16이 계약 보존을 명시하고 W-8이 기존 `test_brain*.py` 어댑터 단언을 `Popen` 대체로 옮겨 같은 기대를 유지(S-9) |
| H-2. 교차 포트 개발 구성(FE 5173→BE 7823)에서 `SameSite=Strict` 쿠키와 `X-CSRF-Token`이 `credentials: include`+정확 Origin CORS로 전달된다 | D-8의 CORS·쿠키 가정 | 개발 FE·E2E 프론트 SUT에서 항상 401 | CORS 계약 테스트(S-3)와 FE SUT가 백엔드의 허용 origin을 `{service.frontend.url}`로 받는 구성(D-21)이 실제 렌더 가능한지 `render_service` 단위 확인(S-14), 브라우저 관통(S-17) |
| H-3. test-tool SUT 백엔드와 하네스 부트스트랩 스크립트가 같은 `OPAL_HOME`을 상속해 같은 token 디렉터리로 해석한다 | D-9·D-21의 경로 해석 | E2E에서 교환이 항상 실패해 AC-6 미달 | 격리 `HOME`·`OPAL_HOME` 하위 프로세스로 `e2e run`을 돌리는 SUT 스위트(S-15)가 실제 교환을 관통 |
| H-4. 이미 떠 있는 구버전(인증 게이트 없는) Console 데몬이 남아 있으면 새 계약이 적용되지 않는다 | `console open`이 구버전에 token을 발급해도 의미가 없고 보호도 없다 | 업그레이드 후 인증 없는 포트가 계속 열려 있음 | D-11 `/health` 마커로 구버전을 식별해 열지 않고 재기동을 안내(S-12). 설치기의 기존 stop→start 경로는 변경하지 않는다 |
| H-5. 끄기 요청과 spawn이 경합해도 끄기 완료 뒤 새 프로세스가 0회다 | D-16 직렬화의 원자성 | 사용자가 끈 뒤에도 `claude -p`가 시작됨(AC-3 정면 위반) | 락 안 허가+`Popen` 시작, `set_enabled` 동일 락. 스레드 배리어로 경합을 만드는 결정론 테스트(S-7) |

## Release and recovery

- 적용 순서: P1 RED 작성과 `scenario-lock` → P2 BE 정책·BE 인증 코어·FE 병렬 → P3 앱 배선·CLI → P4 E2E 접합·문서 → TEST. 배선(W-4) 전에는 인증이 앱에 연결되지 않으므로 중간 상태의 사용자 영향은 없다.
- 검증 범위: 결정론(BE pytest, FE vitest, 셸 회귀)과 실제 연동(test-tool이 임대 포트 위에 기동한 SUT를 격리 `HOME`으로 관통하는 SUT 스위트 + 신규 부트스트랩 시나리오)을 구분한다. 사용자 Console 7823·사용자 `~/.opal`·실제 `claude`·설치기는 이 태스크에서 실행하지 않는다. 설치본 확인은 설치 경로 복사 구조를 쓰는 기존 `test_deploy_smoke.py`(설치본이 없으면 skip)와 임시 `dashboard-server` 구조에서의 `python -m dashboard.backend.entry_token issue` 실행 시나리오로 한정한다.
- 실측 경계: 시간·품질 목표 없음.
- 실패 시: 배포 전에는 브랜치 변경을 되돌리면 되고 데이터 마이그레이션이 없다. 배포 후 문제는 데몬 재설치(이전 설치본)로 복구되며, 저장 상태는 `console.config.json`의 `legacy_brain_enabled` 키뿐이라 이전 버전은 이 키를 무시한다. 런타임 token 디렉터리는 안전하게 삭제해도 새 `console open`이 다시 만든다.
