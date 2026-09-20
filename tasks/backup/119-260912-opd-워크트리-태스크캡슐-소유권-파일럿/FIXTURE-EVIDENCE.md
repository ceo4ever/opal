---
template: sdlc-v2
---
# FIXTURE-EVIDENCE: Git fixture 수명주기·회귀 실증 (W-9)

> 입력: [PLAN.md](PLAN.md) §Work items W-9 · §Decisions D-1~D-10, [TEST-SCENARIO.md](TEST-SCENARIO.md), [TASK.md](TASK.md)
> 담당 AC/C: AC-2, AC-4, AC-5, AC-9, AC-10, AC-11, AC-12, AC-15, AC-16, C-8
> 담당 시나리오: S-1~S-6, S-9~S-18, S-22, S-23, S-27, S-30

## 0. 측정 환경

| 항목 | 값 |
|---|---|
| fixture 루트 | `/private/tmp/op119w9` (C-8 — `/private/tmp` 하위 전용) |
| fixture 허브 | `/private/tmp/op119w9/hub` = `git clone --local --no-hardlinks <운영 허브>` |
| fixture 허브 base | `a5bfb77622183cde8eaac64c1d86b15db058ba36` (운영 `main`과 동일 커밋) |
| git 조작 방식 | 전 구간 `git -C <dir> ...`. `cd <dir> && git ...` 패턴 사용 0건 (C-8) |
| 원격 | `git -C <fixture> remote remove origin` — push 경로 구조적 차단 |
| 도구 실행본 | fixture 허브 clone 안의 **머지된 프로젝트 소스** (`<fixture>/opal/tools/*/run.sh`) |

**[중요] 배포본(`~/.opal/`)은 이 시점에 stale이다.** 확인값:

```bash
grep -c "_resolve_canonical_task_path" ~/.opal/tools/worktree-tool/worktree_tool.py   # → 0
grep -c "_resolve_canonical_task_path" opal/tools/worktree-tool/worktree_tool.py      # → 3
grep -c "상태 의존 해석" ~/.opal/references/harness/worktree.md                       # → 0
grep -c "task-folder" ~/.opal/references/harness/task-process.md                      # → 0
```

따라서 본 측정은 전부 **머지된 프로젝트 소스**로 수행했다. 실 `~/.opal/` 배포와 그 위의 파일럿 완주는 W-10(S-19·S-20) 소관이며 소유자 권한이다.

fixture 한정 조정 2건(측정 성격에 영향 없음): `.opal/worktree.json`의 `setup`(`npm ci`)을 `[]`로 비웠고, 최소 파이프라인(`execute.implement`·`close.done_md` 2행) JSON을 `--rows-from` 입력으로 사용했다.

## 1. ① 새 순서 전 구간 (AC-1·AC-2·AC-15 / S-2·S-3)

`harness/task-process.md` §채번 규칙 3·4항 → 스텝 4.5 → 스텝 5 문면 그대로 실행했다.

### 스텝 1 — 채번 (허브 절대경로 `--file`)

```bash
<fx>/opal/tools/memory-tool/run.sh task-number --file /private/tmp/op119w9/hub/.opal/MEMORY.json --bump
```
```json
{"ok": true, "command": "task-number", "last_task_number": 121, "previous": 120, "bumped": true}
```

### 스텝 4.5 — `worktree-tool create --task-folder`

```bash
<fx>/opal/tools/worktree-tool/run.sh create --project-root /private/tmp/op119w9/hub \
  --task 121 --task-folder "121-260912-opd-픽스처-수명주기"
```
```json
{"ok": true, "command": "create", "task": "121",
 "allocator_root": "/private/tmp/op119w9/hub",
 "task_home":      "/private/tmp/op119w9/hub/.opal-worktrees/task_121",
 "task_folder":    "121-260912-opd-픽스처-수명주기",
 "task_path":      "/private/tmp/op119w9/hub/.opal-worktrees/task_121/tasks/121-260912-opd-픽스처-수명주기",
 "artifact_repo": ".", "task_ownership_version": 2,
 "worktree_root": "/private/tmp/op119w9/hub/.opal-worktrees/task_121",
 "branch": "feat/OP-TASK-121", "warnings": []}
```

