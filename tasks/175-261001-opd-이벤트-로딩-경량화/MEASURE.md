# MEASURE — 이벤트 로딩 경량화 (S-16)

측정 대상: 설치본 `~/.opal` (설치 2026-10-01T14:28Z) 대 변경 전 로더(커밋 bb257506, 임시 체크아웃 `--source-root`). 프로젝트 루트는 OPAL 허브. 반복 1회.
증거 원본: `scratchpad/out2/s16-*.json`, `s16-load-report.json`.

## 정의
- 본문 합계 = `payload_bytes` (응답 `documents[].content` UTF-8 합).
- 응답 바이트 = 응답 JSON 전체 길이(`load` 출력 `wc -c`). 변경 전 응답은 같은 문서 본문이 `documents`와 `required_documents`에 중복 포함된다.
- `measure`의 `response_bytes`는 자기 필드를 0으로 둔 규약값이라 `load` 출력 길이보다 9바이트 작다 (worker.dispatch 기준, 그 외 이벤트는 5바이트).

## 결과 표

| 이벤트(대상) | 변경 전 본문 합계 | 변경 전 응답 바이트 | 변경 후 본문 합계 | 변경 후 원문(source) 합계 | 변경 후 응답 바이트(load) | 변경 후 응답(measure) | 비용 | 시간 |
|---|---|---|---|---|---|---|---|---|
| session.assistant | 11,767 | 26,912 | 11,767 | 11,767 | 14,730 | 14,725 | 미측정(S-17 또는 run-log에서 채움) | 미측정(S-17 또는 run-log에서 채움) |
| pm.activate | 71,529 | 148,614 | 71,682 | 71,682 | 76,229 | 76,224 | 미측정 | 미측정 |
| stage.plan | 42,508 | 89,218 | 42,508 | 42,508 | 45,759 | 45,754 | 미측정 | 미측정 |
| stage.design | 53,305 | 113,880 | 51,967 | 51,967 | 57,703 | 57,698 | 미측정 | 미측정 |
| pilot.start | 69,217 | 145,894 | 69,217 | 69,217 | 75,261 | 75,256 | 미측정 | 미측정 |
| worker.dispatch / opal-be-agent | 46,244 | 98,203 | 32,629 | 47,770 | 39,611 | 39,602 | 미측정 | 미측정 |
| worker.dispatch / opal-test-agent | 46,244 | 98,203 | 32,499 | 47,770 | 39,489 | 39,480 | 미측정 | 미측정 |
| worker.dispatch / opal-security-checker | 46,244 | 98,203 | 32,697 | 47,770 | 39,711 | 39,702 | 미측정 | 미측정 |
| worker.dispatch / opal-plan-agent (전체 항목 대상) | 46,244 | 98,203 | 45,532 | 47,770 | 52,703 | 52,694 | 미측정 | 미측정 |

해석:
- 일반 대상 3종의 본문 합계는 변경 전 46,244보다 모두 작다 (32,499 ~ 32,697, 약 29% 감소). 응답 바이트는 98,203 에서 약 39.6K 로 약 60% 감소한다 (본문 중복 제거 효과).
- 전체 항목 대상 `opal-plan-agent`는 45,532로 제외 절만 빠져 46,244보다 소폭 작다.
- 이벤트 5종은 본문 합계가 거의 같고(`pm.activate` +153, `stage.design` -1,338은 변경 전 체크아웃과 설치본 문서 내용 차이), 응답 바이트는 본문 중복이 사라져 약 절반이다. 응답 바이트가 본문 합계보다 약 3~7K 큰 것은 메타데이터와 선별 정보 때문이다.
- 변경 후 응답에서 `required_documents`·`optional_documents` 항목에 `content` 키가 있는 건수는 0 (session.assistant·pm.activate 확인).
- 비용·시간은 로드량이 아니라 실호출 결과이므로 본 표에서는 미측정이다. S-17(opst 실행) 또는 run-log에서 채운다. 참고용 로더 처리 시간(ns, 1회 측정)은 worker.dispatch 대상별 1.5 ~ 1.9 ms 로 모델 시간과 무관하다.
- 변경 전 `worker.dispatch`는 대상 인자가 없어 대상과 무관하게 전체 로드(46,244 / 98,203)다.

## load-report (재검증 미합산)

명령: `load-report --receipt be.json be.json be-verify.json sec.json sec-verify.json` (be 중복 1회, verify 결과 파일 2개 포함)

```
{"command": "load-report", "load_count": 2, "ok": true, "payload_bytes": 65326, "response_bytes": 79304, "skipped_verify_results": 2}
```

- `load_id` 중복이 제거되어 load_count 2, 본문 합계 65,326 = 32,629 + 32,697, 응답 합계 79,304 = 39,602 + 39,702. verify 결과 파일 2건은 `skipped_verify_results`로만 집계되고 합산에서 제외된다.

## S-17 실행 결과

- 비용 $9.03, 시간 16.0분은 opst `smoke-version-flag`(변형 `//opds`, 1회) 전체 실행의 값이며 로더 단위 비용이 아니다. 위 결과 표의 "미측정" 열은 로더 대상별 값이 없어 그대로 둔다.
- 판정: 변경 후 PASS (숨은 테스트 2 passed, 완료·상태검증 True, run-log 적체 0, 게이트 증거 True, 체크포인트 도구 3/우회 0). 단계별 소요(분): design 6.7, execute 1.7, test 2.4, close 1.7.
- 비교 기준 없음: 변경 전 opst 기록이 저장소에 없어 "변경 전과 같다"는 확인하지 못했다. 단일 실행이므로 품질 동등성 확정은 반복·비교 실험이 필요하다.
- 증거: `run/opst-s17/REPORT.md`, `metrics.json`, `result.json`, `run1.log`.
