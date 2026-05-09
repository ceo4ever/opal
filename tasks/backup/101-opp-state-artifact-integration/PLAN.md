# PLAN: STATE.md 진행 현황 + 완료 산출물 통합

> 작성일: 2026-04-09
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `opal/core/references/opal-harness.md` | 공통 하네스 -- §2 QA 산출물 표준 파일명, §3 STATE.md 템플릿, 진행 현황 행 구성 규칙 | **예** |
| `opal/core/references/opal-harness-interactive.md` | interactive 서브 하네스 -- §2.5 Artifact Gate | **예** |
| `opal/skills/opal-pilot-project/SKILL.md` | opp STATE.md 도메인 치환값 (진행 현황 행 예시) | **예** |
| `opal/skills/opal-pilot-dev-short/SKILL.md` | opds STATE.md 도메인 치환값 (진행 현황 행 예시) | **예** |
| `opal/skills/opal-pilot-dev/SKILL.md` | opd STATE.md 도메인 설정 (진행 현황 행 예시) | **예** |
| `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | opdw STATE.md 도메인 치환값 (진행 현황 행 예시 없음 -- 신규 추가 필요) | **예** |
| `opal/skills/opal-pilot-sdd/SKILL.md` | opsdd STATE.md 도메인 치환값 (독자 구조 -- "완료 산출물" 섹션 보유) | **예** |

### 현재 상태

#### 1-1. 공통 하네스 (`opal-harness.md`)

**§2 QA 산출물 표준 파일명** (L103-L114):
- PLAN QA: `QA-PLAN.md`, EXECUTE QA: `QA-EXECUTE.md`, ANALYSIS QA: `QA-ANALYSIS.md`
- 스킬별 오버라이드 가능. QA 산출물만 정의하고, 단계별 주요 산출물(PLAN.md, DONE.md 등)은 여기에 없음.

**§3 STATE.md 공통 템플릿** (L169-L202):
- 템플릿의 `{진행 현황 행 목록}`은 도메인 치환값으로 주입됨.
- 현재 행 유형: `작업`, `QA Gate`, `State Gate`, `Artifact Gate`, `PM Gate`, `사용자 확인`
- **산출물 생성 행은 없음** -- 이것이 이번 태스크의 핵심 문제.

**진행 현황 행 구성 규칙** (L204-L208):
```
- TASK 단계: 작업, 사용자 확인 (Gate 없음)
- 일반 단계: 작업, QA Gate, State Gate, Artifact Gate, State Gate, PM Gate, State Gate, 사용자 확인
- Gate가 없는 단계는 해당 행 생략
```
- **산출물 행에 대한 언급이 없음.**

#### 1-2. interactive 서브 하네스 (`opal-harness-interactive.md`)

**§2.5 Artifact Gate** (L40-L62):
- QA Gate + State Gate 완료 후 자동 실행.
- 필수 산출물 파일의 **존재 여부**를 사후 점검. 미존재 시 QA 에이전트 재소환.
- 현재는 산출물 존재 여부를 점검하는 **유일한 안전장치**.
- 산출물 행이 추가되면 이 Gate는 "2중 안전장치(fallback)"로 역할이 조정되어야 함.

#### 1-3. opp (`opal-pilot-project/SKILL.md`)

**단계**: TASK / PLAN / EXECUTE
**진행 현황 행 예시** (L106-L126): 18행. Gate 기반 구조만 있고 산출물 행 없음.
**단계별 필수 산출물**:
| 단계 | 주요 산출물 | QA 산출물 |
|------|-----------|----------|
| TASK | TASK.md | - |
| PLAN | PLAN.md | QA-PLAN.md |
| EXECUTE | DONE.md | QA-EXECUTE.md |

#### 1-4. opds (`opal-pilot-dev-short/SKILL.md`)

**단계**: TASK / PLAN / TEST-SCENARIO / EXECUTE / TEST
**진행 현황 행 예시** (L156-L179): 21행. Gate 기반 구조만 있고 산출물 행 없음.
**단계별 필수 산출물**:
| 단계 | 주요 산출물 | QA 산출물 |
|------|-----------|----------|
| TASK | TASK.md | - |
| PLAN | PLAN.md | - |
| TEST-SCENARIO | TEST-SCENARIO.md | QA-PLAN.md (PLAN+TS 동시 검토) |
| EXECUTE | (코드 변경) | - |
| TEST | DONE.md | QA-EXECUTE.md (TEST 결과 검토 시) |

#### 1-5. opd (`opal-pilot-dev/SKILL.md`)

**단계**: TASK / ANALYSIS / PLAN / TEST-SCENARIO / EXECUTE / TEST
**진행 현황 행 예시** (L162-L193): 29행. Gate 기반 구조만 있고 산출물 행 없음.
**단계별 필수 산출물**:
| 단계 | 주요 산출물 | QA 산출물 |
|------|-----------|----------|
| TASK | TASK.md | - |
| ANALYSIS | ANALYSIS.md | QA-ANALYSIS.md |
| PLAN | PLAN.md | - |
| TEST-SCENARIO | TEST-SCENARIO.md | QA-PLAN.md (PLAN+TS 동시 검토) |
| EXECUTE | (코드 변경) | - |
| TEST | DONE.md | QA-EXECUTE.md (TEST 결과 검토 시) |

#### 1-6. opdw (`opal-pilot-dev-wireframe/SKILL.md`)

**단계**: TASK / WIREFRAME / EXECUTE
**진행 현황 행 예시**: **없음** -- 도메인 치환값 섹션에 행별 테이블이 누락되어 있음. 신규 생성 필요.
**단계별 필수 산출물**:
| 단계 | 주요 산출물 | QA 산출물 |
|------|-----------|----------|
| TASK | TASK.md | - |
| WIREFRAME | wireframe.md | QA-WIREFRAME.md (op-dev-qa 호출) |
| EXECUTE | DONE.md | QA-EXECUTE.md |

#### 1-7. opsdd (`opal-pilot-sdd/SKILL.md`)

**단계**: TASK / SPEC / REVIEW / DESIGN / EXECUTE-LOOP / DONE
**STATE.md 구조**: 독자적 구조를 사용. "완료 산출물" 섹션이 이미 별도로 존재함.
- `완료 산출물` 테이블: TASK.md / SPEC.md / TEST-SCENARIOS.md / SPEC-PLAN.md / EXECUTE-LOOP / DONE.md
- **진행 현황 행 예시**: Gate 기반 행 예시가 없음. 독자적 "완료 산출물" + "ACT 목록" + "TS 상태" 테이블 구조.
- opsdd는 이미 산출물 추적이 포함된 구조이므로, **진행 현황 행 기반 산출물 통합의 직접 대상은 아님**. 단, 공통 하네스 규칙과 일관성을 유지하도록 조정이 필요.

### 영향 범위

**직접 변경 대상 (6개 파일)**:
1. `opal/core/references/opal-harness.md` -- 진행 현황 행 구성 규칙 + 공통 템플릿 확장
2. `opal/core/references/opal-harness-interactive.md` -- §2.5 Artifact Gate 역할 재정의
3. `opal/skills/opal-pilot-project/SKILL.md` -- opp 진행 현황 행 예시 갱신
4. `opal/skills/opal-pilot-dev-short/SKILL.md` -- opds 진행 현황 행 예시 갱신
5. `opal/skills/opal-pilot-dev/SKILL.md` -- opd 진행 현황 행 예시 갱신
6. `opal/skills/opal-pilot-dev-wireframe/SKILL.md` -- opdw 진행 현황 행 예시 신규 추가

**간접 영향 (조정 필요)**:
7. `opal/skills/opal-pilot-sdd/SKILL.md` -- opsdd 독자 구조와의 일관성 확인/조정

**변경 안 함 (제외)**:
- opwt, oppd -- 태스크 범위 밖
- 기존 진행 중 태스크의 STATE.md -- 소급 변경 안 함

---

## 2. 구현 계획

### 설계 원칙

**산출물 행 삽입 규칙**: 각 단계에서 워커가 생성하는 **주요 산출물 파일** 생성을 진행 현황 행으로 추적한다.

1. **위치**: `작업` 행 직후, `QA Gate` 행 직전에 삽입한다
   - 이유: 워커가 작업을 완료하면 산출물이 생성되어야 하고, QA Gate가 그 산출물을 검증하는 흐름
2. **항목명 형식**: `{파일명} 생성` (예: `PLAN.md 생성`, `QA-PLAN.md 생성`)
3. **QA 산출물 행**: QA Gate 직후, Artifact Gate 직전에 삽입한다
   - 이유: QA 에이전트가 Gate를 통과하며 QA 산출물을 생성하는 흐름
4. **DONE.md 행**: 최종 단계의 PM Gate 직후, 사용자 확인 직전에 삽입한다
   - 이유: DONE.md는 PM Gate 통과 후 모든 검증이 완료된 시점에 생성됨
5. **산출물이 없는 행은 삽입하지 않는다**: EXECUTE 단계의 `작업`은 코드 변경이므로 별도 산출물 행 불필요

**Artifact Gate 역할 재정의**:
- 기존: 산출물 존재 여부를 점검하는 **1차 안전장치**
- 변경: 산출물 행이 순서 강제로 생성을 보장하므로, Artifact Gate는 **2중 안전장치(fallback)**로 재정의
- Artifact Gate의 점검 내용과 동작은 유지하되, 설명에 "산출물 행이 1차 보장, Artifact Gate는 2차 점검" 역할 구분을 추가

### 파일 변경 계획

#### 신규 생성

없음.

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `opal/core/references/opal-harness.md` | §2 QA 산출물 표준 파일명에 단계별 주요 산출물 표 추가, §3 진행 현황 행 구성 규칙에 산출물 행 규칙 추가 |
| 2 | `opal/core/references/opal-harness-interactive.md` | §2.5 Artifact Gate 역할을 "2중 안전장치"로 재정의 |
| 3 | `opal/skills/opal-pilot-project/SKILL.md` | opp 진행 현황 행 예시에 산출물 행 삽입 |
| 4 | `opal/skills/opal-pilot-dev-short/SKILL.md` | opds 진행 현황 행 예시에 산출물 행 삽입 |
| 5 | `opal/skills/opal-pilot-dev/SKILL.md` | opd 진행 현황 행 예시에 산출물 행 삽입 |
| 6 | `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | opdw 진행 현황 행 예시 신규 작성 (산출물 행 포함) |
| 7 | `opal/skills/opal-pilot-sdd/SKILL.md` | opsdd "완료 산출물" 섹션에 공통 하네스 규칙 참조 문구 추가 |

