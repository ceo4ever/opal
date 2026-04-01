# DONE: Claude Code Hooks 알림 설정 및 install-mac.sh 배포

> 완료일: 2026-03-20 | 모드: Short Task | 작업 유형: 신규

## 완료 요약
Claude Code의 `SubagentStop`/`Stop` hooks로 macOS 네이티브 알림을 보내는 설정 파일을 추가하고, `install-mac.sh`에서 `~/.claude/settings.json`에 자동 머지되도록 배포 파이프라인을 구성했다.

## 변경 파일
| # | 파일 | 변경 내용 |
|---|------|----------|
| 1 | `opal/core/hooks/claude-hooks.json` | (신규) SubagentStop + Stop 이벤트 osascript 알림 설정 |
| 2 | `scripts/install-mac.sh` | `merge_hooks_config()` 함수 추가 + `install_claude()`에 hooks 설치 단계 추가 |

## 핵심 변경 사항
### Before
- Claude Code에 hooks 설정 없음
- 서브에이전트/응답 완료 시 알림 수단 없음

### After
- `SubagentStop`: 서브에이전트 완료 시 macOS 알림 (Glass 사운드)
- `Stop`: 응답 완료 시 macOS 알림 (Glass 사운드)
- `install-mac.sh` [1] Claude Code 또는 [6] 전체 설치 시 자동 배포
- 기존 settings.json의 permissions 등 다른 설정을 보존하면서 hooks만 머지

## 테스트 결과
- JSON 유효성: Pass
- 빈 settings.json 머지: Pass
- 기존 설정 보존 머지: Pass
- bash 문법 검증: Pass

## 산출물 목록
| 파일 | 설명 |
|------|------|
| `tasks/021-claude-code-hooks/TASK.md` | 작업 정의서 |
| `tasks/021-claude-code-hooks/PLAN.md` | 통합 PLAN (코드 분석 + 구현 계획 + 체크리스트) |
| `tasks/021-claude-code-hooks/QA-PLAN.md` | PLAN QA 리뷰 |
| `tasks/021-claude-code-hooks/DONE.md` | 완료 리포트 |
| `opal/core/hooks/claude-hooks.json` | hooks 설정 소스 파일 |
