---
type: concept
title: TEST 병렬 그룹은 단일 에이전트 안에서만
tags:
- test
- parallel
sources:
- task:172
related: [test-two-tier-system, real-invocation-scenario-limit]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

TEST 시나리오의 독립 자동 시나리오를 한 에이전트 안에서 동시에 실행해 벽시계 시간을 줄이는 절차다. 여러 에이전트를 동시에 띄우는 병렬은 채택하지 않았다.

## 결정 배경 (WHY)

(근거: task:172 PARALLEL-PROBE 실측) 한 에이전트 안에서 독립 명령의 동시 실행은 가능했다(순차 8.05초 → 병렬 2.01초). 여러 프로세스의 동시 `scenario-mark`는 5라운드 8프로세스에서 6건이 유실됐다. 파일 잠금이 없고, 에이전트마다 자동 구간을 열면 소요 시간이 합산으로 부풀기 때문이다.

## 결정 내용

- 병렬 대상은 작성자가 시나리오 Setup에 `병렬 그룹:`으로 선언한 것만이다. 에이전트가 추정하지 않는다. 스키마에 필드를 추가하지 않는다.
- 한 번의 Bash에서 그룹 명령을 띄우고 모두 기다린다. 시간은 그룹 전체를 자동 구간 하나로 기록하고, 판정 기록은 그룹 종료 뒤 순차로 한다 (`opal/core/references/harness/test-cycle.md:18`).
- 이번 태스크의 S-1~S-11이 이 절차로 실행되어 자동 구간이 하나(98.9초)였다.
- 후속 과제: `scenario-mark` 잠금 도입과 자동 시간의 합집합 계산이 선행되어야 다중 에이전트 병렬이 가능하다.

## 관련 페이지

- [[test-two-tier-system]]
- [[real-invocation-scenario-limit]]
