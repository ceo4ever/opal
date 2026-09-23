---
template: sdlc-v2
---
# PLAN: ownership-tool 훅의 런타임 루트를 cwd가 아닌 프로젝트 루트로 해석

> 입력: [TASK.md](TASK.md) (ANALYSIS 없음 — opds Short profile)

## Approach

훅 어댑터 5종의 결함은 전부 각 모듈의 `main()` 한 줄에 모여 있다
(`stop_hook.py:76`, `session_start_hook.py:272`, `heartbeat_hook.py:155`,
`session_end_hook.py:92`, `pretooluse_guard_hook.py:213` — 모두 `project_root = payload.get("cwd")`).
`handle()`/`evaluate()`는 이미 `project_root`를 인자로 받으므로, 이 다섯 줄을 **공통 루트
해석 함수 한 개**로 교체하면 판정·저장 계층은 손대지 않고 결함이 닫힌다. 기존 테스트가
`handle(..., project_root=…)`로 직접 호출하는 계층도 그대로 유지된다(C-7).

루트 해석은 `ownership_core.resolve_roots`를 확장하지 않는다. `resolve_roots`는 "cwd가
루트일 때 허브인지 워크트리인지"를 판정하는 3분기 SSOT이고(`ownership_core.py:289-343`),
그 판정 성격을 바꾸지 않는다. 대신 같은 모듈에 `resolve_session_id`(`ownership_core.py:350-367`)와
같은 자리에 `resolve_project_root(payload, env)`를 신설한다.

**[개정 2026-09-23 — D-30]** 초판은 이 함수를 `OPAL_PROJECT_ROOT` → `CLAUDE_PROJECT_DIR` →
`resolve_roots(cwd)` 자기증명 → `None`의 4단계 env 체인으로 설계했다. 그 설계는 폐기한다.
근거는 §Decisions and contracts D-30이며, 요지는 훅의 `project_root`가 `allocator_root`가 아니라
**`task_root`** 축이고 `task_root`의 결정 방법은 계약상 **조상 탐색**이라는 것이다. 초판은
`allocator_root` 전용 금지(C-4·C-5)를 `task_root` 문제에 잘못 적용해, 금지를 우회하려고
플랫폼 env에 의존하는 체인을 만들었다.

범위는 루트의 **출처 교체**까지다. `project_root`를 저장소 루트와 허브 registry 루트로
쪼개는 재설계는 하지 않는다(PRINCIPLES §3 — 계획이 지목한 것만 만진다). README의 낡은
CLI 서술(태스크 150이 무효화) 정정도 이 태스크에서 하지 않는다.

## Decisions and contracts

