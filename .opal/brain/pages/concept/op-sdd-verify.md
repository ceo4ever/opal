---
type: concept
title: op-sdd-verify — 제거된 SDD verify 물리 스킬
tags:
- sdd
- verify
- skill
- stale
sources:
- skill:op-sdd-verify
- task:112
related:
- skill-opal-pilot-sdd
- sdd-internal-stage-skill-ownership
created: '2026-06-11'
updated: '2026-09-10'
status: stale
---
## 개념 요약

옛 `op-sdd-verify` 물리 스킬은 Task 112에서 제거됐다. 현재 SDD REVIEW 검증 계약은 별도 최상위 스킬이 아니라 `opal-pilot-sdd`의 `verify-guide.md`가 소유한다.

## 현재 상태

- 물리 경로 `opal/skills/op-sdd-verify/`는 제거 대상이다.
- 현행 REVIEW의 S-1~S-6 검증 규칙은 유지된다.
- 검증 규칙 SSOT는 `opal/skills/opal-pilot-sdd/references/verify-guide.md`다.
- 설치본에서도 top-level `op-sdd-verify`가 재생성되지 않아야 한다.

## 파일 참조

`file_path: opal/skills/opal-pilot-sdd/references/verify-guide.md`

## 관련

- [[skill-opal-pilot-sdd]]
- [[sdd-internal-stage-skill-ownership]]
