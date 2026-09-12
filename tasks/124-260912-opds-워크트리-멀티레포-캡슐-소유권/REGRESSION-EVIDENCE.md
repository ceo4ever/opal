# REGRESSION-EVIDENCE — OP-TASK-124 monorepo 6명령·비워크트리 바이트 동일 회귀 증거

> W-7 (실행 그룹 P6) 산출물. 완료 기준 연결: AC-12, AC-13, C-2, C-3, C-8 / 담당 시나리오 S-18, S-19.
> 측정 일시: 2026-09-12 19:24 KST. 측정자: EXECUTE 워커(opal-task-agent).
> **이 문서는 측정·판정만 기록한다. W-7은 소스 코드를 한 줄도 수정하지 않았고 실 `~/.opal/`에 배포하지 않았다.**
> 설계는 태스크 119 `REGRESSION-EVIDENCE.md` §0.1 "데이터 루트 고정 · 도구 코드만 스왑"을 그대로 재사용했다(PLAN D-20). 새 검증 방법을 발명하지 않았다.

---

## 0. 측정 대상과 좌표

| 항목 | 값 |
|---|---|
| 허브 | `/Volumes/Data/AIStudio/workspace/ai-framework` |
| 코드 루트(워크트리) | `/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_124` |
| 변경 전 기준(base) | `HEAD` = `4d23cb0` — 124 구현 직전 커밋. 변경 4파일을 `git show HEAD:<경로>`로 추출 |
| 변경 후 기준(after) | 워크트리 작업본(미커밋) — `worktree_tool.py`·`test_worktree_tool.py`·`harness/worktree.md`·제안서 |
| base 소스 트리 | `<W>/src_base` (측정 후 삭제) |
| after 소스 트리 | `<W>/src_after` (측정 후 삭제) |
| 고정 배포 경로 | `<W>/home_swap/.opal` — 격리 `HOME`. base·after **같은 절대경로**에 순차 install |
| 고정 데이터 루트 ①(R0 monorepo) | `<W>/fix_mono` — 6명령용 |
| 고정 데이터 루트 ②(R0 monorepo, 실패 표면) | `<W>/fix_mono_x` — 추가 측정용 |
| 고정 데이터 루트 ③(R0 비워크트리) | `<W>/fix_plain` |
| 작업 루트 `<W>` | `/private/tmp/claude-501/-Volumes-Data-AIStudio-workspace-ai-framework/05aa1095-7700-4bb5-bb4f-a12ab53a7b39/scratchpad/op124w7` (측정 후 삭제, §6) |

### 0.1 실험 설계 — 데이터 고정 · 코드만 스왑 (119 §0.1 재사용)

124도 도구가 **읽는 데이터**가 아니라 **도구 코드**를 바꿨는지가 쟁점이다(C-2·C-3의 문언: "변경 전과 바이트 동일").
"base 트리에서 실행 ↔ 작업본에서 실행" 대조는 코드 차이와 실행 경로·데이터 차이가 동시에 개입하므로 판정력이 없다.
그래서 119와 동일하게:

- **데이터 루트 고정** — fixture를 **불변 pristine 스냅샷**으로 1회 구성하고, 두 실행이 **같은 절대경로**에서 **같은 바이트**의 입력을 보게 한다.
- **도구 코드만 스왑** — 단일 고정 배포 경로 `<W>/home_swap/.opal`에 ① base 소스 install → 캡처 → ② **같은 경로**에 after 소스 install → 재캡처 → `cmp`.
  배포 루트 절대경로가 양쪽 동일하므로 **정규화 0회**, `cmp`로 바이트 동일을 직접 판정한다.

캡처는 명령마다 **stdout / stderr / exit code를 개별 파일로** 남긴다. 14명령 × 3채널 = **42쌍**을 `cmp`했다.

### 0.2 [MUST] 119와 달라진 점 4가지 — 숨기지 않고 명시한다

