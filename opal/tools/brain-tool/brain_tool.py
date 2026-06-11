"""
@header {
  "module": "brain_tool",
  "layer": "util",
  "domain": "opal-brain",
  "description": "OPAL Project Brain 지식 위키 결정론적 집행 CLI — 8개 서브 명령(init/add-page/index/log/search/sync-header/lint/validate). index/log/링크 무결성을 brain-tool이 집행(LLM 직접 편집 금지). frontmatter 파싱은 PyYAML, KST 타임스탬프는 date.js subprocess. sync-header는 code-scan @header → brain entity frontmatter 단방향 동기화만 수행.",
  "exports": [
    "cmd_init", "cmd_add_page", "cmd_index", "cmd_log",
    "cmd_search", "cmd_sync_header", "cmd_lint", "cmd_validate"
  ]
}
"""

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys

import yaml

# ─────────────────────────────────────────────────────────────────────────────
# 상수
# ─────────────────────────────────────────────────────────────────────────────

# 페이지 타입 enum (llm-wiki 원전 용어)
PAGE_TYPES = ["entity", "concept", "flow", "synthesis"]

# index.md 카테고리 헤더 ↔ 페이지 타입 매핑 (한국어 본문 ↔ English type)
TYPE_TO_CATEGORY = {
    "entity":    "엔티티",
    "concept":   "개념",
    "flow":      "흐름",
    "synthesis": "합성",
}
CATEGORY_ORDER = ["도메인", "개념", "엔티티", "흐름", "합성"]

# frontmatter 필수/선택 키 (PLAN 결정7)
REQUIRED_FRONTMATTER = ["type", "title", "created", "updated", "status"]
OPTIONAL_FRONTMATTER = ["tags", "sources", "related"]
ENTITY_EXTRA_KEYS = ["module", "layer", "domain", "exports", "source_ref", "header_synced"]
STATUS_ENUM = ["active", "stale", "draft"]

# log op enum (PLAN 결정3)
LOG_OPS = ["ingest", "init", "lint", "query"]

# init 핵심 엔티티 선별 임계값 (PLAN 결정4) — 프로젝트별 조정 가능
SEED_THRESHOLDS = {
    "exports_min":     3,                                  # exports 수 임계
    "dependents_min":  2,                                  # 피의존도 임계 (역참조)
    "seed_layers":     {"orchestrator", "tool", "pilot", "core"},  # 무조건 시드 레이어
}

# brain 골격 디렉토리
BRAIN_DIRS = [
    "pages/entity", "pages/concept", "pages/flow", "pages/synthesis",
    "sources",
]

# 템플릿 디렉토리 (스크립트와 동일 위치)
TEMPLATES_DIR = pathlib.Path(__file__).resolve().parent / "templates"

# ERROR_CODES 카탈로그 SSOT — 모든 error 응답 값은 이 상수의 키를 참조한다. 임의 변형 금지.
ERROR_CODES = {
    "brain_already_initialized":  "brain이 이미 초기화됨: {brain_path}. --force로만 재초기화 가능",
    "brain_path_invalid":         "brain-path가 유효하지 않음: {brain_path}",
    "brain_not_initialized":      "brain이 초기화되지 않음 (.opal/brain/SCHEMA.md 부재): {brain_path}",
    "invalid_page_type":          "유효하지 않은 페이지 타입: {page_type} (허용: entity|concept|flow|synthesis)",
    "frontmatter_invalid":        "frontmatter 표준 위반: {detail}",
    "duplicate_page":             "동일 경로의 페이지가 이미 존재: {page}",
    "index_write_failed":         "index.md 쓰기 실패: {detail}",
    "date_tool_failed":           "node ~/.opal/tools/date/date.js datetime 호출 실패",
    "log_append_failed":          "log.md append 실패: {detail}",
    "query_empty":                "검색어가 비어 있음",
    "code_scan_json_missing":     "code-scan.json 부재 — sync-header에 @header 시드 데이터원이 없음: {path}",
    "header_parse_failed":        "code-scan @header 파싱 실패: {detail}",
    "invalid_log_op":             "유효하지 않은 log op: {op} (허용: ingest|init|lint|query)",
    "template_missing":           "템플릿 파일 부재: {path}",
}

