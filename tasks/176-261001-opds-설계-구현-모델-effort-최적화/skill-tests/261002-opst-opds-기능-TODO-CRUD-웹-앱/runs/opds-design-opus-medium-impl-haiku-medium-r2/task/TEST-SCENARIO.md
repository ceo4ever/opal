---
template: sdlc-v2
---
# TEST-SCENARIO: TODO CRUD 웹 앱 구현

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: worktree 루트(`feat/OP-TASK-001`)에서 Python 3 + pytest. 서버는 매 시나리오마다 빈 포트와 pytest `tmp_path` 아래 새 `--data` 파일로 `python -m todo_web.app --host 127.0.0.1 --port <PORT> --data <JSON_FILE>`을 실제 프로세스로 띄우고, `GET /health` 200을 확인한 뒤 요청한다(PLAN D-12). 시나리오 종료 시 프로세스를 종료한다.
- 공통 데이터: 없음. 각 시나리오는 빈 `--data` 파일(미존재 경로)에서 시작한다.
- 대역 사용과 한계: 사용하지 않음. S-2~S-6은 실제 서버 프로세스와 실제 파일 시스템을 쓰며, S-7은 실제 브라우저로 실제 서버에 접속한다.
- 실행 조건: 자동 실행. 사람 협업 없음. S-7은 브라우저 자동화 capability(Playwright)가 필요하다.
- 병렬 그룹: S-2, S-3, S-4, S-5, S-6, S-9 (각자 별도 포트·별도 `--data` 파일 사용)

## Scenarios

