---
template: sdlc-v2
---
# TEST-SCENARIO: TODO CRUD 웹 앱 구현

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: worktree 루트(`feat/OP-TASK-001`)에서 Python 3(`python`, 표준 라이브러리) + pytest. 외부 서비스 없음.
- 공통 데이터: 시나리오마다 pytest `tmp_path` 아래 새 `todos.json` 경로(부재 상태에서 시작). 인프로세스 서버는 `ThreadingHTTPServer(("127.0.0.1", 0), make_handler(<경로>))`를 데몬 스레드로 띄우고 `http.client.HTTPConnection`으로 요청한다(임의 method·헤더·원시 본문 전송 가능). 실제 프로세스 시나리오는 `python -m todo_web.app --host 127.0.0.1 --port <빈 포트> --data <경로>`를 subprocess로 띄우고 `GET /health` 200을 최대 10초 폴링한다.
- 대역 사용과 한계: 사용하지 않음. 인프로세스 서버도 실제 `ThreadingHTTPServer`·실제 소켓·실제 파일 I/O를 사용한다. 실행 계약(C-2)과 재시작은 S-8·S-10의 실제 프로세스로, 화면 동작은 S-12의 실제 브라우저로 별도 확인한다.
- 실행 조건: 자동 실행. S-12는 실제 브라우저 자동화 수단이 필요하며 없으면 BLOCKED(H-2).
- 병렬 그룹: 선언 없음(순차).

## Scenarios

