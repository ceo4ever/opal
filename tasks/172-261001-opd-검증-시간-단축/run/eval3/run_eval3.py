#!/usr/bin/env python3
"""ADD-3 측정기: evaluator 후보 E0·E1·E3를 정비된 평가 세트(d01~d11) x 반복 3회로 잰다 (PLAN D-13 계열, RULES.md 사전 고정).

run/eval2/run_eval2_e3.py 의 함수(make_fixture·make_receipt·evaluator_prompt·run_claude·eval_evaluator 등)를 그대로 재사용한다(원본 수정 없음).
달라진 점: 사례 11건(불투명 ID), 후보 E0/E1/E3, 사례x후보x반복 3 = 99 trial(각 trial = scope design + scope scenario 동시 두 호출),
trial 순서 무작위, trial 마다 fresh fixture 폴더(불투명 토큰 이름)·fresh receipt, 호출 직후 결합(`design-gate combine`), 형식 오류 분류.
재시도 없음: 한 호출의 실패는 그대로 기록한다. 이어하기: results/<token>.json 이 있는 trial 은 건너뛴다.

사용:
  python3 run_eval3.py --cases-root <dir> --mapping <mapping.json> --work-root <dir> [--max-parallel 6] [--limit N] [--dry-run]
  python3 run_eval3.py --mapping <mapping.json> --work-root <dir> --aggregate   # results/ 를 집계해 results4.json 과 표를 출력
"""
import argparse
import importlib.util
import json
import math
import os
import random
import shutil
import statistics
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_REPO = HERE.parents[3]
E2_PATH = HERE.parent / "eval2" / "run_eval2_e3.py"

spec = importlib.util.spec_from_file_location("eval2m", str(E2_PATH))
m = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(E2_PATH.parent))
spec.loader.exec_module(m)

CANDS = {
    "E0": {"model": "opus", "effort": None, "label": "opus 미지정"},
    "E1": {"model": "opus", "effort": "medium", "label": "opus medium"},
    "E3": {"model": "opus", "effort": "low", "label": "opus low"},
}
REPS = 3
AXES = m.AXES
SCORE_KEYS = ("goal", "adoption", "boundary")


# ---------------------------------------------------------------- 형식 오류 분류 (RULES.md §형식 오류)
def classify_call(rec, scope):
    """None 이면 정상, 아니면 (유형 a/b/c/d, 설명)."""
    resp = rec.get("response")
    if rec.get("error") or not resp:
        err = rec.get("error") or ("응답 JSON 아님(rc=%s)" % rec.get("returncode"))
        return ("d", ("타임아웃/호출 실패: %s" % err)[:160])
    if resp.get("is_error"):
        txt = ("%s %s" % (resp.get("subtype"), resp.get("result"))).lower()
        kind = "타임아웃" if ("timeout" in txt or "시간" in txt or "timed out" in txt) else "응답 오류"
        return ("d", "%s: %s" % (kind, txt[:140]))
    text = str(resp.get("result") or "")
    objs = m.extract_json_objects(text)
    cands = [o for o in objs if "input_bundle_hash" in o and (o.get("scope") == scope or scope in o)]
    if not cands:
        if "input_bundle_hash" in text:
            return ("b", "JSON 문법 오류(계약 JSON으로 보이는 블록이 파싱되지 않음)")
        return ("a", "응답에서 계약 JSON을 찾지 못함")
    part = cands[-1]
    miss = []
    for k in ("input_bundle_hash", "iteration", "scope", "status"):
        if k not in part:
            miss.append(k)
    if scope == "design":
        d = part.get("design")
        axes = (d or {}).get("axes") if isinstance(d, dict) else None
        if not isinstance(axes, dict):
            miss.append("design.axes")
        else:
            for a in AXES:
                if str(axes.get(a)).upper() not in ("PASS", "FAIL"):
                    miss.append("axes.%s" % a)
        if not isinstance((d or {}).get("gaps") if isinstance(d, dict) else None, list):
            miss.append("design.gaps")
    else:
        s = part.get("scenario")
        sc = (s or {}).get("scores") if isinstance(s, dict) else None
        if not isinstance(sc, dict):
            miss.append("scenario.scores")
        else:
            for k in SCORE_KEYS:
                if not isinstance(sc.get(k), (int, float)) or isinstance(sc.get(k), bool):
                    miss.append("scores.%s" % k)
        if not isinstance((s or {}).get("average") if isinstance(s, dict) else None, (int, float)):
            miss.append("scenario.average")
        if not isinstance((s or {}).get("gaps") if isinstance(s, dict) else None, list):
            miss.append("scenario.gaps")
    if miss:
        return ("c", "필수 키·축·점수 누락: " + ",".join(miss))
    return None


