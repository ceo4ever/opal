# QA-EXECUTE: 테스트 시나리오 양식·작성 흐름·파이프라인 재설계

> 검증일: 2026-05-15 17:10 | 검증 대상: 8개 변경 파일 + PLAN.md 체크리스트
> QA Agent: opal-task-qa-agent | 스킬: op-task-qa | 적용 모드: semi-agentic (PM 자율)

---

## 종합 판정

**Pass** — 32개 검증 항목(§A 21개 기능 + §B 5개 일관성 + §C 6개 문서품질) 100% 통과. 모든 변경이 PLAN.md 요구사항을 정확히 구현하였으며, 변경이력 추적성 완벽, SSOT 준수, 배포 경계 무결. 다음 단계 진행 가능.

---

## §A. §4.1 기능 테스트 결과 (21개 grep 항목)

| # | F-ID | 검증 항목 | grep 결과 | 판정 |
|---|------|---------|---------|------|
| 1 | F-001 | 리스크 가설 표 컬럼 6종 존재 | `grep "ID \| 변경 단위 \| 깨질 수 있는 계약"` = 1건 | Pass |
| 2 | F-001 | L1 기능 단위 서브헤딩 | `grep "L1\. 기능 단위"` = 1건 | Pass |
| 3 | F-001 | 사전 조건 데이터 표 (테이블/식별자/상태/출처) | `grep "테이블.*식별자.*상태.*출처"` = 1건 | Pass |
| 4 | F-001 | L2 프로세스 통합 서브헤딩 | `grep "L2\. 프로세스 통합"` = 1건 | Pass |
| 5 | F-001 | L3 사용자 협업 서브헤딩 | `grep "L3\. 사용자 협업"` = 1건 | Pass |
| 6 | F-002 | 시나리오 수 가이드 섹션 삭제 | `grep "시나리오 수 가이드"` (본문) = 0건 | Pass |
| 7 | F-002 | mock 금지 룰 존재 | `grep "mock 금지"` = 2건 | Pass |
| 8 | F-002 | 계층 결정 규칙 표 신설 | `grep "계층 결정 규칙"` = 1건 | Pass |
| 9 | F-003 | STEP 3.5 TEST-SCENARIO 단계 신설 | `grep "STEP 3.5"` = 2건 | Pass |
| 10 | F-003 | STATE.md 도메인 치환값 28행 구조 | 행 19 = TEST-SCENARIO 사용자 확인 | Pass |
| 11 | F-003 | 모드 경계 이동 (PLAN → TEST-SCENARIO) | `grep "TEST-SCENARIO 사용자 확인"` = 2건 | Pass |
| 12 | F-004 | scenario_source 파라미터 추가 | `grep "scenario_source"` op-dev-execute = 3건 | Pass |
| 13 | F-004 | 자가 점검 절차 섹션 신설 | `grep "자가 점검 절차"` = 1건 | Pass |
| 14 | F-005 | EXECUTE 디스패치 scenario_source 필드 | `grep "scenario_source"` opal-pilot-dev = 2건 | Pass |
| 15 | F-006 | PLAN.md 양식 리스크 가설 표 (SSOT) | `grep "리스크 가설 표"` op-dev-plan = 4건 | Pass |
| 16 | F-006 | 가설 도출 예시 3종 | `grep "H-예1"` = 1건 | Pass |
| 17 | F-006 | plan-agent 행동 규칙 "리스크 가설 표 작성 의무" | `grep "리스크 가설 표"` opal-plan-agent = 1건 | Pass |
| 18 | F-007 | PM Gate TEST-SCENARIO Phase 행 추가 | TEST-SCENARIO 행에 6항목 체크리스트 명시 | Pass |
| 19 | F-008 | 모드 경계 표 opd 행 갱신 | `grep "TEST-SCENARIO 사용자 확인"` harness = 2건 | Pass |
| 20 | F-009 | L3 협업 게이트 (STEP 5 SKILL.md) | `grep "5-0. L3"` = 1건 | Pass |
| 21 | F-010 | 변경이력 행 (004) 8개 파일 모두 | 8개 파일 모두 1건씩 = 8/8 | Pass |

