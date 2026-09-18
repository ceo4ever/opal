---
name: op-oppb-knowledge-finalize
description: |
  **OPPB P5 Project Knowledge Finalizer 단계 스킬**. 프로젝트 전체에서 모인 지식 후보에서 실패·폐기분을 제거하고, 기존 `memory-tool`·`brain-tool`을 프로젝트 batch로 **정확히 한 번** 호출해 허브 MEMORY·brain에 반영한다.
  반드시 이 스킬을 사용해야 하는 상황: OPPB Product Flow가 P5 `p5.knowledge_batch`(pipeline id 20)를 디스패치할 때. 이 스킬은 프로젝트당 1회만 실행된다.
  필수 입력: run_root, allocator_root, task_folder. 보장 출력: `<run_root>/knowledge-receipt.json`과 지식 event 2건의 payload.
version: "1.0"
domain: knowledge
dispatched_by: "OPPB Product Flow (opal-pilot-project-build) — P5 `p5.knowledge_batch`"
---

# op-oppb-knowledge-finalize — 프로젝트 지식 batch 1회

## 역할

OPPB에서 MEMORY와 brain은 **P5 이 단계 전까지 읽기 전용**이다(제안서 §5 P5). 미니 태스크는 지식을
쓰지 않고 `result.json`에 **후보만** 반환하며(제안서 §4.3 출력 `knowledge`), 미니 태스크별 MEMORY·brain
기록은 생성하지 않는다(제안서 §7.3). 이 스킬은 그 후보를 프로젝트 단위로 한 번 정리해 반영하는
유일한 쓰기 지점이다.

- 쓰기 대상은 **허브(allocator root)** 다. 프로젝트 worktree의 `.opal/brain/**`·`.opal/MEMORY.json`은
  끝까지 무변경으로 남는다 — P5 pre-finalize guard(pipeline id 18)가 worktree의 MEMORY/brain diff 0을
  요구하고, `worktree-tool finalize`(id 22)가 관측 집합 S ⊆ 선언 집합 D를 검사하기 때문이다.
- 실행 시점은 **최종 허브 merge 이후**다(id 19 → id 20). merge 전 실행은 거부한다.

## 입력

| 이름 | 내용 |
|---|---|
| `run_root` | `<allocator_root>/.opal-runs/<run_id>/` — `run.json`·`workgraph.json`·`attempts/`·`events.jsonl` 보유 |
| `allocator_root` | 허브 저장소 최상위 **절대경로**. `run.json`의 `allocator_root` 값을 그대로 쓴다. cwd·경로 세그먼트로 추론하지 않는다 |
| `task_folder` | 프로젝트 태스크 캡슐 경로 — MEMORY history 행의 `--path`에 쓴다 |
| `project_docs` | PM이 주입한 문서 목록. 이 목록 밖을 탐색하지 않는다 |

`allocator_root`를 인자로 받지 못하면 즉시 `blocked`다. 추론해서 쓰지 않는다 —
`brain-tool`은 worktree 안의 cwd 파생 쓰기를 `allocator_root_required`(reason `cwd_inference_in_worktree`)로
거부하고, `memory-tool`은 `.opal-worktrees` 하위 `--file`을 `WORKTREE_WRITE_REJECTED`(update/promote/
prune/delete/task-number) 또는 deferred index 요청(append --kind memory)으로 우회시킨다.

## STEP 0 — 실행 전 게이트

아래를 순서대로 판정한다. 하나라도 어긋나면 **아무것도 쓰지 않고** `blocked`로 반환한다.

1. **멱등 가드**: `<run_root>/knowledge-receipt.json`이 이미 있고 `batch_count >= 1`이면 즉시 종료한다.
   `status: skipped`, 사유 `already_applied`. 두 번째 batch는 어떤 경우에도 만들지 않는다.
2. **merge 선행**: `<run_root>/events.jsonl`에 `type == "project.hub_merged"` 이벤트가 최소 1건 있어야 한다.
   없으면 `blocked`(`hub_merge_not_observed`).
3. **선행 쓰기 0**: `events.jsonl`에 `type`이 `knowledge.`으로 시작하는 이벤트가 이미 있으면 `blocked`
   (`knowledge_write_before_p5`). 정상 run에서는 이 단계 전까지 0건이어야 한다.
4. **잔여 작업 0**: `workgraph.json`에 `running`·`verifying`·`needs_revalidation` 상태의 미니 태스크가
   남아 있으면 `blocked`(`tasks_not_settled`).
5. **허브 경로 확인**: `allocator_root`가 절대경로이며 `.opal-worktrees` 세그먼트를 포함하지 않는다.
   포함하면 `blocked`(`allocator_root_is_worktree`).

