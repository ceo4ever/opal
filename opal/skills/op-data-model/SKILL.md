---
name: op-data-model
description: |
  **DB 모델링 단계 스킬 (MODEL)**. 개념(Mermaid) / 논리(Mermaid) / 물리(DBML) 3모드를 분리 발동한다.
  반드시 이 스킬을 사용해야 하는 상황:
    - opal-pilot-data-design(opdd) 파이프라인의 MODEL 단계 — `opal-db-agent`가 디스패치받아 실행
    - 단독 호출: "ERD 만들어줘", "개념 모델링", "논리 모델링", "물리 모델링", "엔티티 설계"
    - `//erm` alias (erd-modeler 하위호환) 호출 시 → 이 스킬로 라우팅됨
  필수 입력: 기획서 또는 업무 컨텍스트 (TASK.md 또는 사용자 대화). 기존 ERD 주입 시 해당 모드부터 시작 가능.
  보장 출력: 발동 모드별 산출물 파일 (`{설계}/개념모델링/`, `논리모델링/`, `물리모델링/`).
version: 1.0
stage: MODEL
dispatched_by:
  - opal-pilot-data-design
---

# op-data-model — DB 모델링 단계 스킬

DB 설계 파이프라인의 MODEL 단계를 담당한다. 개념/논리/물리 3모드를 분리 발동하며, 각 모드는 독립적으로도 호출 가능하다.
산출물 경로는 `{설계}` 변수(PROJECT.md 등록 또는 인터뷰 확정)로 해소하며 하드코딩하지 않는다.

> **인용 의무** (`docs/proposals/opal-data-design.md` §3.2.1):
> - "논리는 개념, 물리는 논리 산출물을 입력으로 한다(증분). 기존 ERD가 인풋으로 주입되면 해당 모드부터 시작 가능."
> - 각 모드 산출물 양식은 이 스킬 `references/mermaid-guide.md`(개념/논리)·`op-data-ddl/references/dbml-guide.md`(물리)를 참조한다.

---

## 실행 컨텍스트

- **호출자**: `opal-pilot-data-design`(opdd) 파이프라인 MODEL 단계, 또는 단독 호출(`//erm` alias 포함)
- **실행 주체**: `opal-db-agent` (`docs/proposals/opal-data-design.md` §3.1 단일 에이전트 확정)
- **입력**:
  - `mode`: `concept` / `logical` / `physical` (pilot 파이프라인에서는 순차 3모드, 단독 호출 시 특정 모드)
  - 기획서·TASK.md·사용자 대화 (엔티티·관계 도출 근거)
  - `{설계}` 변수: PROJECT.md 등록 경로 또는 인터뷰 확정 경로
  - [선택] 기존 ERD 파일: 해당 모드부터 시작하는 증분 설계 베이스라인
  - [선택] DICT 사전 경로: 논리/물리 모드 속성명·타입 SSOT (`{설계}/사전/` 하위)
- **출력**: 발동 모드별 산출물 파일 (아래 §3모드 양식 참조)

---

## 페르소나

`opal/agents/opal-db-agent/personas/db-architect.md` — DB 설계 전문 페르소나 재사용.

---

## 3모드 분리 발동 + 산출물 양식

> 인용: `docs/proposals/opal-data-design.md` §3.2.1 MODEL 3모드 양식표

### 모드 선택 규칙

| 상황 | 발동 모드 |
|------|----------|
| pilot 파이프라인 MODEL 단계 (신규 트랙) | concept → logical → physical 순차 3모드 |
| 단독 호출, 모드 미지정 | 사용자에게 모드 확인 |
| 기존 개념 ERD 주입 | logical 모드부터 시작 |
| 기존 논리 ERD 주입 | physical 모드부터 시작 |
| 기존 DB/DDL 스키마 주입 (역공학) | physical(역추출·정규화) → logical(역산) — **concept 미실행** |
| `//erm` alias 단독 호출 | concept 모드 (기본) 또는 사용자 지정 모드 |

> 역공학 트랙의 물리 역추출 절차는 `op-data-ddl` §Step 4(`sql2dbml`)를 참조한다 — 산출물은 이 스킬 physical 모드 경로(`{설계}/물리모델링/{프로젝트}.dbml`)에 저장한다.