> **개정 이력**: D-22·D-23·D-24는 2026-09-23 D-30으로 대체됐다. 아래 표에 원문을 남겨 두는 것은 폐기 근거를 추적하기 위함이며, 구현 기준은 D-30이다. D-25~D-29는 유효하다.

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| **[폐기 — D-30이 대체]** D-22. 단일 진입점은 신규 `ownership_core.resolve_project_root(payload, env=None)`. `resolve_roots`는 시그니처·분기 무변경 | 훅 어댑터 5종의 `main()`은 이 함수만으로 루트를 얻는다. 다른 모듈은 루트를 스스로 만들지 않는다 | `resolve_roots`의 3분기는 cwd==루트 전제의 판정 SSOT이며 "어느 분기에서도 추론하지 않는다"가 AST 테스트로 집행된다(`ownership_core.py:298-301`). 확장은 C-5 집행 테스트와 정면 충돌한다. 신설 함수는 `resolve_session_id`의 ①중립 env ②플랫폼 어댑터 ③봉투 체인을 그대로 복제한 형태라 새 패턴이 아니다 |
| **[폐기 — D-30이 대체]** D-23. 해석 체인은 4단계 — ① `env["OPAL_PROJECT_ROOT"]` ② `claude_adapter.project_dir_from_env(env)` ③ 봉투 `cwd`(단 `resolve_roots(cwd)["ok"]`가 True일 때만) ④ 없으면 `None` | ①②는 존재하는 디렉토리일 때 그대로 채택한다(명시 전달값). ③은 `<cwd>/.opal-worktrees/.meta/` 또는 `<cwd>/.opal/task-ownership.json`이 있을 때만 채택한다 | ①②는 호출자·플랫폼이 **명시 제공**한 값이므로 `worktree.md` §task root와 allocator root 계약의 "명시 인자로 전달한다"를 만족한다. ③은 발급 사본·허브 meta라는 **디스크 증거**로만 성립하므로 추론이 아니다. 하위 디렉토리에는 두 증거가 모두 없으므로 ③이 성립하지 않고, 결함이 남긴 오염(`<하위>/.opal/run/.runtime/…`)은 `task-ownership.json`이 아니라 증거로 오인되지 않는다 |
| **[폐기 — D-30이 대체]** D-24. `CLAUDE_PROJECT_DIR` 이름은 `claude_adapter.py`에만 둔다 — `PROJECT_DIR_ENV` 상수와 `project_dir_from_env(env)` 추가, `exports`에 반영 | `ownership_core`를 포함한 어느 모듈에도 플랫폼 고유 변수명이 등장하지 않는다 | C-3(=기존 C-15). `SESSION_ID_ENV`(`claude_adapter.py:13`)와 동일 패턴 |
| D-25. 루트 미확정은 `None` 반환이다. 어댑터 `main()`은 기존 `if not project_root: return` 형태를 그대로 유지해 **파일 I/O 이전에** 종료한다 | 루트 미확정 세션은 파일 0건, 무출력, exit 0으로 통과한다. 새 출력 채널·게이트·예외를 만들지 않는다 | C-1·C-2·C-6, AC-5. 집행 계층을 어댑터 진입점 한 곳으로 고정하면 판정·저장 계층에 루트 개념이 새지 않는다 |
| D-26. `write_json_atomic`은 변경하지 않는다. 대신 `session_registry.register`와 `fingerprint.save_receipt`가 falsy `project_root`에 대해 파일을 만들지 않고 구조화 거부(`{"ok": False, "error": "no_project_root"}`)를 돌려준다 | 저장소 쓰기 2함수는 루트 없이 호출되면 무기록이다 | `write_json_atomic`은 `hub_lease_path` 등 절대경로 사용처와 공유되는 범용 유틸이라 루트 개념을 넣을 위치가 아니다. D-25의 보강 방어선이며 단독 집행선이 아니다 |
| D-27. `handle()` 안의 **루트 파생 해석**은 모두 `root`를 받는다 — `session_start_hook.py:234`(`_canonical_task_path`)·`:248`(`_register_registry_owner`), `heartbeat_hook.py:132`·`session_end_hook.py:68`(`owned_task_paths`), `pretooluse_guard_hook.py:136`(`resolve_roots`)·`:151`(`_canonical_task_path`) | `cwd` 지역변수는 `SessionRecord.cwd` 기록(`session_registry.py:34`)과 `evidence["cwd"]`에만 남는다 | AC-6의 제외 대상 6곳(`payload.get("cwd") or project_root`)은 그대로 두되, 그 값이 루트로 흘러가는 경로만 끊는다. `root = project_root if project_root is not None else cwd` 폴백을 유지하므로 `project_root` 없이 호출하는 기존 테스트는 종전 동작 그대로다(C-7) |
| D-28. `lease.claim(..., claimant_root=)`에는 해석된 `root`를 넘긴다(`session_start_hook.py:244`) | 이관 수용 판정의 입력은 봉투 cwd가 아니라 세션 루트다 | `_root_accepts`는 realpath 동치 또는 하위를 수용한다(`lease.py:134-148`). 이관 대상은 registry 발급 워크트리 루트이므로 해석된 루트는 **동치** 케이스로 수용되고, 종전 하위 cwd 수용 케이스와 결과가 같다 — 150의 이관 계약(`worktree.md` §이관)을 약화하지 않는다 |
| D-29. SessionStart env 프리앰블에 루트 줄을 추가하지 않는다 | `_append_session_id`는 `OPAL_SESSION_ID` 1줄만 계속 쓴다(`session_start_hook.py:174-189`) | 그 파일은 Bash 도구의 **부모 쉘이 source하는 프리앰블**이고 훅 프로세스는 플랫폼이 직접 spawn하므로 상속되지 않는다. 훅이 읽지 못하는 두 번째 소스만 늘어난다. 부트스트랩 순환(Q3)은 ②가 SessionStart를 포함한 전 훅에 동일하게 주어지므로 발생하지 않는다 |

