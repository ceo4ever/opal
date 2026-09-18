# ANALYSIS: 태스크 루트 해석 수렴 (구 `OPAL_TASKS_ROOT` 계약안 — 철회)

> 작성일: 2026-09-06 (2026-09-07 정정)
> 입력: TASK.md (개정본)
> 출력: ANALYSIS.md

## 정정 사유 (2026-09-07)

TASK.md 개정으로 전제 3건이 바뀌었다: ① `OPAL_TASKS_ROOT` 환경변수 신설 철회(허브 경로는 `.opal-worktrees` 세그먼트로 유도 가능, 실측 확인) ② `code-scan.json` 워크트리 복사 철회(스코프가 상대경로라 복사 시 워크트리를 스캔하게 됨) ③ 참조 대상이 `tasks/`뿐 아니라 `.opal/` 전체(code-scan.json 포함)임이 명시. 이에 따라 아래 표의 관련 행을 정정하고, §7에 Q9~Q12를 추가하며, §7 Q1·Q3·Q4·Q5·Q7·Q8과 §1.1의 실측 결론은 그대로 유지한다(전제 변경과 무관). §7 Q2만 「환경변수 적용범위」에서 「세그먼트 해석 함수가 다중 프로젝트 스캔 루프에서 어떻게 동작해야 하는가」로 재작성했다.

## 확정 입력 판정 (TASK.md `[결정]`·`[사실]` 전건 재판정 — 개정본 기준)

| 항목 | 판정 | 근거 |
|------|------|------|
| [결정] 범위는 (A)+(B) 둘 다 | 유효 | TASK.md §확정된 설계 방향 1행 — 코드 변경 범위 판단에 이견 없음 |
| [결정] 허브 루트 해석 규칙(`.opal-worktrees` 세그먼트 → 부모가 허브, 없으면 자기 루트) | **유효, 실측 확인** | `.opal-worktrees/.meta/task_109.json`: `worktree_root: ".../ai-framework/.opal-worktrees/task_109"`, `entries[].repo: ".../ai-framework"` — 세그먼트 부모가 허브와 일치. `realpath .opal-worktrees/task_109/opal/tools` = 그대로(심링크 아님, 문자열 세그먼트 검사로 충분) |
| [결정] `OPAL_TASKS_ROOT` 환경변수 신설 **철회** | **철회 타당함, 확인** | 허브 경로가 이미 `.opal-worktrees/.meta/task_{NNN}.json`의 `entries[].repo`(실측 위와 동일)와 세그먼트 규약 양쪽에서 유도되므로 신설할 정보가 없다. 8곳 중 어디도 이 환경변수를 참조하지 않는다(`grep -r OPAL_TASKS_ROOT opal/ dashboard/` 0건, 본 세션 재확인) |
| [결정] `.opal/code-scan.json` 워크트리 복사 **철회** | **철회 타당함, 실측 확인** | `opal/tools/code-scan/code-scan.js:513-515`: 스코프 경로를 `path.resolve(ctx.projectRoot, norm)`으로 조립 — 전부 `projectRoot` 상대. `.opal/code-scan.json`의 scope는 예: `"framework": "opal/"`(상대). 허브 설정을 워크트리 루트에 복사해 적용하면 스코프가 워크트리의 `opal/`을 가리켜 워크트리를 스캔하게 된다 — 복사가 오히려 드리프트를 만든다 |
| [결정] 심볼릭 링크 미채택 | 유효 | TASK.md `[사실]` 1,022건 `D` 실험 인용 그대로 승계, 재실측 불필요(비파괴 실험) |
| [결정] 런타임별 2구현(공용 모듈 없음) | 유효, 재확인 | `dashboard/backend/adapters/state_adapter.py:19-31` 서브프로세스 계약 확인(§1.2), `opal/tools/*`에 `__init__.py` 없음(재확인 0건) |
| [사실] 경로 조립 지점 8곳·테스트 하드코딩 4곳 | 유효(대조 확인) | `dashboard/backend/routers/tasks.py:457,520,654`·`scanner.py:29`·`dashboard.py:50`·`doctor.py:85`·`opal/tools/memory-tool/memory_tool.py:675`·`opal/tools/brain-tool/brain_tool.py:1298` (8곳 실측 재확인) / `opal/tools/state-tool/tests/test_state_tool.py:4569`·`dashboard/backend/tests/test_routers.py:1010-1011`·`test_stats.py:59`·`test_adapters.py:85` (4곳) — **단, 8곳은 `tasks/`·`.opal/` 조립만 포함하고 `code-scan.js`의 `findProjectRoot()`(§Q9~Q10)는 별도 축(허브 판정 자체)이라 이 8곳 목록과 레이어가 다르다** |
| [사실] 심볼릭 링크 시 1,022건 `D` | 유효(대조 확인) | TASK.md 원 실험 기록 그대로 인용 — 본 세션 재실측 대상 아님(비파괴 실험 재현 생략) |
| [사실] 워크트리 sparse 패턴은 `cursor-rules dashboard docs memory opal scripts skills`(7항목, `.opal` 없음) | 유효(대조 확인) | `.opal/worktree.json:10-18` + 실측 동일. TASK.md 개정본이 이미 정정 반영(§배경분석(5)) |
| [사실] 정규 워크트리(task_109)에 `.opal/` 부재, `code-scan validate` → `header_source_unset` | **유효, 재확인 — 파급 확대** | `ls -la .opal-worktrees/task_109` 재확인 결과 `.opal` 없음(본 세션). 추가로 `code-scan.js:332-341` `findProjectRoot()`가 `process.cwd()`에서 `.git`(파일이든 디렉터리든 무관) 발견 시 **즉시 그 경로를 반환**한다 — 워크트리 루트에는 `.git`이 **파일**로 존재하므로(`ls -la` 확인: `-rw-r--r-- .git`) 워크트리 cwd에서 실행하면 부모로 더 올라가지 않고 워크트리 자신을 projectRoot로 확정한다. 즉 현재 `findProjectRoot()`에는 `.opal-worktrees` 세그먼트 검사 자체가 없다 — 이것이 `header_source_unset`의 코드 레벨 원인이다(Q9·Q10 상세) |
| [사실] task_107의 `.opal` 존재는 워커의 무단 `sparse-checkout add` 흔적 | 유효, 판정 근거 승계 | TASK.md가 생성 11:52 vs sparse 수정 13:52 시각차로 이미 실측 — 본 세션 재검증 대상 아님(과거 시각 기록, 재현 불가) |

