# PLAN: Citation Rules 하네스 보편화 — SSOT 완성 + Trigger 주입

> 작성일: 2026-04-24
> 입력: TASK.md (R-1~R-8 + 제약 §8 + 로드맵 §5 + 잠정 파일 목록 §7)
> 출력: PLAN.md
> 모드: 범용 (op-task-plan), 영역 분류=문서 (프레임워크 문서 작업)

---

## 1. 현황 조사

### 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | SSOT 본체 — 기존 §1~§6 구조 보존하며 R-1~R-4 삽입 위치 결정 근거 |
| D-2 | 설계 | opal-harness.md | `opal/core/references/opal-harness.md` | §2 "모듈 구조" 하위에 R-6 "Citation Rules 적용 의무" 블록 추가 대상 |
| D-3 | 소스 | opwt consistency-rules.md | `opal/skills/opal-pilot-write-tech/references/consistency-rules.md` | §1 유형 간 검증(양방향)의 "용어 매핑 테이블" 패턴 참조 — R-4 영역 간 용어 일관성 구조 설계 힌트 |
| D-4 | 소스 | op-dev-plan plan-guide.md | `opal/skills/op-dev-plan/references/plan-guide.md` | 현재 citation 적용 형태 확인 (0단계·3단계 기술 컨텍스트 로딩 구조) |
| D-5 | 소스 | op-task-plan SKILL.md | `opal/skills/op-task-plan/SKILL.md` | R-7 주입 대상 + 본 스킬 구조 (프로세스·실행 컨텍스트 섹션) 참조 |
| D-6 | 소스 | op-sdd-plan SKILL.md | `opal/skills/op-sdd-plan/SKILL.md` | R-7 주입 대상 (실행 컨텍스트 섹션 구조) |
| D-7 | 설계 | opal-harness-agentic.md §6 | `~/.opal/references/opal-harness-agentic.md` | §6 에스컬레이션 조건 (판단 모호 시 기본 에스컬레이션) — R-4 `decision_required` 원칙 정합성 확인 |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §3.1 준수. 유형: `기획` / `설계` / `소스` / `외부`.

### 수정 대상 파일 확정 결과 (R-7 Glob 확정)

TASK.md §7 R-7 잠정 목록 17개 중 **모두 존재 확인 완료**. 누락/스킵 없음.

| # | 파일 경로 | 카테고리 | 존재 여부 | 주입 위치 근거 |
|---|-----------|---------|----------|---------------|
| F-1 | `opal/skills/opal-pilot-project/SKILL.md` | pilot | 존재 | `L11 ## Harness` 아래, L20 `---` 앞 |
| F-2 | `opal/skills/opal-pilot-project-dev/SKILL.md` | pilot | 존재 | `L22 ## Harness` 아래, L30 `---` 앞 |
| F-3 | `opal/skills/opal-pilot-dev/SKILL.md` | pilot | 존재 | `L10 ## Harness` 아래, L17 블랭크 앞 |
| F-4 | `opal/skills/opal-pilot-dev-short/SKILL.md` | pilot | 존재 | `L12 ## Harness` 아래, L19 `---` 앞 |
| F-5 | `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | pilot | 존재 | `L11 ## Harness` 아래, L18 `---` 앞 |
| F-6 | `opal/skills/opal-pilot-sdd/SKILL.md` | pilot | 존재 | `L21 ## Harness` 아래, L29 `---` 앞 |
| F-7 | `opal/skills/opal-pilot-write-tech/SKILL.md` | pilot | 존재 | `L13 ## Harness` 아래, L21 `## 설계 원칙` 앞 |
| F-8 | `opal/skills/opal-pilot-gc/SKILL.md` | pilot | 존재 | `L11 ## Harness` 아래, L22 `---` 앞 |
| F-9 | `opal/skills/op-dev-plan/SKILL.md` | PLAN 스킬 | 존재 | `L12 ## 실행 컨텍스트` 아래, L17 `---` 앞 |
| F-10 | `opal/skills/op-dev-plan/references/plan-guide.md` | PLAN 가이드 | 존재 | `L10 ## 0단계: 기술 컨텍스트 로딩` 앞 (가이드 서두) |
| F-11 | `opal/skills/op-task-plan/SKILL.md` | PLAN 스킬 | 존재 | `L12 ## 실행 컨텍스트` 아래, L17 `---` 앞 |
| F-12 | `opal/skills/op-sdd-plan/SKILL.md` | PLAN 스킬 | 존재 | `L13 ## 실행 컨텍스트` 아래, L18 `---` 앞 |
| F-13 | `opal/skills/op-sdd-action-plan/SKILL.md` | PLAN 스킬 | 존재 | `L14 ## 실행 컨텍스트` 아래, L19 블랭크 앞 |
| F-14 | `opal/skills/op-task/SKILL.md` | TASK 스킬 | **존재 확인** | `L11 ## 실행 컨텍스트` 아래, L15 블랭크 앞 |
| F-15 | `opal/skills/op-dev-analysis/SKILL.md` | ANALYSIS 스킬 | **존재 확인** | `L11 ## 실행 컨텍스트` 아래, L17 블랭크 앞 |
| F-16 | `opal/skills/op-dev-qa/SKILL.md` | QA 스킬 | 존재 | `L11 ## 실행 컨텍스트` 아래, L17 블랭크 앞 (또는 `## 프로세스` L41 Step 1 앞) |
| F-17 | `opal/skills/op-dev-qa/references/qa-dev-guide.md` | QA 가이드 | 존재 | `L7 ## 목적` 앞 (가이드 서두) |
| F-18 | `opal/skills/op-task-qa/SKILL.md` | QA 스킬 | **존재 확인** | `L12 ## 실행 컨텍스트` 아래, L19 블랭크 앞 |

