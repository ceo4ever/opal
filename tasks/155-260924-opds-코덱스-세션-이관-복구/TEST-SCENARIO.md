---
template: sdlc-v2
---
# TEST-SCENARIO: 코덱스 세션 이관 복구

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- source: task_155, Python: ~/.opal/.venv/bin/python. 테스트 디렉터리는 모듈명 충돌을 피해서 개별 실행한다.
- unit/integration의 terminal 대역은 명시 인자·실패 분기 검증에만 사용한다. 실제 Orca/Codex 기동·신원·소유권은 S-5에서 별도 확인한다.
- 실제 E2E는 기존 Orca task_155 workspace terminal과 격리 runtime fixture를 사용한다. 새 PM, 채번, Git worktree를 만들지 않는다. fixture가 제품 코드의 공개 CLI·lease·registry 경로를 소비하게 한다.
- RED-first 적용: S-1/3/4/9. 독립 검증자가 실제 실패를 확인하고 test-tool에 기록한 뒤 잠근다. 실제 연동이 불가능하면 blocked로 남긴다.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1, C-1 | CODEX_SESSION_ID만 있음 및 공백/누락 | ownership 테스트 test_codex_identity와 공개 status 실행 | 실제 입력 신원 해석, 공백/누락은 미해석, core에 플랫폼 변수 리터럴 없음 | unit/integration | 구현 전 RED |
| S-2 | AC-1, C-1 | OPAL·Claude·Codex 값이 함께 존재 | 우선순위 및 비문자 입력 테스트 | OPAL 우선·기존 Claude 우선순위 보존·payload fallback | unit | 구현 후 |
| S-3 | AC-2, C-5 | 명시 owner와 ambient 신원이 다름 | launcher test_codex_handoff 실행 | 공개 handoff가 명시 ID로 성공, 새 세션 기동 1회 | integration | 구현 전 RED |
| S-4 | AC-2, AC-5, C-5 | handoff 후 기동/receipt 실패 | cancel 호출 및 lease 레코드 검사 | handoff와 같은 ID로 cancel, 허브 lease 복원 | integration | 구현 전 RED |
| S-5 | AC-3, AC-4, AC-6, C-2, C-4, C-6, H-1, H-2, H-3 | 공식 install 후 기존 Orca workspace와 격리 fixture | 실제 Codex 검증 terminal 기동, codex-start/status/heartbeat 실행·증거 저장, terminal 정리 | 수동 OPAL export 없이 native ID 사용, registry worktree_session_owned와 live lease owner 일치, 허브 writer 종료, 실제 terminal receipt 및 결과 존재 | E2E 실제 Orca/Codex | 설치 후 |
| S-6 | AC-3, AC-4, C-2, C-5, H-2 | child ID와 parent ID 및 pending lease | 새 세션 claim·heartbeat, registry 앞/뒤 순서 검사, foreign live owner로 재시도 | child≠hub, generation 증가·heartbeat 갱신, 두 순서 owner 정합, foreign live lease 불변·거부 | integration 및 S-5 실제 관측 | 구현 후 |
| S-7 | AC-5, C-5 | 신원 없음·기동 실패·잘못된 cwd·prompt 실패 | launcher 회귀 및 진단 검사 | preflight 미해석은 상태 불변, 실패 terminal 정확히 1개 정리·hub_owned 원복, cause/adapter/source 이름 관측·ID 원문 불필요 노출 없음 | integration | 구현 후 |
| S-8 | AC-1, AC-6, C-1, C-3 | 기존 Claude 환경 및 payload hook | ownership/launcher/worktree 기존 전체 회귀 실행 | Claude 동작 유지, 훅은 payload-only, 타세션 lease에 쓰지 않음 | unit/integration | 구현 후 |
| S-9 | AC-3, AC-6, C-3, C-4, H-1, H-3 | 부모 OPAL/플랫폼 신원 상속·사용자 command 설정 | session-launch와 codex-start 테스트 및 S-5 실제 실행, 배포 source 비교 | 기동 자식에는 부모 신원 없음, Codex가 자기 native ID 주입, 시작은 실제 ID payload 사용, 사용자 템플릿 보존·정식 설치 패키지/부트 일치 | integration 및 실제 E2E | 구현 전 RED |
