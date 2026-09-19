# PROBE-OWNERSHIP — registry 등록 재배포·실측과 기존 증거 회귀 확인 (W-8 / P5)

> 완료 기준: AC-9 · AC-10 · AC-11 · AC-12 · AC-14 · C-8
> checklist_source: `PLAN.md` W-8 행 + Risks H-3 · H-4
> scenario_source: `TEST-SCENARIO.md` S-12 · S-14 · S-15 · S-20 (인용: S-9 · S-10 · S-11)
> 실측 일시: 2026-09-19 20:20~20:23 KST

## 0. 세션 식별자 3종 (H-5 — 착수 직후 선기록)

| 식별자 | 관측값 | 판정 |
|---|---|---|
| `CLAUDE_CODE_SESSION_ID` | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` | 존재 |
| `OPAL_SESSION_ID` | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` (`typeset -p` → `export` 속성 있음) | 존재·export됨 |
| hook 봉투 `session_id` | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` | 3종 **전건 일치** |
| 허브 registry `owner_session_id` (착수 시점) | `null` | **이번 작업이 채울 대상** — blocked 조건 아님 (디스패치 명시) |
| 태스크 lease `owner.json.owner_session_id` | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` | 세션 3종과 일치 |

→ **H-5 판정: PASS.** 워커 세션 식별자 3종이 일치하고 lease owner와도 같다. 잘못된 세션을 측정할 위험 없음.
착수 시점의 registry `owner_session_id=null`은 PROBE-BASELINE §5.4가 판정한 **구조적 결손**(부트 이후 registry를 채우는 주체 부재)이며, W-6이 그 주체를 추가한 것이 이 프로브의 검증 대상이다.

---

## 1. 재배포 (H-3 · H-4 · S-15 · S-20)

### 1.1 재배포 전 대조 기준 (PM 실측값 재확인)

| 대조 항목 | PM 제시 기준 | 워커 실측 (재배포 전) | 일치 |
|---|---|---|---|
| 배포본 `session_start_hook.py`의 `export {}` 패턴 | 0건 (구버전) | `grep -c 'export '` → **0** | 일치 |
| 배포본 `_register_registry_owner` | (구버전이므로 부재) | `grep -c` → **0** | 일치 |
| `dashboard/frontend/dist/` | 부재 | `ls -d` → No such file or directory | 일치 |
| `git status --porcelain dashboard/` | 빈 출력 | 빈 출력 | 일치 |
| 워크트리 **소스** hook `export ` | (수정본) | 3건 | W-1 반영됨 |
| 워크트리 **소스** hook `_register_registry_owner` | (수정본) | 2건 | W-6 반영됨 |

→ 재배포 전 배포본은 **구버전**, 소스는 **수정본**. 대조 기준 성립.

### 1.2 재배포 실행

```
cd /Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_999
OPAL_AUTO_INSTALL=1 bash scripts/install-mac.sh
```

- **EXIT=0** (소유자 승인 하 1회 실행)
- 로그 말미: `✓ OPAL 설치 완료 (main)`, OPAL Console 재기동(PID 91135, 127.0.0.1:7823, `/health` → `{"status":"ok"}`)
- 전체 로그: `<scratchpad>/install.log`

### 1.3 H-4 · S-20 — 재배포 직후 빌드 부산물 처리 (즉시 수행)

| 시점 | `git status --porcelain dashboard/` | `dashboard/frontend/dist/` |
|---|---|---|
| 재배포 **직후** | **빈 출력** | **생성됨** (`install-mac.sh:1842` `npm run build`) |
| `rm -rf dist/` 후 재확인 | **빈 출력** | **부재** |

- `dist/`는 `.gitignore` 대상이라 `git status`에는 잡히지 않았으나, `dashboard/frontend/src/lib/api-env-files.test.ts:57`이 `expect(existsSync(path.join(FRONTEND_ROOT, "dist"))).toBe(false)`로 **파일시스템 존재 자체**를 단언한다. 따라서 git 출력이 비어 있어도 삭제가 필요했다.
- → **H-4 회피 성공. S-20 PASS.** W-10의 stage 전에 한 번 더 확인해야 한다(아래 §6 인계).

