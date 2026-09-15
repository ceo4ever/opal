"""
@header {
  "module": "test_e2e_sut_http_surfaces",
  "task": "127-260912-oppl-E2E-하네스-구현",
  "layer": "test",
  "domain": "opal-tools",
  "description": "W-12 (T12) SUT HTTP 표면 전수 E2E 시나리오 스위트 — surfaces.json이 선언한 kind=\"http\" 표면 16건(sut-health는 S-10 소유)을 실제 임대 SUT 위에서 `e2e run`으로 관통한다. 각 표면은 자기 fixture 시나리오를 임시 폴더에 쓰고 api profile로 실행해 status·응답 필드·후속 observable state를 검증하며, 공통 필수 증적 5종과 assertion expected/actual을 남긴다. surfaces.json·test-scenario.json은 읽기 전용으로만 소비한다(C-8).",
  "scenarios": ["S-45", "S-46", "S-47", "S-48", "S-49", "S-50", "S-51", "S-52", "S-53", "S-54", "S-55", "S-56", "S-57", "S-58", "S-59", "S-60"],
  "exports": ["TestSutHttpSurfaces", "TestUserEnvironmentUntouched", "SURFACE_LEDGER"]
}

집행 근거와 경계:

1. [MUST] 모의 서버 대체 금지(C-API-1). 모든 표면은 `e2e run`이 임대 포트 위에 기동한
   **실제 SUT**(dashboard/backend uvicorn)의 공개 endpoint에 소켓을 열어 호출한다. 이
   파일에는 HTTP 응답을 합성하는 경로가 없다.

2. [MUST] C-2 — 사용자 환경 미접촉. 모든 run은 `HOME`·`OPAL_HOME`을 OS 임시 경로로
   갈아끼운 **하위 프로세스**에서만 돈다. 이것이 필요한 이유는 실측 근거가 있다:
   `dashboard/backend/config.py`의 `CONFIG_PATH`는 모듈 로드 시점의
   `Path.home()/".opal"/"console.config.json"`이며 `OPAL_HOME`을 보지 않는다. 즉
   `POST /api/config/prewarm`(sut-config-prewarm)은 `HOME`을 격리하지 않으면 캡틴의
   실 설정 파일을 덮어쓴다. 부모 pytest 프로세스의 `HOME`은 건드리지 않는다.
   사용자 Console(127.0.0.1:7823)은 `lib/e2e/ports.py`의 `EXCLUDED_PORTS`로 임대
   풀에서 제외되며, 스위트 전후로 그 health와 사용자 `console.config.json` 바이트가
   그대로임을 `TestUserEnvironmentUntouched`가 확인한다.

3. [MUST] C-5 — 산출물은 OS 임시 경로에만 쓴다. `OPAL_E2E_ARTIFACT_DIR`를 임시
   디렉터리로 주면 `_resolve_artifact_layout`이 lease 루트까지 그 아래로 내리므로
   저장소 추적 파일은 물론 사용자 홈에도 아무것도 남지 않는다.

4. [MUST] C-8 — `surfaces.json`은 분모로 **읽기만** 한다. 표면 id 목록을 이 파일에
   리터럴로 복제하지 않고 그 파일에서 읽어, 선언된 http 표면이 전부 다뤄졌는지를
   `test_every_declared_http_surface_is_covered`가 되짚는다.

5. assertion은 전부 `equals`다. `match: "contains"`는 `pass`에 도달할 수 없다 —
   driver·executor가 통과시켜도 `e2e_contract.validate_pass_requirements`가
   `expected != actual` 직접 비교로 뒤집는다(§A.5, C-1 동결).

6. [MUST] H-2 — 외부 의존이 없는 표면을 대역으로 채워 `pass`로 승격하지 않는다.
   brain 계열의 LLM 의존 경로(claude CLI 인증 세션)는 격리 `HOME` 아래에 존재하지
   않는다. 그 사실은 `SURFACE_LEDGER`에 구조화 사유로 남고, 확인되지 않은 축을
   확인된 것처럼 세지 않는다. 특히 `sut-brain-query`는 선언 응답 필드(`job_id`)가
   난수 UUID여서 `equals` 전용 매처로 단언할 수 없고 잡 완료는 LLM 의존이므로
   **`blocked`로 남긴다** — 전송 계층만 실측하고 표면 판정을 승격하지 않는다.

7. POST 계열(`sut-brain-prime`·`sut-brain-query`·`sut-config-prewarm`)은 부수효과를
   만든다. 전부 격리 `HOME`과 run 단위 namespace(session_id에 run 토큰) 안에서만
   수행하며, 쓰기 대상은 임시 홈의 `console.config.json`뿐이다.
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
import urllib.parse
import urllib.request
import uuid

_TOOL_DIR = pathlib.Path(__file__).parent.parent
_TEST_TOOL_PY = _TOOL_DIR / "test_tool.py"
_SOURCE_ROOT = _TOOL_DIR.parent.parent.parent
_PYTHON = sys.executable
sys.path.insert(0, str(_TOOL_DIR))

from lib import e2e_contract  # noqa: E402
from lib.e2e import evidence as e2e_evidence  # noqa: E402
from lib.e2e import orchestrator as e2e_orchestrator  # noqa: E402

# ── surfaces.json — 분모. 읽기 전용이다(C-8). ────────────────────────────────
_TASK_DIRS = sorted(_SOURCE_ROOT.glob("tasks/127-*"))
_SURFACES_PATH = (_TASK_DIRS[0] / "surfaces.json") if _TASK_DIRS else None
_SPEC_PATH = (_TASK_DIRS[0] / "test-scenario.json") if _TASK_DIRS else None


def _spec_assertion_ids() -> dict:
    """동결 `test-scenario.json`에서 표면별 **선언 assertion id**를 읽어 온다(읽기 전용).

    이 표를 리터럴로 적지 않는 이유가 판정에 직결된다:
    `e2e_contract.validate_pass_requirements`는 시나리오가 **선언한** assertion id마다
    결과에 `expected`/`actual`이 실려 있고 서로 같은지를 본다(§A.5). 즉 이 스위트가
    남긴 run.json으로 나중에 `scenario-mark --verdict-json`을 돌리려면, 각 run의
    assertion 중 하나가 spec이 선언한 id(S-45-a1 …)를 그대로 달고 있어야 한다.
    id의 소유자는 동결 spec이므로 여기서 지어내지 않고 읽는다.
    """
    if _SPEC_PATH is None or not _SPEC_PATH.exists():
        return {}
    spec = json.loads(_SPEC_PATH.read_text(encoding="utf-8"))
    table = {}
    for scenario in spec.get("scenarios") or []:
        surface_ref = scenario.get("surface_ref")
        ids = [a.get("id") for a in (scenario.get("assertions") or []) if a.get("id")]
        if surface_ref and ids:
            table[surface_ref] = {"scenario_id": scenario.get("id"), "assertion_ids": ids}
    return table


_SPEC_BY_SURFACE = _spec_assertion_ids()

# 표면별 run.json·assertions.json 보존 위치. C-5 — OS 임시 경로에만 남긴다.
_EVIDENCE_ROOT = pathlib.Path(tempfile.gettempdir()) / "w12-sut-http-surface-evidence"

# S-10이 이미 소유하는 표면. W-12의 분담 경계이며 여기서 중복 검증하지 않는다.
_OWNED_ELSEWHERE = ("sut-health",)

# 표면 id → 이 스위트에서 그 표면을 관통하는 테스트 메서드.
# 메서드 이름에서 표면 id를 되짚지 않는 이유: 이름은 검증 성격까지 담아야 해서
# (`..._transport_only`) id와 1:1로 떨어지지 않는다. 대신 이 표가 분모(surfaces.json)와
# 실제 메서드 양쪽에 대해 검사된다 — 표만 고쳐 커버리지를 늘릴 수 없다.
_COVERED_BY_TEST = {
    "sut-dashboard": "test_sut_dashboard",
    "sut-projects-list": "test_sut_projects_list",
    "sut-projects-detail": "test_sut_projects_detail",
    "sut-projects-doc": "test_sut_projects_doc",
    "sut-tasks-list": "test_sut_tasks_list",
    "sut-tasks-detail": "test_sut_tasks_detail",
    "sut-tasks-artifact": "test_sut_tasks_artifact",
    "sut-memory": "test_sut_memory",
    "sut-doctor": "test_sut_doctor",
    "sut-brain-auth": "test_sut_brain_auth",
    "sut-brain-status": "test_sut_brain_status",
    "sut-brain-prime": "test_sut_brain_prime",
    "sut-brain-query": "test_sut_brain_query_transport_only",
    "sut-brain-job": "test_sut_brain_job",
    "sut-config-get": "test_sut_config_get",
    "sut-config-prewarm": "test_sut_config_prewarm",
}

# 사용자 Console — 임대 풀에서 제외된 상시 가동 프로세스(C-2).
_USER_CONSOLE_HEALTH = "http://127.0.0.1:7823/health"
_USER_CONSOLE_CONFIG = pathlib.Path.home() / ".opal" / "console.config.json"

# 표면별 판정 원장. 구조화 사유는 여기에만 쌓이고 tearDownModule이 임시 경로로 낸다.
SURFACE_LEDGER: list = []

_USER_SNAPSHOT: dict = {}


def _http_status(url: str) -> int:
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return int(response.status)
    except Exception:  # noqa: BLE001 — 가용성 판정에만 쓰며 분류하지 않는다.
        return 0


def setUpModule() -> None:
    """C-2 스냅샷 — 사용자 자산의 실행 전 상태를 바이트로 붙잡는다."""
    shutil.rmtree(_EVIDENCE_ROOT, ignore_errors=True)
    _USER_SNAPSHOT["console_health"] = _http_status(_USER_CONSOLE_HEALTH)
    _USER_SNAPSHOT["config_bytes"] = (
        _USER_CONSOLE_CONFIG.read_bytes() if _USER_CONSOLE_CONFIG.exists() else None
    )


def tearDownModule() -> None:
    """표면 판정 원장을 OS 임시 경로에 낸다(C-5). 저장소에는 쓰지 않는다."""
    if not SURFACE_LEDGER:
        return
    out = pathlib.Path(tempfile.gettempdir()) / "w12-sut-http-surface-ledger.json"
    out.write_text(
        json.dumps(
            {
                "task": "127-260912-oppl-E2E-하네스-구현",
                "work_item": "W-12",
                "surfaces": SURFACE_LEDGER,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    sys.stderr.write(f"\n[W-12] surface ledger: {out}\n")


def _record(surface_id: str, verdict: str, *, evidence: str = "", reason=None) -> None:
    SURFACE_LEDGER.append(
        {
            "surface_id": surface_id,
            "verdict": verdict,
            "evidence": evidence,
            "blocked_reason": reason,
        }
    )


class _Isolated:
    """격리 `HOME` + 스캔 대상 fixture 프로젝트 1건 + 태스크 1건.

    실 SUT가 읽을 **데이터**를 만들 뿐, 응답을 만들지 않는다 — 판정은 언제나 SUT가
    돌려준 값으로 한다.
    """

    PROJECT_NAME = "w12-fixture-proj"
    TASK_ID = "001-260101-w12-fixture"
    DOC_NAME = "PROJECT.md"
    DOC_BODY = "# W-12 fixture PROJECT\n\n고정 문서.\n"
    ARTIFACT_NAME = "TASK.md"
    ARTIFACT_BODY = "# W-12 fixture TASK\n\n고정 산출물.\n"

    def __init__(self, *, prewarm_projects=None):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix="w12-home-"))
        self.home = self.root / "home"
        self.scan_root = self.root / "projects"
        self.project = self.scan_root / self.PROJECT_NAME
        task = self.project / "tasks" / self.TASK_ID

        (self.home / ".opal").mkdir(parents=True)
        (self.project / ".opal").mkdir(parents=True)
        (self.project / "docs").mkdir(parents=True)
        task.mkdir(parents=True)

        seeded = list(prewarm_projects or [])
        (self.home / ".opal" / "console.config.json").write_text(
            json.dumps(
                {
                    "scan_roots": [str(self.scan_root)],
                    "scan_depth": 2,
                    "exclude": ["node_modules"],
                    "prewarm_projects": [
                        str(self.project) if item == "self" else item for item in seeded
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (self.project / ".opal" / "AGENT.md").write_text("# W-12 fixture AGENT\n", encoding="utf-8")
        (self.project / "docs" / self.DOC_NAME).write_text(self.DOC_BODY, encoding="utf-8")
        (task / self.ARTIFACT_NAME).write_text(self.ARTIFACT_BODY, encoding="utf-8")
        (task / "STATE.md").write_text(
            "# STATE\n\n| 단계 | 상태 | 갱신 |\n|---|---|---|\n| PLAN | done | 2026-01-01 |\n",
            encoding="utf-8",
        )

    @property
    def project_path(self) -> str:
        return str(self.project)

    @property
    def quoted_project(self) -> str:
        return urllib.parse.quote(str(self.project), safe="")

    def config_snapshot(self) -> dict:
        return json.loads(
            (self.home / ".opal" / "console.config.json").read_text(encoding="utf-8")
        )

    def dispose(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)


def _api_scenario(scenario_id: str, surface_ref: str, steps, assertions) -> dict:
    """api profile 시나리오 1건. 동결 spec을 고치지 않고 임시 폴더에 자기 fixture를 쓴다.

    첫 assertion의 id는 동결 spec이 그 표면에 대해 선언한 id로 바꿔 단다. spec의
    `expected`는 산문 서술이라 값 비교의 대상이 아니고, 계약 게이트가 보는 것은 결과
    쪽의 `expected == actual`이다 — 즉 id를 맞추는 일이 spec을 고치는 일의 반대편,
    "선언된 assertion을 실제로 판정했다"를 성립시키는 유일한 배선이다.
    """
    spec = _SPEC_BY_SURFACE.get(surface_ref)
    if spec and assertions:
        assertions = [dict(assertions[0], id=spec["assertion_ids"][0])] + list(assertions[1:])
    return {
        "id": scenario_id,
        "surface_kind": "api",
        "profile": "api",
        "actors": ["service"],
        "surface_ref": surface_ref,
        "required_fidelity": e2e_orchestrator.FIDELITY_REAL_HTTP,
        "steps": steps,
        "assertions": assertions,
        "required_evidence": ["metadata", "server_log", "action_log", "assertions", "cleanup"],
    }


def _get(url: str, step_id: str = "st-call") -> list:
    return [{
        "id": step_id,
        "executor": "api",
        "step_role": "verify",
        "method": "GET",
        "url": url,
        "timeout_ms": 30000,
    }]


def _post(url: str, body: dict, step_id: str = "st-call") -> list:
    return [{
        "id": step_id,
        "executor": "api",
        "step_role": "verify",
        "method": "POST",
        "url": url,
        "body": body,
        "timeout_ms": 30000,
    }]


def _field(assertion_id: str, field: str, expected) -> dict:
    """첫 행동(seq 1)의 응답에서 `field`를 읽어 `equals` 비교한다.

    `source_seq`를 못 박는 이유: `verifier: "state"` assertion은 자기 호출로
    `last_seq`를 밀어 올린다. 고정하지 않으면 뒤 assertion이 다른 응답을 본다.
    """
    return {
        "id": assertion_id,
        "verifier": "response",
        "match": "equals",
        "source_seq": 1,
        "field": field,
        "expected": expected,
    }


def _state(assertion_id: str, url: str, field: str, expected) -> dict:
    """후속 observable state — 같은 SUT에 대한 **별도 실 호출**로 확인한다."""
    return {
        "id": assertion_id,
        "verifier": "state",
        "match": "equals",
        "method": "GET",
        "url": url,
        "field": field,
        "expected": expected,
    }


class TestSutHttpSurfaces(unittest.TestCase):
    """surfaces.json의 http 표면을 실제 임대 SUT 위에서 관통한다."""

    maxDiff = None

    # ── 실행 골격 ────────────────────────────────────────────────────────────
    def _run(self, scenario: dict, home: pathlib.Path):
        """`e2e run`을 격리 env의 하위 프로세스로 돌리고 증적을 읽어 온다.

        하위 프로세스인 이유는 `HOME` 교체 때문이다 — 부모 pytest 프로세스의 `HOME`을
        건드리면 그 프로세스가 도구를 해석하는 방식까지 바뀐다(C-2).
        """
        workspace = pathlib.Path(tempfile.mkdtemp(prefix="w12-run-"))
        task_path = workspace / "spec"
        artifact_dir = workspace / "artifacts"
        task_path.mkdir()
        artifact_dir.mkdir()
        (task_path / "test-scenario.json").write_text(
            json.dumps(
                {
                    "schema_version": e2e_contract.E2E_CONTRACT_SCHEMA_VERSION,
                    "task_id": "w12-sut-http-surfaces",
                    "locked": False,
                    "scenarios": [scenario],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        env = os.environ.copy()
        env["HOME"] = str(home)
        env["OPAL_HOME"] = str(home / ".opal")
        env["OPAL_E2E_ARTIFACT_DIR"] = str(artifact_dir)

        proc = subprocess.run(
            [
                _PYTHON, str(_TEST_TOOL_PY), "e2e", "run",
                "--scenario", scenario["id"],
                "--task-path", str(task_path),
                "--target", "source-worktree",
                "--worktree-root", str(_SOURCE_ROOT),
            ],
            capture_output=True,
            text=True,
            env=env,
            timeout=300,
        )
        self.assertTrue(
            proc.stdout.strip(),
            f"'e2e run' produced no payload (rc={proc.returncode}): {proc.stderr[-2000:]!r}",
        )
        payload = json.loads(proc.stdout)
        artifacts = {
            "run.json": json.loads((artifact_dir / "run.json").read_text(encoding="utf-8")),
            "assertions.json": json.loads(
                (artifact_dir / "assertions.json").read_text(encoding="utf-8")
            ),
            "cleanup.json": json.loads(
                (artifact_dir / "cleanup.json").read_text(encoding="utf-8")
            ),
            "actions.jsonl": [
                json.loads(line)
                for line in (artifact_dir / "actions.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ],
        }
        return proc, payload, artifacts, artifact_dir, workspace

    def _verify(self, scenario: dict, home: pathlib.Path, *, expect_path: str, expect_method="GET"):
        """표면 1건을 관통하고 §A.1·§A.5·§A.11·§C.3 증적을 전부 확인한다."""
        proc, payload, art, artifact_dir, workspace = self._run(scenario, home)
        try:
            run_json = art["run.json"]
            detail = run_json.get("detail") or run_json.get("detail_code")

            # ── 판정 ────────────────────────────────────────────────────────
            self.assertEqual(payload["status"], "pass", f"{scenario['id']} must pass: {detail}")
            self.assertEqual(proc.returncode, e2e_contract.status_to_exit("pass"))
            self.assertTrue(payload["executed"], "step runner가 실제로 돌아야 한다")
            self.assertEqual(run_json["observed_executors"], ["api"])
            self.assertEqual(run_json["fidelity"], e2e_orchestrator.FIDELITY_REAL_HTTP)

            # ── 공통 필수 증적 5종(§A.1) ──────────────────────────────────────
            self.assertTrue(run_json["evidence_complete"])
            self.assertEqual(run_json["missing_evidence"], [])
            for kind in e2e_evidence.COMMON_REQUIRED_EVIDENCE:
                path = artifact_dir / e2e_evidence.EVIDENCE_PATHS[kind]
                self.assertTrue(path.is_file(), f"필수 증적 누락: {kind} → {path}")
                self.assertGreater(path.stat().st_size, 0, f"빈 증적: {kind}")

            # ── assertion expected/actual(§A.5) ──────────────────────────────
            results = art["assertions.json"]["results"]
            self.assertEqual(
                len(results), len(scenario["assertions"]),
                "시나리오가 선언한 assertion이 전부 판정돼야 한다",
            )
            for result in results:
                self.assertIn("expected", result)
                self.assertIn("actual", result)
                self.assertTrue(result["passed"], f"assertion 실패: {result}")
                self.assertEqual(result["expected"], result["actual"], f"§A.5 위반: {result}")
                self.assertEqual(result["executor"], "api")

            # ── 실 호출이 일어났다(§A.11·§A.4) ────────────────────────────────
            calls = [
                row for row in art["actions.jsonl"]
                if row["executor"] == "api"
                and row["request"]["method"] == expect_method
                and urllib.parse.urlparse(row["request"]["url"]).path == expect_path
            ]
            self.assertTrue(
                calls,
                f"{expect_method} {expect_path} 실 호출 기록이 없다: {art['actions.jsonl']}",
            )
            self.assertEqual(calls[0]["response"]["status"], 200)
            # 임대 SUT를 쳤다는 근거 — 사용자 Console 포트가 아니다(C-2).
            leased = urllib.parse.urlparse(calls[0]["request"]["url"])
            self.assertEqual(leased.hostname, "127.0.0.1")
            self.assertNotEqual(leased.port, 7823, "사용자 Console을 SUT로 쓰면 안 된다(C-2)")

            # ── 정리(§C.3) ───────────────────────────────────────────────────
            self.assertEqual(art["cleanup.json"]["result"], "complete")
            self.assertEqual(art["cleanup.json"]["leaked"], [])
            return payload, art
        finally:
            shutil.rmtree(workspace, ignore_errors=True)

    def _preserve(self, surface_id: str, art: dict) -> str:
        """run.json·assertions.json을 표면 이름으로 OS 임시 경로에 보존한다(C-5).

        run.json은 그 자체가 `scenario-mark --verdict-json`의 입력 형태다. 이 스위트는
        동결 spec의 result존을 **쓰지 않으므로**(W-12 범위 밖), 나중에 표시를 수행할
        주체가 실측 근거 없이 다시 돌릴 필요가 없도록 근거만 남긴다.
        """
        out = _EVIDENCE_ROOT / surface_id
        out.mkdir(parents=True, exist_ok=True)
        (out / "run.json").write_text(
            json.dumps(art["run.json"], ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (out / "assertions.json").write_text(
            json.dumps(art["assertions.json"], ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return str(out / "run.json")

    def _surface(self, surface_id: str, scenario: dict, home, **kwargs):
        """표면 1건을 검증하고 원장에 판정을 남긴다."""
        try:
            payload, art = self._verify(scenario, home, **kwargs)
        except Exception as exc:  # noqa: BLE001 — 실패도 원장에 남겨야 판정표가 온전하다.
            _record(surface_id, "fail", reason={"code": "verification_failed", "detail": str(exc)[:400]})
            raise
        entry_evidence = (
            f"run_id={payload['run_id']} assertions={len(art['assertions.json']['results'])}"
        )
        _record(surface_id, "pass", evidence=entry_evidence)
        SURFACE_LEDGER[-1]["verdict_json"] = self._preserve(surface_id, art)
        spec = _SPEC_BY_SURFACE.get(scenario.get("surface_ref"))
        if spec:
            SURFACE_LEDGER[-1]["spec_scenario_id"] = spec["scenario_id"]
            # spec이 선언한 assertion이 실제로 판정됐는가 — 표시 가능성의 전제다.
            judged = {row["id"] for row in art["assertions.json"]["results"]}
            self.assertIn(
                spec["assertion_ids"][0], judged,
                f"{spec['scenario_id']}가 선언한 assertion이 판정되지 않았다: {judged}",
            )
        return payload, art

    # ── 분모 되짚기(C-8) ─────────────────────────────────────────────────────
    def test_every_declared_http_surface_is_covered(self):
        """[MUST] surfaces.json이 선언한 http 표면이 이 스위트 + S-10으로 전부 덮인다.

        표면 목록을 이 파일에 복제하지 않고 분모에서 읽는다 — surfaces.json이 소유한다.
        """
        self.assertIsNotNone(_SURFACES_PATH, "surfaces.json(분모)을 찾지 못했다")
        doc = json.loads(_SURFACES_PATH.read_text(encoding="utf-8"))
        declared = {
            item["id"] for item in doc["surfaces"] if item.get("kind") == "http"
        }
        self.assertEqual(
            declared - set(_COVERED_BY_TEST) - set(_OWNED_ELSEWHERE), set(),
            "surfaces.json의 http 표면 중 다뤄지지 않은 것이 있다",
        )
        self.assertEqual(
            set(_COVERED_BY_TEST) - declared, set(),
            "분모에 없는 표면을 덮었다고 주장하고 있다(C-8 — 표면 id는 surfaces.json 소유)",
        )
        # 표만 고쳐 커버리지를 늘릴 수 없게, 각 항목이 실제 메서드를 가리키는지 본다.
        for surface_id, method in _COVERED_BY_TEST.items():
            self.assertTrue(
                callable(getattr(self, method, None)),
                f"{surface_id}가 가리키는 테스트 메서드가 없다: {method}",
            )

    # ── 표면 1: 조회 계열 ────────────────────────────────────────────────────
    def test_sut_dashboard(self):
        fx = _Isolated()
        self.addCleanup(fx.dispose)
        self._surface("sut-dashboard", _api_scenario(
            "w12-sut-dashboard", "sut-dashboard",
            _get("/api/dashboard"),
            [
                _field("a-status", "status", 200),
                _field("a-total-projects", "total_projects", 1),
                _field("a-total-tasks", "total_tasks", 1),
                _field("a-recent", "recent_activities.0.task_id", _Isolated.TASK_ID),
                _state("a-state", "/api/dashboard", "status_distribution.pending", 1),
            ],
        ), fx.home, expect_path="/api/dashboard")

    def test_sut_projects_list(self):
        fx = _Isolated()
        self.addCleanup(fx.dispose)
        self._surface("sut-projects-list", _api_scenario(
            "w12-sut-projects-list", "sut-projects-list",
            _get("/api/projects"),
            [
                _field("a-status", "status", 200),
                _field("a-name", "0.name", _Isolated.PROJECT_NAME),
                _field("a-path", "0.path", fx.project_path),
                _field("a-is-opal", "0.is_opal", True),
                _field("a-task-count", "0.task_count", 1),
                _state("a-state", "/api/projects", "0.name", _Isolated.PROJECT_NAME),
            ],
        ), fx.home, expect_path="/api/projects")

    def test_sut_projects_detail(self):
        fx = _Isolated()
        self.addCleanup(fx.dispose)
        url = f"/api/projects/detail?path={fx.quoted_project}"
        self._surface("sut-projects-detail", _api_scenario(
            "w12-sut-projects-detail", "sut-projects-detail",
            _get(url),
            [
                _field("a-status", "status", 200),
                _field("a-name", "name", _Isolated.PROJECT_NAME),
                _field("a-path", "path", fx.project_path),
                _field("a-is-opal", "is_opal", True),
                _field("a-project-md", "project_md", _Isolated.DOC_BODY),
                _field("a-doc", "docs.0.title", _Isolated.DOC_NAME),
                _state("a-state", url, "docs.0.path", _Isolated.DOC_NAME),
            ],
        ), fx.home, expect_path="/api/projects/detail")

    def test_sut_projects_doc(self):
        fx = _Isolated()
        self.addCleanup(fx.dispose)
        url = f"/api/projects/doc?path={fx.quoted_project}&name={_Isolated.DOC_NAME}"
        self._surface("sut-projects-doc", _api_scenario(
            "w12-sut-projects-doc", "sut-projects-doc",
            _get(url),
            [
                _field("a-status", "status", 200),
                _field("a-name", "name", _Isolated.DOC_NAME),
                _field("a-content", "content", _Isolated.DOC_BODY),
                _field("a-path", "path", str(fx.project / "docs" / _Isolated.DOC_NAME)),
                _state("a-state", url, "content", _Isolated.DOC_BODY),
            ],
        ), fx.home, expect_path="/api/projects/doc")

    def test_sut_tasks_list(self):
        fx = _Isolated()
        self.addCleanup(fx.dispose)
        url = f"/api/tasks?project={fx.quoted_project}"
        self._surface("sut-tasks-list", _api_scenario(
            "w12-sut-tasks-list", "sut-tasks-list",
            _get(url),
            [
                _field("a-status", "status", 200),
                _field("a-task-id", "0.task_id", _Isolated.TASK_ID),
                _field("a-column", "0.column", "pending"),
                _field("a-artifact-count", "0.artifact_count", 2),
                _state("a-state", url, "0.task_id", _Isolated.TASK_ID),
            ],
        ), fx.home, expect_path="/api/tasks")

    def test_sut_tasks_detail(self):
        fx = _Isolated()
        self.addCleanup(fx.dispose)
        url = f"/api/tasks/detail?project={fx.quoted_project}&task_id={_Isolated.TASK_ID}"
        self._surface("sut-tasks-detail", _api_scenario(
            "w12-sut-tasks-detail", "sut-tasks-detail",
            _get(url),
            [
                _field("a-status", "status", 200),
                _field("a-task-id", "task_id", _Isolated.TASK_ID),
                _field("a-current-status", "current_status", "pending"),
                _field("a-artifact", "artifacts.0", _Isolated.ARTIFACT_NAME),
                _field("a-stats", "stats.available", False),
                _state("a-state", url, "task_id", _Isolated.TASK_ID),
            ],
        ), fx.home, expect_path="/api/tasks/detail")

    def test_sut_tasks_artifact(self):
        fx = _Isolated()
        self.addCleanup(fx.dispose)
        url = (
            f"/api/tasks/artifact?project={fx.quoted_project}"
            f"&task_id={_Isolated.TASK_ID}&name={_Isolated.ARTIFACT_NAME}"
        )
        self._surface("sut-tasks-artifact", _api_scenario(
            "w12-sut-tasks-artifact", "sut-tasks-artifact",
            _get(url),
            [
                _field("a-status", "status", 200),
                _field("a-name", "name", _Isolated.ARTIFACT_NAME),
                _field("a-content", "content", _Isolated.ARTIFACT_BODY),
                _field("a-task-id", "task_id", _Isolated.TASK_ID),
                _state("a-state", url, "content", _Isolated.ARTIFACT_BODY),
            ],
        ), fx.home, expect_path="/api/tasks/artifact")

    def test_sut_memory(self):
        fx = _Isolated()
        self.addCleanup(fx.dispose)
        url = f"/api/memory?project={fx.quoted_project}"
        self._surface("sut-memory", _api_scenario(
            "w12-sut-memory", "sut-memory",
            _get(url),
            [
                _field("a-status", "status", 200),
                # fixture 프로젝트에는 메모리 인덱스가 없다 — 빈 목록이 실측값이다.
                _field("a-rows", "rows", []),
                _field("a-history", "history", []),
                _field("a-warning", "warning", None),
                _state("a-state", url, "rows", []),
            ],
        ), fx.home, expect_path="/api/memory")

    def test_sut_doctor(self):
        fx = _Isolated()
        self.addCleanup(fx.dispose)
        url = f"/api/doctor?project={fx.quoted_project}"
        payload, _art = self._surface("sut-doctor", _api_scenario(
            "w12-sut-doctor", "sut-doctor",
            _get(url),
            [
                _field("a-status", "status", 200),
                _field("a-opal-dir", "sections.0.items.1.status", "ok"),
                _field("a-agent-md", "sections.0.items.2.status", "ok"),
                _field("a-tasks", "sections.0.items.6.status", "ok"),
                _state("a-state", url, "sections.0.items.0.status", "ok"),
            ],
        ), fx.home, expect_path="/api/doctor")
        # [MUST] H-2 — 격리 홈에는 opal-cli가 없으므로 `skills`·`counts`·`verdict`
        # 축은 실행되지 않았다. 확인되지 않은 축을 확인된 것처럼 세지 않는다.
        SURFACE_LEDGER[-1]["unverified_aspects"] = [
            {
                "field": "skills/counts/verdict",
                "reason": "opal_cli_absent_in_isolated_opal_home",
                "detail": "doctor의 스킬 점검 축은 {OPAL_HOME}/tools/opal-cli/run.sh를 요구한다. "
                          "격리 홈에 그 도구를 심으면 대역이 되므로(H-2) 실행하지 않았다.",
            }
        ]

    def test_sut_config_get(self):
        fx = _Isolated()
        self.addCleanup(fx.dispose)
        self._surface("sut-config-get", _api_scenario(
            "w12-sut-config-get", "sut-config-get",
            _get("/api/config"),
            [
                _field("a-status", "status", 200),
                _field("a-scan-root", "scan_roots.0", str(fx.scan_root)),
                _field("a-scan-depth", "scan_depth", 2),
                _field("a-exclude", "exclude.0", "node_modules"),
                _field("a-prewarm", "prewarm_projects", []),
                _state("a-state", "/api/config", "scan_depth", 2),
            ],
        ), fx.home, expect_path="/api/config")

    # ── 표면 2: brain 계열(외부 의존) ────────────────────────────────────────
    def test_sut_brain_auth(self):
        """`shutil.which("claude")`만 보는 경량 표면이다 — LLM 호출 0회.

        기대값을 기계 상태에서 끌어오지 않는다: claude가 PATH에 없으면 이 표면의
        `authenticated=true` 경로를 실측할 수 없으므로 `blocked`로 남긴다(H-2).
        """
        if shutil.which("claude") is None:
            _record("sut-brain-auth", "blocked", reason={
                "code": "claude_cli_absent_on_path",
                "detail": "GET /api/brain/auth의 authenticated 경로는 PATH의 claude 실행파일을 "
                          "전제한다. 대역 바이너리를 심어 pass를 만들지 않는다(H-2).",
            })
            self.skipTest("claude CLI not on PATH")
        fx = _Isolated()
        self.addCleanup(fx.dispose)
        self._surface("sut-brain-auth", _api_scenario(
            "w12-sut-brain-auth", "sut-brain-auth",
            _get("/api/brain/auth"),
            [
                _field("a-status", "status", 200),
                _field("a-cli", "cli_available", True),
                _field("a-auth", "authenticated", True),
                _field("a-message", "message", ""),
                _state("a-state", "/api/brain/auth", "cli_available", True),
            ],
        ), fx.home, expect_path="/api/brain/auth")

    def test_sut_brain_status(self):
        """레지스트리 조회 표면 — 미등록 session_id는 `idle`이다. LLM 호출 0회."""
        fx = _Isolated()
        self.addCleanup(fx.dispose)
        sid = f"w12-{uuid.uuid4()}"
        url = f"/api/brain/status?project={fx.quoted_project}&session_id={sid}"
        self._surface("sut-brain-status", _api_scenario(
            "w12-sut-brain-status", "sut-brain-status",
            _get(url),
            [
                _field("a-status", "status", 200),
                _field("a-state", "state", "idle"),
                _field("a-active", "session_active", False),
                _field("a-message", "message", ""),
                _field("a-sid", "session_id", sid),
                _state("a-observable", url, "state", "idle"),
            ],
        ), fx.home, expect_path="/api/brain/status")

    def test_sut_brain_job(self):
        """잡 소멸·불일치 경로는 graceful error 응답이다(500 아님)."""
        fx = _Isolated()
        self.addCleanup(fx.dispose)
        sid = f"w12-{uuid.uuid4()}"
        job_id = f"w12-absent-{uuid.uuid4()}"
        url = f"/api/brain/job/{job_id}?project={fx.quoted_project}&session_id={sid}"
        self._surface("sut-brain-job", _api_scenario(
            "w12-sut-brain-job", "sut-brain-job",
            _get(url),
            [
                _field("a-status", "status", 200),
                _field("a-job-id", "job_id", job_id),
                # 본문의 `status` 필드는 단언할 수 없다 — `executors/api.py`의 `_extract`가
                # field "status"를 HTTP status로 특수 취급한다. 대신 같은 분기에서만
                # 나오는 `error_msg` 원문으로 graceful error 경로를 못 박는다.
                _field("a-error-msg", "error_msg",
                       "잡을 찾을 수 없습니다(세션이 재시작되었을 수 있습니다)"),
                _field("a-answer", "answer", ""),
                _field("a-citations", "citations", []),
                _state("a-observable", url, "job_id", job_id),
            ],
        ), fx.home, expect_path=f"/api/brain/job/{job_id}")
        # [MUST] H-2 — `status="done"` happy path는 인증된 claude 세션을 요구한다.
        SURFACE_LEDGER[-1]["unverified_aspects"] = [
            {
                "field": "status=done / answer / citations(비어 있지 않은 경우)",
                "reason": "brain_llm_dependency_absent_in_isolated_home",
                "detail": "격리 HOME 아래에는 인증된 claude 세션이 없어 잡이 done으로 끝나는 "
                          "경로를 실측할 수 없다. 대역 응답으로 채우지 않았다.",
            }
        ]

    def test_sut_brain_prime(self):
        """POST — run 단위 session_id namespace와 격리 HOME 안에서만 수행한다.

        부수효과는 그 session_id의 인메모리 세션 1건과, 격리 HOME을 보는 백그라운드
        claude 시도뿐이다. 사용자 세션·설정은 이름 공간이 겹치지 않는다(C-2).
        """
        fx = _Isolated()
        self.addCleanup(fx.dispose)
        sid = f"w12-prime-{uuid.uuid4()}"
        self._surface("sut-brain-prime", _api_scenario(
            "w12-sut-brain-prime", "sut-brain-prime",
            _post("/api/brain/prime", {"project": fx.project_path, "session_id": sid}),
            [
                _field("a-status", "status", 200),
                _field("a-priming", "priming", True),
            ],
        ), fx.home, expect_path="/api/brain/prime", expect_method="POST")
        SURFACE_LEDGER[-1]["unverified_aspects"] = [
            {
                "field": "prime 이후 state=ready 전이",
                "reason": "brain_llm_dependency_absent_in_isolated_home",
                "detail": "동기 계약({priming:true} 즉시 반환)은 실측했다. 웜 전이는 인증된 "
                          "claude 세션을 요구하므로 실측하지 않았고 승격하지 않았다(H-2). "
                          "전이 관측을 assertion으로 넣지 않은 또 다른 이유는 경합이다 — "
                          "백그라운드 스레드가 즉시 실패하면 priming/error 중 무엇이 보일지 "
                          "결정되지 않으며, equals 매처로 그 비결정을 단언할 수 없다.",
            }
        ]

    def test_sut_brain_query_transport_only(self):
        """[MUST] H-2 — `sut-brain-query`는 `blocked`다. pass로 승격하지 않는다.

        선언 응답 필드 `job_id`는 난수 UUID이고 assertion 매처는 `equals`뿐이다
        (`e2e_contract.py` C-1 동결 — `contains`는 `validate_pass_requirements`가
        뒤집는다). 즉 이 표면이 선언한 응답 필드를 단언할 수단이 없다. 잡 완료 역시
        인증된 claude 세션을 요구하며 격리 HOME에는 없다. 따라서 여기서는 전송 계층만
        실측하고 표면 판정은 `blocked`로 남긴다.
        """
        fx = _Isolated()
        self.addCleanup(fx.dispose)
        sid = f"w12-query-{uuid.uuid4()}"
        scenario = _api_scenario(
            "w12-sut-brain-query", "sut-brain-query",
            _post("/api/brain/query", {
                "question": "w12 surface transport probe",
                "project": fx.project_path,
                "session_id": sid,
            }),
            [_field("a-status", "status", 200)],
        )
        _payload, art = self._verify(
            scenario, fx.home, expect_path="/api/brain/query", expect_method="POST"
        )
        # 전송은 실제로 일어났다 — 그 사실만 증적으로 남긴다.
        self.assertEqual(art["actions.jsonl"][0]["response"]["status"], 200)
        _record("sut-brain-query", "blocked", evidence=f"run_id={_payload['run_id']} POST 200 실측", reason={
            "code": "declared_response_field_unassertable_and_llm_dependency_absent",
            "detail": "응답 필드 job_id는 난수 UUID다. e2e_contract C-1이 동결한 판정은 "
                      "expected == actual 직접 비교뿐이라(§A.5) 형태 단언이 불가능하고, "
                      "job 완료는 인증된 claude 세션을 요구하는데 격리 HOME에 없다. "
                      "전송 계층(POST 200)만 실측했고 표면은 승격하지 않았다.",
            "verified_axis": ["HTTP POST 도달", "status 200"],
            "unverified_axis": ["job_id 값·형태", "job status=done", "answer/citations"],
        })
        SURFACE_LEDGER[-1]["verdict_json"] = self._preserve("sut-brain-query", art)

    # ── 표면 3: 쓰기 계열 ────────────────────────────────────────────────────
    def test_sut_config_prewarm(self):
        """POST 쓰기 — 격리 HOME의 console.config.json만 바뀐다(C-2).

        `enabled=false`를 쓰는 이유는 두 가지다. ① 씨앗으로 심어 둔 항목이 실제로
        **빠지는** 것을 후속 observable state(`GET /api/config`)로 확인할 수 있어
        쓰기가 관측 가능한 변화를 만든다. ② `newly_added`가 참일 때만 도는
        `prewarm()`(백그라운드 claude 다중 기동)을 부르지 않는다 — 검증에 필요하지
        않은 외부 부수효과를 만들지 않는다.
        """
        fx = _Isolated(prewarm_projects=["self"])
        self.addCleanup(fx.dispose)
        self.assertEqual(
            fx.config_snapshot()["prewarm_projects"], [fx.project_path],
            "씨앗 상태가 먼저 성립해야 '빠졌다'가 관측 가능한 변화가 된다",
        )
        self._surface("sut-config-prewarm", _api_scenario(
            "w12-sut-config-prewarm", "sut-config-prewarm",
            _post("/api/config/prewarm", {"project": fx.project_path, "enabled": False}),
            [
                _field("a-status", "status", 200),
                _field("a-ok", "ok", True),
                _field("a-config", "config.prewarm_projects", []),
                # 후속 observable state — 별도 실 호출로 쓰기가 반영됐는지 본다.
                _state("a-state", "/api/config", "prewarm_projects", []),
            ],
        ), fx.home, expect_path="/api/config/prewarm", expect_method="POST")
        # 디스크에도 반영됐다. 바뀐 파일은 격리 HOME의 것뿐이다.
        self.assertEqual(fx.config_snapshot()["prewarm_projects"], [])


class TestVerdictLedger(unittest.TestCase):
    """스위트가 남긴 근거가 동결 spec의 pass 게이트를 실제로 통과하는지 되짚는다.

    W-12는 result존을 쓰지 않는다(범위 밖). 그러나 "표시할 수 있는 근거를 남겼는가"는
    여기서 확인할 수 있고, 확인하지 않으면 다음 단계가 근거 없이 표시하거나 근거를
    다시 만들어야 한다.
    """

    @classmethod
    def setUpClass(cls):
        if not _EVIDENCE_ROOT.is_dir() or not any(_EVIDENCE_ROOT.iterdir()):
            raise unittest.SkipTest("표면 run이 돌지 않았다(단건 실행) — 되짚을 근거가 없다")
        cls.spec = json.loads(_SPEC_PATH.read_text(encoding="utf-8"))
        cls.by_ref = {
            s["surface_ref"]: s for s in cls.spec["scenarios"] if s.get("surface_ref")
        }

    def test_each_preserved_verdict_satisfies_the_frozen_pass_gate(self):
        """[MUST] 판정은 `e2e_contract`가 낸다 — 여기서 리터럴로 짓지 않는다(C-125-1)."""
        for directory in sorted(_EVIDENCE_ROOT.iterdir()):
            with self.subTest(surface=directory.name):
                scenario = self.by_ref.get(directory.name)
                self.assertIsNotNone(scenario, f"동결 spec에 {directory.name} 표면 시나리오가 없다")
                run_json = json.loads((directory / "run.json").read_text(encoding="utf-8"))
                gate = e2e_contract.validate_pass_requirements(scenario, run_json)
                self.assertTrue(
                    gate["ok"],
                    f"{scenario['id']}({directory.name}) 근거가 pass 게이트를 통과하지 못한다: "
                    f"{gate.get('error')} {gate.get('detail')}",
                )
                # 달성 충실도가 표면의 요구치(real-http) 이상이어야 표시가 성립한다.
                self.assertEqual(run_json["fidelity"], e2e_orchestrator.FIDELITY_REAL_HTTP)
                self.assertEqual(scenario["required_fidelity"], e2e_orchestrator.FIDELITY_REAL_HTTP)

    def test_brain_query_is_recorded_blocked_and_not_promoted(self):
        """[MUST] H-2 — 근거가 게이트를 통과한다는 사실이 승격 사유가 되지 않는다.

        `sut-brain-query`의 run은 status 200만 단언하므로 게이트는 통과한다. 그러나
        표면이 선언한 응답 필드(`job_id`)는 판정되지 않았다. 원장이 그 사실을
        `blocked`로 유지하는지를 못 박아, 다음 단계가 게이트 통과만 보고 표시하는 일을
        막는다.
        """
        entry = next(
            (row for row in SURFACE_LEDGER if row["surface_id"] == "sut-brain-query"), None
        )
        self.assertIsNotNone(entry, "sut-brain-query 판정이 원장에 없다")
        self.assertEqual(entry["verdict"], "blocked")
        self.assertIn("unverified_axis", entry["blocked_reason"])

    def test_ledger_covers_every_declared_http_surface_once(self):
        doc = json.loads(_SURFACES_PATH.read_text(encoding="utf-8"))
        declared = {
            item["id"] for item in doc["surfaces"]
            if item.get("kind") == "http" and item["id"] not in _OWNED_ELSEWHERE
        }
        recorded = [row["surface_id"] for row in SURFACE_LEDGER]
        self.assertEqual(sorted(set(recorded)), sorted(declared))
        self.assertEqual(len(recorded), len(set(recorded)), "표면이 중복 기록됐다")


class TestUserEnvironmentUntouched(unittest.TestCase):
    """[MUST] C-2 — 스위트가 캡틴의 자산을 건드리지 않았다."""

    def test_user_console_still_serves_health(self):
        before = _USER_SNAPSHOT.get("console_health")
        if before != 200:
            self.skipTest("user Console was not up before the suite; nothing to compare")
        self.assertEqual(
            _http_status(_USER_CONSOLE_HEALTH), 200,
            "사용자 Console(127.0.0.1:7823)은 스위트 전후로 그대로여야 한다",
        )

    def test_user_console_config_bytes_unchanged(self):
        before = _USER_SNAPSHOT.get("config_bytes")
        after = _USER_CONSOLE_CONFIG.read_bytes() if _USER_CONSOLE_CONFIG.exists() else None
        self.assertEqual(
            before, after,
            "사용자 ~/.opal/console.config.json이 바뀌었다 — POST /api/config/prewarm이 "
            "격리 HOME 밖으로 샜다(C-2)",
        )


if __name__ == "__main__":
    unittest.main()
