---
template: sdlc-v2
---
# PLAN: TODO CRUD 웹 앱 구현

> 입력: [TASK.md](TASK.md) (PM 경로 — ANALYSIS.md 없음, 분석 결과는 아래 `## Findings`)

## 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | app.py | `todo_web/app.py` | 현재 skeleton 라우팅·응답 helper·서버 기동 |
| D-2 | 소스 | test_basic.py | `tests/test_basic.py` | 보존해야 할 기존 회귀 테스트의 호출 방식 |
| D-3 | 설계 | PROJECT.md | `docs/PROJECT.md` | 프로젝트 구조·담당 에이전트 매핑(웹 앱 → opal-be-agent) |
| D-4 | 설계 | 프로젝트 AGENT | `.opal/AGENT.md` | 표준 라이브러리 전용·범위 밖 변경 금지 |
| D-5 | 소스 | CPython http.server | `http/server.py` (설치본 `/Volumes/Data/PythonStudio/miniconda3/lib/python3.14/http/server.py`) | 미정의 method 처리 방식 |
| D-6 | 기획 | 요구서 | `REQUEST.md` (허브 상위 scratchpad) | API·화면·검증·영속성 원문 계약 |

## Approach

skeleton(`todo_web/app.py`) 한 파일 안에서 (1) JSON 파일 저장소, (2) 경로·method 라우팅과 요청 검증, (3) API를 호출하는 HTML 화면을 구현한다(→ D-1:37-84). 기존 응답 helper `_send_json`·`_send_html`(→ D-1:19-34)과 `main()`의 인자·기동 방식(→ D-1:87-101)은 그대로 재사용해 실행 계약(AC-1)을 보존한다. 공개 HTTP 동작을 먼저 고정할 수 있는 API 계약 변경이므로 RED-first를 적용한다 — 구현자와 다른 주체(opal-test-agent)가 `tests/test_todo_api.py`에 실패 테스트를 먼저 작성하고, opal-be-agent가 GREEN 구현을 한다. 범위는 TASK `Affected users and systems`의 포함 범위로 한정한다.

## Findings

### 직접 변경
- `todo_web/app.py`: CRUD 라우팅·검증·저장소·화면 구현. 현재 `do_POST`/`do_PATCH`/`do_DELETE`는 모두 404(→ D-1:74-81), GET은 health·홈 화면 외 404(→ D-1:44-72), `data_path`는 클래스 속성으로만 보관되고 쓰이지 않는다(→ D-1:83). 모듈 `@header`의 description("CRUD is intentionally unimplemented")도 사실이 바뀌므로 같은 파일에서 갱신한다(→ D-1:1-9).
- `tests/test_todo_api.py`: 신규. AC-1·AC-3~AC-8을 공개 HTTP 인터페이스로 검증하는 테스트(RED 선작성).

### 회귀 확인
- `tests/test_basic.py`: `make_handler(...)`가 반환한 클래스의 `do_GET`을 `TodoHandler` 인스턴스가 아닌 `DummyHandler` 객체로 언바운드 호출한다(→ D-2:37-58). `DummyHandler`는 `path`·`wfile`·`send_response`·`send_header`·`end_headers`만 가지며 `headers`는 응답 헤더 기록용 dict다(→ D-2:16-34). 따라서 health·홈 화면 GET 처리 경로는 `TodoHandler` 전용 메서드·속성(`self.data_path` 포함)과 요청 헤더를 쓰면 안 된다(H-1).

### 문서 갱신
없음. 프로젝트 문서 레지스트리(docs/PROJECT.md)의 구조·스택·담당 매핑은 구현 후에도 사실과 같다(→ D-3 §프로젝트 구조).

