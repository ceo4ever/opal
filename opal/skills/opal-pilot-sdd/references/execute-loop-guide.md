# EXECUTE-LOOP 상세 가이드

> opal-pilot-sdd Phase 6: EXECUTE-LOOP의 상세 운영 지침.
> 오케스트레이터(opsdd)가 태스크별 반복 실행을 관리할 때 참조한다.
> SKILL.md에서 분리된 상세 내용.

---

## 1. 개요

EXECUTE-LOOP는 tasks.md에 정의된 태스크를 의존 순서에 따라 반복 실행하는 단계이다. 각 태스크는 기존 opal-pilot 오케스트레이터(opds/opd/opp)에 위임하여 실행하며, opsdd 오케스트레이터가 루프 관리, 상태 갱신, 검증 루프를 담당한다.

**핵심 원칙**:
- 기존 opal-pilot 파이프라인을 재활용한다 (신규 실행 스킬 불필요)
- tasks.md의 의존관계 그래프가 실행 순서를 결정한다
- SDD 컨텍스트(spec.md, SPEC-PLAN.md, AC/TS 매핑)를 디스패치 시 주입한다
- TDD 원칙: 테스트 먼저 작성 후 구현

---

## 2. 태스크별 실행 흐름

```
for each task T in dependency_order(tasks.md):
  1. 스킬 결정 (tasks.md의 예상 규모 기반)
  2. SDD 컨텍스트 주입 + 디스패치
  3. 오케스트레이터 완료 대기
  4. 상태 갱신 (tasks.md, test-scenarios.md, STATE.md)
  5. 다음 태스크 또는 그룹으로 진행
```

### 상세 단계

**2-1. tasks.md에서 다음 실행 대상 결정**:
- 의존관계 그래프에서 모든 선행 태스크가 완료된 태스크를 선택한다
- 복수의 태스크가 실행 가능하면 병렬 그룹으로 처리한다 (섹션 5 참조)

**2-2. 스킬 결정**:
- tasks.md의 각 태스크에 기록된 `예상 규모`와 `추천 스킬`을 참조한다
- 스킬 결정 기준 테이블 (섹션 3)에 따라 최종 결정한다

**2-3. 디스패치**:
- SDD 컨텍스트 주입 디스패치 프롬프트 (섹션 4)를 사용한다
- 태스크 폴더: `specs/{NNN}-{feature}/tasks/T{N}-{name}/`

**2-4. 완료 후 상태 갱신**:
- 섹션 6의 상태 갱신 절차를 따른다

---

## 3. 스킬 결정 기준 테이블

tasks.md의 `예상 규모`와 `추천 스킬`을 기반으로 실행 스킬을 결정한다.

| 조건 | 스킬 | 파이프라인 | 적용 상황 |
|------|------|----------|----------|
| Small / Standard, 코드 작업, 파일 1~3개 | `opds` | TASK -> PLAN+TEST-SCENARIO -> EXECUTE | 단일 모듈, 구조 명확, 분석 불필요 |
| Large, 코드 작업, 파일 4개+, 다중 모듈 | `opd` | TASK -> ANALYSIS -> PLAN+TEST-SCENARIO -> EXECUTE | 코드 분석 필요, 다중 모듈 영향 |
| 비코드 작업 (문서, 설정, 스크립트) | `opp` | TASK -> PLAN -> EXECUTE | 코드 외 산출물 |

### 스킬 전환 규칙

EXECUTE-LOOP 진행 중 스킬 전환이 필요할 수 있다:

| 전환 | 조건 | 절차 |
|------|------|------|
| opds -> opd | opds 실행 중 예상보다 복잡 (분석 필요, 파일 증가) | PM 승인 후 opd로 재디스패치 |
| opd -> opds | opd 분석 결과 예상보다 단순 | PM 판단으로 opds 전환 가능 |
| opp -> opds/opd | 비코드로 판단했으나 코드 변경 필요 | PM 판단으로 전환 |

**agentic 모드**: 스킬 전환 시 AGENTIC-LOG.md에 `DECISION` 카테고리로 전환 근거를 기록한다.

---

## 4. SDD 컨텍스트 주입 디스패치 프롬프트

