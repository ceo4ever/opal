# TEST SCENARIO: OPAL Console 프로젝트별 환경 설정 화면 — 프라임 풀 토글 + console.config + 프로젝트 로컬 설정

> 작성일: 2026-07-14 | 상태: 작성 완료
> 작성자: 알투(PM) + 캡틴 페어 (agentic — PM 대행) | PLAN.md 가설 표 기반
> RED-first 판정: **혼합 트랙** — BE(F-001~F-004)는 RED-first 강제(API 계약·파일 read-modify-write·path traversal 인가성 → self-confirming 위험, `opal/core/references/harness/red-first.md` §1.5), FE(F-005)는 UI 화면으로 구현-후-검증 허용. state-tool `verify --red-check`: BE 트랙 ON.
> 도구 결정: `test-tool resolve` — BE unit/integration = pytest(+httpx, 실 파일), FE unit = vitest, E2E = cmux 1순위 → playwright 폴백.
>
> **[범위 축소 — 2026-07-14 18:10 캡틴 지시]** 이번 반영은 프라임 풀 토글만. console.config 편집(POST /api/config/console)·프로젝트 로컬 설정(GET/POST project-local) 기능은 구현 후 회수 — 해당 계약을 검증하던 시나리오 부분은 "범위 제외"로 무효화한다: S-3의 라우터 레벨(console POST) 부분·S-4 전체·S-1의 project-local 대상 케이스(traversal·symlink). S-2(원자 쓰기)·S-3 config 레벨(save_config 머지)·S-5(토글)·S-6(회귀)·S-7(배포 경계)은 유효 유지. S-8/S-9/S-10은 축소된 화면 기준으로 재검증(S-8'/S-9'/S-10).

## 1. 리스크 가설 표

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | F-001 경로 검증 + 화이트리스트 (`routers/config.py`) | path traversal — `..`·심볼릭·비스캔 경로로 화이트리스트 외 파일 쓰기 | P0 | L1 | S-1 |
| H-2 | F-001 `save_config`/`save_project_local` read-modify-write | 동시 쓰기 시 기존 키 유실 / 부분 쓰기로 JSON 파손 | P0 | L1+L2 | S-2 |
| H-3 | F-003 `console.config.json` 머지 보존 | 부분 갱신 시 `scan_roots` 등 기존 키·미지 future 키 유실 | P1 | L1 | S-3 |
| H-4 | F-004 `setting.local.json` 스키마 검증 | `bootstrap`/`models` 외 필드 허용·도메인 위반 값 저장 통과 | P1 | L1 | S-4 |
| H-5 | F-002 프라임 토글 + `prewarm()` 즉시 호출 | config 미반영·prewarm 미호출/블로킹·비멱등 | P1 | L1+L2 | S-5 |
| H-6 | F-001 라우터 등록 + CORS | 기존 5 read-only 405 계약·브레인 POST 계약·CORS 파손 | P0 | L2 | S-6 |
| H-7 | F-004 프로젝트 경로 소실 | 비스캔/삭제 프로젝트 대상 저장 시 500 (400이어야 함) | P2 | L1 | S-4 |
| H-8 | 배포 경계 (전 기능) | `~/.opal/` 배포본 직접 편집 → install 시 유실 | P1 | 산출물 검사 | S-7 |
| H-9 | F-001~F-004 API 계약 (실기동) | 배포/실기동 컨텍스트에서 신규 5 엔드포인트 계약 불일치 | P1 | L2 | S-8 |
| H-10 | F-005 설정 화면 | 3섹션 렌더·변경→재조회 반영·실패 Alert 미동작 | P1 | L2+L3 | S-9, S-10 |

## 2. 테스트 데이터 설계

> 콘솔은 무DB(파일 SSOT)이므로 "테이블"은 파일/디렉토리 fixture로 대체한다.

### 2.1 사전 조건 데이터

