"""
@header {
  "module": "test_event_loader_worktree_root",
  "layer": "test",
  "domain": "opal-tools",
  "description": "event-loader `_roots()`의 project_root 판정 계약(D-6) — worktree cwd에서 경로 세그먼트로 허브에 수렴하지 않고 `.git`+`.opal/AGENT.md`를 함께 가진 자기 조상(task root)을 반환한다. 공개 CLI(run.sh)의 stdout JSON error.path 필드로만 판정한다(내부 헬퍼를 직접 호출하지 않음, 기존 test_event_loader.py 관례 준용).",
  "task": "118",
  "scenarios": ["S-17"],
  "exports": ["TestWorktreeProjectRootResolution"]
}

TASK 118 D-6 계약 회귀 스위트.
디스포저블 git clone + `git worktree add` + `sparse-checkout init --cone`으로
`/private/tmp` 하위에 워크트리 픽스처를 만들고, 그 cwd에서 event-loader CLI를
`--project-root` 없이 호출해 `pm.activate`의 필수 문서
`project-agent = {project_root}/.opal/AGENT.md`가 어느 절대경로로 해석되는지
`document_not_found` 에러의 `path` 필드로 관측한다. `pm.activate`를 쓰는 이유는
이 이벤트만 유일하게 `project` root 토큰 문서를 선언하기 때문이다
(worker.dispatch/session.assistant는 source/deployed 변형만 가짐).

계약 구분(TASK.md C-1):
- test_project_root_worktree_own_opal_not_hub: D-6 본계약 — 워크트리 자신이
  `.git`과 `.opal/AGENT.md`를 함께 가지면 project_root는 그 워크트리 자신이며,
  경로에 `.opal-worktrees` 세그먼트가 있다는 이유로 허브에 수렴하지 않는다.
- test_project_root_no_opal_ancestor_stays_within_repo: 회귀 보호 — `.opal`
  조상이 전혀 없으면 `$HOME/.opal`로 탈출하지 않고 cwd 자신에 머문다. 현재도
  이미 성립하므로 구현 전에도 통과해야 정상이다.
- test_explicit_project_root_skips_search: 회귀 보호 — `--project-root` 명시 시
  탐색 없이 그 값을 그대로 쓴다. 현재도 이미 성립하므로 구현 전에도 통과해야
  정상이다.
"""

import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest


_TOOL_DIR = pathlib.Path(__file__).parent.parent
_EVENT_LOADER_PY = _TOOL_DIR / "event_loader.py"
_HUB_ROOT = _TOOL_DIR.parents[2]


def _run_from(cwd, args):
    """event_loader.py를 지정 cwd에서 직접 실행하고 (returncode, payload)를 반환."""
    result = subprocess.run(
        ["python3", str(_EVENT_LOADER_PY), *args],
        capture_output=True,
        text=True,
        cwd=str(cwd),
    )
    stdout = result.stdout.strip()
    try:
        payload = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        payload = {"_raw": stdout}
    return result, payload


def _git(args, cwd=None, check=True):
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=check,
    )


