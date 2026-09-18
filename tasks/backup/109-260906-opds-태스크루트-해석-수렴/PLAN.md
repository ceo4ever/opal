# PLAN: 태스크 루트 해석 수렴 + 위치 불변 집계 경계

> 작성일: 2026-09-07 | 입력: TASK.md(개정본), ANALYSIS.md(정정본)
> 모드: Multi-Feature (기능 6개) | 실행 모드: **복잡**
> RED-first 트랙: **ON** (근거 §RED-first 판정)

## 결론

- **해석 규칙은 후처리 정규화 1함수다** — 기존 `project_root` 확정값(인자 또는 `cwd()`) 위에 「경로 세그먼트에 `.opal-worktrees`가 있으면 그 부모가 허브」를 씌우는 **순수 문자열 함수**로 두고, 제3의 입력(`__file__`)을 만들지 않는다 (→ ANALYSIS §8 「세그먼트 해석 함수의 위치」).
- **구현은 3개다(계약 1개)** — Python 2개(`dashboard/backend/paths.py` · `opal/tools/brain-tool/brain_tool.py`) + Node 1개(`opal/tools/code-scan/code-scan.js`). ANALYSIS §8의 「런타임별 2개」는 언어 경계를 세지 않은 계수이므로 **수정필요** 판정한다 — JS는 Python 함수를 import할 수 없다 (`opal/tools/code-scan/code-scan.js:331`).
- **조립 지점은 8곳이 아니라 9곳이다** — `brain_tool.py:239` `resolve_brain_path()`의 `p / ".opal" / "brain"`이 목록에서 빠져 있었고, 이 지점이 **워크트리에서 brain-tool 전 명령을 먼저 차단**한다(E1-6 실측: `brain_not_initialized`). 이 지점을 고치지 않으면 `brain_tool.py:869,1252`의 `cwd()` 2곳은 애초에 도달하지 않는다.
- **console BE 5건 처방은 ANALYSIS 권고안 (a)를 기각한다** — `backup` 스킵을 이식하면 TS-020·TS-021·TS-022가 **계속 실패**한다(동결 코호트 21건이 전부 `tasks/backup/` 아래에 있다). 채택안은 「`tasks/` 1-depth + `tasks/backup/` 1-depth **2단 열거** + 아카이브 플래그」 단일 열거 함수이며, 이 형태에서 3건 전건 통과가 실측 예측됐다(E1-2).
- **집계 파손의 성질은 「제외 규칙 누락」이 아니라 「모수가 위치에 의존한다」다** — 완료 태스크를 아카이브로 옮기면 통계 모수가 바뀌는 것이 결함이며, 본 태스크의 목표 진술(위치가 바뀌면 깨진다)과 같은 축이다. 열거 기준을 3지점이 **같은 함수**로 공유해 항등을 구조적으로 보장한다.
- **허브 9건 중 2건은 (A)와 무관한 선재 실패다 — 귀속을 실측 확정했다** — `ts108`·`ts137`은 동결 baseline 값(opd 425/799)을 **필터 없이** 단정해 후속 태스크 완료로 중앙값이 이동하며 깨진 것이다(E1-1: `857 != 425`, `1127 != 799`). 이는 `STATS-BASELINE.md` §6.1의 기존 [MUST]를 위반한 단언이므로 **R-8로 신설**해 규약 정렬로 교정한다(초판은 `R-7`로 적었으나 R-7은 FE `@header` 정비에 이미 배정된 번호였다 — 2026-09-07 정정) — 열거 수정으로는 절대 풀리지 않는다.
- **`code-scan validate` exit 0은 세그먼트 수정만으로 달성되지 않는다** — 허브 현재 exit 2이며 차단 3건이 FE 테스트 3파일의 `@header` `exports` 누락이다(E1-4). 이 3건 정비를 Step으로 포함한다.
- **`doctor.py`는 수렴 제외(ANALYSIS Q6 채택)** — 진단 도구가 「이 경로에 tasks/가 있는가」를 「허브에 tasks/가 있는가」로 바꾸면 워크트리 진단이 항상 통과로 보고돼 진단 가치가 소멸한다. 제외를 주석·테스트·문서 3중으로 고정한다.

---

## 확정 입력 판정

> TASK.md `## 확정된 설계 방향`의 `[결정]`·`[사실]` 전건 + ANALYSIS.md §8 승계 확정값을 3값 판정한다. 판정값 `유효`는 재설계 면제이며 검증 면제가 아니다(op-dev-plan SKILL.md §확정 입력 소비 규약).

| 항목 | 판정 | 근거 |
|------|------|------|
| [결정] 범위는 (A)+(B) 둘 다 | 유효 | - |
| [결정] 허브 루트 해석 규칙(`.opal-worktrees` 세그먼트 → 부모가 허브) | 유효 | - |
| [결정] `OPAL_TASKS_ROOT` 환경변수 신설 철회 | 유효 | - |
| [결정] `.opal/code-scan.json` 워크트리 복사 철회 | 유효 | - |
| [결정] 심볼릭 링크 미채택 | 유효 | - |
| [결정] 구현은 런타임별 2개, 계약은 1개 | **수정필요** | 계약 1개는 유효하나 구현 수가 2가 아니라 **3**이다 — `opal/tools/code-scan/code-scan.js:331` `findProjectRoot()`는 Node 런타임이며 Python 함수를 import할 수 없다. 「런타임별 1개」 원칙 자체는 그대로 유지되고, 런타임 계수만 Python 2 + Node 1로 정정한다 |
| [사실] 경로 조립 지점 8곳 | **수정필요** | **9곳**이다 — `opal/tools/brain-tool/brain_tool.py:234-239` `resolve_brain_path()`가 `<자기 루트>/.opal/brain`을 조립하며 8곳 목록에 없다. `--brain-path` 기본값이 `"."`(`brain_tool.py:1385,1401,1406,1416,1428,1435,1440`)이므로 워크트리 cwd에서 brain-tool 전 명령이 이 지점에서 먼저 차단된다 — E1-6 실측 |
| [사실] 테스트 하드코딩 4곳 | **수정필요** | 폴더명 하드코딩은 3곳(`test_stats.py:59` 제외 — ANALYSIS 사실오류 판정 승계)이고, **저장소 루트를 `__file__`에서 파생하는 지점 3곳**(`dashboard/backend/tests/test_routers.py:1007` · `test_parsers.py:19` · `test_adapters.py:85`)이 별도 축으로 실재한다. 후자가 워크트리 델타 24건의 직접 원인이다 — ANALYSIS §7 Q9는 프로덕션 코드에 `__file__` 파생이 없다는 사실만 확인했고 테스트 축은 판정하지 않았다 |
| [사실] 심볼릭 링크 시 1,022건 `D` | 유효 | - |
| [사실] sparse 패턴 7항목, `.opal` 없음 | 유효 | `.opal/worktree.json:2-11` 재확인 |
| [사실] 정규 워크트리에서 `code-scan validate` → `header_source_unset` | 유효(E1-5 재확인) | 실행: `cd /Volumes/.../.opal-worktrees/task_109 && ~/.opal/tools/code-scan/run.sh validate` → `{"ok":false,"error":"header_source_unset"}` |
| [사실] task_107의 `.opal`은 무단 sparse 추가 흔적 | 유효 | - |
| (ANALYSIS §8) 헬퍼 구조 = 런타임별 2개 | **수정필요** | 위 [결정] 행과 동일 근거 — Python 2 + Node 1 = 3 |
| (ANALYSIS §8) 세그먼트 해석은 기존 확정값 위의 후처리 | 유효 | - |
| (ANALYSIS §8) 다중 프로젝트 스캔 루프에서 no-op | 유효 | `dashboard/backend/routers/tasks.py:446-448` — `scan_projects(cfg.scan_roots, ...)` 결과만 순회 |
| (ANALYSIS §8) code-scan 설정 경로 vs 스캔 루트 분리하지 않음 | 유효 | - |
| (ANALYSIS §8) `test_stats.py:59`는 대상 제외 | 유효 | - |
| (ANALYSIS §8) S-31 완전 픽스처화 금지, 동적 탐색만 | 유효 | - |
| (ANALYSIS §8) console BE 5건 처방 = 권고안 (a) `backup` 스킵 이식 | **사실오류** | 권고안 (a)를 적용하면 동결 코호트 21건(`080`~`099`)이 집계에서 영구 배제돼 `test_routers.py:1435-1437`의 `set(cohort) <= observed_prefixes` 단정과 `:1405-1406`의 `completed_tasks >= 21`이 **계속 실패**한다. 코호트 21건은 전건 `tasks/backup/` 아래에 있다(E1-3: `tasks/backup/` 100폴더). 채택안은 §3 F-005 「2단 열거」이며 E1-2로 통과 예측을 실측했다. **소유자 보고 대상** |
| (ANALYSIS §8) 두 구현 동치 = 공유 골든 케이스 표 | 유효 | Q12 권고 (ii) 채택. 표 위치·스키마는 §3 F-002가 확정 |
| (ANALYSIS §8) `doctor.py` R-1 수렴 제외 권고 | 유효(재검토 후 채택) | 판단 근거는 §3 F-005.3 「doctor.py 제외 판정」 |
| (ANALYSIS §8) worktree-tool 응답 확장 지점 | **범위 밖** | TASK.md 개정본 §범위에 worktree-tool 응답 필드 추가가 없다(환경변수·복사·링크 철회로 소멸). 본 PLAN은 `worktree_tool.py`를 변경하지 않는다 |
| (ANALYSIS §8) `.opal` 워크트리 실재 전제 무효 | 유효 | - |

> **사실오류 보고 1건** — ANALYSIS §8 「console BE 5건 처방 = 권고안 (a)」. 확정 지위를 박탈하고 정상 설계 경로로 복귀했다(§3 F-005). 완료 보고에 함께 기재한다.

---

## PLAN 결정 5건 (ANALYSIS §8 「PLAN 결정 필요」 처분)

| # | 쟁점 | 결론 | 상세 |
|---|------|------|------|
| 1 | console BE 집계 의존 5건 처방 | **R-6 신설** + ANALYSIS 권고안 (a) **기각** → 「`tasks/` 1-depth + `tasks/backup/` 1-depth **2단 열거** + 아카이브 플래그」 단일 함수 채택. 실제로는 5건 중 3건만 열거 결함이고 2건은 선재 실패라 **R-8도 신설** | §3.5.2 (1) · §2.6 |
| 2 | S-31 동적 탐색 구현 방식 | `tasks/`·`tasks/backup/` **2글롭 접두사 검색**(1-depth, `rglob` 금지) + **정확히 1건 매칭 요구**, 0/2건은 `skipTest`가 아니라 실패. 단언·픽스처 무변경 | §3.4.2 (1) |
| 3 | `doctor.py` 최종 처리 | ANALYSIS Q6 **채택 — 수렴 제외**. 근거: 진단 문면이 「인자 경로의 리터럴 `tasks/` 상태」이며 허브 정규화 시 워크트리 진단이 영구 통과로 보고돼 자기 관측이 무력화(진단 도구가 진단 대상 해석에 의존하는 순환). 주석·테스트·문서 3중 고정 | §3.5.2 (3) |
| 4 | 정규화 함수 시그니처·배치 | `hub_root(path) -> str` / `hubRootFromPath(p) -> string` — **순수 문자열 함수**(FS·env·cwd 미접근), 세그먼트 **첫 출현** 기준, 항등 반환. 배치 = `dashboard/backend/paths.py`(신규) · `brain_tool.py` 모듈 레벨 · `code-scan.js`. 적용 지점 = brain-tool **3곳**(`resolve_brain_path` 포함) · code-scan 1곳 · 테스트 루트 3곳. 인자 기반 6곳은 무변경 | §3.2.2 · §3.3.2 (2) · §3.4.2 (2) |
| 5 | `findProjectRoot()` 개정 방식 | **최상위 진입점 정규화** — 첫 줄 `let dir = hubRootFromPath(process.cwd())`. 삽입점 1곳 · 세그먼트 부재 시 본문이 현행과 동일 경로를 타므로 바이트 동일이 구조적으로 보장 · 정규화 전 상태 공간 단일 | §3.3.2 (1) |

---

## AC 해석 고정

> 재해석 여지가 있는 AC 2건의 판정 기준을 못박는다. 근거 없는 확대 해석이 EXECUTE에서 과잉 변경을 부르는 것을 막는다.

