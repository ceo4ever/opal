"""
@header {
  "module": "tests.test_stats",
  "layer": "test",
  "domain": "console",
  "description": "[T103] stats.py 집계 코어 순수 함수 계약 (TS-001~TS-009 + R-16 3계열 TS-101~TS-105 + R-20 표시 문자열 TS-120~TS-122). 앵커 차분·2계열 귀속·음수 clamp·단조 앵커·결측 내성·실시간 now 주입·워크플로우별 대표값·format_duration·순환 import 차단을 단정한다. 기대값 원천은 tasks/103-260825-opd-태스크-진행통계/STATS-BASELINE.md §3~§5 (ANALYSIS §8 재검증 완료 수치, 근거 E1) — stats.py 출력을 되쓰지 않는다(self-confirming 금지). 픽스처는 tests/fixtures/t103_states/ 동결 복사본이며 라이브 tasks/*/state.json을 직독하지 않는다. RED-first — 작성자(opal-test-agent, mode: red) != 구현자(opal-be-agent). TS-130~TS-136은 R-21 야간 시간대 보정(집계 기준 17) 계약 — 매일 반복되는 제외 구간 `00:00~09:00`을 소요에서 빼며, 여러 밤 걸침·반개구간 경계·자정 넘는 구간·보정 끔을 단정하고, 워커 소요가 보정 대상이 아님과 3계열 항등 유지를 못박는다. 기대값은 손계산과 STATS-BASELINE.md §4.4(보정 후 병기 절)에서만 가져온다. TS-101~TS-105는 R-16 소요 3계열(캡틴·워커·PM) 계약 — 워커 기록 태스크(103 동결본)의 실분해, 미기록 태스크(101)의 축퇴 항등(PM == 기존 작업 · 캡틴 == 기존 대기), 「기록된 0」과 「미기록」의 worker_measured 신호 구분, 상한 clamp에 의한 PM 음수 차단, 워크플로우 대표값 불변을 단정한다.",
  "exports": [
    "test_ts001_task_static_total_two_series",
    "test_ts002_task_static_stage_breakdown",
    "test_ts003_backward_timestamp_clamped_and_monotonic_anchor",
    "test_ts004_empty_rows_available_false",
    "test_ts004_missing_created_at_available_false",
    "test_ts004_unparsable_timestamp_skips_without_advancing_anchor",
    "test_ts005_live_current_row_and_key_pattern_series",
    "test_ts006_completed_task_ignores_now",
    "test_ts007_workflow_stats_frozen_cohort",
    "test_ts008_stats_module_import_boundary",
    "test_ts009_format_duration_rules",
    "test_ts101_three_series_split_on_measured_task",
    "test_ts101_three_series_stage_breakdown",
    "test_ts102_degenerate_to_two_series_when_unmeasured",
    "test_ts102_degenerate_stage_breakdown_matches_two_series",
    "test_ts103_recorded_zero_differs_from_unrecorded",
    "test_ts104_pm_never_negative_and_clamp_is_reported",
    "test_ts105_workflow_three_series_preserves_two_series",
    "test_ts120_stage_layer_series_labels",
    "test_ts120_stage_layer_labels_match_minutes",
    "test_ts121_workflow_layer_series_labels",
    "test_ts122_task_leadtime_inherits_series_labels",
    "test_ts130_multiple_nights_are_all_excluded",
    "test_ts131_same_day_task_is_unchanged",
    "test_ts132_disabled_keeps_wall_clock",
    "test_ts133_end_boundary_is_exclusive",
    "test_ts134_worker_minutes_are_never_reduced",
    "test_ts135_three_series_identity_holds_under_quiet_hours",
    "test_ts136_cohort_medians_move_to_baseline",
    "test_ts136_wrapping_window_and_surfacing"
  ],
  "depends": ["stats"],
  "task": "103",
  "scenarios": ["TS-001", "TS-002", "TS-003", "TS-004", "TS-005", "TS-006", "TS-007", "TS-008", "TS-009", "TS-101", "TS-102", "TS-103", "TS-104", "TS-105", "TS-120", "TS-121", "TS-122", "TS-130", "TS-131", "TS-132", "TS-133", "TS-134", "TS-135", "TS-136"],
  "changelog": [
    "2026-08-26 T103 R-21: TS-130~TS-136 야간 보정 케이스 8건 추가 — 여러 밤 걸침·미걸침(101 불변)·보정 끔·반개구간 경계(09:00)·워커 미보정·3계열 항등·코호트 대표값 이동(opd 799→425)·자정 넘는 구간. 기존 TS-001~TS-122 무변경(quiet_hours 기본 None)",
    "2026-08-25 T103 R2 RED: TS-001~TS-009 실패 테스트 신규 — dashboard/backend/stats.py 미존재 상태에서 작성. 구현(Step 3) 전 RED 트랙(red-first.md §1), 작성자!=구현자(동 §2)",
    "2026-08-25 T103 R-20: TS-120~TS-122 3계열 표시 문자열 케이스 4건 추가 — 단계·워크플로우·태스크 막대 층의 pm/worker/captain_label과 워크플로우 단계 누적 총 라벨. 오라클은 _spec_label(표시 규칙 독립 재기술)이며 format_duration을 되쓰지 않는다. 기존 케이스·픽스처 무변경",
    "2026-08-25 T103 R-16: TS-101~TS-105 3계열 분해 케이스 7건 추가 + fixtures/t103_states/103-*.json 동결본 신규(워커 소요 기록 6행 보유 — 이 프로젝트 유일). 기존 TS-001~TS-009 무변경"
  ]
}
"""
from __future__ import annotations

import ast
import copy
import json
import os
from datetime import datetime

import pytest

# ── 픽스처 로더 — 동결 복사본만 사용 (§0.5 라이브 직독 금지) ──────────────────

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "t103_states")

FX_101_ID = "101-260824-opd-핸드오프-스키마-계약정합"
FX_086_ID = "086-260810-opp-아키텍처-다이어그램-재작성"
FX_102_ID = "102-260824-opd-태스크분석-경계재정의"

