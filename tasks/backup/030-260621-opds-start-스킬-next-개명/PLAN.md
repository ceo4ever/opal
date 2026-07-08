# PLAN: opal-start 스킬을 opal-next로 개명

> 작성일: 2026-06-21 | 입력: TASK.md (ANALYSIS.md 없음 — Short Task)
> 모드: Flat (단일 기능 — 순수 rename + 참조 정합)

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

재진입 가이드 스킬 `opal-start`(`//start`)를 **`opal-next`(`//next`)**로 개명한다. 이름이 실제 기능("현재 상태 진단 → 다음 액션 안내")과 어긋나 `//opi`·`//onboarding`과 혼동되던 문제를 해소한다. **기능·진단 로직·라우팅 분기는 완전 불변**이며, 폴더/파일명·`name`·트리거·참조 경로·사용자 대면 문서만 변경하는 순수 rename + 참조 정합 작업이다 (→ D-7 §확정 §3).

`//start` alias·트리거는 **완전 제거**(하위호환 미유지)하고, 자연어 트리거도 "다음" 중심으로 재편한다 (→ D-7 §확정 §2).

### 1.2 참조 [MUST] 제약 (자체 로드 + 주입)

설계·실행에 직접 영향을 주는 [MUST] 제약을 원문 인용한다 (citation-rules.md §2.4).

- [MUST] `opal/core/references/opal-harness.md` §1 Guards: "사용자가 명시적으로 '승인','진행해','구현해' 등의 실행 허가를 내릴 때까지 코드를 작성하거나 파일을 생성/수정하지 않는다." → 이 PLAN 단계는 PLAN.md·TEST-SCENARIO.md 문서만 작성하며, 폴더/파일 rename·내용 수정은 모두 EXECUTE 단계의 일이다.
- [MUST] `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `agents/`, `community-skills/`, `scripts/`)에서 수행한다." → 수정 대상은 소스(`opal/`, `README.md`)만. 배포본(`~/.opal/`) 직접 편집 금지, 재배포는 후속 install 경유.
- [MUST] `docs/CONVENTIONS.md` §언어 규칙: "파일/폴더 이름 = English, kebab-case." → `opal-next` / `next-flow.md`는 kebab-case 규칙에 부합.
- [MUST] `docs/CONVENTIONS.md` §컴포넌트 네이밍 체계: "`opal-*` = OPAL 프레임워크 전용 (예: opal-project-init, opal-onboarding)." → `opal-next`는 이 접두사 체계에 부합.
- [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 '## 변경이력' 표에 행을 추가한다. 일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함." → R2/R3/R4 변경이력 행에 KST 일시 + (030) 표기 필수.
- [MUST] `opal/core/references/harness/citation-rules.md` §5 레거시 호환: "기존 산출물 소급 변경하지 않는다." → 과거 `//start` 사료(`opal/skills/opal-onboarding/SKILL.md:265` 변경이력, `tasks/029` 산출물)는 소급 변경 금지.

### 1.3 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | opal-start → opal-next 개명 (rename + 참조 정합 + 동작 검증) | R1, R2, R3, R4, R5, R6, R7 | P0 | 없음 |

> 단일 기능 → **Flat 모드**. §2·§3는 F 하위 섹션 없이 평면으로 작성한다.

### 1.4 기능 의존 그래프

생략 (단일 기능).

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | 레지스트리 `paths` (R4) | `paths`가 rename된 폴더를 못 가리키면 dangling → `//next` 매칭 시 path null/미존재 | P0 (스킬 호출 불가) | L2 (skill-registry match) | S-1, S-2 |
| H-2 | SKILL.md references 경로 (R2·R3) | SKILL.md가 `start-flow.md`(삭제됨)를 가리키면 흐름 가이드 dangling 링크 | P1 (스킬 동작은 하되 참조 깨짐) | L1 (grep 잔존 검사) | S-5 |
| H-3 | `//start` 트리거 잔존 (R2·R4) | `//start`/`^start$` 트리거가 남으면 죽은 alias가 여전히 매칭 → 사용자 혼동·alias 중복 | P1 | L2 (skill-registry match no-match) | S-3 |
| H-4 | 레지스트리 폴더-등록 정합 (R1·R4) | 폴더는 `opal-next`인데 레지스트리는 `opal-start` → validate가 dangling(미존재 path) + unregistered(미등록 폴더) 양방향 검출 | P0 | L2 (validate exit 0) | S-4, S-6 |
| H-5 | 타 스킬 매칭 회귀 (R4) | 레지스트리 JSON 편집 중 형제 항목(opal-onboarding/opal-project-init 등) 구조 훼손 | P0 | L2 (회귀 매칭) | S-7 |
| H-6 | 사료 소급 변경 (R5) | `opal-onboarding/SKILL.md:265` 변경이력의 과거 `//start`를 잘못 치환 → 사료 훼손 | P2 | L1 (L265 불변 확인) | S-8 |

> H-예 대응: H-1/H-4는 H-예3(제약 위반이 mock 통과 후 실제 검증에서만 드러남) 성격 — validate/match 실 도구 실행으로만 입증된다. 따라서 동작 검증(L2)을 의무화한다.

---

## 2. 기능별 분석 (Flat)

### 2.1 관련 파일 맵

