# TEST: 태스크 루트 해석 수렴 + 허브 참조 구현 (109)

> 실행자: opal-test-agent | 모드: BE | 실행 시각: 2026-09-07 17:21~17:40 KST
> 브랜치: `feat/OP-TASK-109` | 커밋: `880a486702633910a8f9d71397c93c011f09785b`

## §1 실행 환경·좌표

| 항목 | 값 |
|---|---|
| 허브 `<H>` | `/Volumes/Data/AIStudio/workspace/ai-framework` |
| 워크트리 `<W>` | `/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_109` |
| 브랜치 | `feat/OP-TASK-109` |
| 커밋 | `880a486702633910a8f9d71397c93c011f09785b` — `feat(fw): 허브 루트 해석 규칙 신설 + 경로 조립 수렴 (109)` |
| 인터프리터 | console BE·brain-tool: `~/.opal/.venv/bin/python` / state-tool: 시스템 `python3` / code-scan: `node` |

**[사고 기록]** 실행 중 §2.3.3 [MUST] "매 Bash 호출마다 cd" 위반을 1회 직접 재현했다 — cd 없이 연속 호출한 console BE pytest가 허브 수치(9 failed/348 passed)를 반환해 워크트리 수치로 오독될 뻔했다. 즉시 `cd` 명시 후 재실행해 정정했다(§2 표는 정정된 값). 또한 `code-scan validate` 최초 실행에서 `../../opal/tools/code-scan/code-scan.js`(허브 스크립트)를 실수로 가리켜 `header_source_unset`이 재현됐다 — 워크트리 자신의 스크립트(`opal/tools/code-scan/code-scan.js`, 상대경로 무 `../..`)로 정정 후 정상 판정 진입을 확인했다(§3 TS-023).

## §2 4스위트 실측 (2회 재현)

| 스위트 | 명령 | 실측 (1회) | 실측 (2회) | PM 스냅샷 대비 |
|---|---|---|---|---|
| ① state-tool (워크트리) | `cd <W>/opal/tools/state-tool && python3 -m pytest tests/ -q -rs` | 400 passed / 0 failed / 3 skipped (76.67s) | 400 passed / 0 failed / 3 skipped (78.66s) | 일치 |
| ② console BE (워크트리) | `cd <W> && ~/.opal/.venv/bin/python -m pytest dashboard/backend/tests -q -rs` | 383 passed / 0 failed / 0 skipped (수집 383, 22.62s) | 383 passed / 0 failed / 0 skipped (21.75s, 21.32s 재확인) | 일치 — 목표(0/0) 달성 |
| ③ console BE (허브, 대조) | `cd <H> && ~/.opal/.venv/bin/python -m pytest dashboard/backend/tests -q -rs` | 9 failed / 348 passed / 1 skipped (수집 358) | — (사고 기록에서 우발 재현) | 착수 전 기준선 그대로 (코드는 워크트리 한정) |
| ④ brain-tool (워크트리) | `cd <W>/opal/tools/brain-tool && ~/.opal/.venv/bin/python -m pytest tests/ -q -rs` | 146 passed + 9 subtests / 0 failed / 0 skipped (0.66s) | 146 passed + 9 subtests / 0 failed / 0 skipped (0.71s) | 일치 |
| ⑤ code-scan (워크트리) | `cd <W>/opal/tools/code-scan && node --test tests/*.js` | 368 pass / 6 fail (tests 374) | 재확인(개별 파일 재실행) 동일 | §2.3.4 목록과 정확히 일치 (아래 §6) |
| ⑥ validate 바이트 동일 (허브) | `cd <H> && node opal/tools/code-scan/code-scan.js validate --json` | 27,614 B / exit 2 | 27,614 B / exit 2, `diff` 바이트 동일 확인 | 일치 |
| ⑦ brain-tool 허브 참조 | `cd <W>/opal/tools/brain-tool && python brain_tool.py search test` | `ok: true`, `page`가 `<H>/.opal/brain/pages/...` | — | 정성 일치(허브 `.opal/brain` 참조 확인) |

