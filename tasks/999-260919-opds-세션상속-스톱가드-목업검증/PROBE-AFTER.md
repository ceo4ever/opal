# PROBE-AFTER — W-1 반영 후 세션 상속·승격 실측 (W-2 / AC-1·AC-2·AC-3·C-1)

> 측정 시각: 2026-09-19 18:19~18:20 KST
> 측정 세션: 워크트리 전용 agentic 세션의 워커 경계 (`ORCA_WORKTREE_ID` = `ce5d0068-fabe-451d-b68d-5604d6495c34::.../task_999`)
> 측정 위치: `/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_999`
> 측정 방법: **워크트리 소스 경로**의 hook 진입점 + 실제 SessionStart 봉투 + 임시 `CLAUDE_ENV_FILE`. 공개 CLI만 사용, 테스트 내부 주입 0건
> 재배포: **수행하지 않음(D-O)**. `scripts/install-mac.sh` 0회, `~/.opal/` 쓰기 0건
> before 값 출처: `PROBE-BASELINE.md` §1 (P-1~P-10) — **재측정하지 않고 인용**

---

## 0. 세션 식별자 3종 선기록 (H-5 / S-21)

| 식별자 | 값 | 출처·비고 |
|---|---|---|
| `CLAUDE_CODE_SESSION_ID` | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` | 워커 Bash 경계 `echo` |
| `OPAL_SESSION_ID` | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` | 워커 Bash 경계 `echo`. **export 여부: 미export** (`typeset OPAL_SESSION_ID=...`, `-x` 없음) — 이 세션은 **구 배포본**으로 부팅됐으므로 baseline P-3와 동일. §4 주의 참조 |
| 주입한 봉투 `session_id` | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` | `session-start-envelope.json` |

**H-5 판정: PASS.** 3종이 전건 동일하고 `PROBE-BASELINE.md` §1 P-1과도 일치한다.

허브 registry `/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/.meta/task_999.json` 의
`execution_ownership.owner_session_id` = `null` — **타 세션 owner가 아니라 미기재(결손)**다. 이 결손은
AC-12/W-6이 닫을 대상이며(부트 시점 registry 등록 경로 미구현), 관측 세션과 PM 세션의 **불일치 증거가 아니다**.
따라서 S-21의 `blocked` 조건(불일치)에 해당하지 않아 진행했다. registry는 읽기만 했고 쓰지 않았다.

---

## 1. before/after 대조 (P-1 ~ P-10)

before = `PROBE-BASELINE.md` §1 인용. after = 이번 프로브 실측.

| # | 관측 지점 | before (baseline §1) | after (이번 프로브) | 판정 |
|---|---|---|---|---|
| P-1 | 부모 세션 ID (`CLAUDE_CODE_SESSION_ID`) | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` / 존재 | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` / 존재 | 불변 |
| P-2 | 쉘 변수 `OPAL_SESSION_ID` (`echo`) | `4e1a2aa2-...` / 존재 | `4e1a2aa2-...` / 존재 | 불변 |
| P-3 | **export 여부** (`typeset -p OPAL_SESSION_ID`) | `typeset OPAL_SESSION_ID=...` — `-x` 없음 / **미export** | `export OPAL_SESSION_ID=4e1a2aa2-1800-43e6-af3c-60b86a27b237` / `typeset -x` 목록에 등재 | **해소 — export됨** |
| P-4 | 자식 프로세스 상속 (`sh -c 'echo $OPAL_SESSION_ID'`) | `unset` / **상속 실패** | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` / 봉투 `session_id`와 **바이트 일치** | **해소 — 상속됨** |
| P-5 | venv python에서 `OPAL_SESSION_ID` 소비 (`_current_session_id()` 상당) | `None` / **상속 실패** | `'4e1a2aa2-1800-43e6-af3c-60b86a27b237'` | **해소** |
| P-6 | `state-tool` 전이 stderr | `{"warning":"ownership_session_id_missing", ...}` / **claim 미수행** | stderr **0바이트**, `ownership_session_id_missing` 0건, exit 0 | **해소 — claim 수행** |
| P-7 | run-log `actor.session_id` | `null` (`run.started`·`state.changed`) / **미기록** | seq 1~10 = `null`(과거 사건 불변), **seq 11 = `4e1a2aa2-1800-43e6-af3c-60b86a27b237`** | **해소 — 기록됨** |
| P-8 | `run/.runtime/owner.json` `claim_source` | `session_start` (17:39:29 claim, 이후 heartbeat만) / **승격 안 됨** | **`state_transition`** | **해소 — 승격됨** |
| P-9 | `owner.json.owner_session_id` | `4e1a2aa2-...` / 존재 | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` / 존재 | 불변 |
| P-10 | `CLAUDE_ENV_FILE` (Bash 경계) | unset / 어댑터 경계에서만 존재 | unset (워커 Bash 경계). 프로브는 임시 파일을 명시 주입 — 플랫폼 소유 `~/.claude/session-env/` **읽기·쓰기 0건** | 불변(설계대로) |

---

## 2. ③ 부모 경계 재현 — 실행 명령과 원문 출력 (S-2 / AC-2 / C-3)

### 2.1 주입한 실제 SessionStart 봉투

`{scratchpad}/w2/session-start-envelope.json` (fixture `tests/fixtures/hook-payloads/session-start.json`의 필드 집합을 따르되 합성 값 대신 **실제 값** 사용)

```json
{
  "session_id": "4e1a2aa2-1800-43e6-af3c-60b86a27b237",
  "transcript_path": "/Users/iskang/.claude/projects/-Volumes-Data-AIStudio-workspace-ai-framework--opal-worktrees-task-999/4e1a2aa2-1800-43e6-af3c-60b86a27b237.jsonl",
  "cwd": "/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_999",
  "hook_event_name": "SessionStart",
  "source": "startup"
}
```

### 2.2 hook 실행 — **워크트리 소스 경로** (D-O)

```
CLAUDE_ENV_FILE="{scratchpad}/w2/env-preamble.sh" \
  ~/.opal/.venv/bin/python \
  opal/tools/ownership-tool/ownership_tool/session_start_hook.py \
  < {scratchpad}/w2/session-start-envelope.json
