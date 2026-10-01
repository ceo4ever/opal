---
template: sdlc-v2
---
# PLAN: TODO CRUD 웹 앱

> 입력: [TASK.md](TASK.md) | 작성자: PM(actor=coordinator, PM 경로) | ANALYSIS.md 없음(분석 결과는 `## Findings`에 기록)

## Approach

표준 라이브러리 `http.server` skeleton(`todo_web/app.py:37-84`)을 유지한 채 세 부분을 더한다.

1. **저장소 모듈 신설** — `todo_web/store.py`에 JSON 파일 영속 저장소 `TodoStore`를 둔다. 모든 변경은 하나의 프로세스 내 lock 아래에서 "전체 상태 복사 → 임시 파일 쓰기 → `os.replace` 원자 교체 → 메모리 반영" 순서로 처리해, 동시 요청·중간 실패에서도 다른 항목이 유실되지 않게 한다.
2. **HTTP 라우팅·검증·오류 계약** — `todo_web/app.py`의 `make_handler(data_path)` 안에서 저장소를 클로저로 만들고, `/api/todos`·`/api/todos/{id}` 라우팅, 입력 검증, `400/404/405/415` JSON 오류를 구현한다.
3. **화면** — `GET /` HTML에 인라인 JS를 넣어 위 API로 목록 표시·생성·완료 토글·삭제를 수행한다(요구서 "화면은 아래 API를 사용하거나 서버 렌더링으로 구현할 수 있다" 중 API 사용 방식 채택).

RED-first(`harness/red-first.md` §1: "API 계약 … 적용")를 따라, 공개 HTTP 계약을 실제 서버 기동 통합 테스트로 먼저 고정(W-1)한 뒤 구현(W-2)한다. 범위는 TASK `Affected users and systems`의 포함 항목으로 한정한다.

## Findings

### 직접 변경

- `todo_web/app.py` — 현재 `do_GET`이 `/health`·`/`만 처리하고 나머지는 `404 {"error":"not_found"}`(`todo_web/app.py:44-72`), `do_POST`/`do_PATCH`/`do_DELETE`는 무조건 404(`todo_web/app.py:74-81`)이며 `data_path`는 클래스 속성으로 보관만 하고 쓰지 않는다(`todo_web/app.py:83`). 정의되지 않은 method(PUT·HEAD·OPTIONS 등)는 표준 라이브러리 `BaseHTTPRequestHandler`가 `do_<METHOD>` 부재 시 HTML 본문의 `501`을 보낸다(Python 3.14 표준 라이브러리 http.server 모듈 477-481행) — AC-5의 `405`+JSON 계약을 위반하므로 W-2가 막는다(H-3).
- `todo_web/store.py` — 신규. 영속성·동시성 계약(AC-6, H-1)을 소유한다.
- `tests/test_todo_api.py` — 신규. 실제 서버 프로세스를 띄우는 공개 HTTP 계약 통합 테스트(RED 대상). 기존 회귀 테스트 파일은 수정하지 않는다(C-2, 아래 §회귀 확인).

### 회귀 확인

- `tests/test_basic.py` — `make_handler(...)`가 만든 클래스의 `do_GET`을 `DummyHandler` 인스턴스로 언바운드 호출한다(`tests/test_basic.py:37-44`, `tests/test_basic.py:47-57`). `DummyHandler`는 `path`·`wfile`·`send_response`·`send_header`·`end_headers`만 가지며(`tests/test_basic.py:16-34`) `headers`는 응답 헤더 기록용 dict다. 따라서 `GET /health`·`GET /` 분기는 저장소·`rfile`·`command`·요청 헤더 등 인스턴스 속성에 의존하면 안 되고, `make_handler`는 데이터 파일이 없는 경로로 호출돼도 예외를 내면 안 된다(H-2). 본문 단언 `"Todo Web"`·`"todo-form"`(`tests/test_basic.py:56-57`)을 화면에 유지한다.
- 실행 계약 CLI(`--host`·`--port`·`--data`, 기본값과 상위 디렉토리 생성)는 app.py 87-101행의 현재 동작을 그대로 유지한다.

### 문서 갱신

없음. docs/PROJECT.md의 프로젝트 구조 표(웹 앱: todo_web·tests, Python 3 표준 라이브러리·pytest, opal-be-agent)와 문서 레지스트리는 변경 후에도 사실과 같다. app.py 모듈 @header의 description("CRUD is intentionally unimplemented")은 코드 파일 안의 헤더이므로 W-2가 함께 갱신한다.

