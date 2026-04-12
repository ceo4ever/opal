# PLAN: opsdd EXECUTE-LOOP 개선 — op-sdd-action-plan + opal-sdd-action-agent 신설

> 작성일: 2026-04-07
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `opal/skills/opal-pilot-sdd/SKILL.md` | opsdd 오케스트레이터 (Phase 4 현황) | **수정** |
| `opal/skills/opal-pilot-sdd/references/execute-loop-guide.md` | EXECUTE-LOOP 상세 가이드 | **수정** |
| `agents/opal-task-action-agent/AGENT.md` | oppd 전용 액션 에이전트 (VERIFY 루프 참조) | 참조만 |
| `opal/skills/op-dev-plan/SKILL.md` | 범용 PLAN 스킬 (대체 대상) | 참조만 |
| `opal/skills/op-dev-execute/SKILL.md` | 재사용할 EXECUTE 스킬 | 참조만 |
| `opal/skills/op-sdd-plan/SKILL.md` | SDD 아키텍처 설계 (Phase 3) | 참조만 |
| `docs/CONVENTIONS.md` | 네이밍/구조 컨벤션 | 참조만 |

### 현재 상태

**Phase 4 EXECUTE-LOOP 현재 구조**:
- opsdd SKILL.md Phase 4는 `op-dev-plan` + `op-dev-execute`를 순차 디스패치
- `execute-loop-guide.md`가 §5에 디스패치 프롬프트 템플릿 정의 (5-1: op-dev-plan, 5-2: op-dev-execute, 5-3: 재시도)
- PM이 직접 루프를 관리하며 Gate를 중개

**문제점 (TASK.md 배경 확인)**:
1. `op-dev-plan`은 `plan-guide.md` + `personas` + `community-skills`를 전부 로딩하고 처음부터 설계 재수행 (SDD에서는 SPEC-PLAN.md에 아키텍처가 이미 확정)
2. `op-dev-execute`는 SPEC.md/TEST-SCENARIOS.md/AC·TS 매핑 미인식
3. 자가 검증 루프(VERIFY) 없음 — 테스트 실패 시 PM 수동 재지시 필요
4. ACT 폴더 생성 타이밍 불명확 (§5-1에 폴더 경로만 있고 "생성하라" 지시 없음)
5. §2-1 실행 순서에 사용자 Gate 누락 (Gate 섹션에만 존재)

**참조 에이전트 (`opal-task-action-agent`)**:
- `agents/opal-task-action-agent/AGENT.md`에 위치 (프로젝트 루트 `agents/` 폴더)
- 6단계 파이프라인: PLAN → QA → TEST-SCENARIO → EXECUTE → VERIFY(L1~L3b) → TEST
- VERIFY 루프: L1(lint) → L2(build) → L3a(unit/integration) → L3b(E2E), 계층별 재시도 한도
- 회귀 방지 가드, L3b E2E 특수 규칙 포함
- oppd 전용이라 SDD 입력 구조(SPEC.md, SPEC-PLAN.md, TEST-SCENARIOS.md, AC/TS 매핑)를 직접 재사용 불가

**에이전트/스킬 디렉토리 구조**:
- 에이전트: `agents/{agent-name}/AGENT.md` (프로젝트 루트)
- 스킬: `opal/skills/{skill-name}/SKILL.md`
- 컨벤션: 에이전트 폴더명 `{대상 워크플로우}-{역할}`, 스킬 접두사 `op-sdd-*`

### 영향 범위

- opsdd Phase 4 디스패치 구조 전면 변경 (op-dev-plan + op-dev-execute 이중 → opal-sdd-action-agent 단일)
- 신규 에이전트가 내부에서 op-sdd-action-plan + op-dev-execute를 디스패치
- 기존 execute-loop-guide.md의 §2-1, §5, §10 구조 변경 (§4 병렬 실행, §6 재시도 루프는 유지)
- op-dev-plan은 SDD 컨텍스트에서 사용 중단 (범용 opd/opds에서는 계속 사용)

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| 1 | `opal/skills/op-sdd-action-plan/SKILL.md` | SDD ACT 전용 경량 PLAN 스킬 |
| 2 | `opal/agents/opal-sdd-action-agent/AGENT.md` | SDD ACT 자율 실행 에이전트 |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 3 | `opal/skills/opal-pilot-sdd/references/execute-loop-guide.md` | §2-1 사용자 Gate 추가 + 단일 디스패치 교체, §5 프롬프트 갱신, §10 흐름 예시 갱신 |
| 4 | `opal/skills/opal-pilot-sdd/SKILL.md` | Phase 4 ACT 실행 순서에 사용자 Gate + 디스패치 대상 변경 |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| — | 없음 | — |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | op-sdd-action-plan 스킬 신설 | `opal/skills/op-sdd-action-plan/SKILL.md` | 중 |
| 2 | opal-sdd-action-agent 에이전트 신설 | `opal/agents/opal-sdd-action-agent/AGENT.md` | 상 |
| 3 | execute-loop-guide.md 갱신 | `opal/skills/opal-pilot-sdd/references/execute-loop-guide.md` | 중 |
| 4 | opsdd SKILL.md Phase 4 갱신 | `opal/skills/opal-pilot-sdd/SKILL.md` | 하 |

