---
type: concept
title: opal-agent stream-json 실행 경로 — 원본 이벤트 passthrough 결정
tags:
- opal-agent
- stream-json
- observability-boundary
- headless-channel
sources:
- task:067
- task:131
related:
- oppl-run-record-journal-dual-observability
- opal-action-monitor
- oppl-internal-channel-opal-agent
created: '2026-07-17'
updated: '2026-09-14'
status: active
---
## 개념 요약

opal-agent(claude 헤드리스 CLI 채널)에 opt-in 스트리밍 실행 경로를 신설해, 루프 액션 에이전트가 디스패치하는 비동기 축 작업을 실행 도중에도 관측 가능하게 만든 결정 묶음이다. 기존 일괄 실행 경로(`--json`)와 5필드 반환 계약은 하위호환으로 그대로 유지된다.

## 배경·문제 (WHY)

기존 opal-agent 채널은 프로세스 종료 후에만 결과를 확인할 수 있는 블랙박스였다. 장시간 실행되는 비동기 축(생성자·Evaluator·test-agent 축)에서 "지금 무엇을 하고 있는가"를 실행 중에 들여다볼 방법이 없었다 (근거: task:067 DONE.md 요약, TASK.md 배경). 이 문제를 풀기 위해 표준출력을 한 줄씩 즉시 흘려보내는 증분 실행 경로가 필요했다.

## 결정 내용 (HOW)

- **산출물 writer 소유권은 opal-agent 프로세스다(R-ASYNC 전환, task:131)**: 초기 결정(task:067)은 opal-agent가 파일을 열지 않고 각 줄을 자기 표준출력으로 흘려보내면 호출하는 쪽이 셸 리다이렉트로 받아 적는 방식이었다. 현재는 opal-agent가 실행 디렉토리·단계 이름·재시도 접미를 인자로 받으면 산출물 파일을 스스로 만들고 열고 닫는다. 세 인자를 주지 않으면 기존 표준출력 흘려보내기가 그대로 동작한다. **전환 근거**: 확장자와 실제 직렬화의 불일치를 거부하려면 실행기가 호출 모드를 알아야 하는데, 호출자가 리다이렉트 대상만으로 모드를 정하는 구조에서는 이 검사가 성립하지 않는다. **원 결정의 실질 근거는 보존된다** — 파일 하나의 writer가 항상 프로세스 하나라는 성질이 그대로이고, 동시 쓰기 충돌 부재도 유지된다. 교환한 것은 결합 억제뿐이다. 실행 중 관측 창을 죽이지 않기 위해 스트림 파일만 줄 단위로 이어 쓰고, 종료코드와 동기 결과 파일은 임시 기록 후 원자적 교체를 쓴다.
- **원본 이벤트 무정규화 결정(R-EVSCHEMA)**: opal-agent는 중간 스트리밍 이벤트를 요약·가공하지 않고 그대로 흘린다. 완료 판정에 필요한 5개 필드(텍스트 결과·세션 ID·에러 여부·비용·소요시간)만 마지막 결과 이벤트 줄에서 추출한다. 트레이드오프는 명확하다 — 헤드리스 CLI의 이벤트 스키마가 바뀌어도 opal-agent가 받는 영향은 마지막 한 줄의 파싱뿐이며, 중간 이벤트를 해석하는 부담은 이 정보를 소비하는 관측 도구([[opal-action-monitor]])가 방어적으로 떠안는다. 정규화 요약 로직을 opal-agent에 넣지 않기로 한 이유는, 그렇게 하면 헤드리스 CLI 스키마 변경 취약성이 opal-agent 쪽으로 옮겨오기 때문이다(근거: task:067 PLAN§3.1.2 결정 R-EVSCHEMA).
- **verbose 옵션 자동 부착**: 스트리밍 실행 모드를 요청하면 필요한 부가 옵션을 자동으로 함께 조립해, 옵션 누락으로 인한 사용법 오류를 코드 내부에서 원천 차단한다(근거: task:067 PLAN§3.1.2 결정 R-VERBOSE).
- **완료 마커 불변**: 완료 판정은 여전히 종료코드 파일의 존재 여부로만 이루어진다 — 이벤트 로그 파일의 존재/비존재로 완료를 판정하지 않는다([066계승] 불변, 근거: task:067 PLAN§3.2.2 H-10).

## 영향·관계

`opal/tools/opal-agent/opal_agent.py`가 개조 본체다. 이 결정으로 생긴 이벤트 로그 산출물은 [[oppl-run-record-journal-dual-observability]]가 정의하는 결과 파일 규약 v2에 편입되고, [[opal-action-monitor]]가 이를 읽어 상태 판정·현황판 렌더에 사용한다. 기존 채널 전환 결정([[oppl-internal-channel-opal-agent]])의 3-분리 캡처·완료 마커 규칙은 이번 확장에서도 불변으로 유지된다.

## 근거 출처

task:067 — TASK.md §제약, PLAN.md §3.1.2(결정 R-ASYNC, R-EVSCHEMA, R-VERBOSE), DONE.md 요약·핵심 설계 결정.
