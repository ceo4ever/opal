---
name: otp-dev-short
description: "Short Task 오케스트레이터 (기본 모드). 코드 변경이 수반되는 모든 개발 작업. 트리거: 개발해줘, 수정해줘, 기능 추가해줘, 버그 수정해줘"
argument-hint: "[작업 설명]"
---

Short Task 파이프라인을 실행한다 (기본 모드).

1. 아래 경로에서 SKILL.md를 Read한다:
   - `{프로젝트}/.opal/skills/otp-dev-short/SKILL.md`
   - `~/.opal/skills/otp-dev-short/SKILL.md`
2. SKILL.md의 프로세스를 따라 실행한다.
3. 규모가 크면 Full Task(otp-dev) 에스컬레이션을 제안한다.
4. 작업 설명: $ARGUMENTS