EXECUTE-LOOP에서 기존 opal-pilot 오케스트레이터를 호출할 때, SDD 컨텍스트를 주입하여 spec 기반 개발을 보장한다.

### 디스패치 프롬프트 템플릿

```
[WORKER] {스킬명} 스킬을 수행하라.

**태스크 폴더**: specs/{NNN}-{feature}/tasks/T{N}-{name}/

**SDD 컨텍스트**:
- **spec.md**: specs/{NNN}-{feature}/spec.md
- **SPEC-PLAN.md**: specs/{NNN}-{feature}/SPEC-PLAN.md
- **AC 매핑**: {해당 태스크의 AC 목록 -- 예: AC-01, AC-03}
- **TS 매핑**: {해당 태스크의 TS 목록 -- 예: TS-01, TS-02, TS-04}
- **TDD 지시**: 테스트 먼저 작성 후 구현

**태스크 설명**: {tasks.md에서 해당 태스크의 범위/설명}

**완료 기준**: {tasks.md에서 해당 태스크의 완료 기준 -- 예: TS-01, TS-02 Green}

**하네스 Guards**: 구현 승인됨. 커밋 허용. `~/.opal/` 직접 수정 금지.
```

### 필드별 설명

| 필드 | 설명 | 출처 |
|------|------|------|
| `{스킬명}` | opds, opd, opp 중 하나 | 스킬 결정 기준 테이블 |
| `spec.md` | 기능 명세 SSOT 경로 | 고정 |
| `SPEC-PLAN.md` | 아키텍처 설계 경로 | 고정 |
| `AC 매핑` | 해당 태스크가 구현하는 AC 목록 | tasks.md > 해당 태스크 > AC 매핑 |
| `TS 매핑` | 해당 태스크가 통과해야 할 TS 목록 | tasks.md > 해당 태스크 > TS 매핑 |
| `TDD 지시` | 테스트 우선 구현 지시 | 고정 |
| `태스크 설명` | 해당 태스크의 범위와 변경 대상 | tasks.md > 해당 태스크 > 범위 |
| `완료 기준` | 해당 태스크의 완료 판단 기준 | tasks.md > 해당 태스크 > 완료 기준 |

### TDD 워커 지시 상세

디스패치된 워커(opds/opd)에게 TDD 패턴을 강제한다:

1. **Red**: test-scenarios.md에서 해당 TS의 시나리오를 읽고 테스트 스켈레톤을 먼저 생성한다
2. **Green**: 테스트를 통과하는 최소한의 구현 코드를 작성한다
3. **Refactor**: 코드 품질을 개선한다 (테스트가 깨지지 않도록)

워커가 참조할 테스트 시나리오 정보:
```
테스트 시나리오 참조: specs/{NNN}-{feature}/tests/test-scenarios.md
해당 시나리오:
- TS-01: {시나리오명} -- {유형} -- GIVEN: {조건}, WHEN: {행위}, THEN: {기대}
- TS-02: {시나리오명} -- {유형} -- GIVEN: {조건}, WHEN: {행위}, THEN: {기대}
```

---

## 5. 병렬 실행 패턴

oppd Phase 3의 병렬 실행 패턴을 opsdd EXECUTE-LOOP에 적용한다.

### 5-1. 의존관계 그래프에서 병렬 그룹 빌드

tasks.md의 `실행 그룹` 섹션 또는 `의존관계 그래프`에서 병렬 그룹을 도출한다.

```python
# 의사코드 (Kahn's algorithm 기반 -- oppd parallel-execution-guide 참조)
groups = buildParallelGroups(tasks.md)

for each group in groups:
  if group has single task:
    -> 순차 실행 (일반 디스패치)
  if group has multiple independent tasks:
    -> worktree 격리 + 병렬 워커 디스패치
    -> 결과 수집 -> 순차 머지 -> 통합 테스트
    -> worktree 정리
```

### 5-2. worktree 격리

각 병렬 태스크는 독립된 git worktree에서 실행한다.

