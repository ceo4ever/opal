# OPAL WorkStudio 제품 개발 방향

> 유형: architecture | 상태: active | 등록: 2026-09-12 23:28 KST
> 결정자: 캡틴

## 결정

- 제품 백로그 SSOT는 `workstudio/BACKLOG.md`가 소유한다.
- 메모리는 기능 목록을 복제하지 않고 백로그 위치, 현재 마일스톤, 장기적인 개발 원칙만 기억한다.
- 기능은 사용자 결과가 완결되는 수직 슬라이스별 개별 태스크로 실행한다.
- 각 태스크의 구체적인 범위와 완료 기준은 시작 전에 캡틴과 대화해 확정한다.

## 현재 MVP

```text
인트로
  → Project 선택 또는 생성
  → PM Agent 등록
  → 실제 Terminal 생성
  → Agent 발동
  → Agent와 대화
```

현재 마일스톤은 `WS-M1 MVP Agent Conversation`이며 첫 실행 후보는 `WS-F101 Project Registry`다.

## Terminal 방향

실제 Terminal은 Orca Terminal 모듈의 PTY 생명주기, resize, scrollback, 프로세스 종료, Agent prompt 전달과 대화/Terminal 보기 분리를 참고한다. Orca 비공개 구현에 직접 결합하지 않고 WorkStudio Electron main이 자체 `TerminalGateway`와 typed preload IPC를 소유한다.
