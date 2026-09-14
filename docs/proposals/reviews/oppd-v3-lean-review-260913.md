# OPPD v3 Lean 제안서 구현 전 검토

> 대상: `docs/proposals/opal-oppd-v3-lean-project-execution.md` (초안, 2026-09-13)
> 검토: 알투(PM) · 2026-09-13
> 근거: v2 제안서, OPPL 안정화 제안서, 현행 `opal-pilot-project-dev` SKILL.md, `opal-task-action-agent`, harness `worktree.md`·`actor.md`, `opal/agents/*`, `opal/tools/*`

## 판정

방향은 타당하다. v2의 안전 계약(lease·단일 Git writer·지식 1회 반영)을 유지하면서 단계·문서·에이전트를 줄인 것은 옳다. 그러나 **구현 착수 기준으로는 미정 항목 5건(B)이 남아 있어 그대로 태스크로 넘기면 워커가 추측하게 된다.** B1~B5를 개정한 뒤 착수한다.

## B. 착수 차단 항목

| # | 문제 | 근거 | 요구 개정 |
|---|---|---|---|
| B1 | **Runner 실행 채널 미정.** Supervisor의 process group·heartbeat·timeout은 프로세스 기반 Runner 전제인데, 현행 oppd는 플랫폼 Agent 도구로 디스패치하고 §4.1 트리도 서브에이전트처럼 그린다 | `opal-pilot-project-dev/SKILL.md:412,520` · OPPL은 내부 축을 opal-agent 헤드리스 채널로 디스패치(`opal-loop-action-agent/AGENT.md:55`) | capability agent·Verifier는 **opal-agent 채널**로 실행함을 명시. PM→Product Flow만 Agent 도구 |
| B2 | **런타임 원시 기능 중복.** OPPL 안정화 제안서의 `oppl-runtime-tool`(ledger·admission·PGID·7상태)과 v3 Controller/Supervisor가 같은 원시 기능을 각각 신설. OPPL 문서는 "범용 Controller"를 비범위로 선언 | `opal-oppl-runtime-stabilization.md:46,96-137` | attempt wrapper(process group·watchdog·terminal framing)와 ledger 라이브러리를 **단일 owner**(opal-agent 확장)로 두고 두 Pilot이 소비. 또한 opal-agent 무출력 watchdog 부재(같은 문서 §3.1)는 v3 선행 의존이므로 §14 구현 순서에 추가 |
| B3 | **산출물 위치·Git 추적·기존 SSOT 관계 미정.** INTENT/PROJECT-DESIGN/workgraph/attempts/evidence의 루트 경로가 없음(v2 §6은 허브 `.opal-runs/<run_id>/` 명시). `state.json`(state-tool MUST)·`pipeline.json`과 `workgraph.json` 관계, 프로젝트 자체의 OPAL 태스크 번호·`tasks/NNN` 폴더 여부 미정 | `.opal/AGENT.md` state-tool MUST · `worktree.md:30,56-59` 슬롯이 `task_{NNN}` 단위, remove 3-guard는 경로별 예외 없음(`:110`) | 프로젝트 = OPAL 태스크 1건(번호·폴더·state.json P0~P5 행)으로 고정, workgraph는 P3 내부 SSOT로 정의. run root 경로·Git 추적 여부 표 복원. `worktree-tool` 확장 범위(1 worktree N writer의 dirty 귀속·finalize) 명시 |
| B4 | **Evidence Tool 삭제.** v2의 schema 검증·content hash 발급 주체가 §4 표에 없다. §7.1은 "각 Verifier wrapper"가 쓴다고만 함 | v2 §12 · v3 §4, §7.1 | Evidence schema owner를 Checkpoint Tool 또는 Controller에 귀속시켜 표에 추가. 수용기준 9·19 판정 근거 |
| B5 | **계약 변경 후 재검증 경로 부재.** §9.1 상태기계는 accepted에서 돌아오는 전이가 없고, v2 §10.4 `needs_revalidation`이 삭제됨. §11 게이트 2는 외부 계약 변경을 허용 | v3 §9.1, §11 · v2 §10.4 | `accepted → needs_revalidation → verifying` 전이와 1-hop consumer 규칙 복원 |