# ─────────────────────────────────────────────────────────────────────────────
# 응답 헬퍼 (state_tool.py 패턴 차용)
# ─────────────────────────────────────────────────────────────────────────────

def ok(command, **kwargs):
    """성공 응답 — 단일 라인 JSON, exit 0"""
    print(json.dumps({"ok": True, "command": command, **kwargs}, ensure_ascii=False, default=str))


def err(command, code, message=None, exit_code=1, **kwargs):
    """에러 응답 — 단일 라인 JSON, exit {exit_code}.
    code는 ERROR_CODES 키 중 하나여야 한다.
    """
    if message is None:
        template = ERROR_CODES.get(code, code)
        try:
            message = template.format(**kwargs)
        except (KeyError, IndexError):
            message = template
    payload = {"ok": False, "command": command, "error": code, "message": message}
    payload.update(kwargs)
    print(json.dumps(payload, ensure_ascii=False, default=str))
    sys.exit(exit_code)

# ─────────────────────────────────────────────────────────────────────────────
# 시점 취득 (state_tool.py get_kst_datetime 패턴 그대로)
# ─────────────────────────────────────────────────────────────────────────────

def get_kst_datetime(command="(unknown)"):
    """node ~/.opal/tools/date/date.js datetime 호출 → KST YYYY-MM-DD HH:mm 반환.
    실패 시 date_tool_failed 에러 응답 후 exit 2.
    """
    date_js = os.path.expanduser("~/.opal/tools/date/date.js")
    try:
        result = subprocess.run(
            ["node", date_js, "datetime"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0 or not result.stdout.strip():
            err(command, "date_tool_failed",
                message=f"exit={result.returncode}, stderr={result.stderr.strip()}",
                exit_code=2)
        return result.stdout.strip()
    except Exception as e:
        err(command, "date_tool_failed", message=str(e), exit_code=2)


def get_kst_date(command="(unknown)"):
    """KST 날짜(YYYY-MM-DD)만 반환."""
    return get_kst_datetime(command).split(" ")[0]

# ─────────────────────────────────────────────────────────────────────────────
# brain 경로·파일 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def resolve_brain_path(brain_path_str):
    """brain-path 정규화. '.'이면 cwd 기준 .opal/brain 으로 해석.

    규칙:
    - 인자가 .opal/brain 으로 끝나거나 SCHEMA.md를 포함하면 그 경로를 brain 루트로.
    - 그 외 디렉토리면 <dir>/.opal/brain 을 brain 루트로 본다.
    """
    p = pathlib.Path(brain_path_str).resolve()
    if p.name == "brain" and p.parent.name == ".opal":
        return p
    # 이미 brain 루트(SCHEMA.md 보유)면 그대로
    if (p / "SCHEMA.md").exists():
        return p
    return p / ".opal" / "brain"


def is_brain_initialized(brain_root):
    """SCHEMA.md 존재 여부로 초기화 판정."""
    return (brain_root / "SCHEMA.md").exists()


def require_brain(command, brain_path_str):
    """초기화된 brain 루트 반환. 미초기화 시 brain_not_initialized + exit 1."""
    brain_root = resolve_brain_path(brain_path_str)
    if not is_brain_initialized(brain_root):
        err(command, "brain_not_initialized", brain_path=str(brain_root))
    return brain_root


def read_template(name, command):
    """templates/<name> 읽기. 부재 시 template_missing + exit 2."""
    tpl = TEMPLATES_DIR / name
    if not tpl.exists():
        err(command, "template_missing", path=str(tpl), exit_code=2)
    return tpl.read_text(encoding="utf-8")

# ─────────────────────────────────────────────────────────────────────────────
# frontmatter 파싱 (PyYAML)
# ─────────────────────────────────────────────────────────────────────────────

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)


def parse_frontmatter(text):
    """페이지 텍스트에서 (frontmatter dict, body) 추출.
    frontmatter 블록이 없거나 YAML 파싱 실패 시 (None, text) 반환.
    """
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return None, text
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return None, text
    if not isinstance(fm, dict):
        return None, text
    return fm, m.group(2)


def validate_frontmatter(fm):
    """frontmatter 표준 검증 → 위반 detail 문자열 목록 반환 (빈 목록=정상)."""
    issues = []
    if fm is None:
        return ["frontmatter block missing or unparseable"]
    for key in REQUIRED_FRONTMATTER:
        if key not in fm or fm.get(key) in (None, ""):
            issues.append(f"missing required key: {key}")
    ptype = fm.get("type")
    if ptype is not None and ptype not in PAGE_TYPES:
        issues.append(f"invalid type: {ptype}")
    status = fm.get("status")
    if status is not None and status not in STATUS_ENUM:
        issues.append(f"invalid status: {status} (allowed: {'|'.join(STATUS_ENUM)})")
    # entity 페이지는 추가 키 일부 권장 (source_ref) — 누락은 경고가 아닌 정보용으로 생략
    return issues

# ─────────────────────────────────────────────────────────────────────────────
# 페이지 스캔
# ─────────────────────────────────────────────────────────────────────────────

def scan_pages(brain_root):
    """pages/ 하위 모든 .md 페이지를 스캔 → [{path, rel, fm, body}] 반환."""
    pages = []
    pages_dir = brain_root / "pages"
    if not pages_dir.exists():
        return pages
    for md_file in sorted(pages_dir.rglob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)
        pages.append({
            "path": md_file,
            "rel":  md_file.stem,  # 파일명(확장자 제외) = 링크 키
            "fm":   fm,
            "body": body,
        })
    return pages

# ─────────────────────────────────────────────────────────────────────────────
# index.md 렌더 (brain-tool 전담 — LLM 직접 편집 금지)
# ─────────────────────────────────────────────────────────────────────────────

def render_index(pages, now_str):
    """페이지 목록을 index.md 마크다운으로 렌더."""
    # 카테고리별 항목 수집
    buckets = {cat: [] for cat in CATEGORY_ORDER}
    for pg in pages:
        fm = pg["fm"] or {}
        ptype = fm.get("type")
        category = TYPE_TO_CATEGORY.get(ptype)
        if category is None:
            continue
        title = fm.get("title", pg["rel"])
        tags = fm.get("tags") or []
        tag_str = " ".join(f"#{t}" for t in tags) if tags else ""
        line = f"- [[{pg['rel']}]] — {title}"
        if tag_str:
            line += f" {tag_str}"
        buckets[category].append(line)

    lines = ["# Project Brain Index", f"> 갱신: {now_str}", ""]
    for cat in CATEGORY_ORDER:
        lines.append(f"## {cat}")
        if buckets[cat]:
            lines.extend(sorted(buckets[cat]))
        else:
            lines.append("(아직 등록된 페이지 없음)")
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def write_index(brain_root, pages, now_str, command):
    """index.md 재생성. 실패 시 index_write_failed."""
    content = render_index(pages, now_str)
    try:
        (brain_root / "index.md").write_text(content, encoding="utf-8")
    except OSError as e:
        err(command, "index_write_failed", detail=str(e))
    # 카테고리별 카운트 반환
    cats = {}
    for pg in pages:
        fm = pg["fm"] or {}
        cat = TYPE_TO_CATEGORY.get(fm.get("type"))
        if cat:
            cats[cat] = cats.get(cat, 0) + 1
    return cats

# ─────────────────────────────────────────────────────────────────────────────
# 1. init
# ─────────────────────────────────────────────────────────────────────────────

def cmd_init(args):
    """brain 골격 디렉토리·SCHEMA·빈 index/log 생성."""
    command = "init"
    target = pathlib.Path(args.brain_path).resolve()

    # brain_path 유효성: 부모 디렉토리가 존재해야 함
    parent = target if target.exists() else target.parent
    if not parent.exists():
        err(command, "brain_path_invalid", brain_path=str(target))

    brain_root = resolve_brain_path(args.brain_path)

    # 멱등성 — 이미 초기화됨 + --force 아니면 거부
    if is_brain_initialized(brain_root) and not args.force:
        err(command, "brain_already_initialized", brain_path=str(brain_root))

    now_date = get_kst_date(command)

    # 골격 디렉토리 생성
    created = []
    try:
        brain_root.mkdir(parents=True, exist_ok=True)
        created.append(str(brain_root))
        for d in BRAIN_DIRS:
            (brain_root / d).mkdir(parents=True, exist_ok=True)
            created.append(str(brain_root / d))
    except OSError as e:
        err(command, "brain_path_invalid", brain_path=str(brain_root), detail=str(e))

    # SCHEMA.md / index.md / log.md 복사
    schema = read_template("schema-template.md", command)
    index_tpl = read_template("index-template.md", command)
    log_tpl = read_template("log-template.md", command)

    (brain_root / "SCHEMA.md").write_text(schema, encoding="utf-8")
    (brain_root / "index.md").write_text(index_tpl, encoding="utf-8")
    (brain_root / "log.md").write_text(log_tpl, encoding="utf-8")

    ok(command,
       brain_path=str(brain_root),
       created=created,
       schema_written=True,
       force=args.force,
       initialized_at=now_date)

# ─────────────────────────────────────────────────────────────────────────────
# 2. add-page
# ─────────────────────────────────────────────────────────────────────────────

def cmd_add_page(args):
    """페이지 생성(템플릿 기반) + frontmatter 검증 + index 자동 등록."""
    command = "add-page"
    brain_root = require_brain(command, args.brain_path)

    page_type = args.type
    if page_type not in PAGE_TYPES:
        err(command, "invalid_page_type", page_type=page_type)

    # 페이지 경로 결정 — 인자가 절대/상대 경로면 그대로, 파일명만이면 pages/{type}/ 하위
    arg_path = pathlib.Path(args.path)
    name = arg_path.stem if arg_path.suffix == ".md" else arg_path.name
    # kebab-case 파일명 강제 (공백→하이픈, 소문자화는 입력 보존)
    file_name = f"{name}.md"
    page_path = brain_root / "pages" / page_type / file_name

    if page_path.exists():
        err(command, "duplicate_page", page=str(page_path))

    now_date = get_kst_date(command)

    # 템플릿 로드 후 frontmatter를 인자로 치환
    tpl = read_template(f"page-{page_type}.md", command)
    fm_tpl, body = parse_frontmatter(tpl)
    if fm_tpl is None:
        err(command, "template_missing", path=f"page-{page_type}.md (frontmatter unparseable)", exit_code=2)

    # 인자 반영
    fm_tpl["type"] = page_type
    fm_tpl["title"] = args.title
    fm_tpl["created"] = now_date
    fm_tpl["updated"] = now_date
    fm_tpl["status"] = "draft"
    if args.tags:
        fm_tpl["tags"] = [t.strip() for t in args.tags.split(",") if t.strip()]
    if args.sources:
        fm_tpl["sources"] = [s.strip() for s in args.sources.split(",") if s.strip()]

    # frontmatter 검증
    issues = validate_frontmatter(fm_tpl)
    if issues:
        err(command, "frontmatter_invalid", detail="; ".join(issues))

    fm_yaml = yaml.safe_dump(fm_tpl, allow_unicode=True, sort_keys=False, default_flow_style=False).strip()
    page_content = f"---\n{fm_yaml}\n---\n{body}"
    page_path.write_text(page_content, encoding="utf-8")

    # index 재생성 (도구 집행)
    pages = scan_pages(brain_root)
    now_str = get_kst_datetime(command)
    write_index(brain_root, pages, now_str, command)

    ok(command,
       page=str(page_path),
       type=page_type,
       title=args.title,
       indexed=True)

# ─────────────────────────────────────────────────────────────────────────────
# 3. index
# ─────────────────────────────────────────────────────────────────────────────

def cmd_index(args):
    """pages/ 스캔 → index.md 재생성."""
    command = "index"
    brain_root = require_brain(command, args.brain_path)

    pages = scan_pages(brain_root)
    now_str = get_kst_datetime(command)
    cats = write_index(brain_root, pages, now_str, command)

    ok(command,
       pages_scanned=len(pages),
       index_written=True,
       categories=cats)

# ─────────────────────────────────────────────────────────────────────────────
# 4. log
# ─────────────────────────────────────────────────────────────────────────────

def cmd_log(args):
    """log.md append (타임스탬프 자동)."""
    command = "log"
    brain_root = require_brain(command, args.brain_path)

    if args.op not in LOG_OPS:
        err(command, "invalid_log_op", op=args.op)

    now_str = get_kst_datetime(command)
    now_date = now_str.split(" ")[0]

    # 엔트리 구성
    lines = [f"## [{now_date}] {args.op} | {args.summary}"]
    if args.new:
        new_items = ", ".join(f"[[{n.strip()}]]" for n in args.new.split(",") if n.strip())
        lines.append(f"- 신규: {new_items}")
    if args.updated:
        upd_items = ", ".join(f"[[{u.strip()}]]" for u in args.updated.split(",") if u.strip())
        lines.append(f"- 갱신: {upd_items}")
    if args.sources:
        src_items = ", ".join(s.strip() for s in args.sources.split(",") if s.strip())
        lines.append(f"- 출처: {src_items}")
    entry = "\n".join(lines) + "\n\n"

    log_file = brain_root / "log.md"
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry)
    except OSError as e:
        err(command, "log_append_failed", detail=str(e))

    ok(command, logged=True, timestamp=now_str, op=args.op)

