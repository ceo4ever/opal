---
type: entity
title: opal-action-monitor
tags:
- tool
- oppl
- observability-boundary
- monitor
sources:
- task:067
related:
- oppl-run-record-journal-dual-observability
- opal-agent-stream-json-passthrough
- opal-loop-action-agent
created: '2026-07-17'
updated: '2026-07-17'
status: active
---
## 개요

루프 액션 에이전트가 남기는 결과 파일 규약 v2 산출물(이벤트 로그·운행 일지 등)을 읽어, 태스크 하나의 단계×축 진행 현황을 한 번의 명령으로 보여주는 읽기 전용 관측 도구다. 소유자(PM)가 실행 중인 에이전트에게 직접 묻는 대신 이 도구로 파일 기반 진행 상황을 확인하는 것이 [[oppl-run-record-journal-dual-observability]]가 규정한 관측 원칙의 실제 구현체다.

## 책임 (WHAT)

- 태스크 폴더의 실행 산출물 디렉토리를 스캔해 6개 단계(생성자 초안·시나리오·게이트·구현·테스트·규칙검사)별 상태를 판정한다.
- 종료코드 파일 존재/부재와 값(0/1/2), 산출물 존재 여부를 근거로 6가지 상태(진행중/대기/완료/실패/하드에러/차단)를 구분해 표시한다 (`opal/tools/opal-action-monitor/opal_action_monitor.py`).
- 이벤트 로그를 역순으로 훑어 가장 최근 의미 있는 이벤트(도구 호출·도구 결과·최종 결과)를 한 줄 요약으로 뽑아낸다 — 알 수 없는 이벤트 타입은 방어적으로 일반 표기로 낮춘다.
- 운행 일지의 최근 항목을 하단에 함께 보여주고, 차단 기록이 있으면 전체 배너로 강조한다.
- `--json`(1회성 기계 판독 출력)과 `--watch`(주기적 재렌더, 상한 도달 시 자동 종료)를 지원한다.
- 폴더 부재 등 입력 오류는 `{"ok": false, ...}` 에러 계약 + 비정상 종료코드로 반환한다.

## 설계 배경 (WHY)

- 실행 중인 에이전트에게 직접 질의하는 방식은 관측 경계를 넘는다 — 소유자가 결과 파일이라는 SSOT를 경유해서만 진행 상황을 확인하도록 하는 것이 이 도구를 만든 이유다(근거: task:067 PLAN§3.3.2, DONE.md 핵심 설계 결정).
- 산출물 판정 대상 파일(이벤트 로그·단일 결과 파일·운행 일지)이 이미 [[oppl-run-record-journal-dual-observability]]에서 규약으로 확정돼 있었기 때문에, 이 도구는 그 규약을 소비하는 독립 리더로만 설계됐다 — opal-agent와 직접 호출·임포트 관계를 맺지 않는다(근거: task:067 PLAN§2.3.3).
- 최초 작성 시 이름은 임시로 붙었으나, 이후 다른 액션 에이전트에도 공용으로 쓰일 것을 대비해 현재 이름으로 다시 지어졌다(근거: task:067 DONE.md 변경 파일 표, 캡틴 지시에 의한 추가작업).

## 관계 (HOW)

- [[oppl-run-record-journal-dual-observability]] — 이 도구가 파싱하는 파일 규약(이벤트 로그·운행 일지)을 정의하는 선행 결정.
- [[opal-agent-stream-json-passthrough]] — 이 도구가 읽는 이벤트 로그를 생성하는 실행 경로.
- [[opal-loop-action-agent]] — 이 도구가 관측 대상으로 삼는 실행 주체.

## 소스 커버리지

| 식별자 | 경로:줄번호 | 설명 |
|--------|-----------|------|
| `opal-action-monitor` | `opal/tools/opal-action-monitor/` | 도구 디렉토리 (신규, task:067 리네임) |
| 등록 | `opal/core/references/tools.md`, `opal/core/references/opal-harness.md` §9 | 도구 레지스트리 등록 항목 |
