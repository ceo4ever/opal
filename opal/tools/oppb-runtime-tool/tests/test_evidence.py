"""
@header {
  "module": "test_evidence",
  "layer": "test",
  "domain": "oppb-runtime",
  "description": "OPPB Evidence Tool 공개 CLI·run root 파일 계약 RED 테스트. 132 TEST-SCENARIO.md S-9(AC-9 — schema 불일치·code head 불일치·scope hash 불일치 evidence 3종은 색인 전에 거부되고 정상 1종만 불변 색인되며, 독립 검증 증거가 없는 미니 태스크의 accepted 전이가 차단된다)를 검증한다. 제안서 §4.5 evidence/<scope>/<evidence-id>.json 소유권과 수용기준 9·28이 근거다. PLAN H-6에 따라 내부 함수·클래스를 import하지 않고 공개 CLI(run.sh evidence/task)와 run root 파일 계약만으로 검증한다. mock/patch 금지 — 실제 git 저장소와 실제 파일만 사용한다(PLAN W-10).",
  "exports": [],
  "depends": ["opal/tools/oppb-runtime-tool/run.sh", "git CLI 2.x"]
}
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import uuid

import pytest

TOOL_DIR = pathlib.Path(__file__).resolve().parents[1]
RUN_SH = TOOL_DIR / "run.sh"

ZERO_SHA = "0" * 40

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


def run_oppb(args: list[str], cwd: pathlib.Path | None = None, timeout: int = 120):
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


def read_json(path: pathlib.Path, label: str) -> dict:
    assert path.exists(), f"RED: {label} 미생성 — {path}"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        pytest.fail(f"{label} 파싱 실패: {exc}")


MINI_TASKS = [
    {
        "id": "mt-verified",
        "capability": "cap-verified",
        "pre_state": "candidate_ready",
        "lease": {"tracked_writes": ["src/verified.txt"]},
    },
    {
        "id": "mt-unverified",
        "capability": "cap-unverified",
        "pre_state": "candidate_ready",
        "lease": {"tracked_writes": ["src/unverified.txt"]},
    },
]


@pytest.fixture
def run_fixture(tmp_path):
    """허브 저장소 + init + workgraph load까지 공개 CLI로만 구성한 run fixture."""
    repo = make_hub_repo(tmp_path)
    init = ok(
        run_oppb(["init", "--allocator-root", str(repo), "--project-root", str(repo)]),
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
                "mini_tasks": MINI_TASKS,
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
    run_root = pathlib.Path(init["run_root"])
    graph = read_json(run_root / "workgraph.json", "workgraph.json")
    tasks = {t.get("id"): t for t in graph.get("mini_tasks", [])}
    assert set(tasks) == {"mt-verified", "mt-unverified"}, (
        f"workgraph 미니 태스크 집합 불일치: {list(tasks)}"
    )
    return {
        "repo": repo,
        "run_id": init["run_id"],
        "run_root": run_root,
        "tasks": tasks,
        "code_head": run_git(["rev-parse", "HEAD"], cwd=repo).stdout.strip(),
    }


def valid_evidence(run_fixture, task_id: str = "mt-verified", evidence_id: str = "ev-ok") -> dict:
    """현재 code head와 workgraph가 공표한 scope hash에 일치하는 정상 evidence."""
    task = run_fixture["tasks"][task_id]
    scope_hash = task.get("scope_hash")
    assert scope_hash, f"RED: workgraph.json이 {task_id}의 scope_hash를 공표하지 않음: {task}"
    return {
        "schema_version": 1,
        "evidence_id": evidence_id,
        "scope": task_id,
        "code_head": run_fixture["code_head"],
        "scope_hash": scope_hash,
        "verifier": {"kind": "integration", "attempt_id": f"verify-{uuid.uuid4().hex[:8]}"},
        "result": "pass",
        "commands": [["/bin/sh", "-c", "true"]],
    }


def submit(run_fixture, document: dict, name: str) -> subprocess.CompletedProcess:
    path = run_fixture["run_root"].parent / f"{name}.json"
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    return run_oppb(
        [
            "evidence",
            "submit",
            "--run-root",
            str(run_fixture["run_root"]),
            "--file",
            str(path),
        ]
    )


def indexed_files(run_fixture) -> list[pathlib.Path]:
    """색인된 evidence 실제 파일 목록 — `evidence/<scope>/<evidence-id>.json`(§4.5)."""
    root = run_fixture["run_root"] / "evidence"
    if not root.exists():
        return []
    return sorted(p for p in root.rglob("*") if p.is_file())


def accept(run_fixture, task_id: str) -> subprocess.CompletedProcess:
    return run_oppb(
        [
            "task",
            "accept",
            "--run-root",
            str(run_fixture["run_root"]),
            "--task-id",
            task_id,
        ]
    )


def task_state(run_fixture, task_id: str) -> str | None:
    graph = read_json(run_fixture["run_root"] / "workgraph.json", "workgraph.json")
    for task in graph.get("mini_tasks", []):
        if task.get("id") == task_id:
            return task.get("state")
    pytest.fail(f"workgraph.json에 {task_id} 없음")


# ============================================== S-9 ① 불일치 3종은 색인 전에 거부


def _schema_mismatch(run_fixture) -> dict:
    document = valid_evidence(run_fixture, evidence_id="ev-schema")
    document.pop("scope_hash")          # 필수 필드 누락
    document["result"] = 12345          # 타입 불일치
    return document


def _code_head_mismatch(run_fixture) -> dict:
    document = valid_evidence(run_fixture, evidence_id="ev-head")
    document["code_head"] = ZERO_SHA
    return document


def _scope_hash_mismatch(run_fixture) -> dict:
    document = valid_evidence(run_fixture, evidence_id="ev-scope")
    document["scope_hash"] = "deadbeef" * 8
    return document


@pytest.mark.parametrize(
    "builder,reason_token",
    [
        (_schema_mismatch, "schema"),
        (_code_head_mismatch, "code_head"),
        (_scope_hash_mismatch, "scope_hash"),
    ],
    ids=["schema_mismatch", "code_head_mismatch", "scope_hash_mismatch"],
)
def test_mismatched_evidence_is_rejected_before_indexing(run_fixture, builder, reason_token):
    """S-9 ① 불일치 evidence는 거부되고, 거부 시점에 색인 파일이 단 하나도 만들어지지 않는다."""
    before = indexed_files(run_fixture)

    result = submit(run_fixture, builder(run_fixture), reason_token)

    assert result.returncode != 0, (
        f"{reason_token} 불일치 evidence가 수용됨. stdout={result.stdout}"
    )
    combined = f"{result.stdout}\n{result.stderr}"
    assert reason_token in combined, f"거부 사유에 {reason_token} 언급 없음:\n{combined}"

    after = indexed_files(run_fixture)
    assert after == before, (
        f"거부된 evidence가 색인 파일을 남겼다(색인 전 거부 위반): {[str(p) for p in after]}"
    )


def test_only_valid_evidence_is_indexed_and_immutable(run_fixture):
    """S-9 ② 네 건 제출 후 정상 1종만 `evidence/<scope>/<evidence-id>.json`에 색인되고,
    같은 id 재제출로 내용을 바꿀 수 없다(불변 색인)."""
    submit(run_fixture, _schema_mismatch(run_fixture), "m1")
    submit(run_fixture, _code_head_mismatch(run_fixture), "m2")
    submit(run_fixture, _scope_hash_mismatch(run_fixture), "m3")

    good = valid_evidence(run_fixture)
    accepted = ok(submit(run_fixture, good, "good"), "evidence submit(정상)")
    assert accepted.get("accepted") is True, f"정상 evidence가 수용되지 않음: {accepted}"

    files = indexed_files(run_fixture)
    assert len(files) == 1, (
        f"색인 파일이 정확히 1건이 아님(불일치 3종 누수): {[str(p) for p in files]}"
    )
    expected = run_fixture["run_root"] / "evidence" / "mt-verified" / "ev-ok.json"
    assert files[0] == expected, f"색인 경로 계약 위반(§4.5): {files[0]} != {expected}"

    frozen = expected.read_bytes()
    tampered = dict(good)
    tampered["result"] = "fail"
    rewrite = submit(run_fixture, tampered, "tampered")
    assert rewrite.returncode != 0, (
        f"색인된 evidence가 덮어쓰기됨(불변 위반). stdout={rewrite.stdout}"
    )
    assert expected.read_bytes() == frozen, "색인된 evidence 바이트가 변경됨(불변 위반)"
    assert len(indexed_files(run_fixture)) == 1, "재제출이 추가 색인 파일을 만들었다"


def test_evidence_from_the_runner_itself_is_not_independent(run_fixture):
    """S-9 ③ 수용기준 9의 '독립' 검증 — Runner attempt 자신이 발행한 evidence는
    독립 검증 증거로 색인되지 않는다."""
    task = run_fixture["tasks"]["mt-verified"]
    runner_attempt = task.get("runner_attempt_id")
    assert runner_attempt, (
        f"RED: workgraph.json이 {task.get('id')}의 runner_attempt_id를 공표하지 않음: {task}"
    )

    document = valid_evidence(run_fixture, evidence_id="ev-selfmade")
    document["verifier"] = {"kind": "runner", "attempt_id": runner_attempt}

    result = submit(run_fixture, document, "selfmade")

    assert result.returncode != 0, (
        f"Runner 자신이 발행한 evidence가 수용됨(수용기준 9 위반). stdout={result.stdout}"
    )
    assert not indexed_files(run_fixture), "거부된 self-made evidence가 색인됨"


# ====================================== S-9 ④ 독립 검증 증거 없는 accepted 전이 차단


def test_accept_is_blocked_without_independent_evidence(run_fixture):
    """S-9 ④ 독립 검증 증거가 없는 미니 태스크는 accepted로 전이할 수 없다."""
    assert task_state(run_fixture, "mt-unverified") != "accepted", "fixture 전제 위반"

    result = accept(run_fixture, "mt-unverified")

    assert result.returncode != 0, (
        f"증거 없는 태스크가 accepted로 전이됨(수용기준 9 위반). stdout={result.stdout}"
    )
    combined = f"{result.stdout}\n{result.stderr}".lower()
    assert "evidence" in combined, f"거부 사유에 evidence 언급 없음:\n{combined}"
    assert task_state(run_fixture, "mt-unverified") != "accepted", (
        "거부됐는데 workgraph 상태가 accepted로 바뀜(상태 손상)"
    )


def test_accept_succeeds_only_after_independent_evidence_is_indexed(run_fixture):
    """S-9 ⑤ 양성 대조 — 정상 evidence가 색인된 뒤에만 accepted 전이가 허용된다."""
    blocked = accept(run_fixture, "mt-verified")
    assert blocked.returncode != 0, "색인 전에 accepted 전이가 허용됨"

    ok(submit(run_fixture, valid_evidence(run_fixture), "good"), "evidence submit(정상)")

    allowed = accept(run_fixture, "mt-verified")
    assert allowed.returncode == 0, (
        f"독립 증거가 색인됐는데 accepted 전이가 거부됨: "
        f"stdout={allowed.stdout}\nstderr={allowed.stderr}"
    )
    assert task_state(run_fixture, "mt-verified") == "accepted", (
        "전이가 성공했다고 보고했으나 workgraph 상태가 accepted가 아님"
    )
    assert task_state(run_fixture, "mt-unverified") != "accepted", (
        "무관한 태스크 상태가 함께 변경됨"
    )
