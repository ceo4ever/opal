# PROBE-MOCKUP.md — W-5 목업 진행 흐름 관측 (실행 그룹 P4)

- **Work item**: W-5 (실행 그룹 P4)
- **checklist_source**: `PLAN.md` W-5 행
- **scenario_source**: `TEST-SCENARIO.md` S-8 · S-8b
- **완료 기준**: AC-8 · C-5 · C-6
- **착수 근거**: W-3(AC-4) 게이트 PASS — `PROBE-STOP.md` §5 「게이트 판정: PASS」
- **판정 기록 시각**: `2026-09-19T18:33:10+0900`
- **판정**: **PASS** — S-8 시각 순서 3증거 성립, S-8b 두 경계 모두 차단 대상 아님을 코드 근거로 확인

---

## H-5 — 착수 직후 세션 식별자 3종

| 식별자 | 값 | export 여부 / 근거 |
|---|---|---|
| `CLAUDE_CODE_SESSION_ID` | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` | **export 됨** — `env` 조회 1건 |
| `OPAL_SESSION_ID` | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` | **export 안 됨** — `env` 0건, `export -p` 0건. 쉘 변수로만 존재 |
| 봉투 `session_id` | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` | W-3 봉투 원문 재사용. 3종 값 전부 동일 |

측정 시각 `2026-09-19T18:31:46+0900`. `OPAL_SESSION_ID` 미export는 W-2가 소유한 결함의 현재 상태
(`PROBE-AFTER.md` §0 P-3 「이 세션은 구 배포본으로 부팅됐으므로 baseline P-3와 동일」)와 일치하며,
이 프로브에서는 **증거 ③의 관측 방법 선택에만** 영향을 줬다(§3.2 참조). 판정을 왜곡하지 않았다.

허브 registry `execution_ownership.owner_session_id = null`은 **미기재**(W-6/AC-12 소관)이지
타 세션 owner가 아니므로 blocked 조건이 아니다 — W-2·W-3과 같은 판정을 유지한다.

---

## 1. 증거 ① — 보고 시점의 상태 뷰 (`state-tool show`)

측정 시각 `2026-09-19T18:31:53+0900`. 실행한 명령:

```
~/.opal/tools/state-tool/run.sh show <task-path>
```

| 필드 | 실측값 | 기대값 | 판정 |
|---|---|---|---|
| `transition_action` | `continue` | `continue` | **일치** |
| `report_type` | `progress_report` | `progress_report` | **일치** |
| `next_action` | `EXECUTE 작업 진행 중` | (비어 있지 않음) | **일치** |

즉 이 시점의 세션은 **단순 진행 보고 상태**이며, 응답을 끝내면 안 되는 `continue` 뷰다.
(`show`의 top-level `current_status`·`task_id`는 `null`이다 — `show` 응답 스키마가 그 2필드를
채우지 않기 때문이며, evaluator는 후보의 `state.current_status`를 별도로 읽는다. `PROBE-STOP.md` §4 덤프에서
`current_status: in_progress`로 관측됨.)

증거 파일: `…/scratchpad/w5/ev1-show.json`

## 2. 증거 ② — stop-guard receipt 갱신

receipt 경로:
`/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_999/.opal/run/.runtime/stop-guard/4e1a2aa2-1800-43e6-af3c-60b86a27b237.json`

### 2.1 기준선 (W-3이 남긴 상태, 재측정 아님)

`PROBE-STOP.md` §6이 소유한 사실 — W-3 프로브가 evaluator를 2회 호출해 이 receipt를 **처음 생성**했다.
따라서 S-8의 기준선은 0이 아니라 **2**다.

| 시점 | mtime | 내용 |
|---|---|---|
| 프로브 직전 (기준선) | `2026-09-19T18:26:37+0900` | `{"block_count": 2, "decided_at": null, "decision_kind": "block_continue", "fingerprint": null, "session_id": "4e1a2aa2-…"}` |

### 2.2 실제 Stop 봉투 1회 주입

W-3이 만든 봉투 원문(`…/scratchpad/w3/stop-envelope.json`)을 **그대로 재사용**해
`~/.claude/settings.json:87` 등록 원문과 동일한 공개 hook 진입점에 stdin으로 **1회** 주입했다.

```
"$HOME/.opal/.venv/bin/python" "$HOME/.opal/tools/ownership-tool/ownership_tool/stop_hook.py" < stop-envelope.json
```

호출 시각 `2026-09-19T18:32:07+0900`, **exit code `0`**, stderr 0바이트.

**stdout 1줄 (원문 그대로)**:

```
{"decision": "block", "reason": "OPAL Stop guard: block_continue. 판정 대상 1건 — task_id=999-260919-opds-세션상속-스톱가드-목업검증 | transition_action=continue | next_action=EXECUTE 작업 진행 중 · 이 태스크가 아직 transition_action=continue다. 응답을 끝내지 말고 이어서 진행하라."}
```

증거 ①의 `transition_action=continue`·`next_action`이 차단 사유문에 **그대로 재현**됐다
(`stop_evaluator.build_reason`, `stop_evaluator.py:112-130`). 두 증거가 같은 상태 뷰를 가리킨다.

### 2.3 갱신 후 receipt — `block_count` 전이

| 시점 | mtime | `block_count` | `decision_kind` | `fingerprint` | `decided_at` |
|---|---|---|---|---|---|
| 기준선 (W-3 소유) | `2026-09-19T18:26:37+0900` | **2** | `block_continue` | `null` | `null` |
| 이 프로브 1회 주입 후 | `2026-09-19T18:32:07+0900` | **3** | `block_continue` | `null` | `null` |

**기준선 2 → 실측 3.** 정확히 +1 — `block_count=prior_block_count + 1`(`stop_evaluator.py:269`)이
차단 경로 1회당 1 증가시키는 계약과 일치한다.

`decided_at`·`fingerprint`가 여전히 `null`인 것은 W-4/S-5가 소유한 별개 관측 축이며
(`fingerprint: null` = state view 미주입 경로), 이 프로브의 시각 기준은 **receipt 파일 mtime**을 썼다.

증거 파일: `…/scratchpad/w5/ev2-hook.stdout` · `…/scratchpad/w5/ev2-receipt.json`

## 3. 증거 ③ — receipt 갱신 **이후** 시각의 후속 도구 호출과 다음 상태 전이

### 3.1 (a) 추가 도구 호출

receipt mtime `18:32:07` **이후**인 `2026-09-19T18:32:31+0900`에 `state-tool show`를 1회 더 호출했고
`transition_action=continue`를 그대로 반환했다 — 차단 후에도 흐름이 **끊기지 않고 도구 호출이 이어졌다**.
증거 파일: `…/scratchpad/w5/ev3a-show.json`

### 3.2 (b)(c) 다음 `state.changed` 사건과 동일 세션

상태 전이는 **파이프라인을 전진시키지 않는 형태**로만 수행했다 — `mark … --action-step N/11`에서 `N<11`이면
행이 `in_progress`로 유지되면서 `state.changed`만 적재된다(`PROBE-AFTER.md` §3.1의 명령 선택 근거와 동일).
`advance`는 사용하지 않았다. W-2가 `2/11`을 썼으므로 이 프로브는 `3/11`·`4/11`을 썼다.

**두 번 적재됐다. 두 사건의 차이가 그 자체로 W-2 결함의 재현이므로 둘 다 남긴다.**

| seq | 적재 시각 (KST) | `actor.session_id` | 호출 경계 | 비고 |
|---|---|---|---|---|
| 11 | `18:20:03` | `4e1a2aa2-…b237` | W-2, 부모 경계 export 경유 | 기존 (`PROBE-AFTER.md` §3.3) |
| 12 | `18:32:32` | **`null`** | 이 프로브, **워커 Bash 기본 경계** (`--action-step 3/11`) | ↓ |
| 13 | `18:33:10` | **`4e1a2aa2-…b237`** | 이 프로브, **부모 경계 export 경유** (`--action-step 4/11`) | 증거 ③ 채택 |

seq 12의 `mark`는 상태 전이 자체는 성공(`"ok": true`, `status: in_progress`)했으나 경고 1줄을 함께 냈다:

```
{"warning": "ownership_session_id_missing", "message": "OPAL_SESSION_ID가 없어 task lease를 claim하지 않았습니다. 상태 전이는 그대로 진행됩니다."}
```

이는 H-5가 기록한 **`OPAL_SESSION_ID` 미export**(W-2 소유 결함)의 직접 귀결이다 — 워커 Bash의 쉘 변수는
`state-tool` subprocess로 상속되지 않는다. 따라서 증거 ③(c)의 「②와 같은 세션」을 보이려면
**W-2가 이미 검증·문서화한 부모 경계 env 파일 경로**를 그대로 써야 한다. seq 13이 그것이다:

```
env -u OPAL_SESSION_ID /bin/zsh -f -c '
  source {scratchpad}/w2/env-preamble.sh
  cd /Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_999
  ~/.opal/tools/state-tool/run.sh mark tasks/999-… \
    --task-step execute.implement --done --as-worker --worker-stage EXECUTE \
    --action-step 4/11 --note "W-5 목업 흐름 관측(PROBE-MOCKUP) — 부모 경계 export 경유 후속 전이"
