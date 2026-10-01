---
template: sdlc-v2
---
# PLAN: TODO CRUD 웹 앱 구현

> 입력: [TASK.md](TASK.md) | 요구 원문: 세션 입력 요구서 `REQUEST.md` §실행 계약·§화면·§API·§검증과 예외·§영속성 | 작성자: PM(actor=coordinator, PM 경로)

## Approach

기존 skeleton(`todo_web/app.py:36-87`)의 `ThreadingHTTPServer` + `BaseHTTPRequestHandler` 구조와 실행 진입점(`todo_web/app.py:90-104`)을 유지하고, 표준 라이브러리만으로 다음 두 층을 만든다.

1. 저장소 층 `todo_web/store.py` — 메모리 상태 + 프로세스 내 잠금 + `--data` JSON 파일 원자적 전체 재기록.
2. HTTP 층 `todo_web/app.py` — 경로·method 라우팅, Content-Type·JSON·필드 검증, JSON 응답, 화면 HTML(브라우저 JS가 API를 호출).

검증은 RED-first로 진행한다. 공개 HTTP 계약을 고정하는 실패 테스트 `tests/test_todo_api.py`를 구현자와 다른 주체(opal-test-agent red mode)가 먼저 작성해 RED를 관찰한 뒤, opal-be-agent가 GREEN 구현을 한다. 범위 밖(인증, 다중 프로세스 동시 쓰기, 외부 DB, 배포)은 다루지 않는다(TASK `Affected users and systems`).

## Findings

### 직접 변경
- `todo_web/app.py`: 라우팅·검증·오류 응답·화면 HTML/JS 구현, `do_PUT` 등 미지원 method 처리, 저장소 연결. 모듈 @header `description`을 CRUD 구현 사실로 갱신(`todo_web/app.py:4-6`).
- `todo_web/store.py`: 신규 저장소 모듈.
- `tests/test_todo_api.py`: 신규 공개 계약 테스트(RED 선작성).

### 회귀 확인
- `tests/test_basic.py`: 수정하지 않는다. 이 테스트는 `make_handler(...)`가 반환한 클래스의 `do_GET`을 `TodoHandler` 인스턴스가 아닌 `DummyHandler`(속성: `path`·`send_response`·`send_header`·`end_headers`·`wfile`만 보유)로 언바운드 호출한다(`tests/test_basic.py:15-31`, `tests/test_basic.py:34-40`, `tests/test_basic.py:43-53`). 따라서 `GET /health`·`GET /` 처리 경로는 그 다섯 속성 외의 handler 속성을 읽지 않아야 한다(H-1).

### 문서 갱신
없음. 프로젝트 레지스트리 문서(docs/PROJECT.md)의 프로젝트 구조 절(웹 앱 = todo_web·tests, Python 3 표준 라이브러리, pytest)과 프로젝트 PM 프로필(.opal/AGENT.md)의 제약 절은 구현 후에도 사실이 그대로다.

### 미확인 가정
- H-2 (브라우저 E2E 실행 수단 가용성)

## Decisions and contracts

### D-1. 모듈 구조

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| 저장소 분리 | `todo_web/store.py`에 `class TodoStore`, `class StoreError(Exception)` 정의. 공개 메서드: `__init__(self, path: Path)`, `list(self) -> list[dict]`, `get(self, todo_id: int) -> dict \| None`, `create(self, title: str, description: str, completed: bool) -> dict`, `update(self, todo_id: int, changes: dict) -> dict \| None`, `delete(self, todo_id: int) -> bool`. 반환 dict는 항상 새 사본(내부 상태 참조 아님) | HTTP 검증과 영속성을 분리해 AC-11을 독립 검증 가능하게 한다 |
| handler 구조 | `make_handler(data_path: Path)`는 시그니처 유지(`todo_web/app.py:36`). 내부에서 `store = TodoStore(data_path)`를 1회 생성해 클로저로 캡처한다. `do_GET`·`do_POST`·`do_PATCH`·`do_DELETE`는 각각 모듈 수준 함수 `_dispatch(handler, store, method)`를 호출하는 한 줄이다. `_dispatch`와 그 하위 함수는 `handler.path`·`handler.headers`·`handler.rfile`·`send_response`·`send_header`·`end_headers`·`wfile`만 사용하며, `GET` 처리 경로는 `handler.headers`·`handler.rfile`을 읽지 않는다 | H-1: `tests/test_basic.py`의 언바운드 `do_GET(DummyHandler())` 호출 호환. `TodoHandler.data_path = data_path` 대입(`todo_web/app.py:86`)은 유지 |
| 미지원 method | `TodoHandler.__getattr__(self, name)`을 정의해 `name`이 `do_`로 시작하고 `do_GET`/`do_POST`/`do_PATCH`/`do_DELETE`가 아니면 405 응답 함수를 반환, 그 외 이름은 `AttributeError`를 발생시킨다 | `BaseHTTPRequestHandler`는 `do_<METHOD>` 부재 시 HTML 501을 보낸다. PUT·HEAD·OPTIONS·임의 method 모두 405 JSON으로 통일(AC-9, AC-10) |
| 런타임 의존성 | import는 표준 라이브러리(`argparse`·`http.server`·`json`·`os`·`re`·`sys`·`threading`·`pathlib`·`urllib.parse`)로 한정한다. 외부 패키지 추가 없음 | C-1 |

