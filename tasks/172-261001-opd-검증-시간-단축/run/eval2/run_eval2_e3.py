#!/usr/bin/env python3
"""E3 측정기 — run_eval2.py 복사·최소 수정본: evaluator 후보 E3(opus + effort low)만 중립 사례 8건으로 측정한다(PLAN D-13).
run_eval2.py와 달라진 점: EVAL_CANDS={E3}, checker 미실행, raw를 raw-e3/에 저장, 보고서는 EVAL-RESULT-3.md(write_report_e3). 호출·프롬프트·fixture·combine은 동일.

(아래는 원본 run_eval2.py 설명)

원본(run_eval.py)과 달라진 점:
  1. 사례 라벨(162-defect, pass-161 …)을 불투명 ID(c01..c18)로 바꾼다. 임시 체크아웃·fixture·receipt·출력 폴더·프롬프트
     안의 경로에는 불투명 ID만 나온다. ID<->라벨 매핑은 mapping.json에만 있고 호출 중에는 스크래치패드(작업 경로 밖)에 둔다.
  2. 호출은 정식 wrapper `~/.opal/tools/opal-agent/run.sh --json ...`이다(raw `claude -p` 아님). 정의는
     저장소 `opal/agents/<이름>/AGENT.md`의 frontmatter 제외 본문을 `--system-prompt`로 준다. `--timeout 300`.
  3. 호출 중 산출(raw)은 스크래치패드 work-root/raw에 쓰고 끝난 뒤 eval2/raw로 옮긴다(에이전트가 태스크 폴더의
     라벨 파일을 우연히 읽지 않게 하려는 격리).
후보 호출은 사례x후보당 1회이고 재시도하지 않는다. 소요 = wrapper 프로세스 시작부터 JSON 수신까지 벽시계 초.

사용:
  python3 run_eval2.py --mapping <mapping.json> [--work-root <dir>] [--part checker|evaluator|all] [--max-parallel 6]
                       [--only cNN,cNN] [--candidates K0,.. ] [--dry-run]
  python3 run_eval2.py --report-only      # eval2/raw 와 eval2/mapping.json 으로 results2.json·EVAL-RESULT-2.md 재생성
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
WRAPPER = os.path.expanduser("~/.opal/tools/opal-agent/run.sh")
sys.path.insert(0, str(HERE))
import build_cases2 as build_cases  # noqa: E402

CHECKER_CANDS = {
    "K0": {"model": "sonnet", "effort": None, "label": "현행"},
    "K1": {"model": "sonnet", "effort": "low", "label": ""},
    "K2": {"model": "sonnet", "effort": "medium", "label": ""},
    "K3": {"model": "haiku", "effort": "medium", "label": ""},
}
EVAL_CANDS = {
    "E3": {"model": "opus", "effort": "low", "label": ""},
}
OLD_EVAL_IDS = ("E0", "E1", "E2")   # 비교용: eval2/results2.json의 기존 측정값(다시 재지 않는다)
SEV_RANK = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
CHECKER_TS = "2026-10-01T00-00-00"
CALL_TIMEOUT = 1800
EV_SET = TASK_DIR.parent / "170-261001-opds-설계-게이트-회차-단축" / "run" / "eval-set"

# 170 EVAL-RESULT.md 기대: pass 3건=pass, 결함 5건=fail(지적 축은 170 표의 "기대 verdict" 열)
EVAL_SPECS = [
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
EVAL_CASES = []   # main()이 매핑을 적용해 채운다: {id(불투명), label, expected_verdict, ...}
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


def system_prompt_of(repo, name):
    """저장소 opal/agents/<이름>/AGENT.md의 frontmatter 제외 본문."""
    return parse_agent_md(Path(repo) / "opal" / "agents" / name / "AGENT.md")["prompt"]


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
    return ("## 이벤트 검증\n- event: `worker.dispatch`\n- receipt: %s\n"
            "- verification: 하네스가 호출 직전 `event-loader load`로 receipt를 새로 만들고 "
            "`event-loader verify --receipt <위> --event worker.dispatch --project-root %s`로 `ok: true`를 확인했다. "
            "너도 진입 게이트대로 직접 verify하고 receipt의 `required_documents[].content` 전문을 적용하라. "
            "verify는 현재 작업 디렉터리와 무관하게 다음 절대경로 명령 그대로 실행한다(다른 --project-root를 쓰지 않는다): "
            "`%s/.opal/tools/event-loader/run.sh verify --receipt %s --event worker.dispatch --project-root %s`\n\n"
            % (receipt, repo, os.path.expanduser("~"), receipt, repo))


def run_claude(raw_path, agent, system_prompt, cand, prompt, cwd, dry_run=False):
    """정식 wrapper(opal-agent)를 1회 실행해 raw_path에 {cmd, elapsed_s, returncode, response, stderr}를 저장한다."""
    raw_path = Path(raw_path)
    if raw_path.exists():
        return json.loads(raw_path.read_text(encoding="utf-8"))   # 재시도 금지: 기존 raw 재사용
    cmd = [WRAPPER, "--json", "--model", cand["model"]]
    if cand["effort"]:
        cmd += ["--effort", cand["effort"]]
    cmd += ["--allowed-tools", "Read,Grep,Glob,Bash", "--cwd", str(cwd), "--opal-bootstrap", "off", "--timeout", "300",
            "--system-prompt", system_prompt, prompt]
    shown = [("<system-prompt %d chars>" % len(c) if c is system_prompt else ("<prompt %d chars>" % len(c) if c is prompt else c))
             for c in cmd]
    if dry_run:
        print("DRY-RUN", raw_path.name, shown)
        return {"dry_run": True}
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    rec = {"agent": agent, "model": cand["model"], "effort": cand["effort"], "cmd": shown}
    try:
        proc = subprocess.Popen(cmd, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            out, err = proc.communicate(timeout=CALL_TIMEOUT)
            rec["returncode"] = proc.returncode
        except subprocess.TimeoutExpired:
            proc.kill()
            out, err = proc.communicate()
            rec["returncode"] = None
            rec["error"] = "하네스 타임아웃(%ds)" % CALL_TIMEOUT
        rec["elapsed_s"] = round(time.monotonic() - started, 1)
        rec["stderr"] = (err or "")[-2000:]
        try:
            rec["response"] = json.loads(out)
        except Exception:
            rec["response"] = None
            rec["stdout_text"] = (out or "")[-4000:]
            if rec.get("returncode") not in (0, None) and not rec.get("error"):
                rec["error"] = "wrapper rc=%s %s" % (rec["returncode"], (err or out or "")[-160:].strip())
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
def make_fixture(case_id, label, fx_root, repo):
    """test_design_gate_parallel --make-fixture로 열린 시도(iteration 1) 임시 태스크를 만든다.
    결정론 검사가 실패하는 결함 fixture는 start가 시도를 deterministic_fail로 닫으므로, 임시 fixture의
    design_gate.status만 evaluating으로 되돌려 열린 시도로 쓴다(시도의 bundle_hash·iteration은 그대로)."""
    target = Path(fx_root) / case_id
    docs = EV_SET / label
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
def load_mapping(path):
    mp = json.loads(Path(path).read_text(encoding="utf-8"))
    return mp


def apply_mapping(mp):
    EVAL_CASES.clear()
    for spec in EVAL_SPECS:
        e = dict(spec)
        e["label"] = spec["id"]
        e["id"] = mp["evaluator"][spec["id"]]
        EVAL_CASES.append(e)
    EVAL_CASES.sort(key=lambda e: e["id"])


def main(argv=None):
    import shutil
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mapping", default="", help="호출 중 사용할 비공개 mapping.json(작업 경로 밖). report-only는 eval2/mapping.json")
    ap.add_argument("--only", default="", help="쉼표로 구분한 불투명 ID만 실행")
    ap.add_argument("--max-parallel", type=int, default=6)
    ap.add_argument("--out", default=str(HERE), help="raw-e3/ 와 results3.json 폴더")
    ap.add_argument("--work-root", default=str(Path(os.environ.get("TMPDIR", "/tmp")) / "opal-172-eval-e3"))
    ap.add_argument("--repo-root", default=str(DEFAULT_REPO))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args(argv)
    repo, out, work = Path(args.repo_root).resolve(), Path(args.out).resolve(), Path(args.work_root).resolve()
    only = {x for x in args.only.split(",") if x}
    mp = load_mapping(args.mapping if args.mapping else out / "mapping.json")
    apply_mapping(mp)
    raw_root = out / "raw-e3" if args.report_only else work / "raw-e3"
    fx_root = work / "fx"
    rows = {"evaluator": [], "combined": []}
    if not args.report_only:
        ev_agent = "opal-evaluator-agent"
        ev_sys = system_prompt_of(repo, ev_agent)
        fixtures, units_ev = {}, []
        for ec in EVAL_CASES:
            if only and ec["id"] not in only:
                continue
            if args.dry_run:
                fixtures[ec["id"]] = {"task_path": str(fx_root / ec["id"]), "bundle_hash": "<hash>", "seeded": None}
            else:
                fixtures[ec["id"]] = make_fixture(ec["id"], ec["label"], fx_root, repo)
                (raw_root / "evaluator").mkdir(parents=True, exist_ok=True)
                (raw_root / "evaluator" / ("fixture-%s.json" % ec["id"])).write_text(
                    json.dumps(fixtures[ec["id"]], ensure_ascii=False, indent=1), encoding="utf-8")
        for ec in EVAL_CASES:
            if ec["id"] not in fixtures:
                continue
            for cid, cand in EVAL_CANDS.items():
                units_ev.append((2, make_evaluator_unit(ec, cid, cand, ev_agent, ev_sys, fixtures[ec["id"]], repo,
                                                        raw_root, work, args.dry_run)))
        run_units(units_ev, args.max_parallel)
        if args.dry_run:
            return 0
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
    if not args.report_only:
        out.mkdir(parents=True, exist_ok=True)
        shutil.copytree(raw_root, out / "raw-e3", dirs_exist_ok=True)
    (out / "results3.json").write_text(json.dumps({"eval_cases": EVAL_CASES, "rows": rows}, ensure_ascii=False, indent=1),
                                       encoding="utf-8")
    print(json.dumps({"ok": True, "evaluator_rows": len(rows["evaluator"]), "combined_rows": len(rows["combined"])}))
    return 0


def make_evaluator_unit(ec, cid, cand, agent, sysprompt, fx, repo, raw_root, work, dry_run):
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
            out[scope] = run_claude(paths[scope], agent, sysprompt, cand, prompt, fx["task_path"], dry_run)
        t0 = time.monotonic()
        threads = [threading.Thread(target=call, args=(s,)) for s in ("design", "scenario")]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        if not dry_run:
            wall = round(time.monotonic() - t0, 1)
            (base / ("%s__%s__pair.json" % (ec["id"], cid))).write_text(json.dumps({"pair_wall_s": wall}), encoding="utf-8")
            print("evaluator %-6s %s design %6.1fs scenario %6.1fs pair %6.1fs" % (
                ec["id"], cid, (out.get("design") or {}).get("elapsed_s") or -1,
                (out.get("scenario") or {}).get("elapsed_s") or -1, wall), flush=True)
    return unit

# ---------------------------------------------------------------- 보고서 (표 생성은 results3.json 기준; EVAL-RESULT-3.md 본문은 수작업 작성)
def _c(text):
    return str(text).replace("|", "/").replace("\n", " ").strip()


def _f(x):
    return "-" if x is None else ("%.1f" % x)


if __name__ == "__main__":
    sys.exit(main())
