# state-tool

> OPAL 파이프라인 현황판 JSON SSOT 관리 CLI
> 소스: `opal/tools/state-tool/` | 배포: `~/.opal/tools/state-tool/`
> 설계 근거: `tasks/134-260501-opp-pipeline-state-tool/PLAN.md` §2.1~§2.20

## 개요

`state-tool`은 STATE.md의 파이프라인 현황판 표를 `state.json`(단일 진실 공급원)으로 분리하고, 상태 변경 명령과 이벤트 receipt 검증 명령을 제공한다.

> **070: task-step 키 주소 체계**. 행 주소를 불안정한 순번(`--row N`)이 아니라 `references/pipeline.json`에 선언된 task-step key(`plan.pm_gate` 형식)로 지정할 수 있다. `advance`/`mark`/`block`/`add-row`는 `--task-step <key>` / `--task-step-id <n>` / `--row <n>`(deprecated 별칭, 하위호환) 중 정확히 하나를 받는다. 미지정 시 `task_step_addr_required`, 2개 이상 동시 지정 시 `task_step_addr_conflict`, key 미매칭 시 `task_step_not_found`(candidates 포함).

- STATE.md는 **의사결정 로그·블로커·자유 기재를 담는 저널**이다. 파이프라인 현황(행 상태·진행·다음 액션)의 SSOT는 `state.json`이며, 조회는 `state-tool show`로 한다.
- **출력 형식**: 모든 응답은 단일 라인 JSON
- **전이 출력 계약**: `show`/`advance`/`mark`/`block`/`add-row`/`status`와 차단 응답은 `transition_action`(`continue`/`await_user`/`blocked`/`complete`), `report_type`(`progress_report`/`decision_request`), `next_action`을 함께 반환한다. `progress_report`는 비차단 통지이고, `decision_request`만 사용자 응답을 기다리는 신호다. 응답 자체는 stdout 계약이며, PM 보고 시 `log-event --event pm.report`가 보고 사건과 `state.json.run_log.last_report` 파생 포인터를 같은 원자 쓰기로 영속한다(`docs/run-log/CONTRACT.md` §1.4·§2.4).

## 테스트 실행

책임 영역별 `test_*.py`는 서로 독립 수집할 수 있다. 기본 회귀 확인에는 파일별
pytest 프로세스를 최대 4개 병렬 실행하는 다음 명령을 사용한다.

```bash
bash opal/tools/state-tool/run-tests.sh --jobs 4
```

실패한 파일이 있어도 나머지 파일을 모두 실행한 뒤 전체 명령이 비정상 종료한다.
재현·진단을 위해 단일 pytest 프로세스에서 순서대로 실행하는 경로도 유지한다.

```bash
~/.opal/.venv/bin/python -m pytest opal/tools/state-tool/tests/ -q
```

병렬 runner에 pytest 옵션을 추가하려면 `--` 뒤에 둔다. 예를 들어
`run-tests.sh --jobs 2 -- -x`처럼 실행할 수 있다. 외부 병렬 플러그인은 필요하지 않다.

## 호출 형식

```bash
~/.opal/tools/state-tool/run.sh <command> <task-path> [options]
```

`event-verify`는 상태를 다루지 않으므로 `<task-path>` 없이 호출한다. 개발 중에는 소스 경로로 직접 호출:
> `bash opal/tools/state-tool/run.sh <command> <task-path> [options]`

### `resolve-mode` — 신규 시작·재개 모드 단일 판정

```bash
~/.opal/tools/state-tool/run.sh resolve-mode <task-path> \
  [--mode <interactive|semi-agentic|agentic>] \
  [--new-task]
```

- 우선순위: 명시 `--mode` > 유효한 기존 `state.json.mode` > 신규 태스크(`--new-task`) 기본값. `--skill`을 주면 아래 `resolve-start`와 같은 Pilot별 기본값 표를 쓰고, 생략하면 `semi-agentic`이다(호환). Pilot 시작·재개의 표준 판정은 세 축을 함께 보는 `resolve-start`다.
- 기존 태스크의 무플래그 재개는 저장 mode를 상속한다. 명시값이 다르면 rows·`created_at`을 보존하고 mode만 원자 갱신하며 STATE.md에 결정을 기록한다.
- 기존 mode 누락·비문자·허용값 밖 값은 파일을 고치지 않고 `interactive` / `fail_closed`로 반환한다. 명시값으로만 복구할 수 있다.
- JSON 문법 오류나 top-level 비객체는 `state_json_malformed`로 차단한다. 프로젝트 브리프의 mode 문구는 표시 전용이며 이 JSON 응답이 판정 SSOT다.

### `resolve-start` — Pilot 시작·재개의 mode·workspace·actor 판정

```bash
~/.opal/tools/state-tool/run.sh resolve-start <task-path> --skill <alias> [--new-task] \
  [--interactive|--semi-agentic|--agentic] [--wt|--worktree|--no-wt] [--pm|--no-pm]
```

- 사용자가 입력한 원문 플래그를 그대로 넘긴다. 응답: `effective_mode`·`mode_source`, `workspace`(`worktree`|`hub`)·`workspace_source`, `actor`(`coordinator`|`worker`|`pm`)·`actor_source`(`default`|`explicit`|`state`|`legacy_default`), `warnings`. 신규는 `init_args`도 반환한다.
- 신규 기본값(`NEW_TASK_DEFAULTS`): `opd`·`opds`·`oppd`·`oppl`·`oppb`는 `agentic`·`worktree`, 그 외 Pilot은 `semi-agentic`·`hub`. actor는 `opd`·`opds`만 `coordinator`이고 그 외는 `worker`(state.json에 키를 만들지 않음). 축별 원문은 `harness/modes.md`·`worktree.md`·`actor.md`가 소유한다.
- 신규는 읽기 전용이다. `init_args`(`--skill`·`--mode`·`--workspace`·opd/opds만 `--actor`와 `--rows-from`)에 worktree면 `worktree-tool create`가 발급한 `--worktree <worktree_root>`를 덧붙여 `init`에 넘긴다.
- opd/opds 신규의 `--rows-from`은 `state_tool.py` 기준 `../../skills/opal-pilot-dev/references/`의 절대경로다 — actor `coordinator`→`pipeline-pm.json`(PM 경로), `worker`+opd→`pipeline.json`, `worker`+opds→`pipeline-short.json`. 파일이 없으면 `spec_file_not_found`. 재개 응답과 다른 Pilot의 `init_args`에는 넣지 않는다.
- 충돌: 모드 플래그 2개 이상 `mode_flag_conflict`, `--wt`+`--no-wt` `workspace_flag_conflict`, `--pm`+`--no-pm` `actor_flag_conflict`, opd/opds 밖 `--pm` `actor_unsupported_for_skill`(`--no-pm`은 경고 `no_pm_redundant`만), oppb `--no-wt` `workspace_required_for_skill`.
- 재개(state.json 존재, `--new-task` 없음): 저장값을 상속한다. workspace는 `worktree` 키 유무, actor는 키 값(부재 시 `worker`/`legacy_default`). 저장값과 다른 workspace·actor 플래그는 `resume_axis_locked`(`axis` 동봉). 명시 mode 플래그만 `resolve-mode`와 같이 mode를 원자 갱신한다.

## 종료 코드

| 코드 | 의미 |
|------|------|
| `0` | 성공 |
| `1` | 위반 / 스코프 오류 / 검증 실패 |
| `2` | 내부 오류 (subprocess 실패 / 미구현 기능) |

> 근거: `tasks/134-260501-opp-pipeline-state-tool/TASK.md` T-3

## 서브 명령

### 1. `init` — state.json + STATE.md 생성

```bash
~/.opal/tools/state-tool/run.sh init <task-path> \
  --skill <opp|opd|opds|opdw|opwt|opgc|oppd|opsdd|oppl|opdd|oppb> \
  --mode <interactive|semi-agentic|agentic> \
  [--workspace <worktree|hub>]          # resolve-start init_args \
  [--worktree <worktree_root 절대경로>] \
  [--actor <coordinator|worker>]        # opd/opds 전용 \
  [--task-title <text>] \
  [--next-action <text>] \
  [--rows-spec <inline-json>] \
  [--rows-from <path-to-pipeline.json-or-skill.md>] \
  [--rows-acts <inline-json>]          # 시그니처만, 미구현 (R-13) \
  [--force]                            # 멱등성 우회 (--note 필수) \
  [--note <text>]
```

