# PLAN: opal/skills 레지스트리 정합 + 분류 정리 + opal-brain 오기재 교정 + validate lint

> 작성일: 2026-06-18 | 입력: TASK.md, ANALYSIS.md
> 모드: Multi-Feature (R1~R4 4기능, ANALYSIS 영향 분류 명시)
> **v2.0 재설계** — PLAN 게이트에서 캡틴이 F-003 전제 오류(opal-brain≠pilot)를 지적, 리네임 철회 → 오기재 교정으로 스코프 변경. 상세는 §변경이력.

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

`opal-skills-registry.json`(스킬 SSOT)이 실제 `opal/skills/` 폴더와 어긋난 드리프트(dangling 2건 / 미등록 1건)와 그룹 오배치(3건)를 해소하고, `docs/PROJECT.md`가 `opal-brain`을 "오케스트레이터 / 브레인 4모드 Pilot"로 분류한 **오기재 1건을 operator(직접 실행 multi-mode) 성격으로 교정**하며, 재발 방지를 위해 기존 `skill-registry.js validate`(`opal/tools/skill-registry/skill-registry.js:277-392`)를 dangling error 격상 + unregistered 역방향 감지로 확장하고 단위 테스트를 신규 추가한다.

> **[F-003 재정의 — 캡틴 확정, 재논의 금지]** 초기 PLAN(v1.0)의 F-003은 "opal-brain → opal-pilot-brain 폴더 리네임 + alias opbr→opb + 전역 9파일 cascade"였으나 **전면 철회**됐다. `opal/skills/opal-brain/SKILL.md` 검증 결과 opal-brain은 pilot이 아니다 — (a) `init|ingest|query|lint`는 순차 단계 파이프라인이 아니라 **독립 4모드 라우터**(`opal/skills/opal-brain/SKILL.md:28-43` 모드 라우팅 표, frontmatter `pipeline: "MODE: init | ingest | query | lint"` `:14`), (b) **워커 디스패치 0건** — `brain-tool`(결정론적 CLI) 직접 호출 + LLM 페이지 작성뿐(`:24`), (c) STATE·Gate·단계 전환 없음. `:21` "단일 pilot 구조"는 "오케스트레이터+단계스킬로 미분할한 단일 스킬"의 느슨한 표기이지 orchestrator를 뜻하지 않는다. → **opal-brain은 operator로서 `opal` 그룹에 잔류, 폴더·name·alias(`opbr`)·triggers·전역 참조 전부 불변.** 변경 대상은 `docs/PROJECT.md`의 유형 오기재 1곳뿐.

본 태스크는 **전부 Framework 영역**(레지스트리/문서/도구)이며 EXECUTE 워커는 `opal-task-agent`로 고정한다(단, docs/ 갱신 Step은 PM 직접). 코드 변경(R4)을 제외한 R1~R3는 JSON/문서 편집으로 RED-first 트랙 대상이 아니다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | 레지스트리 드리프트 해소 (dangling 2건 제거 + 미등록 1건 등록 + 문서 정합) | R1 | P0 | 없음 |
| F-002 | 분류 그룹 재배치 (op-spec-validator→op-sdd, op-brain-ingest→신규 op-brain, opal-pilot-project-dev→opal-pilot) | R2 | P0 | 없음 |
| F-003 | opal-brain 오기재(Pilot) 교정 — `docs/PROJECT.md` 유형 표기 1곳 교정 + 불변 회귀 확인 (리네임 철회) | R3 | P0 | 없음 |
| F-004 | skill-registry validate 확장 (no-SKILL.md error 격상 + unregistered 역방향 감지 + 단위 테스트) | R4 | P0 | F-001, F-002 |

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 (드리프트 해소) ─┐
                       ├─► F-004 (validate 확장+테스트)
F-002 (그룹 재배치) ───┘

F-003 (opal-brain 오기재 교정) ── 독립 (단일 문서 교정, 다른 F와 무관)

근거: F-004 validate는 F-001/F-002 정합 완료 후 실행해야 dangling/unregistered
      0건 PASS를 검증할 수 있다. F-003은 PROJECT.md 단일 문서 1곳 교정이며
      레지스트리·폴더·alias를 건드리지 않으므로 F-001/F-002/F-004와 완전 독립이다.
      (v1.0의 "F-003이 F-001/F-002에 의존하고 F-004가 F-003에 의존" 사슬은 리네임
       철회로 소멸 — F-003이 더 이상 레지스트리를 변경하지 않기 때문.)
```

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨. ANALYSIS §5 R-1~R-7 중 **리네임 종속 리스크(R-1·R-2·R-5·R-7)는 리네임 철회로 소멸**, validate false positive(R-3·R-6) + 문서 잔존(R-4)만 유지·전환.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-3 | F-004 / `validateUnregistered(srcDirs)` (`skill-registry.js:373-380` 인근 신규) | standalone(`skills/` top-level) 폴더를 `opal/skills/`만 스캔 시 미등록 오판(false positive) | P1 | L1(단위: standalone clean exit 0) | TS-403 |
| H-4 | F-004 / 소스·배포 환경 구분 (`getReferencesDir()` `skill-registry.js:55-63` 의존) | 배포 환경(`~/.opal/references/`)에서 unregistered 스캔 실행 시 false positive | P1 | L1(단위: 배포 환경 모킹 시 unregistered 비활성) | TS-404 |
| H-5 | F-004 / no-SKILL.md warning→error 격상 (`skill-registry.js:379`) | dangling이 warning(exit 0)으로 남으면 R4 AC(exit 1) 미달 | P0 | L1(단위: dangling exit 1) | TS-401 |
| H-6 | F-001 / dangling 제거 후 문서 잔존 (`PROJECT.md:61`, `ARCHITECTURE.md:126,328`) | 레지스트리만 제거하고 문서 잔존 시 SSOT 불일치 재발 | P2 | L1(grep `op-sdd-tasks`/`opal-orchestrator` 잔존 0건) | TS-103 |
| H-8 | F-003 / opal-brain 불변 회귀 (`opal-skills-registry.json:670-684`, 폴더, alias·triggers, 전역 참조) | PROJECT.md 교정 작업 중 실수로 opal-brain 폴더·alias(`opbr`)·triggers·레지스트리 entry를 함께 건드리면 부트·`//opbr` 매칭·배포가 깨짐 (리네임 철회 회귀 가드) | P1 | L1(grep: opal-brain 폴더·`//opbr`·alias·전역 참조 **불변** = 변경 0건 확인) | TS-303 |

