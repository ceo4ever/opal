---
type: concept
title: 판정 지점 단일 봉인 패턴 — 080→082→083 3연속 적용
tags:
- code-scan
- architecture
- pattern
- task-082
- task-083
sources:
- task:082
- task:083
related:
- code-scan-manifest-sharding-design
- code-header-dual-source-inheritance
- code-scan-tool
- shard-policy-block-vs-nonblock-fallback-criterion
- code-scan-gate-deadlock-init-placement
created: '2026-08-03'
updated: '2026-08-04'
status: draft
---
## 개요

code-scan에서 조회·기록·검증 여러 경로가 공유해야 하는 판정 로직(무엇을 어디로 보낼지, 무엇이 범위 안인지, 어떤 정책값을 적용할지)을 함수 하나에만 두고 나머지 소비 지점은 전부 그 함수를 호출하게 하는 설계가 세 태스크에 걸쳐 연속 적용됐다 — 080의 헤더 소스 판정·스코프 소속 판정, 082의 샤드 해석 판정, 083의 샤드 정책 판정이다.

## 결정 배경 (WHY)

이 판정을 소비 지점마다 각자 다시 계산하게 두면, 다급한 변경에서 소비 지점 하나가 판정 로직을 인라인으로 복제하려는 유혹이 생기고 그 순간부터 판정 기준이 갈라질 위험이 생긴다(근거: task:082 PLAN §9 R-9). 083도 같은 위험을 정책 값(바이트 상한·파일 수 하한)의 3단 우선순위(`{프로젝트}/.opal/code-scan.json` > `~/.opal/setting.json` > 코드 상수)가 지점별로 갈릴 수 있다는 P0 리스크로 명문화했다(근거: task:083 PLAN §리스크 가설 H-12 "정책 값을 읽는 지점이 2곳 이상으로 늘면 3단 우선순위가 지점별로 갈린다").

## 결정 내용

- **1번째·2번째 적용(080)**: `resolveHeaderSource`·`isInScope`를 각 1곳에 봉인했다(근거: task:082 DONE.md §3).
- **3번째 적용(082)**: 신설한 샤드 해석 판정(`resolveShards`, `opal/tools/code-scan/code-scan.js:1002`)이 조회·기록·검증 소비 지점 네 곳을 하나로 모았다(근거: task:082 DONE.md §3).
- **4번째 적용(083)**: 신설한 정책 판정(`resolveShardPolicy`, PLAN §3.1.2 (E))이 `validate`·`scaffold`·`split` 3개 소비 명령의 바이트 상한·파일 수 하한·조각 목표(`targetBytes`) 계산을 전부 이 함수 하나로 모았다. `resolveShardPolicy` 본문은 프로젝트값 → 전역값(`loadGlobalSetting`) → 코드 상수(`DEFAULT_SHARD_POLICY`) 순으로 **키 단위 루프**를 돌며, 이 함수 밖에서는 `DEFAULT_SHARD_POLICY`·`loadGlobalSetting`을 참조하지 않는다는 것이 명문 제약이다(근거: task:083 PLAN §3.1.2 (E) "[MUST] 이 함수 밖에서 DEFAULT_SHARD_POLICY / loadGlobalSetting을 참조하지 않는다").
- 이 판정 함수가 되돌리는 "해당 없음"(null) 응답·기본값 폴백은 그저 예외 처리가 아니라, 신규 기능을 켜지 않은 기존 자산이 오늘과 완전히 같게 동작한다는 하위호환 보증 자체를 구조적으로 만든다(근거: task:082 DONE.md §3 "`null` 반환 4조건 = 옵트인의 구조적 보증").

## 영향 범위

동일 도구 안에서 앞으로 판정 로직을 추가할 때 재사용할 수 있는 설계 관례다. 판정 함수 봉인이 깨졌는지는 해당 판정의 로딩·병합 로직이 그 함수 밖에 존재하지 않는지 코드 검색으로 점검한다 — 082는 이를 `tests/test-shard.js:543`의 정적 grep 검사로 실행했고(근거: task:082 PLAN §9 R-9, §5.1 F-001), 083도 `DEFAULT_SHARD_POLICY` 식별자가 상수 선언 1줄 + `resolveShardPolicy` 본문 밖에 0회 등장하는지, `loadGlobalSetting(` 호출이 소스에 정확히 1곳뿐인지를 같은 방식(`test-shard-policy.js`, TS-007·TS-008)으로 재점검했다(근거: task:083 PLAN §3.1.2 (E) "봉인 정적 검사(H-12)").

## 관련 페이지

- [[code-scan-manifest-sharding-design]]
- [[code-header-dual-source-inheritance]]
- [[code-scan-tool]]
- [[shard-policy-block-vs-nonblock-fallback-criterion]]
- [[code-scan-gate-deadlock-init-placement]]