### D-2. 라우팅과 상태 코드 판정 순서

경로는 `urllib.parse.urlparse(handler.path).path`로 얻는다(쿼리 문자열 무시). 판정은 아래 순서로 처음 해당하는 단계에서 응답한다.

1. method가 `GET`·`POST`·`PATCH`·`DELETE`가 아니면 → `405 method_not_allowed` (경로 무관, `Allow` 헤더 없음, 본문을 읽지 않음).
2. 경로 매칭:
   - `/` → 허용 `GET`
   - `/health` → 허용 `GET`
   - `/api/todos` → 허용 `GET`, `POST`
   - `/api/todos/{id}` (`{id}`는 정규식 `[1-9][0-9]*`, 선행 0·부호·공백 불가) → 허용 `GET`, `PATCH`, `DELETE`
   - 그 외(`/api/todos/`, `/api/todos/abc`, `/api/todos/0`, 미정의 경로) → `404 not_found`
3. 매칭된 경로에서 method가 허용 목록에 없으면 → `405 method_not_allowed`, 응답 헤더 `Allow: <허용 method를 ", "로 연결>`.
4. `POST`·`PATCH`만: `Content-Type` 헤더의 `;` 앞 media type을 공백 제거·소문자화한 값이 정확히 `application/json`이 아니면(헤더 부재 포함) → `415 unsupported_media_type`. 파라미터(`; charset=utf-8` 등)는 허용한다.
5. `POST`·`PATCH`만: 본문 파싱. `Content-Length` 부재·정수 아님·음수 → 본문을 빈 바이트로 본다. 정확히 `Content-Length` 바이트를 읽어 UTF-8 디코드 후 `json.loads`. 디코드 실패·JSON 문법 오류·빈 본문 → `400 invalid_json`.
6. `POST`·`PATCH`만: 필드 검증(D-3) 실패 → `400 validation_error`.
7. ID 대상(`GET`/`PATCH`/`DELETE /api/todos/{id}`)이 존재하지 않으면 → `404 not_found`. (`PATCH`는 6 통과 후 판정)
8. 성공 응답(D-4).
9. 저장 중 `StoreError` → `500 storage_error` (메모리·파일 모두 변경 전 상태 유지, D-5).

### D-3. 필드 검증 규칙

| 대상 | 규칙 |
|---|---|
| 본문 최상위 | JSON 객체(dict)여야 한다. 배열·문자열·숫자·`null` → `validation_error` |
| `title` (POST 필수, PATCH 선택) | `str`이어야 한다(`null`·숫자 불가). `str.strip()` 결과가 빈 문자열이면 실패. 제거 후 길이(`len`, 코드 포인트 수) > 120이면 실패. **저장값은 strip한 값** |
| `description` (POST·PATCH 선택) | `str`이어야 한다(`null` 불가). `len` > 2000이면 실패. 저장값은 입력 그대로(trim 안 함). POST에서 생략하면 `""` |
| `completed` (POST·PATCH 선택) | `bool`이어야 한다(`isinstance(v, bool)`; `0`/`1`/문자열 불가). POST에서 생략하면 `false` |
| PATCH 최소 필드 | `title`·`description`·`completed` 중 하나 이상이 없으면 `validation_error` |
| 그 외 키 (`id` 포함) | 무시한다(저장·응답에 반영하지 않음, 오류 아님) |

검증은 PATCH의 모든 제공 필드를 먼저 검증한 뒤 한 번에 적용한다(일부만 반영되는 부분 수정 없음).

### D-4. 성공 응답 계약

| 요청 | 상태 | 헤더 | 본문 |
|---|---|---|---|
| `GET /health` | 200 | `Content-Type: application/json; charset=utf-8` | `{"ok": true}` |
| `GET /` | 200 | `Content-Type: text/html; charset=utf-8` | D-6 화면 |
| `GET /api/todos` | 200 | JSON | TODO 객체 배열, `id` 오름차순(생성 순) |
| `POST /api/todos` | 201 | JSON, `Location: /api/todos/{id}` | 생성된 TODO 객체 |
| `GET /api/todos/{id}` | 200 | JSON | TODO 객체 |
| `PATCH /api/todos/{id}` | 200 | JSON | 수정 후 TODO 객체 |
| `DELETE /api/todos/{id}` | 204 | `Content-Length`·`Content-Type` 미전송 | 없음(0바이트) |

