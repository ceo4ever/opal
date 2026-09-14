# OPPD v2 빠른 프로젝트 완수 구조 제안서

> 상태: 검토
> 작성: 알투(PM)
> 작성일: 2026-09-13
> 목적: 기존 OPAL 런타임 자산을 재사용해 아이디어부터 프로젝트 완료까지 무인 실행 구간을 빠르고 안전하게 완주하는 OPPD v2를 구현한다.

---

## 1. 결론

`//oppd`는 전면 교체하되 사용자 기능은 축소하지 않는다. 사용자는 아이디어만 제시할 수 있고,
OPPD는 필요한 경우 기획을 거쳐 프로젝트 계약을 만든 뒤 새 실행 엔진으로 완주한다.

실현 가능한 v2 MVP는 다음 조합이다.

| 영역 | v2 MVP |
|---|---|
| 제어 | 순수 `controller tick` 도구 + tick을 자동 호출하는 최소 Runtime Supervisor |
| 격리 | 프로젝트 전용 worktree 1개 + 미니 태스크별 write/contract/resource lease |
| 통합 | 미니 태스크 merge 폐기, Controller 단일 Git writer가 범위별 checkpoint commit |
| 공유 지식 | 모든 미니 태스크는 MEMORY·brain 읽기 전용, 프로젝트 완료 후 허브에서 1회 반영 |
| Runner | 기존 `opal-task-action-agent`를 Fast·Standard·Critical 프로필로 축소·재구성 |
| 계약 테스트 | SLICE에서 경로·선언 예약, producer 태스크가 실행 가능한 테스트 구현 |
| 검증 | 기존 `op-dev-*`, `op-gc-*`, checker, evaluator 재사용 |
| 동시성 | 하드 상한 2로 시작, 실측 후 설정으로 확대 |
| 교체 게이트 | 품질 비회귀·무인 구간 완주·신규 차단 결함 0만 차단 조건 |
| 관찰 지표 | 경과 시간·관측 가능한 워커 토큰·비용·재작업 범위 |

OPPL을 OPPD 안에 중첩하지 않는다. 유효한 예산·무진전·수렴 판정만 Controller에 이관하고,
OPPD v2 전환 뒤 `//oppl` 진입점은 폐기한다.

## 2. 현행 자산 대조와 정정

### 2.1 즉시 재사용 가능한 자산

- `worktree-tool`은 프로젝트 전용 worktree의 create·list·status·remove·finalize와 실제 Git 저장소
  기반 회귀 테스트를 제공하므로 프로젝트 격리·귀속·회수에 재사용할 수 있다.
- `opal-task-action-agent`는 PLAN부터 TEST까지 무인 실행하는 현재 Runner 후보다.
- `op-dev-plan`, `op-dev-execute`, `op-dev-test-scenario`는 태스크 내부 단계를 제공한다.
- `op-gc-convention`, `op-gc-security`와 두 checker는 변경 범위별 컨벤션·보안 검사에 재사용할 수
  있다.
- `opal-evaluator-agent`는 Critical 태스크의 독립 read-only 검토에 재사용할 수 있다.
- `backlog-tool`은 배타 락을 사용해 read-modify-write를 직렬화한다
  (`opal/tools/backlog-tool/backlog_tool.py:167-198`).

### 2.2 신규 구현이 필요한 자산

- 프로젝트 상태 reducer와 Ready·Checkpoint·Repair·Revalidation 큐
- process-group 수명주기와 tick 자동 호출을 소유하는 Runtime Supervisor
- `workgraph.json`·`acceptance.json`의 잠금·원자적 저장 도구
- immutable verifier record를 검증·저장하는 Evidence Tool과 schema
- 미니 태스크의 write/contract/resource lease를 교차 검사하고 발급·회수하는 Scope Lease Tool
- Controller만 호출할 수 있는 범위별 checkpoint commit·복구 도구
- 완료 프로젝트의 다중 캡슐을 받는 Project Knowledge Finalizer: 기존 memory·brain 판단 기준과 도구 재사용, batch·중복·receipt 계약 신규 구현
- 프로젝트 worktree의 request 보존 증명과 finalize 멱등 분기 확장
- OPPD 엔진 라우터와 v2 실행 본체
- 허브 MEMORY 요청 일괄 적용기: 캡슐 검증·`append --body-sha256` 호출·반영 확인·영속 receipt
- brain 페이지·index·이력 이벤트의 프로젝트 단위 적용과 ID 기반 멱등 후처리
- brain-tool 허브 writer 락(신규): v1·v2의 add-page·update-page·log·index에 공통 적용

위 추가 기능은 현행 명령의 존재를 뜻하지 않는다. 특히 memory 요청 적용기는 기존 append와
state-tool의 subprocess 호출 패턴을 재사용하지만 batch·검증·receipt 처리는 신규 구현이다.

### 2.3 프로젝트 worktree와 finalize 경계

`worktree-tool finalize`는 브랜치를 머지하지 않는다. 실제 구현은 귀속 대상만 커밋하고 metadata를
`completed_unmerged → attribution_pending → closed`로 전이한다
(`opal/tools/worktree-tool/worktree_tool.py:1691-1840`). 현재 하네스는 finalize를 merge 전에 실행하고,
그 뒤 `git merge --ff-only` 또는 `git merge --no-ff`를 허용한다
(`opal/core/references/harness/worktree.md:48-50`, `opal/skills/opal-pilot-dev/SKILL.md:319-334`).

이 현재 경로는 v1의 사실 설명이다. v2는 OPPD 프로젝트 자체의 기존 worktree 하나만 사용하고, 미니
태스크용 하위 worktree나 branch를 만들지 않는다. 다음 순서를 집행한다.

1. 프로젝트 worktree에서 서로 겹치지 않는 미니 태스크에 scope lease 발급
2. Runner는 Git 명령 없이 허용 범위만 수정하고 결과·실제 변경 hash·지식 후보를 원자 기록
3. Controller가 범위 이탈과 증거를 확인하고 해당 범위만 checkpoint commit
4. 계약 경계에서 증분 검증하고 실패하면 같은 project worktree의 독점 Repair lane으로 복귀
5. 모든 완료조건 통과 후 프로젝트 worktree를 현행 사용자 승인 경로로 허브에 merge
6. 허브에서 Project Knowledge Finalizer가 memory·brain 후보를 한 번에 정리·반영하고 history 귀속 처리

기존 v1 finalize mode는 바꾸지 않는다. brain-tool의 허브 writer 락 추가는 v1의 명령 의미·출력 계약을
유지하는 쓰기 직렬화이며 v1 경로에도 적용한다. 구현 docstring과 하네스의 finalize 시점 표현도
함께 정합화해야 한다.

### 2.4 동시 쓰기 위험

현재 `state-tool`은 단순 파일 read/write이며 배타 락과 원자적 교체가 없다
(`opal/tools/state-tool/state_tool.py:358-371`). 병렬 Runner가 공유 상태를 직접 갱신하는 구조는
허용하지 않는다.

v2에서는 Runner가 자신의 `result.json`과 미니 태스크 캡슐 request만 임시 파일에서 원자적으로
rename하고, Runtime Supervisor가 attempt 사건만 기록한다. `workgraph.json`과 `acceptance.json`은
Controller 도구만 배타 락 아래 갱신하는 단일 writer 구조로 고정한다.

### 2.5 병렬 공유 OPAL 메타 경계

현재 자산은 병렬 안전 계약이 완전히 일치하지 않는다.

- `memory-tool`은 worktree의 `MEMORY.json`을 읽기 snapshot으로 취급하고 `task-number`,
  `memories`, `history` 직접 갱신을 거부한다. memory 학습은 이미 `memory-index-request.json`으로
  지연된다.
- 태스크 번호는 허브의 `memory-tool task-number --bump`가 file lock과 atomic rename으로
  중복을 방지한다. 채번 primitive를 새로 만들 필요는 없다.
- 반면 현재 CLOSE는 merge 전 `op-brain-ingest`와 `worktree-tool finalize`를 호출하며,
  `finalize`는 관측된 `.opal/brain/**`·`.opal/MEMORY.json`을 태스크 branch에 귀속 commit할 수 있다.
  병렬 branch가 같은 index·log·page를 바꾸면 정상 코드 변경과 무관한 merge conflict가 생긴다.

v2는 다음 계약으로 이 모순을 제거한다.

1. 프로젝트 worktree에서 모든 미니 태스크는 `.opal/MEMORY.json`과 `.opal/brain/**`를 읽기 전용으로
   사용한다. project-start hash를 execution packet에 기록하고 쓰기 시도를 차단한다.
2. 미니 태스크는 지식을 반영하지 않는다. memory 후보는 `memory-index-request.json`, brain 후보는
   `result.json`의 구조화 필드로 task capsule에 남기고 Controller가 `DONE.md`에 렌더링한다. 후보
   생성은 완료 반영이 아니다.
