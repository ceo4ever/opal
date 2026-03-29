# PLAN: QA 에이전트 통합 — op-dev-qa-agent + op-task-qa-agent → opal-task-qa-agent

> 작성일: 2026-03-29
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `agents/op-dev-qa-agent/AGENT.md` | Dev QA 에이전트 (op-dev-qa 스킬 실행) | 삭제 |
| `agents/op-task-qa-agent/AGENT.md` | 범용 QA 에이전트 (op-task-qa 스킬 실행) | 삭제 |
| `agents/opal-task-qa-agent/AGENT.md` | (신규) 통합 QA 에이전트 | 신규 생성 |
| `skills/op-dev-qa/SKILL.md` | Dev QA 스킬 — 실행 주체: op-dev-qa-agent | 수정 (실행 주체 변경) |
| `skills/op-task-qa/SKILL.md` | 범용 QA 스킬 — 실행 주체: op-task-qa-agent | 수정 (실행 주체 변경) |
| `opal/core/references/opal-harness.md` | QA Gate 테이블에 에이전트 2개 매핑 | 수정 (단일 에이전트로 통합) |
| `opal/core/references/agents.md` | 에이전트 레지스트리 (op-dev-qa-agent, op-task-qa-agent 항목) | 수정 (통합) |
| `CLAUDE.md` | 에이전트 트리 + 설명 | 수정 |
| `README.md` | 에이전트 테이블 + 소스 구조 트리 | 수정 |
| `docs/ARCHITECTURE.md` | 에이전트 다이어그램 + 테이블 + 디렉토리 구조 | 수정 |
| `docs/CONVENTIONS.md` | 에이전트 네이밍 예시 | 수정 |
| `skills/opal-pilot-dev/SKILL.md` | QA Gate에서 op-dev-qa 참조 (에이전트명 직접 미참조) | 변경 불필요 |
| `skills/opal-pilot-dev-short/SKILL.md` | QA Gate에서 op-dev-qa 참조 (에이전트명 직접 미참조) | 변경 불필요 |
| `skills/opal-pilot-dev-wireframe/SKILL.md` | QA Gate에서 op-dev-qa 참조 (에이전트명 직접 미참조) | 변경 불필요 |
| `skills/opal-pilot-write/SKILL.md` | QA Gate에서 op-task-qa 참조 (에이전트명 직접 미참조) | 변경 불필요 |
| `skills/opal-project-pilot/SKILL.md` | QA Gate에서 op-task-qa 참조 (에이전트명 직접 미참조) | 변경 불필요 |
| `skills/opal-pilot-write-tech/SKILL.md` | 자체 QA 메커니즘 (consistency-rules.md 기반) | 변경 불필요 |

### 현재 상태

**두 QA 에이전트의 구조 비교**:

| 항목 | op-dev-qa-agent | op-task-qa-agent |
|------|----------------|-----------------|
| model | light | light |
| 실행 프로세스 | 오케스트레이터 프롬프트에서 검증 대상/단계명/TASK.md 확인 → SKILL.md Read → 페르소나 Read → 가이드 Read → 검증 → 리포트 | 동일 구조 |
| 스킬 탐색 경로 | `op-dev-qa/SKILL.md` | `op-task-qa/SKILL.md` |
| readonly | 기본 true, EXECUTE-UI 예외 false | 기본 true (예외 없음) |
| 결과 반환 형식 | 동일 (artifact_path, summary, status, verdict) | 동일 |
| 행동 규칙 | 동일 (스킬 프로세스 따르기, 객관적 기록, 코드 미수정) | 동일 |

**핵심 차이점**: 스킬 탐색 경로 1줄 + readonly 예외 1줄뿐. 나머지 구조는 완전히 동일.

**QA 디스패치 흐름**:
- 오케스트레이터는 QA **스킬명**(op-dev-qa, op-task-qa)을 참조하며, 에이전트명은 직접 사용하지 않음
- `opal-harness.md`의 QA Gate 테이블이 스킬→에이전트 매핑을 정의
- QA 스킬 SKILL.md의 "실행 주체" 항목에 에이전트명 기재

### 영향 범위

