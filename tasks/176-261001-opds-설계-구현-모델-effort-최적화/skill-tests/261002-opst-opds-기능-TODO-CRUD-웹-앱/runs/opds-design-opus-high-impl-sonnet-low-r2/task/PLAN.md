---
template: sdlc-v2
---
# PLAN: TODO CRUD 웹 앱 구현

> 입력: [TASK.md](TASK.md)
> 참조: `docs/PROJECT.md` §프로젝트 구조(웹 앱 → `opal-be-agent`), `.opal/AGENT.md` §제약, `todo_web/app.py`, `tests/test_basic.py`

## Approach
기존 표준 라이브러리 HTTP skeleton(`todo_web/app.py:37-84`)을 유지하면서 두 층으로 나눈다.
(1) 새 모듈 `todo_web/store.py`가 JSON 파일 영속성과 TODO 상태를 소유하고, (2) `todo_web/app.py`가 라우팅·요청 검증·JSON 오류 규약·HTML 화면을 소유한다.
API 계약은 공개 동작을 테스트로 먼저 고정할 수 있으므로 RED-first를 적용한다 — 구현자와 다른 주체(`opal-test-agent` red mode)가 `tests/test_todo_api.py`를 먼저 작성해 실패를 관찰한 뒤, `opal-be-agent`가 GREEN 구현을 한다.
실행 명령·CLI 인자(`todo_web/app.py:88-91`)는 바꾸지 않는다(C-1). 외부 패키지는 쓰지 않는다(C-2).

## Findings

### 직접 변경
- `todo_web/app.py`: 현재 `POST`·`PATCH`·`DELETE`는 경로와 무관하게 `404 not_found`(`todo_web/app.py:74-81`), `GET`은 `/health`·`/`만 처리(`todo_web/app.py:44-72`). `data_path`는 클래스 속성으로 보관만 된다(`todo_web/app.py:83`). 라우팅·API·화면 스크립트·`@header` 설명(`todo_web/app.py:6` "CRUD is intentionally unimplemented")을 교체한다.
- `todo_web/store.py`: 신규. 파일 저장소 계층.
- `tests/test_todo_api.py`: 신규. RED-first 계약 테스트.

### 회귀 확인
- `tests/test_basic.py`: `DummyHandler`(실제 handler가 아닌 객체)를 만들어 `handler_type.do_GET(handler)`처럼 unbound 호출한다(`tests/test_basic.py:16-34`, `tests/test_basic.py:37-41`, `tests/test_basic.py:47-52`). 이 객체는 `path`·`send_response`·`send_header`·`end_headers`·`wfile`만 가지며 `headers` 속성은 요청 헤더가 아니라 응답 헤더 기록용 dict다(`tests/test_basic.py:19`). `GET /health`·`GET /` 처리 경로가 이 외 속성을 쓰면 C-3이 깨진다(→ H-1). 홈 화면 테스트는 본문에 `Todo Web`·`todo-form` 문자열을 요구한다(`tests/test_basic.py:55-56`).

### 문서 갱신
없음. 프로젝트 문서 레지스트리(docs/PROJECT.md §프로젝트 구조)는 웹 앱을 디렉터리 단위(todo_web, tests)로만 기록하므로 새 모듈 추가로 사실이 바뀌지 않는다.