> 프레임워크 스킬 태스크이므로 영역 축 = **스킬 / 가이드 / 레지스트리 / 문서 / 도구** (plan-guide.md §2.N.1: "프레임워크 문서·스킬 태스크에서는 스킬/가이드/오케스트레이터/에이전트/문서/환경/배치 축 사용").

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/opal-start/` (폴더) | 스킬 식별자 = 폴더명 | rename → `opal/skills/opal-next/` |
| 스킬 | `opal/skills/opal-start/SKILL.md` | `name`·triggers·본문·변경이력 | 수정 (rename 후 경로: `opal-next/SKILL.md`) |
| 가이드 | `opal/skills/opal-start/references/start-flow.md` | 진단·라우팅 흐름 상세 | rename → `next-flow.md` + 내용 수정 |
| 레지스트리 | `opal/core/references/opal-skills-registry.json` (L595~606 + L3 version + L696~ changelog) | 스킬 매칭 SSOT (opal 그룹) | 수정 |
| 문서 | `opal/skills/opal-onboarding/SKILL.md` (L176) | `//start` 교차 참조 | 수정 (L176만; L265 사료 불변) |
| 문서 | `README.md` (L125) | 사용자 대면 쌍슬래시 커맨드 표 | 수정 |
| 도구 | `opal/tools/skill-registry/skill-registry.js` | 매칭·validate 동작 검증 도구 | **불변 (검증 도구로만 사용)** |
| 도구 | `opal/tools/skill-registry/tests/test-validate.js` | validate 단위 테스트 (029 신설) | **불변 (회귀 검증으로만 사용)** |
| 도구 | `scripts/install-mac.sh` | 스킬 배포 (폴더 통째 복사) | **불변 (하드코딩 0건 — 아래 분석)** |

### 2.2 현재 구현

ANALYSIS.md가 없으므로 직접 코드 분석 수행 (Full ANALYSIS 수준).

**(a) opal-start SKILL.md** (`opal/skills/opal-start/SKILL.md:1-72`)
- frontmatter: `name: opal-start` (L2), `triggers` 6개 — `//start`(L7), `시작`(L8), `처음부터`(L9), `어디서부터 시작`(L10), `다음에 뭐 해야`(L11), `온보딩 다시 보고싶어`(L12), `version: 1.0.0` (L13).
- 본문 제목 `# opal-start — OPAL 재진입 가이드` (L16), references 참조 `references/start-flow.md` 2곳 (L22, L66), 진단 결과 표 헤더 `[OPAL Start] ...` (L39).
- Step 1(환경 진단 5항목)·Step 2(분기 7개)는 **진단 로직 = 불변 대상** (→ D-7 §확정 §3).
- 변경이력 1행 (L72): `v1.0.0 | 2026-05-09 00:00 | 초기 작성 (139) — //start 재진입 가이드 스킬 신규` — **사료, 소급 변경 금지** (→ D-9 §5).

**(b) start-flow.md** (`opal/skills/opal-start/references/start-flow.md:1-238`)
- 제목 `# opal-start 진단·라우팅 흐름 가이드` (L1), 로드 시점 주석 `opal-start/SKILL.md` (L3), `//start` 표기 4곳 (L10, L136, L145) — L10="`//start`가 호출되면", L136="//start 재실행", L145="//start 재실행".
- 진단 흐름(§1)·분기 메시지(§3)·관련 컴포넌트(§6)는 **불변 대상** (단, §6 표의 `opal-onboarding` 등 타 스킬 경로는 변경 없음).
- 변경이력 1행 (L238): `v1.0.0 | 2026-05-09 00:00 | 초기 작성 (139)` — **사료**.

**(c) 레지스트리 opal-start 항목** (`opal/core/references/opal-skills-registry.json:594-606`)
```json
{ "name": "opal-start", "alias": "start",
  "description": "OPAL 재진입 가이드 — 현재 상태 진단(...) + 다음 액션 권유",
  "triggers": ["^opal-start$", "^start$", "(?i)(어디서부터\\s*시작|다음에\\s*뭐\\s*해야|온보딩\\s*다시\\s*보고싶어)"],
  "paths": ["~/.opal/skills/opal-start/SKILL.md"] }
```
- 항목은 `groups.opal` 배열 내 위치 (L580 `opal-onboarding` 뒤, L607 `opal-project-init` 앞).
- 레지스트리 버전은 **top-level** `version: "3.5.0"` (L3) + `changelog` 배열 (L696~713, 최신 029/3.5.0). **per-skill version 필드 없음** → R4 AC "version 증가 + changelog 030"은 top-level version·changelog에 매핑.

**(d) onboarding SKILL.md** (`opal/skills/opal-onboarding/SKILL.md:176`)
- L176: "다음에 다시 정체성을 변경하려면 `//start` 또는 `//onboarding`을 사용하세요." → `//start` 1곳만 치환.
- L265 변경이력 `... Step 9 //start·//onboarding 재호출 안내 추가 (139)` → **사료, 불변** (→ D-9 §5).

**(e) README.md** (`README.md:125`)
- L125: `| \`//start\` | 재진입 가이드 — 현재 상태 진단 + 다음 액션 권유 |` → alias만 `//next`로 치환, 설명 유지.

