# DONE: E2E 테스트 환경 설정 체계

## 결과

프로젝트마다 다른 E2E 실행 환경을 프로젝트 설정 파일 `.opal/e2e/environment.json` 하나로 선언하고 검증한다. 이 파일은 서비스 기동 명령·작업 폴더·health, 표면(web·api·macOS/Windows/Linux 앱·사람 참여와 그 혼합), 비밀값 환경 변수 이름, 데이터·외부 연동 정책을 담는다. 검증·해석은 `opal/tools/test-tool/lib/e2e/environment.py` 한 곳이 맡는다.

- **환경 검토·검증·준비 검증 명령**: `test-tool e2e`에 세 명령을 더했다.
  - `env-inspect`: 읽기 전용이다. 표면 후보, 기동 방법 후보, 설치된 driver, 비밀 이름을 보고한다.
  - `env-validate`: 구조화 위반 코드 11종으로 판정한다. 비밀 원문은 `secret_literal`로 거부한다.
  - `env-check`: 실제 기동·health·실행기 확인으로 표면별 ready·not_ready를 판정하고, 원인 11종과 조치를 붙인다. 비밀은 최상위 `secrets`로 따로 집계한다. 데스크톱 표면은 "실행기 없음"(`desktop_executor_absent`)을 명시하며 성공으로 가장하지 않는다.
- **run의 설정 기반 기동**: `e2e run`은 대상 트리의 설정으로 서비스를 의존 순서대로 한 번씩 띄운다. 브라우저 진입 URL과 api executor의 base URL·health 경로를 선택된 표면에서 가져온다. `url` 표면은 포트 임대·기동 없이 그 URL을 쓴다.
  - 설정 부재·무효·표면 선택 실패는 서비스를 띄우지 않고 `blocked`로 끝낸다(`e2e_env_config_missing`·`e2e_env_config_invalid`·`e2e_env_surface_missing`·`e2e_env_surface_ambiguous`). 안내 문구에는 `env-inspect`·`//e2e setup`을 싣는다.
  - test-tool 코드에서 `dashboard` 고정 기동 경로는 없어졌다. 이 저장소의 dashboard 기동은 설정 파일로 옮겼다.
- **`opal-e2e` setup 모드**: `//e2e setup`은 다음 순서로 진행한다.
  1. `env-inspect` 검토
  2. 후보가 부족한 표면에 한해 `docs/PROJECT.md` "프로젝트 구성"으로 환경 추정("추정"·근거 위치 표시, 캡틴 지시로 추가)
  3. 인터뷰로 확정
  4. `env-validate --file` 후 사용자 확인
  5. 확인 뒤에만 설정 기록
  6. `env-check` 결과를 그대로 보고
- **유지한 것**: 실행 판정·exit의 소유자는 계속 test-tool이다. 다음도 바뀌지 않았다.
  - run stdout 14키, 후보 순서·전환 조건, 신선도 키
  - 기존 `author`·`run`·`status` 모드
  - 설정이 없는 트리에서의 포트 임대 모양(`backend`·`frontend`)과 기동 전 판정(정적 거부·후보 게이트·신선도 재사용)
- **회귀 fixture 고정**: 태스크 127 backup 이동(7e2184c)으로 끊겼던 test-tool 회귀 테스트 9개의 fixture를 `opal/tools/test-tool/tests/fixtures/e2e-harness/`로 옮겼다.
- **배포**: 설치본(`~/.opal`)은 재배포하지 않았다. 재배포는 main merge 뒤 수행한다(아래 참고).

## 변경 파일

