# PLAN: 파이프라인 스펙 중복정리 — SKILL.md 감량 + PM Gate SSOT 승격

> 작성일: 2026-08-13 | 입력: TASK.md, ANALYSIS.md
> 모드: Multi-Feature (F-001~F-007)

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

090이 pilot 10종의 **행 구성**을 `references/pipeline.json`으로 단일화했다. 이번 태스크는 그 SSOT 위에 남은 잔재를 걷어내고(SKILL.md 미러 표 134행·구형 `--row` 주소 45건·중복 서술) **PM Gate 정의**를 `task_steps[].gate`로 승격한 뒤, `state_tool.py`가 이를 실제로 소비하게 만든다 — 게이트 행 `mark` 시 (a) artifacts 존재 검증 실패면 거부 (b) 통과 시 checklist를 stdout 페이로드로 반환.

핵심 설계 판단은 "**데이터 이관과 집행 배선을 같은 태스크에서 짝짓되, 서로 무해한 순서로 쌓는다**"이다. pipeline.json에 `gate`를 넣어도 현행 `validate_pipeline_spec()`·`build_rows_from_pipeline_json()`은 미지의 필드를 무시하므로(`opal/tools/state-tool/state_tool.py:875-934`, `:937-972` 전문 확인) Phase 2까지는 **동작이 바이트 단위로 불변**이며, Phase 3에서 비로소 집행이 켜진다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | 전후 동등 baseline 확보 | R-13(전제) | P0 | 없음 |
| F-002 | 상위 규칙·오문장 선행 정정 | R-1, R-2, R-3 | P0 | 없음 |
| F-003 | PM Gate 정의 SSOT 이관 (`task_steps[].gate`) | R-9 | P0 | F-001 |
| F-004 | 게이트 집행 배선 (validate + mark 소비 + 세션 주입) | R-10, R-11 | P0 | F-003 |
| F-005 | pilot SKILL.md 감량 (좌표계 전환 + 중복 제거 + 게이트 표 포인터화) | R-4, R-5, R-6, R-7, R-8, R-12 | P0 | F-002, F-003, F-004 |
| F-006 | 전후 동등·회귀 검증 | R-13 | P0 | F-004, F-005 |
| F-007 | 규칙 문서 갱신 + 배포 정합 | R-14 | P1 | F-006 |

### 1.3 기능 의존 그래프 (ASCII)

```
F-001(baseline) ─┐
                 ├─> F-003(gate 데이터) ─> F-004(집행 배선) ─┐
F-002(선행 정정) ─┘                                          ├─> F-005(SKILL.md 감량) ─> F-006(회귀) ─> F-007(문서·배포)
                                                             │
                             (F-003/F-004는 F-005의 정보 원천·AC 근거이므로 반드시 선행)
```

> **순서 역전에 대한 설명**: TASK.md C-4는 논리 Phase를 "정정 → key 전환 → 중복 제거 → 게이트 승격"으로 잡았다. 본 PLAN은 **논리 순서는 보존하되 물리 디스패치 순서를 재배치**한다 — 근거는 §4.3 R-1.

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | `cmd_mark` 게이트 가드 삽입 위치 (`state_tool.py:1438` 직후) | 검증 실패가 `save_state_json()`(`:1507`) **이후**에 발생하면 state.json은 갱신되고 STATE.md는 미갱신 — 부분 상태 변경 | P0 | L1(단위) + L2(파일시스템 실측) | S-후보: artifacts 부재 mark → state.json mtime/내용 무변화 확인 |
| H-2 | `build_rows_from_pipeline_json()` gate 복사 | `state.json` rows[] 신규 키 추가 — `state.schema.json:47` `additionalProperties:false` 문서 계약 위반 + 기존 태스크 state.json(gate 없음) 하위호환 | P1 | L1 + L2(기존 태스크 폴더 로드) | S-후보: gate 없는 구 state.json으로 mark 정상 통과 |
| H-3 | `gate` 미보유 행의 mark 경로 | 기존 284 tests 회귀 — 신규 가드가 조기 return 하지 않으면 전 파이프라인 mark가 영향 | P0 | L1(pytest 전건) | S-후보: `pytest tests/ -q` 284+N passed |
| H-4 | glob 토큰 매칭 (`pathlib.Path.glob`) | `*` 미포함 토큰을 glob로 오분류 / 절대경로·`..` 토큰 시 `ValueError` 또는 태스크 폴더 밖 매칭 | P1 | L1 | S-후보: `actions/ACT-*/DONE.md` 매칭 성공, `/etc/passwd`·`../x` 토큰 거부 |
| H-5 | `--force` 게이트 우회 | 우회 시 의사결정 로그 미기재 → 감사 추적 상실 (`state_tool.py:1521-1534` 선례 대비 누락) | P2 | L1 + L2(STATE.md 렌더 확인) | S-후보: `--force --note` 우회 후 STATE.md 의사결정 로그에 `gate_artifact_force` + missing[] 기재 |
| H-6 | checklist stdout 페이로드 형태 | `todo_mirror_hook._extract_payload`는 **`isinstance(obj.get(key), dict)`만 통과**(`todo_mirror_hook.py:64-82`) — list를 실으면 조용히 무시되어 세션 주입 무발동 | P1 | L1(hook 단위) + L2(subprocess 실호출) | S-후보: `gate_checklist`가 dict로 직렬화되고 hook이 additionalContext를 출력 |
| H-7 | 미러 표 삭제 (R-6) 후 산문 잔존 참조 | 좌표계 소실 — `행 N` 36건·`--row` 45건이 해석 불능 문서로 남음 | P1 | L1(grep) | S-후보: 변경이력 제외 grep 0건 |
| H-8 | opwt 동적 행 key 규약 신설 | `KEY_PATTERN ^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*(_[0-9]+)?$`(`state_tool.py` ERROR_CODES `task_step_key_invalid`) 위반 시 `add-row` 실패 | P1 | L2(add-row 실호출) | S-후보: `execute.batch_pm_gate_1` 등 제안 key 전량 add-row exit 0 |
| H-9 | init 명령 중복 제거 (R-8) | 정본으로 남길 명령이 `--mode` 누락본이면(opgc:116/434, opwt:431, opsdd:339) 모드 기본값 오적용 | P1 | L2(각 pilot init 실호출) | S-후보: 잔존 init 1개가 `--mode` 포함이고 exit 0 |
| H-10 | install 재배포 | `install-mac.sh`가 변경이력 섹션을 strip(`docs/CONVENTIONS.md:243`) → SKILL.md는 소스-배포본 diff 0이 성립하지 않음. pipeline.json은 strip 대상 아님 | P2 | L2(배포본 diff) | S-후보: pipeline.json 10건 diff 0, SKILL.md는 strip 구간 제외 비교 |
| H-11 | state.json rows[] 신규 필드 → dashboard | `dashboard/backend/models.py:136-141` PipelineRow 명시 생성 — 무영향 예상(ANALYSIS §A-5) 이나 미검증 시 회귀 사각 | P2 | L2(dashboard show 경로) | S-후보: `show --format json` 후 dashboard 어댑터 파싱 정상 |
| H-12 | opd TEST-SCENARIO 게이트를 `test_scenario.scenario_gate` 행에 배치 | 게이트 행이 `*.pm_gate` 네이밍이 아닌 유일 사례 — 후속 자동화가 key 접미로 게이트를 식별하면 누락 | P2 | L1 | S-후보: 게이트 식별이 key 접미가 아니라 `row.get("gate")` 유무로만 이뤄지는지 코드 확인 |
| H-13 | **구형 삭제 후 신형 미채택** (좌표계 전환 R-4/R-5) | 잔존 검증(`--row` 0건·`행 N` 0건)이 **명령 예시를 통째로 삭제해도 통과**한다 — 신형(`--task-step`)이 실제로 들어섰는지는 어떤 시나리오도 보지 않음. **070이 정확히 이 구멍으로 "목표 미검증 완료"를 냈다** | P0 | L1 | S-35: pilot별 `--task-step` 전후 델타 대조. 기준선(변경이력 제외) opdd 0 / opwt 0 / opsdd 0 / oppl 0 / opgc 0 / oppd 1 → 증가분이 `--row` 감소분과 일치(합계 +45) |

> **H-13 추가 경위**: TEST-SCENARIO 목표-커버 게이트 iteration 1이 ⑤ 채택/잔존 축을 1/2로 채점하며 지적한 결함이다(`SCENARIO-GATE-1.md`). PLAN 작성 시점에는 도출되지 않았고, 독립 평가자가 잡았다. `scenario-gate.md` §3이 `hypotheses`를 PLAN.md에서 취하도록 규정하므로 계획 SSOT인 이 표에 소급 등재한다(iteration 2 관측 반영).

---

## 2. 기능별 분석

### F-001: 전후 동등 baseline 확보

#### 2.1.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 배치 | `tasks/091-260813-opd-파이프라인-스펙-중복정리/baseline/` | 편집 전 `rows[]` 스냅샷 20건 | 신규 |
| 스킬 | `opal/skills/opal-pilot-*/references/pipeline.json` × 10 | baseline 입력(읽기 전용) | 무변경(이 단계) |

#### 2.1.2 현재 구현
`cmd_init`은 태스크 폴더가 없으면 자동 생성하고(`state_tool.py` cmd_init 도입부), `--rows-from *.json`이면 `build_rows_from_pipeline_json(spec_path, command, mode)`로 rows[]를 만든다(`state_tool.py:937-972`). mode가 `agentic`일 때만 "사용자 확인" 행(CLOSE 제외)이 `na`/`-`/`auto`로 자동 마킹되므로(`:966-971`), 행 구성 분기는 **agentic vs 그 외** 2갈래다. `semi-agentic`과 `interactive`는 이 함수에서 동일 경로다.

본 PLAN 작성 중 실제로 1건(opd/agentic)을 실행해 절차 성립을 확인했다 — `rows_count: 16`, 투영 JSON 정상 산출.

#### 2.1.3 영향 범위
baseline은 읽기 전용 측정이며 프로젝트 파일을 변경하지 않는다. 단, **편집이 시작되면 재현 불가능**하므로 전체 태스크의 최초 Step이어야 한다.

---

### F-002: 상위 규칙·오문장 선행 정정

#### 2.2.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/core/references/harness/state-template.md` | `:94` 미러 표 의무 서술 | 수정 |
| 가이드 | `opal/core/references/harness/qa-standards.md` | `:46` 도메인 치환값 절 참조 | 수정 |
| 스킬 | `opal/skills/opal-pilot-data-design/SKILL.md` | `:241`(아래 표를 파싱), `:242`(줄번호 오인용) | 수정 (F-005 Step에 흡수) |
| 스킬 | `opal/skills/opal-pilot-sdd/SKILL.md` | `:386`, `:399`(위 SSOT 표를 기준으로) | 수정 (F-005 Step에 흡수) |

#### 2.2.2 현재 구현
- `state-template.md:94`: "오케스트레이터 SKILL.md \"STATE.md 도메인 치환값\"에 해당 스킬의 파이프라인 현황판 행 예시가 명시됨" — 미러 표 존재를 하네스 규칙으로 의무화하고 있다.
- `qa-standards.md:46`: "각 오케스트레이터 SKILL.md의 \"STATE.md 도메인 치환값\" 또는 별도 섹션에서 단계별 QA 산출물 파일명을 명시할 수 있다" — 산출물 오버라이드 근거를 같은 절에 걸어 두었다.
- `opdd SKILL.md:241`: "`--rows-from`이 **아래 표를 파싱**하여 행 구성을 자동 추출한다" — 실제 인자는 `pipeline.json`이므로 문장이 명령과 모순이다.
- `opdd SKILL.md:242`: `opal/skills/opal-pilot-dev/SKILL.md:266-289` 인용 — 실제 미러 표는 `:288-305`(ANALYSIS §A-6)이고, 어차피 이번에 삭제되므로 줄번호 인용 자체가 무효화된다.
- `opsdd SKILL.md:386`·`:399`: "위 SSOT 표를 기준으로 state-tool이 생성" — SSOT는 pipeline.json이다.

#### 2.2.3 영향 범위
`state-template.md`/`qa-standards.md`는 pilot 10종 전체가 준수 대상으로 삼는 하네스 규칙이다. **이 2줄을 먼저 고치지 않고 미러 표를 삭제하면, 삭제 결과물이 하네스 기준으로 결함 판정된다**(TASK.md 배경 분석 §5).

---

### F-003: PM Gate 정의 SSOT 이관 (`task_steps[].gate`)

#### 2.3.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/opal-pilot-{dev,dev-short,dev-wireframe,project}/references/pipeline.json` | 최상위 `pm_gate[]` → `task_steps[].gate` 이관 | 수정 |
| 스킬 | `opal/skills/opal-pilot-{write-tech,sdd,data-design}/references/pipeline.json` | SKILL.md 현행 표에서 신규 이관 | 수정 |
| 스킬 | `opal/skills/opal-pilot-{project-dev,project-loop}/references/pipeline.json` | 이관 원본 표 부재 → 신규 저술 | 수정 |
| 스킬 | `opal/skills/opal-pilot-gc/references/pipeline.json` | PM Gate 개념 부재 — **대상 아님** | 무변경 |
| 공통 | `opal/tools/state-tool/schema/pipeline-spec.schema.json` | `task_steps[].gate` 신설 + 최상위 `pm_gate` 제거 | 수정 |
| 공통 | `opal/tools/state-tool/schema/state.schema.json` | `rows[].gate` 신설 | 수정 |

#### 2.3.2 현재 구현 — 실측 (본 PLAN에서 10종 전량 재확인)

**최상위 `pm_gate` 보유 실측**:

| pilot | `pm_gate` 상태 | 항목 수 |
|-------|--------------|--------|
| opd, opds, opdw, opp | **키 존재** | 4 / 2 / 2 / 2 |
| opdd, opgc, oppd, oppl, opsdd, opwt | **키 자체가 부재(ABSENT)** | 0 |

> **[문서/코드 불일치 보고]** ANALYSIS §4-3은 "다른 9종은 최소 `[]`는 존재"라고 서술하나, 실측 결과 **6종은 `pm_gate` 키가 아예 없다**(빈 배열도 아님). R-9 AC (b) "최상위 `pm_gate` 잔존 0건"의 실제 제거 대상은 **4개 파일**이다. (→ 근거: 10종 `json.load` 후 top-level keys 열거)

**게이트 행(= `gate`를 실을 행) 전수 — 27건**:

| pilot | gate 배치 대상 key | 건수 | 원본 |
|-------|-------------------|-----|------|
| opd | `analysis.pm_gate`, `plan.pm_gate`, `test_scenario.scenario_gate`, `test.pm_gate` | 4 | 최상위 `pm_gate[]` + SKILL.md `:312-321` |
| opds | `plan.pm_gate`, `test.pm_gate` | 2 | 동일 (`:280-288`) |
| opdw | `wireframe.pm_gate`, `execute.pm_gate` | 2 | 동일 (`:212-219`) |
| opp | `plan.pm_gate`, `execute.pm_gate` | 2 | 동일 (`:183-191`) |
| opwt | `plan.pm_gate`, `qa.pm_gate` | 2 | SKILL.md `:472-480` (부분) + 신규 저술 |
| opsdd | `spec.pm_gate`, `review.pm_gate`, `design.pm_gate`, `execute.pm_gate`, `verify.pm_gate` | 5 | SKILL.md `:412-421` (3건) + 신규 저술 2건 |
| opdd | `dict.pm_gate`, `model.pm_gate`, `ddl_migration.pm_gate`, `qa.pm_gate` | 4 | SKILL.md `:268-279` (5행 → 4행 병합) |
| oppd | `plan.pm_gate`, `wbs.pm_gate`, `execute.pm_gate` | 3 | **신규 저술** |
| oppl | `review.pm_gate`, `execute.pm_gate`, `verify.pm_gate` | 3 | **신규 저술** |
| opgc | — | 0 | 대상 아님 |
| **합계** | | **27** | |

**stage → key 매핑이 1:1이 아닌 지점 3건** (C-2가 인라인 배치를 택한 이유의 실증):
1. **opd TEST-SCENARIO**: 이 stage에 `pm_gate` 항목명 행이 없다. 게이트 성격의 행은 `test_scenario.scenario_gate`(항목 "목표-커버 게이트")다 → 여기에 배치. (H-12)
2. **opds PLAN**: `plan.pm_gate`와 `plan.scenario_gate`가 **한 stage에 2개** 존재. 표의 PLAN 행은 `plan.pm_gate`에만 배치하고 `plan.scenario_gate`에는 gate를 두지 않는다(원본에 없으므로 누락 아님).
3. **opdd TASK**: SKILL.md 표에 TASK 행이 있으나 `task.pm_gate` 행이 없다(TASK stage는 `task.task_md`/`task.user_confirm` 2행뿐) → §3.3.2 (2)로 처리.

#### 2.3.3 영향 범위
- **하류 무영향(Phase 2 시점)**: `validate_pipeline_spec()`은 `task_steps[]`의 `id/key/stage`만 검사하고 미지 필드를 무시한다(`state_tool.py:875-934` 전문). `build_rows_from_pipeline_json()`도 `ts["stage"]/["item"]/["key"]/.get("conditional")`만 읽는다(`:948-971`). 따라서 **F-003만 수행한 시점의 런타임 동작은 완전 무변화**다 — F-001 baseline과 이 시점의 재측정이 동일해야 한다(중간 검증 지점).
- **상류**: 두 `.schema.json`은 비집행 문서(`state_tool.py`에 `import jsonschema` 없음 — ANALYSIS §4-1). 갱신하지 않아도 동작은 같지만 문서-코드 정합이 깨지므로 **동시 갱신 대상**이다.

---

### F-004: 게이트 집행 배선

#### 2.4.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `opal/tools/state-tool/state_tool.py` | `validate_pipeline_spec` 확장 / `check_gate_artifacts` 신설 / `build_gate_payload` 신설 / `build_rows_from_*` gate 영속 / `ERROR_CODES` | 수정 |
| BE | `opal/tools/state-tool/todo_mirror_hook.py` | checklist 세션 주입 릴레이 | 수정 |
| BE | `opal/tools/state-tool/tests/test_state_tool.py` | RED-first 신규 클래스 | 수정 |
| BE | `opal/tools/state-tool/tests/test_todo_mirror_hook.py` | hook 확장 테스트 | 수정 |

#### 2.4.2 현재 구현
`cmd_mark`(`state_tool.py:1383-1553`)는 **검증 전용 구간(순서 1~10, `:1386-1438`)** 과 **mutation 구간(순서 11~24, `:1440-1553`)** 이 명확히 갈린 가드 체인이다(ANALYSIS §A-1). 기존 가드 4종(워커 권한 `:1407-1418` / stage 전환 `:1420-1424` / CLOSE 진입 `:1426-1428` / 명확화 `:1430-1432`)은 모두 `err()`로 즉시 종료하며 이 중 2종은 `force` 파라미터로 조건부 스킵된다(`:640-641`, `:697-698`).

`ok()` 응답 확장은 `_ok_kwargs`(`:1548-1552`)에서 이뤄지며, `todo_mirror`(076)·`history_link`(088) 2건이 이미 조건부 추가 패턴을 확립했다.

`todo_mirror_hook._extract_payload(stdout, key)`(`:64-82`)는 **`isinstance(obj.get(key), dict)` 조건을 통과한 값만** 반환한다 — 리스트 페이로드는 조용히 버려진다. (H-6의 근거)

#### 2.4.3 영향 범위
- `state.json`에 `gate`가 실리면 `dashboard/backend/adapters/state_adapter.py`가 그대로 통과시키지만 `models.py:136-141` `PipelineRow`는 4필드를 명시 생성하므로 무영향(ANALYSIS §A-5). 회귀 확인 대상(H-11).
- `--rows-spec` 인라인 경로(`build_rows_from_spec`)는 현재 `gate`를 무시한다. `BaseTestCase._init()`이 이 경로를 쓰므로(ANALYSIS §A-4) 테스트 작성 편의와 `--rows-spec` 존치 제약(TASK.md 제약 e) 정합을 위해 **동일 필드 지원을 포함**한다.

---

### F-005: pilot SKILL.md 감량

#### 2.5.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/opal-pilot-*/SKILL.md` × 10 | 미러 표 / `--row` / `행 N` / 치환값 / init 중복 / PM Gate 표 | 수정 |

#### 2.5.2 현재 구현 — 실측 재검증 (본 PLAN에서 전량 재측정)

**`--row` 출현 (occurrence 기준, `grep -o`)**:

| pilot | 비-변경이력 | 변경이력 내 | 합계 |
|-------|-----------|-----------|------|
| opdd | 14 | 0 | 14 |
| opwt | 11 | 0 | 11 |
| opsdd | **9** | **1** | 10 |
| oppd | 5 | 0 | 5 |
| oppl | 4 | 0 | 4 |
| opgc | 2 | 0 | 2 |
| opd·opds·opdw·opp | 0 | 0 | 0 |
| **합계** | **45** | **1** | **46** |

> **[R-4 수치 확정]** 전환 대상은 **45건**이다. TASK.md의 46은 `opal-pilot-sdd/SKILL.md`의 변경이력 리터럴 1건(`## 변경이력` 헤딩 `:520` 이후)을 포함한 값이며, 변경이력은 불변 대상이다. ANALYSIS §A-6의 정정이 옳다. (→ 재측정: `## 변경이력` 줄번호로 head/tail 분할 후 `grep -o` 카운트)

**산문 `행 [0-9]+` 출현**: 비-변경이력 **36건** / 변경이력 **13건** / 합계 49건. pilot별 비-변경이력 분포 — opds 9, opp 8, opdd 7, opd 6, opdw 3, opsdd 2, opwt 1, opgc·oppd·oppl 0.

**init 완전 명령 중복 (state-tool 한정)**: opgc 3(`:116, :434, :482`) / opwt 3(`:193, :431, :441`) / opdd 2(`:75, :241`) / opdw 2(`:190, :245`) / oppl 2(`:126, :442` — `:211`은 backlog-tool이므로 제외) / opsdd 2(`:339, :447`) / opd·opds·opp·oppd 각 1(중복 없음). TASK.md R-8 수치와 일치.

**미러 표 / 치환값 절 / PM Gate 절 줄 범위**: ANALYSIS §A-6 표를 그대로 채택(재검증 불요 — 미러 표 134행 수치 일치 확인됨).

#### 2.5.3 영향 범위
10개 파일 모두가 **여러 요구사항의 교차 대상**이다(예: opdd 1파일에 R-1·R-3·R-4·R-5·R-6·R-7·R-8·R-12가 동시 적용). 파일 단위 원자성이 요구사항 단위 분해보다 우선한다 — §4.3 R-2.

---

### F-006 / F-007: 회귀·문서·배포

#### 2.6.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | `docs/CONVENTIONS.md` | §State 관리에 gate SSOT 규칙 추가 | 수정 |
| 배치 | `scripts/install-mac.sh` (실행만) | 배포 재적용 | 무변경 |
| 배치 | `~/.opal/**` | 배포본 | 재생성 |

#### 2.6.2 현재 구현
`docs/CONVENTIONS.md:228`은 행 **주소** 규칙만 규정하고 게이트 정의의 SSOT는 언급하지 않는다. R-9로 새 규칙이 도입되므로 갱신 대상이다(plan-guide.md "새 패턴/규칙 도입 → CONVENTIONS.md").

#### 2.6.3 영향 범위
`install-mac.sh`가 변경이력 섹션을 strip 하므로(`docs/CONVENTIONS.md:243`) SKILL.md의 소스-배포본 완전 diff는 성립하지 않는다. R-14 AC의 "diff 0"은 **pipeline.json 10건에만** 적용된다(H-10).

---

## 3. 기능별 설계

### F-001: 전후 동등 baseline 확보

#### 3.1.1 파일 변경 계획

**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `tasks/091-260813-opd-파이프라인-스펙-중복정리/baseline/{skill}-{mode}.json` × 20 | 배치 | 편집 전 rows[] 투영 스냅샷 | TASK.md 제약 (a) |

#### 3.1.2 설계 — baseline 캡처 절차

**[MUST] 이 절차는 어떤 편집보다 먼저, 정확히 1회 실행한다. 편집이 시작되면 재현이 불가능하다.** (→ D-1 §8 전후 동등 검증 선례)

```bash
# 실행 위치: 프로젝트 루트
BL="tasks/091-260813-opd-파이프라인-스펙-중복정리/baseline"
mkdir -p "$BL"
for pair in \
  "opd:opal-pilot-dev"            "opds:opal-pilot-dev-short" \
  "opdw:opal-pilot-dev-wireframe" "opp:opal-pilot-project" \
  "opwt:opal-pilot-write-tech"    "opgc:opal-pilot-gc" \
  "oppd:opal-pilot-project-dev"   "opsdd:opal-pilot-sdd" \
  "oppl:opal-pilot-project-loop"  "opdd:opal-pilot-data-design"; do
  s="${pair%%:*}"; d="${pair##*:}"
  for m in interactive agentic; do
    t="$(mktemp -d)/$s-$m"
    bash opal/tools/state-tool/run.sh init "$t" --skill "$s" --mode "$m" \
      --rows-from "opal/skills/$d/references/pipeline.json" > /dev/null
    python3 - "$t/state.json" "$BL/$s-$m.json" <<'PY'
import json, sys
rows = json.load(open(sys.argv[1]))["rows"]
KEYS = ("row_id", "stage", "item", "key", "status", "status_label", "owner")
json.dump([{k: r.get(k) for k in KEYS} for r in rows],
          open(sys.argv[2], "w"), ensure_ascii=False, indent=2)
PY
  done
done
```

**설계 결정 3건**:

1. **mode는 `interactive`·`agentic` 2종** — `build_rows_from_pipeline_json()`의 유일한 mode 분기는 `mode == "agentic"`이고(`state_tool.py:966`), `semi-agentic`은 `interactive`와 동일 경로다. 2 mode로 전 분기를 커버한다. (TASK.md 제약 (a) "10 pilot × 2 mode"와 정합)
2. **투영 비교축은 7필드** — `(row_id, stage, item, key, status, status_label, owner)`. F-004 이후 rows[]에 `gate`가 추가되므로 **원시 JSON 전체 비교는 반드시 실패한다**. TASK.md 제약 (a)가 규정한 동등성은 "행 구성 불변"이므로 이 투영이 정확한 비교 축이다. `timestamp`·`note`는 실행 시각/모드 메모로 변동하므로 제외한다.
3. **저장 위치는 태스크 폴더 내 `baseline/`** — 임시 디렉토리는 세션 종료 시 소실되고, 검증은 Phase 5(수 Step 뒤)에 수행되므로 영속 필요.

#### 3.1.3 환경 변경
해당 없음 (Python3 표준 라이브러리 + bash만 사용).

#### 3.1.4 배치/마이그레이션
해당 없음.

#### 3.1.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-13 AC(a) 전제 | 산출물 검사 | `baseline/` 아래 20개 JSON 생성, 각 파일의 배열 길이가 해당 pipeline.json `task_steps` 길이와 동일 |

---

### F-002: 상위 규칙·오문장 선행 정정

#### 3.2.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/harness/state-template.md` | 가이드 | `:94` 미러 표 의무 → pipeline.json 원천 지시로 교체 | (→ D-6) |
| 2 | `opal/core/references/harness/qa-standards.md` | 가이드 | `:46` 산출물 오버라이드 근거를 `pipeline.json` `task_steps[].gate.artifacts`로 이전 | (→ D-7) |
| 3 | `opal/skills/opal-pilot-data-design/SKILL.md` | 스킬 | `:241` 오문장, `:242` 줄번호 오인용 — **F-005 Step 12에 흡수** | ANALYSIS §A-6 |
| 4 | `opal/skills/opal-pilot-sdd/SKILL.md` | 스킬 | `:386`·`:399` 오문장 — **F-005 Step 12에 흡수** | ANALYSIS §A-6 |

#### 3.2.2 설계 — 교체 문안

`state-template.md:94` (교체):
```
- 파이프라인 행 구성의 SSOT는 각 pilot의 `references/pipeline.json` `task_steps[]`이다 — 오케스트레이터 SKILL.md에 행 예시를 중복 게재하지 않는다 (091).
```

`qa-standards.md:46` (교체):
```
**스킬별 산출물 오버라이드**: 각 pilot `references/pipeline.json`의 `task_steps[].gate.artifacts`가 단계별 게이트 산출물의 SSOT다 — `state-tool mark`가 이를 존재 검증하고 `gate.checklist`를 stdout으로 반환한다 (091).
```

- **[MUST]** `docs/CONVENTIONS.md` §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 \"## 변경이력\" 표에 행을 추가한다. 일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함" — 두 하네스 참조 문서 모두 변경이력 행 추가 대상이다 (`docs/CONVENTIONS.md:241-242`).
- `opdd:242`의 줄번호 인용은 **삭제**한다(교체 아님) — 인용 대상인 opd 미러 표가 이번에 사라지므로 어떤 줄번호도 유효하지 않다. citation-rules §2.2 근거.