**가설 도출 근거 매핑**: H-3↔R-3(ANALYSIS §5), H-4↔R-6, H-5↔R4 AC, H-6↔R-4(ANALYSIS §5 ARCHITECTURE 잔존을 흡수). **H-8은 신규** — v1.0의 H-1(AGENT.md cascade 누락)·H-2(opbr 매칭 실패)·H-7(brain_tool.py 오갱신)은 모두 "리네임을 한다"는 전제에 종속됐으므로 리네임 철회로 **소멸**시키고, 대신 "리네임을 하지 않음(불변)"을 보장하는 회귀 가드 H-8로 격하·대체한다.

---

## 2. 기능별 분석

### F-001: 레지스트리 드리프트 해소

#### 2.1.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 레지스트리 | `opal/core/references/opal-skills-registry.json` | 스킬 SSOT — op-sdd 그룹 `op-sdd-tasks`(`:304-319`), opal 그룹 `opal-orchestrator`(`:618-629`) 삭제, op-sdd에 `op-sdd-action-plan` 신규 등록 | 수정 |
| 문서 | `docs/PROJECT.md` | `:61` op-sdd-tasks 행 삭제 | 수정 |
| 문서 | `docs/ARCHITECTURE.md` | `:126,328` opal-orchestrator 잔존 행 삭제 | 수정 |
| 스킬 | `opal/skills/op-sdd-action-plan/SKILL.md` | 등록 스키마 근거(name/alias/dispatched_by) — 읽기 전용 | 참조 |

#### 2.1.2 현재 구현
- `op-sdd-tasks`: 레지스트리 op-sdd 그룹에 잔존(`opal-skills-registry.json:304-319`)하나 폴더 부재. git commit `a940318`(feat(093))에서 물리 삭제, 기능은 op-sdd-plan으로 통합 (ANALYSIS §4.3). **리네임 매핑 아님 → 제거**.
- `opal-orchestrator`: 레지스트리 opal 그룹 잔존(`opal-skills-registry.json:618-629`), 폴더 부재. git commit `45d2118`(chore(086))에서 삭제, opal-pm.md로 대체 (ANALYSIS §4.3). **제거**.
- `op-sdd-action-plan`: 폴더 존재(`opal/skills/op-sdd-action-plan/SKILL.md:2-12`)·레지스트리 누락. name=`op-sdd-action-plan`, alias=null, dispatched_by=`opal-sdd-action-agent` (ANALYSIS §4.4). **op-sdd 그룹 등록**.

#### 2.1.3 영향 범위
- 직접: 레지스트리 op-sdd/opal 그룹 배열, PROJECT.md 컴포넌트 테이블, ARCHITECTURE.md 스킬 목록.
- 간접: `skill-registry.js`가 SSOT를 loadJsonFile로 로드 → F-004 validate가 정합 결과를 검증.
- 의존 사실: M2 = dangling 2건 모두 제거 (캡틴 확정, 리네임 매핑 아님).

---

### F-002: 분류 그룹 재배치

#### 2.2.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 레지스트리 | `opal/core/references/opal-skills-registry.json` | groups 재배치 — `op-spec-validator`(`:608-`)→op-sdd, `op-brain-ingest`(`:686-`)→신규 `op-brain`, `opal-pilot-project-dev`(`:594-`)→opal-pilot 그룹 이동 | 수정 |

#### 2.2.2 현재 구현
- 현행 최상위 그룹: `opal-pilot`, `op-dev`, `op-sdd`(`:255`), `op-data`(`:321`), `op-task`, `standalone`, `opal`(`:552`) (`opal-skills-registry.json:3-5`, ANALYSIS §1.2).
- `op-spec-validator`(`:608`)·`op-brain-ingest`(`:686`)·`opal-pilot-project-dev`(`:594`)가 모두 잡동사니 `opal` 그룹(`:552`)에 오배치 (ANALYSIS §3.1).
- 신규 그룹 `op-brain`은 `op-data` 패턴과 대칭 — op-* 단계 스킬 그룹 (멤버 1개여도 OK, op-* 단계스킬 네임스페이스).
- **opal-brain 자체는 그룹 이동 없음** — operator로서 `opal` 그룹 잔류 (F-003 §2.3 참조).

#### 2.2.3 영향 범위
- 직접: 레지스트리 groups 키 1개 신규(`op-brain`) + 3개 항목 이동. 이동 후 `opal` 그룹엔 부트/init/메타작성 스킬(skill-creator/agent-creator/skill-manager 등) + operator(opal-brain·onboarding·start·project-init 류)만 잔존 (R2 AC).
- 간접: 그룹은 매칭/디스패치에 직접 영향 없음(triggers 기반 매칭). 분류 일관성·validate 통과만 영향.

---

### F-003: opal-brain 오기재(Pilot) 교정 — 리네임 철회

#### 2.3.1 관련 파일 맵
ANALYSIS §4.1 인벤토리 중 **변경 대상은 PROJECT.md 1곳뿐**. 나머지 전역 참조는 **불변(회귀 가드)**.

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | `docs/PROJECT.md` `:79` | opal-brain 컴포넌트 행 — "유형: 오케스트레이터", "설명: 브레인 4모드 Pilot: init → ingest → query → lint" 오기재를 operator 성격으로 교정 | 수정 |
| **불변** | `opal/skills/opal-brain/` 폴더, `SKILL.md`, `references/brain-schema.md` | 폴더·name·alias(`opbr`)·triggers 전부 유지 | **변경 0건 (회귀 확인)** |
| **불변** | `opal/core/references/opal-skills-registry.json` `:670-684` | opal-brain entry(name/alias/triggers/paths/group=opal) 유지 | **변경 0건 (회귀 확인)** |
| **불변** | `opal/core/AGENT.md`, `opal/core/references/opal-harness.md`, `opal/skills/op-brain-ingest/SKILL.md`, `README.md`, `opal/tools/brain-tool/*`, `docs/proposals/opal-brain-design.md` | `opal-brain`·`//opbr`·`opbr` 전역 참조 유지 | **변경 0건 (회귀 확인)** |

