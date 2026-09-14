# OPAL WorkStudio Backlog

> 상태: active | 갱신일: 2026-09-12 | 제품 백로그 SSOT

## 1. 제품 목표

여러 OPAL Project의 PM·Worker와 실행 환경을 하나의 Desktop 앱에서 발견하고, 시작하고, 대화하고, 관찰한다.

이 문서는 앞으로 만들 제품 기능의 순서와 상태만 소유한다. 선택된 기능의 요구사항·설계·테스트·구현 결과는 `tasks/{NNN}-.../`가 소유하며, 확정 구현 계약은 필요한 경우에만 `docs/`로 승격한다.

## 2. MVP 사용자 여정

```text
인트로
  → 기존 Project 선택 또는 신규 Project 생성
  → Project의 PM Agent 발견·등록
  → Project cwd에서 Terminal 생성
  → 선택한 Agent 발동
  → Agent와 양방향 대화 수행
```

MVP 완료는 위 흐름이 하나의 실제 Project에서 처음부터 끝까지 연결되고, 핵심 경로에 `simulated` 또는 `not_connected` 경계가 남지 않은 상태를 뜻한다.

### MVP 범위

- 저장 상태가 없을 때 인트로를 표시한다.
- 기존 폴더를 열거나 새 Project 폴더를 만든다.
- `.opal/AGENT.md`를 기준으로 Project PM을 발견·등록한다.
- 등록한 Project를 cwd로 사용하는 실제 PTY Terminal을 생성한다.
- 지원 Agent 하나를 Terminal에서 발동한다.
- 사용자가 메시지를 보내고 Agent 응답을 대화 화면에서 확인한다.
- 취소, 잘못된 경로, Agent 실행 실패, Terminal 종료를 사용자에게 명시한다.

### MVP 제외 범위

- 다중 PM Coordination 자동화
- Worker DAG와 병렬 실행 관리
- 내장 파일 편집기
- Git stage·commit·PR/MR
- 원격 SSH·WSL·컨테이너 Terminal
- 자동 업데이트와 배포 서명

## 3. 상태와 우선순위

### 상태

| 상태 | 의미 |
|---|---|
| `inbox` | 아이디어만 수집됨 |
| `candidate` | 개발 가치가 확인됨 |
| `ready` | 사용자와 범위를 확정하면 시작 가능 |
| `in_progress` | 실행 태스크가 생성됨 |
| `done` | 검증 후 `main` 병합 완료 |
| `deferred` | 의도적으로 보류 |

### 우선순위

| 우선순위 | 기준 |
|---|---|
| `P0` | MVP 경로이거나 다음 기능의 필수 기반 |
| `P1` | 핵심 제품 가치 |
| `P2` | 사용성·운영성 개선 |
| `P3` | 장기 후보 |

## 4. 마일스톤

| ID | 마일스톤 | 사용자 결과 | 상태 | 완료 조건 |
|---|---|---|---|---|
| WS-M0 | Interactive Prototype | 전체 WorkStudio 구조를 체험한다 | `done` | 독립 앱·Project 트리·Coordination·Terminal·Files·인트로 목업 병합 |
| WS-M1 | MVP Agent Conversation | Project를 열고 PM Agent를 발동해 대화한다 | `ready` | MVP 사용자 여정 E2E 통과, 핵심 경로 mock 0 |
| WS-M2 | Session & Coordination | 여러 Task와 PM·Worker 세션을 복원·조율한다 | `candidate` | 세션 복원·실제 상태·Coordination 이벤트 연결 |
| WS-M3 | Files & Git | 변경을 탐색하고 Git 작업을 수행한다 | `candidate` | 실제 Files·diff·stage·commit 연결 |
| WS-M4 | Desktop Product | 안정적으로 설치하고 운영한다 | `inbox` | 패키징·업데이트·장애 복구·보안 점검 |

## 5. Feature Backlog

