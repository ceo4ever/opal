---
type: synthesis
title: 검증 2원화가 잡아낸 결함 6건 (작성자≠검증자)
tags:
- verification
- retrospective
- task-114
sources:
- task:114
related:
- side-effect-observation-enables-runtime-verification
- exploration-marker-as-output-artifact-creates-circularity
- ac-infeasible-from-start-requires-preexisting-baseline-diff
created: '2026-09-09'
updated: '2026-09-09'
status: draft
---
## 개요

작성자와 검증자를 분리한 지점마다 결함이 검출됐다. 태스크 114에서는 PM(작성자) 귀책 결함 3건이 독립 검증자(Evaluator·테스트 워커·컨벤션 워커)에게 적발됐으며, 단일 주체 자가 검증만으로는 이 중 어느 것도 잡히지 않았을 것으로 판단된다.

## 배경 — 검증 2원화 체계

(근거: task:114 DONE.md §3) 파이프라인은 산출물 작성 주체와 검증 주체를 구조적으로 분리한다 — ANALYSIS/PLAN을 작성하는 PM과, PLAN을 판정하는 Evaluator, 구현을 검증하는 테스트 워커, 컨벤션을 진단하는 컨벤션 워커가 각각 별도 주체다.

## 검출 내역 (6건)

| 검출 주체 | 검출 대상 | 결함 |
|----------|----------|------|
| PM | ANALYSIS 워커 | 커밋 해시 오기, 착수 트랙 stale 기재 |
| PM | PLAN 워커 | 내부 자기모순 — "동일한 마커"라고 서술했으나 실제로는 파일 vs 디렉토리라는 다른 대상을 가리켰다. 그대로 구현됐다면 최초 설치 전 루트를 못 찾는 순환과 설치·해석 루트 불일치가 발생했을 것이다(→ [[exploration-marker-as-output-artifact-creates-circularity]]) |
| Evaluator | PM(작성자) | 목표-커버 게이트 1회차 fail — "문서에 규칙이 쓰여 있다"와 "실제로 그렇게 행동한다"를 구분하지 못했고, 보안 게이트조차 정적 grep에 그쳤다(→ [[side-effect-observation-enables-runtime-verification]]) |
| 테스트 워커 | PLAN 설계 | `validate()`에 project 분기가 없어 완료기준(error 0건)이 원천 성립 불가였다(→ [[ac-infeasible-from-start-requires-preexisting-baseline-diff]]). ANALYSIS의 "신규 이슈 아님" 판정도 이 지점에서 틀렸다 |
| TEST 워커 | PM(작성자) | 매핑 표가 존재하지 않는 테스트 케이스를 인용했다 |
| 컨벤션 워커 | PM 지시 | "변경이력 대상 아님(코드 파일)"이라는 지시가 컨벤션 문서의 헤더 내 변경이력 규정을 놓쳤다 |

## 시사점

- PM 귀책 3건이 독립 검증자에게 적발됐다는 것은, 작성자 스스로의 재검토로는 발견하지 못했을 결함이 구조적 분리 덕에 드러났다는 뜻이다.
- 이 사례는 산출물 종류(분석·설계·구현·문서 준수)를 가리지 않고 전 단계에서 반복적으로 나타났다 — 검증 2원화가 특정 단계에만 유효한 것이 아니라 파이프라인 전 구간에서 결함 검출력을 갖는다는 근거다.

## 관련 페이지

- [[side-effect-observation-enables-runtime-verification]]
- [[exploration-marker-as-output-artifact-creates-circularity]]
- [[ac-infeasible-from-start-requires-preexisting-baseline-diff]]
