# DONE: 태스크 실행 로그 — 기록 기반 완성

## 결과

기록 계층이 자기 계약을 거짓 없이 지키는 상태가 됐다. 앞선 수행이 남긴 세 공백이 닫혔다.

**마스킹이 실동작한다.** `redact()`가 pass-through를 벗고 환경변수형 비밀값·`Bearer`/token·API key·private key 블록 4종을 문자열 값 안에서만 치환한다. 키 집합·타입·중첩 구조는 보존되고 멱등 계약이 유지된다. 마스킹은 모든 writer가 통과하는 공통 경로 한 곳에서만 일어나며, 상태 보관함 경로도 `_atomic_write_state_json()`이 같은 초크포인트를 타므로 자동으로 덮인다. `event_id`·`sha256`·`worker_log_token_id`처럼 비밀값과 형태가 비슷한 식별자는 마스킹 대상에서 갈라져 멱등 판정·출처 대조·순번 발급이 어긋나지 않는다. 마스킹을 안전하게 판정할 수 없는 입력은 저장을 거부하고 `redaction_failed`를 반환한다.

**추적 경계가 계약대로 복귀했다.** 마스킹 검증을 통과한 뒤에만 `.gitignore`의 한시 제외를 제거했다. 이제 `tasks/**/run/raw/`·`tasks/**/run/.runtime/`·`.opal-task.lock`은 영구 제외되고 마스킹된 조각은 추적된다. 실행 이력이 태스크 증거로 보존된다.

**조각이 무한히 커지지 않는다.** 4 MiB 상한에 다음 단일 사건의 최대 크기(16 KiB) 여유가 남지 않으면 다음 번호 조각으로 전환한다. 상한 검사·번호 선택·조각 생성이 기존 배타 락 구간 안에서 연속 수행되어 경계 동시 append에서도 새 조각이 정확히 하나만 생긴다. 닫힌 조각은 다시 열리지 않고, `scan_run()`이 번호 순 전 조각을 열거하므로 run 전역 순번과 요청 식별자 멱등 판정 범위가 조각을 넘어 유지된다. 새 조각 경로도 기존 심볼릭 링크·경계 이탈 방어와 0600/0700 권한을 그대로 거친다.

**실행 시간이 단일 원천에서 자동 파생된다.** terminal 사건의 `data.duration_spans[]` 합이 `duration_ms`와 다르거나 같은 `source_id`가 중복되면 append 시점에 거부된다. 시각 차분이 아니라 단조 시계 구간 합이다. `run-log-tool reconcile-duration`이 파생 조회를 노출하고, 스키마 1.2 태스크에서 `state-tool mark`가 그 값을 읽어 `worker_duration_minutes`를 자동 기록한다. 수동 `--worker-duration-minutes`가 파생값과 같으면 deprecated 경고와 함께 수용하고, 다르면 상태를 건드리기 전에 `worker_duration_conflict`로 거부한다. 대상 워커는 해당 run의 terminal이 정확히 한 종일 때만 정해지며, 모호하면 추측하지 않고 기존 수동 경로로 돌아간다.

**시간대 해석이 설정 계층에서 끝난다.** 야간 제외 구간 설정에 `timeZone` 하위 키가 더해졌고, 기존 2층 머지·`enabled`·`start == end` 폴백 규칙은 그대로다. 유효하지 않은 IANA 이름은 예외 없이 `Asia/Seoul`로 폴백하며 설정 파일을 다시 쓰지 않는다. 캐시 토큰이 시간대를 서명에 포함해 시간대만 다른 두 설정이 같은 캐시 키를 공유하지 않는다.

**유지된 것.** 앞선 수행이 확보한 동작이 하나도 깨지지 않았다 — 멱등, 4축 조합 거부, 상태 보관함 복구, legacy·Project Loop 단방향 가져오기, I/O 방어. 스키마 1.0/1.1 태스크는 계속 실행 가능하고 `--run-log-mode` 미지정 경로의 산출물·응답 키 집합이 종전과 동일하다. `stats.py`는 무접촉이며 `quiet_hours` 인자 형태가 2튜플로 유지된다 — 3필드 `QuietHours`는 설정·라우터 계층 안에서만 흐른다. 기록 코어는 여전히 상태 원천 파일을 읽지 않는다.

