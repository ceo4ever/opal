"""
@header {
  "module": "test_convention_precheck",
  "layer": "test",
  "domain": "opal-workspace",
  "description": "convention-precheck(scan·merge)의 결정론 시험. 시험 안에서 임시 git 저장소를 만들어 변경 구간 산출(S-6), merge 결합(S-7), 기계 규칙 4종 사례 a~j(S-8), 162 회귀 재현(S-9, 커밋 48f25a5a 체크아웃), node·code-scan 부재 시 partial 처리(S-10)를 확인한다. 저장소 실제 파일은 수정하지 않으며 에이전트·네트워크를 쓰지 않는다. 162 회귀는 이 저장소 이력에 해당 커밋이 없으면 건너뛴다.",
  "exports": ["TestReviewRanges", "TestMerge", "TestMechanicalRules", "TestMissingCapability"],
  "depends": ["git CLI", "node", "opal/tools/convention-precheck/convention_precheck.py", "opal/tools/code-scan/code-scan.js"],
  "scenarios": ["S-6", "S-7", "S-8", "S-9", "S-10"]
}
"""

from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
TOOL = HERE.parent / "convention_precheck.py"
REPO_ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))
import convention_precheck as cp  # noqa: E402

GIT_CFG = ["-c", "user.email=t@example.com", "-c", "user.name=t", "-c", "commit.gpgsign=false",
           "-c", "init.defaultBranch=main"]
FULL_HEADER = ('"""\n@header {\n  "module": "m", "layer": "util", "domain": "d",\n'
               '  "description": "x", "exports": ["f"]\n}\n"""\n')
FINDING_KEYS = {"id", "fingerprint", "category", "severity", "confidence", "disposition", "rule_id",
                "source_tier", "location", "evidence", "impact", "remediation", "verification", "suppression"}
ENVELOPE_KEYS = {"check", "status", "checked_files", "findings", "evidence", "references",
                 "missing_capabilities", "report_path"}


def git(root, *args):
    return subprocess.run(["git"] + GIT_CFG + ["-C", str(root)] + list(args), check=True,
                          capture_output=True, text=True).stdout.strip()


def write(root, rel, text):
    p = pathlib.Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def commit(root, msg):
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", msg)


def run_scan(root, out, base_ref="main", ts="t", extra=None, env=None, python=None):
    cmd = [python or sys.executable, str(TOOL), "scan", "--project-root", str(root), "--base-ref", base_ref,
           "--output-dir", str(out), "--timestamp", ts] + (extra or [])
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return proc


def load(out, ts="t"):
    findings = json.loads((pathlib.Path(out) / ("gc-findings-convention-precheck-%s.json" % ts)).read_text())
    review = json.loads((pathlib.Path(out) / ("convention-review-input-%s.json" % ts)).read_text())
    return findings, review


class TmpRepoCase(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="cp-test-")).resolve()
        self.root = self.tmp / "repo"
        self.root.mkdir()
        self.out = self.tmp / "out"
        git(self.root, "init", "-q")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def branch_case(self, base_files, change_files):
        """main에 base_files 커밋 → work 브랜치에서 change_files 반영(커밋)."""
        for rel, text in base_files.items():
            write(self.root, rel, text)
        write(self.root, "seed.txt", "seed\n")
        commit(self.root, "base")
        git(self.root, "checkout", "-q", "-b", "work")
        for rel, text in change_files.items():
            write(self.root, rel, text)
        commit(self.root, "change")

    def scan(self, **kw):
        proc = run_scan(self.root, self.out, **kw)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return load(self.out)