### 1.4 S-15 — 배포본 반영 확인 (절반 배포 차단 게이트)

| 확인 | 결과 |
|---|---|
| 배포본 `export ` 접두 write | `session_start_hook.py:186` `handle.write("export {}={}\n".format(...))` — **존재** (W-1 반영) |
| 배포본 `_register_registry_owner` | `:115` 정의, `:247` 호출 — **존재** (W-6 반영) |
| `diff <소스> <배포본>` | **IDENTICAL** (바이트 동일) |

→ **S-15 PASS.** 절반 배포 상태 아님. PLAN `Release and recovery` (d)의 중단 조건에 해당하지 않으므로 프로브를 진행했다.

### 1.5 C-1 준수

- 모든 소스 수정은 워크트리(`opal/tools/ownership-tool/...`) 안에만 있다. 이 Work item에서 워커는 **소스·테스트 파일을 일절 수정하지 않았다**.
- `~/.opal/` 배포본을 **손으로 편집한 사실이 없다**. 배포본 변경은 전적으로 `install-mac.sh` 경유다(§1.4의 `diff` IDENTICAL이 이를 뒷받침 — 수기 편집이 있었다면 소스와 갈라진다).
- H-3(재배포가 `~/.opal/tools/`를 clean 후 재생성) 구간 부작용: hook 전 경로 fail-safe exit 0이므로 세션 차단 없음. 재배포 완료 후에만 프로브를 시작했다.

---

## 2. 부트 경계 재현과 registry 실측 (S-12 / AC-12)

### 2.1 재현 방법

실제 SessionStart 봉투를 **배포본** 진입점에 stdin 주입(실사용 경로 검증):

```bash
CLAUDE_ENV_FILE=<scratchpad>/probe-env-w8.sh \
  ~/.opal/.venv/bin/python ~/.opal/tools/ownership-tool/ownership_tool/session_start_hook.py \
  < <scratchpad>/envelope-w8.json
# EXIT=0
```

봉투: `{"session_id":"4e1a2aa2-1800-43e6-af3c-60b86a27b237","cwd":"<worktree_root>","hook_event_name":"SessionStart","source":"startup"}`
— `session_id`는 이 워크트리의 **실제 세션 ID**, `cwd`는 워크트리 루트.

- `CLAUDE_ENV_FILE`은 **임시 파일**만 사용했고, 플랫폼 소유 `~/.claude/session-env/` 아래는 건드리지 않았다.
- 기록된 env 파일 내용: `export OPAL_SESSION_ID=4e1a2aa2-1800-43e6-af3c-60b86a27b237` — **`export ` 접두 확인**(W-1 계약).

### 2.2 registry 전후 대조표 (7필드) — S-12 · S-14 / AC-12 · AC-14

허브 registry: `/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/.meta/task_999.json`

