# DONE: 파일럿 기본 실행 정책과 PM 역할 재정의

## 결과

- 신규 `opd`·`opds`·`oppd`·`oppl`·`oppb` 태스크는 플래그 없이 agentic·worktree로 시작한다. 그 외 Pilot(`opp`·`opwt`·`opsdd`·`opdd`·`opgc`·`opdw`)은 기존 semi-agentic·허브 기본값을 유지한다. oppb는 프로젝트 worktree 1개·Supervisor 구조를 그대로 쓰며 `--no-wt`는 거부한다.
- `opd`·`opds` 신규 태스크의 기본 actor는 PM 조율(`coordinator`)이다. PM은 TASK·분석·PLAN·TEST-SCENARIO와 분배·파일 소유권·검토·재작업·마감을 맡고, 구현·자가 점검·TEST FAIL 수정은 PLAN `담당`의 전문 워커가 맡는다. 병렬은 선행 관계가 없고 변경 파일이 겹치지 않을 때만 허용한다. 계약 원문은 `opal/core/references/harness/actor.md` 한 곳이다.
- 해제 옵션은 `--no-pm`(결과 = 기존 `actor=worker`)으로 확정했다. 제안된 `--worker`는 `[WORKER]` 마커·`--as-worker`와 어휘가 겹쳐 채택하지 않았다(PLAN DEC-5). legacy `actor=pm`(PM 직접 수행)은 재개만 지원하고 신규 init은 `actor_pm_retired`로 거부한다.
- 세 축 판정은 `state-tool resolve-start`가 원문 플래그로 결정론 집행한다. 충돌은 `mode_flag_conflict`·`workspace_flag_conflict`·`actor_flag_conflict`, 재개 중 workspace·actor 변경은 `resume_axis_locked`로 거부하고, 재개는 저장된 mode·작업본·actor를 상속한다.
- worktree 생성 실패 시 허브 `tasks/` 폴백을 제거했다(`task-process.md` 스텝 4.5). `state init --workspace worktree`는 `--worktree` 없이 `worktree_path_required`로 거부하고, `worktree-tool create`는 작업본 안의 작업본 생성을 `PROJECT_ROOT_IS_WORKTREE`로 거부한다. launcher 실패는 비차단을 유지하되 이미 만든 작업본에서 계속한다.
- `actor.md`의 "actor=pm CLOSE 첫 행 `--owner user`" 문장을 제거해 CLOSE 전이를 actor 무관 `modes.md` 단일 계약으로 정리했다. EXECUTE 분기·TEST FAIL 수정 경로·TEST-SCENARIO 작성자 설명의 모순도 정리했다.
- 유지: 독립 evaluator(`op-scenario-gate`)·opal-test-agent·조건부 GC 검사·실제 실행 증거·기존 state gate·재시도 상한·oppb P5 사용자 전용 merge 게이트·merge/push/배포 승인 경계. oppm 계약은 변경하지 않았다.
- 적용 시점: 새 계약은 2026-09-24 사용자가 이 브랜치 작업본에서 `scripts/install-mac.sh`를 실행한 시점(merge 전)부터 설치본에 적용됐다. 이후 생성하는 신규 태스크가 대상이며, 이 태스크를 포함한 기존 태스크는 저장값(이 태스크는 legacy `actor=pm`)을 유지한다. merge가 반려되면 허브 main에서 install을 다시 실행해 되돌린다.

## 변경 파일

- `opal/tools/state-tool/state_tool.py`, `opal/tools/state-tool/README.md`
- `opal/tools/state-tool/tests/test_start_resolution.py`(신규), `test_state_tool_core_cli.py`, `test_state_tool_extended_contracts.py`, `test_state_tool_mode_contracts.py`
- `opal/tools/worktree-tool/worktree_tool.py`, `opal/tools/worktree-tool/README.md`, `opal/tools/worktree-tool/tests/test_worktree_tool.py`
- `opal/tools/oppb-runtime-tool/tests/test_pilot_isolation.py`
- `opal/core/references/harness/actor.md`, `modes.md`, `worktree.md`, `task-process.md`, `guards.md`, `skill-commands.md`
- `opal/core/references/opal-harness-agentic.md`, `opal-harness-semi-agentic.md`, `opal-harness.md`, `opal-pm.md`, `pm/dispatch-process.md`
- `opal/skills/opal-pilot-dev/SKILL.md`, `opal/skills/opal-pilot-dev/README.md`, `opal/skills/opal-pilot-project-dev/SKILL.md`, `opal/skills/opal-pilot-project-loop/SKILL.md`, `opal/skills/opal-pilot-project-build/SKILL.md`
- `README.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md`, `docs/architecture-diagram/opal_framework_architecture.html`
- `.opal/brain/pages/concept/actor-axis-orthogonal-to-mode.md`, `.opal/brain/pages/entity/opal-self-pm.md`

## 검증

- 목표-커버 게이트: `scenario-coverage-check` exit 0 + opal-evaluator-agent scenario-rubric 2/2/2 pass(i1).
- RED→GREEN: opal-test-agent가 S-1~S-6 RED 작성(state-tool 34 fail, worktree-tool 2 fail) → `scenario-lock` → GREEN 후 `test_start_resolution.py` 23 passed, `-k t156_s6` 3 passed.
- TEST(opal-test-agent 독립 판정): S-1~S-12 12/12 PASS. S-9는 사용자 실설치 후 설치본 `resolve-start` 4종과 source↔installed SHA256 6종 일치로 real-usage PASS. 증거: `run/test-evidence/`.
- 회귀: state-tool 16파일 중 15 PASS, worktree-tool 150, worktree-launcher 148(4 skip), oppb-runtime-tool 142, ownership-tool 165, memory-tool 202, brain-tool 159, event-loader 20, oppl-runtime-tool 45 passed. spec-validate 11/11 pass. 신규 실패 0.
- 기존 실패(main 대조로 동일 재현, 이번 변경 무관): state-tool `TestT138W9*` 3건(세션 환경변수 유입), run-log-tool 5건, `code-scan validate` 1 violation. dashboard `test_routers` 33건은 작업본 경로에서만 실패하며 dashboard 소스 diff 0.
- 컨벤션: opal-convention-checker PASS_WITH_ADVISORIES(Critical/High 0, Low 1 — `state_tool.py` @header의 기존 태스크 번호 누적).
- brain lint: 변경 전후 이슈 목록 동일(320건 모두 기존, 신규 0).
- opal-e2e: 등록 여정 없음·CLI 변경이라 미실행, 실제 CLI 검증 S-1~S-6·S-8·S-9·S-11로 대체(`run/test-evidence/opal-e2e-review.md`).

## 회고적 학습 후보

.opal/brain/pages/concept/new-task-defaults-vs-resume-inheritance.md

## 참고

- 허브 후속: 사용자 승인 뒤 `feat/OP-TASK-156` merge(`--ff-only` 또는 `--no-ff`) → `state-tool finalize-attribution` → `status --set done` → `worktree-tool remove`. merge 뒤 허브 main에서 install을 한 번 더 실행해 설치본 출처를 main으로 맞춘다.
- 기존 환경 의존 실패(state-tool T138 3건, run-log-tool 5건, dashboard 작업본 경로 33건)는 별도 태스크 후보다.
- 설치 스크립트는 `HOME`을 바꾼 격리 설치에서도 7823 콘솔 health를 보고 "기동 완료"를 출력한다(실제 콘솔은 종료하지 않음). 격리 검증 시 오해 소지가 있다.
