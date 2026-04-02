---
name: opal-pilot-dev
description: |
  **Full Task 오케스트레이터**. 대규모 개발 작업을 4단계 파이프라인으로 수행한다.
  반드시 이 스킬을 사용해야 하는 상황: "opal-pilot-dev", "opd".
  코드를 읽기만 하는 설명 요청, API 명세서(api-analyzer), 기획 문서(opal-pilot-write-tech), PR 리뷰, git 작업, 단순 설정 변경은 이 스킬이 아니다.
---
# Full Task 오케스트레이터

## Harness
모드: Full Task (TASK → ANALYSIS → PLAN+TEST-SCENARIO → EXECUTE)
> 부트스트랩에서 로드되지 않은 경우: `~/.opal/references/opal-harness.md`를 Read한다.

**[MUST]** 스킬 시작 즉시 모드에 따라 서브 하네스를 Read한다. 이 단계를 건너뛰면 안 된다:
- `--agentic` 플래그 있음 → `~/.opal/references/opal-harness-agentic.md`를 Read한다
- `--agentic` 없음 (기본) → `~/.opal/references/opal-harness-interactive.md`를 Read한다

## STEP 1: TASK
opal-harness.md "TASK 공통 프로세스" 참조.

## STEP 2: ANALYSIS
워커를 디스패치하여 코드베이스를 분석한다.

**디스패치 프롬프트**:
```
[WORKER]
op-dev-analysis 스킬을 수행하라.
**스킬 경로**: {op-dev-analysis/SKILL.md 탐색 경로}
**태스크 폴더**: {tasks/{NNN}-{name}/}
**이전 산출물**: {TASK.md 경로}
**프로젝트 컨텍스트**: {docs/PROJECT.md + 매칭 참조 문서. 미존재 시 CLAUDE.md 폴백}
**산출물 저장 경로**: {ANALYSIS.md 경로}
**하네스 Guards**: PLAN.md에 없는 파일 생성/수정 금지. PLAN 설계를 임의 변경 금지. 블로커 발생 시 즉시 중단 후 보고.
**참조 문서**: {docs/PROJECT.md 문서 테이블 기반 관련 문서 경로}
```
**model**: light

워커 완료 → **QA Gate** (op-dev-qa) → **PM Gate** → 사용자 보고.

## STEP 3: PLAN + TEST-SCENARIO
워커를 연속 디스패치하여 구현 계획과 테스트 시나리오를 작성한다.

### 3-1. PLAN 디스패치
```
[WORKER]
op-dev-plan 스킬을 수행하라.
**스킬 경로**: {op-dev-plan/SKILL.md 탐색 경로}
**태스크 폴더**: {tasks/{NNN}-{name}/}
**이전 산출물**: {TASK.md 경로}, {ANALYSIS.md 경로}
**프로젝트 컨텍스트**: {docs/PROJECT.md + 매칭 참조 문서. 미존재 시 CLAUDE.md 폴백}
**산출물 저장 경로**: {PLAN.md 경로}, {execution-plan.json 경로 (FE/BE 시)}
**하네스 Guards**: PLAN.md에 없는 파일 생성/수정 금지. PLAN 설계를 임의 변경 금지. 블로커 발생 시 즉시 중단 후 보고.
**참조 문서**: {docs/PROJECT.md 문서 테이블 기반 관련 문서 경로}
```
**model**: advanced

워커 완료 → **QA Gate** (op-dev-qa) → **PM Gate** (TASK.md 요구사항 체크박스 갱신 포함 — 하네스 §3 참조).

### TEST-SCENARIO 스킵 조건
작업 유형이 **문서 전용**(.md 파일만 수정, 소스 코드 없음)인 경우:
- TEST-SCENARIO 디스패치를 **스킵**, "TEST-SCENARIO: 문서 전용 작업으로 스킵" 표기
- **판별**: PLAN.md 파일 변경 계획에 `.ts/.js/.py/.go/.java/.kt/.rs` 등이 없으면 문서 전용

### 3-2. TEST-SCENARIO 디스패치 (연속)
QA + PM Gate 통과 후 연속 디스패치한다.
```
[WORKER]
op-dev-test-scenario 스킬을 수행하라.
**스킬 경로**: {op-dev-test-scenario/SKILL.md 탐색 경로}
**태스크 폴더**: {tasks/{NNN}-{name}/}
**이전 산출물**: {TASK.md 경로}, {PLAN.md 경로}
**프로젝트 컨텍스트**: {docs/PROJECT.md + 매칭 참조 문서. 미존재 시 CLAUDE.md 폴백}
**산출물 저장 경로**: {TEST-SCENARIO.md 경로}
**하네스 Guards**: PLAN.md에 없는 파일 생성/수정 금지. PLAN 설계를 임의 변경 금지. 블로커 발생 시 즉시 중단 후 보고.
**참조 문서**: {docs/PROJECT.md 문서 테이블 기반 관련 문서 경로}
```
**model**: light

