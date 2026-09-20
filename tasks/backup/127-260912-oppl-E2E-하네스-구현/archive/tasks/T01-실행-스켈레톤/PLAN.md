---
template: sdlc-v2
---
# PLAN: T01 실행 스켈레톤 — 주소 주입·CORS·임대 포트 SUT 기동

> 입력: [TASK.md](../../TASK.md), [CONTRACT.md](../../CONTRACT.md), [TRD.md](../../TRD.md), [PRD.md](../../PRD.md), [surfaces.json](../../surfaces.json)
> 이 단계는 설계·시나리오만 산출한다. 구현은 T3에서 수행한다.

## Approach

FE 주소 주입(3파일 동시) → BE CORS 추가 허용 → `lib/e2e/` 최소 골격(가용 포트 bind · strict-port 기동 · health gate · 프로세스 그룹 회수) 순으로 쌓고, 마지막에 FE→BE 실 호출 1건을 헤드리스 브라우저로 관통시킨다.

범위 경계 3개를 고정한다.

1. **T03 경계**: allocator lock(`{artifact_root}/.leases/.lock`) · lease record(`CONTRACT.md` §A.7) · stale 회수(C-LEASE-2) · worktree 동시성(MV-36)은 만들지 않는다. T01의 포트 확보는 "bind 가능한 포트를 고르고 strict-port 기동 실패면 다시 고른다"까지다.
2. **T04 경계**: `test-tool e2e run` CLI(`CONTRACT.md` §B.1)와 run 상태 머신·`run.json`·verdict 조립은 만들지 않는다. T01 골격은 라이브러리 함수로만 존재하고 `sys.exit`를 호출하지 않는다.
3. **T05+ 경계**: `lib/e2e/drivers/*`를 신설하지 않는다. 완료 기준 5의 브라우저 구동 코드는 **테스트 측**(`opal/tools/test-tool/tests/`)에 둔다.

변경 0 계약 대상은 손대지 않는다 — `lib/e2e_contract.py`, `lib/scenario.py`, `opal/tools/worktree-tool/**`, `opal/tools/opal-cli/lib/console.sh`(T02 소유).

## 현행 실측과 변경 전/후

