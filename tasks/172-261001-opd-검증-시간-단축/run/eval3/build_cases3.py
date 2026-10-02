#!/usr/bin/env python3
"""ADD-3 평가 세트 구성기: clean 3건(원본 pass 3건 복사본 + 지적 판정 real 항목을 닫는 문장 추가), borderline 3건(원본 pass 그대로),
defect 5건(원본 그대로)을 불투명 ID d01~d11로 배치한다. 원본(tasks/170-.../run/eval-set)은 수정하지 않는다.

사용: python3 build_cases3.py --cases-root <dir> --mapping <mapping.json> --diffs-dir <dir>
 - cases-root/dNN/{TASK,PLAN,TEST-SCENARIO}.md 를 만든다.
 - mapping.json 은 호출이 끝날 때까지 작업 경로 밖에 둔다. diffs-dir 는 clean 수정 diff(라벨 포함)를 저장한다.
"""
import argparse
import difflib
import json
import random
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
EV_SET = HERE.parents[1].parent / "170-261001-opds-설계-게이트-회차-단축" / "run" / "eval-set"

# (원본 사례, 파일, 이전 문구, 새 문구, 근거 지적 ID)  — 지적 ID는 adjudication.md 의 행 번호
EDITS = {
    "pass-161": [
        ("PLAN.md",
         "① `run`이 없으면 아무 명령도 실행하지 않고 `not_configured`(사유 `run_missing`). ② `check`가 있으면",
         "① `run`이 없으면 아무 명령도 실행하지 않고 `not_configured`(사유 `run_missing`)이며, `run_files`만 있고 `run`이 없는 도구도 `run`이 없는 것으로 본다. ② `check`가 있으면",
         "A5"),
        ("PLAN.md",
         "도구에 `run_files`가 있으면 프로젝트 안에 실재하고 `file_globs`에 맞는 파일만 넘긴다. 0개면 명령을 실행하지 않고 `not_applicable`(사유 `no_matching_files`)이다.",
         "도구에 `run_files`가 있으면 프로젝트 안에 실재하고 `file_globs`에 맞는 파일만 넘긴다. `file_globs`는 경로 전체가 아니라 파일 이름(basename)에 `fnmatch`로 맞추므로 하위 디렉터리의 파일도 이름이 맞으면 대상이다. 0개면 `check`를 포함해 아무 명령도 실행하지 않고(이 판정이 D-2 ②의 `check` 실행보다 먼저다) `not_applicable`(사유 `no_matching_files`)이다.",
         "A3,A4"),
        ("PLAN.md",
         "그 외 `pass`. `ok`는",
         "그 외 `pass`. `required: false` 계층이 `fail`이어도 stop-on-fail은 똑같이 적용되어 후속 계층이 `not_run`이 되며, 그때 `not_run`이 된 필수 계층이 있으면 검증하지 못한 필수 계층으로 보아 전체를 `incomplete`(사유 `required_layer_unverified`)로 한다(필수 계층에 `fail`이 있으면 위 규칙대로 `fail`이 먼저다). 전체 `fail`의 최상위 `reason`은 `layer_failed`다. `incomplete` 사유가 둘 이상 해당하면 최상위 `reason`에는 `no_layers_declared`, `required_layer_unverified`, `no_check_executed` 중 앞선 하나만 낸다. `ok`는",
         "A1,A2,A8"),
        ("PLAN.md",
         "`check: {cmd, exit, status}`(실행 시)",
         "`check: {cmd, exit, status}`(실행 시, `check.status`는 `check` exit 0이면 `pass`, 아니면 `fail`)",
         "A8"),
        ("TEST-SCENARIO.md",
         "(b) 모든 계층이 `run_files`만 쓰는 도구이고 `--changed-files`가 어떤 glob에도 맞지 않음",
         "(b) 모든 계층이 `run`과 `run_files`를 함께 가진 도구이고 `--changed-files`가 어떤 glob에도 맞지 않음",
         "A5"),
        ("TEST-SCENARIO.md",
         "어떤 stub도 호출되지 않음",
         "`check` stub을 포함해 어떤 stub도 호출되지 않음",
         "A4"),
    ],
    "pass-163": [
        ("PLAN.md",
         "새 상태가 이 소비자의 허용 집합에 닿는지 W-1에서 조사한다.",
         "새 상태가 이 소비자의 허용 집합에 닿는지 W-1에서 조사한다. 이 소비자들은 이번 변경 대상이 아니므로 영향이 확인돼도 소비자 코드는 바꾸지 않고, W-1의 영향 판정 기록에 닿는 위치와 후속 조치 필요 여부를 남겨 PM에 보고한다.",
         "B1"),
    ],
    "pass-169": [
        ("PLAN.md",
         "문구(§입력 :35-38)만 실제 안전망(금지 규정 + guard id 18)으로 정정한다",
         "문구(§입력 :35-38)를 실제 안전망(금지 규정 + guard id 18)으로 정정하고, §4.2(:132-133)의 `--allocator-root`가 유일한 허용 경로이며 미지정은 거부된다는 서술도 새 동작(미지정이면 task_root 자신에 쓴다)에 맞게 고친다. OPPB가 `--allocator-root`를 명시해 쓰는 절차는 바꾸지 않는다",
         "C1"),
        ("PLAN.md",
         "P5 pre-finalize diff-0 guard)으로 정정한다 |",
         "P5 pre-finalize diff-0 guard)으로 정정한다. 같은 파일 §4.2(:132-133)의 \"`--allocator-root`는 절대경로 허브 루트다. 회고적 학습 쓰기의 유일한 허용 경로이며, 미지정·상대경로는 `allocator_root_required`로 거부된다\"에서 '유일한 허용 경로'와 '미지정 거부' 부분을 새 동작(미지정이면 task_root 자신에 쓴다. 절대경로가 아닌 `--allocator-root`는 계속 거부한다)에 맞게 고친다 |",
         "C1"),
        ("PLAN.md",
         "정정한다(completeness-3). `test_brain_tool.py`",
         "정정한다(completeness-3). `require_write_root` 자신의 docstring(:322-327의 \"워크트리 안에서 `--brain-path` 기본값으로 쓰는 것은 거부한다\")과 add-page·update-page의 `--allocator-root` argparse help(:1540·:1558의 \"명시 인자 전용 — cwd 추론 금지\")도 새 동작에 맞게 함께 정정한다. `test_brain_tool.py`",
         "C2"),
        ("PLAN.md",
         "- `docs/CONVENTIONS.md` — §266 `allocator_root 명시 전달` 규칙이 MEMORY 전용 서술이며 brain-tool을 지칭하지 않는지 확인한다.",
         "- `docs/CONVENTIONS.md` — §266 `allocator_root 명시 전달` 규칙이 MEMORY 전용 서술이며 brain-tool을 지칭하지 않는지 확인한다.\n"
         "- .opal/brain/pages/concept/worktree-task-root-allocator-root-split.md (:39 \"명시 인자 없는 쓰기를 전용 오류로 막는다\") — 파생 지식 스냅샷이다. 이 태스크의 Work item이 직접 고치지 않으며 CLOSE의 op-brain-ingest가 갱신 여부를 판단한다(W-5 백필 대상이 아님).",
         "C3"),
        ("PLAN.md",
         "원래 차단을 유지한다.",
         "원래 차단을 유지한다. 같은 P1에서 이미 끝난 W-2·W-3·W-6·W-7의 문서 변경은 새 계약을 서술하므로 함께 되돌려 코드와 문서가 어긋나지 않게 한다.",
         "C4"),
        ("PLAN.md",
         "`.gitattributes` 2줄",
         "`.gitattributes` 4줄(빈 줄·주석 포함, D-4)",
         "C5"),
        ("PLAN.md",
         "1문장만 추가한다(completeness-1 해소, D-7).",
         "STEP1 근처에 1문장만 추가하고, STEP6의 `ingested_pages` 포함 기준 문장은 D-8·W-6이 별도로 더한다(completeness-1 해소, D-7).",
         "C6"),
    ],
}
DEFECTS = ["defect-162-i1", "defect-163-i1", "defect-167-i2", "defect-168-i2", "defect-169-i2"]
PASSES = ["pass-161", "pass-163", "pass-169"]
FILES = ("TASK.md", "PLAN.md", "TEST-SCENARIO.md")