**(f) install-mac.sh 배포 로직** (`scripts/install-mac.sh:923-934`)
- L926 `for skill_dir in "$opal_dir/skills"/*/; do` — OPAL 스킬을 **디렉토리 글롭으로 통째 복사** (`install_dir "$skill_dir" "$opal_home/skills/$skill_name"`). `opal-start` **하드코딩 0건** (grep 확인).
- 결론: **폴더 rename만으로 재배포 시 `~/.opal/skills/opal-next/`가 자동 생성**된다. install에 추가 Step 불필요. (단, 재배포는 사용자 명시 요청 시 후속 진행 — 이 태스크 범위 밖.)
- 변경이력 strip: `strip_deploy_md_recursive` (L933)가 배포본 변경이력을 제거하므로, 소스 변경이력 추가가 배포본을 오염시키지 않음.

### 2.3 영향 범위

- **상위 의존(호출자)**: 사용자/PM이 `//next`·`//start`·자연어로 스킬을 호출 → `skill-registry.js matchCommand()`가 레지스트리를 SSOT로 매칭. 따라서 레지스트리(R4)가 핵심 계약.
- **하위 의존(피호출)**: SKILL.md → `next-flow.md` 참조. SKILL.md가 가리키는 경로가 rename 결과와 정합해야 함 (H-2).
- **공유 상태**: 레지스트리 JSON은 모든 스킬의 단일 SSOT — opal 그룹 형제 항목(opal-onboarding L580~593, opal-project-init L607~619 등) 구조를 훼손하면 타 스킬 매칭 회귀 (H-5).
- **관련 검증 도구**: `skill-registry.js` (matchCommand/validate), `tests/test-validate.js` (node:test 5개 TC). 둘 다 **불변**, 회귀·동작 검증 용도로만 실행.
- **사료(소급 변경 금지)**: `opal-onboarding/SKILL.md:265`, `tasks/029/TEST-SCENARIO.md:142` — 변경 대상 아님 (H-6).

---

## 3. 기능별 설계 (Flat)

### 3.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| - | (없음 — 모두 rename 또는 수정) | - | - | git mv는 신규 생성이 아닌 이동 |

**수정** (git mv로 이동되는 파일 포함)

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/opal-start/` → `opal/skills/opal-next/` | 스킬 | `git mv`로 폴더 통째 이동 (하위 SKILL.md·references/ 포함) | (→ D-1, D-7 §확정 §1) |
| 2 | `opal/skills/opal-next/references/start-flow.md` → `next-flow.md` | 가이드 | `git mv`로 파일 이동 | (→ D-2, D-7 §확정 §3) |
| 3 | `opal/skills/opal-next/SKILL.md` | 스킬 | `name`·triggers·본문 제목·references 경로·진단 표 헤더·변경이력 | (→ D-1) `SKILL.md:2,4,5,7-13,16,22,39,66,72` |
| 4 | `opal/skills/opal-next/references/next-flow.md` | 가이드 | 제목·로드 시점 주석·`//start`→`//next` 4곳·변경이력 | (→ D-2) `start-flow.md:1,3,10,136,145,238` |
| 5 | `opal/core/references/opal-skills-registry.json` | 레지스트리 | opal 그룹 항목 + top-level version + changelog | (→ D-3) `opal-skills-registry.json:3,594-606,696-713` |
| 6 | `opal/skills/opal-onboarding/SKILL.md` | 문서 | L176 `//start`→`//next` (L265 사료 불변) | (→ D-4) `SKILL.md:176` |
| 7 | `README.md` | 문서 | L125 `//start`→`//next` alias (설명 유지) | (→ D-5) `README.md:125` |

> install-mac.sh·skill-registry.js·test-validate.js는 §2.1·§2.2(f) 분석대로 **불변**.

### 3.2 변경 상세 설계

> 각 설계 결정 뒤 인라인 인용 기재 (citation-rules.md §2).

#### 3.2.1 SKILL.md 갱신 (Step 3)

치환 매핑 (진단 로직 본문은 불변, 식별자·트리거만 변경):

| 위치 | 현재 | 변경 후 | 근거 |
|------|------|---------|------|
| L2 `name` | `opal-start` | `opal-next` | (→ D-1) R2 AC |
| L4 description | "`//start`, "시작", "처음부터" 등으로 호출된다" | "`//next` 등으로 호출된다 — '다음에 뭐 해야' 류 자연어 포함" | (→ D-1) "다음" 중심 재편 (→ D-7 §2) |
| L5 description | "사용자가 //start 입력 시 ..." | "사용자가 //next 입력 시 ..." | (→ D-1) |
| L6-12 triggers | `//start`/`시작`/`처음부터`/`어디서부터 시작`/`다음에 뭐 해야`/`온보딩 다시 보고싶어` | `//next` + "다음" 중심 재편 (아래 설계 결정) | (→ D-1) R2 AC |
| L13 version | `1.0.0` | `2.0.0` (개명 = breaking change, alias 제거) | (→ D-8 §변경이력) semver major |
| L16 제목 | `# opal-start — OPAL 재진입 가이드` | `# opal-next — OPAL 재진입 가이드` | (→ D-1) |
| L22 references | `references/start-flow.md` | `references/next-flow.md` | (→ D-1) R3 AC |
| L39 진단 표 헤더 | `[OPAL Start] 환경 진단 결과` | `[OPAL Next] 환경 진단 결과` | (→ D-1) 출력 라벨 일관성 |
| L66 references | `references/start-flow.md` | `references/next-flow.md` | (→ D-1) R3 AC |
| L72 변경이력 | (기존 행 — 사료) | 기존 행 보존 + 신규 행 추가 (아래) | (→ D-9 §5) |