@unittest.skipUnless(shutil.which("git"), "git CLI가 필요하다")
class TestWorktreeProjectRootResolution(unittest.TestCase):
    """S-17 — event-loader `_roots()`가 `--project-root` 미지정 시 cwd에서
    `.git`+`.opal/AGENT.md`를 함께 가진 자기 조상(워크트리 루트)을 반환해야 한다.
    disposable git clone(+worktree, sparse-checkout cone)을 `/private/tmp`
    하위에서만 만들고 테스트 종료 시 제거한다(C-8·TASK.md C-3·C-8)."""

    def setUp(self):
        # [MUST][TASK.md C-3·C-8] disposable git fixture는 /private/tmp 하위에만 만든다.
        self._tmpdir = tempfile.mkdtemp(prefix="test_s17_event_loader_", dir="/private/tmp")
        self.base = pathlib.Path(self._tmpdir) / "base"
        _git(["clone", "--no-hardlinks", "--quiet", str(_HUB_ROOT), str(self.base)])
        self.worktree = self.base / ".opal-worktrees" / "task_s17fixture"
        (self.base / ".opal-worktrees").mkdir(parents=True, exist_ok=True)
        _git(
            ["worktree", "add", "--quiet", "-b", "op118-s17-fixture",
             str(self.worktree), "HEAD"],
            cwd=str(self.base),
        )

    def tearDown(self):
        _git(["worktree", "remove", "--force", str(self.worktree)],
             cwd=str(self.base), check=False)
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def _set_cone(self, *patterns):
        _git(["sparse-checkout", "init", "--cone"], cwd=str(self.worktree))
        _git(["sparse-checkout", "set", *patterns], cwd=str(self.worktree))

    def test_project_root_worktree_own_opal_not_hub(self):
        """[T118][S-17] cone에 `.opal`을 포함해 워크트리 자신이 `.opal/AGENT.md`를
        가지면, project_root는 그 워크트리 자신이어야 하고 허브로 수렴돼서는 안 된다.

        계약(D-6): project_root 판정은 cwd 경로의 `.opal-worktrees` 세그먼트를
        근거로 쓰지 않고, `.git`과 `.opal/AGENT.md`를 함께 가진 가장 가까운
        조상(task root)을 반환한다. 따라서 `pm.activate`의 `project-agent` 문서는
        허브(`<base>/.opal/AGENT.md`)가 아니라 워크트리 자신의 경로로 해석된다.
        원문: opal/core/references/harness/worktree.md §task root와 allocator root 계약.
        """
        # `docs`도 cone에 넣는다 — pm.activate의 필수 문서에 `docs/PROJECT.md`(project-registry)가
        # 포함돼 있어, 빠지면 project-agent 판정 전에 문서 부재로 먼저 실패한다(픽스처 setup 결함
        # 보정. 아래 단언은 변경하지 않는다 — red-first §1.5 (5)).
        self._set_cone("opal", "tasks", ".opal", "docs")
        self.assertTrue(
            (self.worktree / ".opal" / "AGENT.md").is_file(),
            "픽스처 설정 오류 — 워크트리 자신의 .opal/AGENT.md가 실체화되지 않았다",
        )

        result, payload = _run_from(self.worktree, ["load", "--event", "pm.activate"])

        expected_path = str((self.worktree / ".opal" / "AGENT.md").resolve())
        hub_path = str((self.base / ".opal" / "AGENT.md").resolve())

        if payload.get("ok"):
            documents = {d["id"]: d["path"] for d in payload.get("documents", [])}
            actual_path = documents.get("project-agent")
        else:
            # docs/PROJECT.md 등 다른 필수 문서가 cone 밖이라 먼저 실패할 수도
            # 있으므로, project-agent 자체의 시도 경로가 아니면 해당 실패는
            # 이 단언의 판정 대상이 아니다(document_not_found의 path 필드로 판정).
            actual_path = payload.get("path") if payload.get("document") == "project-agent" else None
            if actual_path is None:
                self.fail(
                    "project-agent 문서 해석 경로를 관측하지 못했다 — "
                    f"exit={result.returncode} payload={payload!r}"
                )

        self.assertEqual(
            actual_path, expected_path,
            f"[FIX-PIN S-17] project_root가 워크트리 자신이 아니라 다른 경로로 "
            f"해석됐다 — actual={actual_path!r} expected(worktree)={expected_path!r} "
            f"hub={hub_path!r}",
        )
        self.assertNotEqual(
            actual_path, hub_path,
            "[FIX-PIN S-17] project_root가 허브로 수렴했다 — "
            "`.opal-worktrees` 세그먼트 우선 분기(D-6 제거 대상)가 여전히 동작 중이다",
        )

    def test_project_root_no_opal_ancestor_stays_within_repo(self):
        """[회귀 보호][S-17] `.opal` 조상이 전혀 없으면 `$HOME/.opal`로 탈출하지
        않고 cwd 자신(또는 저장소 경계 안)에 머문다. 현재도 이미 성립하므로
        구현 전에도 통과해야 정상이다(TASK.md C-1)."""
        no_opal_dir = pathlib.Path(self._tmpdir) / "no_opal_repo" / "sub" / "dir"
        no_opal_dir.mkdir(parents=True)
        _git(["init", "--quiet"], cwd=str(pathlib.Path(self._tmpdir) / "no_opal_repo"))

        result, payload = _run_from(no_opal_dir, ["load", "--event", "pm.activate"])
        self.assertFalse(payload.get("ok", False))
        self.assertEqual(payload.get("document"), "project-agent")
        attempted_path = payload.get("path", "")

        home_opal = str(pathlib.Path("~/.opal").expanduser())
        self.assertFalse(
            attempted_path.startswith(home_opal),
            f"[FIX-PIN S-17] project_root가 $HOME/.opal로 탈출했다 — path={attempted_path!r}",
        )
        self.assertTrue(
            attempted_path.startswith(str(no_opal_dir.resolve())),
            f"[FIX-PIN S-17] project_root가 저장소 경계(cwd) 밖으로 나갔다 — "
            f"path={attempted_path!r} cwd={no_opal_dir!r}",
        )

    def test_explicit_project_root_skips_search(self):
        """[회귀 보호][S-17] `--project-root`를 명시하면 조상 탐색 없이 그 값을
        그대로 쓴다. 현재도 이미 성립하므로 구현 전에도 통과해야 정상이다."""
        self._set_cone("opal", "tasks")  # .opal을 cone에서 뺀다 — 탐색됐다면 실패할 상황
        explicit_root = str(self.worktree)

        result, payload = _run_from(
            self.worktree,
            ["load", "--event", "pm.activate", "--project-root", explicit_root],
        )
        self.assertFalse(payload.get("ok", False))
        self.assertEqual(payload.get("document"), "project-agent")
        expected_path = str((self.worktree / ".opal" / "AGENT.md").resolve())
        self.assertEqual(
            payload.get("path"), expected_path,
            "[FIX-PIN S-17] --project-root 명시값이 탐색 결과로 대체됐다",
        )


if __name__ == "__main__":
    unittest.main()
