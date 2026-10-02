---
template: sdlc-v2
---
# TEST-SCENARIO: TODO CRUD 웹 앱 구현

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: 워크트리 루트(`feat/OP-TASK-001`), 로컬 `python3`(3.14) + 기존 pytest. 외부 서비스 없음.
- 공통 데이터: integration 시나리오는 테스트마다 pytest `tmp_path` 아래 새 데이터 파일 경로와 OS가 배정한 빈 TCP 포트를 쓴다. 서버는 `sys.executable -m todo_web.app --host 127.0.0.1 --port <p> --data <file>`로 실제 subprocess 기동하고, `GET /health` 200까지 최대 10초 대기한 뒤 `http.client`로 요청하며, 종료 시 terminate·wait한다. 테스트 함수명은 `test_s<N>_...` 형식이고 시나리오 S-N과 1:1로 대응한다(`tests/test_todo_api.py`).
- 대역 사용과 한계: 사용하지 않음. 모든 API·영속성 검증은 실제 서버 프로세스와 실제 파일로 수행한다.
- 실행 조건: 자동 실행. S-10은 에이전트가 브라우저 자동화(Playwright)로 수행하며 사람 조치가 필요 없다.
- 병렬 그룹: 선언 없음(순차).

## Scenarios

| ID | 유형 | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|---|
| S-1 | integration | AC-1, AC-2 | 빈 데이터 파일 경로로 서버 기동 | `python3 -m pytest tests/test_todo_api.py -q -k test_s1_` — `GET /health`, `GET /` 요청 | `/health`: 200, `Content-Type` `application/json`, 본문 `{"ok": true}`. `/`: 200, `Content-Type` `text/html`, 본문에 `Todo Web`, `id="todo-form"`, `id="todo-list"`, `id="title"`, `id="description"`, `id="create-button"` 포함 | pytest + 실서버 subprocess + `http.client` | 구현 전 RED |
| S-2 | integration | AC-3 | 빈 저장소 | `-k test_s2_` — `POST /api/todos` `{"title": "  Buy milk  ", "description": "2L"}` (`Content-Type: application/json`) | 201. 본문 키가 정확히 `id`,`title`,`description`,`completed`; `id`는 정수, `title`은 `"Buy milk"`(앞뒤 공백 제거), `description` `"2L"`, `completed` `false`. `Location` 헤더 = `/api/todos/{id}`. `description` 없이 `{"title": "x"}`도 201이고 `description`은 `""` | pytest + 실서버 | 구현 전 RED |
| S-3 | integration | AC-4 | TODO 2건 생성 | `-k test_s3_` — `GET /api/todos`, `GET /api/todos/{id}`, `GET /api/todos/999999`, `GET /api/todos/abc` | 목록: 200, JSON 배열 길이 2, id 오름차순, 각 원소가 4필드. 상세: 200, 생성 응답과 같은 객체. 없는 ID·비정수 ID: 404, JSON 객체에 `error` 필드 | pytest + 실서버 | 구현 전 RED |
| S-4 | integration | AC-5 | TODO A·B 생성 | `-k test_s4_` — `PATCH /api/todos/{A}` `{"completed": true}`, 이어서 `{"title": "A2"}`, 이후 `GET` A·B, `PATCH /api/todos/999999` `{"completed": true}` | 첫 PATCH 200, `completed` `true`, 나머지 필드 불변. 둘째 PATCH 200, `title` `"A2"`, `completed` `true` 유지. B는 생성 직후 객체와 완전히 동일. 없는 ID: 404 + `error` | pytest + 실서버 | 구현 전 RED |
| S-5 | integration | AC-6 | TODO A·B 생성 | `-k test_s5_` — `DELETE /api/todos/{A}`, `GET /api/todos/{A}`, `GET /api/todos`, `DELETE /api/todos/{A}` 재요청, 이후 새 TODO 생성 | 첫 DELETE 204, 본문 0바이트. 상세 404. 목록에 A 없음·B 있음. 재삭제 404 + `error`. 새 TODO의 `id`는 A의 id와 다름 | pytest + 실서버 | 구현 전 RED |
| S-6 | integration | AC-7 | TODO 1건 생성 | `-k test_s6_` — POST 본문 `{"title": "   "}`, `{"title": "a"*121}`, `{"title": "t", "description": "d"*2001}`, `{"description": "x"}`, `{"title": 1}`, 잘못된 JSON `{bad`, JSON 배열 `[]`; PATCH 본문 `{}`, `{"completed": "yes"}`, `{"title": ""}`; 경계 POST `{"title": "a"*120, "description": "d"*2000}` | 거부 요청 전부 400, `Content-Type` JSON, 본문 객체에 `error` 필드. 거부 PATCH 뒤 대상 TODO는 GET 결과가 변하지 않음. 경계 POST는 201 | pytest + 실서버 | 구현 전 RED |
| S-7 | integration | AC-7, H-2 | 서버 기동, TODO 1건 생성 | `-k test_s7_` — `POST /api/todos` `Content-Type: text/plain`(유효 JSON 본문), `Content-Type` 헤더 없는 POST, `PATCH /api/todos/{id}` `Content-Type: text/plain`; `POST /api/todos` `Content-Type: application/json; charset=utf-8`; `PUT /api/todos`, `DELETE /api/todos`, `POST /health`, `PUT /api/todos/{id}`, 임의 method `FOO /api/todos`; `GET /nope` | 415 3건(+`error`), charset 파라미터 포함 POST는 201. 405 5건, 각각 JSON `error` 필드와 `Allow` 헤더. `GET /nope` 404 + `error` | pytest + 실서버 | 구현 전 RED |
| S-8 | integration | AC-8 | 빈 데이터 파일 | `-k test_s8_` — TODO 5건 생성 → 2번 PATCH(`completed` true, `title` 변경) → 4번 DELETE → 서버 종료 → 같은 `--data`로 재기동 → `GET /api/todos` → 새 TODO 생성 | 재기동 후 목록이 종료 전 목록과 정확히 같음(4건, 수정 반영, 삭제 항목 없음). 데이터 파일은 유효 JSON. 재기동 후 새 TODO의 `id`는 기존 모든 id보다 큼 | pytest + 실서버 2회 기동 | 구현 전 RED |
| S-9 | integration | AC-8 | (a) 0바이트 데이터 파일 미리 생성 (b) 내용이 `{not json`인 데이터 파일 | `-k test_s9_` — 각 파일로 서버 기동 | (a) 기동 성공, `GET /api/todos` 200 `[]`, 이후 POST 201. (b) 프로세스가 10초 안에 종료 코드 1로 끝나고 stderr에 `error:` 포함, 파일 내용은 기동 전과 바이트 동일 | pytest + 실서버 subprocess | 구현 전 RED |
| S-10 | e2e | AC-2 | 구현 후 `python3 -m todo_web.app --host 127.0.0.1 --port 8765 --data <tmp>/e2e.json` 기동 | 브라우저로 `http://127.0.0.1:8765/` 열기 → 목록 영역·제목 입력·설명 입력·Create 버튼 확인 → 제목 `E2E item`, 설명 `from browser` 입력 → Create 클릭 → 새로고침 | 클릭 후 `#todo-list` 안에 `E2E item`과 `from browser`가 표시되고 입력란이 비워짐. 새로고침 후에도 항목 표시. 콘솔 오류 없음. `GET /api/todos`에 같은 항목 존재 | Playwright 브라우저 자동화(에이전트 실행), surface `web_ui`, profile `browser` | 구현 후 |
| S-11 | regression | C-2, H-1 | 구현 완료 | `python3 -m pytest tests/test_basic.py -q` | `2 passed`, 실패·오류 0 (unbound `do_GET` 호출 계약 유지) | pytest | 구현 후 |
| S-12 | check | C-1, C-3 | 구현 완료 | (1) `todo_web/*.py`의 모든 import를 AST로 추출해 `sys.stdlib_module_names` 또는 `todo_web` 패키지에 속하는지 검사 (2) `git diff --name-only main...HEAD` 및 작업트리 변경 목록 확인 | (1) 표준 라이브러리 외 import 0건 (2) 변경 파일이 `todo_web/app.py`, `todo_web/store.py`, `tests/test_todo_api.py`와 태스크 폴더(`tasks/001-261002-opds-할일-CRUD-웹앱/`)로 한정 | 셸 + python AST 스크립트 | 구현 후 |
