---
template: sdlc-v2
---
# TASK: ownership-tool 훅의 런타임 루트를 cwd가 아닌 프로젝트 루트로 해석

## Problem

ownership-tool의 hook 어댑터 5종이 훅 봉투의 `cwd`를 그대로 프로젝트 루트로 채택한다
(`opal/tools/ownership-tool/ownership_tool/stop_hook.py:76`,
`session_start_hook.py:267`, `heartbeat_hook.py:155`, `session_end_hook.py:92`,
`pretooluse_guard_hook.py:213`). Claude Code의 `cwd`는 훅 실행 시점의 작업 디렉토리라
에이전트가 Bash로 하위 디렉토리에 `cd`한 뒤 턴을 끝내면 그 하위 경로가 루트로 채택된다.

관측된 결과는 두 가지다.

1. **런타임 파일이 저장소 임의 위치에 생성된다.** `ownership_core.write_json_atomic`이
   `target.parent.mkdir(parents=True, exist_ok=True)`로 디렉토리 트리를 만들기 때문에
   (`ownership_core.py:184`) `<하위 디렉토리>/.opal/run/.runtime/stop-guard/<sid>.json`이
   생긴다. 외부 프로젝트(storelink) 2026-09-21 세션에서 2회 재현됐고, 두 사례 모두
   gitignore 밖이라 `git status`에 untracked로 노출됐다.
2. **stop guard 판정이 무력화된다.** `stop_evaluator`가 직전 receipt를 같은 잘못된 루트에서
   읽으므로(`stop_evaluator.py:272`) 턴마다 `receipt is None`이 되어
   `prior_block_count`가 0으로 리셋되고(`stop_evaluator.py:274-277`), 연속 차단 상한
   `allow_block_cap_reached`와 무진행 통과 `allow_no_progress_same_fingerprint`가 모두
   발화하지 않는다(`stop_evaluator.py:280-297`). 동시에 `resolve_hub`가
   `<잘못된 루트>/tasks/`를 열어 후보 0건이 되므로 정상 차단도 일어나지 않는다.

부수적으로 `lease.resolve_ttl_sec`가 `<루트>/.opal/setting.local.json`을 읽으므로
(`lease.py:40-41`) heartbeat·PreToolUse 경로에서 프로젝트 TTL 설정이 조용히 무시되고
기본 14400으로 폴백한다.

실측 캡처된 Stop 봉투에는 루트를 알려주는 필드가 `cwd` 하나뿐이므로
(`opal/tools/ownership-tool/tests/fixtures/hook-payloads/stop.json`) 해법은 봉투 밖에서
와야 한다.

## Proposed outcome

에이전트가 프로젝트의 어느 하위 디렉토리에서 턴을 끝내도 다음이 관찰된다.

- stop-guard receipt와 세션 registry가 프로젝트 루트 한 곳에만 기록된다. 하위 디렉토리에
  `.opal/` 디렉토리가 생기지 않으므로 `git status`에 새 untracked 항목이 나타나지 않는다.
- 같은 세션의 연속 Stop이 직전 receipt를 읽으므로 `block_count`가 누적되고 무진행
  동일 fingerprint가 통과 판정된다.
- 프로젝트 `setting.local.json`의 `ownership.lease_ttl_sec`가 cwd와 무관하게 적용된다.
- 루트를 확정하지 못하면 임의 위치에 파일을 쓰지 않는다.

## Affected users and systems

- 영향받는 사용자: OPAL을 쓰는 모든 Claude Code 세션 소유자. 하위 디렉토리에서 턴을 끝내는
  세션이 저장소 오염과 정지 판정 무력화를 동시에 겪는다.
- 영향받는 시스템: `opal/tools/ownership-tool`의 hook 어댑터 5종과 루트를 소비하는
  `fingerprint`·`session_registry`·`lease`·`resolver` 경로. `opal/core/hooks/claude-hooks.json`의
  훅 배선은 명령 문자열 변경이 필요할 때만 포함한다.
- 범위 제외: lease 레코드 경로(`task_path` 절대경로 기준이라 결함 없음), state-tool·brain-tool
  등 ownership-tool 밖 도구의 루트 해석, 이미 생성된 잔여 파일의 일괄 정리.

## Constraints

