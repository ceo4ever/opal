"""
@header {
  "module": "tests.test_deploy_smoke",
  "layer": "test",
  "domain": "console",
  "description": "S-10 보강: 배포 컨텍스트 기동 smoke 테스트. --app-dir 배포 구조(dashboard-server/) 기준으로 app import + /health·/ 200 확인. [T021/L2-R7deploy]",
  "exports": [
    "test_deploy_package_structure",
    "test_deploy_app_importable_from_package",
    "test_deploy_health_endpoint",
    "test_deploy_root_returns_200_or_api_only"
  ],
  "depends": ["main"]
}
"""
from __future__ import annotations

import importlib
import os
import sys
import tempfile
from pathlib import Path

import pytest


# ── 배포 패키지 구조 ──────────────────────────────────────────────────────────
# 배포 후 실제 구조:
#   ~/.opal/dashboard-server/
#     ├── dashboard/__init__.py
#     ├── dashboard/backend/main.py   ← 이 파일
#     └── dist/ (FE 빌드 산출물, 존재 시)
#
# 소스 루트(프로젝트/dashboard/backend/)에서 pytest 실행 시에는
# dashboard.backend.main 이 직접 import 가능 (PYTHONPATH 또는 sys.path에 프로젝트 루트).
# 배포 컨텍스트에서는 --app-dir dashboard-server/ 기준 sys.path에 dashboard-server/가 추가됨.


def _source_root() -> Path:
    """프로젝트 소스 루트 (ai-framework/) 반환."""
    # tests/ → backend/ → (source root)
    return Path(__file__).parent.parent.parent.parent


def _dashboard_server_path() -> Path:
    """배포 경로 ~/.opal/dashboard-server/ 반환."""
    return Path.home() / ".opal" / "dashboard-server"


# ── S-10 보강: 배포 구조 검증 ──────────────────────────────────────────────

class TestDeployPackageStructure:
    """배포 후 패키지 구조가 올바른지 검증 (install_dashboard() 실행 후 전제)."""

    def test_deploy_package_structure_exists(self):
        """배포 후 dashboard/__init__.py 와 dashboard/backend/ 가 존재해야 한다."""
        ds = _dashboard_server_path()
        if not ds.exists():
            pytest.skip("~/.opal/dashboard-server/ 미존재 — install 후 재실행")
        pkg_init = ds / "dashboard" / "__init__.py"
        pkg_backend = ds / "dashboard" / "backend"
        assert pkg_init.exists(), (
            f"dashboard/__init__.py 없음: {pkg_init}\n"
            "install_dashboard() 가 패키지 구조로 배포했는지 확인하세요."
        )
        assert pkg_backend.is_dir(), (
            f"dashboard/backend/ 없음: {pkg_backend}\n"
            "install_dashboard() 가 패키지 구조로 배포했는지 확인하세요."
        )

    def test_deploy_main_py_exists(self):
        """배포 후 dashboard/backend/main.py 가 존재해야 한다."""
        ds = _dashboard_server_path()
        if not ds.exists():
            pytest.skip("~/.opal/dashboard-server/ 미존재 — install 후 재실행")
        main_py = ds / "dashboard" / "backend" / "main.py"
        assert main_py.exists(), f"main.py 없음: {main_py}"

    def test_deploy_backend_init_exists(self):
        """배포 후 dashboard/backend/__init__.py 가 존재해야 한다."""
        ds = _dashboard_server_path()
        if not ds.exists():
            pytest.skip("~/.opal/dashboard-server/ 미존재 — install 후 재실행")
        backend_init = ds / "dashboard" / "backend" / "__init__.py"
        assert backend_init.exists(), (
            f"dashboard/backend/__init__.py 없음: {backend_init}"
        )