### 미확인 가정
- H-1, H-2, H-3 (아래 Risks).

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| DC-1. 경로·method 표 | 허용 조합은 `GET /health`, `GET /`, `GET·POST /api/todos`, `GET·PATCH·DELETE /api/todos/{id}`(`{id}`는 `^[0-9]+$` 10진수)뿐이다. 이 4개 경로 패턴에 맞지 않는 경로는 method와 무관하게 `404 {"error":"not_found"}`. 패턴에 맞지만 허용되지 않은 method(PUT·HEAD·OPTIONS·임의 토큰 포함)는 `405 {"error":"method_not_allowed"}`와 `Allow` 헤더. `Allow` 값은 경로별로 고정이다 — 화면·health 경로는 `GET`, 목록 경로는 `GET, POST`, 항목 경로는 `GET, PATCH, DELETE`(이 순서, `, ` 구분). query string은 무시한다. | 요구서 "지원하지 않는 method는 405"(→ D-6 §검증과 예외). 표준 처리기는 `do_<METHOD>`가 없으면 501을 보내므로(→ D-5:477-481) 미정의 method도 같은 라우팅으로 보낸다(H-3). |
| DC-2. 요청 처리 순서 | 쓰기 요청(POST·PATCH): ① 라우팅(404/405) → ② `Content-Type` 미디어 타입(`;` 앞, 공백 제거, 소문자)이 `application/json`이 아니거나 헤더가 없으면 `415 {"error":"unsupported_media_type"}` → ③ `Content-Length` 만큼 본문을 읽어 UTF-8 디코드·JSON 파싱, 실패(헤더 없음·숫자 아님·빈 본문 포함)는 `400 {"error":"invalid_json"}` → ④ PATCH는 ID 존재 확인(없으면 404) → ⑤ 필드 검증 실패는 `400 {"error":"validation_error","message":<사유>}`. 읽기·삭제(GET·DELETE `/api/todos/{id}`)는 ① 뒤 ID 존재 확인(없으면 404). | 요구서의 415·400·404 조건이 겹칠 때 결과를 하나로 고정(→ D-6 §API, §검증과 예외). |
| DC-3. 필드 검증 | 본문 JSON 최상위가 object가 아니면 validation_error. `title`: 문자열이어야 하고 앞뒤 공백(`str.strip()`) 제거 값이 1~120자(`len` 기준), 제거된 값을 저장. `description`: 문자열, 0~2000자, 공백 제거하지 않음. `completed`: JSON boolean만 허용. POST는 `title` 필수, `description` 생략 시 `""`, `completed` 생략 시 `false`(있으면 boolean 검증 후 적용). PATCH는 `title`·`description`·`completed` 중 하나 이상 필요(0개면 validation_error), 있는 필드만 같은 규칙으로 검증·반영. 그 외 키(`id` 포함)는 무시한다. | 요구서 제목·설명 길이·공백 규칙과 "하나 이상을 포함"(→ D-6 §API 5, §검증과 예외). |
| DC-4. TODO 객체·ID | 응답 객체는 정확히 `{"id": int, "title": str, "description": str, "completed": bool}`. `id`는 1부터 시작하는 정수로 생성마다 1씩 증가하며 삭제 후에도 재사용하지 않는다. 목록은 생성 순(ID 오름차순) 배열. POST 성공은 `201` + `Location: /api/todos/{id}`, PATCH 성공은 `200` + 수정 후 전체 객체, DELETE 성공은 `204`·`Content-Length: 0`·본문 없음. 성공·오류 JSON은 기존 `_send_json`의 `application/json; charset=utf-8`로 보낸다(→ D-1:19-25). | 요구서 TODO 필드·상태 코드·Location 계약(→ D-6 §API). 재사용 금지로 삭제된 ID의 상세 조회가 계속 404가 되도록 한다(AC-6). |
| DC-5. 저장 구조 | `--data` 파일은 UTF-8 JSON `{"next_id": int, "todos": [TODO 객체...]}`. 파일이 없으면 `{"next_id": 1, "todos": []}`로 간주하고 첫 쓰기 때 생성한다. 쓰기는 같은 디렉토리의 `<파일명>.tmp`(예: `todos.json.tmp`)에 전체 내용을 쓰고 flush·`os.fsync` 뒤 `os.replace`로 원자 교체한다. 손상된 파일의 복구는 범위 밖이다(예외 전파). | 요구서 영속성·"저장 중 다른 항목 유실 금지"(→ D-6 §영속성). 임시 파일명은 저장소 `.gitignore`의 `*.json.tmp` 규칙과 맞는다. |
| DC-6. 동시성 | `make_handler(data_path)`마다 `TodoStore` 인스턴스 1개를 만들고, 모든 조회·변경 연산을 그 인스턴스의 `threading.Lock` 안에서 "파일 읽기 → 변경 → 원자 저장"으로 수행한다. 메모리 캐시를 두지 않는다. | `ThreadingHTTPServer`가 요청을 스레드로 병렬 처리하므로(→ D-1:94) 직렬화가 없으면 lost update가 난다(H-2). |
| DC-7. 모듈 구조 | `todo_web/app.py` 안에 공개 클래스 `TodoStore(path: Path)`(메서드 `list() -> list[dict]`, `get(todo_id: int) -> dict \| None`, `create(title: str, description: str, completed: bool) -> dict`, `update(todo_id: int, changes: dict) -> dict \| None`, `delete(todo_id: int) -> bool`)와 모듈 수준 함수 `_dispatch(handler, method: str, store: TodoStore) -> None`를 둔다. `TodoHandler`의 `do_GET`·`do_POST`·`do_PATCH`·`do_DELETE`는 `_dispatch(self, "<METHOD>", store)` 한 줄만 호출하고(`store`는 `make_handler`의 클로저 변수), `__getattr__`가 `do_` 접두 이름에 대해 `_dispatch(self, <접미 method>, store)`를 호출하는 함수를 반환해 DC-1의 405를 처리한다. `_dispatch`의 `GET /health`·`GET /` 분기는 `handler.path`와 응답 메서드만 사용한다. `TodoHandler.data_path = data_path`(→ D-1:83)와 `main()`(→ D-1:87-101)은 유지한다. | H-1의 언바운드 호출 보존(→ D-2:37-58), C-1 표준 라이브러리 전용. |
| DC-8. 화면 | `GET /`은 기존 정적 HTML의 `<title>Todo Web</title>`·`<h1>Todo Web</h1>`·`form#todo-form`(`input[name=title]`, `textarea[name=description]`, `button[type=submit]` "Create")·`section#todo-list`(→ D-1:56-70)를 유지하고, 내장 `<script>`가 (a) 로드 시 `GET /api/todos` 결과를 `#todo-list` 안 `<ul>`의 `<li>`로 그리며(제목·설명·완료 여부, 텍스트는 `textContent`로만 삽입), (b) 폼 제출 시 기본 제출을 막고 `POST /api/todos`(`Content-Type: application/json`)를 보낸 뒤 `201`이면 폼을 비우고 `p#form-error`(`role="alert"`, 초기 빈 텍스트) 텍스트를 지운 뒤 목록을 다시 그리고, `201`이 아니면 목록을 바꾸지 않고 `p#form-error`에 응답의 `message`(없으면 `error`) 값을 표시한다. 수정·삭제 UI는 만들지 않는다. | 요구서 "화면은 API를 사용하거나 서버 렌더링" 중 API 사용 방식 선택(→ D-6 §화면). `textContent` 삽입으로 사용자 입력 HTML 주입을 막는다. |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. RED 테스트 선작성 | opal-test-agent (red mode) | `tests/test_todo_api.py` | TEST-SCENARIO의 S-1, S-3~S-9를 pytest 함수 `test_s<N>_*`로 작성한다. 서버는 in-process `ThreadingHTTPServer(("127.0.0.1", 0), make_handler(tmp_path / "todos.json"))` + 데몬 스레드, 또는 S-1·S-8은 `subprocess`로 `python -m todo_web.app --host 127.0.0.1 --port <빈 포트> --data <tmp>` 기동 후 `/health` 폴링. HTTP 호출은 `http.client`만 사용한다. 각 테스트는 DC-1~DC-6 계약을 assertion으로 고정하고 종료 시 서버·프로세스를 정리한다. 구현 파일은 수정하지 않는다. | 없음 | P1 | AC-1, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, C-2 |
| W-2. CRUD·검증·저장·화면 구현 | opal-be-agent | `todo_web/app.py` | DC-1~DC-8을 그대로 구현한다: `TodoStore`(DC-5·DC-6), `_dispatch` 라우팅·처리 순서·검증·응답(DC-1~DC-4), `TodoHandler` 위임과 `__getattr__` 405 처리(DC-7), 화면 스크립트(DC-8), 모듈 `@header` description·exports(`["main", "make_handler", "TodoStore"]`) 갱신. 표준 라이브러리만 import한다. W-1 테스트와 `tests/test_basic.py`를 수정하지 않고 통과시킨다. | W-1 | P2 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, C-1, C-2, C-3 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. 기존 테스트의 언바운드 `do_GET(DummyHandler())` 호출이 새 구조에서도 동작한다 | `tests/test_basic.py`의 health·home 테스트(→ D-2:37-58) | C-2 위반 — 기존 테스트 실패 | DC-7: 위임은 모듈 함수 + 클로저 `store`, GET `/health`·`/` 분기는 `handler.path`·응답 메서드만 사용. S-10으로 회귀 확인 |
| H-2. 병렬 요청 중에도 저장 파일이 항목을 잃지 않는다 | `ThreadingHTTPServer` 병렬 처리(→ D-1:94) 중 동시 생성·수정 | AC-8 위반 — 다른 항목 유실·깨진 JSON | DC-5 원자 교체 + DC-6 단일 Lock. S-9 동시 생성 검증 |
| H-3. 미정의 method도 405로 응답한다 | 표준 처리기는 `do_<METHOD>` 부재 시 501(→ D-5:477-481) | AC-7 위반 — PUT·HEAD·임의 method에 501 | DC-7 `__getattr__` 위임 + DC-1 라우팅. S-7에서 PUT·임의 method 검증 |

## Release and recovery

- 적용 순서: P1(W-1 RED 테스트 작성·실패 관찰·`scenario-red`·`scenario-lock`) → P2(W-2 GREEN 구현) → TEST(전체 시나리오·`python3 -m pytest -q`).
- 검증 범위: 결정론 — S-11 정적 검사; 회귀 — S-10 기존 테스트; 실제 연동 — S-1·S-3~S-9 실서버 HTTP, S-2 실브라우저.
- 실측 경계: 시간·품질 수치 목표 없음.
- 실패 시: 배포·설치가 없는 로컬 저장소 작업이므로 worktree 브랜치(`feat/OP-TASK-001`)에서 수정 커밋을 추가해 복구하고, merge 전까지 `main`은 변하지 않는다.
