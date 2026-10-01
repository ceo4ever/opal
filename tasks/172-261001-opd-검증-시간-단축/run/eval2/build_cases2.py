#!/usr/bin/env python3
"""W-10 재측정(중립 경로) checker 평가 세트(10건) 구축기 — run/eval/build_cases.py 복사본.

달라진 점: 사례 id(`162-defect` 등) 대신 불투명 ID(`cNN`)로 임시 폴더를 만든다. 임시 체크아웃 경로는
`<work-root>/n/cNN/repo`이고, 사례 라벨은 mapping.json(비공개 위치)에만 있다. 과거 4건은 `git worktree add --detach`,
합성 6건은 임시 git 저장소로 만든다. cases2.json의 id는 불투명 ID이며 expected/target_files는 원본과 같다.

사용:
  python3 build_cases2.py --mapping <mapping.json> [--work-root <dir>] [--out <dir>] [--repo-root <dir>]
  python3 build_cases2.py --cleanup --mapping <mapping.json> [--work-root <dir>] [--out <dir>]
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_REPO = HERE.parents[3]
DEFAULT_WORK = Path(tempfile.gettempdir()) / "opal-172-eval-cases"

# 기대 finding의 rule 키는 finding.rule_id에 포함되어야 하는 부분 문자열이다.
KEY_HEADER = "@header"
KEY_FRONT = "YAML Frontmatter"
KEY_HISTORY = "opal-doc-standard"
KEY_NAMING = "파일/폴더"
KEY_LANG = "언어 규칙"

# 과거 기록 4건: (id, 설명, 기준 ref, 체크아웃 커밋, 기대, 참고 gc-findings 기록)
PAST = [
    {
        "id": "162-defect", "base_ref": "48f25a5a^", "commit": "48f25a5a",
        "desc": "과거 162 결함: @header 규칙 High 2건이 PM Gate 이후 발견됨",
        "expected": [
            {"rule_key": KEY_HEADER, "file": "opal/tools/event-loader/tests/test_event_loader_test_event.py",
             "min_severity": "high"},
            {"rule_key": KEY_HEADER, "file": "opal/tools/state-tool/tests/test_state_tool_test_cycle.py",
             "min_severity": "high"},
        ],
        "history": None,
    },
    {
        "id": "161-pass", "base_ref": "624ea8a0^", "commit": "47414d6a",
        "desc": "과거 161 통과 구간", "expected": [],
        "history": "tasks/161-260927-opd-검증도구-실행정확성-복구/gc-findings-convention-2026-09-27T21-02-28.json",
    },
    {
        "id": "163-pass", "base_ref": "7a6b3017^", "commit": "7a6b3017",
        "desc": "과거 163 통과 구간", "expected": [],
        "history": "tasks/163-260927-opds-코덱스-워크트리-부팅-소유권-복구/gc-findings-convention-2026-09-27T22-19-00.json",
    },
    {
        "id": "169-pass", "base_ref": "502115de^", "commit": "502115de",
        "desc": "과거 169 통과 구간", "expected": [],
        "history": "tasks/169-261001-opds-워크트리-CLOSE-지식-반영/gc-findings-convention-2026-09-30T23-50-35.json",
    },
]

SYNTHETIC_IDS = ["syn-m1-skill-no-description", "syn-m2-changelog-section", "syn-m3-camelcase-py",
                 "syn-j1-korean-identifier", "syn-j2-english-doc-section", "syn-ok-clean"]

BASE_SKILL = """---
name: op-demo-check
description: |
  **데모 검사 스킬**. 호출자가 지정한 데모 파일 목록을 읽기 전용으로 검사하고 결과를 보고한다.
  필수 입력: project_root, target_files.
---

# op-demo-check

데모 파일을 검사한다.

## 절차

