---
template: sdlc-v2
---
# TEST-SCENARIO: TODO CRUD 웹 앱 구현

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: worktree 루트(`.opal-worktrees/task_001`)에서 Python 3.14 + pytest 9 실행. 외부 패키지 설치 없음.
- 공통 데이터: 시나리오마다 pytest `tmp_path` 아래 새 `todos.json` 경로(파일 미존재 상태에서 시작). 포트는 OS 할당 빈 포트(in-process는 포트 0, subprocess는 빈 포트 탐색 후 전달).
- 서버 기동 방식: in-process 시나리오는 `ThreadingHTTPServer(("127.0.0.1", 0), make_handler(<data>))`를 데몬 스레드로 띄우고 종료 시 `shutdown()`·`server_close()`. subprocess 시나리오(S-1·S-8)는 `python -m todo_web.app --host 127.0.0.1 --port <PORT> --data <data>`로 띄우고 `GET /health`가 200이 될 때까지 최대 10초 폴링, 종료 시 terminate·wait.
- HTTP 클라이언트: 표준 라이브러리 `http.client`(요청 헤더·method를 임의로 지정하기 위해).
- 대역 사용과 한계: 사용하지 않음. 모든 API 시나리오는 실제 소켓 HTTP 서버를 호출한다.
- 실행 조건: 자동 실행. S-2는 실제 브라우저 자동화(Playwright 브라우저 도구)로 실행하며 사람 조치가 없다.
- RED 대상: `시점`이 `구현 전 RED`인 S-3~S-9. W-1이 `tests/test_todo_api.py`에 `test_s<N>_*` 함수로 작성하고 현재 skeleton에서 실패를 관찰한다.
- 병렬 그룹: 선언 없음(순차).

## Scenarios