#### 3.2.3 환경 변경 / 3.2.4 배치
해당 없음.

#### 3.2.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-002 | R-2 AC | 산출물 검사 | 두 파일에서 `행 예시가 명시` grep 0건, 각각 `references/pipeline.json` 문자열 ≥1건 |
| TS-003 | R-1 AC | 산출물 검사 | 레포 전역 `표를 파싱`·`SSOT 표를 기준` grep 0건 |
| TS-004 | R-3 AC | 산출물 검사 | pilot SKILL.md 내 타 SKILL.md 줄번호 인용(`SKILL.md:[0-9]`) 0건 |

---

### F-003: PM Gate 정의 SSOT 이관

#### 3.3.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/state-tool/schema/pipeline-spec.schema.json` | 공통 | `task_steps[].properties.gate` 신설, 최상위 `pm_gate` 정의 제거 | `pipeline-spec.schema.json:20-47` |
| 2 | `opal/tools/state-tool/schema/state.schema.json` | 공통 | `rows[].properties.gate` 신설 | `state.schema.json:44-113` |
| 3~6 | `opal-pilot-{dev,dev-short,dev-wireframe,project}/references/pipeline.json` | 스킬 | `pm_gate[]` → 해당 행 `gate` 이관 후 최상위 키 삭제 | 실측 §2.3.2 |
| 7~9 | `opal-pilot-{write-tech,sdd,data-design}/references/pipeline.json` | 스킬 | SKILL.md 표 → `gate` 신규 이관 (+부족분 저술) | SKILL.md `:472-480`/`:412-421`/`:268-279` |
| 10~11 | `opal-pilot-{project-dev,project-loop}/references/pipeline.json` | 스킬 | `gate` 신규 저술 | ANALYSIS §A-6 (표 부재) |

#### 3.3.2 데이터 모델 설계

**(1) `gate` 객체 스키마** — `task_steps[]`와 `rows[]`에 동형으로 정의:

```jsonc
"gate": {
  "type": "object",
  "required": ["artifacts", "checklist"],
  "additionalProperties": false,
  "properties": {
    "artifacts": { "type": "array", "items": { "type": "string" } },
    "checklist": { "type": "array", "items": { "type": "string" }, "minItems": 1 }
  },
  "description": "PM Gate 정의 (091). artifacts=태스크 폴더 기준 상대 경로/글롭 — mark가 존재 검증하여 미충족 시 거부. checklist=PM 판단 항목 — mark stdout으로 주입."
}
```

- `artifacts`는 **빈 배열 허용**(`minItems` 없음) — opdw/opp EXECUTE 게이트처럼 결정론 검증 대상이 하나도 없는 게이트가 정당하게 존재한다.
- `checklist`는 **`minItems: 1`** — 체크리스트 없는 게이트는 SKILL.md 표를 지운 뒤 정보량이 0이 되므로 스펙 오류다. R-10 AC의 "빈 배열" 위반 검출은 이 필드를 가리킨다.
- **[MUST]** `state.schema.json:47`의 `rows[]` `additionalProperties: false` 때문에 `rows[].gate` 등록은 **스킵 불가능한 선행 조건**이다 — `key`(`:102-106`)/`conditional`(`:107-110`) 바로 옆에 형제 속성으로 추가한다 (ANALYSIS §5 R-3).
- 두 `.schema.json`은 **비집행 문서**다(`state_tool.py`에 `import jsonschema` 부재 — ANALYSIS §4-1). 갱신은 문서-코드 정합 유지 목적이며, **집행 본체는 §3.4.2의 `validate_pipeline_spec()` 확장**이다. R-10의 작업량은 Python 함수 쪽에 있다.

**(2) artifacts 토큰 적격성 규칙 — [미결-1 결정]**

> **채택: ②안 변형 (glob 지원 + 비-결정론 토큰의 checklist 전치)**

`artifacts`에 넣을 수 있는 토큰은 아래 2종으로 한정한다:

| 적격 | 형태 | 판정 방법 |
|------|------|----------|
| 정적 상대 경로 | `TASK.md`, `PLAN.md`, `wireframe.md`, `SPEC.md`, `SPEC-PLAN.md` | `(Path(task_path) / token).exists()` |
| 태스크 폴더 기준 글롭 | `actions/ACT-*/DONE.md` | `any(Path(task_path).glob(token))` |

부적격 토큰은 **삭제하지 않고 `checklist`로 전치**한다(원문 보존 — R-9 AC (c) "항목 누락 0"의 충족 방식):

| 토큰 | 부적격 사유 | 전치 후 checklist 문안 |
|------|-----------|---------------------|
| `changed_files` | 파일명이 아닌 논리 개념. state-tool은 git/파일시스템 diff에 접근하지 않는다(`state_tool.py:17-25` import 목록에 git·subprocess-git 없음) → 자체 산출 불가 | `EXECUTE 변경 파일 목록(changed_files) 확인` |
| `GC-CONVENTION-*.md` | **조건부 산출물** — "changed_files 컨벤션 적용 대상 ≥1건 시 발동"(`opal-pilot-dev/SKILL.md:201`, `opal-pilot-dev-short/SKILL.md:144`, `opal-pilot-dev-wireframe/SKILL.md:122`, `opal-pilot-project/SKILL.md:96`). 파일 부재가 위반인지 정상인지 도구가 구분 불가 | `컨벤션 자동 진단 PASS (GC-CONVENTION-*.md Critical/High 0건 — 컨벤션 적용 대상 ≥1건 시 발동)` |
| `{설계}/사전/` 등 opdd 경로 | 태스크 폴더가 아닌 **프로젝트 가변 경로**(`{설계}` 플레이스홀더) | 원문 그대로 checklist 항목화 |

**[MUST] 영구 차단 배제 논증 — opdw EXECUTE 게이트**
1. **구조적 배제**: opdw `execute.pm_gate`의 artifacts 2토큰(`changed_files`, `GC-CONVENTION-*.md`)이 **전량 checklist로 전치**되어 `artifacts: []`가 된다. `check_gate_artifacts()`는 빈 배열이면 즉시 return 하므로(§3.4.2) mark 동작이 현행과 **바이트 동일**하다 → 차단 자체가 발생하지 않는다.
2. **일반 배제**: 조건부·비-경로 토큰은 규칙상 artifacts에 들어갈 수 없다(위 적격 표) → 미래에도 같은 실패 모드가 재발하지 않는다.
3. **최종 안전망**: 그럼에도 정적 산출물이 예외적으로 부재한 경우 `--force --note`로 우회 가능하다(미결-4). 우회는 의사결정 로그에 강제 기록된다.

**탈락 사유**:
- **①안(타입 분리 구조)** — `artifacts`를 `{path:[], glob:[], external:[]}`로 재정의. 표현력은 최고이나 (i) 10개 pipeline.json 전면 재구조 (ii) `validate_pipeline_spec()` 중첩 검증 (iii) 090이 확립한 "행 구성 단순화" 방향과 정반대. **비용 대비 이득 없음** — 실측 결과 타입 분리가 필요한 토큰은 `changed_files` 1종뿐이고, 그것은 애초에 도구가 판정 불가한 항목이라 타입을 나눠도 검증할 수 없다.
- **③안(비-경로 토큰 비차단 통과)** — glob 토큰까지 비차단이 되면 C-3의 "결정론 판정 가능한 지점만 차단"에서 **차단 대상이 사실상 소멸**한다(opsdd `actions/ACT-*/DONE.md`가 유일한 라이브 글롭 소비처인데 이것이 비차단이 됨). 또한 "알 수 없는 토큰은 통과"는 오타를 조용히 삼켜 R-10의 오타 검출 취지와 충돌한다.

**(3) 27건 gate 배치 명세**

opd (`opal/skills/opal-pilot-dev/references/pipeline.json`):
| key | artifacts | checklist |
|-----|-----------|-----------|
| `analysis.pm_gate` | `["ANALYSIS.md"]` | `["-"]` (원본 표 `:316` 그대로) |
| `plan.pm_gate` | `["TASK.md","PLAN.md"]` | `["TASK.md 요구사항","PLAN.md §4.2","PLAN.md §5","PLAN.md §리스크 가설 표"]` |
| `test_scenario.scenario_gate` | `["TEST-SCENARIO.md"]` | 7항목 — ⑥은 **`"L3 [SUPERVISOR] 마커 + PM 요청 양식"`** (SKILL.md `:318` 상세본 채택, 드리프트 정정) |
| `test.pm_gate` | `["TEST-SCENARIO.md"]` | `["시나리오 결과/코드품질/보안/회귀","컨벤션 자동 진단 PASS (GC-CONVENTION-*.md …)"]` |

opds: `plan.pm_gate` = `["TASK.md","PLAN.md","TEST-SCENARIO.md"]` + 4항목 / `test.pm_gate` = `["TEST-SCENARIO.md"]` + 2항목(GC 전치).
opdw: `wireframe.pm_gate` = `["TASK.md","wireframe.md"]` + 3항목 — 3번째는 **`"op-dev-qa/SKILL.md 와이어프레임 검증 기준 참조"`**(SKILL.md `:217` 상세본 채택, 드리프트 정정) / `execute.pm_gate` = `[]` + 5항목(changed_files·GC 전치 포함).
opp: `plan.pm_gate` = `["TASK.md","PLAN.md"]` + 3항목 / `execute.pm_gate` = `[]` + 2항목.
opwt: `plan.pm_gate` = `["PLAN.md"]` + 표 `:476` 체크리스트. **TASK.md/QA-PLAN.md는 실재 확인 후에만 artifacts 승격** — 미확인 시 checklist 유지(기본값) / `qa.pm_gate` = `[]` + 신규 저술(표의 EXECUTE 행은 체크리스트 `-`로 정보량 0이므로 QA 단계 최종 판정 기준을 SKILL.md `:355-376` "PM 최종 판정" 절에서 추출).
opsdd: `spec.pm_gate` = `["TASK.md","SPEC.md"]` / `design.pm_gate` = `["SPEC-PLAN.md"]` / `execute.pm_gate` = `["actions/ACT-*/DONE.md"]` (**글롭 라이브 소비처**) / `review.pm_gate`·`verify.pm_gate` = 신규 저술(각각 `review.*` 4행·`verify.*` 2행의 완료 기준에서 추출).
opdd: 4건 모두 `artifacts: []` — 표의 산출물이 전부 `{설계}/…` 프로젝트 가변 경로라 부적격. 표 5행 중 **TASK 행**은 대응 gate 행이 없으므로 그 체크리스트 3항목을 `dict.pm_gate.checklist` **선두에 병합**한다(`"TASK 전제: {설계} 루트 확정 / 인풋 컨텍스트 수집 완료 / DBMS 확정"`) — 누락 0 원칙 충족.
oppd (신규 저술): `plan.pm_gate` = `["TASK.md","PRD.md","TRD.md"]`(실재 파일명은 EXECUTE에서 SKILL.md 산출물 절로 확정) / `wbs.pm_gate` = `["WBS.md"]` / `execute.pm_gate` = `[]`.
oppl (신규 저술): `review.pm_gate` = `["CONTRACT.md"]` 계열 / `execute.pm_gate` = `[]` / `verify.pm_gate` = `[]`. 체크리스트는 각 stage의 선행 `작업` 행 완료 기준에서 추출.

> **[MUST] 신규 저술 4종(oppd 3 + oppl 3 중 artifacts 확정분)의 파일명은 추측하지 않는다.** EXECUTE Step에서 해당 SKILL.md의 산출물 절을 실측해 존재가 보장되는 파일만 artifacts로 올리고, 확신이 없으면 checklist에 남긴다 — 부적격 승격은 H-4/영구 차단 리스크를 되살린다.

**(4) `gate` 저장 위치 — [미결-3 결정]**

> **채택: (a) init 시점에 row로 복사해 `state.json`에 영속**

근거 3건:
1. **선례 직접 확장** — `key`·`conditional`이 이미 "정적 정의값의 init-time 복사" 패턴이다(`state_tool.py:950-962`). `gate`는 행에 귀속된 정적 정의값이므로 같은 부류다. 반대편 선례(`todo_mirror`/`history_link`의 stdout 전용)는 "매 호출 파생값"에 적용되는 것으로 성격이 다르다.
2. **(b)안은 현재 코드에서 불가능** — `cmd_init`은 `args.rows_from`을 state.json에 어떤 형태로도 저장하지 않고(ANALYSIS §A-2 전수 확인), `skill` enum → pilot 디렉토리 매핑 상수도 존재하지 않는다. 재로드하려면 `mark`에 신규 `--spec-path`를 도입해 **45+건의 mark 호출 예시 전부에 인자를 전파**하거나 매핑 테이블을 신설해야 한다 — R-4로 이미 45건을 손대는 태스크에서 같은 호출부에 인자를 하나 더 얹는 것은 회귀 표면을 배증시킨다.
3. **드리프트 트레이드오프 수용** — (a)는 init 이후 pipeline.json이 바뀌어도 기존 state.json이 구 gate를 들고 있다(정적 스냅샷). 이는 `key`/`conditional`이 이미 감내 중인 동일한 성질이며, 태스크 수명(수 시간~수 일) 내 pipeline.json 변경은 정상 흐름이 아니다. **소급 변경 금지 제약**(TASK.md 제약 d)과도 오히려 정합적이다.

`state.schema.json:47` `additionalProperties: false` 처리: `rows[].properties`에 `gate`를 정식 등록한다(위 (1) 스키마). **미등록 상태로 필드를 실으면 문서 계약 위반**이므로 스키마 갱신은 Step 3에서 코드보다 먼저 수행한다.

부수 효과(의도된 것): `add-row`로 생성되는 **동적 행에는 `gate`가 실리지 않는다**(`cmd_add_row`의 `new_row` 딕셔너리에 gate 없음) → opwt 배치 게이트·oppd 액션 게이트·opsdd ACT 게이트는 게이트 소비 대상 밖이며 mark 동작이 현행과 동일하다. 이것이 미결-2 (b)안의 안전성을 뒷받침한다.

#### 3.3.3 환경 변경 / 3.3.4 배치
해당 없음.

#### 3.3.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-005 | R-9 AC(a) | 산출물 검사 | opgc 제외 9종에서 게이트 행 27건 전부 `gate` 보유, `gate.checklist` 길이 ≥1 |
| TS-006 | R-9 AC(b) | 산출물 검사 | 10종 pipeline.json 최상위 `pm_gate` 키 0건 (제거 대상 실측 4건) |
| TS-007 | R-9 AC(c) | 산출물 검사 | opd ⑥에 `PM 요청 양식`, opdw에 `op-dev-qa/SKILL.md … 참조` 문자열 존재. `changed_files`·`GC-CONVENTION-*.md` 원문이 checklist에 전치 보존 |
| TS-008 | R-9 / F-003 무영향 | 회귀 테스트 | F-003 완료 시점에 baseline 재측정 → 20/20 diff 0 (gate 추가가 rows[]를 바꾸지 않음) |

