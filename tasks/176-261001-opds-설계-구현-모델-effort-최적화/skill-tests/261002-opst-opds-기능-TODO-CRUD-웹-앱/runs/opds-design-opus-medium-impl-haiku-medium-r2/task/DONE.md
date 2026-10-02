# DONE: TODO CRUD 웹 앱 구현

## 결과

`python -m todo_web.app --host 127.0.0.1 --port <PORT> --data <JSON_FILE>`로 실행한 서버에서 TODO 생성·목록·상세·부분 수정·삭제가 JSON API(`/api/todos`, `/api/todos/{id}`)와 브라우저 화면(`GET /`)으로 동작한다.
- 검증·예외: 앞뒤 공백 제거 후 빈 제목, 120자 초과 제목, 2000자 초과 설명, 잘못된 필드 타입, 잘못된 JSON은 `400`, `application/json`이 아닌 쓰기는 `415`, 지원하지 않는 메서드는 `405`(+`Allow`), 없는 ID·경로는 `404`. 모든 오류 응답에는 `error` 필드가 있다.
- 영속성: `{"next_id","todos"}` JSON 파일에 단일 lock과 임시 파일 `os.replace`로 원자적으로 저장한다. 같은 파일로 재시작해도 상태가 유지되고, 삭제된 ID는 재사용하지 않는다. 손상된 파일은 덮어쓰지 않고 시작 시 실패한다. 서버 listen backlog를 128로 올려 20건 동시 쓰기에서도 유실이 없다.
- 유지한 것: `GET /health` 응답, 기존 폼·목록 마크업, `make_handler`·`main` 시그니처와 CLI, 기존 `tests/test_basic.py`(무변경 통과), 표준 라이브러리만 사용.
- 범위 경계: 화면은 목록 표시와 생성만 제공하고 수정·삭제 UI는 넣지 않았다. favicon 엔드포인트는 추가하지 않고 `data:` 아이콘으로 브라우저 요청을 없앴다.

## 변경 파일

- `todo_web/app.py`
- `todo_web/store.py`
- `tests/test_todo_api.py`

## 검증

- `python -m pytest -q` → 7 passed, exit 0 (최종 회귀, `run/test/final-regression-r2.out`)
- `test-scenario.json` S-1~S-9 9/9 pass (S-2~S-6은 구현 전 RED 확인 5/5, S-7은 Playwright 실브라우저 real-usage, S-6은 연속 7회 pass)
- 보안 검사 pass: 하드코딩 시크릿 0, `data/` gitignore, 사용자 입력은 `textContent`로 삽입 (`run/test/security-r2.out`)
- 컨벤션 checker: `docs/CONVENTIONS.md`가 없어 생략

## 회고적 학습 후보

없음

## 참고

- worktree 브랜치 `feat/OP-TASK-001`은 merge 대기 상태다. 체크포인트 커밋: `0ac4272`(명세), `2cae931`(구현), `bef3379`(TEST fix).
