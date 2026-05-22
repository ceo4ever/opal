# QA: PLAN — cmux-tool 범용 확장 + wtm-agent fallback 체인 재배선

> 검토일: 2026-05-20 | 판정: pass_with_recommendations

## 1. 요약

PLAN.md는 TASK.md의 R-1~R-7 요구사항 7건과 F-1~F-7 확정 사항 7건을 모두 §3 실행 체크리스트 10 Step으로 체계적으로 분해했으며, M-1~M-7 미확정 사항 7건을 §0 결정 요약과 §2.1~§2.9 핵심 설계에서 근거 포함 결정했다. Citation Rules를 준수하여 참조 문서 테이블(D-1~D-20)과 [MUST] 원문 인용을 포함했고, docs/CONVENTIONS.md의 언어/네이밍/변경이력/배포 경계 규칙을 모두 명시했다. 다만 영역 간 용어 일관성(tools.md ↔ AGENT.md ↔ README.md)이 EXECUTE에서 최종 결정되어야 함을 표기했으므로 주의 요청.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| GP-1 | 즉시 실행 가능성 | Pass | 10 Step + 4 Phase + 각 Step 완료 기준 명시. EXECUTE 진입 충분. |
| GP-2 | 의존성 순서 | Pass | §3 구현 순서(1→10) + Phase 그룹핑(순차/병렬) 명시. Step 간 파일 의존성도 기재. |
| GP-3 | TASK 반영 | Pass | R-1~R-7 모두 Step으로 분해(§3), F-1~F-7 모두 §2에 반영(§2.1~§2.9), M-1~M-7 모두 §0에서 결정 + 근거. |
| GP-4 | 파일 목록 완전성 | Pass | 신규 8파일(N-1~N-8) + 수정 6파일(M-1~M-6) + 삭제 12파일(D-1~D-12) 모두 명시. 재배치 구조(lib/examples/docs/)도 §2.6 다이어그램으로 명확화. |
| GP-5 | 설계 구체성 | Pass | §2.1~§2.9에서 디스패처 라우팅 로직(§2.2) / JSON 스키마(§2.3) / 트리거 조건 매트릭스(§2.4) / fallback 코드(§2.5) / 디렉토리 구조(§2.6) / 자산 처분표(§2.7) / 2단 체인 구조(§2.8) / install 처리(§2.9) 모두 구체 기재. |
| GP-6 | 체크리스트 커버리지 | Pass | §4에 기능 테스트(R-1~R-7 + 안전 가드) + 일관성 테스트(호칭/에러코드/JSON 스키마/흡수 출처/CONVENTIONS) + 문서 품질(한국어/kebab-case/frontmatter/인용규칙/단순성/외과성) 분류 완성. |
| CT-1 | 참조 문서 테이블 | Pass | §1에 D-1~D-20 (20행 × 3컬럼: 유형/경로/참조이유) 완성. TASK D-1~D-11, D-7a~D-7e 모두 포함되거나 참조 선언. |
| CT-2 | [MUST] 원문 인용 | Pass | §기초 끝에 4개 [MUST] 인용(CONVENTIONS §언어규칙, §구현규칙 Guards/도구우선/변경이력/배포경계/플랫폼분기, cmux-tool README §안전가드, coding-principles §2 단순성 우선, §4 외과성). |
| CT-3 | 인라인 인용 | Pass | §2 핵심 설계 각 절(§2.1~§2.9)에서 → D-N 형태 인용 또는 경로:줄번호 인용. 예: §2.1 "(→ D-1, → D-5)" 등. |
| CC-1 | 언어 규칙 | Pass | 문서 본문 한국어 + 기술 용어 영어 병기. 코드/필드명 English (extract/snapshot 등). |
| CC-2 | 네이밍 규칙 | Pass | 파일 kebab-case: cmux-helpers.sh, e2e-form-fill.sh, branch.sh, dispatch.sh, json.sh, CMUX-REFERENCE.md. 폴더 lib/, examples/, docs/. |
| CC-3 | 구현 규칙 Guards | Pass | PLAN에 EXECUTE 사전 코드 작성·파일 수정 없음. 구체 구현은 EXECUTE Step에서 수행. |
| CC-4 | 구현 규칙 디스패치 의무 | Pass | 각 Step의 "파일" + "작업 내용"에서 워커 실행 대상 명시. EXECUTE 단계에서 Step별 워커 호출 가능. |
| CC-5 | 구현 규칙 도구 우선 | Pass | 기존 run.sh L178-207 JSON 직렬화 패턴 재사용(N-4 json.sh) / 기존 _lib.sh 헬퍼 흡수(N-2 cmux-helpers.sh) / test-browser.sh 분기 로직 일반화(N-3 branch.sh). |
| CC-6 | 구현 규칙 변경이력 | Pass | Step 5, 6, 7, 8, 9에서 "변경이력 v*.* (006) 행 추가" 명시. 파일별 갱신 대상 기재(M-1~M-6 수정 파일). |
| CC-7 | 구현 규칙 배포 경계 | Pass | 프로젝트 소스(opal/, skills/, agents/, scripts/) 수정만 기재. ~/.opal/ 직접 편집 없음. install-mac.sh 재배포로 검증. |
| CC-8 | 구현 규칙 플랫폼 분기 | Pass | PLAN §2 본문에 Claude/Cursor/Gemini 조건문 없음. 플랫폼 분기 필요 시 어댑터 계층(install-mac.sh)으로 위임. |
| SP-1 | M-1 WebFetch 처리 결정 | Pass | §0 M-1: "(a) WebFetch 완전 제거 — 2단(cmux → playwright) 체인으로 축소" 명시. 근거: D-18 (coding-principles §2 단순성 우선) + 의사결정 복잡성 설명. |
| SP-2 | M-2 서브명령 노출 범위 | Pass | §0, §2.1: "7종 필수(extract/snapshot/eval/wait/navigate/click/fill) + 5종 선택(open/open-split/reload/press/get) + extract 레거시(1종) = 총 13종" 명시. A/B/C 분기는 `eval`+`wait` 조합 + lib/branch.sh 헬퍼로만 다룸. |
| SP-3 | M-3 JSON 스키마 통일 | Pass | §2.3: "공통 5필드(ok/command/surface/user_owned/error) + 명령별 특화 필드" 정의. extract는 기존 8필드 보존(R-2 호환). |
| SP-4 | M-4 트리거 조건 표 | Pass | §2.4: 5행 매트릭스(웹 크롤링/정보 수집/웹 테스트/E2E/로컬 SPA) × 대표 문장 × 우선 명령 정의. |
| SP-5 | M-5 fallback 에러 코드 | Pass | §2.5: "4종 자동 폴백(not_in_cmux/cmux_not_installed/surface_parse_failed/open_failed) + 5종 입력 정정(usage/invalid_surface/goto_failed/wait_failed/eval_failed)" 명시. wtm-agent 폴백 로직 pseudocode 포함. |
| SP-6 | M-6 재배치 구조 | Pass | §2.6: lib/(4파일) / examples/(3파일) / docs/(1파일) 구조 다이어그램 + 신규 파일 3행×3컬럼 기재. install_dir 재귀 복사 호환성 확인. |
| SP-7 | M-7 자산 처분표 | Pass | §2.7: "흡수 7건(lib/examples/docs 배치) / 폐기 4건(MAMS 전용) / 후속 보류 없음" 1:1 매핑 표. Step 10에서 cmux/ 폴더 자체 제거. |
| RK-1 | 호환성 리스크 | Pass | §5 R-T1~R-T3: cmux 버전 호환성 / 도구 미설치 환경 / fallback 라벨 치환 모두 대응 방안 명시. |
| RK-2 | 안전 가드 리스크 | Pass | §5 R-T4: A/B/C 분기 미노출 / examples/e2e-branch-auto.sh 제공으로 보완. §4 QA에서 "B/C cleanup 금지" 정적 검증 기재. |
| RK-3 | 출처 추적 리스크 | Pass | §5 R-T5: cmux/ 폴더 제거 후 git 히스토리로 추적 + 신규 파일 헤더 주석 + README 출처 표 두 채널 보존. |
| RK-4 | 단순성 vs 노출 범위 | Pass | §5 R-T6: 12종 노출은 cmux 18종 중 67% (자동화 핵심만) + TASK R-1 AC 충족. 불필요 노출 제외(type/select/hover/focus/back/forward/url). |
| RK-5 | 용어 일관성 | Warning | §5 R-T7: "decision_required 발생 시 캡틴 에스컬레이션" 표기. 3개 문서(tools.md/AGENT.md/README.md)의 용어(웹크롤링↔extract, 네비↔navigate 등) 통일이 EXECUTE에서 최종 결정 필요. |

