---
type: concept
title: 규칙 1소유자 매핑 — Governance 중복 기재 방지 설계
tags:
- governance
- ssot
- design-pattern
- dispatch
sources:
- task:081
related:
- mitigation-recurs-without-ssot-registration
- anchor-load-condition-must-match-target
created: '2026-08-02'
updated: '2026-08-02'
status: draft
---
## 개요

동일한 수치·절차 규칙을 여러 SSOT 문서에 중복 기재하면 한쪽만 갱신되고 다른 쪽이 stale해지는 governance 위반이 발생한다. 각 규칙 요소마다 **단일 소유 문서**를 지정하고, 그 외 문서는 값을 복제하지 않고 소유 문서를 가리키는 참조만 두는 설계로 이를 예방한다.

## 결정 배경 (WHY)

- (근거: task:081 PLAN §1.4 Core Stance) 동일 규칙·수치가 두 파일에 중복 기재되면 한쪽 개정 시 다른 쪽이 뒤처지는 governance 위반 위험이 있다.
- (근거: task:081 PLAN §1.5) 이 태스크에서 재시도 상한(1회), 실측 판정 절차(3단계), 산출 파일 상한(3개), 증분 저장·입력 축소 규율 문언까지 총 4개 규칙 요소가 여러 하네스 문서에 걸쳐 있었다.

## 결정 내용

각 규칙 요소에 정확히 1개의 소유 문서를 지정했다.

| 규칙 요소 | 유일 소유 문서 |
|----------|--------------|
| 재시도 상한 = 1회 | `opal-harness.md` §1 |
| 실측 판정 3단계 | `harness/pm-review-gate.md` |
| 산출 파일 상한 = 3개 | `pm/dispatch-process.md` Step 6 |
| 증분 저장·입력 축소 규율 원문 | `pm/dispatch-process.md` 주입 템플릿 |

소유 문서가 아닌 다른 문서에는 수치·절차 본문을 복제하지 않고, 소유 문서를 가리키는 참조 1줄만 남긴다. 검증은 "각 리터럴이 정확히 1개 파일에서만 발견되는가"를 grep으로 확인하는 방식으로 결정론적으로 수행할 수 있다.

## 영향 범위

여러 SSOT 문서에 걸쳐 규칙을 등재해야 하는 모든 후속 작업(PLAN §1.4 이하 governance 설계)에서 재사용 가능한 설계 패턴이다. 규칙을 새로 등재할 때 "어느 문서가 소유자인가"를 먼저 정하고 나머지는 참조만 남기는 절차로 적용한다.

## 관련 페이지

- [[mitigation-recurs-without-ssot-registration]]
- [[anchor-load-condition-must-match-target]]
