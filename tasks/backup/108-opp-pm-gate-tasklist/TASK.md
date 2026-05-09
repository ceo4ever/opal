---
task_id: "108"
name: PM Gate 점검 목록 — TASK.md 요구사항 추가
skill: opp
status: TASK
created_at: 2026-04-11
---

# TASK: PM Gate 점검 목록 — TASK.md 요구사항 추가

## 배경

107 태스크 사후 분석에서 발견된 이슈:
PLAN PM Gate 자가 진단 절차(opal-harness-interactive §3)의 Step 2는 각 SKILL.md의 `PM Gate 점검 목록`을 읽어 산출물·체크리스트 위치를 파악한다.
그런데 현재 모든 파일럿 스킬의 PM Gate 점검 목록에 TASK.md가 포함되어 있지 않다.
결과적으로 PM Gate 자가 진단이 TASK.md 요구사항 체크리스트를 확인하지 않고 통과된다.

하네스 interactive §3 "체크리스트 갱신 상태 확인" 절에는 "PLAN PM Gate 시 TASK.md 요구사항 체크박스 갱신 상태를 확인한다"가 명시되어 있으나,
자가 진단 5단계 흐름에서 SKILL.md 점검 목록 경로를 통해 자연스럽게 트리거되지 않는 구조 결함이다.

## 작업 범위

### 수정 대상 (6개 파일)

| 파일 | Phase | 현재 | 변경 후 |
|------|-------|------|--------|
| `opal/skills/opal-pilot-project/SKILL.md` | PLAN | PLAN.md, QA-PLAN.md | TASK.md, PLAN.md, QA-PLAN.md |
| `opal/skills/opal-pilot-dev/SKILL.md` | PLAN+TEST-SCENARIO | PLAN.md, TEST-SCENARIO.md, QA-PLAN.md | TASK.md, PLAN.md, TEST-SCENARIO.md, QA-PLAN.md |
| `opal/skills/opal-pilot-dev-short/SKILL.md` | PLAN+TEST-SCENARIO | PLAN.md, TEST-SCENARIO.md, QA-PLAN.md | TASK.md, PLAN.md, TEST-SCENARIO.md, QA-PLAN.md |
| `opal/skills/opal-pilot-write-tech/SKILL.md` | PLAN | PLAN.md, QA-PLAN.md | TASK.md, PLAN.md, QA-PLAN.md |
| `opal/skills/opal-pilot-sdd/SKILL.md` | SPEC | SPEC.md, QA-SPEC.md | TASK.md, SPEC.md, QA-SPEC.md |
| `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | WIREFRAME | wireframe.md, QA-WIREFRAME.md | TASK.md, wireframe.md, QA-WIREFRAME.md |

### 변경 내용 (각 파일 동일 패턴)

PM Gate 점검 목록 테이블의 해당 Phase 행:
- **산출물 컬럼**: `TASK.md` 맨 앞에 추가
- **체크리스트 위치 컬럼**: `TASK.md 요구사항,` 맨 앞에 추가 (기존 값 유지)

예시 (opp):
```
| PLAN | TASK.md, PLAN.md, QA-PLAN.md | TASK.md 요구사항, PLAN.md §3, §4 |
```

### 변경이력 추가

각 파일에 버전 행 추가 (버전은 각 파일의 현재 최신 버전 + 0.1):
```
| {버전} | 2026-04-11 | PM Gate 점검 목록 — PLAN-equivalent Phase에 TASK.md 요구사항 추가 (108) |
```

## 요구사항

- [x] opal-pilot-project SKILL.md — PLAN Phase 점검 목록에 TASK.md 추가
- [x] opal-pilot-dev SKILL.md — PLAN+TEST-SCENARIO Phase 점검 목록에 TASK.md 추가
- [x] opal-pilot-dev-short SKILL.md — PLAN+TEST-SCENARIO Phase 점검 목록에 TASK.md 추가
- [x] opal-pilot-write-tech SKILL.md — PLAN Phase 점검 목록에 TASK.md 추가
- [x] opal-pilot-sdd SKILL.md — SPEC Phase 점검 목록에 TASK.md 추가
- [x] opal-pilot-dev-wireframe SKILL.md — WIREFRAME Phase 점검 목록에 TASK.md 추가
- [x] 각 파일 변경이력 추가

## 범위 외

- opal-harness-interactive.md 변경 없음 (§3 체크리스트 갱신 상태 확인 절에 이미 의도 명시)
- op-task-qa, op-dev-qa SKILL.md 변경 없음
- 파이프라인 흐름 변경 없음 (PM Gate 점검 목록만 수정)
