---
name: 보안 스킬+에이전트 별도 태스크
description: FE/BE 워크플로우(030)에서 분리된 보안 검토 전용 스킬+에이전트 생성 태스크
type: task
---

보안 검토를 별도 스킬+에이전트로 만들어 필요 시 수행하는 구조.

**Why:** 030 태스크에서 보안을 PLAN/TEST에 끼워넣는 것보다 독립 컴포넌트로 분리하는 게 깔끔하다고 캡틴이 결정.

**How to apply:**
- 2단계 보안 검토 설계: PLAN(설계 보안) + TEST(코드 보안)
- 관련 스킬: openai/security-best-practices (OWASP top 10), getsentry/code-review (SQL injection, XSS, access control)
- 스모크 테스트(서버 기동→health 체크)는 dtp-dev-test-agent에 포함됨 (030에서 구현)
- execute-guide.md에 기본 보안 가드레일(하드코딩 시크릿, SQL injection 패턴)은 030에서 구현
- 별도 태스크에서: 전용 보안 스킬 + 보안 QA 에이전트 생성, 필요 시 호출 가능한 구조
