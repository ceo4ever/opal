# QA: PLAN — QA 에이전트 통합

> 검토일: 2026-03-29 | 판정: **Needs Revision**

## 1. 요약

PLAN.md는 전반적인 구조와 의도는 명확하나, **3가지 중대한 오류와 1가지 미명확 사항**이 있다.

- **오류 1**: 레지스트리 agents.md에 이미 op-task-qa-agent와 op-dev-qa-agent가 존재하고 정의되어 있음에도 불구하고, PLAN에서 "opal-task-qa-agent 단일 항목 추가"를 "삭제 후 추가"로만 표현
- **오류 2**: opal-task-qa-agent 생성 시 `qa_skill` 입력 파라미터를 "동적 탐색"한다고 명시했지만, 실제 opal-task-qa-agent의 AGENT.md에는 해당 파라미터 처리 로직이 구현되어야 하는데 그 구체적 방식(YAML 정의 부분)이 누락되어 있음
- **오류 3**: CLAUDE.md 변경 부분의 설명에 모순이 있음. "컴포넌트 유형 테이블의 에이전트 행 (5개 → 4개 아님, 현재 4개 × 1 포맷 유지)"이라는 표현이 불명확

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| GP-1 | 즉시 실행 가능성 | **Fail** | opal-task-qa-agent AGENT.md 생성 시 qa_skill 파라미터 처리 로직이 구체적으로 정의되지 않았음 |
| GP-2 | 의존성 순서 | **Pass** | Step 순서 및 의존성 명시가 올바름 (Step 1 → Step 2,3 → Step 4,5 → Step 6) |
| GP-3 | TASK 반영 | **Pass** | R1~R5 모든 요구사항이 체크리스트에 반영됨 |
| GP-4 | 파일 목록 완전성 | **Pass** | 변경 필요 파일 11개(신규 1 + 수정 9 + 삭제 2) 모두 명시됨 |
| GP-5 | 설계 구체성 | **Fail** | opal-task-qa-agent의 YAML frontmatter와 qa_skill 동적 탐색 메커니즘 미상세 |
| GP-6 | 체크리스트 커버리지 | **Partial** | Step 1~10이 모두 정의되었으나, Step 1(통합 QA 에이전트 생성)의 상세 내용이 불완전 |

## 3. 지적 사항

### 지적 3-1: AGENT.md 설계 미정의 (Critical)

**위치**: PLAN 섹션 2.2.4, 구현 계획의 "1. `agents/opal-task-qa-agent/AGENT.md` (신규)" 부분

**문제점**:

PLAN에서 다음과 같이 설명하고 있다:

```markdown
- **입력 파라미터 추가**: 오케스트레이터 프롬프트에서 `qa_skill` (예: `op-dev-qa` 또는 `op-task-qa`)을 전달받음
- **스킬 탐색 동적화**: 하드코딩 경로 대신 `{프로젝트}/.opal/skills/{qa_skill}/SKILL.md` → `~/.opal/skills/{qa_skill}/SKILL.md`
```

그러나 실제 AGENT.md의 frontmatter 예시(118-127줄)에는 `qa_skill` 입력이 YAML 파라미터로 정의되어 있지 않으며, 실행 프로세스에서 오케스트레이터로부터 `qa_skill`을 수신하는 구체적 메커니즘이 명확하지 않다.

**예상 수정 방안**:

AGENT.md의 "입력" 또는 "실행 프로세스" 섹션에 다음과 같이 명시해야 함:

```markdown
## 입력 파라미터

오케스트레이터 프롬프트에서 다음을 전달받는다:

| 파라미터 | 설명 |
|---------|------|
| `qa_skill` | 실행할 QA 스킬명 (op-dev-qa 또는 op-task-qa) |
| `artifact_path` | 검증 대상 산출물 경로 |
| `stage` | 검증 단계명 |
| `task_path` | 태스크 폴더 경로 |
```

### 지적 3-2: agents.md 레지스트리 변경 과정 모호 (High)

