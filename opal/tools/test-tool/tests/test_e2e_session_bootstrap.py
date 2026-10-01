"""
@header {
  "module": "test_e2e_session_bootstrap",
  "task": "172-261001-opd-콘솔-POST-인증-게이트",
  "layer": "test",
  "domain": "opal-tools",
  "description": "S-14 — environment.json의 선택 키 `session_bootstrap`(D-20) 계약 검증. 선언 스키마 검증, 부트스트랩 명령 stdout 형태와 실패 코드 `e2e_session_bootstrap_failed`(stdout 비노출), API executor 요청 헤더 병합(스텝 헤더 우선·null 제거), 브라우저 entry_url fragment 부착, 증적 마스킹(x-csrf-token·`#entry=`·Cookie), backend env `OPAL_CONSOLE_CORS_ORIGINS={service.frontend.url}` 렌더(D-21)를 실제 코드로 확인한다. 외부 서비스·실제 SUT 기동 없음.",
  "scenarios": ["S-14"],
  "exports": [
    "TestSessionBootstrapSchema", "TestRunSessionBootstrap", "TestApiHeaderMerge",
    "TestEntryUrlFragment", "TestSessionRedaction", "TestCorsOriginRender", "TestRepoEnvironmentDeclaration"
  ]
}

[RED 계약 — GREEN 구현자(W-6)가 따를 계약]
이 파일은 구현 전에 작성된 RED 테스트다. 아래 이름·형태는 PLAN D-20/D-21 문구에서 도출한
것이며, 구현은 이 이름을 그대로 노출해야 한다(바꾸려면 이 테스트를 함께 바꾸고 사유를 남긴다).

1. `lib.e2e.environment`
   - `validate(config)`가 최상위 선택 키 `session_bootstrap`을 허용한다.
     값: `{"service": str, "command": [str, ...], "cwd"?: str, "env"?: {str: str}, "timeout_s"?: int}`.
     위반은 기존 코드 집합만 쓴다(새 코드 금지): 알 수 없는 service → `unknown_service_ref`,
     비리스트·비문자열 command 원소/service 타입 오류 → `invalid_type`, 알 수 없는 키 →
     `unknown_field`, service·command 누락 → `required_field_missing`. 키가 없는 파일은 위반 없음.
   - `normalize(config)`는 `session_bootstrap`을 보존한다(키 없으면 만들지 않는다).
   - `render_session_bootstrap(config, *, ports_by_id, project_root, host=DEFAULT_HOST)`
     → `{"argv": [...], "cwd": str, "env": {...}, "timeout_s": int}` (치환 토큰·cwd 경계는
     `render_service`와 같은 규칙, `timeout_s` 기본 30). 키가 없으면 `None`.
2. `lib.e2e.orchestrator`
   - 상수 `DETAIL_SESSION_BOOTSTRAP_FAILED == "e2e_session_bootstrap_failed"`.
   - 예외 `SessionBootstrapError(Exception)` — `.code`가 위 상수. `str(exc)`·`.detail`에는
     명령 stdout/stderr 내용을 싣지 않는다.
   - `run_session_bootstrap(rendered, *, base_env=None) -> {"headers": {이름: 값}, "browser_entry_fragment": "entry=<token>"}`.
     stdout은 JSON 객체이며 키는 `headers`·`browser_entry_fragment`만 허용한다. 그 밖의 키, 비JSON,
     비0 종료, 타임아웃은 전부 `SessionBootstrapError`다.
   - `_executor_runtime_context(..., session_bootstrap=<위 반환값>)`는 context에
     `session_headers`(headers 사본)를 싣고, web 표면 `entry_url`에 `"#" + fragment`를 붙인다.
     `session_bootstrap`이 없으면 기존 동작과 같다.
3. `lib.e2e.executors.api.ApiExecutor`
   - `runtime_context["session_headers"]`를 모든 요청 헤더에 병합한다. 같은 이름(대소문자 무시)은
     스텝 지정 헤더가 우선한다. 스텝 헤더 값이 `None`이면 병합된 같은 이름 헤더를 제거하고
     보내지 않는다(인증 없는 요청을 같은 SUT에서 검증하기 위한 수단 — S-15가 사용).
4. `lib.e2e.redaction`
   - `x-csrf-token` 헤더 값은 마스킹된다(`SECRET_HEADER_NAMES`에 추가).
   - URL·자유 텍스트의 fragment `#entry=<값>`은 `#entry=[REDACTED]`가 된다.
"""
from __future__ import annotations