## M. 주요 보완 항목

1. **동시성 상한 정의.** §15 "초기 동시성 2"와 §4.1 "상한은 Runner+Executor 합산"을 함께 두면 FE+BE Executor를 부르는 capability 하나로 상한 초과, 실질 병렬 1. 상한을 Runner 수로 두고 Executor는 별도 상한으로 분리하거나 수치를 재설정.
2. **벤치마크 스펙 삭제.** 수용기준 13 "v1 동등 이상"의 판정 근거(v2 §15.2 fixture 3종·실행 횟수·차단/관찰 분리)가 v3에 없다. §14-9 한 줄로는 판정 불가.
3. **Runner Git 금지 guard 수단.** 플랫폼 독립·hook 미채택 원칙상 사전 차단은 불가하다. HEAD·index·reflog 비교 기반 **사후 탐지**로 정의하고, 위반 시 checkpoint 거부·writer 정지로 처리.
4. **provisional PROVE 오탐.** 공유 worktree에서 다른 Runner의 미완성 변경으로 A의 테스트가 실패하면 Repair 예산이 소모된다. 실패 시 다른 active lease가 dirty면 Repair 대신 재실행 대기로 귀속하는 규칙 필요.
5. **소유권 6축 vs lease 3집합.** business rule·acceptance·global output은 lease 집합 밖이다. Slicer 선언·Controller schema 검증·PM 판단의 경계와 "증명 불가 시 분할 금지"의 증명 주체를 명시.
6. **재사용 에이전트 확장 실측.** `opal-plan-agent`는 입력 표가 없어(`AGENT.md:25` 자유 프롬프트) project-slice profile은 신규 입력 계약 설계다. checker 2종은 `skill_path` 얇은 role이므로 "evidence·scope hash 입력 추가"는 `op-gc-*` 스킬 변경이다. `opal-evaluator-agent`만 `phase` 축이 있어 acceptance phase 추가가 자연스럽다.
7. **제거·교체 영향 목록.** `opal-task-action-agent` 참조: `opal/core/references/agents.md:46-52`, `opal-sdd-action-agent/AGENT.md:62,162,285`, `opal-loop-action-agent/AGENT.md:383`, `docs/PROJECT.md:75,101`, `docs/ARCHITECTURE.md:177,480`, `docs/CONVENTIONS.md:21`(15종), 구조 다이어그램 html. install 스크립트는 디렉터리 스캔이라 무변경. 별도로 oppd 접합점인 opal-improve 회고 훅·op-brain-ingest CLOSE 훅·scenario-gate "oppd 2차 유예"·`actor.md` oppd 미지원을 교체 시 재정의해야 한다.
8. **OPPL 관계 미언급.** v2는 `//oppl` 폐기, OPPL 안정화 제안서는 독립 존치를 주장한다. v3는 침묵. 같은 날 작성된 3문서의 입장을 v3에 한 줄로 확정.

## m. 경미 항목

- §4.1 트리의 "Repair Runner"가 별도 에이전트처럼 보인다. 본문대로 "새 attempt의 capability agent"로 표기.
- §8 "Split"은 profile이 아니라 결과다. 표에서 분리.
- §9.2 프로젝트 상태기계에 사용자 게이트 대기 상태(`awaiting_decision`)가 없다.
- §P2.1 "20% 규칙"의 추정 주체·시점 미정.
- brain 기존 결정(`oppd-prd-trd-task-folder-promote`, `wbs-세분화-단일책임-수용시나리오`)을 폐기함을 §15에 명시.

## 다음 단계

1. B1~B5·M1~M8을 반영해 v3를 개정한다(문서 작업, 코드 변경 없음).
2. 개정본 확정 후 `//opd`로 구현 태스크를 기동한다. 첫 태스크는 §14-1(동결 tag)과 B2의 공유 attempt wrapper다.

---

## 2차 검토 (개정본, 748행)

### 1차 항목 반영 결과

