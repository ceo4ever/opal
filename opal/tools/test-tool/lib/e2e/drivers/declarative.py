"""JSON-backed browser driver for project-local ``.opal/e2e/drivers`` manifests.

The manifest is intentionally a thin command adapter.  Each operation executes one
argv template and the command's final stdout line must be a JSON object satisfying
the frozen §B.2 output contract.  Drivers needing richer protocol logic remain
ordinary Python drivers.
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from lib.e2e import drivers as e2e_drivers


class DeclarativeManifestError(e2e_drivers.DriverError):
    """A project-local driver manifest is malformed or cannot be executed."""


def load_project_manifests(project_root: str) -> Dict[Tuple[str, Optional[str]], Any]:
    """Return factories declared by ``<project>/.opal/e2e/drivers/*.json``.

    A declarative driver is registered only when all frozen §B.2 operations are
    present.  This is the registration-side half of the conformance gate; the
    ``driver-verify`` command still performs the required live execution check.
    """
    directory = Path(project_root) / ".opal" / "e2e" / "drivers"
    if not directory.is_dir():
        return {}
    factories: Dict[Tuple[str, Optional[str]], Any] = {}
    for path in sorted(directory.glob("*.json")):
        manifest = load_driver_manifest(path)
        name = str(manifest["driver"])
        mode = manifest.get("session_mode")
        key = (name, mode)
        if key in factories:
            raise DeclarativeManifestError(
                "declarative_driver_duplicate", f"duplicate driver variant {name}/{mode}"
            )

        def factory(*, runtime_context=None, _manifest=manifest, _path=path, **_kwargs):
            return DeclarativeDriver(
                _manifest, manifest_path=_path, runtime_context=runtime_context
            )

        factory.driver_manifest = manifest
        factories[key] = factory
    return factories


def load_driver_manifest(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DeclarativeManifestError(
            "declarative_driver_manifest_unreadable", f"{path}: {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise DeclarativeManifestError(
            "declarative_driver_manifest_invalid", f"{path}: root must be an object"
        )
    name = data.get("driver")
    mode = data.get("session_mode")
    if not isinstance(name, str) or not name.strip():
        raise DeclarativeManifestError(
            "declarative_driver_manifest_invalid", f"{path}: driver is required"
        )
    if mode not in e2e_drivers.SESSION_MODES:
        raise DeclarativeManifestError(
            "declarative_driver_manifest_invalid", f"{path}: invalid session_mode {mode!r}"
        )
    operations = data.get("ops")
    if not isinstance(operations, Mapping):
        raise DeclarativeManifestError(
            "declarative_driver_manifest_invalid", f"{path}: ops must be an object"
        )
    missing = [name for name in e2e_drivers.DRIVER_OPERATIONS if name not in operations]
    if missing:
        raise DeclarativeManifestError(
            "declarative_driver_conformance_required",
            f"{path}: missing §B.2 operations {missing}",
        )
    for operation, spec in operations.items():
        if operation not in e2e_drivers.DRIVER_OPERATIONS or not isinstance(spec, Mapping):
            raise DeclarativeManifestError(
                "declarative_driver_manifest_invalid", f"{path}: invalid op {operation!r}"
            )
        if operation == "act":
            mapping = spec.get("map")
            if "argv" not in spec and not isinstance(mapping, Mapping):
                raise DeclarativeManifestError(
                    "declarative_driver_manifest_invalid", f"{path}: act needs argv or map"
                )
        elif not isinstance(spec.get("argv"), list):
            raise DeclarativeManifestError(
                "declarative_driver_manifest_invalid", f"{path}: {operation}.argv must be an array"
            )
    return data


class DeclarativeDriver(e2e_drivers.BrowserDriver):
    """Execute a validated project-local JSON driver manifest."""

    def __init__(
        self,
        manifest: Mapping[str, Any],
        *,
        manifest_path: Path,
        runtime_context: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self.manifest = dict(manifest)
        self.manifest_path = Path(manifest_path)
        self.runtime_context = dict(runtime_context or {})
        self.name = str(self.manifest["driver"])
        self.session_mode = self.manifest.get("session_mode")
        self.operations = tuple(e2e_drivers.DRIVER_OPERATIONS)
        self.binary_argv, self.resolution_source = self._resolve_binary()
        self.binary_path = self.binary_argv[0] if self.binary_argv else None
        self.declared_version = self._detect_version()

    def dispatch(self, operation: str, payload: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        if operation not in e2e_drivers.DRIVER_OPERATIONS:
            return super().dispatch(operation, payload)
        request = dict(payload or {})
        if operation == "wait" and request.get("wait_kind") not in e2e_drivers.WAIT_KINDS:
            return super().dispatch(operation, request)
        if not self.binary_argv:
            if operation == "probe":
                return self._unavailable_probe("declarative_driver_binary_not_found")
            raise DeclarativeManifestError(
                "declarative_driver_binary_not_found", self.name
            )
        spec = dict(self.manifest["ops"][operation])
        argv_template = spec.get("argv")
        if operation == "act" and argv_template is None:
            kind = (request.get("action") or {}).get("kind")
            argv_template = (spec.get("map") or {}).get(kind)
            if argv_template is None:
                raise DeclarativeManifestError(
                    "declarative_driver_action_unsupported", str(kind)
                )
        argv = [*self.binary_argv, *self._render_argv(argv_template, request)]
        try:
            completed = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                timeout=float(spec.get("timeout_seconds", 120)),
                env=self._environment(),
            )
        except FileNotFoundError as exc:
            if operation == "probe":
                return self._unavailable_probe("declarative_driver_binary_not_found")
            raise DeclarativeManifestError("declarative_driver_binary_not_found", str(exc)) from exc
        except subprocess.TimeoutExpired as exc:
            raise DeclarativeManifestError(
                f"declarative_driver_{operation}_timeout", str(exc)
            ) from exc
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip()[:400]
            if operation == "probe":
                return self._unavailable_probe(
                    str(spec.get("unavailable_reason") or "declarative_driver_probe_failed")
                )
            raise DeclarativeManifestError(
                f"declarative_driver_{operation}_failed", detail or f"exit={completed.returncode}"
            )
        output = self._parse_output(completed.stdout, operation)
        if operation == "probe":
            output.setdefault("available", True)
            output.setdefault("version", self.declared_version)
            output.setdefault("capabilities", self._capability_table(output.get("capabilities")))
        return output

    def _resolve_binary(self) -> Tuple[Sequence[str], Optional[str]]:
        spec = self.manifest.get("binary") or {}
        environment = self._environment()
        env_name = spec.get("env")
        if env_name and environment.get(str(env_name)):
            return tuple(shlex.split(environment[str(env_name)])), f"env:{env_name}"
        for candidate in spec.get("discover") or []:
            expanded = os.path.expanduser(str(candidate))
            resolved = shutil.which(expanded)
            if resolved:
                return (resolved,), "discover"
        return (), None

    def _detect_version(self) -> Optional[str]:
        spec = self.manifest.get("version") or {}
        argv = spec.get("argv")
        if not self.binary_argv or not isinstance(argv, list):
            return None
        try:
            completed = subprocess.run(
                [*self.binary_argv, *[str(item) for item in argv]],
                capture_output=True,
                text=True,
                timeout=float(spec.get("timeout_seconds", 10)),
                env=self._environment(),
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if completed.returncode != 0:
            return None
        text = (completed.stdout or completed.stderr or "").strip()
        return text.splitlines()[-1].strip() if text else None

    def _render_argv(self, template: Any, request: Mapping[str, Any]) -> Sequence[str]:
        if not isinstance(template, list):
            raise DeclarativeManifestError(
                "declarative_driver_manifest_invalid", "argv must be an array"
            )
        values: Dict[str, Any] = dict(request)
        for nested in ("action", "assertion", "condition"):
            item = request.get(nested)
            if isinstance(item, Mapping):
                values.update(item)
        rendered = []
        for item in template:
            try:
                rendered.append(str(item).format_map(values))
            except KeyError as exc:
                raise DeclarativeManifestError(
                    "declarative_driver_template_value_missing", str(exc.args[0])
                ) from exc
        return rendered

    def _parse_output(self, stdout: str, operation: str) -> Dict[str, Any]:
        text = (stdout or "").strip()
        if not text:
            raise DeclarativeManifestError(
                f"declarative_driver_{operation}_empty_output", self.name
            )
        try:
            value = json.loads(text.splitlines()[-1])
        except json.JSONDecodeError as exc:
            raise DeclarativeManifestError(
                f"declarative_driver_{operation}_bad_json", text[:400]
            ) from exc
        if not isinstance(value, dict):
            raise DeclarativeManifestError(
                f"declarative_driver_{operation}_bad_json", "output must be an object"
            )
        return value

    def _environment(self) -> Dict[str, str]:
        configured = self.runtime_context.get("env")
        return dict(configured) if isinstance(configured, Mapping) else dict(os.environ)

    def _capability_table(self, observed: Any = None) -> Dict[str, Dict[str, Any]]:
        table = e2e_drivers.default_capabilities()
        declared = self.manifest.get("capabilities") or {}
        for key in e2e_drivers.CAPABILITY_KEYS:
            value = declared.get(key)
            if value in {"probe", "native", "exec"}:
                table[key] = {
                    "available": True,
                    "route": "native" if value == "native" else "exec",
                    "probed": True,
                }
            elif value == "none":
                table[key] = {"available": False, "route": "exec", "probed": True}
        if isinstance(observed, Mapping):
            table.update({key: dict(value) for key, value in observed.items() if isinstance(value, Mapping)})
        return table

    def _unavailable_probe(self, reason: str) -> Dict[str, Any]:
        return {
            "available": False,
            "version": self.declared_version,
            "unavailable_reason": reason,
            "capabilities": self._capability_table(),
        }
