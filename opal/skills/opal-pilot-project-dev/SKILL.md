---
name: opal-pilot-project-dev
description: |
  **프로젝트 개발 라이프사이클 오케스트레이터**. 아이디어부터 개발 완료(product)까지
  opwt로 기획 산출물(PRD/TRD) 작성 → 로드맵 수립 → opal-task-action-agent로 액션 자율 실행.
  모든 산출물은 PM 검수 → 사용자 확정 순서를 거친다.
  opi 없이 단독 호출도 가능 (docs/PROJECT.md 존재 시).
triggers:
  - "opal-pilot-project-dev"
  - "oppd"
  - "프로젝트 개발 시작"
  - "개발 계획"
  - "개발 파일럿"
version: 3.1.0
---

# opal-pilot-project-dev

아이디어부터 개발 완료(product)까지 전체 라이프사이클을 3 Phase 파이프라인으로 관리한다.
기획 산출물은 opwt에 위임하고, 코드 실행은 opal-task-action-agent에 위임하며, PM이 전체를 조율한다.

## Harness

모드: Project Dev (PLAN → ROADMAP → EXECUTE)
> 부트스트랩에서 로드되지 않은 경우: `~/.opal/references/opal-harness.md`를 Read한다.

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
| 1 | opwt 호출 | docs/PRD.md, docs/TRD.md | 기획 산출물 작성 (opwt "작성" 모드) |
| 2 | PM 직접 | docs/ROADMAP.md | 태스크 분할 + 로드맵 수립 |
| 3 | opal-task-action-agent 디스패치 | actions/A01~A{MM} | 액션 자율 실행 |
```

### STATE.md 초기 생성

아래 "STATE.md 관리" 섹션의 템플릿으로 생성한다.

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
  → Phase 1: opwt "작성" 모드로 PRD/TRD 작성 → 사용자 확정
  → Phase 2: PM 직접 로드맵 수립 → PM 검수 → 사용자 확정
  → Phase 3: opal-task-action-agent로 액션 자율 실행 (순차 + 병렬) → 각 액션 PM 검수 → 전체 완료
  → DONE.md 작성
```

---

## Phase 1: 기획 산출물 작성 (opwt 위임)

PRD와 TRD를 opwt(기획 산출물 네트워크 오케스트레이터)에 위임한다.

### 1-1. opwt 호출

opwt를 "작성" 모드로 호출한다:

```
//opwt 작성
- 대상 문서: PRD, TRD
- 프로젝트 컨텍스트: docs/PROJECT.md, docs/ARCHITECTURE.md
- 사용자 요청: {원래 요청 텍스트}
```

opwt가 자체 Phase 1~4(병렬 분석 → PM 진단 → 병렬 작성 → 정합성 검증)를 수행한다.
oppd PM은 opwt의 정합성 검증(Phase 4) 결과를 신뢰한다.

### 1-2. 사용자 확정

opwt 완료 후, PM이 결과를 종합하여 사용자에게 보고한다:

```
---
[Phase 1] 기획 산출물 완료 — 사용자 검토 요청

산출물:
- docs/PRD.md (제품 요구사항)
- docs/TRD.md (기술 요구사항)

{PRD/TRD 핵심 요약}

검토 후 확정 / 피드백을 알려주세요.
---
```

| 사용자 응답 | 동작 |
|----------|------|
| 확정 / 승인 | 후속 조치 수행 후 Phase 2 진행 |
| 피드백 | opwt "수정" 모드로 재호출 → 재보고 |

### 1-3. 사용자 확정 후 후속 조치 (필수)

1. `docs/PROJECT.md`의 문서 테이블에 PRD.md, TRD.md를 등록한다
2. `docs/ARCHITECTURE.md`를 업데이트한다 (TRD에서 확정된 기술 스택 버전 반영)
3. `STATE.md`를 갱신한다 (Phase 1 → 확정)
4. `.opal/MEMORY.md`의 작업 히스토리를 갱신한다

---

## Phase 2: 로드맵 수립 (PM 직접)

태스크를 분할하고 실행 순서를 결정한다.

### 2-1. 사전 준비

다음 파일을 반드시 Read한다:

- `~/.opal/skills/opal-pilot-project-dev/references/roadmap-guide.md` — 로드맵 구조 및 체크리스트
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
4. 하나의 태스크는 1~3일 분량이 적정하다
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

