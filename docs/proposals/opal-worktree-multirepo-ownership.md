# OPAL 워크트리 multi-repo 캡슐 소유권 제안서

> 상태: 제안
> 작성: 알투(PM)
> 작성일: 2026-09-12
> 범위: multi-repo 프로젝트에서 태스크 캡슐을 소유할 저장소 지목, repo별 base branch 해석,
> 중첩 worktree의 생성·회수 순서
> 선행: [워크트리 태스크 소유권 전환 제안서](./archives/opal-worktree-task-ownership.md) §8 — 본 제안서가 §8을 대체한다
> 규범 목적지: `opal/core/references/harness/worktree.md`

---

## 1. 결론

multi-repo 프로젝트에서 태스크 캡슐을 소유할 저장소는 `repos[]` 안에 없을 수 있다.
캡슐을 추적하는 주체가 **프로젝트 루트 저장소**인 구조가 실사용에 존재하며, 현행 탐지 규칙은
루트를 `repos[]` 후보에서 명시적으로 제외한다. 선행 제안서 §8은 지정 repo가 `repos[]`의
한 원소라고 암묵 전제했으므로 이 구조에 적용되지 않는다.

네 가지를 신설한다.

| 항목 | 신설 내용 | 성격 |
|---|---|---|
| 캡슐 소유 repo 지목 | `task_artifacts.repo`에 예약값 `"."`(프로젝트 루트 저장소) — **1차는 이 값만 허용**, 루트가 Git 저장소이고 `tasks`·`.opal/AGENT.md`·`.opal/MEMORY.json`을 추적할 때만 | §8 축소 대체 |
| repo별 base branch | optional 맵 `baseBranchOverrides` 신설 | §8 미수록 |
| 중첩 worktree 회수 순서 | 생성 정순 / 회수·롤백 **역순** [MUST], 전건 성공 후에만 메타 삭제 | §8 미수록 |
| 부분 회수 이후 재시도 | 경로 실재 × Git 등록 2축 멱등 판정 — `--force` 없이 재시도 가능 | §8 미수록 |

전 국면이 단일 ordered `plan_entries`를 소비한다(§4.5) — 검사 대상과 생성 대상이 갈라지지
않게 하는 전제다.

`repos[]`의 타입과 의미는 바꾸지 않는다. monorepo 경로는 설정·출력·동작 어느 축에서도
이 제안서의 영향을 받지 않는다.

---

## 2. 배경 — Phase 4는 투기가 아니라 실수요다

`/Volumes/Data/StoreLinkStudio/pug`는 OPAL 프로젝트(`.opal/AGENT.md`·`brain`·`MEMORY.json` 보유,
태스크 폴더 12개)이면서 `workspace/` 아래 독립 `.git` 6개를 가진 multi-repo다. `.gitmodules`는 없다.

`worktree-tool init --dry-run` 실측(2026-09-12):

| 관측 | 값 |
|---|---|
| `layout` | `multi-repo` |
| `repos` | `workspace/app_android`·`app_ios`·`backend`·`frontend`·`frontend_admin`·`frontend_app` |
| 루트 repo 추적 파일 | `.opal`+`tasks` 164개 |
| 루트 repo의 `workspace` 추적 | 0개 |
| base branch | 루트 `main` / `app_ios`·`app_android` `develop` / 나머지 4개 `main` |

**worktree·merge 대상은 루트를 포함해 7개다.** 이 상태에서 `create`는
`TASK_ARTIFACT_REPO_MISSING`으로 차단된다(`opal/tools/worktree-tool/worktree_tool.py:701-703`).
즉 pug는 지금 `--worktree`를 쓸 수 없다. Phase 4는 새 기능을 얹는 일이 아니라 이미 닫아둔
경로를 여는 일이다.

---

## 3. §8이 정한 것과 남긴 공백

### 3.1 §8 계약의 승계 구분

| §8 항목 | 본 제안서 처리 |
|---|---|
| `task_artifacts` 키의 존재 | **승계** — `repo` 하나만 남긴다 |
| `tasks_path`·`opal_path` 키 | **폐기** — 설정으로 노출하지 않고 `tasks`·`.opal`로 고정한다(§4.1) |
| `repo`가 `repos[]`의 한 원소일 수 있다 | **축소** — 1차는 `"."`만 허용한다(§4.1) |

나머지는 그대로 승계한다.

- 지정 repo의 worktree가 `task_home`이고, 캡슐은 그 repo branch에 commit·merge된다
- 설정이 없거나 지정 repo에 `tasks/`가 없으면 local task ownership을 활성화하지 않고
  `task_artifact_repo_missing`으로 중단한다
