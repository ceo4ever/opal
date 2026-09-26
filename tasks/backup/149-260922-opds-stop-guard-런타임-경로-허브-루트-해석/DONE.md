# DONE: ownership-tool 훅의 런타임 루트를 cwd가 아닌 프로젝트 루트로 해석

## 결과

훅 어댑터 5종이 훅 봉투의 `cwd`를 무검증으로 프로젝트 루트에 채택하던 경로를 끊었다. 봉투 `cwd`는
훅 발화 시점의 작업 디렉토리라, 에이전트가 하위 디렉토리로 이동한 뒤 턴을 끝내면 그 하위 경로가
루트가 되어 ⑴ `<하위>/.opal/run/.runtime/…`에 런타임 파일이 생기고(레포 루트 고정 패턴인
`.gitignore:2`의 `.opal/*`가 하위를 덮지 않아 `git status`에 untracked로 노출된다) ⑵ stop guard가
직전 receipt를 잘못된 루트에서 찾아 `block_count`가 매 턴 0으로 리셋되며 ⑶ 프로젝트
`setting.local.json`의 `ownership.lease_ttl_sec`가 조용히 무시됐다.

루트 해석을 `ownership_core.resolve_project_root(payload, env=None)` 한 곳으로 모았고, 해석 방법은
**조상 탐색**이다 — ① 명시 오버라이드 `OPAL_PROJECT_ROOT` → ② 봉투 `cwd`부터 조상으로 올라가며
`.opal/MEMORY.json` 또는 `.opal/AGENT.md`를 **파일로** 가진 첫 디렉토리 → ③ `None`. 해석된 루트는
`handle()` 내부의 루트 파생 호출 6곳과 `lease.claim(claimant_root=)`에도 전파된다.

**유지한 것**: `resolve_roots`의 시그니처·3분기·반환 키, `resolver.resolve_hub`의 호출자 인자 전용
계약, 훅의 전 경로 fail-safe(`except Exception: pass` + `exit 0`), 단일 출력 채널
(`{"decision":"block","reason":…}` 1줄), `payload.get("cwd") or project_root` 6곳(cwd를 cwd 의미로
쓰는 의도된 잔존), 태스크 150의 이관(handoff) 수용 계약.

**적용한 경계**: 루트를 확정하지 못하면 어댑터 `main()`이 파일 I/O 이전에 무출력·exit 0으로
종료한다. 임의 위치 생성보다 미기록이 낫다는 판단이며, `state_tool.task_root()`가 `None`일 때
"호출자는 subprocess를 아예 띄우지 말고 조기 반환"하는 것과 같은 계약이다. 보강 방어선으로
`session_registry.register`·`fingerprint.save_receipt`도 falsy 루트를 `no_project_root`로 거부한다.

**플랫폼 독립성**: 초판 설계는 `CLAUDE_PROJECT_DIR`를 해석 체인에 넣었으나 폐기했다(PLAN D-30d).
조상 탐색은 전 플랫폼에서 성립하지만 플랫폼 변수는 그렇지 않아, 루트 해석을 그쪽에 묶으면 단일
실패점이 되고 `docs/PROJECT.md` 프로젝트 원칙 3과 충돌한다. `claude_adapter.py`는 무변경이다.

## 변경 파일

- `opal/tools/ownership-tool/ownership_tool/ownership_core.py`
- `opal/tools/ownership-tool/ownership_tool/stop_hook.py`
- `opal/tools/ownership-tool/ownership_tool/session_start_hook.py`
- `opal/tools/ownership-tool/ownership_tool/heartbeat_hook.py`
- `opal/tools/ownership-tool/ownership_tool/session_end_hook.py`
- `opal/tools/ownership-tool/ownership_tool/pretooluse_guard_hook.py`
- `opal/tools/ownership-tool/ownership_tool/session_registry.py`
- `opal/tools/ownership-tool/ownership_tool/fingerprint.py`
- `opal/tools/ownership-tool/tests/test_root_resolution.py` (신규)
- `opal/tools/ownership-tool/tests/test_stop_hook_process.py`
- `opal/tools/ownership-tool/tests/test_session_start.py`
- `opal/tools/ownership-tool/tests/test_heartbeat.py`
- `opal/tools/ownership-tool/tests/test_pretooluse_guard.py`
- `opal/tools/ownership-tool/README.md`

## 검증

- `~/.opal/.venv/bin/python -m pytest opal/tools/ownership-tool/tests -q` → **114 passed**
  (착수 기준선 100 passed에서 신규 14건 추가, 실패 0)
