# PLAN: op-task-qa → op-dev-qa 리네이밍 + 범용 op-task-qa 신규

> 작성일: 2026-03-29
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `skills/op-task-qa/SKILL.md` | 현재 QA 스킬 (코드 dev 특화) | 디렉토리 리네이밍 → `op-dev-qa` |
| `skills/op-task-qa/references/qa-dev-guide.md` | ANALYSIS/PLAN 검증 가이드 | 경로만 이동 (내용 유지) |
| `skills/op-task-qa/references/qa-wireframe-guide.md` | WIREFRAME/EXECUTE-UI 검증 가이드 | 경로만 이동 (내용 유지) |
| `skills/op-task-qa/personas/qa-engineer.md` | QA 페르소나 | 경로만 이동 (내용 유지) |
| `agents/op-task-qa-agent/AGENT.md` | 현재 QA 에이전트 | 디렉토리 리네이밍 → `op-dev-qa-agent` |
| `opal/core/references/opal-harness.md` | QA Gate 정의 (단일 op-task-qa 탐색) | 분기 로직으로 변경 |
| `opal/core/references/opal-skills-registry.json` | 스킬 레지스트리 JSON | op-dev-qa 추가, op-task-qa 범용화 |
| `opal/core/references/agents.md` | 에이전트 레지스트리 | op-dev-qa-agent 추가, op-task-qa-agent 범용화 |
| `opal/core/references/skills.md` | 스킬 레지스트리 문서 | 참조 변경 없음 (JSON이 SSOT) |
| `scripts/install-mac.sh` | 배포 스크립트 | 변경 불필요 (디렉토리 기반 자동 반영) |
| `skills/opal-pilot-dev/SKILL.md` | Full Task 오케스트레이터 | 하네스 위임으로 직접 참조 없음 → 변경 불필요 |
| `skills/opal-pilot-dev-short/SKILL.md` | Short Task 오케스트레이터 | 하네스 위임으로 직접 참조 없음 → 변경 불필요 |
| `skills/opal-pilot-dev-wireframe/SKILL.md` | Wireframe 오케스트레이터 | op-task-qa 직접 참조 2곳 → op-dev-qa로 변경 |
| `skills/opal-pilot-write/SKILL.md` | 범용 문서 오케스트레이터 | op-task-qa 직접 참조 1곳 → op-task-qa(범용) 유지 확인 |
| `skills/opal-pilot-write-tech/SKILL.md` | 서비스 기획 산출물 오케스트레이터 | QA는 자체 consistency-rules.md → 변경 불필요 |
| `skills/opal-project-pilot/SKILL.md` | 범용 프로젝트 오케스트레이터 | QA Gate만 참조 → 하네스에 분기가 생기면 자동 적용 |
| `CLAUDE.md` | 프로젝트 루트 문서 | op-task-qa 참조 5곳 + 구조 트리 업데이트 |
| `README.md` | 프로젝트 README | op-task-qa 참조 6곳 + 구조 트리 업데이트 |
| `docs/ARCHITECTURE.md` | 아키텍처 문서 | op-task-qa 참조 5곳 + 구조 트리 업데이트 |
| `docs/CONVENTIONS.md` | 컨벤션 문서 | op-task-qa 참조 2곳 → 예시 업데이트 |

### 현재 상태

**op-task-qa 스킬**: `skills/op-task-qa/SKILL.md`는 `stage` 입력으로 `ANALYSIS`, `PLAN`, `WIREFRAME`, `EXECUTE-UI`를 받아 각각 `qa-dev-guide.md`, `qa-wireframe-guide.md`를 참조한다. 모두 코드 개발 도메인 전용 검증 기준이다.

**op-task-qa-agent**: `agents/op-task-qa-agent/AGENT.md`는 op-task-qa 스킬을 탐색하여 실행하는 단순 워커. model: haiku.

**하네스 QA Gate**: `opal-harness.md` 55~56행에서 단일 `op-task-qa` 탐색 경로만 정의. 모든 오케스트레이터가 이 경로를 사용.

