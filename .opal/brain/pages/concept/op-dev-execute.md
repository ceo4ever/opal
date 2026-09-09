---
type: concept
title: op-dev-execute — 코드 실행 단계 스킬
tags:
- dev
- execute
- skill
sources:
- skill:op-dev-execute
- task:111
related:
- sdlc-v2-development-artifact-contract
- op-dev-plan
- test-tool
created: '2026-06-11'
updated: '2026-09-09'
status: active
---
## 개요

PLAN에 확정된 Work item만 구현하고 실제 검증 결과와 변경 파일을 반환하는 실행 단계 스킬이다.

## 현재 계약

sdlc-v2는 PLAN `Work items`를 공식 실행 입력으로 사용한다. 기존 `§4.2`와 실행 계획 형식은 legacy 재개 때만 읽는다. 워커는 자신의 파일 소유권과 선행 작업을 지키고, PM이 주입한 capability만 사용한다. RED 대상은 test-tool 잠금이 확인된 뒤 GREEN 구현을 시작한다.

## 근거

`opal/skills/op-dev-execute/SKILL.md:13`, `opal/skills/op-dev-execute/references/execute-guide.md:14`, task:111.

## 관련 페이지

- [[sdlc-v2-development-artifact-contract]]
- [[op-dev-plan]]
- [[test-tool]]
