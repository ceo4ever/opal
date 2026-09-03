---
type: concept
title: 레지스트리 확장은 스키마 교체보다 additive 필드 추가가 기능 후퇴를 막는다
tags:
- registry
- schema-evolution
- skill-registry
- task-105
sources:
- task:105
related:
- skill-registry-validate-extension
- community-skill-user-registry
created: '2026-09-03'
updated: '2026-09-03'
status: draft
---
## 개요

레지스트리·스키마를 확장해야 할 때, 외부에서 제시된 새 스키마로 통째로 교체하기보다 기존 검증 로직이 미지 필드를 무시하는 성질을 이용해 필드를 additive로 추가하는 쪽이 기존 기능을 보존하면서 더 적은 변경으로 확장을 달성할 수 있다.

## 결정 배경 (WHY)

(근거: task:105 DONE.md §3.2) 외부 스펙안은 `registry.yaml` + Project Registry 2단 구조 도입을 제안했다. 그러나 그 스키마에는 기존에 쓰이던 `commit_sha` 필드가 없었다 — 그대로 교체하면 현행 업데이트 확인(원격 커밋 조회 결과와 저장된 `commit_sha` 대조) 기능이 후퇴한다.

## 결정 내용

- 검증 함수(`validate()`)가 알려진 몇 개 필수 필드만 검사하고 나머지 미지 필드를 무시하는 성질을 확인한 뒤, 이 성질을 이용해 기존 필드 구성에 신규 필드 3개(신뢰도·능력·스캔 시각에 해당하는 필드)를 **추가로만** 붙였다(`opal/tools/skill-registry/skill-registry.js:435-462`).
- 결과적으로 스키마 교체 0건, 검증 함수 재작성 0건으로 확장이 끝났다. 기존 필드(`commit_sha`)가 그대로 보존돼 후퇴가 발생하지 않았다.
- **일반 원칙**: 외부 스펙·레퍼런스가 스키마 전체 교체를 제안할 때는, 먼저 (1) 기존 검증 로직이 실제로 무엇을 강제하는지, (2) 기존 스키마에 있는데 새 스키마엔 없는 필드가 무엇을 지원하고 있었는지를 확인한다. 검증이 미지 필드에 관대하면 additive 확장이 스키마 교체보다 위험이 낮고 변경 범위가 작다.

## 영향 범위

- `opal/tools/skill-registry/skill-registry.js` — `validate()` 미지 필드 관용 성질을 이용한 확장 사례
- 유사한 레지스트리·스키마 확장 결정 시 우선 검토할 패턴

## 관련 페이지

- [[skill-registry-validate-extension]]
- [[community-skill-user-registry]]
