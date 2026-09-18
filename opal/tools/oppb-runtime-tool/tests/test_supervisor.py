"""
@header {
  "module": "test_supervisor",
  "layer": "test",
  "domain": "oppb-runtime",
  "description": "oppb-runtime-tool Supervisor 공개 CLI·run root 파일 계약 RED 테스트. 132 TEST-SCENARIO.md S-4(AC-11, AC-10 — 비정상 종료 후 재기동 시 살아 있는 프로세스 재부착·죽은 프로세스 결과 수확·사람 개입 없는 tick 재개, 고아 프로세스 0, 상태 손상 0)와 S-5(AC-10 — max_active_runners=2·max_active_executors=2·max_total_agent_processes=4 포화 상태에서 첫 반환 slot이 신규 Runner가 아닌 Verifier에 배정)를 검증한다. 제안서 §4.6 Supervisor 실행 모델·§9.3 동시성 예산이 근거다. PLAN H-6에 따라 내부 함수·클래스를 import하지 않고 공개 CLI(run.sh)와 run root 파일(events.jsonl·workgraph.json·attempts/<task>/<attempt>/result.json)만으로 검증한다. mock/patch 금지 — 실제 자식 프로세스를 띄우고 실제 SIGKILL로 비정상 종료를 만든다(PLAN W-10).",
  "exports": [],
  "depends": ["opal/tools/oppb-runtime-tool/run.sh", "opal/tools/opal-agent/opal_agent.py", "git CLI 2.x"]
}
"""

from __future__ import annotations

import json
import os
import pathlib
import signal
import subprocess
import time
import uuid

import pytest

TOOL_DIR = pathlib.Path(__file__).resolve().parents[1]
RUN_SH = TOOL_DIR / "run.sh"

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
DEFAULT_WAIT = 60.0


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
    """공개 인터페이스(run.sh)로만 호출한다. 내부 import 금지(PLAN H-6).
    run.sh 미존재는 W-6~W-9 구현 전 RED 증거다."""
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


def marker_command(marker: str, seconds: float, touch: pathlib.Path | None = None) -> list[str]:
    """실제 자식 프로세스를 만드는 capability 명령. `marker`가 ps 출력에 남아 고아 판정에 쓰인다."""
    tail = f" && : {marker}_DONE" if touch is None else f" && printf done > {touch}"
    return ["/bin/sh", "-c", f": {marker}; sleep {seconds}{tail}"]


