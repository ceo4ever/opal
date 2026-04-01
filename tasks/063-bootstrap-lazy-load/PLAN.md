# PLAN: 부트스트랩 Eager/Lazy 재설계 + 서브에이전트 부트스트랩 생략

> 작성일: 2026-04-01
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `opal/core/AGENT.md` | 부트스트랩 절차 소스 (배포 원본) | **O (핵심)** |
| `~/.opal/AGENT.md` | 배포본 (install-mac.sh로 복사) | O (자동 — 소스 수정 후 재배포) |
| `scripts/install-mac.sh` | `opal/core/AGENT.md` → `~/.opal/AGENT.md` 복사 (L277) | X (기존 로직 유지) |
| `opal/skills/opal-pilot-project/SKILL.md` | opp 오케스트레이터 — 워커 디스패치 섹션 | **O** |
| `opal/skills/opal-pilot-dev/SKILL.md` | opd 오케스트레이터 — 워커 디스패치 프롬프트 | **O** |
| `opal/skills/opal-pilot-dev-short/SKILL.md` | opds 오케스트레이터 — 워커 디스패치 프롬프트 | **O** |
| `opal/skills/opal-pilot-write-tech/SKILL.md` | opwt 오케스트레이터 — 워커 프롬프트 (Phase 1/3) | **O** |
| `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | opdw 오케스트레이터 — 워커 디스패치 프롬프트 | **O** |
| `opal/skills/opal-pilot-project-dev/SKILL.md` | oppd 오케스트레이터 — opal-task-action-agent 디스패치 | **O** |

### 현재 부트스트랩 구조 (`opal/core/AGENT.md`)

| 단계 | 파일 | 동작 | PM 세션 필요 시점 |
|------|------|------|-----------------|
| 1 | `identity.md` | Read | **항상** |
| 2 | `opal-onboarding/SKILL.md` | Read (identity 없을 때) | 조건부 |
| 3 | `opal-harness.md` | Read | **항상** (Guards가 PM 세션 전체에 적용) |
| 4 | `skill-registry` (node) | node 실행 확인 | `//` 커맨드 시만 |
| 5 | `agents.md` + `mcps.md` | Read 2개 | 워커 디스패치 / MCP 시만 |
| 6 | `opal-model-mapping.md` | Read | 워커 디스패치 시만 |
| 7 | 부트스트래퍼 자동 삽입 | 파일 확인/삽입 | 한번만 |
| 8 | `.opal/AGENT.md` (PM) + `docs/PROJECT.md` | Read 1~2개 | PM 작업 시만 |
| 9 | `.opal/MEMORY.md` | Read | 프로젝트 진입 시 |
| 10 | 에이전트 활성화 | 로직 | 항상 |

**총 Read 횟수**: 매 세션 시작마다 최대 8~9회.

### 서브에이전트 부트스트랩 현황

현재 워커가 디스패치되면 플랫폼 부트스트래퍼(CLAUDE.md 등)를 통해 `~/.opal/AGENT.md`를 읽고 동일한 10단계 부트스트랩을 수행한다. `//opp` 하나에 PM + PLAN 워커 + QA 워커 + EXECUTE 워커가 각각 풀 부트스트랩을 실행 -- 대부분 워커에게 불필요하다.

### 워커 디스패치 프롬프트 현황

| 스킬 | 디스패치 프롬프트 형태 | `[WORKER]` 마커 | 하네스 Guards 주입 |
|------|---------------------|----------------|-------------------|
| opd | 코드 블록 내 키-값 (스킬 경로, 태스크 폴더, 이전 산출물, 프로젝트 컨텍스트) | **없음** | **없음** |
| opds | "op-dev-plan 워커 디스패치. model: advanced" (간략 서술) | **없음** | **없음** |
| opp | "op-task-plan 워커 디스패치. model: advanced" (간략 서술) | **없음** | **없음** |
| opwt | `references/network-guide.md` "Phase N 워커 프롬프트" 참조 | **없음** | **없음** |
| opdw | "워커 디스패치로 wireframe.md 생성" (간략 서술) | **없음** | **없음** |
| oppd | opal-task-action-agent 디스패치 (Agent 도구, 키-값 파라미터) | **없음** | **없음** |

### 스킬 Harness 폴백 현황

모든 opal-pilot-* 스킬에 `"부트스트랩에서 로드되지 않은 경우: ~/.opal/references/opal-harness.md를 Read한다"` 폴백이 이미 존재한다. Lazy 구조에서 하네스가 Eager로 올라가므로 이 폴백은 워커 전용 안전장치로 기능한다.

