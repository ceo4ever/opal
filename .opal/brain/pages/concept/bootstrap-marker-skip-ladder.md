---
type: concept
title: 부트스트랩 첫 줄 마커 3단 스킵 사다리 ([WORKER]/[ASSISTANT]/무마커)
tags:
- bootstrap
- 2tier
- assistant-tier
- headless
- pm-gate
- architecture
sources:
- task:051
related:
- opal-bootstrap-2tier-model
- opal-pm-promotion-gate
- opal-bootstrap-skip-gate
- brain-query-latency-model
created: '2026-07-02'
updated: '2026-07-02'
status: active
---

## 개요

OPAL 부트스트랩은 디스패치 프롬프트(또는 헤드리스 `-p` 프롬프트)의 첫 줄 마커로 로드 범위를 3단으로 구분한다. `[WORKER]`는 부트스트랩 전부(비서·PM tier 공통)를 스킵하고, `[ASSISTANT]`는 비서 tier(Phase A)까지만 로드하고 PM tier(Phase B) 승격을 억제하며, 마커가 없으면 비서+PM(Phase A+B, 프로젝트면 승격)이 그대로 진행된다. `[ASSISTANT]`는 049에서 확립된 2-tier 모델(비서/PM 분리, [[opal-bootstrap-2tier-model]])에 헤드리스 호출용 중간 단을 신설한 것이다(task:051 TASK.md §배경).

## 결정 배경 (WHY)

049 2-tier 모델은 PM 승격 게이트를 "`.opal/AGENT.md` 존재" 단일 신호로 정의했다([[opal-pm-promotion-gate]]). 이 신호는 인터랙티브 세션에는 맞지만, `claude -p` 헤드리스 호출에는 문제를 일으켰다 — 대시보드의 브레인 질의 어댑터가 `cwd=project_path`로 서브프로세스를 구동하는데, 프로젝트 cwd에 `.opal/AGENT.md`가 있으면 읽기전용 브레인 워커조차 무조건 PM tier까지 승격되어 구현금지 가드·디스패치 의무 같은 PM 전용 컨텍스트를 불필요하게 로드했다(근거: task:051 TASK.md §배경, `opal/core/AGENT.md:28`).

기존 스킵 경로 2종(`bootstrap:off` 세션 토글, `[WORKER]` 디스패치 마커)은 모두 all-or-nothing이라 "비서 tier만 켜고 PM은 끈다"는 중간 단을 표현할 수 없었다(근거: task:051 TASK.md §배경, PLAN §1 현재 상태). `[ASSISTANT]` 마커는 이 빈 중간 단을 채우는 결정이다.

이 결정의 본질은 **지연 단축이 아니라 tier 격리(정합성)** 다. 037 PoC 이후 콜드 지연 병목이 인-에이전트 멀티턴 루프에 있음이 이미 정정되어 있었고([[brain-query-latency-model]]), 부트스트랩 문서 로딩 자체는 병목이 아니다(자명 작업 ≈5초). `[ASSISTANT]` 캡의 목적은 읽기전용 워커가 자신을 PM으로 오인하는 tier 오염을 제거하는 것이며, 지연 레버는 `opbr --lite` 같은 별건으로 분리된다(근거: task:051 DONE.md §목표 달성, TASK.md §배경 분석 2).

대안으로 `--append-system-prompt` 주입안도 검토됐으나, 게이트에 앵커되지 않는 애드혹 자연어 주입이라 drift·비결정·비재사용 위험이 있어 기각되고 마커 방식이 채택되었다(근거: task:051 TASK.md §배경 분석 4).

## 결정 내용

3단 스킵 사다리는 `opal/core/AGENT.md`의 Phase B 승격 게이트 한 곳에 집중된다. 승격 신호는 "`.opal/AGENT.md` 존재 AND 첫 줄이 `[ASSISTANT]`가 아님"으로 재정의되어, 기존 신호에 억제 조건이 AND로 추가되는 형태다(`opal/core/AGENT.md:32`). 무마커 세션은 "첫 줄이 `[ASSISTANT]`가 아님"이 항상 참이므로 기존 승격 경로가 그대로 보존된다(회귀 0).

