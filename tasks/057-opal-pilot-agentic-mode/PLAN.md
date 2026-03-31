# PLAN: opal-pilot agentic mode 추가

> 작성일: 2026-03-31
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `opal/core/references/opal-harness.md` | 오케스트레이터 공통 인프라 (Guards, Gates, State) | **수정** — agentic mode 공통 규칙 섹션 추가 |
| `opal/skills/opal-pilot-dev/SKILL.md` | opd (Full Task 오케스트레이터) | **수정** — agentic mode 활성화/차이 섹션 추가 |
| `opal/skills/opal-pilot-dev-short/SKILL.md` | opds (Short Task 오케스트레이터) | **수정** — agentic mode 활성화/차이 섹션 추가 |
| `opal/skills/opal-pilot-project/SKILL.md` | opp (프로젝트 범용 오케스트레이터) | **수정** — agentic mode 활성화/차이 섹션 추가 |
| `opal/skills/opal-pilot-project-dev/SKILL.md` | oppd (프로젝트 개발 라이프사이클 오케스트레이터) | **수정** — Phase 1~2 게이트에 agentic mode 적용 |

### 현재 상태

**하네스 (`opal-harness.md`)**:
- §0 용어 정의, §1 Guards, §2 Gates, §3 State, §4 TASK 공통, §5 Observability, §6 Model Mapping — 총 6개 섹션
- §1 Guards에 `구현 금지 원칙`, `Git 사전 점검`, `디스패치 의무 원칙`, `커밋 규칙`, `자동 루핑 제약`이 정의됨
- §2 Gates에 `단계 게이트` (매 단계 사용자 보고+승인), `QA Gate`, `PM Gate`, `체크리스트 검증 게이트`가 정의됨
- agentic mode 관련 내용은 없음. 단, §1의 `자동 루핑 제약`에 이미 루핑 한도/에스컬레이션이 정의되어 있음

**opd (`opal-pilot-dev/SKILL.md`)**:
- 4단계: TASK → ANALYSIS → PLAN+TEST-SCENARIO → EXECUTE
- 각 단계 완료 시 사용자 보고+승인 (하네스 §2 단계 게이트)
- agentic mode 관련 내용 없음

**opds (`opal-pilot-dev-short/SKILL.md`)**:
- 3단계: TASK → PLAN+TEST-SCENARIO → EXECUTE
- 각 단계 완료 시 사용자 보고+승인
- agentic mode 관련 내용 없음

**opp (`opal-pilot-project/SKILL.md`)**:
- 3단계: TASK → PLAN → EXECUTE
- 각 단계 완료 시 사용자 보고+승인
- agentic mode 관련 내용 없음

**oppd (`opal-pilot-project-dev/SKILL.md`)**:
- 3 Phase: PLAN(opwt) → ROADMAP → EXECUTE(opal-task-action-agent)
- Phase 1~2: 사용자 확정 게이트 있음
- Phase 3: **이미 agentic** — opal-task-action-agent가 자율 실행하고 PM이 검수, 사용자에게는 액션 시작/완료만 보고
- Phase 1~2 게이트만 agentic mode 적용 대상

### 영향 범위

