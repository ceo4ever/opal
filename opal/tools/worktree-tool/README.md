# worktree-tool

> 태스크별 코드 작업본을 git worktree로 격리하는 결정론 집행 CLI — 6서브명령 `create`/`list`/`status`/`remove`/`finalize`/`init`
> 소스: `opal/tools/worktree-tool/` | 배포: `~/.opal/tools/worktree-tool/`
> 의존성: `~/.opal/.venv/bin/python` (표준 라이브러리만 — `argparse`/`json`/`os`/`pathlib`/`posixpath`/`shutil`/`subprocess`/`sys`/`datetime`) + 로컬 **git 2.25+**(`sparse-checkout --cone` 사용)

## 개요

`.opal/worktree.json` 선언을 읽어 multi-repo(레포별 worktree)·monorepo(sparse-checkout) 2유형을 흡수한다.

- **all-or-nothing 생성** — `create`는 pre-flight 선검사를 전부 통과한 뒤에만 worktree를 만들고, 중간 실패 시 **자기 생성물만** 역순으로 롤백한다.
- **base-ref 1회 동결** — `create` 시점에 해석해 `.opal-worktrees/.meta/task_{NNN}.json`(worktree 밖)에 기록하고, `status`/`remove`는 그 값만 읽는다(재해석 없음).
- **브랜치를 삭제하지 않는다** — `remove`는 worktree 디렉토리와 슬롯 루트만 회수한다(user sovereignty). 자동 커밋·자동 머지·자동 제거가 없다.
- **비차단 진단** — `.gitignore` 멱등 보장, 캐시 볼륨, code-scan exclude, 동시 슬롯 수는 전부 `warnings[]`로만 보고하고 차단하지 않는다.
- `subprocess`는 전부 인자 리스트(`shell=False`)다.

계약 원문은 `opal/core/references/harness/worktree.md`가 소유한다. 이 문서는 CLI 표면만 다룬다.

## 설정 — `.opal/worktree.json`

문서 SSOT는 `opal/tools/worktree-tool/schema/worktree.schema.json`이다. 런타임에 이 스키마 파일을 로드하지는 않으며, 검증은 `validate_worktree_config()`가 직접 수행한다.

| 키 | 필수 | 기본값 | 설명 |
|----|------|-------|------|
| `layout` | O | — | `multi-repo` \| `monorepo` |
| `repos` | O | — | 격리 대상 경로 배열(프로젝트 루트 상대, 최소 1개). 절대경로·`..` 이탈은 `CONFIG_PATH_ESCAPE` |
| `branchTemplate` | X | `feat/OP-TASK-{NNN}` | 치환 토큰 `{NNN}`·`{slug}`·`{skill}` |
| `baseBranch` | X | 없음 | base-ref 명시 선언 |
| `copy` | X | `[]` | gitignore된 로컬 설정 파일 경로. `create`가 worktree로 복사하며 원본 부재는 비차단 경고 |
| `setup` | X | `[]` | `{cwd, run}` 객체 배열. **`create`는 실행하지 않고 `pending_setup[]`으로 열거만 한다**(lazy setup) |
| `portOffset` | X | `0` | 포트 오프셋 힌트. **도구는 응답에 출력만 하고 적용하지 않는다** |
| `taskCapsuleCone` | X | `[]` | monorepo 분기 전용 — `repos`에 이어 sparse-checkout cone에 전개 |
| `task_artifacts` | X | 없음 | multi-repo 분기 전용 — `repo`는 예약값 `"."`(루트 저장소)만 허용 |
| `baseBranchOverrides` | X | `{}` | multi-repo 분기 전용 — 키는 `repos[]` ∪ `{"."}`만 허용 |

**base-ref 3단 우선순위** (`resolve_base_ref`, 코드 1곳에 봉인): `baseBranch` 선언값 → `origin/HEAD`(symbolic-ref) → 현재 체크아웃 브랜치.

## 호출 형식

```bash
~/.opal/tools/worktree-tool/run.sh <command> --project-root <프로젝트 절대경로> [options]
```