1. roadmap-guide.md의 PM 검수 체크리스트를 1:1 대조한다
2. PRD의 모든 Must 기능이 태스크로 분할되었는지 확인한다
3. 의존성 순서가 올바른지 확인한다 (하위 먼저)
4. 각 태스크의 스킬 판단이 적절한지 확인한다
5. **미달 시**: 자체 재작성 (최대 1회)
6. **통과 시**: 사용자 검토 요청

### 2-4. 사용자 확정

```
---
[ROADMAP] PM 검수 통과 — 사용자 검토 요청

산출물: docs/ROADMAP.md (초안)

{로드맵 요약: 총 액션 수, 마일스톤 등}

액션 목록:
| # | 액션 | 스킬 | 의존성 | 우선순위 | 검증 명령 |
|---|------|------|--------|---------|----------|
| A01 | DB 스키마 | //opds | - | Must | npm run lint && npm test |
| A02 | 인증 API | //opds | A01 | Must | npm run lint && npm test |
| ... | ... | ... | ... | ... | ... |

검토 후 확정 / 피드백을 알려주세요.
---
```

### 2-5. 사용자 확정 후 후속 조치 (필수)

1. `docs/PROJECT.md`의 문서 테이블에 ROADMAP.md를 등록한다
2. `STATE.md`를 갱신한다 (Phase 2 → 확정)
3. `.opal/MEMORY.md`의 작업 히스토리를 갱신한다

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

확정된 `docs/ROADMAP.md`의 의존성 그래프를 기반으로, 순차 + 병렬 혼합으로 진행한다:

```
groups = buildParallelGroups(ROADMAP.actions)  # 의존성 그래프 → 실행 그룹

for each group in groups:
  if group.type == "sequential":
    1. 사용자에게 액션 시작 보고
    2. opal-task-action-agent를 Agent 도구로 디스패치:
       프롬프트에 포함할 파라미터:
       - action_id: A{NN}-{name}
       - action_goal: ROADMAP.md에서 추출한 액션 목표
       - action_scope: ROADMAP.md에서 추출한 변경 범위
       - verify_commands: ROADMAP.md에서 추출한 검증 명령
       - task_folder: actions/A{NN}-{name}/
       - project_root: {프로젝트 루트}
       - project_context: [docs/PROJECT.md, docs/ARCHITECTURE.md, docs/CONVENTIONS.md]
    3. 에이전트 결과 수신 → 결과 처리 (아래 참조)
    4. PM 검수 (완료 산출물 확인)
    5. 사용자에게 액션 완료 보고
    6. STATE.md 갱신 (verification_log 기록 포함)

  if group.type == "parallel":
    1. 사용자에게 병렬 그룹 시작 보고
    2. 병렬 액션 실행 (3-1b)
    3. 전체 머지 + 통합 테스트
    4. PM 검수 (그룹 단위)
    5. 사용자에게 그룹 완료 보고
    6. STATE.md 갱신
```

#### 에이전트 결과 처리

opal-task-action-agent는 `status`와 `verdict`를 반환한다:

| status | verdict | 동작 |
|--------|---------|------|
| `completed` | `All Pass` | PM 검수 → 다음 액션 |
| `completed` | `Partial Fail` | PM 검수 → 사용자에게 Partial Fail 사실 보고 후 판단 |
| `failed` | `Critical Fail` | 사용자에게 에스컬레이션 (`failure_context` 포함) |
| `failed` | - | 사용자에게 에스컬레이션 (`failure_context` 포함) |

에이전트가 반환하는 `verification_log`는 STATE.md의 "검증 루프 로그" 섹션에 기록한다.

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
- **L3b(E2E)**: ROADMAP.md에 E2E 검증 명령이 명시된 액션에만 실행. 병렬 그룹에서는 머지 후 일괄 실행도 가능
- **회귀 방지**: 에이전트가 자동 수정 후 이전 통과 테스트 재실행. 회귀 발생 시 루프 즉시 중단 + `status: failed` 반환
- **에스컬레이션**: 에이전트가 `status: failed`로 반환 → oppd가 사용자에게 보고 (하네스 "자동 루핑 제약" Guards 준수)

### 3-1b. 병렬 액션 실행

