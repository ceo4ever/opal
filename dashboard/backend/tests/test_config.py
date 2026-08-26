"""
@header {
  "module": "tests.test_config",
  "layer": "test",
  "domain": "console",
  "description": "config.load_config()의 prewarm_projects 파싱·타입 가드 테스트(T060 F-1, RED). 5variant: 키 부재/빈 배열/문자열(비-list)/dict(비-list)/정상 배열(경로 2개+비str 원소 혼합) → 부재·빈·비-list는 예외 없이 []로 폴백, 정상 배열은 str 원소만 로드된다(H-4). CONFIG_PATH를 tmp_path로 monkeypatch하여 실제 ~/.opal/console.config.json과 격리. [T061] config.save_config(머지 보존, H-3)·config._atomic_write_json(temp+os.replace 원자 쓰기·동시 쓰기 직렬화, H-2) 검증. save_project_local 계약(TestSaveProjectLocal)은 T061 범위 축소로 프로젝트 로컬 설정 편집이 제외되어 삭제됨. [T103 R-21] TestLoadQuietHours — 야간 제외 구간(집계 기준 17)의 2층 머지 계약. 두 층 부재 시 기본 켬(00:00~09:00), 전역 끔·전역 구간 변경·로컬 하위 키 우선(전역 잔존)·로컬 끔·start==end 무효화·형식 위반 9variant 폴백·파손 JSON 무예외·캐시 키 서명 분리. OPAL_SETTING_PATH를 tmp로 monkeypatch해 실제 ~/.opal/setting.json과 격리한다. TestQuietHoursSeedDefault — setting.default.json 시드와 코드 기본값의 일치 + install-mac.sh SEED_KEYS 배선. [호칭] TestLoadOwnerName — config.load_owner_name의 정상 읽기 + 폴백 4경로(파일 부재·키 부재·값 공란·읽기 실패)를 단정한다. IDENTITY_PATH를 tmp로 monkeypatch해 실행 머신의 ~/.opal/identity.md와 격리하며, 폴백값이 특정인이 아니라 중립 호칭(\"사용자\")임을 못박는다.",
  "exports": ["TestConfigPrewarmProjects", "TestSaveConfigMergePreservation", "TestAtomicWriteJson", "TestLoadQuietHours", "TestQuietHoursSeedDefault"],
  "depends": ["config"],
  "task": "061",
  "scenarios": ["S-2", "S-3", "TS-138"],
  "changelog": [
    "2026-08-26 T103 R-21: TestLoadQuietHours(9케이스) + TestQuietHoursSeedDefault(2케이스) 추가 — 야간 제외 구간 2층 머지·시드 일치. 기존 T060/T061 케이스 무변경",
    "2026-07-14 T061 RED: config.save_config 머지 보존(S-3)·config._atomic_write_json 원자 쓰기+동시성(S-2)·config.save_project_local 원자 쓰기 실패 테스트 추가 — 구현 전 RED 트랙(red-first.md), 작성자(opal-test-agent)≠구현자(opal-be-agent)",
    "2026-07-14 T061 범위 축소: TestSaveProjectLocal 클래스 삭제(save_project_local 제거에 따른 계약 삭제) — TestSaveConfigMergePreservation·TestAtomicWriteJson은 유지"
  ]
}
"""
from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest


def _write_config(tmp_path: Path, data: dict) -> Path:
    """tmp_path에 console.config.json 형식의 JSON 파일을 작성하고 경로를 반환."""
    config_file = tmp_path / "console.config.json"
    config_file.write_text(json.dumps(data), encoding="utf-8")
    return config_file


def _load_with_isolated_config_path(monkeypatch: pytest.MonkeyPatch, config_path: Path):
    """config.CONFIG_PATH를 tmp 경로로 격리한 뒤 load_config()를 호출."""
    import dashboard.backend.config as config_module

    monkeypatch.setattr(config_module, "CONFIG_PATH", config_path)
    return config_module.load_config()


