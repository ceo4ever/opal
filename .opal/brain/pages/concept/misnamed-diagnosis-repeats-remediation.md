---
type: concept
title: 잘못된 이름으로 표면화된 결함은 정비를 반복시킨다
tags:
- diagnostics
- lint
- classification
- tooling
- lesson-learned
sources:
- skill:op-brain-ingest
- code:opal/tools/brain-tool/brain_tool.py
- doc:opal/core/references/pm/dispatch-process.md
related:
- silent-success-defect-class
- enforcement-basis-must-be-structural-not-voluntary
- eye-inspection-cannot-count-machine-check-at-close
created: '2026-08-27'
updated: '2026-08-27'
status: draft
---
## 개요

결함이 제 이름이 아닌 다른 이름으로 표면화되면, 검사를 몇 번 돌려도 원인이 보이지 않는다. 보고서에 항목이 뜨긴 하므로 「검사는 하고 있다」는 감각만 남고, 정비는 증상 쪽에서 반복된다.

## 결정 배경 (WHY)

- brain 무결성 검사는 링크·고아·근거 누락을 보지만 frontmatter 형식은 보지 않았다 — 검사 함수가 형식 검증을 호출하지 않았다.
- 그래서 붕괴한 관련 페이지 목록이 「형식 위반」이 아니라 **「본문에 링크가 없음」**으로 보고됐다. 슬러그가 들어갈 자리에 리스트가 통째로 찍힌 것이 유일한 흔적이었다.
- 그 이름을 그대로 믿고 정비를 두 회차 진행했다 — 링크 표기를 고치고, 본문에 링크를 채웠다. 증상은 줄었지만 원인은 그대로였다.
- 원인은 3회차에 형식을 직접 들여다본 뒤에야 드러났다. 검사 도구가 아니라 사람이 발견했다.

## 결정 내용

- 검사 도구가 여러 종류의 결함을 보고할 때, **분류 이름이 곧 진단명**이다. 잘못된 분류는 없는 것보다 나쁘다 — 없으면 찾아보지만, 틀리면 그 방향으로 시간을 쓴다.
- 조치는 검사 경로에 형식 검증을 편입하는 것이었다. 같은 검증이 페이지 생성 시점에는 이미 걸려 있었으므로, 규칙을 새로 만든 것이 아니라 **이미 있는 규칙을 두 번째 관문에도 연결**한 것이다.
- 함께 중복 보고를 억제했다 — 형식이 깨진 페이지는 형식 위반만 보고하고 증상 쪽 항목은 만들지 않는다. 원인과 증상이 나란히 뜨면 다시 증상을 고치게 된다.
- 일반화: 새 검증을 만들 때 「이 규칙을 어긴 데이터가 다른 검사에 어떤 이름으로 나타나는가」를 확인한다. 다른 이름으로 나타나면 그 검사에도 연결한다.

## 영향 범위

lint·validate·QA 게이트처럼 결함을 분류해 보고하는 모든 도구. 분류 체계에 빈칸이 있으면 그 결함은 사라지지 않고 **이웃 분류로 흘러들어** 오진을 만든다.

## 관련 페이지

- [[silent-success-defect-class]]
- [[enforcement-basis-must-be-structural-not-voluntary]]
- [[eye-inspection-cannot-count-machine-check-at-close]]
