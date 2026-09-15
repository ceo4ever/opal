---
module: track-escalation
role: Short profile에서 Full profile 전환 제안 규칙 SSOT
load: `//opds`의 PLAN 완료 직후 강업 제안 판정
상속: 하향 강등 제안 기준은 `opal/skills/opal-pilot-dev/references/track-routing.md`
---

# 트랙 승격 — opds→opd 강업 제안

> 사용자가 선택한 트랙을 기본적으로 수행한다. 강업은 Short 경로로 실행 계획을 완성할 수 없는 미결정 사항이 발견될 때만 제안한다.

## 1. 최우선 규칙

[MUST] 사용자가 `opds`를 선택했으면 Short profile을 기본 유지한다.

[MUST] 강업은 자동 전환하지 않는다. PM은 근거와 함께 사용자에게 비차단 제안만 한다.

[MUST] 파일 수·변경량·모듈 수·예상 소요 시간은 트랙 전환의 판정 기준으로 사용하지 않는다.

## 2. 판정 시점

[MUST] `opds`의 `PLAN.md` 완료 직후, `EXECUTE` 진입 전에 1회 판정한다.

[MUST] PLAN 작성 전에는 강업 조건을 판정하거나 Full profile 전환을 제안하지 않는다.

## 3. 강업 제안 조건

다음 질문의 답이 **예**이면 `opd` 전환을 제안한다.

> Short의 실행 계획을 만들기 위해 외부 영향이 있는 동작·계약·구조 결정을 새로 해야 하는가?

해당하는 미결정은 다음을 포함한다.

- 요구사항·수용 기준의 해석이 아직 닫히지 않음
- 사용자·API·이벤트의 동작 또는 정책을 새로 정해야 함
- 아키텍처·기술·데이터 구조 선택이 남아 있음
- 기존 패턴만으로 계획을 완성할 수 없어 임의 가정이 필요함

구현 세부(함수 분해·변수명·파일 내 위치)만 남은 경우는 강업 사유가 아니다.

판단 불능이면 강업을 제안하는 쪽으로 보수적으로 처리하되, 사용자가 유지하면 가능한 범위에서 `opds`를 계속 수행한다. 핵심 결정 없이는 실행 자체가 불가능하면 blocker로 보고한다.

## 4. 제안 후 처리

[MUST] 제안은 태스크당 1회만 한다.

- 사용자가 수락하면 TASK·PLAN 산출물과 현재 **effective mode**를 인계해 `opd --interactive|--semi-agentic|--agentic` 중 판정값에 대응하는 명시 플래그로 ANALYSIS 이후 경로로 전환한다. 이 전달은 mode 변경이 아니며 파이프라인 강제 재초기화를 금지한다.
- 사용자가 거절하면 `opds`를 계속 수행한다.
- PM은 사용자 응답 없이 트랙을 바꾸지 않는다.

## 5. 강등 규칙과의 관계

[MUST] `opd→opds` 강등 제안은 `opal/skills/opal-pilot-dev/references/track-routing.md`가 소유한다.

[MUST] `opds`에서 강업 제안 후 `opd`로 전환한 동일 태스크에 대해 강등 판정을 다시 수행하지 않는다.
