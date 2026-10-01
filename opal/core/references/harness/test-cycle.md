---
module: test-cycle
role: TEST 진입·실행·반복·최종 게이트의 단일 SSOT
load: stage.test
---

# TEST 실행 주기

이 계약은 opd/opds의 TEST 단계에 적용한다. 독립 실행·판정은 `opal-test-agent`가 수행하고 PM은 증거를 검토한다. `test-tool`의 시나리오 상태와 구조화 handoff·verifier 계약은 그대로 따른다. 기존 태스크에 새 계측 값이 없으면 알 수 없음으로 보고하고 사후 행 시각으로 추정하지 않는다.

## 진입과 병행 실행

1. 자동 검사를 시작하기 전에 `worktree-tool divergence --project-root <허브 절대경로> --task <NNN>`으로 registry의 동결 `base_ref`와 worktree HEAD의 repo별 `ahead`·`behind`를 확인한다. 조회 실패·미확인은 통과가 아니다. `integration_required=true` 또는 어느 repo든 `behind>0`이면 통합을 요청하고 TEST 시작을 보류한다. merge 승인과 통합은 별도 권한 경계이며, 통합 뒤 다시 조회해 `behind=0`을 확인한다.
2. PM이 TEST-SCENARIO.md의 모든 사람 전용 step과 handoff, 로그인·DDL·권한·관찰 등 선행 조치를 추출한다. 필요한 입력·실행 방법·제출 증거·기한을 **한 요청**으로 먼저 전달한다. 자동 테스트 결과를 기다렸다가 사람 조치를 순차 요청하지 않는다. 사람 항목이 없으면 요청과 human interval을 생략한다.
3. PM은 묶음 요청 발송 시 `state-tool test-clock start <task> --kind human --id <handoff-id>`를 각 handoff ID에 대해 정확히 한 번 호출한 뒤, 요청 증거와 열린 ID 목록을 `opal-test-agent`에 주입하여 디스패치한다. test agent는 요청·시작 ID를 확인하되 사람 요청이나 human start를 반복하지 않는다. 결측·불일치면 PM에 BLOCKED로 반환한다. test agent가 `test-clock start <task> --kind auto --id <실행-id>`를 호출해 자동 시나리오를 실행하고 직후 `auto` stop을 호출한다. 자동 실행은 사람 제출 대기와 병행한다. 각 사람 제출은 같은 run-id/resume-token의 구조화 submission을 verifier가 처리한 뒤에만 PM이 해당 `human` stop을 호출한다. PM이 이 종료 호출을 test agent에 명시 위임한 경우에만 agent가 대신 호출한다. 제출자의 완료 선언만으로 PASS를 기록하지 않는다. 중복 start·열리지 않은 interval의 stop은 오류로 다룬다. 열린 interval은 `test-metrics`에 열린 상태로 남긴다.
4. `test-tool scenario-mark`와 `scenario-status`에 실제 출력·exit code·verifier 결과를 남긴다. TEST-SCENARIO.md 명세에 결과를 덧쓰지 않는다. 사람 대기가 남으면 `awaiting_human`을 유지하고 자동 검사 결과를 먼저 보고한다.

## 병렬 그룹 실행

서로 독립인 자동 시나리오는 한 에이전트 안에서 동시 실행해 벽시계 시간을 줄인다. 병렬 단위는 한 `opal-test-agent`의 한 번의 Bash이며, 여러 에이전트를 동시에 디스패치하지 않는다.

1. **선언**: 작성자가 TEST-SCENARIO Setup에 `병렬 그룹: S-a, S-b, ...` 줄로 선언한 시나리오끼리만 동시 실행한다. 선언이 없거나 선언에 없는 시나리오는 순차 실행한다. 에이전트가 병렬 대상을 추정하거나 추가하지 않는다. 선언은 Setup 문서 줄이며 `test-scenario.json` 스키마에 필드를 추가하지 않는다.
2. **실행**: 에이전트는 그룹의 명령을 한 번의 Bash에서 `&`로 띄우고 `wait`로 모두 기다린다. 시나리오별 stdout과 종료 코드를 각각 파일로 저장한다(`wait <pid>`로 종료 코드를 개별 수집).
3. **시간 기록**: 그룹 전체를 `test-clock`의 auto 구간 하나로 기록한다(`start <task> --kind auto --id batch-N` → 그룹 종료 직후 stop). 시나리오마다 구간을 열지 않으며, 그래야 `auto_seconds`가 구간 합산으로 부풀지 않고 그룹 벽시계 시간이 된다.
4. **기록**: `test-tool scenario-mark`와 `test-clock` 호출은 그룹 실행이 끝난 뒤 에이전트가 순차로 한다. 판정은 시나리오별 저장 파일을 증거로 `opal-test-agent`가 기록하며, TEST 보고에 `batch-N`, 시나리오별 출력·종료 코드 파일 경로, 그룹 벽시계 시간을 남긴다.

**다중 에이전트 병렬은 채택하지 않는다.** 근거는 `tasks/172-261001-opd-검증-시간-단축/run/PARALLEL-PROBE.md`의 실측이다. 단일 에이전트 안 병렬은 가능하다(중앙값 비율 0.250, 출력·종료 코드 보존). 반면 여러 프로세스의 동시 `scenario-mark`는 5라운드에서 기록이 사라진 시나리오가 6건 관측됐고 `opal/tools/test-tool/lib/scenario.py`에 파일 잠금이 없다. 또 에이전트마다 auto 구간을 열면 `auto_seconds`가 구간 합산이 되어 벽시계와 달라진다. 대안은 후속 태스크에서 `scenario-mark` 잠금을 도입하고 auto 구간을 합집합으로 계산하는 것이다. 그 전에는 이 절의 단일 에이전트 절차만 쓴다.

