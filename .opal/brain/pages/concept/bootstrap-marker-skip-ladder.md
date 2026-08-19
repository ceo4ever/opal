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
- task:059
related:
- opal-bootstrap-2tier-model
- opal-pm-promotion-gate
- opal-bootstrap-skip-gate
- brain-query-latency-model
created: '2026-07-02'
updated: 2026-08-20
status: active
---

## 개요

OPAL 부트스트랩은 디스패치 프롬프트(또는 헤드리스 `-p` 프롬프트)의 첫 줄 마커로 로드 범위를 3단으로 구분한다. `[WORKER]`는 부트스트랩 전부(비서·PM tier 공통)를 스킵하고, `[ASSISTANT]`는 비서 tier(Phase A)까지만 로드하고 PM tier(Phase B) 승격을 억제하며, 마커가 없으면 비서+PM(Phase A+B, 프로젝트면 승격)이 그대로 진행된다. `[ASSISTANT]`는 049에서 확립된 2-tier 모델(비서/PM 분리, [[opal-bootstrap-2tier-model]])에 헤드리스 호출용 중간 단을 신설한 것이다(task:051 TASK.md §배경).

## 결정 배경 (WHY)

049 2-tier 모델은 PM 승격 게이트를 "`.opal/AGENT.md` 존재" 단일 신호로 정의했다([[opal-pm-promotion-gate]]). 이 신호는 인터랙티브 세션에는 맞지만, `claude -p` 헤드리스 호출에는 문제를 일으켰다 — 대시보드의 브레인 질의 어댑터가 `cwd=project_path`로 서브프로세스를 구동하는데, 프로젝트 cwd에 `.opal/AGENT.md`가 있으면 읽기전용 브레인 워커조차 무조건 PM tier까지 승격되어 구현금지 가드·디스패치 의무 같은 PM 전용 컨텍스트를 불필요하게 로드했다(근거: task:051 TASK.md §배경, `opal/core/AGENT.md:28`).

기존 스킵 경로 2종(`bootstrap:off` 세션 토글, `[WORKER]` 디스패치 마커)은 모두 all-or-nothing이라 "비서 tier만 켜고 PM은 끈다"는 중간 단을 표현할 수 없었다(근거: task:051 TASK.md §배경, PLAN §1 현재 상태). `[ASSISTANT]` 마커는 이 빈 중간 단을 채우는 결정이다.

이 결정은 **tier 격리(정합성)**를 목적으로 설계됐다. 다만 **지연 단축이 실제 효과로 함께 나타났다** — 브레인 질의 콜드 지연의 실제 병목이 헤드리스 호출 시의 부트스트랩 전체 로딩이었기 때문이다(소유자 확인 2026-08-20). 037 PoC가 병목을 인-에이전트 멀티턴 루프로 지목한 것은 **오진**이었고, 그 정정 경위는 [[brain-query-latency-model]]에 기록했다 — 당시 이 문서가 인용한 "부트스트랩 문서 로딩은 병목이 아니다"는 전제 자체가 틀린 것이었다.

대안으로 `--append-system-prompt` 주입안도 검토됐으나, 게이트에 앵커되지 않는 애드혹 자연어 주입이라 drift·비결정·비재사용 위험이 있어 기각되고 마커 방식이 채택되었다(근거: task:051 TASK.md §배경 분석 4).

## 결정 내용

3단 스킵 사다리는 `opal/core/AGENT.md`의 Phase B 승격 게이트 한 곳에 집중된다. 승격 신호는 "`.opal/AGENT.md` 존재 AND 첫 줄이 `[ASSISTANT]`가 아님"으로 재정의되어, 기존 신호에 억제 조건이 AND로 추가되는 형태다(`opal/core/AGENT.md:32`). 무마커 세션은 "첫 줄이 `[ASSISTANT]`가 아님"이 항상 참이므로 기존 승격 경로가 그대로 보존된다(회귀 0).

`[ASSISTANT]` 마커는 `[WORKER]` 마커와 직교하는 별도 스킵 경로다(`opal/core/AGENT.md:13`). `[WORKER]`는 PM이 컨텍스트를 직접 주입하는 워커용으로 아무것도 로드하지 않지만, `[ASSISTANT]`는 비서 tier 능력(보고 형식·도구 인지맵·`//` 커맨드/스킬 레지스트리 해석)을 유지한 채 PM tier만 억제한다. 마커는 프롬프트 최상단의 단독 줄이며, 그 이후 줄은 실제 요청으로 정상 처리된다. `//` 커맨드는 비서 tier가 보유한 능력이라 전제 조건이 없으므로(`opal/core/AGENT.md:15`), `[ASSISTANT]` 캡 상태에서도 `//opbr` 같은 `//` 커맨드가 정상 발동·완주한다(근거: task:051 PLAN §M-2, TASK.md §확정된 설계 방향).