> 사실오류 보고 없음 — 1차 산출물의 지적(구 `test_stats.py:59` 사실오류 판정 등)은 TASK.md가 이미 반영해 유지했다.

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | 워크스페이스 축 | `opal/core/references/opal-harness.md:142-172` §2.5 | 워크트리 계약 원문 — R-2 개정 대상, `.opal` 미분기 서술 대조 |
| D-2 | 설계 | worktree.json 선언 | `.opal/worktree.json:1-31` | sparse 패턴 원천(7항목, `.opal` 미포함) — 실측 정정 근거 |
| D-3 | 소스 | worktree-tool 본체 | `opal/tools/worktree-tool/worktree_tool.py:720-841` | `cmd_create` 전체 흐름 + 응답 조립(R-4 대상) |
| D-4 | 소스 | worktree-tool 스키마 | `opal/tools/worktree-tool/schema/worktree.schema.json:1-8` | `.opal/worktree.json` 검증용 스키마이며 CLI 응답(JSON) 스키마가 아님 — 응답 필드 추가가 스키마 위반이 아님을 확인 |
| D-5 | brain | 픽스처 구조적 한계 | `.opal/brain/pages/concept/worktree-tasks-fixture-structural-limit.md` | (B)의 성질 진단 — 워크트리 기준선 대비 증분 판정 근거(E5, 단독 인용 금지 원칙에 따라 D-6과 동반) |
| D-6 | 산출물 | 태스크 107 AGENTIC-LOG | `tasks/107-260906-opd-헤더필드-작성기준-이력분리/DONE.md` | D-5의 1차 근거(E1~E4) — brain 페이지 sources 필드 지시 |
| D-7 | 컨벤션 | 배포 경계·Guards | `docs/CONVENTIONS.md` | `~/.opal/` 직접 편집 금지, Guards 준수 |

> **선조회 3단**: brain(D-5)·과거 산출물(D-6, 태스크 107 DONE.md/AGENTIC-LOG)은 TASK.md가 이미 인용해 재조회 없이 승계했다. code-scan 레지스트리 선조회는 생략했다 — 본 태스크는 `code-scan` 규칙 위반 탐지가 아니라 런타임 경로 해석 실측이 핵심이라 규칙 레지스트리 매칭 실익이 낮다(스킵 사실 명시).

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

| 영역 | 경로 | 역할 | 변경 유형 | 근거(줄번호) |
|------|------|------|------|-------------|
| BE | `dashboard/backend/routers/tasks.py` | 태스크 목록/상세 API — `tasks_dir`/`task_dir` 3곳 조립 | 수정 | `tasks.py:457,520,654` |
| BE | `dashboard/backend/scanner.py` | 프로젝트 스캔 — `_count_tasks` 1-depth 카운트 | 수정 | `scanner.py:29` |
| BE | `dashboard/backend/routers/dashboard.py` | 대시보드 집계 — `_collect_all_tasks` 1-depth 순회 | 수정 | `dashboard.py:50` |
| BE | `dashboard/backend/routers/doctor.py` | 환경 진단 — 프로젝트 섹션 `tasks/` 존재·개수 | 판정 보류(Q6, 수정 여부는 PLAN 결정) | `doctor.py:85` |
| 환경 | `opal/tools/memory-tool/memory_tool.py` | `_resolve_last_task_number` — `project_root/tasks` 조립 | 수정 | `memory_tool.py:675,739` |
| 환경 | `opal/tools/brain-tool/brain_tool.py` | tasks 스캔 — `cwd/tasks` 조립 | 수정 | `brain_tool.py:1298,869,1252` |
| 환경 | `opal/tools/worktree-tool/worktree_tool.py` | `cmd_create` 응답 조립 지점 | 수정(필드 추가) | `worktree_tool.py:828-841` |
| 환경 | `opal/tools/code-scan/code-scan.js` | `findProjectRoot()` — cwd에서 `.git`/`.opal`/`CLAUDE.md` 상향 탐색, `.opal`을 만나지 않고도 `.git`(워크트리에선 파일)에서 즉시 확정 / `loadConfig(projectRoot)` — `{projectRoot}/.opal/code-scan.json` 로드 | 수정(허브 판정 로직 추가 대상 — R-1 세그먼트 규칙 미반영) | `code-scan.js:331-341`(`findProjectRoot`)·`377-378`(`loadConfig`) |
| 환경 | `opal/tools/code-scan/code-scan.js` | `discoverFiles`/`getSearchPaths`/`buildCtx` — 스캔 대상 루트를 `projectRoot`(설정 로드와 동일 변수)로 조립 | 판정 보류(Q10, 설정 경로와 스캔 루트 분리 여부는 PLAN 결정) | `code-scan.js:962-991,1277-1280` |
| 환경 | `opal/tools/brain-tool/brain_tool.py` | `_load_code_scan_json` — `cwd / ".opal" / "code-scan.json"` 조립 | 수정 | `brain_tool.py:867-868` |
| 환경 | `dashboard/backend/tests/test_routers.py` | `_T103_TASK_089`·`_T103_TASK_091` 실 폴더명 하드코딩 + 실 `state.json` 직독 | 수정 | `test_routers.py:1010-1011,1063-1064` |
| 환경 | `opal/tools/state-tool/tests/test_state_tool.py` | S-31 — 098 TASK.md 실파일 직접 참조 | 판정 보류(Q3, 대체 불가 소지) | `test_state_tool.py:4559-4585` |
| 환경 | `dashboard/backend/tests/test_adapters.py` | 021 태스크 실 폴더 참조 — 이미 `pytest.skip` 가드 보유 | 판정: 이미 견고, 변경 실익 낮음 | `test_adapters.py:82-91` |
| 환경 | `dashboard/backend/tests/test_stats.py` | `FX_086_ID` 등 — **사실오류**, 실 폴더 미참조(동결 fixture만 사용) | 변경 불요 | `test_stats.py:56-98` |
| 문서 | `opal/core/references/opal-harness.md` | §2.5 워크스페이스 축 — R-2 개정 대상 | 수정 | `opal-harness.md:142-172` |
| 문서 | `opal/core/references/harness/task-process.md` | 4.5 worktree 생성 절차 — R-2·R-4 | 수정 | (§4.5, 절 단위 인용) |
| 문서 | `opal/core/references/pm/dispatch-process.md` | §작업 경로 블록 — R-4 주입 지점 | 수정 | (§작업 경로 블록, 절 단위 인용) |

