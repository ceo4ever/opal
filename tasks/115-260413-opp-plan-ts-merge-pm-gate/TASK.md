---
@header
type: task
task: "115 PLAN 워커 TEST-SCENARIO 통합 + QA Gate 제거 + PM Gate 검증 강화"
layer: task
---

# TASK: PLAN 워커 TEST-SCENARIO 통합 + QA Gate 제거 + PM Gate 검증 강화

> 작성일: 2026-04-13 | 작업 유형: 개선 | 적용 스킬: opp | 모드: interactive
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

`opal-pilot-dev` / `opal-pilot-dev-short`의 PLAN 단계에서 TEST-SCENARIO 별도 워커 디스패치와 QA Gate를 제거하고, PLAN 워커가 두 산출물을 통합 작성하며 PM Gate가 직접 검증하는 방식으로 파이프라인을 슬림화한다.

## 배경

현재 opd/opds의 PLAN 단계는 워커 3번 디스패치(PLAN → TEST-SCENARIO → QA)로 구성되어 단계가 길고 토큰 소비가 크다.

## 배경 분석 (대화에서 도출)

**현재 구조 (opd/opds 공통)**

```
PLAN 워커(advanced) → TEST-SCENARIO 워커(light) → QA 워커 → State Gate → PM Gate → 사용자 확인
         (3번 디스패치)
```

**토큰 구조 분석**
- 서브에이전트는 별도 컨텍스트 윈도우로 실행됨
- 메인 컨텍스트에는 디스패치 프롬프트 + 결과 요약만 쌓임
- 3번 디스패치 = 3번의 컨텍스트 초기화 오버헤드

**TEST-SCENARIO 작성 적합성**
- PLAN 워커는 코드 분석 + 설계를 완료한 상태 → 테스트 시나리오를 가장 잘 쓸 수 있는 시점
- 기존 TEST-SCENARIO는 `light` 모델이었으나, PLAN의 `advanced` 모델이 작성하면 품질도 향상

**QA Gate 제거 타당성**
- QA Gate의 역할(독립 검토)을 PM Gate가 직접 흡수
- PM Gate에 PLAN.md + TEST-SCENARIO.md Read + 구체적 검증 체크리스트 명시 시 실질적 효과 가능

**PM Gate Read 필요성 확인**
- PM Gate는 워커가 아니라 PM(알투)이 직접 수행
- 워커 반환값은 요약(summary)이므로 PM이 직접 Read해야 실질적 검증 가능
- PM Gate 절차에 "PLAN.md Read → TEST-SCENARIO.md Read → 검증" 명시 필요

## 확정된 설계 방향 (대화에서 합의)

1. **PLAN 워커 통합**: PLAN 워커가 PLAN.md + TEST-SCENARIO.md 통합 작성 (단일 디스패치)
2. **QA Gate 제거**: PLAN 단계의 QA Gate + QA-PLAN.md 생성 제거
3. **PM Gate 강화**: PM Gate에 PLAN.md + TEST-SCENARIO.md 직접 Read 절차와 검증 체크리스트 명시
4. **TEST-SCENARIO.md 파일 유지**: 별도 파일 구조는 유지 (EXECUTE/TEST 단계에서 참조)
5. **op-dev-test-scenario SKILL.md**: 수정하지 않음 (opd/opds에서 호출하지 않는 것으로 충분)

## 요구사항

- [ ] **R-1**: `op-dev-plan/SKILL.md`에 TEST-SCENARIO.md 작성 Step 추가
  - **무엇을**: Step 9(PLAN.md 작성) 완료 후 TEST-SCENARIO.md 작성 Step(Step 10)을 추가하고, 기존 Step 10(결과 반환)을 Step 11로 이동
  - **어디에**: `opal/skills/op-dev-plan/SKILL.md` — 프로세스 섹션
  - **왜**: PLAN 워커가 두 산출물을 통합 작성하기 위함 (확정 방향 §1)
  - **AC**: 프로세스에 TEST-SCENARIO.md 작성 Step이 존재하고, TEST-SCENARIO.md 형식(시나리오 목록/코드 품질/보안/회귀 테스트/판정/설계 피드백 섹션)이 명시되어 있다. frontmatter description의 "보장 출력"에 TEST-SCENARIO.md가 포함된다. 결과 반환 Step에 TEST-SCENARIO.md 경로가 포함된다.

- [ ] **R-2**: `opal-pilot-dev/SKILL.md` PLAN 단계 슬림화
  - **무엇을**: STEP 3에서 "3-2. TEST-SCENARIO 디스패치" 섹션 제거, QA Gate + QA-PLAN.md 행 제거, PM Gate에 PLAN+TS 검증 절차 추가
  - **어디에**: `opal/skills/opal-pilot-dev/SKILL.md` — STEP 3, PM Gate 점검 목록
  - **왜**: 확정 방향 §2, §3
  - **AC**: STEP 3에 TEST-SCENARIO 별도 디스패치가 없다. QA Gate / QA-PLAN.md 참조가 없다. PM Gate에 "PLAN.md Read → TEST-SCENARIO.md Read → 검증 체크리스트" 절차가 명시되어 있다. PM Gate 점검 목록의 산출물에 QA-PLAN.md가 없고 PLAN+TEST-SCENARIO 검증 체크리스트 항목이 있다.