TODO 객체는 정확히 4키 `{"id": int, "title": str, "description": str, "completed": bool}`(이 순서)이다. `id`는 1부터 시작하는 정수로 저장소의 `next_id`에서 발급하고 삭제 후에도 재사용하지 않는다. JSON 응답은 기존 `_send_json`(`todo_web/app.py:19-25`, `ensure_ascii=False`, `Content-Length` 포함)을 사용한다.

오류 응답은 모두 `Content-Type: application/json; charset=utf-8`, 본문 `{"error": "<code>", "message": "<사람이 읽는 영문 설명>"}`이다. `<code>`는 폐쇄 집합 `not_found`·`method_not_allowed`·`unsupported_media_type`·`invalid_json`·`validation_error`·`storage_error`이다.

### D-5. 저장 방식

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| 파일 형식 | UTF-8 JSON 객체 `{"next_id": <int>, "todos": [<TODO 객체>, ...]}`, `json.dumps(..., ensure_ascii=False, indent=2)` | `next_id`로 삭제 후 ID 재사용 방지 |
| 시작 시 로드 | `TodoStore.__init__`에서 1회 읽는다. 파일 부재 또는 0바이트 → 빈 상태(`next_id=1`, 파일은 첫 쓰기 때 생성). JSON 오류·형식 불일치(최상위 객체 아님, `next_id` 정수 아님, `todos` 배열 아님, 항목이 4키 타입 계약 위반, `id` 중복, `next_id`가 최대 `id` 이하) → `StoreError` 발생. `main`은 이를 잡아 `stderr`에 `error: invalid data file <path>: <사유>`를 쓰고 exit code 2로 종료한다 | 손상 파일을 빈 상태로 덮어써 기존 데이터를 지우는 것을 막는다(AC-11 유실 금지) |
| 동시성 | 인스턴스당 `threading.Lock` 1개. `create`·`update`·`delete`는 잠금 안에서 "새 상태 사본 생성 → 파일 기록 → 성공 시 메모리 교체"를 수행한다. `list`·`get`도 잠금 안에서 사본을 반환한다 | `ThreadingHTTPServer`(`todo_web/app.py:96`)의 동시 요청이 서로의 변경을 덮어쓰지 않게 한다 |
| 원자적 기록 | 대상과 같은 디렉토리의 `<data 파일명>.tmp`(예: `todos.json.tmp`, `.gitignore`의 `*.json.tmp`와 일치)에 전체 상태를 쓰고 `flush` + `os.fsync` 후 `os.replace(tmp, data_path)`. 기록 중 `OSError` → 임시 파일 삭제 시도 후 `StoreError` 발생, 메모리 상태는 바꾸지 않는다 | 중간 종료 시에도 파일은 이전 완전본 또는 새 완전본 중 하나다 |
| 디렉토리 | `main`의 `args.data.parent.mkdir(parents=True, exist_ok=True)`(`todo_web/app.py:95`)를 유지한다. 저장소는 디렉토리를 만들지 않는다 | 기존 계약 유지 |

### D-6. 화면

`GET /`의 HTML은 `<!doctype html>`, `<title>Todo Web</title>`, `<h1>Todo Web</h1>`을 유지하고 다음 요소를 가진다(기존 `todo-form`·`todo-list` id 유지 — `tests/test_basic.py:52-53`).

| 요소 | 계약 |
|---|---|
| 폼 | `<form id="todo-form">` 안에 `<input id="todo-title" name="title" maxlength="120" required>`, `<textarea id="todo-description" name="description" maxlength="2000">`, `<button id="todo-create" type="submit">Create</button>` |
| 오류 표시 | `<p id="todo-error" role="alert"></p>` — 실패 시 응답 `message`(없으면 `error`)를 표시, 성공 시 비움 |
| 목록 | `<ul id="todo-list" aria-label="Todo list">`, 각 항목 `<li data-id="{id}">` 안에 완료 토글 `<input type="checkbox" class="todo-toggle">`, 제목 `<span class="todo-title">`, 설명 `<span class="todo-description">`, 삭제 `<button type="button" class="todo-delete">Delete</button>` |
| 스크립트 | 인라인 `<script>`(외부 리소스 없음). 로드 시 `GET /api/todos`로 렌더. submit 시 `preventDefault` 후 `fetch('/api/todos', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({title, description})})`, 201이면 입력을 비우고 목록 재조회. 체크박스 변경 → `PATCH /api/todos/{id}` `{completed}`; Delete → `DELETE /api/todos/{id}`; 둘 다 성공 후 목록 재조회. 텍스트는 `textContent`로만 삽입(`innerHTML`에 사용자 값 금지) |

