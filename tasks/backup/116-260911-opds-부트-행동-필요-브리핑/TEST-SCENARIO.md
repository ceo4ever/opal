---
template: sdlc-v2
---
# TEST-SCENARIO: 부트스트랩 행동 필요 브리핑

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: macOS 프로젝트 checkout과 `task_116` worktree, Python 3, Bash, Node.js 설치 환경
- 공통 데이터: 진행 중·차단·완료 상태가 섞인 임시 태스크 state.json과 active/candidate/비대상 메모리가 포함된 임시 MEMORY.json
- 대역 사용과 한계: 외부 서비스 대역 없음. 실제 CLI·파일·부트스트래퍼 소스를 실행하고 설치 parity는 감사 스크립트로 확인
- 실행 조건: 자동 실행. 설치 parity 확인은 소스 checkout의 네 플랫폼 부트스트래퍼를 대상으로 수행

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1, AC-3, AC-4, C-1, C-2, C-3, C-5, H-1 | 프로젝트 루트 아래에 in_progress·blocked·done state.json이 있고 worktree 경로에서 실행 | 상태 boot 요약 CLI를 실행하고 결과를 파싱 | 최신 in_progress 또는 blocked 작업 최대 1건의 제목·단계·next_action만 반환하며 done/손상/외부 경로를 제외하고 1024 bytes 이하 유지 | state-tool 실 프로세스 + 임시 fixture unit/integration | 구현 후 |
| S-2 | AC-2, AC-3, AC-4, C-1, C-2, C-3 | MEMORY.json에 candidate, active feedback/issues/improvement, active project/preferences/task, promoted/dead 메모리를 여러 날짜와 동률로 구성 | `memory-tool show --boot-brief`를 실행하고 review_rows와 기존 키를 확인 | review_rows가 candidate→feedback→issues→improvement 순으로 최대 2건 선택되고 동률은 최신·안정 순서이며 기존 index_rows/history_rows와 1024 bytes 계약을 보존 | memory-tool 실 프로세스 + test_boot_brief fixture unit | 구현 전 RED 및 구현 후 |
| S-3 | AC-1, AC-2, AC-3, AC-4, C-2, C-3, C-4, H-2, H-3 | 네 플랫폼 bootstrapper가 정상·부재·실패·disabled·assistant·worker 분기를 모두 포함 | 각 bootstrapper의 명령 순서·조건·출력 블록을 감사하고 bounded 결과를 주입해 실행 | session.project에서만 상태→메모리 순으로 조건부 브리핑이 표시되고, 항목이 없으면 기존 응답이 바이트 동일하며 다른 세션 분기는 변하지 않고 합성 출력이 1024 bytes 이하 | scripts/tests/task113_bootstrap_audit.py + 플랫폼별 shell/text fixture integration | 구현 후·설치 후 |
| S-4 | AC-5, AC-6, C-4 | 소스 변경과 설치 산출물이 존재하고 기존 memory/state/opal-agent 테스트 스위트가 준비됨 | 신규 테스트와 전체 회귀·설치 parity 감사를 실행 | 네 플랫폼 계약이 동일하고 새 미완료/검토 후보 사례와 기존 회귀 테스트가 모두 통과하며 커밋 없이 worktree 변경 목록만 보고됨 | Python unittest, audit script, code-scan/state-tool 검증 | 설치 후·배포 전 |
