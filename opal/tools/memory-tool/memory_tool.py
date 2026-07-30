"""
@header {
  "module": "memory_tool",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "OPAL 메모리 관리 CLI — MEMORY.json SSOT + 9서브명령 init/append/update/promote/prune/show/review/delete/task-number. lazy 자동 마이그레이션(MEMORY.md→MEMORY.json, .bak 보존)·표준 라이브러리 전용 스키마 런타임 검증기(validate_document)·파일 락 기반 원자적 쓰기(memory_lock/atomic_write_json)·요약 길이캡(≤80)·히스토리 FIFO=5·promote 무손실 이전(--to docs|brain --ref 필수)·자가검토(review) 매 변경 명령 자동 첨부. update --kind history로 작업 히스토리 행 정정(무손실·행수 불변, FIFO 미적용). state-tool ok/err/ERROR_CODES 패턴 재사용. 표준 라이브러리만.",
  "exports": [
    "cmd_init", "cmd_append", "cmd_update", "cmd_promote",
    "cmd_prune", "cmd_show", "cmd_review", "cmd_delete", "cmd_task_number",
    "build_review_block", "load_document", "atomic_write_json",
    "memory_lock", "validate_document", "_migrate_md_to_json"
  ]
}

변경이력:
  v1.1 2026-07-17 VALID_TYPES에 "improvement", VALID_STATUSES에 "candidate" 추가(additive) —
                  improve-tool record --scope local의 memory-tool append 위임 대상 (058)
  v2.0 2026-07-28 MEMORY.json 전환(078) — 구 마커·표 파싱 계층 및 구 변환 서브명령 소멸,
                  lazy 자동 마이그레이션(_migrate_md_to_json) 신설, task-number 서브명령 추가,
                  (fix) argparse help/description 잔존 MEMORY.md 표기 8건 → MEMORY.json 정정,
                  init description을 실제 동작(JSON 문서 create-if-absent)에 맞게 재서술
  v2.1 2026-07-30 update --kind history 정정 명령 추가(079) — --kind/--stage/--result/--path
                  인자 신설, _check_update_kind_args(락 밖 조합 게이트)·_apply_history_correction
                  (무손실 in-place 정정, FIFO 미적용) 신설. --kind memory(기본) 기존 동작 무변경.
"""

# 표준 라이브러리만 (state-tool 동형)
import argparse
import contextlib
import json
import os
import pathlib
import re
import sys
import time
from datetime import datetime, timezone, timedelta

# ─────────────────────────────────────────────────────────────────────────────
# 스키마 로드 (P-1 — 스키마 파일이 SSOT, 코드가 런타임에 파생한다)
# ─────────────────────────────────────────────────────────────────────────────

SCHEMA_PATH = pathlib.Path(__file__).resolve().parent / "schema" / "memory.schema.json"


def _load_schema():
    """schema/memory.schema.json 로드. 부재·파손 시 None (크래시 금지, H-13).
    None이면 main()이 전 서브명령을 schema_load_failed로 결정론 거부한다.
    """
    try:
        with open(SCHEMA_PATH, encoding="utf-8") as f:
            schema = json.load(f)
    except Exception:
        return None
    # 파생에 필요한 최소 구조 확인 — 하나라도 없으면 로드 실패로 간주
    try:
        props = schema["$defs"]["memoryRow"]["properties"]
        _ = props["type"]["enum"], props["status"]["enum"], props["summary"]["maxLength"]
        _ = schema["properties"]["version"]["const"]
        _ = schema["x-constants"]["HISTORY_FIFO_LIMIT"]
    except (KeyError, TypeError):
        return None
    return schema


SCHEMA = _load_schema()

# ─────────────────────────────────────────────────────────────────────────────
# 스키마 파생 상수 (SSOT = schema/memory.schema.json — 하드코딩 금지)
# ─────────────────────────────────────────────────────────────────────────────

if SCHEMA is not None:
    _MEM_PROPS = SCHEMA["$defs"]["memoryRow"]["properties"]
    _HIST_PROPS = SCHEMA["$defs"]["historyRow"]["properties"]
    _X_CONSTANTS = SCHEMA.get("x-constants", {})
    _X_ADVISORY = SCHEMA.get("x-advisory", {})

    VALID_TYPES = set(_MEM_PROPS["type"]["enum"])
    VALID_STATUSES = set(_MEM_PROPS["status"]["enum"])
    SUMMARY_MAX_LENGTH = _MEM_PROPS["summary"]["maxLength"]
    DATE_PATTERN = _MEM_PROPS["date"]["pattern"]
    FILE_PATTERN = _MEM_PROPS["file"]["pattern"]
    CURRENT_VERSION = SCHEMA["properties"]["version"]["const"]
    HISTORY_FIFO_LIMIT = _X_CONSTANTS["HISTORY_FIFO_LIMIT"]
    PROMOTE_AGE_DAYS = _X_CONSTANTS.get("PROMOTE_AGE_DAYS", 30)
    TITLE_MAX_LENGTH = _X_ADVISORY.get("TITLE_MAX_LENGTH", 30)
else:  # 스키마 부재 — main()이 schema_load_failed로 거부하므로 값은 쓰이지 않는다
    VALID_TYPES = set()
    VALID_STATUSES = set()
    SUMMARY_MAX_LENGTH = 0
    DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}$"
    FILE_PATTERN = r"^memory/[^/].*\.md$"
    CURRENT_VERSION = 1
    HISTORY_FIFO_LIMIT = 5
    PROMOTE_AGE_DAYS = 30
    TITLE_MAX_LENGTH = 30

# 구 md 태그 리터럴 (마이그레이션 전용 — 구 태그 사이 영역을 찾기 위한 문자열 상수.
# 신 JSON 계약에는 이 개념이 없다. 변수명에 예약어를 쓰지 않는다 — TS-006)
_LEGACY_INDEX_TAG_START = "<!-- memory:index:start -->"
_LEGACY_INDEX_TAG_END   = "<!-- memory:index:end -->"
_LEGACY_HISTORY_TAG_START = "<!-- memory:history:start -->"
_LEGACY_HISTORY_TAG_END   = "<!-- memory:history:end -->"

# TS-015(2) 결함 주입 훅 — 참이면 히스토리 헤더 프로파일 매칭·위치 폴백을 무력화한다.
_ENV_DISABLE_HISTORY_PROFILES = "MEMORY_TOOL_DISABLE_HISTORY_PROFILES"

# 상태 매핑 (변환기용 — 구포맷 자유 상태값 → 신 enum)
LEGACY_STATUS_MAP = {
    "대기":     "active",
    "예정":     "active",
    "유지":     "active",
    "active":   "active",
    "진행":     "active",
    "진행중":   "active",
    "완료":     "dead",
    "dead":     "dead",
    "폐기 기록": "superseded",
    "폐기":     "superseded",
    "superseded": "superseded",
    "promoted": "promoted",
}

