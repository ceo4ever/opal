# DONE: opd2 프레임워크 통합 — state-tool 단일 상태와 FW 공통 계약 연결

## 결과

opd2(`opal-pilot-dev2`)가 `//opd2`로 호출 가능한 FW 공통 Pilot이 됐다. 신규 태스크는 무플래그로 agentic·worktree 시작하고, 재개는 저장 mode·workspace를 상속하며 다른 workspace 플래그는 거부된다.

opd2 태스크의 단계 상태는 이제 `state-tool`이 관리하는 태스크 루트 `state.json` 한 곳에만 존재한다. 자체 `.sdlc/` journal·projection(`events.jsonl`, sdlc 버전 `state.json`/`STATE.md`/`AGENTIC-LOG.md`)은 더 이상 생성하지 않는다. `lifecycle.py`의 기계 게이트(아티팩트 결합 해시 체인, 계획 파일 범위, 실행 증거의 exit·안정성·로그 해시, Builder/Verifier/Reviewer 역할 분리, 보호 테스트 불변, 재작업 상한 3회)는 로직을 그대로 유지하면서, 판정 결과를 매 전이마다 `state-tool mark`로 SSOT에 커밋하도록 바뀌었다. 원장은 `<task>/run/opd2-ledger.json`(+evidence 로그)로 이전했다.

이 게이트는 `lifecycle.py`를 우회해 `state-tool mark --force`를 직접 호출해도 뚫리지 않는다 — `state_tool.py`에 opd/opds의 `apply_scenario_gate_mark_guard`와 동형인 opd2 전용 가드(`apply_opd2_gate_mark_guard`)를 신설해, 대상 행이 opd2 gate 키일 때 `lifecycle.py verify-mark`로 재검증하고 실패하면 `--force`·`--auto-pass`·`--as-worker` 무관하게 `opd2_gate_record_required`로 거부한다. 이 확장은 TASK C-1의 문자 그대로 범위(식별자·신규 기본값 등록)를 넘어서는 결정이라 세션 중 사용자에게 직접 확인해 승인받았다(PLAN.md Decisions·AGENTIC-LOG.md #5 참조) — 다른 Pilot의 동작은 전혀 바뀌지 않는다.

opd2의 Coordinator/Builder/Verifier/Reviewer 호출은 `pilot.start`·단계별 `stage.*`(VERIFY는 기존 `stage.test` 재사용)·`worker.dispatch` 이벤트 게이트를 거쳐 등록된 FW 워커(`opal-task-agent`)에게 매번 새 Agent 호출로 디스패치하도록 바뀌었다 — 이전 역할의 컨텍스트를 재사용하지 않아 "같은 워커가 구현과 검증·리뷰를 겸하지 않는다"는 요건을 물리적으로 보장한다. `delivery=release`(배포) 요청은 명시적으로 미지원 거부하며, `lifecycle.py`의 기존 `--delivery release` 아티팩트 경로 자체(C-4, 이미 커밋된 계약)는 건드리지 않았다.

빌드 배포 태스크는 독립 리뷰 통과 후 opd와 동일한 CLOSE 절차(`close.done_md`~`close.final`)로 마감돼 `completed_unmerged`가 된다. lease 확보·Stop 종료 차단·재개 안내·`worktree-tool checkpoint`·`finalize`는 skill 이름으로 분기하지 않는 FW 공통 메커니즘이라 opd2 전용 코드 추가 없이 그대로 적용된다(실측 확인, TEST S-11·S-12).

opd2가 FW 문서 체계에 등재됐다 — `opal-skills-registry.json`(alias `opd2`), `opal-pilot-dev2/references/pipeline.json`(신규), `README.md`(신규), `docs/PROJECT.md` Dev 파이프라인 컴포넌트 표, `harness/modes.md`·`harness/worktree.md`·`harness/skill-commands.md`의 신규 기본값 표. `harness/actor.md` §지원 Pilot 폐쇄 목록(`opd`·`opds`만)은 유지했다 — opd2는 actor=coordinator 축을 쓰지 않고 자체 역할 분리 구조를 그대로 쓴다.

## 변경 파일

- `opal/tools/state-tool/state_tool.py`
- `opal/core/references/opal-skills-registry.json`
- `opal/skills/opal-pilot-dev2/references/pipeline.json`(신규)
- `opal/skills/opal-pilot-dev2/scripts/lifecycle.py`
- `opal/skills/opal-pilot-dev2/scripts/opd2.py`
- `opal/skills/opal-pilot-dev2/SKILL.md`
- `opal/skills/opal-pilot-dev2/agents/coordinator.md`
- `opal/skills/opal-pilot-dev2/references/execution.md`
- `opal/skills/opal-pilot-dev2/references/lifecycle.md`
- `opal/skills/opal-pilot-dev2/README.md`(신규)
- `opal/skills/opal-pilot-dev2/tests/test_entrypoint.py`
- `opal/skills/opal-pilot-dev2/tests/test_lifecycle.py`
- `opal/skills/opal-pilot-dev2/tests/test_worktree_integration.py`
- `opal/tools/state-tool/tests/test_opd2_gate_mark_guard.py`(신규)
- `opal/core/references/harness/modes.md`
- `opal/core/references/harness/worktree.md`
- `opal/core/references/harness/skill-commands.md`
- `docs/PROJECT.md`

## 검증

- `~/.opal/.venv/bin/python -m pytest -q opal/tools/state-tool/tests/test_pilot_shared_contract.py opal/tools/state-tool/tests/test_opd2_gate_mark_guard.py` → 23 passed, 169 subtests passed(공유 인프라 회귀 가드 + 신규 가드 unit test 전건 그린, 다른 Pilot 무영향).
- `python3 -m unittest discover -s opal/skills/opal-pilot-dev2/tests -v` → 31 tests, OK.
- `~/.opal/tools/state-tool/run.sh spec-validate opal/skills/opal-pilot-dev2/references/pipeline.json` → `ok:true, violations_count:0`.
- TEST-SCENARIO.md S-1~S-13 전건 PASS — `test-scenario.json`(locked:true)에 구조화 증거 기록. S-3(e2e)이 완전 격리된 임시 저장소에서 `//opd2` 신규 워크트리 태스크로 TASK→DESIGN→PLAN→EXECUTE→VERIFY→CLOSE 전 구간을 완주했고, S-10이 `state-tool mark --force/--auto-pass/--as-worker` 직접 우회 시도를 전건 거부 확인.
- `opal-convention-checker` 컨벤션 자동 진단 — Critical/High 0건(low 6건 발견 후 전건 해소: `@header` 보강).

## 회고적 학습 후보

`.opal/brain/pages/opd2-state-tool-integration.md`

## 참고

- 사용자의 실제 설치본(`~/.opal/skills/opal-pilot-dev2/`, `~/.opal/tools/state-tool/state_tool.py`)이 W-10 검증 과정에서 이 태스크의 변경분으로 이미 동기화됐다(사용자 승인, 원본 백업 보관). 병합·정식 `scripts/install-mac.sh` 실행 시 재확인 권장.
- TEST-SCENARIO.md S-9(재개 시나리오)·S-10(직접 우회 거부)의 절차 문면에 사소한 표현 간극이 있었다(evaluator iteration 4 비차단 지적) — 실제 실행 결과에는 영향 없이 TEST 단계에서 해소하고 실행했다. 문서 자체는 설계 게이트 승인 당시 bundle hash가 동결돼 있어 소급 수정하지 않았다.