**판정: §2 전건 재현 일치.** 착수 전 대비 console BE 33→0, state-tool 1→0, skip 3→0 (PM 스냅샷과 동일).

## §3 시나리오 판정 (42건, TS-061 제외)

### F-001 규칙 SSOT

| TS | 결과 | 근거 |
|---|---|---|
| TS-001 | PASS | `opal-harness.md:167` §2.5(4) 신설, 규칙 원문 grep 결과 다른 문서·코드에 원문 중복 0건(포인터만 존재) |
| TS-002 | PASS | 167행 "2. 깊이 무관" — 세그먼트 완전 일치·monorepo/multi-repo(C-4) 명시 |
| TS-003 | PASS | "3. 허브 항등" — 허브 실행 시 입력 그대로 반환·바이트 동일 명시 |
| TS-004 | PASS | 도입부 "(3)은 …정한다. 이 항은 …판정을 정한다 — (3)의 보완" — 모순 없이 참조 방법 규정 |
| TS-005 | PASS | `opal-harness.md:344~345`(v1.19/v1.18), `docs/CONVENTIONS.md:297`(v1.10.0) 모두 `(109)` + KST 타임스탬프 + semver 포함 |

### F-002 3구현 동치

| TS | 결과 | 근거 |
|---|---|---|
| TS-010 | PASS | `hub_root` — `dashboard/backend/paths.py:18`, `opal/tools/brain-tool/brain_tool.py:232` (Python 2), `hubRootFromPath` — `opal/tools/code-scan/code-scan.js:338` (JS 1). 런타임(console BE/brain-tool/code-scan)별 1개씩 |
| TS-011 | PASS | `node --test tests/test-hub-root.js` → `✔ TS-011 … C-1~C-7 전건` |
| TS-012 | PASS | 같은 실행 → `✔ TS-012 … C-3·C-6 바이트 동일` |
| TS-013 | PASS | 3구현 주석·description 확인 — `§2.5 (4)` 포인터만, 정의 원문 재서술 0건 |
| TS-014 | PASS | `state_tool.find_project_root(<W>/opal/tools/brain-tool)` → `<H>` 반환(직접 실행 확인), `paths.hub_root` 동일 입력 결과와 일치 |
| TS-015 | PASS | `paths.py`·`test_paths.py`·`test-hub-root.js` 3파일 `extractHeader()` 직접 호출 → 3파일 모두 `missing: NONE`. validate 재실행 `newly_uncovered: 0` |

### TS-060 골든 표 단일성

| TS | 결과 | 근거 |
|---|---|---|
| TS-060 | PASS | `find . -name hub-root-cases.json` → `opal/core/references/hub-root-cases.json` 1개뿐. 3스위트 소스에서 동일 상대경로(`opal/core/references/hub-root-cases.json`)를 참조함을 grep으로 확인(사본 0건) |

### F-004 테스트 위치 내성

| TS | 결과 | 근거 |
|---|---|---|
| TS-030 | PASS | `state_tool.py` grep `098-260821` → 0건(하드코딩 없음, `_find_repo_task_dir`가 접두사 `prefix`만 받음) |
| TS-031 | PASS | `test_state_tool.py:4613,9021` `confirmed_ratio`==0.75 단정 원문 보존 확인(grep) |
| TS-032 | PASS | ① state-tool 스위트 400 passed에 포함, 098이 `tasks/backup/` 아래인 현 상태에서 그대로 통과 |
| TS-033 | PASS | `_find_repo_task_dir` 구현 확인 — 후보 `!= 1`건이면 `AssertionError`를 직접 raise(skip 경로 없음). "조용한 skip은 검증 무력화" 주석 존재 |
| TS-034 | PASS | `git diff --stat 6dbef10 880a486 -- dashboard/backend/tests/test_config.py dashboard/backend/tests/test_deploy_smoke.py` → 출력 0줄(무변경) |
| TS-035 | PASS | ② console BE `0 skipped`(수집 383, 착수 전 358 대비 증가 +25 — RED-EVIDENCE §2 인용대로 신설 테스트로 전건 설명, 감소 0). 새로 켜진 테스트(`test_adapters.py:88` 등)의 신규 실패 0건(전체 0 failed에 포함). 허브 `0 skipped`는 TS-071(머지 후)로 이연 |

