"""Install Task 163's changed OPAL components without touching user settings.

The normal all-component installer replaces unrelated tool directories and
migrates setting.json. This scoped installer copies only the runtime files
needed for the worktree boot fix, backs up each installed file, and verifies
that the personal setting file is byte-for-byte unchanged.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile


PROJECT = Path(__file__).resolve().parents[3]
OPAL = Path("/Users/iskang/.opal")
SETTING = OPAL / "setting.json"
PAIRS = (
    ("opal/tools/worktree-tool/worktree_tool.py", "tools/worktree-tool/worktree_tool.py"),
    ("opal/tools/worktree-tool/schema/worktree.schema.json", "tools/worktree-tool/schema/worktree.schema.json"),
    ("opal/tools/worktree-tool/README.md", "tools/worktree-tool/README.md"),
    ("opal/tools/ownership-tool/ownership_tool/ownership_core.py", "tools/ownership-tool/ownership_tool/ownership_core.py"),
    ("opal/tools/ownership-tool/ownership_tool/session_start_hook.py", "tools/ownership-tool/ownership_tool/session_start_hook.py"),
    ("opal/tools/ownership-tool/ownership_tool/codex_adapter.py", "tools/ownership-tool/ownership_tool/codex_adapter.py"),
    ("opal/tools/ownership-tool/README.md", "tools/ownership-tool/README.md"),
    ("opal/tools/worktree-launcher/worktree_launcher/launcher_core.py", "tools/worktree-launcher/worktree_launcher/launcher_core.py"),
    ("opal/tools/worktree-launcher/worktree_launcher/cli.py", "tools/worktree-launcher/worktree_launcher/cli.py"),
    ("opal/tools/worktree-launcher/worktree_launcher/settings.py", "tools/worktree-launcher/worktree_launcher/settings.py"),
    ("opal/tools/worktree-launcher/worktree_launcher/adapters/orca.py", "tools/worktree-launcher/worktree_launcher/adapters/orca.py"),
    ("opal/tools/worktree-launcher/README.md", "tools/worktree-launcher/README.md"),
    ("opal/core/references/harness/worktree.md", "references/harness/worktree.md"),
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    setting_before = SETTING.read_bytes()
    backup = Path(tempfile.mkdtemp(prefix="task163-opal-backup-"))
    records = []
    for source_rel, destination_rel in PAIRS:
        source = PROJECT / source_rel
        destination = OPAL / destination_rel
        if not source.is_file() or not destination.is_file():
            raise RuntimeError(f"source_or_destination_missing: {source} {destination}")
        old = destination.read_bytes()
        new = source.read_bytes()
        backup_file = backup / destination_rel
        backup_file.parent.mkdir(parents=True, exist_ok=True)
        backup_file.write_bytes(old)
        records.append((source, destination, old, new))

    installed = []
    try:
        for source, destination, old, new in records:
            fd, temp_path = tempfile.mkstemp(prefix=".task163-", dir=destination.parent)
            try:
                with os.fdopen(fd, "wb") as stream:
                    stream.write(new)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.chmod(temp_path, destination.stat().st_mode & 0o777)
                os.replace(temp_path, destination)
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            installed.append(destination)
            if destination.read_bytes() != new:
                raise RuntimeError(f"installed_hash_mismatch: {destination}")
        if SETTING.read_bytes() != setting_before:
            raise RuntimeError("personal_setting_changed")
    except Exception:
        for destination in reversed(installed):
            relative = destination.relative_to(OPAL)
            shutil.copy2(backup / relative, destination)
        raise

    receipt = {
        "backup": str(backup),
        "setting_sha256_unchanged": digest(setting_before),
        "files": [
            {
                "source": str(source),
                "installed": str(destination),
                "before_sha256": digest(old),
                "after_sha256": digest(new),
            }
            for source, destination, old, new in records
        ],
    }
    output = Path(__file__).with_name("install-receipt.json")
    output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "backup": str(backup), "files": len(records), "setting_unchanged": True}))


if __name__ == "__main__":
    main()