**오케스트레이터별 QA 참조 방식**:
- `opal-pilot-dev`, `opal-pilot-dev-short`: 하네스의 QA Gate에 위임 (직접 op-task-qa 언급 없음)
- `opal-pilot-dev-wireframe`: op-task-qa를 직접 2회 언급 (WIREFRAME 완료 시, EXECUTE-UI 완료 시)
- `opal-pilot-write`: op-task-qa를 직접 1회 언급 ("복잡한 문서는 op-task-qa 호출")
- `opal-pilot-write-tech`: 자체 QA 시스템 (consistency-rules.md) → op-task-qa 미참조
- `opal-project-pilot`: "QA Gate"만 참조, 구체적 스킬명 없음 (하네스 위임)

**레지스트리**: `opal-skills-registry.json`에서 op-task-qa는 `op-task` 그룹에 속하며, dispatched_by에 dev/write-tech/project 오케스트레이터 5개가 등록.

**install-mac.sh**: `skills/` 및 `agents/` 하위 디렉토리를 glob으로 순회 배포하므로, 소스 디렉토리 리네이밍만으로 배포가 자동 반영된다.

### 영향 범위

1. **직접 영향**: op-task-qa 스킬/에이전트 디렉토리 리네이밍, 하네스 QA Gate 분기
2. **참조 영향**: 오케스트레이터 3개(wireframe, write, project-pilot), 레지스트리 2개(JSON, agents.md)
3. **문서 영향**: CLAUDE.md, README.md, ARCHITECTURE.md, CONVENTIONS.md 내 참조/트리 업데이트
4. **배포 영향**: install-mac.sh는 자동 반영이므로 변경 불필요
5. **비영향**: 커뮤니티 스킬, 레거시 태스크, op-dev-test-agent, opal-task-agent

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| N1 | `skills/op-dev-qa/SKILL.md` | dev 특화 QA 스킬 (기존 op-task-qa 리네이밍) |
| N2 | `skills/op-dev-qa/references/qa-dev-guide.md` | dev QA 가이드 (기존 복사) |
| N3 | `skills/op-dev-qa/references/qa-wireframe-guide.md` | wireframe QA 가이드 (기존 복사) |
| N4 | `skills/op-dev-qa/personas/qa-engineer.md` | QA 페르소나 (기존 복사) |
| N5 | `agents/op-dev-qa-agent/AGENT.md` | dev QA 에이전트 (기존 op-task-qa-agent 리네이밍) |
| N6 | `skills/op-task-qa/SKILL.md` | 범용 QA 스킬 (신규) |
| N7 | `skills/op-task-qa/references/qa-general-guide.md` | 범용 QA 가이드 (신규) |
| N8 | `skills/op-task-qa/personas/qa-engineer.md` | QA 페르소나 (범용화) |
| N9 | `agents/op-task-qa-agent/AGENT.md` | 범용 QA 에이전트 (신규) |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| M1 | `opal/core/references/opal-harness.md` | QA Gate 분기 (방안 B: 오케스트레이터가 QA 스킬명 직접 지정) |
| M2 | `opal/core/references/opal-skills-registry.json` | op-dev-qa 추가, op-task-qa 범용화, dispatched_by 업데이트 |
| M3 | `opal/core/references/agents.md` | op-dev-qa-agent 추가, op-task-qa-agent 범용화 |
| M4 | `skills/opal-pilot-dev-wireframe/SKILL.md` | op-task-qa → op-dev-qa (2곳) |
| M5 | `skills/opal-pilot-dev/SKILL.md` | QA Gate에 op-dev-qa 명시 추가 (현재는 하네스 위임) |
| M6 | `skills/opal-pilot-dev-short/SKILL.md` | QA Gate에 op-dev-qa 명시 추가 (현재는 하네스 위임) |
| M7 | `skills/opal-pilot-write/SKILL.md` | op-task-qa → op-task-qa(범용) 유지 확인, 스킬명 명시 보강 |
| M8 | `skills/opal-project-pilot/SKILL.md` | QA Gate에 op-task-qa(범용) 명시 추가 |
| M9 | `CLAUDE.md` | 구조 트리 + 컴포넌트 설명 업데이트 |
| M10 | `README.md` | 컴포넌트 테이블 + 구조 트리 업데이트 |
| M11 | `docs/ARCHITECTURE.md` | 아키텍처 다이어그램 + 스킬/에이전트 테이블 + 구조 트리 업데이트 |
| M12 | `docs/CONVENTIONS.md` | 네이밍 예시 업데이트 |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| D1 | `skills/op-task-qa/` (기존 디렉토리 전체) | op-dev-qa로 이동, 새로운 범용 op-task-qa로 대체 |
| D2 | `agents/op-task-qa-agent/` (기존 디렉토리 전체) | op-dev-qa-agent로 이동, 새로운 범용 op-task-qa-agent로 대체 |

