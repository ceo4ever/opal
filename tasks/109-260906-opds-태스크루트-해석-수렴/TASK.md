# TASK: 태스크 루트 해석 수렴 + `OPAL_TASKS_ROOT` 계약 신설

> 작성일: 2026-09-06 | 작업 유형: 개선 | 적용 스킬: opds | 모드: agentic | 워크스페이스: `--wt`
> 입력: 사용자 요청 (태스크 107 이월 + 백업 이관 파급)
> 출력: TASK.md

## 작업 목표

**계약은 옳고, 계약을 집행하는 코드가 없다.**

하네스 §2.5는 「태스크 문서(`tasks/`)·`.opal/MEMORY.json`·`.opal/brain/`은 분기하지 않고 **허브에 고정**한다」고 규정한다 — 즉 워크트리는 그것들을 **참조**해야 한다. 그런데 **참조를 구현한 코드가 없다.** 경로 조립 8곳이 전부 `<자기 루트>/tasks` 형태이며, 워크트리에서 실행되면 `<자기 루트>`가 워크트리라 존재하지 않는 곳을 가리킨다. 아무도 「허브가 어디냐」를 묻지 않는다.

**허브 루트 해석 규칙**을 세우고 조립 지점을 그 함수로 수렴시켜, **허브·워크트리 양쪽에서 0 failed**를 만든다. 별개 축으로 테스트의 실 태스크 폴더 하드코딩도 제거한다(위치 변경 내성).

## 배경

두 사건이 같은 뿌리에서 나왔다.

**(A) 위치가 바뀌면 깨진다** — 완료 태스크 20건(080~099)을 `tasks/backup/`으로 이관하자 **허브에서** state-tool 1건 + console BE 7건이 새로 실패했다(이관 전 각 0건·2건).

**(B) 존재하지 않으면 깨진다** — 태스크 107을 `--wt`로 진행할 때 워크트리에 `tasks/`가 없어 34건이 실패했다. 워크트리 계약(`opal-harness.md` §2.5)상 태스크 문서는 허브에 고정되고 sparse-checkout 패턴(`.opal/worktree.json` `repos`)에 `tasks/`가 없다.

107은 이를 「워크트리 기준선 대비 증분」 판정으로 우회했으나, 그 재정의는 PM의 임기응변이지 규범이 아니다.

## 배경 분석 (실측)

### (1) 경로 조립 지점 **9곳** (PLAN 실측 정정 — 초안 8곳)

| 파일 | 줄 | 형태 |
|------|----|------|
| `dashboard/backend/routers/tasks.py` | `:457`·`:520`·`:654` | `os.path.join(proj_path, "tasks")` 외 2 |
| `dashboard/backend/scanner.py` | `:29` | `os.path.join(project_path, "tasks")` |
| `dashboard/backend/routers/dashboard.py` | `:50` | 동형 |
| `dashboard/backend/routers/doctor.py` | `:85` | `p / "tasks"` |
| `opal/tools/memory-tool/memory_tool.py` | `:675` | `pathlib.Path(project_root) / "tasks"` |
| `opal/tools/brain-tool/brain_tool.py` | `:1298` | `cwd / "tasks"` |

| `opal/tools/brain-tool/brain_tool.py` | `:239` | `resolve_brain_path` → `p / ".opal" / "brain"` — **PLAN 실측 추가** |

전부 한 줄짜리 조립이며 공용 헬퍼가 없다.

> **9번째 지점의 파급이 가장 크다** — `resolve_brain_path`(`brain_tool.py:239`)는 워크트리에 `.opal`이 없으면 존재하지 않는 경로를 반환해 **brain-tool 전 명령이 먼저 차단**된다. 초안이 8곳이라 한 목록에 없던 지점이다.

### (2) 테스트의 실 태스크 폴더 하드코딩

