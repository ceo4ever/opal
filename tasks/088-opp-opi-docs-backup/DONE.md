# DONE: opi docs 백업 기능 추가

- 완료일시: 2026-04-06
- 태스크: tasks/088-opp-opi-docs-backup/

## 변경 파일

| 파일 | 변경 내용 |
|------|----------|
| `opal/skills/opal-project-init/SKILL.md` | `## docs/ 백업 프로토콜` 신규 섹션 + 3곳 참조 삽입 + 변경이력 v3.3 |

## 핵심 결정 사항

- `docs/backup/`은 git에 포함 (캡틴 결정: 백업 파일도 중요 자산)
- 백업 발동 조건: 기존 파일 수정 시만 (신규 생성 제외)
- 중복 방지: 동일 세션 내 같은 파일은 최초 1회만 백업
- 타임존: KST 기준 (AGENT.md 기존 규칙 적용)
