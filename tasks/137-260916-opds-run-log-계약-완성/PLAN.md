---
template: sdlc-v2
---
# PLAN: run-log 계약 완성 — PM 활동 누락 판정과 payload 키 폐쇄

> 입력: [TASK.md](TASK.md)

## Approach

계약 조문을 먼저 확정하고(P1), 그 조문을 실패로 관찰하는 시나리오를 붙인 뒤(P2), 구현이 조문을 따르게 한다(P3), 마지막으로 문서 미러와 전건 회귀를 닫는다(P4). TASK C-1("계약 조문 확정이 구현보다 앞선다")을 산문 약속이 아니라 Work items의 `선행 작업` 그래프로 강제한다.

두 공백은 서로 다른 계층에서 닫는다.

- **PM 활동 누락 판정**은 상태 대조 축이므로 `state-tool`이 전담한다. `run_log_core`는 손대지 않는다(C-4 / `docs/run-log/TRD.md` D-5).
- **payload 키 폐쇄**는 스키마 축이므로 기록 코어의 append 스키마 판정으로 내린다. 상태 파일을 읽지 않으므로 같은 단방향 의존을 깨지 않는다.

범위는 TASK `Affected users and systems`가 열거한 6개 파일이다. 신규 오류 코드·신규 표면 id·`surfaces.json` 변경·`~/.opal` 배포는 하지 않는다.

### 근거 코드맵 (실측, `code-scan scan`)

| 파일 | module | layer | domain | exports 중 이번 단위가 접촉하는 것 |
|---|---|---|---|---|
| `opal/tools/run-log-tool/run_log_core.py` | `run_log_core` | `util` | `opal-tools` | `validate_event`, `append`, `RUN_LOG_ERROR_CODES` |
| `opal/tools/state-tool/state_tool.py` | `state_tool` | `util` | `opal-pipeline` | `_run_log_completeness_check`, `_run_log_all_records`, `_run_log_block`, `_build_pm_activity_data` |
| `opal/tools/run-log-tool/tests/test_run_log_tool.py` | `test_run_log_tool` | `test` | `opal-tools` | S-16(`:901`)·S-17(`:951`) fixture |
| `opal/tools/state-tool/tests/test_state_tool_run_log.py` | `test_state_tool_run_log` | `test` | `opal-pipeline` | `TestVerifyCompletenessCheckThreeObservationFields`(`:1287`), `TestPmActivityWhitelistRejection`(`:1009`) |

