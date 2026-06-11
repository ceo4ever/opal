---
type: concept
title: OPAL 모델 매핑 최신화 + 최신 추종 전략
tags:
- model
- mapping
- gemini
- codex
- task
sources:
- task:011
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

OPAL 플랫폼별 모델 매핑(`opal-model-mapping.md`)을 2026-06 최신 라인업으로 갱신하고, Claude/Gemini에 "최신 추종 부동 별칭" 전략을 도입했다. 4개 동기화 지점(opal-model-mapping.md, install-mac.sh, agents.md, windows.ps1)을 모두 정합화했다.

## 배경·문제 (WHY)

TASK 배경 분석이 모델 ID 3곳 불일치를 식별했다. 또한 Gemini가 `-latest` 부동 별칭을 지원하게 되어 stale 자동 해소 전략 도입이 가능해졌다.

## 결정 내용 (HOW)

- 부동 별칭 자동 추종: Claude(`haiku/sonnet/opus`) + Gemini standard/advanced(`gemini-flash-latest`/`gemini-pro-latest`).
- 핀 + 분기점검: Gemini light(`gemini-3.1-flash-lite`)·Codex·OpenAI는 `-latest` 미존재 → §5 "분기마다 공식 docs 점검" 운영 규칙 추가.
- OpenAI 컬럼: "미배선 죽은 컬럼"으로 판정 → 참조전용 각주 추가.
- windows.ps1(4번째 동기화 지점)을 TASK 범위 외에서 신규 발견하여 포함.

## 영향·관계

- 변경 파일: `opal/core/references/opal-model-mapping.md` v1.3, `scripts/install-mac.sh` v2.7, `opal/core/references/agents.md` v1.5, `scripts/install/windows.ps1` v1.9.0.
- [[codex-platform-integration]] 에서 도입된 Codex 모델 매핑 갱신.

## 근거 출처

`sources: task:011` — DONE.md §최종 확정 매핑 참조.
