# QA: PLAN — opgc 진단 전담화 + 프로젝트 구성 표준 정립

> 검토일: 2026-04-18 | 판정: Pass

## 1. 요약

PLAN.md는 TASK.md의 D-1~D-11 확정 설계 방향과 F-1~F-11 요구사항 전부를 10개 파일(신규 1 + 수정 9)과 11개 Step(5개 Phase)으로 분해했다. 의존성 순서는 "표준 선행(PROJECT.md, 허브 가이드) → 하위 컴포넌트(체커 AGENT) → 오케스트레이터(opgc SKILL, opi) → 정합화 문서 → 최종 셀프체크"로 올바르게 배치되어 있으며, 각 Step의 작업 내용·완료 기준·테스트·의존 항목이 구체적으로 기술되었다. `[MUST]` 포맷으로 F-1/F-2/F-3/F-4/F-5/F-6/F-7/F-8/F-9/F-10/F-11 AC 원문이 §2 핵심 설계에 인용되어 재해석 여지가 제거되었고, 참조 문서 테이블(D-1~D-16)과 인라인 `(→ D-N)` 포맷은 `opal/core/references/harness/citation-rules.md` §2/§3.1을 준수한다. 하위호환(프로젝트 구성 섹션 부재 시 1+1 fallback)과 단일 태스크 완료 원칙은 §1 영향 범위·§5 리스크에 명시되어 있다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| GP-1 | 즉시 실행 가능성 | Pass | 11개 Step 각각에 파일 경로·작업 내용·완료 기준·grep 검증 예시·의존 Step이 명시되어 EXECUTE 워커가 재해석 없이 바로 착수 가능 |
| GP-2 | 의존성 순서 | Pass | Phase 1(M-4/N-1 독립) → Phase 2(체커 AGENT, M-4 후) → Phase 3(opgc/opi, 체커 후) → Phase 4(정합화) → Phase 5(CONVENTIONS/셀프체크) 병렬 기회 테이블(§3)로 명확. Step 8(opal-pm.md)이 Step 7(context-injection.md)에 의존하는 등 참조 무결성 순서 보장 |
| GP-3 | TASK 반영 | Pass | F-1~F-11 전부가 Step 1~11에 태그되어 매핑 완료(F-1/F-2/F-3/F-4/F-10→Step 5, F-5/F-6→Step 3/4, F-7→Step 1, F-8→Step 6, F-9→Step 7/8, F-11→Step 2). §3·§4 테이블에 F-ID 명시 |
| GP-4 | 파일 목록 완전성 | Pass | §1 관련 파일 테이블에 D-1~D-16 모두 수록. 변경 대상 9개 + 신규 1개 = 10개 파일 명시. D-15/D-16(README, skills.md)는 변경 없음 근거(grep 결과) 기록. opgc 하위 references/templates 비대상도 §1 영향 범위에 "APPLY 제거로 인한 변경 영향 없음" 명시 |
| GP-5 | 설계 구체성 | Pass | §2 설계 1~9에 파일별 섹션/줄번호·변경 전/후·스키마·의사코드 수록. 주요 AC는 `[MUST]` + TASK.md 원문 인용 포맷(예: 설계 1의 F-7 AC 원문, 설계 3의 F-5/F-6 AC 원문, 설계 4의 F-1/F-2/F-3/F-4 AC 원문)으로 재해석 여지 제거 |
| GP-6 | 체크리스트 커버리지 | Pass | §3 실행 체크리스트 Step 1~11은 F-1~F-11 AC를 모두 커버하며, §4 QA 체크리스트는 F-1~F-11 AC 11항목 + 일관성 테스트 7항목 + 문서 품질 6항목 = 총 24항목으로 분해됨. Step 11 최종 셀프체크가 13개 교차 검증으로 누락 방지 |
| CR-1 | TASK D-1~D-11 설계 방향 일치 | Pass | §2 설계 1~9가 D-4/D-11(PROJECT.md·허브가이드)→D-2·D-3·D-5·D-6(체커)→D-1·D-2·D-3·D-4(opgc)→D-6·D-8(opi)→D-7·D-8·D-9·D-10·D-5(정합화) 순으로 D-1~D-11 전부 반영. 임의 재설계 없음 |
| CR-2 | 제약 조건 반영 | Pass | TASK.md §제약(하네스 Guards, `~/.opal/` 직접 수정 금지, 커뮤니티 스킬 원본 수정 금지, 기준 문서 자동 갱신 금지, 단일 태스크 완료, 산출물 인용 규칙)이 §1 영향 범위 "잠재 영향"·§5 리스크·§변경 요약·Step 11 [MUST] 제약 교차 검증에 반영 |
| CR-3 | citation-rules §2/§3.1 준수 | Pass | §1 참조 문서 테이블이 `# / 유형 / 문서/사이트 / 경로/URL / 참조 이유` 5컬럼 공통 스키마(§3.1). 인라인 인용은 `(→ D-N §M)` + `` `경로:줄번호` `` 혼용(§3.2). `[MUST]` 포맷이 §2.4 "[MUST] `경로` §N: <원문>" 준수. 유형 컬럼은 "기획/설계/소스/외부/하네스/참조"(§1 안내 문구)로 확장 적용 |
| CR-4 | 하위호환 명시 | Pass | §1 "하위호환 보장 포인트", §2 설계 3(c) check_enabled 분기, §2 설계 4(d) SCAN fallback, §3 Step 5 완료 기준, §4 일관성 테스트 "opgc SKILL.md STEP 1/2 fallback 명시", §5 리스크 테이블(scope optional)에 반복 명시 |
| CR-5 | 단일 태스크 완료 원칙 | Pass | §5 리스크 "본 태스크는 단일 태스크 완료 원칙" 명시, §변경 요약 "수정 8개 + 신규 1개 = 단일 태스크 범위", Step 1~10 전부 본 태스크 내 완료. 126/127 분리 언급 없음 |