### 소스 vs 배포본

`install-mac.sh` L277: `cp "$opal_dir/core/AGENT.md" "$opal_home/AGENT.md"` -- 단순 복사. 소스 수정만으로 배포본 자동 갱신.

## 2. 핵심 설계

### 2-1. PM 세션 Eager/Lazy 구조

**Eager 단계** (세션 시작 시 즉시):

| 순서 | 파일 | 동작 |
|------|------|------|
| 1 | `~/.opal/identity.md` | Read → 정체성 로드 (없으면 온보딩) |
| 2 | `~/.opal/references/opal-harness.md` | Read → Guards(구현 금지, 디스패치 의무 등) 로드 |
| 3 | 부트스트래퍼 자동 삽입 확인 | 파일 확인/삽입 (기존 7단계) |
| 4 | 에이전트 활성화 | 정체성 + 하네스 기반 |

**Lazy 트리거 테이블**:

| 트리거 조건 | 로드 대상 | 전제 조건 |
|------------|----------|----------|
| `//` 커맨드 입력 | `skill-registry` (node 확인) → `skills.md` 폴백 | - |
| 워커 디스패치 직전 | `agents.md` + `opal-model-mapping.md` | 하네스(Eager) 로드 완료 |
| MCP 사용 요청 | `mcps.md` | - |
| 프로젝트 작업 요청 또는 `//opp` 호출 | `.opal/AGENT.md` (PM) + `docs/PROJECT.md` | 하네스(Eager) 로드 완료 |
| PM 컨텍스트 로드 시 함께, 또는 소유자 요청 | `.opal/MEMORY.md` | PM 컨텍스트 로드 완료 |

**설계 근거 -- CRITICAL 경고 교체**:
- opal-harness.md를 Eager로 올림 → Guards(구현 금지 원칙, 디스패치 의무)가 세션 시작부터 활성
- 스킬 레지스트리/에이전트 목록/모델 매핑은 실제 사용 시점에만 필요 → Lazy
- PM 컨텍스트는 프로젝트 작업 요청 시에만 필요 → Lazy
- 기존 "하나라도 건너뛰면 위험" 경고의 핵심 우려(하네스 미로드)가 Eager로 해소됨

### 2-2. 서브에이전트 부트스트랩 생략

**`[WORKER]` 마커 규칙** (`AGENT.md`에 추가):
- 디스패치 프롬프트의 **첫 줄**에 `[WORKER]`가 있으면 부트스트랩 전체를 생략하고 즉시 작업을 시작한다
- PM이 디스패치 프롬프트에 필요 컨텍스트(하네스 Guards 핵심 내용, 관련 참조 문서 경로)를 직접 주입하므로 워커가 독자적으로 부트스트랩할 필요 없음

**오케스트레이터 디스패치 템플릿 갱신**:
- 모든 opal-pilot-* 스킬의 워커 디스패치 프롬프트 상단에 `[WORKER]` 마커 추가
- 기존 `agents.md`의 "참조 문서 전달 의무"(AGENT.md "PM 컨텍스트 로드" > "참조 문서 전달 의무")와 통합: PM이 디스패치 시 하네스 Guards 핵심 규칙 + 관련 참조 문서 경로를 포함

### 2-3. 부트스트랩 완료 보고 형식

```
[부트스트랩] ✅ identity ✅ harness ⏳ registry ⏳ references ⏳ model-mapping ⏳ PM
```

- ✅: Eager 로드 완료
- ⏳: Lazy 대기 (사용 시 로드)
- ❌: 실패
- ⬜: 해당 없음

## 3. 구현 계획

