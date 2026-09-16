---
name: op-oppb-project-slice
description: |
  **OPPB P2 프로젝트 슬라이스 단계 스킬**. 승인된 INTENT를 capability 단위 미니 태스크 DAG·계약·완료조건 역인덱스의 구조화 spec으로 변환한다.
  반드시 이 스킬을 사용해야 하는 상황: OPPB Product Flow가 P2 PROJECT DESIGN & SLICE를 Project Planner/Slicer 워커에게 디스패치할 때.
  필수 입력: task_folder, INTENT.md. 선택 입력: PM이 주입한 프로젝트 문서, 기존 PROJECT-DESIGN.md.
  보장 출력: PROJECT-DESIGN.md 초안, .oppb-workgraph-spec.json, .oppb-probe-commands.json.
version: 1.0
---

# op-oppb-project-slice — capability 슬라이스와 실행 계약 초안

## 입력과 책임

- `task_folder`: OPPB 프로젝트 태스크 캡슐(`<task_root>/tasks/{NNN}-oppb-{name}/`)
- `intent`: `<task_folder>/INTENT.md` — 승인된 목표·제외 범위·완료조건·예산
- `project_docs`: PM이 `docs/PROJECT.md` 레지스트리에서 선별해 주입한 문서 목록. 이 목록 밖을 탐색하지 않는다
- `run_root`: 이미 발급됐으면 경로만 받는다. 이 스킬은 run root에 쓰지 않는다

이 스킬은 **초안 작성자**다. 승인은 PM Agent, 기계 검증과 상태 생성은 Controller Tool이 소유한다.

## 실행 계약

- `workgraph.json`·`acceptance.json`·`execution-packet.json`을 직접 만들지 않는다. 유일한 writer는
  `opal/tools/oppb-runtime-tool/controller.py`이며, 이 스킬은 `workgraph load --spec`이 받는 spec 파일만 쓴다.
- `scope_hash`를 계산하거나 적지 않는다. `controller.compute_scope_hash(lease)` 하나가 계산하며 재구현·선점 기입은 거부 사유다.
- `.opal/oppb-environment.json`을 쓰지 않는다. 미추적 쓰기는 **힌트**만 선언하고 봉인은 P2.2 probe가 한다.
- 코드·테스트를 구현하지 않고, 사용자 게이트를 열지 않으며, `state-tool`로 P0~P5 상태를 전이하지 않는다.
- 태스크별 worktree·branch·OPAL 태스크 번호를 제안하지 않는다. 프로젝트 worktree는 하나다.
- 미니 태스크별 `TASK.md`·`PLAN.md`·`DONE.md` 같은 문서 파이프라인을 설계하지 않는다.
- spec의 `budget`·명령·lease는 INTENT가 승인한 범위 안에서만 선언한다.

## 1. 슬라이스 단위 — capability

슬라이스의 기본 단위는 **동일한 비즈니스 개념·변경 이유·정책을 공유하며 사용자가 끝까지 사용할 수 있는
하나의 응집된 capability**다. 하나의 capability는 여러 사용자 동작과 여러 내부 계약을 포함할 수 있다.

**파일 수·레이어 수·API endpoint 수를 1차 분할 기준으로 쓰지 않는다.**

### 수평 레이어 분할 금지

FE/BE/DB, API/화면, 모델/서비스/컨트롤러처럼 **단독으로 사용자 가치를 내지 못하는 레이어 조각을 별도
미니 태스크로 만들지 않는다.** 그런 조각은 같은 capability 안의 `executors` work item이다.

```text
T01 사용자 관리 capability          ← 미니 태스크 1개
  work item: 사용자 CRUD API        ← executors[]
  work item: 관리 화면과 입력 검증   ← executors[]
  work item: 단위·계약·화면 수용 테스트 ← executors[]
```

