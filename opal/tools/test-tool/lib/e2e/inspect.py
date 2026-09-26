"""
@header {
  "module": "inspect",
  "layer": "util",
  "domain": "opal-tools",
  "description": "`test-tool e2e env-inspect`의 읽기 전용 환경 검토. 프로젝트 트리를 제한된 깊이로 훑어 표면 후보(package.json scripts·의존성의 vite/next/electron/tauri, Python 코드의 FastAPI/Flask 앱 선언과 `/health` 문자열, *.xcodeproj·Package.swift·*.csproj·*.desktop)와 `.env.example`의 변수 이름, 설정 파일 존재·유효성, driver 설치 여부(drivers.discover_installed: binary 경로 해석만)를 모은다. 파일·캐시를 쓰지 않고 프로젝트 코드를 import하지 않으며 외부 명령(프로젝트 선언 driver 명령·`--version` 포함)을 실행하지 않고 `.env.example`의 값은 결과에 싣지 않는다.",
  "exports": ["inspect_project"],
  "depends": ["environment", "drivers", "process"]
}

lib.e2e.inspect — 결과는 제안일 뿐 설정을 만들지 않는다. 설정 기록은 사용자가 확인한 뒤
스킬 setup 절차가 한다. 제안 명령은 environment.py의 치환 토큰(`{host}`·`{port}`·`{python}`)을
쓴다. OS 판정은 process.host_platform()만 사용한다.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from lib.e2e import environment as e2e_environment
from lib.e2e import process as e2e_process

# 훑지 않는 디렉터리 — 의존성·빌드 산출물·VCS·가상환경·하네스 산출물.
_SKIP_DIRS = frozenset(
    {
        ".git", "node_modules", ".venv", "venv", "env", "__pycache__", ".mypy_cache",
        ".pytest_cache", ".ruff_cache", "dist", "build", ".next", ".e2e", ".opal-worktrees",
        "target", ".tox", ".idea", ".vscode", "Pods", "DerivedData", "bin", "obj",
    }
)
_MAX_DEPTH = 4
_MAX_FILES = 5000
_MAX_PY_BYTES = 512 * 1024

_FASTAPI_PATTERN = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*FastAPI\s*\(", re.MULTILINE)
_FLASK_PATTERN = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*Flask\s*\(", re.MULTILINE)
_ENV_NAME_PATTERN = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=")

_WEB_FRAMEWORKS = ("vite", "next")
_DESKTOP_JS_FRAMEWORKS = ("electron", "@tauri-apps/cli", "@tauri-apps/api")


def inspect_project(project_root: str) -> Dict[str, Any]:
    """D-7 검토 결과를 돌려준다. 쓰기 연산과 외부 명령 실행을 하지 않는다."""
    from lib.e2e import drivers as e2e_drivers

    root = Path(project_root).resolve()
    files, dirs = _scan_tree(root)

    candidates: List[Dict[str, Any]] = []
    candidates.extend(_package_json_candidates(root, files))
    candidates.extend(_python_candidates(root, files))
    candidates.extend(_desktop_candidates(root, files, dirs))

    return {
        "config": _config_state(root),
        "surface_candidates": candidates,
        "drivers": e2e_drivers.discover_installed(str(root)),
        "secret_hints": _secret_hints(files),
    }


# ── 트리 훑기 ────────────────────────────────────────────────────────────────

def _scan_tree(root: Path) -> Tuple[List[Path], List[Path]]:
    files: List[Path] = []
    dirs: List[Path] = []
    for current, subdirs, names in os.walk(root):
        current_path = Path(current)
        depth = len(current_path.relative_to(root).parts)
        kept = []
        for name in sorted(subdirs):
            if name in _SKIP_DIRS:
                continue
            full = current_path / name
            if name.endswith(".xcodeproj"):
                # 번들 디렉터리 — 근거로만 쓰고 안으로 들어가지 않는다.
                dirs.append(full)
                continue
            kept.append(name)
        subdirs[:] = kept if depth < _MAX_DEPTH else []
        for name in sorted(names):
            files.append(current_path / name)
            if len(files) >= _MAX_FILES:
                return files, dirs
    return files, dirs


def _rel(root: Path, path: Path) -> str:
    rel = path.relative_to(root).as_posix()
    return rel or "."


def _read_text(path: Path, limit: int = _MAX_PY_BYTES) -> Optional[str]:
    try:
        if path.stat().st_size > limit:
            return None
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


# ── 설정 상태 ────────────────────────────────────────────────────────────────

def _config_state(root: Path) -> Dict[str, Any]:
    loaded = e2e_environment.load(str(root))
    present = loaded["status"] != "missing"
    return {
        "present": present,
        "path": loaded["path"],
        "valid": (loaded["status"] == "ok") if present else None,
    }


# ── package.json ─────────────────────────────────────────────────────────────

def _package_json_candidates(root: Path, files: List[Path]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for path in files:
        if path.name != "package.json":
            continue
        text = _read_text(path)
        if text is None:
            continue
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        deps: Dict[str, Any] = {}
        for key in ("dependencies", "devDependencies"):
            if isinstance(data.get(key), dict):
                deps.update(data[key])
        scripts = data.get("scripts") if isinstance(data.get("scripts"), dict) else {}
        cwd = _rel(root, path.parent)
        evidence = [_rel(root, path)]

        framework = next((name for name in _WEB_FRAMEWORKS if name in deps), None)
        script = next((name for name in ("dev", "start") if name in scripts), None)
        if framework is not None and script is not None:
            if framework == "next":
                extra = ["-H", "{host}", "-p", "{port}"]
            else:
                extra = ["--host", "{host}", "--port", "{port}", "--strictPort"]
            out.append(
                {
                    "kind": "web",
                    "evidence": evidence,
                    "suggested": {
                        "command": ["npm", "run", script, "--", *extra],
                        "cwd": cwd,
                        "health": {"type": "port"},
                    },
                }
            )

        if any(name in deps for name in _DESKTOP_JS_FRAMEWORKS):
            # 데스크톱 런타임을 실제로 부르는 script만 제안한다(웹 dev 서버 script를 오인하지 않게).
            desktop_script = next(
                (
                    name for name, body in scripts.items()
                    if isinstance(body, str) and re.search(r"\b(electron|tauri)\s", body)
                ),
                None,
            )
            out.append(
                {
                    "kind": _host_desktop_kind(),
                    "evidence": evidence,
                    "suggested": {
                        "command": ["npm", "run", desktop_script] if desktop_script else None,
                        "cwd": cwd,
                        "health": None,
                    },
                }
            )
    return out


# ── Python ───────────────────────────────────────────────────────────────────

def _python_candidates(root: Path, files: List[Path]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for path in files:
        if path.suffix != ".py":
            continue
        text = _read_text(path)
        if not text:
            continue
        fastapi = _FASTAPI_PATTERN.search(text) if "FastAPI" in text else None
        flask = _FLASK_PATTERN.search(text) if "Flask" in text else None
        if fastapi is None and flask is None:
            continue
        module = ".".join(path.relative_to(root).with_suffix("").parts)
        health: Dict[str, Any] = (
            {"type": "http", "path": "/health", "expect_status": 200}
            if "/health" in text
            else {"type": "port"}
        )
        if fastapi is not None:
            command = ["{python}", "-m", "uvicorn", f"{module}:{fastapi.group(1)}",
                       "--host", "{host}", "--port", "{port}"]
        else:
            command = ["{python}", "-m", "flask", "--app", f"{module}:{flask.group(1)}",
                       "run", "--host", "{host}", "--port", "{port}"]
        out.append(
            {
                "kind": "api",
                "evidence": [_rel(root, path)],
                "suggested": {"command": command, "cwd": ".", "health": health},
            }
        )
    return out


# ── 데스크톱 ─────────────────────────────────────────────────────────────────

def _host_desktop_kind() -> str:
    return f"{e2e_process.host_platform()}-app"


def _desktop_candidates(root: Path, files: List[Path], dirs: List[Path]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for path in dirs:
        rel = _rel(root, path)
        out.append(_desktop("macos-app", rel, ["xcodebuild", "-project", rel, "build"], _rel(root, path.parent)))
    for path in files:
        rel = _rel(root, path)
        if path.name == "Package.swift":
            out.append(_desktop("macos-app", rel, ["swift", "run"], _rel(root, path.parent)))
        elif path.suffix == ".csproj":
            out.append(_desktop("windows-app", rel, ["dotnet", "run", "--project", rel], "."))
        elif path.suffix == ".desktop":
            out.append(_desktop("linux-app", rel, _desktop_exec(path), "."))
    return out


def _desktop(kind: str, evidence: str, command: Optional[List[str]], cwd: str) -> Dict[str, Any]:
    return {
        "kind": kind,
        "evidence": [evidence],
        "suggested": {"command": command, "cwd": cwd, "health": None},
    }


def _desktop_exec(path: Path) -> Optional[List[str]]:
    text = _read_text(path, limit=64 * 1024)
    if not text:
        return None
    for line in text.splitlines():
        if line.startswith("Exec="):
            parts = [part for part in line[len("Exec="):].split() if not part.startswith("%")]
            return parts or None
    return None


# ── 비밀 이름 ────────────────────────────────────────────────────────────────

def _secret_hints(files: List[Path]) -> List[str]:
    """`.env.example`에서 변수 이름만 뽑는다. `=` 뒤 값은 버린다."""
    names: List[str] = []
    for path in files:
        if path.name != ".env.example":
            continue
        text = _read_text(path, limit=256 * 1024)
        if not text:
            continue
        for line in text.splitlines():
            match = _ENV_NAME_PATTERN.match(line)
            if match and match.group(1) not in names:
                names.append(match.group(1))
    return names
