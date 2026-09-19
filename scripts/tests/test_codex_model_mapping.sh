#!/usr/bin/env bash
# Codex 모델 세대 교체와 기존 setting.json 안전 마이그레이션 회귀 테스트.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
MAC_SCRIPT="$REPO_ROOT/scripts/install-mac.sh"
WIN_SCRIPT="$REPO_ROOT/scripts/install/windows.ps1"
DEFAULT_SETTING="$REPO_ROOT/opal/core/setting.default.json"

python3 - "$MAC_SCRIPT" "$WIN_SCRIPT" "$DEFAULT_SETTING" <<'PYTEST'
import json
import pathlib
import subprocess
import sys
import tempfile

mac_path, win_path, default_path = map(pathlib.Path, sys.argv[1:])
mac = mac_path.read_text(encoding="utf-8")
win = win_path.read_text(encoding="utf-8")
default = json.loads(default_path.read_text(encoding="utf-8"))

expected = {
    "light": "gpt-5.6-luna",
    "standard": "gpt-5.6-terra",
    "advanced": "gpt-5.6-sol",
}
assert default["models"]["codex"] == expected

start_marker = 'python3 - "$src" "$dst" <<\'PYEOF\' || warn "setting.json scaffold 병합/승격 실패 — 기존 파일 유지"\n'
start = mac.index(start_marker) + len(start_marker)
end = mac.index("\nPYEOF", start)
migration_program = mac[start:end]


def migrate(existing):
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        src = root / "setting.default.json"
        dst = root / "setting.json"
        src.write_text(json.dumps(default, ensure_ascii=False), encoding="utf-8")
        original = json.dumps(existing, ensure_ascii=False, indent=2) + "\n"
        dst.write_text(original, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "-", str(src), str(dst)],
            input=migration_program,
            text=True,
            capture_output=True,
            check=True,
        )
        return json.loads(dst.read_text(encoding="utf-8")), original, dst.read_text(encoding="utf-8"), result.stderr


legacy = {
    "bootstrap": "on",
    "models": {
        "codex": {
            "light": "gpt-5.4-mini",
            "standard": "gpt-5.4",
            "advanced": "gpt-5.5",
        },
        "claude": {"advanced": "custom-opus"},
    },
}
migrated, _, _, stderr = migrate(legacy)
assert migrated["models"]["codex"] == expected
assert migrated["models"]["claude"]["advanced"] == "custom-opus"
assert migrated["bootstrap"] == "on"
assert "이전 Codex 기본값 승격 완료" in stderr

mixed = {
    "models": {
        "codex": {
            "light": "my-fast-model",
            "standard": "gpt-5.4",
            "advanced": "gpt-6-astra",
        }
    }
}
migrated, _, _, _ = migrate(mixed)
assert migrated["models"]["codex"] == {
    "light": "my-fast-model",
    "standard": "gpt-5.6-terra",
    "advanced": "gpt-6-astra",
}

current = json.loads(json.dumps(default))
_, before, after, stderr = migrate(current)
assert before == after
assert "무변 (멱등)" in stderr

seeded, _, _, _ = migrate({"bootstrap": "on"})
assert seeded["models"]["codex"] == expected

for script, label in ((mac, "mac"), (win, "windows")):
    for value in expected.values():
        assert value in script, f"{label}: missing {value}"
    assert '"minimal":"none"' in script, f"{label}: minimal→none missing"
    assert '"max":"max"' in script, f"{label}: max passthrough missing"

print("[PASS] Codex 모델 매핑 Luna/Terra/Sol 정합")
print("[PASS] 이전 기본값만 셀 단위 승격하고 사용자 지정값 보존")
print("[PASS] 현행 설정 멱등 및 models 미보유 설정 시드")
print("[PASS] macOS/Windows effort minimal→none, max→max 정합")
PYTEST