완료 보고 표기 규칙도 확장되어, `[ASSISTANT]` 캡 세션은 비서 세션(`.opal/AGENT.md` 부재)과 동일하게 `harness`·`PM`·`PM모드`를 `⬜`로 표기한다(`opal/core/AGENT.md:83` 인접). 이 표기는 문서 변경이 실제 런타임 게이트 판단에 반영되는지를 self-confirming 없이 관측하는 근거로 쓰였다(task:051 DONE.md §동작 검증 실측).

## 첫 소비자 — 브레인 질의 어댑터

`[ASSISTANT]` 마커의 첫 적용 대상은 대시보드 브레인 질의 어댑터다. `-p` 프롬프트가 `'[ASSISTANT]\n//opbr query --read-only "<질의>"'` 형태로 구성되어, 첫 줄 마커로 PM tier 승격을 억제하면서 둘째 줄의 `//opbr` 커맨드는 비서 tier 능력으로 완주한다(`dashboard/backend/adapters/opbr_adapter.py:130`). 기존 `cmd` 배열·`shell=False`·`--allowedTools "Bash,Read,Grep,Glob"`·`--read-only` 계약은 이 변경으로 영향받지 않는다(`dashboard/backend/adapters/opbr_adapter.py:6,102-104,127-130`).

## 동작 검증

프로젝트 cwd(`.opal/AGENT.md` 존재)에서 `[ASSISTANT]` 프리픽스 프로브를 실행한 결과, 완료 보고가 `⬜ harness ⬜ PM ⬜ PM모드`로 나타났고 Read 파일 목록에 harness·opal-pm·프로젝트 `.opal/AGENT.md`가 포함되지 않았다. 동일 조건의 무마커 대조군 프로브는 `✅ harness ✅ PM ✅ PM모드`로 Phase B가 정상 로드되어 회귀 0이 확인되었다(task:051 DONE.md §동작 검증 실측).

## opal-agent 도구 표면 — 마커 프로그래밍 인터페이스

부트스트랩 마커 계층은 task:051에서 인터랙티브 세션(`.opal/AGENT.md` 부재 및 `-p` 프롬프트 프리픽스)의 선택 없는 게이트로 설계되었으나, task:059에서 opal-agent 도구가 이를 프로그래머 제어 파라미터로 노출했다. 소유자는 `--opal-bootstrap on|assistant|off`로 부트스트랩 로드 범위를 명시적으로 지정할 수 있으며, 이를 통해 서브에이전트 호출·자동화·도구 체이닝에서 tier를 동적으로 선택할 수 있다(근거: `opal/tools/opal-agent/opal_agent.py` §AgentConfig, task:059 PLAN §3.1).

동일 변경에서 opal-agent는 caller-supplied cold session id 지정(`--session-id <uuid>`)도 추가했다. 이는 부트스트랩 마커 설계(tier 격리)와는 직교하지만, 동일 워크플로에서 "비서 tier 진입 + 신규 세션 생성"을 함께 제어해야 하는 브레인 질의(opbr) 워커의 요구에 응한 것이다. cold=caller-supplied id, warm=resume 기존 세션의 상호배타 설계로 회귀 0이 달성되었다(근거: task:059 PLAN §M-3/M-4/M-5).

## 영향 범위

- `opal/core/AGENT.md` — 설계원칙 박스 3단 사다리 명시, `[ASSISTANT 규칙]` 박스 신설, Phase B 게이트 억제 절, 완료보고 캡 세션 표기, 변경이력 v4.2
- `dashboard/backend/adapters/opbr_adapter.py` — `-p` 프롬프트 첫 줄 프리픽스, @header/docstring 캡 의도 서술
- `opal/tools/opal-agent/opal_agent.py` — task:059에서 `--opal-bootstrap` 3-way 노출 및 `--session-id` 파라미터 추가
- 후속 액션: 캡틴의 canonical install 재배포 필요(`~/.opal/AGENT.md`는 검증용 dev-artifact 배포 상태), opbr_adapter 외 다른 headless `claude -p` 소비자 인벤토리 스캔은 범위 밖(task:051 DONE.md §후속 액션)

## 관련 페이지

- [[opal-bootstrap-2tier-model]]
- [[opal-pm-promotion-gate]]
- [[opal-bootstrap-skip-gate]]
- [[brain-query-latency-model]]
