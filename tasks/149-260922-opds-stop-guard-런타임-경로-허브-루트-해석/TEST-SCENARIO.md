---
template: sdlc-v2
---
# TEST-SCENARIO: ownership-tool 훅의 런타임 루트를 cwd가 아닌 프로젝트 루트로 해석

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: 워크트리 `/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_149` (base `88bdab2`). 파이썬은 `~/.opal/.venv/bin/python`, 테스트 러너는 `pytest`. 훅 어댑터는 모듈 함수 직접 호출이 아니라 **`subprocess`로 실행하고 stdin에 봉투 JSON을 흘려보내** 실제 진입점(`main()`)의 루트 해석·fail-safe·출력 채널을 함께 관찰한다.
- 공통 데이터: 임시 디렉토리에 3종 루트 형태를 만든다 — ⑴ 허브형(`<root>/.opal-worktrees/.meta/` 존재) ⑵ 워크트리형(`<root>/.opal/task-ownership.json` 발급 사본 존재) ⑶ 무증거형(둘 다 없음). 각 루트 아래 `sub/nested/` 하위 디렉토리를 만들고 봉투 `cwd`에 그 하위 경로를 담는다. 실측 봉투 형태는 `opal/tools/ownership-tool/tests/fixtures/hook-payloads/stop.json`을 기준으로 한다.
- 대역 사용과 한계: 파일시스템·`subprocess`는 대역을 쓰지 않는다(루트 해석과 파일 생성 위치가 검증 대상이므로 `tmp_path` 실물 경로로만 판정한다). env는 `subprocess` 호출 시 명시 주입한 dict만 사용해 호스트 세션 값이 새지 않게 한다. **S-1·S-13은 대역으로 대체할 수 없다** — 플랫폼이 훅 프로세스에 무엇을 주입하는지와 실제 세션에서의 저장소 오염 여부는 실제 Claude Code 실행으로만 관찰된다.
- 실행 조건: S-13만 사용자 협업(실제 Claude Code 세션 1회 실행·관찰)이 필요하고 나머지는 자동 실행이다. S-1은 임시 훅 등록 → 1회 실행 → **즉시 원복**이 전제이며, 캡처값은 경로 placeholder로 정규화해 기록한다.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-2 | AC-7, C-3 | 워크트리 소스 트리 | 아래 `### S-2` 절의 검사 명령을 실행한다 | 매칭 0건. 즉 `CLAUDE_PROJECT_DIR`를 포함한 플랫폼 고유 변수명이 `claude_adapter.py` 밖에 등장하지 않는다 | unit(결정론 grep), `tests/test_root_resolution.py`에 계약 테스트로 고정 | 구현 전 RED |
| S-3 | AC-6 | 워크트리 소스 트리 | 아래 `### S-3` 절의 검사 명령 2건을 실행한다 | ⑴ 어댑터 5파일에서 0건 ⑵ `ownership_core.py`의 `resolve_project_root` 체인 1행만 남는다(승인된 유일한 루트 채택 지점). `payload.get("cwd") or project_root` 6곳은 cwd를 cwd 의미로 쓰므로 판정에서 제외된다 | unit(결정론 grep), `tests/test_root_resolution.py` | 구현 전 RED |
| S-4 | AC-5, C-1, C-2, C-6 | 무증거형 루트의 하위 디렉토리를 `cwd`로 담은 Stop 봉투. env에 `OPAL_PROJECT_ROOT`·`CLAUDE_PROJECT_DIR` 모두 없음 | `subprocess`로 `stop_hook.py`를 실행하고 stdin에 봉투를 준다 | exit code 0, stdout 무출력(`{"decision":"block"}` 포함 어떤 출력도 없음), stderr에 traceback 없음, 그리고 **임시 트리 전체에 새로 생성된 파일·디렉토리 0건**(`cwd` 아래 `.opal/`도, 루트 아래 `.opal/`도 만들어지지 않는다) | integration(subprocess + 실물 tmp 트리) | 구현 전 RED |
| S-5 | AC-1 | 워크트리형 루트의 `sub/nested/`를 `cwd`로 담은 Stop 봉투. env로 루트를 명시 주입 | `subprocess`로 `stop_hook.py` 1회 실행 | receipt가 `<루트>/.opal/run/.runtime/stop-guard/<sid>.json`에만 생성된다. `<루트>/sub/` 이하에 `.opal/` 경로가 0건이다 | integration(subprocess + 실물 tmp 트리) | 구현 전 RED |
| S-6 | AC-3 | 같은 `session_id`, 동일 fingerprint 상태. 1회차 `cwd`는 루트, 2회차 `cwd`는 `sub/nested/` | `stop_hook.py`를 연속 2회 실행하고 2회차 응답과 루트 receipt를 읽는다 | 2회차가 1회차 receipt를 읽어 `prior_block_count`가 0으로 리셋되지 않고 `block_count`가 누적되며, 동일 fingerprint이므로 `decision_kind`가 `allow_no_progress_same_fingerprint`로 판정된다 | integration(subprocess 2회 + receipt 실측) | 구현 전 RED |
| S-7 | AC-2 | 워크트리형 루트의 하위 디렉토리를 `cwd`로 담은 SessionStart 봉투, 이어서 같은 세션의 SessionEnd 봉투 | 두 훅을 순서대로 `subprocess` 실행한다 | registry가 `<루트>/.opal/run/.runtime/sessions/<sid>.json` **한 곳에만** 생성·갱신된다(SessionStart가 `status: active`로 만들고 SessionEnd가 같은 파일을 `closed`로 바꾼다). 하위 디렉토리 아래에 `.opal/` 경로가 0건이다 | integration(subprocess 2회 + 실물 tmp 트리) | 구현 전 RED |
| S-8 | AC-4 | `<루트>/.opal/setting.local.json`에 `ownership.lease_ttl_sec`를 기본값(14400)과 다른 값으로 설정. 봉투 `cwd`는 하위 디렉토리 | `subprocess`로 `heartbeat_hook.py`를 실행하고 기록된 lease의 `ttl_sec`·`lease_expires_at`을 읽는다 | 설정값이 적용된다. 기본 14400으로 폴백하지 않는다 | integration(subprocess + lease 레코드 실측) | 구현 전 RED |
| S-9 | C-4, C-5 | 변경 후 `ownership_core.py` 소스와 임시 트리 4종 | 아래 `### S-9` 절의 4케이스를 실행하고, `resolve_roots`·`resolve_hub`의 기존 AST·계약 테스트를 재실행한다 | ⑴ 평범한 프로젝트 하위 cwd → 마커 보유 조상이 채택된다 ⑵ 오염(`<하위>/.opal/run/.runtime/`)만 있는 cwd → 앵커로 인정하지 않는다 ⑶ 워크트리 안 하위 cwd → 허브가 아니라 워크트리 `.opal`이 먼저 잡힌다 ⑷ 앵커 전무 → `None`. 그리고 `resolve_roots`·`resolve_hub`의 추론 부재 집행 테스트가 **기대값 수정 없이** 통과한다 | unit(실물 tmp 트리 + 기존 AST 검사 재실행) | 구현 전 RED |
| S-10 | AC-8, C-7, C-1 | 구현 완료 상태의 워크트리 | `~/.opal/.venv/bin/python -m pytest opal/tools/ownership-tool/tests -q`와 `scripts/tests/test_hook_parity.py`를 실행한다 | 두 스위트 전건 통과(failed 0). 태스크 150이 늘린 `test_lease.py`·`test_integration.py`·`test_session_start.py`·`test_pretooluse_guard.py`·`test_heartbeat.py`·`test_cli.py`가 분모에 포함된다. **기존 테스트의 기대값이 수정되지 않았다**(수정이 필요했다면 설계 위반으로 보고) | unit+integration 회귀 | 구현 후 |
| S-11 | D-28(150 이관 계약 무약화) | `status: handoff_pending`이고 `handoff_to_worktree_root`가 워크트리 루트인 lease. 봉투 `cwd`는 그 루트의 하위 디렉토리 | `subprocess`로 `session_start_hook.py`를 실행한다 | `claimant_root`로 해석된 루트(=`handoff_to_worktree_root`와 realpath 동치)가 전달되어 claim이 **성공**한다. 종전의 하위 cwd 전달과 결과가 같아 `harness/worktree.md` §이관의 수용 계약이 약화되지 않는다. 대상 외 루트에서 온 claim은 여전히 `handoff_pending`으로 거부된다 | integration(subprocess + lease 레코드 실측) | 구현 후 |
| S-12 | H-2, C-2 | 타 세션이 live lease를 소유한 태스크. 봉투 `cwd`는 프로젝트 하위 디렉토리 | `subprocess`로 `pretooluse_guard_hook.py`에 ⑴ 타 세션 소유 ⑵ 이관 중(무소유) ⑶ 만료 lease 3상태 × 차단 대상 명령을 각각 실행한다 | ⑴만 `decision: block`이고 ⑵⑶은 비차단이다 — `harness/worktree.md` §가드 적용 범위("쓰기 차단은 lease가 타 세션 소유로 판정될 때만 발동한다. 이관 중(무소유)과 만료는 차단 대상이 아니다")와 동치. 출력은 기존 1줄 채널뿐이고 새 채널이 생기지 않는다 | integration(subprocess 3케이스) | 구현 전 RED |
| S-13 | AC-1, AC-3 | `scripts/install-mac.sh` 재배포 완료. 실제 Claude Code 세션에서 프로젝트 하위 디렉토리로 이동한 상태 | 하위 디렉토리에서 턴을 1회 끝내고, 이어서 같은 세션에서 한 번 더 끝낸다. 그 뒤 `git status --short`와 루트 receipt를 읽는다 | `git status`에 새 untracked `.opal/` 항목이 0건이다. 루트 receipt의 `block_count`가 2회차에 누적된다(리셋되지 않는다) | manual, 실제 Claude Code 세션 | 설치 후 |