# ERROR_CODES (SSOT — memory-tool 전용)
ERROR_CODES = {
    "memory_file_not_found": "<file>에 해당하는 메모리 파일이 없음: {path}",
    "row_not_found":         "--title '{title}'에 해당하는 인덱스 행이 없음",
    "already_initialized":   "MEMORY.json이 이미 존재합니다 — --force로 재초기화",
    "invalid_kind":          "--kind는 memory 또는 history 중 하나여야 함: {kind}",
    "invalid_type":          "--type {value}는 유형 enum(project/architecture/feedback/preferences/issues/task)에 없음",
    "invalid_status":        "--status {value}는 라이프사이클 enum(active/promoted/superseded/dead)에 없음",
    "summary_too_long":      "요약 {length}자 > 80자 제한 (R2) — 상세는 개별 .md 본문으로",
    "title_required":        "--title은 필수 비공백 문자열",
    "invalid_promote_target": "--to는 docs 또는 brain 중 하나여야 함: {value}",
    "promote_ref_missing":   "--ref(영구 거처 위치) 필수 — 이전 미확인 promote 거부 (무손실, H-1)",
    "date_tool_failed":      "node ~/.opal/tools/date/date.js 호출 실패 — MEMORY.md 변경 없음(원자성)",
    "delete_requires_dead_or_superseded": "delete는 status가 dead 또는 superseded인 행만 허용 (무손실 가드) — active/promoted 행은 먼저 상태를 변경하세요",
    # ── 078 신설 (PLAN §3.2.3) ──
    "memory_json_not_found":      "MEMORY.json이 존재하지 않음 — init을 먼저 실행하세요: {path}",
    "invalid_json":               "MEMORY.json 파싱 실패 (손상된 JSON) — 파일 변경 없음: {path}",
    "unsupported_version":        "지원하지 않는 문서 version={version} (지원 상한 {supported})",
    "schema_validation_failed":   "문서가 스키마를 위반함 — violations[] 참조 (파일 변경 없음)",
    "schema_load_failed":         "스키마 파일을 로드할 수 없음: {path}",
    "schema_unsupported_keyword": "검증기가 지원하지 않는 스키마 키워드: {keyword}",
    "invalid_date":               "날짜 형식 오류 — YYYY-MM-DD가 아님: {value}",
    "lock_timeout":               "메모리 락 획득 시간 초과 ({timeout}s) — 다른 프로세스가 점유 중: {path}",
    "migration_failed":           "MEMORY.md → MEMORY.json 변환 실패 ({reason}) — 원본 무변경, MEMORY.json 미생성",
    "task_number_regression":     "--set {value}는 현재값 {current}보다 작음 — 채번 역행 거부 (무손실)",
    "invalid_args":               "인자 조합이 올바르지 않음: {detail}",
}

# 락 파라미터 (PLAN §3.2.2)
LOCK_TIMEOUT_SECONDS = 5.0
LOCK_STALE_SECONDS = 60.0

# ─────────────────────────────────────────────────────────────────────────────
# 응답 헬퍼 (state-tool ok/err 동형)
# ─────────────────────────────────────────────────────────────────────────────

def ok(command, **kwargs):
    """성공 응답 — 단일 라인 JSON, exit 0"""
    print(json.dumps({"ok": True, "command": command, **kwargs}, ensure_ascii=False, default=str))


