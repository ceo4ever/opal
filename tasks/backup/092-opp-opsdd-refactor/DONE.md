# DONE: opsdd 스킬 개선 — 폴더 통합 + 단계 경량화

> 완료일: 2026-04-07 | 태스크: 092-opp-opsdd-refactor | 스킬: opp

## 완료 요약

opsdd 스킬의 3가지 문제에 대한 설계 검토 완료. 개선 방향 + 수정 파일 목록 + 구현 체크리스트 확정.

## 핵심 결론

### 1. 폴더 구조 통합
- `specs/` + `tasks/` 혼재 → `tasks/` 단일 루트로 통합
- ACT 실행 단위: `actions/ACT-{NNN}-{name}/`
- ACT 내부 문서: `PLAN.md + TEST.md + DONE.md` (STATE.md 제거 — 상위 STATE.md가 통합 관리)

### 2. EXECUTE-LOOP 재구성
- opds/opd는 독립 오케스트레이터 → 서브 재활용 불가 (op-task 경로 하드코딩)
- 해결: `op-dev-plan + op-dev-execute` 직접 디스패치
- 에이전트 구조: A(plan+execute) → B(qa) → PM(done), 루프 관리는 PM

### 3. 파이프라인 간소화 (7단계 → 5단계)
```
Phase 0: TASK    (PM 직접)
Phase 1: SPEC    (워커: op-sdd-spec)
Phase 2: REVIEW  (PM 직접 — 구조검증 → TEST-SCENARIOS.md 작성 = SPEC 검증)
Phase 3: DESIGN  (워커: op-sdd-plan, op-sdd-tasks 통합)
Phase 4: EXECUTE (ACT 루프 — 에이전트 A/B + 재시도 루프)
Phase 5: DONE    (PM 직접)
```

### 4. 스킬 처리 방향
| 스킬 | 처리 |
|------|------|
| `op-sdd-spec` | 재사용 (경로 수정) |
| `op-sdd-plan` | 수정 (op-sdd-tasks 통합) |
| `op-sdd-tasks` | 삭제 |
| `op-sdd-verify` | 워커 → PM 레퍼런스로 역할 변경 |
| `op-dev-plan` | 재사용 |
| `op-dev-execute` | 재사용 |
| `op-dev-qa` | 재사용 |

## 산출물

- `tasks/092-opp-opsdd-refactor/PLAN.md` — 설계 분석 + 개선 방향 + 구현 체크리스트