class TestReviewRanges(TmpRepoCase):
    def test_review_ranges_merge_base_and_context(self):
        a_lines = [("line%d\n" % i) for i in range(1, 31)]
        write(self.root, "src/a.py", "".join(a_lines))
        write(self.root, "src/b.py", "b\n")
        commit(self.root, "base")
        git(self.root, "checkout", "-q", "-b", "work")
        a_new = list(a_lines)
        a_new[11], a_new[12] = "changed12\n", "changed13\n"
        write(self.root, "src/a.py", "".join(a_new))
        write(self.root, "src/c.py", FULL_HEADER + "x = 1\n")
        commit(self.root, "work")
        git(self.root, "checkout", "-q", "main")
        write(self.root, "src/other.py", "o\n")
        commit(self.root, "main advanced")
        git(self.root, "checkout", "-q", "work")
        fnd, rev = self.scan(extra=["--target-files", "src/a.py,src/b.py,src/c.py"])
        self.assertEqual(rev["base_sha"], git(self.root, "merge-base", "main", "HEAD"))
        self.assertEqual(rev["head_sha"], git(self.root, "rev-parse", "HEAD"))
        files = {f["path"]: f for f in rev["files"]}
        self.assertEqual(files["src/a.py"]["status"], "modified")
        self.assertFalse(files["src/a.py"]["whole_file"])
        self.assertEqual(files["src/a.py"]["ranges"], [[2, 23]])
        self.assertEqual(files["src/c.py"]["status"], "added")
        self.assertTrue(files["src/c.py"]["whole_file"])
        n = len((self.root / "src/c.py").read_text().splitlines())
        self.assertEqual(files["src/c.py"]["ranges"], [[1, n]])
        self.assertNotIn("src/b.py", files)
        self.assertNotIn("src/other.py", files)
        self.assertEqual(fnd["checked_files"], ["src/a.py", "src/b.py", "src/c.py"])
        self.assertEqual([f for f in fnd["findings"] if f["location"]["file"] == "src/a.py"], [])
        self.assertEqual(set(fnd.keys()), ENVELOPE_KEYS)
        self.assertIsNone(fnd["report_path"])

    def test_review_ranges_merges_overlaps(self):
        self.assertEqual(cp.compute_ranges([(12, 2), (25, 1)], 40, 10), [[2, 35]])
        self.assertEqual(cp.compute_ranges([(1, 1), (50, 1)], 60, 10), [[1, 11], [40, 60]])
        self.assertEqual(cp.compute_ranges([(5, 0)], 60, 10), [])


