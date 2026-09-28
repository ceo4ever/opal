# OPAL 테스트 시나리오 작성 기준 개선 제안서

> 상태: 제안
>
> 목적: 검증 누락 없이 중복·과잉 시나리오를 줄여 테스트 수행 시간과 워크플로우 길이를 줄인다.

## 1. 핵심 결정

시나리오 개수에는 상한을 두지 않는다. 대신 별도 시나리오로 작성할 이유를 명확히 한다.

1. 각 행동 시나리오는 다른 항목과 겹치지 않는 핵심 요구 또는 고유 결함 신호를 검증해야 한다.
2. 같은 실행으로 여러 기대 결과를 판정할 수 있으면 한 시나리오의 여러 assertion으로 합친다.
3. 정적 확인·문서 확인은 Check로 구분하고, 전체 회귀는 최종 Gate에서 한 번 수행한다.
4. 결과를 충분히 증명하는 가장 저렴한 테스트 계층을 사용한다.
5. 모든 AC/C/H는 검증하되 AC/C/H 하나마다 시나리오 하나를 만들지 않는다.
6. 의미상 중복 여부는 evaluator가 권고하고, PM은 각 권고에 반영 또는 유지 사유로 응답한다.

## 2. 문제

현행 기준은 모든 AC/C/H가 시나리오에 연결됐는지와 목표·채택·경계 검증이 충분한지를
판정한다(`opal/core/references/harness/scenario-gate.md:12-21`). 부족한 검증은 잡지만 다음은
잡지 않는다.

- 다른 항목과 같은 실행을 반복하는가
- 다른 항목에 포함돼 독립적인 결함을 찾지 못하는가
- source grep이나 전체 회귀를 행동 시나리오처럼 작성했는가
- 같은 결과를 더 저렴한 계층에서 검증할 수 있는가

그 결과 연결 완전성을 지키기 위해 불필요한 시나리오가 늘어날 수 있다. 시나리오가 늘면 RED
작성, 실행, 증거 기록, 실패 재검증도 함께 늘어난다.

또한 TEST-SCENARIO에는 유형 열이 없고 test-agent 변환 계약도 `type`을 전달하지 않는다
(`opal/skills/op-dev-test-scenario/references/test-scenario-guide.md:24-32`,
`opal/agents/opal-test-agent/AGENT.md:47-52`). 작성자가 선언하지 않은 유형을 워커가 추론하게
되어 분류가 일관되지 않는다.

## 3. 작성 기준

### 3.1 별도 행동 시나리오를 만드는 기준

다음을 모두 만족할 때만 별도 행동 시나리오로 작성한다.

- 공개 인터페이스 또는 사용자가 관찰할 수 있는 결과를 검증한다.
- 다른 시나리오와 구별되는 고유 결함 신호가 있다.
- 실패했을 때 깨진 요구나 위험을 독립적으로 설명할 수 있다.
- 같은 실행으로 이미 충분히 검증되지 않는다.
- 실제 변경 위험에 맞는 테스트 계층을 사용한다.

다른 시나리오에 완전히 포함되고 별도로 찾아내는 결함이 없다면 만들지 않는다.

### 3.2 합치는 기준

다음이 같고 한 번의 출력으로 각 기대 결과를 판정할 수 있으면 한 시나리오로 합친다.

- 실행 명령 또는 사용자 행동
- 실행 환경과 대상 SHA
- 준비 데이터와 사전 상태

기대 결과가 여러 개면 시나리오를 나누지 않고 assertion을 나눈다. 각 assertion의
`expected`와 `actual`은 별도로 기록한다.

다음 중 하나가 있으면 별도로 유지할 수 있다.

- 실행 환경 또는 배포 표면이 다름
- 실행 주체나 사람 handoff가 다름
- 실패 격리 또는 복구 절차가 다름
- 한 실행의 증거로 다른 기대 결과를 판정할 수 없음

