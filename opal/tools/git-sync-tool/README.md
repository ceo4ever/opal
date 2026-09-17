# git-sync-tool

> 워크스페이스 아래 여러 독립 git 저장소를 순회하며 clean + fast-forward 가능한 것만 안전 최신화하고, 선언 파일이 있으면 멤버십까지 대조하는 결정론 집행 CLI
> 소스: `opal/tools/git-sync-tool/` | 배포: `~/.opal/tools/git-sync-tool/`
> 의존성: `~/.opal/.venv/bin/python` (표준 라이브러리만 — `argparse`/`json`/`pathlib`/`sys`/`subprocess`) + 로컬 **git 2.22+**

## 개요

`git-sync-tool`은 지정 경로 아래의 git 저장소들을 순회해, **문제가 없는 저장소만** `git pull --ff-only`로 최신화하고 나머지는 손대지 않고 사유와 함께 보고한다.

- **자율 조치가 없다** — `stash`/`rebase`/`force`/`commit`/`push`를 일절 수행하지 않는다. dirty·diverged·detached·no-upstream 저장소는 skip 후 보고만 한다(user sovereignty).
- git 호출은 전부 인자 리스트(`shell=False`) 방식이라 셸 인젝션 경로가 없다.
- git 2.22+가 필요한 이유는 `git rev-list --left-right --count`를 ahead/behind 계산에 쓰기 때문이다.
- 호출자는 `opal-workspace-sync` 스킬(alias `opws`)이다 — 대상 결정·보고서·승인 게이트는 스킬이 담당하고, 이 도구는 순회·판정·pull만 집행한다.
- `{프로젝트}/.opal/workspace.json` 선언 파일이 있으면 **선언×디스크를 대조**해 누락·드리프트를 드러낸다. 선언 파일이 없으면 대조 분기를 타지 않아 도입 전과 동작이 동일하다.

## 호출 형식 — 서브명령 3종

```bash
~/.opal/tools/git-sync-tool/run.sh sync  <path> [--root <root_repo_path>]
~/.opal/tools/git-sync-tool/run.sh init  <path> [--dry-run] [--force]
~/.opal/tools/git-sync-tool/run.sh clone <path> --dir <basename> --url <clone-url>
```

개발 중에는 소스 경로로 직접 호출한다(`bash opal/tools/git-sync-tool/run.sh ...`). 서브명령을 생략하면 argparse가 거부한다(`required=True`).

### `sync` — 순회·판정·pull

| 인자 | 필수 | 설명 |
|------|------|------|
| `path` (위치) | O | 순회 대상 경로 |
| `--root <경로>` | X | 기본값 `None`. 순회 대상 밖의 상위 root 저장소를 대상 **선두**에 추가한다 |

### `init` — 선언 초안 생성

기존 `origin`을 정규화해 선언 초안을 만든다. 기록 위치는 위 §선언 파일 위치 판정과 같다.

**저장소 경로는 받지 않는다.** 단일 저장소를 훑으면 그 저장소 자신이 유일한 "자식"이 되어 의미 없는 초안이 나오므로, 컨테이너 경로를 추측해 내려가지 않고 거부한다.

| 인자 | 필수 | 설명 |
|------|------|------|
| `path` (위치) | O | 순회 대상 **컨테이너** 경로. `<path>/.git`이 있으면 `NOT_A_WORKSPACE_CONTAINER`로 거부한다 |
| `--dry-run` | X | 파일을 쓰지 않고 최상위 `draft` 키로 초안만 반환한다 |
| `--force` | X | 기존 파일을 덮어쓴다. 없으면 `CONFIG_EXISTS`로 거부하고 파일을 건드리지 않는다 |

`host`는 `github.com` 고정 기본값이고 `org`는 환원 결과의 최빈값이며, `state`는 **전건 `active`**다 — `deferred`는 사람의 결정이므로 추측하지 않는다.

초안에서 빠지는 자식 2종은 각각 따로 보고된다.

| 필드 | 대상 | 이유 |
|------|------|------|
| `unresolved[]` | 좌표를 환원하지 못한 자식(원격 부재·로컬 경로 등) | 추측하지 않는다 |
| `other_org[]` | 다수 `org`와 다른 조직의 자식 | 선언의 `repo`는 `org` 아래 경로이므로 이 형식으로 표현할 수 없다. 억지로 넣으면 `org/다른org/repo`로 읽힌다 |

