---
@header
type: task
task: "116 전문 에이전트(Specialist Agent) 체계 구축"
layer: task
---

# TASK: 전문 에이전트(Specialist Agent) 체계 구축

> 작성일: 2026-04-14 | 작업 유형: 신규 기능 | 적용 스킬: opp | 모드: interactive
> 입력: 사용자 요청 (MAMS 프로젝트 비서 모드에서 설계)
> 출력: TASK.md
> 비고: 일다 작성만 하고 나중에 필요 시점에 재검토할 예정임.

## 작업 목표

OPAL 프레임워크에 **전문 에이전트(Specialist Agent) 체계**를 도입한다. 프레임워크가 에이전트 템플릿(골격)을 제공하고, 각 프로젝트에서 템플릿 기반으로 프로젝트 특화 전문 에이전트를 생성하며, PM이 단계+도메인에 따라 적합한 전문 에이전트를 선택하여 디스패치하는 구조를 만든다.

## 배경

### 현재 문제

현재 OPAL의 워커 디스패치는 **범용 에이전트(opal-task-agent)** 하나에 의존한다:

1. **PM의 컨텍스트 조합 부담**: PM이 매 디스패치마다 opal-pm.md §3 5단계를 전체 범위에서 수행하여, 관련 문서/컨벤션/확정기준/금지사항을 수동으로 조합해 prompt에 주입
2. **워커의 범용 컨텍스트 과다**: opal-task-agent는 범용이므로 docs/PROJECT.md, CONVENTIONS.md, ARCHITECTURE.md, FRONTEND.md, BACKEND.md 등을 전부 Read — 실제 사용률 30~40%
3. **토큰 비효율**: 워커 prompt에 2~3만 토큰 주입, 워커 내부에서도 범용적 Read — FE 작업에 BE 규칙이, BE 작업에 FE 문서가 포함됨
4. **품질 편차**: PM의 판단에 따라 매번 다른 수준의 컨텍스트가 주입되어 워커 결과 품질이 불안정

### 설계 방향 (대화에서 합의)

| 항목 | 결정 |
|------|------|
| 패턴 | Template Method + Factory |
| PM | 변경 없음 (제너럴리스트, 전체를 알아야 함) |
| 워커 | 범용 → 전문 에이전트 (도메인/역할별 전문화) |
| 기존 에이전트 | 유지 (전문 에이전트 없는 프로젝트는 기존 방식) |
| 기존 pilot SKILL.md | 최소 변경 (디스패치 방식은 PM 프로세스가 담당) |

### 디자인 패턴 대응

```
Template Method Pattern:
  프레임워크 템플릿 (골격)     →  프로젝트 전문 에이전트 (세부)
  templates/specialists/       →  {프로젝트}/.opal/specialists/

Factory Pattern:
  PM이 (단계 + 도메인) → REGISTRY.md 매핑 테이블 → 적합한 에이전트 선택
```

## 배경 분석 (대화에서 도출)

### AS-IS 디스패치 흐름

```
pilot SKILL.md: "op-dev-plan 워커 디스패치. model: advanced"
    ↓
PM:
  1. [WORKER] 마커 삽입
  2. Guards 핵심 규칙 주입
  3. opal-pm.md §3 전체 범위 수행 (문서 선별 → Read → 제약 추출)
  4. 기술 스택 연동 지시 주입
  → Agent(opal-task-agent, prompt: 매번 수동 조합 2~3만 토큰)
    ↓
opal-task-agent (범용):
  1. SKILL.md Read
  2. docs/ 전부 Read (PROJECT, CONVENTIONS, ARCHITECTURE, FRONTEND, BACKEND...)
  3. 스킬 프로세스 실행
```

### TO-BE 디스패치 흐름