#### 삭제

없음.

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | 공통 하네스 -- 산출물 행 규칙 + QA 산출물 표 확장 | `opal-harness.md` | 중 |
| 2 | Artifact Gate 역할 재정의 | `opal-harness-interactive.md` | 하 |
| 3 | opp 진행 현황 행 갱신 | `opal-pilot-project/SKILL.md` | 하 |
| 4 | opds 진행 현황 행 갱신 | `opal-pilot-dev-short/SKILL.md` | 하 |
| 5 | opd 진행 현황 행 갱신 | `opal-pilot-dev/SKILL.md` | 하 |
| 6 | opdw 진행 현황 행 신규 작성 | `opal-pilot-dev-wireframe/SKILL.md` | 중 |
| 7 | opsdd 일관성 조정 | `opal-pilot-sdd/SKILL.md` | 하 |

### 핵심 설계

#### 2-1. `opal-harness.md` -- 진행 현황 행 구성 규칙 확장

**§2 QA 산출물 표준 파일명 섹션에 단계별 주요 산출물 표 추가** (L103-L114 부근):

기존 QA 산출물 표 아래에 "단계별 주요 산출물 표준 파일명" 표를 추가한다:

```markdown
### 단계별 주요 산출물 표준 파일명

진행 현황 산출물 행에서 추적하는 파일명의 기본값.
오케스트레이터 SKILL.md에서 오버라이드 가능하며, 명시가 없으면 이 표준을 따른다.

| 단계 | 주요 산출물 | 위치 |
|------|-----------|------|
| TASK | `TASK.md` | `tasks/{NNN}-{name}/` |
| ANALYSIS | `ANALYSIS.md` | `tasks/{NNN}-{name}/` (해당 단계가 있는 스킬만) |
| PLAN | `PLAN.md` | `tasks/{NNN}-{name}/` |
| TEST-SCENARIO | `TEST-SCENARIO.md` | `tasks/{NNN}-{name}/` (해당 단계가 있는 스킬만) |
| WIREFRAME | `wireframe.md` | `tasks/{NNN}-{name}/` (opdw 전용) |
| DONE | `DONE.md` | `tasks/{NNN}-{name}/` |
```

