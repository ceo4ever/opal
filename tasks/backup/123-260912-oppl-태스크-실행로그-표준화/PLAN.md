---
template: sdlc-v2
---
# PLAN: 태스크 실행 로그 — 기록 기반 완성

> 입력: [TASK.md](TASK.md), [ANALYSIS.md](ANALYSIS.md)
> 작성: 2026-09-14 17:36 (`node ~/.opal/tools/date/date.js datetime`)

## Approach

ANALYSIS가 분해한 3갈래를 **파일 소유권 단위**로 재배치해 실행 순서를 확정한다. 기록 코어
(`opal/tools/run-log-tool/run_log_core.py`)에 닿는 변경은 전부 한 줄기로 직렬화하고, Console
설정 계층(`dashboard/backend/`)과 시드 설정(`opal/core/setting.default.json`)만 병렬로 뗀다.

계약은 이미 확정돼 있으므로 구현자가 새로 정할 설계 선택이 없다. 이 PLAN은 **확정 계약을 어느
파일의 어느 함수에 어떤 순서로 넣을지**만 소유한다.

- 설계 계약 원본(`docs/run-log/CONTRACT.md`·`TRD.md`·`surfaces.json`·`PRD.md`)과 태스크 캡슐
  사본은 `diff` 결과 **4자산 전건 동일**하다. C-5 판정 불능 사유 없음.
- 새로 등재할 오류 코드가 없다. `redaction_failed`·`worker_duration_conflict`는 이미
  `CONTRACT.md` §2.2·§2.2.1과 `surfaces.json`의 `run-log-tool.append`·
  `state-tool.mark.completion-gate`·`run-log-tool.reconcile-duration` `err` 집합에 등재돼 있다.
  **C-9는 자산 개정이 아니라 구현 후 양방향 일치(MV-30) 확인으로 닫는다.**
- AC-9(런타임 색인)는 후속 이관이며 Work item을 만들지 않는다. 이관 근거는 ANALYSIS §4의 실측
  (누적 1,300건에서 append 평균 6.46 ms, 총 5.2초 — 워커 디스패치 단위 대비 비병목)이다.
- main 병합으로 공존하게 된 `run` 개념 2종(`state.json` 최상위 `run_id` / `run_log.active_run_id`)은
  이 태스크가 통합하지 않는다. 후속 검토 항목으로만 남긴다.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| D-P1. 기준선을 먼저 재측정하고 그 값을 C-2 기준으로 확정한다 | 착수 전 `state-tool`·`run-log-tool` 두 스위트의 pass/fail을 실측해 기록한다. main 병합 이전 값(436 / 36)은 참고값으로 강등한다 | ANALYSIS §7 "main 병합 후 재측정 필요". 재측정 없이 회귀를 판정하면 AC-21의 판정 기준 자체가 없다 |