1. **에이전트 레이어**: 2개 삭제 + 1개 신규 → 에이전트 총 수 5→4개
2. **스킬 레이어**: op-dev-qa, op-task-qa의 "실행 주체" 참조만 변경 (스킬 로직 변경 없음)
3. **하네스**: QA Gate 테이블 에이전트 컬럼 통합
4. **오케스트레이터**: 변경 불필요 — 에이전트명이 아닌 스킬명으로 참조하기 때문
5. **문서 4개**: CLAUDE.md, README.md, ARCHITECTURE.md, CONVENTIONS.md — 에이전트 수/이름 업데이트
6. **install-mac.sh**: glob 기반 (`agents/*/AGENT.md`)이므로 소스 변경만으로 자동 반영

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| 1 | `agents/opal-task-qa-agent/AGENT.md` | 통합 QA 에이전트 — qa_skill 파라미터로 스킬 동적 탐색 |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 2 | `skills/op-dev-qa/SKILL.md` | 실행 주체: op-dev-qa-agent → opal-task-qa-agent |
| 3 | `skills/op-task-qa/SKILL.md` | 실행 주체: op-task-qa-agent → opal-task-qa-agent |
| 4 | `opal/core/references/opal-harness.md` | QA Gate 테이블: 에이전트 2개 → 단일 opal-task-qa-agent + qa_skill 컬럼 유지 |
| 5 | `opal/core/references/agents.md` | op-dev-qa-agent + op-task-qa-agent 항목 → opal-task-qa-agent 단일 항목으로 통합 |
| 6 | `CLAUDE.md` | 에이전트 트리/설명 업데이트 (5→4개, opal-task-qa-agent) |
| 7 | `README.md` | 에이전트 테이블 + 소스 구조 트리 업데이트 |
| 8 | `docs/ARCHITECTURE.md` | 에이전트 다이어그램/테이블/디렉토리 구조 업데이트 |
| 9 | `docs/CONVENTIONS.md` | 에이전트 네이밍 예시 업데이트 |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| 10 | `agents/op-dev-qa-agent/AGENT.md` | opal-task-qa-agent로 통합 |
| 11 | `agents/op-task-qa-agent/AGENT.md` | opal-task-qa-agent로 통합 |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | 통합 QA 에이전트 신규 생성 | `agents/opal-task-qa-agent/AGENT.md` | 중 |
| 2 | op-dev-qa 스킬 실행 주체 변경 | `skills/op-dev-qa/SKILL.md` | 하 |
| 3 | op-task-qa 스킬 실행 주체 변경 | `skills/op-task-qa/SKILL.md` | 하 |
| 4 | 하네스 QA Gate 통합 | `opal/core/references/opal-harness.md` | 하 |
| 5 | 에이전트 레지스트리 통합 | `opal/core/references/agents.md` | 하 |
| 6 | 기존 에이전트 삭제 | `agents/op-dev-qa-agent/`, `agents/op-task-qa-agent/` | 하 |
| 7 | CLAUDE.md 업데이트 | `CLAUDE.md` | 하 |
| 8 | README.md 업데이트 | `README.md` | 하 |
| 9 | ARCHITECTURE.md 업데이트 | `docs/ARCHITECTURE.md` | 하 |
| 10 | CONVENTIONS.md 업데이트 | `docs/CONVENTIONS.md` | 하 |

### 핵심 설계

#### 1. `agents/opal-task-qa-agent/AGENT.md` (신규)

두 에이전트의 공통 구조를 기반으로 통합. 핵심 변경점:

- **YAML frontmatter**: name: `opal-task-qa-agent`, model: `light`
- **입력 파라미터 추가**: 오케스트레이터 프롬프트에서 `qa_skill` (예: `op-dev-qa` 또는 `op-task-qa`)을 전달받음
- **스킬 탐색 동적화**: 하드코딩 경로 대신 `{프로젝트}/.opal/skills/{qa_skill}/SKILL.md` → `~/.opal/skills/{qa_skill}/SKILL.md`
- **페르소나/가이드 로딩**: 스킬 SKILL.md 내부의 지시에 따라 자동 결정 (에이전트가 가이드 선택 로직을 가지지 않음)
- **readonly 규칙**: 기본 true, EXECUTE-UI 단계에서만 false (op-dev-qa-agent의 기존 예외 유지)
- **결과 반환**: 기존과 동일한 JSON 형식 유지

```markdown
---
name: opal-task-qa-agent
description: |
  QA 스킬을 독립 컨텍스트에서 실행하는 범용 QA 워커.
  오케스트레이터가 qa_skill, 검증 대상 산출물 경로, 단계명을 전달하면,
  해당 QA 스킬의 SKILL.md를 Read하고 검증을 수행한다.
model: light
---
```