**디렉토리 구조**:
```
{프로젝트 루트}/
├── .worktrees/                     # worktree 루트 (gitignore 대상)
│   ├── {spec-NNN}-T{N}/            # T{N} 태스크 전용 worktree
│   └── {spec-NNN}-T{M}/            # T{M} 태스크 전용 worktree
└── specs/
    └── {NNN}-{feature}/
        └── tasks/
            ├── T{N}-{name}/
            └── T{M}-{name}/
```

**브랜치 네이밍**: `feat/opsdd-{spec-NNN}-T{N}` (예: `feat/opsdd-001-T2`)

**worktree 생성**:
```bash
mkdir -p .worktrees
git worktree add .worktrees/{spec-NNN}-T{N} -b feat/opsdd-{spec-NNN}-T{N}
```

**worktree 정리** (머지 완료 후):
```bash
git worktree remove .worktrees/{spec-NNN}-T{N}
git branch -d feat/opsdd-{spec-NNN}-T{N}
```

### 5-3. 병렬 디스패치

병렬 그룹의 모든 태스크에 대해 Agent 도구를 동일 응답 내에서 병렬 호출한다.

각 워커에게 worktree 경로를 명시:
```
**작업 디렉토리**: {프로젝트 루트}/.worktrees/{spec-NNN}-T{N}/
**브랜치**: feat/opsdd-{spec-NNN}-T{N}
**제약**: 이 worktree 내에서만 파일을 수정하라.
```

### 5-4. 결과 수집과 머지

1. 모든 병렬 워커 완료 대기
2. 변경 범위가 작은 순서대로 main 브랜치에 순차 머지
3. 각 머지 후 즉시 검증 (lint -> build -> test)
4. 머지 충돌 발생 시 PM이 조정 (자동 해결 가능하면 직접, 아니면 에스컬레이션)
5. 모든 머지 완료 후 통합 테스트

### 5-5. Fallback

| 환경 | 전략 |
|------|------|
| Agent 도구 + worktree 지원 | 완전 병렬 실행 |
| Agent 도구 없음 + worktree 지원 | worktree 격리 + 순차 디스패치 |
| 둘 다 미지원 | 순차 실행 (메인 브랜치에서 직접) |

---

## 6. 상태 갱신 절차

EXECUTE-LOOP에서 각 태스크의 실행 상태를 3곳에 동기화한다.

### 6-1. tasks.md 상태 갱신

| 이벤트 | 갱신 |
|--------|------|
| 태스크 실행 시작 | `상태: ⬜ 대기` -> `상태: 🔄 진행 중` |
| 태스크 실행 완료 (성공) | `상태: 🔄 진행 중` -> `상태: ✅ 완료` |
| 태스크 실행 실패 | `상태: 🔄 진행 중` -> `상태: ❌ 실패` |

### 6-2. test-scenarios.md 상태 갱신

| 이벤트 | 갱신 |
|--------|------|
| 해당 태스크의 TS 테스트 통과 | `상태: Red` -> `상태: Green` |
| 해당 태스크의 TS 테스트 실패 | `상태: Red` -> `상태: Fail` (재시도 루프 진입) |

### 6-3. STATE.md 진행 현황 갱신

```markdown
## 현재 상태
- Phase: EXECUTE-LOOP
- 진행: T{현재}/{총 태스크 수}
- 상태: 진행 중
```

**갱신 시점**:
- 태스크 시작/완료/실패마다 갱신
- 병렬 그룹 시작/완료마다 갱신
- 검증 루프 진입/완료마다 갱신

---

## 7. 검증 루프

oppd의 Layered Verification 모델을 EXECUTE-LOOP 내 각 태스크에 적용한다.

### 7-1. 검증 계층

| 계층 | 검증 대상 | 최대 재시도 |
|------|----------|-----------|
| L1: lint/format | 코드 스타일, 미사용 변수 | 제한 없음 |
| L2: build/type | 컴파일 오류, 타입 불일치 | 2회 |
| L3a: unit/integration | 컴포넌트, 함수, API 테스트 | 3회 |
| L3b: E2E | 브라우저 시나리오 (해당 시) | 1회 |

**실행 순서**: L1 -> L2 -> L3a -> L3b (하위 계층 PASS 후 상위 진행)

### 7-2. 검증 루프 흐름

