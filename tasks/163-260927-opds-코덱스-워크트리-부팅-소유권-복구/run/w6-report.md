# W-6 integration report

```json
{
  "artifact_path": "tasks/163-260927-opds-코덱스-워크트리-부팅-소유권-복구/run/w6-report.md",
  "summary": "Added cross-tool launcher integration coverage for a real hub lease handoff, child Codex claim, atomic registry owner confirmation, unknown-terminal recovery, and duplicate-launch rejection. Updated the explicit-owner handoff tests to prove the final registry owner is the claimed child session and to require confirmed terminal absence before hub recovery.",
  "status": "completed",
  "blockers": [],
  "changed_files": [
    "opal/tools/worktree-launcher/tests/test_integration.py",
    "opal/tools/worktree-launcher/tests/test_codex_handoff.py",
    "tasks/163-260927-opds-코덱스-워크트리-부팅-소유권-복구/run/w6-report.md"
  ]
}
```

## Source verification

Executed:

```bash
/Users/iskang/.opal/.venv/bin/python -m pytest -q \
  opal/tools/worktree-launcher/tests/test_integration.py \
  opal/tools/worktree-launcher/tests/test_codex_handoff.py
git diff --check -- \
  opal/tools/worktree-launcher/tests/test_integration.py \
  opal/tools/worktree-launcher/tests/test_codex_handoff.py
```

Result: `5 passed in 1.85s`; `git diff --check` completed without output.

The success test uses a temporary canonical task path and real
`ownership_tool.lease.claim()` calls: hub lease → launcher public handoff →
child claim from the issued worktree root → public `worktree-tool
ownership-set`. It asserts that the registry owner is the child ID. The
failure tests retain `recovery_required` if the adapter supplied no handle,
and permit `hub_owned` only after a close plus status evidence reports absent.

## Prepared installed verification commands (read-only)

Run these only after the approved installation and after the actual task path
and child session ID are observed from the launch result. They do not launch,
close, recover, install, or change task 162 state.

```bash
~/.opal/tools/worktree-tool/run.sh status \
  --project-root /Volumes/Data/AIStudio/workspace/ai-framework \
  --task 162

~/.opal/tools/ownership-tool/run.sh status \
  --task-path '<issued task_162 task_path from the status JSON>' \
  --session-id '<child session ID from the successful launch JSON>'

orca terminal show --terminal '<adapter_handle from the successful launch JSON>' --json
orca terminal list --worktree 'path:<issued task_162 worktree_root from the status JSON>' --json
```

Expected evidence for a successful boot is the same child ID in the ownership
lease and registry `execution_ownership.owner_session_id`; terminal commands
are observational only.