| ID | 유형 | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|---|
| S-1 | contract | AC-1, AC-2, AC-10 | 빈 데이터 파일 경로로 인프로세스 서버 기동 | `GET /health`, `GET /` | `/health`: 200, `Content-Type`이 `application/json`으로 시작, 본문 정확히 `{"ok": true}`. `/`: 200, `Content-Type`이 `text/html`로 시작, 본문에 `id="todo-form"`·`id="todo-title"`·`id="todo-description"`·`id="todo-create"`·`id="todo-list"`·`id="todo-error"` 모두 포함 | pytest 인프로세스 HTTP | 구현 전 RED |
| S-2 | integration | AC-3, AC-4, AC-10 | 빈 데이터 | ① `POST /api/todos` `{"title":"  Buy milk  ","description":"2L"}` ② `POST` `{"title":"Read"}` ③ `GET /api/todos` ④ `GET /api/todos/{①id}` ⑤ `GET /api/todos/999` | ①: 201, `Location == /api/todos/{id}`, 본문 키 집합 정확히 `{id,title,description,completed}`, `title=="Buy milk"`, `description=="2L"`, `completed is False`, `id`는 int. ②: 201, `description==""`, `completed is False`, id가 ①보다 큼. ③: 200, JSON 배열 길이 2, id 오름차순, 각 원소 4키. ④: 200, ①본문과 동일. ⑤: 404, JSON 객체에 `error` 키 | pytest 인프로세스 HTTP | 구현 전 RED |
| S-3 | integration | AC-5, AC-10 | TODO A(`title:"A", description:"a"`), B(`title:"B", description:"b"`) 생성 | ① `PATCH /api/todos/{A}` `{"completed":true}` ② `PATCH {A}` `{"title":"  A2 "}` ③ `GET {A}`, `GET {B}` ④ `PATCH /api/todos/999` `{"completed":true}` | ①: 200, `completed is True`, title·description 불변. ②: 200, `title=="A2"`, `description=="a"`, `completed is True`. ③: A는 ②본문과 동일, B는 생성 직후 본문과 완전히 동일. ④: 404, `error` 키 | pytest 인프로세스 HTTP | 구현 전 RED |
| S-4 | integration | AC-6, AC-10 | TODO A, B 생성 | ① `DELETE {A}` ② `GET {A}` ③ `GET /api/todos` ④ `DELETE {A}` 재요청 ⑤ `POST` 새 TODO C | ①: 204, 본문 0바이트. ②: 404 `error`. ③: B만 포함. ④: 404 `error`. ⑤: 201, C의 id가 A·B의 id와 모두 다름(재사용 없음) | pytest 인프로세스 HTTP | 구현 전 RED |
| S-5 | integration | AC-7, AC-10 | TODO A 1건 생성 후 데이터 파일 바이트와 목록을 기록 | `POST` 본문: `{"title":"   "}`, `{"title":"x"*121}`, `{"title":"ok","description":"d"*2001}`, `{"description":"no title"}`, `{"title":5}`, `[1,2]`, 원시 `{bad json`, 빈 본문 / `PATCH {A}` 본문: `{}`, `{"completed":"yes"}`, `{"title":""}`, `{"description":null}` / 경계 통과: `POST {"title":"x"*120}`, `POST {"title":"t","description":"d"*2000}` | 실패 요청 전부 400, JSON 객체에 `error` 키, 문법 오류·빈 본문은 `error=="invalid_json"`, 나머지는 `error=="validation_error"`. 실패 요청 전후 데이터 파일 바이트와 `GET {A}`가 동일. 경계 통과 2건은 201 | pytest 인프로세스 HTTP | 구현 전 RED |
| S-6 | integration | AC-8, AC-10 | TODO A 1건 생성 후 데이터 파일 바이트 기록 | ① `POST /api/todos` 유효 JSON + `Content-Type: text/plain` ② `PATCH {A}` 유효 JSON + `Content-Type` 헤더 없음 ③ `POST` + `Content-Type: application/x-www-form-urlencoded` ④ `POST` + `Content-Type: application/json; charset=utf-8` | ①②③: 415, `error` 키, 데이터 파일 바이트·목록 불변. ④: 201 | pytest 인프로세스 HTTP | 구현 전 RED |
| S-7 | contract | AC-9, AC-10 | TODO A 1건 생성 | `PUT /api/todos`, `PUT {A}`, `POST {A}`, `DELETE /api/todos`, `PATCH /api/todos`, `POST /health`, `OPTIONS /`, `GET /nope` | `GET /nope`만 404, 나머지는 모두 405. 모든 응답 `Content-Type`이 `application/json`으로 시작하고 본문이 `error` 키를 가진 JSON 객체 | pytest 인프로세스 HTTP | 구현 전 RED |
| S-8 | integration | AC-11, C-2 | 새 `--data` 경로(부모 디렉토리 존재), 실제 프로세스 기동 | ① 3건 POST(X, Y, Z) ② `PATCH {Y}` `{"completed":true,"description":"changed"}` ③ `DELETE {Z}` ④ `GET /api/todos` 결과 저장 ⑤ 프로세스 종료(`terminate`) ⑥ 같은 `--data`로 재기동 ⑦ `GET /api/todos` ⑧ POST 1건 | 기동 명령이 `/health` 200으로 응답(C-2). ⑦ 결과가 ④와 완전히 동일(X 원본, Y 수정값, Z 없음). ⑧의 id가 Z의 id와 다름. 데이터 파일이 유효 JSON이고 X·Y 제목을 포함 | pytest subprocess `python -m todo_web.app` | 구현 전 RED |
| S-9 | integration | AC-11 | 빈 데이터, 인프로세스 서버 | ① 20개 스레드가 동시에 서로 다른 제목으로 POST ② 20건 각각에 동시에 `PATCH {"completed":true}` ③ 서버 종료 후 같은 경로로 `make_handler` 재생성한 서버에서 `GET /api/todos` | ①: 20건 모두 201, id 20개 모두 고유. ③: 목록 20건, 제목 집합이 ①과 동일, 20건 모두 `completed is True`(유실·덮어쓰기 없음) | pytest 인프로세스 HTTP + threading | 구현 전 RED |
| S-10 | integration | AC-11 | `--data` 파일에 손상 JSON(`{not json`) 기록 후 바이트 보관 | 실제 프로세스 기동 | 프로세스가 10초 안에 exit code 2로 종료, stderr에 `invalid data file` 포함, 파일 바이트 불변(빈 상태로 덮어쓰지 않음) | pytest subprocess `python -m todo_web.app` | 구현 전 RED |
| S-11 | regression | C-3, H-1 | GREEN 구현 완료, `tests/test_basic.py` 무수정 | `git diff --exit-code main -- tests/test_basic.py` 후 `python -m pytest -q tests/test_basic.py` | diff exit 0(무수정), 기존 2개 테스트 모두 PASS(언바운드 `do_GET(DummyHandler())` 호환) | pytest + git | 구현 후 |
| S-12 | e2e | AC-1, H-2 | 실제 프로세스 서버 기동(빈 데이터), 실제 브라우저 | ① `/` 접속 ② 제목 `E2E task`, 설명 `from browser` 입력 후 Create 클릭 ③ 목록 확인 ④ 해당 항목 체크박스 클릭 후 페이지 새로고침 ⑤ Delete 클릭 | ③: `#todo-list`에 제목 `E2E task`·설명 `from browser` 항목이 나타나고 입력란이 비워짐. ④: 새로고침 후에도 체크박스 checked(서버 `GET /api/todos`에서 `completed:true`). ⑤: 항목이 목록에서 사라지고 `GET /api/todos`가 빈 배열. 콘솔 오류 없음 | 실제 브라우저 자동화(web_ui), surface_kind `web_ui`, profile `browser` | 구현 후 |
| S-13 | check | C-1 | GREEN 구현 완료 | `todo_web/`의 모든 `import`/`from` 최상위 모듈명을 `sys.stdlib_module_names` 및 `todo_web`과 대조, `git diff --name-only main`에 의존성 선언 파일(`requirements*.txt`·`pyproject.toml`·`setup.py`·`setup.cfg`·`Pipfile`) 없음 확인 | 비표준 모듈 0건, 의존성 파일 추가·변경 0건 | 정적 검사(python 스크립트 + git) | 구현 후 |