실행 프로세스:
1. 오케스트레이터 프롬프트에서 `qa_skill`, 검증 대상 경로, 단계명, TASK.md 경로를 확인
2. `{qa_skill}/SKILL.md`를 탐색·Read
3. 스킬 프로세스에 따라 페르소나/가이드 로딩
4. 검증 수행 + QA 리포트 생성
5. 결과 반환

#### 2. `skills/op-dev-qa/SKILL.md` 변경

14행의 실행 주체만 변경:
- 변경 전: `- **실행 주체**: QA 전용 워커 에이전트 (op-dev-qa-agent)`
- 변경 후: `- **실행 주체**: QA 전용 워커 에이전트 (opal-task-qa-agent)`

#### 3. `skills/op-task-qa/SKILL.md` 변경

15행의 실행 주체만 변경:
- 변경 전: `- **실행 주체**: QA 전용 워커 에이전트 (op-task-qa-agent)`
- 변경 후: `- **실행 주체**: QA 전용 워커 에이전트 (opal-task-qa-agent)`

#### 4. `opal/core/references/opal-harness.md` QA Gate 변경

57~61행 QA Gate 테이블을 변경. 에이전트 컬럼을 단일화하고, `qa_skill` 파라미터를 명시:

변경 전:
```markdown
| 오케스트레이터 도메인 | QA 스킬 | QA 에이전트 |
|---------------------|---------|------------|
| dev (opd/opds/opdw) | op-dev-qa | op-dev-qa-agent |
| 범용 (opp/opw) | op-task-qa | op-task-qa-agent |
```

변경 후:
```markdown
| 오케스트레이터 도메인 | QA 스킬 (qa_skill) | QA 에이전트 |
|---------------------|-------------------|------------|
| dev (opd/opds/opdw) | op-dev-qa | opal-task-qa-agent |
| 범용 (opp/opw) | op-task-qa | opal-task-qa-agent |
```

#### 5. `opal/core/references/agents.md` 변경

`op-task-qa-agent`와 `op-dev-qa-agent` 두 항목을 삭제하고 `opal-task-qa-agent` 단일 항목으로 통합:

```markdown
### opal-task-qa-agent

- **역할**: 범용 QA 워커 — 오케스트레이터가 전달한 qa_skill(op-dev-qa 또는 op-task-qa)의 SKILL.md를 Read하고 산출물 품질 검증
- **호출 시점**: 단계 완료 후 QA Gate에서 오케스트레이터가 디스패치
- **입력**: qa_skill, 검증 대상 산출물 경로, 단계명, TASK.md 경로
- **출력**: QA-{단계}.md 리뷰 문서
```

#### 6. 기존 에이전트 삭제

`git rm -r agents/op-dev-qa-agent/ agents/op-task-qa-agent/`

#### 7-10. 문서 업데이트 공통 변경사항

모든 문서에서 적용할 변경:
- 에이전트 수: 5개 → 4개
- `op-dev-qa-agent` + `op-task-qa-agent` → `opal-task-qa-agent`
- 에이전트 설명: "범용 QA 워커 — qa_skill로 QA 스킬을 동적 실행"
- 디렉토리 트리: `op-dev-qa-agent/`, `op-task-qa-agent/` → `opal-task-qa-agent/`

**CLAUDE.md 변경 부분**:
- 소스 구조 트리의 `agents/` 항목 (op-dev-qa-agent, op-task-qa-agent → opal-task-qa-agent)
- 배포 구조 트리의 `agents/` 항목
- 컴포넌트 유형 테이블의 에이전트 행 (5개 → 4개 아님, 현재 4개 × 1 포맷 유지)
- 에이전트 의존 관계 설명

**README.md 변경 부분**:
- 에이전트 테이블 (5개 → 4개, 3행 → 2행으로 QA 통합)
- 소스 구조 트리의 `agents/` (5개 → 4개)

**ARCHITECTURE.md 변경 부분**:
- 서브에이전트 다이어그램 (op-task-qa-agent, op-dev-qa-agent → opal-task-qa-agent)
- 에이전트 테이블 (5행 → 4행)
- 디렉토리 구조 트리

**CONVENTIONS.md 변경 부분**:
- 에이전트 폴더 네이밍 예시: `opal-task-agent` 유지, `opal-task-qa-agent` 추가 또는 기존 예시 교체

## 3. 실행 체크리스트

> 총 10개 Step

