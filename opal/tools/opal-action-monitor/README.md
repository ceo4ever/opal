# opal-action-monitor

루프 액션 에이전트(opal-agent 채널)의 `<task_folder>/.oppl-run/` 산출물을 파싱해
**단계(phase) × 축(axis) 진행 현황판**을 렌더하는 읽기 전용 CLI.

- **무의존성** — Python 3.10+ 표준 라이브러리만 (`json`/`argparse`/`pathlib`/`os`/`time`/`datetime`/`sys`)
- **읽기 전용** — `.oppl-run/`에 아무 것도 쓰지 않는다(파서/렌더러 전용)
- **텍스트 / `--json` / `--watch`** 3가지 출력 모드

## 설치/배포 경로

```
~/.opal/tools/opal-action-monitor/run.sh  →  ~/.opal/.venv/bin/python opal_action_monitor.py
```

`run.sh`가 OPAL 전용 가상환경(`~/.opal/.venv`)의 python으로 `opal_action_monitor.py`를 실행한다
(`opal/tools/opal-agent/run.sh`와 동일 관례 — state-tool·brain-tool 등 다른 OPAL 파이썬 툴과도 동일).
표준 라이브러리만 쓰므로 추가 의존성은 없다.

## 입력 계약 — `.oppl-run/` 산출물 규약

입력 계약의 SSOT는 `opal/agents/opal-loop-action-agent/AGENT.md` §결과 파일 규약(v2) ·
§운행 일지(journal)다. opal-action-monitor는 아래 규약을 읽기만 하는 독립 리더이며,
루프 액션 에이전트·opal-agent와 직접 import/호출 관계가 없다(파일 계약으로만 연결).

phase 순서: `t1, t2, g, t3, t4a, t4b`.

```
비동기 축(t1/t2/t3): <phase>.events.jsonl  ← stdout (claude stream-json 원본 JSONL; 마지막 줄=result 이벤트)
동기 축(g/t4a/t4b):  <phase>.result.json   ← stdout (claude 단일 JSON; 5필드 소비)
공통:                <phase>.err.log       ← stderr
공통:                <phase>.exitcode      ← 완료 마커(★ 존재 여부로 완료 판정)
공통:                <phase>.prompt.txt    ← 디스패치 프롬프트 원문
공통:                journal.md            ← 루프 액션 에이전트 게이트 판단·재시도·blocked 기록(append-only)
```

재시도 접미사(`<phase>.a<N>.*`, N=2부터)가 있으면 최대 N을 최신 시도로 채택한다.

**완료 마커** = `.exitcode` 파일의 존재. `.events.jsonl`/`.result.json`의 존재/비존재로
완료를 판정하지 않는다([066계승][MUST], `AGENT.md` §결과 파일 규약).

## 상태 판정 — 위임 경로와 legacy 경로

`.oppl-run/runtime.json`(`oppl-runtime-tool` 운영 ledger)의 **존재 여부**로 경로가 갈린다.
monitor는 어느 경로에서도 `.oppl-run/`에 쓰지 않는다.

### 위임 경로 — `runtime.json` 존재 (7상태)

monitor는 **자체 재판정을 하지 않는다.** ledger의 phase별 `status`(7종)와 잔여 상한만 읽어
렌더한다 — `opal-agent`와 monitor는 동일 adapter의 terminal 판정 결과만 소비한다.

| 상태 | 의미 |
|------|------|
| `pending` | 실행 등록 전 또는 자원 대기 |
| `running` | 루트 프로세스나 등록 자식 실행 중 |
| `done` | 완료조건과 결과 계약 모두 성공 |
| `failed` | 실행 또는 검증이 정상적으로 실패 |
| `error` | 실행기·schema·알 수 없는 terminal framing 오류 |
| `blocked` | 계약·승인·예산·무진전으로 자동 진행 불가 |
| `timed_out` | watchdog이 process group을 종료 |

