# PLAN: 미전환 6 pilot 파이프라인 스펙 마이그레이션 (10/10 완전 전환)

> 작성일: 2026-08-13 | 개정: v2.3 (opsdd 포함 — 캡틴 최종 확정 D-7, **제외 pilot 없음**)
> 입력: TASK.md (ANALYSIS.md 없음 — Short Task, 코드 분석 직접 수행)
> 모드: Multi-Feature (F-001 / F-003 ~ F-007)
> 실행 모드: **복잡** (§6)

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

미전환 **6종 전부**(`opdd`·`opgc`·`opwt`·`opsdd`·`oppl`·`oppd`)의 파이프라인 행 구성을 각 스킬의 `references/pipeline.json`으로 이관하고, `state-tool init --rows-from` 인자를 `.md` → `.json`으로 전환한다. 함께 registry `pipeline` 필드 10종을 정합화하고 oppd `domain` 결측을 보강한다. 행 구성은 전후 동등해야 한다 (TASK.md D-4).

**목표 상태 — 10/10 완전 전환.** 이번 태스크로 (1) `init` 불가 pilot이 **0개**가 되고, (2) deprecated `build_rows_from_skill_md` 경로를 지시하는 pilot이 **0건**이 된다. **제외 pilot은 없다** (TASK.md D-7).

**oppl·oppd는 이관과 동시에 결함 해소를 겸한다** — 두 pilot 모두 현재 `init --rows-from .../SKILL.md`가 `skill_md_parse_error`로 하드 실패해 **태스크 시작 자체가 불가능**하다 (D-7a·D-7b / R-8).

**PLAN 각 차수에서 실측한 사실 4건**

| # | 실측 결과 | 근거 | 이번 태스크 취급 |
|---|----------|------|----------------|
| N-1 | **`oppd`는 파이프라인 행 표 자체가 없다.** SKILL.md에 `\| # \| 단계 \| 항목 \|` 표도, `STATE.md 도메인 치환값` 헤더도 없다. 현재 `init --rows-from .../SKILL.md`는 `skill_md_parse_error / header not found`로 **하드 실패**한다 | `build_rows_from_skill_md` 직접 호출 프로브 결과 `ERR-EXIT` / `opal/skills/opal-pilot-project-dev/SKILL.md:115` | **포함.** 행 표는 없지만 **실사용 선례 8행(PM 제공)**이 존재해 baseline이 확정되었다. 표준화 판단 3건을 적용한 **D-7b 확정 13행**을 그대로 이관한다(§2.1.6). 전환으로 하드 실패도 해소(F-007) |
| N-2 | **`oppl`은 19행 표를 온전히 보유하지만 파서가 검출하지 못한다.** 원인은 데이터가 아니라 **명명**이다 — ① 섹션 헤더가 `## STATE.md 초기 생성`(`SKILL.md:121`), ② 표 헤더가 `\| # \| Stage \| 항목 \|`(`:137`). **③ 행 정규식(`state_tool.py:816-820`)은 19건 정상 매칭** | `state_tool.py:778-806` / 행 표 원문 `SKILL.md:137-157` | **포함.** baseline은 SKILL.md 표 19행을 행 정규식으로 직접 추출한 것이다(§2.1.5, D-7a). 전환으로 하드 실패도 해소(F-007) |
| N-3 | **파서 동작 3종(opdd 15행 / opgc 7행 / opwt 10행)은 `.md` 파싱이 정상 동작한다** | `build_rows_from_skill_md` 직접 호출 프로브 결과 (§2.1.3에 원문 박제) | **포함 — 기계적 이관** |
| N-4 | **`opsdd`도 `.md` 파싱이 정상 동작한다 — 25행 추출 성공.** stage 분포 `TASK 3 / SPEC 4 / REVIEW 6 / DESIGN 4 / EXECUTE 3 / VERIFY 4 / CLOSE 1`, **STAGE_ENUM 미등록 stage 0건**. 행 표의 stage는 이미 `EXECUTE`이며 `EXECUTE-LOOP`이 아니다 | 파서 직접 실행 검증(PM) + `build_rows_from_skill_md` 프로브 결과 (§2.1.4에 원문 박제) / `state_tool.py:31-39` | **포함 — 파서 동작 3종과 동일한 기계적 이관.** `meta.stages`에 `EXECUTE`를 쓰고, **산문의 `EXECUTE-LOOP` 표기 17곳은 일절 건드리지 않는다**(D-7c, §2.1.4) |

> **N-4 정정 안내** — PLAN v2.0~v2.2에서 opsdd를 "`EXECUTE-LOOP` 라벨 드리프트 동반"으로 분류해 제외했으나, 캡틴 최종 확정으로 그 판단이 뒤집혔다. **`EXECUTE-LOOP`은 드리프트가 아니라 Phase 이름**이고 `EXECUTE`는 stage 값으로 서로 다른 개념이다 — `opd`의 `STEP 3.5 TEST-SCENARIO`, `oppd`의 `Phase 2: WBS`와 동일 패턴이다 (D-7c). 따라서 이관은 순수 기계 작업이고, 산문 표기는 변경 대상이 아니다.

**baseline 원천이 3그룹으로 갈린다** — 이것이 §2·§3의 소절 분기 기준이다.

| 그룹 | pilot | baseline 원천 | 대조 방식 |
|------|-------|--------------|----------|
| **A** | opdd(15) · opgc(7) · opwt(10) · **opsdd(25)** | `build_rows_from_skill_md` 직접 호출 결과 (파싱 성공) | before rows[] ↔ after rows[] |
| **B** | oppl(19) | SKILL.md `:139-157` 표에 행 정규식 직접 적용 (파서 init은 실패) | 추출 19행 ↔ `task_steps` ↔ after rows[] |
| **C** | oppd(13) | **TASK.md D-7b 확정표** (실사용 선례 8행 + 표준화 판단 3건) | D-7b 13행 ↔ `task_steps` ↔ after rows[] |

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | 미전환 6 pilot pipeline.json 신설 — 전후 동등 이관 | R-1 | P0 | 없음 |
| F-003 | 6 pilot SKILL.md `init` 인자 `.md`→`.json` 전환 + 미러 주석(oppd는 미러 표 신설) + 변경이력 | R-2, R-3 | P0 | F-001 (pilot 단위 같은 디스패치에서 순차 편집) |
| F-004 | registry `pipeline` 필드 **10종** 정합화 + oppd `domain` 보강 | R-4 | P1 | F-001 (`meta.stages` 확정 후) |
| F-005 | 전후 동등 실증 + `spec-validate` 10건 + 잔존/채택 검증 + 임시 산출물 정리 | R-5, R-6 | P0 | F-001, F-003, F-004 |
| F-006 | opsdd `EXECUTE-LOOP` 산문 무변경 보장 | R-7 | P0 | F-005와 동시 검증 |
| F-007 | oppl·oppd `init` 하드 실패 해소 실증 | R-8 | P0 | F-001, F-003 (oppl·oppd분) |
| F-008 | **레포 전역 구형 지시 정정** — pilot 밖 4곳(`tools.md` 2 · `task-process.md` 1 · `op-task/SKILL.md` 1) | R-9 | P0 | 없음 (다른 F와 파일 비중첩) |

> **F-002는 삭제 상태를 유지한다.** 1차 PLAN의 F-002("oppl·oppd pipeline.json 신설")는 v2.0에서 범위 제외로 삭제되었고, v2.1(oppl)·v2.2(oppd)에서 각각 **F-001로 흡수**되었다. **번호는 추적성 유지를 위해 재사용하지 않는다.**
> **F-006은 v2.3에서 의미가 바뀌었다.** v2.0~v2.2의 "제외 pilot 무변경 보장"에서 **"opsdd 산문 `EXECUTE-LOOP` 무변경 보장"**으로 재정의했다 — 제외 pilot이 사라졌기 때문이다.

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 (6 pilot pipeline.json)
   │  └─(pilot 단위 동일 디스패치)─→ F-003 (SKILL.md 전환)
   │                                    │
   │                                    ├─(oppl·oppd분)─→ F-007 (하드 실패 해소 실증)
   │                                    └─(opsdd분)────→ F-006 (EXECUTE-LOOP 무변경)
   │
   └──────────────→ F-004 (registry 10종 + oppd domain) ──→ F-005 (전수 검증·정리)
                                                              ↑
F-008 (pilot 밖 구형 지시 4곳 정정) ───────────────────────────┘
      · 독립 파일 3개 — 다른 F와 비중첩, Batch 1 병렬 편입
      · F-005의 "레포 전역 잔존 스캔"이 이 결과를 검증
```

> F-001과 F-003은 서로 다른 파일을 만진다(`references/pipeline.json` 신규 vs `SKILL.md` 수정). 다만 pilot 단위로 정합성이 강결합이므로 §4.2에서 **pilot별 1 Step**으로 묶어 순차 편집한다 (`opal/core/references/pm/dispatch-process.md` §Step 6 항목 5 — 동일 파일 다중 Step 금지·비중첩 분할).

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨. v2.3 범위(6 pilot)에 맞춰 H-ID를 H-1부터 연속 재부여했다.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-001 / 그룹 A 4종 | **전후 동등 파괴** — `task_steps[]`의 개수·순서·`stage`·`item` 중 하나라도 baseline과 달라지면 pilot STATE 골격이 조용히 바뀐다. `item`에 공백·괄호·특수문자(opgc의 `{ts}`·`[-{element}]`, opwt의 `작업 (Batch 동적 삽입)`, opsdd의 `구조 검증 (S-1~S-6)`·`커버리지 게이트 (scenario-coverage-check)`)가 있어 오타 유입 확률이 높다 | **P0** | L1(문자열 완전 일치 대조) + L2(실 init rows[] 대조) | S-후보: opdd 15 / opgc 7 / opwt 10 / opsdd 25행의 `[(row_id, stage, item)]`이 before와 완전 동일 |
| H-2 | F-001 / opsdd `meta.stages` | **`EXECUTE-LOOP` 오기입** — SKILL.md `:332` "단계 목록" 줄이 `TASK / SPEC / REVIEW / DESIGN / EXECUTE-LOOP / VERIFY / CLOSE`라서 워커가 그 라벨을 `meta.stages`에 옮길 수 있다. `EXECUTE-LOOP`은 **STAGE_ENUM 미등록**이고 실제 행 stage는 `EXECUTE`다. 오기입 시 F-004 registry 값까지 연쇄 오염된다 (D-7c 위반) | **P0** | L1(`meta.stages` 파생 규칙 대조 + `spec-validate`) | S-후보: opsdd `meta.stages` == `["TASK","SPEC","REVIEW","DESIGN","EXECUTE","VERIFY","CLOSE"]`, `EXECUTE-LOOP` 문자열 미포함 |
| H-3 | F-006 / opsdd 산문 | **`EXECUTE-LOOP` 개명 연쇄** — 워커가 "라벨 정합"을 이유로 산문의 `EXECUTE-LOOP`을 `EXECUTE`로 바꾸면 **8개 파일 41곳**이 연쇄된다: `references/execute-loop-guide.md`(**파일명 자체 포함**), brain 페이지 3종, README, `docs/ARCHITECTURE.md`, 다이어그램 HTML, `opal/core/references/opal-harness-semi-agentic.md:32`(모드 경계 SSOT), `opal/skills/op-sdd-plan/SKILL.md`. 형식 이관이 문서 개편으로 변질된다 | **P0** | L1(등장 횟수 전후 동일 + 외부 파일 diff 0) | S-후보: opsdd SKILL.md `EXECUTE-LOOP` 등장 **17회 전후 동일**, `execute-loop-guide.md` 변경 0건, 외부 6개 파일 변경 0건 |
| H-4 | F-001 / opsdd pipeline.json | **최장 배열의 `id` 순차·`key` 유일성 위반** — opsdd 25행은 대상 중 가장 길고, `PM Gate`·`사용자 확인`·`워커 디스패치`가 여러 stage에 반복 등장한다. 수기 번호 중복·누락(검사 ⑥)과 key 충돌(검사 ⑤) 위험이 가장 크다 | P1 | L1(`spec-validate`) | S-후보: opsdd `spec_id_sequence_invalid`·`spec_key_duplicate` 0건, `task_steps` 길이 25 |
| H-5 | F-001 / oppl pipeline.json | **oppl baseline 도출 오류** — oppl은 `.md` init이 하드 실패해 **파서 before가 없다**. SKILL.md 표 19행을 추출해 이관하므로 행 누락·중복·순서 뒤바뀜이 발생해도 before/after 자동 대조로는 잡히지 않는다 | **P0** | L1(행 정규식 추출 ↔ `task_steps` 프로그램 대조) + L2(실 init `rows_count: 19`) | S-후보: `state_tool.py:816-820` 행 정규식으로 `SKILL.md:139-157`에서 추출한 19행 == `task_steps` 19개 |
| H-6 | F-001 / oppl pipeline.json | **`item` 특수문자 원문 훼손** — oppl 19행에는 백틱(`` `references/journey-flow.md` ``), 전각 대시(`—`), 체크마크(`✓`), 플레이스홀더(`{NN}`), 소수점 ID(`D1.5`)가 섞여 있다. JSON 인코딩 중 이스케이프·정규화·자동 교정이 일어나면 문자열이 달라진다 | P1 | L1(문자 단위 완전 일치) | S-후보: 19행 `item`이 SKILL.md 원문과 바이트 단위 동일 |
| H-7 | F-001 / oppd pipeline.json | **D-7b 확정표 이탈** — oppd는 SKILL.md에 행 표가 없어 워커가 "설계 여지"로 오인하고 행을 가감·재설계할 수 있다. 확정 13행은 **실사용 선례 8행 + 캡틴 승인 표준화 판단 3건**의 결과이며 재해석 대상이 아니다 (제약 (g)) | **P0** | L1(D-7b 표 ↔ `task_steps` 문자 단위 대조) | S-후보: `task_steps` 13개의 `id`·`key`·`stage`·`item`이 TASK.md D-7b 표와 완전 일치 |
| H-8 | F-003 / oppd SKILL.md | **미러 표 신설분과 pipeline.json 불일치** — oppd만 SKILL.md에 행 표를 **새로 만든다**(다른 5종은 기존 표에 주석만 추가). 두 곳을 각각 손으로 쓰면 초기부터 미러가 어긋난 채 고정된다 | P1 | L1(SKILL.md 표 ↔ pipeline.json 대조) | S-후보: oppd SKILL.md 미러 표 13행 == `task_steps` 13개 |
| H-9 | F-001 / opdd pipeline.json | **`stage` slug 처리 실패** — opdd만 `stage`에 `/`가 들어간다(`DDL/MIGRATION`). `stage_to_slug`는 `-`·`/`를 `_`로 치환하므로(`state_tool.py:44-46`) key는 `ddl_migration.*`여야 한다. 그대로 두거나 `ddl/migration`으로 쓰면 검사 ③·⑦ 동시 실패 | P1 | L1(`spec-validate`) | S-후보: `spec_stage_invalid`·`spec_key_stage_mismatch` 0건 |
| H-10 | F-001 / 6 pilot pipeline.json | **`key` 패턴 위반** — `^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*(_[0-9]+)?$`. 한글 `item`을 영문 slug로 변환하므로 대문자·하이픈·공백 혼입 위험 | P1 | L1(`spec-validate`) | S-후보: `spec_key_format_invalid` 0건 (6 파일 전부) |
| H-11 | F-001 / opwt `meta.stages` | **`meta.stages` 파생 원천 모호** — opwt SKILL.md `:423`의 "단계 목록" 줄은 `TASK → ANALYSIS → PLAN → EXECUTE → QA → CLOSE (모드에 따라 일부 생략)`이지만, 기본 작성 모드 행 10개에는 `ANALYSIS`가 없다. 라벨 줄을 그대로 옮기면 F-004 registry 값까지 틀어진다 (H-2와 같은 부류) | P2 | L1(파생 규칙 대조) | S-후보: `meta.stages` == 해당 `task_steps[].stage`의 등장순 중복 제거 |
| H-12 | F-004 / `opal-skills-registry.json` | **registry 표기 형식 미결정** — 현행 10건이 서로 다른 형식(단계 나열 / `PLAN+TEST-SCENARIO` 합성 / `Phase 1~4 …` 자연어 / 루프 서술 / 존재하지 않는 단계명 / **결측**)을 혼용한다. 형식을 정하지 않으면 R-4 AC를 기계 검증할 수 없다 | P2 | L1(파생 규칙 대조 스크립트) | S-후보: 10건 `pipeline` 문자열 `" → "` split == 해당 `meta.stages` |
| H-13 | F-003 / 6 SKILL.md | **`--rows-from` 잔존** — 대상 6종에 init 지시가 중복 등장한다(opdd 3 / opgc 5 / opwt 6 / opsdd 6 / oppl 3 / oppd 2회, 변경이력 포함). 일부만 고치면 R-2 AC 미달이거나 문서 내 지시가 서로 모순된다 | P1 | L1(grep 전수) | S-후보: 6 파일에서 `rows-from.*SKILL.md`가 `## 변경이력` 밖 0건 |
| H-14 | F-005 / 검증 절차 | **임시 산출물 레포 잔류** — 동등 검증은 `init`을 실제 실행해 `state.json`+`STATE.md`를 만든다. 레포 안에서 실행하면 트리가 오염되고, 최악의 경우 기존 태스크의 `state.json`을 덮어쓴다(제약 (d) 위반) | **P0** | L2(실행 전후 `git status` 대조) | S-후보: 검증 후 `git status --porcelain`에 임시 파일 0건 |
| H-15 | F-001~F-003 전반 | **배포 경계 위반** — `~/.opal/skills/*/references/pipeline.json`을 직접 만들면 소스와 배포본이 갈라진다 | P1 | L1(변경 파일 경로 검사) | S-후보: 변경 파일이 전부 `opal/`·`docs/`·`tasks/` 하위 |
| H-16 | F-003 / oppl SKILL.md | **범위 밖 개명 유혹** — oppl의 파서 미검출 원인이 명명이므로, 워커가 "결함 해소"를 이유로 `## STATE.md 초기 생성` → `## STATE.md 도메인 치환값`, `\| # \| Stage \|` → `\| # \| 단계 \|` 로 개명할 수 있다. **범위 밖이며 금지**다 — 미러 표가 되면 파서 매칭이 불필요하다 | P2 | L1(diff 검사) | S-후보: oppl `SKILL.md:121` 헤더와 `:137` 표 헤더가 diff에 나타나지 않음 |
| H-17 | F-001 / oppd 런타임 | **`--wbs` 플래그 경로에서 EXECUTE 3행 미완 잔존** — oppd `--wbs`는 Phase 3을 실행하지 않고 종료한다(`SKILL.md:153`). 확정 13행 중 id 10~12(EXECUTE)가 `pending`으로 남아 stage-transition guard가 CLOSE 진입을 차단할 수 있다 | P2 — 운영 마찰 | L2(`--wbs` 시나리오) | S-후보: `--wbs` 경로에서 id 10~12를 `mark --na` 처리하면 CLOSE 진입이 허용된다 (표준화 판단 ③ 검증) |
| H-18 | F-008 / pilot 밖 문서 4곳 | **pilot 밖 구형 지시 잔존** — 잔존 검증이 `opal/skills/opal-pilot-*/SKILL.md`로 한정되면 pilot 밖에 살아 있는 `.md` 파싱 지시를 놓친다. 특히 `opal/core/references/tools.md:152`는 **이미 전환된 opp를 구형 경로로 지시하는 실행 예시**라 지금 그대로 복사·실행하면 deprecation 경고가 뜨고 `key` 결손 `state.json`이 만들어진다. `tools.md:84` 시놉시스는 `.md`를 기대 인자로 표기하고, `task-process.md:49`·`op-task/SKILL.md:223`은 행 원천을 SKILL.md 표로 지시한다. 4곳을 두면 "10/10 전환"이 **pilot 안에서만 참**이 된다 | **P0** | L1(레포 전역 grep, 도구 자신 2파일 제외) | S-18: 4곳 정정 확인 + `state_tool.py`·`state-tool/README.md` **역방향 무변경** |

---

## 2. 기능별 분석

### F-001: 미전환 6 pilot pipeline.json 신설

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/opal-pilot-data-design/references/pipeline.json` | opdd 행 SSOT (15행) | 신규 |
| 스킬 | `opal/skills/opal-pilot-gc/references/pipeline.json` | opgc 행 SSOT (7행) | 신규 |
| 스킬 | `opal/skills/opal-pilot-write-tech/references/pipeline.json` | opwt 행 SSOT (10행) | 신규 |
| 스킬 | `opal/skills/opal-pilot-sdd/references/pipeline.json` | opsdd 행 SSOT (25행) | 신규 |
| 스킬 | `opal/skills/opal-pilot-project-loop/references/pipeline.json` | oppl 행 SSOT (19행) | 신규 |
| 스킬 | `opal/skills/opal-pilot-project-dev/references/pipeline.json` | oppd 행 SSOT (13행) | 신규 |
| 배치 | `opal/tools/state-tool/state_tool.py` | 파싱·검증 계약 (읽기 전용, **무변경**) | 없음 |
| 배치 | `opal/tools/state-tool/schema/state.schema.json` | `stage` enum 19종 / `skill` enum 10종 | 없음 |
| 스킬 | `opal/skills/opal-pilot-dev/references/pipeline.json` | 구조 견본 (전환 완료) | 없음 |

#### 2.1.2 현재 구현

**파싱 경로 2종의 계약 차이** — `cmd_init`은 `--rows-from` 확장자로 분기한다 (`opal/tools/state-tool/state_tool.py:1126-1133`).

| 항목 | `.md` 경로 `build_rows_from_skill_md` (`:768-858`) | `.json` 경로 `build_rows_from_pipeline_json` (`:937-972`) |
|------|--------------------------------------|-------------------------------------|
| 입력 | SKILL.md 정규식 파싱 (헤더 → 표 헤더 → 행) | `spec["task_steps"]` 배열 |
| 산출 row 필드 | `row_id, stage, item, status, status_label, timestamp, owner, note` | 위 8종 + **`key`** (+ `conditional` 조건부) |
| `row_id` | 표의 `#` 열이 아닌 **열거 인덱스 `i+1`** (`:842`) | 동일하게 `i+1` (`:951`) |
| `status` 초기화 | 표의 상태 이모지를 읽되 **전부 `pending`으로 덮어씀** (`:844-845`) | 전부 `pending` (`:955-956`) |
| `owner` | 하드코딩 `"PM"` (`:847`) | 하드코딩 `"PM"` (`:958`) |
| agentic 자동 na | `item == "사용자 확인" and stage != "CLOSE"` (`:851-855`) | **동일 규칙** (`:965-969`) |
| 사전 검증 | `stage ∈ STAGE_ENUM`만 (`:833-836`) | `validate_pipeline_spec` 7종 전수 (`:944-946`) |
| `schema_version` | `"1.0"` | `key` 존재 → **`"1.1"` 승격** (`:1139`) |
| 표준 출력 | `{"warning":"--rows-from <SKILL.md> markdown 파싱은 deprecated..."}` 1줄 선출력 (`:1131`) | 없음 |

