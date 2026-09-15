"""
@header {
  "module": "config",
  "layer": "config",
  "domain": "console",
  "description": "~/.opal/console.config.json 로드 및 기본값 추론. scan_roots/scan_depth/exclude/prewarm_projects 관리. prewarm_projects는 기동 선프라임 대상 프로젝트 절대경로 목록 — _coerce_str_list()로 비-list 값을 안전하게 []로 폴백한다. save_config — 원자적 쓰기(_atomic_write_json: temp write + os.replace) + _WRITE_LOCK(threading.Lock)으로 read-modify-write 사이클 직렬화. 쓰기 대상은 routers/config.py의 POST /api/config/prewarm이 검증한 prewarm_projects 갱신뿐이다. load_quiet_hours — 진행 통계 야간 제외 구간(집계 기준 17)을 OPAL setting 2층 머지로 로드한다. 전역 ~/.opal/setting.json의 quietHours 위에 {프로젝트}/.opal/setting.local.json의 quietHours를 하위 키 단위로 덮어쓰며(로컬 우선), 어느 층에도 없으면 DEFAULT_QUIET_HOURS(enabled true·00:00~09:00·timeZone Asia/Seoul)다. enabled != true거나 start == end면 None(보정 끔). 반환값은 QuietHours(tuple 서브클래스) — 튜플 값 자체는 (start_minute, end_minute) 2-tuple뿐이고 time_zone은 튜플 성분이 아니라 부착 속성(.time_zone)이다. __eq__·__hash__는 오버라이드하지 않고 tuple 상속 구현 그대로 쓴다 — QuietHours(0,540,\"UTC\") == (0,540)이 자연히 참이고 hash도 일치해(dict 키·set 원소로 안전) 기존 테스트(TestLoadQuietHours)의 2-tuple 비교와 완전히 호환된다. timeZone도 같은 2층 머지의 하위 키이며, 무효 IANA 이름은 예외 없이 Asia/Seoul로 폴백하고 설정 파일을 다시 쓰지 않는다(CONTRACT.md §2.8·§3.5). QuietHours는 config·라우터 계층에서만 흐른다 — 라우터가 stats.py에는 (시작 분, 끝 분)으로 좁혀 인자 주입한다(stats.py는 설정을 읽지 않는다, §2.8.1 B-1~B-3). quiet_hours_token은 캐시 키 서명 — isinstance(x, QuietHours)로 분기해 QuietHours 입력은 \"start-end@time_zone\", 평범한 2-tuple 레거시 입력은 \"start-end\", None은 \"off\". timeZone만 다른 두 설정은 반드시 다른 토큰을 만든다(MV-26). load_owner_name — 화면에 쓸 사용자 호칭의 단일 로더다. 원천은 ~/.opal/identity.md frontmatter의 owner_name(전역 1개, 프로젝트별 분기 없음)이며 파일 부재·frontmatter 부재·키 부재·값 공란·읽기 실패 전건을 DEFAULT_OWNER_NAME(\"사용자\")로 폴백하고 예외를 밖으로 던지지 않는다. 표준 라이브러리 정규식만 쓰며 state-tool을 import하지 않는다(콘솔이 도구에 의존하지 않는다). 호칭은 라우터 층에서 붙으며 stats.py는 이 값을 모른다.",
  "exports": ["load_config", "ConsoleConfig", "save_config", "load_quiet_hours", "quiet_hours_token", "QuietHours", "load_owner_name"],
  "depends": [],
  "task": "061"
}
"""
from __future__ import annotations

import json
import os
import re
import threading
from pathlib import Path
from dataclasses import dataclass, field
from zoneinfo import ZoneInfo


CONFIG_PATH = Path.home() / ".opal" / "console.config.json"

DEFAULT_SCAN_ROOTS = [str(Path.home() / "workspace")]
DEFAULT_SCAN_DEPTH = 2
DEFAULT_EXCLUDE = ["node_modules", ".git", ".venv", "__pycache__", ".DS_Store"]

# ── OPAL setting 2층 (집계 기준 17) ───────────────────────────────────────────
# 부트스트랩과 **같은** 2층 머지를 쓴다 — 전역 `~/.opal/setting.json` 위에 프로젝트
# `{프로젝트}/.opal/setting.local.json`을 덮어쓴다(로컬 우선, 로컬에 없으면 전역).
# `models`·`shardPolicy`가 선례이며 `quietHours`도 같은 자리에 산다.
OPAL_SETTING_PATH = Path.home() / ".opal" / "setting.json"
PROJECT_SETTING_RELPATH = os.path.join(".opal", "setting.local.json")