- 임의로 slot root에 비추적 task folder를 만들어 성공으로 처리하지 않는다
- 여러 repo의 코드 변경은 각각 기존 base-ref/merged guard를 통과해야 한다

### 3.2 공백 1 — 지정 대상이 `repos[]`에 없을 수 있다

`_find_independent_git_dirs()`는 "루트 자신은 후보에서 제외한다"를 명시 규칙으로 갖는다
(`worktree_tool.py:501-502`). 따라서 pug에서 캡슐 164파일을 추적하는 루트 저장소는 `repos[]`에
영원히 나타나지 않는다. §8 예시의 `"repo": "workspace"`는 이 구조에서 가리킬 대상이 없다 —
`workspace`는 저장소가 아니라 컨테이너 디렉토리이고, 루트 repo는 그것을 0파일 추적한다.

### 3.3 공백 2 — base branch 입력이 단일 값이다

base-ref는 repo마다 해석되지만 입력은 설정 하나다.

```python
base_refs = {
    str(git_root): resolve_base_ref(git_root, cfg.get("baseBranch"))
    for git_root in git_roots
}
```
(`worktree_tool.py:888-891`)

`init` 초안 생성기 `_build_init_draft()`에는 `baseBranch` 키 자체가 없다(`:587-603`).
루트 포함 7개 repo가 `main`/`develop`으로 갈리는 pug는 현행 스키마로 표현 자체가 불가능하다.
선행 제안서는 이 항목을 Phase 4 할 일 목록(`:721`)에 한 줄로 적었을 뿐 설계를 두지 않았다.

### 3.4 공백 3 — 중첩 worktree의 회수 순서가 정의되지 않았다

§4.2가 도입하는 "slot root = 루트 repo worktree" 구조에서는 자식 6개가 루트 worktree
**디렉토리 안**에 있다. 루트를 먼저 회수할 수 없다. 현행 `cmd_remove`는 이 순서 요구를
만족하지 않는다.

- `entries`를 생성 순서 그대로 순회한다(`worktree_tool.py:1204-1214`).
- `_run_git`은 `CompletedProcess`를 돌려주지만(`:117-123`) 호출부가 반환값을 버려
  `git worktree remove` 실패가 관측되지 않는다(`:1213`).
- 이어서 `_delete_meta`(`:1216`)와 `shutil.rmtree(wt_root, ignore_errors=True)`(`:1228`)를
  조건 없이 실행한다. 자식이 남은 채 메타만 사라지면 그 태스크는 도구로 복구할 수 없다.
- `_rollback`도 `created` 정순으로 돈다(`:839-845`).

### 3.5 공백이 아닌 것 — `copy`·`setup`

`copy[]`와 `setup[]`은 이미 repo 단위로 갈린다. 둘 다 프로젝트 루트 기준 상대경로를 쓰고
(`_copy_local_files`의 `wt_root / rel`, `:413-428`), multi-repo의 worktree 착지점도
`wt_root / rel`이다(`:867-870`). 두 경로가 같은 규칙이라 repo prefix가 그대로 맞물린다.
`init` 실측에서도 `frontend`는 `pnpm install`, `frontend_admin`·`frontend_app`은 `bun install`로
repo마다 다르게 탐지됐다. **이 항목은 본 제안서 범위에서 제외한다.**

---

## 4. 공백 1 해법 — 루트 저장소 지목

### 4.1 설정과 1차 도입 범위

```json
{
  "layout": "multi-repo",
  "repos": ["workspace/frontend", "workspace/backend", "..."],
  "task_artifacts": {
    "repo": "."
  }
}
```

**[MUST] 1차 도입은 `task_artifacts.repo: "."`만 허용한다.** `tasks_path`·`opal_path`는
설정 키로 노출하지 않고 `tasks`·`.opal`로 고정한다.

근거 — canonical path 계약이 두 곳에서 경로를 고정하고 있다.

- `_resolve_canonical_task_path()`의 허브 후보가 `project_root / "tasks" / task_folder`로
  하드코딩돼 있다(`worktree_tool.py:1057`). 캡슐 소유 repo가 자식 repo이면 merge 후 허브 사본은
  `project_root/<repo>/tasks/...`에 생기는데 resolver는 그 경로를 보지 않는다. `closed` 이후에도
  이미 회수된 worktree 경로를 반환한다.
- `harness/worktree.md` §canonical path 발급 계약의 불변식이
  `task_path == realpath(task_home/tasks/task_folder)`로 `tasks` 세그먼트를 고정한다(`:57`).
  가변 `tasks_path`는 이 불변식과 양립하지 않는다.

