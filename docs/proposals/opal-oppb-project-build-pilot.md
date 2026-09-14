# OPPB — 프로젝트 빌드 Pilot 제안서

> 상태: 초안
> 작성: 알투(PM)
> 작성일: 2026-09-13 (신규 Pilot 프레이밍 개정: 2026-09-14)
> 대상 스킬: `opal-pilot-project-build` (alias `oppb`)
> 설계 참조: 현행 OPPD(`opal-pilot-project-dev`)와 `opal-oppd-v2-project-execution.md`
> 목적: 프로젝트 worktree 하나에서 충돌 없는 미니 태스크를 병렬 실행하되 사용자 단계·문서·반복 에이전트 호출을 최소화한다.

---

## 1. 결론

OPPB은 다음 구조로 단순화한다.

```text
선택적 DISCOVERY
→ INTENT
→ PROJECT DESIGN & SLICE
→ MINI-TASK RUN · PROVE · ACCEPT
→ PROJECT VERIFY
→ MERGE · KNOWLEDGE · CLOSE
```

- 프로젝트당 worktree는 하나만 사용한다.
- 미니 태스크마다 worktree·branch·OPAL task 번호를 만들지 않는다.
- PRD는 OPPB 필수 산출물이 아니다. 재사용할 제품 명세가 필요할 때만 별도 Discovery에서 작성한다.
- 기존 OPAL 프로젝트는 `PROJECT.md` 문서 레지스트리로 기술 기준을 읽고 TRD를 기본 생략한다.
- 미니 태스크는 `RUN → PROVE → ACCEPT` 세 단계만 가진다.
- PM Agent는 설계·판단, Controller는 상태·예산·스케줄, Runner는 코드 변경, Verifier는 read-only 판정을 소유한다.
- MEMORY·brain은 미니 태스크에서 읽기만 하고 프로젝트 완료 및 허브 merge 뒤 한 번 반영한다.
- OPPB는 현행 OPPD를 교체하지 않고 **독립 Pilot으로 신설**한다. `//oppd`는 그대로 두고 `//oppb`를 새로 연다.
- 따라서 런타임 라우터·`--engine` 분기·v1 대비 성능 benchmark를 만들지 않는다. 회귀 시 복구는 "`//oppd`를 쓴다"로 끝난다.
- `opal-task-action-agent` 제거와 OPPD 폐기는 이 문서의 범위가 아니다. OPPB 실사용 판정 뒤 별도 정리 태스크가 소유한다.
- capability owner와 Verifier는 Supervisor가 관리하는 `opal-agent` headless attempt 채널로 실행한다.
- OPPB 프로젝트 전체는 OPAL 태스크 1건과 프로젝트 worktree 1개로 관리한다.

여기서 Lean은 **사용자와 미니 태스크가 마주하는 workflow 표면**을 뜻한다. OPPB는 안전한 공유 worktree
병렬 실행을 위해 현행 v1보다 큰 결정론적 runtime을 필요로 한다. 이 구현 복잡성을 숨기거나 “전체
구현량 감소”로 주장하지 않는다. Controller·Lease·Checkpoint·Evidence·Supervisor는 별도 도구 5개가
아니라 하나의 `oppb-runtime-tool` 패키지 안에서 경계가 분리된 subcommand/module로 구현한다.

## 2. Pilot 관계

OPPB는 기존 Pilot의 후속 버전이 아니라 **네 번째 프로젝트 Pilot**이다. 셋 다 살아 있으며 선택 기준이 다르다.

| Pilot | 진입점 | 대상 | 이 문서와의 관계 |
|---|---|---|---|
| OPPD | `//oppd` | 아이디어→product 라이프사이클. PRD·TRD 작성이 중심 | 존치. OPPB가 교체하지 않는다 |
| OPPL | `//oppl` | 목표·계약·백로그가 증거에 따라 반복 변경되는 수렴형 | 존치. 공용 attempt runtime만 공유 |
| OPPB | `//oppb` | **이미 확정된 실행 계약**을 capability 단위로 무인 소화 | 이 문서가 정의 |

`opal-oppd-v2-project-execution.md`는 OPPB 설계의 출발점이며 비교 기준으로 보존한다. OPPB는 v2의 안전
계약(lease·단일 Git writer·지식 1회 반영)을 유지하고 외부 단계·중복 문서·불필요한 에이전트 호출을 축소한다.

세 Pilot은 Controller를 공유하지 않고, process group·watchdog·결과 framing·attempt record 같은 실행 원시
기능만 `opal-agent`의 공용 attempt runtime에서 공유한다. 따라서 v2의 `//oppl` 폐기 결정은 OPPB에서
채택하지 않으며, OPPD 폐기도 이 문서가 결정하지 않는다.

### 2.1 어느 Pilot을 쓰는가

- 한 번의 설계 승인으로 목표·계약·백로그를 잠글 수 있고, capability 단위 수직 분할과 변경 소유권 분리가 가능하면 **OPPB**.
- 잠글 수 없고 증거에 따라 목표가 바뀌면 **OPPL**.
- 제품 명세(PRD·TRD) 작성부터 필요하면 **OPPD**, 또는 `opwt`로 명세를 먼저 만들고 OPPB로 실행한다.
- 단일 태스크로 끝나는 규모면 프로젝트 Pilot이 아니라 `//opd`·`//opds`다.

## 3. 현행 OPPD v1과 OPPB 비교

### 3.1 프로젝트 단계와 실행 주체

| 목적 | 현행 OPPD v1 | v1 실행 주체 | OPPB | OPPB 실행 주체 |
|---|---|---|---|---|
| 프로젝트 준비 | `PROJECT.md` 없으면 `opi` | OPPD PM·`opal-project-init` | 동일, 기존 OPAL이면 문서 레지스트리만 JIT read | OPPB Product Flow·PM Agent |
| 제품 정의 | PRD·TRD를 항상 작성·수정 | `opwt`·`opal-planning-agent`·`op-spec-validator` | PRD는 선택적 Discovery, 실행 계약은 INTENT | PM Agent, 필요할 때만 `opwt` |
| 기술 정의 | PRD와 함께 TRD 작성·승격 | `opwt`·`op-spec-validator`·사용자 | 기존 OPAL이면 관련 기술 문서 read, 신규 결정만 TRD delta | PM Agent·필요 시 read-only Evaluator·사용자 |
| 작업 분할 | WBS 작성 | PM 직접 | PROJECT-DESIGN과 `workgraph.json`에 DAG·계약·lease 선언 | Project Planner/Slicer 초안, PM 승인, Controller Tool schema 검증 |
| 실행 스케줄 | WBS 병렬 그룹 반복 | PM이 직접 디스패치·회수 | Ready queue 연속 스케줄링 | Controller Tool 결정, Runtime Supervisor 집행 |
| 개발 | 액션마다 PLAN→QA→TEST-SCENARIO→EXECUTE→VERIFY→TEST | `opal-task-action-agent`와 내부 전문 에이전트 | capability마다 RUN→PROVE | 신규 `opal-capability-agent`, 필요할 때만 기존 전문 executor |
| Git 격리 | 병렬 액션마다 별도 worktree·branch | PM·worktree-tool·action agent | 프로젝트 worktree 하나, 범위 lease | Scope Lease Tool·Runner·Checkpoint Tool |
| 결과 확정 | 액션 결과를 PM이 직접 검수 | PM | scope 검사·checkpoint·조건부 검증 | Checkpoint Tool·read-only Verifier |
| 통합 품질 | 병렬 그룹 merge 후 통합 테스트, 마지막 전체 확인 | PM·action agent·test agent | 계약 폐쇄 시 증분 검증, 최종 checkpoint 전체 검증 | Integration/Security/Convention Verifier |
| 완료 판정 | PM이 액션·문서 결과 종합 | PM·사용자 | 완료조건↔증거 기계 대응 | Acceptance Evaluator·PM Agent·사용자 |
| 지식 반영 | Phase와 CLOSE에서 history·brain 반영 가능 | PM·memory-tool·brain ingest | 프로젝트 허브 merge 뒤 한 번만 반영 | Project Knowledge Finalizer |
| 실행 감시 | PM 대화 재개로 결과 회수 | PM | process group·heartbeat·timeout 자동 회수 | Runtime Supervisor |

### 3.2 제거되는 중복

| 현행·v2 비용 | OPPB 처리 |
|---|---|
| 모든 실행에서 PRD·TRD 작성 | INTENT 필수, PRD·TRD 조건부 |
| PRD/TRD 검증을 위한 별도 validator 반복 | 문서가 실제 생성된 경우에만 검증 |
| WBS.md와 workgraph의 이중 상태 | `workgraph.json`이 기계 SSOT, PROJECT-DESIGN은 설계 설명만 소유 |
| 액션별 PLAN·QA·TEST·CLOSE 문서 | result·evidence 중심, DESIGN·TEST-SCENARIO 조건부 |
| 미니 태스크별 worktree·branch·merge | 프로젝트 worktree 하나 + scope lease + checkpoint |
| PM의 반복 상태 확인·재촉 | Supervisor가 자동 수확·재-tick |
| 미니 태스크별 MEMORY·brain 반영 | 프로젝트 완료 후 단일 batch |

## 4. OPPB의 에이전트·도구 책임

에이전트는 자연어 판단과 구현을 수행한다. 도구는 상태 전이와 파일·프로세스·Git 조작을 결정론적으로 집행한다.

| 주체 | 종류 | 수행 책임 | 금지 책임 |
|---|---|---|---|
| OPPB Product Flow | 스킬/오케스트레이터 | 진입점·선택적 Discovery·사용자 게이트·최종 경험 | 프로세스 직접 감시 |
| PM Agent | 루트 에이전트 | INTENT 확정·설계 승인·계약 변경·귀속 불명 실패 판단 | 작업 프로세스 수확·Git 조작·코드 구현 |
| Project Planner/Slicer | 서브에이전트 | PROJECT-DESIGN·미니 태스크 DAG·계약·완료조건 역인덱스 초안 | 사용자 승인·코드 구현·스케줄 집행 |
| Controller Tool | `oppb-runtime-tool` module | DAG·Ready queue·예산·상태·dispatch·Repair·deadlock 결정 | 자연어 설계·코드 수정 |
| Runtime Supervisor | `oppb-runtime-tool` 상주 process | `opal-agent` attempt 시작·heartbeat·timeout·종료 수확·tick 재호출 | 태스크 우선순위 판단 |
| `opal-agent` attempt runtime | 공용 실행 원시 기능 | process group·무출력 watchdog·terminal framing·자식 종료·exit code·attempt record | OPPB DAG·OPPL round 정책 |
| `opal-capability-agent` | capability owner 에이전트 | 하나의 비즈니스 기능을 UI·API·데이터·테스트까지 완성하고 결과 통합 | Git·공유 상태·MEMORY·brain 수정 |
| 전문 Executor | 조건부 자식 에이전트 | 같은 미니 태스크 안의 FE·BE·DB work item 구현 | 독립 태스크 상태·checkpoint·수용 판정 |
| Design Evaluator | 조건부 read-only 에이전트 | Critical 기술 결정·계약의 독립 검토 | 코드·문서 직접 수정 |
| Scope Lease Tool | `oppb-runtime-tool` module | Runner·Verifier의 tracked·ephemeral write, contract, runtime resource 충돌 검사·preimage 봉인 | 코드 수정 |
| Checkpoint Tool | `oppb-runtime-tool` module | 실제 변경 검사·ref 미변경 후보 commit·검증 snapshot·통과 후 branch 전진·부분 복구 | 코드 작성·충돌 임의 해결 |
| Evidence Tool | `oppb-runtime-tool` module | verifier evidence schema 검증·원자 저장·content hash 발급 | 테스트 실행·판정 변경 |
| Integration Verifier | read-only 에이전트 | 계약·영향·통합·전체 회귀 판정 | 코드 수정 |
| Security Verifier | read-only 에이전트 | 위험 변경과 최종 통합 보안 판정 | 코드 수정 |
| Convention Verifier | read-only 에이전트 | 변경 파일·최종 신규 위반 판정 | 코드 수정 |
| Acceptance Evaluator | read-only 에이전트 | 프로젝트 완료조건과 증거 대응 | 테스트 실행·코드 수정 |
| Project Knowledge Finalizer | 프로젝트 완료 후 에이전트/도구 조합 | 전체 결과에서 MEMORY·brain 후보 합성·허브 단일 반영 | 프로젝트 실행 중 지식 반영 |

