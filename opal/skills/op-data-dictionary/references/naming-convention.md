# 명명규칙 가이드

> op-data-dictionary 스킬 참조 문서 (erd-modeler/references/naming-convention.md에서 이관)
> 이 문서의 약어 예시는 MAMS 프로젝트 기준이며, 실제 적용 시에는 해당 프로젝트의 표준단어사전을 우선한다. 사전이 없는 경우 이 문서의 규칙과 예시를 기본으로 사용한다.

---

## 1. 영문약어 생성 규칙

### 기본 원칙

1. 모음을 제거하고 자음으로 축약 (원칙)
2. 축약 시 인식이 어려우면 예외 허용
3. 앞자리 2~4자로 축약
4. 단어가 짧거나(3자 이하) 축약 시 애매하면 전체 텍스트 사용
5. 업계 통용 약어가 있으면 우선 사용

### 단어유형

표준단어사전은 **수식어**와 **분류어** 두 가지 유형으로 구분한다.

| 유형 | 역할 | 컬럼명 위치 | 예시 |
|------|------|-------------|------|
| 수식어 | 대상/행위를 수식 | 앞쪽 (접두) | campaign, brand, media |
| 분류어 | 데이터 성격을 분류 | 끝쪽 (접미) | no, nm, cd, cnt, amt |

컬럼명은 `{수식어}_{분류어}` 패턴으로 조합한다. 분류어는 도메인과 1:1 매핑되어 데이터 타입을 결정한다.

### 수식어 약어 예시 (MAMS 프로젝트 기준 — 프로젝트별 사전으로 대체 가능)

