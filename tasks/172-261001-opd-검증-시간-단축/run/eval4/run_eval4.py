#!/usr/bin/env python3
"""ADD-4 보조 측정기: run/eval3/run_eval3.py 를 모듈로 로드해 재사용한다(원본 수정 없음).
바꾸는 것: (a) CANDS = E1·E3 (b) make_fixture 래핑 — fixture 생성 뒤 EV_SET/<사례>/REQUEST.md 가 있으면 task_path 로 복사.
사용법은 run_eval3.py 와 같다. RULES-ADD4.md 참조."""
import importlib.util
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("eval3m", str(HERE.parent / "eval3" / "run_eval3.py"))
r3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r3)

r3.CANDS = {"E1": r3.CANDS["E1"], "E3": r3.CANDS["E3"]}

_orig = r3.m.make_fixture


def make_fixture(case_id, label, fx_root, repo):
    info = _orig(case_id, label, fx_root, repo)
    req = Path(r3.m.EV_SET) / label / "REQUEST.md"
    if req.is_file():
        shutil.copyfile(req, Path(info["task_path"]) / "REQUEST.md")
        info["request_md"] = True
    return info


r3.m.make_fixture = make_fixture

if __name__ == "__main__":
    sys.exit(r3.main())