PM 아래 PL Agent는 기본 생성하지 않는다. 독립 배포·별도 완료조건·독립 계약을 가진 실제 하위 프로젝트만 subgraph로 분리할 때 조건부로 둔다.

### 4.1 서브에이전트 실행 구조

```text
PM Agent
├─ Discovery Agent                    조건부 1회
├─ Project Planner/Slicer             프로젝트 설계 1회
├─ Design Evaluator                   Critical 설계만
├─ opal-capability-agent T01 사용자 관리 ─┐
│  ├─ BE Executor                    │
│  └─ FE Executor                    ├─ 비충돌 capability끼리 병렬
├─ opal-capability-agent T02 알림 설정 ───┘
├─ Integration/Convention/Security Verifier   조건별 병렬 read-only
├─ opal-capability-agent Repair attempt  실패 태스크만 새 attempt
├─ Acceptance Evaluator                프로젝트 완료 후보 1회
└─ Project Knowledge Finalizer         허브 merge 후 1회
```

- 하나의 미니 태스크 attempt는 하나의 `opal-capability-agent`가 RUN과 PROVE, 내부 결과 통합을 끝까지
  책임진다.
- 단일 profile로 충분하면 Runner가 직접 수행한다. UI·API·DB처럼 여러 전문 영역이면서 병렬 이득이
  분명하면 Runner는 같은 태스크 안에서 범위가 정해진 전문 Executor를 호출할 수 있다.
- 전문 Executor는 별도 미니 태스크·상태·checkpoint·완료조건을 갖지 않는다. Controller가 승인한
  work item lease 안에서만 작업하고 결과를 capability owner에게 반환한다.
- Runner가 하위 PL이나 범용 오케스트레이터를 생성하는 것은 금지한다. Runner·전문 Executor·전체
  headless process 상한은 §9.3의 독립된 세 값으로 집행한다.
- P0~P2의 Discovery·Project Planner/Slicer·Critical Design Evaluator는 아직 Controller run이 없으므로
  Product Flow가 기존 대화형 Agent 도구로 한 번씩 호출한다. 이 구간은 사용자 설계 게이트 앞의 bounded
  planning이며 무인 실행 보장의 대상이 아니다.
- P3 이후의 Verifier는 Runner의 자식이 아니라 Controller가 스케줄하고 Supervisor가 실행하는 형제
  read-only 서브에이전트다.
- Repair는 같은 대화를 반복 resume하지 않고 동일 task ID·남은 예산·압축 execution packet을 받은 새
  attempt Runner가 수행한다.
- Controller·Supervisor·Lease·Checkpoint·Evidence는 서브에이전트가 아니라 결정론적 런타임이다.
- P3 이후 capability owner·전문 Executor·Acceptance Evaluator·Verifier는 PM의 대화형 Agent 도구가
  아니라 Supervisor가 `opal-agent` headless attempt로 실행한다. 사용자 대면 세션은 OPPB Product
  Flow와 PM Agent만 소유한다.

### 4.2 신규 capability owner와 기존 OPAL 에이전트 재사용 매핑

OPPB는 capability owner 하나만 신규 에이전트로 만들고 나머지 전문·검증 역할은 기존 에이전트를
재사용한다. 현행 OPPD 전용인 `opal-task-action-agent`는 확장하지도, 호출하지도 않는다.

| OPPB 논리 역할 | 실제 재사용 에이전트 | 변경 방식 | 판정 |
|---|---|---|---|
| Discovery Agent | `opal-planning-agent` | PRD가 명시적으로 필요할 때만 기존 opwt 경로 호출 | 그대로 재사용 |
| Project Planner/Slicer | `opal-plan-agent` | `project-slice` profile과 구조화 입력·출력 계약 추가 | 확장 재사용·신규 profile 계약 |
| Mini-task Capability Owner | 신규 `opal-capability-agent` | RUN·PROVE·내부 work item 통합만 소유 | 신규 1종 |
| 범용 내부 work item | `opal-task-agent` | 선택한 단계 스킬과 승인된 work item lease만 실행 | 그대로 재사용 |
| FE work item | `opal-fe-agent` | 같은 task ID·FE lease로 실행 | 그대로 재사용 |
| BE work item | `opal-be-agent` | 같은 task ID·BE lease로 실행 | 그대로 재사용 |
| DB work item | `opal-db-agent` | 같은 task ID·DB lease로 실행 | 그대로 재사용 |
| Critical Design Evaluator | `opal-evaluator-agent` | design rubric profile | 확장 재사용 |
| 통합·E2E Verifier | `opal-test-agent` | 기존 E2E·BE·FE mode와 evidence schema 연결 | 확장 재사용 |
| 문서·설계 QA | `opal-task-qa-agent` | Critical/조건부 문서 검토에만 호출 | 그대로 재사용 |
| Security Verifier | `opal-security-checker` + `op-gc-security` | agent role은 유지, 호출 adapter와 Evidence Tool이 scope hash·evidence 연결 | agent 재사용·스킬/adapter 확장 |
| Convention Verifier | `opal-convention-checker` + `op-gc-convention` | agent role은 유지, 호출 adapter와 Evidence Tool이 scope hash·evidence 연결 | agent 재사용·스킬/adapter 확장 |
| Acceptance Evaluator | `opal-evaluator-agent` | `acceptance` phase와 구조화 evidence 입력 추가 | 확장 재사용 |
| Project Knowledge Finalizer | `opal-task-agent` + 신규 finalize 단계 스킬 | 기존 memory·brain 도구를 프로젝트 batch로 호출 | 에이전트 재사용·스킬 신규 |

`opal-task-action-agent`의 직접 실행 호출자는 현행 OPPD이며, OPPD가 존치하는 동안 이 에이전트도 그대로
살아 있다. **OPPB는 이 에이전트를 호출하지 않을 뿐 제거하지 않는다.** 제거는 §4.4가 정한 OPPD 폐기 판정
뒤의 별도 정리 태스크가 소유한다. 그 태스크는 `opal-loop-action-agent`와 `opal-sdd-action-agent`가 이 파일의
입력·검증 구조를 준거로 참조하는 점을 함께 처리한다 — 공통 계약을 owner 단계 스킬 또는 harness reference로
이관하고 두 참조를 새 owner로 바꾼 뒤, 에이전트 목록·프로젝트 문서·설치 및 배포 레지스트리의 활성 항목을
회수한다. 과거 brain·태스크 기록의 역사적 언급은 고치지 않는다.

`opal-loop-action-agent`와 `opal-sdd-action-agent`는 각자 OPPL·SDD 실행 책임이 있으므로 어느 경우에도
이번 작업으로 제거하지 않는다. OPPB는 이들을 Runner로 호출하지 않고, 공통 실행·검증 원칙만 owner reference로
공유한다.

### 4.3 `opal-capability-agent` 계약

신규 에이전트는 오케스트레이터가 아니라 하나의 capability 결과에 책임지는 얇은 owner다.

| 입력 | 필수 내용 |
|---|---|
| identity | `task_id`, `attempt_id`, `capability_id` |
| contract | `acceptance_cluster`, `business_rules`, 동결된 외부 contract revision |
| scope | execution packet 경로, write·contract·resource lease receipt |
| execution | profile, task·attempt budget, 허용 전문 Executor 목록 |

| 출력 | 필수 내용 |
|---|---|
| result | `completed`, `blocked`, `failed`와 실패 지문 |
| changes | work item별 changed files·hash·lease ID |
| proof | 실행 명령·exit code·provisional test evidence |
| coordination | 호출한 전문 Executor와 결과 통합 여부 |
| knowledge | 프로젝트 완료 때 검토할 후보만 반환 |

행동 계약은 다음으로 제한한다.

1. RUN과 PROVE를 한 dispatch에서 수행한다.
2. 작은 capability는 직접 구현하고, 여러 전문 영역의 병렬 이득이 분명할 때만 승인된 FE·BE·DB·task
   agent를 호출한다.
3. PLAN·QA·TEST·CLOSE 문서 파이프라인과 자체 PM 게이트를 만들지 않는다.
4. Git·Controller state·MEMORY·brain을 수정하지 않는다.
5. 실패 시 자체 대화를 무한 resume하지 않고 구조화 result를 반환한다.
6. ACCEPT와 최종 판정은 외부 Checkpoint Tool·Verifier·Controller에 맡긴다.

### 4.4 신규 Pilot 출시와 복구 계약

OPPB는 현행 OPPD를 교체하지 않는다. 두 구현을 **런타임에서 고르는 장치**를 만들지 않는다는 v2의 판단은
유지하되, 그 해법을 "전면 교체 + tag revert"가 아니라 **별개 진입점 공존**으로 바꾼다. `--engine` 같은
공개 선택 옵션이나 라우터는 여전히 만들지 않는다. 하나의 Pilot 안에 두 경로를 넣지 않을 뿐이다.

1. OPPB는 `opal-pilot-project-build`(alias `oppb`)라는 신규 스킬로 출시한다. `//oppd`·`//oppl`의 동작·상태·테스트는 바이트 수준으로 무변경이다.
2. 구현은 별도 개발 worktree·branch에서 수행한다. 현행 자산 동결 tag는 일반 릴리스 기준선으로만 남기고 benchmark 재현 용도로 쓰지 않는다.
3. 수용 판정은 v1과의 비교가 아니라 §13의 **절대 기준**으로 한다 — 무인 실행, lease 비충돌, Git 단일 writer, cache 정확성, runtime 안전성, 품질 게이트.
4. 중대한 결함이 발견되면 flag를 내리거나 revert하지 않는다. `//oppd`를 그대로 쓰고 `//oppb`만 수정한다.
5. `opal-task-action-agent`는 OPPD의 실행 에이전트로 계속 살아 있다. OPPB는 이를 호출하지 않을 뿐 제거하지 않는다.
6. OPPD 폐기 판정 시점을 지금 고정한다 — **OPPB로 실제 프로젝트 2건을 완주하면** OPPD를 deprecated로 표시하고, 3건째부터 신규 사용을 중단한 뒤 별도 정리 태스크에서 자산·레지스트리를 회수한다.