| 한글 | 영문 | 약어 | 규칙 적용 |
|------|------|------|-----------|
| 회사 | Company | company | 전체 유지 |
| 브랜드 | Brand | brand | 전체 유지 |
| 회원 | Member | member | 전체 유지 |
| 매체 | Media | media | 전체 유지 |
| 계정 | Account | account | 전체 유지 |
| 캠페인 | Campaign | campaign | 전체 유지 |
| 광고 | Advertisement | ad | 업계 통용 |
| 광고그룹 | Ad Group | adgrp | 모음 제거 |
| 키워드 | Keyword | kwd | 모음 제거 |
| 소재 | Creative | crtv | 모음 제거 |
| 성과 | Performance | perf | 앞 4자 |
| 노출 | Impression | impr | 앞 4자 |
| 클릭 | Click | clk | 모음 제거 |
| 전환 | Conversion | cnvr | 모음 제거+축약 |
| 매출 | Revenue | rev | 앞 3자 |
| 광고비 | Ad Cost | ad_cost | 복합어 |
| 일별 | Daily | daily | 전체 유지 |
| 집계 | Summary | smry | 모음 제거 |
| 원시 | Raw | raw | 전체 유지 (짧음) |
| 사용자 | User | user | 전체 유지 |
| 역할 | Role | role | 전체 유지 (짧음) |
| 메뉴 | Menu | menu | 전체 유지 |
| 알림 | Notification | noti | 앞 4자 |
| 감사 | Audit | audit | 전체 유지 |
| 배치 | Batch | batch | 전체 유지 |
| 수집 | Collection | clct | 모음 제거 |
| 로그 | Log | log | 전체 유지 (짧음) |
| 공통 | Common | cmn | 모음 제거 |
| 게시판 | Board | brd | 모음 제거 |
| 게시글 | Post | post | 전체 유지 |
| 배너 | Banner | banner | 전체 유지 |
| 리포트 | Report | rpt | 모음 제거 |
| 설정 | Config | cfg | 모음 제거 |
| 속성 | Attribute | attr | 앞 4자 |
| 태그 | Tag | tag | 전체 유지 (짧음) |
| 권한 | Permission | perm | 앞 4자 |
| 응답 | Response | rsp | 모음 제거 |
| 대상 | Target | target | 전체 유지 |
| 정의 | Definition | def | 앞 3자 |
| 시작 | Start | start | 전체 유지 |
| 종료 | End | end | 전체 유지 (짧음) |
| 생성 | Create | create | 전체 유지 |
| 수정 | Modify | modify | 전체 유지 |
| 삭제 | Delete | delete | 전체 유지 |
| 사용 | Use | use | 전체 유지 (짧음) |
| 총 | Total | tot | 앞 3자 |
| 외부 | External | ext | 업계 통용 |
| 텍스트 | Text | txt | 모음 제거 |
| 인증 | Auth | auth | 업계 통용 |
| VAT포함 | Including VAT | inc_vat | 복합어 |
| VAT별도 | Excluding VAT | exc_vat | 복합어 |
| 그룹 | Group | grp | 모음 제거 |
| 값 | Value | val | 앞 3자 |
| GA | Google Analytics | ga | 업계 통용 |
| 정렬 | Sort | sort | 전체 유지 |
| 레벨 | Level | lvl | 모음 제거 |
| 엔티티 | Entity | entity | 전체 유지 |
| 액션 | Action | act | 앞 3자 |
| 사업자 | Business | bz | 모음 제거+축약 |
| 등록 | Registration | reg | 앞 3자 |
| 대표자 | Representative | repr | 앞 4자 |
| 주소 | Address | addr | 모음 제거 |
| 세금 | Tax | tax | 전체 유지 (짧음) |
| 계산서 | Invoice | invc | 모음 제거 |
| 변경 | Change | chg | 모음 제거 |
| 유형 | Type | tp | 모음 제거+축약 |
| 직책 | Position | pstn | 모음 제거 |
| 최근 | Recent | rcnt | 모음 제거 |
| 로그인 | Login | login | 전체 유지 |
| 약관 | Terms | terms | 전체 유지 |
| 동의 | Agreement | agree | 앞 5자 |
| 정보 | Info | info | 업계 통용 |
| 영문 | English | eng | 앞 3자 |
| 비용 | Cost | cost | 전체 유지 |
| 단위 | Unit | unit | 전체 유지 |
| 통화 | Currency | crcy | 모음 제거 |
| 방식 | Method | mthd | 모음 제거 |
| 토큰 | Token | tkn | 모음 제거 |
| 만료 | Expiry | expr | 앞 4자 |
| 담당자 | Manager | mng | 모음 제거+축약 |
| 예산 | Budget | budget | 전체 유지 |
| 동기화 | Sync | sync | 업계 통용 |
| 타겟팅 | Targeting | trgtng | 모음 제거 |
| 제목 | Headline | headline | 전체 유지 |
| 설명문구 | Description Text | desc_txt | 복합어 |
| 이미지 | Image | img | 모음 제거 |
| 동영상 | Video | video | 전체 유지 |
| 썸네일 | Thumbnail | thmb | 모음 제거 |
| 랜딩 | Landing | landing | 전체 유지 |
| 표시 | Display | display | 전체 유지 |
| PC | PC | pc | 업계 통용 |
| 모바일 | Mobile | mobile | 전체 유지 |
| 상품 | Product | product | 전체 유지 |
| CTA | Call To Action | cta | 업계 통용 |
| 매칭 | Matching | mtch | 모음 제거 |
| 디바이스 | Device | devc | 모음 제거 |
| 도달 | Reach | reach | 전체 유지 |
| 빈도 | Frequency | freq | 앞 4자 |
| 조회 | View | view | 전체 유지 |
| 환율 | Exchange Rate | exch | 앞 4자 |
| 부서 | Department | dept | 앞 4자 |
| 템플릿 | Template | tmpl | 모음 제거 |
| 채널 | Channel | chnl | 모음 제거 |
| 긴급도 | Urgency | urgc | 모음 제거+축약 |
| 구독 | Subscribe | subscribe | 전체 유지 |
| 너비 | Width | wdth | 모음 제거 |
| 높이 | Height | hght | 모음 제거 |
| 목록 | List | list | 전체 유지 |
| 태깅 | Tagging | tagng | 모음 제거 |

### 분류어 약어 (도메인 연동 — 범용 표준)

분류어는 도메인과 1:1 매핑되어 데이터 타입(MySQL/Oracle/PostgreSQL)을 결정한다.

> 상세 DBMS별 타입 매핑(PostgreSQL/MSSQL/Oracle 포함)은 `db-type-mapping.md`를 참조한다.

