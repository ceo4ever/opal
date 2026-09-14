---
type: concept
title: 개수·열거 표기는 문서 여러 곳에 흩어져 조용히 낡는다
tags:
- documentation
- drift
- task-122
- lesson
sources:
- task:122
related:
- verification-only-workitem-needs-remediation-owner
created: '2026-09-12'
updated: '2026-09-12'
status: active
---
## 개요

새 컴포넌트를 하나 추가하면, 그 개수·목록을 언급하는 자리는 프로젝트 문서 전체에 걸쳐 여러 곳에 흩어져 있다 — 심지어 문서 한 편 안에서도 여러 곳이다. PLAN Work item과 PM의 갱신 지시가 그중 한 자리만 짚으면 나머지는 조용히 낡은 채로 남는다(근거: task:122 AGENTIC-LOG.md 엔트리 #49~#51).

## 결정 배경 (WHY)

- (근거: task:122 AGENTIC-LOG.md 엔트리 #49) `docs/CONVENTIONS.md` 한 문서 안에서만도 개수 표기가 최소 2곳이었다 — §약어(Alias) 표의 "30종"과 §도구 우선 원칙의 "전체 목록: `opal/tools/` (20종)". W-18 Work item과 PM의 갱신 지시는 앞의 것(약어 "30종"→"31종")만 짚었고, 뒤의 것(도구 "20종")과 새 도구(`self-pm-tool`)의 열거 누락은 워커의 1차 산출물 검토에서야 드러났다.
- (근거: task:122 AGENTIC-LOG.md 엔트리 #49) 이 오류의 귀책은 워커가 아니라 **PLAN Work item 서술과 PM 지시** 쪽이다 — 지시 자체가 한 곳만 가리켰기 때문에 워커가 나머지를 놓치는 것이 오히려 자연스러운 결과였다.
- (근거: task:122 AGENTIC-LOG.md 엔트리 #51) 재지시 1회를 소모한 뒤에도 PM은 "같은 문서 안에 복수 개수 표기가 있다"는 사실 자체를 컴포넌트 신설 태스크의 일반 규칙으로 아직 정식화하지 않았다 — PLAN 작성 시 "개수·열거 표기 전수 grep"을 변경 대상 도출 단계에 넣는 절차가 없다.

## 결정 내용

컴포넌트를 신설하는 태스크의 PLAN 변경 대상 도출 단계에서, 그 컴포넌트의 개수·열거가 언급될 수 있는 모든 문서·문서 내 모든 절을 전수 grep으로 훑어 변경 대상 목록에 올린다. Work item 서술이 "한 문서"가 아니라 "그 문서 안의 각 개수 표기 위치"까지 명시적으로 짚어야, PM 지시와 워커 실행 양쪽에서 같은 누락이 재발하지 않는다.

## 영향 범위

이번 태스크에서 실제로 흔들린 자리는 `docs/CONVENTIONS.md`(§약어 표·§도구 우선 원칙)였지만, 같은 성격의 위험은 `docs/PROJECT.md`·`docs/ARCHITECTURE.md`처럼 스킬·도구·에이전트 개수를 서술하는 다른 문서에도 동일하게 적용된다. PM이 이번 태스크의 P4 배치에서 개수 실측값을 선측정해 워커들에게 동일 값으로 주입한 것(`opal/skills` 44·`opal/tools` 21·`opal/agents` 15·`skills` 8)은 이 위험을 완화하는 임시 대응이었을 뿐, 전수 grep을 PLAN 절차 자체에 넣는 일반 규칙은 아직 성립하지 않았다.

## 관련 페이지

- [[verification-only-workitem-needs-remediation-owner]] — 같은 태스크 EXECUTE 단계에서 함께 드러난 PLAN 작성 단계의 세부 규칙 공백 사례.
