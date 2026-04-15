---
@header
type: task
task: "117 전문 개발 에이전트 시스템 설계"
layer: task
---

# TASK: 전문 개발 에이전트 시스템 설계

> 작성일: 2026-04-15 | 작업 유형: 신규 기능 | 적용 스킬: opp | 모드: interactive
> 입력: 사용자 요청 (대화에서 설계 합의)
> 출력: TASK.md

## 작업 목표

opal-task-agent 범용 워커 체계를 **도메인 전문 에이전트 체계**로 개편한다. 프론트엔드, 백엔드, 테스터 등 전문 에이전트를 분리하고, PM이 도메인별로 필요한 컨텍스트만 주입하는 구조를 만들어 **토큰 효율, 개발 속도, 품질**을 동시에 개선한다.

## 배경

### 현재 문제

mams 프로젝트를 하면서 규모가 커지면서 개발 속도와 품질이 떨어지고 있다. 토큰 효율도 떨어지고 있다.

현재 OPAL의 워커 디스패치는 **범용 에이전트(opal-task-agent)** 하나에 의존한다:

```
현재: PM → opal-task-agent (범용) → 모든 단계 실행
                ↓
        매번 ALL docs 로딩 (PROJECT + ARCH + CONV + FE + BE + ...)
        매번 페르소나 전환 (frontend-engineer ↔ backend-engineer)
        FE/BE 구분 = persona 파일 1개 차이뿐
```

### 병목 1: 토큰 낭비

- FE Step인데 BE 문서(BACKEND.md, BE-FRAMEWORK.md)까지 로딩하고, 그 반대도 동일
- opal-task-agent가 매번 SKILL.md + persona + PROJECT.md + ARCHITECTURE.md + CONVENTIONS.md + FRONTEND.md + BACKEND.md + BE-FRAMEWORK.md 등을 전체 로딩
- 컨텍스트의 30~50%가 불필요한 문서

### 병목 2: 전문성 부재

- 범용 에이전트가 personas/frontend-engineer.md 또는 personas/backend-engineer.md 파일 1개로 "전문가 연기"
- 프로젝트가 커질수록 품질 저하
- FE/BE 구분이 persona 파일 1개 차이뿐

### 병목 3: 병렬 실행 한계

- 같은 에이전트 타입이라 도메인 간 충돌 관리 어려움
- FE/BE 동시 진행 시 영역 침범 위험

## 배경 분석 (대화에서 도출)

### opal-task-agent 사용 현황

| 스킬 | 단계 | 파이프라인 |
|------|------|-----------|
| op-dev-analysis | ANALYSIS | opd (개발) |
| op-dev-plan | PLAN | opd (개발) |
| op-dev-test-scenario | TEST-SCENARIO | opd (개발) |
| op-dev-execute | EXECUTE | opd (개발) |
| op-task-execute | EXECUTE | opp (범용) |
| op-sdd-spec | SPEC | opsdd (SDD) |
| op-sdd-plan | PLAN | opsdd (SDD) |
| op-sdd-verify | VERIFY | opsdd (SDD) |

opal-task-action-agent가 opal-task-agent를 내부에서 디스패치하는 역할도 하고 있어 변경 영향을 받는다.

### 현재 에이전트 구성

| 에이전트 | 위치 | 역할 |
|----------|------|------|
| opal-task-agent | agents/ | 범용 워커 — 모든 단계 스킬 실행 |
| opal-task-qa-agent | agents/ | 범용 QA 워커 |
| op-dev-test-agent | agents/ | TEST-SCENARIO 기반 테스트 실행 |
| opal-task-action-agent | agents/ | oppd Phase 3 액션 자율 실행 |
| opal-sdd-action-agent | opal/agents/ | opsdd 전용 액션 에이전트 |
| wtm-agent | agents/ | 범용 web-to-markdown (OPAL 무관) |

### docs/ 업데이트 빈 구간 분석

현재 docs/ 업데이트 담당 현황:

| 스킬 | 역할 | 대상 문서 | 시점 |
|------|------|----------|------|
| opi (opal-project-init) | 생성 + 최신화 | PROJECT, ARCHITECTURE, CONVENTIONS, FRONTEND, BACKEND | 초기화 / `//opi 최신화` 수동 호출 |
| oppd (opal-pilot-project-dev) | 등록 | PROJECT.md 문서 테이블에 PRD, TRD, WBS 등록 | Phase 완료 시 |
| opwt (opal-pilot-write-tech) | 등록 확인 | PROJECT.md 문서 테이블 | 배치 완료 후 |
| opal-pm.md §4 | 등록 제안 | 신규 문서 → PROJECT.md 등록 | 작업 완료 후 |

빈 구간:

```
opi 초기화 → 개발 태스크 반복(코드는 변하는데 docs/는 안 변함) → opi 최신화 (수동)
```

빈 구간의 구체적 문제:

- EXECUTE 후 docs/ 미갱신: 새 API 엔드포인트 추가했는데 BACKEND.md에 미반영 → 다음 태스크에서 에이전트가 잘못된 정보로 작업
- 구조 변경 후 ARCHITECTURE.md 미갱신: 새 미들웨어 레이어 추가했는데 문서 그대로 → PLAN 단계에서 잘못된 아키텍처 참조
- 신규 컨벤션 미반영: 새 패턴 도입했는데 CONVENTIONS.md 미갱신 → 다음 태스크에서 옛날 패턴으로 코드 작성
- 문서 간 불일치 누적: FRONTEND.md의 컴포넌트 목록이 실제와 다름 → FE 에이전트가 없는 컴포넌트 참조

