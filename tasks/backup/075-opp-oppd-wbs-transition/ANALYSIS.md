# ANALYSIS: SDD(Specification-Driven Development) 스킬 설계 분석

> 작성일: 2026-04-03 | 작성자: 알투 | 버전: v1.0

---

## 1. 개요

캡틴의 요청: **명세 주도 개발(SDD)** 워크플로우를 OPAL 프레임워크에 녹여 새로운 스킬 체계를 구축한다. 단일 스킬이 아니라, 오케스트레이터 + 단계 스킬 + 전문 에이전트의 조합으로 설계한다.

### 캡틴 확인 사항

| 항목 | 답변 |
|------|------|
| 스킬 유형 | OPAL 전용 (오케스트레이터 + 하위 스킬/에이전트) |
| 기존 oppd 관계 | 새로운 스킬 (독립) |
| 대상 도메인 | 범용 (웹, 앱, 라이브러리 등 모든 개발) |
| Evals 구현 | LLM 기반 채점 (별도 에이전트) |

---

## 2. SDD 핵심 개념 (캡틴 입력 + spec-kit 분석)

### 2.1 캡틴이 정의한 SDD 7대 요소

| # | 요소 | 설명 |
|---|------|------|
| 1 | 명세서 작성 | 상세 기술 명세(spec.md) — What + 검증 기준 |
| 2 | Evals 품질 게이트 | 명세서 자체의 품질 점수화 (완결성, 경계 명확성, 추적 가능성, 모호성 노출, 아키텍처 일관성) |
| 3 | Test-First | 각 기능 단계 전 테스트 코드 선행 작성 |
| 4 | 하네스 제어 | 프롬프트 분할, 도구 사용 제어, 컨텍스트 관리 |
| 5 | 증거 기반 검증 | 테스트 통과 + 데모 + 명세 기준 충족 = 완료 |
| 6 | 맞춤형 린터 + Break Loop | 아키텍처 경계 강제, 2회 연속 실패 시 중단 |
| 7 | 궤적(Trajectory) 검증 | 결과뿐 아니라 도출 과정까지 확인 |

### 2.2 Evals 채점 루브릭 (캡틴 정의)

| 평가 차원 | 설명 |
|-----------|------|
| 완결성 (Completeness) | Acceptance criteria 명확 존재, Happy/Unhappy path 모두 커버 |
| 경계 명확성 (Boundary clarity) | 도메인 내부에 머물고, 교차 참조는 ID+이벤트로만 |
| 추적 가능성 (Traceability) | 상위 기능, 데이터 모델, ADR과 연결 |
| 모호성 노출 (Ambiguity exposure) | 용어집 미정의 용어, must/should 혼용 탐지 |
| 아키텍처 일관성 | 헌법(Constitution) 원칙 준수 |

### 2.3 캡틴이 정의한 테스트 전략

| 원칙 | 설명 |
|------|------|
| Test-First | 기능 구현 전 테스트 코드 선행 |
| Unhappy Path 포함 | 예외 상황 테스트 필수 |
| 브라우저 자동화 | Puppeteer 등으로 UI 검증 |
| 맞춤형 린터 | 아키텍처 경계 기계적 강제 |
| Break Loop | 2회 연속 실패 시 강제 중단 → 개발자에게 권한 이양 |
| 궤적 검증 | 테스트 통과만이 아닌, 도출 과정(Trajectory)까지 확인 |

---

## 3. GitHub spec-kit 분석

> 소스: https://github.com/github/spec-kit/blob/main/spec-driven.md

### 3.1 핵심 철학: 권력 역전 (Power Inversion)

- 기존: **코드가 왕** → 명세는 코드를 보조하는 스캐폴딩
- SDD: **명세가 왕** → 코드는 명세의 표현(expression)에 불과
- 명세-구현 갭을 좁히는 것이 아니라, **명세가 코드를 생성**함으로써 갭 자체를 제거
- 유지보수 = 명세 진화, 디버깅 = 명세 수정, 리팩토링 = 명세 재구조화

