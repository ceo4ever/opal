# opal-skill-tester 보고서 — function-stockctl-multiloc (function)

다중 위치 재고·이동·감사·가져오기·충돌 감지

| 실행 | 판정 | 숨은 테스트 | 완료 | 상태검증 | run-log 적체 | 게이트 증거 | 체크포인트 커밋 | 최종 수행 시간(분) | $ | 서브에이전트 | 게이트 반복 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| opds-design-opus-high-impl-sonnet-low-r1 | **PASS** | 17 passed in 3.37s | True | True | 0 | True | 도구 3/우회 0 | 20.5 | 10.76 | 7 | 1 |
| opds-design-opus-high-impl-sonnet-low-r2 | **PASS** | 17 passed in 3.22s | True | True | 0 | True | 도구 4/우회 0 | 19.7 | 11.69 | 7 | 1 |
| opds-design-opus-high-impl-sonnet-medium-r1 | **PASS** | 17 passed in 2.78s | True | True | 0 | True | 도구 5/우회 0 | 23.5 | 12.34 | 11 | 1 |
| opds-design-opus-high-impl-sonnet-medium-r2 | **PASS** | 17 passed in 3.41s | True | True | 0 | True | 도구 3/우회 0 | 21.8 | 11.4 | 6 | 1 |
| opds-design-opus-medium-impl-haiku-medium-r1 | **PASS** | 17 passed in 3.15s | True | True | 0 | True | 도구 4/우회 0 | 27.7 | 11.11 | 9 | 1 |
| opds-design-opus-medium-impl-haiku-medium-r2 | **PASS** | 17 passed in 3.12s | True | True | 0 | True | 도구 6/우회 0 | 37.1 | 12.86 | 10 | 1 |
| opds-r1 | **PASS** | 17 passed in 3.32s | True | True | 0 | True | 도구 5/우회 0 | 26.7 | 12.12 | 7 | 1 |
| opds-r2 | **PASS** | 17 passed in 3.46s | True | True | 0 | True | 도구 4/우회 0 | 18.4 | 9.19 | 7 | 1 |

## 불합격 사유와 경고

- **opds-design-opus-high-impl-sonnet-low-r1**: 없음
- **opds-design-opus-high-impl-sonnet-low-r2**: 없음
- **opds-design-opus-high-impl-sonnet-medium-r1**: 없음
- **opds-design-opus-high-impl-sonnet-medium-r2**: 없음
- **opds-design-opus-medium-impl-haiku-medium-r1**: 없음
- **opds-design-opus-medium-impl-haiku-medium-r2**: 없음
- **opds-r1**: 없음
- **opds-r2**: 없음

## 변형 비교 (반복 평균 (최소~최대))

| 지표 | //opds | //opds design=opus/high impl=sonnet/low | //opds design=opus/high impl=sonnet/medium | //opds design=opus/medium impl=haiku/medium |
|---|---|---|---|---|
| wall_min | 22.55 (18.40~26.70) | 20.10 (19.70~20.50) | 22.65 (21.80~23.50) | 32.40 (27.70~37.10) |
| cost_usd | 10.65 (9.19~12.12) | 11.22 (10.76~11.69) | 11.87 (11.40~12.34) | 11.98 (11.11~12.86) |
| turns | 106.50 (91.00~122.00) | 61.00 (13.00~109.00) | 28.00 (17.00~39.00) | 73.50 (47.00~100.00) |
| subagent_runs | 7.00 (7.00~7.00) | 7.00 (7.00~7.00) | 8.50 (6.00~11.00) | 9.50 (9.00~10.00) |
| gate_iterations | 1.00 (1.00~1.00) | 1.00 (1.00~1.00) | 1.00 (1.00~1.00) | 1.00 (1.00~1.00) |
| hidden_pass_rate | 1.00 (1.00~1.00) | 1.00 (1.00~1.00) | 1.00 (1.00~1.00) | 1.00 (1.00~1.00) |
| test_fix_iterations | 0.00 (0.00~0.00) | 0.00 (0.00~0.00) | 0.00 (0.00~0.00) | 0.00 (0.00~0.00) |
| 합격 | 2/2 | 2/2 | 2/2 | 2/2 |

## 품질 하한 판정

기준 변형: //opds — 하한은 숨은 테스트 통과율 평균과 PASS 비율이 모두 기준 이상일 때 충족한다.

- //opds design=opus/high impl=sonnet/low — 하한 충족 (숨은 테스트 평균 1.00, PASS 1.00)
- //opds design=opus/high impl=sonnet/medium — 하한 충족 (숨은 테스트 평균 1.00, PASS 1.00)
- //opds design=opus/medium impl=haiku/medium — 하한 충족 (숨은 테스트 평균 1.00, PASS 1.00)

## 단계별 소요(분)

- opds-design-opus-high-impl-sonnet-low-r1: {'design': 7.5, 'execute': 3.8, 'test': 3.4, 'close': 1.8}
- opds-design-opus-high-impl-sonnet-low-r2: {'design': 8.6, 'execute': 3.4, 'test': 3.0, 'close': 1.2}
- opds-design-opus-high-impl-sonnet-medium-r1: {'design': 6.4, 'execute': 5.1, 'test': 5.7, 'close': 1.8}
- opds-design-opus-high-impl-sonnet-medium-r2: {'design': 8.5, 'execute': 4.3, 'test': 3.6, 'close': 2.0}
- opds-design-opus-medium-impl-haiku-medium-r1: {'design': 6.8, 'execute': 2.9, 'test': 11.9, 'close': 2.2}
- opds-design-opus-medium-impl-haiku-medium-r2: {'design': 6.6, 'execute': 6.0, 'test': 19.1, 'close': 1.7}
- opds-r1: {'design': 8.5, 'execute': 4.2, 'test': 7.3, 'close': 2.8}
- opds-r2: {'design': 6.9, 'execute': 4.1, 'test': 2.4, 'close': 1.5}