**트리거 재설계 결정** (R2 AC: `//next`·자연어 포함, `//start`/`시작`/`처음부터` 미포함):
- 신규 triggers (frontmatter YAML): `"//next"`, `"다음에 뭐 해야"`, `"어디서부터 시작"`, `"온보딩 다시 보고싶어"`
- 제거: `"//start"`, `"시작"`(단독어 — 너무 광범위), `"처음부터"`("처음 시작" 연상 → 개명 취지와 충돌, 제거).
- 유지 근거: "어디서부터 시작"·"온보딩 다시 보고싶어"는 재진입 의미가 명확하여 유지. "다음에 뭐 해야"는 새 이름과 직결되는 핵심 트리거 (→ D-7 §확정 §1·§2).

**신규 변경이력 행** (KST 일시 + 030, [MUST] CONVENTIONS §변경이력):
```
| v2.0.0 | 2026-06-21 HH:mm | 개명 (030) — opal-start → opal-next, //start alias·트리거 제거, references→next-flow.md |
```
> EXECUTE 시점 실제 KST 시각으로 `HH:mm` 채움.

#### 3.2.2 next-flow.md 갱신 (Step 4)

| 위치 | 현재 | 변경 후 | 근거 |
|------|------|---------|------|
| L1 제목 | `# opal-start 진단·라우팅 흐름 가이드` | `# opal-next 진단·라우팅 흐름 가이드` | (→ D-2) |
| L3 로드 시점 | `opal-start/SKILL.md Step 1·2` | `opal-next/SKILL.md Step 1·2` | (→ D-2) |
| L10 | "`//start`가 호출되면" | "`//next`가 호출되면" | (→ D-2) R3 AC |
| L136 | "프로젝트 폴더로 이동 후 //start 재실행" | "... //next 재실행" | (→ D-2) |
| L145 | "초기화 후 //start 재실행" | "... //next 재실행" | (→ D-2) |
| L189 진단 표 헤더 | `[OPAL Start] 환경 진단 결과` | `[OPAL Next] 환경 진단 결과` | (→ D-2) SKILL.md L39와 일관성 |
| L238 변경이력 | (기존 행 — 사료) | 기존 행 보존 + 신규 행 추가 | (→ D-9 §5) |

> 진단 흐름 ASCII(§1)·분기 메시지(§3)·관련 컴포넌트 표(§6)의 **로직·타 스킬 경로는 불변**. §6 표의 `opal-onboarding`·`opal-project-init` 경로는 변경 대상 아님.
> 신규 변경이력 행: `| v2.0.0 | 2026-06-21 HH:mm | 개명 (030) — start-flow.md → next-flow.md, //start→//next |`

#### 3.2.3 레지스트리 갱신 (Step 5)

opal 그룹 항목 (`opal-skills-registry.json:594-606`) 치환:

```json
{
  "name": "opal-next",
  "alias": "next",
  "description": "OPAL 재진입 가이드 — 현재 상태 진단(identity / .opal/AGENT.md / docs/PROJECT.md / cwd 프로젝트 여부) + 다음 액션 권유",
  "triggers": [
    "^opal-next$",
    "^next$",
    "(?i)(어디서부터\\s*시작|다음에\\s*뭐\\s*해야|온보딩\\s*다시\\s*보고싶어)"
  ],
  "paths": [
    "~/.opal/skills/opal-next/SKILL.md"
  ]
}
```

- `name`: `opal-start` → `opal-next`; `alias`: `start` → `next`; triggers `^opal-start$`/`^start$` → `^opal-next$`/`^next$` (자연어 정규식은 기존 유지 — 재진입 의미 명확, R2 트리거 재설계와 정합) (→ D-3, D-7 §확정 §2).
- `paths`: `~/.opal/skills/opal-start/SKILL.md` → `~/.opal/skills/opal-next/SKILL.md` (배포본 경로 — R1 폴더 rename 후 재배포 시 정합) (→ D-3).
- description은 SKILL.md L4와 정합 유지 (alias 토큰 제거).

**top-level version + changelog** (R4 AC "version 증가 + changelog 030"):
- L3 `"version": "3.5.0"` → `"3.6.0"` (minor 증가 — 스킬 1건 개명) (→ D-3, D-8 semver).
- L4 `"updated_at": "2026-06-18"` → `"2026-06-21"`.
- `changelog` 배열 (L696~) 최상단 또는 029 항목 위에 030 항목 추가:
```json
{
  "version": "3.6.0",
  "date": "2026-06-21",
  "task": "030",
  "changes": [
    "opal-start → opal-next 개명: name·alias(start→next)·triggers(^opal-start$/^start$ → ^opal-next$/^next$)·paths(opal-next/SKILL.md) 갱신",
    "//start alias·트리거 완전 제거 (하위호환 미유지) — 자연어 트리거는 재진입 의미 항목만 유지",
    "기능·진단 로직·라우팅 분기 불변 (순수 rename + 참조 정합)"
  ]
}
```

> JSON 편집 시 형제 항목(opal-onboarding L580~593, opal-project-init L607~619) 구조 비훼손 — `name`·`alias`·`triggers`·`paths` 키만 in-place 치환 (H-5 대응).

