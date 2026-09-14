"""
@header {
  "module": "test_revalidation",
  "layer": "test",
  "domain": "opal-workspace",
  "description": "needs_revalidation 1-hop 전파 RED-first 스위트 (TEST-SCENARIO S-16의 계약 revision 전파 부분 / W-28). 외부 계약 revision이 바뀐 실제 git fixture에서 직접 consumer만 needs_revalidation으로 전환되고 무관·미실행 태스크 재검증이 0인지, 재검증 범위가 consumer의 수용 시나리오·계약 테스트뿐인지, 통과 시 즉시 accepted 복귀하고 실패 시 그 consumer의 Repair만 열리는지, Repair가 출력 계약을 다시 바꾼 경우에만 다음 1-hop으로 전파되는지를 기계 단언한다 (제안서 §9.1, §13.2 수용기준 26). PLAN H-6에 따라 내부 API를 import하지 않고 공개 CLI(run.sh revalidate·JSON stdout)와 run root 파일 계약(workgraph.json·attempts)만 사용한다. mock 금지 — 계약 테스트는 fixture 저장소의 실제 스크립트를 실제 프로세스로 실행한다. S-16의 '타 lease dirty PROVE 실패 귀속' 부분은 W-17의 test_recovery.py가 소유하므로 여기서 다루지 않는다.",
  "exports": [
    "test_revalidate_transitions_direct_consumer_only",
    "test_unrelated_and_queued_tasks_are_not_revalidated",
    "test_revalidation_scope_is_acceptance_and_contract_tests_only",
    "test_passing_revalidation_returns_to_accepted_immediately",
    "test_failing_revalidation_opens_repair_for_that_consumer_only",
    "test_failing_revalidation_does_not_propagate_downstream",
    "test_propagation_is_one_hop_when_output_contract_revision_changes"
  ],
  "depends": [
    "git CLI",
    "opal/tools/oppb-runtime-tool/run.sh(W-6, 미구현 — RED 대상)",
    "opal/tools/oppb-runtime-tool/revalidation.py(W-26, 미구현 — RED 대상)",
    "opal/tools/oppb-runtime-tool/tests/test_product_flow.py(동일 CLI·run root 계약)"
  ]
}

이 스위트가 고정하는 공개 계약 (PLAN H-6)
------------------------------------------
1. 공개 CLI — `opal/tools/oppb-runtime-tool/run.sh`
   - `init --allocator-root <A> --project-root <P>`
     → `{"ok": true, "run_root": ...}` (계약 자체는 W-10 `test_oppb_init.py` 소유)
   - `revalidate --run-root <R> --contract <contract_id> --revision <n>`
     → `{"ok": true,
          "needs_revalidation": [task_id...],   # 전환 대상 = 직접 consumer뿐
          "accepted": [task_id...],             # 재검증 통과 후 즉시 복귀
          "repair_opened": [task_id...],        # 재검증 실패 consumer
          "skipped": [task_id...]}`             # 무관·미실행 태스크

2. run root 파일 계약 (seed = 선행 상태 재현, 관측 = 전이 결과)
   - `<run_root>/workgraph.json`
       tasks[].{id, state, profile, consumes_contracts[],
                produces_contract{id, revision},
                acceptance_scenarios[].{id, command},
                contract_tests[].{id, command}}
       contracts[].{id, revision, owner}
   - `<run_root>/attempts/<task_id>/<attempt_id>/execution-packet.json`
       재검증 attempt는 `mode: "revalidation"`과
       `revalidation_scope.{kinds[], commands[]}`를 갖는다.
     Repair attempt는 `mode: "repair"`를 갖는다.

미니 태스크 상태값은 제안서 §9.1의
queued / running / verifying / accepted / needs_revalidation / repair / blocked 뿐이다.
"""

from __future__ import annotations

import json
import pathlib
import subprocess

import pytest

TESTS_DIR = pathlib.Path(__file__).resolve().parent
TOOL_DIR = TESTS_DIR.parent
RUN_SH = TOOL_DIR / "run.sh"

