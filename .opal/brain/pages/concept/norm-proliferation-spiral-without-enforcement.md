---
type: concept
title: 규범 증식 나선 — 집행 수단 부재의 산문 규범
tags:
- enforcement
- agent-md
- norm-design
- anti-pattern
sources:
- task:108
related:
- lean-core-relocation-benefit-precondition
- template-precedence-over-prose-norms
- agent-md-digest-pattern
created: '2026-09-06'
updated: '2026-09-06'
status: draft
---
## 개요

산문으로만 서술되고 집행 도구가 없는 규범은 개정될 때마다 직전 개정이 열어준 회피 경로를 막는 식으로 몸집을 불려간다. `opal/core/AGENT.md` §보고 형식은 13회 개정 중 11회가 특정 7일(설치 초기)에 집중되었고, 각 개정이 직전 개정의 허점을 메우는 연쇄였다(근거: task:108 DONE.md §7 발견 1, 변경이력 실측).

## 결정 배경 (WHY)

- (근거: task:108 DONE.md §7 발견 1) §보고 형식은 골격 4층·헤딩 체계·마크다운 어휘 채택/금지 목록·템플릿 3종·원칙 10항목·체크리스트 13항목·역할별 표기 표까지 누적되어 177줄에 달했다. 이 규범을 집행하는 도구(lint, 자동 검사기 등)는 하나도 없었다 — 전적으로 산문 지시에 의존했다.
- (추론: 코드패턴) 집행 도구가 없는 산문 규범은 위반 사례가 발견될 때마다 "그 사례를 금지하는 문장 추가"로만 대응할 수 있다. 문장 추가는 다른 우회 경로를 닫지 못하므로, 새 우회가 다시 발견되고 또 문장이 추가되는 나선이 반복된다.
- (근거: OPAL 헌법 "Enforce, don't just advise" 원칙) 이 원칙은 규범을 도구로 집행하지 못하면 프레임워크가 그 규범을 실제로 유도하지 못한다고 명시한다. §보고 형식의 개정 나선은 이 원칙이 지켜지지 않았을 때 나타나는 구체적 증상 사례다.

## 결정 내용

- 규범이 반복 개정되며 몸집이 커지는 패턴을 발견하면, "규범 문장을 더 정교하게 다듬을 것"이 아니라 "이 규범을 집행할 도구가 있는가"를 먼저 판정한다.
- 집행 도구를 만들 수 없거나 만들 계획이 없는 규범은, 계속 산문으로 누적시키기보다 폐지·축소·다른 형태(체크리스트·게이트)로의 전환을 검토 대상에 올린다. task:108의 §보고 형식 전면 제거가 이 판단을 실제로 적용한 사례다(`[[lean-core-relocation-benefit-precondition]]`).
- 개정 빈도·집중도(예: 특정 기간에 몰린 개정 횟수)는 "집행 수단 없는 규범 증식"의 조기 경보 신호로 쓸 수 있다.

## 영향 범위

산문으로만 존재하는 모든 상시 로드 규범(AGENT.md·opal-pm.md 등 부트스트랩 파일) 설계·개정 검토에 적용된다. 새 규범을 추가할 때도 "이 규범을 나중에 도구로 집행할 수 있는가"를 사전 판정 기준으로 삼을 수 있다.

## 관련 페이지

- [[lean-core-relocation-benefit-precondition]]
- [[template-precedence-over-prose-norms]]
- [[agent-md-digest-pattern]]
