#!/usr/bin/env python3
"""W-10 재집계: 보정된 convention-precheck로 저장된 checker 응답의 사전 검사·merge를 다시 계산한다.

모델 호출 결과는 사전 검사와 독립이므로 다시 부르지 않는다. 모델 finding은 기존 최종 JSON에서
(기존 사전 검사 finding을 뺀 나머지로) 복원해 보정된 사전 검사와 `merge`한다.
원본은 `*.initial.json`으로 보존한다.

사용: python3 recompute_precheck.py --cases <cases.json(체크아웃이 있는 것)> [--only id,id]
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TOOL = REPO / "opal" / "tools" / "convention-precheck" / "convention_precheck.py"
TS = "2026-10-01T00-00-00"


def key(f):
    return (f.get("fingerprint"), f.get("rule_id"), (f.get("location") or {}).get("file"), (f.get("location") or {}).get("line"))


def run(args):
    p = subprocess.run([sys.executable, str(TOOL)] + args, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stdout + p.stderr)
    return json.loads(p.stdout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", required=True)
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    only = {x for x in a.only.split(",") if x}
    cases = json.loads(Path(a.cases).read_text(encoding="utf-8"))["cases"]
    old_cases = {c["id"]: c for c in json.loads((HERE / "cases.json").read_text(encoding="utf-8"))["cases"]}
    changes = []
    for c in cases:
        if only and c["id"] not in only:
            continue
        tmp = Path(tempfile.mkdtemp(prefix="recompute-"))
        try:
            run(["scan", "--project-root", c["project_root"], "--base-ref", c["base_ref"], "--output-dir", str(tmp),
                 "--timestamp", TS, "--target-files", ",".join(c["target_files"])])
            new_pre = tmp / ("gc-findings-convention-precheck-%s.json" % TS)
            new_rev = tmp / ("convention-review-input-%s.json" % TS)
            newp = json.loads(new_pre.read_text(encoding="utf-8"))
            for cid in ("K0", "K1", "K2", "K3"):
                out = HERE / "raw" / "checker" / ("%s__%s" % (c["id"], cid)) / "out"
                fin = out / ("gc-findings-convention-%s.json" % TS)
                oldpre = out / ("gc-findings-convention-precheck-%s.json" % TS)
                if not fin.is_file() or not oldpre.is_file():
                    continue
                finals = json.loads(fin.read_text(encoding="utf-8"))
                op = json.loads(oldpre.read_text(encoding="utf-8"))
                # 원본 보존
                for p in (fin, oldpre, out / ("convention-review-input-%s.json" % TS)):
                    ini = p.with_name(p.stem + ".initial.json")
                    if p.is_file() and not ini.exists():
                        shutil.copy(p, ini)
                old_keys = {key(f) for f in op["findings"]}
                model = [f for f in finals["findings"] if key(f) not in old_keys]
                mf = tmp / "model.json"
                mf.write_text(json.dumps(model, ensure_ascii=False), encoding="utf-8")
                shutil.copy(new_pre, oldpre)
                shutil.copy(new_rev, out / ("convention-review-input-%s.json" % TS))
                run(["merge", "--precheck", str(oldpre), "--review-input", str(new_rev), "--model-findings", str(mf),
                     "--output", str(fin)])
                nf = json.loads(fin.read_text(encoding="utf-8"))
                d = {key(f) for f in finals["findings"]} ^ {key(f) for f in nf["findings"]}
                if d:
                    changes.append((c["id"], cid, len(finals["findings"]), len(nf["findings"])))
            print("recomputed", c["id"], "precheck findings:", len(newp["findings"]), "old:", len(op["findings"]) if 'op' in dir() else "-")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    print("changed final outputs:", changes)


if __name__ == "__main__":
    main()
