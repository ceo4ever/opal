---
name: opal-pilot-project-dev
description: |
  **프로젝트 개발 라이프사이클 오케스트레이터**. 아이디어부터 개발 완료(product)까지
  opwt로 기획 산출물(PRD/TRD) 작성 → WBS 수립 → opal-task-action-agent로 액션 자율 실행.
  모든 산출물은 PM 검수 → 사용자 확정 순서를 거친다.
  opi 없이 단독 호출도 가능 (docs/PROJECT.md 존재 시).
triggers:
  - "opal-pilot-project-dev"
  - "oppd"
  - "프로젝트 개발 시작"
  - "개발 계획"
  - "개발 파일럿"
version: 4.0.0
---

# opal-pilot-project-dev

아이디어부터 개발 완료(product)까지 전체 라이프사이클을 3 Phase 파이프라인으로 관리한다.
기획 산출물은 opwt에 위임하고, 코드 실행은 opal-task-action-agent에 위임하며, PM이 전체를 조율한다.

## Harness

모드: Project Dev (PLAN → WBS → EXECUTE)
> 부트스트랩에서 로드되지 않은 경우: `~/.opal/references/opal-harness.md`를 Read한다.

**[MUST]** 스킬 시작 즉시 모드에 따라 서브 하네스를 Read한다. 이 단계를 건너뛰면 안 된다:
- `--interactive` 플래그 → `~/.opal/references/opal-harness-interactive.md`를 Read한다
- `--agentic` 플래그 → `~/.opal/references/opal-harness-agentic.md`를 Read한다
- 모드 플래그 없음 (기본) 또는 `--semi-agentic` → `~/.opal/references/opal-harness-semi-agentic.md`를 Read한다
- 다중 모드 플래그 동시 사용 시 즉시 사용자에게 보고 + state init도 거부 (`mode_flag_conflict`)

> **[MUST]** 산출물 작성·검증 시 `opal/core/references/harness/citation-rules.md`를 Read하여 규칙(근거 제시 원칙 / 트랙별 매트릭스 / [MUST] 토큰 / 영역 간 용어 일관성 / decision_required 계약)을 준수한다.

## 설계 원칙

- **위임과 조율**: 기획은 opwt, 코드는 opal-task-action-agent에 위임하고 PM이 조율한다
- **PM 검수 → 사용자 확정**: PM이 통과시킨 결과물만 사용자에게 올린다
- **세션 독립**: STATE.md 기반으로 어느 세션에서든 정확한 지점에서 재개한다
- **agentic 지향**: 아이디어 → product까지 자율적으로 진행하되, 사용자 게이트를 거친다

---

## 사전 조건 체크

`//oppd` 호출 시 프로젝트 루트의 `docs/PROJECT.md` 존재 여부를 확인한다.

| 조건 | 동작 |
|------|------|
| `docs/PROJECT.md` 존재 | Phase 1 시작 |
| `docs/PROJECT.md` 미존재 | opi 자동 실행 → 완료 후 oppd 복귀 |

**opi 자동 실행 시**:
1. 사용자의 원래 요청을 보존한다
2. `~/.opal/skills/opal-project-init/SKILL.md`를 Read하여 opi를 실행한다
3. opi 완료 즉시, 보존한 원래 요청으로 oppd Phase 1을 시작한다

---

## 태스크 생성

사전 조건 체크 통과 후, oppd 전용 태스크 폴더를 생성한다.

```
tasks/{NNN}-oppd-{프로젝트명}/
├── TASK.md       ← 전체 그림 (목표, 참조 문서, 절차)
├── STATE.md      ← 진행 상황 추적
├── DONE.md       ← 완료 시 랩업
└── actions/              ← 액션 폴더
    ├── A01-{액션명}/     ← opal-task-action-agent가 사용하는 태스크 폴더
    │   ├── TASK.md
    │   ├── PLAN.md
    │   ├── TEST-SCENARIO.md
    │   └── DONE.md
    ├── A02-{액션명}/
    └── ...
```

`{NNN}`: 기존 `tasks/` 폴더의 최대 번호 + 1로 자동 채번.

### TASK.md 작성

```markdown
# TASK: {프로젝트명} 개발 파일럿

> 작성일: YYYY-MM-DD | 스킬: //oppd

## 목표

{사용자의 원래 요청}

## 참조 문서

| 문서 | 용도 | 읽는 시점 |
|------|------|----------|
| docs/PROJECT.md | 프로젝트 정의, 원칙 | 전체 |
| docs/ARCHITECTURE.md | 기술 스택 | Phase 1~3 |
| docs/CONVENTIONS.md | 코드 컨벤션 | Phase 3 |
| .opal/AGENT.md | PM 검토 기준 | 전체 |

## 절차

| Phase | 방식 | 산출물 | 설명 |
|-------|------|--------|------|
| 1 | opwt 호출 | tasks/{NNN}-oppd-…/PRD.md, tasks/{NNN}-oppd-…/TRD.md (작업본) | 기획 산출물 작성 (opwt "작성" 모드) — 사용자 확정 후 docs/ 승격 |
| 2 | PM 직접 | tasks/{NNN}-oppd-…/WBS.md | 태스크 분할 + WBS 수립 (태스크 폴더 전용, docs/ 승격 없음) |
| 3 | opal-task-action-agent 디스패치 | actions/A01~A{MM} | 액션 자율 실행 |
```

### STATE.md 초기 생성

