---
name: erd-modeler
description: |
  DB ERD 모델링 스킬. 개념(Mermaid) → 논리(Mermaid) → 물리(DBML→DDL) 3단계 ERD 모델링을 수행합니다.
  반드시 이 스킬을 사용해야 하는 상황: "ERD 만들어줘", "데이터 모델링", "테이블 설계", "논리 모델링", "물리 모델링", "DDL 생성", "스키마 설계", 엔티티/속성/관계 정의가 필요한 모든 작업 시.
  표준사전(단어/도메인/용어/코드) 관리는 data-dictionary 스킬이 담당합니다. 이 스킬은 사전을 "참조"만 합니다.
---

> **[DEPRECATED]** 이 스킬은 `op-data-model` / `op-data-ddl`로 분해 이관되었습니다. `//erm`은 `op-data-model` 단독 호출 alias로 하위호환됩니다. 신규 데이터 설계 파이프라인은 `//opdd` (opal-pilot-data-design)를 사용하세요.

# ERD Modeler

DB ERD 모델링 전용 스킬이다. 개념→논리→물리 3단계 모델링과 DDL 생성을 담당한다.
표준사전은 사용자가 제공한 경로 또는 내부 기본 규칙으로 참조하며, 사전 CRUD는 `data-dictionary` 스킬이 전담한다.

---

## 1. 작업 모드

| 모드 | 트리거 | 설명 |
|------|--------|------|
| `model` | ERD 모델링 | 개념→논리→물리 단계별 모델링 |
| `ddl` | DDL 추출 | DBML → 지정 DBMS용 CREATE TABLE 스크립트 |

모드가 불명확하면 사용자에게 확인한다.

---

## 2. 출력 경로 설정

작업 시작 전 출력 파일의 저장 위치를 확인한다.

1. **사용자가 경로를 지정한 경우** → 해당 경로 사용
2. **프로젝트에 기존 DB 설계 산출물이 있으면** → 해당 경로를 파악하고 동일 구조 유지
3. **경로 미지정 시** → 사용자에게 출력 경로를 확인

권장 폴더 구조 (예시 — 프로젝트 상황에 따라 조정):

```
{출력경로}/
├── 개념모델링/                ← Mermaid (.mermaid + .md)
│   ├── ERD_SA{N}_{영역명}.mermaid
│   └── ERD_SA{N}_{영역명}.md
├── 논리모델링/                ← Mermaid (.mermaid + .md)
│   ├── ERD_SA{N}_{영역명}_논리.mermaid
│   └── ERD_SA{N}_{영역명}_논리.md
└── 물리모델링/                ← DBML + DDL
    ├── {프로젝트명}_전체.dbml
    └── ddl/
        ├── mysql/
        │   └── {프로젝트명}_DDL_mysql.sql
        └── {다른DB}/
```

---

## 3. 사전 참조 규칙

이 스킬은 표준사전을 **읽기 전용**으로 참조한다. 사전은 다음 3단계 폴백으로 획득한다.

### 3단계 폴백 — 사전 획득

| 단계 | 조건 | 처리 |
|------|------|------|
| 1단계 | 사용자가 사전 파일 경로를 제공한 경우 | 해당 경로를 Read하여 사전 로드 |
| 2단계 | 사전 없음 (소규모/신규 프로젝트) | 분류어 약어표(`../../opal/skills/op-data-dictionary/references/naming-convention.md`)를 기반으로 내부 표준 적용 |
| 3단계 | 외부 표준이 필요한 경우 | 웹 검색으로 해당 도메인 표준 약어/타입 참조 |

> 2단계 적용 시 사용자에게 "표준사전 없이 내부 기본 규칙으로 진행합니다" 안내한다.
> data-dictionary 스킬이 있는 프로젝트에서는 연동하여 사전 내용을 가져올 수 있다.

### 논리 모델링 시
- 속성명은 가능하면 **용어사전에 등록된 용어**의 물리컬럼명을 사용한다.
- 사전이 없으면 `naming-convention.md`의 수식어/분류어 패턴을 적용한다.
- 속성의 데이터타입은 **도메인사전 또는 분류어 약어표**에서 매핑한다.