### 미확인 가정
- H-1 (기존 `DummyHandler` 테스트 호환)
- H-2 (화면 E2E 실행기 가용성)

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| D1. 저장 파일 형식 | `--data` 파일은 UTF-8 JSON 객체 `{"next_id": <int>, "todos": [<TODO>...]}`(`ensure_ascii=False`, `indent=2`). TODO 객체는 정확히 `{"id": int, "title": str, "description": str, "completed": bool}` 4필드, 이 키 순서. | `next_id`를 저장해야 삭제된 ID가 재시작 후에도 재사용되지 않는다(AC-6·AC-8). |
| D2. 저장소 로드 정책 | `TodoStore(path)` 생성 시 파일을 읽는다. 파일 없음 또는 0바이트 → 빈 저장소(`next_id=1`), 생성 시점에는 파일을 만들지 않는다. JSON 파싱 실패·최상위가 객체 아님·`next_id`가 int 아님·`todos`가 list 아님·TODO 원소가 D1 4필드 타입과 다름(`id`는 bool이 아닌 양의 int, `completed`는 bool)·`id` 중복 → `StoreError`(store.py에 정의, `Exception` 하위) 발생. 로드 후 `next_id = max(저장 next_id, 최대 id + 1, 1)`. | 손상 파일을 빈 저장소로 덮어쓰면 데이터가 유실된다(AC-8). 0바이트는 사용자가 빈 파일을 미리 만든 경우를 허용. |
| D3. 시작 실패 처리 | `main()`은 저장소 로드에서 `StoreError`가 나면 stderr에 `error: cannot load data file <path>: <사유>` 한 줄을 쓰고 `1`을 반환한다(서버 미기동). | 손상 데이터 위에서 서버가 떠서 덮어쓰는 것을 막는다. |
| D4. 원자적 저장 | 모든 변경(생성·수정·삭제)은 `threading.Lock` 안에서 현재 상태의 사본에 변경을 적용 → 전체 문서를 `<data 경로>.tmp`(예: `todos.json.tmp`)에 쓰고 `flush`+`os.fsync` → `os.replace(tmp, data)` → 성공 후에만 메모리 상태를 사본으로 교체한다. 쓰기 실패(`OSError`)면 메모리 상태는 그대로 두고 `StoreError`를 올린다. 조회도 같은 lock 안에서 사본을 반환한다. | `ThreadingHTTPServer`(`todo_web/app.py:94`)는 요청을 스레드별로 처리하므로 lock 없이 전체 문서를 다시 쓰면 동시 요청 간 항목 유실이 생긴다(AC-8 "다른 항목 유실 금지"). 같은 디렉터리 임시 파일 + `os.replace`는 중단 시에도 이전 완전본을 남긴다. `.gitignore`가 이미 `*.json.tmp`를 무시한다. |
| D5. 저장소 인터페이스 | `todo_web/store.py`: `class StoreError(Exception)`, `class TodoStore` with `__init__(self, path: Path)`, `list(self) -> list[dict]`(id 오름차순), `get(self, todo_id: int) -> dict \| None`, `create(self, title: str, description: str, completed: bool) -> dict`, `update(self, todo_id: int, changes: dict) -> dict \| None`(changes 키는 `title`·`description`·`completed` 부분집합, 없는 ID면 `None`), `delete(self, todo_id: int) -> bool`. 반환 dict는 내부 상태와 공유하지 않는 사본. 검증은 store가 아니라 app이 한다. | HTTP 계층과 영속성 계층을 분리해 원자 저장 규칙을 한 곳에 둔다. |
| D6. ID 규칙 | ID는 1부터 증가하는 정수, 삭제 후 재사용하지 않는다. 경로의 `{id}`는 정규식 `^[1-9][0-9]*$`에 맞을 때만 ID로 해석하고, 맞지 않으면(`abc`, `0`, `01`, 음수) 존재하지 않는 리소스로 보고 `404`. | 결정론적 404 경계. |
| D7. 라우트·허용 method | 경로는 `urlparse(path).path` 정확 일치(쿼리 무시, 끝 `/` 허용 안 함). `/health`: GET. `/`: GET. `/api/todos`: GET, POST. `/api/todos/{id}`: GET, PATCH, DELETE. 그 밖의 경로는 method와 무관하게 `404 {"error":"not_found"}`. 알려진 경로에 허용되지 않은 method는 `405 {"error":"method_not_allowed"}` + `Allow` 헤더(위 허용 목록을 `, `로 연결, 예 `GET, POST`). | AC-7 "지원하지 않는 method는 405". |
| D8. 405 대상 method | handler에 `do_GET`·`do_POST`·`do_PATCH`·`do_DELETE`·`do_PUT`·`do_HEAD`·`do_OPTIONS`를 정의해 모두 같은 dispatch를 탄다. 그 외 임의 method(예 `TRACE`, `FOO`)도 handler 클래스의 `__getattr__`이 `do_` 접두 이름 요청에 같은 dispatch를 돌려주게 해 표준 501 대신 D7 규칙(알려진 경로면 405, 아니면 404)을 따른다. HEAD도 본문을 포함해 동일하게 응답한다. | `BaseHTTPRequestHandler`는 `do_<METHOD>`가 없으면 501을 보내므로 405 계약을 보장하려면 명시가 필요하다. |
| D9. 쓰기 요청 검사 순서 | POST·PATCH는 (1) 경로·method 판정(404/405) → (2) `Content-Type`의 media type(`;` 앞, 공백 제거, 소문자)이 `application/json`이 아니거나 헤더 없음 → `415 {"error":"unsupported_media_type"}` (`charset` 등 파라미터는 허용) → (3) 본문: `Content-Length`(없으면 0, 정수가 아니거나 음수면 `400 invalid_json`)만큼 읽고 UTF-8 디코드 + `json.loads` 실패(빈 본문 포함) → `400 {"error":"invalid_json"}` → (4) 값이 JSON 객체가 아니거나 필드 검증 실패 → `400 {"error":"validation_error"}` → (5) PATCH 대상 ID 부재 → `404 {"error":"not_found"}`. | 결정론적 우선순위. |
| D10. 필드 검증 | `title`: 문자열이어야 하고 앞뒤 공백(`str.strip()`) 제거 후 길이 1~120자(Python 문자 수), 저장값은 제거된 값. `description`: 문자열, 0~2000자, 저장값은 원문 그대로(trim 없음). `completed`: JSON boolean만(`0`/`1`/문자열/`null` 거부). POST: `title` 필수, `description` 선택(없으면 `""`), `completed` 선택(없으면 `false`). PATCH: `title`·`description`·`completed` 중 하나 이상 필수, 있는 키만 위 규칙으로 검증·반영. 두 요청 모두 그 밖의 키는 무시한다. `null` 값은 해당 필드 검증 실패. | AC-3·AC-5·AC-7. |
| D11. 응답 계약 | 성공·오류 JSON은 기존 `_send_json`(`todo_web/app.py:19-25`, `Content-Type: application/json; charset=utf-8`)으로 보낸다. 생성 `201` + `Location: /api/todos/{id}` + TODO 객체. 목록 `200` + 배열(id 오름차순). 상세·수정 `200` + TODO 객체. 삭제 `204`, 본문 없음, `Content-Length: 0`, `Content-Type` 없음. 오류 본문은 `{"error": <코드>, "message": <사람용 설명>}`이며(`message`는 실패 원인을 설명하는 자유 문구 영어 한 문장, 검증 실패면 필드명을 포함 — 테스트는 `message` 문구를 단언하지 않는다) 코드는 `not_found`·`method_not_allowed`·`unsupported_media_type`·`invalid_json`·`validation_error`·`storage_error` 중 하나. 저장 실패(`StoreError`)는 `500 {"error":"storage_error"}`. | AC-3~AC-7. |
| D12. handler 구조와 기존 테스트 호환 | `make_handler(data_path)`는 `TodoStore(data_path)`를 만들어 클로저로 캡처하고, 각 `do_*`는 모듈 수준 함수 `_dispatch(handler, method, store)`를 호출한다. `_dispatch`와 `GET /health`·`GET /` 처리 경로는 `handler.path`·`send_response`·`send_header`·`end_headers`·`wfile`만 사용한다(요청 헤더·`rfile`은 쓰기 요청 처리에서만 접근). `TodoHandler.data_path` 속성(`todo_web/app.py:83`)과 `make_handler`·`main` 이름(`@header` exports)은 유지한다. `log_message` 무음 처리(`todo_web/app.py:41-42`)도 유지. `make_handler`는 저장소 로드 실패 시 `StoreError`를 그대로 올리고, `main()`은 `make_handler` 호출을 `try`로 감싸 `StoreError`를 D3대로 처리한다(서버 소켓 생성 전). | `tests/test_basic.py`가 DummyHandler로 unbound `do_GET`을 호출한다(→ H-1, C-3). |
| D13. HTML 화면 | `GET /`은 기존 구조(`<h1>Todo Web</h1>`, `form#todo-form`, `input[name=title]`, `textarea[name=description]`, `button[type=submit]` "Create", `section#todo-list`)를 유지하고 다음을 추가한다: 폼 아래 `<p id="form-error" role="alert"></p>`, 인라인 `<script>`. 스크립트는 로드 시 `GET /api/todos`로 목록을 받아 `section#todo-list` 안의 `<ul>`에 항목마다 `<li data-id="{id}">`(자식: `<strong class="todo-title">`, `<span class="todo-description">`, `<span class="todo-status">` 텍스트 `completed`/`open`)를 렌더한다. 폼 submit은 기본 동작을 막고 `POST /api/todos`(`Content-Type: application/json`, 본문 `{"title","description"}`)를 보낸 뒤, 성공(201)이면 폼을 비우고 `#form-error`를 비운 뒤 목록을 다시 불러오고, 실패면 응답 JSON의 `message`를 `#form-error`에 표시한다. 사용자 입력은 `textContent`로만 넣는다(`innerHTML` 금지). 수정·삭제 UI는 추가하지 않는다. | AC-2 범위(목록·제목·설명·생성)만 구현(C-4). XSS 방지. |
| D14. 테스트 방식 | `tests/test_todo_api.py`는 pytest + 표준 라이브러리(`http.client`/`urllib.request`, `subprocess`, `threading`)만 쓴다. API 계약은 `ThreadingHTTPServer(("127.0.0.1", 0), make_handler(tmp_path/"todos.json"))`를 스레드로 띄워 실제 HTTP로 검증하고, 실행 명령·재시작 영속성은 `python -m todo_web.app --host 127.0.0.1 --port <빈 포트> --data <tmp>` subprocess로 검증한다(`/health` 폴링으로 기동 대기, 종료는 `terminate()` 후 `wait`). | 공개 HTTP 동작만 검증(RED-first §2), 외부 패키지 금지(C-2). |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. RED 계약 테스트 작성 | opal-test-agent (red mode) | `tests/test_todo_api.py` | TEST-SCENARIO의 `시점: 구현 전 RED` 시나리오를 D14 방식의 pytest 테스트로 작성하고, 구현 전 실행해 실패(exit≠0)와 핵심 실패 출력을 `test-tool scenario-red`로 기록한다. 기대값은 D6~D11 계약을 그대로 따른다. `tests/test_basic.py`는 수정하지 않는다. | 없음 | P1 | AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, C-1 |
| W-2. 저장소·API·화면 구현 | opal-be-agent | `todo_web/store.py`, `todo_web/app.py` | `todo_web/store.py`를 D1·D2·D4·D5대로 신규 작성(`@header` 포함, exports `TodoStore`·`StoreError`). `todo_web/app.py`를 D3·D6~D13대로 변경하고 `@header` description을 CRUD 구현 사실로 갱신한다. W-1 테스트 파일은 수정하지 않는다(RED 계약 불변). 완료 시 `python -m pytest -q` 전체 통과. | W-1 | P2 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, C-1, C-2, C-3, C-4 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. 기존 `DummyHandler` 테스트가 새 dispatch 구조에서도 `GET /health`·`GET /`를 처리할 수 있다는 가정 | `tests/test_basic.py` 2건 통과(C-3) | 회귀 테스트 실패 → 수용 불가 | D12로 dispatch를 모듈 함수 + 클로저 store로 고정하고 해당 경로에서 쓰는 handler 속성을 한정. 기존 테스트 무수정 실행 시나리오로 확인. |
| H-2. 화면 사용자 흐름(AC-2)을 실제 브라우저로 실행할 E2E 실행기(Playwright 등)가 TEST 단계에 가용하다는 가정 | AC-2 "화면에서 생성하고 목록에서 확인" 관찰 | 실행기 부재 시 AC-2 사용자 흐름 미검증 | 브라우저 E2E 시나리오를 두고, 실행기 부재면 PASS로 대체하지 않고 `executor_unavailable`로 보고한다. 별도로 HTML 구조·스크립트 계약(D13) 정적 확인 시나리오를 둔다. |

## Release and recovery
- 적용 순서: P1(W-1 RED 테스트 작성·실패 관찰·`scenario-lock`) → P2(W-2 GREEN 구현) → TEST 단계 전체 시나리오 실행.
- 검증 범위: 결정론 — `python -m pytest -q`(기존 2건 + 신규 계약 테스트), `python -m compileall -q todo_web tests`; 실제 연동 — 실행 명령 subprocess 기동·재시작 영속성, 브라우저 E2E(H-2).
- 실측 경계: 시간·품질 목표 없음.
- 실패 시: 배포·설치 없음. 변경은 worktree 브랜치 `feat/OP-TASK-1`에만 있으므로 실패 시 해당 커밋을 되돌리거나 브랜치를 merge하지 않는 것으로 복구한다.
