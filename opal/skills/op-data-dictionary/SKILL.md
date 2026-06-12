---
name: op-data-dictionary
description: |
  **표준사전·표준코드 관리(CRUD) 단계 스킬**. 표준단어사전·도메인사전·코드사전 3종 md SSOT를 작성·검증·보강하고, xlsx 뷰를 단방향 export한다.
  반드시 이 스킬을 사용해야 하는 상황: 오케스트레이터(opal-pilot-data-design)가 DICT 단계를 디스패치할 때.
  필수 입력: 프로젝트 컨텍스트 (서비스 기획서·기존 사전·스키마 등 중 1종 이상). 보장 출력: 표준단어사전.md / 도메인사전.md / 코드사전.md (+ xlsx export 선택).
version: 1.0
---

# 표준사전 관리 (DICT)

## 실행 컨텍스트

이 스킬은 `opal-db-agent` 워커 에이전트의 컨텍스트에서 실행된다.
오케스트레이터(`opal-pilot-data-design`)가 DICT 단계를 디스패치하면, `opal-db-agent`가 이 스킬을 읽고 프로세스를 따른다.

> **[MUST]** 산출물 작성·검증 시 `opal/core/references/harness/citation-rules.md`를 Read하여 규칙(근거 제시 원칙 / 트랙별 매트릭스 / [MUST] 토큰 / 영역 간 용어 일관성 / decision_required 계약)을 준수한다.

> **[MUST]** `docs/proposals/opal-data-design.md` §3.2.2: "수정은 md에서만. xlsx는 op-data-dictionary가 xlsx-tool로 md→xlsx export하여 생성하는 파생물(원본 아님). 역방향(xlsx 수정→md) 금지 — SSOT 혼선 방지."

> **[MUST]** 사전 저장 경로는 하드코딩하지 않는다. `docs/PROJECT.md`에 등록된 `{설계}` 변수(설계 산출물 루트)를 읽어 `{설계}/사전/`으로 해소한다. PROJECT.md에 경로가 미등록된 경우: ① 루트에 `200.설계/` 디렉토리 탐색 → ② 없으면 default `200.설계/210.사전/` 제안 후 사용자 확인. 결과를 TASK.md "산출물 저장 경로" 항목과 PROJECT.md에 등록한다.

---

## 페르소나

`opal/agents/opal-db-agent/personas/db-architect.md`를 Read하여 DB 전문 지식과 행동 규칙을 적용한다.
(표준사전 준수 / 명명규칙 정합 / 타입 매핑 SSOT 유지 원칙 포함)

---

## 입력/출력

| 항목 | 설명 |
|------|------|
| **필수 입력** | 프로젝트 컨텍스트 (서비스 기획서 / 기존 사전 md / ERD·스키마 중 1종 이상) |
| **선택 입력** | 기존 `표준단어사전.md`, `도메인사전.md`, `코드사전.md` (주입 시 검증·보강 모드로 동작) |
| **보장 출력** | `{설계}/사전/표준단어사전.md`, `{설계}/사전/도메인사전.md`, `{설계}/사전/코드사전.md` |
| **선택 출력** | `{설계}/사전/표준단어사전.xlsx`, `{설계}/사전/도메인사전.xlsx`, `{설계}/사전/코드사전.xlsx` (xlsx-tool export) |
| **제외 출력** | xlsx→md 역방향 import — 이번 범위 미구현 (향후 검토 대상, U-4 확정) |

---

## 모드 분기 (U-2 확정)

DICT 단계는 항상 실행한다. 기존 사전 주입 여부에 따라 모드가 자동 분기된다.

| 조건 | 모드 | 동작 |
|------|------|------|
| 기존 사전 없음 | **신규 작성 모드** | 사전 3종을 처음부터 작성 |
| 기존 사전 주입됨 + 커버리지 충분 | **검증·보강 모드** | 기존 사전을 검증하고 미등록 용어만 추가 |
| 기존 사전 주입됨 + 커버리지 불충분 | **신규 작성 모드** (보강) | 기존 사전 기반으로 누락 항목 전면 보완 |

---

## 프로세스

### Step 1. references 로딩

1. `opal/skills/op-data-dictionary/references/naming-convention.md` Read — 수식어/분류어 약어·명명규칙 숙지
2. `opal/skills/op-data-dictionary/references/db-type-mapping.md` Read — D001~D022 DBMS별 타입 매핑 숙지

### Step 2. 프로젝트 컨텍스트 로딩

1. `docs/PROJECT.md` 에서 `{설계}` 경로 변수 확인
2. 서비스 기획서(`docs/SERVICE.md` / `docs/SPEC.md` / `docs/PRD.md`) 중 존재하는 파일 Read
3. 기존 사전 파일이 주입된 경우 Read → 모드 결정 (위 모드 분기 참조)
4. 기존 ERD·스키마(`docs/db/schema.dbml` 등) 존재 시 Read (속성명 역추적)

### Step 3. 표준단어사전.md 작성/보강

**파일 경로**: `{설계}/사전/표준단어사전.md`

**md 스키마** (수식어 + 분류어 두 섹션):

```markdown
# 표준단어사전

## 수식어

| 한글 | 영문 | 약어 | 규칙 | 도메인 | 비고 |
|------|------|------|------|--------|------|
| 회사 | Company | company | 전체 유지 | - | |

## 분류어

| 한글 | 영문 | 약어 | 도메인 | 비고 |
|------|------|------|--------|------|
| 번호 | Number | no | D001 | PK에 사용 |
```

