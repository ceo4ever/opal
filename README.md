# AI 개발 프레임워크

AI 환경(Claude Code, Cursor, Antigravity 등)에서 IT 프로젝트를 체계적으로 수행하기 위한 **범용 AI 개발 프레임워크**.
에이전트, 스킬, 훅 등의 재사용 가능한 컴포넌트를 만들어 다양한 AI 도구와 프로젝트에 적용할 수 있다.

---

## 2계층 아키텍처

```
Global Layer (1회 설치 → 모든 프로젝트에서 사용)
┌───────────────────────────────────────────────────┐
│  Claude Code : ~/.claude/skills/ + agents/         │
│  Cursor      : ~/.cursor/skills/ + agents/         │
│  Antigravity : ~/.gemini/antigravity/skills/       │
└────────────────────┬──────────────────────────────┘
                     │ READ
Project Layer (프로젝트마다 설정)
┌────────────────────▼──────────────────────────────┐
│  Claude Code  : {프로젝트}/CLAUDE.md                │
│  Cursor       : {프로젝트}/.cursor/rules/*.mdc      │
│  Antigravity  : {프로젝트}/GEMINI.md                 │
│                                                   │
│  언어 규칙, 기술 스택, 아키텍처,                       │
│  코드 컨벤션, 문서 표준, 워크플로우                     │
└───────────────────────────────────────────────────┘
```

글로벌 레이어의 스킬/에이전트는 프로젝트 레이어의 설정을 읽어 프로젝트 컨텍스트(언어 규칙, 기술 스택, 코드 컨벤션 등)에 맞게 동작한다.

---

## 컴포넌트 목록

### Skills (6개)

| 스킬 | 설명 | 용도 |
|------|------|------|
| **task-flow** | 핵심 오케스트레이터 | TASK → RESEARCH → PLAN → TODO → EXECUTE 5단계 파이프라인 |
| **api-analyzer** | 외부 API 분석 | 7단계 분석 및 API 명세서 생성 |
| **doc-writer** | 기술 문서 표준 | 모든 문서 스킬의 베이스 템플릿 |
| **interview** | 요구사항 수집 | 구조화된 Q&A로 요구사항 수집 및 갭 탐지 |
| **version-mgr** | 버전 관리 | 산출물 v{Major}.{Minor} 버전 관리, 덮어쓰기 금지 |
| **wireframe-builder** | 와이어프레임 | 단일 HTML 인터랙티브 와이어프레임 생성 |

### Agents (3개)

| 에이전트 | 설명 | 호출 시점 |
|---------|------|----------|
| **task-flow-qa** | 산출물 품질 검증 | 각 단계 산출물 작성 후 (5단계 문서 리뷰) |
| **task-flow-planner** | 실행 아키텍처 설계 | TODO 단계에서 복잡 모드 판별 시 (Part C 생성) |
| **task-flow-test** | 테스트 실행 | EXECUTE 완료 후 복잡 모드에서 (코드 동적 검증) |

### 의존 관계

```
task-flow (진입점)
├── task-flow-qa ──── 각 단계 완료 후 명시적 호출
├── task-flow-planner ── TODO 복잡 모드 시 호출
├── task-flow-test ───── EXECUTE 복잡 모드 후 호출
├── doc-writer ────────── 문서 작성 시 포맷 참조
├── version-mgr ───────── 산출물 버전 관리
└── interview ─────────── 요구사항 불명확 시 호출

api-analyzer ──── 독립 (외부 API 분석)
wireframe-builder ── 독립 (UI 와이어프레임)
```

---

## 설치 가이드

### 사전 요구사항

- Claude Code 또는 Cursor가 설치되어 있어야 한다
- 이 저장소를 로컬에 클론한다

```bash
git clone {REPO_URL} ai-framework
cd ai-framework
```

### Claude Code 설치

```bash
# 심볼릭 링크 (권장 — 업데이트 자동 반영)
ln -s $(pwd)/claude/skills/* ~/.claude/skills/
ln -s $(pwd)/claude/agents/* ~/.claude/agents/

# 또는 복사
cp -r claude/skills/* ~/.claude/skills/
cp -r claude/agents/* ~/.claude/agents/
```

