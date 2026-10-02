---
type: concept
title: 디스패치 model 지정이 에이전트 frontmatter보다 우선
tags:
- agent
- model
- dispatch
sources:
- task:176
related: [model-effort-customization-points-and-effort-mapping-gap, agent-effort-policy-inherit-by-default, opst-variant-design-impl-settings]
created: '2026-10-02'
updated: '2026-10-02'
status: draft
---
## 개요

서브에이전트를 디스패치할 때 호출자가 `model`을 지정하면, 에이전트 정의 파일(frontmatter)의 `model`보다 호출 지정이 우선한다. 실제 호출로 확인된 사실이다.

## 결정 배경 (WHY)

- (근거: task:176 DONE.md 실호출 프로브) 모의 저장소의 구현 에이전트 정의에 `haiku`를 적으면 서브에이전트가 `claude-haiku-4-5`로 실행됐고, 같은 상태에서 디스패치에 `model: opus`를 주면 정의의 `haiku`를 이기고 opus로 실행됐다.
- (근거: task:176 DONE.md) 같은 에이전트를 파일럿 지시문·에이전트 레지스트리 문서·frontmatter가 각각 다른 모델로 말할 수 있으므로, 어느 층이 이기는지 알아야 설정이 실제로 먹는지 판단할 수 있다.

## 결정 내용

- 모델 우선순위: 디스패치 지정 > 에이전트 정의 frontmatter. 정의에 적은 값은 호출이 모델을 말하지 않을 때의 기본값이다.
- effort의 우선순위는 확인하지 못했다. `--effort` 수용은 확인했으나, 구현 에이전트 frontmatter `effort`가 서브에이전트에 반영되는지는 `modelUsage`로 볼 수 없었다 (근거: task:176 DONE.md 한계).
- 단일 진실 원천(SSOT)을 하나 정하고 이 우선순위를 문서화해야 한다는 필요가 남아 있다. 현재는 문서화되어 있지 않다.

## 영향 범위

- 에이전트 frontmatter만 고쳐서는 호출이 모델을 명시하는 경로의 실행 모델이 바뀌지 않는다.
- 측정 도구의 구현 모델 변형은 이 우선순위를 전제로 정의 사본을 쓴다. [[opst-variant-design-impl-settings]] 참조.

## 관련 페이지

- [[model-effort-customization-points-and-effort-mapping-gap]]
- [[agent-effort-policy-inherit-by-default]]
- [[opst-variant-design-impl-settings]]
