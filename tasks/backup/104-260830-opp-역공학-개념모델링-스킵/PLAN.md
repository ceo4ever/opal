# PLAN: opdd 역공학 트랙 — 개념모델링 스킵

> 작성일: 2026-08-30 16:41 (KST)
> 입력: `tasks/104-260830-opp-역공학-개념모델링-스킵/TASK.md`
> 출력: `tasks/104-260830-opp-역공학-개념모델링-스킵/PLAN.md`
> 성격: 프레임워크 스펙 문서 개정 (Markdown 3 + JSON 1 + brain 1). 코드 변경 없음.

---

## 1. 현황 조사

### 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | TASK.md (104) | `tasks/104-260830-opp-역공학-개념모델링-스킵/TASK.md` | 요구사항 R-1~R-8 · 배경 분석 A-1~A-9 SSOT |
| D-2 | 설계 | opdd SKILL.md | `opal/skills/opal-pilot-data-design/SKILL.md` | 개정 주 대상 — STEP 1/3/5 · §명시 모드 · §변경이력 |
| D-3 | 설계 | opdd pipeline.json | `opal/skills/opal-pilot-data-design/references/pipeline.json` | `model.pm_gate.gate.checklist` SSOT |
| D-4 | 설계 | op-data-model SKILL.md | `opal/skills/op-data-model/SKILL.md` | §모드 선택 규칙 · 모드별 입력 전제 |
| D-5 | 설계 | op-data-ddl SKILL.md | `opal/skills/op-data-ddl/SKILL.md` | §Step 4 역공학(`sql2dbml`) — 실행 순서 결정의 실측 근거 |
| D-6 | 설계 | Data Design 설계 SSOT | `docs/proposals/opal-data-design.md` | opdd SKILL.md가 `[MUST]` 원문 인용하는 상위 SSOT (§3.2·§3.2.1·§3.4) |
| D-7 | 설계 | opal-harness.md | `opal/core/references/opal-harness.md` | §2.5 워크스페이스 축 — 직교 축 서술의 본(本) |
| D-8 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | §언어 규칙 · §변경이력 작성 의무 |
| D-9 | 설계 | PROJECT.md | `docs/PROJECT.md` | §프로젝트 구성 — Framework 요소 담당 에이전트 매핑 |
| D-10 | 설계 | PM 프로필 | `.opal/AGENT.md` | §금지사항 (배포 경계 · 변경이력) |
| D-11 | 설계 | brain — opdd 파이프라인 흐름 | `.opal/brain/pages/flow/opdd-pipeline-flow.md` | 「개념 → 논리 → 물리 (순차 3모드)」 서술 — 갱신 대상 |

**[MUST] 제약 인용**