6필드 발급이 계약대로 나온다. **`create` 직후 `task_path` 디렉토리 실재 = `NOT EXISTS`** — D-2가 근거로 삼은 "`create`는 경로 계약만 확정한다"가 실측으로 재확인됐다.

### 스텝 4.5-1·2, 스텝 5 — mkdir → TASK.md → `state init`

```bash
mkdir -p "<task_path>"
printf ... > "<task_path>/TASK.md"
<fx>/opal/tools/state-tool/run.sh init "<task_path>" --skill opd --mode semi-agentic \
  --task-title "fixture 수명주기" --worktree "/private/tmp/op119w9/hub/.opal-worktrees/task_121"
```
```json
{"ok": true, "command": "init", "task_path": "/private/tmp/op119w9/hub/.opal-worktrees/task_121/tasks/121-260912-opd-픽스처-수명주기", "rows_count": 0}
```

### S-2 판정

| 관측 | 값 |
|---|---|
| 워크트리 안 `state.json` | `YES` |
| 허브 `tasks/121-*` | **없음** |
| 워크트리 `tasks/121-*` | `/private/tmp/op119w9/hub/.opal-worktrees/task_121/tasks/121-260912-opd-픽스처-수명주기` |

**S-2 PASS** — 태스크 폴더와 `state.json`이 워크트리 안에만 생성되고 허브 `tasks/`에는 생기지 않는다.

### S-3 — 채번 `--file` 인자 (cwd = 워크트리)

| 호출 | 결과 |
|---|---|
| `--file <허브 절대경로>/.opal/MEMORY.json` | `{"ok": true, "last_task_number": 122}` |
| `--file .opal/MEMORY.json` (상대경로) | `{"ok": false, "error": "WORKTREE_WRITE_REJECTED", "rejected": "task-number", "path": ".opal/MEMORY.json"}` |

**S-3 PASS** — D-2b가 없었으면 새 순서가 1스텝에서 즉시 실패했을 지점이 절대경로 명시로 통과한다.

## 2. ② fallback과 중단 주입 (AC-2·AC-15·C-3 / S-4·S-22)

### S-4 (a) — `CONFIG_NOT_FOUND` 주입

`.opal/worktree.json`을 일시 제거한 뒤 스텝 4.5 실행.

```json
{"ok": false, "error": "CONFIG_NOT_FOUND", "message": "'.opal/worktree.json' 설정 파일을 찾을 수 없습니다.", "path": "/private/tmp/op119w9/hub/.opal/worktree.json"}
```

| 시점 | 허브 `tasks/125-*` | 워크트리 `task_125` |
|---|---|---|
| `create` 실패 직후 | 없음 | 없음 |
| D-10 fallback 실행 후 (`mkdir` → TASK.md → `--worktree` 없이 `state init`) | 존재 | 없음 |

fallback으로 만든 `state.json`의 키 목록에 **`worktree` 키 부재** — 현행 비워크트리 스키마와 동일하다. **S-4(a) PASS** (폴더가 한 위치에만).

### S-4 (b) — 경로 충돌 주입

`.opal-worktrees/task_126`을 미리 선점한 뒤 `create`:

```json
{"ok": false, "error": "GIT_COMMAND_FAILED",
 "detail": "fatal: '/private/tmp/op119w9/hub/.opal-worktrees/task_126' already exists\n",
 "rolled_back": 1}
```

허브 폴더 없음 / 워크트리 캡슐 없음 / **브랜치 `feat/OP-TASK-126` 생성 안 됨** — 도구의 all-or-nothing 롤백이 동작한다. **S-4(b) PASS**

