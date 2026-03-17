# TASK: OPAL 프로젝트 메모리 시스템 설계

> 작성일: 2026-03-17 | 작업 유형: 신규 개발

## 작업 목표

프로젝트별 `.opal/memory.md` 파일을 통해 프로젝트 기억을 저장하고, 세션 간 연속성을 제공하는 메모리 시스템을 설계한다.

## 배경

현재 OPAL은 세션 간 프로젝트 컨텍스트를 유지하는 자체 메커니즘이 없다:
- Claude Code의 내장 메모리(`~/.claude/projects/.../memory/`)는 플랫폼 종속적이고 OPAL과 독립적
- `{프로젝트}/.opal/AGENT.md`는 프로젝트 구조/규칙만 담고, 동적 학습 내용(패턴, 선호, 이슈 등)은 저장하지 않음
- OPAL AGENT.md의 "기억과 학습" 섹션에서 축적을 명시하지만, 실제 저장소가 정의되지 않은 상태

## 요구사항

- [ ] 프로젝트별 메모리 파일 구조 설계 (`.opal/memory.md` 또는 더 효율적인 구조)
- [ ] 메모리에 저장할 항목 유형 정의 (패턴, 선호, 이슈, 아키텍처 결정 등)
- [ ] 생성 시점 정의 (언제 메모리 파일을 만드는가)
- [ ] 업데이트 시점/트리거 정의 (언제 메모리를 갱신하는가)
- [ ] 클리어/정리 시점 정의 (언제 오래된 메모리를 제거하는가)
- [ ] 크로스 플랫폼 동작 방식 (Claude Code, Cursor, Gemini CLI에서 동일하게 동작)
- [ ] 기존 Claude Code 메모리 시스템과의 관계 정리 (중복 방지)
- [ ] 메모리 읽기/쓰기 메커니즘 (에이전트가 실제로 어떻게 접근하는가)

## 제약 조건

- OPAL 프레임워크의 크로스 플랫폼 원칙 준수 (Claude Code, Cursor, Gemini CLI/Antigravity)
- 기존 `.opal/AGENT.md`, `project-agent.md` 구조와 자연스럽게 통합
- 파일 기반 (별도 DB나 서버 불필요)
- 토큰 효율적 구조 (메모리가 커져도 부트스트랩 시 전체를 읽지 않아도 되는 구조)

## 관련 문서

- `~/.opal/AGENT.md` — 에이전트 코어 (기억과 학습 섹션)
- `~/.opal/skills/project-init/SKILL.md` — 프로젝트 초기화 스킬
- `opal/templates/project-agent.md` — 프로젝트 에이전트 템플릿
- Claude Code 내장 메모리: `~/.claude/projects/{path}/memory/` (참고용)
