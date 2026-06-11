---
type: concept
title: wtm-agent OPAL 표준화 + cmux-tool 신설
tags:
- tool
- agent
- wtm
- cmux
- task
sources:
- task:002
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

`opal-wtm-agent`를 OPAL 표준 워커 구조로 재편하고, cmux browser를 Phase 2 폴백으로 추가하는 `cmux-tool`(신규 도구)을 신설했다. web-to-markdown 스킬은 WebFetch→cmux→Playwright 3단 폴백 체인으로 재구성되었다.

## 배경·문제 (WHY)

기존 wtm-agent가 OPAL 표준 워커 구조를 따르지 않고 Crawl4AI 의존성으로 부정합이 있었다. 사용자 cmux 브라우저 surface를 재사용하면 인증/세션이 필요한 페이지도 접근 가능하다는 요구가 있었다.

## 결정 내용 (HOW)

- 신규 도구 `cmux-tool/run.sh` — A/B/C 3모드 + 환경 감지 + JSON 8필드 출력.
- 신규 에이전트 `opal-wtm-agent/AGENT.md` — 표준 7단계 디스패치 구조, 안전 가드 2차 담당.
- 폴백 체인: Phase 1(WebFetch) → Phase 2(cmux) → Phase 3(Playwright).
- 사용자 surface 3모드(`--surface`): browser/screenshot/session.

## 영향·관계

- `skills/web-to-markdown/SKILL.md` v1.9, `opal/core/references/agents.md` v1.4 갱신.
- [[opal-architecture]] 에이전트 목록에 opal-wtm-agent 추가.

## 근거 출처

`sources: task:002` — DONE.md §2~§3 참조.
