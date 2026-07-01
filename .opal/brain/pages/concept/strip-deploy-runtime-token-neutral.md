---
type: concept
title: strip_deploy_md 런타임 토큰 영향 0 — 변경이력 trim 측정 정정 교훈
tags:
- deploy-pipeline
- token
- install
- measurement
- lesson
sources:
- task:050
related:
- agent-md-digest-pattern
- bootstrapper-marker-ssot-single-point
- deploy-artifact-verification-lesson
created: '2026-06-30'
updated: '2026-06-30'
status: active
---

## 개요

OPAL 배포 파이프라인의 `strip_deploy_md` 함수는 소스 문서의 `## 변경이력` 섹션(한글 헤딩 한정)을 배포 시점에 제거한다. 따라서 소스 파일의 변경이력 trim은 런타임에 로드되는 배포본 토큰에 영향을 주지 않는 순수 소스 위생 작업이다. 이를 "런타임 경감 수단"으로 오판하는 것을 방지하기 위한 교훈 페이지다.

## 결정 배경 (WHY)

task:050 TASK.md는 AGENT.md 소스 493줄 전체가 매 세션 로드된다고 전제했다. 직접 분석(`wc -l ~/.opal/AGENT.md`) 결과 배포된 런타임 파일은 455줄임이 확인되었다. 차이의 원인은 `scripts/install-mac.sh:227` `strip_deploy_md`가 배포 시점에 `## 변경이력` 섹션(38줄)을 제거하기 때문이다 (근거: task:050 PLAN §1.1 측정 정정, `scripts/install-mac.sh:227`).

이 정정의 실질적 의미는 다음과 같다. 변경이력 trim(R-4)은 런타임 토큰 영향이 0이며, 실제 비서 세션 토큰 경감은 PM 섹션 이관(R-2·R-3, 약 250줄)에서만 발생한다. lean core 목표(소스 약 205줄)는 "소스 493줄"이 아닌 "런타임 body 455줄 - 이관 250줄 ≈ 205줄"로 재해석해야 정합하다 (근거: task:050 PLAN §1.1 측정 정정).

## 결정 내용

소스 문서의 변경이력을 trim할 때 "이것이 런타임 토큰을 줄인다"고 보고하거나 목표치에 반영해서는 안 된다. 소스 위생과 런타임 경감은 별개의 축이다.

또한 `strip_deploy_md`는 `## 변경이력`(한글) 헤딩만 제거한다. `PRINCIPLES.md`처럼 `## Changelog`(영문) 헤딩을 사용하는 파일은 strip되지 않는다. 파일별로 실제 strip 여부를 확인하지 않고 "배포 시 자동 strip됨"으로 일반화하면 오판이 생긴다.

런타임 파일 크기를 추정할 때는 반드시 `wc -l ~/.opal/<파일명>` 또는 동등한 직접 측정을 수행하고, 소스 줄 수로 런타임을 대리하지 않는다.

## 영향 범위

이 교훈은 AGENT.md 다이제스트뿐 아니라, 향후 런타임 토큰 예산을 추산하거나 문서 경량화 효과를 측정하는 모든 작업에 적용된다. 배포 파이프라인 변환(strip·injection)이 있는 파일은 항상 배포본 기준으로 측정한다.

## 관련 페이지

- [[agent-md-digest-pattern]]
- [[bootstrapper-marker-ssot-single-point]]
- [[deploy-artifact-verification-lesson]]
