# OPAL Harness — 이벤트·소유 문서 인덱스

> 이 파일은 구형 `opal-harness.md §N` 참조를 보존하는 호환 shim이다.
> 실행 규칙 원문은 아래 owner 문서가 소유하며, 이벤트별 필수 문서 집합은
> `opal/core/references/events.json`만이 소유한다.

## 이벤트 진입점

| 경계 | 표준 이벤트 | 해석 원천 |
|------|-------------|-----------|
| 세션 | `session.disabled` · `session.worker` · `session.assistant` · `session.project` | `events.json` |
| PM 활성화 | `pm.activate` | `events.json` + `pm/activation.md` |
| pilot 시작 | `pilot.start` | `events.json` |
| 단계 진입 | `stage.task` · `stage.analysis` · `stage.plan` · `stage.test_scenario` · `stage.execute` · `stage.test` · `stage.close` | `events.json` |
| 워커 디스패치 | `worker.dispatch` | `events.json` |

이 표는 탐색 인덱스이며 필수 문서 목록의 사본이 아니다. 소비자는 해당 이벤트를
`event-loader load --event <event-id>`로 해석하고, `receipt_required`가 참이면 반환된
receipt 계약을 충족한 뒤 진행한다.

## 실행 소유 문서

| 주제 | owner 문서 |
|------|------------|
| Guards·승인 경계·자동 루핑 상한 | `harness/guards.md` |
| 모드 판정과 서브 하네스 라우팅 | `harness/modes.md` |
| 워크트리 축과 허브 루트 해석 | `harness/worktree.md` |
| 런타임 capability 주입 | `harness/capability.md` |
| PM 활성화 | `pm/activation.md` |
| State | `harness/state.md` |
| TASK 공통 프로세스 | `harness/task-process.md` |
| Observability | `harness/observability.md` |
| 병렬 실행 | `harness/parallel-execution.md` |
| EXECUTE @header | `harness/header-rules.md` |
| Coding Principles | `harness/coding-principles.md` |
| QA 표준 | `harness/qa-standards.md` |
| 인용 규칙 | `harness/citation-rules.md` |
| 분석 코어 | `harness/analysis-core.md` |
| RED-first | `harness/red-first.md` |
| 시나리오 게이트 | `harness/scenario-gate.md` |
| 트랙 라우팅 | `harness/track-routing.md` |
| 추가작업 | `harness/additional-work.md` |
| State 템플릿 | `harness/state-template.md` |
| 모델 매핑 | `opal-model-mapping.md` |

## 구형 절 참조 호환 매핑

구형 소비자가 이 파일의 절 번호를 가리키면 아래 owner 문서를 읽는다. 이 표는
규칙 내용을 재정의하지 않으며, 소비자 전환이 끝날 때까지 참조 해석만 보장한다.

| 구형 참조 | 새 SSOT |
|-----------|---------|
| `opal-harness.md §1 Guards` | `harness/guards.md` |
| `opal-harness.md §1.5 RED-first` | `harness/red-first.md` |
| `opal-harness.md §2 모듈 구조` 중 모드 라우팅 | `harness/modes.md` |
| `opal-harness.md §2` 중 QA·인용·분석 규칙 | `harness/qa-standards.md` · `harness/citation-rules.md` · `harness/analysis-core.md` |
| `opal-harness.md §2.5 워크스페이스 축` | 축·허브 해석은 `harness/worktree.md`, 생성·설정 부재·복구 절차는 `harness/task-process.md` 스텝 4.5 |
| `opal-harness.md §3 State` | `harness/state.md` · `harness/state-template.md` · `harness/additional-work.md` |
| `opal-harness.md §4 TASK 공통 프로세스` | `harness/task-process.md` · `harness/track-routing.md` |
| `opal-harness.md §5 Observability` | `harness/observability.md` |
| `opal-harness.md §6 Model Mapping` | `opal-model-mapping.md` |
| `opal-harness.md §7 병렬 처리` | `harness/parallel-execution.md` |
| `opal-harness.md §8 EXECUTE @header` | `harness/header-rules.md` |
| `opal-harness.md §9 실행 capability` | `harness/capability.md` |
| `opal-harness.md §10 Coding Principles` | `harness/coding-principles.md` |
