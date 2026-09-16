---
module: track-routing
role: 트랙 전환 제안 규칙 SSOT
load: `//opd`의 ANALYSIS 완료 후 강등 제안 판정
상속: Short→Full 승격 제안 기준은 `opal/skills/opal-pilot-dev/references/track-escalation.md`가 소유한다
---

# 트랙 라우팅 — opd→opds 강등 제안

> 사용자가 선택한 트랙을 기본적으로 수행한다. 트랙 전환은 자동 변경이 아니라, 현재 트랙의 핵심 목적과 실제 작업 상태가 어긋날 때만 제안한다.

## 1. 최우선 규칙

[MUST] 사용자가 명시한 `opd` 또는 `opds` 선택을 다른 기준보다 우선한다.

[MUST] 강등·강업은 자동 전환하지 않는다. PM은 근거와 함께 사용자에게 비차단 `progress_report` 제안만 하고 현재 트랙을 계속한다.

[MUST] 파일 수·변경량·모듈 수·예상 소요 시간은 트랙 전환의 판정 기준으로 사용하지 않는다.

## 2. 결정 잠금 판정

트랙 적합성은 외부 영향이 있는 결정의 잔여 여부로 판정한다.

결정 범위는 다음 세 가지다.

1. 목표·수용 기준 — 무엇을 만족해야 하는가
2. 외부 동작·정책·계약 — 사용자·API·이벤트에 무엇이 보여야 하는가
3. 구조·기술 선택 — 어떤 모듈·계약·저장 구조를 사용할 것인가

구현 세부(함수 분해·변수명·파일 내 위치)는 `opds`의 PLAN에서 결정할 수 있다.

핵심 질문:

> 현재 단계 이후에 외부 영향이 있는 동작·계약·구조 결정을 새로 해야 하는가?

## 3. `opd`에서 강등 제안

[MUST] `opd`의 `ANALYSIS` 완료 직후, `PLAN` 진입 전에 1회 판정한다.

- 핵심 질문의 답이 **예**이면 `opd`를 계속 수행한다.
- 핵심 질문의 답이 **아니오**이면 `opds` 강등을 제안한다.
- 판단 불능이면 `opd`를 계속 수행한다(fail-safe).

강등 제안은 Full의 분석·설계 단계가 더 이상 새로운 결정을 만들 가능성이 낮고, Short 경로로 바꿔도 완료 조건·검증 계약이 손상되지 않는다는 근거를 포함한다. 제안은 `report_type=progress_report`, `transition_action=continue`로 취급하며 현 `opd` 트랙을 막지 않는다.

## 4. 제안 후 처리

[MUST] 제안은 태스크당 1회만 한다.

- 소유자가 다음 입력에서 전환을 명시하면 기존 TASK·ANALYSIS 산출물과 현재 **effective mode**를 인계해 `opds --interactive|--semi-agentic|--agentic` 중 판정값에 대응하는 명시 플래그로 PLAN에 진입한다. 이 전달은 mode 변경이 아니며 파이프라인 강제 재초기화를 금지한다.
- 소유자 입력이 없거나 유지 의사가 확인되면 현재 `opd` 트랙을 계속 수행한다.
- PM은 사용자 응답 없이 트랙을 바꾸지 않는다. 단, 현재 트랙 실행이 불가능한 경우에만 `decision_request` 또는 `blocked`로 전환하고 실행 불가 근거를 보고한다.

## 5. 승격 규칙과의 관계

[MUST] `opds→opd` 승격 제안은 `opal/skills/opal-pilot-dev/references/track-escalation.md`가 소유한다.

[MUST] 동일 태스크에서 강등 제안 후 강업 제안을 다시 수행하지 않는다.
