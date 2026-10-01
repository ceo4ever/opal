---
type: concept
title: opst OPPB 판정 프로필 — 종료 계약 위반 검출
tags:
- opst
- oppb
- task
sources:
- task:160
related: [opal-skill-tester, opal-pilot-project-build, oppb-run-records-follow-task-lifecycle]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

스킬 모의 테스트(opst)에 OPPB 판정 프로필을 추가한 결정이다. P1·P3·P4·P5 단계 측정, 태스크에 남는 닫힌 실행 보존본, 예전 실행 루트 미생성, 물리 작업본 회수를 판정 항목으로 넣었고, 일반 워크트리 Pilot의 체크포인트 판정은 그대로 두었다(`tasks/160-260926-opst-OPPB-지원/DONE.md:5-7`, `opal/skills/opal-skill-tester/scripts/skill_tester.py`).

## 핵심 결정

- 실제 유료 실행에서 기능 회귀 7건과 숨은 인수 테스트 4건은 모두 통과했지만, 작업본 회수 단계가 완료로 표기됐는데도 작업본이 남아 있어 최종 불합격으로 판정됐다(`tasks/160-260926-opst-OPPB-지원/DONE.md:9-10`).
- 이것은 테스터가 OPPB 종료 계약 위반을 검출한 결과로 보고, OPPB 런타임 수정은 범위에 넣지 않았다(`tasks/160-260926-opst-OPPB-지원/DONE.md:11`).
- 기존 실행 폴더를 다시 채점해도 보존본은 정상이고 작업본 회수만 거짓이라는 같은 판정이 재현됐다(`tasks/160-260926-opst-OPPB-지원/DONE.md:38-39`).

## 관련 페이지

- [[opal-skill-tester]]
- [[opal-pilot-project-build]]
- [[oppb-run-records-follow-task-lifecycle]]
