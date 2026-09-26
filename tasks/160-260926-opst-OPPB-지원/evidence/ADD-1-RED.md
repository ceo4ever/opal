# ADD-1 RED 증빙: function-todo-crud

## 목적

TODO 기능이 아직 구현되지 않은 기반 저장소에서 숨은 인수 테스트가 실제로 실패하는지 확인한다.

## 실행

```bash
cd opal/skills/opal-skill-tester/scenarios/_bases/todo-web
SUT_REPO="$PWD" /Users/iskang/.opal/.venv/bin/python -m pytest -q \
  ../../function-todo-crud/hidden/test_hidden.py -p no:cacheprovider
```

## 결과

- 기대한 RED: `5 failed, 1 passed`, pytest exit `1`.
- 실패 영역: CRUD happy path, 삭제, 재시작 영속성, 입력 검증, JSON·Content-Type·method 예외 처리.
- 통과 영역: HTML 기본 화면과 기존 테스트.
- 해석: skeleton의 `/health`·`GET /` 기준은 유효하고, 구현 대상인 `/api/todos` 계약이 아직 없어 RED가 결정론적으로 발생했다.
