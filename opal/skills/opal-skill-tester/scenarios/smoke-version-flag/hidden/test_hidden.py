"""
@header {
  "module": "test_hidden_smoke_version_flag",
  "layer": "test",
  "domain": "opal-skill-tester",
  "description": "smoke-version-flag 시나리오 숨은 인수 테스트. SUT_REPO 작업본의 stockctl --version 출력·종료 코드·저장소 무접촉과 기존 테스트 통과를 검증한다.",
  "exports": []
}
"""
import os, pathlib, subprocess, sys
REPO = pathlib.Path(os.environ["SUT_REPO"])
def test_version_output(tmp_path):
    r = subprocess.run([sys.executable, "-m", "stockctl", "--version"], capture_output=True, text=True, cwd=REPO,
                       env={**os.environ, "STOCKCTL_STORE": str(tmp_path / "s.json")})
    assert r.returncode == 0 and r.stdout.strip() == "stockctl 0.1.0"
    assert not (tmp_path / "s.json").exists()
def test_existing_tests_pass():
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests"], cwd=REPO, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-400:]