### 물리 모델링 시
- 테이블명은 **명명규칙**을 따른다: `{스키마}_{주제영역}_{엔티티}_{유형}`
- 컬럼 타입/길이는 **도메인사전의 해당 DBMS 컬럼** 또는 `naming-convention.md` 분류어 매핑표를 참조한다.
- 코드성 컬럼의 CHECK 제약조건은 **코드사전**을 참조한다 (사전이 없으면 생략하고 주석으로 표시).

---

## 4. ERD 모델링 (model 모드)

### 4.1 3단계 모델링 흐름

```
개념 모델링 (Mermaid)
  비즈니스 관계, 카디널리티 중심
  M:N 허용, FK 없음
    ↓
논리 모델링 (Mermaid)
  속성, FK, 데이터타입 상세화
  식별/비식별 관계, M:N 해소
  표준용어사전 기반 속성명
    ↓
물리 모델링 (DBML)
  DBMS 특화 타입, 인덱스, 제약조건
  DDL 자동 추출
```

### 4.2 개념 모델링

비즈니스 관점에서 엔티티와 관계를 정의한다. 기술적 디테일은 배제한다.

규칙:
- 관계명: 한글, 동사형 ("운영한다", "포함한다")
- 카디널리티: 1:1, 1:N, M:N (M:N 허용)
- 선택성: 필수(||) / 선택(o|)
- FK 속성: 표현하지 않음
- 한글 엔티티명 끝에 "정보" 붙임

Mermaid 문법은 `references/mermaid-guide.md`를 참조한다.

개념 ERD 예시:
```mermaid
erDiagram
    COMPANY["회사 정보"] ||--o{ BRAND["브랜드 정보"] : "운영한다"
    BRAND ||--o{ CAMPAIGN["캠페인 정보"] : "집행한다"
    CAMPAIGN ||--o{ ADGROUP["광고그룹 정보"] : "포함한다"
```

### 4.3 논리 모델링

속성, FK, 데이터타입을 상세화한다. **표준용어사전에서 속성명을 가져온다.**

규칙:
- 모든 속성은 표준용어사전에 등록된 용어로 정의 (미등록 시 사전에 먼저 등록)
- 식별 관계: 실선 (부모 PK → 자식 PK에 포함)
- 비식별 관계: 점선 (부모 PK → 자식 일반속성 FK)
- M:N 관계: 매핑 엔티티로 해소
- PK, FK 키 표시

식별 vs 비식별 판단 기준:
- 자식이 부모 없이 독립적으로 존재할 수 있는가? → Yes: 비식별, No: 식별
- 부모 PK가 자식의 정체성(PK)에 포함되는가? → Yes: 식별, No: 비식별
- 대부분의 마스터 테이블 간 관계는 비식별 (자체 ID로 식별)

