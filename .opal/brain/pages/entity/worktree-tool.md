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
related:
- worktree-workspace-isolation-axis
- worktree-slot-existence-to-occupancy-judgment
- state-tool
- git-sync-tool
created: '2026-08-15'
updated: '2026-08-15'
status: draft
---
## 개요

태스크별 코드 작업본을 git worktree로 격리하는 CLI 도구다. OPAL 태스크 파이프라인에 신설된 `--worktree`/`--wt` 워크스페이스 축(→ [[worktree-workspace-isolation-axis]])을 실제로 집행하는 유일한 지점이며, 규칙은 pilot 스킬 산문이 아니라 이 도구가 결정론으로 강제한다.

## 책임 (WHAT)

- 프로젝트가 선언한 `.opal/worktree.json`(`layout`·`repos[]`·`branchTemplate`·`baseBranch`·`copy[]`·`setup[]`·`portOffset` 7키)을 읽어 코드 레포 구성이 다중 레포(multi-repo)인지 단일 모노레포(monorepo)인지 판정한다(`load_config`/`validate_worktree_config`, `opal/tools/worktree-tool/worktree_tool.py:153,174`).
- `create`는 대상 슬롯(`{프로젝트}/.opal-worktrees/task_{NNN}/`)에 유형별 방식(다중 `git worktree add` 또는 `sparse-checkout`)으로 작업본을 만들고, base-ref를 1회 해석해 메타에 동결 기록하며(`resolve_base_ref`/`_write_meta`, `opal/tools/worktree-tool/worktree_tool.py:256,390`), 의존성 설치는 실행하지 않고 열거만 한다(lazy setup).
- `remove`는 dirty→unpushed→미머지 순서의 3중 가드(`check_guards`, `opal/tools/worktree-tool/worktree_tool.py:466`)를 통과해야 슬롯을 회수하며, 브랜치는 보존한다.
- `.gitignore` 멱등 보장(`ensure_gitignore_entry`, `worktree_tool.py:272`), 캐시 볼륨 불일치(`diagnose_cache_volume`, `worktree_tool.py:297`), code-scan exclude 누락(`diagnose_code_scan_exclude`, `worktree_tool.py:324`), 동시 활성 슬롯 수(`diagnose_concurrent_slots`, `worktree_tool.py:343`) 4종을 비차단 경고로 진단한다.
- `list`/`status`는 슬롯 현황을 조회 전용으로 답한다(`cmd_list`/`cmd_status`, `worktree_tool.py:630,660`).

## 설계 배경 (WHY)

- 스키마 검증은 hand-rolled 함수를 채택했다 — `jsonschema`가 `~/.opal/.venv`에 실재하지만 `mcp`의 전이 의존성일 뿐 `requirements.txt`에 선언돼 있지 않아, 직접 쓰려면 런타임 계약을 확장해야 하고 이는 이번 요구사항 대비 과하다(근거: task:092 PLAN §1.4 DEC-4).
- `create` 부분 실패는 도구 계층(all-or-nothing 롤백)과 파이프라인 계층(비차단 계속)으로 책임을 분리했다 — 태스크 폴더는 이미 사용자 승인 산출물이라 자동 삭제하지 않는다(근거: task:092 PLAN §1.4 DEC-2).
- base-ref를 `remove` 시점에 재조회하지 않고 `create` 시점 1회 해석으로 동결한 것은, 재조회 시 그 사이 프로젝트 기본 브랜치가 바뀌면 미머지 판정이 뒤집혀 비결정론이 되기 때문이다(근거: task:092 PLAN §1.4 DEC-3).
- 슬롯·브랜치 판정 기준을 "존재"에서 "점유"로 바꾼 것은 실환경 결함 대응이다 — 상세 경위와 근거는 [[worktree-slot-existence-to-occupancy-judgment]]로 분리했다.

## 관계 (HOW)

- 오케스트레이터 공통 후처리 스텝 4.5(TASK 완료 직후 훅)가 `create`를 호출하고, 결과를 `state-tool init --worktree`가 영속화한다 — [[state-tool]].
- `opal-pilot-dev`(opd) CLOSE 단계가 `remove` 실행을 안내한다(pilot 10종 중 유일하게 이 도구를 언급하는 지점).
- 도구 골격(`ERROR_CODES`/`ok_response`/`err_response`/`_run_git` 리스트 인자 방식)은 [[git-sync-tool]]을 그대로 계승했다.
- 워크스페이스 축의 설계 원칙 전반은 [[worktree-workspace-isolation-axis]] 참조.

## 소스 커버리지

| 식별자 | 경로:줄번호 | 설명 |
|--------|-----------|------|
| `ERROR_CODES` | `opal/tools/worktree-tool/worktree_tool.py:31` | 18종 에러 코드 카탈로그 |
| `validate_worktree_config` | `opal/tools/worktree-tool/worktree_tool.py:174` | 7키 설정 검증(첫 위반 즉시 반환) |
| `_worktree_entries` / `_dest_registered` / `_branch_occupied` | `opal/tools/worktree-tool/worktree_tool.py:106,124,134` | DEC-7 점유 판정 3함수 |
| `resolve_base_ref` | `opal/tools/worktree-tool/worktree_tool.py:256` | base-ref 1회 해석(우선순위 3단) |
| `check_guards` | `opal/tools/worktree-tool/worktree_tool.py:466` | `remove` 3중 가드(dirty→unpushed→unmerged) |
| `cmd_create` / `cmd_remove` | `opal/tools/worktree-tool/worktree_tool.py:494,709` | 서브명령 진입점 |
| `diagnose_cache_volume` / `diagnose_code_scan_exclude` / `diagnose_concurrent_slots` | `opal/tools/worktree-tool/worktree_tool.py:297,324,343` | 비차단 진단 3종 |

## 관련 페이지

- [[worktree-workspace-isolation-axis]]
- [[worktree-slot-existence-to-occupancy-judgment]]
- [[state-tool]]
- [[git-sync-tool]]