따라서 `repos[]` 원소 지정과 가변 경로는 resolver·불변식 확장이 선행되어야 하며 본 제안서
범위에서 제외한다. 설정에 `"."` 외 값이 오면 `TASK_ARTIFACT_REPO_UNSUPPORTED`로 차단하고,
확장 조건을 오류 메시지에 명시한다 — 조용히 동작해 잘못된 경로를 반환하는 것보다 낫다.

`repos[]`에 `"."`를 추가하지 않는다. `repos`의 "worktree를 만들 코드 저장소 목록"이라는
의미를 보존한다.

**[MUST] `"."`의 전제 조건 — multi-repo라고 루트가 항상 Git 저장소인 것은 아니다.**
현행 `init`은 하위 독립 repo가 1개 이상이면 루트 `.git` 유무를 보지 않고 multi-repo로
판정한다(`worktree_tool.py:613-617`). 따라서 다음 4개 조건을 `create` pre-flight에서 검사하고,
하나라도 불만족이면 `TASK_ARTIFACT_REPO_INVALID`로 차단한다.

| # | 조건 | 판정 |
|---|---|---|
| R-1 | 루트에 `.git`이 존재하고 유효한 Git 저장소다 | `git -C <root> rev-parse --git-dir` 성공 |
| R-2 | 루트가 `tasks/`를 추적한다 | `git -C <root> ls-files -- tasks` 비어 있지 않음 |
| R-3 | 루트가 `.opal/AGENT.md`를 추적한다 | `git -C <root> ls-files -- .opal/AGENT.md` 비어 있지 않음 |
| R-4 | 루트가 `.opal/MEMORY.json`을 추적한다 | `git -C <root> ls-files -- .opal/MEMORY.json` 비어 있지 않음 |

**[MUST] R-2~R-4는 각각 판정한다.** 합산 결과 1건으로 통과시키면 `tasks/`만 추적하고
`.opal/`은 ignore하는 프로젝트가 통과해 merge 시 귀속 대상(`.opal/brain/**`·
`.opal/MEMORY.json`)이 브랜치에 담기지 않는다. 오류 응답에 불만족 조건 번호를 동봉한다.

컨테이너 디렉토리만 있고 루트가 저장소가 아닌 multi-repo는 `"."` 모델의 대상이 아니다 —
이 경우 기존 `TASK_ARTIFACT_REPO_MISSING` 차단이 유지된다.

### 4.2 slot root 배치

`repo`가 `"."`이면 **slot root 자체가 루트 저장소의 worktree**다.

```text
.opal-worktrees/task_119/           ← 루트 repo worktree (= task_home)
├── tasks/119-.../                  ← 태스크 캡슐
├── .opal/                          ← 프로젝트 자산
└── workspace/
    ├── frontend/                   ← workspace/frontend repo worktree
    └── backend/                    ← workspace/backend repo worktree
```

허브의 디렉토리 구조와 동형이므로 워커가 보는 상대경로가 허브와 같다.
루트 repo가 `workspace/`를 추적하지 않는다는 전제 위에서만 성립한다 — §4.4가 이를 집행한다.

### 4.3 sparse-checkout을 쓰지 않는다

monorepo 분기는 `taskCapsuleCone`을 sparse-checkout cone에 전개하지만, multi-repo 분기에는
이 키를 적용하지 않는다(태스크 118 결정, `worktree_tool.py:948-949` 주석).
본 제안서는 이 결정을 유지한다 — 루트 repo가 `workspace/`를 추적하지 않으므로
full checkout해도 코드 repo와 겹치지 않는다. cone을 도입하면 118·119가 실측한
"monorepo 전용 스위치" 불변식이 깨진다.

### 4.4 pre-flight 신설 — 추적 범위 겹침 차단

루트 저장소가 `repos[]`의 어느 경로든 1파일 이상 추적하면 `TASK_ARTIFACT_REPO_OVERLAP`으로
차단한다.

- 판정: 각 `rel ∈ repos`에 대해 `git -C <root> ls-files -- <rel>`이 비어 있어야 한다.
- 근거: 겹치면 루트 worktree의 full checkout과 코드 repo worktree가 같은 경로에 착지해
  어느 쪽이 이기는지 정의되지 않는다. 자동 해소 대신 명시 차단한다.
- 오류 응답에 위반 경로를 동봉한다.
- 판정 시점은 worktree 생성 **전**이다 — 위반 시 아무것도 만들지 않는다(DEC-2 all-or-nothing).