phase 레코드 경로는 `counters.<task_id>.phases.<phase>`다. 레코드는 `admit` 시점에 처음
생성되므로(거부된 admit은 레코드를 만들지 않는다) **레코드가 없는 phase는 `pending`·카운터 0**으로
읽고 오류를 내지 않는다.

### legacy 경로 — `runtime.json` 부재 (기존 6상태 휴리스틱)

비-OPPL·legacy `.oppl-run/` 하위호환. 아래 파일 휴리스틱을 그대로 쓰며 **`timed_out`을 절대
출력하지 않는다.** `--json` 출력에 `runtime` 위임 블록도 만들지 않는다(없는 상한을 지어내지 않는다).

| 조건 | 상태 |
|------|------|
| journal.md에 해당 phase `blocked` 기록 | `blocked` |
| `.exitcode` == 0 | `done` |
| `.exitcode` == 1 | `failed` (is_error, 프로세스 정상) |
| `.exitcode` == 2 (또는 그 외 값) | `error` (하드에러) |
| `.exitcode` 부재 + 산출물(events/result/prompt) 존재 | `running` |
| `.exitcode` 부재 + 산출물 전무 | `pending` |

전체 blocked 플래그 = journal.md에 `blocked` 이벤트 행이 1개 이상 존재(두 경로 공통).

## CLI로 사용

```bash
# 텍스트 현황판 (1회성)
~/.opal/tools/opal-action-monitor/run.sh <task_folder>

# JSON 출력 (스킬/도구 파싱용)
~/.opal/tools/opal-action-monitor/run.sh <task_folder> --json

# 주기적 재렌더 (기본 2초 폴링)
~/.opal/tools/opal-action-monitor/run.sh <task_folder> --watch
~/.opal/tools/opal-action-monitor/run.sh <task_folder> --watch 5 --watch-timeout 600
```

| 옵션 | 설명 |
|------|------|
| `task_folder` | 태스크 폴더 경로 (하위 `.oppl-run/` 스캔) |
| `--json` | JSON 스키마로 출력(1회성 — `--watch`와 함께 쓰면 `--watch`는 무시됨) |
| `--watch [간격초]` | 주기적으로 재렌더(기본 2초). ANSI clear + 전체 재그림(full repaint) |
| `--watch-timeout <초>` | `--watch` 상주 상한(초), 기본 1800 |

`--watch` 종료 조건 3종: ① 모든 phase가 terminal 상태(`done`/`failed`/`error`/`blocked`/`timed_out`) +
grace 1주기 경과, ② `--watch-timeout` 도달, ③ `Ctrl-C`(KeyboardInterrupt).

## 텍스트 현황판 컬럼

`축(phase) | 상태 | 경과 | 최근 이벤트 요약 | 비용/세션` + 하단 journal tail(기본 8행) + blocked 배너.
위임 경로에서는 머리말에 `runtime: <run_id> (<status>)  round 사용/상한  dispatch 사용/상한  attempt≤N  identical-fail≤N  cost 사용/상한  wall 사용/상한s` 한 줄이 추가된다.

- **경과**: `min(prompt.txt mtime, events/result 최초 mtime)` → `.exitcode` mtime(있으면) 또는 `now`(진행중) 차이(초). 파일 mtime을 프록시로 사용.
- **최근 이벤트 요약**: stream 축(`events.jsonl`)은 역순 순회로 첫 의미 이벤트를 찾는다 —
  `assistant.message.content[].type=="tool_use"` → `"tool_use: <name>"`,
  `user.message.content[].type=="tool_result"` → `"tool_result"`,
  `type=="result"` → `"result(<subtype>)"`, 그 외 → 최상위 `type`(미보장 타입은 generic degrade).
  sync 축(`result.json`)은 `result` 텍스트 앞부분을 요약한다.
- **비용/세션**: 마지막 result 이벤트의 `total_cost_usd`·`session_id`(있으면).