> **[MUST]** 전후 동등의 판정 축은 `row_id`·`stage`·`item` 3종이다 — `key` 신설과 `schema_version` 1.0→1.1 승격은 `.json` 경로의 **의도된 추가 산출**이며 동등성 위반이 아니다 (TASK.md R-5 AC).

**`.md` 파서의 3단 관문** — 어느 pilot이 왜 실패하는지를 결정하는 구조다.

| 관문 | 정규식 | 위치 | 그룹 A(opdd·opgc·opwt·opsdd) | oppl | oppd |
|------|--------|------|------------------------------|------|------|
| ① 섹션 헤더 | `^(##\|###\|####)\s+.*STATE\.md\s*도메인\s*치환값.*$` | `:778-781` | ✅ 4종 모두 보유 | ❌ `## STATE.md 초기 생성` (`:121`) | ❌ 해당 헤더 없음 |
| ② 표 헤더 | `^\|\s*#\s*\|\s*(?:단계\|Phase)\s*\|\s*항목\s*\|` | `:799-802` | ✅ (opsdd는 `Phase` 열) | ❌ `\| # \| Stage \| 항목 \|` (`:137`) | ❌ 행 표 없음 |
| ③ 행 | `^\|\s*(\d+)\s*\|\s*([^\|]+?)\s*\|\s*([^\|]+?)\s*\|\s*([⬜🔄✅❌\-])\s*\|` | `:816-820` | ✅ 15/7/10/25행 | ✅ **19건 정상 매칭** | — |

> opsdd는 표 헤더가 `| # | Phase | 항목 |`(`SKILL.md:356`)이라 정규식의 `(?:단계|Phase)` 대안에 걸려 정상 통과한다. oppl의 `Stage`만 걸리지 않는다.

**`validate_pipeline_spec` 7종 검사** (`state_tool.py:875-934`) — 신설 6파일 + 기존 4파일이 전부 통과해야 한다 (R-6).

| # | 검사 | 에러 코드 | 신설 시 유의점 |
|---|------|----------|--------------|
| ① | `spec_version`/`skill`/`meta`/`task_steps` 존재 (`:890`) | `spec_missing_field` | 4종 모두 최상위 필수. 하나라도 빠지면 하위 검사 조기 반환 (`:894-896`) |
| ② | `skill ∈ ["opp","opd","opds","opdw","opwt","opgc","oppd","opsdd","oppl","opdd"]` (`:898`) | `spec_skill_invalid` | 대상 6종 모두 기등록 — 도구 변경 불필요 |
| ③ | `task_steps[].stage ∈ STAGE_ENUM` (`:909`) | `spec_stage_invalid` | H-2·H-9. **`EXECUTE-LOOP`은 미등록** — opsdd에 쓰면 즉시 실패 |
| ④ | `key` 정규식 (`:914`) | `spec_key_format_invalid` | H-10 |
| ⑤ | `key` 스펙 내 유일 (`:917`) | `spec_key_duplicate` | H-4. opsdd 25행이 최대 위험 |
| ⑥ | `id == idx+1` (`:930`) | `spec_id_sequence_invalid` | H-4 |
| ⑦ | `key`의 stage_slug == `stage_to_slug(stage)` (`:923-928`) | `spec_key_stage_mismatch` | `stage_to_slug`는 소문자화 + `-`·`/` → `_` (`:44-46`) — opdd 3행이 최대 위험 |

**`meta`는 도구가 읽지 않는다** — `state_tool.py` 전체에서 `meta.` 접근이 0건이고, `validate_pipeline_spec`은 `meta` 키의 **존재만** 확인한다 (`:890`). 즉 `meta.mode_label`·`meta.stages`는 사람·PM 프롬프트용 문서 필드다. 이것이 F-004의 `meta.stages` 파생 규칙을 문서로 고정할 수 있는 근거다 (H-2·H-11 대응).

#### 2.1.3 baseline (그룹 A-1) — opdd·opgc·opwt 실측 원문

> 아래 표들은 `build_rows_from_skill_md(SKILL.md, "init", "semi-agentic")`를 직접 호출해 얻은 `[(row_id, stage, item)]` 원문이다. **이 표가 기준값이며, `task_steps[]`는 이와 문자 단위로 일치해야 한다** (D-4).

**opdd — 15행** (원천: `opal/skills/opal-pilot-data-design/SKILL.md:245-260`)

| # | stage | item |
|---|-------|------|
| 1 | TASK | 작업 |
| 2 | TASK | 사용자 확인 |
| 3 | DICT | 작업 |
| 4 | DICT | PM Gate |
| 5 | DICT | 사용자 확인 |
| 6 | MODEL | 작업 |
| 7 | MODEL | PM Gate |
| 8 | MODEL | 사용자 확인 |
| 9 | DDL/MIGRATION | 작업 |
| 10 | DDL/MIGRATION | PM Gate |
| 11 | DDL/MIGRATION | 사용자 확인 |
| 12 | QA | 작업 |
| 13 | QA | PM Gate |
| 14 | QA | 사용자 확인 |
| 15 | CLOSE | DONE.md 생성 |

**opgc — 7행** (원천: `opal/skills/opal-pilot-gc/SKILL.md:442-450`)

| # | stage | item |
|---|-------|------|
| 1 | SCAN | 대상 파일 선별 + 스택 감지 + 프로젝트 구성 파싱 |
| 2 | CHECK | 에이전트 (요소×체커) 병렬 디스패치 |
| 3 | CHECK | 에이전트 완료 확인 |
| 4 | REPORT | GC-SECURITY-{ts}[-{element}].md 생성 |
| 5 | REPORT | GC-CONVENTION-{ts}[-{element}].md 생성 |
| 6 | REPORT | 실행 요약 테이블 갱신 |
| 7 | CLOSE | DONE.md 생성 |

**opwt — 10행** (원천: `opal/skills/opal-pilot-write-tech/SKILL.md:444-455`)

| # | stage | item |
|---|-------|------|
| 1 | TASK | 작업 |
| 2 | TASK | 사용자 확인 |
| 3 | PLAN | 작업 |
| 4 | PLAN | PM Gate |
| 5 | PLAN | 사용자 확인 |
| 6 | EXECUTE | 작업 (Batch 동적 삽입) |
| 7 | QA | 작업 |
| 8 | QA | PM Gate |
| 9 | QA | 사용자 확인 |
| 10 | CLOSE | DONE.md 생성 |

#### 2.1.4 baseline (그룹 A-2) — opsdd 25행 + `EXECUTE-LOOP` 취급

**opsdd — 25행** (원천: `opal/skills/opal-pilot-sdd/SKILL.md:358-382`). 파서 직접 실행 결과이며 stage 분포는 `TASK 3 / SPEC 4 / REVIEW 6 / DESIGN 4 / EXECUTE 3 / VERIFY 4 / CLOSE 1`, **STAGE_ENUM 미등록 stage 0건**이다.

| # | stage | item |
|---|-------|------|
| 1 | TASK | TASK.md 작성 |
| 2 | TASK | STATE.md 생성 |
| 3 | TASK | 사용자 확인 |
| 4 | SPEC | 워커 디스패치 |
| 5 | SPEC | SPEC.md 생성 |
| 6 | SPEC | PM Gate |
| 7 | SPEC | 사용자 확인 |
| 8 | REVIEW | 구조 검증 (S-1~S-6) |
| 9 | REVIEW | TEST-SCENARIOS.md 작성 |
| 10 | REVIEW | 커버리지 게이트 (scenario-coverage-check) |
| 11 | REVIEW | 목표-커버 게이트 (op-scenario-gate evaluator) |
| 12 | REVIEW | PM Gate |
| 13 | REVIEW | 사용자 확인 |
| 14 | DESIGN | 워커 디스패치 |
| 15 | DESIGN | SPEC-PLAN.md 생성 |
| 16 | DESIGN | PM Gate |
| 17 | DESIGN | 사용자 확인 |
| 18 | EXECUTE | ACT 실행 (상세: ACT 목록 참조) |
| 19 | EXECUTE | PM Gate |
| 20 | EXECUTE | 사용자 확인 |
| 21 | VERIFY | E2E 테스트 수행 |
| 22 | VERIFY | TS 전체 Green 확인 |
| 23 | VERIFY | PM Gate |
| 24 | VERIFY | 사용자 확인 |
| 25 | CLOSE | DONE.md 생성 |

**`EXECUTE-LOOP` vs `EXECUTE` — 두 개념의 분리 (D-7c)**

| 토큰 | 정체 | 등장 위치 | 이번 태스크 취급 |
|------|------|----------|----------------|
| `EXECUTE-LOOP` | **Phase 이름** (사람이 읽는 산문 라벨) | opsdd SKILL.md 산문 **17곳**(`:332` 단계 목록 줄 포함) + 외부 문서 | **일절 변경하지 않는다** |
| `EXECUTE` | **stage 값** (`state_tool.py` STAGE_ENUM 원소) | 행 표 `:375-377`의 3행 | `meta.stages`·`task_steps[].stage`에 사용 |

- 동일 패턴 선례: `opd`의 `STEP 3.5 TEST-SCENARIO`(산문 STEP 이름) ↔ `TEST-SCENARIO`(stage), `oppd`의 `Phase 2: WBS`(산문 Phase 이름) ↔ `WBS`(stage).
- **[MUST] 개명 금지 근거** — `EXECUTE-LOOP`을 `EXECUTE`로 바꾸면 8개 파일 41곳이 연쇄된다: `opal/skills/opal-pilot-sdd/references/execute-loop-guide.md`(**파일명 자체 포함**), brain 페이지 3종, `README.md`, `docs/ARCHITECTURE.md`, 다이어그램 HTML, `opal/core/references/opal-harness-semi-agentic.md:32`(모드 경계 SSOT), `opal/skills/op-sdd-plan/SKILL.md`. 형식 이관이 문서 개편으로 변질된다 (H-3).
- 따라서 opsdd는 **opdd·opgc·opwt와 완전히 동일한 기계적 이관**이며, 산문은 손대지 않는다.

#### 2.1.5 baseline (그룹 B) — oppl 전용 도출 방식

> **oppl은 `.md` init이 하드 실패하므로 파서 before가 없다.** TASK.md D-7a에 따라 **SKILL.md 행 표 19행을 행 정규식으로 직접 추출한 것**을 baseline으로 삼는다.

**도출 절차 (재현 가능)**
1. `opal/skills/opal-pilot-project-loop/SKILL.md`의 **`:137`(표 헤더) ~ `:157`(19행)** 구간을 읽는다. 데이터 행은 `:139-157`이다.
2. `state_tool.py:816-820`의 행 정규식을 그 구간에 적용한다.
3. 매칭 19건의 그룹 2(stage)·그룹 3(item)을 `.strip()` 한 값이 baseline이다 — 파서가 성공했다면 산출했을 값과 동일한 정규화 경로다.

**oppl — 19행** (원천: `opal/skills/opal-pilot-project-loop/SKILL.md:139-157`). `stage` 8종(TASK/ANALYSIS/PLAN/WBS/REVIEW/EXECUTE/VERIFY/CLOSE)은 전부 STAGE_ENUM 등록값이다.

| # | stage | item |
|---|-------|------|
| 1 | TASK | TASK.md 작성 |
| 2 | TASK | STATE.md 생성 |
| 3 | TASK | 사용자 확인 |
| 4 | ANALYSIS | D1 인터뷰 — 명확화 4요소(목표/범위/제약/완료기준) |
| 5 | ANALYSIS | D1.5 여정 매핑 (조건부 — user-facing 프로젝트만, `references/journey-flow.md`) |
| 6 | PLAN | D2 PRD 작성 |
| 7 | PLAN | D3 TRD 작성 |
| 8 | PLAN | D4 CONTRACT 작성 (`references/contract.md`) |
| 9 | WBS | D5 백로그 생성 (`backlog-tool init`+`add-task`) |
| 10 | REVIEW | D6 Evaluator 설계 검토 (phase: design-review) |
| 11 | REVIEW | PM Gate |
| 12 | REVIEW | D7 사용자 확정 게이트 (4요소 잠김 확인) |
| 13 | EXECUTE | L0 태스크 선택 (상세: 태스크 목록 참조 — `add-row`로 T{NN} 행 동적 삽입) |
| 14 | EXECUTE | PM Gate |
| 15 | EXECUTE | 사용자 확인 |
| 16 | VERIFY | L✓ 종료 판정 (`backlog-tool done-check` all_done + 회귀 0) |
| 17 | VERIFY | PM Gate |
| 18 | VERIFY | 사용자 확인 |
| 19 | CLOSE | DONE.md 생성 |

> 위 표의 백틱·`—`·`✓`·`{NN}`은 **SKILL.md 원문의 문자 그대로**다. 보존 규칙은 §3.1.2 ⑤에 [MUST]로 명시한다 (H-6).

#### 2.1.6 baseline (그룹 C) — oppd 전용 도출 방식

> **oppd는 SKILL.md에 행 표가 없다.** 그러나 **실사용 선례 8행(PM 제공)**이 존재한다 — 해당 구조로 oppd 태스크가 실제 완주(`current_status: done`, 8행 전건 done)된 기록이다. 여기에 캡틴 승인 표준화 판단 3건을 적용해 **13행으로 확정**했다 (TASK.md D-7b).

**표준화 판단 3건**

| # | 판단 | 근거 |
|---|------|------|
| ① | **TASK 2행 추가** (`작업`·`사용자 확인`) | 다른 9 pilot 전부가 TASK 단계 행으로 시작한다. 선례 8행에는 없었으나 일관성 확보 |
| ② | **Phase별 PM Gate 행 분리** (PLAN·WBS·EXECUTE 각 1행) | `opal/skills/opal-pilot-project-dev/SKILL.md:117`: "State Gate/QA Gate 행은 존재하지 않으며(state-tool stage-transition guard로 이전), **PM Gate 단일 mark만 사용한다**" — 이 규정에 부합하는 형태 |
| ③ | **`--wbs` 플래그 경로의 EXECUTE 행은 런타임 `mark --na` 처리** | `SKILL.md:153` `--wbs`는 Phase 1~2 완료 후 종료. 스펙에 `conditional`을 넣지 않고(D-1) 런타임에서 해소한다 (H-17) |

> **[MUST] 제약 (g)**: "oppd 행 구성은 D-7b 확정 13행에서 임의 변경 금지". 확정표는 §3.1.2 ⑥에 그대로 옮긴다. **재설계·가감 금지** (H-7).

**oppd 행 원천의 문서 정합성 확인** — 확정 13행이 SKILL.md 서술과 어긋나지 않음을 대조했다.

| 확정 13행의 stage 축 | SKILL.md 근거 |
|--------------------|--------------|
| PLAN = Phase 1 (PRD/TRD, opwt 위임) | `:139-147` 파이프라인 절 / `:585-590` Phase 진행 현황 표의 `1-PLAN` |
| WBS = Phase 2 (WBS 수립, PM 직접) | 동상, `2-WBS` |
| EXECUTE = Phase 3 (액션 자율 실행) | 동상, `3-EXECUTE` |
| PM Gate 행만 존재 (State/QA Gate 행 없음) | `:117` R-10 비표준 행 구성 규정 |
| TASK·CLOSE 앞뒤 배치 | `:139-147` "태스크 생성(TASK.md + STATE.md) … → DONE.md 작성" |

#### 2.1.7 영향 범위

- **상위 의존(호출자)**: 각 pilot SKILL.md의 `init` 지시 블록 → F-003에서 함께 전환한다.
- **하위 의존(피호출)**: `build_rows_from_pipeline_json` → `load_pipeline_spec` → `validate_pipeline_spec`. 전부 읽기 전용 소비이며 소스 변경 없음 (제약 (a)).
- **공유 상태**: `state.json`의 `schema_version`이 `"1.0"` → `"1.1"`로 바뀐다 (`state_tool.py:1139`). 신규 태스크에만 적용되며 기존 태스크 `state.json`은 소급 변경하지 않는다 (제약 (d)).
- **oppl·oppd 특이사항**: 현재 init이 불가능해 이 레포에는 두 pilot으로 생성된 태스크가 없다 (`tasks/` 전수 확인 — `*-oppl-*`·`*-oppd-*` 폴더 0건). 회귀 대상 자산이 없어 이관 위험이 낮다.
- **opsdd 특이사항**: `.md` 경로가 정상 동작 중이므로 **전환 실수 시 회귀가 실재한다**. 그룹 A 대조로 방어한다.
- **배포**: `install-mac.sh:1061-1068`이 `opal/skills/*`를 디렉토리 단위(`install_dir`)로 복사하므로 `references/pipeline.json` 신설 파일은 install 목록 수정 없이 자동 배포된다.
- **관련 테스트**: 전용 테스트 파일 없음. 검증은 F-005의 `spec-validate` + 실 `init` 대조로 수행한다.

---

### F-003: 6 pilot SKILL.md init 인자 전환 + 미러 주석

#### 2.3.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 오케스트레이터 | `opal/skills/opal-pilot-data-design/SKILL.md` | init 호출 2곳 + 미러 문구 1곳 + 변경이력 | 수정 |
| 오케스트레이터 | `opal/skills/opal-pilot-gc/SKILL.md` | init 호출 3곳 + SSOT 문구 1곳 + 미러 문구 1곳 + 변경이력 | 수정 |
| 오케스트레이터 | `opal/skills/opal-pilot-write-tech/SKILL.md` | init 호출 3곳 + SSOT 문구 1곳 + 미러 문구 1곳 + 변경이력 | 수정 |
| 오케스트레이터 | `opal/skills/opal-pilot-sdd/SKILL.md` | init 호출 2곳 + SSOT 문구 1곳 + 미러 문구 1곳 + 변경이력. **`EXECUTE-LOOP` 산문 17곳 불가침** | 수정 |
| 오케스트레이터 | `opal/skills/opal-pilot-project-loop/SKILL.md` | init 호출 2곳 + 미러 문구 1곳 + 오기술 1곳 + 변경이력 | 수정 |
| 오케스트레이터 | `opal/skills/opal-pilot-project-dev/SKILL.md` | init 호출 1곳 + **미러 표 13행 신설** + 미러 문구 + 변경이력 | 수정 |

#### 2.3.2 현재 구현 — `--rows-from` 등장 위치 전수 (grep 실측)

> 변경이력 표 안의 과거 기록 행은 **수정하지 않는다** (이력 개변 금지, TASK.md D-9). 아래 표의 "변경 대상" 열이 편집 범위다.

| pilot | 줄 | 형태 | 변경 대상 |
|-------|----|------|----------|
| opdd | `:75` | 코드블록 init 호출 | ✅ |
| opdd | `:239` | 산문 — "`state init --rows-from <SKILL.md>` 또는 `--rows-spec` 인자의 SSOT" | ✅ (미러 문구로 교체) |
| opdd | `:241` | `[MUST]` 블록 — `--rows-from <SKILL.md 경로>` | ✅ |
| opgc | `:116` | 코드블록 init 호출 | ✅ |
| opgc | `:431` | `[SSOT]` 산문 | ✅ |
| opgc | `:434` | 코드블록 init 호출 | ✅ |
| opgc | `:482` | 코드블록 init 호출 (`--mode agentic`) | ✅ |
| opgc | `:534` | 변경이력 행 | ❌ 보존 (D-9) |
| opwt | `:193` | 코드블록 init 호출 | ✅ |
| opwt | `:428` | `[SSOT]` 산문 — "state-tool은 이 섹션의 `{단계 목록}`을 파싱하여 초기 행을 생성한다" | ✅ (사실과 다름 — §9 참조) |
| opwt | `:431` | 코드블록 init 호출 | ✅ |
| opwt | `:439` | 산문 — "`state init --rows-from <SKILL.md>`의 SSOT" | ✅ (미러 문구로 교체) |
| opwt | `:441` | `[MUST]` 블록 — `--rows-from <SKILL.md 경로>` | ✅ |
| opwt | `:549` | 변경이력 행 | ❌ 보존 (D-9) |
| opsdd | `:336` | `[SSOT]` 산문 — "이 섹션의 파이프라인 현황판 행 테이블을 `--rows-from` 옵션으로 참조" | ✅ |
| opsdd | `:339` | 코드블록 init 호출 | ✅ |
| opsdd | `:351` | 산문 — "**파이프라인 현황판** (`--rows-from` SSOT 표 …)" | ✅ (미러 문구로 교체) |
| opsdd | `:447` | 코드블록 init 호출 | ✅ |
| opsdd | `:536`, `:540` | 변경이력 행 2건 | ❌ 보존 (D-9) |
| oppl | `:126` | 코드블록 init 호출 | ✅ |
| oppl | `:133` | 산문 — "**파이프라인 현황판** (`--rows-from` SSOT 표 …)" | ✅ (미러 문구로 교체) |
| oppl | `:442` | 코드블록 init 호출 | ✅ |
| oppd | `:115` | 코드블록 init 호출 | ✅ |
| oppd | `:808` | 변경이력 행 | ❌ 보존 (D-9) |

> 등장 수(변경이력 포함): opdd 3 / opgc 5 / opwt 6 / **opsdd 6** / oppl 3 / oppd 2 — TASK.md R-2 기재값과 일치. 편집 대상은 opdd 3 / opgc 4 / opwt 5 / opsdd 4 / oppl 3 / oppd 1.
> **`--rows-from` 문자열이 없어 grep에 안 걸리지만 정정이 필요한 지점**: oppl `:128` — "`state-tool`이 아래 SSOT 표를 읽어 state.json을 초기화한다"는 **현재도 사실이 아니고**(파서가 실패한다) 전환 후에도 사실이 아니다. opsdd `:342` — "state-tool이 이 파일의 「파이프라인 현황판」 테이블(25행)을 읽어 state.json을 초기화한다"도 전환 후 사실이 아니게 된다. 둘 다 함께 정정한다.

#### 2.3.3 목표 형태 — 전환 완료 4 pilot의 표준 문구

`opd`(`SKILL.md:282-286`)·`opds`(`:254-258`)·`opp`(`:160-164`)·`opdw`(`:188-192`)가 이미 동일 문구를 쓴다. 대상 6종을 이 형태로 통일한다.