### F-006 이동값 단언 규약 (R-8)

| TS | 결과 | 근거 |
|---|---|---|
| TS-050 | PASS | `test_t103_ts108_dashboard_three_series_is_additive` 등 — 코호트 필터(`_T103_COHORT`) 재계산 경로로 425/23(opd, 보정 후) 및 799/276/75(보정 전, `test_stats.py:807`) 단정 통과(② 스위트 포함) |
| TS-051 | PASS | 값 단정 삭제 0건 — `test_stats.py:807`(`medians == {"opd":799,...}`), `test_routers.py:1951`(보정 전 799) 등 동결값 단정 원문 그대로 잔존 확인 |
| TS-052 | PASS | additive 불변식(`pm+worker+captain==total`)·`quiet_hours` 계약 단정이 무조건(if 분기 없이) 실행되는 형태로 존재(`test_stats.py:867~886`) |
| TS-053 | **PASS — 역검증 완료 + 원복 증명** | `tasks/backup/091-.../state.json`의 마지막 행 `timestamp`를 인위 변경(`2026-08-14 11:46`→`2026-08-20 22:28`) 후 `pytest -k "ts108 or ts137"` 재실행 → **2 failed, 1 passed**(`opd 코호트 중앙값(보정 전) 회귀: assert 1451 == 799` 등 기대한 이유로 실패). 즉시 백업본으로 복원, `diff` 바이트 동일 확인 + `git status --porcelain` → `?? tasks/109-.../` 1건만(원복 완전) + 재실행 `3 passed`로 회귀 없음 재확인 |

### TS-045 경로 이탈 거부 (보안)

| TS | 결과 | 근거 |
|---|---|---|
| TS-045 | PASS | `test_routers.py:2125~` "TS-045 (P0 보안)" 12개 개별 테스트(detail·artifact 조립 지점 각각, `../`·`../../etc`·절대경로·구분자 등 입력별) — `pytest -k "traversal or TS045..."` → `12 passed`. ② 전체 스위트에도 포함(0 failed) |

### L2 프로세스 통합

