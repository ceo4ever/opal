# DONE: opal-harness.md 구조화 리팩토링

> 완료일: 2026-04-12 | 태스크: 110 | 스킬: opp

## 작업 요약

`opal-harness.md` §3 State의 비대화를 해소하여, 도메인 특화 내용 제거 · 레거시 정리 · 중복 제거를 수행했다.

## 변경 파일

| # | 파일 | 변경 내용 |
|---|------|----------|
| 1 | `opal/core/references/opal-harness.md` | R-1: opsdd 파이프라인 현황판 예시 제거 (~40줄), R-2: 병렬 실행 State 제거 (~55줄), R-3: State Gate 자가 점검 프롬프트 deprecated 상태값 갱신, R-5: 변경이력 v3.7 추가 |
| 2 | `opal/core/references/opal-harness-interactive.md` | R-4: §4 순서 강제 원칙 → 공통 하네스 §3 참조로 교체 (운용 테이블 유지), R-5: 변경이력 v2.3 추가 |
| 3 | `opal/skills/opal-pilot-project-dev/SKILL.md` | R-2 후속: 하네스 병렬 실행 State 참조 → parallel-execution-guide.md §7 자체 참조로 갱신 |
| 4 | `opal/skills/opal-pilot-project-dev/references/parallel-execution-guide.md` | R-2 후속: 하네스 참조 2곳 → 자체 참조(§7-2, §7-3)로 갱신 |

## 효과

- opal-harness.md에서 ~95줄 제거 (opsdd 예시 40줄 + 병렬 실행 State 55줄)
- State Gate 자가 점검 프롬프트가 현행 파이프라인 현황판 운용과 정합
- 수행 순서 강제 원칙의 SSOT를 공통 하네스 §3으로 일원화
- §번호(§0~§9) 미변경으로 62개 외부 참조 영향 없음

## QA 결과

- QA-PLAN.md: Pass (Info 1건)
- QA-EXECUTE.md: Pass (13/13 항목 통과, 지적 0건)
