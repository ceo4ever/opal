"""
@header {
  "module": "test_e2e_skeleton",
  "task": "127-260912-oppl-E2E-하네스-구현",
  "layer": "test",
  "domain": "opal-tools",
  "description": "T01 W-5 관통 검증 — S-5(health/openapi 200) · S-6(CORS 실 HTTP) · S-7(CDP real-usage 관통, 호출 순서 계약 ①~⑤ 준수) · S-8(pgid 회수 전건·7823 비간섭·dist 미생성)를 lib/e2e/ 골격(find_free_port·start_backend·start_frontend·wait_healthy·stop_all)으로 검증한다.",
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

# RED: 이 import가 지금은 ModuleNotFoundError를 던진다.
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


class _SutFixtureMixin:
    """backend·frontend SUT를 임대 포트로 기동/회수하는 공통 fixture."""

    def setUp(self):
        self.artifact_dir = tempfile.mkdtemp(prefix="opal-e2e-skeleton-")
        self.handles = []
        self._console_baseline = _console_7823_baseline()
        self._git_status_before = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=_SOURCE_ROOT,
            capture_output=True,
            text=True,
        ).stdout

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

        dist_dir = _SOURCE_ROOT / "dashboard" / "frontend" / "dist"
        assert not dist_dir.exists(), "dashboard/frontend/dist must not be created"

        shutil.rmtree(self.artifact_dir, ignore_errors=True)

    def _start_backend(self, *, port: int, cors_origin: str | None = None):
        # D-11/D-13: port는 호출자가 확보해 필수 키워드 인자로 넘긴다.
        env_extra = {}
        if cors_origin:
            env_extra["OPAL_CONSOLE_CORS_ORIGINS"] = cors_origin
        handle = e2e_runtime.start_backend(
            source_root=str(_SOURCE_ROOT),
            artifact_dir=self.artifact_dir,
            port=port,
            env_extra=env_extra,
        )
        self.handles.append(handle)
        e2e_runtime.wait_healthy(handle.url, timeout_s=60.0)
        return handle

    def _start_frontend(self, *, port: int, backend_url: str):
        handle = e2e_runtime.start_frontend(
            source_root=str(_SOURCE_ROOT),
            artifact_dir=self.artifact_dir,
            port=port,
            backend_url=backend_url,
            env_extra={},
        )
        self.handles.append(handle)
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
        backend = self._start_backend(port=be_port, cors_origin=fe_origin)  # ④ (start_backend 내부에서 wait_healthy)
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
                target_url=f"{frontend.url}/",
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
