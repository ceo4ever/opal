---
type: concept
title: 별칭 없는 개명이 미갱신 호출을 즉시 드러낸다
tags:
- refactoring
- api-design
- silent-failure
- lesson
sources:
- task:118
related:
- worktree-task-root-allocator-root-split
- backward-compat-default-value-discipline
- skill-rename-validate-pattern
- parser-drift-silent-longevity-lesson
created: '2026-09-12'
updated: '2026-09-12'
status: draft
---
## 개요

역할이 갈라진 함수를 개명할 때 하위호환 별칭을 남기지 않으면, 갱신되지 않은 호출은 실행 즉시 이름 없음 예외로 드러난다. 호출부를 전수로 찾아내는 일을 사람의 주의나 검색에 맡기지 않고 런타임이 대신하게 만드는 설계 수단이며, 응답이 항상 성공으로 나와 실패가 은폐되는 경로에서 특히 값이 크다.

## 결정 배경 (WHY)

- 태스크 118은 상태 도구의 단일 루트 탐색 함수를 해석용과 허브 쓰기용으로 갈랐다. 이 함수의 호출은 넷이었고, 그중 하나라도 갱신을 놓치면 완료 처리가 잘못된 루트에 이력을 쓰거나 이력을 통째로 누락한다(근거: task:118 ANALYSIS Q3).
- 문제는 그 실패가 보이지 않는다는 점이다. 완료 처리 명령은 이력 연결의 성공 여부와 무관하게 응답이 항상 성공으로 나가므로, 누락은 오류로 표면화되지 않고 다음 채번과 회고 품질만 조용히 떨어뜨린다(근거: task:118 PLAN §Risks H-1, ANALYSIS Q3 CLOSE 즉시 append 행).
- 그래서 완화책을 검사나 리뷰가 아니라 **이름 자체**에 걸었다. 호출 4곳의 좌표를 계획에 고정하고 하위호환 별칭을 두지 않아, 미갱신 호출이 남아 있으면 실행이 성립하지 않게 했다(근거: task:118 PLAN §Risks H-1 완화 열). 구현된 함수의 문서화 주석에도 이 의도가 계약으로 박혀 있다(`opal/tools/state-tool/state_tool.py:730-739`).

## 결정 내용

- 역할 분리를 동반한 개명에서는 하위호환 별칭을 두지 않는다. 별칭을 두면 미갱신 호출이 옛 이름으로 계속 동작하면서 **분리 이전의 잘못된 역할**을 수행하므로, 분리의 목적 자체가 무력해진다.
- 개명 전에 호출 좌표를 전수로 고정해 계획에 명시하고, 호출자별로 어느 쪽 역할인지 배정한다. 태스크 118에서는 해석 목적 3곳은 호출명만 바꾸고, 쓰기 목적 1곳은 탐색 호출을 제거해 허브 절대 경로를 인자로 받도록 바꿨다(근거: task:118 PLAN D-4).
- 테스트 호출부도 같은 원칙의 적용 대상이다. 옛 이름을 쓰던 테스트 호출 4곳이 새 이름으로 갱신됐고(`opal/tools/state-tool/tests/test_state_tool.py:3012,4644,4682,9209`), 별칭이 없으므로 하나라도 누락됐다면 스위트가 즉시 실패한다.
- 개명 완료는 "새 이름이 정의됐다"가 아니라 **"옛 이름이 저장소 전체에서 0건"**으로 판정한다. 태스크 118은 전체 스위트 404건 통과와 옛 이름 전역 0건을 함께 확인해 통과시켰다(근거: task:118 AGENTIC-LOG 엔트리 66).

## 영향 범위

한 함수가 두 역할을 겸하고 있어 호출자별로 갈라야 하는 모든 리팩터링에 적용된다. 특히 실패가 예외로 표면화되지 않는 경로 — 응답 코드가 항상 성공이거나, 결과가 즉시 읽히지 않는 누적 기록 — 를 만지는 개명에서는 별칭 부재가 유일하게 신뢰할 수 있는 전수 탐지 수단이다.

## 관련 페이지

- [[worktree-task-root-allocator-root-split]]
- [[backward-compat-default-value-discipline]]
- [[skill-rename-validate-pattern]]
- [[parser-drift-silent-longevity-lesson]]
