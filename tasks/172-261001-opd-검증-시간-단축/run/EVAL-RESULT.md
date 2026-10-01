<!--
W-10 checker·evaluator model·effort 후보 측정 결과. PLAN D-13 그대로: checker 4후보×10사례=40회, evaluator 3후보×8사례×scope 2=48회(결합 24건).
이 문서의 표는 run/eval/run_eval.py가 run/eval/raw/ 원본 응답에서 계산해 생성한다(`python3 run_eval.py --report-only`로 재생성).
결과는 후보 간 상대 비교로만 서술하며 절대 누락률을 주장하지 않는다(H-3).
-->
# EVAL-RESULT: checker·evaluator model·effort 평가 (W-10)

실행 호출 88회(checker 40·evaluator 48), 결과 있음 88·결과 없음 0. 모든 호출은 사례×후보당 1회이고 재시도하지 않았다. 결과 없음은 사유와 함께 표에 남겼다. 보정 후 재집계 경위는 8절.

## 1. 후보 표

| 후보 | 대상 | model | effort | 비고 |
|---|---|---|---|---|
| K0 | checker | sonnet | (미지정) | 현행 |
| K1 | checker | sonnet | low |  |
| K2 | checker | sonnet | medium |  |
| K3 | checker | haiku | medium |  |
| E0 | evaluator | opus | (미지정) | 현행 |
| E1 | evaluator | opus | medium |  |
| E2 | evaluator | opus | high |  |

호출 경로: 저장소 `opal/agents/<이름>/AGENT.md` 본문·`tools`로 `--agents` JSON을 만들어 `claude -p --agents <json> --agent <이름> --model <별칭> [--effort <수준>] --output-format json --permission-mode dontAsk --allowedTools Read Grep Glob Bash`로 호출했다(설치본 불변). 호출마다 `event-loader load --event worker.dispatch` receipt를 새로 만들고 `verify ok:true`를 확인한 뒤 프롬프트에 실었다. 소요 시간은 프로세스 시작부터 응답 JSON 수신까지 벽시계 초다. 동시 실행은 최대 6개(evaluator 한 쌍은 슬롯 2개)다.

## 2. checker 결과 (40행)

평가 항목은 최종 finding JSON(`merge` 결과, 사전 검사 finding 포함)을 기대와 대조한 값이다. 기대 매칭은 `location.file` 일치 + `rule_id`에 기대 규칙 키 포함 + 심각도 범위다. `High+ 누락`은 기대 High 이상 finding 중 최종 JSON에 없는 수, `pass 뒤집힘`은 기대가 없는 사례(통과·무결점)에서 High 이상이 나온 경우 1이다.