| 파일 | 줄 | 참조 |
|------|----|------|
| `opal/tools/state-tool/tests/test_state_tool.py` | `:4569` | `repo_root / "tasks" / "098-260821-opds-근거등급-확정판정-트랙강등" / "TASK.md"` |
| `dashboard/backend/tests/test_routers.py` | `:1010-1011` | `_T103_TASK_091`·`_T103_TASK_089` |
| `dashboard/backend/tests/test_stats.py` | `:59` | `FX_086_ID = "086-260810-opp-…"` |
| `dashboard/backend/tests/test_adapters.py` | `:85` | `Path(__file__).parents[3] / "tasks" / "021-260615-opd-opal…"` |

런타임 `tmpdir` 픽스처(`test_state_tool.py:6404` 등)는 대상이 아니다 — 실 저장소 폴더를 참조하는 건만 해당한다.

### (3) 현재 실패 실측 (2026-09-06 23:2x)

| 스위트 | 허브 | 워크트리(109) | 델타 |
|--------|------|--------------|------|
| state-tool | **1 failed** / 396 passed / 6 skipped | **1 failed** / 396 / 6 | 0 |
| console BE | **9 failed** / 348 passed / 1 skipped | **33 failed** / 322 / 3 | **24** |

- 허브 state-tool 1건 = `TestT098EvidenceCheck::test_s31_self_task_md_real_file_confirmed_ratio` — (A) 유래
- 허브 console BE 9건 중 7건이 (A) 유래(이관 전 2건). `test_t103_ts017_…[089-260811-opi-opal]`처럼 폴더명이 파라미터에 박혀 있다
- 워크트리 델타 24건 = (B) 유래

### (4) 성질 진단

(A)와 (B)는 「태스크 폴더를 **데이터**로 쓰면서 그 위치·존재를 **불변으로 가정**한다」는 하나의 문제다. 태스크 107이 brain에 등재한 **「태스크 시점 사실을 영구 회귀 단언으로 고정하면 후속이 구조적으로 걸린다」**(`.opal/brain/pages/concept/regression-pin-of-task-time-fact.md`)의 또 다른 발현이다.

### (5) 워크트리에 `.opal/`이 아예 없다 — 정규 동작 실측

`worktree-tool`은 `sparse-checkout set *cfg["repos"]`(`worktree_tool.py:814`)로 `.opal/worktree.json`의 **`repos` 7항목만** 설정한다. `.opal`은 목록에 없다.

| 워크트리 | sparse 패턴 | `.opal/` |
|---|---|---|
| task_109 (정규 생성) | 7항목 — `.opal` 없음 | **부재** |
| task_107 | **8항목** — `.opal` 포함 | 실재 |

- **task_109가 정규이고 task_107이 예외다.** task_107의 sparse 파일 수정 시각은 **13:52**인데 워크트리 생성은 **11:52**다 — 생성 2시간 뒤 누군가 `git sparse-checkout add .opal`을 실행했다. 태스크 107의 Phase 2~3 워커 구간이며, code-scan이 `.opal/code-scan.json`을 못 찾아 워커가 sparse 패턴을 직접 바꾼 것으로 판단된다.
- **미검출 scope 위반이다.** PM이 워커에게 파일 범위를 [MUST]로 못박았으나 **sparse 패턴 변경은 어떤 규칙도 막지 않았고 PM도 검출하지 못했다.** 태스크 107 내내 워크트리에서 code-scan이 동작한 것이 이 무단 변경 덕이었다.
- 파급: 정규 워크트리에서는 **code-scan이 애초에 동작하지 않는다** — 실측 `{"ok":false,"error":"header_source_unset"}`. `--wt` 태스크가 `@header` 검증을 수행할 수 없다.
- 따라서 참조 대상은 `tasks/`만이 아니라 **`.opal/` 전체**다(`code-scan.json`·`brain/`·`MEMORY.json`).

### (6) 완료기준 초안의 오류 — 허브가 이미 `exit 2`다 (PLAN 실측)

초안 완료기준은 「정규 워크트리에서 `code-scan validate` exit 0」이었다. **달성 불가능한 기준이다.**

