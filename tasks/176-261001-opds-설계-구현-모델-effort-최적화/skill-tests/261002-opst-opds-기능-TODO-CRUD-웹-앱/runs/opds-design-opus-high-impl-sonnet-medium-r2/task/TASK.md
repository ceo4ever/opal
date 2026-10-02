---
template: sdlc-v2
---
# TASK: TODO CRUD 웹 앱

## Problem
현재 저장소의 TODO 웹 앱은 `/health`와 빈 HTML 화면만 제공하는 skeleton이다. 할 일을 만들고, 조회하고, 수정하고, 삭제하는 HTTP API와 영속 저장이 없어 사용자가 TODO 앱으로 쓸 수 없다. 잘못된 입력에 대한 일관된 거부 규칙도 없어 클라이언트가 오류를 판별할 수 없다.

## Proposed outcome
`python -m todo_web.app --host 127.0.0.1 --port <PORT> --data <JSON_FILE>`로 띄운 서버에서 다음이 관찰된다.

- 브라우저로 `GET /`에 접근하면 할 일 목록 영역, 제목 입력, 설명 입력, 생성 버튼이 있는 HTML 화면이 나온다. `GET /health`는 `200`과 `{"ok": true}`를 반환한다.
- JSON API(`/api/todos`, `/api/todos/{id}`)로 TODO를 생성·목록 조회·상세 조회·부분 수정·삭제할 수 있다. 각 TODO는 `id`, `title`, `description`, `completed`를 가진다.
- 잘못된 JSON, 검증 실패, 잘못된 `Content-Type`, 지원하지 않는 method, 없는 ID는 정해진 상태 코드와 `error` 필드를 가진 JSON 오류로 거부된다.
- TODO 데이터는 `--data` JSON 파일에 저장되어 서버 재시작 후에도 생성·수정·삭제 결과가 유지되고, 저장 중 다른 항목이 유실되지 않는다.

요구 원문: 사용자가 지정한 측정 시나리오 요구서 `REQUEST.md`(허브 저장소의 상위 디렉토리)의 요구를 그대로 TASK 요구사항으로 사용한다.

## Affected users and systems
- 사용자: 브라우저로 TODO 화면을 쓰는 사용자, JSON API를 호출하는 클라이언트.
- 시스템: `todo_web` 패키지(HTTP 서버·핸들러·저장소), `tests/` 회귀 테스트, `--data`로 지정한 JSON 데이터 파일.
- 포함: `GET /`, `GET /health`, `/api/todos` 컬렉션·항목 CRUD, 입력 검증과 오류 응답, JSON 파일 영속성.
- 제외: 인증·사용자 구분, 외부 DB, 외부 패키지 기반 프레임워크, 배포 구성, 요청된 TODO 범위 밖의 기능.

## Constraints
- C-1: 런타임 구현은 Python 표준 라이브러리만 사용하고 외부 패키지를 추가하지 않는다.
- C-2: 기존 테스트(`tests/`)는 수정 없이 계속 통과해야 한다.
- C-3: 프로젝트 PM profile(`.opal/AGENT.md` §제약)의 범위 계약 — 요청된 TODO 애플리케이션 범위 밖의 동작은 변경하지 않는다.

## Acceptance criteria
- AC-1: 실행 계약 명령으로 서버가 기동되고, `GET /health`는 `200`과 본문 `{"ok": true}`를, `GET /`는 브라우저에서 열리는 HTML 화면(할 일 목록 영역, 제목 입력, 설명 입력, 생성 버튼 포함)을 반환한다.
- AC-2: `POST /api/todos`(`{"title","description"}`)는 `201`, `completed: false`인 생성 TODO 객체, `Location: /api/todos/{id}` 헤더를 반환하고, 생성된 TODO는 `GET /api/todos`(`200`, TODO 객체 배열)와 `GET /api/todos/{id}`(`200`)로 조회된다. 없는 ID 상세 조회는 `404`다.
- AC-3: `PATCH /api/todos/{id}`는 `title`·`description`·`completed` 중 보낸 필드만 바꾼 TODO 객체를 `200`으로 반환하고, 다른 TODO 항목은 변하지 않는다. 없는 ID는 `404`다.
- AC-4: `DELETE /api/todos/{id}`는 `204`와 빈 본문을 반환하고, 삭제된 TODO는 목록과 상세 조회에서 사라진다. 없는 ID는 `404`다.
- AC-5: 제목은 앞뒤 공백 제거 후 비어 있으면 안 되고 최대 120자, 설명은 최대 2000자다. 검증 실패와 잘못된 JSON 본문은 `400`, `Content-Type: application/json`이 아닌 쓰기 요청(`POST`·`PATCH`)은 `415`, 지원하지 않는 method는 `405`를 반환하며, 모든 API 응답은 JSON이고 오류 응답은 `error` 필드를 가진 JSON 객체다.
- AC-6: TODO 데이터는 `--data` JSON 파일에 저장되어, 서버를 종료하고 같은 파일로 다시 시작해도 생성·수정·삭제 결과가 유지되며, 저장 중 다른 항목이 유실되지 않는다.