| 지점 | 현행(실측) | 변경 후 |
|---|---|---|
| `dashboard/frontend/src/lib/api.ts:14` | `export const API_BASE_URL = "http://127.0.0.1:7823";` | `import.meta.env.VITE_API_BASE_URL ?? ""` (base에 `/api` 없음 — 결합부 `api.ts:69` `` `${API_BASE_URL}${path}` ``는 불변) |
| `API_BASE_URL` 외부 소비자 | 0건. `api.ts:7`(@header exports), `:14`(선언), `:69`(사용) 3곳뿐 (전수 grep) | 변경 표면은 `api.ts` 1파일 |
| `dashboard/frontend/src/**/*.d.ts` | 0건 | `src/vite-env.d.ts` 신설 |
| `dashboard/frontend/tsconfig.app.json:7` | `"types": ["vite/client"]` **이미 존재** | 불변 |
| `node_modules/vite/types/importMeta.d.ts:14` | `interface ImportMetaEnv extends Record<string, any>` — 임의 `VITE_*` 키가 이미 `any`로 통과 | `vite-env.d.ts` 선언 병합으로 `VITE_API_BASE_URL`을 `string \| undefined`로 승격 |
| `dashboard/frontend/.env*` | 0건. `.gitignore`는 `*.local`만 무시하고 `.env*`는 무시하지 않음 | `.env.development` 신설(추적 대상) |
| `dashboard/backend/main.py:76-79` | 모듈 상수 `CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]` | 같은 2종 + `OPAL_CONSOLE_CORS_ORIGINS` 파싱 결과 추가 |
| `dashboard/backend/main.py:81-87` | `allow_credentials=False`, `allow_methods=["GET","POST"]`, `allow_headers=["*"]` | `allow_origins`만 교체. 나머지 3개 인자 불변 |
| `dashboard/backend/tests/` | **빈 디렉터리 아님** — `__init__.py` + 테스트 13파일(`test_main.py` 등) | 파일 1건 추가 |
| `opal/tools/test-tool/lib/` | `e2e_adapter.py`, `e2e_contract.py`, `resolver.py`, `runner.py`, `scenario.py` — `e2e/` 패키지 없음 | `e2e/` 패키지 4파일 신설 |
| 도구 인터프리터 | `opal/tools/test-tool/run.sh:4` — `VENV_PYTHON="$HOME/.opal/.venv/bin/python"`. 이 venv에만 fastapi 0.137.0·uvicorn 0.42.0·pytest·jsonschema가 있고 system `python3`에는 **없다** | 모든 pytest 실행과 SUT backend 기동은 `~/.opal/.venv/bin/python`을 쓴다(읽기 전용 실행 — `~/.opal/`에 쓰지 않으므로 배포 경계 위반 아님) |
| `opal/tools/test-tool` pytest baseline | **84 passed, 100 subtests passed** — `~/.opal/.venv/bin/python -m pytest opal/tools/test-tool/tests/ -q` (저장소 루트 기준) | 84 passed 유지 |
| `dashboard/frontend` typecheck baseline | `npm run typecheck` exit 0 | exit 0 유지 |
| FE 루트 화면 초기 호출 | `src/pages/dashboard/DashboardPage.tsx:1170-1177` — `GET /api/dashboard` (`contextProject` 미설정 시 쿼리 없음) | 불변. 완료 기준 5의 관측 대상 |
| `.opal/code-scan.json` | `headerSource: "inline"`, scopes `framework=opal/`·`console-fe=dashboard/frontend/src/`·`console-be=dashboard/backend/`, extensions에 `.ts`·`.py` 포함(`.env`류 없음) | 신설 `.ts`·`.py`에 인라인 @header 필수, `.env.development`는 대상 아님 |
| headless Chromium | `~/Library/Caches/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-mac-arm64/chrome-headless-shell` 존재. `node -v` = v25.8.2(전역 `WebSocket` 사용 가능) | 설치 0건으로 real-usage 관측 가능 |

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| D-1. `api.ts:14`를 `import.meta.env.VITE_API_BASE_URL ?? ""`로 바꾸고 결합부는 손대지 않는다 | `API_BASE_URL`은 `string`. 미주입 시 `""` → 동일 오리진. base에 `/api` 접두사 없음 | `TRD.md` TD-6, `TASK.md` C-8, `CONTRACT.md` §A.14 [MUST]. `/api`를 넣으면 `api.ts:69` 결합으로 `/api/api/dashboard`가 된다 |
| D-2. `vite-env.d.ts`는 `/// <reference types="vite/client" />` + `ImportMetaEnv` 선언 병합으로 작성한다 | `import.meta.env.VITE_API_BASE_URL: string \| undefined` | `tsconfig.app.json:7`이 이미 `vite/client`를 포함하므로 typecheck는 선언 없이도 통과한다(실측). 선언의 실제 값은 `any`→`string \| undefined` 승격과 `CONTRACT.md` MV-25 충족이다. 드리프트는 §BLOCKED D-4 참조 |
| D-3. `.env.development`는 `VITE_API_BASE_URL=http://127.0.0.1:7823` 1줄 + 주석 | `npm run dev`(5173) 개발 흐름이 오늘과 동일하게 7823 backend를 호출한다 | `TRD.md` TD-6. mode=`development`에서만 로드되므로 `npm run build`(mode=production)·`vitest`(mode=test)에는 적용되지 않는다 → 완료 기준 2의 빈 문자열 동작이 보존된다 |
| D-4. BE는 기본 2종을 **코드에 남기고** env 값을 뒤에 이어 붙인다 | `CORS_ORIGINS = _DEFAULT_DEV_ORIGINS + _parse_extra_origins(os.getenv("OPAL_CONSOLE_CORS_ORIGINS"))` | `TRD.md` TD-7 "기본값 유지 + 추가 허용만". `CONTRACT.md` §C.9가 `dev` 앞 2개를 계약값으로 고정 |
| D-5. env 파싱은 쉼표 split → strip → 빈 문자열 제거 → 순서 유지 중복 제거. **검증 실패 항목은 조용히 버리지 않고 로그 경고 후 제외** | 결과 목록의 모든 원소는 `^https?://[^/,\s]+$`를 만족하고 `*`·`${`를 포함하지 않는다 | `CONTRACT.md` §C.9 전개 규칙 + MV-27. 플레이스홀더가 그대로 넘어오면 CORS가 조용히 무효 origin을 등록하는 것을 막는다 |
| D-6. `allow_credentials`·`allow_methods`·`allow_headers`·`allow_origin_regex`는 건드리지 않는다 | 등록부는 `allow_origins` 인자만 바뀐다 | `TRD.md` TD-7, `CONTRACT.md` §C.8 "보안 경계의 실체" (b)(c). `allow_origin_regex`는 **도입 자체를 금지** |
| D-7. `lib/e2e/`는 `__init__.py`·`process.py`·`ports.py`·`runtime.py` 4파일로만 만든다 | `ports.py`는 `find_free_port`만 노출하고 lock·lease record·stale 회수 함수를 **선언하지 않는다**(stub도 두지 않는다) | T03 소유 경계. 빈 stub을 두면 T03가 계약을 재설계해야 한다 |
| D-8. 기동 실패·health 실패는 상태 문자열이 아니라 `SutStartupError(reason=...)` 예외로 올린다 | reason 코드 집합 = `{port_bind_exhausted, process_exited_early, health_timeout, health_bad_response}`. `FINAL_STATUSES`·`OPERATIONAL_STATUSES`·`PROFILES` 값과 교집합 0 | `CONTRACT.md` C-125-1·MV-19(a). 상태 매핑은 T04 orchestrator가 `e2e_contract` 함수로만 수행한다 |
| D-9. OS 분기는 `process.py`에만 둔다 | `runtime.py`·`ports.py`에 `sys.platform`·`os.name`·`platform.system()`이 0건 | `TRD.md` TD-16, `CONTRACT.md` §C.2 [MUST], MV-20. `sys.executable`·`shutil.which`는 OS 조건문이 아니므로 다른 모듈에서 사용 가능 |
| D-10. child는 새 세션/프로세스 그룹으로 띄우고 회수는 pgid 단위 `SIGTERM → grace → SIGKILL`. **회수 후 그룹 잔존 구성원을 실제로 재열거해 집계한다** | `terminate_process_group(pgid)`는 `{released: bool, method, leaked: list[int]}`를 반환한다. `leaked`는 리더 pid 생존 여부가 아니라 **`SIGKILL` 이후에도 남은 그룹 구성원 pid 전건**이다. 열거는 `os.killpg(pgid, 0)`로 그룹 잔존을 먼저 판정하고, 잔존 시 `ps -o pid= -g <pgid>` 결과를 파싱해 pid 목록을 채운다(이 호출은 `process.py` 안에 둔다) | `TRD.md` TD-5 마지막 항·TD-15, `CONTRACT.md` §C.1·§C.3. **리더 pid 1건만 보면 vite 손자(esbuild) 누출이 검출되지 않는다** — `start_new_session=True`에서 pgid == 리더 pid이므로 리더 검사는 H-3을 전혀 커버하지 못한다. 열거는 pgid 범위로 한정되며 이름 패턴 매칭이 아니므로 C-1·§C.3 위반이 아니다 |
| D-11. **포트 확보 책임은 호출자에게 있다.** `start_backend`·`start_frontend`는 확보된 포트를 **필수 명시 인자 `port`로 받는다** | 두 함수는 내부에서 `find_free_port`를 호출하지 않는다. 호출자가 확보한 정수 그대로 기동한다 | F-1. 함수가 포트를 자체 확보하면 호출자가 CORS origin 문자열을 조립할 시점에 실제 포트를 알 수 없다. 그러면 브라우저가 뜨는 실제 vite origin이 backend 허용 목록에 없어 요청이 CORS로 차단되고, CDP `Network.responseReceived`는 200을 보고하는데 앱 `fetch`는 실패한 **거짓 통과**가 성립한다 |
| D-12. 기동 순서를 **frontend 포트 확보 → backend 포트 확보 → origin 문자열 조립 → backend 기동+health → frontend 기동**으로 고정한다 | 호출자는 `fe_port = find_free_port()` → `be_port = find_free_port()` → `origin = f"http://127.0.0.1:{fe_port}"` → `start_backend(port=be_port, env_extra={"OPAL_CONSOLE_CORS_ORIGINS": origin})` → `wait_healthy` → `start_frontend(port=fe_port, backend_url=f"http://127.0.0.1:{be_port}")` 순으로 호출한다 | F-1·H-4. 주입되는 origin과 브라우저가 실제로 뜨는 origin이 **같은 정수**에서 나오는 것이 CORS 통과의 유일한 보증이다. backend를 먼저 health까지 올려야 vite 기동 직후 첫 화면 요청이 연결 거부로 실패하지 않는다 |
| D-13. strict-port는 D-11의 `port` 인자 위에서 성립한다 | backend: `{venv_python} -m uvicorn dashboard.backend.main:app --host 127.0.0.1 --port {port}` — uvicorn은 지정 포트 점유 시 스스로 기동 실패한다. frontend: `npm run dev -- --host 127.0.0.1 --port {port} --strictPort` — vite가 포트를 자동 증가시키지 않는다. 어느 쪽이든 기동 실패는 `SutStartupError(reason="process_exited_early")`이며, 재선택 루프는 **호출자**가 `MAX_PORT_ATTEMPTS`회까지 수행한다(포트 확보 책임이 호출자에게 있으므로 재확보 책임도 호출자에게 있다) | `TRD.md` TD-3 4~5번, `CONTRACT.md` C-LEASE-3. `sys.executable`이 아니라 venv python을 쓰는 근거는 §현행 실측표 도구 인터프리터 행 |
| D-14. health gate는 stdlib `urllib.request`로 `GET {backend_url}/health`를 폴링하고 200 + JSON `status` 키를 요구한다 | `sut-health` 표면(`surfaces.json`) response_shape `{status,version}` 소비. 신규 의존 0 | `CONTRACT.md` §B.5. `requests`는 미설치이므로 도입 금지(패키지 설치 금지) |
| D-15. 완료 기준 5의 브라우저 구동은 테스트 모듈이 TMPDIR에 생성한 Node 스크립트를 `node`로 실행해 CDP를 구동한다 | 저장소에 추가되는 브라우저 파일 0건. npm 패키지 0건 | 설치 금지 + `lib/e2e/drivers/*` 신설 금지. Node v25 전역 `WebSocket` 사용(실측) |
| D-16. chrome-headless-shell 경로는 하드코딩하지 않고 `CHROME_HEADLESS_SHELL` env override → `~/Library/Caches/ms-playwright/chromium_headless_shell-*/**/chrome-headless-shell` glob 순으로 탐색한다 | 다른 머신에서 경로 부재가 **실패가 아니라 미가용**으로 구분된다 | 이식성. 판정 문자열은 테스트 측에만 존재하며 `lib/e2e/`에는 등장하지 않는다(MV-19(a)) |
| D-17. **브라우저 미발견은 조용한 skip이 아니라 hard fail이다.** `OPAL_E2E_ALLOW_NO_BROWSER=1`이라는 명시적 opt-out이 설정된 경우에만 skip으로 강등하며, 그때도 결과에 `executor_unavailable` 사유를 반드시 남긴다 | 기본 경로에서 S-7은 pytest `fail`로 끝난다(exit ≠ 0). opt-out 경로에서는 skip reason 문자열에 `executor_unavailable`과 탐색한 경로를 모두 기록한다 | A-1. S-7은 이 태스크에서 `real-usage` 문턱(`required_fidelity`)을 충족시키는 **유일한** 행이다. 조용한 skip은 pytest exit 0을 내므로, 문턱을 충족한 실행이 0건인 채로 태스크가 done이 될 수 있다 |
| D-18. `npm run build` 검증은 `npm run build -- --outDir "$TMPDIR/opal-e2e-fe-build-$$/dist" --emptyOutDir`로 수행하고, **이 빌드를 S-2 판정 절차의 필수 단계로 묶는다** | 저장소 `dashboard/frontend/dist/`가 생성되지 않는다. S-2는 파일 존재 2건 + typecheck exit 0 + build exit 0을 **모두** 요구하며 어느 하나라도 빠지면 미충족이다 | `TASK.md` C-5, `CONTRACT.md` §C.6 [MUST], MV-28 + A-2(파일 존재만 검사하면 "둘 다 있는데 빌드가 깨진" 상태를 통과시킨다) |
| D-19. 사용자 `127.0.0.1:7823` Console은 **읽기 전용 health probe**로만 접촉한다 | 기동·종료·재설치 0건. run 전 baseline(응답/무응답)과 run 후가 같은지만 본다 | `TASK.md` C-2, `CONTRACT.md` §C.3. 현재 이 Console은 **기동 중(health 200)**이므로 baseline은 "200 → 200 동일"이다 |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. FE 주소 주입 3파일 동시 변경 | opal-fe-agent | `dashboard/frontend/src/lib/api.ts`, `dashboard/frontend/src/vite-env.d.ts`(신설), `dashboard/frontend/.env.development`(신설) | (a) `api.ts:14`를 `export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";`로 교체하고 `:69` 결합부는 불변 유지. `api.ts:6` @header description에서 고정 주소 전제를 env 주입 전제로 갱신(현재 사실만). (b) `vite-env.d.ts`: @header 블록 주석 → `/// <reference types="vite/client" />` → `interface ImportMetaEnv { readonly VITE_API_BASE_URL?: string }` 선언 병합(삼중 슬래시 지시자 앞에는 주석만 허용되므로 이 순서를 지킨다). (c) `.env.development`: 주석 1줄 + `VITE_API_BASE_URL=http://127.0.0.1:7823`. **세 파일은 한 커밋 단위로 함께 바꾼다**(RK-2) | 없음 | P1 | C-8, AC-13 (backlog 완료기준 1·2) / MV-24, MV-25 |
| W-2. BE CORS 환경 변수 추가 허용 | opal-be-agent | `dashboard/backend/main.py` | `:76-79`를 `_DEFAULT_DEV_ORIGINS`(기존 2종 상수) + `_parse_extra_origins(os.getenv("OPAL_CONSOLE_CORS_ORIGINS"))` 합성으로 교체하고 결과를 `CORS_ORIGINS`에 대입(기존 이름 유지 — `tests/test_main.py:80-93`이 이 심볼을 읽는다). `_parse_extra_origins`는 D-5 규칙으로 파싱하고 무효 항목은 `logger.warning` 후 제외. `:81-87` 등록부는 `allow_origins=CORS_ORIGINS` 외 인자 불변. `main.py:6` @header description에 CORS env 추가 허용 사실 반영. `import os` 추가 | 없음 | P1 | C-8, AC-1 (backlog 완료기준 3) / MV-26, MV-27 |
| W-3. `lib/e2e/` 최소 골격 | opal-be-agent | `opal/tools/test-tool/lib/e2e/__init__.py`, `.../process.py`, `.../ports.py`, `.../runtime.py` (전부 신설) | §모듈 분해 표대로 구현. 4파일 모두 인라인 @header(`headerSource: inline`). `FINAL_STATUSES`·`PROFILES`·`OPERATIONAL_STATUSES` 값 문자열 리터럴 0건, `sys.exit` 0건, `process.py` 외 OS 분기 0건 | 없음 | P1 | AC-1, C-1, C-5, C-7 (backlog 완료기준 4·6) / MV-19, MV-20 |
| W-4. BE CORS env 주입 테스트 | opal-be-agent | `dashboard/backend/tests/test_cors_env.py`(신설) | `importlib.reload(dashboard.backend.main)`을 `monkeypatch.setenv/delenv`와 조합해 4케이스 검증 — (1) env 미주입 시 `CORS_ORIGINS == _DEFAULT_DEV_ORIGINS`(변경 전과 동일), (2) 단일/복수 origin 주입 시 기본 2종 뒤에 정확한 문자열로만 추가, (3) `${OPAL_E2E_FRONTEND_PORT}` 플레이스홀더·`*`·공백만인 항목이 결과에 없음(MV-27), (4) 등록된 `CORSMiddleware` 옵션에 `allow_credentials is False`·`allow_methods == ["GET","POST"]`·`allow_origin_regex` 미설정·`allow_origins`에 `"*"` 부재(MV-26 — 검사 범위는 origin 축으로 한정, §BLOCKED D-1 참조). 옵션은 `app.user_middleware`에서 읽고, reload 후 모듈 상태가 다른 테스트로 새지 않도록 fixture teardown에서 env 원복 + 재reload | W-2 | P2 | C-8, AC-1 (backlog 완료기준 3) / MV-26, MV-27 |
| W-5. 관통 검증 테스트 1건 | opal-be-agent | `opal/tools/test-tool/tests/test_e2e_skeleton.py`(신설) | 시나리오 S-5~S-8을 담는다. **§호출 순서 계약 ①~⑤를 그대로 따른다**(F-1) — `fe_port`·`be_port`를 테스트가 직접 확보하고, `fe_port`로 조립한 origin을 `start_backend(port=be_port, env_extra=...)`에 주입한 뒤, 같은 `fe_port`를 `start_frontend(port=fe_port, backend_url=...)`에 넘긴다. 이어 `/health`·`/openapi.json`·`/docs` 200 → CORS 실 HTTP 검사(주입 origin / 임의 origin) → D-15/D-16 CDP 관측으로 `http://127.0.0.1:{be_port}/api/dashboard` status 200 수집 → teardown에서 `stop_all` 후 `CleanupReport.leaked == []`(D-10, 그룹 구성원 재열거 기반) · 7823 baseline 대조(D-19) · `git status --porcelain` 전후 대조. 브라우저 미발견 시 D-17(기본 hard fail, `OPAL_E2E_ALLOW_NO_BROWSER=1`일 때만 skip + `executor_unavailable` 기록). Node 스크립트는 `tempfile.TemporaryDirectory()`에 생성한다 | W-1, W-2, W-3 | P2 | AC-1, AC-13, C-2, C-5 (backlog 완료기준 4·5·6) / MV-28 |