| # | 119와의 차이 | 이유 | 대조 편향 여부 |
|---|---|---|---|
| ① | fixture를 두 실행 사이에 "건드리지 않는" 대신 **매 실행 직전 불변 pristine 스냅샷에서 복원**한다 | 119의 6명령은 전부 read-only였지만 124의 6명령에는 `create`·`finalize`·`remove`가 있어 실행 자체가 데이터를 변형한다. 변형된 상태를 두 번째 실행에 물려주면 "같은 입력" 전제가 깨진다 | **없음**. 복원 직후 fixture 파일 트리의 sha256 지문을 매 실행마다 기록했고 base·after가 동일함을 §1.4에서 실증한다 |
| ② | 소스 트리 복사에서 `dashboard/`를 제외했다 | `install_opal()`이 `install_dashboard()` + `console_autostart()`를 태워 실 머신 포트 `7823`의 Console 데몬을 중지·재기동한다(119가 겪은 부작용). `dashboard/` 소스가 없으면 `install_dashboard`가 graceful skip하고 `console_autostart`도 전제 미충족으로 반환한다 | **없음**. base·after **양쪽 동일하게** 제외했고, `dashboard/`는 `worktree-tool`·`state-tool`·`event-loader`·`code-scan`·`memory-tool` 어디에도 실리지 않는다. 실측: 두 install 로그 모두 `dashboard-server/dashboard/backend 없음 — 서버 기동 스킵`, `<W>/home_swap/.opal/dashboard-server` 미생성 |
| ③ | 격리 `HOME`의 `.opal/.venv`를 미리 만들어 실 venv의 `site-packages`를 복사해 두었다 | `install_opal_venv()`가 `pandas`·`playwright` 등 전체 의존성을 네트워크에서 내려받는 것을 피하기 위함. **복사 방향은 실 venv → 격리 venv 단방향**이며 실 venv에 쓰지 않았다(실 venv의 `pip` 셰방을 쓰지 않도록 격리 venv를 `python3 -m venv`로 새로 만든 뒤 site-packages만 부었다) | **없음**. `.venv`는 `install_opal()`의 `clean_dirs`에 없어 두 install이 **같은 venv**를 쓴다 — 두 실행의 파이썬 런타임이 동일하다는 뜻이므로 오히려 대조 조건을 강화한다 |
| ④ | 격리 `HOME`에 `Library/Caches/ms-playwright/{chromium,firefox,webkit}-stub` 빈 디렉토리를 두었다 | `install_opal_venv()`의 Chromium 다운로드(약 150MB) 회피 | **없음**. 배포 산출물과 무관하며 base·after 동일 |

### 0.3 [MUST] 정규화 횟수 — **0회**

캡처한 42개 파일 중 **어느 바이트에도 치환·마스킹·정렬·시각 제거를 적용하지 않았다.**
가능했던 이유는 아래 3가지를 설계로 제거했기 때문이다.

- **경로** — 배포 경로·데이터 루트가 양쪽 실행에서 같은 절대경로다(스왑 설계). 출력에 실린 긴 `/private/tmp/...` 경로가 그대로 일치한다.
- **시각** — `worktree_tool.py`에서 `datetime`을 쓰는 곳은 `_now_str()` 1곳이고 그 값은 `_write_meta()`가 **registry meta 파일에만** 기록한다. 어떤 명령의 stdout에도 실리지 않는다(정적 확인 + §1.2 실측 일치).
- **커밋 해시** — fixture git 저장소를 pristine 스냅샷에서 `cp -a`로 복원하므로 `.git` 객체·HEAD SHA가 두 실행에서 동일하다. 게다가 6명령 출력에 커밋 SHA를 싣는 필드가 없다.

---

## 1. S-18 — monorepo 6명령 바이트 동일 (AC-12 / C-2 / H-3) — 판정: **PASS**

### 1.1 R0 monorepo fixture 정의

루트 1개 Git 저장소, 최상위 코드 디렉토리 2개(`docs`·`src`)에 각각 manifest를 둔 monorepo 형상.

```
fix_mono/
├── .gitignore                 # .opal-worktrees/
├── .opal/
│   ├── AGENT.md
│   ├── MEMORY.json
│   └── worktree.json          # layout: monorepo, repos: ["docs","src"],
│                              # taskCapsuleCone: [".opal","tasks"],
│                              # branchTemplate: feat/OP-TASK-{NNN}, baseBranch: main
├── docs/{README.md, package.json}
├── src/{app.py, pyproject.toml}
└── tasks/.gitkeep
```

- 단일 커밋 `d9a6c1f` (고정 author/committer date `2026-01-01T00:00:00+0900`), 기본 브랜치 `main`.
- `taskCapsuleCone`을 둔 것은 **119 전환 이후의 현행 monorepo**를 재현하기 위함이다 — 124가 `taskCapsuleCone` 전개 경로를 건드렸는지까지 함께 걸린다.
- pristine 파일 트리 지문(`find | sort | shasum -a 256` 의 shasum): `e661dbe703274f1d…`

### 1.2 캡처 명령 전문과 대조 결과 — 6명령 × 3채널 = 18쌍 전부 차이 0줄