---

### F-004: 게이트 집행 배선

#### 3.4.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/state-tool/state_tool.py` | BE | `ERROR_CODES` 5종 추가 / `validate_pipeline_spec()` 검사 ⑧~⑪ / `check_gate_artifacts()`·`build_gate_payload()` 신설 / `build_rows_from_pipeline_json()`·`build_rows_from_spec()` gate 전파 / `cmd_mark` 가드·페이로드 배선 | `state_tool.py:81-127`, `:875-934`, `:937-972`, `:1383-1553` |
| 2 | `opal/tools/state-tool/todo_mirror_hook.py` | BE | `extract_gate_checklist()` 신설, `build_additional_context()` 3-페이로드 확장 | `todo_mirror_hook.py:64-124` |
| 3 | `opal/tools/state-tool/tests/test_state_tool.py` | BE | `TestTaskStepGate` 신설 + `TestPipelineSpecValidate` 케이스 추가 + `TestErrorCodesCompleteness` 갱신 | ANALYSIS §A-4 |
| 4 | `opal/tools/state-tool/tests/test_todo_mirror_hook.py` | BE | 게이트 페이로드 릴레이 케이스 추가 | ANALYSIS §A-5 |

#### 3.4.2 API 설계 (함수 시그니처 + 삽입 지점)

**(1) `validate_pipeline_spec(spec)` 확장** — 순수 Python 검증 본체 (`state_tool.py:875-934`)

기존 `task_steps` 순회 루프 안, `id` 순차 검사 뒤에 `gate` 검사 4건을 추가한다:

```python
gate = ts.get("gate")
if gate is not None:
    if not isinstance(gate, dict):
        violations.append({"code": "spec_gate_type_invalid", "id": ts_id, "key": ts_key,
                           "detail": f"gate must be object, got {type(gate).__name__}"})
    else:
        for f in ("artifacts", "checklist"):
            if f not in gate:
                violations.append({"code": "spec_gate_missing_field", "id": ts_id, "key": ts_key,
                                   "detail": f"gate missing field: {f}"})
            elif not isinstance(gate[f], list) or any(not isinstance(x, str) for x in gate[f]):
                violations.append({"code": "spec_gate_field_type_invalid", "id": ts_id, "key": ts_key,
                                   "detail": f"gate.{f} must be array of string"})
        if isinstance(gate.get("checklist"), list) and len(gate["checklist"]) == 0:
            violations.append({"code": "spec_gate_checklist_empty", "id": ts_id, "key": ts_key,
                               "detail": "gate.checklist must not be empty"})
```

- **[MUST]** `artifacts`의 빈 배열은 **위반이 아니다** — opdw/opp EXECUTE 게이트가 정당하게 비어 있다(§3.3.2 (2)). R-10 AC의 "빈 배열" 검출 대상은 `checklist` 한정이며, AC 해석을 이렇게 확정한다.
- 반환 포맷은 기존 `{code, id?, key?, detail}` 계약을 유지한다(`cmd_validate` violations 포맷 차용).

**(2) `check_gate_artifacts(task_path, row, command, force=False)` 신설** — 신규 가드

```python
def check_gate_artifacts(task_path, row, command, force=False):
    """091 R-11: gate.artifacts 존재 검증. 미충족 시 gate_artifact_missing으로 mark 거부.
    gate 미보유 행은 즉시 return — 기존 동작 불변(H-3)."""
    gate = row.get("gate")
    if not isinstance(gate, dict):
        return None
    tokens = gate.get("artifacts") or []
    if not tokens:
        return None
    base = pathlib.Path(task_path)
    missing = []
    for t in tokens:
        if not _is_safe_artifact_token(t):        # 절대경로·상위경로 토큰 거부 (H-4)
            missing.append(t); continue
        if any(c in t for c in "*?["):
            if not any(base.glob(t)):
                missing.append(t)
        elif not (base / t).exists():
            missing.append(t)
    if not missing:
        return None
    if force:
        return missing                            # 우회 — 호출자가 의사결정 로그에 기재
    err(command, "gate_artifact_missing",
        row_id=row["row_id"], key=row.get("key"), missing=missing)
```

보조 함수 `_is_safe_artifact_token(t)`: `pathlib.PurePosixPath(t).is_absolute()` 이거나 `".."`가 파트에 포함되면 False. 태스크 폴더 밖 매칭을 차단한다(H-4).

**삽입 지점**: `cmd_mark`의 `semi_agentic_pre_execute_auto_pass_denied` 검사 직후, `now_str = get_kst_datetime(command)` **직전**(`state_tool.py:1438`↔`:1440` 사이).
- 근거: 이 지점까지가 "검증 실패 시 `err()` 즉시 종료, 성공 시 상태 무변경" 구간이다. 여기 삽입하면 게이트 미충족 시 `save_state_json()`(`:1507`)이 호출되지 않아 **부분 상태 변경이 원천 배제**된다(H-1). 017 다중 Step 로직(`:1442-1462`)이 `row["step"]`을 오염시키기 전이기도 하다.

**(3) `--force` 정책 — [미결-4 결정]**

> **채택: `--force`는 게이트 검증을 우회한다. 단, 우회 사실이 의사결정 로그에 강제 기록된다.**

근거:
1. **UX 일관성** — 기존 가드 2종(stage transition `:640-641`, close gate `:697-698`)이 `force` 파라미터로 조건부 스킵된다. 신규 가드만 예외 없이 절대 차단하면 "`--force`는 가드를 넘긴다"는 사용자 모델이 깨진다(ANALYSIS §5 R-2).
2. **"Enforce, don't just advise"와 충돌하지 않는다** — 헌법이 요구하는 것은 "규칙이 도구로 집행될 것"이지 "탈출구가 없을 것"이 아니다. `--force`는 이미 `--note` 필수(`state_tool.py:1398-1399`)로 **인간이 사유를 작성해야만** 동작하고, §2.17 의사결정 로그가 STATE.md에 남는다. 즉 이탈이 무료가 아니라 **기록 비용이 부과**된다 — 이것이 산문 조언과 결정적으로 다른 지점이다.
3. **데드락 방지** — 조건부/외부 산출물이 정당하게 부재한 상황에서 절대 차단은 파이프라인을 정지시킨다. §3.3.2 (2)의 구조적 배제가 1차 방어이고, `--force`가 2차 안전망이다.

**강화 조건 (신규)** — `cmd_mark`의 decision 로그 구성부(`:1521-1534`, `worker_scope_force` 선례)에 분기 1건 추가:
```python
if _gate_forced_missing:
    decision = (f"gate_artifact_force at row {row['row_id']}, key={row.get('key')}, "
                f"missing={_gate_forced_missing}")
    reason_text = args.note
```
→ H-5 대응. `--force` 우회는 STATE.md 의사결정 로그에 missing 목록까지 남는다.

**(4) `build_gate_payload(row)` 신설 + `cmd_mark` 응답 배선**

```python
def build_gate_payload(row):
    """091 R-11(b): 게이트 통과 시 stdout으로 반환할 checklist 페이로드.
    dict로 감싼다 — todo_mirror_hook._extract_payload가 dict만 통과시킨다(H-6)."""
    gate = row.get("gate")
    if not isinstance(gate, dict):
        return None
    return {
        "key":       row.get("key"),
        "stage":     row["stage"],
        "item":      row["item"],
        "artifacts": gate.get("artifacts") or [],
        "checklist": gate.get("checklist") or [],
        "reminder":  "[PM Gate 점검] 아래 checklist 전 항목을 확인한 뒤 다음 단계로 진행하라. "
                     "SSOT는 해당 pilot references/pipeline.json task_steps[].gate 이다.",
    }
```

`_ok_kwargs`(`:1548-1552`)에 조건부 추가 — `todo_mirror`/`history_link`와 동일 층:
```python
_gate_payload = build_gate_payload(row)
if _gate_payload is not None:
    _ok_kwargs["gate_checklist"] = _gate_payload
```

- **[MUST]** 페이로드는 **반드시 dict**여야 한다. `todo_mirror_hook.py:78`의 `isinstance(obj.get(key), dict)` 조건 때문에 list를 실으면 hook이 조용히 무시하고 세션 주입이 무발동한다(H-6).

**(5) rows 빌더 gate 전파**

`build_rows_from_pipeline_json()`(`:948-971`) — `conditional` 복사 바로 뒤:
```python
if ts.get("gate"):
    row["gate"] = ts["gate"]
```
`build_rows_from_spec()`(`--rows-spec` 인라인 경로) — 동일 1줄. `--rows-spec` 존치 제약(TASK.md 제약 e)과 `BaseTestCase._init()`이 이 경로를 쓰는 사실(ANALYSIS §A-4) 때문에 병행 지원한다.

**(6) `ERROR_CODES` 신규 5종** (`state_tool.py:81-127`)

| code | 메시지 템플릿 |
|------|-------------|
| `gate_artifact_missing` | `PM Gate 산출물 미충족 — 행 {row_id}({key}) 게이트 아티팩트 부재: {missing}` |
| `spec_gate_type_invalid` | `task_steps[].gate가 object가 아님: {detail}` |
| `spec_gate_missing_field` | `task_steps[].gate 필수 필드 누락: {detail}` |
| `spec_gate_field_type_invalid` | `task_steps[].gate 필드 타입 오류(문자열 배열 필요): {detail}` |
| `spec_gate_checklist_empty` | `task_steps[].gate.checklist가 비어 있음: {detail}` |

→ `TestErrorCodesCompleteness`가 존재하므로 테스트 갱신 필수.

**(7) 세션 주입 범위 — [미결-5 결정]**

> **채택: stdout 반환 + `todo_mirror_hook.py` 확장까지 (TASK.md C-3 대비 범위 확대 1건)**

`todo_mirror_hook.py` 변경:
```python
def extract_gate_checklist(stdout):
    """091: stdout에서 gate_checklist 페이로드 추출."""
    return _extract_payload(stdout, "gate_checklist")

def build_additional_context(command_name, payload, history_link=None, gate_checklist=None):
    # ... 기존 todo_mirror / history_link 파트 유지 ...
    if gate_checklist:
        parts.append(gate_checklist.get("reminder", "") + "\n"
                     + json.dumps(gate_checklist, ensure_ascii=False))
    return "\n".join(parts)
```
`main()`은 3-페이로드 분기로 확장하되 **셋 다 없으면 무출력**하는 fail-safe를 유지한다(`todo_mirror_hook.py` DEC-9).

확대 근거:
1. **R-12가 제거의 짝을 요구한다** — SKILL.md의 PM Gate 체크리스트 표를 삭제하면(R-12) PM이 점검 항목을 보는 경로가 mark 출력 하나만 남는다. 삭제와 주입은 같은 태스크에서 짝을 이뤄야 정보 손실이 0이 된다.
2. **비용이 극소** — 088이 `_extract_payload`를 이미 일반화해 두어(`:64-82`) 신규 코드가 함수 1개 + 인자 1개다. 088이 정확히 동형의 확장을 통과시킨 선례가 있어 리스크가 낮다.
3. **격리 가능** — Step 9 단일 파일 단독 Step으로 배치한다. TEST에서 회귀가 나오면 이 Step만 되돌려도 R-11/R-12 AC는 stdout만으로 충족된다(롤백 경계 명확).

대안(stdout까지만) 탈락 사유: ANALYSIS §5 R-7이 지적한 대로 "stdout에는 찍히되 088 이전의 결정론 주입 수준에는 못 미친다". 076이 hook을 도입한 전제(도구 출력이 세션 컨텍스트에 결정론적으로 반영되지 않음)가 그대로 재현된다.

#### 3.4.3 환경 변경
해당 없음 — Python 표준 라이브러리만 사용(`pathlib`·`fnmatch`는 이미 import됨).

#### 3.4.4 배치/마이그레이션
기존 태스크의 `state.json`은 `gate` 없이 존재한다. `check_gate_artifacts()`/`build_gate_payload()`가 `row.get("gate")` 부재 시 즉시 return 하므로 **소급 마이그레이션 불필요**(TASK.md 제약 d 준수).

#### 3.4.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-009 | R-10 AC | 기능 테스트 | `spec-validate` 10/10 `ok:true`. 고의 결손 3종(키 누락 / 타입 오류 / `checklist:[]`)이 각각 `spec_gate_missing_field`·`spec_gate_field_type_invalid`·`spec_gate_checklist_empty`로 검출 |
| TS-010 | R-11 AC(a) | 기능 테스트 | 산출물 부재 상태 게이트 행 mark → `ok:false`, `code:gate_artifact_missing`, `missing[]` 포함 |
| TS-011 | R-11 AC(a)/H-1 | 통합 테스트 | 위 실패 후 `state.json` 내용·mtime 무변화, `STATE.md` 무변화 |
| TS-012 | R-11 AC(b) | 기능 테스트 | artifacts 충족 시 `ok:true` + `gate_checklist` **dict** 페이로드 반환 |
| TS-013 | R-11 AC(c)/H-3 | 회귀 테스트 | `gate` 미보유 행 mark 응답이 변경 전과 동일(키 집합·값) |
| TS-014 | R-11 AC(d) | 기능 테스트 | opdw `execute.pm_gate`(artifacts `[]`) mark가 산출물 없이도 `ok:true` — 영구 차단 부재 |
| TS-015 | 미결-4 / H-5 | 기능 테스트 | artifacts 부재 + `--force --note` → `ok:true` + STATE.md 의사결정 로그에 `gate_artifact_force` + missing 목록 |
| TS-016 | H-4 | 보안 테스트 | artifacts 토큰 `/etc/passwd`·`../outside.md` → 태스크 폴더 밖 매칭 없이 missing 처리 |
| TS-017 | H-4 | 기능 테스트 | `actions/ACT-*/DONE.md` 글롭이 실제 파일 존재 시 통과, 부재 시 missing |
| TS-018 | 미결-5 / H-6 | 통합 테스트 | subprocess 실호출 stdout → `todo_mirror_hook` 실행 → `additionalContext`에 checklist 포함 |
| TS-019 | R-13 AC(c) | 회귀 테스트 | 076 `todo_mirror`·088 `history_link` 페이로드가 병존 출력되고 기존 15 hook 테스트 전건 통과 |

---

### F-005: pilot SKILL.md 감량