`--project-root`는 **6서브명령 전부에서 필수**다.

## 6개 서브 명령

### 1. `init` — 설정 초안 생성

```bash
~/.opal/tools/worktree-tool/run.sh init --project-root <경로> [--force] [--dry-run]
```

프로젝트 구조를 탐지해 `.opal/worktree.json` 초안을 만든다(자동 생성이 아니라 초안 제시다).

- 루트 이하 최대 3 depth에서 독립 `.git` 디렉토리를 찾아 ≥1개면 `multi-repo`(그 경로들이 `repos`).
- 0개면 루트 자체가 git 레포일 때만, 루트가 추적하는 최상위 디렉토리 중 하위에 코드 manifest를 가진 것을 `monorepo`의 `repos`로 채운다.
- 둘 다 실패하면 `LAYOUT_UNDETERMINED`.
- `copy`는 항상 빈 배열, `portOffset`은 항상 0으로 두고 **추측하지 않는다**(로컬 설정 후보는 `_copy_candidates` 주석 키로만 제시).
- `task_artifacts`는 R-1~R-5 전건을 만족할 때만 제시하고, `baseBranchOverrides`는 추측하지 않는다.
- 기존 파일이 있으면 `--force` 없이 `CONFIG_EXISTS`로 거부하고 **파일을 건드리지 않는다.**
- `--dry-run`은 아무것도 쓰지 않고 최상위 `draft` 키로만 반환한다(이 경우 `CONFIG_EXISTS` 게이트 대상이 아니다).

---

### 2. `create` — 코드 작업본 생성

```bash
~/.opal/tools/worktree-tool/run.sh create --project-root <경로> --task <NNN> \
  [--slug <태스크명>] [--skill <약어>] [--task-folder <basename>]
```

**슬롯·브랜치 판정은 "존재"가 아니라 "점유"다.** 대상 경로가 `git worktree list --porcelain`에 실제 등록돼 있으면 `WORKTREE_EXISTS`, 브랜치가 다른 worktree에 체크아웃 중이면 `BRANCH_EXISTS`로 거부한다. 브랜치가 존재하되 미점유면 `worktree add <path> <branch>` 단일 명령으로 재사용한다 — **빈 디렉토리가 남아 있는 것은 차단 사유가 아니다.**

- `--task-folder`는 **basename만** 허용한다(경로 구분자·`..`·NUL 불가 → `TASK_FOLDER_INVALID`).
- canonical task path 6필드(`allocator_root`·`task_home`·`task_folder`·`task_path`·`artifact_repo`·`task_ownership_version`)를 응답과 메타에 발급하고, 불변식 `task_path == realpath(task_home/tasks/task_folder)`를 발급 시점에 검증한다.
- `task_artifacts` 미설정 multi-repo는 위치 필드를 발급하지 않으며, 그 상태에서 `--task-folder`가 명시되면 `TASK_ARTIFACT_REPO_MISSING`으로 중단한다.
- 부수 효과 이전에 루트 Git 적격을 **각각** 판정한다: R-1(루트가 git 저장소) · R-2(`tasks` 추적) · R-3(`.opal/AGENT.md` 추적) · R-4(`.opal/MEMORY.json` 추적). R-1 불만족이면 나머지는 판정 자체가 불가하므로 `['R-1']`만 보고한다. 판정 순서는 R-1~R-4 → 추적 범위 겹침 → R-5다.
- 생성은 루트 → 자식 순, 롤백은 역순(자식 → 루트)이다. multi-repo 롤백은 회수 실패 시 슬롯을 지워 흔적을 없애지 않고 잔존 entry를 `residual`로 보고한다(monorepo는 무조건 정리한다).

**성공 응답**:
```json
{"ok": true, "error": null, "command": "create", "task": "131",
 "allocator_root": "...", "task_home": "...", "task_folder": "...", "task_path": "...",
 "artifact_repo": ".", "task_ownership_version": 2,
 "layout": "multi-repo", "worktree_root": "<절대경로>", "branch": "feat/OP-TASK-131",
 "entries": [{"repo": "...", "path": "...", "branch": "...", "base_ref": "origin/main"}],
 "gitignore": "created|added|present", "copied": ["..."],
 "pending_setup": [{"cwd": "...", "run": "..."}], "port_offset": 0, "warnings": []}
```

