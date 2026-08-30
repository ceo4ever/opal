---
type: concept
title: 스킬이 원문 인용하는 SSOT는 SSOT부터 고친다
tags:
- ssot
- skill-authoring
- citation
- pipeline
- task-104
sources:
- task:104
related:
- skill-owned-constraint-restated-in-prompt-overrides-skill
- new-ssot-pointer-not-value-copy
- skill-opal-pilot-data-design
created: '2026-08-30'
updated: '2026-08-30'
status: draft
---
## 개요

스킬이 상위 설계 SSOT 문서의 문장을 `[MUST]` 원문 인용으로 박아 두고 있으면, SSOT를 고치지 않고 스킬만 고치는 개정은 스킬이 자기 인용문과 모순되는 상태를 만든다. 두 문서를 함께 고쳐야 하고, 고치는 순서도 SSOT가 먼저여야 한다.

## 결정 배경 (WHY)

- (근거: task:104 TASK A-9, PLAN §2.5) opdd 파이프라인의 3모드 순차 규정과 QA 「단계 간 정합」 규정은 `opal-pilot-data-design/SKILL.md`가 `docs/proposals/opal-data-design.md`를 3곳(STEP 3 산문, STEP 3 PM Gate, STEP 5 QA)에서 `[MUST]` 원문 인용하고 있었다. 역공학 트랙을 도입하며 스킬의 실행 순서만 바꾸고 SSOT 원문을 그대로 두면, 스킬 안에서 "인용된 원문"과 "실제로 트랙 분기하는 산문"이 동시에 존재해 워커가 어느 쪽을 따를지 미정이 된다.
- (근거: task:104 PLAN §2.5) 개정 순서를 뒤집으면(스킬 먼저) 축자 불일치가 구조적으로 발생한다 — 스킬 작성자가 즉흥적으로 새 문장을 지어내고, 그 문장이 나중에 고칠 SSOT 원문과 우연히도 다를 위험이 항상 존재하기 때문이다.

## 결정 내용

- 개정을 2단계로 분리한다: (1) SSOT 문서의 확정 문안을 먼저 작성해 파일에 실제로 쓴다. (2) 스킬의 인용 지점이 그 확정 문안 문자열을 그대로 복사하게 한다.
- 축자 일치는 `grep -F` 완전일치로 검증한다 — 눈으로 대조하지 않고 도구로 결정론적으로 확인한다.
- SSOT 문서 중 이미 다른 곳에서 축자 인용되고 있는 문장(이번 사례에서는 「DICT가 MODEL을 선행한다」 등)은 절대 수정 금지로 못박는다 — 건드리면 인용하는 모든 지점이 동시에 파손된다.

## 영향 범위

- 상위 설계 SSOT 문서를 `[MUST]` 원문 인용하는 모든 스킬의 개정 작업. 인용 지점이 여러 곳(3곳 이상)일수록 순서를 지키지 않았을 때의 불일치 위험이 커진다.
- 이 원칙은 개정 순서(SSOT → 스킬)와 검증 방법(`grep -F` 완전일치)을 함께 요구한다 — 순서만 지키고 검증을 생략하면 사람이 손으로 옮겨 적는 과정에서 여전히 어긋날 수 있다.

## 관련 페이지

- [[skill-owned-constraint-restated-in-prompt-overrides-skill]]
- [[new-ssot-pointer-not-value-copy]]
- [[skill-opal-pilot-data-design]]