# STATS-BASELINE.md §2.1 동결 코호트 21건 (3자리 접두)
COHORT_OPD = ["080", "091", "092", "093", "094", "100", "101"]
COHORT_OPDS = ["081", "082", "083", "085", "090", "095", "096", "097", "098", "099"]
COHORT_OPP = ["084", "086", "087", "088"]
COHORT_PREFIXES = COHORT_OPD + COHORT_OPDS + COHORT_OPP

TS_FORMAT = "%Y-%m-%d %H:%M"


def load_state(task_id: str) -> dict:
    """동결 복사본 1건 로드."""
    with open(os.path.join(FIXTURE_DIR, task_id + ".json"), encoding="utf-8") as f:
        return json.load(f)


def load_cohort() -> list[dict]:
    """FX-COHORT — 동결 코호트 21건. 라우터가 하듯 `_title`을 주입한다."""
    states = []
    for name in sorted(os.listdir(FIXTURE_DIR)):
        task_id = name[:-5]
        if task_id[:3] not in COHORT_PREFIXES:
            continue
        state = load_state(task_id)
        state["_task_id"] = task_id
        state["_title"] = task_id
        states.append(state)
    return states


@pytest.fixture
def fx_101():
    return load_state(FX_101_ID)


@pytest.fixture
def fx_086():
    return load_state(FX_086_ID)


@pytest.fixture
def fx_102():
    return load_state(FX_102_ID)


@pytest.fixture
def fx_cohort():
    return load_cohort()


# ── TS-001: 101 총 리드타임 2계열 분해 ───────────────────────────────────────

def test_ts001_task_static_total_two_series(fx_101):
    """[T103/L1-R3] 101 총 425분 = 작업 105 + 대기 320, 대기 비중 75%.

    기대값 원천: STATS-BASELINE.md §3.1.
    RED 기대 실패: dashboard.backend.stats 미존재 → ImportError.
    """
    from dashboard.backend.stats import task_static_stats

    s = task_static_stats(fx_101)

    assert s["available"] is True
    assert s["total_minutes"] == 425
    assert s["work_minutes"] == 105
    assert s["wait_minutes"] == 320
    assert s["work_minutes"] + s["wait_minutes"] == s["total_minutes"]
    assert s["wait_ratio"] == 75
    assert s["total_label"] == "7시간 5분"
    assert s["work_label"] == "1시간 45분"
    assert s["wait_label"] == "5시간 20분"
    assert s["peak_stage"] == "TEST-SCENARIO"
    assert s["gate_count"] == 4
    assert s["gate_recorded"] is True
    assert s["blocker_count"] == 0
    assert len(s["rows"]) == 19


# ── TS-002: 101 단계별 작업·대기 합계 7그룹 ──────────────────────────────────

# STATS-BASELINE.md §3.2 — stage: (total, work, wait)
BASELINE_101_STAGES = [
    ("TASK", 24, 0, 24),
    ("ANALYSIS", 22, 17, 5),
    ("PLAN", 13, 11, 2),
    ("TEST-SCENARIO", 295, 10, 285),
    ("EXECUTE", 18, 18, 0),
    ("TEST", 51, 47, 4),
    ("CLOSE", 2, 2, 0),
]


def test_ts002_task_static_stage_breakdown(fx_101):
    """[T103/L1-R3] 101 단계별 7그룹 소요가 베이스라인 §3.2와 전건 일치한다."""
    from dashboard.backend.stats import task_static_stats

    stages = task_static_stats(fx_101)["stages"]

    assert len(stages) == 7
    assert [g["stage"] for g in stages] == [name for name, _, _, _ in BASELINE_101_STAGES]

    for group, (name, total, work, wait) in zip(stages, BASELINE_101_STAGES):
        assert group["stage"] == name
        assert group["total_minutes"] == total, f"{name} 총 소요"
        assert group["work_minutes"] == work, f"{name} 작업 소요"
        assert group["wait_minutes"] == wait, f"{name} 대기 소요"
        assert group["work_minutes"] + group["wait_minutes"] == group["total_minutes"]

    assert sum(g["total_minutes"] for g in stages) == 425

    peaks = [g["stage"] for g in stages if g["is_peak"]]
    assert peaks == ["TEST-SCENARIO"]

    peak_group = next(g for g in stages if g["stage"] == "TEST-SCENARIO")
    assert peak_group["total_label"] == "4시간 55분"


# ── TS-003: 역행 타임스탬프 0 clamp + 단조 앵커 총합 항등 ────────────────────

def test_ts003_backward_timestamp_clamped_and_monotonic_anchor(fx_086):
    """[T103/L1-R12] 086 row 5(15:46 < 직전 앵커 15:47)가 0으로 clamp되고 총합 항등이 보존된다.

    기대값 원천: STATS-BASELINE.md §1.2 「음수 실측 1건」 + §6.3 대조표.
    총 450분 = 22:48 − 15:18.
    """
    from dashboard.backend.stats import row_durations, task_static_stats

    rows = row_durations(fx_086)
    by_id = {r["row_id"]: r for r in rows}

    # 역행 행: 원시 −1분 → clamp 0
    assert by_id[5]["duration_minutes"] == 0

    # 음수 0건
    negatives = [r for r in rows if (r["duration_minutes"] or 0) < 0]
    assert negatives == []

    # 단조 앵커: row 6은 15:47 앵커 기준 45분이며 15:46 기준 46분으로 부풀지 않는다
    assert by_id[6]["duration_minutes"] == 45

    # clamp 후에도 총합 항등 보존 (449가 아니라 450)
    s = task_static_stats(fx_086)
    assert s["total_minutes"] == 450
    assert s["work_minutes"] + s["wait_minutes"] == 450


# ── TS-004: 결측 내성 3경로 ──────────────────────────────────────────────────

def test_ts004_empty_rows_available_false(fx_101):
    """[T103/L1-R12] FX-EMPTY — rows가 비면 예외 없이 available=false."""
    from dashboard.backend.stats import task_static_stats

    fx_empty = copy.deepcopy(fx_101)
    fx_empty["rows"] = []

    s = task_static_stats(fx_empty)
    assert s["available"] is False


