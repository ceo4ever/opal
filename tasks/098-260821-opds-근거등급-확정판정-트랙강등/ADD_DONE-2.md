# ADD_DONE-2: 배포 경로 루트 파생 결함 수정

> `DONE.md`는 원본 완료 기록으로 보존하며 수정하지 않는다(`harness/additional-work.md`).
> 파일명이 `ADD_DONE-1`이 아닌 이유: ADD-1(§9 E1 관측 스코프 병기)은 TEST 미착수 **인플라이트 EXECUTE 확장**이어서 CLOSE 재진입이 아니었고 `DONE.md` §2에 기록됐다. 별도 ADD_DONE 문서를 만들지 않았으므로 번호를 ADD-2와 일치시켰다.

| 필드 | 내용 |
|------|------|
| 추가작업 번호 | **ADD-2** (`state.json` row 13 / key `close.add2_root_derivation`) |
| 시작 | 2026-08-21 22:58 |
| 완료 | 2026-08-21 23:19 |
| 진입 경로 | CLOSE 재진입 — `add-row` 시 `current_status`가 `done` → `additional_work` 자동 전환 |
| 승인 | 캡틴 "승인" (2026-08-21 22:58) |

## 사유

install 재배포 직후 S-29(배포본 정합) 검증 중 **P0 결함**을 발견했다. 배포가 성공했는데도 `verify --evidence-check`가 반대 방향으로 동작했다.

`state_tool.py:2400` `_resolve_citation_exists()`가 프로젝트 루트를 **스크립트 자기 위치**에서 파생했다:

```
root = find_project_root(str(pathlib.Path(__file__).resolve()))
```

`find_project_root`의 자기 계약은 docstring에 "**task_path**의 조상 중 `.opal/MEMORY.json`을 파일로 가진 첫 디렉토리"로 명시돼 있고, 다른 모든 호출자(`link_memory_history` 등)는 태스크 경로를 넘긴다. 이 호출만 `__file__`을 넘겼다.

배포본 `~/.opal/tools/state-tool/`에는 `.opal/MEMORY.json` 조상이 없어 `root = None`이 되고, 조기 반환 `False`로 **정규 인용이 전건 `citation_path_not_found`로 오강등**됐다. 하네스 §3·`docs/CONVENTIONS.md` §State 관리가 규정하는 실사용 호출 경로는 `~/.opal/tools/state-tool/run.sh` **단일**이므로, R-4 AC(b)가 실사용 환경에서만 반대로 동작하는 상태였다.

발견 당시 실측 (동일 태스크 경로·동일 cwd):

| 실행 경로 | `confirmed_ratio` | 항목 판정 |
|---|---|---|
| 프로젝트 소스 | 0.75 | 범위·제약·완료기준 확정 / 목표만 `grade_unknown` |
| 배포본 | **0.0** | 전건 `citation_path_not_found` |

**검증 공백의 원인**: S-31(①축 목표달성 in-task 자동)과 신규 테스트 16건이 전부 프로젝트 소스·모듈 경로로만 실행됐다. 목표달성 축이 실사용 경로를 한 번도 통과하지 않았고, 배포본 stale이 실결함을 가리고 있었다.

## 변경 내용

RED-first 트랙으로 처리했다(코드 로직 변경 + 동작검증 필수 → L2 우회 부적격).

**RED** — `TestT098Add2RootDerivation` 신설, 3축. 판정 층을 내부 시그니처가 아니라 **공개 CLI 출력**(`confirmed_ratio`·항목별 `verdict`/`reasons`)으로 고정했다 — 결함이 드러난 층이 실사용 CLI이고, `root` 주입 방식은 GREEN 구현 결정이라 테스트가 선점하면 구현을 과잉 구속한다. 입력은 합성 픽스처 금지·저장소 실파일(본 태스크 `TASK.md`) 강제.

| 축 | 내용 | RED |
|----|------|-----|
| ① | 스크립트 위치 독립성 — 프로젝트 밖 사본 실행이 소스 실행과 동일 판정 | FAIL (의도) |
| ② | 오강등 부재 — 실존 파일·유효 줄번호 인용이 `citation_path_not_found`를 받지 않음 | FAIL (의도) |
| ③ | 회귀 가드 — 프로젝트 소스 실행 판정 불변 | PASS (가드성) |

**GREEN** — `_check_evidence_gate`가 루트를 **1회** 계산해 아래로 전달한다.

```
root = (find_project_root(task_md_path)
        or find_project_root(str(pathlib.Path(__file__).resolve())))
```

세 함수에 트레일링 옵셔널 `root=None`을 추가해 연쇄로 전달했다 — `_evaluate_evidence_item` → `_grade_citation` → `_resolve_citation_exists`. `find_project_root`를 재사용했고 신규 탐색 함수는 0건이다.

- **`__file__` 폴백을 남긴 이유**: `TestT098EvidenceCheck`의 합성 태스크 경로(`tempfile.mkdtemp()`)는 실 프로젝트 조상이 없어 1순위 파생이 실패한다. 테스트는 불변이므로 기존 동작을 보존해야 했다. 실사용 경로에서는 태스크 경로가 항상 프로젝트 안에 있어 1순위가 성립하므로 결함이 재발하지 않는다.
- **`root=None` fail-safe 유지** — 오작동 방향을 "미확정 강등"으로 고정하는 설계는 의도된 것이다(`PLAN.md` §3.3.2).
- **보안 가드 `_is_safe_artifact_token()` 무접촉** — 절대경로·`..` 이탈 차단 유지.

