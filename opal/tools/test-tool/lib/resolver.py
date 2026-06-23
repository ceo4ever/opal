"""
@header {
  "module": "resolver",
  "layer": "util",
  "domain": "opal-tools",
  "description": "test-tools.yaml resolution_order(project→global→추론) 해석 모듈. PyYAML 6.0.3 사용.",
  "exports": [
    "resolve_test_tools"
  ]
}

test-tool resolver — test-tools.yaml 3단계 resolution_order 집행.
1. {project}/.opal/test-tools.yaml (최우선)
2. OPAL_TEST_TOOLS_GLOBAL 환경변수 경로 또는 ~/.opal/templates/test-tools.yaml (글로벌 기본값)
3. package.json / pyproject.toml 추론 (내부 폴백 — H-1, H-8)
"""

import json
import os
import pathlib
from typing import Any, Dict, Optional

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


def _load_yaml(path: pathlib.Path) -> Optional[Dict[str, Any]]:
    """YAML 파일을 로드하여 dict 반환. 실패 시 None 반환."""
    if not path.exists():
        return None
    try:
        if _YAML_AVAILABLE:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return data if isinstance(data, dict) else None
        else:
            # PyYAML 미가용 시 stdlib json 폴백 불가 — 에러 상승
            raise ImportError("PyYAML is required for YAML parsing")
    except Exception:
        return None


def _load_yaml_strict(path: pathlib.Path) -> Dict[str, Any]:
    """YAML 파일을 로드. 파싱 실패 시 예외 상승 (에러 코드 분기용)."""
    if not _YAML_AVAILABLE:
        raise RuntimeError("PyYAML not available")
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            raise ValueError(f"YAML root is not a mapping: {type(data)}")
        return data
    except Exception as exc:
        raise ValueError(f"YAML parse failed: {exc}") from exc


def _infer_from_package_json(project_root: pathlib.Path) -> Optional[Dict[str, Any]]:
    """package.json에서 도구셋 추론. 가능한 경우 기본 tiers 반환."""
    pkg_path = project_root / "package.json"
    if not pkg_path.exists():
        return None
    try:
        pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    except Exception:
        return None

    all_deps: Dict[str, str] = {}
    all_deps.update(pkg.get("dependencies", {}))
    all_deps.update(pkg.get("devDependencies", {}))

    fe_unit = []
    if "vitest" in all_deps:
        fe_unit.append({"name": "vitest", "check": "npx vitest run"})
    if "jest" in all_deps:
        fe_unit.append({"name": "jest", "check": "npx jest --watchAll=false"})

    fe_lint = []
    if "eslint" in all_deps:
        fe_lint.append({"name": "eslint", "check": "npx eslint .", "required": True})

    fe_typecheck = []
    if "typescript" in all_deps or "tsc" in all_deps:
        fe_typecheck.append({"name": "tsc", "check": "npx tsc --noEmit", "required": True})

    tiers: Dict[str, Any] = {
        "unit": {
            "fe": {},
            "be": {},
        },
        "integration": {
            "e2e": [
                {"name": "cmux", "priority": 1, "via": "cmux-tool"},
                {"name": "playwright", "priority": 2, "fallback": True},
            ]
        },
    }
    if fe_lint:
        tiers["unit"]["fe"]["lint"] = fe_lint
    if fe_typecheck:
        tiers["unit"]["fe"]["typecheck"] = fe_typecheck
    if fe_unit:
        tiers["unit"]["fe"]["unit"] = fe_unit

    return {
        "version": "2.0",
        "source_label": "infer",
        "stack": {"language": "typescript", "framework": "unknown", "runtime": "node"},
        "tiers": tiers,
    }


