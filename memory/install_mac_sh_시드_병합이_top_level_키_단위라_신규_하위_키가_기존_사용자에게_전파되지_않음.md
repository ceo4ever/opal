# install-mac.sh 시드 병합이 top-level 키 단위라 신규 하위 키가 기존 사용자에게 전파되지 않음

> 등록: 2026-09-15 | 유형: improvement | 상태: candidate | 출처: 태스크 123 CLOSE 회고

## 관측

`scripts/install-mac.sh`의 `SEED_KEYS` 루프가 `if key in existing: continue`로 판정한다. `quietHours` 객체가 이미 있으면 그 안의 신규 하위 키(`timeZone`)를 채우지 않는다.

v4.3의 「키별 독립 판정」 전환은 top-level 키(`models`·`shardPolicy`·`quietHours`) 사이의 독립성만 확보했고, 한 top-level 키 **안의 하위 키 단위 병합은 도입되지 않았다**.

## 영향

태스크 123에서는 `load_quiet_hours()`의 `Asia/Seoul` 폴백이 간극을 실질적으로 메웠다. 그러나 앞으로 **어떤 설정 하위 키를 늘려도 기존 사용자는 재설치해도 받지 못한다**. 폴백이 없는 키를 추가하는 순간 드러난다.

## 제안

재귀적 하위 키 병합, 또는 스키마 기반 시드 보정으로 바꾼다. 사용자가 명시적으로 바꾼 값은 덮지 않는다는 기존 의도는 유지해야 하므로, **부재한 키만 채우는 재귀 병합**이 적합하다.