### D-30 (개정 2026-09-23) — 루트 해석을 조상 탐색으로 교체하고 D-22~D-24를 대체한다

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| D-30a. 훅의 `project_root`는 `allocator_root`가 아니라 **`task_root`** 축이다 | 해석 방법은 `harness/worktree.md` §task root와 allocator root 계약 표의 `task_root` 행을 따른다 | 실측 용처가 셋 다 `.opal` 설정·state다 — `session_registry_path`(`ownership_core.py:40-42`)·`stop_receipt_path`(`:50-52`)·`lease.resolve_ttl_sec`(`lease.py:40-41`). 표의 `task_root` 소비자 칸("state의 설정·gate")에 해당하고 `allocator_root` 소비자(채번·merge history)에는 걸치지 않는다 |
| D-30b. `resolve_project_root(payload, env=None)`는 **① 명시 오버라이드 `OPAL_PROJECT_ROOT` → ② 봉투 `cwd`에서 시작하는 조상 탐색 → ③ `None`** 3단계다 | 조상 탐색은 `cwd` 자신부터 위로 올라가며 **`.opal/MEMORY.json` 또는 `.opal/AGENT.md`를 파일로 가진 첫 디렉토리**를 채택한다. 파일시스템 루트에서 멈추고 예외를 던지지 않는다 | `task_root`의 정의가 "가장 가까운 `.git`·`.opal` 작업본"이다. 선례는 `state_tool.py:2696-2710` `task_root()` — 같은 docstring이 "이 탐색은 task root 목적 전용이며 allocator root는 이 함수로 구하지 않는다"로 두 축을 병기한다 |
| D-30c. 앵커는 **마커 파일**이지 `.opal/` 디렉토리 존재가 아니다 | `.opal/MEMORY.json`·`.opal/AGENT.md`만 앵커로 인정한다 | 이번 결함이 하위에 만드는 오염은 `<하위>/.opal/run/.runtime/…`뿐이고 마커 파일은 만들지 않는다. 디렉토리 존재를 앵커로 쓰면 오염된 하위가 루트로 승격돼 결함이 자기증식한다 |
| D-30d. `CLAUDE_PROJECT_DIR`와 `claude_adapter.project_dir_from_env`를 **도입하지 않는다** | `claude_adapter.py`는 초판 이전 상태로 되돌린다 | 조상 탐색이 전 플랫폼에서 성립하므로 플랫폼 변수가 불필요하다. 훅 배선은 현재 `opal/core/hooks/claude-hooks.json` 하나뿐이지만 부트스트래퍼는 4종(claude·codex·cursor·gemini)이라, 루트 해석을 Claude 변수에 의존시키면 `docs/PROJECT.md` 프로젝트 원칙 3 "플랫폼 독립성"과 충돌한다. C-3은 이름 격리이지 의존 격리가 아니다 |
| D-30e. `OPAL_PROJECT_ROOT`는 유지하되 **명시 오버라이드 전용**이다 | 저장소에 이 변수를 쓰는 주체는 없다(실측: 읽는 곳 2곳, 쓰는 곳 0곳). 테스트와 수동 오버라이드용으로만 남긴다 | 조상 탐색이 기본 경로이므로 env는 생명선이 아니라 예외 처리 수단이다 |
| D-30f. **유효 유지** — D-25(미해석 시 어댑터 진입점 종료)·D-26(저장소 쓰기 falsy 가드)·D-27(해석 루트 내부 전파)·D-28(`claimant_root=root`) | 그대로다 | 이 넷은 "루트를 어떻게 구하나"와 독립이며 이미 구현·검증됐다 |

