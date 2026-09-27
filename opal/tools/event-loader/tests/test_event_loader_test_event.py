"""Task 162 S-8: stage.test must load and verify the TEST execution contract."""

import json
import pathlib
import subprocess


ROOT = pathlib.Path(__file__).resolve().parents[4]
RUN = pathlib.Path(__file__).resolve().parents[1] / "run.sh"
MANIFEST = ROOT / "opal/core/references/events.json"
DEPLOYED_ROOT = ROOT / "opal/core"


def cli(*args):
    result = subprocess.run(["bash", str(RUN), *map(str, args)], cwd=ROOT,
                            capture_output=True, text=True)
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = {"stdout": result.stdout, "stderr": result.stderr}
    return result, payload


def test_t162_s8_stage_test_loads_cycle_and_receipt_verifies(tmp_path):
    context = ("--manifest", MANIFEST, "--source-root", ROOT,
               "--deployed-root", DEPLOYED_ROOT, "--project-root", ROOT)
    result, loaded = cli("load", "--event", "stage.test", *context)
    assert result.returncode == 0, loaded
    assert loaded["ok"] is True
    cycle = next(doc for doc in loaded["documents"] if doc["id"] == "test-cycle")
    assert cycle["path"] == str(DEPLOYED_ROOT / "references/harness/test-cycle.md")
    assert "TEST 실행 주기" in cycle["content"]
    receipt_path = tmp_path / "stage-test-receipt.json"
    receipt_path.write_text(json.dumps(loaded["receipt"]), encoding="utf-8")
    verified_result, verified = cli("verify", "--event", "stage.test", "--receipt", receipt_path,
                                    *context)
    assert verified_result.returncode == 0, verified
    assert verified["ok"] is True
    assert "test-cycle" in {doc["id"] for doc in verified["verified_documents"]}