### 핵심 설계

#### [A] op-sdd-action-plan 스킬 (`opal/skills/op-sdd-action-plan/SKILL.md`)

SDD ACT 전용 경량 PLAN 스킬. op-dev-plan과의 핵심 차이:

| 항목 | op-dev-plan | op-sdd-action-plan |
|------|------------|-------------------|
| 목적 | 범용 구현 계획 | SDD ACT 범위 경량 계획 |
| 입력 | TASK.md (+ ANALYSIS.md) | SPEC.md + SPEC-PLAN.md + TEST-SCENARIOS.md + ACT 정의 |
| 사전 로딩 | plan-guide.md + personas + community-skills | 없음 (SDD 컨텍스트로 대체) |
| 코드 분석 | Full ANALYSIS 수준 | ACT 범위 기준 경량 (Glob/Grep/Read) |
| 설계 재수행 | 전체 설계 | 없음 (SPEC-PLAN.md 아키텍처 준수) |
| 복잡도 판별 | 단순/복잡 모드 | 없음 (항상 direct 실행) |
| execution-plan.json | FE/BE 시 생성 | 생성하지 않음 |
| 산출물 | `tasks/{NNN}/PLAN.md` | `actions/ACT-{NNN}-{name}/PLAN.md` |

**YAML frontmatter**: name, description, version
**프로세스**:
1. SDD 컨텍스트 로딩 (SPEC.md, SPEC-PLAN.md, TEST-SCENARIOS.md에서 해당 ACT 관련 정보 추출)
2. ACT 범위 코드 분석 (SPEC-PLAN.md의 ACT scope 기준 Glob/Grep/Read)
3. 구현 범위 확정 (신규/수정 파일 목록)
4. 핵심 설계 (SPEC-PLAN.md 아키텍처 결정 준수, ACT 단위 구현 상세)
5. 실행 체크리스트 작성 (Step 형식, 완료 기준에 AC/TS 매핑 반영)
6. QA 체크리스트 작성
7. PLAN.md 작성

**PLAN.md 출력 형식**: op-dev-plan 형식을 간소화 — 복잡도 판별/실행 아키텍처/기술 컨텍스트 섹션 제거. "SDD 컨텍스트" 섹션 추가 (ACT ID, AC/TS 매핑 기록).

#### [B] opal-sdd-action-agent (`opal/agents/opal-sdd-action-agent/AGENT.md`)

SDD ACT 자율 실행 에이전트. opal-task-action-agent를 참조하되 SDD 입력 구조에 맞게 재설계.

**입력 명세**:

| 파라미터 | 필수 | 설명 |
|---------|------|------|
| act_id | O | ACT ID (예: `ACT-001-db-schema`) |
| act_goal | O | ACT 목표 |
| act_scope | O | ACT 범위 — 변경 대상 파일/모듈 |
| ac_mapping | O | AC 목록 (예: AC-01, AC-03) |
| ts_mapping | O | TS 목록 (예: TS-01, TS-02) |
| verify_commands | O | 검증 명령 (lint, build, test 등) |
| task_folder | O | 태스크 폴더 경로 |
| sdd_context | O | SPEC.md, SPEC-PLAN.md, TEST-SCENARIOS.md 경로 |

**4단계 파이프라인** (opal-task-action-agent 6단계에서 QA/TEST-SCENARIO 제거 — SDD에서는 TEST-SCENARIOS.md가 이미 존재하고 QA는 PM Gate에서 수행):

