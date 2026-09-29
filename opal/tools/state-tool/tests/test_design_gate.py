"""
@header {
  "module": "test_design_gate",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "PM 설계 경로(pipeline-pm.json)와 state-tool 독립 설계 게이트(design-gate start/record/reset, design-decision)의 공개 CLI 계약 — init_args 파이프라인 판정, 결정론 검사, 문서 묶음 해시·확인 해시, rewrite 대상, 반복 상한·reset, EXECUTE 진입 가드, run-log gate 사건, ADD-1 evaluator 결과 stale 거부(input_bundle_hash·iteration 일치 검사, verdict pass/rewrite 전용), ADD-2 design-decision detail/external의 run-log activity 사건 data 형식(계약: {\"kind\": \"decision\"} 객체) 위반으로 인한 drain 정지·pending_events 적체 회귀(RED, 미수정), ADD-3 Findings 백틱 코드 토큰(확장자 없는 os.replace/json.loads 등)이 경로로 오판되어 발생하는 regression/finding 오탐 회귀(RED, 미수정).",
  "exports": [],
  "depends": ["state_tool"]
}
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
STATE_TOOL = REPO_ROOT / "opal" / "tools" / "state-tool" / "state_tool.py"
REFS_DIR = REPO_ROOT / "opal" / "skills" / "opal-pilot-dev" / "references"
PIPELINE_PM_JSON = REFS_DIR / "pipeline-pm.json"

PM_ROWS_EXPECTED = [
    "task.task_md",
    "task.user_confirm",
    "plan.plan_md",
    "plan.test_scenario_md",
    "plan.design_gate",
    "plan.user_confirm",
]

TASK_MD_SDLC_V2 = """---
template: sdlc-v2
---
# TASK: 픽스처

## Problem

예시 문제 상황.

## Proposed outcome

예시 목표 결과.

## Affected users and systems

예시 영향 대상.

## Constraints

- C-1. 예시 제약

## Acceptance criteria

- AC-1. 예시 기준 1
- AC-2. 예시 기준 2
- AC-3. 예시 기준 3
"""

PLAN_MD_TEMPLATE = """---
template: sdlc-v2
---
# PLAN: 픽스처

## Findings

### 직접 변경

- `pkg/mod.py`

### 회귀 확인

- `pkg/mod_test.py`

### 문서 갱신

- `pkg/mod.py`

### 미확인 가정

없음.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| DEC-1 예시 | 예시 계약 | 예시 근거 |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. 예시 작업 | opal-task-agent | `pkg/mod.py` | 예시 구현 | 없음 | P1 | {plan_refs} |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. 예시 위험 | 예시 동작 | 예시 영향 | 예시 대응 |

## Release and recovery

- 적용 순서: 예시.
"""

TEST_SCENARIO_MD_TEMPLATE = """---
template: sdlc-v2
---
# TEST-SCENARIO: 픽스처

## Setup

