---
type: concept
title: 콘솔 설정 화면 점진 확장 방침
tags:
- product-decision
- console
- scope
- security
sources:
- task:061
related:
- console-write-exception-router-isolation
- opal-console
- opal-security-model
created: '2026-07-14'
updated: '2026-07-14'
status: active
---
## 개념 요약

콘솔 설정 화면은 필요성이 확인된 기능만 하나씩 화면에 추가하고, JSON 설정 파일(console.config·프로젝트 로컬 설정)의 전반적인 편집은 화면 기능으로 만들지 않고 파일 수동 편집으로 유지한다는 소유자 방침이다(2026-07-14 확정).

## 배경·문제 (WHY)

- 설정 화면은 원래 프라임 풀 토글·console.config 전반 관리·프로젝트 로컬 설정 편집 3종을 함께 계획했다(근거: task:061 TASK.md "확정된 설계 방향").
- 구현이 진행되던 중 소유자가 범위 축소를 지시했다 — "복잡하니 이번엔 스위칭만 반영, JSON 수정은 수동으로, 화면에서 필요하면 기능을 하나씩 추가"(근거: task:061 TASK.md §범위 축소, 소유자 원문 인용).
- 축소 판단의 근거로 보안 측면도 함께 제시되었다 — 데몬이 무인증 로컬 서버(127.0.0.1)로 동작하므로, 당장 쓰이지 않는 쓰기 API를 화면에 노출하는 것 자체가 불필요한 공격 표면이 된다는 점이다(근거: task:061 AGENTIC-LOG #21).

## 결정 내용 (HOW)

- 이번 범위는 프라임 풀 토글 단일 기능만 화면·API로 유지한다.
- console.config 전반 편집 화면, 프로젝트 로컬 설정(`.opal/setting.local.json`) 편집 화면과 그 쓰기 API는 이번 범위에서 제외하고 구현분을 회수한다 — 회수된 설계·테스트는 폐기가 아니라 태스크 061 PLAN.md §3.3~3.4와 git 이력에 보존되어 후속 재활용이 가능하다.
- 향후 설정 화면 기능은 실제 필요가 확인될 때마다 하나씩 추가한다 — 사용 여부가 불확실한 쓰기 표면을 미리 넓혀두지 않는다.

## 영향·관계

- [[opal-console]]의 `dashboard/frontend/src/pages/settings/SettingsPage.tsx` — 토글 단일 섹션으로 축소된 화면.
- `dashboard/backend/routers/config.py` — 프라임 토글 엔드포인트만 유지, console.config 전반·프로젝트 로컬 설정 엔드포인트는 미노출.
- [[console-write-exception-router-isolation]] — 이 방침이 적용되는 쓰기 격리 패턴의 실제 노출 범위를 결정한다.
- [[opal-security-model]] — 무인증 로컬 데몬에서 미사용 쓰기 표면을 만들지 않는다는 이번 방침이 정합하는 보안 원칙.
- 후속 후보: console.config 전반 편집·프로젝트 로컬 설정 편집(재활용 가능한 설계는 task:061 PLAN.md §3.3~3.4에 보존).

## 근거 출처

task:061 TASK.md §범위 축소 · AGENTIC-LOG.md #20~22 · DONE.md §운영 기록·§잔여 후속 액션.
