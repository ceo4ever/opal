---
type: concept
title: 형식 버전 상수 동결 — 형식이 안 바뀌면 올리지 않는다
tags:
- code-scan
- versioning
- backward-compat
- task-082
sources:
- task:082
related:
- code-scan-manifest-sharding-design
- backward-compat-default-value-discipline
created: '2026-08-03'
updated: '2026-08-03'
status: draft
---
## 개요

매니페스트가 따르는 형식 버전을 나타내는 상수는, 그 형식 자체가 실제로 바뀌지 않는 한 값을 올리지 않는다는 규율이다.

## 결정 배경 (WHY)

이 버전 상수를 읽는 쪽 로직은 "이 값이 자신이 아는 값과 다르면 그 매니페스트 전체를 지원 불가로 차단한다"로 동작한다. 형식이 실제로는 바뀌지 않았는데 이 값만 올리면, 그 순간 기존에 만들어져 있던 모든 자산이 한꺼번에 지원 불가 판정을 받는다(근거: task:082 DONE.md §3 "`CODE_MAP_VERSION`은 1 고정. 상향하면 기존 전 자산이 `unsupported_version`으로 즉시 차단된다"). 이번 태스크는 매니페스트 안에 필드 하나(샤드 라벨 목록)를 더했을 뿐 매니페스트가 따르는 형식 자체를 바꾸지 않았으므로, 이 상수를 건드릴 이유가 없었다(근거: task:082 PLAN §9 R-8).

## 결정 내용

형식 버전 상수(`CODE_MAP_VERSION`, `opal/tools/code-scan/code-scan.js:59`)는 이번 태스크에서 값을 그대로 유지한다. 이 상수를 올리는 것은 "매니페스트가 따르는 형식 자체가 바뀌어 이전 자산과 더 이상 호환되지 않는다"는 선언과 같은 무게를 가지므로, 필드 추가처럼 기존 자산과 계속 호환되는 확장에는 쓰지 않는다.

## 영향 범위

버전 필드를 두고 하위호환을 판정하는 모든 형식(매니페스트·스키마·프로토콜)에 재사용 가능한 규율이다 — "필드를 늘리는 확장"과 "형식 자체를 바꾸는 변경"을 구분해서, 후자에만 버전 상향을 쓴다.

## 관련 페이지

- [[code-scan-manifest-sharding-design]]
- [[backward-compat-default-value-discipline]]
