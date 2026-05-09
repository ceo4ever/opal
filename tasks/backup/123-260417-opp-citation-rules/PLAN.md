# PLAN: 산출물 인용 위치 추적 하네스 (Citation Rules)

> 작성일: 2026-04-17
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사

### 참조 문서 (PLAN 작성 근거)

| # | 문서 | 경로 | 참조 이유 |
|---|------|------|----------|
| D-1 | 하네스 공통 | `opal/core/references/opal-harness.md` | §2 모듈 테이블 — citation-rules 모듈 등록 위치 |
| D-2 | PM 행동 프로세스 | `opal/core/references/opal-pm.md` | §3 Step 3 기존 인용 포맷(`[MUST] <문서명> §N: <원문>`) |
| D-3 | op-task 스킬 | `opal/skills/op-task/SKILL.md` | TASK.md "관련 문서" 섹션 현재 형식 |
| D-4 | op-dev-analysis 스킬 | `opal/skills/op-dev-analysis/SKILL.md` | ANALYSIS.md 통일 형식 §1~§6 |
| D-5 | op-dev-plan 스킬 | `opal/skills/op-dev-plan/SKILL.md` | PLAN.md 출력 형식 §3 설계 + §8 기술 컨텍스트 |
| D-6 | plan-guide (op-dev-plan) | `opal/skills/op-dev-plan/references/plan-guide.md` | 3단계 설계 가이드 현재 |
| D-7 | op-task-plan 스킬 | `opal/skills/op-task-plan/SKILL.md` | 범용 PLAN.md 형식 |
| D-8 | plan-guide (op-task-plan) | `opal/skills/op-task-plan/references/plan-guide.md` | 범용 PLAN 3단계 설계 가이드 |
| D-9 | 기존 하네스 모듈 샘플 | `opal/core/references/harness/header-rules.md` | 하네스 모듈 작성 패턴 (stub + 본문) |
| D-10 | QA 표준 모듈 샘플 | `opal/core/references/harness/qa-standards.md` | 하네스 모듈 본문 포맷 레퍼런스 |

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `opal/core/references/opal-harness.md` | 하네스 SSOT — §2 모듈 테이블 | ✅ 수정 (citation-rules 행 추가) |
| `opal/core/references/harness/citation-rules.md` | citation 전용 모듈 | ✅ 신규 |
| `opal/skills/op-task/SKILL.md` | TASK.md 템플릿 | ✅ 수정 (관련 문서 섹션 테이블화) |
| `opal/skills/op-dev-analysis/SKILL.md` | ANALYSIS.md 통일 형식 | ✅ 수정 (§1~§3에 인용 컬럼 추가) |
| `opal/skills/op-dev-plan/SKILL.md` | PLAN.md 출력 형식 | ✅ 수정 (§3 설계 인라인, §8 참조 테이블) |
| `opal/skills/op-dev-plan/references/plan-guide.md` | 3단계 설계 가이드 | ✅ 수정 (인용 지시 추가) |
| `opal/skills/op-task-plan/SKILL.md` | 범용 PLAN.md 형식 | ✅ 수정 (§1 참조 문서 테이블 + §2 설계 인라인) |
| `opal/skills/op-task-plan/references/plan-guide.md` | 범용 PLAN 3단계 가이드 | ✅ 수정 (인용 지시 추가) |

### 현재 상태

1. **PM → 워커 인용 포맷 존재**: `opal-pm.md` §3 Step 3 "인용 의무 규칙"에서 `[MUST] <문서명> §N: <규칙 원문>` 포맷이 이미 정의되어 있다. 단, 이는 "PM이 워커에게 주입하는" 방향의 인용이며, "워커가 산출물에 기록하는" 인용은 정의되어 있지 않다.
2. **TASK.md "관련 문서" 섹션**: `op-task/SKILL.md` 템플릿에 존재하나 경로만 나열되는 bullet list 형태 — 섹션/줄번호 미포함.
3. **ANALYSIS.md**: §1.1 관련 파일 목록에 `파일 | 역할 | 변경 필요` 컬럼만 있어 분석 근거(줄번호/섹션) 추적 불가.
4. **PLAN.md (op-dev-plan)**: §8 "기술 컨텍스트" 섹션에 스킬명만 기록 — 설계 결정 근거 문서·섹션 미기록. §3 설계 섹션에 인용 필드 없음.
5. **PLAN.md (op-task-plan)**: §1 "현황 조사" / §2.핵심 설계에 인용 섹션 없음.
6. **하네스 모듈**: `harness/` 폴더에 `header-rules.md` / `qa-standards.md` / `observability.md` 등 6개 모듈 존재. `citation-rules.md` 없음.

### 영향 범위

- **직접 영향**: 3개 단계 스킬(op-task, op-dev-analysis, op-dev-plan, op-task-plan) + 2개 plan-guide + 1개 하네스 모듈 신설 + 1개 하네스 SSOT 테이블
- **간접 영향**: 이후 TASK/ANALYSIS/PLAN을 생성하는 모든 워커 디스패치 — 산출물에 인용 필드가 필수로 포함된다
- **레거시**: 기존 산출물 소급 변경 없음 (TASK.md R-제약에 명시)

