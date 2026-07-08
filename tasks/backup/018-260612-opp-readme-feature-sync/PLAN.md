# PLAN: README 최신화 — 신규 베이스라인(001~017 + brain) 반영

> 작성일: 2026-06-12
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사

### 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | 스킬 레지스트리 | `opal/core/references/opal-skills-registry.json` | Pilot·독립 스킬·약어·pipeline 필드 SSOT |
| D-2 | 설계 | PROJECT.md | `docs/PROJECT.md` | 주요 컴포넌트(브레인/GC), 지원 플랫폼, 프로젝트 정의 |
| D-3 | 설계 | AGENT.md | `~/.opal/AGENT.md` | 부트스트랩 완료 보고 형식(B-1), L2 경량 트랙(A-5) |
| D-4 | 설계 | OPAL 헌법 | `~/.opal/PRINCIPLES.md` | 핵심 철학 정본(A-4) |
| D-5 | 설계 | opal-pilot-sdd SKILL | `~/.opal/skills/opal-pilot-sdd/SKILL.md` | opsdd 파이프라인 정본(B-2/U-2) |
| D-6 | 설계 | opal-pilot-gc SKILL | `~/.opal/skills/opal-pilot-gc/SKILL.md` | GC Pilot 파이프라인·사용법(A-2) |
| D-7 | 설계 | opal-brain SKILL | `~/.opal/skills/opal-brain/SKILL.md` | 브레인 4모드 사용법(A-1) |
| D-8 | 소스 | 현재 README | `README.md` | 갱신 대상 (현행 구조·목차·앵커) |
| D-9 | 설계 | red-first 하네스 | `~/.opal/references/harness/red-first.md` | TDD RED-first 트랙 설명(A-6) |
| D-10 | 소스 | 에이전트 디렉토리 | `opal/agents/` (13개 폴더) | 아키텍처 개요 에이전트 수 검증(B-4) |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §3.1 준수. 본 태스크는 비개발(문서) 트랙 — 문서/소스 근거 필수(citation-rules §1.5).

### 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `README.md` | 프레임워크 공개 소개 문서 (갱신 대상) | ✅ 수정 | `README.md:1-785` |
| `opal/core/references/opal-skills-registry.json` | Pilot·독립 스킬 SSOT | ❌ (Read 전용, 미커밋 `M`) | `opal/core/references/opal-skills-registry.json:6-651` |
| `docs/PROJECT.md` | 컴포넌트·플랫폼 SSOT | ❌ (Read 전용) | `docs/PROJECT.md:53-102` |
| `~/.opal/AGENT.md` | 부트스트랩·L2 트랙 SSOT | ❌ (배포 경계 — Read 전용) | `~/.opal/AGENT.md:54-57`, `141-173` |
| `~/.opal/PRINCIPLES.md` | 헌법(핵심 철학) SSOT | ❌ (배포 경계 — Read 전용) | `~/.opal/PRINCIPLES.md:12-40` |
| `~/.opal/skills/opal-pilot-sdd/SKILL.md` | opsdd 파이프라인 정본 | ❌ (배포 경계 — Read 전용) | `~/.opal/skills/opal-pilot-sdd/SKILL.md:23`, `320` |
| `~/.opal/skills/opal-pilot-gc/SKILL.md` | GC 파이프라인 정본 | ❌ (배포 경계 — Read 전용) | `~/.opal/skills/opal-pilot-gc/SKILL.md:13` |
| `~/.opal/skills/opal-brain/SKILL.md` | 브레인 4모드 정본 | ❌ (배포 경계 — Read 전용) | `~/.opal/skills/opal-brain/SKILL.md:34-38` |
| `~/.opal/references/harness/red-first.md` | RED-first 트랙 정본 | ❌ (배포 경계 — Read 전용) | `~/.opal/references/harness/red-first.md:18-22`, `33-39` |

### 현재 상태

현행 README(`README.md:1-785`)는 `141`(README 정비) 시점 구조를 유지하며 11개 섹션 목차(`README.md:43-62`)로 구성된다. SSOT 대조 결과 다음 갭이 확정됐다.

**(A) 통째로 누락된 신규 기능 — 6건 + 독립 스킬 3건**