## STEP 1 — 후보 수집

`<run_root>/workgraph.json`의 미니 태스크 목록을 읽고, 각 태스크의 **accepted attempt**의
`attempts/<task_id>/<attempt_id>/result.json`에서 `knowledge` 후보만 모은다.

- 태스크당 accepted attempt는 하나다. 그 외 attempt는 읽지 않는다.
- `result.json`이 없거나 `knowledge`가 비어 있으면 그 태스크는 후보 0건이다(오류 아님).
- 후보 본문을 재해석해 새 지식을 창작하지 않는다. 후보에 없는 내용을 지어내지 않는다.

## STEP 2 — 실패·폐기 후보 제거

아래에 해당하는 후보를 **전부 버린다**. 버린 항목은 receipt의 `dropped[]`에 사유와 함께 남긴다.

| 제거 사유 코드 | 대상 |
|---|---|
| `task_not_accepted` | 태스크 최종 상태가 `failed`·`blocked`인 미니 태스크의 후보 |
| `superseded_attempt` | Repair로 대체된 이전 attempt의 후보(accepted attempt 밖) |
| `revalidation_invalidated` | `needs_revalidation` 재검증에서 근거가 뒤집힌 후보 |
| `contract_reverted` | 최종 허브 merge 결과에 남지 않은 계약·파일에 대한 후보 |
| `duplicate` | 같은 대상을 가리키는 중복 후보(선행 1건만 남긴다) |
| `not_durable` | 이번 실행 한정 우회·임시 조치처럼 프로젝트 밖에서 재사용 가치가 없는 후보 |

남은 후보만 STEP 3의 라우팅 대상이다. 남은 후보가 0건이어도 batch는 **실행된 것**이며, 도구 호출 0건과
`batch_count: 1`로 receipt를 쓴다(아무 일도 안 했다는 사실 자체가 1회 판정의 결과다).

## STEP 3 — 라우팅

| 후보 성격 | 거처 | 도구 |
|---|---|---|
| 프로젝트가 만든 구조·개념·흐름·엔티티 지식 | `.opal/brain/` 페이지 | `brain-tool` |
| 운영 피드백·판단 근거·재발 방지처럼 아직 굳지 않은 지식 | MEMORY 인덱스 행 | `memory-tool` |
| 프로젝트 완료 사실 1건 | MEMORY history 행 | `memory-tool` |

brain 페이지로 갈 후보 중 MEMORY에도 같은 내용을 남기지 않는다. brain에 실체가 생긴 지식은 brain이 SSOT다.

## STEP 4 — batch 1회 실행

> **[MUST] 도구 계약 실측 고지**: `memory-tool`·`brain-tool` 어디에도 `batch` 서브명령이나 일괄 입력
> 옵션은 **없다**. 여기서 "프로젝트 batch"는 **아래 순서를 프로젝트당 정확히 한 번 통과하는 단일 pass**를
> 뜻하며, `batch_count`는 개별 명령 수가 아니라 이 pass의 실행 횟수다. 존재하지 않는 옵션을 만들지 않는다.
> 두 도구는 이 스킬이 수정하지 않는다 — 있는 그대로 호출한다.

pass 도중 어느 명령이든 `ok:false`를 반환하면 **즉시 중단**하고, 그 지점까지의 적용분을 receipt의
`partial[]`에 적은 뒤 `blocked`로 반환한다. 실패를 덮어 재시도 pass를 돌리지 않는다(재시도는 PM 결정).

### 4.1 brain — 조회

```bash
~/.opal/tools/brain-tool/run.sh ingest-scan --source all --brain-path <allocator_root>
~/.opal/tools/brain-tool/run.sh search "<후보 제목>" --limit 5 --brain-path <allocator_root>
```

`ingest-scan`의 `items[].skip == true`는 이미 반영된 대상이다 — 재수집하지 않는다.
`search` 결과에 동일 대상 페이지가 있으면 `add-page`가 아니라 `update-page` 경로다.
`--brain-path`는 **명시값**으로 준다. 기본값(cwd 파생)은 worktree 실행에서 해석이 달라진다.

### 4.2 brain — 페이지 쓰기

페이지 본문은 먼저 파일로 쓰고 `--body-file`로 넘긴다(미실체 게이트가 실제 본문을 스캔한다).

