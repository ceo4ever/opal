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
updated: '2026-09-19'
status: active
---
## 개념 요약

OPAL의 ChatGPT 로그인 기반 Codex 모델 매핑을 OpenAI의 2026-09 공식 권장 모델에 맞춰 GPT-5.6 계열로 전환했다. `setting.default.json`이 실모델 SSOT이며, 배포 어댑터와 사용자 설정 마이그레이션이 같은 값을 사용한다.

## 현재 결정

| OPAL 레벨 | Codex 모델 | 역할 |
|---|---|---|
| `light` | `gpt-5.6-luna` | 빠르고 저렴한 검색·분류·보조 워커 |
| `standard` | `gpt-5.6-terra` | 일반 구현·분석 |
| `advanced` | `gpt-5.6-sol` | 복잡한 계획·설계·고난도 구현 |

GPT-6 Astra는 비용과 계정별 가용성이 다른 최상위 선택지이므로 기본 `advanced`에 넣지 않고 프로젝트의 `setting.local.json`에서 선택적으로 오버라이드한다.

## 전환 근거

- ChatGPT 로그인 기반 Codex에서 `gpt-5.4-mini`와 `gpt-5.4`는 2026-08-31 퇴역했다.
- `gpt-5.5`는 2026-10-14 퇴역 예정이다.
- OpenAI의 직접 교체 지침은 각각 `gpt-5.6-luna`, `gpt-5.6-terra`, `gpt-5.6-sol`이다.
- OpenAI API 참조용 `models.openai`는 Codex 퇴역 정책의 적용 대상이 아니므로 이번 변경에서 유지한다.

공식 근거: https://developers.openai.com/codex/models

## reasoning effort 정합

GPT-5.6의 지원 값역에 맞춰 Codex 어댑터 변환을 `minimal`→`none`, `max`→`max`로 변경했다. 기존 `max`→`xhigh` 축약은 제거했다.

## 기존 설치 마이그레이션

설치기는 기존 `setting.json`의 Codex 셀이 직전 OPAL 기본값과 정확히 일치할 때만 새 기본값으로 셀 단위 승격한다. 사용자 지정 모델과 프로젝트 `setting.local.json`은 수정하지 않는다.

## 영향·관계

- 모델 SSOT: `opal/core/setting.default.json`
- 플랫폼 어댑터 SSOT: `scripts/install-mac.sh`의 `OPAL_ADAPTER_FIELD_SPEC`
- Windows 미러: `scripts/install/windows.ps1`
- 사용자 설정 결정: [[model-mapping-2layer-override]]
- 누락 셀 정책: [[model-mapping-missing-cell-error-policy]]
