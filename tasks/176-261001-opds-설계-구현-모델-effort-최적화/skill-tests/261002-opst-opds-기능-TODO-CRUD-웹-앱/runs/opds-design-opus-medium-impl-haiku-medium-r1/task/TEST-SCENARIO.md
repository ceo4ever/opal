---
template: sdlc-v2
---
# TEST-SCENARIO: TODO CRUD 웹 앱 구현

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: 워크트리 루트(`.opal-worktrees/task_001`)에서 Python 3 + pytest. 외부 서비스 없음. 계약 시나리오(S-1~S-5, S-7, S-8)는 `tests/test_todo_api.py`의 pytest fixture가 `ThreadingHTTPServer(("127.0.0.1", 0), make_handler(tmp_path/"todos.json"))`를 데몬 스레드로 띄우고 `http.client`로 실제 HTTP 요청을 보낸다(PLAN D-17). S-6·S-11은 `python -m todo_web.app --host 127.0.0.1 --port <빈 포트> --data <임시 파일>` 실제 프로세스를 쓴다.
- 공통 데이터: 시나리오마다 새 임시 `todos.json`(없음 상태)에서 시작한다.
- 대역 사용과 한계: 사용하지 않음. 모든 시나리오가 실제 소켓 HTTP 요청과 실제 파일 저장을 사용한다.
- 실행 조건: 자동 실행. S-11은 테스트 에이전트가 브라우저 자동화(Playwright)로 수행하며 사람 handoff는 없다.
- 병렬 그룹: 선언 없음(순차).

## Scenarios

