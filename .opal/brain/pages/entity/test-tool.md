---
type: entity
title: test-tool
tags:
- tool
- testing
- pipeline
- scenario-gate
sources:
- task:039
- task:111
- task:161
- task:167
related: [state-tool, sdlc-v2-development-artifact-contract, test-two-tier-system, scenario-goal-coverage-gate-loop, op-scenario-gate-skill]
created: 2026-06-23
updated: '2026-10-01'
status: active
---
## 개요

OPAL 테스트 실행과 시나리오 상태를 결정론적으로 관리하는 CLI 도구다. `unit` 서브명령은 설치 확인과 실제 검사를 분리해 실행하고(task:161), `scenario-*` 서브명령은 시나리오 명세의 유형·정확 중복을 검사하며 목표-커버 게이트 이력을 기록·검증한다(task:167).

## 책임 (WHAT)

- 기존 resolve, check, unit, integration 명령을 유지한다.
- **unit 실행 계약 복구(task:161)**: 도구 항목의 `check`(설치 확인)와 `run`(실제 검사)을 분리해 실행한다. `run`이 없으면 아무 명령도 실행하지 않고 `not_configured`, `check`가 실패하면 `tool_unavailable`(run은 실행하지 않음), `run`이 실패하면 `fail`이다. 계층 상태는 `pass`·`fail`·`tool_unavailable`·`not_configured`·`not_applicable`·`not_run` 폐쇄 목록이고, 전체 상태는 `pass`·`fail`·`incomplete`로 빈 실행이나 설치 확인 실패를 통과로 소비하지 않는다(`opal/tools/test-tool/lib/runner.py:249` `run_unit_layers`). `--changed-files`는 `run_files`를 가진 도구에만 파일 단위로 전달되고, 지원하지 않는 도구는 전체 범위로 실행되며 그 사유(`file_scope_unsupported`)가 응답에 남는다.
- scenario-coverage-build가 sdlc-v2의 AC/C/H/S를 정규화하고 coverage-check가 누락을 판정한다. **유형 열 전달(task:167)**: `Scenarios` 표에 `유형` 열이 있으면 6종 값(unit/integration/contract/regression/e2e/check)을 검증해 payload `type`·`red_required`로 넘긴다. `check` 유형이면서 구현 전 RED 대상이거나, 유형·조건·행동·기대 결과·방법·환경·시점 여섯 셀이 모두 같은 정확 중복 행은 exit 17로 거부한다.
- scenario-init, scenario-red, scenario-lock으로 시나리오 명세와 선택적 RED 증거를 동결한다. `scenario-init`도 `type=check`+`red_required=true` 조합을 `scenario_contract_invalid`(exit 17)로 거부한다.
- scenario-mark가 PASS, FAIL, BLOCKED와 실행 증거를 기록하고 scenario-status가 전체 결과와 필수 RED 진행을 반환한다.
- **목표-커버 게이트 기록·검증(task:167)**: `scenario-gate-record`(`opal/tools/test-tool/lib/scenario.py:1377`)가 회차마다 evaluator 결과·advisory 응답·판정(pass/rewrite/escalate)을 이력 배열에 원자 기록하고, `scenario-gate-verify`(`opal/tools/test-tool/lib/scenario.py:1639`)가 이력 마지막 원소의 `verdict: pass`와 현재 TASK/PLAN/producer 파일의 묶음 hash 일치를 검사한다. 불일치·이력 부재·미통과는 exit 20 `scenario_gate_not_passed`다.

## 설계 배경 (WHY)

상태와 증거를 Markdown 산문에서 분리해 같은 판정을 반복 추론하지 않게 하고, 구현 전 RED가 필요한 행만 도구가 차단하도록 만들었다. 필드가 없는 기존 JSON은 모든 행을 RED 대상으로 보아 하위호환을 유지한다. (근거: task:111 PLAN `Decisions and contracts`)

전역 템플릿의 unit 도구가 전부 `--version`류만 `check`에 선언해 실제 검사 없이 통과되던 결함을 고쳤다. `run` 누락 시 `check`를 대체 실행하지 않는 것은, 구형 설정의 `check`에 든 실제 검사 명령을 설치 확인으로 오인해 실행하는 일을 막기 위해서다(근거: task:161 PLAN D-2 "계층 실행 순서"·D-9 "구형 설정 이관"). 설치 확인 실패·미설정·미실행·검사 실패·통과를 구분해 빈 실행이 통과로 소비되던 결함도 함께 막았다(근거: task:161 PLAN D-4, DONE.md 결과).

유형 선언이 문서에서 JSON까지 전달되지 않아 유형별 자동 검사를 걸 수 없었던 결함을, evaluator의 개선 제안을 구조화된 `advisories[]`로 명시하고 응답을 강제해 반영 여부가 담당자 재량으로 소실되지 않게 한 설계(→ [[scenario-economy-advisory-gate]])의 일부로 고쳤다. 목표-커버 게이트 이력을 스킬이 직접 append하던 방식을 도구 명령으로 옮긴 것은, `state-tool mark`가 기록 누락·문서 변경 후 완료를 기계적으로 차단하게 하기 위해서다(근거: task:167 PLAN Decisions "목표-커버 기록 명령"·"mark 가드").

## 관계 (HOW)

- [[sdlc-v2-development-artifact-contract]]의 테스트 결과 SSOT를 담당한다.
- [[state-tool]]은 단계·승인을 담당하며 두 도구의 상태 소유권은 겹치지 않는다. task:167부터 `state-tool mark`가 게이트 행 완료 시 이 도구의 `scenario-gate-verify`를 subprocess로 호출해 기록 누락을 차단한다.
- [[test-two-tier-system]]의 단위·통합 실행 경계를 유지한다.
- [[scenario-goal-coverage-gate-loop]]에 결정론 coverage 결과를 제공하고, task:167부터 회차별 기록·검증까지 이 도구가 전담한다.
- [[op-scenario-gate-skill]]이 이 도구의 `scenario-gate-record`·`scenario-gate-verify`를 매 회차 호출하는 컨트롤 스킬이다.

## 소스 커버리지

| 식별자 | 경로:줄번호 | 설명 |
|---|---|---|
| scenario handlers | `opal/tools/test-tool/lib/scenario.py:154` | 시나리오 정규화와 결과 관리 |
| selective RED lock | `opal/tools/test-tool/lib/scenario.py:257` | RED 대상만 잠금 검사 |
| result status | `opal/tools/test-tool/lib/scenario.py:358` | PASS/FAIL/BLOCKED와 필수 RED 집계 |
| regression tests | `opal/tools/test-tool/tests/test_scenario.py:395` | 선택적 RED와 BLOCKED 공개 CLI 검증 |
| run_unit_layers | `opal/tools/test-tool/lib/runner.py:249` | check/run 분리, 계층별 상태·사유 판정(task:161) |
| resolve source_path | `opal/tools/test-tool/lib/resolver.py:245` | 설정 출처 파일 절대경로 포함 추론(task:161) |
| scenario-gate-record | `opal/tools/test-tool/lib/scenario.py:1377` | 목표-커버 게이트 회차 이력 원자 기록(task:167) |
| scenario-gate-verify | `opal/tools/test-tool/lib/scenario.py:1639` | 마지막 pass·묶음 hash 일치 검증(task:167) |