```
**진행 현황 행 예시** (아래 표는 사람 열람용 미러 — SSOT는 `references/pipeline.json`. `.md` 파싱은 하위호환 폴백으로만 존치, 편집 금지):

> **[MUST] STATE.md 초기 생성**: `~/.opal/tools/state-tool/run.sh init <task-path> --skill {alias} --mode <interactive|semi-agentic|agentic> --rows-from opal/skills/{skill-dir}/references/pipeline.json` 호출. 기본값: `semi-agentic`. 행 구성 SSOT는 `references/pipeline.json`(task-step key 포함) — `--rows-from`이 확장자로 분기해 파싱한다(070).
```

- 경로 표기는 **프로젝트 소스 상대경로**(`opal/skills/...`)를 그대로 쓴다 — 전환 완료 4종과 동일 표기이며, 표기 변경은 "형식 이관" 범위를 벗어난다 (§9 R-8에 관측 사항으로 등재).
- `--mode` 인자가 없던 호출(opgc `:116`·`:434`, opsdd `:339`)은 **기존 형태를 유지**하고 `--rows-from` 값만 교체한다.
- **oppd만 미러 표를 신설**한다. 다른 5종은 기존 표에 문구만 붙인다 (H-8).

> **[MUST 금지] 2건**
> - oppl 섹션 헤더 `## STATE.md 초기 생성`(`:121`)·표 헤더 `| # | Stage | 항목 | 상태 | 시점 |`(`:137`) **개명 금지** (H-16).
> - opsdd 산문 `EXECUTE-LOOP` 표기 **17곳 전부 불가침**, `references/execute-loop-guide.md` **리네임·수정 금지** (D-7c, H-3).

#### 2.3.4 영향 범위

- SKILL.md는 PM 프롬프트의 직접 입력이다. 문구가 서로 모순되면(일부만 전환) PM이 `.md` 경로를 호출해 deprecation 경고 + `key` 결손 `state.json`을 만든다 → **pilot 단위 원자적 전환**이 필수 (H-13).
- oppl·oppd의 경우 `.md` 경로 호출은 애초에 실패하므로, 잔존 문구는 "동작하지 않는 지시"로 남아 더 해롭다.
- 변경이력 행 추가는 컨벤션 의무다. **[MUST]** `docs/CONVENTIONS.md` §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 "## 변경이력" 표에 행을 추가한다. 일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함 — 예: `(138)`."

---

### F-004: registry `pipeline` 필드 10종 정합화 + oppd `domain` 보강

#### 2.4.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/core/references/opal-skills-registry.json` | 10 pilot `pipeline` + oppd `domain` + `version`/`updated_at`/`changelog[]` | 수정 |

#### 2.4.2 현재 구현

- `pipeline`·`domain` 필드는 **코드 소비처가 0건**이다 — `opal/tools/skill-registry/skill-registry.js` 전수 grep에서 미검출. 둘 다 문서·PM 프롬프트 전용 필드이므로 표기 형식을 정의해도 런타임 회귀가 없다 (H-12 완화 근거).
- 10종 현행 값과 드리프트 (실측):

| 줄 | pilot | 현행 `pipeline` | 판정 |
|----|-------|----------------|------|
| `:21` | opp | `TASK → PLAN → EXECUTE` | CLOSE 누락 |
| `:37` | opd | `TASK → ANALYSIS → PLAN+TEST-SCENARIO → EXECUTE` | TEST·CLOSE 누락, `+` 합성 표기 |
| `:52` | opds | `TASK → PLAN+TEST-SCENARIO → EXECUTE` | TEST·CLOSE 누락, `+` 합성 표기. **opds 실제 `meta.stages`에는 TEST-SCENARIO가 없다** (`opal-pilot-dev-short/references/pipeline.json:4`) |
| `:67` | opdw | `TASK → WIREFRAME → EXECUTE` | CLOSE 누락 |
| `:83` | opwt | `Phase 1~4 (병렬 분석 → PM 진단 → 병렬 작성 → 정합성 검증)` | 단계 축이 아예 다름 (내부 Batch 흐름 서술) |
| `:99` | opsdd | `SPEC → VERIFY → PLAN → TASKS → VERIFY → LOOP → DONE` | 전면 상이 (존재하지 않는 단계명 4종) |
| `:116` | opgc | `SCAN → CHECK → REPORT → APPLY → CLOSE` | 없는 `APPLY` 기재 |
| `:132` | opdd | `TASK → DICT → MODEL → DDL/MIGRATION → QA → CLOSE` | **정합 — 변경 없음** |
| `:130-143` | oppd | (`pipeline` 필드 없음, `domain`도 없음) | **결측 2건** |
| `:162` | oppl | `설계 루프(인터뷰→PRD→TRD→CONTRACT→BACKLOG) → 실행 루프(태스크 반복)` | 단계 축이 다름 (루프 서술) |

- 확정 드리프트 8건 + 결측 1건 + 정합 1건 = 10종. **제외 항목 없음** (D-8).
- 파일 메타: `version: "3.9.0"`, `updated_at: "2026-07-17"` (`:3-4`), `changelog[]` 배열 존재 (`:770-`, 항목 스키마 `{version, date, task, changes[]}`).

#### 2.4.3 영향 범위

- `skill-registry.js`가 참조하는 필드는 `name`/`alias`/`description`/`triggers`/`paths`뿐이다. `pipeline`·`domain` 변경·추가는 비파괴다.
- `groups` 최상위 구조와 기존 필드명은 변경하지 않는다.
- **단일 파일에 10건을 쓰므로 병렬 편집 금지** — §4.2에서 단독 Step으로 배치한다.

---

### F-005: 전후 동등 실증 + spec-validate 10건

#### 2.5.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 배치 | `{scratchpad}/eq-verify/` (레포 밖) | 임시 태스크 폴더 · before/after 스냅샷 | 신규(임시) → **삭제** |
| 배치 | `opal/tools/state-tool/run.sh` | `init` / `spec-validate` 실행 진입점 | 읽기(실행만) |

#### 2.5.2 현재 구현 — 검증 가능성 분석

`cmd_init`은 `task_path`가 없으면 **부모가 쓰기 가능한 한 리프 디렉토리를 자동 생성**한다 (`state_tool.py:1057-1063`). `tasks/` 하위 여부를 강제하지 않으므로 **레포 밖 스크래치패드 경로에서 안전하게 실행**할 수 있다 (H-14 대응의 핵심 근거).

`cmd_spec_validate`는 `{ok, command, violations[], violations_count}` 단일 라인 JSON을 출력하고 `exit 0/1`로 종료한다 (`state_tool.py:1649-1663`). 전수 검사에 그대로 쓸 수 있다.

대조는 §1.1의 3그룹(A/B/C) 기준으로 갈린다. **그룹 A가 4종으로 늘어 자동 대조 커버리지가 51/57행(89%)로 상승**했다 — 전체 79행 중 그룹 A 57행이 before/after 완전 자동 대조 대상이다.

#### 2.5.3 영향 범위

- **before 스냅샷은 편집 전에 떠야 한다.** SKILL.md를 먼저 고치면 그룹 A의 `.md` 파싱 baseline, 그룹 B의 표 원문, oppl·oppd의 하드 실패 증거, opsdd `EXECUTE-LOOP` 등장 횟수 baseline이 모두 소실된다 → §4.2 Step 1을 모든 편집 Step의 선행 의존으로 배치한다.
- 그룹 C(oppd)의 baseline은 TASK.md D-7b 표이므로 편집 순서와 무관하게 유효하다.
- §2.1.3~§2.1.6과 §3.1.2의 표가 **PLAN 문서에 박제된 2차 기준값**이므로 Step 1이 실패해도 대조 기준은 유실되지 않는다 (이중화).
- 검증 실행 자체가 레포 파일을 만들지 않아야 한다 (H-14).

---

### F-006: opsdd `EXECUTE-LOOP` 산문 무변경 보장

#### 2.6.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 오케스트레이터 | `opal/skills/opal-pilot-sdd/SKILL.md` (`EXECUTE-LOOP` 17곳) | 불가침 토큰 — 등장 횟수 전후 동일해야 함 | **부분 불가침** |
| 가이드 | `opal/skills/opal-pilot-sdd/references/execute-loop-guide.md` | **파일명에 토큰 포함** — 리네임·수정 금지 | **없음(금지)** |
| 가이드 | `opal/core/references/opal-harness-semi-agentic.md:32` | 모드 경계 SSOT | **없음(금지)** |
| 스킬 | `opal/skills/op-sdd-plan/SKILL.md` | SDD PLAN 단계 스킬 | **없음(금지)** |
| 문서 | `README.md`, `docs/ARCHITECTURE.md`, 다이어그램 HTML, brain 페이지 3종 | 외부 참조 | **없음(금지)** |

#### 2.6.2 현재 구현

- **[MUST]** TASK.md §제약 조건 (f): "opsdd 산문의 `EXECUTE-LOOP` 표기 17곳과 `references/execute-loop-guide.md`는 **일절 수정하지 않는다**(D-7c)".
- **[MUST]** TASK.md D-7c: "`EXECUTE-LOOP`은 **Phase 이름**이고 `EXECUTE`는 **stage 값**으로 서로 다른 개념이다".
- 이 기능은 **negative requirement**(하지 않음의 보장)이므로 산출물이 없고 검증만 존재한다.
- 검증은 3중이다: ① opsdd SKILL.md 내 `EXECUTE-LOOP` 등장 횟수 **17회 전후 동일**, ② `execute-loop-guide.md` 변경 0건(파일명 포함 — 리네임도 diff에 잡힌다), ③ 외부 6개 파일 변경 0건.

#### 2.6.3 영향 범위

- 워커 오염 경로 2가지를 차단해야 한다. ① SKILL.md `:332` "단계 목록" 줄의 `EXECUTE-LOOP`을 `meta.stages` 기준으로 "정정"하려는 경우(H-2와 H-3 동시 발현). ② "`EXECUTE-LOOP` 라벨 드리프트"라는 **폐기된 표현**(PLAN v2.0~v2.2에서 opsdd를 제외한 근거로 쓰였으나 D-7c로 뒤집혔다 — §1.1 N-4 정정 안내)을 어딘가에서 보고 개명을 시도하는 경우.
- 대응: Step 5(opsdd)의 작업 내용에 "`:332` 줄 불가침"을 명시하고, 완료 기준에 등장 횟수 대조를 넣는다.
- **`meta.stages`에 `EXECUTE`를 쓰는 것과 산문을 그대로 두는 것은 모순이 아니다** — 두 토큰은 서로 다른 개념 계층이다(§2.1.4).

---

### F-007: oppl·oppd `init` 하드 실패 해소 실증

#### 2.7.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 배치 | `{scratchpad}/eq-verify/{oppl,oppd}-*` (레포 밖) | 전환 전 실패 기록 · 전환 후 성공 기록 | 신규(임시) → **삭제** |
| 스킬 | `opal/skills/opal-pilot-project-loop/**`, `opal/skills/opal-pilot-project-dev/**` | 해소 대상 (F-001·F-003 산출물) | 참조 |

#### 2.7.2 현재 구현 — 실패 재현

현재 oppl·oppd로 `init`을 실행하면 각각 다음이 출력되고 종료한다 (프로브 실측):

```
{"ok": false, "command": "init", "error": "skill_md_parse_error",
 "message": "--rows-from SKILL.md에서 행 추출 실패: header not found",
 "path": ".../opal/skills/opal-pilot-project-loop/SKILL.md", "reason": "header not found"}

{"ok": false, "command": "init", "error": "skill_md_parse_error",
 "message": "--rows-from SKILL.md에서 행 추출 실패: header not found",
 "path": ".../opal/skills/opal-pilot-project-dev/SKILL.md", "reason": "header not found"}
```

- 즉 **두 pilot으로는 새 태스크를 시작할 수 없다.** STATE.md·state.json이 생성되지 않으므로 파이프라인 자체가 출발하지 못한다.
- 두 실패 모두 §2.1.2 "3단 관문" ①에서 발생한다 (`state_tool.py:784-786`).

#### 2.7.3 영향 범위

- 전환 후 `--rows-from .../references/pipeline.json` 호출은 관문 ①~③을 전혀 거치지 않고 `build_rows_from_pipeline_json`으로 직행하므로(`state_tool.py:1128-1129`) 결함이 **구조적으로 해소**된다.
- 해소 증거는 pilot별 "before 실패 기록 + after 성공 기록" 쌍이어야 한다. before 기록은 Step 1에서 확보한다(편집 후에는 재현 불가).
- `rows_count`는 `ok()` 페이로드에서 확인한다 — **oppl 19 / oppd 13**.

---

### F-008: 레포 전역 구형 지시 정정

#### 2.8.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/core/references/tools.md` | state-tool 사용 가이드 — 시놉시스(`:84`) + 실행 예시(`:152`) | 수정 |
| 가이드 | `opal/core/references/harness/task-process.md` | 하네스 TASK 절차 — 행 원천 지시(`:49`) | 수정 |
| 스킬 | `opal/skills/op-task/SKILL.md` | 범용 TASK 단계 스킬 — 행 원천 지시(`:223`) | 수정 |
| 배치 | `opal/tools/state-tool/state_tool.py` | **불가침** — `.md` 언급은 도구 자신의 에러 메시지·분기 설명 | **없음(금지)** |
| 배치 | `opal/tools/state-tool/README.md` | **불가침** — 동일 사유 | **없음(금지)** |

#### 2.8.2 현재 구현 — 4곳 원문 실측

> 레포 전역 스캔(`grep -rn "rows-from" --include="*.md" opal/ docs/ README.md`)에서 pilot SKILL.md와 도구 자신을 제외한 결과가 정확히 **4건**이다.

| # | 위치 | 현재 원문 | 성격 |
|---|------|----------|------|
| ① | `opal/core/references/tools.md:152` | `  --rows-from ~/.opal/skills/opal-pilot-project/SKILL.md` (직전 `:148` 주석 `# SKILL.md에서 행 구성 자동 파싱`, `:150-151` `run.sh init tasks/134-.../ --skill opp --mode interactive`) | **실행 예시 — 지금도 틀린 명령.** opp는 이미 `references/pipeline.json`으로 전환되었는데(`opal/skills/opal-pilot-project/SKILL.md:162`) 이 예시는 구형 경로를 지시한다. 복사·실행 시 deprecation 경고 + `schema_version:"1.0"`·`key` 결손 `state.json`이 생성된다 |
| ② | `opal/core/references/tools.md:84` | `  [--rows-spec <inline-json>] [--rows-from <path-to-skill.md>] \` | **시놉시스** — `--rows-from`의 기대 인자를 `.md`로 표기 |
| ③ | `opal/core/references/harness/task-process.md:49` | `   - 행 구성(\`--rows-spec\`/\`--rows-from\`)은 오케스트레이터 SKILL.md "STATE.md 도메인 치환값" 참조` | **행 원천 지시** — SSOT를 SKILL.md 표로 가리킴 |
| ④ | `opal/skills/op-task/SKILL.md:223` | `> - 행 구성(\`--rows-spec\`/\`--rows-from\`)은 오케스트레이터 SKILL.md "STATE.md 도메인 치환값" 참조 (PLAN §2.3)` | **행 원천 지시** — ③과 동일 문구 (하네스 절과 스킬 본문 양쪽에 복제됨) |

**교체 방향 (확정)**

| # | after |
|---|-------|
| ① | `  --rows-from ~/.opal/skills/opal-pilot-project/references/pipeline.json` + 직전 주석 `# SKILL.md에서 행 구성 자동 파싱` → `# pipeline.json에서 행 구성 자동 파싱` |
| ② | `  [--rows-spec <inline-json>] [--rows-from <path-to-pipeline.json>] \` |
| ③ | 행 원천을 **"오케스트레이터 `references/pipeline.json`"**으로 정정 |
| ④ | ③과 동일 문구로 정정 (인용 꼬리 `(PLAN §2.3)`는 보존) |

**제외 2파일이 왜 불가침인가** — `state_tool.py`의 `.md` 언급은 `ERROR_CODES["skill_md_parse_error"]`(`:104`), `build_rows_from_skill_md` docstring(`:769`), deprecation 경고 문자열(`:1131`)이며 전부 **도구가 자기 동작을 설명하는 문자열**이다. `state-tool/README.md`도 `--rows-from` 확장자 분기 동작을 설명한다. 사용 지시가 아니므로 정정 대상이 아니고, 오히려 이 2파일이 **변경 0건**임을 보이는 것이 S-18의 역방향 검증이다.

#### 2.8.3 영향 범위

- **①이 가장 시급하다.** `tools.md`는 PM이 state-tool 사용법을 참조하는 1차 문서이고, `:148-152`는 복사해 쓰라고 만든 실행 예시다. 이미 전환된 opp를 구형 경로로 지시하므로 **지금도 오작동을 유발한다**.
- **③·④는 동일 문구 복제**다. 하나만 고치면 다른 하나가 남아 지시가 갈린다 — 같은 Step에서 함께 처리한다.
- 파일 3개는 **다른 F가 만지지 않는다**. pilot SKILL.md 6종·registry·`docs/CONVENTIONS.md`와 교집합이 공집합이므로 Batch 1 병렬 편입이 안전하다.
- `op-task/SKILL.md`는 opp·opdw 등 pilot이 TASK 단계에서 디스패치하는 단계 스킬이다. 여기의 지시가 구형이면 전환된 pilot에서도 워커가 SKILL.md 표를 행 원천으로 찾게 된다.

---

## 3. 기능별 설계

> 설계 결정 근거는 §8.3 참조 문서 테이블의 `D-N` 단축 인용 또는 `` `경로:줄번호` `` 풀 포맷으로 표기한다 (`opal/core/references/harness/citation-rules.md` §3.2).

### 공통 설계 결정 (전 F 적용)

| # | 결정 | 근거 |
|---|------|------|
| DEC-1 | pipeline.json 최상위 스키마는 `{spec_version, skill, meta, task_steps}` **4키만** 둔다. 최상위 `pm_gate` 배열은 만들지 않는다 | TASK.md D-2 (소비처 0). 필수 필드는 4종뿐 (→ D-2:890) |
| DEC-2 | `spec_version`은 `"1.0"` 고정 | 전환 완료 4종 전부 `"1.0"` (`opal/skills/opal-pilot-dev/references/pipeline.json:2`) |
| DEC-3 | `task_steps[]` 원소는 `{id, key, stage, item}` **4필드만**. `agent`/`model`/`inputs`/`outputs`/`gate`/`conditional`을 넣지 않는다 | TASK.md D-1 (실행 스펙 필드는 후속 태스크). `conditional`도 실행 스펙 성격이며, 넣으면 `.md` 경로에 없던 `row["conditional"]`이 rows[]에 추가된다 (`state_tool.py:961-962`) |
| DEC-4 | `meta = {mode_label, stages}` 2키. `stages`는 **`task_steps[].stage`의 등장순 중복 제거**로 파생한다. **SKILL.md "단계 목록" 줄은 참조하지 않는다** | H-2·H-11 대응. opsdd `:332`(`EXECUTE-LOOP`)·opwt `:423`(`ANALYSIS`)이 실제 행 stage와 다르므로 라벨 줄을 원천으로 삼으면 오염된다 |
| DEC-5 | `mode_label`은 각 SKILL.md "STATE.md 도메인 치환값" 표의 `모드` 값을 그대로 옮긴다. 해당 표가 없는 oppl·oppd는 registry `description`에서 라벨을 만든다 | 전환 완료 4종의 관행(opd `"Full Task"` ← SKILL.md 모드 필드)과 동일 |
| DEC-6 | `key` 명명 규칙 = `{stage_to_slug(stage)}.{item_slug}`. 반복 항목은 전환 완료 4종의 어휘를 재사용한다 — `user_confirm` / `pm_gate` / `done_md` / `task_md` / `plan_md` / `state_md`. **단, oppd는 D-7b 확정표의 `key`를 그대로 쓴다(재명명 금지)** | `opal/skills/opal-pilot-dev/references/pipeline.json:6-21` 어휘 계승. `stage_to_slug` 정의 (→ D-1:44-46). oppd는 제약 (g) |
| DEC-7 | JSON 들여쓰기·정렬은 전환 완료 4종과 동일한 1줄/step 형태를 따른다 (`{ "id": N, "key": "...", "stage": "...", "item": "..." }`) | 디프 가독성 — `opal/skills/opal-pilot-dev-short/references/pipeline.json:6-16` |
| DEC-8 | **opsdd 산문의 `EXECUTE-LOOP` 표기 17곳과 `references/execute-loop-guide.md`를 일절 수정하지 않는다.** `EXECUTE-LOOP`(Phase 이름)과 `EXECUTE`(stage 값)는 서로 다른 개념 계층이다 | **[MUST]** TASK.md D-7c / §제약 조건 (f) (H-3) |
| DEC-9 | **oppl SKILL.md의 섹션 헤더·표 헤더를 개명하지 않는다.** 미러 표가 되면 파서 매칭이 불필요하므로 고칠 이유가 없다 | TASK.md §범위 제외: "oppl SKILL.md 표 헤더(`Stage`) 개명" / R-3 AC (H-16) |
| DEC-10 | **oppd 행 구성은 TASK.md D-7b 확정 13행을 그대로 옮긴다. 재설계·가감·재명명 금지** | **[MUST]** TASK.md §제약 조건 (g) (H-7) |
| DEC-11 | **`.md` 파싱 지시 정정 대상은 "사용 지시"에 한정한다. 도구 자신의 에러 메시지·분기 설명은 정정하지 않는다** — `opal/tools/state-tool/state_tool.py`(`:104` ERROR_CODES, `:769` docstring, `:1131` deprecation 경고)와 `opal/tools/state-tool/README.md`는 **변경 0건** | TASK.md D-10 / R-9 §제외 대상. 도구가 자기 동작을 설명하는 문자열을 지우면 실제 폴백 경로 설명이 사라진다 (H-18 역방향) |

> **[MUST]** `docs/CONVENTIONS.md` §State 관리: "행 주소는 `--task-step <key>`(예: `plan.pm_gate`) 우선 사용, `--task-step-id <N>`은 숫자 폴백 — `--row`는 deprecated 별칭(신규 문서·프롬프트에 사용 금지). key 정의는 pilot `references/pipeline.json`이 SSOT."
> **[MUST]** `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `scripts/`)에서 수행한다."
> **[MUST]** `docs/CONVENTIONS.md` §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 "## 변경이력" 표에 행을 추가한다. 일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함."
> **[MUST]** `opal/core/references/opal-harness.md` §3 State: "파이프라인 현황판 행 상태 변경은 `state-tool`로만 수행한다. LLM이 STATE.md 마크다운 표를 직접 편집하는 것은 금지된다." (`opal/core/references/opal-harness.md:142`)

---

### F-001: 미전환 6 pilot pipeline.json 신설