```
pilot SKILL.md: "PLAN 워커 디스패치. model: advanced"
    ↓
PM:
  1. TASK.md 도메인 태그 확인 → [backend]
  2. REGISTRY.md 조회 → PLAN + backend = analyst
  3. specialists/analyst/AGENT.md 로드 (이미 역할/규칙/도구 내장)
  → Agent(analyst, prompt: [AGENT.md 정의] + [태스크 내용] 1~1.2만 토큰)
    ↓
analyst (전문 에이전트):
  1. 자기 AGENT.md에 정의된 참조 문서만 Read
  2. 자기 역할에 맞는 프로세스 실행
  3. 자기 완료 기준으로 자가 검증
```

### 토큰 절감 예측

| 구분 | 현재 (범용) | 전문화 후 | 절감 |
|------|-----------|----------|------|
| PM → 워커 prompt | ~25,000 토큰 | ~10,000 토큰 | -60% |
| 워커 내부 Read | 범용적 전부 Read | 프로파일 기반 선별 Read | -50% |
| PM 조합 시간 | 매번 §3 5단계 전체 | 에이전트 선택 + 태스크 전달 | 단순화 |

### 현재 에이전트 자산 (활용)

| 자산 | 설명 | 활용 방법 |
|------|------|----------|
| `opal-agent-creator` 스킬 | 에이전트 생성 파이프라인 | 확장하여 템플릿 기반 전문 에이전트 생성 지원 |
| `agents/{name}/AGENT.md` 규격 | frontmatter + 본문 구조 확립 | 전문 에이전트도 동일 규격 사용 |
| 프로젝트별 탐색 경로 | `{프로젝트}/.opal/agents/` → `~/.opal/agents/` | 전문 에이전트도 동일 경로 체계 |
| `opal-model-mapping` | light/standard/advanced 레벨 | 전문 에이전트 model 필드에 적용 |
| `opal-task-agent` | 범용 워커 | 전문 에이전트 미등록 시 폴백 |

## 요구사항

### 1. 에이전트 템플릿 (Template Method)

- [ ] **R-1**: 프레임워크 에이전트 템플릿 체계 구축
  - **무엇을**: `opal/templates/specialists/` 디렉토리에 에이전트 유형별 템플릿 파일 생성. 각 템플릿은 OPAL 에이전트 규격(YAML frontmatter + 본문)을 따르며, 프로젝트가 채워야 할 placeholder를 `{변수명}` 형식으로 명시한다.
  - **어디에**: `opal/templates/specialists/`
  - **왜**: 프로젝트마다 전문 에이전트를 0에서 작성하는 것이 아니라, 프레임워크가 검증된 골격을 제공하여 품질 바닥선을 보장하기 위함
  - **AC**: 아래 4개 템플릿이 존재한다. 각 템플릿이 OPAL 에이전트 규격(frontmatter: name, description, model / 본문: 정체성, 행동 규칙 공통/프로젝트 특화, 참조 문서, 도구 활용, 완료 기준 공통/프로젝트 특화, 금지)을 따른다. 프로젝트 특화 섹션에 `{placeholder}` 변수가 있다.

  | 템플릿 | 역할 | 투입 단계 |
  |--------|------|----------|
  | `analyst.template.md` | 분석/설계 전문 + 병렬 실행 분해 | ANALYSIS, PLAN |
  | `developer.template.md` | 개발 전문 (기술스택별 세분화) | EXECUTE |
  | `qa-tester.template.md` | QA/테스트 전문 | QA Gate, TEST |
  | `writer.template.md` | 기획/문서 작성 전문 | 기획 산출물 |

- [ ] **R-2**: 템플릿 공통 골격(행동 규칙) 정의
  - **무엇을**: 모든 전문 에이전트가 공유하는 공통 행동 규칙을 정의한다. 이 규칙은 각 템플릿의 "행동 규칙 (공통)" 섹션에 포함된다.
  - **어디에**: 각 템플릿의 공통 섹션 또는 별도 `_common.md` 인클루드
  - **왜**: 전문 에이전트 간 일관된 행동 보장 (코드 기준 원칙, 불일치 보고, 완료 기준 충족 후 보고 등)
  - **AC**: 공통 행동 규칙(기존 코드 패턴 파악 → 따르기, 문서/코드 불일치 시 코드 기준 + 보고, 완료 기준 모두 충족 시 보고, 블로커 발생 시 즉시 status:blocked 반환)이 정의되어 있다.