def err(command, code, message=None, exit_code=1, **kwargs):
    """에러 응답 — 단일 라인 JSON, exit {exit_code}
    code는 ERROR_CODES 키 중 하나여야 한다 (SSOT).
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
# 날짜 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def get_kst_date():
    """KST 오늘 날짜 YYYY-MM-DD 반환 (node date.js 폴백 → Python datetime)."""
    date_js = os.path.expanduser("~/.opal/tools/date/date.js")
    try:
        import subprocess
        result = subprocess.run(
            ["node", date_js, "date"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            date_str = result.stdout.strip()
            if re.match(r"\d{4}-\d{2}-\d{2}", date_str):
                return date_str[:10]
    except Exception:
        pass
    # 폴백: Python UTC+9
    kst = timezone(timedelta(hours=9))
    return datetime.now(kst).strftime("%Y-%m-%d")


def _kst_now():
    return datetime.now(timezone(timedelta(hours=9)))


# ─────────────────────────────────────────────────────────────────────────────
# 스키마 검증기 (표준 라이브러리 전용 — PLAN §3.1.3)
# ─────────────────────────────────────────────────────────────────────────────

class SchemaUnsupportedKeyword(Exception):
    """스키마가 검증기 미지원 키워드를 쓰면 무성 통과 대신 실패시킨다."""


# 실제로 검증에 쓰는 키워드 부분집합
_VALIDATION_KEYWORDS = {
    "type", "required", "properties", "additionalProperties", "items", "$ref",
    "enum", "const", "minLength", "maxLength", "pattern", "minimum",
}
# 검증 의미가 없는 주석/구조 키워드 — 무시해도 무성 통과가 아니다
_ANNOTATION_KEYWORDS = {
    "$schema", "$id", "$defs", "title", "description", "default", "examples",
    "x-constants", "x-advisory",
}

_JSON_TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "boolean": bool,
    "integer": int,
    "number": (int, float),
}


def _type_matches(instance, type_name):
    expected = _JSON_TYPES.get(type_name)
    if expected is None:
        raise SchemaUnsupportedKeyword("type:%s" % type_name)
    if type_name in ("integer", "number") and isinstance(instance, bool):
        return False
    return isinstance(instance, expected)


def _resolve_ref(ref, root):
    prefix = "#/$defs/"
    if not ref.startswith(prefix):
        raise SchemaUnsupportedKeyword("$ref:%s" % ref)
    name = ref[len(prefix):]
    try:
        return root["$defs"][name]
    except (KeyError, TypeError):
        raise SchemaUnsupportedKeyword("$ref:%s" % ref)


def _child_path(path, key):
    return "%s.%s" % (path, key) if path else str(key)


def _validate_node(instance, schema, path, root, out):
    for keyword in schema:
        if keyword in _VALIDATION_KEYWORDS or keyword in _ANNOTATION_KEYWORDS:
            continue
        raise SchemaUnsupportedKeyword("%s:%s" % (path or "$", keyword))

    if "$ref" in schema:
        _validate_node(instance, _resolve_ref(schema["$ref"], root), path, root, out)
        return

    if "type" in schema and not _type_matches(instance, schema["type"]):
        out.append({"path": path, "keyword": "type",
                    "expected": schema["type"], "actual": type(instance).__name__})
        return

    if "const" in schema and instance != schema["const"]:
        out.append({"path": path, "keyword": "const",
                    "expected": schema["const"], "actual": instance})
    if "enum" in schema and instance not in schema["enum"]:
        out.append({"path": path, "keyword": "enum",
                    "expected": list(schema["enum"]), "actual": instance})

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            out.append({"path": path, "keyword": "minLength",
                        "expected": schema["minLength"], "actual": len(instance)})
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            out.append({"path": path, "keyword": "maxLength",
                        "expected": schema["maxLength"], "actual": len(instance)})
        if "pattern" in schema and re.match(schema["pattern"], instance) is None:
            out.append({"path": path, "keyword": "pattern",
                        "expected": schema["pattern"], "actual": instance})

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            out.append({"path": path, "keyword": "minimum",
                        "expected": schema["minimum"], "actual": instance})

    if isinstance(instance, dict):
        for required in schema.get("required", []):
            if required not in instance:
                out.append({"path": _child_path(path, required), "keyword": "required",
                            "expected": required, "actual": None})
        properties = schema.get("properties", {})
        if "additionalProperties" in schema:
            if schema["additionalProperties"] is not False:
                raise SchemaUnsupportedKeyword("%s:additionalProperties" % (path or "$"))
            for key in instance:
                if key not in properties:
                    out.append({"path": _child_path(path, key), "keyword": "additionalProperties",
                                "expected": sorted(properties), "actual": key})
        for key, subschema in properties.items():
            if key in instance:
                _validate_node(instance[key], subschema, _child_path(path, key), root, out)

    if isinstance(instance, list) and "items" in schema:
        for i, item in enumerate(instance):
            _validate_node(item, schema["items"], "%s[%d]" % (path, i), root, out)


def validate_document(doc, schema=None):
    """스키마 위반 목록을 반환한다(빈 리스트 = 통과). 부작용 없음.
    항목 형식: {"path": "memories[2].summary", "keyword": "maxLength",
                "expected": 80, "actual": 85}
    미지원 키워드가 스키마에 있으면 SchemaUnsupportedKeyword를 올린다(무성 통과 차단).
    """
    root = SCHEMA if schema is None else schema
    violations = []
    _validate_node(doc, root, "", root, violations)
    return violations


# ─────────────────────────────────────────────────────────────────────────────
# 원자적 쓰기 · 파일 락 (PLAN §3.2.2 — H-2, H-7, H-8)
# ─────────────────────────────────────────────────────────────────────────────

def atomic_write_json(json_path, doc):
    """tmp(같은 디렉토리) → fsync → os.replace 원자적 교체.
    실패 시 tmp를 정리하고 예외를 전파한다 — 원본 불변 [H-8].
    """
    json_path = pathlib.Path(json_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = json_path.parent / ("%s.tmp.%d" % (json_path.name, os.getpid()))
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(str(tmp_path), str(json_path))
    except Exception:
        try:
            tmp_path.unlink()
        except OSError:
            pass
        raise


def _lock_path(json_path):
    return pathlib.Path(str(json_path) + ".lock")


@contextlib.contextmanager
def memory_lock(json_path, command):
    """`<MEMORY.json>.lock` 배타 클레임 (O_CREAT|O_EXCL).
    - 획득 실패 시 재시도, LOCK_TIMEOUT_SECONDS 초과 → lock_timeout
    - 락 파일 mtime이 LOCK_STALE_SECONDS 초과면 stale로 간주하고 제거 후 재클레임
    - finally에서 반드시 unlink [H-2, H-7]
    """
    lock_file = _lock_path(json_path)
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS
    interval = 0.01
    fd = None
    while True:
        try:
            fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            break
        except FileExistsError:
            try:
                age = time.time() - lock_file.stat().st_mtime
            except OSError:
                age = 0.0
            if age > LOCK_STALE_SECONDS:
                try:
                    lock_file.unlink()
                except OSError:
                    pass
                continue
            if time.monotonic() >= deadline:
                err(command, "lock_timeout", timeout=LOCK_TIMEOUT_SECONDS, path=str(lock_file))
            time.sleep(interval)
            interval = min(interval * 2, 0.1)
    try:
        os.write(fd, str(os.getpid()).encode("utf-8"))
        os.close(fd)
        fd = None
        yield
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        try:
            lock_file.unlink()
        except OSError:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# 문서 로더 (PLAN §3.2.2 D-2 — 단일 진입점, JSON 전용)
# ─────────────────────────────────────────────────────────────────────────────

def load_document(json_path, command, *, allow_migration=True, already_locked=False):
    """MEMORY.json 단일 진입 로더. 반환: doc(dict).
    1) json 존재            → read → invalid_json / unsupported_version / schema_validation_failed 검사 후 반환
    2) json 부재 + md 존재  → lazy 변환(§3.4.4) 후 반환. `migration` 리포트는 `_LAST_MIGRATION_REPORT`에
                              담아 호출자(각 cmd_*)가 응답에 첨부하게 한다.
    3) 둘 다 부재           → memory_json_not_found

    `already_locked`: 호출자가 이미 `memory_lock(json_path, command)` 안에서 부르는 경우(append/update/
    promote/prune/delete) True — 동일 락 파일을 재진입하면 자기-교착이 나므로 락을 다시 잡지 않는다
    (§3.4.5 "단일 기전" — 이미 보유한 락이 마이그레이션까지 덮는다).
    False(기본, show/review처럼 락 없이 부르는 read-only 경로)면 double-checked locking을 스스로 수행한다:
    락 밖에서 1차 확인(위에서 이미 함) → 락 획득 → 락 안에서 재확인 → 그래도 없을 때만 변환.
    실패 시 err()가 exit(1)로 종료한다(호출자는 반환값을 그대로 신뢰 가능).
    """
    json_path = pathlib.Path(json_path)
    md_path = json_path.with_suffix(".md")

    if not json_path.exists() and allow_migration and md_path.exists():
        if already_locked:
            if not json_path.exists():
                report = _migrate_md_to_json(md_path, json_path, command)
                _LAST_MIGRATION_REPORT["report"] = report
        else:
            with memory_lock(json_path, command):
                if not json_path.exists():
                    report = _migrate_md_to_json(md_path, json_path, command)
                    _LAST_MIGRATION_REPORT["report"] = report

    if not json_path.exists():
        err(command, "memory_json_not_found", path=str(json_path))

    try:
        text = json_path.read_text(encoding="utf-8")
    except OSError:
        err(command, "memory_json_not_found", path=str(json_path))

    try:
        doc = json.loads(text)
    except json.JSONDecodeError:
        err(command, "invalid_json", path=str(json_path))

    version = doc.get("version") if isinstance(doc, dict) else None
    if isinstance(version, int) and version > CURRENT_VERSION:
        err(command, "unsupported_version", version=version, supported=CURRENT_VERSION)

    violations = validate_document(doc)
    if violations:
        err(command, "schema_validation_failed", violations=violations)

    return doc


# 직전 load_document() 호출에서 수행된 마이그레이션 리포트(있으면). 호출자가 응답에 "migration" 키로 첨부.
_LAST_MIGRATION_REPORT = {"report": None}


def _pop_migration_report():
    report = _LAST_MIGRATION_REPORT["report"]
    _LAST_MIGRATION_REPORT["report"] = None
    return report


# ─────────────────────────────────────────────────────────────────────────────
# md → json 변환 엔진 (PLAN §3.4 — lazy 자동 마이그레이션)
# ─────────────────────────────────────────────────────────────────────────────

_TABLE_ROW_RE = re.compile(r"^\|.*\|$")


def _split_cells(line):
    inner = line.strip()[1:-1]
    return [c.strip() for c in inner.split("|")]


def _is_separator_cells(cells):
    return all(re.fullmatch(r":?-+:?", c.replace(" ", "")) for c in cells if c.strip())


def _locate_region(text, tag_start, tag_end, heading_keyword):
    """cascade 1·2단계 — (region_text, source) 반환. 둘 다 실패하면 (None, "whole")."""
    if tag_start in text and tag_end in text:
        start_idx = text.find(tag_start)
        end_idx = text.find(tag_end)
        if end_idx > start_idx:
            return text[start_idx + len(tag_start):end_idx], "tag"

    lines = text.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("## ") and heading_keyword in stripped:
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith("## "):
                j += 1
            return "\n".join(lines[i + 1:j]), "heading"

    return None, "whole"


def _first_table_block(text):
    """text 안에서 첫 표 블록을 찾아 (header_cells, data_rows) 반환. 없으면 None.
    data_rows는 헤더·구분선을 제외한 원본 셀 리스트들이다(구조적 정의 — candidate_lines).
    """
    lines = text.splitlines()
    n = len(lines)
    i = 0
    while i < n:
        stripped = lines[i].strip()
        if _TABLE_ROW_RE.match(stripped):
            header_cells = _split_cells(stripped)
            j = i + 1
            if j < n:
                cand = lines[j].strip()
                if _TABLE_ROW_RE.match(cand) and _is_separator_cells(_split_cells(cand)):
                    j += 1
            data_rows = []
            while j < n and _TABLE_ROW_RE.match(lines[j].strip()):
                data_rows.append(_split_cells(lines[j].strip()))
                j += 1
            return header_cells, data_rows
        i += 1
    return None


# ── 인덱스(메모리) 헤더 프로파일 ──
def _index_profile(header_cells):
    joined = " ".join(header_cells)
    if len(header_cells) >= 6 and "제목" in header_cells[0]:
        return "new6"
    if len(header_cells) >= 5 and ("등록일시" in joined or "등록일자" in joined) and "카테고리" in joined:
        return "old5"
    return None


def _cap_summary(text, flagged):
    raw = f"[REVIEW] {text}".strip() if flagged else text.strip()
    if len(raw) <= SUMMARY_MAX_LENGTH:
        return raw
    ellipsis = "…"
    limit = SUMMARY_MAX_LENGTH - len(ellipsis)
    return raw[:limit] + ellipsis


def _convert_index_rows(header_cells, data_rows):
    """(rows, unmapped_statuses, review_flagged) 반환. 프로파일 미인식이면 위치 폴백."""
    profile = _index_profile(header_cells)
    if profile is None:
        profile = "new6" if len(header_cells) >= 6 else "old5"

    rows = []
    unmapped = []
    review_flagged = 0

    for cells in data_rows:
        if profile == "new6":
            padded = cells + [""] * max(0, 6 - len(cells))
            title, date, rtype, status, file_field, summary = padded[:6]
            file_field = file_field.strip().strip("`").strip()
            date = date.strip()[:10]
            flagged = False
            if status not in VALID_STATUSES:
                unmapped.append({"title": title or "(제목 없음)", "raw": status})
                status = "active"
                flagged = True
            if rtype not in VALID_TYPES:
                rtype = "project"
            if not title.strip():
                title = _extract_title(summary) or "제목 없음"
                flagged = True
            if not re.match(FILE_PATTERN, file_field):
                file_field = _title_to_filename(title)
                flagged = True
            summary = _cap_summary(summary, flagged)
            if flagged:
                review_flagged += 1
            rows.append({"title": title.strip(), "date": date, "type": rtype,
                         "status": status, "file": file_field, "summary": summary})
        else:  # old5: 등록일시 | 카테고리 | 상태 | 파일 | 설명
            padded = cells + [""] * max(0, 5 - len(cells))
            date, category, status_raw, file_field, desc = padded[:5]
            date = date.strip()[:10]
            title = _extract_title(desc)
            rtype = _map_category_to_type(category)
            clean_status = re.sub(r"~~(.+?)~~", r"\1", status_raw).strip()
            flagged = False
            if clean_status not in LEGACY_STATUS_MAP:
                unmapped.append({"title": title, "raw": status_raw.strip()})
                status = "active"
                flagged = True
            else:
                status = LEGACY_STATUS_MAP[clean_status]
            file_field = file_field.strip().strip("`").strip()
            if not re.match(FILE_PATTERN, file_field):
                file_field = _title_to_filename(title)
                flagged = True
            summary = _cap_summary(desc, flagged)
            if flagged:
                review_flagged += 1
            rows.append({"title": title, "date": date, "type": rtype,
                         "status": status, "file": file_field, "summary": summary})

    return rows, unmapped, review_flagged


# ── 히스토리 헤더 프로파일 (V-2: 신5컬럼 / 구6컬럼-# / 구6컬럼-등록일자) ──
def _history_profile(header_cells):
    if len(header_cells) >= 5 and "제목" in header_cells[0]:
        return "new5"
    joined = " ".join(header_cells)
    if len(header_cells) >= 6 and header_cells[0].strip() == "#" and "작업" in joined:
        return "old6_hash"
    if len(header_cells) >= 6 and ("등록일자" in joined or "등록일시" in joined) and "작업" in joined \
            and ("시작일시" in joined or "완료일시" in joined):
        return "old6_date"
    return None


def _convert_history_rows(header_cells, data_rows, disable_profiles):
    """(rows_or_None, ) — disable_profiles가 참이면 프로파일·위치 폴백 모두 무력화(빈 리스트 반환, D-3용)."""
    if disable_profiles:
        return []

    profile = _history_profile(header_cells)
    if profile is None:
        profile = "new5" if len(header_cells) >= 5 else None
    if profile is None:
        return []

    rows = []
    for cells in data_rows:
        if profile == "new5":
            padded = cells + [""] * max(0, 5 - len(cells))
            title, date, stage, path, result = padded[:5]
            rows.append({"title": title.strip() or "이전 태스크", "date": date.strip()[:10],
                         "stage": stage.strip(), "path": path.strip(), "result": result.strip()})
        else:  # old6_hash / old6_date — # 또는 등록일자|작업|단계|경로|시작일시|완료일시
            padded = cells + [""] * max(0, 6 - len(cells))
            first, task, stage, path, started, ended = padded[:6]
            title = task.strip() or "이전 태스크"
            date_src = first if profile == "old6_date" else started
            date = (date_src.strip() or started.strip())[:10]
            ended = ended.strip()
            result = ended if ended and ended != "-" else stage.strip()
            rows.append({"title": title, "date": date, "stage": stage.strip(),
                         "path": path.strip(), "result": result})
    return rows


def _resolve_last_task_number(md_text, project_root):
    m = re.search(r"last_task_number:\s*(\d+)", md_text)
    if m:
        return int(m.group(1)), "header"
    tasks_dir = pathlib.Path(project_root) / "tasks"
    max_n = None
    if tasks_dir.is_dir():
        for child in tasks_dir.iterdir():
            cm = re.match(r"^(\d{3})-", child.name)
            if cm:
                n = int(cm.group(1))
                if max_n is None or n > max_n:
                    max_n = n
    if max_n is not None:
        return max_n, "tasks_scan"
    return 0, "default"


def _migrate_md_to_json(md_path, json_path, command):
    """PLAN §3.4.4 — [락 보유 상태에서 실행]. 실패 시 err()로 exit(migration_failed, 원본 무변경).
    성공 시 MEMORY.json을 쓰고 원본을 .bak으로 옮긴 뒤 migration 리포트(dict)를 반환한다.
    """
    md_path = pathlib.Path(md_path)
    json_path = pathlib.Path(json_path)
    text = md_path.read_text(encoding="utf-8")
    disable_history_profiles = os.environ.get(_ENV_DISABLE_HISTORY_PROFILES) == "1"

    # 1) 영역 분할(캐스케이드)
    index_region, _ = _locate_region(text, _LEGACY_INDEX_TAG_START, _LEGACY_INDEX_TAG_END, "메모리")
    history_region, _ = _locate_region(text, _LEGACY_HISTORY_TAG_START, _LEGACY_HISTORY_TAG_END, "히스토리")
    index_scope = index_region if index_region is not None else text
    history_scope = history_region if history_region is not None else text

    # 2) 표 블록 탐색 + candidate_lines 회계
    index_block = _first_table_block(index_scope)
    history_block = _first_table_block(history_scope)

    index_header, index_candidates = index_block if index_block else ([], [])
    history_header, history_candidates = history_block if history_block else ([], [])

    empty_source_regions = []

    if len(index_candidates) == 0:
        memories, unmapped_statuses, review_flagged = [], [], 0
        empty_source_regions.append("memories")
    else:
        memories, unmapped_statuses, review_flagged = _convert_index_rows(index_header, index_candidates)
        if len(memories) != len(index_candidates):
            err(command, "migration_failed", reason="row_count_mismatch",
                expected=len(index_candidates), parsed=len(memories))

    if len(history_candidates) == 0:
        history_rows = []
        empty_source_regions.append("history")
    else:
        history_rows = _convert_history_rows(history_header, history_candidates, disable_history_profiles)
        if len(history_rows) != len(history_candidates):
            if len(history_rows) == 0:
                err(command, "migration_failed", reason="row_detection_failed",
                    expected=len(history_candidates), parsed=0)
            err(command, "migration_failed", reason="row_count_mismatch",
                expected=len(history_candidates), parsed=len(history_rows))

    # 3) history FIFO=5 절단 (절단분은 dropped_history에 제목만 기록)
    dropped_history = [r["title"] for r in history_rows[HISTORY_FIFO_LIMIT:]]
    history_rows = _enforce_history_fifo(history_rows)

    # 4) last_task_number 해석 (V-4)
    project_root = md_path.parent.parent
    last_task_number, last_task_number_source = _resolve_last_task_number(text, project_root)

    # 5) doc 조립 + validate_document
    doc = {
        "version": CURRENT_VERSION,
        "last_task_number": last_task_number,
        "memories": memories,
        "history": history_rows,
    }
    violations = validate_document(doc)
    if violations:
        err(command, "migration_failed", reason="schema_validation_failed", violations=violations)

    # 6) atomic_write_json(MEMORY.json) ← json 먼저
    atomic_write_json(json_path, doc)

    # 7) os.replace(MEMORY.md → MEMORY.md.bak) ← 그 다음 백업 (H-12: 선점 시 타임스탬프 suffix)
    backup_path = md_path.parent / (md_path.name + ".bak")
    backup_failed = False
    if backup_path.exists():
        backup_path = md_path.parent / (md_path.name + ".bak." + _kst_now().strftime("%Y%m%d%H%M%S"))
    try:
        os.replace(str(md_path), str(backup_path))
    except OSError:
        backup_failed = True

    return {
        "performed": True,
        "source": str(md_path),
        "backup": str(backup_path) if not backup_failed else None,
        "memories": len(memories),
        "history": len(history_rows),
        "review_flagged": review_flagged,
        "unmapped_statuses": unmapped_statuses,
        "last_task_number": last_task_number,
        "last_task_number_source": last_task_number_source,
        "empty_source_regions": empty_source_regions,
        "dropped_history": dropped_history,
        "backup_failed": backup_failed,
    }


# ─────────────────────────────────────────────────────────────────────────────
# FIFO 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def _enforce_history_fifo(rows):
    """rows = 히스토리 행 리스트(맨 앞=최신). len > HISTORY_FIFO_LIMIT 시 뒤에서 제거.
    결정론: append는 맨 앞 삽입 → 뒤쪽이 오래된 순.
    """
    return rows[:HISTORY_FIFO_LIMIT]


# ─────────────────────────────────────────────────────────────────────────────
# title → 파일 경로 변환 + 경로 보안 가드
# ─────────────────────────────────────────────────────────────────────────────

def _title_to_filename(title):
    """제목 → memory/<slug>.md 파일명 변환.
    특수문자를 제거하고 공백→언더스코어.
    """
    slug = re.sub(r"[^\w가-힣]", "_", title).strip("_")
    slug = re.sub(r"_+", "_", slug)
    return f"memory/{slug}.md"


def _resolve_memory_file(md_path, file_field):
    """MEMORY.md 기준 상대경로 → 절대경로 반환.
    memory/ 디렉토리 외부 탈출 시 None 반환(경로 가드).
    migrate가 생성한 백틱 감싸진 경로(예: `memory/x.md`)를 정규화한다.
    """
    md_dir = pathlib.Path(md_path).parent.resolve()
    # 백틱·공백 strip (migrate 백틱 포맷 대응)
    file_field = file_field.strip().strip("`").strip()
    # 경로 정규화
    try:
        target = (md_dir / file_field).resolve()
    except Exception:
        return None
    # 경로 탈출 가드: memory/ 하위여야 함
    memory_dir = (md_dir / "memory").resolve()
    try:
        target.relative_to(memory_dir)
    except ValueError:
        return None
    return target


def _path_has_traversal(path_str):
    """경로 문자열에 ../ 탈출 패턴이 있으면 True."""
    return ".." in pathlib.Path(path_str).parts or ".." in str(path_str)


# ─────────────────────────────────────────────────────────────────────────────
# 자가검토 헬퍼 (F-010)
# ─────────────────────────────────────────────────────────────────────────────

def build_review_block(doc):
    """자가검토 블록 생성 (PLAN §3.2.2). dict(MEMORY.json 문서)를 받아 read 없이 소비한다.
    x-advisory 위반(title>TITLE_MAX_LENGTH자)을 violations에 추가한다.
    """
    promote_candidates = []
    cleanup_candidates = []
    violations = []

    memories = doc.get("memories", []) if isinstance(doc, dict) else []
    history  = doc.get("history", [])  if isinstance(doc, dict) else []
    today = datetime.now(timezone(timedelta(hours=9))).date()

    for row in memories:
        status  = row.get("status", "")
        title   = row.get("title", "")
        rtype   = row.get("type", "")
        summary = row.get("summary", "")
        date_str = row.get("date", "")

        if status and status not in VALID_STATUSES:
            violations.append({"type": "invalid_status", "title": title, "value": status})
        if rtype and rtype not in VALID_TYPES:
            violations.append({"type": "invalid_type", "title": title, "value": rtype})
        if len(summary) > SUMMARY_MAX_LENGTH:
            violations.append({"type": "summary_too_long", "title": title, "length": len(summary)})
        if len(title) > TITLE_MAX_LENGTH:
            violations.append({"type": "title_too_long", "title": title, "length": len(title)})

        if status == "active":
            is_candidate = False
            if "[REVIEW]" in summary or "[REVIEW]" in title:
                is_candidate = True
            else:
                try:
                    reg_date = datetime.strptime(date_str[:10], "%Y-%m-%d").date()
                    if (today - reg_date).days >= PROMOTE_AGE_DAYS:
                        is_candidate = True
                except (ValueError, TypeError):
                    pass
            if is_candidate:
                promote_candidates.append({"title": title, "type": rtype, "date": date_str})

        if status in ("dead", "superseded"):
            cleanup_candidates.append({"title": title, "status": status})

    history_count = len(history)
    fifo_trimmed = history_count > HISTORY_FIFO_LIMIT

    return {
        "promote_candidates": promote_candidates,
        "cleanup_candidates": cleanup_candidates,
        "history_status": {"fifo_trimmed": fifo_trimmed, "count": history_count},
        "violations": violations,
    }


# ─────────────────────────────────────────────────────────────────────────────
# cmd_init (F-006)
# ─────────────────────────────────────────────────────────────────────────────

def cmd_init(args):
    """MEMORY.json 생성(create-if-absent). 이미 존재 + not --force → already_initialized."""
    json_path = pathlib.Path(args.file)
    with memory_lock(json_path, "init"):
        if json_path.exists():
            if not args.force:
                err("init", "already_initialized")
            # --force: 이미 유효한 JSON이면 재생성 없이 그대로 통과(멱등)
            try:
                doc = json.loads(json_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                err("init", "invalid_json", path=str(json_path))
        else:
            doc = {
                "version": CURRENT_VERSION,
                "last_task_number": 0,
                "memories": [],
                "history": [],
            }
            atomic_write_json(json_path, doc)

    review = build_review_block(doc)
    ok("init", file=str(json_path), review=review)


# ─────────────────────────────────────────────────────────────────────────────
# cmd_append (F-003, F-004)
# ─────────────────────────────────────────────────────────────────────────────

def cmd_append(args):
    """메모리/히스토리 행 추가 (MEMORY.json).
    --kind memory: type/status enum + summary ≤80 검증. 갯수 무제한.
    --kind history: FIFO=5 집행.
    """
    json_path = pathlib.Path(args.file)
    title = (args.title or "").strip()
    if not title:
        err("append", "title_required")

    kind = args.kind
    if kind not in ("memory", "history"):
        err("append", "invalid_kind", kind=kind)

    today = get_kst_date()
    migration = None

    with memory_lock(json_path, "append"):
        doc = load_document(json_path, "append", already_locked=True)
        migration = _pop_migration_report()

        if kind == "memory":
            rtype = (args.type or "").strip()
            if rtype not in VALID_TYPES:
                err("append", "invalid_type", value=rtype)

            status = (args.status or "active").strip()
            if status not in VALID_STATUSES:
                err("append", "invalid_status", value=status)

            summary = (args.summary or "").strip()
            if len(summary) > SUMMARY_MAX_LENGTH:
                err("append", "summary_too_long", length=len(summary))

            file_field = _title_to_filename(title)

            doc["memories"].append({
                "title":   title,
                "date":    today,
                "type":    rtype,
                "status":  status,
                "file":    file_field,
                "summary": summary,
            })

            violations = validate_document(doc)
            if violations:
                err("append", "schema_validation_failed", violations=violations)

            atomic_write_json(json_path, doc)
            active_count = sum(1 for r in doc["memories"] if r.get("status") == "active")

        else:  # kind == "history"
            summary = (args.summary or "").strip()
            stage   = (getattr(args, "stage", None) or "").strip()
            path    = (getattr(args, "path", None) or "").strip()

            new_row = {
                "title":   title,
                "date":    today,
                "stage":   stage,
                "path":    path,
                "result":  summary,
            }
            doc["history"].insert(0, new_row)
            doc["history"] = _enforce_history_fifo(doc["history"])

            violations = validate_document(doc)
            if violations:
                err("append", "schema_validation_failed", violations=violations)

            atomic_write_json(json_path, doc)

    review = build_review_block(doc)
    if kind == "memory":
        ok("append", kind=kind, title=title, active_count=active_count, review=review, migration=migration)
    else:
        ok("append", kind=kind, title=title, history_count=len(doc["history"]), review=review, migration=migration)


# ─────────────────────────────────────────────────────────────────────────────
# cmd_update (F-005, 079: --kind history 정정 분기)
# ─────────────────────────────────────────────────────────────────────────────

_UPDATE_HISTORY_ONLY_ARGS = ("stage", "result", "path")
_UPDATE_MEMORY_ONLY_ARGS = ("status", "summary")
_HISTORY_CORRECTABLE_FIELDS = ("stage", "result", "path")  # argparse dest == historyRow 필드명


def _check_update_kind_args(kind, args):
    """--kind ↔ 필드 인자 조합 사전 검증. 락 획득·파일 접근 이전에 호출한다 (R-4 AC a).
    위반 시 err()가 단일라인 JSON을 출력하고 exit 1로 종료한다.
    """
    if kind not in ("memory", "history"):
        err("update", "invalid_kind", kind=kind)

    if kind == "memory":
        for dest in _UPDATE_HISTORY_ONLY_ARGS:
            if getattr(args, dest, None) is not None:
                err("update", "invalid_args",
                    detail="--stage/--result/--path는 --kind history 전용")
    else:  # kind == "history"
        if getattr(args, "status", None) is not None:
            err("update", "invalid_args",
                detail="--status는 히스토리 행에 없는 필드 — --kind memory 전용")
        if getattr(args, "summary", None) is not None:
            err("update", "invalid_args",
                detail="--summary는 --kind memory 전용 — 히스토리 핵심결과는 --result")

        correction_fields = _HISTORY_CORRECTABLE_FIELDS + ("new_title",)
        if all(getattr(args, dest, None) is None for dest in correction_fields):
            err("update", "invalid_args",
                detail="정정 필드(--stage/--result/--path/--new-title) 중 최소 1개 필요")

        path_value = getattr(args, "path", None)
        if path_value is not None and _path_has_traversal(path_value):
            err("update", "invalid_args",
                detail="--path에 상위 경로 탈출(..) 문자열 금지")


def _apply_history_correction(doc, title, args):
    """히스토리 행 정정 — (target, matched_index, match_count, changed[]) 반환.
    행 추가·삭제 없음. 미지정 필드는 불변. 새 키 삽입 금지.
    """
    rows = doc["history"]
    matches = [i for i, r in enumerate(rows) if r.get("title") == title]
    if not matches:
        err("update", "row_not_found", title=title)
    idx = matches[0]  # 배열 선행 = 가장 최근 append (P-4)
    target = rows[idx]
    changed = []
    if args.new_title is not None:
        new_title = args.new_title.strip()
        if not new_title:
            err("update", "title_required")
        target["title"] = new_title
        changed.append("title")
    for field in _HISTORY_CORRECTABLE_FIELDS:
        value = getattr(args, field, None)
        if value is not None:
            target[field] = value.strip()
            changed.append(field)
    return target, idx, len(matches), changed


def cmd_update(args):
    """메모리 인덱스 행(--kind memory, 기본) 또는 작업 히스토리 행(--kind history) 수정.
    history 분기는 정정 전용 — 행 추가·삭제 없음(행 수 불변, FIFO 미적용).
    dead/superseded 전이 = 행 보존(추적), 로드 제외.
    """
    json_path = pathlib.Path(args.file)
    title = (args.title or "").strip()
    if not title:
        err("update", "title_required")

    kind = getattr(args, "kind", "memory")
    _check_update_kind_args(kind, args)  # 락 밖 사전 게이트 — 위반 시 err()로 종료 (R-4 AC a)

    with memory_lock(json_path, "update"):
        doc = load_document(json_path, "update", already_locked=True)
        migration = _pop_migration_report()

        if kind == "memory":
            target = None
            for row in doc["memories"]:
                if row["title"] == title:
                    target = row
                    break
            if target is None:
                err("update", "row_not_found", title=title)

            if getattr(args, "new_title", None) is not None:
                new_title = args.new_title.strip()
                if not new_title:
                    err("update", "title_required")
                target["title"] = new_title

            if args.status is not None:
                new_status = args.status.strip()
                if new_status not in VALID_STATUSES:
                    err("update", "invalid_status", value=new_status)
                target["status"] = new_status

            if args.summary is not None:
                new_summary = args.summary.strip()
                if len(new_summary) > SUMMARY_MAX_LENGTH:
                    err("update", "summary_too_long", length=len(new_summary))
                target["summary"] = new_summary

            result_kwargs = {"status": target.get("status")}
        else:  # kind == "history"
            target, matched_index, match_count, changed = _apply_history_correction(doc, title, args)
            result_kwargs = {"matched_index": matched_index, "match_count": match_count,
                             "changed": changed, "history_count": len(doc["history"])}

        violations = validate_document(doc)
        if violations:
            err("update", "schema_validation_failed", violations=violations)

        atomic_write_json(json_path, doc)

    review = build_review_block(doc)
    ok("update", kind=kind, title=title, review=review, migration=migration, **result_kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# cmd_promote (F-005)
# ─────────────────────────────────────────────────────────────────────────────

def cmd_promote(args):
    """메모리 → 영구 거처 졸업 (MEMORY.json).
    --to docs|brain --ref <위치> 필수.
    --ref 미지정 → promote_ref_missing (무손실, H-1).
    정상 시 인덱스 행 + memory/<file>.md 원자적 삭제 + provenance 기록.
    brain 경로: brain-tool 재사용 전제 — 자체 brain 쓰기 없음(H-9).
    """
    json_path = pathlib.Path(args.file)
    to_target = (getattr(args, "to", None) or "").strip()
    if to_target not in ("docs", "brain"):
        err("promote", "invalid_promote_target", value=to_target)

    ref = (getattr(args, "ref", None) or "").strip()
    if not ref:
        err("promote", "promote_ref_missing")

    title = (args.title or "").strip()
    if not title:
        err("promote", "title_required")

    if _path_has_traversal(title):
        err("promote", "row_not_found", title=title)

    with memory_lock(json_path, "promote"):
        doc = load_document(json_path, "promote", already_locked=True)
        migration = _pop_migration_report()

        target_idx = None
        for i, row in enumerate(doc["memories"]):
            if row["title"] == title:
                target_idx = i
                break
        if target_idx is None:
            err("promote", "row_not_found", title=title)

        row = doc["memories"][target_idx]
        file_field = row.get("file", "")

        mem_file = _resolve_memory_file(str(json_path), file_field)
        if mem_file is None:
            err("promote", "memory_file_not_found", path=file_field)
        if not mem_file.exists():
            err("promote", "memory_file_not_found", path=str(mem_file))

        today = get_kst_date()

        del doc["memories"][target_idx]

        violations = validate_document(doc)
        if violations:
            err("promote", "schema_validation_failed", violations=violations)

        atomic_write_json(json_path, doc)

        mem_file.unlink()

        provenance_log = json_path.parent / ".memory_provenance.log"
        provenance_entry = (
            f"{today} | promote | title={row['title']} | "
            f"type={row.get('type', '')} | to={to_target} | ref={ref} | "
            f"file={file_field}\n"
        )
        try:
            with provenance_log.open("a", encoding="utf-8") as f:
                f.write(provenance_entry)
        except Exception:
            pass  # provenance 기록 실패는 비치명적

    review = build_review_block(doc)
    ok(
        "promote",
        title=title,
        to=to_target,
        ref=ref,
        file_deleted=True,
        row_removed=True,
        provenance_logged=True,
        review=review,
        migration=migration,
    )


# ─────────────────────────────────────────────────────────────────────────────
# cmd_prune (F-004)
# ─────────────────────────────────────────────────────────────────────────────

def cmd_prune(args):
    """히스토리 FIFO=5 결정론 정리 (MEMORY.json). 이미 ≤5면 no-op."""
    json_path = pathlib.Path(args.file)
    with memory_lock(json_path, "prune"):
        doc = load_document(json_path, "prune", already_locked=True)
        migration = _pop_migration_report()

        before_count = len(doc["history"])
        doc["history"] = _enforce_history_fifo(doc["history"])
        after_count = len(doc["history"])

        if before_count != after_count:
            violations = validate_document(doc)
            if violations:
                err("prune", "schema_validation_failed", violations=violations)
            atomic_write_json(json_path, doc)

    review = build_review_block(doc)
    ok("prune", before=before_count, after=after_count, trimmed=(before_count - after_count),
       review=review, migration=migration)


# ─────────────────────────────────────────────────────────────────────────────
# 마이그레이션 변환 헬퍼 — _migrate_md_to_json이 재사용 (제목 추출 + 카테고리 매핑)
# ─────────────────────────────────────────────────────────────────────────────

def _extract_title(text):
    """설명/작업 텍스트에서 제목 추출: 첫 문장 또는 첫 30자."""
    text = text.strip()
    # [REVIEW] 접두사 제거
    text = re.sub(r"^\[REVIEW\]\s*", "", text)
    # 첫 문장: 마침표, 느낌표, 쉼표, 개행 전까지
    m = re.match(r"^([^.。!,，\n]{1,30})", text)
    if m:
        title = m.group(1).strip()
        if title:
            return title
    # 폴백: 첫 30자
    return text[:30].strip() if text else "제목 없음"


def _map_category_to_type(category):
    """구포맷 카테고리 → 신 유형 enum 매핑."""
    mapping = {
        "feedback":     "feedback",
        "architecture": "architecture",
        "issues":       "issues",
        "preferences":  "preferences",
        "task":         "task",
        "project":      "project",
    }
    return mapping.get(category.lower(), "project")


# ─────────────────────────────────────────────────────────────────────────────
# cmd_show (F-002)
# ─────────────────────────────────────────────────────────────────────────────

_BRIEF_MEMORY_FIELDS = ("title", "date", "type", "file", "summary")


def cmd_show(args):
    """인덱스/히스토리 현황 출력 (MEMORY.json, read-only).
    응답 최상위 키(index_rows/history_rows/active_count/total_count/history_count)는
    improve_tool.py:311 의존 하위호환으로 개명 없이 보존한다(H-4).
    --brief 계약은 PLAN §3.3.2 참조.
    """
    json_path = pathlib.Path(args.file)
    doc = load_document(json_path, "show")
    migration = _pop_migration_report()

    index_rows = doc.get("memories", [])
    history_rows = doc.get("history", [])
    active_count = sum(1 for r in index_rows if r.get("status") == "active")
    total_count = len(index_rows)
    history_count = len(history_rows)

    brief = bool(getattr(args, "brief", False))
    history_arg = getattr(args, "history", None)

    extra = {}
    if brief:
        index_rows = [
            {field: r.get(field) for field in _BRIEF_MEMORY_FIELDS}
            for r in index_rows if r.get("status") == "active"
        ]
        index_rows.sort(key=lambda r: r.get("date", ""), reverse=True)
        extra["brief"] = True

    if brief or history_arg is not None:
        limit = history_arg if history_arg is not None else 3
        sorted_history = sorted(history_rows, key=lambda r: r.get("date", ""), reverse=True)
        history_rows = sorted_history[:limit] if limit >= 0 else sorted_history
        extra["history_truncated"] = len(history_rows) < len(sorted_history)

    if not brief:
        extra["version"] = doc.get("version")
        extra["last_task_number"] = doc.get("last_task_number")

    ok(
        "show",
        file=str(json_path),
        index_rows=index_rows,
        history_rows=history_rows,
        active_count=active_count,
        total_count=total_count,
        history_count=history_count,
        migration=migration,
        **extra,
    )


# ─────────────────────────────────────────────────────────────────────────────
# cmd_delete (9번째 서브명령)
# ─────────────────────────────────────────────────────────────────────────────

def cmd_delete(args):
    """dead/superseded 상태 행 물리 제거 (MEMORY.json).
    --title로 행 식별. 행 없으면 row_not_found.
    무손실 가드: active/promoted 행은 delete_requires_dead_or_superseded 반환 + 행 불변 [MUST — 무변경].
    --with-file 시 memory/<file>.md도 삭제(_resolve_memory_file() 경로 화이트리스트 재사용).
    성공 시 review 블록 첨부.
    """
    json_path = pathlib.Path(args.file)
    title = (args.title or "").strip()
    if not title:
        err("delete", "title_required")

    with memory_lock(json_path, "delete"):
        doc = load_document(json_path, "delete", already_locked=True)
        migration = _pop_migration_report()

        target_idx = None
        for i, row in enumerate(doc["memories"]):
            if row["title"] == title:
                target_idx = i
                break
        if target_idx is None:
            err("delete", "row_not_found", title=title)

        row = doc["memories"][target_idx]
        status = row.get("status", "")

        # 무손실 가드: active/promoted 행은 삭제 거부 [MUST — 무변경]
        if status not in ("dead", "superseded"):
            err("delete", "delete_requires_dead_or_superseded")

        del doc["memories"][target_idx]

        violations = validate_document(doc)
        if violations:
            err("delete", "schema_validation_failed", violations=violations)

        atomic_write_json(json_path, doc)

        file_deleted = False
        if getattr(args, "with_file", False):
            file_field = row.get("file", "")
            if file_field:
                mem_file = _resolve_memory_file(str(json_path), file_field)
                if mem_file is not None and mem_file.exists():
                    mem_file.unlink()
                    file_deleted = True

    review = build_review_block(doc)
    ok("delete", title=title, row_removed=True, file_deleted=file_deleted, review=review, migration=migration)


# ─────────────────────────────────────────────────────────────────────────────
# cmd_review (F-010)
# ─────────────────────────────────────────────────────────────────────────────

def cmd_review(args):
    """자가검토 단독 health 명령 (MEMORY.json, read-only): build_review_block 결과를 ok(...)로 반환."""
    json_path = pathlib.Path(args.file)
    doc = load_document(json_path, "review")
    migration = _pop_migration_report()
    review = build_review_block(doc)
    ok(
        "review",
        file=str(json_path),
        migration=migration,
        **review,
    )


# ─────────────────────────────────────────────────────────────────────────────
# cmd_task_number (F-005 D-1) — last_task_number 조회·원자적 채번
# ─────────────────────────────────────────────────────────────────────────────

def cmd_task_number(args):
    """`task-number` 서브명령 (PLAN §3.5.2).
    인자 없음: 현재값 반환(파일 무변경). --bump: 원자적 +1. --set N: 복구용(역행 거부).
    --bump/--set 동시 지정은 invalid_args.
    """
    json_path = pathlib.Path(args.file)
    bump = bool(getattr(args, "bump", False))
    set_value = getattr(args, "set_value", None)

    if bump and set_value is not None:
        err("task-number", "invalid_args", detail="--bump와 --set은 동시에 지정할 수 없음")

    if not bump and set_value is None:
        # 읽기 전용 — 락 없이 조회, 파일 무변경
        doc = load_document(json_path, "task-number")
        ok("task-number", last_task_number=doc.get("last_task_number"))
        return

    with memory_lock(json_path, "task-number"):
        doc = load_document(json_path, "task-number", already_locked=True)
        migration = _pop_migration_report()
        current = doc.get("last_task_number", 0)

        if bump:
            new_value = current + 1
            doc["last_task_number"] = new_value
            violations = validate_document(doc)
            if violations:
                err("task-number", "schema_validation_failed", violations=violations)
            atomic_write_json(json_path, doc)
            review = build_review_block(doc)
            ok("task-number", last_task_number=new_value, previous=current,
               bumped=True, review=review, migration=migration)
        else:  # --set N
            if set_value < current:
                err("task-number", "task_number_regression", value=set_value, current=current)
            doc["last_task_number"] = set_value
            violations = validate_document(doc)
            if violations:
                err("task-number", "schema_validation_failed", violations=violations)
            atomic_write_json(json_path, doc)
            review = build_review_block(doc)
            ok("task-number", last_task_number=set_value, previous=current,
               set=True, review=review, migration=migration)


# ─────────────────────────────────────────────────────────────────────────────
# argparse main (state-tool 하단 main 동형)
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="memory_tool",
        description="OPAL memory-tool — 메모리 인덱스·히스토리 결정론적 집행 CLI"
    )
    sub = parser.add_subparsers(dest="command", help="서브명령")
    sub.required = True

    # ── init ──
    p_init = sub.add_parser("init", help="MEMORY.json 생성 (create-if-absent)")
    p_init.add_argument("--file", required=True, help="MEMORY.json 경로")
    p_init.add_argument("--force", action="store_true", help="이미 존재해도 already_initialized 에러 없이 통과(유효 JSON 검증만, 재생성 없음)")
    p_init.set_defaults(func=cmd_init)

    # ── append ──
    p_append = sub.add_parser("append", help="메모리/히스토리 행 추가")
    p_append.add_argument("--file", required=True, help="MEMORY.json 경로")
    p_append.add_argument("--kind", required=True, choices=["memory", "history"],
                          help="memory 또는 history")
    p_append.add_argument("--title", required=True, help="제목(필수 비공백)")
    p_append.add_argument("--type", help="유형 enum (memory 전용)")
    p_append.add_argument("--status", default="active", help="상태 (memory 전용, default: active)")
    p_append.add_argument("--summary", default="", help="요약/핵심결과 (≤80자)")
    p_append.add_argument("--stage", default="", help="단계 (history 전용)")
    p_append.add_argument("--path", default="", help="경로 (history 전용)")
    p_append.set_defaults(func=cmd_append)

    # ── update ──
    p_update = sub.add_parser("update", help="메모리 상태/요약 수정")
    p_update.add_argument("--file", required=True, help="MEMORY.json 경로")
    p_update.add_argument("--title", required=True, help="대상 행 제목")
    p_update.add_argument("--kind", default="memory", metavar="{memory,history}",
                          help="정정 대상 — memory(기본: 메모리 인덱스 행) | history(작업 히스토리 행)")
    p_update.add_argument("--status", default=None, help="새 상태값")
    p_update.add_argument("--summary", default=None, help="새 요약 (≤80자)")
    p_update.add_argument("--new-title", default=None, dest="new_title", help="새 제목 (제목 변경 시 사용)")
    p_update.add_argument("--stage", default=None, help="새 단계 (history 전용)")
    p_update.add_argument("--result", default=None, help="새 핵심결과 (history 전용)")
    p_update.add_argument("--path", default=None, help="새 tasks/<폴더>/ 경로 (history 전용)")
    p_update.set_defaults(func=cmd_update)

    # ── promote ──
    p_promote = sub.add_parser("promote", help="메모리 → 영구 거처 졸업")
    p_promote.add_argument("--file", required=True, help="MEMORY.json 경로")
    p_promote.add_argument("--title", required=True, help="대상 행 제목")
    p_promote.add_argument("--to", default=None, choices=["docs", "brain"],
                           help="졸업지: docs 또는 brain")
    p_promote.add_argument("--ref", default=None,
                           help="영구 거처 위치 (예: AGENT.md#금지사항)")
    p_promote.add_argument("--brain-dir", default=None,
                           help="brain 디렉토리 경로 (테스트용 — 실제 brain 쓰기 없음)")
    p_promote.set_defaults(func=cmd_promote)

    # ── prune ──
    p_prune = sub.add_parser("prune", help="히스토리 FIFO=5 결정론 정리")
    p_prune.add_argument("--file", required=True, help="MEMORY.json 경로")
    p_prune.set_defaults(func=cmd_prune)

    # ── show ──
    p_show = sub.add_parser("show", help="인덱스/히스토리 현황 출력 (read-only)")
    p_show.add_argument("--file", required=True, help="MEMORY.json 경로")
    p_show.add_argument("--brief", action="store_true",
                        help="active 메모리 5필드 + 히스토리 요약(PLAN §3.3.2)")
    p_show.add_argument("--history", type=int, default=None, dest="history",
                        help="히스토리 반환 건수 재정의 (brief 기본 3)")
    p_show.set_defaults(func=cmd_show)

    # ── review ──
    p_review = sub.add_parser("review", help="자가검토 단독 health 명령")
    p_review.add_argument("--file", required=True, help="MEMORY.json 경로")
    p_review.set_defaults(func=cmd_review)

    # ── delete ──
    p_delete = sub.add_parser("delete", help="dead/superseded 행 물리 제거 (무손실 가드)")
    p_delete.add_argument("--file", required=True, help="MEMORY.json 경로")
    p_delete.add_argument("--title", required=True, help="삭제할 행 제목")
    p_delete.add_argument("--with-file", action="store_true", dest="with_file",
                          help="memory/<file>.md도 함께 삭제")
    p_delete.set_defaults(func=cmd_delete)

    # ── task-number ──
    p_task_number = sub.add_parser("task-number", help="last_task_number 조회·원자적 채번(D-1)")
    p_task_number.add_argument("--file", required=True, help="MEMORY.json 경로")
    p_task_number.add_argument("--bump", action="store_true", help="원자적으로 +1 증가")
    p_task_number.add_argument("--set", default=None, dest="set_value", type=int,
                               help="복구·보정용 — 역행(현재값 미만)은 거부")
    p_task_number.set_defaults(func=cmd_task_number)

    args = parser.parse_args()
    if SCHEMA is None:
        err(args.command, "schema_load_failed", path=str(SCHEMA_PATH))
    args.func(args)


if __name__ == "__main__":
    main()
