# DBML 가이드

> op-data-ddl 스킬 참조 문서
> 물리 모델링 및 DDL 변환에 사용
>
> **이관**: `skills/erd-modeler/references/dbml-guide.md` → 이 경로 (F-004 op-data-ddl 신설)
> **원천 스킬**: erd-modeler (deprecated → op-data-model / op-data-ddl 분리)

---

## 1. DBML 기본 문법

### 프로젝트 정의

```dbml
Project {
  database_type: 'MySQL'
  Note: '''
    프로젝트: {프로젝트명}
    생성일: YYYY-MM-DD
    DBMS: MySQL 9
  '''
}
```

### 테이블 정의

```dbml
Table 스키마.테이블명 {
  컬럼명 타입 [속성들]

  Note: '한글 테이블명'

  indexes {
    (컬럼1, 컬럼2) [unique, name: '인덱스명']
    컬럼3 [name: '인덱스명']
  }
}
```

### 컬럼 속성

| 속성 | 의미 | 예시 |
|------|------|------|
| `pk` | Primary Key | `campaign_id bigint [pk, increment]` |
| `increment` | AUTO_INCREMENT | `campaign_id bigint [pk, increment]` |
| `not null` | NOT NULL | `campaign_nm varchar(200) [not null]` |
| `null` | NULL 허용 | `memo_cn text [null]` |
| `default: 값` | 기본값 | `use_yn char(1) [not null, default: 'Y']` |
| `note: '설명'` | 한글 속성명 (COMMENT) | `note: '캠페인식별자'` |
| `ref: > 테이블.컬럼` | FK 참조 (인라인) | `ref: > stl_cm_company_bsc.company_id` |

### 관계 정의

인라인 방식 (추천):
```dbml
Table {schema}_ad_campaign_bsc {
  company_id bigint [not null, ref: > {schema}_cm_company_bsc.company_id, note: '회사식별자']
}
```

별도 정의 방식:
```dbml
Ref: {schema}_ad_campaign_bsc.company_id > {schema}_cm_company_bsc.company_id
```

관계 기호:
| 기호 | 의미 |
|------|------|
| `>` | Many-to-One (N:1) |
| `<` | One-to-Many (1:N) |
| `-` | One-to-One (1:1) |
| `<>` | Many-to-Many (M:N, 거의 사용 안함) |

---

## 2. DBMS별 타입 매핑

### 도메인 → 타입 매핑

| 도메인 | 약어 | MySQL | PostgreSQL | MSSQL |
|--------|------|-------|-----------|-------|
| 식별자 | id | BIGINT | BIGINT | BIGINT |
| 명칭 | nm | VARCHAR(200) | VARCHAR(200) | NVARCHAR(200) |
| 코드 | cd | VARCHAR(20) | VARCHAR(20) | VARCHAR(20) |
| 번호 | no | VARCHAR(30) | VARCHAR(30) | VARCHAR(30) |
| 수량 | cnt | INT | INTEGER | INT |
| 숫자 | num | INT | INTEGER | INT |
| 금액 | amt | DECIMAL(15,2) | NUMERIC(15,2) | DECIMAL(15,2) |
| 비율 | rt | DECIMAL(8,4) | NUMERIC(8,4) | DECIMAL(8,4) |
| 일시 | dt | DATETIME | TIMESTAMP | DATETIME2 |
| 일자 | date | DATE | DATE | DATE |
| 여부 | yn | CHAR(1) | CHAR(1) | CHAR(1) |
| 내용 | cn | TEXT | TEXT | NVARCHAR(MAX) |

> **전체 DBMS 타입 매핑 (D001~D022 + Oracle 포함)**은 `opal/skills/op-data-dictionary/references/db-type-mapping.md`를 참조한다.

### DBML에서는 MySQL 타입을 기본으로 사용

```dbml
Table {schema}_ad_campaign_bsc {
  campaign_id bigint [pk, increment, note: '캠페인식별자']
  campaign_nm varchar(200) [not null, note: '캠페인명']
  daily_budget_amt decimal(15,2) [note: '일예산금액']
  cnvr_rt decimal(8,4) [note: '전환율']
  start_date date [note: '시작일자']
  created_dt datetime [not null, note: '생성일시']
  use_yn char(1) [not null, default: 'Y', note: '사용여부']
}
```

---

## 3. 물리 모델링 템플릿

### 전체 파일 구조

