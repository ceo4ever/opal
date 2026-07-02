# PLAN: `[ASSISTANT]` 마커로 headless(claude -p) 호출을 비서 tier로 캡

> 작성일: 2026-07-02
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사

### 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | AGENT.md (부트스트랩 SSOT) | `opal/core/AGENT.md` | Phase A/B 게이트·WORKER 규칙·완료보고·변경이력 — 직접 수정 대상 |
| D-2 | 소스 | opbr_adapter.py | `dashboard/backend/adapters/opbr_adapter.py` | claude -p 첫 소비자 — 프롬프트 프리픽스+docstring 대상 |
| D-3 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | 산출물 인용 규칙 (근거주의 하네스) |
| D-4 | 설계 | op-task-plan SKILL.md | `~/.opal/skills/op-task-plan/SKILL.md` | PLAN 산출물 규격 |
| D-5 | 설계 | plan-guide.md | `~/.opal/skills/op-task-plan/references/plan-guide.md` | Phase 그룹핑·실행 체크리스트 형식 |
| D-6 | 설계 | TASK.md | `tasks/051-260702-opp-헤드리스-비서티어-캡/TASK.md` | 요구사항 R1~R5·제약·확정 설계 방향 |

> 인용 형식: citation-rules.md §3.1. 유형: `설계`/`소스`.
> 주: 이 프로젝트에는 `docs/CONVENTIONS.md`가 없다(OPAL 프레임워크 자체 저장소). CONVENTIONS 인용은 자동 스킵(SKILL.md 품질 체크리스트 §201 부재 스킵 룰).

### 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/core/AGENT.md` | 부트스트랩 SSOT — Phase A/B 게이트, WORKER 규칙, 완료보고, 변경이력 | 예 | `opal/core/AGENT.md:7-9,26-28,68-81,224-235` |
| `dashboard/backend/adapters/opbr_adapter.py` | claude -p 서브프로세스 어댑터 — brain 질의 | 예 | `dashboard/backend/adapters/opbr_adapter.py:6,90-123,129-134` |
| `~/.opal/AGENT.md` | AGENT.md 배포본(런타임 실제 로드 대상) | 검증용 dev-artifact 배포(임시) | 아래 R5/Step 6 참조 |

### 현재 상태

**부트스트랩 2-tier 구조** (D-1):

- **Phase A (비서 tier, 항상)**: setting 머지 게이트(step 0) → identity(step 1) → PRINCIPLES(step 2.5). 보고형식·도구·MCP 인지맵·`//` 커맨드/스킬 레지스트리 해석은 AGENT.md 본문 Read 자체로 활성화 (`opal/core/AGENT.md:13-15`).
- **Phase B (PM tier, 승격 게이트)**: cwd에 `.opal/AGENT.md`가 존재하면 harness(step 3) + opal-pm(step 4) + 프로젝트 AGENT.md(step 5)를 로드 (`opal/core/AGENT.md:26-32`). 승격 신호가 `.opal/AGENT.md` 존재 하나뿐 (`opal/core/AGENT.md:28`).

**기존 스킵 경로 2종** (둘 다 all-or-nothing):

1. `bootstrap:off` (effective setting 토글) — step 1~7 전부 스킵, OPAL 없이 순수 동작 (`opal/core/AGENT.md:18`).
2. `[WORKER]` 첫 줄 마커 — Phase A·B·공통 전부 스킵, 즉시 작업. 비서/PM tier 분기와 직교하는 별도 스킵 경로 (`opal/core/AGENT.md:9`).

**중간 단(비서 tier만 켜고 PM 스킵)이 부재**한다. → 본 태스크가 신설하는 `[ASSISTANT]` 마커가 이 중간 단이다.

**`//` 커맨드는 비서 tier 능력** — `//`(opi 포함) Lazy 트리거의 전제 조건이 없어(`opal/core/AGENT.md:15,52`) 비서 tier(Phase A)만으로 `//opbr` 발동·완주가 가능하다. 이것이 `[ASSISTANT]` 캡(Phase B 스킵)이 브레인 질의를 깨뜨리지 않는 근거다.

**완료 보고 규칙** (`opal/core/AGENT.md:68-81`): 세션 첫 응답에 `[부트스트랩] ✅ principles ✅ identity ✅ harness ✅ PM ✅ PM모드 ⏳ registry ...` 두 줄. 이미 **비서 세션(`.opal/AGENT.md` 부재)** 케이스에 대해 `⬜ harness ⬜ PM ⬜ PM모드` 표기 규칙이 존재한다(`:79`). `[ASSISTANT]` 캡 세션은 이 규칙을 확장 재사용한다.