class TestMerge(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="cp-merge-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def _finding(self, fid, rule, file, line):
        return cp.make_finding(rule, "cat", "cat", "high", "blocking", file, line, "x = 1\n",
                               "ev", "imp", "guide", "ver") | {"id": fid}

    def _inputs(self, status="pass", missing=None):
        pre = {"check": "convention", "status": status, "checked_files": ["a.py"],
               "findings": [self._finding("GC-001", cp.RULE_HEADER, "a.py", 1),
                            self._finding("GC-002", cp.RULE_NAMING, "a.py", 1)],
               "evidence": ["pre"], "references": ["docs/CONVENTIONS.md"],
               "missing_capabilities": missing or [], "report_path": None}
        review = {"base_sha": "b", "head_sha": "h", "mechanical_rule_ids": cp.MECHANICAL_RULE_IDS,
                  "files": [{"path": "a.py", "status": "modified", "whole_file": False, "ranges": [[10, 20]]}]}
        return pre, review

    def _run(self, pre, review, model):
        for name, data in (("pre", pre), ("rev", review)):
            (self.tmp / (name + ".json")).write_text(json.dumps(data))
        mpath = "none"
        if model is not None:
            (self.tmp / "model.json").write_text(json.dumps(model))
            mpath = str(self.tmp / "model.json")
        out = self.tmp / "final.json"
        proc = subprocess.run([sys.executable, str(TOOL), "merge", "--precheck", str(self.tmp / "pre.json"),
                               "--review-input", str(self.tmp / "rev.json"), "--model-findings", mpath,
                               "--output", str(out)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(out.read_text())

    def test_merge_drops_out_of_range_and_mechanical(self):
        pre, review = self._inputs()
        model = {"findings": [self._finding("GC-001", "CONVENTIONS.md §언어 규칙", "a.py", 15),
                              self._finding("GC-002", "CONVENTIONS.md §언어 규칙", "a.py", 40),
                              self._finding("GC-003", cp.RULE_HISTORY, "a.py", 12)]}
        final = self._run(pre, review, model)
        self.assertEqual([f["id"] for f in final["findings"]], ["GC-001", "GC-002", "GC-003"])
        self.assertEqual(final["findings"][2]["location"]["line"], 15)
        self.assertEqual(len(final["findings"]), 3)
        self.assertIn("model findings dropped: out_of_range=1, mechanical_rule=1", final["evidence"])
        self.assertEqual(set(final.keys()), ENVELOPE_KEYS)
        self.assertEqual(final["status"], "pass")
        for f in final["findings"]:
            self.assertEqual(set(f.keys()), FINDING_KEYS)
            self.assertIn(f["severity"], ["critical", "high", "medium", "low", "info"])
            self.assertIn(f["confidence"], ["high", "medium", "low"])
            self.assertIn(f["disposition"], ["blocking", "advisory", "informational"])
            self.assertIn(f["source_tier"], ["T0", "T1", "T2", "T3"])

    def test_merge_partial_precheck_and_none_model(self):
        pre, review = self._inputs(status="partial", missing=["node 없음"])
        final = self._run(pre, review, None)
        self.assertEqual(final["status"], "partial")
        self.assertEqual(final["missing_capabilities"], ["node 없음"])
        self.assertEqual(len(final["findings"]), 2)

    def test_merge_model_partial_unions(self):
        pre, review = self._inputs()
        model = {"status": "partial", "missing_capabilities": ["기준 문서 결측"], "findings": []}
        final = self._run(pre, review, model)
        self.assertEqual(final["status"], "partial")
        self.assertEqual(final["missing_capabilities"], ["기준 문서 결측"])


class TestMechanicalRules(TmpRepoCase):
    def rules(self, findings):
        return sorted((f["rule_id"], f["severity"], f["disposition"], f["location"]["file"])
                      for f in findings["findings"])

    def test_mechanical_rules_header(self):
        self.branch_case({"opal/x/keep.py": FULL_HEADER, "opal/x/gone.py": FULL_HEADER},
                         {"opal/x/new_nohead.py": "x = 1\n",
                          "opal/x/new_noexports.py": '"""\n@header {\n "module":"m","layer":"util","domain":"d","description":"x"\n}\n"""\n',
                          "opal/x/gone.py": "x = 1\n",
                          "opal/x/new_ok.py": FULL_HEADER})
        fnd, _ = self.scan()
        got = {(f["location"]["file"], f["category"]) for f in fnd["findings"]}
        self.assertEqual(got, {("opal/x/new_nohead.py", "@header"), ("opal/x/new_noexports.py", "@header:exports"),
                               ("opal/x/gone.py", "@header")})
        for f in fnd["findings"]:
            self.assertEqual((f["rule_id"], f["severity"], f["disposition"], f["source_tier"]),
                             (cp.RULE_HEADER, "high", "blocking", "T0"))
        self.assertEqual(fnd["status"], "pass")

    def test_mechanical_rules_header_line_comment_legacy_no_finding(self):
        legacy = "# @header\n# module: m\n# layer: util\nx = 1\n"
        self.branch_case({"opal/x/legacy.py": legacy}, {"opal/x/legacy.py": legacy + "y = 2\n"})
        fnd, _ = self.scan()
        self.assertEqual([f for f in fnd["findings"] if f["rule_id"] == cp.RULE_HEADER], [])
        self.assertEqual(fnd["missing_capabilities"], [])

    def test_mechanical_rules_header_regression_kept(self):
        self.branch_case({"opal/x/gone.py": FULL_HEADER}, {"opal/x/gone.py": "x = 1\n"})
        fnd, _ = self.scan()
        hdr = [f for f in fnd["findings"] if f["rule_id"] == cp.RULE_HEADER]
        self.assertEqual(len(hdr), 1)
        self.assertEqual((hdr[0]["severity"], hdr[0]["disposition"], hdr[0]["location"]["file"]),
                         ("high", "blocking", "opal/x/gone.py"))

    def test_mechanical_rules_frontmatter(self):
        self.branch_case({}, {"opal/skills/s1/SKILL.md": "---\nname: s1\n---\nbody\n",
                              "opal/agents/a1/AGENT.md": "---\nname: a1\ndescription: d\n---\nbody\n",
                              "opal/skills/s2/SKILL.md": "---\nname: s2\ndescription: d\n---\n"})
        fnd, _ = self.scan()
        got = sorted((f["location"]["file"], f["category"]) for f in fnd["findings"] if f["rule_id"] == cp.RULE_FRONTMATTER)
        self.assertEqual(got, [("opal/agents/a1/AGENT.md", "frontmatter:model"),
                               ("opal/skills/s1/SKILL.md", "frontmatter:description")])
        for f in fnd["findings"]:
            self.assertEqual((f["severity"], f["disposition"], f["source_tier"]), ("high", "blocking", "T0"))

    def test_mechanical_rules_changelog_heading(self):
        self.branch_case({"docs/old.md": "# T\n\n## 변경이력\n- a\n\nbody\n"},
                         {"docs/new.md": "# T\n\n## Changelog\n- a\n",
                          "docs/old.md": "# T\n\n## 변경이력\n- a\n\nbody changed\n"})
        fnd, _ = self.scan()
        hist = [f for f in fnd["findings"] if f["rule_id"] == cp.RULE_HISTORY]
        self.assertEqual([(f["location"]["file"], f["location"]["line"]) for f in hist], [("docs/new.md", 3)])
        self.assertEqual((hist[0]["severity"], hist[0]["disposition"]), ("medium", "advisory"))

    def test_mechanical_rules_naming(self):
        self.branch_case({}, {"opal/tools/BadDir/camelCaseFile.py": FULL_HEADER,
                              "opal/tools/ok-dir/good_file.py": FULL_HEADER,
                              "tasks/172-261001-opd-공백 있는 폴더/PLAN.md": "x\n",
                              "tasks/173-261001-opd-정상폴더/PLAN.md": "x\n"})
        fnd, _ = self.scan()
        nam = [f for f in fnd["findings"] if f["rule_id"] == cp.RULE_NAMING]
        files = sorted(f["location"]["file"] for f in nam)
        self.assertEqual(files, ["opal/tools/BadDir/camelCaseFile.py", "opal/tools/BadDir/camelCaseFile.py",
                                 "tasks/172-261001-opd-공백 있는 폴더/PLAN.md"])
        for f in nam:
            self.assertEqual((f["severity"], f["disposition"], f["source_tier"]), ("medium", "advisory", "T0"))

    def test_mechanical_rules_clean_and_stable_fingerprint(self):
        self.branch_case({}, {"opal/tools/ok-dir/good_file.py": FULL_HEADER,
                              "opal/skills/s3/SKILL.md": "---\nname: s3\ndescription: d\n---\n"})
        fnd, _ = self.scan()
        self.assertEqual(fnd["findings"], [])
        # 같은 입력의 fingerprint는 재실행해도 같다
        write(self.root, "opal/tools/ok-dir/bad.py", "y = 2\n")
        commit(self.root, "bad")
        first, _ = self.scan()
        second, _ = self.scan()
        fp1 = [f["fingerprint"] for f in first["findings"]]
        self.assertTrue(fp1 and all(len(x) == 16 for x in fp1))
        self.assertEqual(fp1, [f["fingerprint"] for f in second["findings"]])

    def test_mechanical_rules_reproduces_162(self):
        sha = "48f25a5a"
        if subprocess.run(["git", "-C", str(REPO_ROOT), "cat-file", "-e", sha + "^{commit}"],
                          capture_output=True).returncode != 0:
            self.skipTest("이 저장소 이력에 %s가 없다" % sha)
        wt = self.tmp / "wt162"
        subprocess.run(["git", "-C", str(REPO_ROOT), "worktree", "add", "-q", "--detach", str(wt), sha], check=True,
                       capture_output=True)
        try:
            proc = run_scan(wt, self.out, base_ref=sha + "^")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            fnd, _ = load(self.out)
            self.assertEqual(fnd["missing_capabilities"], [])
            hdr = [f for f in fnd["findings"] if f["rule_id"] == cp.RULE_HEADER]
            self.assertEqual(sorted(f["location"]["file"] for f in hdr),
                             ["opal/tools/event-loader/tests/test_event_loader_test_event.py",
                              "opal/tools/state-tool/tests/test_state_tool_test_cycle.py"])
            self.assertEqual(len(hdr), 2)
            for f in hdr:
                self.assertEqual((f["severity"], f["disposition"]), ("high", "blocking"))
        finally:
            subprocess.run(["git", "-C", str(REPO_ROOT), "worktree", "remove", "--force", str(wt)],
                           capture_output=True)


class TestMissingCapability(TmpRepoCase):
    def _case(self):
        self.branch_case({}, {"opal/x/new_nohead.py": "x = 1\n",
                              "opal/skills/s1/SKILL.md": "---\nname: s1\n---\nbody\n"})

    def _check(self, fnd, needle):
        self.assertEqual(fnd["status"], "partial")
        self.assertTrue(fnd["missing_capabilities"])
        self.assertTrue(any(needle in m for m in fnd["missing_capabilities"]), fnd["missing_capabilities"])
        self.assertEqual([f for f in fnd["findings"] if f["rule_id"] == cp.RULE_HEADER], [])
        fm = [f for f in fnd["findings"] if f["rule_id"] == cp.RULE_FRONTMATTER]
        self.assertEqual([f["category"] for f in fm], ["frontmatter:description"])

    def test_missing_capability_node_absent(self):
        self._case()
        bin_dir = self.tmp / "bin"
        bin_dir.mkdir()
        os.symlink(shutil.which("git"), bin_dir / "git")
        env = dict(os.environ, PATH=str(bin_dir))
        proc = run_scan(self.root, self.out, env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        fnd, _ = load(self.out)
        self._check(fnd, "node")

    def test_missing_capability_code_scan_path_absent(self):
        self._case()
        proc = run_scan(self.root, self.out, extra=["--code-scan", str(self.tmp / "nope" / "code-scan.js")])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        fnd, _ = load(self.out)
        self._check(fnd, "code-scan")


if __name__ == "__main__":
    unittest.main()