```
1. ACT 폴더 생성
   → actions/ACT-{NNN}-{name}/ 디렉토리 생성

2. PLAN
   → opal-task-agent 디스패치 (op-sdd-action-plan, model: advanced)
   → PLAN.md 생성

3. EXECUTE
   → opal-task-agent 디스패치 (op-dev-execute, model: standard)
   → SDD 컨텍스트(SPEC.md, SPEC-PLAN.md, TEST-SCENARIOS.md, AC/TS 매핑)를 디스패치 시 주입
   → 코드 변경 + changed_files 반환

4. VERIFY 루프 (L1~L3b)
   → opal-task-action-agent §5 VERIFY 구조 참조
   → L1(lint) → L2(build) → L3a(unit/integration) → L3b(E2E)
   → 실패 시 opal-task-agent에 수정 지시 (한도 내)
   → 한도 초과/회귀 시 status: failed로 반환

5. TEST.md 작성
   → ACT 폴더에 TEST.md 생성 (TS 실행 결과 기록)

6. 결과 반환
   → status: completed/failed + verification_log + changed_files
```

**VERIFY 루프 규격** — `opal-task-action-agent` §5 참조로 중복 정의 최소화:
- 계층별 재시도 한도 동일 (L1: 무제한, L2: 2회, L3a: 3회, L3b: 1회)
- 실행 순서 동일 (L1 → L2 → L3a → L3b, 현재 계층 PASS 전 다음 불가)
- 회귀 방지 가드 동일
- L3b E2E 특수 규칙 동일

**결과 반환 형식**: opal-task-action-agent 형식 기반, `act_id` + `sdd_context` 추가.

**행동 규칙**:
1. 사용자와 직접 상호작용하지 않음 — 결과만 opsdd에 반환
2. STATE.md를 갱신하지 않음 — opsdd 오케스트레이터 책임
3. 하네스 Guards의 재시도 한도 준수
4. 회귀 발생 시 즉시 중단, status: failed 반환
5. 커밋하지 않음 — opsdd가 관리

#### [C] execute-loop-guide.md 갱신

**§1 개요**:
- "op-dev-plan + op-dev-execute를 직접 디스패치" → "opal-sdd-action-agent에 단일 디스패치" 변경
- 핵심 원칙 업데이트

**§2-1 단일 ACT 실행 순서**:
현재:
```
1. op-dev-plan 디스패치 → 2. PM Gate → 3. op-dev-execute 디스패치 → 4. TEST.md 확인 → 5. Pass/Fail
```
변경 후:
```
1. 사용자 Gate (ACT 시작 전 승인, interactive 모드)
2. opal-sdd-action-agent 디스패치 (ACT 폴더 생성 + PLAN + EXECUTE + VERIFY 자율 완주)
3. 결과 수신: status 확인
4. Pass → DONE.md 작성 → STATE.md 갱신
   Fail → 재시도 루프 (§6) 또는 에스컬레이션
```

**§5 디스패치 프롬프트 템플릿**:
- §5-1: op-dev-plan 프롬프트 → opal-sdd-action-agent 디스패치 프롬프트로 교체
- §5-2: op-dev-execute 프롬프트 → 삭제 (에이전트 내부에서 처리)
- §5-3: 재디스패치 프롬프트 → opal-sdd-action-agent 재디스패치 프롬프트로 교체

**§10 전체 흐름 예시**:
- 기존 예시의 op-dev-plan/op-dev-execute 이중 디스패치를 opal-sdd-action-agent 단일 디스패치로 변경
- 사용자 Gate 단계 반영

**유지 항목**: §4 병렬 실행 패턴, §6 재시도 루프 구조 (PM 레벨의 재디스패치)

#### [D] opsdd SKILL.md Phase 4 갱신

**Phase 4 ACT 실행 순서** 변경:
현재:
```
1. op-dev-plan 디스패치 → 2. PM Gate → 3. op-dev-execute 디스패치 → 4. TEST.md 확인 → 5. STATE.md 갱신
```
변경 후:
```
1. 사용자 Gate (ACT 시작 전 승인, interactive 모드)
2. opal-sdd-action-agent 디스패치 (자율 완주)
3. 결과 수신 → Pass/Fail 판정
4. DONE.md 작성 → STATE.md 갱신
```

**파이프라인 요약 다이어그램** 갱신:
```
Phase 4: EXECUTE   ACT 루프   사용자 Gate → opal-sdd-action-agent 디스패치
                              → 결과 수신 → DONE.md
```