### 1.2 아키텍처 패턴

- `dashboard/backend`는 `opal/tools/*`를 **import하지 않는다**. `opal/tools/*`는 `__init__.py`가 없는 단일 스크립트 + `run.sh` 래퍼 구조이며(`find opal/tools -maxdepth 2 -iname "__init__.py"` 결과 0건), console BE는 `dashboard/backend/adapters/*.py`를 통해 **서브프로세스로만** 호출한다(`state_adapter.py:19-20`: "state-tool show --format json read-only 호출 래퍼" — `run.sh` 절대경로 하드코드).
- 결과적으로 두 런타임(Python 웹앱 `dashboard/backend` vs Python CLI 도구군 `opal/tools/*`)은 **프로세스 경계로 격리**되어 있고, import 계약이 아니라 서브프로세스+JSON 계약으로 연결된다.

### 1.3 의존성 맵

- `dashboard/backend/routers/{tasks,dashboard}.py`, `scanner.py`, `doctor.py` — 전부 `project_path`(또는 `p`)를 **함수 인자로 전달받는다**. 이 값의 원 출처는 `dashboard/backend/config.py`의 `scan_roots`(다중 프로젝트 스캔) 또는 `_find_project_path(project)`(단일 프로젝트 조회) — cwd/`__file__` 파생이 아니다.
- `opal/tools/memory-tool/memory_tool.py:739`: `project_root = md_path.parent.parent` — **MEMORY.md 파일 자신의 위치**로부터 역산한다. 인자 전달도 cwd도 아닌 제3의 파생 방식.
- `opal/tools/brain-tool/brain_tool.py:869,1252`: `cwd = pathlib.Path.cwd()` — 프로세스 실행 위치에 의존한다.
- **결론(Q2 재작성, 환경변수 철회 반영)**: 8곳 중 project_root 파생 방식이 **3갈래**로 갈린다 — (a) 인자 전달(dashboard 5곳, `scan_projects(cfg.scan_roots, ...)` 또는 `_find_project_path(project)`에서 이미 확정된 절대경로), (b) 다른 인자(md_path)의 부모 경로 역산(memory-tool — **코드 파일 자기 위치가 아니라 데이터 파일 인자의 부모**, 표현 정정), (c) `cwd()`(brain-tool·code-scan.js). 환경변수가 철회됐으므로 "오버라이드 우선순위" 문제 자체가 사라졌다 — 남는 질문은 **세그먼트 해석 함수를 다중 프로젝트 스캔 루프(예: `tasks.py`의 `for proj_path in project_paths`, `scanner.py`의 `scan_projects` 순회)에 어떻게 적용하는가**다. 답: 스캔 루프의 각 `proj_path`는 이미 **개별 프로젝트의 확정된 절대경로**이므로(§1.3 (a)), 세그먼트 해석 함수를 그 값 각각에 **개별 적용**하면 된다 — 워크트리 스캔 루프 자체가 실재하지 않으므로(콘솔 BE는 항상 허브에서 실행, 워크트리를 `scan_roots`로 등록하는 경로가 없음, `dashboard/backend/config.py` 재확인) 이 루프에서 세그먼트 규칙은 실질적으로 **항상 no-op**(모든 `proj_path`가 이미 허브)이다. 즉 다중 프로젝트 스캔 루프는 세그먼트 규칙 적용의 **대상이 아니라 무해한 통과 경로**다.

### 1.4 테스트 현황

- state-tool: `opal/tools/state-tool/tests/test_state_tool.py` 396 passed / 1 failed / 6 skipped(허브 실측, 2026-09-06 재확인 — TASK.md §배경분석(3) 수치와 일치).
- console BE: `dashboard/backend/tests` 348 passed / 9 failed / 1 skipped(허브 실측, 재확인 — TASK.md §배경분석(3)과 일치). 실패 9건 전체 목록:
  `test_t103_ts015_missing_state_json_returns_200` · `test_t103_ts015_gate_recorded_distinguishes_zero_from_unrecorded` · `test_t103_ts020_dashboard_task_counts_identity` · `test_t103_ts021_workflow_stats_cohort_filtered_medians` · `test_t103_ts022_artifact_total_identity` · `test_t103_ts017_task_detail_legacy_fields_unchanged[089-260811-opi-opal]` · `test_t103_ts108_dashboard_three_series_is_additive` · `test_t103_ts137_disabled_setting_restores_wall_clock` · `test_state_missing_task_still_carries_owner_term` — 전부 `dashboard/backend/tests/test_routers.py` 소재.