- **[MUST] R-3 AC(a) 「`grep`으로 잔여 직접 조립 0건」의 대상은 「`cwd()`·`__file__` 파생 조립」이다.** 인자로 이미 허브 절대경로를 받는 6곳(`tasks.py:457,520,654` · `scanner.py:29` · `dashboard.py:50` · `memory_tool.py:675`)은 값이 이미 허브이므로 무변경이며 grep 잔여로 세지 않는다. 근거: ANALYSIS §8 「인자 기반 6곳은 값이 이미 허브라 무변경」 + `dashboard/backend/routers/tasks.py:446-448`(값 원천이 `scan_roots`) + `opal/tools/memory-tool/memory_tool.py:1522`(`--file` `required=True`).
- **[MUST] R-5 AC(c) 「워크트리 양 스위트가 허브와 동일」의 판정은 passed/failed/**skipped** 3수치 전부다.** 현재 워크트리 console BE는 `3 skipped`, 허브는 `1 skipped`이며 델타 2건은 `tasks/`·`.opal/` 부재로 인한 조건부 skip이다(`dashboard/backend/tests/test_adapters.py:88` · `test_parsers.py:150,163,217`). 검증은 양쪽 `-rs` 실행 후 skip 사유 목록 대조로 한다.
- **[MUST] 허브 코드의 `0 failed`는 머지 후 CLOSE에서 확인한다.** 코드 변경은 워크트리 한정이므로(TASK.md §제약 조건 「워크트리 격리」) EXECUTE/TEST 구간에 허브 소스는 변하지 않는다. 정규화 적용 후 워크트리 실행과 허브 실행은 **데이터 원천이 동일(허브)**해지므로 두 실행은 구성상 등가이며, 이 등가가 R-5 AC(c)의 설계 보장이다.

---

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

하네스 §2.5는 태스크 문서(`tasks/`)·`.opal/`을 허브에 고정하고 워크트리가 그것을 **참조**한다고 규정하나, 참조를 구현한 코드가 없다. 「자기 경로에 `.opal-worktrees` 세그먼트가 있으면 그 부모가 허브」 규칙을 SSOT로 명문화하고, `cwd()`·`__file__` 파생 조립 지점을 그 함수로 수렴시켜 **워크트리·허브 양쪽에서 같은 데이터를 보게** 한다. 별개 축으로 ① 태스크 열거 기준을 위치 불변으로 단일화하고 ② 실 폴더명·이동값에 고정된 회귀 단언을 위치·시점 내성으로 교정해 **양쪽 0 failed**를 만든다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | 허브 루트 해석 규칙 SSOT 명문화 | R-1 | P0 | 없음 |
| F-002 | 런타임별 해석 함수 3구현 + 동치 골든 표 | R-2 | P0 | F-001(규칙 원문) |
| F-003 | `cwd()` 파생 조립 수렴 (brain-tool · code-scan) + FE `@header` 정비 | R-3, **R-7** | P0 | F-002 |
| F-004 | 테스트 위치 내성 — 실 폴더명·저장소 루트 파생 | R-4 | P0 | F-002 |
| F-005 | 태스크 열거·주소 경계 위치 불변화 | **R-6(신설)** | P0 | 없음 |
| F-006 | 이동값 단언 규약 정렬 | **R-8(신설)** | P1 | F-005 |

> **R-6·R-8은 PLAN 신설 요구사항이다.** R-6은 TASK.md R-4 AC(d)(「집계 의존 5건은 별도 처방을 PLAN이 설계한다」)의 위임을 받아 신설했고, R-8은 그 5건 중 2건이 (A)와 무관한 선재 실패임을 실측 귀속한 결과 신설했다(E1-1 — 초판 `R-7`은 FE `@header` 정비와 번호 충돌이라 2026-09-07 R-8로 정정). TASK.md R-7(FE `@header` 정비)은 Step 12가 담당하므로 F-003에 편입했다. R-5(회귀 보존)는 전 기능 공통 완료 게이트로 §5.2·Step 13에서 집행한다. **TASK.md §요구사항 표 갱신 완료(2026-09-07) — R-8 신설 + R-7 = FE `@header` 정비 확정.**

### 1.3 기능 의존 그래프

```
F-001 ── F-002 ──┬── F-003 ── (code-scan validate exit 0)
                 └── F-004 ──┐
                             ├── R-5 완료 게이트 (Step 13)
F-005 ─────────── F-006 ─────┘
```

F-005·F-006은 F-001~F-004와 **파일 교집합이 없다**(단, `test_routers.py` 1파일만 공유 — Step 3에 집약). 따라서 Phase 1 내에서 병렬 가능하다.

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 된다.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | `hub_root()` 3구현 | 세 구현이 같은 입력에 다른 답 → 런타임 간 데이터 원천 분기 | P0 | L1(3스위트 골든 표) | S-후보-1 |
| H-2 | `findProjectRoot()` 진입점 정규화 | 허브 실행 시 반환값이 달라지면 code-scan 전 명령의 출력 바이트가 이동 | P0 | L1(항등 케이스) + L2(허브 CLI 출력 대조) | S-후보-2 |
| H-3 | `resolve_brain_path()` 정규화 | `--brain-path`를 **명시**한 호출이 허브로 강제 리다이렉트되면 격리 테스트(`tmp_path`)가 오염된다 | P0 | L1(명시 인자 불변 단정) + L2(brain-tool 142건 회귀) | S-후보-3 |
| H-4 | 2단 열거 함수 | `tasks/backup/` 포함으로 모수가 늘어 `total_tasks`·`workflow_stats`·`artifact_total`이 이동 | P1 | L2(항등·하한 단정 3건) | S-후보-4 |
| H-5 | detail·artifact의 backup 폴백 | 경로 조립 지점 증가 → `task_id` 경로 이탈(`../`) 노출 | P0(보안) | L1(이탈 입력 거부) + L2(아카이브 카드 200) | S-후보-5 |
| H-6 | S-31 동적 탐색 | 탐색이 0건·2건 이상을 만나면 조용히 skip/오대상 검증으로 강등 | P1 | L1(정확히 1건 매칭 단정) | S-후보-6 |
| H-7 | `_T103_ROOT` 등 테스트 루트 정규화 | 소스 트리 참조(`test_config.py:352,371`)까지 정규화하면 **브랜치 소스가 아니라 허브 소스**를 검증하게 되어 단언 의미가 뒤집힌다 | P0 | L1(정규화 대상 화이트리스트) | S-후보-7 |
| H-8 | ts108·ts137 단언 교정 | 값 단정 → 규약 단정 전환이 **단언 약화**로 흐를 수 있다(reward hacking 외형) | P0 | L1(코호트 필터 재계산으로 동결값 425/799 유지) | S-후보-8 |
| H-9 | 워크트리 code-scan이 허브를 스캔 | 워커가 「내 변경이 검증됐다」고 오해 — 실제로는 허브 트리를 검증 | P1 | L3(문서 명시) | S-후보-9 |
| H-10 | 신규 파일 3종(`paths.py`·테스트 2종) | HEAD 부재 파일은 `@header` 없으면 `newly_uncovered`로 **차단 승격**된다 | P1 | L2(`code-scan validate` 차단 건수 불변) | S-후보-10 |
| H-11 | 선재 실패 2건 귀속 | 귀속이 틀리면 잔여 실패가 남아 R-5 AC(b) 미달 | P1 | L2(9건 개별 실행 대조) | S-후보-11 |

---

## 2. 기능별 분석

### F-001: 허브 루트 해석 규칙 SSOT 명문화

#### 2.1.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | `opal/core/references/opal-harness.md` | §2.5 워크스페이스 축 — 워크트리 경로 계약 원문 | 수정 |
| 문서 | `opal/core/references/harness/task-process.md` | 4.5 worktree 생성 절차 | 수정(포인터) |

#### 2.1.2 현재 구현
§2.5 (3)의 경로 계약 문장이 「태스크 문서(`tasks/`)·`.opal/MEMORY.json`·`.opal/brain/`은 분기하지 않고 허브에 고정한다」까지만 규정하고, **워크트리가 허브를 어떻게 찾는가**를 규정하지 않는다(`opal/core/references/opal-harness.md:168`). 규칙 부재가 구현 부재의 원인이다.

#### 2.1.3 영향 범위
- 하류 소비자: F-002 3구현의 포인터 주석, F-003·F-004의 판정 근거, `docs/CONVENTIONS.md`(새 규칙 도입 → Step 14).
- `~/.opal/` 배포본은 install 시 갱신된다 — [MUST] `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `scripts/`)에서 수행한다."

---

### F-002: 런타임별 해석 함수 3구현 + 동치 골든 표

#### 2.2.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `dashboard/backend/paths.py` | 허브 루트 해석 — console BE 런타임 SSOT 구현 | 신규 |
| 환경 | `opal/tools/brain-tool/brain_tool.py` | 허브 루트 해석 — opal/tools Python 런타임 구현 | 수정 |
| 환경 | `opal/tools/code-scan/code-scan.js` | 허브 루트 해석 — Node 런타임 구현 | 수정 |
| 공통 | `opal/core/references/hub-root-cases.json` | 3스위트 공유 골든 케이스 표 | 신규 |
| 환경 | `dashboard/backend/tests/test_paths.py` | dashboard 구현 동치 검증 | 신규 |
| 환경 | `opal/tools/brain-tool/tests/test_brain_tool.py` | brain-tool 구현 동치 검증 | 수정 |
| 환경 | `opal/tools/code-scan/tests/test-hub-root.js` | Node 구현 동치 + 워크트리 CLI 블랙박스 | 신규 |

#### 2.2.2 현재 구현
- `dashboard/backend`는 `opal/tools/*`를 import하지 않는다 — `opal/tools/*`에 `__init__.py`가 없고 console BE는 서브프로세스로만 호출한다(`dashboard/backend/adapters/state_adapter.py:19-20`). 공용 모듈을 놓을 자리가 없다(ANALYSIS §7 Q1 승계).
- `opal/tools/` 안에서도 크로스 툴 import 선례가 없다 — `sys.path` 조작은 자기 디렉터리 삽입 2건뿐(`opal/tools/test-tool/test_tool.py:35` · `opal/tools/tool-scan/tool_scan.py:36`).
- 이미 허브로 수렴하는 선례가 1건 있다 — `opal/tools/state-tool/state_tool.py:700-708` `find_project_root(task_path)`가 `.opal/MEMORY.json` 보유 조상까지 상향 탐색한다. 워크트리엔 `.opal`이 없으므로 이 함수는 **세그먼트 규칙과 무관하게** 허브를 반환하며, 이것이 state-tool 워크트리 델타가 0인 이유다(TASK.md §배경 분석 (3)).

#### 2.2.3 영향 범위
- 세 구현의 소비자: F-003(brain-tool 3지점 · code-scan 1지점), F-004(테스트 루트 3지점).
- `state_tool.find_project_root()`는 **다른 규칙**(마커 상향 탐색)으로 같은 답을 낸다 — 우연 일치가 갈라지지 않도록 골든 표에 대조 케이스 1건을 둔다(H-1).

---

### F-003: `cwd()` 파생 조립 수렴 (brain-tool · code-scan)

#### 2.3.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 환경 | `opal/tools/brain-tool/brain_tool.py` | `resolve_brain_path`(`:234-239`) · `_load_code_scan_json`(`:869`) · `cmd_ingest_scan`(`:1252`) | 수정 |
| 환경 | `opal/tools/code-scan/code-scan.js` | `findProjectRoot()`(`:331-341`) | 수정 |
| FE | `dashboard/frontend/src/lib/api-timeout.test.ts` | `@header` `exports` 누락 — validate 차단 1건 | 수정 |
| FE | `dashboard/frontend/src/lib/utils.test.ts` | 동일 | 수정 |
| FE | `dashboard/frontend/src/pages/brain/brain-status.test.ts` | 동일 | 수정 |

#### 2.3.2 현재 구현
- `findProjectRoot()`는 `process.cwd()`에서 상향 탐색하며 `.git`·`.opal`·`CLAUDE.md` **어느 하나라도** 만나면 즉시 반환한다(`opal/tools/code-scan/code-scan.js:331-341`). 워크트리 루트에는 `.git`이 **78바이트 파일**로, `CLAUDE.md`가 **0바이트 파일**로 실재하므로(실측: `ls -la .opal-worktrees/task_109`) 워크트리 자신이 projectRoot로 확정되고 `<worktree>/.opal/code-scan.json` 부재 → `header_source_unset`이 된다(E1-5).
- `resolve_brain_path()`는 `--brain-path` 기본값 `"."`을 resolve해 `<cwd>/.opal/brain`을 만든다(`opal/tools/brain-tool/brain_tool.py:234-239` + `:1385`). 워크트리에서 brain-tool은 **전 명령이 이 지점에서 차단**된다(E1-6).
- 설정 경로와 스캔 루트는 단일 `projectRoot` 변수를 공유한다(`code-scan.js:377-378`·`962-991`·`1277-1280`) — 분리하지 않는다(ANALYSIS §8 승계).

#### 2.3.3 영향 범위
- `code-scan.js` 정규화 후 워크트리 실행은 **허브 트리를 스캔**한다. `.opal/code-scan.json`의 `exclude`에 `.opal-worktrees`가 이미 있어(`.opal/code-scan.json:9-10`) 허브 스캔이 워크트리로 내려가지 않는다 — 무한·중복 스캔 위험 없음.
- 파급: 워크트리에서 실행한 `validate`는 **미머지 변경을 보지 않는다**(H-9). 이 의미 한계를 F-001 문서에 명시한다.
- `brain_tool._load_code_scan_json`은 배포본 `~/.opal/tools/code-scan/code-scan.js`를 우선 실행하고 부재 시 `cwd/opal/tools/...`로 폴백한다(`brain_tool.py:874-879`) — 정규화 후 폴백 경로가 허브 소스를 가리킨다. 배포본이 갱신되기 전까지 sync-header 경로는 구 동작이다(§9 리스크 R-5).

---

### F-004: 테스트 위치 내성 — 실 폴더명·저장소 루트 파생

#### 2.4.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 환경 | `opal/tools/state-tool/tests/test_state_tool.py` | S-31 — 098 TASK.md 실파일 직접 참조(`:4573`) | 수정 |
| 환경 | `dashboard/backend/tests/test_routers.py` | `_T103_ROOT`(`:1007`) · `_T103_TASK_089/091`(`:1010-1011`) | 수정 |
| 환경 | `dashboard/backend/tests/test_parsers.py` | `AI_FRAMEWORK_ROOT`(`:19`) → `.opal/MEMORY.md`·`.opal/AGENT.md` 참조(`:20-23`) | 수정 |
| 환경 | `dashboard/backend/tests/test_adapters.py` | `Path(__file__).parents[3] / "tasks" / "021-..."`(`:84-86`) | 수정 |
| 환경 | `dashboard/backend/tests/test_config.py` | `repo_root`(`:352,371`) — **소스 트리 참조, 정규화 제외** | 무변경 |
| 환경 | `dashboard/backend/tests/test_deploy_smoke.py` | `_repo_root`(`:42`) — 배포 소스 참조, 정규화 제외 | 무변경 |

#### 2.4.2 현재 구현
- `_T103_ROOT = str(Path(__file__).resolve().parents[3])`(`test_routers.py:1007`)가 저장소 루트를 파생하고, 이 값이 `/api/*?project=` 쿼리(`:1051,1057`)와 **테스트 측 직접 파일 읽기**(`:1064` `os.path.join(_T103_ROOT, "tasks", task_id, "state.json")`) 양쪽에 쓰인다.
- 따라서 프로덕션 라우터만 정규화해도 워크트리 실패는 해소되지 않는다 — 테스트가 스스로 파일을 여는 경로가 남는다. **테스트 루트 정규화가 필수 경로다.**
- S-31은 `ST.find_project_root(str(_TOOL_DIR))`로 저장소 루트를 얻은 뒤 `repo_root / "tasks" / "098-260821-..." / "TASK.md"`를 조립한다(`test_state_tool.py:4569-4575`). 루트 해석은 이미 허브로 수렴하고, **폴더명 하드코딩만** 남은 실패 원인이다.
- 자기 docstring이 「`tmp_path` 합성 픽스처(S-7)로 대신할 수 없는 목표달성 검증」이라 선언한다(`test_state_tool.py:4562-4565`).

#### 2.4.3 영향 범위
- 정규화 대상은 **허브 고정 데이터(`tasks/`·`.opal/`) 참조**뿐이다. 소스 트리 내용을 단정하는 지점(`test_config.py:352` `opal/core/setting.default.json`, `:371` `scripts/install-mac.sh`)은 브랜치 자신을 봐야 하므로 정규화하면 단언 의미가 뒤집힌다(H-7).
- 워크트리 skip 델타 2건의 원천이 이 축이다(`test_adapters.py:88` · `test_parsers.py:150,163,217`).

---

### F-005: 태스크 열거·주소 경계 위치 불변화 (R-6 신설)

#### 2.5.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `dashboard/backend/scanner.py` | `_count_tasks`(`:26-36`) 1-depth 카운트 + 열거 SSOT 신설 위치 | 수정 |
| BE | `dashboard/backend/routers/dashboard.py` | `_collect_all_tasks`(`:46-65`) 1-depth 순회 | 수정 |
| BE | `dashboard/backend/routers/tasks.py` | 목록 열거(`:455-491`) · detail `task_dir`(`:520`) · artifact `task_dir`(`:654`) | 수정 |
| BE | `dashboard/backend/routers/doctor.py` | `tasks_dir = p / "tasks"`(`:85-90`) — **제외 판정** | 무변경(주석만) |

#### 2.5.2 현재 구현 — 세 지점이 같은 `tasks/`를 다른 기준으로 센다
| 지점 | 현재 기준 | `tasks/backup/` 처리 |
|------|----------|--------------------|
| `tasks.py` 목록(`:455-491`) | 1-depth + `backup` 이름 스킵(`:463-464`) 후 **`backup/` 하위를 archive 컬럼 카드로 별도 열거**(`:473-491`) | **포함**(archive 컬럼) |
| `scanner.py:_count_tasks`(`:29-36`) | 1-depth `os.scandir` 디렉터리 수 | `backup` 폴더 자체를 **태스크 1건으로 오계수**, 하위 100건은 미계수 |
| `dashboard.py:_collect_all_tasks`(`:46-65`) | 1-depth + `state.json` 보유 필터 | `backup/state.json` 부재로 탈락 → 하위 100건 **전량 유실** |

- E1-3 실측: `tasks/` 1-depth 12개(= `backup` 1 + 실태스크 11) · `tasks/backup/` **100개**.
- `/api/tasks/detail`은 `os.path.join(project_path, "tasks", task_id)`만 시도한다(`tasks.py:520`) — 목록이 archive 카드로 내보낸 `task_id`(`:481`)를 **상세에서 열 수 없다**(404). 아카이브 카드 클릭이 항상 404가 되는 실제 제품 결함이며, `ts015`·`ts017[089]`·`owner_term` 3건이 이 404를 관측하고 있다(E1-1: `assert 404 == 200`).

#### 2.5.3 영향 범위
- 모수 이동: `total_tasks` 107 · `completed_tasks` 98 · `artifact_total` 773으로 늘어난다(E1-2). 관련 단정은 전부 항등·하한 형식이라 통과한다(`test_routers.py:1405-1410,1467-1470`).
- `ProjectInfo.task_count` 소비자는 프로젝트 카드 표시와 타입 단정뿐이다(`dashboard/backend/models.py:186` · `test_routers.py:196-198`). 합성 픽스처 단정(`test_scanner.py:79-80`)은 `backup` 없는 픽스처라 2단 열거에서도 값이 불변이다.
- 캐시 키는 무변경 — 모수만 바뀐다(`tasks.py:450` `tasks_list:{project}`).

---

### F-006: 이동값 단언 규약 정렬 (R-8 신설)

#### 2.6.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 환경 | `dashboard/backend/tests/test_routers.py` | `ts108`(`:1826-1832`) · `ts137`(`:1885-1890`) 무조건 값 단정 | 수정 |

#### 2.6.2 현재 구현
- `ts021`은 이동값 규약을 지킨다 — 동결 코호트 ID로 필터한 뒤 재계산해 값을 단정하고, 코호트가 완료 전량과 일치할 때만 API 직접값을 단정한다(`test_routers.py:1435-1452`). 근거로 [MUST] `STATS-BASELINE.md` §6.1을 자기 docstring에 인용한다(`:1418-1421`).
- `ts108`(`:1830-1831`)·`ts137`(`:1888-1890`)은 같은 baseline 값을 **필터 없이** API 직접값에 단정한다 → 후속 태스크가 완료될 때마다 중앙값이 이동해 깨진다.
- E1-1 실측: `ts108` `assert 857 == 425`, `ts137` `assert 1127 == 799`. 두 실패는 `tasks/backup/` 이관과 무관하다 — 2단 열거를 적용해도 모수가 21건이 아니라 98건이므로 API 직접값은 425/799로 돌아오지 않는다(E1-2: 전량 기준 opd 중앙값 253·보정끔 314).

#### 2.6.3 영향 범위
- 이 2건이 TASK.md §배경 분석 (3)이 말한 「이관 전 2건」의 정체다. 9 = 7(위치 유래) + 2(시점 유래)로 귀속이 닫힌다.
- 성질은 태스크 107이 brain에 등재한 「태스크 시점 사실을 영구 회귀 단언으로 고정하면 후속이 구조적으로 걸린다」의 재발이다(`.opal/brain/pages/concept/regression-pin-of-task-time-fact.md`, E5 — 1차 근거는 `tasks/107-260906-opd-헤더필드-작성기준-이력분리/DONE.md`).

---

## 3. 기능별 설계

### F-001: 허브 루트 해석 규칙 SSOT 명문화

#### 3.1.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/opal-harness.md` | 문서 | §2.5에 `(4) 허브 루트 해석 규칙` 신설 + 「## 변경이력」 행 추가 | `opal/core/references/opal-harness.md:168` |
| 2 | `opal/core/references/harness/task-process.md` | 문서 | 4.5에 §2.5 (4) 포인터 1줄 추가 + 변경이력 행 | (→ D-2 §4.5) |

#### 3.1.2 규칙 원문 설계 (§2.5 (4)에 신설)

규칙 본문에 아래 5항을 담는다. 원문은 F-001이 소유하고 구현은 포인터 주석만 둔다(R-2 AC(c)).

1. **정의** — 경로 문자열의 **세그먼트 목록**에 `.opal-worktrees`가 있으면 그 세그먼트의 **부모 경로**가 허브 루트다. 없으면 입력 경로가 그대로 프로젝트 루트다.
2. **깊이 무관** — 판정은 세그먼트 이름 완전 일치이며 경로 깊이·레이아웃(monorepo/multi-repo)과 무관하다. 근거: `.opal-worktrees/.meta/task_109.json`의 `worktree_root`와 `entries[].repo`가 세그먼트 부모 관계로 일치한다.
3. **허브 항등** — 허브에서 실행하면 세그먼트가 없으므로 함수는 입력을 그대로 반환한다. [MUST] 허브 실행 경로의 동작·출력은 바이트 동일해야 한다(TASK.md §제약 ①).
4. **적용 대상 경계** — 정규화는 **허브 고정 데이터**(`tasks/`, `.opal/`) 참조에만 적용한다. **소스 트리 내용**을 다루는 경로(브랜치 소스 검증·빌드·배포 대상)에는 적용하지 않는다 — 적용하면 워크트리가 자기 변경 대신 허브 소스를 보게 되어 의미가 뒤집힌다.
5. **의미 한계 명시** — 워크트리에서 실행한 `code-scan`은 설정도 스캔 대상도 허브 기준이므로 **미머지 변경을 검증하지 않는다**. 워크트리 변경의 `@header` 검증은 머지 후 허브에서 성립한다(H-9).

- 다중 출현 시 **첫 번째** 출현을 기준으로 한다(중첩 워크트리에서도 진짜 허브를 반환).
- 유사 이름(`.opal-worktrees-old` 등)은 **비매칭**이다(세그먼트 완전 일치).
- [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 「## 변경이력」 표에 행을 추가한다. 일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함 — 예: `(138)`."

#### 3.1.3 환경 변경
해당 없음.

#### 3.1.4 배치/마이그레이션
해당 없음 — install 재배포는 CLOSE 단계 판단(§9 R-5).

#### 3.1.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 AC(a) | 산출물 검사 | 규칙 정의가 `opal-harness.md` §2.5 (4) **한 곳**에만 존재하고 다른 문서·코드에 원문 중복이 없다 |
| TS-002 | R-1 AC(b) | 산출물 검사 | 깊이 무관·세그먼트 완전 일치·monorepo/multi-repo 성립이 명시된다 |
| TS-003 | R-1 AC(c) | 산출물 검사 | 허브 실행 시 입력 그대로 반환(항등)이 명시된다 |
| TS-004 | R-1 AC(d) | 산출물 검사 | §2.5 (3) 「허브에 고정」 문장과 모순 없고 (4)가 그 참조 방법을 규정한다 |
| TS-005 | R-1 / CONVENTIONS | 산출물 검사 | 두 문서에 변경이력 행이 추가되고 태스크 번호 `(109)`를 포함한다 |

---

### F-002: 런타임별 해석 함수 3구현 + 동치 골든 표

#### 3.2.1 파일 변경 계획

**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `dashboard/backend/paths.py` | BE | console BE 런타임의 허브 루트 해석 SSOT | `dashboard/backend/adapters/state_adapter.py:19-20` |
| 2 | `opal/core/references/hub-root-cases.json` | 공통 | 3스위트 공유 골든 케이스 표 | 선례: `opal/core/references/opal-skills-registry.json` |
| 3 | `dashboard/backend/tests/test_paths.py` | 환경 | dashboard 구현 골든 표 대조 | (→ D-8 §Q12) |
| 4 | `opal/tools/code-scan/tests/test-hub-root.js` | 환경 | Node 구현 골든 표 대조 + 워크트리 CLI 블랙박스 | `opal/tools/code-scan/tests/test-header-source.js:1-30` |

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 5 | `opal/tools/brain-tool/brain_tool.py` | 환경 | 모듈 레벨 `hub_root()` 신설(+ 포인터 주석) | `brain_tool.py:869,1252` |
| 6 | `opal/tools/code-scan/code-scan.js` | 환경 | `hubRootFromPath()` 신설 + `module.exports` additive 노출 | `code-scan.js:3707-3717` |
| 7 | `opal/tools/brain-tool/tests/test_brain_tool.py` | 환경 | 골든 표 대조 케이스 추가 | `test_brain_tool.py:38-40` |

#### 3.2.2 함수 계약 설계

**[MUST] 세 구현은 같은 계약을 만족한다** — 규칙 원문은 F-001 소유, 아래는 시그니처 계약이다 (→ F-001 §3.1.2).

Python (2구현 공통 시그니처):
```
hub_root(path: str | os.PathLike[str]) -> str
```
- **순수 함수** — 파일시스템·환경변수·`cwd()`를 읽지 않는다. 입력 문자열의 세그먼트만 본다. 근거: FS 접근이 없으면 「허브에서 항등」이 상태와 무관하게 성립하고(H-2), 합성 경로로 multi-repo 깊이를 테스트할 수 있다.
- 반환은 **`str`** — 3구현이 같은 타입으로 비교돼야 골든 표 대조가 문자열 동일성으로 성립한다. 후행 구분자 없음, 대소문자·심링크 정규화 없음(워크트리는 심링크가 아님 — ANALYSIS §확정 입력 판정 `realpath` 확인).
- 판정: `parts = PurePath(path).parts` → `".opal-worktrees"`의 **첫 인덱스** `i` → `str(PurePath(*parts[:i]))`. 없으면 입력을 `str()`로 그대로 반환.
- **상대경로는 정규화하지 않는다** — 호출자가 절대경로를 넘길 책임을 진다. 현 소비 지점 전건이 절대경로다(`pathlib.Path.cwd()` · `Path(__file__).resolve()` · `--file` required 절대경로).
- 배치: `dashboard/backend/paths.py`(신규 모듈, `@header` `module: paths` / `layer: config` / `domain: console` / `exports: ["hub_root"]` / `depends: []`) · `opal/tools/brain-tool/brain_tool.py`(모듈 레벨, `resolve_brain_path` 직전).

Node (1구현):
```
hubRootFromPath(p: string) -> string
```
- 동일 계약. `p.split(path.sep)` → 첫 인덱스 → `slice(0,i).join(path.sep)`. `module.exports`에 additive 추가(`code-scan.js:3707`) — 기존 7키 계약 보존, `code-map-hook.js` 소비 계약 무변경.

#### 3.2.3 골든 케이스 표 설계 (`opal/core/references/hub-root-cases.json`)

스키마: `{ "version": 1, "rule": "opal/core/references/opal-harness.md §2.5 (4)", "cases": [{ "id", "desc", "input_rel", "expected_rel" }] }`
경로는 **상대 형태**로 적어 각 스위트가 임의의 절대 프리픽스를 붙여 대조한다(합성 경로 — FS 생성 불필요).

| id | desc | input_rel | expected_rel |
|----|------|-----------|--------------|
| C-1 | 워크트리 루트 | `hub/.opal-worktrees/task_109` | `hub` |
| C-2 | 워크트리 하위 깊은 경로 | `hub/.opal-worktrees/task_109/opal/tools/brain-tool` | `hub` |
| C-3 | 허브 경로 — 항등 | `hub/opal/tools` | `hub/opal/tools` |
| C-4 | multi-repo 깊이 | `org/repos/hub/.opal-worktrees/task_007/dashboard/backend` | `org/repos/hub` |
| C-5 | 중첩 워크트리 — 첫 출현 기준 | `hub/.opal-worktrees/task_1/.opal-worktrees/task_2` | `hub` |
| C-6 | 유사 이름 비매칭 | `hub/.opal-worktrees-old/task_1` | `hub/.opal-worktrees-old/task_1` |
| C-7 | 세그먼트가 최상위 직하 | `.opal-worktrees/task_1` (절대 프리픽스 직하) | 프리픽스 자신 |

- **[MUST] 3스위트는 이 파일을 각자 읽는다** — 표를 복제하지 않는다. 표가 SSOT이고 대조 코드가 3개다(ANALYSIS §7 Q12 권고 (ii)).
- 대조 케이스 1건 추가: `state_tool.find_project_root(<worktree>/opal/tools/state-tool)`이 허브를 반환하는지 단정한다(다른 규칙의 우연 일치를 고정 — H-1).

#### 3.2.4 환경 변경
해당 없음 — 신규 패키지 없음. `dashboard/backend/paths.py`는 표준 라이브러리(`pathlib`, `os`)만 쓴다.

#### 3.2.5 배치/마이그레이션
해당 없음.

#### 3.2.6 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-010 | R-2 AC(a) | 산출물 검사 | 런타임별 구현이 1개씩 — `grep`으로 Python 2파일·JS 1파일에만 규칙 구현이 존재 |
| TS-011 | R-2 AC(b) | 기능 테스트 | 3스위트가 `hub-root-cases.json`의 C-1~C-7 전건에서 동일 문자열을 반환 |
| TS-012 | R-2 AC(b) | 기능 테스트 | C-3·C-6(항등 케이스)에서 입력과 반환이 **바이트 동일** |
| TS-013 | R-2 AC(c) | 산출물 검사 | 3구현 주석이 규칙 원문을 재서술하지 않고 §2.5 (4) 포인터만 둔다 |
| TS-014 | R-2 / H-1 | 기능 테스트 | `state_tool.find_project_root(<worktree 하위>)`가 허브를 반환(규칙 간 정합) |
| TS-015 | R-2 / H-10 | 회귀 테스트 | 신규 3파일이 `@header`를 보유해 `code-scan validate` 차단 건수가 늘지 않는다 |

---

### F-003: `cwd()` 파생 조립 수렴 (brain-tool · code-scan)

#### 3.3.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/brain-tool/brain_tool.py` | 환경 | `resolve_brain_path`·`_load_code_scan_json`·`cmd_ingest_scan` 3지점 정규화 | `brain_tool.py:234-239,869,1252` |
| 2 | `opal/tools/code-scan/code-scan.js` | 환경 | `findProjectRoot()` **진입점** 정규화 | `code-scan.js:331-341` |
| 3 | `dashboard/frontend/src/lib/api-timeout.test.ts` | FE | `@header`에 `exports` 필드 추가 | E1-4 |
| 4 | `dashboard/frontend/src/lib/utils.test.ts` | FE | 동일 | E1-4 |
| 5 | `dashboard/frontend/src/pages/brain/brain-status.test.ts` | FE | 동일 | E1-4 |

#### 3.3.2 설계 결정

**(1) `findProjectRoot()` — 최상위 진입점 정규화를 채택한다** (PLAN 결정 5)

```
function findProjectRoot() {
  let dir = hubRootFromPath(process.cwd());   // ← 유일한 삽입점
  ... 이하 현행 상향 탐색 본문 그대로 ...
}
```
채택 근거 3건:
- **삽입점 1곳** — 「발견 직후 정규화」안은 `return dir`·`return process.cwd()` 2곳을 손대야 한다(`code-scan.js:337,341`).
- **바이트 동일이 구조적으로 보장된다** — 입력에 세그먼트가 없으면 `hubRootFromPath`가 항등이므로 함수 본문이 현행과 **같은 값으로 같은 경로**를 탄다. 세그먼트 검사가 FS 상태와 독립이다(H-2).
- **정규화 전 상태 공간이 하나다** — 「발견 직후」안은 워크트리 내부 마커(`.git` 파일·`CLAUDE.md` 0바이트·하위 `docs/`)가 어디서 탐색을 멈추느냐에 따라 정규화 입력이 케이스마다 달라진다.

허브에서는 세그먼트가 없어 `.opal/code-scan.json`을 그대로 읽고, 워크트리에서는 허브 설정·허브 스코프를 읽어 `header_source_unset`이 소거된다(R-3 AC(d)).

**(2) brain-tool 3지점** (PLAN 결정 4)

| 지점 | 현행 | 변경 |
|------|------|------|
| `resolve_brain_path`(`:234`) | `p = Path(brain_path_str).resolve()` | **인자가 기본값 `"."`인 경우에만** `hub_root(Path.cwd())`를 기준으로 해석. 명시 인자는 정규화하지 않는다 |
| `_load_code_scan_json`(`:869`) | `cwd = Path.cwd()` | `cwd = Path(hub_root(Path.cwd()))` |
| `cmd_ingest_scan`(`:1252`) | `cwd = Path.cwd()` | `cwd = Path(hub_root(Path.cwd()))` |

- **[MUST] 명시 `--brain-path`는 정규화하지 않는다** — `test_brain_tool.py`가 `tmp_path`로 격리 brain을 만들어 명시 전달하므로(`test_brain_tool.py:34-35` 제약 「tmp_path 기반 — 실제 프로젝트 `.opal/brain` 오염 금지」), 명시 인자를 허브로 리다이렉트하면 142건 스위트가 실 brain을 오염시킨다(H-3). 기본값 경로에만 적용한다.
- `ingest-scan`의 `rel = str(md_file.relative_to(cwd))`(`:1268`)는 `cwd`가 정규화된 뒤에도 정합하다 — 열거 원천과 상대 기준이 같은 값이다.

**(3) `.opal/` 참조와 스캔 대상은 분리하지 않는다** — ANALYSIS §8 승계. 대신 의미 한계를 문서로 고정한다(F-001 §3.1.2 5항).

**(4) FE `@header` 3건** — `exports` 필드 누락으로 `uncovered/incomplete` 차단 3건이 발생한다(E1-4). 테스트 파일이므로 `"exports": []`가 정확한 값이다. [MUST] `docs/CONVENTIONS.md` §@header 규칙: "코드 `@header`에는 이력을 기재하지 않는다 — `@header`는 현재 시점의 사실만 담고, 이력은 git 로그와 `tasks/{NNN}-*/DONE.md`가 갖는다." — `exports` 추가 외 `description`에 태스크 번호를 덧쌓지 않는다.

#### 3.3.3 환경 변경
해당 없음.

#### 3.3.4 배치/마이그레이션
해당 없음. **[MUST] EXECUTE 구간에 `./scripts/install-mac.sh`를 실행하지 않는다** — 검증은 워크트리 소스 직접 실행(`node <워크트리>/opal/tools/code-scan/code-scan.js validate`)으로 수행한다. 미완성 브랜치 코드를 전역 배포본에 덮으면 다른 세션의 도구가 함께 흔들린다.

#### 3.3.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-020 | R-3 AC(a) | 산출물 검사 | `cwd()`·`__file__` 파생 조립 중 정규화 미경유 지점 0건 |
| TS-021 | R-3 AC(c) | 회귀 테스트 | 허브 cwd에서 `code-scan validate` 출력이 변경 전과 **바이트 동일**(차단 3건 정비 전 기준으로 대조) |
| TS-022 | R-3 AC(d) | 기능 테스트 | 워크트리 cwd에서 `code-scan validate` → `header_source_unset` 소거 |
| **TS-027** | **R-7 AC(a)** | 기능 테스트 | FE 3파일이 `uncovered:incomplete` **차단 위반 집합에서 사라진다**(3건 → 0건) |
| **TS-028** | **R-7 AC(b)** | 산출물 검사 | 3파일 `@header`가 **107 신설 규정 준수** — `description`에 서로 다른 태스크 번호 2개 이상 0건 · 이력 전용 필드 0건(`header_history` 검출 0) |
| **TS-029** | **R-7 AC(d)** | 회귀 테스트 | `validate` `counts` **기존 키 값이 차단 3건 감소 외 이동 0** |
| TS-023 | R-3 AC(d) | 기능 테스트 | 워크트리 `validate`가 **정상 판정으로 진입한다**(`header_source_unset` 0 · `headerSource` 확정 · `newly_uncovered` 0). **워크트리 exit·차단 집합은 허브 트리에 대한 값이므로 브랜치 변경과 무관하다**(§2.3.4) — FE 정비의 워크트리 측 증거는 `extractHeader` 직접 호출로, 허브 `exit 0`은 **머지 후 TS-071**로 판정한다 |
| **TS-071** | **R-5 AC(a)(b) / R-7 AC(c)** | 회귀 테스트 | **머지 후 push 전**(실패 시 `git reset --hard`로 머지 되돌림): 허브 state-tool 0 failed(현재 1) · 허브 console BE 0 failed / 0 skipped(현재 9 failed / 1 skipped) · 허브 `validate` exit 0(현재 exit 2 / 차단 3건) |
| TS-024 | R-3 AC(b) | 회귀 테스트 | brain-tool 142건 회귀 0 — 명시 `--brain-path` 격리가 유지된다 |
| TS-025 | R-3 AC(b) | 기능 테스트 | 워크트리 cwd에서 `brain-tool search`가 허브 brain을 읽어 `ok:true` |
| TS-026 | R-3 / H-9 | 산출물 검사 | 워크트리 실행이 미머지 변경을 검증하지 않는다는 한계가 문서에 명시 |

---

### F-004: 테스트 위치 내성

#### 3.4.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/state-tool/tests/test_state_tool.py` | 환경 | S-31 대상 폴더를 접두사 동적 탐색으로 교체 | `test_state_tool.py:4573` |
| 2 | `dashboard/backend/tests/test_routers.py` | 환경 | `_T103_ROOT` 정규화 + `_T103_TASK_089/091` 접두사 동적 해석 | `test_routers.py:1007,1010-1011` |
| 3 | `dashboard/backend/tests/test_parsers.py` | 환경 | `AI_FRAMEWORK_ROOT` 정규화 | `test_parsers.py:19` |
| 4 | `dashboard/backend/tests/test_adapters.py` | 환경 | 루트 정규화 + 021 접두사 동적 탐색 | `test_adapters.py:84-86` |

