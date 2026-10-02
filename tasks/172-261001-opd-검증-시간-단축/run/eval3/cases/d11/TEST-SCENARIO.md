<!--
원본: 태스크 167(opd-테스트-시나리오-작성-기준-개선), 설계 게이트 i2 (verdict=fail, rewrite_target=plan)
인용 gaps 원문: "decision_clarity-1: evaluator 미디스패치 회차(coverage exit 16/17)의 record 처리 미정"
-->
---
template: sdlc-v2
---
# TEST-SCENARIO: 테스트 시나리오 작성 기준 개선(합성 축소판)

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: scenario-coverage-check가 exit 16을 반환하도록 구성한 태스크 폴더를 준비한다.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1 | coverage exit 16 회차 | design-gate record 시도 | PM이 record를 생략하거나 빈 결과로 기록한다(정확한 분기 기준 미정) | unit | 구현 후 |