- **A-1 opal-brain (`//opbr`)**: 레지스트리 `opal` 그룹에 등재(`opal/core/references/opal-skills-registry.json:617-632`), pipeline `MODE: init | ingest | query | lint`. PROJECT.md §주요 컴포넌트(Project Brain)에 정의(`docs/PROJECT.md:73-83`). README 전무.
- **A-2 opal-pilot-gc (`//opgc`)**: 레지스트리 `opal-pilot` 그룹에 등재, alias `opgc`/`gc`(`opal/core/references/opal-skills-registry.json:101-117`). README Pilot 목록·사용법 전무.
- **A-3 Codex 플랫폼**: PROJECT.md 원칙 3 "Claude Code, Cursor, Gemini, Codex 등"(`docs/PROJECT.md:17`), AGENT.md Codex 자동삽입 절(`~/.opal/AGENT.md:370-374`). README는 "Claude Code, Cursor, Gemini"만(`README.md:74`, `103`).
- **A-4 OPAL 헌법 (PRINCIPLES.md)**: 헌법 Core Stance 4원칙 + §1~§4(`~/.opal/PRINCIPLES.md:12-40`). README 핵심 철학 표(`README.md:24-30`)에 헌법·"검증된 동작=완료" 미반영.
- **A-5 L2 경량 트랙**: AGENT.md §"그냥 해 / 직접 수행 = L2 경량 트랙"(`~/.opal/AGENT.md:141-173`). README는 비서/PM 2역할만(`README.md:242-251`).
- **A-6 TDD RED-first 트랙**: red-first 하네스 정본(`~/.opal/references/harness/red-first.md:18-39`). README opds/opd 흐름(`README.md:443-455`, `481-496`)에 미반영.
- **A-7 독립 스킬 누락 3건**: 레지스트리 standalone 그룹에 `html-mockup`(`:457-470`), `system-architecture-html`/alias `html-sa`(`:471-484`), `ppt-builder`/alias `ppt`(`:485-498`) 존재. README §독립 스킬(`README.md:600-675`)에 미등재.

**(B) 부정확 (오정보) — 4건**

- **B-1 부트스트랩 체크리스트**: README `✅ identity ✅ harness ✅ PM …`(`README.md:106`). 정본은 `✅ principles ✅ identity ✅ harness ✅ PM ✅ PM모드 ⏳ registry ⏳ references ⏳ model-mapping`(`~/.opal/AGENT.md:55`) — `principles` 칼럼 선두 추가.
- **B-2 opsdd 파이프라인**: README 2곳(비교표 `README.md:265`, 사용법 `README.md:533`)에서 `TASK → SPEC → VERIFY → REVIEW → DESIGN → EXECUTE-LOOP → DONE`. 정본은 `TASK → SPEC → REVIEW → DESIGN → EXECUTE-LOOP → VERIFY → CLOSE`(`~/.opal/skills/opal-pilot-sdd/SKILL.md:23`, STATE 단계목록 `:320`) — U-2 결정 참조.
- **B-3 지원 플랫폼 표**: README "Claude Code, Cursor, Gemini (Antigravity)"(`README.md:74`). 정본 + Codex.
- **B-4 에이전트 수**: README "전문 6 + 범용 5 + GC 2"(`README.md:734`). 실제 `opal/agents/` 13개 — U-3 인접 결정 참조.

**(C) 일관성/링크 — R-4**

목차(`README.md:43-62`)는 11개 섹션. 신규 섹션 추가 시 목차 항목·내부 앵커 갱신 필요.

### 영향 범위

- 변경 대상은 `README.md` **단일 파일**. 신규/수정 섹션 모두 한 파일 내부에서 처리.
- SSOT(레지스트리·각 SKILL.md·PROJECT.md·헌법)는 **Read 전용** — 본 태스크에서 수정하지 않는다(미커밋 `M`/`??` 변경은 독립).
- README 내부 앵커 무결성(목차↔헤딩, `#앵커` 링크)이 모든 섹션 변경의 후속 영향.

---

## 2. 구현 계획

### 미확정 결정 (PLAN 확정)

#### U-1 ppt-builder 노출 여부 — **결정: README 등재 보류 (decision_required로 캡틴 확인)**

`git status` 확인 결과 `skills/ppt-builder/`는 미추적(`??`), `opal/core/references/opal-skills-registry.json`은 미커밋(`M`) 상태다. PROJECT.md 주요 컴포넌트에도 ppt-builder는 없다(`docs/PROJECT.md:53-83` 어디에도 부재). 따라서 **작업 중 산출물**로 판단하여 README 등재를 **보류**한다. README는 공개 문서이므로 미커밋 컴포넌트를 노출하면 신규 사용자가 동작하지 않는 기능을 보게 될 위험이 있다(TASK §제약 "미커밋 변경은 본 태스크와 독립"). → **decision_required: 캡틴 최종 확인 필요** (정식 컴포넌트로 커밋 예정이면 등재로 전환). `html-mockup`, `system-architecture-html`은 커밋된 정식 스킬이므로 등재 대상.