#### 2.3.2 현재 구현
- `docs/PROJECT.md:79`: `| opal-brain | opbr | 오케스트레이터 | 브레인 4모드 Pilot: init → ingest → query → lint |` — **유형 컬럼이 "오케스트레이터", 설명에 "Pilot"** (직접 확인, `docs/PROJECT.md:79`).
- 동일 표(`:73-83` §주요 컴포넌트(Project Brain))의 다른 행: op-brain-ingest="단계 스킬", brain-tool="도구" — opal-brain만 "오케스트레이터/Pilot"로 오기재.
- opal-brain 실제 성격: 독립 4모드 라우터(`opal/skills/opal-brain/SKILL.md:28-43` 모드 라우팅 표) + brain-tool 직접 호출(`:24`), 워커 디스패치·STATE·Gate·단계 전환 없음. → **operator(직접 실행 multi-mode)**이며 orchestrator/Pilot이 아니다.
- alias `opbr`·triggers `["^opbr$","^opal-brain$",...]`(`SKILL.md:7-11`)·레지스트리 entry(`:670-684`)·전역 참조는 **전부 정상이며 변경 불요**.

#### 2.3.3 영향 범위
- 직접: `docs/PROJECT.md:79` 1행 (유형·설명 컬럼). 부속으로 동일 표 인접 캡션(`:75`·`:83`)은 brain 자산 설명이라 변경 불요 — 단 "Pilot" 단어가 §주요 컴포넌트(Project Brain) 블록 내에 다른 곳에도 있으면 함께 점검.
- 간접: **없음**. PROJECT.md는 표시·문서 SSOT이며 레지스트리·매칭·디스패치·배포에 코드 의존이 없다. 리네임/alias/cascade 0건이므로 install 재배포로 검증할 cascade도 없다.
- 의존 사실: M1 = 리네임 철회 (캡틴 확정). opal-brain 폴더·alias·triggers·전역 참조 불변 — TS-303 회귀로 보장.

---

### F-004: skill-registry validate 확장

#### 2.4.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/skill-registry/skill-registry.js` `:277-392` | `validate()` — no-SKILL.md error 격상(`:379`) + unregistered 역방향 감지 신규 | 수정 |
| 환경(테스트) | `opal/tools/skill-registry/tests/test-validate.js` (신규) | validate 단위 테스트 — dangling/clean/unregistered/배포환경/standalone 5케이스 | 신규 |

#### 2.4.2 현재 구현
- `validate()` **이미 존재** (`skill-registry.js:277-392`), 디스패치 `case 'validate':`(`:438-439`). exit 처리: `result.valid === false` 시 `process.exit(1)` (`:448-450`).
- 현행 dangling 처리: `no SKILL.md found at any path`를 **warnings**로만 push (`:379`) → exit 0. 격상 필요.
- paths 치환: `p.replace(/^~/, os.homedir()).replace(/\{project\}/g, process.cwd())` (`:376`).
- 환경 판별: `getReferencesDir()`(`:55-63`)가 소스 환경에서 `opal/core/references/`, 배포 후 `~/.opal/references/` 반환 (ANALYSIS §4.5).
- 테스트 부재: `opal/tools/skill-registry/`에 단위 테스트 파일 없음 (ANALYSIS §1.4, §4.5(e)).

#### 2.4.3 영향 범위
- 직접: `validate()` 함수 본문, 반환 객체에 unregistered 키 추가.
- 간접: `case 'validate'` 라우터·exit 로직(`:448-450`)은 `valid===false`로 이미 exit 1 처리 → errors에 push하면 자동 전파. 라우터 수정 최소.
- 의존 사실: R4 = 확장(신설 아님). ANALYSIS §4.5 설계 포인트 준수.

---

## 3. 기능별 설계

### F-001: 레지스트리 드리프트 해소

#### 3.1.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/opal-skills-registry.json` | 레지스트리 | op-sdd 그룹에서 `op-sdd-tasks` 객체 삭제(`:304-319`); opal 그룹에서 `opal-orchestrator` 객체 삭제(`:618-629`); op-sdd 그룹에 `op-sdd-action-plan` 객체 추가 | (→ D-6 §4.3·§4.4) |
| 2 | `docs/PROJECT.md` | 문서 | `:61` op-sdd-tasks 컴포넌트 행 삭제 | `docs/PROJECT.md:61` |
| 3 | `docs/ARCHITECTURE.md` | 문서 | `:126,328` opal-orchestrator 잔존 행 삭제 | `docs/ARCHITECTURE.md:126,328` |

#### 3.1.2 데이터 모델 설계 (op-sdd-action-plan 등록 스키마)

ANALYSIS §4.4 제안 스키마를 op-sdd 그룹 기존 항목 필드(stage/dispatched_by 보유 패턴)와 정렬:

```json
{
  "name": "op-sdd-action-plan",
  "alias": null,
  "description": "SDD ACT 전용 경량 PLAN 스킬 — SPEC.md + SPEC-PLAN.md + TEST-SCENARIOS.md + ACT 정의 기반 구현 청사진 작성",
  "triggers": ["^op-sdd-action-plan$"],
  "paths": [
    "{project}/.opal/skills/op-sdd-action-plan/SKILL.md",
    "~/.opal/skills/op-sdd-action-plan/SKILL.md"
  ],
  "stage": "PLAN(ACT)",
  "dispatched_by": ["opal-sdd-action-agent"]
}
```

> [MUST] 등록 전 op-sdd 그룹 실제 항목 스키마 필드(stage/dispatched_by 유무)를 그대로 따른다 (→ D-6 §4.4). 실제 SKILL.md(`opal/skills/op-sdd-action-plan/SKILL.md:2-12`)의 name·alias와 정확히 일치시킨다.
> [MUST] `docs/CONVENTIONS.md` §네이밍: 레지스트리 name은 폴더명과 1:1 일치해야 한다 (드리프트 방지 — F-004 validate 검사 대상).

#### 3.1.3 환경 변경
해당 없음.

