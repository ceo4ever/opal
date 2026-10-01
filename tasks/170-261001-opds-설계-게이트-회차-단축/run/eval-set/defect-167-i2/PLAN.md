<!--
원본: 태스크 167(opd-테스트-시나리오-작성-기준-개선), 설계 게이트 i2 (verdict=fail, rewrite_target=plan)
인용 gaps 원문: "decision_clarity-1: evaluator 미디스패치 회차(coverage exit 16/17)의 record 처리 미정"
이 Work item은 원본 i2 PLAN의 미결정을 의도적으로 재현한다 — coverage exit 16/17 회차의 record 처리가
"PM이 상황에 맞게 판단한다" 식으로 열린 채 남아 있다.
-->
---
template: sdlc-v2
---
# PLAN: 테스트 시나리오 작성 기준 개선(합성 축소판)

## Approach

scenario-coverage-check 결과에 따라 record 절차를 분기한다.

## Findings

### 직접 변경

- `opal/core/references/harness/design-gate.md`(합성 참조) — coverage exit 16/17 분기 서술 추가.

### 회귀 확인

- 기존 정상 coverage(exit 0) 경로는 영향 없음.

### 문서 갱신

- 없음(축소판).

### 미확인 가정

- exit 16과 17의 차이(완전 미디스패치 vs 부분 디스패치)가 record 처리에 어떤 영향을 주는지 아직 확인하지 않았다.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| D-1. evaluator 미디스패치 회차의 record 처리 | coverage가 exit 16/17을 반환하면 PM이 상황에 맞게 record를 생략하거나 빈 결과로 기록할 수 있다 — 구체적 분기 기준은 아직 정하지 않았다. | 두 exit 코드의 의미 차이를 아직 충분히 조사하지 못했다. |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. record 분기 반영 | opal-task-agent | `opal/core/references/harness/design-gate.md` | coverage exit 16/17 회차에서 PM이 record를 생략하거나 빈 결과로 기록하는 식으로 처리하도록 서술을 추가한다(정확한 기준은 구현 중 정리) | 없음 | P1 | AC-1 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. record 처리 기준 미정 | 설계 게이트 반복 상한 계산 일관성 | PM마다 다르게 처리하면 반복 횟수 집계가 어긋날 수 있다 | 없음(아직 미해결) |

## Release and recovery

별도 배포 절차 없음(문서 변경, 축소판).