| # | 필드 | before | after (hook 1회) | 기대 | 판정 |
|---|---|---|---|---|---|
| 1 | `execution_ownership.owner_session_id` | `null` | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` | 세션 ID로 채워짐 | **PASS** |
| 2 | `execution_ownership.state` | `worktree_session_owned` | `worktree_session_owned` | 유지 | **PASS** |
| 3 | `execution_ownership.generation` | `2` | `3` | 단조 증가(역행 0) | **PASS** (+1, 역행 0건) |
| 4 | `execution_ownership.failure_reason` | `null` | `null` | `null` (`hub_owned` 복귀 없음) | **PASS** |
| 5 | `launch_receipt` 4필드 | `adapter=orca` / `adapter_handle=term_216541d9-ed40-48bf-b5f1-54ee21a8f28f` / `launched_at=2026-09-19T08:39:27.966926+00:00` / `reported_cwd=<worktree_root>` | **전건 동일** | 보존 | **PASS** |
| 6 | `prompt_receipt` 2필드 | `prompt_id=451a5b33401bbc7a` / `submitted_at=2026-09-19T08:39:27.966926+00:00` | **전건 동일** | 보존 | **PASS** |
| 7 | `checkpoint_shas` | `[]` | `[]` | 현재 `[]` (W-10이 채움) | **PASS** (예상대로 미변) |

부가 관측: `adapter`·`adapter_handle`도 불변. `state`가 `hub_owned`로 복귀한 사건 0건, 고아 터미널 발생 0건.

### 2.3 registry ↔ lease 일치 (AC-12의 해소 지점)

| 저장소 | 필드 | 값 |
|---|---|---|
| 허브 registry meta | `execution_ownership.owner_session_id` | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` |
| 태스크 lease | `run/.runtime/owner.json.owner_session_id` | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` |

→ **바이트 일치. PROBE-BASELINE §5.4가 기록한 불일치가 해소됐다.**
lease는 `claim_source=state_transition`, `status=active`, `generation=1`로 유지됐다(세션이 동일하므로 소유권 이전 없음).

### 2.4 C-9 준수 — 쓰기 경로

워커는 registry meta를 **읽기만** 했다. 쓰기는 배포본 hook이 CLI를 subprocess로 경유해 1회 수행했다:

- `session_start_hook.py:115` `_register_registry_owner` → `{OPAL_HOME|~/.opal}/tools/worktree-tool/run.sh ownership-set --project-root <allocator_root> --task <N> --execution-ownership worktree_session_owned --attribution-state <prior> --owner-session-id <session_id>` (subprocess, 45초 상한)
- `--generation`을 **지정하지 않아** prior+1 단조 증가에 맡긴다(D-J) → §2.2 #3의 `2 → 3`이 이 계약과 정합.
- meta 파일 직접 편집 경로 없음 → **C-9 PASS**, dual writer 없음.

### 2.5 멱등 확인 (D-J 멱등 게이트)

같은 hook을 **1회 더** 동일 봉투로 실행:

| 항목 | RUN 1 후 | RUN 2 후 | 판정 |
|---|---|---|---|
| `generation` | `3` | **`3`** | **더 오르지 않음 — 멱등 PASS** |
| `owner_session_id` | 세션 ID | 세션 ID | 불변 |
| `state` / `failure_reason` | `worktree_session_owned` / `null` | 동일 | 불변 |
| meta 파일 mtime | `1789816929` | **`1789816929`** | **쓰기 0회** |

→ 이미 자기 세션이 owner이면 `ownership-set`을 **호출조차 하지 않는다**(`session_start_hook.py` 멱등 게이트: `return False, []` — 진단도 남기지 않음). mtime 불변이 "호출 0회"를 파일시스템 레벨에서 확증한다.
→ **H-2(세션마다 generation 증가) 완화 확인.** 재부트마다 generation이 누적 증가하지 않는다.

---

## 3. 기존 증거 회귀 확인 (AC-9 · AC-10 · AC-11 / C-8)

**재측정하지 않고 `PROBE-BASELINE.md` §5.1~§5.4를 인용한 뒤 동일 사실 유지만 대조했다.**

### 3.1 AC-9 — launcher / prompt receipt (S-9 인용)

PROBE-BASELINE §5.1 인용: `adapter=orca`, `adapter_handle=term_216541d9-...`, `launched_at=2026-09-19T08:39:27.966926+00:00`, `reported_cwd`가 `worktree_root`와 일치, `prompt_id=451a5b33401bbc7a`, `submitted_at` 동일 — **6필드 전건 존재**.

→ **수정 후에도 동일 사실 유지.** §2.2 #5·#6에서 6필드가 byte 단위로 보존됐음을 확인했다(재배포와 registry 쓰기가 receipt를 덮어쓰지 않는다). **AC-9 유지 PASS.**

### 3.2 AC-10 — 새 Orca 터미널의 워크트리 인식 (S-10 인용)

PROBE-BASELINE §5.2 인용: 세션 cwd·`git rev-parse --show-toplevel`이 `worktree_root` 일치, `ORCA_WORKTREE_ID=ce5d0068-...::/.../task_999`, 브랜치 `feat/OP-TASK-999`가 registry `branch` 일치, `.opal/task-ownership.json` 6필드가 발급값과 전건 일치.

→ **수정 후에도 동일 사실 유지.** 이번 프로브는 같은 워크트리·같은 터미널 세션에서 수행됐고 registry `branch`·`worktree_root`·`task_path`·`task_folder`는 §2.2에서 미변경이 확인됐다. 발급값 사본 경로(`worktree-locates-hub-by-issued-copy`)에 회귀 없음. **AC-10 유지 PASS.**

### 3.3 AC-11 — 초기 prompt 제출 → 단계 진행, 그리고 **결손 해소** (S-11)

PROBE-BASELINE §5.3 인용: 세션이 `state.json`을 읽어 `999 · TASK · 모드 agentic`으로 재개했고, 같은 세션에서 `mark task.task_md --done`(17:41:41)·`advance plan.plan_md`(17:44:18)가 run-log에 `state.changed`로 적재됐다. **단 그 사건들의 `actor.session_id`는 `null`** — 귀속 증거 결손(부분 만족).

**재배포 후 경로에서의 결손 해소 확인** — run-log `actor.session_id` 추이:

| `sequence` | `event` | `actor.session_id` | 비고 |
|---|---|---|---|
| 11 | `state.changed` | `4e1a2aa2-...` | (W-1 소스 경로 프로브 구간) |
| 12 | `state.changed` | **`null`** | 기준선 결손 사례 |
| 13 | `state.changed` | `4e1a2aa2-...` | 디스패치 시점 최신 |
| **14** | `state.changed` | **`4e1a2aa2-1800-43e6-af3c-60b86a27b237`** | **이번 프로브 — 재배포 후 배포본 경로** |

생성 명령(파이프라인 전진 없음 — `advance` 미사용):

```bash
env -u OPAL_SESSION_ID -u CLAUDE_CODE_SESSION_ID zsh -c '
  source <scratchpad>/probe-env-w8.sh
  ~/.opal/tools/state-tool/run.sh mark <task-folder> --task-step execute.implement --done \
    --as-worker --worker-stage EXECUTE --action-step 5/11 --note "..."'
