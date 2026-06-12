# PLAN: opal-pilot-data-design — DB 설계 OPAL 내재화 구현

> 작성일: 2026-06-12 | 입력: TASK.md, ANALYSIS.md (선택)
> 모드: Multi-Feature

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

DB 설계 업무를 OPAL 표준 3층 체계(pilot + 단계 스킬 + 에이전트)로 내재화한다. 오케스트레이터 `opal-pilot-data-design`(opdd)와 단계 스킬 3종(op-data-dictionary/op-data-model/op-data-ddl)을 신설하고, standalone `erd-modeler`를 분해 이관하며 `opal-db-agent`를 사전·코드 CRUD 주체로 확장하고, 레지스트리·PROJECT.md에 등재한다. 순수 문서·스킬 작업이며 코드 동작 검증 대상은 레지스트리/state-tool 연동·깨진 참조 해소로 한정된다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | op-data-dictionary 신설 (DICT + references 이관 + db-type-mapping 신설) | R-2(DICT), R-3(references 이관 일부) | P0 | 없음 |
| F-002 | opal-pilot-data-design 오케스트레이터 신설 | R-1 | P0 | F-001 |
| F-003 | op-data-model 신설 (MODEL 3모드 + references 이관) | R-2(MODEL), R-3(이관 일부) | P0 | F-001 |
| F-004 | op-data-ddl 신설 (DDL/MIGRATION + references 이관) | R-2(DDL), R-3(이관 일부) | P0 | F-001 |
| F-005 | opal-db-agent 확장 | R-4 | P1 | F-001, F-002, F-003, F-004 |
| F-006 | 레지스트리·PROJECT.md 등록 | R-5 | P1 | F-002, F-003, F-004 |
| F-007 | erd-modeler deprecate + 깨진 참조 해소 + //erm alias 하위호환 | R-3(deprecate) | P1 | F-003, F-006 |
| F-008 | install 배포 자동 확인 (R-6 축소) | R-6 | P2 | F-001~F-004 |

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 (DICT) ─┬─ F-002 (pilot) ─┐
              ├─ F-003 (model) ─┼─ F-006 (registry/PROJECT) ─ F-007 (erd deprecate)
              └─ F-004 (ddl) ───┘
              │
              └─ F-005 (db-agent 확장)   [F-002~F-004 완료 후]
F-001~F-004 ──── F-008 (install 확인)
```

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨. 이 태스크는 문서·스킬 작업이므로 가설은 "구조 정합/참조 무결성/레지스트리 파싱" 계약 중심이다.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-006 레지스트리 JSON | JSON 파싱 유효성(쉼표·중괄호) 깨지면 skill-registry 전체 로드 실패 | P0 | L1(파싱) + L2(skill-registry match) | S-1 후보 |
| H-2 | F-006 opdd alias 등록 | `opdd` alias 충돌 시 트리거 라우팅 오류 | P1 | L2(match "opdd" 단일 해소) | S-2 후보 |
| H-3 | F-002 pilot STATE 행 | `state-tool init --skill opdd --rows-from` 파싱 실패 시 STATE.md 생성 불가 | P1 | L2(state-tool init 실행) | S-3 후보 |
| H-4 | F-007 erd-modeler 깨진 참조 | `../data-dictionary/...` 미해소 시 erm 호출 시 참조 깨짐 잔존 | P1 | L1(grep 잔존 0) | S-4 후보 |
| H-5 | F-001 references 이관 + db-type-mapping | 이관 누락·신규 타입표 불완전 시 모델링 SSOT 공백 | P1 | L1(파일 존재 + 내용 매핑 대조) | S-5 후보 |
| H-6 | F-005 db-agent 확장 | 기존 모델링/마이그레이션 역할 회귀 손실 | P2 | L1(기존 섹션 보존 diff) | S-6 후보 |
| R-T1 | 용어 일관성 — 검토서 `{설계}/사전/` vs db-agent `docs/db/` 경로 토큰 불일치 | 사전·ERD 저장 경로 SSOT 혼선 | P1 | decision_required 후보 → **U-1에서 확정** | - |

---

## 2. 기능별 분석

### F-001: op-data-dictionary 신설

#### 2.1.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/op-data-dictionary/SKILL.md` | DICT 단계 스킬 (사전·코드 CRUD, md SSOT/xlsx export) | 신규 |
| 가이드 | `opal/skills/op-data-dictionary/references/naming-convention.md` | 수식어/분류어·도메인 타입표 이관본 | 신규(이관) |
| 가이드 | `opal/skills/op-data-dictionary/references/db-type-mapping.md` | 도메인 D001~ ↔ DBMS별 타입 매핑 (PG/MSSQL/Oracle 확장) | 신규 |
| 에이전트 | `opal/agents/opal-db-agent/personas/data-steward.md` | DICT 전용 페르소나 (선택 — §6 참조) | 신규 |

#### 2.1.2 현재 구현
- erd-modeler가 사전을 **읽기 전용**으로 참조(`skills/erd-modeler/SKILL.md:55-79` §3 사전 참조 규칙 3단계 폴백). CRUD 주체 없음 (→ D-1 §2).
- `skills/erd-modeler/references/naming-convention.md`에 수식어 약어(§1), 분류어 약어(§1 143-176, 도메인 D001~D022 + MySQL 9 타입만), 테이블/컬럼/제약/주제영역 명명규칙(§2~§5) 존재. **MySQL 9 타입만 매핑** — PG/MSSQL/Oracle 부재 (→ D-3).
- 검토서 §3.2.2: md SSOT(`표준단어사전.md`/`도메인사전.md`/`코드사전.md`) + xlsx 뷰 단방향(md→export). db-agent가 xlsx-tool 보유 (→ D-1 §3.2.2).

#### 2.1.3 영향 범위
- F-002(pilot DICT 단계)·F-003(MODEL 속성명 SSOT)·F-004(DDL 타입 매핑)가 DICT references를 소비한다.
- F-007 erd-modeler 깨진 참조(`../data-dictionary/references/naming-convention.md`·`db-type-mapping.md`)의 해소 목적지가 이 스킬 references이다.

---

### F-002: opal-pilot-data-design 오케스트레이터 신설

#### 2.2.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 오케스트레이터 | `opal/skills/opal-pilot-data-design/SKILL.md` | opdd 파이프라인 조율(Harness/STEP/STATE 행/3-way 모드/PM Gate) | 신규 |

#### 2.2.2 현재 구현
- 템플릿 원천: `opal/skills/opal-pilot-dev/SKILL.md` (391줄). 구조: `# 제목 → ## Harness → ## STEP N → ## STATE.md 도메인 치환값 → ## PM Gate 점검 목록 → ## Agentic/Semi-Agentic 모드 → ## 변경이력` (→ D-5).
- STATE 행 SSOT 패턴: §STATE.md 도메인 치환값에 `| # | 단계 | 항목 | 상태 | 시점 |` 테이블을 두고, `state-tool init --skill <alias> --rows-from <SKILL.md>`가 파싱 (`opal/skills/opal-pilot-dev/SKILL.md:266-289`) (→ D-5).
- 검토서 §3.5에 opdd STATE 행 15행(semi-agentic) 명시 (→ D-1 §3.5).

#### 2.2.3 영향 범위
- DICT/MODEL/DDL 워커를 디스패치하는 주체. 단계별로 `opal-db-agent` 단일 에이전트에 디스패치(검토서 §3.1 단일 도메인).
- DDL이 MODEL 물리 완료 후만 실행 — state-tool stage-transition guard 의존 (→ D-1 §3.2).