**브레인 어댑터** (D-2): `prompt = f'//opbr query --read-only "{question}"'` (`opbr_adapter.py:123`) → `cmd = [CLAUDE_BIN, "--allowedTools", "Bash,Read,Grep,Glob", "-p", prompt, "--output-format", "json"]` (`:129-134`), `shell=False`, `cwd=project_path` (`:158-159`). read-only 가드는 opbr `--read-only` 계약으로 보장(`:122`). 현재 `cwd=project_path`에 `.opal/AGENT.md`가 있으면 서브프로세스가 Phase B까지 승격 → 읽기전용 브레인 워커가 PM tier(구현금지 가드·디스패치 의무)를 불필요 로드하는 tier 오염.

**변경이력 최신** (`opal/core/AGENT.md:228-235`): 최신 행 `v4.1 | 2026-06-30 17:41 | ... (050)`. 신규 행은 `v4.2`.

### 영향 범위

- **집행점 1**: `opal/core/AGENT.md` — Phase B 승격 게이트 억제 절 + 설계원칙/WORKER 인접 3단 사다리 명시 + 완료보고 표기 + 변경이력. 문서 프로즈 변경이므로 코드 회귀 없음. **인터랙티브(무마커) 세션 동작은 게이트가 첫 줄 마커 판정을 추가할 뿐 무마커 경로는 불변 → 회귀 0.**
- **집행점 2**: `opbr_adapter.py` — prompt 문자열 첫 줄 프리픽스 + docstring 1줄. `cmd` 배열·`shell=False`·`--allowedTools`·`--read-only` 계약은 불변.
- **배포 경계**: 런타임 claude는 `~/.opal/AGENT.md`(배포본)를 Read하므로, 소스 수정만으로는 게이트가 반영되지 않는다. R5 검증 전 소스→`~/.opal/AGENT.md` dev-artifact 배포가 선행되어야 한다. 캡틴의 canonical install은 후속.
- **비영향**: 헌법(PRINCIPLES.md)·opal-harness.md·opal-pm.md·프로젝트 `.opal/AGENT.md`는 미변경 (제외 범위 — TASK §명확화 결과 범위 행, D-6).

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| - | (없음) | 신규 파일 없음 — 기존 파일 수정만 | D-6 §범위 |

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| M-1 | `opal/core/AGENT.md` | 설계원칙 박스에 3단 마커 사다리 명시 (`:7` 인접) | R1 AC(b), D-6 R1 |
| M-2 | `opal/core/AGENT.md` | `[WORKER 규칙]` 박스 뒤에 `[ASSISTANT 규칙]` 박스 신설 (`:9` 인접) | R1 AC(a)(c), D-6 R1 |
| M-3 | `opal/core/AGENT.md` | Phase B 승격 게이트에 `[ASSISTANT]` 억제 절 추가 (`:28`) | R1 AC(a), D-6 R1 |
| M-4 | `opal/core/AGENT.md` | 완료 보고에 `[ASSISTANT]` 캡 세션 표기 규칙+예시 추가 (`:79` 인접) | R2, D-6 R2 |
| M-5 | `opal/core/AGENT.md` | 변경이력 표에 v4.2/2026-07-02/051 행 추가 (`:235` 다음) | R3, D-6 R3 |
| M-6 | `dashboard/backend/adapters/opbr_adapter.py` | `prompt` 첫 줄에 `[ASSISTANT]\n` 프리픽스 (`:123`) | R4 AC(a), D-6 R4 |
| M-7 | `dashboard/backend/adapters/opbr_adapter.py` | docstring(@header `:6` 또는 함수 docstring)에 비서 tier 캡 의도 1줄 | R4 AC(b), D-6 R4 |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| - | (없음) | 삭제 없음 |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | AGENT.md 게이트+박스+보고+이력 편집 (M-1~M-5) | `opal/core/AGENT.md` | 중 |
| 2 | opbr_adapter.py 프리픽스+docstring (M-6~M-7) | `opbr_adapter.py` | 하 |
| 3 | dev-artifact 배포 (소스→`~/.opal/AGENT.md`) | 배포본 | 하 |
| 4 | 동작 검증 (프로브 claude -p 실측) | - | 중 |

> M-1~M-5는 동일 파일이므로 반드시 순차(같은 Phase 불가 — plan-guide §Phase 그룹핑 규칙 3). M-6~M-7도 동일 파일 순차. 파일 간(AGENT.md ↔ opbr_adapter.py)은 독립이나, 검증(순서 4)이 두 파일 변경을 모두 소비하므로 실행 체크리스트에서는 파일 단위로 그룹핑한다.