## 변경 파일

| 파일 | 변경 |
|------|------|
| `opal/tools/state-tool/state_tool.py` | 2884 → **2897** — 함수 4개 시그니처·본문 + `@header.description` 098 ADD-2 항목 |
| `opal/tools/state-tool/tests/test_state_tool.py` | 8817 → **8987** — `TestT098Add2RootDerivation` 3건 + `@header` 갱신 |
| `RED-EVIDENCE.md` | ADD-2 절 추가 (기존 내용 보존) |

`README.md` 무변경 — 에러 코드·공개 동작 변경이 없다.

## 검증 결과

| 항목 | 결과 |
|------|------|
| RED → GREEN | `TestT098Add2RootDerivation` **3/3 PASS** (RED 시 2 failed, 1 passed) |
| 기존 계약 무회귀 | `TestT098EvidenceCheck` 13 + `TestErrorCodesCompleteness` 3 = **16/16 PASS** (무수정) |
| 회귀 — 단일 파일 스코프 | `1 failed, 340 passed, 3 skipped, 83 subtests` (RED 직전 `3 failed` → 2건 회복) |
| 회귀 — 디렉토리 스코프 | `1 failed, 357 passed, 3 skipped, 83 subtests` |
| 실질 회귀 | **0건** (잔존 1 FAIL은 §선재 결함) |
| 배포 등가 조건 | **PM 독립 재현** — 프로젝트 밖 임시 사본 실행이 소스 실행과 `confirmed_ratio 0.75` + 항목별 판정 전건 동일 |
| 테스트 불변성 | GREEN 세션에서 `test_state_tool.py` Edit/Write **0회** (8987줄 불변) |
| `--red-check` 게이트 | `mock_in_scenario: pass` / `evidence_missing: pass` / `red_evidence_missing: pass` |

**[MUST] 위 회귀 2행은 같은 시점의 서로 다른 스코프다** — 디렉토리 스코프에는 `test_todo_mirror_hook.py` 17 passed가 더해진다. (ADD-1로 신설한 `citation-rules.md` §9 (a) E1 규칙의 자기적용)

**검증 2원화**: RED 작성(`opal-test-agent`) ≠ GREEN 구현(`opal-be-agent`) ≠ 최종 판정(PM 직접 재실행). 작성자 세션에서 `state_tool.py` 2884줄 불변, 구현자 세션에서 테스트 파일 8987줄 불변으로 각각 실측 확인했다.

## 선재 결함 (미접촉 — ADD-2와 무관)

`TestR11Invariants::test_r11_invariants_S40` 서브테스트 `error_codes_key_set_untouched`가 `git show HEAD:./state_tool.py`의 `ERROR_CODES` 키 집합을 워킹트리와 대조한다(`test_state_tool.py:8795-8809`). 본 태스크가 `evidence_check_flag_conflict`를 추가했으므로 커밋 전까지 구조적으로 FAIL한다. 상세·근거는 `DONE.md` §7 · `TEST-SCENARIO.md` §7.

## 배포 검증 (2026-08-21 23:2x — 캡틴 재배포 후 PM 실측)

캡틴이 `bash scripts/install-mac.sh`를 재실행했고, **실사용 경로**(`~/.opal/tools/state-tool/run.sh`)로 직접 판정해 결함 해소를 확인했다.

| 시점 | 실행 경로 | `confirmed_ratio` | 항목 판정 |
|------|----------|-------------------|----------|
| 1차 배포 직후 (결함) | 배포본 | **0.0** | 전건 `citation_path_not_found` |
| ADD-2 수정 + 2차 배포 후 | 배포본 | **0.75** | 목표만 `grade_unknown` / 범위·제약·완료기준 확정 |
| (대조) | 프로젝트 소스 | 0.75 | 동일 |

배포본 코드 정합도 확인했다 — `~/.opal/tools/state-tool/state_tool.py:2509`에 `find_project_root(task_md_path)` 존재, `root=None` 트레일링 인자 4곳.

**S-29 판정 갱신**: `해당 없음 (CLOSE 절차 이월)` → **PASS**. `TEST-SCENARIO.md` S-29 결과·상세에 2회 배포 대조 실측을 기입했다. 이 시나리오가 in-project 검증만으로는 원리적으로 잡히지 않는 결함을 실제로 검출했다.

**`DONE.md` 미수정**: `harness/additional-work.md`가 "DONE.md는 원본 완료 기록으로 보존하고 수정하지 않는다"를 규정하므로, `DONE.md` §7의 "install 재배포 미수행" 기재는 그대로 두고 본 문서가 그 상태를 갱신한다.

## 미수행 / 후속

- **커밋** — 커밋 금지 규칙에 따라 워킹트리 유지.
- **후속 후보 추가 1건** — 신규 도구 기능의 완료 기준에 "배포 경로 등가 실행"을 표준 항목으로 넣는 것. 이번 결함은 in-project 검증만으로는 원리적으로 잡히지 않았다.
- **후속 후보 추가 1건** — `brain-tool` `speculative_content`가 도메인 용어 '미확정'을 미실체 마커로 오탐한다. 근거 등급을 다루는 모든 후속 brain 페이지가 걸린다(034 `MagicMock` 산문 오탐 선례와 동일 유형).
