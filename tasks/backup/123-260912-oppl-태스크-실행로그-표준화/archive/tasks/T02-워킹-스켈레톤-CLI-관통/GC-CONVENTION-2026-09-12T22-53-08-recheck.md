# GC CONVENTION REPORT — 2026-09-12T22-53-08 (재검사)

## 1. 헤더

- 실행 일시: 시작 2026-09-12 22:53 / 완료 2026-09-12 22:56 / 소요 약 3분
- 범위: T4b 재검사 (직전 지적 GC-C001 재판정 + 2차 변경분)
- 대상 파일: `opal/tools/run-log-tool/run_log_core.py`, `opal/tools/state-tool/state_tool.py`, `.gitignore` (컨텍스트: 직전 실행 대상 10개 파일 전량 재확인)
- 에이전트: opal-convention-checker
- 기준 문서: `docs/CONVENTIONS.md` (존재) + `opal/core/references/header-standard.md` §2.1(CONVENTIONS.md가 인용하는 @header 이력 비기재 원칙)
- APPLY 수행 여부: N (수동 대기 — read-only 진단)

---

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 총 이슈 수 | 1 |
| 심각도 분포 | Critical 0 / High 0 / Medium 1 / Low 0 / Info 0 |
| 자동 수정 가능 | 0 |
| 수동 조치 필요 | 1 |
| 파일별 상위 | `opal/tools/state-tool/state_tool.py` (1건) |
| 카테고리별 빈도 | 문서화(@header 이력 비기재) — 1 파일 (빈도 트리거 미발동, N<3) |
| Critical/High 수 | 0 |
| 문서 업데이트 제안 수 | 0 |

---

## 3. GC-C001 재판정

**판정: 부분(partial) — 원 지적은 닫혔으나 그 수정 과정에서 같은 원칙의 별건 위반이 남았다.**

- **원 지적**(`state_tool.py:6`): `@header.description`이 `--run-log-mode` 신규 동작을 반영하지 않음.
- **닫힘 근거**: 현재 `description`은 `--run-log-mode {shadow,active}`, `RUN_LOG_STATE_ERROR_CODES`, `_cmd_init_run_log`/`_atomic_write_state_json`/`_import_run_log_core`/`_run_log_core_dir`/`_error_template` 5개 신규 헬퍼, GC-001·003~008 대응 보안 수정을 모두 "현재 사실" 서술로 포함한다(`opal/tools/state-tool/state_tool.py:6`, `git diff HEAD~ -- opal/tools/state-tool/state_tool.py`로 신규 함수 5종·심볼 전건 대응 확인). 미래 계획·작업 이력 서술(TODO, 시점 나열) 형태는 없다.
- **미해결 잔여**: 같은 `description` 안에 서로 다른 태스크 번호 **2개**(`118`, `123`)가 남아 있다 — `task_root()` 설명의 `(118 D-4)`·`(118 D-4b, AC-4)`와 `_cmd_init_run_log` 관련 `(123 T02)`. `opal/core/references/header-standard.md` §2.1·§4.2는 "자산의 출신 태스크 1개를 단발로 인용하는 것은 허용"하되 "서로 다른 태스크 번호가 2개 이상 쌓이는 형태"는 이력 누적으로 금지한다. `code-scan validate`가 이 축을 그대로 집행한다(아래 GC-C002).
- **재현 근거**:
  ```
  node opal/tools/code-scan/code-scan.js validate --project-root . \
    --changed opal/tools/state-tool/state_tool.py --json
  → {"header_history":1}, violations: [{"code":"header_history","sub":"description",
     "file":"opal/tools/state-tool/state_tool.py","detail":"118,123","tasks":2}]
  ```

---

## 4. 수정 대상 (체크리스트)

### Medium (1건)

