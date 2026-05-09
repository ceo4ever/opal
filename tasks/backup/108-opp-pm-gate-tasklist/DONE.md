---
task_id: "108"
status: DONE
completed_at: 2026-04-11 13:59
---

# DONE: PM Gate 점검 목록 — TASK.md 요구사항 추가

## 완료 내용

### 수정 파일 (6개)

| 파일 | Phase | 버전 |
|------|-------|------|
| `opal/skills/opal-pilot-project/SKILL.md` | PLAN | v2.3 → v2.4 |
| `opal/skills/opal-pilot-dev/SKILL.md` | PLAN+TEST-SCENARIO | v2.7 → v2.8 |
| `opal/skills/opal-pilot-dev-short/SKILL.md` | PLAN+TEST-SCENARIO | v2.7 → v2.8 |
| `opal/skills/opal-pilot-write-tech/SKILL.md` | PLAN | v2.8 → v2.9 |
| `opal/skills/opal-pilot-sdd/SKILL.md` | SPEC | v2.6.0 → v2.7.0 |
| `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | WIREFRAME | v1.9 → v2.0 |

### 변경 사항

각 파일 `## PM Gate 점검 목록` 테이블의 PLAN-equivalent Phase 행:
- **산출물 컬럼**: `TASK.md, ` 맨 앞에 추가
- **체크리스트 위치 컬럼**: `TASK.md 요구사항, ` 맨 앞에 추가 (기존 `-`인 경우 교체)

## 설계 근거

PM Gate 자가 진단 절차(harness-interactive §3 Step 2)가 SKILL.md PM Gate 점검 목록을 읽어 산출물·체크리스트 위치를 파악한다.
점검 목록에 TASK.md가 없으면 TASK.md 요구사항 체크리스트가 자가 진단 흐름에 포함되지 않는다.
107 태스크에서 이 구조 결함으로 PLAN Gate 시 TASK.md 요구사항 대조가 누락된 사례 확인 → 모든 파일럿 스킬에 일괄 적용.