#### 3.1.4 배치/마이그레이션
해당 없음.

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-101 | R1 AC | 산출물 검사 | 레지스트리에 op-sdd-tasks·opal-orchestrator 객체 0건, op-sdd-action-plan 1건 존재 (jq/grep) |
| TS-102 | R1 AC | 기능 테스트 | `node skill-registry.js validate` → dangling·unregistered 0건 리포트 (F-004 완료 후 통합 검증) |
| TS-103 | R1 AC, H-6 | 산출물 검사 | `grep -rn 'op-sdd-tasks\|opal-orchestrator' opal/ docs/` 잔존 0건 (변경이력 제외) |

---

### F-002: 분류 그룹 재배치

#### 3.2.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/opal-skills-registry.json` | 레지스트리 | groups에 `op-brain` 키 신규 생성; `op-brain-ingest`(`:686`) 객체를 opal→op-brain 이동; `op-spec-validator`(`:608`) 객체를 opal→op-sdd 이동; `opal-pilot-project-dev`(`:594`) 객체를 opal→opal-pilot 이동 | (→ D-6 §3.1) |

#### 3.2.2 데이터 모델 설계 (groups 재배치)

- 그룹 이동은 **객체 자체를 배열 간 이동**(name/alias/triggers/paths 보존), 필드 변경 없음.
- 이동 결과 검증 기준(R2 AC): `op-sdd`에 op-spec-validator 포함, 신규 `op-brain`에 op-brain-ingest 포함, `opal-pilot`에 opal-pilot-project-dev 포함, `opal` 그룹엔 부트/init/메타작성/operator 스킬(skill-creator `:631`, agent-creator `:644`, skill-manager `:657`, **opal-brain 잔류** 등)만 남는다.

> [MUST] `op-brain` 신규 그룹은 `op-data`(`:321`) 그룹 패턴과 대칭이어야 한다 (op-* 단계 스킬 그룹, 멤버 1개여도 정당) (→ D-6 §3.1).
> [MUST] **opal-brain은 그룹 이동 없음** — operator로서 `opal` 그룹 잔류 (F-003 확정, 리네임 철회) (→ TASK 확정사항 §1).

#### 3.2.3 환경 변경
해당 없음.

#### 3.2.4 배치/마이그레이션
해당 없음.

#### 3.2.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-201 | R2 AC | 산출물 검사 | op-spec-validator∈op-sdd, op-brain-ingest∈op-brain, opal-pilot-project-dev∈opal-pilot (jq 그룹 확인) |
| TS-202 | R2 AC | 산출물 검사 | `opal` 그룹에 op-*·pilot 단계 스킬 0건 (부트/init/메타작성/operator만 잔존, opal-brain 포함 확인) |
| TS-203 | R2 AC | 기능 테스트 | `node skill-registry.js list --group=op-brain` → op-brain-ingest 출력, validate exit 0 |

---

### F-003: opal-brain 오기재(Pilot) 교정 — 리네임 철회

#### 3.3.1 파일 변경 계획

**수정 (단일 문서 1곳)**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `docs/PROJECT.md` `:79` | 문서 | opal-brain 행의 "유형: 오케스트레이터"→operator 성격, "설명: 브레인 4모드 Pilot: …"→독립 4모드 라우터 성격으로 교정 + 변경이력 행(KST + 029) | `docs/PROJECT.md:79`, (→ D-7 §1.1) |

> [MUST] 교정 대상은 **PROJECT.md 1곳뿐**. opal-brain 폴더·name·alias(`opbr`)·triggers·레지스트리 entry(`:670-684`)·전역 참조(`opal/core/AGENT.md`·`opal-harness.md`·`op-brain-ingest/SKILL.md`·`README.md`·`brain_tool.py`·`opal-brain-design.md`)는 **일절 변경 금지(불변 회귀)** (→ TASK 확정사항 §1, H-8).

#### 3.3.2 교정 문안 설계 (PROJECT.md:79 최종형)

현행:
```
| `opal-brain` | opbr | 오케스트레이터 | 브레인 4모드 Pilot: init → ingest → query → lint |
```

교정안(권고):
```
| `opal-brain` | opbr | operator (멀티모드) | 브레인 4모드 라우터: init · ingest · query · lint (단계 파이프라인·워커 디스패치 없음, brain-tool 직접 호출) |
```

설계 근거:
- "오케스트레이터"→"operator (멀티모드)": opal-brain은 워커 디스패치·STATE·Gate가 없는 직접 실행 스킬 (`opal/skills/opal-brain/SKILL.md:24,28-43`). operator는 onboarding/start/project-init/skill-creator와 동일 부류.
- "브레인 4모드 Pilot: init → ingest → query → lint"→"4모드 라우터: init · ingest · query · lint": `→` 화살표(순차 파이프라인 함의) 제거 후 `·`(병렬 독립 모드)로 변경 — `init|ingest|query|lint`는 순차 단계가 아니라 모드 라우팅 분기이기 때문 (`SKILL.md:28-43`, frontmatter `pipeline: "MODE: ..."` `:14`).
- alias 컬럼 `opbr` **유지** (리네임 철회).

> [MUST] "Pilot"·"오케스트레이터" 단어를 opal-brain 행에서 제거하되, **다른 행(opal-pilot-sdd·opal-pilot-gc 등 실제 pilot)의 "오케스트레이터/Pilot" 표기는 건드리지 않는다** (→ TASK R3 AC).
> [MUST] §주요 컴포넌트(Project Brain) 블록 캡션(`:75`·`:83`)에 "Pilot"·"오케스트레이터" 잔존이 있으면 함께 교정하되, brain 자산·`//opbr` 커맨드 표기(`:83`의 `//opbr init`)는 alias 불변이므로 **유지**한다.

> 최종 문안(operator 명칭·설명 표현)은 PM이 EXECUTE 시 PROJECT.md 표 톤에 맞춰 미세 조정 가능 — 핵심은 (a) "오케스트레이터/Pilot" 분류 제거, (b) operator/멀티모드 라우터 성격 명시, (c) alias·커맨드 표기 불변.

#### 3.3.3 환경 변경
해당 없음. **install 재배포 불요** — PROJECT.md는 문서 SSOT이며 배포 cascade가 없다 (리네임 0건이므로 v1.0의 install 재배포 검증 Step 소멸).

