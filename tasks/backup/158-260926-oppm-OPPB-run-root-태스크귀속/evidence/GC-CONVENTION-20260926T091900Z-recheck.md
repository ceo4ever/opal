# GC CONVENTION RECHECK REPORT — 20260926T091900Z

## 1. 헤더

- 실행 일시: 시작 2026-09-26 09:35:00 UTC / 완료 2026-09-26 09:37:24 UTC / 소요 2분 24초
- 범위: 1차 보고서와 동일한 task 158 관련 파일 25개
- 기준 문서: `docs/CONVENTIONS.md`
- 실행 설정: `.opal/code-scan.json`
- baseline: `evidence/gc-findings-convention-20260926T091900Z.json`
- APPLY 수행 여부: N — read-only 재검사

검사 대상은 1차 보고서 §1의 25개 목록과 동일하며 누락·프로젝트 루트 이탈은 없다.

## 2. 요약

| 지표 | 값 |
|---|---:|
| 재검사 판정 | **FAIL** |
| 검사 실행 상태 | `pass` |
| 현재 finding | 3 |
| Blocking | 1 |
| Advisory | 1 |
| Informational | 1 |
| 1차 대비 resolved | 10 |
| persisting | 3 |

테스트 fixture 10곳은 모두 `999-260926-oppb-fixture`로 바뀌어 태스크 폴더 네이밍 finding이 해소됐다. TASK의 RED·1차 GREEN·brain·code-scan·독립 보고서 경로도 보강됐다. 다만 전체 회귀 수치 한 줄은 연결된 실행 기록과 일치하지 않아 citation 차단 1건이 남는다.

## 3. 잔여 수정 대상

### Medium (1건, blocking)

- [ ] GC-013 [`tasks/158-260926-oppm-OPPB-run-root-태스크귀속/TASK.md:131`] 전체 회귀 수치의 원증거가 없다.
  - 카테고리: 문서화
  - 위반 기준: `docs/CONVENTIONS.md` §Citation Rules
  - 설명: TASK는 전체 회귀를 `148 passed, 13 subtests passed`라고 기록한다. TASK 116행의 run-log를 확인하면 sequence 10은 `신규 CLI 22건 + 영향 회귀 62건`만 기록하고, self-pm validation도 RED·22·26·36 결과까지만 보존한다. `148/13`을 뒷받침하는 evidence 파일·명령 출력·run-log 사건은 발견되지 않았다.
  - 영향: 독립 검증자가 최종 전체 회귀 통과 수치를 원증거와 대조할 수 없다.
  - 해결 방안: 전체 회귀 명령과 `148 passed, 13 subtests passed` 결과를 evidence 파일 또는 표준 run-log 새 validation 사건에 보존한 뒤 TASK 131행에서 해당 경로/sequence를 직접 인용한다.
  - 자동 수정: N
  - 검증: 인용된 증거의 실제 결과가 TASK 수치와 정확히 일치해야 한다.
  - 참조: `docs/CONVENTIONS.md` §Citation Rules

### Low (1건, advisory)

- [ ] GC-011 [`docs/proposals/opal-oppb-project-build-pilot.md:3`] 제안서 상태가 허용 어휘 밖의 `초안`이다.
  - 카테고리: 문서화
  - 위반 기준: `docs/CONVENTIONS.md` §제안서 생명주기
  - 설명: 1차와 동일한 선행 결손이다. 이번 구현이 만든 값이 아니므로 차단에는 포함하지 않았다.
  - 해결 방안: 현재 단계에 맞춰 `제안`·`검토`·`적용완료`·`폐기` 중 하나로 갱신한다.
  - 자동 수정: Y
  - 검증: 상단 상태가 허용 4값 중 하나다.
  - 참조: `docs/CONVENTIONS.md` §제안서 생명주기

### Info (1건, informational)

- [ ] GC-012 [`opal/tools/oppb-runtime-tool/tests/test_product_flow.py:7`] `@header.migration_note` 누적 이력 경고가 남아 있다.
  - 카테고리: 문서화
  - 위반 기준: `docs/CONVENTIONS.md` §@header 규칙
  - 설명: `code-scan validate`가 이전과 동일하게 `header_history / undeclared_field / migration_note` 경고 1건을 반환했다. 비차단 선행 경고다.
  - 해결 방안: 이력은 git/task 기록으로 이동하고 헤더에는 현재 사실만 둔다.
  - 자동 수정: Y
  - 검증: `counts.header_history == 0`.
  - 참조: `docs/CONVENTIONS.md` §@header 규칙

## 4. 해소 확인

- GC-001~GC-010: `rg -n '999-oppb-fixture' opal/tools/oppb-runtime-tool/tests/*.py` 결과 0건.
- 대체 이름 `999-260926-oppb-fixture`는 10곳이며 `{NNN}-{YYMMDD}-{스킬약어}-{태스크명}` 형식을 만족한다.
- TASK 126행 RED는 `evidence/RED.md`에 연결됐다.
- TASK 127행 1차 GREEN은 run-log sequence 10에 연결됐고 기록 내용과 일치한다.
- TASK 35행 brain 검색과 132행 code-scan은 재현 명령을 포함한다.
- TASK 136~137행 독립 보고서 경로는 실제 존재한다.

## 5. 재검사 증거

- `git diff --check` — exit 0.
- `ruff check <14 Python 대상>` — exit 0, `All checks passed!`.
- `python3 -m py_compile <14 Python 대상>` — exit 0.
- JSON schema 문서 파싱 — exit 0.
- `code-scan validate --changed <23 tracked 대상> --json` — exit 0, `newly_uncovered=0`, `pre_existing=8`, `header_history=1`.
- run-log 1~10행과 self-pm `validation` 배열을 TASK 126~132행과 대조했다.

## 6. 결론

1차 blocking 11건 중 fixture 네이밍 10건은 해소됐다. 전체 회귀 결과 `148 passed, 13 subtests passed`의 원증거 연결 1건이 남아 재검사 판정은 **FAIL**이다. 이 수치와 일치하는 validation evidence를 연결하면 현재 task 158 변경에서 신규 blocking convention finding은 0건이 된다.
