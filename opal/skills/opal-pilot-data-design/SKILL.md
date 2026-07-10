---
name: opal-pilot-data-design
description: |
  **DB 설계 파이프라인 오케스트레이터**. 데이터 사전 확립 → 모델링(개념/논리/물리) → DDL/마이그레이션 생성을 6단계 파이프라인으로 수행한다.
  반드시 이 스킬을 사용해야 하는 상황: "opal-pilot-data-design", "opdd", 데이터 설계, DB 설계, 데이터 모델링 파이프라인.
  기획서·기존 ERD·사전·ORM 코드를 인풋으로 받아 표준사전 확립 → ERD 3모드 → DDL까지 완주한다.
  단계 스킬 단독 호출(`//erm` = op-data-model 단독 등) 또는 단편적 설계 작업은 이 스킬이 아니다.
version: 1.0
---

# DB 설계 오케스트레이터

## Harness

모드: Full Task (TASK → DICT → MODEL → DDL/MIGRATION → QA → CLOSE)

> 부트스트랩에서 로드되지 않은 경우: `~/.opal/references/opal-harness.md`를 Read한다.

**[MUST]** 스킬 시작 즉시 모드에 따라 서브 하네스를 Read한다. 이 단계를 건너뛰면 안 된다:
- `--interactive` 플래그 → `~/.opal/references/opal-harness-interactive.md`를 Read한다
- `--agentic` 플래그 → `~/.opal/references/opal-harness-agentic.md`를 Read한다
- 모드 플래그 없음 (기본) 또는 `--semi-agentic` → `~/.opal/references/opal-harness-semi-agentic.md`를 Read한다
- 다중 모드 플래그 동시 사용 시 즉시 사용자에게 보고 + state init도 거부 (`mode_flag_conflict`)

> **[MUST]** 산출물 작성·검증 시 `opal/core/references/harness/citation-rules.md`를 Read하여 규칙(근거 제시 원칙 / 트랙별 매트릭스 / [MUST] 토큰 / 영역 간 용어 일관성 / decision_required 계약)을 준수한다.

---

## STEP 1: TASK

오케스트레이터가 **직접 수행**한다. interview 스킬 호출 + opdd 전용 컨텍스트 수집.

### 경로 자동 감지 (opwt 패턴 계승)

**[MUST]** `docs/PROJECT.md`로 기존 구조 파악 → 없으면 default 트리 제안 → `PROJECT.md`에 기록한다. 사용자가 다른 컨벤션을 원하면 자유 입력 허용.

**3분기 자동 감지** (`opal/skills/opal-pilot-write-tech/SKILL.md` Q6 패턴 계승):

1. `docs/PROJECT.md`에 `{설계}` 루트가 등록되어 있음 → 등록 경로 사용
2. 프로젝트 루트에 `200.설계/` 폴더가 이미 존재 → 감지된 경로 사용
3. 둘 다 없음 → **default 트리 제안** + 직접 입력 허용

**Default 트리** (opwt `100.기획/` prefix 계승, `XXX.{이름}/` + 10 간격):

```
200.설계/
├── 210.사전/          ← md SSOT 3종 + xlsx 뷰
├── 220.개념모델링/    ← ERD_{영역}.mermaid + .md
├── 230.논리모델링/    ← ERD_{영역}_논리.mermaid + .md
├── 240.물리모델링/    ← {프로젝트}.dbml
└── 250.DDL/           ← DDL 스크립트 + 마이그레이션
```

**확정 후 TASK.md "산출물 저장 경로" 섹션에 기록, `docs/PROJECT.md`에 `{설계}` 루트로 등록한다.**

### 인풋 컨텍스트 주입 (`docs/proposals/opal-data-design.md §3.3` 준수)

TASK 단계에서 다음을 자동 감지·주입한다:

| 인풋 | 감지 경로 | 처리 |
|------|----------|------|
| 기획서 | `docs/PRD.md`·`docs/SERVICE.md`·정책서·IA (존재 시) | 엔티티·용어 추출 근거 |
| 사용자 대화·지시 | interview 스킬 | 범위·제약·대상 DBMS 확정 |
| 기존 ERD | `docs/db/`·`docs/erd/` (존재 시) | MODEL 베이스라인(증분 설계) |
| 기존 데이터 사전 | 사용자 지정 경로·`docs/` (존재 시) | DICT 베이스라인 |
| 기존 ORM | `models/`·`migrations/` code-scan (존재 시) | 현행 스키마 역추적, 마이그레이션 정합 |

> 인풋 부재 시: 기획서/대화에서 신규 도출, 사전은 `naming-convention.md` 기본 규칙 폴백.

### 완료 처리

- TASK.md 작성 (인터뷰 결과 + 인풋 컨텍스트 + `{설계}` 경로 포함)
- STATE.md 초기화:
  ```
  ~/.opal/tools/state-tool/run.sh init <task-path> --skill opdd --mode <interactive|semi-agentic|agentic> --rows-from opal/skills/opal-pilot-data-design/SKILL.md
  ```
- 행 갱신:
  ```
  ~/.opal/tools/state-tool/run.sh advance <task-path> --row 1
  ~/.opal/tools/state-tool/run.sh mark <task-path> --row 1 --done
  ```
- 사용자 보고 → 사용자 확인 행 mark:
  ```
  ~/.opal/tools/state-tool/run.sh mark <task-path> --row 2 --done --owner user --note '{owner_name} 확인: TASK 완료'
  ```

---

## STEP 2: DICT

**[MUST]** `docs/proposals/opal-data-design.md §3.2`: "DICT가 MODEL을 **선행**한다 — 표준사전·코드가 논리/물리 모델링의 속성명·타입을 결정하는 SSOT이기 때문."

`opal-db-agent` 단일 에이전트에 op-data-dictionary 스킬을 디스패치한다 (`docs/proposals/opal-data-design.md §3.1` 단일 도메인 원칙).

**디스패치 프롬프트**:
```
[WORKER]
op-data-dictionary 스킬을 수행하라.
**스킬 경로**: {op-data-dictionary/SKILL.md 탐색 경로}
**태스크 폴더**: {tasks/{NNN}-{name}/}
**이전 산출물**: {TASK.md 경로}
**{설계} 루트**: {PROJECT.md에서 확정된 설계 산출물 루트 경로}
**사전 저장 경로**: {{설계}/210.사전/ 또는 PROJECT.md 등록 경로}
**모드**: 신규 작성 또는 검증·보강 (기존 사전 주입 여부에 따라 자동 분기)
**하네스 Guards**: PLAN.md에 없는 파일 생성/수정 금지. 블로커 발생 시 즉시 중단 후 보고.
```
**model**: standard

워커 완료
  → **PM Gate** (사전 3종 내용·SSOT 정합 검토)
  → 사용자 보고 후 사용자 확인:
  ```
  ~/.opal/tools/state-tool/run.sh mark <task-path> --row 4 --done   # DICT PM Gate
  ~/.opal/tools/state-tool/run.sh mark <task-path> --row 5 --done --owner user --note '{owner_name} 확인: 사전 확정'
  ```

---

## STEP 3: MODEL

**[MUST]** `docs/proposals/opal-data-design.md §3.2`: "DDL/MIGRATION은 MODEL의 물리(DBML) 산출 이후에만 실행 가능(캡틴 명시). state-tool stage-transition guard가 자동 차단."

`opal-db-agent` 단일 에이전트에 op-data-model 스킬을 디스패치한다. pilot은 **3모드 순차 실행** (개념 → 논리 → 물리).

**디스패치 프롬프트**:
```
[WORKER]
op-data-model 스킬을 수행하라.
**스킬 경로**: {op-data-model/SKILL.md 탐색 경로}
**태스크 폴더**: {tasks/{NNN}-{name}/}
**이전 산출물**: {TASK.md 경로}, {DICT 산출물 경로 — 사전 3종}
**{설계} 루트**: {PROJECT.md에서 확정된 설계 산출물 루트 경로}
**실행 순서**: concept → logical → physical (순차, 이전 모드 산출물이 다음 모드 입력)
**속성명 SSOT**: {설계}/사전/표준단어사전.md (논리/물리 모드에서 DICT 사전 기반 필수)
**하네스 Guards**: PLAN.md에 없는 파일 생성/수정 금지. 블로커 발생 시 즉시 중단 후 보고.
```
**model**: standard

