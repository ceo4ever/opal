---
template: sdlc-v2
---
# PLAN: TODO CRUD 웹 앱 구현

> 입력: [TASK.md](TASK.md) | 작성자: PM(coordinator)

## Approach

`todo_web/app.py`의 표준 라이브러리 `ThreadingHTTPServer` skeleton(`todo_web/app.py:36-84`)을 유지하고, JSON 파일 영속 저장소를 새 모듈 `todo_web/store.py`로 분리한 뒤 핸들러에 라우팅·검증·오류 응답을 구현한다. 화면은 서버 렌더링(초기 목록)과 인라인 JS(`fetch`로 생성 후 목록 갱신)를 함께 쓴다. API 계약은 RED-first로 먼저 실패 테스트를 고정한 뒤 구현한다. 범위는 TASK AC-1~AC-11, C-1~C-4이며 그 밖의 기능(인증, 화면의 수정·삭제 UI 등)은 만들지 않는다.

## Findings

### 직접 변경
- `todo_web/app.py`: 현재 `/health`·`/`만 응답하고 POST/PATCH/DELETE는 모두 404(`todo_web/app.py:72-79`). 라우팅·405·415·400·JSON 오류·CRUD·화면·저장소 연결을 구현하고 @header `description`/`exports`를 갱신한다.
- `todo_web/store.py`: 신규. JSON 파일 영속 저장소.
- `tests/test_todo_api.py`: 신규. 공개 HTTP 계약 RED 테스트.

### 회귀 확인
- `tests/test_basic.py`: `make_handler(data_path)`를 인자 1개로 호출하고 더미 핸들러(`path`, `wfile`, `send_response`, `send_header`, `end_headers`만 보유)로 `do_GET`을 직접 호출한다(`tests/test_basic.py:13-52`). 따라서 `make_handler` 시그니처, GET `/health`·`/` 경로가 `self.headers`·`rfile`·`command`에 의존하지 않을 것, 본문의 `Todo Web`·`todo-form` 문자열을 유지해야 한다.

### 문서 갱신
없음. 프로젝트 문서(docs/PROJECT.md)의 구조 표(todo_web, tests 경로)와 문서 레지스트리는 이번 변경으로 사실이 달라지지 않는다.