#### 3.4.2 설계 결정

**(1) S-31 동적 탐색 방식** (PLAN 결정 2)

테스트 모듈 레벨 헬퍼를 1개 둔다:
```
_find_repo_task_dir(repo_root: pathlib.Path, prefix: str) -> pathlib.Path
```
- 탐색 범위: `repo_root/tasks/{prefix}*` 와 `repo_root/tasks/backup/{prefix}*` **2개 글롭**(각 1-depth). `rglob` 금지 — 1,026파일 트리 전수 순회 비용과 중첩 오매칭을 피한다.
- **정확히 1건 매칭을 요구한다.** 0건이면 `self.fail()`, 2건 이상이면 `self.fail()` — [MUST] TASK.md §제약 ③ 「테스트 단언 약화 금지」에 따라 `skipTest`로 강등하지 않는다. 대상 부재는 이 태스크가 다루는 「위치 이동」이 아니라 「삭제」이며, 조용한 skip은 검증 무력화다(`test_state_tool.py:8241`의 기존 PM 판정과 같은 취지).
- 실패 메시지에 **핀 자기고백 1줄**을 넣는다 — 「이 단언은 098 TASK.md 실파일에 고정돼 있다. 삭제됐다면 신 스키마 TASK.md 실파일로 대체 fixture를 선정해야 한다」. 근거: 회귀-핀 개념(§2.6.3, E5+E1) — 핀을 없앨 수는 없으나 후속이 즉시 판단할 정보를 남긴다.
- **[MUST] 픽스처 대체 금지** — `confirmed_ratio == 0.75` 등 4셀 단정은 098 TASK.md 실내용에 대한 단정이므로 그대로 보존한다(`test_state_tool.py:4577-4594`).
- `repo_root` 해석은 현행 `ST.find_project_root(str(_TOOL_DIR))` 유지 — 이미 허브로 수렴한다(§2.2.2).

