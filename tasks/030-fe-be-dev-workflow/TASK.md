# TASK: 프론트엔드/백엔드 개발 워크플로우 체계화

> 작성일: 2026-03-22 | 작업 유형: 신규

## 작업 목표

opi 이후 실제 FE/BE 개발 진행 시, 어떤 스킬·에이전트·커뮤니티 스킬·MCP를 어떻게 조합해서 쓸지 체계를 만든다.

## 배경

현재 dev-task-pilot은 Full/Short/Wireframe UI 3모드 파이프라인이 잘 갖춰져 있지만, 각 모드의 EXECUTE 단계에서 **프론트엔드/백엔드별로 어떤 도구를 어떤 순서로 적용할지** 가이드가 없다. 워커 에이전트(dtp-dev-agent, dtp-wireframe-ui-agent)가 커뮤니티 스킬이나 MCP를 활용하는 규칙도 정의되어 있지 않다.

## 요구사항

- [ ] FE/BE 개발 시 활용할 컴포넌트 조합 체계 정의
- [ ] 기존 구조 개선 / 신규 생성 / 하이브리드 중 최적 방향 도출
- [ ] 선택한 방향에 따른 구현

## 제약 조건

- 기존 dtp 3모드 파이프라인 구조를 깨지 않을 것
- 불필요한 복잡성 추가 금지 — 실제 개발 시 자연스럽게 적용되어야 함

## 관련 문서

- `skills/dev-task-pilot/SKILL.md` — dtp 오케스트레이터
- `skills/dev-task-pilot/modes/` — 모드별 파이프라인
- `skills/dev-task-pilot/references/` — 단계별 가이드
- `agents/dtp-dev-agent/AGENT.md` — Full/Short 워커
- `agents/dtp-wireframe-ui-agent/AGENT.md` — Wireframe UI 워커

## 현행 분석 (사전 리서치)

### 현재 프레임워크가 보유한 FE/BE 관련 컴포넌트

#### 프론트엔드 관련

| 컴포넌트 | 유형 | 현재 역할 |
|---------|------|----------|
| wireframe-builder | 스킬 | 정책서 → wireframe.md (ASCII 레이아웃 + shadcn 매핑) |
| ui-designer | 스킬 | wireframe.md → React + shadcn/ui (프로토타입/프로덕션) |
| dtp-wireframe-ui-agent | 에이전트 | Wireframe UI 파이프라인 워커 |
| dtp-qa-wireframe-agent | 에이전트 | wireframe↔코드 대조 QA |
| vercel-labs/shadcn | 커뮤니티 스킬 | shadcn/ui 4대 Critical Rules |
| vercel-labs/react-best-practices | 커뮤니티 스킬 | 워터폴 제거, 번들 최적화, 리렌더 최소화 (8카테고리) |
| vercel-labs/next-best-practices | 커뮤니티 스킬 | RSC 경계, Data Patterns, async params (11영역) |
| vercel-labs/composition-patterns | 커뮤니티 스킬 | boolean props 폭발 방지, Compound Components (4카테고리) |
| anthropics/frontend-design | 커뮤니티 스킬 | Design Thinking 3단계 (Purpose→Aesthetics→Avoid) |
| anthropics/webapp-testing | 커뮤니티 스킬 | Playwright 기반 UI 동적 검증 |
| shadcn MCP | MCP | 컴포넌트 검색/조회/예제/설치 명령 생성 |
| context7 MCP | MCP | React, Next.js 등 최신 API 문서 실시간 조회 |

#### 백엔드 관련

| 컴포넌트 | 유형 | 현재 역할 |
|---------|------|----------|
| dtp-dev-agent | 에이전트 | Full/Short Task 워커 (범용) |
| dtp-qa-dev-agent | 에이전트 | ANALYSIS/PLAN 정적 리뷰 |
| dtp-action-plan-agent | 에이전트 | 복잡 모드 실행 아키텍처 설계 |
| dtp-dev-test-agent | 에이전트 | 테스트 실행 + 코드 품질/보안 검사 |
| api-analyzer | 스킬 | 외부 API 7단계 분석 → 명세서 |
| interview | 스킬 | 구조화된 Q&A 요구사항 수집 |
| trailofbits/modern-python | 커뮤니티 스킬 | uv, ruff, ty 기반 모던 Python 도구체계 |
| getsentry/code-review | 커뮤니티 스킬 | Runtime errors, N+1, 보안, backwards compat |
| openai/security-best-practices | 커뮤니티 스킬 | OWASP top 10, 보안 취약점 리뷰 |
| context7 MCP | MCP | FastAPI, SQLAlchemy 등 최신 문서 |
| sequential-thinking MCP | MCP | 복잡한 아키텍처 설계 시 단계별 추론 |