- `--rows-spec`과 `--rows-from`은 배타적 (동시 사용 불가 — `rows_input_conflict`)
- `--rows-from`은 확장자로 분기한다(070 R-2): `.json`이면 `pipeline.json` 스펙 검증 후 로딩(rows에 task-step `key` 영속, `conditional` 메타데이터 저장), `.md`이면 기존 SKILL.md 표 파싱(레거시) + stderr에 deprecation 경고 1줄 출력. 두 경로 모두 stdout 응답 계약은 동일.
- `--next-action`: `state.json` `next_action` 필드로 영속화된다(기본값 `"PLAN 단계 진입"`). 이후 `advance`/`mark` 시 파이프라인 프론티어(첫 미완료 행)에서 자동 파생·갱신된다(072) — PM 수동 갱신 불필요. **094부터 이를 렌더하는 STATE.md 전용 섹션은 없다**(저널화로 `## 다음 액션` 자동 파생 섹션 삭제) — 현재 값은 `show`(md의 `- 다음 액션:` 줄 또는 json의 `next_action` 필드)로 조회한다
- `--force` 사용 시 `--note` 필수 (`note_required_for_force`)
- `--workspace worktree`는 `--worktree` 없이 `worktree_path_required`, `--workspace hub --skill oppb`는 `workspace_required_for_skill`로 기록 전에 거부한다. 미지정은 기존 동작이다.
- `--actor`는 opd/opds에서만 받으며 지정 시에만 `actor` 키를 만든다. legacy `--actor pm`은 `actor_pm_retired`로 거부한다.
- 구 STATE.md 표 흡수 옵션(`import`+`existing` 합성명, 094 이전 사용): **094(STATE.md 저널화)에서 제거됨** — 호출 시 rows 파싱 없이 항상 `import_existing_removed`로 거부된다(exit 1). 파싱 대상이던 파이프라인 표 자체가 STATE.md에서 소멸했기 때문이다. 행 구성은 `--rows-from <pipeline.json>` 또는 `--rows-spec`을 사용한다. (해당 인자는 argparse에 `help=argparse.SUPPRESS`로만 존치 — 완전히 삭제하면 미인식 인자로 exit 2 비-JSON 출력이 발생해 stdout 계약이 깨지므로, 인자는 받되 즉시 거부하는 방식을 택했다. 이 문서는 SUPPRESS 취지에 따라 정확한 플래그 철자를 의도적으로 노출하지 않는다)
- 모든 모드의 사용자 확인 행은 `pending`으로 초기화된다. 다음 단계 진입 시 저장 mode를 읽는 단일 판정 훅이 자동 승인 여부를 결정한다. `semi-agentic`은 PLAN-equivalent 승인 뒤, `agentic`은 정상 전 구간에서 CLOSE 직전 행을 포함해 `done/auto`로 처리할 수 있으며 interactive 또는 invalid mode는 fail-closed한다.
- `--note`(`--force` 시 기재)에 `{owner_name}` 플레이스홀더를 쓰면 `~/.opal/identity.md`의 `owner_name`으로 write-time 치환된다. identity.md 부재/`owner_name` 공란/파싱 실패 시 원문(`{owner_name}`) 그대로 유지(fail-safe) — 054

**성공 응답 예시**:
```json
{"ok": true, "command": "init", "task_path": "/path/to/task", "task_id": "134-...", "rows_count": 20, "created_at": "2026-05-01 17:58", "import_existing": false}
```

---

### 2. `show` — 파이프라인 현황 조회 (094 R-5: 표준 경로)

```bash
~/.opal/tools/state-tool/run.sh show <task-path> [--format md|json|full]
```

| `--format` | 출력 내용 |
|-----------|----------|
| `md` (기본) | `state.json.rows[]`에서 파생 렌더한 파이프라인 표 + `## 현재 상태` 3줄(모드/상태/다음 액션) |
| `json` | state.json raw (`marker_present` 필드 포함) |
| `full` | STATE.md 전체 본문 |

- `md`/`full` 모두 **마커 유무와 무관하게** `state.json`에서 렌더한다(094 R-5/D-4 — SSOT는 `state.json` 단일이며, 레거시 STATE.md의 마커·표 잔존 여부는 렌더 소스에 영향을 주지 않는다)
- 레거시(001~093) STATE.md에 파이프라인 마커가 잔존해 `marker_present:true`이면 `md`/`full` 응답 상단에 배너 1줄이 prepend된다: "[레거시] 이 태스크의 STATE.md에는 파이프라인 표가 남아 있으나 더 이상 갱신되지 않는 동결 텍스트입니다. 현황의 SSOT는 state.json이며 아래 렌더가 최신입니다."
- `marker_present`(`json` 포맷 필드): 094 저널화 이후 이 값이 `true`인 것은 **레거시 동결 표 잔존**을 뜻한다(현재 갱신되는 미러가 아니다) — 키·타입은 하위호환으로 존치
- state.json 미존재 시: `state_not_initialized` + exit 1

---

### 3. `advance` — ⬜→🔄 전환

```bash
~/.opal/tools/state-tool/run.sh advance <task-path> \
  (--task-step <key> | --task-step-id <n> | --row <n>) \
  [--note <text>] \
  [--force --note <text>] \
  [--next-action <text>]                    # per-transition 오버라이드, 비지속 (072)
```

- 행 주소는 `--task-step`(key) / `--task-step-id`(숫자) / `--row`(숫자, deprecated 별칭) 중 정확히 하나 (070 R-4)
- `pending` 상태인 행만 `in_progress`로 전환 (T-7)
- `--force`는 `--note`가 필수(`note_required_for_force`)이며 자동 승인·게이트 산출물·명확화·code-scan 인용 가드를 우회한다. PM 경로 설계 게이트 가드(아래 `design-gate` 절)는 우회하지 못한다.
- CLOSE 단계 첫 행의 처리도 mode-aware 단일 판정을 따른다. interactive/fail-closed만 직전 사용자 확인 또는 확인 행 없는 Pilot의 `--owner user` 승인을 요구한다.
- `state.json` `next_action`이 파이프라인 프론티어(첫 미완료 행)에서 자동 파생·갱신된다. `--next-action <text>` 지정 시 해당 값이 파생값보다 우선하며, 이 오버라이드는 **해당 전이 1회에만** 적용된다 — 다음 전이가 `--next-action` 없이 실행되면 자동 파생으로 복귀한다(072). **094부터 STATE.md에 이를 렌더하는 `## 현재 상태`/`## 다음 액션` 섹션은 없다** — 현재 상태 조회는 `show`로 한다
- STATE.md는 `> 최종 갱신:` 헤더 타임스탬프만 갱신된다(저널 후처리, 094)
- `--note`의 `{owner_name}` 플레이스홀더는 identity.md `owner_name`으로 write-time 치환된다. 부재/공란/파싱 실패 시 원문 유지(fail-safe) — 054

---

### 4. `mark` — ⬜/🔄→✅ 전환

```bash
~/.opal/tools/state-tool/run.sh mark <task-path> \
  (--task-step <key> | --task-step-id <n> | --row <n>) --done \
  [--note <text>] \
  [--as-worker --worker-stage <stage>] \   # 워커 권한 게이트 (T-10)
  [--step <N/M> | --action-step <N/M>] \    # EXECUTE Step 진행 표기 (동일 dest, 070 R-5)
  [--worker-duration-minutes <minutes>] \   # 워커 실제 실행 시간(분) 기록 (103 R-15)
  [--worker-duration-unknown] \             # 소요 미상 명시 — 누락 경고 억제 (103 R-21)
  [--owner <PM|worker|user|auto>] \
  [--auto-pass] \                           # agentic 자율 통과 (T-9)
  [--force] \                               # --note 필수
  [--next-action <text>]                    # per-transition 오버라이드, 비지속 (072)
```

- 행 주소는 `--task-step`(key) / `--task-step-id`(숫자) / `--row`(숫자, deprecated 별칭) 중 정확히 하나 (070 R-4). 미지정 시 `task_step_addr_required`, 2개 이상 지정 시 `task_step_addr_conflict`, key 미매칭 시 `task_step_not_found`(응답에 `candidates` 후보 목록 포함)
- `--action-step`은 `--step`의 신규 별칭(동일 동작, 070 R-5) — 기존 `--step`도 그대로 동작
- `--owner`와 `--auto-pass`는 배타적
- `--as-worker` 사용 시 `--worker-stage` 필수
- `--worker-duration-minutes <n>`(103 R-15)은 그 행에서 **워커(서브에이전트)가 실제 실행한 시간을 분 단위 0 이상 정수**로 `rows[].worker_duration_minutes`에 기록한다. 원천은 워커 완료 시 하네스가 반환하는 `duration_ms`이며, PM이 분으로 환산해 전달한다(집계 기준 16-b)
  - **지정 시에만 기록된다** — 미지정 호출은 필드를 만들지 않으며 `state.json`·응답 키 집합이 종전과 완전히 동일하다(기존 태스크 무영향)
  - 미기록 행의 소요는 집계에서 `PM` 계열로 전액 귀속된다(축퇴 규칙, 집계 기준 16-a) — 따라서 기록이 없는 과거 태스크는 종전 2계열 수치와 항등이다
  - `0`은 유효값이다(측정했으나 1분 미만). "측정하지 않음"은 인자 미지정으로 표현한다
  - 음수·소수·비수치는 **argparse 파싱 시점에 거부**된다(exit 2, `--owner` choices 위반과 동일 계열) — 전용 에러 코드는 신설하지 않았다
  - `--auto-pass` 재호출 멱등 no-op(093 F-005)은 이 인자가 실린 호출에는 적용되지 않는다 — 기록할 값이 조용히 버려지지 않게 하기 위함이며, 인자 없는 기존 호출의 no-op 조건은 불변이다
  - 기록에 성공하면 `mark` 응답 JSON에도 `worker_duration_minutes` 키가 실린다(지정하지 않으면 키 없음)