### 파일 변경 계획

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `opal/core/AGENT.md` | 부트스트랩 절차 Eager/Lazy 재작성 + `[WORKER]` 마커 규칙 + 보고 형식 갱신 |
| 2 | `opal/skills/opal-pilot-project/SKILL.md` | 워커 디스패치 프롬프트에 `[WORKER]` 마커 + PM 컨텍스트 주입 지침 추가 |
| 3 | `opal/skills/opal-pilot-dev/SKILL.md` | 워커 디스패치 프롬프트에 `[WORKER]` 마커 + PM 컨텍스트 주입 지침 추가 |
| 4 | `opal/skills/opal-pilot-dev-short/SKILL.md` | 워커 디스패치 프롬프트에 `[WORKER]` 마커 + PM 컨텍스트 주입 지침 추가 |
| 5 | `opal/skills/opal-pilot-write-tech/SKILL.md` | Phase 1/3 워커 프롬프트 지침에 `[WORKER]` 마커 추가 안내 |
| 6 | `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | 워커 디스패치 프롬프트에 `[WORKER]` 마커 + PM 컨텍스트 주입 지침 추가 |
| 7 | `opal/skills/opal-pilot-project-dev/SKILL.md` | opal-task-action-agent 디스패치 프롬프트에 `[WORKER]` 마커 + PM 컨텍스트 주입 지침 추가 |

## 4. 실행 체크리스트

> 총 3개 Step

### Step 1: opal/core/AGENT.md 부트스트랩 재작성

- [x] 완료
- **파일**: `opal/core/AGENT.md`
- **작업 내용**:

  **1-a. CRITICAL 경고를 Lazy 설계 근거로 교체**:
  - 기존 `[CRITICAL]` 경고 블록 삭제
  - 새 설계 근거로 교체:
    > **[설계 원칙]** Eager 단계에서 identity.md + opal-harness.md를 즉시 로드하여 정체성과 Guards(구현 금지, 디스패치 의무)를 세션 시작부터 활성화한다. 나머지 참조 문서는 실제 사용 시점(Lazy)에 로드한다. 각 스킬 Harness 폴백이 하네스 자가 로드를 보장하므로, 스킬 호출 시 하네스 미로드 리스크 없음.

  **1-b. 10단계 절차를 Eager + Lazy 구조로 재구성**:
  - Eager 단계 (세션 시작 시):
    1. `~/.opal/identity.md` Read → 정체성 로드 (없으면 온보딩)
    2. `~/.opal/references/opal-harness.md` Read → Guards 로드
    3. 부트스트래퍼 자동 삽입 확인 (기존 7단계)
    4. 에이전트 활성화 (정체성 + 하네스 기반)
  - Lazy 트리거 테이블 (위 2-1 설계 그대로):

    | 트리거 조건 | 로드 대상 | 전제 조건 |
    |------------|----------|----------|
    | `//` 커맨드 입력 | `skill-registry` (node 확인) → `skills.md` 폴백 | - |
    | 워커 디스패치 직전 | `agents.md` + `opal-model-mapping.md` | 하네스(Eager) 로드 완료 |
    | MCP 사용 요청 | `mcps.md` | - |
    | 프로젝트 작업 요청 또는 `//opp` 호출 | `.opal/AGENT.md` (PM) + `docs/PROJECT.md` | 하네스(Eager) 로드 완료 |
    | PM 컨텍스트 로드 시 함께, 또는 소유자 요청 | `.opal/MEMORY.md` | PM 컨텍스트 로드 완료 |

  **1-c. `[WORKER]` 마커 감지 규칙 추가**:
  - 부트스트랩 섹션 상단(설계 원칙 바로 아래)에 다음 규칙 삽입:
    > **[WORKER 규칙]** 디스패치 프롬프트의 첫 줄에 `[WORKER]`가 있으면 부트스트랩 전체를 건너뛰고 즉시 작업을 시작한다. PM이 디스패치 프롬프트에 필요 컨텍스트를 직접 주입하므로 워커가 독자적 부트스트랩을 수행할 필요 없다.

  **1-d. 부트스트랩 완료 보고 형식 갱신**:
  - 기존 형식:
    ```
    [부트스트랩] ✅ identity  ✅ harness  ✅ registry  ✅ references  ✅ model-mapping  ✅ PM (프로젝트명)
    ```
  - 변경 형식:
    ```
    [부트스트랩] ✅ identity ✅ harness ⏳ registry ⏳ references ⏳ model-mapping ⏳ PM
    ```
  - 범례 갱신: `✅ Eager 완료 | ⏳ Lazy 대기 | ❌ 실패 | ⬜ 해당 없음`

  **1-e. 기존 상세 설명 보존**:
  - "모델 매핑 자동 적용", "PM 컨텍스트 로드", "프로젝트 메모리 브리핑", "프로젝트 부트스트래퍼 자동 관리" 섹션의 내용은 그대로 유지
  - 각 섹션 상단에 Lazy 트리거 조건을 명시하는 한 줄 추가:
    - "모델 매핑 자동 적용": `> **Lazy 트리거**: 워커 디스패치 직전`
    - "PM 컨텍스트 로드": `> **Lazy 트리거**: 프로젝트 작업 요청 또는 // 스킬 호출 시`
    - "프로젝트 메모리 브리핑": `> **Lazy 트리거**: PM 컨텍스트 로드 시 함께, 또는 소유자 요청 시`

  **1-f. 변경이력 추가**: 변경이력 테이블이 없으면 신규 추가, 있으면 행 추가

