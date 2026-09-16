"""
@header {
  "module": "test_verifier_adapter",
  "layer": "test",
  "domain": "oppb-runtime",
  "description": "OPPB Verifier evidence adapter(W-24) 공개 CLI 계약 RED 테스트. 제안서 §4.2 매핑표(통합·E2E=opal-test-agent, Security=op-gc-security, Convention=op-gc-convention)와 §10 검증 시점표(위험 ACCEPT·계약 폐쇄·PROJECT VERIFY)를 근거로 (a) 조건부 Verifier 호출 시점 판정, (b) 세 워커의 기존 입력 계약 그대로의 dispatch payload 생성, (c) 산출 보고서의 Evidence schema 변환·제출을 검증한다. 수용기준 9(독립 검증 증거)에 따라 adapter가 runner attempt id와 같은 attempt id를 절대 싣지 않는 것을 확인한다. PLAN H-6에 따라 내부 함수를 import하지 않고 공개 CLI(run.sh verifier)와 run root 파일 계약만으로 검증한다. mock/patch 금지 — 실제 git 저장소와 실제 파일만 사용한다.",
  "exports": [],
  "depends": ["opal/tools/oppb-runtime-tool/run.sh", "git CLI 2.x"]
}
"""

from __future__ import annotations

import json
import pathlib
import subprocess

import pytest

TOOL_DIR = pathlib.Path(__file__).resolve().parents[1]
RUN_SH = TOOL_DIR / "run.sh"

GIT_AUTHOR_ARGS = [
    "-c", "user.email=test@opal.local",
    "-c", "user.name=OPAL Test",
    "-c", "commit.gpgsign=false",
    "-c", "init.defaultBranch=main",
]


# --------------------------------------------------------------------- 헬퍼


