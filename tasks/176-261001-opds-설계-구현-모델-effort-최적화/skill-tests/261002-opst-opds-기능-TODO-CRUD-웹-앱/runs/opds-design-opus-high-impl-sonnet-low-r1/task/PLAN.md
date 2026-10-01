---
template: sdlc-v2
---
# PLAN: TODO CRUD 웹 앱 구현

> 입력: [TASK.md](TASK.md) | 작성자: PM(actor=coordinator, PM 경로 — ANALYSIS.md 없음, 분석 결과는 아래 Findings)

## Approach
기존 표준 라이브러리 HTTP skeleton(`todo_web/app.py:37-84`)을 유지한 채 두 층으로 확장한다.

1. 저장 층: 새 모듈 `todo_web/store.py`의 `TodoStore`가 `--data` JSON 파일을 단일 진실 원천으로 소유한다. 모든 변경은 프로세스 내 단일 잠금 아래에서 "새 상태 계산 → 임시 파일 기록 → 원자적 교체 → 메모리 반영" 순서로 수행한다.
2. HTTP 층: `todo_web/app.py`의 `make_handler`가 `TodoStore`를 만들고, 핸들러가 경로·method 라우팅, `Content-Type`·JSON·필드 검증, JSON 응답·오류 형식을 담당한다. `GET /` HTML은 기존 요소(`Todo Web`, `todo-form`, `todo-list`)를 보존하면서 `/api/todos`를 호출하는 인라인 스크립트로 목록 표시·생성·완료 토글·삭제를 제공한다.

검증은 RED-first로 진행한다. `opal-test-agent`(red mode)가 실제 서버 프로세스를 띄우는 공개 HTTP 계약 테스트를 먼저 작성해 실패를 기록하고, `opal-be-agent`가 GREEN 구현을 맡는다. 화면 동작은 구현 후 실제 브라우저(Playwright headless Chromium)로 확인한다.

범위 밖: 인증, 다중 사용자, 페이지네이션, 검색, 외부 패키지, 실행 인터페이스 변경.

## Findings

### 직접 변경
- `todo_web/app.py` — 현재 `GET /health`·`GET /`만 처리하고(`todo_web/app.py:44-72`) `POST`·`PATCH`·`DELETE`는 모두 `404`를 반환한다(`todo_web/app.py:74-81`). `data_path`는 클래스 속성으로만 붙고 사용되지 않는다(`todo_web/app.py:83`). 라우팅·검증·응답·HTML 스크립트를 이 파일에 구현하고 @header `description`을 실제 동작으로 갱신한다.
- `todo_web/store.py` — 신규. 파일 기반 TODO 저장소(잠금·원자적 교체)를 둔다.
- `tests/test_todo_api.py` — 신규. 실제 서버 프로세스를 띄우는 HTTP 계약·영속성 테스트(RED 단계에서 작성).

### 회귀 확인
- `tests/test_basic.py` — `make_handler(tmp_path / "todos.json")`로 핸들러 클래스를 만든 뒤 `TodoHandler`가 아닌 `DummyHandler` 인스턴스를 `self`로 `do_GET`에 넘긴다(`tests/test_basic.py:16-57`). `DummyHandler`의 `headers`는 응답 헤더 수집용 빈 dict이고 `rfile`·핸들러 클래스 속성은 없으므로(`tests/test_basic.py:16-34`) `GET /health`·`GET /` 경로는 요청 헤더·본문·클래스 속성에 접근하면 안 된다(H-2). 응답 본문에 `Todo Web`·`todo-form`이 계속 있어야 한다(`tests/test_basic.py:55-57`).
- `.gitignore` — `data/`와 `*.json.tmp`가 이미 ignore되어 기본 데이터 파일과 임시 파일이 커밋 대상이 되지 않는다(`.gitignore:9,14`). 변경하지 않는다.

### 문서 갱신
없음. 프로젝트 구조 표(웹 앱 요소 = todo_web/, tests/, Python 3 표준 라이브러리, pytest)와 문서 레지스트리의 사실이 이번 변경으로 바뀌지 않는다. code-scan은 `headerSource: inline`이므로 신규 모듈의 @header가 곧 코드맵 갱신이다.

