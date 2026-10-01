---
type: concept
title: opal-skill-tester (opst) — 스킬 모의 실행 테스트
tags:
- opst
- testing
- skill
sources:
- skill:opal-skill-tester
related: [opal-pilot-dev2, opal-pilot-project-build, test-tool]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

단위 테스트로는 드러나지 않는 스킬 결함을 찾기 위해, 같은 모의 과업을 격리된 저장소에서 실제 헤드리스 Pilot 세션으로 끝까지 돌리고 세션에 보여 주지 않은 숨은 인수 테스트와 표준 지표로 채점하는 operator 스킬이다(`opal/skills/opal-skill-tester/SKILL.md:3-6`, `docs/PROJECT.md:235`).

## 현재 계약

- 실행 1회가 실제 Pilot 세션 하나라 비용이 크므로, 예상 시간·비용을 알리고 실행 조건을 최종 확인받은 뒤에만 돌린다(`opal/skills/opal-skill-tester/SKILL.md:15`).
- 시나리오는 Pilot과 무관하게 카탈로그에서 고른다. 시나리오의 대상 Pilot 목록은 권장일 뿐이고, 실행 가능 여부는 Pilot별 판정 프로필이 등록됐는지로 정한다(`opal/skills/opal-skill-tester/SKILL.md:55`).
- 변형을 하나만 주면 단일 실행, 둘 이상 주면 같은 조건의 비교 실행이 된다(`opal/skills/opal-skill-tester/SKILL.md:31`).
- 결과는 진행 중 태스크의 테스트 기록 폴더나 `tasks/` 아래에 날짜·대상·모드·제목 형식으로 남기고, 과거 기록과 비교한 추세 대시보드를 만든다(`opal/skills/opal-skill-tester/SKILL.md:34`).
- 요구서는 저장소 밖에, 숨은 테스트는 세션이 볼 수 없게 두며, 모의 저장소는 실제 저장소로 복사하지 않는다(`opal/skills/opal-skill-tester/SKILL.md:94-95`).

## 관련 페이지

- [[opal-pilot-dev2]] · [[opal-pilot-project-build]] — 판정 프로필이 등록된 시험 대상 Pilot
- [[test-tool]]
