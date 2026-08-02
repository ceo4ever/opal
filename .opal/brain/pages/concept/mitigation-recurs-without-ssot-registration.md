---
type: concept
title: 완화책은 SSOT 미등재 시 재발한다
tags:
- governance
- worker
- infra-failure
- ssot
- resilience
sources:
- task:078
- task:079
- task:081
related:
- long-running-worker-infra-failure-mitigation
created: '2026-08-02'
updated: '2026-08-02'
status: draft
---
## 개요

워커 인프라 실패(장시간 스톨·연결 종료) 대응책은 한 태스크에서 도출·재현되어도, 그 대응이 SSOT 문서에 규칙으로 등재되지 않으면 다음 태스크에서 재적용이 누락되고 동일 실패가 재발한다.

## 결정 배경 (WHY)

- (근거: task:078 DONE §8) 워커 인프라 실패가 3연속 발생한 뒤 배치분할·모델하향·함수단위저장 조합을 적용해 전량 성공했다. 그러나 이 대응은 PM 세션 프롬프트 수준에 머물렀고, 별도 SSOT 문서에는 등재되지 않았다.
- (근거: task:079) 같은 조합을 선제 적용한 결과 실패 0건으로 재현되어, 완화책의 효과가 1회성 우연이 아님이 확인됐다.
- (근거: task:081 DONE §1) 080에서는 이 조합이 재적용되지 않아 동일 실패가 5회 재발했다. 원인은 대응이 어느 SSOT 문서에도 없어 다음 PM 세션이 참조할 근거가 없었기 때문이다.

## 결정 내용

081에서 이 조합을 하네스 SSOT 3곳(`opal/core/references/opal-harness.md`, `opal/core/references/harness/pm-review-gate.md`, `opal/core/references/pm/dispatch-process.md`)에 규칙으로 승격했다. 핵심은 "새 규칙을 발명"하는 것이 아니라 "이미 실증된 대응을 문서화되지 않은 세션 지식에서 재현 가능한 SSOT로 옮기는 것"이다.

## 영향 범위

- 워커 프로세스 중단(스톨·연결 종료)을 다루는 모든 향후 PM 세션 — 세션 기억에 의존하지 않고 SSOT만으로 동일 대응을 재현할 수 있다.
- 유사하게, 효과가 실증된 완화책이 발견될 때마다 "어느 SSOT에 등재할지"를 CLOSE 단계에서 점검하는 관행의 근거가 된다.

## 관련 페이지

- [[long-running-worker-infra-failure-mitigation]]
- [[governance-single-owner-rule-mapping]]
