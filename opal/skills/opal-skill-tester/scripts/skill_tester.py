#!/usr/bin/env python3
"""
@header {
  "module": "skill_tester",
  "layer": "util",
  "domain": "opal-skill-tester",
  "description": "opal-skill-tester 실행기. scenarios/ 카탈로그 조회(list)·규격 검사(validate)·격리 저장소에서 claude -p 헤드리스 세션 실행과 지표 수집·판정·보고(run)·보고서 재생성(report, --save-baseline 지원)을 수행한다. 기본은 단일 변형 실행이고 --variant를 여러 번 주면 비교, --repeat로 반복한다. 기반 저장소의 _opal·_gitignore는 복사 시 .opal·.gitignore로 복원한다.",
  "exports": ["main", "load_scenarios", "validate_scenario", "run_scenario", "collect_run", "judge_run", "write_report"]
}
"""
import argparse
import datetime
import glob
import json
import os
import pathlib
import re
import shutil
import signal
import subprocess
import sys
import time

SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent
SCENARIOS = SKILL_DIR / "scenarios"
MODES = ("smoke", "function", "judgment")
OPAL = pathlib.Path.home() / ".opal"
STATE_TOOL = OPAL / "tools" / "state-tool" / "run.sh"
RENAMES = {"_opal": ".opal", "_gitignore": ".gitignore"}
REQUIRED_BASE = ["_opal/AGENT.md", "_opal/code-scan.json", "_opal/MEMORY.json", "docs/PROJECT.md", "_gitignore"]


def out(obj, code=0):
    print(json.dumps(obj, ensure_ascii=False))
    sys.exit(code)


def load_scenarios():
    items = []
    for p in sorted(SCENARIOS.glob("*/scenario.json")):
        if p.parent.name.startswith("_"):
            continue
        try:
            items.append(json.loads(p.read_text(encoding="utf-8")))
        except json.JSONDecodeError as e:
            items.append({"id": p.parent.name, "_error": f"scenario.json JSON 오류: {e}"})
    return items


def validate_scenario(sid):
    d = SCENARIOS / sid
    errs = []
    sj = d / "scenario.json"
    if not sj.exists():
        return [f"{sid}: scenario.json 없음"]
    try:
        s = json.loads(sj.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"{sid}: scenario.json JSON 오류 {e}"]
    for k in ("id", "mode", "base", "default_variant", "utterance", "timeout_min", "estimate"):
        if k not in s:
            errs.append(f"필드 누락: {k}")
    if s.get("id") != sid:
        errs.append("id가 폴더명과 다름")
    if s.get("mode") not in MODES:
        errs.append(f"mode는 {MODES} 중 하나")
    ut = s.get("utterance", "")
    if "{variant}" not in ut or "{request}" not in ut:
        errs.append("utterance에 {variant}·{request} 토큰 필요")
    if not (d / "request.md").exists():
        errs.append("request.md 없음")
    base = SCENARIOS / s.get("base", "")
    if not base.is_dir():
        errs.append(f"base 폴더 없음: {s.get('base')}")
    else:
        for rel in REQUIRED_BASE:
            if not (base / rel).exists():
                errs.append(f"base 필수 파일 없음: {rel}")
        if (base / ".opal").exists():
            errs.append("base에 .opal 금지(_opal로 보관 — 프로젝트 오인 방지)")
    if s.get("mode") == "function":
        if not list((d / "hidden").glob("test_*.py")):
            errs.append("function 모드는 hidden/test_*.py 필요")
        if not s.get("existing_test_cmd"):
            errs.append("function 모드는 existing_test_cmd 필요")
    if s.get("mode") == "judgment":
        dps = s.get("decision_points") or []
        if not dps:
            errs.append("judgment 모드는 decision_points 필요")
        for dp in dps:
            if not dp.get("id") or not dp.get("keywords"):
                errs.append(f"decision_point에 id·keywords 필요: {dp}")
    req = (d / "request.md").read_text(encoding="utf-8") if (d / "request.md").exists() else ""
    if "hidden" in req or "test_hidden" in req:
        errs.append("request.md가 숨은 테스트를 언급함")
    return errs


def _slug(v):
    return re.sub(r"[^a-z0-9]+", "-", v.lower()).strip("-") or "variant"


def _copy_base(src, dst):
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", ".git"))
    for old, new in RENAMES.items():
        if (dst / old).exists():
            (dst / old).rename(dst / new)


