# opal-skill-tester 보고서 — smoke-version-flag (smoke)

--version 옵션 추가

| 실행 | 판정 | 숨은 테스트 | 완료 | 상태검증 | run-log 적체 | 게이트 증거 | 체크포인트 커밋 | 최종 수행 시간(분) | $ | 서브에이전트 | 게이트 반복 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| opd-r1 | **PASS** | 2 passed in 0.37s | True | True | 0 | True | 도구 5/우회 0 | 15.8 | 8.66 | 5 | 1 |
| opd-r2 | **FAIL** | 2 passed in 0.37s | True | True | 0 | True | 도구 0/우회 0 | 15.8 | 9.4 | 5 | 1 |
| opd2-r1 | **FAIL** | - | None | None | None | None | 도구 0/우회 0 | 10.7 | 4.36 | None | None |
| opd2-r2 | **FAIL** | - | None | None | None | None | 도구 0/우회 0 | 13.8 | 5.07 | None | None |

## 불합격 사유와 경고

- **opd-r1**: (경고) 최종 수행 시간(분) 최근 중앙값 21.05 → 15.8 (-25%)
- **opd-r2**: 준수 불충족: checkpoint_commits; (경고) 최종 수행 시간(분) 최근 중앙값 21.05 → 15.8 (-25%)
- **opd2-r1**: 태스크 state.json 없음(세션이 TASK 전에 멈춤)
- **opd2-r2**: 태스크 state.json 없음(세션이 TASK 전에 멈춤)

## 변형 비교 (반복 평균)

| 지표 | //opd | //opd2 |
|---|---|---|
| wall_min | 15.80 | 12.25 |
| cost_usd | 9.03 | 4.71 |
| turns | 16.00 | 59.50 |
| subagent_runs | 5.00 | - |
| gate_iterations | 1.00 | - |
| hidden_pass_rate | 1.00 | - |
| 합격 | 1/2 | 0/2 |

## 단계별 소요(분)

- opd-r1: {'design': 4.2, 'execute': 3.3, 'test': 4.7, 'close': 1.3}
- opd-r2: {'design': 5.5, 'execute': 3.0, 'test': 4.1, 'close': 1.2}
- opd2-r1: None
- opd2-r2: None
