# PLAN: Antigravity 플랫폼 지원 추가 및 QA 호출 구조 개선

> 작성일: 2026-03-07 | 참조: TASK.md, RESEARCH.md

## 1. 구현 범위

### 신규 생성 파일

| # | 파일 경로 | 역할 |
|---|----------|------|
| N-1 | `antigravity/skills/task-flow/SKILL.md` | Antigravity용 task-flow (에이전트→스킬 호출 방식으로 변경) |
| N-2 | `antigravity/skills/task-flow/references/research-guide.md` | task-flow 참조 가이드 (claude/와 동일, QA 호출 단계 포함) |
| N-3 | `antigravity/skills/task-flow/references/plan-guide.md` | 〃 |
| N-4 | `antigravity/skills/task-flow/references/todo-guide.md` | 〃 |
| N-5 | `antigravity/skills/task-flow/references/execute-guide.md` | 〃 |
| N-6 | `antigravity/skills/task-flow/references/execute-plan-guide.md` | 〃 (변경 없이 복사) |
| N-7 | `antigravity/skills/api-analyzer/SKILL.md` | claude/와 동일 내용 복사 |
| N-8 | `antigravity/skills/doc-writer/SKILL.md` | 〃 |
| N-9 | `antigravity/skills/interview/SKILL.md` | 〃 |
| N-10 | `antigravity/skills/version-mgr/SKILL.md` | 〃 |
| N-11 | `antigravity/skills/wireframe-builder/SKILL.md` | 〃 |
| N-12 | `antigravity/skills/task-flow-qa/SKILL.md` | QA 에이전트 → SKILL.md 포맷 변환 |
| N-13 | `antigravity/skills/task-flow-planner/SKILL.md` | Planner 에이전트 → SKILL.md 포맷 변환 |
| N-14 | `antigravity/skills/task-flow-test/SKILL.md` | Test 에이전트 → SKILL.md 포맷 변환 |
| N-15 | `cursor/agents/task-flow-qa.md` | Cursor 플랫 파일 에이전트 |
| N-16 | `cursor/agents/task-flow-planner.md` | 〃 |
| N-17 | `cursor/agents/task-flow-test.md` | 〃 |
| N-18 | `templates/GEMINI.md` | Antigravity 프로젝트 컨텍스트 템플릿 |
| N-19 | `templates/r2/gemini-snippet.md` | 알투 GEMINI.md 삽입 스니펫 |

### 수정 파일

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| M-1 | `claude/skills/task-flow/SKILL.md` | 에이전트 탐색 경로에 Antigravity 경로 추가 + 각 STEP QA 호출을 별도 서브섹션으로 강조 |
| M-2 | `claude/skills/task-flow/references/research-guide.md` | 끝에 "QA 에이전트 호출" 섹션 추가 |
| M-3 | `claude/skills/task-flow/references/plan-guide.md` | 〃 |
| M-4 | `claude/skills/task-flow/references/todo-guide.md` | 〃 |
| M-5 | `claude/skills/task-flow/references/execute-guide.md` | 〃 |
| M-6 | `claude/agents/task-flow-qa/AGENT.md` | "자동 호출됩니다" → "메인 에이전트가 명시적으로 호출해야 합니다" |
| M-7 | `CLAUDE.md` | 아키텍처 섹션에 Antigravity 추가, Cursor 에이전트 구조 업데이트, 배포 구조 3-플랫폼 반영 |
| M-8 | `README.md` | Antigravity 설치/설정 가이드 추가, Cursor 에이전트 마이그레이션 안내 |
| M-9 | `cursor/skills/` (전체) | claude/skills/ 수정 내용을 cursor/skills/에 재복사하여 동기화. task-flow SKILL.md + references 4개 파일의 QA 호출 강조 + Antigravity 탐색 경로가 Cursor 환경에서도 반영됨 |

### 삭제 파일

| # | 파일 경로 | 사유 |
|---|----------|------|
| D-1 | `cursor/agents/task-flow-qa/AGENT.md` | 플랫 파일(N-15)로 대체 |
| D-2 | `cursor/agents/task-flow-planner/AGENT.md` | 플랫 파일(N-16)로 대체 |
| D-3 | `cursor/agents/task-flow-test/AGENT.md` | 플랫 파일(N-17)로 대체 |

## 2. 구현 순서

