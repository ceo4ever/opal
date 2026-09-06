---
type: concept
title: 이름이 아니라 성질로 금지한다
tags:
- header-standard
- code-scan
- design-principle
sources:
- task:107
related:
- tag-removal-is-not-history-removal
- regulation-tool-four-way-mismatch
created: '2026-09-06'
updated: '2026-09-06'
status: draft
---
## 개요

이름을 나열해 금지하는 규칙은 그 이름을 바꾼 새 사례로 곧장 부활한다. `changelog`라는 필드 이름을 금지해도 `revisions`라는 이름으로 같은 문제가 재발할 수 있다 — 금지해야 할 대상은 이름이 아니라 그 이름이 만들어내는 성질(이력 누적 구조)이다. 태스크 107은 규정과 구현 양쪽에서 이 원리를 실제로 적용했다(근거: `tasks/107-260906-opd-헤더필드-작성기준-이력분리/DONE.md` §4 #3).

## 결정 배경 (WHY)

- 규정 측: `header-standard.md` §2에 "이력 전용 필드를 신설하지 않는다 — `changelog`·`history`·`revisions` 이름 불문"이라고 명문화했다(근거: `AGENTIC-LOG.md` "[DECISION] `changelog` 28건 전건 편입" 절).
- 구현 측: 감지기가 처음에는 `changelog`라는 리터럴 이름 하나만 검사했는데, 컨벤션 진단(GC-C001)이 "구현이 자기가 세운 규정을 위반했다"고 지적했다 — 규정은 "이름 불문"인데 감지기는 이름 하나만 봤기 때문이다. 해소는 감지 축을 "필드 이름이 `changelog`인가"에서 "§2 필드 정의 표에 없는 필드(`undeclared_field`)가 존재하는가"로 일반화하는 것이었다(근거: `AGENTIC-LOG.md` "[ERROR] GC-C001" 절, `DONE.md` §4 #3).

## 결정 내용

같은 논리를 규정 문면(이름을 나열하되 "불문"을 명시)과 구현(이름 목록이 아니라 "정의되지 않음"이라는 성질로 판정)에 동형으로 적용했다. 이름 목록으로 금지 범위를 정의하면 항상 아직 나열되지 않은 이름이 다음 회피 경로가 된다 — 성질(정의되지 않은 것, 또는 이력을 서술하는 문장 구조)로 판정 축을 세우면 이름이 바뀌어도 판정이 유지된다.

## 영향 범위

`opal/core/references/header-standard.md` §2, `opal/tools/code-scan/code-scan.js`의 `undeclared_field` 감지 로직. 유사 원리는 [[tag-removal-is-not-history-removal]](이력 판정도 "태그 표기"가 아니라 "문장이 무엇을 말하는가"로 봐야 한다는 동형의 발견)에도 적용된다.

## 관련 페이지

- [[tag-removal-is-not-history-removal]]
- [[regulation-tool-four-way-mismatch]]
