# PROBE-STOP.md — W-3 실제 Stop 봉투 hook 진입점 프로브 (P3 게이트)

- **Work item**: W-3 (실행 그룹 P3, 게이트)
- **checklist_source**: `PLAN.md` W-3 행 + `Decisions and contracts` D-F · D-G
- **scenario_source**: `TEST-SCENARIO.md` S-4 · S-4n
- **완료 기준**: AC-4 · C-4
- **판정 기록 시각**: `2026-09-19T18:27:34+0900` (S-16 대조 원천)
- **게이트 판정**: **PASS** — 기대 3값 전건 일치. P4 이후가 열린다.

---

## H-5 — 착수 직후 세션 식별자 3종

| 식별자 | 값 | 비고 |
|---|---|---|
| `CLAUDE_CODE_SESSION_ID` | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` | **export 됨** (`export -p`에 존재) |
| `OPAL_SESSION_ID` | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` | **export 안 됨** — 쉘 변수로만 존재. `env`에 0건, `export -p`에 0건 |
| 봉투 `session_id` | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` | 3종 값 전부 동일 |

- `OPAL_SESSION_ID` 미export는 W-2가 소유한 export 결함의 현재 상태와 일치한다. 이 프로브에서 이 결함은 **판정에 영향을 주지 않았다** — D-G대로 `resolve_session_id`가 ③ 봉투 경로로 같은 값을 얻었고, evaluator `evidence.session_id`가 세 식별자와 동일하게 해석됐다.
- 허브 registry(`/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/.meta/task_999.json`)의 `execution_ownership.owner_session_id`는 **`null`**, `state`는 `worktree_session_owned`, `generation` 2다. 타 세션 owner가 아니라 **미기재**이므로 blocked 조건이 아니다 — W-2와 같은 판정을 유지한다. (W-6/AC-12가 닫을 결손)

---

## 1. 실제 Stop 봉투

`opal/tools/ownership-tool/tests/fixtures/hook-payloads/stop.json` 스키마의 5필드를 실값으로 채웠다.

**봉투 원문 파일**: `/private/tmp/claude-501/-Volumes-Data-AIStudio-workspace-ai-framework--opal-worktrees-task-999/4e1a2aa2-1800-43e6-af3c-60b86a27b237/scratchpad/w3/stop-envelope.json`

```json
{
  "session_id": "4e1a2aa2-1800-43e6-af3c-60b86a27b237",
  "transcript_path": "/Users/iskang/.claude/projects/-Volumes-Data-AIStudio-workspace-ai-framework--opal-worktrees-task-999/4e1a2aa2-1800-43e6-af3c-60b86a27b237.jsonl",
  "cwd": "/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_999",
  "hook_event_name": "Stop",
  "stop_hook_active": false
}
```

`transcript_path`는 실존 경로를 넣었을 뿐 **읽지 않았고 판정 입력으로 쓰지 않았다**(C-6 준수. transcript 정책은 W-7/AC-6 소관).

## 2. 공개 hook 진입점 실행

등록 원문(`~/.claude/settings.json:87`):

```
"$HOME/.opal/.venv/bin/python" "$HOME/.opal/tools/ownership-tool/ownership_tool/stop_hook.py"
```

실행한 명령은 이것과 동일하다.

**stdout 1줄 (원문 그대로)**:

```
{"decision": "block", "reason": "OPAL Stop guard: block_continue. 판정 대상 1건 — task_id=999-260919-opds-세션상속-스톱가드-목업검증 | transition_action=continue | next_action=EXECUTE 작업 진행 중 · 이 태스크가 아직 transition_action=continue다. 응답을 끝내지 말고 이어서 진행하라."}
```

**exit code**: `0` (`stop_hook.py`는 전 경로 fail-safe exit 0이며, 차단은 exit code가 아니라 stdout 1줄로 전달된다)

## 3. S-4n — 실제 실행된 명령 관측

| 파일 | 경로 |
|---|---|
| 셸 트랜스크립트 (`bash -x`) | `…/scratchpad/w3/probe.trace` |
| 주입한 stdin 봉투 원문 | `…/scratchpad/w3/stop-envelope.json` |
| hook stdout | `…/scratchpad/w3/probe.stdout` |
| 프로브 스크립트 | `…/scratchpad/w3/probe.sh` |

(경로 접두: `/private/tmp/claude-501/-Volumes-Data-AIStudio-workspace-ai-framework--opal-worktrees-task-999/4e1a2aa2-1800-43e6-af3c-60b86a27b237`)

**트랜스크립트 전문** (`+ ` 행 4건 = 변수대입 1 · 봉투 준비 `cat` 1 · **hook 진입점 1** · 결과 `echo` 1):

```
+ W3=/private/tmp/claude-501/-Volumes-Data-AIStudio-workspace-ai-framework--opal-worktrees-task-999/4e1a2aa2-1800-43e6-af3c-60b86a27b237/scratchpad/w3
+ cat
+ /Users/iskang/.opal/.venv/bin/python /Users/iskang/.opal/tools/ownership-tool/ownership_tool/stop_hook.py
+ echo EXIT=0
```

**금지 토큰 grep 결과 — 전건 0건**:

| 토큰 | `probe.trace` | `stop-envelope.json` |
|---|---|---|
| `show_json` | 0 | 0 |
| `lease.claim` | 0 | 0 |
| `owner.json` (쓰기) | 0 | 0 |
| `monkeypatch` | 0 | 0 |
| `unittest.mock` | 0 | 0 |
| `pytest` | 0 | 0 |

C-4 충족 — 실행 표면은 공개 hook 진입점 1건뿐이고, evaluator에 `show_json`·lease를 주입한 흔적이 없다.

## 4. evaluator 반환 덤프 (판정 근거 보강)

같은 봉투·같은 env로 `stop_evaluator.evaluate(payload, project_root=payload["cwd"])`를 1회 호출했다. 이는 `stop_hook.main()`의 호출 형태(`stop_hook.py:47-51`)와 동일하며, `show_json`·`prior_receipt`·`env`·lease를 **주입하지 않아** 실제 파일 상태를 그대로 읽게 뒀다(C-4).

덤프 파일: `…/scratchpad/w3/dump.json` · 스크립트: `…/scratchpad/w3/dump.py`

```json
{
  "decision_kind": "block_continue",
  "diagnostics": [],
  "candidates": [
    {
      "task_id": "999-260919-opds-세션상속-스톱가드-목업검증",
      "classification": "current_session_owned",
      "forced": true,
      "diagnostics": [],
      "evidence": {
        "hub_root": "…/.opal-worktrees/task_999",
        "lease_path": "…/tasks/999-…/run/.runtime/owner.json",
        "registry_matched": false,
        "claim_source": "state_transition"
      },
      "state": {
        "current_status": "in_progress",
        "next_action": "EXECUTE 작업 진행 중"
      }
    }
  ],
  "evidence": {
    "session_id": "4e1a2aa2-1800-43e6-af3c-60b86a27b237",
    "registry_entry_count": 0,
    "candidate_count": 1,
    "forced_count": 1,
    "task_path_ambiguous": false,
    "stop_hook_active": false
  },
  "block_count": 2
}
```

- 후보 `evidence.claim_source` = **`state_transition`** — W-2가 실측한 `run/.runtime/owner.json`의 값이 evaluator까지 그대로 전달됐다. `_PASSIVE_CLAIM_SOURCE = "session_start"`(`stop_evaluator.py:27`)가 아니므로 `passive_ownership`로 강등되지 않았고, `diagnostics`가 빈 배열인 것이 이를 뒷받침한다(D-G).
- `registry_matched: false` / `registry_entry_count: 0` — 허브 registry의 `owner_session_id: null` 결손과 일관된다. **강제 후보 자격은 registry 없이 lease만으로 성립했다.**

## 5. 기대 3값 대조표 (게이트)

| 항목 | 기대값 (D-F) | 실측값 | 판정 |
|---|---|---|---|
| 후보 `classification` | `current_session_owned` | `current_session_owned` | **일치** |
| `evidence.forced_count` | `1` | `1` | **일치** |
| `decision_kind` | `block_continue` | `block_continue` | **일치** |
| (보강) 후보 `claim_source` | `state_transition` | `state_transition` | **일치** |
| (보강) hook stdout | 차단 결정 1줄 | `{"decision":"block","reason":…}` 1줄 | **일치** |

> AC-4 문언의 `classification=owned`는 코드에 없는 값이므로 D-F대로 폐쇄 enum `current_session_owned`로 읽었다(`stop_evaluator.py:22` `_FORCED_CLASSIFICATIONS`).

**게이트 판정: PASS.** 미달 항목 없음 — P4 이후(W-4 · W-5 · W-6)가 열린다.

## 6. 관측된 부수효과 (후속 Work item 주의)

이 프로브는 코드·테스트·`~/.opal/`를 수정하지 않았고 태스크 999 자산만 건드렸다(C-5). 다만 **실제 evaluator를 2회 호출했으므로** stop-guard receipt가 태스크 999 경계 안에서 생성됐다:

- 경로: `/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_999/.opal/run/.runtime/stop-guard/4e1a2aa2-1800-43e6-af3c-60b86a27b237.json`
- 내용: `{"block_count": 2, "decided_at": null, "decision_kind": "block_continue", "fingerprint": null, "session_id": "4e1a2aa2-…"}`
- 프로브 이전 이 receipt json은 **존재하지 않았다**(디렉터리에 `.lock`만 18:08 존재). 즉 `block_count: 2`는 전적으로 이 프로브의 2회 호출(2단계 hook 실행 + 4단계 덤프)에서 발생했다.
- **W-5/S-8은 `block_count` 기준선이 0이 아니라 2에서 출발한다.** `fingerprint: null`(state view 미주입 경로)도 W-4/S-5의 `fingerprint` 유무 실측 시 이 사실을 전제로 읽어야 한다.

`git status`상 워크트리 변경은 W-6 착수 전 기존 2건(`session_start_hook.py`·`test_session_start.py`)과 미추적 태스크 폴더뿐이며, 이 프로브는 새 소스 변경을 만들지 않았다.
