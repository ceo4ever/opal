# QA: PLAN — Gemini Hardening 글로벌 배포

> 검토일: 2026-04-09 | 판정: Pass

## 1. 요약

HARDENING SSOT(프로젝트 루트 `GEMINI.md` 라인 10~182)를 글로벌 `~/.gemini/GEMINI.md`에 독립 마커로 배포하는 계획. 신규 소스 파일 `opal/bootstrapper/gemini-hardening.md` 1개와 `scripts/install-mac.sh` 수정(상수 2개, 신규 함수 `install_gemini_hardening`, 호출 1개, `print_summary` 요약 라인 1개)으로 구성되며 `install_opal_section()`은 비변경으로 하위 호환을 유지한다. 3-Step 실행 체크리스트(소스 생성 → 인스톨러 수정 → dry-run 3케이스 검증)가 명확하다. TASK.md의 함수명 불일치(`print_installed_summary` vs 실제 `print_summary`, `install_opal_bootstrappers` vs 실제 `install_opal`)는 코드 기준으로 해소되었다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| GP-1 | 즉시 실행 가능성 | Pass | 파일 경로, 함수명, 삽입 위치(라인 26/254/457/769), 복사할 원본 라인 범위(11~181)까지 구체적으로 명시됨 |
| GP-2 | 의존성 순서 | Pass | Step 1(소스) → Step 2(인스톨러) → Step 3(검증) 순서 및 Phase 표가 일관됨 |
| GP-3 | TASK 반영 | Pass | TASK 요구사항 3개(신규 소스, 인스톨러 4개 변경, OPAL 섹션 비파괴) 모두 PLAN에 매핑됨. 문서/코드 함수명 불일치는 리스크와 핵심 설계에 명시 처리 |
| GP-4 | 파일 목록 완전성 | Pass | 신규 1 + 수정 1 파일만 요구되며 영향 범위가 명확히 국한됨 |
| GP-5 | 설계 구체성 | Pass | `install_gemini_hardening` 3분기 로직(신규/교체/추가), R2 분기 제외, 마커 독립성, 본문 추출 패턴 재사용이 모두 기술됨 |
| GP-6 | 체크리스트 커버리지 | Pass | 실행 체크리스트 3개 Step + QA 체크리스트 12개 항목이 TASK 요구사항과 SSOT 보장을 모두 커버 |

## 3. 지적 사항

지적 사항 없음.

### Info (참고)
- Step 1 테스트 커맨드의 `sed -n '11,181p' GEMINI.md`에서 라인 181은 공백 라인이다(확인 완료). diff 비교 시 추출 본문의 마지막 공백 처리와 맞춰져야 하는데, ` ```markdown ` 블록에 라인 11~181을 그대로 복사하면 트레일링 공백 라인이 포함되어 일치할 것으로 보인다. EXECUTE 단계에서 최종 확인 권장.
- `install_opal_section()` 복제로 인한 코드 중복은 리스크 섹션에 명시되었고, 후속 리팩토링 태스크 제안이 포함되어 수용 가능.

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md | 요구사항 3개 → PLAN §2 파일 변경 계획에 1:1 매핑 | Pass |
| TASK.md | 제약 "install_opal_section 수정 금지" → PLAN 영향 범위·리스크에 명시 | Pass |
| TASK.md | SSOT(루트 GEMINI.md 동일) → PLAN Step 1 완료 기준 diff 검증 및 리스크 대응에 반영 | Pass |
| TASK.md | 함수명 `print_installed_summary`/`install_opal_bootstrappers` vs 실제 `print_summary`/`install_opal` | Warning→해소 (PLAN §1/§2/§5에서 코드 기준 진행 명시) |
| 프로젝트 루트 GEMINI.md | 마커 라인 10(START)/182(END), 본문 라인 11~181 실측 일치 | Pass |

## 5. 판정

**Pass**
모든 GP-1~GP-6 통과. 실행 단계에서 별도 수정 없이 바로 진입 가능하며, 문서/코드 불일치 2건이 PLAN 단계에서 선제 식별·해결되어 리스크가 낮다.