---

### F-003: op-data-model 신설 (MODEL 3모드)

#### 2.3.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/op-data-model/SKILL.md` | concept/logical/physical 3모드 분리 발동 + 모드별 산출물 양식 | 신규 |
| 가이드 | `opal/skills/op-data-model/references/mermaid-guide.md` | 개념/논리 Mermaid 문법 이관본 | 신규(이관) |

#### 2.3.2 현재 구현
- erd-modeler §4 모델링 로직: `skills/erd-modeler/SKILL.md:82-191` (4.1 3단계 흐름 / 4.2 개념 / 4.3 논리 / 4.4 물리 / 4.5 명명규칙). 출력 폴더 구조 `:35-51` (개념모델링/논리모델링/물리모델링) (→ D-2).
- 검토서 §3.2.1 MODEL 3모드 양식표: concept(`{설계}/개념모델링/ERD_{영역}.mermaid`+`.md`) / logical(`...논리.mermaid`+`.md`) / physical(`{설계}/물리모델링/{프로젝트}.dbml`) (→ D-1 §3.2.1).
- `skills/erd-modeler/references/mermaid-guide.md` 존재 (5638 bytes).

#### 2.3.3 영향 범위
- 논리 모드 속성명이 DICT 표준사전 용어 SSOT를 소비(F-001 의존). 물리 모드 산출물(DBML)이 F-004 DDL 입력.
- `//erm` alias 하위호환의 목적지(F-007).

---

### F-004: op-data-ddl 신설 (DDL/MIGRATION)

#### 2.4.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/op-data-ddl/SKILL.md` | DBML→DDL 추출 + ORM 마이그레이션 (물리 입력 전제) | 신규 |
| 가이드 | `opal/skills/op-data-ddl/references/dbml-guide.md` | 물리 DBML 문법 이관본 | 신규(이관) |

#### 2.4.2 현재 구현
- erd-modeler §5 DDL 로직: `skills/erd-modeler/SKILL.md:194-253` (5.1 DBML→DDL `dbml2sql` / 5.2 CLI 없이 생성 / 5.3 역공학 `sql2dbml`) (→ D-2).
- `skills/erd-modeler/references/dbml-guide.md` 존재 (6659 bytes).
- 타입 매핑은 도메인사전 참조 — F-001 db-type-mapping.md 소비.

#### 2.4.3 영향 범위
- MODEL 물리(DBML) 산출물 입력 전제 (검토서 §3.2 DDL 의존 제약 — 물리 완료 후만) (→ D-1 §3.2).
- DBML CLI 외부 도구(`@dbml/cli`) 의존 — CLI 부재 시 수동 폴백(§5.2 계승).

---

### F-005: opal-db-agent 확장

#### 2.5.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 에이전트 | `opal/agents/opal-db-agent/AGENT.md` | description·실행프로세스에 DICT(사전·코드 CRUD) + op-data-* 경로 인지 추가 | 수정 |

#### 2.5.2 현재 구현
- description: "DB 모델 설계+구현 전문 워커" — 데이터 모델링(개념/논리/물리) + 마이그레이션 정의 (`opal/agents/opal-db-agent/AGENT.md:3-6`) (→ D-4).
- 실행 프로세스 8단계, 표준사전 주입 시 xlsx-tool로 읽기(`:24`), MCP/도구 표(`:60-65`), model 오버라이드 표(`:96-101`) (→ D-4).
- 사전을 "읽어 활용"만 함 — CRUD 주체 부재 (검토서 §2) (→ D-1 §2).

#### 2.5.3 영향 범위
- ANALYSIS §3 확장 지점 6종: description / 실행 프로세스 DICT 단계 / 자체 로드 문서(md·xlsx 사전) / MCP·도구(xlsx export) / op-data-* 스킬 경로 인지 / "단계별 스킬 디스패치 인식" 신규 섹션 (→ ANALYSIS §3).
- 기존 모델링/마이그레이션 역할 보존 필수(H-6 회귀 리스크).

---

### F-006: 레지스트리·PROJECT.md 등록

#### 2.6.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 레지스트리 | `opal/core/references/opal-skills-registry.json` | opdd(opal-pilot 그룹) + op-data 그룹 3종 등록 | 수정 |
| 문서 | `docs/PROJECT.md` | 주요 컴포넌트 표에 Data Design 파이프라인 행 추가 | 수정 |

#### 2.6.2 현재 구현
- 레지스트리 v3.4.0. `groups.opal-pilot[]` (7개), `groups.op-dev[]`, `groups.op-sdd[]`, `groups.op-task[]`, `groups.standalone[]`(erd-modeler 포함 `:444-456`), `groups.opal[]` (→ D-6).
- opal-pilot 항목 스키마: `name/alias/description/triggers[]/paths[]/domain/pipeline` (`:7-22`). op-dev 단계스킬 스키마: `name/alias/description/triggers[]/paths[]/stage/dispatched_by[]` (`:120-135`) (→ D-6).
- `opdd` alias 미사용 — grep 충돌 없음(재확인 필요).

#### 2.6.3 영향 범위
- skill-registry match·state-tool init이 이 JSON을 소비. 파싱 깨지면 전체 라우팅 실패(H-1 P0).
- 신규 그룹 `op-data` 추가 또는 기존 패턴 따라 별도 그룹 키 신설.

---

### F-007: erd-modeler deprecate + 깨진 참조 해소 + //erm alias

#### 2.7.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `skills/erd-modeler/SKILL.md` | deprecate 안내 + 깨진 참조(`:275-276`) 해소 + //erm 하위호환 명시 | 수정 |
| 레지스트리 | `opal/core/references/opal-skills-registry.json` | erd-modeler 항목에 deprecated 표기 + //erm → op-data-model alias 라우팅 (F-006와 병합) | 수정 |

#### 2.7.2 현재 구현
- `skills/erd-modeler/SKILL.md:275-276` 깨진 참조: `../data-dictionary/references/naming-convention.md`·`db-type-mapping.md` — data-dictionary 디렉토리 부재(유령) (→ D-2, D-1 §2).
- standalone 레지스트리 항목 `erd-modeler`/alias `erm` (`:444-456`) (→ D-6).
- 검토서 §4: erd-modeler deprecate, `//erm`은 op-data-model 단독 호출 alias로 하위호환 (→ D-1 §4).

#### 2.7.3 영향 범위
- 깨진 참조 목적지를 신규 op-data-dictionary references로 갱신(H-4).
- 기존 //erm 사용자 호출 경로 보존(U-3 deprecation 정책 의존).

---

### F-008: install 배포 자동 확인

#### 2.8.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 배치 | `scripts/install-mac.sh` | 신규 스킬 배포 확인 (수정 불필요 검증) | 검증만 |

#### 2.8.2 현재 구현
- `scripts/install-mac.sh:888-899`: `for skill_dir in "$opal_dir/skills"/*/` **와일드카드 순회**로 `opal/skills/*/`를 `~/.opal/skills/`에 배포 (→ ANALYSIS §5, D-소스).
- ANALYSIS §5 추정(`:883-900`) 실제 코드로 재확인 완료 — 와일드카드 배포 확정.

#### 2.8.3 영향 범위
- 신규 스킬 디렉토리(op-data-dictionary/model/ddl, opal-pilot-data-design) 생성 시 자동 배포됨 → install 스크립트 **수정 불필요**. R-6은 "배포 자동 확인"으로 축소(ANALYSIS §5 결론 확정).

---

## 3. 기능별 설계

### F-001: op-data-dictionary 신설

