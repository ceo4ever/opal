# PLAN: OPAL 부트스트랩 스킵 옵션 (`OPAL_BOOTSTRAP=off`)

> 작성일: 2026-06-24 | 입력: TASK.md (ANALYSIS.md 없음 — F-NNN별 직접 코드 분석)
> 모드: Multi-Feature

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

환경변수 `OPAL_BOOTSTRAP=off` 설정 시 OPAL 부트스트랩 전체(정체성 포함)를 스킵하여 순수 Claude Code(및 Cursor/Codex/Gemini)로 동작하게 하는 옵션을 추가한다. 4종 플랫폼 마커 텍스트 서두에 "Bash로 `echo $OPAL_BOOTSTRAP` 실행 → `off`이면 이하 절차 전체 생략" skip 게이트를 삽입하고, `opal/core/AGENT.md` Eager 절차 최상단에 동일 게이트를 명문화한다.

### 1.2 핵심 아키텍처 정정 (TASK 전제 vs 실제 구조)

> **[중요]** TASK.md F-1~F-4·F-6은 "install-mac.sh / windows.ps1의 **마커 emit 함수**에 skip 게이트 문구를 삽입"하라고 기술한다. 그러나 실제 코드를 읽은 결과(아래 §2 분석), 이 전제는 코드 구조와 일치하지 않는다. 정정된 설계를 채택한다.

