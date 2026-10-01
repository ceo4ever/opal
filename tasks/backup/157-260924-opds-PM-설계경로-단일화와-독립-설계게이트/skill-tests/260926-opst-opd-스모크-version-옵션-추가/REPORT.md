# opal-skill-tester 보고서 — smoke-version-flag (smoke)

--version 옵션 추가

| 실행 | 판정 | 숨은 테스트 | 완료 | 상태검증 | run-log 적체 | 게이트 증거 | 체크포인트 커밋 | 최종 수행 시간(분) | $ | 서브에이전트 | 게이트 반복 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| opd-r1 | **FAIL** | 2 passed in 0.68s | True | True | 0 | True | 도구 0/우회 0 | 20.6 | 8.8 | 5 | 1 |

## 불합격 사유와 경고

- **opd-r1**: 준수 불충족: checkpoint_commits

## 단계별 소요(분)

- opd-r1: {'design': 4.8, 'execute': 3.2, 'test': 7.9, 'close': 2.0}