#### 3.5.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1~10 | `opal/skills/opal-pilot-*/SKILL.md` | 스킬 | R-4/R-5(좌표계) → R-6/R-7/R-8(중복 제거) → R-12(게이트 표 포인터화) + 변경이력 행 | §2.5.2 실측 |

#### 3.5.2 설계 — 파일 내 편집 순서 규약 + 교체 문안

**[MUST] 파일 내 편집은 반드시 아래 순서로 수행한다.** 미러 표를 먼저 지우면 `--row N`·`행 N`이 참조할 좌표계가 사라져 key 매핑 근거를 잃는다(TASK.md 배경 분석 §2, H-7).

```
① R-1/R-3 오문장·오인용 정정 (opdd·opsdd 한정)
② R-4  --row N → --task-step <key>          (미러 표를 좌표계로 사용)
③ R-5  산문 '행 N' → key 또는 항목명 참조     (동일)
④ R-6  미러 표 삭제 → 원천 포인터 1줄로 교체
⑤ R-7  치환값 절에서 모드·단계 목록 제거
⑥ R-8  init 완전 명령 1지점화
⑦ R-12 PM Gate 표 삭제 → 포인터 + 절차 산문 존치
⑧ 변경이력 행 추가
```

**② R-4 매핑 테이블**: ANALYSIS §A-6의 `--row N → key` 매핑표를 그대로 사용한다(38행 매핑 확정분). 매핑표에 "범용 템플릿"으로 표기된 3건(`opsdd:478`, `opgc:477`, `oppd:140`)은 특정 행 고정이 아니므로 `--task-step <key>` 형태의 **플레이스홀더**로 교체한다(`--row N` 리터럴 제거가 목적).

**④ R-6 교체 문안** (10종 공통):
```
> **행 구성 SSOT**: `references/pipeline.json` `task_steps[]`. 현재 행 목록은
> `~/.opal/tools/state-tool/run.sh show <task-path>` 또는 pipeline.json을 직접 조회한다.
```

**⑤ R-7 규칙**: `{모드}`·`{단계 목록}`은 `meta.mode_label`·`meta.stages`와 중복이므로 삭제한다. **스킬 고유값만 존치** — opwt "네트워크 상태"/"배치 계획" 섹션 정의, opdw `{산출물 목록}`, opdd `{설계}` 루트 등. 형식 3종(표/불릿/혼합)의 통일은 **범위 밖**(TASK.md 제외 항목의 취지 — 표기 통일은 별건)이며, 중복 제거만 수행한다.

**⑥ R-8 규칙**: 정본으로 남길 1건은 **`--mode` 인자를 포함한 완전형**이어야 한다(H-9). 실측상 `--mode` 누락본은 opgc `:116`·`:434`, opwt `:431`, opsdd `:339`, oppl `:442`이므로 정본 후보에서 제외한다. 나머지 지점은 `> STATE.md 초기 생성은 §{정본 절} 참조` 형태의 1줄 참조로 대체한다.

**⑦ R-12 교체 문안** (게이트 표 보유 7종):
```
## PM Gate 점검 목록

> **게이트 정의 SSOT**: `references/pipeline.json` `task_steps[].gate` — 산출물(`artifacts`)과
> 체크리스트(`checklist`)는 이곳에만 정의한다. `state-tool mark --task-step <게이트 key>` 호출 시
> artifacts 존재를 도구가 검증하고(미충족 시 `gate_artifact_missing`으로 거부) checklist를
> stdout `gate_checklist` 페이로드로 반환한다.

{판정 절차·기준 산문 — 존치}
```
- **[MUST]** TASK.md C-6: "SKILL.md에는 PM Gate **절차·판정 기준 산문을 남긴다**". 삭제 대상은 **산출물·체크리스트를 나열한 표**뿐이며, 게이트를 어떻게 수행하는지에 대한 서술은 보존한다.
- oppd·oppl은 표가 없고 블록쿼트 절차 서술만 있으므로(ANALYSIS §A-6) **삭제 대상 없음** — 포인터 1줄만 추가한다. opgc는 PM Gate 개념 자체가 없으므로 **무변경**.

**⑧ 변경이력**: **[MUST]** `docs/CONVENTIONS.md` §변경이력 작성 의무 — 수정한 SKILL.md 10종 전부에 `| {semver} | YYYY-MM-DD HH:mm | {변경내용} (091) |` 행을 추가한다(`docs/CONVENTIONS.md:241-242`).

**opwt 구조적 공백 처리 — [미결-2 결정]**

> **채택: (b) 동적 행은 `add-row --key` 경로로 위임하고, 정적 행만 `--task-step`으로 전환**

opwt `--row` 11건의 처리:

| 줄 | 현재 | 처리 |
|----|------|------|
| `:197,198` | `--row 1` | `--task-step task.task_md` |
| `:199` | `--row 2` | `--task-step task.user_confirm` |
| `:295` | `--row <PLAN_PM_Gate_N>` | `--task-step plan.pm_gate` |
| `:299` | `--row <PLAN_사용자확인_N>` | `--task-step plan.user_confirm` |
| `:362` | `--row <QA_PM_Gate_N>` | `--task-step qa.pm_gate` |
| `:383` | `--row <CLOSE_DONE_행N>` | `--task-step close.done_md` |
| `:249,253` | ANALYSIS 동적 게이트 | `--task-step analysis.pm_gate` / `analysis.user_confirm` — **`add-row --key`로 사전 생성** |
| `:329,334` | EXECUTE 배치 동적 게이트 | `--task-step execute.batch_pm_gate_{N}` / `execute.batch_user_confirm_{N}` — **`add-row --key`로 생성** |

동적 행 생성 규약을 opwt SKILL.md에 **신규 명문화**한다(`:437-443` 기존 `add-row` 안내 절 확장):
```
수정/분석 모드 진입 시 ANALYSIS 행을 동적 삽입한다:
  add-row <task-path> --after-task-step task.user_confirm --stage ANALYSIS --key analysis.analysis_md --item '작업'
  add-row <task-path> --after-task-step analysis.analysis_md --stage ANALYSIS --key analysis.pm_gate --item 'PM Gate'
  add-row <task-path> --after-task-step analysis.pm_gate  --stage ANALYSIS --key analysis.user_confirm --item '사용자 확인'
EXECUTE 배치 행(N=1,2,…):
  add-row … --key execute.batch_{N}            --item 'Batch {N}: {문서 목록}'
  add-row … --key execute.batch_pm_gate_{N}    --item 'PM Gate'
  add-row … --key execute.batch_user_confirm_{N} --item '사용자 확인'
```
- **[MUST]** 제안 key는 전부 `KEY_PATTERN ^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*(_[0-9]+)?$`를 만족해야 한다 — `execute.batch_pm_gate_1`은 item slug `batch_pm_gate` + 접미 `_1`로 매칭된다. EXECUTE Step에서 `add-row` 실호출로 검증한다(H-8, TS-023).

**탈락 사유**:
- **(a) opwt pipeline.json 3모드 확장** — pipeline.json 스펙에 "모드별 변형" 개념이 없다(`validate_pipeline_spec()`은 단일 `task_steps` 배열만 검증, `state_tool.py:875-934`; `meta`는 `mode_label`/`stages` 2필드뿐). 3모드를 담으려면 spec 구조 자체를 바꿔야 하고 → `spec_version` 상향 → 090이 완료한 10종 마이그레이션 재작업 → `--rows-from` 계약 변경. **이 태스크(중복 정리)의 성격을 "스펙 v2 설계"로 바꾸는 범위 초과**다.
- **(c) opwt 제외** — R-4 AC (a) "변경이력 제외 `--row ` grep 0건"이 opwt 11건 때문에 **구조적으로 달성 불가**해진다. 완료 기준을 포기하는 선택이므로 채택 불가.

**(b)의 대가(명시)**: ① opwt 동적 게이트 행에는 `gate`가 실리지 않아(§3.3.2 (4) 부수 효과) **게이트 소비 대상 밖**이다 — 배치별 PM Gate는 현행처럼 PM 판단에만 의존한다. ② opwt SKILL.md에 key 규약 서술 1건을 신규 저술해야 한다. ③ **후속 이월**: "opwt pipeline.json 3모드 반영"은 별도 태스크로 backlog 등록한다(범위 밖 명시).

#### 3.5.3 환경 변경 / 3.5.4 배치
해당 없음.

#### 3.5.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-020 | R-4 AC(a) | 산출물 검사 | 10종 SKILL.md에서 `## 변경이력` 헤딩 **이전** 구간의 `--row ` 출현 **0건** (변경이력 내 1건은 불변) |
| TS-021 | R-4 AC(b) | 기능 테스트 | 교체된 key가 전부 해당 pipeline.json `task_steps[].key`에 실재. 대표 3종(opdd·opsdd·oppl)에서 `--task-step` 실호출 exit 0 |
| TS-022 | **R-5 AC(재정의)** | 산출물 검사 | 10종 SKILL.md에서 `## 변경이력` 헤딩 **이전** 구간의 `행 [0-9]+` 출현 **0건** (기준선: 현행 비-변경이력 36건 → 0건). 변경이력 구간 13건은 **불변 — 손대지 않는다** |
| TS-023 | H-8 | 기능 테스트 | opwt 제안 key 전량(`analysis.*` 3, `execute.batch_*_1` 3)이 `add-row --key`로 exit 0 생성 |
| TS-024 | R-6 AC(a) | 산출물 검사 | 10종에서 `\| # \| 단계 \| 항목 \|` 형식 표 0건 |
| TS-025 | R-7 AC | 산출물 검사 | 10종에서 모드·단계 목록 중복 기재 0건, 잔존 항목이 pipeline.json에 없는 고유 정보만 포함 |
| TS-026 | R-8 AC | 기능 테스트 | pilot당 `state-tool/run.sh init` 완전 명령 최대 1회, 그 1건이 `--mode` 포함, 10종 init 실호출 exit 0 |
| TS-027 | R-12 AC(a) | 산출물 검사 | 게이트 산출물·체크리스트 나열 표 0건, 판정 절차 산문은 존치 |
| TS-028 | R-12 AC(b) | 통합 테스트 | 대표 3 pilot에서 게이트 행 mark 시 pipeline.json 유래 checklist가 stdout에 출력 |

> **[R-5 AC 재정의 근거]** TASK.md R-5 AC는 "`행 [0-9]+` grep이 0건"이라고만 써서 변경이력 배제를 명시하지 않았다. 문언대로 적용하면 불변 대상인 변경이력 13건까지 손대야 하는 것으로 오독되고, 이는 `docs/CONVENTIONS.md` §변경이력 작성 의무의 이력 보존 취지와 충돌한다(ANALYSIS §5 R-5). **본 PLAN은 AC 기준을 "변경이력 제외 36건 → 0건"으로 확정한다.** R-4 AC가 이미 "변경이력 행을 제외한"을 명시하고 있어 두 AC의 기준이 일치하게 된다.

---

### F-006 / F-007: 회귀·문서·배포

#### 3.6.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `docs/CONVENTIONS.md` | 문서 | §State 관리에 gate SSOT 규칙 1줄 추가 + 변경이력 | plan-guide "새 패턴/규칙 도입" |

#### 3.6.2 설계

**전후 동등 검증 절차 (F-001 baseline 소비)**:
```bash
AFTER="$(mktemp -d)/after"; mkdir -p "$AFTER"
# F-001과 동일 루프를 재실행하되 출력 디렉토리만 $AFTER로 교체
diff -r tasks/091-260813-opd-파이프라인-스펙-중복정리/baseline "$AFTER"   # 출력 없음 = 20/20 동일
```
- **[MUST]** 비교는 §3.1.2의 7필드 투영 위에서 수행한다. F-004 이후 rows[]에 `gate`가 추가되므로 원시 비교는 반드시 실패하며, 그것은 결함이 아니라 설계된 변화다.
- 중간 검증 지점 1회 추가: **F-003 완료 직후**에도 같은 비교를 수행한다(TS-008). 이 시점에는 코드가 미변경이므로 `gate` 없이 완전 동일해야 하며, 여기서 diff가 나면 pipeline.json 편집이 행 구성을 건드렸다는 뜻이다 — 원인 국소화가 쉬워진다.

**`docs/CONVENTIONS.md` §State 관리 추가 문안**:
```
- PM Gate의 산출물·체크리스트 정의는 pilot `references/pipeline.json` `task_steps[].gate`가 SSOT다.
  `mark --task-step <게이트 key>`가 `gate.artifacts` 존재를 검증하고(미충족 시 `gate_artifact_missing` 거부,
  `--force --note`로만 우회·의사결정 로그 기록) `gate.checklist`를 stdout `gate_checklist`로 반환한다.
  SKILL.md에 게이트 표를 중복 게재하지 않는다 (091).
```