---

## 2. 핵심 설계 결정

### 2.1 인용 형식 설계

**설계 원칙** (근거: TASK.md "요구사항 핵심" + `opal-pm.md §3 Step 3 인용 의무 규칙`):

| 원칙 | 구현 방법 |
|------|---------|
| 사람이 빠르게 원본 접근 | 상대 경로 + 섹션명 명시 |
| AI가 파일 경로 인식하여 Read | 백틱(`) 감싼 경로로 Read 도구 패턴 매칭 |
| 코드·문서 근거 통일 표현 | `경로:줄번호` / `경로 §N` 두 형식 구분 |
| 재해석 방지 (PM 규칙과 정합) | 핵심 제약은 `[MUST]` + 원문 인용 포맷 재사용 |

**확정 인용 포맷 (4종)**:

1. **문서 근거 (로컬 파일 — 기획/설계 문서)**
   - 표준 포맷: `` `경로` §{N} {섹션명} `` 또는 원문 포함 시 `` `경로` §{N}: "<원문>" ``
   - 예: `` `opal/core/references/opal-harness.md` §2 모듈 구조 ``
   - 예: `` `docs/CONVENTIONS.md` §3.1: "API 응답은 camelCase를 사용한다" ``

2. **코드 근거 (로컬 파일 — 소스 코드)**
   - 표준 포맷: `` `경로:줄번호` `` 또는 범위 `` `경로:N-M` ``
   - 예: `` `opal/skills/op-dev-plan/SKILL.md:134` ``

3. **외부 사이트 근거 (URL)**
   - 표준 포맷: `[사이트명/문서명](URL)` — Markdown 링크로 사람이 클릭, AI가 WebFetch 호출 가능
   - 예: `[FastAPI 공식 문서 — 미들웨어](https://fastapi.tiangolo.com/tutorial/middleware/)`
   - 예: `[shadcn/ui Button](https://ui.shadcn.com/docs/components/button)`

4. **필수 제약 인용 (기존 PM 포맷 재사용)**
   - 포맷: `[MUST] \`경로\` §{N}: <원문>` (로컬 문서) 또는 `[MUST] [사이트명](URL): <원문>` (외부)
   - 적용: 재해석 여지가 있는 금지사항·강제 규칙

> **설계 결정 근거**: `opal-pm.md:101-105` (§3 Step 3 인용 포맷)의 `[MUST]` 포맷을 산출물에 동일 적용하여 **PM 주입 포맷 ↔ 산출물 기록 포맷을 통일**한다. 외부 URL은 Markdown 링크로 표현하여 사람(클릭)과 AI(WebFetch) 모두 접근 가능하게 한다.

### 2.2 혼합 방식 (테이블 + 인라인)

| 방식 | 적용 위치 | 목적 |
|------|---------|------|
| **참조 문서 테이블** | 각 산출물 상단 §1 또는 전용 섹션 | 전체 참조 문서 개요 — 사람 탐색용 |
| **인라인 인용** | 설계 결정·분석 결과 문장 끝 | 구체 근거 — 어느 문장이 어느 문서의 어디에서 왔는지 |

**참조 문서 테이블 공통 컬럼**: `# | 유형 | 문서/사이트 | 경로/URL | 참조 이유`
- 유형: `기획` / `설계` / `소스` / `외부`
- 태스크 내 고유 ID(D-1, D-2...)로 인라인 인용에서 단축 참조 가능: "API camelCase 적용 (→ D-1 §3.1)"
- 외부 사이트는 경로/URL 컬럼에 Markdown 링크 형식 사용: `[FastAPI 미들웨어](https://...)`

### 2.3 단계별 의무 수준

TASK.md "미확정 사항 (PLAN에서 결정)"의 "단계별 차등 적용" 논의에 대한 결정.

| 단계 | 참조 문서 테이블 | 인라인 인용 | `[MUST]` 포맷 |
|------|---------------|-----------|--------------|
| **TASK** | 필수 (`# \| 유형 \| 문서/사이트 \| 경로/URL \| 참조 이유`) | 선택 — 설계 방향 문장에 근거 있을 때 | 선택 — 확정된 설계 방향 중 재해석 여지 규칙 |
| **ANALYSIS** | 필수 | **필수** — 관련 파일 맵에 `경로:줄번호`, 제약/리스크에 `경로 §N` 또는 `[사이트명](URL)` | 선택 — 제약 중 재해석 여지 규칙 |
| **PLAN** | 필수 (§8 또는 §1 최상단) | **필수** — 설계 결정 뒤에 `(→ D-N §N)` 단축 인용 | 필수 — 핵심 설계 중 금지/강제 규칙 |

**공통 예외 규칙**: TASK.md 제약 #3 "인용이 없는 항목(추론/경험 기반 결정)은 인용 생략 허용"를 유지한다. 단, 문서 근거가 명백히 있는 경우에는 필수.

> **설계 결정 근거**: 단계가 뒤로 갈수록(TASK → ANALYSIS → PLAN) 설계 결정이 구체화되므로 근거 의무 수준도 단계적으로 강화. `op-task/SKILL.md:140-143`의 "관련 문서" 섹션은 이미 선택적 참조 기재 위치로 존재하므로 테이블화만으로 의무 전환 가능.

### 2.4 하네스 §2 모듈 등록 설계

기존 모듈 테이블(`opal-harness.md:99-106`)과 동일한 스키마(`모듈 | 파일 | 로드 시점 | 해당 §`)로 행 추가:

```
| 인용 규칙 | `harness/citation-rules.md` | TASK/ANALYSIS/PLAN 산출물 작성 시 | §2 |
```

로드 주체: 워커 (산출물 작성 스킬 실행 시)
로드 시점: TASK.md / ANALYSIS.md / PLAN.md 작성 직전

### 2.5 citation-rules.md 모듈 구조

`header-rules.md` / `qa-standards.md` 포맷을 참조하여 다음 구조로 작성:

```
# 인용 규칙 (Citation Rules)

> 출처: opal-harness.md §2
> 로드 시점: TASK/ANALYSIS/PLAN 산출물 작성 시
> 역할: 산출물 인용 포맷 + 적용 시점 + 의무 수준

---

## 1. 적용 범위 및 목적
## 2. 인용 포맷
  ### 2.1 문서 근거 포맷
  ### 2.2 코드 근거 포맷
  ### 2.3 필수 제약 인용 포맷 ([MUST])
## 3. 적용 방식 (테이블 + 인라인)
## 4. 단계별 의무 수준
## 5. 예외 규칙
## 6. 사람/AI 탐색 가이드
```

---

## 3. 구현 계획

### 3.1 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| N-1 | `opal/core/references/harness/citation-rules.md` | 인용 규칙 하네스 모듈 (포맷/의무 수준/사람·AI 가이드) |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| M-1 | `opal/core/references/opal-harness.md` | §2 "하네스 모듈" 테이블에 citation-rules 행 추가 + 변경이력 행 추가 |
| M-2 | `opal/skills/op-task/SKILL.md` | "관련 문서" 섹션을 bullet → 테이블(`# \| 문서 \| 경로 \| 참조 이유`)로 전환. 작성 체크리스트에 인용 테이블 항목 추가. 변경이력 갱신 |
| M-3 | `opal/skills/op-dev-analysis/SKILL.md` | §1.1 관련 파일 목록 컬럼 확장(`파일 \| 역할 \| 변경 필요 \| 근거(줄번호)`). §5 제약/리스크에 "근거" 컬럼 추가. §6 추천 스킬/MCP에 근거 인용 지시. 맨 앞 또는 §7에 참조 문서 테이블 신설. 품질 체크리스트에 인용 항목 추가. 변경이력 갱신 |
| M-4 | `opal/skills/op-dev-plan/SKILL.md` | §3 핵심 설계 서브섹션(`3.N.1 파일 변경`·`3.N.2 API·데이터 모델·화면 설계`)에 인용 필드 지시 추가. §8 "기술 컨텍스트" 아래에 "참조 문서 테이블" 서브섹션 추가. 품질 체크리스트에 인용 항목 추가. 변경이력 갱신 |
| M-5 | `opal/skills/op-dev-plan/references/plan-guide.md` | 3단계(기능별 설계) 각 서브섹션에 인용 작성 지시 추가. "참조 문서 테이블 작성 가이드" 섹션 신설. 품질 체크리스트에 인용 항목 추가. 변경이력 갱신 |
| M-6 | `opal/skills/op-task-plan/SKILL.md` | §1 "현황 조사" 상단에 "참조 문서" 테이블 추가. §2 "핵심 설계"에 인용 필드 지시 추가. 품질 체크리스트에 인용 항목 추가. 변경이력 갱신 |
| M-7 | `opal/skills/op-task-plan/references/plan-guide.md` | 현황 조사 원칙 + 3단계 핵심 설계에 인용 작성 지시 추가. 품질 체크리스트에 인용 항목 추가. 변경이력 갱신 |

#### 삭제

없음.

### 3.2 구현 순서

의존성: `citation-rules.md (SSOT)` → `opal-harness.md §2 등록` → 각 스킬/가이드 참조

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | citation-rules.md 모듈 신규 작성 (SSOT) | N-1 | 중 (인용 포맷/의무 수준 전체 정의) |
| 2 | opal-harness.md §2 모듈 테이블에 citation-rules 등록 | M-1 | 하 (1행 추가 + 이력) |
| 3 | op-task SKILL.md "관련 문서" 테이블화 | M-2 | 하 |
| 4 | op-dev-analysis SKILL.md 인용 필드 반영 | M-3 | 중 |
| 5 | op-dev-plan SKILL.md 인용 필드 반영 | M-4 | 중 |
| 6 | op-dev-plan plan-guide.md 인용 지시 추가 | M-5 | 중 |
| 7 | op-task-plan SKILL.md 인용 필드 반영 | M-6 | 중 |
| 8 | op-task-plan plan-guide.md 인용 지시 추가 | M-7 | 하 |

**병렬 가능 구간**: Step 3~5/6/7/8은 서로 독립 파일(의존 없음). Step 2 완료 이후 Phase 2에서 전부 병렬.

### 3.3 핵심 설계 (파일별 상세)

#### N-1. `opal/core/references/harness/citation-rules.md` (신규)

**구조**: `header-rules.md:1-8` stub 포맷을 그대로 따른다 (출처 / 로드 시점 / 역할 명시 → 구분선 → 본문).

**본문 섹션**:

- **§1 적용 범위 및 목적**: TASK/ANALYSIS/PLAN 3단계 산출물에 문서·코드 근거를 추적한다. 목적은 (a) 사람의 원본 접근 즉시성 (b) AI의 재탐색 비용 절감 (c) 재해석 방지.
- **§2 인용 포맷**:
  - 2.1 문서 근거: `` `경로` §{N} {섹션명} `` 및 원문 포함 시 `` `경로` §{N}: "<원문>" ``
  - 2.2 코드 근거: `` `경로:줄번호` `` / `` `경로:N-M` ``
  - 2.3 필수 제약: `[MUST] `경로` §{N}: <원문>` — `opal-pm.md §3 Step 3` 포맷과 통일
- **§3 적용 방식**: 참조 문서 테이블(최상단/§8) + 인라인 인용(설계 결정 문장 끝) 혼합. 테이블 공통 컬럼 규정: `# | 유형 | 문서/사이트 | 경로/URL | 참조 이유`. 유형: 기획/설계/소스/외부
- **§4 단계별 의무 수준**: §2.3 테이블을 그대로 옮긴 의무 매트릭스. 워커가 산출물 작성 시 이 매트릭스를 확인.
- **§5 예외 규칙**: 추론/경험 기반 결정은 인용 생략 허용. 단, 문서 근거가 있으면 필수. 레거시 산출물 소급 변경 불필요.
- **§6 사람/AI 탐색 가이드**:
  - 사람: 백틱 경로를 복사하여 에디터 이동 또는 상대 경로로 접근
  - AI: Read 도구에 백틱 경로를 그대로 주입, `경로:줄번호` 패턴은 `offset`/`limit` 파라미터로 매핑 가능
- **변경이력 테이블**: v1.0, 2026-04-17, 초기 작성 (123)

**근거**: `opal/core/references/harness/header-rules.md:1-8` 모듈 stub 포맷 + `opal/core/references/harness/qa-standards.md:1-8` 모듈 stub 포맷.

#### M-1. `opal/core/references/opal-harness.md` §2 수정

**변경 위치**: `opal-harness.md:96-106` "하네스 모듈" 테이블.

**추가 행**:
```
| 인용 규칙 | `harness/citation-rules.md` | TASK/ANALYSIS/PLAN 산출물 작성 시 | §2 |
```

**변경이력 추가**: `opal-harness.md:348-376` 변경이력 테이블 맨 아래에 `v4.3 | 2026-04-17 | §2 하네스 모듈 테이블에 citation-rules 추가 — 산출물 인용 규칙 신설 (123)` 행 추가.

**근거**: `opal-harness.md:99-106` 기존 모듈 테이블 스키마(`모듈 | 파일 | 로드 시점 | 해당 §`)를 그대로 따른다.

#### M-2. `opal/skills/op-task/SKILL.md` 수정

**변경 위치**: `op-task/SKILL.md:140-143` "관련 문서" 섹션.

**변경 전** (bullet):
```
## 관련 문서

- {참고할 기존 문서, API 명세, 디자인 파일 등}
```

**변경 후** (테이블):
```
## 관련 문서

| # | 문서 | 경로 | 참조 이유 |
|---|------|------|----------|
| D-1 | {문서명} | `{경로}` | {참조 이유} |

> 인용 형식은 `opal/core/references/harness/citation-rules.md`를 따른다.
> 문서 근거가 없으면 이 섹션 생략 가능.
```

**작성 체크리스트 추가** (`op-task/SKILL.md:198-212` 하단): `- [ ] 관련 문서를 참조했다면 "관련 문서" 테이블에 경로와 참조 이유가 기재되었는가 (citation-rules.md 참조)`

**변경이력 갱신**: v1.3 | 2026-04-17 | "관련 문서" 섹션을 테이블 포맷으로 전환 + citation-rules 참조 지시 추가 (123)

**근거**: `opal/core/references/harness/citation-rules.md §3` (참조 문서 테이블 공통 컬럼 규정).

#### M-3. `opal/skills/op-dev-analysis/SKILL.md` 수정

**변경 위치**: `op-dev-analysis/SKILL.md:60-124` ANALYSIS.md 통일 형식 템플릿.

**변경 내용**:

1. **§1.1 관련 파일 목록 컬럼 확장** (`op-dev-analysis/SKILL.md:69-71`):
   ```
   | 파일 | 역할 | 변경 필요 | 근거(줄번호) |
   |------|------|----------|-------------|
   ```
   근거 컬럼은 `파일:N-M` 포맷 — 핵심 로직 위치. 없으면 `-`.

2. **§3 영향 범위 - 직접 영향 인용**: 직접 영향 파일에 `경로:줄번호` 인용 의무화.

3. **§5 제약/리스크 컬럼 확장** (`op-dev-analysis/SKILL.md:107-109`):
   ```
   | 항목 | 설명 | 심각도 | 근거 |
   |------|------|--------|------|
   ```
   근거: `경로 §N` 또는 `경로:줄번호` 또는 "없음".

4. **템플릿 최상단 "참조 문서" 섹션 신설** (§0 또는 §1 앞):
   ```
   ## 0. 참조 문서
   | # | 문서 | 경로 | 참조 이유 |
   |---|------|------|----------|
   ```

5. **분석 품질 체크리스트 추가** (`op-dev-analysis/SKILL.md:136-144`):
   - `- [ ] 관련 파일 목록에 근거(줄번호) 컬럼이 채워져 있는가 (인용 생략 항목은 "-" 표기)`
   - `- [ ] 제약/리스크에 근거(§N 또는 줄번호)가 기재되어 있는가`
   - `- [ ] §0 참조 문서 테이블이 작성되어 있는가`

6. **변경이력 갱신**: v1.3 | 2026-04-17 | §0 참조 문서 테이블 신설 + §1.1/§5 근거 컬럼 추가 + citation-rules 적용 (123)

**근거**: `opal/core/references/harness/citation-rules.md §2.2 코드 근거 포맷` + `§4 단계별 의무 수준` (ANALYSIS는 인라인 인용 필수).

#### M-4. `opal/skills/op-dev-plan/SKILL.md` 수정

**변경 위치**:

1. **§3 핵심 설계 서브섹션** (`op-dev-plan/SKILL.md:213-252` `#### 3.N.1 파일 변경 계획`, `#### 3.N.2 API·데이터 모델·화면 설계`):
   - `3.N.1` 신규/수정 테이블에 `근거` 컬럼 추가:
     ```
     | # | 경로 | 영역 | 변경 내용 요약 | 근거 |
     ```
     근거: 설계 결정 근거 문서·섹션 또는 선행 코드 경로:줄번호.
   - `3.N.2` 상단에 지시문 추가: "각 설계 결정 뒤에 인라인 인용(`경로 §N` / `경로:줄번호`)을 기재한다. `[MUST]` 포맷은 citation-rules.md §2.3 참조."

2. **§8 기술 컨텍스트 확장** (`op-dev-plan/SKILL.md:322-329`):
   ```
   ## 8. 기술 컨텍스트

   ### 8.1 기술 스택
   | 영역 | 기술 | 적용 스킬 |
   |------|------|----------|

   ### 8.2 사용 MCP
   | MCP | 조회 결과 요약 |
   |-----|--------------|

   ### 8.3 참조 문서 (설계 결정 근거)
   | # | 문서 | 경로 | 참조 이유 |
   |---|------|------|----------|
   ```

3. **품질 체크리스트 추가** (`op-dev-plan/SKILL.md:400-420`):
   - `- [ ] §3 기능별 설계에 인라인 인용(경로 §N 또는 경로:줄번호)이 기재되어 있는가`
   - `- [ ] §8.3 참조 문서 테이블이 작성되어 있는가`
   - `- [ ] 재해석 여지가 있는 제약은 [MUST] 포맷으로 기재되어 있는가 (citation-rules.md §2.3)`

4. **변경이력 갱신**: v2.3 | 2026-04-17 | §3 설계 근거 컬럼 추가 + §8.3 참조 문서 테이블 신설 + citation-rules 적용 (123)

**근거**: `opal/core/references/harness/citation-rules.md §3 적용 방식` (테이블 + 인라인 혼합) + `§4 단계별 의무 수준` (PLAN은 인라인 + `[MUST]` 필수).

#### M-5. `opal/skills/op-dev-plan/references/plan-guide.md` 수정

**변경 위치**:

1. **3단계 기능별 설계** (`plan-guide.md:110-171`):
   - `3.N.1 파일 변경 계획` 테이블 스키마에 `근거` 컬럼 추가.
   - `3.N.2 API·데이터 모델·화면 설계` 상단에 지시문 추가: "각 설계 결정(클래스 구조, 함수 시그니처, 데이터 모델, API) 뒤에 인라인 인용 기재. 포맷: `opal/core/references/harness/citation-rules.md §2` 참조."

2. **"참조 문서 테이블 작성 가이드" 섹션 신설** (3단계와 4단계 사이):
   ```
   ## 3.5단계: 참조 문서 테이블 (§8.3)

   PLAN.md §8.3에 설계 결정에 사용한 문서를 테이블로 기록한다.
   컬럼: # | 문서 | 경로 | 참조 이유
   포맷 규정: citation-rules.md §3
   ```

3. **품질 체크리스트 추가** (`plan-guide.md:391-408`):
   - 동일한 3개 항목 (M-4와 동일).

4. **변경이력 갱신**: v2.2 | 2026-04-17 | 3단계 설계 인용 지시 추가 + 3.5단계 참조 문서 테이블 가이드 신설 (123)

**근거**: `opal/skills/op-dev-plan/SKILL.md:137` "plan-guide.md의 3단계를 따른다" — 가이드 역시 SKILL.md와 정합하게 갱신.

#### M-6. `opal/skills/op-task-plan/SKILL.md` 수정

**변경 위치**:

1. **PLAN.md 출력 형식 §1 확장** (`op-task-plan/SKILL.md:120-128`):
   ```
   ## 1. 현황 조사

   ### 참조 문서 (PLAN 작성 근거)
   | # | 문서 | 경로 | 참조 이유 |
   |---|------|------|----------|

   ### 관련 파일
   | 파일 | 역할 | 변경 필요 | 근거(줄번호) |
   |------|------|----------|-------------|

   ### 현재 상태
   ### 영향 범위
   ```

2. **§2 핵심 설계 확장** (`op-task-plan/SKILL.md:143-144`):
   - §2.핵심 설계 상단에 지시문: "각 파일별 변경 내용 뒤에 인라인 인용(`경로 §N` / `경로:줄번호`) 기재. 포맷: `opal/core/references/harness/citation-rules.md`"
   - 신규/수정 테이블 스키마에 `근거` 컬럼 추가.

3. **품질 체크리스트 추가** (`op-task-plan/SKILL.md:173-183`):
   - `- [ ] §1 참조 문서 테이블이 작성되어 있는가`
   - `- [ ] §2 핵심 설계에 인라인 인용이 기재되어 있는가`
   - `- [ ] 재해석 여지가 있는 제약은 [MUST] 포맷으로 기재되어 있는가`

4. **변경이력 갱신**: v1.2 | 2026-04-17 | §1 참조 문서 테이블 신설 + §2 설계 인용 필드 추가 + citation-rules 적용 (123)

**근거**: `opal/core/references/harness/citation-rules.md §4 단계별 의무 수준` + `opal/skills/op-dev-plan/SKILL.md` 변경(M-4)과의 일관성.

#### M-7. `opal/skills/op-task-plan/references/plan-guide.md` 수정

**변경 위치**:

1. **현황 조사 원칙 섹션** (`op-task-plan/references/plan-guide.md:10-29`):
   - 조사 항목에 "참조 문서 목록 구성"을 추가.

2. **3단계 핵심 설계** (`op-task-plan/references/plan-guide.md:71-81`):
   - 작성해야 할 내용 bullet에 "근거 인용: `citation-rules.md §2` 참조" 추가.

3. **품질 체크리스트 추가** (`op-task-plan/references/plan-guide.md:147-154`):
   - 동일한 3개 항목 (M-6과 동일).

4. **변경이력 갱신**: v1.1 | 2026-04-17 | 현황 조사에 참조 문서 구성 + 3단계 인용 지시 추가 (123)

**근거**: `opal/skills/op-task-plan/SKILL.md:74` "plan-guide.md의 1단계를 따른다" — SKILL.md 변경과 정합.

---

## 4. 실행 체크리스트

> 총 8개 Step | Phase 2개
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1 | 1 | 순차 | citation-rules.md SSOT 먼저 작성 |
> | 1 | 2 | 순차 | Step 1 완료 후 opal-harness.md §2 등록 |
> | 2 | 3, 4, 5, 6, 7, 8 | 병렬 | 서로 독립 파일, citation-rules.md/opal-harness.md 참조만 |

### Step 1: citation-rules.md 모듈 신규 작성
- [x] 완료
- **파일**: `opal/core/references/harness/citation-rules.md`
- **작업 내용**: stub(출처/로드 시점/역할) + §1 적용 범위 + §2 인용 포맷(문서/코드/MUST) + §3 적용 방식(테이블+인라인) + §4 단계별 의무 수준 + §5 예외 규칙 + §6 사람/AI 탐색 가이드 + 변경이력 작성
- **완료 기준**: 파일이 생성되고 §1~§6 모든 섹션이 작성되어 있다. 인용 포맷 3종(문서/코드/MUST)의 예시가 포함되어 있다. 단계별 의무 수준 매트릭스(TASK/ANALYSIS/PLAN × 테이블/인라인/MUST)가 테이블로 존재한다
- **테스트**: 파일 Read 후 stub(출처/로드 시점/역할) 3줄 존재 확인 + 단계별 의무 매트릭스 3행 존재 확인 + 인용 포맷 예시 3종 존재 확인
- **의존**: 없음

### Step 2: opal-harness.md §2 모듈 테이블 등록
- [x] 완료
- **파일**: `opal/core/references/opal-harness.md`
- **작업 내용**: §2 하네스 모듈 테이블(라인 99-106)에 citation-rules 행 추가. 변경이력 테이블에 v4.3 행 추가
- **완료 기준**: 테이블에 `| 인용 규칙 | \`harness/citation-rules.md\` | TASK/ANALYSIS/PLAN 산출물 작성 시 | §2 |` 행이 존재하고, 변경이력에 v4.3 | 2026-04-17 항목이 추가됨
- **테스트**: Grep `citation-rules` 실행 시 opal-harness.md에서 해당 행 매칭 + 변경이력 테이블 v4.3 존재 확인
- **의존**: Step 1

### Step 3: op-task/SKILL.md "관련 문서" 섹션 테이블화
- [x] 완료
- **파일**: `opal/skills/op-task/SKILL.md`
- **작업 내용**: 라인 140-143 "관련 문서" bullet 섹션을 `# | 문서 | 경로 | 참조 이유` 컬럼 테이블로 전환. citation-rules.md 참조 지시 추가. 작성 체크리스트에 인용 테이블 항목 추가. 변경이력 v1.3 추가
- **완료 기준**: TASK.md 템플릿의 "관련 문서" 섹션이 4컬럼 테이블이고 citation-rules 참조 한 줄 포함. 작성 체크리스트에 `- [ ] 관련 문서를 참조했다면 "관련 문서" 테이블에 경로와 참조 이유가 기재되었는가` 항목 존재
- **테스트**: Grep `\| # \| 문서 \| 경로 \| 참조 이유 \|` op-task/SKILL.md에서 매칭
- **의존**: Step 2

### Step 4: op-dev-analysis/SKILL.md 인용 필드 반영
- [x] 완료
- **파일**: `opal/skills/op-dev-analysis/SKILL.md`
- **작업 내용**: ANALYSIS.md 통일 형식에 §0 참조 문서 테이블 신설, §1.1 관련 파일 목록에 `근거(줄번호)` 컬럼 추가, §5 제약/리스크에 `근거` 컬럼 추가, §3 직접 영향에 경로:줄번호 인용 의무 기재. 품질 체크리스트 3개 항목 추가. 변경이력 v1.3 추가
- **완료 기준**: 템플릿에 §0 참조 문서 테이블 존재, §1.1/§5 컬럼 확장 완료, 품질 체크리스트 3개 추가 항목 존재
- **테스트**: Grep `## 0. 참조 문서` op-dev-analysis/SKILL.md에서 매칭 + `근거(줄번호)` 매칭
- **의존**: Step 2

### Step 5: op-dev-plan/SKILL.md 인용 필드 반영
- [x] 완료
- **파일**: `opal/skills/op-dev-plan/SKILL.md`
- **작업 내용**: PLAN.md §3 파일 변경 테이블에 `근거` 컬럼 추가, §3.N.2 상단 인라인 인용 지시문 추가, §8을 §8.1/§8.2/§8.3으로 분할하고 §8.3 참조 문서 테이블 신설, 품질 체크리스트 3개 항목 추가. 변경이력 v2.3 추가
- **완료 기준**: §3 테이블 스키마 확장, §8.3 섹션 존재, 품질 체크리스트 추가 항목 존재
- **테스트**: Grep `### 8.3 참조 문서` op-dev-plan/SKILL.md에서 매칭
- **의존**: Step 2

### Step 6: op-dev-plan/references/plan-guide.md 인용 지시 추가
- [x] 완료
- **파일**: `opal/skills/op-dev-plan/references/plan-guide.md`
- **작업 내용**: 3단계 기능별 설계 `3.N.1`에 `근거` 컬럼 추가, `3.N.2` 상단 인라인 인용 지시문 추가, "3.5단계: 참조 문서 테이블" 섹션 신설, 품질 체크리스트 3개 항목 추가. 변경이력 v2.2 추가
- **완료 기준**: 3단계 설계 지시 갱신, 3.5단계 섹션 존재, 품질 체크리스트 갱신
- **테스트**: Grep `3.5단계: 참조 문서 테이블` plan-guide.md에서 매칭
- **의존**: Step 2

### Step 7: op-task-plan/SKILL.md 인용 필드 반영
- [x] 완료
- **파일**: `opal/skills/op-task-plan/SKILL.md`
- **작업 내용**: PLAN.md 출력 형식 §1 최상단에 "참조 문서" 테이블 추가, "관련 파일" 테이블에 `근거(줄번호)` 컬럼 추가, §2 핵심 설계에 인라인 인용 지시문 + 테이블 `근거` 컬럼 추가, 품질 체크리스트 3개 항목 추가. 변경이력 v1.2 추가
- **완료 기준**: §1 참조 문서 테이블 존재, §2 인용 지시 존재, 품질 체크리스트 갱신
- **테스트**: Grep `### 참조 문서 \(PLAN 작성 근거\)` op-task-plan/SKILL.md에서 매칭
- **의존**: Step 2

### Step 8: op-task-plan/references/plan-guide.md 인용 지시 추가
- [x] 완료
- **파일**: `opal/skills/op-task-plan/references/plan-guide.md`
- **작업 내용**: 현황 조사 항목에 "참조 문서 목록 구성" 추가, 3단계 핵심 설계에 "근거 인용" bullet 추가, 품질 체크리스트 3개 항목 추가. 변경이력 v1.1 추가
- **완료 기준**: 현황 조사·3단계 설계 지시 갱신, 품질 체크리스트 갱신
- **테스트**: Grep `참조 문서 목록 구성` plan-guide.md에서 매칭
- **의존**: Step 2

---

## 5. QA 체크리스트

### 기능 테스트
- [x] citation-rules.md 파일이 존재하고 §1~§6 섹션이 모두 작성되어 있다 (R-1)
- [x] citation-rules.md에 인용 포맷 3종(문서/코드/MUST)의 구체 예시가 포함되어 있다 (R-1)
- [x] citation-rules.md에 단계별 의무 수준 매트릭스(TASK/ANALYSIS/PLAN × 테이블/인라인/MUST)가 존재한다 (R-1)
- [x] opal-harness.md §2 모듈 테이블에 `citation-rules` 행이 등록되어 있다 (R-2)
- [x] opal-harness.md 변경이력에 v4.3 (2026-04-17, 123) 항목이 추가되었다 (R-2)
- [x] op-task/SKILL.md "관련 문서" 섹션이 `# \| 문서 \| 경로 \| 참조 이유` 테이블 포맷으로 전환되었다 (R-3)
- [x] op-dev-analysis ANALYSIS.md 통일 형식의 §0 참조 문서 테이블이 추가되었다 (R-4)
- [x] op-dev-analysis §1.1/§5에 근거 컬럼이 추가되었다 (R-4)
- [x] op-dev-plan PLAN.md §3 설계 섹션에 근거 필드가 추가되고 §8.3 참조 문서 테이블이 신설되었다 (R-5)
- [x] op-dev-plan plan-guide.md 3단계 + 3.5단계에 인용 작성 지시가 추가되었다 (R-5)
- [x] op-task-plan SKILL.md §1 참조 문서 테이블 + §2 인용 필드가 추가되었다 (R-6)
- [x] op-task-plan plan-guide.md에 인용 작성 지시가 추가되었다 (R-6)

### 일관성 테스트
- [x] 모든 참조 문서 테이블이 공통 컬럼 스키마(`# | 문서 | 경로 | 참조 이유`)를 따른다
- [x] 인용 포맷이 citation-rules.md §2의 표준과 일치한다 (`경로 §N` / `경로:줄번호` / `[MUST] 경로 §N: <원문>`)
- [x] `[MUST]` 포맷이 `opal-pm.md §3 Step 3` 기존 포맷과 호환된다
- [x] 하네스 모듈 stub(출처/로드 시점/역할) 포맷이 기존 모듈(`header-rules.md`/`qa-standards.md`)과 일치한다
- [x] 모든 수정 파일의 변경이력에 2026-04-17 / 123 행이 추가되었다
- [x] 6개 SKILL.md/plan-guide.md 수정 모두 citation-rules.md를 참조한다 (SSOT 일원화)

### 문서 품질
- [x] 한국어 본문 + 영어 코드/필드명 규칙 준수
- [x] kebab-case 파일 네이밍 준수 (`citation-rules.md`)
- [x] Markdown 테이블 문법 유효
- [x] citation-rules.md의 변경이력이 `| 버전 | 날짜 | 변경내용 |` 형식 준수
- [x] 각 수정 파일의 변경이력 행이 `(123)` 태스크 번호로 태깅됨

---

## 6. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| 인용 의무가 워커 작업 부하를 증가시킬 수 있음 | TASK/ANALYSIS/PLAN 작성 시간 증가 | citation-rules.md §5 예외 규칙(추론/경험 기반은 생략)으로 완화. 핵심 제약만 `[MUST]` 필수 |
| 기존 산출물과 신규 산출물 간 포맷 불일치 | 레거시 문서 참조 시 혼란 | TASK.md 제약 #2(레거시 소급 변경 불필요) 명시 + citation-rules.md §5에서 레거시 호환 선언 |
| 6개 스킬 파일 동시 수정으로 정합성 깨질 위험 | 인용 포맷이 파일마다 달라질 수 있음 | SSOT 원칙 적용: 모든 스킬이 `citation-rules.md`를 참조하고 포맷 자체는 기재하지 않음. 포맷 변경은 citation-rules.md 한 곳에서만 |
| `[MUST]` 포맷이 기존 `opal-pm.md` 포맷과 미세 차이 | PM ↔ 워커 간 포맷 불일치 | citation-rules.md §2.3에서 `opal-pm.md §3 Step 3` 포맷 원문 인용 후 경로를 백틱으로 확장한 "상위 호환 규정" 명시 |
| 하네스 §2 테이블 확장이 다른 모듈 로드 규칙에 영향 | 기존 모듈 로드 누락 가능성 | 단순 행 추가 (기존 행 변경 없음). Step 2에서 diff 확인 |
| plan-guide.md 변경이 SKILL.md 변경과 어긋날 위험 | 워커가 SKILL.md ↔ guide 상반 지시 | Step 5/6, Step 7/8을 쌍으로 실행. QA 일관성 테스트에서 상호 참조 확인 |