> 주입 시도 기록: "브랜치 점유"는 **실패 주입이 되지 않는다**. `main`을 가리키는 `feat/OP-TASK-125` 브랜치가 이미 있어도 `create`는 그 브랜치로 worktree를 붙여 `ok: true`를 반환한다. 이는 제품 결함이 아니라 fixture 주입 설계의 한계이며, 위 두 주입(`CONFIG_NOT_FOUND`·경로 충돌)으로 대체했다.

### S-22 — 새 순서 각 스텝에서 중단 주입

| 중단 지점 | 허브 `tasks/{folder}` | 워크트리 캡슐 | 동시 존재 |
|---|---|---|---|
| 채번 직후 | 없음 | 없음 | 없음 (PASS) |
| `create` 직후 | 없음 | 없음 | 없음 (PASS) |
| `mkdir` 직후 | 없음 | 존재 | 없음 (PASS) |
| TASK.md 작성 직후 | 없음 | 존재 | 없음 (PASS) |

**S-22 PASS** — 새 순서에서는 폴더를 나중에 만들므로 두 위치 동시 존재가 구조적으로 불가능하다(D-10 근거 재확인).

## 3. ③ cone (AC-3 / S-5·S-6)

### S-5 — `taskCapsuleCone` 활성 상태

```bash
git -C <wt> sparse-checkout list
```
```
.opal
cursor-rules
dashboard
docs
opal
scripts
skills
tasks
```

| 경로 | 실체화 |
|---|---|
| `.opal/AGENT.md` | OK (file) |
| `.opal/MEMORY.json` | OK (file) |
| `.opal/brain` | OK (dir, `pages/concept` 317건) |
| `tasks` | OK (dir, 22 항목) |

**S-5 PASS**

### S-6 — `taskCapsuleCone` 키 미지정

키를 제거한 설정으로 `create` 실행:

| 관측 | 값 |
|---|---|
| `sparse-checkout list` | `cursor-rules dashboard docs opal scripts skills` |
| 설정 `repos` | `cursor-rules dashboard docs opal scripts skills` |
| `.opal` 실체화 | NO |
| `tasks` 실체화 | NO |

**S-6 PASS** — cone이 `repos`와 동일한 no-op이다. 키 제거만으로 즉시 전환 전 동작으로 돌아간다.

## 4. ④ 상태 의존 canonical path 해석 (AC-4·C-9 / S-7·S-8)

허브 `tasks/{task_folder}` 사본과 워크트리 캡슐을 **동시 존재**시킨 뒤, registry meta의 `attribution_state`를 4값으로 바꿔가며 `status`·`finalize`를 호출했다.

| `attribution_state` | `status` | `finalize` |
|---|---|---|
| 키 부재 | `ok:false` `TASK_PATH_AMBIGUOUS` | `ok:false` `TASK_PATH_AMBIGUOUS` |
| `completed_unmerged` | `ok:false` `TASK_PATH_AMBIGUOUS` | `ok:false` `TASK_PATH_AMBIGUOUS` |
| `attribution_pending` | `ok:false` `TASK_PATH_AMBIGUOUS` | `ok:false` `TASK_PATH_AMBIGUOUS` |
| `closed` | `ok:true`, `task_path_source: "hub_merged"`, `task_path: <허브>/tasks/{folder}` | `ok:true`, `state: "closed"`, `idempotent: true` |

`closed` 상태 `finalize` 재진입의 커밋 무생성 확인:

```
HEAD  a5bfb77... -> a5bfb77...   (무변경)
커밋수 503 -> 503
```

**S-7 PASS** (active 3상태 모두 차단 — 118 단일 복사본 불변식 무약화) / **S-8 PASS** (`closed`만 통과, 허브 merge 사본을 canonical로 반환, finalize 커밋 없이 멱등 반환).

### D-6 반증 — 경로 A(`--no-ff --no-commit`)는 현행 계약이 아니다

별도 태스크(124)로 실측했다. 캡슐 커밋 후 `finalize` 없이 `git merge --no-ff --no-commit`:

