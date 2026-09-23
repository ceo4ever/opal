# ADD_DONE-1: 훅 세션 소유권 우선순위

| 항목 | 내용 |
|---|---|
| 추가작업 번호 | ADD-1 |
| 일시 | 2026-09-16 18:15 ~ 18:30 (KST) |
| 사유 | Claude Stop 훅이 세션 소유가 아닌 태스크를 집어 응답을 계속 차단했다 |
| 검증 | 훅 스크립트 4케이스 실측 + `merge_hooks` 5 passed + 136 계약 테스트 3 OK |

## 사유

태스크 136이 도입한 Stop 훅은 "활성 태스크의 다음 전이가 `continue`이면 조기 종료를 차단"한다. 그 계약 자체는 유효하나, **어떤 태스크가 이 세션의 것인지 판정하지 않는다.**

훅은 `OPAL_TASK_PATH`/`OPAL_ACTIVE_TASK_PATH`를 읽지만 그 결과를 후보 목록에 **추가만** 하고, 최종 선택은 `updated_at` 최신순 정렬이 한다. 그 결과 세션이 자기 태스크를 명시해도 더 최근에 갱신된 다른 태스크가 선택된다.

실제 발생: 태스크 135를 완주해 `completed_unmerged`로 닫은 뒤, 소유자가 별도 관리하는 태스크(워크트리 132)가 선택되어 이 세션이 진행할 수 없는 작업을 계속 요구했다. 다중 PM이 같은 저장소를 다루면 재현되는 구조적 결함이다.

## 변경 내용

`opal/core/hooks/claude-hooks.json`의 `Stop` 훅 스크립트에 세션 선언 우선순위를 추가했다.

- `declared` 플래그를 두어 환경변수가 설정되어 있으면 디스크 스캔(`cwd`·조상 `tasks/`·`.opal-worktrees/.meta`)을 수행하지 않는다.
- 선언한 태스크가 활성이 아니면 이어갈 것이 없다는 뜻이므로 차단하지 않는다. 후보 유무로 판정하면 완료된 태스크를 선언한 세션이 폴백 스캔으로 새어 나간다.
- 환경변수 미설정 시에는 기존 폴백 스캔이 그대로 동작해 태스크 136의 계약을 보존한다.

## 변경 파일

- `opal/core/hooks/claude-hooks.json`

## 검증 결과

훅 스크립트를 추출해 실제 stdin 페이로드로 4케이스 실행:

| 케이스 | 기대 | 결과 |
|---|---|---|
| 환경변수 없음 → 폴백 스캔 | 차단(136 계약 보존) | ✅ `decision: block` |
| 완료된 태스크 선언 | 차단 없음 | ✅ 무출력 |
| `stop_hook_active` 재진입 | 차단 없음 | ✅ 무출력 |
| 존재하지 않는 경로 선언 | 차단 없음 | ✅ 무출력 |

회귀:

- `python3 -m pytest scripts/tests/test_merge_hooks.py -q` → 5 passed
- `python3 scripts/tests/task136_mode_transition_contract.py` → Ran 3 tests, OK

## ADD-2 — pilot run-log 발동 경로

| 항목 | 내용 |
|---|---|
| 추가작업 번호 | ADD-2 |
| 일시 | 2026-09-16 18:30 ~ 21:10 (KST) |
| 사유 | run-log를 완성했으나 어떤 pilot도 켤 수 없어 실행 이력의 단일 원천이 진입 경로에서 성립하지 않았다 |
| 검증 | 3개 스위트 전건 통과 + `init` 3경로 실측 |

### 변경 내용

**설계 선택**: pilot 10종에 `--run-log-mode` 플래그를 다는 대신 `state-tool init`의 기본값을 `shadow`로 전환했다. pilot마다 플래그를 전달하는 방식은 pilot이 늘어날 때마다 빠뜨릴 수 있고 그 구멍이 조용한 반면, 도구 기본값은 구조적으로 구멍이 생기지 않는다. pilot SKILL.md는 한 줄도 바뀌지 않았다.

- `--run-log-mode`의 `choices`에 `off`를 추가하고 `default="shadow"` 적용
- `cmd_init` 분기 조건을 `not in (None, "off")`로 변경 — `off` 명시가 기존 1.1 경로를 그대로 탄다

**계약 7건 재타겟** (독립 워커 수행 — 구현자가 자기 변경에 맞춰 계약을 약화하는 것을 막기 위해 PM이 직접 하지 않았다):

| 출처 | 원래 트리거 | 재타겟 후 |
|---|---|---|
| 태스크 135 C-3 (4건) | `--run-log-mode` **미지정** 경로의 바이트 동일성 | `--run-log-mode off` **명시** 경로의 바이트 동일성 |
| 태스크 103 (3건) | 인자 미지정 `mark`의 응답 키 집합 불변 | fixture를 `off`로 생성해 레거시 응답 형태 계약을 그대로 유지 |

두 계약 모두 실질은 "run-log 비활성화 경로는 개정 전과 같다"이며, 기본값이 바뀌면서 그 경로의 표현이 "미지정"에서 "`off` 명시"로 옮겨간 것이다. 단언을 느슨하게 만들거나 `_T103_BASELINE_MARK_KEYS`에 `run_log`를 더하는 완화는 쓰지 않았다(상수 무변경 확인).

- `docs/run-log/CONTRACT.md` §2.5에 기본값 `shadow`와 `off`의 의미를 반영