state-tool을 호출하여 초기화한다:

```
~/.opal/tools/state-tool/run.sh init <task-path> --skill oppd --mode <interactive|semi-agentic|agentic> --rows-from opal/skills/opal-pilot-project-dev/SKILL.md
```

> **[R-10 비표준 행 구성]** oppd는 Phase 기반(1-PLAN/2-WBS/3-EXECUTE) 비표준 행 구조를 사용한다. `gate-pass` 명령은 deprecated — 사용 불가. State Gate/QA Gate 행은 존재하지 않으며(state-tool stage-transition guard로 이전), PM Gate 단일 mark만 사용한다.
>
> 각 Gate 전환 시 PM Gate 행만 mark한다:
> ```
> ~/.opal/tools/state-tool/run.sh mark <task-path> --row <PM_Gate_N> --done
> ```

아래 "STATE.md 관리" 섹션의 템플릿으로 STATE.md 본문을 작성한다.

---

## 세션 복원

새 세션에서 `//oppd` 호출 시:
1. `tasks/` 하위에 `*-oppd-*` 패턴의 폴더가 있는지 확인한다
2. **존재하면**: STATE.md Read → 현재 Phase와 상태를 파악 → 정확한 지점에서 재개
3. **미존재**: 사전 조건 체크부터 시작한다

---

## 파이프라인

```
사전 조건 체크 → 태스크 생성 (TASK.md + STATE.md)
  → Phase 1: opwt "작성" 모드로 PRD/TRD 작성(tasks/{NNN}-oppd-…/) → 사용자 확정 → docs/ 승격
  → Phase 2: PM 직접 WBS 수립(tasks/{NNN}-oppd-…/) → PM 검수 → 사용자 확정
  → [--wbs 플래그 있음] → Phase 1~2 완료 후 종료 (Phase 3 실행 없음)
  → Phase 3: opal-task-action-agent로 액션 자율 실행 (순차 + 병렬) → 각 액션 PM 검수 → 전체 완료
  → DONE.md 작성
```

### 플래그

| 플래그 | 설명 |
|--------|------|
| `--wbs` | Phase 1(PRD/TRD) + Phase 2(WBS) 완료 후 파이프라인 종료. Phase 3 액션 실행을 건너뛴다. WBS 산출물만 확정하고 종료할 때 사용. `--agentic`과 조합 가능 (`//oppd --wbs --agentic`). |
| `--agentic` | 전 Phase 사용자 게이트를 PM이 대행. opal-harness-agentic.md 참조. |

---

## Phase 1: 기획 산출물 작성 (opwt 위임)

PRD와 TRD를 opwt(기획 산출물 네트워크 오케스트레이터)에 위임한다.

### 1-1. opwt 호출

opwt를 "작성" 모드로 호출한다:

```
//opwt 작성
- 대상 문서: PRD, TRD
- 출력 경로: tasks/{NNN}-oppd-{프로젝트명}/PRD.md, tasks/{NNN}-oppd-{프로젝트명}/TRD.md (작업본)
- 프로젝트 컨텍스트: docs/PROJECT.md, docs/ARCHITECTURE.md
- 사용자 요청: {원래 요청 텍스트}
```

opwt가 자체 Phase 1~4(병렬 분석 → PM 진단 → 병렬 작성 → 정합성 검증)를 수행한다.
oppd PM은 opwt의 정합성 검증(Phase 4) 결과를 신뢰한다.

### 1-1b. SDD 명세 검증 (op-spec-validator 디스패치)

opwt 완료 후, PM이 `op-spec-validator` 에이전트를 디스패치하여 PRD/TRD 명세 완성도를 검증한다.
**이 단계를 통과하지 않으면 1-2 사용자 확정으로 진행하지 않는다.**

#### 디스패치 형식

op-spec-validator 에이전트에 아래 정보를 전달한다:

```
검증 요청:
- PRD 경로: tasks/{NNN}-oppd-{프로젝트명}/PRD.md (작업본)
- TRD 경로: tasks/{NNN}-oppd-{프로젝트명}/TRD.md (작업본)
- 검증 대상: ALL
```

#### 결과 수신 및 처리

에이전트가 반환하는 구조화 결과(종합 판정 + 상세 결과)를 수신한다.

| 판정 | 처리 |
|------|------|
| 종합 Pass | 1-2 사용자 확정으로 진행 |
| PRD Fail | opwt "수정" 모드 재호출 — Fail 항목의 수정 제안을 `이슈`로 전달 |
| TRD Fail | opwt "수정" 모드 재호출 — Fail 항목의 수정 제안을 `이슈`로 전달 |
| PRD+TRD 모두 Fail | opwt "수정" 모드 재호출 — 두 문서의 Fail 항목을 통합 전달 |

#### Fail 시 opwt 재호출 형식

```
//opwt 수정
- 대상 문서: {PRD | TRD | PRD, TRD}
- 이슈:
  - [P{번호}] {항목명}: {Fail 사유} → 제안: {수정 제안}
  - [T{번호}] {항목명}: {Fail 사유} → 제안: {수정 제안}
- 참조 문서: docs/PROJECT.md, docs/ARCHITECTURE.md
```

opwt 재작성 완료 후 op-spec-validator를 재디스패치한다. (무한루프 방지: 최대 2회)
2회 Fail 시 미통과 항목을 사용자에게 보고하고 판단을 요청한다.

### 1-2. 사용자 확정