| TS | 결과 | 근거 |
|---|---|---|
| TS-020 | PASS | grep 결과 cwd 파생 조립 지점 — code-scan `findProjectRoot()`(hubRootFromPath 경유), brain-tool `_hub_cwd()`(4개 호출점: `_load_code_scan_json`·`ingest-scan`·`--brain-path` 기본값 등) 전건이 hub_root/hubRootFromPath 경유. 미경유 지점 0건(단, doctor.py는 문서화된 의도적 예외) |
| TS-021 | PASS | §2 ⑥ — 허브 `validate --json` 2회 실행 바이트 동일(27,614B/exit 2), `diff` 무출력 확인 |
| TS-022 | PASS | `<W>` cwd에서 `node opal/tools/code-scan/code-scan.js validate --json`(워크트리 자신의 스크립트) → `header_source_unset` 없음, `headerSource:"inline"` 반환. code-scan 자체 스위트 `TS-022` 3변형(정탐지·리터럴우선 음성·자기완결 리터럴우선) 전건 `✔` |
| TS-027(a) | PASS | `extractHeader()` 직접 호출 3파일(`api-timeout.test.ts`·`utils.test.ts`·`brain-status.test.ts`) → `missing: NONE` 전건 |
| TS-027(b) | **이연 — CLOSE 게이트** | §2.3.4 5항: 워크트리 `validate`는 허브 트리를 스캔하므로 브랜치 FE 수정이 반영되지 않는다. 판정 기준: 머지 후 허브 `validate --json`의 `uncovered:incomplete` 차단 위반 **집합**에서 이 3파일이 사라지고(건수 아닌 집합 대조) 다른 3건이 새로 들어오지 않아야 한다 |
| TS-028 | PASS(워크트리 측) | 3파일 헤더 직접 확인 — 각 파일 `task` 필드 단일 값(2개 이상 0건), 필드 집합 `module/layer/domain/description/task/scenarios/exports`(7, 선언 8필드 이내), 이력 전용 필드(history/changelog류) 0건. 허브 `header_history` 카운트 불변(2) 확인은 머지 후로 이연 |
| TS-029 | **이연 — CLOSE 게이트** | §2.3.4 근거 동일. 판정 기준: 머지 후 허브 `validate --json` `counts`에서 `uncovered` 등 기존 키 값이 차단 3건 감소분 외에 이동 0(현재 워크트리 관측: `uncovered:247,newly_uncovered:0,header_history:2` — 이 스냅샷을 머지 후와 대조) |
| TS-023 | PASS | 재확인(§1 사고 기록에서 스크립트 경로 정정 후): `<W>` cwd `validate --json` → `header_source_unset` 없음(정상 판정 진입) · `headerSource:"inline"` · `newly_uncovered:0`. exit 코드는 요구하지 않음(§2.3.4 [MUST]) |
| TS-024 | PASS | ④ brain-tool 스위트 146 passed/0 failed(회귀 0) 포함. `--brain-path /tmp/t109_isolated_brain` 명시 호출 시 `brain_not_initialized`(격리된 `/private/tmp/...` 경로 그대로, 허브로 리다이렉트 없음) 직접 확인 |
| TS-025 | PASS | `<W>` cwd `brain_tool.py search test`(기본 `--brain-path`, 명시 없음) → `ok:true`, 결과 `page` 전건이 `<H>/.opal/brain/pages/...` |
| TS-040 | PASS | ② 스위트 포함 — `test_scanner.py` 등 3지점 이름 집합 항등 단정 통과 |
| TS-041 | PASS | ② 스위트 포함 — `completed_tasks>=21`·`total_tasks>=23`·`sum(w.n)==completed_tasks` |
| TS-042 | PASS | ② 스위트 포함 — 코호트 21건 전건 관측 + 중앙값 425/276/75(보정 후) 통과 |
| TS-043 | PASS | ② 스위트 포함 — backup 소재 태스크 detail 200 + legacy 필드 유지, `archive` 컬럼 기존 동작 무변경 |
| TS-044 | PASS | ② 스위트 포함 — `doctor.py` 인자 경로 리터럴 `tasks/` 상태 보고(허브 미치환), doctor.py는 §2.5(4) 명시적 예외로 문서화됨 |
| TS-046 | PASS | ② 스위트 포함 — `test_scanner.py` 합성 픽스처 `task_count`(2/0) 불변 |
| TS-047 | PASS | 함수 1개(`iter_task_dirs`, `scanner.py:50`) — 호출 3지점: `scanner._count_tasks`(126행)·`routers/dashboard._collect_all_tasks`(58행)·`routers/tasks.py`(463행) 전건이 그것만 호출. `scandir`/`iterdir`/`listdir`/`glob`/`rglob`/`walk` 잔존 확인 결과 `tasks.py:148,195`(artifact 파일 나열, task 열거 아님)·`scanner.py:41`(`iter_task_dirs` 자신의 내부 구현, `_sorted_subdirs`)만 존재 — 성질 판정상(task-dir 열거) 잔여 0건 |

### TS-070 4스위트 목표 도달

