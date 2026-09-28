---
template: sdlc-v2
---
# PLAN: 워크트리 registry 메타의 태스크별 폴더 분리와 워크트리 세션 쓰기 권한·기동 전 점검

> 입력: [TASK.md](TASK.md)

## Approach

registry 메타를 태스크별 폴더로 옮기고, 그 폴더를 워크트리 세션에 주는 쓰기 권한의 단위로 삼는다. 메타 파일 쓰기(lock·임시 파일 포함)는 계속 `worktree-tool` 하나가 소유한다. 구 구조를 읽거나 옮기는 코드는 어디에도 두지 않고, 모든 소비자(worktree-tool, ownership-tool 훅, state-tool, launcher, Console, skill-tester)가 새 구조만 읽는다. 구 구조로 남은 기존 메타는 캡틴이 직접 정리한다. launcher는 Codex처럼 쓰기 경로 옵션이 설정된 에이전트에 그 태스크 폴더만 전달하고, 기동 전에 준비 상태를 점검한다. git 쓰기 권한 처리는 범위 밖이며 기존 권한 상승 요청 절차를 유지한다.

설계 가능성의 1차 근거(E1): Codex seatbelt에 태스크 폴더 하나만 쓰기 경로로 주면 그 폴더 쓰기와 폴더 안 임시 파일 생성은 허용되고, 형제 태스크 폴더와 `.meta/` 루트 쓰기는 거부되었다. 관측 명령은 scratch의 `work/`를 cwd로 `codex sandbox -c 'sandbox_mode="workspace-write"' -c 'sandbox_workspace_write.exclude_tmpdir_env_var=true' -c 'sandbox_workspace_write.exclude_slash_tmp=true' -c 'sandbox_workspace_write.writable_roots=["<scratch>/meta/task_1"]' -- sh -c 'touch …'`이며, 결과는 `work:ok t1:ok t2:denied root:denied t1-tmp:ok`이다(codex-cli 0.157.1).

소비자 집합의 근거(E2): `code-scan search '\.meta|registry meta|task_\*\.json|opal-worktrees'`가 9개 파일을 반환했다. 이 중 메타 경로를 직접 조합하거나 `task_*.json`을 glob하는 파일은 아래 직접 변경 목록과 같고, 나머지는 경로를 조합하지 않는다 — `opal/tools/memory-tool/memory_tool.py`는 `.opal-worktrees` 세그먼트 판정만, `opal/tools/ownership-tool/ownership_tool/resolver.py`는 호출자가 읽어 넘긴 registry 객체만 소비, `opal/tools/run-log-tool/adapters/agent_tool_adapter.py`의 `.meta.json`은 서브에이전트 시작 메타 접미사로 무관하다. 테스트를 제외한 소스 grep(`.meta` 경로 조합·`task_*.json` glob)도 직접 변경 목록과 같은 파일 집합을 반환했다.

## Findings

### 직접 변경

- `opal/tools/worktree-tool/worktree_tool.py` — 메타 경로가 registry 폴더 바로 아래의 태스크별 JSON 파일(task_{task}.json)이다(`:938-939`). lock은 `<meta>.lock`(`:994`), 원자 쓰기 임시 파일은 같은 폴더(`:1025-1031`)라 경로 함수만 바꾸면 lock·임시 파일이 태스크 폴더 안으로 들어간다. 목록 조회가 `task_*.json` glob 3곳(`:567-568`, `:1641-1643`, `:1718-1722`)이고, remove는 메타와 lock만 지우고 registry 폴더를 남긴다(`:2649-2658`).
- `opal/tools/ownership-tool/ownership_tool/ownership_core.py` — 독립 경로 함수 `registry_meta_path`(`:74-76`)와 읽기(`:269-277`). 허브 판정의 `.meta` 폴더 존재 검사(`:336-352`)는 유지 대상이다.
- `opal/tools/ownership-tool/ownership_tool/heartbeat_hook.py`, `opal/tools/ownership-tool/ownership_tool/session_start_hook.py`, `opal/tools/ownership-tool/ownership_tool/stop_evaluator.py` — 각자 `task_*.json` glob으로 registry 전건을 읽는다(`heartbeat_hook.py:26,40`, `session_start_hook.py:31,54`, `stop_evaluator.py:19,94`).
- `opal/tools/state-tool/state_tool.py` — 부트 이상 검사가 `task_*.json` glob을 쓴다(`:5080-5082`).
- `opal/tools/worktree-launcher/worktree_launcher/launcher_core.py` — 독립 경로 함수 `registry_meta_path`(`:81-85`)로 registry를 읽는다.
- `opal/tools/worktree-launcher/worktree_launcher/settings.py` — 치환 토큰이 `{utterance}`·`{task_path}` 2종뿐이고(`:46-47`), Codex 기본 명령은 `codex --no-daemon "{utterance}"`다(`:38`).
- `opal/tools/worktree-launcher/worktree_launcher/cli.py` — 기동 명령 확정(`:163-192`) 직후 곧바로 `launcher_core.run`으로 lease 이관·터미널 기동에 들어가며(`:210-218`), 그 사이에 권한 점검이 없다.
- `dashboard/backend/routers/tasks.py` — Console이 registry 폴더를 직접 읽는다(`:101`).
- `opal/skills/opal-skill-tester/scripts/skill_tester.py` — checkpoint SHA를 `task_*.json` glob으로 읽는다(`:212-214`).
- `opal/core/setting.default.json` — launcher 기본값과 `_help`의 "치환 토큰 2종" 설명(`:13`, `:17`).
- `scripts/install-mac.sh`, `scripts/install/windows.ps1` — 이전 배포 기본 Codex 명령과 정확히 같을 때만 새 기본값으로 이관한다(`install-mac.sh:1234-1245`, `windows.ps1:516-529`).