**디스패치 관련 설명** 변경:
- "EXECUTE-LOOP에서 op-dev-plan + op-dev-execute를 직접 디스패치" → "opal-sdd-action-agent에 단일 디스패치"

## 3. 실행 체크리스트

> 총 4개 Step

### Step 1: op-sdd-action-plan 스킬 생성

- [x] 완료
- **파일**: `opal/skills/op-sdd-action-plan/SKILL.md`
- **작업 내용**:
  - `opal/skills/op-sdd-action-plan/` 디렉토리 생성
  - SKILL.md 작성: YAML frontmatter + 입력/출력 명세 + op-dev-plan과의 차이 테이블 + 프로세스 7단계 + PLAN.md 출력 형식 + 품질 체크리스트
  - 네이밍 컨벤션: `op-sdd-*` 접두사, kebab-case
  - personas/references 폴더 없음 (로딩 없음이 설계 의도)
- **완료 기준**: SKILL.md가 존재하며, 입력(SPEC.md + SPEC-PLAN.md + TEST-SCENARIOS.md + ACT 정의) → 산출물(PLAN.md) 흐름이 명확히 정의됨
- **테스트**: SKILL.md Read하여 필수 섹션(frontmatter, 입력/출력, 프로세스, 출력 형식) 존재 확인
- **의존**: 없음

### Step 2: opal-sdd-action-agent 에이전트 생성

- [x] 완료
- **파일**: `opal/agents/opal-sdd-action-agent/AGENT.md`
- **작업 내용**:
  - `opal/agents/opal-sdd-action-agent/` 디렉토리 생성
  - AGENT.md 작성: YAML frontmatter + 입력 명세 + 실행 프로세스(ACT 폴더 생성 → PLAN → EXECUTE → VERIFY → TEST.md → 반환) + VERIFY 루프(opal-task-action-agent §5 참조) + 결과 반환 형식 + 행동 규칙
  - VERIFY 루프는 `opal-task-action-agent §5` 참조 방식으로 중복 최소화 (계층/한도/회귀 가드 요약 + 참조 링크)
  - op-dev-execute 디스패치 시 SDD 컨텍스트 주입 프롬프트 템플릿 포함
- **완료 기준**: AGENT.md가 존재하며, 입력 명세 8개 파라미터 + 실행 프로세스 6단계 + VERIFY 참조 + 결과 반환 형식이 정의됨
- **테스트**: AGENT.md Read하여 필수 섹션(frontmatter, 입력 명세, 실행 프로세스, VERIFY, 결과 반환) 존재 확인
- **의존**: Step 1 (op-sdd-action-plan 참조)

### Step 3: execute-loop-guide.md 갱신

- [x] 완료
- **파일**: `opal/skills/opal-pilot-sdd/references/execute-loop-guide.md`
- **작업 내용**:
  - §1 개요: 핵심 원칙에서 "op-dev-plan + op-dev-execute 직접 디스패치" → "opal-sdd-action-agent 단일 디스패치" 변경
  - §2-1 단일 ACT 실행 순서: 사용자 Gate 1번 단계 추가 + opal-sdd-action-agent 디스패치로 교체 (5단계 → 4단계)
  - §5 디스패치 프롬프트 템플릿: §5-1을 opal-sdd-action-agent 프롬프트로 교체, §5-2 삭제, §5-3을 재디스패치로 교체
  - §10 전체 흐름 예시: 사용자 Gate + 단일 디스패치 반영
  - §4 병렬 실행 패턴, §6 재시도 루프 구조 유지 (내부 디스패치 대상만 변경)
- **완료 기준**: §2-1에 사용자 Gate 포함, §5 프롬프트가 opal-sdd-action-agent 기반, §10 예시가 신규 흐름 반영, §4/§6 구조 유지
- **테스트**: execute-loop-guide.md Read하여 "opal-sdd-action-agent" 키워드 존재 + §2-1에 "사용자 Gate" 존재 + §4/§6 구조 유지 확인
- **의존**: Step 2 (에이전트 입력 명세 확정 필요)

### Step 4: opsdd SKILL.md Phase 4 갱신

- [x] 완료
- **파일**: `opal/skills/opal-pilot-sdd/SKILL.md`
- **작업 내용**:
  - Phase 4 "ACT 실행 순서" 변경: 사용자 Gate → opal-sdd-action-agent 디스패치 → 결과 수신 → DONE.md/STATE.md
  - 5단계 파이프라인 요약 다이어그램 Phase 4 행 갱신
  - 상단 설명문 "op-dev-plan + op-dev-execute를 직접 디스패치" → "opal-sdd-action-agent에 단일 디스패치" 변경
  - Gate 섹션: interactive에 "각 ACT 시작 전 사용자 Gate" 유지 확인
  - 변경이력에 v2.2 추가