### `lib/e2e/` 모듈 분해와 T03 정지선

> W-3의 구현 계약이다.

| 모듈 | T01이 만드는 것 | T01이 만들지 않는 것(소유자) |
|---|---|---|
| `e2e/__init__.py` | 패키지 선언 + @header. re-export 없음 | — |
| `e2e/process.py` — **OS 분기 유일 지점**(TD-16) | `spawn_process_group(argv, *, cwd, env, stdout_path, stderr_path) -> SpawnedProcess{pid, pgid, popen, stdout_path, stderr_path}` (POSIX: `start_new_session=True`) · `pid_alive(pid) -> bool` · `process_group_members(pgid) -> list[int]` (그룹 범위 열거 — 이름 패턴 금지) · `terminate_process_group(pgid, *, grace_seconds=5.0) -> TerminationResult{released, method, leaked: list[int]}` (D-10 — `SIGKILL` 이후 `process_group_members`를 **재호출**해 잔존 pid 전건을 `leaked`에 넣는다) · `temp_root() -> Path`(`TMPDIR` 해석) | Windows 분기 실제 구현(현 범위는 POSIX 경로만 구현하고 비POSIX는 명시적 `NotImplementedError`로 남긴다 — 분기 **지점**은 이 모듈에 고정된다) |
| `e2e/ports.py` | `find_free_port(host="127.0.0.1") -> int` (`socket.bind((host, 0))` → `getsockname()[1]` → close) · `MAX_PORT_ATTEMPTS = 5` 상수. **이 모듈이 포트 확보의 유일한 진입점이며, `runtime.py`는 이 함수를 호출하지 않는다**(D-11) | **T03**: allocator lock(`O_CREAT\|O_EXCL`, C-LEASE-1) · lease record 쓰기/읽기(§A.7) · `state` 전이(`reserved`→`confirmed`→`released`) · stale 회수(C-LEASE-2) · `.leases/` 디렉터리 관리 · worktree 동시성(MV-36). **stub 함수도 두지 않는다** |
| `e2e/runtime.py` | `SutHandle{role, port, url, spawned, log_paths}` · **`start_backend(*, source_root, artifact_dir, port: int, env_extra) -> SutHandle`** · **`start_frontend(*, source_root, artifact_dir, port: int, backend_url: str, env_extra) -> SutHandle`** — 두 함수 모두 `port`가 **필수 키워드 인자**이고 내부에서 `find_free_port`를 호출하지 않는다(D-11·D-13) · `wait_healthy(base_url, *, timeout_s=60.0, interval_s=0.3) -> dict` (D-14) · `stop_all(handles) -> CleanupReport{released[], leaked[]}` — `leaked`는 각 핸들의 `TerminationResult.leaked` pid를 합친 것이며 비어 있지 않으면 정리 실패다(D-10) · `SutStartupError(reason)` (D-8) | 포트 확보·재확보(호출자 책임, D-11·D-13). **T03**: lease 연동. **T04**: run 상태 머신·`run.json`/`journal.json`/`owned.json` 쓰기·verdict·CLI·`OPAL_E2E_*` 전량 주입(T01은 `VITE_API_BASE_URL`·`OPAL_CONSOLE_CORS_ORIGINS`만 주입하고 나머지는 호출자가 `env_extra`로 넘긴다). **T05+**: driver·evidence·redaction |