**배포 정합**:
- **[MUST]** `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다." → `./scripts/install-mac.sh` 실행으로만 배포한다.
- R-14 AC "diff 0"의 적용 범위: **pipeline.json 10건 한정**. SKILL.md는 install이 변경이력 섹션을 strip 하므로(`docs/CONVENTIONS.md:243`) 완전 diff가 성립하지 않는다(H-10).

#### 3.6.3 환경 변경 / 3.6.4 배치
`./scripts/install-mac.sh` 실행 1회. 스크립트 자체는 변경하지 않는다.

#### 3.6.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-029 | R-13 AC(a) | 회귀 테스트 | baseline vs after `diff -r` 출력 없음 (20/20) |
| TS-030 | R-13 AC(b) | 회귀 테스트 | `cd opal/tools/state-tool && python3 -m pytest tests/ -q` → 기존 284 + 신규 전건 passed |
| TS-031 | R-13 AC(c)/H-11 | 회귀 테스트 | 088 히스토리 연결·076 todo_mirror 페이로드 동작 불변, `show --format json` 정상 |
| TS-032 | R-14 AC | 통합 테스트 | 배포본 pipeline.json 10건 `diff` 0. 배포 경로 state-tool로 대표 3 pilot init + 게이트 mark 차단 재현 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 0 | F-001 | 1 | opal-task-agent | 순차 | **최초 1회, 편집 전 필수** |
| 1 | F-002 | 2 | opal-task-agent | 순차 | 하네스 상위 규칙 해제 |
| 2 | F-003 | 3, 4, 5, 6 | opal-be-agent(3) / opal-task-agent(4~6) | 4∥5∥6 병렬 가능 | Step 3 완료 후 |
| 3 | F-004 | 7, 8, 9 | opal-test-agent(7) / opal-be-agent(8, 9) | 순차 | RED → GREEN |
| 4 | F-005 | 10, 11, 12, 13 | opal-task-agent | 10∥11∥12∥13 병렬 가능 | 파일 비중첩 |
| 5 | F-006, F-007 | 14, 15, 16 | opal-test-agent(14) / PM 직접(15) / opal-task-agent(16) | 순차 | |

### 4.2 실행 체크리스트

> 총 16개 Step | Phase 6개 | 실행 모드: **복잡**

#### Step 1: 전후 동등 baseline 캡처 (10 pilot × 2 mode)
- [x] 완료
- **소속 기능**: F-001
- **영역**: 배치
- **agent**: opal-task-agent
- **파일**: `tasks/091-260813-opd-파이프라인-스펙-중복정리/baseline/*.json` (신규 20건)
- **작업 내용**: §3.1.2의 bash 루프를 프로젝트 루트에서 실행한다. 10 pilot × {interactive, agentic} = 20회 `init`을 임시 디렉토리에 수행하고, 각 `state.json`의 `rows[]`를 7필드(`row_id, stage, item, key, status, status_label, owner`)로 투영해 `baseline/{skill}-{mode}.json`에 저장한다. **어떤 프로젝트 파일도 수정하지 않는다.**
- **완료 기준**: `baseline/` 아래 파일 20개. 각 배열 길이가 해당 pipeline.json `task_steps` 길이와 일치(opd 16 / opds 11 / opdw 9 / opp 9 / opwt 10 / opgc 7 / oppd 13 / opsdd 25 / oppl 19 / opdd 15).
- **테스트**: TS-001
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: 하네스 상위 규칙 2건 정정 (미러 표 의무 해제)
- [x] 완료
- **소속 기능**: F-002
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/core/references/harness/state-template.md`, `opal/core/references/harness/qa-standards.md`
- **작업 내용**: §3.2.2 문안으로 `state-template.md:94`, `qa-standards.md:46`을 교체한다. 두 파일 각각 변경이력 표에 행을 추가한다(KST 일시 + `(091)`).
- **완료 기준**: 두 파일에서 "행 예시가 명시" 패턴 grep 0건이고 `references/pipeline.json` 문자열이 각 1건 이상. 변경이력 행 2건 추가됨.
- **테스트**: TS-002
- **실행 방법**: sub-agent
- **의존**: 없음 (Step 1과 병렬 가능하나 순차 배치 — Step 1이 짧다)

#### Step 3: `gate` 스키마 2종 신설
- [x] 완료
- **소속 기능**: F-003
- **영역**: 공통
- **agent**: opal-be-agent
- **파일**: `opal/tools/state-tool/schema/pipeline-spec.schema.json`, `opal/tools/state-tool/schema/state.schema.json`
- **작업 내용**: §3.3.2 (1)의 `gate` 객체를 (a) `pipeline-spec.schema.json`의 `task_steps.items.properties`에 추가하고 최상위 `pm_gate` 정의를 **삭제**한다 (b) `state.schema.json`의 `rows.items.properties`에 `key`/`conditional` 형제로 추가한다. `additionalProperties:false`가 두 곳 모두에 걸려 있으므로 등록 없이는 문서 계약 위반이다.
- **완료 기준**: 두 파일이 유효 JSON이고, `gate.checklist.minItems == 1`·`artifacts`에 minItems 없음. `pipeline-spec.schema.json`에 `pm_gate` 키 0건.
- **테스트**: TS-005, TS-006 (간접)
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 4: pipeline.json 3종 — 최상위 `pm_gate[]` → `task_steps[].gate` 이관 (opd/opds/opdw)
- [x] 완료
- **소속 기능**: F-003
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-dev/references/pipeline.json`, `opal/skills/opal-pilot-dev-short/references/pipeline.json`, `opal/skills/opal-pilot-dev-wireframe/references/pipeline.json` (3파일)
- **작업 내용**: §3.3.2 (3)의 배치 명세대로 opd 4건·opds 2건·opdw 2건의 `gate`를 해당 `task_steps[]` 항목에 인라인 추가하고 최상위 `pm_gate` 키를 삭제한다. **드리프트 2건은 SKILL.md 상세본 채택** — opd `test_scenario.scenario_gate` ⑥에 `"L3 [SUPERVISOR] 마커 + PM 요청 양식"`, opdw `wireframe.pm_gate`에 `"op-dev-qa/SKILL.md 와이어프레임 검증 기준 참조"`. `changed_files`·`GC-CONVENTION-*.md`는 §3.3.2 (2) 문안으로 checklist에 전치한다(원문 보존).
- **완료 기준**: 3파일 최상위 `pm_gate` 0건, 게이트 행 8건이 `gate` 보유, `python3 -m json.tool` 통과, `spec-validate` 3/3 `ok:true`.
- **테스트**: TS-005, TS-006, TS-007
- **실행 방법**: sub-agent
- **의존**: Step 3

#### Step 5: pipeline.json 3종 — `gate` 이관 (opp: 최상위 `pm_gate[]` / opwt·opsdd: SKILL.md 표 + 부족분 저술)
- [x] 완료
- **소속 기능**: F-003
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-project/references/pipeline.json`, `opal/skills/opal-pilot-write-tech/references/pipeline.json`, `opal/skills/opal-pilot-sdd/references/pipeline.json` (3파일)
- **작업 내용**: opp는 최상위 `pm_gate[]` 2건 이관 후 키 삭제. opwt는 SKILL.md `:472-480` 표에서 `plan.pm_gate` 이관 + `qa.pm_gate` 신규 저술(SKILL.md `:355-376` "PM 최종 판정" 절에서 추출). opsdd는 SKILL.md `:412-421` 표에서 3건 이관 + `review.pm_gate`·`verify.pm_gate` 2건 신규 저술. opsdd `execute.pm_gate.artifacts = ["actions/ACT-*/DONE.md"]`(글롭). **[MUST] artifacts에는 해당 게이트 시점까지 반드시 생성되는 태스크 폴더 기준 파일만 올린다** — 확신이 없으면 checklist에 남긴다(§3.3.2 (2) 적격 표).
- **완료 기준**: 3파일 최상위 `pm_gate` 0건, 게이트 행 9건(opp 2 + opwt 2 + opsdd 5)이 `gate` 보유, `spec-validate` 3/3 `ok:true`.
- **테스트**: TS-005, TS-006, TS-017
- **실행 방법**: sub-agent
- **의존**: Step 3

#### Step 6: pipeline.json 3종 — `gate` 신규 저술 (opdd/oppd/oppl) + opgc 제외 확정
- [x] 완료
- **소속 기능**: F-003
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-data-design/references/pipeline.json`, `opal/skills/opal-pilot-project-dev/references/pipeline.json`, `opal/skills/opal-pilot-project-loop/references/pipeline.json` (3파일)
- **작업 내용**: opdd는 SKILL.md `:268-279` 표 5행을 게이트 행 4건에 매핑하되 **TASK 행 체크리스트를 `dict.pm_gate.checklist` 선두에 병합**하고 산출물은 전부 `{설계}` 가변 경로이므로 `artifacts: []`. oppd 3건·oppl 3건은 각 stage 선행 `작업` 행의 완료 기준과 SKILL.md 절차 서술에서 체크리스트를 **신규 저술**한다. **opgc는 대상이 아니다** — PM Gate 개념 자체가 없고(게이트 행 0, SKILL.md 절 없음) 이관 원본이 존재하지 않는다. opgc pipeline.json은 무변경.
- **완료 기준**: 3파일 게이트 행 10건(opdd 4 + oppd 3 + oppl 3)이 `gate` 보유, `checklist` 전건 비어있지 않음, `spec-validate` 3/3 `ok:true`. opgc pipeline.json `git diff` 0.
- **테스트**: TS-005
- **실행 방법**: sub-agent
- **의존**: Step 3

#### Step 7: RED-first 테스트 작성 (게이트 검증·소비·hook 릴레이)
- [x] 완료
- **소속 기능**: F-004
- **영역**: BE
- **agent**: opal-test-agent
- **파일**: `opal/tools/state-tool/tests/test_state_tool.py`, `opal/tools/state-tool/tests/test_todo_mirror_hook.py` (2파일)
- **작업 내용**: `test_state_tool.py` 최하단(`TestCloseHistoryLink` 이후)에 `TestTaskStepGate` 클래스를 신설하고, `TestPipelineSpecValidate`에 gate violation 4종 케이스를 추가하며, `TestErrorCodesCompleteness`에 신규 코드 5종을 반영한다. `test_todo_mirror_hook.py`에 `gate_checklist` 릴레이 케이스를 추가한다. 호출 패턴은 070 선례를 따른다 — 로직은 `_call070` 직접 호출, CLI 계약 1~2건은 `_run070` subprocess. **[MUST] mock/patch 금지** (`opal/core/references/harness/red-first.md` §4). **이 Step에서는 구현을 건드리지 않는다 — 신규 테스트가 실패(RED)하는 것이 정상 결과다.**
- **완료 기준**: 신규 테스트가 TS-009~TS-019를 커버하고, 실행 시 **신규분만 실패**하며 기존 284건은 전건 통과(RED 증거 확보).
- **테스트**: TS-009 ~ TS-019 (RED 상태)
- **실행 방법**: sub-agent
- **의존**: Step 4, Step 5, Step 6 (실 pipeline.json을 픽스처로 참조)

#### Step 8: `state_tool.py` 게이트 집행 구현
- [x] 완료
- **소속 기능**: F-004
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `opal/tools/state-tool/state_tool.py` (1파일)
- **작업 내용**: §3.4.2 (1)~(6)을 구현한다 — ① `ERROR_CODES` 5종 추가 ② `validate_pipeline_spec()`에 gate 검사 4건 ③ `_is_safe_artifact_token()`·`check_gate_artifacts()` 신설 ④ `build_gate_payload()` 신설 ⑤ `build_rows_from_pipeline_json()`·`build_rows_from_spec()`에 gate 전파 1줄씩 ⑥ `cmd_mark`의 `:1438`↔`:1440` 사이에 가드 호출, `:1521-1534` decision 로그에 `gate_artifact_force` 분기, `_ok_kwargs`에 `gate_checklist` 조건부 추가. **[MUST]** 가드는 `save_state_json()`(`:1507`) 이전 검증 구간에만 위치한다(H-1). **[MUST]** `gate` 미보유 행에서 즉시 return 하여 기존 동작을 바이트 단위로 보존한다(H-3). **[MUST]** `opal/core/PRINCIPLES.md` §3: "Touch only what the plan names. Don't improve adjacent code." — 인접 로직 리팩터링 금지.
- **완료 기준**: Step 7의 신규 테스트 전건 GREEN + 기존 284건 유지. `spec-validate` 10/10 `ok:true`. 모듈 상단 @header `description`에 091 변경 요약 추가.
- **테스트**: TS-009 ~ TS-017
- **실행 방법**: sub-agent
- **의존**: Step 7

#### Step 9: `todo_mirror_hook.py` checklist 세션 주입 확장
- [x] 완료
- **소속 기능**: F-004
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `opal/tools/state-tool/todo_mirror_hook.py` (1파일)
- **작업 내용**: §3.4.2 (7)대로 `extract_gate_checklist()`를 신설하고 `build_additional_context(command_name, payload, history_link=None, gate_checklist=None)`로 확장, `main()`을 3-페이로드 분기로 바꾼다. **[MUST]** 셋 다 없으면 무출력 exit 0 fail-safe를 유지한다 — hook은 정상 도구 흐름을 절대 차단하지 않는다. @header `exports`·`description` 갱신.
- **완료 기준**: TS-018·TS-019 GREEN. 기존 hook 테스트 15건 전건 통과. 076/088 페이로드가 병존 출력됨.
- **테스트**: TS-018, TS-019
- **실행 방법**: sub-agent
- **의존**: Step 8

#### Step 10: pilot SKILL.md 감량 — opd / opds / opp
- [x] 완료
- **소속 기능**: F-005
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-dev/SKILL.md`, `opal/skills/opal-pilot-dev-short/SKILL.md`, `opal/skills/opal-pilot-project/SKILL.md` (3파일)
- **작업 내용**: §3.5.2 편집 순서 ①~⑧을 파일별로 수행한다. 이 3종은 `--row` 0건이므로 ②는 생략. R-5 대상은 opd 6 / opds 9 / opp 8 (비-변경이력). R-6 미러 표 삭제 — opd `:288-305`(16행), opds `:260-272`(11행), opp `:166-176`(9행). R-7 치환값 절 — opd `:275-311`, opds `:247-279`, opp `:153-182`. R-8 해당 없음(각 1회). R-12 게이트 표 → 포인터 — opd `:312-321`, opds `:280-288`, opp `:183-191`. **[MUST] 변경이력 구간(`## 변경이력` 이후)은 손대지 않는다.**
- **완료 기준**: 3파일에서 비-변경이력 `행 [0-9]+` 0건, `\| # \| 단계 \| 항목 \|` 표 0건, 게이트 나열 표 0건. 각 파일 변경이력 행 1건 추가. init 실호출 3/3 exit 0.
- **테스트**: TS-022, TS-024, TS-025, TS-026, TS-027
- **실행 방법**: sub-agent
- **의존**: Step 2, Step 4, Step 9