#### U-2 opsdd 파이프라인 정본 — **결정: `TASK → SPEC → REVIEW → DESIGN → EXECUTE-LOOP → VERIFY → CLOSE`**

3개 표기가 상충한다: 레지스트리(`SPEC → VERIFY → PLAN → TASKS → VERIFY → LOOP → DONE`, `opal/core/references/opal-skills-registry.json:99`), PROJECT.md(`SPEC → VERIFY → PLAN → TASKS → EXECUTE`, `docs/PROJECT.md:57`), SKILL.md. TASK §제약 + 제약(doc-code-mismatch)에 따라 **SKILL.md가 SSOT**다. SKILL.md 정본은 두 곳에서 일치한다 — Harness 모드 줄(`~/.opal/skills/opal-pilot-sdd/SKILL.md:23`)과 STATE 단계 목록(`:320`)이 모두 `TASK / SPEC / REVIEW / DESIGN / EXECUTE-LOOP / VERIFY / CLOSE`. README는 이 7단계 표기를 **모든 등장 위치(비교표 `README.md:265` + 사용법 `README.md:533`)에서 동일하게** 사용한다. (레지스트리·PROJECT.md의 상이 표기는 별도 SSOT 정합 태스크 권고 — 본 태스크 범위 밖, 리스크 R-3 참조.)

#### U-3 README 개편 범위 — **결정: 부분 보강 (구조 보존)**

현행 11개 섹션 골격(`README.md:43-62`)은 안정적이고 신규 사용자 친화적이다. 신규 기능 6건 + 정정 4건은 **기존 섹션 내 표 행·단락 추가 + 신규 하위 섹션 삽입**으로 모두 수용 가능하다. 전면 재편(섹션 재배치)은 헌법 §3 "Surgical Changes — 계획이 지정한 것만 건드린다"(`~/.opal/PRINCIPLES.md:29-33`)에 반한다. 따라서 **부분 보강**을 채택한다. 단, Pilot 목록에 `opgc`/`opbr` 2개 신규 항목이 추가되므로 목차·앵커는 R-4로 일괄 갱신한다.

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| - | (없음) | README 단일 파일 내 섹션 추가로 처리 | U-3 결정 |

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| 1 | `README.md` | 핵심 철학 표에 헌법/검증=완료 반영 (A-4) | `~/.opal/PRINCIPLES.md:12-40` |
| 2 | `README.md` | 주요 특징에 GC·브레인 추가 (A-1/A-2) | D-1, D-2 |
| 3 | `README.md` | 설치 Step 1 플랫폼 표 + Codex (B-3/A-3) | `docs/PROJECT.md:17` |
| 4 | `README.md` | 설치 Step 3 부트스트랩 체크리스트 정정 (B-1) | `~/.opal/AGENT.md:55` |
| 5 | `README.md` | Pilot 비교표에 opgc 행 추가 + opsdd 정정 (A-2/B-2) | D-1, D-5 |
| 6 | `README.md` | opsdd 사용법 파이프라인 정정 (B-2) | `~/.opal/skills/opal-pilot-sdd/SKILL.md:23` |
| 7 | `README.md` | opgc 사용법 신규 섹션 (A-2) | `~/.opal/skills/opal-pilot-gc/SKILL.md:13` |
| 8 | `README.md` | opbr 사용법 신규 섹션 (A-1) | `~/.opal/skills/opal-brain/SKILL.md:34-38` |
| 9 | `README.md` | 독립 스킬에 html-mockup·html-sa 추가 (A-7) | `opal/core/references/opal-skills-registry.json:457-484` |
| 10 | `README.md` | 모드·역할 섹션에 L2 경량 트랙 추가 (A-5) | `~/.opal/AGENT.md:141-173` |
| 11 | `README.md` | opds/opd 흐름에 RED-first 트랙 반영 (A-6) | `~/.opal/references/harness/red-first.md:18-39` |
| 12 | `README.md` | 아키텍처 개요 에이전트 수 정정 (B-4) | `opal/agents/` 13개 (D-10) |
| 13 | `README.md` | 목차·내부 앵커 무결성 갱신 (R-4) | `README.md:43-62` |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| - | (없음) | 정정은 치환으로 처리, 섹션 삭제 없음 |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | 정정군 (B-1/B-3/B-4) — 단순 문자열 치환, 앵커 무영향 | README.md | 하 |
| 2 | 철학·특징군 (A-4 + A-1/A-2 특징 언급) | README.md | 하 |
| 3 | Pilot 비교표 + opsdd 정정 (A-2/B-2) | README.md | 중 |
| 4 | 신규 사용법 섹션 (opgc·opbr) (A-1/A-2) | README.md | 중 |
| 5 | 독립 스킬 추가 (A-7) | README.md | 하 |
| 6 | 모드·트랙군 (A-5 L2 + A-6 RED-first) | README.md | 중 |
| 7 | 목차·앵커 무결성 (R-4) — 마지막 일괄 검증 | README.md | 중 |

