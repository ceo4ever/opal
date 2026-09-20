---
template: sdlc-v2
---
# TASK: GC 검사 역량의 공통 스킬 분리

## Problem

보안 검사와 컨벤션 검사 절차가 `opal-pilot-gc` 수명주기 안에 결합되어 있다. 다른 파이프라인이 보안 검사만 필요해도 태스크 채번·상태·CLOSE까지 소유하는 Pilot 전체를 시작해야 한다. 검사 기준도 Pilot 참조 문서와 checker 에이전트 문서 양쪽에 나뉘어 있어, 어느 쪽이 절차 원본인지 불명확하고 한쪽만 갱신되는 표류가 발생한다. 두 검사 결과 형식이 서로 독립적이라 통합 보고가 문자열 결합 수준에 머물고, 검사 결측과 통과를 구조적으로 구분하지 못한다.

## Proposed outcome

보안 검사·컨벤션 검사·결과 통합이 각각 독립 호출 가능한 단계 스킬로 존재한다. `opal-pilot-gc`는 범위 확정과 상태·CLOSE만 소유하는 thin wrapper가 되고, 기존 SCAN→CHECK→REPORT→CLOSE 동작과 사용자 Gate는 그대로 유지된다. 두 검사가 같은 finding schema로 결과를 내고, 통합 보고가 severity·confidence·집행 수준을 분리해 차단 여부를 계산한다. 검사기가 실행되지 못한 상태는 통과가 아니라 별도 판정으로 보고된다.

## Affected users and systems

- `opal-pilot-gc` 사용자 — 기존 `//opgc` 실행 결과와 Gate 동작이 달라지지 않아야 한다.
- `opal-security-checker`·`opal-convention-checker` 에이전트 — 검사 규칙 보유자에서 공통 스킬 실행 역할로 바뀐다.
- 향후 보안·컨벤션 Gate가 필요한 다른 Pilot — 공통 스킬을 직접 호출하는 소비자가 된다.
- 포함 범위: 공통 스킬 3종 신설, checker 에이전트 역할 전환, `opal-pilot-gc` wrapper 전환, 관련 프로젝트 문서 동기화.
- 제외 범위: 외부 reference registry와 공급망 승인 흐름, `opal-self-pm` 연결, 자동 수정 기능.

## Constraints

- C-1: 검사 스킬은 read-only다. 발견한 문제를 자동 수정하지 않는다.
- C-2: 프로젝트 `docs/SECURITY.md`·`docs/CONVENTIONS.md`를 최우선 기준으로 삼고, 공식 표준은 프로젝트 기준을 대체하지 않는다.
- C-3: 외부에서 받은 스킬·스크립트를 자동 설치하거나 실행하지 않는다.
- C-4: 단계 스킬 이름은 프로젝트 네이밍 규칙(`op-{그룹}-{역할}`)을 따른다.
- C-5: 검사 규칙 원본은 스킬 한 곳에만 두고 에이전트 문서에 복제하지 않는다.
- C-6: `opal-pilot-gc`의 독립 실행 수명주기·상태 추적·CLOSE 계약을 제거하지 않는다.
- C-7: 프로젝트 소스만 수정하고 배포본을 직접 편집하지 않는다.

## Acceptance criteria

- AC-1: 보안 검사 스킬·컨벤션 검사 스킬·보고 통합 스킬 3종이 각각 `opal/skills/` 아래 신설되고, `opal-pilot-gc` 없이 단독 호출된다.
- AC-2: `opal-pilot-gc`로 실행한 결과의 단계 구성·사용자 Gate·상태 행이 전환 전과 동일하다.
- AC-3: 두 checker 에이전트 문서에 검사 항목·기준·보고 형식 원본이 남아 있지 않고, 공통 스킬을 실행하는 역할 기술만 남는다.
- AC-4: 검사 스킬이 호출자가 명시한 파일 목록을 그대로 검사 대상으로 사용하며, staged 범위로 임의 축소하지 않는다.
- AC-5: 보안과 컨벤션 결과가 동일한 finding schema를 쓰고, severity·confidence·집행 수준·기준 출처가 각각 별도 필드로 존재한다.
- AC-6: 검사기나 기준 문서가 없어 일부만 검사한 실행이 통과 판정과 구분되는 별도 판정으로 보고된다.
- AC-7: 통합 보고가 이전 실행 대비 신규·잔존·해결 finding을 구분해 표시한다.
- AC-8: 프로젝트 기준 문서가 없는 상태에서 실행해도 검사가 중단되지 않고, 결측이 보고서에 명시된다.
- AC-9: `docs/PROJECT.md`의 GC 파이프라인 구성과 관련 문서 기술이 신규 구조와 일치한다.