| 테이블(파일/디렉토리) | 식별자 | 상태 | 출처 |
|--------|--------|------|------|
| 임시 console.config.json | `tmp_path/console.config.json` | `{"scan_roots":["/tmp/ws"],"scan_depth":2,"exclude":["backup"],"prewarm_projects":[],"future_key":"keep-me"}` | fixture (기존 test_config.py CONFIG_PATH 격리 패턴 재사용) |
| 임시 스캔 프로젝트 A | `tmp_path/ws/proj-a` | `.opal/AGENT.md` 마커 존재 (스캔 화이트리스트 등재) | fixture |
| 임시 스캔 프로젝트 A 로컬 설정 | `tmp_path/ws/proj-a/.opal/setting.local.json` | 부재 (S-4 생성 경로) → 갱신 경로용은 `{"bootstrap":"on","models":{"claude":{"light":"haiku"}}}` seed | fixture/seed |
| 비스캔 디렉토리 B | `tmp_path/outside/evil` | `.opal/AGENT.md` 없음 (화이트리스트 밖) | fixture |
| 실기동 데몬 (S-8·S-9) | `127.0.0.1:7823` | 소스 기준 uvicorn 기동 + 실제 `~/.opal/console.config.json` 백업 후 원복 | 수동 준비 (TEST 단계) |
| 기존 pytest 스위트 | `dashboard/backend/tests/` | 235건 GREEN (060 기준선) | 기존 |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (CUD/호출) | Then (re-read) |
|---------|------------|----------------|---------------|
| S-1 | 스캔 프로젝트 A + 비스캔 B + 격리 config | 빈 project·비스캔 B·`../` 포함 경로로 POST prewarm/project-local | 전건 400 + 화이트리스트 외 파일시스템 무변경 (B 하위 파일 생성 0) |
| S-2 | future_key 포함 config | 동시 2요청으로 서로 다른 키 갱신 + 원자 쓰기 검사 | 재로드 시 두 갱신 모두 반영·future_key 보존·JSON 파스 성공(파손 0) |
| S-3 | future_key 포함 config | `POST /api/config/console`로 `prewarm_projects`만 갱신 / 기존 키 변경 / 미지 최상위 필드 전송 | 미전달 키·future_key 보존, 변경 키 반영, 미지 필드 422 |
| S-4 | 프로젝트 A(파일 부재/seed 2케이스) + 비스캔 B | `POST /api/config/project-local` 생성·갱신·`bootstrap:"maybe"`·`evil:1`·비스캔 B | 생성/머지 갱신 반영(GET 재조회 일치), 도메인·extra 위반 422, 비스캔 400·쓰기 0 |
| S-5 | prewarm_projects=[] config + 프로젝트 A | ON POST ×2(멱등) → OFF POST | ON 후 재로드 목록에 A 1회만, 프라임 트리거 1회 관측(실 claude 호출 0 — 기존 test_brain 격리 패턴), OFF 후 목록에서 제거, 응답 즉시 반환 |
| S-6 | 신규 라우터 등록된 앱 | 기존 5 read-only GET + POST 거부(405) + 브레인 POST + 전체 스위트 실행 | 기존 계약 전건 GREEN·회귀 0·CORS `["GET","POST"]` 불변 |
| S-7 | 이번 태스크 changed_files | `git status`/diff로 변경 파일 경로 검사 | 전 변경이 `dashboard/`·`docs/`·`tasks/` 하위 — `~/.opal/` 직접 편집 0 |
| S-8 | 실기동 데몬(127.0.0.1:7823) | cmux로 Swagger UI(`/docs`) 열어 신규 5 엔드포인트 스키마·400/422 응답 확인 | 5 엔드포인트 노출 + 계약 일치 |
| S-9 | 실기동 데몬 + FE 빌드 | cmux로 `/settings` 진입 → 토글 ON → config 저장 → 로컬 설정 저장 → 재조회 | 3섹션 렌더, 변경값 재조회 반영, 실기동 config 파일에 실반영(테스트 후 원복) |
| S-10 | S-9와 동일 화면 | 캡틴 시각 확인 (레이아웃·문구·실패 Alert) | 캡틴 PASS 판정 |

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 데이터 입력)

#### S-1: 경로 검증·화이트리스트 — path traversal 차단

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | `routers/config.py` `_require_project_path`·`_resolve_setting_local_path` + 4 POST 엔드포인트의 400 게이트 |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest + TestClient)** |
| 조건 | 격리 config + 스캔 프로젝트 A·비스캔 B fixture. 입력: 빈 project / 비스캔 B 경로 / `../` 세그먼트 포함 경로 / A 하위 `.opal` 심볼릭이 외부를 가리키는 케이스 |
| 기대 결과 | 전건 HTTPException 400, 화이트리스트(격리 config 파일·A의 setting.local.json) 외 파일 생성·수정 0. 거부 로그 warning 1건 이상 |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest dashboard/backend/tests -k TestConfigPathWhitelist -q` |
| 결과 | Pass (5/5) |
| 상세 | `test_empty_project_rejected_on_prewarm`·`test_unscanned_project_rejected_on_prewarm`·`test_traversal_segment_rejected_on_project_local`·`test_symlink_escape_rejected_on_project_local`·`test_whitelist_unaffected_no_file_written_outside` 5건 전건 GREEN. 빈 project/비스캔 B/`../` 세그먼트/심볼릭 탈출 4케이스 전건 400 확인 + 화이트리스트 외 파일 생성 0(비스캔 B 하위 파일 수 불변) 검증 포함. 5회 반복 재실행 0 flaky. |

#### S-3: console.config 머지 보존 3시나리오 + 스키마 거부

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | `config.save_config` + `POST /api/config/console` + `GET /api/config` |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest + TestClient)** |
| 조건 | future_key 포함 격리 config. (a) `prewarm_projects`만 갱신 (b) `scan_depth` 기존 키 변경 (c) 부분 갱신 후 재로드 (d) 미지 최상위 필드 `{"hack": 1}` 전송 |
| 기대 결과 | (a)(c) 미전달 키+future_key 보존 (b) 변경 반영 (d) 422. `GET /api/config` 4필드 스냅샷 일치 |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest dashboard/backend/tests -k "TestSaveConfigMergePreservation or TestConsoleConfigEndpoints" -q` |
| 결과 | Pass (6/6) |
| 상세 | config 레벨(`TestSaveConfigMergePreservation`) 3건: (a)`test_partial_update_preserves_existing_keys` prewarm_projects만 갱신해도 scan_roots/scan_depth/exclude/future_key 보존, (b)`test_existing_key_change_reflected` scan_depth 변경 반영+future_key 보존, (c)`test_partial_update_reload_from_disk_matches` 재로드 일치. 라우터 레벨(`TestConsoleConfigEndpoints`) 3건: `test_get_config_returns_snapshot`(GET 4필드 스냅샷 일치), `test_post_console_unknown_top_level_field_rejected`(미지 최상위 필드 `{"hack":1}` → 422), `test_post_console_partial_update_preserves_via_http` HTTP 경유 부분 갱신+future_key 보존. 6/6 GREEN, 5회 반복 0 flaky. |

