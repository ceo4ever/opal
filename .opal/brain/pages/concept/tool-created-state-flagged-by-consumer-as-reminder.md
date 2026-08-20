---
type: concept
title: 생성 도구가 만든 상태를 소비 도구가 결함으로 부르는 구간 — 오탐이 아니라 리마인더
tags:
- memory-tool
- policy-gap
- design-pattern
- lesson
- task-096
sources:
- task:096
related:
- unresolvable-not-absent-two-vocabulary-split
- memory-lifecycle-graduation-workflow
created: '2026-08-20'
updated: '2026-08-20'
status: draft
---
## 개요

한 명령이 항상 만들어내는 상태를 다른 명령이 즉시 결함으로 표면화하는 구간은, 발견 당시 오탐처럼 보이기 쉽지만 실제로는 정책 공백을 드러내는 리마인더로 설계할 수 있다. `memory-tool`의 `append --kind memory`는 인덱스 행만 만들고 본문 파일은 만들지 않는데, 신설된 `review` 참조 무결성 검사가 이를 곧바로 검출한다 — 이 마찰은 결함이 아니라 이 기능이 존재하는 이유다.

## 결정 배경 (WHY)

- `append --kind memory`를 호출하면 인덱스 행이 생성되지만, `memory-tool` 코드 전체에서 `memory/*.md` 본문 파일을 실제로 생성하는 코드는 한 곳도 없다(`write_text`·`open(..., 'w')` grep 0건, `opal/tools/memory-tool/memory_tool.py:965` `cmd_append`는 `file` 필드에 경로 문자열만 기록한다). 즉 `append --kind memory`는 항상 본문 없는 행을 만들며, 본문은 호출자가 별도로 작성해야 한다(근거: task:096 DONE.md §4).
- 이 프로젝트의 실제 `.opal/MEMORY.json`에 남아 있던 "인덱스 참조 10건 중 7건 본문 부재"라는 상태가 정확히 이 경로로 생겼다 — 본문을 쓰지 않으면 그 행은 그대로 고아가 된다(근거: task:096 DONE.md §4).
- 참조 무결성 검사(`build_review_block`)를 신설하고 나면, `append` 직후 호출되는 `review` 블록이 자신이 방금 만든 행을 즉시 위반으로 표면화한다. 개발 중 이 현상은 처음엔 자기 자신을 결함으로 지목하는 것처럼 보였으나, 실제로는 "본문을 안 쓰면 곧바로 경고가 뜬다"는 것이 검사의 최대 가치라고 재해석됐다.
- 부수 효과로 정책 공백도 함께 드러났다 — 스키마는 `file` 포인터 필드를 필수로 요구하지만 그 경로에 파일이 실재해야 한다는 제약은 명시한 적이 없었고, 규범 문서도 "인덱스 행 + 개별 파일이 한 쌍"이라고 서술만 할 뿐 강제하지 않았다(근거: task:096 DONE.md §4).

## 결정 내용

- "본문 없는 행 = 결함으로 표면화"를 정책으로 명문화한다(`opal/core/references/harness/memory-learning.md:41` `[MUST]` 신설).
- 일반화: 도구 A가 항상 만들어내는 중간 상태를 도구 B가 즉시 결함으로 지목하는 패턴을 마주치면, 먼저 "A가 이 상태를 만드는 것이 의도인가"를 확인한다. 의도된 것이라면 B의 검출은 오탐이 아니라 A의 사용자에게 "다음 단계(본문 작성)를 잊지 말라"고 알리는 리마인더로 재해석하고, 그 재해석을 정책 문서에 명문화해 검사를 약화시키지 않는다.
- 이 마찰이 드러낸 정책 공백은 검사를 완화하는 방향이 아니라 정책을 명문화하는 방향으로 닫는다 — 스텁 파일을 자동 생성해 검사를 통과시키는 방식은 검사를 무력화하므로 채택하지 않는다(근거: task:096 DONE.md §9 PM 권고).

## 영향 범위

- `opal/tools/memory-tool/memory_tool.py:965` — `cmd_append`가 본문 파일을 만들지 않는 지점(변경하지 않음, 의도 확인 대상).
- `opal/core/references/harness/memory-learning.md:41` — 정책 명문화 지점.
- 생성 도구와 검사 도구가 분리된 모든 파이프라인 — 생성 시점과 검사 시점 사이에 사람이 채워야 하는 단계가 있는 구조에서 재발 가능한 패턴이다.

## 관련 페이지

- [[unresolvable-not-absent-two-vocabulary-split]] — 이 검사가 사용하는 검출 어휘
- [[memory-lifecycle-graduation-workflow]] — `append`가 속한 memory-tool 라이프사이클