import copy
import json
import pathlib
import sys
import tempfile
import unittest

_TOOL_DIR = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(_TOOL_DIR))
_SOURCE_ROOT = _TOOL_DIR.parent.parent.parent

from lib.e2e import environment as env  # noqa: E402
from lib.e2e import evidence as e2e_evidence  # noqa: E402
from lib.e2e import orchestrator as e2e_orchestrator  # noqa: E402
from lib.e2e import redaction as e2e_redaction  # noqa: E402
from lib.e2e.executors import api as e2e_api  # noqa: E402

_CODE = "e2e_session_bootstrap_failed"
_PY = sys.executable


def _config(**bootstrap_overrides):
    """backend→frontend 의존 구성. frontend URL을 backend env가 참조한다(D-21)."""
    cfg = {
        "schema_version": "1.0",
        "services": [
            {
                "id": "backend",
                "command": ["{python}", "-m", "uvicorn", "app:app", "--port", "{port}"],
                "env": {"OPAL_CONSOLE_CORS_ORIGINS": "{service.frontend.url}"},
                "health": {"type": "http", "path": "/health", "expect_status": 200},
            },
            {
                "id": "frontend",
                "command": ["npm", "run", "dev", "--", "--port", "{port}"],
                "cwd": "web",
                "env": {"VITE_API_BASE_URL": "{service.backend.url}"},
                "depends_on": ["backend"],
                "health": {"type": "port"},
            },
        ],
        "surfaces": [
            {"id": "console", "kind": "web", "service": "frontend", "path": "/"},
            {"id": "console-api", "kind": "api", "service": "backend", "health_path": "/health"},
        ],
        "session_bootstrap": {
            "service": "backend",
            "command": ["{python}", ".opal/e2e/console_session.py", "--base-url", "{service.backend.url}"],
        },
    }
    cfg["session_bootstrap"].update(bootstrap_overrides)
    return cfg


def _codes(config):
    return [item["code"] for item in env.validate(config)]