| ID | 마일스톤 | 기능 | 사용자 결과 | 우선순위 | 상태 | 의존성 | 실행 태스크 |
|---|---|---|---|---|---|---|---|
| WS-F001 | WS-M0 | 독립 WorkStudio 목업 | 전체 제품 구조와 주요 동선을 체험한다 | P0 | `done` | 없음 | `tasks/126-260912-opds-워크스튜디오-독립앱-구축/` |
| WS-F101 | WS-M1 | Project Registry | 등록한 Project와 최근 접근 순서가 재실행 후에도 유지된다 | P0 | `done` | WS-F001 | `tasks/128-260913-opds-워크스튜디오-프로젝트-레지스트리/` |
| WS-F102 | WS-M1 | Project 열기·생성 | 기존 폴더를 열거나 새 Project 폴더를 실제로 만든다 | P0 | `candidate` | WS-F101 | - |
| WS-F103 | WS-M1 | PM Agent 발견·등록 | `.opal/AGENT.md`에서 Project PM을 발견하고 실행 후보로 등록한다 | P0 | `candidate` | WS-F102 | - |
| WS-F104 | WS-M1 | 실제 PTY Terminal | Project cwd에서 실제 shell Terminal을 생성·입력·resize·종료한다 | P0 | `candidate` | WS-F102 | - |
| WS-F105 | WS-M1 | Agent Launcher | 지원 Agent를 선택해 Terminal 세션에서 발동한다 | P0 | `candidate` | WS-F103, WS-F104 | - |
| WS-F106 | WS-M1 | Agent Conversation | 메시지를 전송하고 Agent 응답·진행·종료 상태를 대화 화면에서 확인한다 | P0 | `candidate` | WS-F105 | - |
| WS-F201 | WS-M2 | Workspace 복원 | 마지막 Project·Task·탭·Terminal 세션을 복원한다 | P1 | `candidate` | WS-M1 | - |
| WS-F202 | WS-M2 | OPAL Task 연동 | 실제 Task와 단계 상태를 Project 트리에 표시한다 | P1 | `inbox` | WS-F101 | - |
| WS-F203 | WS-M2 | PM·Worker 상태 | 실제 Agent 실행 상태와 블로커를 표시한다 | P1 | `inbox` | WS-F106, WS-F202 | - |
| WS-F204 | WS-M2 | Coordination 이벤트 | 지시·배정·결정·결과를 실제 이벤트로 표시한다 | P1 | `inbox` | WS-F203 | - |
| WS-F301 | WS-M3 | 실제 파일 탐색 | 등록 Project의 파일을 안전하게 탐색하고 연다 | P1 | `candidate` | WS-F101 | - |
| WS-F302 | WS-M3 | Git status·diff | 실제 변경 파일과 diff를 확인한다 | P1 | `inbox` | WS-F301 | - |
| WS-F303 | WS-M3 | Git stage·commit | 확인 절차를 거쳐 stage와 commit을 수행한다 | P2 | `inbox` | WS-F302 | - |
| WS-F401 | WS-M4 | Desktop 패키징 | 설치 가능한 WorkStudio 앱을 배포한다 | P1 | `inbox` | WS-M1~M3 | - |
| WS-F402 | WS-M4 | 오류 진단·복구 | Terminal·Agent·Project 장애 원인과 복구 방법을 확인한다 | P2 | `inbox` | WS-M1 | - |
| WS-F403 | WS-M4 | 안전한 업데이트 | 기존 상태를 보존하며 새 버전을 적용한다 | P2 | `inbox` | WS-F401 | - |

## 6. Terminal 구현 참조 계약

WS-F104~WS-F106은 Orca Terminal의 사용자 경험과 생명주기 설계를 참고한다. 특정 Orca 내부 구현을 직접 import하거나 비공개 코드를 복사하는 결합은 만들지 않는다.

### 확인된 참조점

- 로컬 Orca `1.4.200`은 실제 PTY 기반으로 `node-pty`를 포함한다.
- 설치본 참조 위치: `/Applications/Orca.app/Contents/Resources/node_modules/node-pty/`
- 플랫폼별 relay에 PTY fd 누수·Windows teardown·console agent 처리를 위한 patch가 존재한다.
- Terminal 보기와 Agent 대화 보기는 분리되며, Agent 미감지·PTY 단절·prompt 전달 실패·종료 상태를 별도 사용자 상태로 표현한다.

