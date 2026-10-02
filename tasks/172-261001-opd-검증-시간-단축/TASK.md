---
template: sdlc-v2
---
# TASK: 검증 시간 단축 — 실호출 최소화·컨벤션 검사 경량화·판정 병렬화

## Problem

opd·opds의 검증 단계(설계 게이트·TEST·컨벤션 검사)가 실제 결함 탐지에 비해 시간을 많이 쓴다.

- **에이전트 실호출 시나리오.** 태스크 170의 S-6은 이전 회차 지적 전달(AC-4)을 확인하려고 evaluator를 실제로 두 번 차례로 디스패치했다(`tasks/170-261001-opds-설계-게이트-회차-단축/TEST-SCENARIO.md` S-6). evaluator 1회는 47~61초가 걸렸다(같은 태스크 `run/EVAL-RESULT.md` baseline 행). 테스트 에이전트는 다른 에이전트를 디스패치할 수 없어 S-6이 blocked 되었고, PM이 직접 수행했다(`c547d9b0`·`74f0ce01`). 독립 검증 경계에서 벗어난 예외다(`opal/core/references/harness/actor.md` §독립 검증 경계). 반면 `design-gate record`는 evaluator 결과를 파일로 받는다(`opal/tools/state-tool/state_tool.py` `--evaluator-result`). 시나리오 가이드에는 "가장 저렴한 계층" 원칙만 있고 실호출에 대한 기준이 없다(`opal/skills/op-dev-test-scenario/references/test-scenario-guide.md:83`).
- **evaluator 권고 미발생.** 170 설계 게이트 6회차 동안 `advisories`는 모든 회차에서 0건이었다(`tasks/170-*/run/design-gate-i1~i6.json`). `cheaper_layer` 기준이 일반적이라 실호출 시나리오가 지적되지 않았다(`opal/agents/opal-evaluator-agent/AGENT.md:92`).
- **이전 지적 조립이 산문 규칙이다.** 이전 회차 지적(`previous_gaps`)을 찾아 evaluator 입력에 넣는 규칙이 `op-scenario-gate` SKILL 산문에만 있다. 그래서 결정론으로 시험할 수 없고, PM이 매 회차 추론해 조립한다(170 S-7은 grep으로 문구만 확인한다).
- **컨벤션 검사가 파일 전체를 읽는다.** 검사 절차는 대상 파일마다 전체를 Read한다(`opal/skills/op-gc-convention/SKILL.md:46`). `state_tool.py`는 8,178줄이고 7행(@header) 하나만 23KB인데, 170은 이 중 약 40줄만 바꿨다. 152~169 기록 16건에서 게이트를 막은 지적은 162의 High 2건뿐이고 둘 다 `@header 규칙` 위반이었다. 나머지는 Medium 이하였다(`tasks/1[56]*/gc-findings-convention-*.json`). 그런데도 기계적 규칙까지 모델이 판단한다.
- **판정 에이전트 effort가 고정되지 않았다.** checker(`model: standard`)와 evaluator(`model: advanced`)는 effort를 실제 값으로 지정하지 않는다. evaluator의 `effort: default`는 배포할 때 생략되는 표시용 값이라, 실제로는 부른 세션 설정을 따른다(`scripts/install-mac.sh:519` `OPAL_ADAPTER_FIELD_SPEC`). 170 측정에서 effort `xhigh`는 기본보다 6배 느렸다(`run/EVAL-RESULT.md`).
- **설계 판정이 한 번에 하나씩 돈다.** `design-rubric` evaluator는 설계 4축과 시나리오 3축을 한 번의 디스패치로 판정한다(`opal/skills/op-scenario-gate/SKILL.md:203`). 170은 두 판정을 병렬 2콜로 나누려 했지만 결합 규칙과 이전 지적 처리의 세부 결정이 3회 연속 미흡해 철회했다(`tasks/170-*/AGENTIC-LOG.md` #4·#9, `PLAN.md` §범위 밖 제안).
- **TEST 시나리오가 순차 실행된다.** 테스트 에이전트의 독립 시나리오 실행을 병렬로 할 수 있는지 확인된 적이 없다(`opal/agents/opal-test-agent/AGENT.md` §실행 프로세스).

## Proposed outcome

에이전트 실호출이 필요한 검증은 모델 판단 자체가 수용 기준일 때로 한정된다. 전달 경로·입력 조립·출력 형식·기록은 미리 만든 결과 파일로 결정론 시험을 하고, evaluator는 이런 시나리오를 더 싼 계층 권고로 지적한다. 이전 회차 지적의 조립은 도구가 결정론으로 수행해 시험할 수 있고, PM의 매 회차 추론이 사라진다.

컨벤션 검사는 변경 구간과 필요한 문맥만 읽고, 기계적 규칙은 결정론 사전 검사가 같은 finding 형식으로 판정한다. checker와 evaluator는 측정 근거로 정한 model·effort로 호출 세션과 무관하게 실행되고, 나머지 에이전트의 effort 정책도 실제로 효과가 있는 방식으로 정리된다.

설계 게이트의 설계 판정과 시나리오 판정은 병렬로 수행되고, 결합 결과는 지금과 같은 판정 기준과 기록 계약을 따른다. TEST의 독립 시나리오 병렬 실행 가능 여부가 실측으로 판정되고, 가능하면 TEST 절차에 적용된다.

## Affected users and systems

- 사용자: opd·opds·opd2로 태스크를 수행하는 캡틴·PM, `opal-evaluator-agent`·`opal-convention-checker`·`opal-test-agent`, 그리고 effort 정책 대상인 `opal/agents/` 전 에이전트.
- 포함: `op-dev-test-scenario` 가이드, `opal-evaluator-agent` 정의(권고 기준·병렬 판정 입력·model·effort), `op-scenario-gate` 스킬, `state-tool` 설계 게이트 명령(입력 조립·결합), `harness/design-gate.md`·`harness/scenario-gate.md`·`harness/test-cycle.md`, `op-gc-convention` 스킬과 결정론 사전 검사 도구, `opal-convention-checker` 정의, `opal-test-agent` 정의, `opal/agents/*/AGENT.md` effort 필드, `scripts/install-mac.sh` 어댑터의 effort 처리, 평가 세트와 측정 기록, install 배포 검증.
- 제외: 설계 4축·시나리오 3축·pass 조건·반복 상한 3회·`reset --owner user`, 컨벤션 기준 문서(`docs/CONVENTIONS.md`)의 규칙 내용, `gc-finding-schema.md` 필드와 판정표, oppl·oppd·oppb 경로의 게이트, 이미 잠긴 과거 태스크 산출물.

## Constraints

- C-1: 설계 게이트·목표-커버 게이트의 판정 기준(설계 4축·시나리오 3축·pass 조건), 반복 상한 3회, `reset --owner user` 전용 해제, `design-gate record`의 결과 검사 순서·오류 코드는 바꾸지 않는다(`opal/core/references/harness/design-gate.md`).
- C-2: 컨벤션 검사의 finding 스키마와 PASS/PASS_WITH_ADVISORIES/FAIL/INCOMPLETE 판정은 바꾸지 않는다(`opal/core/references/harness/gc-finding-schema.md`). 결정론 사전 검사는 같은 스키마로 finding을 낸다.
- C-3: model·effort 하향은 평가 세트에서 결함을 하나도 놓치지 않은 후보 가운데 캡틴이 결정한 값만 적용한다. 컨벤션 checker는 결정론 사전 검사와 합쳐 High 이상 누락 0건이 조건이다. 결정 전에는 현행을 유지한다.
- C-4: 독립 검증 경계를 유지한다. TEST 실행·판정과 설계 판정은 서브에이전트가 수행하고, PM이 직접 수행하는 예외를 새로 만들지 않는다(`opal/core/references/harness/actor.md` §독립 검증 경계).
- C-5: 설치본과 상태 편집은 프로젝트 규칙을 따른다(`.opal/AGENT.md` §금지사항). `~/.opal/`은 직접 수정하지 않고, 플랫폼 분기는 install 어댑터 계층에만 둔다.

## Acceptance criteria

- AC-1: TEST-SCENARIO 작성 기준이 에이전트 실호출을 모델 판단 자체가 수용 기준인 경우로 한정한다. 그 외 전달·조립·형식·기록 검증은 기록된 결과 파일 기반 결정론 시나리오로 안내하며, 실호출을 쓰면 1회 제한과 표시를 요구한다.
- AC-2: evaluator는 실제 에이전트·외부 서비스를 호출하는 시나리오가 기록된 결과로 같은 계약을 증명할 수 있으면 `cheaper_layer` advisory를 낸다. 그런 시나리오를 포함한 문서 묶음에서 실제로 advisory가 반환된다.
- AC-3: 설계 게이트의 이전 회차 지적 조립(`previous_gaps` 선택·evaluator 입력 구성)을 도구가 결정론으로 수행한다. 같은 이력에서 항상 같은 입력을 만들고, 이 동작을 실호출 없이 시험할 수 있다.
- AC-4: 컨벤션 검사가 기준 커밋 대비 변경 구간과 필요한 문맥만 검사 입력으로 사용한다. 변경 구간 밖의 기존 코드는 새 finding의 대상이 되지 않는다.
- AC-5: 기계적으로 판정 가능한 컨벤션 규칙(최소 @header 존재·형식, frontmatter 필수 키, 수기 변경이력 절 금지, 네이밍 패턴)이 결정론 사전 검사로 같은 finding 스키마에 판정되고, 모델 검사는 나머지 규칙만 맡는다. 과거 High 2건(162 `@header 규칙`)이 사전 검사에서 재현된다.
- AC-6: 평가 세트(과거 기록 기반 통과·결함 사례와 구현 규칙 위반 합성 사례)로 컨벤션 checker 후보 model·effort와 evaluator effort 후보를 측정해 판정 일치·결함 누락·소요 시간을 캡틴에게 보고하고, 캡틴이 결정한 값이 설치된 에이전트에 반영되어 호출 세션 effort와 무관하게 실행된다.
- AC-7: `opal/agents/` 전 에이전트의 effort 표기가 배포 결과에 실제로 영향을 주는 방식으로 정리된다. 표시용 `default` 값이 배포에서 조용히 사라지는 상태가 남지 않는다.
- AC-8: 설계 게이트의 설계 판정과 시나리오 판정이 병렬로 수행되고, 두 결과가 결정론 규칙으로 하나의 `design-gate record` 결과로 결합된다. 결합 결과의 verdict·rewrite_target·이전 지적 해소 보고는 단일 판정과 같은 계약을 만족한다.
- AC-9: TEST에서 독립 시나리오의 병렬 실행 가능 여부가 실측으로 판정된다. 가능하면 TEST 절차가 의존 관계와 공유 자원이 없는 시나리오를 병렬 실행하고, 불가능하면 그 근거와 대안이 기록된다.