### Cursor 설치

```bash
# 심볼릭 링크 (권장)
ln -s $(pwd)/cursor/skills/* ~/.cursor/skills/
ln -s $(pwd)/cursor/agents/* ~/.cursor/agents/

# 또는 복사
cp -r cursor/skills/* ~/.cursor/skills/
cp -r cursor/agents/* ~/.cursor/agents/
```

> **참고**: Cursor 에이전트는 플랫 파일 형식 (`.md`)으로 관리된다. `cursor/agents/task-flow-qa.md` 등.

### Antigravity 설치

```bash
# 심볼릭 링크 (권장)
mkdir -p ~/.gemini/antigravity/skills
ln -s $(pwd)/antigravity/skills/* ~/.gemini/antigravity/skills/

# 또는 복사
cp -r antigravity/skills/* ~/.gemini/antigravity/skills/
```

> **참고**: Antigravity에서는 에이전트와 스킬을 구분하지 않는다. 모든 컴포넌트가 `skills/` 디렉토리의 SKILL.md로 통합된다.

---

## 프로젝트 설정 가이드

글로벌 레이어 설치만으로는 스킬/에이전트가 프로젝트 컨텍스트를 알 수 없다. **프로젝트마다** 아래 설정을 해야 한다.

### Claude Code: CLAUDE.md

대부분의 프로젝트에는 이미 `CLAUDE.md`가 있다. 템플릿 파일 전체를 복사하는 것이 아니라, **기존 CLAUDE.md에 누락된 섹션을 추가**하는 방식으로 설정한다.

**설정 방법:**

```bash
# 1. 템플릿을 참조용으로 열어둔다
cat ai-framework/templates/CLAUDE.md

# 2. 기존 프로젝트의 CLAUDE.md에 누락된 섹션을 추가한다
#    아래 테이블에서 "필수" 섹션이 기존 파일에 없으면 템플릿에서 해당 부분을 복사하여 붙여넣는다
#    {PLACEHOLDER}를 프로젝트에 맞게 교체한다
```

> CLAUDE.md가 없는 새 프로젝트라면 `cp ai-framework/templates/CLAUDE.md {프로젝트}/CLAUDE.md`로 복사 후 `{PLACEHOLDER}`를 교체한다.

**스킬/에이전트가 읽는 섹션:**

| 섹션 | 읽는 컴포넌트 | 필수 여부 | 비고 |
|------|-------------|----------|------|
| Project Overview | task-flow (TASK 작성) | 필수 | 프로젝트 설명, 핵심 목표 |
| Language Convention | doc-writer, task-flow-qa | 필수 | 문서/코드/파일 언어 규칙 |
| Tech Stack | task-flow-planner (도구 탐색) | 필수 | 기술 스택 테이블 |
| Architecture | task-flow (RESEARCH), task-flow-planner | 권장 | 소스 구조, 설계 결정 |
| Code Conventions | task-flow-qa (E-4), EXECUTE 서브에이전트 | 필수 | 코드 스타일, 네이밍, 품질 도구 |
| 문서 표준 | doc-writer, version-mgr | 기본값 있음 | 헤더/변경이력 형식 |
| 버전 관리 규칙 | version-mgr | 기본값 있음 | v{Major}.{Minor} 규칙 |
| 개발 워크플로우 | task-flow | 기본값 있음 | 구현 금지 원칙, 파이프라인 |
| 산출물 구조 | task-flow | 기본값 있음 | tasks/ 폴더 구조 |

- **필수**: 기존 CLAUDE.md에 없으면 반드시 추가
- **권장**: 있으면 분석 품질 향상
- **기본값 있음**: 생략해도 프레임워크 기본값으로 동작. 프로젝트 특성에 맞게 수정할 때만 추가

### Cursor: .cursor/rules/

프로젝트 루트에 `.cursor/rules/` 디렉토리를 생성하고 룰 파일을 복사한다.

```bash
# 템플릿 복사
mkdir -p {프로젝트}/.cursor/rules
cp ai-framework/templates/cursor-rules/*.mdc {프로젝트}/.cursor/rules/
```

