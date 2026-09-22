"""
@header {
  "module": "parallel_runner",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "state-tool의 test_*.py 파일을 격리된 pytest 프로세스로 병렬 실행하고 결과를 집계한다.",
  "exports": ["discover_test_files", "run_all", "main"]
}
"""

from __future__ import annotations

import argparse
import concurrent.futures
import dataclasses
import os
import pathlib
import subprocess
import sys
import time
from collections.abc import Sequence


@dataclasses.dataclass(frozen=True)
class FileResult:
    path: pathlib.Path
    returncode: int
    output: str
    duration_seconds: float


def discover_test_files(tests_dir: pathlib.Path) -> list[pathlib.Path]:
    """Return pytest modules in a stable order; support modules are excluded by name."""
    return sorted(path for path in tests_dir.glob("test_*.py") if path.is_file())


def _run_file(path: pathlib.Path, pytest_args: Sequence[str]) -> FileResult:
    started = time.monotonic()
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(path), *pytest_args],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    return FileResult(
        path=path,
        returncode=completed.returncode,
        output=completed.stdout,
        duration_seconds=time.monotonic() - started,
    )


def run_all(
    test_files: Sequence[pathlib.Path], jobs: int, pytest_args: Sequence[str]
) -> list[FileResult]:
    """Run every file even when one fails and return results in filename order."""
    if jobs < 1:
        raise ValueError("jobs must be at least 1")
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as executor:
        futures = {
            path: executor.submit(_run_file, path, pytest_args) for path in test_files
        }
        return [futures[path].result() for path in test_files]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run state-tool pytest modules in parallel subprocesses."
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=min(4, os.cpu_count() or 1),
        help="maximum concurrent pytest processes (default: min(4, CPU count))",
    )
    parser.add_argument(
        "--tests-dir",
        type=pathlib.Path,
        default=pathlib.Path(__file__).resolve().parent,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="extra pytest arguments after --",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.jobs < 1:
        _parser().error("--jobs must be at least 1")

    tests_dir = args.tests_dir.resolve()
    test_files = discover_test_files(tests_dir)
    if not test_files:
        print(f"No test_*.py files found in {tests_dir}", file=sys.stderr)
        return 2

    pytest_args = list(args.pytest_args)
    if pytest_args[:1] == ["--"]:
        pytest_args = pytest_args[1:]

    started = time.monotonic()
    results = run_all(test_files, args.jobs, pytest_args)
    for result in results:
        status = "PASS" if result.returncode == 0 else "FAIL"
        print(f"\n===== {status} {result.path.name} ({result.duration_seconds:.2f}s) =====")
        print(result.output.rstrip())

    failed = [result for result in results if result.returncode != 0]
    elapsed = time.monotonic() - started
    print(
        f"\nParallel summary: {len(results) - len(failed)}/{len(results)} files passed "
        f"with {args.jobs} jobs in {elapsed:.2f}s"
    )
    if failed:
        print("Failed files: " + ", ".join(result.path.name for result in failed))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