| 항목 | 반영 위치 | 판정 |
|---|---|---|
| B1 실행 채널 | §1, §4.1, P3 — capability owner·Verifier는 Supervisor가 `opal-agent` headless attempt로 실행 | 해소 |
| B2 런타임 중복 | §2, §4.6, §14-2 — `opal-agent` 공용 attempt runtime 단일 owner, OPPL 존치, watchdog 선행 조건 | 해소 |
| B3 산출물·SSOT | §4.5 — 프로젝트 = OPAL 태스크 1건, run root 미추적, state.json/workgraph 분리, pre-finalize gate | 해소 |
| B4 Evidence Tool | §4 표, M3-7, §7.1 | 해소 |
| B5 재검증 | §9.1 `needs_revalidation` 1-hop 규칙 | 해소 |
| M1~M8 | §9.3 동시성 3값, §13.1 benchmark, M1 Git 사후 탐지, M2 `retry_after_checkpoint`, §P2.1 6축 검증 주체, §4.2 확장 방식 정정, §14.1 영향 목록, §2 OPPL | 전부 해소 |
| m1~m5 | §4.1 Repair attempt, §8 split_required, §9.2 awaiting_decision, §P2.1 20% 추정 주체, §15 brain 결정 대체 | 전부 해소 |

### 개정으로 새로 생긴 항목

| # | 문제 | 근거 | 요구 |
|---|---|---|---|
| N1 | **ACCEPT 실패 후 복구 순서가 위험하다.** M3는 2단계에서 commit을 먼저 만들고 8단계에서 실패 시 preimage 복구한다. branch HEAD가 이미 전진했으므로 복구가 `reset --hard`면 다른 Runner의 미commit 변경을 파괴한다 | §4.5, M3 2·8단계 | `reset --hard` 금지를 명문화. 권장: checkpoint를 branch ref를 움직이지 않는 dangling commit(`commit-tree`)으로 만들고 snapshot 검증 통과 뒤에만 branch를 fast-forward. 실패 시 ref 이동 없이 lease 경로만 preimage로 파일 복원 |
| N2 | **검증 snapshot의 실행 자원·materialize 방식 미정.** `.git` 없는 복사본에서 Integration Verifier가 테스트를 돌리면 의존성(node_modules·venv)·빌드 산출물 준비와 port·DB·fixture가 필요하다. 실행 중 Runner의 runtime resource와 충돌할 수 있는데 Verifier는 lease를 받지 않는다 | §4.5, M3 3~6단계 | snapshot은 `git archive <commit>`으로 생성하고 의존성 캐시는 read-only 공유로 명시. Verifier 실행에도 runtime resource lease를 요구(§9.3·Scope Lease Tool 책임에 추가) |
| N3 | **`retry_after_checkpoint` 대기가 연속 스케줄링에서 굶을 수 있다.** 다른 lease가 정리되기 전에 새 Runner가 dispatch되면 "dirty 0" 기준선이 오지 않는다 | M2 | 대기 상한 또는 대안: 기준 checkpoint + 해당 lease diff만 materialize한 snapshot에서 PROVE를 재실행(N2 snapshot 기법 재사용) |
| N4 | P1·P2의 Discovery·Planner/Slicer·Design Evaluator 실행 채널이 불명확하다. §4.1은 Evaluator를 headless로 두지만 P2 시점에는 workgraph·Controller 명령이 아직 없다 | §4.1 139행, P2 | planning 상태에서 Product Flow가 Supervisor에 ad-hoc attempt를 요청하는지, 아니면 P0~P2 서브에이전트만 Agent 도구를 허용하는지 명시 |
| N5 | attempt ledger 소유가 OPPL 안정화 제안서(`oppl-runtime-tool`의 `runtime.json`)와 v3 §4.6(`opal-agent` ledger primitive)에 중복 기재 | 두 문서 | 경계 확정: opal-agent = attempt 1건 기록 primitive, Pilot 도구 = 집계·상한 카운터. OPPL 문서도 같은 문장으로 동기화 |
| N6 | 경미 — `DONE.md` writer가 둘(Controller Tool·PM Agent). 허브 `.opal-runs/` ignore 보장 주체 미기재. `max_total_agent_processes`=4가 Runner 2+Executor 2로 포화되면 Verifier가 대기함(의도라면 명시) | §4.5, §9.3 | 한 줄씩 명시 |

