"""
@header {
  "module": "environment",
  "layer": "util",
  "domain": "opal-tools",
  "description": "프로젝트 E2E 환경 설정(`.opal/e2e/environment.json`)의 스키마 원본. 파일 적재(load)·순수 검증(validate, 위반 {path,code,detail} 11종)·서비스 의존 순서(service_order)·서비스 기동 값 확정(render_service: 치환 토큰 6종과 from_env 해석, cwd 실제 경로의 루트 내부 확인)·표면 선택(select_surface)을 제공한다. 비밀 원문 판정은 lib/e2e/redaction.redact_text를 재사용한다. 파일을 쓰지 않고 프로세스를 띄우지 않으며 OS 분기를 두지 않는다.",
  "exports": ["SCHEMA_VERSION", "CONFIG_RELPATH", "SURFACE_KINDS", "DESKTOP_KINDS", "VIOLATION_CODES", "load", "validate", "normalize", "service_order", "render_service", "select_surface"],
  "depends": ["redaction"]
}

lib.e2e.environment — 필드 표와 검증 규칙은 이 모듈에만 둔다. README·스킬 문서는 표를
복제하지 않고 이 모듈을 가리킨다. 검증 결과의 detail에는 설정 값 원문을 싣지 않는다
(비밀 원문이 stdout으로 새지 않게 한다).
"""

from __future__ import annotations

import copy
import json
import os
import posixpath
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from lib.e2e import redaction as e2e_redaction

SCHEMA_VERSION = "1.0"
CONFIG_RELPATH = os.path.join(".opal", "e2e", "environment.json")

SURFACE_KINDS = ("web", "api", "macos-app", "windows-app", "linux-app", "human")
DESKTOP_KINDS = ("macos-app", "windows-app", "linux-app")
HEALTH_TYPES = ("http", "port")

VIOLATION_CODES = (
    "required_field_missing",
    "unknown_field",
    "invalid_type",
    "invalid_kind",
    "duplicate_id",
    "unknown_service_ref",
    "surface_target_conflict",
    "dependency_cycle",
    "invalid_placeholder",
    "path_escape",
    "secret_literal",
)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_STARTUP_TIMEOUT_S = 60
DEFAULT_WEB_PATH = "/"
DEFAULT_API_HEALTH_PATH = "/health"
DEFAULT_HEALTH = {"type": "port"}

_ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")
_ENV_NAME_PATTERN = re.compile(r"^[A-Z_][A-Z0-9_]*$")
_SECRET_KEY_MARKERS = ("PASS", "SECRET", "TOKEN", "API_KEY", "CREDENTIAL", "PRIVATE_KEY")

# `{{`·`}}`는 리터럴 중괄호다. 그 밖의 `{...}`는 아래 토큰만 허용한다.
_PLACEHOLDER_PATTERN = re.compile(r"\{\{|\}\}|\{([^{}]*)\}")
_SIMPLE_TOKENS = ("host", "port", "python", "project_root")
_SERVICE_TOKEN_PATTERN = re.compile(r"^service\.([a-z][a-z0-9-]*)\.(url|port)$")

_TOP_KEYS = ("schema_version", "services", "surfaces", "secrets", "data", "external_integrations")
_TOP_REQUIRED = ("schema_version", "services", "surfaces")
_SERVICE_KEYS = ("id", "command", "cwd", "env", "depends_on", "health", "startup_timeout_s")
_HTTP_HEALTH_KEYS = ("type", "path", "expect_status", "json_field")
_SECRET_KEYS = ("name", "purpose")
_DATA_KEYS = ("prepare", "restore", "notes")
_INTEGRATION_KEYS = ("name", "policy", "notes")
_SURFACE_KEYS_BY_KIND = {
    "web": ("id", "kind", "service", "url", "path"),
    "api": ("id", "kind", "service", "url", "health_path"),
    "macos-app": ("id", "kind", "app"),
    "windows-app": ("id", "kind", "app"),
    "linux-app": ("id", "kind", "app"),
    "human": ("id", "kind"),
}
_APP_KEYS = ("path", "launch")


# ── 적재 ─────────────────────────────────────────────────────────────────────

