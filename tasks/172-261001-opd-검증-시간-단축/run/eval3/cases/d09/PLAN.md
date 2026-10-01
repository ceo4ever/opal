<!--
원본: 태스크 169(opds-워크트리-CLOSE-지식-반영), 설계 게이트 i2 (verdict=fail, rewrite_target=plan)
인용 gaps 원문: "decision_clarity-1: op-brain-ingest 워커가 쓰는 page 집합을 DONE.md 선언 집합 D와 어떻게 맞출지
결정이 없다. ... 선택지는 세 가지다. (a) 워커가 D에 선언된 경로만 쓴다. (b) 워커 결과로 DONE 선언을 갱신한다.
(c) PM이 워커 결과를 선언에 역반영한다. 이 선택이 구현자에게 남아 있다."
이 Work item은 원본 i2 PLAN의 미결정을 의도적으로 재현한다 — (a)(b)(c) 세 선택지 중 하나로 좁히지 않고
구현자에게 남겨두는 형태를 그대로 담는다.
-->
---
template: sdlc-v2
---
# PLAN: 워크트리 CLOSE 지식 반영(합성 축소판)

## Approach

CLOSE 단계에서 op-brain-ingest 워커를 디스패치해 brain 페이지를 갱신한다.

## Findings

### 직접 변경

- `opal/skills/op-oppb-knowledge-finalize/SKILL.md`(합성 참조) — 워커 디스패치 안내 추가.

### 회귀 확인

- 기존 finalize의 ATTRIBUTION_COMMIT_BLOCKED 차단 로직은 영향 없음(변경 대상 아님).

### 문서 갱신

- 없음(축소판).

### 미확인 가정

- 워커가 실제로 어떤 page 경로를 쓸지는 DONE.md 선언과 항상 일치한다고 가정했으나 검증하지 않았다.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| D-1. 워커 page 집합과 DONE 선언 집합의 정합 | 워커가 DONE.md에 선언된 경로만 쓰거나(a), 워커 결과로 DONE 선언을 갱신하거나(b), PM이 워커 결과를 선언에 역반영(c)하는 세 가지 방법이 있다 — 어느 쪽을 쓸지는 구현자가 상황에 맞게 정한다. | 세 방법 모두 가능하지만 아직 하나로 좁히지 않았다. |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. 워커-선언 정합 처리 | opal-task-agent | `opal/skills/op-oppb-knowledge-finalize/SKILL.md` | op-brain-ingest 워커 디스패치 후 page 집합을 DONE.md 선언과 맞춘다. D-1의 (a)/(b)/(c) 중 적절한 방법을 적용한다(구체적 선택은 구현 중 결정) | 없음 | P1 | AC-1 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. 정합 방법 미정 | finalize의 ATTRIBUTION_COMMIT_BLOCKED 차단과 상호작용 | 워커가 선언 밖 page를 쓰면 귀속 커밋이 조용히 실패할 수 있다 | 없음(아직 미해결) |

## Release and recovery

별도 배포 절차 없음(축소판).