## `--json` 출력 스키마

```json
{
  "ok": true,
  "task_folder": "<abs>",
  "generated_at": "<ISO8601>",
  "blocked": false,
  "runtime": {
    "run_id": "run-20260914010203-0a1b2c3d",
    "status": "running", "revision": 7,
    "design_round": 1, "project_dispatch_count": 3,
    "cost_used": 0.15, "wall_time_used": 300.0,
    "budget_snapshot": {"max_design_rounds": 5, "max_project_dispatches": 20,
                        "max_task_attempts": 3, "max_identical_failures": 2,
                        "max_wall_time_sec": 3600, "max_cost_usd": 10.0}
  },
  "phases": [
    {
      "phase": "t1", "axis": "stream", "status": "done", "exitcode": 0,
      "elapsed_sec": 68,
      "last_event": {"kind": "tool_use", "name": "Write"},
      "cost_usd": 0.56, "session_id": "9A63…", "is_error": false,
      "attempt_count": 1, "resume_count": 0
    }
  ],
  "journal_tail": [{"time": "…", "phase": "g", "event": "gate-verdict", "detail": "pass"}]
}
```

`status` ∈ `pending | running | done | failed | error | blocked | timed_out` (7종).
`timed_out`은 위임 경로에서만 나온다.

top-level `runtime`과 phase의 `attempt_count`/`resume_count`는 **위임 경로에서만 존재한다.**
`runtime.json`이 없으면 이 키들이 아예 없고 `status`도 6종으로 제한된다.

`last_event.kind` ∈ `tool_use | tool_result | result | result_text | generic`.
`axis`/`exitcode`/`elapsed_sec`/`last_event`/`cost_usd`/`session_id`는 두 경로 모두 파일 관측값이며,
위임 경로에서도 `status` 판정에는 쓰이지 않는다.

## 에러 계약

폴더 부재 또는 `<task_folder>/.oppl-run/` 부재 시 stdout에 아래를 출력하고 exit 1로 종료한다
(`--json` 여부와 무관하게 동일 계약):

```json
{"ok": false, "error": "<메시지>"}
```

## 관련 소스

- opal-agent(비동기 축 stream-json 실행 경로): `opal/tools/opal-agent/` — opal-action-monitor는
  이 도구의 산출물(`.oppl-run/`)만 읽는 독립 리더이며, opal-agent는 도구 레지스트리에
  등록되어 있지 않다(opal-action-monitor만 레지스트리 등록 대상).
- 결과 파일 규약·운행 일지 SSOT: `opal/agents/opal-loop-action-agent/AGENT.md`

## 변경이력

- v1.0 (2026-07-17 19:55 KST, 067) 최초 구현 — `.oppl-run/` 파서(phase 6종·재시도 접미사 최신 채택), 6상태 판정, R-NEST 최근 이벤트 요약(방어적 파싱), 텍스트 현황판·`--json`·`--watch`(2초 폴링·상한 3종)·에러계약
- v1.1 (2026-07-17 23:04 KST, 067) 도구명 리네임 — `oppl-monitor` → `opal-action-monitor`(향후 oppd·opsdd 액션 에이전트 공통 관측 도구로 확장 예정이라 이름 중립화). 로직 무변경, `.oppl-run/` 규약명 유지
- v1.2 (2026-09-14, 131) 상태 판정 위임 — `.oppl-run/runtime.json`(oppl-runtime-tool ledger) 존재 시 phase status 7종(`timed_out` 추가)과 잔여 상한을 재판정 없이 렌더하고 `--json`에 top-level `runtime` 블록 노출. `runtime.json` 부재 시 기존 6상태 휴리스틱 유지·`timed_out` 미출력·`runtime` 블록 미생성. `TERMINAL_STATUSES`에 `timed_out` 추가(`--watch` 종료 판정). 두 경로 모두 쓰기 0건 유지 (PLAN 131 D7 / W-8 / S-21)