**reason 오너십 (A-7)**: `process_exited_early`·`health_timeout`·`health_bad_response`는 `runtime.py`가 **단일 시도**의 실패로 직접 raise한다(포트 하나로 기동 1회를 시도한 결과). `port_bind_exhausted`는 `runtime.py`가 raise하지 **않는다** — `MAX_PORT_ATTEMPTS`회 재확보 루프는 호출자 책임(D-11·D-13·H-5)이므로, 소진 판정과 그 reason의 raise도 재시도 루프를 도는 **호출자**가 수행한다. T03·T04는 이 경계를 재해석하지 않는다.

**호출 순서 계약 (F-1 — W-5가 이 순서를 그대로 따른다)**

```text
fe_port = ports.find_free_port()                     # ① frontend 포트 먼저
be_port = ports.find_free_port()                     # ② backend 포트
fe_origin = f"http://127.0.0.1:{fe_port}"            # ③ ①의 정수로 origin 조립
be = runtime.start_backend(port=be_port, env_extra={"OPAL_CONSOLE_CORS_ORIGINS": fe_origin}, ...)
runtime.wait_healthy(f"http://127.0.0.1:{be_port}")  # ④ backend를 먼저 ready로
fe = runtime.start_frontend(port=fe_port, backend_url=f"http://127.0.0.1:{be_port}", ...)  # ⑤
```

