---
type: concept
title: 규모 수치의 SSOT는 문서가 아니라 소스 실측이다
tags:
- ssot
- documentation
- drift
- measurement
- discipline
sources:
- task:086
related:
- usage-ssot-live-help-principle
- readme-ssot-principle
- analysis-drift-pm-cross-verify-lesson
- expected-total-as-reference-not-gate-criterion
created: '2026-08-10'
updated: '2026-08-10'
status: draft
---
## 개요

프레임워크 규모를 나타내는 수치의 SSOT는 문서가 아니라 **소스 디렉토리와 frontmatter 실측**이다. 아키텍처 문서와 하네스 참조 문서가 동시에 뒤처져 있었고, 그 수치를 전사하면 오류가 새 산출물로 전파된다.

## 결정 배경 (WHY)

다이어그램 재작성 시점에 문서 수치와 실측이 여러 항목에서 갈렸다 (근거: task:086 DONE.md §8 (4), §9).

- 아키텍처 문서는 워커 에이전트를 12개로, 독립 스킬을 5~6개로 적고 있었고 실측은 각각 15개와 8개였다 (`docs/ARCHITECTURE.md:39`, `:78`).
- 하네스 참조 문서는 brain 도구를 8서브명령, 상태 도구를 9서브명령으로 적고 있었고 실측은 각각 10개였다 (`opal/core/references/opal-harness.md:251-252`).
- 계획서 자체도 문서 수치를 옮겨 적어 brain 도구를 8서브명령으로 기재했다 (근거: task:086 PLAN.md §2.3) — 실측 기준을 세운 태스크 안에서도 전사 오류가 한 번 발생했다.

원인은 v0.5 이후 프레임워크가 확장되는 동안 다이어그램과 문서가 함께 갱신되지 않았다는 점이다 (근거: task:086 DONE.md §2). 수치가 여러 문서에 흩어져 있으면 어느 하나가 갱신될 때 나머지가 조용히 stale이 되고, 문서 간 drift는 오류를 만들지 않으므로 발견되지 않는다.

실측 SSOT로 고정한 판단의 결과로 파일럿 10개·워커 15개·단계 스킬 21개·도구 18종·직접 실행 스킬 11종이라는 수치를 확정하고, 종전 표기의 불일치 11건을 복구했다 (근거: task:086 DONE.md §5).

## 결정 내용

- 규모 수치는 디렉토리 열거와 frontmatter 조회로 그 자리에서 측정한다. 문서에 적힌 수치는 참고로만 보고, 실측과 다르면 실측을 채택하고 문서 불일치를 별도 이관 항목으로 남긴다.
- 실측과 문서가 갈릴 때 문서를 같은 태스크에서 고치려 들지 않는다. 산출물 범위를 지키고 불일치 목록만 정확한 위치(파일·줄번호)와 함께 넘긴다 (근거: task:086 DONE.md §9).
- 각 서브명령 수는 도구 자신의 도움말 출력으로 확인한다 (→ [[usage-ssot-live-help-principle]]). 문서에 적힌 개수는 갱신 누락에 노출된다.
- 문서 간 drift는 어느 쪽도 오류를 내지 않으므로 사람이 대조할 때만 발견된다. 새 산출물을 만들 때가 대조하기 가장 좋은 시점이다.

## 영향 범위

프레임워크 규모·구성을 서술하는 모든 후속 작업 — 아키텍처 문서, 소개·온보딩 자료, 다이어그램, 릴리스 노트. 수치를 인용하는 모든 지점에 적용된다.

## 관련 페이지

- [[usage-ssot-live-help-principle]] — 사용법 SSOT는 도구 자신의 live 도움말
- [[readme-ssot-principle]] — 문서·구현 불일치 시 구현 정본 원칙
- [[analysis-drift-pm-cross-verify-lesson]] — 분석 결과를 직접 교차검증하는 규율
- [[expected-total-as-reference-not-gate-criterion]] — 잘못된 수치가 게이트로 들어갈 때의 손상