> TASK.md §7 R-7에 "존재 확인 필요"로 표기된 3개(op-task/SKILL.md, op-dev-analysis/SKILL.md, op-task-qa/SKILL.md) 모두 실재 확인.
> **총 R-7 대상 파일: 18개** (잠정 17개 목록은 카테고리 합산 시 op-dev-plan 가이드까지 포함해 실제 18개 경로).
> citation-rules.md 본체(R-1~R-5) + opal-harness.md(R-6) 포함 **총 수정 대상: 20개 파일**.

### 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/core/references/harness/citation-rules.md` | SSOT 본체 | **예** (R-1~R-5) | 전체 구조 `opal/core/references/harness/citation-rules.md:1-225` |
| `opal/core/references/opal-harness.md` | 공통 하네스 §2 | **예** (R-6) | §2 모듈 구조 `opal/core/references/opal-harness.md:59-107` |
| R-7 18개 파일 | pilot/스킬/가이드 트리거 주입 | **예** (R-7) | 상단 테이블 참조 |
| `opal/skills/opal-pilot-write-tech/references/consistency-rules.md` | 설계 힌트 (용어 일관성) | 아니오 (참조용) | `opal/skills/opal-pilot-write-tech/references/consistency-rules.md:1-60` |
| `~/.opal/references/opal-harness-agentic.md` | 에스컬레이션 정합성 | 아니오 (참조용) | §6 에스컬레이션 조건 |

### 현재 상태

- citation-rules.md는 이미 §1~§6 골격 확보 — (§1 적용 범위·목적 / §2 인용 포맷 4종 / §3 적용 방식 / §4 단계별 의무 수준 / §5 예외 / §6 탐색 가이드). v1.0 2026-04-17 초판 완결 상태 (→ D-1 §변경이력).
- 그러나 **"상상·추정 금지" 최상위 원칙**이 명시적으로 선언되어 있지 않음 — §1 목적에 "재해석 방지"만 간접 기재 (→ D-1 §1 목적 3항).
- **트랙 구분(비개발/개발)** 개념 부재 — 현 §2는 4종 포맷 나열이지 트랙별 매트릭스가 없음.
- **[MUST] 토큰 대상 구체 목록** 부재 — §2.4에서 포맷만 보여주고 대상 유형 나열 없음.
- **영역 간 용어 일관성 검토 + `decision_required` 계약** 부재.
- opal-harness.md §2는 이미 citation-rules를 "Lazy 로드 모듈" 표(§4.3 변경이력 기준 v4.3)에 등록했으나, **"pilot 필수 적용 의무 블록"은 부재**.
- op-dev-plan SKILL.md / plan-guide.md는 **이미 citation-rules §3.1, §2, §2.4 인라인 참조를 포함** (v2.3 2026-04-17 반영) — 트리거 주입 시 이 기존 참조와 중복 없이 배치 필요 (→ D-4 전체).
- pilot SKILL.md 8개는 공통적으로 `## Harness` → `[MUST] 서브 하네스 Read` → `---` 구조. 트리거 주입 위치가 균질 (→ F-1~F-8 근거 줄번호).
- PLAN/TASK/ANALYSIS/QA 스킬은 `## 실행 컨텍스트` 섹션을 공통으로 보유 — 동일 위치 주입 가능.

### 영향 범위

- **하위호환**: citation-rules.md §2~§6은 [MUST] 구조 보존 (제약 §8). 신설 섹션은 §1 앞 또는 §1과 §2 사이, §4 아래에 **삽입**만. 기존 섹션 번호 변동 시 §2~§6 참조하는 외부 문서(opal-pm.md §3, op-dev-plan SKILL.md §229, plan-guide.md 등) 링크 영향 → **기존 §2~§6 번호는 보존**, 신설은 §0, §1.5, §4.5 등 하위 번호나 신규 §7로 배치한다.
- **opal-harness.md §2 Lazy 로드 모듈 테이블** (`opal-harness.md:84-94`)의 `citation-rules` 행은 유지하며 **별도 블록으로 "Citation Rules 적용 의무" 추가** (제약 §8 충돌 금지).
- **op-dev-plan 계열 기존 인라인 참조**는 재작성하지 않음 — 트리거 1줄만 추가 (R-7).
- **Trigger 블록 내 규칙 내용 복제 금지** (제약 §8) — 1줄 형식 엄수.

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