전문 에이전트 체계에서 이게 더 심각해지는 이유:

- 현재(범용 에이전트): opal-task-agent가 코드도 읽고 docs/도 읽음 → 불일치를 어느 정도 코드로 보완
- 전문 에이전트 체계: opal-fe-agent는 FRONTEND.md + CONVENTIONS.md (FE)만 읽음 → docs/가 부정확하면 에이전트가 받는 컨텍스트 자체가 틀림 → 코드를 전부 읽어서 보완하면 토큰 효율 이점이 사라짐
- **docs/ 정확도가 전문 에이전트 체계의 전제 조건**

## 확정된 설계 방향 (대화에서 합의)

### 1. 전문 개발 에이전트 구성

| 에이전트 | 역할 | model | 대체 대상 |
|----------|------|-------|----------|
| **opal-fe-agent** (신규) | 프론트엔드 전문 워커 | standard | opal-task-agent + FE persona |
| **opal-be-agent** (신규) | 백엔드 전문 워커 | standard | opal-task-agent + BE persona |
| **opal-test-agent** (기존 강화) | 테스트 전문 워커 | standard | op-dev-test-agent 강화 |
| **opal-plan-agent** (신규) | PLAN 단계 전문 워커 — 코드 분석 + 설계를 고품질로. model: advanced 고정 | advanced | opal-task-agent의 PLAN 단계 역할 |
| **opal-task-agent** (기존 축소) | 범용 워커 — 비개발 단계 전담으로 축소 | standard | 비개발 단계(문서 등) 전담 |

추가 고려 에이전트 (이번 태스크 범위 밖, 향후 검토):

| 에이전트 | 근거 | 우선순위 |
|----------|------|----------|
| opal-db-agent | DB 마이그레이션/스키마 전문 — mams처럼 모델이 복잡한 프로젝트에서 유효 | 중간 |
| opal-infra-agent | Docker, CI/CD, 환경 설정 — 현재는 빈도가 낮아 BE에 포함 가능 | 낮음 |

구성도:

```
PM (오케스트레이터)
 │
 ├─ PLAN 단계 ──→ opal-plan-agent (advanced)     ← 신규
 │                  코드 분석 + 설계 + 테스트 시나리오
 │
 ├─ EXECUTE 단계
 │   ├─ FE Steps ──→ opal-fe-agent (standard)    ← 신규
 │   ├─ BE Steps ──→ opal-be-agent (standard)    ← 신규
 │   └─ 범용 Steps → opal-task-agent (standard)  ← 기존 유지
 │
 ├─ TEST 단계 ──→ opal-test-agent (standard)     ← 기존 강화
 │
 └─ QA 단계 ───→ opal-task-qa-agent (light)      ← 기존 유지
```

opal-task-agent의 역할 변화 (비개발 단계 전담으로 축소):

| 단계 | 현재 | 변경 후 |
|------|------|---------|
| PLAN | opal-task-agent | **opal-plan-agent** |
| EXECUTE (FE) | opal-task-agent + FE persona | **opal-fe-agent** |
| EXECUTE (BE) | opal-task-agent + BE persona | **opal-be-agent** |
| EXECUTE (범용/문서) | opal-task-agent | opal-task-agent (유지) |
| TEST-SCENARIO | opal-task-agent | opal-plan-agent (PLAN에 통합됨, 115에서 이미 완료) |
| TEST | op-dev-test-agent | **opal-test-agent** (강화) |

### 2. PM 컨텍스트 효율 — 에이전트별 슬라이싱

**현재** — opal-task-agent가 매번 로드:

```
SKILL.md + persona + PROJECT.md + ARCHITECTURE.md + CONVENTIONS.md 
+ FRONTEND.md + BACKEND.md + BE-FRAMEWORK.md + ...
= 전체 로딩 (사용하지 않는 문서 포함)
```

**제안** — PM이 에이전트별로 필요한 것만 주입:

| 에이전트 | 고정 컨텍스트 (자체 로드) | PM 주입 컨텍스트 |
|----------|------------------------|-----------------|
| **opal-plan-agent** | SKILL.md, plan-guide.md, 커뮤니티 스킬 | TASK.md, 기술 스택별 문서 전체 |
| **opal-fe-agent** | SKILL.md, FE 전문 지식 (내장) | PLAN.md §3 해당 F-NNN 설계만, FRONTEND.md, CONVENTIONS.md (FE 섹션) |
| **opal-be-agent** | SKILL.md, BE 전문 지식 (내장) | PLAN.md §3 해당 F-NNN 설계만, BACKEND.md, BE-FRAMEWORK.md |
| **opal-test-agent** | SKILL.md, 테스트 전문 지식 (내장) | TEST-SCENARIO.md, changed_files, 해당 도메인 문서 |

PM의 "컨텍스트 슬라이싱":

```
PLAN.md
  §3. F-001: 로그인 API
  §3. F-002: 로그인 화면
  §3. F-003: 세션 관리

PM 슬라이싱:
  opal-be-agent  ← §3 F-001 + F-003 (BE 영역)
  opal-fe-agent  ← §3 F-002 (FE 영역)
```

에이전트별 문서 매핑 테이블:

| 에이전트 | 필수 문서 | 선택 문서 |
|----------|----------|----------|
| opal-plan-agent | PROJECT, ARCHITECTURE, CONVENTIONS | FRONTEND, BACKEND, 도메인 전체 |
| opal-fe-agent | CONVENTIONS (FE), FRONTEND | PROJECT (요약만) |
| opal-be-agent | CONVENTIONS (BE), BACKEND, BE-FRAMEWORK | PROJECT (요약만) |
| opal-test-agent | ARCHITECTURE (테스트 섹션) | 해당 도메인 문서 |

토큰 절감 효과 추정:

| 항목 | 현재 | 제안 | 절감 |
|------|------|------|------|
| 문서 로딩 | 전체 (~8,000 토큰) | 도메인별 (~3,000) | ~60% |
| PLAN 참조 | 전체 §1~§9 | 해당 F-NNN §3만 | ~70% |
| 페르소나 | 매번 Read | 에이전트에 내장 | ~100% |

### 3. PLAN 단계 — 에이전트 라우팅 + 병렬/순차 분류

PLAN.md §4에 에이전트 라우팅 정보 추가. 현재 §4.2 실행 체크리스트의 각 Step에 **agent** 필드를 추가:

```markdown
#### Step 1: 로그인 API 엔드포인트 구현
- [ ] 완료
- **소속 기능**: F-001
- **영역**: BE                          ← 기존
- **agent**: opal-be-agent              ← 신규
- **파일**: backend/src/auth/router.py
- **작업 내용**: POST /auth/login 구현
- **완료 기준**: 200 응답 + JWT 발급
- **테스트**: TS-001
- **의존**: 없음

#### Step 2: 로그인 화면 UI 구현
- [ ] 완료
- **소속 기능**: F-002
- **영역**: FE                          ← 기존
- **agent**: opal-fe-agent              ← 신규
- **파일**: frontend/src/pages/login.tsx
- **작업 내용**: 로그인 폼 + 유효성 검사
- **완료 기준**: 폼 제출 → API 호출
- **테스트**: TS-002
- **의존**: Step 1                       ← BE API 먼저
```

병렬/순차 판별 → 에이전트 배치 매핑:

```
§4.1 Phase 그룹핑 + §4.3 의존 관계
  ↓
Batch 1: [Step 1(BE), Step 3(BE)]  → opal-be-agent 병렬
Batch 2: [Step 2(FE), Step 4(FE)]  → opal-fe-agent 병렬 (Step 1,3 완료 후)
Batch 3: [Step 5(통합)]            → opal-be-agent 또는 opal-fe-agent
```

PM 디스패치 프로세스 (변경안):

```
1. PLAN.md §4 파싱
2. Step별 영역(FE/BE/DB/공통) → agent 자동 매핑
3. 의존 그래프로 Batch 구성
4. Batch별 디스패치:
   ├─ 독립 Step → 병렬 디스패치 (각 전문 에이전트)
   └─ 의존 Step → 선행 완료 대기 후 순차 디스패치
5. 각 에이전트에 주입:
   ├─ PLAN.md §3 해당 F-NNN 섹션 (슬라이싱)
   ├─ 도메인 문서 (FE/BE 분리)
   ├─ 관련 TEST-SCENARIO (해당 TS-ID만)
   └─ changed_files (선행 Batch 결과)
```

에이전트별 테스트 시나리오 분배:

| 시나리오 | 영역 | 검증 에이전트 | 시점 |
|----------|------|-------------|------|
| TS-001: API 응답 검증 | BE | opal-test-agent (BE mode) | BE Batch 완료 후 |
| TS-002: 폼 렌더링 검증 | FE | opal-test-agent (FE mode) | FE Batch 완료 후 |
| TS-003: 로그인 E2E | 통합 | opal-test-agent (E2E mode) | 전체 완료 후 |

### 4. opal-pm.md 변경 사항

#### §3. 디스패치 전 프로세스 — 변경

**현재**: 문서 선별 → 핵심 제약 추출 → opal-task-agent에 통째로 주입
**변경 후**: agents.md에서 에이전트 선택 → 문서 선별 → 에이전트별 슬라이싱 → 각 전문 에이전트에 분리 주입

§3에 추가해야 할 신규 Step:

Step 0. 에이전트 선택 (신규, 기존 Step 1~5 앞에 추가):
1. agents.md의 전문 에이전트 매핑 테이블을 Read
2. 현재 단계 + 영역으로 적합한 에이전트를 선택
3. 전문 에이전트 없으면 기존 opal-task-agent로 폴백
4. PLAN 에이전트 디스패치 시: 매핑 테이블을 함께 주입 (agent 필드 배정 위임)

기존 Step 1~5 유지 (전문 에이전트 있으면 슬라이싱 범위가 해당 에이전트 도메인으로 한정됨) +

Step 6. 실행 라우팅 (신규):
1. PLAN.md §4 실행 체크리스트에서 각 Step의 agent 필드를 참조
2. 의존 그래프 기반 Batch 구성
3. Batch 내 독립 Step → 병렬 / 의존 Step → 순차

Step 7. 컨텍스트 슬라이싱 (신규):
에이전트별로 필요한 컨텍스트만 추출:
- PLAN.md §3 해당 F-NNN 섹션만
- 도메인 문서 (FE용 / BE용 분리)
- TEST-SCENARIO 해당 TS-ID만
- 선행 Batch의 changed_files (통합 Step용)

#### §4. 검토 게이트 — 변경

| 항목 | 현재 | 변경 |
|------|------|------|
| 검토 절차 3 | 체크리스트 일괄 평가 | 에이전트별 영역 침범 여부 추가 |
| 검토 절차 신규 | — | Batch 간 인터페이스 정합성 (BE API ↔ FE 호출 일치) |
| Fail 시 재지시 | opal-task-agent에 | 해당 전문 에이전트에 재지시 |

