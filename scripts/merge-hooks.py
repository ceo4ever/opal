#!/usr/bin/env python3
"""
@header {
  "module": "merge-hooks",
  "layer": "util",
  "domain": "opal-install",
  "description": "Claude Code settings.json hooks 멱등 upsert — 소유권을 마커 ∪ command 내용 일치로 판정해 외부 hook 보존 + OPAL 항목 재삽입 + 퇴역 command 회수 (install-mac.sh merge_hooks_config seam)",
  "exports": ["merge_hooks", "main", "MARKER"],
  "depends": []
}
"""
import json
import os
import sys

MARKER = "_opal_managed"  # 소유권 마커 키(매처 블록 수준)


def _commands(block):
    """매처 블록의 command 문자열 집합."""
    return {h.get("command") for h in block.get("hooks", []) if isinstance(h, dict)}


def _is_owned(block, owned_commands):
    """OPAL 소유 판정 — 마커 有, 또는 블록의 모든 command가 OPAL 소유 command 집합에 속함.

    Claude Code는 settings.json 저장 시 스키마 밖 키(_opal_managed)를 버리므로
    마커만으로 판정하면 재배포마다 OPAL 항목이 +1 누적된다(2026-09-17 9중복 사고).
    내용 일치를 함께 보면 마커가 몇 번 지워져도 결과가 동일하다.
    """
    if block.get(MARKER):
        return True
    cmds = _commands(block)
    return bool(cmds) and cmds <= owned_commands


def merge_hooks(target_settings, source_hooks, retired_hooks=None):
    """R-3: source_hooks(OPAL 소유)를 target_settings["hooks"]에 멱등 upsert.

    - 외부 hook(마커 無·command 불일치, 예: orca)은 preserved로 보존(clobber 금지, H-8).
    - 기존 OPAL 항목(마커 有 또는 command가 source/retired와 일치)은 제외 후 source로
      재삽입 → 마커 유실 후에도 N회 실행 결과 동일(멱등).
    - retired_hooks({event: [command, ...]})의 command는 소스에서 퇴역한 OPAL 항목이며
      회수만 하고 재삽입하지 않는다. source에 없는 이벤트도 회수 대상이다.
    - 각 OPAL 매처 블록에 _opal_managed:true를 스탬프(형제 키, DEC-10/11).

    target_settings를 in-place 수정하고 동일 참조를 반환한다.
    """
    retired_hooks = retired_hooks or {}
    hooks = target_settings.setdefault("hooks", {})
    for event in dict.fromkeys([*source_hooks, *retired_hooks]):
        rules = source_hooks.get(event, [])
        owned = {c for r in rules for c in _commands(r)} | set(retired_hooks.get(event, []))
        existing = hooks.get(event, [])
        preserved = [r for r in existing if not _is_owned(r, owned)]  # 외부 보존
        stamped = [{**r, MARKER: True} for r in rules]                  # OPAL 소유 스탬프
        merged = preserved + stamped
        if merged:
            hooks[event] = merged
        else:
            hooks.pop(event, None)                                       # 이벤트 전체 퇴역
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
    # argv: target_path, source_hooks_path [, retired_hooks_path]
    target_path = sys.argv[1]
    source_path = sys.argv[2]
    retired_path = sys.argv[3] if len(sys.argv) > 3 else None

    source_hooks = _load_json(source_path, {})
    retired_hooks = _load_json(retired_path, {}) if retired_path else {}
    target_settings = _load_json(target_path, {})

    merged = merge_hooks(target_settings, source_hooks, retired_hooks)
    _atomic_write(target_path, merged)


if __name__ == "__main__":
    main()