[MUST] ③에서 조립한 origin의 포트와 ⑤에서 vite가 실제로 바인딩하는 포트는 **①의 같은 정수**여야 한다. 이 동일성이 깨지면 브라우저 요청이 CORS로 차단되는데도 CDP `Network.responseReceived`는 200을 보고할 수 있어 S-7이 거짓 통과한다. 동일성 보증 수단은 D-11(`port` 명시 인자)과 D-13(strict-port — 다른 포트로 흘러가는 대신 기동 실패) 두 가지다.

## 테스트 시나리오

| id | 설명 | acceptance 매핑 | required_fidelity | surface_ref | 검증 방법 |
|---|---|---|---|---|---|
| S-1 | `api.ts`에 `http://127.0.0.1:7823` 리터럴이 없고 `import.meta.env.VITE_API_BASE_URL`을 참조하며 base에 `/api` 접두사가 없다 | 1 | `mock` | `null` | 소스 정적 검사(MV-24) + `npm run typecheck` exit 0 |
| S-2 | `src/vite-env.d.ts`와 `.env.development`가 **둘 다** 존재하고, 그 상태에서 `npm run typecheck`·`npm run build`가 통과한다 | 1 | `mock` | `null` | **3단 모두가 판정 조건이다**(A-2) — (i) 파일 존재 2건(MV-25), (ii) `cd dashboard/frontend && npm run typecheck` exit 0, (iii) `npm run build -- --outDir "$TMPDIR/opal-e2e-fe-build-$$/dist" --emptyOutDir` exit 0 + 저장소 `dashboard/frontend/dist/` 부재(D-18). (ii)(iii)은 §Release and recovery 회귀 게이트에서 실행되며, S-2는 그 두 명령의 exit 0을 자기 판정에 포함한다. 파일 존재만으로 S-2를 통과 처리하지 않는다 |
| S-3 | `VITE_API_BASE_URL` 미주입 시 `API_BASE_URL === ""`이고 요청 경로가 `/api/...` 동일 오리진 상대 경로로 조립된다 | 2 | `mock` | `null` | vitest(mode=test → `.env.development` 미로드, 실측 근거 D-3): `api.ts` import 후 `API_BASE_URL` 값 + `fetch` 스텁으로 전달된 URL 문자열 검사 |
| S-4 | env 미주입 시 허용 목록이 변경 전(`localhost:5173`, `127.0.0.1:5173`)과 동일하고, 주입 시 그 origin만 정확한 문자열로 추가되며, `*`·정규식·플레이스홀더가 없고 `allow_credentials=False`·`allow_methods=["GET","POST"]`가 유지된다 | 3 | `mock` | `null` | W-4 pytest(in-process ASGI · 모듈 reload). MV-26, MV-27 |
| S-5 | 임대한 backend 포트에서 `GET /health`가 200 + `{status,version}`을 반환하고 OpenAPI 문서 표면(`GET /openapi.json`, `GET /docs`)이 200으로 노출된다 | 4 | `real-http` | `sut-health` | W-5: §호출 순서 계약 ①②③④ — `find_free_port`로 확보한 `be_port`를 `start_backend(port=be_port)`에 명시 전달 → `wait_healthy` → stdlib `urllib` 실 HTTP 3회 |
| S-6 | 임대 backend가 주입된 frontend origin 요청에 `Access-Control-Allow-Origin`을 **그 정확한 문자열**로 반환하고, 미주입 origin 요청에는 해당 헤더를 반환하지 않는다 | 3 | `real-http` | `sut-health` | W-5: 실 기동 backend에 `Origin` 헤더를 붙인 `GET /health` 2회(주입 origin / 임의 origin) |
| S-7 | 임대 frontend 포트의 vite dev 서버가 임대 backend를 가리키고, **브라우저 화면에서 발생한** 실제 HTTP 호출 1건(`GET /api/dashboard`)이 임대 backend에 도달해 200을 받는다 | 5 | `real-usage` | `sut-dashboard` (§BLOCKED D-5) | W-5: §호출 순서 계약 ①~⑤로 기동(③의 origin 포트 == ⑤의 vite 포트, F-1) → CDP(D-15) `Network.enable` → `Page.navigate(http://127.0.0.1:{fe_port}/)` → `Network.responseReceived`에서 `url == http://127.0.0.1:{be_port}/api/dashboard` **AND** `status == 200` 수집. **이 CDP Network 관측 1건이 유일한 판정 조건이다**(locked `test-scenario.json` S-7 `expected` 원문과 일치). `Runtime.evaluate` DOM 확인은 **판정 조건이 아니라 실패 시 원인 추적용 보조 진단 증적**이며, 그 결과로 S-7을 pass/fail시키지 않는다(A-5). 브라우저 미발견 시 D-17 — 기본은 hard fail이며 `OPAL_E2E_ALLOW_NO_BROWSER=1`일 때만 skip + `executor_unavailable` 기록, 그 경우 완료 기준 5는 **충족되지 않은 것으로 남긴다** |
| S-8 | 기동한 두 프로세스가 종료 시 그룹 단위로 회수되고(누출 0), 사용자 `127.0.0.1:7823` Console 상태가 run 전후 동일하며, 저장소에 `dist/`를 포함한 새 추적·미추적 파일이 생기지 않는다 | 6 | `real-http` | `null` | W-5 teardown: `stop_all` 후 **`CleanupReport.leaked == []`** — 이 단언이 회수 판정의 본체다. `leaked`는 `SIGKILL` 이후 `process_group_members(pgid)`를 재호출해 얻은 **잔존 구성원 pid 전건**이다(D-10). 그룹 리더 pid 1건만 `pid_alive`로 보는 검증은 **금지한다** — `start_new_session=True`에서 pgid == 리더 pid이므로 리더 검사는 항상 통과하고 H-3이 지목한 vite 손자(esbuild) 누출을 전혀 잡지 못한다(A-4). 이어 7823 health baseline/after 대조(D-19, 읽기 전용) · `git status --porcelain` 전후 문자열 동일(MV-28) · `dashboard/frontend/dist` 부재 확인 |

