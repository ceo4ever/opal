---
type: entity
title: opal-action-status
tags:
- skill
- oppl
- observability-boundary
- operator
sources:
- task:068
related:
- opal-action-monitor
- oppl-run-record-journal-dual-observability
created: '2026-07-18'
updated: '2026-07-18'
status: active
---
## 개요

루프 액션 에이전트가 실행되는 태스크의 진행 현황을 소유자(PM)가 한 번의 발동으로 확인할 수 있게 하는 경량 operator 스킬이다. 워커·파이프라인 디스패치 없이 읽기 전용으로 도구를 호출하고 결과를 해석해 보고하는 발동층 역할만 담당한다.

## 책임 (WHAT)

- 인자로 태스크 폴더가 주어지지 않으면 진행 중인 oppl 태스크를 자동 탐지한다 — 루프 루트(backlog.json 보유 폴더) 우선 탐색 후 하위 `.oppl-run/` 중 최신 채택, 미발견 시 전역 glob 폴백, 스캔 깊이 상한을 둔다(`opal/skills/opal-action-status/SKILL.md`).
- `opal-action-monitor --json`을 호출해 태스크의 단계×축 현황을 받고, loop 루트에 `backlog.json`이 있으면 `backlog-tool show`도 결합해 루프 전체 진행까지 한 번에 해석 보고한다.
- 도구가 `{"ok": false}` + 비정상 종료코드를 반환하면(폴더·`.oppl-run/` 부재) 성공으로 오인하지 않고 에러 메시지를 안내한 뒤 종료한다.
- 라이브 관측은 상주하지 않고 `--watch` 터미널 명령을 안내하는 것으로 위임한다.

## 설계 배경 (WHY)

- 067에서 관측 도구(opal-action-monitor)와 파일 규약(`.oppl-run/`)은 완성됐지만, 소유자가 이를 실제로 발동시키는 진입점이 없어 터미널 명령을 직접 치거나 알투에게 자연어로 요청해야 했다 — 이 공백을 메우는 것이 신설 이유다(근거: task:068 TASK.md 배경, PLAN.md §1.1).
- 도구(opal-action-monitor)는 렌더러, 스킬(opal-action-status)은 발동층이라는 역할 분리를 명명에도 반영했다 — 최초 후보명 `opal-monitor`는 도구명과 혼동 소지가 있어 캡틴이 `opal-action-status`(약어 opas)로 확정했다(근거: task:068 DONE.md 명명 절, PLAN.md 3.1.2).
- 수치·상태 판정 규칙·JSON 스키마는 도구 쪽 문서를 SSOT로 유지하고 스킬 본문에는 재서술하지 않는다 — 두 산출물 간 값 drift를 원천 차단하기 위한 결정이다(근거: task:068 PLAN.md §3.1.2 H-4).
- 커버리지는 현재 oppl(`.oppl-run/` 규약 준수 루프)에 한정되며, oppd·opsdd 쪽 액션 에이전트가 같은 규약으로 전환되면 스킬 자체는 무변경으로 커버리지가 확장되도록 설계했다 — 파일 규약 존재 여부만으로 렌더 대상을 판단하는 전방 호환 원칙이다(근거: task:068 PLAN.md §3.1.2 커버리지 경계, 후속 메모 `memory/후속_069_070_액션에이전트_관측_확장.md`).

## 관계 (HOW)

- [[opal-action-monitor]] — 이 스킬이 호출해 소비하는 렌더러 도구. 스킬은 이 도구의 `--json` 출력을 그대로 해석만 한다.
- [[oppl-run-record-journal-dual-observability]] — 이 스킬이 최종적으로 노출하는 관측 데이터(이벤트 로그·운행 일지)의 원 규약.

## 소스 커버리지

| 식별자 | 경로:줄번호 | 설명 |
|--------|-----------|------|
| `opal-action-status` (alias `opas`) | `opal/skills/opal-action-status/SKILL.md` | 스킬 본체 — operator 단일 라우터 |
| 레지스트리 엔트리 | `opal/core/references/opal-skills-registry.json` | alias `opas` 등록 (opal 그룹) |
