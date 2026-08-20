---
type: concept
title: 가드 정밀화가 새 우회로를 만든다 — None 통과는 조기 반환으로 봉쇄한다
tags:
- memory-tool
- guard-design
- none-safety
- lesson
- task-096
sources:
- task:096
related:
- unresolvable-not-absent-two-vocabulary-split
- rotating-log-correction-over-deletion
- silent-render-failure-deterministic-gate
created: '2026-08-20'
updated: '2026-08-20'
status: draft
---
## 개요

무손실 가드의 술어를 좁히려던 변경이, 술어가 참조하는 함수의 `None` 반환 경로를 통해 가드를 조용히 통과시켜 새로운 blind 삭제 벡터를 만들 뻔했다. 원인은 "조회 결과가 없으면 조건이 거짓이 되어 가드를 우회하는" 조건식 구조였고, 해법은 `None` 판정을 **조기 반환**으로 분리해 뒤 조건에 도달하지 못하게 막는 것이다.

## 결정 배경 (WHY)

- 경로 포인터를 절대경로로 해석하는 함수는 예외 발생·`memory/` 디렉토리 탈출·빈 경로 3가지 경로에서 `None`을 반환한다(`opal/tools/memory-tool/memory_tool.py:806-820`).
- 개정 전 삭제 가드는 "해석된 경로가 있고 그 경로에 파일이 있으면 거부"라는 `and` 결합 조건이었다. `None`이 들어오면 앞항이 거짓이 되어 전체 조건이 거짓으로 평가되고, 가드는 뒤 조건(파일 실재 여부)을 아예 검사하지 못한 채 통과했다.
- 실증 결과가 보고보다 심각했다 — 스키마 패턴 `^memory/[^/].*\.md$`에 `memory/../../outside.md`가 **매치**하므로 경로 탈출 포인터를 가진 행이 정상 등록되고, 이 행에서 해석 함수는 `None`을 반환한다. 그 결과 본문이 디스크에 멀쩡히 남아 있는데도 삭제 가드가 뚫려 인덱스 행이 지워지고, 인덱스로도 자가검토로도 다시 찾을 수 없는 실질적 지식 소실이 발생할 수 있었다(근거: task:096 DONE.md §3).
- 이 결함은 목표-커버 게이트 iteration 1에서 검출됐다 — PLAN 설계 단계의 P0 결함이며, 게이트가 없었으면 그대로 배포됐을 것이다(근거: task:096 DONE.md §3).

## 결정 내용

- 가드를 "`None`이면 즉시 거부"로 재구성한다 — `if mem_file is None: err(...)`을 먼저 두어, 뒤따르는 파일 실재 검사에 `None`이 절대 도달하지 못하게 한다(`opal/tools/memory-tool/memory_tool.py:1385-1391`).
- 평가는 "재현 여부"가 아니라 "구조적으로 불가능해졌는가"로 확인한다 — 함수 내부 `None` 반환 지점 2곳(`memory_tool.py:806-820`)과 호출부 처리 1곳을 대조하고, 파생 입력 4종(키 부재·null·공백만·심볼릭 링크)이 모두 이 3경로 중 하나로 귀착함을 확인했다(근거: task:096 AGENTIC-LOG.md #33 "G-3 구조 가드(조기 반환 존재·`is not None and` 부재) 통과").
- 일반화: 술어를 좁히는 리팩터링을 게이트할 때는 "새 술어가 통과시키는 입력 전체"를 열거하기보다, **술어가 의존하는 하위 함수의 실패/예외 반환 경로를 먼저 전수 열거**하고 각 경로가 조기 반환으로 막혀 있는지를 구조적으로 확인한다. `and`로 묶인 조건식에서 앞 항이 조회 실패 시 `None`/`False`/빈 값을 반환하는 함수라면, 그 조건식은 실패를 "거짓"이 아니라 "판정 불가"로 다루도록 재구성해야 한다.

## 영향 범위

- `opal/tools/memory-tool/memory_tool.py:1385-1391` — `delete --orphan` 경로의 조기 반환 가드.
- `opal/tools/memory-tool/memory_tool.py:806-820` — 가드가 의존하는 경로 해석 함수의 3가지 `None` 반환 지점.
- 무손실 가드를 재설계하는 모든 향후 변경 — 술어 정밀화는 그 자체로 새 우회로를 만들 수 있다는 일반 경계 대상이다.

## 관련 페이지

- [[unresolvable-not-absent-two-vocabulary-split]] — 이 가드 재설계가 함께 도입한 검출 어휘 분리
- [[rotating-log-correction-over-deletion]] — memory-tool의 다른 무손실 가드 설계 사례
- [[silent-render-failure-deterministic-gate]] — 조기 반환이 조용한 실패를 막는 유사 패턴
