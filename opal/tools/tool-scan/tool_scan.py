"""
@header {
  "module": "tool_scan",
  "layer": "util",
  "domain": "opal-tools",
  "description": "tool-scan CLI — 5서브명령(list/which/usage/resolve/check) argparse 라우터 + ERROR_CODES 카탈로그 + JSON 출력 헬퍼. 매니페스트(manifest.json) + federation(mcps.md·skills-registry.json) 통합 검색·라우팅·live --help 추출. 정적 캐시 금지(매 호출 live 셸 실행).",
  "exports": [
    "main",
    "ERROR_CODES"
  ],
  "depends": [
    "lib.federation"
  ]
}

tool-scan — 5서브명령 CLI 라우터.

[MUST] 표준 라이브러리만 사용 (json/argparse/pathlib/sys/subprocess/re).
[MUST] subprocess는 shell=False (인자 리스트) — 셸 인젝션 방지.
[MUST] 정적 캐시 금지 — self-help는 매 호출 셸 실행.
[MUST] exit code(==0)로 성공 판정 — ok 필드 기준 판정 금지 (H-4 cmux exit0+ok:false 함정).
"""

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple

# tool-scan 디렉토리
_TOOL_DIR = pathlib.Path(__file__).parent
# lib 경로 추가
sys.path.insert(0, str(_TOOL_DIR))

from lib.federation import load_mcps, load_skills, MAX_INPUT_LENGTH

# ─────────────────────────────────────────────────────────────────────────────
# ERROR_CODES 카탈로그 (SSOT) — 모든 error 응답 값은 이 키를 사용한다.
# 추가/임의 변형 금지.
# ─────────────────────────────────────────────────────────────────────────────

ERROR_CODES: Dict[str, str] = {
    "venv_missing":         "OPAL .venv not found — Run install-mac.sh first",
    "manifest_missing":     "manifest.json 없음 — tool-scan 설치 손상",
    "manifest_parse_failed": "manifest.json 파싱 실패 — JSON 문법 오류",
    "tool_not_found":       "매니페스트에 해당 도구 엔트리 없음",
    "usage_unavailable":    "usage_source 해석 실패 — --help 실행/파일 Read 불가",
    "help_exec_failed":     "self --help 셸 실행 실패 (run.sh 부재·실행권한 없음)",
    "no_match":             "which/resolve — 상황 키워드 매칭 후보 없음",
    "registry_read_failed": "federation 입력(mcps.md/skills-registry.json) 읽기 실패",
}

# kind 우선순위 (낮은 값 = 높은 우선순위)
_KIND_PRIORITY: Dict[str, int] = {
    "tool": 0,
    "mcp": 1,
    "op-skill": 2,
    "pilot-skill": 3,
}


# ─────────────────────────────────────────────────────────────────────────────
# 응답 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def _respond(data: Dict[str, Any], exit_code: int = 0) -> None:
    """JSON 출력 후 지정 exit code로 종료."""
    print(json.dumps(data, ensure_ascii=False))
    sys.exit(exit_code)


def _error(error_key: str, detail: Optional[str] = None, command: str = "") -> None:
    """에러 응답 출력 후 exit 1."""
    resp: Dict[str, Any] = {
        "ok": False,
        "command": command,
        "error": error_key,
    }
    if detail:
        resp["detail"] = detail
    print(json.dumps(resp, ensure_ascii=False))
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# manifest 로딩
# ─────────────────────────────────────────────────────────────────────────────

def _load_manifest() -> List[Dict[str, Any]]:
    """manifest.json 로드. 환경변수 TOOL_SCAN_MANIFEST_PATH로 오버라이드 가능."""
    manifest_path_override = os.environ.get("TOOL_SCAN_MANIFEST_PATH")
    if manifest_path_override:
        manifest_path = pathlib.Path(manifest_path_override)
    else:
        manifest_path = _TOOL_DIR / "manifest.json"

    if not manifest_path.exists():
        _error("manifest_missing", str(manifest_path), "")

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        _error("manifest_parse_failed", str(e), "")

    return data.get("tools", [])