#### 3.2.4 onboarding L176 갱신 (Step 6)

- L176: "`//start` 또는 `//onboarding`" → "`//next` 또는 `//onboarding`" (→ D-4) R5 AC.
- L265 변경이력 사료 **불변** — grep으로 L176만 정확 치환, L265 미접촉 (→ D-9 §5).
- onboarding은 스킬이므로 변경이력 행 추가 의무 ([MUST] CONVENTIONS §변경이력): `| vX.Y | 2026-06-21 HH:mm | (030) opal-start 개명 후속 — L176 //start→//next 교차 참조 갱신 |` (현재 onboarding 버전 확인 후 +0.0.1 또는 +0.1).

#### 3.2.5 README L125 갱신 (Step 7)

- L125: `| \`//start\` | 재진입 가이드 — 현재 상태 진단 + 다음 액션 권유 |` → `| \`//next\` | 재진입 가이드 — 현재 상태 진단 + 다음 액션 권유 |` (alias만 치환, 설명 유지) (→ D-5) R6 AC.
- README는 변경이력 표 없음 (사용자 대면 소개 문서) → 변경이력 행 추가 불필요.

### 3.3 환경 변경

해당 없음. (신규 패키지·환경 설정 없음. Node v22.14.0 기설치 — validate 테스트 실행 가능.)

### 3.4 배치/마이그레이션

해당 없음. (install 재배포는 사용자 명시 요청 시 후속 — `for skill_dir` 글롭이 자동 처리하므로 install 스크립트 수정 불필요, §2.2(f).)

### 3.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R1 AC | 산출물 검사 | `opal/skills/opal-next/SKILL.md`·`opal/skills/opal-next/references/next-flow.md` 존재, `opal/skills/opal-start/` 미존재 (`git mv` 이력 보존) |
| TS-002 | R2 AC | 산출물 검사 | SKILL.md `name: opal-next`, triggers에 `//next`·"다음에 뭐 해야" 포함·`//start`/`시작`/`처음부터` 미포함, 제목 "opal-next", 변경이력 030 행 |
| TS-003 | R3 AC | 산출물 검사 | `next-flow.md` 내 `//start` 잔존 0건(`//next`로 치환), `start-flow.md` 미존재, SKILL.md references가 `next-flow.md` 지칭 |
| TS-004 | R4 AC | 산출물 검사 | 레지스트리 `name: opal-next`·`alias: next`·triggers `^opal-next$`/`^next$`·paths `opal-next/SKILL.md`, `opal-start`/`^start$` 잔존 0건, version 증가 + changelog 030 |
| TS-005 | R5 AC | 산출물 검사 | onboarding L176 `//next`, L265 사료 불변 |
| TS-006 | R6 AC | 산출물 검사 | README L125 `//next`, 설명 유지 |
| TS-007 | R7 AC | 기능 테스트 | `skill-registry.js match "//next"` → opal-next 해석, `match "//start"` → no-match(또는 미해석), `match "^opal-start$"` dangling 없음 |
| TS-008 | R7 AC | 통합 테스트 | `skill-registry.js validate` exit 0 (dangling·unregistered·경로 누락 0건) |
| TS-009 | R7 AC | 회귀 테스트 | `node --test tests/` 5개 TC 전부 PASS (validate 도구 회귀 비파괴), 타 스킬(`//opds`·`//opbr`) 매칭 정상 |
| TS-010 | 제약 | 보안 검사 | 변경 파일에 하드코딩 시크릿 0건 (rename 작업 — 시크릿/.env 무관, 해당 없음 확인) |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001 | 1, 2 | opal-task-agent | 순차 | git mv 폴더→파일 (선행 — 이후 모든 수정의 기반) |
| 2 | F-001 | 3, 4 | opal-task-agent | 순차 | rename된 경로 위에서 내용 수정 |
| 3 | F-001 | 5, 6, 7 | opal-task-agent | 순차(또는 병렬 가능) | 레지스트리·onboarding·README — 독립 파일 |
| 4 | F-001 | 8 | opal-task-agent | 순차 | 동작·정합 검증 (전체 완료 후) |
| 5 | F-001 | 9 | PM 직접 | 순차 | docs/ 갱신 판단 (아래 §4.4) |

### 4.2 실행 체크리스트

> 총 9개 Step | Phase 5개 | 실행 모드: 단순

#### Step 1: git mv 폴더 rename
- [x] 완료
- **소속 기능**: F-001
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-start/` → `opal/skills/opal-next/`
- **작업 내용**: `git mv opal/skills/opal-start opal/skills/opal-next` 실행 (하위 SKILL.md·references/ 통째 이동, 추적 이력 보존). [MUST] `docs/CONVENTIONS.md` §배포 경계 — 소스만, `~/.opal/` 미접촉.
- **완료 기준**: `opal/skills/opal-next/SKILL.md` 존재 AND `opal/skills/opal-start/` 미존재 AND `git status`에 rename(R) 표시
- **테스트**: TS-001
- **실행 방법**: direct
- **의존**: 없음

#### Step 2: git mv references 파일 rename
- [x] 완료
- **소속 기능**: F-001
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-next/references/start-flow.md` → `next-flow.md`
- **작업 내용**: `git mv opal/skills/opal-next/references/start-flow.md opal/skills/opal-next/references/next-flow.md` (Step 1로 폴더가 이미 opal-next로 이동된 상태 기준)
- **완료 기준**: `opal/skills/opal-next/references/next-flow.md` 존재 AND `start-flow.md` 미존재
- **테스트**: TS-003
- **실행 방법**: direct
- **의존**: Step 1