### WorkStudio가 자체 소유할 경계

Electron main의 `TerminalGateway`가 PTY 프로세스를 단독 소유하고 Renderer는 typed preload IPC만 사용한다.

```text
create({ projectId, cwd, shell, cols, rows }) → terminalId
write({ terminalId, data })
resize({ terminalId, cols, rows })
interrupt({ terminalId })
close({ terminalId })

event:data({ terminalId, chunk, sequence })
event:status({ terminalId, status })
event:exit({ terminalId, exitCode, signal })
```

필수 원칙:

- `contextIsolation: true`, `nodeIntegration: false`를 유지한다.
- `cwd`는 등록된 Project root로 검증한다.
- Agent 실행 명령은 등록된 Agent adapter가 구성하며 Renderer가 임의 실행 파일을 직접 지정하지 않는다.
- 출력 순서, resize, interrupt, 정상 종료, 비정상 종료, 앱 종료 시 teardown을 검증한다.
- scrollback과 Agent 대화 기록은 PTY byte stream과 분리해 저장한다.
- Orca 참고 구현의 라이선스와 최신 동작은 WS-F104 태스크에서 다시 확인한다.

## 7. 기술 기반 작업

| ID | 기반 작업 | 발동 조건 | 연결 기능 |
|---|---|---|---|
| WS-E101 | Project feature 모듈 분리 | WS-F101 구현 시 | WS-F101~F103 |
| WS-E102 | persisted state schema와 migration | WS-F101 구현 시 | WS-F101, WS-F201 |
| WS-E103 | TerminalGateway typed IPC | WS-F104 구현 전 | WS-F104~F106 |
| WS-E104 | Agent adapter와 launch contract | WS-F105 구현 전 | WS-F103, WS-F105~F106 |

기술 기반 작업은 독립 리팩터링으로 장기화하지 않고, 연결된 사용자 기능 태스크에서 필요한 범위만 수행한다.

## 8. Ready 진입 조건

기능을 `ready`로 전환하려면 다음이 확인돼야 한다.

- 사용자 결과가 한 문장으로 설명된다.
- 포함 범위와 제외 범위가 구분된다.
- 선행 기능과 기술 위험이 확인된다.
- 정상·취소·오류 흐름을 설명할 수 있다.
- 실제 동작을 판정할 검증 시나리오가 있다.

`ready` 기능을 선택하면 캡틴과 범위를 확정한 뒤 개별 OPAL 태스크를 생성하고 `실행 태스크` 열에 연결한다.

## 9. 운영 규칙

- 초기에는 `in_progress` 기능을 하나만 유지한다.
- 새 요구사항은 진행 중 태스크에 즉시 추가하지 않고 먼저 `아이디어 Inbox`에 기록한다.
- 현재 태스크의 완료에 필수인 경우에만 범위를 변경한다.
- `done`은 테스트와 사용자 확인을 거쳐 `main`에 병합된 상태다.
- 완료 항목이 많아지면 마일스톤 단위로 `workstudio/BACKLOG-HISTORY.md`에 이관한다.
- `.opal/MEMORY.json`은 백로그를 복제하지 않고 위치·현재 마일스톤·장기 결정만 기억한다.

## 10. 결정 대기

| ID | 질문 | 관련 기능 | 상태 |
|---|---|---|---|
| WS-D001 | 신규 Project 생성 시 `.opal/`만 만들지 Git 저장소까지 초기화할지 | WS-F102 | 미결정 |
| WS-D002 | MVP에서 첫 지원 Agent를 Codex 하나로 제한할지 | WS-F105 | 미결정 |
| WS-D003 | Agent 대화를 PTY stream 해석으로 시작할지, Agent별 구조화 adapter를 MVP부터 둘지 | WS-F106 | 미결정 |
| WS-D004 | 앱 종료 후 실제 PTY 세션의 생존·복원 범위를 어디까지 지원할지 | WS-F104, WS-F201 | 미결정 |

## 11. 아이디어 Inbox

- Project 즐겨찾기와 정렬
- 다중 창 지원
- Terminal command palette
- 원격 실행 host
- 음성 입력과 알림
