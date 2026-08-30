# 설계 검토서: opal-pilot-data-design — DB 설계 업무의 OPAL 내재화

> 상태: 제안(검토 중) | 작성일: 2026-06-12 | 작성: 알투[PM]
> 트리거: 캡틴 지시 — "DB 설계 업무를 OPAL framework로 내재화. opal-pilot-data-design(opdd), op-data-model 등 스킬 구조 조정 검토"
> 성격: 아키텍처 결정 제안 — 승인 시 구현 태스크로 전개

---

## 1. 목표

흩어진 DB 설계 자산(erd-modeler·data-dictionary·opal-db-agent)을 OPAL 표준 3층 컴포넌트 체계(**pilot + 단계 스킬 + 에이전트**)로 내재화하여, 기획서·기존 ERD·사전·ORM을 인풋으로 받아 `사전 → 모델링 → DDL/마이그레이션`을 파이프라인으로 수행하는 오케스트레이터를 신설한다.

## 2. 현 상태 진단 — DB 설계만 표준 체계 밖

| 도메인 | 오케스트레이터 | 단계 스킬 | 에이전트 | 상태 |
|--------|--------------|----------|---------|------|
| 개발 | opal-pilot-dev(opd) | op-dev-* (7) | be/fe/db/plan/test | ✅ 표준 |
| SDD | opal-pilot-sdd(opsdd) | op-sdd-* (4) | sdd-action | ✅ 표준 |
| 기획 | opal-pilot-write-tech(opwt) | (PM 직접) | planning | ✅ 표준 |
| **DB 설계** | ❌ 없음 | ❌ 없음 (erd-modeler=standalone) | opal-db-agent | ⚠️ 비표준 |

문제점:
- `erd-modeler`: standalone 단일 스킬. 개념→논리→물리→DDL의 다단계 워크플로인데 **오케스트레이션·State·Gate 없음**
- `data-dictionary`: **유령 스킬** — erd-modeler `SKILL.md:275-276`가 `../data-dictionary/references/...`를 참조하나 디렉토리·레지스트리 등록 모두 부재 (깨진 참조)
- `opal-db-agent`: 표준사전을 **읽어 활용**만 함 — 사전·코드 CRUD 주체 부재
- 표준사전·표준코드의 **생성/관리 SSOT가 없음** → 모델링 품질이 erd-modeler 내부 폴백 규칙에만 의존

## 3. 제안 구조 — 표준 3층 승격

### 3.1 컴포넌트 맵

| 층 | 컴포넌트 | 명명 | 역할 |
|----|---------|------|------|
| 오케스트레이터 | **opal-pilot-data-design** | alias `opdd` | DB 설계 파이프라인 조율 (§3.2) |
| 단계 스킬 | **op-data-dictionary** | (DICT) | 표준사전(단어/도메인) · 표준코드 CRUD |
| 단계 스킬 | **op-data-model** | (MODEL) | 개념·논리·물리 ERD 모델링 (3모드) |
| 단계 스킬 | **op-data-ddl** | (DDL/MIGRATION) | DBML→DDL 추출 + 마이그레이션 스크립트 |
| 에이전트 | **opal-db-agent** | (유지·확장) | 위 단계 스킬의 실행 주체 — 역할에 "사전·코드 관리" 추가 |

> **실행 에이전트 확정**: 전 단계의 작업 주체는 `opal-db-agent` 단일 에이전트다(단일 도메인이므로 op-dev처럼 영역별 분기 없음). db-agent는 이미 "데이터 모델링(개념/논리/물리) 작성·수정·관리 + 마이그레이션"으로 정의되어 있어 정합(`opal-db-agent/AGENT.md`).

### 3.2 파이프라인 (캡틴 사양)

```
TASK → DICT → MODEL → DDL/MIGRATION → QA → CLOSE
              (트랙별 모드)   (물리 이후만)
```

| 단계 | 스킬 | 핵심 | 의존 |
|------|------|------|------|
| TASK | (PM 직접) | 인풋 컨텍스트 수집·범위 확정 | - |
| DICT | op-data-dictionary | 표준사전·코드 신규 작성 또는 기존 보강. **모델링 SSOT 선확립** | TASK |
| MODEL | op-data-model | 신규 트랙: 개념→논리→물리 / 역공학 트랙: 물리→논리(개념 제외). 속성명·타입은 DICT 사전 기반 | **DICT** |
| DDL/MIGRATION | op-data-ddl | DBML→DDL 스크립트 생성 + ORM 마이그레이션 | **MODEL 물리 완료 후만** |
| QA | (PM Gate) | 정합성 검증 (§3.4) | DDL |

> **핵심 순서 결정**: DICT가 MODEL을 **선행**한다 — 표준사전·코드가 논리/물리 모델링의 속성명·타입을 결정하는 SSOT이기 때문(`naming-convention.md`: 분류어가 도메인과 1:1 매핑되어 타입 결정). 기존 사전이 인풋으로 주입되면 DICT는 "검증·보강" 모드로 축약 가능.
> **DDL 의존 제약**: DDL/MIGRATION은 MODEL의 물리(DBML) 산출 이후에만 실행 가능(캡틴 명시). state-tool stage-transition guard가 자동 차단.