폐기한 대안 3건. `transcript_path`의 project slug 역산은 문자열 추론이라 C-4와
`.opal/brain/pages/entity/ownership-tool.md`의 "추론하지 않는다" 경계를 깬다. 세션 registry
역조회는 registry 위치 자체가 루트를 요구해 순환한다. **[개정] 세 번째 폐기 대안은 초판의 `CLAUDE_PROJECT_DIR` 의존 체인 자체다(D-30d) — 플랫폼 독립성 원칙과 충돌하고, 평범한 프로젝트에서 자기증명 증거 2종이 모두 없어 단일 실패점이 된다.**

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. 플랫폼 루트 변수 실측 | BE | `{태스크폴더}/evidence/hook-env/` (증거만) | 훅 1종을 실제 Claude Code 세션에서 1회 실행해 훅 프로세스 env에 `CLAUDE_PROJECT_DIR`가 주입되는지와 그 값이 프로젝트 루트인지 캡처한다. 캡처 방식은 태스크 147 선례를 따른다(`opal/tools/ownership-tool/tests/fixtures/hook-payloads/stop.json`의 `_fixture.capture_method`) — 임시 훅 등록 후 즉시 원복, 값은 경로 placeholder로 정규화. **부재로 확인되면 즉시 blocked 반환**하고 D-23 ②를 재승인받기 전까지 W-2를 시작하지 않는다 | 없음 | P1 | AC-3, AC-4 |
| W-2. 루트 해석 단일 진입점 신설 **(개정 D-30)** | BE | `opal/tools/ownership-tool/ownership_tool/ownership_core.py` | `resolve_project_root(payload, env=None)`을 D-30b의 **3단계**로 구현한다 — ① `env["OPAL_PROJECT_ROOT"]`가 실제 디렉토리면 채택 ② 봉투 `cwd`부터 조상으로 올라가며 `.opal/MEMORY.json` 또는 `.opal/AGENT.md`를 **파일로** 가진 첫 디렉토리를 채택(D-30c) ③ 없으면 `None`. 예외를 던지지 않는다. `resolve_roots`의 시그니처·3분기·반환 키는 무변경이고 `resolve_project_root`는 더 이상 `resolve_roots`를 호출하지 않는다. `claude_adapter.py`의 `PROJECT_DIR_ENV`·`project_dir_from_env`는 **제거**한다(D-30d). `@header.exports`·`description`을 두 파일 모두 실제 사실로 갱신한다 | 없음 | P2 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-7, C-3, C-4, C-5, C-6 |
| W-3. 어댑터 5종 배선 교체 | BE | `.../stop_hook.py`, `.../session_start_hook.py`, `.../heartbeat_hook.py`, `.../session_end_hook.py`, `.../pretooluse_guard_hook.py` | 각 `main()`의 `project_root = payload.get("cwd")`(`stop_hook.py:76`, `session_start_hook.py:272`, `heartbeat_hook.py:155`, `session_end_hook.py:92`, `pretooluse_guard_hook.py:213`)를 `ownership_core.resolve_project_root(payload, os.environ)`로 바꾸고 falsy면 종전과 같이 즉시 `return`한다(D-25). D-27대로 `handle()` 안의 루트 파생 호출 6곳(`session_start_hook.py:234`·`:248`, `heartbeat_hook.py:132`, `session_end_hook.py:68`, `pretooluse_guard_hook.py:136`·`:151`)의 인자를 `cwd`에서 `root`로 바꾸고, `session_start_hook.py:244`의 `claimant_root`도 `root`로 바꾼다(D-28). `payload.get("cwd") or project_root` 6곳과 `except Exception: pass` + `sys.exit(0)` 구조는 유지한다. 각 모듈 `@header.description`에 루트 출처를 반영한다 | W-2 | P3 | AC-1, AC-2, AC-3, AC-4, AC-6, C-1, C-2 |
| W-4. 저장소 쓰기 미기록 보강 | BE | `.../session_registry.py`, `.../fingerprint.py` | `register`(`session_registry.py:34`)와 `save_receipt`(`fingerprint.py:110`) 진입부에 falsy `project_root` 가드를 넣어 `{"ok": False, "error": "no_project_root"}`를 돌려주고 경로 계산·쓰기를 하지 않는다. `write_json_atomic`(`ownership_core.py:170`)과 경로 계산 함수는 변경하지 않는다 | W-2 | P3 | AC-5, C-6 |
| W-5. 회귀·신규 테스트 **(개정 D-30)** | BE | `opal/tools/ownership-tool/tests/test_root_resolution.py`, `.../tests/test_stop_hook_process.py` | S-9 테스트를 D-30b 3단계로 재작성한다 — `resolve_project_root`에 대한 `.parents` 금지 AST 검사를 **제거**하고(조상 탐색이 정의이므로 금지 대상이 아니다, C-5 정정) 대신 ⑴ 평범한 프로젝트 하위 cwd → 마커 보유 조상 채택 ⑵ 오염된 `<하위>/.opal/run/.runtime/`만 있는 cwd → 앵커 아님(D-30c) ⑶ 워크트리 안 하위 cwd → 허브가 아니라 워크트리 `.opal`이 먼저 잡힘 ⑷ 앵커 전무 → `None`을 검증한다. `resolve_roots`·`resolve_hub`에 대한 기존 AST·계약 검사는 **그대로 유지**한다. S-6(캡슐·lease 누락)·S-12(벽시계 의존 TTL) 픽스처 버그를 고친다. **T147 회귀 3건은 픽스처를 고치지 않는다** — D-30 적용만으로 통과해야 하며 통과하지 않으면 설계 오류로 보고한다 | W-2, W-3, W-4 | P4 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, C-4, C-5, C-7 |
| W-6. 루트 해석 계약 문서화 | 문서(PM 직접) | `opal/tools/ownership-tool/README.md` | `## 세션 ID 해석 (PLAN D-18)` 절 뒤에 `## 실행 루트 해석` 절을 신설해 D-30b 3단계(명시 오버라이드 → 조상 탐색 → 미해석)와 "미확정이면 기록하지 않는다"(D-25·D-26)를 적는다. `## 런타임 저장소 3경로 (PLAN D-5)`에 `project_root`의 출처가 `resolve_project_root`임을 한 줄 추가한다. 루트 계약 원문은 복제하지 않고 `opal/core/references/harness/worktree.md` §task root와 allocator root 계약을 가리킨다. CLI 절과 lock 절은 건드리지 않는다 | W-2 | P4 | C-4, C-6 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-2. 하위 cwd에서 PreToolUse 가드가 지금까지 무음 통과하던 구간이 복구되면 새 차단이 발생한다 | `pretooluse_guard_hook.py:136`·`:151`이 루트로 해석되면 타 세션 소유 태스크에 대한 쓰기가 하위 디렉토리에서도 차단된다 | 하위 디렉토리에서 작업하던 기존 세션이 갑자기 `permissionDecision: deny`를 받을 수 있다 | 의도된 복구이므로 되돌리지 않되, W-5에서 차단 조건이 `worktree.md` §가드 적용 범위("쓰기 차단은 lease가 타 세션 소유로 판정될 때만 발동한다. 이관 중(무소유)과 만료는 차단 대상이 아니다")와 동일한지 회귀로 고정한다 |

