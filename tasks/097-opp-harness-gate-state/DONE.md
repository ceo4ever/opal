# DONE: Harness Gate 상태 관리 개선

> 완료: 2026-04-07 18:20

## 완료 요약

Gate 통과 시 STATE.md 갱신이 한꺼번에 처리되던 문제를 구조적으로 해결했다.

State Gate를 PM Gate 이전 1개에서 각 Gate(QA/Artifact/PM) 직후로 내재화하여, 단계 건너뜀이 구조상 불가능하도록 변경했다. 또한 상태 추적 테이블을 컬럼 기반에서 행 기반 순서 실행 테이블로 전환하여 Gate를 포함한 모든 수행 단계가 행으로 노출된다. Gate Fail 처리도 단일 섹션(§5)으로 통합했다.

## 변경 파일

| 파일 | 변경 내용 |
|------|----------|
| `opal/core/references/opal-harness.md` | §3 이벤트 테이블 Gate 행 추가. STATE.md 템플릿 행 기반으로 교체. 수행 순서 강제 원칙 추가. 레거시 Gate 상태값 deprecated |
| `opal/core/references/opal-harness-interactive.md` | §2/§2.5/§3 각 Gate 완료 즉시 State Gate 내재화. §3 구 State Gate 서브섹션 제거. §5 Gate Fail 공통 처리 신설 |
| `opal/skills/opal-pilot-dev-short/SKILL.md` | PLAN/EXECUTE Gate 순서: QA→State Gate→Artifact→State Gate→PM→State Gate. 진행 현황 행 예시 추가 |
| `opal/skills/opal-pilot-dev/SKILL.md` | ANALYSIS/PLAN/EXECUTE Gate 순서 동일 재배치 |
| `opal/skills/opal-pilot-project/SKILL.md` | PLAN/EXECUTE Gate 순서 재배치. 진행 현황 행 예시 추가 |
| `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | WIREFRAME/EXECUTE Gate 순서 재배치 |
| `opal/skills/opal-pilot-sdd/SKILL.md` | QA Gate 없는 Phase 구조 유지 확인 명시 |
| `opal/skills/opal-pilot-write-tech/SKILL.md` | PLAN/EXECUTE/QA 각 단계 Gate 재배치 |

## 핵심 설계 결정

| # | 결정 | 근거 |
|---|------|------|
| 1 | Gate Fail을 opal-harness-interactive.md §5에 통합 | harness.md §1(검증 루프)와 성격이 달라 분리 |
| 2 | agentic 하네스 제외 | 별도 작업으로 분리 |
| 3 | State Gate를 각 Gate 직후에 내재화 | Gate 1개로는 중간 Gate 묶어서 처리 가능 — 흐름 자체에서 건너뜀 불가하게 구조 변경 |
| 4 | 오케스트레이터 SKILL.md 6개 포함 | 하네스 내재화만으로는 PM이 SKILL.md 읽을 때 흐름이 불명확 |
| 5 | 행 기반 진행 현황 테이블 | 모든 상태 노출 + AI가 위에서 아래로 순서대로 처리하는 하네스 도구 역할 |