# ─────────────────────────────────────────────────────────────────────────────
# 5. search
# ─────────────────────────────────────────────────────────────────────────────

def _score_page(pg, query_lower, type_filter, tag_filter):
    """페이지 검색 점수 산출 (단순 가중치). 필터 미통과 시 None."""
    fm = pg["fm"] or {}
    if type_filter and fm.get("type") != type_filter:
        return None
    tags = [str(t).lower() for t in (fm.get("tags") or [])]
    if tag_filter and tag_filter.lower() not in tags:
        return None

    score = 0
    title = str(fm.get("title", "")).lower()
    if query_lower in title:
        score += 5
    if query_lower in pg["rel"].lower():
        score += 3
    if any(query_lower in t for t in tags):
        score += 2
    body_lower = (pg["body"] or "").lower()
    body_hits = body_lower.count(query_lower)
    score += min(body_hits, 5)  # 본문 hit는 최대 5점 캡
    return score


def _make_snippet(body, query_lower):
    """본문에서 query 주변 스니펫 추출."""
    body_lower = body.lower()
    idx = body_lower.find(query_lower)
    if idx == -1:
        snippet = body.strip().split("\n")
        snippet = next((ln.strip() for ln in snippet if ln.strip()), "")
        return snippet[:120]
    start = max(0, idx - 40)
    end = min(len(body), idx + 80)
    return body[start:end].replace("\n", " ").strip()