### 3.2 워크플로우 (3개 커맨드)

| 커맨드 | 역할 | 산출물 |
|--------|------|--------|
| `/speckit.specify` | 아이디어 → 구조화된 명세서 | `specs/{branch}/spec.md` |
| `/speckit.plan` | 명세서 → 구현 계획 | `plan.md`, `data-model.md`, `contracts/`, `research.md`, `quickstart.md` |
| `/speckit.tasks` | 계획 → 실행 가능한 태스크 리스트 | `tasks.md` (병렬 마킹 `[P]` 포함) |

### 3.3 6대 핵심 원칙

1. **Specifications as Lingua Franca** — 명세가 1차 산출물, 코드는 2차
2. **Executable Specifications** — 정밀하고 완전하며 모호하지 않아야 함
3. **Continuous Refinement** — 일회성 게이트가 아닌 지속적 검증
4. **Research-Driven Context** — 리서치 에이전트가 기술 컨텍스트 수집
5. **Bidirectional Feedback** — 프로덕션 현실이 명세 진화에 피드백
6. **Branching for Exploration** — 같은 명세에서 여러 구현 접근법 탐색

### 3.4 헌법 (Constitution) — 9개 조항

`memory/constitution.md`로 **불변 아키텍처 원칙**을 정의:

| 조항 | 원칙 | 핵심 |
|------|------|------|
| I | Library-First | 모든 기능은 독립 라이브러리로 시작 |
| II | CLI Interface Mandate | 모든 라이브러리는 CLI로 기능 노출 (텍스트 IN/OUT) |
| III | Test-First Imperative | **비협상** — 테스트 없이 코드 없음 |
| VII | Simplicity | 최대 3개 프로젝트, future-proofing 금지 |
| VIII | Anti-Abstraction | 프레임워크 직접 사용, 불필요한 래핑 금지 |
| IX | Integration-First Testing | 목(mock)보다 실제 DB/서비스 우선 |

### 3.5 템플릿이 LLM을 제약하는 7가지 메커니즘

| # | 메커니즘 | 효과 |
|---|----------|------|
| 1 | 구현 조기 진입 방지 | WHAT/WHY만, HOW 금지 |
| 2 | `[NEEDS CLARIFICATION]` 마커 강제 | 추측 금지, 모호함 명시 |
| 3 | 체크리스트 = 명세의 단위 테스트 | 자기 검증 |
| 4 | Phase -1 게이트 | Simplicity/Anti-Abstraction/Integration 사전 검증 |
| 5 | 계층적 디테일 관리 | 메인 문서는 high-level, 상세는 별도 파일 |
| 6 | Test-First 순서 강제 | contracts → test → source 순서 |
| 7 | 투기적 기능 방지 | "might need" 금지 |

---

## 4. OPAL과의 매핑 분석

### 4.1 대응 관계

| spec-kit 개념 | OPAL 대응 | 차이/갭 |
|---------------|----------|---------|
| `/speckit.specify` | oppd Phase 1 (opwt → PRD/TRD) | spec-kit은 PRD+TRD를 하나의 spec.md로 통합 |
| `/speckit.plan` | opd PLAN 단계 (op-dev-plan) | spec-kit은 contracts/, data-model 등 별도 분리 |
| `/speckit.tasks` | oppd Phase 2 (로드맵 수립) | 유사. spec-kit은 `[P]` 병렬 마킹이 간결 |
| Constitution | opal-harness Guards | **갭: OPAL엔 프로젝트별 "헌법" 개념 없음** |
| `[NEEDS CLARIFICATION]` 마커 | 없음 | **갭: 모호함 명시적 추적 체계 부재** |
| Phase -1 게이트 | PM 검수 게이트 | 유사하나 spec-kit이 더 구조화(체크리스트) |
| Continuous Refinement | QA Gate + PM Gate | 유사 |
| Research Agent | context7 MCP + 웹 검색 | OPAL이 더 풍부 |
| Template constraints | SKILL.md 프로세스 | 유사한 역할 |