이 방식은 라우팅·상태·테스트를 이중으로 유지하는 비용을 피하면서, 복구 경로를 tag 기반 revert보다 단순하고
확실하게 만든다. 잃는 것은 "OPPB가 OPPD보다 빠르다"는 정량 증거이며, 그 판단은 실사용 결과가 대체한다.

### 4.5 프로젝트 태스크와 산출물 소유권

하나의 OPPB 프로젝트 실행은 하나의 OPAL 태스크다. 허브 allocator가 번호를 한 번 발급하고 기존
`worktree-tool create`로 `.opal-worktrees/task_{NNN}` 프로젝트 worktree 하나를 만든다. 미니 태스크에는
별도 OPAL 번호·태스크 폴더·worktree·branch를 만들지 않는다.

| 산출물 | 위치 | Git | 단일 writer | 역할 |
|---|---|---|---|---|
| 프로젝트 태스크 캡슐 | `<task_root>/tasks/{NNN}-oppb-{name}/` | 추적 | OPPB Product Flow·state-tool | 사용자 산출물과 프로젝트 단계 상태 |
| `INTENT.md` | 프로젝트 태스크 캡슐 | 추적 | PM Agent | 승인된 목표·범위·완료조건·예산 |
| `PROJECT-DESIGN.md` | 프로젝트 태스크 캡슐 | 추적 | PM Agent | 설계·슬라이스 근거·통합 전략 |
| `.opal/oppb-environment.json` | 프로젝트 root | 추적 | Environment Probe Tool | 관측된 미추적 쓰기·cache adapter·runtime resource·입력 hash를 봉인한 프로젝트 실행 profile |
| `state.json`·`STATE.md` | 프로젝트 태스크 캡슐 | 추적 | state-tool | P0~P5 프로젝트 파이프라인 상태·결정 저널 |
| OPPB `pipeline.json` | `opal-pilot-project-build/references/` | 추적 | 프레임워크 소스 | P0~P5 행과 게이트 정의 |
| run root | `<allocator_root>/.opal-runs/<run_id>/` | 미추적·ignore | `oppb-runtime-tool init` | 재시작 가능한 실행 운영 자료 |
| cache root | `<allocator_root>/.opal-cache/oppb/` | 미추적·ignore | `oppb-runtime-tool cache` | run 간 재사용하는 immutable source·dependency·build CAS object와 generation receipt |
| `workgraph.json` | run root | 미추적 | Controller Tool | P3 내부 DAG·미니 태스크·계약·예산·상태 SSOT |
| `acceptance.json` | run root | 미추적 | Controller Tool | 프로젝트 완료조건·기여 태스크·증거 역인덱스 |
| `attempts/<task>/<attempt>/execution-packet.json` | run root | 미추적 | Controller Tool | dispatch 시점 가변 입력 |
| `attempts/<task>/<attempt>/result.json` | run root | 미추적 | attempt wrapper | 실행 결과·실제 변경·비용·실패 지문 |
| `environment-deltas/<fingerprint>.json` | run root | 미추적 | Environment Probe Tool | late discovery 1회용 명령·출력·임시 lease 확장 receipt |
| `evidence/<scope>/<evidence-id>.json` | run root | 미추적 | Evidence Tool | schema 검증된 불변 검증 증거 |
| `verify-sandboxes/<candidate-id>/` | run root | 미추적·임시 | Checkpoint Tool·환경 adapter | 후보 commit의 격리된 검증 source·candidate-private build-cache overlay |
| `events.jsonl`·attempt records | run root | 미추적 | `opal-agent` attempt runtime | PID·PGID·heartbeat·종료·timeout·결과 framing |
| `DONE.md`·evidence manifest | 프로젝트 태스크 캡슐 | 추적 | Controller Tool | acceptance 결과에서 결정론적으로 렌더한 최종 결과·증거 hash·남은 위험 |

`state.json`은 프로젝트 바깥 단계만 소유하고 `workgraph.json`은 P3 내부 상태만 소유한다. Controller는
`state.json`을 직접 쓰지 않는다. P0~P5 전이는 Product Flow가 `state-tool`을 호출하고, 세부 태스크
전이는 Controller가 revision lock 아래 `workgraph.json`만 갱신한다.

미추적 run root는 worktree 회수와 함께 삭제하지 않으며 DONE의 manifest가 경로·content hash를
가리킨다. `oppb-runtime-tool init`이 allocator Git repository의 `.git/info/exclude`에 `.opal-runs/`와
`.opal-cache/oppb/`를 멱등 등록하고 실제 ignore 판정을 확인하지 못하면 run 시작을 거부한다. 별도 보존 정책이 만료시키기
전까지 재시작과 사후 감사에 사용한다. PM Agent는 DONE을 직접 쓰지 않고 최종 사용자 보고만 작성한다.

프로젝트 worktree 안의 Git writer는 Checkpoint Tool 하나다. Runner는 같은 작업본에서 서로 다른 lease를
수정하지만 commit·index·HEAD를 건드리지 않는다. Checkpoint Tool은 lease 경로만 후보 tree에 넣는다. P5의 기존
`worktree-tool finalize` 전에는 active lease 0, 미처리 result 0, checkpoint 밖 dirty source 0,
MEMORY·brain diff 0을 추가 gate로 확인한다. `worktree-tool`의 create·remove·merge 소유권 구조는 바꾸지
않고 이 project-run pre-finalize guard와 receipt 확인만 확장한다.

ACCEPT 전체를 전역 직렬화하지 않는다. candidate 생성은 ref를 바꾸지 않는 임시 index 작업이라 서로
다른 lease끼리 병렬 수행하고, project branch를 전진시키는 publication 구간만 짧은 전역 lock으로
직렬화한다. Checkpoint Tool은 candidate 생성 시점의 accepted project head를 parent로 삼고 별도 임시
index에 해당 lease 경로만 올려 `commit-tree` 후보 commit을 만든다. 이때 project branch ref, HEAD와 공유
index는 움직이지 않는다. receipt에는 parent·candidate·tree·lease path hash·writer identity를 기록한다.

Checkpoint Tool은 최초 generation 또는 cache 복구 때 `git archive <candidate_commit>`으로 run root의 임시
검증 snapshot을 만든다. snapshot은 `.git`·branch·OPAL task가 없는 source 복사본이다. 환경 adapter는 봉인된
`.opal/oppb-environment.json`의 bootstrap 계약으로 의존성을 준비한다. 환경 변수와 fixture는 profile에 선언된
값만 주입하고 secret 원문은 복사하지 않는다.

매 capability마다 source 전체 복사와 dependency bootstrap을 반복하지 않는다. source·dependency·build
cache를 서로 다른 수명주기로 관리한다. 세 계층은 cache root의 content-addressed immutable object로
저장하고, mutable 작업은 candidate별 overlay에서만 수행한다. cache object의 보존과 DONE의 감사 기록은
분리한다. DONE은 object hash·tool/config/input manifest·생성 시각만 기록하며 object 존재를 영구 요구하지
않는다. cache miss이면 같은 입력에서 재생성할 수 있어야 한다.

cache root는 allocator별 기본 soft cap `10 GiB`와 최소 여유 공간 `max(5 GiB, filesystem 10%)`를 함께
집행한다. `.opal/oppb-environment.json.cache_policy`로 더 작게 제한하거나 명시 승인 후 확대할 수 있다. active run·실행 중
candidate·publication 대기 node만 lease로 pin한다. closed run의 node는 기본 warm retention 7일 뒤
evictable이며, 그 전에도 soft cap 또는 최소 여유 공간에 걸리면 last-access receipt 기준 LRU로 제거한다.
GC는 새 cache object 쓰기 전과 run admission 때 자동 실행하고 명시 `cache gc`도 제공한다. pin되지 않은
node를 모두 제거해도 최소 여유 공간을 확보하지 못하면 warm cache를 비활성화한 격리 실행으로 강등하며,
그 실행 공간도 확보할 수 없으면 `disk_budget_exceeded`로 구조화 blocked한다. evidence·DONE·source code는
cache GC 대상이 아니다.

| cache | key·lineage | 갱신 |
|---|---|---|
| source base | accepted commit tree + generation | 최초·복구 시 `git archive`, 이후 parent→accepted `diff-tree`의 변경·삭제·mode만 새 generation에 적용 |
| dependency environment | lockfile+toolchain+bootstrap command hash | 환경 계약이 바뀔 때만 재생성 |
| build cache | build tool/version+config+dependency key+source input manifest+lineage | candidate-private overlay를 fork하고 검증 통과한 모든 overlay를 CAS branch generation으로 봉인 |

source base generation은 이미 materialize된 직전 generation에서 Git blob·mode·삭제 목록만 증분 반영한다.
매 ACCEPT마다 새 tree hash라는 이유로 전체 `git archive`를 반복하지 않는다. 결과 manifest의 Git tree
entries가 candidate tree와 다르면 해당 generation을 폐기하고 전체 archive로 복구한다.

`tsbuildinfo`, `.next/cache`, Vite cache, pytest cache, `GOCACHE`, `CARGO_TARGET_DIR` 등 증분 build cache는
snapshot 로컬 일회성 산출물로 버리지 않는다. candidate별 writable overlay에서만 갱신하고 검증 실패 시
폐기한다. 같은 parent에서 병렬 검증을 통과한 candidate가 여러 개면 승자 하나만 남기지 않는다. 각 overlay를
parent cache·candidate source input manifest·검증 receipt에 연결된 immutable CAS node로 모두 보존한다.

accepted head는 단일 build-cache 파일을 소유하는 대신 재사용 가능한 cache DAG의 head set을 기록한다.
stale sibling을 새 project head에 다시 올릴 때 그 sibling 자신의 검증된 cache node와 현재 accepted cache
node 중 input 일치가 가장 크고 적용할 Git delta가 가장 작은 seed를 결정론적으로 선택한다. `replayable`
adapter는 seed의 candidate-private overlay에 intervening accepted source delta를 반영하고 build tool의 정상
incremental 검사를 다시 실행한다. cache 파일끼리 byte merge하지 않는다. adapter conformance test가 입력
변경 검출을 보장하지 못하는 opaque cache는 `non_reusable`로 분류해 해당 명령만 cold 실행한다. source·config·
dependency closure가 교차하더라도 전체 cache를 일괄 폐기하지 않고 adapter가 선언한 영향 shard만
무효화한다. 안전한 shard 또는 replay 경계를 증명하지 못하면 그 cache만 재사용하지 않는다.

copy-on-write를 지원하지 않는 플랫폼은 동일 manifest를 보존하는 hardlink-break 또는 파일 복사를
사용한다. 어느 방식이든 여러 candidate가 하나의 mutable build cache를 동시에 쓰는 것은 금지한다.
무실행 exact cache hit는 source·dependency·build manifest hash가 모두 일치할 때만 허용한다. source가
달라진 seed 재사용은 `replayable` adapter가 새 overlay에서 build를 실행하고 새 output manifest를 검증하는
경우에만 허용한다.

