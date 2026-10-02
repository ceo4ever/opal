#!/usr/bin/env python3
"""ADD-4 사례 구성: ADD-3 clean 3건을 e01~e03(무작위)로 복사하고, REQUEST.md 참조 사례에만 REQUEST.md를 추가한다.
사용: python3 build_cases4.py --out <e4w>   (cases/, mapping.json 생성)"""
import argparse, json, random, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE.parent
REPO = HERE.parents[3]
DOCS = ("TASK.md", "PLAN.md", "TEST-SCENARIO.md")
REQ = {
    "pass-161": ("624ea8a0", "tasks/161-260927-opd-검증도구-실행정확성-복구/REQUEST.md"),
    "pass-163": ("7a6b3017", "tasks/163-260927-opds-코덱스-워크트리-부팅-소유권-복구/REQUEST.md"),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out).resolve()
    src_map = json.loads((RUN / "eval3" / "mapping.json").read_text(encoding="utf-8"))
    clean = sorted(k for k, v in src_map.items() if v["kind"] == "clean")
    ids = ["e%02d" % i for i in range(1, len(clean) + 1)]
    random.SystemRandom().shuffle(ids)
    mapping = {}
    for old, new in zip(clean, ids):
        dst = out / "cases" / new
        dst.mkdir(parents=True, exist_ok=True)
        for d in DOCS:
            shutil.copyfile(RUN / "eval3" / "cases" / old / d, dst / d)
            if subprocess.run(["cmp", str(RUN / "eval3" / "cases" / old / d), str(dst / d)]).returncode != 0:
                sys.exit("cmp 불일치: %s/%s" % (old, d))
        v = src_map[old]
        added = v["source"] in REQ
        if added:
            commit, path = REQ[v["source"]]
            (dst / "REQUEST.md").write_bytes(subprocess.run(["git", "-C", str(REPO), "show", "%s:%s" % (commit, path)],
                                                              check=True, capture_output=True).stdout)
        mapping[new] = {"label": v["label"], "kind": "clean", "source": v["source"], "expected_verdict": "pass",
                        "expected_axes": [], "request_md_added": added}
    (out / "mapping.json").write_text(json.dumps(dict(sorted(mapping.items())), ensure_ascii=False, indent=1), encoding="utf-8")
    print("ok", len(mapping))


if __name__ == "__main__":
    main()
