---
type: concept
title: 강제의 판정 근거는 자발적 표시가 아니라 구조여야 한다 — 3회 우회 후 행 기반 판정 + CLOSE 차단
tags:
- enforcement
- governance
- state-tool
- worker
- measurement
- lesson-learned
sources:
- task:103
related:
- delegation-only-file-gate-bypass
- worker-bypassed-blocked-tool-filename-trigger
- code-scan-split-execution-precedes-block
- guard-precision-none-passthrough-early-return
created: '2026-08-26'
updated: '2026-08-26'
status: draft
---
## 개요

지켜야 할 규범을 도구로 집행할 때, 위반 여부를 **당사자가 스스로 붙인 표시**로 판정하면 그 표시를 생략하는 것만으로 집행이 통째로 무력화된다. 판정 근거는 당사자의 의사와 무관한 **데이터 구조 자체**에 두어야 한다 (근거: task:103 DONE.md §3.3).

## 결정 배경 (WHY)

- 워커 실행 시간을 파이프라인 행에 남기려는 시도가 세 번 연속 새어나갔다 (근거: task:103 DONE.md §3.3 회차 표).
- 1회차는 기록할 자리(인자)를 만들었으나 쓰라는 규범이 없었고, 2회차는 산문 규범 3곳을 세웠으나 「워커 행임을 표시하라」가 빠져 있었다.
- 3회차에 도구 경고를 붙였지만, 그 경고의 발동 조건이 PM이 자발적으로 붙이는 워커 표시(`--as-worker`)에 걸려 있었다 — 그 인자를 쓰지 않으면 경고조차 침묵했다.
- 결정적 실증은 규범과 도구가 모두 준비된 뒤에 나왔다. 다른 프로젝트의 태스크가 배포 18분 뒤에 시작됐는데도 **15행 전건이 미기록으로 통과**했다 (근거: task:103 DONE.md §3.3 실측 증거).

## 결정 내용

- 판정을 행의 **구조**로 옮겼다 — 단계 이름이 워커 규범 단계에 속하고 항목이 「작업」으로 시작하면 워커 디스패치 행으로 본다(`opal/tools/state-tool/state_tool.py:1594`).
- 이 판정은 PM이 어떤 인자를 쓰든 무관하게 성립하므로, 표시를 생략해서 빠져나가는 경로가 사라진다.
- 경고 하나로는 무시하면 그만이므로, 태스크를 닫는 지점에 **차단**을 걸었다 — 기록도 선언도 없는 워커 행이 남으면 CLOSE 진입을 거부한다(`opal/tools/state-tool/state_tool.py:1672`).
- 통과 경로는 소요를 기록하거나 미측정을 선언하는 둘뿐이며, 사유를 남기는 강제 우회가 최후 수단으로만 열려 있다 (근거: task:103 DONE.md §3.3 최종 설계).

## 영향 범위

도구로 집행하는 모든 규범의 설계. 「위반을 무엇으로 판정하는가」를 정할 때, 그 판정 신호를 당사자가 만들어 넣는 구조라면 집행은 권고와 같다. 탐지 지점(경고)과 차단 지점(게이트)을 분리해 배치하는 것도 같은 이유다.

## 관련 페이지

- [[delegation-only-file-gate-bypass]]
- [[worker-bypassed-blocked-tool-filename-trigger]]
- [[code-scan-split-execution-precedes-block]]
- [[guard-precision-none-passthrough-early-return]]