GIT_CONFIG_ARGS = [
    "-c", "user.email=test@opal.local",
    "-c", "user.name=OPAL Test",
    "-c", "commit.gpgsign=false",
    "-c", "init.defaultBranch=main",
]

CONTRACT_ORDERS = "C-ORDERS"
CONTRACT_API = "C-API"

TASK_PRODUCER = "t-orders"      # C-ORDERS 소유자
TASK_DIRECT = "t-api"           # C-ORDERS 직접 consumer, C-API 생산자
TASK_TWO_HOP = "t-ui"           # C-API consumer = C-ORDERS 기준 2-hop
TASK_UNRELATED = "t-report"     # 무관, accepted
TASK_QUEUED = "t-batch"         # C-ORDERS consumer지만 아직 실행 전

TERMINAL_STATES = {
    "queued", "running", "verifying", "accepted", "needs_revalidation", "repair", "blocked",
}


# --------------------------------------------------------------------------------------
# 실 git·실 CLI 헬퍼 (mock 금지 — PLAN 제약)
# --------------------------------------------------------------------------------------

def run_git(args: list[str], cwd: pathlib.Path) -> subprocess.CompletedProcess:
    cmd = ["git", *GIT_CONFIG_ARGS, *args]
    result = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"git fixture 실패: {' '.join(cmd)}\ncwd={cwd}\n"
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )
    return result


