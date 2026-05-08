# DONE: PM Gate 컨벤션 자동 진단 — opal-convention-checker 영역별 병렬 디스패치

> 완료일: 2026-05-08 22:07 KST | 적용 스킬: opp | 모드: interactive

## 작업 결과 요약

PM Gate에 §13 "컨벤션 자동 진단" 항목을 신설하여 EXECUTE/TEST 워커 완료 후 `changed_files`를 영역별로 분할해 `opal-convention-checker`에 병렬 디스패치하고 영역별 보고서로 컨벤션 준수를 객관 검증하는 절차를 하네스에 정착시켰다.

오케스트레이터별 발동 위치:
- **opp / opdw**: EXECUTE PM Gate에서 §13 발동 (자체 EXECUTE PM Gate 보유)
- **opd / opds**: TEST PM Gate에서 §13 발동 (EXECUTE 후 PM Gate 의도적 부재 — TEST가 종합 검증 위치 — R-T4 (b) 옵션 채택)

## 요구사항 충족 (R-1 ~ R-8)

| # | 요구사항 | 결과 |
|---|---------|------|
| R-1 | PM Gate 검토 §13 항목 신설 | ✅ pm-review-gate.md §검토 절차에 13번 신설 (7개 소절: 트리거 / 영역 분할 / 호출 / 입력 명세 / 판정 / 스킵 3종 / 하위 호환) |
| R-2 | 영역 자동 판정 규약 | ✅ §13에 `context-injection.md` §PROJECT.md 프로젝트 구성 기반 라우팅 D-3 인용 + `scope=all` 폴백 |
| R-3 | opal-convention-checker 입력 명세 확장 | ✅ AGENT.md §입력 명세에 "PM Gate 호출 시나리오 (참고)" 7행 매핑 표 + timestamp 분리 규약 |
| R-4 | 보고서 파일명 규약 | ✅ Phase 5 `file_suffix` 변수 도입 — 단일(`{timestamp}`) / 영역별(`{scope}-{timestamp}`) 2종 분기 |
| R-5 | 판정 기준 명문화 | ✅ §13에 Critical/High = Fail / Medium 이하 = Pass 표 + Fail → 1회 재지시 → 캡틴 에스컬레이션 흐름 |
| R-6 | 스킵 조건 3종 | ✅ §13에 changed_files=0 / 컨벤션 적용 외 / CONVENTIONS.md 부재 3종 + 처리 방식 분기 명시 |
| R-7 | 하위 호환 | ✅ §13에 `.opal/AGENT.md` 미존재 시 PM Gate 자체 스킵으로 §13 동시 스킵 명시 |
| R-8 | 4개 오케스트레이터 SKILL.md PM Gate 점검 목록 갱신 | ✅ opp/opdw EXECUTE 행 산출물 컬럼에 `GC-CONVENTION-*.md` 추가 / opd/opds TEST 행 산출물·체크리스트 컬럼 갱신 + STEP 5(opd) / STEP 4(opds) 검증 체크리스트 6번째 항목 "컨벤션 자동 진단 PASS" 신설 / oppd 비변경 사유(PM Gate 점검 목록 섹션 부재) 명시 |

## 산출물

| # | 파일 | 크기 | 비고 |
|---|------|------|------|
| 1 | `tasks/136-260508-opp-pm-gate-convention-auto-check/TASK.md` | 10KB | 요구사항 R-1~R-8 + 확정 설계 방향 7항 |
| 2 | `tasks/136-260508-opp-pm-gate-convention-auto-check/PLAN.md` | 460줄 | 6 Step / 3 Phase 구현 계획 + R-T4 (b) 옵션 정정(v1.1) |
| 3 | `tasks/136-260508-opp-pm-gate-convention-auto-check/QA-PLAN.md` | 11KB | PLAN 검증 보고서 (R-1~R-8 1:1 매핑) |
| 4 | `tasks/136-260508-opp-pm-gate-convention-auto-check/QA-EXECUTE.md` | 8.2KB | EXECUTE 검증 보고서 — 6 Step grep 테스트 + R-1~R-8 + 일관성 5 + 문서 품질 8 모두 Pass |
| 5 | `tasks/136-260508-opp-pm-gate-convention-auto-check/DONE.md` | (이 파일) | 완료 보고 |

## 변경 파일 (changed_files)

| # | 파일 (진본) | 버전 | 변경 요약 |
|---|------------|------|----------|
| 1 | `opal/core/references/harness/pm-review-gate.md` | v1.2 | §검토 절차 §13 "컨벤션 자동 진단" 신설 (7개 소절) |
| 2 | `opal/agents/opal-convention-checker/AGENT.md` | v1.2 | §입력 명세 PM Gate 호출 시나리오 표 + Phase 5 `file_suffix` 변수 + Phase 6 결과 반환 JSON 동기 갱신 |
| 3 | `opal/skills/opal-pilot-project/SKILL.md` | v2.8 | §PM Gate 점검 목록 EXECUTE 행 산출물 컬럼에 `GC-CONVENTION-*.md` 추가 |
| 4 | `opal/skills/opal-pilot-dev/SKILL.md` | v3.5 | §PM Gate 점검 목록 TEST 행 산출물·체크리스트 컬럼 갱신 + STEP 5 TEST PM Gate 검증 체크리스트 6번째 항목 신설 |
| 5 | `opal/skills/opal-pilot-dev-short/SKILL.md` | v3.4 | §PM Gate 점검 목록 TEST 행 산출물·체크리스트 컬럼 갱신 + STEP 4 TEST PM Gate 검증 체크리스트 6번째 항목 신설 |
| 6 | `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | v2.5 | §PM Gate 점검 목록 EXECUTE 행 산출물 컬럼에 `GC-CONVENTION-*.md` 추가 |

## 검증 결과

- **PLAN PM Gate**: state validate Pass (violations 0건)
- **EXECUTE QA Gate**: Pass — grep 테스트 6/6 / R-1~R-8 8/8 / 일관성 5/5 / 문서 품질 8/8
- **EXECUTE PM Gate**: Pass — 자가 진단 5/5 (산출물 / 체크리스트 갱신 / `~/.opal/` 미편집 / state validate / AGENT.md 부재 PM 검토 스킵)
- **CLOSE 진입 게이트**: 통과 (캡틴 "확인" 발화 → row 18 owner=user mark)

## 후속 태스크

- **태스크 137 (사전 주입 강화 — 제안 A)**: 본 세션 보류 상태로 보존 (`tasks/137-260508-opp-plan-convention-injection/`). PLAN row 4(🔄) 진행 중. 본 태스크 CLOSE 후 캡틴 재개 발화로 PLAN 워커 디스패치 재시도 가능. 잠재 적용 지점 4종(dispatch-process / opal-plan-agent / op-task-plan + op-dev-plan / citation-rules §2.5)은 PLAN 정밀 분석 위임.
- **R-T4 후속**: opd/opds STEP 4(opd) / STEP 3(opds) 본문에 명시적 EXECUTE PM Gate 호출이 정의되어 있지 않은 점은 본 태스크 (b) 옵션 채택으로 일관 정합 처리됨. 별도 후속 태스크 불필요.

## 변경이력

| 버전 | 일시 (KST) | 변경 |
|------|-----------|------|
| v1.0 | 2026-05-08 22:07 | 태스크 완료 보고 |