`api-only`, `ui-only`, `schema-only`처럼 레이어 이름만으로 식별되는 태스크가 spec에 있으면 슬라이스가 틀린 것이다.
예외는 단 하나 — 그 레이어 자체가 독립 수용 가치·독립 rollback 경계를 가질 때이며, 그때는 레이어가 아니라
capability로 이름 붙이고 근거를 `PROJECT-DESIGN.md`에 남긴다.

### 분할한다

- 서로 다른 비즈니스 대상·변경 이유·정책을 가짐
- 한 부분이 없어도 나머지가 독립적으로 사용자 가치를 제공함
- 독립 배포·승인·rollback이 필요함
- 보안·migration처럼 위험과 검증 경계를 분리해야 함
- 일부만 실패했을 때 독립적으로 재실행할 가치가 있음
- capability task 예산 또는 context 한계를 넘을 것으로 예상됨

### 합친다

- 같은 엔티티·용어·권한·validation 정책을 공유함
- API와 그 API만을 소비하는 화면처럼 함께 있어야 사용 가능한 수직 기능임
- 동일 엔티티의 CRUD가 같은 정책·화면 흐름·테스트 fixture를 재사용함
- helper·type·내부 refactor처럼 capability 내부 구현일 뿐 단독 수용 가치가 없음
- 같은 파일과 내부 계약을 반드시 연속 수정함
- 추정한 setup·조정·검증 비용이 실제 구현 예상시간의 20%를 넘음(추정 근거를 PM이 승인해야 한다)
- 분리하면 양쪽 execution packet에 같은 코드 문맥을 대부분 중복 주입해야 함

## 2. 병렬 sibling 선행 조건

별도 미니 태스크로 **병렬 실행**하려면 두 capability의 변경 소유권이 완전히 분리돼야 한다.
공통 프로젝트 문서·기존 코드·동결된 interface를 함께 **읽는** 것은 허용한다. 동시에 바꾸거나 배타적으로
점유하는 집합에 교집합이 없어야 한다.

| 소유권 축 | 병렬 허용 조건 | spec 표현 |
|---|---|---|
| 추적 코드·테스트 | `tracked_writes(A) ∩ tracked_writes(B) = ∅` | `lease.tracked_writes` |
| Git 미추적 산출물 | `ephemeral_write_hints`가 서로 다르거나 공유 불변·배타 정책이 있음 | probe 입력 → 봉인 후 `lease.ephemeral_writes` |
| 계약 | 같은 contract revision을 동시에 바꾸지 않음. 공유 계약은 실행 전 동결 | `lease.contracts` |
| 비즈니스 규칙 | 같은 정책 결정이나 완료조건 ID를 공동 소유하지 않음 | `acceptance[].contributing_tasks` 교집합 |
| 실행 자원 | DB schema·port·service·fixture·queue가 분리되거나 namespace 격리됨 | `lease.runtime_resources` |
| 전역 산출물 | lockfile·migration order·generated index·global config 동시 변경 없음 | 파일이면 `tracked_writes`, 생성기·순서 자원이면 `runtime_resources` |
| 복구 | A를 preimage로 되돌려도 B의 파일·계약·증거가 바뀌지 않음 | 위 네 축의 합집합으로 유도 — 별도 필드 없음 |

Controller가 기계적으로 lease를 발급하는 집합은 `controller.LEASE_AXES` 네 축
(`tracked_writes`·`ephemeral_writes`·`contracts`·`runtime_resources`)뿐이다. 나머지 세 축은 반드시 이 네 축
또는 완료조건 ID 교집합으로 **다시 표현**한다. 표현할 수 없으면 병렬로 선언하지 않는다.

병렬로 선언하려면 다음을 모두 만족해야 한다.

1. DAG 선후 의존 없음(`depends_on` 무관)
2. `tracked_writes`와 mutable ephemeral 힌트의 중복·포함 관계 없음
3. 변경 중인 외부 producer-consumer 계약 공유 없음
4. `runtime_resources` 중복 없음
5. 전역 formatter·schema migration·lockfile·generated index 작업 없음