3. checkpoint와 프로젝트 finalize는 공유 지식 파일이 dirty이면 `SHARED_META_WRITE_REJECTED`를
   반환한다. 미니 태스크 후보를 applied·resolved로 표시하지 않는다.
4. Controller checkpoint는 코드·테스트·task capsule만 범위별 commit한다. 최종 반영 전 프로젝트
   base 대비 MEMORY·brain diff가 모두 0인지 검사한다.
5. OPAL task 번호는 프로젝트 worktree 하나에만 발급한다. 미니 태스크는 `T01` 같은 run-local ID를
   사용하며 `memory-tool task-number --bump`를 호출하지 않는다.
6. 프로젝트 완료조건 통과와 최종 허브 merge 확인 뒤 Project Knowledge Finalizer가 모든 accepted
   태스크의 후보를 위상 순서로 읽고 중복을 제거해 허브에 한 번 반영한다.
7. MEMORY index·history와 brain page·index·log는 각각 기존 도구의 허브 쓰기 계약을 사용한다.
   batch·request ID·content hash·receipt로 중단 후 재개와 중복 방지를 보장한다.

미니 태스크 상태는 `running → provisional → checkpointed → accepted`로 고정한다. 프로젝트 registry는
`active → project_done → awaiting_merge → project_attribution_pending → closed`로 관리한다. `closed`는
최종 허브 merge와 프로젝트 단위 MEMORY·brain 반영까지 끝난 경우에만 허용한다. 보존된 request는 적용
전까지 pending이며 지식 반영에 필요한 참조와 증거는 `closed`까지 유지한다.

허브의 채번 및 사용자 변경은 자동 commit·stash·덮어쓰기를 하지 않는다. Knowledge Finalizer는 허브
최신 MEMORY·brain을 다시 읽고 공용 writer lock 아래 반영한다. 별도의 사용자 변경과 의미 충돌하면
자동 해결하지 않고 구조화된 `project_knowledge_conflict`를 반환한다.

## 3. 사용자 기능과 진입점

현재 OPPD는 PRD·TRD를 `opwt`에 위임하고 WBS를 만든 뒤 액션을 실행한다
(`opal/skills/opal-pilot-project-dev/SKILL.md:183-240`, `294-381`). 이 경로를 제거하면 아이디어에서
출발하는 기능 회귀다.

### 3.1 OPPD 제품 흐름

```text
사용자 //oppd
  ↓
선택적 DISCOVERY — 제품 기획이 별도 산출물로 필요할 때만 PRD 작성
  ↓
INTENT & PROJECT DESIGN — 목표·완료조건·아키텍처 확정
  ↓
SLICE & CONTRACT — 미니 태스크·계약·증거 역인덱스 생성
  ↓
CONTINUOUS EXECUTION — 충돌 없는 미니 태스크를 같은 프로젝트 worktree에서 병렬 실행
  ↓
INCREMENTAL CHECKPOINT — 범위별 commit·계약 검증
  ↓
PROJECT ACCEPTANCE — 완료조건과 증거 대응 판정
  ↓
CLOSE — 사용자 확인·문서 동기화·임시 자산 정리
```

Project Controller는 `opwt`, PRD, TRD 형식을 알지 않는다. OPPD Product Flow가 기획 결과를
`INTENT.md`와 `PROJECT-DESIGN.md`로 정규화해 Controller에 전달한다.

### 3.2 프로젝트 문서 역할과 생성 조건

`INTENT.md`는 PRD의 축약본이 아니다. 사용자 요청과 기존 프로젝트 문서, 사용자가 제공했거나 별도
Discovery에서 확정한 PRD를 Controller가 실행할 수 있는 짧은 **이번 실행 계약**으로 정규화한 문서다.
OPPD는 기본 흐름에서 PRD를 생성하지 않는다.

| 문서 | 소유 정보 | 생성 조건 | 다른 문서와의 관계 |
|---|---|---|---|
| `INTENT.md` | 이번 실행에서 달성할 목표·선택한 범위·제외 범위·완료조건·제약·예산·승인 | 모든 OPPD 실행 | PRD 본문을 복제하지 않고 선택한 requirement ID와 이번 실행 override만 참조 |
| `PRD.md` | 제품 차원의 문제·사용자·사용 흐름·비즈니스 규칙·기능 requirement | 사용자가 요구하거나 재사용할 제품 명세가 별도로 필요한 Discovery에서만 | 여러 실행이 참조하는 제품 입력. 실행 예산·코드 범위·DAG·기술 구현을 소유하지 않음 |
| `PROJECT.md`와 등록 문서 | 프로젝트 환경·원칙·문서 위치·기존 아키텍처·컨벤션·보안 기준 | 기존 OPAL 프로젝트에서는 읽기 | `PROJECT.md`를 문서 허브로 사용해 관련 `ARCHITECTURE.md`·`CONVENTIONS.md`·`SECURITY.md` 등을 선별 로드 |
| `TRD.md` | 아직 승인되지 않은 새 기술 기준·대안·trade-off·목표 구조 | greenfield 또는 기존 기술 SSOT에 없는 중대한 결정을 승인받아야 할 때만 | 현재 환경·컨벤션을 복제하지 않음. 승인 후 `ARCHITECTURE.md`·`SECURITY.md`·`CONVENTIONS.md`에 흡수하고 작업본은 보존·archive |
| `PROJECT-DESIGN.md` | 이번 실행의 변경 전략·미니 태스크 DAG·계약·lease·검증·통합 계획 | 모든 OPPD 실행 | INTENT와 프로젝트 문서, 선택적 PRD/TRD를 실행 구조로 변환 |

기존 OPAL 프로젝트의 판정 기준은 `.opal/AGENT.md`와 `docs/PROJECT.md`가 유효하고, PROJECT 문서
레지스트리로 현재 작업에 필요한 기술·컨벤션·보안 문서를 찾을 수 있는 경우다. 이때 OPPD는
`PROJECT.md`만 읽고 끝내는 것이 아니라 레지스트리에서 현재 변경 범위와 매칭되는 문서만 JIT로 읽는다.
기존 문서가 기술 결정을 충분히 덮으면 TRD를 만들지 않는다. 새 아키텍처·API·데이터 모델·보안 경계처럼
기존 기준에 없는 중대한 결정을 승인받아야 할 때만 **TRD delta**를 작성한다. 승인된 내용은 해당 기술
SSOT에 반영하므로 TRD와 ARCHITECTURE가 동시에 현재 상태의 SSOT가 되지 않는다.

OPAL 문서가 없거나 신규 프로젝트이면 `opi`로 프로젝트 정의와 문서 레지스트리를 먼저 만든다. 단순한
구현 목표는 인터뷰 결과를 바로 INTENT로 정규화하며 PRD를 만들지 않는다. 재사용할 제품 명세가 필요하면
상세 PRD를, 기술 기반이 없으면 상세 TRD를 선택적으로 작성한다. 사용자가 동등한 확정 문서를 제공한
경우에는 새 문서를 복제하지 않고 INTENT와 PROJECT-DESIGN에서 원문을 참조한다.

### 3.3 교체 후 진입점

| 진입점 | 역할 |
|---|---|
| `//opp` | 문서·설정·워크플로우 등 단일 프로젝트 태스크 |
| `//opd`·`//opds` | 공용 Runner를 사용하는 단일 개발 태스크 |
| `//oppd` | 기획·다중 태스크·통합·프로젝트 완료를 소유하는 유일한 프로젝트 개발 진입점 |
| `//oppl` | Controller 기능 이관과 v2 전환 후 폐기 |

검증 기간에는 공개 alias를 늘리지 않는다. 기존 `opal-pilot-project-dev/SKILL.md`를 router로 만들고,
같은 스킬 폴더의 내부 engine 문서가 v1·v2 본체를 소유한다.

- 기본: `//oppd` → v1
- 검증: `//oppd --engine=v2`
- 교체 직후: `//oppd` → v2, `--engine=v1`은 복구 전용
- 안정화 완료: v1 engine 문서와 flag 제거

내부 engine 문서는 공개 trigger와 alias가 없으므로 스킬 레지스트리에 두 번째 사용자 진입점으로
등록하지 않는다.

v1/v2 공존 중에도 v2의 미니 태스크는 프로젝트 worktree의 brain을 변경하지 않는다. 프로젝트 완료 후
Knowledge Finalizer가 허브 최신 상태를 기준으로 후보를 반영하므로 index·log의 최종 merge 충돌을
만들지 않는다. 동일 page에 대한 의미 충돌만 구조화 실패로 반환한다.

## 4. 책임 구조