```

**종단 상속 체인이 이 한 명령에서 모두 관측됐다:**

| 경계 | 관측 |
|---|---|
| hook이 기록한 env 파일 | `export OPAL_SESSION_ID=4e1a2aa2-...` |
| 식별자를 **제거한** 청정 쉘에서 `source` 후 | `typeset -p OPAL_SESSION_ID` → `export OPAL_SESSION_ID=4e1a2aa2-...` (**`-x` 속성 확인**) |
| 손자 프로세스 `sh -c 'echo $OPAL_SESSION_ID'` | `4e1a2aa2-...` (**봉투 값과 바이트 일치**) |
| state-tool run-log `actor.session_id` | `4e1a2aa2-...` (seq 14) |

`env -u`로 부모의 `OPAL_SESSION_ID`·`CLAUDE_CODE_SESSION_ID`를 **제거한 뒤** env 파일만으로 값을 복원했으므로, 상속이 hook의 env-file 계약에서 왔음이 분리 확인된다(C-3의 "자식 프로세스 단순 export" 반례가 아님).

`mark` 응답: `"ok": true, "row_id": 7, "stage": "EXECUTE", "status": "in_progress", "transition_action": "continue"` — `--action-step 5/11`(N<11)이므로 행이 **`in_progress` 유지**, 파이프라인 전진 없음.

→ **AC-11 결손 해소 PASS.** 기준선의 "진행은 이어졌으나 귀속 증거가 비어 있다"가 "진행과 귀속이 모두 기록된다"로 바뀌었다.

### 3.4 AC-12 — baseline 판정 인용과 대조

PROBE-BASELINE §5.4 인용 (재측정 없음):
- **(a) writer** — registry `owner_session_id`는 `worktree-tool ownership-set`만 쓴다(`worktree_tool.py:1791 cmd_ownership_set`, `:1880-1882`). lease는 `ownership_tool.lease.claim()`이 쓴다.
- **(b) 부트 이후 registry를 채우는 주체** — **존재하지 않았다.** launcher는 아직 태어나지 않은 세션 ID를 몰라 `owner_session_id=None`으로 기록하고, 부트 후 등록 경로가 어느 훅·도구에도 없었다.
- **(c) checkpoint 영향** — `worktree_tool.py:2107-2123`의 두 항(`os.environ.get("OPAL_SESSION_ID")` → `None`, `block["owner_session_id"]` → `None`)이 **각각** 실패해 `checkpoint_ownership_denied / reason=foreign_owner`가 구조적으로 불가피했다.

**수정 후 대조 — (a)는 유지, (b)·(c)의 결손은 해소:**

| baseline 판정 | 수정 후 상태 | 근거 |
|---|---|---|
| (a) writer 구분 | **동일 사실 유지** — registry는 여전히 `ownership-set` CLI 단일 writer | §2.4. hook도 meta를 직접 쓰지 않고 같은 CLI를 경유하므로 writer가 늘지 않았다 |
| (b) 부트 후 registry 등록 주체 부재 | **해소** — SessionStart hook의 `_register_registry_owner`가 그 주체다 | §2.2 #1: `null` → 세션 ID |
| (c) checkpoint 2항 차단 | **양항 모두 해소됨** | 1항: §3.3 — `OPAL_SESSION_ID`가 자식까지 상속됨 / 2항: §2.3 — `block["owner_session_id"]`가 세션 ID와 일치 |

→ **AC-12 PASS.** baseline이 판정한 불일치의 원인·영향이 그대로 유효하며, 그 원인이 제거됐음이 실측으로 확인됐다.
→ **AC-13(W-10)의 두 선행 결함이 모두 제거됐다.** 단, `checkpoint` 실호출은 이 Work item 범위 밖이며 W-10이 실증한다.

### 3.5 AC-14 — 소유권 상태 건전성

| 항목 | 결과 |
|---|---|
| `state == worktree_session_owned` | 전 구간 유지 (§2.2 #2, §2.5) |
| `generation` 역행 | **0건** (`2 → 3`, 멱등 재실행에서 `3` 유지) |
| `hub_owned` 복귀 | **없음** (`failure_reason`이 전 구간 `null`) |
| 고아 터미널 | **없음** (터미널을 새로 기동하지 않았고 `adapter_handle` 불변) |

→ **AC-14 PASS.**

---

## 4. 다른 슬롯 불변 확인 (C-8)

읽기만 수행했다.

| 슬롯 meta | mtime (before) | mtime (after) | size | sha256 (before = after) |
|---|---|---|---|---|
| `task_128.json` | `1789228001` | **`1789228001`** | 1072 | `49a4bba824202d5147cabc47d9d11b66a8816e4978a16b705739555a312195cb` |
| `task_142.json` | `1789719901` | **`1789719901`** | 1009 | `0d5bb4111452fd99605928a171c1f85fa4029c39a9718d58dd2fad62432e9515` |

→ **C-8 PASS.** 다른 슬롯의 registry는 mtime·크기·내용 해시가 모두 불변이다. 허브나 다른 슬롯의 터미널도 조작하지 않았다.
→ 이번 작업에서 변경된 허브 자산은 **태스크 999 registry 행 1건뿐**이며, 그 쓰기도 hook이 `ownership-set` CLI로 수행했다.

---

## 5. 완료 기준 판정 요약

| 기준 | 판정 | 근거 |
|---|---|---|
| AC-9 | **유지 PASS** | §3.1 — receipt 6필드 보존 |
| AC-10 | **유지 PASS** | §3.2 — 발급값·브랜치 불변 |
| AC-11 | **PASS (결손 해소)** | §3.3 — run-log seq 14 `actor.session_id` 채워짐 |
| AC-12 | **PASS** | §2.3 · §3.4 — registry ↔ lease 일치, (b)·(c) 해소 |
| AC-14 | **PASS** | §2.2 · §3.5 — state 유지, generation 역행 0, 복귀 없음 |
| C-1 | **준수** | §1.5 — install 경유만, 배포본 수기 편집 0건 |
| C-8 | **준수** | §4 — 다른 슬롯 불변 |
| C-9 | **준수** | §2.4 — 쓰기는 `ownership-set` CLI 경유만 |
| C-10 | **준수** | `main` commit·merge·push 0건. 커밋 자체를 수행하지 않았다 |
| S-12 / S-14 / S-15 / S-20 | **PASS** | §2.2 / §2.2·§2.5 / §1.4 / §1.3 |
| H-2 / H-3 / H-4 / H-5 | **완화 확인 / 회피 / 회피 / PASS** | §2.5 / §1.5 / §1.3 / §0 |

---

## 6. 후속(W-10 · W-11)을 위한 기준선 이동 인계

**이 프로브로 기준선이 이동했다. 후속 Work item은 아래 값을 새 before로 삼아야 한다.**

| 항목 | 기존 기준선 (PROBE-BASELINE) | **이동된 새 기준선** |
|---|---|---|
| registry `owner_session_id` | `null` | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` |
| registry `generation` | `2` | **`3`** |
| run-log 최신 `sequence` | `13` | **`14`** (`actor.session_id` 채워짐) |
| 배포본 `~/.opal/tools/ownership-tool/` | 구버전 | **W-1·W-6 반영본** (소스와 byte identical) |
| `dashboard/frontend/dist/` | 부재 | 부재 (재배포로 생성됐으나 **삭제 완료**) |
| `state.json` EXECUTE row 7 | — | `in_progress`, action-step 5/11 |

