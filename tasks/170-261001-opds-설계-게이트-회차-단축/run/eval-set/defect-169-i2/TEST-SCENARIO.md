<!--
원본: 태스크 169(opds-워크트리-CLOSE-지식-반영), 설계 게이트 i2 (verdict=fail, rewrite_target=plan)
인용 gaps 원문: "decision_clarity-1: op-brain-ingest 워커가 쓰는 page 집합을 DONE.md 선언 집합 D와 어떻게 맞출지
결정이 없다. ... 선택지는 세 가지다. (a) 워커가 D에 선언된 경로만 쓴다. (b) 워커 결과로 DONE 선언을 갱신한다.
(c) PM이 워커 결과를 선언에 역반영한다. 이 선택이 구현자에게 남아 있다."
-->
---
template: sdlc-v2
---
# TEST-SCENARIO: 워크트리 CLOSE 지식 반영(합성 축소판)

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: DONE.md에 page 집합 D가 선언된 임시 워크트리를 준비하고 op-brain-ingest 워커를 디스패치한다.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1 | 워커가 D 밖의 page를 추가로 쓰는 경우 | op-brain-ingest 워커 디스패치 후 finalize | D-1 (a)/(b)/(c) 중 하나로 정합이 맞춰진다(구체적 방법 미정) | unit | 구현 후 |
