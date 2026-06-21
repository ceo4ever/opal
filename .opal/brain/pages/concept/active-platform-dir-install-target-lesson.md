---
type: concept
title: 활성 Claude 플랫폼 디렉토리가 ~/.claude 기본이 아닐 수 있다 — install 타겟 정합 교훈 (032 P2)
tags:
- install
- deploy
- platform
- dispatch
- lesson-learned
sources:
- task:032
related:
- adapter-body-model-level-substitution
- opal-adapter-platform-isolation
created: '2026-06-21'
updated: '2026-06-21'
status: active
---
## 개념 요약

활성 Claude 플랫폼 디렉토리가 항상 기본값 `~/.claude`인 것은 아니다(이 계정은 `~/.claude_platform_mkt`). install이 활성 디렉토리를 타겟하지 못하면, 활성 env에는 변환되지 않은 raw 에이전트(레벨명 그대로)가 남아 sub-dispatch 실패를 유발한다.

## 배경·문제 (WHY)

032 세션 중 PLAN 워커 디스패치가 실패하며 발견됐다(P2). 원인은 활성 플랫폼 디렉토리(`~/.claude_platform_mkt/agents/`)가 변환되지 않은 raw 에이전트를 보유하고 있던 것. install-mac.sh는 `~/.claude/agents`를 하드코딩 타겟으로 배포하므로, 활성 디렉토리가 다른 경로면 배포가 그곳에 닿지 않는다. 어댑터 변환 로직이 아무리 정확해도, 배포 타겟이 활성 env와 어긋나면 변환 효과가 런타임에 나타나지 않는다.

## 결정 내용 (HOW)

### 교훈: 변환 정확성과 배포 타겟 정합은 별개 축이다

- 어댑터 본문/frontmatter 변환이 GREEN이어도, **활성 플랫폼 디렉토리에 배포가 닿았는지**는 독립적으로 확인해야 한다.
- 디스패치 실패(특히 model enum 위반)를 만나면, 소스/어댑터를 의심하기 전에 **활성 env의 배포본 실제 내용을 직접 확인**한다(raw 레벨명 잔존 여부).
- 032에서는 캡틴이 활성 디렉토리로 재배포하여 frontmatter 비대칭은 즉시 해소됐다. 본문 변환은 [[adapter-body-model-level-substitution]]으로 별도 수정 + 재배포가 필요하다(소스만 변경 시 미발효).

### 비차단 후속 후보

install-mac.sh가 `~/.claude/agents`만 하드코딩 타겟하는 한계는, 활성 플랫폼 디렉토리(`~/.claude_platform_mkt` 등) 정합을 별도 태스크로 근본 해소할 후보다(P2 근본 해소, 비차단).

## 영향·관계

- 배포 검증 규율: "어댑터 변환 GREEN"과 "활성 env 배포본 변환됨"을 분리 검증한다.
- [[adapter-body-model-level-substitution]] — 본 변환의 발효는 활성 디렉토리 재배포에 의존한다.
- [[opal-adapter-platform-isolation]] — 어댑터 격리 원칙의 운영 측 보완(타겟 정합).

## 근거 출처

task:032 — DONE.md §처리 메모 P2, §후속 2(install 배포 타겟 정합 비차단 후보).
