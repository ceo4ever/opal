# PLAN: PM Gate 점검 목록 -- TASK.md 요구사항 추가

> 작성일: 2026-04-11
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `opal/skills/opal-pilot-project/SKILL.md` | 프로젝트 범용 오케스트레이터 (opp) | O |
| `opal/skills/opal-pilot-dev/SKILL.md` | Full Task 오케스트레이터 (opd) | O |
| `opal/skills/opal-pilot-dev-short/SKILL.md` | Short Task 오케스트레이터 (opds) | O |
| `opal/skills/opal-pilot-write-tech/SKILL.md` | 기획 산출물 네트워크 오케스트레이터 (opwt) | O |
| `opal/skills/opal-pilot-sdd/SKILL.md` | SDD 오케스트레이터 (opsdd) | O |
| `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | Wireframe UI 오케스트레이터 (opdw) | O |

### 현재 상태

6개 파일럿 스킬의 `## PM Gate 점검 목록` 섹션을 직접 Read하여 확인한 결과:

| 파일 | Phase | 현재 산출물 | 현재 체크리스트 위치 | 현재 버전 |
|------|-------|-----------|---------------------|----------|
| opal-pilot-project | PLAN | PLAN.md, QA-PLAN.md | PLAN.md SS3, SS4 | v2.3 |
| opal-pilot-dev | PLAN+TEST-SCENARIO | PLAN.md, TEST-SCENARIO.md, QA-PLAN.md | PLAN.md SS3, SS4 | v2.7 |
| opal-pilot-dev-short | PLAN+TEST-SCENARIO | PLAN.md, TEST-SCENARIO.md, QA-PLAN.md | PLAN.md SS3, SS4 | v2.7 |
| opal-pilot-write-tech | PLAN | PLAN.md, QA-PLAN.md | PLAN.md SS3, SS4 | v2.8 |
| opal-pilot-sdd | SPEC | SPEC.md, QA-SPEC.md | - | v2.6.0 |
| opal-pilot-dev-wireframe | WIREFRAME | wireframe.md, QA-WIREFRAME.md | - | v1.9 |

> SS = Section Symbol (마크다운 렌더링 회피를 위한 표기)

**모든 파일에서 TASK.md가 PM Gate 점검 목록의 산출물/체크리스트 위치에 포함되어 있지 않다.** 이로 인해 PM Gate 자가 진단 5단계 흐름에서 TASK.md 요구사항 체크박스 갱신 상태를 확인하지 않고 통과되는 구조 결함이 존재한다.

### 영향 범위

