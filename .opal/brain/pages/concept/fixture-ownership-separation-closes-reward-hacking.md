---
type: concept
title: 픽스처 소유권을 구현자와 분리하면 reward hacking 표면이 닫힌다
tags:
- testing
- fixture-design
- reward-hacking
- task-105
sources:
- task:105
related:
- context-tag-suppresses-false-positive-without-removing-hit
- fixture-vs-real-blind-spot-lesson
created: '2026-09-03'
updated: '2026-09-03'
status: draft
---
## 개요

오탐·미탐을 검증해야 하는 기능은 픽스처(테스트 데이터) 설계 자체가 검증의 본질이다. 구현자가 자신의 검증용 픽스처까지 직접 만들면 "자기가 잡을 수 있는 패턴만 넣는" 편향이 구조적으로 발생한다. 픽스처 작성을 구현자와 분리된 주체에게 배정하면 이 표면이 닫힌다.

## 결정 배경 (WHY)

(근거: task:105 DONE.md §3.5) 위험 패턴 스캔 기능은 self-confirming 위험이 높다고 판정됐다. "무해 픽스처에서 위험 검출 0건"이라는 통과 기준은, 픽스처를 무해하게(즉 자기 구현이 통과하도록) 설계할수록 통과하기 쉬워지는 reward hacking 표면이다.

## 결정 내용

- 픽스처 작성 단계를 구현자와 다른 워커(별도 배정된 테스트 전담 에이전트)에게 분리 배정했다.
- 실측 결과, 분리 배정된 워커가 오탐 억제의 4개 분류 축(부정문·주석·픽스처 경로·산문 언급)을 **서로 겹치지 않게 강제 분리**하는 픽스처를 설계했다 — 예: 부정 토큰과 백틱이 모두 없는 픽스처(산문 축만 검증), 주석 기호로 시작하지 않는 라인으로만 구성된 픽스처(부정문 축만 검증). 이렇게 축을 분리하면 구현자가 규칙 하나로 여러 축을 뭉뚱그려 통과시키는 것이 불가능해진다.
- 픽스처가 저장되는 임시 디렉토리 접두어도 도구 이름을 반영한 고유 접두어로 잡아, 픽스처 루트 경로 자체가 다른 억제 규칙(예: `test/` 경로 억제)에 걸려 검증 대상이 무력화되는 경로를 선제 차단했다.
- **일반 원칙**: 오탐/미탐 억제 기능을 검증할 때는 (1) 픽스처 설계자를 구현자와 분리하고, (2) 픽스처가 판정 축을 서로 겹치지 않게 분리해서 커버하는지를 확인 기준으로 삼는다.

## 영향 범위

- `opal/tools/skill-registry/tests/test-scan-risk.js` — 분리 배정된 워커가 설계한 픽스처 11종
- 유사하게 오탐/미탐 검증이 핵심인 모든 정적 분석·필터링 기능 구현에 일반화 가능

## 관련 페이지

- [[context-tag-suppresses-false-positive-without-removing-hit]]
- [[fixture-vs-real-blind-spot-lesson]]
