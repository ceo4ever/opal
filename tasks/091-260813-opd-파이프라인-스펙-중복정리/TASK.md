# TASK: 파이프라인 스펙 중복정리 — SKILL.md 감량 + PM Gate SSOT 승격

> 작성일: 2026-08-13 | 작업 유형: 개선 | 적용 스킬: opd | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

pipeline.json이 행 구성 SSOT가 된 상태(090)에서 pilot 10종 SKILL.md에 남은 중복·구형 지시를 제거하고, PM Gate 정의를 pipeline.json으로 승격하여 `state-tool`이 이를 실제로 소비(checklist 주입 + artifacts 존재 차단)하게 한다.

## 배경

090이 10/10 pilot의 행 구성을 `references/pipeline.json`으로 이관했으나, 이관 범위를 "행 구성 + registry 정합"으로 한정했다(D-1). 그 결과 SKILL.md에는 새 SSOT와 중복되거나 구형 좌표계를 쓰는 서술이 그대로 남았고, 090 DONE.md §8이 이월 4건(실행 스펙 필드 승격·`pm_gate` 정리·SKILL.md 감량·ANALYSIS PM Gate 제거)을 명시했다.

현재 상태의 문제는 세 층이다.

- **중복**: 미러 표 134행이 `task_steps[]`와 100% 동일한데 어느 도구도 읽지 않는다.
- **구형 좌표**: `--row N` 46건이 `docs/CONVENTIONS.md` §State 관리의 금지 규칙을 위반한 채 남아 있다.
- **미배선 SSOT**: `pm_gate`는 스키마에 정의됐지만 `state_tool.py`가 읽지도 검증하지도 않는다 — 두 곳에 정의가 갈라진 채 드리프트가 이미 발생했다.

## 배경 분석 (대화에서 도출)

스킬 호출 전 대화에서 pilot 10종 SKILL.md × pipeline.json 10종을 실측 대조했다.

### 1. 미러 표 — 전량 중복, 소비처 0

| 항목 | 실측 |
|------|------|
| 대조 결과 | 10/10 pilot에서 미러 표 ↔ `task_steps[]`의 `(id, stage, item)` 완전 일치 |
| 총량 | 134행 (opsdd 25 / oppl 19 / opd 16 / opdd 15 / oppd 13 / opds 11 / opwt 10 / opp 9 / opdw 9 / opgc 7) |
| 소비 코드 | 없음 — `state_tool.py`는 `spec_version`·`skill`·`meta`·`task_steps`만 읽는다 |
| 보호 장치 | "편집 금지" 주석뿐. 드리프트를 검출하는 도구 게이트 없음 |

### 2. 구형 좌표계 잔존 — `--row N` 46건 / 산문 `행 N` 49건

| pilot | `--row N` | 비고 |
|-------|-----------|------|
| opdd | 14 | 070 key 전환 대상에서 제외돼 있었음 |
| opwt | 11 | 동일 |
| opsdd | 10 | 동일 |
| oppd | 5 | 090에서 신설된 미러 표와 함께 유입 |
| oppl | 4 | 동일 |
| opgc | 2 | 동일 |
| opd·opds·opdw·opp | 0 | 070에서 `--task-step` 전환 완료 |

산문 `행 N` 리터럴은 10종 합계 49건이다. 두 값 모두 미러 표를 좌표계로 전제하므로, 표만 먼저 삭제하면 95건이 해석 불능이 된다.

### 3. PM Gate 정의 — 두 곳에 갈라진 채 이미 드리프트

`pm_gate` 보유는 4종(opd 4·opds 2·opdw 2·opp 2 항목)이고 나머지 6종은 없다. `state_tool.py`는 `pm_gate`를 **읽지도 검증하지도 않는다**(`validate_pipeline_spec()` 미포함).

| pilot | 드리프트 실측 |
|-------|-------------|
| opd | `TEST-SCENARIO` ⑥항 — SKILL.md "L3 [SUPERVISOR] 마커 **+ PM 요청 양식**" vs pipeline.json "L3 [SUPERVISOR] 마커" (항목 누락) |
| opdw | 2행 — SKILL.md "op-dev-qa/SKILL.md 검증 기준 **참조**" vs pipeline.json 축약형 (표현 불일치) |
| opds·opp | 현재 일치 |

`artifacts` 토큰 전수는 7종이며, 이 중 3종은 단순 파일 존재 검증이 성립하지 않는다.