```
허브 code-scan validate → exit=2, 차단 위반 3건
  uncovered:incomplete  dashboard/frontend/src/lib/api-timeout.test.ts
  uncovered:incomplete  dashboard/frontend/src/lib/utils.test.ts
  uncovered:incomplete  dashboard/frontend/src/pages/brain/brain-status.test.ts
```

FE 테스트 3파일의 `@header`가 불완전해 **세그먼트 수정과 무관하게** 허브가 exit 2다. 워크트리를 허브와 같게 만들어도 exit 0이 될 수 없다. 판정 축을 「exit 0」에서 **「허브와 동일한 exit·차단 위반 집합」**으로 옮기고, 그 3파일 정비를 **R-7**로 편입한다.

### (7) ANALYSIS 「backup 스킵 이식」 권고는 사실오류다 (PLAN 실측)

ANALYSIS §8은 console BE 집계 5건의 처방으로 「`tasks.py`의 `backup` 스킵 규칙을 `scanner.py`·`dashboard.py`에 이식」을 권고했다. **이식하면 계속 실패한다.**

`test_routers.py`의 동결 코호트 21건 중 **19건이 `tasks/backup/` 아래**다(`080~099`; `tasks/` 직속은 `100`·`101` 둘뿐). `test_routers.py:1435`가 `set(cohort) <= observed_prefixes`를 단정하므로 backup을 제외하면 19건이 관측 집합에서 사라진다.

비대칭 진단(「`tasks.py`만 backup을 안다」)은 옳았으나 **맞추는 방향이 반대**였다 — 스킵 이식이 아니라 **「1-depth + `backup` 1-depth 2단 열거 + 아카이브 플래그」를 단일 함수로 두고 3지점이 같은 함수를 호출**하는 것이 답이다(R-6).

## 확정된 설계 방향 (대화에서 합의)

