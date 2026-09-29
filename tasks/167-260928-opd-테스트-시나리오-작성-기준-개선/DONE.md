# DONE: 테스트 시나리오 작성 기준 개선 — 중복·과잉 시나리오 억제와 advisory 응답 게이트

## 결과

TEST-SCENARIO 작성 기준, 유형 전달, 중복 판정, advisory 응답 게이트를 제안서(`docs/proposals/archives/opal-test-scenario-economy-gate.md`)대로 규범 문서와 도구에 옮겼다.

- **작성 기준(AC-1):** 작성 가이드가 별도 행동 시나리오·assertion 통합·Check를 가르는 기준을 제시한다. 기준은 고유 결함 신호, 같은 실행, 가장 저렴한 충분 계층이다. 가이드에는 테스트 계층 선택과 경계 시나리오 기준도 들어 있다. lint·build·전체 회귀는 AC/C가 직접 요구할 때만 Check로 연결한다.
- **유형 전달(AC-2, C-2):** Scenarios 표에 `유형` 열(`unit`·`integration`·`contract`·`regression`·`e2e`·`check`)을 추가했다. `scenario-coverage-build`가 선언값을 payload `type`으로 넘기고, test-agent가 `test-scenario.json.type`에 그대로 옮긴다. 유형 열이 있는 문서에서 유형이 누락되거나 허용되지 않은 값이면 exit 17로 거부한다. 유형 열이 없는 기존 문서는 기존 변환대로(`type` null) 처리한다. `red_required`가 없는 JSON은 여전히 RED 대상으로 읽는다.
- **정확 중복·모순 차단(AC-3):** builder가 check+`구현 전 RED`, 그리고 여섯 셀이 모두 같은 정확 중복을 exit 17로 거부한다. `scenario-init`은 `type=check`와 `red_required=true`의 조합을 거부한다. 기대 결과만 다른 동일 실행 항목은 통과한다.
- **advisory 결과 계약(AC-4):** evaluator의 `scenario-rubric`·`design-rubric` 결과에 pass 점수와 분리된 `advisories[]`를 추가했다. 각 원소는 id, kind 4종, 대상 S-ID, 근거, 권고를 가진다. refinement 입력에서는 빈 배열을 반환한다. 두 기록 도구는 이 형식을 검사한다.
- **응답 게이트와 반영 재판정(AC-5, AC-6, C-3, C-4):**
  - 설계 경로: `state-tool design-gate record --advisory-responses`가 ID 단위 `apply`/사유 있는 `retain` 응답을 강제한다. `apply`가 있으면 `verdict: rewrite`·`reason: advisory_apply`로 기록한 뒤 대상 문서를 고쳐 refinement 회차 1번으로 재판정하며, 이 회차는 반복 상한을 소비하지 않는다(`limit_from` +1). 재판정이 실패하면 `advisory_refinement_failed`로 기존 `retry_limit`·`reset --owner user` 경로에 들어간다. history verdict 5값은 바꾸지 않았다.
  - 목표-커버 경로: 새 `test-tool scenario-gate-record`가 매 회차 이력을 원자 기록하며, 스킬은 더 이상 이력을 직접 쓰지 않는다. 기록 명령에는 `--input-error`·`--evidence-error` 모드가 있다.
- **mark 가드(AC-7, C-1):** 새 `test-tool scenario-gate-verify`와 `state-tool mark` 가드를 추가했다. `test_scenario.scenario_gate`·`plan.scenario_gate` 행은 기록을 생략했거나 통과 후 문서가 바뀐 상태로는 완료할 수 없고, `--force`·`--auto-pass`로도 우회할 수 없다. 이미 완료된 행과 `plan.design_gate`에는 적용하지 않는다.
- **증거 공유(C-5):** test-cycle.md에 규칙을 추가했다. 같은 SHA·명령·환경의 증거는 여러 S-ID가 공유할 수 있고, 판정은 S-ID별 expected/actual로 한다. `test-scenario.json` 필드는 추가하지 않았다.
- **유지한 것:** 이미 잠긴 `test-scenario.json`, 완료된 게이트 행, 태스크 164의 증거는 바꾸지 않았다. opsdd `review.scenario_gate`에는 mark 가드를 넣지 않았다(제안서 §7.2 범위).

실측(구 AC-8, PLAN Release): 최초본과 최종본 모두 행동 시나리오 6건(S-2~S-7), RED 대상 5건, Check 1건(S-1)으로 같다.
- 이 태스크의 설계 게이트는 설치본 evaluator(advisory 계약 이전)로 수행해서 advisory가 0건이었다. 그래서 통합·삭제된 항목이 없다.
- 최초 작성 때 새 기준을 이미 적용했다. AC-1·AC-4·C-4·C-5의 정적 확인은 Check 하나(S-1)로 합쳤고, 도구 경로별 동작은 같은 실행 단위로 묶었다(S-5 설계 경로, S-6 목표-커버 기록, S-7 mark 가드).