- `~/.opal/.venv/bin/python -m pytest scripts/tests/test_hook_parity.py -q` → **20 passed** (무회귀)
- AC-6 `grep -rn 'payload.get("cwd")' ownership_tool/*.py | grep -v 'payload.get("cwd") or project_root'`
  → `ownership_core.py:423` **1행**(승인된 유일한 루트 후보 판독 지점)
- AC-7 `grep -rn 'CLAUDE_' ownership_tool/*.py | grep -v claude_adapter.py` → **0건**
- `code-scan validate --changed <변경 .py> --json` → `ok: true`, `newly_uncovered: 0`
  (`pre_existing` 1건은 `test_pretooluse_guard.py`의 기존 `# @header` 줄 주석 형식, 비차단)
- 시나리오 판정(`test-scenario.json`, `locked: true`) → `passed: 11, failed: 0, blocked: 1`,
  `red_confirmed_required: 9/9`. 훅 진입점을 `subprocess`로 실제 실행한 S-4~S-8·S-12는
  `fidelity: real-usage`
- RED-first 집행: RED 9건을 실제 실패로 관찰한 뒤 `scenario-lock`으로 동결하고 GREEN에 착수했다.
  GREEN 전 구간에서 기존 assertion 삭제 0건 —
  `git diff -- opal/tools/ownership-tool/tests/ | grep '^-' | grep assert`가 빈 출력이다
- 설계 검증점: T147 회귀 4건이 **assertion 무변경**으로 복구됐다
  (`git diff -U0 -- tests/test_stop_hook_process.py | grep '^-'` 빈 출력). 초판 env 체인에서는
  `CLAUDE_PROJECT_DIR` 주입 없이 영구 실패하던 구간이다
- 컨벤션 자동 진단 `GC-CONVENTION-20260923-0807.md` → Critical 0 / High 1 / Medium 1 / Low 1.
  **이 보고서는 수정 이전 스냅샷이다.** High(GC-001 — 어댑터 5종 `@header`가 폐기된 4단계 체인을
  서술)와 Medium(GC-002 — RED-first 잔존 서술)은 수정 후 PM 결정론 재검증으로 해소했다:
  구식 문구 grep 0건, RED 잔존 grep 0건, 114 passed 유지. Low(GC-003 — 테스트 헤더 형식 2종 혼재)는
  범위 밖으로 미처리다

## 회고적 학습 후보

.opal/brain/pages/concept/hook-runtime-root-is-task-root-not-allocator-root.md
.opal/brain/pages/concept/ancestor-search-beats-platform-env-for-root-resolution.md
.opal/brain/pages/entity/ownership-tool.md

## 참고

- **S-13 미실행(blocked)** — "재배포 후 실제 세션에서 `git status` 새 untracked `.opal/` 0건 +
  루트 receipt `block_count` 누적"은 `install-mac.sh` 재배포가 선행이고 배포는 소유자 승인
  경계다(`harness/guards.md` §커밋 규칙). AC 커버리지 공백은 없다 — AC-1은 S-5가, AC-3은 S-6이
  `real-usage`로 이미 판정했고 S-13은 PLAN `Release and recovery`의 배포 후 확인 항목이다.
  **merge 후 허브에서 install하고 1회 관찰할 것.**
- **배포 시 주의** — `scripts/install-mac.sh:1364`의 `install_dir "$opal_dir/tools" "$opal_home/tools"`는
  `tools/` 전체를 덮는다. CLOSE 시점 허브에 태스크 151(`tasks/151-260923-oppm-FW-검토개선-결정론화/`)이
  `harness/pm-review-gate.md`·`harness/worktree.md`·`harness/header-rules.md`·
  `test-tool/lib/scenario.py`를 미커밋으로 보유 중이었다. **149 워크트리에서 install하면 151의
  미배포 변경을 되돌린다** — merge 후 허브에서 실행할 것.
- **TASK.md C-4·C-5 정정** — 초판은 `allocator_root` 전용 금지(`worktree.md` §task root와
  allocator root 계약)를 `task_root` 문제에 적용했다. 같은 절의 표가 `task_root`를 "가장 가까운
  `.git`·`.opal` 작업본"으로 **정의**하므로 조상 탐색은 금지 대상이 아니라 계약이 지시하는
  방법이다. 이 범주 오류가 PLAN 초판(D-22~D-24)의 env 체인을 낳았고, 지적을 받아 PLAN 단계로
  되돌려 D-30으로 대체했다. D-25~D-28은 유효 유지했다.
- `OPAL_PROJECT_ROOT`를 실제로 세팅하는 주체가 저장소에 없다(읽는 곳 2곳, 쓰는 곳 0곳).
  현재는 테스트·수동 오버라이드 전용이며, 필요해지면 별도 태스크 사안이다.