| 영향 대상 | 영향 내용 |
|----------|----------|
| 하네스를 참조하는 모든 오케스트레이터 | §7 추가 시 기존 §0~6은 변경 없으므로 하위 호환 유지 |
| PM 검토 게이트 (AGENT.md) | agentic mode에서 PM Gate 강화 — 기존 규칙 그대로, PM이 사용자 역할도 대행 |
| 사용자 경험 | agentic mode는 opt-in이므로 기본 동작은 변경 없음 |
| 배포본 (`~/.opal/`) | 소스 수정 후 install 스크립트로 배포 필요 |

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| (없음 — AGENTIC-LOG.md는 런타임에 오케스트레이터가 생성하는 산출물이므로 소스 파일 신규 생성 없음) | | |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `opal/core/references/opal-harness.md` | §7 Agentic Mode 섹션 추가 (공통 규칙) |
| 2 | `opal/skills/opal-pilot-dev/SKILL.md` | Agentic Mode 섹션 추가 + 변경이력 |
| 3 | `opal/skills/opal-pilot-dev-short/SKILL.md` | Agentic Mode 섹션 추가 + 변경이력 |
| 4 | `opal/skills/opal-pilot-project/SKILL.md` | Agentic Mode 섹션 추가 + 변경이력 |
| 5 | `opal/skills/opal-pilot-project-dev/SKILL.md` | Phase 1~2 Agentic Mode 섹션 추가 + 변경이력 |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| (없음) | | |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | 하네스 §7 Agentic Mode 공통 규칙 추가 | `opal/core/references/opal-harness.md` | 중 |
| 2 | opd agentic mode 섹션 추가 | `opal/skills/opal-pilot-dev/SKILL.md` | 하 |
| 3 | opds agentic mode 섹션 추가 | `opal/skills/opal-pilot-dev-short/SKILL.md` | 하 |
| 4 | opp agentic mode 섹션 추가 | `opal/skills/opal-pilot-project/SKILL.md` | 하 |
| 5 | oppd Phase 1~2 agentic mode 적용 | `opal/skills/opal-pilot-project-dev/SKILL.md` | 하 |

### 핵심 설계

#### §7 Agentic Mode — 하네스 공통 규칙 (`opal-harness.md`)

§6 Model Mapping 뒤에 새 섹션으로 추가한다.

**핵심 내용**:

1. **모드 정의**
   - `interactive` (기본): 기존 동작. 각 단계 완료 시 사용자 승인을 받는다.
   - `agentic`: PM이 사용자를 대행하여 자율 진행. PM은 사용자 역할을 맡으므로 interactive보다 **높은 검토 기준과 기록 의무**를 진다.

2. **활성화 방법**
   - 반드시 `--agentic` 플래그를 포함해야 활성화. 가급적 스킬명 바로 뒤에 위치.
   - 예: `//opds --agentic 로그인 버그 수정`, `//oppd --agentic 프로젝트 개발 시작`
   - `--agentic` 플래그가 없으면 항상 interactive 모드.
   - STATE.md에 `모드: agentic`으로 기록

3. **PM 대행 의무 (agentic 핵심 원칙)**

   PM이 사용자를 대행하는 만큼, interactive 모드보다 **책임과 의무가 강화**된다:

   | 의무 | 설명 |
   |------|------|
   | **판단 기록 의무** | 매 게이트에서 Pass/Fail 판단 근거를 AGENTIC-LOG.md에 기록한다. 왜 승인했는지, 무엇을 확인했는지 명시. |
   | **산출물 직접 검증 의무** | 체크리스트 수준이 아닌, 산출물을 **직접 Read하여 내용 수준까지 검증**한다. 요구사항 누락, 설계 오류, 일관성 문제를 내용 기반으로 판단. |
   | **완수 의무** | 100% 완수까지 루핑한다. 미완료 항목을 추적하고, 모든 체크리스트 항목이 충족될 때까지 진행. |
   | **품질 책임** | PM이 최종 품질에 책임진다. 사용자가 agentic 결과를 받았을 때 추가 수정이 불필요한 수준이 목표. |
   | **투명성 의무** | 사용자가 사후에 전체 과정을 추적할 수 있도록, 모든 활동(오류, 수정, 의사결정, 개선)을 AGENTIC-LOG.md에 남긴다. |
   | **에스컬레이션 책임** | 올려야 할 것을 안 올리는 것도 PM 실패. 판단이 모호하면 에스컬레이션이 기본. |

4. **PM 자율 검토 (사용자 게이트 대행)**
   - 각 단계 완료 시 PM이 QA Gate + PM Gate를 **강화 검토**로 수행
   - 강화 검토 기준: (1) TASK.md 요구사항 100% 충족, (2) QA 결과 All Pass, (3) PM 검토 기준 Pass, (4) 이전 단계 산출물과 일관성, (5) 산출물 내용을 직접 Read하여 실질 검증
   - **Pass**: PM이 자동 승인하고 다음 단계 진행 — 판단 근거를 AGENTIC-LOG.md에 기록
   - **Fail**: PM이 워커에게 재지시 → 재검토 (아래 "Gate 루핑 규칙" 참조)