opwt 완료 후, PM이 결과를 종합하여 사용자에게 보고한다:

```
---
[Phase 1] 기획 산출물 완료 — 사용자 검토 요청

산출물 (작업본):
- tasks/{NNN}-oppd-{프로젝트명}/PRD.md (제품 요구사항)
- tasks/{NNN}-oppd-{프로젝트명}/TRD.md (기술 요구사항)

{PRD/TRD 핵심 요약}

검토 후 확정 / 피드백을 알려주세요.
확정 시 docs/ 승격 및 후속 조치를 수행합니다.
---
```

| 사용자 응답 | 동작 |
|----------|------|
| 확정 / 승인 | 후속 조치 수행 후 Phase 2 진행 |
| 피드백 | opwt "수정" 모드로 재호출 → 재보고 |

### 1-3. 사용자 확정 후 후속 조치 — docs/ 승격 단계 (필수)

#### 승격 판단 (PM 자동)

`docs/PRD.md`·`docs/TRD.md` 존재 여부로 승격 방식을 결정한다:

| 조건 | 방식 | 동작 |
|------|------|------|
| `docs/PRD.md` 미존재 | **greenfield** | 작업본(tasks/{NNN}-oppd-…/PRD.md·TRD.md) 전체를 docs/로 복사 |
| `docs/PRD.md` 존재 | **반복(델타 병합)** | 작업본의 변경 델타를 기존 docs/PRD.md·TRD.md에 병합 |

#### 승격 대상

1. **PRD/TRD 본문 승격**: 작업본(`tasks/{NNN}-oppd-…/PRD.md`, `TRD.md`) → `docs/PRD.md`, `docs/TRD.md` (greenfield: 전체 복사 / 반복: 델타 병합)
2. **`docs/PROJECT.md` 문서 테이블 등록**: PRD.md, TRD.md를 등록한다
3. **`docs/ARCHITECTURE.md` delta**: TRD에서 확정된 기술 스택 버전을 반영한다

#### 세션/STATE 갱신 (유지)

4. STATE.md Phase 진행 현황 갱신 (Phase 1 → 확정) — state-tool을 호출한다:
   ```
   ~/.opal/tools/state-tool/run.sh mark <task-path> --row <Phase1_확정_행N> --done --owner user --note '{owner_name} 확인: Phase 1 확정'
   ```
5. `.opal/MEMORY.md`의 작업 히스토리를 갱신한다

---

## Phase 2: WBS 수립 (PM 직접)

태스크를 분할하고 실행 순서를 결정한다.

### 2-1. 사전 준비

다음 파일을 반드시 Read한다:

- `~/.opal/skills/opal-pilot-project-dev/references/wbs-guide.md` — WBS 구조 및 체크리스트
- `~/.opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` — 자동 검증 루핑 전략
- `~/.opal/skills/opal-pilot-project-dev/references/parallel-execution-guide.md` — 병렬 실행 전략
- `docs/PRD.md` — 우선순위 매트릭스
- `docs/TRD.md` — 기술 의존성
- `docs/ARCHITECTURE.md` — 시스템 구조 (있으면)

### 2-2. 태스크 분할

PRD/TRD를 기반으로 태스크를 분할한다.

**분할 원칙**:
1. 독립 실행 가능한 단위로 분할한다
2. 의존성 방향: 하위 레이어 → 상위 레이어 (DB → API → UI)
3. Must 우선순위부터 배치한다
4. 하나의 액션은 단일 책임 + 단일 수용 시나리오로 독립 검증 가능한 단위로 분할한다 (둘 이상 책임/수용 기준 섞이면 재분할, 관찰 동작 없는 헬퍼·타입 단독이면 흡수)
5. 각 태스크에 적합한 스킬을 판단한다 (아래 스킬 판단 기준 참조)
6. 각 태스크의 성공/실패를 lint/build/test로 기계적으로 판정할 수 있는 단위로 분할한다 (자동 테스트 가능성)

분할된 태스크를 **"액션(action)"**으로 명명하고, `A{NN}-{name}` 형식으로 채번한다.
`A{NN}`: 2자리 순번, oppd 태스크 스코프 내에서만 유효.

**스킬 판단 기준**:

| 조건 | 스킬 |
|------|------|
| 코드 변경 10+ 파일, 다중 모듈 | `//opd` (Full Task) |
| 코드 변경 <10 파일, 단일 모듈 | `//opds` (Short Task) |
| 와이어프레임 + UI 구현 | `//opdw` (Wireframe) |

### 2-3. PM 검수

1. wbs-guide.md의 PM 검수 체크리스트를 1:1 대조한다
2. PRD의 모든 Must 기능이 태스크로 분할되었는지 확인한다
3. 의존성 순서가 올바른지 확인한다 (하위 먼저)
4. 각 태스크의 스킬 판단이 적절한지 확인한다
5. 아래 4종 기준을 각 액션에 대해 대조한다:
   - [ ] 각 액션이 **단일 책임**인가 — 두 개 이상의 독립 책임이 섞이면 재분할
   - [ ] 각 액션에 **구체 수용 시나리오**가 있는가 — generic 검증 명령(`npm test` 단독 등) 금지
   - [ ] 병렬 그룹마다 **통합 액션**이 존재하는가 — 머지 후 E2E/계약 검증 담당
   - [ ] **너무 큼/작음** 판정 신호에 걸리는 액션이 없는가 (wbs-guide 분할 원칙 참조)