```bash
export HOME="<W>/home_swap"            # 양쪽 실행이 동일한 배포 절대경로를 쓴다
WT="$HOME/.opal/tools/worktree-tool/run.sh"
FM="<W>/fix_mono"                      # 고정 데이터 루트 (pristine에서 복원)

"$WT" init     --project-root "$FM" --dry-run
"$WT" create   --project-root "$FM" --task 900 --task-folder 900-260912-fixture-task
"$WT" list     --project-root "$FM"
"$WT" status   --project-root "$FM" --task 900
"$WT" finalize --project-root "$FM" --task 900
"$WT" remove   --project-root "$FM" --task 900
```

스왑 순서: `install(base) → 캡처 14건 → install(after, 같은 HOME) → 캡처 14건 → cmp 42쌍`. 두 install 모두 종료코드 **0**.

| # | 명령 | stdout | stderr | exit b/a | stdout bytes | stdout sha256(앞 16) b / a |
|---|---|---|---|---|---|---|
| 1 | `init --dry-run` | 동일 | 동일(0B) | 0 / 0 | 791 | `d2d84164d5ddb341` / `d2d84164d5ddb341` |
| 2 | `create --task 900` | 동일 | 동일(0B) | 0 / 0 | 1402 | `87ef2d207b123e68` / `87ef2d207b123e68` |
| 3 | `list` | 동일 | 동일(0B) | 0 / 0 | 479 | `e05c953050ee0345` / `e05c953050ee0345` |
| 4 | `status --task 900` | 동일 | 동일(0B) | 0 / 0 | 973 | `f6a1007e0a329198` / `f6a1007e0a329198` |
| 5 | `finalize --task 900` | 동일 | 동일(0B) | 0 / 0 | 794 | `fb899af32bc48b69` / `fb899af32bc48b69` |
| 6 | `remove --task 900` | 동일 | 동일(0B) | 0 / 0 | 280 | `4632e771d013bf78` / `4632e771d013bf78` |

`cmp` 판정: **18/18 IDENTICAL, 정규화 0회, 차이 0줄.** stderr는 6건 모두 0바이트다.

출력 실물(after 쪽, base와 바이트 동일 — 경로는 `<W>`로 줄여 인용):

```json
// create
{"ok": true, "error": null, "command": "create", "task": "900",
 "allocator_root": "<W>/fix_mono",
 "task_home": "<W>/fix_mono/.opal-worktrees/task_900",
 "task_folder": "900-260912-fixture-task",
 "task_path": "<W>/fix_mono/.opal-worktrees/task_900/tasks/900-260912-fixture-task",
 "artifact_repo": ".", "task_ownership_version": 2, "layout": "monorepo",
 "worktree_root": "<W>/fix_mono/.opal-worktrees/task_900", "branch": "feat/OP-TASK-900",
 "entries": [{"repo": "<W>/fix_mono", "path": "<W>/fix_mono/.opal-worktrees/task_900",
              "branch": "feat/OP-TASK-900", "base_ref": "main"}],
 "gitignore": "present", "copied": [], "pending_setup": [], "port_offset": 0, "warnings": []}

// status
{... "dirty": false, "unpushed": 0, "merged": true ...,
 "task_path_source": "worktree_registered"}

// finalize
{"ok": true, ..., "state": "closed", "previous_state": "completed_unmerged", "idempotent": false,
 "declared": [".opal/brain/index.md", ".opal/brain/log.md", ".opal/MEMORY.json"],
 "observed": [], "violations": [], "committed": false, "done_file_found": false,
 "memory_index_requests_applied": [], "memory_index_requests_resolved": [], "capsule_updated": false}

// remove
{"ok": true, "error": null, "command": "remove", "task": "900",
 "removed": ["<W>/fix_mono/.opal-worktrees/task_900"], "forced": false, "bypassed_guards": []}
```

### 1.3 [MUST] `init` 초안의 키 집합과 순서 — 명시 대조 (H-3 직격)

W-6가 `_build_init_draft`를 multi-repo 분기에서만 확장했으므로 monorepo 초안은 바이트 동일해야 한다. JSON을 파싱해 `draft` 키 순서를 직접 뽑아 대조했다.

| | `draft` 키 집합과 순서 |
|---|---|
| base | `layout`, `repos`, `branchTemplate`, `copy`, `setup`, `portOffset`, `_copy_candidates`, `_help` |
| after | `layout`, `repos`, `branchTemplate`, `copy`, `setup`, `portOffset`, `_copy_candidates`, `_help` |