dependency environment는 CAS에 두고 운영체제가 보장하는 read-only mount 또는 쓰기 불가 권한으로 Runner와
Verifier에 노출한다. 생성 시에는 전체 manifest를 한 번 만들되 attempt마다 10만 개 이상의 파일을 재탐색하지
않는다. 반복 검사는 lockfile·toolchain·bootstrap hash, CAS object ID, 설치 완료 receipt와 read-only mount·권한
identity로 한다. top-level mtime만으로는 깊은 파일 변조를 검출하지 못하므로 단독 불변식으로 사용하지 않는다.
read-only를 보장할 수 없는 플랫폼에서는 dependency environment도 candidate-private copy 또는 overlay를 사용하며
mutable directory를 여러 attempt가 공유하지 않는다.

Verifier 실행 전 Scope Lease Tool이 candidate ID에 귀속된 검증용 runtime resource lease를 발급한다.
포트·DB schema 또는 namespace·service·queue·browser profile이 실행 중 Runner·다른 Verifier와 겹치면
검증을 시작하지 않고 pending으로 둔다. Evidence에는 candidate commit, snapshot manifest hash,
dependency lock hash와 resource lease ID를 함께 기록한다.

모든 검증이 통과한 경우에만 Checkpoint Tool이 parent가 여전히 project branch head인지 확인하고
candidate commit으로 원자적 fast-forward한다. parent가 바뀌었으면 candidate commit의 publication 자격은
stale로 폐기하고 새 parent에서 다시 만든다. 검증된 build-cache CAS node는 폐기하지 않고 §4.5의 cache DAG
seed 후보로 유지한다. 새로 accepted된 변경이 candidate의 `verification_closure`인 tracked read path·contract·
lockfile·runtime setup과 교차하지 않으면 Evidence Tool이 비교 증거를 발행하고 기존 검증을 재사용한다.
교차하거나 closure가 불완전하면 영향 테스트만 새 candidate snapshot에서 재실행한다. ref 전진 직후 공유
index는 승인된 lease 경로만 candidate tree와 맞춘다. 이 짧은 Git metadata
전이는 Checkpoint Tool receipt 아래 수행하며 다른 lease의 index entry·worktree 파일은 건드리지 않는다.
실패하면 candidate를 폐기할 뿐 branch·HEAD·공유 index를 되돌리지 않는다. capability 변경은
해당 lease의 Repair 입력으로 그대로 두며, 폐기 시에도 path-scoped preimage 복구만 허용하고
`reset --hard`·worktree 전체 restore를 금지한다. 마지막으로 검증 resource lease와 snapshot을 회수한다.
이는 미니 태스크 worktree나 branch를 추가하는 구조가 아니다.

ACCEPT 검증 계획도 capability마다 동일한 3개 에이전트를 반복하지 않는다. scope·candidate·evidence schema
검사는 항상 결정론적 도구가 실행한다. 변경 파일 컨벤션 검사는 항상 수행하되 동일 snapshot에서 경량
검사로 실행한다. Integration Verifier는 수용 명령 또는 producer-consumer 계약이 닫힐 때만, Security
Verifier는 위험 표지가 있을 때만 호출한다. 필요한 Verifier들은 resource lease가 분리되면 병렬 실행한다.
전체 회귀·통합 보안·전체 컨벤션은 P4에서 한 번 수행한다.

### 4.6 공용 attempt runtime과 Pilot별 제어

`opal-agent`는 OPPL과 OPPD가 공통으로 쓰는 다음 실행 원시 기능의 단일 owner다.

- process group 생성과 전체 자식 종료 회수
- stdout이 없어도 작동하는 hard timeout·heartbeat watchdog
- terminal result·자식 종료·root exit code의 결합 판정
- attempt ID·PID·PGID·시간·비용·실패 지문을 기록하는 attempt 1건 단위의 원자 record primitive
- 재시작 시 살아 있는 process 재부착 또는 고아 정리 판정

OPPL의 `oppl-runtime-tool`은 round·resume·수렴 상한을, OPPB Controller는 DAG·lease·Repair·프로젝트
예산을 각각 소유한다. 양쪽은 공용 attempt API와 schema를 소비하되 상대 Pilot의 상위 상태기계를
복제하거나 호출하지 않는다. Pilot 도구는 attempt ID와 집계 상태·상한 카운터만 보유하고 PID·PGID·heartbeat·
terminal result 원문을 중복 저장하지 않는다. 현행 `opal-agent`의 무출력 watchdog과 종료 framing 결함
해결은 OPPB Runner 구현보다 앞선 선행 조건이다.

#### Supervisor 실행 모델

P2 사용자 승인과 workgraph 초기화가 끝나면 Product Flow는 `oppb-runtime-tool start <run_id>`를 한 번
호출한다. 이 명령은 run 전용 Supervisor process를 시작하고 PID·시작 fingerprint·lock receipt를 반환한다.
Supervisor는 대화 세션과 독립적으로 다음 event loop를 돈다.

```text
run lock 획득
→ 미수확 attempt·lease 복구
→ now 사건을 명시 입력으로 controller tick
→ 반환된 launch·verify·checkpoint·cancel 명령 집행
→ 자식 종료·heartbeat·timeout·결정 사건 대기
→ 사건 기록 후 다시 tick
```

Supervisor는 `awaiting_decision`, `awaiting_merge`, `closed`, 복구 불가능한 `blocked`에서만 안정적으로
멈춘다. 사용자 결정 뒤 Product Flow가 decision receipt를 기록하고 `resume <run_id>`를 호출하면 같은
상태에서 재시작한다. process가 비정상 종료되면 다음 `start/resume`가 run registry와 attempt records를
읽어 살아 있는 process 재부착·종료 결과 수확·고아 판정을 먼저 수행한다. 동일 run의 두 번째 Supervisor는
`flock`으로 거부한다. PM 대화 재개나 상태 확인 메시지는 tick을 전진시키는 조건이 아니다.

## 5. OPPB 프로젝트 단계

### P0. ENTRY & CONTEXT

| 항목 | 내용 |
|---|---|
| 실행 주체 | OPPB Product Flow·PM Agent |
| 보조 도구 | `opi`, PROJECT 문서 레지스트리 loader |
| 동작 | OPAL 프로젝트 여부·프로젝트 태스크 번호·단일 worktree·기존 문서·사용자 입력 충분성 판정 |
| 문서 | 신규 OPAL이면 `PROJECT.md`; 모든 실행은 프로젝트 태스크 캡슐과 P0~P5 `state.json` 생성 |
| 종료 조건 | 프로젝트 컨텍스트와 결측 정보가 식별됨 |

기존 OPAL 프로젝트에서는 `PROJECT.md`가 등록한 현재 범위 관련 문서만 읽는다. `docs/` 전체를 읽거나 환경·컨벤션을 새 TRD에 복사하지 않는다.

### P1. INTENT

| 항목 | 내용 |
|---|---|
| 실행 주체 | PM Agent |
| 조건부 주체 | 재사용할 제품 명세가 필요할 때만 `opwt`·planning agent |
| 사용자 역할 | 목표·제외 범위·완료조건·비가역 제약 승인 |
| 문서 | `INTENT.md`; 조건부 외부 `PRD.md` |
| 종료 조건 | 실행 목표·범위·완료조건·예산이 명확함 |

PRD가 있으면 INTENT는 requirement ID만 선택한다. PRD가 없으면 사용자 입력을 직접 INTENT로 정규화한다.

### P2. PROJECT DESIGN & SLICE

| 항목 | 내용 |
|---|---|
| 초안 작성 | Project Planner/Slicer 서브에이전트 |
| 승인·판단 | PM Agent |
| 조건부 검토 | Critical 결정만 Design Evaluator |
| 기계 검증 | Controller Tool |
| 문서 | `PROJECT-DESIGN.md`, `workgraph.json`, `acceptance.json`, `.opal/oppb-environment.json`; 조건부 `TRD.md` delta |
| 종료 조건 | DAG·계약·완료조건 역인덱스·probe로 봉인한 병렬 lease 범위가 유효함 |

TRD는 greenfield의 기술 기준 또는 기존 SSOT에 없는 중대한 기술 결정을 승인받을 때만 작성한다. 승인 후 현재 상태는 ARCHITECTURE·SECURITY·CONVENTIONS 등 기술 SSOT가 소유한다.

#### P2.1 미니 태스크 슬라이싱 기준

슬라이스의 기본 단위는 **동일한 비즈니스 개념·변경 이유·정책을 공유하며 사용자가 끝까지 사용할 수
있는 하나의 응집된 capability**다. 하나의 capability에는 여러 사용자 동작과 여러 내부 계약이 포함될
수 있다. 파일 수·레이어 수·API endpoint 수는 1차 분할 기준으로 사용하지 않는다.

#### 병렬 sibling 슬라이스의 선행 조건

별도 미니 태스크로 병렬 실행하려면 두 capability의 **변경 소유권이 완전히 분리**돼야 한다. 공통
프로젝트 문서·기존 코드·동결된 interface를 함께 읽는 것은 허용하지만, 동시에 바꾸거나 배타적으로
점유하는 집합에는 교집합이 없어야 한다.

| 소유권 축 | 병렬 허용 조건 |
|---|---|
| 추적 코드·테스트 | `tracked_write_set(A) ∩ tracked_write_set(B) = ∅` |
| Git 미추적 산출물 | `ephemeral_write_set`이 서로 다르거나 공유 불변·배타 lease 정책이 있음 |
| 계약 | 양쪽이 같은 contract revision을 동시에 변경하지 않음. 공유 계약은 실행 전에 동결 |
| 비즈니스 규칙 | 같은 정책 결정이나 acceptance ID를 공동 소유하지 않음 |
| 실행 자원 | DB schema·port·service·fixture·queue가 분리되거나 namespace 격리됨 |
| 전역 산출물 | lockfile·migration order·generated index·global config 동시 변경 없음 |
| 복구 | A를 preimage로 되돌려도 B의 파일·계약·증거가 바뀌지 않음 |

이 조건을 하나라도 증명할 수 없으면 병렬 sibling 미니 태스크로 분할하지 않는다. 같은 capability로
합치거나, capability 내부의 순차 work item으로 둔다. 크기 때문에 반드시 나눠야 한다면 별도 태스크로
남길 수 있지만 Controller가 순차 실행하며 `parallel_eligible: false`로 기록한다.

| 기준 | 슬라이스 조건 | workgraph 필수 표현 |
|---|---|---|
| 비즈니스 응집성 | 같은 대상·용어·정책·변경 이유를 공유하는 기능 묶음 | `capability_id`, `business_rules` |
| 수직 완결성 | 필요하면 UI·API·데이터·테스트를 함께 포함해 실제 사용 가능 | `acceptance_ids`, user journeys |
| 수용 묶음 | 하나의 capability를 증명하는 여러 시나리오 허용 | `acceptance_cluster` |
| 외부 계약 경계 | 다른 capability가 의존하는 계약만 태스크 간 edge로 노출 | `produces`, `consumes` |
| 변경 소유권 | 다른 병렬 capability와 분리 가능한 추적 쓰기 범위와 미추적 쓰기 힌트 | `tracked_write_set`, `ephemeral_write_hints`, `read_set` |
| 독립 검증 | capability 전체를 끝까지 판정하는 명령·시나리오 존재 | `verify_commands`, evidence type |
| 실행 자원 | DB·port·service·generated file 충돌을 선언 가능 | `runtime_resources` |
| 전문성 | capability owner와 필요한 내부 전문 work item 식별 | `runner_profile`, `work_items` |
| 예산 | 한 capability task의 context·시간·비용 상한 안에서 완료 가능 | `task_budget`, `attempt_budget` |
| 복구 | 실패 시 다른 태스크를 되돌리지 않고 범위 복원 가능 | `preimage_scope`, rollback rule |