6. **미달 시**: 자체 재작성 (최대 1회)
7. **통과 시**: 사용자 검토 요청

### 2-4. 사용자 확정

```
---
[WBS] PM 검수 통과 — 사용자 검토 요청

산출물: tasks/{NNN}-oppd-{프로젝트명}/WBS.md (태스크 폴더 전용)

{WBS 요약: 총 액션 수, Work Package 수, 마일스톤 등}

액션 목록:
| # | WP | 액션 | 스킬 | 의존성 | 우선순위 | 검증 명령 | 상태 |
|---|-----|------|------|--------|---------|----------|------|
| A01 | WP1 | DB 스키마 | //opds | - | Must | npm run lint:fix && npm test | 미시작 |
| A02 | WP2 | 인증 API | //opds | A01 | Must | npm run lint:fix && npm test | 미시작 |
| ... | ... | ... | ... | ... | ... | ... | ... |

검토 후 확정 / 피드백을 알려주세요.
---
```

### 2-5. 사용자 확정 후 후속 조치 (필수)

> WBS.md는 태스크 폴더 전용(`tasks/{NNN}-oppd-…/WBS.md`) 실행 산출물이며 docs/ 승격 대상이 아니다.

1. STATE.md Phase 진행 현황 갱신 (Phase 2 → 확정) — state-tool을 호출한다:
   ```
   ~/.opal/tools/state-tool/run.sh mark <task-path> --row <Phase2_확정_행N> --done --owner user --note '{owner_name} 확인: Phase 2 확정'
   ```
2. `.opal/MEMORY.md`의 작업 히스토리를 갱신한다

---

## Phase 3: 액션 실행 (opal-task-action-agent 위임)

의존성 그래프 기반으로 opal-task-action-agent를 디스패치하여 액션을 자율 실행한다 (순차 + 병렬 혼합).
에이전트는 PLAN → QA → TEST-SCENARIO → EXECUTE → VERIFY → TEST 파이프라인을 사용자 개입 없이 완주하고 결과를 반환한다.

### 3-0. 의존성 최신 검증 (Phase 3 시작 전)

TRD에서 확정한 기술 스택 버전이 아직 유효한지 재검증한다.

```
Phase 3 시작 전:
  1. docs/TRD.md의 기술 스택 목록 확인
  2. 핵심 라이브러리별 웹 검색:
     - 새 메이저 버전 릴리즈 여부
     - deprecation 공지 여부
     - 보안 취약점 패치 여부
  3. 변경 필요 시:
     → 사용자에게 보고 → TRD + ARCHITECTURE.md 갱신 후 진행
  4. 변경 없으면 그대로 진행
```

### 3-1. 실행 루프

확정된 `tasks/{NNN}-oppd-…/WBS.md`의 의존성 그래프를 기반으로, 순차 + 병렬 혼합으로 진행한다:

```
groups = buildParallelGroups(WBS.actions)  # 의존성 그래프 → 실행 그룹

for each group in groups:
  if group.type == "sequential":
    1. 사용자에게 액션 시작 보고
    2. opal-task-action-agent를 Agent 도구로 디스패치:
       프롬프트에 포함할 파라미터:
       - [WORKER] (프롬프트 첫 줄 — 부트스트랩 생략 마커)
       - action_id: A{NN}-{name}
       - action_goal: WBS.md에서 추출한 액션 목표
       - action_scope: WBS.md에서 추출한 변경 범위
       - verify_commands: WBS.md에서 추출한 검증 명령
       - task_folder: actions/A{NN}-{name}/
       - project_root: {프로젝트 루트}
       - project_context: [docs/PROJECT.md, docs/ARCHITECTURE.md, docs/CONVENTIONS.md]
       - harness_guards: "PLAN.md에 없는 파일 생성/수정 금지. PLAN 설계를 임의 변경 금지. 블로커 발생 시 즉시 중단 후 보고."
       - reference_docs: {docs/PROJECT.md 문서 테이블 기반 현재 액션 관련 문서 경로}
    3. 에이전트 결과 수신 → 결과 처리 (아래 참조)
    4. PM 검수 (완료 산출물 확인)
    5. 사용자에게 액션 완료 보고
    6. STATE.md Phase 3 행 갱신 — state-tool을 호출한다:
       ```
       ~/.opal/tools/state-tool/run.sh mark <task-path> --row <Phase3_액션_행N> --done --note 'A{NN} 완료'
       ```

  if group.type == "parallel":
    1. 사용자에게 병렬 그룹 시작 보고
    2. 병렬 액션 실행 (3-1b)
    3. 전체 머지 + 통합 테스트
    4. PM 검수 (그룹 단위)
    5. 사용자에게 그룹 완료 보고
    6. STATE.md 병렬 그룹 행 갱신 — state-tool을 호출한다:
       ```
       ~/.opal/tools/state-tool/run.sh mark <task-path> --row <그룹_행N> --done --note '그룹 완료'
       ```
```

#### 에이전트 결과 처리

opal-task-action-agent는 `status`와 `verdict`를 반환한다:

| status | verdict | 동작 |
|--------|---------|------|
| `completed` | `All Pass` | PM 검수 → 다음 액션 |
| `completed` | `Partial Fail` | PM 검수 → 사용자에게 Partial Fail 사실 보고 후 판단 |
| `failed` | `Critical Fail` | `failure_context.scope`로 분기 처리 (아래 참조) |
| `failed` | - | `failure_context.scope`로 분기 처리 (아래 참조) |

