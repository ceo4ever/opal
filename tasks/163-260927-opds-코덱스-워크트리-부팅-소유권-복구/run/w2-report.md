# W-2 실행 보고

- 완료: 2026-09-27 20:11 KST
- 범위: lease 부팅과 registry 권한 거부 분류

## 변경

- `ownership_core`가 lock 생성·획득 중 EPERM, EACCES, EROFS를 재시도하지 않고 즉시 `registry_write_denied`로 반환한다.
- `session_start_hook`이 `ownership-set`의 명시적 `registry_write_denied`를 보존한다.
- `ownership-set` 응답의 JSON `error`가 정확히 `registry_write_denied`일 때만 이를 보존한다. 다른 오류의 설명 문자열에 같은 토큰이 있어도 실패로 남긴다.
- `codex_adapter`는 lease를 이미 획득했고 hub registry 쓰기 거부만 확인된 경우에만 성공 및 `registry_owner_deferred_to_hub` 진단을 반환한다. 그 밖의 claim·등록·owner 실패는 기존 실패 경로를 유지한다.

## 검증

```text
/Users/iskang/.opal/.venv/bin/python -m pytest -q \
  opal/tools/ownership-tool/tests/test_codex_identity.py \
  opal/tools/ownership-tool/tests/test_session_start.py \
  opal/tools/ownership-tool/tests/test_lease.py
42 passed in 1.06s

EPERM mock: registry_write_denied, 0.0s
```

## 차단 사항

없음.
