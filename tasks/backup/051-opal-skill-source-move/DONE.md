# DONE: OPAL 전용 스킬 소스 디렉토리 이동

> 완료일: 2026-03-30

## 변경 요약

OPAL 전용 스킬 20개를 `skills/` → `opal/skills/`로 이동하여 소스 구조의 관심사를 분리했다.

## 변경 내용

| 작업 | 상세 |
|------|------|
| git mv 20개 | opal-pilot-* (6), op-dev-* (7), op-task-* (4), opal-*-creator (2), opal-project-init → opal/skills/ |
| install-mac.sh | 주석/라벨 갱신 ("프레임워크 스킬" → "독립 스킬", "OPAL 전용 스킬" → "OPAL 스킬") |
| README.md | 소스 구조를 간소화하고 docs/ARCHITECTURE.md 링크로 대체 |
| docs/ARCHITECTURE.md | Global Layer 스킬 수, 배포 모델 도표, 디렉토리 구조 트리 갱신 |

## 최종 구조

- `skills/` — 독립 스킬 5개 (api-analyzer, interview, ui-designer, web-to-markdown, wireframe-builder)
- `opal/skills/` — OPAL 스킬 24개 (기존 4 + 이동 20)
- `~/.opal/skills/` — 배포본 29개 (변경 없음)

## 변경 불필요 확인

- opal-skills-registry.json: 배포 경로만 참조 → 변경 불필요
- opal-harness.md: 배포 경로만 참조 → 변경 불필요
- skills.md, agents.md: 배포 경로만 참조 → 변경 불필요
- skill-registry.js: 배포 경로만 참조 → 변경 불필요
- CLAUDE.md: 부트스트래퍼만 → 변경 불필요