에이전트가 반환하는 `verification_log`는 STATE.md의 "검증 루프 로그" 섹션에 기록한다.

#### failure_context.scope별 PM 처리 분기

에이전트가 `status: failed`를 반환하면, `failure_context.scope` 값에 따라 PM이 분기 처리한다:

| scope | 의미 | PM 처리 |
|-------|------|---------|
| `action` | 액션-로컬 설계 결함 — 에이전트가 자율 재PLAN 시도 완료 | 재PLAN 결과 확인 후 보고 (에이전트가 이미 처리) |
| `wbs` | WBS scope·인터페이스에 영향 | **WBS 2단 기준** 적용 (아래 참조) |
| `trd` | TRD·PRD 변경 필요 | **항상 사용자 에스컬레이션** — PM 자율 결정 불가 |

**WBS 2단 기준** (`scope: wbs` 수신 시):

| 변경 성격 | 판단 주체 | 처리 방법 |
|---------|---------|---------|
| scope·인터페이스 **불변** 조정 (구현 방식 조정, 순서 변경 등) | PM 자율 | WBS 직접 조정 + AGENTIC-LOG.md에 `GATE` 엔트리 기록 |
| scope·기능 **변경** (새 액션 추가, 기능 범위 확대, 인터페이스 변경) | 사용자 | 사용자에게 에스컬레이션 (`failure_context` 포함) |

**TRD/PRD 사용자 게이트** (`scope: trd` 수신 시):
- [MUST] TRD·PRD 변경은 항상 사용자 게이트 — PM이 자율로 결정하지 않는다 (citation-rules §7.5)
- 에스컬레이션 시 `failure_context` 전체를 포함하여 보고한다

**소유권 규칙**:
- `PLAN.md`: 액션 에이전트 소관 (재설계 루프 내 자율 수정 가능)
- `WBS.md`: PM 소관 (에이전트가 직접 수정 불가)
- `TRD.md`·`PRD.md`: 사용자 소관 (항상 사용자 게이트)

### 3-1a. 자동 검증 루핑

**opal-task-action-agent가 자체적으로 검증 루핑을 수행한다.** oppd는 에이전트의 `verification_log`를 STATE.md에 기록만 한다.

상세 전략은 `references/verification-loop-guide.md` 참조.

**에이전트 내부 루프** (oppd가 아닌 에이전트 내부에서 실행됨):

```
EXECUTE 완료
  → L1: lint/format 검증  → FAIL → 에이전트가 워커에 수정 지시 (제한 없음)
  → L2: build/type 검증   → FAIL → 에이전트가 워커에 수정 지시 (최대 2회)
  → L3a: unit/integration → FAIL → 에이전트가 워커에 수정 지시 (최대 3회)
  → L3b: E2E (해당 시)    → FAIL → 1회 재실행 → 2연속 FAIL → status: failed 반환
  → 전체 PASS → TEST 단계 → 결과 반환
```

**oppd의 역할**:
- 에이전트 결과의 `verification_log`를 STATE.md "검증 루프 로그" 섹션에 기록
- `status: failed` 수신 시 `failure_context`를 포함하여 사용자에게 에스컬레이션
- 에이전트 성공 시 PM 검수 진행

**핵심 규칙**:
- 하위 계층 통과 후에만 상위 계층으로 진행 (L1 → L2 → L3a → L3b)
- **L3b(E2E)**: WBS.md에 E2E 검증 명령이 명시된 액션에만 실행. 병렬 그룹에서는 머지 후 일괄 실행도 가능
- **회귀 방지**: 에이전트가 자동 수정 후 이전 통과 테스트 재실행. 회귀 발생 시 루프 즉시 중단 + `status: failed` 반환
- **에스컬레이션**: 에이전트가 `status: failed`로 반환 → oppd가 사용자에게 보고 (하네스 "자동 루핑 제약" Guards 준수)

### 3-1b. 병렬 액션 실행

의존성이 없는 액션을 worktree 격리 + opal-task-action-agent 병렬 디스패치로 동시 실행한다.
상세 전략은 `references/parallel-execution-guide.md` 참조.

**실행 요약**:

```
1. worktree 생성: .worktrees/{action-id}/ (각 액션 격리)
2. Agent 도구로 opal-task-action-agent를 병렬 디스패치 (각 worktree에서 독립 실행)
   - 디스패치 프롬프트 첫 줄에 [WORKER] 삽입 (부트스트랩 생략 마커)
   - 디스패치 프롬프트에 project_root를 worktree 경로로 설정
   - 나머지 파라미터(action_id, action_goal 등)는 순차 실행과 동일
   - harness_guards 및 reference_docs도 동일하게 포함
3. 각 에이전트 결과 수집 (status, verdict, verification_log, changed_files)
4. 결과 수집 후 순차 머지 (변경 범위 작은 순)
5. 머지마다 통합 테스트 실행
6. worktree 정리
```

**핵심 규칙**:
- **오케스트레이터 단독 갱신**: STATE.md는 오케스트레이터(oppd)만 갱신 (동시 쓰기 충돌 방지)
- **에이전트 결과 처리**: 각 에이전트의 결과를 개별적으로 처리 (3-1 "에이전트 결과 처리" 참조)
- **머지 충돌 시**: PM이 조정 (자동 해결 가능 → 직접 해결, 설계 판단 필요 → 사용자 에스컬레이션)
- **Fallback**: worktree/Agent 도구 미지원 시 순차 실행으로 폴백 (parallel-execution-guide.md §7 "STATE.md 갱신" 참조)