**소계: 21/21 Pass**

---

## §B. §4.2 일관성 테스트 결과 (5개)

| # | 항목 | 검증 방법 | 결과 | 판정 |
|---|------|---------|------|------|
| 1 | SKILL.md 통일 형식 vs guide 프로세스 일치 | op-dev-test-scenario/SKILL.md: 7섹션 존재 / test-scenario-guide.md: 5단계 프로세스 명시 | 일치 | Pass |
| 2 | STEP 3.5와 STEP 4 자연스러운 연결 | STEP 3.5 "알투(PM)+캡틴 페어 작성" → STEP 4 EXECUTE 워커 디스패치 흐름 확인 | 자연스러움 | Pass |
| 3 | STATE.md 행 19 = TEST-SCENARIO 사용자 확인 + 모드 경계 | 행 19: \| 19 \| TEST-SCENARIO \| 사용자 확인 \| / 모드 경계 설명: "TEST-SCENARIO 사용자 확인 행 통과 후 → EXECUTE 작업 행부터 PM 자율" | 일치 | Pass |
| 4 | plan-agent 행동규칙 vs op-dev-plan SKILL.md 양식 | plan-agent: "의무" 표현 / op-dev-plan: 6컬럼 양식(ID/변경단위/계약/영향/계층권고/시나리오후보) 정의 | 일치 | Pass |
| 5 | 변경이력 버전 (+0.1 이상) | op-dev-test-scenario v1.3→v1.4 / test-scenario-guide v1.0→v2.0 / opal-pilot-dev v3.7→v3.8 | 모두 충족 | Pass |

**소계: 5/5 Pass**

---

## §C. §4.3 문서 품질 결과 (6개)

| # | 항목 | 검증 방법 | 결과 | 판정 |
|---|------|---------|------|------|
| 1 | 모든 변경 파일 변경이력 행 (F-010) | 8개 파일 모두 `grep "(004)"` = 1건 | 완벽 | Pass |
| 2 | ~/.opal 파일 직접 수정 없음 (배포 경계) | ~/.opal 경로 최근 24시간 수정 0개 | 준수 | Pass |
| 3 | 한국어 본문 + 영어 코드/필드명 규칙 | 모든 변경 파일: 한국어 설명 + scenario_source/H-N/L1/L2/L3 등 영어 코드 일관성 | 준수 | Pass |
| 4 | SSOT 분산 없음 (PLAN.md 양식 단일 위치) | op-dev-plan/SKILL.md에만 양식 정의(4회) / opal-plan-agent는 "의무" 1줄만 명시 | 단일 위치 | Pass |
| 5 | opds 변경 없음 (범위 외 확인) | opal-pilot-dev-short/SKILL.md 최근 수정 없음 (2026-05-09) | 준수 | Pass |
| 6 | mams 107 태스크 retroactive 갱신 없음 | 107 태스크 최근 수정: state.json / STATE.md / DONE.md 등 working 파일만 (프로젝트 소스 변경 없음) | 준수 | Pass |

**소계: 6/6 Pass**

---

## §D. QA-PLAN 권고 3건 반영 확인

| # | 권고 | 반영 확인 | 판정 |
|---|------|---------|------|
| 1 | STATE.md 28행 적용 + 행 19 = TEST-SCENARIO 사용자 확인 + 모드 경계 명시 | 행 19: \| TEST-SCENARIO \| 사용자 확인 \| / 모드 경계: "TEST-SCENARIO 사용자 확인 행 통과 후 EXECUTE부터 PM 자율" 명시 | Pass |
| 2 | §8 차이 표에 TEST-SCENARIO 행 + "(opd 전용)" 비고 | \| TEST-SCENARIO 완료 \| 사용자 승인 \| 사용자 승인 (모드 경계) \| PM 자율 \| opd 전용 \| | Pass |
| 3 | STEP 3.5 작성자 "알투(PM)+캡틴 페어" 명기 + "self-confirming 방지" 명시 | STEP 3.5 본문: "작성자: **알투(PM) + 캡틴 페어** — 오케스트레이터가 직접 작성 (워커 디스패치 없음). 이 단계는 self-confirming 방지를 위해 PLAN 워커와 다른 작성자가 수행한다." | Pass |

