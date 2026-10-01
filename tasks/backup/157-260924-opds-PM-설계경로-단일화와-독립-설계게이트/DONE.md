# DONE: PM 설계 경로 단일화와 독립 설계 게이트

## 결과

opd/opds 신규 PM 조율(`actor=coordinator`) 태스크는 이제 두 트랙이 함께 쓰는 PM 경로 파이프라인(`pipeline-pm.json`)으로 시작한다. `state-tool resolve-start`가 파이프라인 파일을 `init_args`의 `--rows-from`으로 판정하며, EXECUTE 전 행은 TASK 작성·TASK 확인·PLAN 작성·TEST-SCENARIO 작성·설계 게이트·설계 확인 6개다.

- PM은 별도 ANALYSIS 없이 PLAN 안 `## Findings`(직접 변경·회귀 확인·문서 갱신·미확인 가정)로 분석 결과를 구분해 기록한다.
- 설계 게이트(`state-tool design-gate start|record|reset`)가 결정론 검사(TASK 5절, Work item의 AC/C 전수 연결, Findings 규칙, 시나리오 coverage)를 수행하고, 독립 evaluator `design-rubric` 1회가 설계 4축과 시나리오 3축을 함께 판정한다.
- TASK·PLAN·TEST-SCENARIO 묶음 해시를 평가 시작·종료·승인 시점에 기록하고, EXECUTE는 현재 묶음 = 평가 통과 묶음 = 승인 묶음이고 TASK AC/C가 확인 이후 그대로일 때만 진입한다. 재평가는 이전 승인을 무효화한다.
- 반복 상한(3회)에 도달하면 심각도와 무관하게 사용자 대기이며, 해제는 사용자 `reset`뿐이다. agentic의 Normal/Minor 기록 후 진행 규칙은 이 게이트에 적용되지 않는다.
- 설계 중 결정은 `state-tool design-decision --scope external|detail`로 기록한다(external=사용자 대기, detail=PM 기록).
- 게이트 사건은 run-log `gate.requested`/`gate.resolved`(`design-gate-i{N}`)로 남는다. PM 경로 설계 구간은 신설 `stage.design` 이벤트 하나로 로드된다.

유지한 것: 기존 `pipeline.json`·`pipeline-short.json`과 `stage.analysis`·`stage.plan`·`stage.test_scenario`, `--no-pm`(worker) 경로, 저장 행으로 재개하는 기존 태스크, 다른 Pilot의 파이프라인·이벤트 매핑. PM 경로 판정은 행 key `plan.design_gate` 존재로만 하므로 기존 태스크는 새 가드를 타지 않는다. 이 태스크 자체는 착수 시점 계약(`pipeline-short.json`)으로 수행했다.

## 변경 파일

- `docs/PROJECT.md`
- `opal/agents/opal-evaluator-agent/AGENT.md`
- `opal/core/references/events.json`
- `opal/core/references/harness/actor.md`
- `opal/core/references/harness/design-gate.md`
- `opal/core/references/harness/guards.md`
- `opal/core/references/harness/skill-commands.md`
- `opal/core/references/opal-harness-agentic.md`
- `opal/skills/op-dev-plan/references/plan-guide.md`
- `opal/skills/op-scenario-gate/README.md`
- `opal/skills/op-scenario-gate/SKILL.md`
- `opal/skills/opal-pilot-dev/README.md`
- `opal/skills/opal-pilot-dev/SKILL.md`
- `opal/skills/opal-pilot-dev/references/pipeline-pm.json`
- `opal/tools/event-loader/event_loader.py`
- `opal/tools/event-loader/tests/test_event_loader_design_event.py`
- `opal/tools/event-loader/tests/test_event_loader_extended.py`
- `opal/tools/state-tool/README.md`
- `opal/tools/state-tool/schema/state.schema.json`
- `opal/tools/state-tool/state_tool.py`
- `opal/tools/state-tool/tests/test_design_gate.py`
- `opal/tools/state-tool/tests/test_start_resolution.py`
- `scripts/tests/task113_bootstrap_audit.py`

## 검증

- `test-scenario.json` 14/14 PASS(FAIL·BLOCKED 0). S-4·S-12는 real-usage, 나머지는 CLI 단위·회귀.
- 신규 RED 테스트: `pytest opal/tools/state-tool/tests/test_design_gate.py` 17 passed(구현 전 17 failed 관찰), event-loader 신규·확장 테스트 pass.
- S-4: 설치본 `opal-evaluator-agent` `design-rubric` 실제 디스패치. 정상 PLAN은 4축 PASS·시나리오 2/2/2. 실패 정책·저장 방식을 구현자에게 남긴 PLAN은 `decision_clarity` FAIL·`rewrite_target=plan`. 그 결과를 설치본 `design-gate record`에 넣으면 pass 기록은 `design_gate_verdict_mismatch`로 거부되고, rewrite 기록 후 EXECUTE 진입은 `design_gate_not_passed`로 거부된다(`run/test-evidence/s4-*`).
- S-12: `scripts/install-mac.sh` exit 0. 설치본 `resolve-start --new-task --skill opds`의 `--rows-from`이 `~/.opal/skills/opal-pilot-dev/references/pipeline-pm.json`이고, 6행 init과 `stage.design` load가 성공한다. 소스와 설치본 5개 파일의 sha256이 일치한다.
- S-11 회귀: 신규 실패 0. 남은 실패는 main에서 같은 명령으로 동일하게 재현되는 기존 결함이다(state-tool `TestT138W9` 세션 env 의존, test-tool E2E 인프라 의존 41건+3 errors, `task113_bootstrap_contract` bootstrap 4종 본문 불일치, `.sh` 3종). `pipeline.json`·`pipeline-short.json` diff 0.
- PM Gate: `code-scan validate --changed` ok(newly_uncovered 0), `state-tool validate` 위반 0, 컨벤션 진단 Critical/High 0(Medium 1건은 @header 보정 완료, `GC-CONVENTION-2026-09-25T01-02.md`).

## 회고적 학습 후보

.opal/brain/pages/concept/pm-design-path-independent-gate.md

## 참고

- 이 태스크는 착수 시점 계약(`pipeline-short.json`, `plan.pm_gate` 포함)으로 수행했다. 새 PM 경로는 merge·install 이후 생성되는 신규 opd/opds 태스크부터 적용된다.
- 기존 결함(이 태스크 무관, main 재현): `scripts/tests/task113_bootstrap_audit.py`의 bootstrap 4종 본문 byte 불일치, `test_agent_adapter_fields.sh`·`test_archive_contents.sh`의 Stop hook 계약, `test-install-skill-cleanup.sh`의 legacy `opal-pilot-dev-short` 잔존, `TestT138W9` 세션 env 의존.
- install의 `opal-cli console scan ~`이 홈 전체 `find`에서 멈춰 이 세션 소유 프로세스만 종료했다. 콘솔 프로젝트 자동 탐색이 생략됐으므로 필요하면 `opal-cli console scan <경로>`를 수동 실행한다.