- **[결정]** 범위는 **(A)+(B) 둘 다**다. (B)만 닫으면 「워크트리는 허브와 같아졌는데 허브가 깨져 있다」가 되어 목표 진술이 성립하지 않는다.
- **[결정]** **허브 루트 해석 규칙**을 세운다 — 자기 경로에 **`.opal-worktrees` 세그먼트**가 있으면 그 **부모가 허브**이고, 없으면 자기 프로젝트 루트다. 깊이가 아니라 세그먼트 이름을 보므로 monorepo·multi-repo 레이아웃과 무관하게 성립한다(실측 확인).
- **[결정]** **환경변수를 신설하지 않는다.** `OPAL_TASKS_ROOT` 안은 철회한다 — 허브 경로는 `.opal-worktrees/.meta/task_{NNN}.json`의 `entries[].repo`에 **이미 기록**돼 있고(실측 확인) 위 경로 규약으로도 유도된다. 없는 정보를 만드는 것이 아니라 있는 정보를 쓰지 않는 것이 문제다. 오버라이드가 필요해지면 그때 추가한다.
- **[결정]** **`.opal/code-scan.json`을 워크트리로 복사하지 않는다.** 복사 안은 철회한다 — 스코프가 전부 **상대경로**(`"framework": "opal/"` 등)라 허브 설정을 읽어 워크트리 루트에 적용하면 워크트리를 스캔한다. 모호성이 없고, 복사하면 오히려 설정 드리프트가 생긴다.
- **[결정]** 구현은 **런타임별 2개, 계약은 1개**다. `dashboard/backend`는 표준 라이브러리만 import하고 `sys.path` 조작이 없으며 `opal/tools/`의 각 도구는 자기 디렉터리만 `sys.path`에 넣는다 — **두 세계 사이에 공용 모듈을 놓을 자리가 없다.** 해석 규칙을 문서 SSOT로 두고 런타임별 함수 1개씩 두며, **두 구현이 같은 답을 내는지 테스트로 고정**한다. 한 런타임 안에서는 반드시 한 곳이다.
- **[사실]** 경로 조립 지점은 **8곳**, 테스트 하드코딩은 **4곳**이다(§배경 분석 (1)(2), 실측).
- **[사실]** 심볼릭 링크 `tasks` 생성 시 `git status`에 **1,022건 `D`**가 뜬다 — sparse-checkout이 `skip-worktree`로 감추던 tracked 파일이 그 경로를 링크가 차지하자 삭제로 인식된다. 워커가 `git add -A` 한 번 하면 브랜치에서 `tasks/`가 통째로 지워진다(워크트리 실험, 원복 확인). **따라서 링크 안은 채택하지 않는다.**
- **[사실]** 워크트리 sparse 패턴은 `worktree.json` `repos` **7항목**(`cursor-rules dashboard docs memory opal scripts skills`)이며 **`.opal`은 없다.** 정규 워크트리(task_109)에 `.opal/`이 부재하고 code-scan이 `header_source_unset`으로 실패한다(§배경 분석 (5), 실측).
- **[사실]** 「워크트리로 옮기고 완료 후 머지」 안은 **현재 태스크 폴더를 담지 못한다** — 워크트리는 브랜치 시점 스냅샷이고 현재 태스크 폴더는 그 이후 허브에 생성된다. 깨진 테스트 중 `test_verify_passes_own_test_scenario_md`가 **자기 태스크의 시나리오 파일**을 검증하므로 옮겨도 계속 깨진다. 또한 `MEMORY.json`·`brain/index.md`·`brain/log.md`는 **단일 파일에 도구가 append**하므로 브랜치마다 수정되면 머지 충돌이 설계상 보장된다. `tasks/`는 18MB·1,026파일이라 슬롯마다 복제된다.

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | **허브 루트 해석 규칙**(자기 경로에 `.opal-worktrees` 세그먼트가 있으면 그 부모가 허브)을 세우고 경로 조립 8곳을 그 함수로 수렴시켜 **허브·워크트리 양쪽 0 failed**를 달성한다. 별개 축으로 테스트의 실 태스크 폴더 하드코딩 4곳을 제거한다 | - | §배경 분석 (1)(2)(3)(5) 실측 |
| 범위 | **포함** — ① 허브 루트 해석 규칙을 하네스 문서에 SSOT로 명문화 ② 런타임별 해석 함수 **3개**(`dashboard/backend/paths.py` 신설 · `brain_tool.py` · `code-scan.js` — Node 런타임이 별도, PLAN 실측 정정) + **구현 동치를 고정하는 공유 골든 케이스 표** ③ 경로 조립 **9곳** 수렴(`tasks/` · `.opal/`) ④ 테스트 하드코딩 제거(`test_stats.py:59`는 사실오류로 제외) ⑤ **console BE 집계 2단 열거**(R-6) ⑥ **FE 테스트 3파일 `@header` 정비**(R-7) ⑦ **이동값 단언 규약 정렬**(R-8 — PLAN 신설, 번호 충돌 정정). **제외** — 환경변수 신설(철회), `code-scan.json` 복사(철회), 심볼릭 링크(철회), sparse 패턴에 `tasks/`·`.opal` 추가, 「워크트리로 옮기고 머지」(철회), 워커 sparse 패턴 변경 차단 가드(별건), `tasks/backup/` 구조 변경 | ④의 방식(런타임 픽스처 vs 동적 탐색)은 PLAN 결정 / `doctor.py`를 수렴 대상에 넣을지(진단 도구의 순환) | `opal-harness.md` §2.5 · `.opal/worktree.json` |
| 제약 | ① **허브 실행 동작 바이트 동일** — 해석 규칙은 허브에서 자기 루트를 반환하므로 현행과 같아야 한다 ② `~/.opal/` 직접 편집 금지, 소스 수정 후 install 재배포 ③ **테스트 단언 약화 금지** — 하드코딩 제거가 검증 범위 축소가 되면 안 된다. 특히 `test_state_tool.py:4569`(S-31)는 자기 docstring이 실 데이터 대조를 검증의 본질로 선언하므로 **완전 픽스처화 금지**, 동적 탐색만 허용 ④ 코드 변경은 워크트리(`feat/OP-TASK-109`)에서만 ⑤ `doctor.py`는 환경 진단 도구다 — 진단 대상 경로 해석에 의존시키면 순환이 생길 수 있어 별도 판정 ⑥ 두 런타임 구현이 갈라지지 않도록 동치 테스트를 필수로 둔다 | ⑤ 판정 | `docs/CONVENTIONS.md` §배포 경계 · §Guards |
| 완료기준 | **허브** state-tool `0 failed` · console BE `0 failed` **AND 워크트리** state-tool `0 failed` · console BE `0 failed`(= 허브와 동일) + **정규 워크트리 `code-scan validate`의 exit·차단 위반 집합이 허브와 동일**(R-7로 허브 차단 3건도 해소하므로 양쪽 exit 0) + **양쪽 `0 skipped`**(R-4 AC(e)) + 허브 실행 회귀 0건 + code-scan 369 회귀 0건 | 허브 `0 failed` 검증 시점은 **머지 후 push 전**이며 실패 시 `git reset --hard`로 머지를 되돌린다(소유자 결정 2026-09-07 — 코드 변경이 워크트리 한정이라 머지 전 검증 불가, 원격에는 통과 상태만 올린다) | §배경 분석 (3)(5)(6) |