- C-1: Stop 훅의 전 경로 fail-safe(`except Exception: pass` + `exit 0`, 무출력 통과)를 유지한다.
  루트 미확정을 세션 차단이나 예외로 표현하지 않는다(`stop_hook.py:84-88`).
- C-2: 훅의 유일한 출력 채널은 `{"decision":"block","reason":…}` 1줄이다. 새 출력 채널이나
  새 사용자 게이트를 만들지 않는다.
- C-3: `CLAUDE_` 접두 환경변수명은 `claude_adapter.py`에만 둔다(C-15 기존 계약). 다른 모듈에
  플랫폼 고유 변수명을 노출하지 않는다.
- C-4: `harness/worktree.md` §task root와 allocator root 계약을 약화하지 않는다. 특히
  `allocator_root`를 cwd·task path 조상·`.opal-worktrees` 문자열로 추론하는 경로를 만들지 않는다.
  **[정정 2026-09-23] 이 금지는 `allocator_root` 축 전용이다.** 같은 절의 표는 `task_root`를
  "canonical task path에서 가장 가까운 `.git`·`.opal` 작업본"으로 **정의**하므로, `task_root`
  목적의 조상 탐색은 금지 대상이 아니라 계약이 지시하는 방법이다. 훅 어댑터의 `project_root`는
  `.opal` 설정·state 저장 위치를 정하는 값이므로 `task_root` 축에 속한다(소비자: `session_registry_path`·
  `stop_receipt_path`·`lease.resolve_ttl_sec`). 선례는 `state_tool.py:2696-2710`의 `task_root()`다 —
  조상에서 `.opal/MEMORY.json` 앵커를 찾되 allocator root에는 그 탐색을 쓰지 않는다고 같은
  docstring이 두 축을 병기한다.
- C-5: `resolver.resolve_hub`의 "hub_root는 호출자 인자만 사용한다" 계약과 그 부재를 집행하는
  기존 테스트를 유지한다. **[정정 2026-09-23] 이 제약의 대상은 `resolve_hub`(allocator 축)와
  `resolve_roots`(cwd==루트 전제의 3분기 판정)다.** `task_root` 해석 함수에까지 부모 순회 금지를
  확대 적용하지 않는다 — 확대하면 C-4 정정이 인정한 정의와 모순된다.
- C-6: 루트 해석 실패 시 폴백은 파일을 쓰지 않는 방향으로만 둔다. 임의 위치 생성보다 미기록이 낫다.
- C-7: 기존 ownership-tool 테스트 전건이 통과 상태를 유지한다.

## Acceptance criteria

- AC-1: 프로젝트 하위 디렉토리를 `cwd`로 담은 Stop 봉투로 훅을 실행하면 receipt가
  `<프로젝트 루트>/.opal/run/.runtime/stop-guard/<sid>.json`에만 생성되고, 그 하위 디렉토리
  아래에는 `.opal/` 경로가 생성되지 않는다.
- AC-2: SessionStart·SessionEnd 훅을 하위 디렉토리 `cwd` 봉투로 실행하면 세션 registry가
  `<프로젝트 루트>/.opal/run/.runtime/sessions/<sid>.json`에만 기록·갱신된다.
- AC-3: 같은 `session_id`로 `cwd`가 서로 다른 Stop 2회를 연속 실행하면 2회차가 1회차 receipt를
  읽어 `block_count`가 누적되고, 동일 fingerprint일 때
  `decision_kind=allow_no_progress_same_fingerprint`를 반환한다.
- AC-4: `ownership.lease_ttl_sec`를 설정한 프로젝트에서 하위 디렉토리 `cwd`로 heartbeat 훅을
  실행해도 그 설정값이 적용된다(기본 14400으로 폴백하지 않는다).
- AC-5: 루트를 확정할 수 없는 봉투(환경변수 부재 + 루트 판정 근거 부재)로 Stop 훅을 실행하면
  파일을 하나도 생성하지 않고 무출력 exit 0으로 통과한다.
- AC-6: `grep -rn 'payload.get("cwd")'` 결과에 루트로 채택하는 용도의 잔존 호출이 0건이다
  (cwd 자체를 cwd 의미로 쓰는 호출은 제외).
- AC-7: `CLAUDE_` 토큰이 `claude_adapter.py` 밖 ownership-tool 모듈에 0건이다.
- AC-8: ownership-tool 테스트 전건과 `scripts/tests/test_hook_parity.py`가 통과한다.