#### Step 11: pilot SKILL.md 감량 — opdw / opgc
- [x] 완료
- **소속 기능**: F-005
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-dev-wireframe/SKILL.md`, `opal/skills/opal-pilot-gc/SKILL.md` (2파일)
- **작업 내용**: §3.5.2 ①~⑧. R-4 — opgc 2건(`:343` → `close.done_md`, `:477` 범용 템플릿). R-5 — opdw 3건, opgc 0건. R-6 — opdw `:194-204`(9행), opgc `:442-450`(7행). R-7 — opdw `:181-211`(불릿 형식), opgc `:424-455`. R-8 — opdw 2→1(`:190` 또는 `:245` 중 `--mode` 포함본 존치), opgc 3→1(`:482`가 유일한 `--mode` 포함본이므로 이를 정본으로). R-12 — opdw `:212-219` 포인터 교체. **opgc는 PM Gate 절이 없으므로 R-12 대상 아님.**
- **완료 기준**: 2파일 비-변경이력 `--row ` 0건·`행 [0-9]+` 0건, 미러 표 0건, init 완전 명령 각 1회이며 `--mode` 포함. 변경이력 행 2건 추가.
- **테스트**: TS-020 ~ TS-022, TS-024 ~ TS-027
- **실행 방법**: sub-agent
- **의존**: Step 2, Step 4, Step 6, Step 9

#### Step 12: pilot SKILL.md 감량 — opdd / opsdd (최다 작업량 + R-1/R-3 정정)
- [x] 완료
- **소속 기능**: F-002, F-005
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-data-design/SKILL.md`, `opal/skills/opal-pilot-sdd/SKILL.md` (2파일)
- **작업 내용**: §3.5.2 ①~⑧ 전 단계 적용. **① R-1/R-3** — opdd `:241` "아래 표를 파싱" → "`--rows-from`이 `references/pipeline.json`의 `task_steps[]`를 읽어 행을 생성한다", opdd `:242` 줄번호 인용 **삭제**, opsdd `:386`·`:399` "위 SSOT 표를 기준으로" → "`references/pipeline.json`을 기준으로". **② R-4** — opdd 14건·opsdd 9건(변경이력 `:544` 제외)을 ANALYSIS §A-6 매핑표대로 `--task-step <key>`로 교체. **③ R-5** — opdd 7건·opsdd 2건. **④ R-6** — opdd `:245-261`(15행), opsdd `:356-382`(25행). **⑤ R-7** — opdd `:232-267`, opsdd `:327-411`. **⑥ R-8** — 각 2→1. **⑦ R-12** — opdd `:268-279`, opsdd `:412-421`. **[MUST] 범위 밖 고정**: opsdd 산문 `EXECUTE-LOOP` 표기 17곳은 건드리지 않는다(090 D-7c 확정).
- **완료 기준**: 2파일 비-변경이력 `--row ` 0건(23건 전환)·`행 [0-9]+` 0건(9건 전환), `표를 파싱`·`SSOT 표를 기준` grep 0건, 타 SKILL.md 줄번호 인용 0건, 미러 표 0건. 변경이력 행 2건 추가. init 실호출 2/2 exit 0.
- **테스트**: TS-003, TS-004, TS-020 ~ TS-022, TS-024 ~ TS-027
- **실행 방법**: sub-agent
- **의존**: Step 2, Step 5, Step 6, Step 9

#### Step 13: pilot SKILL.md 감량 — opwt / oppd / oppl (+ opwt 동적 key 규약 저술)
- [x] 완료
- **소속 기능**: F-005
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-write-tech/SKILL.md`, `opal/skills/opal-pilot-project-dev/SKILL.md`, `opal/skills/opal-pilot-project-loop/SKILL.md` (3파일)
- **작업 내용**: §3.5.2 ①~⑧ + **opwt 동적 행 key 규약 신규 저술**(§3.5.2 미결-2 (b)안 표대로). R-4 — opwt 11건(정적 7 + 동적 4 → `add-row --key` 규약 경유), oppd 5건, oppl 4건. R-5 — opwt 1건, oppd·oppl 0건. R-6 — opwt `:444-455`(10행), oppd `:120-134`(13행), oppl `:137-157`(19행). R-7 — opwt `:419-462`(혼합 형식), **oppd·oppl은 치환값 절 자체가 없어 대상 아님**. R-8 — opwt 3→1(`:193`이 `--mode` 포함 정본), oppd 1(중복 없음), oppl 2→1. R-12 — opwt `:472-480` 포인터 교체, **oppd·oppl은 표가 없으므로 포인터 1줄만 추가**.
- **완료 기준**: 3파일 비-변경이력 `--row ` 0건(20건 전환)·`행 [0-9]+` 0건, 미러 표 0건, opwt 제안 key 6종이 `KEY_PATTERN` 매칭. 변경이력 행 3건 추가. init 실호출 3/3 exit 0.
- **테스트**: TS-020 ~ TS-024, TS-026, TS-027
- **실행 방법**: sub-agent
- **의존**: Step 2, Step 5, Step 6, Step 9

#### Step 14: 전후 동등 + 전체 회귀 검증
- [x] 완료
- **소속 기능**: F-006
- **영역**: 공통
- **agent**: opal-test-agent
- **파일**: (검증 전용 — 프로젝트 파일 무변경. 증거는 TEST 산출물로 보고)
- **작업 내용**: §3.6.2 절차로 `after` 스냅샷을 재생성해 `diff -r baseline after`를 수행한다(20/20 무출력 기대). `cd opal/tools/state-tool && python3 -m pytest tests/ -q` 전건 실행. 대표 3 pilot에서 게이트 행 mark 실호출로 (a) artifacts 부재 차단 (b) 충족 시 checklist stdout (c) `--force --note` 우회 + 의사결정 로그를 재현한다. 088 히스토리 연결·076 todo_mirror 페이로드 불변 확인.
- **완료 기준**: `diff -r` 무출력, pytest 284+N passed·0 failed, TS-029 ~ TS-032 전건 Pass 증거(실제 출력) 확보.
- **테스트**: TS-029, TS-030, TS-031
- **실행 방법**: sub-agent
- **의존**: Step 10, 11, 12, 13

#### Step 15: `docs/CONVENTIONS.md` §State 관리 갱신
- [x] 완료
- **소속 기능**: F-007
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/CONVENTIONS.md` (1파일)
- **작업 내용**: §3.6.2 문안을 §State 관리(`:224-230`) 목록에 추가하고 변경이력 표에 행을 추가한다. 새 규칙(게이트 정의 SSOT + 도구 집행 + `--force` 우회 기록)이 프로젝트 전역 규약이 되므로 갱신 대상이다.
- **완료 기준**: §State 관리에 `task_steps[].gate` 규칙 1항목 추가, 변경이력 행 1건. `--row` deprecated 규정(`:228`)은 불변.
- **테스트**: 산출물 검사 (grep `task_steps\[\].gate` ≥1)
- **실행 방법**: direct
- **의존**: Step 14

#### Step 16: install 재배포 + 배포본 실동작 확인
- [x] 완료
- **소속 기능**: F-007
- **영역**: 배치
- **agent**: opal-task-agent
- **파일**: `~/.opal/**` (배포본 재생성 — **소스 무변경**)
- **작업 내용**: **[MUST]** `.opal/AGENT.md` §금지사항 — `~/.opal/`을 직접 편집하지 않는다. `./scripts/install-mac.sh`를 실행해 재배포한 뒤, 배포본 pipeline.json 10건과 소스를 `diff`한다(0 기대). 배포 경로 `~/.opal/tools/state-tool/run.sh`로 대표 3 pilot init + 게이트 행 mark 차단을 재현한다. SKILL.md는 install이 변경이력을 strip 하므로 완전 diff 대상이 아니다(H-10).
- **완료 기준**: pipeline.json 10건 diff 0. 배포 경로 init 3/3 exit 0, 게이트 차단 1건 이상 재현.
- **테스트**: TS-032
- **실행 방법**: sub-agent
- **의존**: Step 15

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| **R-1. Step 1 → 그 외 전부** | baseline은 편집 전에만 캡처 가능하다. TASK.md 제약 (a)의 "전후 동등"은 "전"이 존재해야 성립하며, 편집 후에는 원복 없이 재현 불가능하다 |
| **R-2. Phase 2(gate 데이터) → Phase 4(SKILL.md)** | TASK.md C-4의 논리 Phase 순서(정정→key→중복 제거→게이트 승격)를 물리 순서로 그대로 쓰면, 각 pilot SKILL.md가 R-4/R-5/R-6/R-7/R-8 Step과 R-12 Step **두 번**에 걸쳐 편집된다. 프롬프트 [MUST] 산출량 상한 규칙은 "동일 파일을 2개 이상 Step이 변경하면 같은 Step에 묶어라(후행 저장이 선행 편집을 덮어쓰는 충돌 방지)"를 요구하므로, R-12를 흡수하려면 그 선행 조건인 gate 데이터 이관(R-9)이 먼저 끝나야 한다. **논리 순서는 §3.5.2의 파일 내 편집 순서 ①~⑧로 보존된다** |
| **R-3. Phase 2 → Phase 3(도구)** | Step 7 RED 테스트가 실 pipeline.json을 픽스처로 참조한다. 또한 R-10 gate 검증은 실제 데이터 형태를 기준으로 작성되어야 오검출이 없다 |
| **R-4. Step 7 → Step 8** | RED-first — 테스트가 먼저 실패해야 GREEN 증거가 성립한다 (`red-first.md` §1.5 "비즈니스 로직·API 계약"). 생성자≠평가자를 위해 작성 에이전트를 분리한다 |
| **R-5. Step 8 → Step 9** | hook은 `state_tool.py`가 출력하는 `gate_checklist` 페이로드를 소비한다. 생산자 우선 |
| **R-6. Phase 3 → Phase 4** | R-12 AC (b)가 "게이트 행 mark 시 checklist가 실제로 stdout에 출력됨"을 요구한다 — 도구가 완성돼야 SKILL.md의 새 서술이 사실이 된다 |
| **R-7. Step 3 → Step 4 ∥ 5 ∥ 6** | 스키마가 `gate` 형태를 확정한 뒤 데이터를 쓴다. Step 4/5/6은 각 3파일씩 비중첩이므로 병렬 가능 |
| **R-8. Step 10 ∥ 11 ∥ 12 ∥ 13** | 10개 SKILL.md를 3/2/2/3으로 분할했고 파일이 서로 겹치지 않는다. 각 Step ≤3 파일로 산출량 상한을 만족한다 |
| **R-9. Step 14 → 15 → 16** | 회귀가 통과해야 규약을 문서화할 가치가 있고, 문서까지 확정된 뒤 배포해야 배포본이 최종 상태를 담는다 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA
| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | baseline 20건 캡처 완결성 | TS-001 | 파일 20개, 배열 길이가 각 pipeline.json `task_steps` 길이와 일치 |
| F-002 | 상위 규칙·오문장 정정 | TS-002, TS-003, TS-004 | 4개 패턴 grep 전부 0건 + pipeline.json 원천 지시 존재 |
| F-003 | gate 27건 이관 무손실 | TS-005, TS-006, TS-007, TS-008 | 게이트 행 27/27 `gate` 보유, 최상위 `pm_gate` 0건, 드리프트 2건 상세본 채택, 전치 토큰 원문 보존, 이 시점 baseline diff 0 |
| F-004 | 게이트 집행 정확성 | TS-009 ~ TS-019 | 차단·통과·무영향·force 우회·경로 안전·hook 릴레이 전건 Pass |
| F-005 | SKILL.md 감량 + 좌표계 전환 | TS-020 ~ TS-028 | 비-변경이력 `--row ` 0 / `행 N` 0 / 미러 표 0 / 게이트 표 0 / init 1회, 변경이력 10건 추가 |
| F-006 | 전후 동등·회귀 무손실 | TS-029, TS-030, TS-031 | diff 20/20 무출력, pytest 전건 passed, 076/088 동작 불변 |
| F-007 | 문서·배포 정합 | TS-032 | CONVENTIONS.md 규칙 추가, 배포본 pipeline.json diff 0, 배포 경로 실동작 |

### 5.2 회귀 테스트
- [ ] `cd opal/tools/state-tool && python3 -m pytest tests/ -q` — 기존 284건 전건 통과 (신규분 별도 집계)
- [ ] `gate` 미보유 행 mark 응답의 키 집합·값이 변경 전과 동일 (H-3)
- [ ] `gate` 없는 기존 태스크 `state.json`으로 mark/advance/block/status 정상 동작 (H-2, TASK.md 제약 d)
- [ ] `--rows-spec` 인라인 경로 init 정상 (TASK.md 제약 e)
- [ ] `--rows-from *.md` deprecated 폴백 경로 무영향
- [ ] 076 `todo_mirror` / 088 `history_link` 페이로드 병존 출력 (H-6)
- [ ] `dashboard/backend` `show --format json` 소비 경로 정상 (H-11)
- [ ] 10 pilot × 2 mode init `rows[]` 7필드 투영 전후 동일 (TS-029)

### 5.3 코드/문서 품질
- [ ] `docs/CONVENTIONS.md` §State 관리 [MUST] 준수 — 신규 문서·프롬프트에 `--row` 미사용 (`docs/CONVENTIONS.md:228`)
- [ ] `.opal/AGENT.md` §금지사항 — `~/.opal/` 직접 편집 0건, install 경유 배포만 수행
- [ ] 변경이력 행 추가 — SKILL.md 10 + 하네스 참조 2 + `docs/CONVENTIONS.md` 1 = **13건** (`docs/CONVENTIONS.md:241-242`)
- [ ] `state_tool.py`·`todo_mirror_hook.py` @header `description`/`exports` 갱신 (`docs/CONVENTIONS.md:212-216`)
- [ ] `opal/core/PRINCIPLES.md` §3 — PLAN이 명명하지 않은 인접 코드 개선 0건
- [ ] pipeline.json 10종 `python3 -m json.tool` 파싱 통과 + `spec-validate` 10/10 `ok:true`
- [ ] **범위 밖 고정 확인** — opsdd 산문 `EXECUTE-LOOP` 17곳 무변경, `## Agentic / Semi-Agentic 모드` 절 통합 미수행, 변경이력·`> 근거:` 인용줄 무변경

### 5.4 보안
- [ ] artifacts 토큰이 태스크 폴더 밖(절대경로·`..`)을 매칭하지 않는다 — `_is_safe_artifact_token()` (TS-016, H-4)
- [ ] glob 매칭이 심볼릭 링크를 통해 폴더 밖으로 나가지 않는지 확인 (`Path.glob`은 기본적으로 경로 구분자를 넘지 않음)
- [ ] 게이트 오류 메시지에 태스크 폴더 절대 경로 전체를 노출하지 않고 상대 토큰만 반환
- [ ] `--force` 우회가 `--note` 없이는 불가능함을 재확인 (`state_tool.py:1398-1399`)
- [ ] 코드·pipeline.json에 하드코딩된 토큰/시크릿 없음
- [ ] hook 확장이 예외를 삼켜 정상 도구 흐름을 차단하지 않음 (fail-safe exit 0)

---

## 6. 복잡도 판별
| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 16개 | 복잡 |
| 변경 파일 수 | 27개 (SKILL.md 10 + pipeline.json 9 + schema 2 + py 2 + tests 2 + 하네스 2 + docs 1 + baseline 20 신규) | 복잡 |
| 모듈 범위 | 다중 (스킬 자산 / 도구 코어 / 하네스 참조 / 프로젝트 문서 / 배포) | 복잡 |
| 작업 유형 | 대규모 개선 + 신규 집행 로직 | 복잡 |
| 외부 의존성 | 없음 (Python 표준 라이브러리) | 단순 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

