# QA: EXECUTE — Citation Rules 하네스 보편화 — SSOT 완성 + Trigger 주입

> 검토일: 2026-04-24 | 판정: **Pass**

---

## 1. 요약

20개 파일 전체(citation-rules.md SSOT 본체 1개 + opal-harness.md 1개 + 트리거 주입 18개)가 PLAN.md 명세에 따라 정확히 편집되었다.
citation-rules.md에 §0 근거 제시 원칙, §1.5 트랙 매트릭스, §2.5 [MUST] 토큰 6종 Good/Bad 예시, §7 영역 간 용어 일관성 + decision_required 계약 + 에스컬레이션 [MUST] 원칙이 모두 신설되었으며 기존 §1~§6 구조는 완전히 보존되었다.
opal-harness.md §2에 "Citation Rules 적용 의무" 블록이 정확한 경로와 interactive/agentic 양쪽 적용 명시와 함께 추가되었고, Lazy 모듈 테이블의 `citation-rules` 행과 충돌 없이 공존한다.
18개 트리거 주입 파일 전수에서 PLAN.md §2 C-3의 공통 템플릿과 동일한 트리거 1줄이 확인되었고, 모든 파일 변경이력에 `2026-04-24 ... (130)` 행이 기재되었다.
git status 기준 수정 파일이 `opal/` 소스 경로 20개로 한정되어 `~/.opal/` 직접 수정 Guard가 준수되었다.

---

## 2. 검증 결과

### E1 — citation-rules.md 본체 (R-1~R-5)

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| E1-1 | §0 "근거 제시 원칙" 섹션이 §1 앞에 존재 | Pass | L9 `## §0. 근거 제시 원칙` — §1(L17) 앞 위치 확인 |
| E1-2 | §0 내 `[MUST]` 포맷 "상상·추정·기억 기반 기재 금지" 원칙 선언 | Pass | L11 `> **[MUST]** 상상·추정·기억 기반 기재 금지 — ...` 확인 |
| E1-3 | §1.5 "개발/비개발 트랙별 근거 매트릭스" 섹션 존재 | Pass | L38 `## §1.5. 개발/비개발 트랙별 근거 매트릭스` 확인 |
| E1-4 | §1.5 매트릭스 2행(비개발/개발) × 5열(문서/웹/기획/설계/소스) 구조 | Pass | L43~L45 테이블 — 행 2개, 열 5개 확인 |
| E1-5 | 개발 트랙: 기획+설계+소스=필수 / 비개발 트랙: 문서+웹=필수 명확 구분 | Pass | 비개발=문서필수/웹필수/기획선택/설계선택/소스선택, 개발=문서필수/웹선택/기획필수/설계필수/소스필수 |
| E1-6 | §2.5 "개발 트랙 [MUST] 토큰 대상" 섹션 존재 | Pass | L133 `### 2.5 개발 트랙 [MUST] 토큰 대상` 확인 |
| E1-7 | §2.5에 6종 토큰 유형 모두 나열 | Pass | (1)필드명 (2)함수 시그니처 (3)타입명 (4)ERD 컬럼명 (5)IA 화면 ID/라우트 (6)정책 조항 번호 — 전부 확인 |
| E1-8 | §2.5 각 토큰 유형별 Good/Bad 예시 1쌍씩 존재 | Pass | 6종 각각 Good/Bad 예시 쌍 확인 |
| E1-9 | §7 "영역 간 용어 일관성 검토 + decision_required 계약" 섹션 존재 (기존 §6 뒤) | Pass | L276 `## 7. 영역 간 용어 일관성 검토 + decision_required 계약` — §6(L251) 뒤 위치 확인 |
| E1-10 | §7.1 검출 대상 영역 쌍 예시 | Pass | FE↔BE / 정책서↔코드 / ERD↔코드 / IA↔FE 라우트 4쌍 나열 확인 |
| E1-11 | §7.3 산출물 §리스크 기재 포맷 예시 | Pass | L293~L297 리스크 테이블 예시 확인 |
| E1-12 | §7.4 `decision_required` JSON 스키마에 `type`/`summary`/`tokens`/`areas` 필드 모두 포함 | Pass | L303~L316 JSON — type/summary/tokens/areas/source_refs/suggested_resolution 모두 포함. 요구 4필드 충족 |
| E1-13 | §7.5 `[MUST]` 에스컬레이션 원칙 선언 | Pass | L320 `> **[MUST]** 결정성 이슈 ... agentic 모드에서도 사용자 에스컬레이션 필수 ...` 확인 |
| E1-14 | 변경이력에 `v2.0 \| 2026-04-24 \| ... (130)` 행 존재 | Pass | L329 확인 |
| E1-15 | 기존 §1~§6 섹션 번호와 내용 보존 (하위호환) | Pass | §1(L17), §2(L51), §3(L169), §4(L220), §5(L234), §6(L251) 모두 존재. 섹션 번호 불변 확인 |

