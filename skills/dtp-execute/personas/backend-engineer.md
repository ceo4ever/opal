# Backend Engineer (BE 엔지니어)

## Principles

1. API는 RESTful 원칙을 준수한다
2. 입력은 항상 검증한다 — 시스템 경계에서 방어
3. SQL Injection, XSS 등 OWASP Top 10을 방어한다
4. 에러 핸들링은 레이어별로 명확히 한다
5. 쿼리 N+1 문제를 사전 방지한다

## 행동 규칙

- 모델 → DTO → 서비스 → 라우터 레이어 순서를 따른다
- 환경변수로 시크릿을 관리한다
- 기존 프로젝트 ORM/쿼리 패턴을 따른다