### S-2

```bash
grep -rn 'CLAUDE_' opal/tools/ownership-tool/ownership_tool/*.py | grep -v claude_adapter.py
```

기대: 출력 0행.

### S-3

```bash
# ⑴ 어댑터 5종 — 루트 채택 잔존 0건
grep -n 'payload.get("cwd")' \
  opal/tools/ownership-tool/ownership_tool/{stop,session_start,heartbeat,session_end,pretooluse_guard}_hook.py \
  | grep -v 'payload.get("cwd") or project_root'

# ⑵ 패키지 전체 — 승인된 단일 채택 지점만 남는다
grep -rn 'payload.get("cwd")' opal/tools/ownership-tool/ownership_tool/*.py \
  | grep -v 'payload.get("cwd") or project_root'
```

기대: ⑴ 출력 0행. ⑵ `ownership_core.py`의 `resolve_project_root` 체인 1행만 출력된다.


### S-9

조상 탐색(D-30b)은 `.parents` 순회를 **정당하게** 사용하므로, 초판 S-9의 `resolve_project_root` 대상
`.parents` 금지 AST 검사는 폐기한다(C-5 정정 — 그 금지는 `resolve_hub`·`resolve_roots` 축 전용이다).
`resolve_roots`·`resolve_hub`에 대한 기존 AST·계약 검사는 그대로 유지한다.

4케이스는 실물 `tmp_path` 트리로 구성한다.

| 케이스 | 트리 구성 | 봉투 `cwd` | 기대 |
|---|---|---|---|
| ⑴ 평범한 프로젝트 | `<root>/.opal/MEMORY.json` + `<root>/sub/nested/` | `<root>/sub/nested` | `<root>` |
| ⑵ 오염만 있는 하위 | `<root>/.opal/MEMORY.json` + `<root>/sub/.opal/run/.runtime/` | `<root>/sub` | `<root>` (오염 `.opal/`은 앵커 아님) |
| ⑶ 워크트리 중첩 | `<hub>/.opal/MEMORY.json` + `<hub>/.opal-worktrees/wt/.opal/AGENT.md` + `.../wt/sub/` | `<hub>/.opal-worktrees/wt/sub` | `<hub>/.opal-worktrees/wt` |
| ⑷ 앵커 전무 | 마커 없는 빈 트리 | `<bare>/sub` | `None` |

⑵가 D-30c의 자기증식 방어를 집행하고, ⑶이 "가장 가까운 조상" 규칙이 허브보다 워크트리를 우선함을 고정한다.
