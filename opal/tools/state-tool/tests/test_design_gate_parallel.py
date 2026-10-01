"""
@header {
  "module": "test_design_gate_parallel",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "design-gate start 응답의 previous_gaps 조립(역순 유효 회차 선택·파일 부재 폴백·빈 gaps 정지·결정성)과 design-gate combine(설계·시나리오 부분 결과의 결정론 결합 verdict·rewrite_target·average, 오류 코드 3종과 상태 불변, 결합 결과의 record 수락)의 공개 CLI 계약. --make-fixture 진입점은 PM 경로 임시 태스크를 만들고 design-gate start --iteration 1까지 실행해 {task_path, bundle_hash} JSON을 출력한다.",
  "exports": ["main"],
  "depends": ["state_tool"]
}
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
STATE_TOOL = REPO_ROOT / "opal" / "tools" / "state-tool" / "state_tool.py"
sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_design_gate as _base  # noqa: E402  (픽스처 문서 템플릿 재사용)

AXES = ("completeness", "decision_clarity", "executability", "recoverability")
SCORE_KEYS = ("goal", "adoption", "boundary")
DOC_NAMES = ("TASK.md", "PLAN.md", "TEST-SCENARIO.md")


def run_cli(*args):
    completed = subprocess.run(
        [sys.executable, str(STATE_TOOL), *map(str, args)],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    try:
        payload = json.loads(completed.stdout)
    except (json.JSONDecodeError, TypeError):
        payload = None
    return completed, payload


def make_pm_task(task: Path, docs: Path | None = None, run_log: bool = False) -> None:
    """PM 경로로 init하고 plan.test_scenario_md까지 done으로 진행한다."""
    task.mkdir(parents=True, exist_ok=True)
    if docs is not None:
        for name in DOC_NAMES:
            shutil.copyfile(docs / name, task / name)
    else:
        (task / "TASK.md").write_text(_base.TASK_MD_SDLC_V2, encoding="utf-8")
        (task / "PLAN.md").write_text(
            _base.PLAN_MD_TEMPLATE.format(plan_refs="AC-1, AC-2, AC-3, C-1"), encoding="utf-8")
        (task / "TEST-SCENARIO.md").write_text(
            _base.TEST_SCENARIO_MD_TEMPLATE.format(scenario_refs="AC-1, AC-2, AC-3, C-1, H-1"),
            encoding="utf-8")
    completed, resolved = run_cli("resolve-start", task, "--skill", "opd", "--new-task")
    if completed.returncode != 0 or not resolved:
        raise RuntimeError(f"resolve-start failed: {completed.stdout}{completed.stderr}")
    init_extra = ["--run-log-mode", "shadow"] if run_log else []
    completed, _ = run_cli("init", task, *resolved["init_args"], "--worktree", task, *init_extra)
    if completed.returncode != 0:
        raise RuntimeError(f"init failed: {completed.stdout}{completed.stderr}")
    for key in ("task.task_md", "task.user_confirm", "plan.plan_md", "plan.test_scenario_md"):
        extra = ["--worker-duration-unknown"] if key.startswith("plan.") else []
        completed, _ = run_cli("mark", task, "--task-step", key, "--done", *extra)
        if completed.returncode != 0:
            raise RuntimeError(f"mark {key} failed: {completed.stdout}{completed.stderr}")


def partial_result(scope, bundle, iteration, *, axes=None, scores=None, gaps=None,
                   resolved=None, advisories=None):
    result = {"input_bundle_hash": bundle, "iteration": iteration, "scope": scope,
              "status": "ok", "resolved_gaps": resolved or [], "advisories": advisories or []}
    if scope == "design":
        result["design"] = {"axes": axes or {k: "PASS" for k in AXES}, "gaps": gaps or []}
    else:
        s = scores or {"goal": 2, "adoption": 2, "boundary": 2}
        result["scenario"] = {"scores": s, "average": sum(s.values()) / 3, "gaps": gaps or []}
    return result


class _GateFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def ok(self, result) -> dict:
        completed, payload = result
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertTrue(payload and payload.get("ok"), payload)
        return payload

    def err(self, result, code) -> dict:
        completed, payload = result
        self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
        self.assertEqual((payload or {}).get("error"), code, payload)
        return payload

    def state(self, task: Path) -> dict:
        return json.loads((task / "state.json").read_text(encoding="utf-8"))

    def write_json(self, path: Path, data) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return path

    def seed_history(self, task: Path, items, *, refinement_pending=False) -> None:
        """design_gate.history와 iteration을 직접 심는다(start N+1이 가능하도록)."""
        state = self.state(task)
        dg = state.setdefault("design_gate", {})
        dg["history"] = items
        dg["iteration"] = max([i["iteration"] for i in items] or [0])
        if refinement_pending:
            dg["refinement_pending"] = True
        (task / "state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def hist(iteration, verdict="rewrite"):
        return {"iteration": iteration, "verdict": verdict, "rewrite_target": None,
                "bundle_hash": "h", "reason": None, "at": "t"}

    def gap_file(self, task: Path, k: int, design_gaps, scenario_gaps) -> None:
        self.write_json(task / "run" / f"design-gate-i{k}.json",
                        {"design": {"gaps": design_gaps}, "scenario": {"gaps": scenario_gaps}})

    def start(self, task: Path, iteration: int) -> dict:
        return self.ok(run_cli("design-gate", "start", task, "--iteration", iteration))


class PreviousGapsStartTest(_GateFixture):
    """S-1 — design-gate start 응답의 previous_gaps 조립."""

    def prepared(self, name, history, files=None, **kw) -> Path:
        task = self.root / name
        make_pm_task(task)
        self.seed_history(task, history, **kw)
        for k, (d, s) in (files or {}).items():
            self.gap_file(task, k, d, s)
        return task

    def assert_fields(self, resp, flat, by_scope, iteration):
        self.assertEqual(resp["previous_gaps"], flat)
        self.assertEqual(resp["previous_gaps_by_scope"], by_scope)
        self.assertEqual(resp["previous_gaps_iteration"], iteration)

    def test_previous_gaps_no_history(self):
        task = self.root / "a"
        make_pm_task(task)
        resp = self.start(task, 1)
        self.assert_fields(resp, [], {"design": [], "scenario": []}, None)

    def test_previous_gaps_latest_valid_design_then_scenario(self):
        task = self.prepared("b", [self.hist(1), self.hist(2)],
                             {1: (["D-0: old"], []), 2: (["D-1: x", "D-2: y"], ["S-1: z"])})
        resp = self.start(task, 3)
        self.assert_fields(resp, ["D-1: x", "D-2: y", "S-1: z"],
                           {"design": ["D-1: x", "D-2: y"], "scenario": ["S-1: z"]}, 2)

    def test_previous_gaps_non_string_items_ignored(self):
        task = self.prepared("b2", [self.hist(1)], {1: (["D-1: x", 5, None], [{"a": 1}])})
        resp = self.start(task, 2)
        self.assert_fields(resp, ["D-1: x"], {"design": ["D-1: x"], "scenario": []}, 1)

    def test_previous_gaps_skips_non_evaluated_verdicts(self):
        history = [self.hist(1), self.hist(2, "input_error"), self.hist(3, "superseded"),
                   self.hist(4, "deterministic_fail")]
        task = self.prepared("c", history, {1: (["D-1: x"], ["S-1: y"]),
                                            2: (["D-9: no"], []), 3: (["D-9: no"], []),
                                            4: (["D-9: no"], [])})
        resp = self.start(task, 5)
        self.assert_fields(resp, ["D-1: x", "S-1: y"],
                           {"design": ["D-1: x"], "scenario": ["S-1: y"]}, 1)

    def test_previous_gaps_missing_file_falls_back(self):
        task = self.prepared("d", [self.hist(1), self.hist(2)], {1: (["D-1: x"], [])})
        resp = self.start(task, 3)
        self.assert_fields(resp, ["D-1: x"], {"design": ["D-1: x"], "scenario": []}, 1)

    def test_previous_gaps_unreadable_file_falls_back(self):
        task = self.prepared("d2", [self.hist(1), self.hist(2)], {1: (["D-1: x"], [])})
        (task / "run" / "design-gate-i2.json").write_text("{not json", encoding="utf-8")
        resp = self.start(task, 3)
        self.assert_fields(resp, ["D-1: x"], {"design": ["D-1: x"], "scenario": []}, 1)

    def test_previous_gaps_all_files_missing(self):
        task = self.prepared("d3", [self.hist(1), self.hist(2)])
        resp = self.start(task, 3)
        self.assert_fields(resp, [], {"design": [], "scenario": []}, None)

    def test_previous_gaps_empty_gaps_stop(self):
        task = self.prepared("e", [self.hist(1), self.hist(2)],
                             {1: (["D-1: x"], ["S-1: y"]), 2: ([], [])})
        resp = self.start(task, 3)
        self.assert_fields(resp, [], {"design": [], "scenario": []}, 2)

    def test_previous_gaps_deterministic_same_input_same_response(self):
        task = self.prepared("f", [self.hist(1)], {1: (["D-1: x"], ["S-1: y"])})
        before = (task / "state.json").read_bytes()
        first = self.start(task, 2)
        (task / "state.json").write_bytes(before)
        second = self.start(task, 2)
        for key in ("previous_gaps", "previous_gaps_by_scope", "previous_gaps_iteration",
                    "bundle_hash", "iteration", "refinement"):
            self.assertEqual(json.dumps(first[key], sort_keys=True),
                             json.dumps(second[key], sort_keys=True), key)

    def test_previous_gaps_rejection_paths_unchanged(self):
        task = self.root / "g"
        make_pm_task(task)
        self.start(task, 1)
        payload = self.err(run_cli("design-gate", "start", task, "--iteration", 1),
                           "design_gate_attempt_open")
        self.assertNotIn("previous_gaps", payload)
        task2 = self.root / "g2"
        make_pm_task(task2)
        payload = self.err(run_cli("design-gate", "start", task2, "--iteration", 5),
                           "design_gate_iteration_invalid")
        self.assertNotIn("previous_gaps", payload)


class CombineFixture(_GateFixture):
    def open_attempt(self, name="c", history=None, files=None, **kw):
        task = self.root / name
        make_pm_task(task, run_log=kw.pop("run_log", False))
        iteration = 1
        if history:
            self.seed_history(task, history, **kw)
            iteration = max(h["iteration"] for h in history) + 1
        elif kw.get("refinement_pending"):
            self.seed_history(task, [], **kw)
        for k, (d, s) in (files or {}).items():
            self.gap_file(task, k, d, s)
        resp = self.start(task, iteration)
        return task, resp["bundle_hash"], iteration

    def combine(self, task, iteration, design, scenario, output=None):
        d = self.write_json(self.root / "in" / f"{task.name}-d.json", design)
        s = self.write_json(self.root / "in" / f"{task.name}-s.json", scenario)
        out = output or (task / "run" / f"design-gate-i{iteration}.json")
        return run_cli("design-gate", "combine", task, "--iteration", iteration,
                       "--design-result", d, "--scenario-result", s, "--output", out), out


class CombineVerdictTest(CombineFixture):
    """S-2 — 결합 verdict·rewrite_target·average."""

    TOP_KEYS = {"input_bundle_hash", "iteration", "design", "scenario", "resolved_gaps",
                "advisories", "verdict", "rewrite_target"}

    def run_case(self, name, *, axes=None, scores=None, **kw):
        task, bundle, it = self.open_attempt(name, **kw.pop("attempt", {}))
        design = partial_result("design", bundle, it, axes=axes, **kw.pop("d", {}))
        scenario = partial_result("scenario", bundle, it, scores=scores, **kw.pop("s", {}))
        result, out = self.combine(task, it, design, scenario)
        payload = self.ok(result)
        combined = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(set(combined), self.TOP_KEYS)
        self.assertEqual(payload["verdict"], combined["verdict"])
        self.assertEqual(payload["rewrite_target"], combined["rewrite_target"])
        self.assertEqual(payload["output_path"], str(out))
        self.assertEqual(combined["input_bundle_hash"], bundle)
        s = combined["scenario"]["scores"]
        self.assertEqual(combined["scenario"]["average"], round(sum(s.values()) / 3, 3))
        return payload, combined

    def test_combine_verdict_pass(self):
        payload, combined = self.run_case("a")
        self.assertEqual((payload["verdict"], payload["rewrite_target"]), ("pass", None))
        self.assertEqual(payload["resolved_gaps_count"], 0)

    def test_combine_verdict_design_axis_fail_plan(self):
        axes = {k: "PASS" for k in AXES}
        axes["executability"] = "FAIL"
        payload, _ = self.run_case("b", axes=axes)
        self.assertEqual((payload["verdict"], payload["rewrite_target"]), ("fail", "plan"))

    def test_combine_verdict_axis_case_insensitive(self):
        axes = {k: "pass" for k in AXES}
        payload, _ = self.run_case("b2", axes=axes)
        self.assertEqual(payload["verdict"], "pass")

    def test_combine_verdict_score_zero_scenario(self):
        payload, _ = self.run_case("c", scores={"goal": 2, "adoption": 2, "boundary": 0})
        self.assertEqual((payload["verdict"], payload["rewrite_target"]), ("fail", "scenario"))

    def test_combine_verdict_average_below_threshold_scenario(self):
        payload, combined = self.run_case("d", scores={"goal": 1, "adoption": 1, "boundary": 1})
        self.assertEqual((payload["verdict"], payload["rewrite_target"]), ("fail", "scenario"))
        self.assertEqual(combined["scenario"]["average"], 1.0)

    def test_combine_verdict_average_rounding(self):
        payload, combined = self.run_case("d2", scores={"goal": 2, "adoption": 1, "boundary": 2})
        self.assertEqual(combined["scenario"]["average"], 1.667)
        self.assertEqual(payload["verdict"], "pass")

    def test_combine_verdict_both(self):
        axes = {k: "PASS" for k in AXES}
        axes["completeness"] = "FAIL"
        payload, _ = self.run_case("e", axes=axes, scores={"goal": 1, "adoption": 1, "boundary": 1})
        self.assertEqual((payload["verdict"], payload["rewrite_target"]), ("fail", "both"))

    def test_combine_verdict_resolved_gaps_order_design_then_scenario(self):
        history = [self.hist(1)]
        files = {1: (["D-1: a", "D-2: b"], ["S-1: c"])}
        d_res = [{"id": "D-1", "status": "resolved", "reason": "r"},
                 {"id": "D-2", "status": "unresolved", "reason": "r"}]
        s_res = [{"id": "S-1", "status": "resolved", "reason": "r"}]
        payload, combined = self.run_case(
            "f", attempt={"history": history, "files": files},
            d={"resolved": d_res}, s={"resolved": s_res})
        self.assertEqual([r["id"] for r in combined["resolved_gaps"]], ["D-1", "D-2", "S-1"])
        self.assertEqual(payload["resolved_gaps_count"], 3)

    def test_combine_verdict_refinement_clears_advisories(self):
        adv = [{"id": "A-1", "kind": "mergeable", "targets": ["S-1"], "basis": "b",
                "recommendation": "r"}]
        _, combined = self.run_case("g", attempt={"refinement_pending": True}, s={"advisories": adv})
        self.assertEqual(combined["advisories"], [])

    def test_combine_verdict_advisories_from_scenario_only(self):
        adv = [{"id": "A-1", "kind": "mergeable", "targets": ["S-1"], "basis": "b",
                "recommendation": "r"}]
        adv_d = [{"id": "A-9", "kind": "mergeable", "targets": ["S-1"], "basis": "b",
                  "recommendation": "r"}]
        _, combined = self.run_case("h", d={"advisories": adv_d}, s={"advisories": adv})
        self.assertEqual([a["id"] for a in combined["advisories"]], ["A-1"])

    def test_combine_verdict_read_only_no_lock_artifacts(self):
        task, bundle, it = self.open_attempt("ro", run_log=True)
        before = (task / "state.json").read_bytes()
        log_before = sorted(p.name for p in (task / "run").rglob("*") if p.is_file())
        result, out = self.combine(task, it, partial_result("design", bundle, it),
                                   partial_result("scenario", bundle, it),
                                   output=self.root / "elsewhere" / "out.json")
        self.ok(result)
        self.assertEqual((task / "state.json").read_bytes(), before)
        self.assertEqual(sorted(p.name for p in (task / "run").rglob("*") if p.is_file()), log_before)
        self.assertFalse(list(out.parent.glob("*.tmp")))


class CombineErrorsTest(CombineFixture):
    """S-3 — 오류 코드와 상태 불변."""

    def assert_rejected(self, task, it, design, scenario, code, *, iteration_arg=None):
        before = (task / "state.json").read_bytes()
        d = self.write_json(self.root / "in" / "d.json", design)
        s = self.write_json(self.root / "in" / "s.json", scenario)
        out = self.root / "out" / "combined.json"
        payload = self.err(run_cli(
            "design-gate", "combine", task, "--iteration", iteration_arg or it,
            "--design-result", d, "--scenario-result", s, "--output", out), code)
        self.assertEqual((task / "state.json").read_bytes(), before)
        self.assertFalse(out.exists())
        return payload

    def test_combine_errors_no_open_attempt(self):
        task = self.root / "a"
        make_pm_task(task)
        self.assert_rejected(task, 1, partial_result("design", "h", 1),
                             partial_result("scenario", "h", 1), "design_gate_iteration_invalid")

    def test_combine_errors_iteration_mismatch(self):
        task, bundle, it = self.open_attempt("b")
        self.assert_rejected(task, it, partial_result("design", bundle, it),
                             partial_result("scenario", bundle, it),
                             "design_gate_iteration_invalid", iteration_arg=it + 1)

    def test_combine_errors_stale_hash(self):
        task, bundle, it = self.open_attempt("c")
        self.assert_rejected(task, it, partial_result("design", "other", it),
                             partial_result("scenario", bundle, it), "design_gate_result_stale")
        self.assert_rejected(task, it, partial_result("design", bundle, it),
                             partial_result("scenario", "other", it), "design_gate_result_stale")
        missing = partial_result("scenario", bundle, it)
        del missing["input_bundle_hash"]
        self.assert_rejected(task, it, partial_result("design", bundle, it), missing,
                             "design_gate_result_stale")

    def test_combine_errors_stale_iteration(self):
        task, bundle, it = self.open_attempt("d")
        self.assert_rejected(task, it, partial_result("design", bundle, it + 1),
                             partial_result("scenario", bundle, it), "design_gate_result_stale")

    def invalid(self, name, mutate_design=None, mutate_scenario=None, **attempt):
        task, bundle, it = self.open_attempt(name, **attempt)
        design = partial_result("design", bundle, it)
        scenario = partial_result("scenario", bundle, it)
        if mutate_design:
            mutate_design(design)
        if mutate_scenario:
            mutate_scenario(scenario)
        payload = self.assert_rejected(task, it, design, scenario, "design_gate_partial_invalid")
        self.assertTrue(payload.get("detail"), payload)
        return payload

    def test_combine_errors_scope_mismatch(self):
        self.invalid("e1", lambda d: d.update(scope="scenario"))
        self.invalid("e2", None, lambda s: s.update(scope="all"))
        self.invalid("e3", lambda d: d.pop("scope"))

    def test_combine_errors_missing_axis_or_score(self):
        self.invalid("f1", lambda d: d["design"]["axes"].pop("recoverability"))
        self.invalid("f2", None, lambda s: s["scenario"]["scores"].pop("boundary"))

    def test_combine_errors_score_not_number(self):
        self.invalid("g1", None, lambda s: s["scenario"]["scores"].update(goal="2"))
        self.invalid("g2", None, lambda s: s["scenario"]["scores"].update(goal=True))

    def test_combine_errors_resolved_status_invalid(self):
        files = {1: (["D-1: a"], [])}
        self.invalid("h", lambda d: d.update(resolved_gaps=[
            {"id": "D-1", "status": "done", "reason": "r"}]),
            history=[self.hist(1)], files=files)

    def test_combine_errors_resolved_id_set_mismatch(self):
        files = {1: (["D-1: a", "D-2: b"], ["S-1: c"])}
        attempt = {"history": [self.hist(1)], "files": files}
        ok_d = [{"id": "D-1", "status": "resolved", "reason": "r"},
                {"id": "D-2", "status": "resolved", "reason": "r"}]
        ok_s = [{"id": "S-1", "status": "resolved", "reason": "r"}]
        # 누락
        self.invalid("i1", lambda d: d.update(resolved_gaps=ok_d[:1]),
                     lambda s: s.update(resolved_gaps=ok_s), **attempt)
        # 초과
        self.invalid("i2", lambda d: d.update(resolved_gaps=ok_d + [
            {"id": "D-3", "status": "resolved", "reason": "r"}]),
            lambda s: s.update(resolved_gaps=ok_s), **attempt)
        # scope 교차(시나리오 id를 설계 쪽에)
        self.invalid("i3", lambda d: d.update(resolved_gaps=ok_d + ok_s),
                     lambda s: s.update(resolved_gaps=[]), **attempt)
        # 이전 지적이 없는데 resolved_gaps가 있음
        self.invalid("i4", lambda d: d.update(resolved_gaps=ok_d[:1]))


class CombineRecordTest(CombineFixture):
    """S-4 — combine 출력이 record에서 수락된다."""

    def test_combine_record_pass_accepted(self):
        task, bundle, it = self.open_attempt("p", run_log=True)
        result, out = self.combine(task, it, partial_result("design", bundle, it),
                                   partial_result("scenario", bundle, it))
        self.assertEqual(self.ok(result)["verdict"], "pass")
        rec = self.ok(run_cli("design-gate", "record", task, "--iteration", it,
                              "--verdict", "pass", "--evaluator-result", out))
        self.assertEqual(rec["status"], "pass")
        state = self.state(task)
        self.assertEqual(state["design_gate"]["status"], "pass")
        row = next(r for r in state["rows"] if r.get("key") == "plan.design_gate")
        self.assertIn(row["status"], ("done", "complete", "completed"))

    def test_combine_record_rewrite_target_matches_combine(self):
        task, bundle, it = self.open_attempt("r", run_log=True)
        axes = {k: "PASS" for k in AXES}
        axes["completeness"] = "FAIL"
        result, out = self.combine(
            task, it, partial_result("design", bundle, it, axes=axes),
            partial_result("scenario", bundle, it, scores={"goal": 1, "adoption": 1, "boundary": 1}))
        combined = self.ok(result)
        self.assertEqual(combined["rewrite_target"], "both")
        self.ok(run_cli("design-gate", "record", task, "--iteration", it, "--verdict", "rewrite",
                        "--rewrite-target", combined["rewrite_target"], "--evaluator-result", out))
        dg = self.state(task)["design_gate"]
        self.assertEqual(dg["status"], "fail")
        self.assertEqual(dg["last_rewrite_target"], combined["rewrite_target"])

    def test_combine_record_matches_single_call_format(self):
        """결합 결과 파일과 단일 호출 형식 파일로 기록한 history·gate.resolved의 필드 집합이 같다."""
        shapes = []
        for name, use_combine in (("viacombine", True), ("single", False)):
            task, bundle, it = self.open_attempt(name, run_log=True)
            if use_combine:
                result, out = self.combine(task, it, partial_result("design", bundle, it),
                                           partial_result("scenario", bundle, it))
                self.ok(result)
            else:
                out = self.write_json(self.root / "single.json", {
                    "input_bundle_hash": bundle, "iteration": it,
                    "design": {"axes": {k: "PASS" for k in AXES}, "gaps": []},
                    "scenario": {"scores": {"goal": 2, "adoption": 2, "boundary": 2},
                                 "average": 2.0, "gaps": []},
                    "resolved_gaps": [], "advisories": [], "verdict": "pass",
                    "rewrite_target": None})
            self.ok(run_cli("design-gate", "record", task, "--iteration", it,
                            "--verdict", "pass", "--evaluator-result", out))
            history = self.state(task)["design_gate"]["history"][-1]
            events = []
            for log in (task / "run").glob("run-log-*.jsonl"):
                for line in log.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        events.append(json.loads(line))
            resolved = [e for e in events if e.get("event") == "gate.resolved"]
            self.assertEqual(len(resolved), 1, events)
            shapes.append((sorted(history), sorted(resolved[0]),
                           sorted((resolved[0].get("data") or {}))))
            self.assertEqual(resolved[0]["data"]["verdict"], "approved")
        self.assertEqual(shapes[0], shapes[1])


def make_fixture(target: Path, docs: Path) -> dict:
    """PM 경로 임시 태스크를 만들고 design-gate start --iteration 1까지 실행한다."""
    make_pm_task(target, docs=docs)
    completed, payload = run_cli("design-gate", "start", target, "--iteration", 1)
    if completed.returncode != 0 or not payload or not payload.get("ok"):
        raise RuntimeError(f"design-gate start failed: {completed.stdout}{completed.stderr}")
    return {"task_path": str(target), "bundle_hash": payload["bundle_hash"]}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="design-gate 병렬 판정 시험 / 픽스처 생성")
    parser.add_argument("--make-fixture", metavar="<대상 폴더>")
    parser.add_argument("--docs", metavar="<TASK.md·PLAN.md·TEST-SCENARIO.md 폴더>")
    args, rest = parser.parse_known_args(argv)
    if args.make_fixture:
        if not args.docs:
            parser.error("--make-fixture requires --docs")
        target, docs = Path(args.make_fixture).resolve(), Path(args.docs).resolve()
        missing = [n for n in DOC_NAMES if not (docs / n).is_file()]
        if missing:
            print(json.dumps({"ok": False, "error": f"docs missing: {missing}"}, ensure_ascii=False))
            return 1
        print(json.dumps(make_fixture(target, docs), ensure_ascii=False))
        return 0
    unittest.main(argv=[sys.argv[0], *rest])
    return 0


if __name__ == "__main__":
    sys.exit(main())
