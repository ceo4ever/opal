# TASK: Antigravity 플랫폼 지원 추가 및 QA 호출 구조 개선

> 작성일: 2026-03-07 | 작업 유형: 신규 개발 + 기능 개선

## 작업 목표

AI 개발 프레임워크에 Google Antigravity 플랫폼 지원을 추가하고, task-flow의 QA 에이전트 호출 누락 문제를 함께 개선한다.

## 배경

### Antigravity 플랫폼 지원

현재 프레임워크는 Claude Code와 Cursor만 지원한다. Google의 에이전틱 개발 플랫폼 Antigravity(2025.11 발표, 공개 프리뷰 중)에도 프레임워크와 알투(R2)를 적용하고 싶다는 캡틴의 요구가 있다.

Antigravity는 Agent Skills 오픈 표준을 채택하여 SKILL.md 포맷이 Claude Code/Cursor와 동일하다. 다만 Rules 포맷(.md + YAML frontmatter), 디렉토리 구조(.agent/), 에이전트 체계(Manager View UI 기반)에서 차이가 있어 매핑 작업이 필요하다.

### QA 호출 구조 개선

task-flow 스킬에서 각 단계 완료 후 QA 에이전트(task-flow-qa)를 호출해야 하는데, 다른 세션에서 알투가 QA 호출을 건너뛰는 문제가 발견되었다. 원인 분석 결과:

1. **AGENT.md의 "자동 호출" 표현과 실제 명시적 호출 절차의 모순** — 에이전트가 시스템이 자동 처리할 것으로 오해 가능
2. **레퍼런스 가이드(references/*-guide.md)에 QA 호출 언급 없음** — 가이드를 따라가다 QA 호출 지시를 놓침
3. **QA 스킵 방지 장치 부재** — 건너뛰어도 경고가 없음

## 요구사항

### A. Antigravity 플랫폼 지원

- [ ] A-1: Antigravity용 Skills 디렉토리 구성 (`antigravity/skills/`)
  - 기존 6개 스킬(task-flow, api-analyzer, doc-writer, interview, version-mgr, wireframe-builder) 적용
  - Antigravity 스킬 탐색 경로에 맞는 구조: `~/.gemini/antigravity/skills/`
- [ ] A-2: Antigravity용 Agents 적용 방안
  - Antigravity에는 `agents/` 디렉토리 컨벤션이 없음
  - 대안: Skills 내부에서 에이전트 역할 수행 또는 Workflows로 변환
- [ ] A-3: Antigravity용 프로젝트 컨텍스트 템플릿 생성 (`templates/GEMINI.md`)
  - `templates/CLAUDE.md`를 기반으로 Antigravity용 GEMINI.md 템플릿 작성
  - Antigravity에는 `.agent/rules/`가 없으므로 GEMINI.md 단일 파일로 프로젝트 룰 관리
- [ ] A-4: 알투(R2) Antigravity 설정 추가 (`templates/r2/`)
  - GEMINI.md용 알투 스니펫 (`templates/r2/gemini-snippet.md`)
  - 프로젝트 GEMINI.md 또는 글로벌 `~/.gemini/GEMINI.md`에 삽입하는 방식
- [ ] A-5: SKILL.md 내 에이전트 탐색 경로에 Antigravity 경로 추가
  - task-flow 스킬의 QA/Planner/Test 에이전트 탐색 경로에 `.agent/` 경로 추가
- [ ] A-6: 프로젝트 문서 업데이트
  - CLAUDE.md 아키텍처 섹션에 Antigravity 추가
  - README.md에 Antigravity 설치/설정 가이드 추가

### B. Cursor 에이전트 구조 수정

- [ ] B-0: Cursor 에이전트 파일 구조를 플랫 파일 방식으로 변경
  - 현재: `~/.cursor/agents/task-flow-qa/AGENT.md` (디렉토리 기반)
  - 변경: `~/.cursor/agents/task-flow-qa.md` (플랫 파일)
  - 대상: task-flow-qa, task-flow-planner, task-flow-test 3개 에이전트
  - 소스 구조(`cursor/agents/`)도 동일하게 변경
  - SKILL.md 내 에이전트 탐색 경로도 업데이트

### C. QA 호출 구조 개선

- [ ] C-1: 각 레퍼런스 가이드(references/*-guide.md) 끝에 QA 에이전트 호출 단계 추가
  - research-guide.md, plan-guide.md, todo-guide.md, execute-guide.md
- [ ] C-2: AGENT.md(task-flow-qa)의 "자동 호출" 표현을 명시적 호출로 수정
  - "자동 호출됩니다" → "메인 에이전트가 Task 도구로 명시적으로 호출해야 합니다"
- [ ] C-3: SKILL.md 각 STEP의 QA 호출 지시를 별도 서브섹션으로 강조
  - 한 줄 언급이 아닌 눈에 띄는 블록으로 분리

## 제약 조건

- **하위 호환**: 기존 Claude Code/Cursor 사용자에 영향 없어야 함
- **포맷 호환**: Antigravity의 실제 설정 체계(GEMINI.md, .agent/rules/, .agent/skills/)에 정확히 맞아야 함
- **SKILL.md 표준**: Skills는 Agent Skills 오픈 표준(agentskills.io) 포맷 유지
- **소스 원본 유지**: `claude/` 디렉토리가 소스 원본으로서의 역할을 계속 수행
- **Cursor 에이전트 구조 변경 시 Claude Code 구조에 영향 없어야 함**: Claude Code는 기존 디렉토리 기반(`agents/{name}/AGENT.md`) 유지
- **QA 개선이 기존 워크플로우를 깨뜨리지 않아야 함**: 추가/강화만 하고, 기존 절차 변경 금지

## 성공 기준

1. Antigravity에서 `~/.gemini/antigravity/skills/`에 스킬을 배포하면 모든 스킬이 정상 인식됨
2. `.agent/rules/`에 프로젝트 룰을 배포하면 Antigravity가 정상 로딩
3. 알투(R2)가 Antigravity 환경에서도 동일한 페르소나와 기능으로 동작
4. task-flow QA 호출이 레퍼런스 가이드를 따라가도 누락되지 않는 구조
5. Cursor에서 에이전트가 플랫 파일 방식(`~/.cursor/agents/{name}.md`)으로 정상 인식됨
6. 기존 Claude Code 환경에 아무 영향 없음

## 관련 문서

- `claude/skills/task-flow/SKILL.md` — task-flow 스킬 정의 (QA 호출 규칙 포함)
- `claude/agents/task-flow-qa/AGENT.md` — QA 에이전트 정의
- `templates/cursor-rules/` — 기존 Cursor 룰 템플릿 (Antigravity 변환 원본)
- `templates/r2/` — 알투 설정 템플릿
- `CLAUDE.md` — 프로젝트 아키텍처 정의
- `README.md` — 설치/설정 가이드
