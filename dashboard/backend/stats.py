"""
@header {
  "module": "stats",
  "layer": "domain",
  "domain": "console",
  "description": "태스크 진행 통계 집계 코어 — 집계 기준 16항목의 단일 소유 순수 모듈. 앵커(created_at → 각 done 행) 차분으로 행별 소요를 내고, 캡틴·워커·PM 3계열로 분해한다(집계 기준 16, R-16) — 캡틴 = owner==user 행 소요 전액, 워커 = 행의 worker_duration_minutes를 남은 몫으로 상한 clamp, PM = 소요 − 캡틴 − 워커(유도값, 음수 불가). 워커 미기록 행은 전액이 PM에 귀속되므로(축퇴 규칙 16-a) 과거 태스크는 기존 2계열과 수치가 항등이다. 하위 호환 2계열(work = PM + 워커 / wait = 캡틴)은 존치하며 owner 2계열(user=대기 / PM·auto=작업)로 분해한다. 음수 소요는 0 clamp + 단조 앵커(anchor = max(anchor, ts))로 총합 항등을 보존하고, status != done 행과 timestamp 파싱 실패 행은 소요·앵커 진전 모두 건너뛴다. 정적 파생(task_static_stats, 캐시 대상)과 실시간 파생(task_live_stats, now 주입·캐시 밖)을 캐시 경계에 맞춰 분리했다. 실시간 현재 행은 in_progress 우선·없으면 첫 pending이며, 대기 귀속은 owner가 아니라 key의 *.user_confirm 패턴으로 판정한다(pending 행 owner는 init 기본값 PM이라 신뢰 불가). 표시 문자열(format_duration 5규칙·format_timestamp `YY-MM-DD HH:mm:ss`)은 BE 단일 지점 소유 — FE는 계산하지 않는다. 야간 제외 구간(집계 기준 17)은 `quiet_hours=(시작 분, 끝 분)` 2튜플을 **인자로 주입**받아 매일 반복되는 반개구간과 겹치는 분을 소요에서 뺀다 — 여러 밤 걸침을 지원하고, 앵커는 원천 시각 그대로 진전하며, 제외분은 그 행의 계열(캡틴 행=캡틴 / 그 외=PM)에서만 빠진다. 워커는 실측 벽시계라 제외 대상이 아니며 상한 clamp(16-d)로 몫을 먼저 확보한다. 보정 후 행 소요는 3계열 합으로 확정되므로 `총 = PM + 워커 + 캡틴` 항등이 구성적으로 유지된다. 설정 원천(`~/.opal/setting.json` + 프로젝트 `.opal/setting.local.json` 2층 머지)은 `config.load_quiet_hours`가 소유하고 라우터가 주입한다 — 이 모듈은 설정을 읽지 않는다. parse_ts는 초 있음/없음 두 형식을 수용하며 초 부재는 `:00`으로 읽어 분 단위 차분을 종전과 항등으로 보존한다. 3계열 표시 문자열(pm_label·worker_label·captain_label)은 단계·워크플로우·태스크 막대 4층 전건에 실어 내리며, 워크플로우 단계의 누적 total_minutes·total_label(= work + wait)도 여기서 만든다(R-20) — FE는 분→시간 변환을 하지 않는다. [MUST] 표준 라이브러리(datetime·statistics)만 의존하고 모델·라우터·캐시를 import하지 않는다(순환 회피). 파일 I/O 0건.",
  "exports": [
    "TS_FORMAT",
    "TS_FORMAT_SEC",
    "TS_DISPLAY_FORMAT",
    "parse_ts",
    "format_timestamp",
    "format_duration",
    "format_quiet_hours",
    "quiet_overlap_minutes",
    "owner_series",
    "worker_recorded",
    "series_split",
    "row_durations",
    "task_static_stats",
    "task_live_stats",
    "workflow_stats"
  ],
  "depends": [],
  "task": "103",
  "changelog": [
    "2026-08-26 T103 R-21: 야간 시간대 보정(집계 기준 17) — quiet_overlap_minutes·format_quiet_hours 2종 신설, row_durations·task_static_stats·task_live_stats·workflow_stats에 quiet_hours 인자 additive(기본 None=미적용). 제외분은 행의 계열에서 빼고 워커는 보정하지 않는다. quiet_hours_applied·quiet_hours_label 표면화. TS-130~TS-136",
    "2026-08-25 T103 Step3: 집계 코어 신설 — 공개 함수 7종(parse_ts·format_duration·owner_series·row_durations·task_static_stats·task_live_stats·workflow_stats). F-001, TS-001~TS-009",
    "2026-08-25 T103 R-19: 시각 표기 초 해상도 확장 — parse_ts가 `%Y-%m-%d %H:%M:%S`/`%Y-%m-%d %H:%M` 2형식 수용(초 부재는 :00), format_timestamp(`YY-MM-DD HH:mm:ss`) 신설로 행 시각 표시 문자열 소유권을 tasks.py 슬라이싱에서 회수. 날짜 경계 소실 결함 해소",
    "2026-08-25 T103 R-20: 3계열 표시 문자열 additive — 단계 층 그룹·워크플로우 단계·워크플로우 총계·태스크 막대에 pm_label·worker_label·captain_label 추가 + 워크플로우 단계에 누적 total_minutes·total_label 신설. 기존 수치 필드 무변경. TS-120~TS-122",
    "2026-08-25 T103 R-16: 소요 3계열 분해(캡틴·워커·PM) additive — worker_recorded·series_split 2종 신설, 행·단계·태스크·워크플로우 4층에 pm/worker/captain 분해값과 worker_measured 측정 신호 추가. 기존 work·wait 필드는 존치(work = pm + worker). TS-101~TS-105"
  ]
}
"""
from __future__ import annotations