workgraph에는 각 sibling pair의 ownership 교집합 검사 결과와 `parallel_eligible` 근거를 저장한다.
예상 범위는 dispatch 전 admission 기준이고, Runner 종료 후 실제 changed files·contract delta·resource
usage로 다시 검사한다. 실제 교집합이 발견되면 두 결과를 checkpoint하지 않고 `scope_violation`으로
중단한다.

Project Planner/Slicer는 여섯 소유권 축과 실행·검증 명령을 선언하되, 전이 의존 도구의 모든 미추적
쓰기 경로를 미리 안다고 가정하지 않는다. Slicer의 `ephemeral_write_hints`는 probe 입력일 뿐 최종 lease
계약이 아니다. Controller가 기계적으로 lease를 발급하는 집합은 tracked write·probe가 봉인한 ephemeral
write·contract·runtime resource 세 가지다. business rule·acceptance는 workgraph의 논리 소유권 ID
교집합으로 검사하고, global output은 실제 파일이면 write set에, 생성기·순서 자원이면 runtime resource에
반드시 다시 표현한다. schema 누락·교집합·표현 불가능은 dispatch 거부다. 의미상 동일한 정책인지
기계적으로 판정할 수 없는 경우 PM Agent가 근거를 확인하고 병렬 금지 또는 재슬라이스한다. 따라서
“중복 없음”의 증거는 Slicer의 선언, Environment Probe 결과, Controller pairwise 검사와 PM 경계 판정
receipt를 함께 뜻한다.

다음이면 **분할한다**.

- 서로 다른 비즈니스 대상·변경 이유·정책을 가짐
- 한 부분이 없어도 나머지가 독립적으로 사용자 가치를 제공함
- 독립 배포·승인·rollback이 필요함
- 보안·migration처럼 위험과 검증 경계를 분리해야 함
- 일부만 실패했을 때 독립적으로 재실행할 가치가 있음
- capability task 예산 또는 context 한계를 넘을 것으로 예상됨

다음이면 **합친다**.

- 같은 엔티티·용어·권한·validation 정책을 공유함
- API와 그 API만을 소비하는 화면처럼 함께 있어야 사용 가능한 수직 기능임
- 동일 엔티티의 CRUD가 같은 정책·화면 흐름·테스트 fixture를 재사용함
- helper·type·내부 refactor처럼 capability 내부 구현일 뿐 단독 수용 가치가 없음
- 같은 파일과 내부 계약을 반드시 연속 수정함
- P2에서 Project Planner/Slicer가 추정한 setup·조정·검증 비용이 실제 구현 예상시간의 20%를 넘고 PM이
  그 추정 근거를 승인함
- 분리하면 양쪽 execution packet에 같은 코드 문맥을 대부분 중복 주입해야 함

예를 들어 일반적인 사용자 관리라면 다음이 기본 슬라이스다.

```text
T01 사용자 관리 capability
  - 사용자 조회·생성·수정·삭제 정책
  - 사용자 CRUD API
  - 관리 화면과 입력 검증
  - 단위·계약·화면 수용 테스트
```

API와 화면은 이 태스크의 내부 work item이지 별도 미니 태스크가 아니다. 다만 삭제가 법적 보존·승인
workflow를 가지거나, 대량 가져오기가 별도 운영·성능·rollback 경계를 가지면 그 부분만 독립 capability로
분리한다.

두 태스크가 병렬로 실행되려면 다음을 모두 만족해야 한다.

1. DAG 선후 의존 없음
2. `tracked_write_set`과 mutable `ephemeral_write_set` 중복·포함 관계 없음
3. capability 사이의 변경 중인 외부 producer-consumer 계약 공유 없음
4. `runtime_resources` 중복 없음
5. 전역 formatter·schema migration·lockfile·generated index 작업 없음

병렬 조건을 만족하지 않는다고 반드시 하나로 합치지는 않는다. 독립 완료 결과는 유지하되 Controller가
순차 실행한다.

#### P2.2 ENVIRONMENT PROBE & SEAL

병렬 dispatch 전에 `oppb-runtime-tool probe`가 P0에서 수집하고 P2에서 확정한 bootstrap·build·test·검증
명령을 격리된 probe snapshot에서 하나씩 단독 실행한다. probe는 다음을 관측한다.

- Git untracked·ignored 생성·수정·삭제 경로
- build cache와 dependency environment의 실제 위치·도구 버전·설정 입력
- port·DB·service·queue·browser profile 등 실행 자원
- 환경 변수로 재지정 가능한 출력과 고정 위치 출력

Environment Probe Tool은 관측 결과에 `shared_immutable`, `attempt_namespaced`, `exclusive` 정책과 adapter를
배정하고 `.opal/oppb-environment.json`에 command/config/lockfile/toolchain input hash와 함께 원자적으로
봉인한다. 여기서 신선도를 판정하는 입력 hash는 repository tree 전체가 아니라 **실행 command 정의,
관련 build/test config, lockfile, toolchain identity와 bootstrap 정의**만 포함한다. 일반 source ACCEPT만으로
profile을 stale 처리하지 않는다. Controller는 profile이 없거나 이 한정 입력 hash가 현재 값과 다르면 병렬
dispatch를 거부한다.
이 파일은 capability Runner의 write lease가 아니라 Controller maintenance lane이 소유한다. 최초 봉인은 P3
전에 수행하고, 실행 중 갱신은 영향 subgraph의 active lease가 0인 상태에서만 후보 checkpoint에 포함한다.

greenfield처럼 P2 시점에 명령이나 build 설정 자체가 아직 없으면 최소 환경 bootstrap capability 하나만
exclusive로 먼저 accepted한다. 그 직후 probe를 실행하고 profile을 봉인한 뒤 나머지 병렬 dispatch를
연다. 실행 중 lockfile·build config·toolchain 설정을 바꾸는 capability도 별도 태스크를 강제하지 않는다.
그 capability가 `environment_mutation` 배타 lease를 얻어 단독 실행하고, accepted 직후 영향 cache를
무효화한 뒤 delta probe와 profile 재봉인을 완료할 때까지 하류 dispatch만 정지한다. 이 비용과 병렬 손실은
benchmark의 공유 모듈 fixture에서 반드시 측정한다.

#### Git 미추적·ignore 산출물 계약

`node_modules`, `.venv`, `dist`, `.next`, `coverage`, `__pycache__`, compiler cache처럼 Git diff에 나타나지
않는 경로도 쓰기 소유권이다. P2.2 probe가 각 실행·검증 명령의 실제 미추적 출력 경로와 다음 정책 중
하나를 `ephemeral_write_set`으로 봉인한다.

| 정책 | 처리 |
|---|---|
| `shared_immutable` | P3 시작 전에 한 번 준비하고 lockfile hash를 봉인한 뒤 Runner 쓰기 금지 |
| `attempt_namespaced` | run root의 attempt별 경로로 `TMPDIR`·cache·build output을 재지정 |
| `exclusive` | 도구가 출력 위치를 바꿀 수 없을 때 해당 ignored 경로에 배타 lease, 병렬 실행 금지 |

예를 들어 dependency download cache는 `shared_immutable`, `.next`·`dist`·coverage는 가능하면
`attempt_namespaced`, 위치 변경이 불가능한 생성기는 `exclusive`다. Python은
`PYTHONPYCACHEPREFIX` 또는 bytecode 비활성화로 attempt 경계를 지킨다.

cache adapter 계약과 공용 conformance fixture는 Work item 그룹 G3의 runtime 구현자가 작성한다. Environment Probe
Tool은 P2.2에서 선택된 adapter마다 `oppb-runtime-tool cache conformance`를 실행해 clean input·단일 source
delta·config delta·dependency delta·병렬 overlay·stale seed를 검증하고 evidence를 남긴다. tool version이나
adapter config hash가 바뀌면 다시 실행한다. 입력 변화 검출과 overlay 격리를 증명하지 못한 adapter는
자동으로 `non_reusable`이 되며 cache 없이 실행한다.

Scope Lease Tool은 tracked diff뿐 아니라 봉인된 ignored root를 검사한다. `attempt_namespaced`와 `exclusive`
경로는 사전·사후 manifest를 비교하고, `shared_immutable` dependency environment는 §4.5의 저비용 CAS
불변식과 실제 read-only 강제를 검사한다. 봉인되지 않은 ignored 경로 변경은 아래 late discovery 절차를
먼저 적용하며, 자동 확장 조건을 만족하지 못하거나 같은 fingerprint가 반복될 때 `scope_violation`이다.
dependency install·migration·전역 code generation처럼 공유 산출물을 바꾸는 작업은 별도 준비 capability로
먼저 accepted하거나 해당 capability의 `environment_mutation` 배타 구간에서 실행한 뒤 재-probe한다.

#### Late environment discovery

capability가 P2 이후 새 도구·명령·cache를 도입할 수 있으므로 최초 봉인을 완전한 폐쇄 목록으로 가정하지
않는다. 미봉인 ignored 쓰기를 처음 관측하면 Controller는 다음 순서로 한 번만 자동 회수한다.

1. attempt 결과를 accepted하지 않고 해당 process와 겹칠 수 있는 신규 dispatch를 멈춘다.
2. 현재 accepted head와 해당 capability의 tracked diff로 ref 미변경 candidate snapshot을 만든다.
3. task contract revision·실제 실행된 새 command hash·관측 경로 집합을 하나의 discovery fingerprint로 삼아
   snapshot에서 명령을 단독 delta probe한다.
4. 경로가 허용된 project/run root 안에 있고 기존 lease와 교차하지 않으며 정책을 결정론적으로 배정할 수
   있으면 run-local `environment-deltas/<fingerprint>.json`을 봉인하고 임시 ephemeral lease를 확장한다.
5. 같은 task ID의 새 attempt를 확장된 execution packet으로 재실행한다. capability가 accepted되면
   Controller maintenance lane이 delta를 `.opal/oppb-environment.json`에 합치고, 폐기되면 delta도 폐기한다.

추적 profile 반영은 별도 Runner commit이나 후속 임의 commit을 만들지 않는다. 재실행 candidate가 검증을
통과하면 Checkpoint Tool이 publication lock 안에서 현재 parent profile hash를 다시 확인하고 capability의
lease 경로와 maintenance lane의 `.opal/oppb-environment.json` delta를 **같은 candidate commit**에 넣는다.
둘 중 하나라도 stale이면 commit을 publish하지 않고 profile delta를 새 parent 기준으로 재생성한다. receipt는
capability path set과 maintenance path를 구분해 기록한다. 따라서 project worktree의 Git writer는 여전히
Checkpoint Tool 하나다.