```
Automatic merge went well; stopped before committing as requested
허브 캡슐 존재: /private/tmp/op119w9/hub/tasks/124-260912-opd-경로A-반증
meta attribution_state: (부재)
```
```json
finalize → {"ok": false, "error": "TASK_PATH_AMBIGUOUS",
  "candidates": ["<wt>/tasks/124-...", "<hub>/tasks/124-..."]}
status   → {"ok": false, "error": "TASK_PATH_AMBIGUOUS", ...}
```

merge 커밋 안에서 귀속을 확정하려는 시점에 `attribution_state`가 아직 `closed`가 아니므로 D-1 해석에서도 차단이 **정상 판정**이다. `harness/worktree.md` §merge 경로의 `[MUST]` 문장이 문서 문면뿐 아니라 실제 동작과 일치한다.

## 5. ⑤ 동일 경로 관측 (재정의된 AC-4 / S-9)

```bash
<fx>/opal/tools/worktree-tool/run.sh status --project-root <허브> --task 121
```
```json
{"ok": true, "task_path": "/private/tmp/op119w9/hub/.opal-worktrees/task_121/tasks/121-260912-opd-픽스처-수명주기",
 "task_path_source": "worktree_registered"}
```

두 프로세스가 이 canonical `task_path`를 입력받아 각자 cwd에서 `realpath(<task_path>/state.json)` 관측:

| 프로세스 | cwd | 관측값 |
|---|---|---|
| PM | `/private/tmp/op119w9/hub` | `/private/tmp/op119w9/hub/.opal-worktrees/task_121/tasks/121-260912-opd-픽스처-수명주기/state.json` |
| 워커 | `/private/tmp/op119w9/hub/.opal-worktrees/task_121` | `/private/tmp/op119w9/hub/.opal-worktrees/task_121/tasks/121-260912-opd-픽스처-수명주기/state.json` |

**S-9 PASS** — 동일 문자열. D-7이 재정의한 AC-4 기준이 실제로 관측 가능하다(S-26 입력).

## 6. ⑥ 수명주기 두 경로 (AC-9 / S-12·S-13·S-14·S-17)

경로 B = `finalize` → 캡슐 커밋 → merge → `finalize-attribution` → `status --set done` → `remove`.

### 경로 B-1 — `git merge --ff-only` (태스크 122)

| 단계 | 관측 |
|---|---|
| 생성 | 새 순서 전 구간. 워크트리 안 `task_path`, 허브 `tasks/122-*` 없음 |
| 워크트리 신규 메모리 | `{"deferred": true, "index_request": "<task_path>/memory-index-request.json", "pending_count": 1}` |
| CLOSE mark | `{"ok": true, "row_id": 2, "stage": "CLOSE", "owner": "user"}` |
| **S-12** | `current_status = completed_unmerged` / 허브 `tasks/122-*` **없음** / 허브 MEMORY `history` 건수 5 → 5 (무변경) |
| **S-17 (a)** | `remove` → `{"ok": false, "error": "MEMORY_INDEX_REQUEST_PENDING", "pending": ["e3b0c442…"]}` |
| `finalize` (merge 전) | `{"ok": true, "state": "closed", "previous_state": "completed_unmerged", "memory_index_requests_applied": ["e3b0c442…"], "memory_index_requests_resolved": ["e3b0c442…"], "capsule_updated": true, "violations": []}` — 요청 status `pending` → `applied`, `resolved` **정확히 1건** |
| 캡슐 커밋 | `2a3690b feat(122): fixture 코드 변경 + 태스크 캡슐` — `docs/PROJECT.md` + `tasks/122-…/{TASK.md,STATE.md,state.json,memory-index-request.json}` 5파일 |
| `git merge --ff-only` | 성공. 허브 HEAD = `2a3690b` |
| merge 후 `status` | `{"ok": true, "task_path_source": "hub_merged", "task_path": "<허브>/tasks/122-…"}` |
| **S-13 (c)** | `--allocator-root` 미지정 → `allocator_root_required` / 상대경로 `.` → `allocator_root_not_absolute` |
| **S-13 (a)** | `finalize-attribution … --allocator-root <허브>` → `{"status": "created"}` |
| **S-13 (b)** | 동일 인자 재실행 → `{"status": "duplicate_skipped"}`, history 행 증가 0 |
| `status --set done` | `completed_unmerged -> done` |
| **S-17 (b)** | `remove` → `{"ok": true, "removed": ["…/task_122"], "forced": false, "bypassed_guards": []}` — 우회 0건, 기존 3중 가드만 적용 |