def cmd_search(args):
    """frontmatter tags·title·본문 검색 → 관련 페이지 반환."""
    command = "search"
    brain_root = require_brain(command, args.brain_path)

    query = (args.query or "").strip()
    if not query:
        err(command, "query_empty")
    query_lower = query.lower()

    pages = scan_pages(brain_root)
    scored = []
    for pg in pages:
        score = _score_page(pg, query_lower, args.type, args.tag)
        if score is None or score <= 0:
            continue
        fm = pg["fm"] or {}
        scored.append({
            "page":    str(pg["path"]),
            "title":   fm.get("title", pg["rel"]),
            "type":    fm.get("type"),
            "score":   score,
            "snippet": _make_snippet(pg["body"] or "", query_lower),
        })

    scored.sort(key=lambda m: m["score"], reverse=True)
    limit = args.limit if args.limit else 10
    matches = scored[:limit]

    ok(command, query=query, matches=matches, total=len(scored))

# ─────────────────────────────────────────────────────────────────────────────
# 6. sync-header (단방향: code-scan @header → brain entity frontmatter)
# ─────────────────────────────────────────────────────────────────────────────

def _load_code_scan_json(command):
    """프로젝트 .opal/code-scan.json 로드 → {relpath: header} 정규화.

    code-scan.json은 설정 파일(scopes/extensions 등)일 수 있고,
    code-scan scan --json 출력(스캔 결과)일 수도 있다. 여기서는 sync-header가
    @header 시드를 흡수하려면 스캔 결과가 필요하므로, code-scan을 직접 실행해
    @header 맵을 얻는다. code-scan.json 부재 시 code_scan_json_missing.
    """
    cwd = pathlib.Path.cwd()
    config_path = cwd / ".opal" / "code-scan.json"
    if not config_path.exists():
        err(command, "code_scan_json_missing", path=str(config_path))

    # code-scan scan --json 실행으로 @header 맵 취득 (단방향 데이터 흐름)
    code_scan_js = os.path.expanduser("~/.opal/tools/code-scan/code-scan.js")
    if not os.path.exists(code_scan_js):
        # 배포 전 개발 환경 폴백: 소스 경로 시도
        local = cwd / "opal" / "tools" / "code-scan" / "code-scan.js"
        code_scan_js = str(local) if local.exists() else code_scan_js
    try:
        result = subprocess.run(
            ["node", code_scan_js, "scan", "--json"],
            capture_output=True, text=True, timeout=60, cwd=str(cwd)
        )
        if result.returncode != 0 or not result.stdout.strip():
            err(command, "header_parse_failed",
                detail=f"code-scan exit={result.returncode}, stderr={result.stderr.strip()}")
        headers = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        err(command, "header_parse_failed", detail=f"json decode: {e}")
    except Exception as e:
        err(command, "header_parse_failed", detail=str(e))
    return headers


