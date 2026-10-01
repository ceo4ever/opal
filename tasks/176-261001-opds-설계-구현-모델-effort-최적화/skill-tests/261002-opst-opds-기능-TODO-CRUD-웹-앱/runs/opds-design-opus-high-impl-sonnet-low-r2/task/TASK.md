---
template: sdlc-v2
---
# TASK: TODO CRUD 웹 앱 구현

## Problem
현재 저장소의 TODO 웹 앱은 health 확인과 정적 HTML 화면만 제공하는 skeleton이다. `POST`·`PATCH`·`DELETE`와 `/api/todos` 경로는 모두 `404 not_found`를 반환하고(`todo_web/app.py:44-81`), `--data`로 받은 JSON 파일 경로는 handler에 보관만 될 뿐 읽거나 쓰이지 않는다(`todo_web/app.py:83`). 따라서 사용자는 할 일을 만들거나 조회·수정·삭제할 수 없고, 서버를 재시작하면 남는 데이터도 없다.

## Proposed outcome
세션 입력 요구서(REQUEST.md)의 실행 명령으로 서버를 띄우면, 사용자는 브라우저 화면과 JSON API로 할 일을 생성·목록 조회·상세 조회·부분 수정·삭제할 수 있다. 잘못된 요청은 요구서가 정한 상태 코드와 `error` 필드를 가진 JSON으로 거절된다. 모든 변경은 `--data` JSON 파일에 저장되어, 같은 파일로 서버를 다시 시작해도 생성·수정·삭제 결과가 유지된다.

## Affected users and systems
- 사용자: 브라우저 화면 또는 HTTP JSON API로 TODO를 관리하는 사용자.
- 시스템: `todo_web` 패키지의 HTTP 서버와 `--data` JSON 저장 파일, 회귀 테스트 `tests/`.
- 포함: `GET /`, `GET /health`, `/api/todos` 컬렉션·개별 리소스 API, 입력 검증·오류 응답, JSON 파일 영속성.
- 제외: 인증·권한, 다중 사용자 분리, 외부 DB, 배포.

## Constraints
- C-1: 서버는 `python -m todo_web.app --host 127.0.0.1 --port <PORT> --data <JSON_FILE>` 명령으로 실행된다.
- C-2: 외부 패키지를 추가하지 않으며 런타임 구현은 Python 표준 라이브러리만 사용한다(`.opal/AGENT.md` §제약).
- C-3: 기존 테스트(`tests/`)는 계속 통과해야 한다.
- C-4: 요청된 TODO 애플리케이션 범위 밖의 동작은 변경하지 않는다(`.opal/AGENT.md` §제약).

## Acceptance criteria
- AC-1: `GET /health`는 `200`과 본문 `{"ok": true}`를 반환한다.
- AC-2: `GET /`은 브라우저에서 열리는 HTML 화면을 반환하며, 화면에는 할 일 목록 영역·제목 입력·설명 입력·생성 버튼이 있고 사용자는 이 화면에서 할 일을 생성하고 목록에서 확인할 수 있다.
- AC-3: `POST /api/todos`에 `{"title": "...", "description": "..."}`를 보내면 `201`, `id`·`title`·`description`·`completed` 필드를 가진 생성 TODO 객체(`completed`는 `false`), 그리고 `Location: /api/todos/{id}` 헤더를 반환한다.
- AC-4: `GET /api/todos`는 `200`과 각 원소가 `id`·`title`·`description`·`completed` 필드를 가진 TODO 객체 배열을 반환하고, `GET /api/todos/{id}`는 존재하는 ID에 `200`과 해당 TODO 객체를, 없는 ID에 `404`를 반환한다.
- AC-5: `PATCH /api/todos/{id}`는 `title`·`description`·`completed` 중 하나 이상을 담은 요청으로 해당 TODO만 수정해 `200`과 수정된 객체를 반환하며, 다른 TODO 항목은 변하지 않고, 없는 ID에는 `404`를 반환한다.
- AC-6: `DELETE /api/todos/{id}`는 존재하는 ID에 `204`와 빈 본문을 반환하고 이후 그 TODO는 목록과 상세 조회에서 사라지며, 없는 ID에는 `404`를 반환한다.
- AC-7: 모든 API 응답은 JSON이며, 잘못된 JSON 본문과 검증 실패(앞뒤 공백 제거 후 빈 제목, 120자 초과 제목, 2000자 초과 설명)는 `400`, `Content-Type`이 `application/json`이 아닌 쓰기 요청(`POST`·`PATCH`)은 `415`, 지원하지 않는 method는 `405`를 반환하고, 모든 오류 응답은 최소한 `error` 필드를 가진 JSON 객체다.
- AC-8: TODO 데이터는 `--data`로 받은 JSON 파일에 저장되어, 서버를 종료하고 같은 파일로 다시 시작해도 생성·수정·삭제 결과가 유지되며, 저장 과정에서 다른 항목이 유실되지 않는다.