### 회귀 확인

- `opal/tools/ownership-tool/ownership_tool/codex_adapter.py` — lease를 가진 Codex 자식의 `registry_write_denied`를 허브 확정으로 넘기는 부팅 경로. 새 구조에서도 같은 진단이 유지되는지 확인한다.
- `opal/core/hooks/claude-hooks.json` — 훅 배선 자체는 바꾸지 않는다. 세션 시작·heartbeat·stop 훅이 기존 배선 그대로 새 구조 registry를 읽는지 확인한다.
- `opal/tools/ownership-tool/ownership_tool/resolver.py` — registry 객체를 `ownership_core`에게서 받기만 하고 경로를 조합하지 않는다. 새 구조 fixture에서도 분류 결과가 같은지 확인한다.
- `opal/tools/worktree-launcher/worktree_launcher/adapters/orca.py` — 터미널 기동 어댑터. 점검 실패 시 호출되지 않는지 확인한다.

### 문서 갱신

- `opal/core/references/harness/worktree.md` — registry 위치 표(`:79`), canonical path 발급 계약의 메타 경로(`:146`), 워크트리 세션 쓰기 권한 범위, Codex 기본 명령과 권한 상승 절차(`:139-140`)를 새 구조·새 계약으로 갱신한다.
- `opal/core/references/harness/task-process.md` — 스텝 5.5에 기동 전 점검과 실패 시 동작을 추가한다.
- `opal/tools/worktree-tool/README.md` — 메타 위치(`:12`), remove 회수 범위(`:176-181`).
- `opal/tools/ownership-tool/README.md` — `read_registry_meta` 경로 설명(`:107`).
- `opal/tools/worktree-launcher/README.md` — preflight(`:95`)와 치환 토큰, 기동 전 점검 오류 코드.

### 미확인 가정

