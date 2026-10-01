---
template: sdlc-v2
---
# TEST-SCENARIO: opd2 프레임워크 통합 — state-tool 단일 상태와 FW 공통 계약 연결

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: 이 리포지토리의 워크트리(`/Volumes/Data/AiStudio/workspace/opal/.opal-worktrees/task_168`). Python 표준 라이브러리만 쓰는 `state-tool`·`opal-pilot-dev2` 패키지이므로 별도 서비스 기동은 불필요하다.
- 공통 데이터: 없음(고정 fixture 불필요 — `state-tool`·`opal-pilot-dev2/tests`가 각자 임시 디렉토리를 사용).
- 대역 사용과 한계: 사용하지 않음. Builder/Verifier/Reviewer 독립 디스패치(S-3의 디스패치 기록 확인)는 실제 Agent 호출 로그로 확인하며 대역으로 대체하지 않는다.
- 실행 조건: 자동 실행. S-3(E2E)은 실제 워크트리 태스크 1건을 생성·완주해야 하므로 실행 시간이 길다 — TEST 진입 시 한 번에 실행한다.

## Scenarios

| ID | 유형 | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|---|
| S-1 | check | AC-1, AC-7, C-1 | W-1(state-tool 식별자)·W-2(registry 등재)·W-3(pipeline.json) 구현 완료 | `~/.opal/.venv/bin/python -m pytest -q opal/tools/state-tool/tests/test_pilot_shared_contract.py` 실행 | 전 클래스(`PilotDiscoveryTest`·`RequiredFilesTest`·`RegistryRegistrationTest`·`PipelineSpecValidateTest`·`EnumConsistencyTest`·`MutualIsolationTest`·`RegistryIntegrityTest`·`FaultIsolationTest`) PASS, exit 0. `opd2`가 `discover_pilots()`에 포함되고 `opal-pilot-dev`·`opal-pilot-dev-short`를 포함한 다른 파일럿의 결과는 이 실행 전후로 바뀌지 않는다 | unit, 실제 `pytest` 실행 | 구현 후 |
| S-2 | check | AC-1 | W-1 구현 완료 | `~/.opal/tools/state-tool/run.sh resolve-start <신규 임시 task_path> --skill opd2 --new-task` 실행(플래그 없음) | JSON 응답의 `effective_mode == "agentic"`, `workspace == "worktree"`. `--wt`와 `--no-wt`를 함께 주면 `workspace_flag_conflict`로 거부(exit 비0) | integration, 실제 CLI 실행 | 구현 후 |
| S-3 | e2e | AC-2, AC-3, AC-4, AC-5, AC-6, H-2 | W-3~W-6 구현 완료, 워크트리 생성 가능한 Git 환경 | `//opd2`로 신규 워크트리 태스크를 시작해 TASK(intent) → DESIGN(spec) → PLAN(plan, Builder/Verifier/Reviewer 지정) → EXECUTE(Builder evidence) → VERIFY(Verifier evidence + Reviewer verdict pass) → CLOSE(DONE.md)까지 실제로 완주하면서, `plan.plan_md` 전이 직전에 대표 게이트 1종(아티팩트 결합 해시 불일치)을 1회 인위로 유발한다 | 매 전이 후 `<task>/state.json`의 해당 `task_steps` 행이 `done`으로 갱신됨. `<task>/.sdlc/`가 생성되지 않음(`ls`로 확인). 인위 유발한 해시 불일치 상태에서는 해당 행이 `done`으로 전이되지 않음(나머지 게이트 항목별 차단은 S-5가 unit에서 검증하므로 여기서는 반복하지 않는다). 첫 상태 전이 시점에 `run/.runtime/owner.json` lease가 현재 세션으로 확보됨. CLOSE 완료 후 `current_status == "completed_unmerged"`이고 `worktree-tool finalize`가 태스크를 인식함(`registered: true`). 실행 중 생성된 디스패치 기록(Agent 호출 로그·`AGENTIC-LOG.md` 상응 기록)을 확인하면 Builder·Verifier·Reviewer 각 역할이 서로 다른 Agent 호출(별도 세션)로 수행되고 어느 호출도 이전 역할의 대화 컨텍스트를 이어받지 않으며, 매 역할 호출 전 `worker.dispatch` 이벤트 load·verify가 선행됨(receipt 존재) | e2e, 실제 워크트리·실제 명령 실행 | 구현 후 |
| S-4 | unit | H-1 | W-4 구현 완료 | `state-tool mark`를 실패하도록 만든 환경(예: `--task-step` 값을 pipeline.json에 없는 키로 주입하거나 실행 파일을 일시 차단)에서 `lifecycle.py transition`을 호출 | 전이가 비0으로 실패하고, 호출 전후 `.sdlc/` 잔존물이 없으며 원장(`<task>/run/opd2-ledger.json`)의 `stage`도 이전 값 그대로 유지됨(원장 커밋 없음) | unit, 실제 `lifecycle.py` 실행 | 구현 후 |
| S-5 | regression | AC-3, C-4 | W-4 구현 완료 | 기존 `test_lifecycle.py`의 차단 검증 스위트(아티팩트 해시 불일치, scope 위반, builder=verifier, builder=reviewer, RED 증거 누락, evidence 누락, 검증 후 소스 변경, 로그 변조, 보호 테스트 수정, 최신 리뷰 fail, 재시도 상한 4회째)를 실행 | 이전 `.sdlc/` 기반 구현과 동일하게 전 항목이 차단됨(exit 비0, 기대 오류 코드 일치). `intent.schema.json`·`spec.schema.json`·`plan.schema.json`·`evidence.schema.json` 4종은 이 태스크로 수정되지 않음(`git diff --stat`으로 확인) | unit, 실제 `python3 -m unittest discover -s opal/skills/opal-pilot-dev2/tests -v` 실행 | 구현 후 |
| S-6 | integration | AC-6 | W-5 구현 완료 | `opal-pilot-dev2`에 `delivery=release`(배포 요청)를 명시해 시작 | SKILL.md 진입 절차가 "미지원"으로 명시 거부하고 `state-tool`에 release 관련 행을 만들지 않음. 배포 완료로 보고되지 않음 | integration, 실제 실행 1회 + SKILL.md 거부 문면 확인 | 구현 후 |
| S-7 | check | AC-8 | W-7, W-8 구현 완료 | `docs/PROJECT.md`·`opal/core/references/harness/modes.md`·`harness/worktree.md`·`harness/skill-commands.md`·`opal/skills/opal-pilot-dev2/README.md`를 grep | `docs/PROJECT.md` Dev 파이프라인 오케스트레이터 표에 `opal-pilot-dev2`/`opd2` 행 존재. `modes.md` §신규 태스크 기본 mode 표와 `worktree.md` §신규 태스크 기본 workspace 표의 해당 행에 `opd2` 포함. `skill-commands.md`에 `opd2` 언급 존재. `README.md` 파일 존재 및 비어있지 않음 | check, 정적 검사 | 구현 후 |
| S-8 | regression | C-1 | W-1 구현 완료 | `git diff main -- opal/tools/state-tool/state_tool.py`로 변경분을 확인 | `STAGE_ENUM`·`MODE_BOUNDARY_STAGES`·`ACTOR_SKILLS`·`WORKSPACE_REQUIRED_SKILLS`와 `opd`·`opds`·`oppd`·`oppl`·`oppb` 등 기존 `NEW_TASK_DEFAULTS` 항목 값에 diff가 없다(추가 라인만 존재). `apply_opd2_gate_mark_guard`의 신규 분기는 `skill=="opd2"` 조건 안에서만 동작해 다른 Pilot의 `cmd_mark` 경로를 바꾸지 않는다(코드 리뷰로 확인) | check, `git diff` 정적 검사 | 구현 후 |
| S-9 | integration | AC-1 | W-1 구현 완료, S-2에서 만든 기존 opd2 태스크 | 기존 opd2 태스크(`workspace: worktree` 저장됨)를 `~/.opal/tools/state-tool/run.sh resolve-start <task> --skill opd2`(무플래그 재개)와 `--no-wt`(다른 workspace 플래그)로 각각 재실행 | 무플래그 재개는 저장된 `mode`·`workspace`를 그대로 상속한 JSON을 반환(exit 0). `--no-wt`는 `resume_axis_locked`로 거부(exit 비0)되고 태스크의 작업본을 옮기지 않는다 | integration, 실제 CLI 실행 | 구현 후 |
| S-10 | check | AC-3 | W-1 구현 완료(opd2 gate mark 가드), 새 opd2 태스크의 `execute.implement`가 pending 상태 | `lifecycle.py`를 거치지 않고 `~/.opal/tools/state-tool/run.sh mark <task> --task-step execute.implement --done --force --note <사유>`를 직접 호출(이어서 `--auto-pass`·`--as-worker` 조합도 각각 시도) | 매 시도가 `opd2_gate_record_required`로 거부됨(exit 비0). 거부 전후 `<task>/state.json`의 `execute.implement` 행 상태가 바뀌지 않음(`pending` 유지) | check, 실제 CLI 실행 + `state.json` diff 확인 | 구현 후 |
| S-11 | e2e | AC-4 | S-3 진행 중(EXECUTE 또는 VERIFY 단계 진행 중) | 워크트리 세션이 살아있는 상태에서 세션 종료(Stop)를 시도 | Stop 판정이 종료를 차단하고 재개 안내(`transition_action`/다음 액션 등)를 반환함(`ownership-tool` Stop 판정, 일반 메커니즘 — skill 분기 없음). 태스크 완료 후 재시도하면 정상 종료됨 | e2e, 실제 세션 종료 시도 | 구현 후 |
| S-12 | e2e | AC-4 | S-3의 PLAN 완료 직후 같은 워크트리 세션 | 현재 세션이 `worktree-tool checkpoint`를 안정 경계(PLAN 완료 직후)에서 호출 | 커밋이 성공하고 registry `checkpoint_shas[]`에 새 SHA가 append됨(exit 0). 소유권·브랜치 일치·staged 범위 검사를 통과함(`checkpoint_ownership_denied`·`checkpoint_branch_mismatch`·`checkpoint_scope_violation` 없음) | e2e, 실제 checkpoint 호출 | 구현 후 |
| S-13 | check | C-2, C-3 | W-1~W-10 구현 완료 | 이 태스크가 변경한 전 파일에 `git diff main`을 적용해 플랫폼 분기 리터럴(`if platform ==`·`claude`/`cursor`/`gemini` 하드코딩 분기 등)과 `state.json` 직접 파일 쓰기(state-tool CLI를 거치지 않는 `open(...).write` 패턴) 존재 여부를 grep | 플랫폼 전용 분기가 어댑터 계층 밖(opd2 스킬 본문·lifecycle.py)에 추가되지 않았고, `lifecycle.py`의 상태 갱신이 전부 `state-tool` CLI 호출을 경유함(직접 `state.json` write 없음) | check, 정적 검사 | 구현 후 |
