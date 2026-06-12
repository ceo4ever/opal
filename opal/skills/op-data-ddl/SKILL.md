---
name: op-data-ddl
description: |
  **DDL/마이그레이션 생성 단계 스킬**. MODEL 물리(DBML) 산출물을 입력으로 받아 DBMS별 DDL 스크립트와 ORM 마이그레이션 코드를 생성한다.
  반드시 이 스킬을 사용해야 하는 상황: 오케스트레이터(opal-pilot-data-design)가 DDL/MIGRATION 단계를 디스패치할 때. MODEL의 물리(DBML) 산출 이후에만 실행 가능.
  필수 입력: 물리 모델 DBML 파일 (`{설계}/물리모델링/{프로젝트}.dbml`). 보장 출력: DDL SQL 파일 (`{설계}/DDL/{프로젝트}_{DBMS}.sql`) + 마이그레이션 스크립트 (ORM 사용 시).
stage: DDL
dispatched_by: opal-pilot-data-design
version: 1.0
---

# DDL/마이그레이션 생성 (DDL)

## 실행 컨텍스트

이 스킬은 `opal-db-agent` 워커 에이전트의 컨텍스트에서 실행된다.
오케스트레이터(`opal-pilot-data-design`)가 DDL/MIGRATION 단계를 디스패치하면, `opal-db-agent`가 이 스킬을 읽고 프로세스를 따른다.

> **[MUST]** `docs/proposals/opal-data-design.md` §3.2: "DDL/MIGRATION은 MODEL의 물리(DBML) 산출 이후에만 실행 가능(캡틴 명시). state-tool stage-transition guard가 자동 차단." — 물리 DBML 파일이 존재하지 않으면 즉시 블로커 보고.

> **[MUST]** 산출물 작성·검증 시 `opal/core/references/harness/citation-rules.md`를 Read하여 규칙(근거 제시 원칙 / [MUST] 토큰 / 영역 간 용어 일관성)을 준수한다.

> **[MUST]** DDL 출력 경로는 하드코딩하지 않는다. `docs/PROJECT.md`에 등록된 `{설계}` 변수(설계 산출물 루트)를 읽어 `{설계}/DDL/`으로 해소한다. PROJECT.md에 경로가 미등록된 경우: ① 루트에 `200.설계/` 디렉토리 탐색 → ② 없으면 default `200.설계/250.DDL/` 제안 후 사용자 확인.

---

## 페르소나

`opal/agents/opal-db-agent/personas/db-architect.md`를 Read하여 DB 전문 지식과 행동 규칙을 적용한다.
(DDL 생성 규칙 / DBMS별 타입 변환 / 마이그레이션 정합 원칙 포함)

---

## 입력/출력

| 항목 | 설명 |
|------|------|
| **필수 입력** | `{설계}/물리모델링/{프로젝트}.dbml` (MODEL 물리 산출물) |
| **선택 입력** | 대상 DBMS (미지정 시 기획서 또는 사용자에게 확인), 기존 DDL·마이그레이션 (증분 모드) |
| **보장 출력** | `{설계}/DDL/{프로젝트}_{DBMS}.sql` — DBMS별 CREATE TABLE + INDEX + FK DDL 스크립트 |
| **선택 출력** | ORM 마이그레이션 스크립트 (ORM 사용 프로젝트에서 요청 시) |

---

## 물리 입력 전제 검증

DDL 프로세스 시작 전 아래를 반드시 확인한다:

1. `{설계}/물리모델링/{프로젝트}.dbml` 파일 존재 여부 확인
2. DBML 파일이 없으면 **즉시 블로커 보고**: "물리 DBML 파일이 없습니다. MODEL 물리(physical) 단계를 먼저 완료해야 DDL을 생성할 수 있습니다."
3. DBML 파일이 있으면 Read → 테이블·컬럼·관계 구조 파악 후 다음 Step 진행

---

## 프로세스

### Step 1. references 로딩

1. `opal/skills/op-data-ddl/references/dbml-guide.md` Read — DBML 문법·변환 규칙·템플릿 숙지
2. `opal/skills/op-data-dictionary/references/db-type-mapping.md` Read — D001~D022 DBMS별 타입 매핑 숙지
   (CLI 없이 수동 DDL 생성 시 타입 변환의 SSOT)

### Step 2. 프로젝트 컨텍스트 로딩