### 핵심 설계

#### M-1 — 설계원칙 박스: 3단 마커 사다리 명시

현 `[설계 원칙]` 박스(`opal/core/AGENT.md:7`)는 Phase A/B 2-phase를 서술하나 마커 사다리는 `[WORKER 규칙]` 박스(`:9`)에만 부분 존재한다. 3단 스킵 사다리를 한눈에 보이게 명시한다 (R1 AC(b), D-6 R1).

박스 말미 또는 별도 문장으로 추가할 내용(의미):

- 첫 줄 마커로 부트스트랩 로드 범위를 결정하는 3단 사다리가 있다:
  - `[WORKER]` → 전부 스킵 (Phase A·B·공통)
  - `[ASSISTANT]` → 비서 tier만 (Phase A) — `.opal/AGENT.md`가 있어도 Phase B 스킵
  - (무마커) → 비서 + PM (Phase A + B, 프로젝트면 승격)

근거: `[WORKER 규칙]` 직교 스킵 경로 명문화 패턴 재사용 (`opal/core/AGENT.md:9`). 마커는 첫 줄 프리픽스 (D-6 §확정 설계 방향).

#### M-2 — `[ASSISTANT 규칙]` 박스 신설

`[WORKER 규칙]` 박스(`:9`) 직후에 대칭 박스를 신설한다 (R1 AC(a)(c), D-6 R1). 문구(의미):

> **[ASSISTANT 규칙]** 디스패치/프롬프트 첫 줄이 `[ASSISTANT]`이면 Phase A(비서 tier)까지만 로드하고 **Phase B(PM tier) 승격을 억제**한다 — cwd에 `.opal/AGENT.md`가 있어도 harness·opal-pm·프로젝트 PM 컨텍스트를 로드하지 않는다. `[WORKER]`(전부 스킵)와 직교하는 별도 스킵 경로다. **마커 첫 줄 이후의 라인은 실제 요청으로 정상 처리**되며, 비서 tier가 보유한 `//` 커맨드/스킬 레지스트리 해석 능력은 그대로 유효하므로 `//opbr` 등 `//` 커맨드가 정상 발동·완주된다.

- 마커 이후 라인 실제 요청 처리 + `//` 인식 유지 근거: `//` Lazy 트리거는 전제 조건 없음, 비서 tier에서 `//` 발동 가능 (`opal/core/AGENT.md:15,52`) → R1 AC(c) 충족.
- 직교 스킵 경로 표현은 `[WORKER 규칙]` 문구("직교 스킵 경로") 재사용 (`opal/core/AGENT.md:9`).
- [MUST] `opal/core/AGENT.md:15`: "`//`(opi 포함) 커맨드는 harness/PM tier 로드를 전제하지 않는다 — `//` Lazy 트리거의 전제 조건은 없음" — 이 불변식이 `[ASSISTANT]` 캡 상태의 `//opbr` 완주를 보장하므로 박스 문구가 이를 재해석 없이 인용·반영해야 한다.

#### M-3 — Phase B 승격 게이트에 억제 절 추가

Phase B 게이트 문장(`opal/core/AGENT.md:28`)은 현재:

> [MUST] `opal/core/AGENT.md:28`: "**게이트**: cwd에 `.opal/AGENT.md`가 없으면 Phase B 전체를 스킵한다(harness·opal-pm·PM 컨텍스트 미로드). `.opal/AGENT.md` 존재가 PM tier 승격의 유일 신호다."

억제 절을 이 문장에 병합·확장한다 (R1 AC(a), D-6 R1). 변경 후 의미:

> **게이트**: cwd에 `.opal/AGENT.md`가 없으면 Phase B 전체를 스킵한다. `.opal/AGENT.md`가 있으면 PM tier로 승격한다 — **단, 프롬프트/디스패치 첫 줄이 `[ASSISTANT]`이면 `.opal/AGENT.md`가 있어도 Phase B 전체를 스킵한다(`[ASSISTANT 규칙]` 참조)**. 즉 승격 신호는 "`.opal/AGENT.md` 존재 AND 첫 줄 `[ASSISTANT]` 아님"이다.

- 유일 신호가 `.opal/AGENT.md` 존재 하나뿐이라 headless 캡이 불가했던 문제(`opal/core/AGENT.md:28`, D-6 R1 §왜)를 게이트 조건에 억제 항을 AND로 추가하여 해소.
- 회귀 0 보증: 무마커 세션은 "첫 줄 `[ASSISTANT]` 아님"이 참이므로 기존 승격 경로 불변.