`[ASSISTANT]` 마커는 `[WORKER]` 마커와 직교하는 별도 스킵 경로다(`opal/core/AGENT.md:13`). `[WORKER]`는 PM이 컨텍스트를 직접 주입하는 워커용으로 아무것도 로드하지 않지만, `[ASSISTANT]`는 비서 tier 능력(보고 형식·도구 인지맵·`//` 커맨드/스킬 레지스트리 해석)을 유지한 채 PM tier만 억제한다. 마커는 프롬프트 최상단의 단독 줄이며, 그 이후 줄은 실제 요청으로 정상 처리된다. `//` 커맨드는 비서 tier가 보유한 능력이라 전제 조건이 없으므로(`opal/core/AGENT.md:15`), `[ASSISTANT]` 캡 상태에서도 `//opbr` 같은 `//` 커맨드가 정상 발동·완주한다(근거: task:051 PLAN §M-2, TASK.md §확정된 설계 방향).

완료 보고 표기 규칙도 확장되어, `[ASSISTANT]` 캡 세션은 비서 세션(`.opal/AGENT.md` 부재)과 동일하게 `harness`·`PM`·`PM모드`를 `⬜`로 표기한다(`opal/core/AGENT.md:83` 인접). 이 표기는 문서 변경이 실제 런타임 게이트 판단에 반영되는지를 self-confirming 없이 관측하는 근거로 쓰였다(task:051 DONE.md §동작 검증 실측).

## 첫 소비자 — 브레인 질의 어댑터

`[ASSISTANT]` 마커의 첫 적용 대상은 대시보드 브레인 질의 어댑터다. `-p` 프롬프트가 `'[ASSISTANT]\n//opbr query --read-only "<질의>"'` 형태로 구성되어, 첫 줄 마커로 PM tier 승격을 억제하면서 둘째 줄의 `//opbr` 커맨드는 비서 tier 능력으로 완주한다(`dashboard/backend/adapters/opbr_adapter.py:130`). 기존 `cmd` 배열·`shell=False`·`--allowedTools "Bash,Read,Grep,Glob"`·`--read-only` 계약은 이 변경으로 영향받지 않는다(`dashboard/backend/adapters/opbr_adapter.py:6,102-104,127-130`).

## 동작 검증

프로젝트 cwd(`.opal/AGENT.md` 존재)에서 `[ASSISTANT]` 프리픽스 프로브를 실행한 결과, 완료 보고가 `⬜ harness ⬜ PM ⬜ PM모드`로 나타났고 Read 파일 목록에 harness·opal-pm·프로젝트 `.opal/AGENT.md`가 포함되지 않았다. 동일 조건의 무마커 대조군 프로브는 `✅ harness ✅ PM ✅ PM모드`로 Phase B가 정상 로드되어 회귀 0이 확인되었다(task:051 DONE.md §동작 검증 실측).

## 영향 범위

- `opal/core/AGENT.md` — 설계원칙 박스 3단 사다리 명시, `[ASSISTANT 규칙]` 박스 신설, Phase B 게이트 억제 절, 완료보고 캡 세션 표기, 변경이력 v4.2
- `dashboard/backend/adapters/opbr_adapter.py` — `-p` 프롬프트 첫 줄 프리픽스, @header/docstring 캡 의도 서술
- 후속 액션: 캡틴의 canonical install 재배포 필요(`~/.opal/AGENT.md`는 검증용 dev-artifact 배포 상태), opbr_adapter 외 다른 headless `claude -p` 소비자 인벤토리 스캔은 범위 밖(task:051 DONE.md §후속 액션)

## 관련 페이지

- [[opal-bootstrap-2tier-model]]
- [[opal-pm-promotion-gate]]
- [[opal-bootstrap-skip-gate]]
- [[brain-query-latency-model]]