> 원칙: 앵커에 영향 없는 정정(1·2)을 먼저, 신규 섹션 추가(3·4·5·6)를 중간, 앵커 무결성 검증(7)을 마지막에 둔다(`references/plan-guide.md` 2단계 — 통합/검증 마지막).

### 핵심 설계

모든 변경은 단일 `README.md` 내부에서 수행한다. README는 변경이력 표 대상이 아니다(TASK §제약 — 공개 소개 문서).

> **[MUST]** `~/.opal/skills/opal-pilot-sdd/SKILL.md` §STATE 단계 목록(`:320`): "TASK / SPEC / REVIEW / DESIGN / EXECUTE-LOOP / VERIFY / CLOSE" — opsdd 파이프라인을 README 전 위치에서 이 표기로 통일한다(재해석 금지, U-2).
> **[MUST]** `~/.opal/AGENT.md` §부트스트랩 완료 보고(`:55`): "`[부트스트랩] ✅ principles ✅ identity ✅ harness ✅ PM ✅ PM모드 ⏳ registry ⏳ references ⏳ model-mapping`" — README Step 3 예시 블록을 이 문자열로 정정한다(B-1).
> **[MUST]** `~/.opal/AGENT.md` §L2(`:149`): "L2 적격 = 파일 1~2개 + 단순 수정 + 동작검증(TEST) 불요 / 동작검증 필요 작업은 L2 우회 금지" — L2 설명 시 이 가드를 반드시 포함한다(A-5).
> **[MUST]** `~/.opal/references/harness/red-first.md` §1(`:18`): "RED 단계에서 실패 테스트 코드를 작성·실행하여 실패(exit code≠0)를 증거로 기록한 뒤 GREEN(구현) 진입. RED 증거 없이 GREEN 진입 금지." — RED-first 설명의 핵심 규칙(A-6).

**1) 핵심 철학 표 (A-4)** — `README.md:24-30` 표에 행 추가 또는 보강:
- 기존 "사용자 주권" 행은 헌법 Core Stance "User sovereignty"(`~/.opal/PRINCIPLES.md:13`)와 정합 — 유지.
- 추가/보강: **"검증된 완료"** — "완료는 생성된 문서가 아니라 검증된 동작을 의미한다"(→ D-4 헌법 Core Stance `:14` "Done means verified behavior, not a generated document").
- 추가/보강: **"강제 우선"** — "항상 지켜야 하는 규칙은 조언이 아니라 도구로 강제한다"(→ D-4 `:15` "Enforce, don't just advise").
- "OPAL 헌법(PRINCIPLES.md)이 모든 하네스·스킬·에이전트의 행동 SSOT"라는 한 줄을 표 하단 또는 도입부에 추가(→ D-4 `:8-10`).

**2) 주요 특징 (A-1/A-2)** — `README.md:34-40` 불릿에 2개 추가:
- "**프로젝트 브레인(`//opbr`)** — 프로젝트 WHY·HOW 지식을 마크다운 위키로 누적·질의"(→ D-7, D-2 `:73-83`).
- "**경량 품질 게이트(`//opgc`)** — 커밋 전 보안·컨벤션 진단 (OWASP/CWE/SANS 기반)"(→ D-6, D-2 `:63-71`).

**3) 설치 Step 1 플랫폼 (B-3/A-3)** — `README.md:74` 행 치환:
- "지원 AI 플랫폼: Claude Code, Cursor, Gemini (Antigravity), **Codex**"(→ D-2 `:17`, D-3 `:370-374`).
- Step 3 안내 문구(`README.md:103`)의 "Claude Code / Cursor / Gemini"도 Codex 포함으로 정정.

