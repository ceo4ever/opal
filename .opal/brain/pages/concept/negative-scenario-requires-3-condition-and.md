---
type: concept
title: 부정 시나리오는 없다만으로 판정하지 않는다 — 3조건 AND
tags:
- verification
- testing
- skill-wizard
- task-114
sources:
- task:114
related:
- side-effect-observation-enables-runtime-verification
- negative-control-proves-verification-not-weakened
created: '2026-09-09'
updated: '2026-09-09'
status: draft
---
## 개요

부정 시나리오("이 절차는 특정 조건에서 발동하지 않아야 한다")를 「어떤 부작용도 관측되지 않았다」한 가지만으로 판정하면 안 된다. 게이트가 정상적으로 차단한 경우와, 절차가 조기에 실패해 우연히 아무 흔적도 남기지 않은 경우를 구분할 수 없기 때문이다.

## 결정 배경 (WHY)

(근거: task:114 DONE.md §3) 부작용 관측 방법론([[side-effect-observation-enables-runtime-verification]])을 도입할 때, 부작용 부재(c)만을 판정 기준으로 삼으면 「게이트가 차단했다」와 「경로 오류 등으로 조기에 죽어서 우연히 아무 일도 안 일어났다」를 구분하지 못한다는 문제가 남는다. 두 경우 모두 관측 결과는 "변화 없음"으로 동일하게 나타난다.

## 결정 내용

부정 시나리오는 아래 3조건을 **모두(AND)** 충족해야 통과로 판정한다.

1. **exit 0** — 절차가 비정상 종료(크래시·예외)가 아니라 정상적으로 완주했다.
2. **거부·위임 사유 신호** — 절차 자체가 "이 경로에서는 처리하지 않는다"는 취지의 신호(로그·응답 필드·라우팅 분기 등)를 남긴다.
3. **부작용 부재** — 의도하지 않은 파일시스템 변화가 실제로 없다.

(c) 단독은 조건 (a)(b) 없이는 오검출을 걸러내지 못한다. 이 3조건 판정에는 **사전 스냅샷 의무**가 함께 따른다 — (3)을 판정하려면 절차 실행 전 상태를 미리 기록해 두어야 사후 비교가 성립한다.

## 영향 범위

- 부정 테스트 시나리오(설치되지 않아야 한다·전역이 오염되지 않아야 한다 류)를 설계할 때 공통으로 적용 가능한 판정 골격이다.
- (근거: task:114 DONE.md §3) TS-031(전역 `~/.opal/community-skills/` 변화 0건 검사)이 이 3조건 골격의 실제 적용 사례다.

## 관련 페이지

- [[side-effect-observation-enables-runtime-verification]]
- [[negative-control-proves-verification-not-weakened]]