class TestConfigPrewarmProjects:
    """[T060/L1-F1] ConsoleConfig.prewarm_projects 5variant 파싱·타입 가드 (F-1 AC, H-4, RED).

    대상: config.py `ConsoleConfig.prewarm_projects` 필드 + `load_config()` 타입 가드
    (미구현 — PLAN §3.1.2 `_coerce_str_list` 헬퍼 대상). 현재는 필드 자체가 없으므로
    `cfg.prewarm_projects` 접근 시 AttributeError가 정상(RED)이다.
    """

    def test_key_absent_defaults_to_empty_list(self, tmp_path, monkeypatch):
        """[T060/L1-F1] prewarm_projects 키 부재 → []."""
        config_path = _write_config(tmp_path, {"scan_roots": ["/x"]})
        cfg = _load_with_isolated_config_path(monkeypatch, config_path)
        assert cfg.prewarm_projects == []

    def test_empty_list_stays_empty(self, tmp_path, monkeypatch):
        """[T060/L1-F1] prewarm_projects 빈 배열 → []."""
        config_path = _write_config(tmp_path, {"prewarm_projects": []})
        cfg = _load_with_isolated_config_path(monkeypatch, config_path)
        assert cfg.prewarm_projects == []

    def test_string_value_falls_back_to_empty_list(self, tmp_path, monkeypatch):
        """[T060/L1-F1] prewarm_projects가 문자열(비-list) → 예외 없이 []로 폴백(H-4)."""
        config_path = _write_config(tmp_path, {"prewarm_projects": "/not/a/list"})
        cfg = _load_with_isolated_config_path(monkeypatch, config_path)
        assert cfg.prewarm_projects == []

    def test_dict_value_falls_back_to_empty_list(self, tmp_path, monkeypatch):
        """[T060/L1-F1] prewarm_projects가 dict(비-list) → 예외 없이 []로 폴백(H-4)."""
        config_path = _write_config(tmp_path, {"prewarm_projects": {"a": 1}})
        cfg = _load_with_isolated_config_path(monkeypatch, config_path)
        assert cfg.prewarm_projects == []

    def test_valid_list_loads_str_elements_only(self, tmp_path, monkeypatch):
        """[T060/L1-F1] 정상 배열(경로 2개 + 비str 원소 혼합) → str 원소만 로드."""
        config_path = _write_config(
            tmp_path,
            {"prewarm_projects": ["/proj/one", "/proj/two", 123, None]},
        )
        cfg = _load_with_isolated_config_path(monkeypatch, config_path)
        assert cfg.prewarm_projects == ["/proj/one", "/proj/two"]


# ── [T061] config.save_config / _atomic_write_json ───────────────────────────
# PLAN.md §3.1.2 설계 시그니처 대상.


def _isolate_config_path(monkeypatch: pytest.MonkeyPatch, config_path: Path):
    """config.CONFIG_PATH를 tmp 경로로 격리(로드 없이 몽키패치만 수행)하고 config 모듈을 반환."""
    import dashboard.backend.config as config_module

    monkeypatch.setattr(config_module, "CONFIG_PATH", config_path)
    return config_module


