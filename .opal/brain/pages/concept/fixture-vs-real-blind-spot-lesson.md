---
type: concept
title: fixture-vs-real 맹점 — 테스트 픽스처 통과·실데이터 버그 반복 교훈
tags:
  - lesson
  - testing
  - bug
  - fixture
sources:
  - task:045
  - task:039
  - task:044
related:
  - memory-tool
  - agentic-output-direct-verification-lesson
created: "2026-06-26"
updated: "2026-06-26"
status: active
---

## 개요

테스트 픽스처는 단순화된 형식을 사용하기 때문에, 실제 데이터가 가진 특수 문법(백틱·파이프·이스케이프 등)에서 발생하는 버그를 잡지 못한다. 픽스처 통과와 실데이터 동작은 독립 보장이 아니다 — 픽스처가 통과해도 실데이터에서 달리 동작할 수 있다. 이 교훈은 task:039 → task:044 → task:045로 반복 발현됐다. (근거: task:045 DONE 추가작업 #2)

## 결정 배경 (WHY)

task:045에서 `delete`/`promote --with-file` 명령이 `migrate`로 변환된 MEMORY.md에서 실파일을 삭제하지 못하는 버그가 발생했다. 원인은 `migrate`가 파일 경로를 백틱으로 감싸는 형식(`` `memory/x.md` ``)을 생성하는데, `_resolve_memory_file` 함수가 이 백틱을 strip하지 않아 파일 경로를 찾지 못한 것이다. (근거: task:045 DONE 추가작업 #2)

테스트 픽스처는 백틱 없이 `memory/x.md` 형식을 사용했기 때문에 단위 테스트는 전원 통과했다. 실데이터(`migrate` 변환 후 MEMORY.md)에서만 발현하는 형태였다. PM이 직접 실데이터로 재현 검증해서 포착했다. (추론: 코드패턴 — `_resolve_memory_file` strip 1줄 수정으로 해결됐음이 단순 버그임을 시사)

동일한 유형의 맹점이 task:039와 task:044에서도 반복 발현된 바 있다(반복 교훈). (근거: task:045 DONE 추가작업 #2 "039/044 반복 교훈")

## 결정 내용

### 맹점 패턴 정의

픽스처-vs-실데이터 맹점은 아래 조건이 겹칠 때 발생한다:

1. 테스트 픽스처가 실데이터보다 단순한 형식을 사용한다 (특수 문법 부재)
2. 실데이터가 도구 자체 출력물(예: `migrate` 변환 결과)이다 — 도구가 생성한 형식을 도구가 다시 소비할 때 형식 불일치가 발생할 수 있다
3. 파싱·경로 해석 코드가 특수 문법을 처리하지 못한다

### 대응 원칙

- **실데이터 회귀 픽스처**: 버그 발현 후 실데이터에서 추출한 형식을 픽스처로 추가한다. 백틱 포함 경로 형식 등을 별도 픽스처로 보강한다. (task:045에서 버그 회귀 픽스처 3건 추가)
- **PM 직접 실행 검증**: 단위 테스트 통과만으로는 충분하지 않다. 도구가 실데이터에서 end-to-end로 동작하는지 PM이 직접 실행해서 확인한다. 특히 도구 A가 생성한 출력을 도구 B가 소비하는 파이프라인은 실데이터 검증이 필수다.
- **형식 생성 코드와 파싱 코드의 일관성**: 도구가 쓰는 형식과 읽는 코드를 동일 개발 사이클에서 검토한다 — 생성자와 소비자의 형식 계약이 명시적으로 일치해야 한다.

### 해결 사례 (task:045)

`_resolve_memory_file` 함수에 1줄 strip을 추가하여 백틱 감싸기를 제거했다. 버그 회귀 픽스처 3건을 테스트에 추가했다. (근거: task:045 DONE 추가작업 #2)

## 영향 범위

- `opal/tools/memory-tool/memory_tool.py` — `_resolve_memory_file` strip 수정
- `opal/tools/memory-tool/tests/test_memory_tool.py` — 버그 회귀 픽스처 3건 추가

## 관련 페이지

- [[memory-tool]] — 이 교훈이 발현된 도구
- [[agentic-output-direct-verification-lesson]] — PM 직접 검증의 필요성을 다루는 관련 교훈
