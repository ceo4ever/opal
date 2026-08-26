---
type: concept
title: 세어야 하는 검사는 사람이 아니라 도구가 한다 — 미완 슬롯 158건 누락
tags:
- pm-gate
- verification
- close
- tooling
- lesson-learned
sources:
- task:103
related:
- pm-gate-artifact-tool-enforcement
- close-history-auto-link-enforce-conversion
- enforcement-basis-must-be-structural-not-voluntary
created: '2026-08-26'
updated: '2026-08-26'
status: draft
---
## 개요

세어야 알 수 있는 검사는 사람의 눈으로 통과시킬 수 없다. 산출물에 남은 빈 슬롯 158건이 검토 게이트를 그대로 통과했고, 원인은 주의력이 아니라 **검사 방식**이었다 (근거: task:103 DONE.md §4.6).

## 결정 배경 (WHY)

- 테스트 시나리오 문서에 워커가 채우기로 한 빈 자리가 158건 남아 있었다.
- 테스트 단계가 판정을 별도 문서에 쓰면서 원 문서의 결과 칸이 비었고, 그 상태로 검토 게이트를 통과했다.
- 문서를 눈으로 훑어서는 158건을 셀 수 없다 — 개별 슬롯 하나하나는 자연스러워 보이고, 문제는 총량에서만 드러난다.

## 결정 내용

- 빈 슬롯을 결과 문서를 가리키는 포인터로 교체하고, 판정의 소유를 문서별로 갈랐다 — 시나리오 문서는 **정의**를, 테스트 문서는 **결과**를 소유한다 (근거: task:103 DONE.md §4.6).
- 태스크를 닫는 지점에서 미완 슬롯·산출물 누락·배포 신선도를 기계적으로 점검하는 검사를 별도 과제로 세웠다 — 이 사고가 그 제안의 직접 근거다 (근거: task:103 DONE.md §6 이월 1).
- 같은 사상이 워커 소요 강제에도 적용됐다 — 경고는 무시할 수 있으므로 닫는 지점에서 한 번은 반드시 걸리게 한다([[enforcement-basis-must-be-structural-not-voluntary]]).

## 영향 범위

문서 산출물을 대상으로 하는 모든 검토 게이트. 검사 항목이 「빠짐없이 채워졌는가」처럼 총량 판정이면 사람 검토로 배치하지 말고 도구 검사로 옮겨야 한다.

## 관련 페이지

- [[pm-gate-artifact-tool-enforcement]]
- [[close-history-auto-link-enforce-conversion]]
- [[enforcement-basis-must-be-structural-not-voluntary]]
