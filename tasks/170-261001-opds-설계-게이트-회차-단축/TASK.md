---
template: sdlc-v2
---
# TASK: 설계 게이트 회차 단축 — 결정론 사전 검사·사전 점검 절차·evaluator 설정 최적화

## Problem

opd·opds PM 경로의 설계 게이트는 회차가 반복되면서 시간이 오래 걸리고, 반복 상한에 걸리면 캡틴 reset을 기다리느라 태스크가 멈춘다.

- 설계 게이트를 거친 태스크 6건(161·162·163·164·167·168)의 18회차를 보면 결과는 결정론 실패 5회, evaluator rewrite 7회, pass 6회였다. 근거는 각 태스크 `state.json`의 `design_gate.history`이고, 168은 작업본 `.opal-worktrees/task_168`의 기록이다.
- 결정론 실패는 evaluator를 부르기 전의 규칙 검사(`opal/tools/state-tool/state_tool.py:6787` `_design_gate_deterministic_check`)에서 난다. 그런데도 `design-gate start`는 회차를 먼저 올리므로 이 실패가 반복 상한 3회 중 1회를 소모한다. 이 검사만 시도 없이 미리 돌려볼 방법은 없다. `design-gate`의 하위 명령은 start·record·reset뿐이다(`state_tool.py:8026-8042`).
- 반복 상한에 걸린 태스크는 167과 168이다. 두 태스크 모두 1회차가 결정론 실패였다. 167은 3회차(2026-09-28 18:57) 뒤 캡틴 reset을 거쳐 4회차가 2026-09-29 09:54에 기록됐다. 반면 evaluator 회차 사이의 간격은 4~6분이었다(167 `design_gate.history[].at`).
- evaluator rewrite 7회 중 6회가 `decision_clarity` 실패였다. 이 축은 "외부 동작·인터페이스·실패 정책·구조·저장 방식 중 하나라도 구현자에게 선택을 남기면 FAIL"로 판정된다(`opal/agents/opal-evaluator-agent/AGENT.md:114`). 167은 같은 축이 2·3회차에 연속으로 실패했다(`tasks/167-*/run/design-gate-i2.json`·`i3.json`).
- PM 경로는 PM의 자기 검토 게이트(`plan.pm_gate`)를 두지 않는다(`opal/skills/opal-pilot-dev/SKILL.md:69`). 그래서 PLAN에 새 메커니즘이 추가되면 대응 시나리오 누락은 다음 evaluator 회차에서야 드러난다. 168은 2회차에 PLAN을 보완한 뒤 3회차에 시나리오 부족으로 rewrite를 받았다(작업본 168 `AGENTIC-LOG.md` #6).
- evaluator는 `model: advanced`만 지정하고 effort를 지정하지 않는다(`opal/agents/opal-evaluator-agent/AGENT.md:8`). 그래서 판정 깊이와 시간이 evaluator를 부른 세션의 effort 설정에 따라 달라진다. 에이전트 effort를 플랫폼 설정으로 옮기는 통로는 이미 있다(`scripts/install-mac.sh:519` `OPAL_ADAPTER_FIELD_SPEC`).

## Proposed outcome

결정론 검사에서 걸리는 누락은 반복 상한을 소모하지 않고 PM이 미리 보완하므로, evaluator 회차는 의미 판정에만 쓰인다. PM 경로는 `design-gate start` 전에 `decision_clarity` 기준 점검과 "새 메커니즘에 대응하는 시나리오" 점검을 절차로 수행한다. evaluator의 rewrite 지적은 PM이 다음 회차에 무엇을 채워야 하는지 알 수 있을 만큼 구체적이다.

evaluator의 model·effort는 과거 판정 기록으로 만든 평가 세트로 측정한다. 캡틴은 결함을 놓치지 않는 후보 가운데 설정을 고르고, 선택한 설정은 호출 세션과 무관하게 고정 적용된다. 판정 기준과 반복 상한은 그대로다.

## Affected users and systems

- 사용자: opd·opds PM 경로로 태스크를 수행하는 캡틴·PM, 설계 게이트를 판정하는 `opal-evaluator-agent`.
- 포함: `state-tool`의 설계 게이트 명령과 테스트, `harness/design-gate.md`, `op-scenario-gate` 스킬, `opal-pilot-dev` PM 경로 절, `op-dev-plan`·`op-dev-test-scenario` 가이드, `opal-evaluator-agent` 정의(출력 지적 형식·model·effort), 평가 세트와 측정 기록, install 배포 검증.
- 제외: 루브릭 축과 pass 조건, 반복 상한 수치와 reset 권한, `--no-pm`(actor=worker) 경로의 목표-커버 게이트, evaluator의 다른 phase(`design-review`·`spec-review`·`drift-recheck`·`scenario-rubric`)의 판정 기준, advanced 레벨 전역 모델 매핑.

## Constraints

- C-1: 설계 게이트의 판정 기준(설계 4축·시나리오 3축·pass 조건), 반복 상한 3회, `reset --owner user` 전용 해제는 바꾸지 않는다(`opal/core/references/harness/design-gate.md`).
- C-2: evaluator model·effort 변경은 평가 세트에서 결함 사례를 하나도 놓치지 않은 후보 중에서 캡틴이 결정한 설정만 적용한다. 결정 전까지는 현행 설정을 유지한다.
- C-3: 평가 실행은 후보 설정 3개 이하로 한정한다. 사례 수와 실행 상한은 PLAN에서 확정한다.
- C-4: 태스크 168·169가 같은 파일(`state_tool.py`, `opal-pilot-dev/SKILL.md`)을 동시에 수정하므로, 이 태스크의 편집은 자기 영역(헤딩·함수 단위)으로 한정하고 다른 영역을 덮어쓰지 않는다(`.opal/brain/pages/concept/concurrent-task-shared-file-discipline.md`).
- C-5: 설치본과 상태 편집은 프로젝트 규칙을 따른다(`.opal/AGENT.md` §금지사항). `~/.opal/`은 직접 수정하지 않고, 파이프라인 행 상태는 `state-tool`로만 바꾼다.

## Acceptance criteria

- AC-1: 설계 게이트의 결정론 검사에서 걸리는 누락을 PM이 게이트 회차·반복 상한·상태를 소비하지 않고 확인할 수 있다. 이 확인 결과는 `design-gate start`의 결정론 판정과 같은 누락 목록을 낸다.
- AC-2: PM 경로 절차는 `design-gate start` 전에 PLAN이 구현자에게 외부 동작·인터페이스·실패 정책·구조·저장 방식의 선택을 남기지 않는지 점검하도록 요구한다. 점검 항목은 evaluator의 `decision_clarity` 기준과 같은 표현을 쓴다.
- AC-3: PLAN에 새 메커니즘(가드·명령·상태·오류 코드 등 새 검증 대상)을 추가하거나 바꾸면, 대응하는 TEST-SCENARIO 항목도 같은 회차 안에서 갱신하도록 PLAN·시나리오 작성 절차가 요구한다.
- AC-4: evaluator의 rewrite 지적은 항목마다 대상 문서 위치와 구현자에게 남은 선택(필요한 결정)을 명시한다. 다음 회차 판정은 이전 회차 지적 각각의 해소 여부를 보고한다.
- AC-5: 통과 사례(최종 문서 묶음)와 결함 사례(기록된 evaluator 지적으로 재구성)로 이루어진 평가 세트에서, 후보 설정별로 판정 일치·결함 누락 건수·회차 소요 시간이 측정되어 캡틴에게 보고된다.
- AC-6: 캡틴이 결정한 evaluator의 model·effort가 설치된 에이전트 정의에 반영되어, 호출 세션의 effort 설정과 무관하게 같은 설정으로 실행된다.