> **구현 전략**: 기존 디렉토리를 git mv로 리네이밍한 뒤 내용을 수정하고, 새로운 범용 버전을 별도 신규 생성한다.

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | op-task-qa → op-dev-qa 디렉토리 리네이밍 + 내부 참조 수정 | N1~N4 (D1) | 낮음 |
| 2 | op-task-qa-agent → op-dev-qa-agent 디렉토리 리네이밍 + 내부 참조 수정 | N5 (D2) | 낮음 |
| 3 | 범용 op-task-qa SKILL.md + qa-general-guide.md 신규 작성 | N6, N7, N8 | 중간 |
| 4 | 범용 op-task-qa-agent AGENT.md 신규 작성 | N9 | 낮음 |
| 5 | 하네스 QA Gate 변경 | M1 | 낮음 |
| 6 | dev 오케스트레이터에 QA 스킬명 명시 | M4, M5, M6 | 낮음 |
| 7 | 범용 오케스트레이터에 QA 스킬명 명시/확인 | M7, M8 | 낮음 |
| 8 | 레지스트리 업데이트 | M2, M3 | 낮음 |
| 9 | 문서 업데이트 | M9, M10, M11, M12 | 낮음 |

### 핵심 설계

#### N1. skills/op-dev-qa/SKILL.md (리네이밍)

기존 `skills/op-task-qa/SKILL.md`를 `git mv`로 이동 후 다음만 변경:
- frontmatter `name`: `op-task-qa` → `op-dev-qa`
- 제목: `# op-task-qa — QA 검증` → `# op-dev-qa — Dev QA 검증`
- 실행 주체: `op-task-qa-agent` → `op-dev-qa-agent`
- 페르소나 경로: `~/.opal/skills/op-task-qa/` → `~/.opal/skills/op-dev-qa/`
- references 경로: `~/.opal/skills/op-task-qa/references/` → `~/.opal/skills/op-dev-qa/references/`
- 나머지 내용(프로세스, 검증 기준, 단계 가이드 매핑 등)은 그대로 유지

#### N5. agents/op-dev-qa-agent/AGENT.md (리네이밍)

기존 `agents/op-task-qa-agent/AGENT.md`를 `git mv`로 이동 후 다음만 변경:
- frontmatter `name`: `op-task-qa-agent` → `op-dev-qa-agent`
- frontmatter `description`: `op-task-qa 스킬` → `op-dev-qa 스킬`
- 제목: `# op-task-qa-agent` → `# op-dev-qa-agent`
- 스킬 탐색 경로: `op-task-qa/SKILL.md` → `op-dev-qa/SKILL.md`
- 행동 규칙: `op-task-qa SKILL.md` → `op-dev-qa SKILL.md`
- model: `haiku` → `light` (044 모델 매핑 반영)

#### N6. skills/op-task-qa/SKILL.md (범용 신규)

기존 op-task-qa 구조를 기반으로 범용화한 버전:

```yaml
---
name: op-task-qa
description: |
  **범용 QA 검증 스킬**. 도메인 무관 산출물(TASK.md, PLAN.md 등)의 품질을 검증한다.
  코드 개발 QA는 op-dev-qa, 범용 QA는 이 스킬을 사용한다.
---
```

핵심 차이점 (기존 op-task-qa 대비):
- **stage 입력**: `TASK`, `PLAN`, `EXECUTE` (코드 관련 ANALYSIS/WIREFRAME/EXECUTE-UI 제거)
- **가이드**: `qa-general-guide.md` 단일 참조 (qa-dev-guide, qa-wireframe-guide 없음)
- **검증 기준**: 완전성, 정합성, 명확성, 실행 가능성 (코드 실독, 빌드/린트 등 제거)
- **활용 스킬**: getsentry/code-review, openai/security 제거 (코드 관련 불필요)
- **산출물 형식**: 기존 QA-{단계}.md 형식 유지

#### N7. skills/op-task-qa/references/qa-general-guide.md (범용 가이드 신규)

범용 산출물 검증 가이드. 구조는 qa-dev-guide.md를 참고하되 코드 관련 항목 제거:

**TASK 검증 기준**:
| ID | 항목 | 확인 내용 |
|----|------|----------|
| T-1 | 목표 명확성 | 작업 목표가 구체적이고 측정 가능한가 |
| T-2 | 요구사항 완전성 | 모든 요구사항이 빠짐없이 정의되었는가 |
| T-3 | 제약 조건 명시 | 제약 조건과 전제 조건이 명시되었는가 |
| T-4 | 산출물 정의 | 기대 산출물이 명확히 정의되었는가 |

**PLAN 검증 기준**:
| ID | 항목 | 확인 내용 |
|----|------|----------|
| GP-1 | 즉시 실행 가능성 | PLAN만 보고 바로 실행에 들어갈 수 있는가 |
| GP-2 | 의존성 순서 | 의존성을 고려한 올바른 순서인가 |
| GP-3 | TASK 반영 | TASK.md 요구사항이 모두 반영되었는가 |
| GP-4 | 파일 목록 완전성 | 변경 필요 파일이 모두 포함되었는가 |
| GP-5 | 설계 구체성 | 핵심 변경 사항이 충분히 명세되었는가 |
| GP-6 | 체크리스트 커버리지 | 모든 요구사항이 실행 Step으로 분해되었는가 |

**EXECUTE 검증 기준**:
| ID | 항목 | 확인 내용 |
|----|------|----------|
| GE-1 | 체크리스트 완료 | 모든 Step이 완료되었는가 |
| GE-2 | 산출물 존재 | 기대 산출물이 실제로 생성되었는가 |
| GE-3 | TASK 충족 | TASK.md 요구사항이 모두 충족되었는가 |

#### N8. skills/op-task-qa/personas/qa-engineer.md (범용화)

기존 personas/qa-engineer.md를 복사하되, 코드 관련 원칙을 범용화:
- "엣지 케이스" → "누락 시나리오"
- "테스트" → "검증"
- "도구 기반 자동화를 우선한다" → "문서 간 교차 검증을 우선한다"
- "test-tools.yaml" 참조 제거

#### N9. agents/op-task-qa-agent/AGENT.md (범용 신규)

기존 에이전트 구조를 기반으로 범용화:
- frontmatter `name`: `op-task-qa-agent`
- frontmatter `description`: 범용 QA 스킬(op-task-qa)을 실행하는 QA 전용 워커
- model: `light` (044 모델 매핑)
- 스킬 탐색 경로: `op-task-qa/SKILL.md`
- readonly: true (빌드/린트 불필요)

#### M1. opal-harness.md QA Gate 변경

**방안 B 적용**: 하네스는 공통 원칙만 정의하고, 각 오케스트레이터가 자체 QA 스킬명을 지정.