```dbml
// ============================================
// 프로젝트: {프로젝트명}
// DBMS: MySQL 9
// 생성일: YYYY-MM-DD
// 작성자: {작성자}
// ============================================

Project {
  database_type: 'MySQL'
  Note: '{프로젝트명} 물리 데이터 모델'
}

// ----------------------------------------
// SA1: {영역명}
// ----------------------------------------

Table {schema}_cm_company_bsc {
  company_id bigint [pk, increment, note: '회사식별자']
  company_nm varchar(200) [not null, note: '회사명']
  business_no varchar(30) [note: '사업자번호']
  ceo_nm varchar(200) [note: '대표자명']
  use_yn char(1) [not null, default: 'Y', note: '사용여부']
  created_dt datetime [not null, note: '생성일시']
  updated_dt datetime [not null, note: '수정일시']

  Note: '회사 기본 정보'

  indexes {
    business_no [unique, name: 'uq_company_bsc_biz_no']
  }
}

// ----------------------------------------
// SA2: {영역명}
// ----------------------------------------

Table {schema}_ad_campaign_bsc {
  campaign_id bigint [pk, increment, note: '캠페인식별자']
  company_id bigint [not null, ref: > {schema}_cm_company_bsc.company_id, note: '회사식별자']
  brand_id bigint [not null, ref: > {schema}_cm_brand_bsc.brand_id, note: '브랜드식별자']
  media_cd varchar(20) [not null, note: '매체코드']
  campaign_nm varchar(200) [not null, note: '캠페인명']
  campaign_type_cd varchar(20) [note: '캠페인유형코드']
  campaign_state_cd varchar(20) [not null, note: '캠페인상태코드']
  daily_budget_amt decimal(15,2) [note: '일예산금액']
  start_date date [note: '시작일자']
  end_date date [note: '종료일자']
  ext_campaign_id varchar(100) [note: '외부캠페인식별자']
  use_yn char(1) [not null, default: 'Y', note: '사용여부']
  created_dt datetime [not null, note: '생성일시']
  updated_dt datetime [not null, note: '수정일시']

  Note: '캠페인 기본 정보'

  indexes {
    (media_cd, ext_campaign_id) [unique, name: 'uq_cmpgn_media_ext']
    company_id [name: 'idx_cmpgn_company']
    brand_id [name: 'idx_cmpgn_brand']
  }
}
```

---

## 4. DDL 변환

### DBML CLI 사용

```bash
# 설치
npm install -g @dbml/cli

# MySQL DDL 생성
dbml2sql schema.dbml --mysql -o output_mysql.sql

# PostgreSQL DDL 생성
dbml2sql schema.dbml --postgres -o output_postgres.sql

# MSSQL DDL 생성
dbml2sql schema.dbml --mssql -o output_mssql.sql

# 역공학: 기존 DDL → DBML
sql2dbml dump.sql --mysql -o schema.dbml
```

### CLI 없이 수동 DDL 생성

CLI를 사용할 수 없는 환경에서는 DBML을 파싱하여 DDL을 직접 생성한다.

MySQL DDL 변환 규칙:

| DBML | MySQL DDL |
|------|-----------|
| `bigint [pk, increment]` | `BIGINT AUTO_INCREMENT PRIMARY KEY` |
| `varchar(200) [not null]` | `VARCHAR(200) NOT NULL` |
| `[default: 'Y']` | `DEFAULT 'Y'` |
| `[note: '한글명']` | `COMMENT '한글명'` |
| `ref: > table.col` | `FOREIGN KEY (col) REFERENCES table(col)` |
| `indexes { col [name: 'idx'] }` | `CREATE INDEX idx ON table(col)` |

---

## 5. Mermaid → DBML 변환 체크리스트

논리 모델(Mermaid)을 물리 모델(DBML)로 변환할 때:

- [ ] 엔티티명 → 물리 테이블명 (명명규칙 적용: 스키마_주제영역_엔티티_유형)
- [ ] 속성 → 컬럼 (도메인사전에서 타입/길이 매핑)
- [ ] PK 컬럼에 `[pk, increment]` 추가
- [ ] FK 컬럼에 `ref: > 참조테이블.참조컬럼` 추가
- [ ] NOT NULL / DEFAULT 지정
- [ ] 한글명을 `note:` 속성으로 이동
- [ ] 인덱스/유니크 제약조건 추가
- [ ] 공통 컬럼 확인 (use_yn, created_dt, updated_dt)
- [ ] Table Note에 한글 테이블명 추가
