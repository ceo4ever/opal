---
@header
type: done
task: "115 PLAN 워커 TEST-SCENARIO 통합 + QA Gate 제거 + PM Gate 검증 강화"
layer: task
---

# DONE: 115 plan-ts-merge-pm-gate

> 완료일: 2026-04-13 | 소요 단계: TASK → PLAN → EXECUTE

## 완료 요약

`opal-pilot-dev` / `opal-pilot-dev-short`의 PLAN + EXECUTE/TEST 단계 전체에서 QA Gate를 제거하고, PM Gate가 직접 산출물을 Read·검증하는 방식으로 파이프라인을 슬림화했다.

## 변경 파일

| 파일 | 버전 | 핵심 변경 |
|------|------|----------|
| `opal/skills/op-dev-plan/SKILL.md` | v2.0 → v2.1 | Step 10 TEST-SCENARIO.md 작성 추가, Step 11 결과 반환 갱신, 보장 출력에 TEST-SCENARIO.md 포함 |
| `opal/skills/opal-pilot-dev/SKILL.md` | v2.8 → v2.9 | STEP 3 TEST-SCENARIO 별도 디스패치 제거 + QA Gate 제거 + PM Gate 강화. STEP 5 TEST QA Gate 제거 + PM Gate 강화. STATE.md 행 예시 31→24행 |
| `opal/skills/opal-pilot-dev-short/SKILL.md` | v2.8 → v2.9 | STEP 2 TEST-SCENARIO 별도 디스패치 제거 + QA Gate 제거 + PM Gate 강화. STEP 4 TEST QA Gate 제거 + PM Gate 강화. STATE.md 행 예시 25→18행 |

## 파이프라인 변화

| 파일럿 | 변경 전 | 변경 후 |
|--------|---------|---------|
| opd STATE.md 행 수 | 31행 | 24행 (-7) |
| opds STATE.md 행 수 | 25행 | 18행 (-7) |
| PLAN 단계 워커 디스패치 | PLAN → TEST-SCENARIO → QA (3회) | PLAN 1회 (통합) |
| TEST 단계 워커 디스패치 | TEST → QA (2회) | TEST 1회 |

## 적용된 요구사항

- R-1: op-dev-plan Step 10 신설, 보장 출력 갱신 ✅
- R-2: opal-pilot-dev PLAN 단계 슬림화 ✅
- R-3: opal-pilot-dev STATE.md 행 예시 갱신 ✅
- R-4: opal-pilot-dev-short PLAN 단계 슬림화 ✅
- R-5: opal-pilot-dev-short STATE.md 행 예시 갱신 ✅
- R-6: opal-pilot-dev EXECUTE/TEST 단계 슬림화 ✅
- R-7: opal-pilot-dev-short EXECUTE/TEST 단계 슬림화 ✅