#### M-4 — 완료 보고: `[ASSISTANT]` 캡 세션 표기 규칙

현 비서 세션 표기 규칙(`opal/core/AGENT.md:79`)에 `[ASSISTANT]` 캡 세션 행을 병렬 추가한다 (R2, D-6 R2). 추가 내용(의미):

> **`[ASSISTANT]` 캡 세션 (첫 줄 `[ASSISTANT]` — `.opal/AGENT.md` 존재 여부 무관)**: Phase B를 억제하므로 비서 세션과 동일하게 `harness`·`PM`·`PM모드`를 `⬜`로 표기한다.
> 예: `[부트스트랩] ✅ principles ✅ identity ⬜ harness ⬜ PM ⬜ PM모드 ⏳ registry ⏳ references ⏳ model-mapping`

- 관측성 근거: 비서 세션(`.opal/AGENT.md` 부재)과 동일하게 Phase B 미로드 상태를 완료보고로 관측 가능해야 함 (`opal/core/AGENT.md:79` 기존 규칙 확장, D-6 R2 §왜).
- R5 검증의 AC가 바로 이 표기(`⬜ harness ⬜ PM ⬜ PM모드`)이므로 M-4는 R5 검증의 self-observable 근거가 된다.

#### M-5 — 변경이력 v4.2 행

`opal/core/AGENT.md:235` (v4.1 행) 다음에 추가 (R3, D-6 R3). 형식은 기존 행 스키마(`| 버전 | 일시 | 변경내용 |`) 준수:

```
| v4.2 | 2026-07-02 HH:mm | **`[ASSISTANT]` 첫 줄 마커 신설 — headless(claude -p) 호출을 비서 tier(Phase A)로 캡.** Phase B 승격 게이트에 억제 절 추가(첫 줄 `[ASSISTANT]`이면 `.opal/AGENT.md` 있어도 Phase B 스킵). `[WORKER]`(전부)/`[ASSISTANT]`(Phase A만)/무마커(A+B) 3단 마커 사다리 명문화 + `[ASSISTANT 규칙]` 박스 신설. 완료보고에 캡 세션 `⬜ harness ⬜ PM ⬜ PM모드` 표기 추가. opbr_adapter.py -p 프롬프트 첫 줄 `[ASSISTANT]` 프리픽스 (첫 소비자). (051) |
```

- `HH:mm`는 EXECUTE 시점 KST 실측값으로 치환 (제약: 변경이력 행 추가 의무, D-6 §제약).

#### M-6 — opbr_adapter.py prompt 첫 줄 프리픽스

현재 (`opbr_adapter.py:123`):

> [MUST] `dashboard/backend/adapters/opbr_adapter.py:123`: `prompt = f'//opbr query --read-only "{question}"'`

변경 후 (의미):

```python
# [ASSISTANT] 첫 줄 마커: headless 호출을 비서 tier(Phase A)로 캡 —
# cwd(project_path)에 .opal/AGENT.md가 있어도 PM tier(Phase B) 승격 억제 (opal/core/AGENT.md [ASSISTANT 규칙])
# //opbr는 비서 tier `//` 능력으로 완주 (opal/core/AGENT.md:15)
prompt = f'[ASSISTANT]\n//opbr query --read-only "{question}"'
```

- 첫 줄이 `[ASSISTANT]`, 다음 줄이 `//opbr query --read-only "..."` → R4 AC(a) 충족.
- `[ASSISTANT]` 마커는 게이트 판정을 위해 프롬프트 **최상단 단독 줄**이어야 한다. `\n`으로 명확히 분리. `//opbr`가 첫 줄이 아니게 되지만, `[ASSISTANT 규칙]`이 "마커 이후 라인은 실제 요청으로 처리"를 보장(M-2)하므로 `//` 인식 유지 (D-6 §확정 설계, `opal/core/AGENT.md:15`).
- **불변 유지**: `cmd` 배열(`:129-134`)·`shell=False`(`:158`)·`--allowedTools "Bash,Read,Grep,Glob"`(`:131`)·`--read-only` 계약(`:122`)은 미변경 → R4 AC(c) 충족.

#### M-7 — docstring 비서 tier 캡 의도

@header docstring(`opbr_adapter.py:6`) 또는 `prime_and_ask` docstring(`:97-121`)에 1줄 추가 (R4 AC(b)):

