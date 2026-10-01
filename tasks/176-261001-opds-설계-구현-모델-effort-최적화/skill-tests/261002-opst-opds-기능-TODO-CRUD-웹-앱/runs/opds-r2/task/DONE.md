# DONE: TODO CRUD 웹 앱 구현

## 결과

`python -m todo_web.app --host 127.0.0.1 --port <PORT> --data <JSON_FILE>`로 띄운 서버가 요구서(REQUEST.md)의 TODO CRUD 웹 앱으로 동작한다.

- API: `GET /health`, `GET·POST /api/todos`, `GET·PATCH·DELETE /api/todos/{id}`. POST는 201·`Location`, DELETE는 204 무본문, 없는 ID는 404.
- 검증·오류: 제목 strip 후 비어 있으면 400, 제목 120자·설명 2000자 초과 400, 잘못된 JSON 400, `application/json`이 아닌 쓰기 415, 지원하지 않는 method(임의 method 포함) 405 + `Allow`. 모든 오류는 `{"error", "message"}` JSON.
- 화면: `GET /`가 목록·제목 입력·설명 입력·Create 버튼이 있는 HTML을 반환하고, 인라인 JS가 API로 목록을 그리고 생성한다(사용자 데이터는 `textContent`로만 삽입, 외부 리소스 없음).
- 영속성: `--data` 파일에 `{"next_id", "todos"}`를 매 변경마다 임시 파일 + fsync + `os.replace`로 원자 저장하고, 하나의 Lock으로 직렬화한다. 재시작 후 결과가 유지되고 삭제된 ID는 재사용하지 않는다. 빈 파일·JSON 배열은 받아들이고, 손상된 파일이면 파일을 건드리지 않고 `error:`와 종료 코드 1로 기동을 거부한다.
- 유지: 실행 인자, `make_handler`·`main` 공개 시그니처, 기존 `tests/test_basic.py`의 unbound `do_GET` 호출 계약. 런타임은 표준 라이브러리만 사용한다.

## 변경 파일

- `todo_web/store.py` (신규)
- `todo_web/app.py`
- `tests/test_todo_api.py` (신규)
- `tasks/001-261002-opds-할일-CRUD-웹앱/` (태스크 산출물)

## 검증

- `python3 -m pytest -q` → 11 passed (기존 2 + 신규 9, 마지막 수정 기준 독립 실행)
- `tests/test_todo_api.py` 9건은 구현 전 skeleton에서 9 failed를 관찰·기록(RED) 후 잠금
- `test-tool scenario-status` → locked, 12/12 pass (S-1~S-9·S-11·S-12 real-http, S-10 Playwright 브라우저 real-usage: 생성·새로고침 유지·콘솔 오류 0)
- `python3 -m py_compile todo_web/*.py tests/*.py` → ok, AST import 검사 → 표준 라이브러리 외 0건
- 보안: 변경 파일 시크릿 패턴 0건, `.gitignore`가 `data/`·`*.json.tmp` 포함, `innerHTML` 미사용
- 컨벤션: `GC-CONVENTION-2026-10-02T02-11-00.md` Critical/High 0 (기준 문서 부재로 check_enabled=false, Low 3·Info 1 advisory)
- 설계 게이트 i1 pass (설계 4축 PASS, 시나리오 평균 2.0)

## 회고적 학습 후보

없음

## 참고

- 미적용 advisory(컨벤션 Low): `_route`의 긴 if/elif, `TodoStore.list` 메서드명이 builtin을 가림, 미사용 `TodoHandler.data_path`·테스트 지역변수. 동작과 무관해 이번 범위에서 제외.
- `test-tool scenario-mark`가 비-pass 판정의 `observed_executors`를 검증 없이 저장해 `test-scenario.json`이 로드 불가가 된 결함이 있었다. S-10 결과 필드만 PM이 마크 전 상태로 복구(원본 사본 `run/test-scenario.before-s10-repair.json`)한 뒤 도구 경로로 다시 기록했다. FW 개선 후보로 기록.
