<!--
원본: 태스크 168(opd-opd2-프레임워크-통합), 설계 게이트 i2 (verdict=fail, rewrite_target=plan)
인용 gaps 원문: "decision_clarity/row mapping: The PLAN does not say which state.json row each lifecycle.py
transition marks, who marks the user_confirm rows in semi-agentic and agentic modes, or who marks
close.done_md through close.final."
이 Work item은 원본 i2 PLAN의 미결정을 의도적으로 재현한다 — lifecycle.py 전이와 state.json 행의
대응 관계, user_confirm 행 담당자가 "구현하면서 정한다" 식으로 열려 있다.
-->
---
template: sdlc-v2
---
# PLAN: opd2 프레임워크 통합(합성 축소판)

## Approach

opd2 lifecycle.py를 state-tool mark 호출로 연결한다.

## Findings

### 직접 변경

- `opal/skills/opal-pilot-dev2/lifecycle.py`(합성 참조) — 단계 전이 시 state-tool mark 호출 추가.

### 회귀 확인

- 기존 opal-pilot-dev(v1) 경로는 영향 없음(별도 스킬).

### 문서 갱신

- 없음(축소판).

### 미확인 가정

- semi-agentic·agentic 모드별 user_confirm 담당자 차이를 아직 조사하지 않았다.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| D-1. lifecycle.py 전이와 state.json 행 대응 | 각 전이가 어떤 행을 마크하는지는 구현 중 lifecycle.py 코드를 보면서 정한다. user_confirm 행도 semi-agentic은 사용자가, agentic은 PM이 마크하거나 혹은 자동 승인될 수도 있다 — 모드별 정확한 담당자는 아직 정하지 않았다. | 모드별 세부 동작 차이를 아직 충분히 조사하지 못했다. |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. lifecycle mark 연동 | opal-task-agent | `opal/skills/opal-pilot-dev2/lifecycle.py` | 각 단계 전이에서 state-tool mark를 호출한다. 어떤 행을 마크할지, user_confirm 행을 누가 마크할지는 구현하면서 정한다 | 없음 | P1 | AC-1, AC-2 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. 행 대응·담당자 미정 | state.json 행 전이 일관성 | 구현자마다 다르게 마크하면 모드별 동작이 어긋날 수 있다 | 없음(아직 미해결) |

## Release and recovery

별도 배포 절차 없음(축소판).