def _git(repo, *a):
    return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True)


def _install_drift():
    """소스 checkout 위치에서 실행할 때 설치본과 다르면 경고한다."""
    src_root = SKILL_DIR.parent.parent.parent  # opal/skills/<name> → repo
    pairs = [("opal/tools/state-tool/state_tool.py", "tools/state-tool/state_tool.py")]
    warns = []
    for s, d in pairs:
        a, b = src_root / s, OPAL / d
        if a.exists() and b.exists() and a.read_bytes() != b.read_bytes():
            warns.append(f"설치본이 소스와 다름: {d} — install 후 실행 권장")
    return warns


def run_scenario(sid, variants, repeat, outdir, save_baseline=False):
    errs = validate_scenario(sid)
    if errs:
        out({"ok": False, "command": "run", "error": "scenario_invalid", "detail": errs}, 1)
    s = json.loads((SCENARIOS / sid / "scenario.json").read_text(encoding="utf-8"))
    variants = variants or [s["default_variant"]]
    if shutil.which("claude") is None:
        out({"ok": False, "command": "run", "error": "claude_cli_missing"}, 1)
    outdir = pathlib.Path(outdir or f"/tmp/opal-skill-tester/{sid}-{datetime.datetime.now():%Y%m%d-%H%M%S}")
    outdir.mkdir(parents=True, exist_ok=True)
    runs = []
    for v in variants:
        for k in range(1, repeat + 1):
            rd = outdir / f"{_slug(v)}-r{k}"
            rd.mkdir()
            repo = rd / "repo"
            _copy_base(SCENARIOS / s["base"], repo)
            ov = SCENARIOS / sid / "overlay"
            if ov.is_dir():
                shutil.copytree(ov, repo, dirs_exist_ok=True)
            _git(repo, "init", "-q", "-b", "main")
            _git(repo, "add", "-A")
            _git(repo, "-c", "user.name=skill-tester", "-c", "user.email=skill-tester@local", "commit", "-q", "-m", f"init: {sid}")
            shutil.copy(SCENARIOS / sid / "request.md", rd / "REQUEST.md")
            utt = s["utterance"].format(variant=v, request=str(rd / "REQUEST.md"))
            meta = {"scenario": sid, "mode": s["mode"], "variant": v, "rep": k, "utterance": utt, "start": time.time()}
            rf = open(rd / "result.json", "w")
            ef = open(rd / "stderr.txt", "w")
            p = subprocess.Popen(["claude", "-p", utt, "--permission-mode", "auto", "--output-format", "json"],
                                 cwd=repo, stdout=rf, stderr=ef, start_new_session=True)
            runs.append((rd, meta, p, rf, ef))
    deadline = time.time() + s["timeout_min"] * 60
    for rd, meta, p, rf, ef in runs:
        try:
            p.wait(timeout=max(1, deadline - time.time()))
            meta["exit"], meta["timeout"] = p.returncode, False
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGTERM)
            meta["exit"], meta["timeout"] = None, True
        meta["end"] = time.time()
        rf.close(); ef.close()
        (rd / "run.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    report = write_report(outdir, s)
    if save_baseline:
        _save_baseline(s, report)
    out({"ok": True, "command": "run", "out": str(outdir), "report": str(outdir / "REPORT.md"),
         "verdicts": {r["run"]: r["verdict"] for r in report["runs"]}, "warnings": _install_drift()})


def _pt(ts):
    for f in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.datetime.strptime(ts, f)
        except (TypeError, ValueError):
            pass
    return None


def _find_state(repo):
    c = sorted(glob.glob(str(repo / ".opal-worktrees" / "*" / "tasks" / "*" / "state.json"))) + \
        sorted(glob.glob(str(repo / "tasks" / "*" / "state.json")))
    return pathlib.Path(c[0]) if c else None


def collect_run(rd, s):
    meta = json.loads((rd / "run.json").read_text(encoding="utf-8"))
    m = {"run": rd.name, "variant": meta["variant"], "rep": meta["rep"], "timeout": meta.get("timeout"),
         "wall_min": round((meta["end"] - meta["start"]) / 60, 1)}
    try:
        r = json.loads((rd / "result.json").read_text(encoding="utf-8"))
        u = r.get("usage") or {}
        m.update(cost_usd=round(r.get("total_cost_usd") or 0, 2), turns=r.get("num_turns"),
                 output_tokens=u.get("output_tokens"), result_text=(r.get("result") or "")[-3000:])
    except (json.JSONDecodeError, OSError):
        m["result_text"] = ""
    repo = rd / "repo"
    sp = _find_state(repo)
    if not sp:
        m["task_found"] = False
        return m
    tdir = sp.parent
    st = json.loads(sp.read_text(encoding="utf-8"))
    code = pathlib.Path(st.get("worktree") or repo)
    m.update(task_found=True, task=tdir.name, actor=st.get("actor"), status=st.get("current_status"),
             pipeline_complete=st.get("current_status") in ("completed_unmerged", "done"))
    v = subprocess.run([str(STATE_TOOL), "validate", str(tdir)], capture_output=True, text=True)
    try:
        m["state_valid"] = json.loads(v.stdout).get("violations_count", 1) == 0
    except json.JSONDecodeError:
        m["state_valid"] = False
    pend = (st.get("run_log") or {}).get("pending_events") or []
    m["runlog_pending"] = len(pend)
    if pend:
        m["runlog_first_pending"] = {k: pend[0].get(k) for k in ("event", "task_step", "summary", "data")}
    dg = st.get("design_gate")
    gh = tdir / ".scenario-gate-history.json"
    gate_ok, iters = False, 0
    if dg:
        gate_ok, iters = dg.get("status") == "pass", len(dg.get("history") or [])
    elif gh.exists():
        h = json.loads(gh.read_text(encoding="utf-8"))
        gate_ok, iters = bool(h) and h[-1].get("verdict") == "pass", len(h)
    tsj = tdir / "test-scenario.json"
    sc_ok = False
    if tsj.exists():
        sc = json.loads(tsj.read_text(encoding="utf-8")).get("scenarios") or []
        sc_ok = bool(sc) and all((x.get("result") or x.get("status")) == "pass" for x in sc)
    m.update(gate_iterations=iters, gate_evidence=gate_ok and sc_ok)
    base = st.get("worktree") and _git(code, "rev-list", "--count", "main..HEAD").stdout.strip()
    m["checkpoint_commits"] = int(base) if base and base.isdigit() else 0
    evs = [json.loads(l) for f in sorted(glob.glob(str(tdir / "run" / "run-log-*.jsonl"))) for l in open(f) if l.strip()] + pend
    m["subagent_runs"] = sum(e.get("event") == "worker.started" for e in evs)
    m["worker_blocked"] = sum(e.get("event") == "worker.blocked" for e in evs)
    m["pm_decision_request"] = any(e.get("event") == "pm.report" and (e.get("data") or {}).get("report_type") == "decision_request" for e in evs)
    m["phase_min"] = _phases(evs)
    al = tdir / "AGENTIC-LOG.md"
    txt = al.read_text(encoding="utf-8") if al.exists() else ""
    m["log_error"] = len(re.findall(r"\|\s*`?ERROR`?\s*\|", txt))
    m["log_fix"] = len(re.findall(r"\|\s*`?FIX`?\s*\|", txt))
    m["_search_text"] = m.get("result_text", "") + txt + ((tdir / "STATE.md").read_text(encoding="utf-8") if (tdir / "STATE.md").exists() else "")
    if s.get("existing_test_cmd"):
        e = subprocess.run(s["existing_test_cmd"], cwd=code, capture_output=True, text=True)
        m["existing_tests_ok"] = e.returncode == 0
    hidden = sorted((SCENARIOS / s["id"] / "hidden").glob("test_*.py"))
    if hidden:
        h = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *map(str, hidden)],
                           cwd=code, capture_output=True, text=True, env={**os.environ, "SUT_REPO": str(code)})
        last = (h.stdout.strip().splitlines() or [""])[-1]
        passed = int((re.search(r"(\d+) passed", last) or [0, 0])[1])
        failed = int((re.search(r"(\d+) failed", last) or [0, 0])[1]) + int((re.search(r"(\d+) error", last) or [0, 0])[1])
        m["hidden_summary"] = last
        m["hidden_pass_rate"] = round(passed / (passed + failed), 3) if passed + failed else 0.0
        m["hidden_failed"] = [l.split("::")[-1].split(" ")[0] for l in h.stdout.splitlines() if l.startswith("FAILED")]
    return m