## 요구사항

- [ ] **R-1 허브 루트 해석 규칙 명문화** — 무엇을: 「자기 경로에 `.opal-worktrees` 세그먼트가 있으면 그 부모가 허브, 없으면 자기 프로젝트 루트」를 하네스 SSOT로 규정. 어디에: `opal/core/references/opal-harness.md` §2.5. 왜: 계약(「허브 고정 + 워크트리 참조」)은 있으나 **참조 규칙이 없다**. **AC**: (a) 규칙이 한 곳에 정의된다 (b) monorepo·multi-repo 양쪽에서 성립함이 명시된다(깊이 무관·세그먼트 기준) (c) 허브 실행 시 자기 루트를 반환함이 명시된다 (d) 기존 §2.5 경로 계약 문장과 모순되지 않는다
- [ ] **R-2 런타임별 해석 함수 + 동치 고정** — 무엇을: `opal/tools/` 쪽과 `dashboard/backend/` 쪽에 각각 함수 1개. 어디에: PLAN이 배치 결정. 왜: 두 런타임 사이에 공용 모듈을 놓을 자리가 없다(§확정된 설계 방향). **AC**: (a) 런타임별 1개씩 존재하고 한 런타임 안에 중복 구현이 없다 (b) **두 구현이 같은 입력에 같은 답을 내는지 테스트가 고정한다** — 워크트리 경로·허브 경로·multi-repo 깊이 3종 이상 (c) 규칙 원문은 R-1이 소유하고 함수는 포인터 주석만 둔다
- [ ] **R-3 경로 조립 8곳 수렴** — 무엇을: `<자기 루트>/tasks`·`<자기 루트>/.opal` 직접 조립을 해석 함수 경유로 교체. 어디에: §배경 분석 (1) 6파일. 왜: 각자 조립하면 9번째 지점이 또 뚫린다. **AC**: (a) `grep`으로 잔여 직접 조립 0건 (b) console BE·memory-tool·brain-tool 동작 무변경 (c) 허브 실행 결과 바이트 동일 (d) **정규 워크트리에서 `code-scan validate`가 exit 0**으로 동작한다
- [ ] **R-4 테스트 하드코딩 제거** — 무엇을: 실 태스크 폴더·저장소 루트에 고정된 테스트 지점을 폴더 이동·부재에 견디게 바꾼다 — **PLAN 실측: 폴더명 하드코딩 3곳 + 저장소 루트 `__file__` 파생 3곳**(`PLAN.md:33`·`:481`. 초판 「4곳」은 실측 전 추정치이며 `test_stats.py:59`를 포함한 수치였다 — 2026-09-07 정정). 어디에: §배경 분석 (2). 왜: (A)의 직접 원인. **AC**: (a) 해당 지점이 특정 폴더명·자기 저장소 루트에 의존하지 않는다 (b) **단언 강도 무변경** — S-31은 실 데이터 대조가 본질이므로 동적 탐색으로만 바꾸고 픽스처로 대체하지 않는다 (c) 완료 태스크를 `tasks/backup/`으로 옮겨도 통과한다 (d) console BE 9건 중 **집계 의존 5건**은 하드코딩 제거로 풀리지 않으므로 별도 처방을 PLAN이 설계한다 (e) **허브·워크트리 양쪽 `0 skipped`** — 워크트리 2건(`test_parsers.py:150,163` 「AGENT.md 없음」)은 R-3 `.opal/` 참조로, 허브 1건(`test_adapters.py:88` 「실 태스크 디렉토리 없음」)은 하드코딩 제거로 해소하며, **새로 켜진 테스트의 신규 실패 0건** (소유자 결정 2026-09-07 — skip은 약화된 단언이므로 AC(b)와 같은 축이다)
- [ ] **R-6 console BE 집계 2단 열거** — 무엇을: 태스크 열거를 「1-depth + `tasks/backup/` 1-depth **2단** + 아카이브 플래그」 **단일 함수**로 두고 `scanner.py`·`routers/dashboard.py`·`routers/tasks.py` 3지점이 같은 함수를 호출한다. 어디에: `dashboard/backend/scanner.py`(`iter_task_dirs`·`resolve_task_dir` 신설) + 3지점 교체. 왜: 지금 파손 원인은 「같은 `tasks/`를 세는데 한쪽은 backup을 빼고 한쪽은 넣는다」이며, ANALYSIS 권고(backup 스킵 이식)는 동결 코호트 19/21건이 backup 아래라 오히려 실패를 고착시킨다(§배경 분석 (7)). **AC**: (a) 열거 함수가 1개이고 3지점이 그것만 호출한다 (b) `grep`으로 잔여 직접 `scandir`/`iterdir` 열거 0건 (c) 동결 코호트 21건이 관측 집합에 전건 포함된다 (d) 코호트 필터 중앙값이 재현된다 (e) 아카이브 구분이 필요한 지점(`tasks.py` archive 컬럼)의 기존 동작 무변경
- [ ] **R-7 FE 테스트 3파일 `@header` 정비** — 무엇을: `uncovered:incomplete` **차단** 위반 3건을 해소. 어디에: `dashboard/frontend/src/lib/api-timeout.test.ts` · `lib/utils.test.ts` · `pages/brain/brain-status.test.ts`. 왜: 허브가 이미 `exit 2`라 완료기준이 성립하지 않는다(§배경 분석 (6)). **AC**: (a) 3파일 `@header`가 `code-scan validate` 차단 판정을 통과한다 (b) **107 신설 규정 준수** — `description`에 서로 다른 태스크 번호 2개 이상 금지, `changelog` 등 이력 전용 필드 신설 금지 (c) 허브·워크트리 `validate` **exit 0** (d) `counts` 기존 키 값 회귀 0건
- [ ] **R-8 이동값 단언 규약 정렬** — 무엇을: 동결 baseline 값을 **필터 없이** 단정해 후속 태스크 완료로 중앙값이 이동하면 깨지는 회귀 단언 2건(`ts108`·`ts137`)을 코호트 필터 재계산으로 교정한다. 어디에: `dashboard/backend/tests/test_routers.py` — `test_t103_ts108_dashboard_three_series_is_additive`(`:1806`) · `test_t103_ts137_quiet_hours_surfaced_on_both_endpoints`(`:1844`). **초판은 `test_stats.py`로 오기했다**(2026-09-07 정정) — `test_stats.py:59`는 §범위 ④에서 **사실오류로 제외된 파일**이므로 그대로 두면 EXECUTE가 대상을 못 찾는다. 왜: 허브 9건 중 2건은 (A)와 무관한 **선재 실패**이며 열거 수정으로는 절대 풀리지 않는다(PLAN E1-1: `857 != 425`, `1127 != 799`). `STATS-BASELINE.md` §6.1의 기존 [MUST]를 위반한 단언이므로 규약 정렬로 교정한다. **AC**: (a) `ts108`·`ts137`이 코호트 필터 재계산으로 **425/799**를 단정하며 통과한다 (b) **단언 약화 금지** — 교정 후에도 동결값 단정이 남아 있고(값 단정 삭제 0건) additive 불변식·`quiet_hours` 계약 단정이 무조건 형태로 보존된다 (c) 코호트 데이터를 인위 변경하면 두 테스트가 **실패한다**(단언 유효성 역검증)