**키 집합 동일(8/8), 순서 동일, 값 동일, 전체 stdout 791바이트 바이트 동일.**
신설 키 `baseBranch`·`_baseBranch_candidates`·`task_artifacts`와 `_help` 꼬리말 확장은 monorepo 초안에 **하나도 나타나지 않았다.**

코드상의 근거 — `_build_init_draft`의 base↔after 차분 첫 줄이 조기 반환 가드다.

```python
def _build_init_draft(project_root, layout, repos) -> dict:
    draft = _build_init_draft_base(project_root, layout, repos)
    if layout != "multi-repo":
        return draft          # ← monorepo는 여기서 끝. 아래 확장은 도달하지 않는다
```

### 1.4 데이터 루트 동일성 실증

|  | 복원 직후 fixture 파일 트리 지문(sha256) | 실행 후 `git status --porcelain` 줄 수 |
|---|---|---|
| `fix_mono` base 실행 | `e661dbe703274f1d1d80d9656e553ddad373e293e5a173a6cdf3b7be26947529` | 0 |
| `fix_mono` after 실행 | `e661dbe703274f1d1d80d9656e553ddad373e293e5a173a6cdf3b7be26947529` | 0 |
| `fix_mono_x` base / after | 동일(위와 같은 지문) | 0 / 0 |
| `fix_plain` base / after | `ecbe03ac40c3650ff1a0a66616fd1bf8bfda8bb5d72fe26cc691e04f16093619` (양쪽) | 0 / 0 |

**두 실행이 바이트까지 같은 입력을 보았다**는 것이 지문 일치로 확정된다(§0.2 ①의 편향 없음 근거).
실행 후 `git status`가 0줄인 것은 도구가 추적 대상을 변형하지 않았다는 뜻이다(worktree 생성물은 `.gitignore`된 `.opal-worktrees/` 아래이며 `remove`가 회수했다).

### 1.5 [MUST] 비공허성 (non-vacuity) — 배포본이 실제로 달라진 상태에서 출력이 같았다

같은 고정 경로에 두 번 install한 것이 **정말로 코드를 바꿨는지**를 배포본 해시로 확인했다. 같지 않다면 "install이 실패해 같은 코드가 두 번 돌았다"와 구분되지 않는다.

| 배포 파일 (`<W>/home_swap/.opal/`) | base sha256(앞 16) | after sha256(앞 16) | |
|---|---|---|---|
| `tools/worktree-tool/worktree_tool.py` | `2bb746daa1e4b9da` | `21f6c12d0ec512a3` | **DIFF** |
| `tools/worktree-tool/tests/test_worktree_tool.py` | `747dfc613365381c` | `a321c16dc47bc0cb` | **DIFF** |
| `references/harness/worktree.md` | `b37c205630bef19f` | `323ed6cf721a1b56` | **DIFF** |

3/3 실제로 달라진 상태에서 monorepo 6명령 18/18 + 비워크트리 18/18 + 실패 표면 6/6이 동일했다 — **대조는 공허하지 않다.**

보강 근거 2가지:

- **배포본 ↔ 소스 동치**: base install 직후 `cmp <W>/home_swap/.opal/tools/worktree-tool/worktree_tool.py <W>/src_base/opal/tools/worktree-tool/worktree_tool.py` → **BYTE-EQ**. 스왑이 의도한 소스를 실었다.
- **신규 계약이 after 배포본에 실렸다**: after 배포본에서 `TASK_ARTIFACT_REPO_INVALID`·`baseBranchOverrides` 출현 **11회**, base 배포본에서는 **0회**.

### 1.6 왜 monorepo가 영향을 받지 않는가 — 변경 표면의 구조적 경계 (H-3 정적 축)

`worktree_tool.py`를 AST로 함수 단위 분해해 base↔after를 대조했다.

| 함수 | base ↔ after |
|---|---|
| `cmd_init` | UNCHANGED |
| `cmd_list` | UNCHANGED |
| `cmd_status` | UNCHANGED |
| `cmd_finalize` | UNCHANGED |
| `build_parser` | UNCHANGED |
| `load_config` / `ok_response` / `_write_meta` | UNCHANGED |
| `cmd_create` | **CHANGED** |
| `cmd_remove` | **CHANGED** |
| `_build_init_draft` | **CHANGED** (단 monorepo 조기 반환 — §1.3) |
| 신설 함수 8종 | `_root_owns_capsule`, `_root_capsule_violations`, `_root_eligibility_violations`, `_root_overlap_paths`, `_root_tracks`, `_repos_not_ignored`, `_root_base_branch_candidates`, `_build_init_draft_base` |
| 삭제 함수 | 0건 |