- `[MUST]` `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다."
- `[MUST]` `.opal/AGENT.md` §금지사항: "변경이력 누락 금지 — 스킬·에이전트·참조 문서 수정 시 변경이력 표 행 추가 의무."
- `[MUST]` `docs/CONVENTIONS.md` §언어 규칙: "문서 본문 = 한국어 (기술 용어는 영어 병기) / 코드·변수·필드명 = English / YAML frontmatter 키 = English"
- `[MUST]` `docs/CONVENTIONS.md` §변경이력 작성 의무: "일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함"
- `[MUST]` `~/.opal/PRINCIPLES.md` §2 Simplicity First: "Solve only the current requirement. No speculative abstraction or unrequested flexibility."
- `[MUST]` `~/.opal/PRINCIPLES.md` §3 Surgical Changes: "Touch only what the plan names. Don't improve adjacent code."
- `[MUST]` `docs/proposals/opal-data-design.md` §3.2: "DICT가 MODEL을 **선행**한다 — 표준사전·코드가 논리/물리 모델링의 속성명·타입을 결정하는 SSOT이기 때문."
- `[MUST]` `docs/proposals/opal-data-design.md` §3.2.1: "논리는 개념, 물리는 논리 산출물을 입력으로 한다(증분). 기존 ERD가 인풋으로 주입되면 해당 모드부터 시작 가능."
- `[MUST]` `opal/core/references/opal-harness.md` §2.5 (1): "`mode_flag_conflict` 판정 대상이 **아니다** — 모드 플래그 개수 검사에 `--wt`를 세지 않는다."

### 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `docs/proposals/opal-data-design.md` | Data Design 설계 SSOT | **필요** | `:45-47`(파이프라인 도식), `:53`(MODEL 행), `:62`(3모드 순차), `:70`(모드 의존), `:101`(QA 단계 간 정합) |
| `opal/skills/opal-pilot-data-design/SKILL.md` | opdd 오케스트레이터 | **필요** | `:23`(mode_flag_conflict), `:56-68`(인풋 컨텍스트 주입), `:125`(3모드 순차 산문), `:135`(실행 순서 줄), `:142`(MODEL PM Gate 괄호), `:189`(QA 단계 간 정합), `:265-271`(§명시 모드), `:293-299`(§변경이력) |
| `opal/skills/opal-pilot-data-design/references/pipeline.json` | STATE 행·게이트 SSOT | **필요** | `:13-14`(`model.pm_gate.gate.checklist`) |
| `opal/skills/op-data-model/SKILL.md` | MODEL 단계 스킬 | **필요** | `:52-61`(§모드 선택 규칙), `:105`(logical 입력 전제), `:155`(physical 입력 전제), `:196-200`(Step 2 모드 결정), `:304-308`(§변경이력) |
| `.opal/brain/pages/flow/opdd-pipeline-flow.md` | brain 흐름 페이지 | **필요** | `:24`("개념 → 논리 → 물리 (순차 3모드)") |
| `opal/skills/op-data-ddl/SKILL.md` | DDL 단계 스킬 | **불요**(참조만) | `:139-148`(§Step 4 역공학 `sql2dbml`) |
| `opal/core/references/opal-harness.md` | 하네스 SSOT | **불요**(패턴 참조만) | `:142-165`(§2.5 워크스페이스 축) |

### 현재 상태

**(1) 개념모델링은 파이프라인 행이 아니라 MODEL 단계 내부의 모드다.** `pipeline.json`의 MODEL 단계 행은 `model.modeling`(id 6) 1행뿐이며, 3모드는 이 1행 안에서 소비된다 (`opal/skills/opal-pilot-data-design/references/pipeline.json:12`). 따라서 스킵은 **행 삭제가 아니라 디스패치 프롬프트의 실행 순서 분기**로 구현된다 (→ D-1 A-1·A-2).

**(2) 3모드 고정은 5곳에 산재한다.** ① opdd SKILL.md `:125` 산문("pilot은 **3모드 순차 실행** (개념 → 논리 → 물리)"), ② `:135` 디스패치 `**실행 순서**` 줄, ③ `:142` MODEL PM Gate 괄호, ④ `pipeline.json:14` 체크리스트 2항목, ⑤ SSOT `:62`·`:101`. 어느 하나만 고치면 나머지가 자기모순으로 남는다.

**(3) 트랙 개념이 없다.** opdd의 축은 모드 축(`--interactive`/`--semi-agentic`/`--agentic`) 1개뿐이고(`opal/skills/opal-pilot-data-design/SKILL.md:265-271`), 다중 모드 플래그는 `mode_flag_conflict`로 거부된다(`:23`).

**(4) 역공학 신호는 TASK 단계가 이미 감지한다 — 다만 MODEL에 연결되지 않는다.** 인풋 컨텍스트 주입 표의 「기존 ORM → `models/`·`migrations/` code-scan → 현행 스키마 역추적」 행이 존재하나(`opal/skills/opal-pilot-data-design/SKILL.md:66`), 이 감지 결과가 실행 순서를 바꾸지 않는다 (→ D-1 A-3).

**(5) 역공학 실행 경로는 이미 존재한다.** `op-data-ddl` §Step 4가 `sql2dbml dump.sql --mysql -o {설계}/물리모델링/{프로젝트}.dbml`로 기존 DDL에서 물리 DBML을 역추출하며, "역공학 결과물은 MODEL 물리 산출물로 저장하며, op-data-model의 physical 모드 산출물 경로를 따른다"고 명시한다 (`opal/skills/op-data-ddl/SKILL.md:139-148`). 즉 **역공학 트랙의 물리 산출물은 결정론적 도구로 확보 가능한 유일한 출발점**이다.

**(6) 모드 선택 규칙에 「기존 DB/DDL 주입」 분기가 없다.** 현행 표는 「기존 개념 ERD 주입 → logical부터」·「기존 논리 ERD 주입 → physical부터」 2행뿐이다 (`opal/skills/op-data-model/SKILL.md:58-59`).

**(7) 모드별 입력 전제가 역공학과 충돌한다.** logical 모드는 "**입력 전제**: 개념 ERD 산출물 (`{설계}/개념모델링/`) 존재 또는 주입"(`:105`), physical 모드는 "**입력 전제**: 논리 ERD 산출물 (`{설계}/논리모델링/`) 존재 또는 주입"(`:155`)이다. 역공학 트랙에서는 두 전제 모두 최초에 성립하지 않는다.

### 영향 범위

| 영역 | 영향 | 회귀 위험 |
|------|------|----------|
| opdd 파이프라인 (신규 트랙) | 없음 — 트랙 플래그·감지 미발동 시 전 문구 현행 유지 | 조건부 분기가 무조건 실행되면 회귀 (→ H-4) |
| STATE 행 / state-tool | **없음** — `task_steps[]` 15행·`key` 문자열 전량 불변. `gate.checklist` 문자열만 교체 | JSON 파싱 실패 시 `init --rows-from` 전면 중단 (→ H-3) |
| 모드 플래그 검사 | 트랙 플래그가 개수 검사에 섞이면 정상 호출이 `mode_flag_conflict`로 거부 | (→ H-5) |
| `//erm` 단독 호출 경로 | 모드 선택 규칙 표에 역공학 행 1행 추가 — 기존 5행 불변 | 낮음 |
| op-data-ddl | **무변경** — §Step 4는 포인터로만 참조 | 역공학 실행 소유권 모호 (→ H-8) |
| brain | 흐름 페이지 1개 서술 갱신 | 낮음 |

---

## 2. 구현 계획

### 2.1 [결정] 역공학 트랙의 논리·물리 실행 순서 — **(나) `physical → logical` 채택**

TASK.md §명확화 결과 미확정 항목을 여기서 확정한다.

**비교**

| 축 | (가) `logical → physical` 유지 | (나) `physical → logical` 역전 |
|----|-------------------------------|-------------------------------|
| 첫 모드의 입력 전제 | **미충족** — logical 입력 전제가 「개념 ERD 존재 또는 주입」(`opal/skills/op-data-model/SKILL.md:105`)인데 역공학 트랙은 개념을 스킵하므로 첫 모드부터 블로커 | **충족** — 기존 DDL·ORM·DBML이 곧 물리 입력. `sql2dbml`로 결정론 확보 (`opal/skills/op-data-ddl/SKILL.md:139-148`) |
| SSOT 「모드 의존」 규정과의 정합 | **충돌** — "기존 ERD가 인풋으로 주입되면 해당 모드부터 시작 가능"(`docs/proposals/opal-data-design.md:70`)인데 주입된 것은 물리이므로 logical부터 시작할 근거가 없다 | **정합** — 주입된 산출물이 물리이므로 물리를 기점으로 삼는 것이 규정의 직접 적용 |
| 기존 표 패턴과의 일관성 | 「주입 산출물의 다음 모드부터」 패턴(`:58-59`)에서 이탈 | 동일 패턴의 자연 확장 |
| 실제 산출물의 진실성 | 개념 없이 그린 논리가 기존 DB와 괴리 → 물리 단계에서 재작업 발생 | 확정된 물리에서 논리를 역산 → 괴리 0 |
| 정보 흐름 | 존재하지 않는 상위 추상에서 하위를 도출 (허구) | 확정된 하위에서 상위를 추상화 (역공학의 정의) |

**DICT 선행 제약(`docs/proposals/opal-data-design.md` §3.2)의 성립 여부**

