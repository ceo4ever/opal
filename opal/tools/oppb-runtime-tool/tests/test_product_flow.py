"""
@header {
  "module": "test_product_flow",
  "layer": "test",
  "domain": "opal-workspace",
  "description": "OPPB Product Flow RED-first 스위트 (TEST-SCENARIO S-17 / W-28). 관련 문서가 충분한 기존 OPAL 프로젝트 fixture와 greenfield fixture 각각에서 //oppb를 P0부터 CLOSE까지 완주시키고 제안서 §13.2 수용기준 1·2·3·8·11·12를 기계 단언한다 — PRD·TRD 신규 생성 0건과 INTENT.md 단일 실행 계약, 프로젝트 worktree 1개·미니 태스크 worktree/branch 0개, Fast 미니 태스크 상시 산출물이 packet·result·evidence뿐(§7.3 6종 문서 0건), 프로젝트 완료 전 MEMORY·brain 반영 0과 CLOSE 후 batch 정확히 1회. PLAN H-6에 따라 oppb-runtime-tool 내부 API를 import하지 않고 공개 CLI(run.sh 서브커맨드·JSON stdout)·//oppb 진입점 파일·run root 파일 계약 수준에서만 검증한다. PLAN이 이 스위트에 mock 금지를 명시했으므로 실제 git 저장소·실제 프로세스·실제 파일만 사용한다.",
  "exports": [
    "test_oppb_entry_point_files_exist",
    "test_pipeline_defines_p0_to_p5_twenty_two_rows",
    "test_pipeline_gates_only_at_declared_user_call_points",
    "test_pipeline_has_single_knowledge_batch_row_in_p5",
    "test_no_new_prd_or_trd_is_created",
    "test_intent_md_is_the_single_execution_contract",
    "test_single_project_worktree_and_zero_mini_task_worktrees",
    "test_zero_mini_task_branches",
    "test_fast_mini_task_artifacts_are_packet_result_evidence_only",
    "test_forbidden_mini_task_documents_are_never_created",
    "test_no_knowledge_write_before_p5",
    "test_knowledge_batch_runs_exactly_once_after_close"
  ],
  "depends": [
    "git CLI",
    "opal/tools/oppb-runtime-tool/run.sh(W-6, 미구현 — RED 대상)",
    "opal/skills/opal-pilot-project-build/SKILL.md(W-19, 미구현 — RED 대상)",
    "opal/skills/opal-pilot-project-build/references/pipeline.json(W-20, 미구현 — RED 대상)",
    "opal/tools/worktree-tool/tests/conftest.py(실 git fixture 패턴 원천)"
  ]
}

이 스위트가 고정하는 공개 계약 (PLAN H-6 — 내부 함수·클래스 시그니처는 고정하지 않는다)
---------------------------------------------------------------------------------------
1. `//oppb` 진입점 파일
   - `opal/skills/opal-pilot-project-build/SKILL.md`
   - `opal/skills/opal-pilot-project-build/references/pipeline.json`
     (`spec_version`/`skill`/`meta.stages`/`task_steps[].{id,key,stage,item,gate?}`,
      PLAN §Appendix A의 P0~P5 22행)

2. 공개 CLI — `opal/tools/oppb-runtime-tool/run.sh`
   - `init --allocator-root <A> --project-root <P>`
     → stdout JSON `{"ok": true, "run_id": ..., "run_root": ..., "cache_root": ...}`
   - `project-run --run-root <R>`
     → P0부터 CLOSE까지 무인 완주. stdout JSON `{"ok": true, "project_state": "closed", ...}`

3. run root 파일 계약
   - 입력 seed: `<run_root>/INTENT.md`, `<run_root>/gate-approvals.json`
   - 산출(제안서 §7.1·§5 P5):
     `<run_root>/workgraph.json`
     `<run_root>/attempts/<task_id>/<attempt_id>/execution-packet.json`
     `<run_root>/attempts/<task_id>/<attempt_id>/result.json`
     `<run_root>/evidence/<scope>/<evidence_id>.json`
     `<run_root>/events.jsonl`
     `<run_root>/knowledge-receipt.json`

`init`의 run root·cache root·`.git/info/exclude` 봉인 계약 자체는 W-10의
`test_oppb_init.py`(S-7)가 소유한다. 이 스위트는 `init`을 fixture 구성 수단으로만 쓰고
그 계약을 중복 단언하지 않는다.
"""

