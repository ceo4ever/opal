---
template: sdlc-v2
---
# TEST-SCENARIO: TODO CRUD 웹 앱 구현

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: worktree 루트(`feat/OP-TASK-001`)에서 Python 3.14 + pytest. 서버는 매 테스트마다 `python -m todo_web.app --host 127.0.0.1 --port <빈 포트> --data <tmp_path>/todos.json`으로 실제 프로세스를 띄운다(PLAN D-14 하네스: 포트 0 bind로 빈 포트 획득, `GET /health` 200을 최대 10초 폴링, 종료는 `terminate()`+`wait`). HTTP 요청은 표준 라이브러리 `http.client`로 보낸다.
- 공통 데이터: 테스트마다 새 `tmp_path`의 빈 데이터 파일 경로(파일 미존재 상태에서 시작). 생성 요청 기본 본문은 `{"title": "Buy milk", "description": "2L"}`.
- 대역 사용과 한계: 사용하지 않음. 모든 API 시나리오는 실제 서버 프로세스와 실제 JSON 파일을 사용한다. S-10의 `tests/test_basic.py`만 기존 `DummyHandler` 방식을 그대로 쓴다(기존 회귀 계약 자체이므로 대체가 아님).
- E2E: S-9는 OPAL venv의 Playwright(`~/.opal/.venv/bin/python`, headless Chromium)로 실제 브라우저에서 `GET /` 화면을 조작한다. 사람 협업 없음.
- 실행 조건: 자동 실행. RED 대상(S-2~S-8)은 `tests/test_todo_api.py`의 `test_s<N>_...` 함수로 작성한다.
- 병렬 그룹: 선언 없음(순차).

## Scenarios

