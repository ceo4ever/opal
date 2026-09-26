---
template: sdlc-v2
---
# PLAN: E2E 테스트 환경 설정 체계

> 입력: [TASK.md](TASK.md)

## Approach

프로젝트마다 다른 E2E 실행 환경을 프로젝트 설정 파일 하나(`.opal/e2e/environment.json`)로 선언하게 한다. 이 파일의 검증·해석은 새 모듈 `lib/e2e/environment.py` 한 곳이 맡는다. `test-tool e2e`에는 다음 세 명령을 추가한다.

- `env-inspect`: 읽기 전용 환경 검토
- `env-validate`: 스키마 검증
- `env-check`: 실제 기동으로 준비 상태 검증

`e2e run`의 SUT 기동은 `dashboard` 고정 경로(`opal/tools/test-tool/lib/e2e/runtime.py:105`, `:155`) 대신 이 설정의 서비스 선언을 따르도록 바꾼다. `opal-e2e` 스킬에는 `setup` 모드를 더한다. 이 모드는 검토 → 인터뷰 → 사용자 확인 → 설정 기록 → 준비 검증 순서로 진행한다. 이 저장소의 `dashboard` 기동은 설정 파일로 옮긴다.

변경 전 기준선 두 가지를 확인했다.

- **회귀 테스트 fixture 경로가 이미 깨져 있다.** test-tool 회귀 스위트는 변경 전에도 41 failed·3 errors다. 원인은 태스크 127 폴더를 `tasks/backup/`으로 옮긴 커밋(7e2184c)이다. 테스트는 아직 `tasks/127-…/test-scenario.json`·`surfaces.json`을 fixture로 읽는다(예: `opal/tools/test-tool/tests/test_e2e_runtime.py:29`, `opal/tools/test-tool/tests/test_e2e_sut_http_surfaces.py:76-78`). 임시 링크로 경로만 되살리면 해당 9개 파일이 156 passed가 된다. 따라서 AC-7을 판정하려면 fixture 복구가 먼저다(W-1).
- **기존 여정의 변경 전 판정을 기록했다.** `login-to-dashboard`를 `source-worktree`로 실행한 결과는 `blocked`/exit 19다(`evidence/baseline-login-to-dashboard.json`). SUT 기동과 driver 선택(agent-browser orca-managed)을 거쳤고, 로그인 환경 변수 `OPAL_E2E_LOGIN_ID`가 없어 막혔다(`fragment_value_ref_missing`). AC-5의 "같은 판정"은 이 기록과 비교한다.

데스크톱 앱 실행기, 모바일, 기존 여정·조각 계약 변경, freshness 키 확장은 범위 밖이다(TASK §Affected users and systems 제외 항목).

## Findings

### 직접 변경

