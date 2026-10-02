"""
@header {
  "module": "test_e2e_skeleton",
  "task": "127-260912-oppl-E2E-하네스-구현",
  "layer": "test",
  "domain": "opal-tools",
  "description": "설정 기반 SUT 관통 검증 — 이 저장소 `.opal/e2e/environment.json`을 environment.load로 읽고 render_service→start_service(health 포함)로 backend·frontend를 기동해 S-5(health/openapi 200) · S-6(CORS 실 HTTP) · S-7(CDP real-usage 관통, 호출 순서 계약 ①~⑤ 준수, frontend→backend URL은 설정 env 치환) · S-8(pgid 회수 전건·7823 비간섭·dist 미생성)를 검증한다.",
  "scenarios": ["S-5", "S-6", "S-7", "S-8"],
  "exports": ["TestBackendHealthAndOpenapi", "TestCorsRealHttp", "TestBrowserRealUsage", "TestCleanupAndNonInterference"]
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
import urllib.request

_TOOL_DIR = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(_TOOL_DIR))
_SOURCE_ROOT = _TOOL_DIR.parent.parent.parent  # opal/tools/test-tool -> repo root

from lib.e2e import environment as e2e_environment  # noqa: E402
from lib.e2e import ports as e2e_ports  # noqa: E402
from lib.e2e import runtime as e2e_runtime  # noqa: E402
from lib.e2e import process as e2e_process  # noqa: E402


def _chrome_headless_shell_path():
    import glob

    override = os.environ.get("CHROME_HEADLESS_SHELL")
    if override:
        return override
    candidates = glob.glob(
        str(
            pathlib.Path.home()
            / "Library/Caches/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-*/chrome-headless-shell"
        )
    )
    return candidates[0] if candidates else None


def _console_7823_baseline():
    try:
        with urllib.request.urlopen("http://127.0.0.1:7823/health", timeout=1) as resp:
            return resp.status
    except Exception:
        return None


def _repo_environment():
    """이 저장소 설정을 읽는다. 무효·부재면 테스트 전제가 깨진 것이므로 즉시 실패한다."""
    loaded = e2e_environment.load(str(_SOURCE_ROOT))
    assert loaded["status"] == "ok", f"repo environment.json not ok: {loaded!r}"
    return loaded["config"]


def _service(config, service_id):
    for service in config["services"]:
        if service["id"] == service_id:
            return service
    raise AssertionError(f"service '{service_id}' missing in repo environment.json")


class _SutFixtureMixin:
    """이 저장소 설정의 backend·frontend 서비스를 임대 포트로 기동/회수하는 공통 fixture."""

    def setUp(self):
        self.artifact_dir = tempfile.mkdtemp(prefix="opal-e2e-skeleton-")
        self.handles = []
        self.config = _repo_environment()
        self.ports_by_id = {}
        self._console_baseline = _console_7823_baseline()
        self._git_status_before = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=_SOURCE_ROOT,
            capture_output=True,
            text=True,
        ).stdout
        # dist 미생성 단언 대상은 설정의 frontend 작업 폴더에서 정한다.
        frontend = _service(self.config, "frontend")
        self._frontend_dist = pathlib.Path(
            e2e_environment.render_service(
                frontend,
                port=0,
                ports_by_id={svc["id"]: 0 for svc in self.config["services"]},
                project_root=str(_SOURCE_ROOT),
            )["cwd"]
        ) / "dist"

    def tearDown(self):
        if self.handles:
            report = e2e_runtime.stop_all(self.handles)
            # D-10/A-4: leaked는 그룹 리더 1건이 아니라 SIGKILL 이후
            # process_group_members로 재열거한 잔존 구성원 pid 전건이다.
            assert report.leaked == [], f"leaked process group members: {report.leaked}"

        after = _console_7823_baseline()
        assert after == self._console_baseline, "7823 Console health baseline changed"

        git_status_after = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=_SOURCE_ROOT,
            capture_output=True,
            text=True,
        ).stdout
        assert git_status_after == self._git_status_before, "repo dirty state changed by test run"

        assert not self._frontend_dist.exists(), f"{self._frontend_dist} must not be created"

        shutil.rmtree(self.artifact_dir, ignore_errors=True)

    def _start(self, service_id: str, *, port: int, env_extra: dict | None = None):
        # D-11/D-13: port는 호출자가 확보해 필수 키워드 인자로 넘긴다.
        self.ports_by_id[service_id] = port
        # 아직 기동하지 않은 서비스도 치환 토큰({service.<id>.url})이 해석되도록 자리 포트 0을 둔다
        # (하네스는 전 서비스 포트를 먼저 임대하므로 실제 run_e2e 경로와 같은 조건).
        known_ports = {svc["id"]: 0 for svc in self.config["services"]}
        known_ports.update(self.ports_by_id)
        rendered = e2e_environment.render_service(
            _service(self.config, service_id),
            port=port,
            ports_by_id=known_ports,
            project_root=str(_SOURCE_ROOT),
        )
        rendered["env"].update(env_extra or {})
        # start_service는 설정 health(backend: http /health + status 필드, frontend: 포트 오픈)를
        # 통과해야 handle을 돌려준다.
        handle = e2e_runtime.start_service(
            rendered, role=service_id, port=port, artifact_dir=self.artifact_dir
        )
        self.handles.append(handle)
        return handle, rendered

    def _start_backend(self, *, port: int, cors_origin: str | None = None, extra_env: dict | None = None):
        env_extra = {}
        if cors_origin:
            env_extra["OPAL_CONSOLE_CORS_ORIGINS"] = cors_origin
        env_extra.update(extra_env or {})
        handle, _ = self._start("backend", port=port, env_extra=env_extra)
        return handle

    def _start_frontend(self, *, port: int, backend_url: str):
        handle, rendered = self._start("frontend", port=port)
        # H-2: 설정 env의 {service.backend.url} 치환이 기동된 backend URL과 같아야 한다.
        assert rendered["env"].get("VITE_API_BASE_URL") == backend_url, rendered["env"]
        return handle


# ── S-5: health / openapi 표면 ────────────────────────────────────────────────

class TestBackendHealthAndOpenapi(_SutFixtureMixin, unittest.TestCase):
    def test_health_and_openapi_surfaces_return_200(self):
        be_port = e2e_ports.find_free_port()
        backend = self._start_backend(port=be_port)

        with urllib.request.urlopen(f"{backend.url}/health", timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            body = json.loads(resp.read())
            self.assertIn("status", body)
            self.assertIn("version", body)

        with urllib.request.urlopen(f"{backend.url}/openapi.json", timeout=5) as resp:
            self.assertEqual(resp.status, 200)

        with urllib.request.urlopen(f"{backend.url}/docs", timeout=5) as resp:
            self.assertEqual(resp.status, 200)


# ── S-6: CORS 실 HTTP ────────────────────────────────────────────────────────

class TestCorsRealHttp(_SutFixtureMixin, unittest.TestCase):
    def test_injected_origin_reflected_and_other_origin_not(self):
        be_port = e2e_ports.find_free_port()
        injected_origin = "http://127.0.0.1:59999"
        backend = self._start_backend(port=be_port, cors_origin=injected_origin)

        req = urllib.request.Request(f"{backend.url}/health", headers={"Origin": injected_origin})
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), injected_origin)

        other_origin = "http://127.0.0.1:1"
        req2 = urllib.request.Request(f"{backend.url}/health", headers={"Origin": other_origin})
        with urllib.request.urlopen(req2, timeout=5) as resp2:
            self.assertIsNone(resp2.headers.get("Access-Control-Allow-Origin"))


# ── S-7: 브라우저 real-usage 관통 (CDP) ───────────────────────────────────────

class TestBrowserRealUsage(_SutFixtureMixin, unittest.TestCase):
    def test_browser_dashboard_call_reaches_backend(self):
        chrome_path = _chrome_headless_shell_path()
        if not chrome_path:
            # D-17: 기본은 hard fail. 명시적 opt-out이 설정된 경우에만 skip하고,
            # 그 경우에도 executor_unavailable 사유를 결과에 남긴다.
            if os.environ.get("OPAL_E2E_ALLOW_NO_BROWSER") == "1":
                self.skipTest(
                    "executor_unavailable: chrome-headless-shell binary not found "
                    "(OPAL_E2E_ALLOW_NO_BROWSER=1 opt-out) — 완료 기준 5는 충족되지 않은 것으로 남는다"
                )
            self.fail(
                "executor_unavailable: chrome-headless-shell binary not found. "
                "D-17에 따라 기본 경로는 hard fail이다. skip을 원하면 "
                "OPAL_E2E_ALLOW_NO_BROWSER=1을 명시적으로 설정하라."
            )

        # 호출 순서 계약 ①~⑤ (F-1, D-12) — 어길 경우 CORS 차단인데 CDP는 200을
        # 보고하는 거짓 통과가 성립한다.
        fe_port = e2e_ports.find_free_port()          # ① frontend 포트 먼저
        be_port = e2e_ports.find_free_port()           # ② backend 포트
        fe_origin = f"http://127.0.0.1:{fe_port}"      # ③ ①의 정수로 origin 조립
        # 인증 게이트(태스크 175): 세션 없는 브라우저는 잠금 화면만 보고 데이터를 요청하지 않는다.
        # 임시 HOME/OPAL_HOME의 backend에 1회성 진입 token을 발급해 fragment로 진입한다
        # (사용자 ~/.opal·7823은 건드리지 않는다).
        sut_home = pathlib.Path(tempfile.mkdtemp(prefix="opal-e2e-skeleton-home-"))
        self.addCleanup(shutil.rmtree, sut_home, True)
        (sut_home / ".opal").mkdir()
        sut_env = {"HOME": str(sut_home), "OPAL_HOME": str(sut_home / ".opal")}
        issued = subprocess.run(
            [sys.executable, "-m", "dashboard.backend.entry_token", "issue"],
            cwd=_SOURCE_ROOT, capture_output=True, text=True, timeout=30,
            env={**os.environ, **sut_env, "PYTHONPATH": str(_SOURCE_ROOT)},
        )
        self.assertEqual(issued.returncode, 0, "entry token 발급 실패")
        entry_token = issued.stdout.strip()
        backend = self._start_backend(port=be_port, cors_origin=fe_origin, extra_env=sut_env)  # ④ (start_service 내부에서 http health)
        frontend = self._start_frontend(port=fe_port, backend_url=backend.url)  # ⑤

        # [MUST] ③에서 주입한 origin의 포트와 ⑤에서 vite가 실제로 바인딩한
        # 포트가 같은 정수임을 구조적으로 단언한다(동일성 보증 — F-1, D-11/D-13).
        actual_frontend_port = int(frontend.url.rsplit(":", 1)[-1])
        self.assertEqual(
            actual_frontend_port,
            fe_port,
            "frontend가 실제로 바인딩한 포트가 CORS origin에 주입한 포트(fe_port)와 다르다 "
            "— strict-port 계약(D-13) 위반 또는 포트 재확보 누락",
        )

        node_script = pathlib.Path(self.artifact_dir) / "cdp_probe.mjs"
        node_script.write_text(
            _CDP_PROBE_TEMPLATE.format(
                chrome_path=chrome_path,
                target_url=f"{frontend.url}/#entry={entry_token}",
                expect_url=f"{backend.url}/api/dashboard",
            ),
            encoding="utf-8",
        )

        result = subprocess.run(
            ["node", str(node_script)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        observed = json.loads(result.stdout)
        # S-7 locked expected의 유일한 판정 조건: CDP Network.responseReceived 관측 1건
        # (url == 임대 backend의 /api/dashboard AND status == 200).
        # DOM(Runtime.evaluate) 확인은 판정 조건이 아니라 보조 진단 증적이므로
        # 여기서는 사용하지 않는다(A-5).
        self.assertEqual(observed["status"], 200)
        self.assertEqual(observed["url"], f"{backend.url}/api/dashboard")


_CDP_PROBE_TEMPLATE = """
import {{ spawn }} from 'node:child_process';
import {{ mkdtempSync, rmSync }} from 'node:fs';
import {{ tmpdir }} from 'node:os';
import path from 'node:path';

