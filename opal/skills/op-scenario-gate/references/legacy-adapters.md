# Scenario gate legacy adapters

> `template: sdlc-v2`가 아닌 기존 태스크의 gate를 재개할 때 현재 pilot 절만 읽는다.
> 신규 opd/opds 태스크에서는 읽지 않는다.

모든 소스와 출력은 `task_folder` 안에 있어야 한다. 결과는 공통 정규화 계약에 맞춘
`.scenario-coverage-input.json` 한 파일이다.

## opd

| 정규화 필드 | legacy 소스 |
|---|---|
| `goal` | TASK 목표 또는 배경의 목표 문장 |
| `requirements` | TASK의 R-ID |
| `features` | PLAN의 F-ID |
| `hypotheses` | PLAN 리스크 가설 또는 TEST-SCENARIO §1의 H-ID |
| `scenarios` | TEST-SCENARIO §4 추적 매핑의 시나리오 행 |

## opds

opd와 같은 R/F/H/시나리오 매핑을 사용한다. producer는
`<task_folder>/TEST-SCENARIO.md`다.

## opsdd

| 정규화 필드 | legacy 소스 |
|---|---|
| `goal` | TASK 목표 문장 |
| `requirements` | SPEC의 FR-NN |
| `features` | SPEC의 AC-NN |
| `hypotheses` | SPEC의 EC-NN |
| `scenarios` | TEST-SCENARIOS 추적 매트릭스의 각 행 |

opsdd 시나리오 행은 대응 AC의 FR 역참조를 `covers_requirements`, AC 자체를
`covers_features`, EC 기원일 때 EC를 `covers_hypotheses`에 둔다.

## 판단 플래그

각 시나리오에 다음 값을 문서 근거로 설정한다.

- `is_goal_scenario`: 사용자 또는 운영 결과를 직접 검증함
- `is_adoption_scenario`: 교체형 목표의 구형 잔존 또는 신형 채택을 검증함
- `is_boundary_scenario`: 실패, 거부, 경계값을 검증함

문서에 근거가 없으면 `false`다. 채점을 통과시키기 위해 추정하지 않는다.

## 변경이력

| 버전 | 날짜 | 변경내용 |
|---|---|---|
| v1.0 | 2026-09-09 15:33 KST | op-scenario-gate SKILL의 opd·opds·opsdd legacy 변환 계약을 조건부 참조로 분리 (task 111/W-13) |