**§3 진행 현황 행 구성 규칙 확장** (L204-L208):

기존 규칙에 산출물 행 규칙을 추가한다:

```markdown
**진행 현황 행 구성 규칙**:
- TASK 단계: `작업`, `TASK.md 생성`, `사용자 확인` (Gate 없음)
- 일반 단계(PLAN/EXECUTE 등): `작업`, `{산출물} 생성`, `QA Gate`, `{QA 산출물} 생성`, `State Gate`, `Artifact Gate`, `State Gate`, `PM Gate`, `State Gate`, `사용자 확인` 순
- 최종 단계(EXECUTE/TEST): PM Gate 직후 `DONE.md 생성`, 이어서 `State Gate`, `사용자 확인`
- Gate가 없는 단계(opp TASK 등)는 해당 행 생략
- 산출물이 없는 단계(EXECUTE 작업 = 코드 변경)는 산출물 행 생략
- 오케스트레이터 SKILL.md "STATE.md 도메인 치환값"에 해당 스킬의 진행 현황 행 예시가 명시됨

**산출물 행 규칙**:
1. 위치: `작업` 완료 직후, `QA Gate` 직전
2. 항목명: `{파일명} 생성` (예: `PLAN.md 생성`)
3. 상태 전이: ⬜ → ✅ (파일 생성 확인 시)
4. 순서 강제: 앞 행(작업)이 ✅가 아니면 산출물 행 진행 불가
5. QA 산출물 행: QA Gate 직후, Artifact Gate 직전에 위치
6. DONE.md 행: 최종 단계 PM Gate 직후, 사용자 확인 직전에 위치
```