| 구성요소 | 소유 책임 | 금지 책임 |
|---|---|---|
| OPPD Product Flow | 선택적 기획·사용자 게이트·최종 결과 경험 | 프로세스 감시·큐 직접 변경 |
| Controller Tool | 상태 reducer·DAG·큐·예산·사건·deadlock 판정 | 프로세스 실행·자연어 판단 |
| Runtime Supervisor | process group 실행·수확·timeout·tick 재호출 | 스케줄 판단·코드 수정 |
| PM Agent | 프로젝트 설계·슬라이싱·계약 변경·귀속 불명 실패 판단 | 프로세스 수명 관리 |
| Mini-task Runner | lease 범위 안의 설계·구현·로컬 검증 | Git 조작·공유 상태·lease 밖 변경 |
| Scope Lease Tool | write·contract·runtime resource 충돌 판정과 lease 수명주기 | 자연어 판단·코드 수정 |
| Checkpoint Tool | 실제 변경 검증·범위별 commit·실패 범위 복구 | 코드 작성·자동 충돌 해결·지식 반영 |
| Project Knowledge Finalizer | 완료 프로젝트의 memory·brain 후보 집계·허브 단일 반영 | 제품 코드·실행 중 지식 반영 |
| Integration Verifier | 계약·통합·회귀·보안·컨벤션 판정 | 코드 수정 |
| Evidence Tool | verifier evidence schema 검증·단일 파일 원자 저장·content hash 발급 | 테스트 실행·판정 변경 |
| Acceptance Evaluator | 완료조건과 증거의 대응 판정 | 테스트 실행·코드 수정 |

PM 아래 PL은 기본 생성하지 않는다. 독립 배포·독립 완료조건·별도 계약 경계를 가진 하위 프로젝트만
명시적 subgraph로 만들고 조건부 PL을 배정한다.

## 5. 실행 모델

### 5.1 순수 Controller tick

`controller tick`은 저장된 project state와 새 사건을 입력받아 다음 명령을 계산하는 순수 reducer다.

```text
입력: state revision + pending events + current budgets + now
출력: state transition + commands[] + decision_requests[]
```

`now`는 Supervisor가 RFC 3339 UTC 값으로 사건 입력에 명시하며 tick 내부에서 system clock을 읽지
않는다. 같은 revision·사건 집합·budget·`now`에는 같은 결과를 반환한다. 모든 갱신은 배타 락 안에서 revision을
재확인하고 임시 파일을 fsync한 뒤 원자적으로 교체한다. stale revision은 실행하지 않고 재-tick한다.

### 5.2 최소 Runtime Supervisor

PM이 수동으로 tick을 호출하는 구조는 대화 재개 문제를 해결하지 못한다. timeout만 집행하는
watchdog도 작업 종료 뒤 다음 Ready 태스크를 시작하지 못하므로 충분하지 않다.

Runtime Supervisor는 판단 로직 없이 다음만 수행한다.

1. 단일 instance PID·file lock 획득
2. Controller가 반환한 launch·cancel·verify·checkpoint 명령 실행
3. Runner를 별도 process group으로 시작하고 PID·시작 시각·명령 hash 기록
4. wrapper가 원자적으로 기록한 result·exitcode·heartbeat 수확
5. 무출력·시간 초과 시 process group 종료와 timeout 사건 기록
6. worker 종료·timeout·새 decision 응답마다 `controller tick` 재호출
7. PM 판단 사건이 나오면 해당 project를 `awaiting_decision`으로 둔다. 변경 대상 계약의 transitive
   downstream과 split 후보 태스크의 downstream을 `decision_affected`로 계산해 그 집합의 신규
   dispatch·checkpoint를 중단하고, 집합 밖 Ready 작업만 지속한다. 이미 실행 중인 영향 태스크는
   결과를 provisional로 보존하되 결정 전 checkpoint하지 않는다.

Supervisor가 죽어도 Controller 상태는 손상되지 않는다. 재시작 시 run registry를 읽고 다음처럼
복구한다.

- PID와 시작 fingerprint가 일치하고 살아 있음: 감시 재부착
- 프로세스 종료, exitcode 존재: 결과 수확
- 프로세스 없음, exitcode 없음: `orphaned_attempt` 사건
- 중복 Supervisor: file lock으로 두 번째 instance 거부

MVP 로그는 attempt별 크기 상한과 회전 파일 수를 두고, 전체 로그 로테이션 서비스는 만들지 않는다.

### 5.3 Controller → PM 사건

| 사건 | 결정론적 트리거 | PM 결정 |
|---|---|---|
| `contract_change` | Runner·Verifier가 계약 변경 필요 반환 | 계약 revision·직접 consumer 무효화 |
| `split_required` | Runner가 현재 범위로 완료 불가 반환 | 원 태스크 supersede·DAG 재분할 |
| `scope_violation` | Runner의 실제 변경·자원 사용이 lease를 벗어남 | 원 태스크 Repair·재분할 또는 사용자 에스컬레이션 |
| `integration_unattributable` | 통합 실패의 계약 위반 주체 불명 | 설계 보완·예비비 사용 여부 |
| `budget_exceeded` | 태스크·프로젝트 예산 중 하나 소진 | 범위 축소·중단·사용자 게이트 |
| `no_progress` | 같은 실패 지문과 결과가 두 시도 연속 반복 | 재분할·실행 전략 변경·사용자 에스컬레이션 |
| `project_knowledge_conflict` | 최종 허브 상태와 지식 후보를 결정론적으로 합성할 수 없음 | 후보 수정·제외 또는 사용자 게이트 |
| `external_workspace_change` | active lease·checkpoint receipt 어디에도 귀속되지 않는 diff 발견 | 사용자 변경 보존·재계획 또는 실행 재개 |
| `deadlock` | Ready 0·Running 0·blocked가 아닌 미완료 존재 | 순환 의존·누락 계약 진단 |

Ready와 Running이 없고 모든 미완료 태스크가 blocked이면 deadlock이 아니라
`awaiting_user`다. 목록 밖 판단 필요 상태는 `blocked`로 전환하며 Controller가 추측하지 않는다.

project knowledge batch에도 같은 `no_progress`와 예산 규칙을 적용한다. 동일 실패 지문 두 번 또는 batch
재시도·시간·비용 상한 중 하나에 도달하면 자동 재시도를 중단하고 사건을 발행한다. batch ID와
request 집합은 재시도 동안 유지하며 새 ID로 예산을 초기화하지 않는다. 모든 비용은 프로젝트에 합산한다.

## 6. 프로젝트 산출물과 쓰기 계약

| 산출물 | 단일 writer | 쓰기 방식 | 역할 |
|---|---|---|---|
| `INTENT.md` | PM | 사용자 확정 전 문서 갱신 | 목표·범위·제약·완료조건 |
| `PROJECT-DESIGN.md` | PM | 사용자 확정 전 문서 갱신 | 아키텍처·공용 방어·통합 전략 |
| `workgraph.json` | Controller Tool | 배타 락·revision·atomic replace | DAG·계약·큐·예산·상태 |
| `acceptance.json` | Controller Tool | 배타 락·revision·atomic replace | 완료조건·기여 태스크·증거 역인덱스 |
| `tasks/TNN/TASK.md` | PM | 실행 전 잠금 | 불변 태스크 계약 |
| `tasks/TNN/execution-packet.json` | Controller Tool | dispatch 직전 atomic replace | 가변 실행 입력 |
| `tasks/TNN/DESIGN.md` | Standard·Critical Runner | T2 완료 후 고정, Repair는 새 attempt 근거 참조 | 태스크 내부 구현 접근·영향 범위 |
| `tasks/TNN/TEST-SCENARIO.md` | Standard·Critical Runner | T3 RED/baseline 뒤 고정 | 수용·계약·회귀 시나리오 |
| `tasks/TNN/attempts/ANN/result.json` | 해당 Runner wrapper | temp write·fsync·atomic rename | 결과·검증·비용·변경 파일 |
| `tasks/TNN/DONE.md` | Controller Tool | accepted 결과와 증거에서 결정론적 렌더링 | 결과·checkpoint·증거 링크·남은 위험·지식 후보 |
| `evidence/<scope>/<evidence-id>.json` | 해당 Verifier wrapper | 단일 파일 temp write·fsync·atomic rename | 실행 명령·입력 hash·code head·환경·결과·artifact 참조 |
| `tasks/TNN/memory-index-request.json` | task-side memory tool | request ID·content hash 기반 원자 갱신 | 프로젝트 완료 후 memory index 반영 후보 |
| `tasks/TNN/brain-events/<event_id>.json` | Project Knowledge Finalizer | temp write·atomic rename·허브 attribution commit | 프로젝트 완료 후 생성한 본문·출처·page hash·event ID — Git 추적 |
| `runs/ANN/events.jsonl` | Runtime Supervisor | append-only | PID·heartbeat·종료·timeout 사건 |

