---
name: opal-pilot-dev-short
description: |
  **Short Task 오케스트레이터 (기본 모드)**. 코드 변경이 수반되는 모든 개발 작업의 기본 진입점. 3단계 파이프라인으로 수행한다.
  반드시 이 스킬을 사용해야 하는 상황: "opal-pilot-dev-short", "opds".
  PLAN 단계에서 규모가 크다고 판단되면 Full Task(opal-pilot-dev) 에스컬레이션을 제안한다.
  코드를 읽기만 하는 설명 요청, API 명세서(api-analyzer), 기획 문서(opal-pilot-write-tech), PR 리뷰, git 작업, 단순 설정 변경은 이 스킬이 아니다.
---

# Short Task 오케스트레이터

## Harness
모드: Short Task (TASK → PLAN+TEST-SCENARIO → EXECUTE)
> 부트스트랩에서 로드되지 않은 경우: `~/.opal/references/opal-harness.md`를 Read한다.

**[MUST]** 스킬 시작 즉시 모드에 따라 서브 하네스를 Read한다. 이 단계를 건너뛰면 안 된다:
- `--agentic` 플래그 있음 → `~/.opal/references/opal-harness-agentic.md`를 Read한다
- `--agentic` 없음 (기본) → `~/.opal/references/opal-harness-interactive.md`를 Read한다

---

## STEP 1: TASK

harness "4. TASK 공통 프로세스" 참조. 다음 단계명: PLAN.

---

## STEP 2: PLAN + TEST-SCENARIO

워커를 디스패치하여 코드 분석과 구현 계획을 통합 수립한다. **ANALYSIS.md를 전달하지 않는다** -- op-dev-plan이 자동으로 코드 분석을 포함한다.

> **Short Task는 단계를 줄이는 것이지, 분석을 줄이는 것이 아니다.** ANALYSIS.md 없이 호출되면 op-dev-plan이 코드 분석을 직접 수행한다. 분석 품질은 Full Task와 동일해야 한다.

### PLAN 디스패치

op-dev-plan 워커 디스패치. **model**: advanced. 이전 산출물: TASK.md만 (ANALYSIS.md 없음).
워커 완료 -> **QA Gate** (op-dev-qa) -> **PM Gate** (TASK.md 요구사항 체크박스 갱신 포함 — 하네스 §3 참조).

> **[PM 컨텍스트 주입]** 워커 디스패치 프롬프트의 첫 줄에 `[WORKER]`를 삽입한다. `[WORKER]` 마커가 있으면 워커는 부트스트랩을 생략한다. PM은 디스패치 시 다음을 프롬프트에 포함해야 한다:
> 1. 하네스 Guards 핵심 규칙 (구현 금지 원칙, 커밋 규칙)
> 2. 관련 참조 문서 경로 (docs/PROJECT.md 문서 테이블 기반)
> 3. 기술 스택 연동 지시 (기존 "참조 문서 전달 의무" 통합)

### TEST-SCENARIO 스킵 조건

**문서 전용** 작업(PLAN.md 파일 변경 계획이 모두 `.md`, 소스 코드 없음)이면 스킵. 보고 시 "TEST-SCENARIO: 문서 전용 작업으로 스킵" 표기.

### TEST-SCENARIO 디스패치 (연속)

QA + PM Gate 통과 후 op-dev-test-scenario 워커 연속 디스패치. **model**: light. 이전 산출물: TASK.md + PLAN.md.
워커 완료 -> PLAN + TEST-SCENARIO를 함께 사용자에게 보고. **승인 = EXECUTE 시작 허가**.

> **[PM 컨텍스트 주입]** 디스패치 프롬프트 첫 줄에 `[WORKER]` 삽입. 하네스 Guards 핵심 규칙 + 관련 참조 문서 경로를 포함한다.

---

## STEP 3: EXECUTE

op-dev-execute 워커 디스패치. **model**: standard. checklist_source: PLAN.md 섹션 "3. 실행 체크리스트". execution-plan.json 있으면 전달.