의존성 원칙: **소스 원본(claude/) 수정 → Cursor 구조 변경 → Antigravity 생성 → 템플릿/문서**

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | QA 호출 구조 개선 — 레퍼런스 가이드 수정 | M-2, M-3, M-4, M-5 | 낮음 |
| 2 | QA 호출 구조 개선 — AGENT.md 표현 수정 | M-6 | 낮음 |
| 3 | QA 호출 구조 개선 — SKILL.md QA 호출 강조 + Antigravity 탐색 경로 추가 | M-1 | 중간 |
| 4 | Cursor 에이전트 플랫 파일 전환 | D-1~D-3 삭제, N-15~N-17 생성 | 낮음 |
| 5 | Antigravity 스킬 생성 — 단순 복사 (5개) | N-7~N-11 | 낮음 |
| 6 | Antigravity 스킬 생성 — task-flow + references | N-1~N-6 | 중간 |
| 7 | Antigravity 스킬 생성 — 에이전트→스킬 변환 (3개) | N-12~N-14 | 중간 |
| 8 | 템플릿 생성 | N-18, N-19 | 낮음 |
| 9 | Cursor 스킬 미러 동기화 — claude/skills/ 수정 내용을 cursor/skills/에 재복사 | M-9 (cursor/skills/ 전체 재동기화) | 낮음 |
| 10 | 프로젝트 문서 업데이트 | M-7, M-8 | 중간 |

## 3. 핵심 설계

### 3.1 QA 호출 구조 개선 (C 트랙)

#### M-2~M-5: 레퍼런스 가이드에 QA 호출 단계 추가

각 가이드(`research-guide.md`, `plan-guide.md`, `todo-guide.md`, `execute-guide.md`)의 "품질 체크리스트" 섹션 **아래에** 다음 섹션을 추가:

```markdown
---

## ⚠️ QA 에이전트 호출 (필수)

이 가이드의 산출물 작성이 완료되면, 반드시 **QA 에이전트를 호출**해야 한다.
자체 품질 체크리스트 검증만으로는 불충분하며, QA 에이전트의 독립적 리뷰를 거쳐야 사용자에게 보고할 수 있다.

**호출 방법**: SKILL.md의 "QA 에이전트 호출 규칙" 섹션을 참조하여 서브 에이전트(Task 도구)로 실행한다.
```

#### M-6: AGENT.md "자동 호출" 표현 수정

변경 전:
```
이 에이전트는 task-flow 스킬이 각 단계 산출물(.md)을 작성한 직후, 사용자 검토 전에 자동 호출됩니다.
```

변경 후:
```
이 에이전트는 task-flow 스킬의 각 단계 산출물(.md) 작성 직후, 사용자 검토 전에 호출됩니다.
메인 에이전트가 SKILL.md의 "QA 에이전트 호출 규칙"에 따라 서브 에이전트(Task 도구)로 명시적으로 호출해야 합니다. 시스템이 자동으로 호출하지 않습니다.
```

#### M-1: SKILL.md QA 호출 강조 + Antigravity 탐색 경로

각 STEP(1~5)의 마지막 한 줄 QA 호출 지시를 **별도 서브섹션 블록**으로 교체:

변경 전 (STEP 2 예시):
```
RESEARCH.md 작성 후 **QA 에이전트를 호출**(QA 에이전트 호출 규칙 참조)하여 QA-RESEARCH.md를 생성한 뒤, 사용자에게 보고한다.
```

변경 후:
```markdown
### ⚠️ QA 에이전트 호출 (필수)

RESEARCH.md 작성 완료 후, 다음 단계로 넘어가기 전에 **반드시 QA 에이전트를 호출**해야 한다:

1. 상단의 "QA 에이전트 호출 규칙"에 따라 task-flow-qa 에이전트를 서브 에이전트(Task 도구)로 실행
2. QA-RESEARCH.md 생성 확인
3. QA 결과를 포함하여 사용자에게 보고

> 자체 품질 체크리스트 검증은 QA 에이전트 호출을 대체하지 않는다. 반드시 두 가지 모두 수행해야 한다.
```

에이전트 탐색 경로에 Antigravity 추가:

```markdown
**에이전트 탐색 경로** (우선순위):
1. `{프로젝트}/.cursor/agents/task-flow-qa.md`
2. `{프로젝트}/.claude/agents/task-flow-qa/AGENT.md`
3. `{프로젝트}/.agent/skills/task-flow-qa/SKILL.md`
4. `~/.cursor/agents/task-flow-qa.md`
5. `~/.claude/agents/task-flow-qa/AGENT.md`
6. `~/.gemini/antigravity/skills/task-flow-qa/SKILL.md`
```