- **(가)**: DICT가 논리 속성명을 *결정*한다 — 형식적으로는 성립하나, 그 결정이 기존 DB 컬럼명과 무관하게 이루어져 물리 단계에서 무효화된다. 선행이 **무의미하게 성립**한다.
- **(나)**: DICT는 여전히 MODEL을 **선행**한다. 다만 역할이 「결정(prescriptive)」에서 「기존 컬럼명의 표준사전 역등재·검증(descriptive)」으로 전환되고, 그 등재 결과가 **논리 모드 속성명의 SSOT**로 소비된다 — 논리가 물리 뒤에 오므로 DICT → 논리의 SSOT 관계는 그대로다.
- 이 전환은 **신규 규정을 요구하지 않는다.** SSOT는 이미 "기존 사전이 인풋으로 주입되면 DICT는 '검증·보강' 모드로 축약 가능"(`docs/proposals/opal-data-design.md:57`)을 규정하고, opdd STEP 2 디스패치 프롬프트도 이미 `**모드**: 신규 작성 또는 검증·보강 (기존 사전 주입 여부에 따라 자동 분기)`를 갖고 있다(`opal/skills/opal-pilot-data-design/SKILL.md:106`). 따라서 **(나)는 §3.2 DICT 선행 [MUST] 문장을 한 글자도 고치지 않고 성립한다** — SSOT 변경 표면적이 (가)보다 작다.

**결론**: **(나) `physical → logical`을 확정한다.** (가)는 첫 모드의 입력 전제 미충족(실측 `:105`)과 SSOT 「모드 의존」 규정 충돌(실측 `:70`)이라는 두 개의 구조적 결함을 가지며, 두 결함 모두 (나)에는 없다.

**부수 결정**: (나) 채택에 따라 `op-data-model`의 logical·physical 모드 「입력 전제」 문장에 역공학 트랙 예외 포인터를 각 1줄 추가한다 (→ Step 3). 이를 생략하면 표만 고치고 본문이 모순으로 남는다 (H-6).

### 2.2 [결정] 트랙명·플래그명

| 항목 | 확정값 | 근거 |
|------|--------|------|
| 트랙 2종 | `greenfield`(신규 트랙) / `reverse`(역공학 트랙) | `docs/CONVENTIONS.md` §언어 규칙 — 코드·필드명은 English, 본문은 한국어 병기 |
| 명시 플래그 | `--reverse`(약칭 `--rev`) / `--greenfield`(약칭 `--gf`) | `opal/core/references/opal-harness.md` §2.5 `--worktree`/`--wt` 장·단 병기 선례 |
| 기본값(폴백) | `greenfield` | 회귀 0 요구 — 판정 불능·인풋 부재 시 현행 동작이 되어야 한다 |

**양방향 플래그를 두는 이유**: 자동 감지가 역공학을 **오탐**했을 때 사용자가 신규 트랙을 강제할 수단이 필요하다. `--reverse` 하나만 두면 「감지=역공학, 사용자 의도=신규」 조합에서 확인 왕복 외에 회피 경로가 없다. 두 플래그는 대칭 1쌍이며 speculative 확장이 아니다 (`~/.opal/PRINCIPLES.md` §2 Simplicity First 준수 — 요구사항 R-1의 「플래그가 자동 감지보다 우선한다」를 양방향으로 성립시키는 최소 집합).

### 2.3 [결정] 자동 감지 대상 + 확인 절차

**자동 감지 대상 (1건 이상 → 역공학 후보)**

| # | 감지 대상 | 감지 경로 | 기존 근거 |
|---|----------|----------|----------|
| 1 | 기존 ORM 모델·마이그레이션 코드 | `models/`·`migrations/` code-scan | 현행 인풋 표에 이미 존재 (`opal/skills/opal-pilot-data-design/SKILL.md:66`) |
| 2 | 기존 DDL 스크립트·덤프 (`.sql`) | 사용자 지정 경로 · `{설계}/250.DDL/` | `op-data-ddl` §Step 4 입력 (`opal/skills/op-data-ddl/SKILL.md:139-148`) |
| 3 | 기존 물리 DBML | `{설계}/물리모델링/*.dbml` | `op-data-model` physical 산출물 경로 (`opal/skills/op-data-model/SKILL.md:159`) |

> 「기존 ERD」 인풋 행은 개념·논리 ERD일 수 있어 역공학 신호로 **인정하지 않는다** — 오탐 억제.

**확인 절차 (신규 게이트·신규 STATE 행 없음)**

트랙 확정 질의는 **STEP 1 TASK의 interview 절차 내부 질문 항목으로 편입**한다. TASK 단계는 어느 모드에서도 사용자 대면이므로(`opal/skills/opal-pilot-data-design/SKILL.md:31`) 별도 게이트 없이 「감지만으로 자동 스킵하지 않는다」는 확정 방향이 성립한다. `pipeline.json`의 `task_steps[]`를 건드리지 않으므로 [MUST] 행 수·key 불변 제약을 자동 충족한다.

**우선순위**: `명시 플래그 > 자동 감지 + 사용자 확인 > 폴백(greenfield)`. 플래그가 있으면 감지·질의를 모두 생략한다 (사용자 주권 — `~/.opal/PRINCIPLES.md` §Core Stance).

### 2.4 파일 변경 계획

#### 신규 생성

없음.

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| M-1 | `docs/proposals/opal-data-design.md` | §3.2 파이프라인 도식·MODEL 행 트랙 분기 / §3.2.1 「3모드 순차」 문장 트랙 분기 + 모드 의존 규정에 역공학 예외 / §3.4 「단계 간 정합」 항목 트랙 분기 | D-1 R-8 (→ A-9) |
| M-2 | `opal/skills/opal-pilot-data-design/SKILL.md` | STEP 1 트랙 판정 규칙 신설 / STEP 3 실행 순서·산문·PM Gate 괄호 분기 / STEP 5 QA 항목 분기 / §명시 모드에 트랙 축 절 신설 / §변경이력 1행 | D-1 R-1·R-2·R-3·R-5·R-7 |
| M-3 | `opal/skills/opal-pilot-data-design/references/pipeline.json` | `model.pm_gate.gate.checklist` 4항목 중 2항목을 트랙 조건부 문언으로 교체 | D-1 R-4 (→ A-7) |
| M-4 | `opal/skills/op-data-model/SKILL.md` | §모드 선택 규칙 역공학 행 1행 추가 / logical·physical 입력 전제에 트랙 예외 포인터 각 1줄 / Step 2 모드 결정에 트랙 1줄 / §변경이력 1행 | D-1 R-6·R-7 (→ A-5) |
| M-5 | `.opal/brain/pages/flow/opdd-pipeline-flow.md` | MODEL 흐름 서술 트랙 분기 + `updated` 갱신 | D-11 (CLOSE 관련 문서 최신화) |

#### 삭제

없음.

### 2.5 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | 설계 SSOT 트랙 분기 — **원문 문자열 확정** | M-1 | 중 |
| 2 | opdd 스킬 + pipeline.json 개정 (SSOT 원문 축자 인용) | M-2, M-3 | 상 |
| 3 | op-data-model 모드 선택 규칙 확장 | M-4 | 중 |
| 4 | brain 흐름 페이지 갱신 | M-5 | 하 |

