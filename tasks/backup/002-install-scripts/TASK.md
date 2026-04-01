# TASK: 프레임워크 설치 스크립트 작성

> 작성일: 2026-03-08 | 작업 유형: 신규 개발 | 상태: 완료 (소급 정리)

## 작업 목표

AI 개발 프레임워크를 사용자 환경에 설치하는 쉘 스크립트를 OS별로 작성한다. macOS용 우선 구현.

## 배경

001-antigravity-platform-support 태스크에서 Claude Code, Cursor, Antigravity 3개 플랫폼을 지원하게 되었다. 각 플랫폼의 사용자 홈 디렉토리에 skills, agents, R2 페르소나를 설치하는 과정을 자동화할 필요가 있다.

## 요구사항

- [x] `scripts/` 폴더에 macOS용 설치 스크립트 작성
- [x] 4개 설치 대상: Claude Code, Cursor, Antigravity, R2 알투
- [x] 사용자 계정 감지 (whoami) 또는 입력 받기
- [x] 프레임워크 파일 (skills, agents): 기존 있으면 삭제 → 새로 복사
- [x] AI 공용 파일 (CLAUDE.md, GEMINI.md): 마커 기반 R2 섹션 관리 (기존 내용 보존)
- [ ] Linux/Windows용 스크립트 (미구현, 향후 과제)

## 제약 조건

- bash 3.x 호환 (macOS 기본 bash)
- 복사(cp) 방식 (심볼릭 링크 아님)
- Cursor rules (.mdc) 설치 제외 (프로젝트별 관리)

## 산출물

| 파일 | 설명 | 상태 |
|------|------|------|
| `scripts/install-mac.sh` | macOS 설치 스크립트 (~230줄) | ✅ 완료 |

## 설치 매핑

| 플랫폼 | 소스 | 대상 |
|--------|------|------|
| Claude Code | `claude/skills/`, `claude/agents/` | `~/.claude/skills/`, `~/.claude/agents/` |
| Cursor | `cursor/skills/`, `cursor/agents/` | `~/.cursor/skills/`, `~/.cursor/agents/` |
| Antigravity | `antigravity/skills/` | `~/.gemini/antigravity/skills/` |
| R2 (Claude) | `templates/r2/claude-snippet.md` | `~/.claude/CLAUDE.md` (마커 기반 추가) |
| R2 (Cursor) | `templates/r2/000-r2-persona.mdc` | `~/.cursor/rules/` (파일 복사) |
| R2 (AG) | `templates/r2/gemini-snippet.md` | `~/.gemini/GEMINI.md` (마커 기반 추가) |

## R2 마커 방식

```
# === R2 START ===
(R2 페르소나 내용)
# === R2 END ===
```

- 파일 없음 → 마커 + R2 내용으로 새 파일 생성
- 파일 있고 마커 없음 → 끝에 마커 + R2 추가 (기존 보존)
- 파일 있고 마커 있음 → 마커 사이만 교체 (기존 보존)

## 알려진 이슈

- 최초 설치 시 기존 R2 내용이 이미 있으면 중복 발생 가능 (마커 없는 기존 R2 + 마커 있는 새 R2). 기존 R2를 수동 제거하거나, 다음 실행부터는 마커 섹션만 갱신됨.

## 비고

이 태스크는 task-flow 파이프라인을 거치지 않고 직접 구현 후 소급 정리한 건이다. 계획 검토 → 캡틴 승인 → 구현 → 실행 검증까지 완료된 상태.
