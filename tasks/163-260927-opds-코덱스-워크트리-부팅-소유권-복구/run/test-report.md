# Test report — Task 163

## Result

- Verdict: **All Pass** — all source and installed live scenarios have recorded evidence.
- Scenario state: locked; RED evidence is complete (6/6).
- Status count: pass 10, fail 0, blocked 0, awaiting_human 0.

## Scenario evidence

| Scenario | Status | Evidence |
|---|---|---|
| S-1 | PASS | `pytest TestTask163LeaseOwnerRed`: 2 passed; unresolved leases and hub-owner mismatch reject without mutation. |
| S-2 | PASS | Same focused worktree-tool run: live child succeeds and changed owner is rejected atomically. |
| S-3 | PASS | `pytest opal/tools/worktree-launcher/tests`: 155 passed, 4 skipped; timeout/recovery path covered. |
| S-4 | PASS | Approved installed Orca `show` and `list` checks ran. The closed probe handle remained observable as orphaned while the active task list contained a different handle, confirming that list omission alone cannot prove absence; source tests cover stale-plus-empty-list absence. |
| S-5 | PASS | Launcher suite covers guarded recovery, including residual foreign `handoff_pending` rejection. |
| S-6 | PASS | Approved isolated in-memory harness used the real current Codex ID, current cwd, installed `codex_adapter.start`, unmocked `_register_registry_owner`, and unmocked installed `ownership-set`. Real sandbox EPERM produced structured `registry_write_denied`; adapter returned `ok:true` and `registry_owner_deferred_to_hub` in 93.777ms. Registry and lease-owner SHA256 values were unchanged. Focused tests cover exact deferred and foreign-owner public branches. |
| S-7 | PASS | Launcher settings: 22 passed. Installer `TS-028` passed: old default migrates to `--no-daemon`; custom argv remains byte-identical. |
| S-8 | PASS | Installed `live-failure-probe.json`: `session_boot_timeout`, successful close, confirmed absence, and registry return to `hub_owned` at generation 2. Installed and source launcher hashes match. |
| S-9 | PASS | Installed launch succeeded. Fresh lease and registry both name child `01a0e2f5-873d-73c2-afa1-30f88f1e8a0d`; approved Orca show/list confirms `term_808e3d38-bf1d-452e-bada-2ddb9ea96884` is live. |
| S-10 | PASS | Installed registry checkpoint SHA and `git rev-parse HEAD` both equal `48f25a5aac77d320b4f491ddb938992acba50328`; `git show --stat` identifies the Task 162 checkpoint commit. |

## Regression and hygiene

- `pytest opal/tools/worktree-launcher/tests`: 155 passed, 4 skipped.
- `pytest opal/tools/ownership-tool/tests`: 167 passed.
- Focused `worktree-tool` Task 163 tests: 2 passed.
- `git diff --check`, JSON parsing of `opal/core/setting.default.json`, and `bash -n scripts/install-mac.sh`: passed.
- Installer regression script: Task 163 `TS-028` passed; unrelated existing `TS-025` and `TS-026` Claude-hook checks fail.
- Targeted changed-code secret scan found no secret material; `.gitignore` includes `.env`.

## Evidence artifact

Scenario SSOT: `test-scenario.json`, updated only through `test-tool scenario-mark`.

Live structured evidence: `run/s4-live-verdict.json`, `run/s6-live-verdict.json`, `run/s8-live-verdict.json`, `run/s9-live-verdict.json`, and `run/s10-live-verdict.json`.