### W-10 (checkpoint 권한 실증)에 인계

1. **AC-13의 두 선행 결함이 모두 제거됐다** (§3.4) — `worktree_tool.py:2107-2123`의 `OPAL_SESSION_ID` 항과 `block["owner_session_id"]` 항이 모두 세션 ID로 채워진다. `checkpoint`가 `foreign_owner`로 거부될 구조적 이유는 더 이상 없다.
2. **[MUST] stage 직전에 `git status --porcelain dashboard/`와 `dashboard/frontend/dist/` 존재 여부를 한 번 더 확인하라** (H-4, S-20). 이 프로브 종료 시점에는 정리돼 있으나, W-10 사이에 재배포가 또 일어나면 재생성된다.
3. `checkpoint_shas`는 현재 `[]`다. W-10 성공 시 append되는 것이 AC-13 판정 지점이다.
4. **`generation` 경합 주의** — `checkpoint`나 `ownership-set` 경로가 `--generation`을 명시하면 현재 값 `3`을 기준으로 해야 한다. 멱등 게이트 덕에 hook 재실행으로는 더 오르지 않지만, 새 세션이 부트하면 `4`로 오른다.
5. 브랜치는 `feat/OP-TASK-999`로 registry `branch`와 일치한다(§3.2 인용). `main` commit·merge·push 금지는 유효하다(C-10).
6. 워커는 **커밋을 수행하지 않았다.** 워크트리 작업트리에는 W-1·W-6의 소스 변경 4건과 태스크 폴더가 미커밋 상태로 남아 있다 — W-10의 stage 대상이다.