#### 3.1.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/skills/opal-pilot-data-design/references/pipeline.json` | 스킬 | opdd 15 task_step SSOT | §2.1.3 |
| 2 | `opal/skills/opal-pilot-gc/references/pipeline.json` | 스킬 | opgc 7 task_step SSOT | §2.1.3 |
| 3 | `opal/skills/opal-pilot-write-tech/references/pipeline.json` | 스킬 | opwt 10 task_step SSOT | §2.1.3 |
| 4 | `opal/skills/opal-pilot-sdd/references/pipeline.json` | 스킬 | opsdd 25 task_step SSOT | §2.1.4 |
| 5 | `opal/skills/opal-pilot-project-loop/references/pipeline.json` | 스킬 | oppl 19 task_step SSOT | §2.1.5 (행 정규식 추출) |
| 6 | `opal/skills/opal-pilot-project-dev/references/pipeline.json` | 스킬 | oppd 13 task_step SSOT | §2.1.6 / TASK.md D-7b |

**수정**: 없음 (F-003에서 SKILL.md를 별도 처리)

#### 3.1.2 데이터 모델 — 확정 `task_steps[]` 명세

> **[MUST]** 아래 `stage`·`item` 값은 §2.1.3~§2.1.6 baseline과 **문자 단위로 동일**해야 한다.

**① opdd** — `skill: "opdd"`, `meta: { "mode_label": "Full Task", "stages": ["TASK","DICT","MODEL","DDL/MIGRATION","QA","CLOSE"] }`
`mode_label` 원천: `opal/skills/opal-pilot-data-design/SKILL.md:236`

| id | key | stage | item |
|----|-----|-------|------|
| 1 | `task.task_md` | TASK | 작업 |
| 2 | `task.user_confirm` | TASK | 사용자 확인 |
| 3 | `dict.dictionaries` | DICT | 작업 |
| 4 | `dict.pm_gate` | DICT | PM Gate |
| 5 | `dict.user_confirm` | DICT | 사용자 확인 |
| 6 | `model.modeling` | MODEL | 작업 |
| 7 | `model.pm_gate` | MODEL | PM Gate |
| 8 | `model.user_confirm` | MODEL | 사용자 확인 |
| 9 | `ddl_migration.ddl_scripts` | DDL/MIGRATION | 작업 |
| 10 | `ddl_migration.pm_gate` | DDL/MIGRATION | PM Gate |
| 11 | `ddl_migration.user_confirm` | DDL/MIGRATION | 사용자 확인 |
| 12 | `qa.review` | QA | 작업 |
| 13 | `qa.pm_gate` | QA | PM Gate |
| 14 | `qa.user_confirm` | QA | 사용자 확인 |
| 15 | `close.done_md` | CLOSE | DONE.md 생성 |

> `stage_to_slug("DDL/MIGRATION")` = `"ddl_migration"` — `/` → `_` 치환 (→ D-1:44-46). 이 3행의 key stage_slug가 검사 ⑦의 최대 위험 지점이다 (H-9).

**② opgc** — `skill: "opgc"`, `meta: { "mode_label": "GC", "stages": ["SCAN","CHECK","REPORT","CLOSE"] }`
`mode_label` 원천: `opal/skills/opal-pilot-gc/SKILL.md:427`

| id | key | stage | item |
|----|-----|-------|------|
| 1 | `scan.select_targets` | SCAN | 대상 파일 선별 + 스택 감지 + 프로젝트 구성 파싱 |
| 2 | `check.dispatch_agents` | CHECK | 에이전트 (요소×체커) 병렬 디스패치 |
| 3 | `check.await_agents` | CHECK | 에이전트 완료 확인 |
| 4 | `report.security_report` | REPORT | GC-SECURITY-{ts}[-{element}].md 생성 |
| 5 | `report.convention_report` | REPORT | GC-CONVENTION-{ts}[-{element}].md 생성 |
| 6 | `report.summary_table` | REPORT | 실행 요약 테이블 갱신 |
| 7 | `close.done_md` | CLOSE | DONE.md 생성 |

> `item`의 `{ts}`·`[-{element}]`는 플레이스홀더 문자열이다. JSON에 **원문 그대로** 넣는다(치환·이스케이프 금지, H-1).

**③ opwt** — `skill: "opwt"`, `meta: { "mode_label": "작성", "stages": ["TASK","PLAN","EXECUTE","QA","CLOSE"] }`
`mode_label` 원천: `opal/skills/opal-pilot-write-tech/SKILL.md:439`. **`stages`에 `ANALYSIS`를 넣지 않는다** — `:423`의 "단계 목록" 줄은 모드 가변 서술이고 기본 행 10개에 ANALYSIS가 없다 (DEC-4, H-11).

| id | key | stage | item |
|----|-----|-------|------|
| 1 | `task.task_md` | TASK | 작업 |
| 2 | `task.user_confirm` | TASK | 사용자 확인 |
| 3 | `plan.plan_md` | PLAN | 작업 |
| 4 | `plan.pm_gate` | PLAN | PM Gate |
| 5 | `plan.user_confirm` | PLAN | 사용자 확인 |
| 6 | `execute.batches` | EXECUTE | 작업 (Batch 동적 삽입) |
| 7 | `qa.consistency_check` | QA | 작업 |
| 8 | `qa.pm_gate` | QA | PM Gate |
| 9 | `qa.user_confirm` | QA | 사용자 확인 |
| 10 | `close.done_md` | CLOSE | DONE.md 생성 |

**④ opsdd** — `skill: "opsdd"`, `meta: { "mode_label": "SDD Task", "stages": ["TASK","SPEC","REVIEW","DESIGN","EXECUTE","VERIFY","CLOSE"] }`
`mode_label` 원천: `opal/skills/opal-pilot-sdd/SKILL.md:331`

> **[MUST] `meta.stages`에 `EXECUTE`를 쓴다. `EXECUTE-LOOP`을 쓰지 않는다** (D-7c, H-2). `:332`의 "단계 목록" 줄은 Phase 이름 나열이며 stage 값이 아니다 — DEC-4에 따라 `task_steps[].stage`에서 파생한다.

| id | key | stage | item |
|----|-----|-------|------|
| 1 | `task.task_md` | TASK | TASK.md 작성 |
| 2 | `task.state_md` | TASK | STATE.md 생성 |
| 3 | `task.user_confirm` | TASK | 사용자 확인 |
| 4 | `spec.dispatch_worker` | SPEC | 워커 디스패치 |
| 5 | `spec.spec_md` | SPEC | SPEC.md 생성 |
| 6 | `spec.pm_gate` | SPEC | PM Gate |
| 7 | `spec.user_confirm` | SPEC | 사용자 확인 |
| 8 | `review.structure_check` | REVIEW | 구조 검증 (S-1~S-6) |
| 9 | `review.test_scenarios_md` | REVIEW | TEST-SCENARIOS.md 작성 |
| 10 | `review.coverage_gate` | REVIEW | 커버리지 게이트 (scenario-coverage-check) |
| 11 | `review.scenario_gate` | REVIEW | 목표-커버 게이트 (op-scenario-gate evaluator) |
| 12 | `review.pm_gate` | REVIEW | PM Gate |
| 13 | `review.user_confirm` | REVIEW | 사용자 확인 |
| 14 | `design.dispatch_worker` | DESIGN | 워커 디스패치 |
| 15 | `design.spec_plan_md` | DESIGN | SPEC-PLAN.md 생성 |
| 16 | `design.pm_gate` | DESIGN | PM Gate |
| 17 | `design.user_confirm` | DESIGN | 사용자 확인 |
| 18 | `execute.act_run` | EXECUTE | ACT 실행 (상세: ACT 목록 참조) |
| 19 | `execute.pm_gate` | EXECUTE | PM Gate |
| 20 | `execute.user_confirm` | EXECUTE | 사용자 확인 |
| 21 | `verify.e2e_tests` | VERIFY | E2E 테스트 수행 |
| 22 | `verify.ts_green` | VERIFY | TS 전체 Green 확인 |
| 23 | `verify.pm_gate` | VERIFY | PM Gate |
| 24 | `verify.user_confirm` | VERIFY | 사용자 확인 |
| 25 | `close.done_md` | CLOSE | DONE.md 생성 |

> `spec.dispatch_worker`와 `design.dispatch_worker`는 item이 같지만 stage_slug가 달라 key가 유일하다 (검사 ⑤ 통과, H-4).
> opsdd의 R-13 ACT 동적 행은 `add-row`가 `_auto_row_key`로 key를 자동 생성한다 (`state_tool.py:1667-1690`) — 스펙에 미리 선언하지 않는다. `SKILL.md:346`의 `add-row --after 18` 지시는 `id: 18`(EXECUTE ACT 실행)과 정합하므로 그대로 유효하다.

**⑤ oppl** — `skill: "oppl"`, `meta: { "mode_label": "Project Loop", "stages": ["TASK","ANALYSIS","PLAN","WBS","REVIEW","EXECUTE","VERIFY","CLOSE"] }`
`mode_label` 원천: registry `description` "루프 기반 프로젝트 오케스트레이터" (`opal/core/references/opal-skills-registry.json:148`) — DEC-5 폴백.

| id | key | stage | item |
|----|-----|-------|------|
| 1 | `task.task_md` | TASK | TASK.md 작성 |
| 2 | `task.state_md` | TASK | STATE.md 생성 |
| 3 | `task.user_confirm` | TASK | 사용자 확인 |
| 4 | `analysis.d1_interview` | ANALYSIS | D1 인터뷰 — 명확화 4요소(목표/범위/제약/완료기준) |
| 5 | `analysis.d1_5_journey` | ANALYSIS | D1.5 여정 매핑 (조건부 — user-facing 프로젝트만, `references/journey-flow.md`) |
| 6 | `plan.d2_prd` | PLAN | D2 PRD 작성 |
| 7 | `plan.d3_trd` | PLAN | D3 TRD 작성 |
| 8 | `plan.d4_contract` | PLAN | D4 CONTRACT 작성 (`references/contract.md`) |
| 9 | `wbs.d5_backlog` | WBS | D5 백로그 생성 (`backlog-tool init`+`add-task`) |
| 10 | `review.d6_evaluator` | REVIEW | D6 Evaluator 설계 검토 (phase: design-review) |
| 11 | `review.pm_gate` | REVIEW | PM Gate |
| 12 | `review.d7_user_gate` | REVIEW | D7 사용자 확정 게이트 (4요소 잠김 확인) |
| 13 | `execute.l0_select` | EXECUTE | L0 태스크 선택 (상세: 태스크 목록 참조 — `add-row`로 T{NN} 행 동적 삽입) |
| 14 | `execute.pm_gate` | EXECUTE | PM Gate |
| 15 | `execute.user_confirm` | EXECUTE | 사용자 확인 |
| 16 | `verify.done_check` | VERIFY | L✓ 종료 판정 (`backlog-tool done-check` all_done + 회귀 0) |
| 17 | `verify.pm_gate` | VERIFY | PM Gate |
| 18 | `verify.user_confirm` | VERIFY | 사용자 확인 |
| 19 | `close.done_md` | CLOSE | DONE.md 생성 |

> **[MUST] oppl `item` 원문 보존 규칙** (H-6):
> - 백틱은 **`item` 문자열 내부의 일반 문자**다. JSON에 그대로 넣는다 — 이스케이프 불필요, 제거 금지.
> - 전각 대시 `—`(U+2014)를 하이픈 `-`로 바꾸지 않는다 (id 4·13).
> - 체크마크 `✓`(U+2713)를 유지한다 (id 16 `L✓ 종료 판정`).
> - 플레이스홀더 `{NN}`을 치환하지 않는다 (id 13).
> - 소수점 ID `D1.5`를 `D1_5`로 바꾸지 않는다 (id 5) — 단 **`key`에서는** `analysis.d1_5_journey`로 slug화한다.
> - 슬래시·괄호(`(목표/범위/제약/완료기준)`)를 그대로 둔다 (id 4).
>
> `key: "analysis.d1_5_journey"` — `item_slug`는 `[a-z][a-z0-9_]*`이므로 숫자·언더스코어 혼용이 허용된다 (→ D-1:41).
> **`conditional: true`를 넣지 않는다** (DEC-3). oppl의 R-13 태스크 동적 행(`T{NN}`)은 런타임 `add-row`가 처리하며, `SKILL.md`의 `add-row --after 13` 지시는 `id: 13`과 정합하므로 그대로 유효하다.

**⑥ oppd** — `skill: "oppd"`, `meta: { "mode_label": "Project Dev", "stages": ["TASK","PLAN","WBS","EXECUTE","CLOSE"] }`
`mode_label` 원천: registry `description` "프로젝트 개발 라이프사이클" (`opal/core/references/opal-skills-registry.json:134`) — DEC-5 폴백.

> **[MUST] 아래 13행은 TASK.md §확정된 설계 방향 D-7b 확정표를 그대로 옮긴 것이다. 재설계·가감·재명명 금지** (DEC-10 / 제약 (g) / H-7).

| id | key | stage | item |
|----|-----|-------|------|
| 1 | `task.task_md` | TASK | 작업 |
| 2 | `task.user_confirm` | TASK | 사용자 확인 |
| 3 | `plan.prd_trd` | PLAN | Phase1 PRD/TRD 작성 (opwt) |
| 4 | `plan.spec_validate` | PLAN | Phase1 명세 검증 (op-spec-validator) |
| 5 | `plan.pm_gate` | PLAN | PM Gate |
| 6 | `plan.user_confirm` | PLAN | Phase1 사용자 확정 |
| 7 | `wbs.wbs_md` | WBS | Phase2 WBS 작성 |
| 8 | `wbs.pm_gate` | WBS | PM Gate |
| 9 | `wbs.user_confirm` | WBS | Phase2 사용자 확정 |
| 10 | `execute.actions` | EXECUTE | Phase3 액션 실행 (동적 추가) |
| 11 | `execute.pm_gate` | EXECUTE | PM Gate |
| 12 | `execute.user_confirm` | EXECUTE | 사용자 확인 |
| 13 | `close.done_md` | CLOSE | DONE.md 생성 |

> `stage` 5종(TASK/PLAN/WBS/EXECUTE/CLOSE)은 전부 STAGE_ENUM 등록값이다 — `WBS` 포함 확인 완료 (`state_tool.py:31-39`).
> **agentic 자동 na 주의**: id 2·12의 `item`은 `사용자 확인`이라 agentic 모드에서 자동 na 대상이다. id 6·9는 `Phase1 사용자 확정`·`Phase2 사용자 확정`이라 문자열이 달라 **자동 na 대상이 아니다** (`state_tool.py:965`의 조건은 `item == "사용자 확인"` 완전 일치). D-7b 확정표를 그대로 따른 결과이며 임의로 통일하지 않는다.
> **`conditional: true`를 넣지 않는다** (DEC-3). `--wbs` 경로에서 id 10~12가 미완으로 남는 문제는 런타임 `mark --na`로 처리한다 (표준화 판단 ③, H-17).

#### 3.1.3 환경 변경

해당 없음. `install-mac.sh`는 스킬 디렉토리를 통째로 복사하므로 파일 목록 갱신이 필요 없다 (`scripts/install-mac.sh:1061-1068`).

#### 3.1.4 배치/마이그레이션

기존 태스크 `state.json` 소급 변환 **없음** (제약 (d)). 신규 태스크부터 `schema_version: "1.1"` + `key` 보유 rows가 생성된다.

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 AC (파일 생성) | 산출물 검사 | 6개 경로에 pipeline.json 존재, 각 JSON 파싱 성공 |
| TS-002 | R-1/R-5 AC (그룹 A) | 회귀 테스트 | opdd·opgc·opwt·opsdd 각각 before vs after `[(row_id, stage, item)]` 완전 동일 (15·7·10·25행) |
| TS-003 | R-1/R-5 AC (그룹 B) | 회귀 테스트 | oppl: 추출 19행 == `task_steps` 19개 == after rows 19개 (특수문자 포함 문자 단위) |
| TS-004 | R-1/R-5 AC (그룹 C) | 회귀 테스트 | oppd: D-7b 13행 == `task_steps` 13개 == after rows 13개 (`id`·`key`·`stage`·`item` 전부) |
| TS-010 | R-6 AC | 기능 테스트 | 신설 6건 포함 `spec-validate` 10건 `ok:true` / `violations_count: 0` |
| TS-011 | R-5 AC (회귀) | 회귀 테스트 | `--mode agentic` init 시 자동 na 행 집합이 `{item=="사용자 확인" and stage!="CLOSE"}`와 일치. 그룹 A는 before와도 동일 |

---

### F-003: 6 pilot SKILL.md init 인자 전환 + 미러 주석

#### 3.3.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 7 | `opal/skills/opal-pilot-data-design/SKILL.md` | 오케스트레이터 | `:75`·`:241` init 인자 / `:239` 미러 문구 / 변경이력 1행 | §2.3.2 |
| 8 | `opal/skills/opal-pilot-gc/SKILL.md` | 오케스트레이터 | `:116`·`:434`·`:482` init 인자 / `:431` SSOT 문구 / `:439` 표 제목 괄호부 / 변경이력 1행 | §2.3.2 |
| 9 | `opal/skills/opal-pilot-write-tech/SKILL.md` | 오케스트레이터 | `:193`·`:431`·`:441` init 인자 / `:428` SSOT 문구 / `:439` 미러 문구 / 변경이력 1행 | §2.3.2 |
| 10 | `opal/skills/opal-pilot-sdd/SKILL.md` | 오케스트레이터 | `:339`·`:447` init 인자 / `:336` SSOT 문구 / `:342` 오기술 / `:351` 미러 문구 / 변경이력 1행. **`EXECUTE-LOOP` 17곳·`:332` 단계 목록 줄 불가침** | §2.3.2, DEC-8 |
| 11 | `opal/skills/opal-pilot-project-loop/SKILL.md` | 오케스트레이터 | `:126`·`:442` init 인자 / `:133` 미러 문구 / `:128` 오기술 / 변경이력 1행. **헤더·표 헤더 개명 금지** | §2.3.2, DEC-9 |
| 12 | `opal/skills/opal-pilot-project-dev/SKILL.md` | 오케스트레이터 | `:115` init 인자 / **미러 표 13행 신설** + 미러 문구 / `:117`·`:153` 1문장 보강 / 변경이력 1행 | §2.3.2, §3.1.2 ⑥ |

#### 3.3.2 편집 명세

**(a) init 호출 인자 교체** — 각 코드블록의 `--rows-from` 값만 바꾼다. 나머지 인자(`--skill`/`--mode` 유무)는 **현행 유지**.

| pilot | after 값 |
|-------|---------|
| opdd | `--rows-from opal/skills/opal-pilot-data-design/references/pipeline.json` |
| opgc | `--rows-from opal/skills/opal-pilot-gc/references/pipeline.json` |
| opwt | `--rows-from opal/skills/opal-pilot-write-tech/references/pipeline.json` |
| opsdd | `--rows-from opal/skills/opal-pilot-sdd/references/pipeline.json` |
| oppl | `--rows-from opal/skills/opal-pilot-project-loop/references/pipeline.json` |
| oppd | `--rows-from opal/skills/opal-pilot-project-dev/references/pipeline.json` |

**(b) 플레이스홀더 형태 교체** — opdd `:241`·opwt `:441`의 `--rows-from <SKILL.md 경로>`는 실제 경로로 바꾼다.

**(c) 미러 주석 삽입 (R-3)** — 행 표 **직전 줄**에 전환 완료 4종과 동일 문구를 둔다.

```
**진행 현황 행 예시** (아래 표는 사람 열람용 미러 — SSOT는 `references/pipeline.json`. `.md` 파싱은 하위호환 폴백으로만 존치, 편집 금지):
```

- 표 제목이 다른 pilot(opgc `**파이프라인 현황판 행 구조**`, opsdd·oppl `**파이프라인 현황판**`)은 **기존 제목을 유지**하고 괄호 안 설명만 위 문구의 괄호부로 교체한다 — 제목 변경은 문서 내 상호 참조를 깨뜨린다.
- `[SSOT]` 인용 블록(opgc `:431`·opwt `:428`·opsdd `:336`)의 "이 섹션의 행 테이블을 `--rows-from`으로 참조한다" 서술은 **"SSOT는 `references/pipeline.json`이며 아래 표는 사람 열람용 미러"**로 의미를 뒤집어 기술한다.
- opwt `:428`의 "state-tool은 이 섹션의 `{단계 목록}`을 파싱하여 초기 행을 생성한다"는 **사실과 다른 서술**이다(실제 파서는 행 표를 읽는다 — `state_tool.py:799-820`). 함께 정정한다.
- opsdd `:342`의 "state-tool이 이 파일의 「파이프라인 현황판」 테이블(25행)을 읽어 state.json을 초기화한다"는 전환 후 사실이 아니게 되므로 "`references/pipeline.json`을 읽어"로 정정한다.

**(d) opsdd 전용 — `EXECUTE-LOOP` 불가침**

- **[MUST 금지]** 산문의 `EXECUTE-LOOP` 표기 **17곳 전부**를 그대로 둔다. 특히 `:332` "단계 목록" 줄(`TASK / SPEC / REVIEW / DESIGN / EXECUTE-LOOP / VERIFY / CLOSE`)을 `meta.stages` 기준으로 "정정"하지 않는다 (DEC-8, H-3).
- **[MUST 금지]** `opal/skills/opal-pilot-sdd/references/execute-loop-guide.md`를 리네임·수정하지 않는다 (파일명에 토큰 포함).
- `:344`의 `[R-13 ACT 동적 행]` 블록과 `add-row --after 18` 지시는 **그대로 둔다** — `id: 18`과 정합한다.
- `:340-346`의 `[R-10 비표준 행 구성]` 블록은 내용을 보존하고 "행 SSOT는 `references/pipeline.json`" 한 문장만 보강한다.
- 이 pilot의 편집은 **`--rows-from` 4곳 + 미러 문구 1곳 + 오기술 1곳 + 변경이력 1행**으로 한정된다.

**(e) oppl 전용 — 오기술 정정 + 개명 금지**

- `:128`의 "`state-tool`이 아래 SSOT 표를 읽어 state.json을 초기화한다"는 **현재도 거짓**이다(파서가 관문 ①에서 실패). "`state-tool`이 `references/pipeline.json`을 읽어 state.json을 초기화한다. 아래 표는 사람 열람용 미러다"로 정정한다.
- `:130`의 `[R-10 비표준 행 구성]` 블록은 **내용을 보존**하고 "행 SSOT는 `references/pipeline.json`" 한 문장만 보강한다.
- `:159-`의 `[R-13] 태스크 동적 행` 블록(`add-row --after 13 ...`)은 **그대로 둔다** — `id: 13`과 정합한다.
- **[MUST 금지]** `:121` 섹션 헤더(`## STATE.md 초기 생성`)와 `:137` 표 헤더(`| # | Stage | 항목 | 상태 | 시점 |`)를 **개명하지 않는다** (DEC-9, H-16).