| 사례 | 후보 | 기대 | 실제 finding 요약 | 판정 일치 | High+ 누락 | pass 뒤집힘 | 소요(초) | 비고 |
|---|---|---|---|---|---|---|---|---|
| 162-defect | K0 | @header test_event_loader_test_event.py(high+); @header test_state_tool_test_cycle.py(high+) | 2건: high/사전/@header×2 | O | 0 | 0 | 57.1 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 13, $0.35 |
| 162-defect | K1 | @header test_event_loader_test_event.py(high+); @header test_state_tool_test_cycle.py(high+) | 2건: high/사전/@header×2 | O | 0 | 0 | 40.0 | 턴 10, $0.26 |
| 162-defect | K2 | @header test_event_loader_test_event.py(high+); @header test_state_tool_test_cycle.py(high+) | 2건: high/사전/@header×2 | O | 0 | 0 | 48.4 | 턴 11, $0.25 |
| 162-defect | K3 | @header test_event_loader_test_event.py(high+); @header test_state_tool_test_cycle.py(high+) | 2건: high/사전/@header×2 | O | 0 | 0 | 187.4 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 21, $0.37 |
| 161-pass | K0 | High+ 0건 | finding 0건 | O | 0 | 0 | 64.7 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 12, $0.32 |
| 161-pass | K1 | High+ 0건 | finding 0건 | O | 0 | 0 | 49.2 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 9, $0.25 |
| 161-pass | K2 | High+ 0건 | finding 0건 | O | 0 | 0 | 46.1 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 9, $0.24 |
| 161-pass | K3 | High+ 0건 | finding 0건 | O | 0 | 0 | 108.6 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 15, $0.22 |
| 163-pass | K0 | High+ 0건 | finding 0건 | O | 0 | 0 | 48.2 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 10, $0.20 |
| 163-pass | K1 | High+ 0건 | finding 0건 | O | 0 | 0 | 30.8 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 7, $0.12 |
| 163-pass | K2 | High+ 0건 | finding 0건 | O | 0 | 0 | 51.0 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 11, $0.28 |
| 163-pass | K3 | High+ 0건 | finding 0건 | O | 0 | 0 | 154.2 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 26, $0.38 |
| 169-pass | K0 | High+ 0건 | finding 0건 | O | 0 | 0 | 43.5 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 12, $0.24 |
| 169-pass | K1 | High+ 0건 | finding 0건 | O | 0 | 0 | 32.9 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 9, $0.18 |
| 169-pass | K2 | High+ 0건 | finding 0건 | O | 0 | 0 | 47.9 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 14, $0.26 |
| 169-pass | K3 | High+ 0건 | finding 0건 | O | 0 | 0 | 125.0 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 29, $0.30 |
| syn-m1-skill-no-description | K0 | YAML Frontmatter SKILL.md(high+) | 1건: high/사전/frontmatter×1 | O | 0 | 0 | 24.2 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 6, $0.14 |
| syn-m1-skill-no-description | K1 | YAML Frontmatter SKILL.md(high+) | 1건: high/사전/frontmatter×1 | O | 0 | 0 | 25.0 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 7, $0.14 |
| syn-m1-skill-no-description | K2 | YAML Frontmatter SKILL.md(high+) | 1건: high/사전/frontmatter×1 | O | 0 | 0 | 30.2 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 9, $0.18 |
| syn-m1-skill-no-description | K3 | YAML Frontmatter SKILL.md(high+) | 1건: high/사전/frontmatter×1 | O | 0 | 0 | 114.9 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 16, $0.24 |
| syn-m2-changelog-section | K0 | opal-doc-standard demo-guide.md(medium+) | 1건: medium/사전/doc-변경이력×1 | O | 0 | 0 | 41.6 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 9, $0.16 |
| syn-m2-changelog-section | K1 | opal-doc-standard demo-guide.md(medium+) | 1건: medium/사전/doc-변경이력×1 | O | 0 | 0 | 26.6 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 6, $0.14 |
| syn-m2-changelog-section | K2 | opal-doc-standard demo-guide.md(medium+) | 1건: medium/사전/doc-변경이력×1 | O | 0 | 0 | 34.0 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 10, $0.18 |
| syn-m2-changelog-section | K3 | opal-doc-standard demo-guide.md(medium+) | 1건: medium/사전/doc-변경이력×1 | O | 0 | 0 | 158.2 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 30, $0.33 |
| syn-m3-camelcase-py | K0 | 파일/폴더 demoHelper.py(medium+) | 1건: medium/사전/파일명×1 | O | 0 | 0 | 22.3 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 6, $0.14 |
| syn-m3-camelcase-py | K1 | 파일/폴더 demoHelper.py(medium+) | 1건: medium/사전/파일명×1 | O | 0 | 0 | 25.6 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 6, $0.14 |
| syn-m3-camelcase-py | K2 | 파일/폴더 demoHelper.py(medium+) | 1건: medium/사전/파일명×1 | O | 0 | 0 | 29.9 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 8, $0.16 |
| syn-m3-camelcase-py | K3 | 파일/폴더 demoHelper.py(medium+) | 1건: medium/사전/파일명×1 | O | 0 | 0 | 112.6 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 22, $0.28 |
| syn-j1-korean-identifier | K0 | 언어 규칙 demo_tool.py(info+) | 1건: medium/모델/언어규칙×1 | O | 0 | 0 | 34.5 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 8, $0.20 |
| syn-j1-korean-identifier | K1 | 언어 규칙 demo_tool.py(info+) | 1건: medium/모델/언어규칙×1 | O | 0 | 0 | 37.4 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 9, $0.20 |
| syn-j1-korean-identifier | K2 | 언어 규칙 demo_tool.py(info+) | 1건: medium/모델/언어규칙×1 | O | 0 | 0 | 43.9 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 11, $0.24 |
| syn-j1-korean-identifier | K3 | 언어 규칙 demo_tool.py(info+) | finding 0건 | X | 0 | 0 | 105.8 | 누락: 언어 규칙(demo_tool.py); model findings dropped: out_of_range=0, mechanical_rule=0; 턴 19, $0.25 |
| syn-j2-english-doc-section | K0 | 언어 규칙 demo-guide.md(info+) | 1건: medium/모델/언어규칙×1 | O | 0 | 0 | 33.8 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 9, $0.19 |
| syn-j2-english-doc-section | K1 | 언어 규칙 demo-guide.md(info+) | 1건: medium/모델/언어규칙×1 | O | 0 | 0 | 32.9 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 10, $0.20 |
| syn-j2-english-doc-section | K2 | 언어 규칙 demo-guide.md(info+) | 1건: medium/모델/언어규칙×1 | O | 0 | 0 | 77.0 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 8, $0.21 |
| syn-j2-english-doc-section | K3 | 언어 규칙 demo-guide.md(info+) | 1건: medium/모델/언어규칙×1 | O | 0 | 0 | 133.8 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 22, $0.30 |
| syn-ok-clean | K0 | finding 없음(low 이하) | finding 0건 | O | 0 | 0 | 29.3 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 9, $0.16 |
| syn-ok-clean | K1 | finding 없음(low 이하) | finding 0건 | O | 0 | 0 | 22.7 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 6, $0.13 |
| syn-ok-clean | K2 | finding 없음(low 이하) | finding 0건 | O | 0 | 0 | 28.5 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 9, $0.16 |
| syn-ok-clean | K3 | finding 없음(low 이하) | finding 0건 | O | 0 | 0 | 123.5 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 18, $0.26 |

## 3. evaluator 결과

### 3.1 호출별 (48행)

기대 판정은 170 `EVAL-RESULT.md`의 기대 verdict 열(통과 3건=pass, 결함 5건=fail과 해당 실패 축)이다. 결함 fixture 5건은 `design-gate start`의 결정론 검사를 통과하지 않아 (170이 '실제로 돌리지 않는다'고 명시한 합성 최소 재현본) 임시 fixture의 `design_gate.status`만 `evaluating`으로 되돌려 열린 시도로 썼다(시도의 `bundle_hash`·`iteration`은 `start`가 만든 그대로).

