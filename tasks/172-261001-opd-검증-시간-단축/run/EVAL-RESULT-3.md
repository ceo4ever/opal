<!--
E3(opus + effort low) 중립 평가 세트 측정 결과. 호출은 정식 wrapper(opal-agent), 사례는 EVAL-RESULT-2와 같은 불투명 ID. PLAN D-13 판정 규칙 그대로(변경 없음).
E0·E1·E2 값은 run/eval2/results2.json(EVAL-RESULT-2 원자료)을 재사용했고 다시 재지 않았다. E3 원본은 run/eval2/raw-e3/, 집계는 run/eval2/results3.json, 측정기는 run/eval2/run_eval2_e3.py.
-->
# EVAL-RESULT-3: evaluator 후보 E3(opus + effort low) 중립 측정

실행 호출 16회(design 8·scenario 8), 형식상 결과 있음 15·결과 없음 1(c14 design: 응답에 JSON 문법 오류). 사례당 1회, 재시도 없음. 결합(`design-gate combine`)은 8건 중 7건 성립, 1건(c14) 결과 없음.

## 1. 조건과 E2와의 동일성

- 후보만 바꿨다: E3 = `--model opus --effort low`. E2는 `opus --effort high`.
- 같은 것(E2와 동일): 사례 8건(pass 3·결함 5)과 불투명 ID(c01 c03 c05 c08 c13 c14 c15 c16, `mapping.json` 그대로), 기대 verdict·기대 실패 축, fixture 생성 방식(`make_fixture`, 호출 중 cwd·경로엔 ID만 노출), 프롬프트(`evaluator_prompt`, scope: design / scope: scenario 동시 두 호출), 호출 방식(정식 wrapper `~/.opal/tools/opal-agent/run.sh --json --allowed-tools Read,Grep,Glob,Bash --cwd <중립 경로> --opal-bootstrap off --timeout 300 --system-prompt <저장소 opal-evaluator-agent AGENT.md 본문>`), 호출마다 fresh worker.dispatch receipt와 절대경로 verify 명령, 동시 최대 6(사례 쌍 단위 2슬롯), 결합은 실제 `state_tool.py design-gate combine`, 채점 코드(`eval_evaluator`)는 `run_eval2.py` 그대로.
- 바뀐 것은 `run_eval2_e3.py`(복사본)에서 `EVAL_CANDS`를 `{E3}`로 교체, checker 경로 제거, raw 저장 위치를 `raw-e3/`로 한 것뿐이다. 기존 `run_eval2.py`는 수정하지 않았다.
- 한계: 소요는 별도 시각대에 측정한 값이라 E0~E2와 시스템 부하가 다를 수 있다(상대 비교만). 표본이 작다(사례당 1회).

## 2. 측정 표 (E3, 불투명 ID)

### 2.1 결합 8행 (`design-gate combine`)

| 사례 | 기대 verdict | 결합 verdict | 기대 실패 축 | 실제 FAIL 축 | 일치 | 결함 누락 | pass 뒤집힘 | 결합 소요(초) | 비고 |
|---|---|---|---|---|---|---|---|---|---|
| c01 | pass | fail | - | completeness,decision_clarity | X | 0 | 1 | 29.8 | rewrite_target=plan |
| c03 | pass | fail | - | decision_clarity | X | 0 | 1 | 64.4 | rewrite_target=plan |
| c05 | fail | fail | decision_clarity | completeness,decision_clarity,executability,recoverability | O | 0 | 0 | 30.6 | rewrite_target=both |
| c08 | fail | fail | decision_clarity,executability | completeness,decision_clarity,executability,recoverability | O | 0 | 0 | 36.6 | rewrite_target=both |
| c13 | fail | fail | decision_clarity | decision_clarity,executability | O | 0 | 0 | 30.6 | rewrite_target=both |
| c14 | pass | 결과 없음 | - | - | 결과 없음 | - | - | 40.3 | 부분 결과 없음: 결과 텍스트에서 design 부분 결과 JSON을 찾지 못함 |
| c15 | fail | fail | decision_clarity | completeness,decision_clarity,recoverability | O | 0 | 0 | 26.4 | rewrite_target=both |
| c16 | fail | fail | decision_clarity,executability | decision_clarity,executability | O | 0 | 0 | 34.4 | rewrite_target=both |

### 2.2 호출 16행