| 토큰 | 검증 가능성 |
|------|-----------|
| `TASK.md` · `PLAN.md` · `ANALYSIS.md` · `TEST-SCENARIO.md` · `wireframe.md` | 태스크 폴더 기준 경로 — 존재 검증 가능 |
| `GC-CONVENTION-*.md` | glob 패턴 — 매칭 규칙 필요 |
| `changed_files` | 파일명이 아닌 논리 개념(EXECUTE 변경 파일 집합) — 경로 검증 대상 아님 |

### 4. 090이 남긴 자기모순 문장 2지점

| 위치 | 현재 서술 | 실제 |
|------|----------|------|
| `opal/skills/opal-pilot-data-design/SKILL.md:241` | "`--rows-from`이 **아래 표를 파싱**하여 행 구성을 자동 추출한다" | 명령 경로는 `pipeline.json` — 문장만 구형 |
| `opal/skills/opal-pilot-sdd/SKILL.md:386`·`:399` | "**위 SSOT 표를 기준으로** state-tool이 생성" | SSOT는 `pipeline.json` |

### 5. 상위 규칙이 아직 미러 표를 의무화 중

| 위치 | 서술 |
|------|------|
| `opal/core/references/harness/state-template.md:94` | "오케스트레이터 SKILL.md 'STATE.md 도메인 치환값'에 해당 스킬의 파이프라인 현황판 **행 예시가 명시됨**" |
| `opal/core/references/harness/qa-standards.md:46` | 동일 섹션을 산출물 오버라이드 근거로 참조 |

이 2줄을 먼저 정정하지 않고 표를 삭제하면 하네스 기준으로는 결함 상태가 된다.

### 6. 부수 중복

- `## STATE.md 도메인 치환값`의 모드·단계 목록이 `meta.mode_label`+`meta.stages`와 중복이며, 표기 형식도 3가지(표 6종 / 불릿 / 혼합)로 갈렸다.
- 동일 `init` 명령 중복 게재 — opgc 3회, opwt 3회, opdd·opdw·oppl·opsdd 각 2회.
- `## Agentic / Semi-Agentic 모드`는 "차이점만 기술한다"고 선언한 뒤 공통 규칙을 재서술한다 — 9개 파일 동일 문장 1건, 8개 동일 2건, 5개 동일 4건.

## 확정된 설계 방향 (대화에서 합의)

| # | 확정 사항 | 근거 |
|---|----------|------|
| C-1 | PM Gate 정의의 SSOT는 **pipeline.json**이며, SKILL.md `## PM Gate 점검 목록` 표를 제거한다 | 캡틴 확정 — 행 구성을 단일화한 근거가 게이트 정의에도 동일하게 적용된다 |
| C-2 | 배치는 최상위 `pm_gate[]`가 아니라 **`task_steps[].gate` 인라인** | 게이트 행이 이미 `plan.pm_gate` key 주소를 가지며, stage 단위는 한 stage에 PM Gate 행이 둘 이상인 비표준 구조(opsdd 25행·oppl 19행)에서 대응 불가 |
| C-3 | 집행 강도는 **주입 + 산출물 차단** — checklist는 `mark` 시 stdout 주입, artifacts는 존재 검증 후 미충족 시 mark 거부 | 캡틴 선택. 판단 영역(checklist)은 도구가 판정 불가하므로 주입, 결정론 판정 가능한 지점(artifacts)만 차단하여 헌법 "Enforce, don't just advise"를 성립 가능한 범위에 적용 |
| C-4 | 작업 범위는 **4 Phase 전체 한 태스크** — 오문장 정정 → key 전환 → 미러 표 제거 → 게이트 SSOT 승격 | 캡틴 선택. Phase 간 순서 의존이 있어 분할 시 중간 상태에서 문서가 해석 불능이 된다 |
| C-5 | 파일럿은 **opd(Full Task) / agentic** | `state_tool.py` `mark` 경로에 088·076·017이 이미 얹혀 있어 회귀 표면 파악에 ANALYSIS 단계가 필요하다 |
| C-6 | SKILL.md에는 PM Gate **절차·판정 기준 산문을 남긴다** | pipeline.json이 가질 것은 산출물·체크리스트 목록이지 수행 방법이 아니다 |

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | pilot 10종 SKILL.md에서 pipeline.json과 중복·구형인 서술을 제거하고, PM Gate 정의를 `task_steps[].gate`로 승격하여 state-tool이 checklist 주입 + artifacts 존재 차단으로 소비하게 한다 | - | 090 DONE.md §8 이월 4건 |
| 범위 | **포함** — pilot SKILL.md 10종, pipeline.json 10종, `state_tool.py`, `pipeline-spec.schema.json`, `harness/state-template.md`, `harness/qa-standards.md`, 영향받는 `docs/` 규칙 문서. **제외** — opsdd 산문 `EXECUTE-LOOP` 표기(090 D-7c 확정), 변경이력 표, `> 근거:` 인용줄(줄번호 오류 정정은 포함), `## Agentic / Semi-Agentic 모드` 절 통합(별도 태스크) | - | 090 D-7c / citation-rules §1 |
| 제약 | (a) 전후 동등 — 10 pilot × 2 mode init 행 구성 불변 (b) 배포 경계 — 프로젝트 소스 수정 후 install 재배포, `~/.opal/` 직접 편집 금지 (c) 변경이력 행 추가 의무 (d) 기존 태스크 폴더의 state.json 소급 변경 금지 (e) `--rows-spec` 경로 존치 | **artifacts 비-경로 토큰 3종(`GC-CONVENTION-*.md` glob / `changed_files` 논리 개념) 처리 방식** — PLAN에서 결정 | `.opal/AGENT.md` §금지사항 / 배경 분석 §3 |
| 완료기준 | R-1~R-12 AC 전건 충족 + TEST-SCENARIO 전 시나리오 Pass + 목표-커버 게이트 `verdict: pass` | - | opd pipeline.json `test_scenario.scenario_gate` |