## 3. 영향 범위

### 3.1 직접 영향

§1.1 표 전체 — 8개 경로 조립 지점 + 3개 문서 + worktree-tool 응답.

### 3.2 간접 영향

- `opal/tools/worktree-tool/schema/worktree.schema.json`은 `.opal/worktree.json`(설정 입력) 검증용이지 CLI 응답(JSON stdout) 스키마가 아니다(`worktree.schema.json:3`: "worktree-tool이 소비하는 프로젝트 선언 파일... 런타임에 로드되지 않는다(DEC-4)"). 따라서 `cmd_create`의 `ok_response(...)` 호출부(`worktree_tool.py:828-841`)에 kwarg를 추가해도 이 스키마와 충돌하지 않는다 — R-4 AC(b)는 이 함수 호출 외 다른 서브커맨드(`init`/`list`/`status`/`remove`)를 건드리지 않는 것만으로 자연히 성립한다.
- `dashboard/backend/scanner.py:_count_tasks`와 `dashboard.py:_collect_all_tasks`는 **1-depth만 순회**한다(`os.scandir(tasks_dir) if entry.is_dir()`). 태스크 107의 백업 이관으로 `tasks/080~099`가 `tasks/backup/` 아래로 내려가면서, 이 두 함수는 그 20개 태스크를 **더 이상 집계하지 않는다**(백업 폴더 1개만 1-depth 항목으로 보임). 이는 8곳 경로 조립(R-1)과 무관한 **디렉토리 구조 가정(1-depth 비재귀)의 별개 결함**이다.

### 3.3 영향 범위 요약

- [ ] DB 스키마 변경 — 해당 없음
- [x] API 인터페이스 변경 — `worktree-tool create` 응답에 필드 추가(additive)
- [ ] 설정/환경변수 변경 — 해당 없음(`OPAL_TASKS_ROOT` 신설 철회, TASK.md 개정본)
- [ ] 빌드/배포 파이프라인 변경 — 해당 없음(소스 수정 후 install 재배포 필요하나 파이프라인 자체 변경은 아님)

## 4. 핵심 발견 사항

1. **런타임 간 공용 임포트 모듈은 성립하지 않는다(Q1)** — `opal/tools/*`는 `__init__.py` 없는 단일 스크립트군이고 console BE는 이를 서브프로세스로만 호출한다(`state_adapter.py:19-31`). 따라서 "헬퍼를 한 모듈로 만들어 양쪽이 import"하는 안은 구조적으로 불가하다 — 계약(변수명·우선순위·폴백 규칙)만 공유하고, 구현은 런타임별로 각 1곳(`dashboard/backend` 공용 유틸 1개 + `opal/tools` 공용 유틸 1개, 총 2개)에 두는 편이 현실적이다.
2. **`project_root` 파생 방식이 3갈래로 갈리지만 다중 프로젝트 스캔 루프는 위험하지 않다(Q2)** — 인자 전달(dashboard) / 다른 인자의 부모 역산(memory-tool) / `cwd()`(brain-tool·code-scan.js). 환경변수 신설이 철회되며 "오버라이드 우선순위" 문제는 사라졌다. dashboard의 스캔 루프가 순회하는 `proj_path`는 이미 확정된 절대경로이고 워크트리를 `scan_roots`로 등록하는 경로가 없어(재확인), 세그먼트 해석 함수를 개별 적용해도 스캔 루프에서는 항상 no-op다.
3. **테스트 하드코딩 4곳의 성격이 균질하지 않다(Q3)** — `test_stats.py:59`는 TASK.md의 claim과 달리 **실 폴더를 참조하지 않는다**(동결 fixture JSON만 사용, `test_stats.py:73`) — 사실오류로 정정. `test_state_tool.py:4559-4568`은 자기 docstring이 "tmp_path 합성 픽스처로 대신할 수 없는 목표달성 검증"이라 명시한다 — 여기서의 하드코딩 제거는 곧 검증 대상(실제 저장소 데이터 대조)의 축소이므로, R-3 AC(b) "단언 강도 무변경"과 정면으로 충돌한다. PLAN은 이 1곳만 "폴더 이동에도 견디는 동적 탐색"(예: `tasks/` 및 `tasks/backup/`을 모두 훑어 `098-*` 접두 폴더를 찾는 로직)으로 대체하는 방안을 검토해야 하며, 완전히 픽스처화하면 안 된다.
4. **console BE 9건 중 5건은 경로 조립과 무관한 별개 원인이다(Q4/Q5)** — `scanner.py:29`/`dashboard.py:50`의 1-depth 비재귀 스캔이 `tasks/backup/` 하위로 옮겨진 20개 폴더를 아예 안 본다. R-1(경로 조립 수렴)이 이 헬퍼에 반영돼도 **비재귀 스캔 자체는 고쳐지지 않으므로** 이 5건(`ts020`·`ts021`·`ts022`·`ts108`·`ts137`)은 R-1만으로 해소되지 않는다. 나머지 4건(`ts015` 2건·`ts017[089]`·`state_missing_task_still_carries_owner_term`)은 `test_routers.py:1010-1011`의 `_T103_TASK_089` 폴더가 실제로 이동/부재해 404가 나는 경우로, R-3(테스트 하드코딩 제거)의 소관이다. **PLAN은 R-1~R-4 어느 것도 이 5건을 명시적으로 커버하지 않음을 인지하고, R-5 AC(b) "허브 console BE 0 failed"를 달성하려면 별도 처방(예: 스캐너 재귀 깊이 확장 또는 `backup/`을 집계에서 의도적으로 제외하는 규칙)을 R-1~R-4 중 하나에 명시적으로 편입하거나 R-6을 신설해야 한다.**
5. **`.opal`은 현재 신규 워크트리에 실재하지 않는다** — `.opal/worktree.json`의 `repos`(7항목, `.opal` 미포함)는 유일 커밋 이래 불변이고, 본 태스크용으로 정규 생성된 `.opal-worktrees/task_109`에는 `.opal` 디렉토리 자체가 없다. task_107 워크트리에 `.opal`이 존재하는 것은 도구 기본 동작이 아니라 그 워크트리에 대한 개별 개입의 흔적으로 보인다. R-4/PLAN은 "워크트리에서 `.opal/brain`·`.opal/MEMORY.json`을 항상 읽을 수 있다"는 전제를 깔면 안 된다.