- [ ] GC-C002 [opal/tools/state-tool/state_tool.py:6] `@header.description`에 서로 다른 태스크 번호 2건(`118`, `123`)이 누적 — header-standard.md §2.1 이력 비기재 원칙 위반
  - 카테고리: 문서화 (@header 이력 비기재)
  - 위반 기준: 프로젝트(`opal/core/references/header-standard.md` §2.1·§4.2, `docs/CONVENTIONS.md` "코드 `@header`에는 현재 사실만 기재한다" 절이 인용)
  - 설명: `task_root()`·CLOSE 관련 서술이 `118`을 인용하고, `_cmd_init_run_log` 관련 서술이 `123`을 인용한다. 두 태스크 번호가 한 `description` 필드에 공존하는 것은 "서로 다른 태스크 번호 2개 이상 쌓이는 형태"에 해당해 이력 누적 금지 규칙을 위반한다. `code-scan validate`가 `header_history`(비차단, advisory)로 이를 집계한다.
  - 해결 방안: `118` 인용부(`task_root()`, CLOSE 관련 두 문장)를 시점 표기 없이 현재 사실만으로 재서술하거나(예: "task_root()는 ... 탐색이며, 허브 쓰기 대상인 allocator root는 이 탐색으로 추론하지 않는다" — `(118 D-4)` 태그 제거), 두 태스크 태그 중 1개만 남긴다. 이력 근거가 필요하면 git log·`tasks/118-*/DONE.md`로 이관한다.
  - 자동 수정: N
  - 참조: `opal/core/references/header-standard.md` §2.1·§4.2
  - disposition: advisory (T0, non-blocking — `code-scan validate`의 `ok`는 `true` 유지)

---

## 5. 2차 변경분 신규 위반 확인

| 대상 | 결과 |
|---|---|
| `opal/tools/run-log-tool/run_log_core.py` (보안 수정 다수, header 갱신) | 위반 없음 — `code-scan validate` 0건. `description`의 다수 코드(`GC-003~008`, `D-3/D-9/D-A/D-C/D-G/D-I`, `T02`, `T04`, `T06`)는 전부 `letters-digits` 접두 하이픈 패턴(M4 마스킹 대상)이거나 단일 태스크(`T02`)이며 별개 3자리 순수 태스크 번호가 2개 이상 공존하지 않는다. |
| `opal/tools/state-tool/state_tool.py` (`importlib` 적재, outbox redact, header 갱신) | header 갱신 자체는 §4.2 GC-C002(위) 1건 외 위반 없음. `_import_run_log_core()`(importlib.util.spec_from_file_location 단일 파일 로드, `sys.path` 비오염)·`_atomic_write_state_json()`(tmp→fsync→os.replace, redact 초크포인트)·`_error_template()` 신규 함수는 스네이크케이스 네이밍·2회 이상 공백 없음·탭 혼용 없음(직접 확인) 등 §네이밍·§들여쓰기 카테고리에서 위반 없음. |
| `.gitignore` (추적 경계 4패턴 — 주석 규약·한시 조치 표기) | 위반 아님(advisory 근거 없음). 기존 `.gitignore`도 패턴 위에 설명 주석을 다는 관례가 있다(예: `.oppl-run/` 위 "전송 산출물 — AGENT.md §결과 파일 규약" 1줄, `*.local.md` 위 2줄 설명). 신규 블록은 그 관례의 연장이며 `docs/CONVENTIONS.md`에 주석 길이·형식을 제한하는 규칙은 없다. 다만 신규 블록(7줄 설명 + 4패턴)은 기존 항목들(패턴당 0~2줄)보다 눈에 띄게 길다 — **강제 규칙 위반은 아니므로 blocking/advisory finding으로 올리지 않고 참고 사항으로만 남긴다.** `@header` 대상이 아니므로(§2.1 적용 범위는 "@header JSON 블록 전체"로 한정) header-standard.md 이력 비기재 원칙의 직접 적용 대상도 아니다. |

---

## 6. 최종 판정

**fail** — `disposition: blocking` finding은 0건이지만, GC-C001이 완전히 닫히지 않고 같은 성격의 위반(GC-C002)이 재발했으므로 이 실행 단위 기준으로는 **재작업 필요**로 판정한다. `code-scan validate` 자체의 `ok`/`INCOMPLETE` 판정(§6 gc-finding-schema)만 놓고 보면 advisory 1건뿐이라 `PASS_WITH_ADVISORIES`이지만, 이번 재검사는 "직전 지적의 완전한 해소"가 목적이므로 잔여 위반 존재를 이유로 **fail**로 보고한다.

- 생성한 보고서 파일: `tasks/123-260912-oppl-태스크-실행로그-표준화/tasks/T02-워킹-스켈레톤-CLI-관통/GC-CONVENTION-2026-09-12T22-53-08-recheck.md`
- 생성한 findings JSON: `tasks/123-260912-oppl-태스크-실행로그-표준화/tasks/T02-워킹-스켈레톤-CLI-관통/gc-findings-convention-2026-09-12T22-53-08-recheck.json`