### 판정

1차 차단 항목은 전부 해소됐다. 새 항목 중 N1·N2는 Checkpoint Tool·Verifier 구현에 직접 영향을 주므로 **구현 태스크 PLAN 진입 전에 제안서에 반영**한다. N3~N6은 구현 태스크의 PLAN 단계에서 결정해도 된다.

구현은 단일 태스크로 하지 않는다. §14 순서를 기준으로 최소 4묶음(①tag 동결+opal-agent attempt runtime ②Controller·Lease·Checkpoint·Evidence 도구 ③capability agent·plan-agent profile·Verifier 연결 ④benchmark·교체·제거)으로 나누고, 각 묶음을 `//opd` 태스크로 기동한다.

---

## 3차 검토 (개정본, 772행 · 2026-09-14)

| 항목 | 반영 위치 | 판정 |
|---|---|---|
| N1 복구 순서 | §4.5 — 임시 index `commit-tree` candidate, ref·HEAD·공유 index 불변, 통과 시에만 expected parent 확인 후 fast-forward, `reset --hard` 금지. M3 11단계, 수용기준 30·31, 구현 순서 5 | 해소 |
| N2 snapshot 자원 | §4.5 — `git archive <candidate>`, 환경 adapter bootstrap·lockfile cache read-only, Verifier 전용 runtime resource lease, evidence에 candidate·manifest·lock·lease ID 기록. M3 4단계, 수용기준 32 | 해소 |
| N3 `retry_after_checkpoint` 굶주림 | M2 문구 동일 | 미반영 — PLAN 이월 허용. candidate snapshot에서 PROVE 재실행이 자연스러운 해법 |
| N4 P0~P2 서브에이전트 채널 | 언급 없음 | 미반영 — PLAN 이월 허용 |
| N5 ledger 경계 | v3 §4.6은 opal-agent에 ledger primitive, OPPL 문서 §4는 `oppl-runtime-tool`에 attempt ledger | 미반영 — 두 문서 한 문장 동기화 필요. 묶음 ① 태스크의 TASK.md에서 확정 |
| N6 경미 3건 | DONE.md writer 2주체 유지, `.opal-runs` ignore 주체 미기재, 프로세스 상한 포화 시 Verifier 대기 미명시 | 미반영 — PLAN 이월 허용 |

### 판정

착수 차단 항목 없음. 제안서는 구현 태스크 기동 가능 상태다. 이월 항목 N3~N6은 묶음 ①·② 태스크의 TASK.md 결정 사항으로 넘긴다.

---

## 4차 검토 (개정본, 772행 · 2026-09-14)

> 관점: 1~3차가 "빠진 계약"을 채웠다면, 4차는 채워진 계약이 **실행 가능한 비용인지**를 본다.
> 실측: `opal/tools/opal-agent/opal_agent.py`, `opal/tools/worktree-tool/worktree_tool.py`, `opal/skills/opal-pilot-project-loop/SKILL.md`, `opal/tools/opal-action-monitor/`

### 판정

착수 차단 항목은 없다(3차 판정 유지). 다만 **"Lean"은 사용자·문서 표면에만 성립하고 런타임 표면은 v1보다 커진다.**
신규 결정론적 도구 4종(Controller·Lease·Checkpoint·Evidence) + Runtime Supervisor + `opal-capability-agent` + `opal-agent` attempt runtime 재작성이 전제다.
따라서 3차의 4묶음 분할을 유지하되, 아래 C1~C3을 묶음 ②·③의 **설계 입력**으로 고정한다.

### C. 비용·성립성 항목