| 사례 | scope | 기대 | 실제 | 소요(초) | 비고 |
|---|---|---|---|---|---|
| c01 | design | design 4축 PASS | FAIL 축: completeness,decision_clarity | 29.8 | turns 2, $0.43 |
| c01 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 2/2/2 평균 2.0, advisory 0건 | 27.2 | turns 3, $0.39 |
| c03 | design | design 4축 PASS | FAIL 축: decision_clarity | 64.4 | turns 4, $0.50 |
| c03 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 2/2/2 평균 2.0, advisory 0건 | 31.2 | turns 3, $0.43 |
| c05 | design | design 4축 중 decision_clarity FAIL | FAIL 축: completeness,decision_clarity,executability,recoverability | 27.7 | turns 2, $0.37 |
| c05 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 0/2/0 평균 0.67, advisory 0건 | 30.6 | turns 2, $0.36 |
| c08 | design | design 4축 중 decision_clarity·executability FAIL | FAIL 축: completeness,decision_clarity,executability,recoverability | 34.7 | turns 3, $0.40 |
| c08 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 1/2/0 평균 1.0, advisory 0건 | 36.6 | turns 2, $0.36 |
| c13 | design | design 4축 중 decision_clarity FAIL | FAIL 축: decision_clarity,executability | 25.7 | turns 2, $0.36 |
| c13 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 1/2/1 평균 1.33, advisory 0건 | 30.6 | turns 2, $0.37 |
| c14 | design | design 4축 PASS | 결과 없음 | 40.3 | 결과 없음: 결과 텍스트에서 design 부분 결과 JSON을 찾지 못함 |
| c14 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 2/2/2 평균 2.0, advisory 0건 | 37.5 | turns 3, $0.44 |
| c15 | design | design 4축 중 decision_clarity FAIL | FAIL 축: completeness,decision_clarity,recoverability | 24.6 | turns 2, $0.37 |
| c15 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 0/2/1 평균 1.0, advisory 1건 | 26.4 | turns 2, $0.37 |
| c16 | design | design 4축 중 decision_clarity·executability FAIL | FAIL 축: decision_clarity,executability | 34.4 | turns 2, $0.37 |
| c16 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 1/2/1 평균 1.33, advisory 0건 | 27.1 | turns 2, $0.37 |

## 3. E3 채택 판정 (D-13)

- 결함 5건 중 기대 실패 축을 놓친 건수: **0** (5건 모두 verdict fail, 기대 축 포함).
- pass 3건 중 fail로 뒤집은 건수: **2** (c01, c03 뒤집힘). 나머지 c14는 결과 없음(뒤집힘 판정 불가).
- 결합 verdict 일치: **5/8** (결과 있음 7건 중 5건; 불일치 2건은 위 뒤집힘, 결과 없음 1건).
- 판정: **채택 불가** (pass 뒤집힘 2건 > 0, 그리고 결과 없음 1건으로 측정 불완전). 결함 누락 0 조건은 충족.

## 4. E0·E1·E2·E3 비교

결합 verdict / FAIL 축 집합 (기대: 라벨 열). 결함 누락·뒤집힘은 각 칸 괄호의 `누락/뒤집힘`.

| 사례(ID) | 기대 | E0 | E1 | E2 | E3 |
|---|---|---|---|---|---|
| pass-163 (c01) | pass | pass / 없음 (0/0) | fail / decision_clarity,recoverability (0/1) | pass / 없음 (0/0) | fail / completeness,decision_clarity (0/1) |
| pass-161 (c03) | pass | fail / decision_clarity (0/1) | fail / decision_clarity (0/1) | fail / decision_clarity (0/1) | fail / decision_clarity (0/1) |
| defect-168-i2 (c05) | fail [decision_clarity] | fail / completeness,decision_clarity,executability,recoverability (0/0) | fail / completeness,decision_clarity,executability (0/0) | fail / completeness,decision_clarity,executability,recoverability (0/0) | fail / completeness,decision_clarity,executability,recoverability (0/0) |
| defect-162-i1 (c08) | fail [decision_clarity,executability] | fail / completeness,decision_clarity,executability,recoverability (0/0) | fail / completeness,decision_clarity,executability,recoverability (0/0) | fail / completeness,decision_clarity,executability,recoverability (0/0) | fail / completeness,decision_clarity,executability,recoverability (0/0) |
| defect-167-i2 (c13) | fail [decision_clarity] | fail / decision_clarity,executability (0/0) | fail / decision_clarity,executability (0/0) | fail / decision_clarity,executability (0/0) | fail / decision_clarity,executability (0/0) |
| pass-169 (c14) | pass | pass / 없음 (0/0) | pass / 없음 (0/0) | fail / completeness,recoverability (0/1) | 결과 없음 |
| defect-169-i2 (c15) | fail [decision_clarity] | fail / completeness,decision_clarity,executability,recoverability (0/0) | fail / completeness,decision_clarity,executability,recoverability (0/0) | fail / completeness,decision_clarity,executability,recoverability (0/0) | fail / completeness,decision_clarity,recoverability (0/0) |
| defect-163-i1 (c16) | fail [decision_clarity,executability] | fail / decision_clarity,executability (0/0) | fail / completeness,decision_clarity,executability,recoverability (0/0) | fail / completeness,decision_clarity,executability (0/0) | fail / decision_clarity,executability (0/0) |