### 4.5 ordered `plan_entries` 단일 소비 [MUST]

**루트를 포함한 전 entry 목록은 `plan_entries` 하나가 소유하고, 모든 국면이 이것만 소비한다.**

| 국면 | 현행 | 변경 |
|---|---|---|
| pre-flight | `plan_entries` 순회(`:867-880`) | 유지 — 루트 항목이 맨 앞에 들어간다 |
| base-ref 해석 | `plan_entries`에서 파생한 `git_roots`(`:888-891`) | 유지 |
| **worktree 생성** | **`cfg["repos"]`를 다시 순회**(`:907-908`) | **`plan_entries` 순회로 교체** |
| metadata `entries` | 생성 결과(`created`) | 유지 — `plan_entries` 순서를 보존 |
| rollback·remove | `created`·`entries` | 역순 순회(§6.1) |

근거: 생성부만 `cfg["repos"]`를 독립적으로 다시 도는 현행 구조에서는 루트가
pre-flight·base-ref의 검사 대상이면서 실제로는 생성되지 않는다. 두 목록이 갈라지는 순간
`TASK_ARTIFACT_REPO_OVERLAP`을 통과한 검사 결과가 생성 결과를 보장하지 못한다.
목록은 하나여야 하고 순서는 그 목록이 소유한다.

---

## 5. 공백 2 해법 — repo별 base branch

### 5.1 설정

```json
{
  "baseBranch": "main",
  "baseBranchOverrides": {
    "workspace/app_ios": "develop",
    "workspace/app_android": "develop"
  }
}
```

- optional `dict[str, str]`. 기본값 `{}`.
- 키는 `repos[]`의 원소 또는 `"."`와 정확히 일치해야 한다. 불일치 키는
  `CONFIG_UNKNOWN_REPO`로 차단한다 — 오타가 조용히 전역값으로 폴백하면 잘못된 base에서
  브랜치가 갈라진다.
- 해석: `resolve_base_ref(git_root, overrides.get(rel, cfg.get("baseBranch")))`.
  루트 repo의 키는 `"."`다.
- **우선순위는 신설하지 않는다** — `declared`가 없을 때의 3단 폴백
  (`origin/HEAD` symbolic-ref → 현재 HEAD)은 `resolve_base_ref`가 이미 봉인하고 있다
  (`worktree_tool.py:310-318`). override는 `declared` 자리에 값을 넣을 뿐이며
  그 아래 순서를 바꾸지 않는다.
- monorepo 분기는 이 키를 소비하지 않는다. 값이 있어도 무시하며 경고하지 않는다.
  검증(`CONFIG_UNKNOWN_REPO`)도 multi-repo 분기에서만 수행한다.

### 5.2 `repos[]` 객체화 안을 기각하는 근거

`repos`를 `[{"path": ..., "baseBranch": ...}]`로 확장하는 대안이 있으나 채택하지 않는다.

- monorepo의 `repos`는 저장소가 아니라 sparse-checkout **cone 디렉토리 패턴**이다
  (`sparse-checkout set *cfg["repos"]`, `:952`). 여기에 `baseBranch`는 의미를 갖지 않는다.
- `validate_worktree_config`의 `repos` 타입·경로 이탈 검사(`:234-244`)와
  `sparse-checkout set` 소비부가 모두 `list[str]`을 전제한다. 타입을 바꾸면
  monorepo 경로까지 파급되어 118·119가 확보한 "비워크트리·monorepo 바이트 동일"
  회귀 증거를 다시 세워야 한다.
- 별도 맵은 multi-repo 분기에서만 읽히므로 파급이 그 분기에 갇힌다.

### 5.3 `init` 초안 — multi-repo 분기에서만 키를 늘린다

**[MUST] `_build_init_draft()`의 키 집합 변경은 multi-repo 분기에 한정한다.** monorepo 초안은
현행 키 집합과 순서를 그대로 유지한다 — §8.5의 `init` 출력 바이트 동일 요구와 충돌하지 않게
하기 위함이다.

multi-repo 초안에만 다음을 추가한다.

- `baseBranch` — **§4.1의 R-1을 만족할 때만 추가한다.** 값은
  `resolve_base_ref(project_root, None)`의 관측값을 그대로 쓰고(`:310-318`) 별도 탐지 로직을
  만들지 않는다. 루트가 Git 저장소가 아니면 이 호출의 두 폴백이 모두 실패해 빈 문자열이
  나올 수 있으므로, **키를 생략한다** — 생략하면 각 자식 repo가 자기 `origin/HEAD` → 자기
  `HEAD` 폴백을 쓴다. 현재 초안에 키 자체가 없어 사용자가 존재를 알 수 없다.
