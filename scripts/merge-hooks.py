#!/usr/bin/env python3
"""
@header {
  "module": "merge-hooks",
  "layer": "util",
  "domain": "opal-install",
  "description": "Claude Code settings.json hooks 소유권-마커 기반 멱등 upsert — 외부 hook 보존 + OPAL 항목 재삽입 (install-mac.sh merge_hooks_config seam)",
  "exports": ["merge_hooks", "main", "MARKER"],
  "depends": []
}
"""
import json
import os
import sys

MARKER = "_opal_managed"  # 소유권 마커 키(매처 블록 수준)


def merge_hooks(target_settings, source_hooks):
    """R-3: source_hooks(OPAL 소유)를 target_settings["hooks"]에 멱등 upsert.

    - 외부 hook(마커 無, 예: orca PostToolUse)은 preserved로 보존(clobber 금지, H-8).
    - 기존 OPAL 항목(마커 有)은 preserved에서 제외 후 source로 재삽입 → N회 실행 결과 동일(멱등).
    - 각 OPAL 매처 블록에 _opal_managed:true를 스탬프(형제 키, DEC-10/11).

    target_settings를 in-place 수정하고 동일 참조를 반환한다.
    """
    hooks = target_settings.setdefault("hooks", {})
    for event, rules in source_hooks.items():
        existing = hooks.get(event, [])
        preserved = [r for r in existing if not r.get(MARKER)]  # 외부 보존
        stamped = [{**r, MARKER: True} for r in rules]           # OPAL 소유 스탬프
        hooks[event] = preserved + stamped                        # 외부 유지 + OPAL 갱신
    return target_settings


def _load_json(path, default):
    """path 파일을 로드한다. 없거나 공백이면 default 반환."""
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        content = f.read().strip()
    return json.loads(content) if content else default


def _atomic_write(path, data):
    """data를 indent=2 JSON으로 원자적 write(temp → os.replace)."""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)


def main():
    # argv: target_path, source_hooks_path
    target_path = sys.argv[1]
    source_path = sys.argv[2]

    source_hooks = _load_json(source_path, {})
    target_settings = _load_json(target_path, {})

    merged = merge_hooks(target_settings, source_hooks)
    _atomic_write(target_path, merged)


if __name__ == "__main__":
    main()
