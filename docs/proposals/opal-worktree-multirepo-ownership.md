# OPAL 워크트리 multi-repo 캡슐 소유권 제안서

> 상태: 제안
> 작성: 알투(PM)
> 작성일: 2026-09-12
> 범위: multi-repo 프로젝트에서 태스크 캡슐을 소유할 저장소 지목과 repo별 base branch 해석
> 선행: [워크트리 태스크 소유권 전환 제안서](./archives/opal-worktree-task-ownership.md) §8 — 본 제안서가 §8을 대체한다
> 규범 목적지: `opal/core/references/harness/worktree.md`

---

## 1. 결론

multi-repo 프로젝트에서 태스크 캡슐을 소유할 저장소는 `repos[]` 안에 없을 수 있다.
캡슐을 추적하는 주체가 **프로젝트 루트 저장소**인 구조가 실사용에 존재하며, 현행 탐지 규칙은
루트를 `repos[]` 후보에서 명시적으로 제외한다. 선행 제안서 §8은 지정 repo가 `repos[]`의
한 원소라고 암묵 전제했으므로 이 구조에 적용되지 않는다.

두 가지를 신설한다.

| 항목 | 신설 내용 | 성격 |
|---|---|---|
| 캡슐 소유 repo 지목 | `task_artifacts.repo`에 예약값 `"."`(프로젝트 루트 저장소) 허용 | §8 확장 |
| repo별 base branch | optional 맵 `baseBranchOverrides` 신설 | §8 미수록 |

`repos[]`의 타입과 의미는 바꾸지 않는다. monorepo 경로는 이 제안서의 영향을 받지 않는다.

---

## 2. 배경 — Phase 4는 투기가 아니라 실수요다

`/Volumes/Data/StoreLinkStudio/pug`는 OPAL 프로젝트(`.opal/AGENT.md`·`brain`·`MEMORY.json` 보유,
태스크 폴더 12개)이면서 `workspace/` 아래 독립 `.git` 6개를 가진 multi-repo다. `.gitmodules`는 없다.

`worktree-tool init --dry-run` 실측 결과(2026-09-12):

| 관측 | 값 |
|---|---|
| `layout` | `multi-repo` |
| `repos` | `workspace/app_android`·`app_ios`·`backend`·`frontend`·`frontend_admin`·`frontend_app` |
| 루트 repo 추적 파일 | `.opal`+`tasks` 164개 |
| 루트 repo의 `workspace` 추적 | 0개 |
| repo별 현재 브랜치 | `main` 4개 / `develop` 2개(`app_ios`·`app_android`) |

이 상태에서 `create`는 `TASK_ARTIFACT_REPO_MISSING`으로 차단된다
(`opal/tools/worktree-tool/worktree_tool.py:701-703`). 즉 pug는 지금 `--worktree`를 쓸 수 없다.
Phase 4는 새 기능을 얹는 일이 아니라 이미 닫아둔 경로를 여는 일이다.

---

## 3. §8이 정한 것과 남긴 공백

### 3.1 §8이 이미 정한 것 — 유지한다

- `task_artifacts` 설정 키(`repo`·`tasks_path`·`opal_path`)의 존재와 형태
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
`main` 4개 / `develop` 2개인 pug는 현행 스키마로 표현 자체가 불가능하다.
선행 제안서는 이 항목을 Phase 4 할 일 목록(`:721`)에 한 줄로 적었을 뿐 설계를 두지 않았다.

### 3.4 공백이 아닌 것 — `copy`·`setup`

`copy[]`와 `setup[]`은 이미 repo 단위로 갈린다. 둘 다 프로젝트 루트 기준 상대경로를 쓰고
(`_copy_local_files`의 `wt_root / rel`, `:413-428`), multi-repo의 worktree 착지점도
`wt_root / rel`이다(`:867-870`). 두 경로가 같은 규칙이라 repo prefix가 그대로 맞물린다.
`init` 실측에서도 `frontend`는 `pnpm install`, `frontend_admin`·`frontend_app`은 `bun install`로
repo마다 다르게 탐지됐다. **이 항목은 본 제안서 범위에서 제외한다.**

---

## 4. 공백 1 해법 — 루트 저장소 지목

### 4.1 설정

```json
{
  "layout": "multi-repo",
  "repos": ["workspace/frontend", "workspace/backend", "..."],
  "task_artifacts": {
    "repo": ".",
    "tasks_path": "tasks",
    "opal_path": ".opal"
  }
}
```