### 3-2. 액션 시작/완료 보고

```
[Phase 3] 액션 {N}/{M} 시작
액션: {액션 제목} | 에이전트: opal-task-action-agent
```

```
[Phase 3] 액션 {N}/{M} 완료
결과: {완료 요약} | 남은: {M-N}개
다음 액션으로 넘어갈까요?
```

### 3-3. 전체 완료 보고

```
---
oppd 완료

프로젝트: {프로젝트명}

완료 산출물:
- docs/PRD.md (Phase 1 - opwt, 승격)
- docs/TRD.md (Phase 1 - opwt, 승격)
- tasks/{NNN}-oppd-…/WBS.md (Phase 2, 태스크 폴더 전용)
- {Phase 3 액션 목록 및 결과}

전체 {M}개 액션 완료.
---
```

---

## PM 검수 흐름 (각 Phase 공통)

```
산출물 생성 (opwt/opal-task-action-agent 또는 PM 직접)
  │
  ▼
PM 검수
  │  .opal/AGENT.md 검토 기준 적용
  │  참조 문서(docs/) 정합성 확인
  │
  ├─ 미달 → 재지시 또는 자체 재작성 (최대 1회)
  │
  └─ 통과 → 사용자 검토 요청
              │
              ├─ 사용자 피드백 → 반영 → PM 재검수
              └─ 사용자 확정 → 다음 Phase
```

### PM 검수 → 학습 루프 연결

PM 검수 로그에서 **반복 패턴**이 감지되면 PM 학습 루프로 승격:
- 동일 유형의 Fail이 2회 이상 반복
- 사용자 피드백에서 새로운 원칙 도출
- 사용자 승인 시 `.opal/AGENT.md` "확정 기준"에 추가

---

## STATE.md 관리

`tasks/{NNN}-oppd-{프로젝트명}/STATE.md`에 관리한다.

### STATE.md 템플릿

```markdown
# STATE: {프로젝트명} 개발 파일럿

> 최종 갱신: YYYY-MM-DD HH:mm

## 현재 상태
- 스킬: //oppd
- Phase: {1-PLAN(PRD/TRD) / 2-WBS / 3-EXECUTE}
- 상태: {진행 중 / PM 검수 / 사용자 검토 대기 / 완료}

## Phase 진행 현황
| Phase | 방식 | 산출물 | 상태 |
|-------|------|--------|------|
| 1-PLAN | opwt | tasks/{NNN}-oppd-…/PRD.md·TRD.md (작업본) → 확정 후 docs/ 승격 | {미시작 / opwt 진행 / 사용자 검토 / 확정} |
| 2-WBS | PM 직접 | tasks/{NNN}-oppd-…/WBS.md (태스크 폴더 전용) | {미시작 / 작성 중 / PM 검수 / 사용자 검토 / 확정} |
| 3-EXECUTE | opal-task-action-agent | - | {미시작 / A{N}/{M} 진행 중 / 완료} |

## WBS 액션 (Phase 2 확정 후)
> 액션별 상태/완료일시는 tasks/{NNN}-oppd-…/WBS.md에서 관리한다.
| # | WP | 액션 | 스킬 | actions/ 경로 |
|---|-----|------|------|-------------|

## 병렬 실행 현황

### 그룹 요약
| 그룹 | 액션 수 | 완료 | 실패 | 그룹 상태 |
|------|--------|------|------|----------|

### 액션 상세
| 그룹 | 액션 | worktree | 브랜치 | 상태 |
|------|------|----------|--------|------|

### 머지 이력
| # | 그룹 | 머지 순서 | 충돌 여부 | 통합 테스트 | 머지 시점 |
|---|------|----------|----------|-----------|----------|

## 검증 루프 로그
| # | 액션 | 검증 유형 | 시도 | 결과 | 오류 요약 | 시점 |
|---|------|----------|------|------|----------|------|

## 재설계 루프 로그
| # | 액션 | triage 결과 | 재PLAN 횟수 | scope | 시점 |
|---|------|-----------|-----------|-------|------|

## PM 검수 로그
| # | Phase | 검수 결과 | 지시 내용 | 반영 여부 |
|---|-------|----------|----------|----------|

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|
```

---

## DONE.md 작성

모든 Phase 완료 후 DONE.md를 작성한다.

```markdown
# DONE: {프로젝트명} 개발 파일럿

> 완료일: YYYY-MM-DD | 스킬: //oppd

## 생성 문서

| 문서 | Phase | 방식 | 확정일 |
|------|-------|------|--------|
| docs/PRD.md | 1 | opwt (승격) | YYYY-MM-DD |
| docs/TRD.md | 1 | opwt (승격) | YYYY-MM-DD |
| tasks/{NNN}-oppd-…/WBS.md | 2 | PM 직접 (태스크 폴더 전용) | YYYY-MM-DD |

## 실행 액션

| # | 액션 | 경로 | 스킬 | 결과 |
|---|------|------|------|------|
| A01 | {제목} | actions/A01-... | //opds | 완료 |
| A02 | {제목} | actions/A02-... | //opds | 완료 |

## 프로젝트 요약

{전체 개발 과정 요약, 특이사항, 다음 단계}
```

