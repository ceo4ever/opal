# DB 타입 매핑 가이드

> op-data-dictionary 스킬 참조 문서
> 이 문서는 `naming-convention.md` §1 분류어표(D001~D022)의 MySQL 9 타입을 기준으로
> PostgreSQL / MSSQL / Oracle 타입 컬럼을 확장한 DBMS별 타입 매핑 SSOT이다.
>
> **원천**: `skills/erd-modeler/references/naming-convention.md` §1 분류어 약어표 (MySQL 9 타입)
> **확장**: PostgreSQL 16 / SQL Server 2022 / Oracle 19c 기준

---

## 도메인 ↔ DBMS 타입 매핑표

| 도메인 | 한글 | 약어 | MySQL 9 | PostgreSQL 16 | MSSQL (SQL Server 2022) | Oracle 19c | 비고 |
|--------|------|------|---------|--------------|------------------------|------------|------|
| D001 | 번호 | no | `BIGINT UNSIGNED` | `BIGINT` | `BIGINT` | `NUMBER(19)` | PK 자동증가 시: MySQL `AUTO_INCREMENT`, PG `BIGSERIAL`, MSSQL `IDENTITY(1,1)`, Oracle `GENERATED ALWAYS AS IDENTITY` |
| D002 | 명 | nm | `VARCHAR(200)` | `VARCHAR(200)` | `NVARCHAR(200)` | `VARCHAR2(200 CHAR)` | 한글 포함 시 Oracle `CHAR` 단위 필수 |
| D003 | 코드 | cd | `VARCHAR(20)` | `VARCHAR(20)` | `NVARCHAR(20)` | `VARCHAR2(20 CHAR)` | 고정폭 코드는 `CHAR(N)` 사용 가능 |
| D004 | 식별자 | id | `VARCHAR(100)` | `VARCHAR(100)` | `NVARCHAR(100)` | `VARCHAR2(100 CHAR)` | 외부 시스템 ID, UUID 문자열 포함 |
| D005 | 수 | cnt | `INT` | `INTEGER` | `INT` | `NUMBER(10)` | 음수 불가 시 MySQL `INT UNSIGNED`, PG `CHECK (cnt >= 0)` |
| D006 | 숫자 | num | `INT` | `INTEGER` | `INT` | `NUMBER(10)` | 범용 정수. 범위 초과 시 D001(BIGINT) 사용 |
| D007 | 금액 | amt | `DECIMAL(18,4)` | `NUMERIC(18,4)` | `DECIMAL(18,4)` | `NUMBER(18,4)` | 통화 정밀도 4자리. 환율 계산 포함 금액은 소수 4자리 권장 |
| D008 | 율 | rt | `DECIMAL(10,4)` | `NUMERIC(10,4)` | `DECIMAL(10,4)` | `NUMBER(10,4)` | CTR·전환율 등 비율값. 0~1 또는 0~100 범위는 정책으로 결정 |
| D009 | 일시 | dt | `DATETIME` | `TIMESTAMP WITH TIME ZONE` | `DATETIME2` | `TIMESTAMP WITH TIME ZONE` | 타임존 처리: PG/Oracle `WITH TIME ZONE`, MSSQL `DATETIME2(7)`, MySQL UTC 저장 권장 |
| D010 | 일자 | date | `DATE` | `DATE` | `DATE` | `DATE` | 시간 불필요한 날짜 전용 |
| D011 | 여부 | yn | `CHAR(1)` | `CHAR(1)` | `CHAR(1)` | `CHAR(1)` | 허용값: `'Y'`/`'N'`. CHECK 제약 권장. PG `BOOLEAN` 사용 가능(프로젝트 정책 따름) |
| D012 | 내용 | cn | `TEXT` | `TEXT` | `NVARCHAR(MAX)` | `CLOB` | 길이 무제한 텍스트. 인덱스 불가(전문검색은 별도 설계) |
| D013 | 설명 | desc | `VARCHAR(500)` | `VARCHAR(500)` | `NVARCHAR(500)` | `VARCHAR2(500 CHAR)` | 단문 설명. 500자 초과 예상 시 D012(TEXT/CLOB) 사용 |
| D014 | 구분 | clsf | `VARCHAR(20)` | `VARCHAR(20)` | `NVARCHAR(20)` | `VARCHAR2(20 CHAR)` | 분류코드. D003과 구분: 구분은 업무 분기, 코드는 공통코드 |
| D015 | URL | url | `VARCHAR(500)` | `VARCHAR(500)` | `NVARCHAR(500)` | `VARCHAR2(500 CHAR)` | URL 최대 길이 2083자(IE 한계). 긴 URL은 `TEXT`/`CLOB` 고려 |
| D016 | 수량 | qty | `INT` | `INTEGER` | `INT` | `NUMBER(10)` | 재고·수량 등 양의 정수. 음수 불가 정책 적용 시 CHECK 추가 |
| D017 | 비밀번호 | pw | `VARCHAR(200)` | `VARCHAR(200)` | `NVARCHAR(200)` | `VARCHAR2(200 CHAR)` | 반드시 해시 저장(bcrypt 60자, Argon2 95자+). 평문 저장 금지 |
| D018 | 순서 | ord | `INT` | `INTEGER` | `INT` | `NUMBER(10)` | 정렬 순서. 0-based 또는 1-based는 프로젝트 정책 통일 |
| D019 | 퍼센트 | pct | `DECIMAL(5,2)` | `NUMERIC(5,2)` | `DECIMAL(5,2)` | `NUMBER(5,2)` | 0.00~100.00 범위. CHECK(`pct BETWEEN 0 AND 100`) 권장 |
| D020 | 이메일 | email | `VARCHAR(100)` | `VARCHAR(100)` | `NVARCHAR(100)` | `VARCHAR2(100 CHAR)` | RFC 5321 최대 254자. 인덱스 필요 시 대소문자 정규화 후 저장 |
| D021 | 휴대폰 | mobile | `VARCHAR(20)` | `VARCHAR(20)` | `NVARCHAR(20)` | `VARCHAR2(20 CHAR)` | 국가번호 포함 `+821012345678` 형식 고려. `+`·`-` 포함 최대 20자 |
| D022 | UUID | uuid | `BINARY(16)` | `UUID` | `UNIQUEIDENTIFIER` | `RAW(16)` | PG는 네이티브 `UUID` 타입. MySQL `BINARY(16)` + `UUID_TO_BIN()` 변환. Oracle `RAW(16)` + `SYS_GUID()` |