| D-P2. 마스킹은 `redact()` **본문만** 채운다 | writer별 마스킹을 추가하지 않는다. `append()` 직렬화 직전과 `state_tool._atomic_write_state_json()`의 보관함 경로가 이미 이 한 함수를 통과하므로, 본문 구현만으로 표준 로그·가져오기 2경로가 동시에 덮인다 | [MUST] `docs/run-log/TRD.md` D-9: "디스크에 쓰기 전 마스킹을 **모든 writer가 통과하는 공통 경로 한 곳**에 둔다". `run_log_core.py` @header도 "본문은 아직 pass-through다(D-9, writer별 개별 마스킹 금지)"로 같은 경계를 선언한다 |
| D-P3. `redact()`는 구조를 바꾸지 않고 문자열 값만 치환한다 | 키 집합·타입·중첩 깊이를 보존하고 값 안의 비밀 부분만 대체한다. 두 번 통과해도 결과가 같다 | `run_log_core.py:248` 멱등 계약 주석. 폐쇄형 스키마(`validate_event`)가 마스킹 이후 산출물도 통과해야 하고, 직렬화 상한 16 KiB는 `redact()` 통과 후 최종 줄에서 재므로 구조 변경은 상한 판정을 함께 흔든다 |
| D-P4. 추적 경계 복귀는 마스킹 검증을 통과한 **뒤에** 수행한다 | `.gitignore:55`의 `tasks/**/run/*.jsonl` 한시 제외와 그 위 주석 블록(49–54행)을 제거하되, `tasks/**/run/raw/`·`tasks/**/run/.runtime/`·`.opal-task.lock` 3행은 영구 규칙으로 남긴다 | [MUST] `ANALYSIS.md` §6 H-4: "마스킹 검증 통과 후에만 `.gitignore` 한시 제외를 제거한다". git 히스토리 진입은 회수 불가이며 TRD D-9가 사후 스캔을 기각한 이유가 이것이다 |
| D-P5. 조각 경계 전환은 기존 배타 락 구간 **안에서만** 검사·생성한다 | 상한 검사 → 다음 번호 선택 → 새 조각 생성을 `_with_lock()` 구간 안에서 연속 수행한다. 새 락·조각별 락을 만들지 않는다. 닫힌 조각은 재개방하지 않는다 | [MUST] `docs/run-log/TRD.md` D-4 및 §조각 경계 전환이 정확히 한 프로세스에서만 일어나는 이유: "검사와 생성 사이에 락을 놓는 구간이 없다는 것이 단일성의 전부다" |
| D-P6. run 전역 순번은 조각을 넘어 이어진다 | `scan_run()`의 조각 열거를 번호 순 전 조각으로 확장하고 순번·멱등 판정 범위를 run 단위로 유지한다. 조각 전환이 순번을 초기화하지 않는다 | `CONTRACT.md` MV-10·MV-12. 순번은 run 전역이고 조각은 저장 단위일 뿐이다 |
| D-P7. 실행시간은 terminal 사건의 `data.duration_spans[]` 합으로만 확정한다 | `duration_ms`는 span 합과 같아야 하고 같은 `source_id` 중복은 append 시점에 거부한다. 시각 차분으로 시간을 만들지 않는다 | [MUST] `docs/run-log/CONTRACT.md` §1.2 terminal 공통 조건 및 `TRD.md` §실행 시간을 시각 차분이 아니라 단조 시계 구간 합으로 재는 이유 |
| D-P8. 분 투영은 `state-tool mark`가 파생값을 읽어 기록한다 | 1.2 태스크에서 `--worker-duration-minutes`가 파생값과 일치하면 수용 + deprecated 경고, 불일치하면 `worker_duration_conflict`로 거부한다. 1.0/1.1 태스크는 현행 수용 그대로다 | `CONTRACT.md` §2.5 `state-tool.mark.completion-gate` 개정 조항 원문. C-3이 1.0/1.1 경로 불변을 요구한다 |
| D-P9. 이번 범위는 §2.5 개정 조항 중 **시간 절만** 구현한다 | 채널 등급·provenance 증거 검사, `--run-log-override` 묶음, `status=overridden` 전이는 구현하지 않는다 | TASK.md §제외 범위가 AC-4·5·11·16을 후속 이관으로 확정했다. 완료 게이트 강제는 배포 후 그림자 표본 축적이 선행 조건이다 |
| D-P10. 시간대는 `QuietHours` 3필드로 설정·라우터 계층에서 끝난다 | `stats.py` 공개 함수 6종의 `quiet_hours` 인자는 2튜플 `(시작 분, 끝 분)`(미적용은 `None`)로 유지하고, 라우터가 `quiet_hours_token()`에만 3필드를 넘긴다 | [MUST] `docs/run-log/CONTRACT.md` §2.8.1 B-1~B-4. [MUST] `dashboard/backend/stats.py` @header: "표준 라이브러리(datetime·statistics)만 의존하고 모델·라우터·캐시를 import하지 않는다. 파일 I/O 0건" |
| D-P11. 계약 3자산을 개정하지 않는다 | `CONTRACT.md`·`TRD.md`·`surfaces.json`은 읽기 전용이다. 구현이 계약과 어긋나면 계약을 고치지 않고 blocker로 올린다 | [MUST] `TASK.md` C-5. 신설 오류 코드가 0건이므로 C-9는 개정 없이 대조로 닫힌다 |
| D-P12. 새 읽기·쓰기 경로는 기존 방어 함수를 재사용한다 | 조각 전환의 새 조각 생성·조회는 `_reject_symlink_or_escape()`·`O_CREAT`+`O_EXCL`+`O_NOFOLLOW`를 그대로 쓰고 0600/0700 권한을 유지한다. 새 방어를 재작성하지 않는다 | [MUST] `TASK.md` C-8: "새 읽기·쓰기 경로를 만들면 같은 방어를 적용하고 테스트로 고정한다" |
| D-P13. 배포본을 건드리지 않고 install도 실행하지 않는다 | 프로젝트 소스(`opal/`, `dashboard/`, `scripts/`, `.gitignore`)만 수정한다. 검증 종료 지점은 소스 트리 테스트 통과다 | [MUST] `.opal/AGENT.md` §금지사항 "`~/.opal/` 직접 편집 금지", [MUST] `TASK.md` C-1 "이 태스크에서 install을 실행하지 않는다" |
| D-P14. `surfaces.json`의 `reconcile-duration` `request_shape`에 한해 D-P11 읽기 전용을 해제한다 | `optional`에 `--worker-run-id <worker_run_id>` 한 항목을 **추가만** 한다. `required`·`response_shape`·`err` 집합과 다른 표면은 건드리지 않는다 | W-6 구현 중 드리프트 발견 — 동결 RED 테스트가 그 인자를 요구해 CLI가 후방 호환 확장으로 받고 있으나 표면 문서에는 없다(`run_log_tool.py:176` ↔ `surfaces.json` optional 2항목). 방치하면 `surfaces.json`이 표면 SSOT 지위를 잃는다. **소유자 승인으로 이 항목에 한해 D-P11 해제** |