### 2. 에이전트 매핑 체계 (Factory)

- [ ] **R-3**: REGISTRY.md 스펙 정의
  - **무엇을**: 프로젝트별 `{프로젝트}/.opal/specialists/REGISTRY.md`에 에이전트 매핑 테이블 형식을 정의한다. PM이 (단계 + 도메인) 조합으로 적합한 전문 에이전트를 선택하는 데 사용한다.
  - **어디에**: 스펙은 `opal/core/references/` 또는 해당 스킬 가이드 내. 실제 파일은 각 프로젝트 `.opal/specialists/REGISTRY.md`
  - **왜**: PM이 매번 판단하는 것이 아니라, 명시적 매핑 테이블로 에이전트 선택을 표준화하기 위함 (Factory Pattern)
  - **AC**: REGISTRY.md 형식이 정의되어 있다 (단계, 도메인, 에이전트명, 모델 레벨 컬럼). 폴백 규칙(매핑 없으면 opal-task-agent 사용)이 명시되어 있다. 탐색 경로(`{프로젝트}/.opal/specialists/REGISTRY.md`)가 정의되어 있다.

  REGISTRY.md 테이블 형식:
  ```markdown
  | 단계 | 도메인 | 에이전트 | 모델 레벨 | 비고 |
  |------|--------|---------|----------|------|
  | ANALYSIS | 공통 | analyst | standard | |
  | PLAN | 공통 | analyst | advanced | |
  | EXECUTE | backend | be-developer | standard | |
  | EXECUTE | frontend | fe-developer | standard | |
  | QA Gate | 공통 | qa-tester | light | |
  ```

- [ ] **R-4**: TASK.md에 도메인 태그 필드 추가
  - **무엇을**: `op-task/SKILL.md` (또는 op-task-plan)의 TASK.md 작성 프로세스에 `도메인` 필드를 추가한다. PM이 TASK 단계에서 작업 내용을 분석하여 도메인을 태깅한다.
  - **어디에**: `opal/skills/op-task/SKILL.md` — TASK.md 작성 프로세스 및 템플릿
  - **왜**: 후속 단계(PLAN, EXECUTE)에서 PM이 도메인 태그로 REGISTRY.md를 조회하여 전문 에이전트를 자동 선택하기 위함
  - **AC**: TASK.md 헤더에 `도메인:` 필드가 존재한다. 도메인 값 정의(backend, frontend, batch, planning, 복수 지정 가능)가 명시되어 있다. PM이 도메인을 판별하는 기준이 안내되어 있다.

### 3. PM 디스패치 프로세스 변경

- [ ] **R-5**: opal-pm.md §3 에이전트 선택 단계 추가
  - **무엇을**: 디스패치 전 프로세스(§3)에 "Step 0. 전문 에이전트 선택"을 추가한다. TASK.md 도메인 태그 → REGISTRY.md 조회 → 전문 에이전트 AGENT.md 로드. 전문 에이전트가 있으면 에이전트 정의 + 태스크 내용으로 prompt를 구성하고, 없으면 기존 방식(opal-task-agent + §3 Step 1~5 전체 수행)으로 폴백한다.
  - **어디에**: `opal/core/references/opal-pm.md` — §3 디스패치 전 프로세스
  - **왜**: PM의 디스패치 방식을 "컨텍스트 수동 조합"에서 "에이전트 선택 + 태스크 전달"로 전환하기 위함. 전문 에이전트에는 역할/규칙/문서/도구가 이미 내장되어 있으므로 PM의 주입 부담이 줄어든다.
  - **AC**: §3에 Step 0이 추가되어 있다. REGISTRY.md 조회 → 에이전트 선택 → AGENT.md 로드 흐름이 명시되어 있다. 폴백 규칙(REGISTRY.md 미존재 또는 매핑 없으면 기존 opal-task-agent 방식)이 명시되어 있다. Step 1~5와의 관계(전문 에이전트 있으면 Step 2~3 범위가 에이전트 정의로 한정됨)가 설명되어 있다.

