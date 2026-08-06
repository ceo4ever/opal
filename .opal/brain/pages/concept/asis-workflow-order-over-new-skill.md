---
type: concept
title: 부품은 있고 순서가 없었다 — 신규 스킬 대신 참조 문서 + 행동 프로세스
tags:
- pm
- architecture-decision
- ssot
- task-084
sources:
- task:084
related:
- asis-analysis-five-stage-workflow
- inherit-new-boundary-fixed-before-writing
- opal-pm-promotion-gate
- readme-ssot-principle
created: '2026-08-06'
updated: '2026-08-06'
status: draft
---
## 개요

"현황 분석을 잘하게 하자"는 요구에 대해 신규 스킬·신규 파이프라인을 만들지 않고, 참조 문서 1건과 PM 행동 프로세스 등록으로 해결했다. 프레임워크에 필요한 부품은 이미 전부 있었고 없던 것은 그 부품들을 잇는 **순서**였기 때문이다 (근거: task:084 DONE.md §1).

## 결정 배경 (WHY)

착수 전 조사에서 필요한 규칙이 전부 이미 존재한다는 사실이 확인됐다 — brain 사전 조회, code-scan 무조건 호출과 Glob/Grep 직행 금지, 코드=SSOT 불일치 판정 기준, 근거 인용 포맷, 보고 레이아웃 판정 등 7종이 각기 다른 문서에 흩어져 있었다. 부족한 것은 규칙이 아니라 "언제 무엇을 먼저 하는가"였다 (근거: task:084 DONE.md §1, PLAN §중복 회피 설계).

이 상태에서 스킬이나 파이프라인을 신설하면 흩어진 규칙을 스킬 본문으로 다시 옮겨 적게 되고, 원본과 사본이 다른 값을 말하는 이중 SSOT가 생긴다. 게다가 AS-IS 분석은 기획 대화 중간에 발생하는 행위라, 게이트가 있는 파이프라인을 태우면 대화 흐름 자체가 끊긴다 (근거: task:084 DONE.md §6 판단 근거).

## 결정 내용

- **산출 형태는 참조 문서 1건**이다 — `opal/core/references/pm/asis-analysis.md`가 5단계 순서·4축 수집 규율·규모 분기·폴백 매트릭스를 소유하고, 나머지는 경로 참조로 상속한다.
- **진입 경로는 두 갈래**다 — PM 프로세스 문서에 stub 절을 두어 PM이 항상 보는 자리에 5단계 이름을 노출하고(`opal/core/references/opal-pm.md:353-359`), 프레임워크 AGENT.md Lazy 트리거 테이블에 행을 등록해 필요한 시점에만 상세 문서를 로드하게 했다.
- **행동 프로세스로 등록하되 강제 게이트는 두지 않는다** — 대화 중 발생하는 행위이므로 단계 승인·상태 파일 같은 파이프라인 장치를 붙이지 않았다.
- 신규 코드 변경은 0건이고, 문서 4건(신규 1 · 수정 3)의 순증은 264줄이다 (근거: task:084 DONE.md §2).

## 영향 범위

"프로세스를 개선하라"는 요구를 받았을 때 먼저 물어야 할 질문의 형태를 보여준다 — 없는 것이 **규칙**인지 **순서**인지 구분하는 것이다. 규칙이 없으면 새 규칙을 소유할 자리(스킬·도구·참조 문서)가 필요하지만, 규칙은 있는데 순서가 없으면 순서만 소유하는 얇은 문서 1건과 그 문서로 가는 진입 경로면 충분하다. 후자에서 스킬을 만들면 규칙 복제와 이중 SSOT라는 비용만 남는다.

## 관련 페이지

- [[asis-analysis-five-stage-workflow]]
- [[inherit-new-boundary-fixed-before-writing]]
- [[opal-pm-promotion-gate]]
- [[readme-ssot-principle]]