**룰 파일 목록:**

| 파일 | 모드 | 설명 |
|------|------|------|
| `001-project-conventions.mdc` | Always | 프로젝트 핵심 규칙 (언어, 스택, 아키텍처, 컨벤션) |
| `002-development-workflow.mdc` | Always | task-flow 파이프라인 + 구현 금지 원칙 |
| `100-document-standards.mdc` | Agent Requested | 문서 표준 + 버전 관리 (문서 작성 시만 로드) |
| `101-task-artifacts.mdc` | Agent Requested | 태스크 산출물 구조 + 순번 규칙 (태스크 수행 시만 로드) |

**룰 번호 체계:**

- `001-099`: **Always Apply** — 매 세션마다 자동 주입
- `100-199`: **Agent Requested** — AI가 관련성 판단 시에만 로드 (토큰 절약)

`001-project-conventions.mdc`의 `{PLACEHOLDER}`를 프로젝트에 맞게 교체한다. 나머지 파일은 프레임워크 공통이므로 그대로 사용한다.

### Antigravity: GEMINI.md

프로젝트 루트에 `GEMINI.md`를 생성한다. `CLAUDE.md`와 동일한 역할이지만, Antigravity에서 자동으로 읽는 프로젝트 컨텍스트 파일이다.

```bash
# 템플릿 복사
cp ai-framework/templates/GEMINI.md {프로젝트}/GEMINI.md

# {PLACEHOLDER} 교체
```

> **주의**: `~/.gemini/GEMINI.md`에 추가하면 Gemini CLI 등 다른 Gemini 기반 도구와 공유될 수 있다. Antigravity 전용으로 사용하려면 프로젝트 `GEMINI.md`에 추가하는 것을 권장한다.

### CLAUDE.md ↔ Cursor Rules ↔ GEMINI.md 동등성 매핑

CLAUDE.md의 각 섹션이 Cursor Rules의 어느 파일에 대응하는지 정리한 표이다. 두 플랫폼에서 동일한 규칙이 적용되도록 한다.

| CLAUDE.md 섹션 | Cursor 룰 파일 | 모드 |
|---------------|---------------|------|
| Project Overview | `001-project-conventions.mdc` | Always |
| Language Convention | `001-project-conventions.mdc` | Always |
| Tech Stack | `001-project-conventions.mdc` | Always |
| Architecture | `001-project-conventions.mdc` | Always |
| Code Conventions | `001-project-conventions.mdc` | Always |
| 구현 금지 원칙 | `002-development-workflow.mdc` | Always |
| 개발 워크플로우 | `002-development-workflow.mdc` | Always |
| 문서 표준 | `100-document-standards.mdc` | Agent Requested |
| 버전 관리 규칙 | `100-document-standards.mdc` | Agent Requested |
| 산출물 구조 | `101-task-artifacts.mdc` | Agent Requested |

---

## 알투(R2) AI 파트너 설정

알투(R2)는 사용자 전용 AI 파트너다. 한번 설정하면 어떤 프로젝트를 열든 알투로서 대화하고, 프레임워크의 스킬/에이전트를 활용하여 작업을 수행한다.

### Claude Code 설정

`templates/r2/claude-snippet.md`의 마크다운 코드 블록 안 내용을 `~/.claude/CLAUDE.md`에 추가한다.

```bash
# 1. 현재 CLAUDE.md 내용 확인
cat ~/.claude/CLAUDE.md

# 2. claude-snippet.md의 코드 블록 안 내용을 CLAUDE.md 하단에 추가
#    (SuperClaude 등 기존 내용 아래에 붙여넣기)
```

### Cursor 설정

`templates/r2/000-r2-persona.mdc`를 `~/.cursor/rules/`에 복사한다.

```bash
# 글로벌 룰 디렉토리에 복사
mkdir -p ~/.cursor/rules
cp templates/r2/000-r2-persona.mdc ~/.cursor/rules/
```

> **번호 `000`**: 다른 룰보다 먼저 로드되어 AI의 정체성을 가장 먼저 설정한다.
> **`alwaysApply: true`**: 매 세션마다 자동으로 주입된다.