QUIET_HOURS_KEY = "quietHours"

# 캡틴 확정 2026-08-26 — 기본은 **켬**, 제외 구간은 `00:00~09:00`이다.
# 설정 파일에 키가 아예 없는 기존 설치에서도 이 기본이 적용된다.
# timeZone(집계 기준 17 확장, CONTRACT.md §2.8·§3.5) — 미설정 시 기존 동작과
# 동일한 `Asia/Seoul`을 적용한다. 하위 키 1개 추가이며 2층 머지 구조는 그대로다.
DEFAULT_QUIET_HOURS = {
    "enabled": True,
    "start": "00:00",
    "end": "09:00",
    "timeZone": "Asia/Seoul",
}

MINUTES_PER_DAY = 24 * 60

# ── 사용자 호칭 원천 ──────────────────────────────────────────────────────────
# 호칭의 SSOT는 `~/.opal/identity.md` frontmatter의 `owner_name`이다. 콘솔은 여러
# 프로젝트를 한 화면에서 보지만 identity.md는 **전역 1개**라 프로젝트별 분기가 없다.
# 화면에 박아 둔 특정 호칭은 다른 사용자에게 남의 호칭으로 보이므로 읽어서 쓴다.
IDENTITY_PATH = Path.home() / ".opal" / "identity.md"

OWNER_NAME_KEY = "owner_name"

# 읽지 못한 모든 경우(부재·키 부재·공란·파손)의 폴백 — 중립 호칭.
DEFAULT_OWNER_NAME = "사용자"


@dataclass
class ConsoleConfig:
    scan_roots: list[str] = field(default_factory=lambda: list(DEFAULT_SCAN_ROOTS))
    scan_depth: int = DEFAULT_SCAN_DEPTH
    exclude: list[str] = field(default_factory=lambda: list(DEFAULT_EXCLUDE))
    prewarm_projects: list[str] = field(default_factory=list)


def _coerce_str_list(value: object) -> list[str]:
    """list[str]이 아니면 빈 리스트로 폴백. 원소 중 str만 취해 안전 순회 보장(H-4)."""
    if not isinstance(value, list):
        return []
    return [v for v in value if isinstance(v, str)]


def load_config() -> ConsoleConfig:
    """~/.opal/console.config.json 로드. 없으면 기본값 반환.

    설정 파일 생성/갱신은 `opal-cli console scan [기준경로...]`가 수행하며,
    install(install_dashboard)이 신규 머신에서 1회 자동 실행한다.
    백엔드는 이 파일을 읽기 전용으로 소비한다(쓰기 없음, 태스크 021 C-2).
    """
    if not CONFIG_PATH.exists():
        return ConsoleConfig()

    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            data: dict = json.load(f)
    except (json.JSONDecodeError, OSError):
        return ConsoleConfig()

    return ConsoleConfig(
        scan_roots=data.get("scan_roots", DEFAULT_SCAN_ROOTS),
        scan_depth=int(data.get("scan_depth", DEFAULT_SCAN_DEPTH)),
        exclude=data.get("exclude", DEFAULT_EXCLUDE),
        prewarm_projects=_coerce_str_list(data.get("prewarm_projects", [])),
    )


# ── 사용자 호칭 로드 ─────────────────────────────────────────────────────────

_FRONTMATTER_RE = re.compile(r"^---\s*$(.*?)^---\s*$", re.M | re.S)
_OWNER_NAME_RE = re.compile(rf"^{OWNER_NAME_KEY}:\s*(.*)$", re.M)


