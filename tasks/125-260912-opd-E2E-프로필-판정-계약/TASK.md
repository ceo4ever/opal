---
template: sdlc-v2
---
# TASK: E2E profile·verdict 계약 도입

## Problem
현행 E2E 실행은 브라우저 fallback 요청이나 화면 열기·이동만으로도 성공처럼 소비될 수 있고, 요구사항의 공개 표면과 실행 수단이 일치하는지 강제하지 않는다. Browser 외 API·Hybrid·사람 협업 흐름의 상태와 증적 계약도 없어 낮은 충실도의 대체 실행이 실제 사용자 목표 검증으로 승격될 수 있다.

## Proposed outcome
E2E 진입점이 요구사항의 공개 표면을 기준으로 Browser·API·Hybrid·Collaborative·Manual profile을 결정하고, 실행 결과를 공통 상태·exit code·증적 조건으로 판정한다. capability 부재와 제품 실패가 분리되며 assertion 또는 필수 증적이 없는 실행은 성공으로 판정되지 않는다.

## Affected users and systems
OPAL 파일럿으로 E2E를 실행하는 사용자와 워커, `test-tool`의 E2E·충실도 판정 경로, runner resolver와 도구 스키마, L3b/real-usage 계약을 소비하는 개발·프로젝트 파일럿 및 관련 회귀 테스트가 영향받는다. Runtime Manager, 실제 Browser/API/Human executor 구현과 Playwright 기본 설치 제거는 이번 범위에서 제외한다.

## Constraints
- C-1: 요구사항의 공개 표면이 profile을 결정하며, 도구 가용성을 이유로 UI 핵심 행동을 API-only 실행으로 대체하지 않는다.
- C-2: 최종 상태는 `pass`, `fail`, `executor_unavailable`, `infra_error`, `blocked`로 정규화하고 `awaiting_human`은 재개 가능한 중간 상태로만 취급한다.
- C-3: Browser 후보 전환은 `provider_unavailable`일 때만 허용하고 assertion·제품·인증·데이터·증적 실패를 다른 후보의 성공으로 덮지 않는다.
- C-4: 공통 `real-usage` 의미는 실제 공개 표면의 행동, semantic assertion, 필수 증적을 모두 요구하는 단일 계약으로 유지한다.
- C-5: 기존 상태·오류 입력은 명시적인 이행기 변환을 제공하되 신규 결과에서 generic `fallback`, `escalated`, `escalate`를 생성하지 않는다.
- C-6: 플랫폼별 차이는 resolver/adapter 경계에 격리하고 특정 IDE·에이전트 런타임을 코어 판정 로직에 하드코딩하지 않는다.
- C-7: 이번 태스크는 profile·verdict·migration 계약과 그 소비자·테스트까지만 변경하며 Runtime Manager, driver/session 구현, Playwright 제거는 후속 독립 태스크로 남긴다.

## Acceptance criteria
- AC-1: Browser·API·Hybrid·Collaborative·Manual 다섯 profile과 허용 executor 조합이 기계 검증 가능한 계약으로 정의되고 surface 불일치가 거부된다.
- AC-2: 최종 다섯 상태와 `awaiting_human`이 서로 구분되며 `pass=0`, `fail=6`, `infra_error=7`, `executor_unavailable=18`, `blocked=19`, `awaiting_human=20` 매핑이 테스트로 고정된다.
- AC-3: 기존 reason별 fallback·escalation 입력이 명시된 신규 상태로 변환되고, 알 수 없거나 reason 없는 fallback은 fail-safe로 `infra_error`가 된다.
- AC-4: `provider_unavailable`만 다음 Browser 후보를 허용하며 실행 시작 뒤 assertion 실패와 제품 실패는 최종 `fail`로 보존된다.
- AC-5: assertion expected/actual 또는 profile·시나리오가 요구한 필수 증적이 누락된 실행은 `pass`와 `real-usage`로 승격되지 않는다.
- AC-6: API-only 실행이 Web UI 요구사항을 통과하지 못하고 Hybrid가 핵심 UI 행동과 후속 API/state 검증을 모두 요구하는 회귀 테스트가 통과한다.
- AC-7: Collaborative·Manual 흐름은 사람 응답을 즉시 성공으로 해석하지 않고 `awaiting_human` 또는 구조화 검증 뒤 최종 상태로 전이한다.
- AC-8: `test-tool`, resolver/schema, 관련 파일럿 소비자의 기존 호환 테스트와 신규 계약 테스트가 모두 통과한다.
- AC-9: 변경된 규범 문서와 코드의 단일 소유권이 유지되고 source install 검증에서 배포본이 새 계약과 일치한다.