def _load_federation() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """federation(mcps.md + skills-registry.json) 로드.

    환경변수:
        TOOL_SCAN_MCPS_PATH: mcps.md 절대경로 오버라이드
        TOOL_SCAN_SKILLS_REGISTRY_PATH: skills-registry.json 절대경로 오버라이드
    """
    mcps_path = os.environ.get("TOOL_SCAN_MCPS_PATH")
    skills_path = os.environ.get("TOOL_SCAN_SKILLS_REGISTRY_PATH")

    try:
        mcps = load_mcps(mcps_path if mcps_path else None)
    except Exception:
        mcps = []

    try:
        skills = load_skills(skills_path if skills_path else None)
    except Exception:
        skills = []

    return mcps, skills


# ─────────────────────────────────────────────────────────────────────────────
# 라우팅 알고리즘 (which/resolve 공통 — 결정론)
# ─────────────────────────────────────────────────────────────────────────────

def _score_token_against_when(token: str, when: List[str]) -> int:
    """토큰이 when 키워드와 얼마나 매칭되는지 점수 반환 (정확 매칭 + 접두어 부분 매칭)."""
    # 정확 매칭: 1점
    if token in when:
        return 1
    # 부분 매칭: 토큰이 when 키워드의 접두어이거나 when 키워드가 토큰의 접두어 (2자 이상)
    if len(token) >= 2:
        for w in when:
            if len(w) >= 2 and (w.startswith(token) or token.startswith(w)):
                return 1  # 부분 매칭은 정확 매칭과 동일 (상위 정렬은 이름 알파벳으로)
    return 0


def _score_capability(cap: Dict[str, Any], tokens: List[str],
                      situation: str) -> int:
    """capability가 상황 토큰과 얼마나 매칭되는지 점수 계산."""
    kind = cap.get("kind", "")
    score = 0

    if kind == "mcp":
        # mcps.md: when 키워드와 토큰 교집합 (정확 + 부분)
        when = [w.lower() for w in cap.get("when", [])]
        matched = sum(_score_token_against_when(t, when) for t in tokens)
        score += matched
    elif kind in ("op-skill", "pilot-skill"):
        # skills-registry.json: triggers 정규식으로 매칭
        input_str = situation[:MAX_INPUT_LENGTH]
        for pattern in cap.get("triggers", []):
            try:
                if re.search(pattern, input_str):
                    score += 2  # 정규식 매칭은 강한 신호
                    break
            except re.error:
                pass
        # when 키워드도 보조 매칭 (정확 + 부분)
        when = [w.lower() for w in cap.get("when", [])]
        matched = sum(_score_token_against_when(t, when) for t in tokens)
        score += matched
    else:
        # tool: when 배열 키워드 매칭 (정확 + 부분)
        when = [w.lower() for w in cap.get("when", [])]
        matched = sum(_score_token_against_when(t, when) for t in tokens)
        score += matched

    return score