워커 완료
  → **PM Gate** (개념·논리·물리 ERD 정합·DICT 사전 용어 정합 검토)
  → 사용자 보고 후 사용자 확인:
  ```
  ~/.opal/tools/state-tool/run.sh mark <task-path> --row 7 --done   # MODEL PM Gate
  ~/.opal/tools/state-tool/run.sh mark <task-path> --row 8 --done --owner user --note '{owner_name} 확인: 모델링 확정'
  ```

> **모드 경계 (U-5)**: MODEL 사용자 확인 행(행 8) 통과 후부터 DDL·QA·CLOSE 직전까지 PM 자율. DICT·MODEL은 설계 SSOT 확정 단계이므로 사용자 검토 필수. 행 8 이후는 기계적 추출 단계 — PM 자율 적합. (`opal/skills/opal-pilot-dev/SKILL.md:313-314` 모드 경계 패턴 계승)

---

## STEP 4: DDL/MIGRATION

**[MUST]** `docs/proposals/opal-data-design.md §3.2`: "DDL/MIGRATION은 MODEL의 물리(DBML) 산출 이후에만 실행 가능." — 물리 모드(DBML) 산출물이 없으면 이 단계를 시작하지 않는다.

`opal-db-agent` 단일 에이전트에 op-data-ddl 스킬을 디스패치한다.

**디스패치 프롬프트**:
```
[WORKER]
op-data-ddl 스킬을 수행하라.
**스킬 경로**: {op-data-ddl/SKILL.md 탐색 경로}
**태스크 폴더**: {tasks/{NNN}-{name}/}
**이전 산출물**: {물리 모델링 DBML 경로 — 필수 입력}, {DICT 사전 경로}
**{설계} 루트**: {PROJECT.md에서 확정된 설계 산출물 루트 경로}
**DDL 저장 경로**: {{설계}/250.DDL/}
**대상 DBMS**: {TASK.md에서 확정된 DBMS — MySQL/PostgreSQL/MSSQL 등}
**하네스 Guards**: 물리 DBML 없이 DDL 생성 금지. 블로커 발생 시 즉시 중단 후 보고.
```
**model**: standard

워커 완료 (PM 자율)
  → PM Gate (DDL/마이그레이션 내용·명명규칙·제약 검토)
  → 행 mark:
  ```
  ~/.opal/tools/state-tool/run.sh mark <task-path> --row 9 --done   # DDL 작업
  ~/.opal/tools/state-tool/run.sh mark <task-path> --row 10 --done  # DDL PM Gate
  ~/.opal/tools/state-tool/run.sh mark <task-path> --row 11 --done --owner user --note '{owner_name} 확인: DDL 확정'
  ```

---

## STEP 5: QA

PM Gate — QA 검증 항목 직접 수행 (`docs/proposals/opal-data-design.md §3.4` 준수).

**QA 검증 항목**:
- [ ] 단계 간 정합: 개념 ERD ↔ 논리 ↔ 물리 (엔티티/관계 보존)
- [ ] 사전 정합: 모든 컬럼명이 DICT 표준사전 등록 용어 (미등록 0)
- [ ] 기획 정합: 기획서 엔티티 ↔ ERD 누락 0 (citation-rules §7 영역 간 일관성)
- [ ] DDL 검증: 물리 DBML ↔ DDL 일치, 명명규칙(`PK_`/`FK_`/`UQ_`/`IDX_`) 준수

QA 통과 시:
```
~/.opal/tools/state-tool/run.sh mark <task-path> --row 12 --done  # QA 작업
~/.opal/tools/state-tool/run.sh mark <task-path> --row 13 --done  # QA PM Gate
~/.opal/tools/state-tool/run.sh mark <task-path> --row 14 --done --owner user --note '{owner_name} 확인: QA 통과'
```

---

## STEP 6: CLOSE

모든 체크리스트 갱신 완료 확인 후 태스크를 마감한다.