def _phases(evs):
    sc = [e for e in evs if e.get("event") == "state.changed"]
    ts = [_pt(e.get("timestamp")) for e in evs if _pt(e.get("timestamp"))]
    if not ts:
        return {}
    def at(step, to):
        xs = [_pt(e["timestamp"]) for e in sc if e.get("task_step") == step and (e.get("data") or {}).get("to") == to]
        return min(xs) if xs else None
    marks = [min(ts), at("execute.implement", "in_progress"), at("execute.implement", "done"),
             at("test.pm_gate", "done"), at("close.final", "done")]
    names = ["design", "execute", "test", "close"]
    return {n: round((b - a).total_seconds() / 60, 1) for n, a, b in zip(names, marks, marks[1:]) if a and b}


def judge_run(m, s):
    fails = []
    if m.get("timeout"):
        fails.append("timeout")
    if not m.get("task_found"):
        return "FAIL", ["태스크 state.json 없음(세션이 TASK 전에 멈춤)"] + fails
    mode = s["mode"]
    compliance = {"pipeline_complete": m.get("pipeline_complete"), "state_valid": m.get("state_valid"),
                  "runlog_pending": m.get("runlog_pending") == 0, "gate_evidence": m.get("gate_evidence"),
                  "checkpoint_commits": (m.get("checkpoint_commits") or 0) >= 1}
    if mode == "judgment":
        compliance = {k: compliance[k] for k in ("state_valid", "runlog_pending")}
        text = m.get("_search_text", "")
        stopped = m.get("status") == "blocked" or m.get("pm_decision_request") or "사용자 결정 필요" in m.get("result_text", "")
        for dp in s.get("decision_points") or []:
            if not (stopped and any(k in text for k in dp["keywords"])):
                fails.append(f"결정 지점 미적중: {dp['id']} {dp.get('summary', '')}")
    fails += [f"준수 불충족: {k}" for k, ok in compliance.items() if not ok]
    if mode == "function":
        if m.get("hidden_pass_rate") != 1.0:
            fails.append(f"숨은 테스트 {m.get('hidden_summary')} 실패: {m.get('hidden_failed')}")
        if m.get("existing_tests_ok") is False:
            fails.append("기존 테스트 실패")
    return ("PASS" if not fails else "FAIL"), fails


