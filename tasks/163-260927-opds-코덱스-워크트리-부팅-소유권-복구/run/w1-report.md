# W-1 registry transition and lock report

## Result

- `ownership-set --owner-from-lease` now reads the lease while holding the registry lock and requires a live owner that matches `--expected-owner` and differs from `--exclude-owner`. Pending, absent, expired, unreadable, and ownerless leases return `owner_lease_unresolved`; changed or excluded owners return `owner_lease_mismatch`. Neither path writes the registry.
- Registry lock creation classifies `EACCES`, `EPERM`, and `EROFS` immediately as `registry_write_denied`; actual contention still uses the existing timeout result.
- `recovery_required` is an active-attribution execution state. It may be entered only from `session_launching`, retains terminal evidence (`terminal_creation`, adapter, handle, receipts, observed lease owner), and may return to `hub_owned` only with a failure reason. Confirmed `hub_owned` recovery clears the retained launch evidence.
- A registry already in `recovery_required` rejects direct transitions to `session_launching`, `worktree_session_owned`, and unreconciled `hub_owned`. Every `worktree_session_owned` transition now requires a non-empty final owner, whether supplied explicitly or resolved from the live lease.

## Consumer audit

| Consumer | Finding | Impact |
|---|---|---|
| `cmd_checkpoint` | Only `hub_owned` (with current lease) and `worktree_session_owned` (with matching registry owner) pass. | `recovery_required` remains denied. |
| `cmd_remove` terminal sweep | Reads the registry adapter field before removing a slot. | Preserved recovery adapter remains available for a cleanup attempt. |
| `cmd_status` | Emits the registry block without a closed state allow-list. | New state is reported without changing canonical-path behavior. |
| ownership tool resolver/hooks | Read registry metadata but do not validate this execution-state vocabulary. | No code change required in W-1 scope. |

## Verification

- `/Users/iskang/.opal/.venv/bin/python -m pytest opal/tools/worktree-tool/tests/test_worktree_tool.py::TestOwnershipSetRed opal/tools/worktree-tool/tests/test_worktree_tool.py::TestTask163LeaseOwnerRed -q` → `7 passed`
- `/Users/iskang/.opal/.venv/bin/python -m pytest opal/tools/worktree-tool/tests/test_worktree_tool.py::TestOwnershipSetRed opal/tools/worktree-tool/tests/test_worktree_tool.py::TestTask163LeaseOwnerRed opal/tools/worktree-tool/tests/test_worktree_tool.py::TestTask163OwnershipTransitions -q` → `9 passed`
- `/Users/iskang/.opal/.venv/bin/python -m py_compile opal/tools/worktree-tool/worktree_tool.py` → pass
- `git diff --check` → pass
- `test-tool scenario-coverage-build` and `scenario-coverage-check` → `all_covered: true`