1. DONE.md 생성 후 행 mark:
   ```
   ~/.opal/tools/state-tool/run.sh mark <task-path> --row 15 --done
   ```
2. **관련 문서 업데이트** (op-brain-ingest 디스패치 직전 실행):
   - `<프로젝트-루트>/docs/PROJECT.md`의 "프로젝트 문서" 레지스트리와 이번 태스크의 `changed_files`(EXECUTE 산출)를 양쪽 종합하여, 태스크 결과로 내용이 달라진 관련 문서(ARCHITECTURE.md·표준사전·ERD 등)를 식별한다.
   - 갱신 대상이 있으면 PM이 판단하여 직접 수정하거나 적합한 워커를 디스패치해 최신화한다. 갱신 대상이 없으면 자연 스킵(no-op) — CLOSE를 중단시키지 않는다.
   - 목적: brain ingest 이전에 기획·설계 문서를 최신 상태로 만들어 ingest 품질을 보장한다.
3. **op-brain-ingest 디스패치** (DONE.md 생성 직후 실행):
   - `<프로젝트-루트>/.opal/brain/` 존재 여부를 확인한다.
   - **brain이 존재하면**: op-brain-ingest 워커를 디스패치하여 태스크 산출물(DONE.md·사전·ERD·DDL)을 brain에 누적한다.
   - **brain이 없으면**: 자연 스킵(no-op). CLOSE가 막히지 않는다.
   - op-brain-ingest 탐색 경로:
     1. `{프로젝트}/.opal/skills/op-brain-ingest/SKILL.md`
     2. `~/.opal/skills/op-brain-ingest/SKILL.md`
   - 어떤 status(skipped/completed/completed_with_errors)도 CLOSE를 중단시키지 않는다.
4. 완료 보고:
   ```
   [CLOSE] 태스크 완료
   산출물: tasks/{NNN}-{태스크명}/DONE.md
   태스크가 완료되었습니다.
   ```

> **CLOSE 진입 게이트**: CLOSE 단계 첫 행 mark 시 도구가 직전 단계 사용자 확인 행의 `owner=user` 여부를 자동 검증한다 (§2.16 G-13). agentic 모드의 `--auto-pass`도 거부됨.

---

## STATE.md 도메인 치환값

| 필드 | 값 |
|------|------|
| 모드 | Full Task |
| 단계 목록 | TASK / DICT / MODEL / DDL/MIGRATION / QA / CLOSE |

**진행 현황 행 예시** (아래 표는 `state init --rows-from <SKILL.md>` 또는 `--rows-spec` 인자의 SSOT — LLM이 직접 작성하는 것은 금지된다):

> **[MUST] STATE.md 초기 생성**: `~/.opal/tools/state-tool/run.sh init <task-path> --skill opdd --mode <interactive|semi-agentic|agentic> --rows-from <SKILL.md 경로>` 호출. 기본값: `semi-agentic`. `--rows-from`이 아래 표를 파싱하여 행 구성을 자동 추출한다.
> 근거: `docs/proposals/opal-data-design.md §3.5` STATE 행 15행 구성 / `opal/skills/opal-pilot-dev/SKILL.md:266-289` D-5 패턴 계승

```markdown
| # | 단계 | 항목 | 상태 | 시점 |
|---|------|------|------|------|
| 1 | TASK | 작업 | ⬜ | - |
| 2 | TASK | 사용자 확인 | ⬜ | - |
| 3 | DICT | 작업 | ⬜ | - |
| 4 | DICT | PM Gate | ⬜ | - |
| 5 | DICT | 사용자 확인 | ⬜ | - |
| 6 | MODEL | 작업 | ⬜ | - |
| 7 | MODEL | PM Gate | ⬜ | - |
| 8 | MODEL | 사용자 확인 | ⬜ | - |
| 9 | DDL/MIGRATION | 작업 | ⬜ | - |
| 10 | DDL/MIGRATION | PM Gate | ⬜ | - |
| 11 | DDL/MIGRATION | 사용자 확인 | ⬜ | - |
| 12 | QA | 작업 | ⬜ | - |
| 13 | QA | PM Gate | ⬜ | - |
| 14 | QA | 사용자 확인 | ⬜ | - |
| 15 | CLOSE | DONE.md 생성 | ⬜ | - |
```