## 요구사항

### Phase 1 — 정정 (선행)

- [ ] **R-1** 자기모순 문장 정정
  - 무엇을: "아래 표를 파싱" / "위 SSOT 표를 기준으로" 서술을 pipeline.json 기준으로 교체
  - 어디에: `opal/skills/opal-pilot-data-design/SKILL.md:241`, `opal/skills/opal-pilot-sdd/SKILL.md:386`·`:399`
  - 왜: 배경 분석 §4 — 명령 경로와 설명이 서로 다른 원천을 가리킨다
  - AC: 레포 전역에서 `표를 파싱`·`SSOT 표를 기준` 패턴 grep **0건**이고, 각 지점이 `references/pipeline.json`을 원천으로 서술한다

- [ ] **R-2** 상위 규칙의 미러 표 의무 해제
  - 무엇을: 미러 표 존재를 전제한 서술을 pipeline.json 기준으로 교체
  - 어디에: `opal/core/references/harness/state-template.md:94`, `opal/core/references/harness/qa-standards.md:46`
  - 왜: 배경 분석 §5 — 이 규칙이 살아 있으면 표 삭제가 하네스 결함으로 판정된다
  - AC: 두 파일에서 "SKILL.md에 행 예시가 명시됨" 취지의 서술이 0건이고, 행 원천을 `references/pipeline.json`으로 지시한다

- [ ] **R-3** 줄번호 인용 오류 정정
  - 무엇을: 이미 어긋난 줄번호 인용을 섹션 참조로 교체
  - 어디에: `opal/skills/opal-pilot-data-design/SKILL.md:242`(`opal-pilot-dev/SKILL.md:266-289` → 실제 282-306)
  - 왜: citation-rules §2.2 — 줄번호 인용은 대상 이동 시 무효화된다
  - AC: pilot SKILL.md 내 타 SKILL.md 줄번호 인용이 0건이거나, 남은 인용이 실제 줄 범위와 일치한다

### Phase 2 — 좌표계 전환 (미러 표 삭제의 선행 조건)

- [ ] **R-4** `--row N` → `--task-step <key>` 전환
  - 무엇을: 명령 예시의 행 번호 주소를 key 주소로 교체
  - 어디에: opdd 14 / opwt 11 / opsdd 10 / oppd 5 / oppl 4 / opgc 2 = **46건**
  - 왜: `docs/CONVENTIONS.md:228` — "`--row`는 deprecated 별칭(신규 문서·프롬프트에 사용 금지)"
  - AC: (a) **구형 잔존 0** — 변경이력 행을 제외한 pilot SKILL.md에서 `--row ` grep 0건 (b) **신형 채택** — 교체된 key 46건이 전부 해당 pipeline.json `task_steps[].key`에 실재하고, 대표 3종에서 `--task-step` 실호출이 exit 0

