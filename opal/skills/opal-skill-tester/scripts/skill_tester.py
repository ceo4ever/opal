#!/usr/bin/env python3
"""
@header {
  "module": "skill_tester",
  "layer": "util",
  "domain": "opal-skill-tester",
  "description": "opal-skill-tester 실행기. scenarios/ 카탈로그 조회(list)·규격 검사(validate)·격리 저장소에서 claude -p 헤드리스 세션 실행과 지표 수집·판정·보고(run)·보고서 재생성(report)·tasks/ 기록(record)·대시보드 링크 재생성(refresh)을 수행한다. 기록 폴더에는 record.json과 report.html(요약/비교+스킬별 이력 탭)이 생기고, 이력은 tasks/와 tasks/backup/의 모든 record.json에서 모은다. run은 끝나면 보고서·지표·실행별 핵심 산출물을 진행 중 태스크의 skill-tests/ 또는 tasks/ 아래 YYMMDD-opst-{대상}-{모드}-{제목} 폴더에 기록하며(모의 저장소는 복사하지 않음), 기본은 단일 변형 실행이고 --variant를 여러 번 주면 비교, --repeat로 반복한다. 기반 저장소의 _opal·_gitignore는 복사 시 .opal·.gitignore로 복원한다. 준수 판정은 PROFILES(opd·opds·opsdd)의 Pilot별 단계 이정표·게이트 증거 행을 따르고, 체크포인트 커밋은 worktree 태스크에만 요구한다.",
  "exports": ["main", "load_scenarios", "validate_scenario", "run_scenario", "collect_run", "judge_run", "write_report", "record_results", "collect_history"]
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

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import report_html  # noqa: E402

SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent
SCENARIOS = SKILL_DIR / "scenarios"
MODES = ("smoke", "function", "judgment")
OPAL = pathlib.Path.home() / ".opal"
STATE_TOOL = OPAL / "tools" / "state-tool" / "run.sh"
RENAMES = {"_opal": ".opal", "_gitignore": ".gitignore"}
# Pilot별 판정 프로필 — 단계 이정표와 게이트 증거 행이 Pilot마다 다르다.
PROFILES = {
    "opd":   {"exec": "execute.implement", "test_done": "test.pm_gate", "gate_rows": [], "scenario_json": True},
    "opds":  {"exec": "execute.implement", "test_done": "test.pm_gate", "gate_rows": [], "scenario_json": True},
    "opsdd": {"exec": "execute.act_run", "test_done": "verify.pm_gate",
              "gate_rows": ["review.scenario_gate", "verify.ts_green"], "scenario_json": False},
}
PILOT_SKILL_DIRS = {"opd": "opal-pilot-dev", "opds": "opal-pilot-dev", "opsdd": "opal-pilot-sdd", "opp": "opal-pilot-project",
                    "oppd": "opal-pilot-project-dev", "oppl": "opal-pilot-project-loop", "opwt": "opal-pilot-write-tech"}
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
    for k in ("id", "mode", "base", "target_pilots", "default_variant", "utterance", "timeout_min", "estimate"):
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


def run_scenario(sid, variants, repeat, outdir, task_dir=None, project_root=None, no_record=False):
    errs = validate_scenario(sid)
    if errs:
        out({"ok": False, "command": "run", "error": "scenario_invalid", "detail": errs}, 1)
    s = json.loads((SCENARIOS / sid / "scenario.json").read_text(encoding="utf-8"))
    variants = variants or [s["default_variant"]]
    targets = set(s.get("target_pilots") or [])
    off = [v for v in variants if targets and v.split()[0].lstrip("/") not in targets]
    if off:
        out({"ok": False, "command": "run", "error": "variant_not_targeted", "variants": off,
             "target_pilots": sorted(targets)}, 1)
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
            meta = {"scenario": sid, "mode": s["mode"], "variant": v, "rep": k, "utterance": utt, "start": time.time(),
                    "framework": _framework_fingerprint(v.split()[0].lstrip("/"))}
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
    root = _resolve_root(task_dir, project_root)
    report = write_report(outdir, s, collect_history(root) if root else [])
    rec, rec_warn = (None, None) if no_record else record_results(outdir, s, task_dir, project_root)
    out({"ok": True, "command": "run", "out": str(outdir), "report": str(outdir / "REPORT.md"),
         "record": str(rec) if rec else None, "record_warning": rec_warn,
         "verdicts": {r["run"]: r["verdict"] for r in report["runs"]}, "warnings": _install_drift()})


def _pt(ts):
    for f in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.datetime.strptime(ts, f)
        except (TypeError, ValueError):
            pass
    return None


def _registry_checkpoint_shas(repo, code):
    """허브 registry(.opal-worktrees/.meta)에서 코드 작업본과 같은 worktree 행의 checkpoint_shas를 읽는다."""
    code_real = os.path.realpath(str(code))
    for mp in glob.glob(str(repo / ".opal-worktrees" / ".meta" / "task_*.json")):
        try:
            meta = json.loads(pathlib.Path(mp).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if meta.get("worktree_root") and os.path.realpath(meta["worktree_root"]) == code_real:
            return list((meta.get("execution_ownership") or {}).get("checkpoint_shas") or [])
    return []


def checkpoint_ok(m):
    if not m.get("worktree_task"):
        return True
    return (m.get("checkpoint_commits") or 0) >= 1 and not m.get("raw_commits")


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
    prof = PROFILES.get(st.get("skill"))
    m["profile"] = st.get("skill") if prof else None
    gate_ok, iters = False, 0
    if dg:
        gate_ok, iters = dg.get("status") == "pass", len(dg.get("history") or [])
    elif gh.exists():
        h = json.loads(gh.read_text(encoding="utf-8"))
        gate_ok, iters = bool(h) and h[-1].get("verdict") == "pass", len(h)
    rows = {r.get("key"): r.get("status") for r in st.get("rows", [])}
    rows_ok = all(rows.get(k) == "done" for k in (prof or {}).get("gate_rows", []))
    sc_ok = True
    if not prof or prof["scenario_json"]:
        tsj = tdir / "test-scenario.json"
        sc_ok = False
        if tsj.exists():
            sc = json.loads(tsj.read_text(encoding="utf-8")).get("scenarios") or []
            sc_ok = bool(sc) and all((x.get("result") or x.get("status")) == "pass" for x in sc)
    m.update(gate_iterations=iters, gate_evidence=gate_ok and sc_ok and rows_ok, worktree_task=bool(st.get("worktree")))
    branch_shas = _git(code, "rev-list", "main..HEAD").stdout.split() if st.get("worktree") else []
    tool_shas = set(_registry_checkpoint_shas(rd / "repo", code))
    # 체크포인트는 worktree-tool checkpoint로만 인정한다(harness/guards.md §커밋 규칙). git commit
    # 직접 실행은 registry checkpoint_shas에 남지 않으므로 우회 커밋으로 따로 센다.
    m["checkpoint_commits"] = sum(sha in tool_shas for sha in branch_shas)
    m["raw_commits"] = len(branch_shas) - m["checkpoint_commits"]
    evs = [json.loads(l) for f in sorted(glob.glob(str(tdir / "run" / "run-log-*.jsonl"))) for l in open(f) if l.strip()] + pend
    m["subagent_runs"] = sum(e.get("event") == "worker.started" for e in evs)
    m["worker_blocked"] = sum(e.get("event") == "worker.blocked" for e in evs)
    m["pm_decision_request"] = any(e.get("event") == "pm.report" and (e.get("data") or {}).get("report_type") == "decision_request" for e in evs)
    m["phase_min"] = _phases(evs, prof or PROFILES["opd"])
    al = tdir / "AGENTIC-LOG.md"
    txt = al.read_text(encoding="utf-8") if al.exists() else ""
    m["log_error"] = len(re.findall(r"\|\s*`?ERROR`?\s*\|", txt))
    m["log_fix"] = len(re.findall(r"\|\s*`?FIX`?\s*\|", txt))
    m["stage_log"], m["corrections"] = _agentic_log_by_stage(txt)
    m["stage_min"] = _stage_minutes(evs, [r.get("stage") for r in st.get("rows", [])])
    m["decision_requests"] = sum(e.get("event") == "pm.report" and (e.get("data") or {}).get("report_type") == "decision_request" for e in evs)
    m["framework"] = meta.get("framework")  # 실행 시점 지문. 이 필드 도입 전 실행은 None
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


def _agentic_log_by_stage(txt):
    """AGENTIC-LOG 표 행을 단계별 카테고리 수와 자기 교정 기록(ERROR·FIX 본문)으로 요약한다."""
    counts, corr = {}, []
    for line in txt.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5 or not cells[0].isdigit():
            continue
        stage, cat = cells[2], cells[3].strip("`")
        counts.setdefault(stage, {}).setdefault(cat, 0)
        counts[stage][cat] += 1
        if cat in ("ERROR", "FIX"):
            corr.append({"stage": stage, "kind": "발견" if cat == "ERROR" else "교정", "text": cells[4][:240]})
    return counts, corr


def _stage_minutes(evs, stage_order):
    """run-log state.changed로 단계별 소요(분)를 계산한다: 각 단계 마지막 전이 - 직전 단계 마지막 전이."""
    ts_all = [_pt(e.get("timestamp")) for e in evs if _pt(e.get("timestamp"))]
    if not ts_all:
        return {}
    last = {}
    for e in evs:
        if e.get("event") == "state.changed" and e.get("stage") and _pt(e.get("timestamp")):
            t = _pt(e["timestamp"])
            last[e["stage"]] = max(last.get(e["stage"], t), t)
    out, prev = {}, min(ts_all)
    for st in dict.fromkeys(s for s in stage_order if s):
        if st in last:
            out[st] = round(max((last[st] - prev).total_seconds(), 0) / 60, 1)
            prev = max(prev, last[st])
    return out


def _framework_fingerprint(skill):
    import hashlib
    h = hashlib.sha256()
    for rel in ("tools/state-tool/state_tool.py", f"skills/{PILOT_SKILL_DIRS.get(skill, '')}/SKILL.md"):
        p = OPAL / rel
        if p.is_file():
            h.update(p.read_bytes())
    ver = (OPAL / "VERSION").read_text(encoding="utf-8").strip() if (OPAL / "VERSION").exists() else "?"
    return f"{ver}+{h.hexdigest()[:6]}"


def _phases(evs, prof):
    sc = [e for e in evs if e.get("event") == "state.changed"]
    ts = [_pt(e.get("timestamp")) for e in evs if _pt(e.get("timestamp"))]
    if not ts:
        return {}
    def at(step, to):
        xs = [_pt(e["timestamp"]) for e in sc if e.get("task_step") == step and (e.get("data") or {}).get("to") == to]
        return min(xs) if xs else None
    marks = [min(ts), at(prof["exec"], "in_progress"), at(prof["exec"], "done"),
             at(prof["test_done"], "done"), at("close.final", "done")]
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
                  # 허브 작업본 태스크는 규칙상 커밋하지 않으므로 worktree 태스크에만 요구한다.
                  # 체크포인트 도구를 거친 커밋이 1개 이상이고 우회 커밋(git commit 직접)이 없어야 한다.
                  "checkpoint_commits": checkpoint_ok(m)}
    if mode == "judgment":
        compliance = {k: compliance[k] for k in ("state_valid", "runlog_pending")}
        text = m.get("_search_text", "")
        stopped = m.get("status") == "blocked" or m.get("pm_decision_request") or "사용자 결정 필요" in m.get("result_text", "")
        for dp in s.get("decision_points") or []:
            if not (stopped and any(k in text for k in dp["keywords"])):
                fails.append(f"결정 지점 미적중: {dp['id']} {dp.get('summary', '')}")
    fails += [f"준수 불충족: {k}" for k, ok in compliance.items() if not ok]
    if m.get("profile") is None:
        fails.append("판정 프로필 없음 — 이 Pilot의 게이트 증거·단계 이정표를 PROFILES에 추가해야 한다")
    if mode == "function":
        if m.get("hidden_pass_rate") != 1.0:
            fails.append(f"숨은 테스트 {m.get('hidden_summary')} 실패: {m.get('hidden_failed')}")
        if m.get("existing_tests_ok") is False:
            fails.append("기존 테스트 실패")
    return ("PASS" if not fails else "FAIL"), fails


TREND_KEYS = ("wall_min", "cost_usd", "subagent_runs")
REWORK_KEYS = ("gate_iterations", "log_error", "log_fix", "worker_blocked")
METRIC_LABELS = {"wall_min": "최종 수행 시간(분)", "cost_usd": "비용($)", "subagent_runs": "서브에이전트", "gate_iterations": "게이트 반복",
                 "log_error": "오류 기록", "log_fix": "수정 기록", "worker_blocked": "워커 차단"}


def _trend(m, hist):
    warns = []
    if not hist:
        return warns
    import statistics
    base = {}
    for k in TREND_KEYS + REWORK_KEYS:
        vals = [h.get(k) for h in hist[-3:] if isinstance(h.get(k), (int, float))]
        if vals:
            base[k] = statistics.median(vals)
    for k in TREND_KEYS:
        b, c = base.get(k), m.get(k)
        if b and c is not None and abs(c - b) / b > 0.2:
            warns.append(f"{METRIC_LABELS.get(k, k)} 최근 중앙값 {b} → {c} ({(c - b) / b:+.0%})")
    for k in REWORK_KEYS:
        b, c = base.get(k), m.get(k)
        if b is not None and c is not None and c > b:
            warns.append(f"{METRIC_LABELS.get(k, k)} 최근 중앙값 {b} → {c} (증가)")
    return warns


MODE_KO = {"smoke": "스모크", "function": "기능", "judgment": "판단"}
RECORD_TASK_FILES = ("TASK.md", "SPEC.md", "PLAN.md", "SPEC-PLAN.md", "TEST-SCENARIO.md", "TEST-SCENARIOS.md",
                     "DONE.md", "AGENTIC-LOG.md", "state.json")


def _yymmdd():
    try:
        r = subprocess.run(["node", str(OPAL / "tools" / "date" / "date.js"), "yymmdd"], capture_output=True, text=True, timeout=10)
        if r.returncode == 0 and re.fullmatch(r"\d{6}", r.stdout.strip()):
            return r.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return datetime.datetime.now().strftime("%y%m%d")


def _name_slug(text):
    return re.sub(r"-{2,}", "-", re.sub(r"[\s/\\()\[\]{}:;,.'\"`]+", "-", text)).strip("-")


def _project_root(start):
    r = subprocess.run(["git", "-C", str(start), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    root = pathlib.Path(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else None
    return root if root and (root / "tasks").is_dir() else None


def _active_task(root):
    """진행 중(in_progress·additional_work) 태스크가 정확히 하나일 때만 그 폴더를 돌려준다."""
    hits = []
    for sp in glob.glob(str(root / "tasks" / "*" / "state.json")):
        try:
            st = json.loads(pathlib.Path(sp).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if st.get("current_status") in ("in_progress", "additional_work"):
            hits.append(pathlib.Path(sp).parent)
    return hits[0] if len(hits) == 1 else None


def _resolve_root(task_dir=None, project_root=None):
    if project_root:
        return pathlib.Path(project_root).resolve()
    if task_dir:
        return _project_root(pathlib.Path(task_dir))
    return _project_root(pathlib.Path.cwd())


def collect_history(root, exclude=None):
    """tasks/와 tasks/backup/ 아래 모든 기록(record.json)을 실행 단위 레코드로 모은다."""
    out_ = []
    exclude = pathlib.Path(exclude).resolve() if exclude else None
    for rj in glob.glob(str(root / "tasks" / "**" / "record.json"), recursive=True):
        rdir = pathlib.Path(rj).parent.resolve()
        if exclude and rdir == exclude:
            continue
        try:
            meta = json.loads(pathlib.Path(rj).read_text(encoding="utf-8"))
            mets = json.loads((rdir / "metrics.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        rp = rdir / "report.html"
        seen = set()
        for m in mets.get("runs", []):
            if m.get("variant") in seen:
                continue  # 반복 실행은 첫 회차만 이력에 올린다
            seen.add(m.get("variant"))
            out_.append(dict(m, scenario=meta.get("scenario"), mode=meta.get("mode"), created_at=meta.get("created_at", ""), source=meta.get("source"),
                             report_path=str(rp)))
    return out_


def _render_html(dest, s, root):
    mets = json.loads((dest / "metrics.json").read_text(encoding="utf-8"))
    meta = json.loads((dest / "record.json").read_text(encoding="utf-8"))
    hist = [h for h in (collect_history(root, exclude=dest) if root else []) if h["created_at"] < meta["created_at"]]
    (dest / "report.html").write_text(report_html.render_report(s, mets["runs"], hist, str(dest), meta["created_at"]), encoding="utf-8")


def refresh_all(root):
    """tasks/·tasks/backup/의 모든 기록 report.html을 다시 만든다. 아카이브로 폴더가 옮겨져도
    이력은 매번 record.json을 다시 찾아 모으므로 링크가 현재 위치로 고쳐진다."""
    done, skipped = [], []
    for rj in glob.glob(str(root / "tasks" / "**" / "record.json"), recursive=True):
        dest = pathlib.Path(rj).parent
        sid = json.loads(pathlib.Path(rj).read_text(encoding="utf-8")).get("scenario")
        sj = SCENARIOS / str(sid) / "scenario.json"
        if not sj.exists():
            skipped.append(str(dest)); continue
        _render_html(dest, json.loads(sj.read_text(encoding="utf-8")), root)
        done.append(str(dest))
    return done, skipped


def record_results(outdir, s, task_dir=None, project_root=None):
    """결과 폴더의 보고서·지표·실행별 핵심 산출물을 tasks/ 아래 기록 폴더로 복사한다.
    모의 저장소 자체는 복사하지 않는다(중첩 git·가짜 .opal 프로젝트 방지)."""
    outdir = pathlib.Path(outdir)
    runs = sorted(p for p in outdir.iterdir() if (p / "run.json").exists())
    targets = sorted({json.loads((p / "run.json").read_text(encoding="utf-8"))["variant"].split()[0].lstrip("/") for p in runs})
    name = _name_slug(f"{_yymmdd()}-opst-{'-'.join(targets)}-{MODE_KO.get(s['mode'], s['mode'])}-{s.get('title') or s['id']}")
    if task_dir:
        base = pathlib.Path(task_dir).resolve() / "skill-tests"
    else:
        root = pathlib.Path(project_root).resolve() if project_root else _project_root(pathlib.Path.cwd())
        if root is None:
            return None, "tasks/ 폴더가 있는 프로젝트 루트를 찾지 못해 기록을 건너뜀(--project-root 또는 --task-dir 지정)"
        active = _active_task(root)
        base = (active / "skill-tests") if active else (root / "tasks")
    dest = base / name
    k = 2
    while dest.exists():
        dest = base / f"{name}-{k}"; k += 1
    dest.mkdir(parents=True)
    for f in ("REPORT.md", "metrics.json"):
        if (outdir / f).exists():
            shutil.copy(outdir / f, dest / f)
    for rd in runs:
        rdst = dest / "runs" / rd.name
        rdst.mkdir(parents=True)
        for f in ("run.json", "result.json", "REQUEST.md", "stderr.txt"):
            if (rd / f).exists() and (rd / f).stat().st_size:
                shutil.copy(rd / f, rdst / f)
        sp = _find_state(rd / "repo")
        if sp:
            tdst = rdst / "task"
            tdst.mkdir()
            for f in RECORD_TASK_FILES:
                if (sp.parent / f).exists():
                    shutil.copy(sp.parent / f, tdst / f)
    created = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    (dest / "record.json").write_text(json.dumps({"scenario": s["id"], "mode": s["mode"], "created_at": created,
                                                  "variants": targets, "source": str(outdir)}, ensure_ascii=False, indent=1), encoding="utf-8")
    root = _resolve_root(task_dir, project_root)
    if root:
        refresh_all(root)  # 새 기록 포함 전 기록을 다시 만들어 아카이브로 바뀐 링크도 고친다
    else:
        _render_html(dest, s, None)
    (dest / "SOURCE.md").write_text(
        f"# 기록 출처\n\n- 시나리오: `{s['id']}` ({s['mode']})\n- 실행 결과 폴더(모의 저장소 포함): `{outdir}`\n"
        f"- 모의 저장소는 중첩 git·가짜 OPAL 프로젝트 인식을 막기 위해 이 기록에 복사하지 않았다.\n", encoding="utf-8")
    return dest, None


def write_report(outdir, s, history=None):
    outdir = pathlib.Path(outdir)
    history = history or []
    runs = []
    for rd in sorted(p for p in outdir.iterdir() if (p / "run.json").exists()):
        m = collect_run(rd, s)
        m["verdict"], m["fail_reasons"] = judge_run(m, s)
        # 이 실행 자신의 기록과 이 실행보다 나중 기록은 비교 기준에서 뺀다(재판정 시 자기 비교 방지)
        end = json.loads((rd / "run.json").read_text(encoding="utf-8")).get("end") or time.time()
        cutoff = datetime.datetime.fromtimestamp(end).strftime("%Y-%m-%d %H:%M")
        same = [h for h in history if h["variant"] == m["variant"] and h["scenario"] == s["id"]
                and os.path.realpath(str(h.get("source") or "")) != os.path.realpath(str(outdir)) and h["created_at"] < cutoff]
        m["trend_warnings"] = _trend(m, sorted(same, key=lambda h: h["created_at"]))
        m.pop("_search_text", None)
        runs.append(m)
    rep = {"scenario": s["id"], "mode": s["mode"], "runs": runs}
    (outdir / "metrics.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    L = [f"# opal-skill-tester 보고서 — {s['id']} ({s['mode']})", "", s.get("title", ""), "",
         "| 실행 | 판정 | 숨은 테스트 | 완료 | 상태검증 | run-log 적체 | 게이트 증거 | 체크포인트 커밋 | 최종 수행 시간(분) | $ | 서브에이전트 | 게이트 반복 |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for m in runs:
        L.append("| {run} | **{verdict}** | {h} | {pc} | {sv} | {rp} | {ge} | {cc} | {w} | {c} | {sa} | {gi} |".format(
            run=m["run"], verdict=m["verdict"], h=m.get("hidden_summary", "-"), pc=m.get("pipeline_complete"),
            sv=m.get("state_valid"), rp=m.get("runlog_pending"), ge=m.get("gate_evidence"), cc=f'도구 {m.get("checkpoint_commits", 0)}/우회 {m.get("raw_commits", 0)}',
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
    if not history:
        L += ["", "> 같은 시나리오 이력 없음 — 추세 판정 생략(첫 기록)."]
    (outdir / "REPORT.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    return rep




def main(argv=None):
    ap = argparse.ArgumentParser(prog="skill_tester")
    sub = ap.add_subparsers(dest="cmd", required=True)
    l = sub.add_parser("list"); l.add_argument("--mode", choices=MODES)
    v = sub.add_parser("validate"); v.add_argument("id", nargs="?"); v.add_argument("--all", action="store_true")
    r = sub.add_parser("run"); r.add_argument("id"); r.add_argument("--variant", action="append")
    r.add_argument("--repeat", type=int, default=1); r.add_argument("--out")
    r.add_argument("--task-dir"); r.add_argument("--project-root"); r.add_argument("--no-record", action="store_true")
    c = sub.add_parser("record"); c.add_argument("out"); c.add_argument("--task-dir"); c.add_argument("--project-root")
    p = sub.add_parser("report"); p.add_argument("out"); p.add_argument("--project-root")
    f = sub.add_parser("refresh"); f.add_argument("--project-root")
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
        run_scenario(a.id, a.variant, a.repeat, a.out, a.task_dir, a.project_root, a.no_record)
    if a.cmd == "record":
        rd = pathlib.Path(a.out)
        first = next((json.loads((p / "run.json").read_text(encoding="utf-8")) for p in rd.iterdir() if (p / "run.json").exists()), None)
        if not first:
            out({"ok": False, "command": "record", "error": "no_runs"}, 1)
        s = json.loads((SCENARIOS / first["scenario"] / "scenario.json").read_text(encoding="utf-8"))
        root = _resolve_root(a.task_dir, a.project_root)
        write_report(rd, s, collect_history(root) if root else [])
        rec, warn = record_results(rd, s, a.task_dir, a.project_root)
        out({"ok": rec is not None, "command": "record", "record": str(rec) if rec else None, "warning": warn}, 0 if rec else 1)
    if a.cmd == "report":
        rd = pathlib.Path(a.out)
        first = next((json.loads((p / "run.json").read_text(encoding="utf-8")) for p in rd.iterdir() if (p / "run.json").exists()), None)
        if not first:
            out({"ok": False, "command": "report", "error": "no_runs"}, 1)
        s = json.loads((SCENARIOS / first["scenario"] / "scenario.json").read_text(encoding="utf-8"))
        root = _resolve_root(None, a.project_root)
        rep = write_report(rd, s, collect_history(root) if root else [])
        out({"ok": True, "command": "report", "report": str(rd / "REPORT.md"), "verdicts": {m["run"]: m["verdict"] for m in rep["runs"]}})
    if a.cmd == "refresh":
        root = _resolve_root(None, a.project_root)
        if root is None:
            out({"ok": False, "command": "refresh", "error": "project_root_not_found"}, 1)
        done, skipped = refresh_all(root)
        out({"ok": True, "command": "refresh", "refreshed": len(done), "skipped": skipped})


if __name__ == "__main__":
    main()