**의존성 근거**: opdd SKILL.md는 SSOT를 `[MUST]` **원문 인용**한다(`opal/skills/opal-pilot-data-design/SKILL.md:91`·`:123`·`:155`). R-8 AC가 "SSOT 원문과 축자 일치"를 요구하므로 **SSOT 문장을 먼저 확정한 뒤 그 문자열을 그대로 복사**해야 한다. 순서를 뒤집으면 축자 불일치가 구조적으로 발생한다 (H-2).

### 2.6 핵심 설계

#### M-1 `docs/proposals/opal-data-design.md`

**(a) §3.2 파이프라인 도식** (`:44-47`) — 주석 줄을 트랙 분기로 교체.

```
TASK → DICT → MODEL → DDL/MIGRATION → QA → CLOSE
              (트랙별 모드)   (물리 이후만)
```

**(b) §3.2 단계 표 MODEL 행** (`:53`) — "개념(Mermaid)→논리(Mermaid)→물리(DBML)"를 「신규 트랙: 개념→논리→물리 / 역공학 트랙: 물리→논리(개념 제외)」로 교체. 「속성명·타입은 DICT 사전 기반」·의존 열 `**DICT**`는 **불변** (→ §2.1 DICT 선행 성립 논증).

**(c) §3.2 「핵심 순서 결정」 인용 블록** (`:57-58`) — **불변**. opdd SKILL.md `:91`·`:123`·`:155`가 이 두 문장을 축자 인용 중이므로 건드리면 3곳이 동시 파손된다. `[MUST]` `docs/proposals/opal-data-design.md` §3.2: "DICT가 MODEL을 **선행**한다" / "DDL/MIGRATION은 MODEL의 물리(DBML) 산출 이후에만 실행 가능"

**(d) §3.2.1 도입 문장** (`:62`) — "pilot은 MODEL 단계에서 3모드를 순차 실행(개념→논리→물리)하되"를 트랙 분기 문장으로 교체. 확정 문안(이 문자열이 M-2의 축자 인용 원본이 된다):

> pilot은 MODEL 단계에서 **트랙에 따라 모드를 순차 실행**한다 — 신규(greenfield) 트랙은 개념→논리→물리 3모드, 역공학(reverse) 트랙은 물리→논리 2모드(개념 모드 제외)다. 단계 스킬 단독 호출 시 특정 모드만 발동 가능.

**(e) §3.2.1 「모드 의존」 인용 블록** (`:70`) — 기존 문장 유지 + 역공학 예외 1문장 추가:

> 역공학 트랙에서는 기존 DB·DDL·ORM에서 역추출한 **물리(DBML)가 기점**이며, 논리는 물리에서 역산한다. 개념 모드는 실행하지 않는다.

**(f) §3.4 QA 검증 항목 첫 줄** (`:101`) — "단계 간 정합: 개념 ERD ↔ 논리 ↔ 물리 (엔티티/관계 보존)"를 트랙 분기로 교체. 확정 문안(M-2 STEP 5의 축자 인용 원본):

> 단계 간 정합 — 신규 트랙: 개념 ERD ↔ 논리 ↔ 물리 / 역공학 트랙: 물리 ↔ 논리 (엔티티/관계 보존)

> **변경이력 없음**: 이 문서에는 `## 변경이력` 표가 존재하지 않는다(`:151-154`에서 §8로 종료). `docs/CONVENTIONS.md` §변경이력 작성 의무의 대상은 "스킬·에이전트·참조 문서"이며, 표를 신설하는 것은 `~/.opal/PRINCIPLES.md` §3 Surgical Changes 위반이다 — **표를 신설하지 않는다** (→ H-9로 보고).

#### M-2 `opal/skills/opal-pilot-data-design/SKILL.md`

**(a) STEP 1: TASK — §트랙 판정 (R-1)**. `### 인풋 컨텍스트 주입` 절(`:56-68`) **직후**, `### 완료 처리`(`:70`) **직전**에 신규 절 `### 트랙 판정 (신규 / 역공학)` 삽입. 구성:

1. 트랙 2종 정의표 (`greenfield` / `reverse` + 각 트랙의 MODEL 실행 순서)
2. 판정 우선순위 3단: `명시 플래그(--reverse/--rev, --greenfield/--gf) > 자동 감지 + 사용자 확인 > 폴백 greenfield`
3. 자동 감지 대상 3종 표 (→ §2.3)
4. 확인 절차 — interview 질문 항목으로 편입, 신규 STATE 행·게이트 없음
5. 확정 결과를 TASK.md 「산출물 저장 경로」 절과 나란히 **「트랙」으로 기록**하고, STEP 3 디스패치 프롬프트에 주입한다

**(b) STEP 3: MODEL 산문** (`:125`) — "pilot은 **3모드 순차 실행** (개념 → 논리 → 물리)."을 §3.2.1 확정 문안(M-1 (d))의 축자 인용으로 교체:

```
`opal-db-agent` 단일 에이전트에 op-data-model 스킬을 디스패치한다.

**[MUST]** `docs/proposals/opal-data-design.md` §3.2.1: "pilot은 MODEL 단계에서 **트랙에 따라 모드를 순차 실행**한다 — 신규(greenfield) 트랙은 개념→논리→물리 3모드, 역공학(reverse) 트랙은 물리→논리 2모드(개념 모드 제외)다."
```

**(c) STEP 3 디스패치 프롬프트 `**실행 순서**` 줄** (`:135`) — R-3의 실질 구현 지점. 교체안:

```
**트랙**: {greenfield | reverse — TASK.md 트랙 판정 결과}
**실행 순서**:
  - greenfield(신규): concept → logical → physical (순차, 이전 모드 산출물이 다음 모드 입력)
  - reverse(역공학): physical → logical (순차, 역추출 물리를 기점으로 논리를 역산. concept 미실행)
```

`**이전 산출물**`(`:133`) 줄에 역공학 트랙 입력 1건 추가: `{역공학 트랙: 기존 DDL 덤프·ORM 스키마·기존 물리 DBML 중 감지된 인풋 경로}`.

> **AC 검증 포인트**: 교체 후 `reverse` 순서 문자열에 `concept` 0건, `greenfield` 줄은 원문 그대로 보존.