### 미확인 가정

- H-1(동시 쓰기에서 항목 유실 없음)은 lock·원자 교체 설계로 대응하지만 실제 `ThreadingHTTPServer` 동시 요청에서 아직 관찰하지 않았다.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| D-1. 라우팅과 허용 method | `/health`·`/`: `GET`. `/api/todos`: `GET`·`POST`. `/api/todos/{id}`: `GET`·`PATCH`·`DELETE`(`{id}`는 정규식 `^/api/todos/(\d+)$`, 정수 변환). 경로 판정은 query string을 뺀 path로 한다. 위 네 경로 외 path는 method와 무관하게 `404 {"error":"not_found"}`. 알려진 path에 허용되지 않은 method(정의되지 않은 PUT·HEAD·OPTIONS·임의 method 포함)는 `405 {"error":"method_not_allowed"}` + `Allow` 헤더(해당 path 허용 method를 `, `로 연결). `HEAD` 응답은 본문을 쓰지 않는다. | 요구서 §검증과 예외 "지원하지 않는 method는 405". 표준 라이브러리의 501 기본 동작(표준 라이브러리 http.server 477-481행) 차단 — H-3 |
| D-2. 요청 처리 순서 | 쓰기 요청: ① path·method 판정(404/405) → ② `Content-Type` 미디어 타입(`;` 앞, 공백 제거·소문자)이 정확히 `application/json`이 아니면(헤더 부재 포함) `415 {"error":"unsupported_media_type"}` → ③ `Content-Length` 바이트를 읽어 UTF-8 디코드·`json.loads` 실패(본문 없음, 숫자가 아닌 `Content-Length` 포함)면 `400 {"error":"invalid_json"}` → ④ 최상위가 JSON 객체가 아니면 `400 {"error":"validation_error"}` → ⑤ PATCH는 대상 ID 부재 시 `404 {"error":"not_found"}` → ⑥ 필드 검증 실패 시 `400 {"error":"validation_error"}`. | 상태 코드 간 우선순위를 구현자가 고르지 않도록 고정 |
| D-3. 오류 응답 형식 | 모든 오류는 `Content-Type: application/json; charset=utf-8`, 본문 `{"error": "<코드>", "message": "<사람이 읽는 설명>"}`. 코드는 `not_found`·`method_not_allowed`·`unsupported_media_type`·`invalid_json`·`validation_error`·`storage_error` 6종으로 폐쇄. | 요구서 "오류 응답은 최소한 error 필드를 가진 JSON 객체". 기존 `{"error":"not_found"}`(`todo_web/app.py:72`)와 호환 |
| D-4. TODO 객체와 ID | 응답 객체는 정확히 `{"id": int, "title": str, "description": str, "completed": bool}`. `id`는 1부터 증가하는 양의 정수이며 삭제 후에도 재사용하지 않는다(다음 번호를 파일에 영속). 목록은 `id` 오름차순. | 요구서 §API 2 필드 목록. 재사용 금지는 삭제된 ID의 `Location`이 다른 항목을 가리키는 혼동 방지 |
| D-5. 생성(POST) 필드 규칙 | `title`: 필수, 문자열, 앞뒤 공백 제거 후 1~120자(Python `len` 기준), 저장값은 공백 제거본. `description`: 선택(부재 시 `""`), 문자열, 0~2000자, 원문 그대로 저장. `completed`: 선택(부재 시 `false`), bool만 허용. 그 외 키는 무시. 성공 `201` + 생성 객체 + `Location: /api/todos/{id}`. | 요구서 §API 3·§검증과 예외. `completed`는 "기본값 false" 문구에 맞춰 선택 입력으로 허용 |
| D-6. 수정(PATCH) 필드 규칙 | 본문에 `title`·`description`·`completed` 중 하나 이상 필요(없으면 `400 validation_error`). 보낸 필드만 D-5와 같은 규칙으로 검증·반영하며, 하나라도 실패하면 아무 필드도 바꾸지 않는다. `id` 등 그 외 키는 무시. 성공 `200` + 수정된 객체. 다른 항목은 바뀌지 않는다. | 요구서 §API 5 "하나 이상을 포함할 수 있다", "다른 TODO 항목은 변하지 않아야 한다" |
| D-7. 삭제(DELETE) | 성공 `204`, 본문 0바이트(`Content-Length: 0`, `Content-Type` 미전송). 없는 ID `404`. | 요구서 §API 6 |
| D-8. 성공 응답 형식 | `GET /health` → `200 {"ok": true}`. API 성공 응답은 `Content-Type: application/json; charset=utf-8`. `GET /` → `200 text/html; charset=utf-8`. | 요구서 §API 1, §화면. 기존 `_send_json`·`_send_html`(`todo_web/app.py:19-34`) 재사용 |
| D-9. 저장 형식과 원자성 | 데이터 파일은 UTF-8 JSON `{"next_id": int, "todos": [TODO 객체...]}`. 파일이 없으면 빈 저장소(`next_id=1`)로 시작하고 첫 쓰기 때 생성한다. 파일이 있으나 JSON·형식이 깨졌으면 기동 시 예외로 중단하고 덮어쓰지 않는다. 로드 시 `next_id = max(파일 next_id, 최대 id + 1)`. 모든 변경은 단일 `threading.Lock` 안에서 ① 메모리 상태 복사본에 변경 적용 → ② 같은 디렉토리 임시 파일(`<data>.tmp`, `.gitignore`의 `*.json.tmp` 패턴과 일치)에 쓰고 `flush`+`os.fsync` → ③ `os.replace`로 교체 → ④ 성공 시에만 메모리 상태를 복사본으로 교체. 쓰기 실패 시 메모리·파일 모두 이전 상태 유지, 응답 `500 {"error":"storage_error"}`. 읽기(목록·상세)도 같은 lock 아래에서 복사본을 반환한다. | 요구서 §영속성 "저장 중 다른 항목이 유실되면 안 된다"(H-1). `ThreadingHTTPServer`(`todo_web/app.py:14`, `todo_web/app.py:94`)는 요청을 스레드별로 처리 |
| D-10. 저장소 공개 인터페이스 | `todo_web/store.py`: `class TodoStore(path: Path)` — `list() -> list[dict]`, `get(todo_id: int) -> dict \| None`, `create(fields: dict) -> dict`, `update(todo_id: int, fields: dict) -> dict \| None`, `delete(todo_id: int) -> bool`. `fields`는 핸들러가 검증·정규화를 마친 값만 담는다. `StorageError(Exception)`은 파일 쓰기 실패를 감싼다. 검증 함수는 app.py에 두고 store는 검증하지 않는다. | 검증(HTTP 계약)과 영속(파일 계약)의 책임 분리. 단일 소비자이므로 추가 추상화 없음 |
| D-11. 핸들러 구성 | `make_handler(data_path)`는 `TodoStore(data_path)`를 생성해 클로저 변수로 쓰고 기존 `TodoHandler.data_path = data_path`(`todo_web/app.py:83`)를 유지한다. `GET /health`·`GET /` 분기는 `self.path`·`self.wfile`·`send_*`만 사용한다. 미정의 method는 클래스 `__getattr__`가 `do_` 접두 이름에 405 처리기를 돌려주는 방식으로 일괄 처리한다. `main()`·CLI 인자·`exports`(`main`, `make_handler`)는 바꾸지 않는다. | H-2(기존 DummyHandler 회귀), H-3. 공개 시그니처 유지 |
| D-12. 화면 | `GET /` HTML은 `<title>Todo Web</title>`·`<h1>Todo Web</h1>` 유지, `form#todo-form` 안에 `input[name=title]`(`required`, `maxlength=120`), `textarea[name=description]`(`maxlength=2000`), `button[type=submit]`("Create"), 목록 영역 `section#todo-list`(`aria-label="Todo list"`), 오류 표시 `p#error`(`role="alert"`). 인라인 `<script>`가 로드 시 `GET /api/todos`로 목록을 그리고, 제출 시 `POST /api/todos`(JSON) 후 목록 갱신, 각 항목에 완료 체크박스(`PATCH {"completed": …}`)와 삭제 버튼(`DELETE`)을 둔다. 항목 텍스트는 `textContent`로만 넣는다(HTML 주입 방지). API 오류는 응답 `error`·`message`를 `#error`에 표시한다. 외부 CSS·JS·CDN을 쓰지 않는다. | 요구서 §화면, C-1. 기존 단언(`tests/test_basic.py:56-57`) 유지 |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. 공개 HTTP 계약 RED 테스트 | opal-test-agent (red mode — 구현자와 분리) | `tests/test_todo_api.py` | TEST-SCENARIO의 `구현 전 RED` 시나리오(S-2~S-7)를 pytest 통합 테스트로 작성한다. 모듈 scope fixture가 빈 포트(`socket` bind 0)와 `tmp_path_factory` 데이터 파일로 `sys.executable -m todo_web.app --host 127.0.0.1 --port <p> --data <f>` 서브프로세스를 띄우고 `/health` 응답까지 최대 10초 폴링, 종료 시 terminate→wait. HTTP 호출은 `http.client`만 사용. 재시작 시나리오(S-6)는 같은 데이터 파일로 서버를 두 번 띄운다. 테스트는 D-1~D-9 계약만 단언하고 내부 모듈(`todo_web.store`)을 import하지 않는다. 기존 `tests/test_basic.py`는 건드리지 않는다. 구현 전 실행 시 실패(RED)를 확인해 증거로 기록한다. | 없음 | P1 | AC-2, AC-3, AC-4, AC-5, AC-6, C-2 |
| W-2. 저장소·API·화면 구현(GREEN) | opal-be-agent | `todo_web/store.py`, `todo_web/app.py` | `todo_web/store.py`를 D-9·D-10대로 신설한다(@header 포함). `todo_web/app.py`에 D-1~D-8·D-11 라우팅·검증·오류 처리와 D-12 화면을 구현하고 모듈 @header description·exports를 실제 동작에 맞게 갱신한다. 외부 패키지 import 금지. W-1 테스트의 기대 계약을 고치거나 삭제하지 않고 `python -m pytest -q` 전체(기존 `tests/test_basic.py` 포함)를 통과시킨다. | W-1 | P2 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, C-1, C-2, C-3 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. 동시 요청에서도 lock·원자 교체로 항목 유실이 없다 | AC-6 "저장 중 다른 항목이 유실되면 안 된다" — `ThreadingHTTPServer`의 동시 POST/PATCH/DELETE가 읽기-수정-쓰기 경합을 일으키면 일부 변경이 사라지거나 ID가 중복될 수 있다 | 사용자 데이터 손실, 재시작 후 항목 누락 | D-9 단일 lock + 복사본 변경 + `os.replace`. S-7이 동시 생성 후 목록·재시작 결과로 검증 |
| H-2. 기존 `DummyHandler` 언바운드 호출이 계속 동작한다 | C-2 — `GET /health`·`GET /`가 저장소·요청 헤더 등 인스턴스 속성에 의존하면 `tests/test_basic.py`가 `AttributeError`로 실패한다 | 기존 회귀 테스트 실패 | D-11(클로저 저장소, 해당 분기는 `path`·`wfile`·`send_*`만 사용). S-8이 기존 테스트 무수정 통과로 검증 |
| H-3. 정의되지 않은 method도 405 JSON으로 거부된다 | AC-5 — `BaseHTTPRequestHandler`는 `do_<METHOD>`가 없으면 HTML `501`을 보낸다(표준 라이브러리 http.server 477-481행) | 클라이언트가 405/JSON 오류를 판별하지 못함 | D-1·D-11(`__getattr__` 405 폴백, HEAD 본문 생략). S-5가 PUT·HEAD·OPTIONS·임의 method로 검증 |

