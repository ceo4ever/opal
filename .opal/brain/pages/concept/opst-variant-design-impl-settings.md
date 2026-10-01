---
type: concept
title: opst 변형 설정 design=/impl= 문법
tags:
- opst
- variant
- model
- effort
sources:
- task:176
related: [opal-skill-tester, dispatch-model-overrides-agent-frontmatter, model-effort-customization-points-and-effort-mapping-gap]
created: '2026-10-02'
updated: '2026-10-02'
status: draft
---
## 개요

opst(스킬 테스터)의 변형 끝에 `design=<model>[/<effort>]`와 `impl=<model>[/<effort>]`를 붙여, 설계 주체와 구현 에이전트의 모델·effort를 변형마다 따로 지정해 같은 조건에서 비교한다.

## 결정 배경 (WHY)

- (근거: task:176 PLAN 결정 "변형 설정 문법") 기존 `--variant` 반복·기록·이력 구조를 재사용하고 새 인자 체계를 만들지 않기 위해 변형 문자열의 토큰으로 넣었다.
- (근거: task:176 PLAN 결정 "구현 에이전트 적용") 서브에이전트 모델 전역 환경변수는 판정 에이전트까지 바꿔 판정 독립을 깨므로 쓰지 않고, 격리 저장소 안의 프로젝트 정의로만 바꾼다.

## 결정 내용

- 문법: `--variant "//opds design=opus/high impl=sonnet/low"`. 토큰은 둘 다 선택이며, 파일럿 판정과 발화 치환 전에 떼어낸다. 변형 식별은 토큰을 포함한 전체 문자열이다.
- 설계 주체: 세션의 `claude -p`에 `--model`, `--effort`로 전달한다. 미지정이면 플래그를 넣지 않는다.
- 구현 에이전트: 모의 저장소 `.claude/agents/`에 `opal-task-agent`·`opal-be-agent`·`opal-fe-agent` 정의 사본을 만들어 frontmatter만 바꾼다. 프로젝트 정의가 설치본보다 우선함을 실호출로 확인했다 (근거: task:176 DONE.md). 판정 에이전트 4종은 사본을 만들지 않고 세션에 서브에이전트 모델 환경변수를 넘기지 않는다.
- 기록: `run.json`의 `settings`에 선언값과 적용 결과(세션 `modelUsage` 모델, 덮어쓴 정의 sha256)를 남긴다. 선언만 기록하면 적용 실패를 놓치기 때문이다.
- 비교 보고: 지표마다 `평균 (최소~최대)`, 신규 지표 `test_fix_iterations`(`fix 작업` 행 수), 후보별 품질 하한 판정(숨은 테스트 통과율과 준수 합격 비율이 현행보다 낮지 않아야 `하한 충족`). `--max-parallel N`으로 동시 세션 수를 제한한다.
- 비교 묶음의 FW 지문이 하나가 아니면 `비교 무효 — FW 버전 상이`를 표시하고 품질 판정을 내지 않는다. [[measurement-framework-fingerprint-drift-invalidates-comparison]] 참조.

## 영향 범위

- `opal/skills/opal-skill-tester/scripts/skill_tester.py`, `opal/skills/opal-skill-tester/scripts/report_html.py`, `opal/skills/opal-skill-tester/SKILL.md`, `opal/skills/opal-skill-tester/references/metrics.md`

## 관련 페이지

- [[opal-skill-tester]]
- [[dispatch-model-overrides-agent-frontmatter]]
- [[model-effort-customization-points-and-effort-mapping-gap]]
