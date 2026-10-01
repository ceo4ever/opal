#!/usr/bin/env python3
"""W-10 checker·evaluator model·effort 후보 측정기 (PLAN D-13).

호출 경로: 설치본(~/.claude/agents)을 바꾸지 않고 저장소 `opal/agents/<이름>/AGENT.md`의 본문·tools로
`--agents` JSON을 만들어 `claude -p --agents <json> --agent <이름> --model <별칭> [--effort <수준>]`을 부른다.
후보 호출은 사례×후보당 1회이고 재시도하지 않는다(raw 응답 파일이 이미 있으면 다시 부르지 않는다).
소요 시간 = 프로세스 시작부터 응답 JSON 수신까지 벽시계 초(time.monotonic).

사용:
  python3 run_eval.py [--part checker|evaluator|all] [--only id,id] [--candidates K0,K1,E0 ...]
                      [--max-parallel 6] [--out <dir>] [--work-root <dir>] [--repo-root <dir>]
                      [--keep-cases] [--dry-run] [--report-only]
  --report-only : 호출 없이 raw/ 응답에서 results.json과 ../EVAL-RESULT.md를 다시 계산·생성한다.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_REPO = HERE.parents[3]
TASK_DIR = HERE.parents[1]
sys.path.insert(0, str(HERE))
import build_cases  # noqa: E402

CHECKER_CANDS = {
    "K0": {"model": "sonnet", "effort": None, "label": "현행"},
    "K1": {"model": "sonnet", "effort": "low", "label": ""},
    "K2": {"model": "sonnet", "effort": "medium", "label": ""},
    "K3": {"model": "haiku", "effort": "medium", "label": ""},
}
EVAL_CANDS = {
    "E0": {"model": "opus", "effort": None, "label": "현행"},
    "E1": {"model": "opus", "effort": "medium", "label": ""},
    "E2": {"model": "opus", "effort": "high", "label": ""},
}
SEV_RANK = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
CHECKER_TS = "2026-10-01T00-00-00"
CALL_TIMEOUT = 1800
EV_SET = TASK_DIR.parent / "170-261001-opds-설계-게이트-회차-단축" / "run" / "eval-set"

# 170 EVAL-RESULT.md 기대: pass 3건=pass, 결함 5건=fail(지적 축은 170 표의 "기대 verdict" 열)
EVAL_CASES = [
    {"id": "pass-161", "expected_verdict": "pass", "expected_axes": [], "orig_axes": []},
    {"id": "pass-163", "expected_verdict": "pass", "expected_axes": [], "orig_axes": []},
    {"id": "pass-169", "expected_verdict": "pass", "expected_axes": [], "orig_axes": []},
    {"id": "defect-162-i1", "expected_verdict": "fail", "expected_axes": ["decision_clarity", "executability"],
     "orig_axes": ["decision_clarity", "executability"]},
    {"id": "defect-163-i1", "expected_verdict": "fail", "expected_axes": ["decision_clarity", "executability"],
     "orig_axes": ["decision_clarity", "executability"]},
    {"id": "defect-167-i2", "expected_verdict": "fail", "expected_axes": ["decision_clarity"],
     "orig_axes": ["decision_clarity"]},
    {"id": "defect-168-i2", "expected_verdict": "fail", "expected_axes": ["decision_clarity"],
     "orig_axes": ["completeness", "decision_clarity"]},
    {"id": "defect-169-i2", "expected_verdict": "fail", "expected_axes": ["decision_clarity"],
     "orig_axes": ["completeness", "decision_clarity", "recoverability"]},
]
AXES = ("completeness", "decision_clarity", "executability", "recoverability")


# ---------------------------------------------------------------- 호출 하네스
def parse_agent_md(path):
    text = Path(path).read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    if not m:
        raise ValueError("frontmatter 없음: %s" % path)
    fm, body = m.group(1), m.group(2)
    tools = re.search(r"^tools:\s*\[(.*?)\]", fm, re.M)
    desc = re.search(r"^description:\s*\|\n((?:[ \t]+.*\n?)+)", fm + "\n", re.M)
    return {
        "description": re.sub(r"^[ \t]+", "", desc.group(1), flags=re.M).strip() if desc else path.name,
        "prompt": body.lstrip("\n"),
        "tools": [t.strip() for t in tools.group(1).split(",")] if tools else [],
    }


def agents_json(repo, name):
    spec = parse_agent_md(Path(repo) / "opal" / "agents" / name / "AGENT.md")
    return json.dumps({name: spec}, ensure_ascii=False), spec["tools"]


def make_receipt(repo, dest):
    """호출 직전 worker.dispatch receipt를 새로 만들고 verify한다(실제 디스패치와 같은 경로)."""
    loader = os.path.expanduser("~/.opal/tools/event-loader/run.sh")
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    p = subprocess.run([loader, "load", "--event", "worker.dispatch", "--project-root", str(repo)],
                       capture_output=True, text=True)
    if p.returncode != 0:
        return None, "event-loader load 실패: %s" % (p.stderr or p.stdout)[:200]
    dest.write_text(p.stdout, encoding="utf-8")
    v = subprocess.run([loader, "verify", "--receipt", str(dest), "--event", "worker.dispatch",
                        "--project-root", str(repo)], capture_output=True, text=True)
    try:
        ok = json.loads(v.stdout).get("ok") is True
    except Exception:
        ok = False
    if not ok:
        return None, "event-loader verify 실패: %s" % (v.stdout or v.stderr)[:200]
    return str(dest), None


def receipt_block(receipt, repo):
    return ("[WORKER]\n\n## 이벤트 검증\n- event: `worker.dispatch`\n- receipt: %s\n"
            "- verification: 하네스가 호출 직전 `event-loader load`로 receipt를 새로 만들고 "
            "`event-loader verify --receipt <위> --event worker.dispatch --project-root %s`로 `ok: true`를 확인했다. "
            "너도 진입 게이트대로 직접 verify하고 receipt의 `required_documents[].content` 전문을 적용하라. "
            "verify는 현재 작업 디렉터리와 무관하게 다음 절대경로 명령 그대로 실행한다(다른 --project-root를 쓰지 않는다): "
            "`%s/.opal/tools/event-loader/run.sh verify --receipt %s --event worker.dispatch --project-root %s`\n\n"
            % (receipt, repo, os.path.expanduser("~"), receipt, repo))


def run_claude(raw_path, agent, agents_arg, cand, prompt, cwd, add_dirs, max_turns, dry_run=False):
    """claude -p를 1회 실행해 raw_path에 {cmd, elapsed_s, returncode, response, stderr}를 저장한다."""
    raw_path = Path(raw_path)
    if raw_path.exists():
        return json.loads(raw_path.read_text(encoding="utf-8"))   # 재시도 금지: 기존 raw 재사용
    cmd = ["claude", "-p", "--agents", agents_arg, "--agent", agent, "--model", cand["model"]]
    if cand["effort"]:
        cmd += ["--effort", cand["effort"]]
    cmd += ["--output-format", "json", "--max-turns", str(max_turns), "--permission-mode", "dontAsk",
            "--allowedTools", "Read", "Grep", "Glob", "Bash", "--no-session-persistence"]
    for d in add_dirs:
        cmd += ["--add-dir", str(d)]
    cmd += ["--", prompt]
    if dry_run:
        print("DRY-RUN", raw_path.name, [c if len(c) < 90 else c[:80] + "..." for c in cmd])
        return {"dry_run": True}
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    rec = {"agent": agent, "model": cand["model"], "effort": cand["effort"], "max_turns": max_turns}
    try:
        proc = subprocess.Popen(cmd, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            out, err = proc.communicate(timeout=CALL_TIMEOUT)
            rec["returncode"] = proc.returncode
        except subprocess.TimeoutExpired:
            proc.kill()
            out, err = proc.communicate()
            rec["returncode"] = None
            rec["error"] = "타임아웃(%ds)" % CALL_TIMEOUT
        rec["elapsed_s"] = round(time.monotonic() - started, 1)
        rec["stderr"] = (err or "")[-2000:]
        try:
            rec["response"] = json.loads(out)
        except Exception:
            rec["response"] = None
            rec["stdout_text"] = (out or "")[-4000:]
    except Exception as exc:  # noqa: BLE001 — 호출 실패도 결과 없음으로 기록
        rec["elapsed_s"] = round(time.monotonic() - started, 1)
        rec["error"] = "%s: %s" % (type(exc).__name__, exc)
        rec["response"] = None
    raw_path.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    return rec


def extract_json_objects(text):
    dec = json.JSONDecoder()
    found, i = [], 0
    while True:
        i = text.find("{", i)
        if i < 0:
            return found
        try:
            obj, end = dec.raw_decode(text[i:])
            if isinstance(obj, dict):
                found.append(obj)
            i += end
        except ValueError:
            i += 1


# ---------------------------------------------------------------- checker
def checker_prompt(case, receipt, repo, out_dir):
    pre = repo / "opal" / "tools" / "convention-precheck" / "run.sh"
    skill = repo / "opal" / "skills" / "op-gc-convention" / "SKILL.md"
    return receipt_block(receipt, repo) + (
        "## 작업\n"
        "op-gc-convention 스킬로 컨벤션 검사를 수행하라.\n\n"
        "skill_path: %s\n"
        "project_root: %s\n"
        "target_files: %s\n"
        "output_dir: %s\n"
        "timestamp: %s\n"
        "scope: all\n"
        "base_ref: %s\n"
        "project_documents: [docs/CONVENTIONS.md]\n\n"
        "## 평가 하네스 경로 지시\n"
        "- 스킬이 `~/.opal/tools/convention-precheck/run.sh`를 지시하면 저장소 소스 `%s`를 같은 인자로 실행한다(배포 전 측정).\n"
        "- 스킬·참조 문서의 `opal/...` 상대 경로는 project_root 기준으로 읽는다(없으면 건너뛰고 `references`에 남긴다).\n"
        "- `base_ref`가 주어졌으므로 스킬의 `base_ref`가 있을 때 절차(사전 검사 → 변경 구간 모델 검사 → `merge`)를 따른다.\n"
        "- 최종 finding JSON은 `merge --output`으로 `%s/gc-findings-convention-%s.json`에 만든다.\n"
        % (skill, case["project_root"], json.dumps(case["target_files"], ensure_ascii=False), out_dir,
           CHECKER_TS, case["base_ref"], pre, out_dir, CHECKER_TS))


def eval_checker_row(case, cand_id, raw, out_dir):
    row = {"kind": "checker", "case": case["id"], "cand": cand_id, "expected": describe_expected(case),
           "elapsed_s": raw.get("elapsed_s")}
    resp = raw.get("response") or {}
    row["usage"] = resp.get("usage")
    row["num_turns"] = resp.get("num_turns")
    row["cost_usd"] = resp.get("total_cost_usd")
    final = Path(out_dir) / ("gc-findings-convention-%s.json" % CHECKER_TS)
    pre = Path(out_dir) / ("gc-findings-convention-precheck-%s.json" % CHECKER_TS)
    reason = None
    if raw.get("error"):
        reason = raw["error"]
    elif not resp:
        reason = "응답 JSON 아님(rc=%s)" % raw.get("returncode")
    elif resp.get("is_error"):
        reason = "응답 오류: %s %s" % (resp.get("subtype"), str(resp.get("result"))[:120])
    elif not final.is_file():
        reason = "최종 finding JSON(merge 결과) 미생성"
    final_doc = None
    if reason is None:
        try:
            final_doc = json.loads(final.read_text(encoding="utf-8"))
            findings = final_doc.get("findings")
            if not isinstance(findings, list):
                reason = "최종 JSON에 findings 배열 없음"
        except Exception as exc:  # noqa: BLE001
            reason = "최종 JSON 파싱 실패: %s" % exc
    if reason:
        row.update({"result": False, "reason": reason, "match": None, "high_miss": None, "flip": None})
        return row
    findings = final_doc["findings"]
    mech = set(build_mech_ids())
    sev = [(f.get("severity") or "").lower() for f in findings]
    row["result"] = True
    row["status"] = final_doc.get("status")
    row["n_findings"] = len(findings)
    row["by_severity"] = {s: sev.count(s) for s in SEV_RANK if sev.count(s)}
    row["n_precheck"] = sum(1 for f in findings if f.get("rule_id") in mech)
    row["n_model"] = len(findings) - row["n_precheck"]
    row["summary"] = summarize_findings(findings, mech)
    # 기대 대비
    matched, violations, near = [], [], []
    for e in case["expected"]:
        hit = [f for f in findings if f.get("location", {}).get("file") == e["file"] and e["rule_key"] in (f.get("rule_id") or "")]
        ok = [f for f in hit if SEV_RANK.get((f.get("severity") or "").lower(), -1) >= SEV_RANK[e["min_severity"]]
              and ("max_severity" not in e or SEV_RANK.get((f.get("severity") or "").lower(), 99) <= SEV_RANK[e["max_severity"]])]
        if ok:
            matched.append(e)
        else:
            if hit:
                violations.append("%s: 심각도 %s(허용 %s~%s)" % (e["rule_key"], hit[0].get("severity"), e["min_severity"],
                                                          e.get("max_severity", "critical")))
            else:
                near_f = [f for f in findings if f.get("location", {}).get("file") == e["file"]]
                if near_f:
                    near.append("%s 대신 같은 파일의 %s" % (e["rule_key"], "; ".join(sorted({(f.get("rule_id") or "")[:40] for f in near_f}))))
    missing = [e for e in case["expected"] if e not in matched]
    row["high_miss"] = sum(1 for e in missing if SEV_RANK[e["min_severity"]] >= SEV_RANK["high"])
    high_plus = [f for f in findings if SEV_RANK.get((f.get("severity") or "").lower(), -1) >= SEV_RANK["high"]]
    if case["expected"]:
        row["match"] = not missing
        row["flip"] = 0
    else:
        top = max([SEV_RANK.get(s, -1) for s in sev] or [-1])
        row["match"] = top <= SEV_RANK[case.get("max_allowed_severity", "medium")]
        row["flip"] = 1 if high_plus else 0
        row["flip_precheck_only"] = 1 if high_plus and all(f.get("rule_id") in mech for f in high_plus) else 0
    notes = []
    if missing:
        notes.append("누락: " + ", ".join("%s(%s)" % (e["rule_key"], e["file"].split("/")[-1]) for e in missing))
    notes += violations + near
    if not case["expected"] and high_plus:
        notes.append("High+ %d건(사전 검사 %d·모델 %d)" % (
            len(high_plus), sum(1 for f in high_plus if f.get("rule_id") in mech),
            sum(1 for f in high_plus if f.get("rule_id") not in mech)))
    if pre.is_file():
        try:
            pf = json.loads(pre.read_text(encoding="utf-8"))
            high_pre = sum(1 for f in pf.get("findings", []) if (f.get("severity") or "").lower() in ("high", "critical"))
            row["precheck_high"] = high_pre
        except Exception:  # noqa: BLE001
            pass
    drop = [e for e in (final_doc.get("evidence") or []) if isinstance(e, str) and "model findings dropped" in e]
    if drop:
        notes.append(drop[0])
    row["notes"] = notes
    return row


def build_mech_ids():
    return ["CONVENTIONS.md §구현 규칙 §@header 규칙", "CONVENTIONS.md §파일 구조 §YAML Frontmatter",
            "opal-doc-standard.md §5", "CONVENTIONS.md §네이밍 규칙 §파일/폴더"]


def summarize_findings(findings, mech):
    if not findings:
        return "finding 0건"
    by = {}
    for f in findings:
        key = (f.get("severity"), "사전" if f.get("rule_id") in mech else "모델", short_rule(f.get("rule_id")))
        by[key] = by.get(key, 0) + 1
    parts = ["%s/%s/%s×%d" % (k[0], k[1], k[2], n) for k, n in sorted(by.items(), key=lambda kv: -SEV_RANK.get(kv[0][0], 0))]
    text = "; ".join(parts[:5]) + ("; 외 %d종" % (len(parts) - 5) if len(parts) > 5 else "")
    return "%d건: %s" % (len(findings), text)


def short_rule(rule):
    r = rule or "?"
    for key, name in (("@header", "@header"), ("YAML Frontmatter", "frontmatter"), ("opal-doc-standard", "doc-변경이력"),
                      ("파일/폴더", "파일명"), ("언어 규칙", "언어규칙")):
        if key in r:
            return name
    return r[:28]


def describe_expected(case):
    if case["expected"]:
        return "; ".join("%s %s(%s+)" % (e["rule_key"], e["file"].split("/")[-1], e["min_severity"]) for e in case["expected"])
    return "High+ 0건" if case["kind"] == "past" else "finding 없음(%s 이하)" % case.get("max_allowed_severity", "low")


# ---------------------------------------------------------------- evaluator
def make_fixture(case_id, fx_root, repo):
    """test_design_gate_parallel --make-fixture로 열린 시도(iteration 1) 임시 태스크를 만든다.
    결정론 검사가 실패하는 결함 fixture는 start가 시도를 deterministic_fail로 닫으므로, 임시 fixture의
    design_gate.status만 evaluating으로 되돌려 열린 시도로 쓴다(시도의 bundle_hash·iteration은 그대로)."""
    target = Path(fx_root) / case_id
    docs = EV_SET / case_id
    if (target / "state.json").exists():
        import shutil
        shutil.rmtree(target)
    p = subprocess.run([sys.executable, str(Path(repo) / "opal/tools/state-tool/tests/test_design_gate_parallel.py"),
                        "--make-fixture", str(target), "--docs", str(docs)], capture_output=True, text=True)
    info = {"task_path": str(target)}
    if p.returncode == 0:
        try:
            info["bundle_hash"] = json.loads(p.stdout.strip().splitlines()[-1])["bundle_hash"]
            info["seeded"] = False
            return info
        except Exception:  # noqa: BLE001
            pass
    st = json.loads((target / "state.json").read_text(encoding="utf-8"))
    dg = st["design_gate"]
    attempt = dg.get("current_attempt") or {}
    if not attempt.get("bundle_hash") or not dg.get("history") or dg["history"][-1].get("verdict") != "deterministic_fail":
        raise RuntimeError("fixture 생성 실패: %s%s" % (p.stdout[-500:], p.stderr[-500:]))
    info["seed_reason"] = dg["history"][-1].get("reason", "")[:200]
    dg["status"] = "evaluating"
    dg["history"] = []
    (target / "state.json").write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")
    info["bundle_hash"] = attempt["bundle_hash"]
    info["seeded"] = True
    return info


def evaluator_prompt(scope, fx, receipt, repo):
    task = fx["task_path"]
    return receipt_block(receipt, repo) + (
        "## 작업\n"
        "opal-evaluator-agent를 `phase: design-rubric`으로 수행하라. 이번 호출의 `scope`는 `%s`다. "
        "판정 JSON만 반환하고 파일을 만들지 않는다(부분 결과 계약 `scope: design`/`scope: scenario`를 따른다).\n\n"
        "```yaml\n"
        "phase: design-rubric\n"
        "scope: %s\n"
        "task_folder: %s\n"
        "task_md: %s/TASK.md\n"
        "plan_md: %s/PLAN.md\n"
        "scenario_source: %s/TEST-SCENARIO.md\n"
        "iteration: 1\n"
        "input_bundle_hash: %s\n"
        "refinement: false\n"
        "contract_path: (사용 안 함 — design-rubric)\n"
        "timestamp: 2026-10-01T00-00-00\n"
        "project_root: %s\n"
        "```\n" % (scope, scope, task, task, task, task, fx["bundle_hash"], repo))


def parse_partial(rec, scope):
    resp = rec.get("response") or {}
    if rec.get("error"):
        return None, rec["error"]
    if not resp:
        return None, "응답 JSON 아님(rc=%s)" % rec.get("returncode")
    if resp.get("is_error"):
        return None, "응답 오류: %s %s" % (resp.get("subtype"), str(resp.get("result"))[:120])
    objs = extract_json_objects(str(resp.get("result") or ""))
    cands = [o for o in objs if o.get("scope") == scope or ("design" in o and scope == "design") or ("scenario" in o and scope == "scenario")]
    cands = [o for o in cands if "input_bundle_hash" in o]
    if not cands:
        return None, "결과 텍스트에서 %s 부분 결과 JSON을 찾지 못함" % scope
    return cands[-1], None


def eval_evaluator(case, cand_id, fx, raws, out_dir, repo):
    rows, parts = [], {}
    for scope in ("design", "scenario"):
        rec = raws[scope]
        part, reason = parse_partial(rec, scope)
        resp = rec.get("response") or {}
        row = {"kind": "evaluator", "case": case["id"], "cand": cand_id, "scope": scope,
               "expected": ("design 4축 중 " + "·".join(case["expected_axes"]) + " FAIL") if scope == "design" and case["expected_axes"]
               else ("design 4축 PASS" if scope == "design" else "시나리오 3축 ≥1(평균 ≥1.5)"),
               "elapsed_s": rec.get("elapsed_s"), "result": part is not None, "reason": reason,
               "usage": resp.get("usage"), "num_turns": resp.get("num_turns"), "cost_usd": resp.get("total_cost_usd")}
        if part is not None:
            parts[scope] = part
            if scope == "design":
                axes = (part.get("design") or {}).get("axes") or {}
                row["actual"] = "FAIL 축: " + (",".join(a for a in AXES if str(axes.get(a)).upper() != "PASS") or "없음")
                row["fail_axes"] = [a for a in AXES if str(axes.get(a)).upper() != "PASS"]
            else:
                sc = (part.get("scenario") or {}).get("scores") or {}
                row["actual"] = "점수 %s/%s/%s 평균 %s, advisory %d건" % (
                    sc.get("goal"), sc.get("adoption"), sc.get("boundary"), (part.get("scenario") or {}).get("average"),
                    len(part.get("advisories") or []))
        else:
            row["actual"] = "결과 없음"
        rows.append(row)
    comb = {"kind": "combined", "case": case["id"], "cand": cand_id, "expected_verdict": case["expected_verdict"],
            "expected_axes": case["expected_axes"], "d_elapsed_s": raws["design"].get("elapsed_s"),
            "s_elapsed_s": raws["scenario"].get("elapsed_s"), "pair_wall_s": raws.get("pair_wall_s")}
    comb["elapsed_s"] = max([x for x in (comb["d_elapsed_s"], comb["s_elapsed_s"]) if x is not None] or [None]) \
        if comb["d_elapsed_s"] is not None and comb["s_elapsed_s"] is not None else None
    if len(parts) < 2:
        miss = [r["reason"] for r in rows if not r["result"]]
        comb.update({"result": False, "reason": "부분 결과 없음: " + " / ".join(m for m in miss if m),
                     "verdict": None, "match": None, "missed": None, "flip": None})
        return rows, comb
    combine_dir = Path(out_dir) / "combine"
    combine_dir.mkdir(parents=True, exist_ok=True)
    dpath, spath, opath = (combine_dir / ("%s__%s-%s.json" % (case["id"], cand_id, s)) for s in ("design", "scenario", "combined"))
    dpath.write_text(json.dumps(parts["design"], ensure_ascii=False), encoding="utf-8")
    spath.write_text(json.dumps(parts["scenario"], ensure_ascii=False), encoding="utf-8")
    cache = Path(str(opath) + ".resp.json")
    if opath.is_file() and cache.is_file():                    # 재계산(--report-only): fixture 없이 기록된 결합 결과 재사용
        cresp = json.loads(cache.read_text(encoding="utf-8"))
        p = type("P", (), {"returncode": 0, "stderr": ""})()
    else:
        if opath.exists():
            opath.unlink()
        p = subprocess.run([sys.executable, str(Path(repo) / "opal/tools/state-tool/state_tool.py"), "design-gate", "combine",
                            fx["task_path"], "--iteration", "1", "--design-result", str(dpath), "--scenario-result", str(spath),
                            "--output", str(opath)], capture_output=True, text=True)
        try:
            cresp = json.loads(p.stdout)
        except Exception:  # noqa: BLE001
            cresp = {}
        cache.write_text(json.dumps(cresp, ensure_ascii=False), encoding="utf-8")
    if p.returncode != 0 or not cresp.get("ok") or not opath.is_file():
        comb.update({"result": False, "verdict": None, "match": None, "missed": None, "flip": None,
                     "reason": "combine 거부: %s %s" % (cresp.get("error"), str(cresp.get("detail") or cresp.get("message") or p.stderr)[:160])})
        return rows, comb
    out = json.loads(opath.read_text(encoding="utf-8"))
    axes = (out.get("design") or {}).get("axes") or {}
    fail_axes = [a for a in AXES if str(axes.get(a)).upper() != "PASS"]
    comb.update({"result": True, "verdict": out.get("verdict"), "rewrite_target": out.get("rewrite_target"),
                 "fail_axes": fail_axes, "average": (out.get("scenario") or {}).get("average")})
    comb["match"] = out.get("verdict") == case["expected_verdict"]
    if case["expected_verdict"] == "fail":
        miss_axes = [a for a in case["expected_axes"] if a not in fail_axes]
        comb["missed"] = 1 if (out.get("verdict") != "fail" or miss_axes) else 0
        comb["missed_axes"] = miss_axes
        comb["flip"] = 0
    else:
        comb["missed"] = 0
        comb["flip"] = 1 if out.get("verdict") != "pass" else 0
    return rows, comb


# ---------------------------------------------------------------- 스케줄러
class Weighted:
    def __init__(self, n):
        self.free, self.cv = n, threading.Condition()

    def acquire(self, w):
        with self.cv:
            while self.free < w:
                self.cv.wait()
            self.free -= w

    def release(self, w):
        with self.cv:
            self.free += w
            self.cv.notify_all()


def run_units(units, max_parallel):
    """units: [(weight, fn)] — 제출 순서(FIFO)대로 가중 슬롯을 확보해 스레드로 실행한다."""
    sem, threads = Weighted(max_parallel), []
    for weight, fn in units:
        sem.acquire(weight)

        def runner(fn=fn, weight=weight):
            try:
                fn()
            except Exception as exc:  # noqa: BLE001
                print("UNIT ERROR:", type(exc).__name__, exc, file=sys.stderr)
            finally:
                sem.release(weight)
        t = threading.Thread(target=runner)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()


# ---------------------------------------------------------------- 실행 본체
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--part", default="all", choices=["checker", "evaluator", "all"])
    ap.add_argument("--only", default="", help="쉼표로 구분한 사례 id만 실행")
    ap.add_argument("--candidates", default="", help="쉼표로 구분한 후보 id만 실행(K0..K3, E0..E2)")
    ap.add_argument("--max-parallel", type=int, default=6)
    ap.add_argument("--out", default=str(HERE), help="raw/·cases.json·results.json 폴더")
    ap.add_argument("--work-root", default=str(build_cases.DEFAULT_WORK))
    ap.add_argument("--repo-root", default=str(DEFAULT_REPO))
    ap.add_argument("--keep-cases", action="store_true", help="끝나도 임시 worktree를 제거하지 않는다")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args(argv)
    repo, out, work = Path(args.repo_root).resolve(), Path(args.out).resolve(), Path(args.work_root).resolve()
    only = {x for x in args.only.split(",") if x}
    cand_filter = {x for x in args.candidates.split(",") if x}
    raw_root = out / "raw"
    fx_root = work / "eval-fixtures"
    # 호출 환경(report-only가 아닐 때): 사례 구축
    cases = []
    if not args.report_only:
        need = not (out / "cases.json").is_file()
        if not need:   # 이전 실행이 임시 worktree를 정리했으면 다시 만든다(같은 구성)
            need = any(not Path(c["project_root"]).is_dir() for c in json.loads((out / "cases.json").read_text(encoding="utf-8"))["cases"])
        if need:
            build_cases.main(["--work-root", str(work), "--out", str(out), "--repo-root", str(repo)])
    cj = json.loads((out / "cases.json").read_text(encoding="utf-8"))
    cases = cj["cases"]
    for c in cases:
        c.setdefault("max_allowed_severity", "low" if c["id"] == "syn-ok-clean" else "medium")
    results_path = out / "results.json"
    rows = {"checker": [], "evaluator": [], "combined": []}

    if not args.report_only:
        if args.part in ("checker", "all"):
            ck_agent, _ = "opal-convention-checker", None
            ck_json, _tools = agents_json(repo, ck_agent)
            units = []
            for c in cases:
                if only and c["id"] not in only:
                    continue
                for cid, cand in CHECKER_CANDS.items():
                    if cand_filter and cid not in cand_filter:
                        continue
                    units.append((1, make_checker_unit(c, cid, cand, ck_agent, ck_json, repo, raw_root, args.dry_run)))
            run_units(units, args.max_parallel)
        if args.part in ("evaluator", "all"):
            ev_agent = "opal-evaluator-agent"
            ev_json, _tools = agents_json(repo, ev_agent)
            fixtures = {}
            for ec in EVAL_CASES:
                if only and ec["id"] not in only:
                    continue
                if args.dry_run:
                    fixtures[ec["id"]] = {"task_path": "<fx>/" + ec["id"], "bundle_hash": "<hash>", "seeded": None}
                else:
                    fixtures[ec["id"]] = make_fixture(ec["id"], fx_root, repo)
                    (raw_root / "evaluator").mkdir(parents=True, exist_ok=True)
                    (raw_root / "evaluator" / ("fixture-%s.json" % ec["id"])).write_text(
                        json.dumps(fixtures[ec["id"]], ensure_ascii=False, indent=1), encoding="utf-8")
            units = []
            for ec in EVAL_CASES:
                if ec["id"] not in fixtures:
                    continue
                for cid, cand in EVAL_CANDS.items():
                    if cand_filter and cid not in cand_filter:
                        continue
                    units.append((2, make_evaluator_unit(ec, cid, cand, ev_agent, ev_json, fixtures[ec["id"]], repo,
                                                         raw_root, args.dry_run)))
            run_units(units, args.max_parallel)
        if args.dry_run:
            return 0

    # 평가(raw에서 재계산)
    for c in cases:
        for cid in CHECKER_CANDS:
            rp = raw_root / "checker" / ("%s__%s.json" % (c["id"], cid))
            if rp.is_file():
                rows["checker"].append(eval_checker_row(c, cid, json.loads(rp.read_text(encoding="utf-8")),
                                                        raw_root / "checker" / ("%s__%s" % (c["id"], cid)) / "out"))
    for ec in EVAL_CASES:
        fxp = raw_root / "evaluator" / ("fixture-%s.json" % ec["id"])
        if not fxp.is_file():
            continue
        fx = json.loads(fxp.read_text(encoding="utf-8"))
        for cid in EVAL_CANDS:
            raws = {}
            for scope in ("design", "scenario"):
                rp = raw_root / "evaluator" / ("%s__%s__%s.json" % (ec["id"], cid, scope))
                if rp.is_file():
                    raws[scope] = json.loads(rp.read_text(encoding="utf-8"))
            if len(raws) == 2:
                pw = raw_root / "evaluator" / ("%s__%s__pair.json" % (ec["id"], cid))
                raws["pair_wall_s"] = json.loads(pw.read_text())["pair_wall_s"] if pw.is_file() else None
                r, comb = eval_evaluator(ec, cid, fx, raws, raw_root / "evaluator", repo)
                rows["evaluator"] += r
                rows["combined"].append(comb)
    results_path.write_text(json.dumps({"cases": cases, "eval_cases": EVAL_CASES, "rows": rows}, ensure_ascii=False, indent=1),
                            encoding="utf-8")
    write_report((HERE.parent if out == HERE else out) / "EVAL-RESULT.md", results_path, HERE / "analysis-notes.md")
    if not args.report_only and not args.keep_cases:
        build_cases.main(["--cleanup", "--work-root", str(work), "--out", str(out), "--repo-root", str(repo)])
    print(json.dumps({"ok": True, "checker_rows": len(rows["checker"]), "evaluator_rows": len(rows["evaluator"]),
                      "combined_rows": len(rows["combined"])}))
    return 0


def make_checker_unit(case, cid, cand, agent, agents_arg, repo, raw_root, dry_run):
    def unit():
        base = raw_root / "checker" / ("%s__%s" % (case["id"], cid))
        raw_path = raw_root / "checker" / ("%s__%s.json" % (case["id"], cid))
        if raw_path.exists():
            return
        out_dir = base / "out"
        out_dir.mkdir(parents=True, exist_ok=True)
        receipt, why = (None, None) if dry_run else make_receipt(repo, base / "receipt.json")
        if why:
            raw_path.write_text(json.dumps({"error": why, "elapsed_s": None, "response": None}, ensure_ascii=False),
                                encoding="utf-8")
            return
        prompt = checker_prompt(case, receipt, repo, out_dir)
        rec = run_claude(raw_path, agent, agents_arg, cand, prompt, case["project_root"], [repo, out_dir, base], 80, dry_run)
        if not dry_run:
            print("checker %-30s %s %6.1fs" % (case["id"], cid, rec.get("elapsed_s") or -1), flush=True)
    return unit


def make_evaluator_unit(ec, cid, cand, agent, agents_arg, fx, repo, raw_root, dry_run):
    def unit():
        base = raw_root / "evaluator"
        paths = {s: base / ("%s__%s__%s.json" % (ec["id"], cid, s)) for s in ("design", "scenario")}
        if all(p.exists() for p in paths.values()):
            return
        receipts = {}
        for scope in ("design", "scenario"):
            receipts[scope], why = (None, None) if dry_run else make_receipt(repo, base / "receipts" / ("%s__%s__%s.json" % (ec["id"], cid, scope)))
            if why:
                paths[scope].write_text(json.dumps({"error": why, "elapsed_s": None, "response": None}, ensure_ascii=False),
                                        encoding="utf-8")
        out = {}

        def call(scope):
            if paths[scope].exists():
                return
            prompt = evaluator_prompt(scope, fx, receipts[scope], repo)
            out[scope] = run_claude(paths[scope], agent, agents_arg, cand, prompt, repo, [repo, fx["task_path"]], 50, dry_run)
        t0 = time.monotonic()
        threads = [threading.Thread(target=call, args=(s,)) for s in ("design", "scenario")]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        if not dry_run:
            wall = round(time.monotonic() - t0, 1)
            (base / ("%s__%s__pair.json" % (ec["id"], cid))).write_text(json.dumps({"pair_wall_s": wall}), encoding="utf-8")
            print("evaluator %-14s %s design %6.1fs scenario %6.1fs pair %6.1fs" % (
                ec["id"], cid, (out.get("design") or {}).get("elapsed_s") or -1,
                (out.get("scenario") or {}).get("elapsed_s") or -1, wall), flush=True)
    return unit


# ---------------------------------------------------------------- 보고서
def _c(text):
    return str(text).replace("|", "/").replace("\n", " ").strip()


def _f(x):
    return "-" if x is None else ("%.1f" % x)


def _usage_note(row):
    bits = []
    if row.get("num_turns") is not None:
        bits.append("턴 %s" % row["num_turns"])
    if row.get("cost_usd") is not None:
        bits.append("$%.2f" % row["cost_usd"])
    return ", ".join(bits)


def adoption(data):
    """D-13 채택 판정 재계산. 반환: {후보: {...}} (checker·evaluator 공통)."""
    rows = data["rows"]
    out = {}
    n_ck = len(data["cases"])
    for cid, cand in CHECKER_CANDS.items():
        rs = [r for r in rows["checker"] if r["cand"] == cid]
        got = [r for r in rs if r.get("result")]
        miss = sum(r["high_miss"] for r in got)
        flip = sum(r["flip"] for r in got)
        flip_pre = sum(r.get("flip_precheck_only", 0) for r in got)
        nores = n_ck - len(got)
        reasons = []
        if miss:
            reasons.append("High+ 누락 %d건" % miss)
        if flip:
            reasons.append("pass 뒤집힘 %d건" % flip)
        if nores:
            reasons.append("결과 없음/미실행 %d건" % nores)
        times = [r["elapsed_s"] for r in got if r.get("elapsed_s") is not None]
        out[cid] = {"agent": "checker", "n": n_ck, "result": len(got), "no_result": nores, "missed": miss, "flip": flip,
                    "flip_precheck_only": flip_pre, "adoptable": not reasons, "reasons": reasons,
                    "mean_s": sum(times) / len(times) if times else None,
                    "median_s": sorted(times)[len(times) // 2] if times else None, "max_s": max(times) if times else None,
                    "mismatch": sum(1 for r in got if r.get("match") is False)}
    for cid, cand in EVAL_CANDS.items():
        rs = [r for r in rows["combined"] if r["cand"] == cid]
        got = [r for r in rs if r.get("result")]
        miss = sum(r["missed"] for r in got)
        flip = sum(r["flip"] for r in got)
        nores = len(EVAL_CASES) - len(got)
        reasons = []
        if miss:
            reasons.append("결함 누락 %d건" % miss)
        if flip:
            reasons.append("pass 뒤집힘 %d건" % flip)
        mism = sum(1 for r in got if r.get("match") is False)
        if mism and not (miss or flip):
            reasons.append("결합 verdict 기대 불일치 %d건" % mism)
        if nores:
            reasons.append("결과 없음/미실행 %d건" % nores)
        times = [r["elapsed_s"] for r in got if r.get("elapsed_s") is not None]
        out[cid] = {"agent": "evaluator", "n": len(EVAL_CASES), "result": len(got), "no_result": nores, "missed": miss,
                    "flip": flip, "adoptable": not reasons, "reasons": reasons, "mismatch": mism,
                    "mean_s": sum(times) / len(times) if times else None,
                    "median_s": sorted(times)[len(times) // 2] if times else None, "max_s": max(times) if times else None}
    return out


def write_report(path, results_path, notes_path):
    data = json.loads(Path(results_path).read_text(encoding="utf-8"))
    rows, cases = data["rows"], data["cases"]
    ad = adoption(data)
    L = []
    w = L.append
    w("<!--")
    w("W-10 checker·evaluator model·effort 후보 측정 결과. PLAN D-13 그대로: checker 4후보×10사례=40회, evaluator 3후보×8사례×scope 2=48회(결합 24건).")
    w("이 문서의 표는 run/eval/run_eval.py가 run/eval/raw/ 원본 응답에서 계산해 생성한다(`python3 run_eval.py --report-only`로 재생성).")
    w("결과는 후보 간 상대 비교로만 서술하며 절대 누락률을 주장하지 않는다(H-3).")
    w("-->")
    w("# EVAL-RESULT: checker·evaluator model·effort 평가 (W-10)")
    w("")
    ncall = len(rows["checker"]) + len(rows["evaluator"])
    nres = sum(1 for r in rows["checker"] if r.get("result")) + sum(1 for r in rows["evaluator"] if r.get("result"))
    w("실행 호출 %d회(checker %d·evaluator %d), 결과 있음 %d·결과 없음 %d. 모든 호출은 사례×후보당 1회이고 재시도하지 않았다. "
      "결과 없음은 사유와 함께 표에 남겼다. 보정 후 재집계 경위는 8절." % (ncall, len(rows["checker"]), len(rows["evaluator"]), nres, ncall - nres))
    w("")
    w("## 1. 후보 표")
    w("")
    w("| 후보 | 대상 | model | effort | 비고 |")
    w("|---|---|---|---|---|")
    for cid, c in CHECKER_CANDS.items():
        w("| %s | checker | %s | %s | %s |" % (cid, c["model"], c["effort"] or "(미지정)", c["label"] or ""))
    for cid, c in EVAL_CANDS.items():
        w("| %s | evaluator | %s | %s | %s |" % (cid, c["model"], c["effort"] or "(미지정)", c["label"] or ("xhigh는 170 근거로 제외" if False else "")))
    w("")
    w("호출 경로: 저장소 `opal/agents/<이름>/AGENT.md` 본문·`tools`로 `--agents` JSON을 만들어 `claude -p --agents <json> --agent <이름> --model <별칭> [--effort <수준>] "
      "--output-format json --permission-mode dontAsk --allowedTools Read Grep Glob Bash`로 호출했다(설치본 불변). "
      "호출마다 `event-loader load --event worker.dispatch` receipt를 새로 만들고 `verify ok:true`를 확인한 뒤 프롬프트에 실었다. "
      "소요 시간은 프로세스 시작부터 응답 JSON 수신까지 벽시계 초다. 동시 실행은 최대 6개(evaluator 한 쌍은 슬롯 2개)다.")
    w("")
    w("## 2. checker 결과 (%d행)" % len(rows["checker"]))
    w("")
    w("평가 항목은 최종 finding JSON(`merge` 결과, 사전 검사 finding 포함)을 기대와 대조한 값이다. 기대 매칭은 `location.file` 일치 + `rule_id`에 기대 규칙 키 포함 + 심각도 범위다. "
      "`High+ 누락`은 기대 High 이상 finding 중 최종 JSON에 없는 수, `pass 뒤집힘`은 기대가 없는 사례(통과·무결점)에서 High 이상이 나온 경우 1이다.")
    w("")
    w("| 사례 | 후보 | 기대 | 실제 finding 요약 | 판정 일치 | High+ 누락 | pass 뒤집힘 | 소요(초) | 비고 |")
    w("|---|---|---|---|---|---|---|---|---|")
    cmap = {(r["case"], r["cand"]): r for r in rows["checker"]}
    for c in cases:
        for cid in CHECKER_CANDS:
            r = cmap.get((c["id"], cid))
            if r is None:
                w("| %s | %s | %s | 미실행 | 결과 없음 | - | - | - | 미실행 |" % (c["id"], cid, _c(describe_expected(c))))
            elif not r.get("result"):
                w("| %s | %s | %s | 결과 없음 | 결과 없음 | - | - | %s | %s |" % (
                    c["id"], cid, _c(r["expected"]), _f(r.get("elapsed_s")), _c("결과 없음: " + str(r.get("reason")) + (" / " + _usage_note(r) if _usage_note(r) else ""))))
            else:
                note = "; ".join(r.get("notes") or [])
                u = _usage_note(r)
                w("| %s | %s | %s | %s | %s | %d | %d | %s | %s |" % (
                    c["id"], cid, _c(r["expected"]), _c(r["summary"]), "O" if r["match"] else "X", r["high_miss"], r["flip"],
                    _f(r.get("elapsed_s")), _c("; ".join(x for x in (note, u) if x))))
    w("")
    w("## 3. evaluator 결과")
    w("")
    w("### 3.1 호출별 (%d행)" % len(rows["evaluator"]))
    w("")
    w("기대 판정은 170 `EVAL-RESULT.md`의 기대 verdict 열(통과 3건=pass, 결함 5건=fail과 해당 실패 축)이다. 결함 fixture 5건은 `design-gate start`의 결정론 검사를 통과하지 않아 "
      "(170이 '실제로 돌리지 않는다'고 명시한 합성 최소 재현본) 임시 fixture의 `design_gate.status`만 `evaluating`으로 되돌려 열린 시도로 썼다(시도의 `bundle_hash`·`iteration`은 `start`가 만든 그대로).")
    w("")
    w("| 사례 | 후보 | scope | 기대 | 실제 | 소요(초) | 비고 |")
    w("|---|---|---|---|---|---|---|")
    for r in rows["evaluator"]:
        w("| %s | %s | %s | %s | %s | %s | %s |" % (r["case"], r["cand"], r["scope"], _c(r["expected"]), _c(r["actual"]), _f(r.get("elapsed_s")),
                                                _c(("결과 없음: " + str(r["reason"]) if not r["result"] else "") + (" / " if not r["result"] and _usage_note(r) else "") + _usage_note(r))))
    w("")
    w("### 3.2 결합 (실제 `design-gate combine`, %d행)" % len(rows["combined"]))
    w("")
    w("결합 소요는 두 호출 중 긴 쪽(벽시계)이고, 비고의 `쌍 벽시계`는 두 호출을 동시에 시작해 둘 다 끝날 때까지의 시간이다. "
      "`verdict 일치`는 170 단일 호출 기대 verdict와의 일치(H-2)이고, `결함 누락`은 결함 사례에서 결합 verdict가 fail이 아니거나 기대 실패 축이 FAIL이 아닌 경우 1이다.")
    w("")
    w("| 사례 | 후보 | 기대 verdict | 결합 verdict | 기대 실패 축 | 실제 FAIL 축 | verdict 일치 | 결함 누락 | pass 뒤집힘 | design 소요(초) | scenario 소요(초) | 결합 소요(초) | 비고 |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows["combined"]:
        axes_exp = ",".join(r["expected_axes"]) or "-"
        if not r.get("result"):
            w("| %s | %s | %s | 결과 없음 | %s | - | 결과 없음 | - | - | %s | %s | %s | %s |" % (
                r["case"], r["cand"], r["expected_verdict"], axes_exp, _f(r.get("d_elapsed_s")), _f(r.get("s_elapsed_s")),
                _f(r.get("elapsed_s")), _c("결과 없음: " + str(r.get("reason")))))
        else:
            note = ["쌍 벽시계 %s" % _f(r.get("pair_wall_s")), "rewrite_target=%s" % r.get("rewrite_target")]
            if r.get("missed_axes"):
                note.append("못 잡은 축: " + ",".join(r["missed_axes"]))
            w("| %s | %s | %s | %s | %s | %s | %s | %d | %d | %s | %s | %s | %s |" % (
                r["case"], r["cand"], r["expected_verdict"], r["verdict"], axes_exp, ",".join(r["fail_axes"]) or "없음",
                "O" if r["match"] else "X", r["missed"], r["flip"], _f(r.get("d_elapsed_s")), _f(r.get("s_elapsed_s")),
                _f(r.get("elapsed_s")), _c("; ".join(note))))
    w("")
    w("## 4. 후보별 채택 판정 (D-13 규칙)")
    w("")
    w("규칙: 결함을 놓친 건수 0 **AND** pass 사례를 뒤집은 건수 0이면 \"채택 가능\"이고, checker는 사전 검사 finding과 합산해 High 이상 누락 0건이어야 한다. "
      "결과 없음·미실행 행이 있으면 그 후보는 측정이 불완전하므로 \"채택 불가\"로 둔다(결과 없음을 통과로 세지 않는다).")
    w("")
    w("| 후보 | 대상 | 결과 있음/전체 | 결함·High+ 누락 | pass 뒤집힘 | 판정 | 이유 |")
    w("|---|---|---|---|---|---|---|")
    for cid in list(CHECKER_CANDS) + list(EVAL_CANDS):
        a = ad[cid]
        w("| %s | %s | %d/%d | %d | %d | %s | %s |" % (cid, a["agent"], a["result"], a["n"], a["missed"], a["flip"],
                                                      "채택 가능" if a["adoptable"] else "채택 불가", _c("; ".join(a["reasons"]) or "-")))
    w("")
    w("### 4.1 소요 시간 요약 (결과 있는 행, 초)")
    w("")
    w("| 후보 | 대상 | 평균 | 중앙값 | 최대 | 판정 일치 아닌 행 |")
    w("|---|---|---|---|---|---|")
    for cid in list(CHECKER_CANDS) + list(EVAL_CANDS):
        a = ad[cid]
        w("| %s | %s | %s | %s | %s | %d |" % (cid, a["agent"], _f(a["mean_s"]), _f(a["median_s"]), _f(a["max_s"]), a["mismatch"]))
    w("")
    w("evaluator 소요는 결합 소요(두 호출 중 긴 쪽)이고, checker 소요는 호출 1건의 벽시계다.")
    w("")
    w("### 4.2 checker pass 뒤집힘의 출처 분리 (참고)")
    w("")
    w("D-13 판정은 위 4절 표 그대로다. 아래는 같은 데이터에서 뒤집힘이 결정론 사전 검사(모든 후보에 같은 결과) 때문인지 모델 때문인지 가른 참고 표다.")
    w("")
    w("| 후보 | pass 뒤집힘 | 그중 사전 검사 finding만으로 발생 | 모델 finding이 관여한 뒤집힘 |")
    w("|---|---|---|---|")
    for cid in CHECKER_CANDS:
        a = ad[cid]
        w("| %s | %d | %d | %d |" % (cid, a["flip"], a["flip_precheck_only"], a["flip"] - a["flip_precheck_only"]))
    w("")
    w("## 5. 추천 (결정은 캡틴)")
    w("")
    for agent, ids in (("checker", CHECKER_CANDS), ("evaluator", EVAL_CANDS)):
        okc = [cid for cid in ids if ad[cid]["adoptable"]]
        if len(okc) >= 2:
            best = min(okc, key=lambda x: ad[x]["mean_s"] if ad[x]["mean_s"] is not None else 1e9)
            w("- %s: 채택 가능 후보 %s. 평균 소요 시간이 가장 짧은 **%s**(%s초)를 추천한다. 결정은 캡틴이 한다." % (
                agent, ", ".join(okc), best, _f(ad[best]["mean_s"])))
            others = sorted((ad[x]["mean_s"], x) for x in okc if x != best and ad[x]["mean_s"] is not None)
            if others and ad[best]["mean_s"] and (others[0][0] - ad[best]["mean_s"]) / ad[best]["mean_s"] < 0.05:
                w("  - 차순위 %s(%s초)와 평균 차이가 5%% 미만이라 1회 측정 분산 안쪽일 수 있다. 시간만으로는 두 후보를 가르기 어렵다." % (
                    others[0][1], _f(others[0][0])))
        elif len(okc) == 1:
            w("- %s: 채택 가능 후보는 %s 하나뿐이다. 결정은 캡틴이 한다." % (agent, okc[0]))
        else:
            w("- %s: 채택 가능 후보가 없다. 결정 전에는 현행을 유지한다(C-3). 결정은 캡틴이 한다." % agent)
    w("")
    if Path(notes_path).is_file():
        w(Path(notes_path).read_text(encoding="utf-8").rstrip())
        w("")
    w("## 공식 문서 근거")
    w("")
    Path(path).write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