task contract revision당 첫 discovery batch 하나만 task attempt·project rework 예산을 차감하지 않는다.
delta probe가 한 명령에서 관측한 모든 경로를 같은 batch로 봉인한다. 실제 시간·token·process 사용량은
telemetry에 남고 project 총자원 상한에는 포함한다. 같은 revision의 두 번째 미봉인 쓰기, probe 결과와
재실행 결과 불일치, 기존 lease 교차, project 밖·민감 경로, 자동 정책 분류 불가는 즉시
`scope_violation`으로 승격하고 그때부터 attempt·rework 예산을 차감한다. 명시적으로 승인된 command 또는
task contract revision이 바뀌면 새 discovery epoch를 열 수 있다. 이 예외는 tracked write·contract·runtime
resource 위반에는 적용하지 않는다.

#### `scope_violation` 회수

사후 범위 위반을 단순 폐기로 끝내지 않는다.

1. Controller가 위반 경로·계약·자원과 겹치는 active attempt의 연결 성분을 계산하고 신규 dispatch와
   checkpoint를 중단한다.
2. 단독 범위 이탈이면 위반 attempt만 종료하고 declared+actual path의 합집합을 해당 attempt preimage로
   복구한다.
3. 둘 이상의 attempt가 같은 변경을 덮어 귀속할 수 없으면 연결 성분의 process를 모두 종료하고, 영향
   경로를 마지막 accepted head 또는 실행 전 봉인 preimage로 path-scoped 복구한다.
4. 영향 attempt는 새 attempt로 재실행하고 충돌 경로를 새 lease에 포함하거나 순차 capability로
   재분류한다. 무관한 accepted 결과와 lease는 유지한다.
5. 위반 attempt마다 task attempt 예산과 project rework 예산을 차감한다. 같은 실패 지문이 두 번
   발생하거나 예산이 소진되면 `no_progress`로 PM 판단을 요청한다.

복구 과정은 worktree 전체 reset·clean을 사용하지 않는다. 복구 전후 path hash와 종료한 process 목록을
receipt로 남긴다.

### P3. CONTINUOUS MINI-TASK EXECUTION

| 항목 | 내용 |
|---|---|
| 스케줄 결정 | Controller Tool |
| 프로세스 실행·회수 | Runtime Supervisor → `opal-agent` headless attempt |
| 코드 작업 | `opal-capability-agent`·조건부 기존 전문 Executor |
| 범위 관리 | Scope Lease Tool |
| 확정 | Checkpoint Tool·조건부 Verifier |
| 문서 | `execution-packet.json`, `result.json`, evidence; 조건부 DESIGN·TEST-SCENARIO |
| 종료 조건 | 모든 필수 미니 태스크 accepted 또는 구조화 blocked |

고정 Wave를 사용하지 않는다. 의존성이 풀리고 세 lease 집합이 겹치지 않는 태스크를 즉시 실행한다.
PM은 capability owner나 Verifier를 대화형 Agent 도구로 직접 디스패치·회수하지 않는다.

### P4. PROJECT VERIFY

| 항목 | 내용 |
|---|---|
| 실행 주체 | Integration·Security·Convention Verifier |
| 완료 판정 | Acceptance Evaluator |
| PM 역할 | 귀속 불명 실패·계약 변경만 판단 |
| 문서 | project evidence·acceptance 결과 |
| 종료 조건 | 전체 회귀·통합 보안·컨벤션·완료조건 통과 |

모든 write lease를 닫고 최종 project checkpoint에서 실행한다. Verifier는 직접 수정하지 않으며 실패를 귀속 가능한 Repair 또는 PM decision으로 반환한다.

### P5. MERGE · KNOWLEDGE · CLOSE

| 항목 | 내용 |
|---|---|
| 사용자 | 승인된 project head의 허브 merge 승인·확인 |
| merge 확인 | Runtime Supervisor·Git 조상 관계 검사 |
| 지식 반영 | Project Knowledge Finalizer |
| 최종 보고 | PM Agent·OPPB Product Flow |
| 문서 | 프로젝트 `DONE.md`, evidence manifest, knowledge receipt |
| 종료 조건 | 허브 merge·MEMORY·brain batch·registry close·worktree 회수 완료 |

MEMORY·brain은 이 단계 전까지 읽기 전용이다. 실패·폐기된 미니 태스크 후보를 제거한 뒤 프로젝트 단위로 한 번 반영한다.

## 6. 미니 태스크 3단계와 실행 에이전트

### M1. RUN

| 구분 | 내용 |
|---|---|
| 준비 | Controller가 workgraph 계약에서 execution packet 생성 |
| 안전 | Scope Lease Tool이 tracked/ephemeral write·contract·runtime resource lease 발급 |
| 실행 에이전트 | `opal-capability-agent` |
| 조건부 에이전트 | Critical 설계면 Design Evaluator, 수직 기능이 여러 전문 영역이면 범위 제한 Executor |
| 수행 | capability micro design → 내부 work item 조율 → UI·API·데이터·테스트 구현 → formatter·lint |
| 결과 | 변경 파일과 테스트 가능한 구현 |

설계는 별도 파이프라인 단계가 아니다. Fast는 바로 구현하며 Standard·Critical만 필요한 설계 기록을 남긴다.

Runner의 Git 변경 금지는 플랫폼별 hook으로 사전 차단했다고 주장하지 않는다. Supervisor가 dispatch 전에
HEAD·index tree·reflog fingerprint를 봉인하고 종료 뒤 다시 비교한다. 실행 중 발생한 Git 전이는 유효한
Checkpoint Tool receipt의 before/after HEAD·index와 정확히 일치하는 것만 제외한다. 설명되지 않는
commit·checkout·reset·지속 index 변경이 발견되면 result를 수용하지 않고 `runner_git_violation`을 발행하며
Checkpoint Tool의 후속 writer를 중단한다. 읽기 전용 Git 조회는 허용한다. 실제 소스 변경은 worktree 파일
diff로만 전달한다.

### M2. PROVE

| 구분 | 내용 |
|---|---|
| 실행 에이전트 | 같은 `opal-capability-agent` |
| 수행 | 직접 단위 테스트·영향 테스트·기존 보안 회귀 |
| 기록 | wrapper가 실제 file hash·명령·결과·비용·지식 후보를 `result.json`에 원자 기록 |
| 상태 | `running`에서 `verifying`으로 전이 |

공유 worktree에서 얻은 로컬 결과는 provisional이다. 다른 Runner의 미완성 변경이 보일 수 있으므로 이 결과만으로 accepted가 되지 않는다.
PROVE가 실패했을 때 다른 active lease의 dirty 변경이 하나라도 있으면 실패를 구현 결함이나 Repair로
즉시 귀속하지 않는다. 다른 lease의 정리를 기다리는 대신 현재 accepted head와 자기 lease diff만으로
ref 미변경 candidate를 만들고, M3와 같은 `git archive` snapshot·검증 resource lease에서 해당 PROVE를
한 번 재실행한다. 통과하면 공유 worktree 오염으로 판정하고 candidate·환경·입력 hash가 변하지 않는 한
M3가 snapshot과 증거를 재사용한다. 격리 snapshot에서도 실패한 경우에만 attempt 실패와 Repair 예산으로
계산한다. 이 재실행은 attempt당 1회로 제한되므로 연속 스케줄링에서도 대기 굶주림이 없다.

### M3. ACCEPT

| 순서 | 실행 주체 | 수행 |
|---|---|---|
| 1 | Checkpoint Tool | lease 밖 tracked·ephemeral 변경과 hash drift 검사 |
| 2 | Checkpoint Tool | 임시 index로 ref·HEAD 미변경 candidate commit과 receipt 병렬 생성 |
| 3 | Checkpoint Tool | 직전 accepted source generation에 Git delta 적용; 최초·검증 실패 시에만 `git archive` fallback |
| 4 | 환경 adapter·Scope Lease Tool | read-only dependency environment와 candidate-private build-cache overlay 준비, Verifier runtime resource lease 발급 |
| 5 | 경량 Convention 검사 | snapshot의 변경 파일 프로젝트 컨벤션 검사 |
| 6 | Integration Verifier | 수용 명령 또는 계약 폐쇄 시에만 snapshot·격리 자원 검사 |
| 7 | Security Verifier | 위험 태스크일 때만 snapshot·격리 자원 심층 검사 |
| 8 | Evidence Tool | 반환 schema·candidate·환경·closure·scope hash 검증 후 불변 evidence 저장 |
| 9 | Checkpoint Tool | 짧은 publication lock에서 parent 확인 후 fast-forward·승인 lease index 정합. stale이면 lock 해제 후 재검증 판단 |
| 10 | Controller Tool | 통과 시 accepted, 실패 시 branch 변경 없이 같은 태스크 Repair |
| 11 | Checkpoint Tool·Scope Lease Tool | snapshot·검증 자원 회수, publication lock이 남아 있지 않음 확인 |

미니 태스크에는 별도 CLOSE 에이전트가 없다. `accepted`가 종료다. worktree finalize·허브 merge·MEMORY·brain·프로젝트 DONE은 P5에서만 수행한다.

## 7. 미니 태스크 문서

### 7.1 항상 생성

| 산출물 | writer | 역할 |
|---|---|---|
| run root의 `workgraph.json` task record | Controller Tool | 미니 태스크 불변 계약의 기계 SSOT |
| run root의 `attempts/<task>/<attempt>/execution-packet.json` | Controller Tool | dispatch 시점의 가변 입력 |
| run root의 `attempts/<task>/<attempt>/result.json` | `opal-agent` attempt wrapper | 변경·검증·비용·차단·지식 후보 |
| run root의 `evidence/<scope>/<id>.json` | Evidence Tool | Verifier 반환을 schema 검증·hash 봉인한 독립 증거 |

### 7.2 조건부 생성

| 산출물 | 생성 조건 | writer |
|---|---|---|
| `DESIGN.md` | Standard 중 설계 선택을 보존해야 하거나 Critical | `opal-capability-agent` |
| `TEST-SCENARIO.md` | 계약·E2E·보안 시나리오가 복잡해 독립 문서가 필요 | `opal-capability-agent` |

### 7.3 생성하지 않음

- 미니 태스크별 `TASK.md`: workgraph task record와 중복
- 미니 태스크별 `DONE.md`: result·evidence와 중복
- 미니 태스크별 `ANALYSIS.md`, `PLAN.md`, `QA.md`, `CLOSE.md`
- 미니 태스크별 MEMORY·brain 기록

사람이 검토할 필요가 있으면 Controller가 workgraph task record의 Markdown view를 임시 렌더링할 수 있지만 별도 SSOT로 저장하지 않는다.

## 8. 미니 태스크 profile

단계 수는 같고 깊이만 다르다.

| Profile | RUN | PROVE | ACCEPT | 추가 에이전트 |
|---|---|---|---|---|
| Fast | 바로 구현 | 직접 테스트 | scope·기본 checkpoint 검증 | 없음이 기본 |
| Standard | capability micro design | 수직 수용·영향 테스트 | 외부 계약·컨벤션 | 필요 시 FE·BE·DB Executor |
| Critical | 보존할 설계 작성 | 심층 시나리오 | 독립 계약·보안·컨벤션 | Design Evaluator·Security Verifier |

