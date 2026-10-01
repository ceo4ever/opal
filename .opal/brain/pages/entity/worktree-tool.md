---
type: entity
title: worktree-tool
module: <code-scan @header module>
layer: <code-scan @header layer>
domain: <code-scan @header domain>
exports: []
source_ref: '<코드 파일 경로 — 예: opal/tools/state-tool/state_tool.py>'
header_synced: <YYYY-MM-DD>
tags:
- tool
- workspace
- git
- pipeline
sources:
- task:092
- task:118
- task:119
- task:164
- task:169
related: [worktree-workspace-isolation-axis, worktree-slot-existence-to-occupancy-judgment, worktree-task-root-allocator-root-split, state-aware-path-resolution-unblocks-merge, switch-first-plumbing-later-verification, state-tool, git-sync-tool, worktree-close-brain-write-contract]
created: '2026-08-15'
updated: '2026-10-01'
status: draft
---
## 개요

태스크별 코드 작업본을 git worktree로 격리하는 CLI 도구다. OPAL 태스크 파이프라인에 신설된 `--worktree`/`--wt` 워크스페이스 축(→ [[worktree-workspace-isolation-axis]])을 실제로 집행하는 유일한 지점이며, 규칙은 pilot 스킬 산문이 아니라 이 도구가 결정론으로 강제한다.

## 책임 (WHAT)

- 프로젝트가 선언한 `.opal/worktree.json`(`layout`·`repos[]`·`branchTemplate`·`baseBranch`·`copy[]`·`setup[]`·`portOffset` 7키)을 읽어 코드 레포 구성이 다중 레포(multi-repo)인지 단일 모노레포(monorepo)인지 판정한다(`load_config`/`validate_worktree_config`, `opal/tools/worktree-tool/worktree_tool.py:153,174`).
- `create`는 대상 슬롯(`{프로젝트}/.opal-worktrees/task_{NNN}/`)에 유형별 방식(다중 `git worktree add` 또는 `sparse-checkout`)으로 작업본을 만들고, base-ref를 1회 해석해 메타에 동결 기록하며(`resolve_base_ref`/`_write_meta`, `opal/tools/worktree-tool/worktree_tool.py:256,390`), 의존성 설치는 실행하지 않고 열거만 한다(lazy setup).
- registry 메타는 태스크마다 전용 폴더(`.opal-worktrees/.meta/task_{NNN}/meta.json`)에 두고, 메타 쓰기의 lock과 원자 쓰기 임시 파일도 그 폴더 안에서만 만든다. 경로는 도구 안의 계산 함수 하나로만 만든다(`_meta_dir`/`_meta_path`, `opal/tools/worktree-tool/worktree_tool.py:939,944`). 이전 구조의 평면 메타 파일은 읽지도 옮기지도 않는다.
- `remove`가 성공하면 태스크 메타 폴더 전체를 회수하고 `.meta/` 루트는 남긴다. 회수에 실패하면 폴더를 보존하고, 폴더 삭제만 실패하면 회수 성공 판정은 유지한 채 경고로 보고한다.
- `remove`는 미처리 메모리 색인 요청을 먼저 거부한 뒤 dirty→unpushed→미머지 순서의 3중 가드(`check_guards`, `opal/tools/worktree-tool/worktree_tool.py:466`)를 통과해야 슬롯을 회수하며, 브랜치는 보존한다. 정규 경로 해석기는 호출하지 않는다.
- `.gitignore` 멱등 보장(`ensure_gitignore_entry`, `worktree_tool.py:272`), 캐시 볼륨 불일치(`diagnose_cache_volume`, `worktree_tool.py:297`), code-scan exclude 누락(`diagnose_code_scan_exclude`, `worktree_tool.py:324`), 동시 활성 슬롯 수(`diagnose_concurrent_slots`, `worktree_tool.py:343`) 4종을 비차단 경고로 진단한다.
- `list`/`status`는 슬롯 현황을 조회 전용으로 답한다(`cmd_list`/`cmd_status`, `worktree_tool.py:630,1071`). 상태 조회는 정규 태스크 경로를 해석해 그 경로와 출처를 함께 보고한다(`worktree_tool.py:1074`).
- 정규 태스크 경로 해석은 귀속 진행 상태에 의존한다 — 귀속이 아직 진행 중인 세 경우에는 워크트리 사본이 정규이고 허브에 같은 이름의 폴더가 동시에 있으면 자동 선택 없이 차단하며, 병합 확인 뒤 종결된 경우에만 허브의 병합 사본을 정규로 반환한다(`worktree_tool.py:1035`, `:1062-1063`). 배경은 [[state-aware-path-resolution-unblocks-merge]].
- `finalize`는 완료 문서가 선언한 학습 후보 집합과 실제로 변경된 브레인·메모리 경로 집합을 대조해 후자가 전자의 부분집합일 때만 관측 경로를 단일 귀속 커밋으로 확정하고, 아니면 위반 경로를 동봉해 거부한다. **이 확정은 merge 전, 워크트리 브랜치 자신에서 일어난다** — `opal-pilot-dev` CLOSE 스텝의 "merge _전_ finalize" 순서가 원래 설계이며, merge는 이미 커밋된 지식·문서·산출물을 그대로 옮기는 단계일 뿐이다(근거: task:169 PLAN D-1·Approach, `opal/skills/opal-pilot-dev/SKILL.md` §CLOSE 5-(a)). 상태는 미병합 → 귀속 대기 → 종결로 전이하며, 종결 상태에서 다시 부르면 커밋 없이 멱등 반환한다(`worktree_tool.py:1411`, `:1426`, `:1454-1455`, `:1541`).
- `init`은 저장소 구조를 탐지해 설정 초안을 만든다 — 자동 생성이 아니라 초안이며, 기존 파일이 있으면 강제 옵션 없이는 손대지 않는다.

