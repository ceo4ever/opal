"""
@header {
  "module": "agent_browser",
  "layer": "util",
  "domain": "opal-tools",
  "description": "T07 agent-browser 공용 driver — orca-managed·standalone을 하나의 adapter로 구현하고 세션 소유권 모드로만 구분한다(TRD.md TD-11). §B.2 8연산(probe·open·snapshot·act·wait·assert·capture·close)을 전수 구현하며, 바이너리는 하드코딩하지 않고 Orca 설치 위치·PATH에서 해석하고 가용성·capability는 실제 실행한 probe 결과로만 판정한다(C-DRV-2, §A.8). wait timeout은 wait_kind로 fail/infra_error를 가르고(RK-6), run이 연 page/profile만 정리해 같은 worktree의 다른 탭은 보존한다(TASK.md C-2).",
  "exports": [
    "DRIVER_NAME", "SESSION_MODE_ORCA_MANAGED", "SESSION_MODE_STANDALONE",
    "RESOLUTION_SOURCES", "ORCA_RESOURCE_DIRS", "SNAPSHOT_ARTIFACTS",
    "CONSOLE_ARTIFACT", "ERRORS_ARTIFACT", "NETWORK_HAR_ARTIFACT",
    "VERIFIERS", "MATCHERS", "WAIT_KIND_ASSERTION_CONDITION",
    "AgentBrowserDriver", "resolve_binary", "detect_version", "child_env", "register"
  ]
}

lib.e2e.drivers.agent_browser — `drivers/__init__.py`가 소유한 §B.2 8연산 배선을 상속해
agent-browser 한 종류를 구현한다. 이 모듈이 집행하는 규칙은 다음과 같다.

- TD-11 [MUST]: orca-managed와 standalone은 **별도 driver가 아니라 같은 adapter의 두
  session 소유권 모드**다. 연산 구현은 공유하고, 달라지는 것은 (1) 바이너리 해석 경로,
  (2) 세션을 누가 소유하는가, (3) 정리 시 무엇을 우리 것으로 보는가뿐이다.
- C-DRV-2 [MUST]: 가용성은 `op_probe`가 **실제로 실행한** 결과로만 판정한다. `--help`
  문자열에 서브명령이 보인다거나 번들 파일이 존재한다는 사실로 승격하지 않는다(NR-7,
  §A.8 [MUST]). 실행으로 확인하지 못한 capability는 `probed=false`이므로 `available=false`다.
- TASK.md C-2 [MUST]: 정리 대상은 이 run이 연 `browserPageId`와 이 run이 만든 profile
  id뿐이다. `close --all`(모든 세션 종료)은 어떤 경로에서도 쓰지 않는다 — 같은 worktree의
  다른 탭과 사용자 세션을 보존하기 위한 구조 제약이다.
- CONTRACT.md §A.14 [MUST]: standalone 실행 시 child env에서 `AGENT_BROWSER_*` 계열을
  **제거한 뒤** 하네스 소유 값만 주입한다(TD-8 규칙 2 — ambient config 차단).
- CONTRACT.md §C.2 [MUST]: 파일을 직접 쓰지 않는다. 산출물·실행 config 모두 호출자가
  넘긴 `EvidenceWriter` 관문을 통과시킨다 — redaction 우회 경로를 만들지 않는다.
- CONTRACT.md §C.2 [MUST]: OS 조건문을 갖지 않는다(분기 지점은 `lib/e2e/process.py`
  하나뿐, TD-16). 번들 바이너리명이 플랫폼 접미사를 갖는 문제는 `sys.platform` 분기가
  아니라 **설치 위치 glob 탐색**으로 푼다 — 존재하는 것을 찾을 뿐 OS를 묻지 않는다.

미해소 사항(Q-2)의 보수 처리: `--allowed-domains`·`--config`가 global launch 옵션이라는
것은 실측했으나, **이미 실행 중인 managed 세션에 적용되는지는 실행으로 확인되지 않았다.**
따라서 orca-managed 모드의 `isolated_profile` capability는 `probed=false`로 남긴다 —
격리를 요구하는 시나리오는 `capability_missing`으로 이 후보를 제외하게 되고, 격리를
요구하지 않는 시나리오만 이 모드를 쓴다. 미확인을 `available=true`로 승격하지 않는다.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from lib.e2e import drivers as e2e_drivers
from lib.e2e import evidence as e2e_evidence

DRIVER_NAME = "agent-browser"

SESSION_MODE_ORCA_MANAGED = "orca-managed"
SESSION_MODE_STANDALONE = "standalone"

# `candidates[].resolution_source`에 싣는 해석 출처. 후보가 왜 그 바이너리를 골랐는지를
# 사후에 재구성할 수 있어야 한다(T07 완료 기준 5번).
RESOLUTION_ENV_OVERRIDE = "env-override"
RESOLUTION_ORCA_BUNDLE = "orca-bundle"
RESOLUTION_PATH = "path"
RESOLUTION_SOURCES: Tuple[str, ...] = (
    RESOLUTION_ENV_OVERRIDE,
    RESOLUTION_ORCA_BUNDLE,
    RESOLUTION_PATH,
)

# 바이너리 경로를 하드코딩하지 않는다(T07). 번들 바이너리는 플랫폼 접미사를 갖기 때문에
# (`agent-browser-darwin-arm64`) 이름을 고정할 수 없다 — 아래는 **탐색 목록**이며 OS
# 조건문이 아니다. 존재하는 항목만 순서대로 훑고, 파일명은 glob으로 맞춘다.
ORCA_RESOURCE_DIRS: Tuple[str, ...] = (
    "/Applications/Orca.app/Contents/Resources",
    "~/Applications/Orca.app/Contents/Resources",
    "/opt/Orca/resources",
)
_BINARY_GLOB = "agent-browser*"
# glob이 바이너리가 아닌 동봉 파일까지 집지 않도록 걸러낸다.
_NON_BINARY_SUFFIXES = frozenset({".json", ".md", ".txt", ".map", ".sig", ".sha256"})

ENV_BINARY_OVERRIDE = "OPAL_E2E_AGENT_BROWSER_BIN"
ENV_ORCA_RESOURCES = "OPAL_E2E_ORCA_RESOURCES"

# §A.14 [MUST] — standalone child env에서 걷어내는 ambient config 접두사.
AMBIENT_ENV_PREFIX = "AGENT_BROWSER_"

# 실행 config를 남기는 상대 경로. run artifact 디렉터리 안이며(TASK.md C-5) 관문을 거친다.
CONFIG_REL_PATH = "browser/agent-browser.config.json"

# 비파괴 조회 연산의 상한. probe가 브라우저를 기동하지 않으므로 짧게 잡는다.
_PROBE_TIMEOUT_SECONDS = 20.0

_VERSION_PATTERN = re.compile(r"(\d+\.\d+(?:\.\d+)?(?:[-+][0-9A-Za-z.-]+)?)")

# §A.8 capability ↔ artifact 고정 매핑(TD-10). 경로를 여기서만 정한다.
SNAPSHOT_ARTIFACTS = {
    "before": "browser/before.snapshot",
    "after": "browser/after.snapshot",
}
CONSOLE_ARTIFACT = "browser/console.jsonl"
ERRORS_ARTIFACT = "browser/errors.jsonl"
NETWORK_HAR_ARTIFACT = "browser/network.har"

# probe 시점에 **비파괴로 실행 가능한** capability만 여기 있다. 각 값은 그 capability를
# 확인하는 읽기 전용 서브명령이다 — `--clear`류(세션 상태 변경)와 `network har start`
# (기록 시작)는 여기 넣지 않는다. 실행해 보지 않은 것은 승격하지 않는다(§A.8 [MUST]).
_PROBEABLE_CAPABILITIES: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("snapshot", ("snapshot",)),
    ("console", ("console",)),
    ("errors", ("errors",)),
)

# §B.2 `act`의 action.kind → agent-browser 서브명령. 여기 없는 kind는 실행하지 않는다 —
# 모르는 행동을 비슷한 것으로 바꿔 실행하면 시나리오가 단언한 행동과 달라진다.
_ACT_SUBCOMMANDS: Dict[str, str] = {
    "navigate": "open",
    "click": "click",
    "dblclick": "dblclick",
    "fill": "fill",
    "type": "type",
    "press": "press",
    "hover": "hover",
    "focus": "focus",
    "check": "check",
    "uncheck": "uncheck",
    "select": "select",
    "scroll": "scroll",
    "reload": "reload",
    "back": "back",
    "forward": "forward",
}
# target을 인자로 받지 않는 행동 — 셀렉터를 붙이면 CLI 사용법 오류가 된다.
_TARGETLESS_ACTIONS = frozenset({"reload", "back", "forward"})
# value를 두 번째 위치 인자로 받는 행동.
_VALUE_ACTIONS = frozenset({"fill", "type", "select"})

# §B.2 `assert`의 verifier → 관측 경로. 자유 형식 판정을 만들지 않는다.
VERIFIER_DOM_TEXT = "dom_text"
VERIFIER_DOM_ATTRIBUTE = "dom_attribute"
VERIFIER_URL = "url"
VERIFIER_TITLE = "title"
VERIFIER_EVAL = "eval"
VERIFIERS = (VERIFIER_DOM_TEXT, VERIFIER_DOM_ATTRIBUTE, VERIFIER_URL, VERIFIER_TITLE, VERIFIER_EVAL)

MATCH_EQUALS = "equals"
MATCH_CONTAINS = "contains"
MATCHERS = (MATCH_EQUALS, MATCH_CONTAINS)

# CONTRACT.md:231 / RK-6 — wait timeout을 무엇으로 분류하는가.
# `assertion_condition`만 제품 실패(`fail`)다. 나머지는 하네스 인프라 문제(`infra_error`)이며
# wait_kind 누락도 fail이 아니라 infra_error로 fail-safe된다(기반 dispatch가 집행).
WAIT_KIND_ASSERTION_CONDITION = "assertion_condition"
# `session list`가 활성 세션 0건일 때 내는 문구. 문자열로 가용성을 **승격**하지는 않고,
# 활성 세션이 없다는 부정 판정에만 쓴다(승격 금지가 §A.8의 [MUST]다).
_NO_SESSION_MARKER = "no active sessions"


# ─── 바이너리 해석 ───────────────────────────────────────────────────────────
def _executable_candidates(directory: Path) -> List[Path]:
    try:
        entries = sorted(directory.glob(_BINARY_GLOB))
    except OSError:
        return []
    return [
        item
        for item in entries
        if item.is_file()
        and item.suffix.lower() not in _NON_BINARY_SUFFIXES
        and os.access(str(item), os.X_OK)
    ]


def resolve_binary(session_mode: str, *, environ: Optional[Mapping[str, str]] = None) -> Tuple[Optional[str], Optional[str]]:
    """`(binary_path, resolution_source)`를 해석한다. 못 찾으면 `(None, None)`.

    모드가 해석 경로를 가른다 — 이것이 TD-11에서 두 모드가 실제로 달라지는 지점 중 하나다.

    - `orca-managed`: Orca 설치 위치의 번들 바이너리를 쓴다. 이 모드의 전제가 "Orca가
      소유한 runtime에 붙는다"이므로 번들 밖 바이너리를 끌어오면 모드의 의미가 깨진다.
    - `standalone`: 하네스가 세션을 직접 소유하므로 Orca 번들에 의존하지 않는다. 환경
      지정값과 `PATH`만 본다 — Orca 번들로 조용히 되돌아가면 "standalone 전환이 됐다"는
      관측이 거짓이 된다(S-9/AC-5는 바이너리 부재를 `executor_unavailable`로 확정한다).

    두 모드 모두 명시적 환경 지정(`OPAL_E2E_AGENT_BROWSER_BIN`)이 최우선이다 — CI·검증
    실행이 특정 바이너리를 고정할 수 있어야 한다.
    """
    env = os.environ if environ is None else environ

    override = (env.get(ENV_BINARY_OVERRIDE) or "").strip()
    if override:
        path = Path(override).expanduser()
        if path.is_file() and os.access(str(path), os.X_OK):
            return (str(path), RESOLUTION_ENV_OVERRIDE)
        # 지정했는데 쓸 수 없으면 조용히 다른 바이너리로 대체하지 않는다.
        return (None, None)

    if session_mode == SESSION_MODE_ORCA_MANAGED:
        search: List[str] = []
        explicit = (env.get(ENV_ORCA_RESOURCES) or "").strip()
        if explicit:
            search.append(explicit)
        search.extend(ORCA_RESOURCE_DIRS)
        for entry in search:
            found = _executable_candidates(Path(entry).expanduser())
            if found:
                return (str(found[0]), RESOLUTION_ORCA_BUNDLE)
        return (None, None)

    on_path = shutil.which(DRIVER_NAME, path=env.get("PATH"))
    if on_path:
        return (on_path, RESOLUTION_PATH)
    return (None, None)


def detect_version(binary_path: str, *, timeout: float = _PROBE_TIMEOUT_SECONDS) -> Optional[str]:
    """`--version` 원문에서 semver를 뽑는다. **가용성 판정에 쓰지 않는다**(C-DRV-2).

    이 값의 유일한 용도는 §A.15 manifest 게이트(`minimum_version` 미만을 probe 없이
    제외)와 `candidates[].version` 기록이다. 버전이 읽힌다는 사실은 실행 가능하다는
    근거가 아니므로 `available`은 여전히 `op_probe`만 결정한다.
    """
    completed = _run_cli([binary_path, "--version"], timeout=timeout)
    if completed is None or completed.returncode != 0:
        return None
    match = _VERSION_PATTERN.search(completed.stdout or "")
    return match.group(1) if match else None


def _run_cli(
    argv: Sequence[str],
    *,
    timeout: float = _PROBE_TIMEOUT_SECONDS,
    env: Optional[Mapping[str, str]] = None,
) -> Optional[subprocess.CompletedProcess]:
    """비파괴 조회 실행. 실행 자체가 불가능하면 None을 돌려준다.

    프로세스 회수가 필요한 장기 실행은 이 경로로 띄우지 않는다 — 그런 기동은
    `lib/e2e/process.py`의 프로세스 그룹 경로가 소유한다(§C.1, C-9).
    """
    try:
        return subprocess.run(
            list(argv),
            capture_output=True,
            text=True,
            timeout=timeout,
            env=dict(env) if env is not None else None,
        )
    except (OSError, subprocess.SubprocessError):
        return None


def child_env(
    session_mode: str,
    *,
    environ: Optional[Mapping[str, str]] = None,
    injected: Optional[Mapping[str, str]] = None,
) -> Dict[str, str]:
    """child에 넘길 환경을 만든다.

    §A.14 [MUST] — standalone은 `AGENT_BROWSER_*` 계열을 **전부 제거한 뒤** 하네스 소유
    값만 주입한다. 사용자 셸이나 `~/.agent-browser/config.json`을 가리키는 ambient 설정이
    남아 있으면 우리가 지정한 allowed domains·profile 격리가 조용히 뒤집힌다(TD-8 규칙 2).
    orca-managed는 Orca가 소유한 runtime의 환경을 하네스가 재작성하지 않는다(C-2).
    """
    base = dict(os.environ if environ is None else environ)
    if session_mode == SESSION_MODE_STANDALONE:
        for key in [name for name in base if name.startswith(AMBIENT_ENV_PREFIX)]:
            base.pop(key, None)
    base.update(dict(injected or {}))
    return base


# ─── driver ──────────────────────────────────────────────────────────────────
class AgentBrowserDriver(e2e_drivers.BrowserDriver):
    """orca-managed·standalone 공용 adapter (TD-11).

    연산 구현은 두 모드가 공유한다. 모드가 바꾸는 것은 세션 소유권 — 즉 세션을 우리가
    만들었는지, 그래서 정리 대상에 세션이 포함되는지 여부다. `_owned_pages`·
    `_owned_profiles`에 **우리가 연 것만** 담기므로, 같은 worktree의 다른 탭은 정리
    경로에서 구조적으로 닿을 수 없다(C-2).
    """

    name = DRIVER_NAME

    def __init__(
        self,
        *,
        session_mode: str,
        runtime_context: Optional[Mapping[str, Any]] = None,
        environ: Optional[Mapping[str, str]] = None,
    ):
        if session_mode not in (SESSION_MODE_ORCA_MANAGED, SESSION_MODE_STANDALONE):
            raise e2e_drivers.DriverError(
                "driver_session_mode_invalid",
                f"{session_mode!r} is not one of {(SESSION_MODE_ORCA_MANAGED, SESSION_MODE_STANDALONE)}",
            )
        self.session_mode = session_mode
        self.runtime_context: Dict[str, Any] = dict(runtime_context or {})
        self._environ = dict(os.environ if environ is None else environ)

        self.binary_path, self.resolution_source = resolve_binary(session_mode, environ=self._environ)
        # §A.15 게이트는 probe 이전에 돌아야 하므로 버전만 먼저 읽는다. 가용성과는 무관하다.
        self.declared_version: Optional[str] = (
            detect_version(self.binary_path) if self.binary_path else None
        )

        # 이 run이 소유한 자원만 담는다 — 정리 범위의 단일 근거다(C-2).
        self._owned_pages: List[str] = []
        self._owned_profiles: List[str] = []
        self._owns_session: bool = False
        self._config_path: Optional[str] = None

        # 실제 `assert` 연산이 만든 결과만 쌓인다. `open`·`act`는 여기에 아무 것도 넣지
        # 않으므로, 그것만 수행한 run은 비어 있고 `validate_pass_requirements`가
        # `assertion_required`로 `fail`을 낸다(C-DRV-4).
        self._assertion_results: List[Dict[str, Any]] = []
        self._snapshots: Dict[str, str] = {}
        # 증적 관문을 실제로 통과한 종류만 쌓인다 — `observed_evidence()`의 유일한 근거다.
        self._captured_kinds: List[str] = []
        # probe가 실행으로 확인한 capability 표. `op_capture`가 "확인된 수단"만 쓰게 한다.
        self._capabilities: Dict[str, Dict[str, Any]] = e2e_drivers.default_capabilities()
        # 연산별 호출 횟수. 같은 연산의 2회차 호출은 재시도로 관측되므로(S-27 (d-1))
        # 이 대장이 그 사실을 사후에 드러내는 근거가 된다.
        self._op_calls: Dict[str, int] = {}

    # ── 세션·config ──────────────────────────────────────────────────────────
    @property
    def session_name(self) -> str:
        """이 run 전용 세션 이름. run_id로 갈라 다른 run·사용자 세션과 겹치지 않게 한다."""
        run_id = str(self.runtime_context.get("run_id") or "unknown")
        return f"opal-e2e-{run_id}"

    def build_config(self, *, allowed_domains: Sequence[str] = ()) -> Dict[str, Any]:
        """standalone에 넘길 explicit config를 만든다.

        allowed domains는 **임대 localhost + 시나리오가 선언한 외부 origin**으로만 제한한다.
        와일드카드를 넣지 않는 것이 이 config의 존재 이유다 — 임대 포트 밖으로 나가는 트래픽이
        생기면 그 run의 관측은 SUT의 것이 아니게 된다.
        """
        leased = [str(url) for url in (self.runtime_context.get("leased_urls") or []) if url]
        declared = [str(origin) for origin in (self.runtime_context.get("allowed_origins") or []) if origin]
        domains = list(dict.fromkeys([*leased, *declared, *[str(item) for item in allowed_domains if item]]))
        return {
            "session": self.session_name,
            "allowedDomains": domains,
            "profile": self._profile_id(),
        }

    def _profile_id(self) -> str:
        return f"opal-e2e-{self.runtime_context.get('run_id') or 'unknown'}"

    def write_config(self, writer: Any, *, allowed_domains: Sequence[str] = ()) -> str:
        """실행 config를 증적 관문을 통해 artifact 디렉터리에 남기고 **절대경로**를 돌려준다.

        `--config`는 없거나 잘못된 경로면 오류로 종료하는 결정론적 옵션이므로(실측), 상대
        경로나 ambient 탐색에 기대지 않고 방금 쓴 절대경로를 그대로 넘긴다.
        """
        path = writer.write_json(
            CONFIG_REL_PATH,
            self.build_config(allowed_domains=allowed_domains),
            kind=None,
            observed=False,
        )
        self._config_path = os.path.abspath(str(path))
        return self._config_path

    def _base_argv(self) -> List[str]:
        """모든 CLI 호출의 공통 앞부분 — 바이너리 + launch scope 옵션."""
        if not self.binary_path:
            raise e2e_drivers.DriverError(
                "agent_browser_binary_not_found",
                f"no agent-browser binary resolved for session_mode={self.session_mode!r}",
            )
        argv = [self.binary_path]
        if self.session_mode == SESSION_MODE_STANDALONE and self._config_path:
            argv += ["--config", self._config_path]
        return argv

    # ── 공통 배선 ────────────────────────────────────────────────────────────
    def dispatch(self, operation: str, payload: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        """§B.2 연산 1회. 호출 횟수를 대장에 남긴 뒤 기반 클래스에 위임한다.

        기반 `dispatch()`가 연산 이름과 `wait_kind` 필수(C-DRV-1)를 이미 집행하므로
        여기서 다시 판정하지 않는다 — 계약 검증이 두 곳에 갈라지면 어느 쪽이 참인지가
        모호해진다. 이 override가 더하는 것은 관측(호출 횟수) 하나뿐이다.
        """
        self._op_calls[operation] = self._op_calls.get(operation, 0) + 1
        return super().dispatch(operation, payload)

    def operation_calls(self) -> Dict[str, int]:
        """연산별 호출 횟수. 2 이상은 같은 연산의 재시도가 일어났다는 뜻이다(S-27 (d-1))."""
        return dict(self._op_calls)

    def _run(self, args: Sequence[str]) -> Optional[subprocess.CompletedProcess]:
        """launch scope 옵션을 붙여 CLI를 한 번 실행한다."""
        return _run_cli(
            [*self._base_argv(), *[str(item) for item in args]],
            env=child_env(self.session_mode, environ=self._environ),
        )

    def _require(self, args: Sequence[str], *, detail_code: str) -> subprocess.CompletedProcess:
        """실행하고 성공을 요구한다. 실패는 `DriverError`이며 호출자가 §C.7로 분류한다."""
        completed = self._run(args)
        if completed is None:
            raise e2e_drivers.DriverError(detail_code, f"{self.binary_path}: {' '.join(args)} could not be executed")
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip()
            raise e2e_drivers.DriverError(detail_code, f"{' '.join(args)}: {detail}")
        return completed

    def _page_id(self, request: Mapping[str, Any]) -> Optional[str]:
        """호출자가 쓰는 page 식별자를 읽는다.

        §B.2는 이 값을 `handle`로 부르고 orchestrator의 browser 경로는 `page_id`로 부른다.
        둘 다 받아들이고 출력에는 둘 다 싣는다 — 이름 차이 하나로 정리 대장이 비어
        보이면 소유 자원이 회수되지 않는다(C-2).
        """
        value = request.get("page_id")
        if value is None:
            value = request.get("handle")
        return None if value is None else str(value)

    def _writer(self, request: Mapping[str, Any]):
        """증적 관문. orchestrator는 runtime_context에 `writer`로 싣는다(§C.2)."""
        return (
            request.get("evidence_writer")
            or request.get("writer")
            or self.runtime_context.get("evidence_writer")
            or self.runtime_context.get("writer")
        )

    def _log_action(
        self,
        *,
        step_id: str,
        action: str,
        result: str,
        elapsed_ms: int,
        step_role: Optional[str] = None,
        wait_kind: Optional[str] = None,
        error_code: Optional[str] = None,
        current_url: Optional[str] = None,
    ) -> None:
        """§A.4 `actions.jsonl` 행을 공유 ActionLog에 적는다(파일은 쓰지 않는다, C-EXE-3).

        ActionLog는 orchestrator가 run 하나에 하나만 만들어 runtime_context로 내려준다 —
        browser와 api가 같은 로그에 seq를 이어 붙여야 §A.11 상호 참조가 성립한다.
        """
        log = self.runtime_context.get("action_log")
        if log is None:
            return
        kwargs: Dict[str, Any] = {
            "step_id": str(step_id),
            "executor": "browser",
            "action": action,
            "result": result,
            "elapsed_ms": int(elapsed_ms),
            "wait_kind": wait_kind,
            "error_code": error_code,
            "current_url": current_url,
        }
        if step_role is not None:
            kwargs["step_role"] = step_role
        log.record(**kwargs)

    # ── §B.2 probe ───────────────────────────────────────────────────────────
    def op_probe(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """§A.8 probe 결과를 **실행 결과로만** 만든다(C-DRV-2 [MUST]).

        어느 capability도 실행으로 확인되기 전에는 `probed=false`이며, 따라서
        `available=false`다. 번들에 `console`·`errors`·`network har` 서브명령이 보인다는
        사실은 여기서 아무 것도 승격시키지 않는다 — 승격 금지가 §A.8의 [MUST]다.
        """
        if not self.binary_path:
            return self._unavailable("agent_browser_binary_not_found")

        version = self.declared_version
        capabilities = e2e_drivers.default_capabilities()

        if self.session_mode == SESSION_MODE_ORCA_MANAGED:
            listing = _run_cli([*self._base_argv(), "session", "list"])
            if listing is None:
                # 바이너리는 있는데 실행이 안 된다 — "수단 없음"이 아니라 "수단이 깨졌음"이다.
                raise e2e_drivers.DriverError(
                    "agent_browser_probe_exec_failed",
                    f"{self.binary_path}: session list could not be executed",
                )
            if listing.returncode != 0:
                return self._unavailable("agent_browser_session_list_failed", version=version)
            if _NO_SESSION_MARKER in (listing.stdout or "").lower():
                # Orca runtime이 세션을 들고 있지 않다 — provider_unavailable이므로
                # 다음 후보로 전환할 수 있다(TD-13이 금지하는 것은 infra_error 전환이다).
                return self._unavailable("orca_runtime_no_active_session", version=version)
            self._probe_capabilities(capabilities)
            return {
                "available": True,
                "version": version,
                "capabilities": capabilities,
            }

        # standalone — 세션을 하네스가 만든다. 바이너리가 우리 config를 받아들이는지까지
        # 실제로 실행해 확인한다(없거나 잘못된 --config는 오류 종료하므로 판정이 결정론적이다).
        listing = _run_cli(
            [*self._base_argv(), "session", "list"],
            env=child_env(self.session_mode, environ=self._environ),
        )
        if listing is None:
            raise e2e_drivers.DriverError(
                "agent_browser_probe_exec_failed",
                f"{self.binary_path}: session list could not be executed",
            )
        if listing.returncode != 0:
            return self._unavailable("agent_browser_config_rejected", version=version)
        self._probe_capabilities(capabilities)
        # standalone은 explicit config로 profile을 **우리가** 만든다. 바로 위에서 그 config가
        # 실제로 수용됨을 실행으로 확인했으므로 격리는 추정이 아니라 관측이다.
        capabilities["isolated_profile"] = {"available": True, "route": "exec", "probed": True}
        return {"available": True, "version": version, "capabilities": capabilities}

    def _probe_capabilities(self, capabilities: Dict[str, Dict[str, Any]]) -> None:
        """probe 시점에 capability 서브명령을 **실행하지 않는다**. 이유를 남긴다.

        [MUST] 동결 RED `test_red_s27_no_retry_on_product_failure.py` (d-1)은 **같은 연산
        시그니처가 한 run에서 두 번 나타나는 것**을 retry로 판정해 금지한다. `console`을
        probe에서 한 번, `op_capture`에서 또 한 번 부르면 정확히 그 중복이 된다 — 목적이
        달라도 관측되는 것은 "같은 연산 2회"다.

        그래서 capability의 단 한 번뿐인 실행을 **증적이 함께 나오는 쪽**(`op_capture`)에
        둔다. 가용성은 여전히 추정이 아니라 실행 결과로 정해지고(C-DRV-2), 그 결과는
        `_capabilities`에 기록돼 이후 판단의 근거가 된다. 바뀌는 것은 판정 **시점**뿐이다.

        결과적으로 `probe.json`에는 아래 키가 `probed=false`로 남는다. §A.8 [MUST]의
        보수 규칙(`probed=false` → `available=false`)을 그대로 따르는 상태이며, 그 대가로
        `console`·`errors`를 `required_evidence`로 요구하는 시나리오는 이 후보를
        `capability_missing`으로 제외하게 된다 — 미확인을 승격하는 것보다 이쪽이 안전하다.

        - `network_har`: 읽기 전용 형태가 없다. `har start`는 기록을 시작해 세션 상태를
          바꾸므로 probe 수단이 될 수 없다 — 확인하려고 부작용을 만들지 않는다.
        - `screenshot`·`snapshot`: 열린 page가 있어야 한다. probe 시점에는 page가 없다.
        - orca-managed의 `isolated_profile`: Q-2 미해소. `--config`·`--allowed-domains`가
          **이미 실행 중인** managed 세션에 적용되는지를 실행으로 확인하지 못했다. 미확인을
          `available=true`로 승격하지 않는다(PM 확정).
        """
        self._capabilities = {key: dict(value) for key, value in capabilities.items()}

    def _unavailable(self, reason: str, *, version: Optional[str] = None) -> Dict[str, Any]:
        return {
            "available": False,
            "version": version,
            "unavailable_reason": reason,
            "capabilities": e2e_drivers.default_capabilities(),
        }

    # ── §B.2 open / close — 소유권이 갈리는 두 연산 ──────────────────────────
    def op_open(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """`{url, isolation_key}` → `{handle, owned, current_url}`.

        여기서 돌려주는 handle이 정리 대장의 유일한 입구다. 우리가 연 page만 `_owned_pages`에
        오르므로 `close`가 다른 탭에 닿을 수 없다(C-2).
        """
        url = request.get("url")
        if not url:
            raise e2e_drivers.DriverError("driver_open_url_required", "open requires a url")

        started = time.monotonic()
        completed = self._run(["open", str(url)])
        elapsed = int((time.monotonic() - started) * 1000)
        if completed is None or completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip() if completed else "exec failed"
            self._log_action(
                step_id="open", action="open", result="error", elapsed_ms=elapsed,
                error_code="agent_browser_open_failed", current_url=str(url),
            )
            raise e2e_drivers.DriverError("agent_browser_open_failed", f"{url}: {detail}")

        handle = str(request.get("isolation_key") or self.session_name)
        self._owned_pages.append(handle)
        if self.session_mode == SESSION_MODE_STANDALONE:
            self._owns_session = True
            profile_id = self._profile_id()
            if profile_id not in self._owned_profiles:
                self._owned_profiles.append(profile_id)
        self._log_action(
            step_id="open", action="open", result="ok", elapsed_ms=elapsed, current_url=str(url)
        )
        # `handle`은 §B.2의 이름, `page_id`는 orchestrator browser 경로의 이름이다. 둘 다
        # 실어 어느 호출자든 같은 자원을 가리키게 한다.
        return {"handle": handle, "page_id": handle, "owned": True, "current_url": str(url)}

    def op_close(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """`{handle}` → `{closed, released[], leaked[]}`.

        [MUST] `close --all`을 쓰지 않는다. 그 플래그는 **모든 세션**을 닫으므로 사용자
        브라우저와 같은 worktree의 다른 run까지 끌어내린다(C-2). 우리가 대장에 올린 page와
        profile만, 그것도 handle 단위로 닫는다. 대장에 없는 handle은 거부한다 — 남의
        자원을 우리 것으로 착각해 닫는 경로를 아예 열지 않기 위해서다.
        """
        handle = self._page_id(request)
        if handle is not None and str(handle) not in self._owned_pages:
            raise e2e_drivers.DriverError(
                "driver_close_unowned_handle",
                f"{handle!r} was not opened by this run — refusing to close a resource we do not own",
            )

        targets = [str(handle)] if handle is not None else list(self._owned_pages)
        released: List[str] = []
        leaked: List[str] = []
        for item in targets:
            completed = self._run(["tab", "close"])
            if completed is not None and completed.returncode == 0:
                released.append(item)
                if item in self._owned_pages:
                    self._owned_pages.remove(item)
            else:
                leaked.append(item)

        # standalone에서 우리가 만든 세션·profile만 추가로 회수한다. orca-managed는 세션을
        # Orca가 소유하므로 세션 자체에 손대지 않는다 — 소유권 모드가 정리 범위를 가르는
        # 지점이 바로 여기다(TD-11).
        if self.session_mode == SESSION_MODE_STANDALONE and self._owns_session and not self._owned_pages:
            released.extend(self._owned_profiles)
            self._owned_profiles = []
            self._owns_session = False

        return {"closed": not leaked, "released": released, "leaked": leaked}

    # ── §B.2 snapshot / act / wait ───────────────────────────────────────────
    def op_snapshot(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """`{handle|page_id, label}` → `{snapshot, current_url, artifact_path}`.

        `snapshot`은 접근성 트리를 텍스트로 낸다 — 스크린샷과 달리 semantic assertion의
        근거가 되므로 `op_assert`가 참조할 수 있도록 라벨별로 보관한다.
        """
        started = time.monotonic()
        completed = self._require(["snapshot"], detail_code="agent_browser_snapshot_failed")
        elapsed = int((time.monotonic() - started) * 1000)

        label = str(request.get("label") or "after")
        text = completed.stdout or ""
        self._snapshots[label] = text

        artifact_path = SNAPSHOT_ARTIFACTS.get(label, f"browser/{label}.snapshot")
        writer = self._writer(request)
        written = (
            writer.write_text(artifact_path, text, kind="snapshot", observed=True)
            if writer is not None
            else None
        )
        if written is not None and "snapshot" not in self._captured_kinds:
            self._captured_kinds.append("snapshot")
        self._log_action(
            step_id=str(request.get("step_id") or f"snapshot:{label}"),
            action="snapshot", result="ok", elapsed_ms=elapsed,
        )
        return {
            "snapshot": text,
            "current_url": request.get("current_url"),
            "artifact_path": written or artifact_path,
        }

    def op_act(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """`{handle|page_id, step_id, action:{kind, target, value?}}` → `{ok, action_result, current_url}`.

        [MUST] 모르는 `kind`는 비슷한 서브명령으로 바꿔 실행하지 않는다 — 시나리오가 단언한
        행동과 다른 행동을 하면 그 run의 `pass`는 다른 것을 증명한 것이 된다.
        """
        action = request.get("action") or {}
        if not isinstance(action, Mapping):
            raise e2e_drivers.DriverError("driver_act_action_required", "act requires an action object")
        kind = str(action.get("kind") or "")
        step_id_for_log = str(request.get("step_id") or kind or "act")

        if not kind:
            # 행동 종류가 **아예 없다**. 현재 `scenario_adapter.build_execution_plan`은
            # API 형태 키(`method`·`url`·`body`…)만 action으로 옮기므로 browser step의
            # action에는 `kind`가 실리지 않는다 — 어댑터에 browser 행동 어휘가 없다.
            #
            # 이것을 `infra_error`로 올리면 "driver가 실행 중 깨졌다"로 기록돼 실제 원인
            # (어댑터의 번역 공백)이 사라진다. 그렇다고 아무 행동으로 대체해 성공시키면
            # 시나리오가 단언한 것과 다른 것을 증명하게 된다. 그래서 **실행하지 않고**
            # 그 사실을 action log에 남긴 뒤 `ok=false`로 돌려준다 — 행동이 없었으므로
            # 뒤따르는 assertion도 근거를 얻지 못하고, run은 pass가 아니라 fail로 남는다
            # (C-DRV-4). 공백은 증적에 보이고 판정은 거짓이 되지 않는다.
            self._log_action(
                step_id=step_id_for_log, action="act", result="error", elapsed_ms=0,
                step_role=action.get("step_role"),
                error_code="agent_browser_action_kind_absent",
            )
            return {
                "ok": False,
                "action_result": {
                    "error_code": "agent_browser_action_kind_absent",
                    "detail": "step action carries no browser action kind — nothing was performed",
                },
                "current_url": None,
            }

        subcommand = _ACT_SUBCOMMANDS.get(kind)
        if subcommand is None:
            # 이름이 **있는데** 우리가 모르는 행동이다. 비슷한 것으로 바꿔 실행하지 않고
            # 크게 드러낸다 — 조용히 넘기면 시나리오가 요구한 행동이 사라진 채로 판정된다.
            raise e2e_drivers.DriverError(
                "agent_browser_unsupported_action",
                f"{kind!r} is not one of {sorted(_ACT_SUBCOMMANDS)}",
            )

        args: List[str] = [subcommand]
        target = action.get("target")
        if kind not in _TARGETLESS_ACTIONS and target is not None:
            args.append(str(target))
        if kind in _VALUE_ACTIONS and action.get("value") is not None:
            args.append(str(action.get("value")))

        step_id = str(request.get("step_id") or kind)
        started = time.monotonic()
        completed = self._run(args)
        elapsed = int((time.monotonic() - started) * 1000)
        if completed is None or completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip() if completed else "exec failed"
            self._log_action(
                step_id=step_id, action=kind, result="error", elapsed_ms=elapsed,
                step_role=action.get("step_role"),
                error_code="agent_browser_act_failed",
            )
            raise e2e_drivers.DriverError("agent_browser_act_failed", f"{kind}: {detail}")

        current_url = str(target) if kind == "navigate" else None
        self._log_action(
            step_id=step_id, action=kind, result="ok", elapsed_ms=elapsed,
            step_role=action.get("step_role"), current_url=current_url,
        )
        return {
            "ok": True,
            "action_result": {"stdout": (completed.stdout or "").strip()},
            "current_url": current_url,
        }

    def op_wait(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """`{handle|page_id, condition, wait_kind, timeout_ms}` → `{satisfied, wait_kind, elapsed_ms}`.

        [MUST] timeout의 의미는 `wait_kind`가 가른다(RK-6, CONTRACT.md:231).

        - `assertion_condition`: 기다린 조건이 제품 상태다. 충족되지 않은 것은 **제품 실패**
          이므로 `satisfied=false`로 **정상 반환**하고 호출자가 `fail`로 판정하게 한다.
        - 그 외(`navigation_ready`·`transport`): 하네스가 실행 환경을 세우지 못한 것이므로
          `DriverError`를 올려 `infra_error`가 되게 한다. 이것을 `fail`로 내리면 인프라
          문제가 제품 실패로 위장돼 기록된다.

        `wait_kind` 누락은 기반 `dispatch()`가 실행 전에 거부한다(C-DRV-1) — 그 경로도
        `fail`이 아니라 `infra_error`로 fail-safe된다.
        """
        wait_kind = str(request.get("wait_kind") or "")
        condition = request.get("condition")
        args: List[str] = ["wait"]
        if isinstance(condition, Mapping):
            for key in ("selector", "text", "ms"):
                if condition.get(key) is not None:
                    args.append(str(condition.get(key)))
                    break
        elif condition is not None:
            args.append(str(condition))

        started = time.monotonic()
        completed = self._run(args)
        elapsed = int((time.monotonic() - started) * 1000)
        satisfied = completed is not None and completed.returncode == 0

        # §A.4 — `result`는 `ok`|`error` 둘뿐이고 사유는 `error_code`가 싣는다. timeout을
        # 세 번째 enum 값으로 만들지 않는다(그건 §A.4 재정의이며 C-8 위반이다).
        #
        # 시간 안에 조건이 서지 않은 wait은 **연산이 목적을 이루지 못한 것**이므로 error
        # 행이다. 계약 자신이 그렇게 모델링한다 — `e2e_contract.py:229-231`은 error가
        # `wait_failed`인 행을 받아 `wait_kind == "assertion_condition"`일 때만 `fail`로,
        # 아니면 `infra_error`로 가른다. 즉 fail/infra_error를 가르는 것은 `result`가
        # 아니라 `wait_kind`이고, 그래서 `result`를 판정값으로 쓸 필요가 없다(RK-6).
        self._log_action(
            step_id=str(request.get("step_id") or "wait"),
            action="wait",
            result="ok" if satisfied else "error",
            elapsed_ms=elapsed,
            wait_kind=wait_kind,
            error_code=None if satisfied else "wait_failed",
        )

        if not satisfied and wait_kind != WAIT_KIND_ASSERTION_CONDITION:
            detail = (completed.stderr or completed.stdout or "").strip() if completed else "exec failed"
            raise e2e_drivers.DriverError(
                "agent_browser_wait_failed",
                f"wait_kind={wait_kind!r} is an infrastructure wait, not a product condition: {detail}",
            )
        return {"satisfied": satisfied, "wait_kind": wait_kind, "elapsed_ms": elapsed}

    # ── §B.2 assert — C-DRV-4의 본질 ─────────────────────────────────────────
    def op_assert(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """`{handle|page_id, assertion:{id, verifier, expected, target?, match?}}` → `{id, expected, actual, passed}`.

        [MUST] 여기서 만든 결과만 `assertion_results()`에 쌓인다. `open`·`act`만 수행한 run은
        이 목록이 비고 `validate_pass_requirements`가 `assertion_required`로 `fail`을
        낸다(C-DRV-4) — 화면을 열었다는 사실은 단언이 아니다.

        관측값(`actual`)은 브라우저에서 **실제로 읽어 온 값**이며, 판정은 expected와의
        비교로만 만든다. 자유 형식 판정을 두지 않는 이유는 §9.2의 "정상으로 보인다는
        서술은 assertion이 아니다"를 코드로 막기 위해서다.
        """
        assertion = request.get("assertion") or {}
        if not isinstance(assertion, Mapping) or assertion.get("id") is None:
            raise e2e_drivers.DriverError("driver_assert_id_required", "assert requires assertion.id")
        verifier = str(assertion.get("verifier") or "")
        if not verifier:
            # 무엇으로 검증할지가 명시되지 않았다. 관측 근거가 없으므로 이 단언은 **통과할
            # 수 없다** — "정상으로 보인다"는 서술을 assertion으로 승격시키지 않는 것이
            # §9.2와 C-DRV-4의 요지다. 예외로 올려 `infra_error`를 만들면 제품 판정이
            # 인프라 오류로 위장되므로, 실패한 단언 결과로 기록해 fail로 남긴다.
            record = {
                "id": str(assertion.get("id")),
                "expected": assertion.get("expected"),
                "actual": None,
                "passed": False,
                "verifier": None,
                "match": None,
                "reason": "assertion_verifier_unspecified",
            }
            self._assertion_results.append(record)
            # 이 경로는 **연산을 수행하지 못한** 경우다 — 무엇을 읽어야 할지 모르므로
            # 관측 자체가 없었다. §A.4의 `error`가 정확히 이것이고 사유는 error_code가 싣는다.
            self._log_action(
                step_id=str(request.get("step_id") or record["id"]),
                action="assert", result="error", elapsed_ms=0,
                error_code="assertion_verifier_unspecified",
            )
            return dict(record)
        if verifier not in VERIFIERS:
            raise e2e_drivers.DriverError(
                "agent_browser_unsupported_verifier", f"{verifier!r} is not one of {VERIFIERS}"
            )
        match = str(assertion.get("match") or MATCH_EQUALS)
        if match not in MATCHERS:
            raise e2e_drivers.DriverError(
                "agent_browser_unsupported_matcher", f"{match!r} is not one of {MATCHERS}"
            )

        if verifier == VERIFIER_EVAL:
            args = ["eval", str(assertion.get("script") or assertion.get("target") or "")]
        elif verifier == VERIFIER_URL:
            args = ["get", "url"]
        elif verifier == VERIFIER_TITLE:
            args = ["get", "title"]
        elif verifier == VERIFIER_DOM_ATTRIBUTE:
            args = ["get", "attr", str(assertion.get("attribute") or ""), str(assertion.get("target") or "")]
        else:
            args = ["get", "text", str(assertion.get("target") or "")]

        started = time.monotonic()
        completed = self._require(args, detail_code="agent_browser_assert_failed")
        elapsed = int((time.monotonic() - started) * 1000)

        actual = (completed.stdout or "").strip()
        expected = assertion.get("expected")
        passed = (
            str(expected) in actual if match == MATCH_CONTAINS else actual == str(expected)
        )
        record = {
            "id": str(assertion.get("id")),
            "expected": expected,
            "actual": actual,
            "passed": bool(passed),
            "verifier": verifier,
            "match": match,
        }
        self._assertion_results.append(record)
        # §A.4 [MUST] — `result`는 **연산이 정상적으로 끝났는가**이지 판정 결과가 아니다.
        # 여기까지 왔다면 브라우저에서 값을 실제로 읽어 왔고 비교까지 끝났다. 기대와
        # 달랐다는 사실은 §A.5 `assertions.json`의 `passed`·`expected`·`actual`과 이
        # 연산의 반환값이 이미 싣는다.
        #
        # 판정 결과를 `result`에 겹쳐 쓰면 **실패한 assertion 하나가 연산 실패로 읽혀**
        # run 전체가 `infra_error`가 된다 — 제품 실패가 인프라 오류로 위장되는 바로 그
        # 경로이며 C-3·§C.7이 막으려는 것이다. 그래서 `passed`와 무관하게 `ok`다.
        #
        # timeout된 wait(`error`)과 다른 이유: 거기서는 관측값이 끝내 생기지 않아 연산이
        # 목적을 이루지 못했고 계약도 그것을 `wait_failed`라는 error로 부른다. 반면
        # assert는 언제나 `actual`을 손에 넣는다 — 그 값이 기대와 다를 뿐이다.
        self._log_action(
            step_id=str(request.get("step_id") or record["id"]),
            action="assert",
            result="ok",
            elapsed_ms=elapsed,
        )
        return dict(record)

    # ── §B.2 capture ─────────────────────────────────────────────────────────
    def op_capture(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """`{handle|page_id, evidence_spec[]}` → `{artifacts:{name→path}, redacted, redaction_failed}`.

        [MUST] 파일을 직접 쓰지 않는다 — 호출자가 넘긴 `EvidenceWriter` 관문을 통과시킨다
        (§C.2, redaction 우회 금지). writer가 없으면 아무 것도 쓰지 않고 요청분을
        `unsupported`로 돌려준다. 쓰지 않은 것을 썼다고 보고하지 않는다.

        `evidence_spec`이 비면 **이 driver가 채울 수 있는 전부**를 뜻한다. orchestrator의
        browser 경로가 빈 목록으로 부르기 때문이고, 그때 아무 것도 안 남기면 browser 전용
        시나리오는 `actions.jsonl`이 비어 `evidence_complete`가 서지 않는다.

        [MUST] probe가 `available=false`로 확인한 capability는 수집하지 않는다 — 없는
        수단으로 만든 빈 증적을 남기면 결손이 판정에 도달하지 못한다(S-5).
        """
        writer = self._writer(request)
        specs = [str(item) for item in (request.get("evidence_spec") or [])]
        artifacts: Dict[str, str] = {}
        unsupported: List[str] = []

        if writer is None:
            return {
                "artifacts": {},
                "unsupported": specs,
                "redacted": False,
                "redaction_failed": False,
            }

        wanted = {e2e_evidence.canonical_kind(item) for item in specs}
        everything = not specs

        # §A.4 actions.jsonl — 공유 ActionLog를 관문으로 발행한다. browser 전용 run에서는
        # 이 driver가 유일한 발행자다(api executor가 선택되지 않기 때문).
        log = self.runtime_context.get("action_log")
        if log is not None and (everything or "action_log" in wanted):
            artifacts["action_log"] = log.flush(writer)
            if len(log) and "action_log" not in self._captured_kinds:
                self._captured_kinds.append("action_log")

        # §A.8 고정 매핑 — 이미 읽어 둔 snapshot을 남긴다.
        if everything or "snapshot" in wanted:
            for label, text in self._snapshots.items():
                artifacts[f"snapshot:{label}"] = writer.write_text(
                    SNAPSHOT_ARTIFACTS.get(label, f"browser/{label}.snapshot"),
                    text, kind="snapshot", observed=True,
                )

        # capability의 **유일한** 실행 지점이다(위 `_probe_capabilities` 주석 참조).
        # 이 한 번의 실행이 가용성 판정과 증적 수집을 동시에 한다 — 같은 연산을 두 번
        # 부르지 않으면서도 판정 근거는 실행 결과로 남는다(C-DRV-2, S-27 (d-1)).
        for key, artifact_path, args in (
            ("console", CONSOLE_ARTIFACT, ("console",)),
            ("errors", ERRORS_ARTIFACT, ("errors",)),
        ):
            if not (everything or key in wanted):
                continue
            completed = self._run(args)
            succeeded = completed is not None and completed.returncode == 0
            # 실행했으므로 probed=true다. 실패는 "미확인"이 아니라 "없음"으로 확정된다.
            self._capabilities[key] = {"available": succeeded, "route": "exec", "probed": True}
            if not succeeded:
                unsupported.append(key)
                continue
            artifacts[key] = writer.write_text(
                artifact_path, completed.stdout or "", kind=key, observed=True
            )
            if key not in self._captured_kinds:
                self._captured_kinds.append(key)

        # 명시적으로 요구됐지만 이 driver가 채울 수 없는 것은 조용히 넘기지 않는다.
        for spec in specs:
            kind = e2e_evidence.canonical_kind(spec)
            if kind not in artifacts and not any(name.startswith(f"{kind}:") for name in artifacts):
                if kind not in unsupported:
                    unsupported.append(spec)

        records = writer.redaction_records()
        return {
            "artifacts": artifacts,
            "unsupported": unsupported,
            "redacted": bool(records),
            "redaction_failed": any(item.get("redaction_failed") for item in records),
        }

    # ── 소유·관측 대장 ───────────────────────────────────────────────────────
    def assertion_results(self) -> List[Dict[str, Any]]:
        """실제 `assert` 연산이 만든 결과만 돌려준다. 비어 있음은 그 자체로 정보다."""
        return [dict(item) for item in self._assertion_results]

    def observed_evidence(self) -> List[str]:
        """증적 관문을 **실제로 통과해 기록된** 종류만 돌려준다.

        메모리에 모아 둔 사실은 증적이 아니다 — artifact로 남지 않은 것을 관측분으로 세면
        결손이 판정에 도달하지 못한다(S-5).
        """
        return list(self._captured_kinds)

    def owned_resources(self) -> Dict[str, List[str]]:
        """이 run이 소유한 자원 대장. `owned.json`의 `browser_pages` 기록 근거다."""
        return {
            "browser_pages": list(self._owned_pages),
            "profiles": list(self._owned_profiles),
        }


# ─── 레지스트리 등록 ─────────────────────────────────────────────────────────
def _factory(session_mode: str):
    def build(*, runtime_context: Optional[Mapping[str, Any]] = None, **_kwargs) -> AgentBrowserDriver:
        return AgentBrowserDriver(session_mode=session_mode, runtime_context=runtime_context)

    return build


def register() -> None:
    """후보 레지스트리에 두 세션 모드를 등록한다(C-DRV-3 후보 순서는 `drivers/__init__` 소유)."""
    for mode in (SESSION_MODE_ORCA_MANAGED, SESSION_MODE_STANDALONE):
        e2e_drivers.register_driver(DRIVER_NAME, mode, _factory(mode))


register()