---

### 3. `list` — 활성 슬롯 목록

```bash
~/.opal/tools/worktree-tool/run.sh list --project-root <경로>
```

```json
{"ok": true, "error": null, "command": "list", "project_root": "...", "layout": "...",
 "entries": [{"task": "...", "branch": "...", "worktree_root": "...", "exists": true}]}
```

---

### 4. `status` — 단일 슬롯 상태 (거부하지 않는다)

```bash
~/.opal/tools/worktree-tool/run.sh status --project-root <경로> --task <NNN>
```

entry별 `dirty`/`unpushed`/`merged`를 보고하며, 해석된 canonical 경로를 `task_path`·`task_path_source`로 함께 싣는다. 상태가 나쁘다고 거부하지 않는다 — 판정 결과를 보고할 뿐이다.

```json
{"ok": true, "error": null, "command": "status", "task": "131", "branch": "...", "worktree_root": "...",
 "entries": [{"repo": "...", "path": "...", "branch": "...", "base_ref": "...",
              "dirty": false, "unpushed": false, "merged": true}],
 "pending_setup": [], "task_path": "...", "task_path_source": "..."}
```

---

### 5. `remove` — 슬롯 회수

```bash
~/.opal/tools/worktree-tool/run.sh remove --project-root <경로> --task <NNN> [--force]
```

판정 순서가 고정돼 있다.

1. 미처리 memory index 요청(캡슐 파일 `memory-index-request.json`의 `body_sha256` 중 메타 `memory_index_requests_resolved`에 없는 건) → `MEMORY_INDEX_REQUEST_PENDING`
2. 3중 가드 `dirty` → `unpushed` → `unmerged` — **첫 위반에서 즉시 반환**

`--force`는 **가드 우회 전용**이다. 지정 시 위반을 넘기고 `bypassed_guards[]`에 코드를 모으며 `forced: true`를 응답에 싣는다.

회수 계약은 메타에 동결된 `layout`에 따라 갈린다.

- **multi-repo 전용**: entry를 생성의 역순(자식 → 루트)으로 순회하며 **경로 실재 × Git 등록** 2축으로 판정한다. 둘 다 없으면 이미 회수된 것으로 보고 skip한다(오류가 아니며 `--force`를 요구하지 않는다). 한쪽만 있으면 mismatch(`registration_without_path` 또는 `path_without_registration`)를 실은 `WORKTREE_REMOVE_FAILED`로 차단·보존하며 **자동 복구하지 않는다**(`git worktree prune`을 호출하지 않고 미등록 잔여 디렉토리를 삭제하지 않는다). 전 entry 회수가 성공한 뒤에만 메타와 슬롯 루트(`task_{NNN}/`)를 삭제하고, 하나라도 실패하면 메타·슬롯을 보존해 재시도 여지를 남긴다. `--force`는 이 실패 판정을 우회하지 않는다.
- **monorepo·비워크트리**: 경로 부재 시 `WORKTREE_NOT_FOUND`(`--force`면 skip)를 반환하고, 반환값을 검사하지 않는 무조건 회수를 수행한다.

`.opal-worktrees/`와 `.meta/` 디렉토리 자체는 남긴다. `remove`는 canonical path 해석기를 호출하지 않는다.

```json
{"ok": true, "error": null, "command": "remove", "task": "131",
 "removed": ["<path>"], "forced": false, "bypassed_guards": []}
```

---

### 6. `finalize` — merge 후 귀속 후처리 확정

```bash
~/.opal/tools/worktree-tool/run.sh finalize --project-root <경로> --task <NNN>
```

DONE.md의 `## 회고적 학습 후보` 선언 집합 **D**(∪ `.opal/brain/index.md`·`.opal/brain/log.md`·`.opal/MEMORY.json`)와, `git status --porcelain -z -uall`을 `.opal/brain/**`·`.opal/MEMORY.json`으로 필터한 관측 집합 **S**를 레포 루트 상대 POSIX 경로로 정규화해 대조한다.