- `task_artifacts.repo`는 `repos[]`의 한 원소이거나, 예약값 `"."`다.
- `"."`는 프로젝트 루트 저장소를 뜻한다. `repos[]`에 `"."`를 추가하지 않는다 —
  `repos`의 "worktree를 만들 코드 저장소 목록"이라는 의미를 보존한다.
- `tasks_path`·`opal_path`는 지정 repo 안의 상대경로다.

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

`repo`가 `repos[]`의 한 원소이면 §8 원문대로 그 repo의 worktree가 `task_home`이고,
slot root는 기존처럼 단순 컨테이너로 남는다.

### 4.3 sparse-checkout을 쓰지 않는다

monorepo 분기는 `taskCapsuleCone`을 sparse-checkout cone에 전개하지만, multi-repo 분기에는
이 키를 적용하지 않는다(태스크 118 결정, `worktree_tool.py:948-949` 주석).
본 제안서는 이 결정을 유지한다 — 루트 repo가 `workspace/`를 추적하지 않으므로
full checkout해도 코드 repo와 겹치지 않는다. cone을 도입하면 118·119가 실측한
"monorepo 전용 스위치" 불변식이 깨진다.

### 4.4 pre-flight 신설 — 추적 범위 겹침 차단

`repo`가 `"."`이고 루트 저장소가 `repos[]`의 어느 경로든 1파일 이상 추적하면
`TASK_ARTIFACT_REPO_OVERLAP`으로 차단한다.

- 판정: 각 `rel ∈ repos`에 대해 `git -C <root> ls-files -- <rel>`이 비어 있어야 한다.
- 근거: 겹치면 루트 worktree의 full checkout과 코드 repo worktree가 같은 경로에 착지해
  어느 쪽이 이기는지 정의되지 않는다. 자동 해소 대신 명시 차단한다.
- 오류 응답에 위반 경로를 동봉한다.

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
- monorepo 분기는 이 키를 소비하지 않는다. 값이 있어도 무시하며 경고하지 않는다.

### 5.2 `repos[]` 객체화 안을 기각하는 근거

`repos`를 `[{"path": ..., "baseBranch": ...}]`로 확장하는 대안이 있으나 채택하지 않는다.

- monorepo의 `repos`는 저장소가 아니라 sparse-checkout **cone 디렉토리 패턴**이다
  (`sparse-checkout set *cfg["repos"]`, `:952`). 여기에 `baseBranch`는 의미를 갖지 않는다.
- `validate_worktree_config`의 `repos` 타입·경로 이탈 검사(`:234-244`)와
  `sparse-checkout set` 소비부가 모두 `list[str]`을 전제한다. 타입을 바꾸면
  monorepo 경로까지 파급되어 118·119가 확보한 "비워크트리·monorepo 바이트 동일"
  회귀 증거를 다시 세워야 한다.
- 별도 맵은 multi-repo 분기에서만 읽히므로 파급이 그 분기에 갇힌다.

### 5.3 `init` 초안 — 추측하지 않는다

`init`은 `baseBranchOverrides`를 채우지 않는다. repo별 현재 HEAD는 작업 중 브랜치일 수 있어
base로 삼을 근거가 되지 못한다. DEC-8의 "추측하지 않는 것" 원칙에 따라 `_copy_candidates`와
같은 형식의 주석 키 `_baseBranch_candidates`로 repo별 관측값만 제시한다.

`baseBranch` 키도 초안에 추가한다 — 현재 초안에 아예 없어 사용자가 키의 존재를 알 수 없다.
값은 루트 저장소의 기본 브랜치 관측값을 넣되 `_help`에 검토 대상임을 명시한다.

---

## 6. merge와 수명주기

- 캡슐은 지정 repo 하나에만 commit·merge된다. 코드 repo의 merge와 독립 판정이다.
- `finalize-attribution`은 지정 repo에서만 수행한다 — 귀속 커밋의 대상 경로
  (`.opal/brain/**`·`.opal/MEMORY.json`)가 그 repo 추적 범위 안에 있기 때문이다.
- `remove`의 3중 가드(dirty→unpushed→unmerged)는 이미 repo별로 순회한다
  (`worktree_tool.py:1184-1202`). 지정 repo를 포함한 **전 repo가 통과할 때만** 회수한다.
  이 동작은 현행 구현 그대로이며 변경하지 않는다.
- 허용 merge 경로는 `--ff-only`와 `--no-ff` 두 가지다(태스크 119 계약 정정). multi-repo에서도
  같다.