### 미확인 가정
- H-1 참조: 동시 쓰기 요청 직렬화.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| D-1 TODO 모델 | 객체 키는 정확히 `id`(정수, 1부터), `title`(문자열), `description`(문자열), `completed`(불리언) 4개. 목록은 `id` 오름차순. | 요구서 §API 2. 정수 ID는 경로 파싱이 단순하다. |
| D-2 ID 발급 | 저장 파일의 `next_id`로 단조 증가 발급하며 삭제된 ID를 재사용하지 않는다. | 삭제 후 같은 ID 재등장 시 상세 조회 404 계약(AC-7)이 흐려지는 것을 막는다. |
| D-3 저장 형식 | `--data` 파일은 UTF-8 JSON `{"next_id": <int>, "todos": [<TODO>...]}`. 파일이 없거나 크기 0이면 빈 저장소(`next_id`=1)로 시작하고 첫 쓰기 때 생성한다. 파일이 있는데 JSON 파싱 실패 또는 위 형식 아님이면 `todo_web.store.StoreError`를 던진다. | 재시작 유지(AC-11). 손상 파일을 빈 저장소로 덮어써 데이터를 잃지 않게 한다. |
| D-4 원자적 저장 | 모든 쓰기(생성·수정·삭제)는 `threading.Lock` 안에서 ① 메모리 상태의 사본에 변경 적용 → ② 같은 디렉토리의 `<data파일명>.tmp`에 전체 상태 기록 + `flush` + `os.fsync` → ③ `os.replace(tmp, data)` → ④ 성공 시에만 메모리 상태를 사본으로 교체. ②③에서 `OSError`면 메모리 상태 불변, 핸들러는 `500 {"error": "storage_error"}`. 읽기(GET)도 같은 lock 아래 메모리 상태 사본을 반환. | 부분 기록·동시 쓰기로 다른 항목 유실 방지(AC-11, H-1). `.gitignore`가 `*.json.tmp`를 이미 무시한다. |
| D-5 저장소 API | `todo_web/store.py`: `class StoreError(Exception)`, `class TodoStore(path: Path)`(생성 시 파일 로드), 메서드 `list() -> list[dict]`, `get(todo_id: int) -> dict \| None`, `create(title: str, description: str) -> dict`, `update(todo_id: int, changes: dict) -> dict \| None`, `delete(todo_id: int) -> bool`. 반환 dict는 내부 상태와 공유하지 않는 사본. 검증은 하지 않는다(핸들러 책임). | 핸들러와 영속 계층의 파일 소유권 분리. |
| D-6 `make_handler` | 시그니처 `make_handler(data_path: Path)` 유지. 내부에서 `TodoStore(data_path)`를 만들어 핸들러 클래스 속성 `store`로 둔다(기존 `data_path` 속성도 유지). | `tests/test_basic.py` 회귀(C-3). |
| D-7 `main` | 인자·기본값 유지(C-2). `args.data.parent.mkdir(...)` 뒤 `make_handler` 호출에서 `StoreError`가 나면 stderr에 `error: invalid data file <경로>: <사유>`를 출력하고 서버를 열지 않은 채 종료 코드 `2`를 반환한다. | 손상 파일 보호(D-3). |
| D-8 라우팅·method | 경로는 `urlparse(self.path).path`로만 판정(쿼리 무시). 지원 표: `/health`=GET, `/`=GET, `/api/todos`=GET·POST, `/api/todos/{id}`=GET·PATCH·DELETE. `{id}`는 정규식 `^/api/todos/([1-9][0-9]*)$`로만 매칭하고 그 외 경로(`/api/todos/abc`, `/api/todos/`, `/api/todos/0` 포함)는 모든 method에 `404 {"error": "not_found"}`. 경로가 표에 있고 method가 지원 목록 밖이면 `405 {"error": "method_not_allowed"}` + `Allow` 헤더(지원 method를 `, `로 연결). 핸들러는 `do_GET`·`do_POST`·`do_PUT`·`do_PATCH`·`do_DELETE`·`do_HEAD`·`do_OPTIONS`를 정의하고 모두 한 디스패처로 보낸다. HEAD는 상태 줄·헤더만 보내고 본문을 쓰지 않는다. | 요구서 §검증과 예외(405). 표준 라이브러리 기본은 미정의 method에 501 HTML을 내므로 흔한 method는 명시 정의한다. |
| D-9 요청 처리 순서 | 경로 매칭(404) → method 허용(405) → `{id}` 경로면 존재 확인(404) → 쓰기(POST·PATCH)만: Content-Type(415) → 본문 JSON(400) → 필드 검증(400) → 저장(500 가능) → 성공 응답. GET `/health`·`/`는 `self.headers`·`rfile`을 읽지 않는다. | 판정 순서를 하나로 고정해 테스트가 결정적이다. |
| D-10 Content-Type | `Content-Type` 헤더의 `;` 앞 미디어 타입을 공백 제거·소문자화해 `application/json`과 정확히 같을 때만 허용(`application/json; charset=utf-8` 허용). 헤더 없음·다른 값은 `415 {"error": "unsupported_media_type"}`. | 요구서 §API(쓰기 요청은 application/json만). |
| D-11 본문 파싱 | `Content-Length`(없으면 0)만큼 `rfile`에서 읽고 UTF-8 디코드 후 `json.loads`. `Content-Length`가 정수가 아니거나, 디코드·파싱 실패, 빈 본문이면 `400 {"error": "invalid_json"}`. 파싱 결과가 JSON 객체(dict)가 아니면 `400 {"error": "validation_error"}`. | AC-8. |
| D-12 POST 검증 | `title` 필수·문자열이어야 하며 `strip()` 결과가 비어 있지 않고 길이(코드 포인트) ≤120. 저장값은 `strip()` 결과. `description`은 선택(없으면 `""`), 있으면 문자열·길이 ≤2000이며 원문 그대로 저장. 그 외 키(`completed` 포함)는 무시하고 `completed`는 항상 `false`로 생성. 성공 시 `201`, 본문=생성 객체, `Location: /api/todos/{id}`. | 요구서 §API 3, §검증과 예외. |
| D-13 PATCH 검증 | 본문에 `title`·`description`·`completed` 중 하나 이상이 없으면 `400 validation_error`. 있는 키만 검증·반영: `title`·`description`은 D-12와 같은 규칙, `completed`는 JSON 불리언만 허용(`null`·문자열·숫자는 400). 그 외 키는 무시. 성공 시 `200`, 본문=수정된 객체. 다른 항목은 변경하지 않는다. | 요구서 §API 5. |
| D-14 DELETE | 성공 시 `204`, 헤더 `Content-Length: 0`, 본문 없음. | 요구서 §API 6. |
| D-15 오류 본문 | 모든 오류는 `Content-Type: application/json; charset=utf-8`이고 본문 `{"error": <코드>, "message": <사람이 읽는 설명>}`. 코드는 `not_found`·`method_not_allowed`·`unsupported_media_type`·`invalid_json`·`validation_error`·`storage_error` 6종만 쓴다. | AC-10. |
| D-16 화면 | `GET /` HTML은 기존 `<title>Todo Web</title>`, `<h1>Todo Web</h1>`, `form#todo-form`(입력 `name="title"`, `textarea name="description"`, `button type="submit"` 텍스트 `Create`), `section#todo-list`를 유지한다. 서버가 응답 시점 저장소 목록을 `section#todo-list` 안 `<ul>`의 `<li data-id="{id}">`로 렌더링하며 제목·설명은 `html.escape`로 이스케이프한다. 폼 아래 `<p id="form-error" role="alert"></p>`를 둔다. 인라인 `<script>`는 submit 시 기본 동작을 막고 `fetch('/api/todos', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({title, description})})`를 호출, `201`이면 폼을 비우고 `GET /api/todos` 결과로 `<ul>`을 다시 그리며(`textContent` 사용), 실패면 응답 `message`를 `#form-error`에 표시한다. | AC-1. 서버 렌더링으로 브라우저 없이도 목록 표시를 검증할 수 있다. |
| D-17 RED 테스트 방식 | `tests/test_todo_api.py`는 pytest fixture로 `ThreadingHTTPServer(("127.0.0.1", 0), make_handler(tmp_path/"todos.json"))`를 데몬 스레드에서 띄우고 `http.client`로 요청한다. 재시작 영속성은 `subprocess`로 `python -m todo_web.app --host 127.0.0.1 --port <빈 포트> --data <파일>`을 실행해 검증한다. 테스트는 표준 라이브러리와 pytest만 쓴다. | 공개 HTTP 인터페이스 검증(red-first §2), C-1. |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. RED 계약 테스트 작성 | opal-test-agent (red mode) | `tests/test_todo_api.py` | D-17 방식으로 TEST-SCENARIO의 `구현 전 RED` 시나리오(S-1~S-8) 각각을 pytest 테스트로 작성하고, 구현 전 실행해 실패를 관찰·기록한다. 기존 `tests/test_basic.py`는 수정하지 않는다. | 없음 | P1 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, AC-9, AC-10, AC-11, C-2 |
| W-2. 저장소·API·화면 구현 | opal-be-agent | `todo_web/store.py`, `todo_web/app.py` | `todo_web/store.py` 신규 작성(D-2~D-5, @header 포함). `todo_web/app.py`에 D-6~D-16 구현, @header `description`을 CRUD 구현 사실로 갱신. 외부 패키지 import 금지. W-1 테스트를 수정·약화하지 않고 GREEN으로 만든다. | W-1 | P2 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, AC-9, AC-10, AC-11, C-1, C-2, C-3, C-4 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. `ThreadingHTTPServer`가 요청마다 스레드를 쓰므로 동시 쓰기 요청이 같은 파일 상태를 읽고-수정-쓰기하면 한쪽 변경이 덮어써질 수 있다 | AC-11 "저장 중 다른 항목이 유실되면 안 된다" | 동시 생성 시 TODO 유실 | D-4의 단일 lock 직렬화 + 원자적 교체(W-2). 동시 POST 후 목록·파일 건수 검증 시나리오(S-7) |

## Release and recovery
- 적용 순서: P1(W-1 RED 테스트 작성·실패 관찰) → P2(W-2 구현) → 전체 `pytest` 회귀 → 실제 서버 프로세스 기동 검증. 배포·설치 대상은 없으며 검증 종료 지점은 워크트리 브랜치 `feat/OP-TASK-001`에서 전체 테스트와 실제 서버 기동 시나리오 통과다.
- 검증 범위: 결정론(pytest 계약 테스트), 회귀(`tests/test_basic.py`), 실제 연동(`python -m todo_web.app` 프로세스 기동·재시작·HTML 응답).
- 실패 시: 코드 변경은 워크트리 브랜치에만 있으므로 merge 전에는 브랜치를 버리면 허브 `main`은 영향이 없다. merge 후 문제는 해당 merge 커밋 revert로 복구한다. 데이터 파일이 손상되면 서버는 D-7대로 기동을 거부하고 파일을 덮어쓰지 않으므로, 사용자가 파일을 복구하거나 다른 `--data` 경로로 재기동한다.
