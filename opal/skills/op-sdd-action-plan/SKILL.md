---
name: op-sdd-action-plan
description: |
  **SDD ACT 전용 경량 PLAN 스킬**. SPEC.md + SPEC-PLAN.md + TEST-SCENARIOS.md + ACT 정의를 기반으로
  ACT 범위의 실행 가능한 구현 청사진을 작성한다.
  plan-guide.md / personas / community-skills 로딩 없음 — SDD 컨텍스트로 대체.
  반드시 이 스킬을 사용해야 하는 상황: opal-sdd-action-agent가 ACT PLAN 단계를 디스패치할 때.
  필수 입력: SPEC.md, SPEC-PLAN.md, TEST-SCENARIOS.md, ACT 정의. 보장 출력: PLAN.md.
version: 1.0.0
---

# SDD ACT 구현 계획 수립 (PLAN)

## 실행 컨텍스트

이 스킬은 워커 에이전트의 컨텍스트에서 실행된다.
opal-sdd-action-agent가 워커를 디스패치하면, 워커가 이 스킬을 읽고 프로세스를 따른다.

> **[MUST]** 산출물 작성·검증 시 `opal/core/references/harness/citation-rules.md`를 Read하여 규칙(근거 제시 원칙 / 트랙별 매트릭스 / [MUST] 토큰 / 영역 간 용어 일관성 / decision_required 계약)을 준수한다.

---

## op-dev-plan과의 차이

| 항목 | op-dev-plan | op-sdd-action-plan |
|------|------------|-------------------|
| 목적 | 범용 구현 계획 | SDD ACT 범위 경량 계획 |
| 입력 | TASK.md (+ ANALYSIS.md) | SPEC.md + SPEC-PLAN.md + TEST-SCENARIOS.md + ACT 정의 |
| 사전 로딩 | plan-guide.md + personas + community-skills | 없음 (SDD 컨텍스트로 대체) |
| 코드 분석 | Full ANALYSIS 수준 | ACT 범위 기준 경량 (Glob/Grep/Read) |
| 설계 재수행 | 전체 설계 | 없음 (SPEC-PLAN.md 아키텍처 준수) |
| 복잡도 판별 | 단순/복잡 모드 | 없음 (항상 direct 실행) |
| execution-plan.json | FE/BE 시 생성 | 생성하지 않음 |
| 산출물 | `tasks/{NNN}/PLAN.md` | `actions/ACT-{NNN}-{name}/PLAN.md` |

---

## 입력/출력

| 항목 | 설명 |
|------|------|
| **필수 입력** | SPEC.md, SPEC-PLAN.md, TEST-SCENARIOS.md, ACT 정의(ID, 이름, 범위, AC/TS 매핑) |
| **보장 출력** | PLAN.md |

### ACT 정의 (디스패치 프롬프트에서 주입)

| 파라미터 | 설명 |
|---------|------|
| act_id | ACT ID (예: `ACT-001-db-schema`) |
| act_goal | ACT 목표 |
| act_scope | ACT 범위 -- 변경 대상 파일/모듈 |
| ac_mapping | AC 목록 (예: AC-01, AC-03) |
| ts_mapping | TS 목록 (예: TS-01, TS-02) |

---

## 프로세스

### Step 1: SDD 컨텍스트 로딩

디스패치 프롬프트에서 전달받은 SDD 컨텍스트를 Read한다:

1. **SPEC.md** -- 기능 요구사항(FR), 비기능 요구사항(NFR), 제약조건 확인
2. **SPEC-PLAN.md** -- 아키텍처 결정, ACT 분해, 의존관계 확인
3. **TEST-SCENARIOS.md** -- 해당 ACT의 TS 매핑에서 테스트 시나리오 상세 확인

Read 시 해당 ACT에 관련된 정보를 중심으로 추출한다 (전체 문서를 요약하지 않음).

### Step 2: ACT 범위 코드 분석 (경량)

SPEC-PLAN.md의 ACT scope 기준으로 관련 코드를 분석한다.

- Glob/Grep/Read로 `act_scope`에 명시된 파일/모듈을 실제로 읽는다 (추측 금지)
- 기존 코드 구조, 핵심 로직 흐름 파악
- 관련 함수/클래스 시그니처와 역할
- 영향 범위 (ACT scope 내 호출자/피호출자)

**범위 제한**: ACT scope 밖의 코드는 의존 인터페이스만 확인한다 (전체 코드베이스 분석 없음).

