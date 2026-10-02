---
template: sdlc-v2
---
# TEST-SCENARIO: TODO CRUD 웹 앱

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: worktree 루트(`feat/OP-TASK-001`)에서 `python`(3.14)과 `python -m pytest`(9.x)를 사용한다. 통합 시나리오는 실제 서버 프로세스를 `python -m todo_web.app --host 127.0.0.1 --port <빈 포트> --data <임시 디렉토리>/todos.json`으로 띄우고, `GET /health`가 200을 줄 때까지 최대 10초 기다린 뒤 `http.client`로 호출한다. 종료는 terminate→wait.
- 공통 데이터: 시나리오(또는 pytest 모듈)마다 새 임시 데이터 파일을 쓴다. 저장소 상태를 다른 시나리오와 공유하지 않는다.
- 대역 사용과 한계: 사용하지 않음. 모든 API·영속성 시나리오는 실제 서버 프로세스와 실제 파일을 쓴다.
- 실행 조건: 자동 실행. S-2~S-7은 W-1이 `tests/test_todo_api.py`에 pytest로 작성하며 테스트 이름에 S-ID를 넣는다(예: `test_s2_create_and_read`). S-10은 OPAL venv의 `~/.opal/.venv/bin/python` + Playwright headless Chromium(설치 확인됨)으로 TEST 단계에서 실행하며, 스크립트·증거는 태스크 폴더 `run/` 아래에 둔다(앱 런타임 의존성이 아님 — C-1과 무관).
- 병렬 그룹: 선언 없음(순차).

## Scenarios

| ID | 유형 | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|---|
| S-1 | integration | AC-1 | 빈 데이터 파일 경로, 빈 포트 | 실행 계약 명령으로 서버 기동 후 `GET /health`, `GET /` | 프로세스가 기동해 `/health`가 `200`, `Content-Type`이 `application/json`으로 시작, 본문 `{"ok": true}`. `/`는 `200`, `Content-Type`이 `text/html`로 시작, 본문에 `id="todo-form"` 폼, `name="title"` input, `name="description"` textarea, `type="submit"` 버튼, `id="todo-list"` 목록 영역이 있음 | pytest + 실서버 서브프로세스 + `http.client` | 구현 후 |
| S-2 | integration | AC-2 | 빈 저장소 | `POST /api/todos` `{"title":"Buy milk","description":"2L"}`(`Content-Type: application/json`) → `GET /api/todos` → `GET /api/todos/{id}` → `GET /api/todos/999999` | POST `201`, 본문 키 집합이 정확히 `id,title,description,completed`, `completed == false`, `id`는 정수, `Location == /api/todos/{id}`. 목록 `200`·JSON 배열에 같은 객체 1건. 상세 `200`·같은 객체. 없는 ID `404`·JSON 본문에 `error` | pytest + 실서버 | 구현 전 RED |
| S-3 | integration | AC-3 | TODO A·B 생성 | `PATCH /api/todos/{A}` `{"completed": true}` → `PATCH /api/todos/{A}` `{"title":"New","description":"D2"}` → `GET` A·B → `PATCH /api/todos/999999` `{"completed": true}` | 1차 PATCH `200`, `completed`만 `true`로 바뀌고 title·description 그대로. 2차 PATCH `200`, title·description 변경, `completed`는 `true` 유지. B는 생성 직후 객체와 동일. 없는 ID `404`·`error` 필드 | pytest + 실서버 | 구현 전 RED |
| S-4 | integration | AC-4 | TODO A·B 생성 | `DELETE /api/todos/{A}` → `GET /api/todos/{A}` → `GET /api/todos` → `DELETE /api/todos/{A}` 재호출 | 1차 DELETE `204`, 본문 0바이트. 상세 `404`. 목록에 A 없음, B는 남음. 재삭제 `404`·`error` 필드 | pytest + 실서버 | 구현 전 RED |
| S-5 | integration | AC-5, H-3 | TODO 1건 생성(id=X) | 다음 요청을 각각 보낸다: ① POST title `"   "` ② POST title 121자 ③ POST title 120자 ④ POST description 2001자 ⑤ POST description 2000자 ⑥ POST title `"  Trim me  "` ⑦ POST 본문 `{bad json` ⑧ POST `Content-Type: text/plain` 유효 JSON 본문 ⑨ PATCH X `Content-Type: text/plain` ⑩ PATCH X `{"title": ""}` ⑪ PATCH X `{}` ⑫ POST title 정수 `123` ⑬ PATCH X `{"completed": "yes"}` ⑭ `PUT /api/todos` ⑮ `POST /api/todos/X` ⑯ `DELETE /api/todos` ⑰ `HEAD /api/todos` ⑱ `OPTIONS /api/todos/X` ⑲ 임의 method `FOO /api/todos` ⑳ `GET /api/unknown` | ①②④⑦⑩⑪⑫⑬ `400`, ③⑤ `201`, ⑥ `201`이며 저장 title이 `"Trim me"`, ⑧⑨ `415`, ⑭⑮⑯⑰⑱⑲ `405`(⑰은 본문 없음, 나머지는 JSON), ⑳ `404`. 본문이 있는 모든 오류 응답은 `Content-Type`이 `application/json`으로 시작하고 JSON 객체에 `error` 키가 있음. ⑩⑬ 뒤 `GET X`가 수정 전 객체와 동일(실패한 PATCH는 아무것도 바꾸지 않음) | pytest + 실서버(`http.client.request`로 임의 method 전송) | 구현 전 RED |
| S-6 | integration | AC-6 | 빈 데이터 파일 | 서버 1차 기동 → A·B·C 생성, B를 `{"completed": true}`로 PATCH, C 삭제 → 서버 종료 → 같은 `--data`로 2차 기동 → `GET /api/todos` → D 생성 | 2차 기동 후 목록이 1차 종료 직전 목록과 정확히 같음(A 원본, B `completed: true`, C 없음). 데이터 파일은 유효한 JSON. D의 `id`는 A·B·C 어느 것과도 다름(삭제된 ID 재사용 없음) | pytest + 실서버 2회 기동 | 구현 전 RED |
| S-7 | integration | AC-6, H-1 | 빈 데이터 파일, 서버 1개 | 스레드 20개가 동시에 `POST /api/todos`(서로 다른 title) → 이어서 스레드 10개가 생성된 항목 중 서로 다른 10건에 동시에 `PATCH {"completed": true}` → 서버 재기동 → `GET /api/todos` | POST 20건 모두 `201`, `id` 20개가 서로 다름. PATCH 10건 모두 `200`. 재기동 후 목록 길이 20, title 집합이 보낸 20개와 같음, `completed: true`가 정확히 PATCH한 10건 | pytest + 실서버 + `threading` | 구현 전 RED |
| S-8 | regression | C-2, H-2 | 구현 완료 후 worktree | `python -m pytest -q tests/test_basic.py` 실행, `git diff --exit-code main -- tests/test_basic.py` 실행 | pytest 2 passed(실패 0). git diff exit 0(기존 테스트 파일 무수정) | pytest + git | 구현 후 |
| S-9 | check | C-1, C-3 | 구현 완료 후 worktree | `todo_web/` 아래 `.py` 파일을 `ast`로 파싱해 모든 import의 최상위 모듈명을 수집, `sys.stdlib_module_names`·`__future__`·`todo_web`과 대조. `git status --porcelain`과 `git diff --name-only main` 결과에서 변경 경로 목록 수집 | 표준 라이브러리 외 모듈 0건. 저장소에 의존성 선언 파일(`requirements*.txt`·`pyproject.toml`·`setup.py`·`setup.cfg`) 신규 없음. 변경 경로가 `todo_web/app.py`, `todo_web/store.py`, `tests/test_todo_api.py`, `tasks/001-261002-opds-TODO-CRUD-웹앱/` 하위로만 구성됨 | python 스크립트 + git | 구현 후 |
| S-10 | e2e | AC-1 | 실서버 기동(빈 데이터 파일) | 브라우저로 `/` 열기 → 제목 `E2E <b>task</b>`, 설명 `from browser` 입력 후 Create 클릭 → 목록 확인 → 해당 항목 완료 체크박스 클릭 → 삭제 버튼 클릭 → 페이지 새로고침 | 아래 §S-10 assertion 전부 충족 | Playwright headless Chromium(`~/.opal/.venv/bin/python`) + 실서버 + `http.client` 교차 확인 | 구현 후 |

