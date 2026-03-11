# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI 환경(Claude Code, Cursor, Codex 등)에서 IT 프로젝트를 체계적으로 수행하기 위한 **범용 AI 개발 프레임워크**. 에이전트, 스킬, 훅 등의 재사용 가능한 컴포넌트를 만들어 다양한 AI 도구와 프로젝트에 적용할 수 있도록 하는 것이 목적이다.

### 핵심 목표

- **멀티 플랫폼**: Claude Code, Cursor, Codex 등 다양한 AI 개발 환경에서 동작
- **재사용성**: 스킬, 에이전트, 훅을 독립적 컴포넌트로 만들어 프로젝트 간 재활용
- **표준화**: IT 프로젝트 수행 시 분석 → 설계 → 구현의 품질을 일관되게 유지

## Language Convention

- **문서 본문**: 한국어 (기술 용어는 영어 병기)
- **코드/변수/필드명**: English
- **파일/폴더 명명**: kebab-case (예: `user-auth-implementation`)

## Architecture

### 소스 구조 (이 저장소)

```
claude/                          ← Claude Code 전용 컴포넌트
├── skills/                      ← 스킬 정의 (Markdown 기반)
│   ├── task-flow/             핵심 오케스트레이터: TASK → RESEARCH → PLAN → TODO → EXECUTE
│   ├── api-analyzer/             외부 API 7단계 분석 및 명세서 생성
│   ├── doc-writer/               기술 문서 표준 템플릿 (모든 문서 스킬의 베이스)
│   ├── interview/                구조화된 Q&A 요구사항 수집
│   ├── version-mgr/              산출물 버전 관리 (v{Major}.{Minor}, 덮어쓰기 금지)
│   └── wireframe-builder/        단일 HTML 인터랙티브 와이어프레임 생성
├── agents/                      ← 에이전트 정의 (자율 실행 단위)
│   ├── task-flow-qa/          산출물 품질 검증 (5단계 문서 리뷰)
│   ├── task-flow-planner/     실행 아키텍처 설계 (복잡 모드 Part C 생성)
│   └── task-flow-test/        테스트 실행 (코드 동적 검증)
└── hooks/                       ← 훅 정의 (이벤트 트리거, 예정)

cursor/                          ← Cursor 전용 컴포넌트
├── skills/                      ← claude/skills/와 동일 내용
└── agents/                      ← 플랫 파일 형식 (.md)
    ├── task-flow-qa.md
    ├── task-flow-planner.md
    └── task-flow-test.md

antigravity/                     ← Antigravity 전용 컴포넌트
└── skills/                      ← 스킬 정의 (에이전트도 스킬로 통합)
    ├── task-flow/             핵심 오케스트레이터 (Antigravity 특화)
    ├── task-flow-qa/          산출물 품질 검증 (AGENT→SKILL 변환)
    ├── task-flow-planner/     실행 아키텍처 설계 (AGENT→SKILL 변환)
    ├── task-flow-test/        테스트 실행 (AGENT→SKILL 변환)
    ├── api-analyzer/          외부 API 분석
    ├── doc-writer/            기술 문서 표준
    ├── interview/             요구사항 수집
    ├── version-mgr/           버전 관리
    └── wireframe-builder/     와이어프레임 생성

templates/opal/                  ← OPAL AI 에이전트 (크로스 플랫폼)
├── bootstrapper/                ← 부트스트래퍼 (플랫폼별)
│   ├── claude-bootstrap.md      Claude Code용
│   ├── cursor-bootstrap.mdc    Cursor용
│   └── gemini-bootstrap.md     Antigravity용
├── core/                        ← 에이전트 코어 (플랫폼 독립)
│   ├── AGENT.md                 에이전트 핵심 정의
│   └── identity-template.md    정체성 템플릿
├── skills/                      ← OPAL 전용 스킬
│   ├── onboarding/              초기 정체성 인터뷰
│   ├── project-init/            프로젝트 에이전트 생성
│   └── orchestrator/            프로젝트 오케스트레이션
└── templates/                   ← 프로젝트 에이전트 템플릿
    └── project-agent.md
```

### 배포 구조 (사용자 홈)

이 프레임워크를 사용하려면 각 플랫폼의 배포 경로에 복사한다 (또는 심볼릭 링크).