### 3.3 Check로 작성하는 기준

다음은 행동 시나리오가 아니라 Check다.

- source grep 또는 정적 구조 검사
- 문서·레지스트리·설정 존재 확인
- lint, typecheck, build, 보안·컨벤션 검사
- AC/C가 전체 회귀 증거 자체를 직접 요구하는 경우의 확인
- 파일이나 명령 결과의 사실 여부를 확인하는 검증

Check도 AC/C/H를 검증할 수 있다. 별도 목록을 만들지 않고 기존 `scenarios[]`와 S-ID를
유지하되 `type: check`로 구분한다. Check는 RED 대상이 아니다.

lint, typecheck, build, 보안·컨벤션 검사와 전체 회귀는 최종 TEST Gate가 이미 수행하므로
관성적으로 S-ID를 만들지 않는다. AC/C가 해당 검사 자체를 직접 요구할 때만 Check로 연결한다.

### 3.4 테스트 계층 선택 기준

결과를 충분히 증명하는 가장 저렴한 계층을 선택한다.

- 순수 로직과 작은 계약은 unit 또는 contract
- 여러 컴포넌트의 실제 연결이 결과를 좌우하면 integration
- 화면·인증·설치본·외부 시스템 등 실제 경로가 결과를 좌우하면 E2E
- 특정 과거 결함이나 기존 공개 계약의 재발 여부를 겨냥하면 regression
- 자동화할 수 없는 관찰은 방법·환경에 manual과 구조화 handoff를 명시

실제 연동이 필요한 검증을 mock이나 manual 표기로 낮추지 않는다. 반대로 unit으로 충분한 결과를
관성적으로 E2E까지 올리지 않는다.

`regression`은 특정 기존 계약이나 과거 결함을 겨냥한 행동 검증이다. 여러 계약을 한꺼번에
확인하는 전체 회귀 스위트는 `regression` 시나리오가 아니라 최종 Gate 검사이며, AC/C가 직접
요구할 때만 Check로 기록한다.

### 3.5 경계 시나리오 기준

실제로 가능한 실패이고 발생 가능성 또는 영향 중 하나가 유의미할 때만 작성한다. 가능성과 영향이
모두 낮은 가상 edge case는 blocking 시나리오로 만들지 않는다. 위험은 별도 카탈로그가 아니라
PLAN `Risks`의 H-N을 사용한다.

## 4. AC/C/H와의 관계

AC/C/H 연결 완전성은 유지한다. 다만 연결 개수와 시나리오 개수는 같지 않다.

- 하나의 시나리오 또는 Check가 여러 AC/C/H를 검증할 수 있다.
- 하나의 AC/C/H가 필요한 경우 여러 검증 항목으로 입증될 수 있다.
- 검증 대상 연결은 기존 `검증 대상` 열을 단일 연결 지점으로 사용한다.
- AC/C/H마다 기계적으로 새 S-ID를 만들지 않는다.

따라서 작성 완료 조건은 “AC/C/H 수만큼 시나리오가 존재함”이 아니라 “모든 AC/C/H가 최소한의
검증 항목으로 충분히 입증됨”이다.

## 5. 문서와 변환

TEST-SCENARIO 표에 `유형` 열을 추가한다.

```markdown
| ID | 유형 | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|---|
| S-1 | integration | AC-1, H-1 | ... | ... | ... | ... | 구현 전 RED |
| S-2 | check | C-2 | ... | ... | ... | ... | 구현 후 |
```

허용 유형은 다음과 같다.

```text
unit | integration | contract | regression | e2e | check
```

유형은 자유 서술에서 추론하지 않는다. 다음 경로가 선언값을 그대로 전달해야 한다.

```text
TEST-SCENARIO 유형
→ scenario-coverage-build
→ coverage payload
→ test-agent 변환
→ test-scenario.json.type
```