### 미확인 가정
없음. 실행 환경은 확인했다 — Python 3.14.3·pytest 9.0.2(`python3 -m pytest --version`), OPAL venv의 Playwright headless Chromium 기동 성공(2026-10-02 PM 프로브).

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| D-1. 저장 파일 형식 | `--data` 파일 내용은 `{"next_id": <int>, "todos": [<TODO>...]}`(UTF-8, `ensure_ascii=False`, `indent=2`). `todos`는 `id` 오름차순(생성 순). 파일이 없거나 0바이트면 빈 상태(`next_id=1`, `todos=[]`)로 시작하고, 첫 변경 때 파일을 만든다. `next_id`가 없으면 `max(id)+1`(없으면 1). | `next_id`로 삭제된 ID 재사용을 막아 `Location`·상세 조회의 의미를 고정한다. 요구서 §영속성. |
| D-2. 손상 파일 처리 | 파일이 존재하고 내용이 JSON 파싱 불가이거나 최상위가 객체가 아니거나 `todos`가 리스트가 아니면 `TodoStore` 생성 시 `ValueError`를 던진다. 서버는 기동하지 않고(예외 전파로 비정상 종료) 파일은 수정하지 않는다. | 손상 파일 위에 빈 상태를 덮어써 기존 항목을 잃는 경로를 차단한다(AC-8 "다른 항목 유실 금지"). |
| D-3. 쓰기 원자성·동시성 | `TodoStore`는 `threading.Lock` 하나로 모든 읽기·변경을 직렬화한다. 변경은 현재 상태의 깊은 복사본에 적용 → 같은 디렉토리의 `<파일명>.tmp`에 기록 → `flush`+`os.fsync` → `os.replace(tmp, path)` → 성공 후에만 메모리 상태 교체. 기록 실패 시 예외를 전파하고 메모리 상태는 바뀌지 않는다. | `ThreadingHTTPServer`(`todo_web/app.py:94`)가 요청을 스레드로 병렬 처리하므로 잠금 없는 read-modify-write는 항목을 잃는다(H-1). 원자적 교체로 부분 기록 파일을 남기지 않는다. |
| D-4. `TodoStore` 공개 인터페이스 | `TodoStore(path: Path)`; `list() -> list[dict]`; `get(todo_id: int) -> dict \| None`; `create(title: str, description: str) -> dict`; `update(todo_id: int, changes: dict) -> dict \| None`(`changes` 키는 `title`·`description`·`completed`의 부분집합); `delete(todo_id: int) -> bool`. 반환 dict는 내부 상태의 복사본이다. 검증은 하지 않는다(HTTP 층 책임). | 저장과 HTTP 검증의 책임을 분리해 각각 독립 검증 가능하게 한다. |
| D-5. TODO 객체 | 정확히 4키 `{"id": int, "title": str, "description": str, "completed": bool}`. `id`는 1부터 증가하는 정수. | 요구서 §API 2. |
| D-6. 라우팅 | 경로는 `urlparse(self.path).path`로 판정(쿼리 무시). 허용 표: `/health`→{GET}, `/`→{GET}, `/api/todos`→{GET, POST}, `/api/todos/<id>`(정규식 `^/api/todos/(\d+)$`)→{GET, PATCH, DELETE}. 표에 없는 경로는 GET·POST·PATCH·DELETE 모두 `404 not_found`(예: `/api/todos/`, `/api/todos/abc`). 표에 있는 경로에 허용되지 않은 method는 `405 method_not_allowed` + `Allow` 헤더(허용 method를 `, `로 연결). | 요구서 §API·§검증과 예외("지원하지 않는 method는 405"). |
| D-7. 그 외 method | GET·POST·PATCH·DELETE 이외 method(PUT, HEAD, OPTIONS 등 임의 method)는 경로와 무관하게 `405 method_not_allowed`. 구현: 핸들러 클래스에 `__getattr__`을 정의해 `do_`로 시작하는 미정의 속성 조회에 405 응답 함수를 반환하고, 그 외 이름은 `AttributeError`를 던진다. | `BaseHTTPRequestHandler`는 `do_<METHOD>`가 없으면 `501`을 반환하므로 명시 대응이 필요하다. 임의 method까지 405로 닫는다. |
| D-8. 쓰기 요청 처리 순서 | POST·PATCH는 ① 라우팅/405 → ② `Content-Type` 미디어 타입(`;` 앞, 공백 제거, 소문자)이 정확히 `application/json`이 아니면(헤더 부재 포함) `415 unsupported_media_type` → ③ `Content-Length`(부재 시 0)만큼 본문을 읽어 UTF-8 디코드 + `json.loads`; `Content-Length`가 정수가 아니거나 음수, 디코드·파싱 실패, 빈 본문은 `400 invalid_json` → ④ 최상위가 객체가 아니면 `400 validation_error` → ⑤ 필드 검증 실패 `400 validation_error` → ⑥ 저장소 호출, 대상 없음 `404 not_found`. `charset` 등 파라미터는 허용한다(`application/json; charset=utf-8`). | 요구서 §API("쓰기 요청은 application/json만"), §검증과 예외. 순서를 고정해 구현자 선택을 남기지 않는다. |
| D-9. 필드 검증 | 길이는 Python `len()`(문자 수) 기준. `title`: `str`이어야 하고 `strip()` 결과가 비어 있지 않으며 `len(strip 결과) ≤ 120`; 저장값은 `strip()` 결과. `description`: `str`이고 `len ≤ 2000`; 저장값은 원문 그대로. `completed`: `bool`(JSON `true`/`false`)만 허용. POST: `title` 필수, `description` 선택(기본 `""`), `completed`를 포함한 그 외 키는 무시(새 TODO는 항상 `completed=false`). PATCH: `title`·`description`·`completed` 중 하나 이상 필수(없으면 400), 각 필드는 위 규칙으로 검증, 그 외 키는 무시, 지정한 필드만 바뀐다. `null`은 어느 필드에서도 타입 불일치로 400. | 요구서 §검증과 예외(공백 제거 후 비어 있으면 안 됨, 120/2000자). |
| D-10. 응답 형식 | JSON 응답은 `Content-Type: application/json; charset=utf-8` + `Content-Length`(기존 `_send_json` 확장: 추가 헤더 인자). 성공: `GET` 목록 200 배열, 상세 200 객체, `POST` 201 객체 + `Location: /api/todos/{id}`, `PATCH` 200 객체, `DELETE` 204(본문·`Content-Type`·`Content-Length` 없음). 오류: `{"error": <code>, "message": <설명>}`, code는 `not_found`·`method_not_allowed`·`unsupported_media_type`·`invalid_json`·`validation_error`·`storage_error`(저장 실패 시 500) 중 하나. | 요구서 §API·§검증과 예외("오류 응답은 최소한 error 필드를 가진 JSON 객체"). RFC 9110 §8.6: 204에는 Content-Length를 보내지 않는다. |
| D-11. 저장소 바인딩 | `make_handler(data_path)`가 `store = TodoStore(data_path)`를 만들고 핸들러 메서드는 클로저 변수 `store`로 접근한다. `GET /health`·`GET /` 처리 경로는 `self.path`와 응답 메서드(`send_response`·`send_header`·`end_headers`·`wfile`) 외의 핸들러 상태(`self.headers`, `self.rfile`, 클래스 속성)에 접근하지 않는다. 기존 `TodoHandler.data_path = data_path` 대입은 유지한다. | 기존 테스트가 `DummyHandler`를 `self`로 넘기므로(`tests/test_basic.py:36-57`) 클래스 속성·요청 상태 의존은 C-2를 깬다(H-2). |
| D-12. 화면 | `GET /`은 `text/html; charset=utf-8` 문서. 유지 요소: `<h1>Todo Web</h1>`, `form#todo-form`, `section#todo-list`(`aria-label="Todo list"`). 추가·변경: 제목 `input#title[name=title][maxlength=120][required]`, 설명 `textarea#description[name=description][maxlength=2000]`, 생성 버튼 `button#create-button[type=submit]`(텍스트 `Create`), 오류 표시 `p#form-error[role=alert]`, 목록 `ul#todo-items`(`section#todo-list` 안). 인라인 스크립트: 로드 시 `GET /api/todos`로 목록 렌더(항목 `li[data-id]` 안에 제목 `span.todo-title`, 설명 `span.todo-description`, 완료 체크박스 `input.todo-toggle[type=checkbox]`, 삭제 버튼 `button.todo-delete`). 폼 submit은 기본 동작을 막고 `POST /api/todos`(`Content-Type: application/json`)로 생성 → 201이면 폼 초기화 후 목록 재조회, 오류면 응답 `message`를 `#form-error`에 표시. 체크박스 변경은 `PATCH {"completed": <checked>}`, 삭제 버튼은 `DELETE` 후 목록 재조회. 사용자 입력은 `textContent`로만 넣는다(`innerHTML` 금지). | 요구서 §화면. 기존 테스트 문자열(`tests/test_basic.py:55-57`) 보존. XSS 차단. |
| D-13. 실행 인터페이스 | `main()`의 인자(`--host`, `--port`, `--data`)·기본값·`args.data.parent.mkdir(...)`·`ThreadingHTTPServer` 사용은 유지한다(`todo_web/app.py:87-101`). 손상 데이터 파일이면 D-2 예외가 전파되어 프로세스가 0이 아닌 코드로 종료된다. | C-3 실행 계약 보존. |
| D-14. RED 테스트 계약 | `tests/test_todo_api.py`는 pytest 테스트로, 빈 포트를 `socket` bind(포트 0)로 얻어 `subprocess.Popen([sys.executable, "-m", "todo_web.app", "--host", "127.0.0.1", "--port", <port>, "--data", <tmp_path>/"todos.json"], cwd=<저장소 루트>)`로 서버를 띄우고 `GET /health` 200을 최대 10초 폴링한 뒤 `http.client`로 요청한다. 종료는 `terminate()` + `wait(timeout=5)`. 외부 패키지를 쓰지 않는다. 테스트 함수와 시나리오 대응은 TEST-SCENARIO의 S-ID 이름(`test_s2_...`)으로 둔다. | 실제 서버 프로세스·실제 파일을 쓰는 공개 인터페이스 검증(`harness/red-first.md` §2). C-1. |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. RED 계약 테스트 작성 | opal-test-agent (red mode, 파일 소유) | `tests/test_todo_api.py` | D-14 하네스로 TEST-SCENARIO의 `구현 전 RED` 시나리오(S-2~S-8)를 테스트 함수로 작성·실행해 실패를 `test-tool scenario-red`로 기록하고 `scenario-lock`. 프로덕션 코드는 수정하지 않는다. | 없음 | P1 | AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, C-4 |
| W-2. 저장소·HTTP API·화면 구현(GREEN) | opal-be-agent (파일 소유) | `todo_web/store.py`, `todo_web/app.py` | `todo_web/store.py` 신규: D-1~D-5 `TodoStore`와 @header(`exports: ["TodoStore"]`). `todo_web/app.py`: D-6~D-13 라우팅·검증·응답·405 catch-all·HTML/스크립트, `_send_json`에 추가 헤더 인자, @header `description` 갱신. W-1 테스트를 수정·약화하지 않고 `tests/` 전체를 통과시킨다. | W-1 | P2 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, C-1, C-2, C-3, C-4, C-5 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. 동시 요청의 read-modify-write 경합 | 동시에 들어온 생성·수정·삭제 중 일부가 파일·메모리에서 사라지거나, 기록 도중 중단 시 반쯤 쓴 파일이 남음 | 사용자 데이터 유실(AC-8 위반) | D-3 단일 잠금 + 임시 파일 `os.replace`. S-8에서 동시 생성 후 재시작 보존을 검증 |
| H-2. 기존 테스트의 `DummyHandler` 호출 방식 | `GET /health`·`GET /`가 요청 헤더(`self.headers`는 빈 dict)·`self.rfile`·클래스 속성에 의존하면 `tests/test_basic.py`가 `AttributeError`·`KeyError`로 실패 | 기존 회귀 테스트 실패(C-2 위반) | D-11 클로저 바인딩과 GET 경로 접근 제한. S-10에서 `tests/` 전체 통과 확인 |

## Release and recovery
- 적용 순서: P1(W-1 RED 테스트 작성·실패 기록·잠금) → P2(W-2 GREEN 구현) → TEST(전체 시나리오 실행) → CLOSE(worktree 브랜치 체크포인트·finalize → 캡틴 승인 범위 내 로컬 `main` merge).
- 검증 범위: 결정론 계약 테스트(실제 서버 프로세스·실제 JSON 파일), 기존 회귀(`tests/` 전체), 실제 브라우저 E2E(화면), 정적 확인(표준 라이브러리 import·변경 범위).
- 배포·설치 없음: 검증은 worktree에서 TEST 단계 통과로 종료한다.
- 실패 시: 구현은 worktree 브랜치 `feat/OP-TASK-001`에만 존재하므로 merge 전 실패는 브랜치 폐기로 복구된다. 데이터 파일은 D-2에 따라 손상 시 덮어쓰지 않는다.