## 3. 지적 사항

### 경미한 권고 사항 (Warning)

1. **영역 간 용어 일관성 (R-T7)**
   - 위치: PLAN §5 R-T7
   - 내용: tools.md의 "웹 크롤링" ↔ AGENT.md의 Phase 호칭 ↔ README.md의 서브명령 분류명이 일관되어야 함
   - 평가: PLAN에서 주의를 기울였으므로 warning 수준. EXECUTE 단계에서 3개 문서 간 용어 매핑 표를 작성하고 "decision_required" 발생 시 캡틴 에스컬레이션 권고
   - 심각도: Info (진행에 영향 없음)

2. **M-1 근거의 설득력**
   - 위치: PLAN §2.8, §0 M-1
   - 내용: WebFetch 제거 근거 — "의사결정 표가 3분기로 늘어남"이 추상적
   - 평가: D-18(coding-principles §2)로 근거 인용은 충분하나, "3분기"의 구체적 의사결정 매트릭스 예시가 있으면 더 명확했을 것으로 예상. PLAN 수준에서 과도할 수 있으므로 warning.
   - 심각도: Info (설계 결정은 충분히 근거 있음)

3. **Step 간 의존성 표현의 명확성**
   - 위치: PLAN §3 구현 순서
   - 내용: Step 1~10이 순차 나열로만 표현. Phase 그룹핑(§3 표)은 명시되었으나 개별 Step의 파일 의존성은 각 Step 설명 "의존" 줄에 분산
   - 평가: Phase 그룹핑은 명시되었고 각 Step의 의존성도 있으나, 전체 DAG를 한눈에 파악하기 어려울 수 있음. 단순성 우선 원칙상 현재 수준도 충분.
   - 심각도: Info (실행 순서는 이해 가능)

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md | R-1~R-7 + F-1~F-7 + M-1~M-7 모두 PLAN에서 다루어짐 | Pass |
| docs/CONVENTIONS.md | 언어/네이밍/변경이력/배포경계/플랫폼분기 규칙 준수 | Pass |
| opal/core/references/harness/citation-rules.md | 참조 테이블 + [MUST] 인용 + 인라인 인용 | Pass |
| opal/core/references/harness/coding-principles.md | 단순성 우선(M-1 근거) + 외과적 변경(EXECUTE 범위 명시) | Pass |

## 5. 판정

**pass_with_recommendations**

모든 핵심 요구사항(R-1~R-7, F-1~F-7, M-1~M-7, Citation Rules, CONVENTIONS)을 충족했으며, 10 Step + 4 Phase의 명확한 실행 계획과 QA 체크리스트를 포함했다. 경미한 권고 사항 3건(용어 일관성, 근거 설득력, 의존성 표현)은 모두 Info 수준이며 EXECUTE 진행을 막지 않는다. 다음 단계(EXECUTE) 진입 가능.

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-05-20 16:30 | 초기 작성 — 28개 검증 항목 + Warning 3건 + pass_with_recommendations 판정 (QA-PLAN) |
