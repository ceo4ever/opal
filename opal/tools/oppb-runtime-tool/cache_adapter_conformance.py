"""
@header {
  "module": "cache_adapter_conformance",
  "task": "132",
  "layer": "util",
  "domain": "oppb-runtime",
  "description": "OPPB cache adapter conformance suite — build cache adapter가 입력 변경을 실제로 검출하고 candidate별 overlay를 격리하는지 실행으로 증명한다. clean_input·source_delta·config_delta·dependency_delta·parallel_overlay·stale_seed 6항목을 실제 파일시스템 fixture와 실제 adapter 프로세스로 실행하며 mock·patch를 쓰지 않는다. 6항목을 모두 통과한 adapter만 `replayable`이고, 하나라도 실패하면 `non_reusable`로 강등되어 그 adapter를 쓰는 명령만 cold 실행된다(제안서 §4.5 \"adapter conformance test가 입력 변경 검출을 보장하지 못하는 opaque cache는 non_reusable로 분류해 해당 명령만 cold 실행한다\"). 판정 결과는 cache root의 conformance receipt로 원자 기록되어 cache.py의 plan-execution·reseed가 재사용한다. 표준 라이브러리만 사용하고 플랫폼 분기를 두지 않는다.",
  "exports": [
    "ADAPTER_CASES", "ConformanceError",
    "run_adapter", "run_conformance", "read_receipt", "receipt_path",
    "classification_of", "adapter_identity"
  ],
  "depends": ["opal/core/references/harness/tool-output-contract.md"]
}
"""

# 표준 라이브러리만 사용한다 (신규 의존성 도입 금지)
from __future__ import annotations

import contextlib
import datetime
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

EXIT_ERROR = 1

# 제안서 §4.5 — adapter가 증명해야 하는 6항목. 순서는 receipt 렌더링 순서이기도 하다.
ADAPTER_CASES = (
    "clean_input",
    "source_delta",
    "config_delta",
    "dependency_delta",
    "parallel_overlay",
    "stale_seed",
)

CONFORMANCE_DIRNAME = "conformance"

ADAPTER_TIMEOUT_SECONDS = 120

# conformance fixture — source·config·dependency 세 축을 각각 단독으로 흔들 수 있게
# 파일을 분리한다. adapter는 이 세 파일을 모두 input으로 받는다.
FIXTURE_FILES = {
    "src/a.py": "A = 1\n",
    "build.config": "optimize = false\n",
    "lockfile.lock": "dep-a==1.0.0\n",
}
FIXTURE_INPUTS = tuple(sorted(FIXTURE_FILES))

# 축별 delta — 각 축이 독립적으로 output manifest를 움직이는지 본다.
CASE_DELTA = {
    "source_delta": ("src/a.py", "A = 2\n"),
    "config_delta": ("build.config", "optimize = true\n"),
    "dependency_delta": ("lockfile.lock", "dep-a==2.0.0\n"),
    "stale_seed": ("src/a.py", "A = 3\n"),
}


class ConformanceError(Exception):
    """cache.py의 `CacheError`로 어댑트되는 conformance 고유 실패."""

    def __init__(self, code, message="", exit_code=EXIT_ERROR, **extra):
        super().__init__(message or code)
        self.code = code
        self.message = message
        self.exit_code = exit_code
        self.extra = extra


