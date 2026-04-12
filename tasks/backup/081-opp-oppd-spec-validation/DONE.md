# DONE: oppd PRD+TRD SDD 기반 명세 검증 단계 추가

> 완료일: 2026-04-03 | 태스크: 081

## 변경 파일

| 파일 | 변경 내용 |
|------|----------|
| `opal/skills/opal-pilot-write-tech/references/network-guide.md` | 7-3 신규 프롬프트 수행 작업 2번에 PRD(6섹션) + TRD(5섹션) 필수 명세 표 추가 |
| `opal/skills/opal-pilot-project-dev/SKILL.md` | Phase 1에 "1-1b. SDD 명세 검증 (PM 직접 수행)" 삽입 (1-1과 1-2 사이) |

## oppd Phase 1 새 흐름

```
1-1. opwt 호출 (PRD+TRD 작성 + 정합성 검증)
1-1b. SDD 명세 검증 (PM 직접 수행) ← 신규
  ├─ PRD 체크리스트 P1~P6 (Non-goals, 타깃유저, Must분류, AC, 모호표현, OQ)
  ├─ TRD 체크리스트 T1~T5 (버전, 성능수치, 보안, PRD커버리지, OQ)
  ├─ Fail 시 opwt 수정 모드 재호출 (최대 2회)
  └─ 2회 Fail → 사용자 에스컬레이션
1-2. 사용자 확정
1-3. 후속 조치
```

## 향후 개선 후보

- 검증 전용 에이전트 분리 (PM 컨텍스트 절약 + opsdd 재사용) — 별도 태스크 예정
