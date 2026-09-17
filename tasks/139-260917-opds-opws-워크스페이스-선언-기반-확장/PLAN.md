---
template: sdlc-v2
---
# PLAN: opws 워크스페이스 선언 기반 확장

> 입력: [TASK.md](TASK.md)

## Approach

`git-sync-tool`에 선언 파일 축을 추가한다. 기존 `sync`는 디스크 발견 기반이고 이 축은 그대로 둔 채, `{프로젝트}/.opal/workspace.json`이 있을 때만 선언×디스크 대조를 얹는다. 대조의 정체성 키는 `org/repo`이며 접속 방식(host·SSH 별칭·프로토콜)은 판정에서 배제한다.

`code-scan search "git_sync"` 조회로 변경 대상 2파일을 확정했다 — `git_sync_tool.py`(layer=util, domain=opal-workspace, exports는 `cmd_sync`·`process_repo`·`discover_targets`·`resolve_root_target` 4종)와 `tests/test_git_sync_tool.py`(layer=test, 052 RED-first 자산). 이번 변경은 두 파일에 집중되므로 Work item을 파일 단위로 쪼개지 않고 **실행 그룹을 순차로 세운다**.

착수 순서는 의존 관계다. 정규화 파서가 `init` 초안 생성의 입력이므로, 파서보다 `init`을 먼저 만들면 SSH 별칭 사용자에게서 틀린 초안이 나오고 그 초안이 커밋되어 선언 SSOT가 오염된다.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| 정체성 축은 `org/repo` 단일 | `normalize_repo_coord(url)`이 host를 버리고 `org/repo`만 반환한다. 후행 `.git`을 제거한다 | 접속 방식은 사용자마다 다르다. 실측: 한 워크스페이스 안에 `git@github-iskang:storelink-io/blend`와 `...blend-monitoring-front.git`이 공존한다 (C-2, AC-2, AC-9) |
| 대조는 3진 판정 | `compare_repo_coord(declared, actual)` → `match`/`mismatch`/`unknown`. 한쪽이라도 환원 불가면 `unknown`이며 `unknown`은 pull하지 않는다 | 미탐(다른 레포를 같다고 판정)은 엉뚱한 저장소를 pull하는 조용한 손상이다. 오탐은 시끄러울 뿐이다 (C-4, AC-3) |
| 도구 JSON에 원격 URL 원문 미포함 | `repositories[]`에 정규화 키 `repo`만 싣는다. URL 원문은 `mismatch`·`unknown`일 때 스킬이 렌더 시점에 직접 읽어 화면에만 표시한다 | 도구 출력은 DONE.md·brain·태스크 문서로 흘러간다. "영속 기록 시 제외" 산문 규칙은 어겨지므로 통로 자체를 만들지 않는다 (C-3, AC-7) |
| 선언 부재 = 현행 경로 | `load_workspace_config()`가 `None`을 반환하면 `cmd_sync`가 기존 분기를 그대로 타고 응답 키 집합이 바이트 동일하다. `undeclared` 판정 자체를 하지 않는다 | `//opws`는 특정 프로젝트 전용이 아니다. `--root` 도입 때 "미전달 시 동작은 현행과 동일"을 박아둔 선례를 그대로 따른다 (C-1, AC-4) |
| 선언×디스크 6상태 | `active`·있음→sync / `active`·없음→`not-cloned` / `deferred`·없음→skip(정상) / `deferred`·있음→sync + 선언 어긋남 보고 / 미선언·있음→`undeclared` / 환원 불가→`unknown` | `deferred`·있음은 가정이 아니라 예정된 경로다 — blend 3bd6507이 "재개 시 clone으로 복구"를 명시한다 (AC-5) |
| `state`는 도구가 변경하지 않음 | `deferred`·있음을 관측해도 파일을 고치지 않고 보고만 한다 | 선언 변경은 사람 결정이다 (C-6) |
| `init`은 탐지 기반 초안 | 기존 remote를 정규화해 `repos[]` 초안을 만든다. 기존 파일은 `--force` 없이 `CONFIG_EXISTS` 거부, `--dry-run`은 쓰지 않고 최상위 `draft` 키 반환 | `worktree-tool cmd_init`이 이미 같은 계약을 집행한다. 새로 설계하지 않는다 (AC-6) |
| clone은 전용 서브명령 | `cmd_clone`은 스킬이 승인 게이트 통과 후에만 호출한다. `sync`는 clone하지 않는다 | git 호출을 도구에 두면 인자 리스트(`shell=False`) 방식이 유지된다. 스킬이 raw git을 셸로 부르면 인젝션 경로가 생긴다 (C-5, AC-8) |
| 로컬 파일시스템 경로는 정규화 대상이 아니다 | `normalize_repo_coord`는 `git@host:org/repo`·`ssh://host/org/repo`·`https://host/org/repo` 3형식만 환원한다. 절대경로·상대경로·`file://`는 환원하지 않고 None을 반환하며 `compare_repo_coord`가 `unknown`으로 판정해 pull을 보류한다 | 임의 경로의 마지막 2세그먼트를 `org/repo`로 읽으면 `/Users/me/projects/backend`가 `projects/backend`가 된다. 원격 좌표가 아니라 우연히 같은 모양인 문자열이며 서로 다른 레포가 같은 키로 충돌한다 — H-1(미탐)을 새로 만드는 설계다. RED 재작성 중 실제로 이 환원을 요구하는 테스트가 나왔고, 계약에 배제가 명시돼 있지 않아 발생했다 (C-2, C-4, H-1) |
| 대소문자는 비교에서 무시 | `normalize_repo_coord`가 환원 결과를 소문자로 접어 비교한다. 보고·초안 출력은 선언 원문 표기를 유지한다 | GitHub·GitLab은 `org/repo` 해석이 대소문자 구분 없이 같은 레포로 리다이렉트된다. 구분하면 `Storelink-IO/Blend` 선언이 실제 `storelink-io/blend`를 `mismatch`로 막는 오탐이 된다. 평가자 advisory 2 — 미정의 구간이라 구현자 재량으로 갈리는 것을 차단한다 (C-2, AC-2) |
| `install-mac.sh` 무변경 | 신규 `schema/` 하위 디렉토리는 배포에 자동 포함된다 | 실측: `scripts/install-mac.sh:1288`의 `install_dir "$opal_dir/tools" "$opal_home/tools"`가 `opal/tools/` 전체를 복사한다 (C-7) |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. `org/repo` 정규화와 반증 테스트 | PM | `opal/tools/git-sync-tool/tests/test_git_sync_tool.py`, `opal/tools/git-sync-tool/git_sync_tool.py` | **테스트를 먼저 추가해 실패를 확인한 뒤 구현한다.** 반증 3쌍(`storelink-io/blend` vs `storelink-io/blend-admin`, `storelink-io/blend` vs `other-org/blend`, 접두 유사쌍)이 `mismatch`를 내는 케이스, 동치 4형식(`git@alias:org/repo`·`git@github.com:org/repo`·`https://host/org/repo.git`·`ssh://git@host/org/repo`)이 같은 키로 환원되는 케이스, 원격 0개·파싱 불가가 `unknown`을 내는 케이스를 추가한다. 이어서 `normalize_repo_coord(url)`(환원 실패 시 None)과 `compare_repo_coord(declared, actual)` 2함수를 신설하고 `exports`에 등재한다 | 없음 | P1 | AC-1, AC-2, AC-3, AC-9, C-2, C-4 |
| W-2. `workspace.json` 스키마와 선언 로더 | PM | `opal/tools/git-sync-tool/schema/workspace.schema.json`(신규), `git_sync_tool.py`, `tests/test_git_sync_tool.py` | 스키마 신설 — `required: [schema_version, host, org, repos]`, `repos[]`는 `required: [dir, repo, state]`, `state`는 `enum: [active, deferred]`, `additionalProperties: false`. `load_workspace_config(project_root)` 신설 — 파일 부재 시 오류가 아니라 `None` 반환. `validate_workspace_config()`를 hand-rolled로 작성(`worktree_tool.py validate_worktree_config` 선례) — `dir`이 basename이 아니면 거부, `dir`·`repo` 중복 거부, `state` enum 위반 거부. `ERROR_CODES`에 `WORKSPACE_CONFIG_INVALID`·`WORKSPACE_CONFIG_MALFORMED` 2건 추가 | W-1 | P2 | AC-10, C-6, C-7 |
| W-3. `init` 서브명령 | PM | `git_sync_tool.py`, `tests/test_git_sync_tool.py` | `cmd_init(args)` 신설 + `subparsers.add_parser("init")`. 순회 대상 각 자식의 `origin`을 W-1 정규화로 환원해 `repos[]` 초안을 만든다. `org`는 환원 결과의 최빈값, `host`는 `github.com` 고정 기본값(추측하지 않으며 다르면 사용자가 수정), `state`는 전건 `active`(`deferred`를 추측하지 않는다). 기존 파일이 있으면 `--force` 없이 `CONFIG_EXISTS`로 거부하고 파일을 건드리지 않는다. `--dry-run`은 쓰지 않고 최상위 `draft` 키로만 반환한다 | W-2 | P3 | AC-6, C-6 |
| W-4. 6상태 판정과 `sync` 통합 | PM | `git_sync_tool.py`, `tests/test_git_sync_tool.py` | `cmd_sync`에 선언 대조를 삽입한다. `load_workspace_config()`가 `None`이면 기존 분기를 그대로 타고 응답 키 집합을 바이트 동일하게 유지한다(회귀 테스트로 고정). 선언이 있으면 `reason` enum에 `not-cloned`·`undeclared`·`undeclared-active`·`unknown` 4종을 추가하고, `repositories[]`에 정규화 키 `repo` 필드를 추가한다(URL 원문 미포함). `mismatch`·`unknown`은 `process_repo`의 pull 경로에 진입시키지 않는다 | W-3 | P4 | AC-4, AC-5, AC-7, C-1, C-3, C-4 |
| W-5. `clone` 서브명령 | PM | `git_sync_tool.py`, `tests/test_git_sync_tool.py` | `cmd_clone(args)` 신설 + `subparsers.add_parser("clone")`. 인자는 `<path> --dir <basename> --url <clone-url>`이며 스킬이 승인 게이트 통과 후에만 호출한다. `git clone`은 기존 `_run_git` 동형의 인자 리스트 방식으로 실행한다. 대상 디렉토리가 이미 존재하면 거부한다. 응답에 `--url` 값을 싣지 않는다 | W-4 | P5 | AC-8, C-3, C-5 |
| W-6. SKILL 확장 | PM | `opal/skills/opal-workspace-sync/SKILL.md` | STEP 1에 선언 조회 분기를 추가한다(부재 시 현행 3분기 그대로). STEP 3 보고서에 `not-cloned`·`undeclared`·`mismatch`·`unknown` 표시를 추가하고, 원문 URL은 `mismatch`·`unknown`에서만 화면에 노출한다. STEP 4 사유별 카탈로그에 `not-cloned → clone` 행을 추가하고, 접속 방식은 레포당이 아니라 **세션 1회** 질의한다고 명시한다 | W-5 | P6 | AC-8, C-5 |
| W-7. 도구 README 갱신 | PM | `opal/tools/git-sync-tool/README.md` | 서브명령을 `sync` 단일에서 `sync`·`init`·`clone` 3종으로 갱신한다. `workspace.json` 계약, 6상태표, 3진 판정, 선언 부재 시 현행 동일 보장을 기술한다 | W-5 | P6 | C-7 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. 정규화가 서로 다른 레포를 같다고 판정한다(미탐) | 선언×디스크 대조가 `match`를 반환해 `process_repo`가 pull을 수행한다 | 엉뚱한 저장소를 pull하고 사용자에게 아무 신호도 뜨지 않는다. 조용한 손상 | W-1에서 반증 케이스를 먼저 작성해 RED를 확인한 뒤 구현한다. 동치 케이스만으로는 "무조건 match 반환" 구현이 전 테스트를 통과한다 |
| H-2. host를 비교에서 제외해 서로 다른 호스트의 동명 레포가 같다고 판정된다 | `github.com/o/r`과 `gitlab.com/o/r`이 `match` | 실무 발생 빈도가 낮고, 막으려면 host 관리가 되돌아온다 | 수용된 트레이드오프로 확정한다. README와 스키마 `_help`에 명시해 사용자가 알고 쓰게 한다 |
| H-3. 선언 부재 폴백이 깨진다 | `workspace.json`이 없는 모든 프로젝트의 `//opws` | 매니페스트를 만들지 않은 프로젝트 전건이 영향받는다 | W-4에 선언 부재 회귀 테스트를 둬 응답 키 집합 동일성을 고정한다(AC-4) |
| H-4. `install_dir`이 신규 `schema/` 하위를 복사하지 않는다 | 배포본 `~/.opal/tools/git-sync-tool/schema/` 부재 | 소스에서는 통과하고 배포본에서만 실패한다 | 실측으로 `opal/tools/` 전체 복사를 확인했다(`scripts/install-mac.sh:1288`). W-7 완료 후 install 재실행하고 배포 경로 실재를 직접 확인한다 |

## Release and recovery

- 적용 순서: P1 → P6 순차. 같은 파일(`git_sync_tool.py`)을 연속 수정하므로 병렬 배치를 만들지 않는다. P6의 W-6·W-7만 서로 다른 파일이라 동시 수행 가능하다. 전 그룹 완료 후 `scripts/install-mac.sh` 재실행으로 배포한다.
- 검증 범위: 결정론 단위(정규화 3진·스키마 검증·6상태 매트릭스)는 기존 pytest 자산에 추가한다. 회귀는 선언 부재 경로의 응답 동일성 1건이다. 실제 연동은 배포 후 blend 워크스페이스(`/Volumes/Data/StoreLinkStudio/blend`)에 실호출하여 4개 자식과 root 판정을 확인한다.
- 실패 시: 도구 변경은 순수 추가이므로 커밋 되돌림으로 복구된다. 프로젝트의 `workspace.json`은 자산이므로 파일을 지우면 선언 부재 폴백으로 즉시 현행 동작에 복귀한다.
