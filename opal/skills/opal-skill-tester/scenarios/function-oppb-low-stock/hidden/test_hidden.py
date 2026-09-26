"""
@header {
  "module": "test_hidden_function_oppb_low_stock",
  "layer": "test",
  "domain": "opal-skill-tester",
  "description": "function-oppb-low-stock 시나리오의 low-stock 출력·정렬·빈 결과·잘못된 인자·저장소 무변경·기존 회귀를 공개 CLI로 검증한다.",
  "exports": []
}
"""
import os
import pathlib
import subprocess
import sys


REPO = pathlib.Path(os.environ["SUT_REPO"])


def run(store, *args):
    return subprocess.run(
        [sys.executable, "-m", "stockctl", "--store", str(store), *map(str, args)],
        capture_output=True,
        text=True,
        cwd=REPO,
    )


def test_low_stock_lists_sorted_without_changing_store(tmp_path):
    store = tmp_path / "stock.json"
    run(store, "add", "B1", "--qty", 1)
    run(store, "add", "A1", "--qty", 2)
    run(store, "add", "C1", "--qty", 9)
    before = store.read_bytes()

    result = run(store, "low-stock", "--below", 5)

    assert result.returncode == 0
    assert result.stdout.splitlines() == ["A1\t2", "B1\t1"]
    assert store.read_bytes() == before


def test_low_stock_empty_result(tmp_path):
    store = tmp_path / "stock.json"
    run(store, "add", "A1", "--qty", 9)

    result = run(store, "low-stock", "--below", 5)

    assert result.returncode == 0
    assert result.stdout == ""


def test_low_stock_rejects_non_positive_threshold(tmp_path):
    store = tmp_path / "stock.json"
    result = run(store, "low-stock", "--below", 0)

    assert result.returncode == 5
    assert result.stderr.startswith("invalid:")


def test_existing_tests_pass():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout[-400:]
