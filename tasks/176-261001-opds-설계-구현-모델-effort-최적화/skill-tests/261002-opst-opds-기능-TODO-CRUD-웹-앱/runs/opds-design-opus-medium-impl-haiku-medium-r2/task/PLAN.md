---
template: sdlc-v2
---
# PLAN: TODO CRUD 웹 앱 구현

> 입력: [TASK.md](TASK.md)

## Approach
기존 `make_handler(data_path)` 구조(`todo_web/app.py:36-82`)와 `main()` CLI(`todo_web/app.py:85-98`)를 유지한 채, 영속 저장소를 새 모듈 `todo_web/store.py`로 분리하고 `app.py`의 핸들러를 메서드·경로 테이블 기반 라우팅으로 바꿔 REST API·검증·오류 응답을 구현한다. `GET /` 화면은 기존 폼·목록 마크업(`todo_web/app.py:52-66`)을 유지하고 인라인 `<script>`로 `/api/todos`를 호출해 목록을 그리고 생성한다. RED-first: API 계약 시나리오는 구현 전에 `opal-test-agent`(red mode)가 실제 서버 프로세스를 띄우는 통합 테스트로 먼저 고정하고, `opal-be-agent`가 GREEN 구현을 맡는다. 외부 패키지 없이 Python 표준 라이브러리만 쓴다(`.opal/AGENT.md` §제약).

## Findings

### 직접 변경
- `todo_web/app.py`: 현재 `do_POST`·`do_PATCH`·`do_DELETE`가 모두 `404 not_found`(`todo_web/app.py:72-79`), `GET`은 `/health`·`/`만 처리(`todo_web/app.py:42-70`). 라우팅·API·검증·HTML 스크립트를 추가하고 `@header`의 "CRUD is intentionally unimplemented" 설명(`todo_web/app.py:6`)과 `exports`를 실제 상태로 갱신한다. `TodoHandler.data_path` 속성(`todo_web/app.py:81`)과 `make_handler`·`main` 시그니처는 유지한다.
- `todo_web/store.py`: 신규. JSON 파일 영속 저장소.
- `tests/test_todo_api.py`: 신규. 실제 `python -m todo_web.app` 서버 프로세스에 HTTP로 요청하는 통합 테스트(RED 선작성).

### 회귀 확인
- `tests/test_basic.py`: `DummyHandler`로 `handler_type.do_GET(handler)`를 직접 호출하며(`tests/test_basic.py:38-58`) `handler.path`, `send_response`, `send_header`, `end_headers`, `wfile.write`만 제공한다. 따라서 `GET /health`·`GET /` 경로는 `self.headers`·`self.rfile`·`self.command`·`self.server`·저장소 접근 없이 응답해야 한다. 본문에 `"Todo Web"`과 `"todo-form"`이 계속 있어야 한다.

### 문서 갱신
없음.