- [ ] **R-6**: agents.md 레지스트리에 전문 에이전트 카테고리 추가
  - **무엇을**: `opal/core/references/agents.md`에 "전문 에이전트 (Specialist Agents)" 섹션을 추가한다. 프로젝트별로 생성되는 전문 에이전트의 등록 가이드와 탐색 경로를 명시한다.
  - **어디에**: `opal/core/references/agents.md`
  - **왜**: 기존 opal-pilot 에이전트(opal-task-agent 등)와 전문 에이전트의 관계를 명확히 하기 위함
  - **AC**: "전문 에이전트" 섹션이 존재한다. 탐색 경로(`{프로젝트}/.opal/specialists/{name}/AGENT.md`)가 명시되어 있다. 기존 범용 에이전트와의 관계(폴백 구조)가 설명되어 있다.

### 4. 에이전트 생성 스킬

- [ ] **R-7**: opal-agent-creator 확장 — 템플릿 기반 전문 에이전트 생성 모드
  - **무엇을**: 기존 opal-agent-creator에 "전문 에이전트 생성 모드(specialist)" 진입 분기를 추가한다. 이 모드에서는: (1) 프로젝트 코드베이스 분석(code-scan, 디렉토리 구조, 기술 스택) → (2) 필요한 전문 에이전트 식별 → (3) 해당 템플릿 로드 → (4) placeholder를 프로젝트 특화 값으로 채움 → (5) `{프로젝트}/.opal/specialists/{name}/AGENT.md` 생성 → (6) REGISTRY.md 생성/갱신.
  - **어디에**: `opal/skills/opal-agent-creator/SKILL.md`
  - **왜**: 프로젝트별 전문 에이전트를 수동으로 작성하는 부담을 줄이고, 템플릿 기반으로 일관된 품질의 에이전트를 자동 생성하기 위함
  - **AC**: 진입 분기에 "전문 에이전트 생성" 모드가 추가되어 있다. 프로젝트 분석 프로세스(코드베이스 스캔 → 도메인 식별 → 기술 스택 파악)가 정의되어 있다. 템플릿 로드 → placeholder 치환 프로세스가 정의되어 있다. REGISTRY.md 자동 생성이 포함되어 있다. 기존 모드(신규 생성, 개선)와 공존한다.

### 5. 병렬 실행 체계

- [ ] **R-8**: PLAN 산출물에 병렬 실행 설계 섹션 추가
  - **무엇을**: analyst 에이전트가 PLAN 산출물에 작성하는 병렬 실행 설계 구조를 정의한다. PLAN.md에 다음 3개 섹션을 추가한다: (1) 인터페이스 계약 — 에이전트 간 공유 인터페이스(API endpoint, request/response DTO, 공유 모델/타입) 확정, (2) 파일 스코프 — 각 에이전트가 수정 가능한 파일/디렉토리 범위를 명시적으로 분리, (3) 실행 배정 — 각 Step에 담당 에이전트 배정 + 병렬/순차 판단 + 의존 관계 표기.
  - **어디에**: `opal/skills/op-dev-plan/SKILL.md` — PLAN.md 작성 프로세스 및 산출물 구조. analyst 템플릿(`templates/specialists/analyst.template.md`)에도 병렬 분해 능력 반영.
  - **왜**: 전문 에이전트 병렬 디스패치 시, 에이전트 간 인터페이스 불일치와 파일 충돌을 사전에 방지하기 위함. analyst가 작업을 병렬 실행 가능한 수준으로 분해하고 계약을 정의해야 PM이 안전하게 병렬 디스패치할 수 있다.
  - **AC**: PLAN.md에 "인터페이스 계약", "파일 스코프", "실행 배정" 3개 섹션이 정의되어 있다. 실행 배정에 에이전트명 + 병렬/순차 표기 + 의존 관계가 포함된다. analyst 템플릿에 병렬 분해 지침이 포함되어 있다.

  PLAN.md 병렬 실행 설계 예시:
  ```markdown
  ## 인터페이스 계약
  | API | Method | Path | Request | Response |
  |-----|--------|------|---------|----------|
  | 캠페인 목록 | GET | /api/campaigns | ?page=1&size=20 | { items: CampaignResponse[], total } |

  CampaignResponse:
    campaignNo: number, campaignName: string, status: string, ...

  ## 파일 스코프
  | 에이전트 | 수정 가능 범위 | 금지 범위 |
  |---------|-------------|----------|
  | be-developer | workspace/backend/domains/mams/ | workspace/frontend/ |
  | fe-developer | workspace/frontend/src/ | workspace/backend/ |

  ## 실행 배정
  | Step | 에이전트 | 작업 | 병렬 | 의존 |
  |------|---------|------|------|------|
  | 1 | be-developer | 캠페인 조회 API | ∥ | - |
  | 2 | fe-developer | 캠페인 목록 화면 | ∥ | 인터페이스 계약 참조 |
  ```

