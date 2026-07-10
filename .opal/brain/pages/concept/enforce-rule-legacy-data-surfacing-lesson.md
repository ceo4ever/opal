---
type: concept
title: enforce 규칙 신설 시 잔존 데이터 표면화 — 배포 전 실 데이터 스캔 필요 교훈
tags:
  - lesson
  - enforce
  - validate
  - brain-tool
sources:
  - task:053
related:
  - brain-validate-flatness-enforcement
  - brain-tool
created: "2026-07-10"
updated: "2026-07-10"
status: active
---

## 개요

새로운 결정론적 enforce 규칙(validate 등)을 도구에 추가하면, 그 규칙을 실 저장소의 기존 데이터에 적용하는 순간 이전에는 조용히 통과하던 잔존 오류가 신규 violation으로 일괄 표면화된다. task:053에서 이 현상이 두 단계로 반복 발생했다(R-K1 1페이지 4항목 → ADD-1 7페이지 24항목). 배포 전 실 데이터 스캔·정비를 같은 태스크에서 함께 처리해야, 무결성을 집행하는 도구가 배포 직후 스스로 위반을 만들어내는 자기모순을 피할 수 있다.

## 결정 배경 (WHY)

task:053은 brain의 `related` 프론트매터에 위키링크 문법(`[[...]]`)이 quoted string으로 잘못 기입된 손편집 오류 3페이지 6항목을 정규화하고, `validate`에 링크필드 값 검사를 신설해 재발을 막는 것이 목표였다. 그러나 PLAN 단계에서 실 저장소를 스캔한 결과 TASK가 포착하지 못한 4번째 페이지(`skill-opal-pilot-data-design.md`)의 `.md` 접미사 4항목이 발견됐다(R-K1). PM은 이를 캡틴에게 에스컬레이션해 승인받아 정규화 범위에 포함시켰다. (근거: task:053 AGENTIC-LOG #3)

EXECUTE 단계에서 강화된 `validate`를 실 `.opal/brain` 전체에 실행하자, opdd 클러스터 7페이지에서 동일한 `.md` 접미사 related 24항목이 추가로 표면화됐다 — R-K1 승인분보다 훨씬 큰 규모의 잔존 데이터였다. 이는 TASK 범위 밖이라 워커는 조치하지 않고 캡틴에게 재차 에스컬레이션했고(#6), "추가작업으로 즉시 정비"가 승인되어 ADD-1로 해소됐다. (근거: task:053 AGENTIC-LOG #5·#6, ADD_DONE-1.md)

## 결정 내용

### 패턴 정의

1. 도구에 새 결정론적 검사(enforce)를 추가하면, 검사 로직 자체는 신규 데이터에 대해서만 테스트되기 쉽다.
2. 하지만 검사는 배포 즉시 실 저장소의 모든 기존 데이터에도 적용된다 — 이전에는 조용히 통과하던 손편집·레거시 오류가 일괄 violation으로 드러난다.
3. 표면화 규모는 사전에 정확히 예측하기 어렵다 — task:053에서는 처음 추정한 1건(R-K1)이 실행 중 24건(ADD-1)으로 확대됐다.

### 대응 원칙

- **배포 전 실 데이터 스캔**: 새 enforce 규칙을 배포하기 전에 실 저장소 전체에 해당 검사를 시험 적용해 잔존 위반 규모를 먼저 파악한다.
- **같은 태스크에서 정비**: 스캔으로 드러난 잔존 오류는 별도 태스크로 미루지 않고 같은 태스크에서 함께 정비한다 — 그렇지 않으면 "무결성을 집행하는 도구가 배포 직후 스스로 위반을 만들어낸다"는 자기모순이 남는다.
- **스코프 확장은 에스컬레이션**: 잔존 범위가 원래 TASK 범위를 초과하면 PM이 자율 확장하지 않고 캡틴에게 승인을 구한다(모호하면 에스컬레이션 기본 원칙). task:053은 이 원칙을 두 차례(R-K1, ESCALATION #6) 준수했다.

## 영향 범위

- `opal/tools/brain-tool/brain_tool.py` — `validate_frontmatter` 링크필드 검사 신설이 이 표면화를 유발한 변경
- `.opal/brain/pages/` — R-1(3페이지) + R-K1(1페이지) + ADD-1(7페이지) 총 11페이지 34항목 정비로 해소

## 관련 페이지

- [[brain-validate-flatness-enforcement]] — 이번 교훈이 확장한 enforce 설계 결정
- [[brain-tool]] — 잔존 데이터를 표면화시킨 도구
