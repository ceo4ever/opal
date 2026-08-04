---
type: concept
title: code-scan 매니페스트 샤딩 — 예약 폴더 경로 파생과 옵트인 하위호환
tags:
- code-scan
- sharding
- architecture
- task-082
- task-083
sources:
- task:082
- task:083
related:
- code-scan-tool
- code-header-dual-source-inheritance
- code-scan-classification-ladder-design
- code-scan-split-execution-precedes-block
created: '2026-08-03'
updated: '2026-08-04'
status: draft
---
## 개요

code-scan은 소스 디렉토리 하나마다 매니페스트 파일을 정확히 하나만 둔다는 규칙을 고정해 왔다. 이번 결정으로 그 매니페스트 하나를 예약 폴더 아래 의미 단위로 나눠 여러 파일에 분산할 수 있게 됐고, 이 매니페스트를 원래 열던 진입 경로는 그대로 유지된다.

## 결정 배경 (WHY)

실사용 프로젝트에서 매니페스트 하나가 86.4KB·292 엔트리까지 자랐고, 이를 열람한 워커가 모델 턴 1회에 600초 워치독을 초과해 강제 종료되는 사고가 발생했다(근거: task:082 DONE.md §1). 분산을 도입하면서도 도구가 새로운 경로 계산 규칙을 발명하지 않도록, 오늘 도구가 여는 진입 경로에서 순수 문자열로 파생되는 예약 위치 하나만 추가했다(근거: task:082 DONE.md §3).

## 결정 내용

- 진입 경로(원래 도구가 열던 매니페스트, 이하 "베이스 매니페스트")는 경로 계산 규칙이 그대로다. 새로 생기는 것은 그 경로 아래 예약 폴더 `_shards/`에 놓이는 나눠 담긴 파일들("샤드")뿐이다(근거: task:082 DONE.md §3).
- 샤드 파일은 베이스 매니페스트와 완전히 같은 형태를 재사용한다 — 신규 형식·신규 스키마를 만들지 않았다. 베이스 매니페스트에 추가된 것은 어떤 샤드들이 있는지 이름(라벨) 목록을 담는 배열 필드 하나뿐이다(근거: task:082 DONE.md §3 "스키마 추가는 키 1개").
- 조회는 베이스와 그 베이스가 선언한 전 샤드의 내용을 합쳐 하나로 취급한다. 라벨을 아직 선언하지 않은 파일은 계속 베이스로 모인다 — 새 파일이 어느 샤드에 속하는지를 도구가 패턴으로 추측하는 방식(글롭 라우팅)은 채택하지 않았다. 의미상 분할 경계를 정하는 것은 소유자의 몫으로 남긴다(근거: task:082 TASK.md 확정 방향 #8·#10, PLAN §1.5 U-3).
- 샤드 선언이 없는 기존 자산에서는 이 해석 경로 전체가 우회되어 오늘과 완전히 동일하게 동작한다(옵트인). → [[code-scan-sealed-decision-point-pattern]]에서 이 보증을 만드는 판정 지점을 다룬다.

## 영향 범위

`opal/tools/code-scan/code-scan.js`의 조회 8커맨드·`target`·`scaffold` 경로 전체(`resolveShards`, `opal/tools/code-scan/code-scan.js:1002`). 샤드를 선언하지 않은 스코프는 바이트 단위로 무변화가 보증된다.

이 페이지의 "의미상 분할 경계를 정하는 것은 소유자의 몫으로 남긴다"는 결정은 082 시점에는 분할을 실제로 수행하는 명령이 없었다는 뜻이기도 했다 — 083이 `code-scan split`(집행)·`split --plan`(제안 사다리)으로 그 실행 수단을 채워, "경계는 사람이 정하고 이동은 도구가 한다"는 역할 분담을 완성했다(근거: task:083 DONE.md §1, §3.3~3.4). → [[code-scan-classification-ladder-design]] · [[code-scan-split-execution-precedes-block]]

## 관련 페이지

- [[code-scan-tool]]
- [[code-header-dual-source-inheritance]]
- [[code-scan-sealed-decision-point-pattern]]
- [[code-scan-nonblocking-limit-rollout]]
- [[code-scan-classification-ladder-design]]
- [[code-scan-split-execution-precedes-block]]