변경 전 (55~56행):
```
단계 완료 후 op-task-qa 에이전트를 호출하여 산출물을 검증한다.
- op-task-qa 탐색: `{프로젝트}/.opal/skills/op-task-qa/SKILL.md` -> `~/.opal/skills/op-task-qa/SKILL.md`
```

변경 후:
```
단계 완료 후 QA 에이전트를 호출하여 산출물을 검증한다.

| 오케스트레이터 도메인 | QA 스킬 | QA 에이전트 |
|---------------------|---------|------------|
| dev (opd/opds/opdw) | op-dev-qa | op-dev-qa-agent |
| 범용 (opp/opw) | op-task-qa | op-task-qa-agent |

각 오케스트레이터 SKILL.md에서 QA 스킬명을 명시한다.
```

#### M2. opal-skills-registry.json 변경

`op-task` 그룹에서:
- 기존 `op-task-qa` 항목: description → "범용 QA 검증 (도메인 무관 산출물)", dispatched_by → `["opal-pilot-write", "opal-project-pilot"]`
- 신규 추가 `op-dev-qa` 항목을 `op-dev` 그룹에 추가: description → "Dev QA 검증 (코드 개발 산출물)", stage → "QA", dispatched_by → `["opal-pilot-dev", "opal-pilot-dev-short", "opal-pilot-dev-wireframe"]`

#### M3. agents.md 변경

- `op-task-qa-agent` 섹션: 역할 설명을 "범용 QA 에이전트 — op-task-qa 스킬로 도메인 무관 산출물 품질 검증"으로, 호출 시점을 "TASK, PLAN 완료 후 (범용 오케스트레이터)"로 변경
- `op-dev-qa-agent` 섹션 신규 추가: "Dev QA 에이전트 — op-dev-qa 스킬로 코드 개발 산출물 검증", 호출 시점 "ANALYSIS, PLAN, WIREFRAME, EXECUTE-UI 완료 후 (dev 오케스트레이터)"

#### M4. opal-pilot-dev-wireframe/SKILL.md 변경

- 44행: `op-task-qa 호출 (단계: WIREFRAME)` → `op-dev-qa 호출 (단계: WIREFRAME)`
- 55행: `op-task-qa 호출 (단계: EXECUTE-UI)` → `op-dev-qa 호출 (단계: EXECUTE-UI)`

#### M5~M6. opal-pilot-dev/SKILL.md, opal-pilot-dev-short/SKILL.md

현재 "QA Gate"로 하네스에 위임 중. 방안 B에 따라 QA Gate 호출부에 스킬명 명시 추가:
- `**QA Gate** (op-dev-qa)` 형태로 보강

#### M7. opal-pilot-write/SKILL.md

- 50행: `op-task-qa 호출` → 이미 범용이므로 그대로 유지. 다만 "op-task-qa(범용)"으로 명시 보강 검토.

#### M8. opal-project-pilot/SKILL.md

- 37행: `**QA Gate**` → `**QA Gate** (op-task-qa)` 형태로 스킬명 명시

#### M9~M12. 문서 업데이트

**CLAUDE.md**:
- 소스 구조 트리에 `op-dev-qa/` 추가, `op-task-qa/` 설명을 "범용 단계: QA 검증 (도메인 무관)"으로 변경
- 에이전트 트리에 `op-dev-qa-agent/` 추가
- 배포 구조는 자동이므로 변경 불필요
- 컴포넌트 간 의존 관계: `op-task / op-task-qa` → `op-task / op-task-qa(범용)` 분리, `op-dev-qa(dev)` 추가

**README.md**:
- 단계 스킬 테이블: op-task-qa → "범용 | 범용 QA 검증 (도메인 무관)", op-dev-qa 행 추가 → "dev | Dev QA 검증"
- 에이전트 테이블: op-task-qa-agent → "범용 QA 에이전트", op-dev-qa-agent 행 추가
- 소스 구조 트리 업데이트

