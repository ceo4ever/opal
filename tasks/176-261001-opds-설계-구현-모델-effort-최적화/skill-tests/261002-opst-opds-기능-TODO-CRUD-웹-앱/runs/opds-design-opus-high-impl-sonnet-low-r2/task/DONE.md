# DONE: TODO CRUD 웹 앱 구현

## 결과

`python -m todo_web.app --host 127.0.0.1 --port <PORT> --data <JSON_FILE>`로 띄운 서버가 다음을 제공한다.

- `GET /health` → `200 {"ok": true}`(기존 동작 유지).
- `GET /` → 기존 화면 구조(제목·설명 입력, Create 버튼, 목록 영역)에 목록 렌더·생성·오류 표시 스크립트를 더한 HTML. 화면은 `/api/todos` API를 사용하고 사용자 입력은 `textContent`로만 넣는다.
- `/api/todos` 컬렉션(GET 목록·POST 생성 201 + `Location`)과 `/api/todos/{id}` 개별 리소스(GET·PATCH 부분 수정·DELETE 204). 없는 ID와 알 수 없는 경로는 404.
- 검증·오류 규약: 잘못된 JSON 400 `invalid_json`, 검증 실패(공백 제목·120자 초과 제목·2000자 초과 설명·타입 위반) 400 `validation_error`, `application/json`이 아닌 쓰기 요청 415, 지원하지 않는 method 405 + `Allow` 헤더(501 대신). 모든 오류는 `error`·`message` 필드를 가진 JSON.
- 영속성: 새 모듈 `todo_web/store.py`가 `--data` 파일(`{"next_id", "todos"}`)을 lock 안에서 전체 문서 단위로 `<data>.tmp` → `fsync` → `os.replace` 원자 저장한다. 재시작 후 생성·수정·삭제 결과가 유지되고 삭제된 ID는 재사용되지 않는다. 손상된 데이터 파일이면 서버를 띄우지 않고 stderr 메시지와 함께 exit 1로 끝나 기존 파일을 덮어쓰지 않는다.
- 동시 접속에서 연결이 reset되지 않도록 `ThreadingHTTPServer`의 listen backlog를 128로 올렸다(PM 사후 승인한 PLAN 외 변경 — AGENTIC-LOG #8·#9).

유지한 것: CLI 인자, `make_handler`·`main` 공개 이름, `TodoHandler.data_path`, 기존 `tests/test_basic.py`(무수정 통과). 외부 패키지 없음(표준 라이브러리만).

## 변경 파일

- `todo_web/app.py` (수정)
- `todo_web/store.py` (신규)
- `tests/test_todo_api.py` (신규 — RED-first 계약 테스트 S-1~S-9)
- `tasks/001-261002-opds-TODO-CRUD-웹앱-구현/` (태스크 캡슐: TASK·PLAN·TEST-SCENARIO·AGENTIC-LOG·DONE·state·test-scenario.json·컨벤션 보고서)

## 검증

- RED: 구현 전 `python -m pytest -q tests/test_todo_api.py` → 9 failed, `test-tool scenario-red` S-1~S-9 기록 후 `scenario-lock`.
- GREEN·회귀(worktree 루트, 대상 SHA `ad66d5b`): `python -m pytest -q` → 11 passed(기존 2 + 신규 9), `python -m compileall -q todo_web tests` → exit 0.
- TEST(`opal-test-agent` 독립 실행): `test-tool scenario-status` → 14/14 pass(fail·blocked·executor_unavailable 0). S-7 실제 프로세스 2회 기동 재시작 영속성, S-9 손상 파일 exit 1·파일 바이트 불변, S-11 실제 브라우저(Playwright) 생성·새로고침 유지·오류 표시(real-usage), S-13 비표준 import 0건, S-14 변경 경로 한정. 증거: `run/test/`.
- 보안: 변경 파일 시크릿 패턴 스캔 0건, `.gitignore`의 `data/`·`*.json.tmp` 무시를 `git check-ignore`로 실측.
- 컨벤션: `opal-convention-checker` 최종 1회 — blocking 0, advisory 1(GC-001, 아래 참고). 보고서 `GC-CONVENTION-2026-10-02T02-17-23.md`.

## 회고적 학습 후보

없음

## 참고

- 컨벤션 진단 판정은 `docs/CONVENTIONS.md`가 없어 INCOMPLETE(`check_status: partial`)다. advisory GC-001(`tests/test_todo_api.py` `@header`의 `"exports": []`)은 기존 `tests/test_basic.py`와 같은 관례라 오탐으로 판단했다. 프로젝트 컨벤션 문서를 만들면 이후 진단이 PASS 판정을 낼 수 있다.
- `todo_web/app.py`의 `_send_json_list`는 `_send_json`과 같은 동작을 하는 중복 헬퍼다(기능 영향 없음, 미반영 — AGENTIC-LOG #11).
- 화면은 요구 범위(목록·생성)만 구현했다. 화면에서의 수정·삭제 UI는 없다(API로는 가능).