**(f) oppd 전용 — 미러 표 13행 신설**

oppd는 행 표가 없으므로 `### STATE.md 초기 생성`(`:110`) 섹션 안, init 코드블록(`:115`) 다음에 **(c) 미러 문구 + 13행 표**를 신설한다. 표 헤더는 전환 완료 4종과 동일하게 `| # | 단계 | 항목 | 상태 | 시점 |`을 쓰고, 값은 §3.1.2 ⑥과 **1:1 동일**해야 한다 (H-8).

```markdown
**진행 현황 행 예시** (아래 표는 사람 열람용 미러 — SSOT는 `references/pipeline.json`. `.md` 파싱은 하위호환 폴백으로만 존치, 편집 금지):

| # | 단계 | 항목 | 상태 | 시점 |
|---|------|------|------|------|
| 1 | TASK | 작업 | ⬜ | - |
| 2 | TASK | 사용자 확인 | ⬜ | - |
| 3 | PLAN | Phase1 PRD/TRD 작성 (opwt) | ⬜ | - |
| 4 | PLAN | Phase1 명세 검증 (op-spec-validator) | ⬜ | - |
| 5 | PLAN | PM Gate | ⬜ | - |
| 6 | PLAN | Phase1 사용자 확정 | ⬜ | - |
| 7 | WBS | Phase2 WBS 작성 | ⬜ | - |
| 8 | WBS | PM Gate | ⬜ | - |
| 9 | WBS | Phase2 사용자 확정 | ⬜ | - |
| 10 | EXECUTE | Phase3 액션 실행 (동적 추가) | ⬜ | - |
| 11 | EXECUTE | PM Gate | ⬜ | - |
| 12 | EXECUTE | 사용자 확인 | ⬜ | - |
| 13 | CLOSE | DONE.md 생성 | ⬜ | - |
```

- `:117`의 `[R-10 비표준 행 구성]` 블록은 **내용을 보존**하되, "PM Gate 단일 mark 규정이 Phase별 PM Gate 행(id 5·8·11)과 정합" 한 문장을 보강한다.
- `:153`의 `--wbs` 플래그 설명에 "이 경로에서는 EXECUTE 행(id 10~12)을 `mark --na`로 처리한다" 한 문장을 보강한다 (표준화 판단 ③, H-17).
- `:574-630`의 STATE.md 템플릿(`## Phase 진행 현황` 등 서술형 표)은 **건드리지 않는다**.

**(g) 변경이력 1행 추가** — 각 SKILL.md 말미 `## 변경이력` 표. 버전은 직전 행에서 +1, 일시는 `date` 도구로 취득한 KST `YYYY-MM-DD HH:mm`, 말미에 `(090)`.

| pilot | 직전 버전 | 신규 버전 |
|-------|----------|----------|
| opdd | v1.1 | v1.2 |
| opgc | v1.8 | v1.9 |
| opwt | v4.6 | v4.7 |
| opsdd | v3.6.0 | v3.7.0 |
| oppl | v1.7 | v1.8 |
| oppd | v5.2 | v5.3 |

> 문구 예(opdd·opgc·opwt·opsdd): `pipeline.json 전환 — references/pipeline.json 신설(N task-step, SSOT), --rows-from 호출 경로를 SKILL.md에서 pipeline.json으로 교체, 표는 사람 열람용 미러로 명시 (090)`
> opsdd는 불가침 사실을 덧붙인다: `... meta.stages는 stage 값 EXECUTE 사용(산문 Phase 이름 EXECUTE-LOOP 표기는 불변) (090)`
> oppl: `pipeline.json 전환 + init 하드 실패 해소 — references/pipeline.json 신설(19 task-step, SSOT), --rows-from를 pipeline.json으로 교체하여 기존 skill_md_parse_error(header not found) 해소, 표는 사람 열람용 미러로 명시(헤더·표 헤더 개명 없음) (090)`
> oppd: `pipeline.json 전환 + init 하드 실패 해소 — references/pipeline.json 신설(13 task-step, SSOT), 파이프라인 현황판 미러 표 13행 신설, --rows-from를 pipeline.json으로 교체하여 기존 skill_md_parse_error(header not found) 해소 (090)`

#### 3.3.3 환경 변경 / 배치

해당 없음.

#### 3.3.4 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-005 | R-2 AC (잔존 0) | 산출물 검사 | 대상 6 SKILL.md에서 `rows-from.*SKILL\.md` 매칭이 **`## 변경이력` 섹션 밖 0건** (D-9) |
| TS-006 | R-2 AC (채택) | 산출물 검사 | 대상 6 SKILL.md 각각 1건 이상. 전체 `opal-pilot-*/SKILL.md` 중 매칭 파일 **10개** |
| TS-007 | R-3 AC | 산출물 검사 | 6 pilot 전부 미러 문구 존재. oppd 13행 미러 표 신설 후 `task_steps`와 1:1 동일. oppl `:121`·`:137` 라인이 diff에 미출현 |
| TS-014 | 컨벤션 | 코드/문서 품질 | 변경한 6 SKILL.md + registry + CONVENTIONS.md 전부 변경이력/changelog 1건 추가, 일시 KST `YYYY-MM-DD HH:mm`, `(090)` 포함 |

---

### F-004: registry `pipeline` 필드 10종 정합화 + oppd `domain` 보강

#### 3.4.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 13 | `opal/core/references/opal-skills-registry.json` | 가이드 | **10종** `pipeline` 값 교체/신설(opdd 무변경) + oppd `domain` 신설 + `version`/`updated_at` 승격 + `changelog[]` 1항목 | §2.4.2, TASK.md D-8 |

#### 3.4.2 파생 규칙 + 확정 값

**표기 규칙 (H-12 해소)**: `pipeline` 문자열 = 해당 pipeline.json `meta.stages` 배열을 `" → "`(공백-화살표-공백)로 연결한 값. 합성 표기(`PLAN+TEST-SCENARIO`)·자연어 서술·존재하지 않는 단계명을 쓰지 않는다.

| 줄 | pilot | after (확정) | 변경 |
|----|-------|--------------|------|
| `:21` | opp | `TASK → PLAN → EXECUTE → CLOSE` | 수정 |
| `:37` | opd | `TASK → ANALYSIS → PLAN → TEST-SCENARIO → EXECUTE → TEST → CLOSE` | 수정 |
| `:52` | opds | `TASK → PLAN → EXECUTE → TEST → CLOSE` | 수정 |
| `:67` | opdw | `TASK → WIREFRAME → EXECUTE → CLOSE` | 수정 |
| `:83` | opwt | `TASK → PLAN → EXECUTE → QA → CLOSE` | 수정 |
| `:99` | opsdd | `TASK → SPEC → REVIEW → DESIGN → EXECUTE → VERIFY → CLOSE` | 수정 (**`EXECUTE-LOOP` 아님** — D-7c) |
| `:116` | opgc | `SCAN → CHECK → REPORT → CLOSE` | 수정 |
| `:132` | opdd | `TASK → DICT → MODEL → DDL/MIGRATION → QA → CLOSE` | **무변경** |
| `:130-143` | oppd | `TASK → PLAN → WBS → EXECUTE → CLOSE` + `"domain": "dev"` | **신설 2건** |
| `:162` | oppl | `TASK → ANALYSIS → PLAN → WBS → REVIEW → EXECUTE → VERIFY → CLOSE` | 수정 |

- opp/opd/opds/opdw의 `meta.stages` 원천: 각 `references/pipeline.json:4` (실측). 신규 6종은 §3.1.2에서 확정한 값.
- oppd `domain` 값은 `"dev"` — 동렬 계열인 oppl(`:159`)·opd(`:36`)·opds(`:51`)와 동일 (D-8).
- 파일 메타: `version` `"3.9.0"` → `"3.10.0"`, `updated_at` → 작업일(KST `YYYY-MM-DD`), `changelog[]` 선두에 `{version:"3.10.0", date, task:"090", changes:[...]}` 1항목 추가. 문구에 **"10/10 pilot pipeline.json 전환 완료"**를 명시한다.

#### 3.4.3 환경 변경 / 배치

해당 없음.

#### 3.4.4 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-008 | R-4 AC | 산출물 검사 | 10종 전부 `pipeline` 존재, 각 값을 `" → "`로 split한 리스트 == 해당 pipeline.json `meta.stages`. oppd에 `domain` 존재. opsdd 값에 `EXECUTE-LOOP` 미포함 |

---

### F-005: 전후 동등 실증 + spec-validate 10건

#### 3.5.1 파일 변경 계획

**신규 생성**: 없음 (레포 내). 검증 산출물은 전부 스크래치패드에 생성 후 삭제한다.
**수정**: 없음.

#### 3.5.2 검증 절차 설계 (R-5·R-6·R-7·R-8 실증)

> **[MUST]** TASK.md R-5: "어디에: 스크래치패드 등 **레포 밖** 경로에서 실행 (레포 파일 생성·수정 0건)" (H-14).

**작업 루트 정의**
```
WORK=<scratchpad>/eq-verify         # 예: /private/tmp/claude-501/.../scratchpad/eq-verify
REPO=/Volumes/Data/AIStudio/workspace/ai-framework
mkdir -p "$WORK/before" "$WORK/after"
```
`cmd_init`은 부모가 쓰기 가능하면 리프 디렉토리를 자동 생성하며 `tasks/` 하위를 강제하지 않는다 (`state_tool.py:1057-1063`).

**P1. before 스냅샷 (모든 편집 Step보다 선행)**
`$WORK/probe_before.py` 하나에 4가지 채집을 넣는다. `init` 서브명령을 쓰지 않으므로 파일을 만들지 않는다.
- `importlib.util.spec_from_file_location`으로 `$REPO/opal/tools/state-tool/state_tool.py`를 모듈 로드.
- **(a) 그룹 A (4종)** — `opdd`·`opgc`·`opwt`·`opsdd`에 `build_rows_from_skill_md(SKILL.md, "init", mode)`를 `mode ∈ {semi-agentic, agentic}` 2회 호출 → `$WORK/before/{alias}.{mode}.json`. 기대: 15 / 7 / 10 / **25**행.
- **(b) 그룹 B (oppl)** — `SKILL.md`를 읽어 **`:137`(표 헤더)~`:157`(19행) 구간**에 `state_tool.py:816-820`의 행 정규식을 직접 적용 → 19건을 `$WORK/before/oppl.table.json`에 저장.
- **(c) F-007 before 증거** — `oppl`·`oppd` 각각에 `build_rows_from_skill_md`를 호출해 `SystemExit`와 에러 페이로드(`skill_md_parse_error` / `header not found`)를 `$WORK/before/{alias}.init-failure.json`에 기록한다. 편집 후에는 재현 불가.
- **(d) F-006 before 증거** — `grep -c "EXECUTE-LOOP" $REPO/opal/skills/opal-pilot-sdd/SKILL.md` 값을 `$WORK/before/opsdd.execute-loop-count.txt`에 기록한다. **기대: 17**.
- **그룹 C(oppd)의 baseline은 TASK.md D-7b 표**이므로 별도 채집이 없다.
- (a)·(b) 결과를 PLAN §2.1.3·§2.1.4·§2.1.5 표와 대조한다 (기준값 이중화 확인).

**P2. after 스냅샷 (F-001~F-004 완료 후)**
pipeline.json 보유 10종 전부에 대해 실제 CLI를 실행한다.
```
~/.opal/tools/state-tool/run.sh init "$WORK/after/{alias}-{mode}" \
  --skill {alias} --mode {semi-agentic|agentic} \
  --rows-from "$REPO/opal/skills/{skill-dir}/references/pipeline.json"
```
- 대상 10종 = `opd`·`opds`·`opdw`·`opp`·`opdd`·`opgc`·`opwt`·`opsdd`·`oppl`·`oppd`. 10 × 2 mode = **20회**. exit 0 및 `"ok": true` 확인 (채택 검증 — **10/10**).
- `state.json`에서 `rows[]`를 추출해 `$WORK/after/{alias}.{mode}.json`에 정규화 저장.
- `schema_version == "1.1"` 및 모든 행의 `key` 비어있지 않음을 함께 확인한다.
- **oppl·oppd 실행의 `ok()` 페이로드에서 `rows_count`(19 / 13)를 별도 기록**한다 (F-007 after 증거).

**P3. 대조 (핵심 판정)**
- **그룹 A (4종)** — before vs after의 `[(row_id, stage, item)]`가 **완전 동일**. 1건이라도 다르면 **FAIL, 즉시 중단**. → TS-002
- **그룹 B (oppl)** — 3자 대조. ① `before/oppl.table.json` 19건, ② `task_steps[]` 19개, ③ after `rows[]` 19개. 문자 단위 동일(특수문자 포함). → TS-003
- **그룹 C (oppd)** — 3자 대조. ① TASK.md D-7b 13행, ② `task_steps[]` 13개(`id`·`key`·`stage`·`item`), ③ after `rows[]` 13개. → TS-004
- **모드 축** — `agentic`에서 `status == "na"` 집합이 `{item == "사용자 확인" and stage != "CLOSE"}`와 일치. 그룹 A는 before와도 동일. oppd는 id 2·12만 na이고 id 6·9는 비대상임을 확인. → TS-011

**P4. 잔존·채택 검증 (R-5, 대상 6종 / 전체 10종)**
```
for f in opal-pilot-data-design opal-pilot-gc opal-pilot-write-tech \
         opal-pilot-sdd opal-pilot-project-loop opal-pilot-project-dev; do
  awk '/^## 변경이력/{exit} /rows-from.*SKILL\.md/{print FILENAME":"FNR": "$0}' "$REPO/opal/skills/$f/SKILL.md"
done
```
- 출력 **0줄** (D-9). → TS-005
```
grep -l "rows-from.*references/pipeline\.json" "$REPO"/opal/skills/opal-pilot-*/SKILL.md | wc -l   # = 10
grep -rln "rows-from.*SKILL\.md" "$REPO"/opal/skills/opal-pilot-*/SKILL.md                          # 변경이력 행만
```
- 두 번째 명령의 결과가 변경이력 행에만 걸리는지 확인해 **deprecated 경로 호출자 0건**(완료기준 8)을 실증한다. → TS-006, TS-017

**P4-b. 레포 전역 잔존 스캔 (R-9 / 완료기준 (0), F-008 검증)**
```
# 도구 자신(state_tool.py·state-tool/README.md)과 pilot 변경이력 행을 제외한 전역 스캔
grep -rn "rows-from\|STATE\.md \"STATE\.md 도메인 치환값\"\|도메인 치환값\" 참조" \
     --include="*.md" opal/ docs/ README.md \
  | grep -v "^opal/tools/state-tool/" \
  | grep -vE "^opal/skills/opal-pilot-[^:]*:[0-9]+:\| v[0-9]"
```
- 위 결과에 `SKILL.md`를 행 원천·인자로 지시하는 줄이 **0건**이어야 한다. §2.8.2의 4곳(`tools.md:84`·`:152`, `task-process.md:49`, `op-task/SKILL.md:223`)이 전부 정정된 상태다.
- **역방향 검증** — 도구 자신 2파일은 반대로 **손대지 않았음**을 확인한다:
```
git status --porcelain -- opal/tools/state-tool/state_tool.py \
                          opal/tools/state-tool/README.md | wc -l   # = 0
```
→ TS-018 (S-18)

**P5. `spec-validate` 전수 (R-6, 10건)**
```
for d in opal-pilot-dev opal-pilot-dev-short opal-pilot-dev-wireframe opal-pilot-project \
         opal-pilot-data-design opal-pilot-gc opal-pilot-write-tech \
         opal-pilot-sdd opal-pilot-project-loop opal-pilot-project-dev; do
  ~/.opal/tools/state-tool/run.sh spec-validate "$REPO/opal/skills/$d/references/pipeline.json"
done
```
- 10건 전부 `{"ok": true, ..., "violations_count": 0}` + exit 0. → TS-010
- 출력을 `$WORK/spec-validate.log`에 모아 TEST 단계 증거로 인용한다.

**P6. registry 정합 검증 (R-4)**
`$WORK/probe_registry.py` — registry의 **10종** `pipeline`을 `" → "`로 split한 리스트와 해당 `references/pipeline.json`의 `meta.stages`를 비교. 10/10 일치. oppd `domain` 존재 확인. opsdd 값에 `EXECUTE-LOOP` 미포함 확인. → TS-008

**P7. opsdd `EXECUTE-LOOP` 무변경 검증 (R-7)**
```
grep -c "EXECUTE-LOOP" "$REPO/opal/skills/opal-pilot-sdd/SKILL.md"                    # = 17 (before와 동일)
git status --porcelain -- opal/skills/opal-pilot-sdd/references/execute-loop-guide.md | wc -l   # = 0
git status --porcelain -- opal/core/references/opal-harness-semi-agentic.md \
    opal/skills/op-sdd-plan/SKILL.md README.md docs/ARCHITECTURE.md | wc -l           # = 0
```
- brain 페이지 3종·다이어그램 HTML도 `git status`에 나타나지 않아야 한다.
- `execute-loop-guide.md`는 **리네임도 diff에 잡힌다**(파일명 자체가 토큰 포함). → TS-009

**P8. oppl 개명 금지 + oppd 미러 표 정합 검증**
```
git diff -- opal/skills/opal-pilot-project-loop/SKILL.md \
  | grep -E "^[-+].*(## STATE\.md 초기 생성|\| # \| Stage \|)" | wc -l   # = 0
```
- oppd: SKILL.md 신설 미러 표 13행을 파싱해 `pipeline.json` `task_steps`와 `(id, stage, item)` 대조 → 완전 일치. → TS-007

**P9. 정리 (H-14 필수 절차)**
```
rm -rf "$WORK"
cd "$REPO" && git status --porcelain
```
- 삭제 전 `$WORK`가 스크래치패드 하위 경로인지 검사한 뒤 삭제한다.
- `git status --porcelain` 출력이 **§3의 파일 변경 계획 14건 + 태스크 산출물(`tasks/090-…`)**로만 구성되어야 한다. → TS-012
- 기존 태스크 폴더(`tasks/080~089`)의 `state.json`이 수정되지 않았음을 함께 확인한다 (제약 (d)).

#### 3.5.3 환경 변경

Python 3(표준 라이브러리만) + Bash. 신규 패키지 없음. `~/.opal/tools/state-tool/run.sh`는 배포본이며 **소스 무변경**이므로 재설치 없이 사용 가능하다.

#### 3.5.4 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-012 | R-5 AC (산출물 잔류 금지) | 보안/회귀 테스트 | `$WORK` 삭제 완료, `git status --porcelain`에 임시 `state.json`/`STATE.md` 0건, `tasks/080~089` 미변경 |
| TS-013 | 완료기준 (4) | 회귀 테스트 | P2 실행 20회 전부 deprecation 경고 미출력 |
| TS-017 | 완료기준 (8) | 산출물 검사 | `opal-pilot-*/SKILL.md`에서 `rows-from.*SKILL.md`가 변경이력 행에만 존재 — **deprecated 경로 호출자 0건** |

---

### F-006: opsdd `EXECUTE-LOOP` 산문 무변경 보장

#### 3.6.1 파일 변경 계획

**신규 생성**: 없음. **수정**: 없음. — 이 기능의 산출물은 "변경하지 않았다는 증거"다.

#### 3.6.2 설계

- **가드 1 (선제)**: Step 5(opsdd) 작업 내용에 편집 범위를 **`--rows-from` 4곳 + 미러 문구 1곳 + 오기술 1곳 + 변경이력 1행**으로 열거하고, "`:332` 단계 목록 줄 불가침"을 명시한다.
- **가드 2 (선제)**: `execute-loop-guide.md`는 Step 5의 `파일` 필드에 등장하지 않는다 — 대상 파일은 `references/pipeline.json`과 `SKILL.md` 2개뿐이다.
- **가드 3 (선제)**: `meta.stages` 파생 규칙을 DEC-4로 고정해 `:332` 라벨 줄을 참조할 이유 자체를 제거한다 (H-2와 H-3의 공통 발화점 차단).
- **가드 4 (사후)**: P7의 3개 명령으로 검출한다 — 등장 횟수 17회 동일 / `execute-loop-guide.md` 0건 / 외부 6개 파일 0건.
- **개념 분리 명문화**: `EXECUTE-LOOP`(Phase 이름) ≠ `EXECUTE`(stage 값). §2.1.4의 대조표를 EXECUTE 워커 프롬프트에 그대로 주입한다.

#### 3.6.3 환경 변경 / 배치

해당 없음.

#### 3.6.4 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-009 | R-7 AC | 회귀 테스트 | opsdd SKILL.md `EXECUTE-LOOP` 등장 **17회 전후 동일**, `execute-loop-guide.md` 변경 0건(리네임 포함), 외부 6개 파일 변경 0건 |

---

### F-007: oppl·oppd `init` 하드 실패 해소 실증

#### 3.7.1 파일 변경 계획

**신규 생성**: 없음 (레포 내). 증거는 스크래치패드에 남기고 결과를 TEST 보고에 인용한다.
**수정**: 없음 (해소 자체는 F-001·F-003의 oppl·oppd분 산출물이 수행).

#### 3.7.2 설계 — pilot별 before/after 증거 쌍

| pilot | 단계 | 실행 | 기대 결과 | 저장 위치 |
|-------|------|------|----------|----------|
| oppl | before | (Step 1) `build_rows_from_skill_md(oppl SKILL.md, "init", "semi-agentic")` | `SystemExit` + `{"ok": false, "error": "skill_md_parse_error", "reason": "header not found"}` | `$WORK/before/oppl.init-failure.json` |
| oppl | after | (Step 10) `run.sh init … --skill oppl --rows-from .../references/pipeline.json` | **exit 0** + `"ok": true` + **`rows_count: 19`** | `$WORK/after/oppl.init-success.json` |
| oppd | before | (Step 1) `build_rows_from_skill_md(oppd SKILL.md, "init", "semi-agentic")` | 동일 에러 페이로드 | `$WORK/before/oppd.init-failure.json` |
| oppd | after | (Step 10) `run.sh init … --skill oppd --rows-from .../references/pipeline.json` | **exit 0** + `"ok": true` + **`rows_count: 13`** | `$WORK/after/oppd.init-success.json` |

- before 증거는 **편집 전에만 확보 가능**하다 — Step 1을 놓치면 재현할 수 없다 (§4.3 의존 근거).
- after의 `rows_count`가 19/13이 아니면 F-001 해당분 이관에 행 누락·중복이 있는 것이므로 H-5(oppl)·H-7(oppd) 발현으로 간주하고 즉시 중단한다.
- 해소의 구조적 근거: `.json` 경로는 `build_rows_from_pipeline_json`으로 직행하며(`state_tool.py:1128-1129`) `.md` 파서의 3단 관문(§2.1.2)을 전혀 거치지 않는다.

