---
type: concept
title: pilot 파이프라인 행 정의 SSOT 전면 단일화 — pipeline.json 10/10 전환
tags:
- pipeline
- state-tool
- ssot
- migration
- task-090
sources:
- task:090
related:
- pipeline-json-spec
- state-tool
created: '2026-08-13'
updated: '2026-08-13'
status: draft
---
## 개요

파이프라인 행 구성의 근거 문서가 두 갈래로 갈려 있었다 — pilot 4종은 `pipeline.json`을 읽었고, 나머지 6종은 SKILL.md 마크다운 표를 파서로 긁는 방식(구경로)에 여전히 의존하고 있었다. 이번 태스크에서 10개 pilot 전체가 `pipeline.json` 하나만을 읽도록 이관해, 행 구성 근거 문서가 프로젝트 전체에서 하나로 합쳐졌다.

## 결정 배경 (WHY)

- (근거: task:090 DONE.md §1) 구경로(표 파싱)는 섹션 헤딩과 표 헤딩의 정규식 불일치로 두 pilot(프로젝트루프·프로젝트개발)에서 태스크 시작 자체가 하드 실패하고 있었고, 파이프라인 목록을 관리하는 레지스트리 문서의 값도 실제 행 구성과 6건 드리프트·1건 결측을 내고 있었다.
- (근거: task:090 DONE.md D-4) 이관은 "형식 변경"으로 범위를 한정하고 행 구성 자체를 바꾸지 않는 것을 최우선 제약으로 두었다 — 파이프라인 내용이 달라지면 마이그레이션이 아니라 재설계가 되기 때문이다.
- (근거: task:090 DONE.md D-5) 기존 SKILL.md 표는 삭제하지 않고 미러(참고용 사본)로 남겼다 — 표 제거는 별도 후속 범위로 분리했다.

## 결정 내용

- 데이터설계·GC(스캔/체크/리포트)·기술문서작성·SDD·프로젝트루프·프로젝트개발 6개 pilot에 각자의 `pipeline.json`을 신설하고, 그 안의 행 정의가 이제 유일한 근거가 됐다.
- 구경로(SKILL.md 표 파싱)를 실제로 호출하는 곳은 레포 전체에서 0건으로 확인됐다 — 그 경로를 실행하는 코드 자체는 하위호환을 위해 남아 있지만, 실제로 쓰는 곳이 없다(근거: task:090 DONE.md §4 "잔존" 행).
- 파이프라인 목록을 관리하는 레지스트리 문서의 값도 각 파이프라인이 실제로 갖는 단계 목록에서 파생시켜, 값을 손으로 맞출 필요가 없게 했다(근거: task:090 DONE.md §3, §8).

## 영향 범위

- 6개 pilot의 SKILL.md와 신설 `pipeline.json`(`opal/skills/opal-pilot-{data-design,gc,write-tech,sdd,project-loop,project-dev}/references/pipeline.json`)
- 도구 레지스트리 문서(`opal/core/references/opal-skills-registry.json`), 도구 사용법 문서(`opal/core/references/tools.md`), 컨벤션 문서(`docs/CONVENTIONS.md`)의 관련 서술
- 후속 과제 수혜 범위 — 행 정의를 넘어 실행 스펙(담당 에이전트·모델·입출력)까지 승격하는 작업이 이제 4개가 아니라 10개 pilot 전체에 적용 가능해졌다(근거: task:090 DONE.md §8)

## 관련 페이지

- [[pipeline-json-spec]]
- [[state-tool]]