하나라도 증명할 수 없으면 **병렬 sibling으로 분할하지 않는다.** 같은 capability로 합치거나, capability
내부의 순차 work item으로 둔다. 크기 때문에 반드시 나눠야 하면 별도 태스크로 남기되 `depends_on`으로
순차 순서를 고정하고 그 근거를 `PROJECT-DESIGN.md`의 병렬 판정표에 `parallel_eligible: false`로 적는다.

`ephemeral_write_hints`는 probe 입력일 뿐 최종 lease 계약이 아니다. 모든 전이 의존 도구의 미추적 쓰기
경로를 미리 안다고 가정하지 않는다. 의미상 동일한 정책인지 기계적으로 판정할 수 없으면 병렬로 선언하지
말고 PM 판정 항목으로 올린다.

## 3. 구조화 출력 계약

### 3.1 `<task_folder>/.oppb-workgraph-spec.json`

`oppb-runtime-tool workgraph load --run-root <run_root> --spec <이 파일>`이 소비한다.
Controller가 읽는 필드는 아래가 전부이며, 동결된 `schema/oppb-state.schema.json`이 닫힌 집합을 강제하므로
여기에 없는 키를 추가하지 않는다. 추가 근거는 `PROJECT-DESIGN.md`가 소유한다.

```json
{
  "budget": {
    "max_runner_dispatches": 0,
    "max_executor_dispatches": 0,
    "max_verifier_dispatches": 0,
    "max_total_dispatches": 0,
    "max_active_runners": 0,
    "max_active_executors": 0,
    "max_total_agent_processes": 0,
    "max_attempts_per_task": 0
  },
  "mini_tasks": [
    {
      "id": "T01",
      "capability": "사용자 관리",
      "depends_on": [],
      "lease": {
        "tracked_writes": [],
        "ephemeral_writes": [],
        "contracts": [],
        "runtime_resources": []
      },
      "run_command": null,
      "verify_command": ["..."],
      "executors": [{ "id": "be", "run_command": null }]
    }
  ],
  "acceptance": [
    {
      "id": "AC-USER-CRUD",
      "description": "...",
      "contributing_tasks": ["T01"]
    }
  ]
}
```

| 필드 | 의미 | 규칙 |
|---|---|---|
| `budget` | 프로젝트 예산·동시성 상한 | 0 이상 정수. `max_<role>_dispatches`·`max_total_dispatches`는 Controller가, 나머지는 Supervisor가 읽는다 |
| `mini_tasks[].id` | capability ID이자 DAG 노드 ID | 중복 금지. 레이어 이름 금지 |
| `mini_tasks[].capability` | 사람이 읽는 capability 이름 | 비어 있지 않은 문자열. 비즈니스 대상 용어를 쓴다 |
| `mini_tasks[].depends_on` | DAG 선행 태스크 | 같은 spec의 id만. 자기 참조·순환은 load 거부 |
| `mini_tasks[].lease` | 네 축 소유권 선언 | 축별 문자열 배열. `scope_hash`는 Controller가 이 선언에서 계산한다 |
| `mini_tasks[].run_command` | RUN 명령 | argv 배열 또는 `null`. `null`이면 Supervisor가 `opal-agent` attempt로 기동한다 |
| `mini_tasks[].verify_command` | capability 전체를 끝까지 판정하는 독립 검증 명령 | argv 배열. 미니 태스크마다 독립 검증 수단이 반드시 있어야 한다 |
| `mini_tasks[].executors` | capability 내부 work item | `{id, run_command}`. 레이어 조각은 여기에 둔다. 하위 PL·오케스트레이터를 선언하지 않는다 |
| `acceptance[].id` | 완료조건(= acceptance cluster) ID | 중복 금지 |
| `acceptance[].contributing_tasks` | 그 조건에 기여하는 미니 태스크 | `mini_tasks[].id` 밖을 가리키면 load 거부 |