PM Gate 추가 항목:
- [ ] FE 에이전트가 BE 파일을 수정하지 않았는가
- [ ] BE 에이전트가 FE 파일을 수정하지 않았는가
- [ ] 공통 영역(타입 정의 등) 변경 시 양쪽에 영향 분석이 되었는가

#### §6. 참조 문서 전달 의무 — 변경

**현재**: 전체 문서를 워커에게 전달
**변경 후**: 에이전트별 문서 매핑 테이블 추가 (위 에이전트별 문서 매핑 테이블 참조)

#### §10. 통합 조율 (신규 섹션)

전문 에이전트 체계에서 PM이 새로 담당해야 할 역할:

1. 인터페이스 계약 관리
   - BE가 만든 API 스펙 → FE에 전달
   - 공통 타입 정의 → 양쪽에 동기화

2. Batch 간 핸드오프
   - Batch N 완료 → changed_files 수집 → Batch N+1에 주입
   - 선행 Batch 실패 → 후속 Batch 중단 판단

3. 충돌 해소
   - 동일 파일을 FE/BE 양쪽에서 수정해야 할 때 → 순차로 전환
   - 공통 영역 변경 시 → 먼저 실행한 에이전트 결과를 후속에 반영

### 5. docs/ 갱신 관리 — 방안 3 (PLAN 통합)

PLAN.md §4 실행 체크리스트에 docs/ 갱신 Step을 자동 추가:

```markdown
#### Step N+1: docs/ 갱신
- [ ] 완료
- **소속 기능**: F-NNN
- **영역**: 문서
- **agent**: PM 직접
- **파일**: docs/BACKEND.md
- **작업 내용**: 새 API 엔드포인트 3개 반영
- **의존**: Step 3 (BE API 구현 완료 후)
```

이렇게 하면:
1. PLAN 단계에서 docs/ 갱신 범위가 미리 정해짐
2. EXECUTE 후 PM이 해당 Step을 직접 수행 (또는 경량 워커 디스패치)
3. 다음 태스크 시작 전에 docs/가 최신 상태 보장

## 요구사항

### 1. 전문 에이전트 AGENT.md 생성

- [ ] **R-1**: opal-fe-agent AGENT.md 작성
  - **무엇을**: 프론트엔드 전문 워커 에이전트 정의. FE 전문 지식(React, shadcn/ui, Tailwind, 접근성 등)을 에이전트에 내장하고, 자체적으로 FRONTEND.md + CONVENTIONS.md (FE 섹션)만 로딩하도록 정의한다. 기존 `op-dev-execute/personas/frontend-engineer.md`의 지식을 흡수·확장한다.
  - **어디에**: `opal/agents/opal-fe-agent/AGENT.md`
  - **왜**: FE Step 실행 시 BE 문서를 로딩하지 않도록 하여 토큰 절감 + FE 전문 품질 보장
  - **AC**: AGENT.md가 OPAL 에이전트 규격(frontmatter: name, description, model, icon + 본문)을 따른다. 자체 로드 문서 목록(FRONTEND.md, CONVENTIONS.md FE)이 명시되어 있다. BE 파일 수정 금지 규칙이 포함되어 있다. FE 기술 스택별 MCP/스킬 활용 지침(shadcn MCP, context7 등)이 포함되어 있다.

- [ ] **R-2**: opal-be-agent AGENT.md 작성
  - **무엇을**: 백엔드 전문 워커 에이전트 정의. BE 전문 지식(API 설계, 데이터 모델링, 보안, 미들웨어 등)을 에이전트에 내장하고, 자체적으로 BACKEND.md + BE-FRAMEWORK.md + CONVENTIONS.md (BE 섹션)만 로딩하도록 정의한다. 기존 `op-dev-execute/personas/backend-engineer.md`의 지식을 흡수·확장한다.
  - **어디에**: `opal/agents/opal-be-agent/AGENT.md`
  - **왜**: BE Step 실행 시 FE 문서를 로딩하지 않도록 하여 토큰 절감 + BE 전문 품질 보장
  - **AC**: AGENT.md가 OPAL 에이전트 규격을 따른다. 자체 로드 문서 목록(BACKEND.md, BE-FRAMEWORK.md, CONVENTIONS.md BE)이 명시되어 있다. FE 파일 수정 금지 규칙이 포함되어 있다. BE 기술 스택별 MCP/스킬 활용 지침(context7 등)이 포함되어 있다.

- [ ] **R-3**: opal-plan-agent AGENT.md 작성
  - **무엇을**: PLAN 단계 전문 워커 에이전트 정의. 코드 분석 + 설계 + 테스트 시나리오 작성을 고품질로 수행한다. model: advanced 고정. 전체 docs/를 읽을 수 있으며, 기능별 분석·설계·병렬/순차 분류·에이전트 라우팅을 수행한다. PM이 디스패치 시 agents.md의 전문 에이전트 매핑 테이블을 주입하면, 이를 참조하여 PLAN.md §4 실행 체크리스트의 각 Step에 agent 필드를 배정한다.
  - **어디에**: `opal/agents/opal-plan-agent/AGENT.md`
  - **왜**: PLAN 단계는 전체 프로젝트 컨텍스트가 필요하며, advanced 모델로 고품질 설계를 보장. PM이 전문 에이전트 매핑 테이블을 주입하므로 PLAN 에이전트가 에이전트 목록을 하드코딩할 필요 없음.
  - **AC**: AGENT.md가 OPAL 에이전트 규격을 따른다. model: advanced가 명시되어 있다. PLAN.md 작성 시 §4 실행 체크리스트에 agent 필드를 포함하도록 지시되어 있다. "PM이 전달한 전문 에이전트 매핑 테이블을 참조하여 agent를 배정한다"가 명시되어 있다. 매핑 테이블이 없으면 agent 필드를 생략한다(폴백: PM이 직접 판단).

