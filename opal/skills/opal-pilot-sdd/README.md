# opal-pilot-sdd

명세(SPEC.md)를 SSOT로 삼아 검증 → 설계 → 반복 실행 → 검증까지 진행하는 SDD(Spec-Driven Development) 오케스트레이터.

## 개요

- 기능 하나를 단위로 SPEC.md(무엇을 만들 것인가의 단일 진실 소스)를 먼저 확정하고, 그 위에서 아키텍처 설계와 실행 단위(ACT) 분해, 반복 실행, E2E 검증을 진행한다.
- "WHAT 단계"(SPEC 작성 → 검증 → 테스트 기준 확정)와 "HOW 단계"(설계 → 구현 → 검증)를 명확히 분리한다. WHAT이 끝나기 전에는 설계를 시작하지 않는다.
- SPEC 검증(REVIEW)은 SPEC을 작성한 워커가 아니라 PM이 사용자와 함께 직접 수행해, 작성자가 스스로를 검증하는 self-confirming을 피한다.
- 실행 단위(ACT)는 `opal-sdd-action-agent`에 단일 디스패치되어 PLAN·EXECUTE·검증까지 자율로 완주한다.

## 언제 쓰나

기능 하나를 명세부터 확정하고 여러 실행 단위(ACT)로 쪼개 진행해야 하는, 상대적으로 규모가 있는 개발 작업에 사용한다.

| 상황 | 사용할 스킬 |
|---|---|
| 명세를 먼저 확정하고 여러 ACT로 나눠 진행할 기능 개발 | `opal-pilot-sdd`(opsdd) |
| 단일 태스크 규모의 개발 | `opal-pilot-dev-short`(opds) 또는 `opal-pilot-dev`(opd) |
| 범용 작업 | `opal-pilot-project`(opp) |

## 사용법

```
//opsdd {기능 설명}
```

`docs/PROJECT.md`가 없는 프로젝트에서 호출하면 프로젝트 초기화(opi)를 먼저 실행한 뒤 복귀한다.

모드 플래그:

| 호출 | 모드 |
|---|---|
| `//opsdd 기능 설명` | semi-agentic (기본) — DESIGN까지 사용자 검토, EXECUTE-LOOP부터 PM 자율 |
| `//opsdd --interactive 기능 설명` | interactive — 모든 단계 사용자 승인 |
| `//opsdd --agentic 기능 설명` | agentic — 모든 단계 PM 자율 (CLOSE 진입 제외) |

어떤 모드라도 **CLOSE 진입은 항상 사용자 승인이 필요**하다.

## 파이프라인

```
TASK → SPEC → REVIEW → DESIGN → EXECUTE-LOOP → VERIFY → CLOSE
```

- **TASK**: 기능명(`feature`)을 포함한 메타데이터를 정리한다. 이후 모든 산출물은 `tasks/{NNN}-{feature}/` 아래 단일 루트에 저장된다.
- **SPEC**: 워커가 기능 명세(SPEC.md — FR/NFR/제약조건)를 작성한다.
- **REVIEW**: PM이 SPEC.md 구조를 직접 검증하고, SPEC의 각 기능 요구사항(FR)에서 수용 기준(AC)과 테스트 시나리오(TS)를 도출해 TEST-SCENARIOS.md를 작성한다. 이어서 `op-scenario-gate`(커버리지 체크 + 독립 evaluator)로 커버리지를 검증한다. 구조 검증 실패나 게이트 에스컬레이션 시 SPEC 단계로 되돌아간다.
- **DESIGN**: 워커가 SPEC.md와 TEST-SCENARIOS.md를 근거로 아키텍처 설계와 ACT(실행 단위) 분해를 담은 SPEC-PLAN.md를 작성한다.
- **EXECUTE-LOOP**: SPEC-PLAN.md의 의존 순서에 따라 ACT를 하나씩(또는 의존관계가 없으면 워크트리로 병렬) 실행한다. 각 ACT는 `opal-sdd-action-agent`에 단일 디스패치되어 PLAN → EXECUTE → 검증까지 자율로 완주하며, 실패 시 최대 3회 재시도한다. PM은 ACT 완료마다 L1(lint/type check)·L2(빌드)를 직접 검증한다.
- **VERIFY**: PM이 TEST-SCENARIOS.md의 모든 시나리오를 `test-tool` E2E로 직접 검증하고 추적 매트릭스를 갱신한다. 전체 시나리오가 Green이어야 CLOSE 진입 게이트를 통과한다.
- **CLOSE**: 전체 ACT의 DONE.md 존재와 TS Green을 확인한 뒤 DONE.md를 생성하고, 관련 문서 동기화와 brain ingest를 수행한다.

## 산출물

- `TASK.md`, `SPEC.md`, `TEST-SCENARIOS.md`, `SPEC-PLAN.md`, `STATE.md`, `DONE.md`
- `actions/ACT-{NNN}-{name}/`마다 `PLAN.md`, `TEST.md`, `DONE.md`

## 관련 스킬

- `op-sdd-spec` — SPEC 단계 워커 (기능 명세 작성)
- `op-sdd-plan` — DESIGN 단계 워커 (아키텍처 설계 + ACT 분해)
- `op-scenario-gate` — REVIEW 단계의 목표-커버 게이트 판정
- `opal-sdd-action-agent` — EXECUTE-LOOP 단계에서 ACT 단위로 자율 실행되는 워커
- `op-brain-ingest` — CLOSE 단계에서 산출물을 프로젝트 brain에 누적 (brain 사용 프로젝트 한정)

## FAQ

### SPEC 검증은 왜 SPEC을 쓴 워커가 하지 않나요?
작성자가 스스로를 검증하면 self-confirming이 되어 빈틈을 놓치기 쉽다. 그래서 REVIEW는 PM이 사용자와 함께 직접 수행하고, 테스트 시나리오 커버리지는 독립된 `op-scenario-gate` 평가자가 별도로 판정한다.

### ACT는 어떻게 나뉘고 실행되나요?
DESIGN 단계에서 SPEC-PLAN.md에 ACT 분해와 의존관계가 정해진다. EXECUTE-LOOP에서 의존관계가 없는 ACT는 워크트리로 격리해 병렬 실행하고, 의존관계가 있으면 순서대로 실행한다.

### DESIGN이 끝나기 전에 구현을 시작할 수 있나요?
아니다. WHAT 단계(SPEC/REVIEW)에서 무엇을 만들지와 판정 기준이 완전히 확정된 뒤에만 HOW 단계(DESIGN/EXECUTE-LOOP)로 넘어간다.