- `opal/tools/test-tool/lib/e2e/runtime.py` — `start_backend`(`:87-138`)·`start_frontend`(`:141-194`)가 dashboard 백엔드 모듈과 dashboard 프런트 폴더를 고정한다. 이 둘을 설정 서비스 1건을 띄우는 `start_service`로 대체한다. `_resolve_python`(`:63-75`)의 OPAL venv 탐색도 `{python}` 치환으로 대체한다.
- `opal/tools/test-tool/lib/e2e/orchestrator.py` — 포트 임대 역할이 `backend`·`frontend`로 고정돼 있다(`:85-86`, `:511-515`). 기동 순서는 `_start_sut`(`:1495-1527`)이 고정한다. 브라우저 진입 URL은 `urls["frontend"]`에서만 읽는다(`:1181`). api executor 문맥에는 `backend_url`만 전달한다(`:1351-1379`).
- `opal/tools/test-tool/test_tool.py` — `e2e` 하위 명령은 `run`·`resume`·`status`·`clean`·`driver-verify`·`promote-check`뿐이다(`:346-401`). 라우터는 `cmd_e2e`(`:217-297`), 오류 코드 표는 `:57-82`에 있다.
- `opal/tools/test-tool/lib/e2e/process.py` — lib/e2e에서 OS 분기가 허용되는 유일한 지점이다(`:11`, `:47`). 데스크톱 표면의 호스트 플랫폼 판정도 여기에 둔다.
- `opal/tools/test-tool/lib/e2e/drivers/__init__.py` — 후보 해석(`resolve_candidates`, `:393`)과 등록표(`registered_drivers`, `:305`)는 있다. 연산을 호출하지 않고 설치 여부만 보고하는 표면은 없다.
- `opal/skills/opal-e2e/SKILL.md` — 모드가 `author`·`run`·`status` 셋뿐이다(`:25-27`, frontmatter `pipeline`).
- `opal/core/references/opal-skills-registry.json` — `opal-e2e` 항목의 description·pipeline이 3모드 기준이다(`:754-768`).
- 회귀 fixture 참조 9개 파일: `opal/tools/test-tool/tests/test_e2e_drivers.py`:511, `:621`, `opal/tools/test-tool/tests/test_e2e_human_executor.py`:45, `opal/tools/test-tool/tests/test_e2e_runtime.py`:29, `opal/tools/test-tool/tests/test_e2e_sut_http_surfaces.py`:76-78, `opal/tools/test-tool/tests/test_red_s1_concurrent_port_isolation.py`:30, `opal/tools/test-tool/tests/test_red_s2_stale_lease_reclaim.py`:32, `opal/tools/test-tool/tests/test_red_s3_run_json_shape.py`:28, `opal/tools/test-tool/tests/test_red_s4_no_repo_pollution.py`:29, `opal/tools/test-tool/tests/test_red_s7_redaction.py`:38.
- `opal/tools/test-tool/tests/test_e2e_skeleton.py` — `e2e_runtime.start_backend`를 직접 호출하고(`:94-110`), dashboard 프런트 빌드 산출물 경로를 단언한다(`:89-90`). 런타임 API가 바뀌므로 이 저장소 설정을 읽어 `start_service`로 기동하도록 옮긴다.

### 회귀 확인

- `opal/tools/test-tool/lib/e2e/executors/api.py` — `backend_url`·`base_url`·`health_path` 문맥 키를 읽는다(`:158-159`). 이 모듈은 바꾸지 않고, 오케스트레이터가 같은 키로 api 표면 값을 넘기는지만 확인한다.
- `opal/tools/test-tool/lib/e2e_contract.py` — profile·executor 표(`:57-66`)와 상태·exit 표(`:42-56`)는 C-1에 따라 바꾸지 않는다.
- `opal/tools/test-tool/lib/e2e/freshness.py` — 신선도 키(`compose_key`, `:54`)는 바꾸지 않는다. 재사용 판정이 이전과 같은지 확인한다.
- `opal/tools/test-tool/tests/test_e2e_surface_fidelity.py`, `opal/tools/test-tool/tests/test_e2e_api_executor.py`, `opal/tools/test-tool/tests/test_e2e_status_clean.py`, `opal/tools/test-tool/tests/test_e2e_freshness_key.py`, `opal/tools/test-tool/tests/test_red_s27_no_retry_on_product_failure.py` — 수정 없이 통과해야 하는 기존 회귀 테스트다.
- `docs/e2e/journeys/login-to-dashboard.md` — 변경 전 판정(`blocked`/`fragment_value_ref_missing`)과 같은 판정이 나와야 하는 기존 여정이다.

### 문서 갱신

- `opal/tools/test-tool/README.md` — `e2e run` 절(`:160-192`)의 SUT 기동 설명을 바꾸고, 세 명령 절과 오류 코드 표(`:471` 이하) 항목을 더한다.
- `docs/PROJECT.md` — `test-tool e2e` 행(`:181`)의 서브명령 목록과 설정 기반 기동 사실을 갱신한다.
- 프로젝트 E2E 설정 안내 문서(.opal/e2e/README.md, W-2 변경 대상) — 환경 설정 파일의 위치·역할 한 단락을 더한다.
- `opal/skills/opal-e2e/references/setup.md` — 신규 문서. 인터뷰 항목과 사용자 확인 체크리스트를 담는다.

### 미확인 가정

