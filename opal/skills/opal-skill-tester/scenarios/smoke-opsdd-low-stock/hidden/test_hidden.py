"""
@header {
  "module": "test_hidden_smoke_opsdd_low_stock",
  "layer": "test",
  "domain": "opal-skill-tester",
  "description": "smoke-opsdd-low-stock 시나리오 숨은 인수 테스트. SUT_REPO 작업본의 stockctl low-stock 출력·정렬·빈 결과·잘못된 인자·저장소 무변경과 기존 테스트 통과를 검증한다.",
  "exports": []
}
"""
import os, pathlib, subprocess, sys
REPO = pathlib.Path(os.environ["SUT_REPO"])
def run(st, *a):
    return subprocess.run([sys.executable, "-m", "stockctl", "--store", str(st), *map(str, a)], capture_output=True, text=True, cwd=REPO)
def test_low_stock_lists_sorted(tmp_path):
    st = tmp_path / "s.json"
    run(st, "add", "B1", "--qty", 1); run(st, "add", "A1", "--qty", 2); run(st, "add", "C1", "--qty", 9)
    before = st.read_bytes()
    r = run(st, "low-stock", "--below", 5)
    assert r.returncode == 0 and r.stdout.splitlines() == ["A1\t2", "B1\t1"] and st.read_bytes() == before
def test_low_stock_empty_and_invalid(tmp_path):
    st = tmp_path / "s.json"
    run(st, "add", "A1", "--qty", 9)
    r = run(st, "low-stock", "--below", 5); assert r.returncode == 0 and r.stdout == ""
    r = run(st, "low-stock", "--below", 0); assert r.returncode == 5 and r.stderr.startswith("invalid:")
def test_existing_tests_pass():
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests"], cwd=REPO, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-400:]