history 행 확인 (FIFO=5, 신규 1건이 head에 append):
```
['tasks/122-260912-opd-수명주기-ffonly/', 'tasks/118-…/', 'tasks/117-…/', 'tasks/116-…/', 'tasks/115-…/']
```

### 경로 B-2 — `git merge --no-ff` (태스크 123, divergence 주입)

`main`에 선행 커밋 `a6ae4a2`를 넣어 FF 불가 상태를 만든 뒤 동일 경로 완주.

| 단계 | 관측 |
|---|---|
| FF 가능 여부 | `NO` (non-FF 확정) |
| **S-12** | `current_status = completed_unmerged` / 허브 `tasks/123-*` **없음** |
| `finalize` (merge 전) | `{"ok": true, "state": "closed", "applied": ["e3b0c442…"], "committed": false}` |
| 캡슐 커밋 | `4b9f8c2 feat(123): fixture 코드 변경 + 태스크 캡슐` |
| `git merge --no-ff` | 성공. merge 커밋 `4ceff06`, 부모 2개 |
| merge 후 `status` | `{"ok": true, "task_path_source": "hub_merged"}` |
| **S-13** | `created` → 재실행 `duplicate_skipped` |
| `status --set done` | `completed_unmerged -> done` |
| `remove` | `{"ok": true, "bypassed_guards": []}` |

merge 그래프:
```
*   4ceff06 merge(123): no-ff 경로
|\
| * 4b9f8c2 feat(123): fixture 코드 변경 + 태스크 캡슐
* | a6ae4a2 chore: main 선행 커밋 (divergence)
|/
* 2a3690b feat(122): fixture 코드 변경 + 태스크 캡슐
```

**S-14 PASS** — `--ff-only`와 `--no-ff` 두 경로 모두 귀속이 merge **전** 브랜치 finalize에서 확정되고 수명주기가 닫힌다. **S-12 PASS / S-13 PASS / S-17 PASS**

## 7. ⑦ 기존 태스크 무변경과 커밋 집합 (AC-5·AC-6 / S-10·S-11)

### S-10

```bash
git -C <hub> diff --stat a5bfb77 HEAD -- tasks/
```

전 구간 종료 후 base 대비 `tasks/` 변경은 신규 태스크 122·123의 8파일뿐이다.

| 판정 | 값 |
|---|---|
| 현재 태스크 제외 커밋 diff 건수 | **0** |
| 현재 태스크 제외 워킹트리 변경 건수 | **0** |
| 대상 기존 태스크 폴더 수 | 22 |

**S-10 PASS**

### S-11

`git -C <wt> log --oneline main..HEAD` / `git -C <wt> diff --name-only main..HEAD`:

```
2a3690b feat(122): fixture 코드 변경 + 태스크 캡슐
docs/PROJECT.md                                          ← 코드 변경
tasks/122-260912-opd-수명주기-ffonly/TASK.md              ← 캡슐
tasks/122-260912-opd-수명주기-ffonly/STATE.md
tasks/122-260912-opd-수명주기-ffonly/state.json
tasks/122-260912-opd-수명주기-ffonly/memory-index-request.json
```

merge 후 허브 관측: `tasks/122-…/` 4파일 존재 + `grep -c "fixture 122 코드 변경 마커" docs/PROJECT.md` → `1`. 경로 B-2도 동일(`opal/core/references/tools.md` 마커 1건 + 캡슐 4파일).

**S-11 PASS** — 코드 변경과 태스크 캡슐이 같은 브랜치 커밋 집합에 있고 merge 결과에 둘 다 나타난다.

