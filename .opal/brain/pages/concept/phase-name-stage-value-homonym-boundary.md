---
type: concept
title: 프로세스 표시명과 파이프라인 단계값의 동명이의 경계 — 개명 파급 판단 원칙
tags:
- pipeline
- naming
- state-tool
- lesson
- task-090
sources:
- task:090
related:
- opsdd-pipeline-ssot
- pipeline-json-spec
- pipeline-json-full-adoption-migration
created: '2026-08-13'
updated: '2026-08-13'
status: draft
---
## 개요

파이프라인 오케스트레이터마다 산문에서 부르는 진행 구간 이름과, 파이프라인 행이 실제로 갖는 단계값은 글자가 비슷할 뿐 서로 다른 개념 계층인 경우가 있다. 이 둘을 같은 것으로 보고 하나로 통일(개명)하려 하면 그 파급이 예상보다 훨씬 넓어진다.

## 결정 배경 (WHY)

- (근거: task:090 DONE.md D-7c) SDD 파이프라인은 산문에서 실행 구간을 "EXECUTE-LOOP"라 부르지만, 파이프라인 행이 갖는 단계값은 "EXECUTE"다. 전자는 반복 실행이라는 진행 방식을 설명하는 프로세스 이름이고, 후자는 행 하나하나가 속한 단계를 가리키는 값이다 — 같은 어근을 쓸 뿐 지시 대상이 다르다.
- (근거: task:090 DONE.md D-7c, §3 "건드리지 않은 것") 이번 태스크에서 두 표기를 하나로 통일했다면, 산문 표기가 등장하는 8개 파일 41곳이 함께 바뀌어야 했다 — 원래 하려던 "행 정의 이관"이라는 좁은 범위가 문서 전체 개편으로 번질 뻔했다.
- (근거: task:090 TASK.md/DONE.md §3 참고 사례) 같은 패턴이 다른 pilot에도 있다 — 개발 pilot의 산문 표기 "STEP 3.5 TEST-SCENARIO"와 프로젝트개발 pilot의 산문 표기 "Phase 2: WBS"도 각각 실제 단계값과 글자는 겹치지만 다른 계층에서 쓰인다.

## 결정 내용

- 산문에서 프로세스를 부르는 이름(표시용 레이블)과, 도구가 다루는 단계값(기계 판독용 목록값)은 서로 다른 개념 계층으로 취급한다. 하나를 바꾼다고 다른 하나를 자동으로 맞출 필요는 없다.
- 개명이 필요한지 판단할 때는 "이 표기가 몇 파일·몇 곳에 등장하는가"를 먼저 센 뒤, 그 개명이 원래 태스크 범위에 꼭 포함돼야 하는지를 따로 확인한다. 포함되지 않는다면 건드리지 않고 후속 과제로 넘긴다.

## 영향 범위

- SDD pilot의 산문 "EXECUTE-LOOP" 표기 17곳과 실행 가이드 문서는 이번 태스크에서 손대지 않고 그대로 유지했다(`opal/skills/opal-pilot-sdd/SKILL.md`, `opal/core/references/harness/execute-loop-guide.md`).
- 동일 패턴을 가진 개발 pilot·프로젝트개발 pilot의 산문 표기도 같은 이유로 범위 밖으로 유지했다.

## 관련 페이지

- [[opsdd-pipeline-ssot]]
- [[pipeline-json-spec]]
- [[pipeline-json-full-adoption-migration]]