두 워커 완료 → 사용자에게 PLAN + TEST-SCENARIO 함께 보고. **승인 = EXECUTE 시작 허가**.

## STEP 4: EXECUTE
워커를 디스패치하여 코드를 작성한다.

**디스패치 프롬프트**:
```
[WORKER]
op-dev-execute 스킬을 수행하라.
**스킬 경로**: {op-dev-execute/SKILL.md 탐색 경로}
**태스크 폴더**: {tasks/{NNN}-{name}/}
**checklist_source**: {PLAN.md 경로}, 섹션: 3. 실행 체크리스트
**execution-plan.json**: {경로 (있으면)}
**프로젝트 컨텍스트**: {docs/PROJECT.md + 매칭 참조 문서. 미존재 시 CLAUDE.md 폴백}
**하네스 Guards**: PLAN.md에 없는 파일 생성/수정 금지. PLAN 설계를 임의 변경 금지. 블로커 발생 시 즉시 중단 후 보고.
**참조 문서**: {docs/PROJECT.md 문서 테이블 기반 관련 문서 경로}
```
**model**: standard

### FE/BE 병렬 (execution-plan.json 존재 시)
1. Phase 1: Common → 단일 워커 순차
2. Phase 2: FE + BE 워커 병렬
3. Phase 3: 양쪽 완료 후 통합

### EXECUTE 완료 후
워커가 changed_files를 반환하면:
1. **op-dev-test-agent 워커 호출** → TEST-SCENARIO.md에 결과 채움 + 판정
2. **PM Gate** — TEST-SCENARIO 결과 검토 + QA 체크리스트 갱신 (공통 하네스 §2 "QA 체크리스트 검증" 참조)
3. **DONE.md 생성** (checkpoint-guide.md 참조)
4. 사용자에게 완료 보고

## STATE.md 도메인 설정
- 모드: Full Task
- 단계: TASK / ANALYSIS / PLAN+TEST-SCENARIO / EXECUTE
- 산출물: TASK.md, ANALYSIS.md, PLAN.md, TEST-SCENARIO.md, QA-*.md, DONE.md

## Agentic Mode

opal-harness-agentic.md 참조. `--agentic` 플래그 활성화 시 이 스킬의 차이점만 기술한다.

### 활성화

`//opd --agentic {작업 설명}` 형식으로 호출. STATE.md 모드 필드를 `agentic`으로 기록한다.

### 자율 게이트 흐름

```
TASK (PM 직접) → ANALYSIS Gate → PLAN+TEST-SCENARIO Gate → EXECUTE Gate
                   PM 자율 검토      PM 자율 검토              PM 자율 검토
```

- TASK 이후 3개 게이트를 PM이 자율 통과
- EXECUTE 진입 = PM이 대행 승인 (구현 금지 원칙의 "실행 허가"를 PM이 판단)
- 각 게이트에서 opal-harness-agentic.md "Gate 루핑 규칙" 적용
- AGENTIC-LOG.md에 모든 판단/오류/수정/의사결정 기록

## 변경이력
| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-03-26 | 초기 작성 — dev-task-pilot 컴포지션 전환 |
| v1.1 | 2026-03-28 | TEST-SCENARIO를 TODO STEP에 통합, EXECUTE 후 커밋 규칙 추가 |
| v1.2 | 2026-03-28 | TODO를 PLAN에 흡수하여 5→4 STEP, TEST-SCENARIO를 PLAN STEP에 통합, TEST-SCENARIO 스킵 조건 추가 |
| v1.3 | 2026-03-28 | Harness 참조 전환으로 슬림화 (265→105줄) |
| v1.4 | 2026-03-29 | 컴포넌트 리네이밍 (042) |
| v1.5 | 2026-03-29 | model override를 레벨 기반으로 전환 (044) |
| v1.6 | 2026-03-31 | Agentic Mode 섹션 추가 (057) |
| v1.7 | 2026-03-31 | §7 참조 → opal-harness-agentic.md 참조 전환. EXECUTE 후 PM Gate + QA 체크리스트 갱신 추가 (058) |
| v1.8 | 2026-04-01 | 전체 워커 디스패치 프롬프트에 `[WORKER]` 마커 + 하네스 Guards + 참조 문서 주입 지침 추가 (063) |
| v1.9 | 2026-04-02 | PLAN PM Gate에 TASK.md 체크박스 갱신 명시 (072) |