def _infer_from_pyproject(project_root: pathlib.Path) -> Optional[Dict[str, Any]]:
    """pyproject.toml에서 도구셋 추론 (기본 Python 스택)."""
    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.exists():
        return None

    tiers: Dict[str, Any] = {
        "unit": {
            "fe": {},
            "be": {
                "lint": [{"name": "ruff", "check": "ruff .", "required": True}],
                "typecheck": [{"name": "mypy", "check": "mypy .", "required": True}],
                "unit": [{"name": "pytest", "check": "pytest", "required": True}],
            },
        },
        "integration": {
            "e2e": [
                {"name": "cmux", "priority": 1, "via": "cmux-tool"},
                {"name": "playwright", "priority": 2, "fallback": True},
            ],
            "be": {
                "api_db": [{"name": "pytest", "check": "pytest", "real_db": True, "required": True}]
            },
        },
    }
    return {
        "version": "2.0",
        "source_label": "infer",
        "stack": {"language": "python", "framework": "unknown", "runtime": "python"},
        "tiers": tiers,
    }


def resolve_test_tools(
    project_root: Optional[pathlib.Path] = None,
    stack: Optional[str] = None,
) -> Dict[str, Any]:
    """
    resolution_order 3단계로 test-tools.yaml을 해석하여 결과 dict 반환.

    반환 dict:
        ok: bool
        command: str
        tiers: dict
        source: "project" | "global" | "infer"
        stack: str
        error: str (ok=False 시)
    """
    # 프로젝트 루트 결정
    if project_root is None:
        project_root = pathlib.Path.cwd()

    # 1순위: {project}/.opal/test-tools.yaml
    project_yaml_path = project_root / ".opal" / "test-tools.yaml"
    if project_yaml_path.exists():
        try:
            data = _load_yaml_strict(project_yaml_path)
            tiers = data.get("tiers", {})
            return {
                "ok": True,
                "command": "resolve",
                "tiers": tiers,
                "source": "project",
                "stack": stack or data.get("stack", {}),
            }
        except ValueError as exc:
            return {
                "ok": False,
                "command": "resolve",
                "error": "yaml_parse_failed",
                "detail": str(exc),
            }

    # 2순위: OPAL_TEST_TOOLS_GLOBAL 환경변수 → ~/.opal/templates/test-tools.yaml
    # OPAL_TEST_TOOLS_GLOBAL 미설정 시 자동 탐색은 하지 않음 — 추론 폴백으로 진행.
    # (test isolation: 테스트가 OPAL_TEST_TOOLS_GLOBAL을 설정하지 않으면 실 시스템
    #  글로벌 템플릿이 개입하지 않도록 보장. 프로덕션 install은 env var을 설정한다.)
    global_yaml_env = os.environ.get("OPAL_TEST_TOOLS_GLOBAL")
    if not global_yaml_env:
        # env var 미설정 → 글로벌 탐색 건너뜀, 추론으로 진행
        global_yaml_path = None
    else:
        global_yaml_path = pathlib.Path(global_yaml_env)

    if global_yaml_path is not None and global_yaml_path.exists():
        try:
            data = _load_yaml_strict(global_yaml_path)
            tiers = data.get("tiers", {})
            return {
                "ok": True,
                "command": "resolve",
                "tiers": tiers,
                "source": "global",
                "stack": stack or data.get("stack", {}),
            }
        except ValueError as exc:
            return {
                "ok": False,
                "command": "resolve",
                "error": "yaml_parse_failed",
                "detail": str(exc),
            }

    # 3순위: package.json / pyproject.toml 추론 폴백
    inferred = _infer_from_package_json(project_root) or _infer_from_pyproject(project_root)
    if inferred:
        return {
            "ok": True,
            "command": "resolve",
            "tiers": inferred.get("tiers", {}),
            "source": "infer",
            "stack": stack or inferred.get("stack", {}),
        }

    # 러너를 전혀 찾을 수 없음
    return {
        "ok": False,
        "command": "resolve",
        "error": "no_runner",
        "detail": "test-tools.yaml not found and could not infer from package.json/pyproject.toml",
    }