| # | 문제 | 근거 | 요구 |
|---|---|---|---|
| C1 | **ACCEPT 전역 직렬 lane이 시간 목표를 자기모순으로 만든다.** capability마다 `git archive` snapshot 생성 → 의존성 bootstrap → Convention·Integration·Security Verifier를 직렬 반복한다. capability 3~6개 규모에서 준비 비용이 병렬 이득을 넘길 개연성이 높다 | §4.5, M3 3~8단계, §13.1 | §13.1의 "준비 비용"을 관찰에서 **차단 지표로 승격**하거나, snapshot·의존성 재사용과 증분 Verifier 범위를 §4.5에 명시 |
| C2 | **gitignore 산출물이 lease 모델 밖이다.** lease 3집합은 Git 경로·계약·runtime resource 기준인데 `node_modules`·`dist`·`.next`·`__pycache__`는 추적 대상이 아니라 `write_set`에 잡히지 않는다. 프로젝트 worktree가 1개이므로 두 Runner의 RUN·PROVE 빌드가 같은 디렉토리를 동시 갱신한다 | §4.5, §P2.1 소유권 축, M1·M2 | §4.5가 검증 snapshot에만 적용한 "mutable dependency·build 디렉토리 비공유" 원칙을 **Runner 측에도 적용**. build·cache 디렉토리를 `runtime_resources`로 선언 가능하게 하거나 Runner별 build output 분리 |
| C3 | **P3 tick을 실제로 도는 프로세스 주체가 없다.** §4.1은 PM의 직접 디스패치·회수를 금지하고 Supervisor가 tick을 재호출한다고만 한다. 데몬인지 PM 호출형 blocking 명령인지 미정이며, 이는 §13.1 차단 조건 "사용자 게이트 사이 무인 실행"의 전제다 | §4.1 139행, P3, §13.1 | Supervisor의 수명주기(기동 주체·상주 여부·세션 종료 시 거동·재부착)를 §4.6에 명시. 현행 OPPL은 PM 세션이 루프를 돌린다(`opal-pilot-project-loop/SKILL.md:302`) — v3는 이 전제를 바꾸므로 명시가 필수다 |

### M. 보완 항목

1. **`scope_violation` 회수 경로 부재.** §P2.1은 실제 교집합 발견 시 두 결과를 checkpoint하지 않고 중단한다고만 한다. 사후 탐지 모델에서 위반은 예외가 아니라 정상 빈도이므로, 폐기된 두 capability의 재작업 예산 귀속과 재슬라이스 트리거를 정의한다.
2. **benchmark 표본 비대칭.** §13.1은 v1 기준선 fixture당 1회, v3 후보 3회다. 단일 표본 기준선으로 차단 지표 "v1 동등 이상"을 판정할 수 없다. v1도 fixture당 최소 2회로 올리거나, 차단 판정을 "명백한 열위 부재"로 재정의한다.
3. **선행 의존의 검증 경로.** `opal-agent`에 process group·PGID·heartbeat가 없고 timeout은 직접 자식 1개만 대상임을 실측 확인했다(`opal_agent.py:672,709-721`). 이 재작성은 OPPL도 동일하게 기다리는 항목이므로, 묶음 ①을 OPPD가 아니라 **OPPL 실행에서 먼저 검증**하면 회수가 빠르고 v3 benchmark의 변수도 줄어든다.

### 이월

3차의 N3~N6은 그대로 유효하며 재기재하지 않는다. C1~C3은 묶음 ②·③ TASK.md의 결정 사항으로 넘긴다.

---

## 5차 검토 (개정본, 867행 · 2026-09-14)

> 범위: 4차 지적(C1~C3) 반영분에 한정한 초점 검토.
> 축: (1) ACCEPT cold/warm 비용이 §13.1의 80% 차단 조건을 만족할 수 있는가, (2) ignored 산출물 격리가 실제 빌드 도구에서 가능한가.

### 4차 항목 반영 결과

| 항목 | 반영 위치 | 판정 |
|---|---|---|
| C1 ACCEPT 직렬 비용 | §4.5 — 전역 직렬화를 publication 구간으로 축소, content-addressed snapshot·dependency cache, `verification_closure` 기반 검증 재사용. §13.1 — 활성 경과 시간을 차단 지표로 승격 | 해소 |
| C2 ignored 산출물 | §P2.1 — `ephemeral_write_set`과 `shared_immutable`/`attempt_namespaced`/`exclusive` 3정책, 미선언 ignored 쓰기를 `scope_violation`으로 규정 | 해소 |
| C3 Supervisor 주체 | §4.1·§P3 — `oppd-runtime-tool` 상주 process, event loop·재부착·고아 판정·정지 상태 명시. 수용기준 10·24 | 해소 |
| M1 `scope_violation` 회수 | §P2.1 — 연결 성분 계산·path-scoped 복구·재슬라이스·rework 예산 차감 5단계 | 해소 |
| M2 benchmark 표본 | §13.1 — v1·v3 각 fixture 3회, 총 18회, 엔진별 중앙값 비교 | 해소 |
| M3 묶음 ① 선행 | §14 — 4묶음 분할, ①이 공용 attempt runtime과 OPPL ledger 경계 동기화 소유 | 해소 |

