"""
@header {
  "module": "ownership_tool.stop_hook",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "Claude Code Stop hook 어댑터. stdin의 Stop 봉투를 파싱해 stop_evaluator.evaluate에 넘기고, block_continue·defer_to_pm일 때만 hook의 유일한 채널인 {\"decision\":\"block\",\"reason\":…} 1줄을 stdout에 출력한다. 그 밖의 decision_kind는 무출력으로 Stop을 통과시킨다. 판정 로직은 갖지 않고 봉투 파싱·project_root 선택·출력 형식만 소유한다. todo_mirror_hook과 동일하게 전 경로 except Exception: pass + exit 0 fail-safe라 어떤 실패에서도 세션을 막지 않는다.",
  "exports": ["main", "to_hook_output"],
  "depends": ["ownership_tool.stop_evaluator"]
}
"""
from __future__ import annotations

import json
import pathlib
import sys

if __package__:
    from . import stop_evaluator
else:
    # hook은 이 파일을 경로로 직접 실행한다(패키지 컨텍스트 없음) — tool-dir을 path에 올린다.
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    from ownership_tool import stop_evaluator

# 차단 채널로 내보내는 판정 2종. 나머지 decision_kind는 무출력 통과다.
_BLOCKING_KINDS = ("block_continue", "defer_to_pm")


def to_hook_output(result):
    """판정 결과를 hook 출력 dict로 바꾼다. 통과 판정이면 None."""
    if not isinstance(result, dict):
        return None
    if result.get("decision_kind") not in _BLOCKING_KINDS:
        return None
    reason = result.get("reason")
    if not reason:
        return None
    return {"decision": "block", "reason": reason}


def main():
    """stdin Stop 봉투 → evaluate → 차단 시에만 1줄 출력."""
    try:
        payload = json.load(sys.stdin)
    except Exception:  # noqa: BLE001 — 봉투 파싱 실패는 무출력 통과(fail-safe)
        return
    if not isinstance(payload, dict):
        return
    project_root = payload.get("cwd")
    if not project_root:
        return
    output = to_hook_output(stop_evaluator.evaluate(payload, project_root=project_root))
    if output is not None:
        print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001 — 전 경로 fail-safe: 어떤 예외에서도 세션을 차단하지 않는다.
        pass
    sys.exit(0)