- `.opal/e2e/environment.json` (신규)
- `.opal/e2e/README.md`
- `opal/tools/test-tool/lib/e2e/environment.py` (신규)
- `opal/tools/test-tool/lib/e2e/inspect.py` (신규)
- `opal/tools/test-tool/lib/e2e/readiness.py` (신규)
- `opal/tools/test-tool/lib/e2e/runtime.py`
- `opal/tools/test-tool/lib/e2e/orchestrator.py`
- `opal/tools/test-tool/lib/e2e/process.py`
- `opal/tools/test-tool/lib/e2e/drivers/__init__.py`
- `opal/tools/test-tool/test_tool.py`
- `opal/tools/test-tool/README.md`
- `opal/tools/test-tool/tests/fixtures/e2e-harness/test-scenario.json` (신규)
- `opal/tools/test-tool/tests/fixtures/e2e-harness/surfaces.json` (신규)
- `opal/tools/test-tool/tests/test_e2e_environment.py` (신규)
- `opal/tools/test-tool/tests/test_e2e_run_environment.py` (신규)
- `opal/tools/test-tool/tests/test_e2e_env_commands.py` (신규)
- `opal/tools/test-tool/tests/test_e2e_external_project.py` (신규)
- `opal/tools/test-tool/tests/test_red_s159_env.py` (신규)
- `opal/tools/test-tool/tests/test_e2e_skeleton.py`
- `opal/tools/test-tool/tests/test_e2e_drivers.py`, `test_e2e_human_executor.py`, `test_e2e_runtime.py`, `test_e2e_sut_http_surfaces.py`, `test_red_s1_concurrent_port_isolation.py`, `test_red_s2_stale_lease_reclaim.py`, `test_red_s3_run_json_shape.py`, `test_red_s4_no_repo_pollution.py`, `test_red_s7_redaction.py` (fixture 경로 상수만 변경)
- `opal/skills/opal-e2e/SKILL.md`
- `opal/skills/opal-e2e/references/setup.md` (신규)
- `opal/core/references/opal-skills-registry.json`
- `docs/PROJECT.md`

## 검증

- test-tool 전체 회귀: `~/.opal/.venv/bin/python -m pytest opal/tools/test-tool/tests -q` → 547 passed, 0 failed. 변경 전 기준선은 fixture 경로 부재로 41 failed·3 errors였다.
- 설계 게이트 3회차에서 pass했다(독립 `opal-evaluator-agent`, 설계 4축 PASS·시나리오 3축 2/2/2).
- RED-first: S-1~S-7을 구현 전에 실패로 확인하고 기록·잠금한 뒤 구현했다. `test_red_s159_env.py`는 16 passed다.
- TEST(독립 `opal-test-agent`): `test-scenario.json` 13/13 pass. 증거는 `evidence/` 아래에 있다.
  - 기존 여정 `login-to-dashboard`의 변경 전후 판정이 같다(`blocked`/19/`fragment_value_ref_missing`/agent-browser orca-managed/urls `backend`·`frontend`). 증거는 `evidence/baseline-*`·`evidence/after-*`다.
  - 저장소 밖 FastAPI 표본에서 env-inspect 제안 명령을 그대로 써서 validate→check ready→run pass(real-http)까지 갔다. url 기반 web 표면은 임대·기동 없이 ready였다. 증거는 `evidence/external-project/`다.
- 설치본 미변경: `~/.opal/tools/test-tool/lib/e2e/environment.py` 부재를 확인했다.
- PM Gate 보안·컨벤션 진단: {GC_RESULT}

## 회고적 학습 후보

.opal/brain/pages/concept/e2e-environment-config-ownership.md

## 참고

- **재배포(사용자 승인 필요)**: main merge 뒤 `./scripts/install-mac.sh`로 재배포하고 `~/.opal/tools/test-tool/run.sh e2e env-validate --project-root <repo>`가 exit 0인지 확인한다. 병합 전에 재배포하면 설정 파일이 없는 main 체크아웃의 E2E가 `blocked`로 바뀐다.
- 후속 후보:
  - 서비스를 띄우지 않은 run의 안내 로그 경로가 `lib/e2e/evidence.py` `EVIDENCE_PATHS["server_log"]`의 `server/backend.log`로 고정돼 있다. 실제 서비스 로그는 `server/<서비스id>.log`다.
  - `drivers.discover_installed`는 생성자가 binary 경로를 노출하지 않는 driver(ego-lite)를 `installed:false`로 보고한다.
  - 데스크톱 앱 실행기(드라이버) 구현은 TASK 범위 밖이다.