def load(project_root: str, file: Optional[str] = None) -> Dict[str, Any]:
    """설정 파일을 읽어 검증한다.

    반환: `{status: "ok"|"missing"|"invalid", config, violations, path}`.
    `config`는 status가 ok일 때 기본값을 채운 정규화 사본이고, 그 밖에는 None이다.
    """
    if file:
        path = Path(file)
        if not path.is_absolute():
            path = Path.cwd() / path
    else:
        path = Path(project_root) / CONFIG_RELPATH
    path_str = str(path)

    if not path.is_file():
        return {"status": "missing", "config": None, "violations": [], "path": path_str}

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, OSError) as exc:
        return _invalid(path_str, [_v("$", "invalid_type", f"file is not readable UTF-8 JSON: {type(exc).__name__}")])
    except json.JSONDecodeError as exc:
        # 원문 조각을 싣지 않도록 위치만 남긴다.
        return _invalid(path_str, [_v("$", "invalid_type", f"JSON parse error at line {exc.lineno} column {exc.colno}")])

    violations = validate(raw)
    if violations:
        return _invalid(path_str, violations)
    return {"status": "ok", "config": normalize(raw), "violations": [], "path": path_str}


def _invalid(path: str, violations: List[Dict[str, str]]) -> Dict[str, Any]:
    return {"status": "invalid", "config": None, "violations": violations, "path": path}


def _v(path: str, code: str, detail: str) -> Dict[str, str]:
    return {"path": path, "code": code, "detail": detail}


# ── 검증 ─────────────────────────────────────────────────────────────────────

def validate(config: Any) -> List[Dict[str, str]]:
    """설정 dict를 검증해 위반 목록을 돌려준다. 빈 목록이면 유효하다.

    파일 시스템을 보지 않는다. `path_escape`는 cwd 문자열로만 판정한다 — `{project_root}` 외
    치환 토큰이 있거나 어휘 정규화 결과가 루트 밖이면 위반이다.
    """
    out: List[Dict[str, str]] = []
    if not isinstance(config, dict):
        out.append(_v("$", "invalid_type", "top level must be a JSON object"))
        return out

    _check_keys(config, "", _TOP_KEYS, out)
    for key in _TOP_REQUIRED:
        if key not in config:
            out.append(_v(key, "required_field_missing", f"'{key}' is required"))

    if "schema_version" in config and config["schema_version"] != SCHEMA_VERSION:
        out.append(_v("schema_version", "invalid_type", f"schema_version must be \"{SCHEMA_VERSION}\""))

    services = config.get("services")
    service_ids: List[str] = []
    if "services" in config:
        if not isinstance(services, list):
            out.append(_v("services", "invalid_type", "services must be an array"))
            services = []
        service_ids = _collect_ids(services, "services", out)
        for index, service in enumerate(services):
            _validate_service(service, f"services[{index}]", service_ids, out)
        _check_cycles(services, out)

    surfaces = config.get("surfaces")
    if "surfaces" in config:
        if not isinstance(surfaces, list):
            out.append(_v("surfaces", "invalid_type", "surfaces must be an array"))
            surfaces = []
        _collect_ids(surfaces, "surfaces", out)
        for index, surface in enumerate(surfaces):
            _validate_surface(surface, f"surfaces[{index}]", service_ids, out)

    if "secrets" in config:
        _validate_secrets(config["secrets"], out)
    if "data" in config:
        _validate_data(config["data"], out)
    if "external_integrations" in config:
        _validate_integrations(config["external_integrations"], out)

    _scan_secret_literals(config, "", out)
    return out


def _join(prefix: str, key: str) -> str:
    return f"{prefix}.{key}" if prefix else key


def _check_keys(obj: Mapping[str, Any], prefix: str, allowed, out, *, skip=()) -> None:
    for key in obj:
        if key in skip:
            continue
        if key not in allowed:
            out.append(_v(_join(prefix, str(key)), "unknown_field", f"unknown field '{key}'"))