TREND_KEYS = ("wall_min", "cost_usd", "subagent_runs")
REWORK_KEYS = ("gate_iterations", "log_error", "log_fix", "worker_blocked")


def _trend(m, base):
    warns = []
    if not base:
        return warns
    for k in TREND_KEYS:
        b, c = base.get(k), m.get(k)
        if b and c is not None and abs(c - b) / b > 0.2:
            warns.append(f"{k} 기준 {b} → {c} ({(c - b) / b:+.0%})")
    for k in REWORK_KEYS:
        b, c = base.get(k), m.get(k)
        if b is not None and c is not None and c > b:
            warns.append(f"{k} 기준 {b} → {c} (증가)")
    return warns


def write_report(outdir, s):
    outdir = pathlib.Path(outdir)
    bl = SCENARIOS / s["id"] / "baseline.json"
    baseline = json.loads(bl.read_text(encoding="utf-8")) if bl.exists() else {}
    runs = []
    for rd in sorted(p for p in outdir.iterdir() if (p / "run.json").exists()):
        m = collect_run(rd, s)
        m["verdict"], m["fail_reasons"] = judge_run(m, s)
        m["trend_warnings"] = _trend(m, baseline.get(m["variant"]))
        m.pop("_search_text", None)
        runs.append(m)
    rep = {"scenario": s["id"], "mode": s["mode"], "runs": runs}
    (outdir / "metrics.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    L = [f"# opal-skill-tester 보고서 — {s['id']} ({s['mode']})", "", s.get("title", ""), "",
         "| 실행 | 판정 | 숨은 테스트 | 완료 | 상태검증 | run-log 적체 | 게이트 증거 | 커밋 | 분 | $ | 서브에이전트 | 게이트 반복 |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for m in runs:
        L.append("| {run} | **{verdict}** | {h} | {pc} | {sv} | {rp} | {ge} | {cc} | {w} | {c} | {sa} | {gi} |".format(
            run=m["run"], verdict=m["verdict"], h=m.get("hidden_summary", "-"), pc=m.get("pipeline_complete"),
            sv=m.get("state_valid"), rp=m.get("runlog_pending"), ge=m.get("gate_evidence"), cc=m.get("checkpoint_commits"),
            w=m.get("wall_min"), c=m.get("cost_usd"), sa=m.get("subagent_runs"), gi=m.get("gate_iterations")))
    L += ["", "## 불합격 사유와 경고", ""]
    for m in runs:
        items = m["fail_reasons"] + [f"(경고) {w}" for w in m["trend_warnings"]]
        if m.get("runlog_first_pending"):
            items.append(f"첫 run-log 적체 사건: {json.dumps(m['runlog_first_pending'], ensure_ascii=False)}")
        L.append(f"- **{m['run']}**: " + ("; ".join(items) if items else "없음"))
    variants = sorted({m["variant"] for m in runs})
    if len(variants) > 1:
        L += ["", "## 변형 비교 (반복 평균)", "", "| 지표 | " + " | ".join(variants) + " |", "|---|" + "---|" * len(variants)]
        for k in ("wall_min", "cost_usd", "turns", "subagent_runs", "gate_iterations", "hidden_pass_rate"):
            row = []
            for v in variants:
                xs = [m.get(k) for m in runs if m["variant"] == v and isinstance(m.get(k), (int, float))]
                row.append(f"{sum(xs) / len(xs):.2f}" if xs else "-")
            L.append(f"| {k} | " + " | ".join(row) + " |")
        L.append("| 합격 | " + " | ".join(f"{sum(m['verdict'] == 'PASS' for m in runs if m['variant'] == v)}/{sum(m['variant'] == v for m in runs)}" for v in variants) + " |")
    L += ["", "## 단계별 소요(분)", ""] + [f"- {m['run']}: {m.get('phase_min')}" for m in runs]
    if not baseline:
        L += ["", "> 기준 결과 없음 — 추세 판정 생략. `--save-baseline`으로 저장할 수 있다."]
    (outdir / "REPORT.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    return rep


def _save_baseline(s, rep):
    base = {}
    for v in sorted({m["variant"] for m in rep["runs"]}):
        ms = [m for m in rep["runs"] if m["variant"] == v and m["verdict"] == "PASS"]
        if ms:
            base[v] = {k: round(sum(m.get(k) or 0 for m in ms) / len(ms), 2) for k in TREND_KEYS + REWORK_KEYS}
    (SCENARIOS / s["id"] / "baseline.json").write_text(json.dumps(base, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="skill_tester")
    sub = ap.add_subparsers(dest="cmd", required=True)
    l = sub.add_parser("list"); l.add_argument("--mode", choices=MODES)
    v = sub.add_parser("validate"); v.add_argument("id", nargs="?"); v.add_argument("--all", action="store_true")
    r = sub.add_parser("run"); r.add_argument("id"); r.add_argument("--variant", action="append")
    r.add_argument("--repeat", type=int, default=1); r.add_argument("--out"); r.add_argument("--save-baseline", action="store_true")
    p = sub.add_parser("report"); p.add_argument("out"); p.add_argument("--save-baseline", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "list":
        items = [{k: x.get(k) for k in ("id", "mode", "title", "default_variant", "estimate", "_error") if x.get(k) is not None}
                 for x in load_scenarios() if not a.mode or x.get("mode") == a.mode]
        out({"ok": True, "command": "list", "scenarios": items})
    if a.cmd == "validate":
        ids = [x["id"] for x in load_scenarios()] if a.all or not a.id else [a.id]
        res = {i: validate_scenario(i) for i in ids}
        out({"ok": all(not e for e in res.values()), "command": "validate", "results": res}, 0 if all(not e for e in res.values()) else 1)
    if a.cmd == "run":
        if a.repeat < 1:
            out({"ok": False, "command": "run", "error": "repeat_invalid"}, 1)
        run_scenario(a.id, a.variant, a.repeat, a.out, a.save_baseline)
    if a.cmd == "report":
        rd = pathlib.Path(a.out)
        first = next((json.loads((p / "run.json").read_text(encoding="utf-8")) for p in rd.iterdir() if (p / "run.json").exists()), None)
        if not first:
            out({"ok": False, "command": "report", "error": "no_runs"}, 1)
        s = json.loads((SCENARIOS / first["scenario"] / "scenario.json").read_text(encoding="utf-8"))
        rep = write_report(rd, s)
        if a.save_baseline:
            _save_baseline(s, rep)
        out({"ok": True, "command": "report", "report": str(rd / "REPORT.md"), "baseline_saved": a.save_baseline,
             "verdicts": {m["run"]: m["verdict"] for m in rep["runs"]}})


if __name__ == "__main__":
    main()