def load_owner_name() -> str:
    """화면에 쓸 사용자 호칭 → `~/.opal/identity.md` frontmatter의 `owner_name`.

    fail-safe(중립 폴백): 파일 부재·읽기 실패·frontmatter 부재·키 부재·값 공란은
    모두 `DEFAULT_OWNER_NAME`("사용자")를 반환하며 **예외를 밖으로 던지지 않는다** —
    호칭 하나 때문에 조회 응답이 실패해서는 안 된다.

    파싱은 표준 라이브러리 정규식만 쓴다(PyYAML 등 신규 의존 금지). frontmatter가
    없으면 본문 전체에서 키를 찾는 관대한 해석이며, 값의 감싼 따옴표는 벗긴다.
    """
    try:
        content = Path(IDENTITY_PATH).read_text(encoding="utf-8")
    except Exception:
        return DEFAULT_OWNER_NAME

    try:
        matched = _FRONTMATTER_RE.search(content)
        block = matched.group(1) if matched else content
        key = _OWNER_NAME_RE.search(block)
        if not key:
            return DEFAULT_OWNER_NAME
        owner_name = key.group(1).strip().strip("\"'").strip()
    except Exception:
        return DEFAULT_OWNER_NAME

    return owner_name or DEFAULT_OWNER_NAME


# ── 야간 제외 구간 로드 (집계 기준 17) ───────────────────────────────────────

