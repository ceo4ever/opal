"""
@header {
  "module": "test_task176_variant_settings",
  "layer": "test",
  "domain": "opal-skill-tester",
  "description": "TASK-176 S-1~S-5 (RED-first) — opst 변형 토큰(`design=`·`impl=`) 파싱, 설정 적용·기록, FW 지문 비교 무효, 품질 하한 판정, TEST 수정 반복 수집, --max-parallel 동시 실행 상한을 검증한다. 실제 모델은 호출하지 않고 PATH 앞의 가짜 `claude`만 쓴다.",
  "exports": ["test_s1_parse_full_tokens", "test_s1_parse_design_only_effort_omitted_and_order_free", "test_s1_parse_no_tokens_is_empty_settings", "test_s1_parse_invalid_values_rejected_with_variant_setting_invalid", "test_s1_stripped_command_is_looked_up_in_profiles", "test_s2_design_and_impl_settings_applied_and_recorded", "test_s3_framework_mismatch_marks_comparison_invalid", "test_s3_framework_match_shows_quality_floor_and_keeps_existing_items", "test_s4_quality_floor_verdicts_and_metric_ranges", "test_s4_test_fix_iterations_counts_fix_rows", "test_s5_max_parallel_caps_concurrency_and_mixes_variants", "test_s5_without_max_parallel_all_start_together"]
}
"""
import hashlib
import importlib.util
import inspect
import json
import os
import pathlib
import re
import stat
import sys

import pytest

SKILL_DIR = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "skill_tester.py"
SPEC = importlib.util.spec_from_file_location("skill_tester", SCRIPT)
skill_tester = importlib.util.module_from_spec(SPEC)
sys.path.insert(0, str(SCRIPT.parent))
SPEC.loader.exec_module(skill_tester)

IMPL_AGENTS = ("opal-task-agent", "opal-be-agent", "opal-fe-agent")
JUDGE_AGENTS = ("opal-evaluator-agent", "opal-test-agent", "opal-convention-checker", "opal-security-checker")


# ───────────────────────── S-1 변형 파싱 ─────────────────────────

def _parse(v):
    fn = getattr(skill_tester, "parse_variant", None)
    assert fn is not None, "parse_variant 미구현"
    return fn(v)


def test_s1_parse_full_tokens():
    r = _parse("//opds design=opus/high impl=sonnet/low")
    assert r["command"] == "//opds"
    assert r["design"] == {"model": "opus", "effort": "high"}
    assert r["impl"] == {"model": "sonnet", "effort": "low"}


def test_s1_parse_design_only_effort_omitted_and_order_free():
    r = _parse("//opds design=opus")
    assert r["command"] == "//opds"
    assert r["design"] == {"model": "opus", "effort": None}
    assert r["impl"] is None
    r2 = _parse("//opds impl=sonnet/low design=opus/high")
    assert r2["design"] == {"model": "opus", "effort": "high"}
    assert r2["impl"] == {"model": "sonnet", "effort": "low"}


def test_s1_parse_no_tokens_is_empty_settings():
    r = _parse("//opds")
    assert r == {"command": "//opds", "design": None, "impl": None}


@pytest.mark.parametrize("bad", ["//opds design=", "//opds impl=a/b/c", "//opds bogus=x", "//opds impl="])
def test_s1_parse_invalid_values_rejected_with_variant_setting_invalid(bad):
    fn = getattr(skill_tester, "parse_variant", None)
    assert fn is not None, "parse_variant 미구현"
    with pytest.raises(ValueError) as ei:
        fn(bad)
    assert str(ei.value).startswith("variant_setting_invalid")


def test_s1_stripped_command_is_looked_up_in_profiles():
    r = _parse("//opds design=opus/high impl=sonnet/low")
    assert r["command"].lstrip("/") in skill_tester.PROFILES
    # 미등록 Pilot 커맨드 오류(variant_unprofiled)와 설정 오류(variant_setting_invalid)는 다른 오류다.
    with pytest.raises(ValueError) as ei:
        _parse("//opds design=")
    assert "variant_unprofiled" not in str(ei.value)


# ───────────────────────── 공통 fixture: 임시 시나리오 + 가짜 claude ─────────────────────────