| 사례 | 후보 | scope | 기대 | 실제 | 소요(초) | 비고 |
|---|---|---|---|---|---|---|
| pass-161 | E0 | design | design 4축 PASS | FAIL 축: 없음 | 66.9 | 턴 6, $0.39 |
| pass-161 | E0 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 2/2/2 평균 2.0, advisory 0건 | 57.4 | 턴 7, $0.38 |
| pass-161 | E1 | design | design 4축 PASS | FAIL 축: 없음 | 46.1 | 턴 6, $0.33 |
| pass-161 | E1 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 2/2/2 평균 2.0, advisory 0건 | 54.5 | 턴 7, $0.36 |
| pass-161 | E2 | design | design 4축 PASS | FAIL 축: 없음 | 77.1 | 턴 7, $0.39 |
| pass-161 | E2 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 2/2/2 평균 2.0, advisory 0건 | 63.2 | 턴 7, $0.54 |
| pass-163 | E0 | design | design 4축 PASS | FAIL 축: 없음 | 41.2 | 턴 3, $0.21 |
| pass-163 | E0 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 2/2/2 평균 2.0, advisory 0건 | 38.9 | 턴 4, $0.23 |
| pass-163 | E1 | design | design 4축 PASS | FAIL 축: 없음 | 61.0 | 턴 4, $0.24 |
| pass-163 | E1 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 2/2/2 평균 2.0, advisory 0건 | 34.0 | 턴 4, $0.21 |
| pass-163 | E2 | design | design 4축 PASS | FAIL 축: 없음 | 56.1 | 턴 5, $0.28 |
| pass-163 | E2 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 2/2/2 평균 2.0, advisory 0건 | 51.1 | 턴 9, $0.51 |
| pass-169 | E0 | design | design 4축 PASS | FAIL 축: 없음 | 67.2 | 턴 9, $0.59 |
| pass-169 | E0 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 2/2/2 평균 2.0, advisory 1건 | 62.0 | 턴 5, $0.38 |
| pass-169 | E1 | design | design 4축 PASS | FAIL 축: 없음 | 61.5 | 턴 8, $0.46 |
| pass-169 | E1 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 2/2/2 평균 2.0, advisory 0건 | 43.5 | 턴 5, $0.24 |
| pass-169 | E2 | design | design 4축 PASS | FAIL 축: 없음 | 108.5 | 턴 15, $1.07 |
| pass-169 | E2 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 2/2/2 평균 2.0, advisory 0건 | 76.5 | 턴 6, $0.44 |
| defect-162-i1 | E0 | design | design 4축 중 decision_clarity·executability FAIL | FAIL 축: completeness,decision_clarity,executability,recoverability | 51.3 | 턴 5, $0.26 |
| defect-162-i1 | E0 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 1/2/0 평균 1.0, advisory 0건 | 50.1 | 턴 4, $0.17 |
| defect-162-i1 | E1 | design | design 4축 중 decision_clarity·executability FAIL | FAIL 축: completeness,decision_clarity,executability,recoverability | 67.6 | 턴 6, $0.22 |
| defect-162-i1 | E1 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 1/2/0 평균 1.0, advisory 0건 | 44.2 | 턴 5, $0.19 |
| defect-162-i1 | E2 | design | design 4축 중 decision_clarity·executability FAIL | FAIL 축: completeness,decision_clarity,executability,recoverability | 84.7 | 턴 9, $0.50 |
| defect-162-i1 | E2 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 1/2/0 평균 1.0, advisory 0건 | 56.9 | 턴 11, $0.34 |
| defect-163-i1 | E0 | design | design 4축 중 decision_clarity·executability FAIL | FAIL 축: completeness,decision_clarity,executability | 43.0 | 턴 4, $0.18 |
| defect-163-i1 | E0 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 1/2/1 평균 1.33, advisory 0건 | 57.6 | 턴 6, $0.20 |
| defect-163-i1 | E1 | design | design 4축 중 decision_clarity·executability FAIL | FAIL 축: completeness,decision_clarity,executability,recoverability | 61.9 | 턴 4, $0.21 |
| defect-163-i1 | E1 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 1/2/1 평균 1.33, advisory 0건 | 64.5 | 턴 7, $0.23 |
| defect-163-i1 | E2 | design | design 4축 중 decision_clarity·executability FAIL | FAIL 축: completeness,decision_clarity,executability,recoverability | 85.3 | 턴 9, $0.49 |
| defect-163-i1 | E2 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 1/2/1 평균 1.33, advisory 0건 | 85.3 | 턴 9, $0.45 |
| defect-167-i2 | E0 | design | design 4축 중 decision_clarity FAIL | FAIL 축: decision_clarity,executability | 73.7 | 턴 6, $0.34 |
| defect-167-i2 | E0 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 1/2/1 평균 1.67, advisory 0건 | 41.9 | 턴 5, $0.17 |
| defect-167-i2 | E1 | design | design 4축 중 decision_clarity FAIL | FAIL 축: completeness,decision_clarity,executability | 46.9 | 턴 4, $0.19 |
| defect-167-i2 | E1 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 0/2/0 평균 0.67, advisory 0건 | 47.4 | 턴 4, $0.23 |
| defect-167-i2 | E2 | design | design 4축 중 decision_clarity FAIL | FAIL 축: completeness,decision_clarity,executability | 81.8 | 턴 9, $0.46 |
| defect-167-i2 | E2 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 0/2/1 평균 1.0, advisory 0건 | 75.5 | 턴 10, $0.32 |
| defect-168-i2 | E0 | design | design 4축 중 decision_clarity FAIL | FAIL 축: completeness,decision_clarity,executability,recoverability | 50.7 | 턴 5, $0.22 |
| defect-168-i2 | E0 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 0/2/0 평균 0.67, advisory 0건 | 50.6 | 턴 7, $0.27 |
| defect-168-i2 | E1 | design | design 4축 중 decision_clarity FAIL | FAIL 축: completeness,decision_clarity,executability,recoverability | 51.7 | 턴 5, $0.19 |
| defect-168-i2 | E1 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 0/2/0 평균 0.67, advisory 0건 | 37.6 | 턴 5, $0.19 |
| defect-168-i2 | E2 | design | design 4축 중 decision_clarity FAIL | FAIL 축: completeness,decision_clarity,executability,recoverability | 62.7 | 턴 6, $0.28 |
| defect-168-i2 | E2 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 0/2/0 평균 0.67, advisory 0건 | 47.5 | 턴 8, $0.27 |
| defect-169-i2 | E0 | design | design 4축 중 decision_clarity FAIL | FAIL 축: completeness,decision_clarity,executability,recoverability | 42.3 | 턴 6, $0.20 |
| defect-169-i2 | E0 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 0/2/0 평균 0.67, advisory 1건 | 50.1 | 턴 4, $0.18 |
| defect-169-i2 | E1 | design | design 4축 중 decision_clarity FAIL | FAIL 축: completeness,decision_clarity,executability,recoverability | 40.8 | 턴 5, $0.18 |
| defect-169-i2 | E1 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 0/2/0 평균 0.67, advisory 1건 | 49.8 | 턴 5, $0.21 |
| defect-169-i2 | E2 | design | design 4축 중 decision_clarity FAIL | FAIL 축: completeness,decision_clarity,executability,recoverability | 66.4 | 턴 9, $0.47 |
| defect-169-i2 | E2 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 0/2/0 평균 0.67, advisory 1건 | 70.2 | 턴 10, $0.48 |

