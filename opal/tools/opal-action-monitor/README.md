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

## 상태 판정 (6상태)

| 조건 | 상태 |
|------|------|
| journal.md에 해당 phase `blocked` 기록 | `blocked` |
| `.exitcode` == 0 | `done` |
| `.exitcode` == 1 | `failed` (is_error, 프로세스 정상) |
| `.exitcode` == 2 (또는 그 외 값) | `error` (하드에러) |
| `.exitcode` 부재 + 산출물(events/result/prompt) 존재 | `running` |
| `.exitcode` 부재 + 산출물 전무 | `pending` |

전체 blocked 플래그 = journal.md에 `blocked` 이벤트 행이 1개 이상 존재.

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

`--watch` 종료 조건 3종: ① 모든 phase가 terminal 상태(`done`/`failed`/`error`/`blocked`) +
grace 1주기 경과, ② `--watch-timeout` 도달, ③ `Ctrl-C`(KeyboardInterrupt).

## 텍스트 현황판 컬럼

`축(phase) | 상태 | 경과 | 최근 이벤트 요약 | 비용/세션` + 하단 journal tail(기본 8행) + blocked 배너.

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
  "phases": [
    {
      "phase": "t1", "axis": "stream", "status": "done", "exitcode": 0,
      "elapsed_sec": 68,
      "last_event": {"kind": "tool_use", "name": "Write"},
      "cost_usd": 0.56, "session_id": "9A63…", "is_error": false
    }
  ],
  "journal_tail": [{"time": "…", "phase": "g", "event": "gate-verdict", "detail": "pass"}]
}
```

`last_event.kind` ∈ `tool_use | tool_result | result | result_text | generic`.

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