```

- exit = `0`, stdout 없음(hook 계약대로)
- 실행 스크립트가 워크트리 소스임은 §5 재배포 비수행 증거로 교차 확인된다.

### 2.3 기록된 줄 — `export ` 접두 확인 (③.3)

```
$ cat {scratchpad}/w2/env-preamble.sh
export OPAL_SESSION_ID=4e1a2aa2-1800-43e6-af3c-60b86a27b237

$ od -c {scratchpad}/w2/env-preamble.sh
0000000    e   x   p   o   r   t       O   P   A   L   _   S   E   S   S
0000020    I   O   N   _   I   D   =   4   e   1   a   2   a   a   2   -
0000040    1   8   0   0   -   4   3   e   6   -   a   f   3   c   -   6
0000060    0   b   8   6   a   2   7   b   2   3   7  \n
0000074

$ wc -l < {scratchpad}/w2/env-preamble.sh
1
$ head -1 ... | grep -c '^export OPAL_SESSION_ID='
1
```

**판정: PASS.** 정확히 1줄, `export ` 접두 보유, 값에 셸 메타문자가 없어 `shlex.quote`가 quoting을 생략한 형태.

### 2.4 새 쉘에서 `source` 후 export 속성 확인 (③.4)

```
$ env -u OPAL_SESSION_ID -u CLAUDE_CODE_SESSION_ID /bin/zsh -f -c '
    source {scratchpad}/w2/env-preamble.sh
    typeset -p OPAL_SESSION_ID
    typeset -x | grep "^OPAL_SESSION_ID"
  '
