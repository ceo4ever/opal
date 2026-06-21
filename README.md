# OPAL — Open Protocol for Agentic Links

> AI 환경에서 복잡한 작업을 체계적으로 수행하는 **오픈소스 AI 에이전트 프레임워크**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) [![Latest Release](https://img.shields.io/github/v/release/ceo4ever/opal)](https://github.com/ceo4ever/opal/releases)

---

## OPAL이란?

AI 도구(Claude Code, Cursor 등)를 쓰다 보면 공통적인 한계에 부딪힌다.

- 매번 같은 컨텍스트를 반복해서 설명해야 한다
- AI가 코드를 바로 생성해버려서 검토할 틈이 없다
- 복잡한 작업은 중간에 방향을 잃는다
- 프로젝트마다 AI를 다시 세팅하는 게 번거롭다

**OPAL은 이 문제를 해결하는 프로토콜이다.**

`//` 커맨드 하나로 다단계 AI 파이프라인이 실행된다. AI는 작업을 단계별로 나누어 계획을 먼저 세우고, 각 단계마다 사용자에게 확인을 받은 후에만 다음 단계로 넘어간다. 모든 과정은 문서로 기록되어 추적 가능하다.

### 핵심 철학

| 원칙 | 설명 |
|------|------|
| **사용자 주권** | AI는 사용자 승인 없이 코드를 생성하거나 파일을 수정하지 않는다 |
| **검증된 완료** | 완료는 생성된 문서가 아니라 검증된 동작을 의미한다 |
| **강제 우선** | 항상 지켜야 하는 규칙은 조언이 아니라 도구로 강제한다 |
| **단계적 실행** | 작업을 TASK → PLAN → EXECUTE 단계로 분해하여 각 단계를 검증한다 |
| **문서화 우선** | 모든 작업은 문서(TASK.md, PLAN.md 등)로 추적되고 재현 가능하다 |
| **플랫폼 독립** | Claude Code, Cursor 등 어떤 AI 환경에서도 동일하게 동작한다 |
| **프로젝트 학습** | 프로젝트 컨텍스트를 축적하여 세션이 바뀌어도 일관된 품질을 유지한다 |

> 이 철학의 행동 SSOT는 **OPAL 헌법(`PRINCIPLES.md`)**이다. 모든 하네스·스킬·에이전트의 행동은 헌법을 상속한다.

### 주요 특징

- **Pilot 기반 파이프라인** — 개발, 기획, 문서 등 목적에 맞는 파이프라인을 선택해 실행
- **PM 역할 분리** — 에이전트가 프로젝트 매니저로서 워커(서브에이전트)를 지휘
- **QA 내장** — 테스트 시나리오 작성 → 구현 → 자동 검증이 파이프라인 안에 포함
- **3-way 실행 모드** — `interactive` / `semi-agentic`(기본) / `agentic` — 사용자 검토와 PM 자율의 균형을 작업별로 선택
- **전문 에이전트(Specialist Agent)** — 도메인별 전문 워커가 FE/BE/DB/기획/테스트를 담당
- **프로젝트 브레인(`//opbr`)** — 프로젝트 WHY·HOW 지식을 마크다운 위키로 누적·질의
- **경량 품질 게이트(`//opgc`)** — 커밋 전 보안·컨벤션 진단 (OWASP/CWE/SANS 기반)
- **커뮤니티 스킬** — [skills.sh](https://skills.sh/) 카탈로그를 통해 외부 조직 스킬을 온디맨드로 검색·설치 (`//skill-manager`)

---

## 목차

1. [설치](#설치)
2. [프로젝트 설정](#프로젝트-설정)
3. [빠른 시작](#빠른-시작)
4. [핵심 개념 — Pilot과 `//` 커맨드](#핵심-개념--pilot과--커맨드)
5. [Pilot 비교 & 사용 사례](#pilot-비교--사용-사례)
6. [Pilot 사용법](#pilot-사용법)
   - [opds — 개발 Short Task](#opds--개발-short-task-기본)
   - [opd — 개발 Full Task](#opd--개발-full-task)
   - [opdw — Wireframe UI](#opdw--wireframe-ui)
   - [opp — 범용 프로젝트 작업](#opp--범용-프로젝트-작업)
   - [opsdd — SDD 명세 기반 개발](#opsdd--sdd-명세-기반-개발)
   - [opwt — 서비스 기획 산출물](#opwt--서비스-기획-산출물)
   - [oppd — 프로젝트 개발 라이프사이클](#oppd--프로젝트-개발-라이프사이클)
   - [opgc — 품질 게이트 (GC)](#opgc--품질-게이트-gc)
   - [opbr — 프로젝트 브레인](#opbr--프로젝트-브레인)
7. [독립 스킬 사용법](#독립-스킬-사용법)
8. [Pilot 실행 모드 (3-way)](#pilot-실행-모드-3-way)
9. [전문 에이전트 (Specialist Agent)](#전문-에이전트-specialist-agent)
10. [아키텍처 개요](#아키텍처-개요)
11. [트러블슈팅](#트러블슈팅)

---

## 설치

### Step 1: 사전 요구사항 확인

| 항목 | 요구사항 |
|------|---------|
| **OS** | macOS / Linux / Windows |
| **필수 도구** | bash(또는 PowerShell), git, Node.js v18+, Python 3 |
| **지원 AI 플랫폼** | Claude Code, Cursor, Gemini (Antigravity), Codex |

> Node.js는 skill-registry, state-tool 등 CLI 도구 실행에 필요하다. Python은 MCP 서버 venv 구성에 필요하다.
> Windows에서 Python이 설치되어 있지 않으면 install이 winget을 통해 Python 3.14를 자동으로 설치한다.

### Step 2: One-liner 설치

**macOS / Linux**

```bash
curl -fsSL https://raw.githubusercontent.com/ceo4ever/opal/main/scripts/install.sh | bash
```

**Windows (PowerShell)**

```powershell
iex (irm https://raw.githubusercontent.com/ceo4ever/opal/main/scripts/install.ps1)
```

`Restricted` 정책 환경에서는:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/ceo4ever/opal/main/scripts/install.ps1 | iex"
```

> 특정 버전 고정: `OPAL_VERSION=<원하는-태그>` 환경변수 사용 (mac/linux) 또는 `$env:OPAL_VERSION = '<원하는-태그>'` (Windows). 최신 태그는 [GitHub Releases](https://github.com/ceo4ever/opal/releases)에서 확인할 수 있다.

### Step 3: 부트스트랩 체크리스트 확인

AI 도구(Claude Code / Cursor / Gemini / Codex)를 재시작하면 첫 응답에 다음과 같이 표시된다.

```
[부트스트랩] ✅ principles ✅ identity ✅ harness ✅ PM ✅ PM모드 ⏳ registry ⏳ references ⏳ model-mapping
[안내] 프로젝트 작업이라면 //opi 또는 //opp/opd/opds 로 진입하세요
```

이 메시지가 나타나면 설치가 정상 완료된 것이다. (`identity.md`가 없으면 자동으로 에이전트 온보딩이 시작된다.)

### Step 4: 다음 단계

| 명령 | 용도 |
|------|------|
| `//opi` | 프로젝트 환경 초기화 (`.opal/AGENT.md`, `docs/PROJECT.md` 등 생성) |
| `//next` | 재진입 가이드 — 현재 상태 진단 + 다음 액션 권유 |
| `opal-cli doctor` | 의존성·경로·MCP·부트스트래퍼 정합성 진단 |
| `opal-cli update` | 최신 release 동기화 (사용자 데이터 보존) |
| `opal-cli uninstall` | `~/.opal/` 제거 + 부트스트래퍼 마커 회수 |

> `opal-cli` 명령은 PATH에 자동 등록된다. 셸 재시작 후 `opal-cli --help`로 전체 서브커맨드를 확인할 수 있다.

---

## 프로젝트 설정

OPAL을 사용하려는 **각 프로젝트**에 아래 설정이 필요하다.

### 자동 설정 (권장)

AI 채팅창에서 아래 커맨드를 입력하면 프로젝트 설정을 자동으로 생성한다.

```
//opi
```

> `opi`(opal-project-init)가 프로젝트를 분석하고 `.opal/AGENT.md`, `docs/PROJECT.md`, `docs/CONVENTIONS.md` 등을 생성한다.

#### `//opi` 생성물 상세

| 파일 | 역할 |
|------|------|
| `.opal/AGENT.md` | PM 프로필 — 프로젝트별 검토 기준, 금지사항, 확정 기준 |
| `docs/PROJECT.md` | 프로젝트 정의 SSOT — 개요, 원칙, 문서 레지스트리 |
| `docs/CONVENTIONS.md` | 코드/문서 컨벤션 — 네이밍, 파일 구조, 커밋 규칙 |

### 수동 설정 — Claude Code

프로젝트 루트 `CLAUDE.md`에 다음 섹션을 포함한다.

```markdown
## Project Overview
{프로젝트 한 줄 설명}

## Tech Stack
{사용 기술: Next.js 14, FastAPI, PostgreSQL 등}

## Architecture
{주요 아키텍처 설명}

## Code Conventions
{코드 스타일, 네이밍 규칙 등}
```

### 수동 설정 — Cursor

`~/.cursor/rules/000-opal-agent.mdc`가 전역 자동 적용(`alwaysApply: true`)되므로, 프로젝트당 추가 설정은 필요 없다. OPAL 설치 시 자동으로 배치된다.

### 수동 설정 — Gemini

프로젝트 루트 `GEMINI.md`에 OPAL 부트스트래퍼를 삽입한다. Claude Code의 `CLAUDE.md`와 동일한 형식이다.

---

## 빠른 시작

설치와 프로젝트 설정(`//opi`)이 끝났다면, 간단한 작업으로 파이프라인을 체험해 보자.

```
//opp README에 프로젝트 설명 추가해줘
```

AI가 `TASK.md`를 작성하고 승인을 요청한다. "진행해"라고 답하면 `PLAN.md` 작성 → 실행까지 단계별로 진행된다. 각 단계가 끝날 때마다 결과를 보고하고 다음 단계 진행 여부를 확인한다.

코드 변경이 수반되는 작업이라면 `//opds`를 사용한다:

```
//opds 로그인 버튼 클릭 시 스피너가 표시되지 않는 버그 수정
```

---

## 핵심 개념 — Pilot과 `//` 커맨드

### Pilot이란?

OPAL에서 **Pilot**은 작업을 조종하는 오케스트레이터다.

비행기의 파일럿이 목적지까지 항로를 설정하고 각 단계를 통제하듯, OPAL의 Pilot은 복잡한 작업을 단계별 파이프라인으로 분해하고 AI 워커(서브에이전트)를 지휘한다. 단순히 코드를 생성하는 것이 아니라, **무엇을**, **어떻게**, **어떤 순서로** 할지를 먼저 정의하고 실행한다.

```
Pilot (오케스트레이터)
  ├─ TASK 단계: 작업 정의 + 범위 확정
  ├─ PLAN 단계: 구현 계획 수립
  ├─ EXECUTE 단계: 워커 디스패치 → 코드 구현
  └─ QA 단계: 검증 + 완료 확인
```

각 Pilot은 목적에 따라 다른 파이프라인을 가진다. 개발 작업엔 `opds`/`opd`, 기획엔 `opwt`, 복잡한 명세가 필요하면 `opsdd`를 사용한다.

### `//` 커맨드

AI 채팅창에서 `//`로 시작하는 입력은 **OPAL Pilot 호출**로 처리된다.

```
//{Pilot 약어} {작업 설명}
```

예시:
```
//opds 로그인 버튼 클릭 시 스피너가 표시되지 않는 버그 수정
//opwt PRD 초안 작성해줘
//opp 오래된 패키지 의존성 업그레이드
```

### 실행 흐름

Pilot은 작업을 여러 단계로 나누어 실행한다. 각 단계가 끝날 때마다 AI가 결과를 보고하고 다음 단계 진행 여부를 확인한다.

```
사용자: //opds {작업}
  → AI: TASK.md 작성 후 보고 (다음 단계 승인 요청)
  → 사용자: 승인 ("응", "진행해", "go" 등)
  → AI: PLAN.md 작성 후 보고 (구현 계획 검토 요청)
  → 사용자: 승인
  → AI: 코드 구현 → 완료 보고
```

**핵심 규칙**: 사용자가 명시적으로 승인하기 전까지 코드를 생성하거나 파일을 수정하지 않는다.

### 비서 모드와 PM 모드

OPAL 에이전트는 **비서**와 **PM** 두 가지 역할을 수행한다.

| 역할 | 활성 조건 | 동작 |
|------|----------|------|
| **비서** | 프로젝트 밖 (`.opal/AGENT.md` 없음) | 일상 대화, 일반 업무 지원 |
| **PM** | 프로젝트 내 (`.opal/AGENT.md` 존재) | 태스크 관리, 워커 디스패치, Gate 검토 |

프로젝트에 `.opal/AGENT.md`가 있으면 PM 모드로 자동 전환된다. PM 모드에서는 `//` 커맨드로 파이프라인을 실행할 때 워커(서브에이전트)를 지휘하고 각 단계의 품질을 검토한다. `.opal/AGENT.md`가 없는 환경에서는 비서 모드로 동작하여 일반적인 대화와 업무를 지원한다.

### L2 경량 트랙

"그냥 해" 또는 "직접 수행" 발화는 **L2 경량 트랙**의 진입 신호다. L2는 태스크 파이프라인(TASK→PLAN→EXECUTE)을 우회하고 PM이 직접 수정한다.

> L2는 3-way 모드(interactive/semi-agentic/agentic)와는 **별개 축**이다. 3-way 모드는 파이프라인 내 게이트 수준을 다루며, L2는 파이프라인 자체를 우회한다.

**L2 적격 기준**:

| 구분 | 기준 |
|------|------|
| **L2 적격** | 파일 1~2개 + 단순 수정 + 동작검증(TEST) 불요 (문서·문구·오타·주석·설정값 등) |
| **L2 부적격 → 풀 파이프라인** | 코드 로직 변경(동작검증 필요) / 파일 3개 이상 / 구조·스키마·인터페이스 변경 / 다중 영역 |

> **핵심 가드**: L2 적격 = 파일 1~2개 + 단순 수정 + **동작검증(TEST) 불요**. 동작검증(TEST/TEST-SCENARIO/verify)이 필요한 작업은 L2 우회 금지 — 반드시 풀 파이프라인으로 처리한다.

---

## Pilot 비교 & 사용 사례

### Pilot 한눈에 비교

| Pilot | 이름 | 적합한 작업 규모 | 파이프라인 | 주요 산출물 |
|-------|------|----------------|-----------|------------|
| `//opds` | Short Task Dev | 소~중 (단일 기능 단위) | TASK → PLAN(+테스트 시나리오) → EXECUTE → TEST | TASK, PLAN, DONE |
| `//opd` | Full Task Dev | 중~대 (멀티 모듈) | TASK → ANALYSIS → PLAN(+테스트 시나리오) → EXECUTE → TEST | + ANALYSIS |
| `//opdw` | Wireframe UI | 소~중 (화면 단위) | TASK → WIREFRAME → EXECUTE | wireframe.md, UI 컴포넌트 |
| `//opp` | 범용 Project | 제한 없음 | TASK → PLAN → EXECUTE | TASK, PLAN, DONE |
| `//opsdd` | SDD 개발 | 중~대 (명세 복잡) | TASK → SPEC → REVIEW → DESIGN → EXECUTE-LOOP → VERIFY → CLOSE | SPEC, TEST-SCENARIOS, SPEC-PLAN, STATE |
| `//opwt` | 기획 산출물 | 제한 없음 | TASK → (ANALYSIS →) PLAN → EXECUTE → QA | PRD, TRD, IA, 정책서, WBS |
| `//oppd` | 프로젝트 Dev | 대 (전체 라이프사이클) | PLAN(기획) → WBS → EXECUTE(코드) | 기획 산출물 전체 + 코드 |
| `//opgc` | 품질 게이트 (GC) | 커밋 전 진단 | SCAN → CHECK → REPORT → CLOSE | GC-SECURITY/CONVENTION 보고서, DONE |

### 선택 가이드

```
코드를 수정/추가하는 작업인가?
  ├─ YES: 얼마나 복잡한가?
  │    ├─ 단순 (버그 수정, 소기능): //opds
  │    ├─ 복잡 (멀티 모듈, 아키텍처): //opd
  │    ├─ 화면 신규 설계부터: //opdw
  │    └─ 명세를 먼저 엄밀하게 정의하고 싶다: //opsdd
  └─ NO: 어떤 작업인가?
       ├─ 문서, 설정, 환경, 스크립트: //opp
       ├─ 기획 문서 (PRD, TRD, IA 등): //opwt
       ├─ 아이디어 → 기획 → 코드 전체: //oppd
       ├─ 커밋 전 보안·컨벤션 진단: //opgc
       └─ 프로젝트 지식 축적·질의: //opbr
```

---

### `//opds` 사용 사례

버그 수정, 기능 추가, 리팩토링 등 **코드 변경이 수반되는 작업의 기본 진입점**.

```
//opds 결제 완료 후 이메일 발송이 간헐적으로 실패하는 버그 수정
```
> 결제 서비스와 이메일 발송 로직의 의존 관계를 분석하고, 재시도 로직 및 에러 핸들링을 보강한다.

```
//opds 사용자 프로필 페이지에 SNS 링크 입력 필드 추가
```
> 기존 프로필 폼에 URL 유효성 검사 포함한 SNS 링크 필드를 추가하고 저장 로직을 연결한다.

```
//opds UserService의 findById 메서드를 캐시 레이어 적용해서 최적화
```
> Redis 캐시를 도입하여 반복 조회를 최소화하고, 캐시 무효화 전략을 함께 설계한다.

---

### `//opd` 사용 사례

코드베이스를 먼저 깊이 분석(ANALYSIS)한 뒤 계획을 수립하는 **대규모 개발 작업**.

```
//opd OAuth 소셜 로그인 (Google, Kakao) 기능 전체 구현
```
> 기존 인증 시스템 분석 후 OAuth 플로우를 설계하고, 토큰 관리·세션 연동까지 구현한다.

```
//opd 모놀리식 UserService를 도메인 레이어로 분리 리팩토링
```
> 의존 관계와 영향 범위를 먼저 분석하고, 단계적 분리 계획을 수립하여 회귀 없이 리팩토링한다.

```
//opd 실시간 알림 시스템 — WebSocket 기반 서버 푸시 구현
```
> 현재 아키텍처와의 호환성을 분석하고, 연결 관리·이벤트 발행·클라이언트 수신 전체를 설계·구현한다.

---

### `//opdw` 사용 사례

정책서·스케치·구두 요건을 입력으로 받아 **와이어프레임 설계 → UI 구현**까지 한 번에.

```
//opdw 첨부한 정책서 기반으로 마이페이지 화면 설계하고 구현해줘
```
> 정책서의 기능 요건을 분석하여 컴포넌트 구조와 상태 흐름을 먼저 설계한 뒤 React UI를 구현한다.

```
//opdw 스케치 이미지 참고해서 대시보드 화면 만들어줘
```
> 스케치 이미지를 분석하여 레이아웃과 인터랙션 구조를 추출하고, shadcn/ui 컴포넌트로 구현한다.

```
//opdw 새 상품 등록 화면 — 입력 폼 + 이미지 업로드 + 미리보기
```
> 요건 인터뷰로 UX 흐름을 정리하고, 드래그앤드롭 업로드와 실시간 미리보기 포함한 화면을 구현한다.

---

### `//opp` 사용 사례

코드 개발이 아닌 **모든 프로젝트 작업** — 문서, 설정, 환경, 스크립트, 인프라.

```
//opp README 전면 개편 — 오픈소스 공개 수준의 소개 문서로 작성
```
> 프레임워크 철학, 사용 사례, 아키텍처 개요를 포함한 신규 사용자 대상 문서를 작성한다.

```
//opp 패키지 의존성 취약점 점검 및 업그레이드
```
> npm audit / pip check 실행 후 취약 패키지를 파악하고, 호환성을 검토하며 단계적으로 업그레이드한다.

```
//opp GitHub Actions CI 파이프라인 구성 — lint, test, build
```
> PR 트리거 기반의 CI 워크플로우를 설계하고, 각 단계의 실패 처리와 알림 설정까지 구성한다.

---

### `//opsdd` 사용 사례

"무엇을 만들지"를 먼저 엄밀하게 정의하는 **명세(SPEC) 주도 개발** — 복잡한 도메인, 멀티팀 협업, 요건이 불명확한 작업에 적합.

```
//opsdd 구독 플랜 관리 기능 — 플랜 생성/변경/해지, 결제 연동
```
> FR/NFR/제약조건을 SPEC으로 정의하고, 테스트 시나리오를 먼저 확정한 뒤 ACT 단위로 구현한다.

```
//opsdd 멀티 테넌트 권한 시스템 — 조직/역할/리소스 3계층 모델
```
> 복잡한 권한 모델을 SPEC에서 형식화하고, 경계 케이스를 테스트 시나리오로 선제 정의한 뒤 구현한다.

```
//opsdd 실시간 재고 관리 — 입출고 이벤트 기반, 동시성 보장
```
> 동시성 요건과 정합성 기준을 NFR로 명시하고, 이벤트 소싱 설계 후 정합성 테스트를 포함하여 구현한다.

---

### `//opwt` 사용 사례

PRD, TRD, 서비스 정책서, IA 등 **기획 문서를 작성하거나 최신화**할 때.

```
//opwt PRD 초안 작성 — 커머스 플랫폼 셀러 관리 기능
```
> 목표, 사용자 스토리, 기능 요건, 비기능 요건을 구조화하여 PRD를 작성하고 QA 에이전트로 완결성을 검증한다.

```
//opwt 서비스 정책서 수정 — 최근 변경된 환불 정책 반영
```
> 기존 정책서를 분석하여 변경 영향 범위를 파악하고, 관련 섹션을 일관성 있게 업데이트한다.

```
//opwt IA 작성 — 와이어프레임 참고해서 사이트맵과 기능 목록 정리
```
> 와이어프레임을 기반으로 정보 구조를 추출하고, JSON + Mermaid 사이트맵과 MECE 기능 목록을 생성한다.

---

### `//oppd` 사용 사례

아이디어에서 완성까지 **기획 → WBS → 코드 구현을 하나의 파이프라인**으로.

```
//oppd 셀러 온보딩 기능 — 회원가입부터 첫 상품 등록까지 전 과정
```
> PRD → IA → WBS → 개발 태스크 분해까지 전 과정을 한 흐름으로 관리하고, 개발 준비 상태까지 도달한다.

```
//oppd 관리자 대시보드 — 매출 현황, 사용자 통계, 알림 관리
```
> 요건 정의부터 화면 설계, 백엔드 API, 프론트엔드 구현까지 라이프사이클 전체를 Pilot이 조율한다.

```
//oppd 신규 서비스 MVP 구축 — 핵심 기능 3가지 정의부터 배포까지
```
> 아이디어를 PRD로 구체화하고, WBS로 개발 항목을 분해한 뒤 코드 구현까지 단일 파이프라인으로 실행한다.

---

## Pilot 사용법

### opds — 개발 Short Task (기본)

**언제 쓰나**: 코드 변경이 수반되는 모든 개발 작업의 기본 진입점. 버그 수정, 기능 추가, 리팩토링 등.

**파이프라인**: `TASK → PLAN(+테스트 시나리오) → EXECUTE → TEST`

**산출물**: `TASK.md`, `PLAN.md`(테스트 시나리오 포함), `DONE.md`

#### 진행 흐름

```
1. AI → TASK.md 작성 (작업 정의, 요구사항, 범위)
        "TASK 완료했습니다. PLAN 단계로 넘어갈까요?"

2. 승인 → AI → PLAN.md 작성 (구현 계획 + 테스트 시나리오)
            "PLAN 검토해주세요. 승인하시면 구현 시작합니다."

3. 승인 → AI → 코드 구현 (EXECUTE)
            → 테스트 실행 (TEST) — 실패 시 자동 수정 후 재테스트 (최대 3회)
            → DONE.md 생성 + 완료 보고
```

#### RED-first 트랙

코드 변경이 수반되는 작업에서 OPAL은 **RED→GREEN TDD** 순서를 적용한다.

- **RED 단계**: 실패 테스트 코드를 작성·실행하여 실패(exit code≠0)를 증거로 기록. RED 증거 없이 구현(GREEN) 진입 금지.
- **GREEN 단계**: 테스트를 통과하는 구현 진행.
- **작성자≠구현자**: RED 테스트 코드 작성은 `opal-test-agent(mode: red)`, 구현은 `op-dev-execute`가 분리 담당.

**하이브리드 자동분기** — PM이 변경 영역으로 판단:

| 영역 | 트랙 |
|------|------|
| 비즈니스 로직, DB, API 계약, 인증, 버그 수정 | RED-first 강제 |
| UI 화면, 탐색, 행위 불변 리팩터, 문서·설정 | 구현 후 검증 허용 |

> 모호하면 RED-first가 기본(안전측). 어느 트랙이든 테스트 코드 산출물·TEST 단계 검증은 유지한다.

#### Full Task 에스컬레이션

PLAN 분석 결과 작업 규모가 크면 AI가 자동으로 제안한다.

```
[에스컬레이션 제안]
이 작업은 Short Task 범위를 초과합니다: 예상 변경 파일 12개
Full Task(opd)로 전환할까요?
- "Full로 해줘" → 전환
- "Short로 진행해" → 유지
```

---

### opd — 개발 Full Task

**언제 쓰나**: 대규모 기능 개발, 여러 모듈에 걸친 변경, 아키텍처 수준의 작업.

**파이프라인**: `TASK → ANALYSIS → PLAN(+테스트 시나리오) → EXECUTE → TEST`

**산출물**: `TASK.md`, `ANALYSIS.md`, `PLAN.md`(테스트 시나리오 포함), `DONE.md`

> `opds`와 차이: ANALYSIS 단계가 추가되어 코드베이스를 먼저 깊이 분석한 후 계획을 수립한다.

#### 진행 흐름

```
1. AI → TASK.md 작성
        "TASK 완료. ANALYSIS 단계로 넘어갈까요?"

2. 승인 → AI → 코드베이스 분석 → ANALYSIS.md 작성 (의존 관계, 영향 범위, 기술 리스크)
            "분석 완료. PLAN 단계로 넘어갈까요?"

3. 승인 → AI → PLAN.md 작성 (구현 계획 + 테스트 시나리오)
            "PLAN 검토해주세요. 승인하시면 구현 시작합니다."

4. 승인 → AI → 코드 구현 (EXECUTE)
            → 테스트 실행 (TEST) — 실패 시 자동 수정 후 재테스트 (최대 3회)
            → DONE.md 생성 + 완료 보고
```

---

### opdw — Wireframe UI

**언제 쓰나**: 새 화면을 기획 단계부터 설계하고 싶을 때. 정책서·요구사항·스케치를 입력하면 와이어프레임을 거쳐 React UI까지 구현한다.

**파이프라인**: `TASK → WIREFRAME → EXECUTE`

**입력물에 따른 자동 분기**:

| 입력물 | 처리 |
|--------|------|
| `wireframe.md` 이미 있음 | WIREFRAME 단계 스킵 → 바로 UI 구현 |
| 정책서 / 요구사항 문서 | 문서 기반 와이어프레임 생성 |
| 스케치 이미지 (.png/.jpg) | 이미지 분석 후 와이어프레임 생성 |
| 구두 설명만 | 인터뷰로 요건 수집 → 와이어프레임 생성 |

> 기존 프로젝트에서 화면을 수정하거나 추가하는 작업은 `opds` 또는 `opd`를 사용한다.

---

### opp — 범용 프로젝트 작업

**언제 쓰나**: 코드 개발이 아닌 모든 프로젝트 작업. 문서 작성, 설정 변경, 의존성 업그레이드, 환경 설정, 스크립트 작성 등.

**파이프라인**: `TASK → PLAN → EXECUTE`

**산출물**: `TASK.md`, `PLAN.md`, `DONE.md`

---

### opsdd — SDD 명세 기반 개발

**언제 쓰나**: "무엇을 만들지"를 먼저 엄밀하게 정의한 뒤 개발하고 싶을 때. 기능 명세(SPEC)를 SSOT로 삼아 테스트 시나리오 → 설계 → 구현까지 파이프라인을 관리한다.

**파이프라인**: `TASK → SPEC → REVIEW → DESIGN → EXECUTE-LOOP → VERIFY → CLOSE`

**산출물**:

```
tasks/{NNN}-{기능명}/
├── TASK.md              메타데이터
├── SPEC.md              기능 명세 (FR/NFR/제약조건) — SSOT
├── TEST-SCENARIOS.md    테스트 시나리오
├── SPEC-PLAN.md         아키텍처 설계 + ACT 분해
├── STATE.md             전체 진행 상태
├── DONE.md              최종 완료 확인
└── actions/
    ├── ACT-001-{name}/  각 구현 단위 산출물
    └── ACT-002-{name}/
```

#### SPEC 단계에서 정의하는 내용

- **Goals**: 이 기능이 달성해야 할 목표
- **Non-goals**: 이번 범위에서 제외하는 것
- **Functional Requirements (FR)**: 기능 요구사항 + Acceptance Criteria
- **Non-Functional Requirements (NFR)**: 성능, 보안, 가용성 기준
- **제약조건**: 기술 스택, 외부 의존성, 규제 요건

#### `opds`와 선택 기준

| 상황 | 추천 |
|------|------|
| 버그 수정, 간단한 기능 추가 | `opds` |
| 명세가 복잡하거나, 여러 팀원과 공유해야 할 때 | `opsdd` |
| "뭘 만들지"가 불명확해서 먼저 정리가 필요할 때 | `opsdd` |

---

### opwt — 서비스 기획 산출물

**언제 쓰나**: PRD, TRD, 서비스 정책서, IA(정보구조) 등 기획 문서를 작성하거나 최신화할 때.

**3가지 모드**:

| 모드 | 언제 | 단계 |
|------|------|------|
| 작성 | 문서가 없는 상태에서 새로 작성 | TASK → PLAN → EXECUTE → QA |
| 수정 | 기존 문서를 분석하고 보완 | TASK → ANALYSIS → PLAN → EXECUTE → QA |
| 분석 | 기존 문서 진단 보고서만 필요 | TASK → ANALYSIS → PLAN(진단) → QA |

**커버 범위**:

| 유형 | 산출물 |
|------|--------|
| 필수 | PRD, TRD, 서비스 정책서, IA(JSON + Mermaid 사이트맵) |
| 선택 | 기능도, 순서도, 운영 정책서, 서비스 매뉴얼 |
| PMO | 개발 WBS (IA/기능목록 기반 MECE 분해) |

---

### oppd — 프로젝트 개발 라이프사이클

**언제 쓰나**: 아이디어에서 완성까지 전체 개발 사이클을 한 번에 관리하고 싶을 때. 기획(opwt) → WBS → 코드 구현을 하나의 파이프라인으로 연결한다.

**파이프라인**: `PLAN(기획 산출물) → WBS → EXECUTE(코드 구현)`

> `docs/PROJECT.md`가 없으면 프로젝트 초기화(`opi`)를 자동 실행한 후 진행한다.

---

### opgc — 품질 게이트 (GC)

**언제 쓰나**: 커밋 전 보안·컨벤션 진단이 필요할 때. 진단 전담(코드 수정 없음) — 이슈가 발견되면 CLOSE 단계에서 `//opds` 체인으로 수정을 안내한다.

**파이프라인**: `SCAN → CHECK → REPORT → CLOSE`

**호출 예**:

```
//opgc                         # 전체 진단 (staged 파일, 보안+컨벤션)
//opgc --security              # 보안만
//opgc --convention            # 컨벤션만
//opgc --scope all             # 전체 범위 + 보안+컨벤션
```

**산출물**: `GC-SECURITY-{타임스탬프}.md`, `GC-CONVENTION-{타임스탬프}.md`, `DONE.md`

---

### opbr — 프로젝트 브레인

**언제 쓰나**: 프로젝트의 WHY·HOW 지식을 마크다운 위키로 누적하고 질의할 때. code-scan(WHAT)·MEMORY(운영 기억)와 역할이 분리된다.

**4가지 모드**:

| 모드 | 명령 | 설명 |
|------|------|------|
| `init` | `//opbr init` | 브레인 위키 초기화 (프로젝트당 1회) |
| `ingest` | `//opbr ingest --all` | 지식 누적 — 문서·코드를 위키로 흡수 |
| `query` | `//opbr ask "질문"` | 위키 기반 질의 |
| `lint` | `//opbr lint` | 위키 무결성 정비 |

**저장 위치**: `.opal/brain/` (프로젝트 자산)

---

## 독립 스킬 사용법

파이프라인 없이 단독으로 실행하는 특화 스킬이다.

### api-analyzer — 외부 API 분석

외부 API를 7단계로 분석하여 명세서를 생성한다.

```
//api-analyzer https://api.example.com/docs
```

```
//api-analyzer 카카오 로그인 API — 인증 플로우 분석하고 명세서 만들어줘
```

**산출물**: 엔드포인트 목록, 요청/응답 스키마, 에러 코드, 연동 주의사항

---

### wireframe-builder — 와이어프레임 생성

정책서 또는 요구사항을 분석하여 `wireframe.md`를 생성한다. `opdw`와 달리 UI 구현 없이 와이어프레임 문서만 만든다.

```
//wireframe-builder 첨부한 서비스 정책서 기반으로 와이어프레임 작성
```

---

### ui-designer — UI 구현

`wireframe.md`를 기반으로 React + shadcn/ui UI를 구현한다.

```
//ui-designer scaffold wireframe.md 참고해서 프로토타입 빠르게 만들어줘
```

```
//ui-designer plan-driven wireframe.md 기반으로 프로덕션 코드 작성
```

| 모드 | 설명 |
|------|------|
| `scaffold` | 빠른 프로토타입 — `bundle.html` 단일 파일 출력 |
| `plan-driven` | 프로덕션 코드 — Next.js 컴포넌트 구조로 출력 |

---

### interview — 요구사항 수집

구조화된 Q&A로 요구사항을 수집하고 정리한다.

```
//interview 신규 기능 요구사항 인터뷰 — 쇼핑몰 포인트 적립 시스템
```

---

### web-to-markdown — 웹 페이지 변환

웹 페이지를 마크다운으로 변환한다.

```
//web-to-markdown https://docs.example.com/api-reference
```

---

### erd-modeler — ERD 설계

요구사항 또는 기존 스키마를 분석하여 ERD를 작성한다.

```
//erd-modeler 첨부한 PRD 기반으로 데이터 모델 설계
```

---

### html-mockup — HTML 화면 목업

CDN 기반 정적 HTML 화면을 빠르게 생성한다. 태스크 컨텍스트를 자동으로 흡수하고 인터뷰를 통해 요건을 수집한다.

```
//mockup 로그인 화면 목업 만들어줘
//html-mockup 주문 내역 페이지 정적 HTML로 빠르게 보여줘
```

---

### system-architecture-html — 시스템 아키텍처 다이어그램

다층 구조, 색상 코드, 빌드 우선순위 배지를 포함한 시스템 아키텍처 다이어그램을 HTML로 생성한다.

```
//html-sa 현재 마이크로서비스 구조 아키텍처 다이어그램으로 그려줘
//system-architecture-html 신규 서비스 배포 구조 시각화
```

---

## Pilot 실행 모드 (3-way)

OPAL Pilot은 **사용자 검토**와 **PM 자율** 사이의 균형을 작업별로 선택할 수 있는 3가지 실행 모드를 제공한다. 모드 플래그를 명시하지 않으면 기본 `semi-agentic`으로 동작한다.

| 모드 | 호출 | 동작 |
|------|------|------|
| `interactive` | `//opp --interactive {작업}` | 모든 단계 게이트마다 사용자 승인 필요 — 가장 보수적 |
| `semi-agentic` (**기본**) | `//opp {작업}` (플래그 없음) 또는 `//opp --semi-agentic {작업}` | PLAN까지 사용자 검토, EXECUTE 이후 PM 자율, **CLOSE 진입 사용자 승인 필수** |
| `agentic` | `//opp --agentic {작업}` | 전 단계 PM 자율 통과 — CLOSE 진입만 사용자 승인 필수 |

> 모든 Pilot(`opds` / `opd` / `opdw` / `opp` / `opsdd` / `opwt` / `oppd`)에 동일하게 적용된다.

**자율 실행 (semi-agentic / agentic) 동작**:
- 각 단계 완료 후 PM이 품질을 자체 검토하고 다음 단계로 진행
- 모든 판단·오류·수정 사항은 `AGENTIC-LOG.md`에 기록
- 블로커 또는 스코프 변경이 감지되면 즉시 사용자에게 에스컬레이션

**언제 어떤 모드를 쓸까**:

| 상황 | 권장 모드 |
|------|---------|
| 일상적인 개발·문서 작업 (기본) | `semi-agentic` (플래그 없음) |
| 처음 해보는 유형 / 규모가 크고 단계마다 확인하고 싶을 때 | `--interactive` |
| 작업 범위가 명확하고 중간 확인이 불필요할 때 | `--agentic` |

---

## 전문 에이전트 (Specialist Agent)

OPAL의 Pilot은 작업을 단계별로 나누어 워커(서브에이전트)에게 디스패치한다. 기본적으로 범용 워커(`opal-task-agent`)가 모든 단계를 처리하지만, 도메인별 전문성이 필요한 단계에서는 **전문 에이전트**가 투입된다.

PM은 PLAN.md의 각 Step에 명시된 **단계 + 영역** 조합을 보고 적합한 전문 에이전트를 자동으로 선택·라우팅한다. 예를 들어 FE 영역의 EXECUTE 단계에는 `opal-fe-agent`가, DB 영역의 PLAN 단계에는 `opal-db-agent`가 투입된다.

| 에이전트 | 영역 | 단계 | 역할 |
|---------|------|------|------|
| `opal-plan-agent` | 공통 | PLAN | 코드 분석 + 기능 설계 + 에이전트 라우팅 |
| `opal-fe-agent` | FE | EXECUTE | React, shadcn/ui, Tailwind 전문 구현 |
| `opal-be-agent` | BE | EXECUTE | API 설계, OWASP, 레이어 구조 전문 구현 |
| `opal-db-agent` | DB | PLAN, EXECUTE | DB 모델 설계 + 마이그레이션 |
| `opal-planning-agent` | 기획 | EXECUTE | 서비스 기획 산출물 (PRD, TRD 등) |
| `opal-test-agent` | 공통 | TEST | BE/FE/E2E 테스트 모드 |

> 전문 에이전트가 매칭되지 않는 단계·영역 조합에서는 범용 `opal-task-agent`가 폴백으로 사용된다.

---

## 아키텍처 개요

```
Global Layer (~/.opal/)          한 번 설치 → 모든 프로젝트에서 사용
┌─────────────────────────────────────────────────────────┐
│  skills/        Pilot(오케스트레이터) + 단계 스킬        │
│  agents/        서브에이전트 (전문 7 + 범용 4 + GC 2 = 13) │
│  community-skills/ 사용자 fetch 시 채워짐 (skills.sh 카탈로그) │
│  references/    레지스트리 + 모듈화된 하네스 (harness/)  │
│  AGENT.md       AI 에이전트 코어                         │
│  identity.md    에이전트 정체성                          │
└────────────────────────┬────────────────────────────────┘
                         │ 부트스트랩
Project Layer (프로젝트마다 설정)
┌────────────────────────▼────────────────────────────────┐
│  CLAUDE.md / .cursor/rules/  플랫폼 부트스트래퍼        │
│  .opal/AGENT.md              PM 프로필 (검토 기준 등)    │
│  docs/PROJECT.md             프로젝트 정의 + 문서 레지스트리 │
│  tasks/{NNN}-{name}/         태스크 산출물 폴더          │
└─────────────────────────────────────────────────────────┘
```

코드 파일에 `@header` 주석으로 메타데이터를 기록하고, `code-scan` 도구로 빠르게 탐색한다.

상세 아키텍처와 컴포넌트 구조는 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)를 참조한다.

---

## 트러블슈팅

### 부트스트랩 체크리스트가 뜨지 않음

- AI 도구를 재시작했는지 확인한다
- `~/.opal/AGENT.md` 파일이 존재하는지 확인한다: `ls ~/.opal/AGENT.md`
- 플랫폼별 부트스트래퍼 파일이 존재하는지 확인한다:
  - Claude Code: `~/.claude/CLAUDE.md`
  - Cursor: `~/.cursor/rules/000-opal-agent.mdc`
  - Gemini: `~/.gemini/GEMINI.md`

### `//` 커맨드 매칭 실패

- Node.js가 설치되어 있는지 확인한다: `node --version` (v18+ 필요)
- skill-registry 도구가 동작하는지 확인한다: `node ~/.opal/tools/skill-registry/skill-registry.js list`
- 스킬 이름의 정식 또는 약식 명칭이 정확한지 확인한다

### MCP 연결 실패

- 플랫폼별 MCP 설정 파일을 확인한다:
  - Claude Code: `claude mcp list`
  - Cursor: `~/.cursor/mcp.json`
  - Gemini: `~/.gemini/settings.json`
- MCP 서버 설치 상태를 검증한다: `claude mcp list` 또는 `opal-cli doctor` 실행 (현행 install은 자동 등록)

---

## License

OPAL은 MIT License 하에 배포된다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조한다.

Copyright (c) 2026 OPAL contributors