> **[PM 컨텍스트 주입]** 디스패치 프롬프트 첫 줄에 `[WORKER]` 삽입. 하네스 Guards 핵심 규칙 + 관련 참조 문서 경로를 포함한다.

### EXECUTE 완료 후

워커가 changed_files를 반환하면:
1. **op-dev-test-agent 워커 호출** -> TEST-SCENARIO.md에 결과 채움 + 판정
2. **PM Gate** — TEST-SCENARIO 결과 검토 + QA 체크리스트 갱신 (공통 하네스 §2 "QA 체크리스트 검증" 참조)
3. **DONE.md 생성**
4. 사용자에게 완료 보고

---

## 에스컬레이션 규칙

op-dev-plan 결과에서 아래 조건이 감지되면 **Full Task(opal-pilot-dev) 전환을 제안**한다:

| 조건 | 판별 방법 |
|------|----------|
| 예상 변경 파일 >= 10개 | PLAN.md 파일 변경 계획에서 카운트 |
| 다단계 기술 의사결정 | 아키텍처 선택, 기술 스택 비교가 필요한 수준 |
| 다중 모듈 연쇄 영향 | 변경이 3개 이상 독립 모듈에 연쇄 영향 |

```
[에스컬레이션 제안]
이 작업은 Short Task 범위를 초과할 수 있습니다: {해당 조건}
Full Task(opal-pilot-dev)로 전환할까요?
- "Full로 해줘" -> Full Task 전환
- "Short로 진행해" -> Short Task 유지
```

---

## STATE.md 도메인 치환값

| 필드 | 값 |
|------|------|
| 모드 | Short Task |
| 단계 목록 | TASK / PLAN+TEST-SCENARIO / EXECUTE |
| 산출물 목록 | TASK.md, PLAN.md, TEST-SCENARIO.md, QA-*.md, DONE.md |

---

## Agentic Mode

opal-harness-agentic.md 참조. `--agentic` 플래그 활성화 시 이 스킬의 차이점만 기술한다.

### 활성화

`//opds --agentic {작업 설명}` 형식으로 호출. STATE.md 모드 필드를 `agentic`으로 기록한다.

### 자율 게이트 흐름

```
TASK (PM 직접) → PLAN+TEST-SCENARIO Gate → EXECUTE Gate
                   PM 자율 검토              PM 자율 검토
```

- TASK 이후 2개 게이트를 PM이 자율 통과
- 각 게이트에서 opal-harness-agentic.md "Gate 루핑 규칙" 적용
- AGENTIC-LOG.md에 모든 판단/오류/수정/의사결정 기록

### 에스컬레이션 규칙 (agentic 유지)

에스컬레이션 규칙(Full Task 전환 제안)은 agentic mode에서도 유지한다. PM이 판단하여 자동 전환하지 않고, 사용자에게 에스컬레이션으로 보고한다.

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-03-26 | 초기 작성 -- dev-task-pilot 컴포지션 전환 |
| v1.1 | 2026-03-28 | TEST-SCENARIO를 PLAN STEP에 통합, EXECUTE 후 커밋 규칙 추가 |
| v1.2 | 2026-03-28 | TEST-SCENARIO 문서 전용 스킵 조건 추가 |
| v1.3 | 2026-03-28 | harness 참조 슬림화 -- 공통 인프라를 opal-harness.md로 위임 |
| v1.4 | 2026-03-29 | 컴포넌트 리네이밍 (042) |
| v1.5 | 2026-03-29 | model override를 레벨 기반으로 전환 (044) |
| v1.6 | 2026-03-31 | Agentic Mode 섹션 추가 (057) |
| v1.7 | 2026-03-31 | §7 참조 → opal-harness-agentic.md 참조 전환. EXECUTE 후 PM Gate + QA 체크리스트 갱신 추가 (058) |
| v1.8 | 2026-04-01 | 전체 워커 디스패치 서술에 `[WORKER]` 마커 + PM 컨텍스트 주입 지침 추가 (063) |
| v1.9 | 2026-04-02 | PLAN PM Gate에 TASK.md 체크박스 갱신 명시 (072) |