### Step 1: 통합 QA 에이전트 생성
- [x] 완료
- **파일**: `agents/opal-task-qa-agent/AGENT.md`
- **작업 내용**: op-dev-qa-agent + op-task-qa-agent 공통 구조 기반으로 통합 AGENT.md 작성. qa_skill 입력 파라미터 추가, 스킬 탐색 경로 동적화, readonly 규칙 통합.
- **완료 기준**: AGENT.md가 존재하고, YAML frontmatter에 name/description/model이 정의되며, 실행 프로세스에서 qa_skill 기반 동적 탐색이 명시됨
- **테스트**: 파일 존재 확인 + frontmatter 유효성 + qa_skill 파라미터 언급 확인
- **의존**: 없음

### Step 2: op-dev-qa 스킬 실행 주체 변경
- [x] 완료
- **파일**: `skills/op-dev-qa/SKILL.md`
- **작업 내용**: 14행 실행 주체를 `op-dev-qa-agent` → `opal-task-qa-agent`로 변경
- **완료 기준**: "실행 주체" 행이 `opal-task-qa-agent`를 참조
- **테스트**: Grep으로 `opal-task-qa-agent` 확인, `op-dev-qa-agent` 잔존 없음 확인
- **의존**: Step 1

### Step 3: op-task-qa 스킬 실행 주체 변경
- [x] 완료
- **파일**: `skills/op-task-qa/SKILL.md`
- **작업 내용**: 15행 실행 주체를 `op-task-qa-agent` → `opal-task-qa-agent`로 변경
- **완료 기준**: "실행 주체" 행이 `opal-task-qa-agent`를 참조
- **테스트**: Grep으로 `opal-task-qa-agent` 확인, 기존 `op-task-qa-agent` 잔존 없음 확인
- **의존**: Step 1

### Step 4: 하네스 QA Gate 통합
- [x] 완료
- **파일**: `opal/core/references/opal-harness.md`
- **작업 내용**: 57~61행 QA Gate 테이블의 에이전트 컬럼을 단일 `opal-task-qa-agent`로 변경. QA 스킬 컬럼 헤더에 `(qa_skill)` 추가.
- **완료 기준**: QA Gate 테이블에 `opal-task-qa-agent`만 존재, `op-dev-qa-agent`와 `op-task-qa-agent` 미존재
- **테스트**: Grep으로 `op-dev-qa-agent`/`op-task-qa-agent` 잔존 없음 확인
- **의존**: Step 1

### Step 5: 에이전트 레지스트리 통합
- [x] 완료
- **파일**: `opal/core/references/agents.md`
- **작업 내용**: `op-task-qa-agent`와 `op-dev-qa-agent` 두 항목을 삭제하고 `opal-task-qa-agent` 단일 항목 추가. 역할에 qa_skill 동적 실행 명시.
- **완료 기준**: `opal-task-qa-agent` 항목 존재, 기존 두 에이전트 항목 미존재
- **테스트**: agents.md에서 3개 에이전트명 Grep 확인
- **의존**: Step 1

### Step 6: 기존 에이전트 삭제
- [x] 완료
- **파일**: `agents/op-dev-qa-agent/`, `agents/op-task-qa-agent/`
- **작업 내용**: `git rm -r agents/op-dev-qa-agent/ agents/op-task-qa-agent/`
- **완료 기준**: 두 디렉토리가 working tree에서 삭제되고 git staging에 반영됨
- **테스트**: `ls agents/` 에서 두 디렉토리 미존재 확인
- **의존**: Step 2, 3 (스킬이 먼저 새 에이전트를 참조해야 함)

### Step 7: CLAUDE.md 업데이트
- [x] 완료
- **파일**: `CLAUDE.md`
- **작업 내용**: 소스 구조 트리에서 `op-task-qa-agent` + `op-dev-qa-agent` → `opal-task-qa-agent`, 배포 구조 에이전트 수(5→4개 아님, 현재 "4개 x 1 포맷" 유지 확인), 컴포넌트 의존 관계의 QA 에이전트 설명 업데이트
- **완료 기준**: `op-dev-qa-agent`, `op-task-qa-agent` 잔존 없음 + `opal-task-qa-agent` 존재
- **테스트**: Grep으로 레거시 에이전트명 잔존 확인
- **의존**: Step 1

