---
template: sdlc-v2
---
# TASK: PM 보고·활동 이벤트·정지 판정 관측 배선

## Problem
agentic 실행에서 PM이 단순 진행 보고를 한 뒤에도 다음 작업을 계속해야 하지만 실제로는 턴이 종료되는 사례가 있다. 현재 태스크 run-log는 상태 전이만 남기고 실질 활동과 PM 보고, Stop hook 판정을 연결해 기록하지 않아 사후에 정지 원인을 재구성할 수 없다. 현행 계약은 `activity` 네 종류를 정의하지만 실제 태스크 로그에는 활동 사건이 기록되지 않았고, Stop 판정은 보고 의도와 후속 활동을 영속 증거로 남기지 않는다 (`docs/run-log/CONTRACT.md` §1.2, `opal/tools/ownership-tool/ownership_tool/stop_hook.py:40-53`).

## Proposed outcome
실질 활동, PM 보고 의도, Stop 집행 결과가 서로 다른 표준 사건으로 기록되고 인과관계로 연결된다. 사용자 결정이 필요한 보고만 정상 정지하며, 그 밖의 보고에서 상태 전이가 계속을 요구하면 Stop hook이 다음 작업을 재개시킨다. 운영자는 run-log만으로 의도된 대기, hook 미실행·허용, 차단 후 재개 실패를 구분할 수 있다.

## Affected users and systems
영향 대상은 agentic·semi-agentic Pilot을 운영하는 사용자와 PM, 태스크 run-log 계약·기록 코어·state-tool, Claude Stop/PostToolUse 어댑터와 ownership-tool이다. 다른 PM이 수행 중인 태스크 146과 그 worktree·branch·terminal은 범위에서 제외한다.

## Constraints
- C-1: `activity`는 `progress`, `validation`, `decision`, `retry` 네 종류의 실질 작업 증거로 유지하고, PM 보고나 Stop 판정 자체를 진행으로 계산하지 않는다 (`docs/run-log/CONTRACT.md` §1.2-1.3).
- C-2: PM 보고는 별도 사건으로 기록하며 보고 유형, 전이 의도, 사용자 입력 필요 여부, 다음 행동과 원문 비노출 식별자를 포함해야 한다.
- C-3: Stop 판정은 별도 사건으로 기록하며 대응 PM 보고와 마지막 실질 활동을 참조하고 허용·차단 이유를 기계적으로 구분해야 한다.
- C-4: 실제 hook 봉투와 실제 태스크 run-log를 우선 실측하고, 합성 fixture만으로 프로덕션 동작을 확정하지 않는다.
- C-5: 원본 프롬프트, 전체 transcript, chain-of-thought, 비밀값은 기록하지 않고 필요한 요약·상대경로·hash만 보존한다 (`docs/run-log/CONTRACT.md` §1.3).
- C-6: 플랫폼별 관측은 adapter에 격리하고 판정 로직은 플랫폼 중립 코어에 둔다 (`/Users/iskang/.opal/PRINCIPLES.md` §Core Stance).
- C-7: 태스크 146의 파일·상태·registry·branch·terminal을 읽기 목적 외에는 변경하거나 제어하지 않는다.

## Acceptance criteria
- AC-1: 네 종류의 `activity`가 신뢰 가능한 실제 관측 원천과 함께 자동 기록되고, 동일 결과 반복이나 heartbeat·단순 보고는 실질 진행으로 오인되지 않는다.
- AC-2: 모든 PM 보고가 별도 표준 사건으로 기록되어 `progress_report`와 `decision_request`, `continue`와 `await_user|blocked|complete`, 사용자 입력 필요 여부를 식별할 수 있다.
- AC-3: 모든 Stop hook 판정이 별도 표준 사건으로 기록되고 대응 보고 사건, 마지막 활동 사건, 판정 종류, 이유 코드와 차단 횟수를 조회할 수 있다.
- AC-4: 사용자 결정 요청은 정상 정지하고, 사용자 결정이 필요 없는 보고에서 `transition_action=continue`이면 Stop이 차단되어 후속 작업이 계속되는 E2E 증거가 존재한다.
- AC-5: 기록만으로 PM의 잘못된 정지 의도, Stop hook 미실행, hook 허용 판정, hook 차단 뒤 후속 활동 부재를 서로 구분할 수 있다.
- AC-6: 실제 hook 경유 통합 테스트와 기존 run-log·ownership-tool 회귀 테스트가 통과하고, 테스트가 합성 직접 호출만으로 구성되지 않는다.
- AC-7: 기록된 사건에 원본 프롬프트·전체 transcript·chain-of-thought·비밀값이 포함되지 않는 검증이 통과한다.