### 미확인 가정
- H-1 (ThreadingHTTPServer 동시 쓰기에서 lock + 원자적 파일 교체로 항목 유실이 없다는 가정)

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| D-1. 저장 파일 형식 | `--data` 파일은 `{"next_id": <int>, "todos": [<TODO>...]}` UTF-8 JSON 객체. 파일이 없거나 크기 0이면 빈 저장소(`next_id`=1)로 시작하고 첫 쓰기 때 생성한다. 파일 내용이 JSON 파싱 불가하거나 위 형식이 아니면 서버 시작 시 예외로 종료한다(데이터 덮어쓰기 금지). | 재시작 후 유지(AC-5)와 삭제된 ID 재사용 방지를 위해 `next_id`를 함께 저장. 손상 파일을 빈 목록으로 덮으면 데이터 유실이므로 fail-fast. |
| D-2. ID 규칙 | `id`는 1부터 증가하는 정수, 삭제 후에도 재사용하지 않는다. 경로 `/api/todos/{id}`에서 `{id}`가 `^[0-9]+$`가 아니거나 존재하지 않으면 `404`. | 요구서 `Location: /api/todos/{id}`와 정합, 결정론 테스트 가능. |
| D-3. TODO 객체 | 정확히 `{"id": int, "title": str, "description": str, "completed": bool}` 4필드. 저장·응답 모두 동일. | 요구서 API §2. |
| D-4. 저장 원자성·동시성 | 저장소는 시작 시 파일을 메모리로 로드하고, 모든 변경(생성·수정·삭제)은 단일 `threading.Lock` 안에서 메모리 갱신 → 같은 디렉터리 임시 파일에 전체 문서 쓰기 → `flush`+`os.fsync` → `os.replace(tmp, data_path)` 순으로 수행한다. 쓰기 실패 시 메모리 상태를 변경 전으로 되돌리고 예외를 올린다(핸들러가 `500 {"error":"storage_error"}`). 읽기도 같은 lock으로 스냅샷 복사본을 반환한다. `--data` 상위 디렉터리 생성은 기존 `main()`(`todo_web/app.py:91`) 동작 유지. | "저장 중 다른 항목이 유실되면 안 된다"(요구서 영속성) + `ThreadingHTTPServer` 사용(`todo_web/app.py:92`). H-1 대응. |
| D-5. 저장소 지연 생성 | `make_handler(data_path)`는 호출 시점에 `TodoStore(data_path)`를 만들어 핸들러 클래스 속성 `store`로 둔다. 단, `TodoStore` 생성자는 파일을 읽기만 하고 파일을 만들지 않는다(파일 없으면 빈 상태). `/health`·`/` 처리 경로는 `store`를 건드리지 않는다. | `tests/test_basic.py`는 존재하지 않는 `tmp_path/"todos.json"`으로 `make_handler`를 호출(`tests/test_basic.py:39`)하므로 생성자가 파일 부재에 안전해야 한다. |
| D-6. 라우팅·405 | 지원 경로와 메서드: `/health`=GET, `/`=GET, `/api/todos`=GET·POST, `/api/todos/{id}`=GET·PATCH·DELETE. 경로 매칭은 `urlparse(self.path).path` 기준(쿼리 무시). 경로가 위 패턴에 매칭되지만 메서드가 목록 밖이면 `405 {"error":"method_not_allowed"}` + `Allow` 헤더(쉼표 구분 메서드 목록). 어떤 패턴에도 매칭되지 않으면 `404 {"error":"not_found"}`. 핸들러는 `do_GET`·`do_POST`·`do_PATCH`·`do_DELETE`·`do_PUT`·`do_HEAD`·`do_OPTIONS`를 정의해 모두 같은 디스패처로 보낸다(미정의 메서드의 기본 `501` 방지). `/api/todos/{id}`의 405 판정은 ID 존재 여부보다 먼저 한다. | 요구서 "지원하지 않는 method는 405". |
| D-7. 쓰기 요청 판정 순서 | `POST /api/todos`·`PATCH /api/todos/{id}`: ① 405 판정(D-6) → ② `Content-Type`의 `;` 앞 미디어 타입을 공백 제거·소문자화해 `application/json`이 아니면(헤더 없음 포함) `415 {"error":"unsupported_media_type"}` → ③ `Content-Length`만큼 본문을 읽어 UTF-8 디코드·`json.loads` 실패 시(본문 없음 포함) `400 {"error":"invalid_json"}` → ④ 최상위가 JSON 객체가 아니면 `400 {"error":"validation_error"}` → ⑤ PATCH는 ID 부재 시 `404` → ⑥ 필드 검증 실패 `400 {"error":"validation_error","message":<사유>}`. | 요구서 검증과 예외 절. 415를 JSON 파싱보다 먼저 판정해 형식 오류와 내용 오류를 구분. |
| D-8. 필드 검증 | `title`: 문자열이어야 하며 `strip()` 후 길이 1~120, 저장값은 strip된 값. `description`: 문자열, 길이 0~2000(strip하지 않음), POST에서 생략 시 `""`. `completed`: JSON boolean만 허용. POST는 `title` 필수, `completed` 생략 시 `false`. PATCH는 `title`·`description`·`completed` 중 최소 1개 필수(없으면 400), 보낸 필드만 같은 규칙으로 검증 후 반영. 알 수 없는 필드는 무시. 문자열 길이는 Python `len()`(코드포인트) 기준. | 요구서 "제목은 앞뒤 공백 제거 뒤 비어 있으면 안 된다… 최대 120자, 설명은 최대 2000자". |
| D-9. 성공 응답 | POST `201` + 생성 객체 + `Location: /api/todos/{id}`. GET 목록 `200` + id 오름차순 배열. GET 상세·PATCH `200` + 객체. DELETE `204`, 본문 없음, `Content-Type` 미전송, `Content-Length: 0`. 모든 JSON 응답은 기존 `_send_json`(`todo_web/app.py:18-24`)을 사용(`application/json; charset=utf-8`)하고, 배열 본문도 받도록 타입 힌트만 넓힌다. | 요구서 API §1~6. |
| D-10. 오류 본문 | 모든 4xx/5xx 응답은 JSON 객체이며 최소 `error`(snake_case 코드) 필드를 가진다. 코드: `not_found`, `method_not_allowed`, `unsupported_media_type`, `invalid_json`, `validation_error`, `storage_error`. `HEAD` 요청에도 동일 상태·헤더를 보내되 본문은 쓰지 않는다. | 요구서 "오류 응답은 최소한 error 필드를 가진 JSON 객체". |
| D-11. 화면 | `GET /` HTML은 기존 `<h1>Todo Web</h1>`, `<form id="todo-form">`, `input name="title"`, `textarea name="description"`, `<button type="submit">Create</button>`, `<section id="todo-list">` 구조를 유지하고 인라인 `<script>`를 추가한다. 스크립트: 로드 시 `GET /api/todos`로 목록을 그려 `#todo-list` 안에 TODO마다 `<li data-id="{id}">`(제목·설명 텍스트, `textContent`로 삽입해 HTML 이스케이프)를 렌더; 폼 submit 시 기본 제출을 막고 `fetch('/api/todos', {method:'POST', headers:{'Content-Type':'application/json'}, body})` 성공(201)이면 폼을 비우고 목록을 다시 그림; 실패 시 응답 `error`를 `<p id="form-error">`에 표시. 화면 수정·삭제 UI는 이번 범위에 넣지 않는다. | 요구서 화면 절은 목록·제목·설명·생성 버튼만 요구, API 사용 방식 허용. C-4 범위 준수. |
| D-12. 테스트 방식 | 신규 테스트는 pytest로, 빈 포트(`socket` bind 0)를 잡아 `subprocess.Popen([sys.executable, "-m", "todo_web.app", "--host", "127.0.0.1", "--port", P, "--data", tmp])`로 실제 서버를 띄우고 `/health` 폴링으로 준비를 확인한 뒤 `urllib.request`로 호출한다. 서버 재시작 검증은 프로세스 종료(`terminate`+`wait`) 후 같은 `--data`로 재기동한다. | C-1 실행 계약을 그대로 검증. 외부 패키지 불필요(C-2). |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. API 계약 RED 테스트 작성 | opal-test-agent (red mode) | `tests/test_todo_api.py` | D-12 방식의 서버 fixture와 TEST-SCENARIO의 `구현 전 RED` 시나리오(S-2~S-6) 테스트 함수를 작성한다. 각 테스트 함수 이름에 S-ID를 포함한다(예: `test_s2_create_list_detail`). 구현 전 실행해 실패를 관찰·기록한다. 이후 GREEN·fix 단계에서 기대 계약을 약화·삭제하지 않는다. | 없음 | P1 | AC-2, AC-3, AC-4, AC-5, C-1 |
| W-2. 저장소·API·화면 구현 | opal-be-agent | `todo_web/store.py`, `todo_web/app.py` | `store.py`: D-1~D-5의 `TodoStore`(`list()`, `get(id)`, `create(title, description, completed)`, `update(id, fields)`, `delete(id)`; 부재 시 `None`/`False` 반환) 구현 + `@header` 주석(기존 모듈 형식). `app.py`: D-6~D-11 라우팅·검증·응답·HTML 스크립트 구현, `@header` description·exports 갱신, `make_handler`·`main` 시그니처와 `TodoHandler.data_path` 유지. 표준 라이브러리만 import. `tests/` 파일은 수정하지 않는다. | W-1 | P2 | AC-1, AC-2, AC-3, AC-4, AC-5, C-1, C-2, C-3, C-4 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. `ThreadingHTTPServer`의 동시 쓰기 요청에서 lock + 임시 파일 `os.replace`로 항목 유실·파일 손상이 없다 | 동시 POST/PATCH/DELETE 후 파일·목록에 모든 성공 응답 결과가 반영(AC-5) | 동시 사용 시 다른 TODO가 사라지거나 재시작 후 JSON 파손 | D-4 단일 lock + 원자적 교체, TEST-SCENARIO S-6 동시 생성 후 재시작 검증 |

## Release and recovery
- 적용 순서: P1(W-1 RED 테스트 작성·실패 기록·lock) → P2(W-2 GREEN 구현) → TEST 단계 전체 시나리오와 `python -m pytest` 전체 회귀.
- 검증 범위: 실제 서버 프로세스 대상 통합 테스트(S-2~S-6), 브라우저 E2E(S-7), 기존 회귀(S-8), 표준 라이브러리 정적 확인(S-9). 설치·배포 없음 — 검증은 worktree `feat/OP-TASK-001`에서 테스트 통과로 종료.
- 실패 시: worktree 브랜치 변경만 되돌리면 되며 허브 `main`은 merge 전까지 영향 없음. 저장소는 손상 파일을 덮어쓰지 않으므로(D-1) 데이터 복구 절차 불필요.
