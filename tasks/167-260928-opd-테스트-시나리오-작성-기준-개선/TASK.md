---
template: sdlc-v2
---
# TASK: 테스트 시나리오 작성 기준 개선 — 중복·과잉 시나리오 억제와 advisory 응답 게이트

## Problem

현행 TEST-SCENARIO 게이트는 모든 AC/C/H가 시나리오에 연결됐는지, 그리고 목표·채택·경계 검증이 충분한지만 판정한다(`opal/core/references/harness/scenario-gate.md` §판정 축). 검증이 부족한 경우는 잡아내지만, 같은 실행을 반복하는 항목, 다른 항목에 포함되어 독립적인 결함을 찾지 못하는 항목, source grep이나 전체 회귀를 행동 시나리오처럼 작성한 항목, 더 저렴한 계층에서 검증할 수 있는 항목은 잡아내지 못한다(`docs/proposals/opal-test-scenario-economy-gate.md` §2).

그래서 연결 완전성을 지키느라 시나리오가 불필요하게 늘어나고, RED 작성·실행·증거 기록·실패 재검증 비용도 함께 늘어난다. 태스크 164에서 잠긴 12개 항목은 새 기준으로 보면 행동 시나리오 8개와 Check 3개로 나뉘고, 그중 두 항목은 하나의 실행으로 합칠 수 있었다(같은 문서 §9).

TEST-SCENARIO 표에는 유형 열이 없다(`opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` §Scenarios). test-agent의 변환 계약도 유형을 전달하지 않아서(`opal/agents/opal-test-agent/AGENT.md` §test-scenario.json 변환) 작성자가 선언하지 않은 유형을 워커가 추측하게 되고, 그 결과 분류가 일관되지 않다.

## Proposed outcome

TEST-SCENARIO 작성자는 별도 행동 시나리오를 만들지, assertion으로 합칠지, Check로 적을지를 가이드 기준으로 판단한다. 선언한 유형은 Markdown부터 `test-scenario.json`까지 추측 없이 그대로 전달된다. 도구는 확실히 판정할 수 있는 정확 중복과 모순만 차단한다. 의미상 중복은 evaluator가 advisory로 권고하고, PM이 각 advisory에 응답해야 PM 기본 경로(설계 게이트)와 목표-커버 게이트 경로의 게이트를 모두 완료할 수 있다. advisory를 반영한 뒤의 재판정은 기존 반복 상한을 소비하지 않고 한 번만 수행한다.

## Affected users and systems

- 사용자: opd·opds·opsdd로 태스크를 수행하는 PM(TEST-SCENARIO 작성자), 독립 evaluator, test-agent.
- 포함: TEST-SCENARIO 작성 가이드, 목표-커버 게이트·설계 게이트·TEST 실행 주기 규범, `op-scenario-gate` 스킬, evaluator·test-agent 에이전트 정의, test-tool 시나리오 변환·스키마·E2E 계약, state-tool 설계 게이트 기록·mark 가드·상태 스키마, 관련 도구 테스트, install 배포 검증.
- 제외: 시나리오 개수 상한, 프로젝트별 실행 시간 예산, 시나리오별 시간·명령 서명 저장, TEST 시간 미측정 선언 게이트, 별도 위험 카탈로그(제안서 §12 보류 항목). oppl·oppd 경로 변경. 이미 잠긴 `test-scenario.json`과 완료된 게이트 행의 소급 변환.

## Constraints

- C-1: 이미 잠긴 `test-scenario.json`과 완료된 게이트 행, 태스크 164의 잠금·PASS 증거를 소급 변경하지 않는다.
- C-2: `유형` 열이 없는 기존 TEST-SCENARIO 문서는 유형 누락만으로 거부되지 않고 기존 변환 방식으로 계속 처리된다. `red_required`가 없는 JSON을 true로 읽는 하위 호환도 유지한다.
- C-3: 새 상태 체계를 만들지 않는다. `design_gate.history[].verdict`의 기존 다섯 값, 기존 bundle hash, 기존 반복 상한 3회, `retry_limit`과 `reset --owner user` 해제 경로를 재사용하고, 스키마에는 선택 필드만 추가한다.
- C-4: 게이트 history 파일은 도구만 갱신한다. 스킬과 PM은 history를 직접 편집하지 않는다.
- C-5: 여러 검증 항목이 같은 실행 증거를 공유하더라도 항목별 assertion `expected`/`actual` 판정은 유지하며, `test-scenario.json`에 증거 공유용 새 필드를 추가하지 않는다.

## Acceptance criteria

- AC-1: TEST-SCENARIO 가이드만 보고도 작성자가 각 검증을 별도 행동 시나리오, 기존 시나리오의 assertion, Check 중 어디에 둘지와 어떤 테스트 계층을 쓸지 결정할 수 있다. 가이드는 고유 결함 신호, 같은 실행 여부, 가장 저렴한 충분 계층을 기준으로 제시하며, lint·build·전체 회귀는 AC/C가 직접 요구할 때만 Check로 연결하도록 안내한다.
- AC-2: TEST-SCENARIO의 `유형` 선언값(`unit`·`integration`·`contract`·`regression`·`e2e`·`check`)이 추측 없이 `test-scenario.json`의 `type`까지 전달된다. 유형 열이 있는 문서에서 유형이 누락되거나 허용되지 않은 값이면 거부된다.
- AC-3: `check` 유형에 RED가 요구된 항목, 그리고 유형·조건·행동·기대 결과·방법·환경·시점이 모두 같은 정확 중복은 도구가 입력 오류로 거부한다. 기대 결과만 다른 동일 실행 항목은 거부되지 않는다.
- AC-4: evaluator는 의미상 중복(포함 관계, 합칠 수 있는 동일 실행, 더 저렴한 계층, 잘못된 분류)을 pass 점수와 분리된 advisory로 반환하며, 각 advisory에는 대상 S-ID, 판단 근거, 권고 행동이 들어 있다.
- AC-5: 두 게이트 경로 모두에서 모든 advisory에 `apply` 또는 사유 있는 `retain` 응답이 ID 단위로 정확히 대응하지 않으면 게이트를 완료할 수 없다.
- AC-6: `apply`가 있으면 advisory 반영 재판정이 한 번만 수행되고, 이 재판정은 기존 반복 상한 3회를 소비하지 않는다. 재판정이 실패하면 `advisory_refinement_failed`로 사용자 대기에 들어간다.
- AC-7: 목표-커버 게이트 경로에서 게이트 기록을 생략했거나 통과 이후 TASK·PLAN·TEST-SCENARIO를 바꾼 상태로는 게이트 행을 mark할 수 없고, `--force`나 `--auto-pass`로도 우회할 수 없다.
