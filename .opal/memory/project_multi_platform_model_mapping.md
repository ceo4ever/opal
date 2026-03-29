---
name: 멀티 플랫폼 모델 매핑 필요
description: 오케스트레이터 워커 디스패치 시 model override가 Claude 전용(haiku/opus/sonnet) — Gemini, OpenAI 등 플랫폼별 모델 매핑 표준화 필요
type: task
---

현재 모든 오케스트레이터(otp-dev, otp-dev-short 등)의 워커 디스패치 model override가 Claude 전용이다.

- dtp-analysis: haiku
- dtp-plan: opus
- dtp-test-scenario: haiku
- dtp-execute: sonnet

**Why:** OPAL은 멀티 플랫폼 프레임워크(Claude Code, Cursor, Gemini, OpenAI)인데, 모델 정의가 Claude만 커버함.

**How to apply:** 캡틴이 일괄 정리 예정. 플랫폼별 모델 레벨 매핑 (예: opus=고성능, haiku=경량 → 각 플랫폼의 해당 레벨 모델로 매핑) 표준을 정의하고, 모든 오케스트레이터에 적용.