해당 없음 (기존 파일 편집만 수행).

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| 1 | `opal/core/references/harness/citation-rules.md` | §0(또는 §1.0) 근거 제시 원칙 [MUST] 선언 신설(R-1), §1 앞 또는 §1~§2 사이에 §1.5 트랙 매트릭스 신설(R-2), §2.4 아래 §2.5 [MUST] 토큰 대상 6종 + Good/Bad 예시(R-3), §7 "영역 간 용어 일관성 검토 + decision_required 계약" 신설(R-4), 변경이력 v2.0 행 추가(R-5) | TASK.md R-1~R-5, D-1 §1~§6 전체 |
| 2 | `opal/core/references/opal-harness.md` | §2 "모듈 구조" 아래, 기존 "QA 산출물 표준 및 검증" 소섹션과 대칭되는 위치에 **"Citation Rules 적용 의무"** 블록 신설(R-6) + 변경이력 v4.5 행 추가 | TASK.md R-6, D-2 §2:59-107 |
| 3~20 | R-7 18개 파일 | `## Harness` 또는 `## 실행 컨텍스트` 하위 / 가이드 서두에 **트리거 1줄 주입**(R-7) + 각 파일 변경이력 테이블에 태스크 130 행 추가(R-8) | TASK.md R-7, R-8, F-1~F-18 |

#### 삭제

해당 없음 (제약 §8: 기존 §2~§6 구조 보존).

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | citation-rules.md 본체 R-1~R-4 + R-5 변경이력 (SSOT 완성) | citation-rules.md | 중 (§구조 재편) |
| 2 | opal-harness.md R-6 적용 의무 블록 + 변경이력 | opal-harness.md | 하 |
| 3a | pilot SKILL.md 8개 트리거 주입 + 변경이력 | F-1~F-8 | 하 (1줄+1줄) |
| 3b | PLAN 스킬 5개 + PLAN 가이드 1개 트리거 주입 + 변경이력 | F-9~F-13, F-10 | 하 |
| 3c | TASK/ANALYSIS/QA 스킬 5개 트리거 주입 + 변경이력 | F-14~F-18 | 하 |
| 4 | 전 수정 파일 변경이력 일괄 점검(R-8 최종 확인) | 모든 수정 파일 | 하 |

원칙: **의존 받는 쪽(SSOT 본체)부터 먼저**. citation-rules.md가 완성돼야 R-7 트리거가 참조하는 섹션 경로가 정합.

### 핵심 설계

#### C-1. citation-rules.md 본체 재편 (R-1~R-5)

> 기존 §1~§6 구조 보존, 신설은 `§0 근거 제시 원칙` + `§1.5 트랙별 근거 매트릭스` + `§2.5 [MUST] 토큰 대상` + `§7 영역 간 용어 일관성 + decision_required` (→ D-1 §2.4 "[MUST] 포맷", 제약 §8).

**§0 근거 제시 원칙 신설** (R-1, 현 §1 "적용 범위 및 목적" **앞**에 삽입):

- `[MUST]` 포맷 선언: "상상·추정·기억 기반 기재 금지 — 모든 분석·설계 결정은 문서 근거(경로/URL + 섹션/줄번호)를 인용해야 한다."
- 이 원칙이 pilot·스킬 전반에 강제 적용됨을 1~2줄로 선언 (→ TASK.md §2 캡틴 원칙 요약 일치).
- 위치 근거: §1 "적용 범위 및 목적"의 "목적" 항목이 기존에 간접 언급만 했으므로 **서두 직전에 최상위 원칙으로 배치** (→ D-1 §1:9-27).

**§1.5 개발/비개발 트랙별 근거 매트릭스 신설** (R-2, 현 §1 하위 또는 §1과 §2 사이):

- 행: `비개발 트랙` / `개발 트랙`
- 열: `문서` / `웹` / `기획 산출물` / `설계 산출물` / `소스 코드`
- 셀 값: `필수` / `선택` / `불필요`
- 비개발 트랙: 문서=필수, 웹=필수, 기획/설계/소스=선택
- 개발 트랙: 문서=필수, 웹=선택, 기획 산출물=필수, 설계 산출물=필수, 소스 코드=필수 (→ TASK.md R-2 AC)
- 매트릭스 뒤 1줄: "트랙 판별은 산출물 유형으로 한다 — 기획 문서(PRD/TRD/정책서/IA) = 비개발 / 코드·설계 산출물(ANALYSIS/PLAN/EXECUTE 관련) = 개발"

**§2.5 개발 트랙 [MUST] 토큰 대상 구체화 신설** (R-3, 현 §2.4 [MUST] 포맷 바로 아래):

토큰 유형 6종 나열 + 각 유형별 Good/Bad 예시 1쌍:

1. **필드명** — Good: `` [MUST] `docs/CONVENTIONS.md` §3.1: "API 응답은 camelCase" `` / Bad: `"API 응답은 camelCase다 (컨벤션 문서 참고)"`
2. **함수 시그니처** — Good: `` [MUST] `src/user.py:45`: "def create_user(email: str) -> User" `` / Bad: `"create_user는 email 받는다"`
3. **타입명** — Good: `` [MUST] `src/types/user.ts:12`: "type UserRole = 'admin' | 'member'" `` / Bad: `"UserRole은 admin 또는 member"`
4. **ERD 컬럼명** — Good: `` [MUST] `docs/ERD.md` §2.3: "users.deleted_at TIMESTAMP NULL" `` / Bad: `"users 테이블에 deleted_at 있음"`
5. **IA 화면 ID/라우트** — Good: `` [MUST] `docs/IA.md` §4.1: "SCREEN-U001 /settings/profile" `` / Bad: `"설정 페이지 경로"`
6. **정책 조항 번호** — Good: `` [MUST] `docs/policy.md` §5.2.1: "만 14세 미만 가입 불가" `` / Bad: `"14세 제한 정책"`

**§7 영역 간 용어 일관성 검토 + `decision_required` 계약 신설** (R-4, 기존 §6 뒤):

§7.1 검출 대상 영역 쌍:
- FE ↔ BE (타입/필드/API 필드명 불일치)
- 정책서 ↔ 코드 (정책 용어 ↔ 변수/함수명)
- ERD ↔ 코드 (DB 컬럼명 ↔ ORM 모델 필드)
- IA ↔ FE 라우트 (화면 ID ↔ 라우트 path)

§7.2 검출 의무:
- 워커는 산출물 작성 중 위 영역 쌍에서 **동일 개념이 다른 토큰으로 나타나는 경우** 능동 검출하여 산출물 §리스크 섹션에 기재 (→ D-3 §1 "용어 매핑 테이블 기준" 패턴 차용).

§7.3 산출물 §리스크 기재 포맷 예시:
```
| # | 리스크 | 영향 | 대응 |
|---|--------|------|------|
| R-T1 | 용어 불일치 — FE `userType` ↔ BE `subType` | API 직렬화 실패 위험 | decision_required 에스컬레이션 |
```

§7.4 `decision_required` JSON 스키마:
```json
{
  "decision_required": [
    {
      "type": "terminology_mismatch",
      "summary": "FE userType vs BE subType",
      "tokens": ["userType", "subType"],
      "areas": ["FE", "BE"],
      "source_refs": ["src/fe/types.ts:12", "src/be/models/user.py:45"],
      "suggested_resolution": "하나로 통일 (도메인 결정 필요)"
    }
  ]
}
```

§7.5 에스컬레이션 원칙 (`[MUST]` 선언):
- `[MUST]` "결정성 이슈(`type: "terminology_mismatch"` 등)는 **agentic 모드에서도 사용자 에스컬레이션 필수**이며, PM이 자율 결정하지 않는다." (→ D-7 §6 "판단 모호 시 에스컬레이션 기본" 원칙 정합).

**변경이력 v2.0 행 추가** (R-5):

```
| v2.0 | 2026-04-24 | §0 근거 제시 원칙 [MUST] 신설, §1.5 개발/비개발 트랙 매트릭스 신설, §2.5 [MUST] 토큰 대상 6종 + Good/Bad 예시 신설, §7 영역 간 용어 일관성 검토 + decision_required 계약 신설 (130) |
```

#### C-2. opal-harness.md §2 "Citation Rules 적용 의무" 블록 신설 (R-6)

> 위치: §2 "모듈 구조" 서브섹션 "QA 산출물 표준 및 검증"(`opal-harness.md:98-106`)과 **대칭**되는 형식으로 그 아래에 배치.

블록 템플릿 (제안):
```markdown
### Citation Rules 적용 의무

> **[MUST]** 모든 pilot(오케스트레이터) / PLAN·TASK·ANALYSIS 스킬 / QA 스킬은 각자 다루는 산출물의 작성·검증 시 `opal/core/references/harness/citation-rules.md`를 필수 Read하고 그 규칙을 준수한다.
>
> 적용 범위: 근거 제시 원칙(§0) / 트랙별 근거 매트릭스(§1.5) / [MUST] 토큰 대상(§2.5) / 영역 간 용어 일관성 + decision_required 계약(§7)
> 적용 모드: interactive · agentic 양쪽 모두
```

- citation-rules.md 경로 정확 기재 (제약 §8: interactive/agentic 양쪽 적용 명시).
- 기존 Lazy 로드 모듈 테이블 `citation-rules` 행(`opal-harness.md:92`)은 유지 (제약 §8 충돌 금지).
- 변경이력에 `v4.5 | 2026-04-24 | §2 Citation Rules 적용 의무 블록 추가 — 모든 pilot/스킬/가이드/QA 대상 인용 규칙 필수 적용 선언 (130)` 행 추가.

#### C-3. R-7 트리거 주입 공통 템플릿

> **SSOT + Trigger 원칙** 엄수 — 1줄 참조만, 규칙 내용 복제 금지 (제약 §8 R-7).

주입 템플릿:
```
> **[MUST]** 산출물 작성·검증 시 `opal/core/references/harness/citation-rules.md`를 Read하여 규칙(근거 제시 원칙 / 트랙별 매트릭스 / [MUST] 토큰 / 영역 간 용어 일관성 / decision_required 계약)을 준수한다.
```