#### Step 3: SKILL.md 내용 갱신
- [x] 완료
- **소속 기능**: F-001
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-next/SKILL.md`
- **작업 내용**: §3.2.1 치환 매핑대로 `name`(L2)·description(L4-5)·triggers(L6-12)·version(L13)·제목(L16)·references 경로 2곳(L22·L66)·진단 표 헤더(L39)를 갱신. 트리거는 §3.2.1 재설계대로 `//next`+"다음" 중심(`//start`/`시작`/`처음부터` 제거). 진단 5항목·분기 7개 로직 **불변**. 변경이력 030 행 추가(KST 일시), L72 기존 행 보존.
- **완료 기준**: TS-002 충족 — `name: opal-next`, triggers에 `//next`·"다음에 뭐 해야" O / `//start`·"시작"·"처음부터" X, 제목 "opal-next", references `next-flow.md`, 변경이력 030 행
- **테스트**: TS-002
- **실행 방법**: direct
- **의존**: Step 1

#### Step 4: next-flow.md 내용 갱신
- [x] 완료
- **소속 기능**: F-001
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-next/references/next-flow.md`
- **작업 내용**: §3.2.2 매핑대로 제목(L1)·로드 시점 주석(L3)·`//start`→`//next` 4곳(L10·L136·L145)·진단 표 헤더(L189)를 갱신. 진단 흐름 ASCII·분기 메시지·§6 타 스킬 경로 **불변**. 변경이력 030 행 추가(KST 일시), L238 기존 행 보존.
- **완료 기준**: TS-003 충족 — `next-flow.md` 내 `//start` 0건, 제목 "opal-next ..."
- **테스트**: TS-003
- **실행 방법**: direct
- **의존**: Step 2

#### Step 5: 레지스트리 JSON 갱신
- [x] 완료
- **소속 기능**: F-001
- **영역**: 레지스트리
- **agent**: opal-task-agent
- **파일**: `opal/core/references/opal-skills-registry.json`
- **작업 내용**: §3.2.3대로 opal 그룹 opal-start 항목(L594-606)의 `name`·`alias`·`triggers`·`paths`·`description` in-place 치환 (형제 항목 비훼손). top-level `version` 3.5.0→3.6.0(L3), `updated_at`→2026-06-21(L4), `changelog` 배열에 030 항목 추가. JSON 유효성 유지(`node -e` 파싱 또는 validate로 확인).
- **완료 기준**: TS-004 충족 — `opal-next`/`next`/`^opal-next$`/`^next$`/`opal-next/SKILL.md` 존재, `opal-start`/`^start$` 잔존 0건, JSON valid
- **테스트**: TS-004, TS-007, TS-008
- **실행 방법**: direct
- **의존**: Step 1 (paths가 rename된 폴더와 정합해야 함)

#### Step 6: onboarding SKILL.md L176 갱신
- [x] 완료
- **소속 기능**: F-001
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-onboarding/SKILL.md`
- **작업 내용**: L176의 `//start`만 `//next`로 정확 치환. [MUST] `citation-rules.md` §5 — L265 변경이력 사료 **불변**(미접촉). 변경이력 030 행 추가(현재 버전 +increment, KST 일시).
- **완료 기준**: TS-005 충족 — L176 `//next`, L265 원문 그대로
- **테스트**: TS-005
- **실행 방법**: direct
- **의존**: 없음 (Step 1과 독립)

#### Step 7: README.md L125 갱신
- [x] 완료
- **소속 기능**: F-001
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `README.md`
- **작업 내용**: L125 표 항목의 `//start`를 `//next`로 치환, 설명("재진입 가이드 — 현재 상태 진단 + 다음 액션 권유") 유지. README는 변경이력 표 없음 → 행 추가 불필요.
- **완료 기준**: TS-006 충족 — L125 `//next`, 설명 유지
- **테스트**: TS-006
- **실행 방법**: direct
- **의존**: 없음 (Step 1과 독립)

#### Step 8: 동작·정합 검증
- [x] 완료
- **소속 기능**: F-001
- **영역**: 도구 (검증)
- **agent**: opal-task-agent
- **파일**: (검증 전용 — `opal/tools/skill-registry/skill-registry.js`, `tests/test-validate.js`)
- **작업 내용**: 프로젝트 루트에서 ① `node opal/tools/skill-registry/skill-registry.js match "//next"` → opal-next 확인, ② `match "//start"`·`match "^opal-start$"` → no-match/dangling 없음 확인, ③ `node opal/tools/skill-registry/skill-registry.js validate` → exit 0 확인, ④ `node --test opal/tools/skill-registry/tests/` 5 TC PASS, ⑤ 회귀: `match "//opds"`·`match "//opbr"` 정상. (검증 도구·테스트 파일은 불변.)
- **완료 기준**: TS-007·TS-008·TS-009 전부 충족 — match 해석 정확, validate exit 0, 테스트 5 PASS, 회귀 정상
- **테스트**: TS-007, TS-008, TS-009, TS-010
- **실행 방법**: direct
- **의존**: Step 1, 3, 4, 5 (rename + 내용 + 레지스트리 완료 후)