import statistics
from datetime import datetime, timedelta

# state.json `created_at`·`rows[].timestamp` 포맷.
# 103 R-19 이후 state-tool은 초까지 기록하고, 그 이전 기록은 전건 분 해상도다.
# 두 형식을 모두 수용하며, 초가 없으면 `:00`으로 읽는다 — 분 단위 차분은 종전과 항등이다.
TS_FORMAT = "%Y-%m-%d %H:%M"
TS_FORMAT_SEC = "%Y-%m-%d %H:%M:%S"

# 표시용 시각 문자열 포맷 — `YY-MM-DD HH:mm:ss` (캡틴 확정 2026-08-25).
# 날짜를 함께 실어야 날짜 경계를 넘는 행이 시간을 거슬러 가는 것처럼 읽히지 않는다.
TS_DISPLAY_FORMAT = "%y-%m-%d %H:%M:%S"

# 표본 부족 판정 임계 (집계 기준 5)
MIN_SAMPLE = 5

# 워커 소요 원천 필드 (집계 기준 16-b). state.json 행의 선택 필드이며 R-15에서 신설됐다.
WORKER_FIELD = "worker_duration_minutes"

# 야간 제외 구간 표시 문자열의 구분자 (집계 기준 17). 표시 규칙은 여기 단일 소유다 (P-7).
QUIET_HOURS_SEPARATOR = "~"

# 하루의 분 수 — 제외 구간 순회의 단위.
MINUTES_PER_DAY = 24 * 60


# ── 원시 파싱·표시 ────────────────────────────────────────────────────────────

def parse_ts(value: str | None) -> datetime | None:
    """타임스탬프 문자열 파싱. 결측·형식 불일치는 None (예외 전파 금지).

    초 있음(`2026-08-25 10:35:07`)·초 없음(`2026-08-25 10:35`) 두 형식을 모두
    수용한다. 초가 없는 값은 `:00`으로 읽히므로 분 단위 차분은 종전과 항등이다.
    """
    for fmt in (TS_FORMAT_SEC, TS_FORMAT):
        try:
            return datetime.strptime(value, fmt)
        except (TypeError, ValueError):
            continue
    return None


def format_timestamp(value: str | None) -> str:
    """타임스탬프 문자열 → 표시 문자열 `YY-MM-DD HH:mm:ss`. 표시 규칙 단일 소유 (P-7).

    파싱 실패·결측은 빈 문자열이다. 초가 없는 원천은 `:00`으로 표시된다 —
    없는 정밀도를 만들어내지 않으며, 그 값이 분 해상도 기록임을 그대로 드러낸다.
    """
    parsed = parse_ts(value)
    if parsed is None:
        return ""
    return parsed.strftime(TS_DISPLAY_FORMAT)


