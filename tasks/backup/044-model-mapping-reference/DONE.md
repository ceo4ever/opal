# DONE: 멀티 플랫폼 모델 매핑 참조 문서 + 스킬 적용

> 완료일: 2026-03-29

## 변경 요약

### 신규 생성
- **opal/core/references/opal-model-mapping.md** — 3레벨(light/standard/advanced) + 3플랫폼(Claude/Gemini/OpenAI) 매핑 + 플랫폼 감지 자동 적용 가이드

### 수정
- **opal/core/references/opal-harness.md** — 섹션 6 "Model Mapping" 추가
- **opal/core/AGENT.md** — 부트스트랩 5단계에 모델 매핑 자동 적용 로직 추가 (플랫폼 감지 → 매핑 로드)
- **skills/opal-pilot-dev/SKILL.md** — haiku→light, opus→advanced, sonnet→standard (4곳)
- **skills/opal-pilot-dev-short/SKILL.md** — 동일 전환 (3곳)
- **skills/opal-pilot-dev-wireframe/SKILL.md** — sonnet→standard (2곳)
- **skills/opal-project-pilot/SKILL.md** — opus→advanced, sonnet→standard (2곳)
- **skills/opal-agent-creator/SKILL.md** — model 선택 가이드를 레벨 기반으로 전환
- **agents/opal-task-agent/AGENT.md** — frontmatter + 오버라이드 테이블 전환

### 동기화
- 소스 → `~/.opal/` 배포본 전체 동기화 완료
