"""
@header {
  "module": "todo_mirror_hook",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "076 F-002: Claude Code PostToolUse 릴레이 헬퍼 — stdin(PostToolUse 이벤트 JSON)을 파싱해 Bash·state-tool(init/advance/mark/block) 호출을 필터하고, 도구 stdout에서 build_todo_mirror 페이로드를 추출한 뒤 hookSpecificOutput.additionalContext(지시문+payload)로 세션에 결정론 주입한다. 비Bash·비state-tool·페이로드 부재·파싱 실패 등 전 경로에서 무출력 exit0 fail-safe(DEC-9) — 정상 도구 흐름을 절대 차단하지 않는다. 표준 라이브러리만(json/sys/shlex).",
  "exports": [
    "main", "extract_command", "is_state_tool_event",
    "extract_todo_mirror", "build_additional_context"
  ]
}
"""

# 076 T-2: 표준 라이브러리만 import
import json
import shlex
import sys

# state-tool 호출 시그니처 — run.sh 경유 실행(run.sh 선례)
_STATE_TOOL_SIG = "state-tool/run.sh"
# todo 미러 대상 서브명령 4종 (build_todo_mirror가 페이로드를 출력하는 명령)
_MIRRORED_CMDS = ("init", "advance", "mark", "block")


def extract_command(tool_input):
    """PostToolUse tool_input dict에서 Bash command 문자열을 안전 추출.
    dict/키 부재/비문자열이면 빈 문자열(fail-safe)."""
    if not isinstance(tool_input, dict):
        return ""
    cmd = tool_input.get("command", "")
    return cmd if isinstance(cmd, str) else ""


def _subcommand(command):
    """command 문자열에서 state-tool 서브명령(run.sh 다음 토큰)을 추출. 없으면 None.
    shlex 실패 시 단순 split 폴백(fail-safe)."""
    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = command.split()
    for i, tok in enumerate(tokens):
        if _STATE_TOOL_SIG in tok:
            return tokens[i + 1] if i + 1 < len(tokens) else None
    return None


def is_state_tool_event(command):
    """command가 state-tool/run.sh 호출이며 서브명령이 미러 대상 4종인지 판정(DEC-5).
    비state-tool 호출은 여기서 걸러져 무발동(H-6)."""
    if _STATE_TOOL_SIG not in command:
        return False
    return _subcommand(command) in _MIRRORED_CMDS


def _get_stdout(tool_response):
    """tool_response(dict/str 양쪽)에서 stdout 텍스트 추출(fail-safe)."""
    if isinstance(tool_response, dict):
        out = tool_response.get("stdout", "")
        return out if isinstance(out, str) else ""
    if isinstance(tool_response, str):
        return tool_response
    return ""


def extract_todo_mirror(stdout):
    """stdout 라인들 중 마지막으로 파싱되는 JSON 객체에서 todo_mirror를 추출.
    stderr 경고·다중 라인 혼입을 견딘다(H-5). 없으면 None(DEC-9)."""
    result = None
    if not isinstance(stdout, str):
        return None
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except (ValueError, TypeError):
            continue
        if isinstance(obj, dict) and isinstance(obj.get("todo_mirror"), dict):
            result = obj["todo_mirror"]
    return result


def build_additional_context(command_name, payload):
    """결정론 지시문 + todo_mirror payload JSON 직렬화(DEC-8).
    SSOT 불변·능력 감지 문구를 지시에 명시한다."""
    instruction = (
        f"[파이프라인 todo 미러] state-tool {command_name} 감지 — 아래 todo_mirror로 "
        "네이티브 할일 패널을 갱신하라: action=create면 TaskCreate로 단계별 todo를 생성, "
        "action=update면 각 단계 todo를 status(pending/in_progress/completed)로 TaskUpdate. "
        "능력 감지: 네이티브 할일 도구가 없는 세션이면 이 지시를 무시하라(플랫폼 독립). "
        "SSOT는 STATE.md/state-tool이며 todo는 읽기 전용 거울이다(충돌 시 STATE.md가 이긴다)."
    )
    return instruction + "\n" + json.dumps(payload, ensure_ascii=False)


def main():
    """PostToolUse 이벤트를 stdin으로 받아 조건 충족 시 additionalContext를 stdout에 출력.
    미충족 전 경로는 무출력 return(DEC-9 fail-safe)."""
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return
    if not isinstance(data, dict):
        return
    if data.get("tool_name") != "Bash":                      # 비Bash → 무발동
        return
    command = extract_command(data.get("tool_input") or {})
    if not is_state_tool_event(command):                     # 비state-tool → 무발동(H-6)
        return
    payload = extract_todo_mirror(_get_stdout(data.get("tool_response")))
    if not payload:                                          # 페이로드 부재 → 무출력(H-5/DEC-9)
        return
    ctx = build_additional_context(_subcommand(command), payload)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": ctx,
        }
    }, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # DEC-9: 전 경로 fail-safe — 어떤 예외에서도 정상 도구 흐름을 차단하지 않는다.
        pass
    sys.exit(0)