| TS | 결과 | 근거 |
|---|---|---|
| TS-070 | PASS | §2 재현대로 워크트리 state-tool 0 failed·console BE 0 failed/0 skipped·code-scan 회귀 0(§2.3.4 목록과 일치)·brain-tool 146 유지. 허브 양 스위트 0 failed는 TS-071(머지 후 CLOSE)로 이연 |

### L3 (제외) / 문서

| TS | 결과 | 근거 |
|---|---|---|
| TS-026 | PASS | `opal-harness.md:175` "워크트리에서 실행한 `code-scan`은 …**미머지 변경을 검증하지 않는다**" grep 확인 |
| TS-061 | **L3 — PM 소유, 소유자 확인 대기** | `[SUPERVISOR]` 마커. 본 에이전트 관할 밖. PM이 캡틴에게 직접 요청 필요 |

## §4 코드 품질

| # | 검사 | 결과 | 상세 |
|---|---|---|---|
| 1 | 4스위트 회귀 | PASS | §2 재현 — §2.3 기준선 대비 목표 도달(워크트리), 허브는 이연(TS-071) |
| 2 | 변경이력 행 2문서 | PASS | `opal-harness.md`(v1.18/v1.19), `docs/CONVENTIONS.md`(v1.10.0) 모두 `(109)`·KST·semver 포함 |
| 3 | 신규·수정 파일 `@header` 107 규정 준수 | PASS | `paths.py`·`test_paths.py`·`test-hub-root.js`(신규) `missing:NONE`. FE 3파일(수정) task 단일값·이력 전용 필드 0건·선언 필드 이내 확인(§3 TS-015·TS-028) |

## §5 보안

| # | 검사 | 결과 | 상세 |
|---|---|---|---|
| 1 | `task_id` 경로 이탈 거부 (H-5, P0) | PASS | TS-045 — 12개 개별 조립 지점 테스트 전건 404, 경로 이탈 0건 |
| 2 | 하드코딩 시크릿·홈 절대경로 0건 | PASS | `paths.py` grep(`/Users/`·`/home/`·`password`·`secret`·`api_key`) → 0건(순수 stdlib 문자열 함수). 신규 3파일 전건 재확인 |
| 3 | `.env`·인증 파일 신규 0건, `.gitignore` 변경 0건 | PASS | `git diff --stat main...HEAD` 25파일 목록에 `.env`·인증 파일·`.gitignore` 없음 |

## §6 code-scan 6건 = §2.3.4 목록과 정확히 일치 (목록 밖 실패 0건)

실측 실패 6건(distinct test title): `TS-044(S-14)`(`test-regression.js`, ×2 assertion·1 title) · `077 TS-057`(`test-regression.js`) · `TS-154`(`test-shard-policy.js`) · 메타 3종 — `TS-062(S-16)`(`test-regression.js`) · `TS-080`(`test-shard-policy.js`) · `S-19`(`test-shard.js`). §2.3.4 목록(직접 4행 + 메타 3행, TS-044 ×2 포함)과 **완전 일치**. 목록 밖 실패 없음. 이 6건은 「해소해야 할 잔여」가 아니라 §2.5(4) 5항(워크트리 code-scan이 허브 트리를 스캔)의 구조적 귀결이며, 미머지 파일을 검증된 것으로 위장하는 처방은 적용하지 않았다.

## §7 이연 목록 — CLOSE 게이트에서 판정

| TS | 판정 기준 (머지 후 허브 대비) |
|---|---|
| TS-071 | 허브 state-tool 0 failed(현재 1) · 허브 console BE 0 failed/0 skipped/수집 감소 0(현재 9 failed/1 skipped/358) · 허브 `validate --json` exit 0(현재 exit 2, 3 violation) |
| TS-027(b) | 허브 `validate --json` `uncovered:incomplete` 차단 위반 **집합**에서 FE 3파일이 사라짐(집합 대조, 건수 아님) |
| TS-028 (허브 카운트) | 허브 `header_history` 카운트 불변(2) — 현재 워크트리 스캔값 2를 기준으로 대조 |
| TS-029 | 허브 `validate --json` `counts` 기존 키(`orphan`·`uncovered`·`conflict`·`draft`·`exports_not_found`·`worker_scope_violation`·`manifest_oversize`·`pre_existing`) 값이 차단 3건 감소 외 이동 0 |
| TS-035 (허브 skip) | 허브 console BE `0 skipped`(현재 허브 1건 skip 중 — `test_adapters.py:88`) |