#### 3.1.1 파일 변경 계획
**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/skills/op-data-dictionary/SKILL.md` | 스킬 | DICT CRUD + md SSOT/xlsx export | (→ D-1 §3.2.2) |
| 2 | `opal/skills/op-data-dictionary/references/naming-convention.md` | 가이드 | 이관본 (수식어/분류어·명명규칙) | (→ ANALYSIS §1) |
| 3 | `opal/skills/op-data-dictionary/references/db-type-mapping.md` | 가이드 | 도메인 D001~ ↔ DBMS별 타입(PG/MSSQL/Oracle 확장) | (→ ANALYSIS §2) |
| 4 | `opal/agents/opal-db-agent/personas/data-steward.md` | 에이전트 | DICT 페르소나 (§6 — db-architect 재사용 가능 시 생략 검토) | (→ ANALYSIS §6) |

#### 3.1.2 API·데이터 모델·화면 설계 (스킬 명세)
- **frontmatter**: `name: op-data-dictionary` / `description`(반드시 이 스킬 사용 상황 + 필수 입력/보장 출력) / `version: 1.0` — 단계스킬 표준 (→ ANALYSIS §6).
- **섹션 골격**: 실행 컨텍스트(citation-rules 의무) → 페르소나 → 입력/출력 → 프로세스(Step N) → 활용 MCP → 저장 경로 → 품질 체크리스트 → 변경이력 (→ ANALYSIS §6).
- **사전 3종 md 스키마**: `표준단어사전.md`(수식어/분류어 약어), `도메인사전.md`(D001~ 타입 매핑), `코드사전.md`(코드성 컬럼 CHECK 값) — naming-convention.md 구조를 md 테이블로 정식화 (→ D-1 §3.2.2).
- **[MUST]** `` `docs/proposals/opal-data-design.md` §3.2.2 ``: "수정은 md에서만. xlsx는 op-data-dictionary가 xlsx-tool로 md→xlsx export하여 생성하는 파생물(원본 아님). 역방향(xlsx 수정→md) 금지 — SSOT 혼선 방지."
- **db-type-mapping.md 신규 내용**: 현 naming-convention §1 분류어표(D001~D022, MySQL 9 타입만)를 기준 행으로, PostgreSQL/MSSQL/Oracle 컬럼을 추가한 매핑표. 예: D001 번호 → MySQL `BIGINT UNSIGNED` / PG `BIGINT` / MSSQL `BIGINT` / Oracle `NUMBER(19)` (`skills/erd-modeler/references/naming-convention.md:148-172` 기준 확장).
- **DICT 스킵 조건** (U-2 확정): "기존 사전이 인풋으로 주입되고 커버리지 충분 시 **검증·보강 모드**로 축약, 부재 시 **신규 작성 모드**" — 항상 단계는 발동하되 모드 분기.

#### 3.1.3 환경 변경
- xlsx-tool (db-agent 기보유 — 신규 패키지 없음). 해당 없음.

#### 3.1.4 배치/마이그레이션
- 해당 없음 (문서 작업).

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-2(DICT) | 산출물 검사 | SKILL.md에 사전·코드 CRUD + md SSOT/xlsx export 명시 + 표준 frontmatter |
| TS-002 | R-3(이관) | 산출물 검사 | naming-convention.md 이관 완료 (수식어/분류어/명명규칙 보존) |
| TS-003 | ANALYSIS §2 | 산출물 검사 | db-type-mapping.md 존재 + D001~ 행에 PG/MSSQL/Oracle 컬럼 채워짐 |

---

### F-002: opal-pilot-data-design 오케스트레이터 신설

#### 3.2.1 파일 변경 계획
**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/skills/opal-pilot-data-design/SKILL.md` | 오케스트레이터 | opdd 파이프라인 조율 | (→ D-1 §3.1, §3.2) |

#### 3.2.2 API·데이터 모델·화면 설계 (스킬 명세)
- **frontmatter**: `name: opal-pilot-data-design` / `description`(opdd alias + 트리거 상황) / `version: 1.0`.
- **섹션 골격** (D-5 opal-pilot-dev 구조 준수): `# DB 설계 오케스트레이터 → ## Harness → ## STEP 1~6 → ## STATE.md 도메인 치환값 → ## PM Gate 점검 목록 → ## Agentic/Semi-Agentic 모드 → ## 변경이력`.
- **파이프라인 STEP**: `TASK(PM 직접) → DICT(op-data-dictionary) → MODEL(op-data-model 3모드 순차: 개념→논리→물리) → DDL/MIGRATION(op-data-ddl, 물리 완료 후만) → QA(PM Gate) → CLOSE(DONE.md)` (→ D-1 §3.2).
- **[MUST]** `` `docs/proposals/opal-data-design.md` §3.2 ``: "DDL/MIGRATION은 MODEL의 물리(DBML) 산출 이후에만 실행 가능(캡틴 명시). state-tool stage-transition guard가 자동 차단."
- **[MUST]** `` `docs/proposals/opal-data-design.md` §3.2 ``: "DICT가 MODEL을 선행한다 — 표준사전·코드가 논리/물리 모델링의 속성명·타입을 결정하는 SSOT이기 때문."
- **단계별 디스패치**: 전 단계 워커는 `opal-db-agent` 단일 (검토서 §3.1 단일 도메인) (→ D-1 §3.1).
- **STATE 행 SSOT** (검토서 §3.5, 15행 semi-agentic): §STATE.md 도메인 치환값에 `| # | 단계 | 항목 | 상태 | 시점 |` 테이블로 기재. `state-tool init --skill opdd --rows-from <이 SKILL.md>`가 파싱(D-5 패턴 계승).
  ```
  1 TASK 작업 / 2 TASK 사용자확인
  3 DICT 작업 / 4 DICT PM Gate / 5 DICT 사용자확인
  6 MODEL 작업 / 7 MODEL PM Gate / 8 MODEL 사용자확인
  9 DDL/MIGRATION 작업 / 10 DDL PM Gate / 11 DDL 사용자확인
  12 QA 작업 / 13 QA PM Gate / 14 QA 사용자확인
  15 CLOSE DONE.md 생성
  ```
- **모드 경계** (U-5 확정): semi-agentic 기준 **MODEL 사용자 확인 행(행 8) 통과 후 PM 자율** — DICT/MODEL은 설계 SSOT 확정 단계로 사용자 검토 필요, 물리 이후(DDL)는 기계적 추출이므로 자율. (D-5 opal-pilot-dev는 TEST-SCENARIO 후 경계 — 본 파이프라인은 MODEL 후가 등가 지점).

#### 3.2.3 환경 변경
- 해당 없음.

#### 3.2.4 배치/마이그레이션
- 해당 없음.

#### 3.2.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-004 | R-1 | 산출물 검사 | 파이프라인 6단계 정의 + DDL 물리 의존 명시 + 단계별 op-data-* 디스패치 |
| TS-005 | R-1 | 산출물 검사 | STATE 행 15행 테이블 존재 (검토서 §3.5 일치) |
| TS-006 | R-1, H-3 | 통합 테스트 | `state-tool init --skill opdd --rows-from <SKILL.md>` 실행 시 STATE.md 15행 생성 (레지스트리 반영 후) |

---

### F-003: op-data-model 신설 (MODEL 3모드)

