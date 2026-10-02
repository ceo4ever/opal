<!--
원본: 태스크 162(opd-TEST-단계-소요시간-단축), 설계 게이트 i1 (verdict=fail, rewrite_target=plan)
인용 gaps 원문: "W-1 CLI 입력·출력과 저장 구조, 중복·누락 종료 처리, 상한 초과 상태 전이·재개 방법 미정"
-->
---
template: sdlc-v2
---
# TEST-SCENARIO: TEST 단계 소요시간 측정 CLI 추가(합성 축소판)

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: 임시 폴더에 측정 CLI를 설치하고 실행한다.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1 | 신규 측정 세션 | `duration_cli start` 후 `duration_cli stop` | 소요시간(분)이 산출된다 | unit(CLI) | 구현 후 |
| S-2 | AC-2 | `stop` 없이 다시 `start` 호출 | `duration_cli start` 두 번 연속 | 중복 호출이 안전하게 처리된다(구체적 동작 미정) | unit(CLI) | 구현 후 |
