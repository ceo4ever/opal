<!--
원본: 태스크 168(opd-opd2-프레임워크-통합), 설계 게이트 i2 (verdict=fail, rewrite_target=plan)
인용 gaps 원문: "decision_clarity/row mapping: The PLAN does not say which state.json row each lifecycle.py
transition marks, who marks the user_confirm rows in semi-agentic and agentic modes, or who marks
close.done_md through close.final."
-->
---
template: sdlc-v2
---
# TEST-SCENARIO: opd2 프레임워크 통합(합성 축소판)

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: opd2 lifecycle.py가 동작하는 임시 태스크 폴더를 준비한다.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1 | PLAN 단계 전이 | lifecycle.py PLAN 완료 전이 실행 | state.json의 어떤 행이 마크되는지 확인(정확한 대응 미정) | unit | 구현 후 |
| S-2 | AC-2 | semi-agentic 모드 user_confirm 행 | lifecycle.py 실행 | 담당자(사용자/PM/자동)가 누구인지 확인(미정) | unit | 구현 후 |