- `S ⊆ D`이면 관측 경로만 stage해 단일 귀속 commit으로 확정한다. 아니면 `ATTRIBUTION_COMMIT_BLOCKED`(위반 경로 동봉)로 거부한다.
- `.opal/MEMORY.json`의 선행 diff는 allocator의 `last_task_number` 변경만 허용한다.
- 판정 범위 밖(소스·태스크 문서)의 dirty는 판정 대상이 아니며, `remove`의 이진 dirty 가드는 이 경로에서 쓰지 않는다.
- 상태 전이는 `completed_unmerged → attribution_pending → closed`이고, commit·clean 검증 실패 시 `attribution_pending`에 머문다.
- 이미 `closed`면 새 커밋을 만들지 않고 `idempotent: true`, `committed: false`로 멱등 반환한다.

```json
{"ok": true, "error": null, "command": "finalize", "task": "131",
 "state": "closed", "previous_state": "attribution_pending", "idempotent": false,
 "task_path": "...", "worktree_root": "...", "declared": [...], "observed": [...], "violations": [],
 "committed": true, "done_file_found": true,
 "memory_index_requests_applied": [...], "memory_index_requests_resolved": [...], "capsule_updated": true}
```

## canonical task path 해석

registry meta의 `attribution_state`가 판정에 들어간다.

| 상태 | 해석 |
|------|------|
| active 3상태 (키 부재 · `completed_unmerged` · `attribution_pending`) | 등록된 worktree task path가 canonical. 허브 `tasks/{task_folder}`가 **동시에 실재하면 자동 선택 없이 `TASK_PATH_AMBIGUOUS`로 차단**한다(단일 복사본 불변식) |
| `closed` (merge 확인 후) | 허브에 merge된 사본을 `task_path_source: "hub_merged"`로 반환하고 차단하지 않는다 |

차단은 active에만 적용된다 — 가드가 사라진 것이 아니라 적용 상태가 한정된 것이다. `task_ownership_version`이 없는 메타는 legacy로 보아 판정을 건너뛰고 해석 결과를 출력에 싣지 않는다.

## 오류 코드 (ERROR_CODES SSOT)

`worktree_tool.py`의 `ERROR_CODES` 딕셔너리가 SSOT이며 **32종**이다.