def write_spec(path: pathlib.Path, budget: dict, mini_tasks: list[dict]) -> pathlib.Path:
    """`run.sh workgraph load --spec`가 소비하는 공개 fixture 계약.
    Controller Tool이 유일한 workgraph.json writer라는 §4.5 계약을 깨지 않기 위해,
    테스트는 workgraph.json을 직접 쓰지 않고 이 spec을 CLI로 주입한다."""
    path.write_text(
        json.dumps({"budget": budget, "mini_tasks": mini_tasks}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def bootstrap_run(tmp_path: pathlib.Path, budget: dict, mini_tasks: list[dict]) -> dict:
    repo = make_hub_repo(tmp_path)
    init = ok(
        run_oppb(["init", "--allocator-root", str(repo), "--project-root", str(repo)]),
        "init",
    )
    spec = write_spec(tmp_path / "spec.json", budget, mini_tasks)
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
        "run_id": init["run_id"],
        "run_root": pathlib.Path(init["run_root"]),
    }


def status(run_root: pathlib.Path) -> dict:
    return ok(run_oppb(["status", "--run-root", str(run_root)]), "status")


def wait_until(predicate, timeout: float = DEFAULT_WAIT, label: str = ""):
    """조건 성립까지 폴링한다. 실패 시 마지막 관측값을 증거로 남긴다."""
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        last = predicate()
        if last:
            return last
        time.sleep(POLL_INTERVAL)
    pytest.fail(f"{label} 대기 시간 초과({timeout}s). 마지막 관측값={last!r}")


def pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def kill_hard(pid: int) -> None:
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline and pid_alive(pid):
        time.sleep(POLL_INTERVAL)


def stray_processes(marker: str) -> list[str]:
    """marker를 포함한 잔존 프로세스 목록 — 고아 프로세스 0 판정용(실제 ps)."""
    result = subprocess.run(["ps", "-Ao", "pid=,command="], capture_output=True, text=True)
    return [
        line.strip()
        for line in result.stdout.splitlines()
        if marker in line and "ps -Ao" not in line
    ]


def read_events(run_root: pathlib.Path) -> list[dict]:
    """run root의 events.jsonl(§4.5) — 한 줄당 하나의 JSON object."""
    path = run_root / "events.jsonl"
    assert path.exists(), f"RED: events.jsonl 미생성 — {path}"
    events = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError as exc:
            pytest.fail(f"events.jsonl {i}행이 유효 JSON이 아님(상태 손상): {line!r} / {exc}")
    return events


def read_workgraph(run_root: pathlib.Path) -> dict:
    path = run_root / "workgraph.json"
    assert path.exists(), f"RED: workgraph.json 미생성 — {path}"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        pytest.fail(f"workgraph.json 파싱 실패(상태 손상 0 위반): {exc}")


def attempt_results(run_root: pathlib.Path) -> list[pathlib.Path]:
    return sorted((run_root / "attempts").glob("*/*/result.json"))


def running_attempts(snapshot: dict) -> list[dict]:
    return [a for a in snapshot.get("attempts", []) if a.get("status") == "running"]


@pytest.fixture(autouse=True)
def _reap_strays():
    """테스트가 남긴 marker 프로세스를 반드시 회수한다(테스트 자신이 고아를 만들지 않는다)."""
    marker = f"OPPB_TEST_{uuid.uuid4().hex[:12]}"
    yield marker
    for line in stray_processes(marker):
        try:
            kill_hard(int(line.split(None, 1)[0]))
        except (ValueError, IndexError):
            pass


# ================================================================= S-4 crash recovery


def test_supervisor_reattaches_live_attempt_after_sigkill(tmp_path, _reap_strays):
    """S-4 ① 실행 중 attempt가 살아 있는 상태에서 Supervisor를 SIGKILL한 뒤 재기동하면,
    같은 attempt를 새로 띄우지 않고 재부착하고 tick을 사람 개입 없이 재개한다."""
    marker = _reap_strays
    sentinel = tmp_path / "mt-long.done"
    run = bootstrap_run(
        tmp_path,
        budget={"max_active_runners": 2, "max_active_executors": 2, "max_total_agent_processes": 4},
        mini_tasks=[
            {
                "id": "mt-long",
                "capability": "cap-long",
                "lease": {"tracked_writes": ["src/long.txt"]},
                "run_command": marker_command(marker, 20, touch=sentinel),
            }
        ],
    )
    run_root = run["run_root"]

    started = ok(
        run_oppb(["start", "--run-root", str(run_root)]), "start"
    )
    supervisor_pid = int(started["supervisor_pid"])

    first = wait_until(
        lambda: (running_attempts(status(run_root)) or [None])[0],
        label="첫 attempt 기동",
    )
    attempt_id, attempt_pid = first["attempt_id"], int(first["pid"])
    assert pid_alive(attempt_pid), "fixture 전제 위반 — attempt 프로세스가 이미 죽음"

    kill_hard(supervisor_pid)
    assert not pid_alive(supervisor_pid), "Supervisor가 SIGKILL로 종료되지 않음"
    assert pid_alive(attempt_pid), (
        "fixture 전제 위반 — Supervisor와 함께 attempt까지 죽어 재부착 경로를 관찰할 수 없다"
    )

    restarted = ok(
        run_oppb(["start", "--run-root", str(run_root)]), "재기동 start"
    )
    assert int(restarted["supervisor_pid"]) != supervisor_pid, "죽은 Supervisor PID가 재보고됨"

    reattached = wait_until(
        lambda: next(
            (a for a in running_attempts(status(run_root)) if a["attempt_id"] == attempt_id),
            None,
        ),
        label="살아 있는 attempt 재부착",
    )
    assert int(reattached["pid"]) == attempt_pid, (
        f"재부착이 아니라 새 프로세스를 띄웠다: 기존 pid={attempt_pid}, 관측 pid={reattached['pid']}"
    )

    wait_until(lambda: sentinel.exists(), label="tick 자동 재개(capability 완주)")
    results = attempt_results(run_root)
    assert len(results) == 1, (
        f"attempt가 중복 실행됐다(재부착 실패). result.json={([str(p) for p in results])}"
    )
    assert not stray_processes(marker), f"고아 프로세스 잔존: {stray_processes(marker)}"


def test_supervisor_harvests_dead_attempt_and_resumes_tick(tmp_path, _reap_strays):
    """S-4 ② Supervisor가 죽어 있는 동안 attempt 프로세스도 죽으면, 재기동이 결과를 수확한 뒤
    사람 개입 없이 tick을 재개해 후속 태스크를 진행시킨다."""
    marker = _reap_strays
    downstream = tmp_path / "mt-next.done"
    run = bootstrap_run(
        tmp_path,
        budget={"max_active_runners": 2, "max_active_executors": 2, "max_total_agent_processes": 4},
        mini_tasks=[
            {
                "id": "mt-first",
                "capability": "cap-first",
                "lease": {"tracked_writes": ["src/first.txt"]},
                "run_command": marker_command(marker, 30),
            },
            {
                "id": "mt-next",
                "capability": "cap-next",
                "depends_on": ["mt-first"],
                "lease": {"tracked_writes": ["src/next.txt"]},
                "run_command": marker_command(marker, 1, touch=downstream),
            },
        ],
    )
    run_root = run["run_root"]

    started = ok(
        run_oppb(["start", "--run-root", str(run_root)]), "start"
    )
    supervisor_pid = int(started["supervisor_pid"])

    first = wait_until(
        lambda: next(
            (a for a in running_attempts(status(run_root)) if a["task_id"] == "mt-first"),
            None,
        ),
        label="mt-first attempt 기동",
    )
    attempt_id, attempt_pid = first["attempt_id"], int(first["pid"])
    revision_before = read_workgraph(run_root).get("revision")

    kill_hard(supervisor_pid)
    kill_hard(attempt_pid)
    assert not pid_alive(attempt_pid), "attempt 프로세스가 죽지 않음"

    ok(run_oppb(["resume", "--run-root", str(run_root)]), "resume")

    harvested = wait_until(
        lambda: next(
            (
                p
                for p in attempt_results(run_root)
                if attempt_id in p.parts and p.stat().st_size > 0
            ),
            None,
        ),
        label="죽은 attempt 결과 수확",
    )
    record = json.loads(harvested.read_text(encoding="utf-8"))
    assert record.get("status") != "running", (
        f"수확되지 않고 running으로 남음(상태 손상): {record}"
    )

    wait_until(lambda: downstream.exists(), label="수확 후 tick 자동 재개(후속 태스크 실행)")

    revision_after = read_workgraph(run_root).get("revision")
    assert isinstance(revision_after, int) and isinstance(revision_before, int), (
        f"workgraph.json revision이 정수가 아님: before={revision_before}, after={revision_after}"
    )
    assert revision_after > revision_before, (
        f"crash 이후 revision이 전진하지 않음: {revision_before} -> {revision_after}"
    )
    assert not stray_processes(marker), f"고아 프로세스 잔존: {stray_processes(marker)}"


def test_second_supervisor_for_same_run_is_refused(tmp_path, _reap_strays):
    """S-4 ③ 동일 run의 두 번째 Supervisor는 flock으로 거부된다(§4.6) — 이 가드가 없으면
    crash 복구 경로에서 중복 tick으로 상태가 손상된다."""
    marker = _reap_strays
    run = bootstrap_run(
        tmp_path,
        budget={"max_active_runners": 2, "max_active_executors": 2, "max_total_agent_processes": 4},
        mini_tasks=[
            {
                "id": "mt-hold",
                "capability": "cap-hold",
                "lease": {"tracked_writes": ["src/hold.txt"]},
                "run_command": marker_command(marker, 20),
            }
        ],
    )
    run_root = run["run_root"]

    started = ok(
        run_oppb(["start", "--run-root", str(run_root)]), "start"
    )
    try:
        second = run_oppb(["start", "--run-root", str(run_root)])
        assert second.returncode != 0, (
            f"살아 있는 Supervisor가 있는데 두 번째가 기동됨. stdout={second.stdout}"
        )
        combined = f"{second.stdout}\n{second.stderr}".lower()
        assert "lock" in combined, f"거부 사유에 run lock 언급 없음:\n{combined}"
    finally:
        kill_hard(int(started["supervisor_pid"]))


# =========================================================== S-5 Verifier 우선 배정


def _launch_events(events: list[dict]) -> list[dict]:
    return [e for e in events if e.get("event") == "attempt_launched"]


def _exit_events(events: list[dict]) -> list[dict]:
    return [e for e in events if e.get("event") == "attempt_exited"]


def test_verifier_wins_first_returned_slot_when_budget_saturated(tmp_path, _reap_strays):
    """S-5 max_active_runners=2·max_active_executors=2·max_total_agent_processes=4가 전부
    포화하고 candidate가 준비된 상태에서 slot 하나가 반환되면, 첫 배정은 신규 Runner가 아니라
    Verifier여야 한다(§9.3, 수용기준 10)."""
    marker = _reap_strays
    budget = {
        "max_active_runners": 2,
        "max_active_executors": 2,
        "max_total_agent_processes": 4,
    }
    mini_tasks = [
        # 포화 상태를 만드는 Runner 2 + Executor 2. 하나만 짧게 끝나 slot을 반환한다.
        {
            "id": "mt-run-a",
            "capability": "cap-a",
            "lease": {"tracked_writes": ["src/a.txt"]},
            "run_command": marker_command(marker, 3),
            "executors": [{"id": "ex-a", "run_command": marker_command(marker, 30)}],
        },
        {
            "id": "mt-run-b",
            "capability": "cap-b",
            "lease": {"tracked_writes": ["src/b.txt"]},
            "run_command": marker_command(marker, 30),
            "executors": [{"id": "ex-b", "run_command": marker_command(marker, 30)}],
        },
        # 이미 candidate가 준비되어 Verifier 배정만 기다리는 태스크.
        {
            "id": "mt-candidate",
            "capability": "cap-c",
            "pre_state": "candidate_ready",
            "lease": {"tracked_writes": ["src/c.txt"]},
            "verify_command": marker_command(marker, 2),
        },
        # slot이 반환될 때 Verifier보다 먼저 들어가면 안 되는 대기 Runner.
        {
            "id": "mt-pending",
            "capability": "cap-d",
            "lease": {"tracked_writes": ["src/d.txt"]},
            "run_command": marker_command(marker, 2),
        },
    ]
    run = bootstrap_run(tmp_path, budget=budget, mini_tasks=mini_tasks)
    run_root = run["run_root"]

    started = ok(
        run_oppb(["start", "--run-root", str(run_root)]), "start"
    )
    try:
        wait_until(
            lambda: status(run_root).get("active_agent_processes") == 4,
            label="process 상한 4 포화",
        )
        wait_until(
            lambda: any(
                a.get("task_id") == "mt-candidate" and a.get("role") == "verifier"
                for a in status(run_root).get("attempts", [])
            )
            or _exit_events(read_events(run_root)),
            label="첫 slot 반환",
        )
        wait_until(
            lambda: any(
                e.get("role") == "verifier" for e in _launch_events(read_events(run_root))
            ),
            label="Verifier 배정",
        )
    finally:
        kill_hard(int(started["supervisor_pid"]))

    events = read_events(run_root)
    exits = _exit_events(events)
    assert exits, "RED: attempt_exited 이벤트 0건 — slot 반환을 관찰할 수 없다"
    first_exit_index = events.index(exits[0])

    after = [
        e for e in events[first_exit_index + 1 :] if e.get("event") == "attempt_launched"
    ]
    assert after, "slot 반환 이후 배정 이벤트 0건 — 검증이 굶었다"
    assert after[0].get("role") == "verifier", (
        "첫 반환 slot이 Verifier가 아닌 "
        f"{after[0].get('role')!r}(task={after[0].get('task_id')!r})에 배정됨 — 수용기준 10 위반"
    )
    assert after[0].get("task_id") == "mt-candidate", (
        f"준비된 candidate가 아닌 다른 대상에 배정됨: {after[0]}"
    )


def test_concurrency_caps_are_never_exceeded(tmp_path, _reap_strays):
    """S-5 보조 — events.jsonl의 launch/exit 순서를 재생해 어느 시점에도
    runner 2·executor 2·전체 agent process 4를 넘지 않았음을 확인한다(§9.3)."""
    marker = _reap_strays
    budget = {
        "max_active_runners": 2,
        "max_active_executors": 2,
        "max_total_agent_processes": 4,
    }
    mini_tasks = [
        {
            "id": f"mt-{i}",
            "capability": f"cap-{i}",
            "lease": {"tracked_writes": [f"src/{i}.txt"]},
            "run_command": marker_command(marker, 2),
        }
        for i in range(6)
    ]
    run = bootstrap_run(tmp_path, budget=budget, mini_tasks=mini_tasks)
    run_root = run["run_root"]

    started = ok(
        run_oppb(["start", "--run-root", str(run_root)]), "start"
    )
    try:
        wait_until(
            lambda: len(_exit_events(read_events(run_root))) >= 6,
            timeout=120,
            label="전체 미니 태스크 완주",
        )
    finally:
        kill_hard(int(started["supervisor_pid"]))

    live: dict[str, str] = {}
    peak = {"runner": 0, "executor": 0, "total": 0}
    for event in read_events(run_root):
        name = event.get("event")
        if name == "attempt_launched":
            live[event["attempt_id"]] = event.get("role", "runner")
        elif name == "attempt_exited":
            live.pop(event.get("attempt_id"), None)
        else:
            continue
        roles = list(live.values())
        peak["runner"] = max(peak["runner"], roles.count("runner"))
        peak["executor"] = max(peak["executor"], roles.count("executor"))
        peak["total"] = max(peak["total"], len(roles))

    assert peak["runner"] <= 2, f"max_active_runners 초과: {peak}"
    assert peak["executor"] <= 2, f"max_active_executors 초과: {peak}"
    assert peak["total"] <= 4, f"max_total_agent_processes 초과: {peak}"
    assert not stray_processes(marker), f"고아 프로세스 잔존: {stray_processes(marker)}"