| ID | 유형 | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|---|
| S-1 | integration | AC-1 | 빈 포트, 미존재 data 경로 | `python -m todo_web.app --host 127.0.0.1 --port <PORT> --data <tmp>/todos.json` subprocess 기동 후 `GET /health` | 프로세스가 기동 상태로 응답하고 `GET /health`가 `200`, 본문 JSON이 정확히 `{"ok": true}` | `python3 -m pytest -q tests/test_todo_api.py -k test_s1_` | 구현 후 |
| S-2 | e2e | AC-2 | S-1과 같은 방식으로 기동한 서버, 빈 data 파일 | 브라우저로 `http://127.0.0.1:<PORT>/` 열기 → 제목·설명 입력 → Create 클릭 → 새로고침 → 제목 공백만 입력 후 Create | 아래 §S-2 assertion a1~a5 전부 충족 | Playwright 브라우저(실브라우저, headless 허용) | 구현 후 |
| S-3 | integration | AC-3 | in-process 서버, 빈 저장소 | `POST /api/todos` `Content-Type: application/json` 본문 `{"title": "  장보기  ", "description": "우유"}`; 이어서 `Content-Type: application/json; charset=utf-8`로 `{"title": "두번째"}` | 첫 응답 `201`, 본문 `{"id": 1, "title": "장보기", "description": "우유", "completed": false}`, `Location: /api/todos/1`, 응답 `Content-Type`이 `application/json`으로 시작. 둘째 응답 `201`, `id` 2, `description` `""`, `completed` `false`, `Location: /api/todos/2` | `python3 -m pytest -q tests/test_todo_api.py -k test_s3_` | 구현 전 RED |
| S-4 | integration | AC-4 | in-process 서버, TODO 2건 생성 | `GET /api/todos`, `GET /api/todos/1`, `GET /api/todos/999`, `GET /api/todos/abc` | 목록 `200`, ID 1·2 객체를 생성 순으로 담은 배열(각 객체 키 집합이 정확히 `id,title,description,completed`). 상세 `200`과 목록의 ID 1 객체와 동일. `999`·`abc`는 `404`이고 본문이 `error` 키를 가진 JSON 객체 | `python3 -m pytest -q tests/test_todo_api.py -k test_s4_` | 구현 전 RED |
| S-5 | integration | AC-5 | in-process 서버, TODO A(id 1)·B(id 2) 생성 | `PATCH /api/todos/1` `{"completed": true}` → `PATCH /api/todos/1` `{"title": "  새 제목 "}` → `GET /api/todos/2` → `PATCH /api/todos/999` `{"completed": true}` | 첫 PATCH `200`, `completed` true이고 title·description은 생성 값 유지. 둘째 PATCH `200`, title `"새 제목"`, `completed` true 유지. B는 생성 직후 객체와 완전히 동일. `999`는 `404`, `error` 키 JSON | `python3 -m pytest -q tests/test_todo_api.py -k test_s5_` | 구현 전 RED |
| S-6 | integration | AC-6 | in-process 서버, TODO 2건 생성 | `DELETE /api/todos/1` → `GET /api/todos/1` → `GET /api/todos` → `DELETE /api/todos/1` → `POST /api/todos` 새 항목 | 첫 DELETE `204`, 응답 본문 0바이트. 이후 상세 `404`, 목록에는 ID 2만 존재. 재 DELETE `404`(`error` 키 JSON). 새 항목의 `id`는 3(삭제 ID 재사용 없음) | `python3 -m pytest -q tests/test_todo_api.py -k test_s6_` | 구현 전 RED |
| S-7 | integration | AC-7, H-3 | in-process 서버, TODO 1건(id 1) 생성 | 아래 §S-7 요청 표의 각 요청을 순서대로 전송 | 각 요청의 상태 코드가 표와 일치하고, 모든 오류 응답 본문이 `error` 문자열 키를 가진 JSON 객체이며 표에 적힌 `error` 값과 일치. 405 응답은 `Allow` 헤더가 표의 값. 거부된 요청 뒤 `GET /api/todos`가 거부 전과 동일(경계 성공 요청 2건만 추가) | `python3 -m pytest -q tests/test_todo_api.py -k test_s7_` | 구현 전 RED |
| S-8 | integration | AC-8 | 빈 포트, 미존재 data 경로 | subprocess 서버 1차 기동 → TODO 3건 생성, id 2 `PATCH {"completed": true, "description": "수정"}`, id 3 `DELETE` → 프로세스 종료 → 같은 `--data`로 2차 기동 → `GET /api/todos`, `GET /api/todos/3` → `POST` 1건 | 2차 기동 후 목록이 1차 종료 직전 목록과 완전히 동일(id 1 원본, id 2 수정 반영, id 3 없음). `GET /api/todos/3`은 `404`. data 파일은 `json.load` 가능한 유효 JSON. 재기동 후 새 항목 `id`는 4 | `python3 -m pytest -q tests/test_todo_api.py -k test_s8_` | 구현 전 RED |
| S-9 | integration | AC-8, H-2 | in-process 서버, 빈 저장소 | 스레드 30개에서 동시에 `POST /api/todos`(`{"title": "t<i>"}`, i=0..29) → 완료 후 스레드 10개에서 서로 다른 ID 10건 동시 `PATCH {"completed": true}` → `GET /api/todos` → data 파일 직접 `json.load` | 30개 POST 전부 `201`, 반환 `id` 30개 서로 다름. PATCH 10건 전부 `200`. 목록 30건이고 제목 집합이 `t0..t29`와 같으며 정확히 10건만 `completed` true. data 파일도 같은 30건·같은 completed 상태 | `python3 -m pytest -q tests/test_todo_api.py -k test_s9_` | 구현 전 RED |
| S-10 | regression | C-2, H-1 | 구현 완료 상태, `tests/test_basic.py` 미수정 | `python3 -m pytest -q tests/test_basic.py` 실행, `git diff main -- tests/test_basic.py` 확인 | 2 passed, 0 failed. `tests/test_basic.py` diff 없음 | pytest, worktree | 구현 후 |
| S-11 | check | C-1, C-3 | 구현 완료 상태 | ① `todo_web/` 아래 모든 `.py`의 import 최상위 모듈을 `ast`로 수집해 `sys.stdlib_module_names` ∪ `{"todo_web"}`와 비교 ② 저장소 루트에 의존성 선언 파일(`requirements*.txt`, `pyproject.toml`, `setup.py`, `setup.cfg`, `Pipfile`) 존재 여부 ③ `git diff --name-only main` + `git ls-files --others --exclude-standard` 변경 경로 집합 | ① 표준 라이브러리 외 모듈 0개 ② 해당 파일 0개 ③ 변경 경로가 `todo_web/app.py`, `tests/test_todo_api.py`, `tasks/001-261002-opds-TODO-CRUD-웹앱/` 하위로만 구성 | python 스크립트 + git, worktree | 구현 후 |