**적용한 경계.** 확정 설계 결정(TRD D-1~D-9)과 `CONTRACT.md`·`TRD.md`·`PRD.md`는 바꾸지 않았다. `surfaces.json`은 소유자 승인 하에 `reconcile-duration` 표면의 `optional`에 `--worker-run-id` 한 항목만 추가했다(PLAN D-P14) — 코드가 앞서 있던 문서를 코드에 맞춘 단방향 동기화다. `~/.opal/` 배포 파일은 수정하지 않았고 install을 실행하지 않았다.

## 변경 파일

- `.gitignore`
- `docs/run-log/surfaces.json`
- `opal/core/setting.default.json`
- `opal/tools/run-log-tool/run_log_core.py`
- `opal/tools/run-log-tool/run_log_tool.py`
- `opal/tools/run-log-tool/tests/test_run_log_tool.py`
- `opal/tools/state-tool/state_tool.py`
- `opal/tools/state-tool/tests/test_state_tool_run_log.py`
- `dashboard/backend/config.py`
- `dashboard/backend/routers/tasks.py`
- `dashboard/backend/routers/dashboard.py`
- `dashboard/backend/tests/test_config.py`
- `tasks/123-260912-oppl-태스크-실행로그-표준화/TASK.md`
- `tasks/123-260912-oppl-태스크-실행로그-표준화/ANALYSIS.md`
- `tasks/123-260912-oppl-태스크-실행로그-표준화/PLAN.md`
- `tasks/123-260912-oppl-태스크-실행로그-표준화/TEST-SCENARIO.md`
- `tasks/123-260912-oppl-태스크-실행로그-표준화/DONE.md`
- `tasks/123-260912-oppl-태스크-실행로그-표준화/GC-CONVENTION-20260915-1301.md`
- `tasks/123-260912-oppl-태스크-실행로그-표준화/GC-CONVENTION-20260915-1302.md`
- `tasks/123-260912-oppl-태스크-실행로그-표준화/test-scenario.json`
- `tasks/123-260912-oppl-태스크-실행로그-표준화/.scenario-coverage-input.json`
- `tasks/123-260912-oppl-태스크-실행로그-표준화/.scenario-gate-history.json`
- `tasks/123-260912-oppl-태스크-실행로그-표준화/state.json`
- `tasks/123-260912-oppl-태스크-실행로그-표준화/STATE.md`

## 검증

- `python3 -m pytest opal/tools/run-log-tool/tests/ -q` → exit 0, `53 passed, 4 subtests passed` (기준선 36 passed 대비 신규 17건 추가, 실패 0)
- `python3 -m pytest opal/tools/state-tool/tests/ -q` → exit 0, `457 passed, 3 skipped, 111 subtests passed` (기준선 452 passed 대비 +5, 실패 0)
- `python3 -m pytest dashboard/backend/tests/ -q` → `348 passed, 36 failed`. 실패 36건은 전부 `test_routers.py` 소속의 사전 존재 환경 결함이며 기준선 대비 증가 0이다. 같은 코드가 허브에서 `376 passed, 0 failed`로 전건 통과함을 교차 실행으로 확인했다.
- `test-tool scenario-status` → `locked: true`, `total: 19`, `passed: 19`, `failed: 0`, `blocked: 0`
- `test-tool scenario-fidelity-check` → `all_met: true`, `19/19` (real-usage 12 · mock 7)
- `test-tool scenario-coverage-check` → exit 0 (requirements 15 · hypotheses 6 · scenarios 19, 커버 누락 0)
- `opal-evaluator-agent scenario-rubric` (iteration 1) → `verdict: pass`, 목표 2 · 채택 2 · 경계 2, gaps 0
- `state-tool verify --plan-contract-check` → `pass` (W-1~W-10)
- `state-tool verify --code-scan-citation-check` → `pass`
- `state-tool verify --clarification-check` → `pass`
- `state-tool validate` → `violations: 0`
- `code-scan validate --changed <변경 9파일>` → `ok: true`, 커버리지 9/9 (100%), `newly_uncovered: 0`
- `op-gc-convention` 2영역 → Critical 0 · High 0 (Framework Medium 1건은 `@header.exports` 보정으로 해소, Console BE 0건)
- 계약 오류 코드 양방향 대조 → `CONTRACT.md` §2.2 · §2.2.1 · `surfaces.json` `err` 23건 완전 일치, 이번 신설 어긋남 0건
- 추적 경계 실측 → `git check-ignore -v`로 영구 3규칙 적용·조각 경로 미적용 확인, 실제 조각 생성 후 평문 비밀값 0건 확인