## §8 최종 판정

**PASS.**

- PASS 40건 / L3(PM 소유, 미판정) 1건(TS-061) / 이연 5건(CLOSE 게이트: TS-027(b)·TS-028 허브카운트·TS-029·TS-035 허브분·TS-071) — TS-070·TS-050~053 등은 워크트리 측 목표를 이미 충족했으므로 PASS로 계상, 이연 목록은 §7 별도 관리
- FAIL 0건, 목록 밖 code-scan 실패 0건
- 워크트리 4스위트 전건 §2.3 목표치 도달(state-tool 0 failed/3 skip · console BE 0 failed/0 skip · code-scan 6건 구조적 잔존만(§6) · brain-tool 146 유지)
- TS-053 역검증 통과 + 원복 완전 증명(diff 바이트 동일·git status 정상)
- 보안 P0(TS-045) PASS, 신규 파일 시크릿·홈경로 0건
- 잔존물(`.bak`/`.orig`/`.rej`) 0건, `git status` 예상 밖 변경 0건(양쪽 모두 정상 — 허브는 자기 태스크 폴더 1건 untracked만)
- 허브 측 최종 판정(4항목)은 소유자 결정에 따라 TS-071에서 머지 후 push 전 판정 예정 — 미달이다.


---

## §8 TS-061 (L3 [SUPERVISOR]) — FAIL → 처방 반영 → 재판정 대기

### 8.1 1차 판정: **FAIL**

소유자(캡틴)가 워크트리에서 `code-scan validate --json`을 실행하고 **출력만 보고** 판단했다. 결과:

출력에 이 세 줄이 실려 있었다.
```
{"sub":"incomplete","file":"dashboard/frontend/src/lib/api-timeout.test.ts","detail":"exports"}
{"sub":"incomplete","file":"dashboard/frontend/src/lib/utils.test.ts","detail":"exports"}
{"sub":"incomplete","file":"dashboard/frontend/src/pages/brain/brain-status.test.ts","detail":"exports"}
```

**이 태스크가 Step 12에서 이미 고친 3파일이다.** 실측 대조:

| | `exports` 보유 |
|---|---|
| 워크트리 파일 | **1건** (수정됨) |
| 허브 파일 (`main`, 미머지) | **0건** |

즉 출력은 **허브 파일을 읽고** 「미비」라고 보고했다. 그리고 출력 어디에도 **스캔 루트가 없었다** — 최상위 키는 `ok`·`command`·`mode`·`coverage`·`counts`·`violations`·`skipped`·`headerSource` 8개뿐이고, 경로·루트 관련 키는 0건이었다. 허브 직접 실행과 `coverage.total`이 **양쪽 354로 동일**해 같은 트리를 봤음이 확인된다.

**H-9가 실현된 상태였다.** 자연스러운 오독은 「내 수정이 반영되지 않았다」이고, 반대로 통과가 나오면 「내 변경이 검증됐다」로 읽힌다.

**이 태스크 안에서 실제로 두 번 발생했다**:
1. Step 12 워커가 「내 FE 수정이 반영되지 않았다」 상태에 빠져 허브 파일을 임시로 고쳐 확인하려다 권한 차단에 막혔다(우회하지 않고 중단).
2. TEST 단계 워커가 `../../opal/tools/code-scan/code-scan.js`로 **허브의 옛 스크립트**를 가리켜 `header_source_unset`을 재현했다(자체 정정, §1 사고 기록).