- `_baseBranch_candidates` — repo별 현재 HEAD 관측값만 제시하는 주석 키. 값을 채우지 않는
  이유는 현재 HEAD가 작업 중 브랜치일 수 있어 base로 삼을 근거가 못 되기 때문이다
  (DEC-8 "추측하지 않는 것").
- `task_artifacts` — `{"repo": "."}` 초안. **§4.1의 R-1~R-4를 모두 만족할 때만 제시한다.**
  불만족이면 이 키를 초안에 넣지 않고 `_help`에 "이 프로젝트는 캡슐 소유 repo를 결정할 수
  없어 local task ownership을 쓸 수 없다"고 적는다 — 쓸 수 없는 설정을 초안으로 제시하지
  않는다.

정리하면 초안의 키 추가 조건은 두 단이다 — `baseBranch`·`_baseBranch_candidates`는 R-1,
`task_artifacts`는 R-1~R-4 전건이다.

`baseBranchOverrides`는 초안에 넣지 않는다 — 추측 금지 원칙의 직접 적용이다.

---

## 6. 수명주기 — 중첩 worktree의 생성·회수 순서

### 6.1 순서 계약

| 국면 | 순서 | 근거 |
|---|---|---|
| 생성 | 루트 → 자식 | 자식 worktree의 부모 디렉토리가 루트 worktree 안에 있어야 한다 |
| 롤백 | 자식 → 루트 | 자식이 남아 있으면 루트를 제거할 수 없다 |
| 회수(`remove`) | 자식 → 루트 | 위와 같다 |

**[MUST] 회수·롤백은 생성의 역순이다.** 현행 정순 순회(`:1204-1214`, `:839-845`)를 역순으로
바꾼다.

### 6.2 실패 관측과 메타 보존

**[MUST] 전 entry의 `git worktree remove`가 성공한 뒤에만 메타와 slot root를 삭제한다.**

- 각 호출의 `returncode`를 확인한다. 현행은 `_run_git`의 반환값을 버린다(`:1213`).
- 하나라도 실패하면 `WORKTREE_REMOVE_FAILED`(실패 repo·stderr 동봉)로 반환하고
  `_delete_meta`(`:1216`)·`shutil.rmtree`(`:1228`)를 **실행하지 않는다**.
- 메타가 남아 있어야 재시도와 수동 복구가 가능하다. 현행은 실패해도 메타를 지워
  복구 경로가 사라진다.
- `--force`는 가드 우회에만 적용되고 이 실패 판정을 우회하지 않는다.

### 6.3 부분 회수 이후의 멱등 재시도 [MUST]

§6.2가 메타를 보존하므로 재호출이 가능해야 한다. 그런데 현행 `remove`는 경로가 없으면
`--force` 없이는 `WORKTREE_NOT_FOUND`로 즉시 중단한다(`worktree_tool.py:1189-1193`).
자식 3개를 회수한 뒤 4번째에서 실패하면, 재호출은 이미 회수된 1번째에서 다시 막힌다.
`--force`로만 진행할 수 있는데 그건 가드 우회를 함께 켜는 것이라 안전한 재시도가 아니다.

entry별로 **경로 실재**와 **Git 등록** 두 축을 따로 보고 판정한다.

| 경로 | Git 등록 | 판정 | 동작 |
|---|---|---|---|
| 없음 | 없음 | 이미 회수됨 | skip — 오류 아님 |
| 없음 | 있음 | 등록 고아 | `WORKTREE_REMOVE_FAILED`로 차단·보존 |
| 있음 | 없음 | 미등록 잔여 디렉토리 | `WORKTREE_REMOVE_FAILED`로 차단·보존 |
| 있음 | 있음 | 정상 | 가드 판정 후 회수 |

**[MUST] 불일치 2종을 도구가 자동 복구하지 않는다.**

- `git worktree prune`을 호출하지 않는다 — prune의 대상은 해당 repo의 **모든** stale 관리정보라
  현재 태스크보다 범위가 넓다. 다른 태스크의 슬롯 정보를 함께 지울 수 있다.
- 미등록 잔여 디렉토리를 가드 없이 삭제하지 않는다 — Git이 모르는 디렉토리의 내용은
  사용자 파일일 수 있다.
- 두 경우 모두 실패 repo·경로·관측된 불일치 종류를 payload에 담아 반환하고, 메타와 slot을
  보존한다. 해소는 사용자의 명시 조치(직접 `prune`, 디렉토리 확인 후 삭제)에 맡긴다.