### `clone` — 승인 후 클론

`not-cloned` 저장소를 스킬의 승인 게이트 통과 후에 클론한다. `sync`는 클론하지 않는다.

| 인자 | 필수 | 설명 |
|------|------|------|
| `path` (위치) | O | 클론할 부모(순회 대상) 경로 |
| `--dir` | O | 생성할 디렉토리 basename. 경로 구분자가 있으면 `INVALID_DIR` |
| `--url` | O | clone 원본 URL. **응답에 싣지 않는다** |

대상 디렉토리가 이미 존재하면 `DIR_EXISTS`로 거부한다 — 덮어쓰지 않는다.

## 대상 결정 규칙

```
<path>/.git 이 존재       → <path> 1개만 처리한다 (단일 루트)
그렇지 않으면             → <path>의 직속 자식 1단계만, 이름순으로, child/.git 이 있는 것만
```

**재귀하지 않는다.** 손자 디렉토리의 저장소는 대상이 아니다.

`--root`는 `<프로젝트>/workspace`를 순회하면서 `<프로젝트>` 자체도 함께 최신화하고 싶을 때 쓴다.

- 경로 부재 → `PATH_NOT_FOUND`, 비디렉토리 → `NOT_A_DIRECTORY`로 거부한다.
- **`.git`이 없으면 오류가 아니라 조용히 제외한다** — `.git` 없는 경로에서 git을 실행하면 상위 저장소로 올라가 엉뚱한 저장소를 조작하기 때문이다.
- 순회 결과와 중복되면 중복 계상하지 않는다.

## 선언 대조 — `workspace.json` (조건부)

선언 파일이 있으면 순회를 시작하기 전에 읽어 선언×디스크를 대조한다. 스키마 계약은 `schema/workspace.schema.json`이 소유한다.

**선언 파일 위치 판정**은 두 단계다.

| 조건 | 프로젝트 루트 | 선언 파일 |
|------|--------------|----------|
| `<path>/.opal/`이 있다 | `<path>` 자신 | `<path>/.opal/workspace.json` |
| 없다 | `<path>`의 부모 | `<path>/../.opal/workspace.json` |

`<프로젝트>/workspace`를 순회하는 기본 형태에서는 부모가 프로젝트 루트다. 프로젝트 경로를 직접 주면 그 경로 자신이 루트다 — 부모 고정 규칙만 두면 이 경우 선언 파일이 **레포 밖 한 단계 위**로 잡힌다.

```json
{
  "schema_version": 1,
  "host": "github.com",
  "org": "storelink-io",
  "repos": [
    {"dir": "blend-admin", "repo": "blend-admin", "state": "active"},
    {"dir": "blend-batch", "repo": "blend-batch", "state": "deferred"}
  ]
}
```

- `dir`은 basename만 허용한다(경로 구분자·`.`·`..` 거부). `dir`·`repo` 중복도 거부한다.
- `schema_version`은 `1`·`"1"`·`"1.0"` 표기를 모두 받는다. 사람이 손으로 쓰는 파일이고 표기 차이는 판정을 바꾸지 않는다.
- 사람용 부가 필드로 최상위 `_help`, 항목의 `_help`·`note`·`clone_branch`를 받는다. **그 밖의 키는 거부한다** — `stat` 같은 오타가 조용히 통과하면 `state` 판정이 사라진 줄 모른 채 동작한다.
- `repo`는 **항상 최상위 `org` 아래의 경로**다. 짧은 이름이면 `org/repo`, subgroup이면 `org/team/repo`가 된다. `/` 포함을 "전체 좌표"로 달리 해석하지 않는다 — 다른 조직을 쓰려고 `repo`에 org를 적으면 좌표가 어긋나 `mismatch`로 드러난다.
- `state`는 `active` | `deferred` 둘뿐이다. **도구가 `state`를 자동으로 바꾸지 않는다** — 선언 변경은 사람 결정이다.
- 스키마 위반은 `WORKSPACE_CONFIG_INVALID`, JSON 파싱 실패는 `WORKSPACE_CONFIG_MALFORMED`로 **한 저장소도 건드리기 전에** 거부한다.

### 정체성 키는 host를 뺀 경로 전체다 — 접속 방식은 비교하지 않는다

환원 대상은 원격 좌표 3형식뿐이다.