### 4.2 OPAL에서 신규 도입이 필요한 개념

| 개념 | 설명 | 도입 이유 |
|------|------|----------|
| **Constitution** | 프로젝트별 불변 아키텍처 원칙 (`docs/CONSTITUTION.md`) | Guards는 프로세스 제약이고, 헌법은 아키텍처 제약 |
| **`[NEEDS CLARIFICATION]` 마커** | 명세서 내 모호함 명시적 추적 | Evals 에이전트가 탐지/점수 반영 |
| **Phase -1 게이트** | EXECUTE 전 아키텍처 원칙 사전 검증 (체크리스트) | 현재 PM 검수는 비구조적 |
| **Spec Evals 에이전트** | 명세서 품질 LLM 채점 (루브릭 기반) | 기존에 명세서 자체 품질 평가 체계 없음 |
| **궤적(Trajectory) 검증** | 결과뿐 아니라 도출 과정 확인 | 기존 검증은 결과(테스트 통과)에만 집중 |

---

## 5. 초기 아키텍처 구상

### 5.1 기존 OPAL 오케스트레이터 패턴 (참고)

```
opd:  TASK → ANALYSIS → PLAN+TEST-SCENARIO → EXECUTE (단일 태스크)
oppd: Phase1(opwt→PRD/TRD) → Phase2(로드맵) → Phase3(액션실행) (프로젝트)
```

### 5.2 SDD 오케스트레이터 초기 구상

```
opal-pilot-sdd (오케스트레이터)
│
├── Phase 0: CONSTITUTION (헌법 로드/생성)
│   └── 프로젝트 헌법(docs/CONSTITUTION.md) 로드 또는 신규 생성
│
├── Phase 1: SPEC (명세서 작성)
│   ├── op-sdd-spec (단계 스킬) — 도메인별 명세서(spec.md) 작성
│   └── spec-eval-agent (에이전트) — 명세서 품질 채점 (Evals)
│       ├── 루브릭: 완결성, 경계 명확성, 추적 가능성, 모호성 노출, 아키텍처 일관성
│       └── 게이트 점수 미달 → 피드백 → 재작성 루프
│
├── Phase 2: TEST-FIRST (테스트 코드 선행 작성)
│   ├── op-sdd-test (단계 스킬) — spec.md 기반 테스트 코드 생성
│   └── 맞춤형 린터 규칙 생성 (아키텍처 경계 강제)
│
├── Phase 3: EXECUTE (AI 코드 구현)
│   ├── 하네스 제어: 프롬프트 분할, 컨텍스트 관리
│   └── Break Loop: 2회 연속 실패 시 강제 중단
│
└── Phase 4: VERIFY (증거 기반 검증)
    ├── 테스트 통과 + 명세 기준 전수 충족 확인
    └── 궤적(Trajectory) 검증 — 과정 자체의 품질 확인
```

### 5.3 미결 설계 질문

| # | 질문 | 상태 |
|---|------|------|
| Q1 | 스킬 네이밍: `opal-pilot-sdd` (약어: `opsdd`)? | 미결 |
| Q2 | 기존 oppd와의 관계: 병립 (A) / Phase 교체 (B) / 모드 추가 (C) | 캡틴 답변: 새로운 스킬 (A) |
| Q3 | 단일 태스크 vs 프로젝트 단위 | 미결 |
| Q4 | Evals 루브릭 커스터마이징 (프로젝트별 오버라이드) | 미결 |
| Q5 | 명세서 표준 템플릿 형식 | spec-kit의 spec.md 패턴 참고 가능 |
| Q6 | Constitution이 기존 CONVENTIONS.md/ARCHITECTURE.md와 겹치는지 | 미결 |
| Q7 | spec-kit의 contracts/ 디렉토리 구조 채택 여부 | 미결 |

---

## 변경이력

| 버전 | 일시 | 작성자 | 변경내용 |
|------|------|--------|---------|
| v1.0 | 2026-04-03 | 알투 | 초기 작성 — 캡틴 입력 분석 + spec-kit 분석 + OPAL 매핑 |
