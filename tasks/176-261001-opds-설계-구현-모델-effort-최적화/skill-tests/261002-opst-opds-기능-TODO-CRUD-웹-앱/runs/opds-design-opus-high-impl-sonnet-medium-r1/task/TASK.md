---
template: sdlc-v2
---
# TASK: TODO CRUD 웹 앱 구현

## Problem
현재 저장소의 TODO 웹 앱은 Python 표준 라이브러리 기반 skeleton으로, `/health`와 정적 HTML 화면만 응답하고 쓰기 method는 모두 `404`를 반환한다(`todo_web/app.py:47-89`). 사용자는 할 일을 만들거나 조회·수정·삭제할 수 없고, `--data` 인자로 받은 JSON 파일에도 아무것도 저장되지 않는다(`todo_web/app.py:92-98`). 세션 입력 요구서(`REQUEST.md`, 허브 저장소의 상위 scratchpad 디렉토리 — 이하 "요구서")가 정의한 API·화면·검증·영속성 계약을 충족하지 못한다.

## Proposed outcome
`python -m todo_web.app --host 127.0.0.1 --port <PORT> --data <JSON_FILE>`로 띄운 서버에서 사용자는 브라우저 화면으로 할 일 목록을 보고 제목·설명을 입력해 할 일을 만들 수 있다. JSON API로 할 일을 생성·목록 조회·상세 조회·부분 수정·삭제할 수 있고, 잘못된 요청은 요구서가 정한 상태 코드와 `error` 필드를 가진 JSON으로 거부된다. 생성·수정·삭제 결과는 `--data` JSON 파일에 저장되어 서버를 같은 파일로 재시작해도 그대로 유지되며, 한 항목을 저장할 때 다른 항목이 유실되지 않는다.

## Affected users and systems
- 사용자: 브라우저 화면 사용자, JSON API 호출자.
- 시스템: `todo_web/` 웹 앱 패키지와 `tests/` 회귀 테스트(`docs/PROJECT.md` §프로젝트 구조).
- 포함: 요구서의 실행 계약·화면·API 6종·검증과 예외·영속성.
- 제외: 인증·권한, 다중 사용자 분리, 페이지네이션·검색·정렬, 외부 DB, 배포.

## Constraints
- C-1: 런타임 구현은 Python 표준 라이브러리만 사용하고 외부 패키지를 추가하지 않는다(`.opal/AGENT.md` §제약, 요구서 §실행 계약).
- C-2: 기존 테스트(`tests/`)는 계속 통과해야 한다(요구서 §실행 계약, `.opal/AGENT.md` §필수 검토).
- C-3: 요청된 TODO 애플리케이션 범위 밖의 동작은 변경하지 않는다(`.opal/AGENT.md` §제약).

## Acceptance criteria
- AC-1: `python -m todo_web.app --host 127.0.0.1 --port <PORT> --data <JSON_FILE>`로 서버가 기동되고, `GET /health`가 `200`과 본문 `{"ok": true}`를 반환한다.
- AC-2: `GET /`이 브라우저에서 접근 가능한 HTML 화면을 반환하며, 화면에 할 일 목록 영역·제목 입력·설명 입력·생성 버튼이 있고 이 화면에서 할 일을 생성하면 목록에 나타난다.
- AC-3: `Content-Type: application/json`인 `POST /api/todos` 요청(`{"title": "...", "description": "..."}`)이 성공하면 `201`, 생성된 TODO 객체(`id`, `title`, `description`, `completed` 필드, `completed` 기본값 `false`), `Location: /api/todos/{id}` 헤더를 반환한다.
- AC-4: `GET /api/todos`는 `200`과 TODO 객체 배열을 반환하고, `GET /api/todos/{id}`는 존재하면 `200`과 해당 TODO 객체를, 없는 ID면 `404`를 반환한다.
- AC-5: `PATCH /api/todos/{id}`는 `title`·`description`·`completed` 중 하나 이상을 담은 요청을 반영해 `200`과 수정된 TODO 객체를 반환하고, 다른 TODO 항목은 변하지 않으며, 없는 ID면 `404`를 반환한다.
- AC-6: `DELETE /api/todos/{id}`는 성공 시 `204`와 빈 본문을 반환하고 이후 목록과 상세 조회에서 해당 항목이 사라지며, 없는 ID면 `404`를 반환한다.
- AC-7: 제목은 앞뒤 공백 제거 뒤 비어 있으면 안 되고 최대 120자, 설명은 최대 2000자이며, 검증 실패와 잘못된 JSON 본문은 `400`, `application/json`이 아닌 `Content-Type`의 쓰기 요청(`POST`, `PATCH`)은 `415`, 지원하지 않는 method는 `405`를 반환한다. 모든 오류 응답은 최소한 `error` 필드를 가진 JSON 객체다.
- AC-8: TODO 데이터는 `--data`로 받은 JSON 파일에 저장되어, 서버를 종료하고 같은 `--data` 파일로 다시 시작해도 생성·수정·삭제 결과가 유지되고, 저장 중 다른 항목이 유실되지 않는다.
