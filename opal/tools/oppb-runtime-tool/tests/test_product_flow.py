"""
@header {
  "module": "test_product_flow",
  "layer": "test",
  "domain": "opal-workspace",
  "description": "OPPB Product Flow RED-first 스위트 (TEST-SCENARIO S-17 / W-28, W-42에서 fixture 재작성). 관련 문서가 충분한 기존 OPAL 프로젝트 fixture와 greenfield fixture 각각에서 실제 실행 주체별 공개 CLI를 순서대로 호출해 P0~P2 산출물 seed → workgraph 적재 → `start`(P3~P4 무인 구간) → `checkpoint pre-finalize`까지 관측하고, 제안서 §13.2 수용기준 2·3·8을 기계 단언한다 — INTENT.md 단일 실행 계약, 프로젝트 worktree 1개·미니 태스크 worktree/branch 0개, Fast 미니 태스크 상시 산출물이 packet·result·evidence뿐(§7.3 6종 문서 0건). `oppb-runtime-tool project-run`이라는 서브명령은 존재하지 않는다 — 설계상 P0~P2·P5는 대화형 Claude 세션의 행동이고 P3~P4만 `start` 한 번으로 Supervisor가 무인 진행한다(제안서, PM 실측 확정). PLAN H-6에 따라 oppb-runtime-tool 내부 API를 import하지 않고 공개 CLI(run.sh 서브커맨드·JSON stdout)·//oppb 진입점 파일·run root 파일 계약 수준에서만 검증한다. PLAN이 이 스위트에 mock 금지를 명시했으므로 실제 git 저장소·실제 프로세스·실제 파일만 사용한다 — mini task의 run_command·verify_command도 실제 자식 프로세스이고, verify_command는 evidence.py의 실 스키마 검사(code_head·scope_hash·독립성)를 통과하는 evidence submit + task accept를 실제로 수행한다.",
  "migration_note": "W-42가 아래 4건을 W-34로 이관했다(대화형 Claude 세션의 행동을 관측해야 해서 pytest 원리적 검증이 불가능함 — fixture가 P0~P2 산출물을 손으로 seed하면 'PRD가 없다'는 결과가 항진명제가 된다): test_no_new_prd_or_trd_is_created(params: existing_opal/greenfield, AC-1), test_no_knowledge_write_before_p5(AC-11), test_knowledge_batch_runs_exactly_once_after_close(AC-12). 이관 목적지는 W-34 — G5 fixture 3종(existing_opal·greenfield·기타)을 cold 9회·warm 9회 실주행하며 대화형 세션의 관측 결과로 AC-1·AC-11·AC-12를 검증한다. 삭제가 아니라 검증 계층 이동이다: pytest 계층은 CLI·run root 파일 계약만 기계 검증하고, '무엇을 새로 만들지 않았는가'·'언제 지식을 반영했는가' 같은 세션 행동 판정은 G5 실주행 계층이 담당한다.",
  "exports": [
    "test_oppb_entry_point_files_exist",
    "test_pipeline_defines_p0_to_p5_twenty_two_rows",
    "test_pipeline_gates_only_at_declared_user_call_points",
    "test_pipeline_has_single_knowledge_batch_row_in_p5",
    "test_intent_md_is_the_single_execution_contract",
    "test_single_project_worktree_and_zero_mini_task_worktrees",
    "test_zero_mini_task_branches",
    "test_fast_mini_task_artifacts_are_packet_result_evidence_only",
    "test_forbidden_mini_task_documents_are_never_created"
  ],
  "depends": [
    "git CLI",
    "opal/tools/oppb-runtime-tool/run.sh",
    "opal/tools/oppb-runtime-tool/controller.py(W-41, workgraph load/mini_tasks/execution_contract/profile)",
    "opal/tools/oppb-runtime-tool/supervisor.py(W-8, start/status 무인 P3~P4)",
    "opal/tools/oppb-runtime-tool/checkpoint.py(W-14, checkpoint pre-finalize)",
    "opal/tools/oppb-runtime-tool/evidence.py(W-9, evidence submit/task accept)",
    "opal/skills/opal-pilot-project-build/SKILL.md(W-19)",
    "opal/skills/opal-pilot-project-build/references/pipeline.json(W-20)",
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

2. 공개 CLI — `opal/tools/oppb-runtime-tool/run.sh` (실 서브명령만 사용한다 — `project-run`은
   존재하지 않고 존재해서도 안 된다: P0~P2·P5는 대화형 Claude 세션의 행동이다)
   - `init --allocator-root <A> --project-root <P>`
     → stdout JSON `{"ok": true, "run_id": ..., "run_root": ..., "cache_root": ...}`
   - `workgraph load --run-root <R> --spec <S>` → workgraph.json·acceptance.json 최초 생성
   - `start --run-root <R>` → Supervisor 기동, P3(Runner)~P4(Verifier·acceptance)를 무인 진행
   - `status --run-root <R>` → 부작용 없는 관측 (mini_tasks[].state 포함)
   - `checkpoint pre-finalize --run-root <R> --project-root <P>` → `worktree-tool finalize` 전
     사전 검사(active lease 0·미처리 result 0·checkpoint 밖 dirty source 0·MEMORY/brain diff 0)
   - `evidence submit --run-root <R> --file <F>` / `task accept --run-root <R> --task-id <T>`
     → 독립 검증 증거 색인과 미니 태스크 accepted 전이(수용기준 9). 이 스위트는 이 두 CLI를
     mini task의 `verify_command`로 실제 호출해 Fast 미니 태스크의 evidence를 실제로 만든다.

3. run root 파일 계약
   - 입력 seed: `<run_root>/INTENT.md`
   - 산출(제안서 §7.1·§5):
     `<run_root>/workgraph.json`
     `<run_root>/attempts/<task_id>/<attempt_id>/execution-packet.json`
     `<run_root>/attempts/<task_id>/<attempt_id>/result.json`
     `<run_root>/evidence/<scope>/<evidence_id>.json`
     `<run_root>/events.jsonl`

`init`의 run root·cache root·`.git/info/exclude` 봉인 계약 자체는 W-10의
`test_oppb_init.py`(S-7)가 소유한다. 이 스위트는 `init`을 fixture 구성 수단으로만 쓰고
그 계약을 중복 단언하지 않는다. `gate-approvals.json`은 이 스위트의 fixture 범위에 없다 —
이 fixture가 도달하는 지점(`checkpoint pre-finalize`까지)에는 사용자 게이트(P1 user_gate·
P2 user_gate·P5 user_merge_gate)가 하나도 없고, P3·P4의 `pm_gate` 두 행은 Supervisor가
무인으로 통과시킨다. `p5.user_merge_gate`는 설계상 `--auto-pass`를 거부하므로(제안서 §11)
이 fixture는 애초에 P5까지 진행하지 않는다.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import time

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

# 제안서 §7.1 — Fast 미니 태스크 attempt 디렉토리의 "문서" 상시 산출물(SSOT 4종 중
# 파일시스템에 남는 2종). §7은 표제부터 "미니 태스크 문서"이고, §7.1/§7.2/§7.3이 규율하는
# 대상은 문서 계층(누적 산출물)이지 실행 중 부기(runtime bookkeeping)가 아니다.
_DOCUMENT_ATTEMPT_FILES = {"execution-packet.json", "result.json"}

# 아래 5종은 §7(미니 태스크 문서) 논의의 대상이 아니라 AC-11(비정상 종료 복구)이 요구하는
# 런타임 부기 파일이다 — W-47(소유자 승인 (a)안, PM 실측 확정)로 허용 집합에 편입한다.
# 이들을 없애면 AC-11이 소비하는 계약이 깨진다:
#   - "attempt-spec.json" / "attempt-runner.log" / "capability.out" / "capability.err"
#     → supervisor.py:50-53의 ATTEMPT_SPEC_NAME / ATTEMPT_RUNNER_LOG_NAME /
#       CAPABILITY_STDOUT_NAME / CAPABILITY_STDERR_NAME 상수가 그 파일명을 고정한다.
#   - "attempt.attempt.json" → supervisor.py:48의 ATTEMPT_RECORD_STEM = "attempt"(고정
#     문자열, task_id가 아니다)와 recovery.py:59의 동일 상수가 "<stem>.attempt.json"
#     규약으로 이 파일명을 만든다. supervisor.py:443의 reconcile-attempts 조율 루프가
#     `if result is None or not list(directory.glob("*.attempt.json")): continue`로
#     이 파일의 부재 자체를 orphan(고아) 판정 근거로 쓴다. opal-agent
#     (opal/tools/opal-agent/opal_agent.py, 예: `record_path = directory /
#     f"{stem}.attempt.json"`)도 같은 sink stem 규약을 소비한다.
# PLAN H-6에 따라 이 상수들의 값을 여기 하드코딩하고 내부 API는 import하지 않는다 — 상수가
# 어긋나면 아래 assert가 상수 목록이 아니라 생성된 파일명 자체로 실패를 드러낸다.
_RUNTIME_BOOKKEEPING_FILES = {
    "attempt-spec.json",  # supervisor.py:50 ATTEMPT_SPEC_NAME
    "attempt-runner.log",  # supervisor.py:51 ATTEMPT_RUNNER_LOG_NAME
    "capability.out",  # supervisor.py:52 CAPABILITY_STDOUT_NAME
    "capability.err",  # supervisor.py:53 CAPABILITY_STDERR_NAME
    "attempt.attempt.json",  # supervisor.py:48 ATTEMPT_RECORD_STEM="attempt" + ":443"
}

ALLOWED_ATTEMPT_FILES = _DOCUMENT_ATTEMPT_FILES | _RUNTIME_BOOKKEEPING_FILES

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

SUPERVISOR_WAIT_TIMEOUT_SEC = 60.0
POLL_INTERVAL_SEC = 0.2

# 미니 태스크 상태 어휘(controller.TASK_STATES) 중 종결 상태 — 여기서만 값을 복제한다
# (PLAN H-6, 내부 모듈 import 금지). 값이 어긋나면 wait_until이 timeout으로 그 사실을 드러낸다.
TERMINAL_TASK_STATES = ("accepted", "failed", "blocked")


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


def wait_until(predicate, timeout: float = SUPERVISOR_WAIT_TIMEOUT_SEC, label: str = ""):
    """조건 성립까지 폴링한다. 실패 시 마지막 관측값을 증거로 남긴다(실 프로세스이므로 sleep
    폴링이 mock을 대체하지 않는다 — PLAN mock 금지 제약)."""
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        last = predicate()
        if last:
            return last
        time.sleep(POLL_INTERVAL_SEC)
    pytest.fail(f"{label} 대기 시간 초과({timeout}s). 마지막 관측값={last!r}")


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


# --------------------------------------------------------------------------------------
# P2 산출물(workgraph spec)과 실행 주체 대역 — 실 프로세스, mock 없음
# --------------------------------------------------------------------------------------

FAST_TASK_ID = "mt-cancel-reason-code"
FULL_TASK_ID = "mt-cancel-reason-tests"

# `run.sh evidence submit` + `run.sh task accept`를 실제로 호출해 Fast 미니 태스크의
# 독립 검증 증거를 만드는 verify_command 대역 스크립트. Supervisor가 이 스크립트를
# ROLE_VERIFIER attempt로 실제 기동한다(내부 함수 import 없음 — 공개 CLI만 호출).
_VERIFY_SCRIPT_TEMPLATE = """
import json
import pathlib
import subprocess
import sys
import tempfile
import uuid

