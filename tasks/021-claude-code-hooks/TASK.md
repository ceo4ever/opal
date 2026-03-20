# TASK: Claude Code Hooks 알림 설정 및 install-mac.sh 배포

> 작성일: 2026-03-20 | 작업 유형: 신규

## 작업 목표
DTP 서브에이전트 등 장시간 작업 완료 시 macOS 네이티브 알림을 보내는 Claude Code hooks를 구성하고, install-mac.sh로 배포되도록 한다.

## 배경
DTP 워크플로우에서 서브에이전트(dtp-agent, dtp-qa, dtp-planner, dtp-test)가 백그라운드로 실행될 때, 완료 시점을 알 수 없어 작업 효율이 떨어진다. Claude Code의 hooks 시스템(`SubagentStop`, `Stop` 등)을 활용하여 macOS 알림을 자동으로 보내면 이 문제를 해결할 수 있다.

## 요구사항
- [ ] Claude Code hooks 설정 파일(JSON)을 프레임워크 소스에 추가
- [ ] `SubagentStop` 이벤트로 서브에이전트 완료 시 macOS 알림 (osascript)
- [ ] `install-mac.sh`에서 Claude Code 설치 시 hooks 설정을 `~/.claude/settings.json`에 머지
- [ ] 기존 `~/.claude/settings.json`의 다른 설정(permissions 등)을 보존하면서 hooks만 추가/업데이트

## 제약 조건
- Claude Code 전용 기능 (Cursor, Antigravity에는 해당 없음)
- `~/.claude/settings.json`에 기존 설정이 있을 수 있으므로 덮어쓰기 불가 — 머지 방식 필요
- macOS 환경 (osascript 사용)

## 관련 문서
- `scripts/install-mac.sh` — 기존 설치 스크립트
- Claude Code hooks 공식 문서 (SubagentStop, Stop, Notification 이벤트)