```
Batch 1 (순차)   : [Step 1 baseline] → [Step 2 하네스 정정]
Batch 2 (순차)   : [Step 3 스키마]
Batch 3 (병렬 3) : [Step 4 pipeline×3] ∥ [Step 5 pipeline×3] ∥ [Step 6 pipeline×3]
Batch 4 (순차)   : [Step 7 RED] → [Step 8 state_tool.py] → [Step 9 hook]
Batch 5 (병렬 4) : [Step 10 opd/opds/opp] ∥ [Step 11 opdw/opgc] ∥ [Step 12 opdd/opsdd] ∥ [Step 13 opwt/oppd/oppl]
Batch 6 (순차)   : [Step 14 회귀] → [Step 15 docs] → [Step 16 배포]
```

**그룹핑 근거**:
1. **파일 충돌 방지 최우선** — 동일 SKILL.md를 두 Step이 만지지 않도록 파일 단위로 배타 분할했다(Batch 5). `state_tool.py`는 단일 Step(8)이 독점한다.
2. **산출량 상한** — 모든 Step이 생성·수정 파일 ≤3개. Step 1(baseline 20건)은 예외로 취급한다 — 동일 스크립트가 기계 생성하는 측정 산출물이며 설계 판단이 개입하지 않는다.
3. **병렬 극대화** — Batch 3(3-way)과 Batch 5(4-way)가 전체 소요의 대부분을 차지하며 상호 독립이다.

### C-2. 스킬 요구사항
- 기존 스킬로 충족. EXECUTE 단계는 `op-dev-execute` 표준 흐름을 따른다.
- 갭 판별: Batch 5의 4개 Step이 §3.5.2 "파일 내 편집 순서 ①~⑧"이라는 **동일 패턴**을 반복한다(3개 이상 Step → 스킬 후보). 다만 1회성 마이그레이션이므로 스킬화하지 않고 **PLAN §3.5.2를 인라인 지침으로 각 디스패치에 전달**한다.

### C-3. 도구 요구사항
| 도구 | 용도 | 설치 필요 |
|------|------|----------|
| `python3` | state_tool 실행·pytest·JSON 투영 | 기존 |
| `bash` + `opal/tools/state-tool/run.sh` | init/mark/spec-validate 실호출 | 기존 |
| `pytest` | 284+N 회귀 | 기존 |
| `./scripts/install-mac.sh` | 배포 (Step 16) | 기존 |
| `grep`/`diff` | AC 검증 | 기존 |
- 신규 패키지·MCP 없음.

### C-4. 테스트 전략
- **기능 테스트**: `opal/tools/state-tool/tests/` — `python3 -m pytest tests/ -q` (Step 7에서 RED, Step 8/9에서 GREEN)
- **회귀 테스트**: 동일 명령의 전건 실행 + §3.6.2 baseline diff 20/20
- **산출물 검사**: §5.1의 grep AC 전건 (변경이력 구간 배제 규약을 반드시 적용 — `## 변경이력` 헤딩 기준 head 분할)
- **통합 테스트**: 배포 경로(`~/.opal/tools/state-tool/run.sh`) 실호출로 게이트 차단 재현 (Step 16)
- **[MUST]** `opal/core/references/harness/red-first.md` §4 — mock/patch 금지, 공개 인터페이스(`cmd_*` 함수 / `run.sh` subprocess)로만 검증

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 도구 코어 | Python 3 (표준 라이브러리 전용, `state_tool.py:16-25`) | — (외부 스킬 불요) |
| 데이터 | JSON / JSON Schema draft-07 (**비집행 문서**) | — |
| 문서 | Markdown (pilot SKILL.md, 하네스 참조) | — |
| 셸 | Bash (`run.sh`, `install-mac.sh`) | — |
| 테스트 | unittest + pytest 러너 (284 tests 기준선) | — |

> ANALYSIS §6.2/§6.3이 확인한 대로 이 태스크는 프레임워크 내부 정리이며 외부 커뮤니티 스킬·MCP 도입 대상이 아니다. `trailofbits/modern-python`은 uv/ruff/async 패턴을 다루나 `state_tool.py`는 표준 라이브러리 단일 파일 CLI라 적용 지점이 없다.

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| (사용 없음) | 외부 라이브러리 조사 불필요 — 전 근거가 레포 내부 실측 |

### 8.3 참조 문서 (설계 결정 근거)
| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | 090 DONE.md | `tasks/090-260813-opds-파이프라인-스펙-마이그레이션/DONE.md` | 이월 4건 출처, 전후 동등 검증 선례 |
| D-2 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | §State 관리(`:224-230`)·변경이력(`:239-243`)·배포 경계(`:245-250`)·@header(`:210-216`) |
| D-3 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py` | `cmd_mark:1383-1553`, `validate_pipeline_spec:875-934`, `build_rows_from_pipeline_json:937-972`, `ERROR_CODES:81-127`, `cmd_add_row` |
| D-4 | 설계 | pipeline-spec.schema.json | `opal/tools/state-tool/schema/pipeline-spec.schema.json` | `task_steps[]` 허용 필드(`:20-47`), 최상위 `pm_gate` 정의 |
| D-5 | 설계 | state.schema.json | `opal/tools/state-tool/schema/state.schema.json` | `rows[]` `additionalProperties:false`(`:47`), `key`/`conditional` 선례(`:102-110`) |
| D-6 | 설계 | state-template.md | `opal/core/references/harness/state-template.md` | `:94` 미러 표 의무 서술 |
| D-7 | 설계 | qa-standards.md | `opal/core/references/harness/qa-standards.md` | `:46` 산출물 오버라이드 근거 |
| D-8 | 설계 | PM 프로필 | `.opal/AGENT.md` | 배포 경계·변경이력·하네스 우회 금지 |
| D-9 | 설계 | PRINCIPLES.md | `opal/core/PRINCIPLES.md` | Core Stance "Enforce, don't just advise" / §3 Surgical Changes |
| D-10 | 소스 | todo_mirror_hook.py | `opal/tools/state-tool/todo_mirror_hook.py` | `_extract_payload:64-82` dict 전용 제약, `build_additional_context` 확장 지점 |
| D-11 | 소스 | pilot pipeline.json × 10 | `opal/skills/opal-pilot-*/references/pipeline.json` | `pm_gate` 보유 실측, `task_steps[].key` 전수 |
| D-12 | 설계 | pilot SKILL.md × 10 | `opal/skills/opal-pilot-*/SKILL.md` | PM Gate 표·미러 표·`--row`·`행 N`·init 중복 실측 |
| D-13 | 설계 | red-first.md | `opal/core/references/harness/red-first.md` | §1.5 RED-first 강제 분류, §4 mock 금지 |
| D-14 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | §2 인라인 인용·§2.4 `[MUST]` 토큰·§4 PLAN 트랙 요건 |
| D-15 | 설계 | scenario-gate.md | `opal/core/references/harness/scenario-gate.md` | 다음 단계(TEST-SCENARIO)의 목표-커버 게이트 규칙 — 리스크 가설 표가 그 입력 |
| D-16 | 소스 | convention-checker AGENT.md | `opal/agents/opal-convention-checker/AGENT.md` | `:150-154` GC-CONVENTION-*.md 산출 규칙(조건부·타임스탬프 가변) |
| D-17 | 설계 | PROJECT.md | `docs/PROJECT.md` | §프로젝트 구성 — Framework 영역 전문 에이전트 지정(agent 배정 근거) |

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| 1 | baseline 미확보 상태로 편집 착수 → 전후 동등 검증 불가 | F-001 | 치명 | Step 1을 무조건 최초 실행. Step 2 이후 디스패치 전 PM이 `baseline/` 20개 파일 존재를 확인한다 |
| 2 | 게이트 가드가 mutation 구간에 삽입 → 부분 상태 변경 | F-004 | 높음 | 삽입 지점을 `:1438`↔`:1440` 사이로 **[MUST] 고정**. TS-011이 state.json 무변화를 직접 검증 |
| 3 | `gate` 추가가 기존 284 테스트를 깨뜨림 | F-004 | 높음 | `row.get("gate")` 부재 시 즉시 return. Step 8 완료 기준에 "기존 284건 유지"를 명시 |
| 4 | 조건부 산출물(`GC-CONVENTION-*.md`)을 artifacts에 두어 게이트 영구 차단 | F-003 | 높음 | §3.3.2 (2) 적격 규칙으로 **구조적 배제** + `--force --note` 2차 안전망. TS-014가 opdw EXECUTE 무차단을 검증 |
| 5 | SKILL.md 편집 순서 역전(미러 표 선삭제) → 좌표계 소실 | F-005 | 중간 | §3.5.2 ①~⑧ 순서를 각 디스패치 프롬프트에 [MUST]로 전달. Step 완료 기준에 grep AC 명시 |
| 6 | 4개 Step 병렬 편집 중 파일 충돌 | F-005 | 중간 | Batch 5의 파일 집합이 배타적임을 §4.3 R-8에 명시. 동일 파일 2Step 배정 금지 |
| 7 | opwt 동적 key 규약이 `KEY_PATTERN` 위반 | F-005 | 중간 | TS-023이 6종 key를 `add-row` 실호출로 검증. 실패 시 `execute.batch_gate_1` 등 짧은 slug로 대체 |
| 8 | checklist를 list로 실어 hook 주입 무발동 | F-004 | 중간 | `build_gate_payload()`가 **반드시 dict 반환**. TS-018이 실 hook 실행으로 검증 |
| 9 | 신규 저술 게이트(oppd/oppl/opsdd 일부)의 artifacts 파일명 추측 오류 | F-003 | 중간 | **[MUST] 확신 없으면 checklist에 남긴다** 규칙(§3.3.2 (3)). artifacts 승격은 SKILL.md 산출물 절 실측 후에만 |
| 10 | install 후 SKILL.md diff가 변경이력 strip 때문에 불일치로 오판 | F-007 | 낮음 | R-14 AC의 diff 0 대상을 pipeline.json 10건으로 한정 명시(§3.6.2) |
| 11 | 미결-5 hook 확장이 회귀를 유발 | F-004 | 낮음 | Step 9 단일 파일 단독 배치 → 롤백 경계 명확. 되돌려도 R-11/R-12 AC는 stdout만으로 충족 |
| 12 | opd `test_scenario.scenario_gate`가 `*.pm_gate` 네이밍 예외 → 후속 자동화 누락 | F-003 | 낮음 | 게이트 식별을 key 접미가 아니라 `row.get("gate")` 유무로만 수행. §3.4.2 (2)(4) 구현이 이를 보장 |

---

## 부록 A. 미결 5건 결정 요약

| # | 미결 사항 | 결정 | 한 줄 근거 | 탈락안 |
|---|----------|------|----------|--------|
| 1 | artifacts 비-경로 토큰 | **②안 변형** — glob 지원 + `changed_files`·`GC-CONVENTION-*.md`를 checklist로 전치(원문 보존) | 두 토큰 모두 도구가 "부재 = 위반"을 판정할 수 없다(전자는 논리 개념, 후자는 조건부 산출물). 글롭은 opsdd `actions/ACT-*/DONE.md`라는 라이브 소비처가 있어 유지 | ①(090 단순화 역행·재구조 비용) / ③(글롭까지 비차단 시 차단 대상 소멸) |
| 2 | opwt 구조적 공백 | **(b)안** — 정적 7건은 `--task-step`, 동적 4건은 `add-row --key` 규약으로 위임 + 규약 신규 저술 | pipeline.json 스펙에 모드 변형 개념이 없어 (a)는 spec v2 설계가 되고, (c)는 R-4 AC를 구조적으로 포기시킨다 | (a) 범위 초과 / (c) 완료기준 포기 |
| 3 | `gate` 저장 위치 | **(a)안** — init 시 row 복사, `state.json` 영속. `state.schema.json` `rows[].gate` 정식 등록으로 `additionalProperties:false` 해소 | `key`/`conditional`의 직접 확장이며, (b)는 state.json에 spec 경로가 없어 45+ 호출부에 신규 인자 전파를 요구 | (b) 신규 인자 전파·매핑 상수 부담 |
| 4 | `--force` 게이트 우회 | **허용** + 의사결정 로그 강제 기록(`gate_artifact_force` + missing[]) | 기존 가드 2종이 force 우회를 허용하고, `--force`는 `--note` 필수라 이탈에 기록 비용이 부과된다 — 산문 조언과 다른 지점 | 절대 차단(UX 비일관 + 데드락) |
| 5 | checklist 세션 주입 범위 | **확대 채택** — stdout + `todo_mirror_hook.py` 확장 (Step 9 단독 배치) | R-12가 SKILL.md 체크리스트 표를 지우므로 주입이 정보 손실 0의 짝이 된다. 088이 `_extract_payload`를 일반화해 두어 비용이 극소 | stdout까지만(076이 hook을 도입한 전제가 재현됨) |

## 부록 B. TASK.md 대비 범위·수치 변경

| # | 항목 | TASK.md | 본 PLAN | 성격 |
|---|------|---------|---------|------|
| 1 | R-4 전환 대상 | 46건 | **45건** (변경이력 1건 제외) | 수치 정정 (실측 재확인) |
| 2 | R-5 AC 기준 | "`행 [0-9]+` grep 0건" | **변경이력 제외 36건 → 0건** | AC 명확화 (변경이력 불변 원칙 정합) |
| 3 | R-9 미보유 6종 | 일괄 "SKILL.md 표에서 이관" | **3그룹 분리** — opgc 제외 / oppd·oppl 신규 저술 / opwt·opsdd·opdd 이관(+opsdd 2·opwt 1 부족분 저술) | 범위 세분화 |
| 4 | R-9 AC(b) 제거 대상 | "최상위 `pm_gate` 잔존 0건" | 실제 제거 대상 **4파일** (6종은 키 자체가 부재 — ANALYSIS §4-3의 "9종은 최소 `[]`" 서술은 실측과 불일치) | 사실 정정 |
| 5 | R-10 본체 | "스키마 신설" | `validate_pipeline_spec()` **Python 함수가 집행 본체**, `.schema.json` 2건은 비집행 문서 동기화 | 작업량 산정 정정 |
| 6 | artifacts 정제 | `changed_files`만 미확정 | `GC-CONVENTION-*.md`도 **조건부 산출물**로 판명되어 함께 checklist 전치 | **범위 확대(설계 판단)** |
| 7 | 세션 주입 | C-3 "stdout 주입"까지 | `todo_mirror_hook.py` 확장 포함 | **범위 확대(설계 판단)** |
| 8 | Phase 물리 순서 | 정정→key→중복제거→게이트승격 | **게이트 데이터(Phase 2)를 SKILL.md 편집(Phase 4)보다 먼저** 배치 (논리 순서는 파일 내 편집 순서로 보존) | 실행 순서 재배치 |
| 9 | 후속 이월 | — | **opwt pipeline.json 3모드 반영**을 별도 태스크로 이월 | 범위 축소(명시적 이월) |
