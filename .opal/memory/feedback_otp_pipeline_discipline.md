---
name: otp 파이프라인 단계 준수 피드백
description: otp 파이프라인 수행 시 TEST-SCENARIO 스킵 금지, EXECUTE 후 무단 커밋 금지 — 실제 프로젝트에서 반복 발생한 문제
type: feedback
---

otp 파이프라인 수행 시 단계를 절대 건너뛰지 않는다. 특히:

1. **TEST-SCENARIO 스킵 금지**: PLAN/TODO 승인 후 반드시 TEST-SCENARIO를 작성한 뒤 EXECUTE로 진입한다
2. **EXECUTE 후 무단 커밋 금지**: EXECUTE 완료 → Test → DONE.md → 보고 순서를 지킨다. 커밋은 캡틴이 명시적으로 요청할 때만 수행한다

**Why:** 실제 프로젝트에서 TEST-SCENARIO를 건너뛰고 바로 실행하거나, DONE.md 없이 커밋하는 문제가 반복 발생. 036 태스크에서 파이프라인 자체를 개선(TEST-SCENARIO를 PLAN/TODO와 통합)하여 구조적으로 방지함.

**How to apply:** 모든 otp-dev / otp-dev-short 수행 시 SKILL.md의 파이프라인 흐름을 정확히 따른다. 컨텍스트가 길어져도 단계를 스킵하지 않는다.