## 5. 제약/리스크

| 항목 | 설명 | 심각도 | 근거 |
|------|------|--------|------|
| (철회) 다중 프로젝트 스캔과 단일 env var 충돌 | `OPAL_TASKS_ROOT` 신설 자체가 철회되어 소멸한 리스크 — 세그먼트 해석 함수는 스캔 루프에서 no-op(Q2 재작성) | - | 해당 없음 |
| code-scan 설정 경로·스캔 루트 미분리 | `loadConfig`·`discoverFiles`·`buildCtx` 전부 단일 `projectRoot` 인자를 공유한다(`code-scan.js:377-378,962-991,1277-1280`) — 설정만 허브에서 읽고 스캔은 워크트리에서 하려면 이 인자를 둘로 쪼개야 하며 파급이 넓다(Q10) | 상 | `code-scan.js:377-378,513-515,962-991` |
| `findProjectRoot()`에 세그먼트 규칙 부재 | 워크트리 cwd에서 `.git`(파일)을 먼저 만나 상향 탐색이 멈추고 `.opal-worktrees` 세그먼트를 검사하지 않는다 — `header_source_unset`의 코드 레벨 원인(Q9) | 상 | `code-scan.js:331-341` |
| S-31 테스트 단언 약화 리스크 | `test_state_tool.py:4559-4568` docstring이 실 데이터 대조가 검증 본질이라고 명시 — 완전 픽스처 대체 시 R-3 AC(b) 위반 | 상 | `opal/tools/state-tool/tests/test_state_tool.py:4559-4568` |
| console BE 5건이 R-1~R-4 범위 밖 | 스캐너 1-depth 비재귀는 경로 조립 문제가 아니라 별도 결함 — R-5 AC(b) 미달 가능 | 상 | `dashboard/backend/scanner.py:29` · `dashboard.py:50` |
| doctor.py 순환 가능성 | `doctor.py:85`가 R-1 헬퍼(OPAL_TASKS_ROOT 인지)를 그대로 쓰면, 진단 대상 프로젝트의 실제 `tasks/` 존재 여부가 아니라 오버라이드 경로의 존재 여부를 보고하게 됨 | 중 | `dashboard/backend/routers/doctor.py:83-90` |
| `.opal` 워크트리 부재 전제 오류 | TASK.md 사실 기재가 실측과 다름 — R-4 설계가 잘못된 전제 위에 설 위험 | 중 | 본 문서 §확정 입력 판정 표 |

## 6. 기술 컨텍스트

### 6.1 프로젝트 SSOT

전체 기술 스택은 `docs/PROJECT.md`를 참조한다. 이 섹션은 재기재하지 않는다.

### 6.2 이번 태스크 델타

변경 없음(SSOT 그대로) — 신규 기술 도입 없음. 환경변수 계약(`OPAL_TASKS_ROOT`) 신설은 스택이 아니라 런타임 설정.

### 6.3 추천 스킬

해당 없음(범용 하네스/도구 개선 — 특정 프레임워크 스킬 불필요).

### 6.4 추천 MCP

해당 없음.

## 7. 지정 분석 질문 Q1~Q12 답변

> **정정 요약**: Q1·Q3·Q4·Q5·Q7·Q8은 1차 산출물에서 전제 변경 없이 유지한다. Q2는 `OPAL_TASKS_ROOT` 철회로 질문 자체가 무효화되어 "세그먼트 해석 함수가 다중 프로젝트 스캔 루프에서 어떻게 동작해야 하는가"로 재작성했다. Q9~Q12는 신규다.