def test_ts004_missing_created_at_available_false(fx_101):
    """[T103/L1-R12] FX-NOCREATED — created_at 키가 없으면 예외 없이 available=false."""
    from dashboard.backend.stats import task_static_stats

    fx_nocreated = copy.deepcopy(fx_101)
    fx_nocreated.pop("created_at", None)

    s = task_static_stats(fx_nocreated)
    assert s["available"] is False


def test_ts004_unparsable_timestamp_skips_without_advancing_anchor(fx_101):
    """[T103/L1-R12] FX-BADTS — 파싱 실패 행은 소요 None + 앵커 미진전.

    row 3 timestamp를 ISO 표기(2026-08-24T17:13)로 훼손한다.
    앵커가 진전하지 않으므로 row 4 소요는 row 2 앵커(16:56) 기준 17분이 된다
    (17:13 − 16:56). row 5 이후는 FX-101과 동일하다.
    """
    from dashboard.backend.stats import row_durations

    baseline_rows = {r["row_id"]: r for r in row_durations(fx_101)}

    fx_badts = copy.deepcopy(fx_101)
    target = next(r for r in fx_badts["rows"] if r["row_id"] == 3)
    assert target["timestamp"] == "2026-08-24 17:13", "픽스처 전제"
    target["timestamp"] = "2026-08-24T17:13"

    rows = row_durations(fx_badts)
    by_id = {r["row_id"]: r for r in rows}

    assert by_id[3]["duration_minutes"] is None
    assert by_id[4]["duration_minutes"] == 17

    for row_id in range(5, 20):
        assert by_id[row_id]["duration_minutes"] == baseline_rows[row_id]["duration_minutes"], (
            f"row {row_id} 소요가 FX-101과 달라졌다"
        )


# ── TS-005: 실시간 현재 행 식별 + key 패턴 대기 귀속 ─────────────────────────

def test_ts005_live_current_row_and_key_pattern_series(fx_102):
    """[T103/L1-R4] FX-102 + now 고정 주입 — 첫 pending 행이 현재 행이고 key 패턴으로 wait 귀속.

    FX-102는 in_progress 행 0건이고 pending 15행이 전건 owner=PM(init 기본값)이다.
    owner 기반 귀속이면 work로 나오므로, key의 *.user_confirm 패턴 판정이어야 wait가 된다.
    created_at 2026-08-24 17:33 → now 2026-08-25 16:10 = 1357분.
    """
    from dashboard.backend.stats import task_live_stats

    now = datetime(2026, 8, 25, 16, 10)
    s = task_live_stats(fx_102, now=now)

    assert s["is_running"] is True
    assert s["current_row_id"] == 2
    assert s["current_key"] == "task.user_confirm"
    assert s["current_stage"] == "TASK"
    assert s["current_series"] == "wait"
    assert s["total_minutes"] == 1357
    assert s["current_elapsed_minutes"] == 1357

    # 전제 확인 — owner를 썼다면 work가 나왔을 데이터다
    current = next(r for r in fx_102["rows"] if r["row_id"] == 2)
    assert current["owner"] == "PM"
    assert current["status"] == "pending"


# ── TS-006: 완료 태스크는 실시간을 쓰지 않는다 ───────────────────────────────

def test_ts006_completed_task_ignores_now(fx_101):
    """[T103/L1-R4] 완료 태스크(101)는 now를 바꿔도 total_minutes 425 불변."""
    from dashboard.backend.stats import task_live_stats

    early = task_live_stats(fx_101, now=datetime(2026, 8, 24, 23, 40))
    late = task_live_stats(fx_101, now=datetime(2026, 12, 31, 0, 0))

    for s in (early, late):
        assert s["is_running"] is False
        assert s["total_minutes"] == 425
        assert s["current_row_id"] is None
        assert s["current_elapsed_minutes"] is None

    assert early["total_minutes"] == late["total_minutes"]


# ── TS-007: 동결 코호트 21건 워크플로우별 집계 ───────────────────────────────

# STATS-BASELINE.md §4.1·§4.2 — skill: (n, median_minutes, wait_ratio, sample_insufficient)
BASELINE_WORKFLOWS = {
    "opd": (7, 799, 21, False),
    "opds": (10, 276, 4, False),   # n=10 → 표본 충분
    "opp": (4, 75, 54, True),
}


def test_ts007_workflow_stats_frozen_cohort(fx_cohort):
    """[T103/L1-R10] 동결 코호트 21건 → skill별 중앙값 799/276/75, 대기 비중 21/4/54.

    기대값 원천: STATS-BASELINE.md §4.1·§4.2.
    opds 중앙값은 원시 275.5(짝수 모수 n=10)의 정수 반올림 결과 276이다.
    """
    from dashboard.backend.stats import workflow_stats

    assert len(fx_cohort) == 21, "동결 코호트 모수"

    result = workflow_stats(fx_cohort)

    assert len(result) == 3
    by_skill = {w["skill"]: w for w in result}
    assert sorted(by_skill) == ["opd", "opds", "opp"]

    # 집계기준 15 — 응답 키는 원천 용어 `skill`이며 `workflow`를 만들지 않는다
    for w in result:
        assert "workflow" not in w

    for skill, (n, median, wait_ratio, insufficient) in BASELINE_WORKFLOWS.items():
        w = by_skill[skill]
        assert w["n"] == n, f"{skill} 모수"
        assert w["median_minutes"] == median, f"{skill} 중앙값"
        assert w["wait_ratio"] == wait_ratio, f"{skill} 대기 비중"
        assert w["sample_insufficient"] is insufficient, f"{skill} 표본 부족 판정"
        assert len(w["tasks"]) == n

    assert by_skill["opd"]["median_label"] == "13시간 19분"
    assert by_skill["opds"]["median_label"] == "4시간 36분"
    assert by_skill["opp"]["median_label"] == "1시간 15분"

    assert sum(w["n"] for w in result) == 21