| ID | 유형 | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|---|
| S-1 | contract | AC-3, AC-4, AC-10 | 빈 저장소 서버 | `POST /api/todos` (`Content-Type: application/json`, `{"title": "  Buy milk  ", "description": "2L"}`) 후 `GET /api/todos` | POST: `201`, 응답 `Content-Type`이 `application/json`으로 시작, 본문 키 집합이 정확히 `{id, title, description, completed}`, `title == "Buy milk"`(앞뒤 공백 제거), `description == "2L"`, `completed is False`, `Location == "/api/todos/{id}"`. GET: `200`, JSON 배열 길이 1이고 원소가 POST 본문과 같음 | pytest + http.client (`tests/test_todo_api.py`) | 구현 전 RED |
| S-2 | contract | AC-5, AC-6, AC-10 | TODO A(`title "A"`), B(`title "B"`) 생성 | `GET /api/todos/{A}`; `GET /api/todos/9999`; `PATCH /api/todos/{A}` `{"title": "A2", "completed": true}`; `PATCH /api/todos/{A}` `{"description": "d"}`; `GET /api/todos/{B}`; `PATCH /api/todos/9999` `{"title": "x"}` | 상세 `200`+A 객체; 없는 ID `404`+본문에 `error`; 첫 PATCH `200`, `title == "A2"`, `completed is True`, `description` 불변; 둘째 PATCH `200`, `description == "d"`, `title == "A2"` 유지; B는 생성 직후와 동일; 없는 ID PATCH `404`+`error` | pytest + http.client | 구현 전 RED |
| S-3 | contract | AC-7, AC-10 | TODO A, B 생성 | `DELETE /api/todos/{A}`; `GET /api/todos/{A}`; `GET /api/todos`; `DELETE /api/todos/{A}` 재호출 | 첫 DELETE `204`, 본문 길이 0; 이후 상세 `404`+`error`; 목록에 A 없음·B 있음; 재 DELETE `404`+`error` | pytest + http.client | 구현 전 RED |
| S-4 | contract | AC-8, AC-10 | TODO A 생성 | POST 본문 각각: `{"title": "   "}`, `{"title": "x"*121}`, `{"title": "x"*120}`, `{"title": "t", "description": "d"*2001}`, `{"title": "t", "description": "d"*2000}`, `{"description": "no title"}`, 원시 바이트 `{bad json`, `[1, 2]`; PATCH `/api/todos/{A}` 본문 각각: `{}`, `{"title": ""}`, `{"completed": "yes"}`, `{bad` | 120자 제목·2000자 설명은 `201`; 나머지 모든 요청은 `400`이며 본문이 `error` 키를 가진 JSON 객체(잘못된 JSON 2건은 `error == "invalid_json"`, 나머지는 `error == "validation_error"`); 거부 후 A는 변하지 않음 | pytest + http.client | 구현 전 RED |
| S-5 | contract | AC-9, AC-10 | TODO A 생성 | `POST /api/todos` `Content-Type: text/plain` 유효 JSON 본문; `PATCH /api/todos/{A}` Content-Type 헤더 없이 `{"title": "z"}`; `POST /api/todos` `Content-Type: application/json; charset=utf-8` `{"title": "ok"}`; `PUT /api/todos`; `DELETE /api/todos`; `POST /api/todos/{A}`; `PUT /api/todos/{A}`; `POST /health`; `GET /nope` | text/plain POST·헤더 없는 PATCH는 `415`+`error == "unsupported_media_type"`이고 A 불변; charset 포함 POST는 `201`; PUT·DELETE 컬렉션, POST·PUT 상세, POST `/health`는 `405`+`error == "method_not_allowed"`+`Allow` 헤더 존재; `GET /nope`는 `404`+`error`; 모든 오류 응답 `Content-Type`이 `application/json`으로 시작 | pytest + http.client | 구현 전 RED |
| S-6 | integration | AC-11, C-2 | 빈 포트, 존재하지 않는 임시 데이터 파일 경로 | `python -m todo_web.app --host 127.0.0.1 --port <P> --data <F>` 기동 → `/health` 응답 대기 → TODO 3건 생성, 1건 PATCH(`completed: true`), 1건 DELETE → 프로세스 종료 → 같은 명령·같은 `<F>`로 재기동 → `GET /api/todos` | 재기동 후 목록이 종료 직전 목록과 같다(2건, PATCH 반영, 삭제 항목 없음). `<F>`는 `json.load` 가능한 파일이다 | pytest + subprocess 실제 서버 프로세스 | 구현 전 RED |
| S-7 | integration | AC-11, H-1 | 빈 저장소 서버 | 스레드 20개가 동시에 `POST /api/todos`(`{"title": "t<i>"}`) 각 1회 → `GET /api/todos` → 같은 데이터 파일로 `make_handler`를 새로 만들어 띄운 두 번째 서버에서 `GET /api/todos` | 20건 모두 `201`; 첫 서버 목록 20건, `id` 20개 모두 서로 다름; 두 번째 서버(파일 재로드) 목록도 같은 20건 | pytest + http.client + threading | 구현 전 RED |
| S-8 | contract | AC-1 | `POST /api/todos` `{"title": "<b>Milk</b>", "description": "fresh"}` 생성 | `GET /` | `200`, `Content-Type`이 `text/html`로 시작; 본문에 `id="todo-list"`, `id="todo-form"`, `name="title"`, `name="description"`, `type="submit"` 존재; 생성한 제목이 `&lt;b&gt;Milk&lt;/b&gt;`로 이스케이프되어 포함되고 원문 `<b>Milk</b>`는 포함되지 않음 | pytest + http.client | 구현 전 RED |
| S-9 | regression | AC-2, C-3 | 구현 완료 코드 | 워크트리 루트에서 `python -m pytest -q` 전체 실행 | `tests/test_basic.py` 2건(`/health` 200·`{"ok": true}`, 홈 화면 `Todo Web`·`todo-form`)과 `tests/test_todo_api.py` 전부 통과, 실패 0 | pytest 전체 | 구현 후 |
| S-10 | check | C-1, C-4 | 구현 완료 코드 | `todo_web/`의 모든 import 모듈 최상위 이름이 `sys.stdlib_module_names` 또는 `todo_web`에 속하는지 검사; `git diff --name-only main...HEAD`와 작업 트리 변경 경로 확인 | 비표준 import 0건; 코드 변경 경로가 `todo_web/app.py`, `todo_web/store.py`, `tests/test_todo_api.py`와 태스크 폴더(`tasks/001-261002-opds-TODO-CRUD-웹앱/`)로 한정 | Python 스크립트 + git | 구현 후 |
| S-11 | e2e | AC-1 | S-6과 같은 방식으로 기동한 실제 서버(빈 데이터 파일) | 브라우저로 `http://127.0.0.1:<P>/` 열기 → 제목 입력에 `Walk dog`, 설명에 `park` 입력 → `Create` 클릭 → 페이지 새로고침 없이 목록 확인 → 제목을 공백만 넣고 `Create` 클릭 | 생성 후 `#todo-list` 안에 `Walk dog` 표시, 제목·설명 입력이 비워짐; 공백 제목 제출 시 `#form-error`에 비어 있지 않은 오류 문구가 표시되고 목록 항목 수 불변 | Playwright 브라우저 자동화(surface_kind `web_ui`, profile `browser`, executor `browser`, 증적: 생성 후·오류 후 스크린샷 또는 DOM 스냅샷) | 구현 후 |
