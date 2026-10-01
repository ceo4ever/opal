---
template: sdlc-v2
---
# TASK: PM 설계 경로 단일화와 독립 설계 게이트

## Problem
opd/opds 신규 태스크의 기본 actor인 PM 조율(`coordinator`)은 PM이 분석·PLAN·TEST-SCENARIO를 직접 작성한다(`opal/core/references/harness/actor.md` §PM 조율 계약 역할 분담 표). 그러나 파이프라인은 워커 분리 시절 구조를 그대로 쓴다. 그 결과 설계 구간에 다음 문제가 남아 있다.

- 작성자·검토자·승인자가 같다. opd는 PM이 쓴 ANALYSIS와 PLAN을 같은 PM이 `analysis.pm_gate`·`plan.pm_gate`로 검토하고(`opal/skills/opal-pilot-dev/references/pipeline.json` id 4·7), opds도 `plan.pm_gate`로 자기 검토한다(`pipeline-short.json` id 5). agentic에서는 이 PM Gate가 사용자 대행 승인까지 겸한다(`opal/core/references/opal-harness-agentic.md` §4).
- opd는 같은 PM 컨텍스트에서 ANALYSIS.md를 인계 문서로 따로 쓰고 자기 게이트·확인 행을 거친다. 이 때문에 EXECUTE 전 행이 11개다(`pipeline.json` id 1~11).
- 독립 평가는 설계를 보지 않는다. `op-scenario-gate`의 evaluator는 `scenario_source`만 읽고 시나리오 3축만 채점한다(`opal/agents/opal-evaluator-agent/AGENT.md:120`).
- 요구 누락을 결정론적으로 막지 못한다. `plan-contract-check`는 Work item이 참조한 AC/C가 TASK에 존재하는지만 검사하고, TASK의 모든 AC/C가 Work items에 연결됐는지는 검사하지 않는다(`opal/tools/state-tool/state_tool.py:5553-5564`).
- 검증·승인이 문서 내용에 묶이지 않는다. 게이트 도구 검사는 산출물 존재만 확인하고(`state_tool.py` `check_gate_artifacts`), 사용자 확인 행은 완료 표시만 남긴다. PASS나 승인 뒤 문서가 바뀌어도 EXECUTE 진입을 막는 장치가 없다.
- agentic 공통 반복 규칙은 Normal/Minor 게이트 실패가 3회를 넘으면 기록 후 진행하도록 허용한다(`opal-harness-agentic.md:103-108`). 설계 게이트에 이 규칙을 적용하면 검증되지 않은 설계가 EXECUTE에 들어갈 수 있다.

## Proposed outcome
opd/opds 신규 PM 조율 태스크는 두 트랙이 함께 쓰는 PM 경로 파이프라인으로 시작한다. EXECUTE 전 행은 TASK 작성·TASK 확인·PLAN 작성·TEST-SCENARIO 작성·설계 게이트·설계 확인의 6개다. PM은 PLAN 한 문서 안에서 분석 결과를 구분해 기록하고 설계한다. 설계 게이트는 결정론 검사 뒤 독립 evaluator를 1회 실행해 설계와 시나리오를 각각 판정한다. EXECUTE에는 현재 문서 묶음이 평가를 통과한 묶음이자 해당 모드에서 승인된 묶음과 같을 때만 진입한다. 기존 태스크 재개, `--no-pm` 워커 경로, 다른 Pilot의 동작은 바뀌지 않는다.

## Affected users and systems
- 포함:
  - `opal-pilot-dev`(opd/opds) SKILL·references: PM 경로 파이프라인 파일 신설, 결정 체크포인트
  - `state-tool`: 파이프라인 선택, AC/C 연결 검사, Findings 구분 검사, 해시 기록·검증
  - `op-scenario-gate`와 설계 게이트 harness 문서, `opal-evaluator-agent`의 설계 판정 입력·루브릭
  - `op-dev-plan` 가이드의 PM 경로 Findings 형식
  - `events.json`의 PM 경로 설계 이벤트
  - agentic harness의 PM 경로 설계 구간 한정 개정
  - 관련 회귀 테스트, docs, install 반영
- 사용자: 실제 구현 프로젝트에서 opd/opds를 쓰는 사용자와 PM 에이전트.
- 제외: `--no-pm` 워커 경로의 설계 워커 통합과 `opal-plan-agent` 정의 정리, 워크트리 세션 기동 시점 변경, run-log 측정 확장(사용자 응답 사건·워커 소요 시간 보강·구간 조회), 다른 Pilot의 파이프라인.

