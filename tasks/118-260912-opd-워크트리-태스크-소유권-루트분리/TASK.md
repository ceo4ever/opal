---
template: sdlc-v2
---
# TASK: 워크트리 태스크 소유권 — cone 착지 실측과 허브 루트 보정 제거

## Problem

`--worktree` 태스크는 코드를 워크트리에서 수정하고 태스크 문서·상태·로그는 허브에서 수정한다. 하나의 태스크가 두 Git 작업본으로 갈라져, 브랜치만으로는 코드 변경과 실행 증거를 함께 리뷰하거나 복원할 수 없다.

이 분할을 지탱하려고 `.opal-worktrees` 세그먼트를 발견하면 무조건 허브로 보내는 정규화가 네 런타임에 중복 구현돼 있다 — `code-scan.js:338 hubRootFromPath`, `event_loader.py:84 _hub_root`, `brain_tool.py:232 hub_root`, `dashboard/backend/paths.py:hub_root`. 여기에 공유 골든표 `opal/core/references/hub-root-cases.json`과 세 테스트 스위트가 같은 규칙을 다시 소유한다.

보정의 원인은 현재 monorepo sparse cone(`.opal/worktree.json` `repos` 6개 디렉터리)에 `tasks`와 `.opal`이 없다는 결손이다. 그 결과 과거 태스크의 실파일을 인용하는 회귀 테스트가 워크트리에서 구조적으로 실패한다. 또한 `state_tool.py:704 find_project_root`가 "가장 가까운 `.opal/MEMORY.json`" 하나로 태스크 설정 조회와 채번·history 기록을 겸하고 있어, cone을 확장하면 CLOSE가 워크트리 사본에 history를 쓴다.

## Proposed outcome

cone에 `tasks`와 `.opal`을 넣은 상태에서 다섯 root 소비자가 실제로 어디에 착지하는지가 실측 기준선으로 기록된다.

그 위에서 세그먼트 기반 허브 강제 정규화가 활성 계약에서 사라지고, 루트가 용도별 두 개(`task_root`, `allocator_root`)로 분리된다. `worktree-tool create`는 canonical task path와 allocator root를 metadata로 발급하고, 소비자는 cwd에서 경로를 추측하지 않는다. `memory-tool`은 워크트리에서 MEMORY 직접 쓰기를 거부하고 신규 메모리 등록만 index 요청으로 지연한 뒤 허브 finalize에서 1회 반영한다.

비워크트리 실행 결과는 기존과 바이트 동일하다. 실제 태스크 소유권 전환의 운영 활성화(pilot·확산·multi-repo)는 이 태스크에서 수행하지 않는다.

## Affected users and systems

- OPAL PM과 워커: 워크트리 태스크의 경로 해석 계약이 바뀐다.
- 도구: `worktree-tool`, `state-tool`, `memory-tool`, `brain-tool`, `code-scan`, `event-loader`.
- Console: `dashboard/backend/paths.py`, `scanner.resolve_task_dir`, `routers/doctor.py`.
- 규범 문서: `harness/worktree.md`, `harness/task-process.md`, `harness/memory-learning.md`, `harness/observability.md`, `opal-harness.md`, `docs/CONVENTIONS.md`, `docs/PROJECT.md`.
- 제안서: `docs/proposals/opal-worktree-task-ownership.md`, `docs/proposals/opal-task-run-log.md`.
- 범위 제외: Phase 2 monorepo pilot, Phase 3 확산, Phase 4 multi-repo. `opal-pilot-*`의 태스크 생성 순서 전환과 실제 branch merge 귀속 운영도 제외한다.

## Constraints

- C-1: 비워크트리(`--wt` 미사용) 실행의 동작·출력은 변경 전과 바이트 동일해야 한다.
- C-2: `~/.opal/` 배포 파일을 직접 수정하지 않는다. 프로젝트 소스(`opal/`, `skills/`, `agents/`, `scripts/`, `dashboard/`)만 수정하고 install로 배포한다.
- C-3: Phase 0 실측은 disposable Git fixture 또는 명시적 shadow cone에서만 수행한다. 운영 worktree의 기본 cone을 이 태스크에서 일반 활성화하지 않는다.
- C-4: 파이프라인 행 상태 변경은 `state-tool`로만 수행한다. `state.json`·`test-scenario.json` 직접 편집 금지.
- C-5: 현재 active worktree(task_115, task_116과 이 태스크 자신)의 태스크 위치 계약을 실행 중에 자동 이동하지 않는다.
- C-6: 플랫폼 분기를 어댑터 계층 밖에 추가하지 않는다.
- C-7: git 관리 Markdown에 수기 누적 이력 절을 만들지 않는다.
- C-8: 워크트리 안의 상향 탐색 상한을 유지해 `$HOME/.opal`까지 탈출하지 않는다. 제거 대상은 무제한 조상 탐색 방어가 아니라 세그먼트 특례다.