**(2) dashboard 테스트 루트 정규화** (PLAN 결정 4의 테스트 축)

```
from dashboard.backend.paths import hub_root
_T103_ROOT = hub_root(Path(__file__).resolve().parents[3])
```
- 대상 3파일: `test_routers.py:1007` · `test_parsers.py:19` · `test_adapters.py:85`.
- **[MUST] 정규화 제외 화이트리스트** — `test_config.py:352,371`(`opal/core/setting.default.json`·`scripts/install-mac.sh` 내용 단정)과 `test_deploy_smoke.py:42`는 **브랜치 소스**를 봐야 하므로 무변경이다(H-7, F-001 §3.1.2 4항).
- `_T103_TASK_089`·`_T103_TASK_091`은 상수 문자열을 유지하지 않고 접두사(`"089-"`,`"091-"`)에서 해석한다 — dashboard 테스트에도 `_find_repo_task_dir` 동형 헬퍼를 1개 둔다(폴더명 반환). 성질 라벨(FX-089 = state.json 부재 / FX-LEGACY = gate 보유 행 0건)은 주석으로 보존한다.
- 021 태스크 참조(`test_adapters.py:84-88`)는 기존 `pytest.skip` 가드를 유지한다 — 루트 정규화로 허브를 보게 되면 실제로 실행되어 허브 skip 수치와 일치한다.

#### 3.4.3 환경 변경
해당 없음.

#### 3.4.4 배치/마이그레이션
해당 없음.

#### 3.4.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-030 | R-4 AC(a) | 산출물 검사 | 대상 3파일에 특정 태스크 폴더명 리터럴 0건(접두사만 남음) |
| TS-031 | R-4 AC(b) | 회귀 테스트 | S-31의 4셀 단정·`confirmed_ratio 0.75`가 원문 그대로 보존 |
| TS-032 | R-4 AC(c) | 기능 테스트 | 098이 `tasks/backup/` 아래에 있는 현 상태에서 S-31 통과 |
| TS-033 | R-4 / H-6 | 기능 테스트 | 접두사 매칭이 0건·2건일 때 skip이 아니라 실패로 드러난다 |
| TS-034 | R-4 / H-7 | 산출물 검사 | `test_config.py`·`test_deploy_smoke.py`의 루트 파생이 무변경 |
| TS-035 | **R-4 AC(e)** / R-5 AC(c) | 회귀 테스트 | **허브·워크트리 양쪽 console BE `0 skipped`**(`-rs` 사유 목록 대조). 워크트리 2건은 `.opal/` 참조로, 허브 1건(`test_adapters.py:88`)은 하드코딩 제거로 해소 + 새로 켜진 테스트 신규 실패 0건 |

---

### F-005: 태스크 열거·주소 경계 위치 불변화 (R-6)

#### 3.5.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `dashboard/backend/scanner.py` | BE | 열거 SSOT `iter_task_dirs`·`resolve_task_dir` 신설 + `_count_tasks` 위임 | `scanner.py:26-36` |
| 2 | `dashboard/backend/routers/dashboard.py` | BE | `_collect_all_tasks`가 `iter_task_dirs` 위임 + `_archived` 플래그 주입 | `dashboard.py:46-65` |
| 3 | `dashboard/backend/routers/tasks.py` | BE | 목록 열거 위임 + detail·artifact가 `resolve_task_dir` 사용 | `tasks.py:455-491,520,654` |
| 4 | `dashboard/backend/routers/doctor.py` | BE | 제외 판정 주석만 추가(로직 무변경) | `doctor.py:85` |

#### 3.5.2 설계 결정

**(1) 처방 판정 — ANALYSIS 권고안 (a) 기각, 「2단 열거」 채택** (PLAN 결정 1)