**소계: 3/3 Pass**

---

## 발견 사항

### FAIL
없음 — 모든 검증 항목 통과

### 보강 권고
없음 — 변경 사항이 명확하고 PLAN.md 요구사항을 정확히 구현함

---

## PLAN.md 체크리스트 갱신 결과

- **§4.1 기능 테스트**: 21/21 [x] — 모든 항목 통과
- **§4.2 일관성 테스트**: 5/5 [x] — 모든 항목 통과
- **§4.3 문서 품질**: 6/6 [x] — 모든 항목 통과

---

## 결론

### 판정 근거

EXECUTE 단계 검증 결과 32개 항목 전수 통과. 테스트 시나리오 양식 재설계가 정확히 구현되었으며, 파이프라인 5단계 직렬화(TASK→ANALYSIS→PLAN→TEST-SCENARIO→EXECUTE→TEST→CLOSE)의 구조적 변경이 일관성 있게 반영됨. 특히:

1. **양식 SSOT 신설**: op-dev-test-scenario/SKILL.md 통일 형식 7섹션(리스크 가설 표→테스트 데이터→L1/L2/L3→매핑→코드품질→보안→판정) 완성
2. **파이프라인 분리**: PLAN(가설 표 생성)과 TEST-SCENARIO(시나리오 작성)의 워커 분리로 self-confirming 구조 제거
3. **모드 경계 이동**: STATE.md 행 19로 명시된 TEST-SCENARIO 사용자 확인 행을 semi-agentic 모드 경계로 설정 — EXECUTE부터 PM 자율
4. **검증 체크리스트 자동화**: PM Gate에 TEST-SCENARIO Phase 행 추가(mock 금지 grep 포함) — 7대 강제 룰 명시

변경이력 추적(8개 파일 모두 (004) 태스크 번호 포함), 배포 경계 준수(~/.opal 수정 없음), SSOT 단일 위치(op-dev-plan/SKILL.md) 모두 충족.

### 다음 단계

QA 통과. 워커 구현(EXECUTE) 단계로 진행 가능. 변경 내용이 프로젝트 소스에만 적용되었으므로 캡틴의 install-mac.sh 배포 후 신규 태스크부터 적용 예정.

---

## 첨부: 변경 파일 8개 요약

| 파일 | 버전 | 변경사항 |
|------|------|---------|
| op-dev-test-scenario/SKILL.md | v1.3→v1.4 | 통일 형식 7섹션 재편 |
| test-scenario-guide.md | v1.0→v2.0 | 5단계 프로세스 + 계층 결정 규칙 + mock 금지 |
| opal-pilot-dev/SKILL.md | v3.7→v3.8 | 5단계 파이프라인(STEP 3.5 신설) + STATE.md 28행 + PM Gate + L3 게이트 |
| op-dev-execute/SKILL.md | v2.5→v2.6 | scenario_source input + 자가 점검 절차 |
| op-dev-plan/SKILL.md | v1.4→v1.5 | 리스크 가설 표 양식 신설 (SSOT) |
| opal-plan-agent/AGENT.md | v1.8→v1.9 | 리스크 가설 표 작성 의무 |
| opal-test-agent/AGENT.md | v1.5→v1.6 | L3 [SUPERVISOR] 마커 즉시 PM 반환 |
| opal-harness-semi-agentic.md | v1.2→v1.3 | §3 모드 경계 갱신 + §8 TEST-SCENARIO 행 추가 |

---

**QA 완료 일시**: 2026-05-15 17:10 KST  
**QA Agent**: opal-task-qa-agent  
**스킬**: op-task-qa  
**판정**: Pass
