# DONE: `--wt` 전용 세션·Stop 훅 태스크 소유권 결정론화

## 결과

Stop 훅이 `cwd.parents`를 거슬러 올라가 허브 `tasks/`를 스캔하고 `updated_at`이 가장 최신인 태스크를 "이 세션의 태스크"로 지목하던 추론을 제거했다. 소유권은 이제 **발급된 값**으로만 판정한다 — SessionStart가 워크트리 cwd에서 lease를 claim하고 세션 registry에 등재하며, Stop은 그 lease와 세션 생존(TTL)만 본다.

**1호 목표 AC-1 달성**: 허브 실물 읽기전용 실측에서 Task 132가 도입 전 `hub_canonical`·`forced=True`(오탐 차단)였는데, 도입 후 `worktree_owned_shadow`·`forced=False`·`evidence.task_path_ambiguous=True`로 전환됐다.

**신설 도구 2종**
- `ownership-tool` — 12모듈(lease·session_registry·resolver·stop_evaluator·fingerprint·decisions + SessionStart/PostToolUse heartbeat/SessionEnd/PreToolUse/Stop 훅 어댑터)
- `worktree-launcher` — `launcher_core` + 어댑터 3종(orca·generic·opal_agent fallback)

**적용한 경계**
- **D-20** 워크트리는 허브를 추론하지 않는다. 워크트리 생성 시 발급값 사본을 배달받아(W-21) 그것으로 허브를 찾는다.
- **D-21** Stop 강제 차단 후보는 `claim_source=state_transition`일 때만 성립한다. 세션이 부팅만 했다는 사실(`session_start`)은 차단 근거가 아니다.
- **D-18** 세션 ID 해석 순서 고정, **D-19** 패키지 레이아웃 고정.
- PreToolUse 판정은 `Edit|Write|NotebookEdit|Bash` 폐쇄 목록에 한정한다(전면 차단은 기각 — 모든 Bash에 판정 비용 부과).
- 비소유 세션은 읽기(Read/ls)는 통과하고 쓰기·`git commit`만 차단한다. 등록되지 않은 워크트리 밖에서는 I/O 없이 즉시 종료한다.
- 런타임 산출물(`owner.json`·stop-guard receipt·세션 registry)은 전부 기존 `.gitignore` 커버 범위 안에 떨어지며 `.gitignore` 자체를 바꾸지 않는다.

**유지한 기존 동작**: `pipeline.json`/`pipeline-short.json` CLOSE 행의 key·순서·행 개수, `close_final_key`·`semi_agentic_boundary`는 무변경이고 `close.worktree_finalize` item에 "허브 수행" 표식만 붙었다. state-tool의 `ALLOWED_TRANSITIONS`·`_derive_transition`·`cmd_block` 회귀는 535 passed로 고정했다.

**부수로 닫은 main 선존 결함 2건**
- `opal/agents/opal-capability-agent/AGENT.md`에 `worker.dispatch` 계약절이 없어 bootstrap audit이 실패하던 건.
- `scripts/tests/task113_bootstrap_audit.py`가 pilot 10·worker 15를 하드코딩했으나 실측은 11·16이던 stale census. 고정 수치를 `issubset` 커버리지 불변식으로 교체했고, 약화가 아님을 실증했다(pilot 1건을 빼면 누락 경로를 지목하며 실패).

## 변경 파일

- `opal/tools/ownership-tool/**` (신규 68파일 — 구현 12모듈 · `run.sh` · README · tests · fixtures)
- `opal/tools/worktree-launcher/**` (신규 11파일 — `launcher_core`·어댑터 3종 · `run.sh` · README · tests)
- `opal/tools/worktree-tool/worktree_tool.py`, `tests/test_worktree_tool.py`, `README.md`
- `opal/tools/state-tool/state_tool.py`, `tests/test_state_tool.py`, `tests/test_state_tool_ownership.py`(신규), `tests/fixtures/s1_baseline_rows.json`
- `opal/core/hooks/claude-hooks.json`, `claude-hooks.retired.json`
- `opal/core/references/harness/guards.md`, `task-process.md`
- `opal/core/references/opal-harness-agentic.md`, `opal-harness-semi-agentic.md`, `opal-harness-interactive.md`
- `opal/skills/opal-pilot-dev/references/pipeline.json`, `pipeline-short.json`
- `opal/skills/opal-self-pm/SKILL.md`, `docs/CONVENTIONS.md`
- `opal/agents/opal-capability-agent/AGENT.md`
- `scripts/tests/test_hook_parity.py`(신규), `scripts/tests/task113_bootstrap_audit.py`
- `.gitignore`

## 검증

