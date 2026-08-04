---
type: concept
title: 미설정 시 차단 vs 비차단 폴백 판정 기준
tags:
- code-scan
- configuration
- backward-compat
- task-080
- task-083
sources:
- task:080
- task:083
related:
- code-scan-sealed-decision-point-pattern
- code-scan-gate-deadlock-init-placement
- code-scan-nonblocking-limit-rollout
created: '2026-08-04'
updated: '2026-08-04'
status: draft
---
## 개요

설정값이 없을 때 도구가 취하는 태도는 "전 명령을 차단"과 "하위 단계로 조용히 폴백" 두 갈래로 나뉜다. code-scan은 같은 "설정 미존재" 상황에 대해 `headerSource`에는 전자를, `shardPolicy`에는 후자를 택했다 — 두 처방이 정반대인 이유는 값의 성질 차이에 있다.

## 결정 배경 (WHY)

`headerSource`(헤더를 인라인에 남길지 외부 지도에 남길지)는 프로젝트마다 완전히 다른 값이 정답일 수 있는 **추측 불가 값**이다. 도구가 임의로 하나를 가정하면 워커가 잘못된 위치에 헤더를 기록해 조회·검증이 조용히 어긋난다 — 그래서 080은 미설정을 전 명령 차단으로 두었다(근거: task:083 TASK.md 확정 방향 #7 "샤드 정책은 합리적 기본값이 존재하므로 추측 불가한 `headerSource`의 미설정 전면 차단과 성질이 다르다").

`shardPolicy`(바이트 상한·파일 수 하한)는 매니페스트 크기 분포를 실측해 도출한 **합리적 기본값**(10240바이트 / 40파일)이 이미 존재한다(근거: task:083 TASK.md 배경 분석 (1)~(4), 확정된 설계 방향 #1·#2). 이 값이 최적이 아니더라도 도구가 완전히 잘못된 방향으로 동작하지는 않는다 — 상한이 조금 크거나 작을 뿐 오탐/누락의 정도 차이지 정오답의 문제가 아니다. 그래서 083은 전역 설정 부재·JSON 파손·키 부재·타입 위반 4상태 전부를 비차단 폴백으로 두었다(근거: task:083 DONE.md §3.1 "전역 설정 부재·JSON 파손·키 부재·타입 위반 4상태 전부 비차단 폴백이다. `headerSource`의 미설정 전 명령 차단과 성질이 다르다").

## 결정 내용

일반화하면 판정 기준은 다음과 같다.

| 값의 성질 | 처방 | 예시 |
|---|---|---|
| 추측하면 틀릴 수 있는 이분법적 선택 — 잘못 가정하면 결과가 조용히 오염된다 | **미설정 시 전 명령 차단** | `headerSource` (inline vs manifest) |
| 합리적 기본값이 이미 실측으로 도출된 튜닝 파라미터 — 잘못 가정해도 정도 차이일 뿐 방향이 틀리지 않는다 | **미설정 시 비차단 폴백**(코드 상수) | `shardPolicy.maxBytes`/`minFiles` |

083은 이 구분을 3단 우선순위(`{프로젝트}/.opal/code-scan.json` > `~/.opal/setting.json` > 코드 상수)의 말단에 "추측이 아니라 실측 근거가 있는 기본값"을 두는 방식으로 구현했다 — 정책을 읽는 지점 1곳(`resolveShardPolicy`)이 이 폴백까지 포함해 판정한다(근거: task:083 PLAN §3.1.2 (E)).

## 영향 범위

새 설정 키를 도입할 때 "미설정을 차단할 것인가 폴백할 것인가"를 결정하는 재사용 가능한 판단 기준이다. 코드-스캔뿐 아니라 유사한 전역/프로젝트 2층 설정을 도입하는 모든 도구에 적용 가능하다. 단, 이 기준은 정적 판단이며 — 크기처럼 단조 증가하는 값의 경우 폴백을 유지하더라도 "언제 차단으로 승격할지"는 별도 순서 문제가 된다 → [[code-scan-nonblocking-limit-rollout]].

## 관련 페이지

- [[code-scan-sealed-decision-point-pattern]]
- [[code-scan-gate-deadlock-init-placement]]
- [[code-scan-nonblocking-limit-rollout]]