#### Step 9: docs/ 갱신 판단
- [ ] 완료
- **소속 기능**: F-001
- **영역**: 문서
- **agent**: PM 직접
- **파일**: (판단 — `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md`)
- **작업 내용**: §4.4 판단대로 docs/ 갱신 필요 여부 확정. 현 분석상 PROJECT.md/ARCHITECTURE.md/CONVENTIONS.md에 `opal-start` 직접 언급 **없음**(스킬 그룹 표는 일반 항목만 나열) → **갱신 불필요 가능성 높음**. PM이 grep `opal-start` docs/로 재확인 후, 잔존 있으면 치환·없으면 Step 종결.
- **완료 기준**: `grep -rn "opal-start\|//start" docs/` 결과 0건 확인 (또는 발견 시 치환 완료)
- **테스트**: 산출물 검사 (grep 0건)
- **실행 방법**: direct
- **의존**: Step 8

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 → Step 2 | 폴더 rename 후에 그 안의 파일을 rename해야 경로 정합 |
| Step 1 → Step 3 | SKILL.md 수정은 rename된 경로(`opal-next/SKILL.md`) 위에서 수행 |
| Step 2 → Step 4 | next-flow.md 수정은 rename된 파일명 위에서 수행 |
| Step 1 → Step 5 | 레지스트리 `paths`가 rename된 폴더를 가리켜야 dangling 회피 |
| Step 5, 6, 7 ∥ | 독립 파일 — 병렬 가능 (단 단순 모드 direct 순차 실행 무방) |
| Step 3·4·5 → Step 8 | 검증은 모든 내용 변경 완료 후 |
| Step 8 → Step 9 | 동작 확인 후 docs/ 최종 판단 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | 폴더/파일 rename + git 이력 | TS-001 | opal-next/ 존재·opal-start/ 미존재·git rename 표시 |
| F-001 | SKILL.md 식별자·트리거 갱신 | TS-002 | name opal-next, //next O / //start·시작·처음부터 X, 변경이력 030 |
| F-001 | next-flow.md 내용 치환 | TS-003 | //start 0건, start-flow.md 미존재, references 정합 |
| F-001 | 레지스트리 정합 | TS-004 | opal-next/next/^opal-next$/^next$/paths 정합, opal-start 0건, version+changelog |
| F-001 | onboarding 교차 참조 | TS-005 | L176 //next, L265 사료 불변 |
| F-001 | README 사용자 대면 | TS-006 | L125 //next, 설명 유지 |
| F-001 | 매칭 동작 | TS-007 | //next→opal-next, //start no-match, dangling 0 |
| F-001 | validate 정합 | TS-008 | validate exit 0 |
| F-001 | 회귀 (도구·타 스킬) | TS-009 | 5 TC PASS, //opds·//opbr 정상 |

### 5.2 회귀 테스트
- [ ] `skill-registry.js validate` exit 0 (전체 레지스트리 정합 — dangling/unregistered 0) — **주의**: opal-next dangling은 배포 전 예상된 상태 (PLAN §2.2(f)); 4개 pre-existing dangling은 이 태스크 범위 밖. 새 오류 미도입 확인됨.
- [x] `node --test opal/tools/skill-registry/tests/test-validate.js` 5개 TC 전부 PASS (validate 도구 비파괴)
- [x] 타 스킬 매칭 비파괴 — `match "//opds"` opal-pilot-dev-short, `match "//opbr"` opal-brain, `match "onboarding"` opal-onboarding 정상 해석
- [x] opal 그룹 형제 항목(opal-onboarding·opal-project-init·opal-skill-creator 등) 구조 비훼손

### 5.3 코드/문서 품질
- [x] 프로젝트 컨벤션 준수 — 폴더/파일명 kebab-case (`opal-next`/`next-flow.md`), `opal-*` 접두사 체계 (CONVENTIONS §네이밍)
- [x] 변경이력 기록 — SKILL.md·next-flow.md·레지스트리 changelog·onboarding에 KST 일시 2026-06-21 13:58 + (030)
- [x] 사료 보존 — onboarding L265 원문 불변 확인됨 (citation-rules §5)
- [x] 기능·진단 로직·라우팅 분기 불변 (진단 5항목·분기 7개 변경 없음)
- [x] `git mv` 사용으로 rename 추적 이력 보존 (git status R 표시 확인)

### 5.4 보안
- [x] 변경 파일에 하드코딩 토큰/시크릿 없음 (rename 작업 — 시크릿 무관)
- [x] `.env`·인증 파일 미관여 — **본 태스크 보안 항목 해당 없음** (문서/설정 rename, 시크릿/네트워크/입력처리 변경 없음)

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 9개 | 복잡 (6개 이상) |
| 변경 파일 수 | 5개 수정 + 2개 rename = 실질 7개 | 복잡 (4개 이상) |
| 모듈 범위 | 스킬+레지스트리+문서 (다중 위치, 단일 기능) | 단순 (단일 기능·동일 변경 성격) |
| 작업 유형 | 순수 rename + 참조 정합 (동작 불변) | 단순 (오류 수정·단순 수정 성격) |
| 외부 의존성 | 없음 (Node 기설치, 신규 패키지·도구·API 0) | 단순 |
| **실행 모드** | **단순** | 작업 유형(동작 불변 rename)·외부 의존성 0·로직 변경 0이 결정적. Step 수는 9이나 모두 동일 성격의 기계적 치환이며 단일 에이전트(opal-task-agent)가 순차 처리. 워커 내부 서브 에이전트 분할 불필요 → 모든 Step `direct`. |