위치 규칙 (카테고리별):
- **pilot SKILL.md (F-1~F-8)**: `## Harness` 섹션 내, 기존 `[MUST] 서브 하네스 Read` 블록 **직후**, 다음 `---` **앞**
- **PLAN/TASK/ANALYSIS 스킬 (F-9, F-11, F-12, F-13, F-14, F-15)**: `## 실행 컨텍스트` 섹션 끝 또는 `## 프로세스` Step 1 앞
- **가이드 (F-10, F-17)**: 서두 제목 바로 아래, `## 0단계` 또는 `## 목적` 앞
- **QA 스킬 (F-16, F-18)**: `## 실행 컨텍스트` 섹션 내 또는 `## 프로세스` Step 1 앞

변경이력 행 추가 템플릿:
```
| v{X.Y+1} | 2026-04-24 | citation-rules 트리거 1줄 주입 — SSOT + Trigger 패턴 (130) |
```

#### C-4. 변경이력 일괄 갱신 원칙 (R-8)

- citation-rules.md(v2.0) + opal-harness.md(v4.5) + R-7 18개 파일: **모두 2026-04-24, 태스크 130 참조 행** 갱신.
- 각 파일의 기존 변경이력 테이블 컬럼 스키마 준수 (버전/날짜/내용).
- 버전 번호는 기존 파일의 마지막 버전에서 마이너 증가 (예: v2.3 → v2.4).

---

## 3. 실행 체크리스트

> 총 **20개 Step** | Phase **4개** | 실행 모드: **복잡** (파일 수 다수 + 병렬 그룹 디스패치)
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1 | 1 | 순차 | SSOT 본체 선행 완성 (G1) |
> | 2 | 2 | 순차 | opal-harness.md (G2, Step 1 의존) |
> | 3 | 3~10 | 병렬 | pilot SKILL.md 8개 (G3a, Step 1 의존) |
> | 3 | 11~17 | 병렬 | PLAN 스킬 5개 + PLAN 가이드 1개 + TASK 스킬 1개 + ANALYSIS 스킬 1개 = 7개 (G3b, Step 1 의존) |
> | 3 | 18~20 | 병렬 | QA 스킬 2개 + QA 가이드 1개 = 3개 (G3c, Step 1 의존) |
> | 4 | (Step별 내부 포함) | — | 변경이력 갱신은 각 Step 범위에 포함 (G4 통합) |
>
> 각 Step의 `영역` = **문서** (프레임워크 문서 작업 — 6영역 FE/BE/DB/환경/배치/공통 분류 미적용).

### Step 1: citation-rules.md R-1~R-5 SSOT 완성

- [x] 완료
- **파일**: `opal/core/references/harness/citation-rules.md`
- **영역**: 문서
- **작업 내용**:
  1. §0 "근거 제시 원칙 [MUST]" 신설 — 현 §1 앞에 삽입 (R-1)
  2. §1.5 "개발/비개발 트랙별 근거 매트릭스" 신설 — 현 §1과 §2 사이 (R-2)
  3. §2.5 "[MUST] 토큰 대상" 신설 — 현 §2.4 아래, 6종 토큰 + Good/Bad 예시 (R-3)
  4. §7 "영역 간 용어 일관성 검토 + decision_required 계약" 신설 — 기존 §6 뒤, 서브섹션 §7.1~§7.5 (R-4)
  5. 변경이력 v2.0 2026-04-24 태스크 130 행 추가 (R-5)
- **완료 기준**:
  - §0/§1.5/§2.5/§7 모두 존재
  - 기존 §1~§6 섹션 번호 및 내용 보존 (하위호환)
  - §7에 decision_required JSON 스키마 + 에스컬레이션 [MUST] 원칙 모두 포함
  - §2.5에 토큰 6종 각각 Good/Bad 예시 1쌍씩 존재
  - 변경이력 최하단에 v2.0 2026-04-24 130 행 존재
- **테스트**: Grep으로 `\[MUST\] 근거 제시`, `트랙별.*매트릭스`, `decision_required`, `terminology_mismatch`, `v2.0.*2026-04-24.*130` 모두 매치
- **의존**: 없음

### Step 2: opal-harness.md §2 R-6 적용 의무 블록 추가

- [x] 완료
- **파일**: `opal/core/references/opal-harness.md`
- **영역**: 문서
- **작업 내용**:
  1. §2 "모듈 구조" 아래, "QA 산출물 표준 및 검증" 소섹션과 대칭되는 위치에 "Citation Rules 적용 의무" 블록 추가 (R-6)
  2. 블록 내용: [MUST] 선언 + citation-rules.md 경로 + 적용 범위(§0/§1.5/§2.5/§7) + interactive/agentic 양쪽 적용 명시
  3. 변경이력에 v4.5 2026-04-24 태스크 130 행 추가 (R-8)
- **완료 기준**:
  - §2 내 "Citation Rules 적용 의무" 블록 존재
  - citation-rules.md 경로 정확 기재
  - interactive/agentic 양쪽 언급
  - Lazy 로드 모듈 테이블 `citation-rules` 행 유지 (충돌 없음)
  - 변경이력 v4.5 행 존재