| ID | 유형 | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|---|
| S-1 | regression | AC-1, C-3 | 빈 데이터 파일 경로로 실행 계약 명령 그대로 서버 기동 | `python -m todo_web.app --host 127.0.0.1 --port <PORT> --data <tmp>/todos.json` 실행 후 `GET /health` | 프로세스가 기동해 요청을 받고 `200`, `Content-Type`이 `application/json`으로 시작, 본문 JSON이 정확히 `{"ok": true}` | integration — pytest, 실제 서버 프로세스 | 구현 후 |
| S-2 | integration | AC-3, C-4 | 빈 저장소 | `POST /api/todos`, `Content-Type: application/json`, 본문 `{"title": "  Buy milk  ", "description": "2L"}` | `201`; 응답 JSON 객체의 키가 정확히 `id`·`title`·`description`·`completed`; `title == "Buy milk"`(앞뒤 공백 제거 저장), `description == "2L"`, `completed is false`, `id`는 정수; `Location` 헤더 == `/api/todos/{id}`; `Content-Type`이 `application/json`으로 시작 | integration — pytest, 실제 서버 프로세스 | 구현 전 RED |
| S-3 | integration | AC-4, AC-7 | `POST`로 A(`"A"`)·B(`"B"`) 2건 생성 | `GET /api/todos`; `GET /api/todos/{A.id}`; `GET /api/todos/999999` | 목록 `200` + 길이 2 배열, 각 원소 키가 정확히 4필드이고 A·B를 생성 응답과 같은 값으로 포함; 상세 `200` + A와 동일 객체; 없는 ID `404` + 본문이 `error` 키를 가진 JSON 객체 | integration — pytest, 실제 서버 프로세스 | 구현 전 RED |
| S-4 | integration | AC-5 | A(`"A"`, `"a"`)·B(`"B"`, `"b"`) 생성 | `PATCH /api/todos/{A.id}` `{"completed": true}` → `PATCH /api/todos/{A.id}` `{"title": "A2", "description": "a2"}` → `GET /api/todos/{B.id}` → `PATCH /api/todos/999999` `{"completed": true}` | 1차 `200`, `completed == true`이고 `title`·`description`은 `"A"`·`"a"` 유지; 2차 `200`, `title == "A2"`, `description == "a2"`, `completed == true` 유지; B는 생성 응답과 완전히 동일; 없는 ID `404` + `error` 키 JSON | integration — pytest, 실제 서버 프로세스 | 구현 전 RED |
| S-5 | integration | AC-6 | A·B 생성 | `DELETE /api/todos/{A.id}` → `GET /api/todos/{A.id}` → `GET /api/todos` → `DELETE /api/todos/{A.id}`(재삭제) | 삭제 `204` + 응답 본문 0바이트; 이후 상세 `404`; 목록은 B만 포함(길이 1); 재삭제 `404` + `error` 키 JSON | integration — pytest, 실제 서버 프로세스 | 구현 전 RED |
| S-6 | integration | AC-7, C-4 | 빈 저장소 | `POST /api/todos`를 다음 본문으로 각각 전송: `{"title": "   "}`, `{"title": "x"*121}`, `{"title": "t", "description": "d"*2001}`, `{"title": 123}`, 본문 `{bad json`, 빈 본문, 배열 `[1]`; 경계 확인으로 `{"title": "x"*120, "description": "d"*2000}`; 생성된 항목에 `PATCH` `{}`, `{"completed": "yes"}`, `{"title": "  "}` | 거부 요청은 모두 `400` + `Content-Type` `application/json` + `error` 키를 가진 JSON 객체; 120자 제목·2000자 설명은 `201`; 거부 후 `GET /api/todos`에는 경계 확인 1건만 있고 PATCH 거부 대상은 값이 바뀌지 않음 | integration — pytest, 실제 서버 프로세스 | 구현 전 RED |
| S-7 | integration | AC-7, C-4 | 항목 A 생성 | `POST /api/todos`를 `Content-Type: text/plain`·헤더 없음으로 각각 전송(본문은 유효 JSON); `PATCH /api/todos/{A.id}`를 `Content-Type: application/x-www-form-urlencoded`로 전송; `POST /api/todos`를 `Content-Type: application/json; charset=utf-8`로 전송; `PUT /api/todos`, `DELETE /api/todos`, `POST /api/todos/{A.id}`, `POST /health`, `PUT /api/todos/{A.id}`; `GET /nope` | 잘못된 `Content-Type` 쓰기 3건 `415` + `error` 키 JSON, A 불변; `charset` 파라미터 포함 `application/json`은 `201`; 미지원 method 5건 `405` + `error` 키 JSON(501 아님); 알 수 없는 경로 `404` + `error` 키 JSON | integration — pytest, 실제 서버 프로세스 | 구현 전 RED |
| S-8 | integration | AC-8, H-1 | 서버 1차 기동, 빈 데이터 파일 | A·B·C 생성 → B를 `PATCH {"completed": true, "title": "B2"}` → C 삭제 → 스레드 20개로 `POST` 20건 동시 전송 → `GET /api/todos` 결과 기록 → 서버 종료 → 같은 `--data`로 새 포트에서 재기동 → `GET /api/todos` | 동시 생성 20건 모두 `201`이고 서로 다른 `id`; 종료 전 목록 길이 22(A, 수정된 B, 동시 생성 20건, C 없음); 종료 후 데이터 파일이 유효 JSON이고 같은 22건을 포함; 재기동 후 목록이 종료 전 목록과 완전히 같음(B는 `"B2"`·`completed true`, C 없음); 재기동 후 상세 `GET /api/todos/{C.id}`는 `404` | integration — pytest, 실제 서버 프로세스 2회 기동 | 구현 전 RED |
| S-9 | e2e | AC-2 | 서버 기동, 빈 데이터 파일 | 브라우저로 `GET /` 열기 → 할 일 목록 영역(`#todo-list`)·제목 입력(`#title`)·설명 입력(`#description`)·생성 버튼(`#create-button`) 존재 확인 → 제목 `"E2E task"`, 설명 `"from browser"` 입력 후 생성 버튼 클릭 → 목록 갱신 대기 → 페이지 새로고침 | 클릭 전 4요소가 모두 보임; 클릭 후 `#todo-list` 안에 제목 `E2E task`·설명 `from browser` 항목이 나타남; 새로고침 후에도 같은 항목이 목록에 표시되고 `GET /api/todos` 응답에 해당 TODO가 존재 | e2e — Playwright headless Chromium(`~/.opal/.venv/bin/python`) + 실제 서버 프로세스. surface_kind `web_ui`, profile `browser`, actors `agent`, steps `open`·`fill`·`click`·`reload`(executor `browser`), required_evidence `screenshot_after_create`·`api_list_json` | 구현 후 |
| S-10 | check | C-2, H-2 | 구현 완료 worktree | `python -m pytest tests/ -q` | exit 0; 기존 `tests/test_basic.py` 2건을 포함한 전체 테스트 통과(실패·에러 0) | check — pytest 전체 실행 | 구현 후 |
| S-11 | check | C-1, C-5 | 구현 완료 worktree | `todo_web/` 아래 모든 `.py`의 import 최상위 모듈을 `ast`로 수집해 `sys.stdlib_module_names` ∪ {`todo_web`}과 비교; `git diff --name-only main...HEAD`와 미커밋 변경 목록 확인 | 표준 라이브러리 외 import 0건; 의존성 파일(`requirements*.txt`, `pyproject.toml`, `setup.py` 등) 추가 0건; 변경 파일이 `todo_web/app.py`, `todo_web/store.py`, `tests/test_todo_api.py`와 태스크 폴더(`tasks/001-261002-opds-TODO-CRUD-웹앱-구현/`)로 한정(OPAL 런타임 산출 경로 `.opal/run/`는 제외) | check — 정적 검사 스크립트 + git | 구현 후 |
