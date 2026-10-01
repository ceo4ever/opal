---
template: sdlc-v2
---
# TASK: --wt 워크트리 세션으로의 태스크 소유권 이관 계약

## Problem

`--wt`로 시작한 태스크를 전용 워크트리 세션이 이어받지 못하고 첫 쓰기에서 전건 차단된다.
태스크 149에서 실측 재현됐다.

발생 경로는 `harness/task-process.md` §오케스트레이터 공통 영역이 정한 순서 자체에 있다.
허브가 스텝 5(`state init`) 직후 TASK 행을 `mark`하는데, `state_tool.py:728`의
`_claim_task_lease_if_needed()`가 그 전이에서 `lease.claim(claim_source="state_transition")`으로
`<task>/run/.runtime/owner.json`을 만든다. 그 다음 스텝 5.5에서 워크트리 터미널이 뜨고,
워크트리 세션의 SessionStart가 `lease.claim(claim_source="session_start")`을 호출하지만
허브 lease가 live라 `foreign_owner`로 거절된다(`lease.py:141-147`). 즉 허브가 먼저 소유하고
나서 실행 주체를 띄우는 순서라 **실행 주체가 구조적으로 소유권을 받을 수 없다**.

거절의 부작용이 세 겹으로 누적된다.

1. `session_start_hook.py:241-250`은 claim 성공 분기 안에서만 `_register_registry_owner`를
   호출하므로, registry의 `execution_ownership.state`는 `worktree_session_owned`인데
   `owner_session_id`는 `null`로 남는다. 실행 주체가 어느 세션인지 아무도 모른다.
2. `pretooluse_guard_hook.py:158-190`이 `foreign_owner`에서 Edit·Write·NotebookEdit을 전건,
   Bash를 분류된 쓰기 서브명령 단위로 차단한다. 워크트리 세션은 산출물은 물론
   `AGENTIC-LOG.md` 기록과 `state-tool block`까지 못 해서 자기 상태를 남길 수단이 없다.
3. 해제 수단이 없다. `opal/tools/ownership-tool/run.sh`는 `{"error":"not_implemented"}`를
   반환해 CLI 표면이 없고, `lease.release`를 호출하는 곳은 SessionEnd 훅 하나뿐이다.
   허브 세션의 PostToolUse heartbeat가 lease를 매 턴 갱신하므로(`heartbeat_hook.py:131-145`,
   149에서 `lease_expires_at`이 `17:47:27 → 17:58:50`으로 이동함을 실측) TTL 만료도 오지 않는다.
   남은 해소 경로는 허브 세션 종료 하나뿐이다.

근본 원인은 계약 부재다. `opal/core/references/harness/` 전체에 `lease` 언급이 0건이라
(`grep -rln lease opal/core/references/harness/`) 소유권을 언제 누가 잡고 언제 넘기는지
문서에 정의된 적이 없고, 도구만 각자 claim한다.

이 결함은 태스크 138에서 만든 가드가 2026-09-20 21:23 install로 배포된 뒤 첫 `--wt`
태스크인 149에서 처음 드러났다. 그 전 `--wt` 태스크(141~148)는 같은 lease를 만들었지만
집행하는 가드가 배포되지 않아 통과했을 뿐, 순서 결함 자체는 그때도 있었다.

## Proposed outcome

- `--wt`로 시작한 태스크의 전용 워크트리 세션이 부팅 직후 PLAN부터 CLOSE까지 쓰기를
  차단당하지 않고 진행한다. 허브 세션을 종료하거나 TTL을 기다릴 필요가 없다.
- registry만 보면 지금 그 태스크를 실행 중인 세션이 누구인지 알 수 있다.
- 소유권이 남은 태스크를 명령 한 줄로 조회하고 해제할 수 있다. 태스크 149처럼 이미
  잠긴 태스크도 이 명령으로 풀린다.
- 소유권을 언제 누가 잡고 언제 넘기는지가 harness 문서에 기록되어, 다음에 이 순서를
  건드리는 사람이 계약을 읽고 판단한다.

## Affected users and systems

- 영향받는 사용자: `--wt`를 쓰는 모든 OPAL 사용자. 현재 전원이 워크트리 세션 실행 불가 상태다.
- 영향받는 시스템: `opal/tools/ownership-tool`(lease·hook 어댑터·CLI 표면),
  `opal/tools/worktree-launcher`(기동 성공 시 이관 지점), `opal/tools/worktree-tool`
  (`ownership-set` registry 기록), `opal/core/references/harness/`(계약 문서),
  `harness/task-process.md` 스텝 5·5.5 순서 기술.