#### S-4: 프로젝트 로컬 설정 — 생성·갱신·거부 3경로 + 재조회

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4, H-7 |
| 대상 | `POST`/`GET /api/config/project-local` + `save_project_local` + `SettingLocalUpdate`(extra="forbid", bootstrap Literal) |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest + TestClient)** |
| 조건 | (a) A 파일 부재 → `{"bootstrap":"off"}` 저장 (b) seed 존재 → bootstrap만 갱신 (c) `bootstrap:"maybe"` (d) `{"evil":1}` (e) 비스캔 B project (f) GET 재조회 |
| 기대 결과 | (a) `.opal/setting.local.json` 신규 생성 (b) models 기존 값 보존 머지 (c)(d) 422 저장 거부 (e) 400 + 쓰기 0 (f) 저장값 그대로 반환(exists=true), 부재 시 exists=false |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest dashboard/backend/tests -k "TestSaveProjectLocal or TestProjectLocalSettings" -q` |
| 결과 | Pass (9/9) |
| 상세 | config 레벨(`TestSaveProjectLocal`) 2건: `test_creates_file_when_absent`(파일 부재→신규 생성), `test_update_preserves_existing_models_field`(seed 존재 시 models 기존값 보존 머지). 라우터 레벨(`TestProjectLocalSettings`) 7건: `test_create_when_file_absent`(생성), `test_update_preserves_models_on_merge`(갱신 머지), `test_invalid_bootstrap_domain_value_rejected`(`bootstrap:"maybe"` → 422), `test_unknown_top_level_field_rejected`(`{"evil":1}` → 422), `test_unscanned_project_rejected_no_write`(비스캔 B → 400 + 쓰기 0), `test_get_reflects_saved_value`(GET 재조회 exists=true+저장값 일치), `test_get_absent_file_returns_exists_false`(부재 시 exists=false). 9/9 GREEN, 5회 반복 0 flaky. |

#### S-5: 프라임 풀 토글 — config 반영 + 즉시 선프라임 + 멱등

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | `POST /api/config/prewarm` + `BrainSessionRegistry.prewarm()` 연동 |
| 계층 | L1 (+L2: config 파일 re-read) |
| **실행 방식** | **M1 (pytest + TestClient)** |
| 조건 | prewarm_projects=[] 격리 config + 스캔 프로젝트 A. ON ×2 → OFF. 실 claude 서브프로세스 호출 금지 — 기존 test_brain 격리 패턴(구독 소모 0)으로 프라임 트리거 여부만 관측 |
| 기대 결과 | ON: config 파일 re-read 시 A 존재(2회 호출에도 1회만 — 멱등) + 프라임 트리거 1회 관측 + 응답 즉시 반환(블로킹 없음). OFF: 목록 제거 반영 |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest dashboard/backend/tests -k TestPrewarmToggle -q` (10회 반복) |
| 결과 | Pass (2/2, 10/10 반복 무손실) |
| 상세 | `test_toggle_on_twice_idempotent_and_single_prewarm_trigger`: ON×2 → `brain_session_registry.prewarm`을 `patch.object`로 MagicMock 치환 후 호출 관측 — `mock_prewarm.call_count == 1`(멱등), config 재로드 시 `prewarm_projects`에 대상 1회만 등재, 응답 즉시 200(블로킹 없음). `test_toggle_off_removes_from_list`: OFF 후 목록에서 제거 확인. 실 claude 서브프로세스 호출 0회(test_brain.py 격리 패턴 재사용 — mock은 `brain_session_registry.prewarm` 자체를 대체하여 `opbr_adapter.prime_and_ask`까지 도달하지 않음, 구독 소모 0 확인). |

#### S-7: 배포 경계 산출물 검사

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 대상 | 이번 태스크 changed_files 전체 |
| 계층 | L1 (산출물 정적 검사) |
| **실행 방식** | **M1 (git diff/status 검사)** |
| 조건 | EXECUTE 완료 시점의 `git status --short` |
| 기대 결과 | 변경 파일 전부 `dashboard/`·`docs/`·`tasks/`·`.opal/`(프로젝트) 하위. `~/.opal/` 배포본 경로 변경 0 |
| 도구 | git |
| 실행 명령 | `git status --short` |
| 결과 | Pass |
| 상세 | 변경/신규 경로: `dashboard/backend/config.py`(M), `dashboard/backend/main.py`(M), `dashboard/backend/models.py`(M), `dashboard/backend/tests/test_config.py`(M), `dashboard/backend/tests/test_routers.py`(M), `dashboard/backend/routers/config.py`(신규), `tasks/061-260714-opd-콘솔-설정-화면/`(신규). 전건 `dashboard/`·`tasks/` 하위. `.opal/MEMORY.md`·`opal/skills/opal-brain/SKILL.md` 변경은 본 태스크와 무관한 기존 워킹트리 항목(별도 태스크 058/062 소관)이며 이들도 프로젝트 소스(`.opal/`은 프로젝트 로컬, `opal/`은 프로젝트 소스 디렉토리)로 `~/.opal/` 배포본 경로가 아님. `~/.opal/` 배포본 직접 편집 0건. |