## 8. ⑧ memory·brain 경계 (AC-10·AC-11·AC-12 / S-15·S-16·S-17)

### S-16 — 워크트리 memory-tool

| 호출 (cwd = 워크트리, `--file <wt>/.opal/MEMORY.json`) | 결과 |
|---|---|
| `append --kind memory --task-path <task_path>` | `{"ok": true, "deferred": true, "index_request": "<task_path>/memory-index-request.json", "pending_count": 1}` |
| `append --kind history` | `WORKTREE_WRITE_REJECTED` |
| `update` | `WORKTREE_WRITE_REJECTED` |
| `promote` | `WORKTREE_WRITE_REJECTED` |
| `delete` | `WORKTREE_WRITE_REJECTED` |
| `prune` | `WORKTREE_WRITE_REJECTED` |
| `task-number` | `WORKTREE_WRITE_REJECTED` |

`.opal/memory/note.local.md` md5: 거부 6연산 전후 `2349fa2557f17aa0889348b331c4354c` → `2349fa2557f17aa0889348b331c4354c` (**무변경**). `git -C <wt> check-ignore -v` → `.gitignore:14:*.local.md`.

finalize 1회 반영은 §6 경로 B-1·B-2 행에 있다 — `memory_index_requests_applied` 1건, meta `memory_index_requests_resolved` 1건, 캡슐 요청 status `pending` → `applied`, `closed` 재진입 시 `applied` 목록 빈 배열.

**S-16 PASS**

### S-17

| 조건 | `remove` 결과 |
|---|---|
| 미처리 index 요청 잔존 | `{"ok": false, "error": "MEMORY_INDEX_REQUEST_PENDING", "pending": ["e3b0c442…"]}` |
| `finalize`로 해소 후 | `{"ok": true, "forced": false, "bypassed_guards": []}` |

**S-17 PASS**

### S-15 — 회고적 brain 학습

워크트리에서 (cwd = 워크트리):

| 호출 | 결과 |
|---|---|
| `add-page … ` (`--allocator-root` 미지정) | `{"ok": false, "error": "allocator_root_required", "reason": "cwd_inference_in_worktree"}` |
| `add-page … --allocator-root .` (상대경로) | `{"ok": false, "error": "allocator_root_required", "reason": "relative"}` |

워크트리 brain 상태 (전 구간):

| 항목 | 값 |
|---|---|
| `pages/concept` 건수 | 317 → 317 |
| `index.md` md5 | `81f449d22a4b4e18708ed7d86bcae7e5` (무변경) |
| `log.md` md5 | `e44c13b4f5bffcfe65759c57949dbaed` (무변경) |
| `git -C <wt> status --porcelain -- .opal/brain` | 0건 |

merge 후 허브에서 판정 수행:

| 호출 (cwd = 허브, `--allocator-root <허브 절대경로>`) | 결과 |
|---|---|
| `add-page concept/w9-fixture-lesson` | `{"ok": true, "indexed": true}` (create) |
| 동일 슬러그 재실행 | `{"ok": false, "error": "duplicate_page", …"갱신은 update-page를 사용"}` (skip) |
| `update-page` | `{"ok": true, "updated_fields": ["title"], "indexed": true}` (update) |
| `index` | `{"ok": true, "pages_scanned": 349, "index_written": true}` |
| `log --op ingest --summary …` | `{"ok": true, "logged": true}` |

허브 brain: pages 317 → 318, `index.md` md5 변경, `log.md` md5 `e44c13b4…` → `9be0829d…`.

**S-15 PASS** — 워크트리에서 page·index·log 무변경, merge 후 허브에서 create/update/skip 판정 + index 재생성 + log 기록.