5. **Gate 루핑 규칙 (모든 스킬 공통)**

   모든 Gate에 동일하게 적용되는 단일 규칙. 스킬별 차등이나 태스크 레벨 한도 없음.

   ```
   Gate Fail → 재지시 (루핑 카운트 +1)
     → 3회 이내: 재지시 + AGENTIC-LOG 기록
     → 3회 초과: 심각도 판별
         ├─ Critical → 사용자 에스컬레이션 + STOP
         └─ Normal/Minor → AGENTIC-LOG 기록 + 계속 진행
   ```

   **심각도 기준**:

   | 심각도 | 동작 | 예시 |
   |--------|------|------|
   | **Critical** | 에스컬레이션 + 중단 | 아키텍처 변경 필요, 요구사항 모호, 보안 이슈, 데이터 손실 가능성 |
   | **Normal** | LOG 기록 + 진행 | 품질 미달 반복, 컨벤션 위반, 마이너 설계 불일치 |
   | **Minor** | LOG 기록 + 진행 | 포맷/스타일, 문서 표현, 네이밍 |

   **사후 보정**: Normal/Minor로 3회 초과한 Gate는 AGENTIC-LOG.md에 기록되어, 사용자가 완료 보고 시 확인하고 필요하면 보정한다.

   **oppd Phase 3에도 동일 적용**: 각 액션 내부가 opds 파이프라인(TASK→PLAN→EXECUTE)이므로, 액션 내 각 Gate + 액션 간 Gate 모두 동일 규칙.

6. **에스컬레이션 조건** (PM이 사용자에게 올리는 기준)
   - Gate 3회 초과 + 심각도 Critical
   - 설계/아키텍처 변경이 필요한 경우
   - 요구사항 모호성 (TASK.md에서 판단 불가)
   - 하네스 Guards 위반 가능성 (구현 금지 원칙, 커밋 규칙)
   - 자동 루핑 제약 한도 초과 (§1 Guards 준수)
   - **판단이 모호한 경우** (확신이 없으면 에스컬레이션이 기본)

7. **유지되는 규칙 (agentic에서도 변경 없음)**
   - `구현 금지 원칙`: EXECUTE 단계 진입은 PM이 대행 승인하되, 코드 생성/수정은 워커만 수행
   - `커밋 규칙`: 커밋은 agentic mode에서도 사용자 명시 요청 시에만 수행
   - `디스패치 의무 원칙`: 워커 디스패치로 정의된 단계는 반드시 서브에이전트 사용
   - `자동 루핑 제약`: 기존 한도 그대로 적용

8. **AGENTIC-LOG.md (PM 대행 일지)**

   agentic mode 시작 시 태스크 폴더에 `AGENTIC-LOG.md`를 자동 생성한다. PM이 수행한 모든 활동을 시계열로 기록하여, 사용자가 사후에 전체 과정을 추적할 수 있게 한다.

   **생성 위치**: `tasks/{NNN}-{name}/AGENTIC-LOG.md`

   **기록 카테고리**:

   | 카테고리 | 코드 | 기록 대상 |
   |----------|------|----------|
   | 게이트 판단 | `GATE` | 매 게이트 Pass/Fail 판단 + 근거 |
   | 오류 발견 | `ERROR` | 검토 중 발견한 오류, 누락, 불일치 |
   | 수정 지시 | `FIX` | 워커에게 재지시한 내용 + 수정 결과 |
   | 의사결정 | `DECISION` | PM이 사용자 대신 내린 판단 + 근거 |
   | 개선 사항 | `IMPROVE` | 발견한 개선점 + 적용 여부 |
   | 에스컬레이션 | `ESCALATION` | 사용자에게 올린 내용 + 사유 |

   **기록 의무 규칙**:
   - 매 게이트마다 최소 1개 `GATE` 엔트리 필수 (Pass든 Fail이든)
   - `FIX` 엔트리는 반드시 선행 `ERROR` 엔트리를 참조
   - `DECISION` 엔트리는 반드시 근거(why)를 포함
   - 태스크 완료 시 "요약" 섹션을 채워 전체 통계를 갱신

   **템플릿**:

   ```markdown
   # AGENTIC-LOG: {태스크 제목}

   > 모드: agentic | 시작: YYYY-MM-DD HH:mm | 스킬: //{스킬명}

   ## 요약

   | 항목 | 건수 |
   |------|------|
   | 게이트 판단 | {N}회 (Pass: {N} / Fail: {N}) |
   | 3회 초과 Gate | {N}건 (Critical: {N} / Normal: {N} / Minor: {N}) |
   | 오류 발견 | {N}건 |
   | 수정 지시 | {N}건 (반영: {N} / 미반영: {N}) |
   | PM 의사결정 | {N}건 |
   | 개선 사항 | {N}건 |
   | 에스컬레이션 | {N}건 |

   ## 대행 일지

   | # | 시점 | 단계 | 카테고리 | 내용 | 결과 |
   |---|------|------|----------|------|------|
   ```

