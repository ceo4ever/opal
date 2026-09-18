# opal-pilot-dev

코드 개발 태스크를 처리하는 Dev Pilot 오케스트레이터. `opd`(Full profile)와 `opds`(Short profile) 두 가지 호출 방식을 하나의 스킬이 함께 수행한다.

## 개요

- **Full profile(`opd`)**: TASK → ANALYSIS → PLAN → TEST-SCENARIO → EXECUTE → TEST → CLOSE의 7단계로, 코드베이스 분석부터 시나리오 기반 검증까지 온전한 개발 파이프라인을 수행한다.
- **Short profile(`opds`)**: TASK → PLAN → EXECUTE → TEST → CLOSE의 5단계로, ANALYSIS 단계를 생략한다. 단, 분석 자체를 생략하는 것이 아니라 PLAN을 작성하는 워커가 코드 분석까지 함께 수행한다.
- 두 프로필 모두 EXECUTE 전에 TEST-SCENARIO(테스트 시나리오)를 작성하고 "목표-커버 게이트"로 커버리지를 검증한 뒤에만 구현에 들어간다.
- 사용자가 선택한 프로필을 기본으로 유지하되, 분석·설계 상황에 따라 PM이 트랙 전환(강등/강업)을 제안할 수 있다. 자동 전환은 하지 않는다.

## 언제 쓰나

코드를 실제로 변경하는 개발 작업에 사용한다. 코드를 읽기만 하는 설명 요청, API 명세서 작성, 기획 문서 작성, PR 리뷰, git 작업, 단순 설정 변경에는 이 스킬을 쓰지 않는다.

| 상황 | 프로필 |
|---|---|
| 작업 범위가 명확하고 구조·계약 결정이 거의 남지 않음 | `opds` (Short) |
| 요구사항 해석, 외부 동작·정책, 아키텍처·기술 선택 등 결정이 남아 있음 | `opd` (Full) |
| 판단이 서지 않음 | `opd`로 시작 (fail-safe) |

트랙 전환 기준은 파일 수·변경량이 아니라 "이후 단계에서 외부 영향이 있는 동작·계약·구조 결정을 새로 해야 하는가"이다. 전환은 PM이 근거와 함께 제안하며 사용자 응답 없이 자동으로 바뀌지 않는다.

## 사용법

```
//opd {작업 요청}       # Full profile
//opds {작업 요청}      # Short profile
```

모드 플래그:

| 호출 | 모드 |
|---|---|
| `//opd 작업` / `//opds 작업` | semi-agentic (기본) |
| `--interactive` | 모든 단계 사용자 승인 |
| `--agentic` | 모든 단계 PM 자율 (CLOSE 진입 제외) |

`--pm` 플래그를 지정하면 일부 단계(ANALYSIS·PLAN·EXECUTE)를 PM이 워커 디스패치 없이 직접 수행한다. 단, TEST-SCENARIO의 목표-커버 게이트와 TEST 단계의 실제 실행 검증은 `--pm`과 무관하게 항상 독립된 서브에이전트가 수행한다.

어떤 모드·프로필이라도 **CLOSE 진입은 항상 사용자 승인이 필요**하다.

## 파이프라인

**Full profile(`opd`)**
```
TASK → ANALYSIS → PLAN → TEST-SCENARIO → EXECUTE → TEST → CLOSE
```

- **TASK**: 요구사항 정리.
- **ANALYSIS**: 코드베이스를 분석해 ANALYSIS.md를 작성한다(`op-dev-analysis`).
- **PLAN**: 분석 결과를 바탕으로 실행 계획을 작성한다(`op-dev-plan`).
- **TEST-SCENARIO**: PM이 TASK.md의 수용 기준과 PLAN.md의 위험·작업 항목을 근거로 TEST-SCENARIO.md를 작성하고, `op-scenario-gate`로 커버리지를 검증한다.
- **EXECUTE**: PLAN.md의 작업 항목별로 담당(FE/BE/DB 등)에 맞춰 워커를 병렬 또는 순차 디스패치해 구현한다(`op-dev-execute`).
- **TEST**: 워커(`opal-test-agent`)가 TEST-SCENARIO.md를 실행 명세로 삼아 실제로 검증하고 결과를 기록한다. 실패 시 최대 3회 fix 루핑한다.
- **CLOSE**: DONE.md 생성, 관련 문서 동기화, brain ingest.

**Short profile(`opds`)**
```
TASK → PLAN → EXECUTE → TEST → CLOSE
```
ANALYSIS가 없는 대신 PLAN 워커가 분석을 겸한다. PLAN 완료 직후 EXECUTE 진입 전에 Full profile 전환이 필요한 미결정 사항이 있는지 1회 검토한다.

## 산출물

- Full: `TASK.md`, `ANALYSIS.md`, `PLAN.md`, `TEST-SCENARIO.md`, `test-scenario.json`, `DONE.md`
- Short: `TASK.md`, `PLAN.md`, `TEST-SCENARIO.md`, `test-scenario.json`, `DONE.md`
- (컨벤션 적용 대상이 있는 경우) `GC-CONVENTION-*.md`

## 관련 스킬

- `op-dev-analysis` — ANALYSIS 단계 워커 (Full profile 전용, 코드베이스 분석)
- `op-dev-plan` — PLAN 단계 워커 (실행 계획 수립, Short profile은 분석까지 겸함)
- `op-dev-test-scenario` — TEST-SCENARIO 작성 가이드 (작성 주체는 PM)
- `op-scenario-gate` — TEST-SCENARIO의 목표-커버 게이트 판정
- `op-dev-execute` — EXECUTE 단계 워커 (구현, fix 모드 포함)
- `op-dev-qa` — 필요 시 QA 검증 기준 참조
- `op-task` — TASK 단계 공통 프로세스

## FAQ

### `opds`와 `opal-pilot-dev-short`는 같은 것인가요?
`opds`는 `opal-pilot-dev` 안의 Short profile로 수행되는 canonical 방식이다. `opal-pilot-dev-short`라는 별도 스킬 폴더가 존재하지만, 그 스킬 자체가 `opds` 요청을 `opal-pilot-dev`로 라우팅하도록 안내한다.

### ANALYSIS를 생략하면 분석 품질이 떨어지지 않나요?
Short profile은 "단계를 줄이는 것이지 분석을 줄이는 것이 아니다." PLAN 워커가 ANALYSIS 없이 호출되면 코드 분석을 직접 수행하며, 그 품질은 Full profile과 동일한 기준을 따른다.

### TEST-SCENARIO 작성자가 PLAN 워커와 다른 이유는?
PLAN을 작성한 워커가 스스로 시나리오를 작성하면 자기 확인(self-confirming)이 되기 때문에, TEST-SCENARIO는 PM이 별도로 작성하고 독립된 게이트(`op-scenario-gate`)로 검증한다.

### 트랙 전환은 언제, 몇 번 제안되나요?
`opd`는 ANALYSIS 완료 직후 PLAN 진입 전에, `opds`는 PLAN 완료 직후 EXECUTE 진입 전에 각각 1회만 판정한다. 사용자가 응답하지 않으면 현재 트랙을 유지한다.
