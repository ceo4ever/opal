---
type: concept
title: 완료기준 변경의 허용 경계 — 정정과 완화의 구분
tags:
- fw-structure
- governance
- task-087
sources:
- task:087
related:
- doc-line-count-source-vs-deploy-duality
- conditional-batch-output-cap-tradeoff
created: '2026-08-09'
updated: '2026-08-09'
status: draft
---
## 개요

완료기준을 착수 후에 바꾸는 것은 원칙적으로 금지되지만, "측정 방식의 오류를 바로잡는 정정"과 "목표치를 낮추는 완화"는 성격이 다르며 처리 방식도 다르다는 경계 기준이 이번 태스크에서 두 실제 사례로 확인됐다(근거: task:087 DONE.md §6, AGENTIC-LOG 판단 9·13).

## 결정 배경 (WHY)

완료기준을 사후에 바꾸면 자기 완료기준을 스스로 합리화하는 것이 될 위험이 있다. 그러나 모든 사후 변경을 무조건 금지하면, 착수 시점에 이미 알려진 측정 오류를 바로잡을 방법이 없어진다. 이번 태스크는 이 두 경우를 실제로 구분해 처리했다(근거: task:087 DONE.md §2 C1 판정 기준 변경, C4 미달 처리).

## 결정 내용

- **수용된 사례 — 측정 방식 오류 정정**: 로드량 측정 기준을 소스 기준에서 배포본 기준으로 바꾼 결정. 이 불일치는 착수 시점에 이미 기록되어 관리 대상이었고, 판정식 문언 자체는 바꾸지 않았다(→ [[doc-line-count-source-vs-deploy-duality]]).
- **배제된 사례 — 목표치 하향**: 스폰 감축 완료기준(K4 평균 임계값)을 미달한 상황에서 목표치 자체를 낮추는 안은 사후 합리화로 읽혀 배제되고, 대신 미달을 그대로 인정하고 재설계를 후속으로 이월하는 안이 채택됐다(→ [[conditional-batch-output-cap-tradeoff]]).
- 두 사례 모두 담당자 단독으로 결정하지 않고, 선택지와 대가를 정리해 상위 소유자에게 에스컬레이션한 뒤 결정을 받았다.

## 영향 범위

이후 유사 상황(완료기준 미달 또는 측정 불일치 발견)에서 참조할 판단 경계다: 측정 오류 정정은 착수 전 기록 여부·판정식 불변 여부로 판별하고, 목표치 조정은 원칙적으로 담당자 단독 결정 대상에서 제외해 소유자 결정으로 넘긴다.

## 관련 페이지

- [[doc-line-count-source-vs-deploy-duality]]
- [[conditional-batch-output-cap-tradeoff]]
- [[fw-structure-p0-blueprint]]