| 항목 | TASK.md 전제 | 실제 구조 (코드 확인 결과) |
|------|------------|--------------------------|
| 마커 텍스트 위치 | install-mac.sh / windows.ps1 emit 함수에 인라인 | **`opal/bootstrapper/*.md` 4개 파일**의 코드블록 (`` ```markdown ``)이 SSOT |
| install-mac.sh 역할 | 마커 문구를 직접 생성 | `extract_bootstrap_content()`로 bootstrapper `.md`에서 **추출만** 함 (`scripts/install-mac.sh:237-245`) — 문구 미보유 |
| windows.ps1 경로 | `scripts/windows.ps1` | **존재하지 않음.** 실제 미러는 `scripts/install/windows.ps1` |
| windows 미러 역할 | 마커 문구를 직접 생성 | `Get-BootstrapContent()`로 동일 `.md`에서 **추출만** 함 (`scripts/install/windows.ps1:201-224`) — 문구 미보유 |

**정정의 귀결**: emit 함수(install_opal_section / Install-OpalSection)는 **content-agnostic**(어떤 텍스트든 마커로 감싸 배포)이므로, 마커 문구를 emit 함수에서 수정하는 것은 불가능하고 불필요하다. skip 게이트 문구는 **4개 bootstrapper 소스 `.md` 파일을 수정**하면 macOS·Windows 양쪽 어댑터가 자동으로 동일하게 배포한다. 이로써 TASK의 완료기준 ③("4종 플랫폼 마커 emit에 skip 게이트 포함")과 F-6(Windows 미러)이 **단일 수정 지점**으로 동시 충족된다 — 어댑터 계층 SSOT 원칙(→ D-1 §아키텍처)에 정확히 부합한다.

> [MUST] `.opal/AGENT.md` §금지사항: "하드코딩된 플랫폼 분기 추가 금지 — Claude/Cursor/Gemini 분기는 어댑터 계층(install·plugin)에서만 수행한다." → 본 정정은 이 원칙을 강화한다(분기 없이 SSOT 1지점 수정).
> [MUST] `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다." → 모든 수정 대상은 소스(`opal/`, `scripts/`)에 한정.

### 1.3 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | bootstrapper 4종 `.md` 마커에 skip 게이트 문구 삽입 (Claude/Cursor/Codex/Gemini) | F-1, F-2, F-3, F-4 (정정 통합) | P0 | 없음 |
| F-002 | `opal/core/AGENT.md` Eager 절차 최상단에 skip 게이트 명문화 | F-5 | P0 | 없음 |
| F-003 | Windows 미러 정합성 검증 (`scripts/install/windows.ps1`) | F-6 (정정) | P0 | F-001 |

> **F-1~F-4 통합 근거**: 4종 플랫폼 마커는 모두 동일 skip 게이트 문구를 받으며 동일 `opal/bootstrapper/` 디렉토리의 형제 파일이다. 논리적으로 함께 테스트 가능한 단일 묶음이므로 F-001로 통합한다(가이드 §1 그룹핑 기준 — "논리적으로 함께 테스트 가능한 요구사항 묶음"). 단, 4개 파일 각각의 변경은 §3.1·§5.1에서 개별 추적한다.
> **F-003(F-6) 성격 전환**: 정정에 따라 windows.ps1은 **코드 수정 불필요**(동일 bootstrapper 소비). 따라서 F-003은 "수정"이 아닌 "미러 자동 반영 검증" 기능으로 전환한다.

### 1.4 기능 의존 그래프 (ASCII)

```
F-001 (bootstrapper 4종 마커 수정) ──> F-003 (windows 미러 검증)
F-002 (AGENT.md Eager 게이트 명문화)   [독립]
```

### 1.5 핵심 제약 (PLAN 영향 [MUST] 인용)

- [MUST] `opal/core/AGENT.md` §행동규칙(소스 PM 프로필 `.opal/AGENT.md` §금지사항): "`~/.opal/` 직접 편집 금지 — 항상 소스 수정 후 install 재배포" (→ D-1 §60)
- [MUST] `.opal/AGENT.md` §금지사항: "하드코딩된 플랫폼 분기 추가 금지 — Claude/Cursor/Gemini 분기는 어댑터 계층(install·plugin)에서만 수행한다" (→ D-1 §62)
- [MUST] `opal/core/references/opal-harness.md` §1 Guards: "사용자 명시 승인 전 코드 파일 생성/수정 금지" → 본 PLAN 단계는 문서(PLAN.md)만 작성, 소스 미수정 (→ D-5)
- 제약(TASK §제약): "`off` 외 다른 값(미설정/on/기타)은 기존 동작과 동일" → skip 게이트 조건은 **정확히 `off`** 단일 매칭으로 작성 (조건 단순성)

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-001 (4종 `.md` 코드블록) | `extract_bootstrap_content` / `Get-BootstrapContent`가 추출하는 코드블록 경계(`` ```markdown ``~`` ``` ``). 게이트 문구에 백틱/특수문자 삽입 시 코드블록 조기 종료·추출 깨짐 | P0 (부트스트랩 전체 불능) | L1(산출물 검사: 추출 결과 grep) + L2(install 재배포 후 `~/.claude/CLAUDE.md` 내용 확인) | S-1, S-2 |
| H-2 | F-001 게이트 조건 표현 | LLM이 "`off`이면 스킵"을 과확대 해석 → `on`/미설정 세션도 스킵하거나, Bash 미보유 플랫폼에서 무한 대기 | P0 (정상 세션 부트스트랩 누락) | L1(문구 명확성 리뷰) + L3(설정/미설정 세션 실동작) | S-3, S-4 |
| H-3 | F-001 cursor `.mdc` | cursor-bootstrap.mdc는 frontmatter(`---`)+산문 구조이며 코드블록 추출이 아닌 **파일 전체 복사**(install-mac.sh:1092, windows.ps1:816-818). 다른 3종과 삽입 방식이 다름 → 게이트 문구 삽입 위치·포맷 상이 | P0 (Cursor 마커 누락 또는 frontmatter 파손) | L1(파일 구조 검사) + L2(배포 후 `.mdc` 확인) | S-5 |
| H-4 | F-001 Bash 의존 | Cursor/Gemini/Codex 일부 환경이 Bash 도구 미보유 → `echo $OPAL_BOOTSTRAP` 실행 불가 시 폴백 정의 부재로 행 멈춤 | P1 (특정 플랫폼 부트스트랩 지연/실패) | L1(문구에 "Bash 미보유 시 게이트 무시하고 정상 진행" 폴백 명시 검토) | S-6 |
| H-5 | F-002 (AGENT.md Eager) | Eager 절차 step 번호 체계(1, 2, 2.5, 3...) 및 `[WORKER 규칙]` 블록과의 구분. 게이트를 step 1 앞 "step 0"으로 추가 시 후속 번호 불변 유지 필요 | P1 (문서 정합 — 마커 동작과 AGENT.md 정의 불일치) | L1(AGENT.md §Eager 구조 검사: 게이트가 step 1보다 앞, [WORKER]와 구분) | S-7 |
| H-6 | F-001 + F-002 문구 동기 | 마커 게이트 문구와 AGENT.md 게이트 문구의 조건(정확히 `off`)·동작(전부 스킵) 불일치 | P1 (문서 간 모순) | L1(양측 문구 의미 일치 교차 검사) | S-8 |
| H-7 | F-003 (windows 미러) | windows.ps1이 동일 bootstrapper를 소비하지 못하는 숨은 분기(인라인 문구 잔존 등) | P1 (Windows에서 게이트 누락) | L1(windows.ps1에 인라인 마커 문구 부재 + Get-BootstrapContent 동일 소스 참조 확인) | S-9 |

**가설 도출 메모**: H-1·H-3는 추출 메커니즘 의존성(코드블록 경계·복사 방식 차이)이 핵심 리스크. H-2·H-4는 "LLM이 읽는 산문 게이트"의 본질적 모호성 리스크 — 문구 정밀도가 완료기준을 좌우한다.

---

## 2. 기능별 분석

### F-001: bootstrapper 4종 `.md` 마커에 skip 게이트 문구 삽입

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 환경 | `opal/bootstrapper/claude-bootstrap.md` | Claude `~/.claude/CLAUDE.md` 마커 SSOT (코드블록 추출 방식) | 수정 |
| 환경 | `opal/bootstrapper/cursor-bootstrap.mdc` | Cursor `~/.cursor/rules/000-opal-agent.mdc` 마커 SSOT (**파일 전체 복사** 방식) | 수정 |
| 환경 | `opal/bootstrapper/codex-bootstrap.md` | Codex `~/.codex/AGENTS.md` 마커 SSOT (코드블록 추출) | 수정 |
| 환경 | `opal/bootstrapper/gemini-bootstrap.md` | Gemini `~/.gemini/GEMINI.md` 마커 SSOT (코드블록 추출) | 수정 |
| 배치 | `scripts/install-mac.sh` | 위 `.md`에서 코드블록 추출·배포 (수정 없음, 동작 검증 대상) | 검증 |

#### 2.1.2 현재 구현

3종(claude/codex/gemini) bootstrap `.md`는 동일 구조다 — 산문 헤더 + `` ```markdown ``…`` ``` `` 코드블록 안에 마커 본문:

```
## OPAL AI Agent — 필수 부트스트랩

**[MUST]** 사용자의 첫 번째 메시지에 응답하기 전에, 아래 파일들을 Read 도구로 순서대로 읽고 ...

1. `~/.opal/AGENT.md` — 에이전트 정의 및 부트스트랩 절차
2. `~/.opal/identity.md` — 에이전트 정체성 (없으면 ...)
```

(`opal/bootstrapper/claude-bootstrap.md:14-21`, `codex-bootstrap.md:14-21`, `gemini-bootstrap.md:14-21`)

추출 로직: `extract_bootstrap_content()`는 `` ```markdown `` 다음 줄부터 `` ``` `` 전까지를 `sed`로 추출 (`scripts/install-mac.sh:237-245`). Windows는 `Get-BootstrapContent()` 동일 로직 (`scripts/install/windows.ps1:201-224`). 추출 결과는 `install_opal_section`이 `# === OPAL START ===` / `# === OPAL END ===` 마커로 감싸 대상 파일에 멱등 삽입 (`scripts/install-mac.sh:247-321`).

cursor-bootstrap.mdc는 **구조가 다르다** — frontmatter(`---` + `description`/`alwaysApply`) + 산문 본문이며 코드블록이 없다:

```
---
description: OPAL AI 에이전트 부트스트래퍼. ...
alwaysApply: true
---

# OPAL AI Agent

세션 시작 시 ~/.opal/AGENT.md를 Read로 읽어 AI 에이전트로 활성화한다.
파일이 없으면 ~/.opal/skills/opal-onboarding/SKILL.md를 읽어 온보딩을 시작한다.
```

(`opal/bootstrapper/cursor-bootstrap.mdc:1-10`). 배포는 코드블록 추출이 아니라 **파일 전체 복사**다 (`scripts/install-mac.sh:1092` `cp ... 000-opal-agent.mdc`; windows는 CRLF 정규화 복사 `scripts/install/windows.ps1:816-818`).

#### 2.1.3 영향 범위

- **상위 의존(소비자)**: `install_opal_section`(mac), `Install-OpalSection`(win), cursor는 `cp`/`Set-ContentNoBom` 직접 복사. 모두 content-agnostic — 삽입 문구가 무엇이든 그대로 배포.
- **추출 경계 민감도**: claude/codex/gemini는 코드블록 내부에 추가 백틱(`` ``` ``) 또는 `` ```markdown `` 라인이 들어가면 추출이 조기 종료된다(H-1). 게이트 문구에는 코드 펜스를 쓰지 않고 인라인 백틱(`` `echo $OPAL_BOOTSTRAP` ``)만 사용한다.
- **관련 테스트**: bash/markdown 정적 파일 — 단위 테스트 프레임워크 없음. 검증은 산출물 검사(추출 결과 grep) + install 재배포 후 배포 파일 확인(L2)로 수행 (→ §4 RED-first 판단).

---

### F-002: `opal/core/AGENT.md` Eager 절차 최상단에 skip 게이트 명문화

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | `opal/core/AGENT.md` | OPAL AGENT 정의 소스 (배포본 `~/.opal/AGENT.md`의 원천) | 수정 |

#### 2.2.2 현재 구현

`opal/core/AGENT.md`의 부트스트랩 구조 (`opal/core/AGENT.md:5-24`):

- §부트스트랩 헤더(:5) 아래 `[설계 원칙]` 블록(:7), `[WORKER 규칙]` 블록(:9)
- `### Eager 단계 (세션 시작 시 즉시 수행)`(:11) 아래 번호 절차: step 1(:13) → step 2(:14) → step 2.5(:15) → step 3(:16) → step 4(:17) → step 5(:18) → step 6(:19) → step 6.5(:20) → step 7(:24)

`[WORKER 규칙]`(:9)은 "디스패치 프롬프트 첫 줄 `[WORKER]`이면 부트스트랩 전체 건너뛰고 즉시 작업 시작" — **워커 전용** 스킵이다. 신규 게이트는 이와 **구분**되는 **캡틴/세션 전역** 스킵이어야 한다 (TASK F-5 AC: "`[WORKER]` 스킵과 구분되어 기술됨").

#### 2.2.3 영향 범위

- **상위 의존(소비자)**: 모든 OPAL 세션의 부트스트랩 진입 — `~/.opal/AGENT.md`(배포본)를 Read하는 시점. install `strip_deploy_md`가 "## 변경이력" 이전까지만 배포하므로(`scripts/install-mac.sh:220-224`), 게이트 문구는 변경이력 섹션 위(본문)에 위치해야 배포된다.
- **마커와의 관계**: 마커(F-001)는 "`~/.opal/AGENT.md`를 Read하라"고 지시 → AGENT.md Eager 게이트(F-002)는 마커가 이미 Bash 체크를 통과해 AGENT.md를 읽기 시작한 뒤의 **2차 방어선/문서 정합** 역할. 두 게이트의 조건·동작은 일치해야 한다(H-6).
- **번호 체계 영향**: 게이트를 "step 0"(step 1 앞)으로 추가하면 기존 1~7 번호 불변(H-5). step 재번호는 회귀 위험이므로 금지.

---

## 3. 기능별 설계

### F-001: bootstrapper 4종 `.md` 마커에 skip 게이트 문구 삽입

#### 3.1.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/bootstrapper/claude-bootstrap.md` | 환경 | 코드블록 본문 서두(`## OPAL AI Agent — 필수 부트스트랩` 직후, `**[MUST]**` 앞)에 skip 게이트 문단 삽입 + 변경이력 행 추가 | `claude-bootstrap.md:15-17` |
| 2 | `opal/bootstrapper/codex-bootstrap.md` | 환경 | #1과 동일 위치·문구 | `codex-bootstrap.md:15-17` |
| 3 | `opal/bootstrapper/gemini-bootstrap.md` | 환경 | #1과 동일 위치·문구 | `gemini-bootstrap.md:15-17` |
| 4 | `opal/bootstrapper/cursor-bootstrap.mdc` | 환경 | frontmatter 종료(`---`) 직후, `# OPAL AI Agent` 본문 앞(또는 본문 첫 문장 앞)에 skip 게이트 문단 삽입 (코드블록 없음 — 산문 직접 삽입) | `cursor-bootstrap.mdc:5-9` |

> 근거: 추출 메커니즘 — claude/codex/gemini=코드블록 추출(`scripts/install-mac.sh:237-245`), cursor=파일 전체 복사(`scripts/install-mac.sh:1092`).

#### 3.1.2 API·데이터 모델·화면 설계

해당 없음 (마크다운 산문 변경). 대신 **삽입 문구 초안**을 워커가 그대로 사용할 수 있도록 확정한다.

##### skip 게이트 문구 초안 — claude/codex/gemini 코드블록용 (3종 동일)

`## OPAL AI Agent — 필수 부트스트랩` 헤딩 바로 아래, `**[MUST]** 사용자의 첫 번째 메시지...` 문장 **앞**에 아래 문단을 삽입한다:

```
> **[스킵 게이트]** 먼저 Bash 도구로 `echo $OPAL_BOOTSTRAP`를 1회 실행한다. 출력이 정확히 `off`이면 — 이하 OPAL 부트스트랩 절차 전체(정체성 포함)를 생략하고, OPAL 없이 순수 Claude Code로 동작한다. 출력이 `off`가 아니거나(미설정/`on`/기타) Bash 도구를 사용할 수 없으면 — 게이트를 무시하고 아래 절차를 정상 수행한다.
```

> 설계 결정 근거:
> - "정확히 `off`" 단일 매칭 — TASK §제약 "`off` 외 다른 값은 기존 동작" 충족, H-2 방어 (→ TASK §제약 L88).
> - "Bash 사용 불가 시 정상 수행" 폴백 — H-4 방어. 게이트 미동작이 부트스트랩 누락이 아니라 정상 동작으로 안전하게 수렴(fail-safe).
> - 코드 펜스(`` ``` ``) 미사용, 인라인 백틱만 사용 — 추출 경계 보존, H-1 방어.
> - [MUST] 조건/동작을 마커·AGENT.md 양측 동일 표현으로 작성 — H-6 방어.

##### skip 게이트 문구 초안 — cursor `.mdc`용 (산문 직접)

frontmatter `---` 종료 직후 `# OPAL AI Agent` 헤딩 아래, 기존 "세션 시작 시 ..." 문장 **앞**에 삽입:

```
**[스킵 게이트]** 먼저 Bash 도구로 `echo $OPAL_BOOTSTRAP`를 1회 실행한다. 출력이 정확히 `off`이면 이하 OPAL 활성화 절차(정체성 포함)를 전부 생략하고 순수 동작한다. `off`가 아니거나 Bash 도구가 없으면 게이트를 무시하고 아래 절차를 정상 수행한다.
```

> cursor는 코드블록 인용(`>`) 렌더링이 불필요(파일 전체가 룰 본문) → `**[스킵 게이트]**` 강조 인라인으로 작성. 의미는 3종과 동일(H-6 동기).

#### 3.1.3 환경 변경

해당 없음. (install 재배포 시 발효 — TASK 완료기준 전제. 본 PLAN/EXECUTE 단계에서 install 실행 여부는 PM/사용자 결정.)

#### 3.1.4 배치/마이그레이션

install 재배포(`scripts/install-mac.sh` 메뉴 [1] 또는 [3]) 시 4종 마커가 각 대상 파일에 갱신 삽입된다. 별도 마이그레이션 스크립트 불필요(멱등 마커 교체 — `scripts/install-mac.sh:270-289`).

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | F-1 AC | 산출물 검사 | `claude-bootstrap.md`의 `` ```markdown `` 코드블록 내부에 `OPAL_BOOTSTRAP` + `off` + `생략` 문구 존재 |
| TS-002 | F-2 AC | 산출물 검사 | `cursor-bootstrap.mdc` frontmatter 이후 본문에 `OPAL_BOOTSTRAP` 게이트 문구 존재 + `---` frontmatter 구조 무손상 |
| TS-003 | F-3 AC | 산출물 검사 | `codex-bootstrap.md` 코드블록 내부에 게이트 문구 존재 |
| TS-004 | F-4 AC | 산출물 검사 | `gemini-bootstrap.md` 코드블록 내부에 게이트 문구 존재 |
| TS-005 | F-1~F-4 AC (추출 무결성) | 기능 테스트 | `extract_bootstrap_content`(또는 동등 sed)로 4종 추출 시 게이트 문구가 추출 결과에 포함되고 코드블록 조기 종료 없음 (H-1) |
| TS-006 | 완료기준 ① (off 세션) | 통합 테스트 | install 재배포 후 `OPAL_BOOTSTRAP=off` 세션에서 Bash 1회 후 부트스트랩 Read 0건 (수동 검증 — 환경 의존) |
| TS-007 | 완료기준 ② (정상 세션) | 회귀 테스트 | 미설정/`on` 세션에서 기존 부트스트랩 정상 동작 (H-2 회귀) |

---

### F-002: `opal/core/AGENT.md` Eager 절차 최상단에 skip 게이트 명문화

#### 3.2.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 5 | `opal/core/AGENT.md` | 문서 | `### Eager 단계` 헤딩(:11)과 기존 step 1(:13) 사이에 "step 0 — 스킵 게이트" 추가 (기존 1~7 번호 불변). `[WORKER 규칙]`(:9)과 명시 구분 문구 포함 | `opal/core/AGENT.md:11-13` |

#### 3.2.2 API·데이터 모델·화면 설계

해당 없음 (문서). **삽입 문구 초안** 확정:

`### Eager 단계 (세션 시작 시 즉시 수행)` 헤딩 바로 아래, 기존 `1.`(:13) **앞**에 삽입:

```
0. **[스킵 게이트]** 먼저 Bash 도구로 `echo $OPAL_BOOTSTRAP`를 1회 실행한다. 출력이 정확히 `off`이면 — 이하 step 1~7 전체(정체성·헌법·하네스·PM·PM 컨텍스트 포함 부트스트랩 전부)를 생략하고 OPAL 없이 순수 동작한다(부트스트랩 완료 보고도 생략). 출력이 `off`가 아니거나(미설정/`on`/기타) Bash를 쓸 수 없으면 게이트를 무시하고 step 1부터 정상 진행한다. 이 게이트는 세션/캡틴 전역 토글이며, 위 `[WORKER 규칙]`(디스패치 프롬프트 첫 줄 `[WORKER]`)과는 별개의 독립 스킵 경로다.
```

> 설계 결정 근거:
> - "step 0"으로 step 1 앞에 배치 — TASK F-5 AC "step 1보다 앞에 존재" 충족, 기존 번호 불변으로 회귀 차단(H-5) (→ D-2 §11-13).
> - "`[WORKER 규칙]`과 별개" 명시 — F-5 AC "`[WORKER]` 스킵과 구분" 충족(H-5).
> - 조건·동작이 F-001 마커 문구와 동일 의미 — H-6 동기.
> - 변경이력 섹션(파일 하단, install `strip_deploy_md`가 잘라내는 경계 `scripts/install-mac.sh:223`) 위 본문에 위치 → 배포본 `~/.opal/AGENT.md`에 반영 보장.

#### 3.2.3 환경 변경

해당 없음.

#### 3.2.4 배치/마이그레이션

install 재배포 시 `strip_deploy_md`로 `~/.opal/AGENT.md`에 반영 (`scripts/install-mac.sh:941-942`).

#### 3.2.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-008 | F-5 AC | 산출물 검사 | `opal/core/AGENT.md` §Eager 단계에 `OPAL_BOOTSTRAP` 게이트가 step 1보다 앞(step 0)에 존재 |
| TS-009 | F-5 AC (구분) | 산출물 검사 | 게이트 문구에 `[WORKER]` 스킵과의 구분 표현이 포함됨 |
| TS-010 | F-5 + F-1 (동기) | 산출물 검사 | AGENT.md 게이트와 마커 게이트의 조건(`off`)·동작(전부 스킵)이 일치 (H-6) |

---

### F-003: Windows 미러 정합성 검증 (`scripts/install/windows.ps1`)

#### 3.3.1 파일 변경 계획

**수정**: 없음 (정정 결과 — windows.ps1은 동일 bootstrapper 소비).

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| — | `scripts/install/windows.ps1` | 배치 | **코드 변경 없음.** F-001 수정이 자동 반영됨을 검증만 수행 | `scripts/install/windows.ps1:794-846` |

#### 3.3.2 API·데이터 모델·화면 설계

`Register-Bootstrapper`(`scripts/install/windows.ps1:792-847`)는 4종 모두 `opal/bootstrapper/`의 동일 `.md`를 `Get-BootstrapContent`/직접 복사로 소비한다. F-001이 소스 `.md`를 수정하면 windows 어댑터가 자동으로 동일 게이트를 배포한다 → **별도 미러 수정 불필요**. TASK F-6 AC("windows.ps1 어댑터 함수에 skip 게이트 문구 존재")는 정정에 따라 "windows.ps1이 게이트 포함 마커를 배포함"으로 충족.

> 만약 검증 중 windows.ps1에 **인라인 마커 문구가 잔존**(H-7)하면 그때 한정 수정. 현재 코드 확인 결과 인라인 문구 없음(`Get-BootstrapContent` 동일 소스 참조) → 수정 불요.

#### 3.3.3 환경 변경

해당 없음.

#### 3.3.4 배치/마이그레이션

해당 없음.

#### 3.3.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-011 | F-6 AC (정정) | 산출물 검사 | `scripts/install/windows.ps1`에 인라인 마커 문구가 없고, `Register-Bootstrapper`가 `opal/bootstrapper/` 4종 `.md`를 소비함을 확인 (H-7) |
| TS-012 | F-6 AC (정정) | 기능 테스트 | windows `Get-BootstrapContent`(또는 동등 추출)로 게이트 문구가 추출 결과에 포함됨 (수동/정적 검증) |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001 | 1 | opal-task-agent | 순차(단일 Step 내 4파일) | bootstrapper 4종 마커 수정 |
| 1 | F-002 | 2 | PM 직접 / opal-task-agent | 병렬 가능 (F-001과 독립 파일) | AGENT.md Eager 게이트 |
| 2 | F-003 | 3 | opal-task-agent | 순차 (F-001 후) | windows 미러 검증 |

### 4.2 실행 체크리스트

> 총 3개 Step | Phase 2개 | 실행 모드: 단순

#### Step 1: bootstrapper 4종 `.md`에 skip 게이트 문구 삽입
- [x] 완료
- **소속 기능**: F-001
- **영역**: 환경
- **agent**: opal-task-agent
- **파일**: `opal/bootstrapper/claude-bootstrap.md`, `opal/bootstrapper/codex-bootstrap.md`, `opal/bootstrapper/gemini-bootstrap.md`, `opal/bootstrapper/cursor-bootstrap.mdc`
- **작업 내용**: claude/codex/gemini 3종 — 코드블록 본문 서두(헤딩 직후, `**[MUST]**` 앞)에 §3.1.2 "코드블록용" 게이트 문단 삽입(코드 펜스 미사용, 인라인 백틱만). cursor — frontmatter `---` 직후 본문 앞에 §3.1.2 "cursor용" 게이트 문단 삽입. 각 파일 변경이력 행 추가(claude/codex/gemini 하단 표; cursor는 표 부재 시 생략).
- **완료 기준**: TS-001~TS-005 통과 — 4종 모두 게이트 문구 존재 + 코드블록 추출 무결(조기 종료 없음) + cursor frontmatter 구조 무손상
- **테스트**: TS-001, TS-002, TS-003, TS-004, TS-005
- **실행 방법**: direct
- **의존**: 없음

#### Step 2: `opal/core/AGENT.md` Eager 절차에 step 0 스킵 게이트 추가
- [ ] 완료
- **소속 기능**: F-002
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `opal/core/AGENT.md`
- **작업 내용**: `### Eager 단계` 헤딩(:11)과 기존 step 1(:13) 사이에 §3.2.2 "step 0" 게이트 문단 삽입. 기존 step 1~7 번호 불변. `[WORKER 규칙]`과 구분 명시. 파일 하단 변경이력 표에 행 추가(변경이력 섹션은 배포 시 strip — 본문에만 게이트 위치).
- **완료 기준**: TS-008~TS-010 통과 — 게이트가 step 1 앞 + `[WORKER]` 구분 + 마커 문구와 의미 동기
- **테스트**: TS-008, TS-009, TS-010
- **실행 방법**: direct
- **의존**: 없음 (F-001과 병렬 가능)

#### Step 3: Windows 미러 정합성 검증
- [ ] 완료
- **소속 기능**: F-003
- **영역**: 배치
- **agent**: opal-task-agent
- **파일**: `scripts/install/windows.ps1` (읽기 검증 — 수정 없음 원칙)
- **작업 내용**: `Register-Bootstrapper`(:792-847)가 `opal/bootstrapper/` 4종 `.md`를 소비함을 확인. 인라인 마커 문구 잔존 여부 grep. 잔존 시(H-7)에만 한정 수정.
- **완료 기준**: TS-011~TS-012 통과 — windows.ps1 인라인 마커 문구 부재 + 동일 소스 참조 확인
- **테스트**: TS-011, TS-012
- **실행 방법**: direct
- **의존**: Step 1

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 ∥ Step 2 | 독립 파일(bootstrapper `.md` vs AGENT.md), 독립 기능 |
| Step 1 → Step 3 | Step 3은 Step 1 수정이 windows에 자동 반영되는지 검증 — Step 1 완료 후 의미 있음 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | claude 마커 게이트 삽입 + 추출 무결 | TS-001, TS-005 | 코드블록 내 게이트 존재, 추출 조기 종료 없음 |
| F-001 | cursor `.mdc` 게이트 삽입 + frontmatter 무손상 | TS-002 | 본문 게이트 존재, `---` 구조 유지 |
| F-001 | codex 마커 게이트 삽입 | TS-003 | 코드블록 내 게이트 존재 |
| F-001 | gemini 마커 게이트 삽입 | TS-004 | 코드블록 내 게이트 존재 |
| F-001 | off 세션 스킵 동작 (통합) | TS-006 | 재배포 후 off 세션 부트스트랩 Read 0건 |
| F-001 | 정상 세션 회귀 | TS-007 | 미설정/on 세션 기존 동작 유지 |
| F-002 | AGENT.md step 0 게이트 + [WORKER] 구분 | TS-008, TS-009 | step 1 앞 존재 + 구분 표현 포함 |
| F-002 | 마커-AGENT.md 문구 동기 | TS-010 | 조건/동작 일치 |
| F-003 | windows 미러 정합 | TS-011, TS-012 | 인라인 문구 부재 + 동일 소스 소비 |

### 5.2 회귀 테스트
- [ ] 미설정/`on` 세션에서 기존 7단계 부트스트랩 정상 동작 (TS-007)
- [ ] 기존 `[WORKER]` 스킵 메커니즘 불변 (디스패치 첫 줄 `[WORKER]`)
- [ ] install 멱등 마커 교체(`install_opal_section`) 정상 — 재배포 시 게이트 문구 중복 누적 없음

### 5.3 코드/문서 품질
- [ ] 4종 마커 + AGENT.md 게이트 문구 의미 일치 (H-6)
- [ ] 변경이력 기록 (버전, KST 일시, 변경내용) — claude/codex/gemini `.md` 하단 표 + AGENT.md 변경이력 표
- [ ] 코드 펜스/특수문자로 인한 추출 경계 파손 없음 (H-1)

### 5.4 보안
- [ ] 게이트 문구에 하드코딩된 토큰/시크릿 없음 (해당 없음 — 산문)
- [ ] `OPAL_BOOTSTRAP` 환경변수 외 추가 권한 요구 없음 (Bash echo만 사용)

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 3개 | 단순 |
| 변경 파일 수 | 5개 (bootstrapper 4 + AGENT.md 1; windows.ps1 검증만) | 복잡 경계 — 단, 모두 동종 산문 1줄 삽입 |
| 모듈 범위 | 단일 (bootstrapper 어댑터 계층) | 단순 |
| 작업 유형 | 단순 기능 추가 (산문 삽입) | 단순 |
| 외부 의존성 | 없음 | 단순 |
| **실행 모드** | **단순** | 변경 파일 수만 경계지만, 4개가 동일 문구·동일 패턴 1줄 삽입이며 신규 모듈·외부 의존·로직 변경 없음 → 단순 모드 |

> 변경 파일 5개로 가이드 §5 "4개 이상=복잡" 기준에 닿으나, 4개 bootstrapper는 동일 게이트 문구를 동일 위치 규칙으로 삽입하는 **단일 논리 작업**이고 코드 로직·외부 의존·신규 모듈이 전무하다. 실질 복잡도는 단순이므로 §7 실행 아키텍처는 생략한다.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 부트스트래퍼 마커 | Markdown (코드블록/frontmatter) | - |
| 설치 어댑터 | Bash (`install-mac.sh`), PowerShell (`windows.ps1`) | - |
| 게이트 조건 | 환경변수 `OPAL_BOOTSTRAP` + Bash `echo` | - |

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| - | 해당 없음 (프레임워크 내부 문서·셸 스크립트 — 외부 라이브러리 미사용) |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | PM 프로필 (AGENT.md) | `.opal/AGENT.md` | 배포 경계·플랫폼 분기 금지사항 SSOT (§60, §62) |
| D-2 | 설계 | OPAL AGENT.md (소스) | `opal/core/AGENT.md` | Eager 절차 구조·게이트 삽입 대상 (:5-24) |
| D-3 | 소스 | install-mac.sh | `scripts/install-mac.sh` | 마커 추출(:237-245)·삽입(:247-321)·cursor 복사(:1092)·strip(:220-224) |
| D-4 | 소스 | windows.ps1 (실제 경로) | `scripts/install/windows.ps1` | 미러 추출(:201-224)·삽입(:226-278)·Register-Bootstrapper(:792-847) |
| D-5 | 설계 | 공통 하네스 | `opal/core/references/opal-harness.md` | Guards·플랫폼 독립성 원칙 |
| D-6 | 소스 | bootstrapper 4종 | `opal/bootstrapper/{claude,codex,gemini}-bootstrap.md`, `cursor-bootstrap.mdc` | 마커 텍스트 SSOT (실제 수정 대상) |

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | 게이트 문구 백틱/펜스로 코드블록 추출 조기 종료 (H-1) | F-001 | P0 | 코드 펜스 금지, 인라인 백틱만; TS-005 추출 무결 검증 |
| R-2 | LLM이 `off` 조건을 과확대 해석 → 정상 세션 스킵 (H-2) | F-001/F-002 | P0 | "정확히 `off`" 단일 매칭 + "off 아니면 정상 진행" 명시; TS-007 회귀 |
| R-3 | cursor `.mdc` 구조(frontmatter) 파손 (H-3) | F-001 | P0 | frontmatter `---` 바깥 본문에만 삽입; TS-002 구조 검사 |
| R-4 | Bash 미보유 플랫폼에서 게이트 행 멈춤 (H-4) | F-001/F-002 | P1 | "Bash 불가 시 게이트 무시·정상 진행" fail-safe 폴백 문구 |
| R-5 | AGENT.md step 재번호로 인한 회귀 (H-5) | F-002 | P1 | "step 0"으로 추가, 기존 1~7 불변 |
| R-6 | 마커 게이트 ↔ AGENT.md 게이트 의미 불일치 (H-6) | F-001+F-002 | P1 | 양측 동일 조건·동작 표현; TS-010 교차 검사 |
| R-7 | windows.ps1 인라인 마커 잔존으로 미러 누락 (H-7) | F-003 | P1 | TS-011 인라인 문구 부재 확인, 잔존 시 한정 수정 |
| R-8 | TASK 전제(emit 함수 수정)와 실제 구조 불일치 | 전체 | (해소됨) | §1.2 정정 설계 채택 — bootstrapper SSOT 1지점 수정으로 4종+windows 동시 충족 |

---

## RED-first 트랙 판단

> TASK 추가 분석 지시 #4 응답.

- **대상이 bash/markdown 정적 산출물** — bootstrapper `.md`·`.mdc`·AGENT.md 산문 + 셸 스크립트. 실행 가능한 단위 테스트 대상 함수가 없다.
- **RED-first(실패하는 단위 테스트 선작성) 비해당**: 검증은 (a) L1 산출물 검사(grep으로 게이트 문구·구조 확인), (b) L2 install 재배포 후 배포 파일 내용 확인, (c) L3 설정/미설정 세션 실동작(환경 의존·수동)으로 구성된다.
- **권고 검증 순서**: L1(TS-001~005, 008~012, 정적·결정론적) → L2(TS-006 재배포, 사용자 승인 후) → L3(TS-007 회귀, 수동). TEST-SCENARIO.md(PM STEP 3.5 작성)는 위 리스크 가설 표 H-1~H-7과 TS-001~012를 입력으로 시나리오를 구체화한다.