### D. 성능 성립성 항목 (축 1)

| # | 문제 | 근거 | 요구 |
|---|---|---|---|
| D1 | **warm 가정이 dependency env에만 성립하고 build cache에는 성립하지 않는다.** cache key는 lockfile+toolchain+bootstrap hash인데 `tsbuildinfo`·`.next/cache`·vite·pytest 캐시는 source 의존이라 이 키에 잡히지 않는다. 설치 결과·build output을 snapshot 로컬에 두므로 **모든 candidate가 cold build**다 | §4.5 snapshot·cache 문단 | build cache를 dependency와 분리된 content-addressed 캐시 대상으로 추가하고, 이전 accepted base의 build cache를 candidate에 read-write overlay로 상속 |
| D2 | **base snapshot 캐시 키가 ACCEPT마다 무효화된다.** accepted tree snapshot을 tree hash로 캐시하는데 project head는 매 ACCEPT마다 전진하므로 capability N개면 base도 N개다. candidate→base overlay만 정의하고 base→다음 base의 증분 갱신이 없다 | §4.5 | 새 accepted head의 base를 직전 base + 승인 lease 경로 delta로 갱신하는 경로를 명시. `git archive` 전체 복사는 cache miss·무결성 불일치에서만 |
| D3 | **차단 판정의 cold 표본이 부족하다.** fixture 3회 중 첫 회만 cold이므로 중앙값은 warm에 가깝다. 그러나 실사용의 첫 프로젝트는 항상 cold다 | §13.1 | 중앙값 조건과 별도로 **cold 1회 단독 기록**을 남기고, cold가 v1보다 현저히 느리면 최적화 backlog를 차단 해제 조건에 포함 |

### E. 격리 실현성 항목 (축 2)

| # | 문제 | 근거 | 요구 |
|---|---|---|---|
| E1 | **`ephemeral_write_set`을 P2에서 선언한다는 전제가 비현실적이다.** 재지정 자체는 가능하다 — `distDir`·`build.outDir`·`tsBuildInfoFile`·`cacheDirectory`·`PYTHONPYCACHEPREFIX`·`GOCACHE`·`CARGO_TARGET_DIR`. 그러나 전이 의존 도구가 쓰는 캐시 경로는 Slicer가 사전 열거할 수 없고, 미선언 쓰기가 곧 `scope_violation`이므로 **첫 병렬 실행이 위반으로 깨지는 것이 기본 시나리오**다 | §P2.1 ignore 산출물 계약 | 선언이 아니라 **probe로 채운다.** P0 또는 P2에서 선언된 실행·검증 명령을 1회 단독 실행해 미추적 쓰기를 관측하고 프로젝트 설정에 봉인한 뒤, Slicer 선언은 그 기준선의 delta만 담당 |
| E2 | **`shared_immutable` manifest 비교 비용.** `node_modules`는 파일 10만 개 규모이며 attempt마다 사전·사후 manifest를 계산하면 격리 비용이 실행 비용을 넘는다 | §P2.1 Scope Lease Tool 문단 | `shared_immutable`은 전수 manifest 대신 lockfile hash + top-level entry mtime·size 같은 저비용 불변식으로 검사. 전수 비교는 `attempt_namespaced`·`exclusive`에만 적용 |
| E3 | **의존성 추가의 직렬화 빈도.** 규약상 dependency install은 별도 준비 capability로 선행 accepted해야 하는데, 실제로는 capability 구현 도중 발생하는 것이 정상이다. 매번 DAG 앞단으로 되돌리면 병렬 이득이 상쇄된다 | §P2.1 | benchmark fixture에 "구현 중 의존성 추가"를 포함해 실측하고, 허용 가능하면 lockfile 배타 lease + 재bootstrap 경로를 §4.5에 정의 |