> 프롬프트 첫 줄 `[ASSISTANT]` 마커로 headless 호출을 비서 tier(Phase A)로 캡 — 읽기전용 브레인 워커가 PM tier(구현금지 가드·디스패치 의무·CLOSE 게이트)를 불필요 로드하는 tier 오염을 방지한다 (`opal/core/AGENT.md` [ASSISTANT 규칙]).

- 배치 권고: @header `description`(`:6`)에 요약 1구 + `prime_and_ask` docstring 본문(`:97`)에 1줄. @header는 code-scan 검색 노출용이므로 짧게, 함수 docstring에 근거 인용 포함.

---

## 3. 실행 체크리스트

> 총 6개 Step | Phase 3개
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1 | 1, 2 | 순차 | 동일 파일(AGENT.md) — M-1~M-3 편집 |
> | 1 | 3 | 순차 | 동일 파일(AGENT.md) — M-4~M-5 편집 (Step 1,2 뒤) |
> | 2 | 4 | 병렬 가능 | 독립 파일(opbr_adapter.py) — Phase 1과 파일 독립이나 검증 전 완료 필요 |
> | 3 | 5 | 순차 | dev-artifact 배포 (Step 1~4 완료 후) |
> | 3 | 6 | 순차 | 동작 검증 (Step 5 후) |
>
> 주: AGENT.md는 단일 파일이므로 M-1~M-5를 Step 1→2→3 순차로 분할(plan-guide §Phase 규칙 3 — 동일 파일 반드시 순차). Step 4(opbr_adapter.py)는 Step 1~3과 파일이 독립이나, EXECUTE 병렬 디스패치 시 두 워커가 별도 파일을 잡으므로 안전.

### Step 1: AGENT.md — 3단 마커 사다리 + `[ASSISTANT 규칙]` 박스 (M-1, M-2)

- [ ] 완료
- **파일**: `opal/core/AGENT.md`
- **작업 내용**: (1) `[설계 원칙]` 박스(`:7`)에 3단 마커 사다리(`[WORKER]`/`[ASSISTANT]`/무마커) 명시 문장 추가 (M-1 §핵심 설계). (2) `[WORKER 규칙]` 박스(`:9`) 직후에 `[ASSISTANT 규칙]` 박스 신설 — 억제 의미 + 마커 이후 라인 실제 요청 처리 + `//` 커맨드 인식 유지 + `[WORKER]`와 직교 명시 (M-2 §핵심 설계).
- **완료 기준**: (a) 문서에 `[WORKER]`(전부 스킵)/`[ASSISTANT]`(Phase A만)/무마커(A+B) 3단 구분이 명시된다 [R1 AC(b)]. (b) `[ASSISTANT 규칙]` 박스에 "마커 이후 라인 실제 요청 처리" + "`//` 커맨드 인식 유지" 문구가 존재한다 [R1 AC(c)]. (c) `[ASSISTANT]`가 `[WORKER]`와 직교하는 별도 스킵 경로로 명문화된다.
- **테스트**: `grep -n '\[ASSISTANT 규칙\]' opal/core/AGENT.md` 1건 hit. 박스 본문에 `//` + "실제 요청" 문구 확인.
- **의존**: 없음

### Step 2: AGENT.md — Phase B 승격 게이트 억제 절 (M-3)

- [ ] 완료
- **파일**: `opal/core/AGENT.md`
- **작업 내용**: Phase B 게이트 문장(`:28`)에 "첫 줄이 `[ASSISTANT]`이면 `.opal/AGENT.md`가 있어도 Phase B 전체를 스킵한다"는 억제 절을 AND 조건으로 병합 (M-3 §핵심 설계). 승격 신호를 "`.opal/AGENT.md` 존재 AND 첫 줄 `[ASSISTANT]` 아님"으로 재정의.
- **완료 기준**: (a) Phase B 게이트 문장에 `[ASSISTANT]` 억제 조건이 존재한다 [R1 AC(a)]. (b) 무마커 세션의 승격 경로 서술이 보존된다(회귀 0).
- **테스트**: `:26-32` 구간 Read → 게이트 문장에 `[ASSISTANT]` 억제 절 포함 확인. 무마커 승격 문장 잔존 확인.
- **의존**: Step 1 (`[ASSISTANT 규칙]` 박스 참조 링크 정합)

### Step 3: AGENT.md — 완료보고 캡 표기 + 변경이력 v4.2 (M-4, M-5)