> `required_fidelity` 사다리는 `mock < real-http < real-usage`(`lib/scenario.py:119` `FIDELITY_ORDER`). 이 태스크의 문턱은 `real-usage`이며 S-7이 유일하게 그 문턱을 충족시키는 행이다. S-7이 `executor_unavailable`이면 태스크 전체가 문턱 미달이다.

## 기계검증절 충족 매핑

| MV | 충족 수단 | 판정 지점 |
|---|---|---|
| MV-24 | W-1(a) — `api.ts`에서 고정 주소 리터럴 제거, `import.meta.env.VITE_API_BASE_URL` 참조 도입 | S-1 grep 검사 |
| MV-25 | W-1(b)(c) — 두 파일을 **같은 Work item**에서 동시 신설 | S-2 파일 존재 2건 검사 |
| MV-26 | W-2 D-6 — `allow_origins`만 교체하고 `allow_credentials=False`·`allow_methods=["GET","POST"]` 유지, `allow_origin_regex` 미도입, D-5 파싱이 `*` 항목 제외 | S-4(W-4) — `app.user_middleware`의 `CORSMiddleware` 옵션 검사 |
| MV-27 | W-2 D-5 — 파싱 결과 전 원소가 `^https?://[^/,\s]+$` 만족, `${` 미포함 | S-4(W-4, 파싱 단위) + S-6(W-5, 실 HTTP 응답 헤더가 정확한 origin 문자열) |
| MV-28 | W-5 teardown + D-18(build outDir를 저장소 밖 `$TMPDIR`로) + `CONTRACT.md` §C.6(산출물은 TMPDIR만) | S-8 — `git status --porcelain` 전후 동일 |
| (참고) MV-19 | W-3 D-8 — `lib/e2e/` 4파일에 상태 enum 값 리터럴 0건, `sys.exit` 0건 | T4a 게이트. T01은 위반을 만들지 않는 것까지 책임진다 |
| (참고) MV-20 | W-3 D-9 — `process.py` 외 OS 분기 0건 | 같음 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1 (RK-2). `api.ts:14`만 바꾸고 `.env.development`를 빠뜨린다 | `npm run dev`(5173)가 자기 자신을 호출해 Console 개발 흐름이 죽는다 | Console FE 개발 회귀 | 3파일을 **하나의 W-1**로 묶어 분할 디스패치를 불가능하게 한다. S-2가 두 파일 존재를 동시 검사(MV-25)하고, S-3가 빈 base 동작을 별도로 못 박는다 |
| H-2 (RK-2 변형). `vite-env.d.ts`를 빠뜨려도 `tsconfig.app.json:7`의 `vite/client` 폴백 때문에 typecheck가 통과해 누락이 드러나지 않는다 | MV-25 위반이 T4a까지 미발견 | 계약 위반 지연 검출 | typecheck를 누락 탐지 수단으로 쓰지 않는다. S-2를 **파일 존재 검사**로 설계했다(실측 근거: §현행 실측표) |
| H-3 (RK-3). vite가 남기는 손자 프로세스(esbuild)가 회수되지 않아 임대 포트가 다음 run을 오염시킨다 | R-3·R-6, 완료 기준 6 | 후속 태스크 전건이 이 환경 위에서 실행되므로 오염이 전파된다 | D-10 — 새 세션으로 기동하고 pgid 단위 `SIGTERM → grace → SIGKILL` 후 **그룹 구성원을 재열거**해 잔존 pid를 `CleanupReport.leaked`에 넣는다. `leaked`가 비지 않으면 S-8이 실패한다. 리더 pid 1건 검사로는 이 위험이 검출되지 않으므로 그 방식을 금지했다(A-4). 이름 패턴 종료는 쓰지 않는다(C-1) |
| H-4. S-7이 CORS 때문에 실패한다 — FE(`127.0.0.1:{fe_port}`)→BE(`127.0.0.1:{be_port}`)는 **cross-origin**이다 | 완료 기준 5 | 관통 실패, 또는 더 나쁘게는 CDP가 200을 보고하는데 앱 fetch는 차단된 **거짓 통과** | W-2를 W-5의 선행으로 고정하고, §호출 순서 계약 ①~⑤를 설계 계약으로 못박는다. 핵심은 **주입 origin의 포트와 vite 실제 바인딩 포트가 같은 정수임을 구조적으로 보증**하는 것이며, 그 수단이 D-11(`port` 필수 명시 인자 — 함수가 포트를 자체 확보하지 않는다)과 D-13(strict-port — 다른 포트로 흘러가지 않고 기동 실패)이다 |
| H-5. `find_free_port` 이후 기동 전까지 다른 프로세스가 그 포트를 가져간다(TOCTOU) | 완료 기준 4 | 간헐 실패 | T01은 lock을 만들지 않는 대신 strict-port 기동 실패를 신호로 보고 **호출자가** `MAX_PORT_ATTEMPTS=5`회 재확보·재기동한다(D-11·D-13, TD-3 5번). 재확보 시 `fe_port`가 바뀌면 CORS origin도 함께 다시 조립해야 하므로, 재시도는 §호출 순서 계약 ①부터 다시 시작한다. 창을 좁히는 allocator lock은 T03 소유이며 T01은 이 잔여 위험을 명시적으로 감수한다 |
| H-6. `dashboard/backend/tests/test_cors_env.py`의 `importlib.reload`가 모듈 전역 상태를 오염시켜 같은 세션의 다른 테스트(13파일)를 깨뜨린다 | BE pytest 회귀 | 기존 테스트 실패 | W-4 fixture teardown에서 env 원복 후 재reload를 **반드시** 수행한다. 판정은 **저장소 루트에서 `~/.opal/.venv/bin/python -m pytest dashboard/backend/tests/ -q` 전체 실행**으로만 한다(F-3) — 단일 파일 실행이나 system `python3`로 대체하지 않는다. system `python3`에는 fastapi가 없어 수집 자체가 실패하므로 회귀 검출력이 0이다 |