- **완료 기준**: Phase 4 ACT 실행 순서에 사용자 Gate + opal-sdd-action-agent 명시, 파이프라인 요약과 Phase 4 섹션이 일관
- **테스트**: SKILL.md Read하여 Phase 4에 "opal-sdd-action-agent" + "사용자 Gate" 존재 확인
- **의존**: Step 3 (execute-loop-guide.md와 일관성 필요)

## 4. QA 체크리스트

### 기능 테스트

- [ ] op-sdd-action-plan SKILL.md가 SDD 컨텍스트(SPEC.md, SPEC-PLAN.md, TEST-SCENARIOS.md, ACT 정의)를 입력으로 명시하는가
- [ ] op-sdd-action-plan이 plan-guide.md/personas/community-skills 로딩을 하지 않는가
- [ ] opal-sdd-action-agent AGENT.md의 입력 명세가 8개 파라미터(act_id, act_goal, act_scope, ac_mapping, ts_mapping, verify_commands, task_folder, sdd_context)를 포함하는가
- [ ] opal-sdd-action-agent 파이프라인이 ACT 폴더 생성 → PLAN → EXECUTE → VERIFY → TEST.md → 반환 순서인가
- [ ] VERIFY 루프가 opal-task-action-agent §5를 참조하며 중복 정의가 최소화되었는가
- [ ] execute-loop-guide.md §2-1에 사용자 Gate 단계가 추가되었는가
- [ ] execute-loop-guide.md §5 디스패치 프롬프트가 opal-sdd-action-agent 기반인가
- [ ] opsdd SKILL.md Phase 4가 opal-sdd-action-agent 디스패치 + 사용자 Gate를 명시하는가

### 일관성 테스트

- [ ] opsdd SKILL.md Phase 4와 execute-loop-guide.md §2-1의 ACT 실행 순서가 일치하는가
- [ ] opal-sdd-action-agent 입력 명세와 execute-loop-guide.md §5 디스패치 프롬프트의 파라미터가 일치하는가
- [ ] execute-loop-guide.md §4 병렬 실행 패턴이 유지되는가
- [ ] execute-loop-guide.md §6 재시도 루프 구조가 유지되는가
- [ ] VERIFY 루프 재시도 한도가 하네스 §1 자동 루핑 제약과 일치하는가

### 문서 품질

- [ ] 모든 파일이 한국어 본문 + 영어 코드/필드명 규칙을 따르는가
- [ ] 파일/폴더 네이밍이 kebab-case인가 (op-sdd-action-plan, opal-sdd-action-agent)
- [ ] YAML frontmatter가 컨벤션(name, description, version/model)을 따르는가
- [ ] 변경이력이 포함되어 있는가
- [ ] 에이전트가 `opal/agents/` 디렉토리에 생성되는가 (기존 `agents/`와 구분 — TASK.md 명세 기준)

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| 에이전트 디렉토리 위치 불일치 | 기존 에이전트는 `agents/`(루트)에 있으나 TASK.md는 `opal/agents/`에 생성 지시 | TASK.md 명세(`opal/agents/`)를 따른다. 기존 `agents/`는 배포본이므로 소스는 `opal/agents/`가 올바름 |
| op-dev-execute에 SDD 컨텍스트 미인식 | op-dev-execute는 PLAN.md 체크리스트만 따르므로 SDD 컨텍스트를 직접 해석하지 못할 수 있음 | opal-sdd-action-agent의 디스패치 프롬프트에서 SDD 컨텍스트를 명시적으로 주입하여 워커가 인지하도록 함 |
| VERIFY 루프 참조 경로 차이 | opal-task-action-agent는 `agents/`에 있고 opal-sdd-action-agent는 `opal/agents/`에 생성 — 참조 경로 혼선 가능 | 참조 시 배포 경로(`~/.opal/`) 기준이 아닌 프로젝트 소스 경로(`agents/`)로 안내 |
| 병렬 실행에서 opal-sdd-action-agent 호환성 | §4 병렬 실행 시 worktree에서 에이전트 디스패치 방식 변경 필요 | §4에서 에이전트 디스패치 대상만 변경하고 worktree 격리/머지 구조는 유지 |