| 후보 | 판정 | 근거 |
|------|------|------|
| (a) `tasks.py`의 `backup` 스킵을 scanner·dashboard에 이식 | **기각** | 동결 코호트 21건이 전부 `tasks/backup/` 아래라 `set(cohort) <= observed_prefixes`(`test_routers.py:1437`)와 `completed_tasks >= 21`(`:1405`)이 **계속 실패**한다. 또한 같은 리터럴을 3곳에 복제해 4번째 지점에서 재발한다 |
| (b) 재귀(`os.walk`) 전환 | **기각** | 깊이 무제한 순회는 1,026파일 트리에서 비용이 크고 중첩 `backup/` 엣지케이스를 남긴다(ANALYSIS §7 Q11 부작용 승계) |
| **(c) 2단 열거 + 아카이브 플래그(채택)** | **채택** | `tasks/` 1-depth(단, `backup` 디렉터리 자신은 태스크가 아님) + `tasks/backup/` 1-depth. 깊이가 2로 **고정**되어 성능·중첩 리스크가 없고, 모수가 위치 이동에 불변이 된다. E1-2로 TS-020·TS-021·TS-022 통과를 실측 예측 |

**[MUST] 항등 보장은 「같은 함수」로 한다** — 세 지점이 각자 조건문을 갖지 않고 단일 열거 함수를 호출한다. 현재 파손 원인이 「같은 `tasks/`를 세는데 기준이 다르다」이므로, 규칙 복제로는 재발을 막을 수 없다.

`dashboard/backend/scanner.py`에 신설(신규 모듈을 만들지 않는다 — `tasks.py:447`·`dashboard.py:24`가 이미 `scanner`를 import한다):
```
def iter_task_dirs(tasks_dir: str) -> Iterator[tuple[os.DirEntry, bool]]
    # (entry, is_archived) — tasks/ 1-depth(backup 디렉터리 자신 제외) 후 tasks/backup/ 1-depth
def resolve_task_dir(project_path: str, task_id: str) -> str | None
    # iter_task_dirs 열거 결과의 이름 완전 일치로 해석. 문자열 조립하지 않는다
```
- `ProjectInfo.task_count`(`scanner.py:104`)는 `sum(1 for _ in iter_task_dirs(...))`로 위임 — 현재 `backup` 폴더를 태스크 1건으로 오계수하는 결함이 함께 해소된다.
- `_collect_all_tasks`는 `state["_archived"] = is_archived`를 추가한다(additive — 기존 필드·키 계약 불변). `_task_id`는 폴더명(`entry.name`)이며 `backup/` 접두를 붙이지 않는다 — detail 조회 키와 일치해야 한다.
- `tasks.py` 목록은 `is_archived`로 컬럼을 분기한다(현행 archive 카드 조립 로직 `:479-489` 재사용) — **열거는 공통, 표시 분류만 지점별**이다.

**(2) detail·artifact의 주소 해석** (H-5 보안 포함)

- `tasks.py:520`·`:654`의 `os.path.join(project_path, "tasks", task_id)`를 `resolve_task_dir(project_path, task_id)`로 교체한다.
- **[MUST] 문자열 조립이 아니라 열거 대조로 해석한다** — 화이트리스트 방식이므로 `task_id`에 `../`·절대경로가 들어와도 이름 완전 일치에 실패해 404가 된다. 현행 detail 경로에는 traversal 검증이 없으므로(artifact의 `name` 검증만 존재 `:659-660`) 이 설계는 보안을 **강화**한다.
- 결과: 아카이브 카드(`tasks.py:481` `task_id=entry.name`)가 상세에서 열린다 — 목록은 내보내는데 상세는 404였던 제품 결함이 함께 닫힌다.

**(3) `doctor.py` 제외 판정** (PLAN 결정 3 — ANALYSIS Q6 재검토 후 채택)

- 판단 근거: `doctor.py:83-90`은 **인자로 받은 그 경로**에 `tasks/`가 있는지를 사람에게 보고하는 진단이다. 여기에 허브 정규화를 씌우면 워크트리를 진단해도 항상 허브의 `tasks/`를 보고하므로 「이 작업본에 태스크 문서가 없다」는 진단 신호가 영구 소실된다 — 진단 도구가 진단 대상 해석에 의존해 자기 관측을 무력화하는 순환이다.
- 2단 열거도 적용하지 않는다 — 진단 문면이 「`tasks/` — N개 태스크 폴더」로 **디렉터리 리터럴 상태**를 말한다. 집계 모수가 아니다.
- **[MUST] 제외를 3중으로 고정한다**: ① `doctor.py:85`에 예외 마커 주석 + §2.5 (4) 포인터 ② 리터럴 진단 단정 테스트 1건(TS-044) ③ F-001 문서 4항(적용 대상 경계).

#### 3.5.3 환경 변경
해당 없음.

#### 3.5.4 배치/마이그레이션
해당 없음 — `tasks/backup/` 구조는 변경하지 않는다(TASK.md §범위 「제외」).

#### 3.5.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-040 | R-6 / 열거 항등 | 기능 테스트 | 3지점 열거 결과의 태스크 이름 집합이 **동일**(항등) |
| **TS-047** | **R-6 AC(a)(b)** | 기능 테스트 | **열거 함수가 1개이고 3지점이 그것만 호출한다 + 잔여 직접 열거 0건** (TS-040의 출력 항등으로는 3지점이 각자 열거를 유지한 상태를 배제하지 못한다) |
| TS-041 | R-6 AC(d) | 기능 테스트 | `completed_tasks >= 21`·`total_tasks >= 23`·`sum(w.n) == completed_tasks`(TS-020 원본) 통과 |
| TS-042 | R-6 AC(c)(d) | 기능 테스트 | 코호트 21건 전건이 `workflow_stats[].tasks`에 관측되고 코호트 필터 중앙값이 425/276/75(TS-021 원본) 통과 |
| TS-043 | R-6 AC(e) | 기능 테스트 | `tasks/backup/` 소재 태스크의 detail이 200 + legacy 필드 유지(`ts015`·`ts017[089]`·`owner_term`) + `tasks.py` `archive` 컬럼 기존 동작 무변경(backup 소재 true · 직속 false) |
| TS-044 | R-6 / doctor | 기능 테스트 | `doctor`가 인자 경로의 리터럴 `tasks/` 상태를 보고한다(허브로 치환하지 않는다) |
| TS-045 | R-6 / H-5 | 보안 테스트 | `task_id`에 `../`·절대경로·구분자 포함 시 404(경로 이탈 0건) |
| TS-046 | R-6 / H-4 | 회귀 테스트 | `test_scanner.py` 합성 픽스처 `task_count`(2/0) 불변 |

---

### F-006: 이동값 단언 규약 정렬 (R-8)

#### 3.6.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `dashboard/backend/tests/test_routers.py` | 환경 | `ts108`·`ts137`의 무조건 값 단정을 코호트 필터 재계산 단정으로 교정 | `test_routers.py:1830-1831,1888-1890` |

> 이 파일은 F-004·F-005 관련 수정과 **같은 Step(Step 3)**에서 순차 편집한다 — 동시 편집 시 후행 저장이 선행을 덮는다.

#### 3.6.2 설계 결정

- **교정 방향** — `ts021`이 이미 확립한 이동값 규약을 그대로 적용한다: 동결 코호트 ID로 필터해 **재계산**한 값이 baseline과 일치하는지 단정하고, API 직접값은 코호트가 완료 전량과 일치할 때만 단정한다(`test_routers.py:1444-1452`).
- **[MUST] 이는 단언 약화가 아니라 기존 [MUST] 준수로의 정렬이다** — `STATS-BASELINE.md` §6.1: "완료기준 (3) 검증은 반드시 §2 ID 목록으로 필터한 뒤 대조한다"(`test_routers.py:1419-1421`에 인용된 원문). `ts108`·`ts137`은 이 [MUST]를 위반한 단언이며, `ts021`은 준수한다. 동결값 425(보정 후)·799(보정 끔)는 **그대로 단정**된다 — E1-2로 코호트 필터 재계산이 425/276/75를 재현함을 실측했다.
- `ts108`의 additive 불변식(모델 필드 선택성 `:1810-1817`, `pm==work`·`captain==wait` 축퇴 `:1832-1836`)은 **무조건 단정 그대로 유지**한다 — 이동값이 아니다.
- `ts137`의 `quiet_hours_applied is False`·`quiet_hours_label == ""`(`:1886-1887`)도 무조건 유지한다.
- 보정 끔 케이스의 코호트 재계산 기대값은 `STATS-BASELINE.md` §4.1의 동결값(opd 799 / opds 276 / opp 75)을 쓴다 — RED 작성자가 실행 관측으로 재확인한 뒤 고정한다(E1 요구: 관측 스코프·명령 기재).
- **[MUST] `red-first.md` §3 적용 경계** — 이 교정은 **RED 단계에서 테스트 작성자가 1회** 수행한다. GREEN/fix 루핑 중에는 어떤 테스트 파일도 수정하지 않는다.

#### 3.6.3 환경 변경
해당 없음.

#### 3.6.4 배치/마이그레이션
해당 없음.

#### 3.6.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-050 | R-8 AC(a) | 기능 테스트 | `ts108`·`ts137`이 코호트 필터 재계산으로 425/799를 단정하며 통과 |
| TS-051 | R-8 AC(b) | 산출물 검사 | 교정 후에도 동결값 단정이 남아 있다(값 단정 삭제 0건) |
| TS-052 | R-8 AC(b) | 산출물 검사 | additive 불변식·`quiet_hours` 계약 단정이 무조건 형태로 보존 |
| TS-053 | R-8 AC(c) / H-8 | 회귀 테스트 | 코호트 데이터를 인위 변경하면 두 테스트가 실패한다(단언 유효성) |

---

## RED-first 판정

- **트랙: RED-first 강제(ON)** — [MUST] `opal/core/references/harness/red-first.md` §1.5: "RED-first 강제 (self-confirming 위험 높음): … 버그 수정(회귀 방지)". 본 태스크는 전 기능이 버그 수정 + 회귀 방지이며, API 계약 변경(`_archived` additive·detail 주소 해석)도 포함한다.
- **[MUST] RED→GREEN 순서** — 실패 테스트를 먼저 작성·실행해 exit≠0을 증거로 기록한 뒤 구현에 진입한다(red-first.md §1). Step 3이 RED 증거 게이트다.
- **[MUST] 작성자≠구현자** — 테스트 신설·개정 Step(1·2·5·6·7)은 전부 `opal-test-agent`가, 구현 Step(4·8·9·10·11·12)은 `opal-be-agent`/`opal-task-agent`/`opal-fe-agent`가 수행한다(red-first.md §2).
- **[MUST] 테스트 불변성** — GREEN/fix 루핑 중 테스트 파일 수정 금지(red-first.md §3). F-006의 단언 교정은 Step 5(RED 구간) 1회로 한정하며, Step 8 이후 어떤 워커도 테스트 파일을 열지 않는다.
- **공개 인터페이스 검증**(red-first.md §4) — CLI exit code·stdout JSON(code-scan), HTTP 응답(console BE), `module.exports`/모듈 공개 함수(골든 표 대조)로 검증한다. private 내부 상태를 단정하지 않는다.
- **목표계열 선작성 트랙(§1.6)은 적용하지 않는다** — 본 태스크의 목표(양쪽 0 failed)는 파괴 관점(회귀 가설)으로 온전히 환원되고 교체형 목표가 아니다. red-first.md §1.6 착수 판단 기준의 「목표가 단일 결함 수정이고 검증 관점이 파괴 관점과 사실상 일치한다 → 순차 권장」에 해당한다.

---

## 4. 통합 실행 계획

> **[MUST] EXECUTE 워커는 코드 루트(`/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_109/`, 브랜치 `feat/OP-TASK-109`)에서 작업한다.** 아래 §4.2 각 Step의 `**파일**`은 **허브 기준 상대경로**이며, 워커는 이를 코드 루트에 붙여 해석한다. 태스크 산출물(`tasks/109-*/`)만 허브에 쓴다.

### 4.1 Phase 그룹핑

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-002 | 1, 2 | opal-test-agent | 병렬 가능 | 파일 교집합 없음 |
| 1 | F-002 | 3 | opal-test-agent | 순차 | RED 증거 게이트 |
| 2 | F-002 | 4 | opal-be-agent | 순차 | `paths.py` 부재 시 Phase 3 테스트가 수집 단계에서 깨진다 |
| 3 | F-004·F-005·F-006 | 5, 6, 7 | opal-test-agent | 5∥6∥7 병렬 가능 | 파일 교집합 없음 |
| 4 | F-005 | 8 → 9 | opal-be-agent | 순차 | 9가 8의 신설 함수를 소비 |
| 4 | F-003 | 10, 11, 12 | task/task/fe | 8·9와 병렬 가능 | 런타임·영역 분리 |
| 5 | F-001 | 13 | opal-task-agent | 병렬 가능 | 문서 단독 |
| 5 | R-5 | 14 | opal-test-agent | 순차 | 전 Step 완료 후 |
| 5 | 문서 | 15 | PM 직접 | 순차 | 14 통과 후 |

### 4.2 실행 체크리스트
> 총 15개 Step | Phase 5개 | 실행 모드: **복잡**

