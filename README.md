# OPAL — Open Protocol for Agentic Links

AI 환경(Claude Code, Cursor 등)에서 개발·기획·문서 작업을 체계적으로 수행하는 **AI 에이전트 프레임워크**.
설치 후 `//` 커맨드 하나로 다단계 AI 파이프라인을 실행한다.

---

## 목차

1. [설치](#설치)
2. [프로젝트 설정](#프로젝트-설정)
3. [핵심 개념 — `//` 커맨드](#핵심-개념----커맨드)
4. [오케스트레이터 사용법](#오케스트레이터-사용법)
   - [opds — 개발 Short Task](#opds--개발-short-task-기본)
   - [opd — 개발 Full Task](#opd--개발-full-task)
   - [opdw — Wireframe UI](#opdw--wireframe-ui)
   - [opp — 범용 프로젝트 작업](#opp--범용-프로젝트-작업)
   - [opsdd — SDD 명세 기반 개발](#opsdd--sdd-명세-기반-개발)
   - [opwt — 서비스 기획 산출물](#opwt--서비스-기획-산출물)
   - [oppd — 프로젝트 개발 라이프사이클](#oppd--프로젝트-개발-라이프사이클)
5. [독립 스킬 사용법](#독립-스킬-사용법)
6. [Agentic Mode — 자율 실행](#agentic-mode--자율-실행)
7. [아키텍처 개요](#아키텍처-개요)

---

## 설치

```bash
git clone {REPO_URL} opal
cd opal
./scripts/install-mac.sh
```

설치 메뉴에서 선택한다:

| 옵션 | 설명 |
|------|------|
| `[1]` OPAL 설치 | 스킬·에이전트·부트스트래퍼 → `~/.opal/` |
| `[2]` MCP 서버 설정 | Claude Code / Cursor / Gemini용 MCP 설정 |
| `[3]` 전체 설치 | OPAL + MCP 서버 동시 설치 |

설치 후 **AI 도구를 재시작**하면 즉시 사용 가능하다.

---

## 프로젝트 설정

OPAL을 사용하려는 **각 프로젝트**에 아래 설정이 필요하다.

### 자동 설정 (권장)

AI 채팅창에서 아래 커맨드를 입력하면 프로젝트 설정을 자동으로 생성한다.

```
//opi
```

> `opi`(opal-project-init)가 프로젝트를 분석하고 `.opal/AGENT.md`, `docs/PROJECT.md`, `docs/CONVENTIONS.md` 등을 생성한다.

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

---

## 핵심 개념 — `//` 커맨드

AI 채팅창에서 `//`로 시작하는 입력은 **OPAL 스킬 호출**로 처리된다.

```
//{스킬 약어} {작업 설명}
```

예시:
```
//opds 로그인 버튼 클릭 시 스피너가 표시되지 않는 버그 수정
//opwt PRD 초안 작성해줘
//opp 오래된 패키지 의존성 업그레이드
```

### 실행 흐름

오케스트레이터는 작업을 여러 단계로 나누어 실행한다. 각 단계가 끝날 때마다 AI가 결과를 보고하고 다음 단계 진행 여부를 확인한다.

```
사용자: //opds {작업}
  → AI: TASK.md 작성 후 보고 (다음 단계 승인 요청)
  → 사용자: 승인 ("응", "진행해", "go" 등)
  → AI: PLAN.md 작성 후 보고 (구현 계획 검토 요청)
  → 사용자: 승인
  → AI: 코드 구현 → 완료 보고
```

**핵심 규칙**: 사용자가 명시적으로 승인하기 전까지 코드를 생성하거나 파일을 수정하지 않는다.

---

## 오케스트레이터 사용법

### opds — 개발 Short Task (기본)

**언제 쓰나**: 코드 변경이 수반되는 모든 개발 작업의 기본 진입점. 버그 수정, 기능 추가, 리팩토링 등.

**파이프라인**: `TASK → PLAN → TEST-SCENARIO → EXECUTE → TEST`

**산출물**: `TASK.md`, `PLAN.md`, `TEST-SCENARIO.md`, `DONE.md`

#### 사용 예시

```
//opds 결제 완료 후 이메일 발송이 간헐적으로 실패하는 버그 수정
```

```
//opds 사용자 프로필 페이지에 SNS 링크 입력 필드 추가
```

```
//opds UserService의 findById 메서드를 캐시 레이어 적용해서 최적화
```

#### 진행 흐름

```
1. AI → TASK.md 작성 (작업 정의, 요구사항, 범위)
        "TASK 완료했습니다. PLAN 단계로 넘어갈까요?"

2. 승인 → AI → PLAN.md 작성 + TEST-SCENARIO.md 작성 (검증 기준 선정의)
            "PLAN + 테스트 시나리오 검토해주세요. 승인하시면 구현 시작합니다."

3. 승인 → AI → 코드 구현 (EXECUTE)
            → 테스트 실행 (TEST) — 실패 시 자동 수정 후 재테스트 (최대 3회)
            → DONE.md 생성 + 완료 보고
```

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

**파이프라인**: `TASK → ANALYSIS → PLAN → TEST-SCENARIO → EXECUTE → TEST`

**산출물**: `TASK.md`, `ANALYSIS.md`, `PLAN.md`, `TEST-SCENARIO.md`, `DONE.md`

> `opds`와 차이: ANALYSIS 단계가 추가되어 코드베이스를 먼저 깊이 분석한 후 계획을 수립한다.

#### 사용 예시

```
//opd OAuth 소셜 로그인 (Google, Kakao) 기능 전체 구현
```

```
//opd 모놀리식 UserService를 도메인 레이어로 분리 리팩토링
```

```
//opd 실시간 알림 시스템 — WebSocket 기반 서버 푸시 구현
```

#### 진행 흐름

```
1. AI → TASK.md 작성
        "TASK 완료. ANALYSIS 단계로 넘어갈까요?"

2. 승인 → AI → 코드베이스 분석 → ANALYSIS.md 작성 (의존 관계, 영향 범위, 기술 리스크)
            "분석 완료. PLAN 단계로 넘어갈까요?"

3. 승인 → AI → PLAN.md 작성 + TEST-SCENARIO.md 작성 (검증 기준 선정의)
            "PLAN + 테스트 시나리오 검토해주세요. 승인하시면 구현 시작합니다."

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

#### 사용 예시

```
//opdw 첨부한 정책서 기반으로 마이페이지 화면 설계하고 구현해줘
```

```
//opdw 스케치 이미지 참고해서 대시보드 화면 만들어줘
```

```
//opdw 새 상품 등록 화면 — 입력 폼 + 이미지 업로드 + 미리보기
```

> 기존 프로젝트에서 화면을 수정하거나 추가하는 작업은 `opds` 또는 `opd`를 사용한다.

---

### opp — 범용 프로젝트 작업

**언제 쓰나**: 코드 개발이 아닌 모든 프로젝트 작업. 문서 작성, 설정 변경, 의존성 업그레이드, 환경 설정, 스크립트 작성 등.

**파이프라인**: `TASK → PLAN → EXECUTE`

**산출물**: `TASK.md`, `PLAN.md`, `DONE.md`

#### 사용 예시

```
//opp README 전면 개편 — 사용자 매뉴얼 수준으로 상세화
```

```
//opp 패키지 의존성 취약점 점검 및 업그레이드
```

```
//opp ESLint + Prettier 설정 추가 및 기존 코드 일괄 적용
```

```
//opp GitHub Actions CI 파이프라인 구성 — lint, test, build
```

```
//opp 로컬 개발 환경 Docker Compose 구성
```

---

### opsdd — SDD 명세 기반 개발

**언제 쓰나**: "무엇을 만들지"를 먼저 엄밀하게 정의한 뒤 개발하고 싶을 때. 기능 명세(SPEC)를 SSOT로 삼아 테스트 시나리오 → 설계 → 구현까지 파이프라인을 관리한다.

**파이프라인**: `TASK → SPEC → REVIEW → DESIGN → EXECUTE-LOOP → DONE`

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

#### 사용 예시

```
//opsdd 구독 플랜 관리 기능 — 플랜 생성/변경/해지, 결제 연동
```

```
//opsdd 멀티 테넌트 권한 시스템 — 조직/역할/리소스 3계층 모델
```

```
//opsdd 실시간 재고 관리 — 입출고 이벤트 기반, 동시성 보장
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

#### 사용 예시

```
//opwt PRD 초안 작성 — 커머스 플랫폼 셀러 관리 기능
```

```
//opwt 서비스 정책서 수정 — 최근 변경된 환불 정책 반영
```

```
//opwt 기존 PRD와 TRD 검토 후 불일치 사항 진단 보고서 작성
```

```
//opwt IA 작성 — 와이어프레임 참고해서 사이트맵과 기능 목록 정리
```

```
//opwt 개발 WBS 작성 — PRD/TRD 기반으로 개발 항목 구조화
```

---

### oppd — 프로젝트 개발 라이프사이클

**언제 쓰나**: 아이디어에서 완성까지 전체 개발 사이클을 한 번에 관리하고 싶을 때. 기획(opwt) → WBS → 코드 구현을 하나의 파이프라인으로 연결한다.

**파이프라인**: `PLAN(기획 산출물) → WBS → EXECUTE(코드 구현)`

#### 사용 예시

```
//oppd 셀러 온보딩 기능 — 회원가입부터 첫 상품 등록까지 전 과정
```

```
//oppd 관리자 대시보드 — 매출 현황, 사용자 통계, 알림 관리
```

> `docs/PROJECT.md`가 없으면 프로젝트 초기화(`opi`)를 자동 실행한 후 진행한다.

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

## Agentic Mode — 자율 실행

기본 모드에서는 각 단계마다 사용자 승인이 필요하다. `--agentic` 플래그를 추가하면 PM이 단계 간 게이트를 자율적으로 통과하여 중간 확인 없이 끝까지 실행한다.

```
//opds --agentic {작업 설명}
//opd --agentic {작업 설명}
//opp --agentic {작업 설명}
//opsdd --agentic {기능 설명}
```

**자율 실행 시 동작**:
- 각 단계 완료 후 PM이 품질을 자체 검토하고 다음 단계로 진행
- 모든 판단/오류/수정 사항은 `AGENTIC-LOG.md`에 기록
- 블로커 또는 스코프 변경이 감지되면 즉시 사용자에게 에스컬레이션

**언제 agentic을 쓸까**:

| 상황 | 권장 모드 |
|------|---------|
| 작업 범위가 명확하고, 중간에 확인이 필요 없을 때 | `--agentic` |
| 규모가 크거나, 중요한 설계 결정이 포함될 때 | 기본 (interactive) |
| 처음 해보는 유형의 작업 | 기본 (interactive) |

---

## 아키텍처 개요

```
Global Layer (~/.opal/)          한 번 설치 → 모든 프로젝트에서 사용
┌─────────────────────────────────────────────────────────┐
│  skills/        오케스트레이터 + 단계 스킬               │
│  agents/        서브에이전트 (워커)                      │
│  community-skills/  외부 조직 제공 스킬 (31개)           │
│  references/    레지스트리 + 가이드 문서                 │
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

상세 아키텍처와 컴포넌트 구조는 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)를 참조한다.

---

## 오케스트레이터 한눈에 보기

| 커맨드 | 이름 | 사용 상황 |
|--------|------|----------|
| `//opds` | Short Task Dev | 버그 수정, 기능 추가, 리팩토링 — 코드 작업의 기본 |
| `//opd` | Full Task Dev | 대규모 기능 개발, 멀티 모듈 변경 |
| `//opdw` | Wireframe UI | 새 화면 기획 → 와이어프레임 → UI 구현 |
| `//opp` | 범용 Project | 문서, 설정, 환경, 스크립트 등 코드 외 모든 작업 |
| `//opsdd` | SDD 개발 | 명세 먼저 정의하고 개발하는 방식 |
| `//opwt` | 기획 산출물 | PRD, TRD, 정책서, IA, WBS |
| `//oppd` | 프로젝트 Dev | 아이디어 → 기획 → WBS → 코드 전체 라이프사이클 |