| 한글 | 영문 | 약어 | 도메인 | MySQL 9 타입 |
|------|------|------|--------|-------------|
| 번호 | Number | no | D001 | BIGINT UNSIGNED |
| 명 | Name | nm | D002 | VARCHAR(200) |
| 코드 | Code | cd | D003 | VARCHAR(20) |
| 식별자 | Identifier | id | D004 | VARCHAR(100) |
| 수 | Count | cnt | D005 | INT |
| 숫자 | Numeric | num | D006 | INT |
| 금액 | Amount | amt | D007 | DECIMAL(18,4) |
| 율 | Rate | rt | D008 | DECIMAL(10,4) |
| 일시 | Datetime | dt | D009 | DATETIME |
| 일자 | Date | date | D010 | DATE |
| 여부 | YesNo | yn | D011 | CHAR(1) |
| 내용 | Content | cn | D012 | TEXT |
| 설명 | Description | desc | D013 | VARCHAR(500) |
| 구분 | Classification | clsf | D014 | VARCHAR(20) |
| URL | URL | url | D015 | VARCHAR(500) |
| 수량 | Quantity | qty | D016 | INT |
| 비밀번호 | Password | pw | D017 | VARCHAR(200) |
| 순서 | Order | ord | D018 | INT |
| 퍼센트 | Percent | pct | D019 | DECIMAL(5,2) |
| 이메일 | Email | email | D020 | VARCHAR(100) |
| 휴대폰 | Mobile | mobile | D021 | VARCHAR(20) |
| UUID | UUID | uuid | D022 | BINARY(16) |
| 상세 | Detail | dtl | D002 | VARCHAR(200) |
| 일예산 | Daily Budget | daily_bdgt | D007 | DECIMAL(18,4) |

---

## 2. 테이블 명명규칙

### 스키마 접두사

- 프로젝트별 고유 접두사를 사용하여 다른 시스템 테이블과의 네이밍 충돌을 방지한다
- **스키마가 미확정인 프로젝트에서는 반드시 사용자에게 확인 후 진행한다**
- 프로젝트별 스키마 접두사는 `.opal/AGENT.md`의 "프로젝트 규칙 > DB 스키마" 섹션에서 확인한다

### 물리 테이블명

패턴: `{스키마}_{주제영역}_{엔티티}_{유형}`

- 테이블명은 **대문자 UPPER_SNAKE_CASE**를 사용한다

| 요소 | 위치 | 규칙 | 예시 |
|------|------|------|------|
| 스키마 | 1번째 | 프로젝트 약어, 고정 (대문자) | PRJ, SVC 등 프로젝트별 확정 |
| 주제영역 | 2번째 | 업무 영역 약어, 유일해야 함 (대문자 2자리) | MB, CP, CF, SM, CM |
| 엔티티 | 3번째 | 대상 객체, UPPER_SNAKE_CASE | CAMPAIGN, MEMBER |
| 유형 | 4번째 | 테이블 성격 (대문자) | BSC, DTL, HST, MAP, STAT, CD |

### 유형 접미어

| 접미어 | 의미 | 설명 | 예시 |
|--------|------|------|------|
| BSC | 기본(마스터) | 핵심 엔티티 | {SCHEMA}_CP_CAMPAIGN_BSC |
| DTL | 상세 | 부가 정보 | {SCHEMA}_CF_RAW_DATA_DTL |
| HST | 이력 | 변경 추적 | {SCHEMA}_CF_CLCT_LOG_HST |
| MAP | 매핑 | N:M 관계 해소 | {SCHEMA}_MB_MEMBER_BRAND_MAP |
| STAT | 통계/집계 | 집계 데이터 | {SCHEMA}_CF_DAILY_PERF_STAT |
| CD | 코드 | 공통코드 | {SCHEMA}_CM_CMN_CD |

### 한글 테이블명

패턴: `{수식어} {유형한글} 정보`

- 끝에 반드시 **"정보"**를 붙인다
- 유형한글: 기본, 상세, 이력, 매핑, 통계, 코드