| 후보 | 결과 있음/8 | 결함 누락 | pass 뒤집힘 | verdict 일치 | 채택 | 결합 소요 평균(초) | 중앙값 | 최대 |
|---|---|---|---|---|---|---|---|---|
| E0 | 8/8 | 0 | 1 | 7 | 불가 | 63.1 | 54.9 | 88.9 |
| E1 | 8/8 | 0 | 2 | 6 | 불가 | 81.0 | 68.5 | 170.2 |
| E2 | 8/8 | 0 | 2 | 6 | 불가 | 89.4 | 71.0 | 156.0 |
| E3 | 7/8 | 0 | 2 | 5 | 불가 | 36.1 | 30.6 | 64.4 |

공통 7사례(c14 제외) 결합 소요 평균(초): E0 59.4, E1 68.3, E2 79.8, E3 36.1. E2 대비 E3: 0.45x.
(E0~E2 소요는 EVAL-RESULT-2 값이다. 별도 시각대 측정이므로 상대 비교로만 읽는다.)

## 5. 해석 (표본이 작아 단정하지 않는다)

- **결함 누락**: 결함 5건 모두 verdict fail이고 기대 축(`decision_clarity` 전 건, `executability`는 c08·c13·c16 포함 확인)을 모두 짚었다. `decision_clarity`·`executability`를 놓친 사례는 이번 8건에서 없었다. 결함 5건의 FAIL 축은 E0~E2와 비슷하거나 약간 적었다(예: c15는 completeness·decision_clarity·recoverability, E2의 4축보다 `executability`가 빠졌지만 기대 축은 아님).
- **엄격도**: pass 3건 중 c01(completeness·decision_clarity), c03(decision_clarity) 2건을 fail로 뒤집었다. E0는 c03만, E1은 c01·c03, E2는 c03·c14를 뒤집어 사례별로 뒤집는 대상이 후보마다 달랐다. 이 세트의 pass 사례는 어느 후보든 엄격도 경계에서 흔들렸고(c03은 4후보 모두 뒤집음), low가 특별히 더 엄격하다고 단정할 근거는 약하다. 다만 뒤집힘 2건은 E0(1건)보다 많고 E1(2건)과 같다.
- **결과 없음 1건**: c14 design 응답은 4축 PASS 판정을 담았으나 JSON에 쉼표 누락 오류가 있어 파싱되지 않았다(`reasons` 객체 안 문자열 뒤 구조 오류). 규칙대로 결과 없음으로 두었고 재시도하지 않았다. 형식 안정성이 낮다는 신호일 수 있으나 1건이라 단정은 못 한다. 파싱됐다면 c14는 pass였을 것으로 보이며, 그 경우 뒤집힘은 여전히 2건이다.
- **소요**: E3 결합 소요 평균은 36.1초로 E0 63.1·E1 81.0·E2 89.4초보다 크게 짧았다(E2 대비 약 0.40배, 공통 7사례 기준 위 문단). 호출 수가 같고 모델이 같으니 effort 차이가 주 요인으로 보이나 시각대 부하 차이는 분리하지 못했다.
- 정리: low는 결함 검출에서는 이 세트에서 약해지지 않았으나, pass 안정성(뒤집힘 2건)과 형식 오류 1건 때문에 D-13 규칙으로는 채택 불가다. 시간은 크게 줄지만 위 근거가 표본 8건·1회 측정에 기반하므로 채택 여부는 캡틴 판단 사항이다.