`type=check`는 `red_required=false`여야 한다. 반대 조합은 입력 오류로 거부한다. 기존
`red_required` 누락 JSON을 true로 읽는 하위 호환 계약은 유지한다.

### 5.1 전환 규칙

전역 install이 진행 중인 다른 프로젝트를 즉시 막지 않도록 `유형` 열의 존재 여부로 전환한다.

- `유형` 열이 있는 문서: 선언값을 필수로 읽고 허용 enum과 Check/RED 모순을 엄격 검사한다.
- `유형` 열이 없는 기존 문서: builder는 유형 누락만으로 거부하지 않고 test-agent의 기존 변환
  방식을 유지한다.
- 새 가이드로 작성하거나 다시 작성한 TEST-SCENARIO는 반드시 `유형` 열을 사용한다.
- 이미 잠긴 `test-scenario.json`과 완료된 게이트 행은 소급 변환하지 않는다.

`scenario-init`은 `type`을 필수로 검증하므로 기존 문서에서 type을 아예 생략하는 방식은 사용할 수
없다(`opal/tools/test-tool/lib/scenario.py:267-312`). 호환 분기는 문서 입력에서만 적용하고,
생성되는 `test-scenario.json`은 기존처럼 유효한 type을 가져야 한다.

## 6. 판정 기준

### 6.1 도구가 차단할 항목

도구가 확실하게 판정할 수 있는 항목만 하드 게이트로 둔다.

- 중복 S-ID
- 알 수 없는 AC/C/H 참조
- `유형` 열이 있는 문서에서 누락되거나 허용되지 않은 유형
- `check + red_required=true`
- 유형·조건·행동·기대 결과·방법/환경·시점이 모두 같은 정확 중복

기대 결과가 다른 동일 실행 항목은 정확 중복이 아니다. 통합 권고 대상으로 보낸다.

### 6.2 evaluator가 권고할 항목

다음은 의미 판단이 필요하므로 pass 점수와 분리된 `advisories[]`로 반환한다.

- 다른 항목에 포함돼 고유 결함 신호가 없는 후보
- 실행은 같고 assertion만 달라 통합 가능한 후보
- 더 저렴한 계층에서 충분히 검증할 수 있는 후보
- 행동 시나리오와 Check가 잘못 분류된 후보

advisory는 구체적인 S-ID, 판단 근거, 권고 행동을 포함한다. 문장 스타일이나 표현 선호만으로
advisory를 만들지 않는다.

### 6.3 advisory 응답

PM은 각 advisory에 다음 중 하나로 응답한다.

- `apply`: 권고를 반영한다.
- `retain`: 유지 사유를 기록한다.

advisory ID와 응답 ID가 정확히 일치하지 않거나 `retain` 사유가 없으면 게이트를 완료할 수 없다.
응답 내용의 타당성을 도구가 판단하지는 않는다.

`apply`가 하나라도 있으면 모든 반영을 한 묶음으로 수행하고 한 번만 재판정한다. 이 재판정은 기존
반복 상한 3회에 포함하지 않으며 새 advisory를 만들지 않는다.

- PM 기본 경로: coverage와 설계 4축·시나리오 3축 재판정
- 목표-커버 게이트 경로: coverage와 기존 시나리오 3축 재판정
- 통과: 최종 pass
- 실패: `advisory_refinement_failed`로 사용자 대기. PM 기본 경로는
  `status=retry_limit`을 사용해 `reset --owner user` 전 재시작을 막음

## 7. 최소 집행 계약

규칙을 문서 권고로만 두지 않되 새 상태 체계는 만들지 않는다.

### 7.1 PM 기본 경로

기존 `state-tool design-gate record`가 evaluator 결과와 advisory 응답을 함께 받는다.
`state.json.design_gate.history[]`에 응답과 refinement 여부를 기록한다. 기존 bundle hash와
7축 판정 구조를 재사용한다.