# ─── ① 선언 검증 ─────────────────────────────────────────────────────────────
class TestSessionBootstrapSchema(unittest.TestCase):
    def test_valid_declaration_passes(self):
        self.assertEqual(env.validate(_config()), [])

    def test_valid_declaration_with_all_optional_keys(self):
        cfg = _config(cwd=".", env={"OPAL_HOME": "{project_root}/.tmp"}, timeout_s=45)
        self.assertEqual(env.validate(cfg), [])

    def test_unknown_service_is_rejected(self):
        self.assertIn("unknown_service_ref", _codes(_config(service="ghost")))

    def test_non_string_command_is_rejected(self):
        for bad in ("python script.py", ["python", 3], [], None):
            with self.subTest(command=bad):
                self.assertTrue(
                    {"invalid_type", "required_field_missing"} & set(_codes(_config(command=bad))),
                    f"command={bad!r} must be a violation",
                )

    def test_unknown_key_is_rejected(self):
        self.assertIn("unknown_field", _codes(_config(retries=3)))

    def test_missing_required_keys_are_rejected(self):
        for key in ("service", "command"):
            cfg = _config()
            del cfg["session_bootstrap"][key]
            with self.subTest(missing=key):
                self.assertIn("required_field_missing", _codes(cfg))

    def test_wrong_timeout_type_is_rejected(self):
        self.assertIn("invalid_type", _codes(_config(timeout_s="30")))

    def test_file_without_the_key_is_unchanged(self):
        cfg = _config()
        del cfg["session_bootstrap"]
        self.assertEqual(env.validate(cfg), [])
        self.assertNotIn("session_bootstrap", env.normalize(cfg))
        self.assertIsNone(
            env.render_session_bootstrap(
                cfg, ports_by_id={"backend": 1, "frontend": 2}, project_root=str(_SOURCE_ROOT)
            )
        )

    def test_normalize_keeps_the_declaration(self):
        self.assertEqual(env.normalize(_config())["session_bootstrap"]["service"], "backend")

    def test_violation_detail_never_carries_command_text(self):
        cfg = _config(command=["python", "TOP-SECRET-LITERAL", 3])
        blob = json.dumps(env.validate(cfg), ensure_ascii=False)
        self.assertNotIn("TOP-SECRET-LITERAL", blob)

    def test_render_substitutes_tokens_and_defaults_timeout(self):
        rendered = env.render_session_bootstrap(
            _config(), ports_by_id={"backend": 41001, "frontend": 41002}, project_root=str(_SOURCE_ROOT)
        )
        self.assertEqual(rendered["timeout_s"], 30)
        self.assertEqual(rendered["argv"][0], _PY)
        self.assertEqual(rendered["argv"][-1], "http://127.0.0.1:41001")
        self.assertTrue(pathlib.Path(rendered["cwd"]).is_absolute())

    def test_render_honours_timeout_override(self):
        rendered = env.render_session_bootstrap(
            _config(timeout_s=7), ports_by_id={"backend": 1, "frontend": 2}, project_root=str(_SOURCE_ROOT)
        )
        self.assertEqual(rendered["timeout_s"], 7)


# ─── ② 부트스트랩 실행 ───────────────────────────────────────────────────────
def _rendered(script: str, *, timeout_s: int = 30):
    return {"argv": [_PY, "-c", script], "cwd": str(_SOURCE_ROOT), "env": {}, "timeout_s": timeout_s}


class TestRunSessionBootstrap(unittest.TestCase):
    def test_constant_is_the_contract_code(self):
        self.assertEqual(e2e_orchestrator.DETAIL_SESSION_BOOTSTRAP_FAILED, _CODE)

    def test_valid_stdout_is_returned_verbatim(self):
        script = (
            "import json;print(json.dumps({'headers': {'Cookie': 'sid=abc', 'X-CSRF-Token': 'csrf1',"
            " 'Origin': 'http://127.0.0.1:1'}, 'browser_entry_fragment': 'entry=tok123'}))"
        )
        result = e2e_orchestrator.run_session_bootstrap(_rendered(script))
        self.assertEqual(result["headers"]["Cookie"], "sid=abc")
        self.assertEqual(result["headers"]["X-CSRF-Token"], "csrf1")
        self.assertEqual(result["browser_entry_fragment"], "entry=tok123")

    def test_base_env_and_rendered_env_reach_the_command(self):
        script = (
            "import json,os;print(json.dumps({'headers': {'X-Seen': os.environ['SEEN_A'] + os.environ['SEEN_B']},"
            " 'browser_entry_fragment': 'entry=x'}))"
        )
        rendered = _rendered(script)
        rendered["env"] = {"SEEN_B": "b"}
        result = e2e_orchestrator.run_session_bootstrap(rendered, base_env={"SEEN_A": "a", "PATH": ""})
        self.assertEqual(result["headers"]["X-Seen"], "ab")

    def _assert_fails_without_leaking(self, script, *, timeout_s=30, marker="LEAK-MARKER-9137"):
        with self.assertRaises(e2e_orchestrator.SessionBootstrapError) as ctx:
            e2e_orchestrator.run_session_bootstrap(_rendered(script, timeout_s=timeout_s))
        exc = ctx.exception
        self.assertEqual(exc.code, _CODE)
        for text in (str(exc), repr(exc), str(getattr(exc, "detail", ""))):
            self.assertNotIn(marker, text)
        return exc

    def test_non_json_stdout_fails(self):
        self._assert_fails_without_leaking("print('LEAK-MARKER-9137 not json')")

    def test_non_object_json_fails(self):
        self._assert_fails_without_leaking("print('[\"LEAK-MARKER-9137\"]')")

    def test_non_zero_exit_fails_even_with_valid_json(self):
        script = (
            "import json,sys;print(json.dumps({'headers': {'X': 'LEAK-MARKER-9137'},"
            " 'browser_entry_fragment': 'entry=x'}));sys.exit(3)"
        )
        self._assert_fails_without_leaking(script)

    def test_timeout_fails(self):
        self._assert_fails_without_leaking("import time;time.sleep(30)", timeout_s=1)

    def test_extra_keys_are_rejected(self):
        script = (
            "import json;print(json.dumps({'headers': {}, 'browser_entry_fragment': 'entry=x',"
            " 'cookie': 'LEAK-MARKER-9137'}))"
        )
        self._assert_fails_without_leaking(script)

    def test_stderr_content_is_not_carried(self):
        script = "import sys;sys.stderr.write('LEAK-MARKER-9137');sys.exit(1)"
        self._assert_fails_without_leaking(script)

    def test_non_string_header_values_fail(self):
        script = "import json;print(json.dumps({'headers': {'X': 1}, 'browser_entry_fragment': 'entry=x'}))"
        self._assert_fails_without_leaking(script)


