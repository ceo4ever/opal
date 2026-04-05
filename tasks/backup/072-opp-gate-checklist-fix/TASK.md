# TASK: 오케스트레이터 게이트 점검 — TASK.md 체크박스 갱신 + 누락 게이트 보완

> 작성일: 2026-04-02 | 작업 유형: 개선 | 적용 스킬: opp
> 입력: 캡틴 피드백 (071 태스크 운용 중 TASK.md 체크박스 미갱신 발견 → 전체 오케스트레이터 게이트 점검)
> 출력: opal-harness-interactive.md 수정, opd/opds/opp/opdw/opwt SKILL.md 수정

## 작업 목표

오케스트레이터 게이트 구조의 두 가지 문제를 수정한다:

1. **TASK.md 체크박스 갱신 시점 정의 부재** — 하네스와 모든 스킬에 공통으로 누락. 정확한 시점은 PLAN PM Gate (PLAN이 TASK.md 요구사항을 커버했는지 확인하는 시점).
2. **opdw, opwt 스킬의 게이트 누락** — 발견된 구체적 항목 보완.

## 배경

071 태스크 완료 후 캡틴이 TASK.md 체크박스가 갱신되지 않았음을 지적. 원인 분석:

- TASK.md 체크박스의 역할: 요구사항이 PLAN.md에 반영됐는지 확인하는 용도
- 갱신 시점: PLAN PM Gate (PLAN 검토 시 TASK.md → PLAN.md 커버리지 확인 후 갱신)
- EXECUTE 이후 갱신은 타이밍이 틀림 — 실행 완료 후 계획을 소급 검토하는 셈
- 하네스에 이 원칙이 없으니 모든 스킬이 빠뜨리는 구조적 문제

전체 오케스트레이터 게이트 점검에서 추가로 발견된 누락:

- **opdw**: 서브 하네스 로딩 `[MUST]` 지시 누락, WIREFRAME/EXECUTE PM Gate 누락
- **opwt**: ANALYSIS 단계 완료 후 단계 게이트 누락, PLAN/EXECUTE(배치별) QA Gate 누락

## 요구사항

### O1. 하네스에 TASK.md 체크박스 갱신 원칙 추가

**opal-harness-interactive.md**
- [x] §2 QA Gate 또는 §3 PM Gate 하위에 "TASK.md 체크박스 갱신" 항목 추가
  - 갱신 시점: PLAN 단계 PM Gate
  - 갱신 내용: PLAN.md가 TASK.md 요구사항을 커버했는지 확인 후 해당 항목 `[x]`
  - 모든 오케스트레이터에 공통 적용

### O2. 각 스킬의 PLAN PM Gate에 TASK.md 갱신 명시

**opd, opds, opp SKILL.md**
- [x] PLAN 완료 후 PM Gate 서술에 "TASK.md 요구사항 체크박스 갱신" 단계 추가

### O3. opdw 누락 게이트 보완

**opal-pilot-dev-wireframe/SKILL.md**
- [x] Harness 섹션에 서브 하네스 로딩 `[MUST]` 지시 추가
  - `--agentic` 플래그 있음 → `~/.opal/references/opal-harness-agentic.md`
  - `--agentic` 없음 (기본) → `~/.opal/references/opal-harness-interactive.md`
- [x] WIREFRAME 단계 완료 후 PM Gate 추가 (기존 QA Gate 다음)
- [x] EXECUTE 단계 완료 후 PM Gate 추가 (기존 QA Gate 다음)

### O4. opwt 누락 게이트 보완

**opal-pilot-write-tech/SKILL.md**
- [x] ANALYSIS 단계 완료 후 단계 게이트 추가: 사용자 확인 (interactive) / PM 자율 승인 (agentic)
- [x] PLAN 단계 완료 후 QA Gate 추가 (기존 사용자 확인 앞에)
- [x] EXECUTE 배치별 완료 후 QA Gate 추가 (기존 PM 검토 앞에)

## 제약 조건

- O2는 스킬별 디스패치 프롬프트 형식에 맞게 추가 (opd는 서술형, opds/opp는 `[PM 컨텍스트 주입]` 블록 방식)
- O3의 PM Gate는 기존 QA Gate 이후에 위치 (QA → PM 순서 유지)
- O4의 QA Gate는 기존 opwt QA 워커(`references/consistency-rules.md` 기반)가 아닌, 하네스 표준 `op-task-qa` 사용 (opwt는 범용 오케스트레이터에 해당)
- 변경이력 갱신 필수

## 관련 문서

- `opal/core/references/opal-harness-interactive.md` (§2 QA Gate, §3 PM Gate, §4 체크리스트 검증 게이트)
- `opal/skills/opal-pilot-dev/SKILL.md` (STEP 3 PLAN PM Gate)
- `opal/skills/opal-pilot-dev-short/SKILL.md` (STEP 2 PLAN PM Gate)
- `opal/skills/opal-pilot-project/SKILL.md` (STEP 2 PLAN PM Gate)
- `opal/skills/opal-pilot-dev-wireframe/SKILL.md` (Harness, STEP 2 WIREFRAME, STEP 3 EXECUTE)
- `opal/skills/opal-pilot-write-tech/SKILL.md` (ANALYSIS, PLAN, EXECUTE 단계)