- [ ] 완료
- **파일**: `opal/core/AGENT.md`
- **작업 내용**: (1) 완료 보고 규칙(`:79` 인접)에 `[ASSISTANT]` 캡 세션 `⬜ harness ⬜ PM ⬜ PM모드` 표기 규칙+예시 추가 (M-4 §핵심 설계). (2) 변경이력 표(`:235` 다음)에 v4.2/2026-07-02 KST 실측시각/051 행 추가 (M-5 §핵심 설계).
- **완료 기준**: (a) 완료 보고 규칙에 `[ASSISTANT]` 캡 세션 `⬜ harness ⬜ PM ⬜ PM모드` 예시가 존재한다 [R2 AC]. (b) 변경이력 표 마지막에 v4.2 / `2026-07-02 HH:mm` / 051 설명 행이 존재한다 [R3 AC].
- **테스트**: `grep -n 'ASSISTAN.*⬜\|⬜.*harness' opal/core/AGENT.md` hit. 변경이력 표 마지막 행 `v4.2 ... (051)` 확인.
- **의존**: Step 2

### Step 4: opbr_adapter.py — `[ASSISTANT]` 프리픽스 + docstring (M-6, M-7)

- [ ] 완료
- **파일**: `dashboard/backend/adapters/opbr_adapter.py`
- **작업 내용**: (1) `prompt`(`:123`)을 `f'[ASSISTANT]\n//opbr query --read-only "{question}"'`로 변경 + 인접 주석에 캡 의도·근거 (M-6 §핵심 설계). (2) @header description(`:6`) 및/또는 `prime_and_ask` docstring(`:97`)에 비서 tier 캡 의도 1줄 추가 (M-7 §핵심 설계).
- **완료 기준**: (a) prompt 첫 줄이 `[ASSISTANT]`이고 이어서 `//opbr query --read-only "..."`가 온다 [R4 AC(a)]. (b) docstring에 비서 tier 캡 의도가 1줄 이상 기재된다 [R4 AC(b)]. (c) `cmd` 배열·`shell=False`·`--allowedTools "Bash,Read,Grep,Glob"`·`--read-only` 계약이 미변경 유지된다 [R4 AC(c)].
- **테스트**: `grep -n 'ASSISTANT' opbr_adapter.py` → prompt 라인+docstring hit. `git diff` 로 `:129-134,158-159`(cmd/shell/allowedTools) 무변경 확인. `python -c "import ast; ast.parse(open('...').read())"` 구문 검증.
- **의존**: 없음 (Step 1~3과 파일 독립 — Phase 1과 병렬 가능)

### Step 5: dev-artifact 배포 (소스 → `~/.opal/AGENT.md`)

- [ ] 완료
- **파일**: `~/.opal/AGENT.md` (배포본)
- **작업 내용**: 수정된 소스 `opal/core/AGENT.md`를 런타임 로드 대상인 `~/.opal/AGENT.md`로 배포한다(검증 목적 dev-artifact). 런타임 claude가 배포본을 Read하므로 게이트 반영을 위해 필수 선행. **캡틴의 canonical install은 후속 별도 수행** — 이 Step은 검증용 임시 배포임을 명시 (R5 §중요, D-6 R5).
- **완료 기준**: `~/.opal/AGENT.md`에 Step 1~3 변경(`[ASSISTANT 규칙]` 박스·게이트 억제 절·캡 표기·v4.2 이력)이 반영되어 있다.
- **테스트**: `grep -n '\[ASSISTANT 규칙\]\|v4.2' ~/.opal/AGENT.md` hit. `diff <(...) opal/core/AGENT.md` 관련 구간 일치.
- **의존**: Step 3 (AGENT.md 소스 편집 완료), Step 4 (opbr_adapter는 배포 불요 — dashboard가 소스 직접 실행)

### Step 6: 동작 검증 — 캡 마커 프로브 실측 (R5)

