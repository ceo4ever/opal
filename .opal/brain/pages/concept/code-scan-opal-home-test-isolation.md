---
type: concept
title: 전역 홈 파일 읽기 테스트 격리 — OPAL_HOME 주입 + 가짜 홈 5종
tags:
- code-scan
- testing
- pattern
- task-083
sources:
- task:083
related:
- code-scan-sealed-decision-point-pattern
- shard-policy-block-vs-nonblock-fallback-criterion
created: '2026-08-04'
updated: '2026-08-04'
status: draft
---
## 개요

도구가 개발자 실제 홈(`~/.opal/`)의 전역 설정 파일을 읽기 시작하는 순간, 테스트 결과가 그 개발자의 로컬 환경 상태에 좌우될 위험이 생긴다 — 로컬에서는 GREEN인데 CI에서는 RED(또는 그 반대)가 되는 결함이다. 083은 `OPAL_HOME` 환경변수 주입과 5종의 가짜 홈 픽스처로 이 위험을 격리했다.

## 결정 배경 (WHY)

083의 `resolveShardPolicy`는 3단 우선순위의 중간 단계로 `~/.opal/setting.json`을 읽는다(→ [[code-scan-sealed-decision-point-pattern]]) — code-scan이 전역 파일을 읽는 첫 사례다. 이 신규 I/O가 테스트에 그대로 노출되면, 테스트를 실행하는 사람마다 `setting.json`에 무엇이 들어있는지가 달라 같은 테스트 코드가 다른 결과를 낸다 — 083은 이를 P0 리스크로 명문화했다: "개발자 실제 홈 `~/.opal/setting.json` 내용이 테스트 결과에 유입 → 로컬 GREEN·CI RED(또는 그 반대)"(근거: task:083 PLAN §리스크 가설 H-4).

## 결정 내용

- 홈 경로 해석 함수(`resolveOpalHome`)가 `OPAL_HOME` 환경변수를 최우선으로 읽고, 없으면 `os.homedir()`을 폴백으로 쓴다 — 이미 `state_tool.py`가 같은 규칙("경로는 `OPAL_HOME` env 우선, `~/.opal` 하드코딩 분기 금지")을 쓰고 있어 그 관용을 그대로 재사용했다(근거: task:083 PLAN §3.2.2 (A)).
- 테스트 하네스는 `spawnSync` 호출마다 `OPAL_HOME`을 **가짜 홈 경로**로 주입한다. 기본값은 `setting.json`이 아예 없는 빈 트리(`homes/absent`)로 — "전역 정책이 없는 상태"가 대부분의 기존 테스트가 암묵적으로 전제하던 상태이기 때문이다(근거: task:083 PLAN §3.8.2 (B) "기본 격리... 전역 정책이 없는 상태가 모든 기존 테스트의 암묵 전제이므로 기본값이 그것이어야 한다").
- 가짜 홈은 상태별로 **5종**(`absent`·`valid`·`broken`·`nokey`·`badtype`) 픽스처로 나뉘어 각 상태에서의 동작을 개별 검증한다 — 부재/정상/파손 JSON/키 없음(`bootstrap`·`models`만)/타입 위반 5가지가 전역 설정이 취할 수 있는 실제 상태 전부이기 때문이다(근거: task:083 PLAN §3.8.1 신규 픽스처 표, §3.8.2 (B) 전역값 경로 검증).
- 적용 범위는 정책을 소비하는 명령(`validate`·`scaffold`·`split`)뿐 아니라 **조회 전용 테스트 파일도 일괄 포함**한다 — 예외를 두면 나중에 새 명령이 추가될 때 그 파일만 격리가 새는 지점이 되기 때문이다(근거: task:083 PLAN §3.8.2 (B) "조회 전용 파일도 일괄 주입한다 — 예외를 만들면 나중에 명령이 추가될 때 격리가 새는 지점이 된다").
- **실제 홈 파일은 절대 변조하지 않는다.** 배포 경계 준수를 위해, "실 홈 값과 무관하게 결과가 동일하다"는 사실은 실 홈을 읽기만 해서 확인하고, 실제 대조 검증은 가짜 홈 2종을 비교하는 방식으로 대체한다(근거: task:083 PLAN §3.8.2 (B) "[MUST]... 실 홈 파일을 변조하지 않는다 — 변조 대조는 가짜 홈 2종 비교로 대체한다"). PM 독립 재실행에서도 실 `~/.opal/setting.json`의 키(`bootstrap`·`models`)가 변조 0건임을 별도로 확인했다(근거: task:083 DONE.md §5.1).

## 영향 범위

도구가 프로젝트 경계 밖의 전역/사용자 설정 파일을 처음 읽기 시작할 때 반드시 함께 설계해야 할 테스트 전략이다 — 환경변수로 경로 주입 창구를 만들고, 그 설정이 취할 수 있는 상태(부재/정상/파손/키부재/타입위반)마다 전용 픽스처를 두면, 실제 개발자 홈을 변조하지 않고도 전역 경로를 결정론적으로 검증할 수 있다.

## 관련 페이지

- [[code-scan-sealed-decision-point-pattern]]
- [[shard-policy-block-vs-nonblock-fallback-criterion]]
