---
type: concept
title: 할일-crud 시나리오는 현행에서도 checkpoint_commits 불합격
tags:
- opst
- scenario
- measurement
sources:
- task:176
related: [opal-skill-tester, model-effort-measurement-retains-current-config]
created: '2026-10-02'
updated: '2026-10-02'
status: draft
---
## 개요

opst의 `function-할일-crud` 시나리오는 현행 설정에서도 도구 체크포인트 커밋이 0건이어서 `checkpoint_commits` 기준에서 불합격한다. 따라서 이 시나리오의 품질 하한 판정은 변별력이 낮다.

## 결정 배경 (WHY)

- (근거: task:176 DONE.md 한계) 기준 2건을 포함해 측정 8건 모두 `checkpoint_commits`에서 불충족이었다. 설정과 무관한 기존 문제로 보이나 원인은 규명되지 않았다 (WHY 미확보).
- 후보 쪽에는 추가 불충족이 있었다: C2 1건 미완료, C3 1건의 `state_valid`·run-log 적체.

## 결정 내용

- 이 시나리오의 하한 판정은 "똑같이 실패하는 기준 대비"가 되므로 정보량이 낮다. 결론은 stockctl 쪽 지표와 분리해 읽는다.
- 이전 태스크(172)의 `test-cycle.md` 실호출 절이 `opal-agent` 경유를 요구하는 반면 opst 실행기는 raw `claude -p`를 쓰는 불일치가 있다 (근거: task:176 DONE.md). 체크포인트 커밋 0건과의 관련은 확인되지 않았다.

## 관련 페이지

- [[opal-skill-tester]]
- [[model-effort-measurement-retains-current-config]]