# ─── ③ API 헤더 병합 ─────────────────────────────────────────────────────────
class _Opener:
    """전송 계층만 관측한다. 응답을 만들 뿐이며 병합 결과는 executor 몫이다."""

    def __init__(self):
        self.sent = []

    def __call__(self, *, method, url, headers, body, timeout_s):
        self.sent.append({"method": method, "url": url, "headers": dict(headers)})
        return {"status": 200, "headers": {}, "text": "{}", "json": {}}


def _act(executor, handle, **action):
    action.setdefault("step_role", "verify")
    return executor.dispatch("act", {"handle": handle, "step_id": "s", "action": action})


def _api(session_headers, opener, **kwargs):
    ctx = {"backend_url": "http://127.0.0.1:1", "session_headers": session_headers}
    executor = e2e_api.ApiExecutor(runtime_context=ctx, opener=opener, **kwargs)
    handle = executor.dispatch(
        "prepare", {"run_id": "e2e-20261001-001", "base_url": "http://127.0.0.1:1", "target": "source-worktree"}
    )["handle"]
    return executor, handle


def _lower(headers):
    return {str(k).lower(): v for k, v in headers.items()}


class TestApiHeaderMerge(unittest.TestCase):
    SESSION = {"Cookie": "opal_console_session=S1", "X-CSRF-Token": "C1", "Origin": "http://127.0.0.1:1"}

    def test_session_headers_ride_every_request(self):
        opener = _Opener()
        executor, handle = _api(self.SESSION, opener)
        _act(executor, handle, method="GET", url="/api/projects")
        _act(executor, handle, method="POST", url="/api/config/prewarm", body={"a": 1})
        self.assertEqual(len(opener.sent), 2)
        for sent in opener.sent:
            sent_headers = _lower(sent["headers"])
            self.assertEqual(sent_headers["cookie"], "opal_console_session=S1")
            self.assertEqual(sent_headers["x-csrf-token"], "C1")
            self.assertEqual(sent_headers["origin"], "http://127.0.0.1:1")

    def test_step_headers_win_on_the_same_name_case_insensitively(self):
        opener = _Opener()
        executor, handle = _api(self.SESSION, opener)
        _act(executor, handle, method="GET", url="/api/x", headers={"origin": "http://evil.example", "X-Extra": "1"})
        sent_headers = _lower(opener.sent[0]["headers"])
        self.assertEqual(sent_headers["origin"], "http://evil.example")
        self.assertEqual(sent_headers["x-extra"], "1")
        self.assertEqual(sent_headers["cookie"], "opal_console_session=S1")
        origins = [k for k in opener.sent[0]["headers"] if k.lower() == "origin"]
        self.assertEqual(len(origins), 1, "같은 이름 헤더가 중복 전송되면 안 된다")

    def test_null_step_header_removes_the_merged_header(self):
        opener = _Opener()
        executor, handle = _api(self.SESSION, opener)
        _act(executor, handle, method="POST", url="/api/x", headers={"Cookie": None, "X-CSRF-Token": None, "Origin": None})
        sent_headers = _lower(opener.sent[0]["headers"])
        for name in ("cookie", "x-csrf-token", "origin"):
            self.assertNotIn(name, sent_headers)

    def test_without_session_headers_behaviour_is_unchanged(self):
        opener = _Opener()
        executor = e2e_api.ApiExecutor(runtime_context={"backend_url": "http://127.0.0.1:1"}, opener=opener)
        handle = executor.dispatch(
            "prepare", {"run_id": "e2e-20261001-002", "base_url": "http://127.0.0.1:1", "target": "source-worktree"}
        )["handle"]
        _act(executor, handle, method="GET", url="/api/x", headers={"X-Only": "1"})
        self.assertEqual(_lower(opener.sent[0]["headers"]), {"x-only": "1"})