- [ ] **R-9**: PM 병렬 디스패치 및 통합 검증 프로세스
  - **무엇을**: opal-pm.md에 전문 에이전트 병렬 디스패치 시 PM이 따르는 프로세스를 정의한다. (1) 사전 조건 확인 — PLAN.md에 인터페이스 계약 + 파일 스코프 + 실행 배정이 존재하는가, 병렬 표기된 Step 간 파일 스코프가 겹치지 않는가, (2) 병렬 디스패치 — PLAN의 실행 배정에 따라 병렬(∥) Step의 에이전트를 동시 호출, 각 에이전트 prompt에 인터페이스 계약 + 자기 파일 스코프를 주입, (3) 통합 검증 — 양쪽 에이전트 완료 후 PM이 수행: 인터페이스 계약 준수 여부(BE 응답이 계약과 일치, FE 호출이 계약과 일치), 파일 스코프 위반 여부(다른 에이전트 영역 파일을 수정하지 않았는가), 통합 동작 확인(빌드/타입체크/기본 연동).
  - **어디에**: `opal/core/references/opal-pm.md` — 신규 섹션 또는 §3 확장
  - **왜**: 병렬 디스패치 시 에이전트 간 조율은 PM의 책임이다. 에이전트끼리 실시간 통신이 불가능하므로, PM이 사전(계약 확인) + 사후(통합 검증)로 조율해야 한다.
  - **AC**: PM 병렬 디스패치 3단계(사전 조건 확인 → 병렬 디스패치 → 통합 검증)가 정의되어 있다. 각 단계의 체크리스트가 명시되어 있다. 파일 스코프 위반 감지 방법이 안내되어 있다. 기존 하네스 §7 병렬 처리 원칙과의 관계가 명시되어 있다.

  PM 병렬 디스패치 프로세스:
  ```
  Step A. 사전 조건 확인
    1. PLAN.md에 인터페이스 계약이 존재하는가
    2. PLAN.md에 파일 스코프가 명시되어 있는가
    3. 병렬(∥) Step 간 파일 스코프가 겹치지 않는가
    → 하나라도 미충족 시: 순차 실행으로 폴백 (안전 우선)

  Step B. 병렬 디스패치
    1. 병렬(∥) Step의 에이전트를 동시 Agent 호출
    2. 각 에이전트 prompt에 주입:
       - 자기 전문 에이전트 AGENT.md 정의
       - 인터페이스 계약 (공유)
       - 자기 파일 스코프 (수정 가능 범위 + 금지 범위)
       - 자기 Step의 작업 내용
    3. worktree 격리 여부는 파일 스코프 겹침 정도로 판단:
       - 완전 분리 → 동일 워킹 디렉토리 (기본)
       - 부분 겹침 → isolation: "worktree" 사용

  Step C. 통합 검증 (모든 병렬 에이전트 완료 후)
    1. 인터페이스 계약 준수: BE 응답 ↔ 계약, FE 호출 ↔ 계약
    2. 파일 스코프 위반: changed_files가 자기 스코프 내인가
    3. 통합 빌드/타입체크 통과
    4. worktree 사용 시: merge + 충돌 해결
    → 위반 감지 시: 해당 에이전트 재지시 (계약 기준)
  ```

