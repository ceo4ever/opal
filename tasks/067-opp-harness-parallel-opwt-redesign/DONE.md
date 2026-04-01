# DONE: 하네스 병렬 처리 원칙 추가 + opwt 재설계

> 완료일: 2026-04-01 | 스킬: opp --agentic

## 완료 내용

### T1. opal-harness.md §7 병렬 처리 원칙 추가

- 읽기(병렬 툴콜)와 실행(병렬 Agent 디스패치) 구분 명시
- 의존관계 있는 작업만 순차 유지 원칙
- 모든 오케스트레이터 자동 상속 (하위 호환성 완전 유지)
- v2.0 → v2.1

### T2. opwt SKILL.md 재설계

- Phase 1-4 → 하네스 표준 단계 (TASK/ANALYSIS/PLAN/EXECUTE/QA)
- TASK 단계 신규 추가: opwt 전용 확인 항목(모드, 문서 유형, 외부 참조, 저장 경로) + TASK.md/STATE.md 생성
- 각 단계(ANALYSIS/PLAN/EXECUTE/QA)에 STATE.md 갱신 지시 명시
- 병렬 처리 원칙 명시 (하네스 §7 참조)
- 핵심 로직 전부 보존: diagnosis.json, 배치 편성, [WORKER] 마커, 외부 참조, 참조 가이드
- v1.6 → v2.0

## 산출물

| 파일 | 변경 |
|------|------|
| `opal/core/references/opal-harness.md` | §7 추가, v2.1 |
| `~/.opal/references/opal-harness.md` | 배포 동기화 |
| `opal/skills/opal-pilot-write-tech/SKILL.md` | 재설계, v2.0 |
| `~/.opal/skills/opal-pilot-write-tech/SKILL.md` | 배포 동기화 |