FAKE_CLAUDE = """#!{py}
import json, os, sys, time
cwd = os.getcwd()
rd = os.path.dirname(cwd)
log = os.environ.get("FAKE_CLAUDE_TIMES")
t0 = time.time()
if log:
    with open(log, "a") as f:
        f.write(json.dumps({{"ev": "start", "run": os.path.basename(rd), "t": t0}}) + "\\n")
json.dump(sys.argv[1:], open(os.path.join(rd, "argv.json"), "w"))
json.dump(dict(os.environ), open(os.path.join(rd, "env.json"), "w"))
time.sleep(float(os.environ.get("FAKE_CLAUDE_SLEEP", "0")))
if log:
    with open(log, "a") as f:
        f.write(json.dumps({{"ev": "end", "run": os.path.basename(rd), "t": time.time()}}) + "\\n")
model = os.environ.get("FAKE_CLAUDE_MODEL", "sonnet")
print(json.dumps({{"result": "ok", "total_cost_usd": 0.01, "num_turns": 1,
                  "usage": {{"output_tokens": 1}}, "modelUsage": {{model: {{}}}}}}))
"""


@pytest.fixture
def env(tmp_path, monkeypatch):
    scen = tmp_path / "scenarios"
    base = scen / "base1"
    for rel, body in {"_opal/AGENT.md": "x", "_opal/code-scan.json": "{}", "_opal/MEMORY.json": "{}",
                      "docs/PROJECT.md": "x", "_gitignore": "node_modules\n"}.items():
        (base / rel).parent.mkdir(parents=True, exist_ok=True)
        (base / rel).write_text(body, encoding="utf-8")
    sd = scen / "sc1"
    sd.mkdir()
    (sd / "request.md").write_text("do it", encoding="utf-8")
    (sd / "scenario.json").write_text(json.dumps({
        "id": "sc1", "mode": "smoke", "base": "base1", "target_pilots": ["opds"],
        "default_variant": "//opds", "utterance": "{variant} {request}", "timeout_min": 1, "estimate": "1m",
    }), encoding="utf-8")
    agents = tmp_path / "installed_agents"
    agents.mkdir()
    for i, name in enumerate(IMPL_AGENTS + JUDGE_AGENTS):
        (agents / f"{name}.md").write_text(
            f"---\nname: {name}\ndescription: d{i}\nmodel: opus\neffort: high\n---\n\n# body {name}\n本文 {i}\n",
            encoding="utf-8")
    bindir = tmp_path / "bin"
    bindir.mkdir()
    fake = bindir / "claude"
    fake.write_text(FAKE_CLAUDE.format(py=sys.executable), encoding="utf-8")
    fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("PATH", f"{bindir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setattr(skill_tester, "SCENARIOS", scen)
    monkeypatch.setattr(skill_tester, "AGENT_SRC_DIR", agents, raising=False)
    monkeypatch.setattr(skill_tester, "_install_drift", lambda: [])
    monkeypatch.setenv("FAKE_CLAUDE_MODEL", "sonnet")
    return {"tmp": tmp_path, "agents": agents, "times": tmp_path / "times.jsonl"}


def _run(env, variants, repeat=1, **kw):
    outdir = env["tmp"] / "out"
    try:
        skill_tester.run_scenario("sc1", variants, repeat, str(outdir), project_root=str(env["tmp"] / "proj"),
                                  no_record=True, **kw)
    except SystemExit:
        pass
    return outdir


def _runs_by_variant(outdir):
    res = {}
    for p in sorted(outdir.iterdir()):
        if (p / "run.json").exists():
            res[json.loads((p / "run.json").read_text(encoding="utf-8"))["variant"]] = p
    return res


def _split_fm(text):
    _, fm, body = text.split("---\n", 2)
    return dict(l.split(": ", 1) for l in fm.strip().splitlines()), body


# ───────────────────────── S-2 설정 적용·기록 ─────────────────────────

def test_s2_design_and_impl_settings_applied_and_recorded(env, monkeypatch):
    monkeypatch.setenv("CLAUDE_CODE_SUBAGENT_MODEL", "haiku")
    v_set, v_none = "//opds design=opus/high impl=sonnet/low", "//opds"
    outdir = _run(env, [v_set, v_none])
    runs = _runs_by_variant(outdir)
    assert set(runs) == {v_set, v_none}, "두 변형이 모두 실행·run.json 기록돼야 한다"

    rd = runs[v_set]
    argv = json.loads((rd / "argv.json").read_text())
    assert "--model" in argv and argv[argv.index("--model") + 1] == "opus"
    assert "--effort" in argv and argv[argv.index("--effort") + 1] == "high"
    assert "CLAUDE_CODE_SUBAGENT_MODEL" not in json.loads((rd / "env.json").read_text())

    adir = rd / "repo" / ".claude" / "agents"
    assert sorted(p.name for p in adir.glob("*.md")) == sorted(f"{n}.md" for n in IMPL_AGENTS)
    for n in IMPL_AGENTS:
        fm, body = _split_fm((adir / f"{n}.md").read_text(encoding="utf-8"))
        ofm, obody = _split_fm((env["agents"] / f"{n}.md").read_text(encoding="utf-8"))
        assert fm["model"] == "sonnet" and fm["effort"] == "low"
        assert body == obody
        assert {k: v for k, v in fm.items() if k not in ("model", "effort")} == \
            {k: v for k, v in ofm.items() if k not in ("model", "effort")}
    for n in JUDGE_AGENTS:
        assert not (adir / f"{n}.md").exists()

    settings = json.loads((rd / "run.json").read_text(encoding="utf-8"))["settings"]
    assert settings["declared"] == {"design": {"model": "opus", "effort": "high"},
                                    "impl": {"model": "sonnet", "effort": "low"}}
    assert settings["applied"]["models"] == ["sonnet"]
    ov = settings["applied"]["agent_overrides"]
    assert set(ov) == set(IMPL_AGENTS)
    for n in IMPL_AGENTS:
        assert ov[n] == hashlib.sha256((adir / f"{n}.md").read_bytes()).hexdigest()

    rn = runs[v_none]
    argv_n = json.loads((rn / "argv.json").read_text())
    assert "--model" not in argv_n and "--effort" not in argv_n
    assert not (rn / "repo" / ".claude" / "agents").exists()
    sn = json.loads((rn / "run.json").read_text(encoding="utf-8"))["settings"]
    assert sn["declared"] == {"design": None, "impl": None}


# ───────────────────────── S-3/S-4 보고서 ─────────────────────────

def _make_runs(outdir, specs):
    """specs: [(variant, rep, framework, metrics)]. collect_run·judge_run을 대체할 입력만 만든다."""
    outdir.mkdir(parents=True, exist_ok=True)
    table = {}
    for variant, rep, fw, metrics in specs:
        rd = outdir / f"{skill_tester._slug(variant)}-r{rep}"
        rd.mkdir()
        (rd / "run.json").write_text(json.dumps({"scenario": "sc1", "mode": "function", "variant": variant, "rep": rep,
                                                 "start": 1000.0, "end": 1060.0, "framework": fw}), encoding="utf-8")
        table[rd.name] = {"run": rd.name, "variant": variant, "rep": rep, "framework": fw, **metrics}
    return table


@pytest.fixture
def patched_report(monkeypatch):
    def install(table):
        monkeypatch.setattr(skill_tester, "collect_run", lambda rd, s: dict(table[rd.name]))
        monkeypatch.setattr(skill_tester, "judge_run",
                            lambda m, s: (m.get("_verdict", "PASS"), []))
    return install


S = {"id": "sc1", "mode": "function", "title": "t"}


def _m(hidden, verdict="PASS", wall=10.0, cost=1.0, fix=0):
    return {"hidden_pass_rate": hidden, "_verdict": verdict, "wall_min": wall, "cost_usd": cost,
            "test_fix_iterations": fix, "turns": 1, "subagent_runs": 1, "gate_iterations": 1}


def test_s3_framework_mismatch_marks_comparison_invalid(tmp_path, patched_report):
    out = tmp_path / "mismatch"
    table = _make_runs(out, [("//opds", 1, "1.0+aaaaaa", _m(1.0)), ("//opds", 2, "1.0+aaaaaa", _m(1.0)),
                             ("//opds design=a", 1, "1.0+bbbbbb", _m(1.0)), ("//opds design=a", 2, "1.0+bbbbbb", _m(1.0))])
    patched_report(table)
    skill_tester.write_report(out, S)
    txt = (out / "REPORT.md").read_text(encoding="utf-8")
    assert "비교 무효 — FW 버전 상이" in txt
    assert "1.0+aaaaaa" in txt and "1.0+bbbbbb" in txt
    assert "품질 하한" not in txt
    assert "하한 충족" not in txt


def test_s3_framework_match_shows_quality_floor_and_keeps_existing_items(tmp_path, patched_report):
    out = tmp_path / "match"
    table = _make_runs(out, [("//opds", 1, "1.0+aaaaaa", _m(1.0)), ("//opds", 2, "1.0+aaaaaa", _m(1.0)),
                             ("//opds design=a", 1, "1.0+aaaaaa", _m(1.0)), ("//opds design=a", 2, "1.0+aaaaaa", _m(1.0))])
    patched_report(table)
    rep = skill_tester.write_report(out, S)
    txt = (out / "REPORT.md").read_text(encoding="utf-8")
    assert "비교 무효" not in txt
    assert "품질 하한" in txt
    assert any("//opds design=a" in l and "하한 충족" in l for l in txt.splitlines())
    assert "## 불합격 사유와 경고" in txt and "| 실행 | 판정 |" in txt
    assert len(rep["runs"]) == 4


def test_s4_quality_floor_verdicts_and_metric_ranges(tmp_path, patched_report):
    out = tmp_path / "floor"
    fw = "1.0+aaaaaa"
    table = _make_runs(out, [
        ("//opds", 1, fw, _m(1.0, wall=10, cost=1.0, fix=0)), ("//opds", 2, fw, _m(1.0, wall=20, cost=2.0, fix=2)),
        ("//opds design=a", 1, fw, _m(1.0, wall=8, cost=0.5)), ("//opds design=a", 2, fw, _m(1.0, wall=12, cost=0.7)),
        ("//opds design=b", 1, fw, _m(1.0)), ("//opds design=b", 2, fw, _m(0.75, verdict="FAIL")),
        ("//opds design=c", 1, fw, _m(1.0)), ("//opds design=c", 2, fw, _m(1.0, verdict="FAIL")),
    ])
    patched_report(table)
    skill_tester.write_report(out, S)
    lines = (out / "REPORT.md").read_text(encoding="utf-8").splitlines()

    def verdict_line(v):
        return next((l for l in lines if f"{v} " in l + " " and "하한" in l and "//opds design=" in l), "")

    assert "하한 충족" in verdict_line("//opds design=a")
    for v in ("//opds design=b", "//opds design=c"):
        assert "하한 미충족(결정 대상 아님)" in verdict_line(v), v

    rng = r"\d+(\.\d+)?\s*\(\s*\d+(\.\d+)?\s*~\s*\d+(\.\d+)?\s*\)"
    for key in ("wall_min", "cost_usd", "test_fix_iterations"):
        row = next((l for l in lines if l.startswith(f"| {key} |")), None)
        assert row is not None, key
        assert len(re.findall(rng, row)) == 4, (key, row)


def test_s4_test_fix_iterations_counts_fix_rows(tmp_path, monkeypatch):
    monkeypatch.setattr(skill_tester, "STATE_TOOL", pathlib.Path("/usr/bin/true"))
    rd = tmp_path / "run1"
    task = rd / "repo" / "tasks" / "001-t"
    task.mkdir(parents=True)
    (rd / "run.json").write_text(json.dumps({"scenario": "sc1", "mode": "smoke", "variant": "//opds", "rep": 1,
                                             "start": 1000.0, "end": 1060.0}), encoding="utf-8")
    (task / "state.json").write_text(json.dumps({
        "skill": "opds", "current_status": "in_progress",
        "rows": [{"key": "a", "stage": "execute", "item": "구현", "status": "done"},
                 {"key": "b", "stage": "test", "item": "fix 작업 (1/3)", "status": "done"},
                 {"key": "c", "stage": "test", "item": "fix 작업 (2/3)", "status": "done"},
                 {"key": "d", "stage": "test", "item": "TEST 게이트", "status": "done"}]}), encoding="utf-8")
    m = skill_tester.collect_run(rd, {"id": "sc1", "mode": "smoke"})
    assert m.get("test_fix_iterations") == 2


# ───────────────────────── S-5 --max-parallel ─────────────────────────

def _events(env):
    evs = [json.loads(l) for l in env["times"].read_text().splitlines() if l.strip()]
    return sorted(evs, key=lambda e: (e["t"], e["ev"] == "start"))


def _max_concurrency(evs):
    cur = peak = 0
    for e in sorted(evs, key=lambda e: (e["t"], e["ev"] == "start")):
        cur += 1 if e["ev"] == "start" else -1
        peak = max(peak, cur)
    return peak


def test_s5_max_parallel_caps_concurrency_and_mixes_variants(env, monkeypatch):
    assert "max_parallel" in inspect.signature(skill_tester.run_scenario).parameters, "max_parallel 미구현"
    monkeypatch.setenv("FAKE_CLAUDE_TIMES", str(env["times"]))
    monkeypatch.setenv("FAKE_CLAUDE_SLEEP", "0.6")
    _run(env, ["//opds", "//opds design=opus"], repeat=2, max_parallel=2)
    evs = _events(env)
    assert sum(e["ev"] == "start" for e in evs) == 4
    assert _max_concurrency(evs) <= 2
    first_two = [e["run"] for e in evs if e["ev"] == "start"][:2]
    variants = {json.loads((env["tmp"] / "out" / r / "run.json").read_text())["variant"] for r in first_two}
    assert len(variants) == 2, f"첫 배치가 한 변형뿐: {first_two}"


def test_s5_without_max_parallel_all_start_together(env, monkeypatch):
    monkeypatch.setenv("FAKE_CLAUDE_TIMES", str(env["times"]))
    monkeypatch.setenv("FAKE_CLAUDE_SLEEP", "0.6")
    _run(env, ["//opds", "//opds design=opus"], repeat=2)
    evs = _events(env)
    assert sum(e["ev"] == "start" for e in evs) == 4
    assert _max_concurrency(evs) == 4