| 입력 | 환원 결과 |
|------|----------|
| `git@github-alias:storelink-io/blend` | `storelink-io/blend` |
| `git@github.com:storelink-io/blend` | `storelink-io/blend` |
| `https://github.com/storelink-io/blend.git` | `storelink-io/blend` |
| `ssh://git@github.com/storelink-io/blend` | `storelink-io/blend` |
| `https://gitlab.com/orgA/team/repo` | `orgA/team/repo` (계층을 자르지 않는다) |
| `https://host/gitlab/org/repo` (self-hosted 서브패스) | `gitlab/org/repo` — 접두도 좌표의 일부다. 이 경우 선언의 `org`를 `gitlab/org`로 적어야 `match`가 된다 |
| `/Users/me/projects/blend` · `file://...` | **환원하지 않음** (`null`) |

- **host·프로토콜·후행 `.git`·대소문자는 비교에서 배제한다.** 같은 레포를 사용자마다 다른 접속 방식으로 두어도 판정이 갈리지 않는다.
  - **수용한 트레이드오프**: host를 비교하지 않으므로 `github.com/o/r`과 `gitlab.com/o/r`은 같은 좌표로 판정된다. 실무 발생 빈도가 낮고, 막으려면 host 관리 비용이 돌아온다.
- **경로 계층을 자르지 않는다.** 마지막 2세그먼트만 취하면 GitLab subgroup에서 `orgA/team/repo`와 `orgB/team/repo`가 같은 키가 되어 서로 다른 조직의 저장소를 조용히 pull한다(H-1 미탐). 자르지 않으면 시끄러운 `mismatch`가 날 뿐이다.
- 로컬 파일시스템 경로는 환원하지 않는다. 임의 경로의 마지막 2세그먼트를 `org/repo`로 읽으면 서로 무관한 경로가 같은 키로 충돌해 **미탐**(다른 레포를 같다고 판정)을 만든다.
- origin 설정 원문은 `git config --get remote.origin.url`로 읽는다. `git remote get-url`은 `insteadOf` 재작성을 적용하는데, 그건 접속 방식이지 레포 정체성이 아니다.

### 3진 판정과 6상태

대조 결과는 `match` / `mismatch` / `unknown` 3진이다. **한쪽이라도 환원 불가면 `unknown`이며, `unknown`은 일치로 간주하지 않고 pull을 보류한다**(fail-closed). 미탐은 엉뚱한 저장소를 조용히 pull하는 손상이고, 오탐은 시끄러울 뿐이다.

| 선언 | 디스크 | `declaration` | `reason` | pull |
|------|--------|---------------|----------|------|
| `active` | 있음·좌표 일치 | `match` | 순회 판정 | 수행 |
| `active` | 있음·좌표 불일치 | `mismatch` | `mismatch` | **보류** |
| `active`/`deferred` | 있음·환원 불가 | `unknown` | `unknown` | **보류** |
| `active` | 없음 | `not-cloned` | `not-cloned` | — (`clone` 제안 대상) |
| `deferred` | 없음 | — | — | 보고하지 않음 (의도된 상태) |
| `deferred` | 있음 | `undeclared-active` | 순회 판정 | 수행 + 선언 어긋남 보고 |
| 미선언 | 있음 | `undeclared` | `undeclared` | **보류** |

`--root`로 추가된 저장소는 워크스페이스 멤버십 선언의 대상이 아니므로 `declaration`이 `null`이다.

**선언 파일이 없으면 이 절 전체가 적용되지 않는다.** 대조 분기를 타지 않고 `repo`·`declaration`·`workspace_config` 키도 응답에 나타나지 않으므로, 선언을 만들지 않은 프로젝트의 동작은 이 기능 도입 전과 동일하다.

## 저장소별 판정 순서

순서가 고정돼 있고, 각 단계에서 확정되면 즉시 반환한다.

선언 파일이 있으면 **0단계(선언 대조)가 먼저**다 — `mismatch`·`unknown`·`undeclared`는 아래 순서에 진입하지 않고 fetch 이전에 확정된다.

