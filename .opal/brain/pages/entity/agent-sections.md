---
type: entity
title: agent_sections
module: <code-scan @header module>
layer: <code-scan @header layer>
domain: <code-scan @header domain>
exports: []
source_ref: '<코드 파일 경로 — 예: opal/tools/state-tool/state_tool.py>'
header_synced: <YYYY-MM-DD>
tags:
- tool
- event-loader
sources:
- task:175
related: [worker-dispatch-target-section-selection, worker-dispatch-contract-v2-binding]
created: '2026-10-02'
updated: '2026-10-02'
status: draft
---
## 개요

워커 디스패치용 레지스트리 문서에서 대상 에이전트 항목만 골라내는 순수 함수 모듈이다. 이벤트 로더가 호출하며, 코드 펜스 안의 헤딩을 절 경계로 오인하지 않는 것이 핵심이다.

## 책임 (WHAT)

- 문서를 펜스 바깥 헤딩 기준 절 목록으로 나눈다(`opal/tools/event-loader/agent_sections.py:35`).
- 선별 선언과 대상 에이전트를 받아 전달 본문, 유지·제외한 절의 식별자와 바이트, 대상 항목 존재 여부를 돌려준다(`opal/tools/event-loader/agent_sections.py:71`).
- 하위 절 범위 계산으로 제외 절을 하위까지 통째로 뺀다(`opal/tools/event-loader/agent_sections.py:63`).

## 설계 배경 (WHY)

- 레지스트리의 예시 블록 안에 실제 헤딩과 같은 모양의 줄이 있어 펜스 인식이 없으면 절이 유출된다. (근거: task:175 PLAN D-7)
- 선별 로직을 로더 본체와 분리해 단위 테스트가 실제 레지스트리 문서로도 대상별 결과 크기와 예시 문구 부재를 검사하게 했다. (근거: task:175 PLAN W-1)
- 판정 규칙을 설계보다 관대하게 구현했다. (근거: task:175 DONE 설계 대비 차이)

## 관계 (HOW)

- 호출자는 이벤트 로더의 load와 verify이며, verify는 같은 규칙으로 선별을 재수행해 증거 해시와 대조한다.
- [[worker-dispatch-target-section-selection]]
- [[worker-dispatch-contract-v2-binding]]

## 소스 커버리지

| 식별자 | 경로:줄번호 | 설명 |
|--------|-----------|------|
| `Section` | `opal/tools/event-loader/agent_sections.py:21` | 절 하나의 표현 |
| `parse_sections` | `opal/tools/event-loader/agent_sections.py:35` | 펜스 바깥 헤딩 절 분할 |
| `select_agent_entries` | `opal/tools/event-loader/agent_sections.py:71` | 대상 항목 선별 |