### 3.2 결합 (실제 `design-gate combine`, 24행)

결합 소요는 두 호출 중 긴 쪽(벽시계)이고, 비고의 `쌍 벽시계`는 두 호출을 동시에 시작해 둘 다 끝날 때까지의 시간이다. `verdict 일치`는 170 단일 호출 기대 verdict와의 일치(H-2)이고, `결함 누락`은 결함 사례에서 결합 verdict가 fail이 아니거나 기대 실패 축이 FAIL이 아닌 경우 1이다.

| 사례 | 후보 | 기대 verdict | 결합 verdict | 기대 실패 축 | 실제 FAIL 축 | verdict 일치 | 결함 누락 | pass 뒤집힘 | design 소요(초) | scenario 소요(초) | 결합 소요(초) | 비고 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pass-161 | E0 | pass | pass | - | 없음 | O | 0 | 0 | 66.9 | 57.4 | 66.9 | 쌍 벽시계 66.9; rewrite_target=None |
| pass-161 | E1 | pass | pass | - | 없음 | O | 0 | 0 | 46.1 | 54.5 | 54.5 | 쌍 벽시계 54.5; rewrite_target=None |
| pass-161 | E2 | pass | pass | - | 없음 | O | 0 | 0 | 77.1 | 63.2 | 77.1 | 쌍 벽시계 77.1; rewrite_target=None |
| pass-163 | E0 | pass | pass | - | 없음 | O | 0 | 0 | 41.2 | 38.9 | 41.2 | 쌍 벽시계 41.2; rewrite_target=None |
| pass-163 | E1 | pass | pass | - | 없음 | O | 0 | 0 | 61.0 | 34.0 | 61.0 | 쌍 벽시계 61.0; rewrite_target=None |
| pass-163 | E2 | pass | pass | - | 없음 | O | 0 | 0 | 56.1 | 51.1 | 56.1 | 쌍 벽시계 56.1; rewrite_target=None |
| pass-169 | E0 | pass | pass | - | 없음 | O | 0 | 0 | 67.2 | 62.0 | 67.2 | 쌍 벽시계 67.2; rewrite_target=None |
| pass-169 | E1 | pass | pass | - | 없음 | O | 0 | 0 | 61.5 | 43.5 | 61.5 | 쌍 벽시계 61.5; rewrite_target=None |
| pass-169 | E2 | pass | pass | - | 없음 | O | 0 | 0 | 108.5 | 76.5 | 108.5 | 쌍 벽시계 108.5; rewrite_target=None |
| defect-162-i1 | E0 | fail | fail | decision_clarity,executability | completeness,decision_clarity,executability,recoverability | O | 0 | 0 | 51.3 | 50.1 | 51.3 | 쌍 벽시계 51.3; rewrite_target=both |
| defect-162-i1 | E1 | fail | fail | decision_clarity,executability | completeness,decision_clarity,executability,recoverability | O | 0 | 0 | 67.6 | 44.2 | 67.6 | 쌍 벽시계 67.6; rewrite_target=both |
| defect-162-i1 | E2 | fail | fail | decision_clarity,executability | completeness,decision_clarity,executability,recoverability | O | 0 | 0 | 84.7 | 56.9 | 84.7 | 쌍 벽시계 84.7; rewrite_target=both |
| defect-163-i1 | E0 | fail | fail | decision_clarity,executability | completeness,decision_clarity,executability | O | 0 | 0 | 43.0 | 57.6 | 57.6 | 쌍 벽시계 57.6; rewrite_target=both |
| defect-163-i1 | E1 | fail | fail | decision_clarity,executability | completeness,decision_clarity,executability,recoverability | O | 0 | 0 | 61.9 | 64.5 | 64.5 | 쌍 벽시계 64.5; rewrite_target=both |
| defect-163-i1 | E2 | fail | fail | decision_clarity,executability | completeness,decision_clarity,executability,recoverability | O | 0 | 0 | 85.3 | 85.3 | 85.3 | 쌍 벽시계 85.3; rewrite_target=both |
| defect-167-i2 | E0 | fail | fail | decision_clarity | decision_clarity,executability | O | 0 | 0 | 73.7 | 41.9 | 73.7 | 쌍 벽시계 73.7; rewrite_target=both |
| defect-167-i2 | E1 | fail | fail | decision_clarity | completeness,decision_clarity,executability | O | 0 | 0 | 46.9 | 47.4 | 47.4 | 쌍 벽시계 47.4; rewrite_target=both |
| defect-167-i2 | E2 | fail | fail | decision_clarity | completeness,decision_clarity,executability | O | 0 | 0 | 81.8 | 75.5 | 81.8 | 쌍 벽시계 81.8; rewrite_target=both |
| defect-168-i2 | E0 | fail | fail | decision_clarity | completeness,decision_clarity,executability,recoverability | O | 0 | 0 | 50.7 | 50.6 | 50.7 | 쌍 벽시계 50.7; rewrite_target=both |
| defect-168-i2 | E1 | fail | fail | decision_clarity | completeness,decision_clarity,executability,recoverability | O | 0 | 0 | 51.7 | 37.6 | 51.7 | 쌍 벽시계 51.7; rewrite_target=both |
| defect-168-i2 | E2 | fail | fail | decision_clarity | completeness,decision_clarity,executability,recoverability | O | 0 | 0 | 62.7 | 47.5 | 62.7 | 쌍 벽시계 62.7; rewrite_target=both |
| defect-169-i2 | E0 | fail | fail | decision_clarity | completeness,decision_clarity,executability,recoverability | O | 0 | 0 | 42.3 | 50.1 | 50.1 | 쌍 벽시계 50.1; rewrite_target=both |
| defect-169-i2 | E1 | fail | fail | decision_clarity | completeness,decision_clarity,executability,recoverability | O | 0 | 0 | 40.8 | 49.8 | 49.8 | 쌍 벽시계 49.8; rewrite_target=both |
| defect-169-i2 | E2 | fail | fail | decision_clarity | completeness,decision_clarity,executability,recoverability | O | 0 | 0 | 66.4 | 70.2 | 70.2 | 쌍 벽시계 70.2; rewrite_target=both |

