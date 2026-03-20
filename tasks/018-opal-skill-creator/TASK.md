# TASK: opal-skill-creator 스킬 생성

> 작성일: 2026-03-20 | 작업 유형: 신규

## 작업 목표

anthropics/skill-creator 커뮤니티 스킬을 실행하여 SKILL.md를 생성한 후, OPAL 프레임워크 규격에 맞게 후처리를 자동으로 수행하는 파이프라인 스킬을 만든다.

## 배경

현재 OPAL 프레임워크에서 새 스킬을 만들려면:
1. skill-creator로 SKILL.md 콘텐츠를 생성하고
2. 수동으로 OPAL 규격(디렉토리 구조, 레지스트리 등록, 버전 태깅, 3플랫폼 배포 등)을 적용해야 한다

이 두 단계를 하나의 스킬로 통합하면, "스킬 만들어줘" 한마디로 끝까지 자동화할 수 있다.

## 요구사항

- [ ] skill-creator의 핵심 프로세스(Capture Intent → Interview → Draft → Test → Evaluate → Iterate → Optimize)를 파이프라인 1단계로 활용
- [ ] skill-creator 완료 후 OPAL 프레임워크 후처리를 자동 수행:
  - [ ] `skills/{name}/` 디렉토리 구조 생성
  - [ ] YAML frontmatter를 OPAL 규격에 맞게 보정
  - [ ] `~/.opal/references/skills.md` 레지스트리 등록
  - [ ] version-mgr 초기 버전(v1.0) 태깅
- [ ] 에이전트 생성이 필요한 경우 `agents/{platform}/` 3플랫폼 템플릿 자동 생성 지원
- [ ] 기존 스킬 수정/개선 시에도 사용 가능 (skill-creator의 improve 플로우 연동)
- [ ] 프레임워크 스킬로 배치 (`skills/opal-skill-creator/SKILL.md`)

## 제약 조건

- skill-creator 커뮤니티 스킬 자체를 수정하지 않는다 (래핑만 한다)
- 기존 스킬 간 의존 관계를 준수한다 (doc-writer, version-mgr)
- 3개 플랫폼(Claude Code, Cursor, Gemini/Antigravity)에서 동작해야 한다

## 관련 문서

- `~/.opal/community-skills/skill-creator/SKILL.md` — skill-creator 커뮤니티 스킬
- `/Volumes/Data/AIStudio/workspace/ai-framework/CLAUDE.md` — 프레임워크 아키텍처 및 새 컴포넌트 작성 가이드
- `~/.opal/references/skills.md` — 스킬 레지스트리
- `/Volumes/Data/AIStudio/workspace/ai-framework/skills/version-mgr/SKILL.md` — 버전 관리 스킬