def format_duration(minutes: int | None) -> str:
    """정수 분 → 표시 문자열. 표시 규칙의 단일 소유 지점 (P-7).

    None → `—` / 0 → `0분` / 60분 미만 → `{m}분`
    / 60분 이상 나머지 0 → `{h}시간` / 그 외 → `{h}시간 {r}분`
    """
    if minutes is None:
        return "—"
    if minutes < 60:
        return f"{minutes}분"
    hours, remainder = divmod(minutes, 60)
    if remainder == 0:
        return f"{hours}시간"
    return f"{hours}시간 {remainder}분"


# ── 야간 제외 구간 (집계 기준 17) ────────────────────────────────────────────
# 「제외 구간」은 `(시작 분, 끝 분)` 하루 안의 분 오프셋 2튜플이며 매일 반복된다.
# `None`이면 보정을 적용하지 않는다(벽시계 그대로). **이 모듈은 설정 파일을 읽지 않는다**
# — 값의 출처(전역 `~/.opal/setting.json` + 프로젝트 `.opal/setting.local.json` 2층 머지)는
# `config.load_quiet_hours`가 소유하고, 라우터가 인자로 주입한다 (TS-008 파일 I/O 0건).

def format_quiet_hours(quiet_hours: tuple[int, int] | None) -> str:
    """제외 구간 → 표시 문자열 `HH:MM~HH:MM`. 미적용은 빈 문자열 (P-7 단일 소유)."""
    if quiet_hours is None:
        return ""
    start, end = quiet_hours
    return f"{_hhmm(start)}{QUIET_HOURS_SEPARATOR}{_hhmm(end)}"


def _hhmm(offset: int) -> str:
    """하루 안의 분 오프셋 → `HH:MM`. 24:00은 자정 끝을 뜻하므로 그대로 표기한다."""
    hours, minutes = divmod(offset % (MINUTES_PER_DAY + 1), 60)
    return f"{hours:02d}:{minutes:02d}"