`run_log_core`의 `depends`는 상태 도구 모듈을 포함하지 않는다. 이번 변경으로도 포함시키지 않는다.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| D-1. `missing_pm_activity`의 트리거는 **상태 앵커 2종**으로 확정한다 | 앵커 ① **자동 승인 행**: `rows[]` 중 `status == "done"` ∧ `owner == "auto"` ∧ `key` 보유. 앵커 ② **override**: `run_log.status == "overridden"`. 각 앵커마다 대응 PM `activity`가 없으면 1건을 싣는다 | 기존 3종이 쓰는 대조 패턴(상태 사실 ↔ 사건)과 동형이다. 앵커 ①은 `docs/run-log/CONTRACT.md:476`이 이 검사에 이미 부여한 목적("**자동 승인을 포함한 누락**을 진단한다")의 직접 집행이며, `owner="auto"`는 `state_tool.py:2225`·`:3461`이 `--auto-pass`와 `auto_approve_prior_user_confirmations()`에서 남기는 결정론적 자동 승인 흔적이다. 앵커 ②는 `CONTRACT.md` §1.4 "override bundle은 `activity(data.kind=decision)` 1건 + 강제 `state.changed` 1건의 정확히 2건"의 집행일 뿐 신규 규칙이 아니다 |
| D-2. 기대 사건의 **대조 술어**를 조문이 확정한다 | 앵커 ①: `event=="activity"` ∧ `actor.kind=="PM"` ∧ `data.kind=="decision"` ∧ `task_step == row.key`. 앵커 ②: `event=="activity"` ∧ `actor.kind=="PM"` ∧ `data.kind=="decision"`(run 전역, 주소 대조 없음) | `task_step`은 §1.1 공통 필드이고 `row.key`는 `state.schema.json`의 task-step 키 체계와 같은 주소다. 제3자가 조문만으로 같은 판정을 낼 수 있는 유일한 공통 주소다(AC-1) |
| D-3. 대조 대상 사건 집합은 **committed + pending 합집합**이다 | `_run_log_all_records()`를 쓴다. 보관함에 적재된 PM `activity`는 이미 생산된 사건으로 본다 | §1.4가 PM `activity`를 보관함 적재 대상으로 규정한다. 드레인 실패는 `run_log_pending`이 별도 진단하므로(§1.4) 여기서 다시 "누락"으로 잡으면 두 진단이 뒤섞인다. 같은 이유로 보관함 경유 사건인 `missing_gate_event`(`state_tool.py:1355`)와 `unobserved_worker_boundary`(`:1364`)가 이미 `all_records`를 쓴다 |
| D-4. 판정 **범위 한정**을 조문에 명시한다(미집행 공백이 아니라 정의) | (a) `key`가 없는 행(1.0/1.1 주소 체계)은 대조 주소가 없으므로 앵커 ①의 대상이 아니다. (b) `run_log` 블록이 없는 태스크는 검사 전체의 대상이 아니다(기존 §2.5 조항). (c) `--force` 통과는 `note` 자유 문자열에만 흔적이 남아 결정론 파싱이 불가하므로 앵커로 삼지 않는다 | C-2(결정론)를 지키려면 파싱 불가한 자유 서술을 앵커로 쓸 수 없다. 제외 사유를 조문에 적어 "판정 안 함"과 "미구현"을 구분한다 |
| D-5. 출력 **정렬**을 조문이 고정한다 | `row_id` 오름차순으로 앵커 ① 항목을 먼저, 앵커 ② 항목이 있으면 마지막에 1건 | 같은 입력에 같은 배열(순서 포함)을 보장한다(C-2) |
| D-6. 항목 **형태**를 고정한다 | 앵커 ①: `{"row_id", "row_key", "stage", "expected": "activity(decision)", "anchor": "auto_approved_row"}`. 앵커 ②: `{"row_id": null, "row_key": null, "stage": null, "expected": "activity(decision)", "anchor": "override_bundle"}` | `missing_state_changed` 항목(`state_tool.py:1322`)과 키 모양을 맞춰 소비자가 4종을 같은 방식으로 읽는다 |
| D-7. 폐쇄 검사는 **`validate_event()`**에 접합한다 | `event=="activity"` ∧ `actor.kind=="PM"` ∧ `provenance.type=="direct"`일 때 `data`가 있으면 키 집합이 정확히 `{"kind"}`여야 한다. 위반은 **`schema_invalid`** | 폐쇄 목록은 값 조합 인가가 아니라 **필드 집합 위반**이다. `run_log_core.py:896` `validate_provenance()`의 docstring이 "조합표 밖이거나 이 함수가 거부하면 `provenance_invalid` — `schema_invalid`는 `validate_event()` 소관"으로 두 판정기의 경계를 이미 못 박았고, `CONTRACT.md` §2.2 "사건 종류별 actor 제약 위반의 코드" 단락이 "`schema_invalid`는 §1.1 폐쇄형 최상위 키와 개별 필드 enum 위반에만 쓴다"로 같은 경계를 정한다. `validate_event()`는 이미 같은 위치(`run_log_core.py:803`)에서 `data.kind` 4종 enum을 판정하므로 접합점이 하나로 모인다 |
| D-8. **오류 코드를 신설하지 않는다** | `schema_invalid` 재사용. `RUN_LOG_ERROR_CODES`·`RUN_LOG_STATE_ERROR_CODES`·`ERROR_CODES` 어느 테이블도 키를 늘리지 않는다 | `CONTRACT.md` §2.2.1이 `schema_invalid`의 발생 표면으로 `run-log-tool.append`를 이미 등재하고 있어 `surfaces.json`과의 양방향 일치(MV-30)가 그대로 성립한다. 신설하면 3개 테이블의 물리 분리(C-7)와 표면 대응을 같은 변경 단위로 흔들어야 한다 |
| D-9. `state-tool.log-event`의 입력 검증은 **제거하지 않고 앞단 중복 방어로 유지**한다 | `_build_pm_activity_data()`는 그대로 두되, 계약이 "두 지점의 판정 결과는 항상 일치한다"를 명시한다 | CLI 인자 단계에서 더 구체적인 detail을 내는 이점이 있고, 제거하면 `TestPmActivityWhitelistRejection`(`test_state_tool_run_log.py:1009`)의 검증 축이 약해진다. `~/.opal/PRINCIPLES.md` §3 "Touch only what the plan names" |
| D-10. 조문의 **적용 조건은 넓히지 않는다** | 폐쇄는 `actor.kind=PM` ∧ `provenance.type=direct`(조합 A4)에만 적용한다. import 경로(A8)·adapter 경로(A1)는 조합 자체가 이 조문의 조건을 만족하지 않는다 | 조건을 A8까지 넓히는 것은 계약 확장이며 TASK 범위 밖이다. 실제로 막혀 있던 우회로는 `run_log_core.append()`를 직접 타는 A4 생산 경로(`run-log-tool.append` CLI, 인프로세스 호출)이고 AC-4가 지목하는 것도 그것이다 |
| D-11. S-16은 **`data` 축을 유지한 채 폐쇄 준수 값으로 교체**한다 | `test_run_log_tool.py:906`의 `--data '{"kind":"progress","x":1}'` → `'{"kind":"progress"}'` | S-16의 축은 "같은 `request_id` + 다른 payload → `request_id_conflict`"다. 기준 이벤트(`_append_activity_args`, `:102`)는 `--data`를 넘기지 않아 `data=None`이므로, `{"kind":"progress"}`만으로도 digest가 달라져 `data` 축의 차이라는 lever가 그대로 보존된다. actor를 바꾸면 세 variant(`diff_summary`/`diff_data`/`diff_stage`)의 기준 이벤트까지 갈아야 해 변경면이 커진다 |
| D-12. S-17은 **actor를 A7 `state.changed`로 옮긴다** | `test_run_log_tool.py:940-963`의 세 호출을 `--event state.changed --actor-kind tool --recorded-by-kind tool`, `--data '{"from":"pending","to":"in_progress","row_key":"plan.plan"}'`와 그 키 순서 치환으로 바꾼다 | S-17의 축은 "정규화가 키 순서·발급 필드에 불변"이고, 그 축은 **다중 키 `data`가 있어야** 성립한다. PM 폐쇄 후 PM `activity`의 `data`는 단일 키라 키 순서 자체가 사라져 축이 소멸한다(C-5 위반). A7 `state.changed`는 `from`/`to`/`row_key` 3키가 §1.2 필수라 실제 생산 payload로 3! 순열을 만들 수 있고, 폐쇄 조문의 적용 조건(A4) 밖이다. 발급 필드 불변 축(`event_id`/`sequence`/`timestamp`)은 actor와 무관하므로 그대로 보존된다 |
| D-13. RED-first 적용 구분 | **구현 전 RED**: 코어 폐쇄 거부 시나리오(신규), 완전성 진단의 트리거 충족 방향·미충족 방향(신규 2건). **보존·회귀 가드**: S-16·S-17 fixture 정정(현 구현에서도 통과해야 하며 GREEN 전후 불변), 기존 3스위트 전건 통과 | `~/.opal/references/harness/red-first.md` §1 "공개 동작을 테스트 코드로 먼저 고정할 수 있고 회귀 위험이 있는 변경에 적용한다". 신규 3건은 CLI/반환값 축이라 RED 관찰이 가능하고, fixture 정정은 행위 불변 변경이라 RED 대상이 아니다. 계약 문서 변경(W-1)도 RED 대상이 아니며 `state-tool validate`·0건 grep으로 검증한다 |
| D-14. AC-2·AC-5의 "0건" 판정 대상 문장 | 삭제: `docs/run-log/CONTRACT.md:478` 전체 문단, `docs/run-log/CONTRACT.md:131`의 "이 집행 지점은 `state-tool.log-event` CLI를 거치는 …는 이 폐쇄 검사를 받지 않는다." 1문장, `opal/tools/state-tool/README.md:514-515`의 "`missing_pm_activity`는 현재 트리거 조건이 확정되지 않아 항상 빈 배열이다(CONTRACT §2.5 참조)." 1문장, `opal/tools/state-tool/state_tool.py:1371-1372`의 누락 ④ 최소구현 주석. 교체: 같은 자리에 D-1~D-6 조문과 D-7~D-10 집행 지점 조문 | AC-2·AC-5는 유보 서술이 **0건**일 것을 요구하므로 삭제 대상을 파일:줄로 특정한다 |