- [ ] **R-10**: 동일 도메인 병렬 실행 — 파일 스코프 분리 규칙
  - **무엇을**: 같은 도메인(예: BE + BE) 에이전트가 병렬 실행될 때의 파일 스코프 분리 규칙을 정의한다. 동일 도메인은 파일 충돌 위험이 높으므로, (1) 패키지/모듈 단위 분리(model/ vs service/ vs router/) 또는 (2) 기능 단위 분리(campaign/ vs ad_group/)로 스코프를 나눈다. 공유 파일(예: `__init__.py`, 공통 model)이 불가피할 경우 worktree 격리를 필수로 적용한다.
  - **어디에**: opal-pm.md 병렬 디스패치 섹션 내, analyst 템플릿의 파일 스코프 작성 가이드
  - **왜**: FE+BE 병렬은 디렉토리가 물리적으로 분리되어 안전하지만, BE+BE 병렬은 같은 디렉토리 내에서 파일 충돌이 발생할 수 있으므로 별도 규칙이 필요
  - **AC**: 동일 도메인 병렬 시 파일 스코프 분리 방법(패키지 단위 / 기능 단위)이 정의되어 있다. 공유 파일 존재 시 worktree 격리 필수 규칙이 명시되어 있다. analyst가 파일 스코프 작성 시 겹침 여부를 명시적으로 판단하는 가이드가 있다.

  동일 도메인 분리 예시:
  ```markdown
  ## 파일 스코프 (BE + BE 병렬)
  | 에이전트 | 수정 가능 범위 | 공유 파일 | 격리 |
  |---------|-------------|----------|------|
  | be-developer-A | model/campaign.py, repository/campaign/ | __init__.py | worktree |
  | be-developer-B | model/ad_group.py, repository/ad_group/ | __init__.py | worktree |
  ```

### 6. 마이그레이션 및 호환성

- [ ] **R-11**: 하위 호환 보장 — 폴백 체계
  - **무엇을**: 전문 에이전트가 없는 프로젝트에서 기존 방식(opal-task-agent + PM 컨텍스트 주입)이 그대로 작동하도록 폴백 체계를 명시한다.
  - **어디에**: opal-pm.md §3 Step 0, REGISTRY.md 스펙
  - **왜**: 전문 에이전트 체계는 점진적 도입(gradual rollout)이므로, 미적용 프로젝트의 기존 동작을 보장해야 함
  - **AC**: 다음 3가지 폴백 경로가 명시되어 있다.

  폴백 체계:
  ```
  1. REGISTRY.md 미존재       → 기존 방식 (opal-task-agent + §3 Step 1~5 전체)
  2. REGISTRY.md 존재, 매핑 없음 → 해당 단계/도메인은 기존 방식
  3. REGISTRY.md 존재, 매핑 있음 → 전문 에이전트 사용
  ```

- [ ] **R-12**: pilot SKILL.md 영향 최소화
  - **무엇을**: 기존 pilot SKILL.md(opds, opd, opp, oppd, opwt, opsdd)의 변경을 최소화한다. pilot은 "어떤 단계를 어떤 순서로"를 정의하고, "어떤 에이전트로 디스패치하는가"는 opal-pm.md §3이 담당하므로, pilot SKILL.md에는 "PM이 적합한 에이전트를 선택하여 디스패치한다" 정도의 안내만 추가한다.
  - **어디에**: 각 pilot SKILL.md의 디스패치 지시 부분
  - **왜**: pilot SKILL.md는 파이프라인 골격을 정의하는 문서로, 에이전트 선택 로직이 침투하면 관심사가 혼재됨. 디스패치 방식은 PM 프로세스(opal-pm.md)에서 일원화해야 함
  - **AC**: pilot SKILL.md에 에이전트 선택 로직이 포함되지 않는다. "PM이 REGISTRY.md 기반으로 에이전트를 선택한다" 안내가 있거나, 기존 지시를 유지한다.