def quiet_overlap_minutes(
    start: datetime | None,
    end: datetime | None,
    quiet_hours: tuple[int, int] | None,
) -> int:
    """`[start, end)`와 매일 반복되는 제외 구간이 겹치는 총 분 (집계 기준 17).

    여러 밤에 걸칠 수 있다 — 30시간짜리 행이면 두 밤이 모두 빠진다. 구간은 반개구간
    `[시작, 끝)`이라 끝 정각(기본 `09:00`)은 포함하지 않는다. `시작 > 끝`이면 자정을
    넘는 구간으로 읽고(예: `22:00~06:00`), `시작 == 끝`이면 제외할 것이 없다.
    """
    if quiet_hours is None or start is None or end is None or end <= start:
        return 0

    begin, finish = quiet_hours
    if begin == finish:
        return 0

    span = finish - begin if finish > begin else finish + MINUTES_PER_DAY - begin
    # 구간이 자정을 넘으면 전날 창이 `start`까지 흘러올 수 있으므로 하루 앞에서 시작한다.
    day = datetime(start.year, start.month, start.day) - timedelta(days=1)
    total = 0
    while day <= end:
        window_start = day + timedelta(minutes=begin)
        window_end = window_start + timedelta(minutes=span)
        lower = max(start, window_start)
        upper = min(end, window_end)
        if upper > lower:
            total += int((upper - lower).total_seconds() // 60)
        day += timedelta(days=1)
    return total


def owner_series(row: dict, *, live: bool = False) -> str:
    """행의 2계열 귀속 — `work` | `wait` | `""`.

    - 정적(done 행): `owner == "user"` → 대기, `PM`·`auto` → 작업 (집계 기준 6)
    - 실시간(현재 행): `key`가 `*.user_confirm`이면 대기 (집계 기준 14)
      `pending` 행의 `owner`는 `init` 기본값 `PM`이라 귀속 판정에 쓸 수 없다.
    """
    if live:
        key = row.get("key") or ""
        return "wait" if key.endswith(".user_confirm") else "work"
    if row.get("status") != "done":
        return ""
    return "wait" if row.get("owner") == "user" else "work"


def worker_recorded(row: dict) -> int | None:
    """행에 기록된 워커 소요(분). 미기록·비정수는 `None`.

    `0`(측정했으나 1분 미만)과 「미측정」(필드 부재)은 다르다 — 둘 다 계산상 워커 0이지만
    `None`만이 미측정이며, 이 구분이 `worker_measured` 신호의 원천이다.
    """
    value = row.get(WORKER_FIELD)
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return max(0, value)


def series_split(row: dict, minutes: int | None, quiet_minutes: int = 0) -> dict:
    """행 소요를 `캡틴`·`워커`·`PM` 3계열로 분해한다 (집계 기준 16·17).

    - `캡틴` = `owner == "user"` 행의 소요 전액
    - `워커` = 기록된 워커 소요를 남은 몫(`소요 − 캡틴`)으로 상한 clamp
    - `PM` = `소요 − 캡틴 − 워커` (유도값, 별도 계측 없음)

    상한 clamp가 `PM`의 음수를 원천 차단하며, 세 계열의 합은 항상 행 소요와 같다.
    워커 미기록 행은 워커 0이므로 전액이 `PM`에 귀속된다(축퇴 규칙 16-a) — 따라서
    기록이 없는 과거 태스크는 기존 2계열(`작업`·`대기`)과 수치가 항등이다.

    `quiet_minutes`(야간 제외분, 집계 기준 17)는 **그 행이 속한 계열에서** 뺀다 —
    `owner == "user"` 행이면 `캡틴`에서, 그 외 행이면 `PM`에서다. 두 계열은 상호
    배타적이라(캡틴 행은 남은 몫이 0이다) 뺄 곳이 갈리지 않는다. **`워커`는 제외
    대상이 아니다** — 실측 벽시계이므로 야간에 실제로 돈 시간을 깎으면 실제보다
    짧아진다. 그래서 상한 clamp(16-d)로 워커 몫을 **먼저** 확보한 뒤 남은 몫에서만
    제외분을 뺀다. 결과적으로 3계열 합(= 보정 후 행 소요)은 여기서 확정되며,
    호출자는 이 합을 그대로 행 소요로 쓴다 — 항등이 구성적으로 보장된다.
    """
    total = minutes or 0
    captain = total if row.get("owner") == "user" else 0
    available = total - captain

    recorded = worker_recorded(row)
    worker = min(recorded, available) if recorded is not None else 0

    quiet = max(0, min(quiet_minutes, total))
    pm = available - worker
    if captain:
        captain = max(0, captain - quiet)
    else:
        pm = max(0, pm - quiet)

    return {
        "pm_minutes": pm,
        "worker_minutes": worker,
        "captain_minutes": captain,
        "worker_measured": recorded is not None,
        "worker_clamped": recorded is not None and recorded > available,
    }


# ── 행 단위 소요 ──────────────────────────────────────────────────────────────

def row_durations(state: dict, quiet_hours: tuple[int, int] | None = None) -> list[dict]:
    """행별 소요·계열 파생. 입력 `rows` 순서·건수를 그대로 보존한다.

    앵커는 `created_at`에서 시작해 done 행마다 진전한다. `status != "done"` 행과
    `timestamp` 파싱 실패 행은 소요 `None` + 앵커 미진전이며, 음수 소요는 0으로
    clamp하고 앵커는 단조(`max(anchor, ts)`)로 유지해 총합 항등을 보존한다.

    `quiet_hours`가 주어지면(집계 기준 17) 앵커→행 시각 사이에서 제외 구간과 겹치는
    분을 뺀다. **앵커는 원천 시각 그대로 진전한다** — 제외는 계산에만 적용하고
    타임라인을 왜곡하지 않는다. 보정 후 행 소요는 `series_split`이 낸 3계열 합이라
    `총 = PM + 워커 + 캡틴` 항등이 구성적으로 유지된다.
    """
    anchor = parse_ts(state.get("created_at"))
    derived: list[dict] = []

    for index, row in enumerate(state.get("rows") or []):
        minutes: int | None = None
        quiet = 0
        series = owner_series(row)

        if anchor is not None and row.get("status") == "done":
            timestamp = parse_ts(row.get("timestamp"))
            if timestamp is not None:
                minutes = max(0, int((timestamp - anchor).total_seconds() // 60))
                quiet = quiet_overlap_minutes(anchor, timestamp, quiet_hours)
                anchor = max(anchor, timestamp)

        if minutes is None:
            series = ""

        # 소요가 합산되지 않는 행(비 done·파싱 실패)은 3계열도 전부 0이며 미측정으로 둔다.
        split = series_split(row, minutes, quiet) if minutes is not None else _empty_split()

        if minutes is not None:
            # 보정 후 소요 = 3계열 합. 제외분은 계열 안에서 이미 빠졌다 (집계 기준 17).
            minutes = split["pm_minutes"] + split["worker_minutes"] + split["captain_minutes"]

        derived.append({
            "row_id": row.get("row_id", index + 1),
            "duration_minutes": minutes,
            "duration_label": format_duration(minutes),
            "series": series,
            "is_max_gap": False,
            **split,
        })

    _mark_max_gap(derived)
    return derived


def _empty_split() -> dict:
    """소요 미합산 행의 3계열 — 전건 0, 미측정."""
    return {
        "pm_minutes": 0,
        "worker_minutes": 0,
        "captain_minutes": 0,
        "worker_measured": False,
        "worker_clamped": False,
    }


def _mark_max_gap(derived: list[dict]) -> None:
    """최대 공백 행 1건에 `is_max_gap`을 세운다 (동률이면 앞선 행)."""
    peak = None
    for item in derived:
        minutes = item["duration_minutes"]
        if minutes and (peak is None or minutes > peak["duration_minutes"]):
            peak = item
    if peak is not None:
        peak["is_max_gap"] = True


# ── 태스크 단위 — 정적 파생 (캐시 대상) ──────────────────────────────────────

def task_static_stats(state: dict, quiet_hours: tuple[int, int] | None = None) -> dict:
    """태스크 정적 집계. `rows` 부재·`created_at` 파싱 실패면 `available=False`.

    반환값은 렌더 시각에 무관하므로 캐시에 담아도 된다. 실시간 파생은
    `task_live_stats`가 캐시 밖에서 소유한다. `quiet_hours`는 집계 기준 17의 제외
    구간이며, 적용 여부·구간 표시 문자열을 응답에 실어 같은 태스크가 두 수치로
    보이는 혼란을 막는다.
    """
    rows = state.get("rows") or []
    if not rows or parse_ts(state.get("created_at")) is None:
        return _unavailable_static(quiet_hours)

    derived = row_durations(state, quiet_hours)

    stage_map: dict[str, dict] = {}
    for row, item in zip(rows, derived):
        stage = row.get("stage", "")
        group = stage_map.setdefault(stage, {
            "stage": stage,
            "work_minutes": 0,
            "wait_minutes": 0,
            "total_minutes": 0,
            "pm_minutes": 0,
            "worker_minutes": 0,
            "captain_minutes": 0,
            "worker_measured": False,
        })
        minutes = item["duration_minutes"] or 0
        group["total_minutes"] += minutes
        if item["series"] == "wait":
            group["wait_minutes"] += minutes
        elif item["series"] == "work":
            group["work_minutes"] += minutes

        group["pm_minutes"] += item["pm_minutes"]
        group["worker_minutes"] += item["worker_minutes"]
        group["captain_minutes"] += item["captain_minutes"]
        group["worker_measured"] = group["worker_measured"] or item["worker_measured"]

    stages = list(stage_map.values())
    peak = _peak_by(stages, "total_minutes")
    for group in stages:
        group["total_label"] = format_duration(group["total_minutes"])
        # 3계열 표시 문자열 (R-20) — 단계 구획 호버 지표의 원천. FE는 조립하지 않는다 (P-7)
        group["pm_label"] = format_duration(group["pm_minutes"])
        group["worker_label"] = format_duration(group["worker_minutes"])
        group["captain_label"] = format_duration(group["captain_minutes"])
        group["is_peak"] = group is peak

    total = sum(group["total_minutes"] for group in stages)
    work = sum(group["work_minutes"] for group in stages)
    wait = sum(group["wait_minutes"] for group in stages)
    pm = sum(group["pm_minutes"] for group in stages)
    worker = sum(group["worker_minutes"] for group in stages)
    captain = sum(group["captain_minutes"] for group in stages)
    gate_count = sum(1 for row in rows if row.get("gate") is not None)

    return {
        "available": True,
        "total_minutes": total,
        "total_label": format_duration(total),
        # 하위 호환 2계열 — work = PM + 워커, wait = 캡틴 (기존 FE·테스트 계약)
        "work_minutes": work,
        "work_label": format_duration(work),
        "wait_minutes": wait,
        "wait_label": format_duration(wait),
        "wait_ratio": _ratio(wait, total),
        # 3계열 분해 (집계 기준 16) — pm + worker + captain == total
        "pm_minutes": pm,
        "pm_label": format_duration(pm),
        "worker_minutes": worker,
        "worker_label": format_duration(worker),
        "captain_minutes": captain,
        "captain_label": format_duration(captain),
        "worker_measured": any(item["worker_measured"] for item in derived),
        "worker_clamped_count": sum(1 for item in derived if item["worker_clamped"]),
        "peak_stage": peak["stage"] if peak else "",
        "peak_stage_label": format_duration(peak["total_minutes"]) if peak else "—",
        "stages": stages,
        "rows": derived,
        "gate_count": gate_count,
        "gate_recorded": gate_count > 0,
        "blocker_count": sum(1 for row in rows if row.get("status") == "failed"),
        # 야간 보정 표면화 (집계 기준 17) — FE 배지의 원천. 같은 태스크가 보정 전후
        # 두 수치로 보이는 혼란을 막으려면 수치와 함께 「무엇을 뺐는지」가 실려야 한다.
        "quiet_hours_applied": quiet_hours is not None,
        "quiet_hours_label": format_quiet_hours(quiet_hours),
    }


def _unavailable_static(quiet_hours: tuple[int, int] | None = None) -> dict:
    """집계 불가 태스크의 정적 파생. 수치는 0, 표시 문자열은 `—`."""
    return {
        "available": False,
        "total_minutes": 0,
        "total_label": "—",
        "work_minutes": 0,
        "work_label": "—",
        "wait_minutes": 0,
        "wait_label": "—",
        "wait_ratio": 0,
        "pm_minutes": 0,
        "pm_label": "—",
        "worker_minutes": 0,
        "worker_label": "—",
        "captain_minutes": 0,
        "captain_label": "—",
        "worker_measured": False,
        "worker_clamped_count": 0,
        "peak_stage": "",
        "peak_stage_label": "—",
        "stages": [],
        "rows": [],
        "gate_count": 0,
        "gate_recorded": False,
        "blocker_count": 0,
        "quiet_hours_applied": quiet_hours is not None,
        "quiet_hours_label": format_quiet_hours(quiet_hours),
    }


# ── 태스크 단위 — 실시간 파생 (캐시 밖, now 주입) ────────────────────────────

def task_live_stats(
    state: dict,
    now: datetime | None = None,
    quiet_hours: tuple[int, int] | None = None,
) -> dict:
    """태스크 실시간 집계. `now` 주입으로 결정론적 검증이 가능하다.

    진행 중이면 총 리드타임을 `created_at → now`로, 완료면 정적 값 그대로 쓴다
    (집계 기준 11). 현재 행은 `in_progress` 우선·없으면 첫 `pending`이며(집계 기준 12),
    경과 시간은 직전 done 행 → `now`다 (집계 기준 13).

    `quiet_hours`(집계 기준 17)는 실시간 총과 현재 행 경과 양쪽에 같은 규칙으로
    적용한다 — 한쪽만 보정하면 16-c의 4구획 항등(총 = PM + 워커 + 캡틴 + 진행중)이
    깨진다. 현재 행은 아직 계열이 확정되지 않았으므로 제외분을 경과에서 곧장 뺀다.
    """
    if now is None:
        now = datetime.now()

    rows = state.get("rows") or []
    anchor = parse_ts(state.get("created_at"))
    is_running = state.get("current_status") != "done"

    if is_running and anchor is not None:
        total = max(0, int((now - anchor).total_seconds() // 60))
        total = max(0, total - quiet_overlap_minutes(anchor, now, quiet_hours))
    else:
        total = task_static_stats(state, quiet_hours)["total_minutes"]

    current = _current_row(rows) if is_running else None

    elapsed = None
    if current is not None:
        last_done = _last_done_ts(rows, anchor)
        if last_done is not None:
            elapsed = max(0, int((now - last_done).total_seconds() // 60))
            elapsed = max(0, elapsed - quiet_overlap_minutes(last_done, now, quiet_hours))

    return {
        "is_running": is_running,
        "total_minutes": total,
        "total_label": format_duration(total),
        "current_row_id": current.get("row_id") if current else None,
        "current_stage": current.get("stage") if current else None,
        "current_item": current.get("item") if current else None,
        "current_key": current.get("key") if current else None,
        "current_series": owner_series(current, live=True) if current else "",
        "current_elapsed_minutes": elapsed,
        "current_elapsed_label": format_duration(elapsed),
    }


def _current_row(rows: list[dict]) -> dict | None:
    """현재 행 — `in_progress` 우선, 없으면 첫 `pending` (집계 기준 12)."""
    for row in rows:
        if row.get("status") == "in_progress":
            return row
    for row in rows:
        if row.get("status") == "pending":
            return row
    return None


def _last_done_ts(rows: list[dict], anchor: datetime | None) -> datetime | None:
    """직전 done 행의 타임스탬프. done 행이 없으면 앵커(`created_at`)."""
    latest = anchor
    for row in rows:
        if row.get("status") != "done":
            continue
        timestamp = parse_ts(row.get("timestamp"))
        if timestamp is not None and (latest is None or timestamp > latest):
            latest = timestamp
    return latest


# ── 워크플로우 단위 ──────────────────────────────────────────────────────────

def workflow_stats(
    states: list[dict],
    quiet_hours: tuple[int, int] | None = None,
) -> list[dict]:
    """`skill`별 횡단 집계. 모수는 완료 태스크만이다 (집계 기준 3).

    응답 키는 원천 용어 `skill`을 쓰고 `workflow`를 만들지 않는다 (집계 기준 15).
    대표값은 중앙값이 주 지표·평균이 보조이며, `n < 5`는 표본 부족으로 표시한다.
    `quiet_hours`(집계 기준 17)는 태스크 층 집계에 그대로 전달된다 — 모수 구성은
    보정과 무관하므로 코호트 자체는 달라지지 않고 각 태스크의 소요만 줄어든다.
    """
    grouped: dict[str, list[dict]] = {}
    for state in states:
        if state.get("current_status") != "done":
            continue
        grouped.setdefault(state.get("skill", ""), []).append(state)

    return [_workflow_entry(skill, grouped[skill], quiet_hours) for skill in sorted(grouped)]


def _workflow_entry(
    skill: str,
    members: list[dict],
    quiet_hours: tuple[int, int] | None = None,
) -> dict:
    tasks: list[dict] = []
    work = wait = gate_count = blocker_count = 0
    pm = worker = captain = 0
    worker_measured = False
    stage_map: dict[str, dict] = {}

    for state in members:
        static = task_static_stats(state, quiet_hours)
        task_id = state.get("_task_id") or state.get("task_id") or ""
        tasks.append({
            "task_id": task_id,
            "title": state.get("_title") or task_id,
            "total_minutes": static["total_minutes"],
            "total_label": static["total_label"],
            # 3계열 승계 (R-20) — 태스크 막대 호버 지표. 태스크 층 라벨을 그대로 실어 나른다
            "pm_minutes": static["pm_minutes"],
            "pm_label": static["pm_label"],
            "worker_minutes": static["worker_minutes"],
            "worker_label": static["worker_label"],
            "captain_minutes": static["captain_minutes"],
            "captain_label": static["captain_label"],
            "worker_measured": static["worker_measured"],
            "is_peak": False,
        })
        work += static["work_minutes"]
        wait += static["wait_minutes"]
        pm += static["pm_minutes"]
        worker += static["worker_minutes"]
        captain += static["captain_minutes"]
        worker_measured = worker_measured or static["worker_measured"]
        gate_count += static["gate_count"]
        blocker_count += static["blocker_count"]

        for group in static["stages"]:
            accumulator = stage_map.setdefault(group["stage"], {
                "stage": group["stage"],
                "n": 0,
                "_totals": [],
                "work_minutes": 0,
                "wait_minutes": 0,
                "pm_minutes": 0,
                "worker_minutes": 0,
                "captain_minutes": 0,
                "worker_measured": False,
            })
            accumulator["n"] += 1
            accumulator["_totals"].append(group["total_minutes"])
            accumulator["work_minutes"] += group["work_minutes"]
            accumulator["wait_minutes"] += group["wait_minutes"]
            accumulator["pm_minutes"] += group["pm_minutes"]
            accumulator["worker_minutes"] += group["worker_minutes"]
            accumulator["captain_minutes"] += group["captain_minutes"]
            accumulator["worker_measured"] = (
                accumulator["worker_measured"] or group["worker_measured"]
            )

    peak_task = _peak_by(tasks, "total_minutes")
    if peak_task is not None:
        peak_task["is_peak"] = True

    stages = []
    for accumulator in stage_map.values():
        median = _round_half_up(statistics.median(accumulator.pop("_totals")))
        accumulator["median_minutes"] = median
        accumulator["median_label"] = format_duration(median)
        # 누적 총 = work + wait (== pm + worker + captain, 집계 기준 16 항등).
        # 막대 폭의 분모이자 구획 호버가 읽는 「단계 총」이다 (R-20).
        accumulator["total_minutes"] = accumulator["work_minutes"] + accumulator["wait_minutes"]
        accumulator["total_label"] = format_duration(accumulator["total_minutes"])
        accumulator["pm_label"] = format_duration(accumulator["pm_minutes"])
        accumulator["worker_label"] = format_duration(accumulator["worker_minutes"])
        accumulator["captain_label"] = format_duration(accumulator["captain_minutes"])
        accumulator["is_peak"] = False
        stages.append(accumulator)

    peak_stage = _peak_by(stages, "median_minutes")
    if peak_stage is not None:
        peak_stage["is_peak"] = True

    totals = [task["total_minutes"] for task in tasks]
    median_minutes = _round_half_up(statistics.median(totals))
    mean_minutes = _round_half_up(statistics.fmean(totals))

    return {
        "skill": skill,
        "n": len(members),
        "sample_insufficient": len(members) < MIN_SAMPLE,
        "median_minutes": median_minutes,
        "median_label": format_duration(median_minutes),
        "mean_minutes": mean_minutes,
        "mean_label": format_duration(mean_minutes),
        "work_minutes": work,
        "wait_minutes": wait,
        "wait_ratio": _ratio(wait, work + wait),
        "pm_minutes": pm,
        "pm_label": format_duration(pm),
        "worker_minutes": worker,
        "worker_label": format_duration(worker),
        "captain_minutes": captain,
        "captain_label": format_duration(captain),
        "worker_measured": worker_measured,
        "gate_count": gate_count,
        "blocker_count": blocker_count,
        "quiet_hours_applied": quiet_hours is not None,
        "quiet_hours_label": format_quiet_hours(quiet_hours),
        "stages": stages,
        "tasks": tasks,
    }


# ── 공통 유틸 ────────────────────────────────────────────────────────────────

def _peak_by(items: list[dict], field: str) -> dict | None:
    """`field` 최댓값 항목 1건 (동률이면 앞선 항목). 전건 0이면 None."""
    peak = None
    for item in items:
        if item[field] and (peak is None or item[field] > peak[field]):
            peak = item
    return peak


def _round_half_up(value: float) -> int:
    """정수 분·백분율 반올림. 0.5는 위로 올린다 (은행가 반올림 회피)."""
    return int(value + 0.5)


def _ratio(part: int, whole: int) -> int:
    """백분율(정수). 분모 0이면 0."""
    if whole <= 0:
        return 0
    return _round_half_up(part / whole * 100)
