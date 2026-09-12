---
type: concept
title: 실행 주체(actor) 축은 모드 축과 직교한다
tags:
- actor
- mode
- orthogonal-axis
- task-122
- pattern
sources:
- task:122
related:
- auto-approve-user-confirmation-axis-separation
- worktree-tool
- state-tool
- opal-self-pm
- self-pm-tool
created: '2026-09-12'
updated: '2026-09-12'
status: active
---
## 개요

파이프라인을 "누가 자율적으로 진행하는가"(모드 축)와 "누가 실제로 구현을 수행하는가"(실행 주체 축)는 서로 독립된 두 개의 축이며, 후자를 전자의 하위 옵션으로 우겨넣지 않는다. `--pm` 플래그는 모드도 워크스페이스 선택도 아닌 세 번째의 독립 축으로 신설됐다(근거: task:122 PLAN.md D-3).

## 결정 배경 (WHY)

- (근거: task:122 PLAN.md D-3) 실행 주체 축을 모드 플래그 개수 판정에 섞으면, 조합 가능성(예: `--pm --agentic --wt` 3축 동시 지정)이 "플래그 충돌"로 오판된다. 두 질문("얼마나 자율적인가" vs "누가 수행하는가")은 답이 서로 영향을 주지 않으므로 분리해야 한다.
- (근거: task:122 PLAN.md D-1) 이미 워크스페이스 축(`--wt`)이 이 문제를 겪었고, 전용 owner 문서(`harness/worktree.md`)로 원문을 단일화해 해소한 선례가 있다. 신규 축을 만들 때 이 선례를 처음부터 복제하면 같은 실수(원문 산재·직교성 누락)를 되풀이하지 않는다.
- (근거: task:093의 일반 지침, `[[auto-approve-user-confirmation-axis-separation]]`) "판정 축이 추가될 때 필터 하나를 더 넣는 것이 아니라 독립된 새 축을 추가하는 것으로 사고해야 한다"는 원칙이 이미 093에서 정립되어 있었다. actor 축 신설은 이 지침의 두 번째 적용 사례다.

## 결정 내용

`--wt`가 확립해 둔 4개의 서술 패턴을 actor 축에 그대로 복제해, 기본 경로(플래그 미지정)의 무변경을 보장했다.

| 패턴 | `--wt` 선례 | actor 축 적용 |
|---|---|---|
| 전용 owner 문서 | `harness/worktree.md` | `harness/actor.md`(신규) — actor 축 정의·지원 Pilot 폐쇄 목록·`--pm` 실행 계약·독립 검증 경계의 단일 SSOT (근거: task:122 PLAN.md D-1) |
| `pilot.start` required doc 등재 | worktree 문서가 이미 등재 | `events.json`의 `pilot.start` `required_docs`에 5번째 항목으로 `actor.md` 추가 — 모든 Pilot이 작업 전에 강제 로드 (근거: task:122 PLAN.md D-1, DONE.md §변경 파일) |
| 라우팅 계약의 "모드 플래그 개수 미포함" 조문 | `harness/modes.md` §라우팅 계약 조항 5(`--wt`) | 같은 절에 조항 8을 신설해 "`--pm`은 모드가 아니라 별도 실행 주체 축이므로 모드 플래그 개수에 포함하지 않는다"고 대칭 서술 (근거: task:122 PLAN.md D-3) |
| `state-tool init` 선택 인자 + 미지정 시 키 미생성 | `--worktree` 조건부 영속화 | `--actor {pm}` 선택 인자 신설. 지정 시에만 `state["actor"] = "pm"`을 쓰고, 미지정 시 `state.json`에 `actor` 키 자체가 생기지 않는다 — 행 구성·key·순서·STATE 렌더는 전부 무변경 (근거: task:122 PLAN.md D-4, `opal/tools/state-tool/state_tool.py:1422-1425` 패턴 재사용) |

지원 범위는 `opal-pilot-dev`(`opd`/`opds`) 하나로 닫힌 폐쇄 목록이며, 목록 밖 Pilot의 `--pm` 수신은 산문 통보(1행 확인)와 `state-tool`의 `actor_unsupported_for_skill` exit 1 거부 2중으로 막는다(근거: task:122 PLAN.md D-5).

## 영향 범위

`harness/actor.md`(신규 owner), `opal/core/references/events.json`(`pilot.start` required_docs), `opal/core/references/harness/modes.md`(라우팅 계약 조항 8), `opal/tools/state-tool/state_tool.py`(`--actor` 인자), `opal/skills/opal-pilot-dev/SKILL.md`(actor 분기 수직 접합). 향후 새 실행 축이 필요해질 때도 이 표의 4패턴을 재사용할 수 있는 템플릿이 된다.

## 관련 페이지

- [[auto-approve-user-confirmation-axis-separation]]
- [[worktree-tool]]
- [[state-tool]]
- [[opal-self-pm]]
- [[self-pm-tool]]