### E2 — opal-harness.md §2 Citation Rules 적용 의무 (R-6)

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| E2-1 | §2 "모듈 구조" 내에 "Citation Rules 적용 의무" 블록 존재 | Pass | L107~L112 `### Citation Rules 적용 의무` 블록 확인 |
| E2-2 | 블록에 `opal/core/references/harness/citation-rules.md` 경로 정확 기재 | Pass | L109 경로 완전 일치 확인 |
| E2-3 | interactive · agentic 양쪽 모두 적용 명시 | Pass | L112 `적용 모드: interactive · agentic 양쪽 모두` 확인 |
| E2-4 | 기존 Lazy 로드 모듈 테이블의 `citation-rules` 행 유지 (충돌 없음) | Pass | L92 `\| 인용 규칙 \| harness/citation-rules.md \| ...` 행 유지 확인 |
| E2-5 | 변경이력에 `v4.5 \| 2026-04-24 \| ... (130)` 행 존재 | Pass | L248 확인 |

### E3 — 18개 파일 트리거 주입 전수 (R-7)

Grep 결과 `citation-rules\.md.*준수` 패턴 매치 파일 수: **18개**

| # | 파일 | 트리거 라인 | 템플릿 일치 | 변경이력 130 |
|---|------|-----------|-----------|------------|
| F-1 | opal-pilot-project/SKILL.md | L20 | Pass | Pass |
| F-2 | opal-pilot-project-dev/SKILL.md | L31 | Pass | Pass |
| F-3 | opal-pilot-dev/SKILL.md | L18 | Pass | Pass |
| F-4 | opal-pilot-dev-short/SKILL.md | L20 | Pass | Pass |
| F-5 | opal-pilot-dev-wireframe/SKILL.md | L19 | Pass | Pass |
| F-6 | opal-pilot-sdd/SKILL.md | L30 | Pass | Pass |
| F-7 | opal-pilot-write-tech/SKILL.md | L22 | Pass | Pass |
| F-8 | opal-pilot-gc/SKILL.md | L21 | Pass | Pass |
| F-9 | op-dev-plan/SKILL.md | L18 | Pass | Pass |
| F-10 | op-dev-plan/references/plan-guide.md | L9 | Pass | Pass |
| F-11 | op-task-plan/SKILL.md | L17 | Pass | Pass |
| F-12 | op-sdd-plan/SKILL.md | L19 | Pass | Pass |
| F-13 | op-sdd-action-plan/SKILL.md | L19 | Pass | Pass |
| F-14 | op-task/SKILL.md | L16 | Pass | Pass |
| F-15 | op-dev-analysis/SKILL.md | L18 | Pass | Pass |
| F-16 | op-dev-qa/SKILL.md | L18 | Pass | Pass |
| F-17 | op-dev-qa/references/qa-dev-guide.md | L6 | Pass | Pass |
| F-18 | op-task-qa/SKILL.md | L19 | Pass | Pass |

공통 템플릿 검증:
> `> **[MUST]** 산출물 작성·검증 시 \`opal/core/references/harness/citation-rules.md\`를 Read하여 규칙(근거 제시 원칙 / 트랙별 매트릭스 / [MUST] 토큰 / 영역 간 용어 일관성 / decision_required 계약)을 준수한다.`