class TestSaveConfigMergePreservation:
    """[T061/L1-R3] config.save_config 머지 보존 — 부분 갱신 시 기존/미지 키 유실 금지 (H-3, RED, S-3).

    대상: config.save_config(updates: dict) -> dict (미구현 — PLAN §3.1.2 대상).
    현재는 함수 자체가 없으므로 AttributeError가 정상(RED)이다.
    """

    def test_partial_update_preserves_existing_keys(self, tmp_path, monkeypatch):
        """[T061/L1-R3] (a) prewarm_projects만 갱신 → scan_roots/scan_depth/exclude 등 기존 키 보존."""
        config_path = _write_config(
            tmp_path,
            {
                "scan_roots": ["/tmp/ws"],
                "scan_depth": 2,
                "exclude": ["backup"],
                "prewarm_projects": [],
                "future_key": "keep-me",
            },
        )
        config_module = _isolate_config_path(monkeypatch, config_path)
        snapshot = config_module.save_config({"prewarm_projects": ["/tmp/ws/proj-a"]})

        assert snapshot["prewarm_projects"] == ["/tmp/ws/proj-a"]
        assert snapshot["scan_roots"] == ["/tmp/ws"]
        assert snapshot["scan_depth"] == 2
        assert snapshot["exclude"] == ["backup"]
        assert snapshot["future_key"] == "keep-me", "미지 future 키가 갱신 후 유실됨(H-3)"

    def test_existing_key_change_reflected(self, tmp_path, monkeypatch):
        """[T061/L1-R3] (b) scan_depth 기존 키 변경 → 반영."""
        config_path = _write_config(
            tmp_path,
            {"scan_roots": ["/tmp/ws"], "scan_depth": 2, "future_key": "keep-me"},
        )
        config_module = _isolate_config_path(monkeypatch, config_path)
        snapshot = config_module.save_config({"scan_depth": 5})

        assert snapshot["scan_depth"] == 5
        assert snapshot["future_key"] == "keep-me"

    def test_partial_update_reload_from_disk_matches(self, tmp_path, monkeypatch):
        """[T061/L1-R3] (c) 부분 갱신 후 재로드(파일 재읽기) 시 갱신값+future_key 일치."""
        config_path = _write_config(
            tmp_path,
            {
                "scan_roots": ["/tmp/ws"],
                "prewarm_projects": [],
                "future_key": "keep-me",
            },
        )
        config_module = _isolate_config_path(monkeypatch, config_path)
        config_module.save_config({"prewarm_projects": ["/tmp/ws/proj-a"]})

        reloaded = json.loads(config_path.read_text(encoding="utf-8"))
        assert reloaded["prewarm_projects"] == ["/tmp/ws/proj-a"]
        assert reloaded["scan_roots"] == ["/tmp/ws"]
        assert reloaded["future_key"] == "keep-me"


class TestAtomicWriteJson:
    """[T061/L2-R1] config._atomic_write_json — temp 파일 + os.replace 원자적 쓰기 (H-2, RED, S-2).

    대상: config._atomic_write_json(path, data) -> None + config.save_config의
    동시 쓰기 직렬화(_WRITE_LOCK) (미구현 — PLAN §3.1.2 대상).
    """

    def test_writes_valid_json_and_no_temp_leftover(self, tmp_path):
        """[T061/L2-R1] 쓰기 후 대상 파일 파스 성공 + temp 잔존 파일 0."""
        import dashboard.backend.config as config_module

        target = tmp_path / "atomic-target.json"
        config_module._atomic_write_json(target, {"a": 1, "b": [1, 2]})

        assert target.exists()
        loaded = json.loads(target.read_text(encoding="utf-8"))
        assert loaded == {"a": 1, "b": [1, 2]}

        leftovers = [p for p in tmp_path.iterdir() if ".tmp." in p.name]
        assert leftovers == [], f"temp 파일 잔존: {leftovers}"

    def test_concurrent_save_config_no_key_loss(self, tmp_path, monkeypatch):
        """[T061/L2-R1] 스레드 2개 동시 save_config(서로 다른 키) → 두 갱신 모두 반영,
        future_key 보존, JSON 파스 성공(파손 0), temp 잔존 0."""
        config_path = _write_config(
            tmp_path,
            {"scan_roots": ["/tmp/ws"], "future_key": "keep-me"},
        )
        config_module = _isolate_config_path(monkeypatch, config_path)

        barrier = threading.Barrier(2)
        errors: list[Exception] = []

        def _writer(update: dict) -> None:
            try:
                barrier.wait(timeout=5)
                config_module.save_config(update)
            except Exception as exc:  # pragma: no cover - 진단용
                errors.append(exc)

        t1 = threading.Thread(target=_writer, args=({"scan_depth": 9},))
        t2 = threading.Thread(target=_writer, args=({"exclude": ["node_modules"]},))
        t1.start()
        t2.start()
        t1.join(timeout=10)
        t2.join(timeout=10)

        assert not errors, f"동시 쓰기 중 예외 발생: {errors}"

        # 파손 없이 파스 가능해야 함 — 두 갱신 모두 반영(키 유실 0)
        reloaded = json.loads(config_path.read_text(encoding="utf-8"))
        assert reloaded["scan_depth"] == 9, "동시 쓰기 중 한쪽 키가 유실됨(H-2)"
        assert reloaded["exclude"] == ["node_modules"], "동시 쓰기 중 한쪽 키가 유실됨(H-2)"
        assert reloaded["future_key"] == "keep-me"

        leftovers = [p for p in tmp_path.iterdir() if ".tmp." in p.name]
        assert leftovers == [], f"temp 파일 잔존: {leftovers}"


