# ADD-3 측정 규칙 (사전 고정 — 호출 전에 기록, 데이터를 본 뒤 변경 금지)

작성 시점: 호출 시작 전. 이 파일의 sha256 해시는 EVAL-RESULT-4.md에 싣는다.

## 평가 세트 (11건, 불투명 ID d01~d11, 무작위 순서)

- clean 3건: 원본 pass-161/163/169 복사본에서 지적 판정(adjudication.md)이 real로 본 모호성·누락만 닫는 문장을 더한 판본. 기대 verdict pass.
- borderline 3건: 원본 pass-161/163/169 그대로. 기대 verdict pass이나 채택 규칙에서 제외하고 fail 비율만 보고한다.
- defect 5건: 기존 결함 5건(defect-162-i1, 163-i1, 167-i2, 168-i2, 169-i2) 그대로. 기대 verdict fail과 사례별 기대 실패 축(run_eval2의 EVAL_SPECS의 `expected_axes`와 같다)은 다음과 같다.
  - 162-i1: decision_clarity, executability / 163-i1: decision_clarity, executability / 167-i2: decision_clarity / 168-i2: decision_clarity / 169-i2: decision_clarity

## 후보와 호출

- 후보: E0 `opus` effort 미지정 / E1 `opus` `--effort medium` / E3 `opus` `--effort low`. (E2 high 제외)
- 사례 11 x 후보 3 x 반복 3 = 99 trial. 각 trial = `scope: design`과 `scope: scenario` 동시 두 호출 = 198 호출. 결합(`design-gate combine`) 99건.
- 정식 wrapper `~/.opal/tools/opal-agent/run.sh --json --model opus [--effort <수준>] --allowed-tools Read,Grep,Glob,Bash --cwd <중립 fixture 경로> --opal-bootstrap off --timeout 300 --system-prompt <저장소 opal/agents/opal-evaluator-agent/AGENT.md frontmatter 제외 본문>`.
- 프롬프트·fixture 방식은 run/eval2/run_eval2_e3.py와 같다. trial마다 fresh worker.dispatch receipt와 fresh `--make-fixture` 임시 태스크(폴더 이름은 불투명 토큰).
- 반복은 같은 입력에 대한 독립 호출이며 재시도가 아니다. trial 순서(사례·후보·반복)는 무작위로 섞고 최대 6개 동시 실행한다. 한 호출의 실패는 재시도하지 않고 그대로 기록한다.

## 형식 오류 (호출 단위, 분모 = 후보당 66호출)

호출 하나가 다음 중 하나이면 형식 오류 1건이다.

- (a) 응답에서 계약 JSON을 찾지 못함: 응답 텍스트에 `input_bundle_hash`를 가진 JSON 객체도, 그 문자열도 없다.
- (b) JSON 문법 오류: `input_bundle_hash` 문자열은 있으나 그 객체가 파싱되지 않는다.
- (c) 필수 키·축·점수 누락: 파싱된 부분 결과에 `input_bundle_hash`·`iteration`·`scope`·`status` 중 하나가 없거나, design이면 `design.axes`의 4축(`completeness`, `decision_clarity`, `executability`, `recoverability`)이 PASS|FAIL이 아니거나 `design.gaps`가 배열이 아니다. scenario이면 `scenario.scores`의 `goal`·`adoption`·`boundary`가 숫자가 아니거나 `scenario.average`가 숫자가 아니거나 `scenario.gaps`가 배열이 아니다.
- (d) 타임아웃·호출 실패: wrapper 오류, `is_error` 응답, 응답 JSON 없음, 시간 초과.

형식 오류율 = 후보별·scope별 형식 오류 호출 수 / 해당 호출 수(66, scope별 33).

## 채택 규칙 (후보별로 적용, 네 조건 모두 만족하면 "채택 가능")

1. 결함 누락: defect 5건 x 3회 = 15 trial 중 기대 실패 축을 놓친 trial = 0. "놓침" = 결합 verdict가 fail이 아니거나, 기대 실패 축이 결합 FAIL 축에 없는 경우(run_eval2 `eval_evaluator`의 `missed`와 같다).
2. clean 안정성: clean 3건 x 3회 = 9 trial 중 결합 verdict가 fail인 trial <= 2.
3. 형식 오류율: 후보의 66호출 중 형식 오류 <= 2(약 3%).
4. 결합 성립: 후보의 33 trial 중 결합이 성립하지 않은 trial(`combine` 결과 없음·거부) <= 3. (사전 고정 시점의 해석: 지시문의 "99건 중 <= 3"을 후보별 규칙으로 적용하려고 후보 몫 33건에 같은 상한 3을 쓴다. 전체 99건 중 후보 합계도 함께 보고한다.)

borderline(원본 pass 3건 그대로)은 규칙에 넣지 않고 fail 비율만 보고한다.

### 결합이 안 된 trial의 처리

- 규칙 1·2는 결합 결과가 있는 trial만 센다. 결합 결과가 없는 trial은 규칙 3(형식 오류)·4(결합 성립)에서 다룬다.
- 보수적 참고치로, 결합 결과 없는 defect trial을 "놓침"으로, clean trial을 "fail"로 세었을 때의 최악 가정 값도 함께 보고하되 판정에는 쓰지 않는다.

## 소요

- 호출별 소요 = wrapper 프로세스 시작부터 JSON 수신까지 벽시계 초(호출 실패 포함). 결합 소요 = 한 trial의 두 호출 중 긴 쪽.
- 후보별 평균·중앙값·p90(nearest-rank)·최대를 보고한다. 동시 실행 6, 호출 시각대가 섞여 있으므로 상대 비교로만 읽는다.