## 설계 배경 (WHY)

- 스키마 검증은 hand-rolled 함수를 채택했다 — `jsonschema`가 `~/.opal/.venv`에 실재하지만 `mcp`의 전이 의존성일 뿐 `requirements.txt`에 선언돼 있지 않아, 직접 쓰려면 런타임 계약을 확장해야 하고 이는 이번 요구사항 대비 과하다(근거: task:092 PLAN §1.4 DEC-4).
- `create` 부분 실패는 도구 계층(all-or-nothing 롤백)과 파이프라인 계층(비차단 계속)으로 책임을 분리했다 — 태스크 폴더는 이미 사용자 승인 산출물이라 자동 삭제하지 않는다(근거: task:092 PLAN §1.4 DEC-2).
- base-ref를 `remove` 시점에 재조회하지 않고 `create` 시점 1회 해석으로 동결한 것은, 재조회 시 그 사이 프로젝트 기본 브랜치가 바뀌면 미머지 판정이 뒤집혀 비결정론이 되기 때문이다(근거: task:092 PLAN §1.4 DEC-3).
- 슬롯·브랜치 판정 기준을 "존재"에서 "점유"로 바꾼 것은 실환경 결함 대응이다 — 상세 경위와 근거는 [[worktree-slot-existence-to-occupancy-judgment]]로 분리했다.
- 캡슐 실체화 범위를 선언하는 설정 키는 기본이 빈 목록이고 단일 레포 구성에서만 전개된다(`worktree_tool.py:255`, `:948-952`). 값이 비어 있으면 태스크 해석 루트가 허브로 탈출하므로, 이 키가 루트 소유권 계약을 켜는 유일한 스위치다 (근거: task:119 ANALYSIS Q4) — [[switch-first-plumbing-later-verification]].
- 메타를 태스크별 폴더로 나눈 것은 워크트리 세션에 자기 태스크 메타만 쓰기 권한으로 주기 위해서다. 평면 구조에서는 lock·임시 파일이 `.meta/` 루트에 생겨 루트 전체를 열어야 했고, 그러면 다른 태스크 메타까지 쓸 수 있었다 (근거: task:164 TASK AC-1·C-1).
- 병합 이후에도 수명주기가 닫히도록 정규 경로 해석에 귀속 상태를 더한 것은 태스크 119의 차단급 결함 대응이다 (근거: task:119 PLAN D-1).
- **문서상 "finalize는 merge 후 귀속 후처리를 확정한다"는 서술은 오기였다**: 모듈 @header, `cmd_finalize` docstring, README.md 3곳에 이 표현이 남아 있었으나 실제 로직(`S ⊆ D` 판정·단일 귀속 커밋)과 CLOSE 파이프라인 배선은 항상 "merge 전" 확정이었다. 워크트리 brain 쓰기 가드가 거부돼 왔던 탓에 이 순서가 실제로 작동한 적이 없어 오기가 들키지 않았을 뿐이다 — brain-tool 쓰기 루트 반전으로 이 경로가 처음 실동작하면서 세 문서를 "merge 전 확정"으로 정정했다. `S ⊆ D` 판정 로직·분기·반환값 자체는 바꾸지 않았다(근거: task:169 PLAN D-1·W-7, [[worktree-close-brain-write-contract]] 참조).