**ARCHITECTURE.md**:
- 시스템 구성 다이어그램: `op-task-qa-agent: QA 검증` → `op-task-qa-agent: 범용 QA`, `op-dev-qa-agent: Dev QA` 추가
- 스킬 테이블: op-task-qa → "범용 QA 검증", op-dev-qa 행 추가
- 에이전트 테이블: op-task-qa-agent → model: light, 역할 범용화, op-dev-qa-agent 행 추가 (model: light)
- 디렉토리 구조 트리 업데이트

**CONVENTIONS.md**:
- 네이밍 예시: `op-task-qa` 유지 (범용 단계 스킬 예시로 여전히 유효)
- `op-dev-*` 예시에 `op-dev-qa` 추가: `op-dev-analysis, op-dev-plan, op-dev-qa`

---

## 3. 실행 체크리스트

> 총 9개 Step

### Step 1: op-task-qa → op-dev-qa 디렉토리 리네이밍 + 내부 참조 수정
- [x] 완료
- **파일**: `skills/op-dev-qa/` (N1~N4, D1)
- **작업 내용**:
  1. `git mv skills/op-task-qa skills/op-dev-qa`
  2. SKILL.md: frontmatter name → `op-dev-qa`, 제목 → `# op-dev-qa — Dev QA 검증`, 실행 주체 → `op-dev-qa-agent`, 내부 경로 `op-task-qa` → `op-dev-qa` (5곳)
  3. references/, personas/ 파일 내용은 변경 없음
- **완료 기준**: `skills/op-dev-qa/SKILL.md`가 존재하고, 내부에 `op-task-qa` 문자열이 없음
- **테스트**: `grep -r "op-task-qa" skills/op-dev-qa/` 결과 0건
- **의존**: 없음

### Step 2: op-task-qa-agent → op-dev-qa-agent 디렉토리 리네이밍 + 내부 참조 수정
- [x] 완료
- **파일**: `agents/op-dev-qa-agent/AGENT.md` (N5, D2)
- **작업 내용**:
  1. `git mv agents/op-task-qa-agent agents/op-dev-qa-agent`
  2. AGENT.md: frontmatter name → `op-dev-qa-agent`, description → `op-dev-qa 스킬`, model → `light`, 제목 → `# op-dev-qa-agent`, 스킬 탐색 경로 `op-task-qa` → `op-dev-qa` (모든 곳)
- **완료 기준**: `agents/op-dev-qa-agent/AGENT.md`가 존재하고, 내부에 `op-task-qa` 문자열이 없음
- **테스트**: `grep -r "op-task-qa" agents/op-dev-qa-agent/` 결과 0건
- **의존**: 없음

### Step 3: 범용 op-task-qa SKILL.md + qa-general-guide.md + 페르소나 신규 작성
- [x] 완료
- **파일**: `skills/op-task-qa/SKILL.md` (N6), `skills/op-task-qa/references/qa-general-guide.md` (N7), `skills/op-task-qa/personas/qa-engineer.md` (N8)
- **작업 내용**:
  1. `skills/op-task-qa/` 디렉토리 + `references/`, `personas/` 하위 디렉토리 생성
  2. SKILL.md: 핵심 설계 N6 섹션에 따라 작성 (stage: TASK/PLAN/EXECUTE, 범용 검증 기준)
  3. qa-general-guide.md: 핵심 설계 N7 섹션에 따라 작성 (T-1~T-4, GP-1~GP-6, GE-1~GE-3)
  4. qa-engineer.md: 핵심 설계 N8 섹션에 따라 범용화 작성
- **완료 기준**: 3개 파일이 존재하고, SKILL.md에 ANALYSIS/WIREFRAME/EXECUTE-UI 참조가 없음
- **테스트**: `grep -c "ANALYSIS\|WIREFRAME\|EXECUTE-UI" skills/op-task-qa/SKILL.md` 결과 0
- **의존**: Step 1 (기존 op-task-qa 디렉토리가 op-dev-qa로 이동된 후)