- **소요 누락 경고**(103 R-21) — `--as-worker` 또는 `--worker-stage`가 실린 `mark`가 그 행을 실제로 `done`으로 닫는데 `--worker-duration-minutes`가 없으면, 응답 JSON에 `warnings` 배열이 조건부로 실린다(`[{"code": "worker_duration_missing", "message": ...}]`)
  - **경고이지 차단이 아니다** — exit code는 `0`을 유지하고 상태 전이도 정상 수행되며, `state.json`·`STATE.md` 산출물은 경고 유무와 무관하게 동일하다. 경고는 stdout JSON에만 실린다
  - 경고가 없으면 `warnings` 키 자체를 만들지 않는다 — 기존 호출의 응답 키 집합은 종전과 완전히 동일하다
  - 이 경고가 필요한 이유: 워커 완료 알림의 `duration_ms`는 세션과 함께 사라지고 행에는 완료 시각만 남아 시작 시각을 되살릴 수 없다. 그 자리에서 적지 않으면 소요는 **영구히 소실**되고 통계에서 PM 몫으로 잘못 귀속된다(소급 복구 경로 없음)
  - 오탐을 막는 4관문: ① 값이 이미 실림 ② `--worker-duration-unknown` 억제 ③ 워커 신호 부재(PM 직접 수행 행) ④ `--action-step N/M`에서 `N<M`(행이 `in_progress`로 남는 중간 진행 보고). 추가로 `owner = "user"`인 사용자 확인 행과 `--auto-pass` 재호출 멱등 no-op(093 F-005) 경로도 제외된다
  - 경고 코드는 `ERROR_CODES`가 아니라 별도 사전 `WARNING_CODES`에 산다 — 경고는 에러가 아니며, **103은 에러 코드를 늘리지 않았다**(103 시점 45종 유지. 이후 106 F-004가 `code_scan_citation_unmet` 1종, 111 W-1이 `plan_contract_unmet` 1종, 118 W-4가 finalize-attribution 전용 4종, 122 W-2가 `actor_unsupported_for_skill` 1종, 134 W-2가 `state_json_malformed` 1종을 등재해 현재 실측은 **53종**이며, 경고/에러 사전 분리 자체는 불변이다)
- `--worker-duration-unknown`(103 R-21)은 그 행의 워커 소요를 **알 수 없음을 명시**한다(중단된 워커·PM 직접 수행·소급 불가 과거 데이터). 경고를 억제하며 행에는 필드를 만들지 않는다 — 기록 결과는 인자 미지정과 완전히 동형이므로 "미측정"이 `0`("측정했으나 1분 미만")으로 오독되지 않는다
  - `--worker-duration-minutes`와 **배타적**이다(값과 미상 선언은 동시에 성립할 수 없음). 둘 다 지정하면 argparse가 exit 2로 거부한다 — `--owner`/`--auto-pass` 배타와 동일 계열이므로 전용 에러 코드는 신설하지 않았다
- `--auto-pass` 사용 시 `owner = "auto"`, note에 "agentic auto-pass" 자동 기재
- `--auto-pass`는 직접 명시한 자동 승인 옵션이며, CLOSE 진입의 mode-aware 자동 전이는 다음 행 `advance`/`mark`의 내부 원자 경로가 수행한다. 정상 semi-agentic/agentic CLOSE 경로에서 `agentic_close_gate_requires_user`는 방출하지 않는다. 오류 코드는 하위호환 카탈로그로만 유지한다.
- `--force` 사용 시 `--note` 필수 + 의사결정 로그 자동 기재
- `state.json` `next_action`이 파이프라인 프론티어(첫 미완료 행)에서 자동 파생·갱신된다. `--next-action <text>` 지정 시 해당 값이 파생값보다 우선하며, 이 오버라이드는 **해당 전이 1회에만** 적용된다 — 다음 전이가 `--next-action` 없이 실행되면 자동 파생으로 복귀한다(072). **094부터 STATE.md에 이를 렌더하는 `## 다음 액션` 섹션은 없다** — 현재 상태 조회는 `show`로 한다
- 신규 CLOSE tail pipeline은 `close.final` 행이 완료될 때만 `current_status=completed_unmerged`를 확정한다. `close.final`이 없는 legacy 단일 CLOSE pipeline은 기존처럼 CLOSE 마지막 행 완료를 final로 인정한다.
- STATE.md는 `> 최종 갱신:` 헤더 타임스탬프 갱신 + (의사결정 있을 시) `## 의사결정 로그` 표에 1행 자동 추가(저널 후처리, 094)
- `--note`의 `{owner_name}` 플레이스홀더는 identity.md `owner_name`으로 write-time 치환된다(`--auto-pass` 접두 "agentic auto-pass: " 뒤에도 적용). 부재/공란/파싱 실패 시 원문 유지(fail-safe) — 054

---

### 5. `block` — any→❌ + current_status=blocked

```bash
~/.opal/tools/state-tool/run.sh block <task-path> \
  (--task-step <key> | --task-step-id <n> | --row <n>) \
  --reason <text>
```

- 행 주소는 `--task-step`(key) / `--task-step-id`(숫자) / `--row`(숫자, deprecated 별칭) 중 정확히 하나 (070 R-4)
- 행 상태 `failed`(❌) + `current_status` → `blocked` 자동 전환(`state.json`)
- STATE.md는 `> 최종 갱신:` 헤더 타임스탬프만 갱신된다 — **094부터 `- 상태:` 자동 렌더 섹션은 없다**, 현재 상태 조회는 `show`로 한다
- 의사결정 로그 자동 기재 안 함 (`## 블로커` 자유 기재 섹션은 PM이 직접 작성)
- `--reason`의 `{owner_name}` 플레이스홀더는 identity.md `owner_name`으로 write-time 치환된다(`note`는 `"block: {치환결과}"`). 부재/공란/파싱 실패 시 원문 유지(fail-safe) — 054

---

### 6. `validate` — 정합성 검증

```bash
~/.opal/tools/state-tool/run.sh validate <task-path>
```

검증 항목:
- 스키마 필수 필드 존재 여부
- 사용자 확인 행 `owner` 정합성
- interactive 모드에서 `owner=auto` 사용 여부
- semi-agentic 모드에서 EXECUTE-equivalent 이전 행 `owner=auto` 사용 여부 (`semi_agentic_pre_execute_auto_pass_denied`)

> 094: STATE.md 마커 존재 여부 검사는 저널화로 제거되었다 — `validate`는 더 이상 마커 유무를 판정하지 않는다(`marker_missing` 소멸).

**응답 예시**:
```json
{"ok": true, "command": "validate", "violations": [], "violations_count": 0}
```
```json
{"ok": false, "command": "validate", "violations": [{"code": "user_confirmation_owner_mismatch", "row_id": 12, "detail": "owner=None"}], "violations_count": 1}
```

---

### 7. `add-row` — 추가작업 행 삽입

```bash
~/.opal/tools/state-tool/run.sh add-row <task-path> \
  (--after-task-step <key> | --after-task-step-id <n> | --after <n>) \
  --stage <stage> \
  --item <항목명> \
  [--key <key>] \                           # 070 R-9: 명시 지정 (미지정 시 자동 생성)
  [--note <text>]
```

