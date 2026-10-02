---
template: sdlc-v2
---
# TASK: opd2 PLAN 사전심사 — 재검증 절차 정합·회차 상한·지적 해소 추적

## Problem

opd2는 BUILD 진입 전에 PLAN 사전심사를 한다. 1층은 완료조건이 계획 검증에 모두 덮였는지 도구가 확인하고, 2층은 독립 Reviewer 두 명(Call A·B)이 의미를 심사한다. 태스크 170이 opd·opds 설계 게이트에 넣은 보완이 opd2에는 없고, 절차 문서도 도구 동작과 맞지 않는다.

- 문서와 도구가 어긋난다. 절차 문서는 "실패한 Call만 다시 돌리고 통과한 Call은 재실행하지 않는다"고 안내한다(`opal/skills/opal-pilot-dev2/agents/coordinator.md:34-36`). 그런데 PLAN 단계 지문에는 현재 plan 해시가 들어간다(`opal/skills/opal-pilot-dev2/scripts/lifecycle.py:228-229`). 실패를 고치려고 plan을 바꾸면 통과했던 Call 기록이 무효가 되고, 전이는 두 Call 모두 현재 지문에서 pass를 요구한다(`lifecycle.py:310-314`). 문서대로 하면 전이에서 막히고, 약속한 비용 절감도 일어나지 않는다.
- 사전심사 재시도에 상한이 없다. 문서는 재시도가 기존 재작업 상한(3회)을 공유한다고 하지만(`coordinator.md:37`), 도구는 되돌리기(rewind)할 때만 횟수를 센다(`lifecycle.py:542-543`). 그래서 Reviewer가 계속 fail을 주면 plan 수정과 재심사가 끝없이 반복될 수 있다.
- 이전 지적이 해소됐는지 추적하지 않는다. Reviewer의 fail 사유는 자유 서술로만 남고(`lifecycle.py:483`) 다음 회차로 넘어가지 않는다. 다음 Reviewer는 앞선 지적이 고쳐졌는지 보고할 의무가 없어서, 같은 지적이 반복되거나 해소 확인이 누락될 수 있다. 태스크 170은 opd·opds 설계 게이트에 이전 지적 전달과 해소 보고, 지적 형식을 넣어 이 문제를 풀었다(`tasks/170-261001-opds-설계-게이트-회차-단축/DONE.md:9-10`).

## Proposed outcome

- opd2 절차 문서가 안내하는 PLAN 사전심사 재검증 방법을 그대로 따르면 BUILD로 넘어갈 수 있다. 문서가 실제 게이트와 다른 절차를 안내하지 않는다.
- PLAN 사전심사 fail이 정해진 상한에 이르면 opd2가 더 진행하지 않고 사용자 결정을 기다린다. 사용자가 명시적으로 해제해야만 다시 진행된다.
- Reviewer의 fail 지적은 정해진 형식으로 남고, 다음 회차 Reviewer는 직전 회차 지적 하나하나의 해소 여부를 보고한다. 보고가 빠지거나 맞지 않으면 그 심사 기록은 받아들여지지 않는다.

## Affected users and systems

- 사용자: opd2로 개발 태스크를 진행하는 캡틴과 PM(Coordinator), opd2가 호출하는 Reviewer 역할.
- 포함: `opal/skills/opal-pilot-dev2/`의 PLAN 사전심사 관련 절차 문서(`SKILL.md`·`agents/coordinator.md`·`agents/reviewer.md`), 상태기계 도구(`scripts/lifecycle.py`)와 필요한 스키마·테스트, install 배포 확인.
- 제외: opd·opds 설계 게이트와 `op-scenario-gate`·`opal-evaluator-agent`, opd2 VERIFY·REVIEW 단계, opd2 역할을 정식 에이전트로 등록하거나 역할별 effort를 적용하는 일(별도 태스크), 배포·관측(RELEASE·OBSERVE) 경로.

## Constraints

- C-1: opd2의 기존 기계 게이트는 약해지지 않는다. 완료조건 커버리지 검사, 아티팩트 지문 결합, 구현자·검증자·리뷰어 분리, 되돌리기 재작업 상한, state-tool 단일 상태 연동이 지금과 같이 집행된다.
- C-2: 이 변경 전에 만들어진 opd2 원장도 그대로 읽히고 재개된다.
- C-3: 프로젝트 공통 계약을 따른다 — 배포 경계와 플랫폼 분기 금지(`.opal/AGENT.md` §금지사항), 상태 변경은 state-tool로만(`.opal/AGENT.md` §프로젝트별 추가 지침).

## Acceptance criteria

- AC-1: opd2 절차 문서에 적힌 PLAN 사전심사 재검증 방법을 따라 fail을 고치고 다시 심사받으면 PLAN→BUILD 전이가 성공한다. 문서는 통과한 Call 기록이 plan 수정 후에도 유지된다고 안내하지 않는다.
- AC-2: PLAN 사전심사 fail이 상한 3회에 이르면 그 뒤의 재심사 기록과 BUILD 전이가 거부되고 태스크가 사용자 결정 대기 상태가 된다. 사용자의 명시 해제 뒤에만 사전심사를 다시 진행할 수 있다.
- AC-3: Reviewer의 fail은 위치와 남은 선택이 드러나는 정해진 형식의 지적 항목으로 기록된다. 다음 회차 같은 Call의 심사 기록은 직전 fail 지적 전건의 해소 여부를 포함해야 하며, 누락되거나 지적 집합과 맞지 않으면 그 기록이 거부된다.