---

### 모드 1: concept (개념 모델링)

**발동**: `//opdd model --concept` 또는 op-data-model concept 단독 호출

**산출물 경로**:
```
{설계}/개념모델링/ERD_{영역}.mermaid
{설계}/개념모델링/ERD_{영역}.md
```

**핵심 규칙** (erd-modeler `SKILL.md:101-120` 계승):

- Mermaid `erDiagram` 사용 — `references/mermaid-guide.md §2` 참조
- 관계명: 한글 동사형 ("운영한다", "포함한다", "속한다")
- 카디널리티: 1:1, 1:N, M:N 모두 허용 (논리에서 M:N 해소)
- FK 속성: 표현하지 않음 (비즈니스 관점 전용)
- 엔티티명: 영문 대문자, 한글명 끝에 "정보" 필수 (`["회사 정보"]`)
- 속성: 작성하지 않음

**개념 ERD 예시**:
```mermaid
erDiagram
    %% ========================================
    %% 개념 ERD: SA{N} - {영역명}
    %% 프로젝트: {프로젝트명}
    %% 작성일: YYYY-MM-DD
    %% ========================================

    COMPANY["회사 정보"] ||--o{ BRAND["브랜드 정보"] : "운영한다"
    BRAND ||--o{ CAMPAIGN["캠페인 정보"] : "집행한다"
    CAMPAIGN ||--o{ ADGROUP["광고그룹 정보"] : "포함한다"
```

**완료 기준**: `.mermaid` + `.md` 파일 존재, 엔티티명 끝 "정보" 일관 적용, M:N 허용 포함

---

### 모드 2: logical (논리 모델링)

**발동**: `--logical` 또는 기존 개념 ERD 주입 시

**입력 전제**: 개념 ERD 산출물 (`{설계}/개념모델링/`) 존재 또는 주입
역공학 트랙 예외: 물리(DBML) 산출물을 입력으로 논리를 역산한다 (§모드 선택 규칙 참조).

**산출물 경로**:
```
{설계}/논리모델링/ERD_{영역}_논리.mermaid
{설계}/논리모델링/ERD_{영역}_논리.md
```

**핵심 규칙** (erd-modeler `SKILL.md:122-153` 계승):

- Mermaid `erDiagram` + 속성/PK/FK 상세화 — `references/mermaid-guide.md §3` 참조
- **속성명 = DICT 표준사전 용어** (`{설계}/사전/표준단어사전.md` 참조, 미등록 시 사전 먼저 등록)
  - 미등록 용어 발견 시: op-data-dictionary 스킬을 통해 사전 등록 후 속성명 확정
  - 사전 부재 시: `opal/skills/op-data-dictionary/references/naming-convention.md` 기본 규칙 폴백
- 엔티티명: 영문 대문자 + 유형 접미어 (CAMPAIGN_BSC, MEMBER_BSC)
- 타입: 도메인사전 기반 (bigint, varchar, decimal 등)
- 키: PK, FK, UK 명시
- 관계: 식별(`--`) / 비식별(`..`) 구분
- M:N: 매핑 엔티티로 해소 (예: BRAND_MEDIA_MAP)

**식별 vs 비식별 판단 기준**:
- 자식이 부모 없이 독립적으로 존재할 수 있는가? → Yes: 비식별, No: 식별
- 부모 PK가 자식의 정체성(PK)에 포함되는가? → Yes: 식별, No: 비식별
- 대부분의 마스터 테이블 간 관계는 비식별 (자체 ID로 식별)

**논리 ERD 예시**:
```mermaid
erDiagram
    CAMPAIGN_BSC["캠페인 기본 정보"] {
        bigint campaign_id PK "캠페인식별자"
        bigint company_id FK "회사식별자"
        bigint brand_id FK "브랜드식별자"
        varchar campaign_nm "캠페인명"
        varchar media_cd "매체코드"
        varchar campaign_state_cd "캠페인상태코드"
        datetime created_dt "생성일시"
    }

    COMPANY_BSC["회사 기본 정보"] ||..o{ CAMPAIGN_BSC : "집행한다"
    BRAND_BSC["브랜드 기본 정보"] ||..o{ CAMPAIGN_BSC : "소속된다"
```

