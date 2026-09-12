---
template: sdlc-v2
---
# TEST-SCENARIO: E2E profile·verdict 계약 도입

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: task_125 worktree의 source `opal/tools/test-tool/`, Python unittest 실행 환경, public `opal/tools/test-tool/run.sh`, 임시 디렉터리에 만든 격리 설치본.
- 공통 데이터: profile별 surface/actor fixture, legacy fallback·escalation payload, assertion expected/actual 및 required/observed evidence fixture, v1/v2 scenario JSON, human handoff/resume fixture.
- 대역 사용과 한계: cmux/provider 응답과 Human 제출은 결정론 fixture로 대역한다. 이는 adapter·verdict 계약만 검증하며 실제 Browser/API/Human executor의 연동 증거를 대신하지 않는다. 실제 executor와 Runtime Manager는 이번 태스크 범위 밖이다.
- 실행 조건: 자동 실행. 설치 검증은 사용자 전역 `~/.opal/`을 수정하지 않고 임시 `OPAL_HOME` 또는 동등한 격리 경로에서만 수행한다.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1, C-1, C-6 | Browser/API/Hybrid/Collaborative/Manual 표면·actor fixture와 profile별 executor 조합이 준비됨 | 공개 contract API로 profile을 resolve하고 surface/profile 및 executor matrix를 검증 | 다섯 profile이 고유하게 판정되고 허용 조합만 통과하며 Web UI→API, API→무근거 Browser, Hybrid→단일 executor 불일치는 `surface_profile_mismatch`로 거부됨 | `test_e2e_contract.py` unit, 플랫폼 중립 fixture | 구현 전 RED |
| S-2 | AC-2, C-2 | final 5상태와 `awaiting_human` fixture가 준비됨 | 각 상태를 public CLI verdict 경로에 입력하고 process exit와 error를 관찰 | `pass=0`, `fail=6`, `infra_error=7`, `executor_unavailable=18`, `blocked=19`, `awaiting_human=20`이며 `awaiting_human`은 final status 목록에 포함되지 않음 | contract unit + `run.sh` subprocess | 구현 전 RED |
| S-3 | AC-3, C-5 | reason별 legacy fallback/escalated/escalate payload, `wait_failed`의 세 wait kind와 누락/unknown payload가 준비됨 | legacy normalizer와 public CLI 출력에 각 payload를 입력 | provider 부재 두 reason만 후보 내부 `provider_unavailable`; assertion wait만 `fail`; 나머지 명시 오류·누락·unknown은 `infra_error`; 신규 JSON 어디에도 `fallback`, `escalated`, `escalate`, `escalation` 키/상태가 생성되지 않음 | contract table-driven unit + CLI subprocess | 구현 전 RED |
| S-4 | AC-4, C-3 | 첫 Browser 후보가 provider 부재/제품 실패/assertion 실패/인증·데이터·증적 실패를 각각 반환하고 두 번째 후보가 성공하도록 대역됨 | candidate switch guard와 integration adapter를 실행 | `provider_unavailable`일 때만 두 번째 후보가 실행됨; 그 외 실패에서는 호출 횟수가 1이고 최초 `fail` 또는 `infra_error`가 보존되며 후보 성공으로 덮이지 않음 | adapter unit, fake provider 호출 횟수·최종 JSON 단언 | 구현 전 RED |
| S-5 | AC-5, C-4 | open/navigate/close만 성공한 Browser 결과, expected/actual 한쪽 누락, required evidence 일부 누락, 모두 충족한 fixture가 준비됨 | verdict builder, scenario-mark, fidelity gate에 각 fixture를 입력 | 누락 fixture는 `pass`·`real-usage` 저장이 거부되고 구체 error를 반환함; semantic assertion과 필수 증적을 모두 충족한 fixture만 `pass` 및 `real-usage`가 됨 | contract/scenario unit + `scenario-mark` subprocess | 구현 전 RED |
| S-6 | AC-6, C-1, C-4 | Web UI 요구에 API executor만 둔 fixture와 Hybrid 요구에 Browser+API assertion/state evidence를 둔 fixture가 준비됨 | surface match와 pass validator를 실행 | API-only Web UI는 실패함; Hybrid는 핵심 UI 행동 assertion과 후속 API/state assertion·evidence가 모두 있어야 통과하고 어느 한 축 누락 시 실패함 | contract unit, executor/evidence 조합 table | 구현 전 RED |
| S-7 | AC-7, C-2, C-4, H-1 | Collaborative/Manual scenario와 handoff id·instruction·expected observation·required evidence·timeout·resume token·submission fixture가 준비됨 | 최초 human step, 자유 형식 완료 선언, 구조화 submission 재개를 순서대로 scenario-mark에 입력 | 최초 단계는 exit 20의 `awaiting_human`; 자유 형식 선언은 pass가 아님; 올바른 run/token과 구조화 evidence를 deterministic verifier가 확인한 뒤에만 final status로 전이하며 불일치 제출은 거부됨 | scenario contract unit + `scenario-mark --verdict-json`/resume subprocess | 구현 전 RED |
| S-8 | AC-8, C-5, H-2 | 기존 v1 scenario fixture, 신규 v2 valid/invalid fixture와 JSON schema가 준비됨 | scenario-init/status/lock/mark/fidelity/conformance에 v1을 읽히고 v2를 생성·검증하며 invalid v2를 입력 | v1은 명시 legacy defaults로 읽히고 기존 비-E2E 동작이 유지됨; 신규 출력은 schema version 2.0과 구조화 필드를 가짐; enum·필수 필드·surface/executor/evidence가 잘못된 v2는 schema와 runtime validator 양쪽에서 거부됨 | `test_scenario.py` unit + scenario CLI subprocess + schema fixture 검사 | 구현 전 RED |
| S-9 | AC-8, C-6 | project/global/infer 설정과 기존 resolve/check/unit/integration/scenario 회귀 fixture가 준비됨 | resolver 우선순위와 source test-tool 전체 unittest suite를 실행 | project→global→infer 순서 및 기존 비-E2E 명령 계약이 유지되고 전체 suite exit 0; 특정 IDE·agent runtime 이름이 core contract에 추가되지 않음 | source unittest discover + 결정론 source 검사 | 구현 후 |
| S-10 | AC-8, AC-9, C-2, C-4, C-7 | PLAN W-6/W-7의 agent·pilot·README·tools 변경이 완료됨 | 관련 소비자에서 E2E 상태/real-usage 정의와 legacy 출력 토큰을 결정론적으로 검사하고 변경 파일 범위를 PLAN과 대조 | final 5상태와 `awaiting_human`이 손실 없이 전달되고 real-usage는 공통 contract를 참조함; E2E `fallback/escalated/escalate` 신규 생성 지시는 0건이며 별도 scenario-rubric의 `verdict=escalate`는 보존됨; Runtime Manager/driver/session/Playwright 제거 변경은 0건 | grep/정적 계약 검사 + `git diff --name-only` | 구현 후 |
| S-11 | AC-9, C-6, C-7, H-3 | source suite가 통과했고 빈 임시 설치 root가 준비됐으며 사용자 전역 설치본은 비교용 read-only임 | source 도구 트리를 임시 `OPAL_HOME`에 설치/복사한 뒤 contract/schema 핵심 파일 parity와 installed `run.sh` status→exit/legacy-key smoke를 실행 | source와 격리 설치본이 동일 계약을 내고 smoke가 모두 exit 기대값을 충족함; 사용자 `~/.opal/` 변경은 0건이며 설치 불가 시 AC-9를 성공 처리하지 않고 실패 명령·사유가 보고됨 | source unittest + 임시 설치본 unittest/CLI subprocess + checksum/diff | 설치 후 |