#### 3.3.1 파일 변경 계획
**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/skills/op-data-model/SKILL.md` | 스킬 | 3모드 분리 발동 + 모드별 양식 | (→ D-1 §3.2.1) |
| 2 | `opal/skills/op-data-model/references/mermaid-guide.md` | 가이드 | 이관본 (개념/논리 문법) | (→ ANALYSIS §1) |

#### 3.3.2 API·데이터 모델·화면 설계 (스킬 명세)
- **frontmatter + 단계스킬 골격** (ANALYSIS §6).
- **3모드 양식** (검토서 §3.2.1 표 그대로):
  - `concept`: `//opdd model --concept` 또는 단독 호출. 산출물 `{설계}/개념모델링/ERD_{영역}.mermaid`+`.md`. 규칙: Mermaid erDiagram, 관계명 한글 동사형, M:N 허용, FK 없음, 엔티티명 끝 "정보" (erd-modeler `:101-120` 계승).
  - `logical`: `--logical`. 산출물 `{설계}/논리모델링/ERD_{영역}_논리.mermaid`+`.md`. 규칙: 속성/PK/FK, 식별/비식별, M:N 해소, **속성명=DICT 표준사전 용어** (erd-modeler `:122-153` 계승).
  - `physical`: `--physical`. 산출물 `{설계}/물리모델링/{프로젝트}.dbml`. 규칙: 명명규칙 `{스키마}_{주제}_{엔티티}_{유형}`, 타입=도메인사전 매핑, 인덱스·제약·오딧컬럼 (erd-modeler `:155-191` 계승).
- **[MUST]** `` `docs/proposals/opal-data-design.md` §3.2.1 ``: "논리는 개념, 물리는 논리 산출물을 입력으로 한다(증분). 기존 ERD가 인풋으로 주입되면 해당 모드부터 시작 가능."
- **모드 의존**: pilot은 MODEL 단계에서 3모드 순차(개념→논리→물리), 단독 호출 시 특정 모드만 발동.

#### 3.3.3 환경 변경
- 해당 없음.

#### 3.3.4 배치/마이그레이션
- 해당 없음.

#### 3.3.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-007 | R-2(MODEL) | 산출물 검사 | concept/logical/physical 3모드 분리 발동 + 모드별 산출물 양식 명시 |
| TS-008 | R-3(이관) | 산출물 검사 | mermaid-guide.md 이관 완료 + SKILL.md가 이관 references 참조 |

---

### F-004: op-data-ddl 신설 (DDL/MIGRATION)

#### 3.4.1 파일 변경 계획
**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/skills/op-data-ddl/SKILL.md` | 스킬 | DBML→DDL + 마이그레이션 (물리 입력 전제) | (→ D-2 §5) |
| 2 | `opal/skills/op-data-ddl/references/dbml-guide.md` | 가이드 | 이관본 (DBML 문법) | (→ ANALYSIS §1) |

#### 3.4.2 API·데이터 모델·화면 설계 (스킬 명세)
- **frontmatter + 단계스킬 골격** (ANALYSIS §6).
- **DDL 로직 계승** (erd-modeler `:194-253`): DBML→DDL `dbml2sql --mysql/--postgres/--mssql`, CLI 부재 시 수동 생성(도메인사전 타입 매핑 참조), 역공학 `sql2dbml`.
- **[MUST]** `` `docs/proposals/opal-data-design.md` §3.2 ``: "DDL/MIGRATION은 MODEL의 물리(DBML) 산출 이후에만 실행 가능."
- **마이그레이션**: ORM 마이그레이션 스크립트 생성 (db-agent EXECUTE 역할과 정합).

#### 3.4.3 환경 변경
- `@dbml/cli` (선택 — CLI 없으면 수동 폴백). 신규 필수 패키지 아님.

#### 3.4.4 배치/마이그레이션
- 해당 없음 (스킬 문서 작업).

#### 3.4.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-009 | R-2(DDL) | 산출물 검사 | DBML→DDL + 마이그레이션 + 물리 입력 전제 명시 |
| TS-010 | R-3(이관) | 산출물 검사 | dbml-guide.md 이관 완료 + SKILL.md 참조 |

---

### F-005: opal-db-agent 확장

#### 3.5.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/agents/opal-db-agent/AGENT.md` | 에이전트 | description·실행프로세스·자체로드·MCP·스킬경로·신규섹션 6종 확장 | (→ ANALYSIS §3) |

#### 3.5.2 API·데이터 모델·화면 설계
- **description 확장** (`:3-6`): "+ 표준사전·표준코드 관리(CRUD)" 추가, 기존 모델링·마이그레이션 문구 보존.
- **실행 프로세스**: DICT 스킬 인지 + 사전 경로(md SSOT/xlsx export) 관리 단계 추가.
- **자체 로드 문서 표** (`:42-48`): 표준사전 입출력(md/xlsx) 항목 추가.
- **MCP/도구 표** (`:60-65`): xlsx-tool 사전 export 용도 명시.
- **스킬 경로 인지**: op-data-dictionary/op-data-model/op-data-ddl 경로 추가.
- **신규 섹션**: "단계별 스킬 디스패치 인식".
- **[MUST] 회귀 방지**: 기존 모델링(개념/논리/물리)·마이그레이션 역할 문구 보존 (H-6).

#### 3.5.3 환경 변경
- 해당 없음.

#### 3.5.4 배치/마이그레이션
- 변경이력 행 추가 (AGENT.md 변경이력 표).

#### 3.5.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-011 | R-4 | 산출물 검사 | description에 사전·코드 관리 명시 + op-data-* 경로 인지 |
| TS-012 | R-4, H-6 | 회귀 테스트 | 기존 모델링/마이그레이션 역할 문구 보존 |

---

### F-006: 레지스트리·PROJECT.md 등록

#### 3.6.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/opal-skills-registry.json` | 레지스트리 | opal-pilot에 opdd 추가 + op-data 그룹 3종 신설 | (→ D-6) |
| 2 | `docs/PROJECT.md` | 문서 | 주요 컴포넌트 표에 Data Design 파이프라인 행 추가 | (→ D-7) |

#### 3.6.2 API·데이터 모델·화면 설계 (JSON 스키마)
- **opal-pilot 그룹 추가 항목** (스키마 `:7-22` 준수):
  ```json
  {
    "name": "opal-pilot-data-design",
    "alias": "opdd",
    "description": "DB 설계 파이프라인 오케스트레이터 (사전→모델링→DDL/마이그레이션)",
    "triggers": ["^opal-pilot-data-design$", "^opdd$", "(?i)(데이터\\s*설계|DB\\s*설계|데이터\\s*모델링\\s*파이프라인)"],
    "paths": ["{project}/.opal/skills/opal-pilot-data-design/SKILL.md", "~/.opal/skills/opal-pilot-data-design/SKILL.md"],
    "domain": "data-design",
    "pipeline": "TASK → DICT → MODEL → DDL/MIGRATION → QA → CLOSE"
  }
  ```
