---
template: sdlc-v2
---
# TASK: TODO CRUD 웹 앱 구현

## Problem
현재 `todo_web` 앱은 `GET /health`와 정적 HTML 화면만 제공하고, 쓰기 메서드(`POST`·`PATCH`·`DELETE`)는 모두 `404 not_found`를 반환한다(`todo_web/app.py:72-79`). 사용자는 할 일을 생성·조회·수정·삭제할 수 없고, `--data` JSON 파일에 아무것도 저장되지 않아 서버 재시작 후 데이터가 남지 않는다.

## Proposed outcome
`python -m todo_web.app --host 127.0.0.1 --port <PORT> --data <JSON_FILE>`로 띄운 서버에서 사용자가 브라우저 화면 또는 JSON API로 TODO를 생성·목록 조회·상세 조회·부분 수정·삭제할 수 있다. 잘못된 입력·형식·메서드·존재하지 않는 ID는 정해진 상태 코드와 `error` 필드가 있는 JSON으로 거부된다. 모든 변경은 `--data` JSON 파일에 저장되어 같은 파일로 재시작해도 유지되고, 한 항목을 변경해도 다른 항목은 유실·변형되지 않는다.

## Affected users and systems
- 사용자: 브라우저로 `GET /` 화면을 쓰는 사용자, JSON API 클라이언트.
- 시스템: `todo_web/` 패키지(HTTP 핸들러·저장소), `tests/` 회귀 테스트, `--data`로 지정한 JSON 파일.
- 포함 범위: 사용자 요구서(REQUEST.md)의 화면·API·검증과 예외·영속성 절 전체.
- 제외 범위: 인증·사용자 구분, 페이지네이션·검색, 외부 DB, 요구서에 없는 엔드포인트.

## Constraints
- C-1: 서버 실행 명령은 `python -m todo_web.app --host 127.0.0.1 --port <PORT> --data <JSON_FILE>` 형태를 그대로 지원한다.
- C-2: 런타임 구현은 Python 표준 라이브러리만 사용하며 외부 패키지를 추가하지 않는다(`.opal/AGENT.md` §제약).
- C-3: 기존 테스트(`tests/test_basic.py`)는 수정 없이 계속 통과한다.
- C-4: 요청된 TODO 애플리케이션 범위 밖의 동작은 변경하지 않는다(`.opal/AGENT.md` §제약).

## Acceptance criteria
- AC-1: `GET /`은 `200` HTML 화면을 반환하고, 화면에 할 일 목록 영역·제목 입력·설명 입력·생성 버튼이 있으며, 화면에서 생성한 TODO가 목록에 표시된다. `GET /health`는 `200`과 본문 `{"ok": true}`를 반환한다.
- AC-2: `POST /api/todos`에 `{"title","description"}`을 보내면 `201`, `id`·`title`·`description`·`completed`(기본 `false`)를 가진 TODO 객체, `Location: /api/todos/{id}` 헤더를 반환하고, `GET /api/todos`는 `200`과 이 필드를 가진 TODO 객체 배열을, `GET /api/todos/{id}`는 `200`과 해당 객체를 반환한다.
- AC-3: `PATCH /api/todos/{id}`는 `title`·`description`·`completed` 중 보낸 필드만 수정해 `200`과 수정된 객체를 반환하고 다른 TODO는 변하지 않는다. `DELETE /api/todos/{id}`는 `204`와 빈 본문을 반환하고, 이후 목록과 상세 조회에서 해당 TODO가 사라진다. 상세·수정·삭제에서 존재하지 않는 ID는 `404`다.
- AC-4: 앞뒤 공백 제거 후 빈 제목, 120자 초과 제목, 2000자 초과 설명, 그 밖의 필드 검증 실패는 `400`, 잘못된 JSON 본문은 `400`, `Content-Type`이 `application/json`이 아닌 `POST`·`PATCH`는 `415`, 경로가 지원하지 않는 method는 `405`를 반환하며, 모든 오류 응답은 최소 `error` 필드를 가진 JSON 객체다.
- AC-5: 생성·수정·삭제 결과는 `--data` JSON 파일에 저장되어, 서버를 종료하고 같은 파일로 다시 시작해도 그대로 유지되며, 저장 과정에서 다른 항목이 유실되지 않는다.