### Step 3: 구현 범위 확정

- 신규 생성 파일 목록
- 수정 파일 목록
- 영향 확인 파일 목록 (ACT scope 밖이지만 인터페이스 호환 확인 필요)

### Step 4: 핵심 설계

SPEC-PLAN.md의 아키텍처 결정을 **준수**하며, ACT 단위의 구현 상세를 작성한다:

- 클래스/함수 시그니처 (SPEC-PLAN.md에서 정의된 인터페이스 준수)
- 데이터 모델 변경 (해당 시)
- 핵심 로직 흐름
- 외부 라이브러리/API 호출 방식

**금지**: SPEC-PLAN.md에서 확정된 아키텍처를 변경하는 설계. 불일치 발견 시 블로커로 보고한다.

### Step 5: 실행 체크리스트 작성

Step 형식으로 실행 체크리스트를 작성한다.

- 각 Step의 완료 기준에 AC/TS 매핑을 반영
- 모든 Step은 `direct` 실행 (서브 에이전트 없음)
- 의존관계 명시

### Step 6: QA 체크리스트 작성

기능/회귀/코드 품질 항목을 작성한다.

- AC 매핑의 각 AC가 커버되는지 확인 항목 포함
- TS 매핑의 각 TS가 실행 가능한지 확인 항목 포함

### Step 7: PLAN.md 작성

아래 출력 형식으로 PLAN.md를 `{ACT 폴더}/PLAN.md`에 작성한다.

---

## PLAN.md 출력 형식

```markdown
# PLAN: ACT-{NNN} {ACT명}

> 작성일: YYYY-MM-DD
> 입력: SPEC.md, SPEC-PLAN.md, TEST-SCENARIOS.md
> 출력: PLAN.md

## SDD 컨텍스트

| 항목 | 값 |
|------|---|
| ACT ID | {act_id} |
| ACT 목표 | {act_goal} |
| AC 매핑 | {ac_mapping} |
| TS 매핑 | {ts_mapping} |

## 1. 코드 분석

### 관련 파일
| 파일 | 역할 | 변경 필요 |
|------|------|----------|

### 현재 구현
{ACT scope 기준 핵심 로직 흐름, 함수/클래스 시그니처}

### 영향 범위
{ACT scope 내 호출자/피호출자, 외부 인터페이스}

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성
| # | 파일 경로 | 역할 |
|---|----------|------|

#### 수정
| # | 파일 경로 | 변경 내용 |
|---|----------|----------|

### 구현 순서
| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|

### 핵심 설계
{클래스/함수 시그니처, 데이터 모델, SPEC-PLAN.md 아키텍처 준수 사항}

### 테스트 전략
{TS 매핑 기반 테스트 종류, 성공 기준}

## 3. 실행 체크리스트

> 총 {N}개 Step

### Step 1: {작업 제목}
- [ ] 완료
- **파일**: {대상 파일 경로}
- **작업 내용**: {구체적 구현 내용}
- **완료 기준**: {검증 가능한 완료 조건 + AC/TS 매핑}
- **테스트**: {검증 명령어 또는 방법}
- **의존**: {선행 Step 번호 또는 "없음"}

## 4. QA 체크리스트

### 기능 테스트
- [ ] {항목 — AC 매핑 포함}

### 회귀 테스트
- [ ] {항목}

### 코드 품질
- [ ] {항목}

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
```

---

## 품질 체크리스트

- [ ] 이 PLAN만 보고 바로 코딩에 들어갈 수 있는가?
- [ ] 구현 순서의 의존성이 올바른가? (하위 레이어 먼저)
- [ ] SPEC-PLAN.md의 아키텍처 결정을 준수하는가?
- [ ] AC 매핑의 모든 AC가 실행 체크리스트에서 커버되는가?
- [ ] TS 매핑의 모든 TS가 테스트 전략에서 커버되는가?
- [ ] 관련 코드를 실제로 읽고 분석했는가? (추측 금지)
- [ ] ACT scope 밖의 코드를 불필요하게 변경하지 않는가?
- [ ] plan-guide.md / personas / community-skills를 로딩하지 않았는가?
- [ ] execution-plan.json을 생성하지 않았는가?
- [ ] 프로젝트 코드 컨벤션을 따르는가?

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-04-07 | 초기 작성 -- SDD ACT 전용 경량 PLAN 스킬 (095) |
| v1.1 | 2026-04-24 | citation-rules 트리거 1줄 주입 — SSOT + Trigger 패턴 (130) |