- Q1: `dashboard/backend`는 `opal/tools/*`를 import할 수 없다(`__init__.py` 없는 단일 스크립트군, 서브프로세스 계약뿐). 공용 헬퍼는 **런타임별 2개**로 두고 계약(변수명·우선순위·폴백)만 공유해야 한다.
- Q2(재작성): 8곳 중 project_root 파생이 **3갈래**(인자 전달/다른 인자의 부모 역산/`cwd()`)로 갈리지만, `OPAL_TASKS_ROOT`가 철회되며 "오버라이드가 스캔 루프를 오염시키는가"라는 원래 질문은 소멸했다. 대신 실측한 것: dashboard 스캔 루프(`tasks.py`의 `for proj_path in project_paths`, `scanner.py`의 `scan_projects` 순회)가 순회하는 각 `proj_path`는 `config.py`의 `scan_roots`에서 나오고, 이 `scan_roots`에 워크트리 경로를 등록하는 코드 경로가 없다(재확인, 콘솔 BE는 항상 허브 프로세스로 실행됨). 따라서 세그먼트 해석 함수를 스캔 루프의 각 `proj_path`에 개별 적용해도 **모든 `proj_path`가 이미 허브 경로이므로 함수는 no-op**가 된다 — 다중 프로젝트 스캔 루프는 별도 예외 처리가 필요 없고, 다른 6곳(단일 프로젝트 맥락)과 동일한 함수를 그대로 통과시키면 된다.
- Q3: 4곳 중 `test_stats.py:59`는 **사실오류**(실 폴더 미참조, 동결 fixture만 사용) — 대상에서 제외. `test_state_tool.py:4569`(S-31)는 docstring이 "실 데이터 대조가 목표달성 검증의 본질"이라 명시 — 완전 픽스처화는 단언 약화, 동적 탐색(부재 폴더명 대신 접두사 검색)으로 대체 검토 필요. `test_routers.py:1010-1011`·`test_adapters.py:85`는 편의적 실 폴더 참조이나, 후자는 이미 `pytest.skip` 가드 보유로 상대적으로 견고.
- Q4: 허브 console BE 9건 중 4건(`ts015` 2건·`ts017[089]`·`state_missing_task_still_carries_owner_term`)은 (a) 폴더명 하드코딩, 5건(`ts020`·`ts021`·`ts022`·`ts108`·`ts137`)은 (b) `tasks/` 1-depth 집계 의존 — (b)는 하드코딩 제거로 안 풀리며, `scanner.py`/`dashboard.py`의 비재귀 스캔에 대한 별도 처방이 필요하다.
- Q5: 워크트리 델타 24건은 전건 `tasks/` 부재(B) 단일 원인으로 실측됐다(허브 396/348 대비 워크트리 396/322, state-tool 델타 0 + console BE 델타 24 — 별도 원인 미발견).
- Q6: `doctor.py:85`는 인자로 받은 project_path의 `tasks/` 존재를 진단하는 용도이며, R-1 헬퍼가 `OPAL_TASKS_ROOT`를 그대로 반영하면 "이 프로젝트에 tasks/가 있는가"가 아니라 "오버라이드 경로에 tasks/가 있는가"로 의미가 바뀌어 순환·오진 리스크가 생긴다. 판정: **doctor.py는 R-1 수렴 대상에서 제외**하고 현행 `p / "tasks"`를 유지하는 편이 진단 도구의 목적(프로젝트 리터럴 상태 확인)에 부합한다(PLAN 최종 결정 필요).
- Q7: `cmd_create`의 `ok_response(command="create", ...)` 호출부(`worktree_tool.py:828-841`)에 kwarg 1개를 추가하면 된다 — CLI 응답은 `worktree.schema.json`(설정 파일 전용, DEC-4)의 검증 대상이 아니므로 스키마 충돌이 없고, 다른 서브커맨드(`init`/`list`/`status`/`remove`)는 미변경이라 `--wt` 미사용 시 스키마 무변경(AC(b))이 자연히 성립한다.
- Q8: 허브 실측 재확인 — state-tool 396 passed/1 failed/6 skipped, console BE 348 passed/9 failed/1 skipped. **TASK.md §배경분석(3)의 허브 수치와 일치, 정정 불필요.** 워크트리 재실행은 코드 변경 전 단계라 §배경분석(3)의 기존 수치를 승계(재실행 시 동일 실패 패턴 예상되나 본 ANALYSIS 단계에서 재검증하지 않음 — PLAN/TEST 단계 소관).

- **Q9(해석 함수의 입력): 8곳(+code-scan.js) 중 어디도 `__file__`(코드 자기 위치)을 project_root로 쓰지 않는다.** 실측 재확인 결과 입력은 두 갈래뿐이다 — (A) 인자로 이미 확정된 절대경로: dashboard 5곳(`_find_project_path`/`scan_roots`에서 옴) + memory-tool(`_resolve_last_task_number(md_text, project_root)`가 받는 `project_root`는 `memory_tool.py:739` `md_path.parent.parent` — **`md_path`라는 별개 인자의 부모 경로**이지 memory_tool.py 자신의 소스 위치가 아니다, ANALYSIS 1.3의 "파일 자기 위치 역산" 표현은 오해 소지가 있어 본 정정에서 바로잡는다) (B) `cwd()` 직접 호출: brain-tool(`brain_tool.py:869,1252,867`) + code-scan.js `findProjectRoot()`(`code-scan.js:332`). PM이 예시한 "허브에서 워크트리 스크립트 파일을 cwd=허브로 실행"(`node .opal-worktrees/task_109/opal/tools/code-scan/code-scan.js`를 허브 cwd에서 실행) 시나리오를 실측 검증: `findProjectRoot()`는 `process.cwd()`(허브)에서 시작해 즉시 `.git`을 찾아 **허브 경로를 반환한다** — 스크립트 파일의 물리적 위치(워크트리)는 이 함수에 전혀 영향을 주지 않는다(코드에 `__dirname`/`require.main` 등 자기 위치 참조가 없음, `code-scan.js` 전체 재grep 확인). 즉 PM이 우려한 "`__file__` vs cwd 불일치" 조합은 **실재하지 않는다** — 셋이 아니라 둘(인자/`cwd()`)뿐이고, 어느 사이트도 파일 위치를 쓰지 않으므로 애초에 그 축의 충돌이 성립할 수 없다. **실재하는 문제는 반대 방향**이다: 워크트리 **내부에서** 실행할 때(`cwd`=워크트리) `findProjectRoot()`가 워크트리 자신의 `.git`(파일)에서 멈춰 부모(허브)로 올라가지 않는다(`code-scan.js:333-337` — `.git` 존재 검사가 `.opal-worktrees` 세그먼트 검사보다 먼저이자 유일한 종료 조건). 결론: 세그먼트 해석 규칙은 **기존 두 입력 방식(인자/`cwd()`)을 대체하는 제3의 입력이 아니라, 그 위에 얹는 후처리 정규화**여야 한다 — "이미 확정된 project_root 후보 문자열에 `.opal-worktrees` 세그먼트가 있으면 그 앞부분을 반환"하는 함수로, 인자 기반 6곳(변경 불필요, 이미 허브 값)과 `cwd()` 기반 2곳(브레인툴·code-scan, 세그먼트 정규화 적용 필요) 양쪽에 동일하게 씌우면 된다.