운영 산출물의 루트는 허브 `<allocator_root>/.opal-runs/<run_id>/`다. workgraph·acceptance·events·
evidence는 이 run root에 저장하며 Git 미추적·worktree 회수 제외·CLOSE 이후에도 보존한다. 생성
도구가 ignore를 보장한다. evidence가 참조하는 로그도 이 루트에 복사·hash 검증한 후 발행한다.
태스크 문서와 request는 표의 task capsule 상대 경로로 Git 추적한다. CLOSE 산출물에는 증거 manifest
(상대 경로·hash·검증 결과)를 포함하고 영속 run root를 명시한다. evidence 삭제는 별도 보존 정책으로
처리하며 worktree remove에 연동하지 않는다.

Runner와 Verifier는 `workgraph.json`·`acceptance.json`을 직접 쓰지 않는다. 결과 파일을 발행하면
Supervisor가 Controller에 사건으로 전달한다. Evidence schema는 Evidence Tool이 소유하고,
Controller는 immutable evidence ID와 hash만 `workgraph.json`·`acceptance.json`에 색인한다. 여러
Verifier가 하나의 evidence 파일을 함께 갱신하지 않는다.

## 7. TASK와 계약 테스트

### 7.1 불변 TASK.md

`TASK.md`에는 다음을 고정한다.

- 목표와 프로젝트 완료조건 연결
- 허용·금지 변경 범위
- 입력·출력 계약과 수용 시나리오
- producer·consumer 관계
- 계약 테스트의 선언 ID와 예약 파일 경로
- 검증 명령·위험 등급·예산

실행 후 계약을 손편집하지 않는다. 변경이 필요하면 `contract_change` 사건과 새 revision으로 처리한다.

### 7.2 가변 execution-packet.json

Controller가 실제 dispatch 직전에 다음을 조립한다.

- 현재 유효한 선행 인터페이스와 contract revision
- 공용 방어 함수와 필수 회귀 테스트
- 직접 관련 문서와 결정
- 직전 실패 지문·차이·남은 작업
- 검증 cache key와 환경 지문

입력 hash와 생성 시각을 기록한다. 선행 결과가 바뀌거나 재시도하면 새로 생성한다. 이전 대화 전문은
넣지 않는다.

### 7.3 계약 테스트 생산 주체

SLICE & CONTRACT에서 PM은 테스트 코드를 쓰지 않는다. 대신 계약별로 다음 선언을 고정한다.

- 입력·출력·오류 의미
- producer와 직접 consumer
- 실행할 assertion ID
- 예약된 테스트 파일 경로와 실행 명령

producer 태스크의 완료조건에 예약 경로의 실행 가능한 계약 테스트 구현을 포함한다. consumer는
필요한 호환성 사례를 추가할 수 있지만 기존 assertion을 삭제하거나 약화할 수 없다. Integration
Verifier가 producer와 consumer가 닫히는 시점에 이 테스트를 실행한다. Critical 계약은 구현 전
Evaluator가 선언 완전성을 read-only로 검토한다.

## 8. Mini-task Runner 자산 매핑

### 8.1 미니 태스크 단계

미니 태스크는 별도 OPAL 태스크나 worktree가 아니라 프로젝트 실행 내부의 작고 독립적인 변경 단위다.
공통 단계는 다음으로 고정한다.

| 단계 | 주체 | 핵심 동작 | 산출·상태 |
|---|---|---|---|
| T0 DISPATCH | Controller | 불변 `TASK.md`와 최신 `execution-packet.json` 생성, profile·예산 확정 | `ready` |
| T1 LEASE | Scope Lease Tool | write·contract·runtime resource 충돌 검사, preimage hash 봉인 | `running` |
| T2 MICRO DESIGN | Runner | 구현 접근·영향 파일·직접 테스트 확정. Fast는 생략 가능 | 태스크 내부 설계 기록 |
| T3 TEST PROOF | Runner | 필요한 수용 시나리오·계약 테스트 준비, 변경 전 실패 또는 기존 기준선 확인 | RED/baseline evidence |
| T4 BUILD | Runner | lease 범위 안에서 구현·formatter·lint·직접 테스트 반복 | 변경 파일 |
| T5 LOCAL PROOF | Runner | 직접 테스트·영향 테스트·기존 보안 회귀. 공유 worktree이므로 결과는 provisional | `result.json`·candidate |
| T6 HANDOFF | Runner wrapper | 실제 file hash·명령·비용·지식 후보를 원자 기록하고 종료 | `provisional` |
| T7 CHECKPOINT | Checkpoint Tool | 범위 이탈 검사, 해당 lease 경로만 commit, receipt 기록 | `checkpointed` |
| T8 VERIFY | Verifier | checkpoint 기준 수용·계약·위험 보안·변경 파일 컨벤션 검사 | `accepted` 또는 Repair |

미니 태스크의 CLOSE는 T8의 논리적 `accepted` 전이다. worktree finalize·허브 merge·MEMORY·brain 반영은
수행하지 않는다. 실패하면 새 태스크나 worktree를 만들지 않고 원 태스크 예산을 유지한 Repair attempt로
T1 또는 T2에 돌아간다. 계약 변경이나 범위 재분할이 필요할 때만 PM 사건으로 승격한다.

#### 미니 태스크 문서 최소화

| 문서·증거 | 생성 시점 | 생성 profile | 소유 내용 |
|---|---|---|---|
| `TASK.md` | T0 | 전체 | 불변 목표·완료조건 연결·허용/금지 범위·계약·lease 요청·예산·검증 명령 |
| `execution-packet.json` | T0, 매 dispatch·Repair 직전 재생성 | 전체 | 현재 선행 결과·contract revision·입력 hash·실패 지문·남은 예산 |
| `DESIGN.md` | T2 | Standard·Critical만 | 이 미니 태스크 내부 구현 접근·영향 파일·트레이드오프. 프로젝트 아키텍처 반복 금지 |
| `TEST-SCENARIO.md` | T3 | Standard·Critical만 | 수용·계약·회귀 시나리오와 RED/baseline 증거. Fast는 TASK의 검증 명령 사용 |
| 제품 코드·테스트 | T4 | 전체 | lease 범위의 실제 변경 |
| `attempts/ANN/result.json` | T5~T6 | 전체 | 실제 changed files/hash·실행 명령·결과·비용·차단·지식 후보 참조 |
| verifier evidence | T7~T8 | 위험·계약 조건에 따라 | checkpoint code head·scope hash·보안·컨벤션·계약·수용 결과 |
| `DONE.md` | T8 accepted 직후 Controller가 렌더링 | 전체 | 결과·checkpoint·증거 링크·남은 위험·프로젝트 완료 때 검토할 지식 후보 |

Fast profile은 `TASK.md + execution-packet.json + result.json + DONE.md`만 만든다. 문서가 필요한
Standard·Critical에서만 DESIGN과 TEST-SCENARIO를 추가한다. 별도의 `ANALYSIS.md`, `PLAN.md`, `QA.md`,
`CLOSE.md`를 미니 태스크마다 만들지 않는다. 상세 실행 로그는 문서가 아니라 attempt/evidence JSON에
남긴다.

### 8.2 Profile별 기존 자산 매핑

기존 `opal-task-action-agent`를 v2 Runner로 축소·재구성하고 profile 입력을 추가한다. 기존 OPD와
OPPD v1은 전환 기간 compatibility adapter를 통해 기존 호출 계약을 유지한다. 자산 매핑은 Runner와
검증 경계를 한 표에서 고정한다.

adapter는 명시적 `engine:v2`와 profile이 있을 때만 새 경로로 보내고, 기존 입력에는 legacy 경로를
그대로 선택한다. 검증 기간에는 legacy 단계·출력 schema·하위 agent 호출을 삭제하지 않는다. v2 안정화
뒤 별도 회귀와 사용자 승인 없이 legacy 구현을 제거하지 않는다.

| 경계·프로필 | 호출 주체 | 기존 자산 | v2 과정 |
|---|---|---|---|
| Fast | Runner | `op-dev-execute` + 선언 검증 명령 | BUILD → formatter/lint → 직접 테스트 → HANDOFF |
| Standard | Runner | `op-dev-plan` + `op-dev-qa` 기준 adapter + `op-dev-test-scenario` + `op-dev-execute` + `opal-test-agent` | MICRO DESIGN → 자체 문서 QA → RED/수용 시나리오 → BUILD → LOCAL PROOF → HANDOFF |
| Critical | Runner·Evaluator | Standard 자산 + `opal-evaluator-agent` | 독립 설계 검토 → BUILD → 심층 계약 검증 → HANDOFF |
| Split | Controller·PM | Controller·PM 계약 | Runner 실행 금지, `split_required` 반환 |
| 변경 파일 컨벤션 | Verifier wrapper | `opal-convention-checker` + `op-gc-convention` | 태스크 완료 후보의 `changed_files` read-only 검사 |
| 위험 변경 보안 | Verifier wrapper | `opal-security-checker` + `op-gc-security` | 위험 태스크·새 I/O 경로의 심층 read-only 검사 |
| 프로젝트 지식 귀속 | Project Knowledge Finalizer | 신규 다중 캡슐 adapter + `memory-tool`·`state-tool finalize-attribution`·`op-brain-ingest` 기준·`brain-tool` | 최종 허브 merge 확인 후 MEMORY·brain 1회 반영 |

