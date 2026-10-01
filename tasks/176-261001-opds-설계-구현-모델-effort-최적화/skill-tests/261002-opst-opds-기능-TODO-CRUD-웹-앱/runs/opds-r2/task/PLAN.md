---
template: sdlc-v2
---
# PLAN: TODO CRUD 웹 앱 구현

> 입력: [TASK.md](TASK.md)

## Approach
기존 `todo_web/app.py`의 표준 라이브러리 `ThreadingHTTPServer` 구조와 실행 인자(`--host`·`--port`·`--data`)를 유지하고, 그 위에 (1) `--data` JSON 파일을 단일 소유하는 저장 모듈 `todo_web/store.py`와 (2) 경로·method 라우팅, 요청 검증, JSON 오류 응답, API를 사용하는 HTML 화면을 추가한다. 공개 동작은 RED-first로 먼저 고정한다 — 구현자와 다른 주체(`opal-test-agent` red mode)가 실제 서버 프로세스를 띄워 HTTP로 검증하는 테스트 `tests/test_todo_api.py`를 먼저 작성해 실패를 관찰한 뒤, 구현 워커가 GREEN으로 만든다. 범위는 TASK AC-1~AC-8이며 인증·외부 DB·배포·요구서 밖 기능(검색·정렬·화면의 수정/삭제 UI 등)은 만들지 않는다.

## Findings

### 직접 변경
- `todo_web/app.py`: 현재 `/health`·`/`만 응답하고 `do_POST`·`do_PATCH`·`do_DELETE`가 모두 `404 not_found`를 반환한다(`todo_web/app.py:72-79`). `make_handler`는 `data_path`를 클래스 속성으로만 붙이고 쓰지 않는다(`todo_web/app.py:81`). 라우팅·검증·저장 연결·화면을 여기서 구현한다. 모듈 `@header` description의 "CRUD is intentionally unimplemented" 문구도 사실과 달라지므로 같은 파일에서 갱신한다.
- `todo_web/store.py`: 신규. `--data` JSON 파일 로드·원자 저장·ID 발급을 소유한다.
- `tests/test_todo_api.py`: 신규. 실제 서버 프로세스 대상 HTTP 회귀 테스트(RED-first).

### 회귀 확인
- `tests/test_basic.py`: `make_handler(...)`가 반환한 클래스의 `do_GET`을 **인스턴스가 아닌 `DummyHandler`를 `self`로 넘겨 unbound 호출**한다(`tests/test_basic.py:39-44`, `:47-57`). `DummyHandler`는 `path`·`send_response`·`send_header`·`end_headers`·`wfile`만 갖고, `headers`는 응답 헤더 기록용 dict다. 따라서 `GET /health`·`GET /` 경로는 handler 클래스의 다른 메서드·속성이나 요청 헤더·본문을 사용하면 안 된다(H-1). 화면 본문에는 `Todo Web`과 `todo-form` 문자열이 계속 있어야 한다.

### code-scan 결과
`code-scan domain todo-web` (`.opal/code-scan.json` `headerSource: inline`) 결과:

| 파일 | domain | layer | exports | depends |
|---|---|---|---|---|
| todo_web/app.py | todo-web | application | `main`, `make_handler` | depends on: (none) / depended by: (none) — `code-scan depends todo_web.app` |
| todo_web/__init__.py | todo-web | application | (없음) | — |
| tests/test_basic.py | todo-web | test | (없음) | — |

신규 `todo_web/store.py`는 domain `todo-web`·layer `application`으로, `tests/test_todo_api.py`는 domain `todo-web`·layer `test`로 `@header`를 단다. 변경 후 `todo_web/app.py`의 depends에 `todo_web.store`가 생긴다.

### 문서 갱신
없음. 프로젝트 레지스트리(docs/PROJECT.md)의 구조표(웹 앱 = todo_web·tests, Python 3 표준 라이브러리·pytest)와 프로젝트 PM 프로필의 검토 기준은 구현 후에도 사실이 그대로다.