'
```

`env-preamble.sh`는 W-2가 SessionStart 경로에서 실제로 생성시킨 파일(내용 1줄:
`export OPAL_SESSION_ID=4e1a2aa2-1800-43e6-af3c-60b86a27b237`)이며, 이 프로브가 값을 지어내지 않았다.
C-3 준수 — hook 자식 프로세스 안의 `export`가 아니라 **부모 쉘이 `source`하는 경계**다.

seq 13 적재 결과 (`--action-step 4/11`, 행 상태 `in_progress` 유지 · 파이프라인 비전진 확인):

| 필드 | 값 |
|---|---|
| `sequence` | `13` |
| `event` | `state.changed` |
| `timestamp` | `2026-09-19T09:33:10.804Z` (= `18:33:10+0900`) |
| `stage` / `task_step` | `EXECUTE` / `execute.implement` |
| `summary` | `mark: in_progress → in_progress` |
| **`actor.session_id`** | **`4e1a2aa2-1800-43e6-af3c-60b86a27b237`** |

`run/.runtime/owner.json` 대조 — `claim_source: state_transition`,
`owner_session_id: 4e1a2aa2-…b237`, `heartbeat_at: 2026-09-19T18:32:34+09:00`(갱신됨), `status: active`.
즉 **증거 ②의 봉투 `session_id` == 증거 ③의 `actor.session_id` == lease `owner_session_id`** 로 3자 일치한다.

증거 파일: `…/scratchpad/w5/ev3b-mark.json` · `…/scratchpad/w5/ev3c-mark.json`

## 4. S-8 시각 순서 표 (AC-8 핵심)

| 순서 | 증거 | 실제 시각 (KST) | 관측값 |
|---|---|---|---|
| — | H-5 세션 3종 | `18:31:46` | 3종 전부 `4e1a2aa2-…b237` |
| **①** | `state-tool show` | **`18:31:53`** | `transition_action=continue` · `report_type=progress_report` · `next_action=EXECUTE 작업 진행 중` |
| **②** | stop-guard receipt 갱신 (실 Stop 봉투 1회 주입) | **`18:32:07`** | `block_count` **2 → 3**, `decision_kind=block_continue`, hook stdout = 차단 1줄 |
| **③a** | 추가 도구 호출 (`state-tool show`) | **`18:32:31`** | `transition_action=continue` (흐름 계속) |
| ③b | (참고) 기본 Bash 경계 전이 seq 12 | `18:32:32` | `state.changed` 적재, `actor.session_id=null` + `ownership_session_id_missing` |
| **③c** | 다음 `state.changed` seq 13 | **`18:33:10`** | `actor.session_id=4e1a2aa2-…b237` — **②와 동일 세션** |

**① `18:31:53` < ② `18:32:07` < ③ `18:32:31` / `18:33:10`** — 엄격 증가. 시각 순서 성립.

**S-8 판정: PASS.** 단순 진행 보고(`continue`) → Stop 차단(`block_continue`, `block_count` +1) →
추가 도구 호출 → 다음 상태 전이(동일 세션)까지 **파일 증거 3종으로** 이어짐이 확인됐다.
자기 진술이 아니라 `state-tool show` JSON · receipt 파일 mtime·내용 · run-log JSONL 3종으로 입증했다.

---

## 5. S-8b — `await_user` 경계와 CLOSE 진입 게이트

### 5.1 `await_user`는 Stop 차단 대상이 아니다 (코드 근거)

`stop_evaluator`는 후보의 `current_status`에서 `transition_action`을 파생한 뒤
그것을 `decision_kind`로 사상(寫像)한다 — 두 단계 모두 폐쇄 dict다.

| 근거 | 경로:줄번호 | 내용 |
|---|---|---|
| 상태 → 전이 파생 | `opal/tools/ownership-tool/ownership_tool/stop_evaluator.py:31-36` | `_STATUS_TRANSITION = {"in_progress": "continue", "blocked": "await_user", "completed": "complete", "done": "complete"}` |
| 전이 → 판정 사상 | 같은 파일 `:39-43` | `_TRANSITION_DECISION = {"continue": "block_continue", "await_user": "allow_await_user", "complete": "allow_complete"}` |
| 비차단 조기 반환 | 같은 파일 `:263-265` | `if kind != "block_continue": return _finish(kind, …)` — `block_count` 인자 **없이** 반환 |
| 차단 경로 | 같은 파일 `:266-269` | `block_continue`일 때만 `reason=build_reason(...)`, `block_count=prior_block_count + 1` |
| 파생 함수 | 같은 파일 `:106-108` | `_candidate_transition()` → `_STATUS_TRANSITION.get(state.get("current_status"))` |

즉 `current_status=blocked`(사용자 결정 대기) → `await_user` → **`allow_await_user`**이고,
종료 상태(`completed`/`done`) → `complete` → **`allow_complete`**다. 두 경로 모두 `:263`의 조기 반환으로
빠져나가므로 (a) `reason`(차단 사유문)이 붙지 않고 (b) `block_count`가 증가하지 않는다.
**강제 후보(`forced`)가 서 있어도 마찬가지다** — `:244-248`에서 후보를 골라 `transition`을 파생하는 것과
`:262`에서 `kind`를 결정하는 것은 별개 단계이며, 강제 후보 자격은 차단 여부를 결정하지 않는다.
이 프로브가 실측한 `block_continue` 경로(증거 ②)는 `current_status=in_progress`였기 때문이다
(`PROBE-STOP.md` §4 덤프의 `state.current_status: "in_progress"`).

`_STATUS_TRANSITION`의 주석(`:29-30`) 「resolver가 후보로 세우는 상태는 `in_progress`·`blocked` 2종뿐이므로
그 2종과 종료 상태만 다룬다」가 이 폐쇄성을 명시한다. `await_user`를 `block_continue`로 보내는 경로는
파일 전체에 **존재하지 않는다**.

### 5.2 CLOSE 진입 게이트는 별도 축이다 (코드 근거)

| 근거 | 경로:줄번호 | 내용 |
|---|---|---|
| 게이트 함수 | `opal/tools/state-tool/state_tool.py:2383-2404` | `check_close_gate(state, row_index, command, auto_pass, force, owner)` — `row["stage"] != "CLOSE"`면 즉시 반환, CLOSE 첫 행일 때만 검사 |
| 거부 지점 | 같은 파일 `:2403-2404` | `if auto_pass and state.get("mode") in ("agentic", "semi-agentic"): err(command, "agentic_close_gate_requires_user", …)` |
| 오류 enum 등록 | 같은 파일 `:198`, `:385` | `"agentic_close_gate_requires_user": "agentic/semi-agentic 모드 CLOSE 첫 행에 --auto-pass 사용 불가 (§2.16 G-13)"` |
| 계약 문서 | `opal/tools/state-tool/README.md:154`, `:604` | 오류 코드 15번 — `mark` 전용, exit 1 |

**교차 참조 0건 확인** — `stop_evaluator.py`에서 `close_gate`·`CLOSE` 토큰 **0건**.
즉 CLOSE 진입 게이트는 **`state-tool mark`가 소유하는 별도 축**이고, Stop 가드는 이를 읽지도 집행하지도 않는다.
두 축은 서로 독립이며, CLOSE 진입에 사용자 발화를 요구하는 기존 계약은 이 태스크의 Stop 가드 변경과 무관하게 보존된다.

**실제로 CLOSE 행을 `mark`하지 않았다** — 지시대로 코드·문서 근거로만 확인했다(비가역 전이 회피).

### 5.3 S-8b 대조표

| 경계 | 기대 | 코드 근거 | 판정 |
|---|---|---|---|
| `await_user` (사용자 결정 대기) | 차단 대상 아님 · 기존 계약대로 사용자 발화 요구 | `stop_evaluator.py:33` → `:41` → `:263-265` | **충족** |
| 종료 상태 (`completed`/`done`) | 차단 대상 아님 | `stop_evaluator.py:34-35` → `:42` → `:263-265` | **충족** |
| CLOSE 진입 게이트 | Stop 가드와 별개 축 · `state-tool`이 `agentic_close_gate_requires_user`로 거부 | `state_tool.py:2383-2404` · stop_evaluator 교차참조 0건 | **충족** |

**S-8b 판정: PASS.**

---

## 6. C-6 준수 — PM 활동은 관측 전용

- 이 프로브는 **`log-event`를 1회도 호출하지 않았고**, PM activity 사건을 Stop 집행 판정의 입력으로 쓰지 않았다.
- 코드 확인: `stop_evaluator.py`에 `log-event`/`log_event`/`pm_activity`/`activity` 토큰 **0건**,
  `transcript` 토큰 **0건**. evaluator에 신규 입력을 연결하지 않았다(코드 무변경).
- 이 프로브가 남긴 run-log 사건 2건(seq 12·13)은 모두 `event: state.changed` · `actor.kind: tool` ·
  `actor.id: state-tool`인 **상태 전이 사건**이며 PM activity 사건이 아니다. 성격 구분:
  - **progress**(진행) — seq 12·13의 `data.note`가 프로브 진행을 기술. 판정 입력 아님.
  - **decision**(결정) — 이 프로브에서 적재한 결정 사건 **0건**.
- 증거 ②의 hook 호출은 `show_json`·`prior_receipt`·lease를 주입하지 않은 공개 진입점 1회뿐이다(C-4 유지).

## 7. 부수효과와 제약 준수

| 항목 | 실측 | 판정 |
|---|---|---|
| C-1 (`~/.opal/` 쓰기·재배포) | 0건. `~/.opal/` 아래는 인터프리터·hook·state-tool **실행**만 | 준수 |
| C-5 (태스크 999 전용 자산) | 건드린 쓰기 대상: 태스크 999 폴더(`state.json`·run-log·`run/.runtime/owner.json`), 워크트리 `.opal/run/.runtime/stop-guard/` receipt, 스크래치패드. 다른 슬롯·허브 registry는 **읽기 0건** | 준수 |
| C-6 | §6 참조 | 준수 |
| 소스·테스트 수정 | `git status` = 기존 2건(`session_start_hook.py`·`test_session_start.py`, 타 워커 소유 — **읽지도 않음**) + 미추적 태스크 폴더. **새 소스 변경 0건** | 준수 |
| 커밋 | 0건 | 준수 |
| 파이프라인 전진 | `--action-step 3/11`·`4/11` (둘 다 `N<11`). `advance` 0회. 행 상태 `in_progress` 유지 | 준수 |

**후속 Work item 주의 — 기준선 이동**:

- stop-guard receipt `block_count`는 이 프로브로 **2 → 3**이 됐다. W-4/S-5 등 후속 프로브는
  **기준선 3**에서 출발한다. `fingerprint`·`decided_at`은 여전히 `null`로 변하지 않았다.
- run-log 최신 `sequence`는 **11 → 13**이 됐다. seq 12는 `actor.session_id=null`,
  seq 13은 채워짐 — 후속 프로브가 「최신 사건」을 읽을 때 seq 13을 봐야 한다.
- `state.json`의 `execute.implement` 행 `step`은 **`2/11` → `4/11`**로 갱신됐다(행 status는 불변).

## 8. 증거 파일 목록

경로 접두: `/private/tmp/claude-501/-Volumes-Data-AIStudio-workspace-ai-framework--opal-worktrees-task-999/4e1a2aa2-1800-43e6-af3c-60b86a27b237/scratchpad`

| 증거 | 파일 |
|---|---|
| ① `state-tool show` | `w5/ev1-show.json` |
| ② hook stdout / stderr | `w5/ev2-hook.stdout` · `w5/ev2-hook.stderr` (0바이트) |
| ② receipt 사본 | `w5/ev2-receipt.json` |
| ② 주입 봉투 (W-3 원문 재사용) | `w3/stop-envelope.json` |
| ③a 추가 도구 호출 | `w5/ev3a-show.json` |
| ③b 기본 경계 전이 (seq 12) | `w5/ev3b-mark.json` |
| ③c 부모 경계 전이 (seq 13) | `w5/ev3c-mark.json` |
| ③ 부모 경계 env 파일 (W-2 산출) | `w2/env-preamble.sh` |

실 파일 원천(태스크 999 자산):

- run-log — `tasks/999-…/run/run-log-run_7601ab94-d859-4379-82fa-9a8ebe1c4311-0001.jsonl`
- lease — `tasks/999-…/run/.runtime/owner.json`
- receipt — `.opal/run/.runtime/stop-guard/4e1a2aa2-1800-43e6-af3c-60b86a27b237.json`

---

## 9. 완료 기준 대조

| 기준 | 근거 | 판정 |
|---|---|---|
| AC-8 전단 (목업 흐름이 추가 도구 호출·다음 전이까지 이어짐) | §4 시각 순서 표 — ①`18:31:53` < ②`18:32:07` < ③`18:32:31`/`18:33:10`, 동일 세션 | **충족** |
| AC-8 후단 (사용자 결정 경계·CLOSE 게이트 기존 계약 유지) | §5.1 `stop_evaluator.py:33,41,263-265` · §5.2 `state_tool.py:2383-2404` + 교차참조 0건 | **충족** |
| C-5 | §7 — 태스크 999 자산만 사용 | **준수** |
| C-6 | §6 — `log-event` 0회, evaluator 신규 입력 0건, 코드 무변경 | **준수** |

**W-5 판정: PASS.** 미달 항목 없음.
