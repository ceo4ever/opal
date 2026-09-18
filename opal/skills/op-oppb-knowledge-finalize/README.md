# op-oppb-knowledge-finalize

> 이 스킬은 사용자가 직접 호출하지 않습니다. `opal-pilot-project-build`(oppb)가 P5 MERGE · KNOWLEDGE · CLOSE 단계의 `p5.knowledge_batch`에서 디스패치합니다. 프로젝트당 정확히 1회만 실행됩니다.

프로젝트 전체에서 모인 지식 후보에서 실패·폐기분을 제거하고, 기존 `memory-tool`·`brain-tool`을 프로젝트 batch로 정확히 한 번 호출해 허브 MEMORY·brain에 반영하는 OPPB P5 단계 스킬입니다.

## 역할

OPPB에서 MEMORY와 brain은 이 단계 전까지 읽기 전용입니다. 미니 태스크는 지식을 직접 쓰지 않고 `result.json`에 지식 후보만 반환하며, 이 스킬이 그 후보를 프로젝트 단위로 한 번 정리해 반영하는 유일한 쓰기 지점입니다. 쓰기 대상은 항상 허브(`allocator_root`)이며, 프로젝트 worktree의 `.opal/brain/**`·`.opal/MEMORY.json`은 끝까지 무변경으로 남습니다. 실행 시점은 최종 허브 merge 이후로 한정되며, merge 이전 실행은 거부됩니다.

동작 순서는 다음과 같습니다.

1. **실행 전 게이트**: 멱등 가드(이미 batch가 있으면 `skipped`), `project.hub_merged` 이벤트 선행 확인, 지식 관련 이벤트 선행 쓰기 0건 확인, 잔여 미결 태스크 0건 확인, `allocator_root`가 worktree 경로가 아님을 확인합니다. 하나라도 어긋나면 아무것도 쓰지 않고 `blocked`로 반환합니다.
2. **후보 수집**: 각 미니 태스크의 accepted attempt `result.json`에서 지식 후보만 모읍니다.
3. **실패·폐기 후보 제거**: `task_not_accepted`·`superseded_attempt`·`revalidation_invalidated`·`contract_reverted`·`duplicate`·`not_durable` 사유에 해당하는 후보를 버리고 `dropped[]`에 기록합니다.
4. **라우팅과 batch 실행**: 구조 지식은 `brain-tool`(add-page/update-page/log), 유동적 지식·완료 사실은 `memory-tool`(append/promote)로 프로젝트당 단일 pass를 통과시킵니다. 도중 실패하면 즉시 중단하고 `blocked`로 반환합니다.

## 입력

| 이름 | 내용 |
|---|---|
| `run_root` | `<allocator_root>/.opal-runs/<run_id>/` |
| `allocator_root` | 허브 저장소 최상위 절대경로(`run.json`의 값을 그대로 사용, 추론 금지) |
| `task_folder` | MEMORY history 행의 `--path`에 쓸 프로젝트 태스크 캡슐 경로 |
| `project_docs` | PM이 주입한 문서 목록 |

## 출력

- `<run_root>/knowledge-receipt.json` — `batch_count`(항상 1), 적용된 memory·brain 변경, `dropped[]`, 진단(`memory review`·`brain lint`)
- `knowledge.batch_started`·`knowledge.batch_applied` event payload 2건 — OPPB 런타임이 `events.jsonl`에 append(이 스킬은 직접 append하지 않음)

## 호출 시점

허브 merge(id 19) 이후, P5의 `p5.knowledge_batch`(pipeline id 20) 디스패치 시점에 실행됩니다. `op-brain-ingest`(태스크 CLOSE 전용)나 `opal-improve`는 호출하지 않으며, 미니 태스크별 지식 hook을 만들지 않습니다.