### W-11 (결정론 스위트)에 인계

1. 배포본과 소스가 byte identical이므로, pytest가 배포본을 참조하더라도 소스와 동일한 코드를 검증한다.
2. `api-env-files.test.ts`는 `dist/` 부재를 요구한다 — 테스트 실행 전 `dashboard/frontend/dist/` 부재를 확인하라.
3. **S-12r(RED 증거)와의 관계**: 이 프로브는 S-12의 통합 측 PASS 증거다. S-12r의 4분기 단위 테스트(등록 성공 / 이미 자기 세션 / 타 세션 owner / state 불일치) 중 **"등록 성공"**과 **"이미 자기 세션(멱등)"** 두 분기는 이번 실측(§2.2, §2.5)에서 실경로로도 재현됐다. 나머지 2분기(`foreign_registry_owner`·`registry_not_worktree_owned`)는 실측에서 발화하지 않았으므로 단위 테스트가 유일한 증거다.

---

## 7. 이 절의 경계

- 생성한 파일: 이 문서 1건. 소스·테스트 파일 수정 0건.
- 삭제한 파일: `dashboard/frontend/dist/` (재배포 부산물, H-4 요구)
- `git commit`·`advance`·`main` 조작: **0건**
- 허브·다른 슬롯 registry·터미널 조작: **0건** (태스크 999 행만, 그것도 hook의 CLI 경유)
- `~/.claude/session-env/` 접근: **없음** (임시 env 파일만 사용)