부분 회수 재시도는 **"경로 없음 + 등록 없음 → skip"** 한 줄만으로 성립한다. 나머지 두 칸은
재시도를 위한 것이 아니라 불일치를 보고하기 위한 것이다.

- 등록 여부는 기존 `_dest_registered()`(create pre-flight가 쓰는 `git worktree list --porcelain`
  판정, DEC-7)를 그대로 재사용한다. 새 판정 기준을 만들지 않는다.
- `WORKTREE_NOT_FOUND`("메타는 있으나 실제 worktree 경로가 존재하지 않습니다")는 이 경로에서
  발동하지 않는다. 메타 자체의 부재는 `META_NOT_FOUND`가 이미 소유하며 그 계약은 바뀌지 않는다.
- 이 판정은 `--force` 없이 동작한다. 재시도가 가드 우회를 요구해서는 안 된다.

**롤백 실패도 같은 계약을 따른다.** `_rollback`이 자기 생성물을 역순 회수하다 실패하면
`shutil.rmtree(wt_root, ignore_errors=True)`(`:845`)로 흔적을 지우지 않고, 잔존 entry 목록을
오류 payload에 담아 반환한다. 메타를 이미 기록했다면 보존하고, 기록 전이면 잔존 경로·repo·
branch를 payload에 실어 수동 복구 대상을 명시한다.

### 6.4 merge와 귀속

허용 merge 경로는 `--ff-only`와 `--no-ff` 두 가지다(태스크 119 계약 정정). multi-repo도 같다.
현행 수명주기 순서를 그대로 따른다(`opal/skills/opal-pilot-dev/SKILL.md:299-315`).

1. CLOSE 안에서 `worktree-tool finalize` — **merge 전**
2. finalize가 만든 캡슐 변경을 태스크 브랜치에 커밋
3. 허브에서 `git merge --ff-only` 또는 `--no-ff`
4. `state-tool finalize-attribution <task-path> --allocator-root <허브>`
5. `state-tool status <task-path> --set done`
6. `worktree-tool remove`

multi-repo 추가 조건:

- 캡슐은 지정 repo(루트) 하나에만 commit·merge된다. 코드 repo의 merge와 독립 판정이다.
- `finalize`와 `finalize-attribution`은 루트 repo에서만 수행한다 — 귀속 커밋 대상
  (`.opal/brain/**`·`.opal/MEMORY.json`)이 루트 추적 범위 안에 있다.
- `remove`의 3중 가드(dirty→unpushed→unmerged)는 repo별로 순회한다
  (`worktree_tool.py:1184-1202`). **루트를 포함한 7개 전부가 통과할 때만** 회수한다.
  즉 코드 repo 하나라도 미머지면 캡슐이 merge됐어도 회수되지 않는다.

---

## 7. 도구·문서 변경 범위

### 7.1 `worktree-tool`

| 지점 | 변경 |
|---|---|
| `validate_worktree_config` | `task_artifacts` 타입·키 검증(`"."` 외 거부), `baseBranchOverrides` 타입·키 일치 검증 — **둘 다 multi-repo 분기 전용** |
| `cmd_create` pre-flight | `task_artifacts` 해석, §4.1 R-1~R-4, `TASK_ARTIFACT_REPO_OVERLAP` 판정 |
| `plan_entries` 구성(`:867-870`) | 루트 repo 항목을 **맨 앞**에 추가(생성 정순) |
| **worktree 생성 루프(`:907-908`)** | **`cfg["repos"]` 재순회를 `plan_entries` 순회로 교체**(§4.5) |
| base-ref 해석(`:888-891`) | `overrides.get(rel, cfg["baseBranch"])`로 교체. `resolve_base_ref`의 3단 폴백은 불변 |
| `_rollback`(`:839-845`) | `created` 역순 순회, 실패 시 `rmtree` 생략 + 잔존 payload 반환 |
| `cmd_remove`(`:1189-1228`) | `entries` 역순 순회, §6.3 2축 멱등 판정, `returncode` 확인, 전건 성공 시에만 메타·slot 삭제 |
| `cmd_create` 차단(`:701-703`) | `task_artifacts`가 유효하면 `TASK_ARTIFACT_REPO_MISSING`을 발동하지 않음 |
| `_build_init_draft`(`:587-603`) | **multi-repo 분기에만** `baseBranch`·`_baseBranch_candidates`·`task_artifacts` 추가 |
| 오류 카탈로그 | `TASK_ARTIFACT_REPO_OVERLAP`·`TASK_ARTIFACT_REPO_UNSUPPORTED`·`TASK_ARTIFACT_REPO_INVALID`·`CONFIG_UNKNOWN_REPO`·`WORKTREE_REMOVE_FAILED` 신설 |
| `@header` | 위 계약 반영 |

