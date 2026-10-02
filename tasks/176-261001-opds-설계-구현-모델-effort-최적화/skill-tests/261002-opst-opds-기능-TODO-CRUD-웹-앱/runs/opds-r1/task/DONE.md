# DONE: TODO CRUD 웹 앱 구현

## 결과

`todo_web`가 skeleton에서 TODO CRUD 웹 앱이 되었다. `python -m todo_web.app --host 127.0.0.1 --port <PORT> --data <JSON_FILE>` 실행 계약을 유지한 채 다음이 동작한다.

- 화면 `GET /`: 제목·설명 입력, 생성 버튼, 목록(완료 토글·삭제)을 가진 HTML. 인라인 JS가 API를 호출하며 사용자 값은 `textContent`로만 삽입한다.
- API: `GET /health`, `GET/POST /api/todos`, `GET/PATCH/DELETE /api/todos/{id}` — 201+`Location`, 204 빈 본문, 404/405(+`Allow`)/415/400(`invalid_json`·`validation_error`)/500(`storage_error`). 모든 API·오류 응답은 JSON이며 오류는 `error`·`message` 필드를 가진다.
- 검증: 제목은 strip 후 1~120자(strip 값 저장), 설명 ≤2000자, `completed`는 bool, PATCH는 1개 이상 필드 필요.
- 영속성: `--data` 파일에 `{"next_id", "todos"}` 형식으로 잠금 + 임시 파일 fsync + `os.replace` 원자적 전체 기록. 재시작 후 유지, 동시 요청에서도 유실 없음, ID 재사용 없음. 손상된 데이터 파일이면 덮어쓰지 않고 exit 2로 기동을 거부한다.

유지한 것: `make_handler(data_path)` 시그니처와 기존 `tests/test_basic.py`의 언바운드 `do_GET(DummyHandler())` 호환(H-1), 표준 라이브러리 전용 런타임(외부 패키지 0).

## 변경 파일

- `todo_web/app.py` (수정)
- `todo_web/store.py` (신규)
- `tests/test_todo_api.py` (신규)

## 검증

- `python -m pytest -q` → 12 passed (기존 2 + 신규 S-1~S-10 10개). RED-first: 구현 전 10/10 실패 관찰 후 lock.
- `test-tool scenario-status` → 13/13 PASS, FAIL/BLOCKED 0 (S-8·S-10 실제 `python -m todo_web.app` 프로세스, S-12 실제 브라우저 E2E 생성·완료 토글·새로고침 유지·삭제).
- S-11 `git diff --exit-code main -- tests/test_basic.py` exit 0, S-13 비표준 import 0건·의존성 파일 변경 0건.
- 설계 게이트 i1 pass(설계 4축 PASS, 시나리오 2/2/2), 최종 컨벤션 `run/GC-CONVENTION-2026-10-02T02-25-00.md` Critical/High 0, 보안 grep(시크릿 없음·`innerHTML` 미사용·`.gitignore` 데이터 파일 포함) PASS.

## 회고적 학습 후보

없음

## 참고

- S-12 콘솔에 브라우저 자동 요청 `/favicon.ico`의 404 1건이 있다(계약대로 미정의 경로 404 JSON). 앱 스크립트 오류는 없다.
- 운영 서버 `ThreadingHTTPServer`의 기본 listen backlog(5)는 바꾸지 않았다. 테스트 S-9는 동시 20연결 재현을 위해 backlog 128 서브클래스를 쓴다. 대량 동시 접속 요구가 생기면 별도 태스크로 다룬다.
- `docs/CONVENTIONS.md`가 없어 컨벤션 검사가 인접 코드 기준(partial)으로 수행됐다.