```
~/.claude/                       ← Claude Code 전용
├── skills/                      ← Claude Code가 자동 탐색 (네이티브 기능)
│   ├── task-flow/
│   ├── api-analyzer/
│   └── ...
├── agents/                      ← 스킬에서 탐색 경로로 참조 (디렉토리 기반)
│   ├── task-flow-qa/
│   │   └── AGENT.md
│   ├── task-flow-planner/
│   │   └── AGENT.md
│   └── task-flow-test/
│       └── AGENT.md
└── hooks/                       ← (예정)

~/.cursor/                       ← Cursor 전용
├── skills/                      ← Cursor가 자동 탐색 (네이티브 기능)
│   ├── task-flow/
│   └── ...
└── agents/                      ← Cursor가 자동 탐색 (플랫 파일 형식)
    ├── task-flow-qa.md
    ├── task-flow-planner.md
    └── task-flow-test.md

~/.gemini/antigravity/           ← Antigravity 전용
└── skills/                      ← 글로벌 스킬 (에이전트도 스킬로 통합)
    ├── task-flow/
    ├── task-flow-qa/
    ├── task-flow-planner/
    ├── task-flow-test/
    ├── api-analyzer/
    └── ...

~/.opal/                         ← OPAL AI 에이전트 홈 (크로스 플랫폼)
├── AGENT.md                     ← 에이전트 핵심 정의
├── identity.md                  ← 정체성 (온보딩으로 생성)
├── skills/                      ← OPAL 전용 스킬
│   ├── onboarding/
│   ├── project-init/
│   └── orchestrator/
└── templates/
    ├── identity-template.md
    └── project-agent.md
```

**Skills**: 각 플랫폼의 skills 디렉토리에 복사하면 자동 탐색. SKILL.md 포맷은 3개 플랫폼 모두 동일.

**Agents/QA 스킬**: Claude Code는 `agents/` 디렉토리 기반, Cursor는 `agents/` 플랫 파일, Antigravity는 `skills/`로 통합. 스킬은 플랫폼 독립적 탐색 경로로 에이전트/스킬을 찾는다 (프로젝트 로컬 → 사용자 홈 순서).

**OPAL**: `~/.opal/`에 에이전트 코어와 전용 스킬을 배치. 각 AI 플랫폼에 부트스트래퍼(3줄)를 삽입하여 세션 시작 시 AGENT.md를 로드한다.

### 컴포넌트 유형

| 유형 | 설명 | 현재 상태 |
|------|------|----------|
| **Skills** | 특정 작업을 수행하는 절차적 가이드 (SKILL.md) | `claude/skills/` 에 6개, `antigravity/skills/` 에 9개 (에이전트 3개 포함) |
| **Agents** | 독립 컨텍스트에서 자율 실행하는 에이전트 (AGENT.md) | `claude/agents/` 에 3개, `cursor/agents/` 에 3개 (플랫 파일) |
| **Hooks** | 이벤트 기반으로 자동 실행되는 트리거 | 확장 예정 |

### 컴포넌트 간 의존 관계

- **doc-writer** → 모든 문서 생성 스킬의 포맷/규칙 베이스
- **version-mgr** → 산출물을 생성·수정하는 모든 스킬에 적용
- **interview** → 요구사항 불명확 시 다른 스킬에서 호출
- **task-flow** → 개발 작업의 주 진입점 (5단계 파이프라인)
- **task-flow-qa** → task-flow 각 단계 완료 후 명시적으로 호출되는 QA 에이전트
- **task-flow-planner** → task-flow TODO 단계에서 복잡 모드 시 실행 아키텍처 설계
- **task-flow-test** → task-flow EXECUTE 단계에서 복잡 모드 시 코드 동적 검증

## 새 컴포넌트 작성 가이드

### Skill 추가 시

1. `claude/skills/{skill-name}/SKILL.md` 생성
2. YAML frontmatter에 `name`, `description` 정의 (description에 트리거 키워드 포함)
3. 단계별 프로세스와 산출물 형식을 명확히 기술
4. 필요 시 `references/` 하위에 상세 가이드 추가

### Agent 추가 시

1. `claude/agents/{agent-name}/AGENT.md` 생성
2. YAML frontmatter에 `name`, `description` 정의
3. **Cursor 호환 필드 추가** (Claude Code는 무시하므로 양쪽 호환):
   - `model: inherit` — Cursor용: 상위 에이전트 모델 상속
   - `readonly: true` — Cursor용: 읽기 전용 여부 (코드 수정 안 하는 에이전트인 경우)
4. 입력/출력 명세, 실행 프로세스, 검증 기준을 명확히 기술
5. 네이밍: `{대상 워크플로우}-{역할}` (예: `task-flow-qa`)
6. **호출하는 스킬의 SKILL.md에 에이전트 탐색 경로 명시** (3-플랫폼 지원):
   ```
   탐색 경로 (우선순위):
   1. {프로젝트}/.cursor/agents/{agent-name}.md
   2. {프로젝트}/.claude/agents/{agent-name}/AGENT.md
   3. {프로젝트}/.agent/skills/{agent-name}/SKILL.md
   4. ~/.cursor/agents/{agent-name}.md
   5. ~/.claude/agents/{agent-name}/AGENT.md
   6. ~/.gemini/antigravity/skills/{agent-name}/SKILL.md
   ```

### Antigravity 컴포넌트 추가 시

Antigravity에서는 에이전트 개념이 없으므로 모든 컴포넌트를 SKILL.md로 작성한다:

1. `antigravity/skills/{skill-name}/SKILL.md` 생성
2. AGENT.md의 `model`, `readonly` 필드는 제거
3. "에이전트" 용어를 "스킬"로 교체
4. 탐색 경로를 Antigravity 전용으로 설정 (`.agent/skills/`, `~/.gemini/antigravity/skills/`)

### 플랫폼별 디렉토리 분리

```
claude/skills/        ← Claude Code 스킬 (소스 원본)
claude/agents/        ← Claude Code 에이전트 (디렉토리 기반)
cursor/skills/        ← Cursor 스킬 (claude/skills/와 동일)
cursor/agents/        ← Cursor 에이전트 (플랫 파일 .md)
antigravity/skills/   ← Antigravity 스킬 (에이전트도 스킬로 통합)
```

**Cursor hooks** 참고: Cursor는 `.cursor/hooks.json`으로 이벤트 기반 자동화를 지원한다 (예: `afterFileEdit`, `afterFileCreate`). 현재는 SKILL.md 내 명시적 호출 방식을 유지하되, 필요 시 hooks.json으로 전환할 수 있다.

## Core Workflow: task-flow

모든 개발 작업의 중심 5단계 파이프라인:

```
사용자 지시 → [TASK] → [QA] → 사용자 검토
                                    ↓
            [RESEARCH] → [QA] → 사용자 검토
                                    ↓
               [PLAN] → [QA] → 사용자 검토
                                    ↓
               [TODO A+B] → 복잡도 판별
                              ├─ 단순: [QA] → 승인 → [EXECUTE 직접] → [QA] → 완료 보고
                              └─ 복잡: [Planner→Part C] → [QA] → 승인 → [EXECUTE 오케스트레이션] → [Test] → [QA] → 완료 보고
```

**핵심 규칙**: 사용자의 명시적 승인 전까지 코드 생성/수정 금지. 각 단계 산출물 작성 후 QA 에이전트가 1차 검토를 수행한 뒤 사용자에게 보고.

**적응적 실행**: TODO 단계에서 복잡도를 판별하여, 단순 태스크는 메인 에이전트가 직접 실행하고, 복잡 태스크는 Planner가 설계한 토폴로지에 따라 서브 에이전트가 병렬 실행한다.

### 산출물 저장 구조

```
tasks/{NNN}-{kebab-case-task-name}/
├── TASK.md           작업 정의서
├── QA-TASK.md        TASK QA 리뷰
├── RESEARCH.md       분석 결과
├── QA-RESEARCH.md    RESEARCH QA 리뷰
├── PLAN.md           구현 계획
├── QA-PLAN.md        PLAN QA 리뷰
├── TODO.md           실행 체크리스트 + QA (+ Part C 복잡 모드)
├── QA-TODO.md        TODO QA 리뷰
├── QA-EXECUTE.md     EXECUTE QA 리뷰
├── TEST-REPORT.md    테스트 리포트 (복잡 모드)
└── skills/           동적 생성 스킬 (복잡 모드, 필요 시)
```

태스크 폴더명에 3자리 순번을 접두사로 붙인다 (예: `001-user-auth-implementation`). 새 태스크 생성 시 `tasks/` 폴더의 기존 최대 번호 + 1, 폴더가 없으면 001부터 시작.

### 작업 유형별 분석 깊이

| 유형 | 트리거 키워드 | RESEARCH 깊이 |
|------|-------------|--------------|
| 신규 개발 | "새로 만들어", "추가해" | 심층 (기술 선택, 아키텍처) |
| 기능 개선 | "개선해", "최적화" | 중간 (현재 구현 + 개선 방안) |
| 오류 수정 | "에러", "버그", "안 돼" | 집중 (원인 분석) |
| 기능 수정 | "변경해", "바꿔" | 중간 (영향 범위 분석) |

## 문서 표준

모든 기술 문서 헤더:

```markdown
# [제목]

> 작성일: YYYY-MM-DD | 작성자: [작성자] | 버전: v{X.Y}
```

하단 변경이력 테이블:

```markdown
| 버전 | 날짜 | 작성자 | 변경내용 |
|------|------|--------|---------|
```

## 버전 관리 규칙

- `v{Major}.{Minor}` 형식
- **Major**: 구조적 변경 (섹션 추가/삭제, 엔티티 신규, 아키텍처 변경)
- **Minor**: 내용 수정 (보강, 오류 수정, 세부 조정)
- 기존 파일 덮어쓰기 금지 — 항상 새 버전 파일 생성
- 이전 버전의 변경이력을 새 버전에 전부 계승

## 단계 완료 보고 형식

```
📋 [{단계명}] 완료 보고

📎 산출물: tasks/{NNN}-{태스크명}/{단계}.md
📎 QA 리뷰: tasks/{NNN}-{태스크명}/QA-{단계}.md

[QA 요약]
- 검증 항목 {N}개 중 {통과}개 Pass, {경고}개 Warning
- {주요 지적 사항 요약}
- 판정: {✅ Pass / ⚠️ Needs Revision}

다음 단계로 넘어갈까요?
```