# ─── ④ entry_url fragment ────────────────────────────────────────────────────
class TestEntryUrlFragment(unittest.TestCase):
    SURFACES = {
        "web": {"id": "console", "kind": "web", "url": "http://127.0.0.1:5173",
                "entry_url": "http://127.0.0.1:5173/"},
        "api": {"id": "console-api", "kind": "api", "url": "http://127.0.0.1:7000", "health_path": "/health"},
    }

    def _ctx(self, **extra):
        with tempfile.TemporaryDirectory() as tmp:
            writer = e2e_evidence.EvidenceWriter(tmp, "e2e-20261001-010")
            return e2e_orchestrator._executor_runtime_context(
                tmp, tmp, writer, project_root=str(_SOURCE_ROOT), surfaces=copy.deepcopy(self.SURFACES), **extra
            )

    def test_fragment_is_appended_after_the_entry_path(self):
        ctx = self._ctx(session_bootstrap={"headers": {"Cookie": "c=1"}, "browser_entry_fragment": "entry=TOK"})
        self.assertEqual(ctx["entry_url"], "http://127.0.0.1:5173/#entry=TOK")
        self.assertEqual(ctx["session_headers"], {"Cookie": "c=1"})

    def test_without_bootstrap_nothing_changes(self):
        ctx = self._ctx()
        self.assertEqual(ctx["entry_url"], "http://127.0.0.1:5173/")
        self.assertFalse(ctx.get("session_headers"))