### 미확인 가정
- H-1, H-2 (아래 Risks).

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| D-1. 모듈 구성 | `todo_web/store.py`에 `TodoStore`·`TodoStoreError`를 둔다. `todo_web/app.py`는 `make_handler(data_path)` 안에서 `TodoStore(data_path)`를 1회 생성해 클로저로 캡처하고, 모든 `do_*`는 모듈 수준 함수 `_route(handler, method, store)`에 위임한다. `_route`는 `handler.path`·`handler.headers`·`handler.rfile`·`send_response`·`send_header`·`end_headers`·`wfile`만 사용한다. `make_handler`의 공개 시그니처와 `main`은 유지한다. | 저장 책임 분리. unbound 호출(H-1)에서도 `self`의 다른 속성 없이 동작해야 한다. |
| D-2. 라우트 표 | 정확 일치 경로만 인정한다(쿼리스트링은 무시, 끝 `/` 붙은 경로는 별도 경로로 404): `/` → GET, `/health` → GET, `/api/todos` → GET·POST, `/api/todos/{id}` → GET·PATCH·DELETE. `{id}`는 정규식 `[1-9][0-9]*`(양의 10진 정수)만 인정하고 그 외(`abc`, `0`, `-1`, `01`)는 경로 불일치로 404 `not_found`. | 요구서 API 목록을 그대로 경로 계약으로 고정. |
| D-3. 판정 순서와 상태 코드 | ① 경로 불일치 → `404 not_found`(method 무관) ② 경로는 맞고 method 미지원 → `405 method_not_allowed` + `Allow` 헤더(해당 경로 허용 method를 `, `로 연결) ③ POST·PATCH에서 Content-Type 불일치 → `415 unsupported_media_type` ④ 본문 JSON 파싱 실패 → `400 invalid_json` ⑤ `/api/todos/{id}` 대상 ID 없음 → `404 not_found` ⑥ 필드 검증 실패 → `400 validation_error`. 표준 라이브러리가 `do_<METHOD>`가 없는 method에 `501`을 보내지 않도록 handler 클래스에 `__getattr__`을 정의해 `do_`로 시작하는 이름이면 해당 method로 `_route`를 호출하는 함수를 반환하고, 그 외 이름은 `AttributeError`를 그대로 올린다. 이로써 `PUT`·`HEAD`·`OPTIONS`·임의 method도 ①②를 따른다. | 요구서: 미지원 method 405, 잘못된 Content-Type 415, 잘못된 JSON·검증 실패 400, 없는 ID 404. 순서를 고정해 구현자 선택을 없앤다. |
| D-4. 오류 응답 형식 | 모든 오류 응답은 `Content-Type: application/json; charset=utf-8`, 본문 `{"error": "<code>", "message": "<사람이 읽는 설명>"}`. `<code>`는 `not_found`·`method_not_allowed`·`unsupported_media_type`·`invalid_json`·`validation_error`·`storage_error` 6종 폐쇄 목록. | 요구서: 오류 응답은 최소한 `error` 필드를 가진 JSON 객체. 기존 `{"error": "not_found"}` 관례 유지. |
| D-5. Content-Type 판정 | 요청 헤더 `Content-Type`에서 `;` 앞 media type을 공백 제거·소문자화한 값이 정확히 `application/json`이어야 한다(`charset` 등 파라미터 허용). 헤더 부재·다른 값은 415. GET·DELETE는 Content-Type을 검사하지 않는다. | 요구서: 쓰기 요청은 `application/json`만 받는다. |
| D-6. 본문 읽기와 JSON 판정 | `Content-Length` 정수만큼 `rfile`에서 읽는다. 헤더 부재는 길이 0으로 본다. 정수가 아니거나 음수, 본문이 UTF-8로 디코드되지 않음, 빈 본문, `json.loads` 실패는 모두 `400 invalid_json`. 파싱 결과가 JSON 객체(dict)가 아니면 `400 validation_error`. | 잘못된 본문을 400 한 가지로 수렴. |
| D-7. 필드 검증 | 공통: `title`은 `str`이어야 하고 `strip()` 결과가 비어 있지 않으며 그 길이가 120자 이하(`len` 기준). 저장값은 `strip()` 결과. `description`은 `str`이고 길이 2000자 이하(`len` 기준). 저장값은 원문 그대로. `completed`는 JSON boolean이어야 한다(`type(v) is bool`, `0`/`1`/문자열 거부). 알 수 없는 필드와 본문의 `id`는 무시한다. POST: `title` 필수, `description` 선택(없으면 `""`), `completed` 선택(없으면 `false`). PATCH: `title`·`description`·`completed` 중 하나 이상 필수(없으면 400), 제공된 필드만 같은 규칙으로 검증해 변경. 검증은 전부 통과해야 적용된다(부분 적용 없음). | 요구서 길이·공백 규칙. 타입 경계를 고정해 구현자 선택 제거. |
| D-8. TODO 객체와 목록 | 응답 TODO 객체는 정확히 `{"id": <int>, "title": <str>, "description": <str>, "completed": <bool>}`. `GET /api/todos`는 id 오름차순 배열. | 요구서 필드 4종. |
| D-9. 성공 응답 | POST → `201`, 본문 생성 객체, `Location: /api/todos/{id}`. GET 목록·상세, PATCH → `200`, JSON. DELETE → `204`, 본문 없음, `Content-Length`·`Content-Type` 헤더를 보내지 않는다. | 요구서 상태 코드. 204 본문 금지. |
| D-10. ID 발급 | ID는 1부터 시작하는 정수이며 저장 파일의 `next_id`로 발급하고, 삭제된 ID는 재사용하지 않는다. | 삭제 후 같은 ID가 다른 항목으로 되살아나 "삭제 후 사라짐"이 흐려지는 것을 막는다. |
| D-11. 파일 형식과 로드 | 저장 형식은 `{"next_id": <int>, "todos": [<TODO 객체>, ...]}`(UTF-8, `ensure_ascii=False`, indent 2). 로드 규칙: 파일 없음 또는 공백뿐인 파일 → 빈 저장소(`next_id` 1, 파일은 첫 변경 때 생성). JSON 배열 → 그 배열을 `todos`로, `next_id`=max(id)+1(빈 배열이면 1). `todos` 키를 가진 객체 → 그 값 사용, `next_id`가 없거나 max(id) 이하이면 max(id)+1. 그 밖의 형식·JSON 파싱 실패 → `TodoStoreError`를 올리고 파일은 수정하지 않는다. `main`은 `TodoStoreError`를 잡아 `error: <메시지>`를 stderr에 쓰고 종료 코드 1을 반환한다. | 사용자 데이터 파일을 손상시키지 않고, 미리 만들어진 빈 파일·`[]` 시드도 받아들인다. |
| D-12. 저장과 동시성 | `TodoStore`는 메모리 상태를 단일 진실로 갖고 `threading.Lock` 하나로 모든 조회·변경을 직렬화한다. 변경(create/update/delete)은 잠금 안에서 새 상태 사본을 만들고 → `<data>.tmp`(같은 디렉토리, 파일명 = 원본 파일명 + `.tmp`)에 쓰고 `flush`·`os.fsync` → `os.replace`로 원본을 교체한 뒤 → 성공했을 때만 메모리 상태를 교체한다. 쓰기 중 `OSError`면 메모리 상태는 그대로 두고 `TodoStoreError`를 올리며, 라우터는 이를 `500 storage_error`로 응답한다. 저장은 매 변경마다 전체 상태를 쓴다. | 요구서: 재시작 후 유지, 저장 중 다른 항목 유실 금지. 원자 교체로 중간 상태 파일이 남지 않는다. `.gitignore`의 `*.json.tmp`와 일치. |
| D-13. 화면 | `GET /`는 `text/html; charset=utf-8` 단일 HTML을 반환한다. 제목 `Todo Web`(`<title>`·`<h1>`), `<form id="todo-form">` 안에 `<input id="title" name="title" maxlength="120" required>`·`<textarea id="description" name="description" maxlength="2000">`·`<button type="submit" id="create-button">Create</button>`, 오류 표시 `<p id="form-error" role="alert">`, 목록 영역 `<ul id="todo-list" aria-label="Todo list">`. 인라인 `<script>`가 로드 시 `GET /api/todos`로 목록을 그리고, 제출 시 `fetch('/api/todos', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({title, description})})` 후 201이면 입력을 비우고 목록을 다시 그리며, 실패면 응답 `message`를 `#form-error`에 표시한다. 각 항목은 `<li data-id="{id}">` 안에 제목·설명·완료 여부(`done`/`open` 텍스트)를 `textContent`로만 넣는다(`innerHTML`에 사용자 데이터 금지). 외부 스크립트·CSS·폰트를 불러오지 않는다. | 요구서 화면 요소 4종 + API 사용 방식. XSS 방지. 수정/삭제 UI는 요구 밖이라 만들지 않는다. |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. RED 테스트 작성 | opal-test-agent (red mode) | `tests/test_todo_api.py` | TEST-SCENARIO의 `구현 전 RED` 시나리오를 pytest로 작성한다. 각 테스트는 `tmp_path`의 데이터 파일과 빈 포트로 `sys.executable -m todo_web.app --host 127.0.0.1 --port <p> --data <file>`을 subprocess로 띄우고 `/health` 응답을 기다린 뒤 `http.client`로 요청한다(표준 라이브러리만). 종료 시 프로세스를 terminate·wait한다. 공개 HTTP 동작만 검증하고 `todo_web` 내부를 import하지 않는다. | 없음 | P1 | AC-1, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, C-2 |
| W-2. 저장소와 HTTP 라우팅·화면 구현 | opal-be-agent | `todo_web/store.py`, `todo_web/app.py` | D-1~D-13 그대로 구현한다. `store.py`는 `TodoStore(path)`(로드 D-11), `list()`, `get(id)`, `create(fields)`, `update(id, fields)`, `delete(id)`(D-10·D-12)와 `TodoStoreError`를 제공하고 `@header`를 단다. `app.py`는 `_route`·라우트 표·검증·오류 응답·`__getattr__`·화면 HTML/JS를 구현하고 `@header` description·exports를 사실대로 갱신한다. 외부 패키지 import 금지. `tests/`는 수정하지 않는다. | W-1 | P2 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, C-1, C-2, C-3 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. 기존 테스트는 `do_GET`을 실제 handler 인스턴스가 아닌 `DummyHandler`로 unbound 호출한다 | `tests/test_basic.py`의 `/health`·`/` 테스트(C-2) | GET 경로가 `self._xxx` 메서드나 클래스 속성·요청 헤더에 의존하면 `AttributeError`로 기존 테스트가 깨진다 | D-1: 저장소는 클로저, 처리 로직은 모듈 수준 `_route`; GET은 `path`와 응답 메서드만 사용. 기존 테스트 실행 시나리오로 확인 |
| H-2. `BaseHTTPRequestHandler`는 `do_<METHOD>`가 없는 method에 501을 보낸다 | 미지원 method `405`(AC-7) | `PUT` 등에서 405가 아닌 501(HTML 본문)이 나가 오류 JSON 계약도 깨진다 | D-3: `__getattr__`로 모든 `do_*`를 `_route`에 연결. `PUT`·임의 method 405 시나리오로 확인 |

## Release and recovery
- 적용 순서: P1(W-1 RED 테스트 작성·실패 관찰·잠금) → P2(W-2 구현) → TEST에서 전체 `pytest` 회귀와 화면 E2E 확인.
- 검증 범위: 실제 서버 프로세스 대상 HTTP integration(API·검증·영속성), 기존 `tests/` 회귀, 브라우저 화면 E2E, 런타임 import가 표준 라이브러리뿐인지 확인. 대역(mock)은 쓰지 않는다.
- 설치·배포: 없음. 검증은 워크트리에서 테스트·실서버 실행으로 끝난다.
- 실패 시: 변경은 워크트리 브랜치 `feat/OP-TASK-001`에만 있으므로 브랜치를 merge하지 않으면 `main`은 영향이 없다. 기존 데이터 파일은 로드 실패 시 수정하지 않는다(D-11).