- [ ] **R-3**: `opal-pilot-dev/SKILL.md` STATE.md 행 예시 갱신
  - **무엇을**: TEST-SCENARIO 단계 행, QA Gate 행, QA-PLAN.md 생성 행 제거. PLAN 단계 아래 TEST-SCENARIO.md 생성 행 추가
  - **어디에**: `opal/skills/opal-pilot-dev/SKILL.md` — STATE.md 도메인 설정 > 진행 현황 행 예시
  - **왜**: 파이프라인 구조 변경 반영 (확정 방향 §1, §2)
  - **AC**: 진행 현황 행 예시에 TEST-SCENARIO 단계 행이 없고, PLAN 단계 하위에 TEST-SCENARIO.md 생성 행이 있다. QA Gate / QA-PLAN.md 행이 없다.

- [ ] **R-4**: `opal-pilot-dev-short/SKILL.md` PLAN 단계 슬림화 (R-2와 동일 내용)
  - **무엇을**: TEST-SCENARIO 별도 디스패치 제거, QA Gate + QA-PLAN.md 제거, PM Gate 검증 절차 추가
  - **어디에**: `opal/skills/opal-pilot-dev-short/SKILL.md` — STEP 2, PM Gate 점검 목록
  - **왜**: 확정 방향 §2, §3
  - **AC**: R-2와 동일 기준

- [ ] **R-5**: `opal-pilot-dev-short/SKILL.md` STATE.md 행 예시 갱신 (R-3과 동일 내용)
  - **무엇을**: TEST-SCENARIO 단계 행, QA Gate 행, QA-PLAN.md 생성 행 제거. PLAN 단계 아래 TEST-SCENARIO.md 생성 행 추가
  - **어디에**: `opal/skills/opal-pilot-dev-short/SKILL.md` — STATE.md 도메인 치환값 > 진행 현황 행 예시
  - **왜**: R-3과 동일
  - **AC**: R-3과 동일 기준

- [ ] **R-6**: `opal-pilot-dev/SKILL.md` EXECUTE/TEST 단계 슬림화
  - **무엇을**: STEP 5(TEST) PASS 시에서 "QA Gate (op-dev-qa) → State Gate" 제거. PM Gate에 TEST-SCENARIO.md Read + 검증 체크리스트 추가. PM Gate 점검 목록에서 QA-EXECUTE.md 제거 및 TEST 검증 항목으로 교체. STATE.md 행 예시에서 TEST 단계 QA Gate 행 + QA-EXECUTE.md 생성 행 제거.
  - **어디에**: `opal/skills/opal-pilot-dev/SKILL.md` — STEP 5, PM Gate 점검 목록, STATE.md 행 예시
  - **왜**: PLAN 단계와 동일 철학 — TEST 단계 QA Gate 역할을 PM Gate가 직접 흡수. TEST 워커가 이미 TEST-SCENARIO.md를 실행·기록하므로 별도 QA 에이전트가 중복됨.
  - **AC**: STEP 5 PASS 흐름에 QA Gate / QA-EXECUTE.md 참조가 없다. PM Gate에 "TEST-SCENARIO.md Read → 검증 체크리스트" 절차가 있다. PM Gate 점검 목록에 QA-EXECUTE.md가 없고 TEST-SCENARIO.md 검증 항목이 있다. STATE.md 행 예시 TEST 단계에 QA Gate / QA-EXECUTE.md 행이 없다.

- [ ] **R-7**: `opal-pilot-dev-short/SKILL.md` EXECUTE/TEST 단계 슬림화 (R-6와 동일 내용)
  - **무엇을**: STEP 4(TEST) PASS 시에서 "QA Gate (op-dev-qa) → State Gate" 제거. PM Gate Read 절차 + 검증 체크리스트 추가. PM Gate 점검 목록 갱신. STATE.md 행 예시 갱신.
  - **어디에**: `opal/skills/opal-pilot-dev-short/SKILL.md` — STEP 4, PM Gate 점검 목록, STATE.md 행 예시
  - **왜**: R-6과 동일
  - **AC**: R-6과 동일 기준

## 제약 조건

- `op-dev-test-scenario/SKILL.md`는 수정하지 않는다 (호출하지 않는 것으로 충분)
- TEST-SCENARIO.md 파일 형식은 `op-dev-test-scenario/SKILL.md`의 기존 형식을 그대로 따른다
- 각 파일에 변경이력(버전) 추가 필수
- AGENT.md 확정 기준 §2: `~/.opal/` 경로 직접 수정 금지 — 소스 경로(`opal/skills/`)에서만 수정

## 기술 스택

- Markdown 문서 작업 (스킬/오케스트레이터 SKILL.md)

## 관련 문서

- `opal/skills/op-dev-plan/SKILL.md` — PLAN 워커 스킬
- `opal/skills/opal-pilot-dev/SKILL.md` — Full Task 오케스트레이터
- `opal/skills/opal-pilot-dev-short/SKILL.md` — Short Task 오케스트레이터
- `opal/skills/op-dev-test-scenario/SKILL.md` — 기존 TEST-SCENARIO 스킬 (형식 참조용)
- `~/.opal/references/opal-harness.md` — 하네스 공통
- `~/.opal/references/opal-harness-interactive.md` — PM Gate 절차