## 3. 지적 사항

### Info

1. **PROJECT.md:70 opgc 설명 문자열 부재 처리** (Info)
   - 현재 `docs/PROJECT.md:70`의 opgc 컴포넌트 설명이 `"GC 5단계 Pilot: SCAN → CHECK → REPORT → APPLY → CLOSE"`로 기술되어 있음. F-2로 APPLY 단계가 제거되면 이 문구는 정합성이 깨진다.
   - PLAN §2 설계 1(M-4)과 §3 Step 1 작업 내용은 "`## 프로젝트 구성` 신설 + '프로젝트 문서' 테이블 컬럼 추가"만 명시하고, 이 줄 수정은 언급 없음.
   - F-7 AC에는 포함되지 않으므로 **FAIL은 아니나**, 일관성 확보를 위해 EXECUTE에서 Step 1 작업 내용에 "주요 컴포넌트(GC) 테이블 opgc 행의 '5단계 … APPLY → CLOSE'를 '4단계 SCAN/CHECK/REPORT/CLOSE'로 갱신" 1개 세부 작업을 추가 권장. 심각도 **Info** — 진행에 영향 없음.

2. **`opi SKILL.md` 변경이력 버전 표기** (Info)
   - §2 설계 5(d)는 `v3.4` 추가. 현 opi SKILL.md의 기존 변경이력 최신 버전이 v3.3인지 실파일 확인이 EXECUTE에서 필요함(PLAN은 v3.3 가정 없이 v3.4 제시). 만약 현 최신이 다른 번호면 EXECUTE에서 적절한 다음 버전으로 재조정. 심각도 **Info**.

### Warning / Critical

- 없음.

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md §확정된 설계 방향(D-1~D-11) | PLAN §2 설계 1~9가 임의 재설계 없이 D-1~D-11 전부 반영 | Pass |
| TASK.md §요구사항 F-1~F-11 AC | PLAN §2 설계의 `[MUST]` 블록 + §3 Step 완료 기준 + §4 QA 체크리스트 AC 원문 인용 | Pass |
| TASK.md §관련 문서 D-1~D-13 | PLAN §1 참조 문서 D-1~D-13 전부 포함 + D-14~D-16(agents.md 내부 링크, README, skills.md) 추가 조사 결과 편입 | Pass |
| TASK.md §제약 조건 | PLAN §1 영향 범위(잠재 영향) + §5 리스크 + Step 11 교차 검증에 하네스 Guards/~/.opal/ 금지/커뮤니티 스킬 원본 금지/자동 갱신 금지/단일 태스크/인용 규칙 전부 반영 | Pass |
| `opal/core/references/harness/citation-rules.md` §2/§3.1 | §1 참조 테이블 5컬럼 스키마·`[MUST]` 포맷·인라인 `(→ D-N)` 전부 준수 | Pass |
| `docs/PROJECT.md` 현재 구조 | §1 현재 상태가 `docs/PROJECT.md:7-72`, `:74-82` 실 내용과 정합(확인 완료) | Pass |
| STATE.md 파이프라인 | Step 6 "QA Gate 🔄" → QA-PLAN.md 생성 흐름 정합 | Pass |

## 5. 판정

**Pass**

모든 검증 항목(GP-1~GP-6, CR-1~CR-5)이 Pass이며 Critical/Warning 지적 사항 없음. Info 2건은 진행에 영향이 없고 EXECUTE에서 보조적으로 반영 가능. TASK.md §요구사항 F-1~F-11 체크박스를 모두 `[x]`로 갱신했다.
