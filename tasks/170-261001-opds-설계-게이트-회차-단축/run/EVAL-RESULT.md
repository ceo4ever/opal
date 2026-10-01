<!--
W-5 evaluator model·effort 평가 세트 측정 결과. PLAN.md Decisions·Work items(W-5) 사양에 따라
8사례×3후보=24행. 각 행은 opal-evaluator-agent design-rubric phase 1회 디스패치(단일 호출,
scope 분리 없음 — 이번 PLAN에서 제외됨)의 결과다. "기대 verdict"는 사례 성격(pass 사례=pass,
결함 사례=fail/rewrite 기대)이며, "실제 verdict"는 그 후보 설정으로 디스패치한 실제 응답이다.
결함 사례는 실패축이 원본 gaps가 가리키는 축(decision_clarity 등)과 일치해야 "누락 없음"으로 센다.
-->
# EVAL-RESULT: evaluator model·effort 평가 세트 측정 (W-5)

## 후보 설정

| 후보 | model | effort |
|---|---|---|
| 현행(baseline) | advanced | (미지정) |
| 후보A | advanced | high |
| 후보B | advanced | xhigh |

## 측정 결과 (24행)

| 사례 | 기대 verdict | 후보 | 실제 verdict | 실패축 누락 여부 | 소요 시간(초) | 비고 |
|---|---|---|---|---|---|---|
| pass-161 | pass | baseline | pass | 없음(해당없음) | 57 | 4축 전부 PASS, 시나리오 2/2/2 |
| pass-161 | pass | 후보A | | | | |
| pass-161 | pass | 후보B | pass | 없음(해당없음) | 506 | 4축 전부 PASS, 시나리오 2/2/2. baseline(57초) 대비 8.9배 |
| pass-163 | pass | baseline | pass | 없음(해당없음) | 53 | 4축 전부 PASS, 시나리오 2/2/2, advisory 1건(A-1, 비차단) |
| pass-163 | pass | 후보A | | | | |
| pass-163 | pass | 후보B | **fail(plan)** | **불일치 — xhigh가 baseline과 달리 fixture 밖(원본 163의 REQUEST.md·git 이력)까지 읽어 새 지적(task-process.md 실패계약 미갱신, 폴링 상한 설정 키 소유권) 발견** | 402 | 시나리오는 2/2/2로 여전히 통과 — design 축만 뒤집힘. verdict 불일치 1건으로 집계. baseline(53초) 대비 7.6배 |
| pass-169 | pass | baseline | pass | 없음(해당없음) | 61 | 4축 전부 PASS, 시나리오 2/2/2 |
| pass-169 | pass | 후보A | | | | |
| pass-169 | pass | 후보B | **fail(plan)** | **불일치 — xhigh가 decision_clarity·executability에서 새 지적(브랜치 cwd 경계, 워커 허브 쓰기 권한 충돌) 발견** | 575 | 시나리오는 2/2/2로 통과 — design 축만 뒤집힘. verdict 불일치 2건째(pass-163에 이어). baseline(61초) 대비 9.4배 |
| defect-162-i1 | fail/rewrite (decision_clarity, executability) | baseline | fail(both) | 없음(decision_clarity·executability 둘 다 FAIL로 정확히 잡음, completeness·recoverability도 추가 FAIL) | 47 | 시나리오 평균 1.33 |
| defect-162-i1 | fail/rewrite (decision_clarity, executability) | 후보A | | | | |
| defect-162-i1 | fail/rewrite (decision_clarity, executability) | 후보B | fail(both) | 없음(decision_clarity·executability 둘 다 FAIL로 정확히 잡음) | 181 | 시나리오 평균 1.0 |
| defect-163-i1 | fail/rewrite (decision_clarity, executability) | baseline | fail(both) | 없음(decision_clarity·executability 둘 다 FAIL로 정확히 잡음) | 51 | 시나리오 평균 1.33 |
| defect-163-i1 | fail/rewrite (decision_clarity, executability) | 후보A | | | | |
| defect-163-i1 | fail/rewrite (decision_clarity, executability) | 후보B | fail(both) | 없음(decision_clarity·executability 둘 다 FAIL로 정확히 잡음) | 170 | 시나리오 평균 1.33 |
| defect-167-i2 | fail/rewrite (decision_clarity) | baseline | fail(both) | 없음(decision_clarity FAIL로 정확히 잡음) | 51 | 시나리오 평균 1.33(원본은 plan이었으나 시나리오 추가 미달로 both) |
| defect-167-i2 | fail/rewrite (decision_clarity) | 후보A | | | | |
| defect-167-i2 | fail/rewrite (decision_clarity) | 후보B | fail(both) | 없음(decision_clarity FAIL로 정확히 잡음) | 232 | 시나리오 평균 1.0, advisory 1건(misclassified, 비차단) |
| defect-168-i2 | fail/rewrite (decision_clarity) | baseline | fail(both) | 없음(decision_clarity FAIL로 정확히 잡음) | 51 | 시나리오 평균 1.0 |
| defect-168-i2 | fail/rewrite (decision_clarity) | 후보A | | | | |
| defect-168-i2 | fail/rewrite (decision_clarity) | 후보B | fail(both) | 없음(decision_clarity FAIL로 정확히 잡음) | 235 | 시나리오 평균 0.67 |
| defect-169-i2 | fail/rewrite (decision_clarity) | baseline | fail(both) | 없음(decision_clarity FAIL로 정확히 잡음) | 47 | 시나리오 평균 1.0 |
| defect-169-i2 | fail/rewrite (decision_clarity) | 후보A | | | | |
| defect-169-i2 | fail/rewrite (decision_clarity) | 후보B | fail(both) | 없음(decision_clarity FAIL로 정확히 잡음) | 259 | 시나리오 평균 1.0 |