---

## 7. 도구·문서 변경 범위

### 7.1 `worktree-tool`

| 지점 | 변경 |
|---|---|
| `validate_worktree_config` | `task_artifacts` 타입·키 검증, `baseBranchOverrides` 타입·키 일치 검증 |
| `cmd_create` pre-flight | `task_artifacts.repo` 해석, `"."` 예약값 처리, `TASK_ARTIFACT_REPO_OVERLAP` 판정 |
| `plan_entries` 구성 | `repo == "."`일 때 slot root를 루트 repo worktree 항목으로 추가 |
| base-ref 해석(`:888-891`) | `overrides.get(rel, cfg["baseBranch"])`로 교체 |
| `cmd_create` 차단(`:701-703`) | `task_artifacts`가 유효하면 `TASK_ARTIFACT_REPO_MISSING`을 발동하지 않음 |
| `_build_init_draft` | `baseBranch` 키와 `_baseBranch_candidates` 주석 키 추가 |
| 오류 카탈로그 | `TASK_ARTIFACT_REPO_OVERLAP`·`CONFIG_UNKNOWN_REPO` 신설 |
| `@header` | 위 계약 반영 |

### 7.2 문서

| 문서 | 변경 |
|---|---|
| `opal/core/references/harness/worktree.md` | §8 계약 이관 + 본 제안서 §4·§5 규범화 |
| `docs/proposals/archives/opal-worktree-task-ownership.md` | 헤더에 "§8은 본 제안서가 대체한다" 포인터 1행. 본문 §8은 기록으로 보존 |
| `.opal/schema/`(존재 시) | 설정 스키마 갱신 |

---

## 8. 수용 기준

- [ ] `task_artifacts.repo: "."`로 pug에서 `create`가 성공하고, slot root가 루트 repo의
      worktree로 등록된다(`git worktree list`로 관측).
- [ ] 발급된 `task_path`가 slot root 아래 `tasks/{task_folder}`이고 불변식
      `task_path == realpath(task_home/tasks/task_folder)`를 만족한다.
- [ ] `app_ios`·`app_android` worktree의 base-ref가 `develop`에서, 나머지 4개가 `main`에서
      해석된다.
- [ ] `baseBranchOverrides`에 `repos[]`에 없는 키를 넣으면 `CONFIG_UNKNOWN_REPO`로 차단된다.
- [ ] 루트 repo가 `repos[]` 경로를 추적하는 fixture에서 `TASK_ARTIFACT_REPO_OVERLAP`으로
      차단되고 worktree가 하나도 생성되지 않는다(all-or-nothing).
- [ ] `task_artifacts` 미설정 multi-repo는 기존대로 `TASK_ARTIFACT_REPO_MISSING`으로 차단된다.
- [ ] monorepo 프로젝트(ai-framework)의 `create`·`list`·`status`·`remove`·`finalize`·`init`
      6명령 출력이 변경 전과 바이트 동일하다 — 태스크 119 `REGRESSION-EVIDENCE.md`의
      fixture 방식을 그대로 쓴다.
- [ ] CLOSE → commit → merge → `finalize-attribution` → `remove` 수명주기를 pug 또는 동형
      fixture에서 완주한다.

---

## 9. 미결 쟁점

| # | 쟁점 | 판단 필요 시점 |
|---|---|---|
| 1 | pug에 `.opal/worktree.json`이 없다. `init` 초안 생성 후 `task_artifacts`·`baseBranchOverrides`를 수기 보정하는 절차를 문서화할지, `init`이 `task_artifacts` 초안까지 제시할지 | 구현 태스크 PLAN |
| 2 | `"."` 외에 `repos[]` 원소를 지정하는 경로는 실사용 검증 대상이 없다. fixture로만 검증할지, 미검증 상태로 두고 `"."`만 활성화할지 | 구현 태스크 TEST-SCENARIO |
| 3 | 코드 repo 일부만 merge된 상태에서 캡슐 repo가 merge 완료된 경우의 `status` 보고 형태 | 구현 태스크 PLAN |

---

## 10. 단계별 도입

1. 본 제안서 검토·확정 → §8을 `harness/worktree.md`로 이관하며 §4·§5를 규범화
2. `worktree-tool` 구현 + monorepo 바이트 동일 회귀 증거
3. pug에서 `init` → 설정 보정 → `create` 실환경 파일럿
4. 수명주기 완주 검증 후 multi-repo local ownership 활성화