### 변경 파일

- `opal/tools/state-tool/state_tool.py`
- `opal/tools/state-tool/tests/test_state_tool_run_log.py`
- `opal/tools/state-tool/tests/test_state_tool.py`
- `docs/run-log/CONTRACT.md`

### 검증 결과

`init` 3경로 실측:

| 인자 | schema | `run_log` | `run/` |
|---|---|---|---|
| `--run-log-mode off` | 1.1 | 없음 | 미생성 |
| 미지정(기본 shadow) | 1.2 | 생성 | 생성 |
| `--run-log-mode active` | — | — | `profile_not_found` 거부 유지 |

회귀(PM 독립 재실행):

- `test_state_tool_run_log.py` → 29 passed, 0 failed
- `test_state_tool.py` → 411 passed, 3 skipped, 116 subtests (기준선 동일)
- `test_run_log_tool.py` → 53 passed, 4 subtests (기준선 동일)

### 부수 영향

전체 테스트 시간이 117초 → 215초로 늘었다(약 1.8배). 모든 테스트 태스크가 run-log 조각을 생성하기 때문이며, 기본값 전환의 실제 비용이다.

### 진행 경위 기록

PM이 착수 중 계약 7건 폐기 필요를 발견하고 "추가작업 범위 초과"를 사유로 임의 원복했다. 소유자가 이를 지적해 복원했다 — 작업 축소는 소유자 결정 사항이고, 당시 구현은 이미 동작 확인이 끝나 막힌 상태가 아니었다. PM이 우려한 "구현자의 계약 약화"는 원복이 아니라 독립 워커 위임으로 해소했다.

## ADD-3 — 훅 워크트리 태스크 소유권 경계

| 항목 | 내용 |
|---|---|
| 추가작업 번호 | ADD-3 |
| 일시 | 2026-09-16 21:30 ~ 21:50 (KST) |
| 사유 | ADD-1의 `declared` 분기가 배선 불가로 확인되어, 실제 오작동을 해소하지 못했다 |
| 검증 | 훅 3케이스 실측 + `merge_hooks` 5 passed + 136 계약 3 OK |

### 사유 — ADD-1이 실효를 내지 못한 이유

ADD-1은 `OPAL_TASK_PATH` 선언이 있으면 디스크 스캔을 건너뛰게 했으나, 배포 후에도 차단이 계속됐다. 원인을 조사한 결과 **이 변수를 설정하는 주체가 저장소 어디에도 없다**(전수 grep: 훅 스크립트 본문과 이 문서 외 0건).

더 근본적으로, 환경변수로는 이 문제를 풀 수 없다. Claude Code 공식 문서 기준:

- 훅은 *"inherits the parent environment"* — 세션 시작 시점 환경만 물려받는다.
- `settings.json`의 `env`는 훅에 전달되지만 **정적 값**이다. 태스크 경로는 세션 도중 정해진다.
- Bash 도구의 `export`는 각 호출이 독립 서브셸이라 CLI 본체 환경에 반영되지 않는다(문서가 이 한계를 명시).
- `CLAUDE_ENV_FILE`은 Bash 명령 프리앰블 전용이며, 훅 프로세스에도 적용된다는 근거가 문서에 없다.

즉 ADD-1의 분기는 계약으로는 옳으나 **발화할 수 없는 조건**을 다룬다.

### 변경 내용

`opal/core/hooks/claude-hooks.json`의 Stop 훅에서 **`.opal-worktrees/.meta` 순회를 제거**했다.

허브 세션이 메타 파일의 `task_path`를 따라가면 다른 세션이 소유한 워크트리 태스크를 후보로 집는다. 워크트리 태스크는 그 워크트리에서 작업하는 세션의 것이며, 그 세션은 자기 `cwd` 아래 `tasks/`에서 같은 태스크를 정상적으로 발견한다. 메타 순회는 소유권 경계를 넘는 중복 경로였다.

`declared` 분기는 지우지 않고 "현재 미배선" 주석을 달았다. 근본 해법(stdin `session_id`를 키로 한 매핑 파일 조회)이 도입되면 그 자리가 필요하며, 왜 지금 발화하지 않는지를 코드가 스스로 설명해야 다음 사람이 같은 조사를 반복하지 않는다.

### 변경 파일

- `opal/core/hooks/claude-hooks.json`

### 검증 결과

| 케이스 | 기대 | 결과 |
|---|---|---|
| 허브 `cwd` | 차단 없음 | ✅ 무출력 |
| 워크트리 `cwd` | 자기 태스크 발견해 차단 | ✅ `decision: block` |
| `stop_hook_active` 재진입 | 차단 없음 | ✅ 무출력 |

두 번째 케이스가 핵심이다 — 태스크 136의 계약(활성 태스크가 `continue`면 조기 종료 차단)은 워크트리 세션에서 그대로 유지된다. 허브 세션만 남의 태스크를 집지 않게 됐다.

회귀: `scripts/tests/test_merge_hooks.py` 5 passed · `scripts/tests/task136_mode_transition_contract.py` Ran 3 tests OK.

### 이월

훅의 세션 소유권 판정을 `session_id` 매핑으로 재설계하는 작업은 별도 태스크 소관이다. 매핑의 생성·갱신·정리 주체와 세션 비정상 종료 시 잔존 처리를 설계해야 하며, 추가작업 규모가 아니다.