| 순서 | 검사 | 결과 |
|------|------|------|
| 0 | 선언 대조 (선언 파일 있을 때만) | `skipped` / `mismatch`·`unknown`·`undeclared` |
| 1 | `git symbolic-ref -q HEAD` 실패 | `skipped` / `detached` |
| 2 | `@{u}` 조회 실패 | `skipped` / `no-upstream` |
| 3 | `git status --porcelain` 출력 있음 | `skipped` / `dirty` |
| 4 | `git fetch --all --prune` 실패 | `failed` / `fetch-failed` |
| 5 | `rev-list --left-right --count @{u}...HEAD` 실패 또는 출력이 2토큰이 아님 | `failed` / `fetch-failed` |
| 6 | ahead > 0 **그리고** behind > 0 | `skipped` / `diverged` |
| 7 | behind == 0 | `already-current` |
| 8 | behind > 0, ahead == 0 → `git pull --ff-only` | 성공 `updated` / 실패 `failed`+`fetch-failed` |

**detached를 no-upstream보다 먼저 판정하는 이유**: detached HEAD에서는 `@{u}` 조회 자체가 fatal로 실패해 두 상태가 구분되지 않는다. 순서를 바꾸면 detached가 no-upstream으로 오분류된다.

## 출력 형식

```json
{"ok": true, "error": null, "command": "sync",
 "workspace": "<절대경로>",
 "root": "<절대경로>|null",
 "repositories": [{"name": "...", "branch": "...", "upstream": "...", "status": "...", "reason": null,
                   "ahead": 0, "behind": 3, "prev_head": "abc1234", "new_head": "def5678",
                   "pulled_commits": 3}],
 "summary": {"total": 5, "updated": 1, "skipped": 2, "failed": 0}}
```

- `status` ∈ `updated` | `skipped` | `failed` | `already-current`
- `reason` ∈ `detached` | `no-upstream` | `dirty` | `diverged` | `fetch-failed` (정상이면 `null`)
- `root`: `--root`로 추가된 저장소의 절대경로. 미전달이거나 `.git` 부재로 제외됐으면 `null`이며, 추가됐으면 그 저장소가 `repositories[]` 선두다.
- `pulled_commits`는 ff pull 성공 시 `behind` 값과 같고, 그 외에는 0이다.

선언 파일이 있을 때만 다음이 추가된다 — 없으면 키 자체가 나타나지 않는다.

- `workspace_config` (최상위): 대조에 사용한 선언 파일 절대경로
- `repo`: 실제 origin에서 환원한 `org/repo` 좌표. 환원 불가면 `null`
- `declaration`: `match` | `mismatch` | `unknown` | `not-cloned` | `deferred` | `undeclared` | `undeclared-active` (`--root` 저장소는 `null`)
- `reason`에 `mismatch` | `unknown` | `not-cloned` | `deferred` | `undeclared` 5종이 추가된다

**선언됐는데 디스크에 없는 레포는 `state`와 무관하게 전부 보고된다.** `active`는 조치가 필요한 누락(`not-cloned`), `deferred`는 의도된 상태(`deferred`)로 구분될 뿐이다. 경고를 내지 않는 것과 출력에서 지우는 것은 다르다 — 지우면 선언해 둔 레포가 어디에도 나타나지 않아 드리프트 탐지가 절반만 작동한다.

**응답 어디에도 원격 URL 원문을 싣지 않는다.** 도구 출력은 DONE.md·brain·태스크 문서로 흘러가므로, 사용자마다 다른 접속 방식이 영속 기록에 굳을 통로를 만들지 않는다. URL 원문이 필요한 `mismatch`·`unknown` 진단은 호출자가 렌더 시점에 직접 읽어 화면에만 표시한다.

**`already-current`는 `total`에만 들어가고 `updated`/`skipped`/`failed` 어디에도 계상되지 않는다.** 따라서 `updated + skipped + failed == total`이 성립하지 않는 것이 정상이다 — 차이가 곧 이미 최신인 저장소 수다.

## 사용 예시

```bash
# 워크스페이스 컨테이너 순회 (직속 자식 1단계)
~/.opal/tools/git-sync-tool/run.sh sync /Users/me/workspace

# 단일 저장소만 최신화 (<path>/.git 존재 시 자동으로 단일 루트 모드)
~/.opal/tools/git-sync-tool/run.sh sync /Users/me/workspace/my-repo

# workspace 하위 저장소들 + 상위 프로젝트 저장소까지 함께
~/.opal/tools/git-sync-tool/run.sh sync /Users/me/project/workspace --root /Users/me/project

# 선언 초안을 먼저 확인하고(파일 안 씀), 확정되면 기록
~/.opal/tools/git-sync-tool/run.sh init /Users/me/project/workspace --dry-run
~/.opal/tools/git-sync-tool/run.sh init /Users/me/project/workspace

# not-cloned로 보고된 레포를 승인 후 클론
~/.opal/tools/git-sync-tool/run.sh clone /Users/me/project/workspace \
  --dir blend-admin --url git@github.com:storelink-io/blend-admin.git
```

