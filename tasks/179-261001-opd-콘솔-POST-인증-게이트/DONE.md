# DONE: OPAL Console 상태 변경 API 인증 게이트와 구형 Brain 실행 차단 (Gateway 제안 Phase 0)

## 결과

- Console backend 앞단의 단일 ASGI 미들웨어가 `/api/` 하위 전체를 default-deny로 막는다. 검사 순서는 Host → Origin → 세션 → CSRF이며 예외는 `POST /api/auth/exchange`·`GET /api/auth/session` 2종뿐이다. WebSocket handshake도 같은 지점에서 accept 전에 close 1008로 거절한다. 거절된 요청은 핸들러에 진입하지 않아 LLM 실행·설정 쓰기가 0회다.
- `opal-cli console open`은 `OPAL_HOME/run/console-entry/`(0700)에 해시명 0600 파일로 1회성 진입 token을 발급하고 URL fragment(`#entry=`)로만 전달한다. 브라우저는 교환 전에 fragment를 주소창에서 지운 뒤 세션 쿠키(`HttpOnly; SameSite=Strict`, 12시간)와 메모리 보관 CSRF를 받는다. 세션이 없으면 데이터 없는 잠금 화면과 재진입 안내만 보인다. `/health`에 `auth` 마커를 추가해 인증 게이트가 없는 구버전 데몬에는 `open`이 열지 않고 재기동을 안내한다.
- 구형 `claude -p` Brain은 서버 측 정책(`console.config.json`의 `legacy_brain_enabled`, JSON `true`만 켜짐)이 기본 꺼짐으로 결정한다. 게이트는 HTTP 라우터가 아니라 Registry 진입점(prime·prewarm·submit·ask·풀 리필)과 spawn 직전(`Popen` 시작 구간 락)에 있고, 끄기 요청이 반환된 뒤에는 새 프로세스가 0회이며 이미 시작된 turn은 끝까지 진행한다(화면에 진행 중 turn 수 표시). 기동 선프라임도 꺼짐이면 스레드를 만들지 않는다.
- Brain 첫 진입 화면은 새 Brain 출시 전까지 기본적으로 사용할 수 없다는 사실과 업그레이드 안내, 위험 3종(파일 읽기 범위 비제한·임의 Bash·네트워크 유출) 확인 후 켜는 선택지를 함께 보인다. 켜면 `legacy` 배지가 붙는다.
- test-tool 환경 선언에 선택 키 `session_bootstrap`을 추가해 격리 HOME·자체 포트의 SUT가 같은 진입 token 교환으로 인증된 상태가 된다. 증적에서 `x-csrf-token`·`#entry=`·`csrf_token` 등이 마스킹된다.
- 유지한 것: 127.0.0.1 바인딩과 새 소켓 없음(C-1), 기존 Brain 어댑터 호출 계약(`shell=False`·`cwd`·`--allowedTools`·JSON 파싱), 키 없는 기존 E2E 환경 파일의 동작, `routers/config.py`와 읽기 라우터 6종의 코드.

## 변경 파일

- 백엔드: `dashboard/backend/auth.py`, `dashboard/backend/entry_token.py`, `dashboard/backend/routers/auth.py`, `dashboard/backend/adapters/brain_policy.py`(이상 신규), `dashboard/backend/main.py`, `dashboard/backend/models.py`, `dashboard/backend/config.py`, `dashboard/backend/routers/brain.py`, `dashboard/backend/adapters/opbr_adapter.py`, `dashboard/backend/adapters/brain_session.py`
- 프런트엔드: `dashboard/frontend/src/lib/auth.ts`, `dashboard/frontend/src/components/auth/LockScreen.tsx`, `dashboard/frontend/src/pages/brain/BrainLegacyGate.tsx`(이상 신규), `dashboard/frontend/index.html`, `dashboard/frontend/src/lib/api.ts`, `dashboard/frontend/src/App.tsx`, `dashboard/frontend/src/pages/brain/BrainPage.tsx`, `dashboard/frontend/src/pages/settings/SettingsPage.tsx`
- CLI·하네스: `opal/tools/opal-cli/lib/console.sh`, `opal/tools/test-tool/lib/e2e/environment.py`, `opal/tools/test-tool/lib/e2e/orchestrator.py`, `opal/tools/test-tool/lib/e2e/executors/api.py`, `opal/tools/test-tool/lib/e2e/redaction.py`, `.opal/e2e/environment.json`, `.opal/e2e/console_session.py`(신규)
- 문서: `docs/ARCHITECTURE.md`, `docs/PROJECT.md`, `docs/SECURITY.md`, `README.md`, `opal/tools/opal-cli/README.md`, `opal/tools/test-tool/README.md`
- 테스트: 신규 `dashboard/backend/tests/{auth_helpers,test_auth_gate,test_entry_token,test_legacy_brain_policy,test_brain_legacy_api}.py`, `dashboard/frontend/src/lib/auth.test.ts`, `dashboard/frontend/src/components/auth/LockScreen.test.tsx`, `dashboard/frontend/src/pages/brain/brain-legacy-gate.test.tsx`, `opal/tools/test-tool/tests/test_e2e_session_bootstrap.py`. 갱신 `dashboard/backend/tests/{test_brain,test_brain_spike,test_routers,test_skill_docs,test_cors_env,test_main,test_deploy_smoke}.py`, `dashboard/frontend/src/pages/brain/brain-navigation-guard.test.tsx`, `scripts/tests/test_console_open.sh`, `opal/tools/test-tool/tests/test_e2e_sut_http_surfaces.py`, `opal/tools/test-tool/tests/test_e2e_skeleton.py`(PLAN 밖 — 새 환경 선언에 맞춘 fixture·무세션 브라우저 케이스의 진입 방식 갱신, 단언 약화 없음)