- 범위 제외: 태스크 149가 다루는 훅 런타임 루트(cwd) 해석 결함, 비 `--wt` 태스크의 소유권
  동작, PreToolUse 가드의 차단 대상 도구 목록 변경, Stop 판정 로직.

## Constraints

- C-1: 훅의 fail-safe를 유지한다. 전 경로 `except Exception: pass` + `exit 0`이며 소유권
  해석 실패가 세션을 차단하지 않는다.
- C-2: 가드의 차단 자체를 약화하지 않는다. 소유하지 않은 세션이 남의 태스크를 쓰는 것은
  계속 막혀야 한다. 이관은 소유권을 **옮기는** 것이지 검사를 끄는 것이 아니다.
- C-3: live lease를 가진 세션의 소유권을 제3자가 빼앗는 경로를 만들지 않는다. 이전은
  현 소유자의 명시 해제 또는 만료를 거친다.
- C-4: `harness/worktree.md` §task root와 allocator root 계약을 약화하지 않는다.
  `allocator_root`를 cwd·task path 조상·`.opal-worktrees` 문자열로 추론하지 않는다.
- C-5: `CLAUDE_` 접두 환경변수명은 `claude_adapter.py`에만 둔다(C-15 기존 계약).
- C-6: `--wt` 미사용 경로의 동작을 바꾸지 않는다. 비워크트리 태스크의 소유권 동작과
  `state.json` 스키마는 현행과 동일하다.
- C-7: 기존 ownership-tool·worktree-tool·worktree-launcher 테스트 전건이 통과 상태를 유지한다.
- C-8: `~/.opal/` 배포본을 직접 수정하지 않는다. 프로젝트 소스를 고치고 install로 배포한다.

## Acceptance criteria

- AC-1: 허브가 `--wt` 태스크의 lease를 보유한 상태에서 워크트리 터미널을 기동하면, 기동
  성공 시점에 그 태스크의 lease가 허브 소유로 남아 있지 않다.
- AC-2: 기동 후 워크트리 세션이 `state-tool advance`와 산출물 파일 쓰기를 수행할 때
  PreToolUse 가드가 `foreign_owner`로 차단하지 않는다.
- AC-3: 기동 성공 후 registry의 `execution_ownership.owner_session_id`가 `null`이 아니라
  실제 워크트리 세션 id다.
- AC-4: 워크트리 세션의 SessionStart claim이 실패하는 경우에도 registry 소유자 등록이
  수행되거나, 등록되지 않은 사유가 진단으로 남는다.
- AC-5: `ownership-tool run.sh`가 `not_implemented`를 반환하지 않고, 태스크의 현재 소유권을
  조회하는 서브명령과 해제하는 서브명령을 제공한다.
- AC-6: 해제 서브명령으로 태스크 149의 `run/.runtime/owner.json`을 해제하면, 그 뒤 다른
  세션이 같은 태스크를 claim할 수 있다.
- AC-7: 해제 서브명령은 현 소유자가 아닌 세션의 요청을 거부하며, 거부 사유를 구조화 출력한다.
- AC-8: `opal/core/references/harness/`에 소유권 획득 시점·이관 시점·해제 경로·가드 적용
  범위를 정의한 절이 존재하고, `grep -rln lease opal/core/references/harness/`가 1건 이상이다.
- AC-9: `harness/task-process.md` 스텝 5·5.5 기술이 이관 시점을 포함하도록 갱신되어,
  허브가 lease를 잡은 뒤 기동한다는 현행 순서와 이관 지점이 문서에서 일치한다.
- AC-10: `--wt` 없이 생성한 태스크의 `state.json`과 소유권 동작이 변경 전과 동일하다.
- AC-11: ownership-tool·worktree-tool·worktree-launcher 테스트 전건과
  `scripts/tests/test_hook_parity.py`가 통과한다.
- AC-12: 배포 영향 항목이 install 스크립트에 반영되어, install 후 새 `--wt` 태스크가
  AC-1~AC-3을 만족한다.

## Open questions

- 이관 실행 지점을 `worktree-launcher launch` 성공 경로로 둘지, `task-process` 스텝 5.5의
  별도 명령으로 둘지는 PLAN에서 결정한다. 전자는 기동과 이관이 원자적으로 묶이지만
  launcher가 lease를 알게 되고, 후자는 책임 분리가 명확하지만 호출자가 순서를 지켜야 한다.
- 기동 시점에는 워크트리 세션 id를 알 수 없으므로 AC-1을 "해제 후 무소유 상태로 넘김"으로
  구현할지, "예약 소유자"를 두는 모델로 구현할지는 PLAN에서 결정한다.
