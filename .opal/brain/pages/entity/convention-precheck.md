---
type: entity
title: convention-precheck (컨벤션 결정론 사전 검사 도구)
module: <code-scan @header module>
layer: <code-scan @header layer>
domain: <code-scan @header domain>
exports: []
source_ref: '<코드 파일 경로 — 예: opal/tools/state-tool/state_tool.py>'
header_synced: <YYYY-MM-DD>
tags:
- tool
- convention
- verification
sources:
- task:172
related: [op-gc-convention, gc-finding-schema, agent-effort-policy-inherit-by-default]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

컨벤션 검사 중 모델 판단이 필요 없는 부분을 결정론으로 먼저 걸러내는 도구다. 기준 커밋과 비교한 변경 구간을 계산하고 기계적으로 판정 가능한 규칙 4종을 검사해, 컨벤션 검사 에이전트가 변경 구간만 읽어도 되게 만든다.

## 책임 (WHAT)

- 기준 커밋(merge-base) 대비 변경 파일·변경 구간(앞뒤 문맥 포함)을 계산한다 (`opal/tools/convention-precheck/convention_precheck.py:424`).
- 기계 규칙 4종을 판정한다: 헤더 규칙, frontmatter 필수 키, 수기 변경이력 절, 네이밍 (`opal/tools/convention-precheck/convention_precheck.py:29`). 결과는 기존 finding 스키마와 같은 형식이다.
- 사전 검사 결과와 에이전트 검토 결과를 합친다(`merge`, `opal/tools/convention-precheck/convention_precheck.py:576`). 검사 에이전트는 기준 커밋이 주어지면 변경 구간만 읽는다.
- 과거 사례 재현: 162 태스크의 High 2건이 재현된다 (근거: task:172 DONE.md AC-5).

## 설계 배경 (WHY)

- 컨벤션 검사 시간을 줄이려면 모델 판단이 필요한 부분과 결정론으로 고정 가능한 부분을 나눠야 한다는 판단에서 신설했다 (근거: task:172 DONE.md).
- 최초 측정에서 회귀 판정이 163 구간에 High 6건의 거짓 양성을 냈다. 판정기를 기준과 현재 양쪽에 같게 적용하도록 고쳐 해결했고 최초 결과는 보존했다 (근거: task:172 DONE.md 검증).
- 구현 중 해석 4건을 구현 세부로 승인했다: 헤더 규칙은 코드 확장자만, 필수 5필드 검사는 추가 파일만, 네이밍은 새 구성요소만, 지문 입력에 세부 키 부가 (근거: task:172 DONE.md).
- 컨벤션 검사 에이전트는 `standard` + `effort: low`로 고정되었다 ([[agent-effort-policy-inherit-by-default]]).

## 관계 (HOW)

- [[op-gc-convention]] — 이 도구의 결과를 받아 변경 구간만 검토하는 검사 스킬
- [[gc-finding-schema]] — 사전 검사가 따르는 finding 스키마(필드·판정표 불변)
- [[agent-effort-policy-inherit-by-default]]

## 소스 커버리지

| 식별자 | 경로:줄번호 | 설명 |
|--------|-----------|------|
| `cmd_scan` | `opal/tools/convention-precheck/convention_precheck.py:424` | 변경 구간 계산과 기계 규칙 판정 |
| `cmd_merge` | `opal/tools/convention-precheck/convention_precheck.py:576` | 사전 검사·검토 결과 병합 |
| `run.sh` | `opal/tools/convention-precheck/run.sh` | 실행 진입점 |
