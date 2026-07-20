---
type: concept
title: RED-first 하이브리드 검증 트랙 — 도구 계약 변경 한정 적용
tags:
- verification
- red-first
- opal-agent
- testing
sources:
- task:067
related:
- opal-agent-stream-json-passthrough
created: '2026-07-17'
updated: '2026-07-17'
status: active
---
## 개념 요약

한 태스크 안에서 검증 방식을 이원화하는 트랙이다 — 기존 도구의 계약(입출력 형식)을 바꾸는 변경에는 실패하는 테스트를 먼저 작성하는 RED 우선 방식을 강제하고, 신규로 추가되는 읽기 전용 도구나 문서에는 구현 후 검증을 적용한다. 이번 태스크에서 opal-agent 개조분에 처음 실제 적용됐다.

## 배경·문제 (WHY)

opal-agent의 스트리밍 실행 경로 신설은 기존에 이미 동작하던 일괄 실행 경로·5필드 반환 계약을 건드릴 위험이 있는 변경이었다(근거: task:067 PLAN§3.1.5 H-3 — 기존 `test_opal_agent.py` 스위트 회귀 위험). 반면 같은 태스크에서 함께 만들어진 신규 관측 도구([[opal-agent-stream-json-passthrough]]가 만든 산출물을 읽는 읽기 전용 도구)는 애초에 아무 기존 계약도 건드리지 않는다. 두 변경의 위험 프로파일이 다르므로 같은 검증 강제 수준을 적용할 이유가 없었다.

## 결정 내용 (HOW)

- **적용 기준**: 기존 도구의 입출력 계약을 변경하는 작업(이번 태스크에서는 opal-agent 실행 경로 개조)만 RED-first를 강제한다 — 실패하는 테스트를 작성자와 다른 주체가 먼저 작성하고, 이후 구현이 그 테스트를 통과시키는 순서를 밟는다.
- **제외 기준**: 신규로 추가되는 읽기 전용 뷰어나 문서 변경은 구현을 먼저 하고 사후에 검증한다 — 아직 존재하지 않는 계약을 미리 실패시킬 대상이 없기 때문이다.
- **작성자·구현자 분리**: RED 테스트는 검증 주체(test-agent 축)가 작성하고, 구현자(생성자 축)는 그 테스트를 통과시키는 역할만 맡는다 — 같은 사람이 테스트와 구현을 모두 쓰면 테스트가 구현을 정당화하는 방향으로 왜곡될 위험이 있기 때문이다.

## 영향·관계

`opal/tools/opal-agent/tests/test_opal_agent.py`에 RED-first로 먼저 작성된 4개 케이스가 실적용 사례다. [[opal-agent-stream-json-passthrough]]가 이 트랙이 적용된 대상 변경이다.

## 근거 출처

task:067 — PLAN.md §3.1.5(H-3), DONE.md 핵심 설계 결정("RED-first 하이브리드").