> **R-8은 PLAN 신설 요구사항의 번호 정정이다** (2026-09-07). PLAN이 이 요구사항을 「R-7로 신설」이라 적었으나(`PLAN.md:14`) **R-7은 §배경 분석 (6)에서 이미 FE 테스트 3파일 `@header` 정비에 배정된 번호였다** — 같은 ID가 서로 다른 두 요구사항을 가리키는 충돌 상태였다. PLAN 스스로 「TASK.md 요구사항 표 갱신이 필요하다 — 소유자 보고 대상」(`PLAN.md:93`)·리스크 R-11로 예고했으나 번호가 이미 점유된 사실은 포착하지 못했다. 이동값 단언 쪽을 **R-8**로 재배정해 충돌을 해소한다(R-7 = FE `@header` 정비 유지).

- [ ] **R-5 회귀 보존** — **AC**: (a) 허브 state-tool `0 failed` (b) 허브 console BE `0 failed` (c) 워크트리 양 스위트가 허브와 **동일** (d) code-scan 369 passed / 0 failed (e) 허브 실행 경로 회귀 0건

## 제약 조건

- **미설정 시 바이트 동일**: 허브 실행 경로가 달라지면 안 된다. 태스크 107의 `--worker-duration-minutes`가 「미지정 시 키 자체 미생성」으로 하위호환을 지킨 패턴을 준용한다.
- **배포 경계**: `~/.opal/` 배포본 직접 수정 금지. 소스 수정 후 install.
- **단언 약화 금지**: R-3의 하드코딩 제거가 검증 범위 축소로 흐르지 않게 한다.
- **워크트리 격리**: 코드 변경은 `feat/OP-TASK-109` 워크트리에서만.

