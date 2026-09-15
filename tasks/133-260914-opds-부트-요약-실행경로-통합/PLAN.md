---
template: sdlc-v2
---
# PLAN: 부트 요약 실행 경로 통합

> 입력: [TASK.md](TASK.md) (ANALYSIS 없음: opds short)

## Approach

`state-tool boot-summary`가 허브 `tasks/` 직접 태스크와 worktree registry의 canonical `task_path` 태스크를 같은 읽기 전용 후보 목록으로 수집하고, `event-loader project-brief`가 그 목록을 여러 건 렌더링한다. 구현은 프로젝트 소스의 Python 도구와 해당 테스트에 한정하고, `~/.opal/`은 직접 편집하지 않으며 install 이후 source와 installed 결과 동치만 검증한다. code-scan 조회 결과 domain/exports 기준으로 대상 파일을 확인했다.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| D-1. 후보 수집 소유권 | `state-tool boot-summary`는 직접 허브 후보와 registry meta 후보를 합친 `items[]`(최신순, 표시 상한 내)와 `other_count`, `anomalies[]`를 단일 JSON으로 반환한다. 기존 직접-only 프로젝트는 `items[0]` 소비자와 빈 프로젝트 응답을 유지한다. | 기존 구현은 `<root>/tasks`만 순회하고 최대 1건만 반환한다(`opal/tools/state-tool/state_tool.py:2384`, `opal/tools/state-tool/state_tool.py:2431`). Task 116은 이 경로를 read-only bounded 상태 조회로 도입했다(`tasks/116-260911-opds-부트-행동-필요-브리핑/PLAN.md:41`, `tasks/116-260911-opds-부트-행동-필요-브리핑/PLAN.md:42`). |
| D-2. canonical path 소비 | registry 후보는 `.opal-worktrees/.meta/task_*.json`의 `task_path`, `task_folder`, `allocator_root`, `attribution_state`만 소비한다. `task_path`는 반드시 실재 디렉터리의 `state.json`으로 검증하고, cwd나 `.opal-worktrees` 문자열로 태스크 경로를 조립하지 않는다. | worktree 계약은 `task_path == realpath(task_home/tasks/task_folder)` 불변식과 cwd/string 추론 금지를 소유한다(`opal/core/references/harness/worktree.md:53`, `opal/core/references/harness/worktree.md:57`, `opal/core/references/harness/worktree.md:60`). Task 118도 발급원을 먼저 세운 뒤 state-tool/event-loader 소비자가 그 값을 쓰도록 결정했다(`tasks/118-260912-opd-워크트리-태스크-소유권-루트분리/PLAN.md:26`). |
| D-3. dedupe와 이상 노출 | identity는 `task_folder`와 canonical realpath를 함께 본다. active registry 태스크와 허브 사본이 동시에 보이면 정상 후보로 임의 중복하지 않고 canonical 후보 1건과 `task_path_ambiguous` 계열 anomaly를 노출한다. registry meta 누락 필드, `task_path` 소실, broken JSON, active duplicate meta도 `anomalies[]`에 bounded로 노출한다. | active registry와 허브 사본 동시 존재는 자동 선택하지 않는 계약이다(`opal/core/references/harness/worktree.md:61`, `opal/core/references/harness/worktree.md:68`, `opal/core/references/harness/worktree.md:73`). TASK AC-4/AC-5는 중복 사본과 registry/path 이상을 조용히 정상 후보로 오인하지 말라고 요구한다. |
| D-4. active 상태 필터 | state 후보는 `current_status in {"in_progress","blocked"}`와 유효 `updated_at`만 포함한다. `done`, `completed_unmerged`, `additional_work_done`, 필수 필드 누락, 파싱 실패 state는 제외한다. registry meta의 `closed`는 active worktree 후보로 보지 않고 허브 direct 후보 판정에만 맡긴다. | 현행 boot-summary도 `in_progress`/`blocked`와 timestamp만 통과시킨다(`opal/tools/state-tool/state_tool.py:2407`, `opal/tools/state-tool/state_tool.py:2414`). state-tool 완료 상태에는 `completed_unmerged`와 `additional_work_done`이 별도로 존재한다(`opal/tools/state-tool/state_tool.py:104`, `opal/tools/state-tool/state_tool.py:112`). |
| D-5. 렌더링 상한 | `event-loader compose_project_brief`는 `items[]` 최신 2~3건을 렌더하고 남은 건수는 `그 외 N건`으로 표시한다. anomalies가 있으면 상세 경로를 늘어놓지 않고 `경로 이상 N건`처럼 관찰 가능한 한 줄로 제한한다. 최종 Markdown과 `boot-summary` JSON은 각자 UTF-8 1,024바이트 이하를 유지한다. | 현재 `project-brief`는 `items[0]`만 읽는다(`opal/tools/event-loader/event_loader.py:535`, `opal/tools/event-loader/event_loader.py:564`) and 1,024바이트 trim loop를 갖고 있다(`opal/tools/event-loader/event_loader.py:571`). event-loader README도 `project-brief` 1,024바이트 계약을 공개한다(`opal/tools/event-loader/README.md:29`). |
| D-6. 배포 경계 | 소스만 수정하고 installed 검증은 `./scripts/install-mac.sh` 이후 `~/.opal/tools/.../run.sh` 호출로 수행한다. `~/.opal` 파일 직접 편집은 금지한다. | `docs/CONVENTIONS.md`의 배포 경계는 프로젝트 소스 수정 후 install 검증을 요구한다(`docs/CONVENTIONS.md:253`, `docs/CONVENTIONS.md:255`). install은 `opal/tools/`를 `~/.opal/tools`로 배포한다(`scripts/install-mac.sh:1285`). |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. RED-first boot-summary fixture 확장 | opal-test-agent | `opal/tools/state-tool/tests/test_state_tool.py`, `opal/tools/event-loader/tests/test_event_loader_extended.py` | 직접-only, registry-only, 직접+registry 혼합 최신순, canonical 중복 dedupe, registry missing/path-missing/duplicate anomaly, `done`/`completed_unmerged`/`additional_work_done` 제외, 1,024바이트 불변, event-loader `그 외 N건` 렌더를 먼저 실패 테스트로 추가한다. 기존 TestBootSummary 위치와 project-brief 테스트 패턴을 재사용한다(`opal/tools/state-tool/tests/test_state_tool.py:171`, `opal/tools/event-loader/tests/test_event_loader_extended.py:209`). RED 작성자와 W-2/W-3 GREEN 구현자를 분리한다. | 없음 | P1 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, AC-9, C-1, C-2, C-3, C-4, C-5, C-6 |
| W-2. state-tool 통합 수집 구현 | opal-be-agent | `opal/tools/state-tool/state_tool.py` | `collect_boot_summary(project_root)`를 직접 tasks 수집 + registry meta 수집 + canonical dedupe + anomaly bounded 노출 구조로 바꾼다. `items[0]` 호환을 지키며 `other_count`와 `anomalies`만 additive로 추가하고, JSON trim은 title/stage/next_action/anomaly detail까지 포함해 유효 JSON 상태로 1,024바이트를 맞춘다. 현행 parser `boot-summary`/`boot-brief` alias는 유지한다(`opal/tools/state-tool/state_tool.py:2435`, `opal/tools/state-tool/state_tool.py:4171`). | W-1 | P2 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, C-1, C-2, C-3, C-4, C-5, C-6, C-8 |
| W-3. event-loader 다건 렌더 구현 | opal-be-agent | `opal/tools/event-loader/event_loader.py` | `compose_project_brief`가 `items[]` 여러 건과 `other_count`, `anomalies`를 소비하도록 확장한다. 성공한 state/memory 블록만 렌더하는 현행 실패 격리와 `--json` bytes 계약은 유지한다(`opal/tools/event-loader/event_loader.py:525`, `opal/tools/event-loader/event_loader.py:588`, `opal/tools/event-loader/event_loader.py:616`). | W-1, W-2 | P3 | AC-3, AC-5, AC-6, AC-8, AC-9, AC-10, C-1, C-5, C-6 |
| W-4. 공개 도구 설명 정합 | PM 직접 | `opal/tools/state-tool/README.md`, `opal/tools/event-loader/README.md` | README에 direct tasks + registry canonical worktree 통합 조회, `other_count`/`그 외 N건`, anomaly 노출, 1,024바이트 상한을 중복 SSOT가 아닌 도구 공개 계약 수준으로만 반영한다. state-tool README의 소스/배포 경계와 event-loader README의 project-brief 설명을 갱신 대상으로 삼는다(`opal/tools/state-tool/README.md:3`, `opal/tools/state-tool/README.md:22`, `opal/tools/event-loader/README.md:22`, `opal/tools/event-loader/README.md:31`). | W-2, W-3 | P4 | AC-11, C-5, C-7 |
| W-5. 회귀·실환경·설치 검증 | opal-test-agent | `opal/tools/state-tool/tests/test_state_tool.py`, `opal/tools/event-loader/tests/test_event_loader_extended.py`, `opal/tools/state-tool/run.sh`, `opal/tools/event-loader/run.sh`, `scripts/install-mac.sh` | 단위 테스트와 공개 CLI를 실행한 뒤 허브 실환경에서 active registry worktrees task_123/task_127/task_129/task_132와 stale direct hub 109가 동시에 있을 때 source `boot-summary`/`project-brief`가 registry 후보와 `그 외 N건`을 드러내는지 확인한다. 이어 install을 실행하고 installed `~/.opal/tools/state-tool/run.sh` 및 `~/.opal/tools/event-loader/run.sh` 결과가 source 결과와 같은 후보 집합·bytes 상한을 갖는지 비교한다. run.sh wrapper와 install 도구 배포 경로를 검증 대상으로 삼는다(`opal/tools/state-tool/run.sh:1`, `opal/tools/event-loader/run.sh:1`, `scripts/install-mac.sh:1285`). | W-4 | P5 | AC-8, AC-9, AC-10, AC-11, C-5, C-6, C-7, C-8 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. registry anomaly를 후보로 렌더링 | 손상 registry나 active duplicate가 정상 이어보기로 보이면 사용자가 잘못된 태스크를 재개할 수 있다. | 세션 시작 복구가 잘못된 작업본으로 향한다. | W-1/W-2에서 anomaly와 candidate를 분리하고, 정상 후보는 유효 `state.json`과 canonical path가 모두 통과한 경우에만 만든다. |
| H-2. 다건 렌더가 1KB 상한을 깨뜨림 | 여러 태스크와 메모리 review가 함께 길어지면 project-brief 첫 응답 계약이 깨진다. | bootstrap 첫 응답이 OPAL 1,024바이트 계약을 위반한다. | W-2는 JSON 자체를 먼저 줄이고, W-3은 Markdown render loop에서 가장 긴 값부터 줄이되 `그 외 N건`과 anomaly count는 보존한다. |
| H-3. installed 검증이 source와 다른 Python/runtime을 본다 | source CLI는 통과하지만 설치본 `~/.opal` 도구가 이전 계약을 반환할 수 있다. | 실제 세션 브리핑이 개발 검증과 다르게 동작한다. | W-5가 install 후 source→installed 결과 동치를 별도 증거로 닫고, 실패 시 source 변경은 유지하되 배포를 재실행하거나 README 배포 경계를 재확인한다. |

## Release and recovery

- 적용 순서: P1 RED 테스트 → P2 state-tool 구현 → P3 event-loader 렌더 → P4 README 공개 계약 → P5 opal-test-agent 검증과 install parity.
- 검증 범위: `python -m unittest opal/tools/state-tool/tests/test_state_tool.py`, `python -m unittest opal/tools/event-loader/tests/test_event_loader_extended.py`, `bash opal/tools/state-tool/run.sh boot-summary <hub>`, `python opal/tools/event-loader/event_loader.py project-brief --source-root <source> --project-root <hub>`, install 후 대응 installed 명령.
- 실측 경계: source와 installed 모두 UTF-8 1,024바이트 이하, 입력 state/registry/MEMORY 파일 바이트 무변경, 실제 hub의 active worktrees task_123/task_127/task_129/task_132와 stale hub 109가 누락 없이 관찰될 것.
- 실패 시: install 전 실패는 해당 W의 Python/README 변경만 되돌려 재실행한다. install 후 source/installed mismatch는 `~/.opal`을 직접 고치지 않고 `./scripts/install-mac.sh` 재실행 또는 source 배포 경로 수정으로 복구한다.