> **관측된 한계 (AC-10, 차단 아님)**: `brain_tool.finalize_brain_root()`는 `--allocator-root`가 **절대경로이기만 하면** 그 경로가 `.opal-worktrees/` 안이어도 수용한다. `_inside_worktree()` 판정은 `--allocator-root` 미지정(cwd 추론) 분기에만 쓰인다. 실측: `add-page … --allocator-root <워크트리 절대경로>`는 `ok: true`로 워크트리 brain에 page를 쓰고 index를 갱신했다(측정 후 원복, `git status` 0건 복구 확인). AC-10이 집행하는 경로 — CLOSE가 후보만 `DONE.md §회고적 학습 후보`에 선언하고 판정은 허브에서 수행 — 은 정상 동작하므로 AC-10 판정은 PASS로 유지하되, "워크트리 brain 쓰기 불가"가 **구조적 불변식은 아니라는 점**을 기록한다. 개선이 필요하면 별도 태스크 소관이다.

## 9. ⑨ legacy·비워크트리 보존 (AC-16·C-5 / S-18·S-23)

### S-18 (a) — `task_ownership_version` 부재 legacy

meta에서 `task_ownership_version`을 제거하고 허브 사본과 워크트리 캡슐을 동시 존재시킨 뒤 `status`:

```json
{"ok": true, "error": null, "task_path_source": null, "task_path": null}
```

모호성 판정 자체를 건너뛰고(차단도, canonical 발급도 하지 않음) 양쪽 위치 모두 **자동 이동 없음**. **S-18(a) PASS**

### S-18 (b) — 비워크트리 태스크

허브 `tasks/`에 폴더 생성 후 `--worktree` 없이 `state init`:

```
state.json 키: ['task_id','skill','mode','schema_version','created_at','updated_at','current_status','rows','next_action']
worktree 키: 없음 (현행 스키마 100% 유지)
위치: <허브>/tasks/129-…  /  워크트리 사본: 없음
registry 등록 태스크: ['121']   ← 비워크트리 태스크는 registry에 등록되지 않음
```

**S-18(b) PASS**

### S-23 — cone 활성 상태의 워크트리 `.opal` 사본

| 검증 | 명령 | 결과 |
|---|---|---|
| `task_root` 착지 | `state_tool.task_root('<wt task_path>')` | `/private/tmp/op119w9/hub/.opal-worktrees/task_121` (워크트리 자신) |
| `task_root` 비워크트리 대조 | `state_tool.task_root('<hub>/tasks/119-…')` | `/private/tmp/op119w9/hub` (허브) |
| memory-tool 거부 게이트 | §8 S-16 표 | 6연산 `WORKTREE_WRITE_REJECTED` |
| `.opal/code-scan.json` 사본이 스캔 결과를 바꾸지 않음 | `code-scan scan --project-root <허브>` vs `--project-root <워크트리>` | 양쪽 `127 file(s)`, 루트 경로 정규화 후 **diff 0줄** |
| `.opal/worktree.json` 사본 = 읽기 snapshot | `worktree-tool list --project-root <워크트리>` | `{"ok": true, "entries": []}` — 워크트리가 자기를 허브로 간주하지 않는다. 실제 호출은 전 구간 `--project-root <허브>` 명시로 수행 |

`event-loader`는 `_project_root()`가 "`.git`과 `.opal/AGENT.md`를 함께 가진 첫 조상"을 task root로 반환하며, cone으로 워크트리에 `.opal/AGENT.md`가 실체화됨을 §3 S-5에서 확인했다. `session.project` 이벤트는 required document 0건이라 문서 목록으로는 루트를 가를 수 없어, 루트 해석은 `.opal/AGENT.md` 실체화 실측으로 대신했다.

**S-23 PASS**

## 10. 회귀 스위트

```bash
~/.opal/.venv/bin/python -m pytest opal/tools/worktree-tool/tests/ -q   # 83 passed
~/.opal/.venv/bin/python -m pytest opal/tools/state-tool/tests/ -q      # 425 passed, 3 skipped, 111 subtests passed
```

합산 실행: `508 passed, 3 skipped, 111 subtests passed`. 실패 0건.

EXECUTE 진입 계약 검사:
```json
state-tool verify --plan-contract-check        → {"ok": true, "plan_contract_check": "pass", "work_items": ["W-1",…,"W-10"]}
state-tool verify --code-scan-citation-check   → {"ok": true, "code_scan_citation_check": "pass"}
```