- **신규 작성 모드**: naming-convention.md §1 수식어·분류어 기준 행을 초기 데이터로 사용 + 서비스 기획서에서 도출된 프로젝트 특화 용어 추가
- **검증·보강 모드**: 기존 사전 구조 유지 + 서비스 기획서 신규 용어 차분(diff) 후 미등록만 추가

### Step 4. 도메인사전.md 작성/보강

**파일 경로**: `{설계}/사전/도메인사전.md`

**md 스키마** (D001~D022 + 프로젝트 확장 도메인):

```markdown
# 도메인사전

| 도메인 | 한글 | 약어 | MySQL 9 | PostgreSQL 16 | MSSQL | Oracle 19c | 비고 |
|--------|------|------|---------|--------------|-------|-----------|------|
| D001 | 번호 | no | BIGINT UNSIGNED | BIGINT | BIGINT | NUMBER(19) | |
```

- **데이터 원천**: `db-type-mapping.md` 매핑표를 기준 행으로 복사 후 프로젝트 DBMS만 유지 또는 전체 유지
- 프로젝트 특화 도메인(D023~) 필요 시 번호 연장하여 추가

### Step 5. 코드사전.md 작성/보강

**파일 경로**: `{설계}/사전/코드사전.md`

**md 스키마** (코드성 컬럼 CHECK 값 정의):

```markdown
# 코드사전

| 코드그룹 | 한글명 | 코드값 | 코드명 | 비고 |
|---------|--------|--------|--------|------|
| USE_YN | 사용여부 | Y | 사용 | D011 |
| USE_YN | 사용여부 | N | 미사용 | D011 |
| STATE_CD | 상태코드 | ACTIVE | 활성 | D003 |
```

- 서비스 기획서에서 코드성 컬럼(분류어 `_cd`, `_yn`, `_clsf`, `_tp` 등)을 도출
- 각 코드그룹에 대해 허용값 전체 열거

### Step 6. 품질 검증

완료 전 아래 항목을 자체 점검한다:

- [ ] 표준단어사전: 수식어/분류어 약어가 naming-convention.md와 충돌 없음
- [ ] 도메인사전: D001~D022 전체 행 존재 + 프로젝트 타겟 DBMS 타입 채워짐
- [ ] 코드사전: 코드성 컬럼 대상 코드그룹 누락 없음
- [ ] 사전 3종이 동일 경로(`{설계}/사전/`)에 저장됨
- [ ] 역방향 import 미수행 (md→xlsx 단방향 준수)

### Step 7. xlsx Export (선택)

오케스트레이터 또는 사용자가 xlsx export를 요청하는 경우에만 실행한다.

1. `opal-db-agent`의 xlsx-tool을 사용하여 md 테이블 → xlsx 변환
2. 저장 위치: `{설계}/사전/표준단어사전.xlsx`, `도메인사전.xlsx`, `코드사전.xlsx`
3. xlsx 파일은 **파생물** — md가 SSOT. xlsx 수정 금지.

---

## 활용 MCP

| 상황 | 활용 수단 |
|------|-----------|
| xlsx-tool export | `opal-db-agent` 보유 xlsx-tool 사용 |
| 복잡한 도메인 모델링 분해 | `mcp__sequential-thinking__sequentialthinking` |
| DBMS별 타입 최신 문서 확인 | `mcp__context7__resolve-library-id` → `mcp__context7__query-docs` |

---

## 저장 경로

| 산출물 | 경로 | 형식 |
|--------|------|------|
| 표준단어사전 | `{설계}/사전/표준단어사전.md` | md (SSOT) |
| 도메인사전 | `{설계}/사전/도메인사전.md` | md (SSOT) |
| 코드사전 | `{설계}/사전/코드사전.md` | md (SSOT) |
| 표준단어사전 뷰 | `{설계}/사전/표준단어사전.xlsx` | xlsx (파생물) |
| 도메인사전 뷰 | `{설계}/사전/도메인사전.xlsx` | xlsx (파생물) |
| 코드사전 뷰 | `{설계}/사전/코드사전.xlsx` | xlsx (파생물) |

> `{설계}` = `docs/PROJECT.md` 등록 변수. default: `200.설계` (프로젝트 루트 기준 상대경로)
> 사전 default 경로: `200.설계/210.사전/`

---

## 품질 체크리스트

- [ ] 모든 Step 체크박스 완료
- [ ] 사전 3종 파일 존재 + 내용 구조 정합 (섹션·컬럼 누락 없음)
- [ ] `{설계}` 경로 변수 해소 완료 (하드코딩 없음)
- [ ] md→xlsx export 단방향 준수 (역방향 0)
- [ ] db-type-mapping.md 기준 도메인사전 D001~D022 전체 행 포함
- [ ] 코드사전 코드그룹 CHECK 허용값 완전 열거
- [ ] naming-convention.md 충돌 없음
- [ ] 하드코딩 시크릿 없음

---

## 변경이력

| 버전 | 일시(KST) | 변경 내용 |
|------|----------|----------|
| 1.0 | 2026-06-12 | 최초 작성 — F-001 op-data-dictionary 신설 (tasks/019-260612-opd-opal-pilot-data-design PLAN §3.1) |