- H-1, H-2 참조.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| D-1. 설정 파일 위치·형식 | 프로젝트 루트의 `.opal/e2e/environment.json`(UTF-8 JSON). 대상 트리는 `e2e run`의 `project_root`(`opal/tools/test-tool/lib/e2e/target.py` `resolve_target`)를 그대로 쓴다. `source-worktree`는 작업본 쪽 파일을 읽는다 | `.opal/e2e/README.md`가 이미 프로젝트 E2E 추적 설정 위치로 정의돼 있고 `order.json`도 여기 있다 |
| D-2. 스키마 원본 | 최상위 키 `schema_version`("1.0")·`services`·`surfaces`·`secrets`·`data`·`external_integrations`. 모르는 키는 `unknown_field`로 거부한다. 필드 표와 검증은 `lib/e2e/environment.py` 한 곳에 두고, README는 표를 복제하지 않고 이 모듈을 가리킨다 | jsonschema는 설치 의존성으로 선언돼 있지 않다. 기존 계약 모듈(`opal/tools/test-tool/lib/e2e_contract.py`)도 순수 Python으로 검증한다 |
| D-3. 서비스 선언 | `services[]`: `id`(필수, `^[a-z][a-z0-9-]*$`), `command`(필수, 문자열 배열), `cwd`(기본 `.`, 프로젝트 루트 밖이면 `path_escape`), `env`(값은 문자열 또는 `{"from_env": NAME}`), `depends_on`(서비스 id 배열, 순환이면 `dependency_cycle`), `health`(선택. `{"type":"http","path":..., "expect_status":200, "json_field":선택}` 또는 `{"type":"port"}`. 생략하면 `{"type":"port"}`로 보고 포트 오픈만 기다린다. 어느 경우든 health를 통과해야 기동 완료다), `startup_timeout_s`(기본 60). 치환 토큰은 `{host}`·`{port}`·`{python}`(test-tool 인터프리터)·`{project_root}`·`{service.<id>.url}`·`{service.<id>.port}`만 허용하고, 그 밖의 토큰은 `invalid_placeholder`로 거부한다 | 현재 기동 계약(strict-port, http health의 `status` 필드, frontend 포트 오픈 대기, frontend→backend URL 주입)을 설정으로 표현하려면 필요한 최소 표면이다 |
| D-4. 표면 선언 | `surfaces[]`: `id`, `kind` ∈ {`web`,`api`,`macos-app`,`windows-app`,`linux-app`,`human`}. `web`·`api`는 `service`(로컬 기동) 또는 `url`(기존 URL) 중 정확히 하나를 가진다. `web`은 선택 `path`(기본 `/`), `api`는 선택 `health_path`(기본 `/health`)를 가진다. 데스크톱 3종은 `app`(`path` 또는 `launch` 명령 중 하나 이상)을 가진다. 혼합은 여러 표면을 함께 선언해 표현한다 | AC-1이 요구하는 7개 표면을 한 형식으로 덮는다 |
| D-5. 비밀값 | `secrets[]`는 `name`(`^[A-Z_][A-Z0-9_]*$`)과 `purpose`만 가진다. `value` 키가 있으면 `secret_literal`로 거부한다. `env`에서 키 이름이 비밀 계열(`PASS`·`SECRET`·`TOKEN`·`API_KEY`·`CREDENTIAL`·`PRIVATE_KEY`, 대소문자 무시)이면 값은 `{"from_env": NAME}`만 허용한다. 모든 문자열 값은 `lib/e2e/redaction.py`의 `redact_text`에 통과시켜, 마스킹이 일어나면 `secret_literal`로 거부한다 | C-3. 마스킹 규칙은 기존 증적 관문과 한 원본을 쓴다 |
| D-6. 검증 오류 계약 | `env-validate [--project-root P] [--file F]`: 유효하면 exit 0, `{"ok":true,"path":...,"summary":{services,surfaces}}`. 파일이 없으면 exit 1, `error:"e2e_env_config_missing"`. 무효면 exit 1, `error:"e2e_env_config_invalid"`, `violations:[{path,code,detail}]`. `code` 목록: `required_field_missing`, `unknown_field`, `invalid_type`, `invalid_kind`, `duplicate_id`, `unknown_service_ref`, `surface_target_conflict`, `dependency_cycle`, `invalid_placeholder`, `path_escape`, `secret_literal` | AC-1의 구조화 오류 코드 |
| D-7. 환경 검토 | `env-inspect [--project-root P]`: 파일을 쓰지 않는다. 결과는 `{"ok":true,"config":{present,path,valid}, "surface_candidates":[{kind, evidence:[경로], suggested:{command,cwd,health}}], "drivers":[{driver,session_mode,installed,binary}], "secret_hints":[이름]}`. 탐지 근거는 `package.json` scripts·의존성(vite/next/electron/tauri)과 Python 의존성·코드의 FastAPI/Flask 앱 선언, `/health` 문자열, `*.xcodeproj`·`Package.swift`·`*.csproj`·`*.desktop`, 그리고 `.env.example`의 변수 이름(값은 읽지 않음)이다. driver는 binary 탐색과 `--version`까지만 하고 세션 연산은 호출하지 않는다 | AC-2, C-6 |
| D-8. 준비 검증 | `env-check [--project-root P] [--artifact-root R]`: 설정을 먼저 검증한다. 무효·부재면 `env-validate`와 같은 오류와 exit 1로 끝낸다. 결과는 `{"ok":true,"ready":bool,"secrets":[{name,ok,remediation}],"surfaces":[{id,kind,status,checks:[{name,ok,detail}],cause,remediation}]}`이다. `status`는 ready 또는 not_ready이고, ready 표면의 `cause`·`remediation`은 null이다. **비밀값**: `secrets[]`는 프로젝트 전체 항목이라 표면 판정에 섞지 않는다. 최상위 `secrets` 배열에 이름별 `ok`(환경 변수 존재 여부, 값은 출력하지 않음)를 남긴다. 누락 항목의 `remediation`에는 `export <NAME>=...` 안내를 쓴다. 표면 `cause`에는 비밀 누락을 넣지 않는다. **ready 집계**: `ready`는 모든 표면이 ready이고 모든 비밀이 ok일 때만 true다. true면 exit 0, 아니면 exit 1이다. **표면별 check 순서와 cause**: 처음 실패한 check의 코드가 `cause`가 되고, 뒤 check는 수행하지 않은 것으로 `ok:false, detail:"skipped"`를 남긴다. (1) `web`·`api` + `service`: 서비스 기동(프로세스 조기 종료·spawn 실패 → `service_start_failed`, 의존 서비스가 실패하면 기동하지 않고 `dependency_failed`) → health(시간 초과 `health_timeout`, http 상태 불일치·`json_field` 부재 `health_bad_response`) → 실행기(`web`은 브라우저 driver 후보 해석에서 selected 0이면 `driver_unavailable`, `api`는 표면 URL+`health_path`로 한 api executor probe 실패면 `api_executor_unavailable`). 모든 서비스는 판정 뒤 회수한다. (2) `web`·`api` + `url`: 도달(연결 실패·타임아웃 → `url_unreachable`) → 응답 기준(`web`은 `url`+`path` GET 상태가 500 미만이면 통과, `api`는 `url`+`health_path` GET이 200이어야 통과하고 아니면 `health_bad_response`) → 실행기(위와 같은 코드). (3) `human`: human executor 등록 확인(없으면 `human_executor_unavailable`). (4) 데스크톱 3종: 항상 `not_ready`이며 checks에 호스트 플랫폼 일치·앱 존재·실행기 확인 3항목을 모두 남긴다(앞 항목이 실패해도 뒤 항목을 skipped로 기록). `cause`는 처음 실패한 항목 순서(`platform_mismatch` → `app_not_found` → `desktop_executor_absent`)로 정하며, 실행기가 없으므로 실행기 항목은 언제나 실패한다. 각 cause의 `remediation`은 사람이 읽을 조치 한 문장이다. 기동 로그는 `<artifact-root>/readiness/<run>/<service-id>.log`에 남기고 `detail`에 그 경로를 쓴다. cause 코드 집합은 위 11종(`service_start_failed`·`dependency_failed`·`health_timeout`·`health_bad_response`·`driver_unavailable`·`api_executor_unavailable`·`url_unreachable`·`human_executor_unavailable`·`platform_mismatch`·`app_not_found`·`desktop_executor_absent`)으로 닫힌다 | AC-4, C-2. 설정 파일 존재나 진술만으로 ready를 주지 않는다. 비밀은 표면에 속하지 않으므로 별도 배열로 두면 표면 cause가 서로 충돌하지 않는다 |
| D-9. run 통합 | 설정이 유효하면 포트 임대 역할은 선언된 서비스 id(의존 순서)다. SUT 기동 때는 선언된 서비스를 전부 의존 순서로 띄운다(현재처럼 profile과 무관하게 전체 기동). `run.json.urls`는 서비스 id → URL이다. 브라우저 진입 URL은 `web` 표면 URL+`path`, api executor 문맥의 `backend_url`·`health_path`는 `api` 표면 값이다. 같은 종류의 표면이 둘 이상이면 시나리오 `surface_ref`의 첫 `.` 앞 조각과 id가 같은 표면을 고르고, 못 고르면 `blocked`/`e2e_env_surface_ambiguous`로 끝낸다. 필요한 종류의 표면이 없으면 `blocked`/`e2e_env_surface_missing`이다 | AC-5. 이 저장소 설정의 서비스 id를 `backend`·`frontend`로 두면 `run.json` 모양이 그대로다 |
| D-10. 설정 부재 호환 경로 | 설정 파일이 없거나 무효여도 run은 기존처럼 `backend`·`frontend` 두 역할의 포트를 임대하고, SUT 기동 전 단계(정적 거부·후보 게이트·신선도 재사용)도 그대로 진행한다. SUT 기동 시점에 도달하면 서비스를 띄우지 않고 `blocked`로 끝낸다. `detail_code`는 `e2e_env_config_missing` 또는 `e2e_env_config_invalid`이고, detail에 `test-tool e2e env-inspect`·`//e2e setup` 안내를 포함한다. test-tool 코드에 `dashboard` 경로 문자열은 남기지 않는다 | AC-6, C-5. 설정 없는 임시 트리 회귀 테스트가 임대 2건과 `urls` 키를 단언한다(`opal/tools/test-tool/tests/test_e2e_runtime.py:280-330`). 다른 프로젝트는 원래도 `dashboard` 모듈이 없어 `infra_error`였으므로, 원인을 알려 주는 `blocked`가 개선이다 |
| D-11. 오류 코드 등록 | `test_tool.py` `ERROR_CODES`에 `e2e_env_config_missing`, `e2e_env_config_invalid`, `e2e_env_surface_missing`, `e2e_env_surface_ambiguous`를 더한다. 최종 status·exit 매핑은 `e2e_contract`를 쓰고 새 값을 만들지 않는다 | C-1 |
| D-12. 스킬 setup 모드 | `//e2e setup`: ① `env-inspect` 결과 제시 → ①-1 폴백: 후보가 없거나 부족한 표면에 한해 `docs/PROJECT.md`가 있으면 "프로젝트 구성"(요소·경로·기술 스택)과 관련 문서에서 기동 방법·표면을 추정하고 결과에 "추정"과 근거 위치를 표시한다(PROJECT.md가 없으면 건너뛴다. 추정은 test-tool이 아니라 스킬 층의 해석이다) → ② 탐지·추정으로 확정할 수 없는 항목과 모든 추정값을 질문으로 확정한다(대상 표면, 로컬 기동 또는 기존 URL, 계정·비밀 환경 변수 이름, 데이터 준비·복원, 외부 연동 정책) → ③ 초안을 태스크 `e2e/` 또는 `.e2e/scratch/`에 두고 `env-validate --file`로 검증한 뒤 사용자 확인 게이트를 연다 → ④ 확인 후에만 `.opal/e2e/environment.json`에 기록한다 → ⑤ `env-check` 결과의 ready·not_ready·조치를 그대로 보고한다. `author`는 준비된 환경을 전제로 하며, 준비되지 않았으면 `setup`을 안내한다. 추정값은 사용자 확인 전에는 설정 파일에 쓰지 않고, 확인된 추정값도 `env-check` 실제 기동으로만 ready가 된다 | AC-3, C-1, C-2, C-6. PROJECT.md 폴백은 캡틴 지시로 EXECUTE 중 추가(설계 게이트 통과 뒤 계약 보강, AGENTIC-LOG 기록). `env-inspect`는 파일 구조만 보는 결정론 도구로 유지한다 |
| D-13. 회귀 fixture 고정 | 태스크 127의 `test-scenario.json`·`surfaces.json`을 `opal/tools/test-tool/tests/fixtures/e2e-harness/`로 복사하고, 9개 테스트의 경로 상수를 이 폴더로 바꾼다. 테스트 본문의 단언은 바꾸지 않는다 | AC-7. 태스크 폴더 이동과 회귀 스위트를 분리한다 |
| D-14. 배포 | 소스 검증을 worktree에서 끝내고, install 재배포는 main merge 뒤 사용자 승인으로 한다 | 병합 전에 설치본을 바꾸면, 설정 파일이 없는 main 체크아웃의 E2E가 `blocked`로 바뀌어 다른 세션에 영향을 준다(`.opal/AGENT.md` 배포 경계) |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. 회귀 fixture 고정 | opal-task-agent | `opal/tools/test-tool/tests/fixtures/e2e-harness/test-scenario.json`, `opal/tools/test-tool/tests/fixtures/e2e-harness/surfaces.json`, `opal/tools/test-tool/tests/test_e2e_drivers.py`, `opal/tools/test-tool/tests/test_e2e_human_executor.py`, `opal/tools/test-tool/tests/test_e2e_runtime.py`, `opal/tools/test-tool/tests/test_e2e_sut_http_surfaces.py`, `opal/tools/test-tool/tests/test_red_s1_concurrent_port_isolation.py`, `opal/tools/test-tool/tests/test_red_s2_stale_lease_reclaim.py`, `opal/tools/test-tool/tests/test_red_s3_run_json_shape.py`, `opal/tools/test-tool/tests/test_red_s4_no_repo_pollution.py`, `opal/tools/test-tool/tests/test_red_s7_redaction.py` | D-13. `tasks/backup/127-260912-oppl-E2E-하네스-구현/`의 두 파일을 원문 그대로 복사하고, 각 테스트의 fixture 경로 상수(`_TASK_PATH`·`task_path`·`_TASK_DIRS`)만 fixtures 폴더로 바꾼다. 단언·로직은 바꾸지 않는다 | 없음 | P1 | AC-7, C-5 |
| W-2. 환경 설정 모듈과 설정 기반 기동 | opal-task-agent | `opal/tools/test-tool/lib/e2e/environment.py`, `opal/tools/test-tool/lib/e2e/runtime.py`, `opal/tools/test-tool/lib/e2e/process.py`, `opal/tools/test-tool/tests/test_e2e_skeleton.py`, `opal/tools/test-tool/tests/test_e2e_environment.py`, `.opal/e2e/environment.json`, `.opal/e2e/README.md` | D-1~D-6. `environment.py` 공개 함수: `load(project_root, file=None)`(결과 `{status: ok/missing/invalid, config, violations, path}`), `validate(dict)`, `service_order(config)`, `render_service(service, *, port, host, ports_by_id, project_root)`(argv·cwd·env 확정, `from_env` 해석), `select_surface(config, kind, surface_ref)`. `runtime.py`는 `start_backend`·`start_frontend`·`_resolve_python`을 없애고 `start_service(rendered, *, role, port, artifact_dir)`로 대체한다. health는 `wait_http_health(url, path, expect_status, json_field, timeout_s)`와 기존 포트 대기로 나눈다. `SutStartupError` reason 코드와 `stop_all`은 그대로 둔다. `process.py`에 `host_platform()`(`macos`·`windows`·`linux` 중 하나)을 더한다. `.opal/e2e/environment.json`은 현재 기동을 그대로 옮긴다: `backend` = `{python} -m uvicorn dashboard.backend.main:app --host {host} --port {port}`, health http `/health`+`json_field:"status"`. `frontend` = `npm run dev -- --host {host} --port {port} --strictPort`, cwd `dashboard/frontend`, env `VITE_API_BASE_URL={service.backend.url}`, `depends_on:[backend]`, health port, timeout 90. 표면은 `console`(web→frontend)과 `console-api`(api→backend). `test_e2e_skeleton.py`는 이 설정을 읽어 `start_service`로 기동하게 바꾼다. `test_e2e_environment.py`에는 모듈 단위 검증(유효 7종 표면, 위반 코드별 거부, 치환, 의존 순서)을 둔다 | 없음 | P1 | AC-1, AC-6, C-3, C-4 |
| W-3. run의 설정 기반 SUT 기동 | opal-task-agent | `opal/tools/test-tool/lib/e2e/orchestrator.py`, `opal/tools/test-tool/tests/test_e2e_run_environment.py` | D-9·D-10. 대상 해석 직후 `environment.load(project_root)`를 호출한다. 포트 임대 역할은 유효 설정이면 `service_order` 결과, 아니면 `backend`·`frontend`로 정한다. `_start_sut`은 설정 서비스를 의존 순서로 `render_service`→`start_service`→health→`confirm_lease` 한다. 설정이 부재·무효면 기동하지 않고 `blocked`+D-10 detail_code로 끝낸다. 표면 선택 실패는 D-9 코드로 끝낸다. `_urls`는 임대 역할별 URL을 만든다. 브라우저 진입 URL(`_open_browser`)은 선택된 `web` 표면 URL로, `_executor_runtime_context`는 api 표면의 `backend_url`·`health_path`를 싣는다. `url` 표면은 임대·기동 없이 그 URL을 쓴다. `dashboard` 문자열은 남기지 않는다. 신규 테스트는 설정 부재·무효·표면 없음·모호·임시 프로젝트 서비스 기동의 5경로를 둔다 | W-2 | P2 | AC-5, AC-6, C-1, C-4, C-5 |
| W-4. env 명령 3종과 CLI | opal-task-agent | `opal/tools/test-tool/test_tool.py`, `opal/tools/test-tool/lib/e2e/inspect.py`, `opal/tools/test-tool/lib/e2e/readiness.py`, `opal/tools/test-tool/lib/e2e/drivers/__init__.py`, `opal/tools/test-tool/tests/test_e2e_env_commands.py` | D-6~D-8·D-11. `test_tool.py`에 `env-inspect`·`env-validate`·`env-check` 파서와 라우팅을 더하고, `ERROR_CODES`에 D-11의 4종을 등록한다. `inspect.py`는 D-7 탐지를 한다(쓰기 없음). `readiness.py`는 D-8 판정을 한다. 임대·기동·회수는 `ports`·`runtime`·`environment`를 재사용하고, 실행기 확인은 `drivers.resolve_candidates`와 `executors` 레지스트리를 재사용한다. `drivers/__init__.py`에 `discover_installed(project_root)`(후보 순서별 binary 존재·경로, 세션 연산 미호출)를 더한다. 신규 테스트는 검토 무변경(트리 해시 동일), 검증 exit·오류 코드, 준비 검증의 ready·not_ready·데스크톱 `desktop_executor_absent`·비밀 누락을 다룬다 | W-2 | P2 | AC-1, AC-2, AC-4, C-1, C-2, C-3, C-6 |
| W-5. 스킬 setup 모드와 문서 | opal-task-agent | `opal/skills/opal-e2e/SKILL.md`, `opal/skills/opal-e2e/references/setup.md`, `opal/core/references/opal-skills-registry.json`, `opal/tools/test-tool/README.md`, `docs/PROJECT.md` | D-12. SKILL 모드 라우팅 표·frontmatter `pipeline`·description에 `setup`을 더하고 `## setup` 절을 쓴다. `author` 절에는 준비 환경 전제를 한 줄 넣는다. `setup` 절과 `setup.md`에 PROJECT.md 폴백 단계(①-1)를 적는다. `setup.md`에는 인터뷰 항목, PROJECT.md 추정 규칙(읽을 절·추정 표시·근거 위치), 확인 체크리스트를 두고, 스키마 필드는 `environment.py`를 가리킨다. 레지스트리 항목의 description·pipeline을 SKILL과 맞춘다. README에는 세 명령 절, `e2e run` 설정 기반 기동 설명, 오류 코드 4종, 재배포는 main merge 뒤 install로 한다는 배포 경계(D-14)를 더한다. `docs/PROJECT.md` `test-tool e2e` 행을 갱신한다. 이 작업과 전 Work item은 `~/.opal/`을 수정하거나 install을 실행하지 않는다 | W-3, W-4 | P3 | AC-3, C-1, C-6, C-7 |
| W-6. 저장소 밖 프로젝트 관통 테스트 | opal-task-agent | `opal/tools/test-tool/tests/test_e2e_external_project.py` | AC-8 자동화. OS 임시 폴더에 표준 라이브러리 API 서버 1개(`/health` JSON)와 `test-scenario.json`(api profile 1건)을 만든다. 이어서 CLI subprocess로 `env-inspect`(무변경) → 설정 작성 → `env-validate` → `env-check`(ready) → `e2e run --target source-worktree --worktree-root <temp>`(pass)를 관통하고, 각 단계의 stdout JSON과 exit을 단언한다 | W-3, W-4 | P3 | AC-8, AC-5 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. `{python}`을 test-tool 인터프리터(`sys.executable`)로 치환하면, 격리 `HOME`에서도 이 저장소 backend 의존성(fastapi·uvicorn)이 있는 interpreter를 가리킨다 | 기존 `_resolve_python`은 `~/.opal/.venv`를 먼저 찾았다(`opal/tools/test-tool/lib/e2e/runtime.py:63-75`). `test_e2e_sut_http_surfaces.py`는 `HOME`을 격리해 subprocess로 run을 띄운다 | 틀리면 dashboard backend가 `process_exited_early`로 떠서 16개 http 표면 회귀와 AC-5가 깨진다 | W-2 치환 규칙. TEST에서 http 표면 스위트와 `run.sh` 경유 실행을 함께 확인한다 |
| H-2. 설정 서비스 env의 `{service.backend.url}` 치환이 기존 `VITE_API_BASE_URL` 주입(`opal/tools/test-tool/lib/e2e/runtime.py:169-171`)과 같은 결과를 낸다 | frontend→backend 호출 경로(CORS 포함)와 브라우저 real-usage 관통 | 틀리면 브라우저 회귀(`test_e2e_skeleton.py`·`test_e2e_surface_fidelity.py`)와 기존 여정 판정이 바뀐다 | W-2·W-3. TEST에서 브라우저 관통 테스트와 기준선 여정 재실행 판정을 비교한다 |