## 실호출 시나리오

에이전트·외부 서비스를 실제로 호출하는 시나리오는 TEST-SCENARIO의 방법·환경 열에 `[실호출 1회]` 표지가 있는 행이다.

1. 실행 주체는 `opal-test-agent`다. Bash로 헤드리스 `claude -p --agent <이름>`을 시나리오당 **1회** 실행한다. 설치 전 단계에서 저장소 정의를 쓰려면 `--agents` JSON으로 저장소의 에이전트 정의를 지정한다. 반복 호출하지 않는다.
2. 원본 JSON 응답을 증거 파일로 저장하고, 그 파일을 기대 결과와 대조해 판정한다. 요약·가공본만으로 판정하지 않는다.
3. 헤드리스 호출이 불가능하면 `blocked`로 반환한다. PM은 직접 수행하거나 우회 판정하지 않고 사용자에게 보고한다(`actor.md` §독립 검증 경계 유지).

## EXECUTE 증거 재사용

EXECUTE의 lint·type/build·unit PASS는 **현재 TEST 대상과 동일한 commit SHA**, 동일한 명령과 환경 서명(도구·의존성·설정·실행 환경), 읽을 수 있는 PASS 출력 증거 경로가 모두 확인될 때만 TEST에서 재사용한다. TEST 보고에 각 항목의 SHA·정확한 명령·환경 서명·PASS 증거 경로와 재사용 판정을 기록한다. 하나라도 다르거나 증거가 없으면 `opal-test-agent`가 다시 실행한다. 재사용은 독립 TEST 시나리오 실행·판정을 대체하지 않는다. 이를 위해 `test-scenario.json` 스키마에 필드를 임의로 추가하지 않는다.

같은 commit SHA·같은 명령·같은 환경 서명의 증거 경로는 여러 S-ID가 함께 참조할 수 있다. 판정은
S-ID별 assertion의 `expected`/`actual`로 개별 기록하며, 증거를 공유한다고 해서
`test-scenario.json`에 필드를 추가하지 않는다.

## 수정 반복

- TEST 추가 행의 삽입 기준은 `state-tool show`에서 확인한 **마지막 TEST 추가 행의 key**다. 아직 추가 행이 없으면 `test.run_tests`를 기준으로 한다. `add-row --after-task-step <기준 key>`를 사용하고 도구가 반환한 새 `key`를 다음 반복의 기준으로 보관한다. 행 번호는 사용하지 않는다.
- TEST 실패 수정은 `state-tool add-row <task> --stage TEST --test-change-kind fix ...`로 기록한다. `opal-test-agent`의 FAIL/BLOCKED S-ID와 변경 파일에 영향받는 S-ID를 합쳐 재실행한다. 영향 관계가 없거나 불확실하면 해당 시나리오 묶음 전체를 포함한다. 재실행하지 않은 PASS는 기존 증거를 유지하되 변경 SHA가 그 시나리오에 영향이 없다는 근거를 TEST 보고에 남긴다. 회귀가 발견되면 수정 루프를 중단하고 에스컬레이션한다. `guards.md` §자동 루핑 제약의 오류 종류별 상한을 따른다.
- 현재 목표·수용 기준을 충족하기 위한 사용자 피드백과 TEST 지적은 정상적인 수정으로 받아 `fix`에 기록한다. 합의된 목표·수용 기준 자체를 새로 바꾸는 요청만 `requirement_change`로 별도 기록한다. 이 계수는 소요 분석용이며 횟수로 수용을 거부하지 않는다. 새 요청이 현재 범위를 벗어나 계획·일정·외부 계약을 바꿔야 할 때만 내용을 기준으로 사용자와 새 태스크 또는 PLAN 재진입을 결정한다. legacy 미분류 TEST 행은 분류를 추정하지 않는다.
- 수정 중에는 전체 회귀·보안·컨벤션 checker를 매 반복의 필수 호출로 삼지 않는다. 실패와 영향 범위의 검증 결과를 먼저 확정하고 마지막 수정 뒤 아래 최종 게이트를 수행한다.

## 최종 TEST PM Gate

`opal-test-agent`가 모든 필수 S-ID의 구조화 PASS 증거를 확인하고, 마지막 수정 기준으로 **전체 회귀 1회**와 보안 검사 1회를 독립 실행한다. lint·type·unit은 위 재사용 조건을 각각 판정하고 불충족 항목을 실행한다. 컨벤션 적용 파일이 있으면 마지막 수정 뒤 `opal-convention-checker`를 **최종 1회** 호출하여 Critical/High 0건을 확인한다. 최종 검사 뒤 수정이 생기면 영향 시나리오를 다시 검증하고 변경으로 무효화된 최종 증거를 갱신한 다음 게이트를 재판정한다. PM은 독립 워커의 증거·보고서를 확인하며 직접 PASS를 대신 선언하지 않는다.

`state-tool test-metrics <task>`로 실제 start/stop 사건에 기반한 `auto_seconds`, 겹친 대기 구간의 합집합인 `human_wait_seconds`, `fix_count`, `requirement_change_count`, 열린 구간과 legacy 미분류 행을 조회한다. 기록이 없는 시간은 unknown이며 행 mark 시각으로 보충하지 않는다.