# ─── ⑤ 마스킹 ────────────────────────────────────────────────────────────────
class TestSessionRedaction(unittest.TestCase):
    def test_csrf_header_value_is_masked_and_cookie_stays_masked(self):
        out, touched = e2e_redaction.redact_headers(
            {"X-CSRF-Token": "csrf-RAW", "Cookie": "sid=RAW", "Accept": "application/json"}
        )
        self.assertEqual(out["X-CSRF-Token"], e2e_redaction.MASK)
        self.assertEqual(out["Cookie"], e2e_redaction.MASK)
        self.assertEqual(out["Accept"], "application/json")
        self.assertTrue(touched)
        self.assertTrue(e2e_redaction.is_secret_header("x-csrf-token"))

    def test_url_fragment_entry_value_is_masked(self):
        out, touched = e2e_redaction.redact_url("http://127.0.0.1:5173/#entry=TOKEN-RAW")
        self.assertEqual(out, "http://127.0.0.1:5173/#entry=" + e2e_redaction.MASK)
        self.assertTrue(touched)

    def test_url_fragment_with_other_params_keeps_them(self):
        out, _ = e2e_redaction.redact_url("http://h/p?x=1#a=1&entry=TOKEN-RAW&b=2")
        self.assertNotIn("TOKEN-RAW", out)
        self.assertIn("x=1", out)

    def test_free_text_fragment_is_masked(self):
        out, _ = e2e_redaction.redact_text("navigated to http://127.0.0.1:5173/#entry=TOKEN-RAW ok")
        self.assertNotIn("TOKEN-RAW", out)

    def test_nested_value_walk_masks_fragment_urls_and_csrf_headers(self):
        out, _ = e2e_redaction.redact_value(
            {"current_url": "http://h/#entry=TOKEN-RAW", "headers": {"x-csrf-token": "csrf-RAW"}}
        )
        self.assertNotIn("TOKEN-RAW", json.dumps(out))
        self.assertNotIn("csrf-RAW", json.dumps(out))

    def test_api_evidence_never_contains_session_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            writer = e2e_evidence.EvidenceWriter(tmp, "e2e-20261001-020")
            executor, handle = _api(
                {"Cookie": "opal_console_session=COOKIE-RAW", "X-CSRF-Token": "CSRF-RAW", "Origin": "http://127.0.0.1:1"},
                _Opener(),
                writer=writer,
            )
            _act(executor, handle, method="POST", url="/api/config/prewarm", body={"enabled": False})
            executor.dispatch("capture", {"handle": handle, "evidence_spec": []})
            blob = "\n".join(
                (pathlib.Path(tmp) / rel).read_text(encoding="utf-8")
                for rel in (e2e_api.API_REQUESTS_PATH, e2e_api.API_RESPONSES_PATH, "actions.jsonl")
            )
        for secret in ("COOKIE-RAW", "CSRF-RAW"):
            with self.subTest(secret=secret):
                self.assertNotIn(secret, blob)
        self.assertIn(e2e_redaction.MASK, blob)


# ─── ⑥ CORS origin 렌더 ──────────────────────────────────────────────────────
class TestCorsOriginRender(unittest.TestCase):
    def test_backend_env_resolves_to_the_leased_frontend_url_without_cycle(self):
        cfg = _config()
        self.assertEqual(env.validate(cfg), [])
        self.assertEqual(env.service_order(cfg), ["backend", "frontend"])
        ports = {"backend": 41001, "frontend": 41002}
        rendered = env.render_service(
            env.normalize(cfg)["services"][0], port=41001, ports_by_id=ports, project_root=str(_SOURCE_ROOT)
        )
        self.assertEqual(rendered["env"]["OPAL_CONSOLE_CORS_ORIGINS"], "http://127.0.0.1:41002")


# ─── 프로젝트 선언(D-21) ─────────────────────────────────────────────────────
class TestRepoEnvironmentDeclaration(unittest.TestCase):
    def setUp(self):
        self.cfg = json.loads((_SOURCE_ROOT / ".opal" / "e2e" / "environment.json").read_text(encoding="utf-8"))

    def test_repo_environment_is_valid(self):
        self.assertEqual(env.validate(self.cfg), [])

    def test_repo_declares_session_bootstrap_on_backend(self):
        spec = self.cfg.get("session_bootstrap")
        self.assertIsInstance(spec, dict, "D-21: .opal/e2e/environment.json must declare session_bootstrap")
        self.assertEqual(spec["service"], "backend")
        self.assertTrue(any("console_session.py" in part for part in spec["command"]))

    def test_repo_backend_allows_the_frontend_origin(self):
        backend = next(s for s in self.cfg["services"] if s["id"] == "backend")
        self.assertEqual(backend.get("env", {}).get("OPAL_CONSOLE_CORS_ORIGINS"), "{service.frontend.url}")


if __name__ == "__main__":
    unittest.main()
