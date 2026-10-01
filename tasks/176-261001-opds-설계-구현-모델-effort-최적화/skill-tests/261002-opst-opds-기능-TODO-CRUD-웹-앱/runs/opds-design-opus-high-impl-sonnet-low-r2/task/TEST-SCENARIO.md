---
template: sdlc-v2
---
# TEST-SCENARIO: TODO CRUD 웹 앱 구현

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: worktree 루트(`.opal-worktrees/task_1`)를 cwd로 하는 Python 3(표준 라이브러리) + pytest. 외부 서비스 없음.
- 공통 데이터: 각 시나리오는 pytest `tmp_path` 아래 새 `todos.json` 경로를 쓴다(시작 시 파일 없음, S-9만 예외). 시나리오 간 데이터 공유 없음.
- 서버 기동 방식: in-process 시나리오는 `ThreadingHTTPServer(("127.0.0.1", 0), make_handler(<tmp>/todos.json))`를 데몬 스레드로 띄우고 `http.client`로 요청한다(PLAN D14). subprocess 시나리오(S-7·S-9·S-11)는 `python -m todo_web.app --host 127.0.0.1 --port <빈 포트> --data <tmp>/todos.json`으로 띄운다. 빈 포트는 `socket.bind(("127.0.0.1", 0))`로 얻는다. 기동 대기는 `GET /health` 폴링(최대 5초).
- 계약 테스트 위치: `tests/test_todo_api.py`(W-1, RED 작성). 각 S-ID는 이름에 S-ID를 포함한 pytest 테스트(예 `test_s1_create_todo`)로 구현하며 하나의 S가 여러 assertion을 가질 수 있다.
- 대역 사용과 한계: 사용하지 않음. 모든 API 검증은 실제 HTTP 소켓을 통한다.
- 실행 조건: 자동 실행. S-11은 브라우저 자동화 실행기(Playwright 등)가 필요하며, 실행기가 없으면 `executor_unavailable`로 기록하고 PASS로 대체하지 않는다(PLAN H-2). 사람 handoff 없음.
- 병렬 그룹: S-1, S-2, S-3, S-4, S-5, S-6, S-8

## Scenarios