#### 3.7.3 환경 변경 / 배치

해당 없음.

#### 3.7.4 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-016 | R-8 AC | 기능 테스트 | oppl·oppd 각각 before `skill_md_parse_error` 기록 + after exit 0 · `ok:true` · `rows_count` 19 / 13. 증거가 쌍으로 제시된다 |

---

### F-008: 레포 전역 구형 지시 정정

#### 3.8.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 15 | `opal/core/references/tools.md` | 가이드 | `:84` 시놉시스 인자 표기 + `:148` 주석 + `:152` 실행 예시 경로 / 변경이력 1행 | §2.8.2 ①② |
| 16 | `opal/core/references/harness/task-process.md` | 가이드 | `:49` 행 원천 지시 정정 / 변경이력 1행 | §2.8.2 ③ |
| 17 | `opal/skills/op-task/SKILL.md` | 스킬 | `:223` 행 원천 지시 정정 / 변경이력 1행 | §2.8.2 ④ |

**신규 생성**: 없음.

> **[MUST] 불가침 2파일** — `opal/tools/state-tool/state_tool.py`·`opal/tools/state-tool/README.md`는 **정정 대상이 아니다**. 두 파일의 `.md` 언급은 도구 자신의 에러 메시지·분기 설명이며 사용 지시가 아니다 (DEC-11). 이 2파일의 **변경 0건**이 S-18의 역방향 검증 항목이다.

#### 3.8.2 편집 명세 — 4곳 before/after

**① `opal/core/references/tools.md:148-152` — 실행 예시**

```
before
# SKILL.md에서 행 구성 자동 파싱
~/.opal/tools/state-tool/run.sh init tasks/134-.../ \
  --skill opp --mode interactive \
  --rows-from ~/.opal/skills/opal-pilot-project/SKILL.md

after
# pipeline.json에서 행 구성 자동 파싱
~/.opal/tools/state-tool/run.sh init tasks/134-.../ \
  --skill opp --mode interactive \
  --rows-from ~/.opal/skills/opal-pilot-project/references/pipeline.json
```

- 경로 표기는 **`~/.opal/skills/...` 형태를 유지**한다 — `tools.md`는 배포본 기준 사용 가이드이고 기존 예시도 그 형태다. pilot SKILL.md의 프로젝트 상대경로(`opal/skills/...`)와 표기가 다른 것은 문서 성격 차이이며 이번 범위에서 통일하지 않는다 (§9 R-8).
- `--skill opp`·`--mode interactive`·태스크 경로는 **그대로 둔다**. 교체 대상은 주석 1줄 + `--rows-from` 값 1줄이다.

**② `opal/core/references/tools.md:84` — 시놉시스**

```
before   [--rows-spec <inline-json>] [--rows-from <path-to-skill.md>] \
after    [--rows-spec <inline-json>] [--rows-from <path-to-pipeline.json>] \
```

- 같은 블록의 `--skill <opp|opd|opds|opdw|opwt|opgc|oppd|opsdd>`(`:81`)에 `oppl`·`opdd`가 빠져 있으나 **이번 범위 밖**이다 — R-9는 `.md` 파싱 지시 정정에 한정된다. §9 R-17에 관측 사항으로 등재한다.

**③ `opal/core/references/harness/task-process.md:49`**

```
before   - 행 구성(`--rows-spec`/`--rows-from`)은 오케스트레이터 SKILL.md "STATE.md 도메인 치환값" 참조
after    - 행 구성(`--rows-from`)은 오케스트레이터 `references/pipeline.json`이 SSOT다. SKILL.md 행 표는 사람 열람용 미러이며 `.md` 파싱은 deprecated(090)
```

- `--rows-spec`은 여전히 유효한 옵션이므로 **삭제하지 않고** 문장 구조만 조정한다. `--rows-from`의 원천만 pipeline.json으로 못 박는다.
- 직후 `:51`의 `근거:` 인용 줄은 **보존**한다.

**④ `opal/skills/op-task/SKILL.md:223`**

```
before   > - 행 구성(`--rows-spec`/`--rows-from`)은 오케스트레이터 SKILL.md "STATE.md 도메인 치환값" 참조 (PLAN §2.3)
after    > - 행 구성(`--rows-from`)은 오케스트레이터 `references/pipeline.json`이 SSOT다. SKILL.md 행 표는 사람 열람용 미러이며 `.md` 파싱은 deprecated(090) (PLAN §2.3)
```

- ③과 **동일 취지 문구**로 맞춘다 (두 곳이 복제 관계이므로 표현이 갈리면 안 된다).
- 인용 꼬리 `(PLAN §2.3)`는 **보존**한다.

**⑤ 변경이력 1행 추가 (3개 파일 전부)** — **[MUST]** `docs/CONVENTIONS.md` §변경이력 작성 의무. 일시는 `date` 도구로 취득한 KST `YYYY-MM-DD HH:mm`, 말미에 `(090)`.

| 파일 | 직전 버전 | 신규 버전 |
|------|----------|----------|
| `opal/core/references/tools.md` | v2.11 | v2.12 |
| `opal/core/references/harness/task-process.md` | v1.6 | v1.7 |
| `opal/skills/op-task/SKILL.md` | v2.4 | v2.5 |

> 문구 예: `state-tool 행 원천 지시 정정 — --rows-from 시놉시스·실행 예시·행 원천 서술을 references/pipeline.json 기준으로 교체(구형 .md 파싱 지시 제거). 10/10 pilot 전환에 맞춘 pilot 밖 정합 (090)`

#### 3.8.3 환경 변경 / 배치

해당 없음. 세 파일 모두 `install-mac.sh`가 디렉토리 단위로 복사하므로 Step 12(배포)에서 자동 반영된다.

#### 3.8.4 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-018 | R-9 AC / 완료기준 (0) | 산출물 검사 | 레포 전역(`opal/`·`docs/`·`README.md`) `.md` 파싱 지시 **0건** — pilot SKILL.md 변경이력 행과 **도구 자신 2파일**만 예외. 4곳 각각 지정 문자열로 교체됨. `state_tool.py`·`state-tool/README.md` **변경 0건**(역방향) |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| P0 | F-005, F-006, F-007 (before) | 1 | opal-task-agent | 단독 | **before 스냅샷 — 모든 편집보다 반드시 선행.** 그룹 A 4종 파서 호출 + 그룹 B 표 추출 + oppl·oppd 실패 증거 + opsdd `EXECUTE-LOOP` 17회 baseline |
| P1 | F-001 + F-003 + **F-008** | 2, 3, 4, 5, 6, 7, **8** | opal-task-agent ×7 | **병렬 7** | pilot 6종 + pilot 밖 문서 3파일. 전체 파일 집합이 완전 비중첩 |
| P2 | F-004 | 9 | opal-task-agent | 순차 | registry — 단일 파일, 전 pilot `meta.stages` 확정 후에만 파생 가능 |
| P3 | F-005 + F-006 + F-007 (after) + F-008 검증 | 10 | opal-task-agent | 순차 | after 스냅샷 + 3그룹 대조 + spec-validate 10건 + 잔존/채택 + **레포 전역 스캔** + `EXECUTE-LOOP` 무변경 + 하드 실패 해소 + 정리 |
| P4 | 문서 | 11 | PM 직접 | 순차 | `docs/CONVENTIONS.md` §State 규칙 1줄 추가 |
| P5 | 배포 | 12 | opal-task-agent | 순차 | `install-mac.sh` 재배포 + 배포본 정합 확인 |

**Batch 1 병렬 가능 여부 판정 (근거 포함)**

| 관계 | 판정 | 근거 |
|------|------|------|
| opdd ∥ opgc ∥ opwt ∥ opsdd ∥ oppl ∥ oppd | **병렬 가능 (6병렬)** | 각 Step의 산출 파일이 `{자기 스킬 디렉토리}/references/pipeline.json` + `{자기 스킬 디렉토리}/SKILL.md` 2개뿐이며 교집합이 공집합. 공유 파일(registry·docs·state_tool.py)은 이 Step들에서 만지지 않는다 |
| opsdd Step의 특수 제약 | 병렬 유지 | `execute-loop-guide.md`·외부 6개 파일은 **접근 자체를 금지**하므로 다른 Step과 충돌 지점이 생기지 않는다 |
| oppd Step의 추가 작업량 | 병렬 유지 | oppd만 미러 표 13행을 **신설**하지만 대상 파일은 동일하게 2개다. 분할 규율(≤3) 충족 |
| **Step 8 (F-008) ∥ pilot Step 6종** | **병렬 가능** | 산출 파일이 `opal/core/references/tools.md` · `opal/core/references/harness/task-process.md` · `opal/skills/op-task/SKILL.md` **3개**로 상한(≤3) 이내이고, pilot 6종·registry·`docs/CONVENTIONS.md`와 교집합이 공집합이다. 입력 의존도 없다(F-008 의존: 없음) |
| Step 8 ↔ Step 1 | **의존 없음** | F-008은 `.md` 파싱 baseline과 무관한 문서 문구 정정이다. 다만 실행 편의상 Batch 1에 함께 배치한다 |
| Step 9 (registry) | **순차 필수** | 단일 파일에 10건을 쓴다 → 병렬 시 write 충돌. 또한 입력(`meta.stages`)이 Step 2~7의 산출물 |
| Step 10 (검증) | **순차 필수** | 전 편집 완료가 입력. 생성자≠검증자 분리를 위해 Step 2~8 담당 에이전트와 분리한다 |
| Step 1 → Step 2~7 | **순차 필수** | 그룹 A baseline·그룹 B 표 원문·하드 실패 증거·`EXECUTE-LOOP` 횟수가 편집 즉시 소실 |

> Step 분할 규율 준수: 편집 Step의 산출 파일은 pilot Step **2개**, F-008 Step **3개**로 전부 상한(≤3) 이내다. 동일 파일을 2개 이상 Step이 만지는 경우는 없다 (`opal/core/references/pm/dispatch-process.md` §Step 6 항목 5).

### 4.2 실행 체크리스트

> 총 12개 Step | Phase 6개 | 실행 모드: **복잡**
>
> **[MUST] 전 Step 공통 금지 4건**
> 1. opsdd 산문 `EXECUTE-LOOP` 표기 17곳 · `references/execute-loop-guide.md` **불가침** (D-7c, H-3)
> 2. oppl `SKILL.md:121` 섹션 헤더 · `:137` 표 헤더 **개명 금지** (DEC-9, H-16)
> 3. oppd 행 구성은 **TASK.md D-7b 확정 13행 고정** — 재설계·가감·재명명 금지 (제약 (g), H-7)
> 4. `opal/tools/state-tool/state_tool.py` · `opal/tools/state-tool/README.md` **불가침** — `.md` 언급은 도구 자신의 에러 메시지·분기 설명이다 (DEC-11, H-18 역방향)

#### Step 1: before 스냅샷 확보 (편집 전 baseline·증거 고정)
- [ ] 완료
- **소속 기능**: F-005, F-006, F-007
- **영역**: 배치
- **agent**: opal-task-agent
- **파일**: `{scratchpad}/eq-verify/probe_before.py`, `{scratchpad}/eq-verify/before/*` (레포 밖 — 레포 파일 **생성·수정 0건**)
- **작업 내용**: §3.5.2 P1 수행. (a) 그룹 A 4종(opdd·opgc·opwt·**opsdd**) × 2 mode `build_rows_from_skill_md` 결과 저장. (b) 그룹 B(oppl) — `SKILL.md:137-157`에 행 정규식 직접 적용해 19행 추출. (c) oppl·oppd `build_rows_from_skill_md`의 `skill_md_parse_error` 페이로드 기록. (d) `grep -c "EXECUTE-LOOP" opsdd/SKILL.md` 값 기록. `init` 서브명령을 쓰지 않는다(파일 미생성).
- **완료 기준**: 그룹 A 8개 JSON(15/7/10/25행 × 2 mode) + `oppl.table.json`(19행) + `oppl.init-failure.json` + `oppd.init-failure.json` + `opsdd.execute-loop-count.txt`(**17**) 존재. 그룹 A가 PLAN §2.1.3·§2.1.4와 4/4 일치, oppl 19행이 §2.1.5와 일치. `git status --porcelain`에 신규 파일 0건.
- **테스트**: TS-002·TS-003·TS-009·TS-016 준비 데이터
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: opdd — pipeline.json 신설 + SKILL.md 전환
- [ ] 완료
- **소속 기능**: F-001, F-003
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-data-design/references/pipeline.json` (신규), `opal/skills/opal-pilot-data-design/SKILL.md` (수정) — **이 2개 외 금지**
- **작업 내용**: ① §3.1.2 ①의 15 task_step으로 pipeline.json 생성 (DEC-1~DEC-7). `DDL/MIGRATION` 3행 key는 `ddl_migration.*` (H-9). ② `:75`·`:241` `--rows-from` 교체, `:241` 플레이스홀더 제거. ③ `:239` 미러 문구 교체. ④ 변경이력 `v1.2` 1행.
- **완료 기준**: `spec-validate` `ok:true`·violations 0. `(stage,item)` 15쌍이 §2.1.3 opdd 표와 문자 단위 동일. `rows-from.*SKILL.md`가 `## 변경이력` 밖 0건.
- **테스트**: TS-001, TS-002, TS-005, TS-007, TS-010, TS-014
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 3: opgc — pipeline.json 신설 + SKILL.md 전환
- [ ] 완료
- **소속 기능**: F-001, F-003
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-gc/references/pipeline.json` (신규), `opal/skills/opal-pilot-gc/SKILL.md` (수정) — **이 2개 외 금지**
- **작업 내용**: ① §3.1.2 ②의 7 task_step. `{ts}`·`[-{element}]` 원문 보존. ② `:116`·`:434`·`:482` `--rows-from` 교체(`--mode` 유무 현행 유지). ③ `:431` `[SSOT]` 블록 재기술. ④ `**파이프라인 현황판 행 구조**` 제목 유지 + 괄호 설명만 미러 문구로 교체. ⑤ 변경이력 `v1.9` (`:534` 이력 행 수정 금지).
- **완료 기준**: `spec-validate` `ok:true`. `(stage,item)` 7쌍이 §2.1.3 opgc 표와 동일. `rows-from.*SKILL.md`가 변경이력 밖 0건.
- **테스트**: TS-001, TS-002, TS-005, TS-007, TS-010, TS-014
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 4: opwt — pipeline.json 신설 + SKILL.md 전환
- [ ] 완료
- **소속 기능**: F-001, F-003
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-write-tech/references/pipeline.json` (신규), `opal/skills/opal-pilot-write-tech/SKILL.md` (수정) — **이 2개 외 금지**
- **작업 내용**: ① §3.1.2 ③의 10 task_step. **`meta.stages`에 `ANALYSIS` 금지** (DEC-4, H-11). ② `:193`·`:431`·`:441` `--rows-from` 교체, `:441` 플레이스홀더 제거. ③ `:428` `[SSOT]` 오기술 정정("`{단계 목록}`을 파싱" → "`references/pipeline.json`을 읽음"). ④ `:439` 미러 문구 교체. ⑤ 변경이력 `v4.7` (`:549` 이력 행 수정 금지).
- **완료 기준**: `spec-validate` `ok:true`. `(stage,item)` 10쌍이 §2.1.3 opwt 표와 동일. `meta.stages`에 `ANALYSIS` 미포함. `rows-from.*SKILL.md`가 변경이력 밖 0건.
- **테스트**: TS-001, TS-002, TS-005, TS-007, TS-010, TS-014
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 5: opsdd — pipeline.json 신설 + SKILL.md 전환 (`EXECUTE-LOOP` 불가침)
- [ ] 완료
- **소속 기능**: F-001, F-003, F-006
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-sdd/references/pipeline.json` (신규), `opal/skills/opal-pilot-sdd/SKILL.md` (수정) — **이 2개 외 금지. 특히 `references/execute-loop-guide.md`는 열지도 마라**
- **작업 내용**: ① §3.1.2 ④의 25 task_step으로 pipeline.json 생성. **[MUST] `meta.stages`는 `["TASK","SPEC","REVIEW","DESIGN","EXECUTE","VERIFY","CLOSE"]` — `EXECUTE-LOOP` 금지** (D-7c, H-2). `id` 1..25 순차·key 유일성 재확인 (H-4). ② `:339`·`:447` `--rows-from` 교체. ③ `:336` `[SSOT]` 블록 재기술. ④ `:342` 오기술 정정("이 파일의 테이블(25행)을 읽어" → "`references/pipeline.json`을 읽어"). ⑤ `:351` 괄호 설명을 미러 문구로 교체(제목 `**파이프라인 현황판**` 유지). ⑥ `:340-346` R-10/R-13 블록 내용 보존 + "행 SSOT는 `references/pipeline.json`" 1문장 보강. `add-row --after 18`은 그대로. ⑦ 변경이력 `v3.7.0` (`:536`·`:540` 이력 행 수정 금지). **⑧ [MUST 금지] 산문 `EXECUTE-LOOP` 17곳 전부 불가침 — 특히 `:332` "단계 목록" 줄을 고치지 않는다.**
- **완료 기준**: `spec-validate` `ok:true`·violations 0(`spec_id_sequence_invalid`·`spec_key_duplicate` 0). `(stage,item)` 25쌍이 §2.1.4 표와 문자 단위 동일. `meta.stages`에 `EXECUTE-LOOP` 미포함. **`grep -c "EXECUTE-LOOP" SKILL.md` = 17** (before와 동일). `execute-loop-guide.md` 변경 0건. `rows-from.*SKILL.md`가 변경이력 밖 0건.
- **테스트**: TS-001, TS-002, TS-005, TS-007, TS-009, TS-010, TS-014
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 6: oppl — pipeline.json 신설 + SKILL.md 전환 (하드 실패 해소 겸)
- [ ] 완료
- **소속 기능**: F-001, F-003, F-007
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-project-loop/references/pipeline.json` (신규), `opal/skills/opal-pilot-project-loop/SKILL.md` (수정) — **이 2개 외 금지**
- **작업 내용**: ① §3.1.2 ⑤의 19 task_step. **[MUST] `item` 특수문자 원문 보존** — 백틱·`—`(U+2014)·`✓`(U+2713)·`{NN}`·`D1.5`를 `SKILL.md:139-157` 원문 그대로 (H-6). `conditional` 금지(DEC-3). ② `:126`·`:442` `--rows-from` 교체. ③ `:133` 괄호 설명을 미러 문구로 교체(제목 유지). ④ `:128` 오기술 정정(§3.3.2(e)). ⑤ `:130` R-10 블록에 1문장 보강. ⑥ `[R-13]` 블록·`--after 13` 그대로. ⑦ 변경이력 `v1.8`. **⑧ [MUST 금지] `:121` 섹션 헤더·`:137` 표 헤더 개명 금지** (DEC-9, H-16).
- **완료 기준**: `spec-validate` `ok:true`. `task_steps[]` 19개가 §2.1.5 표와 문자 단위 동일. `rows-from.*SKILL.md`가 변경이력 밖 0건. `git diff`에 `## STATE.md 초기 생성`·`| # | Stage |` 라인 미출현.
- **테스트**: TS-001, TS-003, TS-005, TS-007, TS-010, TS-014, TS-016
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 7: oppd — pipeline.json 신설 + SKILL.md 전환 + 미러 표 13행 신설 (하드 실패 해소 겸)
- [ ] 완료
- **소속 기능**: F-001, F-003, F-007
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-project-dev/references/pipeline.json` (신규), `opal/skills/opal-pilot-project-dev/SKILL.md` (수정) — **이 2개 외 금지**
- **작업 내용**: ① §3.1.2 ⑥의 13 task_step. **[MUST] TASK.md D-7b 확정표를 그대로 옮긴다 — 재설계·가감·재명명 금지** (DEC-10 / 제약 (g) / H-7). ② `:115` `--rows-from` 교체. ③ **미러 표 13행 신설** — `### STATE.md 초기 생성` 섹션 내 init 코드블록 다음에 §3.3.2(f)의 미러 문구 + `| # | 단계 | 항목 | 상태 | 시점 |` 13행 표 추가. pipeline.json과 1:1 동일해야 한다(H-8). ④ `:117` R-10 블록에 1문장 보강. ⑤ `:153` `--wbs` 설명에 "EXECUTE 행(id 10~12)은 `mark --na` 처리" 1문장 보강. ⑥ `:574-630` STATE.md 템플릿 **불변**. ⑦ 변경이력 `v5.3` (`:808` 이력 행 수정 금지).
- **완료 기준**: `spec-validate` `ok:true`. `task_steps[]` 13개의 `id`·`key`·`stage`·`item`이 TASK.md D-7b 표와 완전 일치. SKILL.md 미러 표 13행이 pipeline.json과 1:1 동일. `rows-from.*SKILL.md`가 변경이력 밖 0건.
- **테스트**: TS-001, TS-004, TS-005, TS-007, TS-010, TS-014, TS-016
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 8: 레포 전역 구형 지시 정정 (pilot 밖 4곳)
- [ ] 완료
- **소속 기능**: F-008
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/core/references/tools.md` (수정), `opal/core/references/harness/task-process.md` (수정), `opal/skills/op-task/SKILL.md` (수정) — **이 3개 외 금지. 특히 `opal/tools/state-tool/state_tool.py`·`opal/tools/state-tool/README.md`는 열지도 마라**
- **작업 내용**: §3.8.2의 4곳을 지정 문자열로 교체한다. ① `tools.md:148` 주석 `# SKILL.md에서 행 구성 자동 파싱` → `# pipeline.json에서 행 구성 자동 파싱`, `:152` `--rows-from ~/.opal/skills/opal-pilot-project/SKILL.md` → `--rows-from ~/.opal/skills/opal-pilot-project/references/pipeline.json` (`--skill opp`·`--mode interactive`·태스크 경로는 불변). ② `tools.md:84` `<path-to-skill.md>` → `<path-to-pipeline.json>`. ③ `task-process.md:49` 행 원천 서술을 "오케스트레이터 `references/pipeline.json`이 SSOT" 로 정정(`--rows-spec` 언급 보존, `:51` 근거 줄 보존). ④ `op-task/SKILL.md:223` 동일 문구로 정정(인용 꼬리 `(PLAN §2.3)` 보존). ⑤ 3개 파일 각각 변경이력 1행 추가(`tools.md` v2.12 / `task-process.md` v1.7 / `op-task/SKILL.md` v2.5, KST 일시 + `(090)`). **⑥ [MUST 금지] `state_tool.py`·`state-tool/README.md`의 `.md` 언급은 도구 자신의 에러 메시지·분기 설명이므로 정정 대상이 아니다 (DEC-11).** **⑦ `tools.md:81`의 `--skill` enum에 `oppl`·`opdd`가 빠진 것은 범위 밖이므로 건드리지 않는다** (§9 R-17).
- **완료 기준**: 4곳 전부 지정 문자열로 교체됨. 레포 전역 스캔(§3.5.2 P4-b)에서 `.md` 파싱 지시 **0건**(pilot 변경이력 행·도구 자신 2파일 제외). `git status --porcelain -- opal/tools/state-tool/state_tool.py opal/tools/state-tool/README.md` 결과 **0줄**. 3개 파일 변경이력 1행씩 추가.
- **테스트**: TS-018 (S-18), TS-014
- **실행 방법**: sub-agent
- **의존**: 없음 (Batch 1 병렬 편입 — 파일 비중첩)

