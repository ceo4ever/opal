# DONE: opi 프로젝트 최신화 (077)

> 완료일: 2026-04-03

## 변경된 문서

| 파일 | 변경 내용 |
|------|---------|
| `docs/ARCHITECTURE.md` | oppd WBS 반영, Global Layer .venv/+tools.md 추가, 배포 모델 opal/tools/ 분리 및 MCP 경로 정확화, 디렉토리 구조 opal/tools/ 하위 항목 추가 |
| `.opal/MEMORY.md` | 작업 히스토리 075, 076, 077 추가 |
| `tasks/077-opi-project-update/TASK.md` | 신규 생성 |

## 핵심 결정 사항

- `opal/tools/`는 `opal/core/`와 별개 소스 경로임을 배포 모델에 명확히 분리
- `~/.opal/.venv/`를 Global Layer 항목으로 공식 등록
- `opal/core/references/tools.md` — 도구 레지스트리 신규 파일, references/ 설명에 반영
- MCP 배포 경로를 플랫폼별로 명확히 구분 (claude mcp add / gemini mcp add / config merge)