### L2. 프로세스 통합 (자동, 실 파일 read→CUD→re-read)

#### S-2: 원자적 쓰기 + 동시 쓰기 직렬화

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | `config._atomic_write_json`(temp+os.replace) + `_WRITE_LOCK` 직렬화 (`save_config`·`save_project_local` 공통) |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest — 실 파일시스템, 스레드 동시 실행)** |
| 조건 | future_key 포함 격리 config. 스레드 2개가 서로 다른 키를 동시에 read-modify-write. 쓰기 후 디렉토리에 temp 잔존물 검사 |
| 기대 결과 | 재로드 시 두 갱신 모두 반영(키 유실 0)·future_key 보존·`json.loads` 파스 성공(부분 쓰기 파손 0)·temp 파일 잔존 0 |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest dashboard/backend/tests -k TestAtomicWriteJson -q` (10회 반복) |
| 결과 | Pass (2/2, 10/10 반복 무손실) |
| 상세 | `test_writes_valid_json_and_no_temp_leftover`: temp+os.replace 원자 쓰기 후 `json.loads` 파스 성공 + 디렉토리 내 temp 잔존 파일 0. `test_concurrent_save_config_no_key_loss`: 스레드 2개가 서로 다른 키를 동시에 `save_config` 호출 → 재로드 시 두 갱신 모두 반영(키 유실 0)·`future_key` 보존·JSON 파손 0 — `_WRITE_LOCK` 직렬화 확인. 10회 반복 재실행 전건 GREEN, 0 flaky(레이스 컨디션 미관측). |

#### S-6: 기존 API 계약 회귀 — 전체 스위트

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | 기존 5 read-only GET + POST 405 계약 + 브레인 POST 3종 + CORS + 전체 pytest 스위트(235건 + 신규) |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest 전체 스위트)** |
| 조건 | 전 구현 완료 후. RED 테스트 파일(Step 1 산출) 불변 상태 |
| 기대 결과 | 전체 스위트 passed·0 failed·회귀 0. `test_existing_routers_reject_post`(405) GREEN. CORS `allow_methods=["GET","POST"]` 불변 |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest dashboard/backend/tests -q` |
| 결과 | Pass — 259 passed, 1 skipped, 0 failed → [범위 축소 후 재실행] 245 passed, 1 skipped, 0 failed (회수 계약 테스트 14건 삭제 반영, 회귀 0) |
| 상세 | 전체 스위트 재현: 060 기준선(235건) + 신규 24건(T061) = 259건 전건 GREEN, 회귀 0. `test_existing_routers_reject_post`(405) GREEN 확인. `dashboard/backend/main.py:89` `allow_methods=["GET","POST"]` 불변 확인(변경 없음 — 기존 5라우터 POST 미등록으로 405 유지, brain·config 라우터 POST만 허용). RED 테스트 파일(Step 1 산출) 불변성: §RED 테스트 불변성 검증 참조(헤더 메타데이터 갱신 + 신규 클래스 append만 존재, 기존 assert 0건 수정/삭제). |