`design_gate.history[].verdict`는 기존 다섯 값(`pass`, `rewrite`, `input_error`,
`deterministic_fail`, `superseded`)을 유지한다. advisory 적용은 `verdict: rewrite`와
`reason: advisory_apply`, 재판정 실패는 기존 verdict와 `reason: advisory_refinement_failed`로
구분한다. 재판정 실패 시 `design_gate.status=retry_limit`으로 전이해 기존 사용자 대기와
`reset --owner user` 해제 경로를 재사용한다. state schema에는 advisory 응답과 refinement 여부를
담는 선택 필드만 추가한다.

### 7.2 목표-커버 게이트 경로

`test-tool scenario-gate-record`가 다음만 담당한다.

- coverage와 evaluator 결과 검증
- advisory 응답 완전성 검사
- 현재 TASK·PLAN·TEST-SCENARIO bundle hash 기록
- `.scenario-gate-history.json` 원자 갱신

`op-scenario-gate`의 반환 reason enum에는 `advisory_apply`와
`advisory_refinement_failed`를 추가한다. 목표-커버 게이트 history도 같은 reason과 refinement 여부를
기록한다.

스킬과 PM은 history를 직접 편집하지 않는다.

`state-tool mark`는 `test_scenario.scenario_gate`와 `plan.scenario_gate`를 완료할 때 다음을
검사한다.

- 최신 history가 pass
- 현재 bundle hash가 통과 hash와 같음
- 모든 advisory 응답이 완전함
- refinement가 있었다면 최종 재판정이 pass

이 검사는 `--force`, `--auto-pass`, 마지막 진행률 mark로 우회할 수 없다. `plan.design_gate`는
기존 design-gate record가 상태를 직접 소유하므로 이 가드를 중복 적용하지 않는다.

## 8. 실행과 증거 재사용

동일 SHA·명령·환경에서 한 번 생성한 증거 경로를 여러 검증 항목이 참조할 수 있다.
`test-scenario.json`에 새 필드를 추가하지 않는다.

증거를 공유하려면 출력이 각 항목의 기대 결과를 실제로 포함해야 한다. 이는 문자열 하드 게이트로
판정하지 않고 기존 구조화 verdict에 항목별 assertion `expected/actual`을 기록해 확인한다
(`opal/skills/op-dev-test-scenario/references/test-scenario-guide.md:46`).

전체 회귀는 최종 Gate에서 한 번 수행한다. AC/C가 전체 회귀 증거 자체를 직접 요구할 때만
Check로 연결한다. 수정 반복 중에는 영향받은 항목만 재실행하는 기존 test-cycle 계약을 유지한다
(`opal/core/references/harness/test-cycle.md:22-31`).

## 9. 태스크 164에서 확인된 사례

164의 잠긴 12개 항목을 새 기준으로 분류하면 행동 시나리오 8개와 Check 3개가 된다. 같은
launcher 실행인 S-5·S-8은 한 실행의 여러 assertion으로 통합할 수 있다. source grep, 문서 grep,
그리고 C-3이 직접 요구한 호환성 전체 회귀는 Check에 해당한다. 설치본 환경을 검증하는 S-11은
실행 환경과 충실도가 달라 별도로 유지한다.

이 분석은 기준의 근거로만 사용한다. 164의 잠금과 PASS 증거를 다시 쓰지 않는다. 잠금 해제,
증거 재매핑, 재실행 비용이 개선 효과보다 크기 때문이다.

164에서는 자동 테스트 시간이 측정되지 않았으므로 시나리오 통합의 시간 절감량을 정량 확정하지
않는다. 테스트 시간 미측정 선언과 정량 실행 예산은 이 제안의 구현 범위에서 제외하고 별도 개선
후보로 남긴다.

구현 태스크 자체에서는 시간 대신 작성 결과의 변화를 측정한다. 최초 작성본과 advisory 반영 후
최종본의 행동 시나리오 수, RED 대상 수, Check 수를 기록해 통합이 실제로 일어났는지 확인한다.

