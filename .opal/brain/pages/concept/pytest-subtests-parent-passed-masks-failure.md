---
type: concept
title: pytest-subtests는 subtest 실패를 부모 PASSED로 표시한다 — 판정 단위를 서브케이스로 내린다
tags:
- testing
- pytest
- verification
- lesson
- task-096
sources:
- task:096
related:
- green-tests-do-not-imply-contract-conformance
- red-test-determinism-abort-trap
created: '2026-08-20'
updated: '2026-08-20'
status: draft
---
## 개요

`pytest-subtests`는 subtest 실패를 부모 테스트에 `PASSED`로 표시한다. `pytest -v` 출력의 `PASSED`/`FAILED` 판정 어휘만으로 결과를 읽으면, exit code는 정상 집행됐더라도 케이스 단위 신호를 놓쳐 실패가 통과로 오인될 수 있다.

## 결정 배경 (WHY)

- GREEN 단계 검증에서 요약 라인 "24 failed"를 보고 워커의 보고(20건 RED·4건 PASS)가 틀렸다고 판단했으나, 재대조 결과 워커 보고가 정확했다(근거: task:096 DONE.md §7 "PM 판독 오류 1건").
- 이 특성이 위험한 지점은 exit code가 아니라 **판정 단위**다. `pytest-subtests`의 subtest 실패는 부모 테스트 함수 자체를 `FAILED`로 만들지 않고, `-v` 출력에서도 부모가 `PASSED`로 보일 수 있다. GREEN 단계 워커가 이 `PASSED` 표시만으로 통과를 판정하면, 실제로는 실패한 P0 음성 통제(예: `SUBFAILED` 4건을 보유한 테스트)가 통과한 것으로 오인될 수 있다(근거: task:096 DONE.md §7).

## 결정 내용

- pytest-subtests를 쓰는 테스트 스위트를 판정할 때는 부모 테스트의 `PASSED`/`FAILED` 표시가 아니라, `-v` 출력의 subtest 단위 결과(각 subtest 라인 또는 `SUBFAILED`/서브테스트 실패 카운트)를 판정 근거로 삼는다.
- 워커 디스패치 프롬프트에 이 판정 규약을 명시적으로 주입해, 후속 GREEN 검증 단계가 동일한 오판을 반복하지 않도록 파급을 차단한다(근거: task:096 DONE.md §7 "Step 2~5 디스패치 프롬프트에 판정 규약을 주입해 파급을 차단").
- 일반화: 테스트 러너의 리포팅 계층(요약 라인·상위 케이스 상태)이 실제 실패 단위(서브케이스)를 가릴 수 있는 도구를 사용할 때는, 판정을 상위 계층 표시가 아니라 실패가 실제로 발생하는 최소 단위의 출력으로 내려서 확인한다.

## 영향 범위

- `opal/tools/memory-tool/tests/test_memory_tool.py` — `pytest-subtests`를 사용하는 테스트 스위트(31개 subtest, 근거: task:096 DONE.md §5).
- pytest-subtests를 사용하는 모든 향후 테스트 판정 — GREEN/RED 판정을 부모 테스트 상태만으로 내리는 모든 검증 단계가 이 함정에 노출된다.

## 관련 페이지

- [[green-tests-do-not-imply-contract-conformance]] — GREEN 판정 자체가 계약 준수를 보장하지 않는다는 인접 원칙
- [[red-test-determinism-abort-trap]] — 테스트 결과 판정 신뢰성에 관한 인접 교훈