### Step 4: 범용 op-task-qa-agent AGENT.md 신규 작성
- [x] 완료
- **파일**: `agents/op-task-qa-agent/AGENT.md` (N9)
- **작업 내용**:
  1. `agents/op-task-qa-agent/` 디렉토리 생성
  2. AGENT.md: 핵심 설계 N9 섹션에 따라 작성 (model: light, op-task-qa 탐색, readonly: true)
- **완료 기준**: 파일이 존재하고, op-dev-qa 참조가 없으며 op-task-qa를 정확히 참조
- **테스트**: `grep "op-dev-qa" agents/op-task-qa-agent/AGENT.md` 결과 0건
- **의존**: Step 2 (기존 op-task-qa-agent 디렉토리가 op-dev-qa-agent로 이동된 후)

### Step 5: 하네스 QA Gate 변경
- [x] 완료
- **파일**: `opal/core/references/opal-harness.md` (M1)
- **작업 내용**: 핵심 설계 M1에 따라 55~56행 영역을 분기 테이블로 교체
- **완료 기준**: QA Gate에 dev/범용 분기 테이블이 존재하고, 단일 op-task-qa 탐색 경로가 제거됨
- **테스트**: 하네스에 `op-dev-qa`와 `op-task-qa` 두 스킬이 모두 언급됨
- **의존**: Step 1, Step 3

### Step 6: dev 오케스트레이터에 QA 스킬명 명시
- [x] 완료
- **파일**: `skills/opal-pilot-dev-wireframe/SKILL.md` (M4), `skills/opal-pilot-dev/SKILL.md` (M5), `skills/opal-pilot-dev-short/SKILL.md` (M6)
- **작업 내용**:
  - wireframe: op-task-qa → op-dev-qa (44행, 55행)
  - dev-full: QA Gate 언급부에 `(op-dev-qa)` 스킬명 추가
  - dev-short: QA Gate 언급부에 `(op-dev-qa)` 스킬명 추가
- **완료 기준**: dev 오케스트레이터 3개 모두 op-dev-qa를 참조
- **테스트**: `grep "op-dev-qa" skills/opal-pilot-dev*/SKILL.md` 결과 3개 파일 매칭
- **의존**: Step 5

### Step 7: 범용 오케스트레이터에 QA 스킬명 명시/확인
- [x] 완료
- **파일**: `skills/opal-pilot-write/SKILL.md` (M7), `skills/opal-project-pilot/SKILL.md` (M8)
- **작업 내용**:
  - write: 50행의 op-task-qa 참조 유지 (이미 범용), 필요시 "(범용)" 표기 보강
  - project-pilot: QA Gate 언급부에 `(op-task-qa)` 스킬명 추가
- **완료 기준**: 범용 오케스트레이터 2개 모두 op-task-qa를 참조
- **테스트**: `grep "op-task-qa" skills/opal-pilot-write/SKILL.md skills/opal-project-pilot/SKILL.md` 결과 매칭
- **의존**: Step 5

### Step 8: 레지스트리 업데이트
- [x] 완료
- **파일**: `opal/core/references/opal-skills-registry.json` (M2), `opal/core/references/agents.md` (M3)
- **작업 내용**:
  - JSON: op-dev 그룹에 op-dev-qa 항목 추가, op-task 그룹의 op-task-qa dispatched_by를 범용 오케스트레이터만으로 변경
  - agents.md: op-dev-qa-agent 섹션 추가, op-task-qa-agent 설명 범용화
- **완료 기준**: JSON이 valid하고, op-dev-qa + op-task-qa(범용) 모두 등록됨
- **테스트**: `python3 -c "import json; json.load(open('opal/core/references/opal-skills-registry.json'))"` 성공
- **의존**: Step 1, Step 3