**4) 설치 Step 3 부트스트랩 (B-1)** — `README.md:106` 코드블록 치환: 위 [MUST] 정본 문자열. `[안내]` 줄은 정본(`~/.opal/AGENT.md:56`)이 동적값이므로 현행 예시 유지 가능.

**5) Pilot 비교표 + opsdd 정정 (A-2/B-2)** — `README.md:259-267` 표:
- opsdd 행(`:265`) 파이프라인 → U-2 정본으로 치환.
- **opgc 신규 행** 추가: `| //opgc | 품질 게이트 (GC) | 커밋 전 진단 | SCAN → CHECK → REPORT → CLOSE | GC-SECURITY/CONVENTION 보고서, DONE |`(→ D-6 `:13`).
- opbr은 Pilot 비교표에 넣지 않고 별도 섹션으로 다룸(브레인은 4모드 도구 성격 — 파이프라인 표와 이질). 선택 가이드(`README.md:271-282`)에도 "프로젝트 지식 축적·질의: `//opbr`" 한 줄 추가 검토.
- §689 "모든 Pilot(...)에 동일 적용" 목록에 opgc 추가 여부는 EXECUTE에서 판단(opgc는 3-way 중 interactive/agentic만 — `~/.opal/skills/opal-pilot-gc/SKILL.md:17-19`, semi-agentic 없음 → 목록에 넣지 않거나 주석 처리).

**6) opsdd 사용법 정정 (B-2)** — `README.md:533` 파이프라인 줄 → U-2 정본 치환. 산출물 트리(`:537-548`)는 SKILL.md 폴더 구조(`~/.opal/skills/opal-pilot-sdd/SKILL.md:75-90`)와 정합 확인 후 유지.

**7) opgc 사용법 신규 섹션 (A-2)** — Pilot 사용법군 끝(`README.md:597` oppd 다음) 또는 독립 위치에 추가:
- 언제 쓰나: 커밋 전 보안·컨벤션 진단(진단 전담, 수정은 opds 체인).
- 파이프라인: `SCAN → CHECK → REPORT → CLOSE`(→ D-6 `:13`).
- 호출 예: `//opgc`(전체), `//opgc --security`, `//opgc --convention`, `//opgc --scope all`(→ D-6 `:30-37`).
- 산출물: `GC-SECURITY-{ts}.md`, `GC-CONVENTION-{ts}.md`, `DONE.md`(→ D-6 `:65-69`).

**8) opbr 사용법 신규 섹션 (A-1)** — 독립 스킬군 또는 신규 "프로젝트 브레인" 섹션:
- 4모드: `init`(부트스트랩) / `ingest`(지식 누적) / `query`(`//opbr ask` 질의) / `lint`(무결성 정비)(→ D-7 `:34-38`).
- 호출 예: `//opbr init`, `//opbr ingest --all`, `//opbr ask "질문"`, `//opbr lint`(→ D-7 `:34-38`).
- 저장 위치: `.opal/brain/`(프로젝트 자산)(→ D-2 `:83`). code-scan(WHAT)·MEMORY(운영 기억)와 역할 분리(WHY/HOW)(→ D-2 `:83`).

**9) 독립 스킬 추가 (A-7)** — `README.md:600-675` §독립 스킬에 2개 추가(ppt-builder는 U-1로 보류):
- **html-mockup (`//mockup`)** — CDN 기반 정적 HTML 화면 빠른 생성(→ D-1 `:457-470`).
- **system-architecture-html (`//html-sa`)** — 시스템 아키텍처 다이어그램 HTML 생성(→ D-1 `:471-484`).
- 기존 목록(api-analyzer/wireframe-builder/ui-designer/interview/web-to-markdown/erd-modeler)과 레지스트리 standalone 그룹 1:1 대조 — 레지스트리에 있으나 README 누락분만 추가, README에 있으나 레지스트리에 없는 항목은 없음(대조 결과).

**10) L2 경량 트랙 (A-5)** — `README.md:242-251` "비서/PM 모드" 섹션 뒤 또는 모드 섹션에 추가:
- "그냥 해 / 직접 수행" 발화 = L2 경량 트랙 진입 신호. 태스크 파이프라인 우회, PM 직접 수정(→ D-3 `:141-143`).
- **[MUST] 가드**: L2 적격 = 파일 1~2개 + 동작검증(TEST) 불요. 동작검증 필요 작업은 L2 우회 금지(→ D-3 `:149-152`).
- 3-way 모드(interactive/semi-agentic/agentic)와는 **별개 축**임을 명시(→ D-3 `:143`).