- [ ] 완료
- **파일**: - (런타임 실측)
- **작업 내용**: 프로젝트 cwd(`.opal/AGENT.md` 존재 디렉토리, 예: 본 저장소 루트)에서 `[ASSISTANT]` 프리픽스가 있는 `claude -p` 프로브를 실행하여 Phase B 미로드를 실측한다. 프로브 프롬프트: 첫 줄 `[ASSISTANT]`, 다음 줄에 "부트스트랩 완료 보고 두 줄과 이번 세션에서 Read한 파일 목록을 출력하라"는 지시. (실제 `//opbr` 부작용 없이 로드 상태만 관측하는 프로브로 구성.)
- **완료 기준**: (a) 프로브 완료 보고가 `⬜ harness ⬜ PM ⬜ PM모드`이다. (b) Read한 파일 목록에 `opal-harness.md`·`opal-pm.md`·프로젝트 `.opal/AGENT.md`가 **없다** [R5 AC]. (c) 대조군: 무마커 동일 프로브는 `✅ harness ✅ PM ✅ PM모드`로 Phase B 로드(회귀 0 확인) — 선택적 대조 실측.
- **테스트**: `claude -p` 출력에서 `⬜ harness` 문자열 + Read 파일 목록에 harness/opal-pm/프로젝트 AGENT.md 부재 확인. self-confirming 방지: 문서 프로즈가 실제 게이트 판단에 반영됨을 런타임 산출로 확인 (헌법 §4, D-6 R5 §왜).
- **의존**: Step 5 (배포본 반영 후여야 게이트 실측 가능)

---

## 4. QA 체크리스트

### 기능 테스트

- [ ] R1 — Phase B 게이트에 `[ASSISTANT]` 억제 절 존재 + 3단 사다리 명시 + 마커 이후 라인 실제 요청/`//` 인식 유지 명시 (Step 1,2)
- [ ] R2 — 완료보고에 `[ASSISTANT]` 캡 세션 `⬜ harness ⬜ PM ⬜ PM모드` 예시 존재 (Step 3)
- [ ] R3 — 변경이력에 v4.2/2026-07-02/051 행 존재 (Step 3)
- [ ] R4 — prompt 첫 줄 `[ASSISTANT]` + docstring 캡 의도 + cmd/shell/allowedTools/read-only 계약 불변 (Step 4)
- [ ] R5 — `[ASSISTANT]` 프로브 실측: `⬜ harness ⬜ PM ⬜ PM모드` + harness/opal-pm/프로젝트 AGENT.md 미Read (Step 6)

### 일관성 테스트

- [ ] `[ASSISTANT 규칙]` 박스와 Phase B 게이트 억제 절의 서술이 상호 정합(동일 억제 의미)
- [ ] `[WORKER 규칙]`(직교 스킵 경로 표현)과 `[ASSISTANT 규칙]`의 직교성 서술 일관
- [ ] opbr_adapter.py prompt의 `[ASSISTANT]` 마커 형식(첫 줄 단독 + `\n`)이 AGENT.md 게이트 판정 규약(첫 줄 마커)과 일치
- [ ] 회귀 0 — 무마커 인터랙티브 세션 승격 경로 서술 불변 (Step 2 완료기준 b)
- [ ] 049/050 2-tier 부트스트랩 용어(Phase A/비서 tier, Phase B/PM tier)와 신규 서술 용어 일관

### 문서 품질

- [ ] 한국어 본문 + 영어 코드/마커(`[ASSISTANT]`)/필드명 규칙 준수
- [ ] 변경이력 행 스키마(`| 버전 | 일시 | 변경내용 |`) 준수 + KST 시각 실측
- [ ] `~/.opal/` 직접 편집 금지 준수 — 소스 수정 후 dev-artifact 배포는 검증 예외로만, canonical install은 후속 명시

---

## 5. 리스크 및 대응

| # | 리스크 | 영향 | 대응 방안 |
|---|--------|------|----------|
| R-1 | 배포본 미반영 상태로 R5 검증 시 self-confirming(소스만 보고 통과 착각) | 게이트가 런타임에 반영 안 됐는데 통과 오판 | Step 5(dev-artifact 배포)를 R5 검증(Step 6)의 명시적 선행 의존으로 강제. 검증은 배포본 기준 실측 |
| R-2 | claude -p 게이트 판정이 "첫 줄 마커"를 `[ASSISTANT]\n` 형태로 인식하지 못할 가능성(프롬프트 파싱 규약 불명확) | R1/R4 의도대로 억제 안 될 수 있음 | 마커를 프롬프트 **최상단 단독 줄 + `\n` 분리**로 명확화(M-6). Step 6 실측이 최종 판정 — 실패 시 마커 위치/구분자 조정 후 재검증 |
| R-3 | `//opbr`가 첫 줄이 아니게 되어 커맨드 인식 실패 | 브레인 질의 회귀 | `[ASSISTANT 규칙]`이 "마커 이후 라인 실제 요청 처리 + `//` 인식 유지" 명문화(M-2), 근거 `opal/core/AGENT.md:15`(`//` 전제조건 없음). Step 6에서 `//opbr` 완주 실측 권고(선택 확장) |
| R-4 | 캡틴 canonical install 누락 → dev-artifact가 최종 배포로 오인 | 배포 경계 위반, 이후 install이 dev-artifact 덮어씀 | Step 5 완료기준·변경이력에 "검증용 임시, canonical install 후속" 명시. EXECUTE 결과 반환 시 캡틴 install 필요를 blocker/후속으로 보고 |
| R-5 | 변경이력 시각 placeholder(HH:mm) 미치환 | R3 AC 미충족 | Step 3 테스트에 KST 실측 시각 치환 확인 포함 |
| R-6 | 지연 단축 목적으로 오해된 설계 변경 | 본질(정합성) 이탈, `--lite` 등 별건과 혼선 | PLAN §1/변경이력 문구를 "tier 격리(정합성) 목적, 지연 레버 아님"으로 고정 (D-6 §배경 분석 2, `.opal/memory/follow-up-brain-query-lite.md`) |