### 현재의 문제점

1. **연결 부재**: 위 컴포넌트들이 개별적으로 존재하지만, dtp 파이프라인 안에서 "언제 어떤 것을 적용할지" 규칙이 없음
2. **워커 무지**: dtp-dev-agent는 커뮤니티 스킬(react-best-practices, modern-python 등)의 존재를 모름 — 참조 지시가 없음
3. **FE/BE 구분 없음**: EXECUTE 가이드(execute-guide.md)가 FE/BE 구분 없이 범용적 — 프론트 코드를 작성하면서 shadcn 규칙이나 RSC 경계를 자동 적용할 메커니즘 없음
4. **테스트 도구 연계 부재**: dtp-dev-test-agent가 webapp-testing(Playwright) 스킬을 활용하는 규칙이 없음
5. **프로토타입→프로덕션 전환 가이드 부재**: ui-designer의 두 모드를 전환하는 명확한 절차 없음

### 검토 방향 (ANALYSIS에서 비교)

| # | 방향 | 설명 |
|---|------|------|
| A | 기존 개선 | references/에 fe-guide.md, be-guide.md 추가 + execute-guide.md에 분기 로직 |
| B | 신규 생성 | FE 전용 워커 / BE 전용 워커 에이전트 분리 |
| C | 하이브리드 | 기존 dtp 구조 유지 + FE/BE 레퍼런스 가이드 + 워커 프롬프트에 커뮤니티 스킬 참조 주입 |

---

## 참고: opi 이후 개발 워크플로우 제안 (사전 리서치 결과)

> 아래는 ANALYSIS 전 사전 리서치에서 도출한 "이상적인 개발 워크플로우" 제안이다. 현재 프레임워크에 이 체계가 없으며, 이 태스크의 목표는 이를 실현하는 것이다.

### 1. 진입점: dev-task-pilot (모든 개발의 시작)

opi로 프로젝트 세팅이 끝나면, 모든 개발 요청은 **dev-task-pilot** 스킬이 진입점. 자동으로 3가지 모드를 판별:

| 모드 | 판별 조건 | 파이프라인 | 적합한 작업 |
|------|----------|-----------|------------|
| **Short Task** (기본) | 대부분의 작업 | TASK → PLAN → TEST-SCENARIO → EXECUTE | 버그 수정, 단일 기능, 3~5파일 변경 |
| **Full Task** | 변경 파일 ≥10, 다중 모듈, 아키텍처 결정 | TASK → ANALYSIS → PLAN → TODO → TEST-SCENARIO → EXECUTE | 신규 모듈, 대규모 리팩토링 |
| **Wireframe UI** | "UI 만들어줘", wireframe.md 제공, 정책서+UI | TASK → WIREFRAME → EXECUTE → QA | 화면 설계+구현 |

### 2. 프론트엔드 개발

#### 설계 단계

| 순서 | 컴포넌트 | 유형 | 역할 |
|------|---------|------|------|
| 1 | **wireframe-builder** | 스킬 | 정책서/요구사항 → wireframe.md (ASCII 레이아웃 + shadcn 매핑 + 인터랙션 정의) |
| 2 | **dtp-qa-wireframe-agent** | 에이전트 | wireframe.md 품질 검증 (W-1~W-5: 커버리지, 구조, 인터랙션, 데이터, 구현가능성) |
| 3 | **interview** | 스킬 | 요구사항 불명확 시 구조화된 Q&A로 보완 |

#### 구현 단계

| 순서 | 컴포넌트 | 유형 | 역할 |
|------|---------|------|------|
| 1 | **ui-designer** | 스킬 | wireframe.md → React + shadcn/ui 코드 (프로토타입: bundle.html / 프로덕션: Next.js) |
| 2 | **shadcn MCP** | 도구 | 컴포넌트 검색(`search_items`), 소스 조회(`view_items`), 예제(`get_item_examples`), 설치(`get_add_command`) |
| 3 | **context7 MCP** | 도구 | Next.js, React 등 최신 API 문서 실시간 조회 (deprecated 방지) |

#### 품질 보증 (자동 적용)