#### Step 9: registry `pipeline` 필드 10종 정합화 + oppd `domain` 보강
- [ ] 완료
- **소속 기능**: F-004
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/core/references/opal-skills-registry.json` (수정, 단일 파일)
- **작업 내용**: §3.4.2 확정 표대로 **10종** `pipeline` 값 교체/신설(opdd 무변경). **opsdd 값은 `TASK → SPEC → REVIEW → DESIGN → EXECUTE → VERIFY → CLOSE` — `EXECUTE-LOOP` 금지**. oppd에 `"domain": "dev"` 추가. `version` `"3.9.0"`→`"3.10.0"`, `updated_at` 작업일(KST). `changelog[]` 선두에 `{version:"3.10.0", date, task:"090", changes:[...]}` 추가하며 "10/10 pilot pipeline.json 전환 완료" 명시. `groups` 구조·기존 필드명 불변.
- **완료 기준**: JSON 파싱 성공. 10종 전부 `pipeline` 존재하고 `" → "` split 결과가 해당 `meta.stages`와 순서·원소 완전 일치. oppd `domain` 존재. opsdd 값에 `EXECUTE-LOOP` 미포함. `skill-registry.js` 소비 필드 무변경.
- **테스트**: TS-008, TS-014
- **실행 방법**: sub-agent
- **의존**: Step 2, 3, 4, 5, 6, 7 (`meta.stages` 확정 필요). Step 8(F-008)과는 무관

#### Step 10: 전수 검증 + 무변경 보장 + 해소 실증 + 임시 산출물 정리
- [ ] 완료
- **소속 기능**: F-005, F-006, F-007, F-008(검증)
- **영역**: 배치
- **agent**: opal-task-agent
- **파일**: `{scratchpad}/eq-verify/**` (레포 밖, 종료 시 삭제). 레포 파일 **생성·수정 0건**
- **작업 내용**: §3.5.2의 P2~P9를 순서대로 수행. ① 10 pilot × 2 mode = 20회 `init` 실행, `rows[]`·`rows_count` 추출. ② 그룹 A 4종 before/after 완전 대조, 그룹 B(oppl) 3자, 그룹 C(oppd) D-7b 3자. ③ agentic na 집합 대조(oppd id 6·9 비대상 확인 포함). ④ 잔존 grep(6종, 변경이력 제외) + 채택 grep(10 파일) + deprecated 호출자 0건 확인. **④-b P4-b 레포 전역 잔존 스캔** — pilot 밖 `.md` 파싱 지시 0건 + 도구 자신 2파일(`state_tool.py`·`state-tool/README.md`) **역방향 무변경**(`git status` 0줄) 확인. ⑤ `spec-validate` 10건. ⑥ registry 파생 대조 10종 + oppd `domain` + opsdd `EXECUTE-LOOP` 미포함. ⑦ opsdd `EXECUTE-LOOP` 17회 + `execute-loop-guide.md` 0건 + 외부 6파일 0건. ⑧ oppl 개명 금지 diff + oppd 미러 표 정합. ⑨ oppl·oppd 해소 증거 쌍 구성. ⑩ `rm -rf $WORK` + `git status --porcelain`.
- **완료 기준**: (1) 그룹 A 4/4 완전 동일. (2) oppl 3자 19개·oppd 3자 13개 완전 일치. (3) 20회 init 전부 exit 0·`ok:true`·`schema_version:"1.1"`·전 행 `key` 보유. (4) 대상 6 SKILL.md에서 `rows-from.*SKILL.md`가 변경이력 밖 0건 / `rows-from.*references/pipeline.json` 매칭 파일 **10개** / deprecated 호출자 0건. **(4-b) 레포 전역(`opal/`·`docs/`·`README.md`)에서 `.md` 파싱 지시 0건 — pilot 변경이력 행·도구 자신 2파일만 예외. `state_tool.py`·`state-tool/README.md` 변경 0줄(역방향).** (5) `spec-validate` 10/10 `ok:true`·violations 0. (6) registry 10/10 정합 + oppd `domain` 존재. (7) deprecation 경고 0회. (8) opsdd `EXECUTE-LOOP` 17회 동일 + 관련 7개 파일 변경 0건. (9) oppl `rows_count: 19` · oppd `rows_count: 13`, before 실패 기록과 쌍으로 제시. (10) `$WORK` 삭제됨, `git status --porcelain`에 임시 파일 0건, `tasks/080~089` 미변경.
- **테스트**: TS-002~TS-013, TS-016, TS-017, **TS-018 (S-18)**
- **실행 방법**: sub-agent
- **의존**: Step 9 (Step 8 완료도 선행 — 레포 전역 스캔의 입력)

#### Step 11: docs/ 갱신 — CONVENTIONS.md §State 규칙 1줄 추가
- [ ] 완료
- **소속 기능**: F-003 (규칙 고정)
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/CONVENTIONS.md` (§State 관리 + §변경이력)
- **작업 내용**: §State 관리(`:224-230`)에 1줄 추가 — "`state-tool init --rows-from`은 pilot `references/pipeline.json`을 지정한다. SKILL.md 마크다운 파싱(`build_rows_from_skill_md`)은 deprecated이며 신규 지시에 사용 금지 — **10/10 pilot 전환 완료(090)**." 문서 말미 `## 변경이력` 표에 1행 추가.
- **완료 기준**: 해당 문장이 §State 관리에 존재하고, 기존 4개 불릿과 근거 줄이 보존됨. 변경이력 1행 추가.
- **테스트**: TS-014
- **실행 방법**: direct
- **의존**: Step 10

#### Step 12: 배포 재적용 + 배포본 정합 확인
- [ ] 완료
- **소속 기능**: F-001, F-003
- **영역**: 환경
- **agent**: opal-task-agent
- **파일**: 없음 (실행만). `~/.opal/`은 **install 스크립트를 통해서만** 갱신
- **작업 내용**: `./scripts/install-mac.sh` 실행. 완료 후 `~/.opal/skills/opal-pilot-*/references/pipeline.json` **10개** 존재 확인 및 소스와 `diff` 0 확인. 배포본을 직접 편집하지 않는다.
- **완료 기준**: install 정상 종료. 배포본 pipeline.json 10건 존재, 전 10건 `diff` 0. 변경 파일 목록이 전부 `opal/`·`docs/`·`tasks/` 하위.
- **테스트**: TS-015
- **실행 방법**: sub-agent
- **의존**: Step 11

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 → Step 2~7 | 그룹 A `.md` baseline·그룹 B 표 원문·oppl/oppd 하드 실패 증거·opsdd `EXECUTE-LOOP` 횟수가 SKILL.md 편집 즉시 소실된다 |
| Step 2 ∥ 3 ∥ 4 ∥ 5 ∥ 6 ∥ 7 | 각 Step의 산출 파일 2개가 서로 다른 스킬 디렉토리에 속해 교집합 공집합. 공유 파일 미접촉 |
| Step 2 ∥ … ∥ 7 ∥ **8** | Step 8(F-008)은 `tools.md`·`task-process.md`·`op-task/SKILL.md` 3파일만 만지며 pilot 6종·registry·`docs/CONVENTIONS.md`와 교집합이 공집합이다. 입력 의존도 없어 Batch 1에 병렬 편입한다 |
| Step 2~7 → Step 9 | registry `pipeline` 값이 각 pipeline.json `meta.stages`에서 파생됨 (입력 의존). Step 8과는 무관 |
| Step 9 단독 | 단일 파일 `opal-skills-registry.json`에 10건을 쓰므로 분할 시 write 충돌 |
| Step 8·9 → Step 10 | 검증 P6(registry 정합)이 Step 9 산출물을, P4-b(레포 전역 스캔)가 Step 8 산출물을 입력으로 받음 |
| Step 10 → Step 11 | 규칙 문서화는 실증 통과 후에만 의미가 있음 (실패 시 규칙을 못 박으면 안 됨) |
| Step 11 → Step 12 | 배포는 소스 확정 후 마지막 |
| Step 1·10 ↔ 레포 | 두 Step 모두 레포 파일을 만들지 않는다 — 스크래치패드 전용 (H-14) |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | 6 pilot pipeline.json 생성 + 스키마 무결 | TS-001, TS-010 | 6개 파일 존재·JSON 파싱 성공, `spec-validate` 10건 `ok:true`·`violations_count:0` |
| F-001 | 전후 행 구성 동등 — 그룹 A 4종 | TS-002 | opdd·opgc·opwt·opsdd의 before vs after `[(row_id, stage, item)]`가 4/4 완전 동일 (15·7·10·25행). 1건이라도 불일치 시 FAIL |
| F-001 | oppl 표 기준 3자 대조 — 그룹 B | TS-003 | 추출 19행 == `task_steps` 19개 == after rows 19개. 백틱·`—`·`✓`·`{NN}`·`D1.5` 포함 문자 단위 동일 |
| F-001 | oppd D-7b 확정표 3자 대조 — 그룹 C | TS-004 | D-7b 13행 == `task_steps` 13개 == after rows 13개. `id`·`key`·`stage`·`item` 전부 일치 (재설계 흔적 0) |
| F-001 | opsdd `meta.stages` 정합 | TS-008, TS-010 | `["TASK","SPEC","REVIEW","DESIGN","EXECUTE","VERIFY","CLOSE"]` — `EXECUTE-LOOP` 미포함, `spec_stage_invalid` 0건 |
| F-001 | agentic 자동 na 규칙 회귀 | TS-011 | `status=="na"` 집합 == `{item=="사용자 확인" and stage!="CLOSE"}`. 그룹 A는 before와도 동일. oppd id 2·12만 na, id 6·9는 비대상 |
| F-003 | `.md` 파싱 경로 잔존 0 (대상 6종) | TS-005 | 대상 6 SKILL.md에서 `rows-from.*SKILL\.md`가 `## 변경이력` 섹션 밖 **0건** (D-9) |
| F-003 | `.json` 경로 채택 10/10 | TS-006 | 대상 6 SKILL.md 각각 1건 이상. 전체 `opal-pilot-*/SKILL.md` 중 매칭 파일 **10개** |
| F-003 | 미러 주석 + oppd 미러 표 + oppl 개명 금지 | TS-007 | 6 pilot 전부 미러 문구 존재. oppd 13행 미러 표 신설 후 `task_steps`와 1:1 동일. oppl `:121`·`:137` 라인이 diff에 미출현 |
| F-004 | registry 10종 정합 + oppd `domain` | TS-008 | 10종 전부 `pipeline` 존재, `" → "` split == 해당 `meta.stages`. oppd `domain` 존재. `skill-registry.js` 소비 필드 무변경 |
| F-005 | `spec-validate` 전수 (10건) | TS-010 | 10건 전부 `ok:true` / `violations_count: 0` / exit 0 |
| F-005 | 임시 산출물 미잔류 | TS-012 | `$WORK` 삭제 완료, `git status --porcelain`에 임시 `state.json`/`STATE.md` 0건, `tasks/080~089` 미변경 |
| F-005 | deprecated 경로 미호출 | TS-013 | 20회 init 중 deprecation 경고 출력 0회 |
| F-005 | **deprecated 경로 호출자 0건** (완료기준 8) | TS-017 | `opal-pilot-*/SKILL.md`에서 `rows-from.*SKILL.md`가 변경이력 행에만 존재 |
| F-006 | opsdd `EXECUTE-LOOP` 산문 무변경 | TS-009 | 등장 횟수 **17회 전후 동일**, `execute-loop-guide.md` 변경 0건(리네임 포함), 외부 6개 파일 변경 0건 |
| F-007 | oppl·oppd `init` 하드 실패 해소 | TS-016 | 두 pilot 각각 before `skill_md_parse_error` 기록 + after exit 0·`ok:true`·`rows_count` 19 / 13. 증거가 쌍으로 제시됨 |
| F-008 | **레포 전역 구형 지시 정정 (4곳)** | TS-018 | `tools.md:84`·`:148`·`:152`, `task-process.md:49`, `op-task/SKILL.md:223`이 §3.8.2 지정 문자열로 교체됨. 레포 전역 `.md` 파싱 지시 **0건**(pilot 변경이력 행·도구 자신 2파일 제외) |
| F-008 | **도구 자신 2파일 역방향 무변경** | TS-018 | `git status --porcelain -- opal/tools/state-tool/state_tool.py opal/tools/state-tool/README.md` 결과 **0줄** (DEC-11) |
| F-001~F-003 | 배포 경계 준수 + 배포본 정합 | TS-015 | 변경 파일이 전부 `opal/`·`docs/`·`tasks/` 하위. install 후 배포본 pipeline.json 10건, 전 10건 `diff` 0 |

### 5.2 회귀 테스트

- [ ] 전환 완료 4 pilot(opd·opds·opdw·opp)의 `pipeline.json`·`SKILL.md`가 **내용 무변경**이다 (registry 값만 바뀐다)
- [ ] 4 pilot의 `spec-validate`가 이번 변경 전후 동일하게 `ok:true`다
- [ ] 4 pilot의 `.json` init이 20회 실행 중 전부 exit 0이다
- [ ] `opal/tools/state-tool/state_tool.py`가 `git diff`에서 **0줄 변경**이다 (제약 (a))
- [ ] `opal/tools/state-tool/schema/state.schema.json`이 무변경이다 (신규 `stage`·`skill` enum 추가 불필요 — 전부 기등록)
- [ ] 기존 태스크 폴더(`tasks/080`~`tasks/089`)의 `state.json`·`STATE.md`가 무변경이다 (제약 (d))
- [ ] `opal-skills-registry.json`의 `groups` 구조·`name`/`alias`/`description`/`triggers`/`paths` 필드가 무변경이다
- [ ] 최상위 `pm_gate` 배열이 **신규 6 파일에 없다**(D-2) / **기존 4 파일에서 삭제되지 않았다**(D-3)
- [ ] 대상 pilot SKILL.md의 기존 행 표가 **삭제되지 않고 존치**한다 (D-5). oppd는 신설이므로 해당 없음
- [ ] 대상 6 pilot SKILL.md의 `## 변경이력` 기존 행이 **개변되지 않았다** (D-9)
- [ ] opsdd SKILL.md의 `[R-13]` 블록과 `add-row --after 18` 지시가 보존되고 `id: 18`과 정합한다
- [ ] oppl SKILL.md의 `[R-13]` 블록과 `add-row --after 13` 지시가 보존되고 `id: 13`과 정합한다
- [ ] oppd SKILL.md의 `## STATE.md 관리` 템플릿(`:574-630`)이 무변경이다
- [ ] **opsdd 산문 `EXECUTE-LOOP` 17곳 + `execute-loop-guide.md` + 외부 6개 파일이 0건 변경이다** (제약 (f))
- [ ] **`opal/tools/state-tool/state_tool.py`·`opal/tools/state-tool/README.md`가 0건 변경이다** — 도구 자신의 에러 메시지·분기 설명은 정정 대상이 아니다 (DEC-11, S-18 역방향)
- [ ] `opal/core/references/tools.md`의 `--rows-spec` 옵션 설명·`--skill` enum 줄(`:81`)·나머지 서브명령 예시가 무변경이다 (R-9는 `.md` 파싱 지시에만 한정)
- [ ] `opal/core/references/harness/task-process.md:51`의 `근거:` 인용 줄과 `opal/skills/op-task/SKILL.md:223`의 `(PLAN §2.3)` 인용 꼬리가 보존된다

### 5.3 코드/문서 품질

- [ ] 변경한 6 SKILL.md 전부 `## 변경이력`에 1행 추가, 일시 KST `YYYY-MM-DD HH:mm`, 말미 `(090)` — **[MUST]** `docs/CONVENTIONS.md` §변경이력 작성 의무
- [ ] `docs/CONVENTIONS.md` 변경이력 1행 추가
- [ ] **F-008 대상 3파일(`tools.md` v2.12 / `task-process.md` v1.7 / `op-task/SKILL.md` v2.5) 변경이력 1행씩 추가** — **[MUST]** `docs/CONVENTIONS.md` §변경이력 작성 의무
- [ ] F-008 정정 문구가 3파일에서 **동일 취지**로 일관된다 (`task-process.md:49`와 `op-task/SKILL.md:223`은 복제 관계)
- [ ] `opal-skills-registry.json` `changelog[]` 1항목 추가 + `version`/`updated_at` 승격, 문구에 "10/10 전환 완료" 명시
- [ ] 신규 6 pipeline.json이 전환 완료 4종과 동일한 키 순서(`spec_version`→`skill`→`meta`→`task_steps`)·들여쓰기 스타일을 따른다
- [ ] 신규 6 pipeline.json에 `agent`/`model`/`inputs`/`outputs`/`gate`/`conditional` 필드가 없다 (D-1, DEC-3)
- [ ] **oppd `task_steps`가 TASK.md D-7b 확정표와 완전 일치하며 재해석 흔적이 없다** (제약 (g), DEC-10)
- [ ] **opsdd `meta.stages`에 `EXECUTE-LOOP`이 없고 산문 표기는 그대로다** (D-7c, DEC-8)
- [ ] `~/.opal/` 하위를 직접 편집하지 않았다 — **[MUST]** `docs/CONVENTIONS.md` §배포 경계
- [ ] 하네스 관련 규칙 변경은 `opal/core/references/opal-harness.md`(SSOT) 또는 `docs/CONVENTIONS.md`에서만 이뤄졌고 다른 곳에 복제되지 않았다
- [ ] PLAN.md의 모든 설계 결정에 인용(`경로:줄번호` / `경로 §N` / `(→ D-N)`)이 붙어 있다
- [ ] PLAN.md·산출물 어디에도 외부 프로젝트 경로·파일명이 기재되지 않았다 (oppd 선례는 "실사용 선례 8행(PM 제공)"으로만 표기)

### 5.4 보안

- [ ] 신규·수정 파일에 토큰·시크릿·개인정보 하드코딩이 없다 (전부 파이프라인 단계 메타데이터)
- [ ] 검증 스크립트가 임의 경로를 `rm -rf` 하지 않는다 — 삭제 대상은 `$WORK` 단일 경로로 고정하고, 실행 전 `$WORK`가 스크래치패드 하위인지 검사한다
- [ ] `init` 실행 경로가 레포 트리 밖으로 제한되어 기존 태스크 `state.json` 덮어쓰기가 구조적으로 불가능하다 (H-14)
- [ ] `.gitignore` 변경 없음 — 임시 산출물을 레포에 만들지 않으므로 무시 규칙 추가가 불필요하다

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 12개 (기준 5개 초과) | 복잡 |
| 변경 파일 수 | **17개** — 신규 6 + 수정 11(pilot SKILL.md 6 · registry 1 · CONVENTIONS.md 1 · **F-008 3**) | 복잡 |
| 모듈 범위 | 다중 (6 pilot 스킬 + core references 3 + op-task 스킬 + docs + 배포) | 복잡 |
| 작업 유형 | 마이그레이션(대규모 개선) + 결함 해소 2건 + 레포 전역 문서 정합 | 복잡 |
| 외부 의존성 | 없음 (state-tool 기존 CLI만 사용, 신규 패키지 0) | 단순 |
| **실행 모드** | **복잡** | 5기준 중 4개 해당 |

> P0 리스크 **7건**(H-1 전후동등 / H-2 opsdd `EXECUTE-LOOP` 오기입 / H-3 개명 연쇄 / H-5 oppl baseline / H-7 oppd 확정표 이탈 / H-14 임시 잔류 / **H-18 pilot 밖 구형 지시**)은 **전부 기계 검증 가능**하다. 설계 판단이 필요한 리스크는 D-7b(oppd 확정)·D-7c(opsdd 개념 분리) 확정으로 제거되었다.
> **자동 대조 커버리지**: 전체 79행 중 그룹 A 57행(72%)이 before/after 완전 자동 대조 대상이고, 나머지 22행(oppl 19 + oppd 3자 대조 13 중 문서 기준분)은 문서 기준값 대조로 커버한다.

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

```
Batch 0 ── A0: opal-task-agent  [Step 1]  before 스냅샷 (레포 미접촉, 6종 + EXECUTE-LOOP 횟수)
              │
Batch 1 ──────┼── A1: opal-task-agent [Step 2] opdd   (pipeline.json + SKILL.md)
              ├── A2: opal-task-agent [Step 3] opgc   (pipeline.json + SKILL.md)
              ├── A3: opal-task-agent [Step 4] opwt   (pipeline.json + SKILL.md)
              ├── A4: opal-task-agent [Step 5] opsdd  (pipeline.json + SKILL.md, EXECUTE-LOOP 불가침)
              ├── A5: opal-task-agent [Step 6] oppl   (pipeline.json + SKILL.md, 헤더 개명 금지)
              ├── A6: opal-task-agent [Step 7] oppd   (pipeline.json + SKILL.md + 미러 표 신설)
              └── A7: opal-task-agent [Step 8] pilot 밖 4곳 (tools.md · task-process.md · op-task/SKILL.md)
              │
Batch 2 ── A8: opal-task-agent  [Step 9]  registry 10종 + oppd domain (단일 파일, 단독)
              │
Batch 3 ── A9: opal-task-agent  [Step 10] 전수 검증 + 무변경 보장 + 해소 실증 + 정리 (레포 미접촉)
              │
Batch 4 ── PM 직접              [Step 11] docs/CONVENTIONS.md
              │
Batch 5 ── A10: opal-task-agent [Step 12] install 재배포 + 배포본 diff
```

**그룹핑 근거**
1. **파일 충돌 방지** — 동일 파일을 만지는 Step이 하나도 중복되지 않도록 pilot 단위로 에이전트를 1:1 배정했다. `opal-skills-registry.json`을 만지는 Step은 Step 9 하나뿐이고, pilot 밖 3파일을 만지는 Step은 Step 8 하나뿐이다.
2. **모듈 응집도** — 한 pilot의 `references/pipeline.json`과 `SKILL.md`는 서로의 정합성 검사 대상이므로 같은 에이전트가 순차 편집한다. oppd는 미러 표 신설까지 같은 에이전트가 처리해야 H-8을 막는다.
3. **병렬 극대화** — Batch 1에서 **7 에이전트** 동시 실행. 산출 파일은 pilot 에이전트 2개·A7(F-008) 3개로 전부 분할 규율(≤3) 충족.
4. **생성자≠검증자** — Batch 3(A9)은 Batch 1·2와 다른 에이전트다. Step 2~8 담당 에이전트는 자기 산출물의 최종 판정을 하지 않는다 — A7이 정정한 4곳도 A9가 레포 전역 스캔으로 재검증한다.
5. **금지 규칙 주입** — 모든 에이전트 프롬프트에 §4.2 서두의 **공통 금지 4건**(opsdd `EXECUTE-LOOP` / oppl 헤더 / oppd D-7b 고정 / **도구 자신 2파일 불가침**)을 명시 주입한다. A4·A5·A6·**A7**에는 해당 전용 금지를 재차 강조한다.

