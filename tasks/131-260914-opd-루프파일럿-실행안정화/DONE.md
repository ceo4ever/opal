# DONE: OPPL 실행 안정화 — 상한·완료판정 도구 집행

## 결과

OPPL의 장시간 실행·반복 상한·완료 판정이 문서 규칙에서 도구 집행으로 바뀌었다. 에이전트가 자체 카운터로 상한을 세거나 receipt 없이 완료를 기록하는 경로가 사라졌다.

**실행 원시 기능** — `opal-agent`가 루트 프로세스를 별도 process group으로 띄우고, stdout read loop와 독립된 monotonic timer로 hard timeout과 (stream 한정) heartbeat timeout을 집행한다. 초과 시 PGID 전체에 TERM을 보내고 유예 후 KILL로 승격하며, PGID 소멸을 확인한 뒤에만 `timed_out`을 확정한다. 완료 판정은 마지막 유효 result를 terminal candidate로 삼고 그 뒤 epilogue allowlist(`subtype` 기준)만 허용하며, stream 종료 시점에 등록된 자식이 전부 terminal이어야 한다. 산출물 writer 소유권이 호출측 셸 리다이렉트에서 opal-agent 프로세스로 이동했다.

**상한 집행** — 신규 `oppl-runtime-tool`이 `.oppl-run/runtime.json`을 운영 ledger로 소유하고, 설계 회전·프로젝트 dispatch·task attempt·resume·비용·벽시계·무진전을 `admit` 경계에서 판정한다. 거부는 폐쇄 집합 8종 코드와 `scope` 필드로 반환하며 에이전트가 재해석하지 않는다.

**도구 문서 구조** — `tools.md`가 규범·레지스트리·사용법을 함께 들고 있던 구조를 소유 경계로 갈랐다. 출력 규범은 하네스 owner 문서로 분리해 `stage.execute` 이벤트에 편입했고, 레지스트리는 도구 22종 전수 표가 됐으며, 사용법은 각 도구 README가 소유한다.

**유지한 동작** — `opal-agent`의 신규 인자를 주지 않은 호출은 stdout·stderr·exit code·생성 파일이 변경 전과 동일하다. `state.json`은 `required` 8필드와 `additionalProperties: false`가 불변이고 `run_id` 없는 기존 파일이 계속 검증을 통과한다. `opal-action-monitor`는 `runtime.json` 부재 시 기존 6상태 휴리스틱을 유지하고 `timed_out`을 출력하지 않으며 어느 경로에서도 파일을 쓰지 않는다. 3-SSOT 정의는 3축 그대로이고 `runtime.json`은 별개의 런타임 가드 축이다.

## 변경 파일

코드
- `opal/tools/oppl-runtime-tool/oppl_runtime_tool.py`
- `opal/tools/oppl-runtime-tool/ledger.py`
- `opal/tools/oppl-runtime-tool/run.sh`
- `opal/tools/opal-agent/opal_agent.py`
- `opal/tools/state-tool/state_tool.py`
- `opal/tools/state-tool/schema/state.schema.json`
- `opal/tools/backlog-tool/backlog_tool.py`
- `opal/tools/opal-action-monitor/opal_action_monitor.py`
- `scripts/install-mac.sh`

테스트
- `opal/tools/opal-agent/tests/test_opal_agent_runtime.py`
- `opal/tools/opal-agent/tests/test_opal_agent_cli_runtime.py`
- `opal/tools/opal-agent/tests/fixtures/` (stream fixture 6종)
- `opal/tools/oppl-runtime-tool/tests/test_oppl_runtime_config.py`
- `opal/tools/oppl-runtime-tool/tests/test_oppl_runtime_admission.py`
- `opal/tools/oppl-runtime-tool/tests/test_ac_integration.py`
- `opal/tools/state-tool/tests/test_run_identity.py`
- `opal/tools/backlog-tool/tests/test_backlog_header_sync.py`
- `opal/tools/opal-action-monitor/tests/test_monitor_delegation.py`
- `opal/tools/memory-tool/tests/test_memory_tool.py`
- `opal/tools/tool-scan/tests/test_tool_scan.py`
- `opal/tools/code-scan/tests/test-regression.js`

하네스·문서
- `opal/core/references/harness/tool-output-contract.md` (신규)
- `opal/core/references/events.json`
- `opal/core/references/tools.md`
- `opal/core/references/opal-harness.md`
- `opal/core/references/pm/code-scan-management.md`
- `opal/agents/opal-loop-action-agent/AGENT.md`
- `opal/skills/opal-pilot-project-loop/SKILL.md`
- `opal/skills/opal-pilot-project-loop/references/loop-control.md`
- `docs/CONVENTIONS.md`
- `docs/PROJECT.md`
- `docs/proposals/archives/opal-oppl-runtime-stabilization.md` (갱신 후 아카이브 이동)