현행 `op-dev-qa`는 PM 전용 기준이다. v2 adapter가 기준만 Runner 자체 검토에 적용하도록 호출 계약을
확장한다. Standard마다 PM을 호출하지 않으며 독립 검토가 필요한 Critical은 Evaluator를 사용한다.
checker role은 자체 규칙을 만들지 않고 대응 `op-gc-*` 스킬을 실행한다. AC-08은 이 표의 호출
주체·자산 allowlist를 기준으로 판정한다.

프로젝트 실행은 항상 `interactive: false`다. 질문이 필요하면 추측하거나 응답을 기다리지 않고
`blocked` 또는 정의된 PM 사건을 반환한다. 단일 `//opd` 사용 시에만 `interactive: true`를
허용한다.

## 9. 스케줄링·격리·동시성

### 9.1 연속 DAG

고정 Wave를 사용하지 않는다. 선행 계약이 충족되고 자원·예산·충돌 조건을 통과한 태스크를 Ready
큐에서 즉시 실행한다.

| 큐 | 진입 조건 | 처리 |
|---|---|---|
| Ready | 선행 계약 충족·예산 있음 | Runner dispatch |
| Checkpoint | Runner 성공·scope 검증 통과 | Controller 단일 writer가 범위별 commit |
| Revalidation | 직접 소비 계약 변경 | 수용 시나리오·계약 테스트만 재실행 |
| Repair | 귀속 가능한 구현·통합 결함 | 원 태스크 예산으로 독점 lease 재실행 |

### 9.2 worktree 격리

- worktree는 프로젝트 격리 단위다. OPPD가 이미 실행 중인 프로젝트 worktree를 사용하며 미니 태스크
  worktree를 중첩 생성하지 않는다.
- 구현 미니 태스크는 같은 프로젝트 worktree에서 실행하되 `write_set`, `contract_set`,
  `runtime_resources`에 대한 배타 lease를 먼저 받아야 한다.
- 계획·설계·구현·로컬 테스트·수정은 같은 미니 태스크의 단계다. 단계별 격리 공간을 만들지 않는다.
- 분석·읽기·검토·Acceptance 판정은 write lease 없이 pinned checkpoint와 허브 run root를 사용한다.
- 서로 독립적으로 수용할 수 없거나 같은 파일을 연속 수정해야 하는 작은 작업은 별도 미니 태스크로
  분할하지 않고 하나의 구현 태스크로 묶는다. 예상 setup·조정 비용이 실행시간의 20%를 넘는
  분할도 합치는 쪽을 기본으로 한다.
- 병렬 실행은 세 집합이 모두 비충돌일 때만 허용한다. 공용 인터페이스·schema·lockfile·generated
  file·formatter 전역 범위·테스트 DB·port·service는 공유 자원으로 선언해 직렬화한다.
- 자동 실행 구간에는 프로젝트 worktree의 모든 변경이 active lease 또는 Controller receipt에 귀속돼야
  한다. 사용자의 별도 변경은 덮어쓰거나 되돌리지 않고 `external_workspace_change`로 일시 정지한다.
- Controller는 dispatch 전에 leased 파일의 존재 여부와 content hash를 preimage manifest에 기록한다.
  Runner는 허용 범위만 수정하며 `git add`·`commit`·`merge`·`rebase`를 실행하지 않는다.
- 프로젝트 worktree의 `.opal/MEMORY.json`과 `.opal/brain/**`는 project-start snapshot이며 수정 금지다.
  학습 결과는 task capsule request로만 반환한다.
- Runner 종료 후 wrapper가 lease 범위의 실제 file hash를 기록하고 Checkpoint Tool이 범위 이탈을
  검사한다. 범위 이탈이면 checkpoint하지 않고 `scope_violation`을 반환한다.
- 실패 복구는 해당 lease의 preimage만 Controller가 복원한다. 다른 활성 lease와 겹치면 자동 복구하지
  않고 모든 관련 writer를 멈춘 뒤 판정한다.
- 공유 worktree에서 실행한 로컬 테스트는 provisional 증거다. 계약 검증은 관련 write lease가 닫힌
  checkpoint에서, 전체 회귀는 모든 writer가 멈춘 최종 checkpoint에서 다시 실행한다.

### 9.3 동시성 정책

- MVP 하드 상한은 2다.
- 첫 태스크는 단독 실행해 Runner 준비 시간·공유 자원 사용량을 측정한다.
- 준비·조정 비용이 태스크 전체 시간의 20%를 넘으면 태스크를 합치거나 동시성 1을 유지한다.
- 비용이 20% 이하이고 write·contract·runtime resource가 모두 겹치지 않을 때만 2를 사용한다.
- CPU·메모리·디스크·비용 임계치 도달 시 신규 dispatch를 중단한다.
- 패키지 다운로드처럼 내용 주소 기반·읽기 안전 캐시만 공유한다.
- mutable build 출력은 태스크별 임시 경로를 쓰거나 resource lease로 직렬화한다.

상한 3 이상은 benchmark와 실제 프로젝트에서 자원·충돌·준비 비용 기준을 통과한 뒤 설정으로만
확대한다.

## 10. 공유 프로젝트 worktree 통합 모델

### 10.1 Scope lease

Scope Lease Tool은 Controller만 호출한다. 각 lease는 `task_id`, `attempt_id`, `write_set`,
`contract_set`, `runtime_resources`, `base_checkpoint`, `preimage_manifest`, `generation`을 가진다.
경로는 canonical realpath로 정규화하고 파일·디렉터리·glob 포함 관계까지 비교한다. 계약과 실행 자원도
같은 ID를 쓰는 활성 lease가 있으면 충돌로 판정한다.

lease registry는 허브 `.opal-runs/<run_id>/leases/`에 atomic write하며 `fcntl.flock`으로 직렬화한다.
시간 만료만으로 lease를 탈취하지 않는다. Supervisor는 owner PID·시작 fingerprint·heartbeat를 확인하고
process group 종료 또는 정상 result 수확 뒤에만 lease를 해제한다.

MVP의 lease는 실행 허가와 사후 검증 계약이지 OS 파일 권한 격리가 아니다. 따라서 Runner의 범위 이탈을
발견하면 해당 시점의 병렬 결과를 안전하다고 간주하지 않고 관련 writer를 모두 정지한다. 향후 플랫폼이
경로 단위 sandbox를 제공할 때만 동일 계약 아래 hard enforcement를 추가한다.

### 10.2 Checkpoint commit

Checkpoint Tool은 프로젝트 branch의 유일한 Git writer다. Runner와 Verifier는 Git index·ref를
조작하지 않는다. 동시에 끝난 태스크는 완료 속도가 아니라 workgraph 위상 순서와 태스크 ID 순서로
처리한다.

1. result·lease generation·preimage·실제 file hash 확인
2. lease 밖 변경과 다른 활성 lease 침범 여부 검사
3. 해당 태스크 경로만 명시적으로 stage하고 예상 diff hash 재확인
4. `task_id`·계약 revision·evidence ID를 포함한 checkpoint commit 생성
5. commit receipt를 원자 기록하고 태스크를 `checkpointed`로 전이
6. 계약 경계가 닫히면 관련 검증을 실행하고 통과 시 `accepted`

Git index lock은 Checkpoint Tool이 독점한다. 다른 Runner의 lease 파일은 stage하지 않으며 commit 뒤에도
그 변경은 working tree에 그대로 남아야 한다. 이 동작은 임시 실제 Git 저장소에서 병렬 writer를 둔
회귀 테스트로 검증한다. 예상하지 않은 staged 파일, lease 밖 diff 또는 hash drift가 있으면 commit하지
않고 구조화 실패를 반환한다.

프로젝트 지식 반영은 최종 허브 merge 뒤 별도의 허브 writer lock 아래 수행한다. 프로젝트 실행 중
checkpoint는 knowledge candidate와 request의 보존 위치·hash만 기록하고 MEMORY나 brain에 적용하지
않는다.