```bash
# 신규
~/.opal/tools/brain-tool/run.sh add-page <slug> \
  --type <entity|concept|flow|synthesis> \
  --title "<제목>" \
  [--tags a,b] [--sources <근거 경로 CSV>] [--related <슬러그 CSV>] \
  --body-file <본문 파일 경로> \
  --allocator-root <allocator_root>

# 기존 갱신
~/.opal/tools/brain-tool/run.sh update-page <slug> \
  [--title ..] [--tags ..] [--sources ..] [--related ..] [--status ..] \
  [--body-file <본문 파일 경로>] \
  --allocator-root <allocator_root>
```

- `--type`은 그 프로젝트 brain의 `SCHEMA.md` §1.5가 채택한 타입만 쓴다. 미채택 타입은 `invalid_page_type`이다.
- `--allocator-root`는 **절대경로 허브 루트**다. 회고적 학습 쓰기의 유일한 허용 경로이며,
  미지정·상대경로는 `allocator_root_required`로 거부된다.
- 미실체 마커(`미착수`·`향후계획` 등)가 본문에 있으면 `speculative_content`로 거부된다. 이때
  `--force --note`로 우회하지 않는다 — 실체 없는 후보는 STEP 2에서 `not_durable`로 버렸어야 한다.
- `index.md`는 `add-page`/`update-page`가 자동 재생성한다. `index` 서브명령을 따로 부르지 않고,
  `index.md`·`log.md`를 직접 편집하지 않는다.

### 4.3 brain — log 1건

페이지 쓰기가 전부 끝난 뒤 **정확히 1회** 호출한다. 페이지마다 부르지 않는다.

```bash
~/.opal/tools/brain-tool/run.sh log \
  --op ingest \
  --summary "OPPB <run_id> 프로젝트 지식 batch" \
  [--new <신규 슬러그 CSV>] [--updated <갱신 슬러그 CSV>] [--sources <근거 CSV>] \
  --brain-path <allocator_root>
```

`--op`는 `ingest|init|lint|query` 중에서만 고른다. 프로젝트 지식 반영은 `ingest`다.

### 4.4 MEMORY — 인덱스 행

행을 넣기 전에 본문 `.md`를 먼저 쓴다. `memory-tool`은 제목에서 `memory/<slug>.md`를 파생하고,
그 경로는 `MEMORY.json`의 부모 디렉토리 기준으로 해석된다 — 본문은
`<allocator_root>/.opal/memory/<slug>.md`에 둔다. 본문이 없으면 `review`가
`memory_file_missing` 위반으로 잡는다.

```bash
~/.opal/tools/memory-tool/run.sh append \
  --file <allocator_root>/.opal/MEMORY.json \
  --kind memory \
  --title "<제목>" \
  --type <project|architecture|feedback|preferences|issues|task|improvement> \
  --summary "<80자 이하 요약>" \
  [--status active|candidate]
```

- `--file`은 반드시 **허브 경로**다. worktree 경로를 주면 MEMORY.json을 쓰지 않고
  `memory-index-request.json`에 지연 요청만 남기며, 그것은 이 단계의 계약이 아니다.
- `--summary`는 80자를 넘기면 `summary_too_long`이다. 상세는 본문 `.md`가 갖는다.

### 4.5 MEMORY — history 1행

프로젝트당 **1행**만 넣는다(FIFO=5는 도구가 집행한다).

```bash
~/.opal/tools/memory-tool/run.sh append \
  --file <allocator_root>/.opal/MEMORY.json \
  --kind history \
  --title "<프로젝트명>" \
  --summary "<핵심결과>" \
  --stage "완료" \
  --path "<task_folder>"
```

### 4.6 MEMORY — brain 졸업(조건부)

STEP 3에서 brain 페이지가 생겼고 같은 대상의 기존 MEMORY 행이 남아 있을 때만 호출한다.
`memory-tool`은 brain에 직접 쓰지 않으므로 **4.2가 먼저 성공한 뒤**에만 부른다.

```bash
~/.opal/tools/memory-tool/run.sh promote \
  --file <allocator_root>/.opal/MEMORY.json \
  --title "<기존 행 제목>" \
  --to brain \
  --ref "<4.2에서 만든 brain 페이지 슬러그>"
```

### 4.7 마감 점검 (read-only)

```bash
~/.opal/tools/memory-tool/run.sh review --file <allocator_root>/.opal/MEMORY.json
~/.opal/tools/brain-tool/run.sh lint --brain-path <allocator_root>
```

`violations`·`issues`는 receipt에 싣고 보고한다. 이 단계에서 자동 수정하지 않는다.

## STEP 5 — receipt와 event

### 5.1 `<run_root>/knowledge-receipt.json`

pass가 끝난 직후 **한 번** 원자적으로 쓴다. `batch_count`는 이 pass의 실행 횟수이며 항상 `1`이다.