# ── TS-008: stats.py 순수 모듈 경계 (순환 import 차단) ───────────────────────

def test_ts008_stats_module_import_boundary():
    """[T103/L1-R1] stats.py의 import 대상이 표준 라이브러리 2종으로 한정된다.

    [MUST] PLAN.md §8: "stats.py 의존 범위 — 표준 라이브러리(datetime·statistics)만.
    모델·라우터·캐시 import 금지".
    """
    import dashboard.backend.stats as stats_mod

    source_path = stats_mod.__file__
    with open(source_path, encoding="utf-8") as f:
        tree = ast.parse(f.read())

    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level:  # 상대 import는 곧 패키지 내부 결합이다
                imported.add("<relative>")
            elif node.module:
                imported.add(node.module.split(".")[0])

    allowed = {"__future__", "datetime", "statistics"}
    assert imported <= allowed, f"허용 밖 import: {sorted(imported - allowed)}"

    # dashboard.backend 하위 모듈 import 0건
    assert not any(name == "dashboard" for name in imported)

    # 파일 I/O 0건 — open() 직접 호출 없음
    open_calls = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "open"
    ]
    assert open_calls == []


# ── TS-009: format_duration 표시 문자열 규칙 ─────────────────────────────────

@pytest.mark.parametrize(
    ("minutes", "expected"),
    [
        (None, "—"),
        (0, "0분"),
        (45, "45분"),
        (105, "1시간 45분"),
        (120, "2시간"),
        (276, "4시간 36분"),
        (285, "4시간 45분"),
        (295, "4시간 55분"),
        (320, "5시간 20분"),
        (425, "7시간 5분"),
    ],
)
def test_ts009_format_duration_rules(minutes, expected):
    """[T103/L1-R6] format_duration 5규칙 — None/0/분 단독/시분/나머지 0 경계."""
    from dashboard.backend.stats import format_duration

    assert format_duration(minutes) == expected


# ══════════════════════════════════════════════════════════════════════════════
# TS-101~TS-105 — 소요 3계열 분해 (R-16, 집계 기준 16·16-a)
# 기대값 원천: TASK.md §집계 기준 16·16-a + 103 state.json 동결 복사본 실측 차분.
# 축퇴 규칙 — 워커 미기록 행은 그 몫이 전액 PM에 귀속되므로 과거 태스크는 2계열과 항등.
# ══════════════════════════════════════════════════════════════════════════════

FX_103_ID = "103-260825-opd-태스크-진행통계"

# 103 동결본 실측 — 총 299 = 캡틴 130 + 워커 146 + PM 23
BASELINE_103_SERIES = {"total": 299, "captain": 130, "worker": 146, "pm": 23}

# 103 동결본 단계별 — stage: (total, pm, worker, captain, worker_measured)
BASELINE_103_STAGES = [
    ("TASK", 115, 0, 0, 115, False),
    ("ANALYSIS", 26, 3, 16, 7, True),
    ("PLAN", 28, 5, 21, 2, True),
    ("TEST-SCENARIO", 32, 6, 20, 6, True),
    ("EXECUTE", 87, 7, 80, 0, True),
    ("TEST", 11, 2, 9, 0, True),
    ("CLOSE", 0, 0, 0, 0, False),
]


@pytest.fixture
def fx_103():
    return load_state(FX_103_ID)


# ── TS-101: 워커 기록 태스크의 3계열 실분해 ──────────────────────────────────

def test_ts101_three_series_split_on_measured_task(fx_103):
    """[T103/L1-R16] 103 총 299 = 캡틴 130 + 워커 146 + PM 23, 음수 0건."""
    from dashboard.backend.stats import task_static_stats

    s = task_static_stats(fx_103)

    assert s["available"] is True
    assert s["total_minutes"] == BASELINE_103_SERIES["total"]
    assert s["captain_minutes"] == BASELINE_103_SERIES["captain"]
    assert s["worker_minutes"] == BASELINE_103_SERIES["worker"]
    assert s["pm_minutes"] == BASELINE_103_SERIES["pm"]

    # 3계열 합 항등 — PM이 유도값이므로 이 항등이 정의 그 자체다
    assert s["pm_minutes"] + s["worker_minutes"] + s["captain_minutes"] == s["total_minutes"]

    # PM 음수 금지 (clamp 없이도 양수인 실데이터)
    assert s["pm_minutes"] > 0
    assert s["worker_clamped_count"] == 0

    # 측정 신호 — 「워커 0분」이 아니라 「측정됨」
    assert s["worker_measured"] is True


def test_ts101_three_series_stage_breakdown(fx_103):
    """[T103/L1-R16] 103 단계별 3계열이 행별 분해의 단순 합이며 단계마다 항등이 성립한다."""
    from dashboard.backend.stats import task_static_stats

    stages = task_static_stats(fx_103)["stages"]
    assert [g["stage"] for g in stages] == [name for name, *_ in BASELINE_103_STAGES]

    for group, (name, total, pm, worker, captain, measured) in zip(stages, BASELINE_103_STAGES):
        assert group["total_minutes"] == total, f"{name} 총 소요"
        assert group["pm_minutes"] == pm, f"{name} PM"
        assert group["worker_minutes"] == worker, f"{name} 워커"
        assert group["captain_minutes"] == captain, f"{name} 캡틴"
        assert group["pm_minutes"] + group["worker_minutes"] + group["captain_minutes"] == total
        assert group["worker_measured"] is measured, f"{name} 측정 신호"


# ── TS-102: 축퇴 규칙 — 미기록 태스크는 기존 2계열과 항등 ────────────────────

