# DONE: PM Gate 자가 진단 통합 + Artifact Gate 제거

> 태스크: 106 — opp-pm-gate-self-diagnosis
> 완료일: 2026-04-10

## 완료 요약

Artifact Gate(§2.5)를 제거하고, PM Gate에 5단계 자가 진단 절차를 통합했다.
R-4로 STATE.md `진행 현황` 섹션을 `파이프라인 현황판`으로 이름 변경했다.

## 변경 파일

| 파일 | 변경 내용 |
|------|----------|
| `opal/core/references/opal-harness-interactive.md` | §2.5 Artifact Gate 제거 + §3 PM Gate 자가 진단 5단계 추가 + §4 체크리스트 검증 게이트 제거 → v2.2 |
| `opal/core/references/opal-harness.md` | Artifact Gate 이벤트 행 제거 + 파이프라인 현황판 이름 변경 + STATE.md 템플릿 헤더 변경 → v3.5 |
| `opal/skills/opal-pilot-project/SKILL.md` | Artifact Gate 제거 + PM Gate 점검 목록 추가 + 파이프라인 현황판 이름 변경 → v2.3 |
| `opal/skills/opal-pilot-dev/SKILL.md` | Artifact Gate 제거 + PM Gate 점검 목록 추가 + 파이프라인 현황판 이름 변경 → v2.7 |
| `opal/skills/opal-pilot-dev-short/SKILL.md` | Artifact Gate 제거 + PM Gate 점검 목록 추가 + 파이프라인 현황판 이름 변경 → v2.7 |
| `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | Artifact Gate 제거 + PM Gate 점검 목록 추가 + 파이프라인 현황판 이름 변경 → v1.9 |
| `opal/skills/opal-pilot-write-tech/SKILL.md` | Artifact Gate 제거 + PM Gate 점검 목록 추가 → v2.8 |
| `opal/skills/opal-pilot-sdd/SKILL.md` | Artifact Gate 제거 + PM Gate 점검 목록 추가 + 파이프라인 현황판 이름 변경 → v2.6.0 |

## 핵심 설계 변경

### Before
```
QA Gate → State Gate → Artifact Gate → State Gate → PM Gate → State Gate → 사용자 확인
```

### After
```
QA Gate → State Gate → PM Gate (자가 진단 포함) → State Gate → 사용자 확인
```

### PM Gate 자가 진단 (harness-interactive.md §3)
1. STATE.md Read → 현재 Phase 파악
2. SKILL.md `## PM Gate 점검 목록` 섹션 Read → Phase별 산출물·체크리스트 위치 확인
3. 각 산출물 Read → 존재 여부 + 내용 확인
4. 체크리스트 `[ ]` 발견 시 내용 기반 판단 → 완료면 `[x]` 갱신, 미완료면 목록 추가
5. 판정: 미완료 없음 → PM 검토 기준 진행 / 있음 → 사용자 보고