9. **완료 보고**
   - 전체 태스크 완료 시 사용자에게 종합 보고
   - 보고 내용: 각 단계별 PM 판단 요약 + 변경 파일 + 특이 사항 + AGENTIC-LOG.md 참조 경로
   - AGENTIC-LOG.md의 "요약" 섹션이 완전히 채워져 있어야 한다
   - 사용자는 AGENTIC-LOG.md를 통해 PM이 무엇을 발견하고, 어떻게 판단하고, 무엇을 수정했는지 전체 이력을 추적할 수 있다

#### opd, opds, opp — 스킬별 Agentic Mode 섹션

각 SKILL.md에 `## Agentic Mode` 섹션을 추가한다. 변경이력 바로 위에 배치.

**공통 패턴** (3개 스킬 동일):
```markdown
## Agentic Mode

하네스 §7 Agentic Mode 참조. 이 스킬에서의 차이점만 기술한다.

### 활성화
`--agentic` 플래그가 스킬명 뒤에 포함되면 활성화.
STATE.md 모드 필드를 `agentic`으로 기록한다.

### 자율 게이트 흐름
{스킬별 파이프라인에 맞춘 게이트 흐름 기술}
```

**opd 차이점**:
- 4단계(TASK → ANALYSIS → PLAN+TEST-SCENARIO → EXECUTE)에서 TASK 이후 3개 게이트를 PM이 자율 통과
- EXECUTE 진입 = PM이 대행 승인 (구현 금지 원칙의 "실행 허가"를 PM이 판단)

**opds 차이점**:
- 3단계(TASK → PLAN+TEST-SCENARIO → EXECUTE)에서 TASK 이후 2개 게이트를 PM이 자율 통과
- 에스컬레이션 규칙(Full Task 전환 제안)은 agentic에서도 유지 — PM이 판단하여 자동 전환하지 않고 사용자에게 보고

**opp 차이점**:
- 3단계(TASK → PLAN → EXECUTE)에서 TASK 이후 2개 게이트를 PM이 자율 통과

#### oppd — 전 Phase Agentic Mode 적용

**oppd 차이점**:

- **Phase 1~2**: "사용자 확정" 게이트를 PM이 대행
  - Phase 1 (opwt 결과): PM이 PRD/TRD 품질을 검토하여 자율 확정 → Phase 2 진행
  - Phase 2 (ROADMAP): PM이 로드맵을 검수하여 자율 확정 → Phase 3 진행

- **Phase 3 액션 내부**: 각 액션이 opds 파이프라인(TASK→PLAN→EXECUTE)이므로, 액션 내 각 Gate에도 **공통 Gate 루핑 규칙(3회 초과 → 심각도 판별)** 동일 적용
- **Phase 3 액션 간 게이트**: PM이 각 액션 결과를 검수하여 자율 승인 → 다음 액션 진행 (interactive에서는 "다음 액션으로 넘어갈까요?" 사용자 게이트가 있었음)
  - 각 액션 완료 시 AGENTIC-LOG.md에 `GATE` 엔트리 기록
  - 액션 실패(status: failed) 시에도 PM이 판단: 재시도 가능 → `FIX` + 재디스패치, 불가 → `ESCALATION`