def _route(situation: str, manifest_tools: List[Dict[str, Any]],
           mcps: List[Dict[str, Any]], skills: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """상황 문자열 기반 capability 목록을 결정론적으로 정렬하여 반환."""
    # 입력 정규화
    normalized = situation.lower()[:MAX_INPUT_LENGTH]
    tokens = re.findall(r"[a-z가-힣0-9]+", normalized)

    # 모든 capability 수집
    all_caps: List[Dict[str, Any]] = []
    all_caps.extend(manifest_tools)
    all_caps.extend(mcps)
    all_caps.extend(skills)

    # 점수 계산
    scored: List[Tuple[int, int, str, Dict[str, Any]]] = []
    for cap in all_caps:
        s = _score_capability(cap, tokens, situation)
        if s > 0:
            kind = cap.get("kind", "")
            kind_priority = _KIND_PRIORITY.get(kind, 99)
            name = cap.get("name", "")
            # 결정론 정렬: (-score, kind_priority, name알파벳)
            scored.append((-s, kind_priority, name, cap))

    # 안정 정렬
    scored.sort(key=lambda x: (x[0], x[1], x[2]))

    return [item[3] for item in scored]


# ─────────────────────────────────────────────────────────────────────────────
# usage 추출 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def _resolve_usage(entry: Dict[str, Any]) -> Dict[str, Any]:
    """usage_source 기반으로 live --help 추출.

    [MUST] exit code(returncode==0)로 성공 판정 (H-4 cmux exit0+ok:false 함정).
    [MUST] stdout+stderr 병합 (H-7 외부 CLI stderr-only 케이스).
    [MUST] 정적 캐시 금지 — 매 호출 셸 실행 (H-8).
    """
    usage_source = entry.get("usage_source", {})
    source_type = usage_source.get("type", "self-help")

    if source_type == "inline":
        text = usage_source.get("text", "")
        return {
            "ok": True,
            "live": False,
            "exit_code": None,
            "usage_text": text,
            "usage_json": None,
        }

    if source_type in ("context7", "url"):
        return {
            "ok": True,
            "live": False,
            "exit_code": None,
            "usage_text": None,
            "usage_json": None,
            "pointer": {"type": source_type, "ref": usage_source.get("ref")},
        }

    if source_type == "doc":
        ref = usage_source.get("ref", "")
        try:
            doc_path = pathlib.Path(ref.replace("~", str(pathlib.Path.home())))
            text = doc_path.read_text(encoding="utf-8")
            freshness = usage_source.get("freshness")
            return {
                "ok": True,
                "live": False,
                "exit_code": None,
                "usage_text": text + (f"\n\n(as of {freshness})" if freshness else ""),
                "usage_json": None,
            }
        except Exception as e:
            return {"ok": False, "error": "usage_unavailable", "detail": str(e)}

    # self-help: 셸 실행 (정적 캐시 금지 — 매 호출)
    # TOOL_SCAN_HELP_CMD 환경변수로 테스트 격리 가능
    help_cmd_override = os.environ.get("TOOL_SCAN_HELP_CMD")
    if help_cmd_override:
        exec_cmd = ["bash", help_cmd_override]
    else:
        exec_str = usage_source.get("exec", "run.sh --help")
        # exec_str 파싱: "run.sh --help" → ["bash", "<절대경로>/run.sh", "--help"]
        parts = exec_str.split()
        if parts[0] == "run.sh":
            # 대상 도구의 run.sh: ~/.opal/tools/<name>/run.sh (resolve 서브명령과 동일 규칙)
            tool_run_sh = pathlib.Path.home() / ".opal" / "tools" / entry["name"] / "run.sh"
            cmd_parts = ["bash", str(tool_run_sh)] + parts[1:]
        else:
            cmd_parts = parts  # 외부 CLI: 그대로 사용
        exec_cmd = cmd_parts

    try:
        # shell=False (보안: 인자 리스트)
        result = subprocess.run(
            exec_cmd,
            capture_output=True,
            text=True,
        )
        returncode = result.returncode
        stdout = result.stdout
        stderr = result.stderr

        # [MUST] exit code(returncode==0)로 성공 판정
        if returncode == 0:
            # stdout+stderr 병합 (H-7: 일부 CLI는 stderr로만 help 출력)
            combined = stdout + stderr
            # stdout이 JSON이면 파싱
            stdout_stripped = stdout.strip()
            if stdout_stripped.startswith("{") or stdout_stripped.startswith("["):
                try:
                    usage_json = json.loads(stdout_stripped)
                    return {
                        "ok": True,
                        "live": True,
                        "exit_code": returncode,
                        "usage_json": usage_json,
                        "usage_text": None,
                    }
                except json.JSONDecodeError:
                    pass
            # stdout+stderr 병합 텍스트 반환
            return {
                "ok": True,
                "live": True,
                "exit_code": returncode,
                "usage_json": None,
                "usage_text": combined.strip(),
            }
        else:
            return {
                "ok": False,
                "error": "help_exec_failed",
                "detail": f"exit_code={returncode}, stderr={stderr[:200]}",
            }
    except FileNotFoundError as e:
        return {
            "ok": False,
            "error": "help_exec_failed",
            "detail": str(e),
        }
    except Exception as e:
        return {
            "ok": False,
            "error": "usage_unavailable",
            "detail": str(e),
        }


# ─────────────────────────────────────────────────────────────────────────────
# 서브명령 핸들러
# ─────────────────────────────────────────────────────────────────────────────

def cmd_list(args: argparse.Namespace) -> None:
    """list 서브명령 — 매니페스트 7 엔트리를 kind별 그룹핑, purpose 1줄만.

    [설계 결정] list는 manifest SSOT만 반환 (TS-012: stub manifest 7엔트리 → 7개).
    federation(MCP/스킬) 포함은 which/resolve 시 동적 조회.
    2단 토큰 금지: purpose만, usage 본문 미포함.
    """
    tools = _load_manifest()

    capabilities: List[Dict[str, Any]] = []

    for t in tools:
        capabilities.append({
            "name": t.get("name", ""),
            "kind": t.get("kind", "tool"),
            "purpose": t.get("purpose", ""),
        })

    _respond({
        "ok": True,
        "command": "list",
        "capabilities": capabilities,
    })


def cmd_which(args: argparse.Namespace) -> None:
    """which 서브명령 — 상황 키워드 → 후보 capability 목록 반환."""
    situation = args.situation
    if not situation:
        _error("no_match", "상황 문자열 필요", "which")

    tools = _load_manifest()
    mcps, skills = _load_federation()

    matches = _route(situation, tools, mcps, skills)

    if not matches:
        _error("no_match", f"매칭 없음: {situation!r}", "which")

    result_matches = []
    normalized = situation.lower()[:MAX_INPUT_LENGTH]
    tokens = re.findall(r"[a-z가-힣0-9]+", normalized)

    for cap in matches:
        when = [w.lower() for w in cap.get("when", [])]
        matched_on = [t for t in tokens if t in when]
        score = _score_capability(cap, tokens, situation)
        result_matches.append({
            "name": cap.get("name", ""),
            "kind": cap.get("kind", ""),
            "score": score,
            "matched_on": matched_on,
        })

    _respond({
        "ok": True,
        "command": "which",
        "situation": situation,
        "matches": result_matches,
    })


def cmd_usage(args: argparse.Namespace) -> None:
    """usage 서브명령 — live --help 추출."""
    tool_name = args.tool
    tools = _load_manifest()

    # 도구 엔트리 탐색
    entry = None
    for t in tools:
        if t.get("name") == tool_name:
            entry = t
            break

    if entry is None:
        _error("tool_not_found", f"매니페스트에 '{tool_name}' 없음", "usage")

    usage_result = _resolve_usage(entry)

    if not usage_result.get("ok"):
        resp: Dict[str, Any] = {
            "ok": False,
            "command": "usage",
            "error": usage_result.get("error", "usage_unavailable"),
        }
        if "detail" in usage_result:
            resp["detail"] = usage_result["detail"]
        print(json.dumps(resp, ensure_ascii=False))
        sys.exit(1)

    resp = {
        "ok": True,
        "command": "usage",
        "tool": tool_name,
        "kind": entry.get("kind", "tool"),
        "source_type": entry.get("usage_source", {}).get("type", "self-help"),
        "live": usage_result.get("live", False),
        "exit_code": usage_result.get("exit_code"),
    }
    if usage_result.get("usage_json") is not None:
        resp["usage_json"] = usage_result["usage_json"]
    if usage_result.get("usage_text") is not None:
        resp["usage_text"] = usage_result["usage_text"]
    if usage_result.get("pointer") is not None:
        resp["pointer"] = usage_result["pointer"]
    if entry.get("fallback") is not None:
        resp["fallback"] = entry["fallback"]

    _respond(resp)


def cmd_resolve(args: argparse.Namespace) -> None:
    """resolve 서브명령 — 상황 → top-1 capability + invoke 형태 + usage 결합."""
    situation = args.situation
    if not situation:
        _error("no_match", "상황 문자열 필요", "resolve")

    tools = _load_manifest()
    mcps, skills = _load_federation()

    matches = _route(situation, tools, mcps, skills)

    if not matches:
        _error("no_match", f"매칭 없음: {situation!r}", "resolve")

    top = matches[0]
    kind = top.get("kind", "tool")
    name = top.get("name", "")

    resolved: Dict[str, Any] = {
        "name": name,
        "kind": kind,
    }

    if kind == "tool":
        # tool: shell invoke + usage live + fallback
        opal_home = pathlib.Path.home() / ".opal"
        exec_path = str(opal_home / "tools" / name / "run.sh")
        resolved["invoke"] = "shell"
        resolved["exec"] = exec_path
        # fallback 계약 동봉 (manifest에서)
        manifest_entry = next((t for t in tools if t.get("name") == name), None)
        if manifest_entry:
            resolved["fallback"] = manifest_entry.get("fallback")
            # usage 결합 (live)
            usage_result = _resolve_usage(manifest_entry)
            if usage_result.get("ok"):
                if usage_result.get("usage_json") is not None:
                    resolved["usage_json"] = usage_result["usage_json"]
                elif usage_result.get("usage_text") is not None:
                    resolved["usage_text"] = usage_result["usage_text"]
        else:
            resolved["fallback"] = None

    elif kind == "mcp":
        # mcp: ToolSearch 포인터만 — 스키마 미반환 (H-3)
        resolved["invoke"] = "ToolSearch"
        resolved["exec"] = f'ToolSearch query "select:{name}"'
        resolved["description"] = top.get("description", "")
        # [MUST] parameters 미포함 (TS-031)

    elif kind == "pilot-skill":
        # pilot-skill: alias 진입
        alias = top.get("alias", name)
        resolved["invoke"] = "alias"
        resolved["exec"] = f"//{alias}"
        resolved["skill_path"] = top.get("skill_path", "")

    elif kind == "op-skill":
        # op-skill: dispatch + skill_path + dispatched_by (TS-032)
        resolved["invoke"] = "dispatch"
        resolved["skill_path"] = top.get("skill_path", "")
        if top.get("stage"):
            resolved["stage"] = top["stage"]
        if top.get("dispatched_by"):
            resolved["dispatched_by"] = top["dispatched_by"]

    _respond({
        "ok": True,
        "command": "resolve",
        "situation": situation,
        "resolved": resolved,
    })


def cmd_check(args: argparse.Namespace) -> None:
    """check 서브명령 — 도구 설치·실행 가능 여부 검사."""
    tool_name = args.tool
    tools = _load_manifest()

    entry = next((t for t in tools if t.get("name") == tool_name), None)
    if entry is None:
        _error("tool_not_found", f"매니페스트에 '{tool_name}' 없음", "check")

    kind = entry.get("kind", "tool")
    installed = False
    detail = ""
    fallback_allowed = False

    if kind == "tool":
        # run.sh 존재 및 실행권한 확인
        opal_home = pathlib.Path.home() / ".opal"
        run_sh = opal_home / "tools" / tool_name / "run.sh"
        # 소스 환경 폴백
        if not run_sh.exists():
            # cwd 기준 탐색
            cwd_run = pathlib.Path.cwd() / "opal" / "tools" / tool_name / "run.sh"
            if cwd_run.exists():
                run_sh = cwd_run
        installed = run_sh.exists() and os.access(run_sh, os.X_OK)
        if not installed:
            detail = f"run.sh 미존재 또는 실행권한 없음: {run_sh}"

        # fallback_allowed: manifest fallback 계약에서 확인
        fallback = entry.get("fallback")
        if isinstance(fallback, list):
            for fb in fallback:
                if isinstance(fb, dict) and fb.get("on") != "usage":
                    fallback_allowed = fallback_allowed or fb.get("allow_fallback", False)
        elif isinstance(fallback, dict):
            fallback_allowed = fallback.get("allow_fallback", False)

    _respond({
        "ok": True,
        "command": "check",
        "tool": tool_name,
        "installed": installed,
        "detail": detail if detail else None,
        "fallback_allowed": fallback_allowed,
    })


# ─────────────────────────────────────────────────────────────────────────────
# argparse 빌더 — JSON 에러 응답 파서
# ─────────────────────────────────────────────────────────────────────────────

class _JsonErrorParser(argparse.ArgumentParser):
    """argparse 파싱 에러를 JSON 응답으로 변환하는 파서."""

    def error(self, message: str) -> None:  # type: ignore[override]
        print(json.dumps({
            "ok": False,
            "command": "",
            "error": "no_match",
            "detail": message,
        }, ensure_ascii=False))
        sys.exit(2)


def _build_parser() -> _JsonErrorParser:
    parser = _JsonErrorParser(
        prog="tool-scan",
        description="OPAL 도구·MCP·스킬 통합 검색·사용법·활용 체계",
    )
    subparsers = parser.add_subparsers(dest="command")

    # list
    subparsers.add_parser("list", help="전체 capability 목록 (purpose 1줄)")

    # which
    which_p = subparsers.add_parser("which", help="상황 기반 capability 후보 검색")
    which_p.add_argument("situation", nargs="+", help="상황 키워드")

    # usage
    usage_p = subparsers.add_parser("usage", help="도구 live --help 추출")
    usage_p.add_argument("tool", help="도구 이름 (manifest name)")
    usage_p.add_argument("subcmd", nargs="?", help="세부 명령 (선택)")

    # resolve
    resolve_p = subparsers.add_parser("resolve", help="상황 → top-1 capability + invoke 방법")
    resolve_p.add_argument("situation", nargs="+", help="상황 키워드")

    # check
    check_p = subparsers.add_parser("check", help="도구 설치·실행 가능 여부 확인")
    check_p.add_argument("tool", help="도구 이름")

    return parser


# ─────────────────────────────────────────────────────────────────────────────
# main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = _build_parser()

    # 인자 없음 또는 알 수 없는 서브명령 처리
    if len(sys.argv) < 2:
        print(json.dumps({
            "ok": False,
            "command": "",
            "error": "no_match",
            "detail": "서브명령 필요: list | which | usage | resolve | check",
        }, ensure_ascii=False))
        sys.exit(1)

    # 알 수 없는 서브명령 사전 체크 (argparse가 unknown subcommand를 None으로 처리하는 문제 방지)
    known_commands = {"list", "which", "usage", "resolve", "check"}
    first_arg = sys.argv[1]
    if first_arg.startswith("-"):
        # --help 등 옵션은 argparse에 위임
        pass
    elif first_arg not in known_commands:
        print(json.dumps({
            "ok": False,
            "command": first_arg,
            "error": "no_match",
            "detail": f"알 수 없는 서브명령: {first_arg}",
        }, ensure_ascii=False))
        sys.exit(1)

    args = parser.parse_args()

    if args.command is None:
        print(json.dumps({
            "ok": False,
            "command": "",
            "error": "no_match",
            "detail": "알 수 없는 서브명령",
        }, ensure_ascii=False))
        sys.exit(1)

    # which/resolve: 복수 인자를 공백으로 결합
    if args.command in ("which", "resolve"):
        args.situation = " ".join(args.situation)

    dispatch = {
        "list": cmd_list,
        "which": cmd_which,
        "usage": cmd_usage,
        "resolve": cmd_resolve,
        "check": cmd_check,
    }

    handler = dispatch.get(args.command)
    if handler is None:
        print(json.dumps({
            "ok": False,
            "command": args.command,
            "error": "no_match",
            "detail": f"알 수 없는 서브명령: {args.command}",
        }, ensure_ascii=False))
        sys.exit(1)

    handler(args)


if __name__ == "__main__":
    main()