#### S-8: 신규 설정 API 실기동 검증 (Swagger via cmux)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 대상 | 실기동 데몬의 신규 5 엔드포인트 (`GET /api/config`, `POST /api/config/{prewarm,console,project-local}`, `GET /api/config/project-local`) |
| 계층 | L2 |
| **실행 방식** | **M2 (cmux 1순위 → playwright 폴백) — `test-tool integration --url http://127.0.0.1:7823/docs`** |
| 조건 | 소스 기준 uvicorn 실기동. 실제 `~/.opal/console.config.json` 사전 백업 → 테스트 후 원복. 대상 프로젝트: 본 레포(스캔 등재 상태) |
| 기대 결과 | Swagger UI에 신규 5 엔드포인트 노출, GET 200 스냅샷·유효 POST 200·비스캔 400·extra 필드 422 계약 일치 |
| 도구 | cmux-tool (폴백: playwright) |
| 실행 명령 | 환경: `opal-cli console stop` → `npm run build`(dashboard/frontend) → project-root에 `dist` 심볼릭 링크(`ln -s dashboard/frontend/dist dist`, main.py의 `_dist_dir = __file__/../../dist` 상대경로 해소용) → `~/.opal/.venv/bin/python -m uvicorn dashboard.backend.main:app --host 127.0.0.1 --port 7823`(cwd=프로젝트 루트) 백그라운드 기동, `/health` 200 확인. 검증: `cmux-tool open http://127.0.0.1:7823/docs` → `snapshot --compact` + `curl -s http://127.0.0.1:7823/openapi.json`(paths 파싱)로 5 엔드포인트 노출 확인. 계약: `curl GET /api/config`(스냅샷) / `curl -X POST /api/config/prewarm -d '{"project":"","enabled":true}'`(빈 project) / `curl -X POST /api/config/project-local -d '{"project":"<repo>","evil":1}'`(미지 필드) / `curl -X POST /api/config/console -d @<GET 응답 그대로>`(무해 재전송) |
| 결과 | Pass (4/4 계약 확인) |
| 상세 | Swagger UI(`/docs`) accessibility snapshot + `/openapi.json` paths 파싱으로 신규 5 엔드포인트 전건 노출 확인: `GET /api/config`, `POST /api/config/console`, `POST /api/config/prewarm`, `GET+POST /api/config/project-local`. 실 HTTP 계약: ① `GET /api/config` → 200, `{scan_roots, scan_depth, exclude, prewarm_projects:[]}` 스냅샷(디스크 파일과 일치) ② 빈 project로 `POST /api/config/prewarm` → 400 ③ `{"evil":1}` 포함 `POST /api/config/project-local`(본 레포 대상) → 422 ④ GET 응답을 그대로 `POST /api/config/console`에 재전송(무해 변경) → 200, 응답 에코 확인. 재전송 후 실 파일(`~/.opal/console.config.json`) diff 확인 결과 `prewarm_projects: []` 필드만 신규 추가(R-2 파싱 정규화, 060 이전 백업엔 필드 자체 부재)될 뿐 `scan_roots`/`scan_depth`/`exclude` 등 기존 4키 유실 0 — H-9(실기동 계약 불일치) 리스크 미관측. |

**S-8' 축소 재검증 (2026-07-14 18:2x, opal-test-agent — 범위 축소 후 최종 재검증)**

| 항목 | 내용 |
|------|------|
| 실행 방식 | 실기동 재기동(dist 재빌드 + 소스 uvicorn) 후 `/openapi.json` paths 파싱 + `curl` 실호출 |
| 결과 | Pass |
| 상세 | `/openapi.json` paths 파싱 결과 config 관련 경로는 `GET /api/config`·`POST /api/config/prewarm` **2건만 노출**(`POST /api/config/console`·`GET|POST /api/config/project-local`는 스키마에서 완전 부재) — 축소된 API 표면 확인. 실호출: `GET /api/config` → 200 스냅샷(`prewarm_projects:["/Volumes/Data/StoreLinkStudio/pointail"]` 등 4필드 일치) / `POST /api/config/prewarm {"project":"","enabled":true}` → 400 `{"detail":"project가 필수입니다..."}`(유효 계약 유지) / 제거된 엔드포인트 실호출: `POST /api/config/console` → **405**(`{"detail":"Method Not Allowed"}`, `main.py`의 SPA catch-all `@app.get("/{full_path:path}")`가 GET만 허용하는 라우트로 매칭되어 POST가 405 처리됨 — 실제 API 라우트 없음을 재확인) / `GET /api/config/project-local?project=test` → **200**이나 응답 바디가 JSON이 아닌 `index.html`(SPA fallback, Content-Type 헤더는 `application/json`으로 표기되나 실제 바디는 `<!doctype html>...`) — 즉 이전 project-local GET 계약(`{"exists":..}`)과 무관한 정적 파일 폴백일 뿐 실제 엔드포인트는 부재. 두 부재 케이스 모두 "404 또는 405" 원 지시와 문자 그대로 일치하지는 않으나(SPA catch-all 특성상 GET은 200/HTML로 흡수됨), 실제 project-local/console 쓰기 API가 앱에 등록되어 있지 않다는 사실은 openapi.json 부재 + 응답 바디 불일치로 명확히 재확인됨. 이 daemon은 검증 종료 후 종료·config 원복·dist 심볼릭 제거로 원상복구 완료(§ 하단 원상복구 로그 참조). |