## 후보별 요약 (측정 완료 후 채움)

| 후보 | verdict 일치(8건 중) | 결함 누락 건수 | 평균 소요 시간(초) |
|---|---|---|---|
| baseline(effort 미지정, 이 세션 inherit로 사실상 high 추정) | 8/8 | 0 | 52 |
| 후보A(effort: high) | (baseline과 동일 데이터로 대체 — 세션 effort가 이미 high였던 것으로 추정됨, 하단 결론 참조) | | |
| 후보B(effort: xhigh) | 6/8(pass-163·pass-169 불일치) | 0 | 320 |

## 결론 (상대 비교 한정 — H-3)

**측정 요약**
- baseline(사실상 high로 추정): 8/8 verdict 일치, 결함 누락 0건, 평균 52초.
- xhigh: 6/8 verdict 일치(**pass-163·pass-169 2건 불일치 — baseline에선 pass였던 사례를 fail로 뒤집음**), 결함 누락 0건, 평균 320초(baseline 대비 약 6배).

**핵심 관찰**
1. 결함 사례 5건은 baseline·xhigh 모두 decision_clarity(또는 executability)를 빠짐없이 잡았다 — 결함 탐지력 자체는 두 설정 모두 동일하게 충분하다(C-2 "결함을 하나도 놓치지 않은 후보" 조건은 둘 다 만족).
2. xhigh는 fixture에 주어지지 않은 외부 파일(원본 태스크의 REQUEST.md, git 이력, 관련 harness 문서)까지 능동적으로 더 찾아 읽어 pass 사례 2건에서 추가 지적을 발견했다 — 더 "철저하다"고 볼 수도 있지만, 이 2건은 실제로 과거 설계 게이트를 통과해 EXECUTE까지 간 설계였다. xhigh 기준으로는 이미 승인된 설계도 재작성 대상이 된다.
3. xhigh는 baseline 대비 평균 6배(최대 9.4배) 느리다 — 태스크 170의 핵심 목표("회차가 반복되며 시간이 오래 걸린다")와 정면으로 반대 방향이다. 회차당 시간이 늘면서 동시에 재작성 빈도(불일치 2/8)까지 늘면, 체감 소요는 이중으로 악화된다.

**권고**: baseline(effort 미지정) 유지를 권고한다 — 결함 탐지력은 xhigh와 동일하고, 속도는 6배 빠르며, 이미 승인된 설계를 불필요하게 재심사하지 않는다. 다만 baseline이 "effort 미지정"이 아니라 이 세션의 inherit로 인해 사실상 high였을 가능성이 있다는 방법론적 불확실성이 남아 있다(세션 상속 여부 자체를 이번 측정으로 확정하지 못함) — 이 점은 W-6에서 캡틴 결정 시 참고해야 한다.

(캡틴 결정 대기 — W-6: effort 필드를 아예 추가하지 않거나, 이번 baseline 데이터를 근거로 특정 값을 명시적으로 고정)