`split_required`는 profile이 아니라 Runner 또는 Slicer의 구조화 결과다. Controller는 Runner를 시작하지
않거나 현재 attempt를 닫고 영향 subgraph dispatch를 중단한 뒤 PM Agent에 재슬라이스 결정을 요청한다.

## 9. 상태기계

### 9.1 미니 태스크

```text
queued → running → verifying → accepted
             ↑          │
             └─ repair ─┘

accepted → needs_revalidation → verifying → accepted
                                  └─ 실패 → repair

어느 상태에서든 판단 필요 → blocked
```

`provisional`과 `checkpointed`는 상태가 아니라 result·receipt 속성이다.

외부 계약 revision이 바뀌면 해당 계약의 직접 consumer만 `needs_revalidation`으로 전환한다. 재검증은
consumer의 수용 시나리오와 계약 테스트만 실행한다. 통과하면 즉시 `accepted`로 돌아가고, 실패하면 그
consumer의 Repair가 열린다. Repair가 다시 출력 계약을 바꾼 경우에만 다음 1-hop consumer로 같은 규칙을
전파한다. 무관하거나 아직 실행 전인 태스크는 재검증하지 않는다.

### 9.2 프로젝트

```text
planning
→ active
→ verifying
→ project_done
→ awaiting_merge
→ project_attribution_pending
→ closed
→ worktree_removed
```

사용자·PM 판단이 필요한 동안은 현재 단계에서 `awaiting_decision`으로 전환한다. 영향 가능 subgraph의
신규 dispatch만 중단하고 독립 subgraph는 계속 진행할 수 있다. 결정 receipt 뒤 원래 단계로 복귀한다.

### 9.3 동시성 예산

동시성은 계층별로 분리한다.

| 설정 | 초기값 | 의미 |
|---|---:|---|
| `max_active_runners` | 2 | 동시에 실행 가능한 capability attempt 수 |
| `max_active_executors` | 2 | 모든 Runner가 합산해 사용할 수 있는 전문 Executor 자식 수 |
| `max_total_agent_processes` | 4 | Runner·Executor·Verifier를 합한 전체 headless agent 상한 |

전문 Executor는 Runner admission 상한에 포함하지 않고 별도 pool에서 빌린다. 어느 상한이든 먼저 차면
추가 dispatch는 pending이다. 첫 프로젝트에서 준비 시간·CPU·메모리·포트·테스트 간섭을 측정한 뒤 설정
값만 조정하며, 동시성 확대를 위해 lease 충돌 규칙을 완화하지 않는다.

Runner는 RUN·PROVE result를 남긴 뒤 종료하므로 ACCEPT를 기다리며 process slot을 점유하지 않는다.
candidate가 준비되면 Verifier admission이 신규 Runner·Executor보다 우선한다. 전체 process 상한이 차면
완료된 Executor 또는 Runner slot이 반환될 때 Verifier를 먼저 실행하며, 새 작업을 계속 넣어 검증이
굶는 것을 허용하지 않는다.

## 10. 검증 시점과 실행 주체

| 시점 | 검사 | 실행 주체 |
|---|---|---|
| RUN 중 | formatter·lint·직접 단위 테스트 | `opal-capability-agent` |
| PROVE | 영향 테스트·기존 보안 회귀 | `opal-capability-agent` |
| ACCEPT | 범위·변경 파일 컨벤션·조건부 수용/계약 | Checkpoint Tool·경량 Convention 검사·조건부 Integration Verifier |
| 위험 ACCEPT | 새 I/O·인증·권한·외부 입력·명령 실행 | Security Verifier |
| 계약 폐쇄 | producer-consumer 통합 테스트 | Integration Verifier |
| PROJECT VERIFY | 전체 회귀·통합 보안·전체 신규 컨벤션 | 세 Verifier |
| 완료조건 | 완료조건↔증거 대응 | Acceptance Evaluator |

## 11. 사용자 게이트

사용자를 부르는 시점은 다음으로 제한한다.

1. INTENT와 중대한 신규 기술 결정 승인
2. 기능 범위·외부 계약 변경
3. 비가역 작업·실제 배포
4. 예산 초과·반복 무진전\*
5. 귀속되지 않은 외부 workspace 변경
6. 최종 project head 허브 merge와 CLOSE

\* OPPB v1은 §9.3의 동시성 예산 3종(`max_active_runners`·`max_active_executors`·`max_total_agent_processes`)만
집행한다. 비용·벽시계 예산과 무진전(실패 지문 반복) 판정은 후속 태스크가 소유한다.

일반 미니 태스크 완료·Repair·상태 확인에는 사용자를 호출하지 않는다.

## 12. v2 T0~T8에서 OPPB로의 매핑

| v2 상세 단계 | OPPB 단계 | 처리 |
|---|---|---|
| T0 DISPATCH | M1 RUN 준비 | Controller 내부 명령으로 흡수 |
| T1 LEASE | M1 RUN 준비 | Scope Lease Tool 내부 처리 |
| T2 MICRO DESIGN | M1 RUN | Runner 행동으로 흡수, 문서는 조건부 |
| T3 TEST PROOF | M1 RUN·M2 PROVE | 테스트 작성과 실행으로 분리 흡수 |
| T4 BUILD | M1 RUN | 유지 |
| T5 LOCAL PROOF | M2 PROVE | 유지하되 provisional 명시 |
| T6 HANDOFF | M2 PROVE 종료 | wrapper의 result 원자 기록으로 흡수 |
| T7 CHECKPOINT | M3 ACCEPT | 도구 내부 처리 |
| T8 VERIFY | M3 ACCEPT | 조건부 Verifier 호출로 유지 |

안전 검사는 삭제하지 않는다. 사용자와 Runner가 따라야 할 단계만 세 개로 줄이고, 기계 집행은 해당 단계 내부 command로 내린다.

## 13. 출시 검증

OPPB는 OPPD를 교체하지 않으므로 v1과의 비교 실행을 수행하지 않는다. 수용은 **절대 기준**으로 판정한다 —
OPPB가 주장하는 가치(무인 실행·lease 비충돌 병렬·Git 단일 writer 안전성·cache 정확성)는 모두 다른 엔진
없이 그 자체로 참·거짓을 가릴 수 있다.

### 13.1 fixture spec

대표 fixture는 각각 30~60분, capability 3~6개 규모로 고정한다.

| fixture | 확인 목적 |
|---|---|
| 독립 capability 묶음 | lease 비충돌 병렬 처리량·checkpoint 격리 |
| 공유 모듈 순차 변경 | DAG·계약 폐쇄·`needs_revalidation`, capability 내부 dependency/build-config 변경과 새 command 도입의 배타 구간·late discovery 비용 |
| 외부 I/O·인증 경계 | 심층 보안·실패 귀속·최종 통합 품질 |

OPPB를 fixture별로 cold 3회, warm replay 3회 실행한다. 총 18회이며 전부 무인 headless 실행이므로 사람이
세션을 운용하는 구간이 없다. cold는 새 run root·dependency environment·source generation·build cache에서
시작한다. warm은 직전 정상 실행의 봉인된 environment profile과 CAS generation을 보존한 상태다. 각
fixture·cohort 안의 3회 중앙값을 쓰며 cold 1회가 섞인 warm 중앙값으로 판정하지 않는다. 실행 전 예상
시간·모델 비용을 사용자에게 보고하고 승인받는다.

공유 모듈 fixture의 각 cold run은 P2 profile에 없던 새 command가 안전한 ignored cache 경로를 만드는
capability를 정확히 한 번 포함한다. delta probe·lease 확장·재실행의 벽시계와 process 비용을 cold 활성
시간에서 빼지 않는다. 같은 fixture에는 dependency 또는 build-config 변경도 포함해 environment mutation과
late discovery가 병렬 이득을 얼마나 줄이는지 각각 기록한다.

| 분류 | 지표 | 출시 판정 |
|---|---|---|
| 차단 | 수용 시나리오·전체 회귀·보안·컨벤션 | fixture 완료조건 All Pass, 신규 차단 결함 0 |
| 차단 | 사용자 게이트 사이 무인 실행 | 재촉·강제 재개 없이 완료 또는 구조화 decision 도달 |
| 차단 | runtime 안전성 | 고아 process·상태 손상·미감지 deadlock 0 |
| 차단 | 병렬 안전성 | 동시 lease 충돌 0, `scope_violation` 회수 정상, Runner Git 상태 변경 0 |
| 차단 | cache 정확성 | cold/warm 최종 tree·검증 결과 동일, stale cache 오수용 0, warm이 cold보다 느린 fixture 0 |
| 관찰 | cold·warm 활성 경과 시간 | fixture별 중앙값 기록. 목표치는 두되 출시를 막지 않는다 |
| 관찰 | `opal-agent`가 관측한 워커 token·비용 | 기록 |
| 관찰 | 실패당 재작업 범위 | 재실행 capability 수 기록 |
| 관찰 | lease 대기·candidate 생성·snapshot/cache·검증 비용 | capability별 source 증분·dependency/build cache hit와 ACCEPT 비용을 cold/warm으로 분리 기록 |

시간과 token은 **관찰 지표**다. OPPD와 나란히 돌려 비교하지 않으므로 "v1 대비 80%" 같은 상대 조건을 차단
기준으로 쓰지 않는다. 대신 실사용 프로젝트 2건의 결과가 OPPD 폐기 판정(§4.4)의 근거가 된다. warm cohort는
source generation·dependency environment·build cache 재사용이 정확하고 실제로 이득인지 판정한다. cache
정확성 차단 조건에 걸리면 snapshot 증분·dependency/build cache·Verifier 계획·슬라이스 크기를 개선하고 동일
fixture를 다시 통과하기 전에는 출시하지 않는다.

### 13.2 출시 수용 기준

