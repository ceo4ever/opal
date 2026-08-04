---
type: concept
title: 게이트 순환 안티패턴과 복구 명령 앞배치 해법
tags:
- code-scan
- architecture
- pattern
- task-080
- task-083
sources:
- task:080
- task:083
related:
- shard-policy-block-vs-nonblock-fallback-criterion
- code-scan-sealed-decision-point-pattern
created: '2026-08-04'
updated: '2026-08-04'
status: draft
---
## 개요

설정이 없으면 명령을 거부하는 차단 게이트를, 그 설정을 만들어 주는 복구 명령 자신에게까지 적용하면 "설정이 없어 복구 명령이 거부되고, 복구 명령을 못 돌려 설정을 못 만드는" 순환이 생긴다. 이 순환은 080이 만들었고 083이 `init` 서브명령을 차단 게이트 **앞** 분기에 배치해 끊었다.

## 결정 배경 (WHY)

080은 `headerSource` 미설정을 전 명령 차단으로 만들었다 — 추측 불가한 값이라는 것이 그 이유였다(→ [[shard-policy-block-vs-nonblock-fallback-criterion]]). 그런데 그 설정 파일 자체가 생기는 정의된 경로가 어디에도 없었다 — PM 프로세스(`opi`)에도, 도구 자신에도 설정을 최초 생성하는 수단이 없었다(근거: task:083 TASK.md F-9 "왜: 설정 파일이 생기는 정의된 경로가 없고(`opi`·도구 어디에도 없음), 080이 미설정을 전 명령 차단으로 만들어 구멍이 곧 막힘이 된다"). 결과적으로 이 구멍은 뚫려 있는 채로 막혀 있었다 — 이론적으로는 우회로가 없는 게 아니라(PM이 손으로 파일을 만들면 됨), **도구 스스로 자신의 전제 조건을 해소할 방법이 없는** 구조적 결함이었다.

083은 이 리스크를 P0로 명문화했다: "`init`이 `main()`의 전 명령 차단 게이트 뒤에 배치되면, `headerSource`가 없어서 `init`이 거부되고 `init`을 못 돌려서 `headerSource`를 못 만드는 순환이 생긴다 — 기능이 통째로 무용지물이 된다"(근거: task:083 PLAN §리스크 가설 H-22).

## 결정 내용

- `cmdInit`을 `main()`의 전 명령 차단 게이트(`code-scan.js:2362-2367`) **앞** 분기에 배치한다. 다른 12개 명령의 차단 동작은 바이트 단위로 불변이다 — `init`만 이 게이트를 우회하는 것이 아니라, **게이트가 요구하는 바로 그 값을 CLI 인자로 강제로 받는다**(근거: task:083 PLAN §3.12.2 (B) "게이트를 무력화하는 것이 아니라, 게이트가 요구하는 값을 CLI 인자로 직접 받는다").
- `init`은 대화형 프롬프트를 만들지 않는다 — `--header-source <inline|manifest>`가 없으면 추론하지 않고 즉시 exit 1로 거부하며 파일을 만들지 않는다(근거: task:083 PLAN §3.12.2 (A), `pm/code-scan-management.md:87` "도구는 이 질문을 하지 않는다 — 비대화형을 유지한다"). 이 값은 [[shard-policy-block-vs-nonblock-fallback-criterion]]에서 말하는 "추측하면 틀릴 수 있는 값"이므로, 게이트 순환을 끊는 방법은 추론이 아니라 **호출자(PM)가 사람에게 확인한 값을 인자로 전달**하는 것이다.
- `init`은 설정이 **없는** 트리와 **깨진**(JSON 파싱 실패·타입 위반) 트리 양쪽에서 동작해야 한다 — 후자를 위해 `cmdInit`은 `config.configError`를 참조하지 않고, 디렉토리 스캔 제외 목록도 `config.exclude`가 아닌 규약 고정 목록을 쓴다(근거: task:083 PLAN §3.12.2 (B) "`cmdInit`은 깨진 config에서도 동작해야 한다(복구 창구)"). `--force`는 기존 파일이 있을 때 백업(`.bak`, 원본과 바이트 동일) 후 덮어써 복구 창구를 겸한다.
- 차단 게이트가 보내는 에러 메시지의 `fix` 문구에 `init` 복구 명령을 안내에 추가했다 — 차단 자체를 완화하지 않으면서 빠져나가는 길을 알려주는 방식이다(근거: task:083 DONE.md §7 K-5).

## 영향 범위

"필수 설정이 없으면 차단"이라는 게이트를 도구에 도입할 때, 그 설정을 최초로 만들어 주는 복구 명령이 반드시 그 게이트의 **앞**에 위치해야 한다는 재사용 가능한 배치 원칙이다. 순환의 징후는 "차단 게이트를 통과해야 실행되는 명령 목록에, 그 게이트가 요구하는 값을 만들어 주는 명령 자신이 포함되어 있는가"로 점검할 수 있다.

## 관련 페이지

- [[shard-policy-block-vs-nonblock-fallback-criterion]]
- [[code-scan-sealed-decision-point-pattern]]
