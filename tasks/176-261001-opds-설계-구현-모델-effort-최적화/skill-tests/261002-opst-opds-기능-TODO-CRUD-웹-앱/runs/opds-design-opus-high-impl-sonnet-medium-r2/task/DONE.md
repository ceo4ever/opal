# DONE: TODO CRUD 웹 앱

## 결과

`python -m todo_web.app --host 127.0.0.1 --port <PORT> --data <JSON_FILE>`로 띄운 표준 라이브러리 서버가 요구서의 TODO CRUD 웹 앱을 제공한다.

- 화면: `GET /`는 할 일 목록 영역(빈 목록이면 "No todos yet." 표시)·제목 입력·설명 입력·생성 버튼이 있는 HTML을 반환한다. 인라인 JS가 API로 목록 표시·생성·완료 토글·삭제를 수행하며, 항목 텍스트는 `textContent`로만 넣는다.
- API: `GET /health`, `GET·POST /api/todos`, `GET·PATCH·DELETE /api/todos/{id}`. 생성은 `201`+`Location`, 삭제는 `204` 빈 본문, 없는 ID는 `404`.
- 검증·오류: 제목은 앞뒤 공백 제거 후 1~120자(공백 제거본 저장), 설명은 최대 2000자. 검증 실패·잘못된 JSON(깊은 중첩 포함)은 `400`, `application/json`이 아닌 쓰기는 `415`, 허용되지 않은 method(PUT·HEAD·OPTIONS·임의 method 포함)는 `405`+`Allow`. 모든 오류는 `{"error","message"}` JSON이다.
- 영속성: `--data` 파일에 `{"next_id","todos"}`로 저장한다. 단일 lock 아래에서 복사본 변경 → 임시 파일 fsync → `os.replace` 순서로 원자 교체해, 동시 요청과 재시작에도 항목이 유실되지 않는다. 삭제된 ID는 재사용하지 않는다.
- 유지한 것: `make_handler`/`main` 공개 시그니처와 CLI 인자, 기존 `tests/test_basic.py`(무수정 통과), 외부 패키지 0건.
- 요구서가 정하지 않은 외부 동작(정수 id·재사용 금지, description·completed 선택 입력, 빈 PATCH 400, 오류 코드 6종과 판정 순서, 405 `Allow`, 깨진 데이터 파일은 덮어쓰지 않고 기동 중단)은 PLAN.md D-1~D-12로 확정했다.

## 변경 파일

- `todo_web/app.py`
- `todo_web/store.py`
- `tests/test_todo_api.py`
- `tasks/001-261002-opds-TODO-CRUD-웹앱/` (TASK·PLAN·TEST-SCENARIO·AGENTIC-LOG·DONE·상태·검증 증거)

## 검증

- 설계 게이트 i1: evaluator design 4축 PASS, scenario goal·adoption·boundary 2/2/2 → pass.
- RED: S-2~S-7 통합 테스트가 구현 전 실패(`POST /api/todos` 404)를 관찰·기록한 뒤 `scenario-lock`.
- 최종 TEST(SHA `faf3417`, opal-test-agent): S-1~S-10 전부 PASS — `scenario-status` passed 10 / fail 0, `scenario-fidelity-check` all_met 10/10. S-10은 headless Chromium으로 실제 화면에서 생성·완료·삭제·새로고침과 HTML 이스케이프를 확인했다.
- 전체 회귀: `python -m pytest -q -p no:cacheprovider` → 8 passed. `tests/test_todo_api.py` 15회 반복 실행 시 실패 0.
- 보안(op-gc-security, 02-26-00): Critical/High 0, Low 2·Info 3(advisory/informational), 시크릿 0.
- 컨벤션(op-gc-convention, 02-26-00): Critical 0 / High 1 advisory. `tests/test_todo_api.py` @header의 빈 `exports`를 지적한 것으로, 기존 `tests/test_basic.py`와 같은 패턴인 오탐이다. blocking 0.
- TEST 수정 반복: 1회(fix 1/3). 자동 실행 시간 합계 약 192초, 사람 대기 없음.

## 회고적 학습 후보

없음

## 참고

- 범위 밖 개선 후보(보안 Low): 요청 본문 크기 상한(413)과 소켓 timeout(GC-001). 잘못된 Content-Type의 2MB 본문은 클라이언트가 415 대신 Broken pipe를 받는다. Host/Origin 검증(GC-003, DNS rebinding).
- 범위 밖 개선 후보(Info): 보안 응답 헤더, 데이터 파일 권한·고정 임시 파일명, `.gitignore`의 `.env`·키 패턴.
- `docs/CONVENTIONS.md`·`docs/SECURITY.md`가 없어 컨벤션·보안 판정이 내장 기준(advisory)으로만 수행됐다.
- `worktree-tool create` 경고: `.opal/code-scan.json` exclude에 `.opal-worktrees` 없음, uv 캐시가 다른 볼륨에 있음.