def test_ts102_degenerate_to_two_series_when_unmeasured(fx_101):
    """[T103/L1-R16] 101(워커 전건 미기록) 총 425 = PM 105 + 워커 0 + 캡틴 320.

    기존 2계열 확정값(작업 105 / 대기 320, STATS-BASELINE.md §3.1)과 수치가 항등이어야 한다.
    """
    from dashboard.backend.stats import task_static_stats

    s = task_static_stats(fx_101)

    assert s["total_minutes"] == 425
    assert s["pm_minutes"] == 105
    assert s["worker_minutes"] == 0
    assert s["captain_minutes"] == 320

    # 축퇴 항등 — PM == 기존 작업, 캡틴 == 기존 대기
    assert s["pm_minutes"] == s["work_minutes"]
    assert s["captain_minutes"] == s["wait_minutes"]

    # 미기록은 「0분 측정」이 아니다 — FE가 「워커 미측정」을 표기할 신호
    assert s["worker_measured"] is False

    assert s["pm_label"] == "1시간 45분"
    assert s["worker_label"] == "0분"
    assert s["captain_label"] == "5시간 20분"


def test_ts102_degenerate_stage_breakdown_matches_two_series(fx_101):
    """[T103/L1-R16] 101 단계별로도 PM == 작업 · 캡틴 == 대기가 전건 성립한다."""
    from dashboard.backend.stats import task_static_stats

    for group in task_static_stats(fx_101)["stages"]:
        assert group["pm_minutes"] == group["work_minutes"], group["stage"]
        assert group["captain_minutes"] == group["wait_minutes"], group["stage"]
        assert group["worker_minutes"] == 0, group["stage"]
        assert group["worker_measured"] is False, group["stage"]


# ── TS-103: 「0」과 「미기록」 구분 ───────────────────────────────────────────

def test_ts103_recorded_zero_differs_from_unrecorded(fx_101):
    """[T103/L1-R16] worker_duration_minutes: 0은 「측정했으나 1분 미만」이다.

    계산값(워커 0)은 미기록과 같지만 worker_measured 신호가 다르다.
    """
    from dashboard.backend.stats import task_static_stats, worker_recorded

    assert worker_recorded({}) is None
    assert worker_recorded({"worker_duration_minutes": 0}) == 0
    assert worker_recorded({"worker_duration_minutes": 7}) == 7

    fx_zero = copy.deepcopy(fx_101)
    target = next(r for r in fx_zero["rows"] if r["row_id"] == 3)
    target["worker_duration_minutes"] = 0

    s = task_static_stats(fx_zero)

    # 수치는 미기록과 완전히 동일 — 축퇴가 깨지지 않는다
    assert (s["total_minutes"], s["pm_minutes"], s["worker_minutes"], s["captain_minutes"]) == (
        425, 105, 0, 320
    )
    # 신호만 다르다
    assert s["worker_measured"] is True

    rows = {r["row_id"]: r for r in s["rows"]}
    assert rows[3]["worker_measured"] is True
    assert rows[3]["worker_minutes"] == 0
    assert rows[4]["worker_measured"] is False


# ── TS-104: PM 음수 금지 — 상한 clamp ────────────────────────────────────────

def test_ts104_pm_never_negative_and_clamp_is_reported(fx_101):
    """[T103/L1-R16] 기록 워커가 행 소요를 넘으면 남은 몫으로 상한 clamp되고 그 사실이 보고된다."""
    from dashboard.backend.stats import series_split, task_static_stats

    # 소요 19분 행에 워커 999분을 주입 → 워커 19 / PM 0, 총합 항등 유지
    fx_over = copy.deepcopy(fx_101)
    target = next(r for r in fx_over["rows"] if r["row_id"] == 3)
    target["worker_duration_minutes"] = 999

    s = task_static_stats(fx_over)
    assert s["total_minutes"] == 425
    assert s["pm_minutes"] >= 0
    assert s["pm_minutes"] + s["worker_minutes"] + s["captain_minutes"] == 425
    assert s["worker_clamped_count"] == 1

    for row in s["rows"]:
        assert row["pm_minutes"] >= 0, row["row_id"]
        assert row["worker_minutes"] >= 0, row["row_id"]
        assert row["captain_minutes"] >= 0, row["row_id"]

    # 캡틴 행에 워커가 기록돼도 캡틴 몫을 잠식하지 않는다 (남은 몫 0 → 워커 0)
    split = series_split({"owner": "user", "worker_duration_minutes": 30}, 20)
    assert split == {
        "pm_minutes": 0,
        "worker_minutes": 0,
        "captain_minutes": 20,
        "worker_measured": True,
        "worker_clamped": True,
    }

    # 비 done 행(소요 None)은 3계열 전건 0 + 미측정
    unmeasured = series_split({"owner": "PM"}, None)
    assert unmeasured["pm_minutes"] == 0
    assert unmeasured["worker_measured"] is False


# ── TS-105: 워크플로우 집계의 3계열 승계 + 불변 확인 ─────────────────────────

def test_ts105_workflow_three_series_preserves_two_series(fx_cohort):
    """[T103/L1-R16] 동결 코호트(워커 전건 미기록)의 3계열이 2계열과 항등이며 대표값이 불변이다."""
    from dashboard.backend.stats import workflow_stats

    by_skill = {w["skill"]: w for w in workflow_stats(fx_cohort)}

    for skill, (n, median, wait_ratio, _) in BASELINE_WORKFLOWS.items():
        w = by_skill[skill]
        # 3계열 추가가 기존 대표값을 흔들지 않는다
        assert w["median_minutes"] == median, f"{skill} 중앙값 회귀"
        assert w["wait_ratio"] == wait_ratio, f"{skill} 대기 비중 회귀"
        # 축퇴 항등
        assert w["pm_minutes"] == w["work_minutes"], skill
        assert w["captain_minutes"] == w["wait_minutes"], skill
        assert w["worker_minutes"] == 0, skill
        assert w["worker_measured"] is False, skill

        for stage in w["stages"]:
            assert stage["pm_minutes"] == stage["work_minutes"], (skill, stage["stage"])
            assert stage["captain_minutes"] == stage["wait_minutes"], (skill, stage["stage"])
            assert stage["worker_minutes"] == 0, (skill, stage["stage"])


