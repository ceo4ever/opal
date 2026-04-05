---
name: op-sdd-spec
description: |
  **SDD 명세 작성 단계 스킬**. TASK.md와 프로젝트 컨텍스트를 분석하여 10섹션 표준 구조의 spec.md를 작성한다.
  반드시 이 스킬을 사용해야 하는 상황: 오케스트레이터(opal-pilot-sdd)가 SPEC 단계를 디스패치할 때.
  필수 입력: TASK.md. 선택 입력: docs/PROJECT.md, docs/ARCHITECTURE.md, 코드베이스. 보장 출력: specs/{NNN}-{feature}/spec.md.
---

# op-sdd-spec -- SDD 명세 작성

## 실행 컨텍스트

- **호출자**: 오케스트레이터(opal-pilot-sdd)가 SPEC 단계를 디스패치
- **실행 주체**: 워커 에이전트 (opal-task-agent)
- **model**: advanced
- **입력**: `tasks/{NNN}-{태스크명}/TASK.md`
- **출력**: `specs/{NNN}-{feature}/spec.md`

서브 에이전트 사용이 불가능한 플랫폼에서는 오케스트레이터가 직접 이 스킬을 따른다.

---

## 페르소나

```
Read ~/.opal/skills/op-sdd-spec/personas/spec-writer.md
```

페르소나 파일이 없으면 다음 역할을 따른다:
- SDD 명세 작성 전문가
- WHAT(무엇을 할 것인가)에 집중하고, HOW(어떻게 구현할 것인가)는 배제한다
- 10섹션 표준 구조를 빠짐없이 작성하되, 각 섹션의 품질을 보장한다
- 모호한 표현을 제거하고 검증 가능한 명세를 작성한다

---

## 입력/출력

| 항목 | 설명 |
|------|------|
| **필수 입력** | TASK.md |
| **선택 입력** | docs/PROJECT.md, docs/ARCHITECTURE.md, docs/CONVENTIONS.md, 코드베이스 |
| **보장 출력** | specs/{NNN}-{feature}/spec.md |

### 입력 상세

| 입력 | 용도 | 없을 때 |
|------|------|---------|
| TASK.md | 요구사항의 원천 -- FR/NFR/AC 도출의 기반 | 진행 불가 (필수) |
| docs/PROJECT.md | 프로젝트 정의, 도메인 용어, 기술 스택 파악 | TASK.md만으로 진행 |
| docs/ARCHITECTURE.md | 기존 시스템 구조, 컴포넌트 관계 파악 | 코드 직접 분석 |
| docs/CONVENTIONS.md | 네이밍/코드 컨벤션, 도메인 용어 | 기존 코드에서 추론 |
| 코드베이스 | 기존 구현 패턴, 관련 모듈 파악 | 문서만으로 진행 |

---

## 프로세스

### Step 1: 프로젝트 컨텍스트 로딩

프로젝트의 기존 구조와 맥락을 파악한다.

1. `docs/PROJECT.md`를 Read한다 (없으면 스킵)
2. `docs/ARCHITECTURE.md`를 Read한다 (없으면 스킵)
3. `docs/CONVENTIONS.md`를 Read한다 (없으면 스킵)
4. `specs/` 디렉토리에 기존 spec이 있으면 Glob으로 확인하고, 최근 spec 1~2개를 Read하여 형식과 수준을 참조한다

### Step 2: TASK.md 분석

TASK.md를 정밀하게 분석한다.

1. TASK.md를 Read한다
2. 요구사항을 기능 요구사항(FR)과 비기능 요구사항(NFR)으로 분류한다
3. 암묵적 요구사항을 식별한다 -- TASK.md에 명시되지 않았지만 기능상 필요한 것
4. 범위 판별: 단일 응집 기능인지, 분할이 필요한 복합 기능인지 판단한다

**범위 과도 시 분할 제안**:
- TASK.md의 요구사항이 3개 이상의 독립적 기능을 포함하면 분할을 제안한다
- 분할 제안 형식: `[SCOPE-SPLIT] {기능A}, {기능B}, {기능C}로 분할을 제안합니다. 계속 진행할까요?`
- 오케스트레이터(또는 소유자)의 승인 없이는 분할하지 않고 하나의 spec으로 작성한다

### Step 3: 코드베이스 분석

관련 기존 코드를 실제로 읽고 분석한다. **추측 금지**.