- H-1 참조.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| D-1. 메타 저장 구조 | 태스크 메타는 `<hub_root>/.opal-worktrees/.meta/task_{NNN}/meta.json`이다. lock은 `meta.json.lock`, 원자 쓰기 임시 파일은 `meta.json.tmp.<pid>`로 같은 폴더 안에만 생긴다. 이 폴더는 태스크 소유이며 앞으로 태스크별로 추가할 파일도 이 폴더 아래에 둔다 | 폴더가 곧 권한 부여 단위가 되어 다른 태스크를 열지 않는다(C-1). 캡틴 결정 |
| D-2. 단일 writer 유지 | 메타 파일 생성·교체·삭제는 `worktree-tool`만 수행한다. ownership-tool·state-tool·launcher·Console·skill-tester는 읽기만 한다 | 기존 dual-writer 방지 불변식 유지(C-3). brain `entity/ownership-tool` |
| D-3. 태스크 폴더 목록 | 전건 조회는 `.meta/` 아래 `task_*` 폴더 중 `meta.json`이 있는 것만 이름순으로 읽는다. 각 도구는 경로 계산 함수를 하나만 두고 그 함수를 거친다. 구 구조 파일(`.meta/task_{NNN}.json`)은 읽지도 옮기지도 않는다 | 소비자별 glob 중복을 한 규칙으로 고정(AC-2). 기존 메타 정리는 캡틴 몫 |
| D-4. 회수 범위 | `remove` 성공 시 lock 보유 상태로 `meta.json`을 지운 뒤, 같은 inode의 lock 이름을 회수하고 태스크 폴더 전체를 삭제한다. 실패 경로는 폴더를 보존한다. `.meta/`는 남긴다 | 폴더가 태스크 소유이므로 함께 회수. 실패 시 보존 계약은 기존과 같다(`worktree.md` §생성·회수 순서) |
| D-5. 쓰기 경로 전달 | launcher 치환 토큰에 `{meta_dir}`(= D-1 태스크 폴더 절대경로, 허브 루트·태스크 번호 발급값으로 계산)을 추가한다. Codex 기본 명령은 `codex --no-daemon --add-dir "{meta_dir}" "{utterance}"`다. Claude 기본 명령은 바꾸지 않는다 | 플랫폼 차이를 launcher 설정에만 둔다(C-2). 샌드박스 없는 세션 동작 불변 |
| D-6. 기동 전 점검 | `launch`는 명령 확정 뒤, lease 이관·터미널 기동 전에 점검한다. ① 태스크 메타 폴더와 `meta.json`이 있고 허브에서 쓰기 가능해야 한다. ② 명령 템플릿에 `{meta_dir}`가 있으면 바로 앞 토큰을 쓰기 경로 옵션으로 보고, `<실행 파일> --help` 출력(10초 제한)에 그 옵션이 있어야 한다. ③ `{meta_dir}`를 쓰는 에이전트에는 공유 `.git` 쓰기를 부여하지 않으므로 `git_write_requires_escalation` 경고를 응답에 담는다(차단 아님). ①·②가 실패하면 `launch_preflight_failed`와 `cause`(`meta_dir_missing`·`meta_dir_not_writable`·`grant_option_unsupported`·`agent_help_unavailable`)로 종료하고 터미널·lease를 건드리지 않는다 | AC-5, AC-6. 실패를 CLOSE가 아니라 기동 시점에 드러낸다 |
| D-7. 설정 이관 | 설치 스크립트는 전역 `setting.json`의 Codex 명령이 이전 배포 기본값 2종(`codex "{utterance}"`, `codex --no-daemon "{utterance}"`) 중 하나와 정확히 같을 때만 새 기본값으로 바꾼다. 그 밖의 값은 사용자 설정으로 보고 유지하며 안내만 출력한다. Windows 설치 스크립트도 같은 규칙이다 | 기존 TS-028 이관 방식과 같다(C-5) |
| D-8. git 쓰기 | git checkpoint·finalize 커밋은 이번에 바꾸지 않는다. 막히면 기존 권한 상승 요청 절차를 따른다 | TASK 범위 제외. 허브 위임은 후속 태스크 |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. worktree-tool 메타 폴더 구조·회수 | opal-task-agent | `opal/tools/worktree-tool/worktree_tool.py`, `opal/tools/worktree-tool/README.md`, `opal/tools/worktree-tool/tests/` | D-1 경로 함수(`_meta_dir`, `_meta_path`)와 D-3 목록 함수로 기존 glob 3곳 교체. D-4 폴더 회수. README의 메타 위치·회수 갱신. 정상 생성(lock·임시 파일 위치 포함)·조회·회수·구 구조 파일 무시 단위 테스트 추가 | 없음 | P1 | AC-1, AC-2, C-3 |
| W-2. state-tool·skill-tester 읽기 경로 | opal-task-agent | `opal/tools/state-tool/state_tool.py`, `opal/skills/opal-skill-tester/scripts/skill_tester.py`, `opal/tools/state-tool/tests/` | 두 glob을 D-3 규칙으로 교체. state-tool 부트 이상 검사 테스트 fixture를 새 구조로 갱신 | 없음 | P1 | AC-2 |
| W-3. Console registry 읽기 경로 | opal-be-agent | `dashboard/backend/routers/tasks.py`, `dashboard/backend/tests/` | `_WORKTREE_REGISTRY_DIR` 기반 조회를 D-3 규칙으로 교체하고 관련 테스트 fixture 갱신 | 없음 | P1 | AC-2 |
| W-4. launcher 쓰기 경로 토큰과 기동 전 점검 | opal-task-agent | `opal/tools/worktree-launcher/worktree_launcher/settings.py`, `opal/tools/worktree-launcher/worktree_launcher/launcher_core.py`, `opal/tools/worktree-launcher/worktree_launcher/cli.py`, `opal/tools/worktree-launcher/README.md`, `opal/tools/worktree-launcher/tests/` | D-5 `{meta_dir}` 토큰과 Codex 기본 명령, launcher_core 경로 함수를 D-1로 교체. D-6 점검을 `_cmd_launch`의 `launcher_core.run` 호출 전에 추가. README 토큰·점검·오류 코드 갱신. 점검 성공·실패 원인별·경고·어댑터 미호출 테스트 추가. 실제 Codex 샌드박스 쓰기 실측 대상 | 없음 | P1 | AC-3, AC-4, AC-5, AC-6, C-1, C-2 |
| W-5. 기본 설정과 설치 이관 | opal-task-agent | `opal/core/setting.default.json`, `scripts/install-mac.sh`, `scripts/install/windows.ps1`, `scripts/tests/test_agent_adapter_fields.sh` | D-5 Codex 기본 명령과 `_help` 토큰 설명 갱신. D-7 이관 규칙을 두 설치 스크립트에 반영하고 기존 TS-028 테스트를 새 이관 대상 2종·사용자 값 보존으로 확장. 정식 install 재배포와 배포본 재확인의 진입점 | 없음 | P1 | AC-3, AC-8, C-2, C-4, C-5 |
| W-6. 하네스 문서 | opal-task-agent | `opal/core/references/harness/worktree.md`, `opal/core/references/harness/task-process.md` | worktree.md의 registry 위치 표·canonical path 메타 경로·워크트리 세션 쓰기 권한 범위(D-1, D-5, D-8)·Codex 기본 명령 문장 갱신. task-process.md 스텝 5.5에 D-6 점검과 실패 시 비차단 허브 계속 규칙 추가 | 없음 | P1 | AC-7, C-1 |
| W-7. ownership-tool 읽기 경로 | opal-task-agent | `opal/tools/ownership-tool/ownership_tool/ownership_core.py`, `opal/tools/ownership-tool/ownership_tool/heartbeat_hook.py`, `opal/tools/ownership-tool/ownership_tool/session_start_hook.py`, `opal/tools/ownership-tool/ownership_tool/stop_evaluator.py`, `opal/tools/ownership-tool/README.md`, `opal/tools/ownership-tool/tests/` | `registry_meta_path`와 전건 조회를 D-1·D-3 규칙 하나로 통일하고 세 훅이 그 함수를 쓰게 한다. README 경로 설명 갱신. 새 구조 fixture로 테스트 갱신 | W-1 | P2 | AC-2, C-3 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. 대화형·`exec` Codex의 `--add-dir`가 seatbelt `writable_roots`와 같은 쓰기 경로를 부여한다 | D-5 쓰기 경로 전달 | 가정이 틀리면 태스크 메타 폴더 쓰기가 계속 거부되어 AC-4 실패 | TEST에서 실제 `codex exec --sandbox workspace-write --add-dir <태스크 폴더>`로 자기 폴더 쓰기 성공·형제 폴더 거부를 실측한다. 불일치하면 `-c sandbox_workspace_write.writable_roots` 방식으로 D-5를 재설계한다 |