## 11. S-27 — 상태 파일의 도구 외 직접 편집 흔적

| 검사 | 결과 |
|---|---|
| `state-tool validate <태스크폴더>` | `{"ok": true, "violations": [], "violations_count": 0}` |
| `test-tool scenario-coverage-check` | `{"ok": true}` |
| `state.json` 워킹트리 diff 라인 유형 | `updated_at`, `timestamp`, `note`, `step` 만 — `state-tool mark --action-step` 형상과 일치 |
| `test-scenario.json` 워킹트리 변경 | 0건 |
| W-9가 수행한 두 파일 편집 | **0건** (fixture 안에서도 `state-tool`/`test-tool` 경유만 사용) |

**S-27 PASS**

## 12. S-30 — fixture 잔여물과 운영 허브 무결성

fixture 회수: 잔여 `task_121` 슬롯은 `remove`가 `MEMORY_INDEX_REQUEST_PENDING`으로 한 번 거부한 뒤 `--force`(`bypassed_guards: ["MEMORY_INDEX_REQUEST_PENDING","GUARD_DIRTY"]`)로 회수했고, 이어서 fixture 루트를 전량 삭제했다.

| 검사 | 결과 |
|---|---|
| `ls -1d /private/tmp/op119w9*` | **0건** |
| 운영 `git worktree list` vs 작업 전 baseline | **diff 0줄** (`main` + `.opal-worktrees/task_119` 2건) |
| 운영 `git branch --list` vs baseline | **diff 0줄** |
| 운영 `.opal-worktrees/` 하위 | `task_119` 1건 — fixture worktree 흔적 **0건** |
| 운영 `.opal/MEMORY.json` md5 | `0a1f1fea7dc2e3113ddc04ee0a09ecc4` (baseline과 동일, 무변경) |
| 운영 HEAD | `a5bfb77` (무변경 — 운영 허브 커밋·머지·푸시 0건) |
| `cd <dir> && git ...` 패턴 사용 | **0건** (전 구간 `git -C`) |

> `/private/tmp/op119-scen.json`·`op119-scen2.json`은 선재 파일로 W-9가 만든 것이 아니며 `op119w9*` 네임스페이스 밖이다. W-8 소유 경로(`/private/tmp/op119w8*`)와 `REGRESSION-EVIDENCE.md`는 건드리지 않았다.

**S-30 PASS**

## 13. 판정 요약

| S | 대상 AC/C | 판정 |
|---|---|---|
| S-2 | AC-1 | PASS |
| S-3 | AC-1, AC-3 | PASS |
| S-4 | AC-2, AC-15, C-3 | PASS |
| S-5 | AC-3 | PASS |
| S-6 | AC-3, C-1 | PASS |
| S-9 | AC-4 (D-7 재정의) | PASS |
| S-10 | AC-5 | PASS |
| S-11 | AC-6 | PASS |
| S-12 | AC-7 | PASS |
| S-13 | AC-8 | PASS |
| S-14 | AC-9 (D-6 재정의) | PASS |
| S-15 | AC-10 | PASS (§8 한계 주석 동반) |
| S-16 | AC-11 | PASS |
| S-17 | AC-12 | PASS |
| S-18 | AC-16, C-5 | PASS |
| S-22 | H-2 | PASS |
| S-23 | H-3 | PASS |
| S-27 | C-4 | PASS |
| S-30 | C-8 | PASS |

담당 AC/C 전건(AC-2·AC-4·AC-5·AC-9·AC-10·AC-11·AC-12·AC-15·AC-16·C-8)이 실행 증거로 확인됐다. 실패 0건.

**W-9 범위 밖 (미수행)**: S-1(비워크트리 바이트 동일 — W-8 소관), S-7·S-8의 단위 테스트 축은 §10 스위트가 담당, S-19·S-20(실 `~/.opal/` 배포와 파일럿 완주 — W-10, 소유자 권한), S-21·S-24~S-26·S-28·S-29.
