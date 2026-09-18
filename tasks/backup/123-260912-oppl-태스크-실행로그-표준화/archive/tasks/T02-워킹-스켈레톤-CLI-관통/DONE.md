# DONE: T02 — 워킹 스켈레톤 (CLI 관통 1건)

## 결과

태스크 실행 로그의 **끝에서 끝까지 관통 경로 1건**이 실제로 살아 있다. 목·스텁이 아니다.

`state-tool init --run-log-mode shadow`가 스키마 1.2 `state.json`(§1.4 로그 계약 블록 7필드)과 첫 기록 조각을
outbox 2단 원자 커밋(`status=pending` → 기록 코어 `init`/`append` → `status=active`, D-2)으로 함께 만들고,
`run-log-tool append` 1건이 붙고, `run-log-tool validate-run`이 `verdict=pass`로 그 경로를 통과한다(AC-2).

커버 표면 4종이 실제로 호출 가능하다 — `state-tool.init.run-log-mode`, `run-log-tool.init`,
`run-log-tool.append`, `run-log-tool.validate-run`.

**확정 결정 준수**
- D-1 — 실행 이력은 `<task-path>/run/run-log-{run_id}-{segment}.jsonl` append 전용 줄 단위 조각에 둔다. 상태 파일에 사건 배열을 만들지 않았다.
- D-5 — 의존은 상태 도구 → 기록 코어 **단방향**이다. `run_log_core.py`·`run_log_tool.py`에 `state_tool` import와 `state.json` 문자열이 **0건**이며, 기록 도구 테스트는 상태 자산 없이 통과한다(AC-19 / MV-24). 상태 도구는 락을 쥔 채 같은 프로세스에서 `lock_held=True`로 코어를 호출한다(§2.6).
- D-7 — 로그 계약 활성화 여부는 `state.json`의 `run_log` 필수 블록이 소유한다. 별도 매니페스트 파일을 만들지 않았다.
- D-9 — 디스크 쓰기 직전 공통 마스킹 초크포인트 `run_log_core.redact()`(멱등 계약)를 **모든 writer 경로에 배선**했다: 조각 writer, `_atomic_write_state_json`, `save_state_json`. T02에서는 pass-through이며 **T06이 이 함수 본문만 채우면 된다**.
- §3.2 경로 계약 — 기록 경로는 전달받은 절대 task path로만 해석한다. cwd·워크트리 문자열로 추론하지 않으며 상대 경로는 `task_path_not_absolute`로 거부한다.

**유지된 기존 동작 (회귀 보전)**
- C-2 — 기존 `state-tool` 테스트 **428 passed, 3 skipped, 111 subtests passed**(기준선 425 + 신규 3건, 실패 0건). `tests/test_state_tool.py`와 `schema/state.schema.json`은 **한 줄도 수정하지 않았다**.
- C-3 — `--run-log-mode` **미지정** init은 개정 전과 `state.json` **바이트 동일**하다(`run_log` 키 부재, `run/` 미생성, 권한 644 유지). 스키마 1.0/1.1 태스크의 자동 강등·자동 이동 없음.
- `state_tool.ERROR_CODES` 딕셔너리 리터럴은 HEAD와 **바이트 동일**(69키)이다 — run-log 오류 코드는 `run_log_core.RUN_LOG_ERROR_CODES`와 `state_tool.RUN_LOG_STATE_ERROR_CODES` 별도 테이블이 소유하고 `err()`는 조회만 합성한다. 동결 단언 4건을 우회가 아니라 경계 분리로 통과했다.

**응답 봉투 2종 병존 (의도된 경계)**
- `run-log-tool`·`run_log_core`: CONTRACT §2.1 중첩 봉투 `{"ok":false,"error":{"code","message","detail"}}`
- `state-tool`: 기존 평면 봉투 유지(동결 테스트·기존 도구 관례 보전)
- 경계를 `opal/tools/run-log-tool/README.md`에 명시했다. `CONTRACT.md`는 수정하지 않았다.

## 변경 파일

신규
- `opal/tools/run-log-tool/run_log_core.py`
- `opal/tools/run-log-tool/run_log_tool.py`
- `opal/tools/run-log-tool/run.sh`
- `opal/tools/run-log-tool/README.md`
- `opal/tools/run-log-tool/tests/test_run_log_tool.py`
- `opal/tools/state-tool/tests/test_state_tool_run_log.py`