| 컴포넌트 | 유형 | 적용 시점 |
|---------|------|----------|
| **vercel-labs/shadcn** | 커뮤니티 스킬 | 구현 시 — 4대 Critical Rules (Styling, Forms, Structure, Component Selection) |
| **vercel-labs/react-best-practices** | 커뮤니티 스킬 | 구현 시 — 워터폴 제거, 번들 최적화, 리렌더 최소화 |
| **vercel-labs/next-best-practices** | 커뮤니티 스킬 | Next.js 프로젝트 — RSC 경계, Data Patterns, async params |
| **vercel-labs/composition-patterns** | 커뮤니티 스킬 | 복잡 컴포넌트 — boolean props 폭발 방지, Compound Components |
| **dtp-qa-wireframe-agent** | 에이전트 | EXECUTE 완료 후 — 빌드/린트 + wireframe↔코드 대조 (E-1~E-6) |
| **anthropics/webapp-testing** | 커뮤니티 스킬 | 테스트 — Playwright 기반 UI 동적 검증 |

### 3. 백엔드 개발

#### 분석·설계 단계

| 순서 | 컴포넌트 | 유형 | 역할 |
|------|---------|------|------|
| 1 | **dtp-dev-agent** | 에이전트 | ANALYSIS — 코드베이스 분석, 영향 범위, 기술 조사 |
| 2 | **api-analyzer** | 스킬 | 외부 API 연동 시 — 7단계 분석 (인증→엔드포인트→요청/응답→페이징→레이트리밋→에러→연동전략) |
| 3 | **dtp-qa-dev-agent** | 에이전트 | ANALYSIS.md/PLAN.md 정적 리뷰 (커버리지, 코드 실독, 설계 구체성 검증) |
| 4 | **dtp-action-plan-agent** | 에이전트 | Full Task 복잡 모드 — 실행 토폴로지(DAG), 스킬 갭 분석, 도구 요구사항, 테스트 전략 |
| 5 | **context7 MCP** | 도구 | FastAPI, SQLAlchemy 등 최신 문서 조회 |
| 6 | **sequential-thinking MCP** | 도구 | 복잡한 아키텍처 설계 시 단계별 추론 구조화 |

#### 구현 단계

| 순서 | 컴포넌트 | 유형 | 역할 |
|------|---------|------|------|
| 1 | **dtp-dev-agent** | 에이전트 | EXECUTE — TODO 체크리스트 기반 코드 작성 (복잡 모드: 내부 서브에이전트 병렬 배치) |
| 2 | **trailofbits/modern-python** | 커뮤니티 스킬 | Python 프로젝트 — uv, ruff, ty 기반 모던 도구체계 |

#### 테스트·보안 (자동 적용)

| 컴포넌트 | 유형 | 적용 시점 |
|---------|------|----------|
| **dtp-dev-test-agent** | 에이전트 | EXECUTE 완료 후 — TEST-SCENARIO 실행, 회귀 테스트, 코드 품질, 보안 검사 |
| **getsentry/code-review** | 커뮤니티 스킬 | QA 시 — Runtime errors, N+1 쿼리, 보안, backwards compat |
| **anthropics/webapp-testing** | 커뮤니티 스킬 | API 엔드포인트 Playwright 테스트 |

### 4. 전체 흐름도

```
opi 완료 (프로젝트 세팅)
    │
    ▼
개발 요청 → dev-task-pilot (모드 자동 판별)
    │
    ├─── 프론트엔드 UI ──────────────────────────────────┐
    │    Wireframe UI 모드                                │
    │    ┌─ wireframe-builder → wireframe.md             │
    │    ├─ QA: dtp-qa-wireframe-agent (W-1~W-5)        │
    │    ├─ ui-designer → React + shadcn/ui              │
    │    │  ├─ shadcn MCP (컴포넌트 검색/설치)           │
    │    │  ├─ shadcn 스킬 (Critical Rules)              │
    │    │  ├─ react-best-practices (성능)               │
    │    │  ├─ next-best-practices (RSC, Data)           │
    │    │  └─ composition-patterns (구조)               │
    │    ├─ QA: dtp-qa-wireframe-agent (E-1~E-6)        │
    │    └─ webapp-testing (Playwright UI 검증)          │
    │                                                     │
    ├─── 백엔드 로직 ────────────────────────────────────┐
    │    Short Task (소규모) / Full Task (대규모)         │
    │    ┌─ dtp-dev-agent: ANALYSIS                      │
    │    │  ├─ api-analyzer (외부 API 연동 시)           │
    │    │  └─ context7 MCP (최신 문서)                  │
    │    ├─ QA: dtp-qa-dev-agent                         │
    │    ├─ dtp-dev-agent: PLAN                          │
    │    │  └─ sequential-thinking MCP (복잡 설계)       │
    │    ├─ QA: dtp-qa-dev-agent                         │
    │    ├─ [Full] dtp-dev-agent: TODO                   │
    │    │  └─ dtp-action-plan-agent (복잡 모드 Part C)  │
    │    ├─ dtp-dev-agent: EXECUTE                       │
    │    │  └─ modern-python (Python 백엔드)             │
    │    ├─ dtp-dev-test-agent (테스트 실행)             │
    │    └─ code-review (코드 품질/보안)                 │
    │                                                     │
    └─── 공통 ───────────────────────────────────────────┐
         ├─ interview (요구사항 불명확 시)                │
         ├─ STATE.md (체크포인트, 세션 중단 복구)        │
         └─ .opal/MEMORY.md (작업 히스토리 축적)         │
```

