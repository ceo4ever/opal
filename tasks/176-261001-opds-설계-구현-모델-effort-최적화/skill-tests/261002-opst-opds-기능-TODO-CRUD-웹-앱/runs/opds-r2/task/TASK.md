---
template: sdlc-v2
---
# TASK: TODO CRUD 웹 앱 구현

## Problem
현재 `todo_web` 저장소는 `/health`와 빈 HTML 폼만 있는 skeleton이다. 할 일을 만들고, 조회하고, 수정하고, 삭제할 수 있는 API와 화면이 없고, 데이터를 파일에 남기지 않아 서버를 다시 시작하면 아무것도 유지되지 않는다. 요구서(`REQUEST.md`)가 정한 TODO CRUD 웹 앱으로 쓸 수 없는 상태다.

## Proposed outcome
`python -m todo_web.app --host 127.0.0.1 --port <PORT> --data <JSON_FILE>`로 띄운 서버에서 사용자가 브라우저 화면으로 할 일 목록을 보고 제목·설명을 입력해 생성할 수 있고, JSON API로 TODO를 생성·목록 조회·상세 조회·부분 수정·삭제할 수 있다. 잘못된 요청은 요구서가 정한 상태 코드와 `error` 필드를 가진 JSON으로 거부된다. 모든 변경은 `--data` JSON 파일에 저장되어 같은 파일로 서버를 재시작해도 유지되고, 한 항목의 변경이 다른 항목을 잃게 만들지 않는다.

## Affected users and systems
- 사용자: 브라우저로 화면을 쓰는 TODO 사용자, HTTP JSON API 클라이언트.
- 시스템: `todo_web/` 패키지(HTTP 서버·화면·저장), `tests/`(회귀 테스트), `--data`로 지정한 JSON 파일.
- 제외: 인증·다중 사용자, 외부 DB, 배포·패키징, 요구서에 없는 기능(검색·정렬·페이지네이션 등).

## Constraints
- C-1: 런타임 구현은 Python 표준 라이브러리만 사용하고 외부 패키지를 추가하지 않는다.
- C-2: 기존 테스트(`tests/`)는 변경 후에도 계속 통과해야 한다.
- C-3: 프로젝트 PM 프로필(`.opal/AGENT.md` §제약)의 범위 계약을 따른다 — 요청된 TODO 애플리케이션 범위 밖 동작은 변경하지 않는다.

## Acceptance criteria
- AC-1: `python -m todo_web.app --host 127.0.0.1 --port <PORT> --data <JSON_FILE>`로 서버가 실행되고, `GET /health`가 `200`과 본문 `{"ok": true}`를 JSON으로 반환한다.
- AC-2: `GET /`가 브라우저에서 열리는 HTML 화면을 반환하고, 화면에 할 일 목록 영역·제목 입력·설명 입력·생성 버튼이 있으며, 화면에서 제목·설명을 입력해 생성하면 그 할 일이 목록 영역에 나타난다.
- AC-3: `POST /api/todos`에 `{"title": "...", "description": "..."}`를 JSON으로 보내면 `201`과 생성된 TODO 객체(`id`, `title`, `description`, `completed` 포함, `completed` 기본값 `false`)를 JSON으로 반환하고, `Location` 헤더가 `/api/todos/{id}`이다.
- AC-4: `GET /api/todos`는 `200`과 TODO 객체 배열(각 객체에 `id`, `title`, `description`, `completed`)을, `GET /api/todos/{id}`는 `200`과 해당 TODO 객체를 반환하며, 없는 ID 상세 조회는 `404`다.
- AC-5: `PATCH /api/todos/{id}`는 `title`·`description`·`completed` 중 하나 이상을 담은 본문으로 해당 항목만 수정해 `200`과 수정된 객체를 반환하고, 다른 TODO 항목은 변하지 않으며, 없는 ID는 `404`다.
- AC-6: `DELETE /api/todos/{id}`는 `204`와 빈 본문을 반환하고, 삭제된 항목은 이후 목록과 상세 조회에서 사라지며, 없는 ID는 `404`다.
- AC-7: 잘못된 요청을 거부한다 — 앞뒤 공백 제거 뒤 빈 제목, 120자 초과 제목, 2000자 초과 설명 등 검증 실패와 잘못된 JSON 본문은 `400`, `Content-Type: application/json`이 아닌 `POST`·`PATCH`는 `415`, 지원하지 않는 method는 `405`이며, 모든 오류 응답은 최소한 `error` 필드를 가진 JSON 객체다.
- AC-8: TODO 데이터는 `--data` JSON 파일에 저장되어, 서버를 종료하고 같은 파일로 다시 시작해도 생성·수정·삭제 결과가 유지되고, 저장 과정에서 다른 항목이 유실되지 않는다.