1. 기존 OPAL 프로젝트에서 관련 문서가 충분하면 PRD·TRD 신규 생성 0
2. 명확한 요청은 INTENT 하나로 실행 계약 확정
3. 프로젝트 worktree 수 1, 미니 태스크 worktree·branch 0
4. 단독 environment probe가 ignored 출력을 정책·한정 입력 hash와 함께 봉인한다. 새 command의 안전한 미봉인 출력은 task contract revision당 1 batch만 delta probe·lease 확장·무과금 재실행하고 반복 또는 위험 경로는 `scope_violation`
5. 봉인된 profile에서 비충돌 미니 태스크 두 개가 실제 동시 실행에 성공하고, 동일 tracked/ephemeral write·contract·runtime resource의 동시 lease 0
6. Runner의 Git 상태 변경과 공유 지식 쓰기 0, 위반 fixture에서 checkpoint 거부
7. 다른 Runner의 미완료 변경을 candidate commit에 포함한 건수 0
8. Fast 미니 태스크의 상시 산출물은 packet·result·evidence뿐
9. 미니 태스크 accepted 전 독립 검증 증거 존재
10. P3 Supervisor start 뒤 사용자 게이트까지 PM tick·수동 재촉·강제 resume 0. process 4개 포화 상태에서 candidate가 준비되면 첫 반환 slot은 신규 Runner가 아니라 Verifier에 배정
11. 프로젝트 완료 전 MEMORY·brain 반영 0
12. 최종 허브 merge 후 MEMORY·brain batch 정확히 1회
13. fixture 3종의 수용 시나리오·전체 회귀·보안·컨벤션 All Pass, 신규 차단 결함 0, cold/warm cache 정확성 조건 통과. 활성 경과 시간은 중앙값 기록만 하고 출시를 막지 않는다
14. 각 미니 태스크가 하나의 capability ID·응집된 acceptance cluster·독립 end-to-end 검증을 가짐
15. 병렬 태스크의 tracked/ephemeral write·contract·business rule·acceptance·runtime resource·global output 교집합 0
16. Runner의 하위 PL·범용 오케스트레이터 생성 0, 전문 Executor는 동일 task ID·승인된 work item lease만 사용
17. Repair는 새 attempt와 압축 packet을 사용하고 동일 대화 강제 resume 0
18. API와 그 전용 화면처럼 단독 가치가 없는 수평 레이어 분할 0
19. 실제 변경 교집합 발생 시 영향 연결 성분만 중단·path-scoped 복구·예산 차감되고 무관 accepted 결과 불변
20. 신규 owner는 `opal-capability-agent` 1종뿐이며 전문·검증 에이전트는 §4.2의 기존 자산 재사용
21. 신규 `//oppb`가 추가 실행 방식 선택 옵션 없이 `opal-capability-agent` 경로만 호출하고 `opal-task-action-agent` 직접 호출 0
22. `//oppd`·`//oppl`·`//opsdd`의 스킬·상태·회귀가 OPPB 도입 전후로 무변경이고, 기존 에이전트·레지스트리 항목 제거 0
23. OPPB 차단 결함을 주입한 fixture에서 `//oppd` 경로가 영향 없이 정상 완주해 복구 계약(§4.4)이 실증됨
24. Supervisor 비정상 종료·재시작 fixture에서 capability owner와 Verifier attempt 재부착/수확 후 자동 tick 재개
25. 프로젝트 태스크 `state.json`은 P0~P5만, `workgraph.json`은 미니 태스크 상태만 변경하고 상호 직접 쓰기 0
26. contract revision 변경 fixture에서 직접 consumer만 `needs_revalidation`, 무관 태스크 재검증 0
27. 다른 active lease가 dirty인 PROVE 실패는 자기 candidate snapshot에서 즉시 재검증되어 대기 굶주림·오귀속 0
28. Evidence Tool이 schema·code head·scope hash 불일치 evidence를 색인 전에 거부
29. G3가 작성한 cache adapter conformance suite를 통과한 `replayable` fixture에서 같은 parent 병렬 candidate 두 overlay가 모두 CAS에 남고, 첫 publication 뒤 stale sibling이 결정론적 seed에 intervening delta를 replay해 cold fallback 0. 실패 adapter는 `non_reusable`
30. 검증 실패 candidate에서 project branch·HEAD·공유 index와 다른 Runner lease path hash 변경 0, `reset --hard` 호출 0
31. 검증 통과 candidate만 expected parent 비교 뒤 fast-forward되고 승인 lease index만 정합, stale parent candidate 반영 0
32. Verifier가 `git archive` fallback·환경 manifest·전용 runtime resource lease로 실행되고 Runner와 port·DB·service 충돌 0
33. 작은 cache cap·만료 retention fixture에서 active node 삭제 0, closed node LRU 회수, DONE·evidence 불변, 공간 부족 시 cacheless 강등 또는 `disk_budget_exceeded`

수용기준의 구현·증거 owner는 §14의 Work item 그룹에 단일 배정한다. 뒤 그룹은 앞 그룹의 evidence를 다시
소유하지 않고 게이트에서 소비한다.

| Work item 그룹 | 소유 수용기준 |
|---|---|
| G1 공용 attempt runtime | 없음* |
| G2 스케줄러 kernel | 9·10·24·25*·28 |
| G3 격리·검증 runtime | 4~7·15·19·27·29~33 |
| G4 Product Flow | 1~3·8·11·12·14·16~18·20·26 |
| G5 출시 검증 | 13·21·22·23 및 전체 회귀 |

\* 기준 25의 소유 그룹은 G2다. 선행 조건인 `state-tool`의 additive enum 확장(`init --skill` choices에 `oppb`, `STAGE_ENUM`에 `P0`~`P5`)만 G1이 소관한다.

## 14. 구현 순서

33개 수용기준은 **하나의 `//opd` 태스크**가 소유한다. OPPB는 기존 Pilot을 교체하지 않으므로 v1 기준선
측정·비교 benchmark가 없고, 사람이 세션을 운용해야 하는 구간도 없다. 따라서 태스크를 쪼갤 이유가
사라졌다. 대신 선후 의존은 PLAN의 **Work item 그룹**으로 표현하고, 앞 그룹의 공개 API와 회귀가 통과한
뒤 다음 그룹을 시작한다.

| 그룹 | 범위 | 산출물 | 소유 수용기준 |
|---|---|---|---|
| G1 공용 attempt runtime | `opal-agent` process group·무출력 watchdog·종료 framing·attempt record, OPPL ledger 경계 동기화 | `opal-agent` 확장, 공용 attempt API | 24 |
| G2 스케줄러 kernel | `oppb-runtime-tool` Controller·Supervisor. run root·event loop·상태·예산·process admission·Evidence·crash recovery | state/event/command/Evidence API 동결 | 9·10·25·28 |
| G3 격리·검증 runtime | `oppb-runtime-tool` Lease·Probe·Checkpoint·Cache. tracked/ephemeral/resource lease, initial·late probe, candidate checkpoint, source/dependency/build CAS DAG·용량/GC, cache adapter conformance suite, scope 회수 | 격리 계약 전체 | 3~7·15·19·27·29~33 |
| G4 Product Flow | `opal-pilot-project-build` 스킬·`pipeline.json`·P0~P5, `opal-capability-agent` 신규, `opal-plan-agent` project-slice profile, 조건부 Verifier, `needs_revalidation`, OPAL/greenfield 문서 라우팅, Knowledge Finalizer·CLOSE | `//oppb` 진입점 | 1·2·8·11·12·14·16~18·20·26 |
| G5 출시 검증 | fixture 3종 cold 9회·warm 9회, 성능·cache 정확성·품질 게이트, 복구 계약 실증, 레지스트리·설치·문서 동기화 | 출시 판정 evidence | 13·21·22·23·전체 회귀 |

### 14.1 그룹 경계 규율

- G2는 API 동결이 산출물이다. G3는 G2 API가 동결된 뒤 시작한다.
- G4는 G2 API 기준으로 준비할 수 있지만 실제 ACCEPT 연결은 G3 회귀 통과 뒤 켠다.
- G5는 G1~G4가 모두 완료된 뒤 시작한다.
- **각 그룹 경계에서 회귀를 통과하면 허브로 중간 merge한다.** 단일 태스크가 main과 장기간 벌어지는 것을 막고, 그룹 단위 복구 지점을 남긴다.
- 기존 Pilot 무변경은 그룹마다 확인한다 — `//oppd`·`//oppl`·`//opsdd`의 스킬·상태·회귀에 손대지 않는다.

### 14.2 도입 영향 목록

교체가 아니므로 기존 자산은 **제거·수정 대상이 아니다**. 아래는 신규 등재와 공용 자산 확장만 담는다.

| 접합점 | 도입 시 처리 |
|---|---|
| `opal-pilot-project-build`·`pipeline.json` | **신규 생성**. P0~P5 Product Flow·상태 행 정의 |
| `opal-capability-agent` | **신규 생성**. 활성 agent registry와 설치 배포 대상에 등재 |
| `opal-skills-registry.json` | `oppb` alias·trigger·pipeline 신규 등재. 기존 항목 무변경 |
| `opal-agent` | 공용 attempt runtime 확장(process group·watchdog·framing·record). OPPL과 공유하므로 **하위 호환 필수** |
| `opal-plan-agent`·`opal-evaluator-agent`·`opal-test-agent` | profile·phase 추가만. 기존 호출 경로 무변경 |
| `op-gc-security`·`op-gc-convention` | evidence·scope hash 입력을 받는 adapter 추가. 기존 `//opgc` 경로 무변경 |
| `op-scenario-gate` | OPPB acceptance cluster·Evidence Tool 입력 normalizer 추가. 기존 OPPD 분기 무변경 |
| `op-brain-ingest`·`opal-improve` hook | OPPB 경로에서는 미니 태스크별 호출 없이 프로젝트 CLOSE 1회. 기존 Pilot의 hook 동작 무변경 |
| `agents.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md`, 구조 다이어그램 | 신규 스킬·에이전트·Pilot 선택 기준을 **추가**. 기존 OPPD 서술 삭제 없음 |
| `actor.md` | OPPB는 고정 Product Flow+headless worker 구조이므로 `--pm` 미지원을 명시 |
| OPPD·OPPL·SDD | **무변경**. 공용 attempt runtime 확장의 하위 호환만 회귀로 확인 |

백업·과거 task·brain 기록은 당시 사실이므로 일괄 치환하지 않는다.

## 15. 확정이 필요한 핵심 결정

이 문서는 다음을 OPPB의 기본값으로 제안한다.

- 필수 프로젝트 문서: `INTENT.md`, `PROJECT-DESIGN.md`
- 선택 문서: PRD·TRD·미니 태스크 DESIGN·TEST-SCENARIO
- 미니 태스크 단계: RUN·PROVE·ACCEPT
- 미니 태스크 기계 SSOT: `workgraph.json`
- 프로젝트 worktree: 1개
- 초기 동시성: active Runner 2·전문 Executor 2·전체 headless agent 4
- PM 하위 PL: 기본 미생성
- 지식 반영: 프로젝트 완료·허브 merge 후 1회
- 진입점: `opal-pilot-project-build`(alias `oppb`) 신규 스킬. 기존 Pilot 교체·라우터 없음
- OPPD 관계: 존치. 실사용 프로젝트 2건 완주 시 deprecated 표시, 3건째부터 신규 사용 중단 후 별도 정리 태스크
- 복구 방식: OPPB 결함 시 `//oppd`를 그대로 사용. tag revert·복구 release 불요
- 구 OPPD 실행 에이전트: `opal-task-action-agent`는 OPPD 소유로 존치. OPPB는 호출하지 않을 뿐 제거하지 않음
- OPPL 관계: 수렴형 독립 Pilot로 존치, attempt 실행 원시 기능만 공유
- 출시 판정: v1 비교가 아닌 절대 기준(무인 실행·병렬 안전성·cache 정확성·품질). 시간·token은 관찰 지표
- 구현 단위: 단일 `//opd` 태스크. 선후 의존은 PLAN Work item 그룹 G1~G5로 표현
- 기존 brain 결정: `oppd-prd-trd-task-folder-promote`, `wbs-세분화-단일책임-수용시나리오`는 OPPD에
  계속 적용되며, OPPB에는 조건부 PRD·TRD·capability 슬라이스·단일 프로젝트 태스크 계약이 대신 적용된다
