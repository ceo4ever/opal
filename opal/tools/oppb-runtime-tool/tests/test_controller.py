"""
@header {
  "module": "test_controller",
  "layer": "test",
  "domain": "oppb-runtime",
  "description": "OPPB Controller와 Product Flow의 상태 소유권 경계 RED 테스트. 132 TEST-SCENARIO.md S-8(AC-1, C-6 — 한 run 전체를 진행시키며 state.json과 workgraph.json의 writer를 추적해, state.json은 P0~P5 전이만·workgraph.json은 미니 태스크 상태만 변경하고 상호 직접 쓰기 0)을 검증한다. 제안서 §4.5 산출물 소유권 표와 §9.2 프로젝트 상태기계, 수용기준 25가 근거다. PLAN H-6에 따라 내부 함수·클래스를 import하지 않고 공개 CLI(oppb-runtime-tool run.sh, state-tool)와 파일 계약(state.json·workgraph.json·acceptance.json·execution-packet.json·result.json)의 content hash 불변식으로만 검증한다. mock/patch 금지 — 실제 git 저장소·실제 프로세스·실제 파일만 사용한다(PLAN W-10).",
  "exports": [],
  "depends": ["opal/tools/oppb-runtime-tool/run.sh", "opal/tools/state-tool/state_tool.py"]
}
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import signal
import subprocess
import sys
import time
import uuid

import pytest

TOOL_DIR = pathlib.Path(__file__).resolve().parents[1]
RUN_SH = TOOL_DIR / "run.sh"
OPAL_DIR = TOOL_DIR.parents[1]  # .../opal (skills/, core/, tools/ 보유)
STATE_TOOL_PATH = OPAL_DIR / "tools" / "state-tool" / "state_tool.py"
PROJECT_STAGES = ["P0", "P1", "P2", "P3", "P4", "P5"]

# S-8 fixture는 OPPB pipeline.json(W-20, P9)에 선행 의존하지 않는다. state-tool의
# `--rows-spec` 인라인 경로로 P0~P5 최소 행 집합만 주입한다 — S-8의 검증 의도는
# state.json↔workgraph.json 상호 직접 쓰기 0이며 rows의 출처와 무관하다.
# `--skill oppb` enum 의존(W-3, P2)은 의도적으로 남긴다.
MINIMAL_PROJECT_ROWS = [
    {"stage": stage, "item": f"{stage} 프로젝트 단계", "owner_default": "PM"}
    for stage in PROJECT_STAGES
]
STAGE_TOKEN = re.compile(r"\bP[0-5]\b")

GIT_AUTHOR_ARGS = [
    "-c",
    "user.email=test@opal.local",
    "-c",
    "user.name=OPAL Test",
    "-c",
    "commit.gpgsign=false",
    "-c",
    "init.defaultBranch=main",
]

POLL_INTERVAL = 0.2
DEFAULT_WAIT = 90.0


# --------------------------------------------------------------------- 헬퍼


def run_git(args: list[str], cwd: pathlib.Path, check: bool = True) -> subprocess.CompletedProcess:
    cmd = ["git", *GIT_AUTHOR_ARGS, *args]
    result = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(
            f"git fixture 구성 실패: {' '.join(cmd)}\ncwd={cwd}\n"
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )
    return result


def make_hub_repo(base: pathlib.Path, name: str = "hub") -> pathlib.Path:
    repo = base / name
    repo.mkdir(parents=True)
    run_git(["init", "-b", "main", "."], cwd=repo)
    (repo / "README.md").write_text("# hub\n", encoding="utf-8")
    run_git(["add", "README.md"], cwd=repo)
    run_git(["commit", "-m", "init"], cwd=repo)
    return repo


def run_oppb(args: list[str], cwd: pathlib.Path | None = None, timeout: int = 180):
    """공개 인터페이스(run.sh)로만 호출한다(PLAN H-6). 미존재는 RED 증거."""
    if not RUN_SH.exists():
        pytest.fail(
            "RED: opal/tools/oppb-runtime-tool/run.sh 미존재 — W-6~W-9 구현 전 정상 실패. "
            f"요청 명령: run.sh {' '.join(args)}"
        )
    return subprocess.run(
        ["bash", str(RUN_SH), *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def run_state(args: list[str]) -> subprocess.CompletedProcess:
    """state-tool 공개 CLI. run.sh(venv 위임)를 거치지 않고 스크립트를 직접 호출한다."""
    return subprocess.run(
        [sys.executable, str(STATE_TOOL_PATH), *args], capture_output=True, text=True
    )


def parse_json_stdout(result: subprocess.CompletedProcess, label: str = "") -> dict:
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        pytest.fail(
            f"{label} stdout이 유효 JSON이 아님. exit={result.returncode}\n"
            f"stdout={result.stdout!r}\nstderr={result.stderr!r}\n원인: {exc}"
        )


def ok(result: subprocess.CompletedProcess, label: str) -> dict:
    assert result.returncode == 0, (
        f"{label} 실패: exit={result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
    )
    return parse_json_stdout(result, label)


def sha256_of(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wait_until(predicate, timeout: float = DEFAULT_WAIT, label: str = ""):
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        last = predicate()
        if last:
            return last
        time.sleep(POLL_INTERVAL)
    pytest.fail(f"{label} 대기 시간 초과({timeout}s). 마지막 관측값={last!r}")


def kill_hard(pid: int) -> None:
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        return


def marker_command(marker: str, seconds: float, touch: pathlib.Path | None = None) -> list[str]:
    tail = "" if touch is None else f" && printf done > {touch}"
    return ["/bin/sh", "-c", f": {marker}; sleep {seconds}{tail}"]


def make_project_capsule(repo: pathlib.Path, folder: str = "900-oppb-fixture") -> pathlib.Path:
    """프로젝트 태스크 캡슐을 state-tool 공개 CLI로만 만든다.
    `--skill oppb`(W-3 enum 확장)와 P0~P5 stage enum이 없으면 여기서 RED가 난다."""
    capsule = repo / "tasks" / folder
    capsule.mkdir(parents=True)
    result = run_state(
        [
            "init",
            str(capsule),
            "--skill",
            "oppb",
            "--mode",
            "agentic",
            "--task-title",
            "OPPB controller boundary fixture",
            "--rows-spec",
            json.dumps(MINIMAL_PROJECT_ROWS, ensure_ascii=False),
        ]
    )
    assert result.returncode == 0, (
        f"RED: state-tool init --skill oppb 실패 — W-3 enum 확장 전 정상 실패. "
        f"exit={result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
    )
    assert (capsule / "state.json").exists(), f"state.json 미생성: {capsule}"
    return capsule


def bootstrap_run(tmp_path: pathlib.Path, mini_tasks: list[dict]) -> dict:
    repo = make_hub_repo(tmp_path)
    capsule = make_project_capsule(repo)
    init = ok(
        run_oppb(
            ["init", "--allocator-root", str(repo), "--project-root", str(capsule)]
        ),
        "init",
    )
    spec = tmp_path / "spec.json"
    spec.write_text(
        json.dumps(
            {
                "budget": {
                    "max_active_runners": 2,
                    "max_active_executors": 2,
                    "max_total_agent_processes": 4,
                },
                "mini_tasks": mini_tasks,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    ok(
        run_oppb(
            [
                "workgraph",
                "load",
                "--run-root",
                init["run_root"],
                "--spec",
                str(spec),
            ]
        ),
        "workgraph load",
    )
    return {
        "repo": repo,
        "capsule": capsule,
        "run_id": init["run_id"],
        "run_root": pathlib.Path(init["run_root"]),
    }


def status(run_root: pathlib.Path) -> dict:
    return ok(run_oppb(["status", "--run-root", str(run_root)]), "status")


def read_json(path: pathlib.Path, label: str) -> dict:
    assert path.exists(), f"RED: {label} 미생성 — {path}"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        pytest.fail(f"{label} 파싱 실패(상태 손상): {exc}")


def sample_tasks(marker: str, sentinel: pathlib.Path) -> list[dict]:
    return [
        {
            "id": "mt-alpha",
            "capability": "cap-alpha",
            "lease": {"tracked_writes": ["src/alpha.txt"]},
            "run_command": marker_command(marker, 1),
            "verify_command": marker_command(marker, 1),
        },
        {
            "id": "mt-beta",
            "capability": "cap-beta",
            "depends_on": ["mt-alpha"],
            "lease": {"tracked_writes": ["src/beta.txt"]},
            "run_command": marker_command(marker, 1, touch=sentinel),
            "verify_command": marker_command(marker, 1),
        },
    ]


@pytest.fixture
def marker() -> str:
    return f"OPPB_TEST_{uuid.uuid4().hex[:12]}"


# ============================================================ S-8 상호 직접 쓰기 0


def test_controller_never_writes_project_state_json(tmp_path, marker):
    """S-8 ① run 전체를 진행시키는 동안 Controller는 state.json을 한 번도 쓰지 않는다 —
    workgraph.json은 전진하지만 state.json content hash와 mtime은 불변이다."""
    sentinel = tmp_path / "beta.done"
    run = bootstrap_run(tmp_path, sample_tasks(marker, sentinel))
    run_root, capsule = run["run_root"], run["capsule"]

    state_path = capsule / "state.json"
    state_hash_before = sha256_of(state_path)
    state_mtime_before = state_path.stat().st_mtime_ns
    workgraph_path = run_root / "workgraph.json"
    revision_before = read_json(workgraph_path, "workgraph.json").get("revision")

    started = ok(
        run_oppb(["start", "--run-root", str(run_root)]), "start"
    )
    try:
        wait_until(lambda: sentinel.exists(), label="run 전체 진행")
        wait_until(
            lambda: read_json(workgraph_path, "workgraph.json").get("revision")
            != revision_before,
            label="workgraph revision 전진",
        )
    finally:
        kill_hard(int(started["supervisor_pid"]))

    assert sha256_of(state_path) == state_hash_before, (
        "Controller가 state.json을 직접 썼다(수용기준 25 위반) — "
        f"before={state_hash_before}, after={sha256_of(state_path)}"
    )
    assert state_path.stat().st_mtime_ns == state_mtime_before, (
        "state.json이 재기록됐다(내용이 같아도 writer 경계 위반)"
    )


def test_product_flow_state_transition_never_writes_workgraph(tmp_path, marker):
    """S-8 ② P0~P5 전이(state-tool 경유 Product Flow 경로)는 workgraph.json을 건드리지 않는다."""
    sentinel = tmp_path / "beta.done"
    run = bootstrap_run(tmp_path, sample_tasks(marker, sentinel))
    capsule, run_root = run["capsule"], run["run_root"]

    workgraph_path = run_root / "workgraph.json"
    workgraph_hash_before = sha256_of(workgraph_path)
    workgraph_mtime_before = workgraph_path.stat().st_mtime_ns

    advance = run_state(["advance", str(capsule)])
    assert advance.returncode == 0, (
        f"RED: state-tool advance 실패 — W-3 oppb 전이 지원 전 정상 실패. "
        f"exit={advance.returncode}\nstdout={advance.stdout}\nstderr={advance.stderr}"
    )

    assert sha256_of(workgraph_path) == workgraph_hash_before, (
        "Product Flow의 P 전이가 workgraph.json을 직접 썼다(수용기준 25 위반)"
    )
    assert workgraph_path.stat().st_mtime_ns == workgraph_mtime_before, (
        "P 전이가 workgraph.json을 재기록했다"
    )


def test_state_json_records_only_project_stage_transitions(tmp_path, marker):
    """S-8 ③ state.json에는 P0~P5 전이만 있고 미니 태스크 식별자가 전혀 등장하지 않는다."""
    sentinel = tmp_path / "beta.done"
    run = bootstrap_run(tmp_path, sample_tasks(marker, sentinel))
    run_root, capsule = run["run_root"], run["capsule"]

    started = ok(
        run_oppb(["start", "--run-root", str(run_root)]), "start"
    )
    try:
        wait_until(lambda: sentinel.exists(), label="run 전체 진행")
    finally:
        kill_hard(int(started["supervisor_pid"]))

    raw = (capsule / "state.json").read_text(encoding="utf-8")
    for task_id in ("mt-alpha", "mt-beta"):
        assert task_id not in raw, (
            f"state.json에 미니 태스크 식별자 {task_id!r}가 기록됨 — 소유권 경계 위반(§4.5)"
        )
    for noise in ("attempt_id", "candidate", "lease", "workgraph"):
        assert noise not in raw, f"state.json에 P3 내부 개념 {noise!r}가 누출됨"

    stages = set(STAGE_TOKEN.findall(raw))
    assert stages, "state.json에 P0~P5 단계 토큰이 없음 — 프로젝트 파이프라인 미생성"
    assert stages <= set(PROJECT_STAGES), f"state.json에 P0~P5 밖 단계 토큰: {stages}"


def test_workgraph_records_only_mini_task_state(tmp_path, marker):
    """S-8 ④ workgraph.json에는 미니 태스크 상태만 있고 P0~P5 프로젝트 단계가 없다."""
    sentinel = tmp_path / "beta.done"
    run = bootstrap_run(tmp_path, sample_tasks(marker, sentinel))
    run_root = run["run_root"]

    started = ok(
        run_oppb(["start", "--run-root", str(run_root)]), "start"
    )
    try:
        wait_until(lambda: sentinel.exists(), label="run 전체 진행")
    finally:
        kill_hard(int(started["supervisor_pid"]))

    raw = (run_root / "workgraph.json").read_text(encoding="utf-8")
    leaked = set(STAGE_TOKEN.findall(raw))
    assert not leaked, f"workgraph.json에 프로젝트 단계 토큰 누출: {leaked}"
    for noise in ("task_steps", "pm_gate", "STATE.md"):
        assert noise not in raw, f"workgraph.json에 state.json 소유 개념 {noise!r}가 누출됨"

    graph = read_json(run_root / "workgraph.json", "workgraph.json")
    ids = {t.get("id") for t in graph.get("mini_tasks", [])}
    assert ids == {"mt-alpha", "mt-beta"}, f"미니 태스크 집합 불일치: {ids}"


def test_run_root_owns_operational_artifacts_and_capsule_owns_user_artifacts(tmp_path, marker):
    """S-8 ⑤ §4.5 산출물 소유권 — 운영 자료(workgraph·acceptance·packet·result)는 run root에만
    있고 추적 캡슐에는 새지 않는다."""
    sentinel = tmp_path / "beta.done"
    run = bootstrap_run(tmp_path, sample_tasks(marker, sentinel))
    repo, run_root, capsule = run["repo"], run["run_root"], run["capsule"]

    started = ok(
        run_oppb(["start", "--run-root", str(run_root)]), "start"
    )
    try:
        wait_until(lambda: sentinel.exists(), label="run 전체 진행")
        wait_until(
            lambda: list((run_root / "attempts").glob("*/*/result.json")),
            label="attempt result.json 생성",
        )
    finally:
        kill_hard(int(started["supervisor_pid"]))

    for name in ("workgraph.json", "acceptance.json"):
        assert (run_root / name).exists(), f"RED: run root에 {name} 미생성"
        assert not (capsule / name).exists(), f"{name}이 추적 캡슐로 새어 나감(§4.5 위반)"

    packets = list((run_root / "attempts").glob("*/*/execution-packet.json"))
    results = list((run_root / "attempts").glob("*/*/result.json"))
    assert packets, "RED: execution-packet.json 미생성"
    assert results, "RED: result.json 미생성"

    tracked = run_git(["status", "--porcelain"], cwd=repo).stdout
    assert ".opal-runs" not in tracked, (
        f"run root가 Git 추적 상태에 노출됨 — 미추적 계약 위반:\n{tracked}"
    )