## Release and recovery

- 적용 순서: P1(W-1 RED 테스트 작성·실패 증거 기록, `test-tool scenario-red`·`scenario-lock`) → P2(W-2 구현) → TEST(전 시나리오 실행, 브라우저 E2E 포함) → worktree 브랜치 `feat/OP-TASK-001` 체크포인트 → CLOSE·finalize 후 허브 `main`에 local merge(사용자가 격리 저장소 안의 local merge·finalize를 사전 승인함). push·배포는 하지 않는다.
- 검증 범위: 결정론 — pytest 통합 테스트(실제 서버 프로세스·실제 데이터 파일), 표준 라이브러리 import 검사, 변경 파일 범위 검사. 실제 연동 — headless Chromium으로 실제 화면에서 생성·완료·삭제(S-10). 설치·배포 단계는 없다.
- 실측 경계: 시간·품질 목표 없음.
- 실패 시: 배포가 없으므로 worktree 브랜치에서 수정 후 재검증한다. merge 뒤 문제가 발견되면 허브에서 해당 merge를 되돌리는 것은 사용자 승인 후 수행한다. 데이터 파일 형식(D-9)이 깨진 경우 서버는 덮어쓰지 않고 기동을 중단하므로 사용자가 파일을 복구·삭제한 뒤 재기동한다.