- **테스트**: Grep `Citation Rules 적용 의무`, `interactive.*agentic|양쪽`, `v4\.5.*2026-04-24.*130` 모두 매치
- **의존**: Step 1 (citation-rules §번호가 옳은지 확인하여 블록에 기재)

### Step 3: opal-pilot-project/SKILL.md 트리거 주입

- [x] 완료
- **파일**: `opal/skills/opal-pilot-project/SKILL.md`
- **영역**: 문서
- **작업 내용**: `## Harness` 섹션 내 `[MUST] 서브 하네스 Read` 블록 직후에 트리거 1줄 추가 + 변경이력 행 추가 (R-7, R-8)
- **완료 기준**: 트리거 1줄 존재, 경로 정확, 변경이력 2026-04-24 130 행 존재
- **테스트**: Grep `citation-rules.md.*준수` + 변경이력 `130`
- **의존**: Step 1

### Step 4: opal-pilot-project-dev/SKILL.md 트리거 주입

- [x] 완료
- **파일**: `opal/skills/opal-pilot-project-dev/SKILL.md`
- **영역**: 문서
- **작업 내용**: `## Harness` 섹션 내 `[MUST] 서브 하네스 Read` 블록 직후 트리거 1줄 + 변경이력 (R-7, R-8)
- **완료 기준**: Step 3과 동일 패턴
- **테스트**: Grep 검증
- **의존**: Step 1

### Step 5: opal-pilot-dev/SKILL.md 트리거 주입

- [x] 완료
- **파일**: `opal/skills/opal-pilot-dev/SKILL.md`
- **영역**: 문서
- **작업 내용**: `## Harness` 섹션 내 `[MUST] 서브 하네스 Read` 직후 트리거 1줄 + 변경이력 (R-7, R-8)
- **완료 기준**: Step 3과 동일 패턴
- **테스트**: Grep 검증
- **의존**: Step 1

### Step 6: opal-pilot-dev-short/SKILL.md 트리거 주입

- [x] 완료
- **파일**: `opal/skills/opal-pilot-dev-short/SKILL.md`
- **영역**: 문서
- **작업 내용**: `## Harness` 섹션 내 `[MUST] 서브 하네스 Read` 직후 트리거 1줄 + 변경이력 (R-7, R-8)
- **완료 기준**: Step 3과 동일 패턴
- **테스트**: Grep 검증
- **의존**: Step 1

### Step 7: opal-pilot-dev-wireframe/SKILL.md 트리거 주입

- [x] 완료
- **파일**: `opal/skills/opal-pilot-dev-wireframe/SKILL.md`
- **영역**: 문서
- **작업 내용**: `## Harness` 섹션 내 `[MUST] 서브 하네스 Read` 직후 트리거 1줄 + 변경이력 (R-7, R-8)
- **완료 기준**: Step 3과 동일 패턴
- **테스트**: Grep 검증
- **의존**: Step 1

### Step 8: opal-pilot-sdd/SKILL.md 트리거 주입

- [x] 완료
- **파일**: `opal/skills/opal-pilot-sdd/SKILL.md`
- **영역**: 문서
- **작업 내용**: `## Harness` 섹션 내 `[MUST] 서브 하네스 Read` 직후 트리거 1줄 + 변경이력 (R-7, R-8)
- **완료 기준**: Step 3과 동일 패턴
- **테스트**: Grep 검증
- **의존**: Step 1

### Step 9: opal-pilot-write-tech/SKILL.md 트리거 주입

- [x] 완료
- **파일**: `opal/skills/opal-pilot-write-tech/SKILL.md`
- **영역**: 문서
- **작업 내용**: `## Harness` 섹션 내 `[MUST] 서브 하네스 Read` 직후 트리거 1줄 + 변경이력 (R-7, R-8)
- **완료 기준**: Step 3과 동일 패턴
- **테스트**: Grep 검증
- **의존**: Step 1

### Step 10: opal-pilot-gc/SKILL.md 트리거 주입

- [x] 완료
- **파일**: `opal/skills/opal-pilot-gc/SKILL.md`
- **영역**: 문서
- **작업 내용**: `## Harness` 섹션 내 `[MUST] 서브 하네스 Read` 직후 트리거 1줄 + 변경이력 (R-7, R-8)
- **완료 기준**: Step 3과 동일 패턴
- **테스트**: Grep 검증
- **의존**: Step 1

### Step 11: op-dev-plan/SKILL.md 트리거 주입

- [x] 완료
- **파일**: `opal/skills/op-dev-plan/SKILL.md`
- **영역**: 문서
- **작업 내용**: `## 실행 컨텍스트` 섹션 끝에 트리거 1줄 + 변경이력 (R-7, R-8). 기존 §3.N.2 인라인 참조는 유지.
- **완료 기준**: 트리거 존재, 변경이력 v2.4 2026-04-24 130 행
- **테스트**: Grep 검증
- **의존**: Step 1

### Step 12: op-dev-plan/references/plan-guide.md 트리거 주입