**완료 기준**: `.mermaid` + `.md` 파일 존재, 모든 속성명이 DICT 용어, M:N 해소 완료, FK 키 표시

---

### 모드 3: physical (물리 모델링)

**발동**: `--physical` 또는 기존 논리 ERD 주입 시

**입력 전제**: 논리 ERD 산출물 (`{설계}/논리모델링/`) 존재 또는 주입
역공학 트랙 예외: 기존 DDL·ORM·DB 스키마를 입력으로 하며 논리 ERD 선행을 요구하지 않는다 (§모드 선택 규칙 참조).

**산출물 경로**:
```
{설계}/물리모델링/{프로젝트}.dbml
```

**핵심 규칙** (erd-modeler `SKILL.md:155-191` 계승):

- DBML 형식 — `op-data-ddl/references/dbml-guide.md` 참조
- 엔티티명 → 물리 테이블명 변환 (명명규칙 적용): `{스키마}_{주제영역}_{엔티티}_{유형}`
- 속성 → 컬럼 변환 (도메인사전에서 해당 DBMS의 타입/길이 매핑)
  - `opal/skills/op-data-dictionary/references/db-type-mapping.md` 참조
- 관계 → FK 제약조건 + 인덱스 생성
- 오딧 컬럼 필수: `created_dt DATETIME`, `updated_dt DATETIME` (+ `created_by`, `updated_by` 선택)
- 프로젝트 명명규칙 우선; 없으면 이 스킬 기본 명명규칙 적용

**명명규칙** (기본):

| 구성요소 | 패턴 | 예시 |
|---------|------|------|
| 테이블명 | `{스키마}_{주제}_{엔티티}_{유형}` | `prj_ad_campaign_bsc` |
| Primary Key | `pk_{테이블약칭}` | `pk_cmpgn_bsc` |
| Foreign Key | `fk_{자식약칭}_{부모약칭}` | `fk_cmpgn_bsc_cmpny_bsc` |
| Unique Index | `uq_{테이블약칭}_{컬럼들}` | `uq_cmpgn_media_ext_id` |
| 일반 Index | `idx_{테이블약칭}_{컬럼들}` | `idx_cmpgn_bsc_company_id` |

**완료 기준**: `.dbml` 파일 존재, 모든 테이블 명명규칙 준수, FK 제약 + 인덱스 + 오딧컬럼 포함

---

## 프로세스

### Step 1. 산출물 경로 확정

1. `{설계}` 변수를 다음 우선순위로 해소:
   - PROJECT.md 등록 경로 (존재 시)
   - 루트에 `200.설계/` 또는 유사 설계 디렉토리 존재 시 해당 경로
   - 둘 다 없음 → default `200.설계/` 제안 + 사용자 확인
2. 발동 모드별 출력 경로를 구성한다.

### Step 2. 모드 결정

- pilot 파이프라인 디스패치 시: 오케스트레이터가 지정한 모드부터 시작
- 단독 호출 시: 사용자 지정 또는 확인
- 기존 ERD 주입 시: 주입된 ERD 단계 다음 모드부터 시작
- 역공학 트랙 디스패치 시: physical부터 시작하고 concept은 실행하지 않는다

### Step 3. 입력 컨텍스트 수집

- 기획서 (`docs/PRD.md`·`docs/SERVICE.md`·`docs/SPEC.md` 존재 시 Read)
- DICT 사전 (`{설계}/사전/` 존재 시 Read — 논리/물리 모드 필수)
- 기존 ERD (주입된 경우 Read)

### Step 4. 모드별 산출물 생성

각 모드의 규칙(위 §3모드 분리 발동)을 따라 `.mermaid` 또는 `.dbml` 파일과 `.md` 설명 파일을 생성한다.

**개념 모드**:
- 엔티티·관계 도출: 기획서·대화에서 업무 객체 식별
- M:N 포함 자유 표현
- `references/mermaid-guide.md §2` 템플릿 사용

**논리 모드**:
- 개념 ERD의 각 엔티티에 속성 추가 (DICT 사전 기반)
- M:N 매핑 엔티티로 해소
- `references/mermaid-guide.md §3` 템플릿 사용

