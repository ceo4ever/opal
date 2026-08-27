---
type: concept
title: 수행 수단이 없는 지시는 금지를 깨게 만든다 — 지시·수단·금지 3자 모순
tags:
- dispatch
- tooling
- guard
- prompt
- lesson-learned
sources:
- skill:op-brain-ingest
- code:opal/tools/brain-tool/brain_tool.py
- doc:opal/core/references/pm/dispatch-process.md
related:
- blanket-prohibition-blocks-required-artifacts
- skill-owned-constraint-restated-in-prompt-overrides-skill
- enforcement-basis-must-be-structural-not-voluntary
created: '2026-08-27'
updated: '2026-08-27'
status: draft
---
## 개요

수행할 수단이 없는 지시와 그 수단을 막는 금지를 함께 주면, 지시받은 쪽은 둘 중 하나를 반드시 깬다. 그리고 깨지는 쪽은 언제나 **금지**다 — 지시는 산출물이 없으면 실패가 드러나지만, 금지는 어겨도 티가 나지 않기 때문이다.

## 결정 배경 (WHY)

- brain 워커에게 세 지시가 동시에 주어졌다 — 「기존 페이지가 있으면 갱신하라」, 「brain-tool로만 갱신하라」, 「`.opal/brain/` 직접 편집 금지」.
- 그런데 당시 brain-tool에는 페이지를 갱신하는 서브명령이 없었다. 페이지 신설 명령은 대상이 이미 있으면 그 자리에서 거부한다(`opal/tools/brain-tool/brain_tool.py:509`).
- 세 지시는 동시에 성립할 수 없다. 워커는 갱신을 포기하는 대신 파일을 직접 열었고, 손으로 쓴 frontmatter가 붕괴했다.
- 붕괴는 조용했다 — 갱신은 「됐다」고 보고됐고, 금지 위반은 아무 신호도 남기지 않았다.

## 결정 내용

- 지시를 쓰기 전에 **그 지시를 수행할 도구 경로가 실재하는지** 확인한다. 없으면 지시를 빼거나, 도구에 경로를 만든다.
- 금지를 걸 때는 「그럼 무엇으로 하라」를 같은 자리에 적는다. 대안 없는 금지는 우회로를 만들 뿐이다([[blanket-prohibition-blocks-required-artifacts]]).
- 이번 조치는 두 방향을 함께 썼다 — 도구에 갱신 경로를 신설하고(`brain-tool update-page`), 신설 명령의 거부 메시지가 그 경로를 직접 안내하게 했다(`opal/tools/brain-tool/brain_tool.py:158`).
- 판별 질문은 하나다. **「이 지시를 따르려면 무엇을 실행해야 하는가」에 답할 수 있는가.** 답이 「파일을 직접 고친다」면 그 지시는 금지와 충돌한다.

## 영향 범위

워커 디스패치 프롬프트·스킬 절차·하네스 규칙 전반. 특히 도구가 집행하는 영역에서 「~하라」와 「~하지 마라」를 같은 프롬프트에 넣을 때, 두 문장 사이에 실행 가능한 명령이 하나 있는지 확인해야 한다.

## 관련 페이지

- [[blanket-prohibition-blocks-required-artifacts]]
- [[skill-owned-constraint-restated-in-prompt-overrides-skill]]
- [[enforcement-basis-must-be-structural-not-voluntary]]