## 회고적 학습 후보

.opal/brain/pages/concept/wallclock-field-breaks-byte-identity-assertion.md
.opal/brain/pages/concept/tuple-subclass-attribute-over-namedtuple-eq-override.md
.opal/brain/pages/concept/masking-before-tracking-boundary-restore.md

## 참고

**후속 이관 — 이 태스크 범위 밖으로 확정된 항목**

| 항목 | 대응 AC | 사유 |
|---|---|---|
| 런타임 색인과 재구축 | AC-9 | 실측이 병목을 보이지 않는다(누적 1,300건 append 평균 6.46 ms·총 5.2초). 색인은 조각 전환과 같은 파일·같은 락 구간을 건드려 AC-8의 위험을 키운다. 소유자 승인으로 합격 기준에서 제외 범위로 이관 |
| 완료 게이트 강제 집행 | AC-4·5·11·16 | 배포 후 그림자 표본 축적이 선행 조건 |
| 채널 변환기(adapter) | — | 강제 승격과 한 묶음 |
| 파이프라인 10종 확산·규범 개정 | AC-17·18 | 다른 파일럿 스킬과 하네스 문서를 건드려 파일 경계가 다르다 |

**이번 수행에서 발견된 별도 태스크 후보**

1. **Console 프로젝트 탐색과 워크트리 깊이 불일치** — `dashboard/backend/tests/test_routers.py` 36건이 워크트리 안에서만 실패한다. 워크트리가 `scan_roots` 기준 depth 3인데 `console.config.json`의 `scan_depth`가 2라 `_find_project_path()`가 `None`을 반환해 전부 404가 된다. 테스트는 "워크트리 안에서 실행하면 그 워크트리 자신이 기준 루트"를 전제하는데 Console의 project-discovery 계약이 그렇지 않다. 허브에서는 전건 통과한다.
2. **`install-mac.sh`의 시드 병합이 하위 키를 전파하지 않는다** — `SEED_KEYS` 루프가 top-level 키 존재 여부만 보고 건너뛴다(`if key in existing: continue`). 이미 `quietHours`를 가진 기존 사용자는 재설치해도 신규 `timeZone` 하위 키를 받지 못한다. 이번에는 `load_quiet_hours()`의 `Asia/Seoul` 폴백이 간극을 메우지만, 앞으로 어떤 설정 하위 키를 늘려도 같은 문제가 반복된다.
3. **`test-tool`에 `red_required` 갱신 경로가 없다** — 시나리오 성격을 잘못 배정했을 때 되돌리려면 `scenario-init` 재실행뿐이고, 그러면 이미 확보한 RED 증거가 전량 초기화된다. 이번 수행에서 S-9 한 건을 정정하느라 10건의 RED 증거를 재실행으로 복구해야 했다.
4. **워커 반환 문구가 실제 수행과 어긋나는 패턴** — 긴 포그라운드 명령 뒤 존재하지 않는 알림을 기다린다고 보고하며 종료하는 사례가 8건 누적됐다. 산출물은 정상인 경우가 대부분이라, 워커 자기보고의 부재를 산출물의 부재로 간주하지 않는 실측 판정 절차가 매번 필요했다.

**계약의 사전 존재 격차 (이번 변경과 무관, 참고용)**

- 계약에만 있고 구현에 없는 오류 코드 10건 — `worker_token_invalid`·`capability_expiry_invalid`·`capability_scope_invalid`·`run_log_inconsistent`·`completion_evidence_missing`·`gate_not_requested`·`gate_duplicate`·`profile_receipt_mismatch`·`cooperative_active_rejected`·`actor_not_allowed`. 소속 표면 자체가 위 후속 이관 범위에 속해 미구현이다.
- 구현에만 있고 계약에 없는 오류 코드 1건 — `run_log_core`의 `run_id_invalid`.

**실행 상태**

- `run` 개념 2종(`state.json` 최상위 `run_id`와 `run_log.active_run_id`)이 공존한다. JSON 경로가 달라 충돌은 없으며 통합 여부는 양쪽 계약을 함께 보아야 하므로 이 태스크가 정하지 않았다.
- 커밋은 수행하지 않았다.
