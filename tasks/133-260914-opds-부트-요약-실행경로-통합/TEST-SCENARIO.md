---
template: sdlc-v2
---
# TEST-SCENARIO: 부트 요약 실행 경로 통합

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: Task 133 canonical worktree의 Python 표준 라이브러리 테스트 환경과 허브 `/Volumes/Data/AIStudio/workspace/ai-framework`
- 공통 데이터: 임시 디렉터리에 만든 direct `tasks/*/state.json`, `.opal-worktrees/.meta/task_*.json`, canonical worktree task fixture와 실제 허브의 task 123·127·129·132
- 대역 사용과 한계: 단위 테스트는 임시 registry/state fixture로 파일 경계와 정렬을 결정론 검증하며, 실제 registry 경로 및 source→installed 동치는 S-7에서 별도 확인
- 실행 조건: S-1~S-6·S-8 자동 실행, S-7은 프로젝트 소스 설치 후 허브에서 source/installed 명령 자동 대조

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1, C-1, C-4, C-6 | 임시 허브에 유효한 direct 진행 태스크만 존재하고 입력 파일 바이트를 사전 기록 | `collect_boot_summary`와 `boot-summary` CLI를 실행 | direct 태스크가 이어보기 후보에 포함되고 기존 첫 항목 필드가 유지되며 입력 바이트가 불변 | state-tool unit/CLI, 임시 디렉터리 | 구현 후 |
| S-2 | AC-2, C-1, C-2, C-4 | direct 태스크 없이 registry meta가 실재 canonical `task_path`의 진행 state를 가리킴 | `boot-summary`를 허브 root로 실행 | registry가 발급한 경로의 태스크가 후보에 포함되고 cwd나 경로 문자열 조립 없이 같은 결과가 나옴 | state-tool unit/CLI, 임시 registry/worktree fixture | 구현 전 RED |
| S-3 | AC-3, AC-4, AC-5, C-2, C-3, H-1 | direct와 registry 후보, 동일 `task_folder`의 허브 사본, 누락 필드·소실 경로·중복 active meta를 함께 구성 | 통합 수집을 실행하고 JSON을 검사 | 유효 후보는 `updated_at` 최신순이고 canonical 태스크는 한 번만 나오며 임의 경로 선택 없이 모든 이상이 bounded 진단으로 분리됨 | state-tool unit, 임시 혼합 fixture | 구현 전 RED |
| S-4 | AC-7, C-4, C-6 | `in_progress`·`blocked`와 함께 `done`·`completed_unmerged`·`additional_work_done`, 손상 JSON, 필수 필드 누락 state를 구성 | 통합 수집과 기존 state-tool 회귀 테스트를 실행 | 진행 상태만 후보가 되고 완료·손상 상태는 정상 후보에서 제외되며 `state-tool show` 계약은 회귀하지 않음 | state-tool unit/regression | 구현 후 |
| S-5 | AC-6, AC-8, C-5, H-2 | 표시 상한보다 많은 다국어 장문 태스크와 memory review 블록을 구성하고 입력 파일 바이트를 기록 | `boot-summary` JSON과 `compose_project_brief`/`project-brief` Markdown을 실행 | 최신 복수 항목과 정확한 `그 외 N건`이 보이고 anomaly count가 관찰 가능하며 두 공개 출력이 각각 유효 형식·UTF-8 1,024바이트 이하이고 입력은 불변 | state-tool/event-loader unit+CLI | 구현 전 RED |
| S-6 | AC-9, C-6, C-8 | Task 133 worktree 안에서 구현·신규 fixture가 완료되고 다른 worktree는 미변경 | state-tool, event-loader, worktree 관련 지정 회귀 스위트와 git 변경 범위 검사를 실행 | 신규 혼합 경로 테스트와 기존 테스트가 모두 PASS하고 변경은 PLAN의 대상 및 Task 133 canonical worktree 안으로 제한됨 | unittest/regression + `git status --short` | 구현 후 |
| S-7 | AC-10, C-1, C-5, C-7, H-3 | 실제 허브에 task 123·127·129·132 registry가 있고 stale direct hub 109가 존재하며 source 테스트가 PASS | source `boot-summary`/`project-brief`를 실행하고 `./scripts/install-mac.sh` 후 installed 명령을 같은 허브에 실행해 정규화 결과와 byte 수를 비교 | 두 실행본 모두 worktree 진행 상태를 포함하고 direct 상태도 통합하며 후보 집합·잔여 건수·진단·1,024바이트 상한이 동등함 | 실제 허브 integration, source→install→installed | 설치 후 |
| S-8 | AC-11, C-5, C-7 | 구현과 공개 계약 문서 갱신이 완료됨 | 변경된 README·PROJECT/CONVENTIONS 참조와 source/install diff를 검사 | 도구 설명이 direct+registry canonical 통합 조회를 설명하고 worktree owner 규칙을 복제하지 않으며 `~/.opal` 직접 수정 흔적이 없음 | 문서 diff·정적 검사 | 구현 후 |