## Acceptance criteria

- AC-1: shadow cone(`tasks`·`.opal` 포함) worktree에서 `.git`, `.opal/AGENT.md`, `.opal/MEMORY.json`, `.opal/brain`, `tasks`의 실체화 여부와 다섯 root 소비자(code-scan·event-loader·brain-tool·state-tool·Console)의 실제 착지 경로가 실측값으로 산출물에 기록된다.
- AC-2: 태스크 107에서 구조적으로 실패했던 `tasks` 실파일 의존 회귀 스위트가 shadow cone에서 재실행되고 새 기준선이 확정된다.
- AC-3: `hubRootFromPath`, `_hub_root`, `brain_tool.hub_root`, `paths.hub_root`와 `hub-root-cases.json`이 활성 코드·테스트·import에서 0건이다(역사 `tasks/` 기록 제외).
- AC-4: `state_tool.find_project_root`가 `task_root` 경로와 명시 `allocator_root` 소비 경로로 분리되고, CLOSE mark가 MEMORY history를 즉시 append하지 않는다.
- AC-5: `worktree-tool create` 응답과 `.opal-worktrees/.meta/task_{NNN}.json`이 `allocator_root`·`task_home`·`task_folder`·`task_path`·`artifact_repo`·`task_ownership_version`을 발급하고, `task_path`가 `task_home/tasks/task_folder`와 동일 `realpath`임이 검증된다.
- AC-6: cone 확장 대상은 `repos`와 분리된 신규 설정 키가 소유하며, multi-repo layout에서는 그 키가 적용되지 않고 `repos`의 독립 저장소 의미가 보존된다.
- AC-7: 허브·워크트리 양쪽에 같은 `task_folder`가 있으면 자동 선택 없이 `task_path_ambiguous`로 차단된다.
- AC-8: `memory-tool`이 워크트리에서 `last_task_number`·`history[]`·`memories[]` 직접 쓰기와 `update/promote/delete/prune`·`*.local.md` 변경을 거부하고, 신규 메모리는 `memory-index-request` 1건으로만 기록된다.
- AC-9: finalize가 title 동등성으로 멱등 판정한다 — 동일 title·file·본문 hash 재실행은 적용 완료, 불일치는 `memory_title_duplicate` 차단.
- AC-10: finalize가 중단 후 재실행될 때 직전 실행이 남긴 미커밋 brain page·index·log 때문에 스스로 차단되지 않고 재개된다(재개 판정 기준이 계약으로 정의되고 fixture로 검증된다).
- AC-11: `memory-index-request`의 처리 완료 상태 저장 위치가 계약으로 정의되고, `worktree-tool remove`의 미처리 요청 거부 가드가 그 위치를 읽어 동작한다.
- AC-12: `.opal-worktrees` 세그먼트 규칙 원문과 그 stale 포인터(`opal-harness.md §2.5 (4)`)가 활성 규범 문서·코드 주석·`@header`에 남지 않고, `harness/worktree.md`가 task/allocator root 계약으로 교체된다.
- AC-13: Phase 1 진입 legacy gate(active legacy worktree 0건 또는 슬롯별 cone·root 회귀 검증 완료)가 규범 문서에 절차로 기재된다.
- AC-14: Console의 task resolver가 hub tasks root와 registry 등록 active task root의 realpath 화이트리스트 밖 경로를 거부하고, `routers/doctor.py`의 입력 경로 리터럴 진단 동작은 유지된다.
- AC-15: 비워크트리 실행의 회귀 증거가 제출된다 — 변경 전후 출력이 바이트 동일함을 실제 실행 결과로 확인한다.
- AC-16: `docs/proposals/opal-worktree-task-ownership.md` §4.2의 `tasks/**` 수치가 실측값(1,114 / Markdown 888)으로 정정되고, 이 태스크에서 확정한 AC-6·AC-10·AC-11 계약이 제안서에 반영된다.
