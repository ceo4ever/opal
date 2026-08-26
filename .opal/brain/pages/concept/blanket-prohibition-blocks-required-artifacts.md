---
type: concept
title: 워커 프롬프트의 포괄 금지가 규정 산출물을 막는다 — 금지 대신 반환 경로를 지정한다
tags:
- dispatch
- prompt
- worker
- pm-discipline
- lesson-learned
sources:
- task:103
related:
- worker-bypassed-blocked-tool-filename-trigger
- delegation-only-file-gate-bypass
created: '2026-08-26'
updated: '2026-08-26'
status: draft
---
## 개요

워커 프롬프트에 넣은 포괄 금지 문구가 **규정된 산출물까지 함께 막는다**. 금지로 행동을 좁히는 대신, 결과를 어디로 보낼지 경로를 지정해야 한다 (근거: task:103 DONE.md §4.5).

## 결정 배경 (WHY)

- 워커가 태스크 폴더를 임의로 어지럽히는 것을 막으려고 디스패치 프롬프트에 「태스크 폴더에 파일을 만들지 마라」를 넣었다.
- 그 문구가 파이프라인이 요구하는 산출물을 두 번 막았다 — 게이트 보고서 한 건과 테스트 시나리오 문서가 직접 지시한 증거 문서 한 건이다 (근거: task:103 DONE.md §4.5).
- 둘 다 PM이 대신 작성해 메웠고, 각 문서에 지시 오류 사실을 남겼다.
- 금지 문구는 「무엇을 하지 마라」만 말하고 「그럼 어떻게 하라」를 말하지 않는다. 워커는 규정 산출물과 임의 파일을 구별할 근거를 프롬프트에서 얻지 못한다.

## 결정 내용

- 금지 문구를 **반환 경로 지정**으로 바꿨다 — 「보고할 내용은 응답으로 반환하라」로 문구를 교체한 3회차부터 재발이 없다 (근거: task:103 DONE.md §4.5).
- 워커의 쓰기 범위를 좁힐 때는 금지 대상이 파이프라인 규정 산출물과 겹치는지 먼저 확인한다.

## 영향 범위

워커 디스패치 프롬프트 작성 전반. 제약을 넣을 때 「금지형」보다 「경로 지정형」이 안전하며, 금지형을 쓸 경우 규정 산출물 목록과 대조하는 절차가 선행돼야 한다.

## 관련 페이지

- [[worker-bypassed-blocked-tool-filename-trigger]]
- [[delegation-only-file-gate-bypass]]