def run_git(args: list[str], cwd: pathlib.Path, check: bool = True) -> subprocess.CompletedProcess:
    cmd = ["git", *GIT_AUTHOR_ARGS, *args]
    result = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(
            f"git fixture 구성 실패: {' '.join(cmd)}\nstdout={result.stdout}\nstderr={result.stderr}"
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


def run_oppb(args: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
    if not RUN_SH.exists():
        pytest.fail(f"RED: run.sh 미존재 — 요청 명령: run.sh {' '.join(args)}")
    return subprocess.run(
        ["bash", str(RUN_SH), *args], capture_output=True, text=True, timeout=timeout
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


def fail(result: subprocess.CompletedProcess, label: str) -> dict:
    assert result.returncode != 0, f"{label}이 거부되지 않음: stdout={result.stdout}"
    payload = parse_json_stdout(result, label)
    assert payload.get("ok") is False, f"{label} 실패 응답의 ok가 False가 아님: {payload}"
    return payload


# 계약 폐쇄 판정을 위해 두 미니 태스크가 같은 contract(`api/orders`)를 공유한다.
MINI_TASKS = [
    {
        "id": "mt-producer",
        "capability": "cap-producer",
        "pre_state": "candidate_ready",
        "runner_attempt_id": "mt-producer-runner-0",
        "lease": {
            "tracked_writes": ["src/orders/api.py"],
            "contracts": ["api/orders"],
            "runtime_resources": ["port:8000"],
        },
    },
    {
        "id": "mt-consumer",
        "capability": "cap-consumer",
        "pre_state": "candidate_ready",
        "runner_attempt_id": "mt-consumer-runner-0",
        "lease": {"tracked_writes": ["src/web/orders.ts"], "contracts": ["api/orders"]},
    },
    {
        "id": "mt-plain",
        "capability": "cap-plain",
        "pre_state": "candidate_ready",
        "runner_attempt_id": "mt-plain-runner-0",
        "lease": {"tracked_writes": ["docs/notes.md"]},
    },
]


@pytest.fixture
def run_fixture(tmp_path):
    repo = make_hub_repo(tmp_path)
    init = ok(
        run_oppb(["init", "--allocator-root", str(repo), "--project-root", str(repo)]), "init"
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
        ),
        encoding="utf-8",
    )
    ok(
        run_oppb(["workgraph", "load", "--run-root", init["run_root"], "--spec", str(spec)]),
        "workgraph load",
    )
    run_root = pathlib.Path(init["run_root"])
    graph = json.loads((run_root / "workgraph.json").read_text(encoding="utf-8"))
    return {
        "repo": repo,
        "run_root": run_root,
        "tasks": {t["id"]: t for t in graph["mini_tasks"]},
        "code_head": run_git(["rev-parse", "HEAD"], cwd=repo).stdout.strip(),
        "tmp": tmp_path,
    }


def plan(run_fixture, task_id: str, trigger: str, *extra: str) -> dict:
    return ok(
        run_oppb(
            [
                "verifier", "plan",
                "--run-root", str(run_fixture["run_root"]),
                "--task-id", task_id,
                "--trigger", trigger,
                *extra,
            ]
        ),
        f"verifier plan({task_id},{trigger})",
    )


def write_report(run_fixture, name: str, payload: dict) -> str:
    path = run_fixture["tmp"] / f"{name}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return str(path)


def convention_report(status: str = "pass", findings=None) -> dict:
    return {
        "check": "convention",
        "status": status,
        "checked_files": ["src/orders/api.py"],
        "findings": findings if findings is not None else [],
        "evidence": ["ruff check src/orders/api.py"],
        "references": ["docs/CONVENTIONS.md"],
        "missing_capabilities": [],
        "report_path": "/tmp/GC-CONVENTION-20260915-1200.md",
        "commands": [["ruff", "check", "src/orders/api.py"]],
    }


# ------------------------------------------------ 조건부 Verifier 호출 시점 판정


def test_plain_accept_calls_convention_only(run_fixture):
    """§10 ACCEPT 행 — 위험 신호도 계약 폐쇄도 없으면 경량 Convention 검사만 판정한다."""
    result = plan(run_fixture, "mt-plain", "accept")
    assert result["resolved_trigger"] == "accept", result
    assert [v["kind"] for v in result["verifiers"]] == ["convention"], result


def test_risk_signal_promotes_accept_to_risk_accept(run_fixture):
    """§10 위험 ACCEPT 행 — 새 I/O·인증·권한·외부 입력·명령 실행 신호는 Security Verifier를 부른다."""
    result = plan(run_fixture, "mt-plain", "accept", "--signals", "auth,command_execution")
    assert result["resolved_trigger"] == "risk_accept", result
    kinds = [v["kind"] for v in result["verifiers"]]
    assert kinds == ["convention", "security"], result
    assert "auth" in result["risk_signals"] and "command_execution" in result["risk_signals"]


def test_runtime_resource_lease_is_a_risk_signal(run_fixture):
    """lease.runtime_resources 선언은 그 자체가 새 I/O 신호다 — 명시 신호 없이도 승격한다."""
    result = plan(run_fixture, "mt-producer", "accept")
    assert result["resolved_trigger"] == "risk_accept", result
    assert "security" in [v["kind"] for v in result["verifiers"]], result


def test_contract_closure_calls_integration_verifier(run_fixture):
    """§10 계약 폐쇄 행 — 같은 contract를 공유한 peer가 모두 run을 마치면 통합 검증을 부른다."""
    result = plan(run_fixture, "mt-producer", "accept")
    assert result["contract_closure"] is True, result
    assert "integration" in [v["kind"] for v in result["verifiers"]], result
    assert "api/orders" in result["closed_contracts"], result


def test_no_contract_closure_without_peer(run_fixture):
    result = plan(run_fixture, "mt-plain", "accept")
    assert result["contract_closure"] is False, result
    assert "integration" not in [v["kind"] for v in result["verifiers"]], result


def test_project_verify_calls_all_three_verifiers(run_fixture):
    """§10 PROJECT VERIFY 행 — 전체 회귀·통합 보안·전체 신규 컨벤션은 세 Verifier 전부다."""
    result = plan(run_fixture, "mt-plain", "project_verify")
    assert sorted(v["kind"] for v in result["verifiers"]) == [
        "convention", "integration", "security",
    ], result


def test_unknown_trigger_is_rejected(run_fixture):
    payload = fail(
        run_oppb(
            [
                "verifier", "plan",
                "--run-root", str(run_fixture["run_root"]),
                "--task-id", "mt-plain",
                "--trigger", "whenever",
            ]
        ),
        "unknown trigger",
    )
    assert payload["error"] == "verifier_trigger_unknown", payload


# ------------------------------------------------ 세 워커 기존 입력 계약 그대로


def test_dispatch_payload_keeps_existing_worker_contracts(run_fixture):
    """C-2 — 세 워커의 입력 계약 키를 adapter가 그대로 채운다(스킬·AGENT.md 무변경)."""
    result = plan(run_fixture, "mt-producer", "project_verify")
    by_kind = {v["kind"]: v for v in result["verifiers"]}

    integration = by_kind["integration"]
    assert integration["agent"] == "opal-test-agent", integration
    assert integration["input"]["test_mode"] == "e2e", integration
    assert set(integration["input"]) >= {
        "mode", "test_mode", "changed_files", "project_root",
    }, integration
    assert integration["input"]["changed_files"] == ["src/orders/api.py"], integration

    security = by_kind["security"]
    assert security["skill"] == "op-gc-security", security
    assert set(security["input"]) == {
        "project_root", "target_files", "output_dir", "timestamp",
    }, security
    assert security["input"]["target_files"] == ["src/orders/api.py"], security

    convention = by_kind["convention"]
    assert convention["skill"] == "op-gc-convention", convention
    assert set(convention["input"]) == {
        "project_root", "target_files", "output_dir", "timestamp",
    }, convention


# ------------------------------------------------ Evidence schema 변환·제출


def submit(run_fixture, task_id: str, kind: str, report: str, *extra: str):
    return run_oppb(
        [
            "verifier", "submit",
            "--run-root", str(run_fixture["run_root"]),
            "--task-id", task_id,
            "--kind", kind,
            "--report", report,
            *extra,
        ]
    )


def test_submit_converts_report_to_indexed_evidence(run_fixture):
    report = write_report(run_fixture, "conv-pass", convention_report())
    payload = ok(submit(run_fixture, "mt-producer", "convention", report), "verifier submit")
    assert payload["accepted"] is True, payload

    indexed = json.loads(pathlib.Path(payload["path"]).read_text(encoding="utf-8"))
    task = run_fixture["tasks"]["mt-producer"]
    assert indexed["schema_version"] == 1, indexed
    assert indexed["scope"] == "mt-producer", indexed
    assert indexed["scope_hash"] == task["scope_hash"], indexed
    assert indexed["code_head"] == run_fixture["code_head"], indexed
    assert indexed["verifier"]["kind"] == "convention", indexed
    assert indexed["result"] == "pass", indexed
    assert indexed["commands"] == [["ruff", "check", "src/orders/api.py"]], indexed


def test_submitted_evidence_is_independent_of_runner_attempt(run_fixture):
    """수용기준 9 — adapter가 싣는 attempt id는 절대 runner attempt id와 같지 않다."""
    report = write_report(run_fixture, "conv-indep", convention_report())
    payload = ok(submit(run_fixture, "mt-producer", "convention", report), "verifier submit")
    indexed = json.loads(pathlib.Path(payload["path"]).read_text(encoding="utf-8"))
    assert indexed["verifier"]["attempt_id"] != "mt-producer-runner-0", indexed


def test_explicit_runner_attempt_id_is_rejected_before_index(run_fixture):
    report = write_report(run_fixture, "conv-dep", convention_report())
    payload = fail(
        submit(
            run_fixture, "mt-producer", "convention", report,
            "--attempt", "mt-producer-runner-0",
        ),
        "runner attempt 재사용",
    )
    assert payload["error"] == "verifier_attempt_not_independent", payload
    evidence_dir = run_fixture["run_root"] / "evidence" / "mt-producer"
    assert not list(evidence_dir.glob("*.json")) if evidence_dir.is_dir() else True


def test_blocking_finding_becomes_fail_result(run_fixture):
    report = write_report(
        run_fixture,
        "conv-fail",
        convention_report(
            findings=[
                {
                    "id": "C-1",
                    "severity": "high",
                    "confidence": "high",
                    "disposition": "blocking",
                    "rule_id": "CONVENTIONS.md §2",
                }
            ]
        ),
    )
    payload = ok(submit(run_fixture, "mt-producer", "convention", report), "verifier submit")
    indexed = json.loads(pathlib.Path(payload["path"]).read_text(encoding="utf-8"))
    assert indexed["result"] == "fail", indexed
    assert indexed["blocking_findings"] == 1, indexed


def test_missing_capabilities_becomes_incomplete_result(run_fixture):
    body = convention_report()
    body["status"] = "partial"
    body["missing_capabilities"] = ["docs/CONVENTIONS.md 부재"]
    report = write_report(run_fixture, "conv-incomplete", body)
    payload = ok(submit(run_fixture, "mt-producer", "convention", report), "verifier submit")
    indexed = json.loads(pathlib.Path(payload["path"]).read_text(encoding="utf-8"))
    assert indexed["result"] == "incomplete", indexed


def test_test_agent_verdict_converts_to_result(run_fixture):
    report = write_report(
        run_fixture,
        "test-agent",
        {
            "artifact_path": "/tmp/test-scenario.json",
            "status": "completed",
            "verdict": "All Pass",
            "pass_count": 3,
            "fail_count": 0,
            "skip_count": 0,
            "commands": ["pytest -q tests/"],
        },
    )
    payload = ok(submit(run_fixture, "mt-producer", "integration", report), "verifier submit")
    indexed = json.loads(pathlib.Path(payload["path"]).read_text(encoding="utf-8"))
    assert indexed["result"] == "pass", indexed
    assert indexed["commands"] == [["pytest", "-q", "tests/"]], indexed


def test_runner_result_triplet_lands_in_evidence_document(run_fixture):
    """O-1 — changes·proof·knowledge는 attempt_result가 아니라 evidence 문서에 안착한다."""
    body = convention_report()
    body["changes"] = [{"work_item": "W-1", "files": ["src/orders/api.py"]}]
    body["proof"] = [{"command": "pytest -q", "exit_code": 0}]
    body["knowledge"] = [{"candidate": "orders API는 idempotent key를 요구한다"}]
    report = write_report(run_fixture, "conv-triplet", body)
    payload = ok(submit(run_fixture, "mt-producer", "convention", report), "verifier submit")
    indexed = json.loads(pathlib.Path(payload["path"]).read_text(encoding="utf-8"))
    assert indexed["runner_result"]["changes"] == body["changes"], indexed
    assert indexed["runner_result"]["proof"] == body["proof"], indexed
    assert indexed["runner_result"]["knowledge"] == body["knowledge"], indexed


def test_task_accept_succeeds_on_adapter_submitted_evidence(run_fixture):
    """AC-9 — adapter가 제출한 증거만으로 accepted 전이가 성립한다."""
    report = write_report(run_fixture, "conv-accept", convention_report())
    ok(submit(run_fixture, "mt-producer", "convention", report), "verifier submit")
    payload = ok(
        run_oppb(
            [
                "task", "accept",
                "--run-root", str(run_fixture["run_root"]),
                "--task-id", "mt-producer",
            ]
        ),
        "task accept",
    )
    assert payload["state"] == "accepted", payload


def test_adapter_does_not_write_git(run_fixture):
    """read-only Verifier 경로 — plan·submit 어느 쪽도 allocator repo를 더럽히지 않는다."""
    before = run_git(["status", "--porcelain"], cwd=run_fixture["repo"]).stdout
    head_before = run_git(["rev-parse", "HEAD"], cwd=run_fixture["repo"]).stdout
    plan(run_fixture, "mt-producer", "project_verify")
    report = write_report(run_fixture, "conv-git", convention_report())
    ok(submit(run_fixture, "mt-producer", "convention", report), "verifier submit")
    assert run_git(["status", "--porcelain"], cwd=run_fixture["repo"]).stdout == before
    assert run_git(["rev-parse", "HEAD"], cwd=run_fixture["repo"]).stdout == head_before