## 기술 스택

- Python — `dashboard/backend/` (FastAPI), `opal/tools/{memory,state}-tool/`
- Node.js — `opal/tools/worktree-tool/`(래퍼는 Python), `code-scan`(회귀 대상)
- Markdown — `opal-harness.md` · `harness/task-process.md` · `pm/dispatch-process.md`

## 관련 문서

| # | 유형 | 문서 | 경로 | 참조 이유 |
|---|------|------|------|----------|
| D-1 | 하네스 | 워크스페이스 축 | `opal/core/references/opal-harness.md` §2.5 | 워크트리 계약 원문 — R-2 개정 대상 |
| D-2 | 하네스 | TASK 공통 프로세스 | `opal/core/references/harness/task-process.md` 4.5 | worktree 생성 절차 — R-2·R-4 |
| D-3 | PM | 디스패치 프로세스 | `opal/core/references/pm/dispatch-process.md` | §작업 경로 블록 — R-4 주입 지점 |
| D-4 | 설정 | worktree 선언 | `.opal/worktree.json` | sparse 패턴 원천 |
| D-5 | 산출물 | 태스크 107 | `tasks/107-260906-opd-헤더필드-작성기준-이력분리/DONE.md` §7 | 발원 — 하네스 발견 2번 |
| D-6 | brain | 회귀 단언 고정 | `.opal/brain/pages/concept/regression-pin-of-task-time-fact.md` | (A)(B)의 성질 진단 근거 |
| D-7 | 컨벤션 | 프로젝트 컨벤션 | `docs/CONVENTIONS.md` | §배포 경계 · §Guards |