1. 입력 `target_files`의 존재를 확인한다.
2. 각 파일을 읽고 결과를 요약한다.
"""

BASE_PY = '''"""
@header {
  "module": "demo_tool",
  "layer": "util",
  "domain": "opal-workspace",
  "description": "데모용 숫자 유틸. 숫자 목록의 평균을 구하는 average 함수를 제공한다.",
  "exports": ["average"],
  "depends": []
}
"""


def average(values):
    """숫자 목록의 평균을 반환한다. 빈 목록이면 0.0을 반환한다."""
    if not values:
        return 0.0
    return sum(values) / len(values)
'''

BASE_DOC = """# 데모 가이드

> 데모 도구의 사용법을 설명한다.

## 개요

`demo_tool.average`는 숫자 목록의 평균을 구한다. 빈 목록은 0.0이다.

## 제약

- 입력은 숫자 목록이어야 한다.
"""

BASE_README = """# demo-tool

> 데모용 숫자 유틸 도구

## 사용법

```python
from demo_tool import average
average([1, 2, 3])
```
"""

CHANGED_SKILL = """---
name: op-demo-check
---

# op-demo-check

데모 파일을 검사한다.

## 절차

1. 입력 `target_files`의 존재를 확인한다.
2. 각 파일을 읽고 결과를 요약한다.
3. 결과를 `output_dir`에 쓴다.
"""

CHANGELOG_SECTION = """
## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.1 | 2026-10-01 | 제약 절 보강 |
| v1.0 | 2026-09-01 | 최초 작성 |
"""

CAMEL_PY = '''"""
@header {
  "module": "demo_helper",
  "layer": "util",
  "domain": "opal-workspace",
  "description": "데모용 문자열 유틸. 문자열 앞뒤 공백을 제거해 반환하는 clean_text 함수를 제공한다.",
  "exports": ["clean_text"],
  "depends": []
}
"""


def clean_text(text):
    """문자열 앞뒤 공백을 제거해 반환한다."""
    return text.strip()
'''

KOREAN_FUNC = '''

def 합계_계산(숫자_목록):
    """숫자 목록의 합계를 반환한다."""
    결과 = 0
    for 숫자 in 숫자_목록:
        결과 += 숫자
    return 결과
'''

ENGLISH_SECTION = """
## 사용 예시

The average function accepts any list of numbers and returns their arithmetic mean.
When the list is empty, the function returns 0.0 instead of raising an error.

Callers should validate that every element is numeric before calling the function,
because the function does not coerce strings or other types and will raise a TypeError.
"""

OK_FUNC = '''

def total(values):
    """숫자 목록의 합계를 반환한다."""
    result = 0
    for value in values:
        result += value
    return result
'''

OK_SECTION = """
## 사용 예시