### S-10

- `surface_kind`: `hybrid` / `profile`: `hybrid`(브라우저 조작 + API 교차 확인) / `actors`: `agent`
- `steps[]`:
  - `st-1` (`browser`): `GET /` 로드, `#todo-form`·`input[name=title]`·`textarea[name=description]`·`button[type=submit]`·`#todo-list`가 보이는지 확인
  - `st-2` (`browser`): 제목·설명 입력 후 submit 버튼 클릭, `#todo-list`에 항목이 나타날 때까지 대기(최대 5초)
  - `st-3` (`browser`): 그 항목의 완료 체크박스 클릭 후 0.5초 대기
  - `st-4` (`api`): `GET /api/todos`로 해당 항목 `completed: true` 확인
  - `st-5` (`browser`): 그 항목의 삭제 버튼 클릭, 목록에서 사라질 때까지 대기
  - `st-6` (`browser`): 새로고침 후 목록 확인, `GET /api/todos` 빈 배열 확인
- `assertions[]`:
  - `a-1`: 초기 화면에 폼·제목 입력·설명 입력·생성 버튼·목록 영역이 모두 보인다
  - `a-2`: 생성 후 목록에 `E2E <b>task</b>`가 문자열 그대로(태그로 해석되지 않고, 목록 영역 안 `b` 요소 0개) 표시된다
  - `a-3`: 체크박스 클릭 후 API 상 해당 항목 `completed`가 `true`다
  - `a-4`: 삭제 후 화면 목록과 API 목록 모두에서 항목이 사라지고 새로고침 후에도 없다
  - `a-5`: 전 과정에서 브라우저 console error 0건
- `required_evidence[]`: `screenshot-after-create`, `screenshot-after-delete`, `console-log`, `api-list-after-toggle`
