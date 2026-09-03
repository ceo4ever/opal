---
type: concept
title: 오탐 억제는 hit를 배열에서 빼지 않고 context 태그로 분류한다
tags:
- false-positive
- pattern-scan
- risk-detection
- task-105
sources:
- task:105
related:
- fixture-ownership-separation-closes-reward-hacking
- score-free-tiered-verdict-ladder
created: '2026-09-03'
updated: '2026-09-03'
status: draft
---
## 개요

문서·코드에서 위험 패턴을 문자열로 스캔할 때, 정상적으로 존재하는 금지 산문(예: "이 명령을 쓰지 마라")까지 그대로 매칭시키면 무해한 대상이 대량으로 오탈락한다. hit를 판정 결과 배열에서 제거하는 대신 각 hit에 `context` 태그(부정문·주석·픽스처 경로·산문 언급 등)를 붙여 분류하고, 그중 실제 위험을 뜻하는 태그만 최종 판정에 반영하면 오탐을 억제하면서 탈락 근거를 감사 가능하게 유지할 수 있다.

## 결정 배경 (WHY)

(근거: task:105 DONE.md §3.4) 스킬 문서는 "`rm -rf`를 쓰지 마라" 같은 금지 산문을 정상적으로 포함한다. 위험 패턴을 무조건 매칭하면 무해한 스킬이 전량 위험 판정을 받아 절차가 기능 정지한다.

## 결정 내용

- hit를 배열에서 제거하지 않고 각 hit에 `context` 태그를 붙인다. 우선순위는 `negated`(부정문) > `comment`(주석) > `fixture`(테스트 픽스처 경로) > `active`(실제 위험) 순으로 판정하며, **`active`로 분류된 hit만 최종 위험 판정에 반영**한다.
- 마크다운 문서에서는 코드펜스·인라인 백틱 스팬 안의 매치만 코드 영역으로 계상해, 산문 설명 중의 언급과 실행 가능한 코드 스니펫을 구분한다.
- **대가는 미탐이다** — 백틱이나 코드펜스 없이 산문만으로 위험을 지시하는 문서는 이 방식으로는 통과한다. 그래서 이 판정 층은 "필요조건이며 사람 검토를 대체하지 않는다"를 문서에 명문화해야 한다(→ [[score-free-tiered-verdict-ladder]] 1층 원칙과 동일 계열).

## 영향 범위

- `opal/tools/skill-registry/skill-registry.js` — `scan-risk` 서브명령의 hit 분류 로직
- 유사한 패턴 매칭 기반 오탐 억제가 필요한 모든 정적 스캔 도구에 일반화 가능

## 관련 페이지

- [[fixture-ownership-separation-closes-reward-hacking]]