동일 패턴을 Planner, Test 에이전트 탐색 경로에도 적용.

### 3.2 Cursor 에이전트 플랫 파일 전환 (B 트랙)

#### N-15~N-17: 플랫 파일 생성 + D-1~D-3: 디렉토리 삭제

`cursor/agents/task-flow-qa/AGENT.md`의 내용을 `cursor/agents/task-flow-qa.md`로 이동.

**변경 사항**: 내용 동일, 파일 위치만 변경.

```
변경 전:
cursor/agents/task-flow-qa/AGENT.md
cursor/agents/task-flow-planner/AGENT.md
cursor/agents/task-flow-test/AGENT.md

변경 후:
cursor/agents/task-flow-qa.md
cursor/agents/task-flow-planner.md
cursor/agents/task-flow-test.md
```

M-6의 "자동 호출" 표현 수정도 Cursor 버전에 동일 적용.

### 3.3 Antigravity 스킬 — 단순 복사 (N-7~N-11)

`claude/skills/{name}/SKILL.md`를 `antigravity/skills/{name}/SKILL.md`로 복사.

대상: `api-analyzer`, `doc-writer`, `interview`, `version-mgr`, `wireframe-builder`

각 스킬에 하위 디렉토리(references/ 등)가 있으면 함께 복사.

### 3.4 Antigravity task-flow (N-1~N-6)

`claude/skills/task-flow/`를 `antigravity/skills/task-flow/`로 복사한 뒤, **Antigravity 특화 수정** 적용:

**SKILL.md 수정 사항:**

1. **에이전트 호출 → 스킬 호출로 용어 변경**:
   - "QA 에이전트" → "task-flow-qa 스킬"
   - "서브 에이전트(Task 도구)" → "스킬 호출" (Antigravity는 스킬 간 체이닝으로 동작)

2. **탐색 경로를 Antigravity 전용으로**:
   ```markdown
   **스킬 탐색 경로** (우선순위):
   1. `{프로젝트}/.agent/skills/task-flow-qa/SKILL.md`
   2. `~/.gemini/antigravity/skills/task-flow-qa/SKILL.md`
   ```

3. **호출 방법 변경**:
   ```
   1. 위 탐색 경로에서 SKILL.md를 찾아 읽는다
   2. SKILL.md의 실행 프로세스에 따라 QA 검증을 수행한다
   3. QA-{단계}.md를 생성한다
   4. QA 결과를 포함하여 사용자에게 보고한다
   ```

references 가이드(N-2~N-6)는 M-2~M-5 수정이 적용된 상태로 복사. execute-plan-guide.md(N-6)는 변경 없이 복사.

### 3.5 Antigravity 에이전트→스킬 변환 (N-12~N-14)

AGENT.md의 내용을 SKILL.md 포맷으로 변환. 핵심 구조:

**변환 전 (AGENT.md frontmatter):**
```yaml
---
name: task-flow-qa
description: |
  task-flow 산출물 품질 검증 에이전트...
model: inherit
readonly: true
---
```

**변환 후 (SKILL.md frontmatter):**
```yaml
---
name: task-flow-qa
description: |
  **task-flow 산출물 품질 검증 스킬**. TASK → RESEARCH → PLAN → TODO → EXECUTE 각 단계 산출물을 독립적으로 검토하여 요약과 판정을 제공합니다.
  task-flow 스킬이 각 단계 산출물(.md)을 작성한 직후 호출합니다.
---
```

**변환 규칙:**
- `model: inherit` → 제거 (SKILL.md에 해당 필드 없음)
- `readonly: true/false` → 제거 (SKILL.md에 해당 필드 없음, 본문에 주의사항으로 표기)
- `description` → 시맨틱 매칭을 위해 트리거 키워드 보강
- 본문 → 그대로 유지 (검증 기준, 입출력 명세, 프로세스 동일)
- "에이전트" 용어 → "스킬" 로 교체
- "서브 에이전트(Task 도구)" 표현 → 제거 (Antigravity에서는 스킬로 직접 실행)

### 3.6 템플릿 (N-18, N-19)

#### N-18: `templates/GEMINI.md`

`templates/CLAUDE.md`를 기반으로 작성. 주요 변경:

- 헤더: "이 파일은 Antigravity에서 프로젝트 컨텍스트로 사용됩니다"
- Claude Code 전용 언급 제거
- 배포 경로를 Antigravity 기준으로 변경:
  - Skills: `~/.gemini/antigravity/skills/`
  - Workflows: `.agent/workflows/`