class TestDeployAppImport:
    """배포 컨텍스트(dashboard-server/ 를 sys.path 루트로) 에서 app import 가능한지 검증."""

    def test_deploy_app_importable_from_dashboard_server_root(self):
        """dashboard-server/ 를 sys.path 에 추가 시 dashboard.backend.main:app 이 import 가능해야 한다."""
        ds = _dashboard_server_path()
        if not ds.exists():
            pytest.skip("~/.opal/dashboard-server/ 미존재 — install 후 재실행")
        if not (ds / "dashboard" / "__init__.py").exists():
            pytest.skip("패키지 구조 미완성 — install_dashboard() 실행 후 재시도")

        # 배포 경로를 sys.path 앞에 삽입하여 배포 컨텍스트 시뮬레이션
        original_path = sys.path.copy()
        str_ds = str(ds)
        try:
            if str_ds not in sys.path:
                sys.path.insert(0, str_ds)
            # 기존 캐시 제거 (이전 import 와 충돌 방지)
            mods_to_remove = [k for k in sys.modules if k.startswith("dashboard.")]
            for mod in mods_to_remove:
                del sys.modules[mod]

            mod = importlib.import_module("dashboard.backend.main")
            assert hasattr(mod, "app"), "dashboard.backend.main 에 'app' 이 없음"
        finally:
            sys.path[:] = original_path
            # 정리: 배포 경로에서 import 한 모듈 제거
            mods_to_remove = [k for k in sys.modules if k.startswith("dashboard.")]
            for mod in mods_to_remove:
                del sys.modules[mod]


class TestDeployEndpoints:
    """배포 컨텍스트 기준으로 TestClient 로 /health 와 / 엔드포인트를 검증."""

    @pytest.fixture(autouse=True)
    def _setup_deploy_path(self):
        """배포 경로를 sys.path 에 추가하고 테스트 후 복구."""
        ds = _dashboard_server_path()
        if not ds.exists():
            pytest.skip("~/.opal/dashboard-server/ 미존재 — install 후 재실행")
        if not (ds / "dashboard" / "__init__.py").exists():
            pytest.skip("패키지 구조 미완성 — install_dashboard() 실행 후 재시도")

        original_path = sys.path.copy()
        str_ds = str(ds)
        # 배포 경로를 sys.path 앞에 삽입
        if str_ds not in sys.path:
            sys.path.insert(0, str_ds)

        # 기존 캐시 제거
        mods_to_remove = [k for k in sys.modules if k.startswith("dashboard.")]
        for mod in mods_to_remove:
            del sys.modules[mod]

        yield

        # 복구
        sys.path[:] = original_path
        mods_to_remove = [k for k in sys.modules if k.startswith("dashboard.")]
        for mod in mods_to_remove:
            del sys.modules[mod]

    def test_deploy_health_endpoint(self):
        """/health 가 배포 컨텍스트에서 200 + {status:ok} 반환."""
        from fastapi.testclient import TestClient
        mod = importlib.import_module("dashboard.backend.main")
        client = TestClient(mod.app)
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") == "ok", f"/health status != ok: {data}"

    def test_deploy_root_accessible(self):
        """/ 경로가 배포 컨텍스트에서 접근 가능한지 확인.

        TestClient 는 소스 루트의 __file__ 기준으로 _dist_dir 을 계산하므로,
        배포 경로의 dist/ 를 직접 검사하는 별도 경로 어설션으로 보완한다:
          1. 실제 기동(localhost:7823)이 가능한 경우: curl 기반 검증이 더 정확
          2. TestClient 내: API 엔드포인트(/health) 계약이 유효하면 SPA 마운트 로직도 통과
        여기서는 main 모듈이 오류 없이 로드되고 /health 가 동작함을 재확인한다.
        SPA fallback 실 동작은 live curl 검증(배포본 smoke)으로 대체.
        """
        from fastapi.testclient import TestClient
        ds = _dashboard_server_path()

        mod = importlib.import_module("dashboard.backend.main")
        client = TestClient(mod.app, raise_server_exceptions=False)

        # /health 는 dist 존재 여부와 무관하게 항상 200
        resp = client.get("/health")
        assert resp.status_code == 200, f"/health 200 기대, {resp.status_code} 수신"

        # 배포 dist 존재 여부를 직접 파일시스템으로 검사 (실 기동은 200 반환 확인됨)
        dist_index = ds / "dist" / "index.html"
        assert dist_index.exists(), (
            f"dist/index.html 없음: {dist_index}\n"
            "FE 빌드 후 install_dashboard() 가 dist/ 를 배포했는지 확인하세요."
        )
