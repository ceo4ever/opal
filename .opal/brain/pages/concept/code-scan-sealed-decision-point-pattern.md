---
type: concept
title: 판정 지점 단일 봉인 패턴 — resolveShards로 3번째 적용
tags:
- code-scan
- architecture
- pattern
- task-082
sources:
- task:082
related:
- code-scan-manifest-sharding-design
- code-scan-tool
created: '2026-08-03'
updated: '2026-08-03'
status: draft
---
## 개요

code-scan에서 조회·기록·검증 여러 경로가 공유해야 하는 판정 로직(무엇을 어디로 보낼지, 무엇이 범위 안인지)을 함수 하나에만 두고 나머지 소비 지점은 전부 그 함수를 호출하게 하는 설계가 이번 태스크로 세 번째 반복 적용됐다.

## 결정 배경 (WHY)

이 판정을 소비 지점마다 각자 다시 계산하게 두면, 다급한 변경에서 소비 지점 하나가 판정 로직을 인라인으로 복제하려는 유혹이 생기고 그 순간부터 판정 기준이 갈라질 위험이 생긴다(근거: task:082 PLAN §9 R-9). 태스크 082는 이 위험을 "샤드 로딩·`byKey` 합집합·중복 판정이 이 함수 밖에 존재하지 않는다"는 요건으로 명문화했다(근거: task:082 DONE.md §3).

## 결정 내용

이번 태스크에서 신설한 샤드 해석 판정(`resolveShards`, `opal/tools/code-scan/code-scan.js:1002`)은, 같은 도구에서 이전 태스크가 헤더 소스 판정·스코프 소속 판정을 각각 함수 하나에 봉인했던 선례를 그대로 따른 세 번째 사례다(근거: task:082 DONE.md §3 "태스크 080이 resolveHeaderSource·isInScope를 각 1곳에 봉인한 선례를 따랐다"). 조회·기록·검증의 소비 지점 네 곳이 전부 이 하나의 판정 함수를 거친다.

이 판정 함수가 되돌리는 "해당 없음"(null) 응답은 그저 예외 처리가 아니라, 신규 기능을 켜지 않은 기존 자산이 오늘과 완전히 같게 동작한다는 하위호환 보증 자체를 구조적으로 만든다 — 그 조건 중 하나가 해석 모드가 켜져 있지 않은 경우다(근거: task:082 DONE.md §3 "`null` 반환 4조건 = 옵트인의 구조적 보증").

## 영향 범위

동일 도구 안에서 앞으로 판정 로직을 추가할 때 재사용할 수 있는 설계 관례다. 판정 함수 봉인이 깨졌는지는 해당 판정의 로딩·병합 로직이 그 함수 밖에 존재하지 않는지 코드 검색으로 확인하는 방식으로 점검됐다(근거: task:082 PLAN §9 R-9, §5.1 F-001).

## 관련 페이지

- [[code-scan-manifest-sharding-design]]
- [[code-header-dual-source-inheritance]]
- [[code-scan-tool]]