- [ ] **R-5** 산문 `행 N` 참조 → key 참조 전환
  - 무엇을: 산문의 행 번호 리터럴을 key 또는 항목명 참조로 교체
  - 어디에: pilot SKILL.md 10종 합계 **49건**
  - 왜: 배경 분석 §2 — 미러 표 없이 해석 가능해야 표를 삭제할 수 있다
  - AC: 미러 표 삭제 후에도 산문의 모든 행 참조가 pipeline.json만으로 해석 가능하고, `행 [0-9]+` grep이 0건이거나 잔존분이 pipeline.json key를 병기한다

### Phase 3 — 중복 제거

- [ ] **R-6** 미러 표 삭제
  - 무엇을: 파이프라인 현황판 미러 표 제거 + 원천 포인터 1줄로 교체
  - 어디에: pilot SKILL.md 10종, 총 **134행**
  - 왜: 배경 분석 §1 — SSOT도 폴백도 아닌 수동 유지 사본
  - AC: (a) **구형 잔존 0** — 10종에서 `| # | 단계 | 항목 |` 형식 표 0건 (b) **신형 채택** — 10 pilot × 2 mode init 후 `rows[]`의 `(id, stage, item)`이 삭제 전 baseline과 완전 동일

- [ ] **R-7** `STATE.md 도메인 치환값` 정리
  - 무엇을: `meta.mode_label`·`meta.stages`와 중복되는 모드·단계 목록 제거, 스킬 고유값(산출물 목록 등)만 존치
  - 어디에: pilot SKILL.md 10종 (표 6종 / 불릿 / 혼합 3형식)
  - 왜: 배경 분석 §6 — 동일 정보가 두 곳에 있고 표기 형식마저 갈렸다
  - AC: 10종에서 모드·단계 목록 중복 기재 0건이고, 잔존 항목이 pipeline.json에 없는 스킬 고유 정보만 포함한다

- [ ] **R-8** `init` 명령 중복 게재 정리
  - 무엇을: 동일 파일 내 반복된 init 명령을 1지점으로 통합 + 나머지는 참조
  - 어디에: opgc 3 / opwt 3 / opdd·opdw·oppl·opsdd 각 2
  - 왜: 배경 분석 §6 — 한쪽만 갱신되는 드리프트 원천
  - AC: pilot당 `state-tool/run.sh init` 완전 명령이 최대 1회 등장하고, 각 pilot init 실호출이 exit 0

### Phase 4 — PM Gate SSOT 승격

- [ ] **R-9** `task_steps[].gate` 스키마 신설 + 10종 정의 이관
  - 무엇을: `gate: { artifacts, checklist }`를 `task_steps[]` 항목에 인라인 신설, 기존 최상위 `pm_gate[]` 4종을 이관 후 제거, 미보유 6종은 SKILL.md 현행 표에서 이관
  - 어디에: `opal/tools/state-tool/schema/pipeline-spec.schema.json`, pipeline.json 10종
  - 왜: C-1·C-2 — SSOT 단일화 + 비표준 행 구조 대응
  - AC: (a) 10/10 pipeline.json이 게이트 행마다 `gate` 보유 (b) 최상위 `pm_gate` 잔존 0건 (c) 이관 시 SKILL.md 현행 표 대비 항목 누락 0 — opd `TEST-SCENARIO` ⑥ "PM 요청 양식", opdw "참조" 표현 등 드리프트 2건은 SKILL.md 쪽(상세본)을 채택

- [ ] **R-10** `spec-validate` gate 검증 추가
  - 무엇을: `validate_pipeline_spec()`에 `gate` 구조 검증 추가 (필수 키·타입·비어있지 않음)
  - 어디에: `opal/tools/state-tool/state_tool.py`
  - 왜: 배경 분석 §3 — 현재는 오타가 나도 검출되지 않는다
  - AC: `spec-validate` 10/10 `ok:true`이고, 고의 결손 스펙 3종(키 누락·타입 오류·빈 배열)이 전부 위반으로 검출된다

- [ ] **R-11** `mark` 게이트 소비 — checklist 주입 + artifacts 차단
  - 무엇을: `mark --task-step <gate행 key>` 시 (a) artifacts 존재 검증 → 미충족이면 `gate_artifact_missing`으로 거부 (b) 통과 시 stdout에 checklist 반환
  - 어디에: `opal/tools/state-tool/state_tool.py`, `ERROR_CODES`
  - 왜: C-3 — 데이터만 옮기면 집행력이 현재와 동일하다
  - AC: (a) 산출물 부재 상태에서 게이트 행 mark가 `ok:false`·`gate_artifact_missing`·`missing[]` 반환 (b) 존재 시 `ok:true`와 함께 checklist 페이로드 반환 (c) `gate` 미보유 행의 mark 동작은 기존과 바이트 동일 (d) 비-경로 토큰(PLAN 확정안)이 게이트를 영구 차단하지 않음