```

원문 출력:

```
-- typeset -p --
export OPAL_SESSION_ID=4e1a2aa2-1800-43e6-af3c-60b86a27b237
-- is it in exported list? --
OPAL_SESSION_ID=4e1a2aa2-1800-43e6-af3c-60b86a27b237
exported_grep_rc=0
```

**판정: PASS.** zsh의 `typeset -p`는 export 속성을 가진 파라미터를 `export NAME=value` 형태로 출력한다
(baseline P-3의 `typeset OPAL_SESSION_ID=...`와 대비되는 형태). `typeset -x`(export 전용 목록) 조회에서도
`OPAL_SESSION_ID`가 등재돼 `-x` 속성이 독립 증거로 확인된다. `env -u`로 부모 값을 제거한 쉘이라
`source` 이외의 경로로 값이 들어올 여지가 없다.

### 2.5 자식 프로세스 바이트 일치 — H-1 판정 (③.4, ③.5)

```
$ sh -c 'printf %s "$OPAL_SESSION_ID"' > {scratchpad}/w2/child-value.txt   # 위 source된 쉘 내부
```

바이트 비교 결과:

```
envelope bytes : b'4e1a2aa2-1800-43e6-af3c-60b86a27b237'
child bytes    : b'4e1a2aa2-1800-43e6-af3c-60b86a27b237'
byte_equal     : True
```

같은 쉘의 venv python 소비:

```
$ ~/.opal/.venv/bin/python -c "import os;print(repr(os.environ.get('OPAL_SESSION_ID')))"
'4e1a2aa2-1800-43e6-af3c-60b86a27b237'
```

**H-1 판정: PASS (revert 불필요).** 자식 프로세스 값이 봉투 `session_id`와 바이트 일치하므로
중단 조건에 해당하지 않는다. revert 대상 여부의 최종 판정은 PM 소유다.

---

## 3. ④ 승격 실측 (S-3 / AC-3)

### 3.1 실행한 전이 1회 — 파이프라인 비전진

```
$ env -u OPAL_SESSION_ID /bin/zsh -f -c '
    source {scratchpad}/w2/env-preamble.sh
    cd /Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_999
    ~/.opal/tools/state-tool/run.sh mark tasks/999-260919-opds-세션상속-스톱가드-목업검증 \
      --task-step execute.implement --done --as-worker --worker-stage EXECUTE \
      --action-step 2/11 --note "W-2 세션 상속 실측 프로브(PROBE-AFTER)"
  '
```

**명령 선택 근거** — `advance`는 이 행이 이미 `in_progress`라 `row_not_found`로 거부되어 run-log 사건을
만들지 못한다(`state_tool.py` `cmd_advance`의 `row["status"] not in ("pending",)` 가드). 반면
`mark --action-step N/M`은 `N<M`에서 행을 `in_progress`로 **유지**하면서(`cmd_mark`의 부분 Step 분기)
`state.changed` 사건을 적재하므로, **파이프라인 행을 전진시키지 않고** `actor.session_id` 기록을 관측할 수 있다.
이 호출은 `execute-guide.md` §5 「상태 기록」이 워커에게 지시하는 바로 그 명령이며 W-2(11개 Work item 중 2번째)
진행 기록을 겸한다. `_claim_task_lease_if_needed()`는 두 명령 모두 `load_state_json()` 직후 동일 경계에서 호출된다.

실행 결과 — 행 상태 불변 확인:

```
{"ok": true, "command": "mark", "row_id": 7, "stage": "EXECUTE", "item": "작업",
 "status": "in_progress", "timestamp": "2026-09-19 18:20:03", "owner": "PM",
 "auto_approved": [], "run_log": {"status": "active", "pending": 0,
 "active_run_id": "run_7601ab94-d859-4379-82fa-9a8ebe1c4311"},
 "transition_action": "continue", "report_type": "progress_report", ...}