- **완료 기준**:
  - Eager 단계가 identity.md + opal-harness.md + 부트스트래퍼 확인 + 에이전트 활성화만 포함
  - 모든 Lazy 항목에 트리거 조건이 명시된 테이블 존재
  - `[WORKER]` 마커 감지 규칙이 부트스트랩 섹션에 존재
  - 부트스트랩 완료 보고에 ⏳ 상태 포함
  - 기존 상세 설명(모델 매핑, PM 컨텍스트, 메모리 브리핑 등)이 내용 보존됨
  - CRITICAL 경고가 Lazy 설계 근거로 교체됨
- **의존**: 없음

### Step 2: opal-pilot-* 스킬 워커 디스패치 섹션 갱신

- [x] 완료
- **파일**: 6개 스킬 SKILL.md
- **작업 내용**:

  **2-a. opal-pilot-dev (`opal/skills/opal-pilot-dev/SKILL.md`)**:
  - STEP 2 (ANALYSIS) 디스패치 프롬프트 코드 블록 첫 줄에 `[WORKER]` 추가
  - STEP 3-1 (PLAN) 디스패치 프롬프트 코드 블록 첫 줄에 `[WORKER]` 추가
  - STEP 3-2 (TEST-SCENARIO) 디스패치 프롬프트 코드 블록 첫 줄에 `[WORKER]` 추가
  - STEP 4 (EXECUTE) 디스패치 프롬프트 코드 블록 첫 줄에 `[WORKER]` 추가

  **2-b. opal-pilot-dev-short (`opal/skills/opal-pilot-dev-short/SKILL.md`)**:
  - STEP 2의 PLAN 디스패치 + TEST-SCENARIO 디스패치 서술에 `[WORKER]` 마커 포함 지침 추가
  - STEP 3 (EXECUTE) 디스패치 서술에 `[WORKER]` 마커 포함 지침 추가

  **2-c. opal-pilot-project (`opal/skills/opal-pilot-project/SKILL.md`)**:
  - STEP 2 (PLAN) 디스패치 서술에 `[WORKER]` 마커 포함 지침 추가
  - STEP 3 (EXECUTE) 디스패치 서술에 `[WORKER]` 마커 포함 지침 추가

  **2-d. opal-pilot-write-tech (`opal/skills/opal-pilot-write-tech/SKILL.md`)**:
  - Phase 1 (병렬 분석) 워커 프롬프트 참조에 `[WORKER]` 마커 포함 지침 추가
  - Phase 3 (병렬 작성) 워커 프롬프트 참조에 `[WORKER]` 마커 포함 지침 추가
  - Phase 4 (정합성 검증) QA 워커 디스패치에 `[WORKER]` 마커 포함 지침 추가

  **2-e. opal-pilot-dev-wireframe (`opal/skills/opal-pilot-dev-wireframe/SKILL.md`)**:
  - STEP 2 (WIREFRAME) 워커 디스패치에 `[WORKER]` 마커 포함 지침 추가
  - STEP 3 (EXECUTE) 워커 디스패치에 `[WORKER]` 마커 포함 지침 추가

  **2-f. opal-pilot-project-dev (`opal/skills/opal-pilot-project-dev/SKILL.md`)**:
  - Phase 3 "3-1. 실행 루프"의 opal-task-action-agent 디스패치 프롬프트 파라미터에 `[WORKER]` 마커 포함 지침 추가

  **2-g. PM 컨텍스트 주입 지침 (공통)**:
  - 각 스킬의 워커 디스패치 섹션에 다음 규칙 추가:
    > **[PM 컨텍스트 주입]** 워커 디스패치 프롬프트의 첫 줄에 `[WORKER]`를 삽입한다. `[WORKER]` 마커가 있으면 워커는 부트스트랩을 생략한다. PM은 디스패치 시 다음을 프롬프트에 포함해야 한다:
    > 1. 하네스 Guards 핵심 규칙 (구현 금지 원칙, 커밋 규칙)
    > 2. 관련 참조 문서 경로 (docs/PROJECT.md 문서 테이블 기반)
    > 3. 기술 스택 연동 지시 (기존 "참조 문서 전달 의무" 통합)
  - 기존 AGENT.md "참조 문서 전달 의무"와의 관계: AGENT.md의 기존 규칙이 PM 수준에서 적용되고, 여기서는 디스패치 프롬프트에 물리적으로 포함하는 방법을 명시