`demo_tool.total`은 숫자 목록의 합계를 구한다. 빈 목록이면 0을 반환한다.
호출자는 모든 원소가 숫자인지 먼저 확인해야 한다.
"""


def sh(args, cwd=None, check=True):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if check and p.returncode != 0:
        raise RuntimeError("command failed: %s\n%s%s" % (" ".join(map(str, args)), p.stdout, p.stderr))
    return p


def write(root, rel, text):
    path = Path(root) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def git_commit(root, message):
    sh(["git", "add", "-A"], cwd=root)
    sh(["git", "-c", "user.name=eval", "-c", "user.email=eval@example.invalid", "commit", "-q", "-m", message],
       cwd=root)


def make_synthetic_repo(repo_root, dest):
    """기준 커밋 하나가 있는 임시 git 저장소를 만든다. 프레임워크 기준 문서를 사본으로 둔다."""
    dest.mkdir(parents=True, exist_ok=True)
    sh(["git", "init", "-q", "-b", "main"], cwd=dest)
    for rel in ("docs/CONVENTIONS.md", ".opal/code-scan.json",
                "opal/core/references/header-standard.md",
                "opal/core/references/opal-doc-standard.md",
                "opal/core/references/conventions-hub-model.md",
                "opal/core/references/harness/gc-finding-schema.md"):
        src = Path(repo_root) / rel
        if src.is_file():
            write(dest, rel, src.read_text(encoding="utf-8"))
    write(dest, "opal/skills/op-demo-check/SKILL.md", BASE_SKILL)
    write(dest, "opal/tools/demo-tool/demo_tool.py", BASE_PY)
    write(dest, "opal/tools/demo-tool/README.md", BASE_README)
    write(dest, "opal/core/references/demo-guide.md", BASE_DOC)
    git_commit(dest, "base")


def synthetic_case(cid, repo_root, work_root, opaque):
    case_dir = work_root / "n" / opaque
    repo = case_dir / "repo"
    make_synthetic_repo(repo_root, repo)
    base_sha = sh(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
    expected, changed, desc = [], [], ""
    if cid == "syn-m1-skill-no-description":
        write(repo, "opal/skills/op-demo-check/SKILL.md", CHANGED_SKILL)
        changed = ["opal/skills/op-demo-check/SKILL.md"]
        desc = "기계 규칙: 기존 SKILL.md에서 frontmatter `description` 제거"
        expected = [{"rule_key": KEY_FRONT, "file": changed[0], "min_severity": "high"}]
    elif cid == "syn-m2-changelog-section":
        doc = (repo / "opal/core/references/demo-guide.md").read_text(encoding="utf-8")
        write(repo, "opal/core/references/demo-guide.md", doc + CHANGELOG_SECTION)
        changed = ["opal/core/references/demo-guide.md"]
        desc = "기계 규칙: 기존 문서에 새 `## 변경이력` 절 추가"
        expected = [{"rule_key": KEY_HISTORY, "file": changed[0], "min_severity": "medium"}]
    elif cid == "syn-m3-camelcase-py":
        write(repo, "opal/tools/demo-tool/demoHelper.py", CAMEL_PY)
        changed = ["opal/tools/demo-tool/demoHelper.py"]
        desc = "기계 규칙: camelCase 파이썬 파일명 추가(@header는 정상)"
        expected = [{"rule_key": KEY_NAMING, "file": changed[0], "min_severity": "medium"}]
    elif cid == "syn-j1-korean-identifier":
        py = (repo / "opal/tools/demo-tool/demo_tool.py").read_text(encoding="utf-8")
        write(repo, "opal/tools/demo-tool/demo_tool.py", py + KOREAN_FUNC)
        changed = ["opal/tools/demo-tool/demo_tool.py"]
        desc = "판단 규칙: 신규 함수에 한글 식별자 사용(docs/CONVENTIONS.md §언어 규칙)"
        expected = [{"rule_key": KEY_LANG, "file": changed[0], "min_severity": "info", "max_severity": "medium"}]
    elif cid == "syn-j2-english-doc-section":
        doc = (repo / "opal/core/references/demo-guide.md").read_text(encoding="utf-8")
        write(repo, "opal/core/references/demo-guide.md", doc + ENGLISH_SECTION)
        changed = ["opal/core/references/demo-guide.md"]
        desc = "판단 규칙: 신규 문서 절을 영문 본문으로 작성(docs/CONVENTIONS.md §언어 규칙)"
        expected = [{"rule_key": KEY_LANG, "file": changed[0], "min_severity": "info", "max_severity": "medium"}]
    elif cid == "syn-ok-clean":
        py = (repo / "opal/tools/demo-tool/demo_tool.py").read_text(encoding="utf-8")
        py = py.replace('"exports": ["average"]', '"exports": ["average", "total"]').replace(
            "평균을 구하는 average 함수를 제공한다.", "평균을 구하는 average와 합계를 구하는 total 함수를 제공한다.")
        write(repo, "opal/tools/demo-tool/demo_tool.py", py + OK_FUNC)
        doc = (repo / "opal/core/references/demo-guide.md").read_text(encoding="utf-8")
        write(repo, "opal/core/references/demo-guide.md", doc + OK_SECTION)
        changed = ["opal/tools/demo-tool/demo_tool.py", "opal/core/references/demo-guide.md"]
        desc = "무결점 변경: 영문 식별자 함수 + 한국어 문서 절 + @header 갱신"
    else:
        raise ValueError(cid)
    git_commit(repo, "change")
    return {"id": opaque, "kind": "synthetic", "desc": "", "project_root": str(repo), "base_ref": base_sha,
            "target_files": changed, "expected": expected, "expect_clean": not expected,
            "max_allowed_severity": "low"}


def past_case(spec, repo_root, work_root, opaque):
    case_dir = work_root / "n" / opaque
    case_dir.mkdir(parents=True, exist_ok=True)
    wt = case_dir / "repo"
    if wt.exists():
        sh(["git", "worktree", "remove", "--force", str(wt)], cwd=repo_root, check=False)
    sh(["git", "worktree", "add", "--detach", str(wt), spec["commit"]], cwd=repo_root)
    base_ref = spec["base_ref"]
    names = sh(["git", "diff", "--name-only", "--diff-filter=ACMR", base_ref, spec["commit"]], cwd=wt).stdout.split("\n")
    changed = [n for n in names if n and not n.startswith("tasks/")]
    note = "target_files = 구간 변경 파일 중 tasks/ 아래 태스크 산출물 제외(EXECUTE 워커 changed_files에 해당)"
    if spec["history"]:
        # 과거 기록의 checked_files가 있으면 그 목록(당시 PM Gate가 확정한 target_files)을 그대로 쓴다.
        hist = json.loads((Path(repo_root) / spec["history"]).read_text(encoding="utf-8"))
        cf = [f for f in hist.get("checked_files", []) if isinstance(f, str)]
        if cf:
            changed = cf
            note = "target_files = 과거 gc-findings-convention 기록의 checked_files(%d건)" % len(cf)
    return {"id": opaque, "kind": "past", "desc": "", "project_root": str(wt),
            "base_ref": base_ref, "head_commit": spec["commit"], "target_files": changed,
            "expected": spec["expected"], "expect_clean": not spec["expected"], "max_allowed_severity": "medium",
            "note": note}


def cleanup(work_root, repo_root, out_dir):
    cases_file = Path(out_dir) / "cases2.json"
    if cases_file.is_file():
        for case in json.loads(cases_file.read_text(encoding="utf-8")).get("cases", []):
            if case["kind"] == "past":
                sh(["git", "worktree", "remove", "--force", case["project_root"]], cwd=repo_root, check=False)
    sh(["git", "worktree", "prune"], cwd=repo_root, check=False)
    if Path(work_root).exists():
        shutil.rmtree(work_root, ignore_errors=True)
    print(json.dumps({"ok": True, "cleaned": str(work_root)}, ensure_ascii=False))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mapping", required=True, help="사례 라벨<->불투명 ID 매핑 JSON(checker: {label: cNN})")
    ap.add_argument("--work-root", default=str(DEFAULT_WORK), help="임시 worktree·저장소 폴더")
    ap.add_argument("--out", default=str(HERE), help="cases2.json을 쓸 폴더")
    ap.add_argument("--repo-root", default=str(DEFAULT_REPO), help="OPAL 저장소 루트")
    ap.add_argument("--cleanup", action="store_true", help="임시 worktree와 work-root를 제거")
    args = ap.parse_args(argv)
    repo_root, work_root, out_dir = Path(args.repo_root).resolve(), Path(args.work_root).resolve(), Path(args.out).resolve()
    if args.cleanup:
        cleanup(work_root, repo_root, out_dir)
        return 0
    mp = json.loads(Path(args.mapping).read_text(encoding="utf-8"))["checker"]
    work_root.mkdir(parents=True, exist_ok=True)
    cases = []
    for spec in PAST:
        cases.append(past_case(spec, repo_root, work_root, mp[spec["id"]]))
    for cid in SYNTHETIC_IDS:
        cases.append(synthetic_case(cid, repo_root, work_root, mp[cid]))
    cases.sort(key=lambda c: c["id"])
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "cases2.json").write_text(json.dumps(
        {"work_root": str(work_root), "cases": cases}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "cases": [c["id"] for c in cases]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