from __future__ import annotations

import json
import pathlib
import subprocess

import pytest

# --------------------------------------------------------------------------------------
# 경로 상수
# --------------------------------------------------------------------------------------

TESTS_DIR = pathlib.Path(__file__).resolve().parent
TOOL_DIR = TESTS_DIR.parent
REPO_ROOT = TOOL_DIR.parents[2]

RUN_SH = TOOL_DIR / "run.sh"
SKILL_DIR = REPO_ROOT / "opal" / "skills" / "opal-pilot-project-build"
SKILL_MD = SKILL_DIR / "SKILL.md"
PIPELINE_JSON = SKILL_DIR / "references" / "pipeline.json"

# 제안서 §7.3 — 미니 태스크별로 생성하지 않는 문서
FORBIDDEN_MINI_TASK_DOCS = (
    "TASK.md",
    "DONE.md",
    "ANALYSIS.md",
    "PLAN.md",
    "QA.md",
    "CLOSE.md",
)

# 제안서 §7.1 — Fast 미니 태스크 attempt 디렉토리의 상시 산출물
ALLOWED_ATTEMPT_FILES = {"execution-packet.json", "result.json"}

# PLAN §Appendix A — OPPB pipeline.json 22행
EXPECTED_PIPELINE_ROWS = (
    (1, "p0.context_probe", "P0"),
    (2, "p0.task_capsule", "P0"),
    (3, "p1.intent_draft", "P1"),
    (4, "p1.conditional_prd", "P1"),
    (5, "p1.user_gate", "P1"),
    (6, "p2.project_design", "P2"),
    (7, "p2.workgraph", "P2"),
    (8, "p2.critical_review", "P2"),
    (9, "p2.environment_seal", "P2"),
    (10, "p2.user_gate", "P2"),
    (11, "p3.supervisor_start", "P3"),
    (12, "p3.continuous_execution", "P3"),
    (13, "p3.pm_gate", "P3"),
    (14, "p4.project_checkpoint", "P4"),
    (15, "p4.three_verifiers", "P4"),
    (16, "p4.acceptance", "P4"),
    (17, "p4.pm_gate", "P4"),
    (18, "p5.pre_finalize_guard", "P5"),
    (19, "p5.user_merge_gate", "P5"),
    (20, "p5.knowledge_batch", "P5"),
    (21, "p5.done_md", "P5"),
    (22, "p5.worktree_finalize", "P5"),
)

# PLAN §Appendix A — gate를 두는 행 (제안서 §11이 정한 호출 시점에만)
EXPECTED_GATE_ROW_IDS = {5, 10, 13, 17, 19, 21}

GIT_CONFIG_ARGS = [
    "-c", "user.email=test@opal.local",
    "-c", "user.name=OPAL Test",
    "-c", "commit.gpgsign=false",
    "-c", "init.defaultBranch=main",
]

PROJECT_RUN_TIMEOUT_SEC = 3600


# --------------------------------------------------------------------------------------
# 실 git·실 CLI 헬퍼 (mock 금지 — PLAN 제약)
# --------------------------------------------------------------------------------------

def run_git(args: list[str], cwd: pathlib.Path, check: bool = True) -> subprocess.CompletedProcess:
    """fixture 구성·관측 전용 실제 git 실행. 전역 git config에 의존하지 않는다."""
    cmd = ["git", *GIT_CONFIG_ARGS, *args]
    result = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(
            f"git fixture 실패: {' '.join(cmd)}\ncwd={cwd}\n"
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )
    return result