## Release and recovery

- RED 단계: EXECUTE 진입 직후 PM이 `test-tool scenario-init`으로 TEST-SCENARIO의 `구현 전 RED` 행(S-1~S-7)을 `red_required`로 등록한다. 이어 `opal-test-agent`(red mode)가 `opal/tools/test-tool/tests/test_red_s159_env.py`를 작성하고 실패를 `scenario-red`로 기록한 뒤 `scenario-lock`을 통과한다. 그 후에만 W 구현 디스패치를 시작한다. 이 파일은 구현 워커의 변경 대상이 아니며, 구현 워커는 이 파일을 수정하지 않는다(`harness/red-first.md` §1.5).
- 적용 순서: P1(W-1·W-2 병렬, 파일 겹침 없음) → P2(W-3·W-4 병렬, 파일 겹침 없음, 오류 코드 이름은 D-11로 고정) → P3(W-5·W-6 병렬).
- 검증 범위: 결정론 단위 테스트는 `environment`·`inspect`·`readiness`와 오류 코드를 다룬다. 회귀는 test-tool 전체 스위트(변경 전 fixture 복구 기준 전건 통과)다. 실제 연동은 이 저장소 dashboard의 설정 기반 기동(http 표면 16건·브라우저 관통)과 기준선 여정 재실행, 저장소 밖 임시 프로젝트 관통(W-6 자동 테스트와 TEST 단계 CLI 수동 관통 증적)이다.
- 실측 경계: 기존 기동 타임아웃을 유지한다(backend health 60초, frontend 포트 90초).
- 설치: 소스 경로(`~/.opal/.venv/bin/python opal/tools/test-tool/test_tool.py`)로 검증을 끝낸다. `./scripts/install-mac.sh` 재배포는 main merge 뒤 사용자 승인으로 수행하고, 재배포 뒤 `~/.opal/tools/test-tool/run.sh e2e env-validate --project-root <repo>`가 exit 0인지 확인한다(D-14).
- 실패 시: 병합 전에는 브랜치 커밋을 되돌린다. 병합·재배포 뒤 문제가 생기면 이전 커밋으로 되돌리고 install을 다시 실행한다. 설정 파일은 추적 파일이므로 git으로 복구한다.