| ID | 유형 | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|---|
| S-1 | integration | AC-1, C-1, C-4 | 빈 `--data` 경로로 서버 기동 | `GET /health`, `GET /` | `/health`: `200`, 본문 JSON이 정확히 `{"ok": true}`. `/`: `200`, `Content-Type`이 `text/html`로 시작, 본문에 `id="todo-form"`, `name="title"` 입력, `name="description"` textarea, `type="submit"` 버튼, `id="todo-list"` 영역이 모두 존재. 기동 직후 `--data` 파일은 생성되지 않음(읽기 전용 시작, PLAN D-5) | pytest + subprocess 실서버 + `urllib.request` | 구현 후 |
| S-2 | integration | AC-2, C-1 | 빈 저장소 서버 | `POST /api/todos` `{"title":"  Buy milk  ","description":"2L"}` (`Content-Type: application/json`) → `GET /api/todos` → `GET /api/todos/{id}` | POST: `201`, 본문 키 집합이 정확히 `{id,title,description,completed}`, `title`=`"Buy milk"`(strip), `description`=`"2L"`, `completed`=`false`, `id`는 정수, `Location` 헤더=`/api/todos/{id}`. 목록: `200`, JSON 배열 길이 1, 원소가 POST 응답과 동일. 상세: `200`, POST 응답과 동일. `description` 생략 POST는 `description`=`""`로 `201` | pytest + subprocess 실서버 + `urllib.request` | 구현 전 RED |
| S-3 | integration | AC-3 | TODO A(`title`=a, `description`=da), B(`title`=b, `description`=db) 생성 | ① `PATCH A {"title":"a2"}` ② `PATCH A {"completed":true}` ③ `DELETE A` ④ `GET A`, `GET /api/todos` ⑤ `GET`·`PATCH {"title":"x"}`·`DELETE` on `/api/todos/9999` 및 `/api/todos/abc` | ①: `200`, `title`=`a2`, `description`=`da`, `completed`=`false`. ②: `200`, `title`=`a2`, `completed`=`true`. 이때 `GET B`는 생성 시와 완전히 동일. ③: `204`, 응답 본문 0바이트. ④: `GET A` `404` + JSON `error` 필드, 목록에 A 없음·B 그대로. ⑤: 6건 모두 `404` + JSON 객체에 `error` 필드 | pytest + subprocess 실서버 + `urllib.request` | 구현 전 RED |
| S-4 | integration | AC-4 | 빈 저장소 서버(필요 시 TODO 1건 생성) | POST `/api/todos`: `title` `"   "`, `title` 121자, `title` 누락, `title` 숫자 `5`, `description` 2001자, 본문 `{bad json`, 본문 `[1,2]`, `Content-Type: text/plain` 유효 JSON 본문, `Content-Type` 없음. PATCH 기존 ID: `{}`, `{"completed":"yes"}`, `{"title":""}`, `Content-Type: text/plain`. 경계 성공: `title` 120자 + `description` 2000자 POST, `Content-Type: application/json; charset=utf-8` POST. 메서드: `PUT /api/todos`, `DELETE /api/todos`, `POST /api/todos/{id}`, `PUT /api/todos/{id}`, `POST /health`, `GET /no-such-path` | 공백·121자·누락·숫자 제목, 2001자 설명, `{"completed":"yes"}`, `{}`, `{"title":""}`, `[1,2]` → 모두 `400`. `{bad json` → `400`. POST `text/plain`·`Content-Type` 없음, PATCH `text/plain` → `415`. 120자/2000자 및 `charset=utf-8` POST → `201`. `PUT`·`DELETE /api/todos`, `POST`·`PUT /api/todos/{id}`, `POST /health` → `405` + `Allow` 헤더 존재. `GET /no-such-path` → `404`. 모든 4xx 응답 본문은 `json.loads` 가능한 객체이고 `error` 키를 가짐. 실패 요청 후 `GET /api/todos` 결과는 성공 요청분만 포함 | pytest + subprocess 실서버 + `urllib.request` | 구현 전 RED |
| S-5 | integration | AC-5, C-1 | 빈 `--data` 경로로 서버 기동 | TODO 3건(t1,t2,t3) 생성 → `PATCH t2 {"completed":true,"description":"changed"}` → `DELETE t3` → 목록 L1 기록 → 서버 프로세스 종료 → 같은 `--data`로 재기동 → `GET /api/todos` → 새 TODO t4 생성 | 재기동 후 목록이 L1과 동일(t1 원본, t2 수정본, t3 없음). `--data` 파일은 `json.loads` 가능. t4의 `id`는 t1~t3의 어떤 `id`와도 다름(삭제 ID 재사용 없음) | pytest + subprocess 실서버 2회 기동 | 구현 전 RED |
| S-6 | integration | AC-5, H-1 | 빈 `--data` 경로로 서버 기동 | 스레드 20개로 서로 다른 제목의 `POST /api/todos` 동시 전송 → 생성된 TODO 중 5건 동시 `PATCH {"completed":true}` + 다른 5건 동시 `DELETE` → 서버 종료 → 같은 `--data`로 재기동 → `GET /api/todos` | POST 20건 모두 `201`, `id` 20개 모두 고유. PATCH 5건 `200`, DELETE 5건 `204`. 재기동 후 목록 길이 15, 남은 제목 집합이 기대 집합과 일치, PATCH 대상 5건만 `completed`=`true`. `--data` 파일은 `json.loads` 가능 | pytest + subprocess 실서버 + `threading`/`concurrent.futures` | 구현 전 RED |
| S-7 | e2e | AC-1 | 빈 `--data` 경로로 실서버 기동 | 브라우저로 `http://127.0.0.1:<PORT>/` 열기 → 제목 `E2E item`, 설명 `from browser` 입력 → Create 버튼 클릭 → 페이지 새로고침 없이 대기 → 이후 페이지 새로고침 | 클릭 후 `#todo-list` 안에 `E2E item` 텍스트가 나타남. `GET /api/todos`에 해당 TODO(`completed`=`false`)가 존재. 새로고침 후에도 `#todo-list`에 `E2E item` 표시. 브라우저 콘솔 에러 없음. surface_kind `web_ui`, profile `browser`, actors `agent`, steps executor `browser`, required_evidence: 클릭 후 목록 스냅샷, `/api/todos` 응답 | Playwright 브라우저 자동화 + 실서버 | 구현 후 |
| S-8 | regression | C-3, C-4 | 구현 완료 worktree | `python -m pytest tests/test_basic.py -q` 실행, `git diff --exit-code main -- tests/test_basic.py` 실행 | pytest 2 passed, exit 0. git diff exit 0(파일 무변경) | pytest + git | 구현 후 |
| S-9 | check | C-2 | 구현 완료 worktree | `todo_web/*.py`의 모든 `import`/`from` 최상위 모듈이 `sys.stdlib_module_names` 또는 `todo_web`인지 AST로 검사, 저장소 루트에 `requirements*.txt`·`pyproject.toml`·`setup.py`·`setup.cfg`·`Pipfile` 신규 추가가 없는지 `git diff --name-status main` 확인 | 비표준 import 0건, 의존성 선언 파일 추가 0건 | Python `ast` 스크립트 + git | 구현 후 |