**(d) STEP 3 PM Gate 괄호** (`:142`) — "(개념·논리·물리 ERD 정합·DICT 사전 용어 정합 검토)"를 "(트랙별 모델링 산출물 정합 — 신규: 개념·논리·물리 / 역공학: 물리·논리 · DICT 사전 용어 정합 검토)"로 교체.

**(e) STEP 5: QA 첫 항목** (`:189`) — M-1 (f) 확정 문안의 축자 인용으로 교체:

```
- [ ] 단계 간 정합 — 신규 트랙: 개념 ERD ↔ 논리 ↔ 물리 / 역공학 트랙: 물리 ↔ 논리 (엔티티/관계 보존)
```

나머지 3개 QA 항목(`:190-192`)은 **불변** (`~/.opal/PRINCIPLES.md` §3 Surgical Changes).

**(f) §명시 모드 — 트랙 축 절 신설 (R-2)**. `### 명시 모드` 표(`:267-271`) **직후**에 `### 트랙 축 (--reverse / --greenfield)` 신설. `opal/core/references/opal-harness.md` §2.5의 4소절 구성을 그대로 계승:

| 소절 | 내용 |
|------|------|
| (1) 모드 축과 직교하는 별개 축 | 모드 축은 "PM이 얼마나 자율적으로 진행하는가", 트랙 축은 "설계의 출발점이 백지인가 기존 스키마인가"를 결정한다. 조합 가능(`//opdd --agentic --rev`). **`mode_flag_conflict` 판정 대상이 아니다 — 모드 플래그 개수 검사에 트랙 플래그를 세지 않는다.** 서브 하네스 로딩 규칙(§Harness)에 영향을 주지 않는다 |
| (2) 트랙 플래그 미사용 시 = 현행 동작 100% 유지 | 자동 감지 0건이면 `greenfield`로 확정되고, MODEL 실행 순서·PM Gate·QA 항목 문구가 전부 현행과 동일하다. 어떤 조건부 분기도 실행되지 않는다. `pipeline.json` `task_steps[]` 행 수·key·STATE 렌더 결과 불변 |
| (3) 감지 불능·인풋 부재 시 폴백 | 감지 대상 3종이 모두 부재하거나 code-scan 실패 시 **태스크를 중단하지 않는다.** `greenfield`로 폴백하고 사용자에게 사유를 통보한다 (fail-safe = 현행 동작) |
| (4) 산출물 경로 계약 | 역공학 트랙에서도 `{설계}` 트리는 불변이며, `{설계}/220.개념모델링/`만 **생성하지 않는다**. `230.논리모델링/`·`240.물리모델링/`·`250.DDL/` 경로는 신규 트랙과 동일하다 |

**(g) §변경이력** (`:299` 다음 행) — `v1.6` 행 추가. 일시는 `node ~/.opal/tools/date/date.js datetime`로 취득(추측 금지). 변경 내용에 `(104)` 포함. 기존 표 컬럼 형식(`| 버전 | 날짜 | 변경 내용 |`)을 그대로 따른다.

> **frontmatter `version: 1.0`은 건드리지 않는다** — 변경이력이 이미 v1.5인데 frontmatter가 1.0으로 남아 있는 기존 불일치는 이 태스크 범위 밖이다 (→ H-10로 보고).

#### M-3 `opal/skills/opal-pilot-data-design/references/pipeline.json`

`model.pm_gate.gate.checklist`(`:14`) 4항목 중 1·2번만 교체. 3·4번(`"논리 속성명 = DICT 용어"`, `"물리 DBML 존재"`)은 **양 트랙 공통이므로 불변**.

```json
"checklist": [
  "{설계} 모델링 산출물 — 신규 트랙: 개념·논리·물리 / 역공학 트랙: 물리·논리",
  "트랙별 모드 순차 완료 — 신규: concept→logical→physical 3모드 / 역공학: physical→logical 2모드(개념 산출물 미요구)",
  "논리 속성명 = DICT 용어",
  "물리 DBML 존재"
]
```

**[MUST]** `task_steps[]` 15개 행의 `id`·`key`·`stage`·`item`, 그리고 `dict.pm_gate`·`ddl_migration.pm_gate`·`qa.pm_gate`의 `gate` 블록은 **전량 불변**. `gate.artifacts`는 빈 배열 유지 — 트랙 조건부 산출물을 `artifacts`에 넣으면 `gate_artifact_missing`으로 영구 차단된다.

> `qa.pm_gate.checklist`(`:22`)는 "docs/proposals/opal-data-design.md §3.4 4개 검증 항목 PASS"로 SSOT를 포인터 참조하므로 **M-1 (f) 수정만으로 자동 정합** — 무변경.

#### M-4 `opal/skills/op-data-model/SKILL.md`

**(a) §모드 선택 규칙 표** (`:54-61`) — 「기존 논리 ERD 주입」 행 다음에 1행 추가 (R-6):

| 상황 | 발동 모드 |
|------|----------|
| 기존 DB/DDL 스키마 주입 (역공학) | physical(역추출·정규화) → logical(역산) — **concept 미실행** |

기존 5개 행은 **불변**. 첫 행("pilot 파이프라인 MODEL 단계 → concept → logical → physical 순차 3모드")에 트랙 조건을 명시: `pilot 파이프라인 MODEL 단계 (신규 트랙)`.

표 하단 노트 1줄 추가:
> 역공학 트랙의 물리 역추출 절차는 `op-data-ddl` §Step 4(`sql2dbml`)를 참조한다 — 산출물은 이 스킬 physical 모드 경로(`{설계}/물리모델링/{프로젝트}.dbml`)에 저장한다.

**(b) 모드 2 logical 입력 전제** (`:105`) — 1줄 추가:
> 역공학 트랙 예외: 물리(DBML) 산출물을 입력으로 논리를 역산한다 (§모드 선택 규칙 참조).

**(c) 모드 3 physical 입력 전제** (`:155`) — 1줄 추가:
> 역공학 트랙 예외: 기존 DDL·ORM·DB 스키마를 입력으로 하며 논리 ERD 선행을 요구하지 않는다 (§모드 선택 규칙 참조).

**(d) §프로세스 Step 2 모드 결정** (`:196-200`) — 불릿 1개 추가:
> - 역공학 트랙 디스패치 시: physical부터 시작하고 concept은 실행하지 않는다