## 검증

- 시나리오 17건 전부 PASS(`test-scenario.json`, RED 12건 확인 후 lock): 결정론 S-1~S-14·S-16, 실제 uvicorn 격리 SUT S-15(real-http), 실제 Chrome S-17(real-usage).
- 최종 게이트: 백엔드 전체 524 passed·41 failed — 실패 집합이 변경 전과 동일(`test_routers.py` 36·`test_skill_docs_layout.py` 4·`test_config.py` 1, 인증과 무관한 fixture·설치기 문자열 부재), 신규 실패 0. test-tool 전체 633 passed. 프런트엔드 `tsc`·`lint` 통과, vitest 170 passed, `npm run build` 성공. `console.sh` 회귀 3종(open 10/ownership 23/scan 16) PASS. `code-scan validate --changed` ok.
- 독립 checker: 컨벤션 Critical/High 0(Low 1 해소), 보안 Critical/High 0(Medium 5·Low 6, 아래 참고).

## 회고적 학습 후보

.opal/brain/pages/concept/console-auth-default-deny-gate.md
.opal/brain/pages/concept/console-entry-token-channel.md
.opal/brain/pages/concept/legacy-brain-spawn-policy-gate.md
.opal/brain/pages/entity/opal-console.md
.opal/brain/pages/concept/console-open-health-readiness.md
.opal/brain/pages/concept/e2e-environment-config-ownership.md

## 참고

- 보안 Medium 중 이번에 고친 것: M1(E2E 증적 마스킹 누락 — 키 추가). 남은 것: M2 진입 token이 `open` 명령 인자에 실려 같은 호스트의 다른 uid가 60초 안에 선점할 수 있음(다중 사용자 호스트 한정), M3 개발용 CORS 기본 origin(`127.0.0.1:5173`)이 credentials와 함께 항상 허용되어 그 포트의 다른 페이지가 세션 CSRF를 읽을 수 있음, M4 FastAPI `/docs`·`/redoc`·`/openapi.json`이 세션 없이 응답하고 CDN 스크립트를 로드(E2E가 `openapi.json` 200에 의존해 이번에는 유지, SECURITY.md 서술은 정정), M5 로그 파일 `/tmp/opal-console.log` 예측 가능 경로(이번 태스크 이전부터). Low: Host `[::1]` 접미사 파싱 관대, 인증 전 교환 본문 크기 상한 검사 시점, 구형 Brain 켜기·끄기 경합 시 메모리와 파일 불일치 가능(재시작 시 꺼짐으로 복구), 진입 token 디렉터리 상위 경로 미검증, 첫 이동 URL의 브라우저 기록 잔존, 502 detail의 claude stderr 일부 노출.
- 제안서 §9 Phase 0 완료 기준 충족. Phase 1 이후(Gateway·Account·Profile·새 Brain transport)는 이 태스크 범위 밖이다. 설치본(`~/.opal/dashboard-server`) 재배포와 Console 재기동은 실행하지 않았다 — 반영하려면 `opal-cli update` 후 `opal-cli console stop` → `opal-cli console open`.
- S-17은 `e2e run`이 아니라 같은 SUT 로직을 재현한 임시 CDP 스크립트로 관찰했다(하네스 브라우저 컨텍스트가 하나뿐이라 ③④ 관찰 불가). S-15의 `requests`·`responses` 증적명은 하네스 어휘와 어긋나 별도 검증했다. 두 가지는 후속 정리 후보다.
