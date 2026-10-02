# DIAG-S13: S-13 판정 편차 진단 표본

> 시나리오 S-13의 판정(FAIL)을 바꾸는 측정이 아니다. 같은 `pass-161` 묶음을 설치된 `opal-evaluator-agent`(opus+effort medium)로 단일(scope all) 3회, 병렬(scope design + scenario) 3쌍 호출했다. 호출은 `claude -p --agent … --permission-mode dontAsk --allowedTools Read Grep Glob Bash`, 각 1회·재시도 없음. 병렬 쌍은 실제 `design-gate combine`으로 결합했다. 원본은 `test-evidence/diag/`. 첫 시도 9건은 `event-loader verify`가 승인 대기로 막혀 모델 판정이 없어 무효이며 `test-evidence/diag-invalid-attempt0/`에 보존했다.

## 결과

| 종류 | verdict | rewrite_target | decision_clarity | design gaps 수 | 소요(초) |
|---|---|---|---|---|---|
| 단일 1 | fail | plan | FAIL | 4 | 98.6 |
| 단일 2 | fail | plan | FAIL | 2 | 98.2 |
| 단일 3 | fail | plan | FAIL | 2 | 91.5 |
| 병렬 쌍 1 (design 104.5 / scenario 64.0) | fail | plan | FAIL | 4 | 벽시계 104.5 |
| 병렬 쌍 2 (design 89.4 / scenario 66.4) | fail | plan | FAIL | 3 | 벽시계 89.4 |
| 병렬 쌍 3 (design 100.1 / scenario 71.5) | fail | plan | FAIL | 3 | 벽시계 100.1 |
| S-13 병렬 쌍 (TEST 원본) | fail | plan | FAIL | 3 | 벽시계 73.3 (design 73.3 / scenario 64.6) |

평균 소요: 단일 96.1초, 병렬 쌍 벽시계 91.8초 (병렬 4쌍 포함).

## 해석(관찰만, 표본이 작아 통계 주장은 하지 않는다)

1. **verdict 분포는 같다.** 단일 3/3과 병렬 4/4(S-13 포함)가 모두 `fail`이고 모두 `decision_clarity`만 FAIL이다. 설계 판정과 시나리오 판정을 나눈 것이 verdict를 바꾼다는 근거는 없다.
2. **S-13의 기대(`pass`)와 어긋나는 쪽은 분리가 아니라 호출 조건이다.** W-10 측정(저장소 정의를 `--agents`로 주입, 자체 프롬프트)에서는 같은 후보·같은 사례가 `pass`였고, 설치된 정의 + TEST 프롬프트에서는 단일·병렬 모두 `fail`이다. 이 차이의 원인(프롬프트·정의 주입 방식·표본 변동)은 이 표본으로 분리하지 못했다. 지적 내용은 161 PLAN의 실제 모호성(예: `run` 없이 `run_files`만 있는 설정의 우선순위)에 관한 것이다.
3. **병렬의 시간 이득은 이 표본에서 확인되지 않는다.** design 호출 하나가 단일 호출 전체와 비슷한 시간이 걸려(약 90~105초) 병렬 쌍 벽시계가 단일과 거의 같다. 시나리오 판정 호출(약 65~72초)이 design 호출과 겹치는 만큼만 이득인데 design 쪽이 지배적이다. S-13의 "개별 소요 합보다 짧다"는 기준은 만족하지만 단일 호출 대비 단축은 보이지 않는다.
4. **결론: 판단 불가(분리가 verdict를 바꾼다는 근거 없음 / 기대 verdict와 측정 조건 차이는 미해소 / 시간 이득 미확인).**