최종 허브 merge 후 Supervisor는 Project Knowledge Finalizer를 한 번 실행한다. Finalizer는 모든
accepted task capsule을 위상 순서로 읽고 중복 후보를 합성한 뒤, 명시적 allocator root에서 신규 허브
요청 적용기·`memory-tool`·`state-tool finalize-attribution`·`brain-tool`을 사용해 MEMORY와 brain을
반영한다. last_task_number를 snapshot 값으로 되돌리지 않는다. 요청별 receipt는 run registry에
원자 기록하며, 적용 뒤 receipt 기록 전에 종료돼도 request/event ID와 허브 저장 결과를 대조해 중복
적용하지 않는다. FIFO history에 행이 남아 있는지만으로 멱등성을 판단하지 않는다.

canonical resolver는 프로젝트가 active인 동안 프로젝트 worktree의 단일 task capsule을 선택하고,
최종 허브 merge가 Git 조상 관계로 확인된 뒤 허브 사본으로 전환한다. 귀속 pending인 허브 사본도
정상 경로다. 증명 없는 중복 사본은 기존처럼 차단한다. `project_done`·`awaiting_merge`·
`project_attribution_pending`을 finalize 멱등 분기에 추가하고 기존 closed 전용 경로는 v1 호환
분기로 유지한다.

### 10.3 semantic conflict 귀속

| 실패 | 귀속 |
|---|---|
| producer가 명시 계약을 위반 | producer Repair |
| consumer가 명시 계약을 잘못 사용 | consumer Repair |
| 양쪽이 계약을 지켰으나 checkpoint 검증 실패 | `integration_unattributable`, PM 설계 보완 |
| 계약에 없는 semantic conflict | `integration_unattributable`, SLICE 결함 |

계약별 producer와 모든 직접 consumer가 `checkpointed`가 되면 해당 계약 검증을 자동
트리거한다.

### 10.4 needs_revalidation

계약 변경 시 직접 consumer만 `needs_revalidation`으로 전환한다. 재검증은 해당 태스크의 수용
시나리오와 계약 테스트만 실행한다.

- 통과: `accepted` 복귀
- 실패: 해당 태스크 Repair
- Repair가 자신의 출력 계약을 변경: 다음 직접 consumer에 새 1-hop 재검증

### 10.5 프로젝트 단위 MEMORY·brain 반영 경계

미니 태스크는 project-start MEMORY·brain snapshot을 읽을 수 있지만 갱신하지 않는다.
프로젝트 설계·계약·accepted 결과가 같은 실행에서 필요한 최신 지식을 전달하므로 중간 brain 반영을
태스크 간 통신 수단으로 사용하지 않는다.

최종 허브 merge 확인 후 Project Knowledge Finalizer가 다음을 한 batch로 수행한다.

1. 모든 accepted task의 memory request·DONE 후보·결정·결과를 읽고 중복과 미실체 후보 제거
2. MEMORY index와 task history를 허브 최신 문서에 멱등 적용
3. brain page를 허브 최신 page와 대조해 add·update·skip 결정
4. `brain-tool index`로 전체 page에서 index 재생성
5. log event를 event ID별 한 번만 append
6. 각 결과와 최종 파일 hash를 receipt로 기록하고 모든 검증 통과 후 attribution commit 생성

현행 `brain-tool index`는 페이지를 스캔해 재생성하고(`brain_tool.py:752`), `log`는 ID 없는 append다
(`brain_tool.py:772`). 따라서 log event 멱등 적용과 project batch receipt는 신규 구현이다. 현행
brain-tool에는 writer lock이 없으므로 허브 공용 락도 새로 도입한다. v1·v2의
add-page·update-page·log·index와 Project Knowledge Finalizer가 같은 락을 사용한다. 중간 실패 시
완료 receipt가 없는 단계부터 재개하며 새 프로젝트 batch ID로 예산을 우회하지 않는다.

## 11. Repair 계약

Repair는 원 태스크의 예산을 우회하는 새 루트 태스크가 아니다.

- `origin_task_id`, `trigger_event_id`, `attempt_index`, `affected_contracts` 필수
- 사용 시간·토큰·비용을 원 태스크와 프로젝트 예산에서 동시에 차감
- 원 태스크 재시도 상한에 포함
- 원 태스크 예산 소진 시 추가 생성 금지, `no_progress` 또는 `budget_exceeded`

Repair는 새 worktree를 만들지 않는다. 실패한 태스크와 충돌 가능한 lease를 모두 닫은 뒤 현재 프로젝트
checkpoint에서 독점 write·contract·resource lease를 받아 실행한다. 실패 원인과 관련 결과를
execution packet에 넣되 변경 권한은 귀속된 태스크 범위로 제한한다. 복구 전 preimage와 새 checkpoint
receipt를 모두 보존한다.

귀속 불가능한 설계 누락은 프로젝트 예비비에서 명시적 design Repair를 만들며, 예비비 사용은 PM과
사용자 게이트를 거친다.

## 12. 검증·보안·컨벤션과 증거 신선도

| 경계 | 소유자 | 실행 항목 |
|---|---|---|
| 변경 중 | Runner | lease 범위 formatter·lint·직접 단위 테스트·기존 보안 회귀 — provisional |
| checkpoint 후보 | Checkpoint Tool·변경 파일 checker | 범위 이탈·hash·수용 시나리오·영향 회귀·변경 파일 프로젝트 컨벤션 |
| 위험 변경 | Security Verifier | 새 I/O·인증·권한·외부 입력·명령 실행 심층 검사 |
| 계약 폐쇄 | Integration Verifier | producer-consumer 계약·관련 통합 테스트 |
| 프로젝트 완료 후보 | Integration Verifier | 전체 회귀·통합 보안·전체 신규 컨벤션 위반 검사 |
| 완료조건 판정 | Acceptance Evaluator | 완료조건별 증거 존재·신선도·통과 상태 대응 |

Acceptance Evaluator는 테스트를 실행하지 않는다. `acceptance.json`의 완료조건과 Runner·Verifier
증거 대응만 판정한다.

각 검증 실행은 공유 배열에 append하지 않고 `evidence/<scope>/<evidence-id>.json` 한 파일을 새로
발행한다. Evidence Tool이 소유하는 schema의 필수 필드는 다음과 같다.

- `evidence_id`, `scope`, `producer`, `status`
- `task_ids`, `contract_ids`, `acceptance_ids`
- `command`, `code_head`, `scope_hash`, `input_hash`, `environment_hash`
- `started_at`, `finished_at`, `artifact_refs`

Runner·Integration Verifier·Security Verifier·Convention Verifier는 각자 wrapper를 통해 자신의
evidence만 쓴다. Controller는 schema 검증과 content hash 확인 뒤 ID를 색인하며 결과 본문을 다시
작성하지 않는다.

공유 worktree의 Runner evidence는 provisional로 저장한다. Controller는 관련 write·contract·resource
lease가 닫힌 checkpoint에서 검증을 다시 실행하거나, 실행 입력과 `scope_hash`가 동일함을 증명한
경우에만 완료 증거로 승격한다.

증거 신선도는 다음으로 고정한다.

- 태스크 증거: 해당 태스크 코드·테스트·execution packet hash가 유지되는 동안 유효
- 계약 증거: producer·직접 consumer 집합과 contract revision이 유지되는 동안 유효
- 프로젝트 증거: 모든 writer가 멈추고 필수 checkpoint가 반영된 단일 project head에서만 생성

검증 cache key는 코드·테스트·명령·의존성 잠금·환경·execution packet hash를 포함한다. 프로젝트
전체 회귀는 최종 project checkpoint에서 모든 write lease를 막고 한 번 실행한다.

## 13. 선택적 Discovery·기술 결정과 사용자 게이트

| 입력 상태 | 동작 |
|---|---|
| 목표·범위·완료조건·핵심 제약이 충분 | 별도 PRD 없이 INTENT 작성 |
| 기존 OPAL 프로젝트·기술 문서 충분 | PROJECT 문서 레지스트리에서 관련 문서만 읽고 TRD 생략 |
| 재사용할 제품 명세가 필요 | 별도 Discovery로 PRD 작성 후 INTENT가 requirement ID만 선택 |
| greenfield·비 OPAL·기술 기준 없음 | `opi` 후 상세 TRD 작성, 승인 내용을 기술 SSOT에 반영 |
| 기존 프로젝트에 중대한 신규 기술 결정 | 현재 문서를 참조하는 TRD delta만 작성·승인 후 기술 SSOT 갱신 |
| 승인된 PRD·TRD 또는 동등 문서 제공 | 재작성하지 않고 INTENT·PROJECT-DESIGN에서 ID·경로 참조 |

사용자 게이트는 다음으로 제한한다.

