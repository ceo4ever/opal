---
module: scenario-gate
role: TEST-SCENARIO 목표-커버리지 게이트 규칙 SSOT
load: op-scenario-gate 호출 시
상속: opal/core/PRINCIPLES.md §4
---

# TEST-SCENARIO 목표-커버리지 게이트

## 판정 축

| 축 | 확인 내용 | 판정 주체 |
|---|---|---|
| 목표 달성 | 사용자·운영 결과를 직접 검증하는 시나리오가 있는가 | evaluator |
| 요구 커버 | sdlc-v2 AC/C 또는 legacy R/AC가 모두 시나리오에 연결되는가 | test-tool |
| 기능 커버 | legacy 또는 별도 기능 ID가 모두 연결되는가 | test-tool |
| 위험 커버 | PLAN에 H가 있으면 모두 연결되는가 | test-tool |
| 채택·잔존 | 교체형 목표의 구형 잔존 0과 신형 채택을 검증하는가 | evaluator |
| 경계·부정 | 실패·경계 조건을 검증하는가 | evaluator |

요구·기능·위험 커버는 결정론 도구가 판정하고, 목표·채택·경계의 충분성은 독립 evaluator가 판정한다. 서로의 판정을 대신하지 않는다.

## 정규화 입력

```json
{
  "goal": "목표 문장",
  "requirements": ["AC-1", "C-1"],
  "features": [],
  "hypotheses": ["H-1"],
  "scenarios": [{
    "id": "S-1",
    "covers_requirements": ["AC-1", "C-1"],
    "covers_features": [],
    "covers_hypotheses": ["H-1"],
    "is_goal_scenario": true,
    "is_adoption_scenario": false,
    "is_boundary_scenario": true
  }]
}
```

- sdlc-v2는 AC/C를 `requirements`, S를 `scenarios`로 변환한다.
- PLAN에 실제 H가 있을 때만 `hypotheses`를 채운다. H가 없으면 빈 배열을 허용한다.
- sdlc-v2 W는 실행 단위이므로 `features`에 넣지 않는다.
- pilot별 문서를 이 입력으로 바꾸는 책임은 op-scenario-gate가 소유한다.

## 게이트 흐름

1. Producer인 PM이 TEST-SCENARIO를 작성한다.
2. test-tool build/check가 정규화와 매핑 누락을 판정한다.
3. 결정론 검사가 통과한 경우에만 독립 evaluator가 목표·채택·경계 축을 판정한다.
4. 둘 다 통과하면 pass다. 누락이나 gaps가 있으면 PM이 해당 항목만 보완하고 같은 gate iteration을 올려 다시 실행한다.

Producer와 evaluator는 매 반복 분리한다. 사용자는 현재 진행 모드의 사용자 확인 행에서 결과를 검토한다.

## 종료 조건

- **pass**: 커버 누락 0, evaluator 각 축 0점 없음, 평균 1.5 이상
- **rewrite**: 보완 가능한 missing 또는 gaps가 있고 반복·무진전 상한 전
- **escalate**: 하네스 반복 상한 초과 또는 연속 2회 개선 없음
- **input error**: 문서 파손, 알 수 없는 참조, 필수 AC/C 부재, S 0건, 중복 S-ID. 재작성 verdict가 아니라 입력 블로커로 반환한다.

반복 상한 수치는 `opal/core/references/harness/guards.md` §자동 루핑 제약이 소유한다.

## 통과 증거

pass에는 두 증거가 모두 필요하다.

- sdlc-v2 build와 coverage-check exit 0 또는 legacy 정규화 입력의 coverage-check exit 0
- opal-evaluator-agent `scenario-rubric` verdict pass

게이트 호출자는 이 증거 없이 pipeline gate 행을 mark하지 않는다.
반복별 missing·scores·gaps·verdict·advisories는 `test-tool scenario-gate-record`가 매 회차
1회 `.scenario-gate-history.json`에 기록한다. `op-scenario-gate` 스킬은 이 파일을 직접
append하지 않는다. 별도 Markdown 보고서는 만들지 않는다.

`state-tool mark`가 `test_scenario.scenario_gate`·`plan.scenario_gate` 행을 완료로 바꿀 때는
형제 `test-tool scenario-gate-verify`로 마지막 기록이 pass이고 현재 문서 묶음과 일치하는지
확인한다. 불일치·부재는 `scenario_gate_record_required`로 거부되며 `--force`로 우회할 수 없다.

## advisory와 refinement

evaluator 결과의 `advisories[]`는 pass 판정 점수와 분리된 권고다 — 시나리오가 다른 시나리오에
완전히 포함되거나(`subsumed`), 합칠 수 있거나(`mergeable`), 더 저렴한 계층으로 충분하거나
(`cheaper_layer`), Check·행동 시나리오 분류가 틀렸음(`misclassified`)을 가리킨다. advisory는
판정을 바꾸지 않으며, pass 회차에 advisories가 1건 이상이면 PM의 응답(`apply`|`retain`, retain은
사유 필수)을 요구한다.

응답에 `apply`가 1건 이상이면 그 회차는 `rewrite`/`reason: advisory_apply`로 기록되고 상한을
소비하지 않는다. PM은 advisory를 문서에 반영한 뒤 **refinement 회차**(다음 회차, 도구가 이력으로
판정)를 1회만 거친다. refinement 회차는 상한을 소비하지 않지만 실패하면(`reason:
advisory_refinement_failed`) 반복 상한 도달과 동일하게 사용자 대기로 전이하며 재시도하지 않는다.
refinement 회차의 evaluator 결과에 비어 있지 않은 `advisories[]`가 와도 응답 없이 무시하고
이력에는 `advisories: []`로 기록한다.
