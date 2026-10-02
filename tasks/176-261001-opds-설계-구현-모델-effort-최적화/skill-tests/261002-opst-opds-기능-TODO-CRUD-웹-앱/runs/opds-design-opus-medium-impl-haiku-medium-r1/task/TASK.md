---
template: sdlc-v2
---
# TASK: TODO CRUD 웹 앱 구현

## Problem
저장소의 TODO 웹 앱은 `/health`와 기본 HTML 화면만 있는 skeleton이다. 할 일을 생성·조회·수정·삭제하는 API와 영속 저장이 없어 사용자가 할 일을 관리할 수 없고, 서버를 재시작하면 남는 데이터도 없다. 요구서(`REQUEST.md`, 요구서: TODO CRUD 웹 앱)의 요구를 이 태스크의 요구사항으로 그대로 사용한다.

## Proposed outcome
- 서버를 `python -m todo_web.app --host 127.0.0.1 --port <PORT> --data <JSON_FILE>`로 실행하면, 브라우저에서 `GET /`로 할 일 목록 영역·제목 입력·설명 입력·생성 버튼이 있는 HTML 화면을 볼 수 있고, 화면에서 할 일을 만들고 목록으로 확인할 수 있다.
- `GET /health`, `GET/POST /api/todos`, `GET/PATCH/DELETE /api/todos/{id}` JSON API로 TODO(`id`, `title`, `description`, `completed`)를 생성·조회·수정·삭제할 수 있다.
- 잘못된 입력·Content-Type·method·없는 ID는 요구서가 정한 상태 코드와 `error` 필드를 가진 JSON 오류로 거부된다.
- 생성·수정·삭제 결과가 `--data` JSON 파일에 저장되어, 같은 파일로 서버를 재시작해도 유지되고 다른 항목이 유실되지 않는다.

## Affected users and systems
- 사용자: 브라우저 또는 HTTP 클라이언트로 TODO를 관리하는 사용자.
- 시스템: `todo_web/` 패키지(서버·화면·API·저장), `tests/` 회귀 테스트, `--data`로 지정한 JSON 데이터 파일.
- 범위 밖: 인증·다중 사용자, 외부 DB, 배포 설정, 요구서에 없는 API.

## Constraints
- C-1: 런타임 구현은 Python 표준 라이브러리만 사용하며 외부 패키지를 추가하지 않는다(요구서 §실행 계약, `.opal/AGENT.md` §제약).
- C-2: 서버 실행 명령 `python -m todo_web.app --host 127.0.0.1 --port <PORT> --data <JSON_FILE>` 계약을 유지한다.
- C-3: 기존 테스트(`tests/`)는 계속 통과해야 한다.
- C-4: 요청된 TODO 애플리케이션 범위 밖의 동작은 변경하지 않는다(`.opal/AGENT.md` §제약).

## Acceptance criteria
- AC-1: `GET /`은 브라우저에서 접근 가능한 HTML 화면을 반환하며, 화면에 할 일 목록 영역, 제목 입력, 설명 입력, 생성 버튼이 있고 화면에서 생성한 할 일이 목록에 표시된다.
- AC-2: `GET /health`는 `200`과 본문 `{"ok": true}`를 JSON으로 반환한다.
- AC-3: `GET /api/todos`는 `200`과 TODO 객체 배열을 반환하며, 각 객체는 `id`, `title`, `description`, `completed` 필드를 가진다.
- AC-4: `Content-Type: application/json`인 `POST /api/todos` `{"title": "...", "description": "..."}`는 `201`, 생성된 TODO 객체(`completed` 기본값 `false`), `Location: /api/todos/{id}` 헤더를 반환한다.
- AC-5: `GET /api/todos/{id}`는 존재하는 ID에 `200`과 해당 TODO 객체를, 없는 ID에 `404`를 반환한다.
- AC-6: `PATCH /api/todos/{id}`는 `title`, `description`, `completed` 중 하나 이상을 받아 `200`과 수정된 TODO 객체를 반환하고 다른 TODO 항목은 변하지 않으며, 없는 ID는 `404`를 반환한다.
- AC-7: `DELETE /api/todos/{id}`는 성공 시 본문 없는 `204`를 반환하고 이후 목록과 상세 조회에서 해당 항목이 사라지며, 없는 ID는 `404`를 반환한다.
- AC-8: 제목은 앞뒤 공백 제거 뒤 비어 있으면 안 되고 최대 120자, 설명은 최대 2000자이며, 검증 실패와 잘못된 JSON 요청 본문은 `400`을 반환한다.
- AC-9: `Content-Type`이 `application/json`이 아닌 쓰기 요청(`POST`, `PATCH`)은 `415`, 지원하지 않는 method는 `405`를 반환한다.
- AC-10: 모든 API 응답은 JSON이며 모든 오류 응답은 최소한 `error` 필드를 가진 JSON 객체다.
- AC-11: TODO 데이터는 `--data` JSON 파일에 저장되어, 서버를 종료하고 같은 파일로 다시 시작해도 생성·수정·삭제 결과가 유지되고 저장 중 다른 항목이 유실되지 않는다.