# ══════════════════════════════════════════════════════════════════════════════
# [T103 R-21] 야간 제외 구간 2층 머지 (집계 기준 17)
# 캡틴 지시 2026-08-26 — 「이 시간을 환경변수 등 어딘가에 정의해서 변경 가능하게.」
# 기존 부트스트랩과 같은 2층(전역 ~/.opal/setting.json + 프로젝트 .opal/setting.local.json)을
# 그대로 쓴다. 여기서는 「끄는 수단」과 「시간대 변경」이 두 층 모두에서 듣는지를 단정한다.
# ══════════════════════════════════════════════════════════════════════════════

class TestLoadQuietHours:
    """[T103/L1-R21] config.load_quiet_hours — 2층 머지·기본값·형식 내성."""

    @staticmethod
    def _isolate(monkeypatch, tmp_path, global_setting=None, local_setting=None):
        """전역·프로젝트 설정을 tmp로 격리하고 프로젝트 경로를 반환. None이면 파일 미생성."""
        import dashboard.backend.config as config_module

        global_path = tmp_path / "setting.json"
        if global_setting is not None:
            global_path.write_text(json.dumps(global_setting), encoding="utf-8")
        monkeypatch.setattr(config_module, "OPAL_SETTING_PATH", global_path)

        project = tmp_path / "project"
        if local_setting is not None:
            (project / ".opal").mkdir(parents=True, exist_ok=True)
            (project / ".opal" / "setting.local.json").write_text(
                json.dumps(local_setting), encoding="utf-8"
            )
        return str(project)

    def test_absent_everywhere_defaults_to_on(self, tmp_path, monkeypatch):
        """[T103/L1-R21] 두 층 모두 키가 없으면 기본은 **켬** — `00:00~09:00`.

        기존 설치의 setting.json에는 quietHours가 없다. 그 상태에서도 캡틴이 지시한
        기본(켬)이 적용돼야 한다.
        """
        from dashboard.backend.config import load_quiet_hours

        project = self._isolate(monkeypatch, tmp_path)
        assert load_quiet_hours(project) == (0, 540)
        assert load_quiet_hours(None) == (0, 540)

    def test_global_disables_correction(self, tmp_path, monkeypatch):
        """[T103/L1-R21] 전역 `enabled: false` → None (보정 끔)."""
        from dashboard.backend.config import load_quiet_hours

        project = self._isolate(
            monkeypatch, tmp_path, global_setting={"quietHours": {"enabled": False}}
        )
        assert load_quiet_hours(project) is None

    def test_global_changes_window(self, tmp_path, monkeypatch):
        """[T103/L1-R21] 전역에서 시간대를 바꾸면 그대로 반영된다."""
        from dashboard.backend.config import load_quiet_hours

        project = self._isolate(
            monkeypatch,
            tmp_path,
            global_setting={"quietHours": {"enabled": True, "start": "23:30", "end": "07:15"}},
        )
        assert load_quiet_hours(project) == (23 * 60 + 30, 7 * 60 + 15)

    def test_project_local_overrides_global(self, tmp_path, monkeypatch):
        """[T103/L1-R21] 로컬 우선 — 로컬에 없는 하위 키는 전역이 살아남는다."""
        from dashboard.backend.config import load_quiet_hours

        project = self._isolate(
            monkeypatch,
            tmp_path,
            global_setting={"quietHours": {"enabled": True, "start": "01:00", "end": "08:00"}},
            local_setting={"quietHours": {"end": "10:00"}},
        )
        # end만 덮였고 start는 전역 01:00이 유지된다
        assert load_quiet_hours(project) == (60, 600)

    def test_project_local_can_turn_it_off(self, tmp_path, monkeypatch):
        """[T103/L1-R21] 전역이 켬이어도 프로젝트에서 끌 수 있다."""
        from dashboard.backend.config import load_quiet_hours

        project = self._isolate(
            monkeypatch,
            tmp_path,
            global_setting={"quietHours": {"enabled": True, "start": "00:00", "end": "09:00"}},
            local_setting={"quietHours": {"enabled": False}},
        )
        assert load_quiet_hours(project) is None
        # 프로젝트 경로를 주지 않으면 로컬을 읽지 않으므로 전역이 그대로다
        assert load_quiet_hours(None) == (0, 540)

    def test_equal_start_and_end_means_no_window(self, tmp_path, monkeypatch):
        """[T103/L1-R21] `시작 == 끝`이면 제외할 구간이 없다 → None."""
        from dashboard.backend.config import load_quiet_hours

        project = self._isolate(
            monkeypatch,
            tmp_path,
            global_setting={"quietHours": {"enabled": True, "start": "09:00", "end": "09:00"}},
        )
        assert load_quiet_hours(project) is None

    @pytest.mark.parametrize(
        "bad", ["", "9", "09:60", "25:00", "abc", "09-00", None, 900, {"h": 9}]
    )
    def test_malformed_values_fall_back_to_default(self, tmp_path, monkeypatch, bad):
        """[T103/L1-R21] 형식 위반 값은 예외 없이 기본 구간으로 폴백한다."""
        from dashboard.backend.config import load_quiet_hours

        project = self._isolate(
            monkeypatch,
            tmp_path,
            global_setting={"quietHours": {"enabled": True, "start": bad, "end": "09:00"}},
        )
        assert load_quiet_hours(project) == (0, 540)

    def test_broken_json_does_not_raise(self, tmp_path, monkeypatch):
        """[T103/L1-R21] 파손·빈 설정 파일은 예외를 던지지 않고 기본으로 폴백한다."""
        import dashboard.backend.config as config_module
        from dashboard.backend.config import load_quiet_hours

        global_path = tmp_path / "setting.json"
        global_path.write_text("{ not json", encoding="utf-8")
        monkeypatch.setattr(config_module, "OPAL_SETTING_PATH", global_path)

        project = tmp_path / "project"
        (project / ".opal").mkdir(parents=True)
        (project / ".opal" / "setting.local.json").write_text("", encoding="utf-8")

        assert load_quiet_hours(str(project)) == (0, 540)

    def test_cache_token_separates_settings(self):
        """[T103/L1-R21] 캐시 키 서명이 구간별로 갈린다 — 설정 변경이 캐시에 갇히지 않는다."""
        from dashboard.backend.config import quiet_hours_token

        assert quiet_hours_token(None) == "off"
        assert quiet_hours_token((0, 540)) == "0-540"
        assert quiet_hours_token((0, 540)) != quiet_hours_token((0, 600))


