# GC CONVENTION FINAL RECHECK — 20260926T091900Z

## 1. 헤더

- 실행 완료: 2026-09-26 09:40:52 UTC
- 범위: 이전 재검사 25개 파일 + 신규 `evidence/GREEN.md`, 총 26개
- 기준 문서: `docs/CONVENTIONS.md`
- 실행 설정: `.opal/code-scan.json`
- baseline: `evidence/gc-findings-convention-20260926T091900Z-recheck.json`
- APPLY 수행 여부: N — read-only 최종 재검사

## 2. 최종 판정

**PASS_WITH_ADVISORIES** — 잔여 blocking finding은 0건이다.

| 지표 | 값 |
|---|---:|
| 검사 실행 상태 | `pass` |
| Blocking | 0 |
| Advisory | 1 |
| Informational | 1 |
| 직전 재검사 대비 resolved | 1 |
| persisting | 2 |
| missing capabilities | 0 |

## 3. 마지막 blocking 해소 확인

직전 GC-013은 해소됐다.

- `evidence/GREEN.md:15-28`에 세 공개 검증 명령과 실제 결과가 있다.
  - 신규 경계: `27 passed in 6.36s`
  - OPPB runtime 전체: `151 passed, 13 subtests passed in 203.13s`
  - OPPL/opal-agent 비영향: `18 passed in 3.90s`
- `TASK.md:131-133`이 `evidence/GREEN.md`와 표준 run-log sequence 11을 직접 인용한다.
- run-log sequence 11의 요약 수치가 `27 / 151+13 / 18`로 GREEN과 일치하고, `refs`가 같은 `evidence/GREEN.md`를 가리킨다.

따라서 최종 전체 회귀 수치는 독립 평가자가 원증거와 대조할 수 있다.

## 4. 잔여 비차단 finding

### Advisory

- GC-011 — `docs/proposals/opal-oppb-project-build-pilot.md:3`의 상태 `초안`은 허용 proposal 상태 어휘 밖이다. 이번 변경 이전부터 존재한 선행 결손이므로 task 158 차단에는 포함하지 않았다.

### Informational

- GC-012 — `opal/tools/oppb-runtime-tool/tests/test_product_flow.py:7`의 `@header.migration_note`에 대해 code-scan이 선행 `header_history` 비차단 경고를 반환한다.

## 5. 최종 검사 증거

- `git diff --check` — exit 0.
- Ruff 14개 Python 대상 — `All checks passed!`.
- `py_compile` 14개 Python 대상 — exit 0.
- `oppb-state.schema.json` JSON 파싱 — exit 0.
- `code-scan validate` — exit 0, `newly_uncovered=0`, `pre_existing=8`, `header_history=1`.
- `999-oppb-fixture` 잔존 0건, 정식 `999-260926-oppb-fixture` 10건.
- GREEN/TASK/run-log sequence 11 수치·경로 교차 대조 일치.

## 6. 결론

task 158 변경에서 새로 발생한 컨벤션 차단은 모두 해소됐다. 선행 advisory 1건과 informational 1건은 후속 정리 대상이지만 현재 구현 완료를 막지 않는다.
