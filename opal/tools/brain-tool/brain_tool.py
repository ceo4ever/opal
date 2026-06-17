"""
@header {
  "module": "brain_tool",
  "layer": "util",
  "domain": "opal-brain",
  "description": "OPAL Project Brain 지식 위키 결정론적 집행 CLI — 10개 서브 명령(init/add-page/index/log/search/sync-header/lint/validate/analyze/ingest-scan). index/log/링크 무결성을 brain-tool이 집행(LLM 직접 편집 금지). 페이지 타입은 SCHEMA §1.5에서 동적 로드(하드코딩 없음). frontmatter 파싱은 PyYAML, KST 타임스탬프는 date.js subprocess. sync-header는 code-scan @header → brain entity frontmatter 단방향 동기화만 수행. analyze는 code-scan @header 정량 집계 → JSON. ingest-scan은 docs/skills/tasks 목록 반환. [027] lint에 term 일관성 2종(term_duplicate·alias_collision) 추가. search에 draft 필터(--include-draft, R-6 term 한정) 추가. init이 schema-template.md에서 타입 동적 로드.",
  "exports": [
    "cmd_init", "cmd_add_page", "cmd_index", "cmd_log",
    "cmd_search", "cmd_sync_header", "cmd_lint", "cmd_validate",
    "cmd_analyze", "cmd_ingest_scan",
    "load_page_types", "DEFAULT_PAGE_TYPES"
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

# 기본 페이지 타입 후보 (기존 테스트 호환 보존, SCHEMA 부재 시 폴백)
DEFAULT_PAGE_TYPES = ["entity", "concept", "flow", "synthesis"]

# 하위 호환 alias — 기존 테스트(BT.PAGE_TYPES)가 그대로 통과
PAGE_TYPES = DEFAULT_PAGE_TYPES

# 기본 index.md 카테고리 헤더 ↔ 페이지 타입 매핑 (SCHEMA 부재 시 폴백)
_DEFAULT_TYPE_TO_CATEGORY = {
    "entity":    "엔티티",
    "concept":   "개념",
    "flow":      "흐름",
    "synthesis": "합성",
}
_DEFAULT_CATEGORY_ORDER = ["도메인", "개념", "엔티티", "흐름", "합성"]

# 모듈 수준 노출 상수 (기존 테스트 CATEGORY_ORDER 참조 호환)
TYPE_TO_CATEGORY = _DEFAULT_TYPE_TO_CATEGORY
CATEGORY_ORDER = _DEFAULT_CATEGORY_ORDER

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

# 기본 brain 골격 디렉토리 (SCHEMA 부재 시 폴백)
_DEFAULT_BRAIN_DIRS = [
    "pages/entity", "pages/concept", "pages/flow", "pages/synthesis",
    "sources",
]

# 모듈 수준 노출 상수 (기존 테스트 BRAIN_DIRS 참조 호환)
BRAIN_DIRS = _DEFAULT_BRAIN_DIRS

# 템플릿 디렉토리 (스크립트와 동일 위치)
TEMPLATES_DIR = pathlib.Path(__file__).resolve().parent / "templates"

# ─────────────────────────────────────────────────────────────────────────────
# SCHEMA 동적 타입 로드
# ─────────────────────────────────────────────────────────────────────────────

_SCHEMA_TABLE_RE = re.compile(
    r"##\s+1\.5\s+페이지 타입 정의[^\n]*\n.*?\n"  # 절 헤더 + 설명 줄
    r"\|[^\n]*\n\|[-| ]+\n"                       # 테이블 헤더 + 구분선
    r"((?:\|[^\n]*\n)+)",                          # 테이블 데이터 행들
    re.DOTALL,
)


def load_page_types(brain_root):
    """SCHEMA.md §1.5 테이블에서 타입 세트를 동적 로드.

    반환: (types: list[str], type_to_category: dict[str, str])
    SCHEMA 부재·파싱 실패 시 DEFAULT_PAGE_TYPES로 graceful 폴백.
    """
    schema_path = pathlib.Path(brain_root) / "SCHEMA.md"
    if not schema_path.exists():
        return list(DEFAULT_PAGE_TYPES), dict(_DEFAULT_TYPE_TO_CATEGORY)

    try:
        text = schema_path.read_text(encoding="utf-8")
        m = _SCHEMA_TABLE_RE.search(text)
        if not m:
            return list(DEFAULT_PAGE_TYPES), dict(_DEFAULT_TYPE_TO_CATEGORY)

        rows_text = m.group(1)
        types = []
        type_to_cat = {}
        for row in rows_text.strip().splitlines():
            # 행 파싱: | type | category | 설명 |
            cols = [c.strip() for c in row.strip().strip("|").split("|")]
            if len(cols) >= 2:
                ptype = cols[0].strip()
                category = cols[1].strip()
                if ptype and category:
                    types.append(ptype)
                    type_to_cat[ptype] = category

        if not types:
            return list(DEFAULT_PAGE_TYPES), dict(_DEFAULT_TYPE_TO_CATEGORY)

        return types, type_to_cat

    except Exception:
        return list(DEFAULT_PAGE_TYPES), dict(_DEFAULT_TYPE_TO_CATEGORY)


def _get_category_order(type_to_category):
    """type_to_category에서 CATEGORY_ORDER를 파생 (도메인 선두 고정)."""
    cats = list(dict.fromkeys(type_to_category.values()))  # 삽입 순서 보존·중복 제거
    if "도메인" not in cats:
        cats = ["도메인"] + cats
    return cats


def _get_brain_dirs(types):
    """타입 목록에서 BRAIN_DIRS를 파생."""
    dirs = [f"pages/{t}" for t in types]
    dirs.append("sources")
    return dirs


# ERROR_CODES 카탈로그 SSOT — 모든 error 응답 값은 이 상수의 키를 참조한다. 임의 변형 금지.
ERROR_CODES = {
    "brain_already_initialized":  "brain이 이미 초기화됨: {brain_path}. --force로만 재초기화 가능",
    "brain_path_invalid":         "brain-path가 유효하지 않음: {brain_path}",
    "brain_not_initialized":      "brain이 초기화되지 않음 (.opal/brain/SCHEMA.md 부재): {brain_path}",
    "invalid_page_type":          "유효하지 않은 페이지 타입: {page_type} (허용: {allowed})",
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


def validate_frontmatter(fm, page_types=None):
    """frontmatter 표준 검증 → 위반 detail 문자열 목록 반환 (빈 목록=정상).

    page_types: 동적 타입 목록 (None이면 모듈 상수 PAGE_TYPES 사용).
    """
    allowed_types = page_types if page_types is not None else PAGE_TYPES
    issues = []
    if fm is None:
        return ["frontmatter block missing or unparseable"]
    for key in REQUIRED_FRONTMATTER:
        if key not in fm or fm.get(key) in (None, ""):
            issues.append(f"missing required key: {key}")
    ptype = fm.get("type")
    if ptype is not None and ptype not in allowed_types:
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

def render_index(pages, now_str, type_to_category=None, category_order=None):
    """페이지 목록을 index.md 마크다운으로 렌더.

    type_to_category, category_order: 동적 타입 매핑 (None이면 모듈 상수 사용).
    """
    ttc = type_to_category if type_to_category is not None else TYPE_TO_CATEGORY
    cat_order = category_order if category_order is not None else CATEGORY_ORDER
    # 카테고리별 항목 수집
    buckets = {cat: [] for cat in cat_order}
    for pg in pages:
        fm = pg["fm"] or {}
        ptype = fm.get("type")
        category = ttc.get(ptype)
        if category is None:
            continue
        title = fm.get("title", pg["rel"])
        tags = fm.get("tags") or []
        tag_str = " ".join(f"#{t}" for t in tags) if tags else ""
        line = f"- [[{pg['rel']}]] — {title}"
        if tag_str:
            line += f" {tag_str}"
        buckets.setdefault(category, []).append(line)

    lines = ["# Project Brain Index", f"> 갱신: {now_str}", ""]
    for cat in cat_order:
        lines.append(f"## {cat}")
        if buckets.get(cat):
            lines.extend(sorted(buckets[cat]))
        else:
            lines.append("(아직 등록된 페이지 없음)")
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def write_index(brain_root, pages, now_str, command, type_to_category=None, category_order=None):
    """index.md 재생성. 실패 시 index_write_failed.

    type_to_category, category_order: 동적 타입 매핑 (None이면 모듈 상수 사용).
    """
    ttc = type_to_category if type_to_category is not None else TYPE_TO_CATEGORY
    content = render_index(pages, now_str, ttc, category_order)
    try:
        (brain_root / "index.md").write_text(content, encoding="utf-8")
    except OSError as e:
        err(command, "index_write_failed", detail=str(e))
    # 카테고리별 카운트 반환
    cats = {}
    for pg in pages:
        fm = pg["fm"] or {}
        cat = ttc.get(fm.get("type"))
        if cat:
            cats[cat] = cats.get(cat, 0) + 1
    return cats

# ─────────────────────────────────────────────────────────────────────────────
# 1. init
# ─────────────────────────────────────────────────────────────────────────────

def cmd_init(args):
    """brain 골격 디렉토리·SCHEMA·빈 index/log 생성.

    --types <csv>: 사용자 확정 타입 세트(예: entity,concept,flow). 미지정 시 DEFAULT_PAGE_TYPES.
    """
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

    # --types 파싱 (미지정 시 schema-template.md에서 동적 로드 → 폴백 DEFAULT_PAGE_TYPES)
    if getattr(args, "types", None):
        init_types = [t.strip() for t in args.types.split(",") if t.strip()]
    else:
        # schema-template.md를 먼저 파싱해 타입 목록을 추출한다.
        # 이렇게 하면 init이 생성하는 dirs와 SCHEMA가 기록하는 타입 세트가 항상 일치한다.
        try:
            schema_tpl_path = TEMPLATES_DIR / "schema-template.md"
            if schema_tpl_path.exists():
                tpl_text = schema_tpl_path.read_text(encoding="utf-8")
                m_tpl = _SCHEMA_TABLE_RE.search(tpl_text)
                if m_tpl:
                    tpl_types = []
                    for row in m_tpl.group(1).strip().splitlines():
                        cols = [c.strip() for c in row.strip().strip("|").split("|")]
                        if len(cols) >= 1 and cols[0]:
                            tpl_types.append(cols[0])
                    init_types = tpl_types if tpl_types else list(DEFAULT_PAGE_TYPES)
                else:
                    init_types = list(DEFAULT_PAGE_TYPES)
            else:
                init_types = list(DEFAULT_PAGE_TYPES)
        except Exception:
            init_types = list(DEFAULT_PAGE_TYPES)

    # 골격 디렉토리 생성 (타입 기반 동적)
    brain_dirs = _get_brain_dirs(init_types)
    created = []
    try:
        brain_root.mkdir(parents=True, exist_ok=True)
        created.append(str(brain_root))
        for d in brain_dirs:
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
       types=init_types,
       initialized_at=now_date)

# ─────────────────────────────────────────────────────────────────────────────
# 2. add-page
# ─────────────────────────────────────────────────────────────────────────────

def cmd_add_page(args):
    """페이지 생성(템플릿 기반) + frontmatter 검증 + index 자동 등록."""
    command = "add-page"
    brain_root = require_brain(command, args.brain_path)

    # --type 검증: argparse choices 제거 후 명령 내부에서 동적 타입 목록으로 검증
    page_type = args.type
    dyn_types, type_to_cat = load_page_types(brain_root)
    if page_type not in dyn_types:
        err(command, "invalid_page_type", page_type=page_type,
            allowed="|".join(dyn_types))

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

    # frontmatter 검증 (동적 타입 목록 사용)
    issues = validate_frontmatter(fm_tpl, page_types=dyn_types)
    if issues:
        err(command, "frontmatter_invalid", detail="; ".join(issues))

    fm_yaml = yaml.safe_dump(fm_tpl, allow_unicode=True, sort_keys=False, default_flow_style=False).strip()
    page_content = f"---\n{fm_yaml}\n---\n{body}"
    page_path.write_text(page_content, encoding="utf-8")

    # index 재생성 (도구 집행, 동적 타입 매핑 사용)
    pages = scan_pages(brain_root)
    now_str = get_kst_datetime(command)
    cat_order = _get_category_order(type_to_cat)
    write_index(brain_root, pages, now_str, command, type_to_cat, cat_order)

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

    dyn_types, type_to_cat = load_page_types(brain_root)
    cat_order = _get_category_order(type_to_cat)
    pages = scan_pages(brain_root)
    now_str = get_kst_datetime(command)
    cats = write_index(brain_root, pages, now_str, command, type_to_cat, cat_order)

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

def _norm(s):
    """검색 시점 정규화 — 소문자화 + 모든 공백 제거 (휘발성 사본 전용).

    str.split() (인자 없음)은 스페이스·탭·개행·전각 공백 등 공백류를 모두 분리한다.
    stdlib만 사용. 결정론 보장 (동일 입력 → 동일 출력).
    """
    return "".join(str(s).lower().split())


def _score_page(pg, query_norm, type_filter, tag_filter, include_draft=False):
    """페이지 검색 점수 산출 (단순 가중치). 필터 미통과 시 None.

    query_norm: _norm() 적용된 정규화 쿼리 (공백 제거 + 소문자).
    4필드(title/rel/tags/body) 비교는 _norm 사본 기준.
    --tag 필터는 기존 소문자 정확 일치 유지(회귀 0, H-6).
    tag 가중치(+2) 매칭만 _norm 적용.
    include_draft: True이면 draft term도 포함. False(기본)이면 type==term AND status==draft 제외.
    [R-6 결정 2026-06-17]: draft 필터는 type=='term'에만 적용. 비-term 타입은 draft여도 노출.
    """
    fm = pg["fm"] or {}
    if type_filter and fm.get("type") != type_filter:
        return None
    # R-6 term 한정 draft 필터: type==term AND status==draft → include_draft=False 시 제외
    if (not include_draft
            and fm.get("type") == "term"
            and fm.get("status") == "draft"):
        return None
    # tag_filter: 정확 일치(정규화 미적용) — 기존 동작 보존
    tags_raw = [str(t) for t in (fm.get("tags") or [])]
    tags_lower = [t.lower() for t in tags_raw]
    if tag_filter and tag_filter.lower() not in tags_lower:
        return None

    score = 0
    if query_norm in _norm(fm.get("title", "")):
        score += 5
    if query_norm in _norm(pg["rel"]):
        score += 3
    # tag 가중치 매칭은 _norm 적용 (4필드 일괄 정규화 일관성)
    if any(query_norm in _norm(t) for t in tags_raw):
        score += 2
    body_norm = _norm(pg["body"] or "")
    body_hits = body_norm.count(query_norm) if query_norm else 0
    score += min(body_hits, 5)  # 본문 hit는 최대 5점 캡
    return score


def _make_snippet(body, query_norm):
    """본문에서 query 주변 스니펫 추출 — 정규화 기준 매칭 + 원문(공백 포함) 반환.

    query_norm: _norm() 적용된 정규화 쿼리.
    정규화 인덱스 → 원문 인덱스 역매핑으로 공백 포함 원문 스니펫을 반환한다.
    fallback(첫 비어있지 않은 라인 120자)은 기존 동작 보존.
    """
    # 원문 각 문자의 "공백 제거 후 정규화 인덱스" 매핑 테이블 구성
    norm_chars = []   # 정규화된 문자열
    orig_index = []   # norm_chars[i]가 원문에서 위치한 인덱스
    for i, ch in enumerate(body):
        if ch.isspace():
            continue
        norm_chars.append(ch.lower())
        orig_index.append(i)
    body_norm = "".join(norm_chars)

    pos = body_norm.find(query_norm) if query_norm else -1
    if pos == -1:
        # fallback — 첫 비어있지 않은 라인 앞 120자 (기존 동작 보존)
        first = next((ln.strip() for ln in body.split("\n") if ln.strip()), "")
        return first[:120]
    orig_start = orig_index[pos]           # 원문 매칭 시작 위치
    start = max(0, orig_start - 40)
    end = min(len(body), orig_start + 80)
    return body[start:end].replace("\n", " ").strip()


def cmd_search(args):
    """frontmatter tags·title·본문 검색 → 관련 페이지 반환."""
    command = "search"
    brain_root = require_brain(command, args.brain_path)

    query = (args.query or "").strip()
    if not query:
        err(command, "query_empty")
    query_norm = _norm(query)

    include_draft = getattr(args, "include_draft", False)
    pages = scan_pages(brain_root)
    scored = []
    for pg in pages:
        score = _score_page(pg, query_norm, args.type, args.tag, include_draft=include_draft)
        if score is None or score <= 0:
            continue
        fm = pg["fm"] or {}
        scored.append({
            "page":    str(pg["path"]),
            "title":   fm.get("title", pg["rel"]),
            "type":    fm.get("type"),
            "score":   score,
            "snippet": _make_snippet(pg["body"] or "", query_norm),
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

    # ── term 일관성 검출 2종 (027) ─────────────────────────────────────────
    # term 페이지만 추출 — term 미채택 brain은 0건, 회귀 0 보장
    term_pages = [pg for pg in pages if (pg["fm"] or {}).get("type") == "term"]

    if term_pages:
        # term_duplicate: 정규화된 title이 동일한 term 페이지 쌍 검출
        # [MUST] 자동 동의어 해소·임베딩 금지 — _norm(소문자+공백제거) 정확 일치만
        norm_to_terms = {}  # {norm_title: [rel, ...]}
        for pg in term_pages:
            fm = pg["fm"] or {}
            title = fm.get("title", "")
            nt = _norm(title)
            if nt:
                norm_to_terms.setdefault(nt, []).append(pg["rel"])
        for nt, rels in norm_to_terms.items():
            if len(rels) >= 2:
                for rel in rels:
                    issues.append({
                        "kind": "term_duplicate",
                        "page": rel,
                        "detail": f"정규화 표준명 '{nt}' 중복 — {', '.join(rels)}",
                    })

        # alias_collision: 한 term의 alias가 다른 term의 title 또는 alias와 충돌 검출
        # 충돌 = 동일 정규화 (_norm)
        # 모든 term의 {norm: source_rel} 맵 구성 (title + aliases 모두 포함)
        term_norm_map = {}  # {norm_value: rel} — title/alias 출처 페이지
        for pg in term_pages:
            fm = pg["fm"] or {}
            rel = pg["rel"]
            title = fm.get("title", "")
            nt = _norm(title)
            if nt:
                term_norm_map.setdefault(nt, []).append(("title", rel))
            for alias in (fm.get("aliases") or []):
                na = _norm(str(alias))
                if na:
                    term_norm_map.setdefault(na, []).append(("alias", rel))

        # alias_collision: 같은 norm 값이 서로 다른 페이지(alias 출처가 다른 페이지)에 존재
        alias_collision_reported = set()
        for pg in term_pages:
            fm = pg["fm"] or {}
            rel = pg["rel"]
            for alias in (fm.get("aliases") or []):
                na = _norm(str(alias))
                if not na:
                    continue
                sources = term_norm_map.get(na, [])
                # 이 alias의 norm값을 가진 title/alias가 다른 페이지에도 존재하면 충돌
                other_sources = [(kind, src_rel) for kind, src_rel in sources if src_rel != rel]
                if other_sources:
                    collision_key = tuple(sorted([rel] + [s[1] for s in other_sources]))
                    if collision_key not in alias_collision_reported:
                        alias_collision_reported.add(collision_key)
                        other_rels = ", ".join(f"{k}:{r}" for k, r in other_sources)
                        issues.append({
                            "kind": "alias_collision",
                            "page": rel,
                            "detail": f"alias '{alias}' 정규화 충돌 — {other_rels}",
                        })

    ok(command, issues=issues, issues_count=len(issues))

# ─────────────────────────────────────────────────────────────────────────────
# 8. validate
# ─────────────────────────────────────────────────────────────────────────────

def cmd_validate(args):
    """전체 brain 구조·frontmatter 표준 준수 검증 → violations[]."""
    command = "validate"
    brain_root = require_brain(command, args.brain_path)

    dyn_types, type_to_cat = load_page_types(brain_root)
    brain_dirs = _get_brain_dirs(dyn_types)
    violations = []

    # 구조 검증: 필수 파일·디렉토리
    for required in ["SCHEMA.md", "index.md", "log.md"]:
        if not (brain_root / required).exists():
            violations.append({"page": None, "rule": "structure",
                               "detail": f"필수 파일 부재: {required}"})
    for d in brain_dirs:
        if not (brain_root / d).exists():
            violations.append({"page": None, "rule": "structure",
                               "detail": f"필수 디렉토리 부재: {d}"})

    # 페이지별 frontmatter·배치 검증 (동적 타입 목록 사용)
    pages = scan_pages(brain_root)
    for pg in pages:
        fm = pg["fm"]
        rel = pg["rel"]
        issues = validate_frontmatter(fm, page_types=dyn_types)
        for iss in issues:
            violations.append({"page": rel, "rule": "frontmatter", "detail": iss})
        # 타입별 디렉토리 배치 검증
        if fm:
            ptype = fm.get("type")
            if ptype in dyn_types:
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
# 9. analyze — code-scan @header 정량 집계 (결정론적, LLM 입력용)
# ─────────────────────────────────────────────────────────────────────────────

def cmd_analyze(args):
    """code-scan @header에서 domain·layer·exports·피의존도를 정량 집계 → JSON.

    결정론적 집계만 수행. 요약·제안은 LLM이 담당한다.
    code-scan.json 부재 시 code_scan_json_missing 에러.
    """
    command = "analyze"

    headers = _load_code_scan_json(command)  # {relpath: {module, layer, domain, exports, ...}}

    # domain별 모듈 수 집계
    domain_counts = {}
    # layer별 모듈 수 집계
    layer_counts = {}
    # exports 수 분포 (exports_count)
    exports_dist = {}
    # 피의존도 집계: source_ref → 참조 수 (forward ref 파싱)
    dependents = {}

    for relpath, header in headers.items():
        if not isinstance(header, dict):
            continue

        domain = header.get("domain") or "unknown"
        domain_counts[domain] = domain_counts.get(domain, 0) + 1

        layer = header.get("layer") or "unknown"
        layer_counts[layer] = layer_counts.get(layer, 0) + 1

        exports = header.get("exports") or []
        if isinstance(exports, list):
            n = len(exports)
        else:
            n = 0
        bucket = str(n)
        exports_dist[bucket] = exports_dist.get(bucket, 0) + 1

        # 피의존도: 각 파일이 참조하는 모듈(imports)에 +1
        imports = header.get("imports") or []
        if isinstance(imports, list):
            for imp in imports:
                dependents[imp] = dependents.get(imp, 0) + 1

    # SEED_THRESHOLDS 기준 시드 후보 목록
    seed_candidates = []
    for relpath, header in headers.items():
        if not isinstance(header, dict):
            continue
        exports = header.get("exports") or []
        exp_count = len(exports) if isinstance(exports, list) else 0
        layer = header.get("layer") or ""
        module = header.get("module") or relpath
        dep_count = dependents.get(module, 0)
        if (exp_count >= SEED_THRESHOLDS["exports_min"]
                or dep_count >= SEED_THRESHOLDS["dependents_min"]
                or layer in SEED_THRESHOLDS["seed_layers"]):
            seed_candidates.append({
                "path": relpath,
                "module": module,
                "layer": layer,
                "domain": header.get("domain") or "unknown",
                "exports_count": exp_count,
                "dependents_count": dep_count,
            })

    ok(command,
       total_files=len(headers),
       domain_counts=domain_counts,
       layer_counts=layer_counts,
       exports_distribution=exports_dist,
       seed_candidates=seed_candidates,
       seed_thresholds=SEED_THRESHOLDS)


# ─────────────────────────────────────────────────────────────────────────────
# 10. ingest-scan — docs/skills/tasks 스캔 목록 반환 (멱등 skip 판정 포함)
# ─────────────────────────────────────────────────────────────────────────────

def cmd_ingest_scan(args):
    """docs/.md·skills·tasks 스캔 → 멱등 skip 판정과 함께 목록 반환 (LLM 배치 대상).

    --source docs|skills|tasks|all: 스캔 범위 지정
    brain 이미 ingest된 항목(sources 참조 일치)은 skip=true로 표시.
    본문 요약은 LLM이 담당. 이 명령은 목록(결정론)만 반환.
    """
    command = "ingest-scan"
    brain_root = require_brain(command, args.brain_path)

    source = getattr(args, "source", "all") or "all"
    cwd = pathlib.Path.cwd()

    # 이미 ingest된 sources 수집 (멱등 skip 판정용)
    pages = scan_pages(brain_root)
    ingested_sources = set()
    for pg in pages:
        fm = pg["fm"] or {}
        for src in (fm.get("sources") or []):
            ingested_sources.add(str(src).strip())

    results = []

    def _is_ingested(ref):
        return ref in ingested_sources

    # docs 스캔
    if source in ("docs", "all"):
        docs_dir = cwd / "docs"
        if docs_dir.exists():
            for md_file in sorted(docs_dir.rglob("*.md")):
                rel = str(md_file.relative_to(cwd))
                ref = f"doc:{rel}"
                results.append({
                    "kind": "doc",
                    "path": rel,
                    "source_ref": ref,
                    "skip": _is_ingested(ref),
                })

    # skills 스캔
    if source in ("skills", "all"):
        for skills_root in [cwd / "opal" / "skills", cwd / "skills"]:
            if skills_root.exists():
                for skill_md in sorted(skills_root.rglob("SKILL.md")):
                    rel = str(skill_md.relative_to(cwd))
                    ref = f"skill:{skill_md.parent.name}"
                    results.append({
                        "kind": "skill",
                        "path": rel,
                        "source_ref": ref,
                        "skip": _is_ingested(ref),
                    })
                break  # 첫 번째 존재 경로만 사용

    # tasks 스캔
    if source in ("tasks", "all"):
        tasks_dir = cwd / "tasks"
        if tasks_dir.exists():
            for task_dir in sorted(tasks_dir.iterdir()):
                if not task_dir.is_dir():
                    continue
                # tasks/NNN-xxx 형식 확인
                name = task_dir.name
                parts = name.split("-", 1)
                if not parts[0].isdigit():
                    continue
                task_num = parts[0]
                ref = f"task:{task_num}"
                # DONE.md 또는 PLAN.md 존재 여부
                done_exists = (task_dir / "DONE.md").exists()
                plan_exists = (task_dir / "PLAN.md").exists()
                results.append({
                    "kind": "task",
                    "path": str(task_dir.relative_to(cwd)),
                    "task_num": task_num,
                    "source_ref": ref,
                    "has_done": done_exists,
                    "has_plan": plan_exists,
                    "skip": _is_ingested(ref),
                })

    total = len(results)
    skip_count = sum(1 for r in results if r["skip"])
    pending = [r for r in results if not r["skip"]]

    ok(command,
       source=source,
       total=total,
       skip_count=skip_count,
       pending_count=len(pending),
       items=results)


# ─────────────────────────────────────────────────────────────────────────────
# argparse
# ─────────────────────────────────────────────────────────────────────────────

def build_parser():
    parser = argparse.ArgumentParser(
        prog="brain-tool",
        description="OPAL Project Brain 지식 위키 결정론적 집행 CLI (10 서브 명령)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
서브 명령 (10종):
  init          brain 골격·SCHEMA·빈 index/log 생성
  add-page      페이지 생성 + frontmatter 검증 + index 자동 등록
  index         pages/ 스캔 → index.md 재생성
  log           log.md append (타임스탬프 자동)
  search        tags·title·본문 검색 → 관련 페이지 반환
  sync-header   code-scan @header → entity frontmatter 단방향 동기화
  lint          링크 무결성·고아·stale·근거 누락 탐지
  validate      brain 구조·frontmatter 표준 검증
  analyze       code-scan @header 정량 집계 → JSON (init 제안 입력용)
  ingest-scan   docs/skills/tasks 스캔 → 멱등 skip 판정 목록 반환

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
    p_init.add_argument("--types", default=None,
                        help="사용자 확정 타입 세트 csv (예: entity,concept,flow). 미지정 시 기본 4종")
    p_init.set_defaults(func=cmd_init)

    # ── add-page ──
    p_add = sub.add_parser("add-page", help="페이지 생성 + index 자동 등록")
    p_add.add_argument("path", metavar="<path>")
    p_add.add_argument("--type", required=True)   # choices 제거 → cmd_add_page 내부 검증
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
    p_srch.add_argument("--type")   # choices 제거 → 필터로만 동작 (유효하지 않으면 0 결과)
    p_srch.add_argument("--tag")
    p_srch.add_argument("--limit", type=int)
    p_srch.add_argument("--include-draft", dest="include_draft", action="store_true",
                        default=False,
                        help="draft 상태 term 페이지도 검색 결과에 포함 (기본: term draft 제외)")
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

    # ── analyze ──
    p_analyze = sub.add_parser("analyze", help="code-scan @header 정량 집계 → JSON (init 제안 입력용)")
    p_analyze.set_defaults(func=cmd_analyze)

    # ── ingest-scan ──
    p_iscan = sub.add_parser("ingest-scan", help="docs/skills/tasks 스캔 → 멱등 skip 판정 목록 반환")
    p_iscan.add_argument("--source", default="all",
                         choices=["docs", "skills", "tasks", "all"],
                         help="스캔 범위 (기본: all)")
    p_iscan.add_argument("--brain-path", dest="brain_path", default=".")
    p_iscan.set_defaults(func=cmd_ingest_scan)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
