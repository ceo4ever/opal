# test-tool에 red_required 갱신 경로 부재 — 시나리오 성격 오배정의 되돌림 비용이 전량 재실행

> 등록: 2026-09-15 | 유형: improvement | 상태: candidate | 출처: 태스크 123 CLOSE 회고

## 관측

TEST-SCENARIO 작성 시 보존·회귀 가드형 시나리오(S-9)를 `시점: 구현 전 RED`로 잘못 배정했다. 구현 전에 이미 통과하는 시나리오라 RED 증거를 만들 수 없었고, 워커가 허위 RED를 거부하고 blocker로 반환한 판단은 옳았다.

## 왜 문제인가

`red_required`만 정정할 도구 경로가 없다. `scenario-init` 재실행이 유일한 수단인데, `scenario-init`은 설계상 `red_confirmed`를 전부 `false`로 강제하고 시드 주입도 차단한다(056/ADD-1). 그 결과 시나리오 **1건**의 플래그를 고치려고 이미 확보한 **10건**의 RED 증거를 재실행으로 복구해야 했다.

## 제안

`red_required`만 갱신하는 서브명령을 두거나, `scenario-init`에 기존 `red_confirmed`·`red_evidence`·`red_at`을 보존하는 옵션을 둔다. 허위 RED 차단이라는 원래 의도는 유지하되, **플래그 정정과 증거 위조를 구분**해야 한다.