## Constraints
- C-1: 새 파이프라인은 opd/opds 신규 태스크 중 actor가 `coordinator`인 경우에만 적용한다. `--no-pm`(`worker`) 신규 태스크, 저장된 행으로 재개하는 기존 태스크, 다른 Pilot의 동작은 바꾸지 않는다.
- C-2: 기존 `pipeline.json`·`pipeline-short.json`과 `stage.analysis`·`stage.plan`·`stage.test_scenario` 이벤트는 삭제하거나 의미를 바꾸지 않는다. opwt·opp·opsdd 등이 이 이벤트를 사용한다.
- C-3: 독립 검증 경계를 유지한다. evaluator는 읽기 전용 판정만 하며, evaluator·opal-test-agent·조건부 보안/컨벤션 검사·실제 실행 증거는 어느 mode에서도 생략되지 않는다.
- C-4: agentic의 사용자 대행 검토를 설계 게이트 판정으로 대체하는 범위는 신규 PM 경로의 설계 구간에 한정한다. TASK·EXECUTE·TEST·CLOSE와 다른 Pilot은 기존 규칙을 따른다.
- C-5: 설계 중 새 결정은 트랙 라우팅의 결정 범위 3종(`opal/skills/opal-pilot-dev/references/track-routing.md` §2)으로 분류한다. 기존 합의로 정할 수 없는 외부 영향 사항은 사용자에게 묻고, 구현 세부는 PM이 정해 기록한다. 권한·안전·실행 불가·재시도 상한에 따른 기존 중단 조건은 유지한다.
- C-6: 게이트 통과, 문서 묶음 일치, EXECUTE 진입 판정은 산문 지시가 아니라 `state-tool`의 상태 저장 전 검사로 집행한다.
- C-7: 분석 책임을 보존한다. 직접 변경·문서 갱신 대상은 Work items에, 회귀 확인 대상은 시나리오에, 미확인 가정은 위험과 검증 방법에 연결한다. 참조나 회귀 확인만 할 파일을 변경 작업으로 만들지 않는다.
- C-8: 플랫폼별 차이는 어댑터 계층에만 둔다. `~/.opal/` 배포본을 직접 수정하지 않고 소스를 수정한 뒤 install로 반영한다.
- C-9: 이 태스크 자체는 착수 시점 설치본의 현행 opds 계약(`pipeline-short.json`, `coordinator`)으로 실행한다. 새 계약은 merge·install 뒤 생성되는 신규 태스크부터 적용한다.
- C-10: 허브 working tree의 기존 미추적 변경(`.claude/skills/`)을 보존하고 이 태스크 커밋에 포함하지 않는다.

## Acceptance criteria
- AC-1: 무플래그 신규 opd·opds 태스크(`coordinator`)의 초기화 인자에 PM 경로 파이프라인 파일이 도구 판정으로 포함되고, 생성된 EXECUTE 전 행이 TASK 작성·TASK 확인·PLAN 작성·TEST-SCENARIO 작성·설계 게이트·설계 확인 6개다. `--no-pm` 신규 태스크는 기존 파일을 받는다(자동 테스트로 확인).
- AC-2: TASK의 AC 또는 C 중 어느 Work item에도 연결되지 않은 항목이 있으면, 시나리오에는 연결돼 있더라도 설계 게이트의 결정론 검사가 실패한다(자동 테스트로 확인).
- AC-3: PLAN에 직접 변경·회귀 확인·문서 갱신·미확인 가정 구분이 없으면 설계 게이트의 결정론 검사가 실패한다(자동 테스트로 확인).
- AC-4: evaluator 설계 판정은 TASK·PLAN·TEST-SCENARIO를 함께 읽고, 요구·변경 범위 완전성, 결정·계약 명확성, 실행 가능성, 적용·복구 가능성 4축을 각각 PASS/FAIL로 판정한다. 한 축이라도 FAIL이거나 시나리오 3축이 기존 기준에 미달하면 게이트는 PASS가 아니다. 외부 동작·인터페이스·실패 정책·구조나 저장 방식 결정을 구현자에게 남긴 PLAN 사례가 FAIL로 판정된다.
- AC-5: rewrite 판정은 대상이 PLAN인지 시나리오인지 명시한다. PLAN이 바뀌면 영향받은 시나리오와 결정론 검사를 다시 수행한 뒤에만 재판정한다.
- AC-6: 설계 게이트 PASS와 설계 승인 시 TASK·PLAN·TEST-SCENARIO 묶음의 해시가 기록된다. 평가 시작 시점과 종료 시점의 입력 해시가 다르면 PASS 기록이 거부된다. EXECUTE 진입 시 현재 묶음·평가 통과 묶음·승인 묶음이 모두 같지 않으면 진입이 거부된다. 문서 변경 뒤 재평가만 통과하고 이전 승인을 재사용하는 경로와, TASK AC/C 변경 뒤 TASK 확인 없이 진행하는 경로도 거부된다(자동 테스트로 확인).
- AC-7: 설계 게이트 FAIL, 입력 오류, 반복 상한 도달 상태에서는 EXECUTE 진입이 거부된다. 반복 상한에 도달하면 심각도와 무관하게 사용자 대기로 전환되고, Normal/Minor 기록 후 진행 규칙은 적용되지 않는다(자동 테스트로 확인).
- AC-8: agentic에서 외부 영향 결정은 사용자 대기로, 구현 세부 결정은 PM 의사결정 기록으로 처리된다. 외부 영향 결정이 없어도 권한 부족·반복 상한 등 기존 중단 조건은 작동한다.
- AC-9: 설계 게이트 실행이 run-log에 게이트 요청·해결 사건으로 기록된다.
- AC-10: PM 경로 설계 구간은 신설 설계 이벤트 하나로 로드되고, 기존 `stage.*` 이벤트의 문서 목록과 opwt·opp·opsdd의 이벤트 매핑은 바뀌지 않는다(자동 테스트로 확인).
- AC-11: 기존 태스크 재개, `--no-pm`, 기존 opd·opds 파이프라인, 다른 Pilot의 회귀 테스트가 모두 통과하고, install 후 설치본에서 새 동작이 관측된다.
- AC-12: 관련 docs(PROJECT.md 레지스트리, opd/opds SKILL·README, agentic harness, 스킬 커맨드 문서 등)가 새 계약으로 갱신되고, PM 경로의 자기 검토 게이트를 현행 계약으로 서술하는 문장이 대상 문서에 남지 않는다.