> 행 8(MODEL 사용자 확인) 이후부터 PM 자율 — 모드 경계(U-5 확정). CLOSE 진입은 사용자 승인 필수(공통).

---

## PM Gate 점검 목록

| Phase | 산출물 | 체크리스트 |
|-------|-------|----------|
| TASK | TASK.md | `{설계}` 루트 확정, 인풋 컨텍스트 수집 완료, DBMS 확정 |
| DICT | `{설계}/사전/` 3종 md | 표준단어·도메인·코드사전 존재, md SSOT 규칙 준수, xlsx export 선택 여부 |
| MODEL | `{설계}/개념·논리·물리` 모델링 | 3모드 순차 완료, 논리 속성명 = DICT 용어, 물리 DBML 존재 |
| DDL/MIGRATION | `{설계}/DDL/` | DDL 스크립트 + 마이그레이션, 물리 DBML 기반 생성 확인 |
| QA | 전체 산출물 | `docs/proposals/opal-data-design.md §3.4` 4개 검증 항목 PASS |

---

## Agentic / Semi-Agentic 모드

opal-harness-agentic.md / opal-harness-semi-agentic.md 참조. 본 절은 이 스킬의 차이점만 기술한다.

### 기본 모드 (semi-agentic)

기본 호출(`//opdd {작업}`)은 semi-agentic 모드.

**모드 경계** (이 시점부터 PM 자율):
- MODEL 사용자 확인 행(행 8) 통과 후 → DDL·QA 행부터 PM 자율 (`opal/skills/opal-pilot-dev/SKILL.md:313-314` 패턴 계승 — 본 파이프라인에서 MODEL이 설계 SSOT 확정의 최종 사용자 게이트)

### 명시 모드

| 호출 | 모드 |
|------|------|
| `//opdd 작업` | semi-agentic (기본) |
| `//opdd --interactive 작업` | interactive — 모든 단계 사용자 승인 |
| `//opdd --agentic 작업` | agentic — 모든 단계 PM 자율 (CLOSE 진입 제외) |

### 자율 게이트 흐름 (semi-agentic)

```
TASK → DICT Gate → MODEL Gate → DDL Gate → QA Gate → CLOSE
사용자   사용자 승인    사용자 승인    PM 자율     PM 자율    사용자 승인 필수
                       (모드 경계 — 행 8)
```

- TASK→DICT Gate→MODEL Gate까지 사용자 승인 필수
- MODEL 사용자 확인(행 8) 통과 후 DDL·QA Gate는 PM 자율 통과
- CLOSE 진입은 사용자 승인 필수 (공통 게이트)

### CLOSE 진입 게이트 (공통)

semi-agentic / agentic 모두 CLOSE 첫 행 `--auto-pass` 거부 (`agentic_close_gate_requires_user`). 소유자 발화 후 직전 사용자 확인 행 `--owner user` mark 필수.

---

## 변경이력

| 버전 | 날짜 | 변경 내용 |
|------|------|---------|
| v1.0 | 2026-06-12 | 초기 작성 — opal-pilot-data-design(opdd) 오케스트레이터 신설. 파이프라인 6단계(TASK/DICT/MODEL/DDL·MIGRATION/QA/CLOSE), STATE 15행, 모드경계 행 8, DDL 물리 의존, opal-db-agent 단일 디스패치 (019) |
| v1.1 | 2026-06-24 | CLOSE 단계 op-brain-ingest 디스패치 직전에 "관련 문서 업데이트" 스텝 삽입 — PROJECT.md 레지스트리 + changed_files 종합으로 관련 문서 최신화 후 ingest (없으면 no-op). 후속 항목 번호 재정렬 (042) |
| v1.2 | 2026-07-10 13:12 | note 예시의 소유자 확인 표기를 `{owner_name} 확인:` 형식으로 통일 — identity.md owner_name 재해석 규칙(AGENT.md §정체성 적용)과 정합, 오염 차단 (054) |
