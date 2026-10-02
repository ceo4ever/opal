# DONE: TODO CRUD 웹 앱 구현

## 결과

표준 라이브러리 TODO 웹 앱 skeleton에 요구서(REQUEST.md) 기능을 구현했다.

- `python -m todo_web.app --host 127.0.0.1 --port <PORT> --data <JSON_FILE>` 실행 계약은 그대로다.
- `GET /` 화면은 기존 요소(`todo-form`, 제목·설명 입력, `Create` 버튼, `todo-list`)를 유지한다. 서버가 현재 목록을 HTML 이스케이프해 렌더링하고, 인라인 스크립트가 생성 후 목록을 `textContent`로 다시 그린다. 실패하면 `#form-error`에 오류 메시지를 표시한다.
- JSON API: `GET /health`, `GET`·`POST /api/todos`, `GET`·`PATCH`·`DELETE /api/todos/{id}`. 응답 상태 코드는 201(`Location` 포함), 204(본문 없음), 404를 사용한다.
- 오류 처리:
  - 상태 코드: 400(`invalid_json`/`validation_error`), 415, 405(`Allow` 포함), 500(`storage_error`).
  - 오류 본문은 모두 `{"error", "message"}` 형식이다.
  - 검증 규칙: 제목은 공백 제거 후 1~120자, 설명은 2000자 이하다.
- 영속성:
  - `--data` 파일 형식은 `{"next_id", "todos"}`다. 삭제된 ID는 재사용하지 않는다.
  - 모든 쓰기는 하나의 lock으로 직렬화하고, tmp 파일을 fsync한 뒤 `os.replace`로 교체한다. 저장에 실패하면 메모리 상태는 바뀌지 않는다.
  - 손상된 데이터 파일은 덮어쓰지 않고 종료 코드 2로 기동을 거부한다.
- 기존 `make_handler(data_path)` 시그니처와 `tests/test_basic.py` 동작을 유지했다. 외부 패키지는 추가하지 않았다.

## 변경 파일

- `todo_web/app.py`
- `todo_web/store.py` (신규)
- `tests/test_todo_api.py` (신규)
- `tasks/001-261002-opds-TODO-CRUD-웹앱/` (TASK·PLAN·TEST-SCENARIO·AGENTIC-LOG·DONE·state 파일)

## 검증

- 설계 게이트 i1 pass: 독립 evaluator 판정으로 design 4축 PASS, scenario 2/2/2.
- RED-first: 구현 전 `python -m pytest -q tests/test_todo_api.py`에서 9건 모두 assertion 실패(S-1~S-8). `scenario-red` 8건을 기록하고 lock했다.
- `python -m pytest -q`: 11 passed. 기존 2건과 신규 9건이다.
- `test-scenario.json`: S-1~S-11 11/11 pass, `scenario-fidelity-check` all_met. 시나리오별로 확인한 내용은 다음과 같다.
  - S-6: 실제 프로세스 재기동 후에도 데이터가 유지됐다.
  - S-7: 20건 동시 POST에서 유실이 없었다.
  - S-11: Playwright 실브라우저에서 화면 생성과 오류 표시를 확인했다.
- 보안 검사: 하드코딩 시크릿 없음, `.gitignore`가 `data/`와 `*.json.tmp`를 포함, 출력 이스케이프 확인.
- 컨벤션 최종 진단: Critical 0, High 0, Low advisory 2.

## 회고적 학습 후보

없음

## 참고

- 컨벤션 Low advisory 2건(`todo_web/store.py`)은 미처리로 남겼다.
  - 메서드 안에서 `import copy`를 반복한다.
  - `from __future__ import annotations`를 쓰지 않는다.
- 프로젝트에 `docs/CONVENTIONS.md`가 없어 컨벤션 진단 결과가 `partial`이다.
- `.opal/code-scan.json`의 exclude에 `.opal-worktrees`가 빠져 있다. worktree-tool이 이 경고를 냈다.
