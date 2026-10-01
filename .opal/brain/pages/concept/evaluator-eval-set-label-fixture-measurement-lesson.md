---
type: concept
title: 평가자 model·effort 측정의 세 가지 왜곡 경로 (라벨 노출·fixture 결손·한도 장애)
tags:
- lesson
- evaluator
- measurement
- eval-set
sources:
- task:172
related: [opal-evaluator-agent, agent-effort-policy-inherit-by-default, fixture-vs-real-blind-spot-lesson, evaluator-self-weakness-disclosure-pattern]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

모델 판정자(evaluator)의 model·effort 후보를 평가 세트로 비교할 때, 측정 자체가 결과를 왜곡하는 세 가지 경로가 task:172의 추가작업에서 확인됐다. 사례 라벨의 경로 노출, 평가 세트 fixture의 참조 파일 결손, 그리고 계정 한도 장애를 모델 실패로 세는 것이다.

## 결정 배경 (WHY)

- (근거: task:172 ADD1-S13-REVIEW.md) 같은 문서를 같은 후보로 판정해도 fixture 폴더·receipt 이름에 `pass-161` 같은 라벨이 있으면 pass, 중립 이름이면 fail이 나왔다(라벨 경로 5/5 pass, 중립 경로 11/11 fail). 모델은 라벨을 인용하지 않았지만 엄격도가 갈렸다.
- (근거: task:172 EVAL-RESULT-2·3) 라벨을 불투명 ID로 바꾸자 이전에 "채택 가능"이던 평가자 후보 세 개가 모두 pass 사례를 뒤집어 채택 불가가 됐다. 기준선(현행 설정)도 예외가 아니었다.
- (근거: task:172 EVAL-RESULT-4 §6, EVAL-RESULT-5) 평가 세트의 TASK·PLAN이 같은 폴더의 `REQUEST.md`를 입력으로 가리키는데 fixture 생성기가 TASK·PLAN·TEST-SCENARIO 3파일만 복사해 그 파일이 빠져 있었다. 평가자 세 후보 모두 "REQUEST.md가 없다"를 지적했고, 파일을 넣자 그 지적은 사라지고 low 후보의 clean 뒤집힘이 3/9에서 2/9로 줄었다.
- (근거: task:172 EVAL-RESULT-4 §5) 계정 세션 한도(HTTP 429)로 호출이 `exit 1`·응답 없음·4초로 실패한 것은 모델이 입력을 받은 적이 없는 "미측정"이다. 이것을 사전 고정 규칙의 "호출 실패(d)"로 세면 형식 오류율이 측정 대상과 무관하게 올라간다.

## 결정 내용

- 평가 세트 호출은 사례 라벨을 프롬프트·cwd·fixture 폴더·receipt 파일명 어디에도 노출하지 않는다. 라벨↔ID 매핑은 호출이 끝날 때까지 작업 경로 밖(스크래치)에 둔다.
- "기대 pass" 사례는 먼저 지적 판정(adjudication)으로 실제 모호성을 닫은 clean 판본을 만들고, 원본은 borderline으로 따로 보고한다. clean 판본이 세 후보 모두에서 fail이면 정비 불충분 신호로 기록한다.
- fixture는 사례 문서가 참조하는 입력 파일(REQUEST.md 등)을 함께 넣는다. 결손은 문서 결함이 아니라 측정 결함이며, 과거 측정의 pass 판정에도 소급 영향이 있을 수 있다.
- 채택 규칙(결함 누락·clean 안정성·형식 오류율·결합 성립)은 호출 전에 파일로 고정하고 sha256을 보고서에 싣는다. 인프라 장애로 인한 미측정 재실행은 규칙 문면 이탈이므로 토큰 목록과 함께 보고서에 선언한다.
- 소요 시간은 계정·시각대가 섞이면 상대 비교로만 읽는다.

## 영향 범위

- `opal/agents/opal-evaluator-agent/AGENT.md`의 `effort` 선언(task:172 ADD-5에서 `low`로 변경).
- `opal/tools/state-tool/tests/test_design_gate_parallel.py`의 `--make-fixture`(3파일만 복사 — REQUEST.md 보정은 측정 스크립트가 덧붙였고 도구 자체는 바꾸지 않았다).
- 측정 자산: `tasks/172-…/run/eval3/`(RULES.md·adjudication.md·cases)·`run/eval4/`.

## 관련 페이지

- [[opal-evaluator-agent]]
- [[agent-effort-policy-inherit-by-default]]
- [[fixture-vs-real-blind-spot-lesson]]
- [[evaluator-self-weakness-disclosure-pattern]]