## Release and recovery

- **적용 순서**: P1(W-1 · W-2 · W-3 — 변경 대상 무교집합, 병렬 가능) → P2(W-4 · W-5). 배포·설치는 없다. `~/.opal/`을 직접 편집하지 않으며, T01 범위에서 `install-mac.sh` 재배포도 수행하지 않는다(검증은 전부 소스 트리에서 끝난다).
- **검증 범위**:
  - 결정론: S-1 · S-2 · S-3 · S-4 (정적·in-process)
  - 회귀 (F-3 — cwd·인터프리터가 판정의 일부다. **backend·test-tool pytest는 저장소 루트에서 venv 인터프리터로 전체 실행**한다):

    ```bash
    cd "$(git rev-parse --show-toplevel)"   # F-4: 아래 모든 명령의 cwd 기준점을 저장소 루트로 고정

    # FE — 유일하게 frontend 디렉터리 기준
    cd dashboard/frontend && npm run typecheck                      # exit 0
    npm run build -- --outDir "$TMPDIR/opal-e2e-fe-build-$$/dist" --emptyOutDir   # exit 0, 저장소 dist/ 미생성

    # BE · test-tool — 저장소 루트에서 venv python으로 (S-2 (ii)(iii)의 실행 지점이기도 하다)
    ~/.opal/.venv/bin/python -m pytest dashboard/backend/tests/ -q  # 기존 전건 유지
    ~/.opal/.venv/bin/python -m pytest opal/tools/test-tool/tests/ -q \
        --ignore=opal/tools/test-tool/tests/test_e2e_skeleton.py    # baseline 84 passed 유지
    ```

    - `python3`(system)을 쓰지 않는다 — fastapi·uvicorn·jsonschema가 전부 없어 수집 단계에서 실패하므로 회귀를 **검출할 수 없다**. 인터프리터 근거는 `opal/tools/test-tool/run.sh:4`.
    - `cd opal/tools/test-tool` 후 실행하지 않는다 — `dashboard.backend.*` import가 저장소 루트를 기준으로 해석되어야 한다.
    - **`--ignore=...test_e2e_skeleton.py`는 RED 기간(T3 구현 전) 한정 필수 플래그다**(A-3). 이 파일은 `from lib.e2e import ports as e2e_ports` import-level RED이므로 빼지 않으면 `Interrupted: 1 error during collection`으로 **스위트 전체 수집이 중단되어 84 baseline 측정 자체가 불가능**하다. W-3 구현이 끝나면 이 플래그는 자연 해소되며, T3 이후 최종 게이트는 `--ignore` 없이 실행한다.
  - 실제 연동: S-5 · S-6(real-http) · S-7(real-usage) · S-8(정리·비간섭)
- **실측 경계**: health gate 기본 타임아웃 60s(backend), vite dev ready 타임아웃 90s. 초과 시 `SutStartupError(reason="health_timeout")`으로 종료하고 재시도 루프를 내장하지 않는다(`CONTRACT.md` §B.1.1 [MUST] "1회 실행" 원칙의 선반영).
- **실패 시 복구**: 코드 변경은 전부 소스 트리 내 되돌림(`git checkout -- <경로>` / 신설 4+3파일 삭제)으로 원복된다. 런타임 잔여물은 (a) 프로세스 그룹 — S-8 teardown이 실패해도 `process.terminate_process_group(pgid)`를 소유 pgid로 직접 재호출해 회수한다(이름 패턴 종료 금지), (b) 산출물 — TMPDIR 하위만이므로 삭제로 끝난다. 사용자 `~/.opal`·7823 Console·설치본은 어느 경로에서도 변경되지 않으므로 복구 대상이 아니다.

## BLOCKED

아래 5건은 **설계를 멈출 사유가 아니라 판정이 필요한 불일치**다. 각 항목에 이번 설계가 채택한 해석을 함께 적었으며, CONTRACT.md는 수정하지 않았다. PM/Evaluator가 해석을 기각하면 해당 W와 S만 재작성하면 된다.

**현재 상태**: D-1(판정 대기 — 오너십 `#2 내부 조정`, PM 자율 반영) · D-2(실측 반영 완료) · **D-3(취소 — 무효였음)** · D-4(실측 반영 완료) · D-5(판정 대기). 미해결 판정 대기는 **D-1·D-5 2건**이다.