수정
- `opal/tools/state-tool/state_tool.py`
- `scripts/install-mac.sh` (run-log-tool chmod 배선 — **install 미실행**)
- `.gitignore` (추적 경계 4패턴)
- `docs/CONVENTIONS.md`, `docs/PROJECT.md` (도구 종수 20 → 21)

## 검증

- `python3 -m pytest opal/tools/run-log-tool/tests/ -q` → **8 passed**
- `python3 -m pytest opal/tools/state-tool/tests/test_state_tool_run_log.py -q` → **3 passed**
- `python3 -m pytest opal/tools/state-tool/tests/ -q` → **428 passed, 3 skipped, 111 subtests passed** (실패 0건, C-2)
- 시나리오 9건 전건 `pass` / 충실도 `real-usage` 9/9 met — 원본은 `test-scenario.json`이 소유
- RED-first: `scenario-red` 7/7 실관찰 기록 후 `scenario-lock` 통과, 그 뒤 구현 진입
- 관통 실증(오케스트레이터 독립 실행): shadow init → `schema_version 1.2` + `run_log` 7필드 + 조각 1줄(`run.started`, `sequence=1`, `actor_sequence=1`, `actor.kind=tool`, `timestamp` RFC3339 밀리초 Z) → append(`sequence=2`, `idempotent_hit=false`) → validate-run(`verdict=pass`, `event_count=2`, `sequence_gaps=[]`, `violations=[]`)
- 심볼릭 링크 선점 공격 3종 실제 재현 → 전건 차단(victim 내용·권한 불변): 락 링크 → `task_lock_timeout` / `run/` 디렉터리 링크 → `run_log_write_failed` / `state.json.tmp.*` 5000건 링크 선점 → 무영향
- 파일 권한: run-log 경로 `state.json`·조각·락 `0600`, `run/` `0700`. 미지정 경로 `state.json` `644` 유지
- 구현 전 명세 리뷰(G, 별도 Evaluator) `verdict: pass` — `QA-SPEC.md`
- 규칙검사: 보안 최종 `pass`(blocking 0, advisory 4 + info 2), 컨벤션 `pass`

## 회고적 학습 후보

없음

## 참고

**배포 — PM 승인 필요**
`./scripts/install-mac.sh`를 **실행하지 않았다**(TASK C-1). 배포 후 확인 항목 2건:
(a) `~/.opal/tools/run-log-tool/run.sh`가 실행 가능하고 `init`이 응답한다,
(b) 배포본 `state-tool init --run-log-mode shadow`가 관통한다 — 기록 코어는 `importlib.util.spec_from_file_location`으로 형제 배치 우선 적재하므로 배포 레이아웃에서 성립해야 한다(PLAN H-3).

**한시 조치 — 복귀 조건 있음**
`.gitignore`의 `tasks/**/run/*.jsonl` 제외는 **한시적**이다. AC-14는 "마스킹된 segment는 추적된다"를 요구하지만
현재 `redact()`가 pass-through이므로 지금 조각을 추적하면 마스킹되지 않은 내용이 git 히스토리에 들어가고,
히스토리 진입 후에는 회수가 불가능하다(TRD D-9가 사후 스캔 b안을 기각한 이유).
**복귀 조건: T06이 `redact()` 본문을 구현하면 이 줄을 제거한다.** `.gitignore` 해당 위치에 같은 주석을 남겨 두었다.
같은 블록의 `tasks/**/run/raw/`·`tasks/**/run/.runtime/`·`.opal-task.lock` 3패턴은 영구 규칙이다.

**후속 태스크 인계**