의존성이 없는 액션을 worktree 격리 + opal-task-action-agent 병렬 디스패치로 동시 실행한다.
상세 전략은 `references/parallel-execution-guide.md` 참조.

**실행 요약**:

```
1. worktree 생성: .worktrees/{action-id}/ (각 액션 격리)
2. Agent 도구로 opal-task-action-agent를 병렬 디스패치 (각 worktree에서 독립 실행)
   - 디스패치 프롬프트에 project_root를 worktree 경로로 설정
   - 나머지 파라미터(action_id, action_goal 등)는 순차 실행과 동일
3. 각 에이전트 결과 수집 (status, verdict, verification_log, changed_files)
4. 결과 수집 후 순차 머지 (변경 범위 작은 순)
5. 머지마다 통합 테스트 실행
6. worktree 정리
```

**핵심 규칙**:
- **오케스트레이터 단독 갱신**: STATE.md는 오케스트레이터(oppd)만 갱신 (동시 쓰기 충돌 방지)
- **에이전트 결과 처리**: 각 에이전트의 결과를 개별적으로 처리 (3-1 "에이전트 결과 처리" 참조)
- **머지 충돌 시**: PM이 조정 (자동 해결 가능 → 직접 해결, 설계 판단 필요 → 사용자 에스컬레이션)
- **Fallback**: worktree/Agent 도구 미지원 시 순차 실행으로 폴백 (하네스 "병렬 실행 State" 참조)

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
- docs/PRD.md (Phase 1 - opwt)
- docs/TRD.md (Phase 1 - opwt)
- docs/ROADMAP.md (Phase 2)
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
- Phase: {1-PLAN(PRD/TRD) / 2-ROADMAP / 3-EXECUTE}
- 상태: {진행 중 / PM 검수 / 사용자 검토 대기 / 완료}

## Phase 진행 현황
| Phase | 방식 | 산출물 | 상태 |
|-------|------|--------|------|
| 1-PLAN | opwt | docs/PRD.md, docs/TRD.md | {미시작 / opwt 진행 / 사용자 검토 / 확정} |
| 2-ROADMAP | PM 직접 | docs/ROADMAP.md | {미시작 / 작성 중 / PM 검수 / 사용자 검토 / 확정} |
| 3-EXECUTE | opal-task-action-agent | - | {미시작 / A{N}/{M} 진행 중 / 완료} |

## 로드맵 (Phase 2 확정 후)
| # | 액션 | 스킬 | actions/ 경로 | 상태 |
|---|------|------|-------------|------|

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
| docs/PRD.md | 1 | opwt | YYYY-MM-DD |
| docs/TRD.md | 1 | opwt | YYYY-MM-DD |
| docs/ROADMAP.md | 2 | PM 직접 | YYYY-MM-DD |

## 실행 액션

| # | 액션 | 경로 | 스킬 | 결과 |
|---|------|------|------|------|
| A01 | {제목} | actions/A01-... | //opds | 완료 |
| A02 | {제목} | actions/A02-... | //opds | 완료 |

## 프로젝트 요약

{전체 개발 과정 요약, 특이사항, 다음 단계}
```

---

## 문서 등록 프로토콜

각 Phase에서 산출물이 확정되면 `docs/PROJECT.md`의 프로젝트 문서 테이블에 등록한다.

| Phase | 산출물 | 등록 설명 |
|-------|--------|----------|
| 1 | `docs/PRD.md` | 제품 요구사항 정의서 |
| 1 | `docs/TRD.md` | 기술 요구사항 정의서 |
| 2 | `docs/ROADMAP.md` | 개발 로드맵 (액션 분할 및 실행 순서) |

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

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-03-26 | 초기 작성 — 4 Phase 파이프라인 (PRD/TRD/ROADMAP/EXECUTE) |
| v2.0 | 2026-03-30 | opal-project-dev-pilot → opal-pilot-project-dev 리네이밍. Phase 1~2(PRD/TRD)를 opwt 위임으로 전환. 4→3 Phase 슬림화 (052) |
| v3.0 | 2026-03-30 | agentic 자율 루핑 + 병렬 실행 + actions 구조 (053) |
| v3.1 | 2026-03-30 | Phase 3 opd/opds 호출 → opal-task-action-agent 디스패치로 전환 (056) |
