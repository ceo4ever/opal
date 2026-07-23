---
type: concept
title: 레거시 행번호 파이프라인에 게이트 행 삽입 시 전수 수정 결합 회귀
tags:
- state-tool
- pipeline
- legacy-row
- regression
- scenario-gate
- task-075
sources:
- task:075
related:
- state-tool-task-step-key-address
- opsdd-pipeline-ssot
- pipeline-json-spec
- scenario-gate-pilot-fit-criteria
created: '2026-07-23'
updated: '2026-07-23'
status: draft
---
## 개요

파이프라인 정의를 아직 구조화 SSOT(pipeline.json)로 전환하지 않고 SKILL.md 마크다운 표를 리터럴 행번호(`--row N`)로 참조하는 pilot에 게이트 행을 삽입하면, 삽입 지점 이후의 모든 행번호가 밀려 본문 전 구간의 `--row N`·`#N`·`--after N` 리터럴을 전수 수정해야 한다. task:075의 opsdd 접합에서 이 결합 회귀 위험(최고 리스크)이 실제로 발생했고, 전수 수정으로 흡수했다. 이는 key 주소 체계(pipeline.json) 전환이 이런 삽입 결합을 왜 없애는지를 반증으로 보여준다.

## 결정 배경 (WHY)

- opsdd는 파이프라인 현황판을 SKILL.md 자신의 마크다운 표로 유지하고, `--rows-from`가 그 표를 파싱하는 레거시 경로다. 본문 전 구간이 `--row 15`·`#18~#19`·`--after 17`처럼 숫자 주소로 작성돼 있었다(근거: task:075 PLAN §2.3.2, `opal/skills/opal-pilot-sdd/SKILL.md`).
- REVIEW에 게이트 2행(결정론 커버리지 행 + 목표-커버 게이트 행)을 삽입하려면 24행이 25행으로 늘고, 삽입 지점 이후 행을 참조하던 모든 리터럴이 +1씩 밀린다. 한 곳이라도 누락하면 이후 단계의 mark가 엉뚱한 행을 성공적으로 갱신해 파이프라인이 조용히 깨진다(근거: task:075 PLAN 리스크 H-3, §3.3.2).
- 반면 key 주소 체계로 전환된 pilot은 행 참조가 안정적인 key(`{stage}.{item}`)라 행 삽입 시 순번이 밀려도 본문 명령이 무영향이다 — opds 접합이 그러했다(근거: task:075 PLAN §3.2.2, [[state-tool-task-step-key-address]]).

## 결정 내용

- opsdd는 최소변경 원칙에 따라 pipeline.json 전환을 이번 범위에서 제외하고, 레거시 표 유지 상태로 `--row N` 리터럴을 전수 대조·수정하는 방식으로 게이트를 삽입했다(근거: task:075 DONE.md §2 R-3, PLAN §3.3.2).
- 회귀 방어 기준: 삽입 후 `--rows-from` init의 행 개수 파싱이 정상값(25)으로 나오고 이후 단계 행 참조가 정합함을 완료 조건으로 삼았다(근거: task:075 PLAN §3.3.2, DONE.md §2 R-5).
- 일반 교훈: 레거시 행번호 참조 pilot에 행을 삽입하는 작업은 "삽입 1건 = 전수 수정 N건"의 결합을 강제한다. 이 결합 자체가 파이프라인 정의를 구조화 SSOT + 안정 key로 분리해야 하는 근거다.

## 영향 범위

- `opal/skills/opal-pilot-sdd/SKILL.md` — 레거시 표 파싱 pilot, 게이트 삽입 시 `--row N`·`#N`·`--after N` 전수 수정(task:075 수정 대상).
- opsdd는 key 주소 체계(그룹 A) 전환 대상에 아직 포함되지 않은 pilot이다(근거: [[state-tool-task-step-key-address]] §영향·관계 후속 범위).

## 관련 페이지

- [[state-tool-task-step-key-address]]
- [[opsdd-pipeline-ssot]]
- [[pipeline-json-spec]]
- [[scenario-gate-pilot-fit-criteria]]