const chromePath = {chrome_path!r};
const targetUrl = {target_url!r};
const expectUrl = {expect_url!r};

const userDataDir = mkdtempSync(path.join(tmpdir(), 'opal-chs-'));

const proc = spawn(chromePath, [
  '--headless=new', '--remote-debugging-port=0',
  '--user-data-dir=' + userDataDir,
  '--no-first-run', '--disable-gpu',
], {{ detached: true }});

let cleanedUp = false;
function cleanup() {{
  if (cleanedUp) return;
  cleanedUp = true;
  try {{ process.kill(-proc.pid, 'SIGKILL'); }} catch {{}}
  try {{ proc.kill('SIGKILL'); }} catch {{}}
  try {{ rmSync(userDataDir, {{ recursive: true, force: true }}); }} catch {{}}
}}
process.on('exit', cleanup);

function withTimeout(promise, ms, label) {{
  return Promise.race([
    promise,
    new Promise((_, reject) => setTimeout(() => reject(new Error('timeout: ' + label)), ms)),
  ]);
}}

try {{
  let wsUrl = null;
  const wsUrlDeadline = Date.now() + 15000;
  for await (const chunk of proc.stderr) {{
    const line = chunk.toString();
    const m = line.match(/ws:\\/\\/[^\\s]+/);
    if (m) {{ wsUrl = m[0]; break; }}
    if (Date.now() > wsUrlDeadline) break;
  }}
  if (!wsUrl) {{ console.error('no devtools endpoint'); process.exitCode = 1; }}
  else {{
    const ws = new WebSocket(wsUrl);
    await withTimeout(
      new Promise((resolve) => ws.addEventListener('open', resolve)),
      15000,
      'ws-open',
    );

    let id = 0;
    const pending = new Map();
    ws.addEventListener('message', (ev) => {{
      const msg = JSON.parse(ev.data.toString());
      if (msg.id && pending.has(msg.id)) {{
        pending.get(msg.id)(msg);
        pending.delete(msg.id);
      }}
    }});
    function send(method, params, sessionId) {{
      const thisId = ++id;
      return withTimeout(
        new Promise((resolve) => {{
          pending.set(thisId, resolve);
          ws.send(JSON.stringify({{ id: thisId, method, params, sessionId }}));
        }}),
        15000,
        'cdp-send:' + method,
      );
    }}

    const target = await send('Target.createTarget', {{ url: 'about:blank' }});
    const targetId = target.result.targetId;
    const attach = await send('Target.attachToTarget', {{ targetId, flatten: true }});
    const sessionId = attach.result.sessionId;

    await send('Network.enable', {{}}, sessionId);
    await send('Page.enable', {{}}, sessionId);

    let found = null;
    ws.addEventListener('message', (ev) => {{
      const msg = JSON.parse(ev.data.toString());
      if (msg.method === 'Network.responseReceived' && msg.params.response.url === expectUrl) {{
        found = {{ url: msg.params.response.url, status: msg.params.response.status }};
      }}
    }});

    await send('Page.navigate', {{ url: targetUrl }}, sessionId);
    const deadline = Date.now() + 15000;
    while (!found && Date.now() < deadline) {{
      await new Promise((r) => setTimeout(r, 200));
    }}

    if (!found) {{ console.error('no matching network response observed'); process.exitCode = 1; }}
    else {{ console.log(JSON.stringify(found)); }}
  }}
}} catch (err) {{
  console.error(String(err && err.message || err));
  process.exitCode = 1;
}} finally {{
  cleanup();
}}
"""


# ── S-8: 정리·비간섭 ──────────────────────────────────────────────────────────

class TestCleanupAndNonInterference(_SutFixtureMixin, unittest.TestCase):
    def test_pgid_reclaimed_and_no_leak_after_stop_all(self):
        be_port = e2e_ports.find_free_port()
        backend = self._start_backend(port=be_port)
        pgid = backend.spawned.pgid

        # A-4: 리더 pid 1건(pid_alive)만 보면 start_new_session=True에서
        # pgid == 리더 pid이므로 항상 통과해버려 vite 손자(esbuild) 누출을
        # 전혀 검출하지 못한다. process_group_members로 그룹 구성원 전건을
        # 재열거해 실질 방어로 삼는다.
        report = e2e_runtime.stop_all(self.handles)
        self.handles = []  # already stopped — avoid double stop in tearDown

        self.assertEqual(report.leaked, [])
        self.assertEqual(e2e_process.process_group_members(pgid), [])
        self.assertFalse(e2e_process.pid_alive(pgid))


if __name__ == "__main__":
    unittest.main()