논리 ERD 예시:
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

    COMPANY_BSC["회사 기본 정보"] ||--o{ CAMPAIGN_BSC : "집행한다"
    BRAND_BSC["브랜드 기본 정보"] ||--o{ CAMPAIGN_BSC : "소속된다"
```

### 4.4 물리 모델링

DBML로 전환하여 DBMS 특화 설계를 수행한다.
Mermaid 논리 모델을 DBML로 변환하는 과정에서:

1. 엔티티명 → 물리 테이블명 변환 (명명규칙 적용)
2. 속성 → 컬럼 변환 (**도메인사전에서 해당 DBMS의 타입/길이 매핑**)
3. 관계 → FK 제약조건 + 인덱스 생성
4. 프로젝트 명명규칙의 스키마, 주제영역 접두어 적용

DBML 작성 규칙은 `references/dbml-guide.md`를 참조한다.

### 4.5 명명규칙

이 스킬의 기본 명명규칙이다. 프로젝트에 별도 명명규칙이 있으면 프로젝트 규칙을 우선한다.
상세 규칙은 data-dictionary 스킬의 `references/naming-convention.md`를 참조한다.

**테이블명**: `{스키마}_{주제영역}_{엔티티}_{유형}`

| 요소 | 설명 | 예시 |
|------|------|------|
| 스키마 | 프로젝트/서비스 약어 (프로젝트별 확정) | prj, svc 등 |
| 주제영역 | 업무 영역 약어 (유일해야 함) | ad, cm, mb |
| 엔티티 | 대상 객체 | campaign, member |
| 유형 | bsc(기본), dtl(상세), hst(이력), map(매핑), stat(통계), cd(코드) | bsc |

**한글 테이블명**: 끝에 반드시 "정보"를 붙인다.
- 예: 캠페인 기본 정보, 광고그룹 상세 정보, 일별 성과 통계 정보

**제약조건 명명**:
| 제약조건 | 패턴 | 예시 |
|---------|------|------|
| Primary Key | `pk_{테이블약칭}` | pk_cmpgn_bsc |
| Foreign Key | `fk_{자식약칭}_{부모약칭}` | fk_cmpgn_bsc_cmpny_bsc |
| Unique Index | `uq_{테이블약칭}_{컬럼들}` | uq_cmpgn_media_ext_id |
| Index | `idx_{테이블약칭}_{컬럼들}` | idx_cmpgn_bsc_company_id |

---

## 5. DDL 추출 (ddl 모드)

### 5.1 DBML → DDL 변환

DBML CLI를 사용한다:
```bash
# MySQL (기본)
dbml2sql schema.dbml --mysql -o output_mysql.sql

# PostgreSQL
dbml2sql schema.dbml --postgres -o output_postgres.sql

# MSSQL
dbml2sql schema.dbml --mssql -o output_mssql.sql
```

CLI가 설치되어 있지 않으면:
```bash
npm install -g @dbml/cli
```

### 5.2 CLI 없이 DDL 생성

DBML CLI를 사용할 수 없는 환경에서는 DBML 파일을 직접 읽어서 DDL을 생성한다.
이때 **도메인사전의 DBMS별 타입 매핑**을 참조한다.

MySQL DDL 생성 시 포함 항목:
- CREATE TABLE (컬럼, 타입, NOT NULL, DEFAULT)
- PRIMARY KEY
- FOREIGN KEY (ON DELETE, ON UPDATE)
- INDEX, UNIQUE INDEX
- 테이블/컬럼 COMMENT (한글명)

DDL 템플릿:
```sql
-- ============================================
-- 프로젝트: {프로젝트명}
-- DBMS: {DBMS명}
-- 생성일: YYYY-MM-DD
-- ============================================

CREATE TABLE {테이블명} (
    {컬럼명} {타입} {제약조건} COMMENT '{한글용어명}',
    ...
    PRIMARY KEY ({PK컬럼}),
    CONSTRAINT {FK명} FOREIGN KEY ({FK컬럼})
        REFERENCES {참조테이블}({참조컬럼})
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='{한글 테이블명}';

CREATE INDEX {인덱스명} ON {테이블명}({컬럼들});
```

### 5.3 역공학 (DDL → DBML)

기존 DB에서 DBML을 생성하는 경우:
```bash
sql2dbml dump.sql --mysql -o schema.dbml
```

---

## 6. 작업 전 체크리스트

모델링 작업 시작 전 반드시 확인:

- [ ] 출력 경로가 확정되었는가? → 미지정 시 사용자에게 확인
- [ ] 프로젝트 명명규칙 문서가 있는가? → 있으면 우선 적용, 없으면 `naming-convention.md` 기본 규칙 사용
- [ ] 표준사전이 존재하는가? → 있으면 경로 확인, 없으면 3단계 폴백 진행 (Section 3 참조)
- [ ] 이전 단계 산출물이 존재하는가? (개념→논리 시 개념 ERD 확인)
- [ ] 물리 모델링 시 대상 DBMS가 확정되었는가? (기본: MySQL 9)

---

## 7. 참고 문서

| 문서 | 경로 | 용도 |
|------|------|------|
| Mermaid 가이드 | `references/mermaid-guide.md` | 개념/논리 모델링 문법 |
| DBML 가이드 | `references/dbml-guide.md` | 물리 모델링 문법 |
| 명명규칙 가이드 | `../../opal/skills/op-data-dictionary/references/naming-convention.md` | 축약, 테이블/컬럼 이름 짓기 상세 |
| DB 타입 매핑표 | `../../opal/skills/op-data-dictionary/references/db-type-mapping.md` | DBMS별 물리 타입 상세 매핑 |

---

## 변경이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-06-12 | [DEPRECATED] op-data-model / op-data-ddl 로 분해 이관. //erm alias 하위호환 유지. 참조 경로 data-dictionary → opal/skills/op-data-dictionary 갱신 (Task 019) |
