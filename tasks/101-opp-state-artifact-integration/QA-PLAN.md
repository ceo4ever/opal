# QA: PLAN — STATE.md 진행 현황 + 완료 산출물 통합

> 검토일: 2026-04-09 | 판정: Pass

## 1. 요약

STATE.md 진행 현황 테이블에 산출물 행을 통합하여 워커의 산출물 누락을 순서 강제로 방지하는 개선 작업이다. PLAN은 공통 하네스(opal-harness.md)의 진행 현황 행 구성 규칙 확장과 Artifact Gate 역할 재정의, 그리고 opp/opds/opd/opdw/opsdd 5개 스킬의 진행 현황 행 예시 갱신을 7개 파일 변경으로 구체화했다. 각 스킬별 필수 산출물 행의 삽입 위치·형식·상태 전이 규칙이 설계 원칙으로 명확히 제시되며, 실제 예시 테이블(opp 23행, opds 27행, opd 37행, opdw 21행)로 검증 가능한 수준으로 명세되어 있다. Step 1~7 실행 체크리스트와 Pass/Fail 판정 가능한 QA 체크리스트가 포함되어 있다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| GP-1 | 즉시 실행 가능성 | Pass | 각 Step에 파일 경로, 작업 내용, 완료 기준, 테스트 방법이 명시됨. 이 PLAN만으로 실행 진입 가능. |
| GP-2 | 의존성 순서 | Pass | Phase 1(Step 1,2 병렬) → Phase 2(Step 3~6 병렬, Step 1 의존) → Phase 3(Step 7, Step 1 의존). 의존성 순서 타당함. |
| GP-3 | TASK 반영 | Pass | TASK 요구사항 4개(진행 현황 행 통합, 오케스트레이터 도메인값 갱신, Artifact Gate 조정, 공통 템플릿 갱신) 모두 PLAN에 반영됨. |
| GP-4 | 파일 목록 완전성 | Warning | TASK 요구사항 2번에 "opp/opds/opdw/opsdd"가 명시되나 PLAN은 opd를 추가로 포함(7개). TASK 영향 범위에 opd가 있으므로 타당하나, TASK 요구사항 항목과 불일치 서술이 있음. |
| GP-5 | 설계 구체성 | Pass | 산출물 행 삽입 규칙 5개 원칙, Artifact Gate 역할 재정의 문구, 스킬별 행 예시 테이블이 구체적으로 명세됨. |
| GP-6 | 체크리스트 커버리지 | Warning | opp QA 산출물 행(QA-PLAN.md 생성 #7) 위치가 QA Gate(#6) 직후, State Gate(#8) 직전으로 배치되나, 설계 원칙 3번은 "QA Gate 직후, Artifact Gate 직전"이라 기술함. State Gate가 중간에 위치하여 설계 원칙 서술과 실제 예시 사이에 미세한 표현 불일치가 있음. 실행에는 무방하나 원칙 문구 보완 필요. |

## 3. 지적 사항

### GP-4 Warning: TASK 요구사항 항목과 PLAN 변경 대상 파일 수 불일치

- **상황**: TASK.md 요구사항 2번에는 대상 스킬을 "opp / opds / opdw / opsdd"로 열거했으나, PLAN §1.1 "직접 변경 대상"에는 opd(`opal-pilot-dev/SKILL.md`)가 추가되어 총 7개 파일로 확장되었다.
- **판단**: TASK.md "영향 범위" 및 "관련 문서" 섹션에 opd가 명시되어 있으므로 PLAN의 포함은 타당하다. 그러나 요구사항 2번 항목 서술과 실제 변경 범위 사이에 문서적 불일치가 존재한다.
- **권고**: QA 통과(Warning). 실행 전 캡틴 확인 권장. opd 포함이 의도였다면 TASK 요구사항 2번 문구를 "opp / opds / opd / opdw / opsdd"로 갱신하거나, PLAN에 "요구사항 2번 범위 확장 근거" 주석을 추가하면 명확해진다.
- **심각도**: Warning

### GP-6 Warning: QA 산출물 행 위치 규칙 표현 모호성

- **상황**: 설계 원칙 3번은 "QA Gate 직후, Artifact Gate 직전"이라 기술하나, 실제 행 순서는 `QA Gate → QA 산출물 생성 → State Gate → Artifact Gate`이다. State Gate가 QA 산출물 행과 Artifact Gate 사이에 위치하여 "Artifact Gate 직전"이라는 표현이 정확하지 않다.
- **판단**: 실제 예시 테이블(opp #6~#9, opds #10~#12, opd #19~#22)을 보면 일관되게 `QA Gate → QA 산출물 → State Gate → Artifact Gate`로 배치되어 실행 관점에서는 문제없다. 단, 규칙 문구가 예시와 정확히 일치하지 않아 혼선 가능성이 있다.
- **권고**: 설계 원칙 3번 문구를 "QA Gate 직후, State Gate 직전에 삽입한다"로 수정하거나, "(QA Gate → QA 산출물 → State Gate → Artifact Gate 순)"으로 전체 순서를 명시하면 해소된다.
- **심각도**: Warning

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md | 요구사항 4개 반영 여부 | Pass — 4개 모두 §2 설계 및 Step에서 다룸 |
| TASK.md | 제약 조건(`~/.opal/` 직접 수정 금지, 소급 변경 안 함) | Pass — PLAN §5 리스크에서 "소급 변경 안 함" 명시. `~/.opal/` 금지는 명시적 언급 없으나 변경 파일이 모두 `opal/core/`, `opal/skills/` 범위임 |
| TASK.md | 영향 범위 파일 목록 vs PLAN 변경 대상 | Warning — TASK 영향 범위 6개 + opd(관련 문서) = PLAN 7개, 요구사항 2번 열거 vs PLAN 범위 불일치 |
| TASK.md | 산출물 행 삽입 위치(작업 직후 QA Gate 직전 / QA Gate 직후 Artifact Gate 직전 / PM Gate 직후) | Pass — 설계 원칙 1,3,4번에 명시됨. 단 3번 표현 모호성(GP-6 참조) |

## 5. 판정

**Pass**

TASK.md 4개 요구사항 모두 PLAN에 반영되었고, 7개 파일 변경 대상 및 산출물 행 삽입 규칙이 구체적으로 명세되어 있다. Warning 2개(opd 포함 근거 서술 불일치, QA 산출물 행 위치 표현 모호성)가 있으나 실행에 영향을 주지 않는 수준이다. 판정 기준(Warning 3개 미만)에 따라 Pass로 판정한다. 지적 사항은 EXECUTE 단계 실행 전 선택적으로 보완 가능하다.