### C-2. 스킬 요구사항

| 필요 역량 | 매칭 스킬 | 갭 |
|----------|----------|-----|
| EXECUTE 단계 수행 | `op-dev-execute` (`opal/skills/op-dev-execute/SKILL.md`) | 없음 |
| pipeline.json 구조 준수 | 견본 파일 4종 + 본 PLAN §3.1.2 명세 | 없음 — 동일 패턴 6회이나 산출물 내용이 §3.1.2에 전량 확정되어 인라인 지침으로 충분 |
| 전후 동등 검증 (3그룹) | 전용 스킬 없음 → 본 PLAN §3.5.2 절차를 인라인 지침으로 제공 | 없음 (1회성 검증) |

### C-3. 도구 요구사항

| 도구 | 용도 | 상태 |
|------|------|------|
| `~/.opal/tools/state-tool/run.sh init` | after 스냅샷 생성 (20회) | 기존 배포본, 변경 없음 |
| `~/.opal/tools/state-tool/run.sh spec-validate` | 스펙 무결성 10건 | 기존 배포본 |
| Python 3 (표준 라이브러리) | `state_tool.py` 모듈 로드 프로브 · 행 정규식 추출 · JSON 대조 | 설치됨 |
| `grep -rn` / `grep -c` / `awk` / `git status --porcelain` / `git diff` / `diff` | 잔존(pilot·**레포 전역**)·채택·`EXECUTE-LOOP` 횟수·개명금지·**도구 자신 역방향**·잔류 검증 | 기본 |
| `./scripts/install-mac.sh` | 배포 재적용 | 기존 |
| `date`(KST) | 변경이력 일시 취득 | 기존 |

### C-4. 테스트 전략

- **기능 테스트**: TS-001·TS-010·TS-016 — `spec-validate` 10건 + `init` 20회 + 하드 실패 해소 증거 쌍.
- **회귀 테스트**: TS-002·TS-003·TS-004·TS-009·TS-011·TS-013 + §5.2 체크리스트 14항목. 핵심은 3그룹 대조와 `EXECUTE-LOOP` 무변경.
- **산출물 검사**: TS-005·TS-006·TS-007·TS-008·TS-017·**TS-018** — grep·awk·JSON 파생 대조. TS-018은 레포 전역 스캔 + 도구 자신 2파일 역방향 무변경.
- **정리/경계**: TS-012·TS-015 — `git status --porcelain` + 배포본 `diff`.
- **실행 주체**: EXECUTE 내 검증은 Step 9(opal-task-agent)가 수행하고, TEST 단계에서 `opal-test-agent`가 TEST-SCENARIO.md 기준으로 재수행한다.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 데이터 | JSON (pipeline.json 스펙, registry) | - |
| 문서 | Markdown (SKILL.md, docs/) | - |
| 도구 | Python 3 (`state_tool.py` — **읽기 전용 소비**) | - |
| 검증 | Bash + Python 3 표준 라이브러리 | - |
| 배포 | Bash (`install-mac.sh`) | - |

> React/Next.js/shadcn/Python 패키징 등 커뮤니티 스킬 적용 대상 기술이 없다. `trailofbits/modern-python`은 Python **소스 변경**이 있을 때 참조하나 이번 태스크는 `state_tool.py` 무변경이므로 해당 없음.

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| (없음) | 외부 라이브러리 API 의존이 없어 context7·shadcn MCP 조회 불필요. 모든 계약이 프로젝트 내부 소스(`state_tool.py`)에 있어 직접 Read로 확인 |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py` | `STAGE_ENUM`(:31-39)·`KEY_PATTERN`(:41)·`stage_to_slug`(:44-46)·`build_rows_from_skill_md`(:768-858)·`validate_pipeline_spec`(:875-934)·`build_rows_from_pipeline_json`(:937-972)·`cmd_init`(:1052-1200)·`cmd_spec_validate`(:1649-1663)·`_auto_row_key`(:1667-1690) 계약 |
| D-2 | 소스 | state_tool.py — 검증 필수 필드 | `opal/tools/state-tool/state_tool.py:890` | 최상위 필수 4종(`spec_version`/`skill`/`meta`/`task_steps`) — DEC-1 근거 |
| D-3 | 설계 | state.schema.json | `opal/tools/state-tool/schema/state.schema.json:15-16, :61` | `skill` enum 10종·`stage` enum 19종 — 대상 6 pilot 전부 기등록 확인, `EXECUTE-LOOP` 미등록 확인 |
| D-4 | 설계 | opd pipeline.json (견본) | `opal/skills/opal-pilot-dev/references/pipeline.json` | 구조·key 어휘 기준 (DEC-2·DEC-6), `meta.stages` 실측 |
| D-5 | 설계 | opds pipeline.json (견본) | `opal/skills/opal-pilot-dev-short/references/pipeline.json` | 들여쓰기·1줄/step 스타일 기준 (DEC-7), `meta.stages` 실측 |
| D-6 | 설계 | opp / opdw pipeline.json | `opal/skills/opal-pilot-project/references/pipeline.json:4`, `opal/skills/opal-pilot-dev-wireframe/references/pipeline.json:4` | F-004 registry 파생용 `meta.stages` 실측 |
| D-7 | 설계 | 스킬 레지스트리 | `opal/core/references/opal-skills-registry.json` | `pipeline` 현행값(:21,:37,:52,:67,:83,:99,:116,:132,:162)·oppd 결측(:130-143)·`version`/`changelog`(:3-4,:770)·`domain` 관행(:36,:51,:159) |
| D-8 | 소스 | opdd SKILL.md | `opal/skills/opal-pilot-data-design/SKILL.md:75, :232-262` | init 호출부·모드 라벨(:236)·15행 baseline |
| D-9 | 소스 | opgc SKILL.md | `opal/skills/opal-pilot-gc/SKILL.md:116, :424-450, :482, :534` | init 호출 3곳·모드 라벨(:427)·7행 baseline·변경이력 행 위치 |
| D-10 | 소스 | opwt SKILL.md | `opal/skills/opal-pilot-write-tech/SKILL.md:193, :419-456, :549` | init 호출 3곳·`{단계 목록}` 파싱 오기술(:428)·10행 baseline |
| D-11 | 소스 | opsdd SKILL.md | `opal/skills/opal-pilot-sdd/SKILL.md:327-382, :447, :536, :540` | init 호출 4곳·모드 라벨(:331)·`EXECUTE-LOOP` 라벨 줄(:332)·25행 baseline(:358-382)·R-13 `add-row --after 18`(:346) |
| D-12 | 소스 | oppl SKILL.md | `opal/skills/opal-pilot-project-loop/SKILL.md:121-157, :442` | 파서 미검출 원인(헤더 :121·`Stage` 열 :137)·19행 표 원문(:139-157)·오기술(:128) |
| D-13 | 소스 | oppd SKILL.md | `opal/skills/opal-pilot-project-dev/SKILL.md:110-155, :574-630, :808` | 행 표 부재 실증·Phase 구조(:139-147, :585-590)·R-10 규정(:117)·`--wbs` 플래그(:153)·STATE.md 템플릿 |
| D-14 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` §State 관리(:224-230), §배포 경계(:244-250), §변경이력 작성 의무(:238-243), §Citation Rules(:218-223) | [MUST] 제약 4종 |
| D-15 | 설계 | 하네스 State 절 | `opal/core/references/opal-harness.md:142` §3 State | state-tool 전용 사용 의무 |
| D-16 | 설계 | 인용 규칙 | `opal/core/references/harness/citation-rules.md` §2·§3 | 산출물 근거 기재 포맷 |
| D-17 | 설계 | PROJECT.md | `docs/PROJECT.md` §프로젝트 구성 | Framework 영역(`opal/`, `skills/`) 전문 에이전트 = `opal-task-agent`(범용) |
| D-18 | 설계 | 디스패치 프로세스 | `opal/core/references/pm/dispatch-process.md` §Step 6 항목 5 | Step 분할 규율(산출 3개 초과 시 비중첩 분할, 동일 파일 다중 Step 금지) |
| D-19 | 소스 | install-mac.sh | `scripts/install-mac.sh:1061-1068` | 스킬 디렉토리 통째 복사 — pipeline.json 자동 배포 근거 |
| D-20 | 설계 | 모드 경계 SSOT | `opal/core/references/opal-harness-semi-agentic.md:32` | `EXECUTE-LOOP` 토큰 외부 참조처 (개명 금지 근거, D-7c) |
| D-22 | 가이드 | state-tool 사용 가이드 | `opal/core/references/tools.md:81, :84, :148-152` | F-008 정정 대상 — 시놉시스 인자 표기·실행 예시 구형 경로. `--skill` enum 결측(범위 밖 관측) |
| D-23 | 가이드 | 하네스 TASK 절차 | `opal/core/references/harness/task-process.md:49, :51` | F-008 정정 대상 — 행 원천 지시. `:51` 근거 줄 보존 대상 |
| D-24 | 스킬 | op-task SKILL.md | `opal/skills/op-task/SKILL.md:223` | F-008 정정 대상 — `task-process.md:49`와 복제 관계 |
| D-25 | 소스 | state-tool 도구 자신 | `opal/tools/state-tool/state_tool.py:104, :769, :1131` / `opal/tools/state-tool/README.md` | **불가침 근거** — `.md` 언급이 ERROR_CODES·docstring·deprecation 경고 문자열임을 확인 (DEC-11, S-18 역방향) |
| D-21 | 기획 | TASK.md | `tasks/090-260813-opds-파이프라인-스펙-마이그레이션/TASK.md` | 요구사항 R-1~**R-9**·확정 방향 D-1~**D-10**(D-7a·D-7b·D-7c 포함)·제약 조건 (a)~(g)·완료기준 **(0)**·oppd 확정 13행 표 |

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | **전후 동등 파괴** — `item` 문자열 오타/공백 차이로 baseline과 어긋남 (H-1) | F-001 | P0 — pilot STATE 골격이 조용히 변경됨 | Step 9에서 그룹 A 4종 프로그램 대조. 1건 불일치 시 즉시 중단·롤백. 기준값을 PLAN §2.1.3·§2.1.4에 박제해 2중화 |
| R-2 | **opsdd `meta.stages`에 `EXECUTE-LOOP` 오기입** (H-2) | F-001, F-004 | P0 — `spec_stage_invalid`로 init 불가 + registry 연쇄 오염 | DEC-4를 "행 stage 등장순 중복 제거"로 고정해 라벨 줄 참조 자체를 차단. Step 5 완료 기준에 `EXECUTE-LOOP` 미포함 검사 + `spec-validate` 포함 |
| R-3 | **`EXECUTE-LOOP` 개명 연쇄 — 8개 파일 41곳** (H-3) | F-006 | P0 — 형식 이관이 문서 개편으로 변질 | 4중 가드(§3.6.2): 편집 범위 열거 / `execute-loop-guide.md` 대상 파일 미포함 / DEC-4로 발화점 제거 / Step 9 P7 사후 검출(17회 동일·7개 파일 0건) |
| R-4 | **opsdd 25행 `id` 순차·`key` 유일성 위반** (H-4) | F-001 | P1 — init 불가 | §3.1.2 ④에 25행 전량을 `id`·`key` 확정값으로 명세. Step 5 완료 기준에 `spec-validate` `violations_count:0` |
| R-5 | **oppl baseline 도출 오류** — 파서 before가 없어 자동 대조로 못 잡음 (H-5) | F-001 | P0 | 3자 대조(추출 19행 ↔ `task_steps` ↔ after rows)로 커버. `rows_count: 19` 이중 확인. §2.1.5에 표 원문 박제 |
| R-6 | **oppl `item` 특수문자 훼손** (H-6) | F-001 | P1 | §3.1.2 ⑤에 보존 규칙 6항목을 [MUST]로 명시. 문자 단위 대조로 검출 |
| R-7 | **oppd D-7b 확정표 이탈** (H-7) | F-001 | P0 — 잘못된 골격이 SSOT로 고정 | DEC-10 + 제약 (g). §3.1.2 ⑥에 확정표 전재. Step 7 완료 기준에 `id`·`key`·`stage`·`item` 완전 일치 |
| R-8 | **`--rows-from` 경로가 프로젝트 상대경로** — 다른 프로젝트에서 `opal/skills/...`가 없어 실패 가능 | F-003 | P2 — 기존 4 pilot에도 동일 존재(선행 결함) | 전환 완료 4종과 동일 표기를 유지한다(동등 이관 원칙). 경로 표기 통일은 별도 태스크로 일괄 처리 |
| R-9 | **부분 전환 상태의 문서 모순** — 한 SKILL.md 내 여러 init 호출 중 일부만 교체 (H-13) | F-003 | P1 | §2.3.2의 전수 위치 표를 Step별 작업 내용에 그대로 인용. 각 Step 완료 기준에 "해당 파일 내 `rows-from.*SKILL.md` 변경이력 밖 0건" 포함 |
| R-10 | **임시 산출물 레포 잔류 / 기존 `state.json` 덮어쓰기** (H-14) | F-005 | P0 — 제약 (d) 위반 | `init` 실행 경로를 스크래치패드로 고정. Step 9 완료 기준에 `rm -rf $WORK` + `git status --porcelain` 검사 포함. 삭제 전 경로 검사 |
| R-11 | **배포 경계 위반** (H-15) | F-001~F-003 | P1 | 변경 파일 경로를 `opal/`·`docs/`·`tasks/` 하위로 제한. `~/.opal/` 갱신은 Step 11의 `install-mac.sh` 실행으로만 수행 |
| R-12 | **oppl 헤더·표 헤더 개명 유혹** (H-16) | F-003 | P2 | DEC-9로 금지 명문화. Step 6 작업 내용 ⑧에 [MUST 금지] 명시 + Step 9 P8 diff 검사 |
| R-13 | **oppd `--wbs` 경로에서 EXECUTE 3행 미완 잔존** (H-17) | F-001 | P2 — 운영 마찰 | 표준화 판단 ③에 따라 런타임 `mark --na` 처리. Step 7에서 `:153` 플래그 설명에 처리 지침 1문장 보강 |
| R-14 | **registry 표기 형식 합의 부재** (H-12) | F-004 | P2 | §3.4.2에서 `meta.stages`를 `" → "`로 연결하는 파생 규칙을 확정하고 TS-008로 기계 검증 |
| R-16 | **pilot 밖 구형 지시 잔존** — 잔존 검증이 pilot SKILL.md로 한정돼 `tools.md:84`·`:152`, `task-process.md:49`, `op-task/SKILL.md:223` 4곳을 놓친다. 특히 `tools.md:152`는 **이미 전환된 opp를 구형 경로로 지시하는 실행 예시**라 지금 복사·실행하면 오작동한다 (H-18) | F-008 | **P0** — "10/10 전환"이 pilot 안에서만 참이 됨 | Step 8에서 4곳 지정 문자열 교체 + 3파일 변경이력. Step 10 P4-b 레포 전역 스캔으로 사후 검출. 도구 자신 2파일은 DEC-11로 불가침 처리하고 **변경 0줄을 역방향 검증**(S-18) |
| R-17 | **`tools.md:81` `--skill` enum 결측** — `<opp\|opd\|opds\|opdw\|opwt\|opgc\|oppd\|opsdd>`에 `oppl`·`opdd`가 빠져 있다. `state_tool.py:2350`의 실제 choices 10종과 불일치 | F-008 | P2 — 관측 사항 | **이번 범위 밖**(R-9는 `.md` 파싱 지시에만 한정). Step 8 작업 내용 ⑦에 "건드리지 않는다"로 명시하고 후속 태스크로 이월 보고 |
| R-15 | **변경이력 행 개변** — R-2 잔존 grep을 문자 그대로 만족시키려고 과거 이력 행을 수정 | F-003 | P2 | D-9로 확정 — `## 변경이력` 섹션 이후는 검사 대상 제외. 각 Step 작업 내용에 "기존 이력 행 수정 금지"를 명시 |

---

> ### 완료 시 도달 상태 (경고 아님 — 잔여 결함 0)
>
> 이번 태스크 완료 시점의 프레임워크 상태는 다음과 같다.
>
> - **`init` 불가 pilot: 0개.** oppl·oppd의 `skill_md_parse_error` 하드 실패가 해소된다 (F-007).
> - **레포 전역 구형 지시: 0건.** pilot 밖 4곳(`tools.md` 2 · `task-process.md` 1 · `op-task/SKILL.md` 1)이 정정되어 "10/10 전환"이 **레포 전역에서 참**이 된다 (F-008 / 완료기준 (0)). 도구 자신 2파일은 의도적으로 그대로 둔다 (DEC-11).
> - **deprecated `build_rows_from_skill_md` 경로를 지시하는 pilot: 0건.** 10/10이 `references/pipeline.json`을 가리킨다 (TS-017 / 완료기준 8).
> - **`pipeline.json` 미보유 pilot: 0개.** `spec-validate` 10건 전부 통과 (TS-010).
> - **registry `pipeline` 드리프트·결측: 0건.** 10종이 각자의 `meta.stages`와 정합한다 (TS-008).
>
> **이월 항목은 4건이며 모두 이번 범위 밖으로 사전 합의된 것이다** (TASK.md §이월): 실행 스펙 필드 승격(D-1) / 죽은 `pm_gate` 배열 정리(D-3) / SKILL.md 행 표 삭제·감량(D-5) / ANALYSIS PM Gate 제거(D-6). **제외 pilot으로 인한 잔여 결함은 없다.**

---

> **문서/코드 불일치 보고 (PM 전달용)** — 아래 3건은 **이번 범위 안**이며 코드 기준으로 정정한다.
> 1. `opwt` SKILL.md `:428`: "state-tool은 이 섹션의 `{단계 목록}`을 파싱하여 초기 행을 생성한다" → 실제 파서는 **행 표**를 읽는다 (`state_tool.py:799-820`). Step 4에서 정정.
> 2. `oppl` SKILL.md `:128`: "`state-tool`이 아래 SSOT 표를 읽어 state.json을 초기화한다" → **현재도 거짓**이다(파서가 관문 ①에서 실패). Step 6에서 정정.
> 3. `opsdd` SKILL.md `:342`: "state-tool이 이 파일의 「파이프라인 현황판」 테이블(25행)을 읽어 state.json을 초기화한다" → 전환 후 사실이 아니게 된다. Step 5에서 정정.
>
> 아래 1건은 **불일치가 아니다** — 개념 계층이 다른 두 토큰이다.
> - `opsdd` SKILL.md `:332`의 `EXECUTE-LOOP`(Phase 이름) vs 행 표의 `EXECUTE`(stage 값). D-7c에 따라 **양쪽 모두 그대로 유지**한다 (§2.1.4).

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-08-13 | 초기 작성 — 미전환 6 pilot 전환 계획. F-001~F-005, 11 Step, 리스크 가설 H-1~H-10 |
| v2.0 | 2026-08-13 | **범위 축소 (캡틴 확정 D-7 1차)** — 대상을 opdd·opgc·opwt 3종으로 한정, oppd·oppl·opsdd 제외. F-002 삭제 후 부록 강등, F-006(제외 무변경) 신설, Step 8개, registry 7종 (090) |
| v2.1 | 2026-08-13 | **oppl 재포함 (캡틴 확정 D-7 2차)** — 대상 4종. F-001에 oppl 흡수(부록에서 승격), 그룹 B(표 19행 baseline) 신설, F-007(하드 실패 해소) 신설, Step 9개, registry 8종, `spec-validate` 8건 (090) |
| v2.2 | 2026-08-13 | **oppd 재포함 (캡틴 확정 D-7 3차)** — 대상 5종. F-001에 oppd 흡수, 그룹 C(D-7b 확정 13행 baseline) 신설, oppd 미러 표 신설 설계, Step 10개, registry 9종 + oppd `domain`, `spec-validate` 9건 (090) |
| v2.3 | 2026-08-13 | **opsdd 포함 — 10/10 완전 전환 확정 (캡틴 최종 확정 D-7·D-7c)** — 대상 6종, **제외 pilot 없음**. 부록 완전 제거(제외 대상 소멸). F-001에 opsdd 25행 추가(그룹 A 4종으로 확장, `meta.stages`는 `EXECUTE` 사용). **F-006을 "opsdd `EXECUTE-LOOP` 산문 무변경 보장"으로 재정의**(제외 pilot 무변경 → 토큰 불가침, 8파일 41곳 연쇄 차단). F-004 registry 10종. F-005 `spec-validate` 10건·채택 10/10·잔존 6종·init 20회. Step 11개 연속 재부여(6병렬). 리스크 H-1~H-17 재부여(H-2 `EXECUTE-LOOP` 오기입·H-3 개명 연쇄·H-4 25행 id/key 신설). §9 "완료 시 도달 상태"로 경고 대체 — `init` 불가 0개·deprecated 호출자 0건, 이월 4건은 전부 사전 합의분 (090) |
| v2.4 | 2026-08-13 | **목표-커버 게이트 iteration 1 gap 대응 — 범위 확장 (캡틴 A안 확정, TASK.md D-10·R-9·완료기준 (0))** — ⑤채택·잔존 축 gap(S-10 잔존 검사가 pilot SKILL.md로 한정) 해소. **F-008 신설**(레포 전역 구형 지시 4곳 정정 — `tools.md:84` 시놉시스·`:148`·`:152` 실행 예시, `task-process.md:49`, `op-task/SKILL.md:223`). **H-18 신설**(P0, TEST-SCENARIO와 ID 정합) + R-16·R-17 추가. **DEC-11 신설**(도구 자신 2파일 불가침 — `state_tool.py`·`state-tool/README.md` 변경 0건이 S-18 역방향 검증). §3.5.2에 **P4-b 레포 전역 잔존 스캔** 신설. Step 8(F-008) 신설·Batch 1 병렬 편입(**7병렬**), Step 11개 → **12개** 연속 재부여. 검증 Step에 레포 전역 스캔·역방향 무변경 추가 + TS-018(S-18) 매핑. §6 복잡도 재평가(파일 14 → **17**, P0 6 → **7**). §4.2 공통 금지 3건 → **4건** (090) |