---

## 리스크 가설 표 (H-N) — TEST-SCENARIO 입력

| # | 가설 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|---|------|-----------------|----------|--------------|-------------|
| H-1 | `[ASSISTANT]` 첫 줄이 있으면 프로젝트 cwd에서도 Phase B(harness/opal-pm/프로젝트 AGENT.md)를 로드하지 않는다 | 부트스트랩 게이트 판정 | tier 오염 방지의 핵심 — 실패 시 목적 미달 | L3(런타임 claude -p 실측) | 프로브 claude -p, 완료보고·Read목록 관측 (Step 6) |
| H-2 | `[ASSISTANT]` 캡 상태에서도 `//opbr query --read-only` 가 정상 완주한다 | `//` 커맨드 = 비서 tier 능력 계약 (`opal/core/AGENT.md:15`) | 실패 시 브레인 질의 전체 회귀 | L3(런타임 claude -p) | `//opbr` 실제 질의 1건 완주 + JSON 펜스 반환 |
| H-3 | 무마커 인터랙티브/헤드리스 세션의 승격 동작이 불변이다(회귀 0) | Phase B 승격 게이트 무마커 경로 | 실패 시 정상 PM 세션 붕괴 | L3(대조군 실측) + L1(diff) | 무마커 프로브 → `✅ harness ✅ PM ✅ PM모드` |
| H-4 | opbr_adapter 변경이 read-only/shell=False/allowedTools 계약을 깨지 않는다 | `:129-134,158` 보안 계약 | 실패 시 셸 인젝션/쓰기 노출 | L1(git diff·ast) + L2(단위) | `git diff`로 cmd/shell/allowedTools 무변경 확인 |
| H-5 | dev-artifact 배포본이 소스와 동일하게 반영되어 게이트가 런타임에 유효하다 | 배포 경계(소스→~/.opal) | 미반영 시 self-confirming 오판 | L1(diff) → L3(실측) | `diff ~/.opal/AGENT.md opal/core/AGENT.md` 관련 구간 |

---

## 미해결 이슈 / 설계 피드백

1. **claude -p 첫 줄 마커 파싱 규약 (R-2, H-1)**: `[WORKER]` 마커가 claude -p `-p <prompt>` 첫 줄에서 실제로 어떻게 소비되는지(정확한 파싱 위치·구분자)의 결정론적 근거는 문서 프로즈(`opal/core/AGENT.md:9`)뿐이며, `[WORKER]`가 headless에서 검증된 사례가 소스에 명시돼 있지 않다. `[ASSISTANT]`도 동일 파싱 경로에 의존하므로, Step 6 실측이 유일한 최종 판정이다. EXECUTE에서 마커 미인식 시 (a) 마커를 프롬프트 최상단 완전 단독 줄로 조정 또는 (b) 마커+개행 후 빈 줄 삽입 등 폴백 실험이 필요할 수 있다. — PM 확인 권고.
2. **캡틴 canonical install 경계 (R-4)**: Step 5 dev-artifact 배포는 검증용 임시이고 최종 canonical install은 캡틴 수행이다(D-6 §제약). EXECUTE 워커가 배포본을 덮어쓰는 순서·소유권이 install 스크립트(`install-mac.sh`)와 충돌하지 않는지 확인 필요 — 배포 후 캡틴 install 필요를 후속 액션으로 반드시 보고.
3. **`opbr_adapter.py` 외 다른 claude -p 소비자**: 본 태스크는 opbr_adapter를 첫 소비자로 적용하나, dashboard 내 다른 headless 소비자(있다면)의 캡 적용은 범위 밖이다. 후속 태스크로 headless 호출 지점 인벤토리 스캔 권고 (범위 확정 — 현재는 opbr_adapter 단일).