- **Q10(`.opal/` 참조와 스캔 대상의 분리): 현재 code-scan.js는 설정 경로와 스캔 대상을 분리하지 않는다 — 동일 `projectRoot` 변수 하나가 양쪽을 겸한다.** `loadConfig(projectRoot)`(`code-scan.js:377-378`)는 `{projectRoot}/.opal/code-scan.json`을 읽고, `discoverFiles(projectRoot, config, opts)` → `getSearchPaths(projectRoot, ...)`(`962-991`)는 스코프 경로를 **같은** `projectRoot` 기준 `path.resolve`로 조립하며, `buildCtx(projectRoot, ...)`(`1277-1280`)의 `ctx.projectRoot`가 이후 `classifyUncovered`·manifest 경로(`1362`)·설계 루트(`readDesignRootFromProjectMd`, `478-479`, `docs/PROJECT.md`도 같은 루트)까지 전부 전파된다. 분리하려면 이 호출 체인 전체(적어도 6개 함수)에 `configRoot`/`scanRoot` 두 값을 각각 통과시켜야 하는데, `docs/PROJECT.md` 참조(설계 루트)나 `code-map/index.json`(`loadCodeMap`, `1216-1217`)처럼 "허브 문서를 워크트리에서도 봐야 하는" 지점과 "워크트리 소스만 스캔해야 하는" 지점이 같은 함수 안에 섞여 있어 **분리가 과도하다 — 사실상 code-scan.js 절반을 이중 경로 인자로 재작성해야 한다.** 따라서 TASK.md가 이미 시사한 대안(`--header-source` 플래그류 주입)이 타당하다: **분리 대신, `findProjectRoot()`가 세그먼트 정규화(Q9)로 워크트리에서도 허브를 정확히 반환하게 하고, `projectRoot` 단일값을 계속 "설정도 스캔도 허브 기준"으로 유지한다.** 이는 §확정된 설계 방향의 "code-scan.json 복사 철회" 결정과도 정합적이다 — 복사도 분리도 하지 않고, 유일한 진짜 결함(세그먼트 미인식)만 고친다.

- **Q11(console BE 집계 의존 5건의 처방): `tasks/backup/`으로 옮긴 20개 폴더를 1-depth 스캔이 못 보는 것이 근본 원인이며, 단순 재귀 전환은 새 항등 위반을 만든다.** 실측: `scanner.py:_count_tasks`(`:23-30`)와 `dashboard.py:_collect_all_tasks`(`:38-...`)는 `os.scandir(tasks_dir)`로 1-depth만 순회하고, `tasks.py`의 `/api/tasks` 목록 엔드포인트(`:459-465`)는 **이미 `backup` 폴더명을 명시적으로 스킵**한다(`if entry.name == "backup": continue`, `tasks.py:463-464`) — 즉 "일반 태스크 카드 목록"은 backup을 원천 제외하도록 이미 고쳐져 있는데, `scanner.py`·`dashboard.py`는 그 규칙이 없어 **backup 폴더 자체를 1개의 (잘못된) 태스크 항목으로 세거나(scanner), 혹은 아예 하위를 못 봐서 20건이 통째로 빠진다(dashboard 집계)**. 재귀 스캔으로 단순 전환하면 `tasks/backup/080-.../`처럼 백업 하위 20건이 **다시 잡혀** `total_tasks`·`workflow_stats` 등의 모수에 포함되고, 이는 `tasks.py`가 이미 확립한 "backup은 집계 제외"(§배경분석 (3) 주석 "백업 폴더는 아카이브 컬럼으로 별도 처리") 규칙과 **어긋나 새 항등 위반**을 만든다(`tasks.py`의 목록 API와 `dashboard.py`의 집계 API가 backup 포함 여부에서 서로 달라짐). 처방 후보 2개: **(a) `tasks.py`의 `entry.name == "backup"` 스킵 규칙을 `scanner.py`·`dashboard.py`에 그대로 이식하고 두 함수 다 1-depth로 유지** — 부작용: 규칙 중복(3곳에 같은 문자열 리터럴), 향후 4번째 집계 지점이 생기면 또 빠뜨릴 위험. **(b) 재귀 스캔으로 바꾸되 `backup` 세그먼트를 만나면 그 서브트리 전체를 walk에서 제외**(예: `os.walk`에서 `dirnames`가 `backup`을 만나면 `dirnames.remove("backup")`) — 부작용: 1-depth보다 스캔 비용이 커지고(파일 수 많은 프로젝트에서 O(n) 증가), `backup/` 아래 또 다른 `backup/`(중첩)이 생기면 이름 매칭 규칙을 재검토해야 한다. **PLAN 권고: (a)가 더 낫다** — 이미 `tasks.py`에 준칙이 있고 재귀 전환의 성능·엣지케이스 리스크가 없다.