```json
{
  "run_id": "<run_id>",
  "stage": "P5",
  "batch_count": 1,
  "applied_after_event": "project.hub_merged",
  "allocator_root": "<절대경로>",
  "memory": { "appended": ["<제목>"], "history": ["<제목>"], "promoted": ["<제목>"] },
  "brain": { "added": ["<슬러그>"], "updated": ["<슬러그>"], "logged": true },
  "dropped": [{ "candidate": "<식별자>", "task_id": "<id>", "reason": "task_not_accepted" }],
  "diagnostics": { "memory_review_violations": [], "brain_lint_issues": [] }
}
```

`batch_count`를 2 이상으로 올리는 경로는 없다. 재실행 요청은 STEP 0.1에서 `skipped`로 끝난다.

### 5.2 event payload 2건

`events.jsonl`의 writer는 OPPB 런타임 하나다. 이 스킬은 **직접 append하지 않고** 아래 두 레코드를
반환하며, Product Flow가 순서대로 append한다. 둘 다 `stage`가 `"P5"`이고, 마지막
`project.hub_merged`보다 **뒤**에 놓여야 한다.

```json
{"type": "knowledge.batch_started", "stage": "P5", "run_id": "<run_id>", "candidates": 0}
{"type": "knowledge.batch_applied", "stage": "P5", "run_id": "<run_id>", "batch_count": 1,
 "receipt": "knowledge-receipt.json"}
```

`knowledge.batch_applied`는 run 전체에서 **1건**이다. 부분 실패로 `blocked`가 되면
`knowledge.batch_applied`를 발행하지 않는다.

## 하지 않는 것

- **`op-brain-ingest`를 호출하지 않는다.** 그 스킬은 태스크 CLOSE에서 태스크 폴더의
  `DONE.md`/`PLAN.md`/`TASK.md`를 읽어 태스크 단위로 ingest하는 워커다. OPPB 미니 태스크는 그 문서들을
  아예 만들지 않고(제안서 §7.3) 지식 후보를 `result.json`으로만 돌려주므로 입력 자체가 없다. 미니 태스크마다
  붙이면 "프로젝트 완료 전 MEMORY·brain 반영 0"이 깨진다. 본문 판별 기준이 필요하면 그 스킬의
  포함/제외 기준을 **참조만** 하고 호출하지 않는다.
- **`opal-improve`를 호출하지 않는다.** 그 스킬은 PM의 개선 신호를 `improve-tool`로 기록하는
  온디맨드 루프(`//opim`)이고, 기록 대상이 프로젝트 지식이 아니라 프레임워크·로컬 PM 개선이다.
  거처와 도구가 다르므로 이 단계에 hook으로 끼우지 않는다.
- 미니 태스크별 지식 hook·CLOSE 에이전트를 만들지 않는다. `accepted`가 미니 태스크의 종료다.
- `memory-tool`·`brain-tool`·`op-brain-ingest`·`opal-improve`를 수정하지 않는다.
- worktree의 `.opal/brain/**`·`.opal/MEMORY.json`을 건드리지 않는다.
- `index.md`·`log.md`·`MEMORY.json`을 직접 편집하지 않는다(도구 집행 경계).
- `state-tool`로 P0~P5를 전이하지 않고, Git commit·merge를 하지 않는다.

## 자기검사와 반환

반환 전에 직접 확인한다. 어긋나면 고치고, 고칠 수 없으면 `blocked`다.

- `knowledge-receipt.json`의 `batch_count`가 정확히 `1`이다
- `knowledge.batch_applied` payload를 1건만 반환했다
- 두 event payload의 `stage`가 모두 `"P5"`다
- 쓰기 명령의 대상 경로가 전부 `allocator_root` 하위이고 `.opal-worktrees`를 포함하지 않는다
- 버린 후보가 전부 `dropped[]`에 사유와 함께 남았다
- `--force --note`로 미실체 게이트를 우회한 페이지가 0건이다

반환:

```text
KNOWLEDGE BATCH 완료: {run_root}/knowledge-receipt.json
batch_count: 1
brain: 신규 {n} / 갱신 {m} / log 1
MEMORY: 인덱스 {k} / history 1 / promote {p}
제거한 후보: {개수} ({사유별 내역})
진단: {memory review violations} / {brain lint issues}
```

## 변경이력

| 버전 | 일시 | 변경내용 |
|---|---|---|
| v1.0 | 2026-09-15 | OPPB P5 Project Knowledge Finalizer 단계 스킬 신설 — merge 후 1회 게이트·실패/폐기 후보 제거·기존 memory-tool·brain-tool 실측 CLI 단일 pass·knowledge receipt와 event 계약 (task 132/W-27) |