# 사례 종류별 기대 (run_eval2 EVAL_SPECS 와 동일한 기대 verdict·축)
EXPECT = {
    "defect-162-i1": ("fail", ["decision_clarity", "executability"]),
    "defect-163-i1": ("fail", ["decision_clarity", "executability"]),
    "defect-167-i2": ("fail", ["decision_clarity"]),
    "defect-168-i2": ("fail", ["decision_clarity"]),
    "defect-169-i2": ("fail", ["decision_clarity"]),
}


def build(cases_root, mapping_path, diffs_dir, seed=None):
    cases_root, diffs_dir = Path(cases_root), Path(diffs_dir)
    labels = ["clean-" + p for p in PASSES] + ["borderline-" + p for p in PASSES] + ["defect:" + d for d in DEFECTS]
    rng = random.Random(seed) if seed is not None else random.SystemRandom()
    ids = ["d%02d" % i for i in range(1, len(labels) + 1)]
    rng.shuffle(ids)
    mapping = {}
    if cases_root.exists():
        shutil.rmtree(cases_root)
    diffs_dir.mkdir(parents=True, exist_ok=True)
    for lab, did in zip(labels, ids):
        dest = cases_root / did
        dest.mkdir(parents=True)
        if lab.startswith("clean-"):
            src = lab[len("clean-"):]
            kind = "clean"
        elif lab.startswith("borderline-"):
            src = lab[len("borderline-"):]
            kind = "borderline"
        else:
            src = lab.split(":")[1]
            kind = "defect"
        texts = {f: (EV_SET / src / f).read_text(encoding="utf-8") for f in FILES}
        if kind == "clean":
            for fname, old, new, why in EDITS[src]:
                assert texts[fname].count(old) == 1, (src, fname, old[:40], texts[fname].count(old))
                texts[fname] = texts[fname].replace(old, new)
            for f in FILES:
                orig = (EV_SET / src / f).read_text(encoding="utf-8")
                if orig != texts[f]:
                    diff = "".join(difflib.unified_diff(
                        orig.splitlines(keepends=True), texts[f].splitlines(keepends=True),
                        fromfile="eval-set/%s/%s" % (src, f), tofile="eval3/clean-%s/%s" % (src, f), n=0))
                    (diffs_dir / ("clean-%s__%s.diff" % (src, f.replace(".md", "")))).write_text(diff, encoding="utf-8")
        for f in FILES:
            (dest / f).write_text(texts[f], encoding="utf-8")
        exp = EXPECT.get(src) if kind == "defect" else ("pass", [])
        mapping[did] = {"label": lab, "kind": kind, "source": src, "expected_verdict": exp[0], "expected_axes": exp[1]}
    Path(mapping_path).write_text(json.dumps(mapping, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    return mapping


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases-root", required=True)
    ap.add_argument("--mapping", required=True)
    ap.add_argument("--diffs-dir", required=True)
    a = ap.parse_args()
    mp = build(a.cases_root, a.mapping, a.diffs_dir)
    print(json.dumps({k: v["kind"] for k, v in sorted(mp.items())}, ensure_ascii=False))
