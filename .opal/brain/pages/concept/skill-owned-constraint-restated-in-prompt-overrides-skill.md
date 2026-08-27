---
type: concept
title: 프롬프트에 재서술한 제약은 스킬 원문을 이긴다
tags:
- dispatch
- prompt
- skill
- pm-discipline
- lesson-learned
sources:
- skill:op-brain-ingest
- code:opal/tools/brain-tool/brain_tool.py
- doc:opal/core/references/pm/dispatch-process.md
related:
- instruction-without-tool-path-forces-violation
- template-precedence-over-prose-norms
- blanket-prohibition-blocks-required-artifacts
created: '2026-08-27'
updated: '2026-08-27'
status: draft
---
## 개요

디스패치 프롬프트에 제약을 다시 적으면, 그 문장이 스킬 원문보다 강하게 작동한다. 워커는 스킬을 읽지만 프롬프트를 **자기에게 내려진 지시**로 받기 때문이다. 그래서 재서술이 원문과 조금이라도 어긋나면, 스킬이 막아 둔 경로가 프롬프트 쪽에서 열린다.

## 결정 배경 (WHY)

- brain 지식 등록 워커에게 내려간 프롬프트가 스킬의 금지 범위를 넓혀 적었다 — 스킬은 인덱스·로그 파일의 직접 편집을 금지하고 페이지 본문은 워커가 쓰도록 정의하는데, 프롬프트는 brain 디렉토리 전체의 직접 편집을 금지했다.
- 같은 프롬프트가 도구에 없는 동작(기존 페이지 갱신)을 함께 지시했다. 두 문장이 충돌하자 워커는 프롬프트를 기준으로 판단했고, 결과적으로 스킬이 정의한 절차 바깥으로 나갔다([[instruction-without-tool-path-forces-violation]]).
- 재서술이 일어난 구조적 이유가 있다 — 파일럿 스킬은 이 워커의 디스패치를 「입력: 태스크 폴더 경로」로만 정의하고 프롬프트 본문을 규정하지 않는다. 프롬프트 전체가 매번 즉흥 작성되므로, 작성자는 중요한 제약을 빠뜨리지 않으려 스킬 내용을 옮겨 적게 된다.
- 선의의 행동이 결함을 만든 경우다. 제약을 빠뜨리지 않으려는 시도가 원문과 어긋난 사본을 만들었다.

## 결정 내용

- 프롬프트의 제약 절에는 **문서에서 추출한 원문 인용**과 전 워커 공통 고정 항목만 넣는다. 대상 스킬이 이미 정의한 절차·금지·도구 사용법은 넣지 않는다 — 워커가 스킬을 읽는다.
- 판별은 두 갈래다. 쓰려는 제약이 스킬에 **있으면** 넣지 않는다. **없으면** 프롬프트가 아니라 스킬을 고친다. 프롬프트에 임시로 채워 넣는 선택지는 없다 — 그 프롬프트는 이번 한 번만 존재하고, 다음 태스크에서 같은 결함이 되풀이된다.
- 이 규칙을 워커 컨텍스트 주입 템플릿에 실물로 배치했다(`opal/core/references/pm/dispatch-process.md`) — 산문으로만 적으면 유도되지 않는다([[template-precedence-over-prose-norms]]).

## 영향 범위

모든 워커 디스패치. 특히 스킬이 절차를 촘촘히 정의한 영역일수록 재서술의 위험이 크다 — 옮겨 적을 내용이 많고, 그만큼 어긋날 여지도 크다.

## 관련 페이지

- [[instruction-without-tool-path-forces-violation]]
- [[template-precedence-over-prose-norms]]
- [[blanket-prohibition-blocks-required-artifacts]]