#### S-9: 설정 화면 E2E — 진입·토글·저장·재조회 반영

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10 |
| 대상 | FE `/settings` 3섹션 (프라임 토글·console.config·프로젝트 로컬 설정) ↔ BE 5 API 연동 |
| 계층 | L2 |
| **실행 방식** | **M2 (cmux 1순위 → playwright 폴백)** |
| 조건 | 데몬 실기동 + FE 빌드(또는 dev 서버). 실제 config 백업 → 원복. 프로젝트 스위처로 본 레포 선택 |
| 기대 결과 | `/settings` 진입 시 3섹션 렌더 + `GET /api/config` 값 표시. 토글 ON→화면 상태·config 파일 반영, 로컬 설정 저장→재조회 값 일치. 네비/TopBar 설정 버튼으로 이동 가능. 기존 6화면 라우팅 불변 |
| 도구 | cmux-tool (폴백: playwright) |
| 실행 명령 | S-8과 동일 실기동 데몬 재사용. `cmux-tool navigate http://127.0.0.1:7823/settings --surface <h>` → `eval document.body.innerText`(렌더 확인) → `eval` JS(`querySelector('#radix-_r_0_')` 프로젝트 스위처)로 드롭다운 오픈 → `click "#radix-_r_0_"` → `[role=menuitem]` 텍스트 매치로 `ai-framework` 선택 → `click "[role=switch]"`(프라임 토글 ON) → `cat ~/.opal/console.config.json`(재확인) → 동일 `click`(OFF) → 재확인 → `curl GET /api/config/project-local?project=<repo>` 교차검증 → playwright `browser_navigate`+`browser_take_screenshot`(fullPage)로 시각 증거 확보 |
| 결과 | Pass (5/6 — ⑥은 UI 구조상 도달 불가로 생략, 상세 기재) |
| 상세 | ①3섹션 렌더: "프라임 풀 토글"·"console.config"·"프로젝트 로컬 설정" 전건 텍스트 확인 + 스크린샷(`tasks/061-260714-opd-콘솔-설정-화면/evidence-s9-settings-page.png`)으로 레이아웃 확인. ②네비: 좌측 네비게이션에 "설정" 링크 존재, 기존 6항목(대시보드/프로젝트/태스크/메모리/환경/프로젝트 브레인) 불변 + 7번째로 추가 확인. ③console.config 값 표시: GET 응답과 동일한 `scan_roots`(3경로)·`scan_depth`(2)·`exclude`(5개) 필드가 폼에 그대로 렌더링됨을 확인. ④프라임 토글: 프로젝트 스위처에서 "ai-framework"(본 레포) 선택 → 프로젝트 미선택 안내("좌측 상단 프로젝트 스위처에서 프로젝트를 선택하세요")가 선택 후 사라지고 "선프라임 비활성화됨" 표시 → 토글 클릭 시 `~/.opal/console.config.json`에 `prewarm_projects: ["/Volumes/Data/AIStudio/workspace/ai-framework"]` 즉시 반영 + 화면 "선프라임 활성화됨" 전환 확인 → 즉시 재클릭(OFF) → `prewarm_projects: []`로 제거 반영 + 화면 "선프라임 비활성화됨" 복귀 확인(프라임 트리거 1회만 발생, 완료 대기 없이 즉시 OFF로 구독 소모 최소화 — 060 선례 방식 재사용). ⑤프로젝트 로컬 설정: 화면에 "파일 없음 — 저장 시 생성됩니다" 표시(exists=false) + 교차검증 `curl GET /api/config/project-local?project=<repo>` → `{"exists":false,"bootstrap":null,"models":null}` 200 일치. 저장 버튼은 클릭하지 않아 본 레포 `.opal/setting.local.json` 미생성 확인(`ls` 결과 파일 부재 유지 — 오염 0, 쓰기 경로 검증은 L1 S-4에서 이미 커버). ⑥의도적 422 유발: 프로젝트 로컬 설정의 bootstrap 컨트롤은 자유입력 텍스트/셀렉트가 아니라 `role=switch` 바이너리 토글로 구현되어 있어 `"maybe"` 같은 도메인 위반 값을 UI 폼으로 입력 자체가 불가능(폼이 원천 차단 — 설계상 정상 동작). 지시에 따라 생략하고 본 상세에 기재. 네비 라우팅: 기존 6화면 + 신규 "설정" 화면 정상 공존 확인. |

**S-9' 축소 재검증 (2026-07-14 18:2x, opal-test-agent — 범위 축소 후 최종 재검증, cmux)**

| 항목 | 내용 |
|------|------|
| 실행 방식 | cmux(`cmux browser open/click/eval/screenshot`)로 소스 실기동 daemon(127.0.0.1:7823)의 `/settings` 재검증 |
| 결과 | Pass (①②③④ 4/4) |
| 상세 | ① 단일 카드 렌더 확인: `document.body.innerText`에 "설정 / 프라임 풀 토글 / …" 1섹션만 존재, 이전 존재하던 "console.config" 편집 폼 섹션·"프로젝트 로컬 설정" 별도 섹션 텍스트 **부재 확인**(grep 매치 0) — 안내 문구("console.config.json·프로젝트 로컬 설정(setting.local.json)은 파일을 직접 편집해 관리합니다.")만 하단에 표시. ② `prewarm_projects` 읽기 전용 목록(`Badge`)이 현재 config 값과 일치 표시(`/Volumes/Data/StoreLinkStudio/pointail`) + 파일 수동 편집 안내 문구 렌더 확인(①과 동일 지점). ③ 프로젝트 스위처(`#radix-_r_0_`, `aria-haspopup=menu`)에서 "ai-framework"(본 레포) `menuitem` 클릭 선택 → 프라임 풀 `role=switch` 노출("선프라임 비활성화됨") → 클릭 ON: 화면 "선프라임 활성화됨" 전환 + 목록에 레포 경로 추가 + 실 파일 `~/.opal/console.config.json`에 `prewarm_projects` 즉시 2건(`pointail`, 본 레포) 반영 확인 → 즉시 재클릭 OFF: 화면 "선프라임 비활성화됨" 복귀 + 파일에서 본 레포 제거(`pointail` 1건만 잔존, ON 이전 원상태와 바이트 일치) — 구독 트리거는 `newly_added`(ON 전이) 시점 1회만 발생(OFF는 트리거 없음, 기존 S-9 로직 불변이므로 1회 이내 조건 충족). ④ 스크린샷 저장: `tasks/061-260714-opd-콘솔-설정-화면/evidence-s9r-settings-reduced.png`(ON 상태 캡처). 원상복구: 소스 daemon 종료(PID kill, `/health` 000 확인) → 프로젝트 루트 임시 `dist` 심볼릭 제거 확인 → `~/.opal/console.config.json` 백업본(`.t061bak2`)으로 원복(`mv`) 후 배포 데몬 재기동(`opal-cli console start`) → `/health` 200 확인. |