#### 3.3.4 배치/마이그레이션
해당 없음 (폴더 리네임 없음 — `git mv` 불요).

#### 3.3.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-301 | R3 AC | 산출물 검사 | `docs/PROJECT.md:79` opal-brain 행에 "오케스트레이터"·"Pilot" 표기 0건, operator/멀티모드 라우터 성격 기재 |
| TS-303 | R3 AC, H-8 | 산출물 검사 (불변 회귀) | `git diff --stat`에서 `opal/skills/opal-brain/`·`opal-skills-registry.json`(opal-brain entry)·`opal/core/AGENT.md`·`README.md`·`brain_tool.py` **변경 0건**; `grep -rn '//opbr\|\bopbr\b\|opal-brain' opal/ scripts/ README.md`가 v2.0 작업 전과 **동일**(불변) 확인 |

---

### F-004: skill-registry validate 확장

#### 3.4.1 파일 변경 계획

**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/tools/skill-registry/tests/test-validate.js` | 환경 | validate 단위 테스트 — dangling/clean/unregistered/배포환경/standalone 5케이스 | (→ D-2 §4.5(d)(e)) |

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/skill-registry/skill-registry.js` | 도구 | `:379` no-SKILL.md를 warnings→errors push (격상); `validateUnregistered()` 신규 + validate()에서 소스 환경 조건부 호출; 반환 객체에 `unregistered` 키 추가 | (→ D-2 §4.5) |

#### 3.4.2 API·함수 시그니처 설계

**(a) no-SKILL.md error 격상** (`skill-registry.js:379`):
```
// 현행:  if (!found) warnings.push(`${skill.name}: no SKILL.md found at any path`);
// 변경:  if (!found) errors.push(`${skill.name}: dangling — no SKILL.md found at any path`);
```
→ errors 비어있지 않으면 `valid:false` → 라우터(`:448-450`)가 자동 exit 1. (H-5)

**(b) unregistered 역방향 감지** (신규 함수, 소스 환경 전용):
```js
/**
 * 소스 레포의 스킬 폴더를 스캔하여 레지스트리 미등록 폴더를 감지한다.
 * @param {string} cwd
 * @param {Set<string>} registeredNames - 레지스트리 등록 스킬명 집합
 * @returns {string[]} unregistered 폴더명 목록
 */
function validateUnregistered(cwd, registeredNames) {
  const srcDirs = [
    path.resolve(cwd, 'opal', 'skills'),  // opal-pilot-*, op-*, opal-*
    path.resolve(cwd, 'skills'),           // standalone (api-analyzer 등) — H-3 false positive 방지
  ];
  const unregistered = [];
  for (const dir of srcDirs) {
    if (!fs.existsSync(dir)) continue;
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      if (!entry.isDirectory()) continue;
      if (!fs.existsSync(path.join(dir, entry.name, 'SKILL.md'))) continue;
      if (!registeredNames.has(entry.name)) unregistered.push(entry.name);
    }
  }
  return unregistered;
}
```

**(c) validate() 통합** (소스 환경 판별로 false positive 방지 — H-4):
```
// validate() 내부, names 집계 후:
const refDirIsSource = refDir.includes(path.join('opal', 'core', 'references'));
if (refDirIsSource) {                       // 소스 환경 전용 (배포 환경 비활성)
  const unreg = validateUnregistered(process.cwd(), names);
  for (const n of unreg) errors.push(`${n}: unregistered — folder exists but not in registry`);
}
// 반환 객체에 unregistered 키 추가
```
> [MUST] unregistered 스캔은 `opal/skills/` + top-level `skills/` **양쪽**을 스캔한다 (standalone 오판 방지) (→ D-2 §4.5(c), H-3).
> [MUST] unregistered 감지는 **소스 환경 전용**. `getReferencesDir()`가 `opal/core/references/` 반환 시에만 활성, 배포 환경(`~/.opal/references/`)에서는 비활성 (→ D-2 §4.5(c), H-4).
> [MUST] `docs/CONVENTIONS.md` §@header: skill-registry.js 신규 함수에 @header 주석 규칙을 따른다 (프로젝트 컨벤션 — 기존 파일 패턴 확인 후 적용).

**(d) 단위 테스트 케이스** (`tests/test-validate.js`):
- TC1 clean: 정합 fixture → exit 0, errors 0
- TC2 dangling: 폴더 없는 레지스트리 항목 → errors에 `dangling` 포함, exit 1
- TC3 unregistered: 등록 없는 폴더 fixture → errors에 `unregistered` 포함, exit 1
- TC4 배포환경: refDir이 배포 경로일 때 unregistered 비활성 (false positive 없음)
- TC5 standalone: top-level `skills/` 폴더가 등록되어 있으면 unregistered 오판 없음 (H-3)

#### 3.4.3 환경 변경
- 테스트 실행: Node.js 내장 `node:assert`/`node:test` 또는 단순 assert 스크립트 (프로젝트 기존 JS 테스트 패턴 확인 후 정렬). 신규 패키지 없음.

#### 3.4.4 배치/마이그레이션
해당 없음.

#### 3.4.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-401 | R4 AC, H-5 | 기능 테스트 | dangling fixture → validate exit 1 + dangling 리포트 |
| TS-402 | R4 AC | 기능 테스트 | clean(정합) → validate exit 0 |
| TS-403 | R4 AC, H-3 | 기능 테스트 | unregistered 폴더 fixture → exit 1; standalone 등록 폴더는 오판 없음 |
| TS-404 | R4 AC, H-4 | 기능 테스트 | 배포 환경 모킹 시 unregistered 스캔 비활성 (false positive 0건) |
| TS-405 | 완료기준 ④ | 회귀 테스트 | `node tests/test-validate.js` 전 케이스 PASS |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001, F-002, F-003 | 1, 2, 3, 4 | opal-task-agent / PM 직접 | Step 1 후 Step 2·3·4 병렬 | 레지스트리 정합(R1·R2) + 문서 정합(PROJECT/ARCHITECTURE) + opal-brain 오기재 교정(R3). R3는 단일 문서라 Phase 1에 병합 |
| 2 | F-004 | 5, 6 | opal-task-agent | 순차 (RED-first) | validate 확장 + 단위 테스트. Phase 1 정합 완료 후 validate가 exit 0 PASS해야 함 |