- **op-data 그룹 신설** (op-dev 단계스킬 스키마 `:120-135` 준수, 3종): 각 `name/alias:null/description/triggers/paths/stage/dispatched_by`.
  - op-data-dictionary: `stage: "DICT"`, `dispatched_by: ["opal-pilot-data-design"]`
  - op-data-model: `stage: "MODEL"`, `dispatched_by: ["opal-pilot-data-design"]`, triggers에 `^op-data-model$` (+ //erm alias 라우팅은 F-007에서 처리)
  - op-data-ddl: `stage: "DDL"`, `dispatched_by: ["opal-pilot-data-design"]`
- **[MUST]** JSON 파싱 유효성 — 마지막 항목 쉼표·중괄호 검증 (H-1 P0). `python3 -m json.tool` 통과 필수.
- **PROJECT.md**: 주요 컴포넌트 표에 "Data Design (opdd) / op-data-* (3) / opal-db-agent" 행 추가.

#### 3.6.3 환경 변경
- 해당 없음.

#### 3.6.4 배치/마이그레이션
- PROJECT.md 변경이력 행 추가 (레지스트리는 TASK 제약상 변경이력 행 제외).

#### 3.6.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-013 | R-5, H-1 | 통합 테스트 | `python3 -m json.tool opal-skills-registry.json` 파싱 성공 |
| TS-014 | R-5, H-2 | 통합 테스트 | `skill-registry match "opdd"` → opal-pilot-data-design 단일 해소 (충돌 없음) |
| TS-015 | R-5 | 산출물 검사 | PROJECT.md 컴포넌트 표에 Data Design 행 존재 |

---

### F-007: erd-modeler deprecate + 깨진 참조 해소 + //erm alias

#### 3.7.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `skills/erd-modeler/SKILL.md` | 스킬 | deprecate 안내 헤더 + 깨진 참조(`:275-276`) 해소 + //erm 하위호환 | (→ D-2:275-276, D-1 §4) |
| 2 | `opal/core/references/opal-skills-registry.json` | 레지스트리 | erd-modeler 항목 deprecated 표기 + //erm→op-data-model 안내 (F-006와 단일 작업으로 병합 가능) | (→ D-6:444-456) |

#### 3.7.2 API·데이터 모델·화면 설계
- **깨진 참조 해소** (`skills/erd-modeler/SKILL.md:275-276`): `../data-dictionary/references/naming-convention.md` → `../../opal/skills/op-data-dictionary/references/naming-convention.md` (또는 상대경로 재계산), `db-type-mapping.md` 동일 갱신. **단, deprecate 처리 시 해당 §7 참고문서 표를 "이관 안내"로 대체하는 것이 더 깔끔** — 깨진 경로를 신규 op-data-* 안내로 치환.
- **deprecate 안내**: SKILL.md 상단에 "> **[DEPRECATED]** 이 스킬은 op-data-model/op-data-ddl로 분해 이관되었습니다. `//erm`은 op-data-model 단독 호출 alias로 하위호환됩니다." 추가.
- **//erm alias 하위호환** (U-3 확정): 레지스트리 erd-modeler 항목 유지 + description에 deprecated 명시, alias `erm` 트리거를 op-data-model로 라우팅하거나 안내 메시지 출력. **deprecation 정책**: 최소 2개 마이너 버전(또는 차기 분기까지) alias 유지 후 제거 공지, SKILL.md 헤더 + 호출 시 안내 메시지로 마이그레이션 유도.
- **[MUST]** `` `docs/proposals/opal-data-design.md` §4 ``: "erd-modeler standalone deprecate. //erm은 op-data-model 단독 호출 alias로 하위호환."

#### 3.7.3 환경 변경
- 해당 없음.

#### 3.7.4 배치/마이그레이션
- erd-modeler SKILL.md 변경이력 행 추가.

#### 3.7.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-016 | R-3, H-4 | 통합 테스트 | `grep -r "../data-dictionary/" skills/erd-modeler/` → 잔존 0 |
| TS-017 | R-3 | 산출물 검사 | erd-modeler SKILL.md에 deprecate 안내 + //erm 하위호환 명시 |

---

### F-008: install 배포 자동 확인

#### 3.8.1 파일 변경 계획
**수정**: 없음 (검증만).

#### 3.8.2 API·데이터 모델·화면 설계
- `scripts/install-mac.sh:888-899` 와일드카드 순회 확인 — 신규 스킬 자동 배포. 수정 불필요 (→ ANALYSIS §5 확정).

#### 3.8.3 환경 변경
- 해당 없음.

#### 3.8.4 배치/마이그레이션
- 해당 없음.

#### 3.8.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-018 | R-6 | 산출물 검사 | install-mac.sh 와일드카드 배포 확인 — 신규 스킬 4개 자동 포함, 수정 없음 |

---

## 미확정 사항 결정 (U-1~U-5 확정)

> TASK §미확정 + 검토서 §6 오픈 이슈를 PLAN에서 확정. 각 결정에 권고안 + 근거.

### U-1 (O-3) 사전·코드 SSOT 위치 — **권고: `{설계산출물}/사전/` (프로젝트 상대)**
- **결정**: 사전 md 3종은 DB 설계 산출물 디렉토리 하위 `{설계}/사전/`에 둔다. xlsx 뷰도 동일 위치.
- **근거**: ① 검토서 §3.2.2가 예시 위치를 `{설계}/사전/표준단어사전.md`로 명시 (→ D-1 §3.2.2). ② `.opal/AGENT.md` 프로젝트 규칙에 두면 git diff·링크 무결성 관리는 가능하나 사전이 비대해져 부트스트랩 컨텍스트를 오염시킴(헌법 컨텍스트 절약 원칙 위배). ③ 별도 디렉토리는 ERD 산출물과 분리되어 응집도 저하. ④ 모델링 산출물과 같은 트리에 두면 op-data-model이 상대경로로 사전을 참조하기 용이.
- **✅ 캡틴 확정 (R-T1 해소) — opwt 패턴 차용**: opwt(`opal-pilot-write-tech/SKILL.md:40-46`, `:138-146`)의 "PROJECT.md SSOT + default 트리 + 인터뷰 확정" 패턴을 그대로 차용한다.
  - **경로 비하드코딩**: 프로젝트별 설계 산출물 루트 `{설계}`를 `docs/PROJECT.md`에 1회 선언. op-data-* 스킬은 이를 변수로 읽어 `{설계}/사전/` 등을 해소. db-agent `docs/db/` 토큰(`AGENT.md:44`)도 `{설계}` 변수 참조로 통일 → 불일치 소멸.
  - **default 트리** (opwt `100.기획/` prefix 계승, `XXX.{이름}/` + 10 간격): `200.설계/` 하위 `210.사전/`(md SSOT + xlsx 뷰) · `220.개념모델링/` · `230.논리모델링/` · `240.물리모델링/` · `250.DDL/`.
  - **TASK 자동 감지 3분기** (opwt Q6 계승): ① PROJECT.md 등록 경로 ② 루트에 `200.설계/` 존재 ③ 둘 다 없음 → default 제안 + 직접입력. 결과를 TASK.md "산출물 저장 경로" + PROJECT.md 등록.
  - **영향**: F-001(op-data-dictionary)·F-002(pilot TASK 단계 경로 감지)·F-005(db-agent 토큰 통일)에 `{설계}` 변수 + 자동 감지 반영. opwt와 경로 처리 일관성 확보(헌법 §2 표준화).

### U-2 (O-4) DICT 스킵 조건 — **권고: 항상 발동 + 모드 분기 (검증·보강 vs 신규 작성)**
- **결정**: DICT 단계는 항상 실행하되, 기존 사전이 주입되고 커버리지 충분 시 **검증·보강 모드**(미등록 용어만 추가)로, 부재 시 **신규 작성 모드**로 동작.
- **근거**: ① 검토서 §3.2가 "기존 사전이 인풋으로 주입되면 DICT는 검증·보강 모드로 축약 가능"으로 명시 — 완전 스킵이 아닌 축약 (→ D-1 §3.2). ② 사전이 MODEL의 속성명 SSOT이므로 검증 자체를 생략하면 H-5(SSOT 공백) 리스크. ③ STATE 행 무결성: 단계를 스킵하면 stage-transition guard 흐름이 끊김 — 모드 분기가 행 보존에 유리.

### U-3 (O-5) //erm deprecation — **권고: alias 2 마이너 버전 유지 + 3단 안내**
- **결정**: `//erm` alias를 레지스트리에 유지하되 deprecated 표기, op-data-model로 라우팅. 유지 기간 = 최소 2개 마이너 버전(또는 차기 통합 분기까지).
- **근거**: ① 검토서 §4 "`//erm`은 op-data-model 단독 호출 alias로 하위호환" (→ D-1 §4). ② 급격한 제거는 기존 사용자 호출 경로 단절. **3단 안내**: (a) erd-modeler SKILL.md 헤더 [DEPRECATED] 배너, (b) 레지스트리 description에 "deprecated → op-data-model", (c) 호출 시 마이그레이션 안내 메시지. 제거는 별도 후속 태스크에서 공지 후 진행.

### U-4 xlsx→md 역방향 import — **권고: 이번 범위 제외 (보조 모드 미구현)**
- **결정**: xlsx→md 역방향 import 보조 모드는 이번 태스크에서 구현하지 않는다. 단방향(md→xlsx export)만 구현.
- **근거**: ① 검토서 §3.2.2가 단방향을 SSOT 혼선 방지 원칙으로 확정, 역방향은 "O-2 잔여"로 분류 (→ D-1 §3.2.2). ② 역방향 허용 시 SSOT가 두 곳이 되어 origin/wiki 단방향 패턴(brain 차용) 위배. ③ 실사용 수요 미확인 — 사용자 역방향 요구가 실제 발생하면 후속 태스크로 별도 검토(op-data-dictionary 보조 모드 자리만 SKILL.md에 "향후 검토" 주석으로 표기).

### U-5 STATE 행 모드 경계 — **권고: MODEL 사용자 확인 행(행 8) 후 PM 자율**
- **결정**: semi-agentic 기준, MODEL 사용자 확인(행 8) 통과 후부터 DDL·QA를 PM 자율 진행. CLOSE 진입은 사용자 승인 필수(공통).
- **근거**: ① DICT·MODEL은 사전·ERD 설계 SSOT를 확정하는 단계로 사용자 검토가 본질적(틀리면 하류 전체 오류). ② 물리(DBML) 확정 후 DDL은 기계적 추출 — 자율 적합. ③ D-5 opal-pilot-dev가 "TEST-SCENARIO 후 PM 자율"인 것과 등가 — 본 파이프라인에서 설계 확정의 최종 사용자 게이트가 MODEL이므로 그 직후가 경계 (`opal/skills/opal-pilot-dev/SKILL.md:313-314` 패턴 계승). ④ 검토서 §3.5 STATE 주석 "← 모드 경계(이후 PM 자율)"가 행 8에 표기됨 (→ D-1 §3.5).

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001 | 1, 2, 3 | opal-db-agent(2,3) / opal-task-agent(1) | 순차 | DICT 선행 (사전이 모델 SSOT, ANALYSIS §7) |
| 2 | F-002, F-003, F-004 | 4, 5, 6 | opal-task-agent | 병렬 가능 | pilot·model·ddl 독립 파일 (F-001 완료 후) |
| 3 | F-005, F-006, F-007 | 7, 8, 9 | opal-task-agent | 순차(8→9), 7 병렬 | 레지스트리 후 erd deprecate |
| 4 | F-008 | 10 | opal-task-agent | 단독 | install 확인 |
| 5 | F-002~F-007 | 11 | PM 직접 | 단독 | PROJECT.md 갱신 (docs/ Step) |

### 4.2 실행 체크리스트
> 총 11개 Step | Phase 5개 | 실행 모드: 복잡 (Step 11개 ≥ 6, 변경/신규 파일 12개 ≥ 4, 다중 컴포넌트)

#### Step 1: db-type-mapping.md 신규 작성 + naming-convention.md 이관
- [x] 완료
- **소속 기능**: F-001
- **영역**: 가이드
- **agent**: opal-db-agent (DB 도메인 타입 매핑 지식 필요)
- **파일**: `opal/skills/op-data-dictionary/references/naming-convention.md`(이관), `opal/skills/op-data-dictionary/references/db-type-mapping.md`(신규)
- **작업 내용**: `skills/erd-modeler/references/naming-convention.md` 전체 이관(수식어/분류어/명명규칙 보존). db-type-mapping.md 신규 — naming-convention §1 분류어표(D001~D022, MySQL 9 타입)를 기준으로 PG/MSSQL/Oracle 타입 컬럼 확장
- **완료 기준**: 두 파일 존재 + db-type-mapping.md에 D001~ 행마다 4개 DBMS 타입 채워짐
- **테스트**: TS-002, TS-003
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: op-data-dictionary SKILL.md 신설
- [x] 완료
- **소속 기능**: F-001
- **영역**: 스킬
- **agent**: opal-task-agent (스킬 문서 작성) + opal-db-agent 검토 (사전 스키마 도메인 정합)
- **파일**: `opal/skills/op-data-dictionary/SKILL.md`
- **작업 내용**: 단계스킬 표준 frontmatter+골격. 사전·코드 CRUD, md SSOT 3종 스키마(표준단어/도메인/코드사전), xlsx export 단방향(U-4 단방향만), DICT 스킵 조건(U-2 모드 분기), 사전 위치(U-1 `{설계}/사전/`) 명시
- **완료 기준**: SKILL.md에 CRUD + md→xlsx export + 표준 frontmatter + references 참조
- **테스트**: TS-001
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 3: data-steward 페르소나 신설 (선택)
- [x] 완료
- **소속 기능**: F-001
- **영역**: 에이전트
- **agent**: opal-task-agent
- **파일**: `opal/agents/opal-db-agent/personas/data-steward.md`
- **작업 내용**: DICT 전용 페르소나. **db-architect 페르소나 재사용으로 충분하면 이 Step 생략** (ANALYSIS §6: db-architect 재사용 가능). 신설 시 사전 관리·표준화 원칙 기술
- **완료 기준**: 페르소나 파일 존재 또는 재사용 결정 기록
- **테스트**: TS-001 (페르소나 참조 확인)
- **실행 방법**: direct
- **의존**: Step 2

#### Step 4: opal-pilot-data-design SKILL.md 신설
- [x] 완료
- **소속 기능**: F-002
- **영역**: 오케스트레이터
- **agent**: opal-task-agent (pilot 구조 문서) + opal-db-agent 검토 (파이프라인 도메인 정합)
- **파일**: `opal/skills/opal-pilot-data-design/SKILL.md`
- **작업 내용**: opal-pilot-dev 구조(D-5) 준수. STEP 1~6(TASK→DICT→MODEL→DDL→QA→CLOSE), DDL 물리 의존 [MUST], 단계별 db-agent 디스패치, STATE 행 15행(검토서 §3.5), 모드 경계 행 8(U-5)
- **완료 기준**: 파이프라인 6단계 + STATE 15행 + DDL 의존 명시 + opal-pilot 구조 준수
- **테스트**: TS-004, TS-005
- **실행 방법**: sub-agent
- **의존**: Step 2 (DICT 스킬 경로 참조)

#### Step 5: op-data-model SKILL.md 신설 + mermaid-guide 이관
- [x] 완료
- **소속 기능**: F-003
- **영역**: 스킬
- **agent**: opal-task-agent + opal-db-agent 검토 (3모드 모델링 도메인)
- **파일**: `opal/skills/op-data-model/SKILL.md`, `opal/skills/op-data-model/references/mermaid-guide.md`(이관)
- **작업 내용**: 3모드(concept/logical/physical) 분리 발동 + 모드별 양식(검토서 §3.2.1). erd-modeler §4(`:82-191`) 로직 계승. 논리 속성명=DICT 용어 [MUST]. mermaid-guide.md 이관
- **완료 기준**: 3모드 양식 + 모드 의존 + 이관 references 참조
- **테스트**: TS-007, TS-008
- **실행 방법**: sub-agent
- **의존**: Step 1 (사전 SSOT 참조), Step 2

#### Step 6: op-data-ddl SKILL.md 신설 + dbml-guide 이관
- [x] 완료
- **소속 기능**: F-004
- **영역**: 스킬
- **agent**: opal-task-agent + opal-db-agent 검토 (DDL/마이그레이션 도메인)
- **파일**: `opal/skills/op-data-ddl/SKILL.md`, `opal/skills/op-data-ddl/references/dbml-guide.md`(이관)
- **작업 내용**: erd-modeler §5(`:194-253`) 계승 — DBML→DDL, CLI 폴백, 역공학, 마이그레이션. 물리 입력 전제 [MUST]. dbml-guide.md 이관
- **완료 기준**: DDL+마이그레이션+물리 전제 명시 + 이관 references 참조
- **테스트**: TS-009, TS-010
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 2 (Step 5와 병렬 가능)

#### Step 7: opal-db-agent AGENT.md 확장
- [ ] 완료
- **소속 기능**: F-005
- **영역**: 에이전트
- **agent**: opal-task-agent
- **파일**: `opal/agents/opal-db-agent/AGENT.md`
- **작업 내용**: ANALYSIS §3 6종 확장 — description(+사전·코드 CRUD), 실행프로세스(DICT 단계), 자체로드(md/xlsx 사전), MCP(xlsx export), op-data-* 경로 인지, "단계별 스킬 디스패치 인식" 섹션. 기존 역할 보존
- **완료 기준**: 6종 확장 반영 + 기존 모델링/마이그레이션 문구 보존 + 변경이력 행
- **테스트**: TS-011, TS-012
- **실행 방법**: sub-agent
- **의존**: Step 4, 5, 6 (스킬 경로 확정 후)

#### Step 8: 레지스트리 등록 (opdd + op-data 그룹 + erd-modeler deprecate 표기)
- [ ] 완료
- **소속 기능**: F-006, F-007
- **영역**: 레지스트리
- **agent**: opal-task-agent
- **파일**: `opal/core/references/opal-skills-registry.json`
- **작업 내용**: opal-pilot 그룹에 opdd 추가, op-data 그룹(3종) 신설, erd-modeler 항목 deprecated 표기(F-007 병합). JSON 유효성 유지
- **완료 기준**: `python3 -m json.tool` 통과 + opdd alias 충돌 0 + op-data 3종 등록
- **테스트**: TS-013, TS-014
- **실행 방법**: sub-agent
- **의존**: Step 4, 5, 6

#### Step 9: erd-modeler SKILL.md deprecate + 깨진 참조 해소
- [ ] 완료
- **소속 기능**: F-007
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `skills/erd-modeler/SKILL.md`
- **작업 내용**: 상단 [DEPRECATED] 배너, `:275-276` 깨진 참조(`../data-dictionary/...`)를 신규 op-data-dictionary references 경로로 갱신 또는 이관 안내로 대체, //erm 하위호환 명시(U-3), 변경이력 행
- **완료 기준**: `grep -r "../data-dictionary/" skills/erd-modeler/` 잔존 0 + deprecate 안내 존재
- **테스트**: TS-016, TS-017
- **실행 방법**: sub-agent
- **의존**: Step 5 (op-data-model 경로 확정), Step 8

#### Step 10: install 배포 자동 확인
- [ ] 완료
- **소속 기능**: F-008
- **영역**: 배치
- **agent**: opal-task-agent
- **파일**: `scripts/install-mac.sh` (검증만)
- **작업 내용**: `:888-899` 와일드카드 순회 재확인 — 신규 스킬 4개 자동 배포 검증, 수정 불필요 확정
- **완료 기준**: 와일드카드 배포 확인 + 수정 없음 기록
- **테스트**: TS-018
- **실행 방법**: direct
- **의존**: Step 4, 5, 6 (신규 스킬 디렉토리 존재)

#### Step 11: PROJECT.md 컴포넌트 표 갱신
- [ ] 완료
- **소속 기능**: F-006
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/PROJECT.md`
- **작업 내용**: 주요 컴포넌트 표에 "Data Design 파이프라인 (opdd / op-data-* 3종 / opal-db-agent)" 행 추가 + 변경이력
- **완료 기준**: 컴포넌트 표에 Data Design 행 존재
- **테스트**: TS-015
- **실행 방법**: direct
- **의존**: Step 8 (레지스트리 확정 후)

### 4.3 병렬/순차 판별 근거
| 관계 | 근거 |
|------|------|
| Step 1 → Step 2 | 사전 references가 SKILL.md 참조 대상 (이관 선행) |
| Step 2 → Step 4,5,6 | 모든 op-data-*·pilot이 DICT 스킬·사전 SSOT 참조 (ANALYSIS §7 DICT 선행) |
| Step 5 ∥ Step 6 | op-data-model·op-data-ddl 독립 파일 (병렬 가능) |
| Step 4,5,6 → Step 7 | db-agent가 확정된 op-data-* 경로 인지 |
| Step 4,5,6 → Step 8 | 레지스트리가 확정 스킬명·paths 등록 |
| Step 5,8 → Step 9 | erd 깨진참조 목적지(op-data-model)·레지스트리 deprecate 표기 후 |
| Step 8 → Step 11 | PROJECT.md가 레지스트리 등록 내용 반영 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA
| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | DICT 스킬 + references 이관 + db-type-mapping | TS-001,002,003 | CRUD/export 명시 + 이관 완료 + 타입표 4 DBMS |
| F-002 | pilot 파이프라인 + STATE 행 + state-tool 연동 | TS-004,005,006 | 6단계 + 15행 + init 실행 성공 |
| F-003 | MODEL 3모드 분리 발동 | TS-007,008 | 3모드 양식 + mermaid 이관 |
| F-004 | DDL/MIGRATION + 물리 전제 | TS-009,010 | DDL+마이그레이션 + dbml 이관 |
| F-005 | db-agent 확장 + 회귀 보존 | TS-011,012 | 사전·코드 명시 + 기존 역할 보존 |
| F-006 | 레지스트리 파싱·매칭 + PROJECT.md | TS-013,014,015 | json.tool 통과 + opdd 매칭 + 표 행 |
| F-007 | erd 깨진참조 해소 + deprecate | TS-016,017 | grep 잔존 0 + deprecate 안내 |
| F-008 | install 자동 배포 확인 | TS-018 | 와일드카드 확인 + 수정 없음 |

### 5.2 회귀 테스트
- [ ] erd-modeler 기존 사용자 호출(//erm) 경로 보존 (deprecate 안내 후에도 동작/라우팅)
- [ ] opal-db-agent 기존 모델링/마이그레이션 역할 문구 비파괴 (H-6)
- [ ] 레지스트리 기존 그룹(opal-pilot/op-dev/op-sdd/op-task/standalone/opal) 비파괴 — 기존 항목 보존

### 5.3 코드/문서 품질
- [ ] 신규 SKILL.md 4종이 단계스킬/pilot 표준 frontmatter·골격 준수 (ANALYSIS §6)
- [ ] 신규 SKILL.md·AGENT.md 변경이력 표 포함, 수정 문서(레지스트리 제외) 변경이력 행 추가
- [ ] 배포 경계 준수 — `~/.opal/` 직접 편집 0, 소스만 수정
- [ ] erd-modeler 줄번호 매핑 기준 이관 누락 0 (§4=`:82-191`, §5=`:194-253`)

### 5.4 보안
- [ ] 신규 문서에 하드코딩 시크릿/토큰 없음 (스킬 문서라 해당 없음 확인)
- [ ] db-type-mapping.md에 실 DB 접속정보 미포함

---

## 6. 복잡도 판별
| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 11개 | 복잡 |
| 변경 파일 수 | 신규 9 + 수정 3 = 12개 | 복잡 |
| 모듈 범위 | 다중 (스킬 3종 + pilot + 에이전트 + 레지스트리 + 문서) | 복잡 |
| 작업 유형 | 신규 컴포넌트 4개 + 이관 + 확장 | 복잡 |
| 외부 의존성 | 없음 (DBML CLI는 op-data-ddl 런타임 선택, 본 태스크 문서작업) | 단순 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지
```
Batch 1 (Phase 1): [opal-db-agent: Step1] → [opal-task-agent: Step2] → [Step3 direct]
Batch 2 (Phase 2): [opal-task-agent: Step4] ∥ [Step5] ∥ [Step6]   (병렬, F-001 완료 후)
Batch 3 (Phase 3): [opal-task-agent: Step7] / [Step8] → [Step9]
Batch 4 (Phase 4-5): [Step10 direct] / [Step11 PM 직접]
```
- **파일 충돌 방지**: Step 8·9가 모두 레지스트리 수정 → 동일 에이전트 순차(8→9) 또는 8에 erd deprecate 표기 병합.
- **그룹핑**: op-data-* 스킬 문서 작성은 opal-task-agent, DB 도메인 내용 검토는 opal-db-agent 보조.

### C-2. 스킬 요구사항
- 기존 스킬 매칭: op-dev-plan(본 PLAN), 신규 작성 대상이 곧 산출물 — 별도 신규 스킬 불필요.
- 갭: 없음 (문서·스킬 작성 태스크).

### C-3. 도구 요구사항
- `python3 -m json.tool` (레지스트리 유효성), `grep`(깨진 참조 잔존 확인), `skill-registry match`(라우팅), `state-tool init`(STATE 생성) — 모두 기존 도구.

### C-4. 테스트 전략
- 본 태스크는 문서·스킬 작업 → **RED-first 비적용** (red-first.md 하이브리드 분기: "문서=구현 후 검증"). TEST-SCENARIO.md는 PM이 별도 작성하며, 검증 포인트는 §5 QA + 아래 검증 4종으로 한정:
  1. 레지스트리 JSON 파싱 유효성 — `python3 -m json.tool opal/core/references/opal-skills-registry.json`
  2. `skill-registry match "opdd"` → opal-pilot-data-design 단일 해소
  3. `state-tool init --skill opdd` → STATE.md 15행 생성 (레지스트리 반영 후)
  4. erd-modeler 깨진 참조 해소 — `grep -r "../data-dictionary/" skills/erd-modeler/` 잔존 0
- 산출물 검사(TS-001,002,004,005,007~011,015,017,018)는 파일 존재·내용 grep으로 검증.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 스킬/에이전트 문서 | Markdown | op-dev-plan, ANALYSIS §6 단계스킬 템플릿 |
| 레지스트리 | JSON | opal-skills-registry v3.4.0 스키마 |
| 배포 | Bash | install-mac.sh 와일드카드 |
| 모델링 산출물 양식 | DBML / Mermaid | dbml-guide / mermaid-guide (이관) |

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| (없음) | 본 태스크는 OPAL 내부 컴포넌트 구조 작업 — 외부 라이브러리 문서 조회 불필요 |

### 8.3 참조 문서 (설계 결정 근거)
| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | 설계 검토서 (SSOT) | `docs/proposals/opal-data-design.md` | 전체 설계 확정안 (§3 컴포넌트맵·§3.2 파이프라인·§3.2.1 MODEL 양식·§3.2.2 사전 포맷·§3.5 STATE·§6 오픈이슈) |
| D-2 | 소스 | erd-modeler SKILL | `skills/erd-modeler/SKILL.md` | 모델링/DDL 로직 이관 원천 (§3=`:55-79`, §4=`:82-191`, §5=`:194-253`, 깨진참조=`:275-276`) |
| D-3 | 소스 | naming-convention | `skills/erd-modeler/references/naming-convention.md` | 사전 스키마·분류어 타입표(`:143-172` D001~D022 MySQL만) |
| D-4 | 소스 | opal-db-agent | `opal/agents/opal-db-agent/AGENT.md` | 에이전트 확장 대상 (description `:3-6`, 자체로드 `:42-48`, MCP `:60-65`) |
| D-5 | 설계 | opal-pilot-dev SKILL | `opal/skills/opal-pilot-dev/SKILL.md` | pilot 구조 템플릿 (STATE 행 `:266-289`, 모드경계 `:313-314`) |
| D-6 | 설계 | 스킬 레지스트리 | `opal/core/references/opal-skills-registry.json` | 컴포넌트 등록 (opal-pilot 스키마 `:7-22`, op-dev 스키마 `:120-135`, erd-modeler `:444-456`) |
| D-7 | 설계 | PROJECT.md | `docs/PROJECT.md` | 주요 컴포넌트 등재 |
| D-8 | 소스 | install-mac.sh | `scripts/install-mac.sh` | 배포 와일드카드 확인 (`:888-899`) |

---

## 9. 리스크 및 대응 (기능-리스크 연결)
| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | erd-modeler 로직 이관 누락 | F-003,004 | P1 | 줄번호 매핑(D-2: §4 `:82-191`, §5 `:194-253`) 기준 대조 검증 (TS-008,010) |
| R-2 | 깨진 참조 잔존 (`../data-dictionary/`) | F-007 | P1 | §2 경로 갱신 + grep 잔존 0 검증 (TS-016) |
| R-3 | 신규 스킬 구조 비일관 | F-001~004 | P1 | ANALYSIS §6 표준 템플릿 적용 + D-5 pilot 골격 준수 (TS-001,004,007,009) |
| R-4 | 레지스트리 JSON 파싱 깨짐 | F-006 | **P0** | `python3 -m json.tool` 통과 필수 (TS-013), 마지막 항목 쉼표·중괄호 주의 |
| R-5 | db-agent 기존 역할 회귀 손실 | F-005 | P2 | 기존 모델링/마이그레이션 문구 보존 diff 검증 (TS-012) |
| R-6 | db-type-mapping 신규 작성 부정확 (PG/MSSQL/Oracle) | F-001 | P1 | naming-convention §1 MySQL 행 기준 + DB 도메인 지식(opal-db-agent) 검토 |
| R-T1 | 용어 불일치 — 검토서 `{설계}/사전/` ↔ db-agent `docs/db/` 경로 토큰 | F-001,005 | P1 | **U-1에서 확정** — `{설계}` 루트를 PROJECT.md/`.opal/AGENT.md`에 1회 선언, op-data-* 가 읽어 해소 (하드코딩 회피) |

---

## 변경이력
| 버전 | 일시(KST) | 변경 내용 |
|------|----------|----------|
| 1.0 | 2026-06-12 | 초안 — TASK/ANALYSIS/설계검토서 기반 PLAN 작성, U-1~U-5 확정, 11 Step/5 Phase 복잡모드 |