# ---------------------------------------------------------------- trial 실행
def make_plan(mapping, work):
    p = Path(work) / "plan.json"
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    rng = random.SystemRandom()
    trials = [{"case": c, "cand": cand, "rep": r} for c in sorted(mapping) for cand in CANDS for r in range(1, REPS + 1)]
    rng.shuffle(trials)
    used = set()
    for t in trials:
        while True:
            tok = "t%06x" % rng.randrange(1 << 24)
            if tok not in used:
                used.add(tok)
                t["token"] = tok
                break
    plan = {"trials": trials}
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    return plan


def make_trial_unit(t, mapping, repo, sysprompt, work, dry_run):
    results = Path(work) / "results"
    base = Path(work) / "raw" / "ev"
    fx_root = Path(work) / "fx"
    agent = "opal-evaluator-agent"

    def unit():
        tok, cid, cand_id = t["token"], t["case"], t["cand"]
        cand = CANDS[cand_id]
        rpath = results / (tok + ".json")
        if rpath.is_file():
            return
        paths = {s: base / ("%s__%s.json" % (tok, s)) for s in ("design", "scenario")}
        if dry_run:
            print("DRY-RUN", tok, cid, cand_id, t["rep"])
            return
        fx = m.make_fixture(tok, cid, fx_root, repo)
        (base / "fixtures").mkdir(parents=True, exist_ok=True)
        (base / "fixtures" / (tok + ".json")).write_text(json.dumps(fx, ensure_ascii=False), encoding="utf-8")
        receipts = {}
        for scope in ("design", "scenario"):
            if paths[scope].exists():
                continue
            receipts[scope], why = m.make_receipt(repo, Path(work) / "raw" / "receipts" / ("%s__%s.json" % (tok, scope)))
            if why:   # receipt 실패: 호출하지 않고 오류로 기록(재시도 없음)
                paths[scope].parent.mkdir(parents=True, exist_ok=True)
                paths[scope].write_text(json.dumps({"error": why, "elapsed_s": None, "response": None}, ensure_ascii=False),
                                        encoding="utf-8")
        out = {}

        def call(scope):
            if paths[scope].exists():
                out[scope] = json.loads(paths[scope].read_text(encoding="utf-8"))
                return
            prompt = m.evaluator_prompt(scope, fx, receipts[scope], repo)
            out[scope] = m.run_claude(paths[scope], agent, sysprompt, cand, prompt, fx["task_path"], False)
        t0 = time.monotonic()
        th = [threading.Thread(target=call, args=(s,)) for s in ("design", "scenario")]
        for x in th:
            x.start()
        for x in th:
            x.join()
        wall = round(time.monotonic() - t0, 1)
        raws = {"design": out["design"], "scenario": out["scenario"], "pair_wall_s": wall}
        mp = mapping[cid]
        case = {"id": "%s__r%d__%s" % (cid, t["rep"], tok), "expected_verdict": mp["expected_verdict"],
                "expected_axes": mp["expected_axes"]}
        rows, comb = m.eval_evaluator(case, cand_id, fx, raws, Path(work) / "raw" / "combine", repo)
        fmt = {}
        for scope in ("design", "scenario"):
            c = classify_call(out[scope], scope)
            fmt[scope] = None if c is None else {"type": c[0], "detail": c[1]}
        res = {"token": tok, "case": cid, "cand": cand_id, "rep": t["rep"], "kind": mp["kind"], "source": mp["source"],
               "expected_verdict": mp["expected_verdict"], "expected_axes": mp["expected_axes"],
               "rows": rows, "comb": comb, "fmt": fmt, "pair_wall_s": wall,
               "elapsed": {s: out[s].get("elapsed_s") for s in ("design", "scenario")}}
        results.mkdir(parents=True, exist_ok=True)
        rpath.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        try:
            shutil.rmtree(fx["task_path"])
        except Exception:  # noqa: BLE001
            pass
        print("%s %s %s r%d design %6.1fs scenario %6.1fs verdict=%s fmt=%s/%s" % (
            tok, cid, cand_id, t["rep"], out["design"].get("elapsed_s") or -1, out["scenario"].get("elapsed_s") or -1,
            comb.get("verdict"), (fmt["design"] or {}).get("type", "-"), (fmt["scenario"] or {}).get("type", "-")), flush=True)
    return unit