## 4. 후보별 채택 판정 (D-13 규칙)

규칙: 결함을 놓친 건수 0 **AND** pass 사례를 뒤집은 건수 0이면 "채택 가능"이고, checker는 사전 검사 finding과 합산해 High 이상 누락 0건이어야 한다. 결과 없음·미실행 행이 있으면 그 후보는 측정이 불완전하므로 "채택 불가"로 둔다(결과 없음을 통과로 세지 않는다).

| 후보 | 대상 | 결과 있음/전체 | 결함·High+ 누락 | pass 뒤집힘 | 판정 | 이유 |
|---|---|---|---|---|---|---|
| K0 | checker | 10/10 | 0 | 0 | 채택 가능 | - |
| K1 | checker | 10/10 | 0 | 0 | 채택 가능 | - |
| K2 | checker | 10/10 | 0 | 0 | 채택 가능 | - |
| K3 | checker | 10/10 | 0 | 0 | 채택 가능 | - |
| E0 | evaluator | 8/8 | 0 | 0 | 채택 가능 | - |
| E1 | evaluator | 8/8 | 0 | 0 | 채택 가능 | - |
| E2 | evaluator | 8/8 | 0 | 0 | 채택 가능 | - |

### 4.1 소요 시간 요약 (결과 있는 행, 초)

| 후보 | 대상 | 평균 | 중앙값 | 최대 | 판정 일치 아닌 행 |
|---|---|---|---|---|---|
| K0 | checker | 39.9 | 41.6 | 64.7 | 0 |
| K1 | checker | 32.3 | 32.9 | 49.2 | 0 |
| K2 | checker | 43.7 | 46.1 | 77.0 | 0 |
| K3 | checker | 132.4 | 125.0 | 187.4 | 1 |
| E0 | evaluator | 57.3 | 57.6 | 73.7 | 0 |
| E1 | evaluator | 57.2 | 61.0 | 67.6 | 0 |
| E2 | evaluator | 78.3 | 81.8 | 108.5 | 0 |

evaluator 소요는 결합 소요(두 호출 중 긴 쪽)이고, checker 소요는 호출 1건의 벽시계다.