def _now():
    return (
        datetime.datetime.now(datetime.timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _atomic_write_json(path, payload):
    """대상 디렉토리에 임시 파일을 만들고 fsync 후 교체한다(부분 쓰기 노출 0).

    형태만 `oppl-runtime-tool/ledger.py:336-377`을 복제한다 — 해당 도구를 import하지 않는다.
    """
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".oppb-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, str(path))
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise
    return payload


# ─────────────────────────────────────────────────────────────────────────────
# adapter identity와 호출 규약
# ─────────────────────────────────────────────────────────────────────────────


def adapter_identity(adapter):
    """adapter의 content hash — build cache key의 `build tool/version` 축이다.

    경로가 아니라 내용으로 식별한다. adapter 본문이 바뀌면 그 adapter가 만든
    cache node는 더 이상 exact hit 대상이 아니다.
    """
    path = pathlib.Path(adapter)
    if not path.is_file():
        raise ConformanceError("adapter_not_found", "받은 값: %s" % adapter)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _adapter_argv(adapter, payload):
    """shebang을 존중해 adapter를 직접 실행한다.

    실행 권한이 없고 `.py`이면 현재 인터프리터로 한 번만 폴백한다. 플랫폼별 분기가
    아니라 adapter 파일 속성에 대한 판정이다.
    """
    path = pathlib.Path(adapter)
    if os.access(str(path), os.X_OK):
        return [str(path), payload]
    if path.suffix == ".py":
        return [sys.executable, str(path), payload]
    raise ConformanceError(
        "adapter_not_executable", "실행 권한이 없고 .py도 아닙니다: %s" % adapter
    )


def _adapter_request(source, overlay, inputs, extra=None):
    request = {
        "source": str(source),
        "overlay": str(overlay),
        "inputs": list(inputs),
    }
    if extra:
        request.update(extra)
    return json.dumps(request, ensure_ascii=False, sort_keys=True)


def _spawn_adapter(adapter, source, overlay, inputs, extra=None):
    pathlib.Path(overlay).mkdir(parents=True, exist_ok=True)
    argv = _adapter_argv(adapter, _adapter_request(source, overlay, inputs, extra))
    return subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def _collect(process, adapter):
    try:
        stdout, stderr = process.communicate(timeout=ADAPTER_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        process.kill()
        process.communicate()
        raise ConformanceError(
            "adapter_timeout", "%ss 안에 끝나지 않았습니다: %s" % (ADAPTER_TIMEOUT_SECONDS, adapter)
        ) from None
    if process.returncode != 0:
        raise ConformanceError(
            "adapter_failed",
            "exit=%s stderr=%s" % (process.returncode, (stderr or "").strip()),
        )
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise ConformanceError(
            "adapter_output_invalid", "stdout이 JSON이 아닙니다: %r (%s)" % (stdout, exc)
        ) from exc
    if not isinstance(payload, dict) or payload.get("ok") is not True:
        raise ConformanceError("adapter_output_invalid", "adapter가 ok를 보고하지 않았습니다: %r" % payload)
    if not isinstance(payload.get("output_manifest"), dict):
        raise ConformanceError("adapter_output_invalid", "output_manifest가 object가 아닙니다: %r" % payload)
    return payload


def run_adapter(adapter, source, overlay, inputs, extra=None):
    """adapter를 한 번 실행하고 결과 manifest를 돌려준다(실제 프로세스, mock 없음)."""
    return _collect(_spawn_adapter(adapter, source, overlay, inputs, extra), adapter)


# ─────────────────────────────────────────────────────────────────────────────
# fixture
# ─────────────────────────────────────────────────────────────────────────────


def _materialize_fixture(root, overrides=None):
    root = pathlib.Path(root)
    for relpath, content in FIXTURE_FILES.items():
        target = root / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    for relpath, content in (overrides or {}).items():
        target = root / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return root


def _overlay_state(overlay):
    """overlay에 실제로 남은 파일 내용 — overlay 격리 판정의 근거다."""
    overlay = pathlib.Path(overlay)
    state = {}
    for path in sorted(overlay.rglob("*")):
        if path.is_file():
            state[str(path.relative_to(overlay))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return state


def _manifest_matches_overlay(payload, overlay):
    """adapter가 선언한 output이 overlay에 실제로 존재하는지 확인한다."""
    overlay = pathlib.Path(overlay)
    manifest = payload.get("output_manifest") or {}
    if not manifest:
        return False
    return all((overlay / relpath).is_file() for relpath in manifest)


def _signature(payload):
    """입력 변경 검출 판정에 쓰는 adapter 출력 지문."""
    return json.dumps(
        {
            "output_manifest": payload.get("output_manifest"),
            "input_key": payload.get("input_key"),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# 6항목
# ─────────────────────────────────────────────────────────────────────────────


def _case_clean_input(adapter, work):
    """baseline 입력에서 adapter가 정상 동작하고 선언한 산출물을 실제로 남기는가."""
    source = _materialize_fixture(work / "clean" / "source")
    overlay = work / "clean" / "overlay"
    payload = run_adapter(adapter, source, overlay, FIXTURE_INPUTS)
    passed = _manifest_matches_overlay(payload, overlay)
    return passed, {"signature": _signature(payload)}, _signature(payload)


def _case_axis_delta(adapter, work, case, baseline_signature):
    """한 축만 흔들었을 때 출력 지문이 baseline과 달라지는가."""
    relpath, content = CASE_DELTA[case]
    source = _materialize_fixture(work / case / "source", {relpath: content})
    overlay = work / case / "overlay"
    payload = run_adapter(adapter, source, overlay, FIXTURE_INPUTS)
    signature = _signature(payload)
    return signature != baseline_signature, {"signature": signature, "changed": relpath}


def _case_parallel_overlay(adapter, work, baseline_signature):
    """서로 다른 입력의 두 candidate를 동시에 실행했을 때 overlay가 격리되는가.

    실제로 두 프로세스를 동시에 띄운다. 하나의 mutable build cache를 공유하면
    overlay 상태가 섞이거나 같은 지문이 나온다 — 둘 다 실패로 본다.
    """
    left_source = _materialize_fixture(work / "parallel" / "a" / "source")
    right_source = _materialize_fixture(
        work / "parallel" / "b" / "source", {"src/a.py": "A = 99\n"}
    )
    left_overlay = work / "parallel" / "a" / "overlay"
    right_overlay = work / "parallel" / "b" / "overlay"

    left_proc = _spawn_adapter(adapter, left_source, left_overlay, FIXTURE_INPUTS)
    right_proc = _spawn_adapter(adapter, right_source, right_overlay, FIXTURE_INPUTS)
    left = _collect(left_proc, adapter)
    right = _collect(right_proc, adapter)

    isolated = _overlay_state(left_overlay) != _overlay_state(right_overlay)
    distinct = _signature(left) != _signature(right)
    unchanged_baseline = _signature(left) == baseline_signature
    passed = bool(isolated and distinct and unchanged_baseline)
    return passed, {
        "isolated_overlays": isolated,
        "distinct_signatures": distinct,
        "left_matches_baseline": unchanged_baseline,
    }


def _case_stale_seed(adapter, work, baseline_signature):
    """warm seed overlay 위에서도 intervening delta를 검출하는가.

    baseline 산출물로 seed한 overlay를 그대로 두고 source만 바꿔 다시 실행한다.
    warm 산출물을 그대로 재사용하는 opaque adapter는 baseline 지문을 반복한다.
    """
    seed_source = _materialize_fixture(work / "seed" / "source")
    seed_overlay = work / "seed" / "overlay"
    run_adapter(adapter, seed_source, seed_overlay, FIXTURE_INPUTS)

    relpath, content = CASE_DELTA["stale_seed"]
    replay_source = _materialize_fixture(work / "stale" / "source", {relpath: content})
    replay_overlay = work / "stale" / "overlay"
    replay_overlay.parent.mkdir(parents=True, exist_ok=True)
    # seed overlay를 복사해 warm 상태에서 시작한다 — 두 candidate가 하나의 mutable
    # build cache를 공유하지 않도록 항상 복사본을 쓴다(CoW 미지원 플랫폼 계약).
    if replay_overlay.exists():
        shutil.rmtree(replay_overlay)
    shutil.copytree(seed_overlay, replay_overlay)

    payload = run_adapter(adapter, replay_source, replay_overlay, FIXTURE_INPUTS)
    signature = _signature(payload)
    return signature != baseline_signature, {"signature": signature, "seeded": True}


# ─────────────────────────────────────────────────────────────────────────────
# 실행과 receipt
# ─────────────────────────────────────────────────────────────────────────────


def receipt_path(cache_root, adapter_hash):
    return pathlib.Path(cache_root) / CONFORMANCE_DIRNAME / ("%s.json" % adapter_hash)


def read_receipt(cache_root, adapter):
    """기록된 conformance receipt. 없으면 None."""
    try:
        adapter_hash = adapter_identity(adapter)
    except ConformanceError:
        return None
    path = receipt_path(cache_root, adapter_hash)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def classification_of(cache_root, adapter, run_if_missing=True):
    """adapter 분류를 돌려준다. receipt가 없으면 그 자리에서 suite를 실행한다.

    추정하지 않는다 — 분류는 언제나 실제 실행 결과다.
    """
    receipt = read_receipt(cache_root, adapter)
    if receipt is None and run_if_missing:
        receipt = run_conformance(cache_root, adapter)
    if receipt is None:
        return "unknown", None
    return receipt.get("classification", "unknown"), receipt


def run_conformance(cache_root, adapter):
    """6항목을 실제 실행하고 분류 receipt를 원자 기록한다."""
    adapter_hash = adapter_identity(adapter)
    cache_root = pathlib.Path(cache_root)
    workspace = cache_root / CONFORMANCE_DIRNAME / ("work-%s" % adapter_hash[:16])
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True, exist_ok=True)

    cases = {}
    details = {}
    try:
        passed, detail, baseline_signature = _case_clean_input(adapter, workspace)
        cases["clean_input"] = "pass" if passed else "fail"
        details["clean_input"] = detail

        for case in ("source_delta", "config_delta", "dependency_delta"):
            passed, detail = _case_axis_delta(adapter, workspace, case, baseline_signature)
            cases[case] = "pass" if passed else "fail"
            details[case] = detail

        passed, detail = _case_parallel_overlay(adapter, workspace, baseline_signature)
        cases["parallel_overlay"] = "pass" if passed else "fail"
        details["parallel_overlay"] = detail

        passed, detail = _case_stale_seed(adapter, workspace, baseline_signature)
        cases["stale_seed"] = "pass" if passed else "fail"
        details["stale_seed"] = detail
    finally:
        shutil.rmtree(workspace, ignore_errors=True)

    classification = (
        "replayable"
        if all(cases.get(case) == "pass" for case in ADAPTER_CASES)
        else "non_reusable"
    )
    receipt = {
        "schema_version": "1.0",
        "adapter_path": str(pathlib.Path(adapter).resolve()),
        "adapter_hash": adapter_hash,
        "classification": classification,
        "cases": {case: cases.get(case, "fail") for case in ADAPTER_CASES},
        "details": details,
        "checked_at": _now(),
    }
    _atomic_write_json(receipt_path(cache_root, adapter_hash), receipt)
    return receipt