- 환경: 예시.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | {scenario_refs} | 예시 조건 | 예시 행동 | 예시 기대 | unit | 구현 전 RED |
"""

EVALUATOR_PASS_JSON = {
    "design": {
        "axes": {
            "completeness": "PASS",
            "decision_clarity": "PASS",
            "executability": "PASS",
            "recoverability": "PASS",
        },
        "gaps": [],
    },
    "scenario": {
        "scores": {"goal": 2, "adoption": 2, "boundary": 2},
        "average": 2.0,
        "gaps": [],
    },
    "verdict": "pass",
    "rewrite_target": None,
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class DesignGateCliContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    # -- CLI helpers ---------------------------------------------------
    def _run(self, *args: str) -> tuple[subprocess.CompletedProcess[str], dict | None]:
        completed = subprocess.run(
            [sys.executable, str(STATE_TOOL), *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        try:
            payload = json.loads(completed.stdout)
        except (json.JSONDecodeError, TypeError):
            payload = None
        return completed, payload

    def _assert_ok(self, result) -> dict:
        completed, payload = result
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertIsInstance(payload, dict, completed.stdout)
        self.assertTrue(payload.get("ok"), payload)
        return payload

    def _assert_err(self, result, code: str) -> dict:
        completed, payload = result
        self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
        self.assertIsInstance(payload, dict, completed.stdout)
        self.assertFalse(payload.get("ok"), payload)
        self.assertEqual(payload.get("error"), code, payload)
        return payload

    # -- fixture helpers -------------------------------------------------
    def _write_pm_docs(
        self,
        task: Path,
        *,
        plan_refs: str = "AC-1, AC-2, AC-3, C-1",
        scenario_refs: str = "AC-1, AC-2, AC-3, C-1, H-1",
        plan_overrides: dict | None = None,
    ) -> None:
        task.mkdir(parents=True, exist_ok=True)
        (task / "TASK.md").write_text(TASK_MD_SDLC_V2, encoding="utf-8")
        plan_text = PLAN_MD_TEMPLATE.format(plan_refs=plan_refs)
        (task / "PLAN.md").write_text(plan_text, encoding="utf-8")
        (task / "TEST-SCENARIO.md").write_text(
            TEST_SCENARIO_MD_TEMPLATE.format(scenario_refs=scenario_refs), encoding="utf-8"
        )

    def _make_pm_task(
        self,
        name: str,
        *,
        plan_refs: str = "AC-1, AC-2, AC-3, C-1",
        scenario_refs: str = "AC-1, AC-2, AC-3, C-1, H-1",
        mode: str | None = None,
    ) -> Path:
        """PM 경로(pipeline-pm.json)로 init하고 plan.test_scenario_md까지 done으로 진행한다.

        pipeline-pm.json이 아직 없으므로(DEC-2 미구현) 이 헬퍼 자체가 RED다.
        mode: None(기본 agentic) 또는 "semi-agentic"/"agentic"(명시 플래그).
        """
        task = self.root / name
        self._write_pm_docs(task, plan_refs=plan_refs, scenario_refs=scenario_refs)
        resolve_args = ["resolve-start", str(task), "--skill", "opd", "--new-task"]
        if mode == "semi-agentic":
            resolve_args.append("--semi-agentic")
        elif mode == "agentic":
            resolve_args.append("--agentic")
        resolved = self._assert_ok(self._run(*resolve_args))
        init_args = list(resolved.get("init_args") or [])
        self.assertIn("--rows-from", init_args, resolved)
        completed, payload = self._run("init", str(task), *init_args, "--worktree", str(task))
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        state = json.loads((task / "state.json").read_text(encoding="utf-8"))
        keys = [row.get("key") for row in state.get("rows", []) if row.get("stage") != "EXECUTE"]
        self.assertEqual(keys[: len(PM_ROWS_EXPECTED)], PM_ROWS_EXPECTED, state)

        for key in ("task.task_md", "task.user_confirm", "plan.plan_md", "plan.test_scenario_md"):
            args = ["mark", str(task), "--task-step", key, "--done"]
            if key in ("plan.plan_md", "plan.test_scenario_md"):
                args.append("--worker-duration-unknown")
            if key == "task.user_confirm" and mode == "semi-agentic":
                args += ["--owner", "user"]
            completed, payload = self._run(*args)
            self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        return task

    def _record(
        self,
        task: Path,
        iteration: int,
        *,
        verdict: str,
        evaluator: dict | None = None,
        rewrite_target: str | None = None,
        input_bundle_hash: str | None = "auto",
        stale_iteration: int | None = None,
    ):
        """ADD-1: 기본(input_bundle_hash="auto")은 현재 열린 시도의 bundle_hash·iteration을
        evaluator 결과에 그대로 채워 기존 테스트 흐름의 판정 의미를 바꾸지 않는다.
        stale 시나리오 전용으로 input_bundle_hash=None(필드 생략) 또는 명시 문자열,
        stale_iteration으로 회차 불일치를 만들 수 있다.
        """
        payload = json.loads(json.dumps(evaluator or EVALUATOR_PASS_JSON, ensure_ascii=False))
        if input_bundle_hash == "auto":
            state = json.loads((task / "state.json").read_text(encoding="utf-8"))
            attempt = (state.get("design_gate") or {}).get("current_attempt") or {}
            payload["input_bundle_hash"] = attempt.get("bundle_hash")
            payload["iteration"] = (
                stale_iteration if stale_iteration is not None else attempt.get("iteration")
            )
        elif input_bundle_hash is None:
            payload.pop("input_bundle_hash", None)
            if stale_iteration is not None:
                payload["iteration"] = stale_iteration
        else:
            payload["input_bundle_hash"] = input_bundle_hash
            payload["iteration"] = stale_iteration if stale_iteration is not None else iteration
        eval_path = task / f"evaluator-result-i{iteration}.json"
        eval_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        args = [
            "design-gate", "record", str(task),
            "--iteration", str(iteration),
            "--verdict", verdict,
            "--evaluator-result", str(eval_path),
        ]
        if rewrite_target:
            args += ["--rewrite-target", rewrite_target]
        return self._run(*args)

    # ------------------------------------------------------------------
    # S-1 — resolve-start init_args, PM 경로 행 구성 (DEC-1, DEC-2, C-1, H-1)
    # ------------------------------------------------------------------

    def test_s1_new_task_rows_from_init_args(self):
        for skill, expect_file in (("opd", "pipeline-pm.json"), ("opds", "pipeline-pm.json")):
            with self.subTest(skill=skill):
                task = self.root / f"s1-{skill}-pm"
                resolved = self._assert_ok(
                    self._run("resolve-start", str(task), "--skill", skill, "--new-task")
                )
                init_args = list(resolved.get("init_args") or [])
                self.assertIn("--rows-from", init_args, resolved)
                rows_from = init_args[init_args.index("--rows-from") + 1]
                self.assertTrue(Path(rows_from).is_absolute(), resolved)
                self.assertTrue(Path(rows_from).exists(), resolved)
                self.assertEqual(Path(rows_from).name, expect_file, resolved)

    def test_s1_no_pm_uses_worker_pipeline(self):
        for skill, expect_file in (("opd", "pipeline.json"), ("opds", "pipeline-short.json")):
            with self.subTest(skill=skill):
                task = self.root / f"s1-{skill}-no-pm"
                resolved = self._assert_ok(
                    self._run("resolve-start", str(task), "--skill", skill, "--new-task", "--no-pm")
                )
                init_args = list(resolved.get("init_args") or [])
                self.assertIn("--rows-from", init_args, resolved)
                rows_from = init_args[init_args.index("--rows-from") + 1]
                self.assertEqual(Path(rows_from).name, expect_file, resolved)

    def test_s1_opp_unchanged(self):
        task = self.root / "s1-opp"
        resolved = self._assert_ok(
            self._run("resolve-start", str(task), "--skill", "opp", "--new-task")
        )
        init_args = list(resolved.get("init_args") or [])
        self.assertNotIn("--rows-from", init_args, resolved)

    def test_s1_resume_no_init_args(self):
        task = self.root / "s1-resume"
        resolved = self._assert_ok(
            self._run("resolve-start", str(task), "--skill", "opd", "--new-task")
        )
        init_args = list(resolved.get("init_args") or [])
        completed, _ = self._run("init", str(task), *init_args, "--worktree", str(task))
        self.assertEqual(completed.returncode, 0, completed.stderr)
        resumed = self._assert_ok(self._run("resolve-start", str(task), "--skill", "opd"))
        self.assertNotIn("init_args", resumed, resumed)

    def test_s1_pm_row_keys_order(self):
        task = self.root / "s1-rows"
        resolved = self._assert_ok(
            self._run("resolve-start", str(task), "--skill", "opd", "--new-task")
        )
        init_args = list(resolved.get("init_args") or [])
        completed, _ = self._run("init", str(task), *init_args, "--worktree", str(task))
        self.assertEqual(completed.returncode, 0, completed.stderr)
        state = json.loads((task / "state.json").read_text(encoding="utf-8"))
        keys = [row.get("key") for row in state.get("rows", []) if row.get("stage") != "EXECUTE"]
        self.assertEqual(keys[: len(PM_ROWS_EXPECTED)], PM_ROWS_EXPECTED, state)

    # ------------------------------------------------------------------
    # S-2 — coverage 결정론 실패 (DEC-7, DEC-8 ②)
    # ------------------------------------------------------------------

    def test_s2_uncovered_requirement_blocks_start(self):
        task = self._make_pm_task("s2", plan_refs="AC-1, AC-2, C-1")
        # TEST-SCENARIO.md에는 AC-3까지 연결되지만 PLAN Work items에는 AC-1·AC-2·C-1만 연결
        (task / "TEST-SCENARIO.md").write_text(
            TEST_SCENARIO_MD_TEMPLATE.format(scenario_refs="AC-1, AC-2, AC-3, C-1, H-1"),
            encoding="utf-8",
        )
        result = self._assert_err(
            self._run("design-gate", "start", str(task), "--iteration", "1"),
            "design_gate_deterministic_fail",
        )
        missing = result.get("missing") or []
        self.assertTrue(any("uncovered requirement AC-3" in str(m) for m in missing), result)

        state = json.loads((task / "state.json").read_text(encoding="utf-8"))
        history = state.get("design_gate", {}).get("history", [])
        self.assertEqual(len(history), 1, state)
        self.assertEqual(history[0].get("verdict"), "deterministic_fail", state)

        verify_completed, verify_payload = self._run(
            "verify", str(task), "--plan-contract-check"
        )
        self.assertEqual(verify_completed.returncode, 0, verify_completed.stderr)

    # ------------------------------------------------------------------
    # S-3 — Findings 4소절 결정론 검사 (DEC-8 ③~⑥)
    # ------------------------------------------------------------------

    def _plan_variant(self, task: Path, mutate) -> None:
        plan_text = PLAN_MD_TEMPLATE.format(plan_refs="AC-1, AC-2, AC-3, C-1")
        (task / "PLAN.md").write_text(mutate(plan_text), encoding="utf-8")

    def test_s3_missing_section_removed(self):
        task = self._make_pm_task("s3-1")
        self._plan_variant(task, lambda t: t.replace(
            "### 회귀 확인\n\n- `pkg/mod_test.py`\n\n", ""
        ))
        result = self._assert_err(
            self._run("design-gate", "start", str(task), "--iteration", "1"),
            "design_gate_deterministic_fail",
        )
        missing = " ".join(str(m) for m in (result.get("missing") or []))
        self.assertIn("회귀 확인", missing, result)

    def test_s3_regression_target_listed_as_change(self):
        task = self._make_pm_task("s3-2")
        self._plan_variant(task, lambda t: t.replace(
            "### 직접 변경\n\n- `pkg/mod.py`\n",
            "### 직접 변경\n\n- `pkg/mod.py`\n- `pkg/mod_test.py`\n",
        ))
        result = self._assert_err(
            self._run("design-gate", "start", str(task), "--iteration", "1"),
            "design_gate_deterministic_fail",
        )
        missing = " ".join(str(m) for m in (result.get("missing") or []))
        self.assertIn("regression target listed as change", missing, result)

    def test_s3_finding_not_in_work_items(self):
        task = self._make_pm_task("s3-3")
        self._plan_variant(task, lambda t: t.replace(
            "### 직접 변경\n\n- `pkg/mod.py`\n",
            "### 직접 변경\n\n- `pkg/other.py`\n",
        ))
        result = self._assert_err(
            self._run("design-gate", "start", str(task), "--iteration", "1"),
            "design_gate_deterministic_fail",
        )
        missing = " ".join(str(m) for m in (result.get("missing") or []))
        self.assertIn("finding not in work items", missing, result)

    def test_s3_unconfirmed_assumption_bad_reference(self):
        task = self._make_pm_task("s3-4")
        self._plan_variant(task, lambda t: t.replace(
            "### 미확인 가정\n\n없음.\n",
            "### 미확인 가정\n\nH-9 참조.\n",
        ))
        result = self._assert_err(
            self._run("design-gate", "start", str(task), "--iteration", "1"),
            "design_gate_deterministic_fail",
        )
        self.assertTrue(result.get("missing"), result)

    def test_s3_normal_plan_passes(self):
        task = self._make_pm_task("s3-ok")
        result = self._assert_ok(
            self._run("design-gate", "start", str(task), "--iteration", "1")
        )
        self.assertEqual(result.get("status"), "evaluating", result)

    def test_add3_findings_code_token_not_treated_as_path(self):
        # (a) 확장자 없는 백틱 코드 토큰(os.replace, json.loads)은 경로가 아니므로
        # 정상 PM 경로 픽스처에 설명 문구로 추가해도 결정론 검사를 통과해야 한다.
        task = self._make_pm_task("add3-ok")
        self._plan_variant(task, lambda t: t.replace(
            "### 직접 변경\n\n- `pkg/mod.py`\n",
            "### 직접 변경\n\n- `pkg/mod.py` (`os.replace`로 원자적 교체)\n",
        ).replace(
            "### 회귀 확인\n\n- `pkg/mod_test.py`\n",
            "### 회귀 확인\n\n- `pkg/mod_test.py` (`json.loads` 파싱 결과 검증)\n",
        ))
        result = self._assert_ok(
            self._run("design-gate", "start", str(task), "--iteration", "1")
        )
        self.assertEqual(result.get("status"), "evaluating", result)

        # (b) 회귀 확인에 Work item 변경 대상과 같은 경로(pkg/mod.py)를 넣으면
        # 기존 판정(regression target listed as change)이 유지되어야 한다.
        task_b = self._make_pm_task("add3-regression")
        self._plan_variant(task_b, lambda t: t.replace(
            "### 회귀 확인\n\n- `pkg/mod_test.py`\n",
            "### 회귀 확인\n\n- `pkg/mod_test.py`\n- `pkg/mod.py`\n",
        ))
        result_b = self._assert_err(
            self._run("design-gate", "start", str(task_b), "--iteration", "1"),
            "design_gate_deterministic_fail",
        )
        missing_b = " ".join(str(m) for m in (result_b.get("missing") or []))
        self.assertIn("regression target listed as change", missing_b, result_b)

        # (c) 직접 변경에 슬래시 없는 파일명(README.md, Work item 변경 대상에 없음)을
        # 넣으면 기존 판정(finding not in work items)이 유지되어야 한다.
        task_c = self._make_pm_task("add3-not-in-work-items")
        self._plan_variant(task_c, lambda t: t.replace(
            "### 직접 변경\n\n- `pkg/mod.py`\n",
            "### 직접 변경\n\n- `pkg/mod.py`\n- `README.md`\n",
        ))
        result_c = self._assert_err(
            self._run("design-gate", "start", str(task_c), "--iteration", "1"),
            "design_gate_deterministic_fail",
        )
        missing_c = " ".join(str(m) for m in (result_c.get("missing") or []))
        self.assertIn("finding not in work items", missing_c, result_c)

    # ------------------------------------------------------------------
    # S-5 — rewrite 대상 판정 (DEC-7 ⑥, DEC-9)
    # ------------------------------------------------------------------

    def test_s5_rewrite_flow(self):
        task = self._make_pm_task("s5")
        self._assert_ok(self._run("design-gate", "start", str(task), "--iteration", "1"))

        # ① --rewrite-target 없이 record --verdict rewrite → design_gate_result_invalid
        self._assert_err(
            self._record(task, 1, verdict="rewrite"),
            "design_gate_result_invalid",
        )

        # ② --rewrite-target plan 지정 기록
        self._assert_ok(self._record(task, 1, verdict="rewrite", rewrite_target="plan"))

        # ③ PLAN 불변 상태로 start i2 → rewrite_target_unchanged
        before_sha = _sha256(task / "state.json")
        self._assert_err(
            self._run("design-gate", "start", str(task), "--iteration", "2"),
            "rewrite_target_unchanged",
        )
        after_sha = _sha256(task / "state.json")
        self.assertEqual(before_sha, after_sha)

        # ④ PLAN 수정하되 TEST-SCENARIO에서 AC-1 연결 제거 후 start i2
        self._plan_variant(task, lambda t: t + "\n<!-- rewrite -->\n")
        (task / "TEST-SCENARIO.md").write_text(
            TEST_SCENARIO_MD_TEMPLATE.format(scenario_refs="AC-2, AC-3, C-1, H-1"),
            encoding="utf-8",
        )
        result = self._assert_err(
            self._run("design-gate", "start", str(task), "--iteration", "2"),
            "design_gate_deterministic_fail",
        )
        missing = " ".join(str(m) for m in (result.get("missing") or []))
        self.assertIn("AC-1", missing, result)
        state = json.loads((task / "state.json").read_text(encoding="utf-8"))
        history = state.get("design_gate", {}).get("history", [])
        self.assertEqual(len(history), 2, state)

        # ⑤ 연결 복구 후 start i3 → 성공
        (task / "TEST-SCENARIO.md").write_text(
            TEST_SCENARIO_MD_TEMPLATE.format(scenario_refs="AC-1, AC-2, AC-3, C-1, H-1"),
            encoding="utf-8",
        )
        result = self._assert_ok(
            self._run("design-gate", "start", str(task), "--iteration", "3")
        )
        self.assertEqual(result.get("status"), "evaluating", result)
        state = json.loads((task / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(
            state.get("design_gate", {}).get("current_attempt", {}).get("iteration"), 3, state
        )

    # ------------------------------------------------------------------
    # S-6 — 문서 묶음 hash·재확인 (DEC-6, DEC-7, DEC-11, H-2)
    # ------------------------------------------------------------------

    def test_s6_semi_agentic_reconfirm_flow(self):
        task = self._make_pm_task("s6-semi", mode="semi-agentic")
        self._assert_ok(self._run("design-gate", "start", str(task), "--iteration", "1"))

        # ① start 후 PLAN 수정, record pass → design_gate_input_changed, state 불변
        before_sha = _sha256(task / "state.json")
        self._plan_variant(task, lambda t: t + "\n<!-- edit -->\n")
        self._assert_err(
            self._record(task, 1, verdict="pass"),
            "design_gate_input_changed",
        )
        after_sha = _sha256(task / "state.json")
        self.assertEqual(before_sha, after_sha)

        # ② 재start → pass 기록 → mark plan.design_gate → mark plan.user_confirm --owner user
        # → PLAN 한 줄 수정 → advance execute.implement (재승인 없음 → 거부, --force --note도 거부)
        self._assert_ok(self._run("design-gate", "start", str(task), "--iteration", "2"))
        self._assert_ok(self._record(task, 2, verdict="pass"))
        self._assert_ok(self._run("mark", str(task), "--task-step", "plan.design_gate", "--done"))
        self._assert_ok(
            self._run("mark", str(task), "--task-step", "plan.user_confirm", "--done", "--owner", "user")
        )
        self._plan_variant(task, lambda t: t + "\n<!-- edit2 -->\n")
        before_sha2 = _sha256(task / "state.json")
        completed, payload = self._run("advance", str(task), "--task-step", "execute.implement")
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertEqual(payload.get("error"), "design_bundle_mismatch", payload)
        completed, payload = self._run(
            "advance", str(task), "--task-step", "execute.implement", "--force", "--note", "x"
        )
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertEqual(payload.get("error"), "design_bundle_mismatch", payload)
        after_sha2 = _sha256(task / "state.json")
        self.assertEqual(before_sha2, after_sha2)

        # ③ 다시 start → plan.user_confirm이 pending으로 되돌아감 → pass 기록 →
        # (재승인 없이) advance execute.implement → semi-agentic은 user_confirmation_required
        self._assert_ok(self._run("design-gate", "start", str(task), "--iteration", "3"))
        state = json.loads((task / "state.json").read_text(encoding="utf-8"))
        rows = {row.get("key"): row for row in state.get("rows", [])}
        self.assertEqual(rows.get("plan.user_confirm", {}).get("status"), "pending", state)
        self._assert_ok(self._record(task, 3, verdict="pass"))
        self._assert_err(
            self._run("advance", str(task), "--task-step", "execute.implement"),
            "user_confirmation_required",
        )

        # ④ 정상 승인(재확인 mark) 후 TASK AC 문장 수정 → advance/start 모두 task_reconfirm_required
        # (--force --note도 거부)
        self._assert_ok(
            self._run("mark", str(task), "--task-step", "plan.user_confirm", "--done", "--owner", "user")
        )
        (task / "TASK.md").write_text(
            TASK_MD_SDLC_V2.replace("AC-1. 예시 기준 1", "AC-1. 변경된 기준 1"),
            encoding="utf-8",
        )
        self._assert_err(
            self._run("advance", str(task), "--task-step", "execute.implement"),
            "task_reconfirm_required",
        )
        completed, payload = self._run(
            "advance", str(task), "--task-step", "execute.implement", "--force", "--note", "x"
        )
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertEqual(payload.get("error"), "task_reconfirm_required", payload)
        self._assert_err(
            self._run("design-gate", "start", str(task), "--iteration", "4"),
            "task_reconfirm_required",
        )

        # ⑤ TASK 원복(해시 재일치) 후 advance → exit 0, passed=approved=현재 묶음 hash
        (task / "TASK.md").write_text(TASK_MD_SDLC_V2, encoding="utf-8")
        self._assert_ok(self._run("advance", str(task), "--task-step", "execute.implement"))
        state = json.loads((task / "state.json").read_text(encoding="utf-8"))
        design_gate = state.get("design_gate", {})
        bundle_hash = design_gate.get("passed_bundle_hash")
        self.assertIsNotNone(bundle_hash, state)
        self.assertEqual(bundle_hash, design_gate.get("approved_bundle_hash"), state)

    def test_s6_agentic_auto_approval_flow(self):
        task = self._make_pm_task("s6-agentic", mode="agentic")
        self._assert_ok(self._run("design-gate", "start", str(task), "--iteration", "1"))

        # ① start 후 PLAN 수정, record pass → design_gate_input_changed, state 불변
        before_sha = _sha256(task / "state.json")
        self._plan_variant(task, lambda t: t + "\n<!-- edit -->\n")
        self._assert_err(
            self._record(task, 1, verdict="pass"),
            "design_gate_input_changed",
        )
        after_sha = _sha256(task / "state.json")
        self.assertEqual(before_sha, after_sha)

        # ② 재start → pass 기록 → mark plan.design_gate → mark plan.user_confirm --owner user
        # → PLAN 한 줄 수정 → advance execute.implement (재승인 없음 → 거부, --force --note도 거부)
        self._assert_ok(self._run("design-gate", "start", str(task), "--iteration", "2"))
        self._assert_ok(self._record(task, 2, verdict="pass"))
        self._assert_ok(self._run("mark", str(task), "--task-step", "plan.design_gate", "--done"))
        self._assert_ok(
            self._run("mark", str(task), "--task-step", "plan.user_confirm", "--done", "--owner", "user")
        )
        self._plan_variant(task, lambda t: t + "\n<!-- edit2 -->\n")
        completed, payload = self._run("advance", str(task), "--task-step", "execute.implement")
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertEqual(payload.get("error"), "design_bundle_mismatch", payload)
        completed, payload = self._run(
            "advance", str(task), "--task-step", "execute.implement", "--force", "--note", "x"
        )
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertEqual(payload.get("error"), "design_bundle_mismatch", payload)

        # ③ 다시 start → plan.user_confirm이 pending으로 되돌아감 → pass 기록 →
        # agentic은 자동 승인이 새 approved_bundle_hash를 기록한 뒤 advance가 성공한다
        self._assert_ok(self._run("design-gate", "start", str(task), "--iteration", "3"))
        state = json.loads((task / "state.json").read_text(encoding="utf-8"))
        rows = {row.get("key"): row for row in state.get("rows", [])}
        self.assertEqual(rows.get("plan.user_confirm", {}).get("status"), "pending", state)
        self._assert_ok(self._record(task, 3, verdict="pass"))
        self._assert_ok(self._run("advance", str(task), "--task-step", "execute.implement"))
        state = json.loads((task / "state.json").read_text(encoding="utf-8"))
        design_gate = state.get("design_gate", {})
        bundle_hash = design_gate.get("passed_bundle_hash")
        self.assertIsNotNone(bundle_hash, state)
        self.assertEqual(bundle_hash, design_gate.get("approved_bundle_hash"), state)

    # ------------------------------------------------------------------
    # S-7 — 반복 상한·reset (DEC-9, DEC-10, DEC-11)
    # ------------------------------------------------------------------

    def test_s7_retry_limit_and_reset(self):
        task = self._make_pm_task("s7")
        fail_eval = json.loads(json.dumps(EVALUATOR_PASS_JSON))
        fail_eval["design"]["axes"]["decision_clarity"] = "FAIL"
        fail_eval["verdict"] = "rewrite"

        # i1 start (열린 시도)
        self._assert_ok(self._run("design-gate", "start", str(task), "--iteration", "1"))

        # 열린 시도 중 start → design_gate_attempt_open (record가 먼저)
        before_sha = _sha256(task / "state.json")
        self._assert_err(
            self._run("design-gate", "start", str(task), "--iteration", "2"),
            "design_gate_attempt_open",
        )
        after_sha = _sha256(task / "state.json")
        self.assertEqual(before_sha, after_sha)

        # ① 설계 한 축 FAIL인데 --verdict pass 전달 → design_gate_verdict_mismatch (열린 시도 유지)
        self._assert_err(
            self._record(task, 1, verdict="pass", evaluator=fail_eval),
            "design_gate_verdict_mismatch",
        )
        state = json.loads((task / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state.get("design_gate", {}).get("status"), "evaluating", state)
        self.assertEqual(
            state.get("design_gate", {}).get("current_attempt", {}).get("iteration"), 1, state
        )

        # ② 아직 pass 아닌 상태에서 mark/advance → design_gate_not_passed
        self._assert_err(
            self._run("mark", str(task), "--task-step", "plan.design_gate", "--done"),
            "design_gate_not_passed",
        )
        completed, payload = self._run("advance", str(task), "--task-step", "execute.implement")
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertEqual(payload.get("error"), "design_gate_not_passed", payload)

        # i1을 --verdict rewrite --rewrite-target plan으로 정상 기록(1회)
        self._assert_ok(
            self._record(task, 1, verdict="rewrite", evaluator=fail_eval, rewrite_target="plan")
        )
        state = json.loads((task / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(len(state.get("design_gate", {}).get("history", [])), 1, state)

        # ③ PLAN 수정 후 i2 start, --verdict input_error 기록(2회) 후 advance 거부
        self._plan_variant(task, lambda t: t + "\n<!-- retry-2 -->\n")
        (task / "TEST-SCENARIO.md").write_text(
            TEST_SCENARIO_MD_TEMPLATE.format(scenario_refs="AC-1, AC-2, AC-3, C-1, H-1"),
            encoding="utf-8",
        )
        self._assert_ok(self._run("design-gate", "start", str(task), "--iteration", "2"))
        self._assert_ok(self._record(task, 2, verdict="input_error", evaluator=fail_eval))
        state = json.loads((task / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(len(state.get("design_gate", {}).get("history", [])), 2, state)
        completed, payload = self._run("advance", str(task), "--task-step", "execute.implement")
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertEqual(payload.get("error"), "design_gate_not_passed", payload)

        # PLAN 수정 후 i3 start, rewrite 기록(3회) → status=retry_limit·await_user·decision_request
        self._plan_variant(task, lambda t: t + "\n<!-- retry-3 -->\n")
        (task / "TEST-SCENARIO.md").write_text(
            TEST_SCENARIO_MD_TEMPLATE.format(scenario_refs="AC-1, AC-2, AC-3, C-1, H-1"),
            encoding="utf-8",
        )
        self._assert_ok(self._run("design-gate", "start", str(task), "--iteration", "3"))
        completed, last_payload = self._record(
            task, 3, verdict="rewrite", evaluator=fail_eval, rewrite_target="plan"
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(last_payload.get("status"), "retry_limit", last_payload)
        self.assertEqual(last_payload.get("transition_action"), "await_user", last_payload)
        self.assertEqual(last_payload.get("report_type"), "decision_request", last_payload)
        state = json.loads((task / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(len(state.get("design_gate", {}).get("history", [])), 3, state)

        # ⑤ 4회차 start → design_gate_retry_limit
        self._assert_err(
            self._run("design-gate", "start", str(task), "--iteration", "4"),
            "design_gate_retry_limit",
        )

        # ⑥ reset --owner user 없이 → user_confirmation_required, 있으면 exit 0
        self._assert_err(
            self._run("design-gate", "reset", str(task), "--note", "재시도 승인"),
            "user_confirmation_required",
        )
        self._assert_ok(
            self._run(
                "design-gate", "reset", str(task), "--owner", "user", "--note", "재시도 승인"
            )
        )

        # reset 후 PLAN 수정한 i4 start → exit 0 (회차 번호 이어 사용)
        self._plan_variant(task, lambda t: t + "\n<!-- retry-4 -->\n")
        (task / "TEST-SCENARIO.md").write_text(
            TEST_SCENARIO_MD_TEMPLATE.format(scenario_refs="AC-1, AC-2, AC-3, C-1, H-1"),
            encoding="utf-8",
        )
        result = self._assert_ok(
            self._run("design-gate", "start", str(task), "--iteration", "4")
        )
        self.assertEqual(result.get("status"), "evaluating", result)

    # ------------------------------------------------------------------
    # S-8 — 설계 결정 기록 (DEC-12)
    # ------------------------------------------------------------------

    def test_s8_design_decision(self):
        task = self._make_pm_task("s8")

        result = self._assert_ok(
            self._run(
                "design-decision", str(task),
                "--scope", "detail",
                "--summary", "예시 세부 결정",
                "--basis", "예시 근거",
            )
        )
        self.assertEqual(result.get("transition_action"), "continue", result)
        state_md = (task / "STATE.md").read_text(encoding="utf-8")
        self.assertIn("예시 세부 결정", state_md)

        # ② --scope external은 plan.plan_md가 in_progress인 상태에서 호출한다
        # (헬퍼가 mark하기 전 advance --task-step plan.plan_md로 만든 별도 태스크)
        ext_task = self.root / "s8-ext"
        self._write_pm_docs(ext_task)
        resolved = self._assert_ok(
            self._run("resolve-start", str(ext_task), "--skill", "opd", "--new-task")
        )
        init_args = list(resolved.get("init_args") or [])
        completed, _ = self._run("init", str(ext_task), *init_args, "--worktree", str(ext_task))
        self.assertEqual(completed.returncode, 0, completed.stderr)
        for key in ("task.task_md", "task.user_confirm"):
            completed, _ = self._run("mark", str(ext_task), "--task-step", key, "--done")
            self.assertEqual(completed.returncode, 0, completed.stderr)
        completed, _ = self._run("advance", str(ext_task), "--task-step", "plan.plan_md")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        state = json.loads((ext_task / "state.json").read_text(encoding="utf-8"))
        rows = {row.get("key"): row for row in state.get("rows", [])}
        self.assertEqual(rows.get("plan.plan_md", {}).get("status"), "in_progress", state)

        result = self._assert_ok(
            self._run(
                "design-decision", str(ext_task),
                "--scope", "external",
                "--summary", "예시 외부 결정",
                "--basis", "예시 근거",
            )
        )
        self.assertEqual(result.get("current_status"), "blocked", result)
        self.assertEqual(result.get("transition_action"), "blocked", result)
        self.assertEqual(result.get("report_type"), "decision_request", result)
        state = json.loads((ext_task / "state.json").read_text(encoding="utf-8"))
        rows = {row.get("key"): row for row in state.get("rows", [])}
        self.assertEqual(rows.get("plan.plan_md", {}).get("status"), "failed", state)

        # ③ PM 경로가 아닌 폴더 (pipeline-short.json, --no-pm)
        other = self.root / "s8-no-pm"
        self._write_pm_docs(other)
        resolved = self._assert_ok(
            self._run("resolve-start", str(other), "--skill", "opds", "--new-task", "--no-pm")
        )
        init_args = list(resolved.get("init_args") or [])
        completed, _ = self._run("init", str(other), *init_args, "--worktree", str(other))
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self._assert_err(
            self._run(
                "design-decision", str(other),
                "--scope", "detail",
                "--summary", "예시",
                "--basis", "예시",
            ),
            "design_gate_not_applicable",
        )

    # ------------------------------------------------------------------
    # S-9 — run-log gate 이벤트 (DEC-9)
    # ------------------------------------------------------------------

    def test_s9_run_log_gate_events(self):
        task = self.root / "s9"
        self._write_pm_docs(task)
        resolved = self._assert_ok(
            self._run("resolve-start", str(task), "--skill", "opd", "--new-task")
        )
        init_args = list(resolved.get("init_args") or [])
        completed, _ = self._run(
            "init", str(task), *init_args, "--worktree", str(task), "--run-log-mode", "shadow"
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        for key in ("task.task_md", "task.user_confirm", "plan.plan_md", "plan.test_scenario_md"):
            args = ["mark", str(task), "--task-step", key, "--done"]
            if key in ("plan.plan_md", "plan.test_scenario_md"):
                args.append("--worker-duration-unknown")
            completed, _ = self._run(*args)
            self.assertEqual(completed.returncode, 0, completed.stderr)

        self._assert_ok(self._run("design-gate", "start", str(task), "--iteration", "1"))
        self._assert_ok(self._record(task, 1, verdict="pass"))

        run_dir = task / "run"
        entries = []
        if run_dir.exists():
            for log_file in run_dir.glob("run-log-*.jsonl"):
                for line in log_file.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        entries.append(json.loads(line))
        requested = [e for e in entries if e.get("event") == "gate.requested"]
        resolved_events = [e for e in entries if e.get("event") == "gate.resolved"]
        self.assertEqual(len(requested), 1, entries)
        self.assertEqual(len(resolved_events), 1, entries)
        self.assertEqual(requested[0].get("gate_id"), "design-gate-i1", requested)
        self.assertEqual(resolved_events[0].get("gate_id"), "design-gate-i1", resolved_events)
        self.assertEqual(
            resolved_events[0].get("data", {}).get("verdict"), "approved", resolved_events
        )

        completed, payload = self._run(
            "verify", str(task), "--run-log-completeness-check"
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(payload.get("missing_gate_event"), [], payload)

    # ------------------------------------------------------------------
    # ADD-1 — stale evaluator 결과 거부 (input_bundle_hash·iteration 일치)
    # ------------------------------------------------------------------

    def test_add1_stale_evaluator_result_rejected(self):
        task = self._make_pm_task("add1-stale")
        self._assert_ok(self._run("design-gate", "start", str(task), "--iteration", "1"))

        # i1을 pass로 정상 기록해두고, 그 결과 JSON을 stale 재사용 재료로 삼는다.
        completed, payload1 = self._record(task, 1, verdict="pass")
        self._assert_ok((completed, payload1))
        i1_result_path = task / "evaluator-result-i1.json"
        i1_result = json.loads(i1_result_path.read_text(encoding="utf-8"))
        self.assertIn("input_bundle_hash", i1_result, i1_result)
        self.assertEqual(i1_result.get("iteration"), 1, i1_result)

        # PLAN 수정 후 i2 start — 새 bundle_hash 발급
        self._plan_variant(task, lambda t: t + "\n<!-- add1-stale-i2 -->\n")
        self._assert_ok(self._run("design-gate", "start", str(task), "--iteration", "2"))

        # (a) i1의 결과 JSON(input_bundle_hash·iteration=1)을 그대로 i2에 pass로 제출 → stale 거부
        stale_path = task / "evaluator-result-i2-stale.json"
        stale_path.write_text(json.dumps(i1_result, ensure_ascii=False), encoding="utf-8")
        before_sha = _sha256(task / "state.json")
        completed, payload = self._run(
            "design-gate", "record", str(task),
            "--iteration", "2", "--verdict", "pass",
            "--evaluator-result", str(stale_path),
        )
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertEqual(payload.get("error"), "design_gate_result_stale", payload)
        after_sha = _sha256(task / "state.json")
        self.assertEqual(before_sha, after_sha)
        state = json.loads((task / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(
            state.get("design_gate", {}).get("current_attempt", {}).get("iteration"), 2, state
        )

        # (b) input_bundle_hash 누락 JSON → stale 거부
        missing_hash = json.loads(json.dumps(EVALUATOR_PASS_JSON))
        missing_hash["iteration"] = 2
        self._assert_err(
            self._record(
                task, 2, verdict="pass", evaluator=missing_hash, input_bundle_hash=None
            ),
            "design_gate_result_stale",
        )
        after_sha_b = _sha256(task / "state.json")
        self.assertEqual(before_sha, after_sha_b)

        # (c) 해시는 맞고 iteration만 다름 → stale 거부
        state2 = json.loads((task / "state.json").read_text(encoding="utf-8"))
        current_hash = state2.get("design_gate", {}).get("current_attempt", {}).get("bundle_hash")
        self.assertIsNotNone(current_hash, state2)
        self._assert_err(
            self._record(
                task, 2, verdict="pass",
                input_bundle_hash=current_hash, stale_iteration=99,
            ),
            "design_gate_result_stale",
        )
        after_sha_c = _sha256(task / "state.json")
        self.assertEqual(before_sha, after_sha_c)

        # (d) 올바른 해시·회차로 기록하면 pass
        self._assert_ok(self._record(task, 2, verdict="pass"))
        state3 = json.loads((task / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state3.get("design_gate", {}).get("status"), "pass", state3)

        # (e) --verdict input_error는 해시 없는 evaluator 결과로도 기록 성공한다
        self._plan_variant(task, lambda t: t + "\n<!-- add1-stale-i3 -->\n")
        (task / "TEST-SCENARIO.md").write_text(
            TEST_SCENARIO_MD_TEMPLATE.format(scenario_refs="AC-1, AC-2, AC-3, C-1, H-1"),
            encoding="utf-8",
        )
        self._assert_ok(self._run("design-gate", "start", str(task), "--iteration", "3"))
        broken = {"not": "a contract shaped result"}
        self._assert_ok(
            self._record(task, 3, verdict="input_error", evaluator=broken, input_bundle_hash=None)
        )

    # ------------------------------------------------------------------
    # ADD-2 — design-decision detail/external의 run-log activity 사건 data 형식
    # ------------------------------------------------------------------

    def _make_shadow_pm_task_plan_in_progress(self, name: str) -> Path:
        """run-log-mode shadow PM 태스크를 plan.plan_md in_progress까지 준비한다."""
        task = self.root / name
        self._write_pm_docs(task)
        resolved = self._assert_ok(
            self._run("resolve-start", str(task), "--skill", "opd", "--new-task")
        )
        init_args = list(resolved.get("init_args") or [])
        completed, _ = self._run(
            "init", str(task), *init_args, "--worktree", str(task), "--run-log-mode", "shadow"
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        for key in ("task.task_md", "task.user_confirm"):
            completed, _ = self._run("mark", str(task), "--task-step", key, "--done")
            self.assertEqual(completed.returncode, 0, completed.stderr)
        completed, _ = self._run("advance", str(task), "--task-step", "plan.plan_md")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        state = json.loads((task / "state.json").read_text(encoding="utf-8"))
        rows = {row.get("key"): row for row in state.get("rows", [])}
        self.assertEqual(rows.get("plan.plan_md", {}).get("status"), "in_progress", state)
        return task

    def _collect_run_log_entries(self, task: Path) -> list[dict]:
        entries: list[dict] = []
        run_dir = task / "run"
        if run_dir.exists():
            for log_file in run_dir.glob("run-log-*.jsonl"):
                for line in log_file.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        entries.append(json.loads(line))
        return entries

    def test_add2_design_decision_detail_commits_activity(self):
        # ① --scope detail: design-decision 사건이 run-log activity로 정상 drain돼야
        # 한다. 계약(docs/run-log/CONTRACT.md §1.3, log-event --event activity와 동일
        # 형식)은 data가 {"kind": "decision"} 객체이지만 결함 구현은 문자열 "decision"을
        # 만들어 기록 코어가 거부하고 drain이 멈춘다 — 이 단언에서 실패해야 한다(RED).
        task = self._make_shadow_pm_task_plan_in_progress("add2-detail")

        result = self._assert_ok(
            self._run(
                "design-decision", str(task),
                "--scope", "detail",
                "--summary", "예시 세부 결정",
                "--basis", "예시 근거",
            )
        )
        self.assertEqual(result.get("transition_action"), "continue", result)

        state = json.loads((task / "state.json").read_text(encoding="utf-8"))
        pending = (state.get("run_log") or {}).get("pending_events") or []
        self.assertEqual(pending, [], state)
        self.assertNotEqual(
            (state.get("run_log") or {}).get("status"), "pending", state
        )

        entries = self._collect_run_log_entries(task)
        activity_entries = [
            e for e in entries
            if e.get("event") == "activity"
            and e.get("data") == {"kind": "decision"}
            and str(e.get("summary", "")).startswith("design-decision(detail):")
        ]
        self.assertEqual(len(activity_entries), 1, entries)

        # drain이 막히지 않았으면 이어지는 log-event도 정상 처리돼야 한다.
        completed, payload = self._run(
            "log-event", str(task),
            "--event", "activity", "--kind", "progress", "--summary", "x",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertIsInstance(payload, dict, completed.stdout)
        self.assertTrue(payload.get("ok"), payload)
        warnings = payload.get("warnings") or []
        self.assertNotIn("run_log_pending", warnings, payload)

        # ② --scope external도 같은 조건(pending 0)으로 확인한다.
        ext_task = self._make_shadow_pm_task_plan_in_progress("add2-external")
        result_ext = self._assert_ok(
            self._run(
                "design-decision", str(ext_task),
                "--scope", "external",
                "--summary", "예시 외부 결정",
                "--basis", "예시 근거",
            )
        )
        self.assertEqual(result_ext.get("current_status"), "blocked", result_ext)
        state_ext = json.loads((ext_task / "state.json").read_text(encoding="utf-8"))
        pending_ext = (state_ext.get("run_log") or {}).get("pending_events") or []
        self.assertEqual(pending_ext, [], state_ext)
        self.assertNotEqual(
            (state_ext.get("run_log") or {}).get("status"), "pending", state_ext
        )


# ─────────────────────────────────────────────────────────────────────────────
# [T167] S-5/S-7: design-gate advisory 응답·refinement 전이, scenario_gate mark 가드
# RED-first — 태스크 167 PLAN.md Decisions and contracts SSOT. 기존 클래스를 상속하면
# 상속된 test_s1~s9가 이 클래스에서도 재실행되므로, 필요한 헬퍼만 독립 함수로 복제한다.
# ─────────────────────────────────────────────────────────────────────────────

TEST_TOOL_RUN = REPO_ROOT / "opal" / "tools" / "test-tool" / "run.sh"


def _t167_dg_run(*args):
    completed = subprocess.run(
        [sys.executable, str(STATE_TOOL), *args],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    try:
        payload = json.loads(completed.stdout)
    except (json.JSONDecodeError, TypeError):
        payload = None
    return completed, payload


def _t167_assert_ok(result):
    completed, payload = result
    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert isinstance(payload, dict), completed.stdout
    assert payload.get("ok"), payload
    return payload


def _t167_assert_err(result, code):
    completed, payload = result
    assert completed.returncode == 1, completed.stderr or completed.stdout
    assert isinstance(payload, dict), completed.stdout
    assert not payload.get("ok"), payload
    assert payload.get("error") == code, payload
    return payload


def _t167_write_pm_docs(task, *, plan_refs="AC-1, AC-2, AC-3, C-1", scenario_refs="AC-1, AC-2, AC-3, C-1, H-1"):
    task.mkdir(parents=True, exist_ok=True)
    (task / "TASK.md").write_text(TASK_MD_SDLC_V2, encoding="utf-8")
    (task / "PLAN.md").write_text(PLAN_MD_TEMPLATE.format(plan_refs=plan_refs), encoding="utf-8")
    (task / "TEST-SCENARIO.md").write_text(
        TEST_SCENARIO_MD_TEMPLATE.format(scenario_refs=scenario_refs), encoding="utf-8"
    )


def _t167_make_pm_task(root, name):
    task = root / name
    _t167_write_pm_docs(task)
    resolved = _t167_assert_ok(
        _t167_dg_run("resolve-start", str(task), "--skill", "opd", "--new-task")
    )
    init_args = list(resolved.get("init_args") or [])
    completed, payload = _t167_dg_run("init", str(task), *init_args, "--worktree", str(task))
    assert completed.returncode == 0, completed.stderr or completed.stdout
    for key in ("task.task_md", "task.user_confirm", "plan.plan_md", "plan.test_scenario_md"):
        args = ["mark", str(task), "--task-step", key, "--done"]
        if key in ("plan.plan_md", "plan.test_scenario_md"):
            args.append("--worker-duration-unknown")
        completed, payload = _t167_dg_run(*args)
        assert completed.returncode == 0, completed.stderr or completed.stdout
    return task


def _t167_record(task, iteration, *, verdict, advisories=None, rewrite_target=None, advisory_responses=None):
    payload = json.loads(json.dumps(EVALUATOR_PASS_JSON, ensure_ascii=False))
    payload["verdict"] = verdict
    payload["advisories"] = advisories if advisories is not None else []
    state = json.loads((task / "state.json").read_text(encoding="utf-8"))
    attempt = (state.get("design_gate") or {}).get("current_attempt") or {}
    payload["input_bundle_hash"] = attempt.get("bundle_hash")
    payload["iteration"] = attempt.get("iteration")
    eval_path = task / f"t167-evaluator-i{iteration}.json"
    eval_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    args = [
        "design-gate", "record", str(task),
        "--iteration", str(iteration), "--verdict", verdict,
        "--evaluator-result", str(eval_path),
    ]
    if rewrite_target:
        args += ["--rewrite-target", rewrite_target]
    if advisory_responses is not None:
        resp_path = task / f"t167-responses-i{iteration}.json"
        resp_path.write_text(json.dumps(advisory_responses, ensure_ascii=False), encoding="utf-8")
        args += ["--advisory-responses", str(resp_path)]
    return _t167_dg_run(*args)


_T167_ADVISORY = {
    "id": "A-1", "kind": "mergeable", "targets": ["S-1"],
    "basis": "동일 축 검증", "recommendation": "통합",
}


class TestS167_S5DesignGateAdvisory(unittest.TestCase):
    """[T167/S-5] design-gate record의 advisory 형식 검사·응답 완전성·apply→refinement
    전이 (AC-4, AC-5, AC-6, C-3). `--advisory-responses`가 아직 없어 RED다."""

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_malformed_advisory_result_rejected_state_unchanged(self):
        """① advisory 필드 누락 결과는 design_gate_result_invalid이고 state가 바뀌지 않는다."""
        task = _t167_make_pm_task(self.root, "s5-malformed")
        _t167_assert_ok(_t167_dg_run("design-gate", "start", str(task), "--iteration", "1"))
        before = _sha256(task / "state.json")
        _t167_assert_err(
            _t167_record(task, 1, verdict="pass", advisories=[{"id": "A-1"}]),
            "design_gate_result_invalid",
        )
        after = _sha256(task / "state.json")
        self.assertEqual(before, after, "state.json이 바이트 단위로 불변이어야 한다")

    def test_pass_with_incomplete_advisory_response_rejected_attempt_open(self):
        """② pass에 응답 없음·ID 불일치·사유 없는 retain은 advisory_response_invalid이고
        시도가 열린 채 state가 바뀌지 않는다. ③ 전부 retain(사유 포함)이면 pass다."""
        task = _t167_make_pm_task(self.root, "s5-incomplete")
        _t167_assert_ok(_t167_dg_run("design-gate", "start", str(task), "--iteration", "1"))
        before = _sha256(task / "state.json")
        _t167_assert_err(
            _t167_record(task, 1, verdict="pass", advisories=[_T167_ADVISORY], advisory_responses=None),
            "advisory_response_invalid",
        )
        after = _sha256(task / "state.json")
        self.assertEqual(before, after)
        state = json.loads((task / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state.get("design_gate", {}).get("status"), "evaluating", state)

        # 전부 retain(사유 포함) → pass
        result = _t167_assert_ok(
            _t167_record(
                task, 1, verdict="pass", advisories=[_T167_ADVISORY],
                advisory_responses=[{"id": "A-1", "response": "retain", "reason": "현행 유지"}],
            )
        )
        self.assertEqual(result.get("status"), "pass", result)

    def test_apply_then_refinement_pass_flow_without_consuming_retry_limit(self):
        """④ iteration 3의 apply는 history verdict: rewrite·reason: advisory_apply이고
        status는 retry_limit이 아닌 fail이다. 다음 start의 attempt와 응답은 refinement:
        true다. ⑤ 그 record 결과에 비어 있지 않은 advisories가 있어도 응답 없이 기록되고
        pass면 status가 pass다. ⑧ apply·refinement 회차는 상한을 소비하지 않는다 —
        i1 rewrite → i2 apply → i3 refinement pass 흐름에서 retry_limit이 나오지 않는다."""
        task = _t167_make_pm_task(self.root, "s5-apply-refine")

        # i1: 일반 rewrite (advisory 없음, 상한 소비)
        _t167_assert_ok(_t167_dg_run("design-gate", "start", str(task), "--iteration", "1"))
        _t167_assert_ok(_t167_record(task, 1, verdict="rewrite", rewrite_target="plan"))

        # i2: apply
        (task / "PLAN.md").write_text(
            PLAN_MD_TEMPLATE.format(plan_refs="AC-1, AC-2, AC-3, C-1") + "\n<!-- t167-apply -->\n",
            encoding="utf-8",
        )
        _t167_assert_ok(_t167_dg_run("design-gate", "start", str(task), "--iteration", "2"))
        result = _t167_assert_ok(
            _t167_record(
                task, 2, verdict="pass", advisories=[_T167_ADVISORY], rewrite_target="plan",
                advisory_responses=[{"id": "A-1", "response": "apply", "reason": "통합 채택"}],
            )
        )
        self.assertEqual(result.get("status"), "fail", result)
        state = json.loads((task / "state.json").read_text(encoding="utf-8"))
        history = state.get("design_gate", {}).get("history", [])
        self.assertEqual(history[-1].get("verdict"), "rewrite", state)
        self.assertEqual(history[-1].get("reason"), "advisory_apply", state)
        self.assertNotEqual(result.get("status"), "retry_limit", result)

        # i3: refinement(도구가 refinement_pending으로 자동 판정) — start 응답에 refinement: true
        started = _t167_assert_ok(_t167_dg_run("design-gate", "start", str(task), "--iteration", "3"))
        state = json.loads((task / "state.json").read_text(encoding="utf-8"))
        attempt = state.get("design_gate", {}).get("current_attempt", {})
        self.assertIs(attempt.get("refinement"), True, state)

        result3 = _t167_assert_ok(
            _t167_record(task, 3, verdict="pass", advisories=[_T167_ADVISORY])
        )
        self.assertEqual(result3.get("status"), "pass", result3)
        self.assertNotEqual(result3.get("status"), "retry_limit", result3)

    def test_refinement_fail_hits_retry_limit_then_reset_clears_refinement(self):
        """⑥ 별도 흐름에서 refinement record가 rewrite면 history reason:
        advisory_refinement_failed, status retry_limit, await_user·decision_request다.
        다음 start는 design_gate_retry_limit이고, reset --owner user 뒤에는
        refinement: false로 start가 허용된다."""
        task = _t167_make_pm_task(self.root, "s5-refine-fail")
        _t167_assert_ok(_t167_dg_run("design-gate", "start", str(task), "--iteration", "1"))
        _t167_assert_ok(_t167_record(task, 1, verdict="rewrite", rewrite_target="plan"))

        (task / "PLAN.md").write_text(
            PLAN_MD_TEMPLATE.format(plan_refs="AC-1, AC-2, AC-3, C-1") + "\n<!-- t167-apply -->\n",
            encoding="utf-8",
        )
        _t167_assert_ok(_t167_dg_run("design-gate", "start", str(task), "--iteration", "2"))
        _t167_assert_ok(
            _t167_record(
                task, 2, verdict="pass", advisories=[_T167_ADVISORY], rewrite_target="plan",
                advisory_responses=[{"id": "A-1", "response": "apply", "reason": "통합 채택"}],
            )
        )

        _t167_assert_ok(_t167_dg_run("design-gate", "start", str(task), "--iteration", "3"))
        result = _t167_assert_ok(_t167_record(task, 3, verdict="rewrite", rewrite_target="plan"))
        self.assertEqual(result.get("status"), "retry_limit", result)
        self.assertEqual(result.get("transition_action"), "await_user", result)
        self.assertEqual(result.get("report_type"), "decision_request", result)
        state = json.loads((task / "state.json").read_text(encoding="utf-8"))
        history = state.get("design_gate", {}).get("history", [])
        self.assertEqual(history[-1].get("reason"), "advisory_refinement_failed", state)

        _t167_assert_err(
            _t167_dg_run("design-gate", "start", str(task), "--iteration", "4"),
            "design_gate_retry_limit",
        )
        _t167_assert_ok(
            _t167_dg_run("design-gate", "reset", str(task), "--owner", "user", "--note", "재시도 승인")
        )
        (task / "PLAN.md").write_text(
            PLAN_MD_TEMPLATE.format(plan_refs="AC-1, AC-2, AC-3, C-1") + "\n<!-- t167-reset -->\n",
            encoding="utf-8",
        )
        _t167_assert_ok(_t167_dg_run("design-gate", "start", str(task), "--iteration", "4"))
        state = json.loads((task / "state.json").read_text(encoding="utf-8"))
        attempt = state.get("design_gate", {}).get("current_attempt", {})
        self.assertIs(attempt.get("refinement"), False, state)


# ------------------------------------------------------------------
# S-7 (T167) — 목표-커버 게이트 mark 가드 (AC-7, C-1, H-1)
# ------------------------------------------------------------------

def _t167_short_make_worker_task(root, name):
    """opds(pipeline-short.json) --no-pm 경로로 plan.plan_md까지 완료한다."""
    task = root / name
    _t167_write_pm_docs(task)
    resolved = _t167_assert_ok(
        _t167_dg_run("resolve-start", str(task), "--skill", "opds", "--new-task", "--no-pm")
    )
    init_args = list(resolved.get("init_args") or [])
    completed, _payload = _t167_dg_run("init", str(task), *init_args, "--worktree", str(task))
    assert completed.returncode == 0, completed.stderr or completed.stdout
    for args in (
        ["mark", str(task), "--task-step", "task.task_md", "--done"],
        ["mark", str(task), "--task-step", "task.user_confirm", "--done"],
        ["mark", str(task), "--task-step", "plan.plan_md", "--done", "--worker-duration-unknown"],
    ):
        completed, _payload = _t167_dg_run(*args)
        assert completed.returncode == 0, completed.stderr or completed.stdout
    return task


def _t167_test_tool_run(*args):
    completed = subprocess.run(
        ["bash", str(TEST_TOOL_RUN), *args], capture_output=True, text=True, check=False,
    )
    try:
        payload = json.loads(completed.stdout) if completed.stdout.strip() else None
    except json.JSONDecodeError:
        payload = None
    return completed.returncode, completed.stdout, payload


def _t167_write_gate_eval(task, name, *, verdict="pass", advisories=None):
    payload = {
        "scores": {"goal": 2, "adoption": 2, "boundary": 2}, "average": 2.0,
        "gaps": [], "verdict": verdict, "advisories": advisories if advisories is not None else [],
    }
    path = task / name
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


class TestS167_S7ScenarioGateMarkGuard(unittest.TestCase):
    """[T167/S-7] state-tool mark가 plan.scenario_gate(opds)·test_scenario.scenario_gate
    (opd) 행을 완료로 바꿀 때 test-tool scenario-gate-verify를 거치지 않으면 거부한다
    (AC-7, C-1, H-1). scenario-gate-verify가 아직 없고 mark에 가드도 없어 RED다."""

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self):
        self.tempdir.cleanup()

    def _mark_scenario_gate(self, task, *extra_args):
        return _t167_dg_run(
            "mark", str(task), "--task-step", "plan.scenario_gate", "--done", *extra_args
        )

    def test_no_history_rejected_required_action_mentions_record(self):
        """(a) 이력 없음 → scenario_gate_record_required, state.json 바이트 불변,
        required_action에 scenario-gate-record 재실행 안내."""
        task = _t167_short_make_worker_task(self.root, "s7-a")
        before = _sha256(task / "state.json")
        completed, payload = self._mark_scenario_gate(task)
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertEqual(payload.get("error"), "scenario_gate_record_required", payload)
        after = _sha256(task / "state.json")
        self.assertEqual(before, after, "state.json이 바이트 단위로 불변이어야 한다")
        required_action = str(payload.get("required_action") or "")
        self.assertIn("scenario-gate-record", required_action, payload)

    def test_last_round_rewrite_rejected(self):
        """(b) 마지막 회차 rewrite 이력 → scenario_gate_record_required."""
        task = _t167_short_make_worker_task(self.root, "s7-b")
        _t167_write_gate_eval(task, "eval-i1.json", verdict="pass", advisories=[_T167_ADVISORY])
        responses = task / "responses-i1.json"
        responses.write_text(
            json.dumps([{"id": "A-1", "response": "apply", "reason": "통합"}], ensure_ascii=False),
            encoding="utf-8",
        )
        _t167_test_tool_run(
            "scenario-gate-record", "--task-folder", str(task), "--iteration", "1",
            "--evaluator-result", str(task / "eval-i1.json"),
            "--advisory-responses", str(responses),
        )
        completed, payload = self._mark_scenario_gate(task)
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertEqual(payload.get("error"), "scenario_gate_record_required", payload)

    def test_bypass_flags_do_not_skip_guard(self):
        """(d) 이력 없는 상태에서 --force --note·--auto-pass·--step 1/1로도 우회할 수 없다."""
        task = _t167_short_make_worker_task(self.root, "s7-d")
        for extra in (
            ["--force", "--note", "우회 시도"],
            ["--auto-pass"],
            ["--step", "1/1"],
        ):
            with self.subTest(extra=extra):
                completed, payload = self._mark_scenario_gate(task, *extra)
                self.assertEqual(completed.returncode, 1, completed.stdout)
                self.assertEqual(payload.get("error"), "scenario_gate_record_required", payload)

    def test_pass_then_doc_change_rejected_by_hash_mismatch(self):
        """(c) pass 뒤 TEST-SCENARIO 수정 → 다음 mark는 scenario_gate_record_required로
        거부된다(bundle_hash 변경)."""
        task = _t167_short_make_worker_task(self.root, "s7-c")
        _t167_write_gate_eval(task, "eval-i1.json", verdict="pass", advisories=[])
        record_code, record_stdout, _record_data = _t167_test_tool_run(
            "scenario-gate-record", "--task-folder", str(task), "--iteration", "1",
            "--evaluator-result", str(task / "eval-i1.json"),
        )
        self.assertEqual(record_code, 0, f"pass 기록 자체는 exit 0이어야 한다, 실제={record_stdout!r}")

        (task / "TEST-SCENARIO.md").write_text(
            (task / "TEST-SCENARIO.md").read_text(encoding="utf-8") + "\n<!-- t167-changed -->\n",
            encoding="utf-8",
        )
        completed, payload = self._mark_scenario_gate(task)
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertEqual(payload.get("error"), "scenario_gate_record_required", payload)

    def test_normal_pass_allows_mark_done(self):
        """(e) 정상 pass 이력 뒤 mark는 done이 된다. 이미 완료된 게이트 행 외 다른 행 mark는
        가드 없이 성공한다."""
        task = _t167_short_make_worker_task(self.root, "s7-e")
        _t167_write_gate_eval(task, "eval-i1.json", verdict="pass", advisories=[])
        record_code, record_stdout, _record_data = _t167_test_tool_run(
            "scenario-gate-record", "--task-folder", str(task), "--iteration", "1",
            "--evaluator-result", str(task / "eval-i1.json"),
        )
        self.assertEqual(record_code, 0, f"pass 기록은 exit 0이어야 한다, 실제={record_stdout!r}")

        completed, payload = self._mark_scenario_gate(task)
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertTrue(payload.get("ok"), payload)
        state = json.loads((task / "state.json").read_text(encoding="utf-8"))
        rows = {row.get("key"): row for row in state.get("rows", [])}
        self.assertEqual(rows.get("plan.scenario_gate", {}).get("status"), "done", state)

        # 이미 완료된 게이트 행 외 다른 행(plan.pm_gate)의 mark는 가드 없이 성공해야 한다.
        completed2, payload2 = _t167_dg_run(
            "mark", str(task), "--task-step", "plan.pm_gate", "--done",
        )
        self.assertEqual(completed2.returncode, 0, completed2.stderr or completed2.stdout)


if __name__ == "__main__":
    unittest.main()