1. Glob/Grep으로 TASK.md 요구사항과 관련된 기존 코드를 탐색한다
2. 관련 파일의 핵심 구조(함수 시그니처, 클래스 구조, 데이터 모델)를 파악한다
3. 기존 패턴과 컨벤션을 식별한다 -- spec 작성 시 이를 존중한다
4. 기존 시스템과의 통합 포인트를 식별한다

### Step 4: spec.md 10섹션 작성

아래 출력 형식에 따라 10섹션을 모두 작성한다. 각 섹션별 작성 지침:

#### 4-1. Background (배경)
- 비즈니스 맥락과 필요성을 기술한다
- TASK.md의 배경 정보를 기반으로 하되, 프로젝트 컨텍스트를 반영하여 보강한다

#### 4-2. Goals (목표)
- 이 기능이 달성해야 할 것을 명확히 나열한다
- 검증 가능한 목표를 우선한다

#### 4-3. Non-goals (비목표)
- 명시적으로 범위 밖인 것을 정의한다
- "이번에 하지 않는 것"을 분명히 하여 범위 크리프를 방지한다

#### 4-4. User Stories (사용자 스토리)
- `As a {역할}, I want {기능}, so that {가치}` 형식으로 작성한다
- 주요 사용자 유형별로 최소 1개 이상 작성한다

#### 4-5. Functional Requirements (기능 요구사항)
- `[FR-NN]` ID를 부여한다 (01부터 순차)
- 각 FR은 하나의 검증 가능한 요구사항을 기술한다
- TASK.md의 모든 요구사항이 FR로 매핑되어야 한다

#### 4-6. Acceptance Criteria (수용 기준)
- `[AC-NN]` ID를 부여한다 (01부터 순차)
- 반드시 **GIVEN/WHEN/THEN** 형식으로 작성한다
- **최소 3개** 이상 작성한다
- 모든 FR에 대응하는 AC가 1개 이상 있어야 한다 (FR-AC 양방향 추적성)
- AC 상단에 대응하는 FR ID를 명시한다

#### 4-7. Edge Cases (엣지 케이스)
- `[EC-NN]` ID를 부여한다 (01부터 순차)
- 예외 상황과 기대 동작을 기술한다
- 정상 경로만 기술된 spec은 불완전하다 -- 적극적으로 엣지 케이스를 도출한다

#### 4-8. Non-functional Requirements (비기능 요구사항)
- `[NFR-NN]` ID를 부여한다 (01부터 순차)
- 성능, 보안, 접근성, 확장성 등을 고려한다
- 생략하지 않는다

#### 4-9. Constraints (제약)
- 기술적 제약 (프레임워크, 언어, 호환성 등)
- 정책적 제약 (보안 정책, 라이선스 등)
- 프로젝트 컨텍스트에서 도출된 제약

#### 4-10. Open Questions (미결 사항)
- spec 작성 과정에서 발생한 미해결 질문을 기록한다
- **"없음"이 SPEC-VERIFY 진행 조건** -- 해소할 수 있는 OQ는 Step 5에서 해소한다
- 해소 불가능한 OQ는 오케스트레이터에 보고하여 소유자 판단을 구한다

### Step 5: Open Questions 해소

1. Step 4에서 기록한 OQ를 검토한다
2. 코드베이스, 문서, 프로젝트 컨텍스트에서 답을 찾을 수 있는 OQ는 해소한다
3. 해소된 OQ는 해당 섹션 내용에 반영하고 OQ 목록에서 제거한다
4. 해소 불가능한 OQ가 남아있으면 `[OQ-UNRESOLVED]` 태그와 함께 반환한다

### Step 6: 자체 검증

아래 품질 체크리스트를 자체 수행한다. 미달 항목이 있으면 수정 후 다시 검증한다.

### Step 7: spec.md 저장

1. `specs/{NNN}-{feature}/` 디렉토리를 생성한다 ({NNN}은 TASK.md의 태스크 번호, {feature}는 기능명 kebab-case)
2. spec.md를 저장한다
3. 기존 spec.md가 있으면 버전 관리 규칙에 따라 처리한다

### Step 8: 결과 반환

워커는 QA를 직접 호출하지 않는다. spec.md 작성이 완료되면 결과를 오케스트레이터에 반환한다. 오케스트레이터가 QA 단계 실행 여부를 결정한다.

**반환 형식**:
```
SPEC 완료: specs/{NNN}-{feature}/spec.md
- 10섹션 완비: {Yes/No}
- AC 수: {N}개
- OQ 상태: {없음 / N개 미해소}
- 범위 분할 제안: {없음 / 제안 내용}
```