---

## 보조 매핑: 별칭 도메인

naming-convention.md의 별칭 행(도메인 재사용)도 동일 타입을 따른다.

| 별칭 | 한글 | 약어 | 참조 도메인 | 비고 |
|------|------|------|------------|------|
| D002 | 상세 | dtl | D002 (VARCHAR(200)) | 상세 설명이지만 단문 — D002 타입 그대로 |
| D007 | 일예산 | daily_bdgt | D007 (DECIMAL(18,4)) | 금액 도메인 재사용 |

---

## DBMS별 특이사항 요약

### MySQL 9

- `BIGINT UNSIGNED`는 D001(번호/PK)에만 사용. 일반 정수는 `INT`.
- `DATETIME` 기본값 `CURRENT_TIMESTAMP`, 타임존은 `@@global.time_zone` 설정 의존 → UTC 저장 권장.
- `BINARY(16)` + `UUID_TO_BIN(uuid, 1)` 조합으로 UUID 저장 성능 최적화 가능.

### PostgreSQL 16

- `SERIAL`/`BIGSERIAL`은 deprecated 경향 → `GENERATED ALWAYS AS IDENTITY` 권장.
- `BOOLEAN` 타입이 있으나 D011(여부) 표준은 `CHAR(1)` — 프로젝트 정책에 따라 선택.
- 문자열 타입에 `N` 접두어 불필요 (모든 문자열이 UTF-8 유니코드).
- `TIMESTAMP WITH TIME ZONE` = `TIMESTAMPTZ` (내부적으로 UTC 저장, 출력 시 세션 타임존 변환).

### MSSQL (SQL Server 2022)

- 한글 등 멀티바이트 문자 저장 시 반드시 `NVARCHAR`/`NCHAR` 사용 (`VARCHAR`는 ASCII 기반 코드페이지 의존).
- `DATETIME2`는 `DATETIME`보다 정밀도 높음(최대 100ns). D009에 `DATETIME2(7)` 권장.
- `UNIQUEIDENTIFIER`는 `NEWID()` 또는 `NEWSEQUENTIALID()` 기본값 사용.
- `NVARCHAR(MAX)` = D012(내용) 대응. 최대 2GB.

### Oracle 19c

- 문자열은 `VARCHAR2` 사용 (`VARCHAR`는 미래 의미 변경 가능성으로 Oracle 공식 비권장).
- `VARCHAR2(N CHAR)` 단위 명시: 바이트 단위(기본)가 아닌 문자 단위로 한글 안전하게 저장.
- `NUMBER(P,S)`: 정수는 `NUMBER(10)` 또는 `NUMBER(19)`, 소수는 `NUMBER(18,4)` 등.
- `CLOB` = D012(내용) 대응. 4GB까지 저장.
- `RAW(16)` + `SYS_GUID()` 또는 `SYS_GUID()` 반환값을 `RAW`로 저장.
- `TIMESTAMP WITH TIME ZONE` 지원 (Oracle 9i 이상).

---

## 타입 선택 결정 흐름

```
1. 컬럼의 분류어 약어를 확인한다 (예: no, nm, amt, dt ...)
2. 위 매핑표에서 해당 도메인(D001~D022)을 찾는다
3. 프로젝트 타겟 DBMS 열의 타입을 적용한다
4. DBMS별 특이사항이 있으면 비고·하단 요약을 참고한다
5. 프로젝트 정책(타임존, UUID 포맷, BOOLEAN vs CHAR(1))이 있으면 정책을 우선한다
```

---

## 변경이력

| 버전 | 일시(KST) | 변경 내용 |
|------|----------|----------|
| 1.0 | 2026-06-12 | 최초 작성 — naming-convention.md §1 D001~D022 MySQL 기준 + PG/MSSQL/Oracle 타입 컬럼 확장 |
