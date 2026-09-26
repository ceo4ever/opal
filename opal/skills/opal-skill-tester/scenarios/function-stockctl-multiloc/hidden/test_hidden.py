"""
@header {
  "module": "test_hidden_function_stockctl_multiloc",
  "layer": "test",
  "domain": "opal-skill-tester",
  "description": "function-stockctl-multiloc 시나리오 숨은 인수 테스트 17건. SUT_REPO 작업본의 다중 위치 구조·이관·transfer·감사 로그·history·import-csv·version 충돌 감지와 기존 테스트·표준 라이브러리 제약을 CLI로 검증한다.",
  "exports": []
}
"""
import json, os, subprocess, sys, pathlib, pytest
REPO = pathlib.Path(os.environ["SUT_REPO"])
def run(store, *a):
    return subprocess.run([sys.executable, "-m", "stockctl", "--store", str(store), *map(str, a)],
                          capture_output=True, text=True, cwd=REPO)
@pytest.fixture
def st(tmp_path): return tmp_path / "s.json"
def audit(st): p = pathlib.Path(str(st) + ".audit.jsonl"); return [json.loads(l) for l in p.read_text().splitlines()] if p.exists() else []
def test_h01_add_list_multi_location(st):
    run(st, "add", "A1", "--qty", 5, "--name", "Apple"); run(st, "add", "A1", "--qty", 3, "--location", "B2")
    assert run(st, "list").stdout.splitlines() == ["A1\tApple\tB2\t3", "A1\tApple\tMAIN\t5"]
def test_h02_legacy_migration(st):
    st.write_text(json.dumps({"items": {"X": {"name": "Old", "qty": 7, "location": "W1"}}}))
    assert run(st, "list").stdout.strip() == "X\tOld\tW1\t7"
    assert run(st, "add", "X", "--qty", 1, "--location", "W1").returncode == 0
    d = json.loads(st.read_text()); assert d["items"]["X"]["locations"] == {"W1": 8} and d["version"] == 1
def test_h03_transfer_ok(st):
    run(st, "add", "A1", "--qty", 5); r = run(st, "transfer", "A1", "--from", "MAIN", "--to", "B2", "--qty", 2)
    assert r.returncode == 0 and r.stdout.strip() == "A1 MAIN->B2 2"
    assert "A1\tA1\tB2\t2" in run(st, "list").stdout
def test_h04_transfer_insufficient_no_change(st):
    run(st, "add", "A1", "--qty", 1); before = st.read_bytes()
    r = run(st, "transfer", "A1", "--from", "MAIN", "--to", "B2", "--qty", 5)
    assert r.returncode == 2 and r.stderr.startswith("insufficient:") and st.read_bytes() == before
def test_h05_transfer_invalid(st):
    run(st, "add", "A1", "--qty", 1)
    assert run(st, "transfer", "A1", "--from", "MAIN", "--to", "MAIN", "--qty", 1).returncode == 5
    r = run(st, "transfer", "A1", "--from", "MAIN", "--to", "B", "--qty", 0); assert r.returncode == 5 and r.stderr.startswith("invalid:")
def test_h06_transfer_unknown(st):
    assert run(st, "transfer", "ZZ", "--from", "MAIN", "--to", "B", "--qty", 1).returncode == 1
def test_h07_remove_location(st):
    run(st, "add", "A1", "--qty", 4, "--location", "B2")
    assert run(st, "remove", "A1", "--qty", 1).returncode == 2
    assert run(st, "remove", "A1", "--qty", 1, "--location", "B2").returncode == 0
def test_h08_audit_lines(st):
    run(st, "add", "A1", "--qty", 5); run(st, "transfer", "A1", "--from", "MAIN", "--to", "B2", "--qty", 2)
    run(st, "transfer", "A1", "--from", "MAIN", "--to", "B2", "--qty", 99)
    a = audit(st); assert [x["op"] for x in a] == ["add", "transfer"]
    assert a[1]["changes"] == {"MAIN": -2, "B2": 2} and a[1]["sku"] == "A1" and "ts" in a[1]
def test_h09_history_order_format(st):
    run(st, "add", "A1", "--qty", 5); run(st, "remove", "A1", "--qty", 1)
    lines = run(st, "history", "A1").stdout.splitlines()
    assert len(lines) == 2 and lines[0].split("\t")[1] == "remove" and lines[0].split("\t")[2] == "MAIN:-1"
    assert lines[1].split("\t")[2] == "MAIN:+5"
def test_h10_history_empty(st):
    r = run(st, "history", "NONE"); assert r.returncode == 0 and r.stdout == ""
def test_h11_import_all_valid(st, tmp_path):
    f = tmp_path / "in.csv"; f.write_text("sku,name,location,qty\nA1,Apple,MAIN,3\nB1,Ball,W2,4\n")
    r = run(st, "import-csv", f); assert r.returncode == 0 and r.stdout.strip() == "applied 2, rejected 0"
    assert not pathlib.Path(str(f) + ".rejected.csv").exists()
    assert json.loads(st.read_text())["version"] == 1
def test_h12_import_partial(st, tmp_path):
    f = tmp_path / "in.csv"; f.write_text("sku,name,location,qty\nA1,Apple,MAIN,3\nB1,Ball,W2,-1\nC1,,W2,2\nD1,Dog,W3,x\n")
    r = run(st, "import-csv", f); assert r.returncode == 3 and r.stdout.strip() == "applied 1, rejected 3"
    rej = pathlib.Path(str(f) + ".rejected.csv").read_text().splitlines()
    assert rej[0].split(",")[-1] == "reason" and len(rej) == 4
    assert [x["op"] for x in audit(st)] == ["import"]
def test_h13_version_increments(st):
    run(st, "add", "A1", "--qty", 1); run(st, "add", "A1", "--qty", 1)
    assert run(st, "version").stdout.strip() == "2"
def test_h14_expect_version_conflict(st):
    run(st, "add", "A1", "--qty", 1); before = st.read_bytes()
    r = run(st, "add", "A1", "--qty", 1, "--expect-version", 0)
    assert r.returncode == 4 and r.stderr.strip() == "conflict: expected 0, found 1" and st.read_bytes() == before
    assert run(st, "transfer", "A1", "--from", "MAIN", "--to", "B", "--qty", 1, "--expect-version", 1).returncode == 0
def test_h15_failed_command_no_audit(st):
    run(st, "add", "A1", "--qty", 1); run(st, "remove", "A1", "--qty", 9); run(st, "add", "A1", "--qty", 1, "--expect-version", 7)
    assert len(audit(st)) == 1
def test_h16_existing_tests_pass():
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests"], cwd=REPO, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-500:]
def test_h17_stdlib_only():
    import re
    bad = []
    for p in (REPO / "stockctl").glob("*.py"):
        for m in re.finditer(r"^\s*(?:import|from)\s+([a-zA-Z_][\w]*)", p.read_text(), re.M):
            if m.group(1) not in sys.stdlib_module_names and m.group(1) not in ("stockctl",): bad.append((p.name, m.group(1)))
    assert not bad, bad