**(e) §변경이력** (`:308` 다음 행) — `1.1` 행 추가. 기존 표 컬럼 형식(`| 버전 | 일시(KST) | 변경 내용 |`)·버전 표기(접두사 `v` 없음)를 그대로 따른다. `(104)` 포함.

> 모드 1 concept 절(`:64-97`)·§품질 체크리스트(`:274-300`)·§저장 경로(`:248-270`)는 **불변** — 개념 모드는 신규 트랙에서 그대로 쓰인다.

#### M-5 `.opal/brain/pages/flow/opdd-pipeline-flow.md`

`:24` "↓ 개념 → 논리 → 물리 (순차 3모드)"를 트랙 분기로 교체:

```
  ↓ 신규 트랙: 개념 → 논리 → 물리 (3모드)
  ↓ 역공학 트랙: 물리 → 논리 (2모드, 개념 스킵)
```

frontmatter `updated: 2026-06-12` → 작업일로 갱신. `sources: [task:019]` → `[task:019, task:104]` 추가. 나머지 절(핵심 의존 제약·모드 경계·산출물 트리·관련 페이지)은 **불변**.

> brain 수정은 `brain-tool`의 index·링크 무결성 대상이다. 페이지 본문만 수정하고 `related`·파일명은 건드리지 않으므로 `brain-tool lint` 재실행으로 족하다.

---

## 3. 리스크 가설 표 (TEST-SCENARIO §1 입력)

| # | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|---|----------|-----------------|----------|--------------|-------------|
| H-1 | M-1 §3.4 / M-2 STEP 5 | QA 「사전 정합: 모든 컬럼명이 DICT 표준사전 등록 용어 (미등록 0)」가 역공학 트랙에서 구조적 달성 불가 — 기존 DB 컬럼명을 사전이 바꿀 수 없다 | 역공학 태스크가 QA에서 영구 미통과 | L1 문서 정합 | 역공학 트랙 QA 4항목을 순회하며 「사전 정합」 항목이 달성 가능한지 판정 |
| H-2 | M-1 → M-2 순서 | SSOT 원문과 opdd SKILL.md `[MUST]` 인용문의 **축자 불일치** (R-8 AC 직접 위반) | 스킬이 자기 인용문과 모순 → 워커가 어느 쪽을 따를지 미정 | L1 결정론 | M-1 (d)·(f) 확정 문안을 M-2 (b)·(e)에서 `grep -F` 완전일치로 대조 |
| H-3 | M-3 | `pipeline.json` JSON 파싱 실패 또는 `task_steps[]` 행 수·key 변경 | `state-tool init --rows-from` 전면 중단 — **기존 opdd 태스크 전건 호환 파손** | L1 결정론 | `python3 -m json.tool` 통과 + `task_steps[]` 길이 15 + key 15종 문자열 diff 0 |
| H-4 | M-2 (b)(c)(d)(e)(f), M-3 | 트랙 플래그 미사용 시 조건부 분기가 무조건 실행되어 신규 트랙 동작이 바뀜 (회귀 0 제약 위반) | 기존 사용자의 `//opdd` 호출 결과가 달라짐 | L1 문서 정합 | 트랙 미지정 경로를 따라 읽었을 때 `concept → logical → physical` 문구가 보존되는지 확인 |
| H-5 | M-2 (f) | 트랙 플래그가 모드 플래그 개수 검사에 섞여 `mode_flag_conflict` 오판 (`opal/skills/opal-pilot-data-design/SKILL.md:23`) | `//opdd --agentic --rev` 정상 호출이 거부됨 | L1 문서 정합 | §Harness `:23` 4번째 불릿과 §트랙 축 (1)의 제외 규정이 상호 참조되는지 확인 |
| H-6 | M-4 (b)(c) | logical·physical 「입력 전제」 본문이 역공학 예외를 반영하지 않아 표와 본문이 모순 | 워커가 첫 모드에서 입력 전제 미충족 블로커를 올림 | L1 문서 정합 | `//erm` 역공학 단독 호출 경로에서 physical 모드가 전제 미충족으로 막히지 않는지 확인 |
| H-7 | M-5 | brain 흐름 페이지에 「순차 3모드」 서술이 잔존 | brain 검색이 폐기된 규정을 반환 | L1 문서 정합 | `grep -n "순차 3모드" .opal/brain/pages/` 0건 |
| H-8 | M-4 (a) 노트 | 역공학 물리 역추출의 **실행 소유권**이 `op-data-model` physical 모드와 `op-data-ddl` §Step 4 사이에서 모호 | MODEL 단계 워커가 `sql2dbml`을 돌려도 되는지 판단 불가 | L1 문서 정합 | 노트가 "참조"인지 "실행 위임"인지 문언상 1의로 읽히는지 확인 |
| H-9 | M-1 | `docs/proposals/opal-data-design.md`에 변경이력 표 부재 — 개정 이력이 추적되지 않음 | 이 문서의 변경 추적 공백 (기존 상태 유지) | 보고만 | 변경이력 표 신설 여부를 소유자에게 질의 (이번 범위 밖) |
| H-10 | M-2 (g) | opdd SKILL.md frontmatter `version: 1.0` ↔ 변경이력 v1.5 기존 불일치 | 스킬 버전 신뢰도 저하 (기존 상태 유지) | 보고만 | frontmatter 동기화 여부를 소유자에게 질의 (이번 범위 밖) |

---

## 4. 실행 체크리스트

> 총 4개 Step | Phase 3개
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1 | 1 | 순차 | SSOT 원문 확정 — Step 2·3이 축자 인용 |
> | 2 | 2, 3 | 병렬 | 독립 파일 집합 (비중첩) |
> | 3 | 4 | 순차 | Step 2 확정 문구 반영 |

> **산출량 상한 준수**: Step 2가 2파일(같은 스킬 폴더), 나머지는 1파일. 3파일 초과 Step 없음. 동일 파일을 2개 Step이 건드리지 않음.

