---
template: sdlc-v2
---
# TASK: 설계·구현 모델·effort 최적화 — opst 변형 측정과 적용

## Problem

캡틴은 설계를 좋은 모델·effort로 하고, 구현은 더 낮은 모델이나 effort로 빠르게 하되 품질은 유지하고 싶다. 하지만 지금 구성은 이 의도와 맞지 않고, 비교 측정할 수단도 없다.

- PM 경로(`actor=coordinator`)에서 PLAN·TEST-SCENARIO를 쓰는 주체는 worktree 세션의 PM이다(`opal/core/references/harness/actor.md` §PM 조율 계약). 그런데 이 세션은 builder 레벨인 `models.<provider>.standard`(Claude: sonnet)로 기동된다(`opal/tools/worktree-launcher/README.md` §builder 모델 기동 시점 주입, `opal/core/references/harness/worktree.md` §실행 세션 기동과 터미널 회수 경계). 설계에 좋은 모델(opus)을 쓰는 곳은 판정 evaluator뿐이다(`opal/agents/opal-evaluator-agent/AGENT.md` frontmatter).
- 구현 에이전트 `opal-task-agent`·`opal-be-agent`·`opal-fe-agent`는 모두 `model: standard`이고 effort를 선언하지 않아 호출 세션 설정을 따른다(각 `opal/agents/*/AGENT.md` frontmatter). 태스크 172는 판정 에이전트 2종만 측정해 effort를 고정했고, 나머지 에이전트는 effort 미선언을 유지했다(`tasks/172-261001-opd-검증-시간-단축/AGENTIC-LOG.md` #7).
- 판정 에이전트는 effort에 따라 소요 시간이 크게 달랐다. 170 측정에서 `xhigh`는 기본 대비 약 6배 느렸다(`tasks/170-261001-opds-설계-게이트-회차-단축/run/EVAL-RESULT.md`). 구현 에이전트는 측정된 적이 없다.
- `opal-skill-tester`(opst)는 모의 과업을 실제 Pilot 세션으로 끝까지 실행해 숨은 인수 테스트와 표준 지표로 채점한다. 하지만 비교 변형은 실행 커맨드만 바꿀 수 있고(`opal/skills/opal-skill-tester/SKILL.md:31`), 에이전트나 worktree 세션의 model·effort를 변형별로 바꾸는 기능은 없다.

## Proposed outcome

opst가 설계 주체(worktree 세션 PM)와 구현 에이전트의 model·effort를 변형별로 바꿔 같은 조건에서 비교 실행한다. 판정 쪽(evaluator·test-agent·convention-checker)은 고정하고, 각 실행에는 변형 설정과 배포된 FW 버전을 기록한다.

이 기능으로 "설계는 좋은 설정, 구현은 낮은 설정" 후보들을 현행과 측정한다. 숨은 인수 테스트 통과율과 준수 지표를 품질 하한으로 두고, 시간·비용·수정 반복 횟수를 비교한 결과를 캡틴에게 보고한다. 캡틴이 결정한 설계·구현 설정이 배포된 에이전트 정의와 worktree 세션 기동 설정에 반영되어, 호출 세션 effort와 무관하게 그 설정으로 실행된다.

## Affected users and systems

- 사용자: opd·opds·opd2로 태스크를 수행하는 캡틴·PM, 구현 에이전트(`opal-task-agent`·`opal-be-agent`·`opal-fe-agent`), worktree 세션 기동.
- 포함: `opal-skill-tester`(실행기·시나리오 변형 규격·지표·보고서), 구현 에이전트 정의의 model·effort, worktree 세션 기동 설정(`launcher` 모델·effort 주입과 `setting.json` 설정 키), 측정 기록, install 배포 검증.
- 제외: 판정 에이전트(evaluator·test-agent·convention-checker·security-checker)의 설정, 설계 게이트·TEST 판정 기준, opst 숨은 인수 테스트 내용, 기존 opst 시나리오의 과업 정의, 다른 Pilot(oppl·oppd·oppb)의 실행 구조.

## Constraints

- C-1: 측정 비교에서 판정 에이전트와 그 설정, 시나리오, 숨은 인수 테스트는 모든 변형에서 같게 고정한다.
- C-2: 품질 하한은 현행 설정 대비 숨은 인수 테스트 통과율과 opst 준수 지표가 떨어지지 않는 것이다. 이 하한을 만족하지 않는 후보는 결정 대상이 아니다.
- C-3: 측정은 후보 설정 3개 이하(현행 제외), 시나리오 2개 이하로 한정한다. 반복 횟수·총 실행 수·총 시간 상한은 PLAN에서 확정하고, 측정 실행 전에 캡틴 승인을 받는다.
- C-4: 측정 기간에는 배포된 FW를 다시 설치하지 않으며, 모든 측정 실행이 같은 배포 버전에서 수행됐음을 기록으로 확인한다. 모델 실호출은 `opal-agent` CLI를 사용한다(`opal/core/references/harness/test-cycle.md` §실호출 시나리오).
- C-5: 설정 변경은 캡틴이 결정한 값만 적용한다. 설치본과 상태 편집은 프로젝트 규칙을 따른다(`.opal/AGENT.md` §금지사항). 플랫폼별 모델·effort 값 변환은 install 어댑터와 launcher 설정 계층에만 둔다.

## Acceptance criteria

- AC-1: opst 비교 실행에서 변형마다 worktree 세션(설계 주체)과 구현 에이전트의 model·effort를 각각 지정할 수 있다. 지정하지 않은 에이전트와 판정 에이전트는 배포 설정 그대로 실행되며, 실제 적용된 설정이 실행 결과에 기록된다.
- AC-2: 각 측정 실행 결과에 배포 FW 버전이 기록되고, 비교 묶음 안에서 버전이 다르면 보고서가 그 비교를 무효로 표시한다.
- AC-3: 현행과 후보 설정의 측정 결과(숨은 인수 테스트 통과율, 준수 지표, 소요 시간, 비용, TEST 수정 반복 횟수, 반복 간 편차)가 하나의 비교 보고서로 캡틴에게 제시되고, 품질 하한 충족 여부가 후보별로 판정된다.
- AC-4: 캡틴이 결정한 설계 주체와 구현 에이전트의 model·effort가 배포된 에이전트 정의와 worktree 세션 기동에 반영되어, 새 worktree 태스크에서 실제로 그 설정으로 실행된다.