폐기한 대안: 순번 색인(SQLite) 도입은 이번 범위에서 기각했다. 되돌림 비용이 낮고(TRD D-3)
실측이 병목을 보여주지 않으므로, 색인 없이 전량 스캔을 유지한 채 조각 전환만 넣는다. 이 선택은
조각 수가 늘수록 스캔 대상이 늘어난다는 뜻이므로, 후속 색인 이관의 판단 입력이 된다.

## Work items

변경 대상 경로는 `code-scan search`·`code-scan depends`(`--project-root {task_home}`) 실측으로
확인했다. `run_log_core.py`·`state_tool.py`는 `code-scan search redact` 조회 결과 `[util]` layer
2건으로 확인했고, `dashboard/backend/` 3파일은 `code-scan scan dashboard/backend`의 `[service]`
layer 열거와 각 파일 @header의 exports 필드로 확인했다.

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. 회귀 기준선 재측정 | opal-task-agent | `opal/tools/state-tool/tests/`·`opal/tools/run-log-tool/tests/` (실행 전용 — 파일 변경 없음) | main 병합 후 두 스위트를 실행해 pass/fail 수를 실측하고, 그 값을 이번 태스크의 C-2 기준선으로 선언한다. 실패가 1건이라도 있으면 구현에 착수하지 않고 blocker로 보고한다. 기존 테스트 파일을 고쳐 통과시키지 않는다 | 없음 | P1 | C-2, AC-21 |
| W-2. `redact()` 본문 구현 | opal-task-agent | `opal/tools/run-log-tool/run_log_core.py`, `opal/tools/run-log-tool/tests/test_run_log_tool.py` | `redact()` pass-through(242–251행)를 실동작으로 바꾼다. 대상은 환경변수형 비밀값·bearer/token·API key·private key 블록이며 `docs/SECURITY.md`의 추가 패턴을 병합한다. 문자열 값만 치환하고 키 집합·타입·중첩 구조는 보존한다(멱등). 마스킹 불가 판정 원본은 `redaction_failed`를 반환하고 메타데이터 사건만 남긴다 — 코드를 `RUN_LOG_ERROR_CODES`에 등재한다. 16 KiB 상한이 `redact()` 통과 후 최종 줄에서 측정되는 현재 순서를 바꾸지 않는다. secret fixture를 표준 로그·가져오기 경로에 투입해 **실제 디스크 파일**에 평문이 0건인지 판정하는 테스트를 추가한다(문구 검사 금지). @header의 pass-through 서술을 현재 사실로 갱신한다 | W-1 | P2 | AC-13, C-5, C-8 |
| W-3. 조용시간 `timeZone` 2층 머지·캐시 토큰 | opal-be-agent | `dashboard/backend/config.py`, `dashboard/backend/routers/tasks.py`, `dashboard/backend/routers/dashboard.py`, `dashboard/backend/tests/test_config.py`, `dashboard/backend/tests/test_routers.py` | `DEFAULT_QUIET_HOURS`에 `"timeZone": "Asia/Seoul"`을 추가하고 `QuietHours` NamedTuple 3필드(start_minute·end_minute·time_zone)를 신설한다. `load_quiet_hours()`가 `QuietHours`(미적용은 `None`)를 반환하되 2층 머지·`enabled != True`·`start == end` 폴백 규칙은 그대로 둔다. 유효하지 않은 IANA 이름은 `Asia/Seoul`로 폴백하고 예외를 밖으로 던지지 않으며 설정 파일을 다시 쓰지 않는다. `quiet_hours_token()`은 `f"{start}-{end}@{tz}"`를 만들고 `None`은 `"off"` 그대로다. 두 라우터는 `quiet_hours_token()`에만 3필드를 넘기고 `stats` 호출에는 `(start_minute, end_minute)`로 좁혀 넘긴다. `stats.py`는 건드리지 않는다. 날짜 경계 fixture와 `timeZone`만 다른 두 설정의 토큰 분기 테스트를 추가한다. 두 파일 @header의 반환형 서술을 갱신한다 | W-1 | P2 | AC-20, C-2, C-7 |
| W-4. 설정 시드에 `timeZone` 키 배선 | opal-task-agent | `opal/core/setting.default.json`, `scripts/install-mac.sh` | 시드 원본 `quietHours`에 `"timeZone": "Asia/Seoul"`과 `_help` 설명(IANA 이름, 미설정 시 `Asia/Seoul` 폴백, 프로젝트 로컬 하위 키 덮어쓰기)을 추가한다. `install-mac.sh:1112`의 `SEED_KEYS`는 `quietHours`를 객체 단위로 이미 싣고 있으므로 **배선 변경 없이 하위 키가 전파되는지 확인만** 하고, 전파되지 않으면 그 사실을 보고한다. 배포본을 직접 편집하지 않고 install을 실행하지 않는다 | W-1 | P2 | AC-20, C-1 |
| W-5. 조각 경계 원자 전환 | opal-task-agent | `opal/tools/run-log-tool/run_log_core.py`, `opal/tools/run-log-tool/tests/test_run_log_tool.py` | 조각 상한 4 MiB 상수와 전환 경로를 넣는다. 상한 검사·다음 번호 선택·새 조각 생성을 기존 `_with_lock()` 락 구간 안에서 연속 수행하고 중간에 락을 놓지 않는다. 새 조각 생성은 `segment_path()` + `O_CREAT`+`O_EXCL`+`O_NOFOLLOW` 0600을 그대로 쓰고 `_reject_symlink_or_escape()`를 거친다. 닫힌 조각은 다시 쓰지 않는다. `scan_run()`의 조각 열거를 번호 순 전 조각으로 확장해 run 전역 순번·요청 식별자 멱등 판정 범위를 유지한다. 경계 직전 다중 프로세스 barrier 동시 해제 시나리오로 새 조각 정확히 1개·순번 중복 0·누락 0·정상 완료 표시 오탐 0을 고정하고, barrier 대기는 락 상한 30,000 ms보다 충분히 짧게 잡는다. @header의 "조각 경계 전환은 이 모듈이 다루지 않는다" 서술을 갱신한다 | W-2 | P3 | AC-8, C-5, C-8 |
| W-6. terminal 시간 증거 검증과 파생 조회 표면 | opal-task-agent | `opal/tools/run-log-tool/run_log_core.py`, `opal/tools/run-log-tool/run_log_tool.py`, `opal/tools/run-log-tool/tests/test_run_log_tool.py` | `validate_event()`에 terminal 공통 조건의 미구현 절을 더한다 — `data.duration_spans[]`는 `{source_id, duration_ms}` 배열이고, `duration_ms`가 span 합과 다르면 거부하며 같은 `source_id` 중복은 거부한다(기존 `duration_ms`+`duration_source` XOR `duration_unknown_reason` 검사는 유지). 같은 `worker_run_id`의 terminal 사건에서 `duration_ms`와 `floor(duration_ms / 60000)`을 돌려주는 읽기 함수를 추가하고, `surfaces.json`에 이미 등재된 `run-log-tool.reconcile-duration` 서브명령으로 노출한다(불일치 시 `worker_duration_conflict`). 코어는 `state.json`을 읽지 않는다 — task_path·run_id·worker_run_id만 인자로 받는다 | W-5 | P4 | AC-12, C-4, C-5 |
| W-7. `state.json` 분 투영과 수동값 거부 | opal-task-agent | `opal/tools/state-tool/state_tool.py`, `opal/tools/state-tool/tests/test_state_tool_run_log.py` | `mark`가 1.2 태스크에서 W-6의 코어 조회 함수를 `_import_run_log_core()` 경로로 호출해 파생 분값을 `worker_duration_minutes`에 자동 기록하도록 한다. `--worker-duration-minutes`가 실렸고 파생값과 같으면 수용 + deprecated 경고, 다르면 `worker_duration_conflict`로 거부한다. `worker_duration_conflict`를 `RUN_LOG_STATE_ERROR_CODES`에 등재한다(`ERROR_CODES`와 물리 분리 유지). `run_log` 블록이 없는 1.0/1.1 태스크는 기존 `_worker_duration_minutes()` 수동 경로와 응답 키 집합을 그대로 유지한다. §2.5의 등급·override 조항은 구현하지 않는다. @header의 `worker_duration_minutes` 서술을 갱신한다 | W-6 | P5 | AC-12, C-3, C-4 |
| W-8. 추적 경계 복귀 | opal-task-agent | `.gitignore` | 마스킹 검증(W-2)과 조각·시간 경로 변경이 모두 통과한 뒤에만 `.gitignore:49-55`의 한시 제외 주석 블록과 `tasks/**/run/*.jsonl` 한 줄을 제거한다. `tasks/**/run/raw/`·`tasks/**/run/.runtime/`·`.opal-task.lock` 3행은 영구 규칙으로 남기고, 남는 주석을 현재 사실(마스킹된 조각은 추적)로 고친다. 제거 후 실제 태스크 실행으로 git 추적 목록을 확인해 원본·런타임·락이 제외되고 마스킹된 조각만 추적되는지 판정한다 | W-2, W-7 | P6 | AC-14, C-8 |
| W-9. 회귀·자산 일관성 최종 확인 | opal-task-agent | `opal/tools/state-tool/tests/`·`opal/tools/run-log-tool/tests/`·`dashboard/backend/tests/` (실행 전용), `docs/run-log/surfaces.json`(읽기 대조) | W-1 기준선과 대비해 세 스위트 전건 통과를 실측한다. 기 충족 AC-1·2·3·6·7·10·15·19의 동작을 실제 실행 출력으로 확인하며 기존 테스트 파일을 고쳐 통과시키지 않는다. `CONTRACT.md` §2.2 표·§2.2.1 대응·`surfaces.json` `err` 집합 3자산의 양방향 일치를 대조해 신설 코드 0건·누락 0건을 확인한다. 어긋나면 계약을 고치지 않고 blocker로 보고한다 | W-8 | P7 | AC-21, C-2, C-9 |
| W-10. `reconcile-duration` 표면 드리프트 해소 | opal-task-agent | `docs/run-log/surfaces.json` | `run-log-tool.reconcile-duration` 표면의 `request_shape.optional`에 `--worker-run-id <worker_run_id>` 한 항목을 추가한다. 같은 파일의 다른 표면, 이 표면의 `required`·`response_shape`·`err` 집합은 건드리지 않는다. 추가 후 CLI 실인자(`run_log_tool.py`의 `reconcile-duration` argparse)와 표면 `request_shape`가 일치하는지 대조한다. 코드는 바꾸지 않는다 — 문서 쪽을 코드에 맞추는 단방향 동기화다 | W-9 | P8 | C-9 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. 마스킹이 사건 구조를 바꾸면 이미 쌓인 조각과 해석이 갈린다 | `redact()`가 모든 writer의 공통 경로여서 영향 범위가 전 사건이다. 폐쇄형 스키마 검증과 16 KiB 상한 판정이 동시에 흔들린다 | 기존 조각을 읽는 검증·가져오기가 위반으로 오판하고, 상한 경계 사건의 수용 여부가 바뀐다 | D-P3 — 구조 불변·값만 치환·멱등. W-2가 멱등성과 상한 측정 순서를 테스트로 고정한다 |
| H-2. 조각 전환이 run 전역 순번 연속성을 깬다 | 순번은 run 전역이고 조각을 넘어 이어져야 한다(MV-10). 요청 식별자 멱등 판정 범위도 run 단위다 | 순번 중복·누락이 발생하면 AC-8이 깨지고 이미 기록된 실행 이력의 재구성이 불가능해진다 | D-P5·D-P6 — 같은 락 안에서 전환, `scan_run()` 열거를 전 조각으로 확장. W-5가 barrier 동시 해제 시나리오로 고정한다 |
| H-3. 시간대 도입이 `stats.py` 시그니처를 바꿔 동결 표본을 깬다 | C-2가 동결한 `STATS-BASELINE.md` 기준값과 `dashboard/backend/tests/fixtures/t103_states/` fixture가 `stats` 공개 함수 6종에 직접 닿는다 | Console 통계 회귀가 발생하고 동결 fixture를 고쳐야 하는 상황이 되어 C-2 자체가 무의미해진다 | D-P10 — `QuietHours`는 config·라우터 안에서만 흐른다. W-3이 `stats.py`를 변경 대상에서 제외한다 |
| H-4. 추적 경계 복귀 시 마스킹이 불완전하면 평문이 git에 들어간다 | git 히스토리는 회수 불가다. TRD D-9가 사후 스캔을 기각한 이유가 이것이다 | 비밀값이 영구히 저장소에 남고 되돌릴 방법이 없다 | D-P4 — W-8의 선행에 W-2·W-7을 걸어 순서를 강제한다. 실제 파일 검사로 판정하고 문구 검사를 인정하지 않는다 |
| H-5. 마스킹 패턴의 오탐이 정상 식별자를 지운다 | `event_id`·`sha256`·`worker_log_token_id`는 비밀값과 형태가 비슷한 16진 문자열이다. 이들이 마스킹되면 멱등 판정·출처 대조·순번 발급이 전부 어긋난다 | 기존 36+436 테스트가 광범위하게 깨지고, 원인이 마스킹인지 다른 변경인지 분리하기 어려워진다 | W-2가 마스킹 대상 키와 보존 키를 명시적으로 가르고, 발급 필드·해시 필드가 통과 후에도 동일한지 테스트로 고정한다. W-1의 기준선이 분리 판정의 기준이 된다 |
| H-6. `mark`의 코어 조회 추가가 1.0/1.1 경로의 바이트 동일성을 깬다 | C-3이 `--run-log-mode` 미지정 경로의 바이트 동일성을 요구하고, `run_log` 블록이 없는 태스크는 `run_log_commit()`이 `save_state_json()`으로 우회하는 현재 구조에 의존한다 | 구버전 태스크의 `state.json` 산출물·응답 키 집합이 달라져 실행 중인 태스크가 깨진다 | D-P8 — 파생 조회를 1.2 분기 안에만 둔다. W-7이 1.0/1.1 우회 경로의 산출물·응답 키 동일성을 테스트로 고정한다 |