- 최초 프로젝트 계약과 프로젝트 branch의 Controller checkpoint commit 승인
- 기능 범위 또는 외부 계약 변경
- 비가역 작업·실제 배포·최종 main 반영
- 프로젝트 예산 초과·설계 예비비 사용
- 반복 실패의 제품·설계 판단
- 자동 실행 중 귀속되지 않은 외부 workspace 변경
- 최종 CLOSE

일반 태스크 완료, 상태 확인, 귀속 가능한 Repair에는 사용자를 호출하지 않는다.

## 14. 완료 판정

다음을 모두 만족해야 `project_done` 후보가 된다.

1. 필수 완료조건이 `acceptance.json`에 모두 등록됨
2. 완료조건별 기여 태스크와 증거 역인덱스 존재
3. 필수 태스크가 모두 `accepted`이고 `needs_revalidation` 없음
4. 전체 회귀·통합 보안·신규 컨벤션 위반 검사 통과
5. 미해결 blocker와 살아 있는 Runner·자식 프로세스 0
6. Acceptance Evaluator가 모든 필수 완료조건을 증거로 충족 판정
7. MEMORY·brain 후보와 근거·본문·증거가 영속 보존되고 프로젝트 단위 반영 가능한 상태

이 후보는 최종 반영 준비 완료를 뜻하며 registry `closed`를 요구하지 않는다. 사용자 승인 후 허브
merge는 사용자 재개 명령으로 확인한다. 승인 시 동결한 project head를 대상으로
`git merge-base --is-ancestor <approved-project-head> <hub-HEAD>`가 성공해야 후처리를 시작한다.
실패하면 awaiting_merge로 유지한다. 허브 HEAD 폴링으로 사용자 게이트를 넘지 않는다. 확인 성공 시
canonical 경로를 허브로 전환하고 Project Knowledge Finalizer를 한 번 수행한다.
모든 MEMORY·brain receipt가 확인되고 project knowledge queue가 비었으며 project registry가 `closed`일
때만 최종 CLOSE한다.
후처리 실패 시 merge를 반복하지 않고 미처리 요청부터 재개한다. 증거 manifest와 보존 경로를 최종
산출물에 기록한 뒤 worktree를 회수한다.

## 15. 백업·benchmark·교체 게이트

### 15.1 백업

활성 소스에 v1 복사 폴더를 만들지 않는다. 현재 OPPD v1 commit에 annotated tag
`oppd-v1-before-rewrite`를 먼저 생성하고 별도 worktree에서 v2를 개발한다. benchmark 기준선은 이
태그를 checkout해 이후에도 재현한다.

### 15.2 benchmark 설계

대표 fixture는 각각 30~60분, 5~8개 미니 태스크 규모로 만든다.

- 독립 태스크가 많은 프로젝트
- 공유 모듈을 순차 변경하는 프로젝트
- 외부 I/O·인증 또는 보안 경계를 포함한 프로젝트

v1은 태그에서 fixture별 1회만 실행해 기준선 3건을 만든다. 대화 세션 기반 v1을 9회 반복해 사람을
5~9시간 묶지 않는다. v2는 fixture별 3회 실행해 분산과 무인 완주를 확인한다. 최종 benchmark는
v1 3회 + v2 9회, 총 12회다. 실행 전 예상 시간·모델 비용을 계산해 사용자에게 승인받는다.

### 15.3 차단 조건과 관찰 지표

v1 PM 대화 세션의 전체 token과 수동 재촉 횟수는 현행 도구로 자동 측정할 수 없다. 판정 불가능한
값을 교체 차단 조건으로 사용하지 않는다.

| 분류 | 지표 | 처리 |
|---|---|---|
| 차단 | 수용 시나리오·전체 회귀·보안·컨벤션 품질 | v1 동등 이상, 신규 차단 결함 0 필수 |
| 차단 | 사용자 게이트 사이 무인 실행 | 상태 확인·재촉·강제 재개 없이 완료 또는 구조화 decision 도달 |
| 차단 | runtime 안전성 | 고아 process·상태 손상·미감지 deadlock 0 |
| 관찰 | 전체 활성 경과 시간 | v1·v2 start/end 기록, 사용자 대기 제외 |
| 관찰 | 워커 token·비용 | opal-agent로 관측되는 호출분만 비교 |
| 관찰 | 재작업 범위 | 실패가 유발한 재실행 태스크 수 비교 |
| 관찰 | 준비·조정 비용 | Runner 준비 시간·lease 대기·공유 자원 직렬화·최대 동시성 기록 |

시간과 token의 목표는 각각 v1의 80%, 관측 가능한 워커 token의 70%로 유지하되 교체 불가를 만드는
하드 게이트로 쓰지 않는다. 목표 미달은 후속 최적화 백로그와 원인 보고를 생성한다. 품질 또는 무인
실행 차단 조건이 실패하면 엔진을 전환하지 않는다.

## 16. 병렬 구현 계획

v1 benchmark 3종 완주를 v2 개발의 직렬 선행 조건으로 두지 않는다.

### Gate 0 — 착수 전 필수

1. 현재 OPPD v1 source tag 생성
2. Controller·Supervisor·Scope Lease·Checkpoint·계약 테스트 생산 주체 결정 확정
3. benchmark fixture 계약과 측정 범위 확정
4. 모든 미니 태스크의 MEMORY·brain 읽기 전용, request 보존, 프로젝트 완료 후 일괄 반영 계약 확정

### Track A — Runtime Core

1. Controller 상태 reducer·락·atomic state
2. Runtime Supervisor process group·수확·timeout·재부착
3. 사건·예산·deadlock 회귀 테스트

### Track B — Runner와 Project Workspace

1. action-agent profile 축소
2. execution packet·result 계약
3. 프로젝트 worktree 단일 수명주기와 미니 태스크 중첩 worktree 금지
4. OPPD v1·단일 OPD 호출 계약을 보존하는 compatibility adapter와 공개 CLI 회귀 테스트
5. Standard 문서 QA의 Runner 자체 검토 adapter 및 불필요한 PM 호출 부재 검증
6. write·contract·runtime resource lease와 preimage manifest·crash 회수 구현

### Track C — Checkpoint와 Verification

1. Controller 단일 Git writer·범위별 checkpoint commit·부분 복구
2. 프로젝트 worktree 공유 지식 쓰기 금지·후보 봉인·프로젝트 완료 후 허브 일괄 귀속
3. 계약 테스트 trigger·귀속·1-hop revalidation
4. Evidence schema·GC checker·Evaluator·Acceptance 연결
5. Project Knowledge 후보·batch·receipt schema와 충돌 반환 계약
6. project merge receipt 기반 canonical resolver·새 상태와 finalize 멱등 분기·보존 hash 기반 remove 가드
7. 최종 허브 merge·project knowledge 반영·crash 재개·evidence 보존을 연결한 실제 Git 회귀 시나리오
8. Project Knowledge Finalizer: 허브 MEMORY batch·brain page/index/log batch·공용 writer 락·defer pending·receipt 복구

### Track D — 기준선과 제품 흐름

1. 태그에서 OPPD v1 smoke·기준선 측정
2. 선택적 Discovery·기술 결정·engine router
3. v2 smoke·최종 benchmark·문서 동기화

Track A~D는 계약 파일이 잠긴 뒤 병렬 진행한다. 기본 `//oppd` 전환은 네 트랙과 차단 조건이 모두
통과한 뒤 수행한다.

실행 의존은 B-6(scope lease·preimage) → C-1(checkpoint commit), C-5의 후보·receipt schema 확정
→ C-8(Project Knowledge Finalizer)이다. 의존 API의 fixture 작업은 병행할 수 있지만 선행 기능 없이
실행 완료로 보고하지 않는다.

## 17. 수용 시나리오