### 7.2 문서

| 문서 | 변경 |
|---|---|
| `opal/core/references/harness/worktree.md` | §8 계약 이관 + 본 제안서 §4·§5·§6 규범화 |
| `docs/proposals/archives/opal-worktree-task-ownership.md` | 헤더에 "§8은 본 제안서가 대체한다" 포인터 1행. 본문 §8은 기록으로 보존 |

---

## 8. 수용 기준

### 8.1 설정·생성

- [ ] `task_artifacts.repo: "."`로 pug에서 `create`가 성공하고, **루트 포함 7개** worktree가
      등록된다(`git worktree list`로 repo별 관측).
- [ ] slot root가 루트 repo의 worktree이고 자식 6개가 그 아래 `workspace/*`에 착지한다.
- [ ] 발급된 `task_path`가 slot root 아래 `tasks/{task_folder}`이고 불변식
      `task_path == realpath(task_home/tasks/task_folder)`를 만족한다.
- [ ] `task_artifacts.repo`에 `"."` 외 값을 넣으면 `TASK_ARTIFACT_REPO_UNSUPPORTED`로 차단된다.
- [ ] `task_artifacts` 미설정 multi-repo는 기존대로 `TASK_ARTIFACT_REPO_MISSING`으로 차단된다.
- [ ] 루트 repo가 `repos[]` 경로를 추적하는 fixture에서 `TASK_ARTIFACT_REPO_OVERLAP`으로
      차단되고 worktree가 하나도 생성되지 않는다.
- [ ] R-1~R-4 각각을 단독으로 위반하는 fixture 4종에서 `TASK_ARTIFACT_REPO_INVALID`로
      차단되고, 오류 payload에 위반 조건 번호가 실린다.
- [ ] 같은 4종 fixture에서 `init` 초안에 `task_artifacts` 키가 **나타나지 않는다**.
      R-1 위반 fixture에서는 `baseBranch`·`_baseBranch_candidates`도 나타나지 않는다.
- [ ] R-1 위반 fixture에서 각 자식 repo의 base-ref가 자기 `origin/HEAD`(없으면 자기 `HEAD`)로
      해석되고 빈 문자열이 나오지 않는다.
- [ ] pre-flight를 통과한 entry 집합과 실제 생성된 worktree 집합이 일치한다 —
      루트를 포함한 `plan_entries` 전건이 `git worktree list`에 등록된다(§4.5).

### 8.2 base branch

- [ ] 루트와 4개 repo의 base-ref가 `main`에서, `app_ios`·`app_android`가 `develop`에서
      해석된다 — 7개 전부를 `.meta/task_{NNN}.json`의 동결값으로 관측한다.
- [ ] `baseBranchOverrides`에 `repos[]`·`"."` 어느 쪽과도 일치하지 않는 키를 넣으면
      `CONFIG_UNKNOWN_REPO`로 차단된다.

### 8.3 회수 순서

- [ ] `remove`가 자식 6개를 먼저 회수한 뒤 루트를 회수한다(git 호출 순서로 관측).
- [ ] 자식 worktree 하나를 제거 불가 상태로 만든 fixture에서 `WORKTREE_REMOVE_FAILED`가
      반환되고, `.meta/task_{NNN}.json`과 slot root가 **보존**된다.
- [ ] create 중간 실패 fixture에서 롤백이 자식 → 루트 역순으로 수행되고 잔여물이 0건이다.

### 8.3.1 멱등 재시도(§6.3)

- [ ] 자식 3개를 회수한 뒤 4번째에서 실패한 상태에서 `remove`를 **`--force` 없이** 재호출하면,
      이미 회수된 3개는 skip되고 남은 entry부터 진행된다.
- [ ] 경로·등록이 모두 없는 entry는 오류 없이 skip된다.
- [ ] 경로는 없고 Git 등록만 남은 entry는 `WORKTREE_REMOVE_FAILED`로 차단되고, 메타·slot이
      보존되며, 도구가 `git worktree prune`을 호출하지 **않는다**(호출 로그로 관측).
- [ ] 경로만 있고 등록이 없는 entry는 `WORKTREE_REMOVE_FAILED`로 차단되고 해당 디렉토리가
      **삭제되지 않는다**.