#### Step 1: 공유 골든 케이스 표 + Python 2스위트 동치 테스트 신설 [RED]
- [ ] 완료
- **소속 기능**: F-002
- **영역**: 환경
- **agent**: opal-test-agent — 테스트 신설이며 red-first.md §2가 RED 작성 주체를 test-agent로 못박는다
- **파일**: `opal/core/references/hub-root-cases.json`(신규) · `dashboard/backend/tests/test_paths.py`(신규) · `opal/tools/brain-tool/tests/test_brain_tool.py`(수정)
- **작업 내용**: §3.2.3 표 스키마로 C-1~C-7 골든 케이스 작성. 두 Python 스위트가 이 파일을 각자 읽어(경로 파생: dashboard = `Path(__file__).resolve().parents[3]`, brain-tool = `_TOOL_DIR.parents[2]`) `hub_root()` 반환값을 문자열 대조. 항등 케이스는 입력 문자열과 바이트 동일 단정. `state_tool.find_project_root` 정합 케이스 1건 추가(TS-014). [MUST] 표를 스위트 안에 복제하지 않는다.
- **완료 기준**: `test_paths.py`는 `ModuleNotFoundError`/`AttributeError`로, brain-tool 케이스는 `AttributeError: hub_root`로 **실패**한다(RED). 신규 2파일에 `@header` 보유.
- **테스트**: TS-011, TS-012, TS-014, TS-015
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: code-scan Node 동치 + 워크트리 CLI 블랙박스 테스트 신설 [RED]
- [ ] 완료
- **소속 기능**: F-002, F-003
- **영역**: 환경
- **agent**: opal-test-agent — 동일 근거(RED 작성 주체)
- **파일**: `opal/tools/code-scan/tests/test-hub-root.js`(신규)
- **작업 내용**: ① `require('../code-scan.js').hubRootFromPath`로 골든 표 C-1~C-7 문자열 대조 ② CLI 블랙박스 1건 — `os.tmpdir()`에 `hub/.opal/code-scan.json`(headerSource inline)과 `hub/.opal-worktrees/task_001/`을 만들고 **[MUST] 워크트리 루트에 `.git`을 파일로 생성**(실제 워크트리 재현 — `code-scan.js:333`은 `fs.existsSync`로 파일/디렉터리를 구분하지 않는다), 그 cwd에서 CLI 실행 → `header_source_unset`이 아니어야 한다. ③ 음성 케이스 — 설정을 워크트리 쪽에만 두면 허브 기준 해석이므로 `header_source_unset`이 난다.
- **완료 기준**: `node --test tests/test-hub-root.js`가 실패한다(RED — `hubRootFromPath` 미export + 세그먼트 미인식). `@header` 보유(기존 테스트 헤더 포맷 준용 — `tests/test-header-source.js:1-11`).
- **테스트**: TS-011, TS-022
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 3: RED 증거 수집·기록
- [ ] 완료
- **소속 기능**: F-002
- **영역**: 공통
- **agent**: opal-test-agent — RED 증거는 작성자가 자기 테스트 실행으로 기록한다
- **파일**: `tasks/109-260906-opds-태스크루트-해석-수렴/RED-EVIDENCE.md`(신규, 허브 산출물)
- **작업 내용**: Step 1·2 테스트를 워크트리에서 실행해 exit code·실패 메시지를 기록한다. **[MUST] 실행 명령과 관측 스코프를 함께 적는다**(citation-rules.md §9 (a)). 기존 실패 9건 + state-tool 1건의 현재 상태도 기준선으로 함께 캡처한다.
- **완료 기준**: RED-EVIDENCE.md에 신규 테스트 실패(exit≠0) 증거와 기준선 수치가 명령·스코프와 함께 기재된다.
- **테스트**: 검증 방법 — `node --test` · `pytest` exit code 캡처
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 2

#### Step 4: `dashboard/backend/paths.py` 신설 [GREEN]
- [ ] 완료
- **소속 기능**: F-002
- **영역**: BE
- **agent**: opal-be-agent — `dashboard/backend` 패키지 신규 모듈이며 console BE 런타임 계약을 다룬다
- **파일**: `dashboard/backend/paths.py`(신규)
- **작업 내용**: §3.2.2 계약대로 `hub_root(path) -> str` 구현(순수 문자열 함수, 표준 라이브러리만). `@header`에 `module: paths` / `layer: config` / `domain: console` / `exports: ["hub_root"]` / `depends: []` 기재. 규칙 원문 재서술 금지 — `opal-harness.md` §2.5 (4) 포인터 주석 1줄. **[MUST] `docs/CONVENTIONS.md` §@header 규칙: 이력 전용 필드를 신설하지 않고 태스크 번호를 덧쌓지 않는다.**
- **완료 기준**: `test_paths.py`가 통과(GREEN)하고 `dashboard/backend/tests` 전체에서 신규 실패 0건. `code-scan validate`의 차단 건수가 늘지 않는다.
- **테스트**: TS-011, TS-012, TS-015
- **실행 방법**: sub-agent
- **의존**: Step 3

#### Step 5: console BE 테스트 일괄 개정 (test_routers.py) [RED]
- [ ] 완료
- **소속 기능**: F-004, F-005, F-006
- **영역**: 환경
- **agent**: opal-test-agent — 테스트 개정이며 F-006의 단언 교정 판단이 작성자 소관이다
- **파일**: `dashboard/backend/tests/test_routers.py`
- **작업 내용**: **[MUST] 이 파일의 모든 변경을 이 Step에서 순차 편집한다**(3기능이 같은 파일을 만진다 — 분할 시 후행 저장이 선행을 덮는다). ① `_T103_ROOT`를 `hub_root(...)`로 정규화(§3.4.2) ② `_T103_TASK_089/091`을 접두사 동적 해석으로 교체 + 성질 라벨 주석 보존 ③ 3지점 열거 항등 단정 신설(TS-040) ④ 아카이브 태스크 detail 200 단정(TS-043) ⑤ `task_id` 경로 이탈 거부 단정(TS-045) ⑥ `ts108`·`ts137`을 코호트 필터 재계산 단정으로 교정(§3.6.2) — **[MUST] 동결값 425/799 단정을 삭제하지 않는다**.
- **완료 기준**: 개정 후 실행에서 ①~⑤가 RED(실패), ⑥은 통과. 삭제된 단언 0건 — 개정 전/후 `assert` 개수와 대상을 RED-EVIDENCE.md에 대조 기재.
- **테스트**: TS-030, TS-035, TS-040, TS-041, TS-042, TS-043, TS-045, TS-050, TS-051, TS-052
- **실행 방법**: sub-agent
- **의존**: Step 4

#### Step 6: console BE 잔여 테스트 위치 내성 개정 [RED]
- [ ] 완료
- **소속 기능**: F-004, F-005
- **영역**: 환경
- **agent**: opal-test-agent — 동일 근거
- **파일**: `dashboard/backend/tests/test_parsers.py` · `dashboard/backend/tests/test_adapters.py` · `dashboard/backend/tests/test_scanner.py`
- **작업 내용**: `AI_FRAMEWORK_ROOT`(`test_parsers.py:19`)·021 루트(`test_adapters.py:85`)를 `hub_root(...)`로 정규화하고 021 폴더를 접두사 동적 탐색으로 해석. `test_scanner.py`에 2단 열거 단정 추가(`backup` 폴더 자체는 태스크로 세지 않고 하위는 센다) + 합성 픽스처 불변 단정 유지. **[MUST] `test_config.py`·`test_deploy_smoke.py`는 손대지 않는다**(소스 트리 참조 — H-7).
- **완료 기준**: `test_scanner.py` 신규 단정이 RED. `test_parsers`·`test_adapters`는 허브 실행에서 통과 유지(정규화가 허브에서 항등이므로).
- **테스트**: TS-034, TS-035, TS-046
- **실행 방법**: sub-agent
- **의존**: Step 4

#### Step 7: state-tool S-31 동적 탐색 개정 [RED]
- [ ] 완료
- **소속 기능**: F-004
- **영역**: 환경
- **agent**: opal-test-agent — 단언 강도 보존 판단이 필요한 테스트 개정이다
- **파일**: `opal/tools/state-tool/tests/test_state_tool.py`
- **작업 내용**: §3.4.2 (1)대로 모듈 레벨 `_find_repo_task_dir(repo_root, prefix)` 신설(2글롭·1건 정확 매칭·0/2건 시 fail·핀 자기고백 메시지) 후 S-31이 `"098-"` 접두사로 대상을 해석하게 바꾼다. **[MUST] `confirmed_ratio == 0.75` 등 4셀 단정과 docstring의 검증 본질 선언을 보존한다.** `skipTest` 도입 금지.
- **완료 기준**: 098이 `tasks/backup/` 아래인 현 상태에서 S-31 통과 → state-tool `0 failed`. 개정 전후 단언 개수 동일.
- **테스트**: TS-030, TS-031, TS-032, TS-033
- **실행 방법**: sub-agent
- **의존**: Step 3

#### Step 8: 태스크 열거 SSOT 신설 (scanner.py) [GREEN]
- [ ] 완료
- **소속 기능**: F-005
- **영역**: BE
- **agent**: opal-be-agent — console BE 서비스 계층 신규 공개 함수 2개를 만든다
- **파일**: `dashboard/backend/scanner.py`
- **작업 내용**: §3.5.2 (1)대로 `iter_task_dirs(tasks_dir) -> Iterator[tuple[os.DirEntry, bool]]`·`resolve_task_dir(project_path, task_id) -> str | None` 신설(2단 열거 고정 깊이, `os.walk` 금지). `_count_tasks`를 `iter_task_dirs` 위임으로 바꾼다. `@header`의 `exports`·`description`을 갱신한다(현재 사실만 — 이력 금지).
- **완료 기준**: `test_scanner.py` 전건 통과(합성 픽스처 2/0 불변 포함). `iter_task_dirs`가 같은 입력에 결정론적 순서를 반환한다.
- **테스트**: TS-040, TS-046
- **실행 방법**: sub-agent
- **의존**: Step 5, Step 6

#### Step 9: 열거·주소 소비 전환 (dashboard.py · tasks.py · doctor.py) [GREEN]
- [ ] 완료
- **소속 기능**: F-005
- **영역**: BE
- **agent**: opal-be-agent — 라우터 3파일의 응답 계약을 다룬다
- **파일**: `dashboard/backend/routers/dashboard.py` · `dashboard/backend/routers/tasks.py` · `dashboard/backend/routers/doctor.py`
- **작업 내용**: ① `_collect_all_tasks`가 `iter_task_dirs` 위임 + `state["_archived"]` additive 주입 ② `tasks.py` 목록 열거를 위임으로 전환(archive 컬럼 분기는 `is_archived` 플래그로) ③ `tasks.py:520,654`의 `task_dir` 조립을 `resolve_task_dir`로 교체(문자열 조립 제거 → 경로 이탈 차단) ④ `doctor.py:85`에 **제외 마커 주석 + §2.5 (4) 포인터**만 추가(로직 무변경). `@header` 갱신.
- **완료 기준**: 허브 console BE에서 `ts015`×2·`ts017[089]`·`owner_term`·`ts020`·`ts021`·`ts022` 7건이 통과하고 신규 실패 0건. `doctor` 응답은 인자 경로의 리터럴 상태를 보고한다.
- **테스트**: TS-040~TS-045
- **실행 방법**: sub-agent
- **의존**: Step 8

#### Step 10: brain-tool 허브 정규화 3지점 [GREEN]
- [ ] 완료
- **소속 기능**: F-002, F-003
- **영역**: 환경
- **agent**: opal-task-agent — `opal/tools/` 프레임워크 도구이며 console BE·FE 어느 전문 영역도 아니다(폴백 범용, advanced)
- **파일**: `opal/tools/brain-tool/brain_tool.py`
- **작업 내용**: 모듈 레벨 `hub_root(path) -> str` 신설(§3.2.2 계약, 규칙 포인터 주석만) + §3.3.2 (2) 표대로 3지점 적용. **[MUST] 명시 `--brain-path` 인자는 정규화하지 않는다**(기본값 `"."` 경로에만 적용 — 격리 테스트 오염 방지, H-3).
- **완료 기준**: brain-tool 142건 회귀 0. 워크트리 cwd에서 `brain-tool search`가 허브 brain을 읽어 `ok:true`. Step 1의 brain-tool 골든 케이스 통과.
- **테스트**: TS-011, TS-024, TS-025
- **실행 방법**: sub-agent
- **의존**: Step 3

#### Step 11: code-scan `findProjectRoot()` 세그먼트 정규화 [GREEN]
- [ ] 완료
- **소속 기능**: F-002, F-003
- **영역**: 환경
- **agent**: opal-task-agent — Node 런타임 프레임워크 도구(3,400줄 이상)이며 BE/FE 전문 영역이 아니다. **[MUST] grep으로 구간을 특정한 뒤 부분 Read**한다(입력 축소)
- **파일**: `opal/tools/code-scan/code-scan.js`
- **작업 내용**: `hubRootFromPath(p)` 신설(§3.2.2) + `findProjectRoot()` **첫 줄만** `let dir = hubRootFromPath(process.cwd());`로 교체(§3.3.2 (1)) + `module.exports`에 `hubRootFromPath` additive 추가(`:3707`). `@header` `description`·`exports` 갱신 — [MUST] 이력·태스크 번호 누적 금지.
- **완료 기준**: `node --test tests/*.js` 369건 회귀 0 + Step 2 신규 테스트 통과. 허브 cwd `validate` 출력이 변경 전과 바이트 동일. 워크트리 cwd에서 `header_source_unset` 소거.
- **테스트**: TS-011, TS-021, TS-022
- **실행 방법**: sub-agent
- **의존**: Step 3

#### Step 12: FE 테스트 3파일 `@header` `exports` 보강 [GREEN]
- [ ] 완료
- **소속 기능**: F-003
- **영역**: FE
- **agent**: opal-fe-agent — `dashboard/frontend/src/` 소재 TS 파일의 헤더 규약을 다룬다
- **파일**: `dashboard/frontend/src/lib/api-timeout.test.ts` · `dashboard/frontend/src/lib/utils.test.ts` · `dashboard/frontend/src/pages/brain/brain-status.test.ts`
- **작업 내용**: 각 `@header`에 `"exports": []` 추가(테스트 파일이므로 공개 export 없음). **[MUST] `description`에 태스크 번호를 덧쌓거나 이력 필드를 신설하지 않는다**(`docs/CONVENTIONS.md` §@header 규칙).
- **완료 기준**: `code-scan validate`의 `uncovered/incomplete` 3건 소거 → **exit 0**. FE 테스트 스위트 회귀 0.
- **테스트**: TS-023
- **실행 방법**: sub-agent
- **의존**: Step 11

#### Step 13: 허브 루트 해석 규칙 SSOT 명문화
- [ ] 완료
- **소속 기능**: F-001
- **영역**: 문서
- **agent**: opal-task-agent — `docs/` 갱신이 아니라 프레임워크 참조 문서 개정(실질 산출물)이므로 「문서=PM 직접」 규칙(docs/ 전용) 대상이 아니다
- **파일**: `opal/core/references/opal-harness.md` · `opal/core/references/harness/task-process.md`
- **작업 내용**: §2.5에 `(4) 허브 루트 해석 규칙`을 §3.1.2의 5항 + 3부칙으로 신설하고, `task-process.md` 4.5에 포인터 1줄을 추가한다. **[MUST] 두 문서에 「## 변경이력」 행을 추가한다** — 일시 `YYYY-MM-DD HH:mm`(KST), semver, 변경내용에 `(109)` 포함(`docs/CONVENTIONS.md` §변경이력 작성 의무). **[MUST] `~/.opal/` 배포본을 직접 편집하지 않는다**(§배포 경계).
- **완료 기준**: 규칙이 한 곳에만 존재하고 §2.5 (3)과 모순이 없으며, 3구현의 포인터 주석이 이 절을 가리킨다.
- **테스트**: TS-001~TS-005, TS-013, TS-026
- **실행 방법**: sub-agent
- **의존**: Step 3

