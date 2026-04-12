# TASK: opsdd EXECUTE-LOOP 개선 — op-sdd-action-plan + opal-sdd-action-agent 신설

> 작성일: 2026-04-07 | 스킬: //opp

## 적용 스킬

`opal-pilot-project (opp)` — 신규 파일 생성 + 기존 파일 수정

## 배경

opsdd EXECUTE-LOOP(Phase 4)에서 각 ACT 실행 시 `op-dev-plan` + `op-dev-execute`를 순차 디스패치하는 구조가 다음 문제를 유발한다.

1. **토큰 비효율**: `op-dev-plan`은 opd/opds 범용 스킬로, `plan-guide.md` · `personas` · `community-skills`를 전부 로딩하고 처음부터 설계를 재수행한다. SDD에서는 SPEC-PLAN.md에 아키텍처·ACT 범위가 이미 확정되어 있어 재설계가 불필요하다.

2. **SDD 컨텍스트 단절**: `op-dev-execute`는 PLAN.md 체크리스트만 따르며, SPEC.md·TEST-SCENARIOS.md·AC/TS 매핑을 인식하지 않는다.

3. **자가 검증 루프 없음**: 테스트 실패 시 PM이 수동으로 재지시해야 하며, 에이전트 내 자율 루프(구현 → 테스트 → 수정 → 재테스트)가 없다.

4. **ACT 폴더 생성 타이밍 불명확**: `execute-loop-guide.md §5-1` 디스패치 프롬프트에 폴더 경로는 있으나 "폴더를 생성하고 진행하라"는 명시 지시가 없다. PM이 폴더만 만들고 디스패치하는 혼선 발생.

5. **사용자 Gate 누락**: `execute-loop-guide.md §2-1` 실행 순서에 "ACT 시작 전 사용자 승인" 단계가 없다(Gate 섹션에만 존재).

기존 `opal-task-action-agent`(oppd 전용)는 유사한 자율 루프를 갖추고 있으나 SDD 컨텍스트 입력 구조가 달라 직접 재사용 불가.

## 목표

1. SDD ACT 전용 경량 PLAN 스킬(`op-sdd-action-plan`) 신설
2. SDD ACT 자율 실행 에이전트(`opal-sdd-action-agent`) 신설 — PLAN → EXECUTE → VERIFY 루프 → TEST.md 자가 완주
3. `execute-loop-guide.md` 갱신 — 신규 에이전트 기반 디스패치로 교체 + 누락 항목 보완

## 요구사항

### [A] op-sdd-action-plan 스킬 신설

- [x] `opal/skills/op-sdd-action-plan/SKILL.md` 생성
- [x] 입력: SPEC.md + SPEC-PLAN.md + TEST-SCENARIOS.md + ACT 정의(ID·이름·범위·AC/TS 매핑)
- [x] 프로세스: ACT 범위 기준 경량 코드 분석 → PLAN.md 작성 (재설계 없음, SPEC-PLAN.md 아키텍처 준수)
- [x] plan-guide.md · personas · community-skills 로딩 없음 (또는 최소화)
- [x] 산출물: `actions/ACT-{NNN}-{name}/PLAN.md`

### [B] opal-sdd-action-agent 에이전트 신설

- [x] `opal/agents/opal-sdd-action-agent/AGENT.md` 생성
- [x] 입력: act_id, act_goal, act_scope, ac_mapping, ts_mapping, verify_commands, task_folder, sdd_context(SPEC.md·SPEC-PLAN.md·TEST-SCENARIOS.md 경로)
- [x] 파이프라인: ACT 폴더 생성 → op-sdd-action-plan(PLAN.md) → op-dev-execute(구현) → VERIFY 루프(L1~L3b) → TEST.md 작성 → DONE.md 반환
- [x] VERIFY 루프: `opal-task-action-agent` §5 VERIFY 구조 참조 (L1~L3b, 재시도 한도 준수)
- [x] 사용자와 직접 상호작용 없음 — 결과만 opsdd PM에 반환
- [x] STATE.md 갱신 없음 — opsdd 오케스트레이터 책임

### [C] execute-loop-guide.md 갱신

- [x] `§2-1 단일 ACT 실행 순서` 에 사용자 Gate 단계 추가 (ACT 시작 전)
- [x] `§2-1` op-dev-plan + op-dev-execute 이중 디스패치 → `opal-sdd-action-agent` 단일 디스패치로 교체
- [x] `§5` 디스패치 프롬프트 템플릿 갱신 — 신규 에이전트 입력 명세 반영
- [x] `§10` 전체 흐름 예시 갱신

### [D] opsdd SKILL.md Phase 4 갱신

- [x] Phase 4 EXECUTE-LOOP ACT 실행 순서에 사용자 Gate 명시
- [x] 디스패치 대상을 `opal-sdd-action-agent`로 변경

## 범위

**신규 생성**:
- `opal/skills/op-sdd-action-plan/SKILL.md`
- `opal/agents/opal-sdd-action-agent/AGENT.md`

**수정**:
- `opal/skills/opal-pilot-sdd/references/execute-loop-guide.md`
- `opal/skills/opal-pilot-sdd/SKILL.md`

## 제약

- `~/.opal/` 직접 수정 금지 — 모든 변경은 `opal/` 소스에서 수행
- `opal-task-action-agent` VERIFY 루프 구조(L1~L3b) 재사용 — 중복 정의 최소화
- `op-dev-execute`는 신규 스킬 없이 재사용 (SDD 컨텍스트를 디스패치 시 주입)
- execute-loop-guide.md의 병렬 실행(§4) · 재시도 루프(§6) 구조는 유지