## 10. 적용 범위

### 규칙과 변환

- `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md`
- `opal/core/references/harness/scenario-gate.md`
- `opal/core/references/harness/design-gate.md`
- `opal/core/references/harness/test-cycle.md`
- `opal/skills/op-scenario-gate/SKILL.md`
- `opal/agents/opal-evaluator-agent/AGENT.md`
- `opal/agents/opal-test-agent/AGENT.md`

### 도구와 스키마

- `opal/tools/test-tool/lib/scenario.py`
- `opal/tools/test-tool/schema/test-scenario.schema.json`
- `opal/tools/test-tool/lib/e2e_contract.py`
- `opal/tools/state-tool/state_tool.py`
- `opal/tools/state-tool/schema/state.schema.json`
- 관련 도구 테스트

`docs/PROJECT.md`는 구현 결과가 현재 컴포넌트 설명을 바꾸는 경우에만 갱신한다.

### 구현 순서

한 태스크로 구현하되 Work item 순서는 다음과 같이 분리한다.

1. 공통 작성 기준·유형 변환·evaluator 결과 계약
2. PM 기본 경로의 design-gate record와 refinement
3. 목표-커버 게이트 경로의 scenario-gate-record와 mark 가드
4. 두 경로의 회귀 및 install 검증

목표-커버 게이트 경로 구현에 문제가 생겨도 공통 계약과 PM 기본 경로 결과를 독립적으로 검증할
수 있게 파일 소유권과 완료 기준을 나눈다.

## 11. 수용 기준

1. 별도 시나리오는 고유 결함 신호가 있을 때만 작성하도록 가이드가 판정 기준을 제공한다.
2. 같은 실행의 여러 기대 결과는 별도 시나리오가 아니라 여러 assertion으로 작성할 수 있다.
3. 정적 확인은 `type=check`로 구분하고, 전체 회귀는 최종 Gate에서 한 번 수행하며 AC/C가 직접
   요구할 때만 Check로 연결한다.
4. `유형`이 Markdown부터 `test-scenario.json.type`까지 추론 없이 전달된다.
5. 정확 중복만 도구가 거부하고 의미 중복은 advisory로 반환한다.
6. advisory에 응답하지 않고는 두 게이트 경로 모두 완료할 수 없다.
7. advisory 반영 재판정은 기존 반복 상한을 소비하지 않고 한 번만 수행된다.
8. 목표-커버 게이트 경로에서 record를 생략하거나 통과 뒤 문서를 바꾼 상태로 게이트 행을
   mark할 수 없다.
9. 같은 실행 증거를 공유해도 항목별 expected/actual 판정은 유지된다.
10. 기존 잠긴 태스크와 이미 완료된 게이트 행은 소급 변경하지 않는다.
11. 구현 태스크의 최초 작성본과 최종본에 대해 행동 시나리오 수, RED 대상 수, Check 수가
    기록되고 통합 또는 유지 결과를 설명한다.

## 12. 보류 항목

다음은 데이터와 별도 설계가 필요하므로 이번 개선에 포함하지 않는다.

- 시나리오 개수 상한
- 프로젝트별 실행 시간 예산
- 시나리오별 시간 및 명령 서명 저장
- TEST 시간 미측정 선언 게이트
- 별도 위험 카탈로그

## 13. 채택 후 이관

이 제안서는 구현 입력이며 규범 SSOT가 아니다. 구현이 끝나면 작성 기준은
`test-scenario-guide.md`, 판정 의미는 `scenario-gate.md`, 경로별 상태 계약은
`design-gate.md`와 `op-scenario-gate/SKILL.md`, 결정론 집행은 test-tool과 state-tool로
이관한다.

이관과 검증이 끝나면 잔여 규범 인용을 확인하고 이 문서를 `docs/proposals/archives/`로 옮긴다.