| ID | 유형 | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|---|
| S-1 | contract | AC-3 | 빈 저장소 in-process 서버 | `POST /api/todos` `Content-Type: application/json` 본문 `{"title": "  Buy milk  ", "description": "2L"}` → 이어서 `{"title": "Done task", "completed": true}` 생성 | 첫 응답 `201`, `Content-Type`이 `application/json`으로 시작, `Location: /api/todos/1`, 본문이 정확히 `{"id": 1, "title": "Buy milk", "description": "2L", "completed": false}`(제목 앞뒤 공백 제거). 둘째 응답 `201`, `id` 2, `description` `""`, `completed` `true`, `Location: /api/todos/2` | pytest + `http.client`, in-process 서버 | 구현 전 RED |
| S-2 | contract | AC-4 | in-process 서버에 TODO 2건 생성(id 1, 2) | `GET /api/todos`, `GET /api/todos/2`, `GET /api/todos/999`, `GET /api/todos/abc` | 목록 `200`, JSON 배열 길이 2, id 오름차순 `[1, 2]`, 각 원소 키 집합이 정확히 `{id, title, description, completed}`. 상세 `200`, 생성 응답과 같은 객체. `999`·`abc`는 `404`이고 본문 JSON 객체의 `error` 값이 `"not_found"` | pytest + `http.client`, in-process 서버 | 구현 전 RED |
| S-3 | contract | AC-5 | in-process 서버에 TODO A(id 1)·B(id 2) 생성 | `PATCH /api/todos/1` `{"title": "New"}` → `PATCH /api/todos/1` `{"completed": true, "description": "d2"}` → `GET /api/todos` → `PATCH /api/todos/999` `{"title": "x"}` → `PATCH /api/todos/1` `{"unknown": 1}` | 첫 PATCH `200`, 본문 title `"New"`·나머지 필드 원래 값. 둘째 PATCH `200`, `completed` `true`·`description` `"d2"`·title `"New"` 유지. 목록에서 B는 생성 직후 객체와 완전히 같음. 없는 ID `404`(`error` `"not_found"`). 알려진 필드가 없는 본문 `400`(`error` `"validation_error"`)이고 A는 변하지 않음 | pytest + `http.client`, in-process 서버 | 구현 전 RED |
| S-4 | contract | AC-6 | in-process 서버에 TODO 2건 생성(id 1, 2) | `DELETE /api/todos/1` → `GET /api/todos/1` → `GET /api/todos` → `DELETE /api/todos/1` | 첫 DELETE `204`, 응답 본문 0바이트. 이후 상세 `404`, 목록은 id 2 한 건만. 두 번째 DELETE `404`(`error` `"not_found"`) | pytest + `http.client`, in-process 서버 | 구현 전 RED |
| S-5 | contract | AC-7 | 빈 저장소 in-process 서버 | `POST /api/todos`에 차례로: 본문 `{bad json`; 빈 본문; `[]`; `{"title": "   "}`; title 121자; title 120자; description 2001자(title 정상); description 2000자; `{"title": 5}`. 이어서 120자 제목으로 생성된 TODO(id 1)에 `PATCH` `{"completed": "yes"}`, `PATCH` `{"title": null}` | `{bad json`·빈 본문 → `400` `error` `"invalid_json"`. `[]`·공백 제목·121자 제목·2001자 설명·숫자 제목·문자열 completed·null 제목 → `400` `error` `"validation_error"`. 120자 제목·2000자 설명 → `201`. 모든 실패 요청 뒤 `GET /api/todos` 건수는 성공한 생성 수(2)와 같고 PATCH 대상은 변하지 않음 | pytest + `http.client`, in-process 서버 | 구현 전 RED |
| S-6 | contract | AC-7 | 빈 저장소 in-process 서버, TODO 1건 생성(id 1) | `POST /api/todos` `Content-Type: text/plain`(본문은 유효한 JSON); `Content-Type` 헤더 없이 `POST`; `PATCH /api/todos/1` `Content-Type: text/plain`; `POST /api/todos` `Content-Type: application/json; charset=utf-8`; `PUT /api/todos`; `DELETE /api/todos`; `POST /api/todos/1`; `PUT /api/todos/1`; `POST /health`; `TRACE /api/todos`; `GET /nope` | text/plain POST·헤더 없는 POST·text/plain PATCH → `415` `error` `"unsupported_media_type"`(PATCH 대상 불변). charset 파라미터 포함 POST → `201`. `PUT /api/todos`·`DELETE /api/todos` → `405`, `Allow: GET, POST`. `POST /api/todos/1`·`PUT /api/todos/1` → `405`, `Allow: GET, PATCH, DELETE`. `POST /health` → `405`, `Allow: GET`. `TRACE /api/todos` → `405`(501 아님). `GET /nope` → `404`. 위 모든 오류 응답은 `Content-Type`이 `application/json`으로 시작하고 본문이 문자열 `error` 필드를 가진 JSON 객체 | pytest + `http.client`, in-process 서버 | 구현 전 RED |
| S-7 | integration | AC-8, AC-1, C-1 | 존재하지 않는 `<tmp>/todos.json` | 실행 명령으로 서버 기동 → `GET /health` → TODO 3건 생성(id 1~3) → id 2를 `PATCH {"completed": true}` → id 3 `DELETE` → 목록 L1 기록 → `terminate()`·`wait()` → 같은 명령·같은 `--data`로 재기동 → 목록 L2 → TODO 1건 생성 | `/health`는 `200`, 본문 정확히 `{"ok": true}`. 종료 후 데이터 파일이 존재하고 `json.load` 가능. L2 == L1(id 1·2만, id 2 `completed: true`, id 3 없음). 재기동 후 생성 TODO의 id는 `4`(삭제된 3 재사용 없음) | pytest + `subprocess`(`sys.executable -m todo_web.app`) + `urllib.request`, 실제 프로세스 2회 기동 | 구현 전 RED |
| S-8 | integration | AC-8 | 빈 저장소 in-process 서버 | 20개 스레드가 동시에 `POST /api/todos`(title `t0`~`t19`) → 완료 후 `GET /api/todos` → 서버 종료 없이 데이터 파일을 `json.load` | 20개 응답 모두 `201`, id 집합이 `{1..20}`로 중복 없음. 목록 20건, 제목 집합 `{t0..t19}`. 데이터 파일의 `todos`도 같은 20건(동시 저장 중 항목 유실 없음) | pytest + `threading` + `http.client`, in-process 서버 | 구현 전 RED |
| S-9 | integration | AC-8 | `<tmp>/todos.json`에 `{not json` 기록(손상 파일) | 실행 명령으로 서버 기동, 최대 5초 대기 | 프로세스가 5초 안에 스스로 종료하고 exit code `1`, stderr에 `cannot load data file` 포함, 데이터 파일 내용은 기동 전과 바이트 동일(손상 파일을 덮어써 기존 데이터를 잃지 않음). 5초 안에 종료하지 않으면 FAIL 후 kill | pytest + `subprocess`, 실제 프로세스 | 구현 전 RED |
| S-10 | regression | C-3, H-1, AC-1 | 기존 `tests/test_basic.py` 무수정 | `git diff --quiet main -- tests/test_basic.py` 후 `python -m pytest -q tests/test_basic.py` | diff 없음(exit 0). 2 passed — `DummyHandler` unbound `do_GET`으로 `/health` `200 {"ok": true}`와 `/` 본문 `Todo Web`·`todo-form` 유지 | pytest, worktree | 구현 후 |
| S-11 | e2e | AC-2, H-2 | 실행 명령으로 기동한 서버(빈 데이터) | 브라우저로 `http://127.0.0.1:<PORT>/` 열기 → 제목 `E2E title`, 설명 `E2E desc` 입력 → Create 클릭 → 목록 확인 → 페이지 새로고침 → 제목 비우고(공백만) Create 클릭 | 첫 화면에 제목 입력·설명 입력·Create 버튼·목록 영역이 보임. 생성 후 폼 입력이 비워지고 `#todo-list`에 `E2E title` 항목(상태 `open`)이 나타남. 새로고침 후에도 항목 유지. 공백 제목 제출 시 `#form-error`에 비어 있지 않은 메시지가 보이고 목록 항목 수는 1 그대로 | 브라우저 자동화(Playwright 등) 실제 브라우저, subprocess 서버. 실행기 부재 시 `executor_unavailable` | 구현 후 |
| S-12 | check | AC-2, H-2 | 구현 완료 worktree | in-process 또는 subprocess 서버에 `GET /` 후 본문 검사, `todo_web/app.py` 소스 검사 | `200`, `Content-Type`이 `text/html`로 시작. 본문에 `id="todo-form"`, `name="title"`, `name="description"`, `type="submit"`, `id="todo-list"`, `id="form-error"`, `/api/todos` 호출 스크립트가 있음. `todo_web/app.py`에 `innerHTML` 문자열이 없음 | pytest 또는 셸 검사 | 구현 후 |
| S-13 | check | C-2 | 구현 완료 worktree | `todo_web/*.py`의 import를 `ast`로 수집해 `sys.stdlib_module_names`와 패키지 내부(`todo_web`) 외 모듈이 있는지 검사, 저장소 루트에 `requirements*.txt`·`pyproject.toml`·`setup.py`·`Pipfile` 신규 존재 여부 확인 | 표준 라이브러리·`todo_web` 외 import 0건, 의존성 선언 파일 0건 | Python 스크립트 | 구현 후 |
| S-14 | check | C-4, C-3 | 구현 완료 worktree | `git diff --name-only main...HEAD`와 `git status --porcelain`으로 변경 경로 수집 → `python -m pytest -q` 전체 실행 | 변경 경로가 `todo_web/app.py`, `todo_web/store.py`, `tests/test_todo_api.py`, `tasks/001-261002-opds-TODO-CRUD-웹앱-구현/**`로 한정. 전체 pytest exit 0(기존 2건 포함 전부 passed) | git + pytest, worktree | 구현 후 |

### S-11

- `surface_kind`: `web_ui`
- `profile`: `browser`
- `actors`: `user`, `agent`
- `steps[]`:
  - `step-1` (`browser`): `/` 열기, 폼·목록 영역 확인
  - `step-2` (`browser`): 제목·설명 입력 후 Create 클릭
  - `step-3` (`browser`): `#todo-list` 항목 확인
  - `step-4` (`browser`): 새로고침 후 항목 재확인
  - `step-5` (`browser`): 공백 제목 제출 후 `#form-error`·항목 수 확인
- `assertions[]`:
  - `a-form-visible` — expected: 제목 입력·설명 입력·Create 버튼·목록 영역이 모두 렌더됨
  - `a-created-listed` — expected: `#todo-list`에 `E2E title` 텍스트 항목 1건, 상태 `open`
  - `a-form-cleared` — expected: 생성 후 제목·설명 입력값이 빈 문자열
  - `a-persist-reload` — expected: 새로고침 후 `E2E title` 항목 유지
  - `a-error-shown` — expected: 공백 제목 제출 시 `#form-error` 텍스트 비어 있지 않음, 항목 수 1
- `required_evidence[]`: `screenshot-after-create`, `dom-snapshot-todo-list`, `screenshot-error`