def cmd_sync_header(args):
    """code-scan @header와 entity 페이지 frontmatter 비교 → drift 시 단방향 갱신 + stale 표시."""
    command = "sync-header"
    brain_root = require_brain(command, args.brain_path)

    headers = _load_code_scan_json(command)  # {relpath: {module, layer, domain, exports, description}}
    now_date = get_kst_date(command)

    synced = []
    drift = []
    stale_marked = []

    pages = scan_pages(brain_root)
    for pg in pages:
        fm = pg["fm"] or {}
        if fm.get("type") != "entity":
            continue
        source_ref = fm.get("source_ref")
        if not source_ref:
            continue
        # --page 필터
        if args.page and pg["rel"] != args.page:
            continue
        # --scope 필터 (domain 또는 layer 일치)
        if args.scope and fm.get("domain") != args.scope and fm.get("layer") != args.scope:
            continue

        header = headers.get(source_ref)
        if header is None:
            # 코드가 사라졌거나 @header 없음 → stale 표시
            if fm.get("status") != "stale":
                fm["status"] = "stale"
                stale_marked.append(pg["rel"])
                _rewrite_page_fm(pg, fm)
            continue

        # @header → frontmatter 단방향 비교/갱신
        page_drift = []
        for field in ("module", "layer", "domain", "exports"):
            new_val = header.get(field)
            old_val = fm.get(field)
            if new_val is not None and new_val != old_val:
                page_drift.append({"page": pg["rel"], "field": field,
                                   "old": old_val, "new": new_val})
                fm[field] = new_val

        if page_drift:
            fm["header_synced"] = now_date
            fm["updated"] = now_date
            drift.extend(page_drift)
            _rewrite_page_fm(pg, fm)
            synced.append(pg["rel"])

    ok(command, synced=synced, drift=drift, stale_marked=stale_marked)