- [ ] **R-4**: opal-test-agent AGENT.md 작성 (기존 op-dev-test-agent 강화)
  - **무엇을**: 기존 op-dev-test-agent를 opal-test-agent로 리네이밍하고, 도메인별 테스트 모드(BE mode, FE mode, E2E mode)를 지원하도록 강화한다. 해당 도메인 문서만 로딩한다.
  - **어디에**: `opal/agents/opal-test-agent/AGENT.md`
  - **왜**: 테스트도 도메인별로 전문화하여 적절한 검증 수행
  - **AC**: 3가지 모드(BE, FE, E2E)가 정의되어 있다. 모드별 로딩 문서가 구분되어 있다. 기존 op-dev-test-agent의 기능(TEST-SCENARIO.md 기반 동적 검증)이 유지된다.

- [ ] **R-5**: opal-planning-agent AGENT.md 작성
  - **무엇을**: 서비스 기획 전문 워커 에이전트 정의. 서비스 초기 기획부터 기획서(정책서, IA, 와이어프레임, WBS, API 분석 등) 작성/수정/관리를 수행한다. 문서는 MD 기본, 필요 시 엑셀 파일 가능. opwt(opal-pilot-write-tech) 파이프라인의 EXECUTE 단계에서 워커로 투입된다.
  - **어디에**: `opal/agents/opal-planning-agent/AGENT.md`
  - **왜**: 현재 opwt의 워커가 opal-task-agent(범용)인데, 기획 전문 에이전트로 교체하여 기획 산출물 품질 향상 + 기획 도메인 문서만 로딩하여 토큰 절감
  - **AC**: AGENT.md가 OPAL 에이전트 규격을 따른다. model: advanced가 명시되어 있다. 기획 산출물 유형(PRD, TRD, 정책서, IA, WBS, 외부 API 명세서, 기능도, 순서도)이 나열되어 있다. 자체 로드 문서(기획 산출물, 와이어프레임 등 외부 참조)가 명시되어 있다. MD 기본 + 엑셀 가능이 명시되어 있다. opal-doc-standard 참조가 포함되어 있다.

- [ ] **R-6**: opal-db-agent AGENT.md 작성
  - **무엇을**: DB 모델 설계+구현 전문 워커 에이전트 정의. 서비스 기획서를 참고하여 데이터 모델링(개념, 논리, 물리)을 작성/수정/관리하고, 마이그레이션 코드를 구현한다. 문서는 MD 기본, DBML 지원, 표준사전은 엑셀로 참조. PLAN 단계에서 DB 설계, EXECUTE 단계에서 마이그레이션 구현을 모두 담당한다.
  - **어디에**: `opal/agents/opal-db-agent/AGENT.md`
  - **왜**: DB 모델링은 BE와 밀접하지만 별도 전문성이 필요(정규화, 인덱스 설계, 표준사전 준수). 설계+구현을 같은 에이전트가 담당하여 일관성 보장.
  - **AC**: AGENT.md가 OPAL 에이전트 규격을 따른다. 3단계 모델링(개념/논리/물리)이 명시되어 있다. DBML 출력 지원이 명시되어 있다. 표준사전 참조 방법(엑셀 Read)이 명시되어 있다. 자체 로드 문서(DB 설계 문서, 표준사전)가 명시되어 있다. PLAN(설계)과 EXECUTE(마이그레이션 구현) 양 단계에서 투입 가능함이 명시되어 있다.

### 2. PLAN.md 에이전트 라우팅 + docs/ 갱신 Step

- [ ] **R-7**: op-dev-plan SKILL.md에 agent 필드 추가 (기존 R-5)
  - **무엇을**: PLAN.md §4.2 실행 체크리스트의 각 Step에 `**agent**` 필드를 추가하는 규칙을 op-dev-plan/SKILL.md에 명시한다. 영역 태그(FE/BE/DB/공통)를 기반으로 agent를 자동 매핑하는 기준도 포함한다.
  - **어디에**: `opal/skills/op-dev-plan/SKILL.md` — 실행 체크리스트 작성 규칙
  - **왜**: PM이 EXECUTE 단계에서 에이전트를 자동 선택할 수 있도록 PLAN에서 사전 배정
  - **AC**: PLAN.md §4.2 Step 템플릿에 `**agent**` 필드가 포함되어 있다. 영역 → agent 매핑 테이블(FE → opal-fe-agent, BE → opal-be-agent, 공통/환경/배치 → opal-task-agent)이 명시되어 있다.