| 물리명 (예시) | 한글명 |
|--------|--------|
| {SCHEMA}_MB_COMPANY_BSC | 회사 기본 정보 |
| {SCHEMA}_MB_BRAND_BSC | 브랜드 기본 정보 |
| {SCHEMA}_MB_MEMBER_BSC | 회원 기본 정보 |
| {SCHEMA}_MB_MEMBER_BRAND_MAP | 회원브랜드 매핑 정보 |
| {SCHEMA}_CP_CAMPAIGN_BSC | 캠페인 기본 정보 |
| {SCHEMA}_CF_RAW_DATA_DTL | 원시데이터 상세 정보 |
| {SCHEMA}_CF_CLCT_LOG_HST | 수집로그 이력 정보 |
| {SCHEMA}_CF_DAILY_PERF_STAT | 일별성과집계 통계 정보 |
| {SCHEMA}_CM_CMN_CD_GRP_CD | 공통코드그룹 코드 정보 |

---

## 3. 컬럼 명명규칙

### 물리 컬럼명

패턴: `{수식어약어}_{분류어약어}`

- 표준용어사전의 영문약어를 소문자로 사용
- 단어와 단어 사이는 `_`로 연결
- 분류어가 데이터 타입을 결정한다 (도메인 매핑)

| 한글용어 | 물리 컬럼명 | 구성 | 도메인 |
|----------|------------|------|--------|
| 캠페인번호 | campaign_no | campaign + no | D001 |
| 캠페인명 | campaign_nm | campaign + nm | D002 |
| 캠페인식별자 | campaign_id | campaign + id | D004 |
| 매체코드 | media_cd | media + cd | D003 |
| 광고비금액(VAT별도) | cost_exc_vat_amt | ad_cost + exc_vat + amt | D007 |
| 노출수 | impr_cnt | impr + cnt | D005 |
| 전환율 | cnvr_rt | cnvr + rt | D008 |
| 시작일자 | start_date | start + date | D010 |
| 외부식별자 | ext_id | ext + id | D004 |
| 생성일시 | create_dt | create + dt | D009 |
| 수정일시 | modify_dt | modify + dt | D009 |
| 생성자번호 | create_user_no | create + user + no | D001 |
| 수정자번호 | modify_user_no | modify + user + no | D001 |
| 사용여부 | use_yn | use + yn | D011 |
| 삭제여부 | delete_yn | delete + yn | D011 |
| 정렬순서 | sort_ord | sort + ord | D018 |
| 상태코드 | state_cd | state + cd | D003 |
| 동기화일시 | sync_dt | sync + dt | D009 |

### 오딧(Audit) 컬럼 표준

모든 테이블에 공통 적용되는 4개 오딧 컬럼. 전부 NULL 허용.

| 컬럼명 | 한글명 | 타입 | 비고 |
|--------|--------|------|------|
| create_dt | 생성일시 | DATETIME | NULL 허용 |
| create_user_no | 생성자번호 | BIGINT UNSIGNED | NULL 허용 (시스템 자동 생성 대응) |
| modify_dt | 수정일시 | DATETIME | NULL 허용 |
| modify_user_no | 수정자번호 | BIGINT UNSIGNED | NULL 허용 (매체 API 자동 수집 대응) |

---

## 4. 제약조건 명명규칙

| 제약조건 | 패턴 | 예시 |
|---------|------|------|
| Primary Key | `PK_{테이블약칭}` | PK_CP_CAMPAIGN_BSC |
| Foreign Key | `FK_{자식약칭}_{부모약칭}` | FK_CP_CAMPAIGN_BSC_MB_COMPANY_BSC |
| Unique Index | `UQ_{테이블약칭}_{컬럼들}` | UQ_CP_CAMPAIGN_MEDIA_EXT_ID |
| Index | `IDX_{테이블약칭}_{컬럼들}` | IDX_CP_CAMPAIGN_BSC_COMPANY_NO |

---

## 5. 주제영역(SA) 약어 규칙

- 각 주제영역 약어는 **대문자 2자리**를 기본으로 한다
- 프로젝트 내에서 **유일**해야 하며, 충돌 시 3자리까지 허용
- **새로운 주제영역이 필요할 때는 반드시 사용자에게 약어를 확인받는다** (임의 생성 금지)

### 등록된 주제영역

프로젝트별 SA 코드는 `.opal/AGENT.md`의 "프로젝트 규칙 > 주제영역(SA) 코드" 섹션이 원본(source of truth)이다.

### 신규 주제영역 등록 절차

1. 기존 약어와 중복되지 않는지 확인
2. 해당 약어가 다른 의미로 오해될 소지가 없는지 확인
3. **사용자에게 약어 후보를 제시하고 확정받은 후 등록**
