# QA: PLAN — opsdd EXECUTE-LOOP 개선 — op-sdd-action-plan + opal-sdd-action-agent 신설

> 검토일: 2026-04-07 | 판정: Pass

## 1. 요약

PLAN.md는 opsdd EXECUTE-LOOP(Phase 4)의 ACT 실행 구조를 개선하기 위해 2개의 신규 파일 생성과 2개의 기존 파일 수정을 계획한다. 핵심은 기존의 `op-dev-plan + op-dev-execute` 이중 디스패치를 SDD 전용 `opal-sdd-action-agent` 단일 디스패치로 교체하는 것이다. 현황 조사(§1)에서 현재 구조의 5가지 문제점을 확인하고, 신규 스킬([A] op-sdd-action-plan)과 에이전트([B] opal-sdd-action-agent)의 상세 설계를 정의하며, 기존 가이드([C][D]) 갱신 범위를 구체적으로 명세하였다. 구현 순서(Step 1→2→3→4)가 의존성을 올바르게 반영하며, 리스크 테이블(§5)에서 에이전트 디렉토리 위치 차이 등 잠재적 문제에 대한 대응 방안도 포함되어 있다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| GP-1 | 즉시 실행 가능성 | Pass | §3 각 Step에 파일 경로·작업 내용·완료 기준·테스트·의존 관계가 모두 명시되어 즉시 실행 가능 |
| GP-2 | 의존성 순서 | Pass | Step 1(op-sdd-action-plan) → Step 2(agent, Step 1 의존) → Step 3(guide, Step 2 의존) → Step 4(SKILL, Step 3 의존). 올바른 순서 |
| GP-3 | TASK 반영 | Pass | TASK.md [A][B][C][D] 요구사항이 PLAN §2 파일 변경 계획 및 §3 체크리스트에 1:1 매핑됨 |
| GP-4 | 파일 목록 완전성 | Pass | TASK.md 범위(신규 2개 + 수정 2개) = PLAN §2(신규 2개 + 수정 2개 + 삭제 0개). 완전 일치 |
| GP-5 | 설계 구체성 | Warning | §2.3 [B] 제목에 "4단계 파이프라인"이라 쓰여 있으나 실제 내용은 6단계(1.ACT폴더생성 2.PLAN 3.EXECUTE 4.VERIFY 5.TEST.md 6.결과반환)로 라벨과 내용 불일치 |
| GP-6 | 체크리스트 커버리지 | Pass | §3 4개 Step이 TASK.md [A][B][C][D]에 정확히 대응. §4 QA 체크리스트가 기능·일관성·문서 품질 항목을 포괄 |

## 3. 지적 사항

### Warning: GP-5 — 파이프라인 단계 수 라벨 불일치

**위치**: PLAN.md §2.3 [B] opal-sdd-action-agent 섹션

**현재 표기**:
```
**4단계 파이프라인** (opal-task-action-agent 6단계에서 QA/TEST-SCENARIO 제거 …):
```

**실제 내용**: 1.ACT 폴더 생성 / 2.PLAN / 3.EXECUTE / 4.VERIFY 루프 / 5.TEST.md 작성 / 6.결과 반환 — 6단계

**영향**: 구현 담당자가 라벨("4단계")을 보고 실제 단계 수와 혼동할 수 있음. 설계 자체는 정확하므로 실행에 치명적 영향은 없으나 수정 권장.

**수정 방향**: "**6단계 파이프라인**"으로 변경하거나, 제거 배경 설명("opal-task-action-agent 6단계에서 QA/TEST-SCENARIO 제거")과 함께 실제 단계 수를 일치시킴.

---

**참고 사항(Info)**:

- TASK.md [B] 파이프라인에 "DONE.md 반환" 표현이 있으나, PLAN에서는 에이전트 내부 단계에 DONE.md를 포함하지 않고 opsdd PM 책임으로 분리하였다. §2.3 [D]의 "Pass → DONE.md 작성 → STATE.md 갱신"에서 PM 책임임이 명확히 정의되어 있어 설계 의도는 일관성 있음. 다만 TASK.md 표현이 오해를 유발할 수 있으므로 참고.

### 심각도 분류
- Critical: 없음
- Warning: GP-5 파이프라인 라벨 불일치 (1건)
- Info: TASK.md "DONE.md 반환" 표현 모호성 (설계 의도는 명확)

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md [A] | op-sdd-action-plan 요구사항(입력·프로세스·산출물) → PLAN §2.3 [A] 상세 설계에 모두 반영 | Pass |
| TASK.md [B] | opal-sdd-action-agent 8개 입력 파라미터 → PLAN §2.3 [B] 입력 명세 테이블에 8개 전부 포함 | Pass |
| TASK.md [B] | VERIFY 루프 opal-task-action-agent §5 참조 → PLAN §2.3 [B] VERIFY 루프 규격에 명시 | Pass |
| TASK.md [C] | execute-loop-guide.md §2-1·§5·§10 갱신 → PLAN §2.3 [C]에 각 섹션별 변경 내용 구체적 명세 | Pass |
| TASK.md [D] | opsdd SKILL.md Phase 4 갱신(사용자 Gate + 에이전트 변경) → PLAN §2.3 [D]에 반영 | Pass |
| TASK.md 제약 | `opal/agents/` 위치 vs 기존 `agents/` 위치 불일치 리스크 → PLAN §5 리스크 테이블에서 인지 및 대응 방안 명시 | Pass |
| TASK.md 제약 | §4 병렬 실행 · §6 재시도 루프 유지 → PLAN §2.3 [C] "유지 항목"에 명시 | Pass |
| execute-loop-guide.md (현황) | 현재 §2-1이 "op-dev-plan 디스패치 → PM Gate → op-dev-execute" 구조임을 §1 현황 조사에서 정확히 파악 | Pass |

## 5. 판정

**Pass**

모든 TASK.md 요구사항([A][B][C][D])이 PLAN에 반영되었고, 의존성 순서·파일 목록·실행 체크리스트가 충분히 구체적이다. Warning 1건(파이프라인 단계 수 라벨 불일치)은 설계 내용 자체에는 영향이 없으며 라벨 수정으로 간단히 해결 가능하므로, 이대로 EXECUTE 단계 진행이 가능하다.