## 오류 코드 (ERROR_CODES SSOT)

`git_sync_tool.py`의 `ERROR_CODES` 딕셔너리가 SSOT다. 저장소 개별 문제는 오류가 아니라 `repositories[].reason`으로 보고되므로 여기에 없다.

| 코드 | 발생 지점 | 의미 |
|------|----------|------|
| `PATH_NOT_FOUND` | 전 서브명령 / `--root` | 지정한 경로가 존재하지 않음 |
| `NOT_A_DIRECTORY` | 전 서브명령 / `--root` | 지정한 경로가 디렉토리가 아님 |
| `WORKSPACE_CONFIG_INVALID` | `sync` | 선언 파일이 스키마를 위반함. `details[]`에 위반 사유가 담긴다 |
| `WORKSPACE_CONFIG_MALFORMED` | `sync` | 선언 파일이 유효한 JSON이 아님 |
| `CONFIG_EXISTS` | `init` | 선언 파일이 이미 존재함(`--force` 필요). 파일을 건드리지 않는다 |
| `INVALID_DIR` | `clone` | `--dir`가 basename이 아님 |
| `DIR_EXISTS` | `clone` | 대상 디렉토리가 이미 존재함. 덮어쓰지 않는다 |
| `CLONE_FAILED` | `clone` | `git clone` 실패. stderr에 URL 원문이 섞이므로 응답에 싣지 않는다 |
| `NOT_A_WORKSPACE_CONTAINER` | `init` | 경로가 저장소 자체임(`<path>/.git` 존재). 자식을 담은 컨테이너 경로가 필요하다 |

```json
{"ok": false, "error": "PATH_NOT_FOUND", "message": "지정한 경로가 존재하지 않습니다: /no/such/dir"}
```

## 종료 코드

| 코드 | 의미 |
|------|------|
| `0` | 순회 완료 — 개별 저장소에 `skipped`/`failed`가 있어도 0이다 |
| `1` | `ERROR_CODES` 전건(경로 오류·선언 파일 오류·`CONFIG_EXISTS`·`DIR_EXISTS`·`CLONE_FAILED` 등), 그리고 `run.sh`의 venv 부재 선검사 |
| `2` | argparse 인자 오류(서브명령 누락, 위치 인자 `path` 누락 등) |

**exit 0은 "순회가 끝났다"는 뜻이지 "전부 최신화됐다"는 뜻이 아니다.** 호출자는 `summary.failed`와 `repositories[].reason`을 반드시 읽어야 한다.

exit 2 경로는 argparse 기본 동작이라 JSON이 아닌 usage 텍스트를 stderr로 내보낸다. `run.sh`의 venv 부재 메시지도 stdout이 아닌 **stderr**로 나간다.

## 제약

- **재귀 순회가 없다** — 2단계 이상 중첩된 저장소는 대상에서 빠지며, 빠졌다는 사실도 출력에 나타나지 않는다.
- submodule을 인식하지 않는다.
- 선언 대조의 정체성 키에 host가 없다 — 서로 다른 호스트의 동명 레포는 구분되지 않는다(위 트레이드오프 절 참조).
- **한 선언 파일은 `org` 하나만 표현한다.** `repo`가 항상 `org` 아래 경로이므로, 다른 조직의 자식을 같은 파일에서 `active`로 선언할 방법이 없다. 그런 자식은 `init`이 `other_org[]`로 드러내고 `sync`는 `undeclared`로 보고한다 — 조용히 사라지지 않지만 `match`로 만들 수는 없다. 여러 조직을 아우르는 워크스페이스는 현재 형식의 범위 밖이다.
- 원격 인증(자격증명 프롬프트 등)은 도구가 다루지 않는다 — `fetch`가 실패하면 `fetch-failed`로 동일하게 접힌다. `reason`만으로는 네트워크 실패와 인증 실패, rev-list 파싱 실패가 구분되지 않는다.