- [x] 완료
- **파일**: `opal/skills/op-dev-plan/references/plan-guide.md`
- **영역**: 문서
- **작업 내용**: 서두(제목 아래, `## 0단계` 앞)에 트리거 1줄 + 변경이력 행(없으면 신설) (R-7, R-8)
- **완료 기준**: 트리거 존재, 가이드 변경이력 행 추가
- **테스트**: Grep 검증
- **의존**: Step 1

### Step 13: op-task-plan/SKILL.md 트리거 주입

- [x] 완료
- **파일**: `opal/skills/op-task-plan/SKILL.md`
- **영역**: 문서
- **작업 내용**: `## 실행 컨텍스트` 섹션 끝에 트리거 1줄 + 변경이력 (R-7, R-8)
- **완료 기준**: Step 11과 동일 패턴
- **테스트**: Grep 검증
- **의존**: Step 1

### Step 14: op-sdd-plan/SKILL.md 트리거 주입

- [x] 완료
- **파일**: `opal/skills/op-sdd-plan/SKILL.md`
- **영역**: 문서
- **작업 내용**: `## 실행 컨텍스트` 섹션 끝에 트리거 1줄 + 변경이력 (R-7, R-8)
- **완료 기준**: Step 11과 동일 패턴
- **테스트**: Grep 검증
- **의존**: Step 1

### Step 15: op-sdd-action-plan/SKILL.md 트리거 주입

- [x] 완료
- **파일**: `opal/skills/op-sdd-action-plan/SKILL.md`
- **영역**: 문서
- **작업 내용**: `## 실행 컨텍스트` 섹션 끝에 트리거 1줄 + 변경이력 (R-7, R-8)
- **완료 기준**: Step 11과 동일 패턴
- **테스트**: Grep 검증
- **의존**: Step 1

### Step 16: op-task/SKILL.md 트리거 주입

- [x] 완료
- **파일**: `opal/skills/op-task/SKILL.md`
- **영역**: 문서
- **작업 내용**: `## 실행 컨텍스트` 섹션 끝 또는 `## 프로세스` Step 1 앞에 트리거 1줄 + 변경이력 (R-7, R-8)
- **완료 기준**: 트리거 존재, 변경이력 130 행
- **테스트**: Grep 검증
- **의존**: Step 1

### Step 17: op-dev-analysis/SKILL.md 트리거 주입

- [x] 완료
- **파일**: `opal/skills/op-dev-analysis/SKILL.md`
- **영역**: 문서
- **작업 내용**: `## 실행 컨텍스트` 섹션 끝 또는 `## 프로세스` Step 1 앞에 트리거 1줄 + 변경이력 (R-7, R-8)
- **완료 기준**: Step 16과 동일 패턴
- **테스트**: Grep 검증
- **의존**: Step 1

### Step 18: op-dev-qa/SKILL.md 트리거 주입

- [x] 완료
- **파일**: `opal/skills/op-dev-qa/SKILL.md`
- **영역**: 문서
- **작업 내용**: `## 실행 컨텍스트` 섹션 끝 또는 `## 프로세스` Step 1 앞에 트리거 1줄 + 변경이력 (R-7, R-8)
- **완료 기준**: 트리거 존재, 변경이력 130 행
- **테스트**: Grep 검증
- **의존**: Step 1

### Step 19: op-dev-qa/references/qa-dev-guide.md 트리거 주입

- [x] 완료
- **파일**: `opal/skills/op-dev-qa/references/qa-dev-guide.md`
- **영역**: 문서
- **작업 내용**: 서두(`## 목적` 앞)에 트리거 1줄 + 변경이력 행(없으면 신설) (R-7, R-8)
- **완료 기준**: 트리거 존재, 가이드 변경이력 행 추가
- **테스트**: Grep 검증
- **의존**: Step 1

### Step 20: op-task-qa/SKILL.md 트리거 주입

- [x] 완료
- **파일**: `opal/skills/op-task-qa/SKILL.md`
- **영역**: 문서
- **작업 내용**: `## 실행 컨텍스트` 섹션 끝 또는 `## 프로세스` Step 3 "품질 검증" 앞에 트리거 1줄 + 변경이력 (R-7, R-8)
- **완료 기준**: 트리거 존재, 변경이력 130 행
- **테스트**: Grep 검증
- **의존**: Step 1

---

## 4. QA 체크리스트

### 기능 테스트

- [ ] R-1: citation-rules.md §0 근거 제시 원칙이 `[MUST]` 포맷으로 선언되어 있는가
- [ ] R-2: citation-rules.md §1.5에 개발/비개발 트랙 매트릭스(행 2 × 열 5)가 존재하고 셀 값이 필수/선택/불필요로 기재되어 있는가
- [ ] R-3: citation-rules.md §2.5에 토큰 6종(필드명/함수 시그니처/타입명/ERD 컬럼명/IA 화면 ID·라우트/정책 조항 번호)이 모두 나열되고, 각 유형별 Good/Bad 예시 1쌍이 있는가
- [ ] R-4: citation-rules.md §7에 (a) 검출 대상 영역 쌍 (b) 산출물 §리스크 기재 포맷 (c) `decision_required` JSON 스키마 (d) 에스컬레이션 `[MUST]` 원칙이 모두 존재하는가
- [ ] R-5: citation-rules.md 변경이력에 v2.0 2026-04-24 태스크 130 행이 있는가
- [ ] R-6: opal-harness.md §2에 "Citation Rules 적용 의무" 블록이 존재하고 interactive/agentic 양쪽 적용을 명시하는가
- [ ] R-7: 18개 대상 파일 모두에 트리거 1줄이 주입되어 있고, 누락 0건인가
- [ ] R-8: 20개 수정 파일 모두의 변경이력에 2026-04-24 태스크 130 행이 존재하는가

