---
type: concept
title: 모델 매핑 미설정 셀 오류 정책 (폴백 없음 · "default" 폐기)
tags:
  - model
  - mapping
  - error
  - policy
  - setting
sources:
  - task:046
related:
  - model-mapping-2layer-override
  - model-mapping-latest-tracking
created: "2026-06-28"
updated: "2026-06-28"
status: active
---

## 개요

전역(`~/.opal/setting.json`)과 프로젝트(`setting.local.json`) 어느 쪽에도 해당 플랫폼·레벨 셀이 존재하지 않으면 OPAL은 디스패치를 **오류로 중단**한다. 표 폴백(`opal-model-mapping.md` §2) 및 `"default"` 값은 더 이상 유효하지 않다.

## 결정 배경 (WHY)

초기 설계(v1)는 ①프로젝트 setting → ②유저 setting → ③`opal-model-mapping.md` §2 표 순으로 3단 폴백을 두었다. v2에서는 inert `"default"` 스캐폴드를 도입했다. 그러나 표 폴백은 "setting을 쓰면 표는 버려도 된다"는 사용자 직관과 충돌하고, `"default"` 값은 의도인지 실수인지 구분이 불가했다(근거: task:046 DONE.md §5 설계 3차 진화). 최종 v3에서 명시적 오류 정책으로 전환했다.

## 결정 내용

- **셀 미설정**: 전역·로컬 어느 레이어에도 해당 `models[provider][level]` 셀이 없으면 → 오류(디스패치 중단).
- **`"default"` 값**: 무효 — 실모델명으로 교체 필요. 기존 `~/.opal/setting.json`에 `"default"` 잔재가 있으면 `rm ~/.opal/setting.json` 후 재설치로 concrete 시드 획득.
- **폴백 순서**: 전역 setting.json → 프로젝트 setting.local.json (셀 단위 덮어쓰기, 로컬 우선). 이 두 레이어를 모두 소진한 뒤에도 셀이 없으면 오류.

## 운영 영향

- 새 설치: `setting.default.json`에 실모델명이 있으므로 시드 후 즉시 동작.
- 과도기 `"default"` 사용자: 재설치 필요(안내: `opal/core/references/opal-model-mapping.md §5.3`).
- `invest-stock` 프로젝트처럼 `setting.local.json`에 `"bootstrap":"off"` + `"default"` models가 있으면 재배포 후 오류 발생 가능 — 명시적 실모델로 교체 또는 키 제거 필요.

## 관련 페이지

- [[model-mapping-2layer-override]]
- [[model-mapping-latest-tracking]]