- [ ] **R-12** SKILL.md `## PM Gate 점검 목록` 표 → 포인터 교체
  - 무엇을: 표를 삭제하고 원천 포인터 + 판정 절차 산문만 존치
  - 어디에: 해당 절 보유 pilot SKILL.md
  - 왜: C-1·C-6
  - AC: (a) **구형 잔존 0** — 게이트 산출물·체크리스트를 나열한 표 0건 (b) **신형 채택** — 각 pilot에서 게이트 행 mark 시 pipeline.json 유래 checklist가 실제로 stdout에 출력됨

### Phase 5 — 회귀·배포

- [ ] **R-13** 전후 동등 및 회귀 무손실
  - 무엇을: 전체 변경 전후 파이프라인 동작 동등성 검증
  - 어디에: 10 pilot × 2 mode
  - 왜: 제약 (a)
  - AC: (a) init `rows[]` 전후 완전 동일 20/20 (b) `advance`/`mark`/`block`/`add-row`/`status` 기존 회귀 전건 통과 (c) 088 메모리 히스토리 연결·076 todo_mirror 페이로드 동작 불변

- [ ] **R-14** 배포 정합
  - 무엇을: install 재배포 후 배포본으로 실동작 확인
  - 어디에: `~/.opal/` 배포 경로
  - 왜: `.opal/AGENT.md` §금지사항 — 배포 경계 준수
  - AC: 배포본 pipeline.json 10건이 소스와 `diff` 0이고, 배포 경로 `state-tool`로 대표 3 pilot init + 게이트 mark 차단이 재현된다

## 제약 조건

- **전후 동등 최우선** — 행 구성·기존 서브명령 동작은 변경 대상이 아니다. 게이트 소비는 **추가 동작**이며 `gate` 미보유 행에는 영향이 없어야 한다.
- **배포 경계** — `~/.opal/` 직접 편집 금지. 프로젝트 소스(`opal/`) 수정 후 install로 재배포한다.
- **소급 변경 금지** — 기존 태스크 폴더의 `state.json`·`STATE.md`는 건드리지 않는다.
- **변경이력 의무** — 수정한 스킬·에이전트·참조 문서마다 변경이력 표에 행을 추가한다(일시 KST + 태스크 번호).
- **`--rows-spec` 존치** — 인라인 JSON 직접 지정 경로는 폐기 대상이 아니다(090 Gate Fail 선례).
- **범위 밖 고정** — opsdd 산문 `EXECUTE-LOOP` 표기 17곳, `## Agentic / Semi-Agentic 모드` 절 통합은 이번 범위가 아니다.
- **미확정 1건** — artifacts 비-경로 토큰 3종 처리 방식은 PLAN에서 결정한다(3안: 스키마 타입 분리 / glob만 지원하고 `changed_files`는 checklist 강등 / 비-경로 토큰 비차단 통과).

## 기술 스택

- Markdown (pilot SKILL.md, 하네스 참조 문서)
- JSON (pipeline.json 10종, JSON Schema draft-07)
- Python 3 (`opal/tools/state-tool/state_tool.py`)
- Bash (`run.sh` 래퍼, install 스크립트)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | 090 DONE.md | `tasks/090-260813-opds-파이프라인-스펙-마이그레이션/DONE.md` | 이월 4건(D-1·D-3·D-5·D-6)의 원 출처, 전환 baseline |
| D-2 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | §State 관리 — 행 원천 규칙, `--row` deprecated 규정 |
| D-3 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py` | `validate_pipeline_spec()`·`build_rows_from_pipeline_json()`·`cmd_mark` 변경 대상 |
| D-4 | 설계 | pipeline-spec.schema.json | `opal/tools/state-tool/schema/pipeline-spec.schema.json` | `gate` 인라인 신설 대상 |
| D-5 | 설계 | state-template.md | `opal/core/references/harness/state-template.md` | 미러 표 의무 서술(:94) 정정 대상 |
| D-6 | 설계 | qa-standards.md | `opal/core/references/harness/qa-standards.md` | 도메인 치환값 절 참조(:46) 정정 대상 |
| D-7 | 설계 | PM 프로필 | `.opal/AGENT.md` | 배포 경계·변경이력·하네스 우회 금지 |
| D-8 | 설계 | pilot SKILL.md 10종 | `opal/skills/opal-pilot-*/SKILL.md` | 감량 대상 본체 |