- `cmd_create`의 신규 블록은 `root_owned = _root_owns_capsule(cfg)`가 참일 때만 실행되고, `plan_entries` 분기도 `cfg["layout"] == "multi-repo"`로 가드된다. monorepo는 기존 단일 entry 경로를 그대로 탄다.
- `cmd_remove`의 신규 판정은 `multi_repo = meta.get("layout") == "multi-repo"`로 가드되고, monorepo는 기존 `WORKTREE_NOT_FOUND` 경로를 유지한다(§2가 실행 출력으로 확증).
- **argparse 표면 변경 0건** — `add_argument`/`add_parser` 목록이 base↔after `diff` 결과 완전 동일. 따라서 119 §0.2가 계약으로 남긴 "신규 CLI 표면 제외" 예외를 이번 판정은 **쓰지 않는다**.

### 1.7 H-3 판정 — 정규화 cfg 확장이 monorepo 출력에 새지 않았다

PLAN H-3이 지목한 위험: `validate_worktree_config` 반환 dict에 키가 늘어나므로 cfg를 통째로 직렬화하는 경로가 하나라도 있으면 `list`·`init` 출력이 달라진다.

**실제로 반환 키가 늘었다.**

| | `validate_worktree_config` 반환 키 |
|---|---|
| base | `layout`, `repos`, `branchTemplate`, `baseBranch`, `copy`, `taskCapsuleCone`, `setup`, `portOffset` (8) |
| after | 위 8개 + **`task_artifacts`**, **`baseBranchOverrides`** (10) |

그럼에도 `list`(479B)·`init`(791B)을 포함한 6명령 출력이 바이트 동일했다. PLAN이 정적 확인으로 남겨 둔 판단(`cmd_list`는 `cfg["layout"]`만 싣고, `cmd_create`·`_write_meta`는 cfg를 통째로 싣지 않으며, `cmd_init`이 싣는 `config=draft`는 cfg가 아니다)이 **실행 출력 `cmp`로 확증**되었다. **H-3 실현 0건.**

---

## 2. 추가 측정 — monorepo 실패 표면 (경로 부재 + 등록 잔존) — 판정: **PASS**

구현 과정에서 monorepo 실패 표면이 한 번 바뀌었다가 되돌려진 이력이 있으므로, 성공 경로만으로는 회귀를 놓친다.
`cmd_remove`가 `multi_repo` 가드로 갈라 놓은 **monorepo 쪽 legacy 분기**를 직접 때린다.

조건 구성: 별도 고정 데이터 루트 `fix_mono_x`(같은 pristine에서 복원) → `create --task 901` → **slot 디렉토리만 `rm -rf`** → git 등록과 registry meta는 잔존.

| # | 명령 | stdout | stderr | exit b/a | stdout sha256(앞 16) b / a |
|---|---|---|---|---|---|
| 7 | `remove --task 901` (`--force` 없음) | 동일 | 동일(0B) | 1 / 1 | `7c000bfeb6554639` / `7c000bfeb6554639` |
| 8 | `remove --task 901 --force` | 동일 | 동일(0B) | 0 / 0 | `7ea2d5c83d7212dc` / `7ea2d5c83d7212dc` |

출력 실물(양쪽 바이트 동일):

```json
// --force 없음 → legacy 응답 유지
{"ok": false, "error": "WORKTREE_NOT_FOUND",
 "message": "메타는 있으나 실제 worktree 경로가 존재하지 않습니다.",
 "path": "<W>/fix_mono_x/.opal-worktrees/task_901"}

// --force → legacy 응답 유지
{"ok": true, "error": null, "command": "remove", "task": "901",
 "removed": [], "forced": true, "bypassed_guards": []}
```

**기대값과 정확히 일치한다** — `WORKTREE_NOT_FOUND` / `--force` 시 `ok: true, removed: []`.
multi-repo 신설 계약인 `WORKTREE_REMOVE_FAILED` + `mismatch: "registration_without_path"`는 monorepo 경로에 **나타나지 않았다**(base·after 양쪽). 실패 표면 회귀 0건.

---

## 3. S-19 — 비워크트리 실행 바이트 동일 (AC-13 / C-3) — 판정: **PASS**

### 3.1 R0 비워크트리 fixture와 명령군