도구 README 22종 — 신규 9(`code-scan`·`xlsx-tool`·`worktree-tool`·`improve-tool`·`git-sync-tool`·`tool-scan`·`date`·`playwright-tool`·`skill-registry`), 갱신 7(`state-tool`·`test-tool`·`memory-tool`·`brain-tool`·`cmux-tool`·`opal-action-monitor`·`oppl-runtime-tool`)

brain
- `.opal/brain/pages/concept/opal-agent-stream-json-passthrough.md`
- `.opal/brain/pages/concept/oppl-executor-delegation-architecture.md`
- `.opal/brain/index.md`

## 검증

- `pytest opal/tools/ -q` (OPAL venv) → **1239 passed, 3 skipped, 263 subtests passed**. 실패 4건은 `tool-scan`의 `TestOutputArtifacts`이며 `main`에서 동일 재현되는 선재분이다(하네스 §9 도구 표 drift).
- `node opal/tools/code-scan/tests/test-regression.js` → 작업본 11 실패 = `main` 11 실패, 증분 0건.
- 시나리오 35/35 `pass`, `locked: true`. RED 대상 24건은 `red_confirmed` 후 `scenario-lock`을 통과했다.
- process group 회수는 대역 없이 실측했다 — 손자 프로세스를 fork하는 무출력 스크립트에서 TERM→유예→KILL 후 `os.kill(pgid, 0)`가 `ProcessLookupError`를 던져 PGID 전체 소멸을 확정했다. SIGTERM 무시 자식은 KILL 승격으로 회수됐다.
- 파일 lock 직렬화는 음성 대조군으로 증명했다 — 16 프로세스 × 5회전에서 락 구현은 매회 `granted=1`, 스크래치패드 사본에서 `fcntl.flock` 한 줄을 무력화하면 `granted=3`(lost update)이 재현됐다.
- 회귀 경계는 실측했다 — `opal-agent` 신규 인자 미지정 호출의 stdout·stderr가 변경 전과 바이트 동일, 생성 파일 0건.
- 배포본 실호출 — `./scripts/install-mac.sh` 후 `~/.opal/tools/opal-agent/run.sh`가 신규 플래그 7종을 노출하고 상한 초과 요청을 프로세스 생성 0건으로 거부한다. 배포본 loader의 `stage.execute`가 `tool-output-contract`를 포함해 문서 3건을 싣는다.
- 컨벤션 자동 진단 2회 — 1차 High 1건(존재하지 않는 절을 규범 SSOT로 인용) 시정 후 2차 Critical 0·High 0.

## 회고적 학습 후보

.opal/brain/pages/concept/tool-doc-ownership-split.md
.opal/brain/pages/concept/subtest-masks-red-first-failure.md
.opal/brain/pages/concept/condensed-copy-rots-faster-than-source.md
.opal/brain/pages/concept/norm-must-match-fleet-reality.md

## 참고

**제안서 아카이브 판정 — `docs/proposals/archives/`로 이동, 상태 `적용완료`**

`proposal-lifecycle.md`의 판정 명령(`grep -rn "proposals/<파일명>"`)이 잔여 0건을 반환했고, 이동 후 재판정도 0건이다. `docs/PROJECT.md` 문서 레지스트리에는 등재돼 있지 않아 제거할 행이 없다.

PM이 초기에 경로 없는 `제안서 §N` 형태 인용을 근거로 보류했으나 오판이었다. 이 형태는 여러 도구가 각기 다른 제안서를 가리키는 프로젝트 전역 관행이며, `worktree-tool`이 `제안서 §6.3`으로 인용하는 제안서가 이미 `archives/`에 있다. 즉 판정 명령이 경로 형태만 세는 것은 사각지대가 아니라 의도된 설계이고, 계약의 "판정은 명령이 소유하며 PM이 눈으로 세지 않는다"를 PM이 어긴 것이다.

**후속 과제**

1. 하네스 §9 도구 표 drift — `tool-scan` 테스트 4건과 `code-scan` 회귀 일부가 이 표의 낡음에서 실패한다. 이번 재정의가 만든 것이 아니라 드러낸 것이다.
2. `oppl-runtime-tool`에 오류 코드 선언 목록 부재 — 22개 도구 중 8개만 보유한 패턴이라 규범 위반은 아니나, 이 도구는 거부 코드가 여러 서브명령에 걸치므로 도입이 맞다.
3. 커버리지 빌더의 침묵 누락 — `test-tool scenario-coverage-build`가 인식하지 못한 표 행을 오류 없이 버린다. 식별자 형식 이탈과 조건 열의 파이프 문자 두 경로에서 재현됐다.

**운영 전제**

전역 `~/.opal/setting.json`에 `oppl.runtime` 블록이 없으면 `init`·`admit`이 전부 거부된다. 설계대로의 fail-closed이며 필요한 9개 키는 `opal/tools/oppl-runtime-tool/README.md`가 소유한다.
