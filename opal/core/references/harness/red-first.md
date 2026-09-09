---
module: red-first
role: RED-first 적용 판정과 RED→GREEN 증거 계약
load: TEST-SCENARIO 작성·EXECUTE 진입 시
상속: opal/core/PRINCIPLES.md
---

# RED-first 트랙

## 1. 적용 판정

공개 동작을 테스트 코드로 먼저 고정할 수 있고 회귀 위험이 있는 변경에 적용한다.

- 비즈니스 로직, DB 스키마·마이그레이션, API 계약, 인증·인가, 버그 수정: 적용
- 탐색적 프로토타입, 시각 UI, 행위 불변 리팩터, 설정·문서: 구현 후 검증 가능

혼합 작업은 Work item별로 판정한다. RED 대상에는 `구현 전 RED`, 나머지는 실제 검증 시점을
TEST-SCENARIO에 적는다.

## 1.5 RED→GREEN

1. PM은 TEST-SCENARIO의 `시점`이 `구현 전 RED`인 시나리오만 `red_required: true`로 변환해
   `test-tool scenario-init`을 호출한다. 나머지는 `red_required: false`다.
2. 구현자와 다른 주체가 공개 인터페이스를 검증하는 실패 테스트를 작성한다.
3. 실패 명령·exit·핵심 출력을 `test-tool scenario-red`로 기록한다.
4. `test-tool scenario-lock`이 모든 RED 대상의 증거를 확인한 뒤 구현자가 GREEN 작업을 시작한다.
5. GREEN과 수정 루프에서는 RED 테스트의 기대 계약을 약화·삭제하지 않는다.

RED 작성은 `opal-test-agent`의 red mode, GREEN은 배정된 구현 워커가 담당한다.
sdlc-v2는 `test-tool`의 `red_required`와 `scenario-red`/`scenario-lock`을 사용한다.
`red_required`가 없는 기존 `test-scenario.json`은 기존 계약대로 모든 시나리오를 RED 대상으로 본다.
legacy 태스크만 `state-tool verify --red-check`를 사용한다.

## 1.6 목표계열 선작성

sdlc-v2 기본 경로는 PLAN 확정 후 TEST-SCENARIO를 한 번 작성한다. 사용자가 명시했거나 호출 pilot이
legacy 선작성을 요구할 때만 PLAN과 병렬로 초안을 만들 수 있다.

선작성 입력은 TASK의 목표와 AC/C뿐이다. 이 시점에는 gate를 호출하지 않는다. PLAN 확정 뒤 실제
H와 변경 경계를 반영해 중복·과잉·불일치 시나리오를 수정하거나 삭제한 후 gate를 호출한다.
작성자는 PM이며 PLAN 작성자와 분리한다.

## 2. 검증 경계

- 내부 private 구현 대신 반환값, exit code, API 응답, 저장 결과, 화면 동작을 검증한다.
- 테스트 substitute는 단위 계약에 사용할 수 있으나 실제 integration을 통과한 증거가 아니다.
- RED가 필요한 작업인데 테스트 실행 환경이 없어 실패를 관찰할 수 없으면 자동 우회하지 않고 BLOCKED로 반환한다.
- 문서·설정처럼 RED 대상이 아닌 작업은 결정론 검사나 실제 적용 확인으로 검증한다.

RED는 EXECUTE 내부 절차이며 별도 pipeline 행을 만들지 않는다.

## 변경이력

| 버전 | 날짜 | 내용 |
|---|---|---|
| v1.0 | 2026-06-09 18:42 | RED-first 트랙 신설 (016) |
| v1.1 | 2026-08-19 20:59 | 목표계열 선작성 트랙 추가 (095) |
| v1.2 | 2026-09-02 17:22 | 소유자 호칭을 런타임 플레이스홀더로 전환 (L2 직접 수정) |
| v1.3 | 2026-09-09 15:25 | sdlc-v2 목표·AC/C와 legacy R 입력 분기 반영 (111) |
| v2.0 | 2026-09-09 15:33 KST | sdlc-v2 기본 1회 작성 경로에 맞춰 선작성 규칙을 조건부로 축소. 삭제된 Block A/B 참조와 사례 산문·고정 시나리오 수 규칙 제거 (task 111/W-13) |