- **직접 영향**: PM Gate 자가 진단 절차 (opal-harness-interactive SS3 Step 2)가 각 SKILL.md의 PM Gate 점검 목록을 참조하므로, 해당 테이블에 TASK.md를 추가하면 자가 진단 시 TASK.md 요구사항 체크리스트가 자동으로 확인 대상에 포함된다.
- **간접 영향 없음**: 하네스 interactive SS3의 "체크리스트 갱신 상태 확인" 절은 이미 TASK.md 요구사항 체크박스 확인을 의도하고 있으므로, 하네스 문서 자체의 변경은 불필요하다.
- **범위 외 확인**: op-task-qa, op-dev-qa SKILL.md 변경 없음. 파이프라인 흐름 변경 없음.

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| (없음) | | |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `opal/skills/opal-pilot-project/SKILL.md` | PM Gate 점검 목록 PLAN Phase에 TASK.md 추가 + 변경이력 |
| 2 | `opal/skills/opal-pilot-dev/SKILL.md` | PM Gate 점검 목록 PLAN+TEST-SCENARIO Phase에 TASK.md 추가 + 변경이력 |
| 3 | `opal/skills/opal-pilot-dev-short/SKILL.md` | PM Gate 점검 목록 PLAN+TEST-SCENARIO Phase에 TASK.md 추가 + 변경이력 |
| 4 | `opal/skills/opal-pilot-write-tech/SKILL.md` | PM Gate 점검 목록 PLAN Phase에 TASK.md 추가 + 변경이력 |
| 5 | `opal/skills/opal-pilot-sdd/SKILL.md` | PM Gate 점검 목록 SPEC Phase에 TASK.md 추가 + 변경이력 |
| 6 | `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | PM Gate 점검 목록 WIREFRAME Phase에 TASK.md 추가 + 변경이력 |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| (없음) | | |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | PLAN Phase PM Gate 점검 목록 수정 + 변경이력 | opal-pilot-project/SKILL.md | 낮음 |
| 2 | PLAN+TEST-SCENARIO Phase PM Gate 점검 목록 수정 + 변경이력 | opal-pilot-dev/SKILL.md | 낮음 |
| 3 | PLAN+TEST-SCENARIO Phase PM Gate 점검 목록 수정 + 변경이력 | opal-pilot-dev-short/SKILL.md | 낮음 |
| 4 | PLAN Phase PM Gate 점검 목록 수정 + 변경이력 | opal-pilot-write-tech/SKILL.md | 낮음 |
| 5 | SPEC Phase PM Gate 점검 목록 수정 + 변경이력 | opal-pilot-sdd/SKILL.md | 낮음 |
| 6 | WIREFRAME Phase PM Gate 점검 목록 수정 + 변경이력 | opal-pilot-dev-wireframe/SKILL.md | 낮음 |

### 핵심 설계

6개 파일 모두 동일한 패턴으로 변경한다:

#### 변경 패턴 (공통)

**PM Gate 점검 목록 테이블 수정**:
- 각 스킬의 PLAN-equivalent Phase(PLAN, PLAN+TEST-SCENARIO, SPEC, WIREFRAME) 행에서:
  - **산출물 컬럼**: 기존 값 앞에 `TASK.md, ` 추가
  - **체크리스트 위치 컬럼**: 기존 값 앞에 `TASK.md 요구사항, ` 추가 (기존 값이 `-`인 경우 `TASK.md 요구사항`으로 교체)

#### 파일별 변경 상세

**1. opal-pilot-project/SKILL.md** (v2.3 -> v2.4)

현재:
```
| PLAN | PLAN.md, QA-PLAN.md | PLAN.md §3, §4 |
```
변경 후:
```
| PLAN | TASK.md, PLAN.md, QA-PLAN.md | TASK.md 요구사항, PLAN.md §3, §4 |
```

**2. opal-pilot-dev/SKILL.md** (v2.7 -> v2.8)

현재:
```
| PLAN+TEST-SCENARIO | PLAN.md, TEST-SCENARIO.md, QA-PLAN.md | PLAN.md §3, §4 |
```
변경 후:
```
| PLAN+TEST-SCENARIO | TASK.md, PLAN.md, TEST-SCENARIO.md, QA-PLAN.md | TASK.md 요구사항, PLAN.md §3, §4 |
```

**3. opal-pilot-dev-short/SKILL.md** (v2.7 -> v2.8)

현재:
```
| PLAN+TEST-SCENARIO | PLAN.md, TEST-SCENARIO.md, QA-PLAN.md | PLAN.md §3, §4 |
```
변경 후:
```
| PLAN+TEST-SCENARIO | TASK.md, PLAN.md, TEST-SCENARIO.md, QA-PLAN.md | TASK.md 요구사항, PLAN.md §3, §4 |
```

**4. opal-pilot-write-tech/SKILL.md** (v2.8 -> v2.9)

현재:
```
| PLAN | PLAN.md, QA-PLAN.md | PLAN.md §3, §4 |
```
변경 후:
```
| PLAN | TASK.md, PLAN.md, QA-PLAN.md | TASK.md 요구사항, PLAN.md §3, §4 |
```

**5. opal-pilot-sdd/SKILL.md** (v2.6.0 -> v2.7.0)

현재:
```
| SPEC | SPEC.md, QA-SPEC.md | - |
```
변경 후:
```
| SPEC | TASK.md, SPEC.md, QA-SPEC.md | TASK.md 요구사항 |
```

**6. opal-pilot-dev-wireframe/SKILL.md** (v1.9 -> v2.0)

현재:
```
| WIREFRAME | wireframe.md, QA-WIREFRAME.md | - |
```
변경 후:
```
| WIREFRAME | TASK.md, wireframe.md, QA-WIREFRAME.md | TASK.md 요구사항 |
```

#### 변경이력 추가 (공통 패턴)

각 파일의 변경이력 테이블에 다음 행을 추가:
```
| {다음 버전} | 2026-04-11 | PM Gate 점검 목록 -- PLAN-equivalent Phase에 TASK.md 요구사항 추가 (108) |
```

## 3. 실행 체크리스트

> 총 6개 Step | Phase 1개
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1     | 1, 2, 3, 4, 5, 6 | 병렬 | 모두 독립 파일, 의존 없음 |

### Step 1: opal-pilot-project SKILL.md 수정
- [x] 완료
- **파일**: `opal/skills/opal-pilot-project/SKILL.md`
- **작업 내용**:
  1. PM Gate 점검 목록의 PLAN 행 산출물을 `TASK.md, PLAN.md, QA-PLAN.md`로 변경
  2. 체크리스트 위치를 `TASK.md 요구사항, PLAN.md §3, §4`로 변경
  3. 변경이력에 `v2.4 | 2026-04-11 | PM Gate 점검 목록 -- PLAN-equivalent Phase에 TASK.md 요구사항 추가 (108)` 추가
- **완료 기준**: PLAN 행에 TASK.md가 산출물과 체크리스트 위치 양쪽에 존재
- **테스트**: Read로 PM Gate 점검 목록 섹션 확인 + 변경이력 최신 행 확인
- **의존**: 없음

### Step 2: opal-pilot-dev SKILL.md 수정
- [x] 완료
- **파일**: `opal/skills/opal-pilot-dev/SKILL.md`
- **작업 내용**:
  1. PM Gate 점검 목록의 PLAN+TEST-SCENARIO 행 산출물을 `TASK.md, PLAN.md, TEST-SCENARIO.md, QA-PLAN.md`로 변경
  2. 체크리스트 위치를 `TASK.md 요구사항, PLAN.md §3, §4`로 변경
  3. 변경이력에 `v2.8 | 2026-04-11 | PM Gate 점검 목록 -- PLAN-equivalent Phase에 TASK.md 요구사항 추가 (108)` 추가
- **완료 기준**: PLAN+TEST-SCENARIO 행에 TASK.md가 산출물과 체크리스트 위치 양쪽에 존재
- **테스트**: Read로 PM Gate 점검 목록 섹션 확인 + 변경이력 최신 행 확인
- **의존**: 없음

### Step 3: opal-pilot-dev-short SKILL.md 수정
- [x] 완료
- **파일**: `opal/skills/opal-pilot-dev-short/SKILL.md`
- **작업 내용**:
  1. PM Gate 점검 목록의 PLAN+TEST-SCENARIO 행 산출물을 `TASK.md, PLAN.md, TEST-SCENARIO.md, QA-PLAN.md`로 변경
  2. 체크리스트 위치를 `TASK.md 요구사항, PLAN.md §3, §4`로 변경
  3. 변경이력에 `v2.8 | 2026-04-11 | PM Gate 점검 목록 -- PLAN-equivalent Phase에 TASK.md 요구사항 추가 (108)` 추가
- **완료 기준**: PLAN+TEST-SCENARIO 행에 TASK.md가 산출물과 체크리스트 위치 양쪽에 존재
- **테스트**: Read로 PM Gate 점검 목록 섹션 확인 + 변경이력 최신 행 확인
- **의존**: 없음

### Step 4: opal-pilot-write-tech SKILL.md 수정
- [x] 완료
- **파일**: `opal/skills/opal-pilot-write-tech/SKILL.md`
- **작업 내용**:
  1. PM Gate 점검 목록의 PLAN 행 산출물을 `TASK.md, PLAN.md, QA-PLAN.md`로 변경
  2. 체크리스트 위치를 `TASK.md 요구사항, PLAN.md §3, §4`로 변경
  3. 변경이력에 `v2.9 | 2026-04-11 | PM Gate 점검 목록 -- PLAN-equivalent Phase에 TASK.md 요구사항 추가 (108)` 추가
- **완료 기준**: PLAN 행에 TASK.md가 산출물과 체크리스트 위치 양쪽에 존재
- **테스트**: Read로 PM Gate 점검 목록 섹션 확인 + 변경이력 최신 행 확인
- **의존**: 없음

### Step 5: opal-pilot-sdd SKILL.md 수정
- [x] 완료
- **파일**: `opal/skills/opal-pilot-sdd/SKILL.md`
- **작업 내용**:
  1. PM Gate 점검 목록의 SPEC 행 산출물을 `TASK.md, SPEC.md, QA-SPEC.md`로 변경
  2. 체크리스트 위치를 `TASK.md 요구사항`으로 변경 (기존 `-`)
  3. 변경이력에 `v2.7.0 | 2026-04-11 | PM Gate 점검 목록 -- PLAN-equivalent Phase에 TASK.md 요구사항 추가 (108)` 추가
- **완료 기준**: SPEC 행에 TASK.md가 산출물과 체크리스트 위치 양쪽에 존재
- **테스트**: Read로 PM Gate 점검 목록 섹션 확인 + 변경이력 최신 행 확인
- **의존**: 없음

### Step 6: opal-pilot-dev-wireframe SKILL.md 수정
- [x] 완료
- **파일**: `opal/skills/opal-pilot-dev-wireframe/SKILL.md`
- **작업 내용**:
  1. PM Gate 점검 목록의 WIREFRAME 행 산출물을 `TASK.md, wireframe.md, QA-WIREFRAME.md`로 변경
  2. 체크리스트 위치를 `TASK.md 요구사항`으로 변경 (기존 `-`)
  3. 변경이력에 `v2.0 | 2026-04-11 | PM Gate 점검 목록 -- PLAN-equivalent Phase에 TASK.md 요구사항 추가 (108)` 추가
- **완료 기준**: WIREFRAME 행에 TASK.md가 산출물과 체크리스트 위치 양쪽에 존재
- **테스트**: Read로 PM Gate 점검 목록 섹션 확인 + 변경이력 최신 행 확인
- **의존**: 없음

## 4. QA 체크리스트

### 기능 테스트
- [x] opal-pilot-project SKILL.md PLAN Phase에 TASK.md 산출물 + 체크리스트 위치 추가됨
- [x] opal-pilot-dev SKILL.md PLAN+TEST-SCENARIO Phase에 TASK.md 산출물 + 체크리스트 위치 추가됨
- [x] opal-pilot-dev-short SKILL.md PLAN+TEST-SCENARIO Phase에 TASK.md 산출물 + 체크리스트 위치 추가됨
- [x] opal-pilot-write-tech SKILL.md PLAN Phase에 TASK.md 산출물 + 체크리스트 위치 추가됨
- [x] opal-pilot-sdd SKILL.md SPEC Phase에 TASK.md 산출물 + 체크리스트 위치 추가됨
- [x] opal-pilot-dev-wireframe SKILL.md WIREFRAME Phase에 TASK.md 산출물 + 체크리스트 위치 추가됨
- [x] 각 파일의 변경이력에 (108) 태스크 행이 추가됨

### 일관성 테스트
- [x] 6개 파일 모두 동일한 패턴(TASK.md 맨 앞 추가, TASK.md 요구사항 맨 앞 추가)으로 수정됨
- [x] EXECUTE/기타 Phase 행은 변경되지 않음 (PLAN-equivalent Phase만 수정)
- [x] 기존 산출물/체크리스트 위치 값이 유지됨 (앞에 TASK.md만 추가)
- [x] 변경이력 버전이 각 파일의 최신 버전 + 0.1 (또는 semver 규칙)으로 올바르게 채번됨

### 문서 품질
- [x] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가
- [x] 마크다운 테이블 정렬이 깨지지 않았는가
- [x] 변경이력 날짜가 2026-04-11인가

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| PM Gate 점검 목록 테이블 외 다른 섹션에도 TASK.md 참조가 필요할 수 있음 | 낮음 - 하네스 SS3에 이미 의도가 명시되어 있으므로, 점검 목록만 보완하면 자가 진단 흐름이 자동으로 TASK.md를 포함한다 | 하네스 interactive SS3 문서와 크로스 체크 완료 -- 추가 변경 불필요 확인 |
| opsdd의 버전 형식이 다름 (semver v2.6.0 vs 다른 파일 v2.7) | 낮음 - 각 파일의 기존 버전 형식을 유지하면 됨 | opsdd는 semver 형식(v2.7.0) 유지, 나머지는 기존 형식(vX.Y) 유지 |