| ID | 검증 시나리오 | 통과 증거 |
|---|---|---|
| AC-01 | 명확한 입력과 일부 불명확한 입력을 각각 투입 | 둘 다 INTENT 생성, 후자는 결측 질문만 수행, PRD 자동 생성 0 |
| AC-02 | 같은 state revision·사건·budget·`now`로 tick을 두 번 실행 | 동일 commands·decision 결과, 중복 state 전이 0 |
| AC-03 | Supervisor 실행 중 프로세스를 강제 종료 후 재시작 | result 수확 또는 `orphaned_attempt`, 상태 손상 0 |
| AC-04 | timeout보다 긴 무출력 process 실행 | process group 종료·timeout 사건·다음 tick 자동 호출 |
| AC-05 | 충돌 없는 Ready 태스크 두 개를 생성 | 프로젝트 worktree는 1개 유지, 서로 겹치지 않는 write·contract·resource lease 두 개 발급 |
| AC-06 | 두 Runner가 동시에 결과 반환 | 각 result 원자 생성, 공유 JSON 손상·lost update 0 |
| AC-07 | 입력 필수 항목을 제거한 `interactive:false` 태스크 실행 | 추측·정지 없이 `blocked` 또는 정의 사건 반환 |
| AC-08 | Fast·Standard·Critical fixture 실행 | 각 profile에 정의된 기존 자산만 호출 |
| AC-09 | producer 태스크 완료 | 예약 경로에 실행 가능한 계약 테스트 존재·통과 |
| AC-10 | 완료 순서와 위상 순서를 반대로 만든 두 태스크 checkpoint | 위상 순서·태스크 ID 순으로 범위별 commit |
| AC-11 | 동일 파일·계약·runtime resource를 각각 요구하는 태스크 둘 생성 | 두 번째 동시 dispatch 차단, 중복 lease 0 |
| AC-12 | producer와 consumer의 계약 위반을 각각 주입 | 계약 근거에 따라 정확한 origin Repair 생성 |
| AC-13 | 계약 밖 semantic conflict 주입 | `integration_unattributable`과 PM decision 요청 |
| AC-14 | 계약 revision 변경 | 직접 consumer만 `needs_revalidation`, 무관 태스크 불변 |
| AC-15 | 모든 미완료를 blocked로 설정 | `awaiting_user`, deadlock 미발행 |
| AC-16 | Ready·Running 0이며 실행 가능한 미완료를 남김 | `deadlock` 발행 |
| AC-17 | 원 태스크 예산을 소진한 뒤 Repair 요청 | Repair 생성 거부·budget/no-progress 사건 |
| AC-18 | 변경 파일에 프로젝트 컨벤션 위반 삽입 | 태스크 완료 후보 단계에서 차단 |
| AC-19 | 기여 태스크 hash를 바꾸고 기존 증거 재사용 시도 | 관련 태스크·계약 증거 stale 판정 |
| AC-20 | 최종 project checkpoint 이전 증거로 project_done 시도 | 프로젝트 증거 부적합으로 거부 |
| AC-21 | 사용자 게이트 사이 대표 프로젝트 실행 | 수동 tick·재촉·강제 resume 0회 |
| AC-22 | `//oppd --engine=v2`와 기본 v1 호출 | 동일 공개 alias에서 올바른 내부 engine 선택 |
| AC-23 | v2 차단 조건 실패 | 기본 engine v1 유지 |
| AC-24 | 차단 조건 전체 통과 후 전환 | 기본 v2, 복구 flag 외 신규 공개 alias 0 |
| AC-25 | 동시성 2로 비충돌 구현 태스크 둘을 같은 프로젝트 worktree에서 완주 | 중첩 worktree·mini branch 0, 범위 밖 변경 0, OPAL task 번호 추가 발급 0, PM decision 호출 0 |
| AC-26 | T02가 미완료 변경을 가진 동안 T01 checkpoint commit | T01 lease 경로만 commit, T02 변경은 working tree에 보존, Git index·ref 손상 0 |
| AC-27 | adapter 경유 v1 OPPD와 단일 OPD 회귀 fixture 실행 | 기존 입력·출력·단계 호출 계약 통과, `--engine=v1` 복구 가능 |
| AC-28 | contract decision 대기 중 영향·비영향 태스크를 함께 Ready로 설정 | 영향 subgraph dispatch·checkpoint 0, 비영향 태스크만 진행, 실행 중 영향 결과는 provisional 보존 |
| AC-29 | 두 Verifier가 동시에 서로 다른 evidence를 발행 | schema-valid immutable 파일 2개, 경로 충돌·lost update 0, Controller index hash 일치 |
| AC-30 | 프로젝트 병렬 실행과 checkpoint 뒤 최종 허브 merge | 프로젝트 branch의 MEMORY·brain diff 0, 허브 기존 변경 보존, 공유 지식 파일 때문에 merge가 거부되지 않음 |
| AC-31 | 최종 허브 merge 뒤 Project Knowledge Finalizer가 MEMORY를 적용하고 receipt 직전 중단·재시작 | 허브 canonical 경로 정상, MEMORY·brain·history 중복 0, 채번 역행 0, 전체 후처리 완료 후만 closed |
| AC-32 | checkpoint commit 중 Supervisor 종료·재시작 | 이전 Git writer 확인 전 신규 writer 0, commit receipt·HEAD 대조로 중복 commit 없이 복구 |
| AC-33 | 한 병렬 태스크 실패 후 preimage 복구 | 실패 태스크 lease 파일만 복원, 다른 태스크 변경·신규 파일 유실 0 |
| AC-34 | 프로젝트 worktree 회수 뒤 evidence manifest 검증 | 허브 run root의 증거·로그 hash 일치, 증거 유실 0 |
| AC-35 | Standard 태스크의 문서 QA 수행 | Runner 자체 검토 증거 존재, 문서 QA만을 위한 PM 호출 0 |
| AC-36 | 미니 태스크가 프로젝트 worktree에서 MEMORY·brain 쓰기를 각각 시도 | 모두 `SHARED_META_WRITE_REJECTED`, 공유 지식 파일 무변경 |
| AC-37 | v2 실행 중 v1이 허브 brain을 갱신한 뒤 v2 최종 merge·프로젝트 지식 반영 | 프로젝트 branch brain diff 0, Finalizer가 최신 허브를 읽어 v1 이력 보존, index 전체 페이지 반영, 이벤트 중복 0 |
| AC-38 | 프로젝트 완료·Finalizer 실행 전/후 request 상태 검사 | 실행 전 pending·resolved 미등록, 프로젝트 단위 실제 반영 증명 후만 applied |
| AC-39 | merge 전과 승인 commit merge 후 각각 사용자 재개 명령 | 전자는 awaiting_merge, 후자만 canonical 전환·후처리 실행 |
| AC-40 | project knowledge batch에 같은 실패를 두 번 주입 | no_progress 발행·자동 재시도 중단, batch 재발급에 의한 예산 우회 0 |
| AC-41 | 설계·구현·테스트·수정 단계를 가진 미니 태스크와 read-only 검토를 함께 실행 | 프로젝트 worktree 총 1개, 단계·검토용 추가 worktree 0 |
| AC-42 | 같은 파일을 연속 수정하고 setup·조정 예상 비용이 실행시간의 20%를 넘는 두 작업을 입력 | 하나의 미니 태스크로 병합하거나 순차화, 불필요한 병렬 Runner 0 |
| AC-43 | 서로 다른 파일이지만 같은 DB·port·generated file을 요구하는 태스크 둘을 입력 | runtime resource lease 충돌로 동시 실행 차단, 데이터·산출물 오염 0 |
| AC-44 | active lease 밖에서 사용자 변경을 만든 뒤 checkpoint 시도 | 변경 보존, commit·자동 복구 0, `external_workspace_change`와 사용자 게이트 발생 |
| AC-45 | PROJECT 문서 레지스트리와 관련 기술 기준이 충분한 기존 OPAL 프로젝트 실행 | 등록 문서 선별 read, 신규 PRD·TRD 0, PROJECT-DESIGN에는 참조와 변경 delta만 존재 |
| AC-46 | OPAL 문서와 기술 기준이 없는 greenfield 프로젝트 실행 | `opi` 선행, 필요 범위의 상세 TRD와 기술 SSOT 승격 계획 생성 |
| AC-47 | 기존 프로젝트에 중대한 신규 기술 결정을 승인 | TRD delta에 대안·근거만 기록, 승인 뒤 기술 SSOT 반영, 현재 상태를 중복 소유하는 문서 0 |

각 시나리오는 mock 내부 함수가 아니라 임시 실제 Git 저장소, 실제 subprocess, 공개 CLI와 생성된
상태 파일을 기준으로 검증한다.

## 18. 확정 사항과 구현 설정

이 제안에서 아키텍처로 확정하는 항목은 다음이다.

- 순수 tick reducer + 자동 tick Runtime Supervisor
- 프로젝트당 worktree 1개, 미니 태스크 중첩 worktree·branch 미생성
- 비충돌 write·contract·runtime resource lease를 받은 미니 태스크만 병렬 실행
- Runner Git 금지와 Controller 단일 checkpoint writer
- 모든 미니 태스크의 MEMORY·brain 읽기 전용과 프로젝트 완료 후 허브 1회 반영
- producer가 구현하고 Verifier가 실행하는 계약 테스트
- 단일 writer·배타 락·원자적 상태 저장
- blocking release gate와 observational performance metric 분리
- v1 benchmark와 v2 구현의 병렬 진행

구현 태스크에서 정할 값은 다음 설정뿐이다.

- 프로젝트 예산과 설계 예비비 기본 비율
- heartbeat·무출력·hard timeout 기본값
- process·로그 보존 상한
- environment fingerprint 필드
- 실제 프로젝트 안정화 표본 선정 기준

이 값들은 Controller 설정 schema와 benchmark spec이 소유하며 스킬 산문에 복제하지 않는다.