### 일관성 테스트

- [ ] citation-rules.md 기존 §1~§6 섹션 번호·내용이 **보존**되어 있는가 (제약 §8 하위호환)
- [ ] opal-harness.md §2 Lazy 로드 모듈 테이블의 `citation-rules` 행이 유지되어 있는가 (제약 §8 충돌 금지)
- [ ] 18개 트리거 주입 파일의 트리거 블록에 **규칙 내용이 복제되어 있지 않은가** (제약 §8 SSOT 원칙)
- [ ] 모든 트리거 1줄이 **동일 템플릿** (`opal/core/references/harness/citation-rules.md` 경로 포함)을 사용하는가
- [ ] §7 `decision_required` 스키마가 TASK.md §7 R-4의 페이로드 예시 필드(`type`/`summary`/`tokens`/`areas`)를 모두 포함하는가
- [ ] §7 에스컬레이션 [MUST] 원칙이 `~/.opal/references/opal-harness-agentic.md` §6 "판단 모호 시 에스컬레이션 기본" 원칙과 정합하는가
- [ ] op-dev-plan SKILL.md / plan-guide.md의 기존 citation-rules 인라인 참조(§3.1, §2.4 등)가 보존되어 있는가

### 문서 품질

- [ ] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가
- [ ] kebab-case 파일/폴더 네이밍을 따르는가
- [ ] `[MUST]` 토큰 포맷이 `opal-pm.md` §3 Step 3 포맷과 통일되어 있는가 (→ D-1 §4 PM 주입 정합성)
- [ ] 모든 인라인 인용이 `(→ D-N §N)` 또는 `` `경로:줄번호` `` 또는 `[사이트명](URL)` 포맷을 따르는가
- [ ] 트리거 주입 위치가 각 파일의 `## Harness` / `## 실행 컨텍스트` / 가이드 서두 중 가장 자연스러운 위치인가

---

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| citation-rules.md 신설 §번호(§0/§1.5/§2.5/§7)가 기존 참조 링크(op-dev-plan SKILL.md §229, plan-guide.md §229 등)와 충돌 | 기존 인라인 참조가 깨질 수 있음 | 기존 §1~§6 번호는 **절대 보존**. 신설은 §0(서두), §1.5(하위), §2.5(하위), §7(말미)로만 배치하여 기존 §번호 불변 보장. |
| R-7 트리거 블록 내 규칙 내용 복제 실수 (SSOT 위반) | 유지보수 시 중복 문서 갱신 부담 | Step 3~20 모두 **단일 공통 템플릿** 사용 강제. QA §일관성 테스트 항목에 "복제 없음" 검증 추가. |
| opal-harness.md §2 Lazy 모듈 테이블 vs 신설 "적용 의무 블록" 중복 감각 | 독자가 둘 중 어느 것이 진실인지 혼동 | 적용 의무 블록은 **pilot 적용 의무 선언**에 집중(정책), Lazy 테이블은 **로드 시점**만 지시(기술). 역할 분리 명시. |
| 존재 여부 "확인 필요"였던 3개 파일(op-task/op-dev-analysis/op-task-qa) 실제 구조가 예상과 다를 가능성 | 트리거 주입 위치 재판단 필요 | Glob으로 확인 완료(§1 수정 대상 확정 결과 표) — 모두 `## 실행 컨텍스트` 섹션 존재 확인. EXECUTE 단계 워커가 서두 구조 변동 발견 시 PM에 즉시 보고. |
| `decision_required` 계약이 각 pilot Gate 처리 로직에 반영되지 않음 | agentic 모드에서 실효성 없는 스키마로 남을 수 있음 | 본 태스크는 스키마 + 에스컬레이션 원칙까지만 정의(제약 §8 Guards 7). 각 pilot Gate 처리는 별도 후속 태스크에서 다룸. TASK.md §8에 이 경계 명시됨. |
| pilot SKILL.md 8개 동일 위치 주입 시 파일별 `## Harness` 섹션 구조 미세 차이 | 주입 후 포맷 불일치 | §1 F-1~F-8 근거 줄번호 사전 조사 완료. EXECUTE 워커는 각 파일 Read 후 정확한 위치 확인 후 삽입. |
| 변경이력 v 버전 증분 계산 오류 (기존 버전과 중복) | 버전 관리 혼란 | 각 파일의 최신 v 버전을 EXECUTE 워커가 Read로 확인 후 마이너/메이저 증분 판단 (Step 1은 v1.0→v2.0, Step 2는 v4.4→v4.5 등 명시). |
