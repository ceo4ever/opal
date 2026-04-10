---
task_id: "107"
name: opd ANALYSIS Gate 슬림화 + PLAN QA 범위 확대
skill: opp
status: TASK
created_at: 2026-04-10
---

# TASK: opd ANALYSIS Gate 슬림화 + PLAN QA 범위 확대

## 배경

opd(Full Task) 파이프라인의 ANALYSIS 단계에 QA Gate·PM Gate가 붙어 있어 과도하게 무거움.
ANALYSIS.md는 탐색 결과 중간 산출물이므로, PLAN이 나오기 전에 QA하는 것은 의미가 없음.
반면 PLAN QA는 ANALYSIS.md가 PLAN에 제대로 반영됐는지를 검증해야 하는데 현재 범위에서 ANALYSIS.md가 빠져 있음.

## 작업 범위

### 수정 대상

- `opal/skills/opal-pilot-dev/SKILL.md` — STEP 2 ANALYSIS Gate 재설계 + STEP 3 PLAN QA 범위 확대 + STATE.md 예시 갱신

### 변경 내용

#### STEP 2 ANALYSIS (간소화)

**현재**:
```
워커 완료
  → QA Gate (op-dev-qa) → State Gate
  → Artifact Gate → State Gate
  → PM Gate (종합 검토) → State Gate → 사용자 보고
```

**변경 후**:
```
워커 완료
  → State Gate
  → Artifact Gate (ANALYSIS.md 존재 확인)
  → 사용자 보고 (방향 검토 후 PLAN 진입 승인)
```

#### STEP 3 PLAN QA (범위 확대)

**현재**: QA Gate — PLAN.md + TEST-SCENARIO.md 동시 검토

**변경 후**: QA Gate — **ANALYSIS.md + PLAN.md + TEST-SCENARIO.md** 통합 검토
- QA 산출물명: `QA-PLAN.md` 유지 (범위만 확대, 파일명 변경 없음)

#### STATE.md 진행 현황 행 예시 (갱신)

- ANALYSIS 행 수: 10행 → 5행으로 축소
  - 제거: QA Gate, QA-ANALYSIS.md 생성, 중복 State Gate 3개, PM Gate
  - 유지: 작업, ANALYSIS.md 생성, State Gate, Artifact Gate, 사용자 확인
- 전체 행 수: 37행 → 32행으로 축소

## 요구사항

- [ ] ANALYSIS 단계에서 QA Gate, QA-ANALYSIS.md, PM Gate 제거
- [ ] ANALYSIS 단계 완료 후 State Gate → Artifact Gate → 사용자 보고 순서 유지
- [ ] PLAN QA 검토 범위에 ANALYSIS.md 추가 명시
- [ ] STATE.md 행 예시 갱신 (행 번호 재정렬 포함)
- [ ] 변경이력 추가 (v2.6 다음 버전)

## 범위 외

- opds SKILL.md 변경 없음 (구조 이미 올바름)
- op-dev-qa SKILL.md 변경 없음 (QA 내용 자체는 그대로, 범위만 호출 시 지시)
- STATE.md 하네스 참조 구조 변경 없음