**11) RED-first 트랙 (A-6)** — `README.md:443-455`(opds) / `:481-496`(opd) 흐름 또는 QA 내장 특징(`:36`)에 반영:
- RED→GREEN: 실패 테스트 작성·실행(증거 기록) → 구현(→ D-9 `:18`).
- 적용 기준(하이브리드 자동분기): 비즈니스 로직·DB·API 계약·인증·버그수정 = RED-first 강제 / UI·탐색·리팩터·문서 = 구현 후 검증 허용(→ D-9 `:24-39`).
- 작성자≠구현자: RED는 opal-test-agent(mode: red), 구현은 op-dev-execute 분리(→ D-9 `:33-35`).

**12) 아키텍처 개요 에이전트 수 (B-4)** — `README.md:734` 줄 정정. 실제 `opal/agents/` 13개(D-10) 분류:

| 분류 | 에이전트 | 수 |
|------|---------|---|
| 도메인 전문 | opal-be / opal-fe / opal-db / opal-plan / opal-planning / opal-test / opal-wtm | 7 |
| 범용·액션 러너 | opal-task / opal-task-qa / opal-sdd-action / opal-task-action | 4 |
| GC 체커 | opal-security-checker / opal-convention-checker | 2 |
| **합계** | | **13** |

- 정정안: "**전문 7 + 범용 4 + GC 2 = 13**"(→ D-10 `opal/agents/` 13개 폴더). 현행 "전문 6 + 범용 5 + GC 2 = 13"(`README.md:734`)은 총합은 맞으나 전문/범용 분류가 틀림. (분류 경계는 설명 편의이므로 EXECUTE에서 "워커 13종"으로 단순 표기하는 대안도 허용 — 리스크 R-4 참조.)

**13) 목차·앵커 무결성 (R-4)** — `README.md:43-62` 목차:
- 신규 섹션(opgc 사용법, opbr 사용법, L2 트랙) 추가 시 목차 항목 + 내부 `#앵커` 추가.
- 한글 헤딩 앵커 규칙(공백→`-`, 특수문자 제거)에 맞춰 `#opgc--품질-게이트` 등 정확히 생성.
- 변경 후 모든 목차 항목이 실제 헤딩과 매칭되는지, 본문 `#앵커` 링크가 존재 헤딩을 가리키는지 EXECUTE에서 grep 검증.

---

## 3. 실행 체크리스트

> 총 8개 Step | Phase 4개
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1 | 1, 2 | 순차 | 동일 파일 README.md — Step 간 순차 필수 |
> | 2 | 3, 4, 5 | 순차 | 동일 파일 — 신규 섹션 추가 |
> | 3 | 6, 7 | 순차 | 동일 파일 — 모드·트랙 |
> | 4 | 8 | 순차 | 앵커 무결성 최종 검증 |
>
> **[중요] 전 Step 동일 파일(README.md) 대상 → 병렬 불가, 전체 순차 실행.** (plan-guide §Phase 그룹핑 규칙 3: 동일 파일 수정 Step은 반드시 순차.)

### Step 1: 정정군 (B-1/B-3/B-4) — 앵커 무영향 단순 치환
- [x] 완료
- **파일**: `README.md`
- **작업 내용**: ① Step 3 부트스트랩 체크리스트(`:106`)를 정본 문자열로 치환(B-1, [MUST] §2 정본). ② 설치 Step 1 플랫폼 행(`:74`) + Step 3 안내(`:103`)에 Codex 추가(B-3/A-3). ③ 아키텍처 개요 에이전트 수(`:734`)를 "전문 7 + 범용 4 + GC 2"로 정정(B-4).
- **완료 기준**: 3개 문자열이 각 SSOT(AGENT.md `:55` / PROJECT.md `:17` / `opal/agents/` 13개)와 일치. 정정 외 줄 변경 없음.
- **테스트**: `grep "principles" README.md`로 체크리스트 정정 확인 / `grep -c "Codex" README.md` ≥ 2 / `grep "전문 7" README.md` 존재.
- **의존**: 없음

### Step 2: 철학·특징군 (A-4 + A-1/A-2 특징)
- [x] 완료
- **파일**: `README.md`
- **작업 내용**: ① 핵심 철학 표(`:24-30`)에 "검증된 완료"·"강제 우선" 반영 + 헌법 SSOT 한 줄(A-4, →D-4). ② 주요 특징(`:34-40`)에 브레인·GC 불릿 2개 추가(A-1/A-2).
- **완료 기준**: 헌법 Core Stance 4원칙(`~/.opal/PRINCIPLES.md:13-16`)이 철학 표에 반영. 특징에 `//opbr`·`//opgc` 언급 존재.
- **테스트**: `grep -E "검증된|verified|brain|opbr|opgc" README.md` 매칭.
- **의존**: Step 1

