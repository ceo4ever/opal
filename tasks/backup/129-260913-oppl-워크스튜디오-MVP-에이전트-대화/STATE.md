# STATE: WorkStudio MVP Agent Conversation

> 최종 갱신: 2026-09-13 01:40:54
> 파이프라인 현황(rows/상태/다음 액션)의 SSOT는 `state.json`입니다.
> 조회: `~/.opal/tools/state-tool/run.sh show <task-path>`

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|
| 1 | 2026-09-13 01:04 | WorkStudio를 user-facing Electron 프로젝트로 분류하고 USER_JOURNEY를 생성한다. | 인트로에서 Agent 대화까지 사용자가 직접 조작·관찰한다. |
| 2 | 2026-09-13 01:04 | 신규 Project는 `.opal/AGENT.md`까지만 초기화하고 Git 초기화는 제외한다. | MVP 여정에 필요한 최소 소유 경계만 닫고 Git 작업은 기존 제외 범위를 유지한다. |
| 3 | 2026-09-13 01:04 | 최초 Agent는 Codex 단일, 대화는 PTY transport + 구조화 adapter로 구성한다. | MVP 지원 표면을 줄이면서 UI가 raw byte stream 해석을 소유하지 않게 한다. |
| 4 | 2026-09-13 01:04 | 앱 종료 시 PTY·Agent를 teardown하고 복원은 WS-M2로 이월한다. | 프로세스 누수 방지를 MVP 완료 계약으로 우선한다. |

## 블로커
없음
