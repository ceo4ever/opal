---
name: otp-dev
description: "Full Task 오케스트레이터. 사용자가 명시적으로 Full Task를 요청한 경우. 트리거: Full Task로 해줘, Full로 개발해줘"
argument-hint: "[작업 설명]"
---

Full Task 파이프라인을 실행한다.

1. 아래 경로에서 SKILL.md를 Read한다:
   - `{프로젝트}/.opal/skills/otp-dev/SKILL.md`
   - `~/.opal/skills/otp-dev/SKILL.md`
2. SKILL.md의 프로세스를 따라 실행한다.
3. 작업 설명: $ARGUMENTS
