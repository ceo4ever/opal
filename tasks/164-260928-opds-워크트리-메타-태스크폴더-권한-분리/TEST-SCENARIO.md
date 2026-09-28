---
template: sdlc-v2
---
# TEST-SCENARIO: 워크트리 registry 메타의 태스크별 폴더 분리와 워크트리 세션 쓰기 권한·기동 전 점검

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: 이 worktree의 source에서 각 도구의 pytest·installer bash 테스트를 실행한다. 통합 검증은 scratch 아래 임시 허브(`git init` + `.opal/worktree.json` + `.opal-worktrees/.meta/`)를 만들어 공개 CLI(`worktree-tool`·`ownership-tool` 훅·`state-tool`·`worktree-launcher`)로 수행한다. 실제 허브 `.meta/`는 읽기만 하고 쓰지 않는다.
- 공통 데이터: 임시 허브의 새 구조 태스크 2건(`task_901/`, `task_902/`)과 구 구조 파일 1건(`task_900.json`). 구 구조 파일은 모든 소비자가 무시해야 하는 대조군이다.
- 대역 사용과 한계: 단위 테스트의 fake adapter·fake agent 실행 파일은 점검 순서·호출 여부·원인 코드 확인에만 쓴다. 실제 Codex 샌드박스 쓰기(S-6)와 배포본 재확인(S-11)을 대신하지 않는다. PowerShell 실행 환경이 없으므로 Windows 설치 스크립트는 기존 TS 방식대로 소스 정적 검사로만 확인하며, 실제 Windows 실행은 이번 범위에서 확인하지 않는다.
- 실행 조건: S-1~S-10·S-12는 자동 실행. S-6은 로그인된 codex-cli가 필요하다. S-11은 정식 install 뒤 실행하며, install 전에 이 태스크(task_164) 자신의 구 구조 메타 처리 방식을 캡틴에게 확인받는다(PLAN Release and recovery).

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1, C-3 | 빈 `.meta/`를 가진 임시 허브 | `worktree-tool create`로 태스크를 만들고 `ownership-set`·`status`로 메타를 다시 쓴다. 쓰기 중 생성되는 lock·임시 파일 경로를 기록한다 | 메타가 `.meta/task_{NNN}/meta.json`에만 있고, lock(`meta.json.lock`)과 임시 파일(`meta.json.tmp.*`)이 전부 같은 태스크 폴더 안에서만 생긴다. `.meta/` 바로 아래에는 태스크 폴더 외 파일이 없다. 발급 6종 필드와 `task_path == realpath(task_home/tasks/task_folder)` 불변식은 변경 전과 같다 | pytest + 임시 허브 CLI 통합 / worktree-tool | 구현 전 RED |
| S-2 | AC-1, AC-2, C-3 | 새 구조 2건 + 구 구조 `task_900.json` 1건이 있는 임시 허브 | `worktree-tool list`·`status`, ownership-tool 세션 시작·heartbeat·stop 훅, `state-tool` 부트 이상 검사, launcher registry 조회, Console `/api/tasks`, skill-tester checkpoint 조회를 실행한다 | 모든 소비자가 새 구조 2건만 정확히 보고하고 `task_900.json`은 결과에 나타나지 않으며 바이트도 바뀌지 않는다. ownership-tool의 `registry_write_denied` 진단과 resolver 분류 결과는 변경 전 fixture와 같다 | pytest(도구별 스위트) + 임시 허브 CLI 통합 | 구현 전 RED |
| S-3 | AC-1, C-3 | 새 구조 태스크 2건, 한 건은 회수 가능·다른 한 건은 dirty 또는 entry 회수 실패 | 각 태스크에 `worktree-tool remove`를 실행한다 | 성공한 태스크는 태스크 폴더 전체(메타·lock 포함)가 사라지고 `.meta/`와 다른 태스크 폴더는 남는다. 실패한 태스크는 `WORKTREE_REMOVE_FAILED` 또는 가드 오류로 끝나고 메타·lock·폴더가 그대로 보존된다 | pytest + 임시 허브 CLI 통합 / worktree-tool | 구현 전 RED |
| S-4 | AC-2 | 구현 완료된 source | 테스트를 제외한 source에서 `.meta` 경로 조합, `task_*.json` glob, `task_{…}.json` 파일명 조합을 검색하고, 각 도구의 소비 지점이 도구별 경로 계산 함수 하나를 호출하는지 확인한다 | 구 구조 경로 조합 0건. 메타 경로를 계산하는 지점은 도구마다 함수 하나이며 나머지 소비 지점은 모두 그 함수를 거친다 | 결정론 grep + 코드 확인 | 구현 후 |
| S-5 | AC-3, C-1, C-2 | 임시 허브의 `task_901`, 기본 launcher 설정 | launcher가 Codex와 Claude 기동 명령을 확정하는 경로를 dry-run 또는 fake adapter로 실행해 argv를 기록한다 | Codex argv에 `--add-dir <hub>/.opal-worktrees/.meta/task_901`이 정확히 1회 들어가고 `.meta/` 루트·다른 태스크 폴더·`.git` 경로는 없다. Claude argv는 변경 전과 바이트 동일하다 | pytest / worktree-launcher | 구현 전 RED |
| S-6 | AC-4, C-1, H-1 | 로그인된 codex-cli 0.157.1, 임시 허브의 `task_901/`·`task_902/`와 `.git` | S-5가 만든 Codex 쓰기 경로 인자를 그대로 붙여 `codex exec --sandbox workspace-write --add-dir <task_901 폴더>`로 `task_901` 쓰기·임시 파일 생성·`os.replace`, `task_902` 쓰기, `.meta/` 루트 쓰기, `.git` 쓰기를 시도한다 | `task_901` 쓰기·임시 파일·교체는 성공하고 `task_902`·`.meta/` 루트·`.git` 쓰기는 거부된다. 결과가 다르면 H-1 불일치로 보고하고 PLAN D-5 재설계로 되돌린다 | 실제 Codex 샌드박스 integration | 구현 후 |
| S-7 | AC-5 | 원인별 조건 4종 — 태스크 메타 폴더 없음, 폴더 쓰기 불가, 에이전트 `--help`에 쓰기 경로 옵션 없음, 실행 파일 없음 또는 `--help` 10초 초과 | 각 조건에서 `worktree-launcher launch`를 실행한다 | 모두 0이 아닌 종료와 `launch_preflight_failed` + 해당 `cause`(`meta_dir_missing`·`meta_dir_not_writable`·`grant_option_unsupported`·`agent_help_unavailable`). 터미널 어댑터 launch·lease 이관이 한 번도 호출되지 않고 registry·lease 파일 바이트가 불변이다 | pytest(fake adapter·fake agent) + 메타 폴더 없음 1건은 실제 CLI로 터미널 미생성 확인 | 구현 전 RED |
| S-8 | AC-6 | 점검 ①·②를 통과하는 Codex 설정과 Claude 설정 | 두 설정으로 각각 `launch`를 실행한다 | Codex는 응답에 `git_write_requires_escalation` 경고가 담기고 기동이 계속 진행된다(차단 없음). Claude 설정에는 이 경고가 없다 | pytest / worktree-launcher | 구현 전 RED |
| S-9 | AC-7, C-1 | 갱신된 하네스 문서와 README | `worktree.md`·`task-process.md`·세 도구 README를 읽고, 구 구조 경로(`task_{NNN}.json`, `.meta/task_*.json`)를 검색한다 | 문서가 태스크 폴더 구조, 워크트리 세션 쓰기 범위(자기 태스크 메타 폴더만, `.meta/` 루트·다른 태스크·공유 `.git` 제외), 기동 전 점검 계약과 실패 동작을 기술한다. 구 구조를 현재 사실로 기술한 문장 0건 | 결정론 grep + PM 문서 검토 | 구현 후 |
| S-10 | AC-3, C-2, C-5 | 전역 설정의 Codex 명령이 없음 / 구 기본값 `codex "{utterance}"` / 구 기본값 `codex --no-daemon "{utterance}"` / 사용자 수정값 | Mac 설치 스크립트의 설정 이관 함수를 각 조건에서 실행하고, Windows 설치 스크립트 소스에 같은 규칙이 있는지 정적 검사한다 | 없음·구 기본값 2종은 새 기본값(`--add-dir "{meta_dir}"` 포함)이 되고, 사용자 수정값은 바이트 보존과 안내 출력. Claude 명령은 모든 조건에서 불변. Windows 소스가 같은 이전 기본값 2종과 새 기본값을 가진다 | installer bash 테스트 + PowerShell 소스 정적 검사 | 구현 후 |
| S-11 | AC-8, C-4 | source 테스트 전건 통과, 캡틴의 task_164 메타 처리 확인 완료 | `scripts/install-mac.sh`로 재배포한 뒤 배포본 `~/.opal/tools/` 진입점으로 S-5(argv), S-6(실제 Codex 쓰기), S-7(메타 폴더 없음 실패)을 다시 실행한다. 배포본 파일이 source와 같은지 대조한다 | 세 시나리오가 배포본에서 source와 같은 결과를 낸다. 배포본은 install 산출물과 일치하며 `~/.opal/`을 직접 수정한 흔적이 없다 | 설치본 CLI + 실제 Codex | 설치 후 |
| S-12 | C-3 | 구현 완료된 source | worktree-tool·ownership-tool·state-tool·worktree-launcher·Console backend·installer 테스트 스위트 전체를 실행한다 | 전 스위트 PASS. lease 저장 위치·canonical path 발급·`allocator_root` 비추론·`task_path_ambiguous` 판정 관련 기존 테스트가 변경 없이 통과한다 | pytest + installer bash | 구현 후 |