```
워커 EXECUTE 완료
  -> L1 lint 검증
    -> FAIL -> 워커에게 수정 지시 -> 재검증 (반복)
    -> PASS
  -> L2 build 검증
    -> FAIL -> 워커에게 수정 지시 (최대 2회)
    -> PASS
  -> L3a test 검증
    -> FAIL -> 워커에게 수정 지시 (최대 3회)
    -> PASS
  -> L3b E2E (해당 시)
    -> FAIL -> 1회 재시도 -> 2회 연속 FAIL -> 에스컬레이션
    -> PASS
  -> 태스크 완료 + 상태 갱신
```

### 7-3. 하네스 Guards 준수

오케스트레이터 공통 하네스(`opal-harness.md`)의 **자동 루핑 제약(Verification Loop Guards)** 을 준수한다.

- 재시도 한도 초과 시 사용자 에스컬레이션
- 회귀 감지 시 즉시 중단 + 에스컬레이션
- QA 설계/아키텍처 이슈는 즉시 에스컬레이션 (재시도 0회)

### 7-4. 회귀 방지 가드

자동 수정 후 기존 통과 코드가 깨지지 않도록 한다:

1. L3(test) 자동 수정 완료 후 전체 테스트 스위트 재실행
2. 이전 통과 테스트가 새로 실패하면 회귀로 판정
3. 회귀 감지 시 루프 즉시 중단 + 에스컬레이션

---

## 8. 전체 흐름 예시

### 시나리오

specs/001-user-auth/ 기능의 tasks.md에 4개 태스크:

```
T1: 데이터 모델 (Small -> opds, 의존: 없음)
T2: 인증 API (Standard -> opds, 의존: T1)
T3: 세션 관리 (Standard -> opds, 의존: T1)
T4: 통합 테스트 (Small -> opds, 의존: T2, T3)
```

### 실행 순서

```
Group 1 (순차): T1
  -> opds 디스패치 + SDD 컨텍스트 주입
  -> 완료 -> tasks.md T1 ✅, TS-01/TS-02 Green

Group 2 (병렬): T2, T3  <- T1 완료 후
  -> worktree 생성: .worktrees/001-T2/, .worktrees/001-T3/
  -> 병렬 디스패치 (opds x 2)
  -> 결과 수집 -> 순차 머지 -> 통합 테스트
  -> tasks.md T2/T3 ✅, TS-01/TS-02/TS-03/TS-04 Green

Group 3 (순차): T4  <- T2, T3 완료 후
  -> opds 디스패치 + SDD 컨텍스트 주입
  -> 완료 -> tasks.md T4 ✅, TS-05 Green
  -> 전체 TS Green 확인 -> EXECUTE-LOOP 완료
```

### 디스패치 예시 (T2)

```
[WORKER] opds 스킬을 수행하라.

**태스크 폴더**: specs/001-user-auth/tasks/T2-auth-api/

**SDD 컨텍스트**:
- **spec.md**: specs/001-user-auth/spec.md
- **SPEC-PLAN.md**: specs/001-user-auth/SPEC-PLAN.md
- **AC 매핑**: AC-01, AC-03
- **TS 매핑**: TS-01, TS-02, TS-04
- **TDD 지시**: 테스트 먼저 작성 후 구현

**태스크 설명**: POST /auth/login, /auth/logout 인증 API 구현

**완료 기준**: TS-01, TS-02, TS-04 Green

**하네스 Guards**: 구현 승인됨. 커밋 허용. `~/.opal/` 직접 수정 금지.
```

---

## 관련 문서

- `opal-pilot-sdd/SKILL.md` -- opsdd 오케스트레이터 메인 (Phase 6 개요)
- `verify-guide.md` -- 검증 상세 (DONE 검증)
- `spec-guide.md` -- spec.md 구조 (SDD 컨텍스트 참조)
- `spec-plan-guide.md` -- SPEC-PLAN.md 구조 (SDD 컨텍스트 참조)
- `~/.opal/skills/opal-pilot-project-dev/references/parallel-execution-guide.md` -- oppd 병렬 실행 패턴 원본
- `~/.opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` -- oppd 검증 루프 패턴 원본
