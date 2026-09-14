# git-sync-tool

> 워크스페이스 아래 여러 독립 git 저장소를 순회하며 clean + fast-forward 가능한 것만 안전 최신화하는 결정론 집행 CLI
> 소스: `opal/tools/git-sync-tool/` | 배포: `~/.opal/tools/git-sync-tool/`
> 의존성: `~/.opal/.venv/bin/python` (표준 라이브러리만 — `argparse`/`json`/`pathlib`/`sys`/`subprocess`) + 로컬 **git 2.22+**

## 개요

`git-sync-tool`은 지정 경로 아래의 git 저장소들을 순회해, **문제가 없는 저장소만** `git pull --ff-only`로 최신화하고 나머지는 손대지 않고 사유와 함께 보고한다.

- **자율 조치가 없다** — `stash`/`rebase`/`force`/`commit`/`push`를 일절 수행하지 않는다. dirty·diverged·detached·no-upstream 저장소는 skip 후 보고만 한다(user sovereignty).
- git 호출은 전부 인자 리스트(`shell=False`) 방식이라 셸 인젝션 경로가 없다.
- git 2.22+가 필요한 이유는 `git rev-list --left-right --count`를 ahead/behind 계산에 쓰기 때문이다.
- 호출자는 `opal-workspace-sync` 스킬(alias `opws`)이다 — 대상 결정·보고서·승인 게이트는 스킬이 담당하고, 이 도구는 순회·판정·pull만 집행한다.

## 호출 형식 — 단일 서브명령

```bash
~/.opal/tools/git-sync-tool/run.sh sync <path> [--root <root_repo_path>]
```

개발 중에는 소스 경로로 직접 호출한다.

```bash
bash opal/tools/git-sync-tool/run.sh sync <path> [--root <root_repo_path>]
```

| 인자 | 필수 | 설명 |
|------|------|------|
| `sync` | O | 유일한 서브명령. 생략하면 argparse가 거부한다(`required=True`) |
| `path` (위치) | O | 순회 대상 경로 |
| `--root <경로>` | X | 기본값 `None`. 순회 대상 밖의 상위 root 저장소를 대상 **선두**에 추가한다 |

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

## 저장소별 판정 순서

순서가 고정돼 있고, 각 단계에서 확정되면 즉시 반환한다.

| 순서 | 검사 | 결과 |
|------|------|------|
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

**`already-current`는 `total`에만 들어가고 `updated`/`skipped`/`failed` 어디에도 계상되지 않는다.** 따라서 `updated + skipped + failed == total`이 성립하지 않는 것이 정상이다 — 차이가 곧 이미 최신인 저장소 수다.

## 사용 예시

```bash
# 워크스페이스 컨테이너 순회 (직속 자식 1단계)
~/.opal/tools/git-sync-tool/run.sh sync /Users/me/workspace

# 단일 저장소만 최신화 (<path>/.git 존재 시 자동으로 단일 루트 모드)
~/.opal/tools/git-sync-tool/run.sh sync /Users/me/workspace/my-repo

# workspace 하위 저장소들 + 상위 프로젝트 저장소까지 함께
~/.opal/tools/git-sync-tool/run.sh sync /Users/me/project/workspace --root /Users/me/project
```

## 오류 코드 (ERROR_CODES SSOT)

`git_sync_tool.py`의 `ERROR_CODES` 딕셔너리가 SSOT이며 **2종뿐**이다. 저장소 개별 문제는 오류가 아니라 `repositories[].reason`으로 보고되므로 여기에 없다.

| 코드 | 발생 지점 | 의미 |
|------|----------|------|
| `PATH_NOT_FOUND` | `sync <path>` / `--root` | 지정한 경로가 존재하지 않음 |
| `NOT_A_DIRECTORY` | `sync <path>` / `--root` | 지정한 경로가 디렉토리가 아님 |

```json
{"ok": false, "error": "PATH_NOT_FOUND", "message": "지정한 경로가 존재하지 않습니다: /no/such/dir"}
```

## 종료 코드

| 코드 | 의미 |
|------|------|
| `0` | 순회 완료 — 개별 저장소에 `skipped`/`failed`가 있어도 0이다 |
| `1` | `PATH_NOT_FOUND` / `NOT_A_DIRECTORY`, 그리고 `run.sh`의 venv 부재 선검사 |
| `2` | argparse 인자 오류(서브명령 누락, 위치 인자 `path` 누락 등) |

**exit 0은 "순회가 끝났다"는 뜻이지 "전부 최신화됐다"는 뜻이 아니다.** 호출자는 `summary.failed`와 `repositories[].reason`을 반드시 읽어야 한다.

exit 2 경로는 argparse 기본 동작이라 JSON이 아닌 usage 텍스트를 stderr로 내보낸다. `run.sh`의 venv 부재 메시지도 stdout이 아닌 **stderr**로 나간다.

## 제약

- **재귀 순회가 없다** — 2단계 이상 중첩된 저장소는 대상에서 빠지며, 빠졌다는 사실도 출력에 나타나지 않는다.
- submodule을 인식하지 않는다.
- 원격 인증(자격증명 프롬프트 등)은 도구가 다루지 않는다 — `fetch`가 실패하면 `fetch-failed`로 동일하게 접힌다. `reason`만으로는 네트워크 실패와 인증 실패, rev-list 파싱 실패가 구분되지 않는다.