### 7. MAMS 프로젝트 적용 예시

- [ ] **R-13**: MAMS 전문 에이전트 초안 목록
  - **무엇을**: MAMS 프로젝트에서 생성할 전문 에이전트 목록과, 기존 AGENT.md 확정기준/금지사항의 분배 예시를 작성한다. 이 항목은 설계 참고용이며, 실제 생성은 R-7 완료 후 MAMS 프로젝트에서 수행한다.
  - **어디에**: 이 TASK.md 내 (참고 섹션)
  - **왜**: 설계가 실제 프로젝트에서 어떻게 적용되는지 구체적 예시를 제공하여 설계 검증 및 OPAL 알투의 구현 참고 자료로 활용
  - **AC**: 아래 에이전트 목록과 분배 예시가 포함되어 있다.

  MAMS 전문 에이전트 목록:
  | 에이전트 | 역할 | 기존 확정기준 분배 |
  |---------|------|------------------|
  | analyst | 분석/설계 전문 | #1 (기획 관리 방식) |
  | be-developer | BE 개발 전문 (FastAPI+SQLAlchemy) | #2(camelCase), #3(엔티티 네이밍), #4(user_no 기본값), #5(Service 규칙), #6(소프트 삭제), #7(AUTO_INCREMENT) |
  | fe-developer | FE 개발 전문 (Vue+shadcn/ui) | (향후 FE 확정기준 추가 시) |
  | batch-developer | 배치/수집 전문 (DAG, 매체 API) | 매체별 수집 패턴 차별화 (메모리 참조) |
  | qa-tester | QA/테스트 전문 | #8(@header 규칙) — 공통 |

  MAMS REGISTRY.md 예시:
  | 단계 | 도메인 | 에이전트 | 모델 레벨 |
  |------|--------|---------|----------|
  | ANALYSIS | 공통 | analyst | standard |
  | PLAN | 공통 | analyst | advanced |
  | EXECUTE | backend | be-developer | standard |
  | EXECUTE | frontend | fe-developer | standard |
  | EXECUTE | batch | batch-developer | standard |
  | QA Gate | 공통 | qa-tester | light |
  | TEST | 공통 | qa-tester | standard |

## 제약 조건

- 기존 범용 에이전트(opal-task-agent, opal-task-qa-agent 등)는 수정하지 않는다 — 폴백으로 유지
- 기존 pilot SKILL.md의 파이프라인 구조(단계 정의, Gate 순서)는 변경하지 않는다
- 전문 에이전트의 AGENT.md는 기존 OPAL 에이전트 규격(frontmatter + 본문)을 따른다
- `~/.opal/` 직접 수정 금지 — 소스 경로(`opal/`)에서만 수정 후 install로 배포
- 전문 에이전트가 pilot의 단계 스킬(op-dev-plan, op-dev-execute 등)을 대체하는 것이 아니다 — 전문 에이전트가 단계 스킬을 "더 잘 실행"하는 것이다

## 아키텍처 변경 범위

### 레이어 구조

