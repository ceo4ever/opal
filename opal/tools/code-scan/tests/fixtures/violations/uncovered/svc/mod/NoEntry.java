package svc.mod;
// fixture: uncovered:no_entry — present on disk, NOT listed in manifest "files", no inline
// @-header (no real header block) either. Also expected to co-trigger worker_scope_violation:files_key_removed
// (dual detection is contractually allowed per PLAN §3.7.2).
public class NoEntry {}