def _rewrite_page_fm(pg, fm):
    """페이지의 frontmatter를 새 fm으로 교체 후 저장 (본문 보존)."""
    fm_yaml = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False, default_flow_style=False).strip()
    content = f"---\n{fm_yaml}\n---\n{pg['body']}"
    pg["path"].write_text(content, encoding="utf-8")

# ─────────────────────────────────────────────────────────────────────────────
# 7. lint
# ─────────────────────────────────────────────────────────────────────────────

_WIKILINK_RE = re.compile(r"\[\[([^\]:]+)\]\]")  # [[page]] (source: 제외)


def cmd_lint(args):
    """링크 무결성·고아·stale·근거 누락 페이지 탐지 → JSON 리포트.
    kind ∈ {orphan, stale, broken_link, missing_link, unsourced, contradiction}
    """
    command = "lint"
    brain_root = require_brain(command, args.brain_path)

    pages = scan_pages(brain_root)
    page_keys = {pg["rel"] for pg in pages}
    issues = []

    # 피참조 카운트 (고아 판정용)
    referenced = set()
    for pg in pages:
        body = pg["body"] or ""
        for link in _WIKILINK_RE.findall(body):
            referenced.add(link.strip())

    for pg in pages:
        fm = pg["fm"] or {}
        body = pg["body"] or ""
        rel = pg["rel"]

        # stale: status == stale
        if fm.get("status") == "stale":
            issues.append({"kind": "stale", "page": rel,
                           "detail": "status=stale (코드 @header drift 가능)"})

        # broken_link: 본문 [[link]]가 실재 페이지 아님
        for link in _WIKILINK_RE.findall(body):
            target = link.strip()
            if target.startswith("source:"):
                continue
            if target not in page_keys:
                issues.append({"kind": "broken_link", "page": rel,
                               "detail": f"링크 대상 부재: [[{target}]]"})

        # orphan: 어떤 페이지에서도 참조되지 않고 본문 링크도 없음
        out_links = [l.strip() for l in _WIKILINK_RE.findall(body) if not l.strip().startswith("source:")]
        if rel not in referenced and not out_links:
            issues.append({"kind": "orphan", "page": rel,
                           "detail": "피참조·발신 링크 모두 없음 (고립 페이지)"})

        # missing_link: related frontmatter에 있으나 본문에 링크 부재
        related = fm.get("related") or []
        for r in related:
            r = str(r).strip()
            if r and f"[[{r}]]" not in body:
                issues.append({"kind": "missing_link", "page": rel,
                               "detail": f"related '{r}'가 본문 링크에 없음"})

        # unsourced: sources frontmatter 비어 있음 (concept/synthesis는 근거 필수)
        if fm.get("type") in ("concept", "synthesis") and not (fm.get("sources")):
            issues.append({"kind": "unsourced", "page": rel,
                           "detail": "concept/synthesis 페이지에 sources 근거 없음"})

    ok(command, issues=issues, issues_count=len(issues))