def _read_json_object(path: Path | str) -> dict:
    """JSON 객체 1건 로드. 부재·파손·비객체는 빈 dict (예외 전파 금지)."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _parse_hhmm(value: object, fallback: int) -> int:
    """`HH:MM` 24시간 표기 → 하루 안의 분 오프셋. 형식 위반은 `fallback`.

    `24:00`은 자정 끝을 뜻하므로 허용한다 — `00:00~24:00`으로 하루 전체를 제외할 수 있다.
    """
    if not isinstance(value, str):
        return fallback
    parts = value.strip().split(":")
    if len(parts) != 2:
        return fallback
    try:
        hours, minutes = int(parts[0]), int(parts[1])
    except ValueError:
        return fallback
    if not (0 <= hours <= 24 and 0 <= minutes < 60):
        return fallback
    offset = hours * 60 + minutes
    return offset if offset <= MINUTES_PER_DAY else fallback


class QuietHours(tuple):
    """설정 계층의 야간 제외 구간 판정 결과 — 튜플 값은 `(시작 분, 끝 분)`뿐이고
    `time_zone`은 그 구간에 붙는 **메타데이터 속성**이다(튜플 성분이 아니다).

    [CONTRACT.md §2.8.1 B-1] `config` 모듈과 라우터 계층 내부에서만 흐른다.
    `stats.py` 공개 함수 인자로는 나타나지 않는다 — 라우터가 `(start_minute,
    end_minute)`로 좁혀 넘긴다.

    [동등성·해시 계약] `__eq__`·`__hash__`를 오버라이드하지 않고 `tuple`의
    상속 구현을 그대로 쓴다 — 튜플 값이 `(시작 분, 끝 분)` 2-tuple뿐이므로
    `QuietHours(0, 540, "UTC") == (0, 540)`이 **자연히** 참이고 `hash`도
    일치한다(`a == b ⟹ hash(a) == hash(b)` 불변식 보존, dict 키·set 원소로도
    안전). 기존 테스트(`TestLoadQuietHours`)의 `== (0, 540)` 비교와
    `quiet_hours_token((0, 540))` 레거시 2-tuple 호출은 이 상속 동작만으로
    통과한다 — 특수 오버라이드가 필요하지 않다.
    """

    def __new__(cls, start_minute: int, end_minute: int, time_zone: str) -> "QuietHours":
        self = super().__new__(cls, (start_minute, end_minute))
        self.time_zone = time_zone
        return self

    @property
    def start_minute(self) -> int:
        return self[0]

    @property
    def end_minute(self) -> int:
        return self[1]

    def __repr__(self) -> str:
        return (
            f"QuietHours(start_minute={self[0]!r}, end_minute={self[1]!r}, "
            f"time_zone={self.time_zone!r})"
        )


def _resolve_time_zone(value: object) -> str:
    """`timeZone` 값 → 유효한 IANA 이름이면 그대로, 아니면 기본값으로 폴백.

    무효 이름(오탈자·존재하지 않는 지역)은 `zoneinfo.ZoneInfo`가 예외를 던지므로
    이를 흡수해 `DEFAULT_QUIET_HOURS["timeZone"]`(`Asia/Seoul`)로 대체한다.
    예외를 밖으로 던지지 않고, 설정 파일도 다시 쓰지 않는다(§3.5).
    """
    if isinstance(value, str) and value:
        try:
            ZoneInfo(value)
            return value
        except Exception:
            pass
    return DEFAULT_QUIET_HOURS["timeZone"]


def load_quiet_hours(project_path: str | None = None) -> QuietHours | None:
    """진행 통계에서 매일 제외할 야간 구간 → `QuietHours(시작 분, 끝 분, 시간대)`.

    미적용은 `None`. 2층 머지다 — 전역 `~/.opal/setting.json`의 `quietHours` 위에
    프로젝트 `{project_path}/.opal/setting.local.json`의 `quietHours`를
    **하위 키 단위로** 덮어쓴다(`timeZone`도 같은 머지의 하위 키). 어느 층에도
    키가 없으면 `DEFAULT_QUIET_HOURS`(켬, `00:00~09:00`, `Asia/Seoul`)다.

    `enabled`가 참이 아니면 `None`(보정 끔)이고, `시작 == 끝`이면 제외할 구간이
    없으므로 역시 `None`이다. 반환값은 라우터가 `stats` 모듈에 **분 구간만 좁혀**
    인자로 주입한다 — `stats.py`는 설정을 읽지 않는다 (TS-008 파일 I/O 0건).
    """
    merged = dict(DEFAULT_QUIET_HOURS)

    for source in _quiet_hours_sources(project_path):
        section = source.get(QUIET_HOURS_KEY)
        if isinstance(section, dict):
            merged.update(section)

    if merged.get("enabled") is not True:
        return None

    start = _parse_hhmm(merged.get("start"), _parse_hhmm(DEFAULT_QUIET_HOURS["start"], 0))
    end = _parse_hhmm(merged.get("end"), _parse_hhmm(DEFAULT_QUIET_HOURS["end"], 0))
    if start == end:
        return None
    time_zone = _resolve_time_zone(merged.get("timeZone"))
    return QuietHours(start, end, time_zone)


def _quiet_hours_sources(project_path: str | None) -> list[dict]:
    """머지 순서대로의 설정 원천 — 전역 먼저, 프로젝트 로컬이 나중(로컬 우선)."""
    sources = [_read_json_object(OPAL_SETTING_PATH)]
    if project_path:
        sources.append(_read_json_object(os.path.join(project_path, PROJECT_SETTING_RELPATH)))
    return sources


def quiet_hours_token(quiet_hours: "QuietHours | tuple[int, int] | None") -> str:
    """캐시 키에 실을 제외 구간 서명. 설정이 바뀌면 캐시가 자연히 갈린다.

    캐시 무효화 축은 `state.json` mtime뿐이라(cache.py) 설정 변경은 감지되지 않는다.
    구간을 키에 실어 두면 보정 전후 값이 같은 키를 공유하지 않는다.

    `QuietHours`(3필드) 입력은 `timeZone`도 서명에 포함한다(`"start-end@tz"`) —
    `timeZone`만 다른 두 설정이 같은 캐시 키를 공유하지 않게 한다(CONTRACT §2.8).
    평범한 `(시작 분, 끝 분)` 2-tuple 입력(기존 레거시 호출)은 기존 포맷
    (`"start-end"`)을 그대로 유지한다.
    """
    if quiet_hours is None:
        return "off"
    if isinstance(quiet_hours, QuietHours):
        return f"{quiet_hours.start_minute}-{quiet_hours.end_minute}@{quiet_hours.time_zone}"
    return f"{quiet_hours[0]}-{quiet_hours[1]}"


# ── 쓰기 인프라 (T061 F-001) ──────────────────────────────────────────────────
# 쓰기 대상은 routers/config.py가 검증한 console.config.json(prewarm_projects)
# 갱신으로 한정된다. 이 모듈은 경로 검증을 수행하지 않고 전달받은 경로에
# 원자적으로 쓴다.

_WRITE_LOCK = threading.Lock()   # read-modify-write 사이클 직렬화(H-2)


def _atomic_write_json(path: Path, data: dict) -> None:
    """temp 파일 쓰기 후 os.replace로 atomic rename (부분 쓰기·파손 방지)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)        # 동일 파일시스템 내 atomic rename (POSIX 보장)


def save_config(updates: dict) -> dict:
    """console.config.json 머지 보존 쓰기. 기존 키 유실 금지(H-3)."""
    with _WRITE_LOCK:
        existing = {}
        if CONFIG_PATH.exists():
            try:
                existing = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                existing = {}
        existing.update(updates)          # 부분 갱신 — 미전달 키 보존
        _atomic_write_json(CONFIG_PATH, existing)
        return existing