**위치**: PLAN 섹션 2.2.5 및 Step 5

**문제점**:

agents.md에서 "op-task-qa-agent와 op-dev-qa-agent 두 항목을 삭제하고 opal-task-qa-agent 단일 항목으로 통합"이라고만 되어 있으나, agents.md의 현재 상태를 점검해보니:

- `### op-task-qa-agent` — 범용 QA 에이전트 (line ~20)
- `### op-dev-qa-agent` — Dev QA 에이전트 (line ~25)

두 항목이 명확히 구분되어 있고, 통합할 때 각 항목의 내용을 어떻게 병합할지 구체적으로 정의되지 않았다.

**예상 수정 방안**:

agents.md 변경의 상세 내용을 추가하면:

```markdown
### Step 5 상세 작업

op-task-qa-agent 섹션의 "역할":
  기존: "범용 QA 에이전트 — op-task-qa 스킬로..."

  변경: "범용 QA 워커 — 오케스트레이터가 qa_skill(op-dev-qa 또는 op-task-qa)을 지정하면 해당 QA 스킬의 SKILL.md를 Read하고 산출물 품질 검증"

그리고 op-dev-qa-agent 섹션(호출 시점 ~ 끝) 전체 삭제.
```

### 지적 3-3: CLAUDE.md 변경 설명 불명확 (Medium)

**위치**: PLAN 섹션 2.2.7, "CLAUDE.md 변경 부분"

**문제점**:

> 컴포넌트 유형 테이블의 에이전트 행 (5개 → 4개 아님, 현재 4개 × 1 포맷 유지 확인)

이 표현이 모호하다. 무엇이 "4개 × 1 포맷"인지, 왜 "5개 → 4개 아님"인지 명확하지 않다.

**확인 결과**:

CLAUDE.md의 "컴포넌트 유형" 테이블은:

```markdown
| 유형 | 설명 | 현재 상태 |
|------|------|----------|
| **Agents** | 독립 컨텍스트에서 자율 실행하는 에이전트 (AGENT.md) | `agents/` 4개 × 1 포맷 |
```

현재 CLAUDE.md에 이미 "4개 × 1 포맷"이라고 명시되어 있으므로, 이 부분은 변경이 불필요하다. 대신 에이전트 목록 부분만 업데이트하면 된다.

**예상 수정 방안**:

Step 7의 CLAUDE.md 변경 내용을 더 명확히:

```markdown
**CLAUDE.md 변경 부분**:
- 소스 구조 트리의 `agents/` 항목 (op-dev-qa-agent, op-task-qa-agent → opal-task-qa-agent)
- 배포 구조 트리의 `agents/` 항목 (동일)
- 컴포넌트 의존 관계의 에이전트 설명에서 기존 QA 에이전트 2개 → opal-task-qa-agent으로 통합
- **변경 불필요**: "컴포넌트 유형 테이블" (이미 "4개 × 1 포맷" 명시)
```

### 지적 3-4: QA 체크리스트 Step 1 검증 기준 미상세 (Medium)

**위치**: PLAN 섹션 3, Step 1 "완료 기준"

**문제점**:

> 완료 기준: AGENT.md가 존재하고, YAML frontmatter에 name/description/model이 정의되며, 실행 프로세스에서 qa_skill 기반 동적 탐색이 명시됨

"qa_skill 기반 동적 탐색이 명시됨"이라는 표현이 모호하다. 구체적으로:

- AGENT.md의 어느 섹션에 명시되어야 하는가? (입력 파라미터 섹션? 실행 프로세스 섹션?)
- 어떤 표현이 "명시"된 것으로 인정될 것인가? (예: "opal-task-qa-agent는 `qa_skill` 파라미터를 입력받아 동적으로 QA 스킬을 탐색한다")

**예상 수정 방안**:

```markdown
완료 기준:
1. AGENT.md가 존재하고, YAML frontmatter에 name/description/model이 정의됨
2. "입력 파라미터" 또는 "실행 프로세스" 섹션에 qa_skill 파라미터 명시
3. 스킬 탐색 경로가 `{프로젝트}/.opal/skills/{qa_skill}/SKILL.md` → `~/.opal/skills/{qa_skill}/SKILL.md`로 정의됨
4. readonly 규칙이 명시됨 (기본 true, EXECUTE-UI 예외 false)
```

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md R1 (opal-task-qa-agent 신규) | PLAN에서 상세한 설계 정의 필요 | **Fail** — qa_skill 입력 처리 로직 미정의 |
| TASK.md R3 (스킬 실행 주체 변경) | PLAN Step 2,3에서 구체적 변경 내용 명시 | **Pass** — 14행/15행 변경 명확함 |
| TASK.md R4 (하네스 QA Gate 통합) | PLAN Step 4에서 변경 전후 예시 명시 | **Pass** — 테이블 변경 예시 명확함 |
| TASK.md R5.1 (agents.md 통합) | PLAN Step 5에서 상세 변경 내용 | **Partial** — 개요만 있고 세부 병합 로직 미정의 |
| 기존 op-dev-qa-agent AGENT.md | 파라미터/프로세스 호환성 확인 | **Pass** — 기존 구조는 공통이므로 호환 가능 |

## 5. 판정

**Needs Revision**

### 판정 근거

1. **Critical Issue (GP-1, GP-5 실패)**: opal-task-qa-agent AGENT.md 생성 시 가장 중요한 기능인 `qa_skill` 입력 파라미터 처리 메커니즘이 구체적으로 정의되지 않았다. "동적 탐색"이라는 개념만 기술되어 있으며, 실제 AGENT.md 파일에서 이를 구현하기 위한 구체적 지시사항이 부족하다.

2. **High Issue (agents.md 레지스트리 변경)**: 기존 두 QA 에이전트 항목을 통합하는 과정이 명확하지 않다. 어떤 내용을 보존하고 어떤 내용을 삭제할지, 그리고 최종 opal-task-qa-agent 항목에 어떤 내용을 병합할지 명시되어야 한다.

3. **Clarity Issues**: CLAUDE.md 변경 설명과 QA 체크리스트의 검증 기준이 모호하여, 실행자가 해석의 여지가 생길 수 있다.

### 수정 요청사항

1. **Step 1 (통합 QA 에이전트 생성)**:
   - AGENT.md의 YAML frontmatter 및 "입력 파라미터" 섹션에 `qa_skill` 파라미터 명시
   - 실행 프로세스에서 qa_skill 기반 동적 스킬 탐색 로직을 구체적으로 서술
   - readonly 규칙(기본 true, EXECUTE-UI 예외 false) 명시

2. **Step 5 (agents.md 레지스트리 통합)**:
   - 현재 op-task-qa-agent와 op-dev-qa-agent 항목의 정의 확인
   - 통합된 opal-task-qa-agent 항목의 최종 형태를 상세히 기술
   - 어떤 부분을 op-task-qa-agent에서 가져오고, 어떤 부분을 op-dev-qa-agent에서 가져올지 명시

3. **Step 7 (CLAUDE.md 변경)**:
   - "컴포넌트 유형 테이블의 에이전트 행 (5개 → 4개 아님, 현재 4개 × 1 포맷 유지 확인)" 문구를 명확히
   - 변경할 부분과 변경 불필요 부분을 구분하여 명시

4. **QA 체크리스트**:
   - Step 1의 완료 기준을 더 구체적으로 정의
   - 테스트 항목에서 "qa_skill 파라미터 언급 확인"을 "qa_skill 파라미터 및 탐색 경로 확인"으로 수정

### 재검증 전제

위 4가지 사항을 반영한 PLAN.md 수정본에 대해 재검증 시, Pass 판정이 가능할 것으로 예상된다.

---

**작성자**: 알투 (QA 에이전트) | **검토 모드**: QA 검증 (PLAN.md)
