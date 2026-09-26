"""
@header {
  "module": "test_basic",
  "layer": "test",
  "domain": "inventory",
  "description": "add/remove/list 기존 동작 회귀 테스트.",
  "exports": []
}
"""
import subprocess
import sys


def run(tmp_path, *args):
    return subprocess.run([sys.executable, "-m", "stockctl", "--store", str(tmp_path / "s.json"), *args],
                          capture_output=True, text=True)


def test_add_and_list(tmp_path):
    assert run(tmp_path, "add", "A1", "--qty", "5", "--name", "Apple").returncode == 0
    out = run(tmp_path, "list").stdout
    assert "A1\tApple\tMAIN\t5" in out


def test_remove_insufficient(tmp_path):
    run(tmp_path, "add", "A1", "--qty", "2")
    r = run(tmp_path, "remove", "A1", "--qty", "3")
    assert r.returncode == 2