- **완료 기준**:
  - 6개 opal-pilot-* 스킬 모두에 `[WORKER]` 마커 지침이 추가됨
  - PM 컨텍스트 주입 규칙이 각 스킬에 명시됨
  - 기존 디스패치 프롬프트 구조(키-값, 서술형)는 유지하되 `[WORKER]` 첫 줄만 추가
  - 기존 "참조 문서 전달 의무"와의 통합 관계가 명시됨
- **의존**: Step 1 (AGENT.md에 `[WORKER]` 규칙이 먼저 정의되어야 함)

### Step 3: 배포 테스트

- [x] 완료
- **파일**: `scripts/install-mac.sh` (실행만, 수정 없음)
- **작업 내용**:
  1. `diff opal/core/AGENT.md ~/.opal/AGENT.md` 실행 → 소스 변경 내용 확인
  2. 차이가 있으면: 소스 수정이 의도한 대로 반영되었는지 검토
  3. 필요 시 `install-mac.sh` 재실행하여 배포 확인
- **완료 기준**: `opal/core/AGENT.md`의 변경 내용이 `~/.opal/AGENT.md`에 반영 가능함을 확인
- **의존**: Step 1, Step 2

## 5. QA 체크리스트

### 기능 테스트

- [x] Eager 단계에서 identity.md + opal-harness.md만 Read하는지 확인
- [x] Lazy 트리거 테이블에 기존 10단계의 모든 참조 문서가 포함되어 있는지 확인
- [x] 각 Lazy 항목의 트리거 조건이 TASK.md 요구사항과 일치하는지 확인
- [x] `[WORKER]` 마커 규칙이 AGENT.md 부트스트랩 섹션에 존재하는지 확인
- [x] 6개 opal-pilot-* 스킬 모두에 `[WORKER]` 마커 + PM 컨텍스트 주입 지침이 추가되었는지 확인

### 일관성 테스트

- [x] 기존 스킬 Harness 폴백 문구("부트스트랩에서 로드되지 않은 경우")와 Lazy 설계가 정합하는지 확인
- [x] PM 컨텍스트 로드의 전제 조건("opal-harness.md 로드 필요")이 Eager로 보장되는지 확인
- [x] 부트스트랩 완료 보고 형식이 Eager(✅)/Lazy(⏳) 구분을 정확히 반영하는지 확인
- [x] AGENT.md의 나머지 섹션(정체성 적용, 핵심 역할, 행동 규칙 등)이 변경되지 않았는지 확인
- [x] 각 스킬의 PM 컨텍스트 주입 규칙이 AGENT.md "참조 문서 전달 의무"와 충돌하지 않는지 확인

### 문서 품질

- [x] 새 부트스트랩 절차가 명확하고 모호함 없이 기술되었는지 확인
- [x] Lazy 트리거 조건이 구체적이고 실행 가능한지 확인
- [x] 기존 상세 설명(모델 매핑, PM 컨텍스트, 메모리 브리핑)이 누락 없이 보존되었는지 확인
- [x] 각 스킬의 변경이력에 이번 변경 기록이 추가되었는지 확인

## 6. 리스크 및 대응

| 리스크 | 영향 | 대응 |
|--------|------|------|
| `[WORKER]` 마커 없이 워커 디스패치 | 워커가 풀 부트스트랩 수행 (기존 동작, 느리지만 안전) | 폴백으로 동작 -- 마커 누락은 성능 저하일 뿐 기능 문제 아님 |
| PM이 하네스 Guards를 디스패치에 누락 | 워커가 구현 금지 원칙 미인지 | 각 스킬 Harness 폴백이 워커에서 하네스 자가 로드 보장 (2중 안전망) |
| Lazy 항목 트리거 시점 오판 | 참조 문서 미로드 상태에서 작업 | Lazy 테이블에 전제 조건 컬럼 명시 + 연쇄 로드 규칙 |
| 새 참조 문서 추가 시 Lazy 테이블 미등록 | 해당 문서 로드 누락 | AGENT.md에 "새 참조 추가 시 Lazy 테이블에 트리거 조건 명시 필수" 규칙 포함 |
| opwt의 워커 프롬프트가 references/ 파일 참조형 | `[WORKER]` 마커를 references 파일에도 반영 필요 | opwt SKILL.md에서 "워커 프롬프트 첫 줄에 `[WORKER]` 포함" 지침으로 해결 (references 파일 자체는 프롬프트 템플릿이 아닌 가이드) |
