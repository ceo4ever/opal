---
template: sdlc-v2
---
# TASK: TODO CRUD 웹 앱 구현

> 요구 원천: 세션 입력 요구서 `REQUEST.md`(저장소 밖, 「요구서: TODO CRUD 웹 앱」). 요구서의 요구를 이 TASK의 요구사항으로 그대로 사용한다.

## Problem
현재 저장소의 TODO 웹 앱은 `GET /health`와 빈 HTML 화면만 제공하는 skeleton이다(`todo_web/app.py:44-82`). `POST`·`PATCH`·`DELETE`는 모두 `404`를 반환하고(`todo_web/app.py:84-91`), `--data` 경로는 받기만 할 뿐 저장에 쓰이지 않는다(`todo_web/app.py:93`). 사용자는 할 일을 생성·조회·수정·삭제할 수 없고, 서버를 재시작하면 남는 데이터도 없다.

## Proposed outcome
`python -m todo_web.app --host 127.0.0.1 --port <PORT> --data <JSON_FILE>`로 띄운 서버에서 사용자가 브라우저 화면과 JSON API로 TODO를 생성·목록 조회·상세 조회·부분 수정·삭제할 수 있다. 잘못된 요청은 요구서가 정한 상태 코드와 `error` 필드를 가진 JSON 오류로 거부된다. 모든 변경은 `--data` JSON 파일에 저장되어, 같은 파일로 서버를 재시작해도 생성·수정·삭제 결과가 유지되고 저장 중 다른 항목이 유실되지 않는다.

## Affected users and systems
- 사용자: 브라우저 화면 또는 HTTP 클라이언트로 TODO를 관리하는 사용자.
- 시스템: `todo_web/` 패키지(HTTP 서버·화면·저장), `tests/`(기존 회귀 테스트와 신규 검증), `--data`로 지정한 JSON 파일.
- 포함: 요구서의 실행 계약·화면·API 6종·검증과 예외·영속성.
- 제외: 인증·다중 사용자·페이지네이션·검색 등 요구서에 없는 기능, 외부 패키지 도입.

## Constraints
- C-1: 런타임 구현은 Python 표준 라이브러리만 사용하며 외부 패키지를 추가하지 않는다(요구서 §실행 계약, `.opal/AGENT.md` §제약).
- C-2: 기존 테스트(`tests/`)는 계속 통과해야 한다(요구서 §실행 계약).
- C-3: 서버 실행 인터페이스는 `python -m todo_web.app --host 127.0.0.1 --port <PORT> --data <JSON_FILE>`를 유지한다(요구서 §실행 계약).
- C-4: 모든 API 응답은 JSON이며(`204` 본문 없음 제외), 쓰기 요청(`POST`, `PATCH`)은 `Content-Type: application/json`만 받는다(요구서 §API).
- C-5: 요청된 TODO 애플리케이션 범위 밖의 동작은 변경하지 않는다(`.opal/AGENT.md` §제약).

## Acceptance criteria
- AC-1: `GET /health`는 `200`과 본문 `{"ok": true}`를 반환한다.
- AC-2: `GET /`은 브라우저에서 접근 가능한 HTML 화면을 반환하고, 화면에 할 일 목록 영역·제목 입력·설명 입력·생성 버튼이 있으며, 화면에서 API 또는 서버 렌더링을 통해 할 일을 생성하고 목록을 볼 수 있다.
- AC-3: `POST /api/todos`에 `{"title": "...", "description": "..."}`를 보내면 `201`과 생성된 TODO 객체(`id`, `title`, `description`, `completed`)를 반환하고, 새 TODO의 `completed`는 `false`이며, `Location` 헤더는 `/api/todos/{id}`다.
- AC-4: `GET /api/todos`는 `200`과 TODO 객체 배열(각 객체는 `id`, `title`, `description`, `completed` 필드 보유)을 반환하고, `GET /api/todos/{id}`는 존재하는 ID에 `200`과 해당 TODO 객체를, 없는 ID에 `404`를 반환한다.
- AC-5: `PATCH /api/todos/{id}`는 `title`, `description`, `completed` 중 하나 이상을 포함한 본문으로 해당 필드만 수정해 `200`과 수정된 TODO 객체를 반환하고, 다른 TODO 항목은 변하지 않으며, 없는 ID는 `404`다.
- AC-6: `DELETE /api/todos/{id}`는 성공 시 `204`와 빈 본문을 반환하고, 삭제된 항목은 이후 목록과 상세 조회에서 사라지며, 없는 ID는 `404`다.
- AC-7: 제목이 앞뒤 공백 제거 뒤 비어 있거나 120자를 넘거나 설명이 2000자를 넘는 검증 실패와 잘못된 JSON 요청 본문은 `400`, 잘못된 `Content-Type`의 쓰기 요청은 `415`, 지원하지 않는 method는 `405`를 반환하며, 모든 오류 응답은 최소한 `error` 필드를 가진 JSON 객체다.
- AC-8: TODO 데이터는 `--data`로 받은 JSON 파일에 저장되어, 서버를 종료하고 같은 `--data` 파일로 다시 시작해도 생성·수정·삭제 결과가 유지되고, 저장 중 다른 항목이 유실되지 않는다.