**TS-026(문서에 한계가 명시되는가)은 PASS다** — `opal-harness.md` §2.5 (4) 5항에 명문화돼 있다. **문서에 적혀 있어도 출력을 보는 순간 오해한다는 것이 이 시나리오의 발견이다.** TS-061을 M3(사용자 협업)로 남긴 이유가 정확히 이것이며, 시나리오에 미리 기재한 처방대로 **고칠 곳은 문서가 아니라 출력**이다.

### 8.2 처방 — 소유자 결정: stderr 전용 경고

3안 중 캡틴이 **「stderr로만 경고 — 바이트 동일 보증 유지」**를 선택했다. `stdout`(JSON)을 건드리면 **TS-021(허브 출력 바이트 동일, 27,614 B)**이 깨진다 — 이 태스크의 P0 단언이다.

**발화 조건 (둘을 모두 만족할 때만)**:
1. `hubRootFromPath(process.cwd()) !== process.cwd()` — cwd가 워크트리 안이다
2. 해석된 스캔 루트 === `hubRootFromPath(process.cwd())` — 스캔 루트가 **허브로 착지**했다

| 상황 | 조건1 | 조건2 | 발화 |
|---|---|---|---|
| 워크트리 루트 | ○ | ○ | **경고** |
| 픽스처(자기 `.opal/` 보유) | ○ | ✗ | 침묵 |
| 허브 | ✗ | — | 침묵 |

조건2를 빼면 `tests/fixtures/<프로젝트>`처럼 **자기완결 프로젝트가 워크트리 하위에 있을 때 오발화**한다(§2.5 (4) 부칙 「탐색 우선순위」).

경고 원문 (399 B, 1줄):
```
code-scan: [worktree] cwd는 워크트리 안이지만 스캔 루트는 허브 <허브 절대경로> 입니다 —
허브 작업트리의 파일만 읽었고 미머지 브랜치의 변경은 반영도 검증도 되지 않았으므로,
위반 보고도 통과도 이 워크트리 수정에 대한 판정이 아닙니다.
규칙: opal/core/references/opal-harness.md §2.5 (4)
```

**양방향 오해를 한 절에 병렬로 묶은 것이 요점이다** — 「위반 보고도 통과도 … 판정이 아니다」. 한쪽만 쓰면 반대쪽이 열린다.

### 8.3 처방이 피한 함정 2건 — 실재했다

| 함정 | 내용 |
|---|---|
| **배치 지점** | `findProjectRoot()` 안에 넣으면 `code-map-hook.js:108`이 그 함수를 직접 호출하므로 **편집마다 경고가 새어** TS-076(`test-hook.js:299`)·S-6(a)/(c)(`test-shard.js:739,761`)의 「hook stderr **0바이트**」 `strictEqual` 단정 3건이 즉시 깨진다. → `main()` 배치로 hook 경로 완전 침묵 |
| **문자열 충돌** | `test-header-source.js:397,421`이 stderr 줄을 `l.includes('headerSource')`로 필터해 **정확히 1줄**을 단정한다. 경고 문면에 그 문자열이 들어가면 깨진다. → 문면에서 `headerSource`를 **의도적으로 배제**(「기록 소스」 같은 우회 표현도 쓰지 않음) |

### 8.4 처방 검증 (PM 독립 실측)

| # | 항목 | 결과 |
|---|---|---|
| ① | 허브 stdout 바이트 동일 | **27,614 B `cmp` IDENTICAL**, stderr 양쪽 **0 B**(세그먼트 부재로 미발화) |
| ② | 워크트리 발화 | stdout **27,614 B 유지** / stderr **399 B, 1줄** |
| ③ | 픽스처 오발화 | `grep -c worktree` = **0** |
| ④ | 실행당 1회 | 354파일 스캔에 stderr **1줄** (`noticeOnce` 기존 패턴 재사용, 신규 메커니즘 0건) |
| ⑤ | code-scan 회귀 | **368 pass / 6 fail** — 기준선 유지, 신규 0 |
| ⑥ | stderr 단정 테스트 | `test-hook.js` **18/0** · `test-header-source.js` **12/0** · `test-shard.js` 56/1(1건은 S-19 집계기, 구조적 잔존) |