- **에스컬레이션 조건**: 하네스 §7 공통 기준 + oppd 고유:
  - PRD/TRD에서 사용자 비즈니스 판단이 필요한 경우
  - 액션 Critical Fail로 전체 로드맵 재조정이 필요한 경우

## 3. 실행 체크리스트

> 총 5개 Step

### Step 1: 하네스 §7 Agentic Mode 공통 규칙 추가
- [x] 완료
- **파일**: `opal/core/references/opal-harness.md`
- **작업 내용**: §6 Model Mapping 뒤에 `## 7. Agentic Mode` 섹션을 추가한다. 핵심 설계의 9개 항목(모드 정의, 활성화 방법(`--agentic` 플래그), PM 대행 의무, PM 자율 검토, Gate 루핑 규칙(3회 초과→심각도 판별), 에스컬레이션 조건, 유지 규칙, AGENTIC-LOG.md 템플릿/기록 규칙, 완료 보고)을 포함한다.
- **완료 기준**: §7 섹션이 존재하고, PM 대행 의무 6개 항목 + Gate 루핑 규칙(3회 초과→Critical:STOP/Normal·Minor:LOG+진행) + 심각도 기준 테이블 + AGENTIC-LOG.md 템플릿(7개 카테고리 포함 3회초과Gate 통계)이 포함되며, 기존 §0~6과 충돌 없고 interactive 모드에 영향 없음
- **테스트**: §1 Guards의 각 항목이 agentic mode에서도 유지됨을 명시적으로 확인. §2 Gates의 단계 게이트가 agentic 분기를 포함
- **의존**: 없음

### Step 2: opd SKILL.md agentic mode 섹션 추가
- [x] 완료
- **파일**: `opal/skills/opal-pilot-dev/SKILL.md`
- **작업 내용**: 변경이력 섹션 바로 위에 `## Agentic Mode` 섹션을 추가한다. 하네스 §7 참조 + 4단계 파이프라인에서의 자율 게이트 흐름을 기술한다. 변경이력에 v1.6 추가.
- **완료 기준**: Agentic Mode 섹션이 존재하고, TASK→ANALYSIS→PLAN+TEST-SCENARIO→EXECUTE 각 게이트의 agentic 동작이 명확
- **테스트**: 기존 interactive 모드 설명과 충돌 없음 확인
- **의존**: Step 1

### Step 3: opds SKILL.md agentic mode 섹션 추가
- [x] 완료
- **파일**: `opal/skills/opal-pilot-dev-short/SKILL.md`
- **작업 내용**: 변경이력 섹션 바로 위에 `## Agentic Mode` 섹션을 추가한다. 하네스 §7 참조 + 3단계 파이프라인에서의 자율 게이트 흐름 기술. 에스컬레이션 규칙(Full Task 전환)은 agentic에서도 사용자 보고 유지를 명시. 변경이력에 v1.6 추가.
- **완료 기준**: Agentic Mode 섹션이 존재하고, 에스컬레이션 규칙의 agentic 동작이 명확
- **테스트**: 기존 interactive 모드 설명과 충돌 없음 확인
- **의존**: Step 1

### Step 4: opp SKILL.md agentic mode 섹션 추가
- [x] 완료
- **파일**: `opal/skills/opal-pilot-project/SKILL.md`
- **작업 내용**: 변경이력 섹션 바로 위에 `## Agentic Mode` 섹션을 추가한다. 하네스 §7 참조 + 3단계 파이프라인에서의 자율 게이트 흐름 기술. 변경이력에 v1.4 추가.
- **완료 기준**: Agentic Mode 섹션이 존재하고, TASK→PLAN→EXECUTE 각 게이트의 agentic 동작이 명확
- **테스트**: 기존 interactive 모드 설명과 충돌 없음 확인
- **의존**: Step 1