119 §1.1이 쓴 비워크트리 명령군을 그대로 재사용했다(D-20). fixture는 실태스크 1건(`tasks/119-…-파일럿`)과 `.opal/`(AGENT.md·MEMORY.json·code-scan.json·worktree.json) + code-scan 대상 소스(`opal/tools/memory-tool/`)를 담은 단일 Git 저장소이며, `.opal-worktrees/`가 **없다**(= 비워크트리 실행).

```bash
export HOME="<W>/home_swap"
FP="<W>/fix_plain"
TASKP="$FP/tasks/119-260912-opd-워크트리-태스크캡슐-소유권-파일럿"

"$HOME/.opal/tools/state-tool/run.sh"    show "$TASKP"
"$HOME/.opal/tools/state-tool/run.sh"    validate "$TASKP"
"$HOME/.opal/tools/worktree-tool/run.sh" list --project-root "$FP"
"$HOME/.opal/tools/memory-tool/run.sh"   show --file "$FP/.opal/MEMORY.json" --boot-brief
node "$HOME/.opal/tools/code-scan/code-scan.js" scan --project-root "$FP"
"$HOME/.opal/tools/event-loader/run.sh"  load --event session.project --project-root "$FP"
```

### 3.2 대조 결과 — 18쌍 전부 차이 0줄

| # | 명령 | stdout | stderr | exit b/a | stdout bytes | stdout sha256(앞 16) b / a |
|---|---|---|---|---|---|---|
| 9 | `state-tool show` | 동일 | 동일(0B) | 0 / 0 | 1776 | `56186150ee066141` / `56186150ee066141` |
| 10 | `state-tool validate` | 동일 | 동일(0B) | 0 / 0 | 77 | `08c62a593a726078` / `08c62a593a726078` |
| 11 | `worktree-tool list` | 동일 | 동일(0B) | 0 / 0 | 239 | `29e6d8289a3f62fd` / `29e6d8289a3f62fd` |
| 12 | `memory-tool show --boot-brief` | 동일 | 동일(0B) | 0 / 0 | 732 | `235860a87a3a3717` / `235860a87a3a3717` |
| 13 | `code-scan scan` | 동일 | 동일(0B) | 0 / 0 | 2220 | `1593d203b29639d2` / `1593d203b29639d2` |
| 14 | `event-loader load --event session.project` | 동일 | 동일(0B) | 0 / 0 | 1056 | `7a9586c33895a4bd` / `7a9586c33895a4bd` |

`cmp` 판정: **18/18 IDENTICAL, 정규화 0회, 차이 0줄.** C-3 위반 0건.

교차 확인: #12·#13의 stdout sha256(`235860a87a3a3717`·`1593d203b29639d2`)은 119 `REGRESSION-EVIDENCE.md` §1.2가 기록한 값과 **동일하다** — 119→124 두 태스크에 걸쳐 이 두 도구의 비워크트리 출력이 변하지 않았음을 뜻한다.

### 3.3 [MUST] 이 증거가 커버하지 않는 범위 (과대주장 방지)

- **`event-loader load --event session.project`는 문서 payload가 0건이다.** `document_count: 0`, `payload_bytes: 0`은 fixture 사정이 아니라 manifest(`events.json`)가 `session.project`에 선언한 문서 수가 0이기 때문이다. 따라서 이 명령은 manifest 해석·predecessor·receipt 구성을 대조할 뿐, **`harness/worktree.md` 본문이 어떤 이벤트 payload에 실리는지는 판정하지 않는다.**
  - 이것이 C-3 축소가 아닌 이유: `harness/worktree.md`는 124가 **의도적으로 개정한 규범 문서**이므로, 이 문서를 payload로 싣는 이벤트(예: `worker.dispatch`의 lazy 로드 경로)의 출력이 달라지는 것은 **회귀가 아니라 의도된 문서 변경**이다. C-3이 묻는 것은 "도구 실행 동작이 달라졌는가"다.
- fixture는 비워크트리이므로 `worktree-tool list`의 `entries`는 빈 배열이다. 워크트리가 등록된 상태의 출력은 §1(monorepo)이 판정한다.
- **multi-repo 형상은 이 문서의 판정 대상이 아니다.** multi-repo는 124가 의도적으로 동작을 바꾼 대상이며 그 검증은 S-1~S-17(pytest)이 소유한다. 여기서 판정한 것은 "monorepo·비워크트리가 안 변했다"이다.
- pug 실환경 연동은 범위 밖이다(D-22). 모든 판정은 fixture 한정이다.

---

## 4. C-8 — 실 `~/.opal/` 미배포와 허브 무결성 — 판정: **PASS**

### 4.1 install은 격리 `HOME`에만 수행했다