## 관계 (HOW)

- 오케스트레이터 공통 후처리 스텝 4.5(TASK 완료 직후 훅)가 `create`를 호출하고, 결과를 `state-tool init --worktree`가 영속화한다 — [[state-tool]].
- `opal-pilot-dev`(opd) CLOSE 단계가 `remove` 실행을 안내한다(pilot 10종 중 유일하게 이 도구를 언급하는 지점). 같은 CLOSE 단계가 merge _전_에 `finalize`를 먼저 호출한다.
- 도구 골격(`ERROR_CODES`/`ok_response`/`err_response`/`_run_git` 리스트 인자 방식)은 [[git-sync-tool]]을 그대로 계승했다.
- 워크스페이스 축의 설계 원칙 전반은 [[worktree-workspace-isolation-axis]] 참조.
- `finalize`가 쓰는 brain 쓰기 경로와 CLOSE 전체 계약은 [[worktree-close-brain-write-contract]] 참조.

## 소스 커버리지

| 식별자 | 경로:줄번호 | 설명 |
|--------|-----------|------|
| `ERROR_CODES` | `opal/tools/worktree-tool/worktree_tool.py:31` | 18종 에러 코드 카탈로그 |
| `validate_worktree_config` | `opal/tools/worktree-tool/worktree_tool.py:174` | 7키 설정 검증(첫 위반 즉시 반환) |
| `_worktree_entries` / `_dest_registered` / `_branch_occupied` | `opal/tools/worktree-tool/worktree_tool.py:106,124,134` | DEC-7 점유 판정 3함수 |
| `resolve_base_ref` | `opal/tools/worktree-tool/worktree_tool.py:256` | base-ref 1회 해석(우선순위 3단) |
| `check_guards` | `opal/tools/worktree-tool/worktree_tool.py:466` | `remove` 3중 가드(dirty→unpushed→unmerged) |
| `cmd_create` / `cmd_remove` | `opal/tools/worktree-tool/worktree_tool.py:494,709` | 서브명령 진입점 |
| `_meta_dir` / `_meta_path` / `_list_task_meta_dirs` | `opal/tools/worktree-tool/worktree_tool.py:939,944,948` | 태스크별 메타 폴더 경로 계산 단일 지점과 새 구조 전건 조회 |
| `_resolve_canonical_task_path` | `opal/tools/worktree-tool/worktree_tool.py:1035` | 귀속 상태 의존 정규 경로 해석(출처 동반 반환) |
| `ATTRIBUTION_STATE_KEY` | `opal/tools/worktree-tool/worktree_tool.py:86` | 귀속 상태 메타 키 |
| `cmd_finalize` | `opal/tools/worktree-tool/worktree_tool.py:1411` | 귀속 확정 서브명령(merge 전, 종결 상태 멱등 반환 `:1426`) |
| `taskCapsuleCone` | `opal/tools/worktree-tool/worktree_tool.py:255,948-952` | 캡슐 실체화 범위 설정(단일 레포 분기 전용, 기본 빈 목록) |
| `diagnose_cache_volume` / `diagnose_code_scan_exclude` / `diagnose_concurrent_slots` | `opal/tools/worktree-tool/worktree_tool.py:297,324,343` | 비차단 진단 3종 |

## 관련 페이지

- [[worktree-workspace-isolation-axis]]
- [[worktree-slot-existence-to-occupancy-judgment]]
- [[worktree-task-root-allocator-root-split]]
- [[state-aware-path-resolution-unblocks-merge]]
- [[switch-first-plumbing-later-verification]]
- [[state-tool]]
- [[git-sync-tool]]
- [[worktree-close-brain-write-contract]]