### Antigravity 설정

`templates/r2/gemini-snippet.md`의 마크다운 코드 블록 안 내용을 프로젝트 `GEMINI.md` 또는 글로벌 `~/.gemini/GEMINI.md`에 추가한다.

```bash
# 프로젝트 GEMINI.md에 추가 (권장)
# gemini-snippet.md의 코드 블록 안 내용을 GEMINI.md 하단에 추가

# 또는 글로벌 설정
# ~/.gemini/GEMINI.md 하단에 추가
```

> **주의**: `~/.gemini/GEMINI.md`에 추가하면 Gemini CLI 등 다른 도구와 공유될 수 있다.

---

## 빠른 시작 (Quick Start)

### Claude Code 프로젝트

```bash
# 1. 글로벌 설치 (최초 1회)
ln -s $(pwd)/claude/skills/* ~/.claude/skills/
ln -s $(pwd)/claude/agents/* ~/.claude/agents/

# 2. 프로젝트 설정 — 기존 CLAUDE.md에 섹션 추가
#    templates/CLAUDE.md를 참조하여, 기존 CLAUDE.md에 누락된 섹션을 추가한다
#    (CLAUDE.md가 없는 새 프로젝트라면 cp templates/CLAUDE.md {프로젝트}/CLAUDE.md)

# 3. {PLACEHOLDER} 교체
#    추가한 섹션의 {PLACEHOLDER}를 프로젝트에 맞게 교체

# 4. 개발 시작
cd /path/to/your-project
claude  # Claude Code 실행 후 task-flow 스킬 사용
```

### Cursor 프로젝트

```bash
# 1. 글로벌 설치 (최초 1회)
ln -s $(pwd)/cursor/skills/* ~/.cursor/skills/
ln -s $(pwd)/cursor/agents/* ~/.cursor/agents/

# 2. 프로젝트 설정
mkdir -p /path/to/your-project/.cursor/rules
cp templates/cursor-rules/*.mdc /path/to/your-project/.cursor/rules/

# 3. {PLACEHOLDER} 교체
#    001-project-conventions.mdc의 {PLACEHOLDER}를 프로젝트에 맞게 교체

# 4. 개발 시작
#    Cursor에서 프로젝트를 열고 task-flow 스킬 사용
```

### Antigravity 프로젝트

```bash
# 1. 글로벌 설치 (최초 1회)
mkdir -p ~/.gemini/antigravity/skills
ln -s $(pwd)/antigravity/skills/* ~/.gemini/antigravity/skills/

# 2. 프로젝트 설정
cp templates/GEMINI.md /path/to/your-project/GEMINI.md

# 3. {PLACEHOLDER} 교체
#    GEMINI.md의 {PLACEHOLDER}를 프로젝트에 맞게 교체

# 4. 개발 시작
#    Antigravity에서 프로젝트를 열고 task-flow 스킬 사용
```

---

## 핵심 워크플로우: task-flow

모든 개발 작업의 중심 5단계 파이프라인:

```
TASK → RESEARCH → PLAN → TODO → EXECUTE
```

| 단계 | 목적 | 산출물 |
|------|------|--------|
| **TASK** | 작업 정의 | TASK.md — 목표, 요구사항, 제약사항, 성공 기준 |
| **RESEARCH** | 기술 분석 | RESEARCH.md — 현재 코드, 영향 범위, 리스크 |
| **PLAN** | 구현 설계 | PLAN.md — 설계, 의존 관계, 파일 목록 |
| **TODO** | 실행 계획 | TODO.md — Part A(단계) + Part B(QA) + Part C(복잡 모드) |
| **EXECUTE** | 코드 구현 | 승인된 계획에 따른 코드 변경 |

**핵심 규칙**: 사용자의 명시적 승인 전까지 코드 생성/수정 금지. 각 단계 산출물은 QA 에이전트/스킬이 1차 검토 후 사용자에게 보고한다.

**적응적 실행**: TODO 단계에서 복잡도를 자동 판별한다.

| 기준 | 단순 모드 | 복잡 모드 |
|------|----------|----------|
| 단계 수 | ≤5 | ≥6 |
| 변경 파일 수 | ≤3 | ≥4 |
| 모듈 범위 | 단일 | 다중 |
| 신규 의존성 | 없음 | 있음 |

