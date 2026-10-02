# DONE: TODO CRUD 웹 앱 구현

## 결과

`python -m todo_web.app --host 127.0.0.1 --port <PORT> --data <JSON_FILE>`로 띄운 서버가 요구서의 화면·API·검증·영속성을 모두 제공한다.

- API: `GET /health`, `GET/POST /api/todos`, `GET/PATCH/DELETE /api/todos/{id}`가 JSON으로 응답한다. 상태 코드는 201+`Location`, 204 무본문, 없는 ID 404를 따른다. 쓰기 요청 오류는 `application/json`이 아니면 415, 잘못된 JSON이나 검증 실패(공백 제목, 제목 120자 초과, 설명 2000자 초과, 타입 불일치)면 400이다. 지원하지 않는 method는 경로와 무관하게 405이고 `Allow` 헤더를 준다. 모든 오류 본문은 `{"error", "message"}` 형태다.
- 영속성: `--data` 파일(`{"next_id", "todos"}`)을 단일 잠금 아래 임시 파일 + `fsync` + `os.replace`로 원자 교체한다. 재시작해도 생성·수정·삭제가 유지되고, 동시 생성 20건도 유실되지 않는다. 파일이 손상돼 있으면 서버가 기동을 거부하고 파일을 덮어쓰지 않는다.
- 화면: `GET /`에 목록 영역·제목 입력·설명 입력·생성 버튼이 있다. 인라인 스크립트가 API로 목록 표시·생성·완료 토글·삭제를 수행하며, 목록이 비면 "No todos yet." 안내를 보여 준다. 사용자 입력은 `textContent`로만 렌더링한다.
- 유지된 것: 실행 인자와 기본값, `ThreadingHTTPServer` 기반(동시 접속을 위해 listen backlog를 128로 올린 하위 클래스 사용), 기존 `tests/test_basic.py` 계약(`DummyHandler`로 `GET /health`·`GET /` 호출), 표준 라이브러리만 사용.

## 변경 파일

- `todo_web/store.py` (신규)
- `todo_web/app.py`
- `tests/test_todo_api.py` (신규)

## 검증

- `python -m pytest tests/ -q` 결과 9 passed(SHA `37aa532`, 최종 회귀).
- `test-scenario.json` 기록: S-1~S-11 11/11 pass, RED 7/7 확인(S-2~S-8은 구현 전 실패를 기록한 뒤 잠금).
- S-8 동시성·재시작 시나리오를 10회 반복해 10/10 통과했다.
- S-9는 Playwright headless Chromium으로 실제 브라우저에서 검증했다. 생성, 목록 표시, 새로고침 후 유지, API 존재를 모두 확인했다.
- 보안: 변경 파일의 시크릿 0건, 위험 API 0건, `innerHTML` 미사용. XSS 입력은 텍스트로 렌더링됐다.
- TEST 수정 반복은 2회였다. ① S-9: 빈 목록 영역의 높이가 0이라 보이지 않던 문제를 빈 상태 안내로 고쳤다. ② S-8: listen backlog 5 때문에 생기던 동시 접속 reset을 backlog 128로 고쳤다.

## 회고적 학습 후보

없음

## 참고

- 기본 데이터 경로 `data/`와 임시 파일 `*.json.tmp`는 기존 `.gitignore`가 커버한다.
