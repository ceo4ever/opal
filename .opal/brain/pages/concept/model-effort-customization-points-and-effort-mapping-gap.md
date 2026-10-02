---
type: concept
title: 모델·effort 커스텀 지점 7곳과 effort 매핑 층 부재
tags:
- model
- effort
- settings
sources:
- task:176
related: [dispatch-model-overrides-agent-frontmatter, agent-effort-policy-inherit-by-default, model-mapping-2layer-override]
created: '2026-10-02'
updated: '2026-10-02'
status: draft
---
## 개요

모델과 effort를 조정할 수 있는 지점이 일곱 곳으로 흩어져 있고, 모델에는 한 줄 매핑이 있으나 effort에는 그런 매핑 층이 없다.

## 결정 배경 (WHY)

- (근거: task:176 DONE.md 개선 후보) 모델·effort 최적화 측정을 하며 조정 지점을 전수 정리했다. 계속 튜닝하려면 이 분산이 비용이 된다.

## 결정 내용

조정 지점 일곱 곳:

1. 레벨과 모델의 매핑(`setting.json`의 `models`)
2. 에이전트 정의 frontmatter
3. 설계 주체(worktree 세션) 기동 설정(`launcher.builderEffort`, `launcher.builderModelLevel`)
4. 파일럿 SKILL.md의 디스패치 지시
5. 에이전트 레지스트리 문서 `agents.md`
6. opst 변형 토큰(`design=`, `impl=`)
7. `opal-agent` CLI

- 모델은 `models` 매핑 한 줄로 바꾼다. effort는 에이전트 frontmatter(16개)와 `builderEffort`에 흩어져 있어, 에이전트별 effort를 재배포 없이 조정하는 설정 층이 없다.
- `launcher._help`와 `setting.default.json`에는 `builderEffort`·`builderModelLevel`이 문서화되어 있지 않고 launcher README에만 사용법이 있다 (근거: task:176 DONE.md).
- 설계 주체의 모델 레벨은 `launcher.builderModelLevel.<에이전트|provider>`(`light|standard|advanced`)로 고른다. 미설정은 `standard`이며 에이전트 키가 provider 키를 이긴다 (근거: task:176 PLAN 결정 "builder 모델 레벨 키").

## 영향 범위

- `opal/tools/worktree-launcher/worktree_launcher/settings.py`, `opal/tools/worktree-launcher/README.md`, `opal/core/references/harness/worktree.md`

## 관련 페이지

- [[dispatch-model-overrides-agent-frontmatter]]
- [[agent-effort-policy-inherit-by-default]]
- [[model-mapping-2layer-override]]