### Step 5: oppd SKILL.md 전 Phase agentic mode 적용
- [x] 완료
- **파일**: `opal/skills/opal-pilot-project-dev/SKILL.md`
- **작업 내용**: `## Agentic Mode` 섹션을 추가한다. Phase 1~2의 사용자 확정 게이트 + Phase 3의 액션 간/내부 게이트를 PM이 대행하는 흐름을 기술한다. Phase 3 액션 내부는 opds 파이프라인(TASK→PLAN→EXECUTE)이므로 공통 Gate 루핑 규칙이 동일 적용됨을 명시. oppd 고유 에스컬레이션 조건(비즈니스 판단, 로드맵 재조정)을 추가. 변경이력에 v3.2 추가.
- **완료 기준**: 전 Phase 게이트의 agentic 동작이 명확하고, Phase 3 액션 내부 = opds 파이프라인 + 공통 Gate 루핑 규칙 적용이 명시됨
- **테스트**: Phase 3의 기존 opal-task-action-agent 흐름과 충돌 없음 확인. 액션 간 게이트의 AGENTIC-LOG 기록 흐름이 하네스 §7과 일관됨
- **의존**: Step 1

## 4. QA 체크리스트

### 기능 테스트
- [ ] 하네스 §7이 9개 항목(모드 정의, 활성화, PM 대행 의무, 자율 검토, Gate 루핑 규칙, 에스컬레이션, 유지 규칙, AGENTIC-LOG.md, 완료 보고)을 모두 포함하는가
- [ ] Gate 루핑 규칙: 3회 초과 → 심각도 판별(Critical→STOP, Normal/Minor→LOG+진행)이 명시되는가
- [ ] 심각도 기준 테이블(Critical/Normal/Minor)이 예시와 함께 정의되는가
- [ ] AGENTIC-LOG.md 템플릿에 6개 카테고리 + "3회 초과 Gate" 요약 통계가 정의되는가
- [ ] AGENTIC-LOG.md 기록 의무 규칙(매 게이트 GATE 필수, FIX→ERROR 참조, DECISION 근거 필수)이 명시되는가
- [ ] 4개 스킬(opd, opds, opp, oppd) 모두에 Agentic Mode 섹션이 존재하는가
- [ ] 각 스킬의 agentic 게이트 흐름이 해당 파이프라인 단계와 일치하는가
- [ ] oppd는 Phase 1~2 게이트 + Phase 3 액션 간 게이트에 agentic 적용이고, Phase 3 액션 내부는 변경 없음이 명시되는가

### 일관성 테스트
- [ ] 하네스 §0~6 기존 내용이 변경되지 않았는가
- [ ] 각 스킬의 기존 interactive 모드 설명이 변경되지 않았는가
- [ ] `구현 금지 원칙`과 `커밋 규칙`이 agentic mode에서도 유지됨이 명시되는가
- [ ] 에스컬레이션 조건이 하네스 §1 Guards의 `자동 루핑 제약`과 일관되는가
- [ ] STATE.md 모드 필드 "agentic" 기록이 §3 State 템플릿과 호환되는가
- [ ] AGENTIC-LOG.md가 산출물 목록에 포함되는가 (agentic mode 시)

### 문서 품질
- [ ] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가
- [ ] kebab-case 파일/폴더 네이밍을 따르는가
- [ ] 변경이력이 올바른 버전과 일시로 기록되는가

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| PM 자율 검토의 판단 품질이 낮아 사용자 기대와 다른 결과물 생성 | 사용자 불만, 재작업 필요 | 에스컬레이션 조건을 보수적으로 설정 (모호하면 사용자에게 올림). 완료 보고에서 각 단계 결과를 상세히 포함하여 사용자가 사후 검토 가능 |
| agentic mode에서 구현 금지 원칙 위반 가능성 | Guards 무력화 | §7에 "유지되는 규칙"을 명시적으로 나열하여 agentic에서도 Guards가 적용됨을 강조 |
| oppd Phase 1~2 agentic에서 비즈니스 판단이 필요한 PRD 내용을 PM이 임의 확정 | 요구사항 불일치 | oppd 고유 에스컬레이션 조건에 "비즈니스 판단 필요 시" 명시 |
| 배포본(~/.opal/) 동기화 누락 | 소스와 배포본 불일치 | install 스크립트 실행을 DONE.md에 후속 조치로 기록 |