#### 2-2. `opal-harness-interactive.md` -- §2.5 Artifact Gate 역할 재정의

기존 §2.5 서두에 역할 구분 문구를 추가한다:

```markdown
## 2.5 Artifact Gate (2중 안전장치)

> **1차 보장**: 진행 현황 테이블의 산출물 행이 순서 강제 원칙으로 생성을 보장한다.
> **2차 점검(이 Gate)**: 산출물 행 통과 후에도 파일이 실제로 존재하는지 한 번 더 확인한다.

QA Gate 완료 후 PM Gate 진입 전, 필수 산출물 파일의 존재 여부를 확인한다.
```

나머지 내용(게이트 진입 조건, 자가 점검, 결과 테이블, 차단 원칙 등)은 그대로 유지한다.

#### 2-3. opp 진행 현황 행 예시 (갱신)

```markdown
| # | 단계 | 항목 | 상태 | 시점 |
|---|------|------|------|------|
| 1 | TASK | 작업 | ⬜ | - |
| 2 | TASK | TASK.md 생성 | ⬜ | - |
| 3 | TASK | 사용자 확인 | ⬜ | - |
| 4 | PLAN | 작업 | ⬜ | - |
| 5 | PLAN | PLAN.md 생성 | ⬜ | - |
| 6 | PLAN | QA Gate | ⬜ | - |
| 7 | PLAN | QA-PLAN.md 생성 | ⬜ | - |
| 8 | PLAN | State Gate | ⬜ | - |
| 9 | PLAN | Artifact Gate | ⬜ | - |
| 10 | PLAN | State Gate | ⬜ | - |
| 11 | PLAN | PM Gate | ⬜ | - |
| 12 | PLAN | State Gate | ⬜ | - |
| 13 | PLAN | 사용자 확인 | ⬜ | - |
| 14 | EXECUTE | 작업 | ⬜ | - |
| 15 | EXECUTE | QA Gate | ⬜ | - |
| 16 | EXECUTE | QA-EXECUTE.md 생성 | ⬜ | - |
| 17 | EXECUTE | State Gate | ⬜ | - |
| 18 | EXECUTE | Artifact Gate | ⬜ | - |
| 19 | EXECUTE | State Gate | ⬜ | - |
| 20 | EXECUTE | PM Gate | ⬜ | - |
| 21 | EXECUTE | DONE.md 생성 | ⬜ | - |
| 22 | EXECUTE | State Gate | ⬜ | - |
| 23 | EXECUTE | 사용자 확인 | ⬜ | - |
```