> **[폐기 2026-09-23] 초판 위험 가설 1번(플랫폼 env 주입 전제)** — "Claude Code가 훅 프로세스 env에 `CLAUDE_PROJECT_DIR`를 주입하고 그 값이 세션 프로젝트 루트다"는 D-30d가 그 의존 자체를 제거하면서 소멸했다. 조상 탐색은 플랫폼 env를 읽지 않으므로 검증할 전제가 없다. 조사 기록은 `evidence/hook-env/W1-FINDINGS.md`에 남긴다 — 그 문서의 결론은 여전히 사실이나 이제 설계 입력이 아니다. 가설 번호를 본문에 다시 쓰지 않는 것은 커버리지 빌더가 `H-N` 토큰을 위험 목록으로 수집하기 때문이다.

## Release and recovery

- 적용 순서: P1(W-1 실측) → P2(W-2) → P3(W-3·W-4 병렬) → P4(W-5·W-6 병렬) → `scripts/install-mac.sh`로 `~/.opal` 재배포. 소스만 수정하고 `~/.opal/`을 직접 편집하지 않는다(`.opal/AGENT.md` §금지사항).
- 검증 범위: 결정론 — `~/.opal/.venv/bin/python -m pytest opal/tools/ownership-tool/tests -q` 전건(150이 늘린 `test_lease.py`·`test_integration.py`·`test_session_start.py`·`test_pretooluse_guard.py`·`test_heartbeat.py`·`test_cli.py` 포함)과 `scripts/tests/test_hook_parity.py`(AC-8). 기계 검사 2건(Q5) — AC-6은 `grep -rn 'payload.get("cwd")' opal/tools/ownership-tool/ownership_tool/*.py | grep -v 'payload.get("cwd") or project_root'`가 `ownership_core.py`의 `resolve_project_root` 1행만 남기고(그 1행이 승인된 유일한 루트 채택 지점), 5개 어댑터 파일에 대한 같은 grep은 0건. AC-7은 `grep -rn 'CLAUDE_' opal/tools/ownership-tool/ownership_tool/*.py | grep -v claude_adapter.py`가 0건. 실제 연동 — 재배포 후 프로젝트 하위 디렉토리에서 턴을 1회 끝내고 `git status`에 새 untracked `.opal/`이 없는지, 루트 receipt의 `block_count`가 누적되는지 확인한다.
- 실패 시: 배포 전이면 커밋 되돌리기로 끝난다. 배포 후 회귀가 관측되면 이전 커밋에서 `scripts/install-mac.sh`를 재실행해 원복한다 — 훅 파일 교체만이므로 마이그레이션 잔여물이 없다. 경로 변경 직후 첫 Stop은 이전 위치의 receipt를 읽지 못해 `block_count`가 0에서 다시 시작하며, 이는 세션당 1회 발생하고 다음 Stop부터 정상 누적된다.
