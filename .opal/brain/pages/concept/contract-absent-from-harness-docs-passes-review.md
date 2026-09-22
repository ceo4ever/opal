---
type: concept
title: 규범 문서에 없는 계약은 리뷰를 통과한다
tags:
- contract
- harness
- review
- deployment-gap
- task-150
- lesson
sources:
- task:150
related: [lease-handoff-before-terminal-launch, ownership-tool]
created: '2026-09-22'
updated: '2026-09-22'
status: draft
---
## 개요

계약이 코드에만 있고 규범 문서에 없으면 그 계약을 어기는 변경이 리뷰를 통과한다. 리뷰어가 읽을 근거가 없기 때문이다.

## 관측된 사례

`--wt` 소유권 교착(태스크 150)의 근본 원인이 이것이었다. lease는 태스크 138이 코드로 도입했고 claim·heartbeat·release·classify가 모두 구현돼 있었다. 그런데 `grep -rln lease opal/core/references/harness/`가 **0건**이었다 — 언제 누가 소유권을 잡고 언제 넘기는지가 규범 문서 어디에도 없었다.

그 결과 `harness/task-process.md`의 `--wt` 순서(스텝 5 `state init` → 스텝 5.5 기동)가 "허브가 먼저 lease를 잡고 나서 실행 주체를 띄운다"는 뜻이 된다는 사실을 아무도 판정하지 않았다. 순서 문서와 소유권 코드가 각자 정합했지만 둘을 겹쳤을 때 교착이 되는 것은 어느 쪽 문서에도 없었다.

## 왜 늦게 드러났나

집행자가 배포되기 전까지 증상이 없었다. lease는 만들어지고 있었지만 그것을 근거로 차단하는 가드가 사용자 환경에 배포되지 않아 워크트리 세션이 그냥 통과했다. 가드가 배포된 뒤 첫 `--wt` 태스크에서 교착이 드러났다.

**표시만 있고 집행이 없는 기간은 결함을 숨긴다.** 코드 머지 시점과 배포 시점이 다르면 그 사이 실행은 결함을 관측하지 못한다.

## 대응

- 규범 계약을 신설할 때 코드와 문서를 같은 작업 단위로 묶는다.
- 문서 존재 자체를 기계 검사로 고정한다. 태스크 150은 `grep -rln lease <규범 디렉터리>` 1건 이상을 시나리오 완료 기준에 넣었다. 문구 검사는 동작 증거가 아니지만, **계약 문서의 존재**는 문구로만 판정할 수 있는 드문 대상이다.
- 훅 배선(`claude-hooks.json`)을 바꾸는 변경은 새 세션부터 적용되고, 그 배선이 호출하는 파일만 바꾸는 변경은 즉시 적용된다. 어느 쪽인지에 따라 "언제부터 집행되는가"가 달라지므로 배포 계획에서 구분한다.

## 적용 범위

도구가 집행하는 모든 계약. 특히 순서·소유권·상태 전이처럼 두 문서가 각자 정합해도 겹치면 모순이 되는 축.

## 관련

- 이 교훈을 드러낸 구체 사례의 설계는 [[lease-handoff-before-terminal-launch]]가 다룬다.
- 문서에 없던 계약을 코드로 갖고 있던 도구는 [[ownership-tool]]이다.
- 규범 문서 작성 규칙은 `opal/core/references/opal-doc-standard.md`가 소유한다(brain page 미보유).