### Step 8: README.md 업데이트
- [x] 완료
- **파일**: `README.md`
- **작업 내용**: 에이전트 테이블 3행(opal-task-agent, op-task-qa-agent, op-dev-qa-agent, op-dev-test-agent, wtm-agent)에서 QA 2행을 opal-task-qa-agent 1행으로 통합 (5→4개). 소스 구조 트리의 agents/ 하위 항목 업데이트.
- **완료 기준**: 에이전트 테이블이 4행, 소스 트리에 `opal-task-qa-agent/` 존재
- **테스트**: Grep으로 레거시 에이전트명 잔존 확인
- **의존**: Step 1

### Step 9: ARCHITECTURE.md 업데이트
- [x] 완료
- **파일**: `docs/ARCHITECTURE.md`
- **작업 내용**: 서브에이전트 다이어그램에서 `op-task-qa-agent` + `op-dev-qa-agent` → `opal-task-qa-agent`. 에이전트 테이블 5행→4행 (QA 통합). 디렉토리 구조 트리 업데이트. 에이전트 수 "5개" → "4개".
- **완료 기준**: 다이어그램/테이블/트리에서 레거시 에이전트명 미존재 + `opal-task-qa-agent` 존재
- **테스트**: Grep으로 레거시 에이전트명 잔존 확인
- **의존**: Step 1

### Step 10: CONVENTIONS.md 업데이트
- [x] 완료
- **파일**: `docs/CONVENTIONS.md`
- **작업 내용**: 에이전트 폴더 네이밍 예시에서 `opal-task-agent, wtm-agent` 외에 `opal-task-qa-agent` 반영. 현재 예시가 `opal-task-agent, wtm-agent`이므로 `opal-task-qa-agent` 추가.
- **완료 기준**: 에이전트 네이밍 예시에 `opal-task-qa-agent` 포함
- **테스트**: 해당 섹션 Read 확인
- **의존**: 없음

## 4. QA 체크리스트

### 기능 테스트

- [x] R1: `agents/opal-task-qa-agent/AGENT.md` 존재 + YAML frontmatter 유효 + qa_skill 파라미터 정의
- [x] R2: `agents/op-dev-qa-agent/`, `agents/op-task-qa-agent/` 디렉토리 미존재
- [x] R3: `skills/op-dev-qa/SKILL.md`와 `skills/op-task-qa/SKILL.md`의 실행 주체가 `opal-task-qa-agent`
- [x] R4: `opal-harness.md` QA Gate 테이블에 `opal-task-qa-agent`만 존재
- [x] R5: `agents.md` 레지스트리에 `opal-task-qa-agent` 단일 항목 존재

### 일관성 테스트

- [x] 전체 소스에서 `op-dev-qa-agent` 잔존 없음 (Grep 검증) — tasks/ 변경이력만 잔존
- [x] 전체 소스에서 `op-task-qa-agent` 잔존 없음 (Grep 검증, 단 변경이력 제외) — tasks/ 변경이력만 잔존
- [x] 오케스트레이터 5개의 QA Gate 참조가 정상 동작 (스킬명만 참조하므로 변경 불필요 확인)
- [x] CLAUDE.md, README.md, ARCHITECTURE.md, CONVENTIONS.md에서 에이전트 수/이름 일관성
- [x] 에이전트 총 수가 4개로 일관 (opal-task-agent, opal-task-qa-agent, op-dev-test-agent, wtm-agent)

### 문서 품질

- [x] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가
- [x] kebab-case 파일/폴더 네이밍을 따르는가
- [x] YAML frontmatter가 올바른가 (name, description, model)

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| 레거시 에이전트명 잔존 | QA 에이전트 탐색 실패 | 전체 소스 Grep으로 `op-dev-qa-agent`, `op-task-qa-agent` 잔존 검증 |
| opal-pilot-write-tech의 QA 메커니즘 영향 | opwt의 Phase 4 정합성 검증 파손 | opwt은 자체 QA (consistency-rules.md)를 사용하며 QA Gate 에이전트를 참조하지 않음 — 영향 없음 |
| 기존 배포된 ~/.opal/agents/ 잔존 | 이전 에이전트가 남아 혼란 | install-mac.sh가 glob 기반이므로 재설치 시 자동 정리됨. 삭제된 파일은 install-mac.sh의 클린 배포 전략에 의해 제거 |
| opal-task-qa-agent 네이밍 혼동 (opal-task-agent와 유사) | 사용자/에이전트가 혼동 | description에서 "QA 워커"를 명확히 구분. 네이밍 패턴은 CONVENTIONS.md 예시에 반영 |