---

## 새 컴포넌트 작성 가이드

### Skill 추가

1. `claude/skills/{skill-name}/SKILL.md` 생성
2. YAML frontmatter에 `name`, `description` 정의 (description에 트리거 키워드 포함)
3. 단계별 프로세스와 산출물 형식을 명확히 기술
4. 필요 시 `references/` 하위에 상세 가이드 추가

### Agent 추가

1. `claude/agents/{agent-name}/AGENT.md` 생성
2. YAML frontmatter에 `name`, `description` 정의
3. Cursor 호환 필드 추가: `model: inherit`, `readonly: true/false`
4. 입력/출력 명세, 실행 프로세스, 검증 기준을 명확히 기술
5. 네이밍: `{대상 워크플로우}-{역할}` (예: `task-flow-qa`)
6. 호출하는 스킬의 SKILL.md에 에이전트 탐색 경로 명시

### 탐색 경로 (우선순위)

에이전트/스킬을 호출할 때 아래 순서로 탐색한다:

1. `{프로젝트}/.cursor/agents/{agent-name}.md`
2. `{프로젝트}/.claude/agents/{agent-name}/AGENT.md`
3. `{프로젝트}/.agent/skills/{agent-name}/SKILL.md`
4. `~/.cursor/agents/{agent-name}.md`
5. `~/.claude/agents/{agent-name}/AGENT.md`
6. `~/.gemini/antigravity/skills/{agent-name}/SKILL.md`

---

## 소스 구조

```
ai-framework/
├── README.md                    ← 이 파일
├── CLAUDE.md                    ← 이 저장소 자체의 프로젝트 설정
├── claude/                      ← Claude Code 전용 소스
│   ├── skills/
│   │   ├── task-flow/           핵심 오케스트레이터
│   │   ├── api-analyzer/        외부 API 분석
│   │   ├── doc-writer/          기술 문서 표준
│   │   ├── interview/           요구사항 수집
│   │   ├── version-mgr/         버전 관리
│   │   └── wireframe-builder/   와이어프레임 생성
│   └── agents/
│       ├── task-flow-qa/        산출물 품질 검증
│       ├── task-flow-planner/   실행 아키텍처 설계
│       └── task-flow-test/      테스트 실행
├── cursor/                      ← Cursor 전용 소스
│   ├── skills/                  (claude/skills/와 동일)
│   └── agents/                  플랫 파일: task-flow-qa.md 등
├── antigravity/                 ← Antigravity 전용 소스
│   └── skills/                  스킬 9개 (에이전트 3개를 스킬로 통합)
│       ├── task-flow/           (Antigravity 특화 수정)
│       ├── task-flow-qa/        (AGENT→SKILL 변환)
│       └── ...
└── templates/                   ← 프로젝트 설정 템플릿
    ├── CLAUDE.md                CLAUDE.md 템플릿 (Claude Code)
    ├── GEMINI.md                GEMINI.md 템플릿 (Antigravity)
    ├── cursor-rules/
    │   ├── 001-project-conventions.mdc    Always: 프로젝트 핵심 규칙
    │   ├── 002-development-workflow.mdc   Always: 워크플로우 + 구현 금지
    │   ├── 100-document-standards.mdc     Agent Requested: 문서 표준
    │   └── 101-task-artifacts.mdc         Agent Requested: 산출물 구조
    └── r2/                      ← 알투(R2) AI 파트너 설정
        ├── claude-snippet.md    ~/.claude/CLAUDE.md에 추가할 스니펫
        ├── gemini-snippet.md    GEMINI.md에 추가할 스니펫 (Antigravity)
        └── 000-r2-persona.mdc   ~/.cursor/rules/에 복사할 글로벌 룰
```

---

## 언어 규칙

| 대상 | 언어 |
|------|------|
| 문서 본문 | 한국어 (기술 용어는 영어 병기) |
| 코드/변수/필드명 | English |
| 파일/폴더 명명 | kebab-case |

---

## 라이선스

{LICENSE}