# ─────────────────────────────────────────────────────────────────────────────
# 8. validate
# ─────────────────────────────────────────────────────────────────────────────

def cmd_validate(args):
    """전체 brain 구조·frontmatter 표준 준수 검증 → violations[]."""
    command = "validate"
    brain_root = require_brain(command, args.brain_path)

    violations = []

    # 구조 검증: 필수 파일·디렉토리
    for required in ["SCHEMA.md", "index.md", "log.md"]:
        if not (brain_root / required).exists():
            violations.append({"page": None, "rule": "structure",
                               "detail": f"필수 파일 부재: {required}"})
    for d in BRAIN_DIRS:
        if not (brain_root / d).exists():
            violations.append({"page": None, "rule": "structure",
                               "detail": f"필수 디렉토리 부재: {d}"})

    # 페이지별 frontmatter·배치 검증
    pages = scan_pages(brain_root)
    for pg in pages:
        fm = pg["fm"]
        rel = pg["rel"]
        issues = validate_frontmatter(fm)
        for iss in issues:
            violations.append({"page": rel, "rule": "frontmatter", "detail": iss})
        # 타입별 디렉토리 배치 검증
        if fm:
            ptype = fm.get("type")
            if ptype in PAGE_TYPES:
                expected_dir = brain_root / "pages" / ptype
                try:
                    pg["path"].relative_to(expected_dir)
                except ValueError:
                    violations.append({"page": rel, "rule": "placement",
                                       "detail": f"type={ptype} 페이지가 pages/{ptype}/ 밖에 있음"})

    valid = len(violations) == 0
    print(json.dumps({
        "ok": valid, "command": command,
        "valid": valid, "violations": violations,
        "violations_count": len(violations),
    }, ensure_ascii=False, default=str))
    sys.exit(0 if valid else 1)