DONE.md 생성 직후 **op-brain-ingest 디스패치**를 수행한다:
- `<프로젝트-루트>/.opal/brain/` 존재 여부를 확인한다.
- **brain이 존재하면**: op-brain-ingest 워커를 디스패치하여 태스크 산출물(DONE.md·PLAN 결정·신규 엔티티)을 brain에 누적한다.
- **brain이 없으면**: 자연 스킵(no-op). 종료가 막히지 않는다.
- op-brain-ingest 탐색 경로:
  1. `{프로젝트}/.opal/skills/op-brain-ingest/SKILL.md`
  2. `~/.opal/skills/op-brain-ingest/SKILL.md`
- 디스패치 입력: 태스크 폴더 경로
- 워커가 `status: skipped` 또는 `status: completed` 또는 `status: completed_with_errors` 반환 — 어떤 경우도 종료를 중단시키지 않는다.

---

## 문서 등록 프로토콜

각 Phase에서 산출물이 확정되면 `docs/PROJECT.md`의 프로젝트 문서 테이블에 등록한다.

| Phase | 산출물 | 등록 설명 |
|-------|--------|----------|
| 1 | `docs/PRD.md` | 제품 요구사항 정의서 (작업본 → 사용자 확정 후 docs/ 승격) |
| 1 | `docs/TRD.md` | 기술 요구사항 정의서 (작업본 → 사용자 확정 후 docs/ 승격) |

> WBS.md는 태스크 폴더 전용(`tasks/{NNN}-oppd-…/WBS.md`)으로 docs/ 등록 대상이 아니다.

---

## 스킬 탐색 경로

**opi (사전 조건 미충족 시)**:
1. `{프로젝트}/.opal/skills/opal-project-init/SKILL.md`
2. `~/.opal/skills/opal-project-init/SKILL.md`

**opwt (Phase 1 기획 산출물)**:
1. `{프로젝트}/.opal/skills/opal-pilot-write-tech/SKILL.md`
2. `~/.opal/skills/opal-pilot-write-tech/SKILL.md`

**opal-task-action-agent (Phase 3 액션 자율 실행)**:
1. `{프로젝트}/.opal/agents/opal-task-action-agent/AGENT.md`
2. `~/.opal/agents/opal-task-action-agent/AGENT.md`

**opd/opds/opdw (독립 호출 시 — 사용자 `//` 커맨드)**:
1. `{프로젝트}/.opal/skills/opal-pilot-dev/SKILL.md` (Full Task)
2. `~/.opal/skills/opal-pilot-dev/SKILL.md`
3. `{프로젝트}/.opal/skills/opal-pilot-dev-short/SKILL.md` (Short Task)
4. `~/.opal/skills/opal-pilot-dev-short/SKILL.md`
5. `{프로젝트}/.opal/skills/opal-pilot-dev-wireframe/SKILL.md` (Wireframe)
6. `~/.opal/skills/opal-pilot-dev-wireframe/SKILL.md`

---

## 프로젝트 메모리 동기화

`{프로젝트}/.opal/MEMORY.md`가 존재하면, Phase 전환 시 작업 히스토리를 갱신한다:

- Phase 완료: `단계` 컬럼 → `Phase {N} 확정 → Phase {N+1} 대기`
- 전체 완료: `단계` 컬럼 → `완료`

---

## Agentic / Semi-Agentic 모드

opal-harness-agentic.md / opal-harness-semi-agentic.md 참조. 본 절은 이 스킬의 차이점만 기술한다.

### 기본 모드 (semi-agentic)

기본 호출(`//oppd {작업}`)은 semi-agentic 모드. Phase 1+2(PLAN-equivalent)까지 사용자 검토, Phase 3 이후(EXECUTE-equivalent) PM 자율, CLOSE 진입은 사용자 승인 필수.

**모드 경계** (이 시점부터 PM 자율):
- Phase 2 WBS 사용자 확정 행 통과 후 → Phase 3 액션 실행 첫 행부터 PM 자율 (D-DEC-1)
- Phase 1 내부 opwt 위임 결과(PRD/TRD)는 Phase 1 사용자 확정 행에서 검토 — 별도 모드 경계 없음

### 명시 모드

| 호출 | 모드 |
|------|------|
| `//oppd 작업` | semi-agentic (기본) |
| `//oppd --interactive 작업` | interactive — 모든 단계 사용자 승인 |
| `//oppd --agentic 작업` | agentic — 모든 단계 PM 자율 (CLOSE 진입 제외) |
| `//oppd --wbs 작업` | `--wbs` 플래그와 조합 가능 |

### 자율 게이트 흐름 (semi-agentic)

```
Phase 1 Gate → Phase 2 Gate → Phase 3 (액션 내부 Gate + 액션 간 Gate)
사용자 승인     사용자 승인     PM 자율 검토
               (모드 경계)
```

#### Phase 1~2: 사용자 검토 (semi-agentic)

- Phase 1 (opwt 결과): 사용자가 PRD/TRD 품질을 검토·확정 후 → Phase 2 진행
- Phase 2 (WBS): 사용자가 WBS를 검토·확정 후 → Phase 3 진행 (이 시점부터 PM 자율)

#### Phase 1~2: 사용자 확정 게이트 대행 (agentic 전용)

- Phase 1 (opwt 결과): PM이 PRD/TRD 품질을 검토하여 자율 확정 → Phase 2 진행
- Phase 2 (WBS): PM이 WBS를 검수하여 자율 확정 → Phase 3 진행

#### Phase 3: 액션 실행