```

행 7 `EXECUTE / 작업` = `🔄 in_progress` → `🔄 in_progress` (전진 0). exit 0.

### 3.2 stderr 경고 (⑦)

| 항목 | 값 |
|---|---|
| stderr 바이트 수 | `0` |
| `ownership_session_id_missing` 출현 | `0`건 |

**판정: PASS.** baseline P-6의 경고가 사라졌다.

### 3.3 run-log `actor.session_id` (⑧)

최신 사건 (`run/run-log-run_7601ab94-d859-4379-82fa-9a8ebe1c4311-0001.jsonl`):

| 필드 | 값 |
|---|---|
| `sequence` | `11` |
| `event` | `state.changed` |
| `timestamp` | `2026-09-19T09:20:03.143Z` |
| `task_step` | `execute.implement` |
| `summary` | `mark: in_progress → in_progress` |
| `actor` | `{"kind":"tool","id":"state-tool","provider":null,"session_id":"4e1a2aa2-1800-43e6-af3c-60b86a27b237"}` |
| **`actor.session_id`** | **`4e1a2aa2-1800-43e6-af3c-60b86a27b237`** |

run 전체 대조 (before 구간이 그대로 보존됨을 함께 확인):

| sequence | event | `actor.session_id` |
|---|---|---|
| 1 | `run.started` | `null` (before) |
| 2 ~ 10 | `state.changed` ×9 | `null` (before) |
| **11** | `state.changed` | **`4e1a2aa2-1800-43e6-af3c-60b86a27b237`** (after) |

**판정: PASS.** 기존 사건은 재작성되지 않았고, 수정 후 첫 전이부터 세션 ID가 채워진다(S-11 후반부 충족).

### 3.4 `run/.runtime/owner.json` 4필드 (⑨)

```json
{
  "claim_source": "state_transition",
  "claimed_at": "2026-09-19T17:39:29.025782+09:00",
  "generation": 1,
  "heartbeat_at": "2026-09-19T18:20:03.385796+09:00",
  "lease_expires_at": "2026-09-19T22:20:03.385796+09:00",
  "owner_session_id": "4e1a2aa2-1800-43e6-af3c-60b86a27b237",
  "status": "active",
  "task_path": ".../tasks/999-260919-opds-세션상속-스톱가드-목업검증",
  "ttl_sec": 14400
}
```

| 필드 | 값 |
|---|---|
| `owner_session_id` | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` |
| `claim_source` | `state_transition` |
| `generation` | `1` |
| `claimed_at` | `2026-09-19T17:39:29.025782+09:00` |

**AC-3 핵심 대조**: run-log `actor.session_id` == `owner.json.owner_session_id` ==
`4e1a2aa2-1800-43e6-af3c-60b86a27b237` — **동일하고 비어 있지 않다.** `claim_source = state_transition`.

---

## 4. S-3i — lease 불변식 대조 (⑩)

before 출처: `PROBE-BASELINE.md` §1 P-8(`session_start`, 17:39:29 claim) · P-9(`owner_session_id`).

| 필드 | before | after | 기대 | 판정 |
|---|---|---|---|---|
| `generation` | `1` | `1` | 불변 | **PASS** |
| `claimed_at` | `2026-09-19T17:39:29.025782+09:00` (P-8의 "17:39:29 claim") | `2026-09-19T17:39:29.025782+09:00` | 불변 | **PASS** |
| `owner_session_id` | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` (P-9) | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` | 불변 | **PASS** |
| `claim_source` | `session_start` | `state_transition` | 승격만 | **PASS** |

**강등 0건 · 재생성 0건 · generation 역행 0건.** 3필드 불변 + `claim_source` 단방향 승격이라는
S-3i 기대가 전건 충족된다.

**중간 관측 (승격 시점 분리 증거)** — hook 실행 직후·`state-tool` 실행 직전의 `owner.json`:

```json
{"claim_source": "session_start", "claimed_at": "2026-09-19T17:39:29.025782+09:00",
 "generation": 1, "heartbeat_at": "2026-09-19T18:19:34.636275+09:00",
 "owner_session_id": "4e1a2aa2-1800-43e6-af3c-60b86a27b237", ...}
```

즉 hook의 재-claim은 같은 세션 멱등(heartbeat만 갱신, `generation`·`claimed_at` 불변)이었고,
`state_transition` 승격은 **오직 `state-tool` 전이 경계에서** 일어났다. 두 경계가 분리 관측된다.

---

## 5. 경계 준수 증거 (C-1 / D-O / C-5)