- [ ] 롤백 실패 fixture에서 `wt_root`가 삭제되지 않고, 잔존 entry(경로·repo·branch)가
      오류 payload에 포함된다.

### 8.4 수명주기 완주

- [ ] CLOSE → `worktree-tool finalize`(merge 전) → 캡슐 커밋 → `git merge --ff-only` →
      `state-tool finalize-attribution` → `status --set done` → `worktree-tool remove`를
      pug 또는 동형 fixture에서 완주한다.
- [ ] 같은 순서를 `--no-ff` 경로로도 완주한다.
- [ ] 코드 repo 하나가 미머지인 상태에서 `remove`가 `GUARD_UNMERGED`로 거부된다.
- [ ] merge 후 `status`가 `task_path_source: hub_merged`를 보고한다.

### 8.5 회귀

- [ ] monorepo 프로젝트(ai-framework)의 `create`·`list`·`status`·`remove`·`finalize`·`init`
      6명령 출력이 변경 전과 바이트 동일하다 — 태스크 119 `REGRESSION-EVIDENCE.md`의
      fixture 방식을 그대로 쓴다. `init` 초안의 키 집합·순서도 포함한다.
- [ ] 비워크트리 실행이 변경 전과 바이트 동일하다.

---

## 9. pug 파일럿 사전 조건

실측상 pug는 `"."` 모델과 overlap pre-flight에 정확히 맞지만, 파일럿 전에 처리할 상태가 있다.

| 항목 | 실측 | 처리 |
|---|---|---|
| `.opal/worktree.json` | 없음 | `init`으로 초안 생성 → `task_artifacts`·`baseBranchOverrides` 수기 보정 → **루트 repo에 커밋**. 캡슐 소유 repo가 루트이므로 설정 파일도 루트가 추적한다 |
| 루트 `.gitignore`의 `.opal-worktrees/` | **없음** | **수동 선등재 후 설정과 같은 커밋에 포함**. `ensure_gitignore_entry`는 `create` 실행 중에 등재하므로(pre-flight 통과 뒤 부수 효과 단계) 설정 커밋 시점에는 아직 없다. 선등재하지 않으면 첫 `create`가 루트를 dirty하게 만든다 |
| `workspace/frontend_admin` | `bun.lockb` 수정됨 | 파일럿 전 커밋 또는 stash. worktree는 base-ref에서 새로 체크아웃되므로 이 변경은 전달되지 않고 허브에 남는다 |
| `workspace/backend` | `.DS_Store` 미추적 | `.gitignore` 등재 또는 삭제. 미처리해도 `create`는 막히지 않지만, `remove`의 dirty 가드 판정 대상이 worktree이지 허브가 아니라는 점과 혼동을 남긴다 |
| 나머지 4 repo + 루트 | clean | 처리 불요 |

`ensure_gitignore_entry`는 이미 있으면 파일에 write하지 않으므로(`worktree_tool.py:339-342`)
선등재해 두면 `create`가 `.gitignore`를 건드리지 않는다.

---

## 10. 확정과 후속 후보

미결 쟁점은 없다. 직전 검토에서 열려 있던 두 항목을 아래로 확정한다.

**확정 — 부분 merge 상태 보고는 현행으로 충분하다.** `cmd_status`가 이미 entry별
`merged` 값을 보고한다(`worktree_tool.py:1078-1110`). 코드 repo 일부만 merge된 상태는
`entries[]`의 `merged` 값 나열로 그대로 드러나므로 별도 설계가 필요 없다. 이 절의 §6.4
회수 조건("루트 포함 7개 전부 통과")과도 같은 데이터를 쓴다.

**후속 제안 후보 — `repos[]` 원소를 캡슐 repo로 지정하는 경로.** 본 제안서에서 1차 범위
제외로 이미 결정됐으므로 미결이 아니다. 착수하려면 resolver의 허브 후보 경로 고정(`:1057`)과
`worktree.md:57` 불변식의 `tasks` 세그먼트 고정을 함께 풀어야 하며, 그 범위는 본 제안서와
분리된 별도 제안서가 소유한다.

---

## 11. 단계별 도입

1. 본 제안서 확정 → §8을 `harness/worktree.md`로 이관하며 §4·§5·§6을 규범화
2. `worktree-tool` 구현 + monorepo·비워크트리 바이트 동일 회귀 증거
3. 중첩 remove 순서·실패 보존·멱등 재시도를 Git fixture로 검증(§8.3·§8.3.1)
4. pug 사전 조건 처리(§9) → `create` 실환경 파일럿
5. 수명주기 완주 검증(§8.4) 후 multi-repo local ownership 활성화
