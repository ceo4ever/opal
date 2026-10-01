"""
@header {
  "module": "convention_precheck",
  "layer": "util",
  "domain": "opal-workspace",
  "description": "컨벤션 검사 전에 기계적으로 판정되는 규칙 4종과 변경 구간을 결정론으로 산출하는 CLI. scan은 기준 커밋(git merge-base <base-ref> HEAD)과 체크아웃된 HEAD의 변경 파일을 구하고, 변경 구간(git diff -U0 신규 쪽 구간을 앞뒤 context-lines줄 넓혀 병합, 추가 파일은 전체 줄)을 convention-review-input JSON으로, 기계 규칙 finding을 gc-findings-convention-precheck JSON으로 쓴다. 기계 규칙은 @header(코드 확장자 변경 파일에 한해 code-scan target·scan --json을 node 서브프로세스로 호출, 추가 파일이거나 기준 커밋에 헤더가 있었던 파일이 헤더 없음이면 1건, 추가 파일은 필수 5필드 누락마다 1건, 실패하면 status partial과 missing_capabilities로 남기고 그 규칙만 건너뛴다), SKILL.md·AGENT.md frontmatter 필수 키, 새 변경이력 절 제목, 추가 파일 네이밍이다. finding은 gc-finding-schema.md의 14필드, envelope은 8필드만 쓰고 fingerprint는 §4(±3줄 정규화)로 산출한다. merge는 모델 finding 중 변경 구간 밖이거나 기계 규칙 rule_id인 것을 제거하고 남은 것의 id를 사전 검사 finding 뒤에서 GC-NNN으로 다시 매겨 최종 JSON을 만들며 status와 missing_capabilities는 두 입력의 합집합으로 결합한다. 종료 코드는 정상 0, 사용·git 오류 1이며 finding 유무는 종료 코드에 영향이 없다. git CLI와 (@header 판정용) node가 필요하다.",
  "exports": ["cmd_scan", "cmd_merge", "compute_ranges", "parse_hunks", "make_finding", "compute_fingerprint", "merge_findings", "MECHANICAL_RULE_IDS"],
  "depends": ["git CLI", "node (선택, @header 판정)", "opal/tools/code-scan/code-scan.js (선택, @header 판정)"]
}
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

RULE_HEADER = "CONVENTIONS.md §구현 규칙 §@header 규칙"
RULE_FRONTMATTER = "CONVENTIONS.md §파일 구조 §YAML Frontmatter"
RULE_HISTORY = "opal-doc-standard.md §5"
RULE_NAMING = "CONVENTIONS.md §네이밍 규칙 §파일/폴더"
MECHANICAL_RULE_IDS = [RULE_HEADER, RULE_FRONTMATTER, RULE_HISTORY, RULE_NAMING]

REFERENCES = [
    "docs/CONVENTIONS.md",
    "opal/core/references/opal-doc-standard.md",
    "opal/core/references/harness/gc-finding-schema.md",
]

HEADER_FIELDS = ["module", "layer", "domain", "description", "exports"]
FRONTMATTER_KEYS = {"SKILL.md": ["name", "description"], "AGENT.md": ["name", "description", "model"]}
DEFAULT_CODE_EXTENSIONS = [".py", ".js", ".ts", ".jsx", ".tsx", ".vue", ".svelte", ".kt", ".kts", ".java", ".swift"]
DEFAULT_EXCLUDE_DIRS = ["node_modules", "__pycache__", ".git", "dist", "build", ".venv", "env", ".next",
                        ".nuxt", ".output", "fixtures", "backup", ".pytest_cache", "tasks", "specs",
                        ".opal-worktrees"]
HISTORY_RE = re.compile(r"^#{1,6}\s*(변경\s*이력|Changelog|History|Revisions)\b", re.IGNORECASE)
KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
PY_FILE_RE = re.compile(r"^[a-z0-9_]+\.py$")
OTHER_FILE_RE = re.compile(r"^[A-Za-z0-9._-]+$")
TASK_DIR_RE = re.compile(r"^\d{3}-\d{6}-[a-z0-9]+-\S+$")
NAMING_SKIP_DIRS = {"__pycache__", "tests", "fixtures", "references", "personas"}
HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
CODE_SCAN_TIMEOUT = 60


class ToolError(Exception):
    """사용·git 오류. 종료 코드 1로 이어진다."""


# ─────────────────────────────────────────────────────────────────────────────
# git 보조
# ─────────────────────────────────────────────────────────────────────────────
def run_git(root, args, check=True):
    proc = subprocess.run(["git", "-c", "core.quotepath=false", "-C", str(root)] + args,
                          capture_output=True)
    if check and proc.returncode != 0:
        msg = proc.stderr.decode("utf-8", "replace").strip()
        raise ToolError("git %s 실패: %s" % (" ".join(args[:2]), msg))
    return proc


def git_text(root, args):
    return run_git(root, args).stdout.decode("utf-8", "replace").strip()


def git_show(root, rev, path):
    proc = run_git(root, ["show", "%s:%s" % (rev, path)], check=False)
    if proc.returncode != 0:
        return None
    return proc.stdout.decode("utf-8", "replace")


def read_file(root, rel):
    p = pathlib.Path(root) / rel
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return git_show(root, "HEAD", rel)


def changed_files(root, base_sha):
    """[(status, path)] — status는 A|M|C 첫 글자, diff-filter ACMR."""
    out = run_git(root, ["diff", "--name-status", "-z", "--diff-filter=ACMR", base_sha, "HEAD"]).stdout
    tokens = out.decode("utf-8", "replace").split("\0")
    result = []
    i = 0
    while i < len(tokens) and tokens[i]:
        st = tokens[i]
        if st[0] == "C":
            result.append(("A", tokens[i + 2]))
            i += 3
        else:
            result.append((st[0], tokens[i + 1]))
            i += 2
    return result


def parse_hunks(diff_text):
    """git diff -U0 출력에서 신규 쪽 (시작, 개수)와 추가된 줄 [(줄번호, 텍스트)]를 뽑는다."""
    hunks = []
    added = []
    cur = None
    for line in diff_text.split("\n"):
        m = HUNK_RE.match(line)
        if m:
            start = int(m.group(1))
            count = 1 if m.group(2) is None else int(m.group(2))
            hunks.append((start, count))
            cur = start
            continue
        if cur is None:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            added.append((cur, line[1:]))
            cur += 1
    return hunks, added


def compute_ranges(hunks, total_lines, context):
    spans = []
    for start, count in hunks:
        if count <= 0:
            continue
        s = max(1, start - context)
        e = min(total_lines, start + count - 1 + context)
        if e >= s:
            spans.append([s, e])
    spans.sort()
    merged = []
    for s, e in spans:
        if merged and s <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return merged


# ─────────────────────────────────────────────────────────────────────────────
# finding 생성 (gc-finding-schema.md §1, §4)
# ─────────────────────────────────────────────────────────────────────────────
def normalize_snippet(text):
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    text = re.sub(r"(?m)(^|\s)#.*$|//.*$", " ", text)
    text = re.sub(r"\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'", "STR", text)
    text = re.sub(r"\b\d+(?:\.\d+)?\b", "NUM", text)
    text = re.sub(r"[A-Za-z_가-힣][\w가-힣]*", lambda m: m.group(0) if m.group(0) in ("STR", "NUM") else "ID", text)
    return re.sub(r"\s+", " ", text).strip()


def compute_fingerprint(category_id, content, line):
    snippet = ""
    if content:
        lines = content.split("\n")
        lo = max(0, line - 1 - 3)
        snippet = normalize_snippet("\n".join(lines[lo:line + 3]))
    return hashlib.sha1(("%s|%s" % (category_id, snippet)).encode("utf-8")).hexdigest()[:16]


def make_finding(rule_id, category, fp_key, severity, disposition, file, line, content,
                 evidence, impact, guidance, verification):
    return {
        "id": "",
        "fingerprint": compute_fingerprint(fp_key, content, line),
        "category": category,
        "severity": severity,
        "confidence": "high",
        "disposition": disposition,
        "rule_id": rule_id,
        "source_tier": "T0",
        "location": {"file": file, "line": line},
        "evidence": evidence,
        "impact": impact,
        "remediation": {"guidance": guidance, "reference": rule_id, "auto_fixable": False},
        "verification": verification,
        "suppression": None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# code-scan 호출 (@header 판정)
# ─────────────────────────────────────────────────────────────────────────────
class CodeScanClient:
    def __init__(self, root, code_scan):
        self.root = str(root)
        self.code_scan = code_scan
        self.node = shutil.which("node")
        cfg = pathlib.Path(root) / ".opal" / "code-scan.json"
        self.extra = [] if cfg.exists() else ["--header-source", "inline"]
        self.config = {}
        if cfg.exists():
            try:
                self.config = json.loads(cfg.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                self.config = {}
        self.failures = []

    def unavailable_reason(self):
        if not self.node:
            return "node 실행 파일을 PATH에서 찾을 수 없어 @header 규칙을 판정하지 못했다"
        if not os.path.isfile(self.code_scan):
            return "code-scan 스크립트가 없어 @header 규칙을 판정하지 못했다: %s" % self.code_scan
        return None

    def call(self, args):
        proc = subprocess.run([self.node, self.code_scan] + args + ["--json"] + self.extra,
                              capture_output=True, cwd=self.root, timeout=CODE_SCAN_TIMEOUT)
        text = proc.stdout.decode("utf-8", "replace").strip()
        try:
            data = json.loads(text) if text else {}
        except ValueError:
            raise ToolError("code-scan 출력이 JSON이 아니다")
        if proc.returncode != 0 or (isinstance(data, dict) and data.get("ok") is False):
            detail = data.get("error") if isinstance(data, dict) else None
            raise ToolError("code-scan %s 실패(exit %d): %s" % (args[0], proc.returncode, detail or text[:120]))
        return data

    def target_in_scope(self, rel):
        data = self.call(["target", rel])
        return data.get("write_to") != "none"

    def header_of(self, rel):
        data = self.call(["scan", rel])
        if isinstance(data, dict):
            for key, val in data.items():
                if isinstance(val, dict):
                    return val
        return None

    def base_header_of(self, root, base_sha, rel):
        """기준 커밋 버전 파일을 임시 프로젝트에 같은 상대경로로 두고 현재와 같은 scan 판정을 적용한다.
        기준 커밋에 파일이 없으면 None."""
        proc = run_git(root, ["show", "%s:%s" % (base_sha, rel)], check=False)
        if proc.returncode != 0:
            return None
        tmp = tempfile.mkdtemp(prefix="cp-base-")
        try:
            dest = pathlib.Path(tmp) / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(proc.stdout)
            cfg = pathlib.Path(self.root) / ".opal" / "code-scan.json"
            if cfg.exists():
                (pathlib.Path(tmp) / ".opal").mkdir()
                shutil.copy(str(cfg), str(pathlib.Path(tmp) / ".opal" / "code-scan.json"))
            return CodeScanClient(tmp, self.code_scan).header_of(rel)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def is_code_file(self, rel):
        exts = [e for e in self.config.get("extensions", DEFAULT_CODE_EXTENSIONS) if e != ".md"]
        excl = set(self.config.get("exclude", DEFAULT_EXCLUDE_DIRS))
        parts = rel.split("/")
        if any(p in excl for p in parts[:-1]):
            return False
        return any(rel.endswith(e) for e in exts)


# ─────────────────────────────────────────────────────────────────────────────
# 규칙
# ─────────────────────────────────────────────────────────────────────────────
def check_header(root, status, rel, base_sha, client, missing, evidence):
    if not client.is_code_file(rel):
        return []
    reason = client.unavailable_reason()
    if reason:
        if reason not in missing:
            missing.append(reason)
        return []
    content = read_file(root, rel)
    try:
        if status != "A":
            # 기준·현재에 같은 code-scan 판정을 적용한다. 기준에 인식 가능한 헤더가 없었으면
            # 기존 레거시이므로 이번 변경의 회귀가 아니다.
            if not client.base_header_of(root, base_sha, rel):
                return []
        if not client.target_in_scope(rel):
            return []
        header = client.header_of(rel)
    except (ToolError, subprocess.TimeoutExpired, OSError) as exc:
        msg = "code-scan 호출 실패로 @header 규칙을 판정하지 못했다: %s" % exc
        if msg not in missing:
            missing.append(msg)
        return []
    findings = []
    if not header:
        why = "추가된 파일에 @header 블록이 없다" if status == "A" else "기준 커밋에는 @header가 있었으나 지금 없다(회귀)"
        findings.append(make_finding(
            RULE_HEADER, "@header", "@header", "high", "blocking", rel, 1, content,
            "code-scan scan --json 결과가 비어 있다. %s" % why,
            "코드 지도(code-scan)에서 이 파일이 누락되어 모듈 탐색·헤더 커버리지가 깨진다",
            "파일 상단에 module·layer·domain·description·exports를 갖춘 @header 블록을 작성한다",
            "code-scan scan %s --json 이 헤더를 반환한다" % rel))
        return findings
    if status != "A":
        return findings
    for field in HEADER_FIELDS:
        val = header.get(field)
        if val is None or val == "" or val == []:
            findings.append(make_finding(
                RULE_HEADER, "@header:%s" % field, "@header:%s" % field, "high", "blocking", rel, 1, content,
                "@header 블록에 `%s` 필드가 없다" % field,
                "필수 필드가 비어 코드 지도 검색·검증이 불완전해진다",
                "@header 블록에 `%s` 필드를 채운다" % field,
                "code-scan scan %s --json 결과에 `%s`가 있다" % (rel, field)))
    return findings


def parse_frontmatter_keys(text):
    if not text:
        return set()
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return set()
    keys = set()
    for ln in lines[1:]:
        if ln.strip() == "---":
            return keys
        m = re.match(r"^([A-Za-z0-9_-]+)\s*:", ln)
        if m:
            keys.add(m.group(1))
    return keys


def check_frontmatter(root, rel):
    base_name = rel.rsplit("/", 1)[-1]
    required = FRONTMATTER_KEYS.get(base_name)
    if not required:
        return []
    content = read_file(root, rel)
    keys = parse_frontmatter_keys(content)
    out = []
    for key in required:
        if key not in keys:
            out.append(make_finding(
                RULE_FRONTMATTER, "frontmatter:%s" % key, "frontmatter:%s" % key, "high", "blocking", rel, 1,
                content, "%s 첫 frontmatter에 `%s` 키가 없다" % (base_name, key),
                "에이전트·스킬 로더가 정의를 식별하지 못할 수 있다",
                "첫 YAML frontmatter에 `%s` 키를 추가한다" % key,
                "파일 첫 frontmatter에 `%s:`가 있다" % key))
    return out


def check_history(root, rel, added_lines):
    if not rel.endswith(".md"):
        return []
    content = read_file(root, rel)
    out = []
    for lineno, text in added_lines:
        if HISTORY_RE.match(text):
            out.append(make_finding(
                RULE_HISTORY, "doc-history", "doc-history", "medium", "advisory", rel, lineno, content,
                "기준 커밋 대비 추가된 제목줄: %s" % text.strip(),
                "변경 이력은 git이 갖는데 문서에 이력 절이 누적된다",
                "이력 절을 제거하고 git 로그·DONE.md로 위임한다",
                "해당 제목줄이 문서에 없다"))
    return out


def check_naming(root, rel, base_dirs, reported_tasks):
    parts = rel.split("/")
    out = []
    if parts[0] == "tasks" and len(parts) > 2:
        folder = parts[1]
        if ("tasks/" + folder) not in base_dirs and folder not in reported_tasks:
            reported_tasks.add(folder)
            if not TASK_DIR_RE.match(folder):
                out.append(make_finding(
                    RULE_NAMING, "naming", "naming:tasks/%s" % folder, "medium", "advisory", rel, 1, None,
                    "새 태스크 폴더명 `%s`가 `{NNN}-{YYMMDD}-{스킬약어}-{태스크명}`(공백 금지) 형식이 아니다" % folder,
                    "태스크 번호·날짜 파싱과 셸 호출이 불안정해진다",
                    "폴더명을 `NNN-YYMMDD-스킬약어-태스크명` 형식으로 바꾼다",
                    "폴더명이 `^\\d{3}-\\d{6}-[a-z0-9]+-\\S+$`에 맞는다"))
        return out
    if parts[0] != "opal":
        return out
    if any(p in ("__pycache__", "fixtures") for p in parts[:-1]):
        return out
    dirs = parts[:-1]
    for idx, d in enumerate(dirs):
        prefix = "/".join(parts[:idx + 1])
        if prefix in base_dirs or d in NAMING_SKIP_DIRS or d.startswith("."):
            continue
        if not KEBAB_RE.match(d):
            out.append(make_finding(
                RULE_NAMING, "naming", "naming:%s" % prefix, "medium", "advisory", rel, 1, None,
                "새 디렉터리 `%s`가 kebab-case(`^[a-z0-9]+(-[a-z0-9]+)*$`)가 아니다" % d,
                "폴더 이름 규칙이 어긋나 탐색·자동화 규칙이 흔들린다",
                "디렉터리명을 kebab-case로 바꾼다",
                "디렉터리명이 kebab-case 정규식에 맞는다"))
    fname = parts[-1]
    if fname.endswith(".md"):
        return out
    ok = PY_FILE_RE.match(fname) if fname.endswith(".py") else (OTHER_FILE_RE.match(fname) and " " not in fname)
    if not ok:
        want = "snake_case `.py`" if fname.endswith(".py") else "영문·숫자·`._-`만 쓰고 공백 없는 이름"
        out.append(make_finding(
            RULE_NAMING, "naming", "naming:%s" % rel, "medium", "advisory", rel, 1, None,
            "새 파일명 `%s`가 규칙(%s)에 맞지 않는다" % (fname, want),
            "파일 이름 규칙이 어긋나 탐색·자동화 규칙이 흔들린다",
            "파일명을 규칙에 맞게 바꾼다",
            "파일명이 규칙 정규식에 맞는다"))
    return out


# ─────────────────────────────────────────────────────────────────────────────
# scan
# ─────────────────────────────────────────────────────────────────────────────
def norm_rel(root, p):
    p = p.strip()
    if os.path.isabs(p):
        try:
            p = os.path.relpath(p, str(root))
        except ValueError:
            pass
    return p[2:] if p.startswith("./") else p


def cmd_scan(args):
    root = pathlib.Path(args.project_root).resolve()
    if not root.is_dir():
        raise ToolError("project-root가 디렉터리가 아니다: %s" % root)
    out_dir = pathlib.Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    base_sha = git_text(root, ["merge-base", args.base_ref, "HEAD"])
    head_sha = git_text(root, ["rev-parse", "HEAD"])
    changed = changed_files(root, base_sha)
    targets = None
    if args.target_files:
        targets = [norm_rel(root, t) for t in args.target_files.split(",") if t.strip()]
        tset = set(targets)
        changed = [(s, p) for s, p in changed if p in tset]
    checked = targets if targets is not None else [p for _, p in changed]
    base_dirs = set()
    tree = run_git(root, ["ls-tree", "-r", "--name-only", "-z", base_sha]).stdout.decode("utf-8", "replace")
    for f in tree.split("\0"):
        segs = f.split("/")
        for i in range(1, len(segs)):
            base_dirs.add("/".join(segs[:i]))

    client = CodeScanClient(root, os.path.abspath(args.code_scan) if args.code_scan else
                            str(pathlib.Path(__file__).resolve().parent.parent / "code-scan" / "code-scan.js"))
    missing, evidence = [], []
    findings, review_files = [], []
    reported_tasks = set()
    for status, rel in changed:
        content = read_file(root, rel)
        total = len(content.splitlines()) if content else 0
        diff = run_git(root, ["diff", "-U0", "--no-color", base_sha, "HEAD", "--", rel]).stdout.decode("utf-8", "replace")
        hunks, added_lines = parse_hunks(diff)
        if status == "A":
            review_files.append({"path": rel, "status": "added", "whole_file": True,
                                 "ranges": [[1, total]] if total > 0 else []})
        else:
            review_files.append({"path": rel, "status": "modified", "whole_file": False,
                                 "ranges": compute_ranges(hunks, total, args.context_lines)})
        findings += check_header(root, status, rel, base_sha, client, missing, evidence)
        findings += check_frontmatter(root, rel)
        findings += check_history(root, rel, added_lines)
        if status == "A":
            findings += check_naming(root, rel, base_dirs, reported_tasks)
    for i, f in enumerate(findings, 1):
        f["id"] = "GC-%03d" % i
    evidence = [
        "git merge-base %s HEAD -> %s" % (args.base_ref, base_sha),
        "git diff --name-status --diff-filter=ACMR %s HEAD -> %d files" % (base_sha[:12], len(changed)),
        "git diff -U0 per changed file (context-lines=%d)" % args.context_lines,
        "mechanical rules: %d" % len(MECHANICAL_RULE_IDS),
    ] + evidence
    envelope = {
        "check": "convention",
        "status": "partial" if missing else "pass",
        "checked_files": checked,
        "findings": findings,
        "evidence": evidence,
        "references": REFERENCES,
        "missing_capabilities": missing,
        "report_path": None,
    }
    review = {"base_sha": base_sha, "head_sha": head_sha,
              "mechanical_rule_ids": MECHANICAL_RULE_IDS, "files": review_files}
    ts = args.timestamp
    findings_path = out_dir / ("gc-findings-convention-precheck-%s.json" % ts)
    review_path = out_dir / ("convention-review-input-%s.json" % ts)
    write_json(findings_path, envelope)
    write_json(review_path, review)
    print(json.dumps({"ok": True, "status": envelope["status"], "base_sha": base_sha, "head_sha": head_sha,
                      "findings": len(findings), "changed_files": len(review_files),
                      "missing_capabilities": missing,
                      "findings_path": str(findings_path), "review_input_path": str(review_path)},
                     ensure_ascii=False))
    return 0


def write_json(path, data):
    pathlib.Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# merge
# ─────────────────────────────────────────────────────────────────────────────
def load_json(path):
    try:
        return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ToolError("JSON을 읽지 못했다: %s (%s)" % (path, exc))


def in_ranges(review, file, line):
    if not isinstance(line, int):
        return False
    for f in review.get("files", []):
        if f.get("path") == file:
            return any(s <= line <= e for s, e in f.get("ranges", []))
    return False


def merge_findings(pre, review, model):
    """(최종 envelope, out_of_range 수, mechanical 수)."""
    mech = set(review.get("mechanical_rule_ids", []))
    model_findings, model_env = [], {}
    if isinstance(model, list):
        model_findings = model
    elif isinstance(model, dict):
        model_env = model
        model_findings = model.get("findings", []) or []
    kept, oor, mrule = [], 0, 0
    for f in model_findings:
        if f.get("rule_id") in mech:
            mrule += 1
            continue
        loc = f.get("location") or {}
        if not in_ranges(review, loc.get("file"), loc.get("line")):
            oor += 1
            continue
        kept.append(dict(f))
    final = list(pre.get("findings", []))
    for f in kept:
        final.append(f)
    for i, f in enumerate(final, 1):
        f["id"] = "GC-%03d" % i

    def union(a, b):
        res = list(a or [])
        for x in (b or []):
            if x not in res:
                res.append(x)
        return res

    missing = union(pre.get("missing_capabilities"), model_env.get("missing_capabilities"))
    statuses = [pre.get("status"), model_env.get("status")]
    if "error" in statuses:
        status = "error"
    elif "partial" in statuses or missing:
        status = "partial"
    else:
        status = "pass"
    evidence = union(pre.get("evidence"), model_env.get("evidence"))
    return {
        "check": "convention",
        "status": status,
        "checked_files": union(pre.get("checked_files"), model_env.get("checked_files")),
        "findings": final,
        "evidence": evidence,
        "references": union(pre.get("references"), model_env.get("references")),
        "missing_capabilities": missing,
        "report_path": pre.get("report_path"),
    }, oor, mrule


def cmd_merge(args):
    pre = load_json(args.precheck)
    review = load_json(args.review_input)
    model = None if args.model_findings == "none" else load_json(args.model_findings)
    env, oor, mrule = merge_findings(pre, review, model)
    if model is not None:
        env["evidence"].append("model findings dropped: out_of_range=%d, mechanical_rule=%d" % (oor, mrule))
    write_json(args.output, env)
    print(json.dumps({"ok": True, "status": env["status"], "findings": len(env["findings"]),
                      "dropped": {"out_of_range": oor, "mechanical_rule": mrule},
                      "output": str(args.output)}, ensure_ascii=False))
    return 0


# ─────────────────────────────────────────────────────────────────────────────
def build_parser():
    p = argparse.ArgumentParser(prog="convention-precheck")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan")
    s.add_argument("--project-root", required=True)
    s.add_argument("--base-ref", required=True)
    s.add_argument("--output-dir", required=True)
    s.add_argument("--timestamp", required=True)
    s.add_argument("--target-files", default=None)
    s.add_argument("--context-lines", type=int, default=10)
    s.add_argument("--code-scan", default=None, help="code-scan.js 경로(기본: 형제 도구)")
    s.set_defaults(func=cmd_scan)
    m = sub.add_parser("merge")
    m.add_argument("--precheck", required=True)
    m.add_argument("--review-input", required=True)
    m.add_argument("--model-findings", required=True)
    m.add_argument("--output", required=True)
    m.set_defaults(func=cmd_merge)
    return p


def main(argv=None):
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:
        return 1 if exc.code not in (0, None) else 0
    try:
        return args.func(args)
    except ToolError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