# ══════════════════════════════════════════════════════════════════════════════
# TS-120~TS-122 — 3계열 표시 문자열 소유권 (R-20, 구획 호버 지표)
# 라벨은 BE 단일 소유다(P-7). 여기서는 「라벨이 그 계열의 분과 맞는가」를 단정하며,
# format_duration 5규칙 자체는 TS-009가 리터럴로 이미 못박았다.
# 오라클은 stats.format_duration이 아니라 TASK.md §집계 기준 표시 규칙의 독립 재기술이다.
# ══════════════════════════════════════════════════════════════════════════════

def _spec_label(minutes: int | None) -> str:
    """표시 규칙의 독립 재기술 — 구현을 호출하지 않는 오라클 (self-confirming 금지)."""
    if minutes is None:
        return "—"
    if minutes < 60:
        return "%d분" % minutes
    if minutes % 60 == 0:
        return "%d시간" % (minutes // 60)
    return "%d시간 %d분" % (minutes // 60, minutes % 60)


# 103 동결본 단계별 3계열 라벨 — BASELINE_103_STAGES 분값의 리터럴 표기
BASELINE_103_STAGE_LABELS = [
    ("TASK", "1시간 55분", "0분", "0분", "1시간 55분"),
    ("ANALYSIS", "26분", "3분", "16분", "7분"),
    ("PLAN", "28분", "5분", "21분", "2분"),
    ("TEST-SCENARIO", "32분", "6분", "20분", "6분"),
    ("EXECUTE", "1시간 27분", "7분", "1시간 20분", "0분"),
    ("TEST", "11분", "2분", "9분", "0분"),
    ("CLOSE", "0분", "0분", "0분", "0분"),
]


def test_ts120_stage_layer_series_labels(fx_103):
    """[T103/L1-R20] 단계 층이 3계열 표시 문자열을 내려준다 — 103 실측 리터럴."""
    from dashboard.backend.stats import task_static_stats

    stages = task_static_stats(fx_103)["stages"]
    assert [g["stage"] for g in stages] == [name for name, *_ in BASELINE_103_STAGE_LABELS]

    for group, (name, total, pm, worker, captain) in zip(stages, BASELINE_103_STAGE_LABELS):
        assert group["total_label"] == total, f"{name} 총"
        assert group["pm_label"] == pm, f"{name} PM"
        assert group["worker_label"] == worker, f"{name} 워커"
        assert group["captain_label"] == captain, f"{name} 캡틴"


def test_ts120_stage_layer_labels_match_minutes(fx_101):
    """[T103/L1-R20] 축퇴 태스크(101)에서도 단계 층 라벨이 그 계열의 분과 일치한다."""
    from dashboard.backend.stats import task_static_stats

    for group in task_static_stats(fx_101)["stages"]:
        assert group["pm_label"] == _spec_label(group["pm_minutes"]), group["stage"]
        assert group["worker_label"] == _spec_label(group["worker_minutes"]), group["stage"]
        assert group["captain_label"] == _spec_label(group["captain_minutes"]), group["stage"]


def test_ts121_workflow_layer_series_labels(fx_cohort):
    """[T103/L1-R20] 워크플로우 층·그 단계 층이 3계열 라벨과 누적 총 라벨을 내려준다."""
    from dashboard.backend.stats import workflow_stats

    result = workflow_stats(fx_cohort)
    assert result, "동결 코호트가 비었다"

    for w in result:
        assert w["pm_label"] == _spec_label(w["pm_minutes"]), w["skill"]
        assert w["worker_label"] == _spec_label(w["worker_minutes"]), w["skill"]
        assert w["captain_label"] == _spec_label(w["captain_minutes"]), w["skill"]

        for stage in w["stages"]:
            tag = (w["skill"], stage["stage"])
            # 누적 총 = work + wait == pm + worker + captain (집계 기준 16 항등)
            assert stage["total_minutes"] == stage["work_minutes"] + stage["wait_minutes"], tag
            assert stage["total_minutes"] == (
                stage["pm_minutes"] + stage["worker_minutes"] + stage["captain_minutes"]
            ), tag
            assert stage["total_label"] == _spec_label(stage["total_minutes"]), tag
            assert stage["pm_label"] == _spec_label(stage["pm_minutes"]), tag
            assert stage["worker_label"] == _spec_label(stage["worker_minutes"]), tag
            assert stage["captain_label"] == _spec_label(stage["captain_minutes"]), tag
            # 중앙값은 누적 총과 별개 지표다 — 덮어쓰이지 않았음을 확인
            assert stage["median_label"] == _spec_label(stage["median_minutes"]), tag


def test_ts122_task_leadtime_inherits_series_labels(fx_cohort):
    """[T103/L1-R20] 태스크 막대(TaskLeadtime)가 태스크 층 3계열 수치·라벨을 승계한다."""
    from dashboard.backend.stats import workflow_stats

    by_id = {}
    for w in workflow_stats(fx_cohort):
        for task in w["tasks"]:
            by_id[task["task_id"]] = task
            assert (
                task["pm_minutes"] + task["worker_minutes"] + task["captain_minutes"]
                == task["total_minutes"]
            ), task["task_id"]
            assert task["pm_label"] == _spec_label(task["pm_minutes"]), task["task_id"]
            assert task["worker_label"] == _spec_label(task["worker_minutes"]), task["task_id"]
            assert task["captain_label"] == _spec_label(task["captain_minutes"]), task["task_id"]
            # 동결 코호트는 워커 전건 미기록 — 호버가 「미측정」을 말할 신호
            assert task["worker_measured"] is False, task["task_id"]

    # 101 실측(총 425 = PM 105 + 워커 0 + 캡틴 320)이 태스크 막대까지 그대로 도달한다
    t101 = by_id[FX_101_ID]
    assert (t101["total_label"], t101["pm_label"], t101["worker_label"], t101["captain_label"]) == (
        "7시간 5분", "1시간 45분", "0분", "5시간 20분"
    )


# ══════════════════════════════════════════════════════════════════════════════
# TS-130~TS-136 — 야간 시간대 보정 (R-21, 집계 기준 17)
# 캡틴 지시 2026-08-26: 「날이 다음 날로 바뀌는 경우 보정을 해서 00시~09시는 제외.
# 이 시간을 환경변수 등 어딘가에 정의해서 변경 가능하게.」 — TASK.md §확정된 설계 방향의
# 「근무시간 보정·야간 공백 제외는 적용하지 않는다」가 이 지시로 뒤집혔다.
#
# 기대값 원천은 STATS-BASELINE.md §4.4(보정 후 병기 절)와 아래 손계산이며,
# stats.py 출력을 되쓰지 않는다(self-confirming 금지).
# ══════════════════════════════════════════════════════════════════════════════

# 기본 제외 구간 — setting.default.json `quietHours` 기본값 `00:00~09:00`.
QUIET_DEFAULT = (0, 9 * 60)


def _state(created_at: str, rows: list[dict], status: str = "done") -> dict:
    """최소 state — 야간 보정 경로만 드러내는 합성 픽스처."""
    return {"created_at": created_at, "current_status": status, "skill": "opd", "rows": rows}


def _done(stage: str, timestamp: str, owner: str = "PM", **extra) -> dict:
    return {"stage": stage, "status": "done", "timestamp": timestamp, "owner": owner, **extra}


# ── TS-130: 여러 밤 걸침 ─────────────────────────────────────────────────────

def test_ts130_multiple_nights_are_all_excluded():
    """[T103/L1-R21] 30시간짜리 행에서 두 밤이 모두 빠진다 (집계 기준 17).

    손계산 — `08-01 10:00` → `08-02 16:00`은 1,800분이다. 겹치는 야간은
    `08-02 00:00~09:00` 한 밤(540분)뿐이므로 1,260분이다.
    `08-03 16:00`까지 늘리면 `08-03 00:00~09:00`이 더해져 두 밤(1,080분)이 빠진다.
    """
    from dashboard.backend.stats import quiet_overlap_minutes, task_static_stats

    one_night = _state("2026-08-01 10:00", [_done("EXECUTE", "2026-08-02 16:00")])
    two_nights = _state("2026-08-01 10:00", [_done("EXECUTE", "2026-08-03 16:00")])

    assert task_static_stats(one_night)["total_minutes"] == 1800
    assert task_static_stats(one_night, QUIET_DEFAULT)["total_minutes"] == 1800 - 540

    assert task_static_stats(two_nights)["total_minutes"] == 1800 + 1440
    assert task_static_stats(two_nights, QUIET_DEFAULT)["total_minutes"] == 3240 - 1080

    # 겹침 계산 자체도 직접 못박는다 — 상위 집계를 거치지 않는 경로다
    assert quiet_overlap_minutes(
        datetime(2026, 8, 1, 10, 0), datetime(2026, 8, 3, 16, 0), QUIET_DEFAULT
    ) == 1080


# ── TS-131: 미걸침 — 하루 안에 끝난 태스크는 불변 ────────────────────────────

def test_ts131_same_day_task_is_unchanged(fx_101):
    """[T103/L1-R21] `101`은 하루 안에 끝나 야간과 겹치지 않는다 — 보정 전후가 항등이다.

    [MUST] STATS-BASELINE.md §3.1: 총 425분 = 작업 105분 + 대기 320분.
    완료기준 (2)의 A 블록 확정값이 야간 보정으로 흔들리지 않아야 한다.
    """
    from dashboard.backend.stats import task_static_stats

    plain = task_static_stats(fx_101)
    quiet = task_static_stats(fx_101, QUIET_DEFAULT)

    assert quiet["total_minutes"] == 425
    assert quiet["pm_minutes"] == 105
    assert quiet["worker_minutes"] == 0
    assert quiet["captain_minutes"] == 320
    assert quiet["work_minutes"] == 105
    assert quiet["wait_minutes"] == 320

    # 단계 7행까지 전건 항등 — 어느 행도 야간을 건너지 않는다
    assert [(g["stage"], g["total_minutes"]) for g in quiet["stages"]] == \
           [(g["stage"], g["total_minutes"]) for g in plain["stages"]]


# ── TS-132: 보정 끔 ──────────────────────────────────────────────────────────

def test_ts132_disabled_keeps_wall_clock(fx_cohort):
    """[T103/L1-R21] `quiet_hours=None`(설정 `enabled: false`)이면 벽시계 그대로다.

    [MUST] STATS-BASELINE.md §4.1: opd 799 / opds 276 / opp 75 (보정 전 확정값).
    끄는 수단이 실제로 종전 수치를 되돌려야 캡틴이 두 기준을 대조할 수 있다.
    """
    from dashboard.backend.stats import workflow_stats

    medians = {w["skill"]: w["median_minutes"] for w in workflow_stats(fx_cohort, None)}
    assert medians == {"opd": 799, "opds": 276, "opp": 75}


# ── TS-133: 경계값 — 반개구간 `[시작, 끝)` ───────────────────────────────────

def test_ts133_end_boundary_is_exclusive():
    """[T103/L1-R21] 끝 정각(`09:00`)은 제외 구간에 포함되지 않는다.

    손계산 — `09:00 → 10:00`은 제외 0분(60분 그대로). `08:00 → 10:00`은 앞의
    60분만 야간이라 60분이 빠진다. `08:59 → 09:00`은 1분이 통째로 야간이다.
    """
    from dashboard.backend.stats import quiet_overlap_minutes

    at = lambda h, m: datetime(2026, 8, 2, h, m)   # noqa: E731

    assert quiet_overlap_minutes(at(9, 0), at(10, 0), QUIET_DEFAULT) == 0
    assert quiet_overlap_minutes(at(8, 0), at(10, 0), QUIET_DEFAULT) == 60
    assert quiet_overlap_minutes(at(8, 59), at(9, 0), QUIET_DEFAULT) == 1
    # 시작 정각은 포함된다 — `[시작, 끝)`이므로 자정 1분도 제외 대상이다
    assert quiet_overlap_minutes(
        datetime(2026, 8, 1, 23, 59), at(0, 1), QUIET_DEFAULT
    ) == 1


# ── TS-134: 워커 소요는 보정 대상이 아니다 ──────────────────────────────────

def test_ts134_worker_minutes_are_never_reduced():
    """[T103/L1-R21] 야간에 실제로 돈 워커 시간은 깎이지 않는다 (캡틴 지시).

    손계산 — `08-01 22:00` → `08-02 12:00`은 840분이고 야간 겹침은 540분
    (`00:00~09:00`)이다. 워커가 600분을 돌았다면 워커 몫을 먼저 확보하므로
    워커 600 그대로, 남은 PM 240에서 540을 빼려다 0으로 clamp된다 → 총 600.
    보정분을 워커에서 뺐다면 총이 300이 되어 실제보다 짧아진다.
    """
    from dashboard.backend.stats import task_static_stats

    state = _state("2026-08-01 22:00", [
        _done("EXECUTE", "2026-08-02 12:00", worker_duration_minutes=600),
    ])

    plain = task_static_stats(state)
    assert (plain["total_minutes"], plain["worker_minutes"], plain["pm_minutes"]) == (840, 600, 240)

    quiet = task_static_stats(state, QUIET_DEFAULT)
    assert quiet["worker_minutes"] == 600, "워커 소요가 보정으로 깎였다"
    assert quiet["pm_minutes"] == 0
    assert quiet["captain_minutes"] == 0
    assert quiet["total_minutes"] == 600


# ── TS-135: 3계열 항등 유지 ─────────────────────────────────────────────────

def test_ts135_three_series_identity_holds_under_quiet_hours(fx_cohort, fx_103):
    """[T103/L1-R21] 보정 후에도 총 = PM + 워커 + 캡틴이다 (집계 기준 16 항등).

    제외분을 어느 계열에서 빼든 합이 어긋나면 스택 막대가 총과 맞지 않는다.
    코호트 21건 + 워커 기록 태스크(103) 전건에서 4층(행·단계·태스크·워크플로우)을 단정한다.
    """
    from dashboard.backend.stats import row_durations, task_static_stats, workflow_stats

    for state in [*fx_cohort, fx_103]:
        static = task_static_stats(state, QUIET_DEFAULT)
        assert static["pm_minutes"] + static["worker_minutes"] + static["captain_minutes"] \
            == static["total_minutes"]
        # 2계열도 항등을 유지한다 — work = PM + 워커, wait = 캡틴
        assert static["work_minutes"] == static["pm_minutes"] + static["worker_minutes"]
        assert static["wait_minutes"] == static["captain_minutes"]

        for group in static["stages"]:
            assert group["pm_minutes"] + group["worker_minutes"] + group["captain_minutes"] \
                == group["total_minutes"], group["stage"]

        for item in row_durations(state, QUIET_DEFAULT):
            if item["duration_minutes"] is None:
                continue
            assert item["pm_minutes"] + item["worker_minutes"] + item["captain_minutes"] \
                == item["duration_minutes"], item["row_id"]
            assert item["pm_minutes"] >= 0 and item["captain_minutes"] >= 0

    for entry in workflow_stats(fx_cohort, QUIET_DEFAULT):
        assert entry["pm_minutes"] + entry["worker_minutes"] + entry["captain_minutes"] \
            == entry["work_minutes"] + entry["wait_minutes"], entry["skill"]


# ── TS-136: 코호트 대표값 이동 + 자정 넘는 구간 + 표면화 ────────────────────

# STATS-BASELINE.md §4.4 — 보정(`00:00~09:00`) 후 skill: (n, median, wait_ratio)
BASELINE_QUIET_WORKFLOW = {
    "opd": (7, 425, 23),
    "opds": (10, 276, 5),
    "opp": (4, 75, 54),
}


def test_ts136_cohort_medians_move_to_baseline(fx_cohort):
    """[T103/L1-R21] 동결 코호트 21건의 중앙값이 보정 후 기준선과 일치한다.

    [MUST] STATS-BASELINE.md §4.4 — opd 799 → 425(-47%), opds·opp는 불변.
    """
    from dashboard.backend.stats import workflow_stats

    entries = {w["skill"]: w for w in workflow_stats(fx_cohort, QUIET_DEFAULT)}
    for skill, (n, median, wait_ratio) in BASELINE_QUIET_WORKFLOW.items():
        assert entries[skill]["n"] == n, skill
        assert entries[skill]["median_minutes"] == median, f"{skill} 중앙값"
        assert entries[skill]["wait_ratio"] == wait_ratio, f"{skill} 대기 비중"


def test_ts136_wrapping_window_and_surfacing():
    """[T103/L1-R21] 자정을 넘는 구간(`22:00~06:00`)과 적용 여부 표면화.

    손계산 — `22:00~06:00`은 하루 480분이다. `08-01 12:00` → `08-02 12:00`(1,440분)에서
    겹치는 야간은 `08-01 22:00 → 08-02 06:00` 480분이므로 960분이 남는다.
    """
    from dashboard.backend.stats import (
        format_quiet_hours,
        quiet_overlap_minutes,
        task_static_stats,
    )

    wrapping = (22 * 60, 6 * 60)
    assert quiet_overlap_minutes(
        datetime(2026, 8, 1, 12, 0), datetime(2026, 8, 2, 12, 0), wrapping
    ) == 480

    state = _state("2026-08-01 12:00", [_done("EXECUTE", "2026-08-02 12:00")])
    assert task_static_stats(state, wrapping)["total_minutes"] == 960

    # 적용 여부·구간이 응답에 실린다 — 같은 태스크가 두 수치로 보이는 혼란을 막는다
    assert format_quiet_hours(None) == ""
    assert format_quiet_hours(QUIET_DEFAULT) == "00:00~09:00"
    assert format_quiet_hours(wrapping) == "22:00~06:00"

    applied = task_static_stats(state, QUIET_DEFAULT)
    assert applied["quiet_hours_applied"] is True
    assert applied["quiet_hours_label"] == "00:00~09:00"

    off = task_static_stats(state, None)
    assert off["quiet_hours_applied"] is False
    assert off["quiet_hours_label"] == ""