def _collect_ids(items: list, prefix: str, out) -> List[str]:
    seen: List[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        ident = item.get("id")
        if not isinstance(ident, str):
            continue
        if ident in seen:
            out.append(_v(f"{prefix}[{index}].id", "duplicate_id", f"duplicate id '{ident}'"))
        else:
            seen.append(ident)
    return seen


def _check_id(obj: dict, path: str, out) -> None:
    if "id" not in obj:
        out.append(_v(f"{path}.id", "required_field_missing", "'id' is required"))
    elif not isinstance(obj["id"], str) or not _ID_PATTERN.match(obj["id"]):
        out.append(_v(f"{path}.id", "invalid_type", "id must match ^[a-z][a-z0-9-]*$"))


def _is_string_list(value: Any, *, non_empty: bool) -> bool:
    if not isinstance(value, list) or (non_empty and not value):
        return False
    return all(isinstance(item, str) for item in value)


def _is_positive_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def _validate_service(service: Any, path: str, service_ids: List[str], out) -> None:
    if not isinstance(service, dict):
        out.append(_v(path, "invalid_type", "service must be an object"))
        return
    _check_keys(service, path, _SERVICE_KEYS, out)
    _check_id(service, path, out)

    if "command" not in service:
        out.append(_v(f"{path}.command", "required_field_missing", "'command' is required"))
    elif not _is_string_list(service["command"], non_empty=True):
        out.append(_v(f"{path}.command", "invalid_type", "command must be a non-empty array of strings"))
    else:
        for index, arg in enumerate(service["command"]):
            _check_placeholders(arg, f"{path}.command[{index}]", service_ids, out)

    if "cwd" in service:
        cwd = service["cwd"]
        if not isinstance(cwd, str):
            out.append(_v(f"{path}.cwd", "invalid_type", "cwd must be a string"))
        else:
            _check_placeholders(cwd, f"{path}.cwd", service_ids, out)
            if _cwd_escapes(cwd):
                out.append(_v(f"{path}.cwd", "path_escape", "cwd must stay inside the project root"))

    if "env" in service:
        _validate_env(service["env"], f"{path}.env", service_ids, out)

    if "depends_on" in service:
        deps = service["depends_on"]
        if not _is_string_list(deps, non_empty=False):
            out.append(_v(f"{path}.depends_on", "invalid_type", "depends_on must be an array of service ids"))
        else:
            for index, dep in enumerate(deps):
                if dep not in service_ids:
                    out.append(_v(f"{path}.depends_on[{index}]", "unknown_service_ref", f"unknown service '{dep}'"))

    if "health" in service:
        _validate_health(service["health"], f"{path}.health", service_ids, out)

    if "startup_timeout_s" in service and not _is_positive_number(service["startup_timeout_s"]):
        out.append(_v(f"{path}.startup_timeout_s", "invalid_type", "startup_timeout_s must be a positive number"))


def _is_secret_key(name: str) -> bool:
    upper = name.upper()
    return any(marker in upper for marker in _SECRET_KEY_MARKERS)


def _validate_env(env: Any, path: str, service_ids: List[str], out) -> None:
    if not isinstance(env, dict):
        out.append(_v(path, "invalid_type", "env must be an object"))
        return
    for name, value in env.items():
        item_path = f"{path}.{name}"
        if not _ENV_NAME_PATTERN.match(str(name)):
            out.append(_v(item_path, "invalid_type", "env name must match ^[A-Z_][A-Z0-9_]*$"))
        if isinstance(value, str):
            if _is_secret_key(str(name)):
                out.append(_v(item_path, "secret_literal", "secret-like env must use {\"from_env\": NAME}, not a literal"))
            else:
                _check_placeholders(value, item_path, service_ids, out)
        elif isinstance(value, dict):
            _check_keys(value, item_path, ("from_env",), out)
            ref = value.get("from_env")
            if "from_env" not in value:
                out.append(_v(f"{item_path}.from_env", "required_field_missing", "'from_env' is required"))
            elif not isinstance(ref, str) or not _ENV_NAME_PATTERN.match(ref):
                out.append(_v(f"{item_path}.from_env", "invalid_type", "from_env must be an env var name"))
        else:
            out.append(_v(item_path, "invalid_type", "env value must be a string or {\"from_env\": NAME}"))


def _validate_health(health: Any, path: str, service_ids: List[str], out) -> None:
    if not isinstance(health, dict):
        out.append(_v(path, "invalid_type", "health must be an object"))
        return
    if "type" not in health:
        out.append(_v(f"{path}.type", "required_field_missing", "'type' is required"))
        return
    kind = health["type"]
    if kind not in HEALTH_TYPES:
        out.append(_v(f"{path}.type", "invalid_kind", "health.type must be one of http, port"))
        return
    if kind == "port":
        _check_keys(health, path, ("type",), out)
        return
    _check_keys(health, path, _HTTP_HEALTH_KEYS, out)
    if "path" not in health:
        out.append(_v(f"{path}.path", "required_field_missing", "'path' is required for http health"))
    elif not isinstance(health["path"], str) or not health["path"].startswith("/"):
        out.append(_v(f"{path}.path", "invalid_type", "health.path must be a string starting with '/'"))
    else:
        _check_placeholders(health["path"], f"{path}.path", service_ids, out)
    if "expect_status" in health:
        status = health["expect_status"]
        if not isinstance(status, int) or isinstance(status, bool) or not 100 <= status <= 599:
            out.append(_v(f"{path}.expect_status", "invalid_type", "expect_status must be an HTTP status integer"))
    if "json_field" in health and (not isinstance(health["json_field"], str) or not health["json_field"]):
        out.append(_v(f"{path}.json_field", "invalid_type", "json_field must be a non-empty string"))


def _check_placeholders(text: str, path: str, service_ids: List[str], out) -> None:
    for match in _PLACEHOLDER_PATTERN.finditer(text):
        token = match.group(1)
        if token is None:
            continue  # `{{` / `}}` 리터럴
        if token in _SIMPLE_TOKENS:
            continue
        service_match = _SERVICE_TOKEN_PATTERN.match(token)
        if service_match:
            if service_match.group(1) not in service_ids:
                out.append(_v(path, "unknown_service_ref", f"placeholder refers to unknown service '{service_match.group(1)}'"))
            continue
        out.append(_v(path, "invalid_placeholder", f"unsupported placeholder '{{{token}}}'"))


def _cwd_escapes(cwd: str) -> bool:
    """cwd 문자열이 프로젝트 루트를 벗어날 수 있으면 True.

    `{project_root}` 외 치환 토큰(`{python}`·`{host}`·`{port}`·`{service.*}`)은 치환 값이
    루트 밖 절대경로일 수 있으므로 cwd에서는 path_escape로 본다. symlink 해석을 포함한
    최종 판정은 render_service가 치환 뒤 realpath로 다시 한다.
    """
    for match in _PLACEHOLDER_PATTERN.finditer(cwd):
        token = match.group(1)
        if token is not None and token != "project_root":
            return True
    text = cwd.replace("\\", "/")
    if text.startswith("{project_root}"):
        text = "." + text[len("{project_root}"):]
    if text.startswith("/") or re.match(r"^[A-Za-z]:", text):
        return True
    normalized = posixpath.normpath(text)
    return normalized == ".." or normalized.startswith("../")


def _check_cycles(services: list, out) -> None:
    graph: Dict[str, List[str]] = {}
    for service in services:
        if isinstance(service, dict) and isinstance(service.get("id"), str):
            deps = service.get("depends_on")
            graph.setdefault(service["id"], [d for d in deps if isinstance(d, str)] if isinstance(deps, list) else [])
    cycle = _find_cycle(graph)
    if cycle:
        index = next(i for i, s in enumerate(services) if isinstance(s, dict) and s.get("id") == cycle[0])
        out.append(_v(f"services[{index}].depends_on", "dependency_cycle", "dependency cycle: " + " -> ".join(cycle)))


def _find_cycle(graph: Dict[str, List[str]]) -> Optional[List[str]]:
    state: Dict[str, int] = {}  # 1=visiting, 2=done
    stack: List[str] = []

    def visit(node: str) -> Optional[List[str]]:
        state[node] = 1
        stack.append(node)
        for dep in graph.get(node, []):
            if dep not in graph:
                continue
            if state.get(dep) == 1:
                return stack[stack.index(dep):] + [dep]
            if state.get(dep) is None:
                found = visit(dep)
                if found:
                    return found
        stack.pop()
        state[node] = 2
        return None

    for node in graph:
        if state.get(node) is None:
            found = visit(node)
            if found:
                return found
    return None


def _validate_surface(surface: Any, path: str, service_ids: List[str], out) -> None:
    if not isinstance(surface, dict):
        out.append(_v(path, "invalid_type", "surface must be an object"))
        return
    _check_id(surface, path, out)
    if "kind" not in surface:
        out.append(_v(f"{path}.kind", "required_field_missing", "'kind' is required"))
        return
    kind = surface["kind"]
    if kind not in SURFACE_KINDS:
        out.append(_v(f"{path}.kind", "invalid_kind", "kind must be one of " + ", ".join(SURFACE_KINDS)))
        return
    _check_keys(surface, path, _SURFACE_KEYS_BY_KIND[kind], out)

    if kind in ("web", "api"):
        has_service = "service" in surface
        has_url = "url" in surface
        if has_service and has_url:
            out.append(_v(path, "surface_target_conflict", "declare exactly one of 'service' or 'url'"))
        elif not has_service and not has_url:
            out.append(_v(f"{path}.service", "required_field_missing", "one of 'service' or 'url' is required"))
        if has_service:
            ref = surface["service"]
            if not isinstance(ref, str):
                out.append(_v(f"{path}.service", "invalid_type", "service must be a service id"))
            elif ref not in service_ids:
                out.append(_v(f"{path}.service", "unknown_service_ref", f"unknown service '{ref}'"))
        if has_url:
            url = surface["url"]
            if not isinstance(url, str) or not re.match(r"^https?://[^/\s]+", url):
                out.append(_v(f"{path}.url", "invalid_type", "url must be an http(s) URL"))
        path_key = "path" if kind == "web" else "health_path"
        if path_key in surface:
            value = surface[path_key]
            if not isinstance(value, str) or not value.startswith("/"):
                out.append(_v(f"{path}.{path_key}", "invalid_type", f"{path_key} must be a string starting with '/'"))
        return

    if kind in DESKTOP_KINDS:
        if "app" not in surface:
            out.append(_v(f"{path}.app", "required_field_missing", "'app' is required for desktop surfaces"))
            return
        app = surface["app"]
        if not isinstance(app, dict):
            out.append(_v(f"{path}.app", "invalid_type", "app must be an object"))
            return
        _check_keys(app, f"{path}.app", _APP_KEYS, out)
        if "path" not in app and "launch" not in app:
            out.append(_v(f"{path}.app.path", "required_field_missing", "app needs 'path' or 'launch'"))
        if "path" in app and (not isinstance(app["path"], str) or not app["path"]):
            out.append(_v(f"{path}.app.path", "invalid_type", "app.path must be a non-empty string"))
        if "launch" in app and not _is_string_list(app["launch"], non_empty=True):
            out.append(_v(f"{path}.app.launch", "invalid_type", "app.launch must be a non-empty array of strings"))


def _validate_secrets(secrets: Any, out) -> None:
    if not isinstance(secrets, list):
        out.append(_v("secrets", "invalid_type", "secrets must be an array"))
        return
    seen: List[str] = []
    for index, item in enumerate(secrets):
        path = f"secrets[{index}]"
        if not isinstance(item, dict):
            out.append(_v(path, "invalid_type", "secret must be an object"))
            continue
        if "value" in item:
            out.append(_v(f"{path}.value", "secret_literal", "secret values must not be stored; declare the env var name only"))
        _check_keys(item, path, _SECRET_KEYS, out, skip=("value",))
        name = item.get("name")
        if "name" not in item:
            out.append(_v(f"{path}.name", "required_field_missing", "'name' is required"))
        elif not isinstance(name, str) or not _ENV_NAME_PATTERN.match(name):
            out.append(_v(f"{path}.name", "invalid_type", "name must match ^[A-Z_][A-Z0-9_]*$"))
        elif name in seen:
            out.append(_v(f"{path}.name", "duplicate_id", f"duplicate secret '{name}'"))
        else:
            seen.append(name)
        if "purpose" in item and not isinstance(item["purpose"], str):
            out.append(_v(f"{path}.purpose", "invalid_type", "purpose must be a string"))


def _validate_data(data: Any, out) -> None:
    if not isinstance(data, dict):
        out.append(_v("data", "invalid_type", "data must be an object"))
        return
    _check_keys(data, "data", _DATA_KEYS, out)
    for key in ("prepare", "restore"):
        if key in data and not _is_string_list(data[key], non_empty=True):
            out.append(_v(f"data.{key}", "invalid_type", f"data.{key} must be a non-empty command array"))
    if "notes" in data and not isinstance(data["notes"], str):
        out.append(_v("data.notes", "invalid_type", "data.notes must be a string"))


def _validate_integrations(items: Any, out) -> None:
    if not isinstance(items, list):
        out.append(_v("external_integrations", "invalid_type", "external_integrations must be an array"))
        return
    for index, item in enumerate(items):
        path = f"external_integrations[{index}]"
        if not isinstance(item, dict):
            out.append(_v(path, "invalid_type", "integration must be an object"))
            continue
        _check_keys(item, path, _INTEGRATION_KEYS, out)
        for key in ("name", "policy"):
            if key not in item:
                out.append(_v(f"{path}.{key}", "required_field_missing", f"'{key}' is required"))
            elif not isinstance(item[key], str) or not item[key]:
                out.append(_v(f"{path}.{key}", "invalid_type", f"{key} must be a non-empty string"))
        if "notes" in item and not isinstance(item["notes"], str):
            out.append(_v(f"{path}.notes", "invalid_type", "notes must be a string"))


def _scan_secret_literals(value: Any, path: str, out) -> None:
    """모든 문자열 값을 증적 마스킹 규칙(redact_text)에 통과시켜 비밀 원문을 거부한다.

    `secrets[].value`는 이미 별도 위반으로 잡았으므로 중복 보고하지 않는다.
    """
    if isinstance(value, dict):
        for key, item in value.items():
            child = _join(path, str(key))
            if key == "value" and re.match(r"^secrets\[\d+\]$", path):
                continue
            _scan_secret_literals(item, child, out)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _scan_secret_literals(item, f"{path}[{index}]", out)
    elif isinstance(value, str):
        try:
            _, touched = e2e_redaction.redact_text(value, path=path or "$")
        except e2e_redaction.RedactionError:
            touched = [path]
        if touched and not any(v["path"] == (path or "$") and v["code"] == "secret_literal" for v in out):
            out.append(_v(path or "$", "secret_literal", "value matches a secret pattern; reference an env var instead"))


# ── 정규화·해석 ──────────────────────────────────────────────────────────────

def normalize(config: Mapping[str, Any]) -> Dict[str, Any]:
    """유효한 설정에 기본값을 채운 사본을 돌려준다. 원본은 바꾸지 않는다."""
    result = copy.deepcopy(dict(config))
    result["services"] = [_normalize_service(s) for s in result.get("services", [])]
    surfaces = []
    for surface in result.get("surfaces", []):
        surface = dict(surface)
        if surface.get("kind") == "web":
            surface.setdefault("path", DEFAULT_WEB_PATH)
        elif surface.get("kind") == "api":
            surface.setdefault("health_path", DEFAULT_API_HEALTH_PATH)
        surfaces.append(surface)
    result["surfaces"] = surfaces
    result.setdefault("secrets", [])
    return result


def _normalize_service(service: Mapping[str, Any]) -> Dict[str, Any]:
    out = copy.deepcopy(dict(service))
    out.setdefault("cwd", ".")
    out.setdefault("env", {})
    out.setdefault("depends_on", [])
    health = dict(out.get("health") or DEFAULT_HEALTH)
    if health.get("type") == "http":
        health.setdefault("expect_status", 200)
        health.setdefault("json_field", None)
    out["health"] = health
    out.setdefault("startup_timeout_s", DEFAULT_STARTUP_TIMEOUT_S)
    return out


def service_order(config: Mapping[str, Any]) -> List[str]:
    """의존 순서(선언 순서를 안정 기준으로 한 위상 정렬)의 서비스 id 목록을 돌려준다.

    순환이 있으면 ValueError를 올린다 — validate를 통과한 설정에서는 일어나지 않는다.
    """
    services = [s for s in config.get("services", []) if isinstance(s, dict)]
    ids = [s["id"] for s in services]
    deps = {s["id"]: [d for d in s.get("depends_on", []) if d in ids] for s in services}
    ordered: List[str] = []
    while len(ordered) < len(ids):
        progressed = False
        for ident in ids:
            if ident in ordered:
                continue
            if all(dep in ordered for dep in deps[ident]):
                ordered.append(ident)
                progressed = True
                break
        if not progressed:
            raise ValueError("dependency cycle among services: " + ", ".join(i for i in ids if i not in ordered))
    return ordered


def _is_within(path: str, root: str) -> bool:
    try:
        return os.path.commonpath([path, root]) == root
    except ValueError:  # 드라이브가 다른 경로
        return False


def _service_url(host: str, port: int) -> str:
    return f"http://{host}:{port}"


def _substitute(text: str, values: Mapping[str, str]) -> str:
    def _sub(match: "re.Match[str]") -> str:
        whole = match.group(0)
        if whole == "{{":
            return "{"
        if whole == "}}":
            return "}"
        token = match.group(1)
        if token not in values:
            raise ValueError(f"unresolvable placeholder '{{{token}}}'")
        return values[token]

    return _PLACEHOLDER_PATTERN.sub(_sub, text)


def render_service(
    service: Mapping[str, Any],
    *,
    port: int,
    host: str = DEFAULT_HOST,
    ports_by_id: Mapping[str, int],
    project_root: str,
) -> Dict[str, Any]:
    """서비스 선언 1건의 argv·cwd·env·health를 확정한다.

    - 치환 토큰: `{host}`·`{port}`·`{python}`(현재 인터프리터 sys.executable)·`{project_root}`·
      `{service.<id>.url}`·`{service.<id>.port}`.
    - env의 `{"from_env": NAME}`은 현재 프로세스 환경에서 읽는다. 없으면 설정하지 않고
      `missing_env`에 이름을 남긴다.
    - argv[0]가 경로가 아니면 PATH에서 실행 파일을 찾아 절대경로로 바꾼다(찾지 못하면 그대로).
    - 치환한 cwd의 실제 경로(symlink 해석)가 project_root 밖이면 `path_escape`로 시작하는
      ValueError를 올린다.
    반환 env는 덮어쓸 항목만 담는다 — 부모 환경 병합은 기동하는 쪽이 한다.
    """
    svc = _normalize_service(service)
    root = str(Path(project_root).resolve())
    values: Dict[str, str] = {
        "host": host,
        "port": str(port),
        "python": sys.executable,
        "project_root": root,
    }
    for ident, other_port in ports_by_id.items():
        values[f"service.{ident}.port"] = str(other_port)
        values[f"service.{ident}.url"] = _service_url(host, other_port)
    values.setdefault(f"service.{svc['id']}.port", str(port))
    values.setdefault(f"service.{svc['id']}.url", _service_url(host, port))

    argv = [_substitute(arg, values) for arg in svc["command"]]

    env: Dict[str, str] = {}
    missing_env: List[str] = []
    for name, value in svc["env"].items():
        if isinstance(value, dict):
            ref = value["from_env"]
            if ref in os.environ:
                env[name] = os.environ[ref]
            else:
                missing_env.append(ref)
        else:
            env[name] = _substitute(value, values)

    if argv and os.sep not in argv[0] and "/" not in argv[0]:
        search_path = env.get("PATH", os.environ.get("PATH"))
        resolved = shutil.which(argv[0], path=search_path)
        if resolved:
            argv[0] = resolved

    cwd_text = _substitute(svc["cwd"], values)
    cwd_path = Path(cwd_text)
    if not cwd_path.is_absolute():
        cwd_path = Path(root) / cwd_path
    cwd = os.path.normpath(str(cwd_path))
    if not _is_within(os.path.realpath(cwd), root):
        raise ValueError("path_escape: cwd resolves outside the project root")

    health = dict(svc["health"])
    if health.get("type") == "http":
        health["path"] = _substitute(health["path"], values)

    return {
        "id": svc["id"],
        "argv": argv,
        "cwd": cwd,
        "env": env,
        "missing_env": missing_env,
        "health": health,
        "startup_timeout_s": float(svc["startup_timeout_s"]),
        "host": host,
        "port": int(port),
        "url": _service_url(host, port),
    }


def select_surface(config: Mapping[str, Any], kind: str, surface_ref: Optional[str]) -> Dict[str, Any]:
    """종류가 `kind`인 표면 하나를 고른다.

    - 0개: `{status:"missing", detail_code:"e2e_env_surface_missing"}`
    - 1개: 그 표면
    - 2개 이상: `surface_ref`의 첫 `.` 앞 조각과 id가 같은 표면. 없으면
      `{status:"ambiguous", detail_code:"e2e_env_surface_ambiguous"}`
    반환: `{status: ok|missing|ambiguous, surface, candidates, detail_code}`.
    """
    candidates = [s for s in config.get("surfaces", []) if isinstance(s, dict) and s.get("kind") == kind]
    ids = [s.get("id") for s in candidates]
    if not candidates:
        return {"status": "missing", "surface": None, "candidates": ids, "detail_code": "e2e_env_surface_missing"}
    if len(candidates) == 1:
        return {"status": "ok", "surface": candidates[0], "candidates": ids, "detail_code": None}
    head = surface_ref.split(".", 1)[0] if isinstance(surface_ref, str) and surface_ref else None
    for surface in candidates:
        if head is not None and surface.get("id") == head:
            return {"status": "ok", "surface": surface, "candidates": ids, "detail_code": None}
    return {"status": "ambiguous", "surface": None, "candidates": ids, "detail_code": "e2e_env_surface_ambiguous"}