class TestQuietHoursSeedDefault:
    """[T103/R-21] setting.default.json 시드가 캡틴 지시와 일치한다."""

    def test_seed_matches_captain_directive(self):
        """[T103/L1-R21] 시드 기본값은 켬 + `00:00~09:00`이고 `_help`를 갖춘다."""
        from dashboard.backend.config import DEFAULT_QUIET_HOURS

        repo_root = Path(__file__).resolve().parents[3]
        seed = json.loads(
            (repo_root / "opal" / "core" / "setting.default.json").read_text(encoding="utf-8")
        )

        quiet = seed["quietHours"]
        assert quiet["enabled"] is True
        assert quiet["start"] == "00:00"
        assert quiet["end"] == "09:00"
        assert quiet["_help"], "기존 키들처럼 _help 안내가 있어야 한다"

        # 코드 기본값과 시드가 어긋나면 설치 여부에 따라 수치가 갈린다
        assert {k: v for k, v in quiet.items() if k != "_help"} == DEFAULT_QUIET_HOURS

    def test_installer_seeds_the_key(self):
        """[T103/L1-R21] install-mac.sh SEED_KEYS에 quietHours가 실려 있다.

        키별 독립 판정이므로 기존 사용자의 setting.json에도 멱등하게 주입된다.
        """
        repo_root = Path(__file__).resolve().parents[3]
        script = (repo_root / "scripts" / "install-mac.sh").read_text(encoding="utf-8")
        assert "SEED_KEYS = ['models', 'shardPolicy', 'quietHours']" in script