```bash
env -i PATH=/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin \
    HOME="<W>/home_swap" TERM=dumb LANG=en_US.UTF-8 OPAL_AUTO_INSTALL=1 \
    bash <W>/src_{base|after}/scripts/install-mac.sh </dev/null
```

`install_opal()`이 `opal_home`을 `"$USER_HOME/.opal"`로 하드코딩하고 비표준 경로를 `OPAL_HOME` 가드로 거부하므로, **`HOME` 환경변수로만 격리**했다(119 §2.1과 동일). `env -i`로 환경을 비운 것은 실 세션 환경변수가 새어 들어가는 것을 막기 위함이다.

### 4.2 실 `~/.opal/`은 한 번도 install 대상이 아니었다 — 실증

| 실 배포본 파일 | 실 `~/.opal/` sha256(앞 16) | 판정 |
|---|---|---|
| `tools/worktree-tool/worktree_tool.py` | `2bb746daa1e4b9da` | base 배포본과 **동일** = 124 미배포 |
| `references/harness/worktree.md` | `b37c205630bef19f` | base 배포본과 **동일** = 124 미배포 |

두 파일의 mtime은 `2026-09-12 17:02:5x`로, 이 측정(19:0x~19:2x)보다 **이전**이다. 측정이 실 배포본을 건드리지 않았음을 시각으로도 확인한다.
실 배포는 소유자가 merge 이후 1회 수행한다(C-8·PLAN §Release and recovery).

### 4.3 부작용 차단 실증

| 잠재 부작용 | 이번 측정 결과 |
|---|---|
| Console 데몬 기동/재기동 (119가 겪음) | **0건**. `dashboard/` 제외로 `install_dashboard` skip, `console_autostart`는 `dashboard-server/dashboard/backend 없음 — 서버 기동 스킵`. `<W>/home_swap/.opal/dashboard-server` 미생성. 측정 전후로 포트 `7823`에 이 측정이 띄운 리스너 0건 |
| `claude`/`codex` CLI 경유 MCP 등록이 실 설정을 건드림 | **0건**. `env -i` PATH 제한으로 두 CLI 미탐지 → `claude CLI 없음 — 수동 등록` 경고만. MCP 설정 파일은 전부 `<W>/home_swap/.claude`·`.cursor`·`.gemini` 아래 |
| `git config --global core.quotepath false` | 격리 `HOME`의 `.gitconfig`에만 기록됨(`HOME` 치환). 실 전역 설정은 측정 전부터 이미 `false` |
| 실 `~/.opal/.venv` 변형 | **0건**. 격리 venv를 `python3 -m venv`로 새로 만들고 site-packages를 **읽기 방향으로만** 복사했다. 두 install의 `pip`는 격리 venv의 pip다 |
| 허브/워크트리 git 변경 | **0건**. §4.4 |

### 4.4 허브·워크트리 무결성

```
$ git -C <허브> worktree list
<허브>                           4d23cb0 [main]
<허브>/.opal-worktrees/task_122  0d587c9 [feat/OP-TASK-122]
<허브>/.opal-worktrees/task_123  b44ef2f [feat/OP-TASK-123]
<허브>/.opal-worktrees/task_124  4d23cb0 [feat/OP-TASK-124]
<허브>/.opal-worktrees/task_125  4d23cb0 [feat/OP-TASK-125]
        → 측정 전과 동일. 신규 worktree 0건 (fixture worktree는 전부 <W> 하위)

$ git -C <워크트리 task_124> status --porcelain
 M docs/proposals/opal-worktree-multirepo-ownership.md
 M opal/core/references/harness/worktree.md
 M opal/tools/worktree-tool/tests/test_worktree_tool.py
 M opal/tools/worktree-tool/worktree_tool.py
?? tasks/124-260912-opds-워크트리-멀티레포-캡슐-소유권/
        → 측정 시작 시점과 동일. W-7이 추가한 소스 변경 0건, 커밋 0건
```

fixture git 조작은 전부 `git -C <dir>` 형식으로만 수행했고 `git stash`는 사용하지 않았다.
W-7의 유일한 변경 파일은 이 문서다.

---

## 5. 실패 복구 기준 — 어긋난 캡처 ↔ 소관 W 매핑

이번 측정에서 어긋난 항목은 **0건**이므로 아래는 재발 시 적용할 판정표다.