`acceptance`가 완료조건 ↔ 기여 태스크 ↔ 증거 **역인덱스**의 원천이다. Controller가 이 선언에서
`acceptance.json`의 `criteria`와 `evidence_index`(evidence_id → `{task_id, criteria}`)를 만든다.
`acceptance`를 비워 두면 미니 태스크 1개당 조건 1개로 자동 유도되므로, **의도한 묶음이 있으면 반드시 명시한다.**
하나의 capability를 여러 시나리오가 증명해도 되고, 하나의 조건에 여러 태스크가 기여해도 된다.

`pre_state`·`runner_attempt_id`는 재개 fixture 전용이다. 신규 슬라이스에서는 쓰지 않는다.

### 3.2 `<task_folder>/.oppb-probe-commands.json`

`oppb-runtime-tool probe seal --commands <이 파일>`이 소비한다. 미추적 쓰기 힌트는 이 파일의 명령으로
관측되며, 정책(`shared_immutable`·`attempt_namespaced`·`exclusive`) 배정과 봉인은 probe가 한다.

```json
{
  "commands": [
    { "id": "bootstrap", "kind": "bootstrap", "argv": ["..."], "runtime_resources": [] },
    { "id": "build", "kind": "build", "argv": ["..."], "runtime_resources": [] },
    { "id": "verify-T01", "kind": "test", "argv": ["..."], "runtime_resources": ["port:3000"] }
  ],
  "config": [],
  "lockfile": [],
  "toolchain": {}
}
```

`mini_tasks[].verify_command`와 `mini_tasks[].run_command`에 쓴 argv는 여기에도 같은 내용으로 등재한다.
등재되지 않은 명령의 미추적 출력은 봉인되지 않아 late discovery 또는 `scope_violation` 경로로 들어간다.

### 3.3 `<task_folder>/PROJECT-DESIGN.md` 초안

기계 SSOT가 담지 못하는 설계 설명만 소유한다. spec 필드를 다시 옮겨 적지 않는다.

```markdown
# PROJECT-DESIGN (초안)

## 슬라이스 근거
| capability ID | 비즈니스 대상·변경 이유·정책 | 수직 완결성 근거 | 합치기/나누기 판정 |

## 병렬 판정
| A | B | 7축 교집합 검사 결과 | parallel_eligible | 근거 |

## 계약 경계
| 계약 ID | producer | consumer | 동결 여부 |

## 통합 전략과 위험
## PM 판정 요청 항목
```

`parallel_eligible: false`인 쌍과, 기계적으로 판정할 수 없어 PM 경계 판정이 필요한 항목은 반드시 적는다.

## 4. 자기검사와 반환

spec을 쓴 뒤 다음을 직접 확인한다. 어긋나면 고쳐 쓰고 반환하지 않는다.

- 모든 미니 태스크가 capability 이름을 갖고 레이어 이름이 없다
- 모든 미니 태스크에 `verify_command`가 있다
- `depends_on`이 존재하는 id만 가리키고 순환이 없다
- 병렬 가능하다고 본 모든 쌍에서 네 lease 축의 교집합이 0이다
- 모든 `acceptance[].contributing_tasks`가 존재하는 id만 가리킨다
- `scope_hash`·`revision`·`state` 같은 Controller 소유 필드를 쓰지 않았다

반환:

```text
SLICE 완료: {task_folder}/.oppb-workgraph-spec.json
미니 태스크: {id 목록}
병렬 후보: {쌍 목록}
순차 강제: {쌍 목록과 사유}
PM 판정 요청: {없음 | 항목}
```

## 변경이력

| 버전 | 일시 | 변경내용 |
|---|---|---|
| v1.0 | 2026-09-15 | OPPB P2 capability 슬라이스 단계 스킬 신설 — 슬라이싱 기준·수평 레이어 분할 금지·병렬 sibling 7축 선행 조건·Controller spec 구조화 출력 계약 (task 132/W-22) |