### Step 1: 설계 SSOT 트랙 분기 (R-8)
- [x] 완료
- **파일**: `docs/proposals/opal-data-design.md`
- **영역**: 문서 / **agent**: `opal-task-agent`
- **작업 내용**: §2.6 M-1 (a)~(f)를 수행한다. (a) §3.2 도식 주석 트랙 분기, (b) §3.2 단계 표 MODEL 행 트랙 분기, (d) §3.2.1 도입 문장을 확정 문안으로 교체, (e) §3.2.1 모드 의존 블록에 역공학 예외 1문장 추가, (f) §3.4 첫 항목 트랙 분기. **(c) §3.2 「핵심 순서 결정」 인용 블록(`:57-58`)은 절대 수정 금지** — opdd SKILL.md `:91`·`:123`·`:155`가 축자 인용 중이다. 변경이력 표를 **신설하지 않는다**.
- **완료 기준**: §3.2·§3.2.1·§3.4 세 절 각각에 「역공학 트랙에서 개념 모드가 제외된다」는 취지가 명시된다. `:57-58` 두 문장의 diff 0. §3.2 MODEL 행 의존 열이 `**DICT**`로 유지된다.
- **테스트**: `grep -n "DICT가 MODEL을" docs/proposals/opal-data-design.md`가 원문 그대로 1건. `grep -cn "역공학" docs/proposals/opal-data-design.md` ≥ 3.
- **의존**: 없음
- **커버 요구사항**: R-8

### Step 2: opdd 스킬 트랙 판정·실행 순서·게이트 개정 (R-1·R-2·R-3·R-4·R-5·R-7)
- [x] 완료
- **파일**: `opal/skills/opal-pilot-data-design/SKILL.md`, `opal/skills/opal-pilot-data-design/references/pipeline.json`
- **영역**: 문서(프레임워크 스펙) / **agent**: `opal-task-agent`
- **작업 내용**: §2.6 M-2 (a)~(g) 및 M-3을 수행한다. SKILL.md는 grep으로 대상 줄을 특정한 뒤 부분 편집(전체 재작성 금지). 순서: ① STEP 1 §트랙 판정 절 신설 → ② STEP 3 산문·`**실행 순서**`·`**이전 산출물**`·PM Gate 괄호 → ③ STEP 5 QA 첫 항목 → ④ §명시 모드 뒤 §트랙 축 4소절 신설 → ⑤ §변경이력 `v1.6` 행 → ⑥ pipeline.json `model.pm_gate.gate.checklist` 1·2번 항목 교체. STEP 3·STEP 5의 트랙 분기 문구는 **Step 1에서 확정한 SSOT 원문을 복사**한다.
- **완료 기준**: ① 트랙명 2종·플래그 2쌍·자동 감지 대상 3종·확인 절차·「플래그 우선」 규칙이 모두 기재. ② §트랙 축에 「모드 플래그 개수 검사에 트랙 플래그를 세지 않는다」 취지 문장 존재 + 미사용 시 현행 유지 명시. ③ 역공학 순서 문자열에 `concept` 0건, 신규 순서 문자열은 원문 보존. ④ pipeline.json `python3 -m json.tool` 통과 + `task_steps[]` 15행·key 15종 불변. ⑤ QA 첫 항목이 트랙 분기. ⑥ 변경이력 1행 추가.
- **테스트**:
  - `python3 -m json.tool opal/skills/opal-pilot-data-design/references/pipeline.json > /dev/null && echo OK`
  - `python3 -c "import json;d=json.load(open('opal/skills/opal-pilot-data-design/references/pipeline.json'));print(len(d['task_steps']),[s['key'] for s in d['task_steps']])"` → 15 + 기존 key 목록 일치
  - `grep -n "실행 순서" -A 4 opal/skills/opal-pilot-data-design/SKILL.md` → `reverse` 줄에 `concept` 미출현
  - `grep -n "mode_flag_conflict" opal/skills/opal-pilot-data-design/SKILL.md` → §Harness + §트랙 축 2건
  - Step 1 확정 문안 축자 대조: `grep -F "<§3.2.1 확정 문안>" opal/skills/opal-pilot-data-design/SKILL.md`
- **의존**: Step 1
- **커버 요구사항**: R-1, R-2, R-3, R-4, R-5, R-7(opdd 분)

### Step 3: op-data-model 모드 선택 규칙 확장 (R-6·R-7)
- [x] 완료
- **파일**: `opal/skills/op-data-model/SKILL.md`
- **영역**: 문서(프레임워크 스펙) / **agent**: `opal-task-agent`
- **작업 내용**: §2.6 M-4 (a)~(e)를 수행한다. (a) §모드 선택 규칙 표에 역공학 행 1행 추가 + 첫 행에 `(신규 트랙)` 조건 명시 + 표 하단 `op-data-ddl` §Step 4 포인터 노트 1줄, (b) 모드 2 logical 입력 전제 예외 1줄, (c) 모드 3 physical 입력 전제 예외 1줄, (d) §프로세스 Step 2에 불릿 1개, (e) §변경이력 `1.1` 행. 모드 1 concept 절·§품질 체크리스트·§저장 경로는 무변경.
- **완료 기준**: 표에 역공학 행이 1행 존재하고 그 발동 모드에 `concept`이 포함되지 않는다. logical·physical 두 「입력 전제」 문장이 역공학 트랙에서 모순되지 않는다. 변경이력 1행 추가.
- **테스트**:
  - `grep -n "역공학" opal/skills/op-data-model/SKILL.md` → 표 행 + 노트 + 입력 전제 2건 + Step 2 불릿 ≥ 5건
  - `grep -n "기존 DB/DDL" -A 1 opal/skills/op-data-model/SKILL.md` → 발동 모드 셀에 `concept` 미출현
  - `grep -n "^| 1.1 " opal/skills/op-data-model/SKILL.md` → 1건
- **의존**: Step 1
- **커버 요구사항**: R-6, R-7(op-data-model 분)

### Step 4: brain 흐름 페이지 갱신
- [x] 완료
- **파일**: `.opal/brain/pages/flow/opdd-pipeline-flow.md`
- **영역**: 문서 / **agent**: `opal-task-agent`
- **작업 내용**: §2.6 M-5를 수행한다. `:24` 흐름 서술을 트랙 분기 2줄로 교체, frontmatter `updated`를 작업일로 갱신, `sources`에 `task:104` 추가. 나머지 절 무변경. 수정 후 `~/.opal/tools/brain-tool/run.sh lint <프로젝트>` 실행.
- **완료 기준**: `grep -n "순차 3모드" .opal/brain/pages/` 0건. `brain-tool lint` exit 0.
- **테스트**: `grep -rn "순차 3모드" .opal/brain/` → 0건
- **의존**: Step 2
- **커버 요구사항**: (CLOSE 관련 문서 최신화 — D-11)

### 요구사항 → Step 매핑

