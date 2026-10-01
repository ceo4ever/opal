---
template: sdlc-v2
---
# TASK: TODO CRUD 웹 앱 구현

## Problem
현재 `todo_web`은 `/health`와 정적 HTML 화면만 제공하는 skeleton이다(`todo_web/app.py:44-85`). 쓰기·조회 API는 모두 `404`를 반환하고(`todo_web/app.py:76-83`) `--data` 파일은 받기만 하고 사용하지 않는다(`todo_web/app.py:85`). 그 결과 사용자는 할 일을 만들거나 조회·수정·삭제할 수 없고, 서버를 재시작하면 남는 데이터도 없다. 요구 원문은 세션 입력 요구서 `REQUEST.md` §화면·§API·§검증과 예외·§영속성이다.

## Proposed outcome
`python -m todo_web.app --host 127.0.0.1 --port <PORT> --data <JSON_FILE>`로 띄운 서버에서 사용자는 브라우저 화면과 JSON API로 할 일을 생성·목록 조회·상세 조회·부분 수정·삭제할 수 있다. 잘못된 요청은 규정된 상태 코드와 `error` 필드를 가진 JSON으로 거부되고, 모든 변경은 `--data` JSON 파일에 남아 같은 파일로 재시작해도 유지된다.

## Affected users and systems
- 사용자: 브라우저 화면 사용자와 HTTP JSON API 클라이언트
- 시스템: `todo_web` 패키지(HTTP 서버·HTML 화면·저장소), `tests/` 회귀 테스트, `--data`로 지정한 JSON 데이터 파일
- 포함: `REQUEST.md`에 명시된 화면, API 6종, 검증·예외, 영속성
- 제외: 인증·권한, 다중 프로세스 간 동시 쓰기 조율, 외부 DB, 배포

## Constraints
- C-1: 프로젝트 강제 계약 `.opal/AGENT.md` §제약을 따른다 — 외부 패키지를 추가하지 않고 런타임은 Python 표준 라이브러리만 사용하며, TODO 애플리케이션 범위 밖 동작은 바꾸지 않는다.
- C-2: 서버 실행 계약 `python -m todo_web.app --host 127.0.0.1 --port <PORT> --data <JSON_FILE>`을 유지한다.
- C-3: 기존 `tests/` 테스트는 계속 통과해야 한다.

## Acceptance criteria
- AC-1: `GET /`은 브라우저에서 열 수 있는 HTML을 `200`으로 반환하고, 그 화면에 할 일 목록 영역·제목 입력·설명 입력·생성 버튼이 있으며 화면에서 할 일을 생성하면 목록에 나타난다.
- AC-2: `GET /health`는 `200`과 본문 `{"ok": true}`를 반환한다.
- AC-3: `POST /api/todos`에 `{"title": "...", "description": "..."}`를 보내면 `201`, `Location: /api/todos/{id}` 헤더, `id`·`title`·`description`·`completed` 필드를 가진 생성 객체(`completed`는 `false`)를 반환한다.
- AC-4: `GET /api/todos`는 `200`과 각 원소가 `id`·`title`·`description`·`completed`를 가진 TODO 배열을 반환하고, `GET /api/todos/{id}`는 존재하면 `200`과 해당 객체를, 없는 ID면 `404`를 반환한다.
- AC-5: `PATCH /api/todos/{id}`는 `title`·`description`·`completed` 중 보낸 필드만 바꿔 `200`과 수정된 객체를 반환하고, 다른 TODO는 변하지 않으며, 없는 ID는 `404`다.
- AC-6: `DELETE /api/todos/{id}`는 `204`와 빈 본문을 반환하고 이후 목록·상세 조회에서 사라지며, 없는 ID는 `404`다.
- AC-7: 앞뒤 공백 제거 후 빈 제목, 120자 초과 제목, 2000자 초과 설명 같은 검증 실패와 파싱할 수 없는 JSON 본문은 `400`으로 거부되고 저장 데이터는 바뀌지 않는다.
- AC-8: `Content-Type`이 `application/json`이 아닌 `POST`·`PATCH` 요청은 `415`로 거부되고 저장 데이터는 바뀌지 않는다.
- AC-9: 지원하지 않는 method 요청은 `405`를 반환한다.
- AC-10: 모든 API 응답 본문은 JSON이며, 모든 오류 응답은 최소한 `error` 필드를 가진 JSON 객체다.
- AC-11: 생성·수정·삭제 결과는 `--data` JSON 파일에 저장되어 서버를 종료하고 같은 파일로 다시 시작해도 유지되며, 저장 과정에서 다른 항목이 유실되지 않는다.