### 이월

- 프로세스 상한 `max_total_agent_processes` 4가 Runner 2 + Executor 2로 포화될 때 Verifier 대기 여부(3차 N6)는 여전히 미명시.
- D1·D2는 묶음 ②(snapshot/cache)의 설계 입력, E1·E2는 묶음 ②(Lease), D3·E3은 묶음 ④(benchmark)의 완료조건으로 귀속한다.

### 판정

착수 차단 항목 없음. 묶음 ①은 D·E와 독립이므로 즉시 기동 가능하다.

---

## 6차 검토 (최종본, 1012행 · 2026-09-14)

> 범위: 5차 이후 3회 개정(867 → 926 → 972 → 1012행)의 누적 확인.

### 지적 해소 결과

| # | 지적 | 반영 위치 | 판정 |
|---|---|---|---|
| D1 build cache cold | §4.5 — build cache를 dependency와 분리한 3계층 CAS, candidate overlay 갱신·통과 시 승격 | 해소 |
| D2 base snapshot 무효화 | §4.5 — `diff-tree` 증분 generation, `git archive`는 최초·복구 fallback | 해소 |
| D3 cold 표본 | §13.1 — v1 cold 9·v3 cold 9·v3 warm 9로 코호트 분리, 차단은 cold로 판정 | 해소 |
| E1 probe 선언 전제 | §P2.2 ENVIRONMENT PROBE & SEAL — 명령별 단독 실행 관측 후 `.opal/oppd-environment.json` 봉인 | 해소 |
| E2 manifest 비용 | §4.5 — `shared_immutable`은 CAS object ID·receipt·read-only 강제로 검사, 전수 비교는 namespaced/exclusive만 | 해소 |
| E3 의존성 추가 직렬화 | §P2.2 — `environment_mutation` 배타 구간 + 재-probe, fixture 2에서 측정 | 해소 |
| F1 새 command 미봉인 | §P2.2 Late environment discovery — revision당 1 batch 무과금 delta probe·lease 확장·재실행, 반복·교차·민감 경로는 `scope_violation` 승격 | 해소 |
| F2 build cache 직렬 승격 | §4.5 — 단일 파일 대신 cache DAG head set, 병렬 sibling 전부 CAS 보존, 결정론적 seed 선택, `replayable`/`non_reusable` adapter | 해소 |
| F3 v1 baseline 시점 | §13.1·§14 — v1 cold 9회를 묶음 ①로 전진, immutable baseline receipt | 해소 |
| F4 입력 hash 범위 | §P2.2 — repository tree 전체가 아닌 command·config·lockfile·toolchain 한정 명시 | 해소 |
| F5 묶음 ② 비대 | §14 — 4묶음 → 5묶음, 스케줄러 kernel과 격리·검증 runtime 분리 | 해소 |
| G1 cache 무한 보존 | §4.5 — warm retention 7일·soft cap·LRU eviction·active node pin, 수용기준 33 | 해소 |
| G2 late discovery 시간 | §13.1 — fixture 2의 cold run마다 새 command 1회 포함, 벽시계를 cold 활성 시간에서 빼지 않음 | 해소 |
| G3 environment delta writer | §P2.2 — capability lease 경로와 maintenance lane delta를 **같은 candidate commit**에 포함 | 해소 |
| G4 conformance 주체 | §4.5·§14 — cache adapter 계약과 공용 conformance fixture를 묶음 ③이 작성, P2.2에서 adapter별 실행 | 해소 |

### 판정

착수 차단 항목 없음. 4차~6차에서 제기한 성능 성립성·격리 실현성·운영 한계 항목이 모두 계약으로 내려왔고,
수용기준은 33개로 확장돼 §14의 5묶음에 배분됐다. 제안서는 구현 태스크 기동 가능 상태다.

구현은 묶음 ① → ②·(v1 baseline 병행) → ③ → ④ → ⑤ 순서로 기동한다.
