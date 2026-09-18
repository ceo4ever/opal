# opal-standard-heading (fixture README)

이 파일은 태스크 143 S-1 시나리오(README 원문 바이트 동일·`origin=readme`)를 검증하기 위한
fixture README다. 서버는 이 파일의 바이트를 그대로 `body.markdown`에 실어야 한다.

## 개요

`opal-standard-heading`는 README 우선 렌더 계약을 검증하는 fixture 스킬이다.

## 사용법

```bash
opal-standard-heading run --target ./demo
```

## 참고

- README가 있으면 SKILL.md 본문 대신 이 파일이 렌더된다.
- 원문은 파싱되지 않고 Markdown 그대로 전달된다.