def run_oppb_cli(args: list[str], timeout: int = 600, expect_ok: bool = True) -> dict:
    assert RUN_SH.exists(), (
        f"//oppb runtime CLI가 없다: {RUN_SH} — W-6이 `run.sh`를 제공해야 한다"
    )
    result = subprocess.run(
        ["bash", str(RUN_SH), *args], capture_output=True, text=True, timeout=timeout
    )
    if expect_ok:
        assert result.returncode == 0, (
            f"`run.sh {' '.join(args)}` exit={result.returncode}\n"
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:  # pragma: no cover - 계약 위반 시에만
        raise AssertionError(
            f"`run.sh {' '.join(args)}`가 JSON stdout 계약을 지키지 않았다: {exc}\n"
            f"stdout={result.stdout}"
        ) from exc


def read_json(path: pathlib.Path) -> dict:
    assert path.exists(), f"run root 파일 계약 위반 — 없음: {path}"
    return json.loads(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------------------
# fixture — 실제 git 저장소 + 실제 계약 테스트 스크립트 + seed된 run root
# --------------------------------------------------------------------------------------

PASSING_CHECK = "import sys\nsys.exit(0)\n"
FAILING_CHECK = (
    "import sys\n"
    "sys.stderr.write('contract mismatch: C-ORDERS revision 2\\n')\n"
    "sys.exit(1)\n"
)


def _script_cmd(repo: pathlib.Path, name: str) -> str:
    return f"python3 {repo / 'checks' / name}"


def _build_repo(root: pathlib.Path, direct_consumer_passes: bool) -> pathlib.Path:
    """
    실제 git 저장소 fixture. 계약 테스트·수용 시나리오는 실행 가능한 실제 스크립트다.
    `direct_consumer_passes=False`이면 직접 consumer의 계약 테스트만 실제로 exit 1 한다.
    """
    repo = root / "hub"
    (repo / "checks").mkdir(parents=True)
    run_git(["init"], repo)

    scripts = {
        "api_contract.py": PASSING_CHECK if direct_consumer_passes else FAILING_CHECK,
        "api_acceptance.py": PASSING_CHECK,
        "ui_contract.py": PASSING_CHECK,
        "ui_acceptance.py": PASSING_CHECK,
        "report_acceptance.py": PASSING_CHECK,
        "orders_acceptance.py": PASSING_CHECK,
        "batch_acceptance.py": PASSING_CHECK,
    }
    for name, body in scripts.items():
        (repo / "checks" / name).write_text(body, encoding="utf-8")
    (repo / "README.md").write_text("# revalidation fixture\n", encoding="utf-8")

    run_git(["add", "-A"], repo)
    run_git(["commit", "-m", "fixture: revalidation graph"], repo)
    return repo


def _seed_workgraph(repo: pathlib.Path) -> dict:
    """
    제안서 §9.1 전파 규칙을 관측할 수 있는 최소 그래프.

        C-ORDERS ──> t-api ──(C-API)──> t-ui
             │
             └──> t-batch (queued, 실행 전)

        t-report: 어떤 계약도 소비하지 않는 무관 accepted 태스크
    """
    return {
        "contracts": [
            {"id": CONTRACT_ORDERS, "revision": 1, "owner": TASK_PRODUCER},
            {"id": CONTRACT_API, "revision": 1, "owner": TASK_DIRECT},
        ],
        "tasks": [
            {
                "id": TASK_PRODUCER,
                "state": "accepted",
                "profile": "fast",
                "consumes_contracts": [],
                "produces_contract": {"id": CONTRACT_ORDERS, "revision": 1},
                "acceptance_scenarios": [
                    {"id": "A-ORDERS-1", "command": _script_cmd(repo, "orders_acceptance.py")}
                ],
                "contract_tests": [],
            },
            {
                "id": TASK_DIRECT,
                "state": "accepted",
                "profile": "standard",
                "consumes_contracts": [CONTRACT_ORDERS],
                "produces_contract": {"id": CONTRACT_API, "revision": 1},
                "acceptance_scenarios": [
                    {"id": "A-API-1", "command": _script_cmd(repo, "api_acceptance.py")}
                ],
                "contract_tests": [
                    {"id": "K-API-1", "command": _script_cmd(repo, "api_contract.py")}
                ],
            },
            {
                "id": TASK_TWO_HOP,
                "state": "accepted",
                "profile": "fast",
                "consumes_contracts": [CONTRACT_API],
                "produces_contract": None,
                "acceptance_scenarios": [
                    {"id": "A-UI-1", "command": _script_cmd(repo, "ui_acceptance.py")}
                ],
                "contract_tests": [
                    {"id": "K-UI-1", "command": _script_cmd(repo, "ui_contract.py")}
                ],
            },
            {
                "id": TASK_UNRELATED,
                "state": "accepted",
                "profile": "fast",
                "consumes_contracts": [],
                "produces_contract": None,
                "acceptance_scenarios": [
                    {"id": "A-REPORT-1", "command": _script_cmd(repo, "report_acceptance.py")}
                ],
                "contract_tests": [],
            },
            {
                "id": TASK_QUEUED,
                "state": "queued",
                "profile": "fast",
                "consumes_contracts": [CONTRACT_ORDERS],
                "produces_contract": None,
                "acceptance_scenarios": [
                    {"id": "A-BATCH-1", "command": _script_cmd(repo, "batch_acceptance.py")}
                ],
                "contract_tests": [],
            },
        ],
    }


def _prepare(tmp_root: pathlib.Path, direct_consumer_passes: bool = True) -> dict:
    repo = _build_repo(tmp_root, direct_consumer_passes)
    init_res = run_oppb_cli(
        ["init", "--allocator-root", str(repo), "--project-root", str(repo)]
    )
    assert init_res.get("ok") is True, f"init 실패: {init_res}"
    run_root = pathlib.Path(init_res["run_root"])

    workgraph = _seed_workgraph(repo)
    (run_root / "workgraph.json").write_text(
        json.dumps(workgraph, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return {"repo": repo, "run_root": run_root}


def _states(run_root: pathlib.Path) -> dict[str, str]:
    workgraph = read_json(run_root / "workgraph.json")
    states = {t["id"]: t["state"] for t in workgraph["tasks"]}
    unknown = {tid: s for tid, s in states.items() if s not in TERMINAL_STATES}
    assert unknown == {}, f"§9.1에 없는 상태값이 기록됐다: {unknown}"
    return states


def _attempt_dirs(run_root: pathlib.Path, task_id: str) -> list[pathlib.Path]:
    task_dir = run_root / "attempts" / task_id
    if not task_dir.is_dir():
        return []
    return sorted(p for p in task_dir.iterdir() if p.is_dir())


def _packets(run_root: pathlib.Path, task_id: str) -> list[dict]:
    return [
        read_json(d / "execution-packet.json")
        for d in _attempt_dirs(run_root, task_id)
        if (d / "execution-packet.json").exists()
    ]


def _revalidate(run_root: pathlib.Path, contract_id: str, revision: int) -> dict:
    return run_oppb_cli(
        [
            "revalidate",
            "--run-root", str(run_root),
            "--contract", contract_id,
            "--revision", str(revision),
        ]
    )


@pytest.fixture
def passing_graph(tmp_path) -> dict:
    return _prepare(tmp_path, direct_consumer_passes=True)


@pytest.fixture
def failing_graph(tmp_path) -> dict:
    return _prepare(tmp_path, direct_consumer_passes=False)


# --------------------------------------------------------------------------------------
# 수용기준 26 — 직접 consumer만 needs_revalidation
# --------------------------------------------------------------------------------------

def test_revalidate_transitions_direct_consumer_only(passing_graph):
    run_root = passing_graph["run_root"]
    result = _revalidate(run_root, CONTRACT_ORDERS, 2)

    assert result.get("ok") is True, f"revalidate 실패: {result}"
    assert sorted(result.get("needs_revalidation", [])) == [TASK_DIRECT], (
        "C-ORDERS revision 변경 시 전환 대상은 직접 consumer뿐이어야 한다 — "
        f"실제={result.get('needs_revalidation')}"
    )
    assert TASK_TWO_HOP not in result.get("needs_revalidation", []), (
        "2-hop consumer가 같은 연산에서 전환됐다 (§9.1 1-hop 규칙 위반)"
    )


def test_unrelated_and_queued_tasks_are_not_revalidated(passing_graph):
    """§9.1 — 무관하거나 아직 실행 전인 태스크는 재검증하지 않는다."""
    run_root = passing_graph["run_root"]
    before = {
        tid: len(_attempt_dirs(run_root, tid))
        for tid in (TASK_PRODUCER, TASK_TWO_HOP, TASK_UNRELATED, TASK_QUEUED)
    }

    _revalidate(run_root, CONTRACT_ORDERS, 2)
    states = _states(run_root)

    assert states[TASK_UNRELATED] == "accepted", "무관 태스크 상태가 바뀌었다"
    assert states[TASK_QUEUED] == "queued", "실행 전 태스크가 재검증 대상이 됐다"
    assert states[TASK_PRODUCER] == "accepted", "계약 생산자 상태가 바뀌었다"

    for tid, count in before.items():
        assert len(_attempt_dirs(run_root, tid)) == count, (
            f"{tid}에 재검증 attempt가 생성됐다 — 무관 태스크 재검증 0 위반"
        )


def test_revalidation_scope_is_acceptance_and_contract_tests_only(passing_graph):
    """§9.1 — 재검증은 consumer의 수용 시나리오와 계약 테스트만 실행한다."""
    run_root = passing_graph["run_root"]
    _revalidate(run_root, CONTRACT_ORDERS, 2)

    packets = [p for p in _packets(run_root, TASK_DIRECT) if p.get("mode") == "revalidation"]
    assert len(packets) == 1, (
        f"{TASK_DIRECT}의 재검증 packet이 1건이 아니다: {len(packets)}건"
    )

    scope = packets[0].get("revalidation_scope", {})
    assert sorted(scope.get("kinds", [])) == ["acceptance_scenario", "contract_test"], (
        f"재검증 범위가 수용 시나리오·계약 테스트를 벗어났다: {scope.get('kinds')}"
    )
    commands = scope.get("commands", [])
    assert len(commands) == 2, f"실행 명령이 2건이 아니다: {commands}"
    assert all("api_" in c for c in commands), (
        f"다른 태스크의 명령이 재검증 범위에 들어왔다: {commands}"
    )


def test_passing_revalidation_returns_to_accepted_immediately(passing_graph):
    """§9.1 — 통과하면 즉시 accepted로 돌아간다."""
    run_root = passing_graph["run_root"]
    result = _revalidate(run_root, CONTRACT_ORDERS, 2)

    assert _states(run_root)[TASK_DIRECT] == "accepted", (
        "재검증 통과 후에도 needs_revalidation에 머물렀다"
    )
    assert result.get("accepted") == [TASK_DIRECT]
    assert result.get("repair_opened", []) == [], (
        f"통과했는데 Repair가 열렸다: {result.get('repair_opened')}"
    )


# --------------------------------------------------------------------------------------
# §9.1 — 실패 시 그 consumer의 Repair만 열린다
# --------------------------------------------------------------------------------------

def test_failing_revalidation_opens_repair_for_that_consumer_only(failing_graph):
    run_root = failing_graph["run_root"]
    result = _revalidate(run_root, CONTRACT_ORDERS, 2)

    assert result.get("repair_opened") == [TASK_DIRECT], (
        f"실패 consumer의 Repair만 열려야 한다 — 실제={result.get('repair_opened')}"
    )
    states = _states(run_root)
    assert states[TASK_DIRECT] == "repair", f"{TASK_DIRECT} 상태={states[TASK_DIRECT]}"

    repair_packets = [p for p in _packets(run_root, TASK_DIRECT) if p.get("mode") == "repair"]
    assert len(repair_packets) == 1, (
        f"Repair attempt가 1건이 아니다: {len(repair_packets)}건"
    )


def test_failing_revalidation_does_not_propagate_downstream(failing_graph):
    """
    §9.1 — Repair가 **다시 출력 계약을 바꾼 경우에만** 다음 1-hop으로 전파된다.
    재검증 실패 그 자체로는 downstream이 전환되지 않는다.
    """
    run_root = failing_graph["run_root"]
    _revalidate(run_root, CONTRACT_ORDERS, 2)

    states = _states(run_root)
    assert states[TASK_TWO_HOP] == "accepted", (
        "출력 계약이 아직 바뀌지 않았는데 2-hop consumer가 전환됐다"
    )
    assert _attempt_dirs(run_root, TASK_TWO_HOP) == [], (
        "downstream에 재검증 attempt가 생성됐다"
    )

    workgraph = read_json(run_root / "workgraph.json")
    api = next(c for c in workgraph["contracts"] if c["id"] == CONTRACT_API)
    assert api["revision"] == 1, (
        f"Repair 없이 C-API revision이 올라갔다: {api['revision']}"
    )


def test_propagation_is_one_hop_when_output_contract_revision_changes(passing_graph):
    """
    §9.1 — 출력 계약(C-API) revision이 실제로 바뀌면 그 직접 consumer(t-ui) 하나만 전환된다.
    상류(t-orders)·무관(t-report)·미실행(t-batch)은 그대로다.
    """
    run_root = passing_graph["run_root"]
    _revalidate(run_root, CONTRACT_ORDERS, 2)

    result = _revalidate(run_root, CONTRACT_API, 2)
    assert sorted(result.get("needs_revalidation", [])) == [TASK_TWO_HOP], (
        f"C-API 변경의 전환 대상이 t-ui 하나가 아니다: {result.get('needs_revalidation')}"
    )

    states = _states(run_root)
    assert states[TASK_TWO_HOP] == "accepted", "t-ui 재검증이 통과했는데 accepted로 복귀하지 않았다"
    assert states[TASK_PRODUCER] == "accepted"
    assert states[TASK_UNRELATED] == "accepted"
    assert states[TASK_QUEUED] == "queued"
    assert _attempt_dirs(run_root, TASK_UNRELATED) == [], "무관 태스크가 재검증됐다"
    assert _attempt_dirs(run_root, TASK_QUEUED) == [], "미실행 태스크가 재검증됐다"