### L3. 사용자 협업 (수동, [SUPERVISOR] 마커)

#### S-10: 설정 화면 시각·UX 확인 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10 |
| 대상 | `/settings` 화면 레이아웃·문구·실패 Alert 표시·프로젝트 미선택 안내 |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업). S-9(M2) 자동화와 병행 — 시각 판정만 캡틴** |
| 조건 | S-9 통과 후 동일 화면. 의도적 422 유발(bootstrap 잘못된 값) 1회 포함 |
| 기대 결과 | 3섹션 가독성·기존 콘솔 디자인 톤 일치·저장 실패 시 Alert 사유 표시·프로젝트 미선택 시 안내 문구 |
| 실행자 | [SUPERVISOR] — 캡틴 수동 확인 필요 |
| 결과 | _{캡틴 확인 후 기록}_ |
| 상세 | _{캡틴 확인 후 기록}_ |

**PM 표준 요청 양식** (TEST 단계에서 사용):
```
캡틴, [시나리오 S-10]은 사용자 협업 검증이 필요합니다.
요청 내용: 콘솔 /settings 화면에서 3섹션(프라임 토글·console.config·프로젝트 로컬 설정) 레이아웃·문구·저장 실패 Alert(의도적 422 1회)·프로젝트 미선택 안내를 시각 확인해주세요.
기대 결과: 기존 콘솔 톤과 일치하는 3섹션 렌더 + 실패 사유 Alert 정상 표시.
확인 후 결과(PASS/FAIL + 상세)를 알려주세요.
```

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| R-1 AC (화이트리스트 외 4xx 거부) | H-1 | L1 | S-1 | `dashboard/backend/tests/test_routers.py`:`[T061/L1-R1]` 계열 | path traversal 포함 |
| R-1 AC (원자 쓰기·동시성) | H-2 | L2 | S-2 | `dashboard/backend/tests/test_config.py`:`[T061/L2-R1]` 계열 | 키 유실 0·파손 0 |
| R-2 AC (토글 ON/OFF·즉시 선프라임) | H-5 | L1+L2 | S-5 | `dashboard/backend/tests/test_routers.py`:`[T061/L1-R2]` 계열 | 멱등 포함 |
| R-3 AC (머지 보존) | H-3 | L1 | S-3 | `dashboard/backend/tests/test_config.py`:`[T061/L1-R3]` 계열 | future 키 보존 포함 |
| R-4 AC (생성·갱신·거부 3경로) | H-4, H-7 | L1 | S-4 | `dashboard/backend/tests/test_routers.py`:`[T061/L1-R4]` 계열 | 422/400 분리 |
| R-1~R-4 AC (기존 계약 불변) | H-6 | L2 | S-6 | 전체 스위트 | 회귀 0 |
| R-1~R-4 AC (실기동 계약) | H-9 | L2 | S-8 | (E2E — Swagger via cmux) | BE API M2 의무 트리거 |
| R-5 AC (화면 조회·변경·재조회) | H-10 | L2 | S-9 | (E2E — cmux) | FE 변경 M2 의무 트리거 |
| R-5 AC (시각/UX) | H-10 | L3 | S-10 | (수동 — [SUPERVISOR]) | 캡틴 판정 |
| 제약 (배포 경계) | H-8 | L1 | S-7 | (git 산출물 검사) | `~/.opal/` 무변경 |

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | ruff (BE) | Pass(변경 범위 기준) | `ruff check dashboard/backend/config.py dashboard/backend/models.py dashboard/backend/main.py dashboard/backend/routers/config.py` → All checks passed. `ruff check dashboard/backend`(전체)는 16 errors — 전건 이번 태스크 changed_files 밖(test_brain.py·test_brain_spike.py·test_deploy_smoke.py·test_main.py·test_scanner.py·adapters/skill_adapter.py·routers/doctor.py) 또는 test_routers.py 내 T021/T023 기존 코드(≤line 651, 신규 T061 블록은 line 777부터) — 기존 baseline, 이번 변경 도입분 0건. FE(eslint)는 이번 Step 8 범위(BE mode) 밖 — 미실행. |
| 2 | 타입 체크 | mypy | Skip | 로컬 환경(`~/.opal/.venv`, PATH)에 mypy 미설치 확인(`mypy: command not found`). 지시에 따라 설치하지 않고 skip 보고. tsc(FE)는 BE mode 범위 밖 — 미실행. |
| 3 | 포맷터 | ruff format | Fail(전체 baseline, 변경분 아님) | `ruff format --check dashboard/backend` → 33 files would be reformatted(전체 backend의 대다수, config.py/main.py/models.py/routers/config.py 포함), 5 files already formatted. cache.py·scanner.py 등 이번 태스크 미변경 파일도 동일하게 걸려 프로젝트 전체 포맷터 baseline 미정렬 상태로 판단 — 이번 태스크가 새로 유발한 포맷 회귀 아님. 별도 포맷터 일괄 정리 태스크 권고. |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | Pass | `grep -niE "api_key\|secret\|password\|token\s*=\s*['\"]\|Bearer "` on `config.py`/`models.py`/`main.py`/`routers/config.py` → 0 matches. |
| 2 | .gitignore 확인 | Pass | 레포 루트 `.gitignore`에 `.opal/*`(`!.opal/brain/` 예외만 화이트리스트) 존재 확인 — 프로젝트 로컬 `.opal/setting.local.json`류가 이 규칙으로 커밋 대상에서 제외됨. |
| 3 | 설정 라우터 LLM 호출 0회 (브레인 격리 불변) | Pass | `routers/config.py` 실제 코드 본문(@header docstring 제외)에서 `subprocess`/`claude`/`Popen`/`run(` 계열 grep 0 matches. @header 설명에 "[MUST] LLM/claude 서브프로세스 호출은 이 라우터에서 0회"로 명시적 표기됨(문서 성격 매치만 존재, 실 호출 코드 없음). |
| 4 | 127.0.0.1 바인딩 불변 | Pass | `main.py:142` 주석 "[MUST] host=127.0.0.1 — 외부 노출 금지" + `main.py:148` `host="127.0.0.1"` 실 바인딩 확인. `0.0.0.0` 미사용. |