**OQ 미해소 시 반환 형식**:
```
[OQ-UNRESOLVED] SPEC 작성 완료, 미해소 OQ {N}개:
- OQ-01: {질문}
- OQ-02: {질문}
소유자 판단 필요. SPEC-VERIFY 진행 불가.
```

---

## spec.md 출력 형식

```markdown
# SPEC: {기능명}

> 버전: 1.0 | 작성일: YYYY-MM-DD | 상태: Draft
> TASK: tasks/{NNN}-{태스크명}/TASK.md

## 1. Background (배경)

{왜 이 기능이 필요한지 -- 비즈니스 맥락}

## 2. Goals (목표)

- {목표 1}
- {목표 2}

## 3. Non-goals (비목표)

- {비목표 1 -- 왜 범위 밖인지 간략 설명}
- {비목표 2}

## 4. User Stories (사용자 스토리)

- As a {역할}, I want {기능}, so that {가치}
- As a {역할}, I want {기능}, so that {가치}

## 5. Functional Requirements (기능 요구사항)

- [FR-01] {기능 요구사항}
- [FR-02] {기능 요구사항}

## 6. Acceptance Criteria (수용 기준)

### AC-01: {시나리오명}
> 대응 FR: FR-01

- **GIVEN**: {사전 조건}
- **WHEN**: {행위}
- **THEN**: {기대 결과}

### AC-02: {시나리오명}
> 대응 FR: FR-01, FR-02

- **GIVEN**: {사전 조건}
- **WHEN**: {행위}
- **THEN**: {기대 결과}

### AC-03: {시나리오명}
> 대응 FR: FR-02

- **GIVEN**: {사전 조건}
- **WHEN**: {행위}
- **THEN**: {기대 결과}

## 7. Edge Cases (엣지 케이스)

- [EC-01] {예외 상황} -- {기대 동작}
- [EC-02] {예외 상황} -- {기대 동작}

## 8. Non-functional Requirements (비기능 요구사항)

- [NFR-01] {성능/보안/접근성 등}
- [NFR-02] {성능/보안/접근성 등}

## 9. Constraints (제약)

- {기술적/정책적 제약}

## 10. Open Questions (미결 사항)

- 없음
```

---

## 활용 MCP

| MCP | 용도 | 사용 시점 |
|-----|------|----------|
| context7 | `resolve-library-id` + `get-library-docs` | 외부 라이브러리 API 사양 확인 시 |
| WebSearch | 공식 문서/릴리스 노트 검색 | context7에 없는 라이브러리, 도메인 지식 보강 시 |

---

## 저장 경로

```
specs/{NNN}-{feature}/spec.md
```

- `{NNN}`: TASK.md의 태스크 번호 (3자리 zero-padded)
- `{feature}`: 기능명 kebab-case
- 기존 spec.md가 있으면 opal-doc-standard 규칙에 따라 버전 관리한다

---

## 품질 체크리스트

spec.md 작성 후 자체 검증한다:

- [ ] 10섹션이 모두 존재하는가
- [ ] AC가 모두 GIVEN/WHEN/THEN 형식인가
- [ ] AC가 최소 3개 이상인가
- [ ] 모든 FR에 대응하는 AC가 1개 이상 있는가 (FR-AC 추적성)
- [ ] Open Questions가 "없음"인가 (미해소 시 [OQ-UNRESOLVED] 반환)
- [ ] Non-goals가 명시적으로 정의되어 있는가
- [ ] Edge Cases가 도출되어 있는가 (정상 경로만 있는 spec은 불완전)
- [ ] NFR이 생략되지 않았는가 (성능/보안/접근성 등)
- [ ] 구현 방법(HOW)이 아닌 요구사항(WHAT)을 기술하고 있는가
- [ ] 프로젝트 도메인 용어와 컨벤션을 따르는가
- [ ] TASK.md의 모든 요구사항이 FR로 매핑되었는가
- [ ] 기능 범위가 단일 응집 단위인가 (과도하면 분할 제안)
- [ ] 기존 시스템과의 통합 포인트가 Constraints에 반영되었는가

---

## 완료 후 동작

워커는 QA를 직접 호출하지 않는다. spec.md 작성이 완료되면 결과를 오케스트레이터에 반환한다. 오케스트레이터가 QA 단계 실행 여부를 결정한다.

**반환 형식**:
```
SPEC 완료: specs/{NNN}-{feature}/spec.md
```

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-04-05 | 초기 작성 -- PLAN D5/D13 기반, 10섹션 표준 구조 + GIVEN/WHEN/THEN AC + OQ 해소 프로세스 |