- 시나리오 **29건 중 28 pass · fail 0 · blocked 0 · awaiting_human 1**(`test-scenario.json` 실측 집계). AC 29/29 · C 23/23이 전건 시나리오에 연결된다.
- 스위트 전건 실행(호출 분리 병렬 — 한 pytest 호출로 합치면 conftest 모듈명 충돌로 collection error)
  - `ownership-tool/tests` → **56 passed**
  - `worktree-tool/tests` → **136 passed**
  - `worktree-launcher/tests` → **15 passed**
  - `state-tool/tests` → **535 passed, 3 skipped**
  - `scripts/tests` → **21 passed**
- Work items **22/22 완료** — PLAN의 W-1~W-20 + 실행 중 신설한 W-21(발급값 사본 배달)·W-22(claim 출처 구분).
- 허브 실물 읽기전용 실측으로 AC-1 전후 전환 확인(`hub_canonical`/`forced=True` → `worktree_owned_shadow`/`forced=False`).
- 허브 무쓰기 확인: 작업 전후 `git -C <허브> status --porcelain | wc -l` 동일(42).
- 통합 테스트가 단위 테스트를 통과하던 실결함 2건을 잡았고 둘 다 RED 확보 후 닫았다 — registry receipt가 객체 대신 JSON 문자열로 저장되던 건, SessionEnd로 닫힌 세션 registry가 PostToolUse heartbeat로 되살아나던 건.

## 회고적 학습 후보

.opal/brain/pages/concept/red-corpus-precedes-contract-fabricates-layout.md
.opal/brain/pages/concept/worktree-locates-hub-by-issued-copy.md
.opal/brain/pages/concept/stop-force-requires-state-transition-claim.md
.opal/brain/pages/entity/ownership-tool.md

## 참고

- **S-25 배포 후 수행 결과(2026-09-18 20:2x, 부분 수행 — 4절 중 2절 관측 완료·2절 미수행)**
  - §1 cwd 전달 — **pass**. 워크트리 루트에서 기동된 실제 세션 `07966882-…`의 SessionStart hook이 만든 registry 레코드 `cwd`가 워크트리 루트와 일치(추정 아님, 파일 실측).
  - §1 session ID 전달 — **미충족(플랫폼 측)**. `echo $OPAL_SESSION_ID`가 빈값이고 `~/.claude/session-env/<id>/`가 빈 디렉터리다. 이 Claude Code 빌드가 `CLAUDE_ENV_FILE`을 훅에 주지 않는다. 배포된 훅에 `CLAUDE_ENV_FILE`을 직접 주면 `OPAL_SESSION_ID=<id>` 1줄을 정확히 append하므로 구현 결함이 아니다.
  - §1 Stop hook 발화 — **pass**. 해당 세션 전사에서 Stop hook_success 3회(턴 3회)·전부 exit 0, stop-guard receipt `block_count=0`·`decision_kind=allow_inactive`로 그 시점 소유 태스크 없음과 일치.
  - §4 D-21 조용한 부팅 — **pass**. `claim_source=session_start` 상태에서 배포된 Stop hook stdout 빈값(통과), evaluator 실측 `forced=False`·`classification=current_session_owned` 유지·`diagnostics=[passive_ownership]`.
  - §4 상태 전진 후 차단 — **pass**. `claim_source=state_transition`으로 승격 후 같은 훅이 `{"decision":"block", …block_continue…transition_action=continue…}`를 출력. 동일 상태에서 허브 cwd는 통과(worktree_owned_shadow 비강제) — AC-1 설계와 일치.
  - **부수 실측**: 기존 워크트리(`task_138`)에 D-20 발급값 사본이 없었고, 배포된 `worktree-tool status` 1회로 `.opal/task-ownership.json`이 생성됐다. 백필 트리거가 `create`/`status`뿐이라 배포 직후 기존 워크트리에는 사본 공백 구간이 존재한다.
  - **미수행 2절** — §2 orca `--wt` 실기동 prompt receipt 관측은 실제 터미널 기동과 대상 태스크가 필요하고, S-25 기대결과 (3) `opal-agent --provider claude --cwd <worktree_root> -p`는 **이 머신에 `opal-agent`가 설치돼 있지 않아** 수행 불가다. §3 fixture 실캡처 교체는 S-29 범위다.
- 허브 main이 127 계열로 전진해 **CLOSE 후 main 재병합이 필요**하다.
- RED 코퍼스를 구현 계약보다 먼저 써서 **실재하지 않는 레이아웃·아키텍처를 전제한 사례가 4회**(shadow 술어·워크트리 registry·receipt 가드 우회·launcher 사설 writer) 나왔다. 매번 fixture를 실물에 맞추고 구현을 계약에 맞췄다.
- 개선 후보 3건을 남긴다 — ① `scripts/merge-hooks.py`가 `_help` 등 `_` 접두 키를 이벤트로 순회한다 ② "hook 차단은 PM 승격 근거가 아니다"를 하네스에 명문화해야 한다 ③ 워커마다 같은 스위트를 반복 지시해 중복 실행이 발생했다.