### 5. 개선 포인트

| # | 포인트 | 현황 | 제안 |
|---|--------|------|------|
| 1 | **프론트+백 동시 개발** | 각각 별도 태스크로 진행 | Full Task 복잡 모드의 Part C 토폴로지가 이미 병렬 배치를 지원하므로, 하나의 태스크에서 FE/BE 에이전트를 병렬 실행 가능 |
| 2 | **API 계약 연동** | FE↔BE 간 API 스펙 동기화가 명시적이지 않음 | api-analyzer로 생성한 명세서를 wireframe.md의 데이터 바인딩과 연결하는 규칙 추가 고려 |
| 3 | **프로토타입→프로덕션 전환** | ui-designer가 두 모드 지원하지만, 전환 가이드 부족 | 프로토타입(bundle.html) 검증 후 프로덕션(Next.js)으로 이식하는 마이그레이션 가이드 필요 |
| 4 | **테스트 도구 레지스트리** | `.opal/test-tools.yaml`로 관리 | opi에서 프로젝트 기술 스택 기반으로 test-tools.yaml 초기 템플릿 자동 생성하면 dtp-dev-test-agent 첫 실행이 매끄러워짐 |

---

## 참고: 다른 세션에서의 실전 피드백

> 실제 데이터 파이프라인 태스크에서 발견된 3개 버그가 모두 "실행해보기 전까지 발견 불가" 유형이었음. 이를 기반으로 다른 알투가 제안한 개선안.

### 실전 버그 사례

| 버그 | 원인 | 방지 수단 |
|------|------|----------|
| `async_session_factory = None` | Python 값 복사 import | code-review 스킬, 스모크 테스트 |
| 날짜 float, campaign_id float | 데이터 파일 컬럼 타입 미확인 | ANALYSIS에서 실제 데이터 샘플링 |
| (기타 런타임 에러) | 정적 분석만으로 미발견 | 서버 기동 테스트 |

### 제안된 개선안 (ROI순)

#### 1. ANALYSIS에 실데이터 샘플링 추가 — ROI 높음

**대상**: `analysis-guide.md`

데이터 파이프라인 태스크에서 "실제 파일의 첫 5행을 읽어 컬럼 타입/형식을 기록" 단계 추가. 날짜 float, campaign_id float 같은 문제를 ANALYSIS에서 사전 발견 가능.

#### 2. EXECUTE 후 스모크 테스트 자동화 — ROI 높음

**대상**: `dtp-dev-test-agent AGENT.md`

현재 정적 분석만 수행 (py_compile, tsc). 개선:
- ruff check 실제 실행
- 서버 기동 테스트 (uvicorn 시작 → /health 호출 → 종료)
- 핵심 API 1회 호출 (실제 에러 발생 여부 확인)

→ `async_session_factory = None` 같은 런타임 에러 즉시 발견.

#### 3. ANALYSIS에 context7 MCP 의무 호출 — ROI 중간

**대상**: `analysis-guide.md`

태스크에서 사용하는 핵심 라이브러리(openpyxl, SQLAlchemy, asyncio 등)의 최신 문서를 context7로 조회. deprecated 패턴 방지 + 정확한 API 사용.

#### 4. EXECUTE 후 code-review 스킬 자동 실행 — ROI 중간

**대상**: `dev-full.md` EXECUTE 단계

EXECUTE 완료 후 getsentry/code-review 스킬 기준으로 자동 리뷰. Runtime errors, N+1 쿼리, 보안 취약점 등 패턴 매칭.

#### 5. EXECUTE에서 shadcn MCP/스킬 자동 적용 — ROI 낮음

**대상**: `execute-guide.md`

UI 변경이 포함된 EXECUTE에서:
- shadcn MCP로 Progress, Alert 등 기존 컴포넌트 확인 후 사용
- vercel-labs/shadcn 스킬로 shadcn/ui 베스트 프랙티스 적용

### 핵심 시사점

이 피드백의 공통 메시지: **현재 dtp 파이프라인에 커뮤니티 스킬과 MCP를 연결하는 메커니즘이 없어서, 이미 갖고 있는 도구를 활용하지 못하고 있다.** 이는 본 태스크의 "문제점 1. 연결 부재", "문제점 2. 워커 무지"와 정확히 일치한다.
