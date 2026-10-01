# PARALLEL-PROBE — TEST 병렬 실측 (W-6, D-14, AC-9·C-4)

실행: `python3 run/parallel-probe/probe.py` (2026-10-01, 재실행 가능, 임시 폴더 픽스처만 사용, 종료 시 삭제).

## 실행 환경

| 항목 | 값 |
|---|---|
| OS / CPU | macOS 27.0 (Darwin), 10코어 |
| Python | 3.14.3 |
| test-tool | `~/.opal/tools/test-tool/run.sh` (배포본, 읽기·실행만) |
| (a) 파라미터 | 명령 4개, 각 `sleep 2`, 3회 반복 |
| (b) 파라미터 | 8프로세스 × 5라운드, 라운드마다 새 픽스처(`scenario-init`→`scenario-lock`, `red_required:false` check 8건) |

## (a) 단일 에이전트 안 병렬

명령 i(0~3)는 2초 대기 후 `out-i`를 출력하고 종료 코드 i로 끝난다. 순차는 하나씩 실행, 병렬은 한 번의 bash에서 `&`·`wait`로 동시 실행하며 명령별 출력(`i.out`)·종료 코드(`i.rc`)를 파일로 받았다.

| 회차 | 순차(초) | 병렬(초) |
|---|---|---|
| 1 | 8.044 | 2.011 |
| 2 | 8.051 | 2.017 |
| 3 | 8.064 | 2.013 |
| 중앙값 | 8.051 | 2.013 |

- 병렬/순차 중앙값 비율 = 2.013 / 8.051 = **0.250** (기준 0.60 이하)
- 출력·종료 코드 보존: 6회 실행(순차 3·병렬 3) 모두 4개 명령의 출력과 종료 코드가 기대값과 일치 = **보존**
- (a) 판정: **가능**

## (b) 여러 프로세스의 동시 scenario-mark

| 라운드 | mark 성공 보고 | status `passed` | 사라진 시나리오 수 |
|---|---|---|---|
| 1 | 8 | 7 | 1 |
| 2 | 8 | 6 | 2 |
| 3 | 8 | 8 | 0 |
| 4 | 8 | 7 | 1 |
| 5 | 7 | 6 | 2 |
| 합계 | | | **6** |

사라진 시나리오 수 = 8 − `scenario-status`의 `passed`. 5라운드 중 4라운드에서 mark가 성공(`ok:true`)으로 보고됐는데도 기록이 사라졌고(라운드 5는 mark 1건이 오류 응답), 사라진 건이 한 번이라도 있었다.

## (c) 잠금 부재 코드 근거

- `opal/tools/test-tool/lib/scenario.py:206` `_save_spec`: `open(path, "w")`로 `test-scenario.json` 전체를 덮어쓴다. 파일 잠금·임시 파일 교체(rename)가 없다.
- `opal/tools/test-tool/lib/scenario.py:445` `cmd_scenario_mark`: `_load_spec`(읽기) → 대상 시나리오 수정 → `_save_spec`(`:512`)의 읽기-수정-쓰기이며 구간 전체에 잠금이 없다. 두 프로세스가 같은 원본을 읽으면 나중에 쓴 쪽이 앞선 쪽의 mark를 덮는다(위 (b)의 사라진 건과 일치).
- 파일에 `fcntl`·`flock`·`lockf`·`msvcrt`·`O_EXCL` 사용이 없음을 `probe.py`가 소스 검색으로 확인했다(`lock_in_code: false`).
- `opal/tools/state-tool/state_tool.py:4928` `_interval_sum_seconds`: `auto` 구간 `started_at`~`ended_at` 길이를 단순 합산한다(호출 `:4943` `auto_seconds`). 여러 에이전트가 같은 시간대에 각자 auto 구간을 기록하면 `auto_seconds`가 벽시계 시간보다 커진다(human 구간은 `_interval_union_seconds`로 합집합이라 다르다).

## (d) D-14 규칙 판정

규칙: (a) 병렬 중앙값이 순차 중앙값의 60% 이하이고 출력·종료 코드가 모두 보존되면 "가능". (b) 사라진 건이 한 번이라도 있거나 코드에 파일 잠금이 없으면 "불가".

| 항목 | 값 | 판정 |
|---|---|---|
| (a) 비율 / 보존 | 0.250 ≤ 0.60 / 보존 | 가능 |
| (b) 사라진 건 / 잠금 | 6건(>0) / 잠금 없음(`scenario.py:206`) | 불가 |

**최종 판정: (a) 가능 · (b) 불가.** 관측 사라진 건이 6건이고 코드 근거도 있어 두 조건 모두 "불가"를 가리킨다.

### 채택 절차 (한 에이전트 안 병렬 그룹)

- TEST-SCENARIO Setup에 `병렬 그룹: S-a, S-b, ...` 줄로 작성자가 선언한 시나리오끼리만, 한 에이전트가 한 번의 Bash로 동시 실행(`&`·`wait`, 명령별 출력·종료 코드 파일 저장)한다. 선언이 없는 시나리오는 순차다.
- 동시 실행 묶음은 `test-clock`의 auto 구간 하나(`--id batch-N`)로 기록해 `auto_seconds`가 벽시계 시간이 되게 한다.
- `scenario-mark`와 `test-clock` 호출은 에이전트가 순차로 한다.
- `test-scenario.json` 스키마에 필드를 더하지 않는다(`opal/core/references/harness/test-cycle.md:20`).

### 비채택: 여러 `opal-test-agent` 동시 디스패치

- 근거: (b) 동시 mark에서 5라운드 중 4라운드 6건 소실, 파일 잠금 부재(`scenario.py:206`·`:445`), `auto_seconds` 단순 합산(`state_tool.py:4928`·`:4943`).
- 대안: 후속 태스크에서 `scenario-mark`(`_save_spec`)에 파일 잠금과 원자적 쓰기를 도입하고, `auto_seconds`를 구간 합집합 방식으로 바꾼 뒤 재측정한다.