**물리 모드**:
- 논리 ERD → DBML 변환
- 도메인사전 타입 매핑 적용
- 인덱스·제약·오딧컬럼 추가

### Step 5. 설명 문서 생성

각 `.mermaid` 파일에 대응하는 `.md` 문서를 `references/mermaid-guide.md §4` 템플릿으로 작성한다.
(물리 모드는 `.dbml` 파일 헤더 주석으로 대체 가능)

### Step 6. 완료 기준 검증

각 모드의 완료 기준을 자체 점검 후 다음 모드로 진행하거나 결과를 반환한다.

---

## 활용 MCP

| 상황 | MCP/도구 |
|------|---------|
| Mermaid 문법 최신 변경사항 확인 | `mcp__context7__resolve-library-id` → `mcp__context7__query-docs` |
| DBML 문법 확인 | `mcp__context7__resolve-library-id` → `mcp__context7__query-docs` |
| 복잡한 엔티티 관계 분석 | `mcp__sequential-thinking__sequentialthinking` |

---

## 저장 경로 (변수 해소 규칙)

```
{설계}/개념모델링/ERD_{영역}.mermaid
{설계}/개념모델링/ERD_{영역}.md
{설계}/논리모델링/ERD_{영역}_논리.mermaid
{설계}/논리모델링/ERD_{영역}_논리.md
{설계}/물리모델링/{프로젝트}.dbml
```

- `{설계}`: PROJECT.md의 설계 산출물 루트 변수 (하드코딩 금지, U-1 확정)
- `{영역}`: Subject Area 이름 (예: 회원, 캠페인, 광고그룹)
- `{프로젝트}`: 프로젝트 약어 (예: prj, svc)

default 트리 (`{설계}` 미선언 시 제안값):
```
200.설계/
├── 210.사전/
├── 220.개념모델링/
├── 230.논리모델링/
├── 240.물리모델링/
└── 250.DDL/
```

---

## 품질 체크리스트

### 개념 모드
- [ ] 엔티티명 끝에 "정보" 일관 적용
- [ ] 관계명 한글 동사형
- [ ] 속성 미포함 (비즈니스 뷰 전용)
- [ ] M:N 관계 허용 포함 (억제하지 않음)
- [ ] `.mermaid` + `.md` 쌍 생성

### 논리 모드
- [ ] 모든 속성명이 DICT 표준사전 용어 (`{설계}/사전/표준단어사전.md`)
- [ ] M:N → 매핑 엔티티로 해소
- [ ] PK / FK / UK 명시
- [ ] 식별/비식별 관계 구분 (`--` vs `..`)
- [ ] `.mermaid` + `.md` 쌍 생성

### 물리 모드
- [ ] 테이블명 명명규칙 준수 (`{스키마}_{주제}_{엔티티}_{유형}`)
- [ ] 타입 = 도메인사전 매핑 (`db-type-mapping.md`)
- [ ] FK 제약조건 + 인덱스 명시
- [ ] 오딧 컬럼 포함 (`created_dt`, `updated_dt`)
- [ ] `.dbml` 파일 생성

### 공통
- [ ] 산출물 경로가 `{설계}` 변수 사용 (하드코딩 없음)
- [ ] 엔티티 15개 이상이면 Subject Area 분할 적용
- [ ] 설명 문서(`.md`)에 설계 결정사항 기록

---

## 변경이력

| 버전 | 일시(KST) | 변경 내용 |
|------|----------|----------|
| 1.0 | 2026-06-12 | 초안 — erd-modeler §4(`:82-191`) 계승 + 검토서 §3.2.1 MODEL 3모드 양식 반영. mermaid-guide.md 이관 (erd-modeler → op-data-model/references/). stage=MODEL, dispatched_by=opal-pilot-data-design |
| 1.1 | 2026-08-30 17:18 | 역공학(reverse) 트랙 지원 — §모드 선택 규칙에 「기존 DB/DDL 스키마 주입」 행 추가(physical→logical, concept 미실행) + `op-data-ddl` §Step 4 참조 노트, logical/physical 입력 전제에 역공학 예외 추가, Step 2 모드 결정에 역공학 분기 불릿 추가 (104) |