```
Layer 1. 프레임워크 (opal/)
  ├── templates/specialists/        [신규] 에이전트 템플릿
  ├── core/references/opal-pm.md    [수정] §3 Step 0 추가 + 병렬 디스패치 프로세스
  ├── core/references/agents.md     [수정] 전문 에이전트 섹션 추가
  ├── skills/opal-agent-creator/    [수정] specialist 모드 추가
  └── skills/op-dev-plan/           [수정] PLAN.md에 병렬 실행 설계 섹션 추가

Layer 2. 프로젝트 ({프로젝트}/.opal/)
  ├── specialists/                  [신규] 프로젝트 특화 전문 에이전트
  │   ├── REGISTRY.md              [신규] 에이전트 매핑 테이블
  │   ├── analyst/AGENT.md         [신규] 템플릿 기반 생성
  │   ├── be-developer/AGENT.md    [신규] 템플릿 기반 생성
  │   └── ...
  └── AGENT.md                      [변경 없음] PM 공통 설정 유지

Layer 3. Pilot (기존 유지)
  └── pilot SKILL.md                [최소 변경] 디스패치 안내만 추가
```

### 디스패치 흐름 변경

```
기존 (순차 + 범용):
  pilot → PM §3(전체 수행) → opal-task-agent(범용) → 완료 → 다음 Step

변경 후 (전문 에이전트 + 병렬 가능):
  pilot → PM §3 Step 0(에이전트 선택)
              │
              ├── REGISTRY.md 있음 + 매핑 있음 → 전문 에이전트 디스패치
              │   │
              │   ├── PLAN.md 실행 배정 = 순차(→)
              │   │   → Step 1 에이전트 완료 → Step 2 에이전트 디스패치
              │   │
              │   └── PLAN.md 실행 배정 = 병렬(∥)
              │       → Step 1 + Step 2 에이전트 동시 디스패치
              │       → 양쪽 완료 → PM 통합 검증
              │
              └── REGISTRY.md 없음 or 매핑 없음 → 기존 방식 폴백
                  prompt = §3 Step 1~5 전체 수행 + opal-task-agent

병렬 디스패치 조건 (R-9):
  1. PLAN.md에 인터페이스 계약 있음
  2. PLAN.md에 파일 스코프 분리 있음
  3. 파일 스코프 겹침 없음 → 동일 워킹 디렉토리
     파일 스코프 부분 겹침 → worktree 격리
  4. 조건 미충족 → 순차 폴백 (안전 우선)
```

## 기술 스택

- Markdown 문서 작업 (에이전트 AGENT.md, 스킬 SKILL.md, 레퍼런스 .md)
- YAML frontmatter (에이전트 규격)

## 관련 문서

- `opal/core/references/agents.md` — 에이전트 레지스트리
- `opal/core/references/opal-pm.md` — PM 행동 프로세스 (§3 디스패치 전 프로세스)
- `opal/core/references/opal-harness.md` — 하네스 공통
- `opal/core/references/opal-harness-interactive.md` — PM Gate 절차
- `opal/core/references/opal-model-mapping.md` — 모델 매핑
- `opal/skills/opal-agent-creator/SKILL.md` — 기존 에이전트 생성 스킬
- `opal/agents/opal-task-agent/AGENT.md` — 범용 워커 (폴백 대상)
- `opal/agents/opal-task-qa-agent/AGENT.md` — 범용 QA 워커 (폴백 대상)
- `opal/templates/` — 기존 템플릿 폴더 (현재 test-tools.yaml만 존재)
- `opal/core/references/harness/parallel-execution.md` — 기존 하네스 §7 병렬 처리 원칙 (R-9와 정합 필요)
- `opal/skills/op-dev-plan/SKILL.md` — PLAN 워커 스킬 (R-11 PLAN 산출물 구조 변경)

## 구현 우선순위 제안

```
Phase 1 (기반): R-1, R-2, R-3       — 템플릿 + REGISTRY 스펙
Phase 2 (연결): R-4, R-5, R-6       — TASK.md 도메인 태그 + PM 프로세스 + agents.md
Phase 3 (병렬): R-8, R-9, R-10       — PLAN 병렬 설계 + PM 병렬 디스패치 + 동일 도메인 규칙
Phase 4 (자동화): R-7                — 에이전트 생성 스킬 확장
Phase 5 (호환): R-11, R-12           — 폴백 + pilot 최소 변경
Phase 6 (검증): R-13                 — MAMS 적용으로 검증
```