- [ ] **R-8**: op-dev-plan SKILL.md에 docs/ 갱신 Step 자동 생성 규칙 추가 (기존 R-6)
  - **무엇을**: PLAN.md §4.2 실행 체크리스트 작성 시, 코드 변경이 docs/ 문서 내용에 영향을 미치는 경우 docs/ 갱신 Step을 자동으로 추가하는 규칙을 정의한다. 영역: 문서, agent: PM 직접.
  - **어디에**: `opal/skills/op-dev-plan/SKILL.md` — 실행 체크리스트 작성 규칙
  - **왜**: EXECUTE 후 docs/ 문서가 코드와 불일치하는 빈 구간을 해소. 전문 에이전트 체계의 전제 조건(docs/ 정확도)을 보장
  - **AC**: 실행 체크리스트에 docs/ 갱신 Step 자동 추가 규칙이 정의되어 있다. Step 영역이 "문서"이고 agent가 "PM 직접"으로 표기된다. 갱신 대상 docs/ 파일(BACKEND.md, FRONTEND.md, ARCHITECTURE.md, CONVENTIONS.md)이 변경 내용에 따라 식별된다.

### 3. PM 디스패치 프로세스 변경

- [ ] **R-9**: opal-pm.md §3 에이전트 선택 + 실행 라우팅 + 컨텍스트 슬라이싱 (기존 R-7)
  - **무엇을**: 디스패치 전 프로세스(§3)에 전문 에이전트 체계를 반영한다. (1) **Step 0. 에이전트 선택** — agents.md의 전문 에이전트 매핑 테이블을 Read하여 현재 단계+영역에 맞는 에이전트를 선택한다. 전문 에이전트가 없으면 기존 opal-task-agent로 폴백. (2) **Step 6. 실행 라우팅** — PLAN.md §4의 agent 필드를 참조하여 에이전트별 배치(Batch)를 구성한다. (3) **Step 7. 컨텍스트 슬라이싱** — 에이전트별로 필요한 컨텍스트(PLAN.md §3 해당 F-NNN, 도메인 문서, TEST-SCENARIO 해당 TS-ID, 선행 Batch changed_files)만 추출한다. PLAN 에이전트 디스패치 시에는 agents.md의 전문 에이전트 매핑 테이블을 함께 주입하여 agent 배정을 위임한다.
  - **어디에**: `opal/core/references/opal-pm.md` — §3 디스패치 전 프로세스
  - **왜**: PM의 디스패치 방식을 "전체 문서 주입"에서 "agents.md 기반 에이전트 선택 + 에이전트별 슬라이싱 주입"으로 전환. agents.md를 SSOT로 활용하여 에이전트 추가/변경 시 agents.md만 갱신하면 됨.
  - **AC**: §3에 Step 0(에이전트 선택: agents.md 매핑 테이블 조회 → 에이전트 결정 → 폴백 규칙)이 정의되어 있다. §3에 Step 6(실행 라우팅: agent 필드→Batch 구성, 병렬/순차 판별)이 정의되어 있다. §3에 Step 7(컨텍스트 슬라이싱: 에이전트별 필요 컨텍스트 추출)이 정의되어 있다. 폴백 규칙 3단계가 명시되어 있다: (1) agents.md에 전문 에이전트 섹션 없음 → 기존 방식, (2) 매핑 테이블에 해당 단계/영역 없음 → 해당 단계는 기존 방식, (3) 매핑 있음 → 전문 에이전트 사용.

- [ ] **R-10**: opal-pm.md §4 검토 게이트 항목 추가 (영역 침범 + 인터페이스 정합성) (기존 R-8)
  - **무엇을**: PM Gate 검토 절차에 다음 항목을 추가한다: (1) FE 에이전트가 BE 파일을 수정하지 않았는가, (2) BE 에이전트가 FE 파일을 수정하지 않았는가, (3) 공통 영역 변경 시 양쪽에 영향 분석이 되었는가, (4) Batch 간 인터페이스 정합성 (BE API ↔ FE 호출 일치).
  - **어디에**: `opal/core/references/opal-pm.md` — §4 PM 검토 게이트
  - **왜**: 전문 에이전트 체계에서 도메인 간 영역 침범과 인터페이스 불일치를 PM이 검증해야 함
  - **AC**: PM Gate 검토 절차에 4개 항목이 추가되어 있다. Fail 시 해당 전문 에이전트에 재지시하는 규칙이 명시되어 있다.

- [ ] **R-11**: opal-pm.md §6 참조 문서 전달 의무 변경 (에이전트별 문서 매핑) (기존 R-9)
  - **무엇을**: 현재 "전체 문서를 워커에게 전달"을 "에이전트별 문서 매핑 테이블에 따라 전달"로 변경한다.
  - **어디에**: `opal/core/references/opal-pm.md` — §6 참조 문서 전달 의무
  - **왜**: 에이전트별로 필요한 문서만 전달하여 토큰 절감
  - **AC**: 에이전트별 문서 매핑 테이블(opal-plan-agent, opal-fe-agent, opal-be-agent, opal-test-agent)이 §6에 포함되어 있다. 기존 범용 방식(opal-task-agent 사용 시)도 유지된다.

- [ ] **R-12**: opal-pm.md §10 통합 조율 신규 섹션 (기존 R-10)
  - **무엇을**: 전문 에이전트 체계에서 PM이 새로 담당해야 할 역할을 정의한다: (1) 인터페이스 계약 관리 — BE가 만든 API 스펙 → FE에 전달, 공통 타입 정의 → 양쪽에 동기화, (2) Batch 간 핸드오프 — Batch N 완료 → changed_files 수집 → Batch N+1에 주입, 선행 Batch 실패 → 후속 Batch 중단 판단, (3) 충돌 해소 — 동일 파일을 FE/BE 양쪽에서 수정해야 할 때 → 순차로 전환, 공통 영역 변경 시 → 먼저 실행한 에이전트 결과를 후속에 반영.
  - **어디에**: `opal/core/references/opal-pm.md` — §10 통합 조율 (신규)
  - **왜**: 전문 에이전트끼리 실시간 통신이 불가능하므로 PM이 중간 조율자 역할을 수행해야 함
  - **AC**: §10에 3가지 역할(인터페이스 계약 관리, Batch 간 핸드오프, 충돌 해소)이 정의되어 있다. 각 역할의 절차가 구체적으로 명시되어 있다.