### 8.5 재판정 — 대기

**처방을 넣었으므로 소유자가 같은 판단을 다시 해야 한다.** 「오해를 막는가」는 문자열 단언으로 판정 불가이며, 처방을 작성한 쪽이 스스로 판정하면 이 시나리오의 존재 이유가 사라진다.

재판정 명령 (허브 셸 기준):
```
cd .opal-worktrees/task_109 && node opal/tools/code-scan/code-scan.js validate >/dev/null
```

**판정 기준**: 경고를 보고도 「내 수정이 반영되지 않았다」 또는 「통과했으니 내 변경이 검증됐다」로 읽히면 **여전히 FAIL**이다.

**미결 판단 1건 (소유자 확인 요청)**: 문면에 「머지 후 허브에서 재실행하라」는 **행동 지시를 넣지 않았다.** 「규칙 원문 재서술 금지」(TS-001·TS-013)를 좁게 해석한 결과다. 처방까지 실어야 한다고 보면 한 절 추가는 사소하다.

### 8.6 재판정: **PASS** (소유자 확인, 2026-09-07)

소유자(캡틴)가 워크트리에서 재실행하고 경고를 확인했다.

```
$ node opal/tools/code-scan/code-scan.js validate >/dev/null
code-scan: [worktree] cwd는 워크트리 안이지만 스캔 루트는 허브 /Volumes/Data/AIStudio/workspace/ai-framework 입니다
— 허브 작업트리의 파일만 읽었고 미머지 브랜치의 변경은 반영도 검증도 되지 않았으므로,
위반 보고도 통과도 이 워크트리 수정에 대한 판정이 아닙니다.
규칙: opal/core/references/opal-harness.md §2.5 (4)
```

**판정: PASS** — 출력이 스캔 루트를 스스로 드러내며, 「내 수정이 반영되지 않았다」·「통과했으니 검증됐다」 양방향 오해가 닫혔다.

**미결 판단 처리**: 「머지 후 허브에서 재실행하라」 행동 지시는 **추가하지 않는다**(소유자 확인). 근거 — 머지 전에는 재실행해도 답이 같아 지시가 헛수고를 유발하고, 「이 판정은 네 변경에 대한 것이 아니다」까지 전달되면 다음 행동은 상황이 정한다. 경고는 **사실 진술에 한정**하고 처방은 규칙 포인터가 담당한다.

### 8.7 이 시나리오가 남긴 것

TS-061은 **PM 보강으로 신설한 유일한 L3 시나리오**이며, 43건 중 **실제 결함을 잡은 유일한 시나리오**다. 나머지 42건은 전부 PASS 또는 이연이었다.

| | 무엇을 보았나 | 결과 |
|---|---|---|
| TS-026 (M1, 자동) | 문서에 한계가 명시되는가 | PASS — §2.5 (4) 5항에 있었다 |
| **TS-061 (M3, 사람)** | **그 한계가 실제로 오해를 막는가** | **FAIL** — 문서에 있어도 출력을 보면 오해했다 |

**문자열 단언으로 판정 가능한 것과 불가능한 것의 경계가 여기서 드러났다.** 「문서에 적혔는가」는 grep으로 되지만 「사람이 오해하는가」는 안 된다. 자동 검증만으로 구성했다면 TS-026 PASS로 덮이고 결함은 남았을 것이다.

그리고 그 결함은 **가설이 아니라 실제로 두 번 발생했다** — Step 12 워커(허브 파일을 임시 수정하려다 권한 차단)와 TEST 워커(허브 옛 스크립트 오지정). 같은 세션 안에서다.