### 3.2.1 MODEL 3모드 — 분리 발동 + 산출물 양식 (캡틴 사양)

op-data-model은 개념/논리/물리 **3모드를 분리 발동**할 수 있다(`erd-modeler` 3단계 모델링 흐름 계승). pilot은 MODEL 단계에서 **트랙에 따라 모드를 순차 실행**한다 — 신규(greenfield) 트랙은 개념→논리→물리 3모드, 역공학(reverse) 트랙은 물리→논리 2모드(개념 모드 제외)다. 단계 스킬 단독 호출 시 특정 모드만 발동 가능.

| 모드 | 발동 | 산출물 (양식) | 핵심 규칙 (erd-modeler 계승) |
|------|------|-------------|------------------------------|
| `concept`(개념) | `//opdd model --concept` 또는 op-data-model concept | `{설계}/개념모델링/ERD_{영역}.mermaid` + `.md` | Mermaid erDiagram. 관계명 한글 동사형, 카디널리티(M:N 허용), FK 없음, 엔티티명 끝 "정보" |
| `logical`(논리) | `--logical` | `{설계}/논리모델링/ERD_{영역}_논리.mermaid` + `.md` | Mermaid + 속성/PK/FK. 식별/비식별 관계, M:N 매핑 해소, **속성명=DICT 표준사전 용어** |
| `physical`(물리) | `--physical` | `{설계}/물리모델링/{프로젝트}.dbml` | DBML. 명명규칙 `{스키마}_{주제}_{엔티티}_{유형}`, 타입=도메인사전 매핑, 인덱스·제약·오딧컬럼 |

> **모드 의존**: 논리는 개념, 물리는 논리 산출물을 입력으로 한다(증분). 기존 ERD가 인풋으로 주입되면 해당 모드부터 시작 가능. 역공학 트랙에서는 기존 DB·DDL·ORM에서 역추출한 **물리(DBML)가 기점**이며, 논리는 물리에서 역산한다. 개념 모드는 실행하지 않는다. 각 모드 산출물 양식·폴더 구조는 erd-modeler `SKILL.md:35-51`·`references/mermaid-guide.md`·`dbml-guide.md`를 op-data-model `references/`로 이관하여 관리한다.

### 3.2.2 DICT 사전 포맷 — 이중 포맷 (md SSOT + xlsx 뷰) (캡틴 사양)

캡틴 트레이드오프("관리는 md, 사용자 열람은 xlsx")를 **단방향 이중 포맷**으로 해소한다. brain의 `origin=SSOT / wiki=파생 단방향` 패턴을 차용한다.

| 구분 | 포맷 | 위치(예) | 역할 |
|------|------|---------|------|
| **SSOT (원본)** | Markdown | `{설계}/사전/표준단어사전.md`·`도메인사전.md`·`코드사전.md` | 알투 관리·git diff·링크 무결성·CRUD 대상 |
| **뷰 (파생)** | xlsx | `{설계}/사전/표준사전.xlsx` | 사용자 열람 전용. md에서 **재생성** |

- **단방향 규칙**: 수정은 **md에서만**. xlsx는 op-data-dictionary가 `xlsx-tool`로 md→xlsx **export**하여 생성하는 파생물(원본 아님). 역방향(xlsx 수정→md) 금지 — SSOT 혼선 방지.
- **근거**: opal-db-agent가 이미 `xlsx-tool` 보유(`AGENT.md` MCP/도구) → export 구현 용이. 사전 내용 구조는 `naming-convention.md`(수식어/분류어 약어표, 도메인 D001~ 타입 매핑, 코드사전)를 md 스키마로 정식화.
- **사용자 역방향 요구 시**: xlsx에서 사전을 편집하고 싶다는 요구가 있으면, `xlsx→md import` 1회성 동기화 명령을 op-data-dictionary 보조 모드로 추가 검토(O-2 잔여).

### 3.3 인풋 컨텍스트 주입 (캡틴 사양)

TASK 단계에서 다음을 자동 감지·주입한다 (opwt의 외부참조 자동 스캔 + db-agent 자체로드 패턴 결합):

| 인풋 | 감지 경로 | 처리 |
|------|----------|------|
| 기획서 | `docs/PRD.md`·`docs/SERVICE.md`·정책서·IA (존재 시) | 엔티티·용어 추출 근거 |
| 사용자 대화·지시 | interview 스킬 | 범위·제약·대상 DBMS 확정 |
| 기존 ERD | `docs/db/`·`docs/erd/` (존재 시) | MODEL 베이스라인(증분 설계) |
| 기존 데이터 사전 | 사용자 지정 경로·`docs/` (존재 시) | DICT 베이스라인 |
| 기존 ORM | `models/`·`migrations/` code-scan (존재 시) | 현행 스키마 역추적, 마이그레이션 정합 |