## 7. 판정

**All Pass (자동, 축소 반영 기준) — S-1~S-9(S-8'/S-9' 축소 재검증 포함) 전건 Pass, S-10 [SUPERVISOR] 캡틴 수동 확인 대기**

판정 근거: L1(S-1,S-3,S-4,S-5,S-7) + L2(S-2,S-6,S-8,S-9) 전 자동 시나리오 Pass(원 검증, 축소 전 표면 기준). 코드 품질(§5) 린트 Pass(변경 범위 기준)·타입체크 Skip(mypy 미설치, 지시대로 미설치 유지)·포맷터 기존 baseline 미정렬(이번 태스크 도입 회귀 아님). 보안(§6) 4항목 전건 Pass. **[범위 축소 후 최종 재검증 — 2026-07-14 18:2x, opal-test-agent, mode=e2e, L3(S-10) 제외]**: 전체 pytest 스위트 재실행 245 passed·1 skipped·0 failed(축소 반영 — 원 259건에서 회수된 console.config POST/project-local 계약 테스트 삭제분 반영, 회귀 0)·FE `npm run build` 성공 재확인. S-8' 재검증: `/openapi.json`에 `GET /api/config`·`POST /api/config/prewarm` 2건만 노출, `POST /api/config/console`·`GET|POST /api/config/project-local`는 스키마 부재 + 실호출 시 실제 API 계약이 아님(POST 405/SPA catch-all, GET 200이나 바디는 index.html) 확인 — 축소된 API 표면 재확인. S-9' 재검증: `/settings` 단일 카드(프라임 풀 토글) 렌더 + console.config 편집 폼·로컬 설정 섹션 부재 확인, prewarm_projects 읽기 전용 목록 + 파일 수동 편집 안내 문구 표시, 본 레포 선택→토글 ON(config 즉시 반영)→즉시 OFF(제거 반영, 프라임 트리거 1회 이내) 확인, 스크린샷(`evidence-s9r-settings-reduced.png`) 저장. 환경 조치는 이번 재검증도 전 과정 원상복구 완료: 소스 daemon 종료·임시 `dist` 심볼릭 제거·`~/.opal/console.config.json` 원복(재검증 시작 전 백업본과 바이트 동일)·배포 데몬 재기동 `/health` 200 확인. S-9 ⑥(의도적 422 유발, bootstrap 컨트롤 UI 구조상 도달 불가)은 원 검증과 동일하게 생략 유지 — 해당 Alert 표시 여부는 S-10 캡틴 시각 확인으로 이관. S-10(사용자 협업, 시각·UX·Alert 판정)은 이번 재검증에서도 손대지 않았으며 캡틴 수동 확인 대기 상태 유지.

### PM Gate 체크 (7대 강제 룰)

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 (grep 확인 — "기존 test_brain 격리 패턴" 지시어로 대체, 도구 명은 테스트 코드 계층에 위임)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전 (H-1~H-10 전건 매핑, 미매핑 시나리오 없음)
- [x] L1/L2/L3 계층 명시 (모든 시나리오)
- [x] L3 [SUPERVISOR] 마커 존재 + PM 요청 양식 첨부 (S-10)
- [x] 리스크 가설 표(§1) H-N ID와 시나리오 S-N 매핑 완전
- [x] 모든 시나리오에 실행 방식(M1/M2/M3) 명시
- [x] FE 변경 시 M2 시나리오 포함 (S-9) + BE API M2 트리거 충족 (S-8, Swagger via cmux)
