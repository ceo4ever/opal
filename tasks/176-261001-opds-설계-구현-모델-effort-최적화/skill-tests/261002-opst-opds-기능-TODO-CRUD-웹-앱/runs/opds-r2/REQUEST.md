@header {
  "module": "function-todo-crud-request",
  "layer": "scenario-request",
  "domain": "opal-skill-tester",
  "description": "Pilot 중립 TODO CRUD 웹 앱 기능 시나리오의 세션 입력 요구서를 정의한다.",
  "exports": []
}

# 요구서: TODO CRUD 웹 앱

현재 저장소에는 Python 표준 라이브러리 기반의 작은 TODO 웹 앱 skeleton이 있다. 아래 요구를 만족하도록 구현한다.

## 실행 계약

- 서버는 `python -m todo_web.app --host 127.0.0.1 --port <PORT> --data <JSON_FILE>`로 실행한다.
- 외부 패키지를 추가하지 않는다. 런타임 구현은 Python 표준 라이브러리만 사용한다.
- 기존 테스트(`tests/`)는 계속 통과해야 한다.

## 화면

- `GET /`은 브라우저에서 접근 가능한 HTML 화면을 반환한다.
- 화면에는 할 일 목록 영역, 제목 입력, 설명 입력, 생성 버튼이 있어야 한다.
- 화면은 아래 API를 사용하거나 서버 렌더링으로 구현할 수 있다.

## API

모든 API 응답은 JSON이다. 쓰기 요청(`POST`, `PATCH`)은 `Content-Type: application/json`만 받는다.

1. `GET /health`
   - `200`
   - 본문: `{"ok": true}`

2. `GET /api/todos`
   - `200`
   - 본문: TODO 객체 배열
   - 각 TODO 객체는 `id`, `title`, `description`, `completed` 필드를 가진다.

3. `POST /api/todos`
   - 요청 본문: `{"title": "...", "description": "..."}`
   - 성공 시 `201`, 생성된 TODO 객체 반환
   - 새 TODO의 `completed` 기본값은 `false`
   - `Location` 헤더는 `/api/todos/{id}`

4. `GET /api/todos/{id}`
   - 성공 시 `200`, 해당 TODO 객체 반환
   - 없는 ID는 `404`

5. `PATCH /api/todos/{id}`
   - 요청 본문은 `title`, `description`, `completed` 중 하나 이상을 포함할 수 있다.
   - 성공 시 `200`, 수정된 TODO 객체 반환
   - 다른 TODO 항목은 변하지 않아야 한다.
   - 없는 ID는 `404`

6. `DELETE /api/todos/{id}`
   - 성공 시 `204`, 본문 없음
   - 삭제 후 목록과 상세 조회에서 사라져야 한다.
   - 없는 ID는 `404`

## 검증과 예외

- 제목은 앞뒤 공백 제거 뒤 비어 있으면 안 된다.
- 제목은 최대 120자, 설명은 최대 2000자다.
- 잘못된 JSON 요청 본문은 `400`을 반환한다.
- 검증 실패는 `400`을 반환한다.
- 잘못된 `Content-Type`의 쓰기 요청은 `415`를 반환한다.
- 지원하지 않는 method는 `405`를 반환한다.
- 오류 응답은 최소한 `error` 필드를 가진 JSON 객체여야 한다.

## 영속성

- TODO 데이터는 `--data`로 받은 JSON 파일에 저장한다.
- 서버를 종료하고 같은 `--data` 파일로 다시 시작해도 생성·수정·삭제 결과가 유지되어야 한다.
- 저장 중 다른 항목이 유실되면 안 된다.