| 요구사항 | Step | 대상 파일 |
|---------|------|----------|
| R-1 트랙 판정 규칙 신설 | Step 2 | opdd SKILL.md §STEP 1 |
| R-2 트랙 플래그 축 정의 | Step 2 | opdd SKILL.md §명시 모드 |
| R-3 MODEL 실행 순서 분기 | Step 2 | opdd SKILL.md §STEP 3 |
| R-4 MODEL PM Gate 체크리스트 분기 | Step 2 | pipeline.json |
| R-5 QA 검증 항목 분기 | Step 2 | opdd SKILL.md §STEP 5 |
| R-6 op-data-model 모드 선택 규칙 확장 | Step 3 | op-data-model SKILL.md |
| R-7 변경이력 갱신 | Step 2 + Step 3 | opdd SKILL.md, op-data-model SKILL.md |
| R-8 설계 SSOT 정합 | Step 1 | docs/proposals/opal-data-design.md |

---

## 5. QA 체크리스트

### 기능 테스트

- [ ] R-1: opdd SKILL.md §STEP 1에 트랙명 2종(`greenfield`/`reverse`)·플래그명(`--reverse`/`--rev`, `--greenfield`/`--gf`)·자동 감지 대상 3종·확인 절차가 모두 기재되고, 「플래그가 자동 감지보다 우선」이 명문화되었는가
- [ ] R-2: §트랙 축 절에 「모드 플래그 개수 검사에 트랙 플래그를 세지 않는다」 취지 문장과 「플래그 미사용 시 현행 동작 100% 유지」가 존재하는가
- [ ] R-3: 신규 트랙 순서 문자열이 `concept → logical → physical`로 보존되고, 역공학 트랙 순서 문자열에 `concept`이 0건인가
- [ ] R-4: `model.pm_gate.gate.checklist`가 트랙 조건부로 읽히고, JSON 파싱이 통과하며, `task_steps[]` 15행·key 15종이 불변인가
- [ ] R-5: STEP 5 QA 첫 항목이 역공학 트랙에서 논리↔물리 정합만 요구하는가
- [ ] R-6: op-data-model §모드 선택 규칙 표에 역공학 행이 1행 이상 존재하고 발동 모드에 `concept`이 없는가
- [ ] R-7: opdd SKILL.md `v1.6`·op-data-model `1.1` 변경이력 행이 각 1행 추가되고 `(104)`를 포함하는가
- [ ] R-8: SSOT §3.2·§3.2.1·§3.4 세 절에 역공학 트랙 개념 제외가 명시되고, opdd SKILL.md `[MUST]` 인용문과 **축자 일치**하는가

### 일관성 테스트

- [ ] 트랙 플래그 미사용 경로를 따라 읽었을 때 현행 문구가 100% 보존되는가 (회귀 0)
- [ ] `docs/proposals/opal-data-design.md:57-58` 두 인용 원문의 diff가 0인가 (opdd SKILL.md `:91`·`:123`·`:155` 3곳 파손 방지)
- [ ] §트랙 축 4소절 구성이 `opal/core/references/opal-harness.md` §2.5 서술 패턴과 정합하는가
- [ ] `op-data-ddl` SKILL.md가 무변경으로 남았는가 (범위 제외 준수)
- [ ] `~/.opal/` 배포 파일이 수정되지 않았는가 (`git status`에 `~/.opal/` 경로 0건)
- [ ] `git log`·워킹트리 상태 — 커밋·푸시·리셋이 실행되지 않았는가

### 문서 품질

- [ ] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가 (`docs/CONVENTIONS.md` §언어 규칙)
- [ ] 변경이력 일시가 `YYYY-MM-DD HH:mm` (KST)이고 `node ~/.opal/tools/date/date.js datetime`로 취득되었는가 (추측 금지)
- [ ] 각 파일의 **기존 변경이력 표 컬럼 형식**을 그대로 따랐는가 (opdd `| 버전 | 날짜 | 변경 내용 |` + `v` 접두사 / op-data-model `| 버전 | 일시(KST) | 변경 내용 |` + 접두사 없음)
- [ ] 인접 코드·문구를 개선하지 않았는가 (`~/.opal/PRINCIPLES.md` §3 Surgical Changes)
- [ ] brain 페이지 frontmatter 키가 English이고 `brain-tool lint`가 통과하는가

---

## 6. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| `pipeline.json` 파손 (H-3) | 기존 opdd 태스크 전건 `state-tool init` 실패 | Step 2 테스트에 JSON 파싱 + `task_steps[]` 길이 15 + key 목록 diff 0 검증을 완료 기준으로 고정 |
| SSOT ↔ 스킬 축자 불일치 (H-2) | 스킬이 자기 `[MUST]` 인용문과 모순 | Step 1을 선행 Phase로 분리하고, Step 2·3이 확정 문안을 **복사**하도록 명시. `grep -F` 완전일치 대조를 테스트로 고정 |
| SSOT `:57-58` 인용 원문 파손 | opdd SKILL.md 3곳(`:91`·`:123`·`:155`) 동시 파손 | Step 1 작업 내용에 「절대 수정 금지」 명시 + diff 0을 완료 기준화 |
| 신규 트랙 회귀 (H-4) | 기존 사용자 호출 결과 변경 | 모든 분기를 「신규 원문 보존 + 역공학 줄 추가」 형태로 작성. 원문 문자열 치환 대신 **행 추가**를 우선 |
| 역공학 트랙 QA 「사전 정합」 달성 불가 (H-1) | 역공학 태스크가 QA 영구 미통과 | **이번 범위 밖**(R-5는 「단계 간 정합」만 지정) — PM에게 후속 태스크 후보로 보고 |
| 역공학 실행 소유권 모호 (H-8) | MODEL 워커가 `sql2dbml` 실행 가부 판단 불가 | Step 3의 표 하단 노트를 「참조」로 1의 확정 (실행 위임 아님). `op-data-ddl` 무변경 유지 |
| 트랙 플래그 2쌍이 과설계로 판정될 여지 | Simplicity First 위반 지적 | §2.2에 양방향 필요 근거(오탐 시 신규 강제 경로)를 명시 — 소유자 판단으로 `--greenfield` 제거 가능하도록 단일 절에 격리 |
| 배포 반영 누락 | 소스만 수정되고 `~/.opal/`에 미반영 | 워킹트리 변경만 남기고 커밋·배포는 소유자 권한 — 완료 보고에 `install` 필요를 명시 |