# ─────────────────────────────────────────────────────────────────────────────
# argparse
# ─────────────────────────────────────────────────────────────────────────────

def build_parser():
    parser = argparse.ArgumentParser(
        prog="brain-tool",
        description="OPAL Project Brain 지식 위키 결정론적 집행 CLI (8 서브 명령)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
서브 명령 (8종):
  init         brain 골격·SCHEMA·빈 index/log 생성
  add-page     페이지 생성 + frontmatter 검증 + index 자동 등록
  index        pages/ 스캔 → index.md 재생성
  log          log.md append (타임스탬프 자동)
  search       tags·title·본문 검색 → 관련 페이지 반환
  sync-header  code-scan @header → entity frontmatter 단방향 동기화
  lint         링크 무결성·고아·stale·근거 누락 탐지
  validate     brain 구조·frontmatter 표준 검증

호출 형식: ~/.opal/tools/brain-tool/run.sh <command> [options]
종료 코드: 0=ok  1=violation/error  2=internal_error
"""
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    # ── init ──
    p_init = sub.add_parser("init", help="brain 골격·SCHEMA·index/log 생성")
    p_init.add_argument("brain_path", metavar="<brain-path>")
    p_init.add_argument("--force", action="store_true")
    p_init.set_defaults(func=cmd_init)

    # ── add-page ──
    p_add = sub.add_parser("add-page", help="페이지 생성 + index 자동 등록")
    p_add.add_argument("path", metavar="<path>")
    p_add.add_argument("--type", required=True, choices=PAGE_TYPES)
    p_add.add_argument("--title", required=True)
    p_add.add_argument("--tags")
    p_add.add_argument("--sources")
    p_add.add_argument("--brain-path", dest="brain_path", default=".")
    p_add.set_defaults(func=cmd_add_page)

    # ── index ──
    p_idx = sub.add_parser("index", help="pages/ 스캔 → index.md 재생성")
    p_idx.add_argument("--brain-path", dest="brain_path", default=".")
    p_idx.set_defaults(func=cmd_index)

    # ── log ──
    p_log = sub.add_parser("log", help="log.md append (타임스탬프 자동)")
    p_log.add_argument("--op", required=True, choices=LOG_OPS)
    p_log.add_argument("--summary", required=True)
    p_log.add_argument("--new")
    p_log.add_argument("--updated")
    p_log.add_argument("--sources")
    p_log.add_argument("--brain-path", dest="brain_path", default=".")
    p_log.set_defaults(func=cmd_log)

    # ── search ──
    p_srch = sub.add_parser("search", help="tags·title·본문 검색")
    p_srch.add_argument("query", metavar="<query>")
    p_srch.add_argument("--type", choices=PAGE_TYPES)
    p_srch.add_argument("--tag")
    p_srch.add_argument("--limit", type=int)
    p_srch.add_argument("--brain-path", dest="brain_path", default=".")
    p_srch.set_defaults(func=cmd_search)

    # ── sync-header ──
    p_sh = sub.add_parser("sync-header", help="code-scan @header → entity frontmatter 단방향 동기화")
    p_sh.add_argument("--scope")
    p_sh.add_argument("--page")
    p_sh.add_argument("--brain-path", dest="brain_path", default=".")
    p_sh.set_defaults(func=cmd_sync_header)

    # ── lint ──
    p_lint = sub.add_parser("lint", help="링크 무결성·고아·stale·근거 누락 탐지")
    p_lint.add_argument("--brain-path", dest="brain_path", default=".")
    p_lint.set_defaults(func=cmd_lint)

    # ── validate ──
    p_val = sub.add_parser("validate", help="brain 구조·frontmatter 표준 검증")
    p_val.add_argument("--brain-path", dest="brain_path", default=".")
    p_val.set_defaults(func=cmd_validate)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