- 나머지 구조(Project Overview, Language Convention, Tech Stack 등)는 동일

#### N-19: `templates/r2/gemini-snippet.md`

`templates/r2/claude-snippet.md`를 기반으로 작성. 주요 변경:

- "~/.claude/CLAUDE.md에 추가하세요" → "프로젝트 GEMINI.md 또는 ~/.gemini/GEMINI.md에 추가하세요"
- 알투 페르소나 내용은 동일
- 에이전트 탐색 경로를 Antigravity 기준으로 변경
- Gemini CLI와의 충돌 가능성 주의사항 추가

### 3.7 프로젝트 문서 업데이트 (M-7, M-8)

#### M-7: `CLAUDE.md`

수정 영역:
1. **소스 구조**에 `antigravity/` 추가
2. **배포 구조**에 Antigravity 배포 경로 추가 (`~/.gemini/antigravity/`)
3. **Cursor 에이전트 구조**를 플랫 파일로 업데이트
4. **에이전트 탐색 경로**에 Antigravity 경로 추가
5. **컴포넌트 유형 테이블**에 Antigravity 상태 추가

#### M-8: `README.md`

추가 영역:
1. **Antigravity 설치** 섹션 (Skills 배포 + GEMINI.md 설정)
2. **Antigravity 프로젝트 설정** 섹션
3. **Cursor 마이그레이션** 안내 (디렉토리 에이전트 → 플랫 파일)
4. 아키텍처 다이어그램에 Antigravity 추가

## 4. 의존성 및 환경 변경

- 추가 패키지: 없음
- 환경 설정 변경: 없음
- 외부 도구: 없음

모든 작업이 Markdown 파일 생성/수정이므로 외부 의존성이 없다.

## 5. 테스트 전략

| # | 테스트 항목 | 검증 방법 |
|---|-----------|----------|
| T-1 | SKILL.md YAML frontmatter 유효성 | 모든 신규 SKILL.md에 `name`과 `description` 필드 존재 확인 |
| T-2 | 에이전트 탐색 경로 일관성 | SKILL.md에 명시된 모든 탐색 경로에 대응하는 파일이 존재하는지 확인 |
| T-3 | 레퍼런스 가이드 QA 호출 섹션 | 4개 가이드 모두에 "QA 에이전트 호출" 섹션이 추가되었는지 확인 |
| T-4 | Cursor 플랫 파일 구조 | `cursor/agents/` 아래에 디렉토리가 없고 `.md` 파일만 존재하는지 확인 |
| T-5 | claude ↔ cursor ↔ antigravity 스킬 내용 동기화 | task-flow 제외 5개 스킬의 내용이 3-플랫폼 동일한지 diff 비교 |
| T-6 | 문서 상호 참조 | CLAUDE.md, README.md에 명시된 경로/구조가 실제 파일 구조와 일치하는지 확인 |
| T-7 | GEMINI.md 템플릿 유효성 | `templates/GEMINI.md`가 `templates/CLAUDE.md`의 필수 섹션(Project Overview, Language, Tech Stack, Architecture, Code Conventions)을 모두 포함하는지 확인 |
| T-8 | 알투 페르소나 동일성 | `templates/r2/gemini-snippet.md`가 `claude-snippet.md`의 알투 핵심 요소(정체성, 성격, 주도성, 역할)를 모두 포함하는지 확인 |
| T-9 | Claude Code 하위 호환 | `claude/agents/` 디렉토리 구조가 변경되지 않았는지 확인 (AGENT.md 내용 수정만, 디렉토리 구조는 그대로) |

## 6. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| Antigravity 프리뷰 설정 체계 변경 | antigravity/ 디렉토리 전체 수정 필요 | antigravity/를 격리된 디렉토리로 유지, README에 버전 명시 |
| 에이전트→스킬 변환 시 독립 컨텍스트 약화 | QA 객관성 저하 | SKILL.md 내 "독립적 관점에서 검토" 지시 강화 |
| Cursor 에이전트 구조 변경 시 기존 사용자 영향 | 기존 디렉토리 에이전트 무효화 | README에 마이그레이션 가이드 명시 |
| `~/.gemini/GEMINI.md` Gemini CLI 충돌 | 글로벌 알투 설정이 CLI에 영향 | 프로젝트 GEMINI.md 우선 사용 권장, README에 충돌 주의사항 명시 |