# ---------------------------------------------------------------- 집계
def pctl(vals, p):
    if not vals:
        return None
    s = sorted(vals)
    return s[max(0, math.ceil(p * len(s)) - 1)]   # nearest-rank


def stats(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return {"n": 0}
    return {"n": len(vals), "mean": round(statistics.mean(vals), 1), "median": round(statistics.median(vals), 1),
            "p90": round(pctl(vals, 0.9), 1), "max": round(max(vals), 1)}


def aggregate(work, mapping):
    res = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((Path(work) / "results").glob("*.json"))]
    out = {"n_trials": len(res), "cands": {}, "cases": {}}
    for cand in CANDS:
        rs = [r for r in res if r["cand"] == cand]
        c = {"n_trials": len(rs), "n_calls": 2 * len(rs)}
        fe = {"design": [], "scenario": []}
        for r in rs:
            for s in ("design", "scenario"):
                if r["fmt"][s]:
                    fe[s].append({"token": r["token"], "case": r["case"], "rep": r["rep"], "scope": s, **r["fmt"][s]})
        c["format_errors"] = fe
        c["format_error_count"] = {"design": len(fe["design"]), "scenario": len(fe["scenario"]),
                                   "total": len(fe["design"]) + len(fe["scenario"])}
        c["format_error_types"] = {}
        for s in fe:
            for e in fe[s]:
                c["format_error_types"][e["type"]] = c["format_error_types"].get(e["type"], 0) + 1
        ok = [r for r in rs if r["comb"].get("result")]
        c["combined_ok"] = len(ok)
        c["combined_fail"] = len(rs) - len(ok)
        # 규칙 1: defect
        d = [r for r in rs if r["kind"] == "defect"]
        d_ok = [r for r in d if r["comb"].get("result")]
        c["defect"] = {"trials": len(d), "with_result": len(d_ok), "no_result": len(d) - len(d_ok),
                       "missed": sum(1 for r in d_ok if r["comb"].get("missed") == 1),
                       "missed_worst_case": sum(1 for r in d_ok if r["comb"].get("missed") == 1) + (len(d) - len(d_ok))}
        # 규칙 2: clean
        cl = [r for r in rs if r["kind"] == "clean"]
        cl_ok = [r for r in cl if r["comb"].get("result")]
        c["clean"] = {"trials": len(cl), "with_result": len(cl_ok), "no_result": len(cl) - len(cl_ok),
                      "fail": sum(1 for r in cl_ok if r["comb"].get("verdict") != "pass"),
                      "fail_worst_case": sum(1 for r in cl_ok if r["comb"].get("verdict") != "pass") + (len(cl) - len(cl_ok))}
        bl = [r for r in rs if r["kind"] == "borderline"]
        bl_ok = [r for r in bl if r["comb"].get("result")]
        c["borderline"] = {"trials": len(bl), "with_result": len(bl_ok), "no_result": len(bl) - len(bl_ok),
                           "fail": sum(1 for r in bl_ok if r["comb"].get("verdict") != "pass")}
        # 규칙 판정
        c["rule1"] = c["defect"]["missed"] == 0
        c["rule2"] = c["clean"]["fail"] <= 2
        c["rule3"] = c["format_error_count"]["total"] <= 2
        c["rule4"] = c["combined_fail"] <= 3
        c["adoptable"] = bool(c["rule1"] and c["rule2"] and c["rule3"] and c["rule4"])
        # 소요
        comb_el = [r["comb"].get("elapsed_s") for r in rs]
        call_el = [r["elapsed"][s] for r in rs for s in ("design", "scenario")]
        c["time_combined"] = stats(comb_el)
        c["time_call"] = stats(call_el)
        c["time_call_design"] = stats([r["elapsed"]["design"] for r in rs])
        c["time_call_scenario"] = stats([r["elapsed"]["scenario"] for r in rs])
        c["time_pair_wall"] = stats([r["pair_wall_s"] for r in rs])
        out["cands"][cand] = c
    # 사례별
    for cid in sorted(mapping):
        row = {"label": mapping[cid]["label"], "kind": mapping[cid]["kind"], "cands": {}}
        for cand in CANDS:
            rs = sorted([r for r in res if r["case"] == cid and r["cand"] == cand], key=lambda r: r["rep"])
            row["cands"][cand] = [{"rep": r["rep"], "verdict": r["comb"].get("verdict") if r["comb"].get("result") else "결과없음",
                                   "fail_axes": r["comb"].get("fail_axes"), "missed": r["comb"].get("missed"),
                                   "design_gaps_axes": None} for r in rs]
        out["cases"][cid] = row
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cases-root", default="")
    ap.add_argument("--mapping", required=True)
    ap.add_argument("--work-root", required=True)
    ap.add_argument("--repo-root", default=str(DEFAULT_REPO))
    ap.add_argument("--max-parallel", type=int, default=6)
    ap.add_argument("--limit", type=int, default=0, help="앞에서부터 N trial 만 실행(스모크)")
    ap.add_argument("--only-tokens", default="")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--aggregate", action="store_true")
    ap.add_argument("--out", default=str(HERE))
    a = ap.parse_args(argv)
    mapping = json.loads(Path(a.mapping).read_text(encoding="utf-8"))
    work = Path(a.work_root).resolve()
    if a.aggregate:
        agg = aggregate(work, mapping)
        Path(a.out, "results4.json").write_text(json.dumps(agg, ensure_ascii=False, indent=1), encoding="utf-8")
        print(json.dumps({k: (v if k != "cands" else {c: {kk: vv for kk, vv in cv.items() if kk in (
            "n_trials", "format_error_count", "combined_fail", "defect", "clean", "borderline", "rule1", "rule2", "rule3",
            "rule4", "adoptable", "time_combined")} for c, cv in v.items()}) for k, v in agg.items() if k != "cases"},
            ensure_ascii=False, indent=1))
        return 0
    repo = Path(a.repo_root).resolve()
    m.EV_SET = Path(a.cases_root).resolve()          # make_fixture 가 docs 를 EV_SET/<사례ID> 에서 읽는다
    plan = make_plan(mapping, work)
    trials = plan["trials"]
    if a.only_tokens:
        want = set(a.only_tokens.split(","))
        trials = [t for t in trials if t["token"] in want]
    if a.limit:
        trials = trials[:a.limit]
    sysprompt = m.system_prompt_of(repo, "opal-evaluator-agent")
    units = [(2, make_trial_unit(t, mapping, repo, sysprompt, work, a.dry_run)) for t in trials]
    m.run_units(units, a.max_parallel)
    print(json.dumps({"ok": True, "done": len(list((work / "results").glob("*.json"))) if (work / "results").exists() else 0,
                      "planned": len(plan["trials"])}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