> 인풋 부재 시: 기획서/대화에서 신규 도출, 사전은 `naming-convention.md` 기본 규칙 폴백.

### 3.4 QA 검증 항목

- 단계 간 정합 — 신규 트랙: 개념 ERD ↔ 논리 ↔ 물리 / 역공학 트랙: 물리 ↔ 논리 (엔티티/관계 보존)
- 사전 정합: 모든 컬럼명이 DICT 표준사전 등록 용어 (미등록 0)
- 기획 정합: 기획서 엔티티 ↔ ERD 누락 0 (citation-rules §7 영역 간 일관성)
- DDL 검증: 물리 DBML ↔ DDL 일치, 명명규칙(`PK_`/`FK_`/`UQ_`/`IDX_`) 준수

### 3.5 STATE 행 구성 (semi-agentic 기준, opd 패턴)

```
1 TASK 작업 / 2 TASK 사용자확인
3 DICT 작업 / 4 DICT PM Gate / 5 DICT 사용자확인
6 MODEL 작업 / 7 MODEL PM Gate / 8 MODEL 사용자확인   ← 모드 경계(이후 PM 자율)
9 DDL/MIGRATION 작업 / 10 PM Gate / 11 사용자확인
12 QA 작업 / 13 QA PM Gate / 14 QA 사용자확인
15 CLOSE DONE.md 생성
```

## 4. 기존 자산 마이그레이션

| 자산 | 처리 |
|------|------|
| `erd-modeler` §4 모델링 | → `op-data-model`로 이관 |
| `erd-modeler` §5 DDL | → `op-data-ddl`로 이관 |
| `erd-modeler` §3 사전 참조 | → `op-data-dictionary`로 승격(참조→CRUD) |
| references(mermaid/dbml/naming-convention) | → 해당 op-data-* `references/`로 이관 |
| `erd-modeler` standalone | deprecate. `//erm`은 op-data-model 단독 호출 alias로 하위호환 |
| `data-dictionary`(유령) | `op-data-dictionary`로 정식화 + 깨진 참조 해소 |
| `opal-db-agent` | 역할에 "사전·코드 관리" 추가, op-data-* 스킬 경로 인지 |
| 레지스트리·PROJECT.md | opal-pilot-data-design 그룹·약어 등록, 주요 컴포넌트 표 추가 |

## 5. opwt(기획) 연계

- opwt는 기획 전용 유지(ERD는 외부참조 읽기). 역으로 opal-pilot-data-design은 기획서를 인풋으로 주입받음 — **단방향 의존(설계가 기획을 참조)**.
- 라이프사이클: `oppd`(opal-pilot-project-dev)에 기획(opwt) → **설계(opdd)** → 개발(opd) 순서로 설계 단계 삽입 검토.

## 6. 오픈 이슈 (구현 전 확정 필요)

| # | 이슈 | 상태 / 결정 |
|---|------|------------|
| O-1 | 오케스트레이터 명명 | ✅ **확정: `opal-pilot-data-design`(alias `opdd`)** — pilot 접두사 체계 정합 + data-design 의미 (캡틴 결정) |
| O-2 | 표준사전 저장 포맷 | ✅ **확정: md SSOT + xlsx 뷰 단방향**(§3.2.2). 잔여: xlsx→md 역방향 import 보조 모드 필요 여부(PLAN 검토) |
| O-3 | 사전·코드 SSOT 위치 | ⬜ `.opal/AGENT.md` 프로젝트 규칙 / `{설계}/사전/` / 별도. 현 naming-convention은 `.opal/AGENT.md` 참조 전제 — PLAN 확정 |
| O-4 | DICT 스킵 조건 | ⬜ 기존 사전 충분 시 DICT "검증만" 축약 vs 항상 실행 — PLAN 확정 |
| O-5 | `//erm` 하위호환 범위 | ⬜ alias 유지 기간·deprecation 안내 방식 — PLAN 확정 |

## 7. 트레이드오프

- **이득**: 표준화(헌법 §2, 타 도메인 일관) · 파이프라인 게이트/State/QA 자동 적용 · data-dictionary 유령 해소 · 사전→모델→DDL SSOT 체인 확립
- **비용**: 컴포넌트 4개 신설(pilot 1 + 단계스킬 3) · 단일 `//erm` 단순성 상실 · 마이그레이션 작업량
- **과설계 방지**: pilot은 "전체 데이터 설계", 단계 스킬 단독 호출(`//erm` 등)은 "부분 작업"으로 양립 설계 → 소규모는 단계 스킬 직접 사용

## 8. 다음 액션

1. 오픈 이슈 O-1~O-5 확정
2. 확정 후 구현 태스크 전개 — 컴포넌트 다수 신설·구조 변경이므로 **//opd(Full Task) 또는 //opp** 풀 파이프라인 권고 (순수 문서/스킬 작업이라 코드 동작검증은 없으나 구조 규모가 큼)