> **Phase 간 의존**: Phase 1(레지스트리 정합)은 Phase 2 validate의 dangling/unregistered 0건 검증의 전제. **F-003(R3)은 레지스트리·폴더 불변이므로 validate 결과에 영향 없음** — Phase 1 내 독립 Step으로 병합 가능(v1.0의 별도 리네임 Phase 소멸). R3은 단일 문서 교정이라 R1(PROJECT.md 편집)과 같은 파일을 만지므로 동일 에이전트로 묶거나 순차 처리하여 충돌 회피.

> **R3 ↔ R1 파일 충돌 주의**: F-001 Step 2(PROJECT.md:61 행 삭제)와 F-003 Step 4(PROJECT.md:79 교정)는 **동일 파일 `docs/PROJECT.md`**를 수정한다. 파일 충돌 방지를 위해 두 변경을 **하나의 PM 직접 작업으로 묶거나** 순차 처리한다(§4.3 참조).

### 4.2 실행 체크리스트
> 총 6개 Step | Phase 2개 | 실행 모드: **복잡** (Step 6개·코드+문서+도구 혼합·다중 모듈·RED-first 트랙)

#### Step 1: 레지스트리 드리프트·그룹 재배치 통합 수정 (단일 파일)
- [x] 완료
- **소속 기능**: F-001, F-002
- **영역**: 레지스트리
- **agent**: opal-task-agent
- **파일**: `opal/core/references/opal-skills-registry.json`
- **작업 내용**: ① op-sdd-tasks 객체(`:304-319`) 삭제 ② opal-orchestrator 객체(`:618-629`) 삭제 ③ op-sdd 그룹에 op-sdd-action-plan 등록(§3.1.2 스키마) ④ groups에 `op-brain` 키 신규 ⑤ op-brain-ingest(`:686`)→op-brain, op-spec-validator(`:608`)→op-sdd, opal-pilot-project-dev(`:594`)→opal-pilot 이동 ⑥ **opal-brain entry(`:670-684`)는 불변(opal 그룹 잔류)** ⑦ 레지스트리 `version`/`updated_at` 갱신 + 변경이력(KST + 태스크 029)
- **완료 기준**: jq로 op-sdd-tasks·opal-orchestrator 0건, op-sdd-action-plan 1건, op-brain 그룹 존재, 3개 항목 정합 그룹 배치, **opal-brain은 opal 그룹·alias opbr 유지** 확인. JSON 파싱 유효(`node -e "require('./...')"`)
- **테스트**: TS-101, TS-201, TS-202
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: ARCHITECTURE.md opal-orchestrator 잔존 행 삭제
- [x] 완료
- **소속 기능**: F-001
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/ARCHITECTURE.md`
- **작업 내용**: `:126,328` opal-orchestrator 잔존 행 삭제 + 변경이력 행 추가(KST + 029)
- **완료 기준**: `grep -n 'opal-orchestrator' docs/ARCHITECTURE.md` 0건
- **테스트**: TS-103
- **실행 방법**: direct
- **의존**: Step 1 (레지스트리 정합 후 문서 정합)

#### Step 3: PROJECT.md 통합 교정 (op-sdd-tasks 삭제 + opal-brain 오기재 교정)
- [x] 완료
- **소속 기능**: F-001, F-003
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/PROJECT.md`
- **작업 내용**: ① `:61` op-sdd-tasks 컴포넌트 행 삭제 (F-001) ② `:79` opal-brain 행 "오케스트레이터/브레인 4모드 Pilot" → operator(멀티모드)/4모드 라우터로 교정 (§3.3.2 문안, F-003) ③ §주요 컴포넌트(Project Brain) 블록(`:75,83`)에 "Pilot/오케스트레이터" 잔존 점검·교정(단 `//opbr` 커맨드·brain 자산 표기는 alias 불변 유지) ④ 변경이력 행(KST + 029). **동일 파일 2개 변경이므로 단일 작업으로 묶어 충돌 회피**
- **완료 기준**: `grep -n 'op-sdd-tasks' docs/PROJECT.md` 0건; `:79` opal-brain 행에 "오케스트레이터"·"Pilot" 0건 + operator/라우터 성격 기재; opal-brain의 alias 컬럼 `opbr`·`//opbr` 커맨드 표기 유지
- **테스트**: TS-103, TS-301
- **실행 방법**: direct
- **의존**: Step 1

#### Step 4: opal-brain 불변 회귀 확인 (리네임 철회 가드)
- [x] 완료
- **소속 기능**: F-003
- **영역**: 문서
- **agent**: PM 직접
- **파일**: (검증 전용) `opal/skills/opal-brain/`, `opal-skills-registry.json`, `opal/core/AGENT.md`, `README.md`, `opal/tools/brain-tool/*`
- **작업 내용**: opal-brain 폴더·name·alias(`opbr`)·triggers·레지스트리 entry·전역 참조가 v2.0 작업 전과 **변경 0건**임을 확인 (리네임 철회 회귀 가드 H-8). Step 1·3에서 실수로 건드리지 않았는지 grep + git diff로 검증
- **완료 기준**: `git diff --stat`에서 `opal/skills/opal-brain/` 변경 0건; `git diff opal-skills-registry.json`에 opal-brain entry(name/alias/triggers/group) 변경 없음; `grep -rn '//opbr\|\bopbr\b\|opal-brain' opal/ scripts/ README.md` 결과가 작업 전과 동일(불변)
- **테스트**: TS-303
- **실행 방법**: direct
- **의존**: Step 1, Step 3 (정합·교정 완료 후 불변 확인)

#### Step 5: validate 단위 테스트 작성 (RED-first)
- [ ] 완료
- **소속 기능**: F-004
- **영역**: 환경(테스트)
- **agent**: opal-task-agent (RED 작성자 = opal-test-agent mode:red 권장, §7 참조)
- **파일**: `opal/tools/skill-registry/tests/test-validate.js` (신규)
- **작업 내용**: §3.4.2(d) TC1~TC5 작성. RED 단계에서 확장 전 코드 대상 실패(dangling/unregistered 미검출) 증거 기록 후 Step 6 GREEN 진입
- **완료 기준**: RED 시 실패(exit≠0 또는 미검출) 증거 기록 → Step 6 후 전 케이스 PASS
- **테스트**: TS-405
- **실행 방법**: sub-agent
- **의존**: Step 1 (정합 fixture 기준 마련) — Step 6보다 선행(작성자≠구현자)