- **D-1. MV-26의 문자열 범위가 현행 코드와 충돌한다.**
  `CONTRACT.md` MV-26은 "backend CORS 설정에 `"*"`·정규식 패턴이 없고"를 요구한다. 그러나 `dashboard/backend/main.py:86`은 현재 `allow_headers=["*"]`이고, `TRD.md` TD-7은 "등록부(`main.py:81-87`)의 `allow_credentials=False`·`allow_methods=["GET","POST"]`는 유지한다"고만 하여 `allow_headers`를 변경 대상에서 제외한다. MV-26을 문자 그대로 "CORS 설정 전체에 `"*"` 부재"로 읽으면 **어떤 구현으로도 통과할 수 없다**.
  **채택 해석**: MV-26의 `"*"`·정규식 금지는 **origin 축**(`allow_origins`·`allow_origin_regex`)에 한정된다. 근거는 MV-26의 계약 근거로 명시된 `TRD.md` TD-7("허용은 정확한 origin 문자열 추가만")과 `PRD.md` NR-4("서버의 허용 출처는 … 전체 허용을 도입하지 않는다")가 둘 다 origin만 다룬다는 점, 그리고 `CONTRACT.md` §C.8이 보안 경계로 `allow_credentials=False`·`allow_methods` 제한만 꼽고 `allow_headers`를 꼽지 않는다는 점이다. W-4 S-4는 이 범위로 검사한다.

  **오너십 계층: `#2 내부 조정`** — 기계검증절 문구의 **범위 명확화**이며 (a) 외부 노출 표면 변경 0건, (b) 인터페이스·스키마·시그니처 변경 0건, (c) `surfaces.json` 변경 0건, (d) 다른 태스크(T02~T09)의 계약 소비 방식 변경 0건이다. 따라서 상위 승인이 필요한 계약 재설계가 아니라 **PM 자율 반영 대상**이다.
  **권고 문구(PM이 CONTRACT.md에 반영)**: MV-26의 `"*"`·정규식 금지 대상을 **`allow_origins`·`allow_origin_regex`로 한정**한다 — 예: "backend CORS 설정의 `allow_origins`에 `"*"`가 없고 `allow_origin_regex`가 설정되지 않으며, `allow_credentials==False`, `allow_methods==["GET","POST"]`가 유지된다".
  [MUST] 이 PLAN은 `CONTRACT.md`를 직접 수정하지 않는다. 반영 주체는 PM이다.

- **D-2. 디스패치 전제와 실측이 다르다 — `dashboard/backend/tests/`는 빈 디렉터리가 아니다.**
  디스패치 프롬프트는 "현재 `dashboard/backend/tests/`는 빈 디렉터리다"라고 전제했으나, 실측 결과 `__init__.py` + 테스트 13파일(`test_main.py`, `test_routers.py`, `test_brain.py` 등)이 존재한다.
  **영향**: 변경 대상 5번은 "신설 1건"이므로 그대로 성립하지만, 회귀 기준선이 "0건 → 1건"이 아니라 "기존 전건 유지 + 1건 추가"로 바뀐다. 특히 `tests/test_main.py:80-93`이 `dashboard.backend.main.CORS_ORIGINS` 심볼을 직접 읽으므로 **W-2는 이 심볼 이름을 유지해야 한다**(D-4에 반영). H-6도 이 실측에서 파생된 위험이다.

- **D-3. ~~verify_commands의 "기존 84건 회귀 0" 전제가 실측과 다르다.~~ → 취소(무효). 이전 판의 D-3은 인터프리터 선택 오류였다.**
  이전 판은 "baseline 82 passed / 2 failed, 2건은 `jsonschema` 미설치 기인"이라고 적었으나, 그 값은 **system `python3`로 실행했을 때의 값**이다. `opal/tools/test-tool/run.sh:4`가 `VENV_PYTHON="$HOME/.opal/.venv/bin/python"`을 도구 인터프리터로 선언하고 `jsonschema`는 그 venv에만 있다. 올바른 인터프리터로 재측정한 결과는 다음과 같다.

  ```text
  ~/.opal/.venv/bin/python -m pytest opal/tools/test-tool/tests/ -q   (저장소 루트)
  → 84 passed, 100 subtests passed
  ```

  **정정된 결론**: 원래 전제("기존 84건")가 **맞다**. T01 회귀 기준선을 **84 passed**로 확정한다. 실패가 1건이라도 생기면 회귀다. `jsonschema` 설치·의존 선언은 애초에 필요 없었으므로 후속 판단 대상도 아니다. 연동 수정 — §현행 실측표의 baseline 행, §Release and recovery 회귀 게이트 명령, H-6의 판정 기준을 모두 venv 인터프리터 + 저장소 루트 전체 실행으로 고쳤다(F-2·F-3). 이 항목은 미해결 blocker가 아니라 **해소 기록**으로만 남긴다.

- **D-4. TRD TD-6의 typecheck 회귀 근거가 실측과 다르다.**
  TD-6은 "현재 `.d.ts`가 하나도 없어(전수 검색 무결과) `npm run typecheck`가 깨진다. 선언 파일 없이 이 변경만 하면 기존 타입 검사가 회귀한다"고 한다. 그러나 `dashboard/frontend/tsconfig.app.json:7`이 이미 `"types": ["vite/client"]`를 선언하고 있고, `node_modules/vite/types/importMeta.d.ts:14`의 `interface ImportMetaEnv extends Record<string, any>`가 임의 `VITE_*` 키를 `any`로 통과시킨다. 즉 `vite-env.d.ts` 없이도 typecheck는 깨지지 않는다.
  **채택 해석**: `vite-env.d.ts` 신설은 **그대로 유지**한다 — (a) `CONTRACT.md` MV-25가 파일 존재를 독립 요구하고, (b) 선언 병합으로 `any` → `string | undefined` 타입 승격이라는 실질 이득이 있다. 다만 그 근거를 "typecheck 회귀 차단"이 아니라 "MV-25 충족 + 타입 승격"으로 바꿔 기술했고, H-2를 "typecheck는 누락 탐지 수단이 못 된다"는 위험으로 등재했다.

- **D-5. 완료 기준 5의 `surface_ref`가 지정된 `sut-health`로는 성립하지 않는다.**
  디스패치는 "T01이 커버하는 표면은 `sut-health` 1건"이라고 지정했다. 그러나 완료 기준 5는 "**FE 화면에서 발생한** 실제 HTTP 호출 1건"을 요구하는데, FE 루트 화면이 실제로 호출하는 것은 `GET /api/dashboard`다(`dashboard/frontend/src/pages/dashboard/DashboardPage.tsx:1170-1177` 실측). FE는 `/health`를 호출하지 않으므로 S-7의 `surface_ref`를 `sut-health`로 두면 시나리오와 관측 대상이 어긋난다.
  **채택 해석**: S-7의 `surface_ref`를 `surfaces.json`에 이미 등재된 `sut-dashboard`로 둔다. `surfaces.json`은 읽기 전용으로만 소비하며 T01은 이 파일을 수정하지 않으므로 **변경 범위 확장은 아니다**. 커버리지 게이트 집계상 T01이 2개 표면(`sut-health`, `sut-dashboard`)을 관통하는 것으로 기록되는 점만 판정이 필요하다.