def run_oppb_cli(args: list[str], timeout: int = 300) -> dict:
    """
    `oppb-runtime-tool/run.sh`의 공개 CLI를 실제 프로세스로 호출하고 JSON stdout을 파싱한다.
    내부 모듈을 import하지 않는다 (PLAN H-6).
    """
    assert RUN_SH.exists(), (
        f"//oppb runtime CLI가 없다: {RUN_SH} "
        "— W-6이 `run.sh`와 JSON stdout 계약을 제공해야 한다"
    )
    result = subprocess.run(
        ["bash", str(RUN_SH), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    assert result.returncode == 0, (
        f"`run.sh {' '.join(args)}` exit={result.returncode}\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:  # pragma: no cover - 계약 위반 시에만
        raise AssertionError(
            f"`run.sh {' '.join(args)}`가 JSON stdout 계약을 지키지 않았다: "
            f"{exc}\nstdout={result.stdout}"
        ) from exc


def read_json(path: pathlib.Path) -> dict:
    assert path.exists(), f"파일 계약 위반 — 없음: {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: pathlib.Path) -> list[dict]:
    assert path.exists(), f"run root 파일 계약 위반 — 없음: {path}"
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


# --------------------------------------------------------------------------------------
# fixture — 실제 git 저장소 2종
# --------------------------------------------------------------------------------------

EXISTING_OPAL_DOCS = {
    "docs/PROJECT.md": (
        "# PROJECT — sample\n\n"
        "## 문서 레지스트리\n"
        "| 문서 | 범위 |\n|---|---|\n"
        "| docs/PRD.md | 제품 요구 |\n"
        "| docs/TRD.md | 기술 요구 |\n"
        "| docs/ARCHITECTURE.md | 구조 |\n"
        "| docs/CONVENTIONS.md | 컨벤션 |\n"
    ),
    "docs/PRD.md": "# PRD\n\n- R-1 주문 생성\n- R-2 주문 조회\n- R-3 주문 취소\n",
    "docs/TRD.md": "# TRD\n\n- Python 3.13 표준 라이브러리\n- 저장소: 단일 git worktree\n",
    "docs/ARCHITECTURE.md": "# ARCHITECTURE\n\n- orders 모듈 단일 계층\n",
    "docs/CONVENTIONS.md": "# CONVENTIONS\n\n- 테스트는 tests/test_*.py\n",
    ".opal/AGENT.md": "# sample project agent\n",
    "src/orders.py": "def create_order(item: str) -> dict:\n    return {'item': item}\n",
    "tests/test_orders.py": (
        "from src.orders import create_order\n\n\n"
        "def test_create_order():\n    assert create_order('a')['item'] == 'a'\n"
    ),
}

GREENFIELD_DOCS = {
    "README.md": "# greenfield\n\n아직 OPAL 문서가 없다.\n",
}


def _write_tree(root: pathlib.Path, files: dict[str, str]) -> None:
    for rel, content in files.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def _build_hub_and_project(tmp_root: pathlib.Path, kind: str) -> dict:
    """
    allocator(hub) git 저장소와 그 안의 프로젝트 체크아웃을 실제 git으로 구성한다.

    kind == "existing_opal": PROJECT.md 레지스트리가 PRD·TRD·ARCHITECTURE를 등록한
                             기존 OPAL 프로젝트 (관련 문서 충분)
    kind == "greenfield":    OPAL 문서가 전혀 없는 신규 프로젝트
    """
    hub = tmp_root / f"hub-{kind}"
    hub.mkdir(parents=True)
    run_git(["init"], hub)
    _write_tree(hub, EXISTING_OPAL_DOCS if kind == "existing_opal" else GREENFIELD_DOCS)
    run_git(["add", "-A"], hub)
    run_git(["commit", "-m", f"fixture: {kind}"], hub)
    return {"kind": kind, "hub": hub, "head": run_git(["rev-parse", "HEAD"], hub).stdout.strip()}


INTENT_SEED = """# INTENT

## 목표
주문 취소 사유 코드를 추가하고 조회 API에 노출한다.

## 제외 범위
결제 환불 연동, 관리자 화면.

## 완료조건
- C-1 취소 시 사유 코드가 저장된다
- C-2 조회 API가 사유 코드를 반환한다

## 비가역 제약
실제 배포·외부 호출 없음.

## 예산
attempt 8회, 프로세스 4개.
"""

GATE_APPROVALS_SEED = {
    "approve_all": True,
    "approver": "oppb-red-fixture",
    "note": "무인 완주 관측용 — 사용자 게이트 6종을 사전 승인한다 (제안서 §11)",
}


def _completed_run(tmp_root: pathlib.Path, kind: str) -> dict:
    """fixture 저장소에서 //oppb 런타임을 P0부터 CLOSE까지 실제로 완주시킨다."""
    fixture = _build_hub_and_project(tmp_root, kind)
    hub = fixture["hub"]

    init_res = run_oppb_cli(
        ["init", "--allocator-root", str(hub), "--project-root", str(hub)]
    )
    assert init_res.get("ok") is True, f"init 실패: {init_res}"
    run_root = pathlib.Path(init_res["run_root"])

    (run_root / "INTENT.md").write_text(INTENT_SEED, encoding="utf-8")
    (run_root / "gate-approvals.json").write_text(
        json.dumps(GATE_APPROVALS_SEED, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    run_res = run_oppb_cli(
        ["project-run", "--run-root", str(run_root)],
        timeout=PROJECT_RUN_TIMEOUT_SEC,
    )
    assert run_res.get("ok") is True, f"project-run 실패: {run_res}"
    assert run_res.get("project_state") == "closed", (
        f"P0~CLOSE 완주 실패 — project_state={run_res.get('project_state')!r} (§9.2)"
    )

    fixture["run_root"] = run_root
    fixture["run_result"] = run_res
    fixture["workgraph"] = read_json(run_root / "workgraph.json")
    return fixture


@pytest.fixture(scope="module", params=["existing_opal", "greenfield"])
def completed_project(request, tmp_path_factory) -> dict:
    tmp_root = tmp_path_factory.mktemp(f"oppb-{request.param}")
    return _completed_run(tmp_root, request.param)


@pytest.fixture(scope="module")
def completed_existing_opal(tmp_path_factory) -> dict:
    tmp_root = tmp_path_factory.mktemp("oppb-existing-opal-only")
    return _completed_run(tmp_root, "existing_opal")


def _mini_task_ids(workgraph: dict) -> list[str]:
    tasks = workgraph.get("tasks")
    assert isinstance(tasks, list) and tasks, (
        "workgraph.json이 미니 태스크 record를 담지 않았다 (제안서 §7.1)"
    )
    ids = [t["id"] for t in tasks]
    assert len(set(ids)) == len(ids), f"미니 태스크 ID 중복: {ids}"
    return ids


# --------------------------------------------------------------------------------------
# 1. //oppb 진입점·pipeline 구조 (수용기준 2의 단계 구조 전제)
# --------------------------------------------------------------------------------------

def test_oppb_entry_point_files_exist():
    assert SKILL_MD.exists(), f"//oppb Product Flow 스킬이 없다: {SKILL_MD} (W-19)"
    assert PIPELINE_JSON.exists(), f"OPPB pipeline.json이 없다: {PIPELINE_JSON} (W-20)"


def test_pipeline_defines_p0_to_p5_twenty_two_rows():
    pipeline = read_json(PIPELINE_JSON)
    assert pipeline.get("skill") == "oppb", f"skill 필드가 oppb가 아니다: {pipeline.get('skill')}"
    assert pipeline.get("meta", {}).get("stages") == ["P0", "P1", "P2", "P3", "P4", "P5"]

    rows = pipeline.get("task_steps", [])
    actual = tuple((r["id"], r["key"], r["stage"]) for r in rows)
    assert actual == EXPECTED_PIPELINE_ROWS, (
        "pipeline task_steps가 PLAN §Appendix A 22행과 다르다\n"
        f"기대={EXPECTED_PIPELINE_ROWS}\n실제={actual}"
    )


def test_pipeline_gates_only_at_declared_user_call_points():
    """제안서 §11 — 일반 미니 태스크 완료·Repair·상태 확인에는 gate를 두지 않는다."""
    rows = read_json(PIPELINE_JSON).get("task_steps", [])
    gate_ids = {r["id"] for r in rows if "gate" in r}
    assert gate_ids == EXPECTED_GATE_ROW_IDS, (
        f"gate 배치가 §11 호출 시점과 다르다 — 기대={sorted(EXPECTED_GATE_ROW_IDS)}, "
        f"실제={sorted(gate_ids)}"
    )


def test_pipeline_has_single_knowledge_batch_row_in_p5():
    """수용기준 11·12 — 지식 반영 행은 P5에 정확히 하나뿐이다."""
    rows = read_json(PIPELINE_JSON).get("task_steps", [])
    knowledge_rows = [r for r in rows if "knowledge" in r["key"]]
    assert len(knowledge_rows) == 1, f"지식 반영 행이 1개가 아니다: {[r['key'] for r in knowledge_rows]}"
    assert knowledge_rows[0]["key"] == "p5.knowledge_batch"
    assert knowledge_rows[0]["stage"] == "P5"


# --------------------------------------------------------------------------------------
# 2. 수용기준 1·2 — PRD·TRD 신규 생성 0건, INTENT.md 단일 실행 계약
# --------------------------------------------------------------------------------------

def test_no_new_prd_or_trd_is_created(completed_project):
    """
    수용기준 1. 기존 OPAL fixture는 PROJECT.md가 등록한 문서만 읽고 PRD·TRD를 새로 만들지 않는다.
    greenfield도 INTENT 입력이 충분하므로 PRD·TRD를 만들지 않는다 (신규 OPAL이면 PROJECT.md만 허용).
    """
    hub = completed_project["hub"]
    tracked = run_git(["ls-files"], hub).stdout.splitlines()
    baseline = set(
        EXISTING_OPAL_DOCS if completed_project["kind"] == "existing_opal" else GREENFIELD_DOCS
    )

    created = [p for p in tracked if p not in baseline]
    offenders = [
        p for p in created
        if pathlib.PurePosixPath(p).name.upper() in {"PRD.MD", "TRD.MD"}
    ]
    assert offenders == [], f"PRD·TRD 신규 생성 0건 위반: {offenders}"

    if completed_project["kind"] == "existing_opal":
        for rel in ("docs/PRD.md", "docs/TRD.md"):
            assert (hub / rel).read_text(encoding="utf-8") == EXISTING_OPAL_DOCS[rel], (
                f"기존 {rel}이 수정됐다 — 읽기 전용 재사용 계약 위반"
            )


def test_intent_md_is_the_single_execution_contract(completed_project):
    """수용기준 2. 실행 계약 문서는 INTENT.md 하나로 확정된다."""
    run_root = completed_project["run_root"]
    intents = sorted(p.relative_to(run_root).as_posix() for p in run_root.rglob("INTENT.md"))
    assert intents == ["INTENT.md"], f"INTENT.md가 run root에 1개가 아니다: {intents}"

    workgraph = completed_project["workgraph"]
    contract = workgraph.get("execution_contract")
    assert contract == "INTENT.md", (
        f"workgraph가 지목한 실행 계약이 INTENT.md 하나가 아니다: {contract!r}"
    )


# --------------------------------------------------------------------------------------
# 3. 수용기준 3 — 프로젝트 worktree 1개, 미니 태스크 worktree·branch 0개
# --------------------------------------------------------------------------------------

def test_single_project_worktree_and_zero_mini_task_worktrees(completed_project):
    hub = completed_project["hub"]
    porcelain = run_git(["worktree", "list", "--porcelain"], hub).stdout
    paths = [
        line.split(" ", 1)[1].strip()
        for line in porcelain.splitlines()
        if line.startswith("worktree ")
    ]
    linked = [p for p in paths if pathlib.Path(p).resolve() != hub.resolve()]
    assert len(linked) <= 1, f"프로젝트 worktree가 1개를 넘는다: {linked}"

    for task_id in _mini_task_ids(completed_project["workgraph"]):
        hits = [p for p in paths if task_id in p]
        assert hits == [], f"미니 태스크 {task_id}에 worktree가 만들어졌다: {hits}"


def test_zero_mini_task_branches(completed_project):
    hub = completed_project["hub"]
    branches = [
        b.strip().lstrip("* ").strip()
        for b in run_git(["branch", "--list", "--all"], hub).stdout.splitlines()
        if b.strip()
    ]
    for task_id in _mini_task_ids(completed_project["workgraph"]):
        hits = [b for b in branches if task_id in b]
        assert hits == [], f"미니 태스크 {task_id}에 branch가 만들어졌다: {hits}"


# --------------------------------------------------------------------------------------
# 4. 수용기준 8 — Fast 미니 태스크 상시 산출물은 packet·result·evidence뿐
# --------------------------------------------------------------------------------------

def test_fast_mini_task_artifacts_are_packet_result_evidence_only(completed_existing_opal):
    run_root = completed_existing_opal["run_root"]
    workgraph = completed_existing_opal["workgraph"]
    fast_tasks = [t for t in workgraph["tasks"] if t.get("profile") == "fast"]
    assert fast_tasks, "Fast profile 미니 태스크가 하나도 없어 수용기준 8을 관측할 수 없다"

    evidence_blob = "\n".join(
        p.read_text(encoding="utf-8") for p in (run_root / "evidence").rglob("*.json")
    )

    for task in fast_tasks:
        task_id = task["id"]
        task_dir = run_root / "attempts" / task_id
        assert task_dir.is_dir(), f"attempt 디렉토리가 없다: {task_dir}"

        produced = sorted(
            p.relative_to(task_dir).as_posix() for p in task_dir.rglob("*") if p.is_file()
        )
        names = {pathlib.PurePosixPath(p).name for p in produced}
        extra = names - ALLOWED_ATTEMPT_FILES
        assert extra == set(), (
            f"Fast 미니 태스크 {task_id}의 상시 산출물이 packet·result를 넘는다: {sorted(extra)}"
        )
        assert "execution-packet.json" in names, f"{task_id}에 execution-packet.json이 없다"
        assert "result.json" in names, f"{task_id}에 result.json이 없다"
        assert task_id in evidence_blob, f"{task_id}의 독립 evidence가 색인되지 않았다"


def test_forbidden_mini_task_documents_are_never_created(completed_existing_opal):
    """제안서 §7.3 — 미니 태스크별 TASK/DONE/ANALYSIS/PLAN/QA/CLOSE 문서를 만들지 않는다."""
    run_root = completed_existing_opal["run_root"]
    task_ids = _mini_task_ids(completed_existing_opal["workgraph"])

    offenders: list[str] = []
    for name in FORBIDDEN_MINI_TASK_DOCS:
        for hit in run_root.rglob(name):
            rel = hit.relative_to(run_root).as_posix()
            # 프로젝트 단위 DONE.md 1건은 P5 산출물로 허용된다 (pipeline p5.done_md).
            if name == "DONE.md" and rel == "DONE.md":
                continue
            offenders.append(rel)

    assert offenders == [], f"미니 태스크 문서가 생성됐다 (§7.3 위반): {offenders}"

    hub = completed_existing_opal["hub"]
    tracked = run_git(["ls-files"], hub).stdout.splitlines()
    tracked_offenders = [
        p for p in tracked
        if pathlib.PurePosixPath(p).name in FORBIDDEN_MINI_TASK_DOCS
        and any(task_id in p for task_id in task_ids)
    ]
    assert tracked_offenders == [], (
        f"미니 태스크 문서가 프로젝트 저장소에 커밋됐다: {tracked_offenders}"
    )


# --------------------------------------------------------------------------------------
# 5. 수용기준 11·12 — 완료 전 MEMORY·brain 반영 0, CLOSE 후 batch 정확히 1회
# --------------------------------------------------------------------------------------

def test_no_knowledge_write_before_p5(completed_existing_opal):
    """수용기준 11. MEMORY·brain은 P5 전까지 읽기 전용이다 (제안서 §5 P5)."""
    events = read_jsonl(completed_existing_opal["run_root"] / "events.jsonl")
    knowledge_events = [e for e in events if str(e.get("type", "")).startswith("knowledge.")]
    assert knowledge_events, "지식 반영 event가 전혀 없다 — 수용기준 12를 관측할 수 없다"

    early = [e for e in knowledge_events if e.get("stage") != "P5"]
    assert early == [], f"프로젝트 완료 전 MEMORY·brain 반영이 발생했다: {early}"


def test_knowledge_batch_runs_exactly_once_after_close(completed_existing_opal):
    """수용기준 12. 최종 허브 merge 후 MEMORY·brain batch가 정확히 1회다."""
    run_root = completed_existing_opal["run_root"]
    receipt = read_json(run_root / "knowledge-receipt.json")
    assert receipt.get("batch_count") == 1, (
        f"지식 batch가 정확히 1회가 아니다: batch_count={receipt.get('batch_count')!r}"
    )

    events = read_jsonl(run_root / "events.jsonl")
    batch_events = [e for e in events if e.get("type") == "knowledge.batch_applied"]
    assert len(batch_events) == 1, (
        f"knowledge.batch_applied event가 1건이 아니다: {len(batch_events)}건"
    )

    merge_events = [e for e in events if e.get("type") == "project.hub_merged"]
    assert merge_events, "허브 merge event가 없어 batch 시점을 판정할 수 없다"
    assert events.index(batch_events[0]) > events.index(merge_events[-1]), (
        "지식 batch가 최종 허브 merge보다 먼저 실행됐다 (수용기준 12)"
    )