### S-2

- 계약: `surface_kind: web_ui`, `profile: browser`, `actors: [agent]`.
- steps: `st1`(browser) 페이지 열기, `st2`(browser) `input[name=title]`에 `브라우저 할 일`, `textarea[name=description]`에 `e2e 설명` 입력 후 `button[type=submit]` 클릭, `st3`(browser) 페이지 새로고침, `st4`(browser) `input[name=title]`에 공백 3칸 입력 후 클릭.
- assertions:
  - `a1`: 페이지 제목 `Todo Web`이고 `#todo-list`, `input[name=title]`, `textarea[name=description]`, `button[type=submit]`(텍스트 `Create`)가 모두 보인다.
  - `a2`: `st2` 뒤 페이지 이동 없이 `#todo-list` 안에 텍스트 `브라우저 할 일`과 `e2e 설명`을 포함한 항목이 나타나고 제목 입력란이 비워진다.
  - `a3`: `st2` 뒤 `GET /api/todos`에 title `브라우저 할 일`·description `e2e 설명`·completed false 항목이 정확히 1건 있다.
  - `a4`: `st3` 뒤에도 `#todo-list`에 `브라우저 할 일` 항목이 보인다.
  - `a5`: `st4` 뒤 `#form-error`에 비어 있지 않은 오류 텍스트가 보이고 `GET /api/todos` 항목 수가 1로 유지된다.
- required_evidence: `st2`·`st4` 직후 스크린샷, `a3`·`a5` 시점의 `GET /api/todos` 응답 본문.

### S-7

`Content-Type`을 적지 않은 쓰기 요청은 `application/json`을 보낸다. 길이 경계 문자열은 ASCII 반복(`"a" * N`)으로 만든다.

| # | 요청 | 기대 상태 | 기대 `error` / 헤더 |
|---|---|---|---|
| 1 | `POST /api/todos` `{"title": "   "}` | 400 | `validation_error` |
| 2 | `POST /api/todos` `{"description": "x"}`(title 없음) | 400 | `validation_error` |
| 3 | `POST /api/todos` `{"title": 123}` | 400 | `validation_error` |
| 4 | `POST /api/todos` title 121자 | 400 | `validation_error` |
| 5 | `POST /api/todos` title 120자 | 201 | — (경계 성공) |
| 6 | `POST /api/todos` `{"title": "d", "description": <2001자>}` | 400 | `validation_error` |
| 7 | `POST /api/todos` `{"title": "d", "description": <2000자>}` | 201 | — (경계 성공) |
| 8 | `POST /api/todos` 본문 `{"title": ` (깨진 JSON) | 400 | `invalid_json` |
| 9 | `POST /api/todos` 본문 `[1, 2]` | 400 | `validation_error` |
| 10 | `POST /api/todos` `Content-Type: text/plain` 본문 `{"title": "x"}` | 415 | `unsupported_media_type` |
| 11 | `POST /api/todos` `Content-Type` 헤더 없음 | 415 | `unsupported_media_type` |
| 12 | `PATCH /api/todos/1` `{}` | 400 | `validation_error` |
| 13 | `PATCH /api/todos/1` `{"completed": "yes"}` | 400 | `validation_error` |
| 14 | `PATCH /api/todos/1` `{"title": ""}` | 400 | `validation_error` |
| 15 | `PATCH /api/todos/1` `Content-Type: text/plain` | 415 | `unsupported_media_type` |
| 16 | `PATCH /api/todos/1` 깨진 JSON | 400 | `invalid_json` |
| 17 | `PUT /api/todos/1` `{"title": "x"}` | 405 | `method_not_allowed`, `Allow: GET, PATCH, DELETE` |
| 18 | `DELETE /api/todos` | 405 | `method_not_allowed`, `Allow: GET, POST` |
| 19 | `POST /api/todos/1` `{"title": "x"}` | 405 | `method_not_allowed`, `Allow: GET, PATCH, DELETE` |
| 20 | `POST /health` `{}` | 405 | `method_not_allowed`, `Allow: GET` |
| 21 | 임의 method `PURGE /api/todos` | 405 | `method_not_allowed`, `Allow: GET, POST` |
| 22 | `GET /api/unknown` | 404 | `not_found` |
| 23 | 거부 후 `GET /api/todos/1` | 200 | 생성 직후 객체와 동일(12~16 거부로 변하지 않음) |
