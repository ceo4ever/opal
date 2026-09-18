"""
@header {
  "module": "worktree_tool",
  "layer": "util",
  "domain": "opal-workspace",
  "description": "태스크별 코드 작업본을 git worktree로 격리하는 CLI. `.opal/worktree.json`(multi-repo/monorepo 2유형)을 선언 기반으로 읽어 create/list/status/ownership-set/checkpoint/remove/finalize/init 8서브명령을 제공한다. create의 슬롯·브랜치 판정은 '존재'가 아니라 '점유'다(DEC-7) — 대상 경로가 `git worktree list --porcelain`에 실제 등록돼 있으면 WORKTREE_EXISTS, 브랜치가 다른 worktree에 체크아웃 중이면 BRANCH_EXISTS로 거부하고, 브랜치가 존재하지만 미점유면 `worktree add <path> <branch>` 단일 명령으로 재사용한다(빈 디렉토리 잔존은 차단 사유가 아니다). pre-flight(대상 미점유·repos 경로 실재·git 레포 여부) 전부 통과 후에만 worktree를 생성하고(all-or-nothing), 중간 실패 시 자기 생성물만 롤백한다(DEC-2, 신규 브랜치 경로에만 적용). base-ref는 create 시점에 1회 해석해 `.opal-worktrees/.meta/task_{NNN}.json`(worktree 밖)에 동결 기록하고 remove/status는 그 값만 읽는다(DEC-3, 재해석 없음). create는 canonical task path 6필드(`allocator_root`·`task_home`·`task_folder`·`task_path`·`artifact_repo`·`task_ownership_version`)를 응답과 메타에 additive로 발급하고 불변식 `task_path == realpath(task_home/tasks/task_folder)`를 발급 시점에 검증한다 — `task_folder`는 basename만 허용한다. create는 registry meta와 **같은 발급값 원천**으로 이 6종을 `<worktree_root>/.opal/task-ownership.json`에도 읽기 snapshot 사본으로 내려보내고 status는 누락·불일치 사본을 registry 기준으로 멱등 보강한다(본문 동일이면 파일을 건드리지 않아 연속 호출이 바이트 동일하다) — 워크트리 안에는 `.opal-worktrees`가 없어 소비자가 허브 registry를 탐색으로 찾을 수 없으므로 추론이 아니라 발급으로 해결한다. 이 사본은 `.opal/worktree.json`과 별개 파일이며 `task_ownership_version` 부재 legacy 메타에는 만들지 않는다. 계약 원문은 `opal/core/references/harness/worktree.md`가 소유한다. optional 설정 키 `taskCapsuleCone`(list[str], 기본 `[]`)은 monorepo 분기에서만 `repos`에 이어 sparse-checkout cone에 전개하며 multi-repo 분기에는 적용하지 않는다. multi-repo에서는 optional 키 `task_artifacts.repo`(1차 도입은 예약값 `'.'`=루트 저장소만 허용하고 그 외 값은 TASK_ARTIFACT_REPO_UNSUPPORTED)로 루트 저장소가 태스크 캡슐을 소유한다 — 이때 slot root 자체가 루트 저장소의 worktree이자 `task_home`이고 `artifact_repo`는 `'.'`다. `task_artifacts` 미설정 multi-repo는 위치 필드를 발급하지 않고 `--task-folder`가 명시되면 TASK_ARTIFACT_REPO_MISSING으로 중단한다. create는 부수 효과·소유권 발급 이전에 루트 Git 적격 R-1(루트가 git 저장소)·R-2(`tasks` 추적)·R-3(`.opal/AGENT.md` 추적)·R-4(`.opal/MEMORY.json` 추적)를 **각각** 판정하고(R-1 불만족이면 R-2~R-4는 판정 자체가 불가하므로 `['R-1']`만 보고한다), 판정 순서는 R-1~R-4 → 추적 범위 겹침 → R-5다 — 루트가 `repos[]` 경로를 1파일이라도 추적하면 TASK_ARTIFACT_REPO_OVERLAP, 루트가 `repos[]`를 ignore하지 않으면 violations `['R-5']`를 실은 TASK_ARTIFACT_REPO_INVALID로 거부한다. R-5는 `git check-ignore -q`의 '실효 ignore' 축이며 `--no-index`를 쓰지 않는다 — 추적 중인 경로는 rc=1이 되므로 R-5를 겹침 판정보다 앞에 두면 겹침 위반이 전용 오류에 도달하지 못한다. 루트를 포함한 전 entry 목록은 ordered `plan_entries`(`(rel, git_root, dest)`, 루트가 `'.'`로 먼저 오고 `repos[]`가 뒤따른다) **하나**가 소유하며 pre-flight·base-ref 해석·worktree 생성·메타 `entries`·롤백이 모두 이 목록만 소비한다(생성부가 `repos`를 따로 순회하지 않는다). 생성은 루트 → 자식 순이고 롤백은 생성의 역순(자식 → 루트)이며, multi-repo 롤백은 회수 실패 시 slot을 지워 흔적을 없애지 않고 잔존 entry를 `residual`로 보고한다(monorepo는 무조건 정리한다). `baseBranchOverrides`(`dict[str,str]`, 키는 `repos[]`∪`{'.'}`이며 벗어나면 CONFIG_UNKNOWN_REPO)도 multi-repo 분기 전용이고, `resolve_base_ref`의 `declared` 자리에 값을 넣을 뿐 3단 폴백 순서를 바꾸지 않는다. `init` 초안은 R-1~R-5 전건을 만족할 때만 `task_artifacts`를 제시하고 `baseBranchOverrides`는 추측하지 않는다. multi-repo 캡슐 소유권 경로의 오류 코드는 TASK_ARTIFACT_REPO_INVALID·TASK_ARTIFACT_REPO_UNSUPPORTED·TASK_ARTIFACT_REPO_OVERLAP·CONFIG_UNKNOWN_REPO·WORKTREE_REMOVE_FAILED 5종이다. canonical task path 해석은 registry meta의 `attribution_state`에 의존한다(제안서 §4.3) — active 3상태(키 부재·`completed_unmerged`·`attribution_pending`)에서는 등록된 worktree task path가 canonical이며 허브 `tasks/{task_folder}`가 동시에 실재하면 자동 선택 없이 TASK_PATH_AMBIGUOUS로 차단하고(단일 복사본 불변식), merge 확인 뒤 `closed`에서는 허브에 merge된 사본을 `task_path_source=\"hub_merged\"`로 반환하고 차단하지 않는다. 차단은 active에만 적용되며 가드가 사라진 것이 아니다. `task_ownership_version` 부재 메타는 legacy로 판정을 건너뛰고 해석 결과를 출력에 싣지 않는다. status는 해석된 canonical 경로를 `task_path`·`task_path_source`로 보고하고, finalize는 `closed` 상태에서 커밋 없이 `idempotent: true`로 멱등 반환한다. remove는 해석기를 호출하지 않는다. remove는 미처리 memory index 요청(캡슐 파일 `memory-index-request.json`의 body_sha256 중 메타 `memory_index_requests_resolved`에 없는 건)을 MEMORY_INDEX_REQUEST_PENDING으로 먼저 거부한 뒤 dirty→unpushed→unmerged 순서로 3중 가드를 적용하고 worktree 디렉토리 + 슬롯 루트(`task_{NNN}/`)를 회수한다(브랜치 보존, user sovereignty. `.opal-worktrees/`·`.meta/`는 남긴다). 이 회수 계약은 메타에 동결된 `layout: multi-repo` 분기 **전용**이다 — monorepo·비워크트리는 경로 부재 시 WORKTREE_NOT_FOUND(`--force`면 skip)를 반환하고, 반환값을 검사하지 않는 무조건 회수를 수행한다. multi-repo에서만 entry를 생성의 역순(자식 → 루트)으로 순회하고 **경로 실재 × Git 등록** 2축으로 판정한다 — 둘 다 없으면 이미 회수된 것으로 보고 skip하고(오류가 아니며 `--force`를 요구하지 않는다), 한쪽만 있으면 mismatch(`registration_without_path` 또는 `path_without_registration`)를 실은 WORKTREE_REMOVE_FAILED로 차단·보존하며 자동 복구하지 않는다(`git worktree prune`을 호출하지 않고 미등록 잔여 디렉토리를 삭제하지 않는다). 전 entry의 `git worktree remove`가 성공한 뒤에만 메타와 슬롯 루트를 삭제하고, 하나라도 실패하면 WORKTREE_REMOVE_FAILED로 반환하며 메타·슬롯을 보존해 재시도와 수동 복구 여지를 남긴다. `--force`는 가드 우회에만 적용되며 이 실패 판정을 우회하지 않는다. `.gitignore`·캐시 볼륨·code-scan exclude·동시 슬롯 수는 전부 비차단 진단이다. finalize(PLAN D-3b, 제안서 §6.3)는 merge 후 귀속 후처리를 확정한다 — DONE.md `## 회고적 학습 후보` 선언 집합 D(∪ `.opal/brain/index.md`·`.opal/brain/log.md`·`.opal/MEMORY.json`)와 `git status --porcelain -z -uall`을 `.opal/brain/**`·`.opal/MEMORY.json`으로 필터한 관측 집합 S를 레포 루트 상대 POSIX 경로로 정규화해 대조하고, `S ⊆ D`이면 재개를 허용하고 아니면 ATTRIBUTION_COMMIT_BLOCKED(위반 경로 동봉)로 거부한다. `.opal/MEMORY.json`의 선행 diff는 allocator의 `last_task_number` 변경만 허용한다. 판정 범위 밖(소스·태스크 문서)의 dirty는 판정 대상이 아니며 remove의 이진 dirty 가드(check_guards)는 finalize 경로에서 쓰지 않는다. 관측 경로만 stage해 단일 귀속 commit으로 확정한 뒤 registry meta의 `memory_index_requests_resolved`에 처리한 body_sha256을 append하고 캡슐 파일의 해당 요청 status를 applied로 바꾼다. 상태 전이는 `completed_unmerged → attribution_pending → closed`이고 commit·clean 검증 실패 시 `attribution_pending`에 머문다. init(DEC-8, ADD-1)은 `.opal/worktree.json`을 탐지 기반으로 초안 생성한다(자동 생성이 아니다) — 루트 이하 최대 3 depth에서 독립 `.git` 디렉토리를 찾아 ≥1개면 multi-repo(그 경로들이 repos), 0개면 root 자체가 git 레포일 때만 루트 레포가 추적하는 최상위 디렉토리 중 하위에 코드 manifest를 가진 것을 monorepo repos로 채운다(둘 다 실패하면 LAYOUT_UNDETERMINED). `copy`는 항상 빈 배열·`portOffset`은 항상 0으로 두고 추측하지 않으며(로컬 설정 후보는 `_copy_candidates` 주석 키로만 제시), 기존 파일이 있으면 `--force` 없이는 `CONFIG_EXISTS`로 거부해 파일을 건드리지 않고, `--dry-run`은 쓰지 않고 최상위 `draft` 키로만 반환한다. worktree 실행 lifecycle의 영속 SSOT도 이 registry meta가 소유한다(TASK 138 §Worktree registry SSOT, C-12·C-15) — `execution_ownership` 하위 객체가 `state`(`hub_owned`·`session_launching`·`worktree_session_owned`·`released`)·`owner_session_id`·`adapter`·`adapter_handle`·`generation`·`launch_receipt`·`prompt_receipt`·`failure_reason`·`checkpoint_shas[]`를 canonical 발급 6필드와 분리해 담고, create는 소유권을 발급하는 v2 메타에만 원점(`hub_owned`, generation 0)을 심으며 이미 기록된 블록이 있으면 generation을 잃지 않도록 이어받는다(legacy 메타에는 붙이지 않는다). `ownership-set`은 `execution_ownership`과 `attribution_state` 두 축을 registry lock(`<meta>.lock`, LOCK_EX|LOCK_NB 재시도)과 temp→os.replace 원자 교체 **한 번** 안에서 함께 전이하며, 허용 조합은 `hub_owned`/`session_launching`/`worktree_session_owned` × attribution 키 부재와 `released` × `completed_unmerged`/`attribution_pending`/`closed` 6개뿐이고 나머지는 `ownership_state_invalid`다(CLI에서 attribution 키 부재는 토큰 `active`로 지칭한다). `--launch-receipt`·`--prompt-receipt`는 registry meta에 **객체**로만 기록한다 — argparse 변환자(`type=json.loads`)를 두면 파싱 실패가 usage+exit 2로 새므로 `cmd_ownership_set`이 lock 획득 전에 문자열 인자를 생김새 추론 없이 항상 JSON으로 파싱하며(이미 dict면 그대로, None은 미지정), 파싱 실패와 dict가 아닌 파싱 결과(배열·스칼라)를 모두 `ownership_receipt_invalid` 구조화 오류로 거부한다. `worktree_session_owned`로 진입하는 전이는 prior 상태와 무관하게 `launch_receipt`와 `prompt_receipt`가 둘 다 있을 때만 성공하고(`ownership_receipt_missing`, 메타에 이미 기록된 receipt는 승계되므로 멱등 재설정은 통과한다), `--failure-reason launch_failed`는 `hub_owned` + attribution 키 부재로만 허용되어 generation 증가와 owner·receipt 소거를 같은 교체에 담아 dual writer·orphan owner를 남기지 않는다. `generation`은 단조 증가이며 역행은 `ownership_generation_regressed`다. `ownership-set`과 `status`는 정규형 `--project-root`+`--task` 외에 경로 주소형 `--task-path`를 받는다 — 허브 루트는 자신 포함 조상 중 registry나 `.opal/worktree.json`을 가진 첫 디렉터리이고, 태스크는 registry에 기록된 `task_path`·`worktree_root`·entry 경로와 realpath 동치인 행으로만 찾는다(문자열 접두·mtime·이름 추론 금지, C-6). registry 조회는 대상 디렉터리 존재 검사보다 앞서므로 등록된 행이 가리키는 worktree가 이미 회수돼 사라졌어도 해석에 성공하고, 등록도 없고 디렉터리도 없을 때만 PROJECT_ROOT_NOT_FOUND다. 미등록 경로는 `status`에서 `registered: false`로 통과하고 `ownership-set`은 등록된 행에만 동작해 미등록 경로·미등록 task를 `ownership_task_unregistered`로 거부한다(행도 lock 파일도 만들지 않는다) — registry 행은 `create`만 발급한다. create는 부수 효과 이전에 허브 `.claude/settings.json`을 읽어 워크트리 설정 provisioning 대상을 확정하고(D-8, C-4·C-5), 성공 경로에서 `permissions` 키 **하나만** `<worktree_root>/.claude/settings.local.json`에 내려보낸 뒤 기존 export `ensure_gitignore_entry`로 그 경로를 워크트리 `.gitignore`에 멱등 등록한다 — 원본에 `hooks` 키가 있으면 아무것도 복사하지 않고 `settings_hook_key_forbidden`으로 create를 거부해 워크트리 세션이 허브 Stop evaluator를 물려받는 dual owner를 원천 차단하고, 파일 부재·읽기 실패는 create를 차단하지 않는 no-op이며, `.claude` 디렉터리 복제와 `taskCapsuleCone` 변경은 이 경로에서 하지 않는다. `checkpoint`는 소유 worktree branch의 로컬 체크포인트 커밋 **하나**를 폐쇄 검사 뒤에만 수행한다(TASK 138 C-17~C-20) — 검사 순서는 금지 Git 동작 → 소유권 → branch 일치 → staged scope → 모드 경계다. `--git-command`로 들어온 요청은 예외 없이 `requires_user_approval`이고(merge·push·pull·rebase·reset·revert·cherry-pick·amend·worktree·tag·filter-branch는 `forbidden_git_operation`, 그 밖은 `unsupported_git_command` — 이 서브명령의 수행 범위가 commit 하나뿐이므로 기본 거부다), `main`·`master` 브랜치와 허브 루트 자체에 대한 commit도 같은 코드로 거부한다. 대상은 `--worktree-root`(발급값 사본 `.opal/task-ownership.json`의 `allocator_root`로만 허브에 도달하고 registry에서 realpath 동치 행을 찾는다 — 경로 추론 금지) 또는 `--project-root`+`--task`·`--task-path`로 지정한다. registry 행이 있으면 `execution_ownership.state == worktree_session_owned` + `owner_session_id == OPAL_SESSION_ID`를 요구하고(`checkpoint_ownership_denied`), 현재 branch가 registry `branch`와 다르면 `checkpoint_branch_mismatch`다. staged 경로는 `--owned-scope`(반복 지정, 경로 구분자 경계 판정)를 벗어나면 `checkpoint_scope_violation`이며 미지정이면 worktree 경계 자체가 소유 범위다. 모드 경계는 `agentic`=단계 안정 경계 자율, `interactive`=`--approved`(단계 사용자 승인) 필요, `semi_agentic`=`--approved` + PLAN·CLOSE 계열 단계만이고 EXECUTE·TEST와 미지정 모드는 `checkpoint_mode_denied`다. staged가 0건이면 `checkpoint_nothing_staged`로 커밋하지 않는다. 성공 SHA는 registry lock + `write_meta_atomic` 기존 경로로 `execution_ownership.checkpoint_shas[]`에 append하며(미등록 worktree는 `registered: false`로 이번 커밋만 보고), 커밋은 worktree cwd에서만 수행돼 허브 working tree에 쓰지 않고 공유 objects/refs만 사용한다. git 신원이 없는 환경에서도 결정론적으로 커밋되도록 `commit.gpgsign=false`를 항상 주고 `user.email` 미설정 시에만 fallback 신원을 주입한다. registry meta 쓰기는 create·finalize 경로까지 전부 원자 교체로 통일하되(본문은 종전과 동일한 `ensure_ascii=False, indent=2`) 락은 두 축을 함께 바꾸는 `ownership-set` 구간에서만 잡는다.",
  "exports": [
    "load_config", "validate_worktree_config", "resolve_base_ref", "check_guards",
    "ensure_gitignore_entry", "diagnose_cache_volume", "diagnose_code_scan_exclude",
    "diagnose_concurrent_slots", "registry_lock", "write_meta_atomic",
    "cmd_create", "cmd_list", "cmd_status", "cmd_ownership_set", "cmd_checkpoint",
    "cmd_remove",
    "cmd_init", "cmd_finalize"
  ],
  "depends": ["git CLI 2.25+"]
}
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import json
import os
import pathlib
import posixpath
import shutil
import subprocess
import sys
import time
from datetime import datetime
from typing import NoReturn

# ─────────────────────────────────────────────────────────────────────────────
# 에러 코드 카탈로그 (git_sync_tool.py:23-26 패턴, PLAN §3.2.2)
# ─────────────────────────────────────────────────────────────────────────────
ERROR_CODES = {
    "CONFIG_NOT_FOUND": "'.opal/worktree.json' 설정 파일을 찾을 수 없습니다.",
    "CONFIG_INVALID_JSON": "'.opal/worktree.json' 파일이 유효한 JSON이 아닙니다.",
    "CONFIG_MISSING_KEY": "필수 키가 누락되었습니다.",
    "CONFIG_INVALID_LAYOUT": "'layout' 값이 유효하지 않습니다. 'multi-repo' 또는 'monorepo'만 허용됩니다.",
    "CONFIG_INVALID_TYPE": "설정 값의 타입이 유효하지 않습니다.",
    "CONFIG_PATH_ESCAPE": "경로가 프로젝트 루트를 벗어납니다.",
    "PROJECT_ROOT_NOT_FOUND": "지정한 프로젝트 루트가 존재하지 않습니다.",
    "WORKTREE_EXISTS": "대상 worktree 경로가 이미 존재합니다.",
    "BRANCH_EXISTS": "브랜치가 이미 존재합니다.",
    "REPO_NOT_FOUND": "지정된 repos 경로가 존재하지 않습니다.",
    "NOT_A_GIT_REPO": "지정된 경로가 git 저장소가 아닙니다.",
    "GIT_COMMAND_FAILED": "git 명령이 실패했습니다.",
    "META_NOT_FOUND": "메타 파일을 찾을 수 없습니다. --force로만 우회할 수 있습니다.",
    "WORKTREE_NOT_FOUND": "메타는 있으나 실제 worktree 경로가 존재하지 않습니다.",
    "GUARD_DIRTY": "작업본에 미커밋 변경 사항이 있습니다.",
    "GUARD_UNPUSHED": "원격에 반영되지 않은 커밋이 있습니다.",
    "GUARD_UNMERGED": "base 브랜치에 아직 병합되지 않았습니다.",
    "CONFIG_EXISTS": "'.opal/worktree.json' 파일이 이미 존재합니다. --force로만 덮어쓸 수 있습니다.",
    "LAYOUT_UNDETERMINED": "layout을 결정할 수 없습니다 — 독립 저장소도, manifest를 가진 최상위 디렉토리도 찾지 못했습니다.",
    "TASK_FOLDER_INVALID": "task_folder는 basename만 허용됩니다 — 경로 구분자·'..'·NUL을 포함할 수 없습니다.",
    "TASK_ARTIFACT_REPO_MISSING": "multi-repo layout에서는 태스크 캡슐을 소유할 repo가 결정되지 않아 local task ownership을 활성화할 수 없습니다.",
    "TASK_ARTIFACT_REPO_UNSUPPORTED": "task_artifacts.repo는 1차 도입에서 예약값 '.'(루트 저장소)만 허용됩니다.",
    "TASK_ARTIFACT_REPO_INVALID": "캡슐 소유 루트 저장소가 적격 조건(R-1~R-5)을 만족하지 않습니다.",
    "TASK_ARTIFACT_REPO_OVERLAP": "루트 저장소가 repos[] 경로를 추적하고 있어 worktree 배치가 겹칩니다.",
    "CONFIG_UNKNOWN_REPO": "baseBranchOverrides의 키가 repos[] 또는 '.'와 일치하지 않습니다.",
    "WORKTREE_REMOVE_FAILED": "일부 worktree 회수에 실패했습니다 — 메타와 슬롯을 보존합니다.",
    "TASK_PATH_AMBIGUOUS": "등록된 worktree 태스크와 같은 task_folder가 허브 tasks/에도 존재합니다 — 자동 선택하지 않습니다.",
    "MEMORY_INDEX_REQUEST_PENDING": "처리되지 않은 memory index 요청이 남아 있습니다.",
    "ATTRIBUTION_COMMIT_BLOCKED": "선언되지 않은 귀속 대상 변경이 남아 있어 finalize를 진행할 수 없습니다.",
    "ATTRIBUTION_COMMIT_FAILED": "귀속 commit 생성 또는 clean 검증에 실패했습니다.",
    "TASK_PATH_MISSING": "메타에 canonical task_path가 없어 finalize 대상을 결정할 수 없습니다.",
    "INTERNAL_ERROR": "예상하지 못한 오류가 발생했습니다.",
    # execution ownership 축(TASK.md §Worktree registry SSOT) — 소비자가 문자열을 그대로
    # 비교하므로 소문자 코드를 계약으로 고정한다.
    "ownership_state_invalid": "execution_ownership과 attribution_state가 허용 조합이 아닙니다.",
    "ownership_receipt_missing": "worktree_session_owned로 전이하려면 launch/prompt receipt가 둘 다 필요합니다.",
    "ownership_receipt_invalid": "receipt 인자가 JSON 객체가 아닙니다 — registry meta에는 객체로만 기록합니다.",
    "ownership_generation_regressed": "generation은 단조 증가해야 합니다.",
    "ownership_task_unregistered": "registry에 등록되지 않은 태스크입니다 — 행은 create가 발급합니다.",
    "registry_lock_timeout": "registry 잠금 획득 상한을 초과했습니다.",
    "settings_hook_key_forbidden": "허브 `.claude/settings.json`에 `hooks` 키가 있어 워크트리 설정 provisioning을 중단했습니다 — hook은 워크트리로 복제하지 않습니다.",
    # 체크포인트 커밋 게이트(TASK.md C-17~C-20) — 소유권 축과 같은 소문자 규약이다.
    "checkpoint_scope_violation": "staged 경로가 소유 범위를 벗어납니다 — 체크포인트 커밋을 수행하지 않습니다.",
    "checkpoint_mode_denied": "현재 모드·단계 조합에서는 자율 체크포인트 커밋이 허용되지 않습니다.",
    "checkpoint_ownership_denied": "현재 세션이 이 worktree의 registry 소유자가 아닙니다.",
    "checkpoint_branch_mismatch": "현재 branch가 registry에 기록된 branch와 다릅니다.",
    "checkpoint_nothing_staged": "staged 변경이 없어 체크포인트 커밋할 대상이 없습니다.",
    "requires_user_approval": "사용자 승인 경계의 동작입니다 — 이 서브명령은 수행하지 않습니다.",
}

# 태스크 소유권 계약 버전 (harness/worktree.md §canonical path 발급 계약).
# 이 키가 메타에 없는 태스크는 legacy이며 실행 중 위치를 자동 이동하지 않는다(D-9, TASK.md C-5).
TASK_OWNERSHIP_VERSION = 2

# 태스크 캡슐의 memory index 요청 추적 파일 (PLAN D-2) — {task_path}/ 아래 고정 이름.
MEMORY_INDEX_REQUEST_FILE = "memory-index-request.json"

# finalize 재진입 판정(PLAN D-3b) 상수.
# DONE.md의 선언 절 제목 — 형식 계약 원문은 `harness/done-template.md`가 소유한다.
DONE_FILE = "DONE.md"
LEARNING_CANDIDATE_HEADING = "회고적 학습 후보"
# 선언 없이도 항상 선언 집합 D에 포함되는 귀속 산출물.
ATTRIBUTION_ALWAYS_DECLARED = (
    ".opal/brain/index.md",
    ".opal/brain/log.md",
    ".opal/MEMORY.json",
)
# 관측 집합 S의 판정 범위 — 이 범위 밖(소스·태스크 문서)의 dirty는 판정 대상이 아니다.
ATTRIBUTION_SCOPE_PREFIX = ".opal/brain/"
ATTRIBUTION_MEMORY_FILE = ".opal/MEMORY.json"
# MEMORY.json의 선행 diff에서 허용되는 유일한 변경 키(제안서 §6.3 — allocator 채번).
ATTRIBUTION_MEMORY_ALLOWED_DIFF_KEYS = frozenset({"last_task_number"})
# 귀속 후처리 상태 전이(제안서 §6.3, R-7).
ATTRIBUTION_STATE_KEY = "attribution_state"
ATTRIBUTION_STATE_UNMERGED = "completed_unmerged"
ATTRIBUTION_STATE_PENDING = "attribution_pending"
ATTRIBUTION_STATE_CLOSED = "closed"
ATTRIBUTION_COMMIT_TEMPLATE = "chore(opal): finalize task {task} attribution"

GITIGNORE_ENTRY = ".opal-worktrees/"

# ─────────────────────────────────────────────────────────────────────────────
# 워크트리 설정 provisioning (TASK 138 D-8, C-4·C-5) — permissions 키 **하나만** 옮긴다.
# `hooks`는 어떤 경로로도 내려보내지 않는다: 워크트리 세션이 허브의 Stop evaluator를
# 물려받으면 소유권이 둘로 갈라지기 때문이다(C-5). `.claude` 디렉터리 복제도 금지이며
# `taskCapsuleCone`은 이 경로에서 건드리지 않는다.
# ─────────────────────────────────────────────────────────────────────────────
HUB_SETTINGS_REL = ".claude/settings.json"
WORKTREE_SETTINGS_LOCAL_REL = ".claude/settings.local.json"
SETTINGS_PROVISION_KEY = "permissions"
SETTINGS_FORBIDDEN_KEY = "hooks"

# ─────────────────────────────────────────────────────────────────────────────
# execution ownership 축 (TASK.md §Worktree registry SSOT, C-12·C-15)
# ─────────────────────────────────────────────────────────────────────────────
EXECUTION_OWNERSHIP_KEY = "execution_ownership"
EXEC_STATE_HUB_OWNED = "hub_owned"
EXEC_STATE_SESSION_LAUNCHING = "session_launching"
EXEC_STATE_WORKTREE_SESSION_OWNED = "worktree_session_owned"
EXEC_STATE_RELEASED = "released"

# `attribution_state`의 "키 부재"를 CLI에서 지칭하는 토큰. 저장 시 키를 지운다 —
# harness/worktree.md §상태 의존 해석이 부르는 active 진입 상태다.
ATTRIBUTION_TOKEN_ACTIVE = "active"

# TASK.md §Worktree registry SSOT 표의 6개 파생 단계 조합 — 이 집합 밖은 전부 거부한다.
ALLOWED_OWNERSHIP_COMBOS = frozenset(
    {
        (EXEC_STATE_HUB_OWNED, ATTRIBUTION_TOKEN_ACTIVE),
        (EXEC_STATE_SESSION_LAUNCHING, ATTRIBUTION_TOKEN_ACTIVE),
        (EXEC_STATE_WORKTREE_SESSION_OWNED, ATTRIBUTION_TOKEN_ACTIVE),
        (EXEC_STATE_RELEASED, ATTRIBUTION_STATE_UNMERGED),
        (EXEC_STATE_RELEASED, ATTRIBUTION_STATE_PENDING),
        (EXEC_STATE_RELEASED, ATTRIBUTION_STATE_CLOSED),
    }
)

FAILURE_REASON_LAUNCH_FAILED = "launch_failed"

# registry lock — run_log_core._acquire_lock과 같은 방식(O_CREAT|O_RDWR|O_NOFOLLOW·0o600·
# LOCK_EX|LOCK_NB 재시도)이다. 새 방식을 만들지 않는다.
REGISTRY_LOCK_TIMEOUT_MS = 30000
_LOCK_POLL_INTERVAL_SEC = 0.05


# ─────────────────────────────────────────────────────────────────────────────
# 응답 계약 — git_sync_tool.py:29-42 완전 동형
# ─────────────────────────────────────────────────────────────────────────────


def ok_response(**kwargs):
    payload = {"ok": True, "error": None, **kwargs}
    print(json.dumps(payload, ensure_ascii=False, default=str))


def err_response(code, exit_code=1, **kwargs) -> NoReturn:
    message = ERROR_CODES.get(code, code)
    payload = {"ok": False, "error": code, "message": message, **kwargs}
    print(json.dumps(payload, ensure_ascii=False, default=str))
    sys.exit(exit_code)


# ─────────────────────────────────────────────────────────────────────────────
# git 호출 헬퍼 — 리스트 인자, shell=True 금지(injection 방지)
# ─────────────────────────────────────────────────────────────────────────────


def _run_git(args: list, cwd: pathlib.Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


class GitFailure(Exception):
    """_git_or_raise가 git 명령 실패 시 발생시키는 예외. stderr 원문을 보존한다."""

    def __init__(self, stderr: str):
        self.stderr = stderr
        super().__init__(stderr)


def _git_or_raise(cwd: pathlib.Path, args: list) -> subprocess.CompletedProcess:
    result = _run_git(args, cwd)
    if result.returncode != 0:
        raise GitFailure(result.stderr)
    return result


def _branch_exists(git_root: pathlib.Path, branch: str) -> bool:
    result = _run_git(["branch", "--list", branch], git_root)
    return bool(result.stdout.strip())


def _worktree_entries(git_root: pathlib.Path) -> list:
    """`git worktree list --porcelain` 파싱 (DEC-7 ④). 각 항목:
    {"worktree": <절대경로 str>, "branch": <브랜치명 또는 None(detached)>}."""
    result = _run_git(["worktree", "list", "--porcelain"], git_root)
    entries = []
    current = None
    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            if current is not None:
                entries.append(current)
            current = {"worktree": line[len("worktree ") :], "branch": None}
        elif line.startswith("branch ") and current is not None:
            current["branch"] = line[len("branch ") :].removeprefix("refs/heads/")
    if current is not None:
        entries.append(current)
    return entries


def _dest_registered(git_root: pathlib.Path, dest: pathlib.Path) -> bool:
    """dest가 git_root에 실제 worktree로 등록돼 있는지 판정 — 디렉토리 존재가 아니라
    git이 알고 있는 worktree인지가 기준이다(DEC-7 슬롯 존재 판정 변경: '존재' → '점유')."""
    dest_norm = os.path.normpath(str(dest))
    return any(
        os.path.normpath(e["worktree"]) == dest_norm
        for e in _worktree_entries(git_root)
    )


def _branch_occupied(git_root: pathlib.Path, branch: str) -> bool:
    """branch가 git_root의 어느 worktree에서든 체크아웃(점유) 중인지 판정(DEC-7 브랜치 판정
    변경: '존재' → '점유'). git이 이미 점유 중인 브랜치의 재`add`를 자체 거부하므로(PLAN §1.4
    DEC-7 실측 ③), 이 판정은 그 신호를 사전에 BRANCH_EXISTS로 옮기는 역할을 한다."""
    return any(e["branch"] == branch for e in _worktree_entries(git_root))


# ─────────────────────────────────────────────────────────────────────────────
# config 로더 + 검증 (F-001, PLAN §3.1.3)
# ─────────────────────────────────────────────────────────────────────────────


def _resolve_project_root(raw: str) -> pathlib.Path:
    path = pathlib.Path(raw)
    if not path.is_dir():
        err_response("PROJECT_ROOT_NOT_FOUND", path=str(path))
    return path


def load_config(project_root: pathlib.Path) -> dict:
    """{project_root}/.opal/worktree.json 로드. 부재→CONFIG_NOT_FOUND, 파싱실패→CONFIG_INVALID_JSON."""
    config_path = project_root / ".opal" / "worktree.json"
    if not config_path.is_file():
        err_response("CONFIG_NOT_FOUND", path=str(config_path))
    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        err_response("CONFIG_INVALID_JSON", path=str(config_path))


def _is_inside(project_root: pathlib.Path, rel: str) -> bool:
    """os.path.normpath 후 project_root 하위인지 판정. 심볼릭 링크는 해석하지 않는다
    (경로 문자열 기준 — Path.resolve()/os.path.realpath()를 쓰지 않는다, PLAN §3.1.3)."""
    if os.path.isabs(rel):
        return False
    root_norm = os.path.normpath(str(project_root))
    combined = os.path.normpath(os.path.join(root_norm, rel))
    return combined == root_norm or combined.startswith(root_norm + os.sep)


def validate_worktree_config(cfg: dict, project_root: pathlib.Path) -> dict:
    """검증 통과 시 기본값이 채워진 정규화 dict 반환. 위반 시 err_response로 즉시 종료(exit).

    검증 순서(첫 위반에서 즉시 반환 — 결정론): dict 타입 → 필수 키(layout/repos) →
    layout 유효값 → repos 타입/공백 → repos 경로 이탈 → copy 타입/경로 이탈 →
    taskCapsuleCone 타입/경로 이탈 → branchTemplate/baseBranch 타입 → setup 타입 →
    portOffset 타입.
    """
    if not isinstance(cfg, dict):
        err_response("CONFIG_INVALID_TYPE", key="root")

    if "layout" not in cfg:
        err_response("CONFIG_MISSING_KEY", key="layout")
    if "repos" not in cfg:
        err_response("CONFIG_MISSING_KEY", key="repos")

    layout = cfg["layout"]
    if layout not in ("multi-repo", "monorepo"):
        err_response("CONFIG_INVALID_LAYOUT", value=layout)

    repos = cfg["repos"]
    if (
        not isinstance(repos, list)
        or not repos
        or not all(isinstance(r, str) for r in repos)
    ):
        err_response("CONFIG_INVALID_TYPE", key="repos")
    for rel in repos:
        if not _is_inside(project_root, rel):
            err_response("CONFIG_PATH_ESCAPE", value=rel)

    copy = cfg.get("copy", [])
    if not isinstance(copy, list) or not all(isinstance(c, str) for c in copy):
        err_response("CONFIG_INVALID_TYPE", key="copy")
    for rel in copy:
        if not _is_inside(project_root, rel):
            err_response("CONFIG_PATH_ESCAPE", value=rel)

    # taskCapsuleCone — optional, 기본값 [] (PLAN D-1, harness/worktree.md §cone 확장 계약).
    # 검증 패턴은 copy와 완전 동형이며 신규 에러 코드를 만들지 않는다. 기본값 []의 전개는
    # no-op이라 키 미지정 시 sparse-checkout 인자가 현행과 바이트 동일하다(TASK.md C-1).
    task_capsule_cone = cfg.get("taskCapsuleCone", [])
    if not isinstance(task_capsule_cone, list) or not all(
        isinstance(c, str) for c in task_capsule_cone
    ):
        err_response("CONFIG_INVALID_TYPE", key="taskCapsuleCone")
    for rel in task_capsule_cone:
        if not _is_inside(project_root, rel):
            err_response("CONFIG_PATH_ESCAPE", value=rel)

    # task_artifacts / baseBranchOverrides — **multi-repo 분기 전용**
    # (harness/worktree.md §multi-repo 캡슐 소유권 계약). monorepo는 값이 있어도 읽지 않고
    # 검증하지 않으므로 monorepo 6명령 출력이 변경 전과 바이트 동일하게 유지된다(TASK C-2).
    task_artifacts = None
    base_branch_overrides: dict = {}
    if layout == "multi-repo":
        raw_artifacts = cfg.get("task_artifacts")
        if raw_artifacts is not None:
            if not isinstance(raw_artifacts, dict):
                err_response("CONFIG_INVALID_TYPE", key="task_artifacts")
            if "repo" not in raw_artifacts:
                err_response("CONFIG_MISSING_KEY", key="task_artifacts.repo")
            artifact_repo = raw_artifacts["repo"]
            if not isinstance(artifact_repo, str):
                err_response("CONFIG_INVALID_TYPE", key="task_artifacts.repo")
            # 1차 도입은 예약값 "."(루트 저장소)만 허용한다 — `repos[]` 원소를 캡슐 소유 repo로
            # 쓰려면 canonical resolver의 허브 후보 경로 고정을 먼저 확장해야 한다.
            if artifact_repo != ".":
                err_response(
                    "TASK_ARTIFACT_REPO_UNSUPPORTED",
                    value=artifact_repo,
                    required=".",
                    prerequisite=(
                        "canonical task path 불변식과 resolver의 허브 후보 경로 고정을 "
                        "먼저 확장해야 repos[] 원소를 캡슐 소유 repo로 지정할 수 있습니다."
                    ),
                )
            task_artifacts = {"repo": artifact_repo}

        raw_overrides = cfg.get("baseBranchOverrides", {})
        if not isinstance(raw_overrides, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in raw_overrides.items()
        ):
            err_response("CONFIG_INVALID_TYPE", key="baseBranchOverrides")
        known = set(repos) | {"."}
        unknown = sorted(k for k in raw_overrides if k not in known)
        if unknown:
            err_response("CONFIG_UNKNOWN_REPO", keys=unknown, known=sorted(known))
        base_branch_overrides = dict(raw_overrides)

    branch_template = cfg.get("branchTemplate", "feat/OP-TASK-{NNN}")
    if not isinstance(branch_template, str):
        err_response("CONFIG_INVALID_TYPE", key="branchTemplate")

    base_branch = cfg.get("baseBranch")
    if base_branch is not None and not isinstance(base_branch, str):
        err_response("CONFIG_INVALID_TYPE", key="baseBranch")

    setup = cfg.get("setup", [])
    if not isinstance(setup, list):
        err_response("CONFIG_INVALID_TYPE", key="setup")
    for item in setup:
        if not isinstance(item, dict) or "cwd" not in item or "run" not in item:
            err_response("CONFIG_INVALID_TYPE", key="setup")

    port_offset = cfg.get("portOffset", 0)
    if (
        not isinstance(port_offset, int)
        or isinstance(port_offset, bool)
        or port_offset < 0
    ):
        err_response("CONFIG_INVALID_TYPE", key="portOffset")

    return {
        "layout": layout,
        "repos": repos,
        "branchTemplate": branch_template,
        "baseBranch": base_branch,
        "copy": copy,
        "taskCapsuleCone": task_capsule_cone,
        "setup": setup,
        "portOffset": port_offset,
        # additive — 기존 8키를 제거·개명하지 않는다. 어떤 명령 출력도 cfg를 통째로 싣지 않는다.
        "task_artifacts": task_artifacts,
        "baseBranchOverrides": base_branch_overrides,
    }


def _render_branch(
    template: str, task: str, slug: str | None, skill: str | None
) -> str:
    result = template.replace("{NNN}", task)
    if slug:
        result = result.replace("{slug}", slug)
    if skill:
        result = result.replace("{skill}", skill)
    return result


def resolve_base_ref(git_root: pathlib.Path, declared: str | None) -> str:
    """DEC-3 3단 우선순위, 1곳에 봉인 — create 시점에만 호출한다(remove/status는 메타 값만 사용)."""
    if declared:
        return declared
    result = _run_git(["symbolic-ref", "refs/remotes/origin/HEAD"], git_root)
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip().removeprefix("refs/remotes/")
    result2 = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], git_root)
    return result2.stdout.strip()


# ─────────────────────────────────────────────────────────────────────────────
# create 부수 효과 — .gitignore 멱등 / 캐시 볼륨 / code-scan exclude / 동시 슬롯 (F-007, F-009, DEC-5, DEC-6)
# ─────────────────────────────────────────────────────────────────────────────


def ensure_gitignore_entry(
    project_root: pathlib.Path, entry: str = GITIGNORE_ENTRY
) -> str:
    """루트 .gitignore에 entry를 멱등 보장. 반환: "created" | "added" | "present".

    이미 있으면 파일에 write를 하지 않는다 — 바이트 단위 무변경(TASK F-7 AC).
    """
    gitignore_path = project_root / ".gitignore"
    stripped = entry.rstrip("/")
    if not gitignore_path.exists():
        gitignore_path.write_text(entry + "\n", encoding="utf-8")
        return "created"

    content = gitignore_path.read_text(encoding="utf-8")
    for line in content.splitlines():
        if line.strip() in (entry, stripped):
            return "present"

    if content and not content.endswith("\n"):
        content += "\n"
    content += entry + "\n"
    gitignore_path.write_text(content, encoding="utf-8")
    return "added"


def diagnose_cache_volume(project_root: pathlib.Path) -> list:
    """캐시·프로젝트 볼륨(st_dev) 불일치를 경고 문자열 리스트로 반환. 절대 차단하지 않는다.

    예외(경로 부재·권한 오류·st_dev 미지원)는 모두 삼켜 빈 리스트를 반환한다.
    """
    try:
        cache_dir = os.environ.get("UV_CACHE_DIR")
        cache_path = (
            pathlib.Path(cache_dir)
            if cache_dir
            else (pathlib.Path.home() / ".cache" / "uv")
        )
        if not cache_path.exists() or not project_root.exists():
            return []
        cache_dev = os.stat(cache_path).st_dev
        project_dev = os.stat(project_root).st_dev
        if cache_dev != project_dev:
            return [
                f"uv 캐시({cache_path}, dev={cache_dev})가 프로젝트({project_root}, dev={project_dev})와 "
                "다른 볼륨입니다 — 슬롯당 .venv가 실복사됩니다. UV_CACHE_DIR을 프로젝트와 같은 볼륨으로 "
                "옮기면 제거됩니다."
            ]
        return []
    except OSError:
        return []


def diagnose_code_scan_exclude(project_root: pathlib.Path) -> list:
    """DEC-5(b). {project_root}/.opal/code-scan.json이 있고 exclude에 '.opal-worktrees'가 없으면
    경고 1건. 파일을 수정하지 않는다(DEC-5 (c) 제외 결정). 파일 부재·파싱 실패는 빈 리스트."""
    try:
        code_scan_path = project_root / ".opal" / "code-scan.json"
        if not code_scan_path.is_file():
            return []
        cfg = json.loads(code_scan_path.read_text(encoding="utf-8"))
        exclude = cfg.get("exclude", [])
        if ".opal-worktrees" not in exclude:
            return [
                ".opal/code-scan.json의 exclude에 '.opal-worktrees'가 없습니다 — worktree 사본이 "
                "code-scan 대상에 포함되어 커버리지 지표가 왜곡될 수 있습니다."
            ]
        return []
    except (OSError, json.JSONDecodeError):
        return []


def diagnose_concurrent_slots(project_root: pathlib.Path) -> list:
    """DEC-6. 이번 슬롯 포함 동시 활성 슬롯이 2개 이상이면 공유 자원 충돌 주의 경고.
    비차단(ok:true 유지)이며 파일을 수정하지 않는다. list 로직(메타 디렉토리 열거)을 재사용한다."""
    try:
        meta_dir = project_root / ".opal-worktrees" / ".meta"
        existing = len(list(meta_dir.glob("task_*.json"))) if meta_dir.is_dir() else 0
        total = existing + 1  # 이번에 생성될 슬롯 포함
        if total >= 2:
            return [
                f"동시 슬롯 {total}개 — 공유 자원(개발 DB·포트·compose 프로젝트명) 충돌 주의"
            ]
        return []
    except OSError:
        return []


def _copy_local_files(
    project_root: pathlib.Path, wt_root: pathlib.Path, copy_list: list, warnings: list
):
    """copy[] 값을 worktree로 복사한다. 원본 부재는 비차단 경고."""
    copied = []
    warnings = list(warnings)
    for rel in copy_list:
        src = project_root / rel
        if not src.is_file():
            warnings.append(f"copy 원본 파일 없음(비차단): {rel}")
            continue
        dest = wt_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        copied.append(rel)
    return copied, warnings


# ─────────────────────────────────────────────────────────────────────────────
# init 서브명령 — 탐지 기반 초안 생성 (F-002, DEC-8/ADD-1). 자동 생성이 아니라
# `code-scan init`과 동형의 비대화형 탐지 초안 생성이다. 알고리즘은 PLAN.md §1.4
# DEC-8 "탐지 규칙"·"setup[] 탐지"·"추측하지 않는 것"·"멱등·안전" 4절 그대로다.
# ─────────────────────────────────────────────────────────────────────────────

MANIFEST_FILENAMES = frozenset(
    {
        "package.json",
        "pyproject.toml",
        "go.mod",
        "Cargo.toml",
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "composer.json",
        "Gemfile",
    }
)

# lock/manifest → 생성될 setup 항목(run). 순서가 곧 우선순위(한 디렉토리에 둘 이상
# 있으면 먼저 매치되는 것 하나만 채택). gradle·maven·go·cargo는 의도적으로 없음
# (빌드 시 자동 해석 — DEC-8 setup[] 탐지표).
_LOCK_FILE_SETUP_MAP = (
    ("uv.lock", "uv sync"),
    ("pnpm-lock.yaml", "pnpm install"),
    ("bun.lock", "bun install"),
    ("bun.lockb", "bun install"),
    ("package-lock.json", "npm ci"),
    ("yarn.lock", "yarn install"),
)

# gitignore된 로컬 설정 후보 — copy[]는 채우지 않고(추측 금지) 이 패턴으로만
# `_copy_candidates`에 제시한다(DEC-8 "추측하지 않는 것").
_COPY_CANDIDATE_PATTERNS = (".env*", "settings*.local.*", "settings.yaml")

# `setup[]`·`_copy_candidates` 깊은 탐색에서 내려가지 않는 빌드 산출물·의존성
# 디렉토리(DEC-8 보충 2 — S-31). 이 이름을 가진 디렉토리는 그 자체도 검사하지
# 않고 하위로도 재귀하지 않는다.
_BUILD_ARTIFACT_DIR_NAMES = frozenset(
    {"node_modules", ".venv", ".git", "dist", "build", ".next"}
)


def _iter_setup_search_dirs(repo_dir: pathlib.Path, max_depth: int = 2):
    """`repo_dir` 자신(depth 0)부터 `max_depth`까지 하위 디렉토리를 얕게 순회한다
    (DEC-8 보충 2 — mams 실측: repos 자신보다 한 단계 더 깊은 곳에 lock이 있다).
    `_BUILD_ARTIFACT_DIR_NAMES`에 속한 이름의 디렉토리는 자기 자신도 내어주지
    않고 그 하위로도 내려가지 않는다(무한 재귀 금지 + 빌드 산출물 제외)."""
    if not repo_dir.is_dir():
        return
    yield repo_dir

    def _walk(directory: pathlib.Path, depth: int):
        try:
            children = sorted(directory.iterdir())
        except OSError:
            return
        for child in children:
            if not child.is_dir() or child.name in _BUILD_ARTIFACT_DIR_NAMES:
                continue
            yield child
            if depth < max_depth:
                yield from _walk(child, depth + 1)

    yield from _walk(repo_dir, 1)


def _find_independent_git_dirs(project_root: pathlib.Path, max_depth: int = 3) -> list:
    """루트 이하 최대 3 depth에서 독립 `.git` **디렉토리**(worktree의 `.git` 파일은
    제외 — 기존 태스크 슬롯을 오탐하지 않기 위함)를 찾는다. 루트 자신은 후보에서
    제외하고(DEC-8 탐지 규칙 2단계), 발견 즉시 그 경계 아래로는 내려가지 않는다."""
    found: list = []

    def _walk(directory: pathlib.Path, depth: int) -> None:
        if depth > max_depth:
            return
        try:
            children = sorted(directory.iterdir())
        except OSError:
            return
        for child in children:
            if not child.is_dir():
                continue
            if child.name in (".git", ".opal-worktrees"):
                continue
            if (child / ".git").is_dir():
                found.append(child)
                continue  # 독립 레포 경계 — 더 내려가지 않는다
            _walk(child, depth + 1)

    _walk(project_root, 1)
    return sorted(child.relative_to(project_root).as_posix() for child in found)


def _tracked_top_level_dirs(project_root: pathlib.Path) -> list:
    """루트 레포(HEAD)가 추적하는 최상위 디렉토리 이름 목록. HEAD가 없거나 git 실패 시
    빈 리스트(추측하지 않는다 — 호출부가 LAYOUT_UNDETERMINED로 이어진다)."""
    result = _run_git(["ls-tree", "-d", "--name-only", "HEAD"], project_root)
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def _has_manifest_beneath(dir_path: pathlib.Path) -> bool:
    for _root, dirnames, filenames in os.walk(dir_path):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        if any(name in MANIFEST_FILENAMES for name in filenames):
            return True
    return False


def _find_monorepo_candidates(project_root: pathlib.Path) -> list:
    """DEC-8 탐지 규칙 4단계 — 루트 레포가 추적하는 최상위 디렉토리 중 하위(임의 깊이)에
    코드 manifest를 하나라도 가진 것만 후보로 채택한다."""
    candidates = []
    for name in _tracked_top_level_dirs(project_root):
        candidate_path = project_root / name
        if candidate_path.is_dir() and _has_manifest_beneath(candidate_path):
            candidates.append(name)
    return sorted(candidates)


def _detect_setup(project_root: pathlib.Path, repos: list) -> list:
    """DEC-8 `setup[]` 탐지(보충 2로 깊이 확장) — repos 각 경로 이하 최소 depth 2까지
    하위 디렉토리를 탐색해 lock 파일을 찾아 매핑한다. `cwd`는 lock 파일이 실제로
    있는 디렉토리(repos 경로 자신이 아닐 수 있다)이며, 같은 디렉토리에 lock이
    여러 종류면 `_LOCK_FILE_SETUP_MAP` 순서상 첫 매칭 1건만 채택한다. 빌드
    산출물·의존성 디렉토리(`_BUILD_ARTIFACT_DIR_NAMES`)는 탐색하지 않는다."""
    setup = []
    for rel in repos:
        repo_dir = project_root / rel
        for search_dir in _iter_setup_search_dirs(repo_dir):
            for lock_name, run_cmd in _LOCK_FILE_SETUP_MAP:
                if (search_dir / lock_name).is_file():
                    cwd = search_dir.relative_to(project_root).as_posix()
                    setup.append({"cwd": cwd, "run": run_cmd})
                    break
    return setup


def _detect_copy_candidates(project_root: pathlib.Path, repos: list) -> list:
    """gitignore 대상이 될 법한 로컬 설정 후보를 `setup[]`과 동일 깊이·동일 제외
    규칙(`_iter_setup_search_dirs`)으로 찾아 제시한다(DEC-8 보충 2). `copy[]`에
    넣지 않는다 — 안내용이다(DEC-8 "추측하지 않는 것")."""
    candidates = set()
    for rel in repos:
        repo_dir = project_root / rel
        for search_dir in _iter_setup_search_dirs(repo_dir):
            for pattern in _COPY_CANDIDATE_PATTERNS:
                for match in search_dir.glob(pattern):
                    if match.is_file():
                        candidates.add(match.relative_to(project_root).as_posix())
    return sorted(candidates)


# ─────────────────────────────────────────────────────────────────────────────
# multi-repo 캡슐 소유권 — 루트 Git 적격 R-1~R-5 / 추적 범위 겹침
# (harness/worktree.md §multi-repo 캡슐 소유권 계약). 전부 multi-repo 분기 전용이다.
# ─────────────────────────────────────────────────────────────────────────────


def _root_owns_capsule(cfg: dict) -> bool:
    """`layout: multi-repo` + `task_artifacts.repo == "."`일 때만 참. 정규화 cfg 기준이며
    `"."` 외 값은 validate 단계에서 이미 TASK_ARTIFACT_REPO_UNSUPPORTED로 차단된다."""
    artifacts = cfg.get("task_artifacts")
    return (
        cfg.get("layout") == "multi-repo"
        and isinstance(artifacts, dict)
        and artifacts.get("repo") == "."
    )


def _root_tracks(project_root: pathlib.Path, pathspec: str) -> bool:
    result = _run_git(["ls-files", "--", pathspec], project_root)
    return result.returncode == 0 and bool(result.stdout.strip())


def _root_eligibility_violations(project_root: pathlib.Path) -> list:
    """R-1~R-4를 **각각** 판정한다. 합산 1건 통과를 허용하면 `tasks/`만 추적하고 `.opal/`은
    ignore하는 프로젝트가 통과해 merge 시 귀속 대상이 브랜치에 담기지 않는다.
    R-1 불만족이면 R-2~R-4는 판정 자체가 불가하므로 `["R-1"]`만 돌려준다."""
    if not (project_root / ".git").exists():
        return ["R-1"]
    if _run_git(["rev-parse", "--git-dir"], project_root).returncode != 0:
        return ["R-1"]
    violations = []
    for condition, pathspec in (
        ("R-2", "tasks"),
        ("R-3", ".opal/AGENT.md"),
        ("R-4", ".opal/MEMORY.json"),
    ):
        if not _root_tracks(project_root, pathspec):
            violations.append(condition)
    return violations


def _root_overlap_paths(project_root: pathlib.Path, repos: list) -> list:
    """루트가 `repos[]` 경로를 1파일이라도 추적하면 그 경로들을 돌려준다(§추적 범위 겹침 차단).
    겹치면 루트 full checkout과 코드 repo worktree가 같은 경로에 착지해 승자가 정의되지 않는다."""
    return [rel for rel in repos if _root_tracks(project_root, rel)]


def _repos_not_ignored(project_root: pathlib.Path, repos: list) -> list:
    """R-5 — 루트가 각 `repos[]` 경로를 ignore하는지. `check-ignore -q`의 '실효 ignore' 의미를
    유지한다(`--no-index`를 쓰지 않는다). 추적 중인 경로는 rc=1이 되므로 이 판정은 반드시
    §추적 범위 겹침 차단 **뒤에** 놓는다."""
    return [
        rel
        for rel in repos
        if _run_git(["check-ignore", "-q", rel], project_root).returncode != 0
    ]


def _root_capsule_violations(project_root: pathlib.Path, repos: list) -> list:
    """R-1~R-5 전건 판정(`init` 초안 제시 조건용). 순서 의존을 피하려고 overlap 판정은
    포함하지 않으며, R-5는 R-1~R-4가 성립할 때만 의미를 갖는다."""
    violations = _root_eligibility_violations(project_root)
    if violations:
        return violations
    if _repos_not_ignored(project_root, repos):
        violations.append("R-5")
    return violations


def _root_base_branch_candidates(project_root: pathlib.Path, repos: list) -> list:
    """관측된 base-ref 후보 — 루트와 각 코드 저장소가 스스로 해석한 값을 그대로 모은다.
    추측하지 않는다(초안 주석 키 전용)."""
    observed = {resolve_base_ref(project_root, None)}
    for rel in repos:
        repo_dir = project_root / rel
        if (repo_dir / ".git").exists():
            observed.add(resolve_base_ref(repo_dir, None))
    return sorted(value for value in observed if value)


def _build_init_draft(project_root: pathlib.Path, layout: str, repos: list) -> dict:
    draft = _build_init_draft_base(project_root, layout, repos)
    if layout != "multi-repo":
        return draft

    # multi-repo 분기에서만 키를 늘린다(§repo별 base branch). `baseBranch`는 R-1을 만족할 때만,
    # `task_artifacts`는 R-1~R-5 전건을 만족할 때만 제시한다 — 루트가 저장소가 아니면 관측
    # base-ref가 빈 문자열이 되고(H-4), 적격하지 않은 루트의 `task_artifacts`는 쓸 수 없다.
    violations = _root_capsule_violations(project_root, repos)
    if "R-1" not in violations:
        base_branch = resolve_base_ref(project_root, None)
        if base_branch:
            draft["baseBranch"] = base_branch
            draft["_baseBranch_candidates"] = _root_base_branch_candidates(
                project_root, repos
            )
    if not violations:
        draft["task_artifacts"] = {"repo": "."}
    else:
        draft["_help"] += (
            " 루트 저장소가 캡슐 소유 적격 조건을 만족하지 않아(위반: "
            + ", ".join(violations)
            + ") task_artifacts를 제시하지 않았습니다 — 캡슐 소유 repo를 결정할 수 없어 "
            "local task ownership을 쓸 수 없습니다."
        )
    # baseBranchOverrides는 추측하지 않으므로 초안에 넣지 않는다.
    return draft


def _build_init_draft_base(project_root: pathlib.Path, layout: str, repos: list) -> dict:
    return {
        "layout": layout,
        "repos": repos,
        "branchTemplate": "feat/OP-TASK-{NNN}",
        "copy": [],
        "setup": _detect_setup(project_root, repos),
        "portOffset": 0,
        "_copy_candidates": _detect_copy_candidates(project_root, repos),
        "_help": (
            "이 파일은 worktree-tool init이 탐지 결과로 자동 생성한 초안입니다 — "
            "그대로 신뢰하지 말고 검토·수정하세요. copy/portOffset은 도구가 추측하지 "
            "않으므로 빈 값/0으로 남겨두었습니다. _copy_candidates는 로컬 설정으로 "
            "보이는 gitignore 후보 파일을 참고용으로 나열한 것이며 copy[]에 자동 반영되지 "
            "않습니다."
        ),
    }


def cmd_init(args) -> None:
    project_root = _resolve_project_root(args.project_root)
    config_path = project_root / ".opal" / "worktree.json"

    # ── 멱등·안전(DEC-8) — dry-run은 쓰지 않으므로 이 게이트 대상이 아니다 ──
    if not args.dry_run and config_path.is_file() and not args.force:
        err_response("CONFIG_EXISTS", path=str(config_path))

    # ── 탐지(DEC-8 탐지 규칙, 결정론) ──
    independent = _find_independent_git_dirs(project_root)
    if independent:
        layout = "multi-repo"
        repos = independent
    else:
        if not (project_root / ".git").exists():
            err_response("NOT_A_GIT_REPO", path=str(project_root))
        candidates = _find_monorepo_candidates(project_root)
        if not candidates:
            err_response("LAYOUT_UNDETERMINED", path=str(project_root))
        layout = "monorepo"
        repos = candidates

    draft = _build_init_draft(project_root, layout, repos)

    if args.dry_run:
        ok_response(
            command="init",
            project_root=str(project_root),
            dry_run=True,
            draft=draft,
        )
        return

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    ok_response(
        command="init",
        project_root=str(project_root),
        config_path=str(config_path),
        forced=bool(args.force),
        layout=layout,
        repos=repos,
        config=draft,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 메타 파일 — {project_root}/.opal-worktrees/.meta/task_{NNN}.json (DEC-3, worktree 밖)
# ─────────────────────────────────────────────────────────────────────────────


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _meta_path(project_root: pathlib.Path, task: str) -> pathlib.Path:
    return project_root / ".opal-worktrees" / ".meta" / f"task_{task}.json"


def _acquire_registry_lock(lock_path: pathlib.Path, timeout_ms: int):
    """LOCK_EX|LOCK_NB 재시도 루프. 성공 시 열린 fd, 상한 초과 시 None.
    `run_log_core._acquire_lock`과 동형이다(O_CREAT|O_RDWR|O_NOFOLLOW·0o600)."""
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + (timeout_ms / 1000.0)
    while True:
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        except OSError:
            if time.monotonic() >= deadline:
                return None
            time.sleep(_LOCK_POLL_INTERVAL_SEC)
            continue
        try:
            os.fchmod(fd, 0o600)
        except OSError:
            pass
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fd
        except OSError:
            os.close(fd)
            if time.monotonic() >= deadline:
                return None
            time.sleep(_LOCK_POLL_INTERVAL_SEC)


@contextlib.contextmanager
def registry_lock(meta_path: pathlib.Path, timeout_ms: int = REGISTRY_LOCK_TIMEOUT_MS):
    """registry meta 1건에 대한 배타 락(`<meta>.lock`). 상한 초과는 즉시 오류 반환이다 —
    두 축(`execution_ownership`·`attribution_state`)을 한 번에 교체하는 구간만 감싼다."""
    fd = _acquire_registry_lock(pathlib.Path(str(meta_path) + ".lock"), timeout_ms)
    if fd is None:
        err_response("registry_lock_timeout", path=str(meta_path), timeout_ms=timeout_ms)
    try:
        yield
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        except OSError:
            pass
        os.close(fd)


def write_meta_atomic(meta_path: pathlib.Path, meta: dict) -> None:
    """registry meta를 temp→os.replace로 원자 교체한다(본문은 종전과 바이트 동일한
    `ensure_ascii=False, indent=2`). `ownership_core.write_json_atomic`과 같은 방식이며
    락은 호출자가 필요한 구간에서만 잡는다."""
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(meta, ensure_ascii=False, indent=2).encode("utf-8")
    tmp_path = meta_path.with_name(f"{meta_path.name}.tmp.{os.getpid()}")
    try:
        fd = os.open(
            str(tmp_path),
            os.O_CREAT | os.O_WRONLY | os.O_TRUNC | os.O_NOFOLLOW,
            0o644,
        )
        try:
            os.write(fd, body)
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(str(tmp_path), str(meta_path))
    except OSError:
        with contextlib.suppress(OSError):
            tmp_path.unlink()
        raise


def _execution_ownership_origin() -> dict:
    """lifecycle 원점 — worktree 세션이 생기기 전 registry가 표현하는 유일한 상태다."""
    return {
        "state": EXEC_STATE_HUB_OWNED,
        "owner_session_id": None,
        "adapter": None,
        "adapter_handle": None,
        "generation": 0,
        "launch_receipt": None,
        "prompt_receipt": None,
        "failure_reason": None,
        "checkpoint_shas": [],
    }


def _validate_task_folder(value: str) -> str:
    """task_folder는 basename만 허용한다 — `/`·`\\`·`..`·NUL·경로 구분자를 거부한다
    (harness/worktree.md §canonical path 발급 계약, 제안서 §5.1)."""
    if not isinstance(value, str) or not value.strip():
        err_response("TASK_FOLDER_INVALID", value=value, reason="empty")
    if "\x00" in value:
        err_response("TASK_FOLDER_INVALID", value=value, reason="nul_byte")
    separators = {"/", "\\", os.sep, os.altsep or "/"}
    if any(sep in value for sep in separators):
        err_response("TASK_FOLDER_INVALID", value=value, reason="path_separator")
    if value in (".", ".."):
        err_response("TASK_FOLDER_INVALID", value=value, reason="dot_segment")
    if value != os.path.basename(value):
        err_response("TASK_FOLDER_INVALID", value=value, reason="not_basename")
    return value


def _issue_task_ownership(
    project_root: pathlib.Path,
    wt_root: pathlib.Path,
    cfg: dict,
    task_folder: str | None,
) -> dict:
    """canonical task path 6필드를 발급한다(AC-5). 불변식
    `task_path == realpath(task_home/tasks/task_folder)`를 발급 시점에 검증한다.

    - monorepo: 슬롯 worktree 자신이 `task_home`, `artifact_repo`는 `"."`.
    - multi-repo + `task_artifacts.repo: "."`: slot root 자체가 루트 저장소의 worktree이고 곧
      `task_home`이다 — monorepo와 동일 경로를 타며 `artifact_repo`는 `"."`.
    - multi-repo(task_artifacts 미설정): 태스크 캡슐을 소유할 repo가 설정으로 정해지지 않았으므로
      local task ownership을 활성화하지 않는다 — 위치 필드는 발급하지 않고(None),
      `--task-folder`가 명시되면 추측 대신 `TASK_ARTIFACT_REPO_MISSING`으로 중단한다.
    - `allocator_root`는 허브 절대 경로이며 registry가 소유한다. 소비자는 이 발급값을
      전달받아 쓰고 cwd·`.opal-worktrees` 문자열로 추론하지 않는다.
    """
    allocator_root = str(project_root)
    if cfg["layout"] != "monorepo" and not _root_owns_capsule(cfg):
        if task_folder is not None:
            err_response("TASK_ARTIFACT_REPO_MISSING", layout=cfg["layout"])
        return {
            "allocator_root": allocator_root,
            "task_home": None,
            "task_folder": None,
            "task_path": None,
            "artifact_repo": None,
            "task_ownership_version": TASK_OWNERSHIP_VERSION,
        }

    task_home = str(wt_root)
    task_path = None
    if task_folder is not None:
        task_path = os.path.realpath(os.path.join(task_home, "tasks", task_folder))
        expected = os.path.realpath(os.path.join(task_home, "tasks", task_folder))
        home_real = os.path.realpath(task_home)
        # 불변식 + 심볼릭 링크로 task_home 밖을 가리키지 않는지 함께 검증한다.
        if task_path != expected or os.path.commonpath([task_path, home_real]) != home_real:
            err_response(
                "TASK_FOLDER_INVALID",
                value=task_folder,
                reason="path_escape",
                task_path=task_path,
                task_home=home_real,
            )

    return {
        "allocator_root": allocator_root,
        "task_home": task_home,
        "task_folder": task_folder,
        "task_path": task_path,
        "artifact_repo": ".",
        "task_ownership_version": TASK_OWNERSHIP_VERSION,
    }


# 워크트리에 내려보내는 발급값 사본 — 소비자(hook)가 허브를 찾을 계약상 경로다.
# 워크트리 안에는 `.opal-worktrees`가 없으므로 registry를 탐색으로 찾을 수 없다. 추론이
# 아니라 발급으로 해결한다(harness/worktree.md §task root와 allocator root 계약: allocator_root는
# cwd·task path의 조상·`.opal-worktrees` 문자열로 추론하지 않는다).
TASK_OWNERSHIP_COPY_NAME = "task-ownership.json"
TASK_OWNERSHIP_ISSUED_KEYS = (
    "allocator_root",
    "task_home",
    "task_folder",
    "task_path",
    "artifact_repo",
    "task_ownership_version",
)


def _task_ownership_copy_path(wt_root) -> pathlib.Path:
    """`<worktree_root>/.opal/task-ownership.json` — `.opal/worktree.json`과 별개 파일이다."""
    return pathlib.Path(wt_root) / ".opal" / TASK_OWNERSHIP_COPY_NAME


def _task_ownership_copy_body(source: dict) -> str | None:
    """발급값 6종만 추려 사본 본문을 만든다 — 값을 재계산하지 않고 발급 원천을 그대로 옮긴다.

    `task_ownership_version`이 없는 legacy 원천은 사본 대상이 아니다(None).
    """
    if not isinstance(source, dict) or source.get("task_ownership_version") is None:
        return None
    # 위치 필드를 발급하지 않은 형상(`--task-folder` 미지정, `task_artifacts` 미설정 multi-repo)은
    # 배달할 태스크 소유권 자체가 없다 — 사본도 만들지 않는다(없는 값을 지어내지 않는다).
    if not source.get("task_path"):
        return None
    payload = {key: source.get(key) for key in TASK_OWNERSHIP_ISSUED_KEYS}
    return json.dumps(payload, ensure_ascii=False, indent=2)


TASK_OWNERSHIP_COPY_EXCLUDE = ".opal/task-ownership.json"


def _ensure_task_ownership_copy_excluded(wt_root) -> str | None:
    """사본 경로를 해당 worktree의 git exclude에 멱등 등록한다. 반환: "created"|"added"|"present"|None.

    [MUST] T124 S-26(AC-16, H-1): slot root의 `git status --porcelain`이 비어 있어야 한다 —
    비어 있지 않으면 `_inspect`의 dirty가 항상 참이 되어 `--force` 없는 remove가 **영구 차단**된다.
    도구가 내려보낸 런타임 사본이 이 불변식을 깨서는 안 되므로, 프로젝트 `.gitignore` 내용에
    의존하지 않고 `ensure_gitignore_entry`와 같은 결(이미 있으면 write 없음)의 ignore 등록을
    git exclude로 수행한다. 사본은 도구 산출물이지 사용자 소스가 아니므로 커밋 대상이 아니다.

    exclude 파일은 git common dir 소유라 같은 저장소의 다른 worktree·본체와 공유된다 — 등록
    경로가 도구 전용 파일명 하나뿐이라 다른 작업본의 판정을 넓히지 않는다. worktree가 아니거나
    git 호출이 실패하면 조용히 건너뛴다(비차단 — 사본 배달 자체는 이미 성공했다).
    """
    probe = _run_git(["rev-parse", "--git-path", "info/exclude"], pathlib.Path(wt_root))
    if probe.returncode != 0 or not probe.stdout.strip():
        return None
    exclude_path = pathlib.Path(wt_root) / probe.stdout.strip()
    exclude_path = pathlib.Path(os.path.normpath(str(exclude_path)))

    if not exclude_path.exists():
        exclude_path.parent.mkdir(parents=True, exist_ok=True)
        exclude_path.write_text(TASK_OWNERSHIP_COPY_EXCLUDE + "\n", encoding="utf-8")
        return "created"

    content = exclude_path.read_text(encoding="utf-8")
    for line in content.splitlines():
        if line.strip() == TASK_OWNERSHIP_COPY_EXCLUDE:
            return "present"
    if content and not content.endswith("\n"):
        content += "\n"
    exclude_path.write_text(content + TASK_OWNERSHIP_COPY_EXCLUDE + "\n", encoding="utf-8")
    return "added"


def _write_task_ownership_copy(wt_root, source: dict) -> bool:
    """발급값 사본을 워크트리에 기록하고 실제로 썼는지 돌려준다.

    사본은 **읽기 snapshot**이다(harness/worktree.md §cone 확장 계약) — 이 파일을 근거로
    워크트리가 자기를 허브로 간주하지 않으며, `allocator_root`는 허브가 적어준 값 그대로다.
    본문이 이미 동일하면 파일을 건드리지 않는다(멱등 — 연속 호출 바이트 동일).
    """
    body = _task_ownership_copy_body(source)
    if body is None:
        return False
    _ensure_task_ownership_copy_excluded(wt_root)
    copy_path = _task_ownership_copy_path(wt_root)
    if copy_path.is_file() and copy_path.read_text(encoding="utf-8") == body:
        return False
    copy_path.parent.mkdir(parents=True, exist_ok=True)
    copy_path.write_text(body, encoding="utf-8")
    return True


def _resolve_settings_provisioning(project_root: pathlib.Path):
    """허브 `.claude/settings.json`에서 워크트리로 내려보낼 `permissions` 값을 확정한다.

    반환은 provisioning 대상 본문(dict)이거나 no-op을 뜻하는 None이다. `hooks` 키가 있으면
    아무것도 복사하지 않고 `settings_hook_key_forbidden`으로 **create 자체를 거부한다** —
    부수 효과 이전에 판정하므로 거부 시 worktree도 사본도 남지 않는다(DEC-2 all-or-nothing).

    파일 부재는 no-op이며 create를 차단하지 않는다. 읽기·파싱 실패도 같은 no-op이다 —
    내용을 알 수 없는 원본에서 `permissions`만 안전히 뽑아낼 방법이 없으므로 아무것도
    내려보내지 않는 쪽이 계약(hooks 무전파)을 지킨다.
    """
    src = project_root / HUB_SETTINGS_REL
    if not src.is_file():
        return None
    try:
        data = json.loads(src.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    if SETTINGS_FORBIDDEN_KEY in data:
        err_response("settings_hook_key_forbidden", source=str(src))
    permissions = data.get(SETTINGS_PROVISION_KEY)
    if permissions is None:
        return None
    return {SETTINGS_PROVISION_KEY: permissions}


def _provision_worktree_settings(wt_root: pathlib.Path, body: dict) -> str:
    """확정된 본문을 `<worktree_root>/.claude/settings.local.json`에 기록하고 제외 등록한다.

    제외는 새 헬퍼를 만들지 않고 기존 export `ensure_gitignore_entry`를 그대로 쓴다(PLAN W-15).
    파일은 도구가 내려보낸 런타임 사본이지 사용자 소스가 아니므로 커밋 대상이 아니다.
    """
    dest = wt_root / WORKTREE_SETTINGS_LOCAL_REL
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")
    return ensure_gitignore_entry(wt_root, WORKTREE_SETTINGS_LOCAL_REL)


def _write_meta(
    project_root, task, cfg, branch, created, base_refs, pending_setup, ownership=None
) -> None:
    wt_root = project_root / ".opal-worktrees" / f"task_{task}"
    meta = {
        "task": task,
        "layout": cfg["layout"],
        "branch": branch,
        "created_at": _now_str(),
        "worktree_root": str(wt_root),
        "entries": [
            {
                "repo": str(gr),
                "path": str(path),
                "branch": b,
                "base_ref": base_refs[str(gr)],
            }
            for gr, path, b in created
        ],
        "pending_setup": pending_setup,
    }
    # 신규 소유권 필드는 additive다 — 기존 키를 제거·개명하지 않는다(remove/status가 읽는다).
    # 처리 완료 상태(D-2b)의 거처도 registry meta가 소유한다.
    meta_path = _meta_path(project_root, task)
    if ownership:
        meta.update(ownership)
        meta.setdefault("memory_index_requests_resolved", [])
        # execution ownership 축도 registry meta가 소유한다(C-12). legacy(= `ownership`
        # 미발급) 메타에는 붙이지 않아 `_issue_task_ownership`의 legacy 계약을 그대로 둔다.
        # 이미 기록된 블록이 있으면 generation을 잃지 않도록 이어받는다.
        existing = {}
        if meta_path.is_file():
            try:
                existing = json.loads(meta_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                existing = {}
        meta[EXECUTION_OWNERSHIP_KEY] = (
            existing.get(EXECUTION_OWNERSHIP_KEY) or _execution_ownership_origin()
        )
    write_meta_atomic(meta_path, meta)


def _load_meta(project_root: pathlib.Path, task: str) -> dict:
    meta_path = _meta_path(project_root, task)
    if not meta_path.is_file():
        err_response("META_NOT_FOUND", path=str(meta_path))
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        err_response("META_NOT_FOUND", path=str(meta_path))


def _delete_meta(project_root: pathlib.Path, task: str) -> None:
    meta_path = _meta_path(project_root, task)
    if meta_path.exists():
        meta_path.unlink()


# ─────────────────────────────────────────────────────────────────────────────
# 가드 판정 — dirty→unpushed→unmerged 고정 순서, 첫 위반 즉시 반환 (F-008, PLAN §3.8.2)
# ─────────────────────────────────────────────────────────────────────────────

GUARD_ORDER = ("dirty", "unpushed", "unmerged")


def _inspect(
    wt_path: pathlib.Path, git_root: pathlib.Path, branch: str, base_ref: str
) -> dict:
    """dirty(bool)/unpushed(int)/merged(bool) 원값을 계산한다. 거부하지 않는다 — status가 그대로 노출한다."""
    dirty = bool(_run_git(["status", "--porcelain"], wt_path).stdout.strip())

    upstream = _run_git(
        ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], wt_path
    )
    ref = upstream.stdout.strip() if upstream.returncode == 0 else base_ref
    count_res = _run_git(["rev-list", f"{ref}..HEAD", "--count"], wt_path)
    try:
        unpushed = int(count_res.stdout.strip() or 0)
    except ValueError:
        unpushed = 0

    merged_res = _run_git(
        ["branch", "--merged", base_ref, "--format=%(refname:short)"], git_root
    )
    merged_branches = merged_res.stdout.split()
    merged = branch in merged_branches

    return {"dirty": dirty, "unpushed": unpushed, "merged": merged}


def check_guards(
    wt_path: pathlib.Path, git_root: pathlib.Path, branch: str, base_ref: str
):
    """(위반 코드 | None, 상세 dict) 반환. 판정 순서는 dirty→unpushed→unmerged 고정(첫 위반 즉시 반환)."""
    info = _inspect(wt_path, git_root, branch, base_ref)
    if info["dirty"]:
        return "GUARD_DIRTY", info
    if info["unpushed"] > 0:
        return "GUARD_UNPUSHED", info
    if not info["merged"]:
        return "GUARD_UNMERGED", info
    return None, info


# ─────────────────────────────────────────────────────────────────────────────
# create 서브명령 (F-002, DEC-2·DEC-3 집행)
# ─────────────────────────────────────────────────────────────────────────────


def _rollback(
    created: list, wt_root: pathlib.Path, preserve_on_failure: bool = False
) -> list:
    """자기 생성물만 회수한다(DEC-2 all-or-nothing) — worktree remove --force + branch -D.

    [MUST] 회수는 생성의 **역순**(자식 → 루트)이다 — 자식이 남아 있으면 루트 worktree를 제거할
    수 없다. 역순 순회는 monorepo에서 `created`가 1건이라 관측 가능한 차이가 없으므로 분기하지
    않는다.

    `preserve_on_failure`는 **multi-repo 분기 전용**이다(harness/worktree.md §multi-repo 캡슐
    소유권 계약). 참이면 역순 회수 중 실패했을 때 slot을 지워 흔적을 없애지 않고 잔존
    entry(경로·repo·branch)를 돌려준다 — 흔적을 지우면 수동 복구 대상이 사라진다. 거짓이면
    monorepo의 기존 동작 그대로 반환값을 검사하지 않고 항상 `branch -D`와 slot 삭제를 수행한다.
    """
    residual = []
    for git_root, path, branch in reversed(created):
        result = _run_git(["worktree", "remove", "--force", str(path)], git_root)
        if preserve_on_failure and result.returncode != 0:
            residual.append(
                {
                    "repo": str(git_root),
                    "path": str(path),
                    "branch": branch,
                    "stderr": result.stderr.strip(),
                }
            )
            continue
        _run_git(["branch", "-D", branch], git_root)
    if residual:
        return residual
    if wt_root.exists():
        shutil.rmtree(wt_root, ignore_errors=True)
    return []


def cmd_create(args) -> None:
    project_root = _resolve_project_root(args.project_root)
    cfg = validate_worktree_config(load_config(project_root), project_root)
    branch = _render_branch(cfg["branchTemplate"], args.task, args.slug, args.skill)
    wt_root = project_root / ".opal-worktrees" / f"task_{args.task}"

    # ── (0a) 루트 캡슐 소유 적격 — 부수 효과 이전, 소유권 발급 이전에 판정한다.
    # [MUST] 판정 순서는 R-1~R-4 → 추적 범위 겹침 → R-5다(harness/worktree.md §multi-repo
    # 캡슐 소유권 계약). `check-ignore -q`는 추적 파일이 있는 경로에 rc=1을 돌려주므로, R-5를
    # 겹침보다 먼저 두면 겹침 위반이 R-5로 먼저 걸려 TASK_ARTIFACT_REPO_OVERLAP에 도달하지
    # 못한다. 두 조건은 배타적 원인이며 원인별 전용 오류를 준다. ──
    root_owned = _root_owns_capsule(cfg)
    if root_owned:
        violations = _root_eligibility_violations(project_root)
        if violations:
            err_response(
                "TASK_ARTIFACT_REPO_INVALID",
                violations=violations,
                root=str(project_root),
            )
        overlapped = _root_overlap_paths(project_root, cfg["repos"])
        if overlapped:
            err_response(
                "TASK_ARTIFACT_REPO_OVERLAP",
                paths=overlapped,
                root=str(project_root),
            )
        not_ignored = _repos_not_ignored(project_root, cfg["repos"])
        if not_ignored:
            err_response(
                "TASK_ARTIFACT_REPO_INVALID",
                violations=["R-5"],
                paths=not_ignored,
                root=str(project_root),
            )

    # ── (0) 소유권 발급값 사전 확정 — 부수 효과 이전에 검증한다(DEC-2 all-or-nothing) ──
    task_folder = getattr(args, "task_folder", None)
    if task_folder is not None:
        _validate_task_folder(task_folder)
    ownership = _issue_task_ownership(project_root, wt_root, cfg, task_folder)

    # ── (0b) 설정 provisioning 대상 확정 — 소유권 발급과 같은 이유로 부수 효과 이전이다.
    # `hooks` 거부는 worktree를 만든 뒤가 아니라 여기서 일어나야 흔적이 남지 않는다(DEC-2). ──
    settings_body = _resolve_settings_provisioning(project_root)

    # ── (1) pre-flight — 여기서 실패하면 아무것도 만들지 않는다 (DEC-2)
    # 슬롯·브랜치 판정 기준은 '존재'가 아니라 '점유'다(DEC-7) — 빈 디렉토리 잔존은
    # 차단 사유가 아니며, 재생성이 영구 차단되는 결함(H-22)을 이 판정 전환으로 없앤다. ──
    for rel in cfg["repos"]:
        src = project_root / rel
        if not src.is_dir():
            err_response("REPO_NOT_FOUND", path=rel)
    # [MUST] 루트를 포함한 전 entry 목록은 `plan_entries` 하나가 소유한다 — pre-flight·
    # base-ref 해석·worktree 생성·metadata `entries`·rollback이 모두 이 목록만 소비하며
    # 생성부가 `cfg["repos"]`를 따로 순회하지 않는다. 목록이 둘로 갈라지면 pre-flight 통과
    # 결과가 생성 결과를 보장하지 못한다. entry는 base-ref override 조회 키인 `rel`을 함께
    # 들고 다닌다(`rel`은 파생값이 아니라 설정 원문이며 루트는 `"."`).
    if cfg["layout"] == "multi-repo":
        plan_entries = [(".", project_root, wt_root)] if root_owned else []
        plan_entries += [(rel, project_root / rel, wt_root / rel) for rel in cfg["repos"]]
    else:
        plan_entries = [(".", project_root, wt_root)]
    for _rel, git_root, dest in plan_entries:
        if not (git_root / ".git").exists():
            err_response("NOT_A_GIT_REPO", path=str(git_root))
        if _dest_registered(git_root, dest):
            err_response("WORKTREE_EXISTS", path=str(dest))
        if _branch_occupied(git_root, branch):
            err_response("BRANCH_EXISTS", branch=branch, repo=str(git_root))

    # ── (2) 부수 효과(비파괴) ──
    gitignore_state = ensure_gitignore_entry(project_root)
    warnings = diagnose_cache_volume(project_root)
    warnings += diagnose_code_scan_exclude(project_root)
    warnings += diagnose_concurrent_slots(project_root)

    # ── (3) base-ref 해석 + 동결 (DEC-3) ──
    # override는 `declared` 자리에 값을 넣을 뿐이며 `resolve_base_ref`의 3단 폴백 순서를 바꾸지
    # 않는다. monorepo는 overrides를 소비하지 않으므로 식이 현행과 동치다(TASK C-2).
    overrides = cfg["baseBranchOverrides"] if cfg["layout"] == "multi-repo" else {}
    base_refs = {
        str(git_root): resolve_base_ref(
            git_root, overrides.get(rel, cfg.get("baseBranch"))
        )
        for rel, git_root, _dest in plan_entries
    }

    # ── (4) worktree 생성 — 실패 시 자기 생성물만 롤백 (DEC-2)
    # 각 레포에 브랜치가 이미 존재하는지(미점유 — (1)에서 점유는 이미 거부됨)로 경로가
    # 갈린다(DEC-7):
    #   - 브랜치 미존재 → 신규 브랜치 경로. [MUST] `git worktree add -b <branch> ...`를 단일
    #     명령으로 실행하면, git이 브랜치 ref를 먼저 만든 뒤 .git/worktrees/ 메타 등록 단계에서
    #     실패하는 경우(예: 이 단계만 권한 문제로 막힘) 브랜치가 고아 상태로 남는다 — 실패 시
    #     rollback은 "성공한 worktree add"만 대상으로 하므로 이 고아 브랜치는 회수되지 않고,
    #     재실행이 BRANCH_EXISTS로 영구 차단된다(H-7 위반). 그래서 worktree 등록(--detach)과
    #     브랜치 생성(checkout -b)을 분리한다 — worktree add가 실패하면 애초에 브랜치가 생성되지
    #     않으므로 롤백 대상 자체가 사라진다.
    #   - 브랜치 존재(미점유) → 재사용 경로. 브랜치를 만들지 않으므로 고아 브랜치 리스크가
    #     없다 — `worktree add <path> <branch>` 단일 명령으로 충분하다(DEC-7 근거).
    created = []
    try:
        if cfg["layout"] == "multi-repo":
            # 생성 순서는 루트 → 자식이다 — 자식 worktree의 부모 디렉토리가 루트 worktree 안에
            # 있어야 한다. `created`에는 `worktree add`가 실제로 성공한 entry만 넣는다(롤백이
            # 만들지 않은 대상을 회수하려 들면 회수 순서 관측이 오염된다).
            for _rel, git_root, dest in plan_entries:
                dest.parent.mkdir(parents=True, exist_ok=True)
                if _branch_exists(git_root, branch):
                    _git_or_raise(git_root, ["worktree", "add", str(dest), branch])
                    created.append((git_root, dest, branch))
                else:
                    _git_or_raise(
                        git_root,
                        [
                            "worktree",
                            "add",
                            "--detach",
                            str(dest),
                            base_refs[str(git_root)],
                        ],
                    )
                    created.append((git_root, dest, branch))
                    _git_or_raise(dest, ["checkout", "-b", branch])
        else:  # monorepo — 순서 [MUST]: --no-checkout → init --cone → set → checkout(-b)/materialize
            git_root = project_root
            created.append((git_root, wt_root, branch))
            reuse = _branch_exists(git_root, branch)
            if reuse:
                _git_or_raise(
                    git_root, ["worktree", "add", "--no-checkout", str(wt_root), branch]
                )
            else:
                _git_or_raise(
                    git_root,
                    [
                        "worktree",
                        "add",
                        "--no-checkout",
                        "--detach",
                        str(wt_root),
                        base_refs[str(git_root)],
                    ],
                )
            _git_or_raise(wt_root, ["sparse-checkout", "init", "--cone"])
            # taskCapsuleCone은 monorepo 분기에서만 repos에 이어 전개한다(PLAN D-1).
            # 기본값 []의 전개는 no-op이라 키 미지정 시 인자가 현행과 바이트 동일하다(C-1).
            _git_or_raise(
                wt_root,
                ["sparse-checkout", "set", *cfg["repos"], *cfg["taskCapsuleCone"]],
            )
            if not reuse:
                _git_or_raise(wt_root, ["checkout", "-b", branch])
            # `--no-checkout`로 만든 worktree는 인덱스가 비어 있어 detached HEAD(신규)나 이미
            # 선택된 브랜치(재사용)와 동일 커밋을 가리키는 것만으로는 sparse 패턴이 실제 파일로
            # 물질화되지 않는다(git이 "트리 변경 없음"으로 판단해 작업 디렉토리 갱신을 건너뜀).
            # reset --hard로 강제 반영한다.
            _git_or_raise(wt_root, ["reset", "--hard", "HEAD"])
    except GitFailure as exc:
        residual = _rollback(
            created, wt_root, preserve_on_failure=(cfg["layout"] == "multi-repo")
        )
        if residual:
            err_response(
                "GIT_COMMAND_FAILED",
                detail=exc.stderr,
                rolled_back=len(created) - len(residual),
                residual=residual,
            )
        err_response("GIT_COMMAND_FAILED", detail=exc.stderr, rolled_back=len(created))

    # ── (5) copy[] — 원본 부재는 비차단 경고 ──
    copied, warnings = _copy_local_files(project_root, wt_root, cfg["copy"], warnings)

    # ── (6) setup[]은 실행하지 않는다 (C-7 lazy) — 열거만 ──
    pending_setup = cfg["setup"]

    _write_meta(
        project_root,
        args.task,
        cfg,
        branch,
        created,
        base_refs,
        pending_setup,
        ownership=ownership,
    )
    # registry meta와 **같은 발급값 원천**(ownership)으로 워크트리에 읽기 snapshot을 내려보낸다.
    _write_task_ownership_copy(wt_root, ownership)
    # 성공 경로에서만 `permissions` 사본을 내려보낸다 — 발급값 사본과 같은 결의 런타임 산출물이다.
    settings_provisioned = None
    if settings_body is not None:
        settings_provisioned = _provision_worktree_settings(wt_root, settings_body)
    ok_response(
        command="create",
        task=args.task,
        **ownership,
        layout=cfg["layout"],
        worktree_root=str(wt_root),
        branch=branch,
        entries=[
            {"repo": str(g), "path": str(p), "branch": b, "base_ref": base_refs[str(g)]}
            for g, p, b in created
        ],
        gitignore=gitignore_state,
        settings_provisioned=settings_provisioned,
        copied=copied,
        pending_setup=pending_setup,
        port_offset=cfg["portOffset"],
        warnings=warnings,
    )


# ─────────────────────────────────────────────────────────────────────────────
# list / status / remove (F-002, F-008)
# ─────────────────────────────────────────────────────────────────────────────


def cmd_list(args) -> None:
    project_root = _resolve_project_root(args.project_root)
    cfg = validate_worktree_config(load_config(project_root), project_root)

    entries = []
    meta_dir = project_root / ".opal-worktrees" / ".meta"
    if meta_dir.is_dir():
        for meta_file in sorted(meta_dir.glob("task_*.json")):
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            wt_root = pathlib.Path(meta.get("worktree_root", ""))
            entries.append(
                {
                    "task": meta.get("task"),
                    "branch": meta.get("branch"),
                    "worktree_root": meta.get("worktree_root"),
                    "exists": wt_root.exists(),
                }
            )

    ok_response(
        command="list",
        project_root=str(project_root),
        layout=cfg["layout"],
        entries=entries,
    )


def _resolve_canonical_task_path(project_root: pathlib.Path, meta: dict) -> tuple:
    """registry meta의 `attribution_state`를 판정에 넣어 canonical task path를 해석하고
    `(path, source)`를 돌려준다(PLAN D-1, 제안서 §4.3 "registry가 `active`일 때는 등록된
    worktree task path를, merge 확인 뒤 `closed`일 때는 허브에 merge된 task path를 반환한다").

    - active 3상태(`attribution_state` 부재·`completed_unmerged`·`attribution_pending`):
      허브 `tasks/{task_folder}`가 워크트리 캡슐과 동시에 존재하면 자동 선택 없이
      `TASK_PATH_AMBIGUOUS`로 차단한다(AC-7, C-9, harness/worktree.md §canonical path 발급 계약).
      이 절은 118이 확정한 단일 복사본 불변식 그대로이며 약화되지 않는다.
    - `closed`(merge 확인 후): 허브 사본이 실재하면 그 경로를 `source="hub_merged"`로 반환하고
      차단하지 않는다. 가드를 없애는 게 아니라 적용 상태를 `active`로 한정하는 것이다(D-1).

    `task_ownership_version`이 없는 메타는 legacy이므로 판정 자체를 하지 않고 `(None, None)`을
    돌려준다 — 기존 활성 슬롯의 태스크 위치를 실행 중 자동 이동하지 않는다는 D-9·TASK.md C-5의
    직접 집행이며, 호출부 출력도 그만큼 변하지 않는다(C-1).
    """
    if meta.get("task_ownership_version") is None:
        return None, None
    task_folder = meta.get("task_folder")
    task_path = meta.get("task_path")
    if not task_folder or not task_path:
        return None, None
    hub_candidate = project_root / "tasks" / str(task_folder)
    if not hub_candidate.exists():
        return str(task_path), "worktree_registered"
    if os.path.realpath(str(hub_candidate)) == os.path.realpath(str(task_path)):
        return str(task_path), "worktree_registered"
    if meta.get(ATTRIBUTION_STATE_KEY) == ATTRIBUTION_STATE_CLOSED:
        return str(hub_candidate), "hub_merged"
    err_response(
        "TASK_PATH_AMBIGUOUS",
        task_folder=task_folder,
        candidates=[str(task_path), str(hub_candidate)],
    )


def _hub_root_from_path(target: pathlib.Path):
    """`--task-path`에서 허브 루트를 해석한다 — 자신 포함 조상 중 registry(`.opal-worktrees/
    .meta`)나 `.opal/worktree.json`을 가진 첫 디렉터리다. 찾지 못하면 None이다.
    cwd로 추론하지 않는다(harness/worktree.md §cone 확장 계약)."""
    current = pathlib.Path(os.path.realpath(str(target)))
    for candidate in (current, *current.parents):
        if (candidate / ".opal-worktrees" / ".meta").is_dir():
            return candidate
        if (candidate / ".opal" / "worktree.json").is_file():
            return candidate
    return None


def _registry_task_for_path(project_root: pathlib.Path, target: pathlib.Path):
    """registry에 등록된 태스크 중 `target`과 정확히 일치하는 행의 task 번호를 돌려준다.
    문자열 접두·mtime·이름 추론을 쓰지 않고 기록된 경로와 realpath 동치만 본다(C-6)."""
    meta_dir = project_root / ".opal-worktrees" / ".meta"
    if not meta_dir.is_dir():
        return None
    wanted = os.path.realpath(str(target))
    for meta_path in sorted(meta_dir.glob("task_*.json")):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(meta, dict):
            continue
        candidates = [meta.get("task_path"), meta.get("worktree_root")]
        candidates += [
            entry.get("path")
            for entry in (meta.get("entries") or [])
            if isinstance(entry, dict)
        ]
        for candidate in candidates:
            if candidate and os.path.realpath(str(candidate)) == wanted:
                return meta.get("task") or meta_path.stem[len("task_") :]
    return None


def _resolve_ownership_target(args):
    """`--project-root`+`--task`(정규형)와 `--task-path`(경로 주소형) 두 지정 방식을 하나로
    해석한다. 경로 주소형에서 registry 행을 못 찾으면 task는 None이다."""
    task_path = getattr(args, "task_path", None)
    if task_path:
        target = pathlib.Path(task_path)
        # registry 조회가 디렉터리 존재 검사보다 앞선다 — 등록된 행이 원천이고 worktree
        # 디렉터리는 회수되면 사라지는 파생물이다(legacy 메타는 태스크 138 이전에 발급돼
        # 이미 회수된 worktree를 가리킬 수 있다). 해석은 registry 발급값 realpath 동치로만
        # 하며 경로 문자열에서 신원을 추론하지 않는다(harness/worktree.md §상태 의존 해석).
        hub_root = _hub_root_from_path(target)
        if hub_root is not None:
            registered_task = _registry_task_for_path(hub_root, target)
            if registered_task is not None:
                return hub_root, registered_task
        if not target.is_dir():
            err_response("PROJECT_ROOT_NOT_FOUND", path=str(target))
        if hub_root is None:
            err_response(
                "PROJECT_ROOT_NOT_FOUND", path=str(target), reason="hub_root_not_found"
            )
        return hub_root, None
    if args.project_root and args.task:
        return _resolve_project_root(args.project_root), args.task
    err_response("CONFIG_MISSING_KEY", reason="task_target_required")


def cmd_status(args) -> None:
    project_root, task = _resolve_ownership_target(args)
    if task is None:
        # 경로 주소형이 registry 미등록 경로를 가리킨 경우 — 워크트리 lifecycle 밖의 태스크다.
        # execution ownership 축이 추가돼도 이 경로가 실패하지 않는다(legacy 통과 계약).
        ok_response(
            command="status",
            task=None,
            project_root=str(project_root),
            task_path=os.path.realpath(str(args.task_path)),
            registered=False,
        )
        return
    meta = _load_meta(project_root, task)
    canonical_task_path, canonical_source = _resolve_canonical_task_path(
        project_root, meta
    )
    # 기존 워크트리 보강 — registry가 원천이고 사본은 그 복제다. 값이 다르면 registry 기준으로
    # 덮어쓰고, 같으면 파일을 건드리지 않는다(연속 호출 바이트 동일). legacy 메타
    # (`task_ownership_version` 부재)는 발급값 자체가 없으므로 사본도 만들지 않는다.
    meta_wt_root = meta.get("worktree_root")
    if meta_wt_root and pathlib.Path(meta_wt_root).is_dir():
        _write_task_ownership_copy(meta_wt_root, meta)

    entries_out = []
    for entry in meta.get("entries", []):
        git_root = pathlib.Path(entry["repo"])
        wt_path = pathlib.Path(entry["path"])
        branch = entry["branch"]
        base_ref = entry["base_ref"]

        if not wt_path.exists():
            entries_out.append(
                {
                    "repo": entry["repo"],
                    "path": entry["path"],
                    "branch": branch,
                    "base_ref": base_ref,
                    "dirty": None,
                    "unpushed": None,
                    "merged": None,
                    "worktree_missing": True,
                }
            )
            continue

        info = _inspect(wt_path, git_root, branch, base_ref)
        entries_out.append(
            {
                "repo": entry["repo"],
                "path": entry["path"],
                "branch": branch,
                "base_ref": base_ref,
                "dirty": info["dirty"],
                "unpushed": info["unpushed"],
                "merged": info["merged"],
            }
        )

    # canonical task path는 `task_ownership_version` 보유 메타에서만 해석된다 — legacy·
    # 비워크트리 경로의 출력은 변경 전과 바이트 동일하게 유지한다(TASK.md C-1).
    canonical_out = {}
    if canonical_task_path:
        canonical_out["task_path"] = canonical_task_path
        canonical_out["task_path_source"] = canonical_source

    execution_ownership = meta.get(EXECUTION_OWNERSHIP_KEY)
    if execution_ownership:
        canonical_out[EXECUTION_OWNERSHIP_KEY] = execution_ownership
        canonical_out[ATTRIBUTION_STATE_KEY] = meta.get(ATTRIBUTION_STATE_KEY)

    ok_response(
        command="status",
        task=task,
        branch=meta.get("branch"),
        worktree_root=meta.get("worktree_root"),
        entries=entries_out,
        pending_setup=meta.get("pending_setup", []),
        **canonical_out,
    )


def _parse_receipt_arg(value, field):
    """`--launch-receipt`/`--prompt-receipt` 값을 registry meta에 실을 객체로 정규화한다.

    argparse `type=json.loads`를 쓰지 않는다 — 파싱이 실패하면 argparse가 usage를 찍고
    exit 2로 죽어 이 CLI의 '단일 라인 JSON 응답' 규약이 깨지기 때문이다. 실패는 여기서
    `ownership_receipt_invalid` 구조화 오류로 반환한다. None은 미지정, dict는 그대로 통과.

    문자열은 생김새로 의도를 추론하지 않고 **항상** JSON으로 파싱한다. 파싱에 실패하거나
    결과가 dict가 아니면(배열·숫자·문자열 리터럴) 거부한다 — receipt는 객체만 허용한다.
    """
    if value is None or isinstance(value, dict):
        return value
    try:
        parsed = json.loads(value)
    except ValueError:
        err_response("ownership_receipt_invalid", field=field, value=value)
    if not isinstance(parsed, dict):
        err_response("ownership_receipt_invalid", field=field, value=value)
    return parsed


def cmd_ownership_set(args) -> None:
    """registry meta의 `execution_ownership`과 `attribution_state`를 **한 번의** lock +
    atomic replace 안에서 함께 전이한다(TASK.md §Worktree registry SSOT, C-12·C-15).

    허용 조합은 TASK.md 표의 6개 파생 단계뿐이고 나머지는 `ownership_state_invalid`다.
    `session_launching → worktree_session_owned`은 launch/prompt receipt가 둘 다 있을 때만
    성공하며, launch/prompt 실패는 `failure_reason=launch_failed` + generation 증가와 함께
    `hub_owned` + `attribution_state` 키 부재로 단일 교체로 복귀한다 — 중간 상태를 만들지
    않으므로 dual writer·orphan owner가 남지 않는다.
    """
    project_root, task = _resolve_ownership_target(args)
    if task is None:
        # 경로 주소형이 registry 미등록 경로를 가리킨 경우 — 행을 만들지 않고 거부한다.
        # registry 행은 `create`가 발급하고, 해석은 발급값 realpath 동치로만 한다
        # (harness/worktree.md §canonical path 발급 계약 — 경로에서 신원 추론 금지).
        err_response(
            "ownership_task_unregistered",
            task_path=os.path.realpath(str(args.task_path)),
            project_root=str(project_root),
        )

    state = args.execution_ownership
    attribution = args.attribution_state
    if (state, attribution) not in ALLOWED_OWNERSHIP_COMBOS:
        err_response(
            "ownership_state_invalid",
            execution_ownership=state,
            attribution_state=attribution,
            allowed=sorted(ALLOWED_OWNERSHIP_COMBOS),
        )
    if args.failure_reason and (state, attribution) != (
        EXEC_STATE_HUB_OWNED,
        ATTRIBUTION_TOKEN_ACTIVE,
    ):
        err_response(
            "ownership_state_invalid",
            execution_ownership=state,
            attribution_state=attribution,
            reason="failure_requires_hub_owned_revert",
        )

    # receipt는 registry meta에 **객체**로 저장한다(PLAN W-11) — lock 획득 전에 정규화해
    # 잘못된 입력이 락·파일에 닿지 않게 한다.
    launch_receipt_arg = _parse_receipt_arg(args.launch_receipt, "launch_receipt")
    prompt_receipt_arg = _parse_receipt_arg(args.prompt_receipt, "prompt_receipt")

    meta_path = _meta_path(project_root, task)
    # 등록된 행에만 동작한다 — 미등록 task는 lock 파일조차 만들지 않고 먼저 거부한다.
    if not meta_path.is_file():
        err_response(
            "ownership_task_unregistered", task=task, meta_path=str(meta_path)
        )
    with registry_lock(meta_path):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            err_response("META_NOT_FOUND", path=str(meta_path))
        if not isinstance(meta, dict):
            err_response("META_NOT_FOUND", path=str(meta_path))

        prior = meta.get(EXECUTION_OWNERSHIP_KEY) or _execution_ownership_origin()
        launch_receipt = launch_receipt_arg or prior.get("launch_receipt")
        prompt_receipt = prompt_receipt_arg or prior.get("prompt_receipt")
        # `worktree_session_owned`로 **진입하는 모든 전이**가 receipt 2종을 요구한다 —
        # prior 상태를 조건으로 두면 원점에서 직행해 가드를 우회할 수 있다(AC-7·AC-8·C-15).
        # 이미 메타에 있는 receipt는 위에서 prior로 승계되므로 멱등 재설정은 통과한다.
        if state == EXEC_STATE_WORKTREE_SESSION_OWNED and not (
            launch_receipt and prompt_receipt
        ):
            err_response(
                "ownership_receipt_missing",
                launch_receipt=launch_receipt,
                prompt_receipt=prompt_receipt,
            )

        prior_generation = int(prior.get("generation") or 0)
        if args.generation is None:
            generation = prior_generation + 1
        elif args.generation <= prior_generation:
            err_response(
                "ownership_generation_regressed",
                generation=args.generation,
                prior_generation=prior_generation,
            )
        else:
            generation = args.generation

        block = {
            "state": state,
            "owner_session_id": args.owner_session_id
            if args.owner_session_id is not None
            else prior.get("owner_session_id"),
            "adapter": args.adapter if args.adapter is not None else prior.get("adapter"),
            "adapter_handle": args.adapter_handle
            if args.adapter_handle is not None
            else prior.get("adapter_handle"),
            "generation": generation,
            "launch_receipt": launch_receipt,
            "prompt_receipt": prompt_receipt,
            "failure_reason": args.failure_reason,
            "checkpoint_shas": list(prior.get("checkpoint_shas") or [])
            + list(args.checkpoint_sha or []),
        }
        if args.failure_reason:
            # 실패 복귀는 owner·receipt를 남기지 않는다 — orphan owner 금지(C-13).
            block["owner_session_id"] = None
            block["adapter_handle"] = None
            block["launch_receipt"] = None
            block["prompt_receipt"] = None

        meta.setdefault("task", task)
        meta[EXECUTION_OWNERSHIP_KEY] = block
        if attribution == ATTRIBUTION_TOKEN_ACTIVE:
            meta.pop(ATTRIBUTION_STATE_KEY, None)
        else:
            meta[ATTRIBUTION_STATE_KEY] = attribution
        write_meta_atomic(meta_path, meta)

    ok_response(
        command="ownership-set",
        task=task,
        project_root=str(project_root),
        meta_path=str(meta_path),
        execution_ownership=block,
        attribution_state=meta.get(ATTRIBUTION_STATE_KEY),
    )


# ─────────────────────────────────────────────────────────────────────────────
# 체크포인트 커밋 게이트 (TASK.md C-17~C-20, PLAN W-16)
# ─────────────────────────────────────────────────────────────────────────────
CHECKPOINT_MODES = ("interactive", "semi_agentic", "agentic")

# C-18 — `semi-agentic`이 자율 커밋할 수 있는 단계 계열. PLAN-equivalent 승인과 CLOSE 진입
# 승인 두 시점뿐이며 EXECUTE·TEST는 이 집합 밖이라 `checkpoint_mode_denied`가 된다.
SEMI_AGENTIC_STAGE_FAMILIES = frozenset({"plan", "close"})

# C-20 — 이 서브명령이 절대 수행하지 않는 Git 동작. 목록 밖 요청도 수행 범위가 아니므로
# 기본 거부(default-deny)한다 — 이 게이트는 staged 변경의 로컬 commit **하나**만 수행한다.
FORBIDDEN_GIT_OPS = frozenset(
    {
        "merge",
        "push",
        "pull",
        "rebase",
        "reset",
        "revert",
        "cherry-pick",
        "amend",
        "worktree",
        "tag",
        "filter-branch",
    }
)

# C-20 — 기본 브랜치 commit은 모드와 무관하게 사용자 승인 경계다.
PROTECTED_BRANCHES = frozenset({"main", "master"})

CHECKPOINT_FALLBACK_AUTHOR = (
    "-c",
    "user.name=OPAL worktree-tool",
    "-c",
    "user.email=worktree-tool@opal.local",
)


def _normalize_mode(raw: str) -> str:
    return (raw or "").strip().lower().replace("-", "_")


def _stage_family(raw: str) -> str:
    """`plan.user_confirm`·`PLAN`·`plan-equivalent` 같은 표기를 단계 계열 한 단어로 줄인다.
    파이프라인 step key(`<stage>.<step>`)와 단계 이름을 같은 어휘로 받기 위한 정규화다."""
    token = (raw or "").strip().lower().replace("-", "_")
    return token.split(".", 1)[0]


def _checkpoint_git_or_fail(wt_root: pathlib.Path, args: list) -> str:
    result = _run_git(args, wt_root)
    if result.returncode != 0:
        err_response(
            "GIT_COMMAND_FAILED",
            command=" ".join(["git", *args]),
            stderr=result.stderr.strip(),
        )
    return result.stdout


def _staged_paths(wt_root: pathlib.Path) -> list:
    """staged 경로를 worktree 루트 상대 POSIX 경로로 돌려준다 — index만 읽으므로 허브
    working tree에 쓰지 않는다(AC-19)."""
    raw = _checkpoint_git_or_fail(wt_root, ["diff", "--cached", "--name-only", "-z"])
    return [path for path in raw.split("\0") if path]


def _within_owned_scope(path: str, scopes: list) -> bool:
    """`path`가 소유 범위 중 하나에 포함되는지 — 경로 구분자 경계로만 판정한다
    (`owned_only.txt`가 `owned_only.txt.bak`을 덮지 않는다)."""
    for scope in scopes:
        prefix = scope.strip("/")
        if not prefix:
            continue
        if path == prefix or path.startswith(prefix + "/"):
            return True
    return False


def _checkpoint_target(args) -> tuple:
    """체크포인트 대상 worktree와 registry 행을 해석한다.

    `--worktree-root`는 워크트리 세션이 가진 **발급값 사본**(`.opal/task-ownership.json`)의
    `allocator_root`로만 허브에 도달하고, 허브 registry에서 realpath 동치인 행을 찾는다 —
    경로 문자열·조상 순회로 신원을 추론하지 않는다(C-6, harness/worktree.md §canonical path
    발급 계약). 사본이 없으면 이 worktree는 registry lifecycle 밖이며, 그 사실을 지어내지
    않고 `meta=None`으로 보고한다.
    """
    worktree_root = getattr(args, "worktree_root", None)
    if worktree_root:
        wt_root = pathlib.Path(os.path.realpath(str(worktree_root)))
        if not wt_root.is_dir():
            err_response("PROJECT_ROOT_NOT_FOUND", path=str(wt_root))
        copy_path = _task_ownership_copy_path(wt_root)
        if not copy_path.is_file():
            return wt_root, None, None, None
        try:
            copy_data = json.loads(copy_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return wt_root, None, None, None
        allocator_root = (copy_data or {}).get("allocator_root")
        if not allocator_root:
            return wt_root, None, None, None
        project_root = pathlib.Path(str(allocator_root))
        task = _registry_task_for_path(project_root, wt_root)
        if task is None:
            return wt_root, project_root, None, None
        return wt_root, project_root, task, _load_meta(project_root, task)

    project_root, task = _resolve_ownership_target(args)
    if task is None:
        err_response(
            "ownership_task_unregistered",
            task_path=os.path.realpath(str(args.task_path)),
            project_root=str(project_root),
        )
    meta = _load_meta(project_root, task)
    meta_wt_root = meta.get("worktree_root")
    if not meta_wt_root:
        err_response("WORKTREE_NOT_FOUND", task=task, project_root=str(project_root))
    wt_root = pathlib.Path(os.path.realpath(str(meta_wt_root)))
    if not wt_root.is_dir():
        err_response("WORKTREE_NOT_FOUND", task=task, path=str(wt_root))
    return wt_root, project_root, task, meta


def _append_checkpoint_sha(meta_path: pathlib.Path, sha: str) -> list:
    """`execution_ownership.checkpoint_shas[]`에 SHA를 append한다 — 기존 registry lock +
    원자 교체 경로를 그대로 재사용하고 사설 writer를 만들지 않는다(W-11 계약)."""
    with registry_lock(meta_path):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            err_response("META_NOT_FOUND", path=str(meta_path))
        if not isinstance(meta, dict):
            err_response("META_NOT_FOUND", path=str(meta_path))
        block = dict(meta.get(EXECUTION_OWNERSHIP_KEY) or _execution_ownership_origin())
        shas = list(block.get("checkpoint_shas") or [])
        shas.append(sha)
        block["checkpoint_shas"] = shas
        meta[EXECUTION_OWNERSHIP_KEY] = block
        write_meta_atomic(meta_path, meta)
    return shas


def cmd_checkpoint(args) -> None:
    """소유 worktree branch의 로컬 체크포인트 커밋 **하나**를 폐쇄 검사 뒤에 수행한다.

    검사 순서는 PLAN W-16의 열거 순서와 같다 — 금지 Git 동작(C-20) → 소유권 1:1(C-15) →
    branch 일치 → staged scope 폐쇄 → 모드별 허용 경계(C-17·C-18). 커밋은 worktree에서만
    수행하므로 허브 working tree에 쓰지 않고, 공유 objects/refs만 사용한다(AC-19).
    """
    requested_git = (getattr(args, "git_command", None) or "").strip()
    if requested_git:
        tokens = [token.lstrip("-").lower() for token in requested_git.split()]
        forbidden = bool(FORBIDDEN_GIT_OPS.intersection(tokens))
        err_response(
            "requires_user_approval",
            requested=requested_git,
            reason="forbidden_git_operation" if forbidden else "unsupported_git_command",
            forbidden=sorted(FORBIDDEN_GIT_OPS),
        )

    mode = _normalize_mode(args.mode)
    stage = (args.stage or "").strip()
    wt_root, project_root, task, meta = _checkpoint_target(args)

    toplevel = _run_git(["rev-parse", "--show-toplevel"], wt_root)
    if toplevel.returncode != 0:
        err_response("NOT_A_GIT_REPO", path=str(wt_root))

    branch_result = _run_git(["symbolic-ref", "--quiet", "--short", "HEAD"], wt_root)
    branch = branch_result.stdout.strip()
    if not branch:
        err_response(
            "checkpoint_branch_mismatch", reason="detached_head", worktree_root=str(wt_root)
        )
    if branch in PROTECTED_BRANCHES:
        err_response(
            "requires_user_approval", reason="protected_branch_commit", branch=branch
        )
    if project_root and os.path.realpath(str(project_root)) == str(wt_root):
        err_response(
            "requires_user_approval", reason="hub_commit", worktree_root=str(wt_root)
        )

    # (1) 소유권 1:1 — registry 행이 있을 때만 판정한다. 행이 없으면 이 worktree는 lifecycle
    # 밖이고 주장할 소유자도 없으므로, 없는 소유권을 지어내지 않는다(발급값이 SSOT).
    session_id = os.environ.get("OPAL_SESSION_ID")
    if meta is not None:
        block = meta.get(EXECUTION_OWNERSHIP_KEY) or {}
        if block.get("state") != EXEC_STATE_WORKTREE_SESSION_OWNED:
            err_response(
                "checkpoint_ownership_denied",
                reason="not_worktree_session_owned",
                task=task,
                execution_ownership=block.get("state"),
            )
        if not session_id or block.get("owner_session_id") != session_id:
            err_response(
                "checkpoint_ownership_denied",
                reason="foreign_owner",
                task=task,
                owner_session_id=block.get("owner_session_id"),
            )
        # (2) 현재 branch == registry branch
        if meta.get("branch") and branch != meta.get("branch"):
            err_response(
                "checkpoint_branch_mismatch",
                task=task,
                branch=branch,
                registry_branch=meta.get("branch"),
            )

    # (3) staged 경로 폐쇄 — `--owned-scope` 미지정이면 worktree 경계 자체가 소유 범위다.
    staged = _staged_paths(wt_root)
    if not staged:
        err_response("checkpoint_nothing_staged", worktree_root=str(wt_root), stage=stage)
    owned_scope = list(getattr(args, "owned_scope", None) or [])
    if owned_scope:
        violations = [p for p in staged if not _within_owned_scope(p, owned_scope)]
        if violations:
            err_response(
                "checkpoint_scope_violation",
                violations=violations,
                owned_scope=owned_scope,
                task=task,
            )

    # (4) 모드별 허용 경계 — 목록에 없는 조합은 전부 거부한다(default-deny).
    if mode not in CHECKPOINT_MODES:
        err_response(
            "checkpoint_mode_denied",
            reason="unknown_mode",
            mode=args.mode,
            allowed=sorted(CHECKPOINT_MODES),
        )
    approved = bool(getattr(args, "approved", False))
    if mode == "semi_agentic" and _stage_family(stage) not in SEMI_AGENTIC_STAGE_FAMILIES:
        err_response(
            "checkpoint_mode_denied",
            reason="semi_agentic_autonomous_stage",
            mode=mode,
            stage=stage,
            allowed_stages=sorted(SEMI_AGENTIC_STAGE_FAMILIES),
        )
    if mode in ("interactive", "semi_agentic") and not approved:
        err_response(
            "checkpoint_mode_denied",
            reason="stage_approval_required",
            mode=mode,
            stage=stage,
        )

    message = args.message or f"chore({task or 'task'}): {stage} 체크포인트"
    commit_args = ["-c", "commit.gpgsign=false"]
    identity = _run_git(["config", "--get", "user.email"], wt_root)
    if identity.returncode != 0 or not identity.stdout.strip():
        commit_args.extend(CHECKPOINT_FALLBACK_AUTHOR)
    commit = _run_git([*commit_args, "commit", "-m", message], wt_root)
    if commit.returncode != 0:
        err_response(
            "GIT_COMMAND_FAILED", command="git commit", stderr=commit.stderr.strip()
        )
    sha = _checkpoint_git_or_fail(wt_root, ["rev-parse", "HEAD"]).strip()

    # (5) 성공 SHA를 lifecycle에 append한다. registry 행이 없으면 기록할 SSOT가 없으므로
    # 이번 커밋만 보고한다(`registered: false`).
    if meta is not None and project_root is not None and task is not None:
        checkpoint_shas = _append_checkpoint_sha(_meta_path(project_root, task), sha)
    else:
        checkpoint_shas = [sha]

    ok_response(
        command="checkpoint",
        task=task,
        project_root=str(project_root) if project_root else None,
        worktree_root=str(wt_root),
        branch=branch,
        mode=mode,
        stage=stage,
        commit=sha,
        checkpoint_shas=checkpoint_shas,
        staged=staged,
        registered=meta is not None,
    )


def _pending_memory_index_requests(meta: dict) -> list:
    """메타의 `task_path`로 태스크 캡슐 추적 파일을 읽어, 아직 처리 완료로 기록되지 않은
    요청의 `body_sha256` 목록을 돌려준다(PLAN D-2/D-2b).

    요청 "내용"은 캡슐 파일(`{task_path}/memory-index-request.json`)이, "처리 완료" 상태는
    registry meta의 `memory_index_requests_resolved`가 소유한다. 캡슐 파일 부재는 요청 0건과
    동치이므로 no-op으로 통과한다 — legacy 메타(`task_path` 없음)도 같은 경로로 통과한다.
    """
    task_path = meta.get("task_path")
    if not task_path:
        return []
    request_file = pathlib.Path(str(task_path)) / MEMORY_INDEX_REQUEST_FILE
    if not request_file.is_file():
        return []
    try:
        doc = json.loads(request_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(doc, dict):
        return []
    resolved = meta.get("memory_index_requests_resolved") or []
    pending = []
    for request in doc.get("requests") or []:
        if not isinstance(request, dict):
            continue
        body_sha = request.get("body_sha256")
        if body_sha and body_sha not in resolved and body_sha not in pending:
            pending.append(body_sha)
    return pending


def cmd_remove(args) -> None:
    project_root = _resolve_project_root(args.project_root)
    meta = _load_meta(project_root, args.task)
    entries = meta.get("entries", [])

    # ── (1) 가드 판정 — 첫 위반에서 즉시 반환. --force면 우회하고 계속 ──
    bypassed_guards = []

    # memory index 요청 가드 — worktree를 회수하면 캡슐 파일도 함께 사라지므로, 미처리 요청이
    # 남아 있으면 기존 3중 가드보다 먼저 거부한다(AC-11). 기존 가드와 같은 규율로 --force만
    # 우회할 수 있고, 우회하면 bypassed_guards에 기록된다.
    pending_requests = _pending_memory_index_requests(meta)
    if pending_requests:
        if args.force:
            bypassed_guards.append("MEMORY_INDEX_REQUEST_PENDING")
        else:
            err_response(
                "MEMORY_INDEX_REQUEST_PENDING",
                task_path=meta.get("task_path"),
                pending=pending_requests,
            )

    # ── 신규 계약의 적용 범위는 `layout: "multi-repo"` 분기 하나다
    # (harness/worktree.md §multi-repo 캡슐 소유권 계약 첫 줄). monorepo·비워크트리 경로는 이
    # 절의 어떤 항목도 소비하지 않으며 기존 판정·출력·실패 표면을 그대로 유지한다(TASK C-2·C-3).
    # 판정 기준은 create 시점에 메타로 동결된 layout이다 — remove는 설정을 다시 읽지 않는다.
    multi_repo = meta.get("layout") == "multi-repo"

    # [MUST] 회수는 생성의 역순(자식 → 루트)이다 — 자식이 남아 있으면 루트를 제거할 수 없다.
    # entry별로 **경로 실재**와 **Git 등록** 두 축을 따로 보고 판정한다(멱등 재시도):
    #   (없음, 없음) → 이미 회수됨, skip(오류 아님)   (없음, 있음) → 등록 고아, 차단·보존
    #   (있음, 없음) → 미등록 잔여 디렉토리, 차단·보존 (있음, 있음) → 가드 판정 후 회수
    # 등록 판정은 create pre-flight가 쓰는 기존 판정기를 재사용하며 새 기준을 만들지 않는다.
    # 이 판정은 `--force` 없이 동작한다 — 재시도가 가드 우회를 요구하지 않는다.
    pending = []
    for entry in (reversed(entries) if multi_repo else entries):
        git_root = pathlib.Path(entry["repo"])
        wt_path = pathlib.Path(entry["path"])
        branch = entry["branch"]
        base_ref = entry["base_ref"]

        if multi_repo:
            path_exists = wt_path.exists()
            registered = _dest_registered(git_root, wt_path)
            if not path_exists and not registered:
                continue  # 이미 회수됨
            if path_exists != registered:
                # [MUST] 불일치 2종을 도구가 자동 복구하지 않는다 — `git worktree prune`을
                # 호출하지 않고(대상이 해당 repo의 모든 stale 관리정보라 다른 태스크 슬롯까지
                # 지운다) 미등록 잔여 디렉토리를 삭제하지 않는다(내용이 사용자 파일일 수 있다).
                err_response(
                    "WORKTREE_REMOVE_FAILED",
                    repo=str(git_root),
                    path=str(wt_path),
                    mismatch=(
                        "registration_without_path"
                        if registered
                        else "path_without_registration"
                    ),
                )
        elif not wt_path.exists():
            # monorepo·비워크트리는 기존 WORKTREE_NOT_FOUND 경로를 그대로 유지한다.
            if args.force:
                continue
            err_response("WORKTREE_NOT_FOUND", path=str(wt_path))

        code, info = check_guards(wt_path, git_root, branch, base_ref)
        if code:
            if args.force:
                if code not in bypassed_guards:
                    bypassed_guards.append(code)
            else:
                err_response(code, **info)
        pending.append(entry)

    # ── (2) 실제 제거 — worktree 디렉토리만 회수, 브랜치는 삭제하지 않는다 ──
    # [MUST] multi-repo 분기에 한해, 전 entry의 `git worktree remove`가 성공한 뒤에만 메타와
    # slot root를 삭제한다(monorepo는 반환값 미검사 + 무조건 삭제인 기존 동작을 유지한다).
    # 하나라도 실패하면 WORKTREE_REMOVE_FAILED로 반환하고 메타 삭제와 slot 삭제를 실행하지
    # 않는다 — 메타가 남아 있어야 재시도와 수동 복구가 가능하다. `--force`는 가드 우회에만
    # 적용되며 이 실패 판정을 우회하지 않는다.
    removed = []
    for entry in pending:
        git_root = pathlib.Path(entry["repo"])
        wt_path = pathlib.Path(entry["path"])
        remove_args = ["worktree", "remove", str(wt_path)]
        if args.force:
            remove_args.append("--force")
        result = _run_git(remove_args, git_root)
        if multi_repo and result.returncode != 0:
            err_response(
                "WORKTREE_REMOVE_FAILED",
                repo=str(git_root),
                path=str(wt_path),
                detail=result.stderr.strip(),
                removed=removed,
            )
        removed.append(entry["path"])

    _delete_meta(project_root, args.task)

    # ── (3) 슬롯 루트 회수 (DEC-7 정리 범위 확장) ──
    # 레포별 worktree 경로(entry["path"])만 회수하면 그 상위 디렉토리(예: multi-repo의
    # `task_{NNN}/workspace/`)와 슬롯 루트 자체(`task_{NNN}/`)가 빈 껍데기로 남아 같은 번호
    # 재생성이 WORKTREE_EXISTS로 영구 차단된다(H-22, revup 실측). `.opal-worktrees/` 자체와
    # `.meta/`는 다른 슬롯이 쓰므로 남긴다 — 회수 대상은 `task_{NNN}/` 이하뿐이다.
    wt_root = pathlib.Path(
        meta.get("worktree_root")
        or str(project_root / ".opal-worktrees" / f"task_{args.task}")
    )
    if wt_root.exists():
        shutil.rmtree(wt_root, ignore_errors=True)

    ok_response(
        command="remove",
        task=args.task,
        removed=removed,
        forced=bool(args.force),
        bypassed_guards=bypassed_guards,
    )


# ─────────────────────────────────────────────────────────────────────────────
# finalize 서브명령 — 재진입 path-scoped 판정 (PLAN D-3b, AC-10·AC-11)
# ─────────────────────────────────────────────────────────────────────────────


def _normalize_repo_relative(raw: str) -> str | None:
    """선언 집합과 관측 집합을 같은 표기로 맞춘다 — 레포 루트 상대 POSIX 경로(H-4).

    표기가 어긋나면 부분집합 판정이 늘 거짓이 되어 재진입이 영구 차단되므로, 양쪽 입력을
    반드시 이 함수 하나로 통과시킨다. 백슬래시 구분자·`./` 접두·중복 슬래시·`..` 세그먼트를
    정규화하고, 레포 밖을 가리키거나 빈 경로가 되면 None을 돌려준다.
    """
    if not isinstance(raw, str):
        return None
    value = raw.strip().replace("\\", "/")
    if not value:
        return None
    value = value.lstrip("/")
    value = posixpath.normpath(value)
    if value in (".", "..") or value.startswith("../"):
        return None
    return value


def _parse_learning_candidates(done_text: str) -> list:
    """DONE.md `## 회고적 학습 후보` 절의 선언 경로를 읽는다(harness/done-template.md).

    형식 계약: 레포 루트 상대 POSIX 경로 1행 1건, 후보가 없으면 `없음` 한 줄. 경로 외 본문은
    이 절에 오지 않으므로, 목록 마커(`-`/`*`/`+`)와 인라인 코드 백틱만 벗겨 정규화한다.
    """
    candidates = []
    in_section = False
    for line in done_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip()
            in_section = heading == LEARNING_CANDIDATE_HEADING
            continue
        if not in_section or not stripped:
            continue
        entry = stripped
        for marker in ("- ", "* ", "+ "):
            if entry.startswith(marker):
                entry = entry[len(marker) :].strip()
                break
        entry = entry.strip("`").strip()
        if not entry or entry == "없음":
            continue
        normalized = _normalize_repo_relative(entry)
        if normalized and normalized not in candidates:
            candidates.append(normalized)
    return candidates


def _declared_attribution_paths(task_path: pathlib.Path) -> tuple:
    """선언 집합 D = DONE.md 선언 경로 ∪ 항상 선언된 귀속 산출물 3종. (D, DONE.md 존재 여부)."""
    done_file = task_path / DONE_FILE
    declared = []
    if done_file.is_file():
        try:
            declared = _parse_learning_candidates(done_file.read_text(encoding="utf-8"))
        except OSError:
            declared = []
    for always in ATTRIBUTION_ALWAYS_DECLARED:
        normalized = _normalize_repo_relative(always)
        if normalized and normalized not in declared:
            declared.append(normalized)
    return declared, done_file.is_file()


def _in_attribution_scope(path: str) -> bool:
    """판정 범위는 `.opal/brain/**`와 `.opal/MEMORY.json`뿐이다 — 소스·태스크 문서의 dirty는
    이 게이트의 판정 대상이 아니다(PLAN D-3b)."""
    return path == ATTRIBUTION_MEMORY_FILE or path.startswith(ATTRIBUTION_SCOPE_PREFIX)


def _observed_attribution_paths(wt_root: pathlib.Path) -> list:
    """관측 집합 S — `git status --porcelain -z -uall` 결과를 판정 범위로 필터한다.

    `-z`(NUL 구분)는 비ASCII 경로의 따옴표 감싸기를 구조적으로 없앤다(H-4). rename/copy
    엔트리(`R`/`C`)는 NUL 토큰 2개(신규 경로 다음에 원본 경로)를 쓰므로 양쪽 모두 관측
    대상으로 잡는다 — 선언된 page를 선언되지 않은 경로로 옮긴 변경을 놓치지 않기 위함이다.
    `-uall`은 미추적 디렉토리를 파일 단위로 펼쳐 `dir/` 표기가 판정에 섞이지 않게 한다.
    기존 이진 dirty 판정(`check_guards`)은 remove 경로 전용이며 여기서 쓰지 않는다.
    """
    result = _run_git(["status", "--porcelain", "-z", "-uall"], wt_root)
    if result.returncode != 0:
        raise GitFailure(result.stderr)
    tokens = [token for token in result.stdout.split("\0")]
    observed = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        index += 1
        if not token:
            continue
        # 각 엔트리는 `XY <path>` — 상태 코드 2글자 + 공백 1개 뒤가 경로다.
        if len(token) < 4 or token[2] != " ":
            continue
        status_code = token[:2]
        paths = [token[3:]]
        if "R" in status_code or "C" in status_code:
            if index < len(tokens):
                paths.append(tokens[index])
                index += 1
        for raw_path in paths:
            normalized = _normalize_repo_relative(raw_path)
            if not normalized or not _in_attribution_scope(normalized):
                continue
            if normalized not in observed:
                observed.append(normalized)
    return observed


def _memory_json_unallowed_diff_keys(wt_root: pathlib.Path) -> list:
    """`.opal/MEMORY.json`의 선행 diff에서 allocator의 `last_task_number` 외 변경 키를 돌려준다
    (제안서 §6.3). HEAD 사본이나 작업본을 JSON으로 읽을 수 없으면 판정 불능이므로 전체를
    위반으로 본다 — 조용한 통과를 만들지 않는다."""
    head = _run_git(["show", f"HEAD:{ATTRIBUTION_MEMORY_FILE}"], wt_root)
    if head.returncode != 0:
        return ["<untracked>"]
    try:
        before = json.loads(head.stdout)
        after = json.loads(
            (wt_root / ATTRIBUTION_MEMORY_FILE).read_text(encoding="utf-8")
        )
    except (json.JSONDecodeError, OSError):
        return ["<unparsable>"]
    if not isinstance(before, dict) or not isinstance(after, dict):
        return ["<not_an_object>"]
    changed = [
        key
        for key in sorted(set(before) | set(after))
        if before.get(key) != after.get(key)
    ]
    return [key for key in changed if key not in ATTRIBUTION_MEMORY_ALLOWED_DIFF_KEYS]


def _mark_requests_applied(task_path: pathlib.Path, applied: list) -> bool:
    """캡슐 파일의 해당 요청 `status`를 `applied`로 바꾼다(D-2b). 요청 "내용"은 캡슐 파일이,
    "처리 완료" 상태는 registry meta가 소유하므로 이 쓰기는 캡슐 쪽 표시일 뿐이다."""
    if not applied:
        return False
    request_file = task_path / MEMORY_INDEX_REQUEST_FILE
    if not request_file.is_file():
        return False
    try:
        doc = json.loads(request_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    if not isinstance(doc, dict):
        return False
    touched = False
    for request in doc.get("requests") or []:
        if isinstance(request, dict) and request.get("body_sha256") in applied:
            request["status"] = "applied"
            touched = True
    if touched:
        request_file.write_text(
            json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return touched


def _save_meta(project_root: pathlib.Path, task: str, meta: dict) -> None:
    write_meta_atomic(_meta_path(project_root, task), meta)


def cmd_finalize(args) -> None:
    """merge 후 귀속 후처리를 확정한다(제안서 §6.3, PLAN D-3b).

    `S ⊆ D`이면 재개를 허용하고, 아니면 `ATTRIBUTION_COMMIT_BLOCKED`로 위반 경로 목록과 함께
    거부한다. 상태 전이는 `completed_unmerged → attribution_pending → closed`이며, commit 생성이나
    clean 검증이 실패하면 `attribution_pending`에 머문다.
    """
    project_root = _resolve_project_root(args.project_root)
    meta = _load_meta(project_root, args.task)
    canonical_task_path, canonical_source = _resolve_canonical_task_path(
        project_root, meta
    )

    # 이미 `closed`면 귀속은 merge 전 브랜치 커밋으로 확정돼 있다 — 새 커밋을 만들지 않고
    # 멱등 반환한다(PLAN D-1b, AC-8 "재실행이 중복을 만들지 않는다"의 브랜치 커밋 축).
    if meta.get(ATTRIBUTION_STATE_KEY) == ATTRIBUTION_STATE_CLOSED:
        ok_response(
            command="finalize",
            task=args.task,
            state=ATTRIBUTION_STATE_CLOSED,
            previous_state=ATTRIBUTION_STATE_CLOSED,
            idempotent=True,
            committed=False,
            task_path=canonical_task_path or meta.get("task_path"),
            task_path_source=canonical_source,
            memory_index_requests_applied=[],
            memory_index_requests_resolved=list(
                meta.get("memory_index_requests_resolved") or []
            ),
        )
        return

    raw_task_path = meta.get("task_path")
    if not raw_task_path:
        err_response("TASK_PATH_MISSING", task=args.task, meta_path=str(_meta_path(project_root, args.task)))
    task_path = pathlib.Path(str(raw_task_path))
    wt_root = pathlib.Path(
        str(meta.get("task_home") or meta.get("worktree_root") or "")
    )
    if not wt_root or not wt_root.exists():
        err_response("WORKTREE_NOT_FOUND", path=str(wt_root))

    # ── (1) attribution_pending 진입 — 아래 검증이 하나라도 실패하면 이 상태에 머문다 ──
    previous_state = meta.get(ATTRIBUTION_STATE_KEY) or ATTRIBUTION_STATE_UNMERGED
    meta[ATTRIBUTION_STATE_KEY] = ATTRIBUTION_STATE_PENDING
    _save_meta(project_root, args.task, meta)

    declared, done_found = _declared_attribution_paths(task_path)
    try:
        observed = _observed_attribution_paths(wt_root)
    except GitFailure as exc:
        err_response(
            "GIT_COMMAND_FAILED",
            stderr=str(exc),
            state=ATTRIBUTION_STATE_PENDING,
        )

    # ── (2) S ⊆ D 판정 — 선언·관측 양쪽이 이미 같은 정규화를 통과했다 ──
    violations = [path for path in observed if path not in declared]
    if ATTRIBUTION_MEMORY_FILE in observed and ATTRIBUTION_MEMORY_FILE not in violations:
        unallowed = _memory_json_unallowed_diff_keys(wt_root)
        if unallowed:
            violations.append(ATTRIBUTION_MEMORY_FILE)
    if violations:
        err_response(
            "ATTRIBUTION_COMMIT_BLOCKED",
            task=args.task,
            state=ATTRIBUTION_STATE_PENDING,
            previous_state=previous_state,
            declared=declared,
            observed=observed,
            violations=violations,
            done_file=str(task_path / DONE_FILE),
            done_file_found=done_found,
        )

    # ── (3) 귀속 commit — 관측된 대상만 정확히 stage한다(사용자의 다른 변경은 건드리지 않는다) ──
    committed = False
    if observed:
        # observed 경로만 정확히 stage한다 — 사용자의 다른 미커밋 변경은 건드리지 않는다.
        # `-A`로 추가·수정·삭제를 함께 잡되 경로마다 따로 호출한다: rename으로 이미 staged
        # deletion이 된 원본 경로는 index·worktree 어디에도 없어 pathspec 불일치로 실패하는데
        # (실측), 그 변경은 이미 index에 있으므로 무시해도 커밋에 포함된다.
        for path in observed:
            add = _run_git(["add", "-A", "--", path], wt_root)
            if add.returncode != 0 and "did not match any files" not in add.stderr:
                err_response(
                    "ATTRIBUTION_COMMIT_FAILED",
                    state=ATTRIBUTION_STATE_PENDING,
                    stage="add",
                    path=path,
                    stderr=add.stderr,
                )
        commit = _run_git(
            ["commit", "-m", ATTRIBUTION_COMMIT_TEMPLATE.format(task=args.task), "--", *observed],
            wt_root,
        )
        if commit.returncode != 0:
            err_response(
                "ATTRIBUTION_COMMIT_FAILED",
                state=ATTRIBUTION_STATE_PENDING,
                stage="commit",
                stderr=commit.stderr,
            )
        committed = True

    # ── (4) clean 검증 — 전체 git status가 아니라 판정 범위의 잔여 0건만 확인한다 ──
    try:
        remaining = _observed_attribution_paths(wt_root)
    except GitFailure as exc:
        err_response(
            "GIT_COMMAND_FAILED", stderr=str(exc), state=ATTRIBUTION_STATE_PENDING
        )
    if remaining:
        err_response(
            "ATTRIBUTION_COMMIT_FAILED",
            state=ATTRIBUTION_STATE_PENDING,
            stage="clean",
            remaining=remaining,
        )

    # ── (5) 처리 완료 기록 — index row commit 확정 뒤에만 append한다(D-2b) ──
    applied = _pending_memory_index_requests(meta)
    resolved = list(meta.get("memory_index_requests_resolved") or [])
    for body_sha in applied:
        if body_sha not in resolved:
            resolved.append(body_sha)
    meta["memory_index_requests_resolved"] = resolved
    capsule_updated = _mark_requests_applied(task_path, applied)

    meta[ATTRIBUTION_STATE_KEY] = ATTRIBUTION_STATE_CLOSED
    _save_meta(project_root, args.task, meta)

    ok_response(
        command="finalize",
        task=args.task,
        state=ATTRIBUTION_STATE_CLOSED,
        previous_state=previous_state,
        idempotent=False,
        task_path=str(task_path),
        worktree_root=str(wt_root),
        declared=declared,
        observed=observed,
        violations=[],
        committed=committed,
        done_file_found=done_found,
        memory_index_requests_applied=applied,
        memory_index_requests_resolved=resolved,
        capsule_updated=capsule_updated,
    )


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="worktree_tool")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    p_create = subparsers.add_parser("create")
    p_create.add_argument("--project-root", required=True)
    p_create.add_argument("--task", required=True)
    p_create.add_argument("--slug", default=None)
    p_create.add_argument("--skill", default=None)
    p_create.add_argument("--task-folder", default=None, dest="task_folder")
    p_create.set_defaults(func=cmd_create)

    p_list = subparsers.add_parser("list")
    p_list.add_argument("--project-root", required=True)
    p_list.set_defaults(func=cmd_list)

    p_status = subparsers.add_parser("status")
    p_status.add_argument("--project-root", default=None)
    p_status.add_argument("--task", default=None)
    p_status.add_argument("--task-path", default=None, dest="task_path")
    p_status.set_defaults(func=cmd_status)

    p_ownership = subparsers.add_parser("ownership-set")
    p_ownership.add_argument("--project-root", default=None)
    p_ownership.add_argument("--task", default=None)
    p_ownership.add_argument("--task-path", default=None, dest="task_path")
    p_ownership.add_argument(
        "--execution-ownership", "--state", required=True, dest="execution_ownership"
    )
    p_ownership.add_argument(
        "--attribution-state", default=ATTRIBUTION_TOKEN_ACTIVE, dest="attribution_state"
    )
    p_ownership.add_argument("--generation", type=int, default=None)
    p_ownership.add_argument("--owner-session-id", default=None, dest="owner_session_id")
    p_ownership.add_argument("--adapter", default=None)
    p_ownership.add_argument("--adapter-handle", default=None, dest="adapter_handle")
    p_ownership.add_argument("--launch-receipt", default=None, dest="launch_receipt")
    p_ownership.add_argument("--prompt-receipt", default=None, dest="prompt_receipt")
    p_ownership.add_argument("--failure-reason", default=None, dest="failure_reason")
    p_ownership.add_argument(
        "--checkpoint-sha", action="append", default=None, dest="checkpoint_sha"
    )
    p_ownership.set_defaults(func=cmd_ownership_set)

    p_checkpoint = subparsers.add_parser("checkpoint")
    p_checkpoint.add_argument("--project-root", default=None)
    p_checkpoint.add_argument("--task", default=None)
    p_checkpoint.add_argument("--task-path", default=None, dest="task_path")
    p_checkpoint.add_argument("--worktree-root", default=None, dest="worktree_root")
    p_checkpoint.add_argument("--mode", required=True)
    p_checkpoint.add_argument("--stage", required=True)
    p_checkpoint.add_argument("--message", default=None)
    p_checkpoint.add_argument(
        "--owned-scope", action="append", default=None, dest="owned_scope"
    )
    p_checkpoint.add_argument("--git-command", default=None, dest="git_command")
    p_checkpoint.add_argument("--approved", action="store_true")
    p_checkpoint.set_defaults(func=cmd_checkpoint)

    p_remove = subparsers.add_parser("remove")
    p_remove.add_argument("--project-root", required=True)
    p_remove.add_argument("--task", required=True)
    p_remove.add_argument("--force", action="store_true")
    p_remove.set_defaults(func=cmd_remove)

    p_finalize = subparsers.add_parser("finalize")
    p_finalize.add_argument("--project-root", required=True)
    p_finalize.add_argument("--task", required=True)
    p_finalize.set_defaults(func=cmd_finalize)

    p_init = subparsers.add_parser("init")
    p_init.add_argument("--project-root", required=True)
    p_init.add_argument("--force", action="store_true")
    p_init.add_argument("--dry-run", action="store_true", dest="dry_run")
    p_init.set_defaults(func=cmd_init)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 — 트레이스백 유출 방지, 통제된 JSON으로 대체 (S-28)
        err_response("INTERNAL_ERROR", detail=str(exc))