- 앵커 행 주소는 `--after-task-step`(key) / `--after-task-step-id`(숫자) / `--after`(숫자, deprecated 별칭) 중 정확히 하나 (070 R-4) — 그 행 직후에 새 행 삽입 (row_id 전체 재정렬, 기존 행 key는 불변)
- 신규 행의 `key`는 `--key` 명시 지정(형식 위반 시 `task_step_key_invalid`, 기존 key와 중복 시 `task_step_key_duplicate`) 또는 미지정 시 `{stage_slug}.{item_slug}_{n}` 자동 생성(파일 내 유일성 보장, 070 R-9)
- `current_status == "done"` → `additional_work` 자동 전환
- `current_status == "additional_work_done"` → `additional_work` 자동 회귀
- 의사결정 로그 자동 기재 (§2.17 트리거 #5)
- `--note`의 `{owner_name}` 플레이스홀더는 identity.md `owner_name`으로 write-time 치환된다. 부재/공란/파싱 실패 시 원문 유지(fail-safe) — 054

**성공 응답**:
```json
{"ok": true, "command": "add-row", "row_id": 11, "key": "test.fix_1", "rows_count": 21, "current_status": "additional_work"}
```

---

### 8. `status` — current_status 명시 전환

```bash
~/.opal/tools/state-tool/run.sh status <task-path> \
  --set <in_progress|done|blocked|additional_work|additional_work_done> \
  [--note <text>]
```

허용 전이 그래프:
- `in_progress` → `done` / `blocked` / `additional_work`
- `done` → `additional_work` / `blocked`
- `blocked` → `in_progress` / `done`
- `additional_work` → `additional_work_done` / `blocked` / `in_progress`
- `additional_work_done` → `additional_work` / `blocked`

위 그래프 외 전이 시도: `invalid_status_transition` + exit 1

`--note`의 `{owner_name}` 플레이스홀더는 identity.md `owner_name`으로 write-time 치환된다(의사결정 로그 근거에 반영). 부재/공란/파싱 실패 시 원문 유지(fail-safe) — 054

---

### 8a. `run-start` — 새 run_id 발급 (131 D8)

```bash
~/.opal/tools/state-tool/run.sh run-start <task-path>
```

- 새 `run_id`를 발급해 `state.json.run_id`에 기록한다.
- 형식: `run-<UTC YYYYMMDDHHMMSS>-<8자리 소문자 hex>` (정규식 `^run-[0-9]{14}-[0-9a-f]{8}$`). 타임스탬프만 UTC이며 `created_at`/`updated_at`의 KST 표기와 다르다.
- 현재 run은 항상 1개다. 재호출하면 새 id로 **교체**하며 이력을 누적하지 않는다(`runs`/`run_ids` 같은 목록을 만들지 않는다).
- `run_id`는 optional 필드다. `init`은 만들지 않고, 스키마 `required` 8필드는 불변이며, `run_id` 없는 기존 `state.json`도 계속 `validate`를 통과한다.
- `show --format json`의 `data.run_id`로 통과한다. `run_id`를 소유·발급하는 것은 `state-tool`이며 다른 도구는 외래 참조로만 복제한다.

```json
{"ok": true, "command": "run-start", "run_id": "run-20260914081530-3f9a1c7e", "previous_run_id": null}
```

---

### 8b. `finalize-attribution` — 허브 MEMORY history 귀속 (118 D-4b / AC-4)

```bash
~/.opal/tools/state-tool/run.sh finalize-attribution <task-path> \
  --allocator-root <절대경로>
```

- CLOSE 마지막 행 `mark`에서 분리된 허브 `.opal/MEMORY.json` history append를 이 명령이 전담한다. merge 확인 뒤 허브 PM이 worktree registry 발급값을 `--allocator-root`로 넘겨 호출한다.
- **[MUST] `allocator_root`는 추론하지 않는다** — cwd·task path 조상·`.opal-worktrees` 문자열 어느 것도 근거로 쓰지 않는다. 미지정은 `allocator_root_required`, 상대경로는 `allocator_root_not_absolute`, 하위에 `.opal/MEMORY.json`이 없으면 `allocator_root_invalid`로 거부한다(모두 exit 1).
- **멱등**: 동일 `path` 행이 이미 있으면 append를 건너뛰고 `duplicate_skipped`로 응답한다(exit 0).
- append 실패(memory-tool 부재·손상 JSON·호출 실패)는 `finalize_attribution_failed` — 파일은 변경되지 않는다.

---

### 8c. `boot-summary` (별칭 `boot-brief`) — 부트 요약 (read-only)

```bash
~/.opal/tools/state-tool/run.sh boot-summary <project-root>
```

- `session.project` 부트스트랩용으로 허브 `tasks/`의 직접 수행 태스크와 worktree registry가 발급한 canonical `task_path`의 진행 태스크를 합친 **읽기 전용** 요약을 낸다. task-path가 아니라 허브 **project-root**를 받는다.
- 후보는 `updated_at` 최신순이며 최대 3건을 `items`로 반환한다. 표시 밖의 유효 후보는 `other_count`, canonical 경로를 확정할 수 없는 registry 상태는 정상 후보와 분리된 bounded `anomalies`로 반환한다. worktree 경로·상태 판정의 원문은 `opal/core/references/harness/worktree.md` §canonical path 발급 계약·§상태 의존 해석이 소유한다.
- 출력은 UTF-8 1024 bytes 이하로 제한된다 — 초과 시 `title`/`stage`/`next_action`과 anomaly detail을 길이 순으로 줄이며, 항목 구조·잔여 건수·anomaly code와 유효한 단일 JSON을 유지한다.
- `boot-brief`는 동일 구현·동일 출력 계약의 별칭이다.
- 상태 파일을 쓰지 않는다.

```json
{"ok": true, "command": "boot-summary", "items": [{"title": "...", "stage": "...", "next_action": "..."}], "other_count": 2, "anomalies": [{"code": "task_path_ambiguous"}]}
```

---

### 9. `gate-pass` — Gate 4행 일괄 ✅ 처리 **[deprecated — 레거시 전용]**

```bash
~/.opal/tools/state-tool/run.sh gate-pass <task-path> \
  --start <N> \
  [--note <text>]
```

> **[deprecated] 신규 태스크에서 사용하지 않는다** (014 Phase 4). 새 표준 행 구조에는 "QA Gate"/"State Gate" 행이 없어 `[QA Gate, State Gate, PM Gate, State Gate]` 4행 패턴 자체가 성립하지 않는다 — PM Gate는 통과 후 **단일 `mark`**로 닫는다. 레거시 `state.json`(해당 4행이 실재하는 태스크)에서만 동작하며, 성공 응답에 `deprecated: true`와 `deprecation_note`가 실린다. 후속 버전에서 제거 예정.

- 행 N부터 4행이 `[QA Gate, State Gate, PM Gate, State Gate]` 패턴이어야 함
- 4행 모두 동일 stage여야 함
- 4행 모두 동일 timestamp로 ✅ 처리
- 의사결정 로그 자동 기재 (§2.17 트리거 #6)

**성공 응답**:
```json
{"ok": true, "command": "gate-pass", "rows_passed": [6, 7, 8, 9], "stage": "PLAN", "timestamp": "2026-05-01 18:00"}
```

---

### 10. `spec-validate` — pipeline.json 스펙 검증 (070 R-6)

```bash
~/.opal/tools/state-tool/run.sh spec-validate <pipeline.json 경로>
```

- task-path가 아닌 **pipeline.json 파일 경로**를 받는 유일한 서브 명령
- 검사 항목: 필수 필드(spec_version/skill/meta/task_steps) 존재, skill enum 정합, `task_steps[].stage` STAGE_ENUM 정합, key 형식(`^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*(_[0-9]+)?$`), key 유일성, id 1..N 순차, key의 stage_slug와 실제 stage 정합
- `init --rows-from <pipeline.json>`이 내부적으로 동일 검증을 재사용한다(공유 단일 검증 지점)

**성공 응답**:
```json
{"ok": true, "command": "spec-validate", "violations": [], "violations_count": 0}
```
**실패 응답**:
```json
{"ok": false, "command": "spec-validate", "violations": [{"code": "spec_key_duplicate", "id": 2, "key": "plan.pm_gate", "detail": "..."}], "violations_count": 1}
```

---

### 11. `event-verify` — 이벤트 receipt 검증

파일럿과 단계 진입 전에 event-loader가 발급한 receipt를 검증한다. 이 명령은
`state.json`과 `STATE.md`를 읽거나 쓰지 않으며 기존 `advance`/`mark` 호출 계약도 바꾸지 않는다.

```bash
~/.opal/tools/event-loader/run.sh load --event stage.execute > /tmp/stage.execute.json
~/.opal/tools/state-tool/run.sh event-verify \
  --event stage.execute --receipt /tmp/stage.execute.json
```

- 성공하려면 요청 event, manifest hash, 필수 문서 집합, 경로, sha256, bytes가 모두 현재 값과 일치해야 한다.
- receipt 누락, wrong-event, stale manifest, 문서 누락·변경은 event-loader의 구조화 오류와 non-zero 종료 코드를 그대로 반환한다.
- 파일럿은 load 응답의 `documents[].content` 전문을 적용한 뒤 이 명령이 성공해야 해당 단계 작업을 시작할 수 있다.

---

### `log-event` — PM 활동·보고 사건 기록

```bash
~/.opal/tools/state-tool/run.sh log-event <task-path> --event activity ...
~/.opal/tools/state-tool/run.sh log-event <task-path> --event pm.report ...
```

- `--event`는 `activity`와 `pm.report` 두 값만 수용한다. `stop.decision`은 Stop receipt를
  소비하는 내부 drain 경로가 제출한다.
- `activity`는 기존 `--kind` 경로를 유지한다. `pm.report`는 구조화 보고 인자를 받아 기록 코어의
  결정론 renderer를 사용하며, 호환용 `--summary` 문자열은 저장하지 않는다.
- `pm.report`가 admission을 통과하면 사건과 `run_log.last_report` 포인터가 같은 원자 쓰기에서
  갱신된다. 거부되면 둘 다 바뀌지 않는다.
- 사건별 필드·폐쇄 규칙을 이 README에 복제하지 않는다. CLI 계약은
  `docs/run-log/CONTRACT.md` §1.2·§1.3.1·§1.4·§2.4를 따른다.

---

### `design-gate` — PM 경로 독립 설계 게이트 (157)

```bash
~/.opal/tools/state-tool/run.sh design-gate start  <task-path> --iteration N
~/.opal/tools/state-tool/run.sh design-gate record <task-path> --iteration N \
  --verdict pass|rewrite|input_error --evaluator-result <json> [--rewrite-target plan|scenario|both]
~/.opal/tools/state-tool/run.sh design-gate reset  <task-path> --owner user --note <사유>
```

- PM 경로(rows에 key `plan.design_gate` 존재) 태스크에서만 동작하고, 그 외는 `design_gate_not_applicable`. 흐름·해시·상한 규칙 원문은 `opal/core/references/harness/design-gate.md`가 소유한다.
- 상태는 `state.json` `design_gate` 블록(`status` idle/evaluating/pass/fail/retry_limit, `iteration`, `limit`=3, `limit_from`, `task_confirm_req_hash`, `current_attempt`, `passed_bundle_hash`, `approved_bundle_hash`, `last_rewrite_target`, `history[]`)이 소유한다.
- 문서 묶음 hash = sha256(`"TASK.md\n"+h1+"\nPLAN.md\n"+h2+"\nTEST-SCENARIO.md\n"+h3`). TASK 요구 hash = TASK.md `## Constraints`·`## Acceptance criteria` 본문 sha256.
- `start` 검사 순서: PM 경로 → `execute.implement` pending(`design_gate_locked`) → `retry_limit`(`design_gate_retry_limit`) → 열린 시도(`design_gate_attempt_open`, 단 열린 시도의 묶음 hash가 현재와 다르면 그 시도를 `superseded`로 닫고 진행) → `plan.design_gate` 앞 행 완료(`stage_transition_violation`) → 대상 문서 존재(`design_gate_input_missing`) → TASK 요구 hash(`task_reconfirm_required`) → `N = iteration+1`(`design_gate_iteration_invalid`) → 직전 verdict가 rewrite면 대상 문서 중 하나라도 불변이면 `rewrite_target_unchanged` → 결정론 검사. 결정론 검사 전 거부는 상태를 바꾸지 않는다.
- 결정론 검사: sdlc-v2 TASK 5절, 기존 PLAN 계약 검사 전 항목, 모든 AC/C의 Work item `완료 기준 연결`(`uncovered requirement AC-N`), `## Findings` H3 4소절(`직접 변경`·`회귀 확인`·`문서 갱신`·`미확인 가정`) 존재·비공백, `회귀 확인` 경로가 Work item `변경 대상` 또는 `직접 변경`·`문서 갱신`에도 있으면 `regression target listed as change`, `직접 변경`·`문서 갱신` 경로가 Work item `변경 대상`에 없으면 `finding not in work items`, `미확인 가정` 항목은 `없음` 또는 Risks의 `H-N` 참조, 형제 test-tool(`sys.executable test-tool/test_tool.py`) `scenario-coverage-build --template sdlc-v2` + `scenario-coverage-check`의 exit 0(16은 missing 병합, 17은 input_error). 실패는 `design_gate_deterministic_fail`(exit 1, `missing` 동봉)이며 시도 1회로 history에 `deterministic_fail`로 남고 상한 계산에 포함된다. `verify --plan-contract-check`는 이 strict 검사를 쓰지 않는다.
- `start` 통과: `status=evaluating`, `current_attempt` 기록, 통과·승인 hash 삭제, `plan.design_gate`→in_progress, done이던 `plan.user_confirm`→pending, run-log `gate.requested`(`gate_id=design-gate-i{N}`)를 같은 커밋으로 기록.
- `record` 거부(상태 불변·시도 유지, 검사 순서): 열린 시도 없음·회차 불일치 `design_gate_iteration_invalid` → 묶음 변경 `design_gate_input_changed` → (`--verdict pass|rewrite`에 한해) `--evaluator-result` JSON 최상위 `input_bundle_hash`가 현재 열린 시도의 `bundle_hash`와 같고 `iteration`이 `--iteration` N과 같아야 하며, 없거나 다르면 `design_gate_result_stale`(ADD-1, 157) → pass·rewrite에서 `design.axes` 4키(`completeness`·`decision_clarity`·`executability`·`recoverability`)·`scenario.scores` 3키(`goal`·`adoption`·`boundary`) 누락이나 rewrite의 `--rewrite-target` 누락 `design_gate_result_invalid` → pass인데 4축 전부 PASS·시나리오 각 ≥1·평균 ≥1.5가 아니면 `design_gate_verdict_mismatch`. `input_error`는 `design_gate_result_stale`·축 검사 모두 대상이 아니다(파일 부재·파싱 실패·`input_bundle_hash` 부재 허용). evaluator에게 넘기는 판정 입력에는 `input_bundle_hash`(=`design-gate start` 응답의 `bundle_hash`)를 반드시 포함해야 하며, evaluator는 결과 JSON 최상위에 그 값과 `iteration`을 그대로 반환해야 한다.
- `record` 성공: pass→`status=pass`, `passed_bundle_hash`, `plan.design_gate` done. 그 외→`status=fail`, `iteration - limit_from ≥ limit`이면 `status=retry_limit`과 `transition_action=await_user`·`report_type=decision_request`. 모두 history에 추가하고 run-log `gate.resolved`(`data.verdict` pass→`approved`, 그 외→`rejected`, 원문 verdict는 summary)를 같은 커밋으로 남긴다.
- `reset`: `--owner user`가 없으면 `user_confirmation_required`. `retry_limit`일 때만 `status=idle`, `limit_from=iteration`으로 해제하고 STATE.md 의사결정 로그에 기록한다(history·회차 번호 유지). 그 외 상태에서는 변경 없이 `reset: false`로 성공한다.
- `advance`/`mark` 가드(PM 경로, 자동 승인 직후·저장 전, `--force` 우회 불가): `task.user_confirm`이 done이 되는 순간 `task_confirm_req_hash` 기록. `plan.user_confirm`이 done이 되는 순간 현재 묶음이 `passed_bundle_hash`와 다르면 `design_bundle_mismatch`, 같으면 `approved_bundle_hash` 기록. 자동 승인 불가 mode에서 `--owner user` 없는 확인 행 mark는 `user_confirmation_required`. `mark plan.design_gate --done`은 `status=pass`·현재=통과 hash일 때만(`design_gate_not_passed`/`design_bundle_mismatch`). `execute.implement`가 pending에서 진입할 때 `status=pass`(`design_gate_not_passed`) → TASK 요구 hash 일치(`task_reconfirm_required`) → 현재=통과=승인 hash(`design_bundle_mismatch`)를 요구한다.

### `design-decision` — PM 경로 설계 결정 분류 기록 (157)

```bash
~/.opal/tools/state-tool/run.sh design-decision <task-path> --scope external|detail --summary <text> --basis <text>
```

- PM 경로 PLAN 단계에서만 허용한다. PM 경로가 아니면 `design_gate_not_applicable`, `execute.implement`가 pending이 아니면 `design_gate_locked`, 첫 미완 행이 PLAN이 아니면 `stage_transition_violation`.
- `detail`: STATE.md 의사결정 로그 + PM `activity`(decision) 사건 기록, `transition_action=continue`.
- `external`: `plan.plan_md` 행을 `block`과 같은 방식으로 failed·`current_status=blocked` 처리하고 STATE.md 의사결정 로그를 남긴다. `transition_action=blocked`·`report_type=decision_request`. 해소는 기존 `status --set`·`advance` 재개 경로.
- 두 scope 모두 기록 성공이므로 `ok: true`·exit 0이다.

---

### `verify` — TEST-SCENARIO.md 검증 + TASK/PLAN 게이트 (013/016/005/098/100/111)

위 11개 번호 명령과 별개로 동작하는 검증 전용 명령. task-path 하나에 여러 독립
분기(mock 패턴/증거 누락 검사, `--red-check`, `--fix-mode`, `--clarification-check`,
`--evidence-check`, `--plan-contract-check`, `--code-scan-citation-check`)가 있으며 각 분기는
조기 반환한다 — 동시 지정 가능 조합은 플래그별 계약을 따른다
(`--clarification-check`·`--evidence-check`·`--plan-contract-check`·`--code-scan-citation-check`
4종은 서로 동시 지정 불가, 아래 참조).

```bash
~/.opal/tools/state-tool/run.sh verify <task-path> --evidence-check [--task-md <path>]
```

- `--evidence-check`: TASK.md의 **두 곳**을 근거 등급 4축(① 인용 존재 ② 인용
  유효(경로·줄 실존) ③ 등급 부여 ④ E5 단독 아님)으로 판정하여 항목별
  확정/미확정 + 사유를 반환하는 **라우터**다 — 미충족이어도 차단하지 않는다
  (exit code 항상 0). PM이 반환된 `unconfirmed`를 검토해 판단으로 확정 승격할
  수 있다(098, PLAN §3.3.2 / 100 §3.7.2).
  - **파싱 대상 ①** `## 명확화 결과` **표**의 `의존 사실` 열 → `source:
    "clarification"` (098부터).
  - **파싱 대상 ②** `## 확정된 설계 방향` 섹션의 **최상위 불릿** → `source:
    "confirmed_direction"` (100부터). 표가 아니라 불릿 리스트이므로 전용 파서로
    수집하며, 표의 열 구성에는 아무 영향이 없다. 중첩(들여쓴) 불릿은 항목으로
    수집하지 않고, `element`에는 불릿 본문 원문이 그대로 담긴다(어떤 항목이
    미확정인지 PM이 식별할 수 있어야 하므로 인덱스형 라벨을 쓰지 않는다).
- `items[]`의 `source` 필드가 두 출처를 구분한다(`"clarification"` |
  `"confirmed_direction"`). 두 소스는 하나의 `items[]`로 병합되지만 **비율
  분모는 공유하지 않는다** — 아래 `confirmed_ratio` / `direction_confirmed_ratio`
  참조.
- `--task-md <path>`: TASK.md 경로 명시(기본 `<task-path>/TASK.md`).
- `--clarification-check`와 동시 지정 시 `evidence_check_flag_conflict`로 거부(exit 1) — 같은 표를 서로 다른 반환 계약(차단형/라우터형)으로 동시에 소비할 수 없다.
- TASK.md 부재, `## 명확화 결과` 섹션/표 부재, `의존 사실` 열 부재는 모두 하위호환
  graceful skip(`evidence_check: "skipped"`, exit 0) — 레거시 TASK.md 회귀 없음.
  `## 확정된 설계 방향` 섹션 부재·항목 0건도 마찬가지로 조용히 건너뛴다
  (`direction_confirmed_ratio: null`, 분모 0 나눗셈 없음).
- 인용 형식 4종: `` `경로:N` ``/`` `경로:N-M` `` (등급 매핑 + 파일·줄 실존 검사) /
  `` `경로` §N `` (등급 매핑 + 경로 존재만) / `[사이트명](URL)` (네트워크 접근
  금지, `grade:"unknown"`) / `(→ D-N §N)` 단축 참조(테이블 역참조 미해석,
  `grade:"unknown"`). 디렉토리 없는 파일명 단독 토큰(`/` 없음)도 저장소 탐색 없이
  `grade:"unknown"`.
- 등급 패턴 기본 세트(1차): `.opal/brain/**`·`.opal/code-scan.json`·`*code-map*` →
  E5 / `docs/**`·`*.md` → E4 / `**/tests/**`·`test_*.py` 및 코드 확장자(`.py .ts
  .tsx .js .sh .json`) → E2 / 그 외 → `unknown`. E1(실행 관측)·E3(생성 코드)은
  경로 패턴으로 판별 불가하므로 자동 부여 대상이 아니다(항상 `unknown`).
- `unknown` 등급은 `confirmed_ratio` 계산에서 미확정으로 계상한다(분자 제외·
  분모 포함) — 근거 없음은 완료가 아니라는 원칙의 도구 집행이다.
- **verdict 3종**: `확정` / `승계` / `미확정`.
  - `확정` — `[결정]` 태그 보유(캡틴 결정은 근거 판정 면제) 또는 4축 통과.
  - `승계` — `[사실]` 태그 + 유효 인용(E2/E4 + 실존)으로 4축 통과. 상류에서 이미
    대조 확인된 사실을 승계했다는 표시이며(재확인 면제), **계수상 `확정`과
    동등하게 confirmed로 집계**된다(100).
  - `미확정` — 인용 부재/경로 부재/등급 unknown/E5 단독 등. `unconfirmed[]`에
    오르며, 두 출처의 미확정 항목이 함께 담긴다.

**성공 응답(라우터)**:
```json
{
  "ok": true, "command": "verify", "evidence_check": "routed",
  "items": [
    {"element": "목표", "verdict": "확정", "reasons": [],
     "citations": [{"raw": "`opal/tools/state-tool/state_tool.py:100`", "grade": "E2", "exists": true}],
     "source": "clarification"},
    {"element": "제약", "verdict": "미확정", "reasons": ["citation_missing"], "citations": [],
     "source": "clarification"},
    {"element": "`[사실]` evidence-check는 라우터다 (`opal/tools/state-tool/README.md:267`).",
     "verdict": "승계", "reasons": [],
     "citations": [{"raw": "`opal/tools/state-tool/README.md:267`", "grade": "E4", "exists": true}],
     "source": "confirmed_direction"}
  ],
  "confirmed_ratio": 0.5, "direction_confirmed_ratio": 1.0,
  "unconfirmed": ["제약", "완료기준"]
}
```
`evidence_check`는 `"pass"`(confirmed_ratio 1.0) / `"routed"`(일부 미확정) /
`"skipped"`(graceful skip) 중 하나이며, exit code는 항상 0이다.

**두 비율 키는 분모가 다르다**(100 PD-1 — 분리형):

| 키 | 분모 | 분자 |
|----|------|------|
| `confirmed_ratio` | `## 명확화 결과` 4요소 항목 수 **고정(불변)** | 그중 `확정`+`승계` |
| `direction_confirmed_ratio` | `## 확정된 설계 방향` 최상위 불릿 수 | 그중 `확정`+`승계` |

`confirmed_ratio`의 분모에 방향 항목이 섞이지 않는다 — 기존 소비자의 의미를
바꾸지 않기 위한 의도적 분리다. `direction_confirmed_ratio`는 섹션 부재 또는
항목 0건일 때 `null`이며, `evidence_check` 상태값(`pass`/`routed`) 판정에는
관여하지 않는다(기존 `confirmed_ratio` 단독 기준 유지).

**플래그 충돌 응답**:
```json
{"ok": false, "command": "verify", "error": "evidence_check_flag_conflict", "message": "..."}
```

---

#### `--plan-contract-check` — sdlc-v2 Work items 실행 계약 게이트 (111)

```bash
~/.opal/tools/state-tool/run.sh verify <task-path> --plan-contract-check
```

- 첫 YAML frontmatter가 정확히 `template: sdlc-v2`인 `PLAN.md`만 검사한다. legacy
  PLAN은 `plan_contract_check:"skipped"`, `reason:"legacy_plan"`, exit 0으로 명시 skip한다.
- 검사 항목: `Work items` 표의 7개 열(`작업/담당/변경 대상/구체적 변경/선행 작업/실행 그룹/완료 기준 연결`),
  W-ID 존재·중복, 빈 내용, 선행 W 참조 실존, 순환, P그룹 순서, 같은 P그룹 파일 충돌,
  완료 기준 연결의 AC/C 참조와 W별 최소 1개 AC/C 연결.
- 위반 시 `plan_contract_unmet`으로 exit 1이며 `missing`/`violations`에 상세 사유,
  `work_items`에 파싱된 W-ID 목록을 반환한다. 정상 시 `plan_contract_check:"pass"`와
  `work_items`/`work_item_ids`를 반환한다.
- `TASK.md`의 `Acceptance criteria`와 `Constraints`에서 추출한 AC/C ID를 참조 분모로 쓴다.
  W는 실행 단위이므로 기능 coverage의 F로 변환하지 않는다.

---

#### `--code-scan-citation-check` — code-scan 결과 인용 게이트 (106)

```bash
~/.opal/tools/state-tool/run.sh verify <task-path> --code-scan-citation-check
```

- **판정 대상**: `<task-path>/PLAN.md`의 sdlc-v2 `Work items` 변경 대상 또는 legacy §4.2 실행 체크리스트 본문. 그 안에 code-scan 결과
  인용 토큰(`domain`/`layer`/`depends`/`exports` 및 `discover`/`scaffold`/`target`/`validate`/`feature`
  결과 필드)이 1건 이상 존재하는지 판정한다. 디스패치 프롬프트는 파일로 남지 않으므로,
  **파일로 영속되고 워커에 그대로 전달되는 PLAN.md Step 본문**을 증거로 삼는다.
- **반환** `code_scan_citation_check`: `pass` | `skipped` | `unmet` (도메인 3값으로 닫힘).
  `exit`: `pass`·`skipped` → 0 / `unmet` → 1 (`error: code_scan_citation_unmet`).
- **스킵 `reason` 3값** — **[MUST] 판정보다 앞에 평가한다.** 순서 자체가 계약이며, 아래로
  내리면 조용히 통과해야 할 태스크에서 거부가 발생한다:
  1. `code_scan_unavailable` — `.opal/code-scan.json` 부재 또는 `headerSource` ∉ {`inline`, `manifest`}
  2. `plan_md_absent` — PLAN.md 부재 (하위호환)
  3. `doc_only_task` — §4.2 대상 파일에 code-scan 적용 확장자 0건 (순수 문서 태스크)
- **집행 지점 2곳**: ① 위 라우터(PM 수동 호출) ② **EXECUTE 단계 첫 행 진입 시
  `advance`/`mark`의 자동 훅** — 동일 판정을 재실행해 진입 자체를 차단한다. 거부는
  `save_state_json()` **이전** 검증 구간이므로 `state.json`·`STATE.md`가 오염되지 않는다.
  우회는 `--force --note`만 가능하며(의사결정 로그에 남는다), `--auto-pass`로는 우회할 수 없다.
- `--clarification-check`·`--evidence-check`·`--plan-contract-check`와 동시 지정 시 `evidence_check_flag_conflict`로 거부(exit 1).
- 신규 영속 필드 0건 — `state.json`·`STATE.md`·`schema/*.json`은 변경되지 않는다.
- 규정 SSOT: `opal/core/references/harness/pm-review-gate.md` §표준 검토 항목 14.

---

#### `--run-log-completeness-check` — run-log 완전성 진단 (135 W-4, read-only·비차단)

```bash
~/.opal/tools/state-tool/run.sh verify <task-path> --run-log-completeness-check
```

- `state.json`의 현재 행·자동 승인 흔적과 기록 사건(조각+보관함)을 대조해 자동 승인을 포함한
  기록 누락을 진단한다. **read-only이며 exit 0 고정** — 완료 여부를 뒤집지 않는다.
- `run-log-tool validate-run`(조각 자체의 순번·스키마·provenance 검증)과는 별개 축이다.
  이 검사만 `state.json`과 대조한다 — `run-log-core`가 상태 파일을 읽지 않는 단방향 의존
  때문에 이 대조는 `state-tool`만 수행할 수 있다(CONTRACT §2.5·§3.1).
- 반환: 기존 누락 목록 4종(`missing_state_changed`/`missing_pm_activity`/`missing_gate_event`/
  `unobserved_worker_boundary`)에 PM 보고·Stop 판정 진단 5종을 더한 목록 9종과 관측 지점 3필드(`last_observed_decision`/
  `last_observed_state_change`/`last_observed_boundary`, 각 `{event_id, ts, ref}` 또는 `null`).
  새 진단 이름과 판정식은 `docs/run-log/CONTRACT.md` §2.5가 소유한다. 3필드는 누락 목록과
  무관하게 항상 반환된다.
- `missing_pm_activity`는 앵커 2종을 대조해 대응 PM `activity(decision)`가 없으면 1건씩 싣는다 —
  ① `status=done`·`owner=auto`·`key` 보유 행에 `task_step` 일치 사건이 없으면 그 행마다 1건,
  ② `run_log.status=overridden`인데 run 전역에 사건이 0건이면 배열 마지막에 1건. 항목은
  `row_id`·`row_key`·`stage`·`expected`·`anchor` 5키다. 대조 집합·정렬·범위 한정을 포함한
  정확한 조문은 CONTRACT §2.5가 소유한다.
- `run_log` 블록이 없는 1.0/1.1 태스크는 모든 목록이 비고 3필드가 전부 `null`이다.
- 필드·enum의 계약 원문은 CONTRACT.md §2.5·§1.4/§1.5가 소유한다. 여기서 복제하지 않는다.

## `--rows-spec` 입력 형식

```bash
~/.opal/tools/state-tool/run.sh init <task-path> \
  --skill opp --mode interactive \
  --rows-spec '[
    {"stage": "TASK", "item": "작업"},
    {"stage": "TASK", "item": "사용자 확인"},
    {"stage": "PLAN", "item": "작업"},
    {"stage": "PLAN", "item": "PLAN.md 생성"},
    {"stage": "PLAN", "item": "QA Gate"},
    {"stage": "PLAN", "item": "QA-PLAN.md 생성"},
    {"stage": "PLAN", "item": "State Gate"},
    {"stage": "PLAN", "item": "PM Gate"},
    {"stage": "PLAN", "item": "State Gate"},
    {"stage": "PLAN", "item": "사용자 확인"},
    {"stage": "CLOSE", "item": "DONE.md 생성"},
    {"stage": "CLOSE", "item": "State Gate"}
  ]'
```

---

## 사용 예시

행 주소는 `--task-step <key>` / `--task-step-id <n>` 중 하나를 쓴다(`--row`는 deprecated 별칭).

```bash
# TASK 단계 시작 — pipeline.json에서 행 구성 자동 파싱
~/.opal/tools/state-tool/run.sh init tasks/134-.../ \
  --skill opp --mode interactive \
  --task-title "파이프라인 state-tool 도입" \
  --rows-from ~/.opal/skills/opal-pilot-project/references/pipeline.json

# 단계 시작 (⬜→🔄) / 단계 완료 (→✅)
~/.opal/tools/state-tool/run.sh advance tasks/134-.../ --task-step plan.work
~/.opal/tools/state-tool/run.sh mark    tasks/134-.../ --task-step plan.work --done

# 워커 EXECUTE Step 완료 (→✅, 권한 게이트 + 소요 기록)
~/.opal/tools/state-tool/run.sh mark tasks/134-.../ \
  --task-step execute.work --done --as-worker --worker-stage EXECUTE \
  --action-step 3/8 --worker-duration-minutes 12

# 사용자 확인 행 처리
~/.opal/tools/state-tool/run.sh mark tasks/134-.../ \
  --task-step plan.user_confirm --done --owner user \
  --note "{owner_name} 확인: PLAN 단계 검토 완료"

# PM Gate 전 정합성 검증 / 파이프라인 행 현황 출력(기본 마크다운)
~/.opal/tools/state-tool/run.sh validate tasks/134-.../
~/.opal/tools/state-tool/run.sh show     tasks/134-.../

# 추가작업 행 삽입 → 완료 상태 전환
~/.opal/tools/state-tool/run.sh add-row tasks/134-.../ \
  --after-task-step close.done_md --stage CLOSE --item "추가 검증" --note "추가작업 진입"
~/.opal/tools/state-tool/run.sh status tasks/134-.../ \
  --set additional_work_done --note "추가작업 완료"
```

---

## 에러 코드 카탈로그 (59종)

코드는 `state_tool.py`의 세 물리 분리 테이블이 소유한다. 기본 상태 오류는 `ERROR_CODES` 59종,
run-log 연동 오류는 `RUN_LOG_STATE_ERROR_CODES` 15종, 설계 게이트 오류는 `DESIGN_GATE_ERROR_CODES`
14종이다. `err()`가 조회 시에만 `ERROR_CODES` → `RUN_LOG_STATE_ERROR_CODES` → `DESIGN_GATE_ERROR_CODES`
순으로 합성하며, 종수는 문서가 아니라 코드의 키 집합을 실측한다. 이 절 헤딩의 종수는 `ERROR_CODES` 기준이다.

### 설계 게이트 오류 (14종, 157)

| 코드 | 의미 |
|---|---|
| `design_gate_not_applicable` | PM 경로가 아닌 태스크에서 설계 게이트·설계 결정 명령 호출 |
| `design_gate_locked` | `execute.implement`가 pending이 아닌 상태에서 `start`·`design-decision` 호출 |
| `design_gate_attempt_open` | 묶음이 그대로인 열린 시도가 있는 상태에서 새 `start`(먼저 `record`) |
| `design_gate_retry_limit` | 반복 상한 도달, `reset` 전 `start` 불가(사용자 대기) |
| `task_reconfirm_required` | TASK 요구 hash가 `task_confirm_req_hash`와 불일치(사용자 대기) |
| `design_gate_iteration_invalid` | `start`의 N≠iteration+1, `record`의 N≠열린 시도 회차 또는 열린 시도 없음 |
| `rewrite_target_unchanged` | 직전 rewrite 대상 문서 중 하나라도 직전 시도와 동일 |
| `design_gate_deterministic_fail` | 결정론 검사 실패(`missing` 동봉) |
| `design_gate_input_missing` | TASK/PLAN/TEST-SCENARIO 부재 |
| `design_gate_input_changed` | `record` 시점 묶음 hash가 시도 시작 시점과 다름 |
| `design_gate_result_stale` | evaluator 결과의 `input_bundle_hash`·`iteration`이 현재 열린 시도와 불일치(pass·rewrite만, ADD-1) |
| `design_gate_result_invalid` | evaluator 결과 필수 축 누락 또는 rewrite의 `--rewrite-target` 누락(pass·rewrite만) |
| `design_gate_verdict_mismatch` | `--verdict pass`인데 설계 4축·시나리오 기준 미충족 |
| `design_gate_not_passed` | `status≠pass`에서 `plan.design_gate` 완료·EXECUTE 진입 시도 |
| `design_bundle_mismatch` | 현재 묶음 hash가 통과·승인 hash와 불일치 |

### run-log 연동 오류 (15종)

| 코드 | 의미 |
|---|---|
| `profile_not_found` | active 초기화에 필요한 채널 profile 부재 |
| `run_log_missing` | 활성 계약의 기록 또는 필수 사건 부재 |
| `run_log_pending` | 보관함 사건 미전송 |
| `run_log_outbox_full` | 보관함 admission 상한 도달 |
| `run_log_write_failed` | 기록 append 실패 |
| `event_too_large` | 보관함 항목 크기 상한 초과 |
| `completion_evidence_missing` | active 완료 profile의 신뢰 증거 부족 |
| `worker_duration_conflict` | 명시 소요시간과 사건 파생값 불일치 |
| `task_path_not_absolute` | run-log 표면에 상대 task path 전달 |
| `task_lock_timeout` | 공용 task lock 대기 상한 초과 |
| `actor_not_allowed` | PM 전용 사건 표면에 다른 actor 지정 |
| `gate_not_requested` | 선행 `gate.requested` 부재 |
| `gate_duplicate` | 같은 gate 사건 중복 |
| `refs_invalid` | 허용되지 않는 절대경로 ref |
| `schema_invalid` | 폐쇄형 사건 스키마 위반 |

### 기본 상태 오류 (59종 실측 SSOT — PLAN §2.18 E-1 + 070 R-1/R-4/R-9 + 091 F-004 R-10/R-11 + 093 F-004 R-4 + 094 R-3/R-4/R-9 + 098 F-003 R-4 + 106 F-004 R-4 + 111 W-1 + 118 W-4 + 122 W-2 + 134 W-2 + 156 W-1)

> 종수는 `len(ERROR_CODES)`(`state_tool.py`) 실측값이 기준이다 — 이 헤더 숫자를 리터럴로 신뢰하지 말고 코드 실측으로 재검증할 것(094 R-9 ①, S-7/S-15).

| # | 에러 코드 | 발생 명령 | 종료 코드 | 의미 |
|---|---------|---------|---------|------|
| 1 | `worker_scope_violation` | mark | 1 | 워커가 자기 단계 외 행 갱신 시도 |
| 2 | `already_initialized` | init | 1 | state.json 이미 존재 (`--force`로 우회) |
| 3 | `date_tool_failed` | 모든 갱신 명령 | 2 | date.js 호출 실패 |
| 4 | `import_existing_removed` | init(구 STATE.md 표 흡수 옵션 호출 시) | 1 | 해당 옵션 사용 시 항상 거부 — 파싱 대상이던 파이프라인 표가 STATE.md에서 소멸 (094 R-4/D-2) |
| 5 | `invalid_status_transition` | status | 1 | current_status 전이 그래프 위반 |
| 6 | `row_not_found` | mark/advance/block/add-row | 1 | --row N 행 미존재 |
| 7 | `invalid_stage_enum` | add-row | 1 | --stage 값이 16종 enum 외 |
| 8 | `gate_pattern_mismatch` | gate-pass | 1 | 4행 패턴 불일치 |
| 9 | `gate_stage_mixed` | gate-pass | 1 | 4행 stage 혼합 |
| 10 | `state_not_initialized` | show/advance/mark/block/validate/add-row/status/gate-pass | 1 | state.json 미존재 |
| 11 | `user_confirmation_owner_mismatch` | validate | 1 | 사용자 확인 행 owner 불일치 |
| 12 | `owner_flag_conflict` | mark | 1 | --owner와 --auto-pass 동시 사용 |
| 13 | `auto_pass_in_interactive_mode` | validate | 1 | interactive 모드에서 owner=auto |
| 14 | `close_gate_violation` | mark/advance | 1 | CLOSE 진입 게이트 위반 |
| 15 | `agentic_close_gate_requires_user` | mark | 1 | 하위호환 오류 코드. 레거시 직접 `--auto-pass` CLOSE 호출의 거부를 식별하며 정상 mode-aware 자동 전이에서는 방출하지 않음 |
| 16 | `semi_agentic_pre_execute_auto_pass_denied` | mark / validate | 1 | semi-agentic 모드에서 EXECUTE 등가 단계 이전 행에 --auto-pass 사용 불가 |
| 17 | `mode_flag_conflict` | (state init 포함 -- 향후) | 1 | 다중 모드 플래그 동시 사용 불가 |
| 18 | `note_required_for_force` | init --force / mark --force | 1 | --force 시 --note 미제공 |
| 19 | `rows_spec_invalid_json` | init --rows-spec | 1 | --rows-spec JSON 배열 아님 |
| 20 | `skill_md_parse_error` | init --rows-from | 1 | SKILL.md 행 추출 실패 |
| 21 | `task_path_not_found` | 모든 명령 | 1 | task-path 디렉토리 미존재 |
| 22 | `worker_stage_required` | mark | 1 | --as-worker 시 --worker-stage 미지정 |
| 23 | `rows_input_conflict` | init | 1 | --rows-spec과 --rows-from 동시 사용 |
| 24 | `rows_acts_not_implemented` | init --rows-acts | 2 | opsdd ACT 동적 주입 미구현 |
| 25 | `mock_in_scenario` | mark(TEST stage done 훅) | 1 | TEST-SCENARIO.md에 mock 코드 패턴 발견 (013) |
| 26 | `evidence_missing` | mark(TEST stage done 훅) | 1 | TEST-SCENARIO.md Pass 시나리오에 실행 증거 누락 (013) |
| 27 | `stage_transition_violation` | advance/mark | 1 | 단계 건너뛰기 차단 — 앞 행 미완료 (014 §M-A) |
| 28 | `red_evidence_missing` | verify --red-check | 1 | RED 증거(실패 출력) 누락 (016) |
| 29 | `test_modified_in_fix` | verify --fix-mode | 1 | fix 루핑 중 RED 테스트 파일 수정 감지 (016) |
| 30 | `clarification_gate_unmet` | verify --clarification-check / advance / mark | 1 | TASK 4요소 미잠금 — 다음 단계 진입 거부 (005) |
| 31 | `spec_file_not_found` | spec-validate / init --rows-from(.json) | 1 | pipeline.json 스펙 파일 없음 (070) |
| 32 | `spec_invalid_json` | spec-validate / init --rows-from(.json) | 1 | pipeline.json JSON 파싱 실패 (070) |
| 33 | `spec_validation_failed` | init --rows-from(.json) | 1 | pipeline.json 스펙 검증 실패(violations[0] 포함) (070) |
| 34 | `task_step_addr_required` | advance/mark/block/add-row | 1 | 행 주소 플래그 0개 지정 (070) |
| 35 | `task_step_addr_conflict` | advance/mark/block/add-row | 1 | 행 주소 플래그 2개 이상 동시 지정 (070) |
| 36 | `task_step_not_found` | advance/mark/block/add-row | 1 | `--task-step <key>` 미매칭(candidates 후보 목록 포함) (070) |
| 37 | `task_step_key_invalid` | add-row --key | 1 | `--key` 형식 위반(KEY_PATTERN) (070) |
| 38 | `task_step_key_duplicate` | add-row --key | 1 | `--key`가 기존 행 key와 중복 (070) |
| 39 | `gate_artifact_missing` | mark | 1 | PM Gate 산출물(`gate.artifacts`) 미충족 — 게이트 아티팩트 부재(`--force`+`--note`로만 우회) (091) |
| 40 | `spec_gate_type_invalid` | spec-validate / init --rows-from(.json) | 1 | `task_steps[].gate`가 object가 아님 (091) |
| 41 | `spec_gate_missing_field` | spec-validate / init --rows-from(.json) | 1 | `task_steps[].gate` 필수 필드(`artifacts`/`checklist`) 누락 (091) |
| 42 | `spec_gate_field_type_invalid` | spec-validate / init --rows-from(.json) | 1 | `task_steps[].gate` 필드 타입 오류(문자열 배열 필요) (091) |
| 43 | `spec_gate_checklist_empty` | spec-validate / init --rows-from(.json) | 1 | `task_steps[].gate.checklist`가 비어 있음 (091) |
| 44 | `user_confirmation_required` | advance/mark | 1 | 자동 승인 불가 구간의 사용자 확인 행 — 캡틴 승인 필요 (093) |
| 45 | `evidence_check_flag_conflict` | verify --evidence-check | 1 | `--evidence-check`와 `--clarification-check` 동시 지정 — 두 게이트 계약 충돌 (098) |
| 46 | `code_scan_citation_unmet` | verify --code-scan-citation-check / advance·mark(EXECUTE 첫 행 자동 훅) | 1 | `PLAN.md` §4.2 대상 파일에 코드 확장자가 있는데 §4.2 본문에 code-scan 결과 인용 토큰이 0건 — 또는 EXECUTE 첫 행 진입에 `--auto-pass`가 실려 우회 시도 (106) |
| 47 | `plan_contract_unmet` | verify --plan-contract-check | 1 | sdlc-v2 `PLAN.md` Work items 필수 열/W-ID/내용/선행/P그룹/파일 충돌/AC-C 연결 계약 위반 (111 W-1) |
| 48 | `allocator_root_required` | finalize-attribution | 1 | `--allocator-root` 미지정 — allocator_root는 cwd·task path 조상·`.opal-worktrees` 문자열로 추론하지 않는다 (118 W-4, AC-4) |
| 49 | `allocator_root_not_absolute` | finalize-attribution | 1 | `--allocator-root`가 상대경로 — 절대경로만 허용 (118 W-4, AC-4) |
| 50 | `allocator_root_invalid` | finalize-attribution | 1 | `--allocator-root` 하위에 `.opal/MEMORY.json`이 없음 (118 W-4, AC-4) |
| 51 | `finalize_attribution_failed` | finalize-attribution | 1 | 허브 MEMORY history append 실패(memory-tool 부재·손상 JSON·호출 실패) — 파일은 변경되지 않는다 (118 W-4, AC-4) |
| 52 | `actor_unsupported_for_skill` | init, resolve-start | 1 | actor 축(`init --actor`, `resolve-start --pm`)이 opd/opds 외 Pilot과 함께 지정됨 — actor 축은 opd/opds에서만 지원 |
| 53 | `state_json_malformed` | resolve-mode, resolve-start | 1 | `state.json`이 유효한 JSON 객체가 아니어서 저장 mode를 신뢰할 수 없음 — 명시 모드로도 자동 덮어쓰지 않고 복구를 요구 (134 W-2) |
| 54 | `workspace_flag_conflict` | resolve-start | 1 | `--wt`(`--worktree`)와 `--no-wt`를 함께 지정 |
| 55 | `actor_flag_conflict` | resolve-start | 1 | `--pm`과 `--no-pm`을 함께 지정 |
| 56 | `workspace_required_for_skill` | resolve-start, init | 1 | 프로젝트 worktree가 필수인 Pilot(oppb)에 허브 작업본(`--no-wt`, `init --workspace hub`)을 요청 — 조용히 무시하거나 허브로 폴백하지 않는다 |
| 57 | `resume_axis_locked` | resolve-start | 1 | 기존 태스크 재개 중 저장값과 다른 workspace·actor 플래그 — 응답 `axis`가 잠긴 축을 가리킨다 |
| 58 | `actor_pm_retired` | init | 1 | `--actor pm`(legacy PM 직접 수행)으로 신규 태스크를 만들려 함 — `coordinator`·`worker`만 허용, legacy `pm` 태스크는 재개만 지원 |
| 59 | `worktree_path_required` | init | 1 | `--workspace worktree`인데 `--worktree <worktree_root>`가 없음 — worktree 생성 실패 뒤 허브로 폴백하는 init을 막는다 |

> `spec-validate` 서브 명령 자체의 violations[] 내부 코드(`spec_missing_field`/`spec_skill_invalid`/`spec_stage_invalid`/`spec_key_format_invalid`/`spec_key_duplicate`/`spec_id_sequence_invalid`/`spec_key_stage_mismatch`)는 `cmd_validate`의 `schema_violation`처럼 인라인 문자열로 쓰이며 ERROR_CODES 템플릿을 거치지 않는다(070 §3.1.2). (`spec_gate_*` 4종은 동일하게 violations[]에 인라인 append되지만 ERROR_CODES에 등록되어 있어 위 카탈로그에 포함된다 — 091이 만든 예외.)

---

## 의존성

- `~/.opal/.venv/bin/python` — 표준 라이브러리만 사용 (`json`, `argparse`, `pathlib`, `subprocess`, `re`, `sys`, `datetime`, `os`)
- `~/.opal/tools/date/date.js` — KST 시점 취득 (node.js)
- `opal/tools/state-tool/schema/state.schema.json` — JSON Schema Draft-07 참조용 (1.0/1.1 병행)
- `opal/tools/state-tool/schema/pipeline-spec.schema.json` — pipeline.json 스펙 JSON Schema Draft-07 참조용 (070 신설)

## 관련 문서

| 문서 | 경로 | 참조 이유 |
|------|------|---------|
| PLAN.md | `tasks/134-260501-opp-pipeline-state-tool/PLAN.md` | §2.1~§2.20 전체 설계 SSOT |
| TASK.md | `tasks/134-260501-opp-pipeline-state-tool/TASK.md` | T-1~T-13 기술 결정 |
| state.schema.json | `opal/tools/state-tool/schema/state.schema.json` | JSON Schema Draft-07 |
| xlsx-tool 패턴 | `opal/tools/xlsx-tool/run.sh:1-12` | OPAL Tools 래퍼 패턴 |
