# @header
# module: worktree_launcher.tests.conftest
# layer: test
# domain: worktree-launcher
# description: worktree-launcher 테스트 공용 헬퍼. ownership-tool fixtures/launcher의 `{HUB}`/`{WT}` 플레이스홀더를 fixtures/README.md 계약대로 tmp 경로로 치환해 읽고, W-11(worktree_tool.cmd_ownership_set)이 소유한 registry v2 스키마와 동형인 `<hub>/.opal-worktrees/.meta/task_{NNN}.json`을 실물 동형 레이아웃(`<hub>/.opal-worktrees/task_{NNN}/`, 워크트리 안에 `.opal-worktrees` 없음)으로 tmp_path 안에 직접 배치한다. worktree_tool.py는 import하지 않고 스키마만 대조 참조한다(worktree_tool.py:936-948 `_execution_ownership_origin`, :1765-1786 `cmd_ownership_set` 블록 조립, :121 `ATTRIBUTION_TOKEN_ACTIVE`=키 부재 관례).
# exports: FIXTURES_ROOT, load_launcher_fixture, LauncherHub, build_launcher_hub, read_meta
# depends: opal/tools/ownership-tool/tests/fixtures/launcher/**, opal/tools/ownership-tool/tests/fixtures/README.md
"""worktree-launcher pytest 공용 헬퍼 — 구현 모듈(worktree_launcher)은 소유하지 않는다.

RED-first 트랙에서 launcher_core.run()·adapters.*는 아직 없다(ModuleNotFoundError가 정상).
이 conftest는 그 모듈이 GREEN으로 채워졌을 때 대조해야 할 **registry 실물 스키마**와
**fixture 플레이스홀더 치환**만 미리 고정해 둔다 — import는 각 테스트 함수 첫 줄에서
수행해 어떤 셋업 오류도 ModuleNotFoundError보다 먼저 관측되지 않게 한다.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

FIXTURES_ROOT = (
    Path(__file__).parent.parent.parent / "ownership-tool" / "tests" / "fixtures" / "launcher"
)


def load_launcher_fixture(name: str, hub: Path, wt_parent: Path) -> dict:
    """`fixtures/launcher/<name>`을 읽어 `{HUB}`→hub, `{WT}`→wt_parent로 치환한 뒤 파싱한다
    (fixtures/README.md §플레이스홀더 규약). 원본 fixture 파일은 절대 수정하지 않는다 —
    텍스트를 메모리에서 치환할 뿐이다."""
    text = (FIXTURES_ROOT / name).read_text(encoding="utf-8")
    text = text.replace("{HUB}", str(hub)).replace("{WT}", str(wt_parent))
    return json.loads(text)


@dataclass
class LauncherHub:
    hub: Path
    wt_parent: Path
    worktree_root: Path
    meta_path: Path
    task: str


def _execution_ownership_block(state: str, generation: int, adapter: str | None) -> dict:
    """`execution_ownership` 하위 9필드 — worktree_tool.py의 `_execution_ownership_origin`
    (:936-948)과 `cmd_ownership_set`의 block 조립(:1765-1780)이 쓰는 필드 집합과 동형이다."""
    return {
        "state": state,
        "owner_session_id": "session-launcher-red" if state == "session_launching" else None,
        "adapter": adapter,
        "adapter_handle": None,
        "generation": generation,
        "launch_receipt": None,
        "prompt_receipt": None,
        "failure_reason": None,
        "checkpoint_shas": [],
    }


def build_launcher_hub(
    tmp_path: Path,
    task: str = "220",
    prior_state: str = "session_launching",
    prior_generation: int = 1,
    adapter: str = "generic",
) -> LauncherHub:
    """실물 동형 레이아웃으로 tmp 허브를 조립한다.

    - `worktree_root` = `<hub>/.opal-worktrees/task_{task}/` — 워크트리 **안**에는
      `.opal-worktrees`를 만들지 않는다.
    - registry v2 메타를 `<hub>/.opal-worktrees/.meta/task_{task}.json`에 직접 배치한다
      (`worktree-tool create`의 실 git 셋업 없이 스키마만 동형으로 재현 — PLAN 138 완료 기준
      B-2가 허용한 두 방식 중 경량 대안).
    - `attribution_state` 키는 만들지 않는다(active = 키 부재, worktree_tool.py:121).
    """
    hub = tmp_path / "hub"
    wt_parent = hub / ".opal-worktrees"
    worktree_root = wt_parent / f"task_{task}"
    worktree_root.mkdir(parents=True)
    meta_dir = wt_parent / ".meta"
    meta_dir.mkdir(parents=True)
    meta_path = meta_dir / f"task_{task}.json"

    branch = f"feat/OP-TASK-{task}"
    meta = {
        "task": task,
        "layout": "monorepo",
        "branch": branch,
        "created_at": "2026-09-17 10:00",
        "worktree_root": str(worktree_root),
        "entries": [
            {
                "repo": str(hub),
                "path": str(worktree_root),
                "branch": branch,
                "base_ref": "main",
            }
        ],
        "pending_setup": [],
        "allocator_root": str(hub),
        "task_home": str(worktree_root),
        "task_folder": None,
        "task_path": None,
        "artifact_repo": ".",
        "task_ownership_version": 2,
        "memory_index_requests_resolved": [],
        "execution_ownership": _execution_ownership_block(
            prior_state, prior_generation, adapter
        ),
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return LauncherHub(
        hub=hub,
        wt_parent=wt_parent,
        worktree_root=worktree_root,
        meta_path=meta_path,
        task=task,
    )


def read_meta(meta_path: Path) -> dict:
    return json.loads(meta_path.read_text(encoding="utf-8"))