### 4.2 checker pass 뒤집힘의 출처 분리 (참고)

D-13 판정은 위 4절 표 그대로다. 아래는 같은 데이터에서 뒤집힘이 결정론 사전 검사(모든 후보에 같은 결과) 때문인지 모델 때문인지 가른 참고 표다.

| 후보 | pass 뒤집힘 | 그중 사전 검사 finding만으로 발생 | 모델 finding이 관여한 뒤집힘 |
|---|---|---|---|
| K0 | 0 | 0 | 0 |
| K1 | 0 | 0 | 0 |
| K2 | 0 | 0 | 0 |
| K3 | 0 | 0 | 0 |

## 5. 추천 (결정은 캡틴)

- checker: 채택 가능 후보 K0, K1, K2, K3. 평균 소요 시간이 가장 짧은 **K1**(32.3초)를 추천한다. 결정은 캡틴이 한다.
- evaluator: 채택 가능 후보 E0, E1, E2. 평균 소요 시간이 가장 짧은 **E1**(57.2초)를 추천한다. 결정은 캡틴이 한다.
  - 차순위 E0(57.3초)와 평균 차이가 5% 미만이라 1회 측정 분산 안쪽일 수 있다. 시간만으로는 두 후보를 가르기 어렵다.

## 6. 측정 관찰 (후보 간 상대 비교)

이 절의 수치는 2~5절 표에서 파생한 값이며 절대 누락률이 아니다. 사례가 10건·8건뿐이고 합성 사례가 섞여 있어 후보 간 상대 비교로만 읽는다.

### 6.1 checker

1. **163-pass 뒤집힘은 보정 후 사라졌다(최초 측정에서는 4개 후보 모두 뒤집힘).** 최초 측정의 뒤집힘은 모델이 아니라 사전 검사(W-1)의 판정 결함 때문이었다. 163 구간의 테스트 파일 6개는 `# @header` 다음 줄에 `# module: ...` 형식의 줄 주석 헤더를 쓰고, `code-scan scan --json`은 이 형식에서 기준 커밋·현재 모두 `{}`를 반환한다. 보정 전 `check_header`는 기준 쪽을 텍스트 포함으로, 현재 쪽을 scan 결과로 판정해 거짓 "회귀" High를 만들었다. 보정 후에는 양쪽에 같은 scan 판정을 적용하므로 기존부터 인식되지 않던 형식은 finding을 만들지 않는다(8절). 보정 후 163-pass는 4개 후보 모두 finding 0건이다. 모델이 만든 High+ finding은 처음부터 0건이었다.
2. **High+ 누락 0은 후보 간 변별력이 없다.** 기대 High+ finding(162의 @header 2건, `SKILL.md` frontmatter 1건)은 전부 기계 규칙이라 모든 후보가 사전 검사 결과로 받는다. 모델 판단이 필요한 합성 판단 사례 2건의 기대는 medium 이하여서 High+ 누락 지표에 들어가지 않는다. 후보 간 차이는 판단 사례 2건과 소요 시간에서만 나타난다.
3. **판단 사례**: syn-j1(한글 식별자)과 syn-j2(영문 문서 절)에서 K0·K1·K2는 두 사례 모두 `§언어 규칙` medium finding을 냈다. K3(haiku·medium)는 syn-j2는 냈으나 syn-j1은 finding 0건이었다(판정 일치 X 1건). 누락한 심각도는 medium 이하다.
4. **소요 시간**(재집계 후에도 불변; 163-pass는 모델 호출 시간이라 보정과 무관): 162-defect를 뺀 9사례 공통 평균은 K0 38.0초, K1 31.5초, K2 43.2초, K3 126.3초다(K1 대비 K0 약 1.2배, K3 약 4배). K3는 평균 21.8턴으로 sonnet 후보(7.7~9.9턴)보다 턴이 2배 이상 많았다. sonnet 세 후보의 차이는 이 표본에서 사례별 편차(예: syn-j2 K2 77.0초)와 비슷한 크기라 순서를 확정하지 않는다.
5. **최초 결과 없음 2건(162-defect K1·K2)은 후보 품질이 아닌 진입 게이트 때문이었고, 재집계에서 첫 결과를 확보했다.** 최초 호출 두 건은 에이전트가 `event-loader verify`를 직접 실행했을 때 `stale_receipt`(agent-registry 경로: receipt는 `~/.opal/references/agents.md`, 검증은 저장소 소스 `opal/core/references/agents.md` 기준)를 받고 `status: blocked`로 반환했다(원본 `raw/checker/initial-no-result/`). 재집계에서는 프롬프트에 verify 절대경로 명령(`--project-root` 포함)을 명시하고 호출 직전 receipt를 새로 만들어 두 건을 실행했으며, 둘 다 사전 검사 @header High 2건을 포함한 최종 JSON을 만들었다(K1 40.0초, K2 48.4초; 8절). 최초 원인은 확정하지 않았다.

### 6.2 evaluator