1. `docs/PROJECT.md`에서 `{설계}` 경로 변수 + 타겟 DBMS 확인
2. `{설계}/물리모델링/{프로젝트}.dbml` Read (물리 입력 전제 검증 완료 후)
3. 기존 DDL·마이그레이션 파일 존재 시 Read (증분 변경 파악)
4. 타겟 DBMS 미확인 시 — 사용자에게 확인 (MySQL 9 / PostgreSQL 16 / MSSQL / Oracle 19c)

### Step 3. DBML → DDL 변환

`dbml2sql` CLI를 우선 사용하고, CLI 부재 시 수동 폴백으로 처리한다.

#### 3-A. DBML CLI 사용 (우선)

```bash
# CLI 설치 여부 확인
which dbml2sql || npm list -g @dbml/cli

# MySQL DDL 생성
dbml2sql {설계}/물리모델링/{프로젝트}.dbml --mysql -o {설계}/DDL/{프로젝트}_mysql.sql

# PostgreSQL DDL 생성
dbml2sql {설계}/물리모델링/{프로젝트}.dbml --postgres -o {설계}/DDL/{프로젝트}_postgres.sql

# MSSQL DDL 생성
dbml2sql {설계}/물리모델링/{프로젝트}.dbml --mssql -o {설계}/DDL/{프로젝트}_mssql.sql
```

CLI가 설치되어 있지 않으면:
```bash
npm install -g @dbml/cli
```
설치 불가 환경이면 Step 3-B 폴백으로 전환한다.

#### 3-B. CLI 없이 수동 DDL 생성 (폴백)

DBML 파일을 직접 읽어 DDL을 수동 생성한다. `db-type-mapping.md` 타입 매핑을 SSOT로 사용한다.

**MySQL DDL 변환 규칙:**

| DBML | MySQL DDL |
|------|-----------|
| `bigint [pk, increment]` | `BIGINT AUTO_INCREMENT PRIMARY KEY` |
| `varchar(N) [not null]` | `VARCHAR(N) NOT NULL` |
| `[default: 'Y']` | `DEFAULT 'Y'` |
| `[note: '한글명']` | `COMMENT '한글명'` |
| `ref: > table.col` | `FOREIGN KEY (col) REFERENCES table(col) ON DELETE RESTRICT ON UPDATE CASCADE` |
| `indexes { col [name: 'idx'] }` | `CREATE INDEX idx ON table(col)` |
| `indexes { (col1,col2) [unique, name: 'uq'] }` | `CREATE UNIQUE INDEX uq ON table(col1, col2)` |

**DDL 파일 헤더 템플릿:**