| 코드 | 의미 |
|------|------|
| `CONFIG_NOT_FOUND` | `.opal/worktree.json` 설정 파일을 찾을 수 없음 |
| `CONFIG_INVALID_JSON` | 설정 파일이 유효한 JSON이 아님 |
| `CONFIG_MISSING_KEY` | 필수 키 누락 |
| `CONFIG_INVALID_LAYOUT` | `layout`이 `multi-repo`/`monorepo`가 아님 |
| `CONFIG_INVALID_TYPE` | 설정 값의 타입이 유효하지 않음 |
| `CONFIG_PATH_ESCAPE` | 경로가 프로젝트 루트를 벗어남 |
| `CONFIG_EXISTS` | `init` — 설정 파일이 이미 존재(`--force`로만 덮어쓰기) |
| `CONFIG_UNKNOWN_REPO` | `baseBranchOverrides`의 키가 `repos[]` 또는 `"."`와 불일치 |
| `PROJECT_ROOT_NOT_FOUND` | 지정한 프로젝트 루트가 존재하지 않음 |
| `WORKTREE_EXISTS` | 대상 worktree 경로가 이미 점유됨 |
| `BRANCH_EXISTS` | 브랜치가 다른 worktree에 체크아웃 중 |
| `REPO_NOT_FOUND` | 지정된 `repos` 경로가 존재하지 않음 |
| `NOT_A_GIT_REPO` | 지정된 경로가 git 저장소가 아님 |
| `GIT_COMMAND_FAILED` | git 명령 실패 (create는 여기서 자기 생성물만 롤백) |
| `META_NOT_FOUND` | 메타 파일을 찾을 수 없음 — `--force`로만 우회 |
| `WORKTREE_NOT_FOUND` | 메타는 있으나 실제 worktree 경로가 없음 |
| `WORKTREE_REMOVE_FAILED` | 일부 worktree 회수 실패 — 메타와 슬롯을 보존 |
| `GUARD_DIRTY` | 작업본에 미커밋 변경 사항 존재 |
| `GUARD_UNPUSHED` | 원격에 반영되지 않은 커밋 존재 |
| `GUARD_UNMERGED` | base 브랜치에 아직 병합되지 않음 |
| `LAYOUT_UNDETERMINED` | `init` — 독립 저장소도, manifest를 가진 최상위 디렉토리도 찾지 못함 |
| `TASK_FOLDER_INVALID` | `--task-folder`가 basename이 아님(경로 구분자·`..`·NUL 포함) |
| `TASK_ARTIFACT_REPO_MISSING` | multi-repo에서 캡슐 소유 repo가 결정되지 않음 |
| `TASK_ARTIFACT_REPO_UNSUPPORTED` | `task_artifacts.repo`가 예약값 `"."` 외의 값 |
| `TASK_ARTIFACT_REPO_INVALID` | 캡슐 소유 루트 저장소가 R-1~R-5를 만족하지 않음 |
| `TASK_ARTIFACT_REPO_OVERLAP` | 루트 저장소가 `repos[]` 경로를 추적해 배치가 겹침 |
| `TASK_PATH_AMBIGUOUS` | 등록된 worktree 태스크와 같은 `task_folder`가 허브 `tasks/`에도 존재 |
| `TASK_PATH_MISSING` | 메타에 canonical `task_path`가 없어 `finalize` 대상을 결정할 수 없음 |
| `MEMORY_INDEX_REQUEST_PENDING` | 처리되지 않은 memory index 요청이 남아 있음 |
| `ATTRIBUTION_COMMIT_BLOCKED` | 선언되지 않은 귀속 대상 변경이 남아 `finalize` 진행 불가 |
| `ATTRIBUTION_COMMIT_FAILED` | 귀속 commit 생성 또는 clean 검증 실패 |
| `INTERNAL_ERROR` | 예상하지 못한 오류 — traceback 대신 통제된 JSON으로 대체 |

```json
{"ok": false, "error": "<ERROR_CODE>", "message": "<사람이 읽는 설명>", "...": "상황별 부가 필드"}
```

## 종료 코드

| 코드 | 의미 |
|------|------|
| `0` | `ok: true` |
| `1` | `err_response()` 경유 전건(위 32종) |
| `2` | argparse 인자 오류(서브명령 누락, `--project-root`/`--task` 누락 등) |

`__main__` 진입점이 예상 밖 예외를 잡아 `INTERNAL_ERROR` JSON + exit 1로 바꾸므로 **traceback이 stdout·stderr로 새지 않는다.** exit 2 경로만 argparse 기본 usage 텍스트를 stderr로 내보낸다. `run.sh`의 venv 부재 메시지도 stderr로 나간다.

## 제약

- **`setup` 명령을 실행하지 않는다.** `create`는 `pending_setup[]`으로 열거만 하므로 의존성 설치는 호출자나 사람이 별도로 수행한다.
- **`portOffset`을 적용하지 않는다.** 응답에 힌트로 싣기만 한다.
- `taskCapsuleCone`은 monorepo 분기 전용, `task_artifacts`·`baseBranchOverrides`는 multi-repo 분기 전용이다 — 반대 layout에서는 적용되지 않는다.
- `baseBranchOverrides`는 `resolve_base_ref`의 `declared` 자리에 값을 넣을 뿐 **3단 폴백 순서를 바꾸지 않는다.**
- `remove`는 브랜치를 삭제하지 않는다 — 머지 후 브랜치 정리는 사용자의 몫이다.
- `.gitignore`·캐시 볼륨·code-scan exclude·동시 슬롯 수는 전부 비차단 진단이라 `warnings[]`를 읽지 않으면 문제가 있어도 알 수 없다.