1. 3개 후보 모두 결합 verdict 24건 중 24건이 170 단일 호출 기대와 일치했다(H-2: 호출을 scope로 나눠도 기대 verdict가 달라진 사례 없음). 결함 누락 0, pass 뒤집힘 0이다. 170에서 xhigh가 뒤집었던 pass-163·pass-169도 E0·E1·E2 모두 pass였다.
2. 결함 사례에서 기대 실패 축 외의 축도 FAIL로 판정한 경우가 많았다(예: 168·169의 4축 전부). 기대 축을 못 잡은 건수만 누락으로 세었으므로 이 초과 지적은 채택 판정에 들어가지 않는다. 후보 간 차이도 작다.
3. **소요 시간**: 결합 소요(두 호출 중 긴 쪽) 평균은 E0 57.3초, E1 57.2초, E2 78.3초다. E1은 E0과 시간 차이가 없고 E2는 E0 대비 약 1.37배다. 두 호출을 동시에 실행한 쌍 벽시계 평균은 E0 57.3초, E1 57.2초, E2 78.3초이고, 개별 소요의 합 평균(E0 105.6초, E1 101.6초, E2 143.6초)보다 24쌍 모두 짧았다.
4. effort 미지정(E0)이 실제로 어느 effort로 실행되었는지는 CLI 출력으로 확인되지 않는다. E0과 E1의 시간이 같다는 사실만 관측했다. 호출당 비용 합은 E0 $4.36, E1 $3.87, E2 $7.30이다.

## 7. 한계

1. **합성 사례 대표성(H-3)**: checker의 합성 6건은 필자가 만든 최소 변경이며 기계 규칙 3건은 사전 검사가 결정론으로 잡는다. 실제 변경의 판단 규칙 위반 분포를 대표하지 않는다. 판단 사례가 2건뿐이라 모델 간 변별은 약하다. 결과는 후보 간 상대 비교로만 읽고 절대 누락률은 주장하지 않는다.
2. **헤드리스 호출은 실제 서브에이전트 디스패치와 완전히 같지 않다**: `claude -p --agents … --agent …`로 에이전트 정의를 주입했고 `--permission-mode dontAsk --allowedTools Read Grep Glob Bash`로 권한을 열었다. 실제 PM 디스패치의 컨텍스트 주입·모델 별칭 매핑(`standard`→sonnet 등)·세션 effort 상속과 다를 수 있다. 호출마다 `--no-session-persistence`를 썼고 사용자 전역 MCP·커넥터가 로드된 상태에서 호출되었다.
3. **동시 실행 영향**: 최대 6개 호출이 동시에 돌아 소요 시간에 서로의 부하가 섞인다. 같은 사례의 후보들이 같은 시각대에 실행되도록 사례 순서로 제출했으나, 시간은 1회 측정값이며 반복 분산을 알 수 없다.
4. **사례 구성 판단**(PLAN D-13 문구 우선): ① 과거 기록 4건 중 통과 3건의 `target_files`는 해당 태스크의 과거 `gc-findings-convention-*.json` `checked_files`를, 162 결함은 기록이 없어 구간 변경 파일 중 `tasks/` 아래 산출물을 제외한 목록을 썼다. ② 합성 사례의 기준 저장소는 `docs/CONVENTIONS.md`와 참조 문서 사본을 가진 임시 git 저장소다. ③ 판단 사례의 기대는 "해당 파일에 `§언어 규칙` finding이 있고 심각도가 medium 이하"로 읽었다. ④ evaluator의 기대 실패 축은 170 `EVAL-RESULT.md` 표(162·163은 decision_clarity+executability, 167·168·169는 decision_clarity)를 썼고 원본 gate 축(168·169는 completeness 등 추가)은 쓰지 않았다. ⑤ 결과 없음·미실행이 있는 후보는 측정 불완전으로 "채택 불가"로 두었다(결과 없음을 통과로 세지 않기 위한 해석이며 D-13 문구에는 없다).
5. **evaluator fixture**: 결함 fixture 5건은 `design-gate start`의 결정론 검사를 통과하지 못해(TASK.md sdlc-v2 frontmatter 등), `start`가 만든 시도(`bundle_hash`·`iteration` 1)를 유지한 채 임시 fixture의 `design_gate.status`만 `evaluating`으로 되돌려 `combine`을 실행했다. evaluator는 state.json을 입력으로 받지 않으므로 판정에는 영향이 없다고 보지만, 실제 PM 경로 그대로는 아니다.
6. **사전 검사 기여**: checker의 최종 JSON은 사전 검사 finding을 포함하므로 모델 단독 성능이 아니라 "사전 검사 + 모델 + merge" 흐름의 결과다. 모델이 `merge`를 수행하지 않으면 결과 없음이다.

## 8. 재집계 경위

### 8.1 최초 측정이 드러낸 결함

최초 측정(`results-initial.json`·`results-initial-EVAL-RESULT.md`로 보존)에서 163-pass가 checker 4개 후보 모두에서 "pass 뒤집힘"이 되어 checker 전 후보가 채택 불가였다. 원인은 모델이 아니라 `convention_precheck.py` `check_header`의 비교 기준 불일치였다. 수정 파일의 "기준 커밋에 @header가 있었는지"는 텍스트 포함(`"@header" in base`)으로, "지금 없는지"는 `code-scan scan --json` 결과가 비었는지로 판정했다. 163의 테스트 파일 6개(`# @header` 다음 줄에 `# module: ...` 줄 주석 헤더)는 code-scan이 기준·현재 모두 `{}`로 해석하는 기존 형식인데도 거짓 "회귀" High가 되었다. 163의 과거 검사 기록은 같은 6개를 info/advisory로 보고했고 통과였다. PLAN D-10 ①은 "기준 커밋 버전에는 @header가 있었는데 지금 없으면(회귀)"를 규칙으로 정했으므로, 결함은 규칙이 아니라 구현이 기준 쪽을 다른 판정기로 본 것이다.

