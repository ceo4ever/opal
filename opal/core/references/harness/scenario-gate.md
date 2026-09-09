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

반복 상한 수치는 `opal/core/references/opal-harness.md`의 자동 루핑 제약이 소유한다.

## 통과 증거

pass에는 두 증거가 모두 필요하다.

- sdlc-v2 build와 coverage-check exit 0 또는 legacy 정규화 입력의 coverage-check exit 0
- opal-evaluator-agent `scenario-rubric` verdict pass

게이트 호출자는 이 증거 없이 pipeline gate 행을 mark하지 않는다.
반복별 missing·scores·gaps·verdict는 `.scenario-gate-history.json`에 기록하며 별도 Markdown
보고서를 만들지 않는다.

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-07-23 | 최초 작성 — 루브릭 6축·판정주체분리·정규화계약·루프 프로세스·종료조건 3종·tool-gated 집행 SSOT 신설 (073) |
| v1.1 | 2026-08-19 20:59 | §4에 `[MUST]` 호출 시점 규율 블록 신설 — PLAN 확정+보강 완료 후 1회 호출 / 선작성 시점 호출 금지 근거(F·H 미확정 → ③④ 결정론 판정 불가) / state-tool stage-transition guard 정합 (095) |
| v1.2 | 2026-09-02 17:22 | 에이전트명·소유자 호칭 리터럴 제거 — 규범 산문은 역할어(`PM`/`사용자`/`소유자`)로, 산출물·보고 문면은 `{owner_name}` 플레이스홀더로 전환해 런타임에 소유자 호칭으로 대체된다. 프레임워크 재사용성 확보 (L2 직접 수정) |
| v1.3 | 2026-09-09 15:24 | sdlc-v2 AC/C/H/S 정규화와 legacy R/F/H 변환을 분리하고, W를 features로 취급하지 않는 coverage 계약을 반영 (111) |
| v1.4 | 2026-09-09 15:58 | sdlc-v2 tool-gated 증거 체인에 `scenario-coverage-build --template sdlc-v2` 입력 생성을 명시 (111) |
| v1.5 | 2026-09-09 KST | 사례 회고·도구 내부 설명을 제거하고 6축·정규화·종료·통과 증거만 유지. H 없는 정상 태스크를 허용 (111) |
| v1.6 | 2026-09-09 15:33 KST | 반복 판정 증거를 `.scenario-gate-history.json`으로 일원화하고 반복별 Markdown 보고서 생성을 제거 (task 111/W-13) |