```sql
-- ============================================
-- 프로젝트: {프로젝트명}
-- DBMS: {DBMS명}
-- 생성일: YYYY-MM-DD
-- 원천: {설계}/물리모델링/{프로젝트}.dbml
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

**DBMS별 DDL 생성 시 타입 변환:**
- CLI 없는 수동 생성 시, DBML의 MySQL 기본 타입을 타겟 DBMS에 맞게 `db-type-mapping.md` 기준으로 치환한다.
- 예: MySQL `DATETIME` → PostgreSQL `TIMESTAMP WITH TIME ZONE`, MSSQL `DATETIME2`, Oracle `TIMESTAMP WITH TIME ZONE`

### Step 4. 역공학 (선택 — DDL → DBML)

기존 DB에서 DBML을 역추출해야 하는 경우:

```bash
# DDL → DBML 역공학
sql2dbml dump.sql --mysql -o {설계}/물리모델링/{프로젝트}.dbml
```

역공학 결과물은 MODEL 물리 산출물로 저장하며, op-data-model의 physical 모드 산출물 경로를 따른다.

### Step 5. ORM 마이그레이션 스크립트 생성 (선택)

ORM을 사용하는 프로젝트에서 마이그레이션 스크립트 생성이 요청된 경우:

1. 프로젝트 ORM 파악 (Alembic / Django ORM / Prisma / Sequelize / TypeORM 등)
2. ORM별 마이그레이션 패턴 적용:

| ORM | 마이그레이션 방식 | 산출물 경로 |
|-----|----------------|------------|
| Alembic (Python) | `upgrade()` / `downgrade()` 함수 | `migrations/versions/{rev}_{desc}.py` |
| Django ORM | `operations` 리스트 | `{app}/migrations/{NNNN}_{desc}.py` |
| Prisma | `prisma migrate` | `prisma/migrations/{ts}_{desc}/migration.sql` |
| TypeORM | `up()` / `down()` 메서드 | `src/migrations/{ts}-{Desc}.ts` |
| Sequelize | `up` / `down` 함수 | `migrations/{ts}-{desc}.js` |

3. DDL 스크립트와 ORM 마이그레이션 코드 간 정합성 검증:
   - 테이블명·컬럼명 일치
   - 타입·제약조건 일치
   - FK·인덱스 누락 없음

4. ORM 최신 마이그레이션 API 확인 시 context7 사용:
   ```
   mcp__context7__resolve-library-id → mcp__context7__query-docs
   ```

### Step 6. 품질 검증

완료 전 아래 항목을 자체 점검한다:

- [ ] 물리 DBML 입력 존재 확인 (선행 전제 검증 완료)
- [ ] DDL SQL 파일 생성됨: `{설계}/DDL/{프로젝트}_{DBMS}.sql`
- [ ] 모든 테이블의 CREATE TABLE 구문 포함
- [ ] PRIMARY KEY 제약조건 누락 없음
- [ ] FOREIGN KEY 참조 무결성 — 참조 테이블이 먼저 생성되는 순서
- [ ] 인덱스·유니크 제약조건 포함
- [ ] 테이블/컬럼 COMMENT (한글명) 포함
- [ ] DBMS별 타입이 `db-type-mapping.md` 기준과 일치
- [ ] 명명규칙 준수: `PK_{테이블약칭}` / `FK_{테이블약칭}_{참조약칭}` / `UQ_{테이블약칭}_{컬럼들}` / `IDX_{테이블약칭}_{컬럼들}`
- [ ] ORM 마이그레이션 요청 시 ORM 코드 생성됨 + DDL과 정합

---

## 활용 MCP

| 상황 | 활용 수단 |
|------|-----------|
| ORM 마이그레이션 최신 API 조회 | `mcp__context7__resolve-library-id` → `mcp__context7__query-docs` |
| 복잡한 DDL 변환 로직 분해 | `mcp__sequential-thinking__sequentialthinking` |
| @dbml/cli 문서 확인 | `mcp__context7__resolve-library-id` → `mcp__context7__query-docs` |

---

## 저장 경로

| 산출물 | 경로 | 형식 |
|--------|------|------|
| DDL 스크립트 (MySQL) | `{설계}/DDL/{프로젝트}_mysql.sql` | SQL |
| DDL 스크립트 (PostgreSQL) | `{설계}/DDL/{프로젝트}_postgres.sql` | SQL |
| DDL 스크립트 (MSSQL) | `{설계}/DDL/{프로젝트}_mssql.sql` | SQL |
| DDL 스크립트 (Oracle) | `{설계}/DDL/{프로젝트}_oracle.sql` | SQL |
| ORM 마이그레이션 | ORM 관례 경로 (Step 5 참조) | ORM별 |

> `{설계}` = `docs/PROJECT.md` 등록 변수. default: `200.설계` (프로젝트 루트 기준 상대경로)
> DDL default 경로: `200.설계/250.DDL/`

---

## 품질 체크리스트

- [ ] 물리 DBML 입력 전제 충족 (블로커 없음)
- [ ] DDL SQL 파일 존재 + DBMS 타입 정합
- [ ] 모든 테이블 CREATE TABLE 포함 (DBML 테이블 수 일치)
- [ ] FK 참조 순서 정합 (참조 테이블 선행 생성)
- [ ] 인덱스·제약조건 누락 없음
- [ ] COMMENT 한글명 포함
- [ ] `db-type-mapping.md` 기준 타입 변환 준수
- [ ] 명명규칙(`PK_`/`FK_`/`UQ_`/`IDX_`) 준수
- [ ] ORM 마이그레이션 요청 시 정합성 검증 완료
- [ ] `{설계}` 경로 변수 해소 완료 (하드코딩 없음)
- [ ] 하드코딩 시크릿/접속정보 없음

---

## 변경이력

| 버전 | 일시(KST) | 변경 내용 |
|------|----------|----------|
| 1.0 | 2026-06-12 | 최초 작성 — F-004 op-data-ddl 신설 (tasks/019-260612-opd-opal-pilot-data-design PLAN §3.4). erd-modeler §5(`:194-253`) DDL 로직 계승. dbml-guide.md 이관. 물리 입력 전제 [MUST] 명시. db-type-mapping.md(op-data-dictionary) 연동. |