## Release and recovery

- 적용 순서: P1(W-1, W-2, W-3, W-4, W-5, W-6) → P2(W-7) → 통합 테스트 → `scripts/install-mac.sh` 재배포 → 배포본 검증.
- 검증 범위: 결정론(단위 테스트, 구 구조 경로 조합 0건 검색), 회귀(worktree-tool·ownership-tool·state-tool·launcher·Console·설치 스크립트 스위트), 실제 연동(새 구조로 만든 임시 허브에서 worktree-tool·ownership-tool·state-tool CLI 결과 확인, 실제 Codex 샌드박스 쓰기 실측, launcher 점검 실패 시 터미널 미기동).
- 기존 메타 경계: 새 도구는 구 구조 메타를 읽지 않으므로, 캡틴이 정리하기 전까지 구 구조로 남은 active 태스크는 배포 뒤 registry 조회에서 보이지 않는다. 이 태스크(task_164) 자신의 메타도 구 구조이므로, 재배포·배포본 검증(TEST) 전에 이 태스크 메타의 처리 방식을 캡틴에게 확인받는다.
- 실패 시: 이전 설치본으로 재배포한다. 새 도구는 구 구조 파일을 수정·삭제하지 않으므로 재배포만으로 기존 메타가 다시 보인다. 새 구조로 만든 태스크 폴더는 이전 설치본이 읽지 않으므로, 롤백 전에 새 구조로 생성한 태스크가 있는지 확인한다.
