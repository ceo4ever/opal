---
template: sdlc-v2
---
# TEST-SCENARIO: 파일럿 전용 스킬 내부화와 Dev Pilot 통합

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: `/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_112`의 `feat/OP-TASK-112` 코드 작업본과 허브 태스크 폴더. Node.js, Python, Bash, Git 사용 가능.
- 공통 데이터: 변경 전 `abbeda6`를 비교 기준으로 사용하고, Full/Short pipeline의 기존 행 수와 key를 회귀 기준으로 사용.
- 대역 사용과 한계: 외부 서비스 대역은 사용하지 않음. 설치 확인은 실제 사용자 `~/.opal/` 대신 임시 HOME 또는 설치 스크립트가 지원하는 격리 경로에서 실행하며, 이것은 현재 사용자 설치본 갱신 증거를 대신하지 않음.
- 실행 조건: 결정론·회귀 검사는 자동 실행. 설치 cleanup 시나리오의 실패 테스트만 구현 전 RED로 실행하고, 나머지는 구현 후 및 격리 설치 후 실행.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1, AC-2, C-4, C-6, H-3 | 구현된 worktree에서 active source/docs만 검사 | 최상위 `opal/skills/op-sdd-{spec,plan,action-plan,verify}` 존재 여부와 활성 `op-sdd-verify/SKILL.md` 참조를 검색하고 opsdd/Action Agent의 내부 경로를 확인 | 네 최상위 폴더 0건, active stale verify 포인터 0건, 세 active 단계와 S-1~S-6 REVIEW 규칙의 내부 경로가 모두 존재 | `find`·`rg` 구조 검사 + `skill-registry validate` | 구현 후 |
| S-2 | AC-3, AC-4, C-1, C-2, H-2 | canonical Dev Pilot과 registry 변경 완료 | registry에 `//opd`를 match하고 Full pipeline을 spec-validate 및 임시 state init | match path가 `opal-pilot-dev/SKILL.md`, profile이 Full로 판정되고 `skill=opd` 16행과 기존 key가 유지 | Node registry CLI + state-tool `spec-validate`/임시 `init` | 구현 후 |
| S-3 | AC-3, AC-4, C-1, C-2, H-2 | S-2와 동일 | registry에 `//opds`를 match하고 Short pipeline을 spec-validate 및 임시 state init | match path가 동일 canonical SKILL, profile이 Short로 판정되고 `skill=opds` 11행과 기존 key가 유지 | Node registry CLI + state-tool `spec-validate`/임시 `init` | 구현 후 |
| S-4 | AC-5, C-3, H-2 | Full/Short profile과 라우팅 SSOT 갱신 완료 | 강등·승격 경계 및 임계 상호배타 회귀 테스트와 active 포인터 검사를 실행 | 강등은 TASK 직후 1회, 승격은 PLAN 결과에서만 동작하고 왕복 재귀 경로와 제거된 Short 폴더 포인터가 0건 | 관련 Node/Python 테스트 + `rg` | 구현 후 |
| S-5 | AC-6, C-1, C-2, C-4 | registry/state 테스트 갱신 완료 | skill-registry validate/match 테스트와 state-tool 전체 관련 테스트를 실행 | shared canonical path의 두 logical alias, 내부 SDD SKILL 비공개 처리, 16/11행 계약을 포함한 관련 테스트 전부 exit 0 | Node 테스트 + `pytest` | 구현 후 |
| S-6 | AC-8, C-5, C-6, H-1 | 임시 설치 루트에 제거 예정 최상위 폴더를 미리 만든 fixture 준비 | 격리 설치 테스트를 실행하고 설치 후 스킬 트리를 검사 | 테스트가 구현 전에는 stale 폴더 잔존 때문에 실패하고, 구현 후에는 canonical Dev Pilot·nested SDD 3종만 배포되며 제거된 최상위 5개 폴더가 0건 | shell 자동화, 임시 HOME/격리 install | 구현 전 RED, 구현 후 |
| S-7 | AC-7, C-6, C-7 | 구조·registry 변경 완료 | README·PROJECT·ARCHITECTURE·CONVENTIONS·시각 SSOT의 active 설명과 실측 top-level skill 수를 대조 | Short는 canonical Pilot profile로, SDD는 내부 단계로 설명되고 수량·경로·alias가 실측과 일치하며 이번 태스크 변경 문서에 수기 누적 이력 절·주석·작성 의무가 0건 | `rg`·`find`·문서 정합 스크립트 | 구현 후 |
| S-8 | AC-6, C-5, C-7, H-4 | 허브 `.opal/worktree.json`의 stale 항목 제거 완료 | worktree-tool 단위 테스트와 별도 임시 프로젝트 create 사례를 실행 | 없는 `memory` repo 때문에 실패하지 않고, 생성 worktree sparse set에 `.opal/`·`tasks/`가 포함되지 않으며 hub state가 단일 사본 | `pytest opal/tools/worktree-tool/tests` + 임시 프로젝트 integration | 구현 후 |
| S-9 | AC-6, C-5, C-7 | 모든 구현과 문서 갱신 완료 | worktree diff와 허브 diff를 경로별로 검사하고 과거 task/brain/dashboard fixture 변경 여부 확인 | 구현은 task_112 worktree에만 존재하고, 허브는 태스크 산출물·MEMORY·worktree 설정만 변경되며 과거 기록/fixture 변경 0건 | `git status --short`, `git diff --name-only`, `git diff --check` | 구현 후 |