### Step 3: Pilot 비교표 + opsdd 정정 (A-2/B-2)
- [x] 완료
- **파일**: `README.md`
- **작업 내용**: ① 비교표(`:259-267`) opsdd 행을 U-2 정본 파이프라인으로 치환. ② opgc 행 추가(SCAN→CHECK→REPORT→CLOSE). ③ 선택 가이드(`:271-282`)에 opbr 한 줄 검토 추가.
- **완료 기준**: 비교표에 opgc 행 존재 + opsdd 표기가 U-2 정본([MUST] §1)과 일치.
- **테스트**: `grep "REVIEW → DESIGN → EXECUTE-LOOP → VERIFY → CLOSE" README.md` 존재 / `grep "SCAN → CHECK → REPORT → CLOSE" README.md` 존재.
- **의존**: Step 2

### Step 4: opsdd 사용법 정정 + opgc·opbr 신규 사용법 섹션 (A-1/A-2/B-2)
- [x] 완료
- **파일**: `README.md`
- **작업 내용**: ① opsdd 사용법 파이프라인(`:533`)을 U-2 정본으로 치환. ② opgc 사용법 신규 섹션 추가(파이프라인·호출 예·산출물 — →D-6). ③ opbr 사용법 신규 섹션 추가(4모드·호출 예·저장 위치 — →D-7, D-2).
- **완료 기준**: opsdd 사용법 표기가 비교표와 동일(U-2 일관). opgc/opbr 섹션이 각 1개 이상 호출 예 포함.
- **테스트**: README 내 `EXECUTE-LOOP → VERIFY → CLOSE` 등장 2회 일치(비교표+사용법) / `grep -E "//opgc|//opbr" README.md` 매칭.
- **의존**: Step 3 (opsdd 표기 일관성)

### Step 5: 독립 스킬 추가 (A-7)
- [x] 완료
- **파일**: `README.md`
- **작업 내용**: §독립 스킬(`:600-675`)에 html-mockup(`//mockup`)·system-architecture-html(`//html-sa`) 추가. ppt-builder는 U-1 결정으로 **보류**(decision_required 미해소 시 미등재). 레지스트리 standalone 그룹과 1:1 대조.
- **완료 기준**: 레지스트리 standalone 노출 스킬(ppt-builder 제외)과 README 독립 스킬 목록 1:1 대응. 존재하지 않는 스킬 없음.
- **테스트**: `grep -E "html-mockup|html-sa|mockup" README.md` 매칭 / 레지스트리 standalone 8개 중 ppt 제외 7개 ↔ README 대조표 일치.
- **의존**: Step 4

### Step 6: L2 경량 트랙 (A-5)
- [x] 완료
- **파일**: `README.md`
- **작업 내용**: 비서/PM 모드 섹션(`:242-251`) 또는 3-way 모드 섹션에 L2 경량 트랙 설명 추가. [MUST] §3 가드(동작검증 필요 시 L2 금지) + 3-way와 별개 축 명시.
- **완료 기준**: "그냥 해/직접 수행" = L2 + 적격 기준(파일 1~2개, TEST 불요) + 가드가 본문에 존재.
- **테스트**: `grep -E "L2|그냥 해|직접 수행" README.md` 매칭 + 가드 문구 포함 확인.
- **의존**: Step 5

### Step 7: RED-first 트랙 (A-6)
- [x] 완료
- **파일**: `README.md`
- **작업 내용**: opds/opd 흐름(`:443-455`, `:481-496`) 또는 QA 내장 특징(`:36`)에 RED-first 트랙 반영. RED→GREEN 순서 + 하이브리드 자동분기 기준 + 작성자≠구현자(→D-9).
- **완료 기준**: RED→GREEN, RED-first 강제/허용 영역, 작성자≠구현자 3요소가 본문에 존재.
- **테스트**: `grep -iE "RED-first|RED→GREEN|실패 테스트" README.md` 매칭.
- **의존**: Step 6