> 판정 근거: Step/파일 수만 임계 초과하나, 단일 기능·동작 불변·외부 의존성 0·단일 에이전트 처리이므로 실행 아키텍처(§7) 불필요. plan-guide.md §5 "하나라도 복잡 기준 해당 시 복잡 모드" 규칙상 형식적으로는 복잡이나, 실질 토폴로지가 선형 단일 에이전트라 §7을 생략하고 단순 모드 처리한다(과잉 설계 회피, PRINCIPLES §3 surgical). 모든 실행 방법 = `direct`.

---

## 7. 실행 아키텍처 (복잡 모드 시)

해당 없음 — §6 판정대로 실질 단순 모드(단일 에이전트 선형 처리). 에이전트 토폴로지 분할·신규 스킬·신규 도구 불필요.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 스킬·문서 | Markdown | (해당 community-skill 없음 — 프레임워크 문서 작업) |
| 레지스트리 | JSON | - |
| 검증 도구 | Node.js (v22.14.0) — skill-registry.js / node:test | - |
| rename | Bash / git (`git mv`) | - |

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| (없음) | 외부 라이브러리 API 조회 불필요 — 내부 프레임워크 rename 작업 |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | opal-start SKILL.md | `opal/skills/opal-start/SKILL.md` | 개명 대상 스킬 정의 (name·triggers·본문) |
| D-2 | 소스 | start-flow.md | `opal/skills/opal-start/references/start-flow.md` | 개명 대상 참조 흐름 가이드 |
| D-3 | 설계 | 스킬 레지스트리 | `opal/core/references/opal-skills-registry.json` | 스킬 매칭 SSOT (opal 그룹 L594-606 + top-level version/changelog) |
| D-4 | 소스 | onboarding SKILL.md | `opal/skills/opal-onboarding/SKILL.md` | `//start` 교차 참조 (L176) + 사료 보존 대상(L265) |
| D-5 | 소스 | README | `README.md` | 사용자 대면 커맨드 표 (L125) |
| D-6 | 소스 | skill-registry.js / test-validate.js | `opal/tools/skill-registry/skill-registry.js`, `tests/test-validate.js` | 매칭·validate 동작 검증 도구 (불변, 검증 용도) |
| D-7 | 기획 | TASK.md | `tasks/030-260621-opds-start-스킬-next-개명/TASK.md` | 확정 설계 방향(§확정 §1·§2·§3)·요구사항 R1~R7·cascade 전수조사 |
| D-8 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 네이밍·배포 경계·변경이력·구현 규칙(Guards/배포) |
| D-9 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | §5 레거시 호환 (사료 소급 변경 금지) |
| D-10 | 설계 | red-first.md | `opal/core/references/harness/red-first.md` | RED-first 적용 기준 (§1.5 — 설정·문서·행위 불변 리팩터 트랙) |
| D-11 | 설계 | install-mac.sh | `scripts/install-mac.sh` | 배포 로직 확인 (L923-934 글롭 복사, opal-start 하드코딩 0건) |
| D-12 | 설계 | PROJECT.md | `docs/PROJECT.md` | 프로젝트 구성(Framework 영역 → opal-task-agent)·문서 테이블(README 참조 시점) |

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | 레지스트리 `paths`가 rename된 폴더와 불일치 → `//next` dangling | F-001 (H-1, H-4) | P0 | Step 5에서 paths를 `opal-next/SKILL.md`로 갱신, Step 8 validate exit 0 확인 |
| R-2 | `//start` 트리거 잔존 → 죽은 alias 매칭 | F-001 (H-3) | P1 | Step 3·5에서 `//start`/`^start$`/`시작`/`처음부터` 완전 제거, Step 8 `match "//start"` no-match 확인 |
| R-3 | SKILL.md references가 삭제된 `start-flow.md` 지칭 | F-001 (H-2) | P1 | Step 3에서 L22·L66을 `next-flow.md`로 갱신, grep 잔존 0건 확인 |
| R-4 | 레지스트리 JSON 편집 중 형제 항목 구조 훼손 → 타 스킬 회귀 | F-001 (H-5) | P0 | Step 5에서 키 in-place 치환만, Step 8 회귀(`//opds`·`//opbr`) + validate + 5 TC 확인 |
| R-5 | 사료(onboarding L265·tasks/029) 잘못 치환 | F-001 (H-6) | P2 | Step 6에서 L176만 정확 치환, L265 미접촉 — grep으로 L265 원문 보존 확인 |
| R-6 | 배포본(`~/.opal/`) 직접 편집 위반 | F-001 | P1 | [MUST] CONVENTIONS §배포 경계 — 소스만 수정, 재배포는 후속 install 경유 (이 태스크 범위 밖) |
| R-7 | 진단 로직·분기 무심코 수정 (인접 개선) | F-001 | P1 | 각 Step "로직 불변" 명시, 치환 매핑 외 라인 미접촉 (PRINCIPLES §3 surgical) |