- [ ] **R-13**: opal-pm.md §4 PM Gate에 docs/ 무효화 체크 항목 추가 (기존 R-11)
  - **무엇을**: PM Gate 검토 시 "EXECUTE의 changed_files가 docs/ 문서의 내용을 무효화하지 않는가"를 확인하는 항목을 추가한다. 새 API 추가 → BACKEND.md 갱신 필요?, 새 컴포넌트 추가 → FRONTEND.md 갱신 필요?, 구조 변경 → ARCHITECTURE.md 갱신 필요?, 새 패턴 도입 → CONVENTIONS.md 갱신 필요?
  - **어디에**: `opal/core/references/opal-pm.md` — §4 PM 검토 게이트
  - **왜**: docs/ 갱신 빈 구간을 PM Gate에서 최종 확인하여 누락 방지
  - **AC**: PM Gate에 docs/ 무효화 체크 항목이 추가되어 있다. 갱신 필요 시 PM이 직접 갱신하거나 opi 최신화를 제안하는 절차가 명시되어 있다.

### 4. 스킬/레퍼런스 변경

- [ ] **R-14**: 관련 스킬 SKILL.md에서 에이전트 참조 갱신 (기존 R-12)
  - **무엇을**: opal-task-agent를 참조하는 스킬(op-dev-execute, op-dev-analysis, op-dev-plan, op-dev-test-scenario)에서 전문 에이전트 사용 안내를 추가한다. "PM이 agents.md 매핑 테이블 또는 PLAN.md agent 필드에 따라 적합한 에이전트를 선택한다"로 갱신. 기존 opal-task-agent 참조는 폴백으로 유지.
  - **어디에**: 해당 스킬 SKILL.md의 실행 주체 섹션
  - **왜**: 전문 에이전트 체계 도입을 스킬 레벨에서도 반영. pilot SKILL.md에 에이전트 선택 로직을 넣지 않고, "PM이 선택한다"만 안내하여 관심사 분리 유지.
  - **AC**: 각 스킬 SKILL.md의 실행 주체에 "전문 에이전트 또는 opal-task-agent (폴백)"이 명시되어 있다. 기존 동작(opal-task-agent)이 폴백으로 유지된다. pilot SKILL.md에 에이전트 선택 로직이 포함되지 않는다.

- [ ] **R-15**: agents.md 레지스트리에 전문 에이전트 등록 + 매핑 테이블 + 에이전트 추가 가이드 (기존 R-13)
  - **무엇을**: `opal/core/references/agents.md`에 다음을 추가한다: (1) "전문 에이전트 (Specialist)" 섹션 — 4종 에이전트의 상세 정보(역할, 호출 시점, 단계, 영역, 자체 로드 문서, 금지 규칙). (2) 전문 에이전트 매핑 테이블 — PM과 opal-plan-agent가 단계+영역으로 에이전트를 선택하는 SSOT. (3) 에이전트 추가 가이드 — 신규 에이전트 추가 시 절차(프레임워크 레벨 / 프로젝트 레벨). (4) 폴백 규칙 — 매핑에 없는 단계/영역은 opal-task-agent 사용. (5) 프로젝트별 에이전트 오버라이드 — 탐색 경로 우선순위(`{프로젝트}/.opal/agents/` → `~/.opal/agents/`)로 프로젝트 전용 에이전트 지원.
  - **어디에**: `opal/core/references/agents.md`
  - **왜**: agents.md를 전문 에이전트 매핑의 SSOT로 활용. 기존 skills.md/tools.md/mcps.md와 동일한 레지스트리 패턴. 에이전트 추가/변경 시 agents.md만 갱신하면 PM과 opal-plan-agent가 자동으로 새 에이전트를 인식.
  - **AC**: "전문 에이전트 (Specialist)" 섹션이 존재한다. 매핑 테이블이 아래 형식으로 포함되어 있다. 에이전트 추가 가이드(프레임워크/프로젝트 레벨)가 포함되어 있다. 폴백 규칙 3단계가 명시되어 있다. 기존 "opal-pilot 에이전트" 섹션과 공존한다.

  매핑 테이블 형식:
  ```markdown
  ## 전문 에이전트 매핑 테이블

  | 에이전트 | 단계 | 영역 | model | 자체 로드 문서 |
  |----------|------|------|-------|--------------|
  | opal-plan-agent | PLAN | 공통 | advanced | 전체 docs/ |
  | opal-fe-agent | EXECUTE | FE | standard | FRONTEND.md, CONVENTIONS.md (FE) |
  | opal-be-agent | EXECUTE | BE | standard | BACKEND.md, BE-FRAMEWORK.md, CONVENTIONS.md (BE) |
  | opal-test-agent | TEST | 공통 | standard | ARCHITECTURE.md (테스트 섹션) |
  ```

  에이전트 추가 절차:
  ```
  프레임워크 에이전트 추가:
    1. opal/agents/{agent-name}/AGENT.md 작성
    2. agents.md "전문 에이전트" 섹션 + 매핑 테이블에 등록
    3. install-mac.sh로 배포

  프로젝트 전용 에이전트 추가:
    1. {프로젝트}/.opal/agents/{agent-name}/AGENT.md 작성
    2. 매핑은 PM이 프로젝트 컨텍스트에서 판단
       (프로젝트 agents.md가 있으면 참조, 없으면 PM 재량)
    3. 탐색 경로 우선순위로 자동 발견
  ```

  폴백 규칙:
  ```
  1. agents.md에 전문 에이전트 섹션 없음 → 기존 방식 (opal-task-agent)
  2. 매핑 테이블에 해당 단계/영역 없음 → 해당 단계는 기존 방식
  3. 매핑 있음 → 전문 에이전트 사용
  ```