`todo-list`가 `<section>`에서 `<ul>`로 바뀌어도 기존 테스트는 id 문자열만 확인하므로 통과한다(`tests/test_basic.py:53`는 `todo-form`만 확인).

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. 공개 계약 RED 테스트 작성 | opal-test-agent (red mode) — `tests/test_todo_api.py` 단독 소유 | `tests/test_todo_api.py` | TEST-SCENARIO의 `구현 전 RED` 행(S-1~S-10)을 pytest로 작성. 인프로세스 서버: `ThreadingHTTPServer(("127.0.0.1", 0), make_handler(tmp_path/"todos.json"))`를 데몬 스레드로 띄우고 `http.client.HTTPConnection`으로 임의 method·헤더·원시 본문을 보낸다. 재시작 시나리오는 `subprocess.Popen([sys.executable, "-m", "todo_web.app", "--host", "127.0.0.1", "--port", <빈 포트>, "--data", <tmp 파일>], cwd=<저장소 루트>)`로 실행하고 `/health` 200을 최대 10초 폴링, 종료는 `terminate()` 후 `wait(timeout=10)`. 표준 라이브러리 + pytest만 사용. 구현 전 실행해 실패(RED)를 관찰·기록한다. `todo_web/` 파일은 수정하지 않는다 | 없음 | P1 | AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, AC-9, AC-10, AC-11, C-2 |
| W-2. 저장소·HTTP·화면 구현 | opal-be-agent — `todo_web/store.py`, `todo_web/app.py` 단독 소유 | `todo_web/store.py`, `todo_web/app.py` | D-1~D-6 그대로 구현. `store.py`에 `TodoStore`·`StoreError`와 @header 블록(`module`·`layer`·`domain`·`description`·`exports`, 기존 `todo_web/app.py:1-9` 형식)을 작성. `app.py`는 `_dispatch`·검증 함수·`__getattr__`·화면 HTML/JS를 추가하고 `main`에서 `StoreError`를 처리하며 @header `description`·`exports`를 갱신. `tests/` 파일은 수정하지 않는다. 완료 조건: `python -m pytest -q` 전체 통과(W-1 RED 테스트 포함, 테스트 계약 불변) | W-1 | P2 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, AC-9, AC-10, AC-11, C-1, C-2, C-3 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. 기존 테스트가 `do_GET`을 `DummyHandler`로 언바운드 호출한다(`tests/test_basic.py:34-53`) | `GET /health`·`GET /`가 `self`의 다른 속성(저장소, 헬퍼 메서드, `headers`)을 쓰면 `AttributeError`로 C-3 위반 | 기존 회귀 테스트 실패 | D-1 handler 구조(모듈 함수 `_dispatch` + 클로저 `store`, GET 경로는 다섯 속성만 사용). S-11에서 기존 테스트 무수정 통과 확인 |
| H-2. TEST 단계에서 브라우저 자동화(실제 브라우저로 페이지 조작) 수단이 opal-test-agent에 가용하다 | AC-1의 "화면에서 생성하면 목록에 나타난다"를 실제 브라우저로 판정 | 수단이 없으면 AC-1 E2E가 BLOCKED, 추정 통과 금지 | S-12를 실제 브라우저 E2E로 두고, 수단 부재 시 BLOCKED로 보고(대역·정적 검사로 대체하지 않음). PM이 TEST 디스패치 시 실제 가용 capability를 주입 |

## Release and recovery

- 적용 순서: P1(W-1 RED 작성·RED 증거 기록·`scenario-lock`) → P2(W-2 GREEN 구현) → TEST(전 시나리오 실행) → worktree 브랜치 `feat/OP-TASK-001` 체크포인트 → CLOSE finalize → 사용자 사전 승인 범위의 격리 저장소 내 local merge. 설치·배포 없음.
- 검증 범위: 결정론(pytest 인프로세스 HTTP 계약 S-1~S-7·S-9, 기존 회귀 S-11), 실제 프로세스(S-8 재시작 영속성, S-10 손상 데이터 파일 기동 거부 — 둘 다 `python -m todo_web.app`), 실제 브라우저 E2E(S-12), 정적 의존성 확인(S-13).
- 실측 경계: 시간·품질 수치 목표 없음.
- 실패 시: 변경은 worktree 브랜치에만 있으므로 merge 전에는 브랜치 폐기로 원복한다. merge 후 문제 발견 시 merge 이전 커밋으로 되돌리는 별도 커밋을 만든다(이력 재작성 금지). 데이터 파일은 원자적 교체만 하므로 실패 시에도 직전 완전본이 남는다.