#### Step 6: validate 확장 (no-SKILL.md error 격상 + unregistered 감지)
- [ ] 완료
- **소속 기능**: F-004
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/skill-registry/skill-registry.js`
- **작업 내용**: §3.4.2 (a)(b)(c) 적용 — `:379` errors 격상, `validateUnregistered()` 신규(양쪽 폴더 스캔), 소스 환경 조건부 호출, 반환 객체 `unregistered` 키 추가, @header/변경이력(KST + 029)
- **완료 기준**: Step 5 RED 테스트가 GREEN 전환(전 케이스 PASS) + `node skill-registry.js validate` 현행 정합 레포에서 exit 0 (완료기준 ①②④ 통합 PASS)
- **테스트**: TS-401~TS-405, TS-102
- **실행 방법**: sub-agent
- **의존**: Step 5 (RED-first: 테스트 선행), Step 1 (정합 완료 후 exit 0 검증)

### 4.3 병렬/순차 판별 근거
| 관계 | 근거 |
|------|------|
| F-001 ∥ F-002 (Step 1 내 통합) | 동일 레지스트리 파일 → 파일 충돌 방지 위해 1 Step 묶음(순차 편집) |
| Step 2 ∥ Step 3 | 독립 문서(ARCHITECTURE.md vs PROJECT.md), Step 1 완료 후 병렬 가능 |
| Step 3 내 F-001+F-003 묶음 | **동일 파일 `docs/PROJECT.md`** (`:61` 삭제 + `:79` 교정) → 파일 충돌 방지 위해 단일 작업으로 묶음 |
| Step 4 ← Step 1, 3 | 불변 회귀는 레지스트리·PROJECT.md 작업 완료 후 "건드리지 않았음"을 검증 |
| Step 5 → Step 6 | RED-first: 테스트(RED) 선행, 구현(GREEN) 후행, 작성자≠구현자 |
| Phase 1 → Phase 2 | validate exit 0 검증은 레지스트리 정합(Step 1) 완료가 전제 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA
| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | dangling 2건 제거 + 미등록 1건 등록 + 문서 정합 | TS-101, TS-103 | 레지스트리·PROJECT.md·ARCHITECTURE.md에서 dangling 0건, op-sdd-action-plan 등록 |
| F-002 | 그룹 3건 재배치 + opal 그룹 정화(opal-brain 잔류) | TS-201, TS-202, TS-203 | 3항목 정합 그룹 배치, opal 그룹에 단계 스킬 0건, opal-brain은 opal 잔류 |
| F-003 | opal-brain 오기재 교정 + 불변 회귀 | TS-301, TS-303 | PROJECT.md:79에서 "오케스트레이터/Pilot" 0건·operator 성격 기재; 폴더·alias·entry·전역 참조 변경 0건 |
| F-004 | validate dangling/unregistered 검출 + 테스트 PASS | TS-401~TS-405 | dangling/unregistered exit 1, clean exit 0, false positive 0건 |

### 5.2 회귀 테스트
- [ ] `node skill-registry.js match`/`list`/`get` 기존 명령 정상 동작 (validate 확장이 타 명령 비파괴)
- [ ] `node skill-registry.js match '//opbr'` → opal-brain 매칭 **유지** (리네임 철회 → alias 불변, H-8)
- [ ] `opal/tools/brain-tool/tests/test_brain_tool.py` PASS (domain 태그 미변경)

### 5.3 코드/문서 품질
- [ ] `docs/CONVENTIONS.md` §네이밍·§@header 준수 (skill-registry.js 신규 함수)
- [ ] 수정 레지스트리·문서·도구에 변경이력/버전 행 추가 (KST + 태스크 029)
- [ ] 배포 경계 준수: `~/.opal/` 직접 편집 0건, 프로젝트 소스만 수정
- [ ] STATE.md 직접 편집 0건 (state-tool로만)

### 5.4 보안
- [ ] validateUnregistered fs 접근이 cwd 하위로 한정 (path traversal 없음)
- [ ] 신규 코드에 하드코딩 시크릿/토큰 없음
- [ ] 레지스트리 JSON에 민감정보 미포함

---

## 6. 복잡도 판별
| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 6개 | 복잡 |
| 변경 파일 수 | 4개 (레지스트리·PROJECT.md·ARCHITECTURE.md·skill-registry.js) + 테스트 신규 1 | 복잡 |
| 모듈 범위 | 다중 (레지스트리·문서·도구) | 복잡 |
| 작업 유형 | 개선(드리프트 해소·오기재 교정) + 코드 변경(validate) | 복잡 |
| 외부 의존성 | 없음 (신규 패키지 0) | 단순 |
| **실행 모드** | **복잡** | Step 6개·RED-first 트랙·코드 변경 포함 |

> v1.0(9 Step·12+파일) 대비 대폭 축소 — 리네임 cascade(9파일 동시 수정)와 install 재배포 검증이 소멸. 단, RED-first 트랙(F-004)과 다중 모듈이 남아 복잡 모드 유지.

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지
```
Batch 1 (Phase 1): opal-task-agent[Step1 레지스트리] → 완료 후 PM[Step2 ARCHITECTURE ∥ Step3 PROJECT.md 통합] → PM[Step4 불변 회귀 확인]
Batch 2 (Phase 2): opal-test-agent(mode:red)[Step5 RED] → opal-task-agent[Step6 GREEN]
```
**그룹핑 근거**: 동일 레지스트리 파일(Step1)은 단일 에이전트. PROJECT.md를 만지는 F-001 일부(Step3①)와 F-003(Step3②)은 동일 파일이므로 Step3에 묶어 충돌 회피. RED/GREEN은 작성자≠구현자 분리.

### C-2. 스킬 요구사항
- 기존 스킬로 충족 (op-dev-execute가 Step 디스패치). 신규 스킬 갭 없음 — JSON 편집/문서 교정/JS 구현은 범용 작업.

### C-3. 도구 요구사항
- CLI: `node`(skill-registry.js·테스트 실행), `grep`/`jq`/`git diff`(검증).
- MCP: 불필요. 신규 패키지: 없음 (Node 내장 assert/test).
- **install 재배포 불요** — 리네임 cascade 0건, PROJECT.md는 문서 SSOT (v1.0 install Step 소멸).

### C-4. 테스트 전략
- **RED-first 적용**: F-004(validate 코드 + 테스트). `red-first.md §1.5` "비즈니스 로직/버그 수정(회귀 방지)" + self-confirming 위험(테스트 작성자=구현자 회피) 해당 → **RED-first 트랙 적용**. Step 5(RED, opal-test-agent mode:red) → Step 6(GREEN, opal-task-agent), `verify --red-check` ON.
- **구현-후-검증 트랙**: F-001/F-002/F-003 = JSON·문서 편집(설정·문서, 행위 불변) → `red-first.md §1.5` "설정·문서" 트랙. grep/jq/git diff 산출물 검사로 검증.
- 회귀: skill-registry 기존 명령(특히 `match '//opbr'` 유지 확인) + brain-tool 테스트(§5.2).
- 최종 통합: Step 6에서 완료기준 ①②④ 검증, Step 3·4에서 완료기준 ③ 검증.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 레지스트리/문서 | JSON, Markdown | (해당 스킬 없음 — 직접 편집) |
| 도구 | Node.js (skill-registry.js, 단위 테스트) | (해당 스킬 없음 — 내장 assert) |

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| (없음) | 모든 분석 대상이 프로젝트 내부 파일 — 외부 라이브러리 조회 불필요 (ANALYSIS §2) |

### 8.3 참조 문서 (설계 결정 근거)
| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | opal-skills-registry.json | `opal/core/references/opal-skills-registry.json` | 정합·재그룹 대상 SSOT (`:255,304,321,552,594,608,618,670,686`) |
| D-2 | 소스 | skill-registry.js | `opal/tools/skill-registry/skill-registry.js` | validate 확장 근거 (`:55-63,277-392,438-450`) |
| D-3 | 소스 | opal-brain SKILL.md | `opal/skills/opal-brain/SKILL.md` | opal-brain≠pilot 검증(모드 라우터·brain-tool 직접 호출) (`:14,21,24,28-43`) |
| D-4 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 네이밍·@header·변경이력·배포 경계 규칙 (`:14,91,170,194,200`) |
| D-5 | 설계 | install-mac.sh | `scripts/install-mac.sh` | 폴더 동적 순회 배포(소스 수정 불요) (`:923-934`) |
| D-6 | 설계 | ANALYSIS.md | `tasks/029-.../ANALYSIS.md` | 인벤토리·dangling 판정·validate 설계·리스크 (§4.1~§4.6, §5) |
| D-7 | 설계 | PROJECT.md | `docs/PROJECT.md` | op-sdd-tasks 행(`:61`)·opal-brain 오기재 교정 대상(`:79`) |
| D-8 | 설계 | red-first.md | `opal/core/references/harness/red-first.md` | RED-first 트랙 적용 판단 (§1.5) |
| D-9 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | 인용 의무·§7 용어 일관성 |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §3.1 참조.

---

## 9. 리스크 및 대응 (기능-리스크 연결)
| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| H-3 | validate false positive (standalone `skills/` top-level 미스캔) | F-004 | 중간 | `opal/skills/`+`skills/` 양쪽 스캔, TC5 standalone 케이스 (TS-403) |
| H-4 | validate 소스/배포 환경 미구분 → 배포 환경 false positive | F-004 | 중간 | getReferencesDir 소스 판별로 unregistered 조건부, TC4 (TS-404) |
| H-5 | no-SKILL.md warning 잔존 시 dangling exit 0 (AC 미달) | F-004 | 높음 | `:379` errors 격상, TC2 dangling exit 1 (TS-401) |
| H-6 | dangling 제거 후 문서 잔존(PROJECT.md:61·ARCHITECTURE.md) | F-001 | 낮음 | Step 2·3 분리 + grep 검증 (TS-103) |
| H-8 | opal-brain 불변 회귀 — PROJECT.md 교정 중 폴더·alias·entry·전역 참조 실수 변경 | F-003 | 중간 | Step 4 불변 회귀 가드 — git diff·grep으로 변경 0건 확인, `match '//opbr'` 유지 (TS-303, §5.2) |

> **v1.0 대비 제거된 리스크**: R-1(AGENT.md //opbr cascade 누락), R-2(M1 완전 제거로 //opbr 매칭 실패), R-5/R-7(brain_tool.py 오갱신·용어 일관성 cascade) — 모두 "리네임을 수행한다"는 전제에 종속됐으므로 **리네임 철회로 소멸**. 리네임 종속 리스크를 제거하고, 반대로 "리네임을 하지 않음(불변)"을 보장하는 H-8 회귀 가드로 대체했다.

---

> 변경이력
> | 버전 | 일시(KST) | 작업자 | 변경 내용 |
> |------|----------|--------|----------|
> | 1.0 | 2026-06-18 | opal-plan-agent (태스크 029) | PLAN.md 최초 작성 — R1~R4 4기능, 9 Step, 4 Phase, RED-first(F-004) 적용 |
> | 2.0 | 2026-06-18 | opal-plan-agent (태스크 029) | **F-003 리네임 철회→오기재 교정 재설계** (PLAN 게이트 캡틴 지적: opal-brain은 pilot 아님 — 독립 4모드 라우터·워커 디스패치 0건). F-003을 "opal-brain→opal-pilot-brain 리네임+전역 9파일 cascade"에서 "docs/PROJECT.md:79 오기재 1곳 교정+불변 회귀 확인"으로 축소. F-003 의존을 F-001/F-002 종속→독립으로 단순화. 리네임 Phase·git mv Step·cascade Step·install 재배포 Step 삭제 → 9 Step/4 Phase → 6 Step/2 Phase로 축소. 리네임 종속 리스크 H-1·H-2·H-7 소멸, 불변 회귀 가드 H-8 신설. validate false positive(H-3·H-4) 유지. |