- **Q12(두 구현 동치 테스트의 위치): 한 테스트로 두 런타임을 동시에 검증하는 것은 가능하지만 무겁다 — 서브프로세스 호출이 유일한 경로다.** `dashboard/backend`는 `opal/tools/*`를 import할 수 없으므로(Q1), 파이썬 프로세스 하나에서 두 구현을 직접 호출·비교하는 단위 테스트는 성립하지 않는다. 가능한 방식은 (i) `dashboard/backend/tests/`에 테스트 하나를 두고 그 안에서 `subprocess.run(["python", "opal/tools/.../resolve_root.py", ...])`처럼 **opal 쪽 CLI를 서브프로세스로 호출**해 dashboard 쪽 함수 리턴값과 비교하는 통합 테스트, 또는 (ii) 각 런타임 테스트 스위트에 **동일 케이스 표(고정 fixture)** 를 따로 두고 표 자체를 한 SSOT 파일(JSON/YAML)로 공유해 두 스위트가 같은 표를 읽게 하는 방식. **(i)는 실제 프로세스 경계를 넘는 진짜 동치 검증이지만 opal 쪽에 "결과만 stdout으로 찍는 얇은 CLI 서브커맨드"가 없으면 새로 만들어야 하고(현재 `memory_tool.py`/`brain_tool.py`는 이 해석 로직을 노출하는 전용 커맨드가 없음, 재확인), pytest 안에서 Node/Python 프로세스를 기동하는 비용도 든다. (ii)는 가볍지만 "표가 갈라지지 않게" 하려면 표 파일 자체를 두 스위트가 같은 경로에서 읽어야 하는데, 두 런타임의 테스트 루트가 다르므로(`dashboard/backend/tests/` vs `opal/tools/*/tests/`) **공유 표 파일을 두 곳 모두가 상대경로로 읽을 수 있는 위치**(예: 허브 루트의 `docs/` 또는 `opal/core/references/` 하위 JSON)에 둬야 한다. **PLAN 권고: (ii) + 공유 표 파일**을 채택하고, 표 파일 자체의 신선도는 R-1 SSOT 문서(§Q9 세그먼트 규칙)에 대한 골든 케이스로 버전 관리한다 — (i)는 CLI 서브커맨드 신설이 별도 요구사항(R-2 범위 밖)이 되므로 이번 태스크의 필수 조건으로 두지 않는다.

## 8. 다음 단계 입력 — PLAN이 재조사 없이 쓸 수 있는 확정값

| 항목 | 확정값 | 근거 |
|------|--------|------|
| 헬퍼 구조 | 런타임별 2개(dashboard/backend 1 + opal/tools 1, code-scan.js는 opal 쪽에 귀속), import 공유 불가 | §7 Q1 |
| `OPAL_TASKS_ROOT` | **신설하지 않는다(철회 확정)** — 세그먼트 해석 함수로 대체 | §확정 입력 판정, TASK.md 개정본 |
| 세그먼트 해석 함수의 위치 | 기존 project_root 확정값(인자 또는 `cwd()`) **위에 얹는 후처리**로 구현 — 제3의 입력(`__file__`)을 새로 만들지 않는다 | §7 Q9 |
| 세그먼트 해석 함수 vs 다중 프로젝트 스캔 루프 | 스캔 루프의 `proj_path`는 항상 이미 허브 경로라 함수는 no-op — 예외 처리 불필요 | §7 Q2(재작성) |
| code-scan 설정 경로 vs 스캔 루트 | **분리하지 않는다** — 분리 시 6개 이상 함수 이중 인자화가 필요해 과도, 대신 `findProjectRoot()`에 세그먼트 정규화만 추가 | §7 Q10 |
| `test_stats.py:59` | R-3 대상에서 제외(사실오류) | §확정 입력 판정, `test_stats.py:56-98` |
| `test_state_tool.py:4569`(S-31) | 완전 픽스처화 금지 — 동적 탐색(접두사 검색) 방식만 허용 | §4 핵심발견 3 |
| console BE 9건 중 5건(집계 의존) | R-1~R-4 범위 밖 — `tasks.py`의 기존 `backup` 스킵 규칙을 `scanner.py`·`dashboard.py`에 이식(권고안 (a), 재귀 전환 (b)는 항등 위반 부작용 있어 비권고) | §7 Q11 |
| 두 구현 동치 테스트 | 서브프로세스 통합 테스트(무겁다) 대신 **공유 골든 케이스 표 파일**을 두 스위트가 각자 읽는 방식 권고 | §7 Q12 |
| `doctor.py` | R-1 수렴 제외 권고(현행 `p / "tasks"` 유지) | §7 Q6 |
| worktree-tool 응답 확장 지점 | `worktree_tool.py:828-841` `ok_response(command="create", ...)`에 kwarg 추가 | §7 Q7 |
| `.opal` 워크트리 실재 전제 | 무효 — 신규 워크트리엔 `.opal` 없음(코드도 없음: `code-scan.js`의 `findProjectRoot()`가 `.opal`을 찾기 전에 워크트리 자신의 `.git` 파일에서 먼저 멈춘다), R-4 설계에서 전제 삼지 말 것 | §확정 입력 판정, §7 Q9 |
| `code-scan.json` 복사 | **하지 않는다(철회 확정)** — 스코프가 상대경로라 복사 시 워크트리를 스캔하게 됨 | §확정 입력 판정 |

### PLAN 결정 필요

| 항목 | 쟁점 | 근거 |
|------|------|------|
| console BE 5건(비재귀 스캔) 처방 | R-1~R-4로 커버 안 됨 — R-6 신설 or 기존 R에 편입 여부, 처방은 (a) `backup` 스킵 이식 권고 | §7 Q11 |
| S-31 동적 탐색 구현 방식 | `tasks/098-*` 접두사 검색을 `tasks/`·`tasks/backup/` 양쪽에서 수행할지, 다른 방식(글롭)을 쓸지 | §4 핵심발견 3 |
| `doctor.py` 최종 처리 | R-1 제외 vs 포함 — Q6 판정을 그대로 채택할지 재검토할지 | §7 Q6 |
| 세그먼트 정규화 함수의 정확한 시그니처·배치 | 인자 기반 6곳은 값이 이미 허브라 무변경, `cwd()` 기반 2곳(brain-tool·code-scan.js)에만 정규화를 씌우는 구체 코드 위치 | §7 Q9 |
| code-scan.js `findProjectRoot()` 개정 방식 | `.git` 발견 시 즉시 반환하는 현행 로직에 세그먼트 검사를 어느 지점에 삽입할지(발견 직후 vs 최상위 진입점) | §7 Q9·Q10 |