폐기한 대안: 폐쇄 검사를 `validate_provenance()`에 넣고 `provenance_invalid`로 내는 안. `§1.3` 절에 조문이 있다는 이유만으로 고른 배치이며, 두 판정기의 오류 코드 경계(D-7 근거)를 깨고 `surfaces.json`의 `provenance_invalid` 표면 대응까지 흔든다.

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. 계약 조문 2건 확정 | opal-task-agent | `docs/run-log/CONTRACT.md` | §1.3 말미: `data` 위반의 집행 지점을 `run_log_core.validate_event()`로 바꾸고, `run_log_core.append()`를 통과하는 모든 A4 생산 경로에 동일 적용됨을 명시한다. `state-tool.log-event`의 `_build_pm_activity_data()`는 같은 규칙의 앞단 중복 방어이며 두 지점의 판정이 항상 일치함을 적는다(D-7·D-9·D-10). 범위 한정 문장 1건을 삭제한다(D-14). §2.5: `:478` 유보 문단을 삭제하고 그 자리에 `missing_pm_activity` 트리거 조문을 넣는다 — 앵커 2종(D-1), 대조 술어(D-2), 대조 집합(D-3), 범위 한정 3항(D-4), 정렬(D-5), 항목 형태(D-6). 오류 코드·표면 id는 신설하지 않음을 명시한다(D-8) | 없음 | P1 | AC-1, AC-2, AC-5, C-1, C-2, C-4 |
| W-2. 기록 코어 시나리오 — 폐쇄 RED + S-16·S-17 정정 | opal-task-agent | `opal/tools/run-log-tool/tests/test_run_log_tool.py` | (a) 신규 시나리오: `run_log_core.append()` 직접 호출과 `run-log-tool append` CLI 두 경로 각각에서 PM `activity`(A4)의 `data`에 `kind` 외 키를 실으면 `schema_invalid`로 거부되고 조각 바이트가 불변임을 검증한다. 같은 시나리오에 A8(import 조합) payload는 거부되지 않음을 함께 고정해 적용 조건 경계를 못 박는다(D-10). (b) `:906` S-16 `diff_data` variant의 `--data`를 `'{"kind":"progress"}'`로 바꾼다 — 세 variant 모두 `request_id_conflict`를 기대하는 단언은 그대로 둔다(D-11). (c) `:940-963` S-17의 세 append 호출을 A7 `state.changed`로 옮기고 `data` 3키 순열로 키 순서 불변을, `time.sleep(1.1)` 뒤 재호출로 발급 필드 불변을 그대로 검증한다. 클래스명·docstring의 검증 축 서술은 유지한다(D-12) | W-1 | P2 | AC-4, AC-6, C-5, C-1 |
| W-3. 완전성 진단 시나리오 — 트리거 양방향 RED | opal-task-agent | `opal/tools/state-tool/tests/test_state_tool_run_log.py` | 기존 `TestVerifyCompletenessCheckThreeObservationFields`(`:1287`) 옆에 신규 클래스를 추가한다. (a) 충족 방향: `owner="auto"` + `status="done"` + `key` 보유 행을 만들고 대응 PM `activity(decision)`를 기록하지 않은 fixture에서 `missing_pm_activity`가 비어 있지 않고 항목이 D-6 키 형태를 가짐을 검증한다. (b) 미충족 방향: 같은 행에 `task_step == row.key`인 PM `activity(decision)`를 `state-tool log-event`로 남긴 fixture에서 빈 배열임을 검증한다. (c) `run_log.status="overridden"`인데 `activity(decision)`가 없는 fixture에서 `anchor="override_bundle"` 항목 1건을 검증한다. (d) 모든 호출이 exit 0이고 `state.json` 바이트가 불변임을 검증한다. (e) `run_log` 블록이 없는 1.0/1.1 fixture에서 응답 키 집합이 종전과 동일함을 검증한다 | W-1 | P2 | AC-3, C-2, C-3, C-6 |
| W-7. 기준선 선행 실패 4건 정정 — 자기무효화된 HEAD 비교 기준 | opal-task-agent | `opal/tools/state-tool/tests/test_state_tool_run_log.py` | 실패 4건의 원인은 **2종**이다(실행 중 실측 정정). (i) `TestOffModeInitByteIdentical`·`TestOffModeDurationPathByteIdentical`(1.0/1.1 2건) 3건은 "개정 전 동작"을 `git show HEAD:./state_tool.py`로 대리하는데, 커밋 `f8aba0a`("run-log 기본 활성화")가 머지되며 HEAD 자신이 개정 후가 되어 영구 실패 상태다. (ii) `TestExistingRegressionBaseline`은 `git show`를 호출하지 않는다 — 중첩 pytest를 `["python3", "-m", "pytest", ...]`로 하드코딩 기동하는데, 커밋 `15fee62`가 신설한 테스트 인터프리터 게이트가 이를 거부해 스위트가 수집조차 되지 않는다. 즉 이 가드는 `15fee62` 머지 이후 회귀를 관측하지 못하는 상태였다. (i)는 비교 기준을 **개정 직전 커밋 SHA로 고정**하고, (ii)는 중첩 기동 인터프리터를 게이트를 통과하는 OPAL 테스트 인터프리터로 교체한다. 어느 경우도 단언을 약화하지 않는다. 어느 쪽이든 각 클래스의 원래 검증 축(무플래그·`off` 경로의 산출물 불변)이 여전히 관측되는 형태여야 하며, 축을 잃는 제거는 하지 않는다. `git show HEAD:` 패턴이 이 파일에 남아 있으면 같은 자기무효화가 재발하므로 잔존 0건을 확인한다 | W-3 | P3 | AC-6, C-5 |
| W-4. 기록 코어 폐쇄 집행 | opal-task-agent | `opal/tools/run-log-tool/run_log_core.py` | `validate_event()`의 activity 판정 블록(`:801-805`)에 PM A4 조건 분기를 덧붙인다 — `event=="activity"` ∧ `actor.kind=="PM"` ∧ `provenance.type=="direct"` ∧ `data is not None`이면 `set(data.keys()) != {"kind"}`를 `schema_invalid`로 거부하고 detail에 CONTRACT §1.3을 인용한다. 오류 코드 테이블·`COMBINATION_TABLE`·`validate_provenance()`는 손대지 않는다. `@header`의 `description`에 이 집행을, 필요 시 `exports`를 현재 사실로 갱신한다 | W-1, W-2 | P3 | AC-4, C-4, C-7, C-8 |
| W-5. 완전성 진단 PM 활동 누락 구현 | opal-task-agent | `opal/tools/state-tool/state_tool.py` | `_run_log_completeness_check()`의 누락 ④ 자리(`:1371`)에 D-1~D-6 조문을 그대로 구현한다 — `rows[]`에서 앵커 ① 후보를 `row_id` 오름차순으로 모으고 `_run_log_all_records()` 결과에서 대조 술어로 매칭, 이어서 `block.get("status")=="overridden"`이면 앵커 ② 1건을 뒤에 붙인다. 상태 파일을 쓰지 않고 exit 0을 유지한다. `_build_pm_activity_data()`는 유지하되 docstring에 "코어 집행의 앞단 중복 방어"를 적는다(D-9). 함수 docstring과 `@header` `description`에서 "최소 구현" 서술을 제거하고 현재 사실로 갱신한다 | W-1, W-3 | P3 | AC-3, AC-7, C-2, C-3, C-4, C-6 |
| W-6. 문서 미러 갱신과 전건 회귀 | opal-task-agent | `opal/tools/state-tool/README.md` | `:514-515`의 유보 문장을 삭제하고 트리거 앵커 2종의 1줄 요약과 CONTRACT §2.5 포인터로 바꾼다(계약 원문은 복제하지 않는다). 이어서 `test_run_log_tool.py`·`test_state_tool_run_log.py`·`test_state_tool.py` 3스위트를 전건 실행하고, `state-tool validate`가 violations 0인지, CONTRACT·README에서 유보 서술 grep이 0건인지 확인한다. `~/.opal` 배포본은 수정하지 않는다 | W-4, W-5 | P4 | AC-2, AC-6, AC-7, C-8 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. 코어 폐쇄가 S-16·S-17 외의 기존 fixture도 깬다는 가정이 틀릴 수 있다 | `test_run_log_tool.py` 전건 통과(AC-6) | GREEN 전환이 예상 밖 지점에서 막힌다 | 실측으로 범위를 좁혀 뒀다 — `:2014`·`:2084`·`:2121`의 다중 키 `data`는 `core.redact()` 직접 호출이거나 actor가 `worker`라 A4 조건 밖이고, `:2187`·`:2290`의 filler는 `append()`를 거치지 않고 파일에 직접 쓰며 `validate_run()`은 스키마를 재판정하지 않는다(`run_log_core.py:1159-1207`). W-2가 3스위트를 돌려 이 가정을 먼저 확인하고, 추가 위반 fixture가 나오면 C-5 판단이 필요하므로 블로커로 올린다 |
| H-2. 앵커 ①이 기존 태스크에서 대량 발화할 수 있다 | 진단 신호 대 잡음 비 | 운영자가 `missing_pm_activity`를 무시하게 되어 AC-1의 목적이 무력화된다 | 진단은 read-only·비차단(C-3)이라 실행을 막지 않는다. W-3 (a)/(b) 두 방향 시나리오가 "기록하면 사라진다"를 고정해 발화가 해소 가능한 신호임을 보장한다. 발화량이 실제로 과다하면 앵커 축소가 아니라 계약 개정(W-1 재실행) 대상이다 |
| H-3. S-17을 `state.changed`로 옮기면 `run-log-tool append` CLI가 A7 조합을 그대로 수용한다는 가정에 의존한다 | S-17의 두 단언(키 순서 불변·발급 필드 불변) | 시나리오가 검증 축이 아닌 사유로 실패한다 | `run_log_tool.py:136-160`의 append 파서가 `--event`/`--actor-kind`/`--recorded-by-kind`/`--data`를 자유 문자열로 받고 `COMBINATION_TABLE`에 A7(`tool`/`direct`/`tool`/`null`)이 있음을 확인했다. W-2가 정정 직후 S-17 단독 실행으로 이 가정을 먼저 관측한다 |