run_root, hub, task_id, run_sh = sys.argv[1:5]

code_head = subprocess.run(
    ["git", "-C", hub, "rev-parse", "HEAD"],
    capture_output=True, text=True, check=True,
).stdout.strip()

workgraph = json.loads((pathlib.Path(run_root) / "workgraph.json").read_text(encoding="utf-8"))
task = next(t for t in workgraph["mini_tasks"] if t["id"] == task_id)
scope_hash = task["scope_hash"]

evidence = {
    "schema_version": 1,
    "evidence_id": "ev-%s-%s" % (task_id, uuid.uuid4().hex[:8]),
    "scope": task_id,
    "code_head": code_head,
    "scope_hash": scope_hash,
    "verifier": {
        "kind": "integration_test",
        "attempt_id": "verify-%s-%s" % (task_id, uuid.uuid4().hex[:8]),
    },
    "result": "pass",
    "commands": [["/bin/sh", "-c", "true"]],
}

fd, tmp_path = tempfile.mkstemp(suffix=".json")
with open(fd, "w", encoding="utf-8") as handle:
    json.dump(evidence, handle, ensure_ascii=False)

try:
    submit = subprocess.run(
        ["bash", run_sh, "evidence", "submit", "--run-root", run_root, "--file", tmp_path],
        capture_output=True, text=True,
    )
    if submit.returncode != 0:
        sys.stderr.write("evidence submit 실패: %s\\n%s\\n" % (submit.stdout, submit.stderr))
        sys.exit(1)

    accept = subprocess.run(
        ["bash", run_sh, "task", "accept", "--run-root", run_root, "--task-id", task_id],
        capture_output=True, text=True,
    )
    if accept.returncode != 0:
        sys.stderr.write("task accept 실패: %s\\n%s\\n" % (accept.stdout, accept.stderr))
        sys.exit(1)