#### Step 14: 회귀·완료 게이트 검증
- [ ] 완료
- **소속 기능**: R-5 (전 기능 공통)
- **영역**: 공통
- **agent**: opal-test-agent — 4스위트 동적 검증이 전문 영역이다
- **파일**: 변경 없음(관측만) — 결과는 TEST 단계 산출물에 기재
- **작업 내용**: §5.2 회귀 표 전건 실행. **[MUST] console BE는 저장소 루트에서 실행한다**(`cd dashboard/backend`는 `ModuleNotFoundError` 134 errors가 나는 오답). **[MUST] brain-tool·console BE는 `~/.opal/.venv/bin/python`**(시스템 `python3`에 PyYAML 없음). 워크트리 실행에 `-rs`를 붙여 skip 사유 목록을 허브와 대조한다. 워크트리 `code-scan validate`는 **워크트리 소스 직접 실행**으로 확인한다(`node <코드루트>/opal/tools/code-scan/code-scan.js validate`).
- **완료 기준**: 워크트리 state-tool `0 failed` · console BE `0 failed` · brain-tool 142+ `0 failed` · **워크트리 `validate`는 「정상 판정 진입」으로 판정**(`header_source_unset` 0 · `headerSource` 확정 · `newly_uncovered` 0 — exit·차단 집합은 허브 트리에 대한 값이므로 브랜치 변경과 무관하다, §2.3.4) · **워크트리 code-scan은 §2.3.4 구조적 잔존 목록 밖 실패 0건**(총계 0을 요구하지 않는다) + **양쪽 `0 skipped`**(R-4 AC(e) — 「수치·사유가 허브와 동일」은 `1 == 1`로도 충족되므로 판정 축이 아니다) + **양쪽 수집 수가 착수 전(358)보다 줄지 않았고 증가분이 신설 테스트로 전건 설명된다**(이 기준의 취지는 「테스트 삭제·skip 조건 무력화로 `0 skipped`를 달성하는 경로 차단」이다 — 이 태스크는 테스트를 신설하므로 수집 수는 늘어난다. 「358 불변」은 착수 전 값을 고정한 오기였다). **잔여 실패가 있으면 즉시 중단하고 원인 귀속을 보고한다(H-11).**
- **테스트**: TS-021, TS-023, TS-024, TS-035, TS-041~TS-043, TS-046, TS-050
- **실행 방법**: sub-agent
- **의존**: Step 9, Step 10, Step 11, Step 12, Step 13

#### Step 15: `docs/` 갱신 — 허브 루트 해석 규칙 포인터
- [ ] 완료
- **소속 기능**: F-001
- **영역**: 문서
- **agent**: PM 직접 — docs/ 갱신 Step 규칙(op-dev-plan SKILL.md §docs/ 갱신 Step 자동 생성 규칙)
- **파일**: `docs/CONVENTIONS.md`
- **작업 내용**: 새 규칙 도입에 해당하므로(코드 변경 → 갱신 대상 매핑 「새 패턴/규칙 도입 → CONVENTIONS.md」) 「허브 루트 해석」 항목을 신설해 §2.5 (4) 포인터 + 정규화 적용/제외 경계 1줄을 기재한다. 원문 중복 금지(포인터만). 「## 변경이력」 행 추가.
- **완료 기준**: `docs/CONVENTIONS.md`에 포인터가 추가되고 규칙 원문 중복이 0건이다.
- **테스트**: TS-001
- **실행 방법**: direct
- **의존**: Step 14

### 4.3 병렬/순차 판별 근거
| 관계 | 근거 |
|------|------|
| Step 1 ∥ Step 2 | 파일 교집합 0 — Python 스위트 vs Node 스위트 |
| Step 1·2 → Step 3 | RED 증거는 두 스위트 실행 결과가 있어야 기록된다(red-first.md §1) |
| Step 3 → Step 4 | RED 증거 없이 GREEN 진입 금지 |
| Step 4 → Step 5·6 | 테스트가 `dashboard.backend.paths`를 import한다 — 모듈 부재 시 **수집 단계에서 파일 전체가 error**로 떨어져 기준선 관측이 오염된다 |
| Step 5 ∥ Step 6 ∥ Step 7 | 파일 교집합 0 (`test_routers.py` / 3파일 / `test_state_tool.py`) |
| Step 5·6 → Step 8 | 열거 SSOT의 RED 단정이 먼저 있어야 GREEN 판정이 성립 |
| Step 8 → Step 9 | 9가 8의 신설 함수(`iter_task_dirs`·`resolve_task_dir`)를 소비 |
| Step 10 ∥ Step 11 ∥ Step 8·9 | 런타임 분리(brain-tool Python / code-scan Node / console BE) — 파일 교집합 0 |
| Step 11 → Step 12 | `validate` exit 0 판정은 세그먼트 수정 후에만 의미가 있다(그 전엔 `header_source_unset`으로 조기 종료) |
| Step 13 ∥ 4·5·6·7·8·9·10·11·12 | 문서 단독 — 코드 파일 교집합 0. 다만 3구현의 포인터 주석이 절 번호를 참조하므로 Step 14 전 완료 필수 |
| 전 Step → Step 14 | 회귀 게이트는 마지막 관측 |
| Step 14 → Step 15 | 검증 통과 후 docs/ 확정 |
| `test_routers.py` 단일 Step 집약 | F-004·F-005·F-006이 같은 파일을 만진다 — 분할 시 후행 저장이 선행 편집을 덮는다 |

---

## 5. QA 체크리스트

### 5.1 기능별 QA
| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | 규칙이 한 곳에만 정의되고 깊이 무관·허브 항등·적용 경계·의미 한계를 명시 | TS-001~TS-005, TS-026 | `opal-harness.md` §2.5 (4) 존재 + 원문 중복 0건 + 변경이력 행 2건 |
| F-002 | 3구현이 골든 표 전건에서 같은 문자열을 반환 | TS-010~TS-015 | 3스위트 통과 + 항등 케이스 바이트 동일 + 런타임별 구현 1개 |
| F-003 | 워크트리에서 code-scan·brain-tool이 허브를 본다 | TS-020~TS-026 | `validate` exit 0(양쪽) + `header_source_unset` 0건 + brain-tool `ok:true` + 허브 출력 바이트 동일 |
| F-004 | 실 폴더 이동·부재에 테스트가 견딘다(단언 강도 무변경) | TS-030~TS-035 | S-31 통과 + 폴더명 리터럴 0건 + 단언 개수 불변 + **양쪽 `0 skipped`** |
| F-005 | 3지점 열거 항등 + 아카이브 주소 지정 + 경로 이탈 차단 | TS-040~TS-046 | 열거 집합 동일 + 7건 통과 + `../` 404 + doctor 리터럴 보고 |
| F-006 | 이동값 단언이 규약을 지키며 동결값을 유지 | TS-050~TS-053 | `ts108`·`ts137` 통과 + 값 단정 삭제 0건 |

### 5.2 회귀 테스트
| 스위트 | 실행 명령 | 허브 현재 | 워크트리 현재 | 목표 |
|--------|----------|----------|--------------|------|
| state-tool | `cd opal/tools/state-tool && python3 -m pytest tests/ -q` | 1 failed / 396 | 1 failed / 396 | **0 failed** |
| console BE | **저장소 루트에서** `~/.opal/.venv/bin/python -m pytest dashboard/backend/tests -q -rs` | **9 failed** / 348 / 1 skipped | **33 failed** / 322 / 3 skipped | **0 failed** + **양쪽 `0 skipped`** + **수집 수 감소 0**(착수 전 358 대비) |
| code-scan | `cd opal/tools/code-scan && node --test tests/*.js` | 369 / 0 | 369 / 0 | 회귀 0 (+ 신규 통과) |
| brain-tool | `cd opal/tools/brain-tool && ~/.opal/.venv/bin/python -m pytest tests/ -q` | 142 / 0 | — | 회귀 0 (+ 신규 통과) |
| code-scan validate | `node <코드루트>/opal/tools/code-scan/code-scan.js validate` | **exit 2**(차단 3건) | `header_source_unset` | **exit 0 양쪽** |

- [ ] 허브 `code-scan validate` 출력이 변경 전과 바이트 동일(FE 3건 정비 전 기준 대조 후 정비)
- [ ] `code-scan validate` 차단 건수가 신규 파일로 증가하지 않는다(신규 3파일 `@header` 보유)
- [ ] `test_scanner.py` 합성 픽스처 `task_count` 2/0 불변
- [ ] `test_config.py`·`test_deploy_smoke.py` 무변경(소스 트리 참조 보존)
- [ ] 머지 후 허브 재실행에서 4스위트 `0 failed`(CLOSE 게이트)

### 5.3 코드/문서 품질
- [ ] 신규·수정 파일의 `@header`가 현재 사실만 담고 이력 필드·태스크 번호 누적이 없다(`docs/CONVENTIONS.md` §@header 규칙, `header_history` 경고 미증가)
- [ ] `~/.opal/` 배포본 직접 편집 0건(§배포 경계)
- [ ] 참조 문서 2건 + `docs/CONVENTIONS.md`에 변경이력 행 추가(semver·KST·`(109)`)
- [ ] 규칙 원문이 문서 1곳에만 있고 코드 주석은 포인터만 둔다(R-2 AC(c))
- [ ] git 이력 변경 0건 — `commit`·`push`·`reset`·`rebase`·`stash` 미실행(`opal-harness.md` §1)
- [ ] `os.walk`·`rglob` 도입 0건(고정 깊이 2단 열거)

### 5.4 보안
- [ ] `task_id` 경로 이탈(`../`·절대경로·구분자) 입력이 404로 거부된다(열거 화이트리스트 해석)
- [ ] artifact 이름 검증(`tasks.py:659-660`)이 유지된다
- [ ] 새 환경변수·시크릿·하드코딩 토큰 0건(환경변수 신설 철회 확정)
- [ ] 워크트리 sparse 패턴을 변경하지 않는다(태스크 107의 미검출 scope 위반 재발 방지 — TASK.md §배경 분석 (5))

---

## 6. 복잡도 판별
| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 15개 | 복잡 |
| 변경 파일 수 | 20개(신규 5 · 수정 15) | 복잡 |
| 모듈 범위 | 다중 — console BE · opal/tools(Python·Node) · FE · 하네스 문서 | 복잡 |
| 작업 유형 | 대규모 개선(계약 신설 + 회귀 수복) | 복잡 |
| 외부 의존성 | 없음(신규 패키지·환경변수 0) | 단순 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처

### C-1. 에이전트 토폴로지

```
Batch 1 (병렬)   A1:test-agent[Step 1]      A2:test-agent[Step 2]
                        └──────────┬──────────┘
Batch 2          A3:test-agent[Step 3 — RED 증거 게이트]
Batch 3          A4:be-agent[Step 4 paths.py]
Batch 4 (병렬)   A5:test-agent[Step 5]  A6:test-agent[Step 6]  A7:test-agent[Step 7]
Batch 5 (병렬)   A8:be-agent[Step 8 → Step 9]   A9:task-agent[Step 10]
                 A10:task-agent[Step 11 → Step 12(fe-agent)]   A11:task-agent[Step 13]
Batch 6          A12:test-agent[Step 14 회귀 게이트]
Batch 7          PM[Step 15 docs/]
```

**그룹핑 근거**:
- **파일 충돌 방지** — `test_routers.py`(Step 5)·`scanner.py`+라우터(Step 8·9)·`code-scan.js`(Step 11)는 각각 단일 에이전트에 봉인한다. 동일 파일을 만지는 Step이 서로 다른 배치에 흩어지지 않는다.
- **모듈 응집도** — Step 8→9는 신설 함수와 소비자를 같은 에이전트가 순차 처리한다(계약 드리프트 차단).
- **병렬 극대화** — Batch 5는 런타임 4갈래(console BE / brain-tool / code-scan+FE / 문서)로 갈라 동시 실행한다.
- **작성자≠구현자** — 테스트 파일은 test-agent만, 프로덕션은 be/task/fe-agent만 만진다.

### C-2. 스킬 요구사항
- 기존 스킬로 충분하다 — `op-dev-execute`(구현 Step) · `op-dev-test`(Step 14). 신규 스킬 갭 없음.
- 반복 패턴 「경로 정규화 + 포인터 주석」이 6 Step에 걸치나, 규칙 SSOT가 문서 1곳(F-001)이므로 스킬화가 아니라 **문서 포인터**로 흡수한다.

### C-3. 도구 요구사항
| 도구 | 용도 | 비고 |
|------|------|------|
| `~/.opal/.venv/bin/python` | console BE·brain-tool pytest | [MUST] 시스템 `python3`에는 PyYAML이 없다 |
| `python3` | state-tool pytest | 표준 라이브러리만 사용 |
| `node --test` | code-scan 스위트 | Node 내장 러너 |
| `code-scan`(워크트리 소스 직접 실행) | `validate` 검증 | [MUST] EXECUTE 구간에 install 재배포 금지 |
| `state-tool run.sh` | STATE 갱신 | [MUST] `state.json` 직접 편집 금지 |
| 신규 CLI·MCP·패키지 | **없음** | |

### C-4. 테스트 전략
1. **L1 단위** — 골든 표 3스위트 대조(합성 경로, FS 무접근), 경로 이탈 거부, 열거 항등.
2. **L2 통합** — 실 저장소 데이터 대조: console BE HTTP 응답(348+건), state-tool S-31 실파일, code-scan CLI 블랙박스(tmpdir 워크트리 픽스처 + 실 워크트리).
3. **회귀** — §5.2 표 4스위트 + `validate` 출력 바이트 대조.
4. **관측 규율** — [MUST] 실행 명령과 관측 스코프를 결과와 함께 기록한다(citation-rules.md §9 (a) — 스코프 없는 E1 인용은 E1로 인정되지 않는다).
5. **중단 규율** — Step 14에서 잔여 실패 1건이라도 있으면 즉시 중단·보고(H-11).

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| console BE | Python 3 / FastAPI / pytest | 해당 없음(표준 라이브러리 경로 처리) |
| opal/tools Python | Python 3 표준 라이브러리 / unittest·pytest | 해당 없음 |
| opal/tools Node | Node.js / `node --test` | 해당 없음 |
| FE | TypeScript(테스트 파일 `@header`만) | 해당 없음 |
| 문서 | Markdown(하네스 참조 문서) | 해당 없음 |