**변경점**: 기존 18행 -> 23행. 추가된 행: TASK.md 생성(#2), PLAN.md 생성(#5), QA-PLAN.md 생성(#7), QA-EXECUTE.md 생성(#16), DONE.md 생성(#21).

#### 2-4. opds 진행 현황 행 예시 (갱신)

```markdown
| # | 단계 | 항목 | 상태 | 시점 |
|---|------|------|------|------|
| 1 | TASK | 작업 | ⬜ | - |
| 2 | TASK | TASK.md 생성 | ⬜ | - |
| 3 | TASK | 사용자 확인 | ⬜ | - |
| 4 | PLAN | 작업 | ⬜ | - |
| 5 | PLAN | PLAN.md 생성 | ⬜ | - |
| 6 | TEST-SCENARIO | 작업 | ⬜ | - |
| 7 | TEST-SCENARIO | TEST-SCENARIO.md 생성 | ⬜ | - |
| 8 | TEST-SCENARIO | State Gate | ⬜ | - |
| 9 | PLAN | QA Gate | ⬜ | - |
| 10 | PLAN | QA-PLAN.md 생성 | ⬜ | - |
| 11 | PLAN | State Gate | ⬜ | - |
| 12 | PLAN | Artifact Gate | ⬜ | - |
| 13 | PLAN | State Gate | ⬜ | - |
| 14 | PLAN | PM Gate | ⬜ | - |
| 15 | PLAN | State Gate | ⬜ | - |
| 16 | PLAN | 사용자 확인 | ⬜ | - |
| 17 | EXECUTE | 작업 | ⬜ | - |
| 18 | EXECUTE | State Gate | ⬜ | - |
| 19 | TEST | 작업 | ⬜ | - |
| 20 | TEST | State Gate | ⬜ | - |
| 21 | TEST | QA Gate | ⬜ | - |
| 22 | TEST | QA-EXECUTE.md 생성 | ⬜ | - |
| 23 | TEST | State Gate | ⬜ | - |
| 24 | TEST | PM Gate | ⬜ | - |
| 25 | TEST | DONE.md 생성 | ⬜ | - |
| 26 | TEST | State Gate | ⬜ | - |
| 27 | TEST | 사용자 확인 | ⬜ | - |
```

**변경점**: 기존 21행 -> 27행. 추가된 행: TASK.md 생성(#2), PLAN.md 생성(#5), TEST-SCENARIO.md 생성(#7), QA-PLAN.md 생성(#10), QA-EXECUTE.md 생성(#22), DONE.md 생성(#25).

#### 2-5. opd 진행 현황 행 예시 (갱신)

```markdown
| # | 단계 | 항목 | 상태 | 시점 |
|---|------|------|------|------|
| 1 | TASK | 작업 | ⬜ | - |
| 2 | TASK | TASK.md 생성 | ⬜ | - |
| 3 | TASK | 사용자 확인 | ⬜ | - |
| 4 | ANALYSIS | 작업 | ⬜ | - |
| 5 | ANALYSIS | ANALYSIS.md 생성 | ⬜ | - |
| 6 | ANALYSIS | QA Gate | ⬜ | - |
| 7 | ANALYSIS | QA-ANALYSIS.md 생성 | ⬜ | - |
| 8 | ANALYSIS | State Gate | ⬜ | - |
| 9 | ANALYSIS | Artifact Gate | ⬜ | - |
| 10 | ANALYSIS | State Gate | ⬜ | - |
| 11 | ANALYSIS | PM Gate | ⬜ | - |
| 12 | ANALYSIS | State Gate | ⬜ | - |
| 13 | ANALYSIS | 사용자 확인 | ⬜ | - |
| 14 | PLAN | 작업 | ⬜ | - |
| 15 | PLAN | PLAN.md 생성 | ⬜ | - |
| 16 | TEST-SCENARIO | 작업 | ⬜ | - |
| 17 | TEST-SCENARIO | TEST-SCENARIO.md 생성 | ⬜ | - |
| 18 | TEST-SCENARIO | State Gate | ⬜ | - |
| 19 | PLAN | QA Gate | ⬜ | - |
| 20 | PLAN | QA-PLAN.md 생성 | ⬜ | - |
| 21 | PLAN | State Gate | ⬜ | - |
| 22 | PLAN | Artifact Gate | ⬜ | - |
| 23 | PLAN | State Gate | ⬜ | - |
| 24 | PLAN | PM Gate | ⬜ | - |
| 25 | PLAN | State Gate | ⬜ | - |
| 26 | PLAN | 사용자 확인 | ⬜ | - |
| 27 | EXECUTE | 작업 | ⬜ | - |
| 28 | EXECUTE | State Gate | ⬜ | - |
| 29 | TEST | 작업 | ⬜ | - |
| 30 | TEST | State Gate | ⬜ | - |
| 31 | TEST | QA Gate | ⬜ | - |
| 32 | TEST | QA-EXECUTE.md 생성 | ⬜ | - |
| 33 | TEST | State Gate | ⬜ | - |
| 34 | TEST | PM Gate | ⬜ | - |
| 35 | TEST | DONE.md 생성 | ⬜ | - |
| 36 | TEST | State Gate | ⬜ | - |
| 37 | TEST | 사용자 확인 | ⬜ | - |
```

**변경점**: 기존 29행 -> 37행. 추가된 행: TASK.md 생성(#2), ANALYSIS.md 생성(#5), QA-ANALYSIS.md 생성(#7), PLAN.md 생성(#15), TEST-SCENARIO.md 생성(#17), QA-PLAN.md 생성(#20), QA-EXECUTE.md 생성(#32), DONE.md 생성(#35).

#### 2-6. opdw 진행 현황 행 예시 (신규)

opdw SKILL.md의 "STATE.md 도메인 치환값" 섹션에 진행 현황 행 예시를 신규 추가한다:

```markdown
**진행 현황 행 예시** (STATE.md 초기 생성 시 이 구조로 작성):

| # | 단계 | 항목 | 상태 | 시점 |
|---|------|------|------|------|
| 1 | TASK | 작업 | ⬜ | - |
| 2 | TASK | TASK.md 생성 | ⬜ | - |
| 3 | TASK | 사용자 확인 | ⬜ | - |
| 4 | WIREFRAME | 작업 | ⬜ | - |
| 5 | WIREFRAME | wireframe.md 생성 | ⬜ | - |
| 6 | WIREFRAME | QA Gate | ⬜ | - |
| 7 | WIREFRAME | QA-WIREFRAME.md 생성 | ⬜ | - |
| 8 | WIREFRAME | State Gate | ⬜ | - |
| 9 | WIREFRAME | Artifact Gate | ⬜ | - |
| 10 | WIREFRAME | State Gate | ⬜ | - |
| 11 | WIREFRAME | PM Gate | ⬜ | - |
| 12 | WIREFRAME | State Gate | ⬜ | - |
| 13 | WIREFRAME | 사용자 확인 | ⬜ | - |
| 14 | EXECUTE | 작업 | ⬜ | - |
| 15 | EXECUTE | QA Gate | ⬜ | - |
| 16 | EXECUTE | QA-EXECUTE.md 생성 | ⬜ | - |
| 17 | EXECUTE | State Gate | ⬜ | - |
| 18 | EXECUTE | PM Gate | ⬜ | - |
| 19 | EXECUTE | DONE.md 생성 | ⬜ | - |
| 20 | EXECUTE | State Gate | ⬜ | - |
| 21 | EXECUTE | 사용자 확인 | ⬜ | - |
```

> WIREFRAME 스킵 시(wireframe.md 기존 존재): WIREFRAME 단계 행(#4-#13)을 `-`로 표기한다.

**참고**: opdw EXECUTE 단계에는 Artifact Gate가 없음 (SKILL.md 원문에 명시 안 됨). SKILL.md EXECUTE 완료 후 흐름: QA Gate -> PM Gate -> DONE.md 생성 -> 사용자 완료 보고.

#### 2-7. opsdd 일관성 조정

opsdd는 독자적 STATE.md 구조("완료 산출물" 테이블 + ACT 목록 + TS 상태)를 사용하므로, 진행 현황 행 기반 산출물 통합을 직접 적용하지 않는다.

대신, "완료 산출물" 섹션에 공통 하네스 규칙 참조 문구를 추가하여 일관성을 유지한다:

```markdown
## 완료 산출물

> 공통 하네스 §2 "단계별 주요 산출물 표준 파일명" + "QA 산출물 표준 파일명" 참조.
> opsdd는 Phase 기반 독자 구조이므로 진행 현황 행 대신 이 테이블로 산출물을 추적한다.

| 산출물 | 상태 |
|--------|------|
...
```

---

## 3. 실행 체크리스트

> 총 7개 Step | Phase 3개
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1     | 1, 2 | 병렬 | 공통 하네스 2개 파일 (독립 섹션) |
> | 2     | 3, 4, 5, 6 | 병렬 | 4개 스킬 파일 (독립 파일) |
> | 3     | 7 | 순차 | Step 1 의존 (하네스 규칙 참조) |

### Step 1: 공통 하네스 -- 산출물 행 규칙 + 표준 파일명 추가
- [x] 완료
- **파일**: `opal/core/references/opal-harness.md`
- **작업 내용**:
  1. §2 "QA 산출물 표준 파일명" 섹션 아래에 "단계별 주요 산출물 표준 파일명" 서브섹션 추가
  2. §3 "진행 현황 행 구성 규칙" (L204-L208)을 산출물 행 규칙 포함 버전으로 교체
  3. §3 이벤트 테이블(L135-L151)에 산출물 생성 이벤트 행 추가
- **완료 기준**:
  - "단계별 주요 산출물 표준 파일명" 표가 TASK/ANALYSIS/PLAN/TEST-SCENARIO/WIREFRAME/DONE 산출물을 포함
  - "진행 현황 행 구성 규칙"에 산출물 행 위치/형식/상태전이 규칙이 명시
  - 이벤트 테이블에 "산출물 생성" 행이 추가되고 갱신 주체/강제 여부가 기재
- **테스트**: 규칙을 읽고 opp/opds/opd/opdw 진행 현황 행 예시를 도출할 수 있는지 확인
- **의존**: 없음

### Step 2: Artifact Gate 역할 재정의
- [x] 완료
- **파일**: `opal/core/references/opal-harness-interactive.md`
- **작업 내용**:
  1. §2.5 제목에 "(2중 안전장치)" 추가
  2. §2.5 서두에 "1차 보장(산출물 행) / 2차 점검(이 Gate)" 역할 구분 문구 추가
  3. 기존 게이트 동작(진입 조건, 자가 점검, 결과 테이블, 차단 원칙 등)은 그대로 유지
- **완료 기준**:
  - §2.5 제목과 서두에 역할 구분이 명확히 기재
  - 기존 Artifact Gate 동작이 변경 없이 보존
- **테스트**: §2.5를 읽고 산출물 행과 Artifact Gate의 역할 차이를 구분할 수 있는지 확인
- **의존**: 없음

### Step 3: opp 진행 현황 행 예시 갱신
- [x] 완료
- **파일**: `opal/skills/opal-pilot-project/SKILL.md`
- **작업 내용**: "STATE.md 도메인 치환값" 섹션의 진행 현황 행 예시를 2-3절 설계(23행)로 교체
- **완료 기준**: 진행 현황 행 예시에 TASK.md/PLAN.md/QA-PLAN.md/QA-EXECUTE.md/DONE.md 생성 행이 포함
- **테스트**: 행 번호가 연속이고, 단계별 산출물이 누락 없이 포함되는지 확인
- **의존**: Step 1 (규칙 참조)

### Step 4: opds 진행 현황 행 예시 갱신
- [x] 완료
- **파일**: `opal/skills/opal-pilot-dev-short/SKILL.md`
- **작업 내용**: "STATE.md 도메인 치환값" 섹션의 진행 현황 행 예시를 2-4절 설계(27행)로 교체
- **완료 기준**: 진행 현황 행 예시에 TASK.md/PLAN.md/TEST-SCENARIO.md/QA-PLAN.md/QA-EXECUTE.md/DONE.md 생성 행이 포함
- **테스트**: 행 번호가 연속이고, 단계별 산출물이 누락 없이 포함되는지 확인
- **의존**: Step 1 (규칙 참조)

### Step 5: opd 진행 현황 행 예시 갱신
- [x] 완료
- **파일**: `opal/skills/opal-pilot-dev/SKILL.md`
- **작업 내용**: "STATE.md 도메인 설정" 섹션의 진행 현황 행 예시를 2-5절 설계(37행)로 교체
- **완료 기준**: 진행 현황 행 예시에 TASK.md/ANALYSIS.md/QA-ANALYSIS.md/PLAN.md/TEST-SCENARIO.md/QA-PLAN.md/QA-EXECUTE.md/DONE.md 생성 행이 포함
- **테스트**: 행 번호가 연속이고, 단계별 산출물이 누락 없이 포함되는지 확인
- **의존**: Step 1 (규칙 참조)

### Step 6: opdw 진행 현황 행 예시 신규 작성
- [x] 완료
- **파일**: `opal/skills/opal-pilot-dev-wireframe/SKILL.md`
- **작업 내용**: "STATE.md 도메인 치환값" 섹션에 진행 현황 행 예시(21행)를 2-6절 설계에 따라 신규 추가. WIREFRAME 스킵 주석도 포함.
- **완료 기준**: 진행 현황 행 예시에 TASK.md/wireframe.md/QA-WIREFRAME.md/QA-EXECUTE.md/DONE.md 생성 행이 포함
- **테스트**: 행 번호가 연속이고, WIREFRAME 스킵 조건 주석이 있는지 확인
- **의존**: Step 1 (규칙 참조)

### Step 7: opsdd 일관성 조정
- [x] 완료
- **파일**: `opal/skills/opal-pilot-sdd/SKILL.md`
- **작업 내용**: "STATE.md 구조" 내 "완료 산출물" 섹션에 공통 하네스 §2 참조 문구 추가
- **완료 기준**: "완료 산출물" 섹션 상단에 공통 하네스 참조 문구가 있고, 기존 테이블 구조가 보존
- **테스트**: 참조 문구가 §2와 정확히 매핑되는지, 기존 내용 손상이 없는지 확인
- **의존**: Step 1 (하네스 규칙 참조)

---

## 4. QA 체크리스트

### 기능 테스트
- [x] 공통 하네스 §2에 "단계별 주요 산출물 표준 파일명" 표가 존재하고, 모든 단계(TASK/ANALYSIS/PLAN/TEST-SCENARIO/WIREFRAME/DONE)를 커버하는가
- [x] 공통 하네스 §3 "진행 현황 행 구성 규칙"에 산출물 행 위치(작업 직후, QA Gate 직전), 항목명 형식(`{파일명} 생성`), 상태 전이가 명시되는가
- [x] Artifact Gate(§2.5) 역할이 "2중 안전장치"로 재정의되고, 기존 동작은 보존되는가
- [x] opp 진행 현황 행 예시에 TASK.md/PLAN.md/QA-PLAN.md/QA-EXECUTE.md/DONE.md 생성 행이 포함되는가
- [x] opds 진행 현황 행 예시에 TASK.md/PLAN.md/TEST-SCENARIO.md/QA-PLAN.md/QA-EXECUTE.md/DONE.md 생성 행이 포함되는가
- [x] opd 진행 현황 행 예시에 TASK.md/ANALYSIS.md/QA-ANALYSIS.md/PLAN.md/TEST-SCENARIO.md/QA-PLAN.md/QA-EXECUTE.md/DONE.md 생성 행이 포함되는가
- [x] opdw 진행 현황 행 예시가 신규 생성되고, TASK.md/wireframe.md/QA-WIREFRAME.md/QA-EXECUTE.md/DONE.md 생성 행이 포함되는가
- [x] opsdd "완료 산출물" 섹션에 공통 하네스 참조 문구가 추가되고, 기존 테이블 구조가 보존되는가

### 일관성 테스트
- [x] 5개 스킬(opp/opds/opd/opdw/opsdd)의 진행 현황 행이 각각의 SKILL.md 단계 흐름(STEP 서술)과 일치하는가
- [x] 공통 하네스 "행 구성 규칙"으로 각 스킬의 진행 현황 행을 도출했을 때, 실제 예시와 일치하는가
- [x] 산출물 행의 항목명이 §2 "단계별 주요 산출물 표준 파일명" 또는 "QA 산출물 표준 파일명"과 일치하는가
- [x] 각 진행 현황 행 예시의 행 번호가 1부터 연속 증가하는가
- [x] Artifact Gate 역할 재정의가 기존 Gate Fail 공통 처리(§5)와 충돌하지 않는가

### 문서 품질
- [x] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가
- [x] 기존 문서의 변경이력 섹션에 이번 변경이 추가되는가 (버전, 날짜, 변경내용)
- [x] 마크다운 테이블 정렬이 올바른가

---

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| 산출물 행 추가로 테이블 행 수 증가 (예: opd 29→37행) | 워커가 테이블을 갱신할 때 행 번호 오류 가능성 | 행 번호는 고정값이므로 혼란 최소화. 기존 State Gate가 미갱신을 즉시 감지하여 보완. |
| opdw 진행 현황 행 예시가 없었으므로 신규 추가 시 기존 동작과 불일치 위험 | 기존 opdw 태스크의 STATE.md가 예시 없이 운영되었을 수 있음 | 소급 변경 안 함. 신규 태스크부터 적용. |
| opsdd 독자 구조와 공통 규칙 간 인지 혼란 | PM이 opsdd에도 진행 현황 행 기반 규칙을 적용하려 할 수 있음 | "opsdd는 독자 구조" 명시 + 공통 하네스 참조 문구로 구분 |
| TASK.md 생성 행 추가가 TASK 공통 프로세스와 중복으로 느껴질 수 있음 | TASK 단계는 "직접 수행"이므로 산출물 행이 불필요하다는 의견 가능 | TASK.md 생성은 State Gate 전에 이미 완료되므로, 행 추가는 "추적의 일관성"을 위한 것. 필요 시 캡틴 판단으로 제거 가능. |