finally:
    pathlib.Path(tmp_path).unlink(missing_ok=True)

sys.exit(0)
"""


def _write_verify_script(tmp_root: pathlib.Path) -> pathlib.Path:
    path = tmp_root / "verify_task.py"
    path.write_text(_VERIFY_SCRIPT_TEMPLATE, encoding="utf-8")
    return path


def _write_spec(
    tmp_root: pathlib.Path,
    verify_script: pathlib.Path,
    run_root: pathlib.Path,
    hub: pathlib.Path,
) -> pathlib.Path:
    """`run.sh workgraph load --spec`가 소비하는 공개 fixture 계약(controller.py 소유,
    workgraph.json은 직접 쓰지 않는다). Fast 미니 태스크 1개(verify_command로 실제 evidence
    round-trip) + Full 미니 태스크 1개(즉시 accepted 경로)로 구성한다.

    `init`이 이미 끝난 뒤에 spec을 쓰므로 run_root·hub는 이 시점에 이미 확정돼 있다 —
    workgraph.json은 controller.py의 유일한 writer라 load 재호출로 고칠 수 없으므로,
    placeholder를 남겨 두고 나중에 고치는 방식은 쓰지 않는다."""
    spec = {
        "execution_contract": "INTENT.md",
        "budget": {
            "max_active_runners": 2,
            "max_active_executors": 2,
            "max_total_agent_processes": 4,
        },
        "mini_tasks": [
            {
                "id": FAST_TASK_ID,
                "capability": "cap.orders.cancel_reason_code",
                "profile": "fast",
                "lease": {"tracked_writes": ["src/orders.py"]},
                "run_command": ["/bin/sh", "-c", ": run %s; sleep 0.05" % FAST_TASK_ID],
                "verify_command": [
                    sys.executable, str(verify_script), str(run_root), str(hub), FAST_TASK_ID, str(RUN_SH),
                ],
            },
            {
                "id": FULL_TASK_ID,
                "capability": "cap.orders.cancel_reason_code_tests",
                "profile": "standard",
                "depends_on": [FAST_TASK_ID],
                "lease": {"tracked_writes": ["tests/test_orders.py"]},
                "run_command": ["/bin/sh", "-c", ": run %s; sleep 0.05" % FULL_TASK_ID],
            },
        ],
    }
    path = tmp_root / "spec.json"
    path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _completed_run(tmp_root: pathlib.Path, kind: str) -> dict:
    """fixture 저장소에서 실행 주체별 실제 공개 CLI를 순서대로 호출한다:
    `init` → P0~P2 산출물 seed(INTENT.md·workgraph spec) → `workgraph load` →
    `start`(P3~P4 무인 구간, Supervisor headless) → `checkpoint pre-finalize`.

    `project-run`이라는 서브명령은 존재하지 않는다 — P0~P2·P5는 대화형 Claude 세션의
    행동이라 무인 완주 대상이 아니고(제안서), 이 fixture는 P3~P4 무인 구간만 실제로
    완주시킨 뒤 P5 진입 직전(pre-finalize)에서 관측을 멈춘다.
    """
    fixture = _build_hub_and_project(tmp_root, kind)
    hub = fixture["hub"]

    # 1) init
    init_res = run_oppb_cli(
        ["init", "--allocator-root", str(hub), "--project-root", str(hub)]
    )
    assert init_res.get("ok") is True, f"init 실패: {init_res}"
    run_root = pathlib.Path(init_res["run_root"])

    # 2) P0~P2 산출물 seed — INTENT.md(P1)와 workgraph spec(P2)을 손으로 준비한다.
    #    이 부분은 대화형 Claude 세션이 실제로 만드는 문서이므로, fixture는 그 결과물의
    #    형태만 대신 채운다(대화 자체는 관측 불가 — 그 판정은 W-34가 담당).
    (run_root / "INTENT.md").write_text(INTENT_SEED, encoding="utf-8")

    verify_script = _write_verify_script(tmp_root)
    spec_path = _write_spec(tmp_root, verify_script, run_root, hub)

    # 3) workgraph 적재 — Controller Tool이 유일한 workgraph.json writer다(§4.5).
    load_res = run_oppb_cli(
        ["workgraph", "load", "--run-root", str(run_root), "--spec", str(spec_path)]
    )
    assert load_res.get("ok") is True, f"workgraph load 실패: {load_res}"

    # 4) start — Supervisor 기동, P3(Runner)~P4(Verifier·acceptance) 무인 진행.
    start_res = run_oppb_cli(["start", "--run-root", str(run_root)])
    assert start_res.get("ok") is True, f"start 실패: {start_res}"

    def _mini_task_states() -> dict | None:
        snapshot = run_oppb_cli(["status", "--run-root", str(run_root)])
        states = {t["id"]: t["state"] for t in snapshot.get("mini_tasks", [])}
        if states and all(state in TERMINAL_TASK_STATES for state in states.values()):
            return states
        return None

    final_states = wait_until(
        _mini_task_states, label="P3~P4 무인 구간 완주(모든 미니 태스크 종결 상태)"
    )
    assert final_states.get(FAST_TASK_ID) == "accepted", (
        f"Fast 미니 태스크가 accepted에 도달하지 못함: {final_states}"
    )
    assert final_states.get(FULL_TASK_ID) == "accepted", (
        f"Full 미니 태스크가 accepted에 도달하지 못함: {final_states}"
    )

    # 5) checkpoint pre-finalize — `worktree-tool finalize` 호출 전 사전 검사를 실제로
    #    통과하는지 단언한다. `worktree-tool finalize` 자체는 호출하지 않는다.
    #    이 fixture는 P5(user_merge_gate 이후)로 진행하지 않는다 — p5.user_merge_gate는
    #    --auto-pass를 거부하므로(제안서 §11) 무인 fixture가 도달할 수 없는 지점이다.
    #
    #    checkpoint.py:_unprocessed_results는 W-43이 이미 동결 스키마의 `mini_tasks`를
    #    읽도록 고쳤다(과거에는 `document.get("tasks")`를 읽어 모든 미니 태스크를 항상
    #    비종결로 오판했다). accepted로 끝난 이 fixture에서는 미처리 result·활성
    #    lease·checkpoint 밖 dirty source·MEMORY/brain diff가 모두 0이어야 하므로
    #    pre-finalize가 실제로 finalize_allowed=true를 반환함을 단언한다.
    pre_finalize_result = subprocess.run(
        ["bash", str(RUN_SH), "checkpoint", "pre-finalize",
         "--run-root", str(run_root), "--project-root", str(hub)],
        capture_output=True, text=True, timeout=60,
    )
    try:
        pre_finalize_res = json.loads(pre_finalize_result.stdout)
    except json.JSONDecodeError:
        pre_finalize_res = {
            "ok": False,
            "stdout": pre_finalize_result.stdout,
            "stderr": pre_finalize_result.stderr,
        }
    assert pre_finalize_res.get("ok") is True and pre_finalize_res.get("finalize_allowed") is True, (
        f"checkpoint pre-finalize가 accepted 완주 후에도 통과하지 못함: {pre_finalize_res}"
    )

    fixture["run_root"] = run_root
    fixture["pre_finalize"] = pre_finalize_res
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
    tasks = workgraph.get("mini_tasks")
    assert isinstance(tasks, list) and tasks, (
        "workgraph.json이 미니 태스크 record를 담지 않았다 (동결 스키마 최상위 키는 "
        "mini_tasks다 — tasks가 아니다)"
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
# 2. 수용기준 2 — INTENT.md 단일 실행 계약
# --------------------------------------------------------------------------------------
#
# 수용기준 1(PRD·TRD 신규 생성 0건)은 대화형 Claude 세션의 행동 관측이 필요해
# W-34(G5 fixture 3종 cold 9회·warm 9회 실주행)로 이관됐다 — 이 파일은 더 이상
# 검증하지 않는다.


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
    """수용기준 8 — Fast 미니 태스크의 attempt 디렉토리에 §7.2 조건부 문서(DESIGN.md·
    TEST-SCENARIO.md 등)와 §7.3 금지 문서가 생기지 않는다.

    W-47 판정 근거(소유자 승인): 실측 결과 이 테스트는 원래 AC-11(비정상 종료 복구)이
    요구하는 런타임 부기 파일 5종(attempt-spec.json·attempt-runner.log·
    attempt.attempt.json·capability.out·capability.err — supervisor.py:50-53의
    ATTEMPT_SPEC_NAME/ATTEMPT_RUNNER_LOG_NAME/CAPABILITY_STDOUT_NAME/
    CAPABILITY_STDERR_NAME, supervisor.py:48의 ATTEMPT_RECORD_STEM="attempt")까지
    위반으로 판정해 AC-11을 깨고 있었다. supervisor.py:443의 reconcile-attempts
    조율 루프는 `*.attempt.json`의 부재 자체를 orphan 판정 근거로 쓰므로, 이 파일들을
    없애면 비정상 종료 복구가 무너진다. 제안서 §7은 표제부터 "미니 태스크 문서"이고
    §7.1(상시 문서)/§7.2(조건부 문서)/§7.3(금지 문서)이 규율하는 대상은 문서 계층뿐이다
    — 런타임 부기는 이 절의 논의 대상이 아니다. 그래서 AC-8은 "attempt 디렉토리에 다른
    파일이 하나도 없어야 한다"가 아니라 "§7.2 조건부 문서를 만들지 않는다"로 읽어야
    한다. 이 판정에 따라 허용 집합을 런타임 부기 파일까지 넓히되(ALLOWED_ATTEMPT_FILES),
    단언의 이빨은 그대로 유지한다: 목록 밖 예기치 않은 파일은 여전히 실패해야 하고,
    `.md` 문서(§7.2/§7.3 대상)는 attempt 디렉토리에 0건이어야 한다.
    """
    run_root = completed_existing_opal["run_root"]
    workgraph = completed_existing_opal["workgraph"]
    fast_tasks = [t for t in workgraph["mini_tasks"] if t.get("profile") == "fast"]
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

        # §7.2 조건부 문서(DESIGN.md·TEST-SCENARIO.md 등)·§7.3 금지 문서는 문서
        # 계층이므로 Fast attempt 디렉토리에 `.md`가 0건이어야 한다 — 확장된
        # ALLOWED_ATTEMPT_FILES가 런타임 부기 파일을 흡수하더라도 이 단언은 무뎌지지
        # 않는다(§7.2/§7.3 문서를 넣으면 여전히 실패한다).
        md_docs = sorted(n for n in names if n.endswith(".md"))
        assert md_docs == [], (
            f"Fast 미니 태스크 {task_id}의 attempt 디렉토리에 §7.2/§7.3 문서가 생겼다: "
            f"{md_docs}"
        )

        # 허용 집합 밖의 예기치 않은 파일(문서든 부기든)은 여전히 실패해야 한다 — 허용
        # 확장이 "무조건 통과"로 퇴화하지 않도록 하는 게이트.
        extra = names - ALLOWED_ATTEMPT_FILES
        assert extra == set(), (
            f"Fast 미니 태스크 {task_id}의 상시 산출물이 허용 목록을 넘는다: {sorted(extra)}"
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
            # 프로젝트 단위 DONE.md 1건은 P5 산출물로 허용된다(pipeline p5.done_md) — 이
            # fixture는 P5까지 진행하지 않으므로 실제로는 나타나지 않아야 정상이다.
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