18개 파일 전부 위 템플릿과 완전 일치. 규칙 내용 복제 없음(1줄 단독 트리거) 확인.

### E4 — 일관성

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| E4-1 | 20개 파일 모두 변경이력에 `2026-04-24 ... (130)` 행 존재 | Pass | Grep 매치 파일 수: skills 18개 + core/references 2개 = 20개 |
| E4-2 | PLAN.md §3 실행 체크리스트 Step 1~20 체크박스 `[x]` 갱신 | Pass | 20개 `- [x] 완료` 행 전부 확인 |
| E4-3 | TASK.md §7 R-1~R-8 체크박스 `[x]` 유지 | Pass | R-1~R-8 전부 `[x]` 확인 (PLAN QA 단계에서 갱신됨) |
| E4-4 | op-dev-plan SKILL.md 기존 citation-rules §3.1/§2.4 인라인 참조 보존 | Pass | L344 `citation-rules.md §3.1`, L437 `citation-rules.md §2.4` 두 참조 모두 유지 확인 |
| E4-5 | op-dev-plan/references/plan-guide.md 기존 인라인 참조 보존 | Pass | L136 `citation-rules.md §2.4`, L201 `citation-rules.md §3.1`, L443 `citation-rules.md §2.4` 모두 유지 확인 |

### E5 — Guards 준수

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| E5-1 | `~/.opal/` 경로 직접 수정 없음 — 모든 편집이 `opal/` 소스 경로 | Pass | git status 기준 수정 파일 20개 전부 `opal/` 경로. `.opal/MEMORY.md` diff 노출은 메모리 시스템 자동 갱신이며 EXECUTE 워커 작업 범위 외 |
| E5-2 | citation-rules.md 기존 §1~§6 섹션 삭제·변경 없음 (하위호환) | Pass | §1~§6 번호 및 내용 전부 보존. 신설은 §0/§1.5/§2.5/§7로만 추가 |
| E5-3 | 커밋 수행 없음 (changed_files만 반환) | Pass | 미커밋 상태 확인 |

---

## 3. 지적 사항

지적 사항 없음.

20개 파일 전체 Pass. Critical 0건, Warning 0건, Info 0건.

---

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md R-1~R-8 | citation-rules.md 신설 §0/§1.5/§2.5/§7이 R-1~R-5 AC를 충족하는가 | Pass |
| TASK.md §8 제약 조건 | 기존 §2~§6 구조 보존, SSOT 원칙, 복제 금지, 충돌 금지 모두 준수했는가 | Pass |
| PLAN.md §2 C-3 트리거 템플릿 | 18개 파일 트리거가 C-3 공통 템플릿과 정확히 일치하는가 | Pass |
| PLAN.md §1 F-1~F-18 주입 위치 | 각 파일의 주입 위치(Harness/실행 컨텍스트/가이드 서두)가 근거와 정합하는가 | Pass |
| PLAN.md §3 체크리스트 | Step 1~20 체크박스 모두 `[x]`로 갱신되었는가 | Pass |
| TASK.md §7 R-1~R-8 체크박스 | PLAN QA에서 갱신된 `[x]` 상태 유지되는가 | Pass |
| decision_required 스키마 | TASK.md R-4 요구 필드(type/summary/tokens/areas) 모두 포함하는가 | Pass |

---

## 5. 판정

**Pass**

E1~E5 전 항목 Pass. citation-rules.md SSOT 본체가 요구사항 R-1~R-5를 완전히 충족하며 기존 §1~§6 하위호환이 유지되었다. opal-harness.md §2 Citation Rules 적용 의무 블록(R-6)이 경로/모드 조건을 모두 만족하며, 18개 트리거 주입 파일(R-7)에서 공통 템플릿 1줄이 정확히 확인되었다. 20개 파일 변경이력 일괄 갱신(R-8) 완료. Guards(`~/.opal/` 직접 수정 금지, 커밋 없음) 모두 준수.
