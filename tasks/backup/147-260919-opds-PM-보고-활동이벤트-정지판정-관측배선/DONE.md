# DONE: PM 보고·활동 이벤트·정지 판정 관측 배선

> 완료일: 2026-09-20 10:22 (KST) | 스킬: `//opds --agentic --wt` | 태스크: 147

## 결과

PM의 보고 의도, 워커의 실질 활동, Stop hook의 정지 판정을 서로 다른 표준 사건으로 기록하고 인과 참조로 연결했다. 운영자는 run-log만으로 의도된 사용자 대기, Stop hook 차단·허용, 워커 경계 누락을 구분할 수 있다.

- `pm.report`와 `stop.decision`을 기록 코어의 폐쇄형 사건으로 추가했다.
- 두 사건의 요약은 구조화 필드에서만 결정론적으로 생성하고, 원본 프롬프트·자유 서술이 사건에 복사되지 않게 막았다.
- `state-tool log-event --event pm.report`가 사건과 `run_log.last_report` 파생 포인터를 같은 원자 쓰기로 갱신한다.
- Stop receipt의 `pending_decisions` FIFO를 `state-tool`이 drain하며 `stop.decision`을 적재한다.
- Stop evaluator는 `last_report`의 구조화 의도를 우선하고, 포인터가 없을 때만 기존 상태 추정으로 폴백한다.
- 정지 판정 완전성 진단 5축을 추가해 보고 의도 불일치, 판정 사건 누락, 차단 후 미재개, 앵커 없는 활동을 따로 보이게 했다.
- Claude Code의 현행 `Agent`와 legacy `Task` 완료 훅을 단일 어댑터로 정규화해 A1 조합의 `worker.started`·`activity`·terminal을 방출한다.

## 변경 영역

| 영역 | 핵심 산출물 |
|---|---|
| 기록 계약·코어 | `docs/run-log/CONTRACT.md`, `surfaces.json`, `run_log_core.py`, `run_log_tool.py` |
| PM 보고·완전성 | `state_tool.py`, `state.schema.json`, state-tool 테스트·README |
| Stop 판정·receipt | ownership resolver·evaluator·hook·fingerprint·core, 실훅 subprocess 테스트 |
| 워커 어댑터 | `agent_tool_adapter.py`, `test_agent_tool_adapter.py`, Claude hook 정의, macOS install 배포 |
| 운영 문서 | run-log·state-tool·ownership-tool README, harness state·modes |
| 태스크 증거 | TASK·PLAN·TEST-SCENARIO, `test-scenario.json`, AGENTIC-LOG, 실측 evidence |

태스크 146의 소스·상태·워크트리는 이 태스크의 변경 집합에 포함되지 않았다. 146 소유 세션이 독립적으로 수행한 install·lifecycle 변화는 AGENTIC-LOG에 분리 기록했다.

## 검증

- 시나리오: S-1~S-19 `19/19 PASS`, FAIL 0, BLOCKED 0.
- RED: 필수 10건 모두 구현 전 실패 증거 확인.
- 최종 전체 회귀: run-log-tool·state-tool·ownership-tool 3개 디렉터리 `709 passed, 3 skipped, 431 subtests passed`.
- 실제 Claude Code 2.1.278 `Agent` 호출: 동일 worker run에 `worker.started`·`activity`·`worker.completed` 각 1건, A1 조합·어댑터 귀속 확인.
- 실제 PM 흐름: `pm.report` `evt_7144a862-b15c-4f39-ae28-1f837ddb2903`과 `last_report` 3축 일치, 이어진 `stop.decision` `evt_599421dd-f6e4-4d60-881c-9cf5072de23f`의 인과 참조 일치.
- 시나리오 충실도: 19/19 충족. 요구사항 14건·가설 5건 모두 커버.
- PLAN 계약·code-scan 인용·state validate·`git diff --check` 통과.
- CLOSE 변경 파일 code-scan: `ok:true`, `newly_uncovered=0`. 기존 파일의 `pre_existing` 7건과 `header_history` 3건은 도구 계약상 비차단 진단.

## 배포·채택 결과

macOS install 경로로 최신 어댑터와 hook 정의를 `~/.opal/` 배포본에 반영했다. 소스와 배포본 `agent_tool_adapter.py` SHA-256 일치를 확인했다. install 말미의 비필수 홈 전체 Console scan은 이 태스크가 시작한 프로세스만 중단했고, 다른 태스크의 install 프로세스는 건드리지 않았다.

## 문서·제안서 생명주기

구현으로 달라진 사실은 계약서, 도구 README, harness state·modes, 배포 hook에 동기화했다. 이 태스크의 TASK·PLAN 참조 문서와 변경 집합에 `docs/proposals/` 파일은 없어 제안서 아카이브 판정은 자연 스킵한다.

Project Brain의 `mock-only-adapter-verification-passes-schema-drift` 초안에 태스크 147의 Claude Agent 훅 이름·terminal 봉투 실측 사례와 시작·중간·종료 3경계 검증 규율을 통합하고 `draft → active`로 승격했다. 해당 페이지의 lint 위반은 0건이다. brain 전체 validate의 `sources/` 필수 디렉터리 부재 1건과 전체 lint 35건은 기존 골격·페이지 진단으로 이번 지식 갱신 범위 밖이다.

## 회고

표면 계약과 단위 테스트만으로는 실제 플랫폼 채택을 확정할 수 없었다. Claude Code 실행을 붙이자 완료 hook 이름이 `Task`에서 `Agent`로 바뀌 사실과 terminal 원천이 legacy 알림에서 구조화 `toolUseResult`로 바뀌 사실이 두 번에 걸쳐 드러났다. 플랫폼 어댑터는 문서화된 예상 봉투만이 아니라 설치본의 실제 호출로 시작·중간·종료 3경계를 끝까지 증명해야 한다.

또한 어댑터 사건의 `recorded_by.id`가 actor가 아니라 변환기 식별자를 가리켜야 사후 감사에서 채널 귀속을 복원할 수 있음을 확인했다. 이 계약은 선택 인자와 후방 호환 폴백으로 해소했다.

## 종료 경계

- CLOSE 후 캘틴의 명시 승인으로 태스크 커밋을 생성했으며, merge·push·worktree 제거는 수행하지 않는다.
- CLOSE 최종 상태는 `completed_unmerged`이다.
- merge 후 허브가 `finalize-attribution` 및 MEMORY history 결과 보강을 수행한다.