### 5. 에이전트 디렉토리 이동

- [ ] **R-16**: OPAL 전용 에이전트를 agents/ → opal/agents/로 이동 (기존 R-14)
  - **무엇을**: OPAL 전용 에이전트(op-dev-test-agent, opal-task-action-agent, opal-task-agent, opal-task-qa-agent)를 `agents/`에서 `opal/agents/`로 이동한다. 범용 에이전트(wtm-agent)는 `agents/`에 유지한다. opal-sdd-action-agent는 이미 `opal/agents/`에 있으므로 그대로 둔다. 에이전트 경로를 참조하는 곳(agents.md, install-mac.sh 등)도 함께 갱신한다.
  - **어디에**: `agents/` → `opal/agents/`, 관련 참조 문서
  - **왜**: OPAL 전용 에이전트와 범용 에이전트의 디렉토리 구조를 명확히 분리. opal-sdd-action-agent만 opal/agents/에 있던 불일치 해소
  - **AC**: 4개 에이전트가 opal/agents/로 이동되어 있다. wtm-agent는 agents/에 유지된다. agents.md와 install-mac.sh의 경로 참조가 갱신되어 있다. CONVENTIONS.md의 에이전트 경로 규칙이 갱신되어 있다.

## 제약 조건

- 기존 범용 에이전트(opal-task-agent, opal-task-qa-agent 등)는 삭제하지 않는다 — 폴백으로 유지
- 기존 pilot SKILL.md의 파이프라인 구조(단계 정의, Gate 순서)는 변경하지 않는다
- 전문 에이전트의 AGENT.md는 기존 OPAL 에이전트 규격(frontmatter + 본문)을 따른다
- `~/.opal/` 직접 수정 금지 — 소스 경로(`opal/`)에서만 수정 후 install로 배포
- 전문 에이전트가 pilot의 단계 스킬(op-dev-plan, op-dev-execute 등)을 대체하는 것이 아니다 — 전문 에이전트가 단계 스킬을 "더 잘 실행"하는 것이다

## 기술 스택

- Markdown 문서 작업 (에이전트 AGENT.md, 스킬 SKILL.md, 레퍼런스 .md)
- YAML frontmatter (에이전트 규격)

## 관련 문서

- `opal/core/references/agents.md` — 에이전트 레지스트리
- `opal/core/references/opal-pm.md` — PM 행동 프로세스 (§3 디스패치 전 프로세스)
- `opal/core/references/opal-harness.md` — 하네스 공통
- `opal/core/references/opal-harness-interactive.md` — PM Gate 절차
- `opal/core/references/opal-model-mapping.md` — 모델 매핑
- `opal/agents/opal-task-agent/AGENT.md` — 범용 워커 (폴백 대상)
- `opal/agents/opal-task-qa-agent/AGENT.md` — 범용 QA 워커 (폴백 대상)
- `opal/agents/op-dev-test-agent/AGENT.md` — 테스트 워커 (강화 대상)
- `opal/skills/op-dev-plan/SKILL.md` — PLAN 스킬 (R-7, R-8)
- `opal/skills/op-dev-execute/SKILL.md` — EXECUTE 스킬 (R-14)
- `opal/skills/op-dev-execute/personas/frontend-engineer.md` — FE 페르소나 (R-1 흡수 대상)
- `opal/skills/op-dev-execute/personas/backend-engineer.md` — BE 페르소나 (R-2 흡수 대상)
- `opal/skills/opal-pilot-write-tech/SKILL.md` — 기획 산출물 오케스트레이터 (R-5 opal-planning-agent 투입 대상)
- `opal/core/references/harness/parallel-execution.md` — 기존 하네스 §7 병렬 처리 원칙

## 구현 우선순위 제안

| 순위 | 작업 | 요구사항 | 이유 |
|------|------|---------|------|
| 1 | opal-fe-agent + opal-be-agent 분리 | R-1, R-2 | 즉시 토큰 절감 + 품질 향상, mams에서 바로 체감 |
| 2 | opal-planning-agent + opal-db-agent 추가 | R-5, R-6 | 기획/DB 도메인 전문화 |
| 3 | PLAN.md에 agent/영역 기반 라우팅 | R-7, R-8 | PM 디스패치 자동화의 기반 |
| 4 | PM 컨텍스트 슬라이싱 로직 | R-9, R-10, R-11 | 토큰 효율 극대화 |
| 5 | opal-plan-agent 분리 | R-3 | PLAN 품질 안정화 |
| 6 | opal-test-agent 강화 | R-4 | 도메인별 테스트 전략 분리 |
| 7 | PM 통합 조율 + docs/ 갱신 | R-12, R-13 | 전문 에이전트 체계 전제 조건 |
| 8 | 스킬/레퍼런스 갱신 | R-14, R-15 | 일관성 보장 |
| 9 | 에이전트 디렉토리 이동 | R-16 | 구조 정리 |