| H-4. W-7의 "개정 직전 커밋" 특정이 틀릴 수 있다 | 4건의 원래 검증 축(무플래그·`off` 경로 산출물 불변) | 기준을 잘못 고정하면 가드가 통과하지만 아무것도 지키지 않는다 | `f8aba0a`가 기본값을 바꾼 커밋임은 실측 확인했다(현재 무플래그 `init` → `schema_version 1.2` + `run_log` 블록). W-7은 후보 SHA로 `git show <SHA>:./state_tool.py`를 실제 실행해 그 버전의 무플래그 `init`이 `run_log` 블록을 만들지 않음을 먼저 관측한 뒤에만 고정한다. 관측되지 않으면 SHA 고정 대신 가드 명시 폐기 경로를 택하고 사유를 주석에 남긴다 |

## Release and recovery

- 적용 순서: P1(계약) → P2(시나리오·fixture) → P3(구현) → P4(미러·회귀). 배포(install)는 이 태스크 범위 밖이므로(C-8, TASK `범위 제외`) 프로젝트 소스 커밋까지가 종료 지점이다.
- 검증 범위: 결정론 검사 — `~/.opal/tools/state-tool/run.sh validate <task-path>` violations 0(AC-7), CONTRACT·README 유보 서술 grep 0건(AC-2·AC-5). 회귀 — `test_run_log_tool.py`·`test_state_tool_run_log.py`·`test_state_tool.py` 3스위트 전건 통과, 135 시점 대비 신규 실패 0건(AC-6). 실제 연동 — 완전성 진단은 CLI(`verify --run-log-completeness-check`) 반환값으로, 폐쇄는 코어 직접 호출과 CLI 두 경로 반환값으로 관측한다(내부 private 함수 단언에 의존하지 않는다).
- 실패 시: 배포·설치가 없으므로 복구는 작업본 되돌리기다. P3에서 회귀가 나면 P2의 시나리오를 약화시키지 않고 P1의 조문으로 되돌아가 재확정한다(C-1). W-2가 C-5 범위를 넘는 fixture 수정을 요구하면 진행하지 않고 블로커로 반환한다.