- **액션 내부**: 각 액션이 opds 파이프라인(TASK→PLAN→EXECUTE)이므로, 액션 내 각 Gate에도 **opal-harness-agentic.md "Gate 루핑 규칙"** 동일 적용
- **액션 간 게이트**: PM이 각 액션 결과를 검수하여 자율 승인 → 다음 액션 진행
  - interactive에서는 "다음 액션으로 넘어갈까요?" 사용자 게이트 → agentic/semi-agentic(Phase 3)에서는 PM이 대행
  - 각 액션 완료 시 AGENTIC-LOG.md에 `GATE` 엔트리 기록
  - 액션 실패(status: failed) 시에도 PM이 판단: 재시도 가능 → `FIX` + 재디스패치, 불가 → `ESCALATION`

### CLOSE 진입 게이트 (공통)

semi-agentic / agentic 모두 CLOSE 첫 행 `--auto-pass` 거부 (`agentic_close_gate_requires_user`). 소유자 발화 후 직전 사용자 확인 행 `--owner user` mark 필수.

### AGENTIC-LOG.md 생성 시점

- agentic: TASK 시작 시점
- semi-agentic: Phase 3 첫 액션 행 advance 시점에 PM이 생성

### oppd 고유 에스컬레이션 조건

opal-harness-agentic.md "에스컬레이션 조건" 공통 기준에 추가:
- PRD/TRD에서 사용자 비즈니스 판단이 필요한 경우
- 액션 Critical Fail로 전체 WBS 재조정이 필요한 경우

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-03-26 | 초기 작성 — 4 Phase 파이프라인 (PRD/TRD/ROADMAP/EXECUTE) |
| v2.0 | 2026-03-30 | opal-project-dev-pilot → opal-pilot-project-dev 리네이밍. Phase 1~2(PRD/TRD)를 opwt 위임으로 전환. 4→3 Phase 슬림화 (052) |
| v3.0 | 2026-03-30 | agentic 자율 루핑 + 병렬 실행 + actions 구조 (053) |
| v3.1 | 2026-03-30 | Phase 3 opd/opds 호출 → opal-task-action-agent 디스패치로 전환 (056) |
| v3.2 | 2026-03-31 | Agentic Mode 섹션 추가 — 전 Phase 적용 (057) |
| v3.3 | 2026-03-31 | §7 참조 → opal-harness-agentic.md 참조 전환 (058) |
| v3.4 | 2026-04-01 | Phase 3 opal-task-action-agent 디스패치 프롬프트에 `[WORKER]` 마커 + harness_guards + reference_docs 파라미터 추가 (063) |
| v4.0 | 2026-04-02 | ROADMAP → WBS 전면 전환. Phase 2 명칭·산출물·참조 변경. Work Package 계층 도입. `--wbs` 플래그 추가. STATE.md 템플릿 경량화 (액션 상태 추적을 WBS.md로 이관) (075) |
| v4.1 | 2026-04-24 | citation-rules 트리거 1줄 주입 — SSOT + Trigger 패턴 (130) |
| v4.2 | 2026-05-01 | state-tool 도입 — STATE.md 직접 편집 금지 + `state-tool` 호출 표현 교체 (P-1~P-8 패턴 적용). 태스크 생성 init 호출 + `--rows-from` SSOT. R-10 비표준 행 구성 `gate-pass` 금지 + mark 4회 개별 호출 필수 블록 추가. Phase 1~3 각 확정/완료 시 mark 호출 명시 (134) |
| v4.3 | 2026-05-09 11:22 | 3-way 모드 체계 도입 — semi-agentic 기본 채택 + Agentic/Semi-Agentic 모드 절 확장 + Phase 2 WBS 모드 경계 명시(D-DEC-1) + Harness 절 3-way 분기 + state init --mode 추가 (140) |
| v4.4 | 2026-05-09 18:30 | 개인 식별자 "캡틴" → "소유자"/"사용자" 치환 — 배포 파일 정체성 누설 정정 (139) |
| v4.5 | 2026-06-07 | R-10 gate-pass deprecated 정합 — State Gate/QA Gate 행 미존재 명시 + PM Gate 단일 mark로 간소화 (014 Phase 4) |
| v4.6 | 2026-06-11 19:25 | DONE.md 생성 직후 op-brain-ingest 디스패치 훅 삽입 — brain 존재 시 워커 디스패치, 부재 시 no-op, 종료 비중단 (016) |
| v4.7 | 2026-06-21 16:05 | oppd 개선 — PRD/TRD 태스크폴더 작성+확정 후 docs 승격(F-001/002), WBS 태스크폴더 전용화(F-003), sizing "1~3일"→단일책임+수용시나리오(F-010), §2-3 PM검수 4종 추가(F-015), Phase3 scope 3계층 분기+WBS 2단기준+TRD/PRD 사용자게이트(F-023/024), STATE 재설계 루프 로그 행(F-024) (031) |
| v4.8 | 2026-06-21 | `npm run lint` → `npm run lint:fix` 정합 — WBS 예시 표(A01·A02) generic `&&` 변형의 lint 명령을 L1 표준(`lint:fix`)으로 교체 (033) |
| v4.9 | 2026-07-10 13:12 | note 예시의 소유자 확인 표기를 `{owner_name} 확인:` 형식으로 통일 — identity.md owner_name 재해석 규칙(AGENT.md §정체성 적용)과 정합, 오염 차단 (054) |
