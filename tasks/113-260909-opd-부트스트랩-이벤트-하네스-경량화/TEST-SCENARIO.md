---
template: sdlc-v2
---
# TEST-SCENARIO: 부트스트랩 이벤트 하네스 경량화

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: macOS worktree `/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_113` 기준으로 소스 검증을 수행한다. 설치 검증은 같은 worktree의 `scripts/install-mac.sh`를 사용한다.
- 공통 데이터: 태스크 폴더의 TASK/PLAN/ANALYSIS와 source tree의 OPAL core, references, tools, skills, agents, bootstrapper, scripts.
- 대역 사용과 한계: Windows는 현재 환경에 `pwsh`가 있으면 실행 검증하고, 없으면 PowerShell 정적 parity 검사로 대체한다. 대체 시 실제 Windows 실행은 별도 환경에서 확인해야 한다.
- 실행 조건: 자동 실행. 단, install-mac은 사용자 전역 `~/.opal` 배포본을 갱신하므로 실행 직전 핵심 파일 해시를 기록한다.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-5, C-3, H-1 | `event-loader` 구현 전 | `event-loader verify`가 없는 receipt, 다른 event id, 변경된 문서 hash를 거부하는 테스트를 먼저 작성해 실행한다. | 구현 전에는 테스트가 실패하거나 실행 불가로 RED가 된다. | unit / worktree Python | 구현 전 RED |
| S-2 | AC-2, C-6 | `memory-tool show --boot-brief` 구현 전 | boot brief가 최대 3개 memory와 1024 bytes 이하를 보장하는 테스트를 먼저 작성해 실행한다. | 구현 전에는 옵션 부재 또는 byte 초과로 RED가 된다. | unit / worktree Python | 구현 전 RED |
| S-3 | AC-3, C-2 | marker precedence 테스트 구현 전 | `[WORKER]`, `[ASSISTANT]`, 무마커, `bootstrap: off` 조합별 session event 판정 테스트를 먼저 작성해 실행한다. | 구현 전에는 event id 판정 부재로 RED가 된다. | unit / worktree Python | 구현 전 RED |
| S-4 | AC-1, AC-2, C-1, C-6 | W-1~W-4 구현 후 | source 기준 declared Eager 목록을 측정하고 일반 비서와 프로젝트 인지 비서 payload/time 측정 명령을 3회 실행한다. | Eager payload가 변경 전 대비 70% 이상 감소하고 30KB 이하이며, `opal-harness.md`, 전체 `opal-pm.md`, 전체 `docs/PROJECT.md`가 부트 목록에 없다. project-aware assistant는 PM을 활성화하지 않고 memory boot brief만 3개·1KB 이하로 사용한다. | integration / shell + event-loader measure | 구현 후 |
| S-5 | AC-3, C-2 | W-1, W-4 구현 후 | marker/session 해석 단위 테스트와 `opal-agent --opal-bootstrap off|assistant` 테스트를 실행한다. | `[WORKER]`가 최우선으로 전역 boot를 스킵하고, `[ASSISTANT]`는 PM 승격만 억제하며, 무마커 프로젝트 감지는 `session.project`로만 끝난다. | unit / Python | 구현 후 |
| S-6 | AC-4, AC-5, C-3, H-1 | W-1, W-5 구현 후 | `event-loader load --event pm.activate`, `pilot.start`, 각 `stage.*`, `worker.dispatch`를 실행하고 receipt를 `verify`한다. 누락 문서·stale receipt·wrong-event fixture도 실행한다. | 각 이벤트는 manifest의 필수 문서 전문과 현재 sha256을 반환한다. 오류 fixture는 non-zero 구조화 JSON으로 진행 거부를 반환한다. | unit + integration / Python CLI | 구현 후 |
| S-7 | AC-6, C-4 | W-3 구현 후 | `opal-harness.md`와 owner 문서들을 정적 검사한다. 금지 구형 본문 잔존, 동일 규칙 원문 복제, 구형 fallback 문구를 검색한다. | `opal-harness.md`는 인덱스/shim만 가지며 원문 규칙은 owner 문서 한 곳에 있다. 규칙 복제와 금지 fallback 검출 0건이다. | static / shell + event-loader static-check | 구현 후 |
| S-8 | AC-7, C-3 | W-5 구현 후 | `[WORKER]` 디스패치 prompt에 `worker.dispatch` receipt가 없는 케이스와 유효 receipt가 있는 케이스를 검사한다. | receipt 없는 worker 요청은 blocked로 반환하도록 문서 계약과 static-check가 탐지한다. 유효 receipt는 주입 문서만 읽는 계약을 유지한다. | static + unit / shell + Python | 구현 후 |
| S-9 | AC-8, C-5 | W-4, W-5 구현 후 | 모든 `opal/skills/opal-pilot-*`와 주요 `opal/agents/*/AGENT.md`에 대해 event-loader 계약 누락 정적 검사를 실행하고, 4개 bootstrapper snippet을 검사한다. | pilot/stage/worker 소비자는 event id 또는 receipt 계약을 가진다. 플랫폼별 차이는 bootstrapper/install adapter에만 있고 event/harness 로직에는 없다. | static / event-loader static-check | 구현 후 |
| S-10 | AC-8, AC-9, C-5, C-7, H-2, H-3 | W-1~W-6 구현 후 | mac install 전 핵심 `~/.opal` 해시를 기록하고 `scripts/install-mac.sh`를 실행한다. source와 installed `events.json`, `event-loader`, 하네스 owner 문서 parity를 검사한다. `pwsh`가 있으면 Windows install script 정적/실행 검사를 함께 수행한다. | mac 설치가 성공하고 정책상 허용된 차이를 제외한 배포 parity가 통과한다. Windows는 실행 또는 정적 parity 결과가 명확히 산출된다. | integration / mac shell, optional pwsh | 설치 후 |
| S-11 | AC-10, C-7, C-8 | W-7 이후 | 변경 전 선측정값과 변경 후 payload/time 측정값, 실행 명령, 반복 횟수, 설치 parity 결과를 TEST에 기록한다. | TEST가 cold-start before/after payload와 시간 결과를 포함하고, 기존 dirty/task112 변경을 건드리지 않은 git status 근거를 포함한다. | manual 기록 + shell 검증 | 구현 후 |
| S-12 | C-8, C-9 | 전체 구현 중 | hub와 worktree git status를 확인하고 태스크 113 범위 외 변경·커밋·merge·worktree 제거·CLOSE 진입 여부를 검사한다. | 기존 dirty와 task112는 보존되고, 소스 변경은 task_113 worktree에만 있다. 커밋·merge·worktree 제거·CLOSE는 수행되지 않는다. | static / git status | 구현 후 |