### Step 9: 문서 업데이트
- [x] 완료
- **파일**: `CLAUDE.md` (M9), `README.md` (M10), `docs/ARCHITECTURE.md` (M11), `docs/CONVENTIONS.md` (M12)
- **작업 내용**:
  - CLAUDE.md: 소스 구조 트리에 op-dev-qa 추가, op-task-qa 설명 범용화, 에이전트 트리에 op-dev-qa-agent 추가, 컴포넌트 의존 관계 업데이트
  - README.md: 단계 스킬 테이블, 에이전트 테이블, 소스 구조 트리 업데이트
  - ARCHITECTURE.md: 다이어그램, 스킬 테이블, 에이전트 테이블, 디렉토리 트리 업데이트
  - CONVENTIONS.md: op-dev-* 예시에 op-dev-qa 추가
- **완료 기준**: 4개 문서 모두에서 op-dev-qa가 언급되고, 기존 op-task-qa가 "범용"으로 설명됨
- **테스트**: `grep "op-dev-qa" CLAUDE.md README.md docs/ARCHITECTURE.md docs/CONVENTIONS.md` 결과 4개 파일 매칭
- **의존**: Step 1~8 모두 완료 후

---

## 4. QA 체크리스트

### 기능 테스트
- [x] R1: `skills/op-dev-qa/` 디렉토리가 존재하고 SKILL.md/references/personas 구조가 완전한가
- [x] R2: `agents/op-dev-qa-agent/AGENT.md`가 존재하고 op-dev-qa 스킬을 탐색하는가
- [x] R3: `skills/op-task-qa/` 디렉토리가 범용 버전으로 재생성되었는가
- [x] R4: `agents/op-task-qa-agent/AGENT.md`가 범용 버전으로 재생성되었는가
- [x] R5: 하네스 QA Gate가 dev/범용 분기를 포함하는가
- [x] R5.2~R5.7: 각 오케스트레이터가 올바른 QA 스킬을 참조하는가 (dev→op-dev-qa, 범용→op-task-qa)
- [x] R6: opal-skills-registry.json이 valid JSON이고 op-dev-qa, op-task-qa(범용) 모두 포함하는가
- [x] R7: agents.md에 op-dev-qa-agent, op-task-qa-agent(범용) 모두 포함하는가

### 일관성 테스트
- [x] dev 오케스트레이터(opd/opds/opdw)가 모두 op-dev-qa를 참조하는가
- [x] 범용 오케스트레이터(opp/opw)가 모두 op-task-qa를 참조하는가
- [x] opal-pilot-write-tech는 자체 QA(consistency-rules.md)를 유지하고 변경되지 않았는가
- [x] op-dev-qa의 stage 입력(ANALYSIS/PLAN/WIREFRAME/EXECUTE-UI)이 기존과 동일한가
- [x] op-task-qa(범용)의 stage 입력(TASK/PLAN/EXECUTE)에 코드 전용 단계가 없는가
- [x] install-mac.sh에 하드코딩된 op-task-qa 경로가 없는가

### 문서 품질
- [x] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가
- [x] kebab-case 파일/폴더 네이밍을 따르는가
- [x] YAML frontmatter가 올바른가 (name, description 필수)
- [x] CLAUDE.md, README.md, ARCHITECTURE.md, CONVENTIONS.md 4개 문서가 모두 업데이트되었는가

---

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| git mv 후 기존 디렉토리 잔존 | 배포 시 중복 | git status로 확인, 잔존 시 삭제 |
| 범용 op-task-qa가 dev QA 호출하는 오케스트레이터에서 잘못 사용 | QA 품질 저하 | 하네스 분기 테이블 + 오케스트레이터별 명시적 스킬명으로 방지 |
| opal-pilot-write-tech가 op-task-qa를 잠재적으로 참조할 가능성 | 불필요한 변경 | 현재 자체 QA 시스템 확인 완료, 변경 불필요 |
| 기존 배포된 ~/.opal/skills/op-task-qa가 dev 내용으로 남아있을 수 있음 | 범용 QA 오동작 | install-mac.sh 재배포로 해결 (클린 배포 전략) |