## 변경 파일

- `opal/tools/test-tool/lib/scenario.py`
- `opal/tools/test-tool/lib/e2e_contract.py`
- `opal/tools/test-tool/schema/test-scenario.schema.json`
- `opal/tools/test-tool/tests/test_scenario.py`
- `opal/tools/test-tool/README.md`
- `opal/tools/state-tool/state_tool.py`
- `opal/tools/state-tool/schema/state.schema.json`
- `opal/tools/state-tool/tests/test_design_gate.py`
- `opal/tools/state-tool/tests/test_mode_transition_contract.py`
- `opal/tools/state-tool/tests/test_state_tool_mode_contracts.py`
- `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md`
- `opal/skills/op-scenario-gate/SKILL.md`
- `opal/skills/op-scenario-gate/README.md`
- `opal/agents/opal-evaluator-agent/AGENT.md`
- `opal/agents/opal-test-agent/AGENT.md`
- `opal/core/references/harness/scenario-gate.md`
- `opal/core/references/harness/design-gate.md`
- `opal/core/references/harness/test-cycle.md`
- `docs/PROJECT.md`
- `docs/proposals/opal-test-scenario-economy-gate.md` → `docs/proposals/archives/opal-test-scenario-economy-gate.md`

체크포인트 커밋: `51bb463`(명세), `c86ae8f`(W-1·W-2·RED), `c4a79dd`(W-3), `b8c3a85`(W-4), `3cd2a87`(GC-001 수정), 그리고 CLOSE 커밋.

## 검증

- 설계 게이트: i1 결정론 실패, i2·i3 evaluator fail(결정 명확성), 상한 도달 후 캡틴 reset, i4 pass(설계 4축 PASS, 시나리오 1·2·2 평균 1.67).
- RED: S-2·S-4·S-5·S-6·S-7에서 실패를 관찰하고 `scenario-red`로 기록한 뒤 `scenario-lock`.
- 시나리오: `test-tool scenario-status` 결과 total 7, passed 7, failed 0, red_confirmed 5/5.
- 최종 회귀(HEAD b8c3a85): `~/.opal/.venv/bin/python -m pytest -q opal/tools/test-tool/tests opal/tools/state-tool/tests` → 25 failed, 1194 passed. 실패 25건은 모두 변경 전 HEAD에서도 실패하던 환경 의존 테스트다(E2E 브라우저·백엔드 기동 23건, 세션 ID 환경변수 2건 — 후자는 `env -i`로 다시 돌리면 2 passed).
- fix 재검증(HEAD 3cd2a87): 영향 시나리오 테스트 30 passed. test-tool 회귀에서 새 실패는 없다. S-7 가드 테스트 10 passed.
- 보안: 변경한 코드 파일에서 시크릿 패턴 grep 0건, `.gitignore` 영향 없음. `py_compile` 7개 파일 OK.
- 컨벤션: 최종 checker PASS_WITH_ADVISORIES(Critical/High/Medium/Low 0, Info 1). 보고서는 `run/GC-CONVENTION-20260929-r2.md`.

## 회고적 학습 후보

.opal/brain/pages/concept/scenario-economy-advisory-gate.md
.opal/brain/pages/concept/scenario-goal-coverage-gate-loop.md
.opal/brain/pages/entity/op-scenario-gate-skill.md
.opal/brain/pages/entity/test-tool.md
.opal/brain/pages/entity/state-tool.md

## 참고

- 설치본 검증(merge 후 허브에서 install한 뒤, 허브 PM이 캡틴 승인을 받아 수행):
  - `~/.opal/tools/test-tool/run.sh scenario-gate-verify --help` 성공 여부
  - 임시 태스크에서 목표-커버 게이트 행 mark가 거부되는지 재현
  - 설치본 evaluator로 중복 시나리오 fixture에서 advisory가 반환되는지 1회 확인
- install 직후 목표-커버 게이트 행이 미완인 진행 중 태스크는 `scenario-gate-record`로 이력을 만든 뒤 mark해야 한다(PLAN H-1). 거부 응답의 `required_action`이 이 절차를 안내한다.
- `opal/tools/test-tool/tests/test_e2e_human_executor.py::TestScenarioModuleUnchanged`는 `git diff HEAD`로 `scenario.py`·`e2e_contract.py`의 미커밋 변경만 막는 과거 태스크의 한시 가드다. 커밋 뒤에는 통과하지만 편집 중에는 실패하므로 정리 후보로 남긴다.
- 컨벤션 Info GC-002: `state_tool.py` @header description이 계속 누적되고 있다(baseline 유래). 리팩터 후보다.