| 항목 | 소유 |
|---|---|
| `state.schema.json`에 `schema_version` `"1.2"`·`run_log` 등재 + `test_schema_version_enum_allows_1_0_and_1_1` 기대 집합 동반 갱신 (현재 런타임 1.2 ↔ 정적 스키마 1.0/1.1 드리프트. `cmd_validate`가 이 파일을 참조하지 않아 런타임 판정에는 무해) | T05 |
| 사건 어휘 12종 전수·§1.3 허용 조합 전수·16 KiB 상한·`request_id` 멱등 충돌·`--data` 크기 상한(GC-009) | T03 |
| outbox `status: pending` 반제 상태 회수 분기 부재(GC-203) — 락 선점 실패 시 영구 잔존, 재시도가 `already_initialized`로 거부됨 | T03 |
| 배타 락 경합·런타임 색인(`run/.runtime/`)·조각 경계 전환(4 MiB)·순번 색인 재구축 | T04 |
| 미전송 사건 보관함 전량(상한·admission·override)·중단 가능 초기화·복구 reconcile | T05 |
| `redact()` 본문 구현 + `.gitignore` 한시 제외 복귀 + 원본 상한·시간계 | T06 |
| 변환기(adapter) | T07 |

**보안 잔여 항목 (최종 검사 `pass`, blocking 0 — 차단 사유 아님)**

| ID | 내용 | 권고 |
|---|---|---|
| GC-204 (info, **선행**) | `docs/SECURITY.md` §1이 이번에 방어한 공격자 모델(태스크 디렉터리 로컬 쓰기)을 선언하지 않는다. CWE-59·367 미채택. **이 항목이 나머지 집행 수준을 좌우한다** — §1에 해당 표면을 채택하면 GC-201·202가 blocking으로 재평가되어야 한다. 소유자 판단 필요 | 선행 결정 |
| GC-201 (advisory) | 조각 파일 **하드링크** 선점 — `O_NOFOLLOW`는 심링크만 막는다. macOS 실측 성공. 수정은 `os.fstat(fd).st_nlink != 1` 3줄 | GC-202와 함께 |
| GC-202 (advisory) | `_ensure_run_dir`가 검증된 dirfd를 닫고 경로만 반환해 검사가 open까지 이어지지 않는다(TOCTOU 잔존). `dir_fd=` openat 전환 | GC-201과 함께 |
| GC-205 / GC-206 (info) | 락 open의 전 `OSError` 일괄 재시도로 오류 코드 오도 / `os.fdopen` 실패 시 fd 누수 | 여력 시 |

수용 가능한 잔여 위험: 락 선점 시 30초 지연(§2.7 상한 준수), 미지정 경로 `state.json` 644(S-2 바이트 동일성 보전을 위한 의도된 계약), `redact()` pass-through(T06 범위 — 배선은 닫혔다).

**PM 판단 필요 (계약·백로그 — 워커 권한 밖)**

| 항목 | 내용 |
|---|---|
| `CONTRACT.md` §2.1 서술 정정 | §2.1이 "기존 도구 관례를 복제한다"며 중첩 봉투를 정하지만, 실측상 `state_tool.py`·`backlog_tool.py`는 **평면** 봉투다 — 인용한 선례를 잘못 서술하고 있다. 계약 본문 정정은 PM 소관이라 수정하지 않았다(G 게이트 F-1) |
| `backlog.json` `covers` 보강 | `run-log-tool.append`의 잔여 계약(§1.3 조합 전수·16 KiB·멱등 = MV-1·2·3·5·6)을 T03이 완성하지만 T03의 `covers`에는 이 표면이 없다. 현재 이 표면을 `covers`로 가진 태스크는 T02뿐이라 게이트상 미소유로 남는다(G 게이트 F-3). `backlog.json`은 PM 단독 오너십이라 갱신하지 않았다 |
| `state-tool.init.run-log-mode`의 active 3종 분기 미배정 | `profile_not_found`·`profile_receipt_mismatch`·`cooperative_active_rejected`(MV-23 / AC-18). T02는 배정 파일 미배포 상태에서 계약상 정확한 `profile_not_found`로 거부한다. C-6(Phase 0 실측 없이 active 승격 금지)과 T01 의존 때문에 T02가 끝까지 구현할 수 없다. 권고는 T07 편입 |

**표면 conformance 게이트 참고**
`test-tool scenario-conformance`는 `surfaces.json` **19종 전체**를 분모로 삼아 `surface_unverified`(exit 14)를 반환한다.
미검증 15종은 전부 T03~T12 소유이며 **T02 커버 4종은 전건 green**이다. T02 범위 내 결함이 아니라 태스크 집합 수준의 커버리지 지표다.