### 8.2 수정 내용

수정 파일(status M)의 기준 커밋 blob을 임시 폴더에 같은 상대경로로 쓰고 project-root의 `.opal/code-scan.json`을 복사해 현재와 같은 `code-scan scan <rel> --json`을 적용한다(`CodeScanClient.base_header_of`). 회귀 = 기준 scan 결과가 비어 있지 않고 현재 scan 결과가 비어 있음. 기준·현재 모두 비어 있으면(기존부터 code-scan이 인식 못 하는 형식) finding을 만들지 않는다. 추가된 파일(A)은 종전대로 scan 결과가 비면 finding이다. 다른 규칙·finding 스키마·fingerprint는 바꾸지 않았다. 162 재현(S-9 시험)은 그대로 정확히 2건이다. 시험 2건을 추가했다(`test_mechanical_rules_header_line_comment_legacy_no_finding`, `test_mechanical_rules_header_regression_kept`; 전체 15건 통과).

### 8.3 재집계 방식

- 모델 호출 40건 중 38건의 응답은 재사용했고 다시 호출하지 않았다. 모델 응답은 사전 검사와 독립이다.
- 최종 finding JSON은 "사전 검사 + 모델 finding"을 에이전트가 `merge`한 결과이므로 사전 검사 산출물이 raw에 저장되어 있었다. 그래서 과거 체크아웃을 같은 커밋·`base_ref`·`target_files`로 다시 만들어 보정된 `scan`을 실행하고(`recompute_precheck.py`), 기존 최종 JSON에서 기존 사전 검사 finding을 뺀 나머지를 모델 finding으로 복원해 보정된 사전 검사와 다시 `merge`했다. 원본 JSON은 `*.initial.json`으로 보존했다. 합성 사례는 체크아웃을 다시 만들면서 `base_ref` 커밋 sha가 달라졌으므로 새 `cases.json`(스크래치)의 값으로 `scan`했고, 기존 사전 검사 결과와 비교해 163-pass 외에는 finding 집합이 같음을 확인했다. 복원한 모델 finding은 어느 사례에서도 없었다.
- 재집계로 바뀐 최종 JSON은 163-pass 4건(K0~K3; 사전 검사 6건 → 0건)뿐이다. 나머지는 변동이 없다.
- 신규 호출 2건: 최초 결과가 없던 `162-defect` K1·K2. 호출 직전 receipt를 새로 만들고 verify `ok: true` 확인 후, 프롬프트에 verify 절대경로 명령(`~/.opal/tools/event-loader/run.sh verify --receipt <receipt> --event worker.dispatch --project-root <저장소 루트>`)을 명시했다(`run_eval.py receipt_block`의 문구 보강). 이번에는 `stale_receipt` 없이 둘 다 완료했다. 이 두 건은 재시도가 아니라 최초 결과 확보다.
- evaluator 48건은 이 보정과 무관하므로 건드리지 않았다(결과 동일).

### 8.4 최초 결과 대비 달라진 판정

| 후보 | 최초 | 재집계 |
|---|---|---|
| K0 | 채택 불가(pass 뒤집힘 1: 163-pass) | 채택 가능(결과 10/10, 누락 0, 뒤집힘 0) |
| K1 | 채택 불가(뒤집힘 1; 결과 없음 1) | 채택 가능(10/10) |
| K2 | 채택 불가(뒤집힘 1; 결과 없음 1) | 채택 가능(10/10) |
| K3 | 채택 불가(뒤집힘 1) | 채택 가능(10/10, 판정 일치 아닌 행 1: syn-j1) |
| E0·E1·E2 | 채택 가능 | 변동 없음 |

D-13 채택 규칙(결함 누락 0 AND pass 뒤집힘 0, 결과 없음은 채택 불가)은 사후에 바꾸지 않았고 보정된 값에 그대로 적용했다. 163-pass 뒤집힘이 사라졌고, 사라지지 않은 항목은 없다. checker 4개 후보는 모두 채택 가능이 되었으나 High+ 누락 0은 후보 간 변별력이 없고(6.1의 2), 후보 선택은 소요 시간과 판단 사례 2건의 차이에서만 갈린다. 추천 문구의 K1은 평균 소요 시간 기준이다(1회 측정, 시간 차이는 분산 안쪽일 수 있다). 결정은 캡틴이 한다.

## 공식 문서 근거


- 출처: https://code.claude.com/docs/en/sub-agents.md
  - "Add the `effort` field to your subagent's frontmatter"
  - "The `effort` value applies only when that specific subagent is active"
- 지원 값: low / medium / high / xhigh / max. 요구 버전: Claude Code v2.1.242 이상. 생략하면 세션 effort를 상속한다.
- 한계: 문서는 에이전트에 선언한 값이 호출 세션의 effort보다 우선(override)한다는 규칙을 명문으로 기술하지 않는다. 이 우선 규칙은 확인되지 않았다(H-6 부분 확인). 선언 값이 배포 파일에 존재함은 시험으로 확인한다.