| 항목 | 증거 | 판정 |
|---|---|---|
| `install-mac.sh` 실행 | 0회 | 준수 |
| `~/.opal/` 쓰기 | 0건. 배포본 `~/.opal/tools/ownership-tool/ownership_tool/session_start_hook.py:94`는 여전히 `handle.write("{}={}\n".format(...))` — **`export` 접두 없음(구 버전 그대로)** | 준수 (D-O) |
| 프로브가 쓴 파일 | 스크래치패드 임시 파일 3건(`session-start-envelope.json`·`env-preamble.sh`·`child-value.txt`)뿐 | 준수 |
| `~/.claude/session-env/` | 읽기·쓰기 0건 (디렉터리 존재 확인 외 접근 없음) | 준수 |
| 소스 코드 수정 | 0건. `git status --porcelain` = `M session_start_hook.py` · `M test_session_start.py`(둘 다 **W-1 산출물**) · `?? tasks/999-.../` | 준수 (C-2) |
| 테스트 파일 편집 | 0건 (RED 동결 유지) | 준수 |
| 커밋 | 0건 | 준수 |
| 타 태스크 자산 | `.meta/task_128.json`(mtime 9/13 00:46) · `.meta/task_142.json`(mtime 9/18 17:25) 불변. 허브 registry `task_999.json`은 **읽기만**(mtime 9/19 17:39 불변) | 준수 (C-5) |
| 테스트 내부 주입 | `show_json`·lease 직접 주입·`monkeypatch`·`unittest.mock` 0건. 공개 hook 진입점 + 공개 CLI만 사용 | 준수 (C-4) |

**이 프로브가 검증한 대상은 워크트리 소스다.** 배포본은 구 버전이므로, 실세션 종단 확인(S-3b)은
소유자 승인 후 재배포 경계에서 별도로 남아 있다. 이는 D-O가 의도한 분리다.

---

## 6. 완료 기준 판정

| 기준 | 근거 | 판정 |
|---|---|---|
| AC-1 (세션 식별자 전 구간 동일성 실증) | §1 P-1~P-9 after 전건, §3.4 run-log == owner.json == 봉투 `session_id` | **충족** (배포본 경유 실세션 재현은 S-3b에 잔여) |
| AC-2 (부모 경계 export·상속) | §2.3 `export ` 접두, §2.4 `-x` 속성 2종 증거, §2.5 바이트 일치 `True` | **충족** |
| AC-3 (lease 승격·run-log 기록) | §3.2 경고 0건, §3.3 `actor.session_id` 기록, §3.4 `claim_source=state_transition`, §4 S-3i 4필드 전건 | **충족** |
| C-1 (배포본 직접 수정 금지) | §5 — `~/.opal/` 쓰기 0건, 소스 수정 0건 | **준수** |
| C-3 (hook 자식 프로세스 export를 해결로 인정 금지) | 변경 효과는 **부모 쉘이 `source`하는 프리앰블 파일 내용**에서만 관측됐고, hook 자신의 `os.environ` 수정은 0건 | **준수** |
| C-4 (공개 CLI·실제 봉투) | §5 테스트 내부 주입 0건 | **준수** |
| C-5 (태스크 999 전용 자산) | §5 타 태스크 자산 불변 | **준수** |
| H-1 (바이트 불일치 시 중단) | §2.5 `byte_equal = True` | **중단 조건 미해당** |
| H-5 (식별자 3종 선기록) | §0 | **충족** |

**S-2 · S-3 · S-3i 전건 PASS.** W-3(P3, 실제 Stop 봉투 evaluator 프로브) 게이트 진입 조건이 열린다.

## 잔여 항목 (W-2 범위 밖, PM 판단)

- **S-3b** — 소유자 승인 후 재배포하고 **진짜 새 Orca 워크트리 세션**에서 §2.4·§3을 재현해야 실세션 종단이 닫힌다.
  현재 세션은 구 배포본으로 부팅돼 Bash 경계 `OPAL_SESSION_ID`가 여전히 미export다(§0). 이는 W-1 미반영 배포본의
  예상된 상태이며 W-1 수정의 결함이 아니다.
- **registry `owner_session_id = null`** — AC-12/W-6이 닫을 결손. W-2에서는 읽기만 했다.