> 추천 스킬·MCP는 ANALYSIS §6.3·§6.4가 「해당 없음」으로 확정했다(범용 하네스/도구 개선 — 프레임워크 스킬 불필요). `trailofbits/modern-python`은 uv·ruff·async 패턴을 다루며 본 태스크의 표준 라이브러리 경로 처리와 접점이 없어 로드하지 않았다(스킵 사실 명시).

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| 없음 | 외부 라이브러리 API 참조가 필요한 설계 결정이 없다(표준 라이브러리 `pathlib`/`os.path`/`node:path`만 사용) |

### 8.3 참조 문서 (설계 결정 근거)
| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 기획 | TASK.md(개정본) | `tasks/109-260906-opds-태스크루트-해석-수렴/TASK.md` | R-1~R-5 원문·확정된 설계 방향·제약 |
| D-2 | 설계 | ANALYSIS.md(정정본) | `tasks/109-260906-opds-태스크루트-해석-수렴/ANALYSIS.md` §8 | 승계 확정값 + PLAN 결정 필요 5건 |
| D-3 | 설계 | 워크스페이스 축 | `opal/core/references/opal-harness.md` §2.5 | 경로 계약 원문(`:168`) — R-1 개정 대상 |
| D-4 | 설계 | TASK 공통 프로세스 | `opal/core/references/harness/task-process.md` §4.5 | worktree 생성 절차 — 포인터 주입 지점 |
| D-5 | 설계 | RED-first 트랙 | `opal/core/references/harness/red-first.md` §1·§1.5·§2·§3·§4 | 트랙 판정·작성자≠구현자·테스트 불변성 |
| D-6 | 설계 | 인용 규칙 | `opal/core/references/harness/citation-rules.md` §2·§3·§9 | 인용 포맷·[MUST] 토큰·근거 등급(E1 스코프 의무) |
| D-7 | 설계 | 프로젝트 컨벤션 | `docs/CONVENTIONS.md` §@header 규칙·§변경이력 작성 의무·§Citation Rules·§배포 경계·§State 관리 | [MUST] 제약 5건 |
| D-8 | 설계 | worktree 선언 | `.opal/worktree.json:2-11` | sparse 패턴 7항목(`.opal` 미포함) |
| D-9 | 설계 | code-scan 설정 | `.opal/code-scan.json:1-11` | `headerSource: inline` · `exclude`에 `.opal-worktrees` 기재 |
| D-10 | 소스 | code-scan 본체 | `opal/tools/code-scan/code-scan.js:331-341,377-378,3707-3717` | `findProjectRoot`·`loadConfig`·공개 export |
| D-11 | 소스 | brain-tool 본체 | `opal/tools/brain-tool/brain_tool.py:234-239,869,1252,1385` | 9번째 조립 지점 + cwd 2지점 + 기본 인자 |
| D-12 | 소스 | console BE 라우터 | `dashboard/backend/routers/tasks.py:446-448,455-491,520,654` | 목록·archive 카드·detail·artifact 주소 조립 |
| D-13 | 소스 | console BE 열거 | `dashboard/backend/scanner.py:26-36` · `dashboard/backend/routers/dashboard.py:46-65` | 1-depth 열거 2지점 |
| D-14 | 소스 | console BE 테스트 | `dashboard/backend/tests/test_routers.py:1000-1011,1405-1452,1826-1832,1885-1890` | 이동값 규약·코호트 단정·baseline |
| D-15 | 소스 | state-tool | `opal/tools/state-tool/state_tool.py:700-708` · `tests/test_state_tool.py:4559-4594` | 기존 허브 수렴 선례 + S-31 본질 선언 |
| D-16 | 소스 | doctor 라우터 | `dashboard/backend/routers/doctor.py:83-90` | 리터럴 진단 문면(제외 판정 근거) |
| D-17 | brain | 회귀 단언 고정 | `.opal/brain/pages/concept/regression-pin-of-task-time-fact.md` | F-006 성질 진단(E5 — 1차 근거 D-18 동반) |
| D-18 | 산출물 | 태스크 107 | `tasks/107-260906-opd-헤더필드-작성기준-이력분리/DONE.md` | D-17의 E1~E4 근거 |
| D-19 | 설정 | worktree 메타 | `.opal-worktrees/.meta/task_109.json` | `worktree_root`·`entries[].repo` 세그먼트 부모 관계 실측 |

### 8.4 E1 실측 부록 (본 PLAN 작성 중 관측)

> [MUST] `citation-rules.md` §9 (a): "E1을 인용할 때는 관측 스코프와 실행 명령을 함께 기재한다."

| # | 실행 명령 (cwd) | 스코프 | 관측 |
|---|----------------|--------|------|
| E1-1 | `~/.opal/.venv/bin/python -m pytest dashboard/backend/tests/test_routers.py -q -k "ts020 or ts021 or ts022 or ts108 or ts137 or ts015 or ts017 or owner_term"` (허브 루트, 2026-09-07 11:11 KST) | test_routers.py 중 9+7건 | **9 failed / 7 passed / 73 deselected**. `ts108`: `assert 857 == 425` · `ts137`: `assert 1127 == 799` · `owner_term`: `assert 404 == 200` |
| E1-2 | `~/.opal/.venv/bin/python <scratchpad>/probe2.py` — `_collect_all_tasks`를 2단 열거로 대체한 뒤 `TestClient`로 `GET /api/dashboard?project=<허브>` 호출 (허브 루트, 2026-09-07 11:12 KST) | 전 프로젝트 집계 1회 | `completed_tasks` 98 · `total_tasks` 107 · `artifact_total` 773(=by_type 합) · **코호트 21건 누락 0건** · 코호트 필터 중앙값 opd **425** / opds **276** / opp **75** → TS-020·TS-021·TS-022 통과 예측 True |
| E1-3 | `os.scandir` 카운트(동 probe) | `tasks/` · `tasks/backup/` 1-depth | `tasks/` **12**개(= `backup` 1 + 실태스크 11) · `tasks/backup/` **100**개 |
| E1-4 | `~/.opal/tools/code-scan/run.sh validate [--json]` (허브 루트) | `opal/` · `dashboard/backend/` · `dashboard/frontend/src/` 스코프 354파일 | **exit 2** — 차단 3건 = `uncovered/incomplete`(detail `exports`) on `dashboard/frontend/src/lib/api-timeout.test.ts` · `lib/utils.test.ts` · `pages/brain/brain-status.test.ts`. 비차단 `header_history/undeclared_field` 2건(`track`) |
| E1-5 | `~/.opal/tools/code-scan/run.sh validate` (워크트리 `task_109`) | 동일 | `{"ok":false,"error":"header_source_unset"}` |
| E1-6 | `~/.opal/tools/brain-tool/run.sh search "test"` (워크트리 `task_109`) | brain 조회 1회 | `{"ok":false,"error":"brain_not_initialized","brain_path":"<worktree>/.opal/brain"}` — 9번째 조립 지점 실증 |
| E1-7 | `ls -la .opal-worktrees/task_109` (허브) | 워크트리 루트 1-depth | `.git` **파일 78바이트** · `CLAUDE.md` **0바이트 파일** — `findProjectRoot` 조기 종료 원인 |

---

## 9. 리스크 및 대응
| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | 3구현이 갈라져 런타임 간 데이터 원천이 분기(H-1) | F-002 | 상 | 골든 표 SSOT 1파일 + 3스위트가 각자 읽어 대조. 표 복제 금지 |
| R-2 | 허브 실행 출력이 흔들려 「바이트 동일」 위반(H-2) | F-002·F-003 | 상 | 정규화를 순수 문자열 함수로 두고 진입점 1곳에만 삽입. 허브 `validate` 출력 전후 대조를 Step 11 완료 기준에 포함 |
| R-3 | 명시 `--brain-path` 정규화로 격리 테스트가 실 brain을 오염(H-3) | F-003 | 상 | 기본값 `"."` 경로에만 적용. brain-tool 142건 회귀 0을 완료 기준으로 고정 |
| R-4 | 2단 열거로 늘어난 모수가 다른 단정을 깨뜨림(H-4) | F-005 | 중 | E1-2로 항등·하한 단정 통과를 사전 실측. `test_scanner.py` 합성 픽스처 불변 확인 |
| R-5 | 배포본(`~/.opal/`) 미갱신으로 brain-tool sync-header 경로가 구 동작 유지 | F-003 | 중 | EXECUTE 구간 install 금지(§3.3.4). 검증은 워크트리 소스 직접 실행. 재배포는 머지 후 CLOSE 판단 |
| R-6 | 워커가 「워크트리에서 validate 통과 = 내 변경 검증됨」으로 오해(H-9) | F-003 | 중 | F-001 문서 5항에 의미 한계 명시 + Step 11 완료 기준에 문구 반영 |
| R-7 | 신규 파일이 `@header` 없이 들어가 `newly_uncovered` 차단으로 승격(H-10) | F-002 | 중 | 신규 3파일 `@header` 보유를 Step 1·2·4 완료 기준으로 못박고 Step 14에서 차단 건수 불변 확인. 근거: `code-scan.js:classifyUncovered` — HEAD에 파일이 없으면 `newly_uncovered` |
| R-8 | 선재 실패 귀속이 틀려 잔여 실패가 남음(H-11) | F-006 | 중 | E1-1·E1-2로 귀속을 이미 실측(7 = 위치 유래 / 2 = 시점 유래). Step 14에서 9건 개별 실행 대조, 잔여 1건이라도 있으면 중단·보고 |
| R-9 | 단언 교정이 reward hacking으로 보임(H-8) | F-006 | 상 | 교정을 RED 구간 1회로 한정, 동결값 425/799 단정을 유지, `STATS-BASELINE.md` §6.1 [MUST] 인용을 코드 주석에 남긴다. GREEN 루핑 중 테스트 수정 금지(red-first.md §3) |
| R-10 | S-31 대상 태스크가 삭제되면 영구 실패(H-6) | F-004 | 하 | 0건 매칭 시 실패 메시지에 대체 fixture 선정 안내를 넣어 후속이 즉시 판단하게 한다(단언 강도는 유지) |
| R-11 | R-6·R-8 신설로 TASK.md 요구사항 표와 PLAN이 불일치 | F-005·F-006 | 중 | **해소(2026-09-07)** — TASK.md에 R-8 신설. 아울러 초판 「R-7 신설」이 FE `@header` 정비의 R-7과 **ID 충돌**이었음을 발견해 R-8로 재배정하고, TASK.md R-7의 AC(a)(b)(d)를 검증하는 TS-027~029를 신설했다(초판은 AC(c)만 커버) |
| R-12 | `improve_tool.py:138`·`tool_scan.py:549`의 `cwd()` 파생이 미수렴 잔존 | 범위 밖 | 하 | TASK.md 확정 범위(9곳)를 넘으므로 본 태스크에서 다루지 않는다. 별건 백로그로 보고 — **미확인**: 두 지점이 워크트리에서 실제로 문제를 일으키는지는 검증하지 않았다 |

---

## PLAN 개정 — 목표-커버 게이트 iteration 1·2 반영 (2026-09-07 14:30)

목표-커버 게이트가 PLAN §3.5.5·TS-023 행의 AC 문자 어긋남을 **상류 원천**으로 지목했다(iteration 2 G-5). **하류만 고치면 같은 드리프트가 재발한다** — PLAN이 TS 도출의 상류이므로 여기서 정렬한다.

| 지점 | 변경 |
|------|------|
| §3.5.5 R-6 TS 표 | AC 문자 재정렬 — TS-040은 `AC(a)`가 아니라 「열거 항등」, TS-041→`AC(d)`, TS-042→`AC(c)(d)`, TS-043→`AC(e)`, TS-044→「doctor」. `TASK.md:132` 원문 대조 결과 |
| §3.5.5 R-6 TS 표 | **TS-047 신설** — `AC(a)(b)`(함수 1개 + 3지점이 그것만 호출 + 잔여 직접 열거 0건)를 단정하는 TS가 없었다 |
| TS-023 행 | 「워크트리·허브 양쪽 exit 0」 → 워크트리 한정 + 허브는 TS-071로 이연. 허브는 머지 전 브랜치 코드를 보지 못한다 |
| TS-023 행 아래 | **TS-071 신설** — 허브 목표 도달(CLOSE 게이트 시점) |

> 게이트 최종 판정: iteration 2 `verdict: pass` (① 목표 2 / ⑤ 채택 2 / ⑥ 경계 2, 평균 2.0). 시나리오 40건.

### 소유자 결정 3건 반영 (2026-09-07 14:40)

`test_scenario.user_confirm` 행에서 캡틴이 결정한 3건. **모두 범위·시점 결정이라 PM이 정할 수 없는 항목이었다.**

| 결정 | 선택 | 반영 |
|------|------|------|
| **skip 범위** | **skip 0 목표로 편입** | R-4 **AC(e) 신설** + TS-035 강화(「skip 수 동일」 → 「양쪽 `0 skipped`」) + §2.3에 skip 사유 실측 표. 허브가 스스로 `test_adapters.py:88`을 skip 중이며 그 사유가 이 태스크가 고치는 하드코딩이다 — **허브에서 테스트 1건이 조용히 안 돌고 있었다** |
| **허브 검증 시점** | **머지 후 push 전, 실패 시 `git reset --hard`** | TS-071 조건·기대 결과에 절차 명기. 예행이 아니라 실전 조건 검증이면서 완전 롤백이 가능하고, 원격에는 통과한 상태만 올라간다 |
| **TS-061 (L3)** | **유지** | 변경 없음. TEST 단계에서 PM 표준 요청 양식으로 발신 |

### R-4 AC(d) 미매핑 — G-4와 같은 유형을 하나 더 발견

결정 반영 중 R-4 AC 문자를 `TASK.md:131` 원문과 대조하니 **AC(d)가 §4 매핑 표에 없었다.** AC(d)는 「console BE 9건 중 **집계 의존 5건**은 하드코딩 제거로 풀리지 않으므로 별도 처방을 PLAN이 설계한다」이고, PLAN의 처방은 R-6 2단 열거다 — 따라서 **TS-041·TS-042**가 그 AC의 검증자다.

G-4(R-6 AC 어긋남)를 고치면서 **R-4는 대조하지 않았다.** 같은 실수가 다른 요구사항에 그대로 있었다. AC 문자 정합은 요구사항 단위로 전건 대조해야 한다 — 한 곳을 고쳤다고 나머지가 정렬되지 않는다.