### Step 8: 목차·앵커 무결성 최종 검증 (R-4)
- [x] 완료
- **파일**: `README.md`
- **작업 내용**: 신규 섹션(opgc 사용법·opbr 사용법·L2 트랙 등)을 목차(`:43-62`)에 추가하고 내부 `#앵커`를 생성. 한글 헤딩 앵커 규칙 적용. 전체 목차↔헤딩, 본문 `#앵커`↔헤딩 매칭 검증.
- **완료 기준**: 목차 모든 항목이 실제 헤딩과 매칭. README 내부 `#앵커` 링크가 모두 존재 헤딩을 가리킴(깨진 링크 0).
- **테스트**: 목차 앵커 목록 vs 본문 헤딩 슬러그 대조(수동/스크립트). `grep -oE "\(#[^)]+\)" README.md`로 내부 앵커 추출 → 각 헤딩 존재 확인.
- **의존**: Step 1~7 (모든 섹션 변경 완료 후 일괄 검증)

---

## 4. QA 체크리스트

### 기능 테스트 (R-1~R-4 커버리지)
- [x] R-1: A-1~A-6 6개 항목이 README 본문에 각각 1개 이상 단락/표 행으로 존재 (브레인/GC/Codex/헌법/L2/RED-first)
- [x] R-1: 약어(`//opbr`,`//opgc`)·파이프라인·모드 설명이 레지스트리·PROJECT.md와 일치
- [x] R-2 B-1: 부트스트랩 체크리스트가 `~/.opal/AGENT.md:55` 문자열과 일치(principles 선두)
- [x] R-2 B-2: opsdd 파이프라인이 README 모든 등장 위치에서 U-2 정본으로 동일
- [x] R-2 B-3: 지원 플랫폼 표에 Codex 포함
- [x] R-2 B-4: 에이전트 수가 `opal/agents/` 13개 실제 구성과 합치
- [x] R-3: 레지스트리 standalone 그룹(ppt 제외)과 README 독립 스킬 1:1 대응
- [x] R-4: 목차·내부 앵커 무결성 (깨진 링크 0)

### 일관성 테스트
- [x] opsdd 파이프라인 표기가 비교표·사용법 2곳에서 문자 단위 동일
- [x] 신규 약어(opgc/opbr)가 목차·비교표·사용법에서 동일 표기
- [x] 기존 11개 섹션 골격 보존(U-3 부분 보강 — 섹션 재배치 없음)
- [x] 정정 외 기존 문장의 의도치 않은 변경 없음(헌법 §3 Surgical Changes)

### 문서 품질
- [x] 한국어 본문 + 영어 코드/약어(`//opbr` 등) 규칙 준수
- [x] SSOT 미커밋 컴포넌트(ppt-builder) 미노출(U-1) — decision_required 미해소 시
- [x] 상상·추정 기재 없음 — 모든 신규 내용이 §1 SSOT 근거 보유(citation-rules §0)

---

## 5. 리스크 및 대응

| # | 리스크 | 영향 | 대응 방안 |
|---|--------|------|----------|
| R-1 | U-1 ppt-builder 미커밋 — 등재 시 동작 안 하는 기능 노출 | 신규 사용자 혼란 | **보류**(미등재) + decision_required로 캡틴 확인. 정식 커밋 시 등재 전환 |
| R-2 | opsdd 파이프라인 3개 표기 상충(레지스트리/PROJECT.md/SKILL.md) | README가 어느 것을 따를지 모호 | SKILL.md SSOT 확정(U-2). README는 정본만 사용 |
| R-3 | 용어 불일치 — 레지스트리(`SPEC→VERIFY→PLAN→TASKS→VERIFY→LOOP→DONE`)·PROJECT.md(`…→EXECUTE`) ↔ SKILL.md 정본 | SSOT 간 불일치 잔존(README 범위 밖) | README는 SKILL.md 정본 채택. 레지스트리·PROJECT.md 정합은 별도 태스크 권고(본 태스크 미수정 — TASK §제약) |
| R-4 | B-4 에이전트 전문/범용 분류 경계 모호(7+4 vs 6+5) | 분류 표기 재해석 여지 | 합계 13 고정 + 분류는 설명 편의로 명시. 모호하면 "워커 13종"으로 단순화 허용 |
| R-5 | 신규 섹션 추가로 목차 앵커 깨짐(한글 슬러그) | 내부 링크 무효 | Step 8 일괄 검증 — grep 기반 앵커↔헤딩 대조 |
| R-6 | 배포 경계 위반 위험(`~/.opal/` 직접 수정) | 메모리 피드백 위반 | SSOT는 Read 전용. 변경은 프로젝트 `README.md`만 |