## Release and recovery

- **적용 순서**: P1(기준선) → P2(마스킹·시간대·시드, 3-way 병렬) → P3(조각 전환) → P4(시간 증거
  검증) → P5(분 투영) → P6(추적 경계 복귀) → P7(회귀·자산 대조). P2의 세 W는 변경 대상이 서로
  겹치지 않는다. P3~P5는 전부 기록 코어 계열 파일을 만지므로 순차다.
- **검증 범위**: 결정론 — 마스킹 멱등·조합 판정·순번 단조성·토큰 분기·분 투영식. 회귀 —
  `state-tool`·`run-log-tool`·`dashboard/backend` 세 스위트와 동결 fixture. 실제 연동 — 조각 경계
  다중 프로세스 barrier 시나리오와 추적 경계의 git 목록 확인 2건만 실행 관측이 필요하다.
- **실측 경계**: 조각 전환 barrier 대기는 배타 락 상한 30,000 ms보다 충분히 짧게 잡는다. 그러지
  않으면 판정이 `task_lock_timeout`과 뒤섞여 AC-8의 참·거짓이 갈리지 않는다.
- **실패 시**: 이 태스크는 배포·설치를 수행하지 않으므로(C-1) 복구는 소스 되돌리기로 끝난다.
  단 W-8만은 예외다 — 추적 경계 복귀 후에 커밋된 조각에서 평문이 발견되면 되돌리기로 회수되지
  않는다. 그래서 W-8은 마지막 실행 그룹이고, 커밋 전에 실제 파일 검사로 판정한다. 검증 종료
  지점은 W-9의 세 스위트 통과와 3자산 양방향 일치 확인이다.