# ══════════════════════════════════════════════════════════════════════════════
# [호칭 하드코딩 제거] config.load_owner_name — 화면 호칭의 단일 로더
# 콘솔 화면에 특정 호칭이 박혀 있으면 다른 사용자에게 남의 호칭이 뜬다. 원천은
# `~/.opal/identity.md` frontmatter의 `owner_name`이며, **읽지 못한 모든 경우**는
# 중립 호칭("사용자")으로 폴백하고 예외를 밖으로 던지지 않아야 한다.
# ══════════════════════════════════════════════════════════════════════════════

class TestLoadOwnerName:
    """[호칭] config.load_owner_name — 정상 읽기 + 폴백 4경로."""

    @staticmethod
    def _isolate(monkeypatch, tmp_path, content=None, name="identity.md"):
        """identity.md를 tmp로 격리. content가 None이면 **파일을 만들지 않는다**."""
        import dashboard.backend.config as config_module

        path = tmp_path / name
        if content is not None:
            path.write_text(content, encoding="utf-8")
        monkeypatch.setattr(config_module, "IDENTITY_PATH", path)
        return path

    def test_reads_owner_name_from_frontmatter(self, tmp_path, monkeypatch):
        """[호칭] frontmatter의 owner_name을 그대로 읽는다 (폴백 아님)."""
        from dashboard.backend.config import load_owner_name

        self._isolate(
            monkeypatch,
            tmp_path,
            "---\nname: 알투\nowner_name: 홍길동\ntone: 존댓말\n---\n\n# 알투\n본문의 owner_name: 미끼\n",
        )
        assert load_owner_name() == "홍길동"

    def test_missing_file_falls_back(self, tmp_path, monkeypatch):
        """[호칭] 폴백 ① 파일 부재 → "사용자". 예외를 던지지 않는다."""
        from dashboard.backend.config import load_owner_name

        path = self._isolate(monkeypatch, tmp_path, content=None)
        assert not path.exists()
        assert load_owner_name() == "사용자"

    def test_missing_key_falls_back(self, tmp_path, monkeypatch):
        """[호칭] 폴백 ② frontmatter는 있으나 owner_name 키가 없다 → "사용자"."""
        from dashboard.backend.config import load_owner_name

        self._isolate(monkeypatch, tmp_path, "---\nname: 알투\ntone: 존댓말\n---\n\n# 알투\n")
        assert load_owner_name() == "사용자"

    @pytest.mark.parametrize("raw", ["owner_name:", "owner_name: ", 'owner_name: ""', "owner_name: ''"])
    def test_blank_value_falls_back(self, tmp_path, monkeypatch, raw):
        """[호칭] 폴백 ③ 값이 공란(따옴표 빈 값 포함) → "사용자"."""
        from dashboard.backend.config import load_owner_name

        self._isolate(monkeypatch, tmp_path, f"---\nname: 알투\n{raw}\n---\n")
        assert load_owner_name() == "사용자"

    def test_unreadable_source_falls_back(self, tmp_path, monkeypatch):
        """[호칭] 폴백 ④ 읽기·파싱 실패(경로가 디렉토리) → "사용자", 예외 전파 0."""
        import dashboard.backend.config as config_module
        from dashboard.backend.config import load_owner_name

        directory = tmp_path / "identity.md"
        directory.mkdir()
        monkeypatch.setattr(config_module, "IDENTITY_PATH", directory)
        assert load_owner_name() == "사용자"

    def test_quoted_value_is_unwrapped(self, tmp_path, monkeypatch):
        """[호칭] 따옴표로 감싼 값은 벗겨서 읽는다 — 화면에 따옴표가 새지 않는다."""
        from dashboard.backend.config import load_owner_name

        self._isolate(monkeypatch, tmp_path, '---\nowner_name: "김 대표"\n---\n')
        assert load_owner_name() == "김 대표"

    def test_no_frontmatter_still_reads_key(self, tmp_path, monkeypatch):
        """[호칭] frontmatter 구분선이 없어도 본문에서 키를 찾는다(관대한 해석)."""
        from dashboard.backend.config import load_owner_name

        self._isolate(monkeypatch, tmp_path, "owner_name: 사장님\n")
        assert load_owner_name() == "사장님"

    def test_fallback_is_neutral_term(self):
        """[호칭] 폴백값은 특정인이 아니라 중립 호칭이다."""
        from dashboard.backend.config import DEFAULT_OWNER_NAME

        assert DEFAULT_OWNER_NAME == "사용자"