| 어긋난 캡처 | 1차 의심 소관 | 되돌릴 대상 |
|---|---|---|
| `init --dry-run` 초안 키 증가 | **W-6** (`_build_init_draft`의 multi-repo 조기 반환 가드) | `worktree_tool.py` `_build_init_draft` |
| `list` / `create` 출력에 `task_artifacts`·`baseBranchOverrides` 노출 | **W-3** (`validate_worktree_config` 확장) — H-3 실현 | `worktree_tool.py` `validate_worktree_config` 소비부 |
| monorepo `create` 실패·entry 목록 변화 | **W-4** (`plan_entries`·`root_owned` 가드) | `worktree_tool.py` `cmd_create` |
| monorepo `remove` 실패 표면 변화(`WORKTREE_NOT_FOUND` → `WORKTREE_REMOVE_FAILED` 등) | **W-5** (`multi_repo` 가드) | `worktree_tool.py` `cmd_remove` |
| `status` / `finalize` 출력 변화 | 124 변경 대상 아님(양 함수 UNCHANGED) — 119 잔여·데이터 원인 먼저 의심 | — |
| `state-tool` / `memory-tool` / `code-scan` / `event-loader` 출력 변화 | 124 변경 대상 아님 | 124 외 원인(타 태스크·데이터) 먼저 의심 |

P6 시점은 실 배포 전이므로 복구는 `git restore`(소스) + 격리 HOME 삭제 + `<W>` fixture 폐기로 끝난다.

---

## 6. fixture 잔여물 — 삭제 실증

### 6.1 사용한 임시 자원 — 전부 `<W>` 하위 (총 497M)

`src_base`, `src_after`, `home_swap`(격리 HOME·배포본·venv), `pristine_mono`, `pristine_plain`,
`fix_mono`, `fix_mono_x`, `fix_plain`, `cap_base`(48파일), `cap_after`(48파일), `capture.sh`, `install_{base,after}.log`, 배포본 해시 기록.

운영 `.opal-worktrees/` 하위에는 fixture worktree를 만들지 않았다.

### 6.2 삭제 실증 — 잔여물 0건 (2026-09-12 19:2x KST 실행)

```
$ rm -rf <W>
$ ls -d <W>
ls: <W>: No such file or directory          → 잔여물 0건
$ ls -d <W>*
zsh: no matches found: <W>*                 → 접두사 일치 잔여물 0건
$ lsof -nP -iTCP:7823 -sTCP:LISTEN | wc -l
0                                           → 리스너 0건
```

삭제 후 재확인: 실 `~/.opal/tools/worktree-tool/worktree_tool.py` = `2bb746daa1e4b9da`(base와 동일),
실 `~/.opal/references/harness/worktree.md` = `b37c205630bef19f`(base와 동일),
허브 `git worktree list` 5줄(측정 전과 동일), 워크트리 `git status --porcelain` 5줄(측정 시작과 동일).

---

## 7. 최종 판정

| 시나리오 | 완료 기준 | 결과 |
|---|---|---|
| S-18 | AC-12, C-2 — monorepo 6명령 바이트 동일 | **PASS** — 6명령 × (stdout·stderr·exit) = 18쌍 전부 차이 0줄, 정규화 0회 |
| S-18 | H-3 — 정규화 cfg 확장이 monorepo 출력에 샘 | **미실현** — 반환 키가 8→10으로 실제로 늘었음에도 `list`·`init` 포함 6명령 출력 바이트 동일 |
| S-18 | `init` 초안 키 집합·순서 | **PASS** — 8키 집합·순서·값 동일, 791바이트 바이트 동일. 신설 키 monorepo 미노출 |
| 추가 측정 | monorepo 실패 표면(경로 부재 + 등록 잔존) | **PASS** — 2경로 × 3채널 = 6쌍 동일. legacy 응답(`WORKTREE_NOT_FOUND` / `ok: true, removed: []`) 유지 |
| S-19 | AC-13, C-3 — 비워크트리 실행 바이트 동일 | **PASS** — 6명령 × 3채널 = 18쌍 전부 차이 0줄, 정규화 0회 |
| — | 비공허성 | **PASS** — 배포본 3파일 sha256이 base↔after DIFF인 상태에서 출력 42/42 동일. 배포본↔소스 BYTE-EQ, 신규 계약 문자열 after 11회 / base 0회 |
| C-8 | 실 `~/.opal/` 미배포·임시 자원 회수 | **PASS** — 실 배포본 해시·mtime 불변, `<W>` 전량 삭제·잔여물 0건, 허브 무결 |

**총계: `cmp` 42쌍 / 차이 0줄 / 정규화 0회 / 소스 코드 수정 0건 / 커밋 0건.**
블로커 없음.
