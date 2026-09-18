"""
@header {
  "module": "test_pilot_shared_contract",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "파일럿(opal-pilot-*) 추가·수정 시 공유 인프라(state-tool skill/STAGE_ENUM, opal-skills-registry.json)와의 계약 회귀를 판정하는 상시 가드. 일회성 태스크 검증이 아니라 앞으로 모든 신규 파일럿에 자동 적용되는 재사용 테스트다.",
  "exports": [
    "PilotDiscoveryTest", "RequiredFilesTest", "RegistryRegistrationTest",
    "PipelineSpecValidateTest", "EnumConsistencyTest", "MutualIsolationTest",
    "RegistryIntegrityTest", "FaultIsolationTest"
  ],
  "depends": ["state_tool"]
}

## 이 가드가 존재하는 이유 (OPAL 태스크 132 W-49)

opal-pilot-dev / opal-pilot-project-loop / opal-pilot-sdd / opal-pilot-project-build 등
파일럿 스킬끼리는 서로 독립이지만(상호 SKILL.md 참조 0건), 전부가 공유 인프라
(state-tool의 skill/STAGE_ENUM, opal-skills-registry.json)를 함께 소비한다. 그래서
사고는 파일럿 파일이 아니라 공유 인프라 쪽에서 난다 — 실제로 OPPB(oppb) 파일럿을
신설한 태스크 132에서도 state_tool.py의 skill enum(두 군데 중 한쪽만 갱신하면 CLI가
막힘), opal-skills-registry.json, STAGE_ENUM 갱신이 위험 지점이었다. 이 파일은 그
회귀를 다음 파일럿 추가 시에도 자동으로 잡기 위한 상시 가드다.

## 검사 7종의 근거

1. 필수 파일 — SKILL.md·references/pipeline.json이 없는 파일럿은 state-tool init
   --rows-from으로 파이프라인을 못 띄운다(런타임에 무음 실패).
2. 레지스트리 등재 — opal-skills-registry.json에 없으면 사용자가 트리거 문구로
   파일럿을 못 찾고, alias 충돌은 라우팅 오작동으로 이어진다.
3. 파이프라인 규격 — spec-validate 미통과 pipeline.json은 state-tool init 단계에서
   비로소 발견되는 지연 실패다. CI에서 조기 검출한다.
4. enum 정합 — state_tool.py의 skill 목록은 argparse `--skill` choices와
   validate_pipeline_spec() 내부 지역 skill_enum 두 군데에 물리적으로 중복 존재한다
   (SSOT 아님). 과거 실제로 한쪽만 갱신해 파이프라인이 막힌 사고가 있었다(132 실측).
   STAGE_ENUM 쪽도 동일한 이유로 각 pipeline.json의 stage 값과 대조한다.
5. 상호 격리 — [설계 결정, 아래 "허용목록 설계" 절 참조] 파일럿이 서로의 내부를
   말없이 파고들기 시작하면 독립 배포·독립 검증이 무너진다.
6. 레지스트리 무결성 — JSON 문법 오류나 alias 중복은 로더가 전체 그룹을 못 읽거나
   잘못된 파일럿으로 라우팅하게 만든다.
7. 결함 격리 — 파일럿 1종의 스펙이 깨졌을 때 나머지 파일럿까지 연쇄로 막히면
   "공유 인프라"라는 설계 자체가 위험 증폭기가 된다. 이 성질을 실제로 깨뜨려 확인한다.

## 허용목록 설계 (검사 5) — 왜 "무조건 0건"이 아닌가

배경 설명의 "4종 SKILL.md 상호 참조 0건"은 그 4종(opal-pilot-dev/project-loop/sdd/
project-build) *서로 사이의* 참조가 0건이라는 관측이다. 이 파일은 절대 요건에 따라
opal/skills/opal-pilot-* 전체(집필 시점 11종)를 스캔 대상으로 삼는데, 전체 스캔에서는
상위 오케스트레이터가 사용자에게 하위 전문 파일럿으로 라우팅을 안내하는 정상적인 프로즈
참조가 다수 존재한다(예: opal-pilot-project가 코드 작업은 opal-pilot-dev-short를
쓰라고 안내, opal-pilot-dev-short가 자신을 "canonical Dev Pilot(opal-pilot-dev)이
소유하는 라우팅 스텁"이라고 명시). 이들은 결함이 아니라 문서화된 설계다.

따라서 "파일럿은 서로를 참조하지 않는다"를 전체 11종에 그대로 적용하면 오늘도
6/11이 즉시 실패한다(이 파일 작성 중 실측) — 이는 테스트 설계가 틀린 경우이지 실제
결함이 아니다. 대신 이 가드는 "문서화되지 않은 새 참조가 생기면 실패"로 설계했다 —
CROSS_REFERENCE_ALLOWLIST가 현재 관측된 참조 전체를 근거와 함께 명시하고, 목록에
없는 새 참조가 나타나면 실패한다(회귀 가드 본연의 목적: 다음에 파일럿을 추가·수정하는
사람이 의도치 않게 다른 파일럿과 얽히면 이 테스트가 잡고, 의도한 참조라면
CROSS_REFERENCE_ALLOWLIST에 근거와 함께 추가하면 된다). 허용목록 항목 자체가
여전히 유효한 파일럿 쌍을 가리키는지도 별도로 검증해 방치된 허용목록 항목을 막는다.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# 경로 상수
# ─────────────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[4]
SKILLS_DIR = REPO_ROOT / "opal" / "skills"
STATE_TOOL_PATH = REPO_ROOT / "opal" / "tools" / "state-tool" / "state_tool.py"
REGISTRY_PATH = REPO_ROOT / "opal" / "core" / "references" / "opal-skills-registry.json"

# state_tool.py를 직접 import — 기존 관례(test_state_tool.py)와 동일하게
# PYTHONPATH를 조정해 sibling 모듈로 적재한다. STAGE_ENUM(top-level 상수)과
# build_parser()/validate_pipeline_spec()(공개 함수) 접근에 사용한다.
_TOOL_DIR = Path(__file__).resolve().parent.parent
if str(_TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOL_DIR))
import state_tool as ST  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# 절대 요건 — 파일럿 목록은 스캔으로만 얻는다 (하드코딩 금지)
# ─────────────────────────────────────────────────────────────────────────────

def discover_pilots() -> dict[str, Path]:
    """opal/skills/opal-pilot-* 디렉토리를 스캔해 발견되는 전부를 반환한다.

    이름·개수를 하드코딩하지 않는다 — 신규 파일럿이 추가되면 이 함수가 다음 실행에서
    자동으로 포함한다(W-49 절대 요건). 반환값은 이름순 정렬된 {디렉토리명: Path}.
    """
    return {
        p.name: p
        for p in sorted(SKILLS_DIR.glob("opal-pilot-*"), key=lambda x: x.name)
        if p.is_dir()
    }


PILOTS: dict[str, Path] = discover_pilots()


# ─────────────────────────────────────────────────────────────────────────────
# 검사 1 예외 — pipeline.json을 독자적으로 갖지 않는 파일럿
# ─────────────────────────────────────────────────────────────────────────────
# 조용히 건너뛰지 않고 근거와 함께 명시 기록한다(W-49 지시).

PIPELINE_JSON_EXEMPT: dict[str, str] = {
    "opal-pilot-dev-short": (
        "opal-skills-registry.json의 opal-pilot-dev-short 항목 paths가 "
        "opal-pilot-dev/SKILL.md를 직접 가리키고(자신의 SKILL.md 아님), "
        "opal-pilot-dev-short/SKILL.md 서두가 'opds short profile은 canonical "
        "Dev Pilot(opal-pilot-dev)이 소유하므로 opds 요청은 이 스킬이 아니라 "
        "opal-pilot-dev로 라우팅한다'고 명시한다 — 독자 실행 파이프라인이 없는 "
        "라우팅 스텁이며 pipeline.json은 opal-pilot-dev가 소유한다."
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# 검사 5 허용목록 — 문서화된 파일럿 간 참조 (위 모듈 docstring "허용목록 설계" 참조)
# ─────────────────────────────────────────────────────────────────────────────

CROSS_REFERENCE_ALLOWLIST: dict[tuple[str, str], str] = {
    ("opal-pilot-data-design", "opal-pilot-write-tech"):
        "opal-pilot-data-design SKILL.md가 opal-pilot-write-tech Q6 분기 패턴을 "
        "계승한다고 명시 — 기획 산출물 3분기 자동 감지 로직 공유 문서화.",
    ("opal-pilot-dev", "opal-pilot-write-tech"):
        "opal-pilot-dev가 기획 문서 세트 작업은 opal-pilot-write-tech를 쓰라고 "
        "사용자에게 라우팅 안내.",
    ("opal-pilot-dev-short", "opal-pilot-dev"):
        "opal-pilot-dev-short 자신이 opal-pilot-dev 소유 라우팅 스텁임을 명시 "
        "(PIPELINE_JSON_EXEMPT 근거와 동일 관계).",
    ("opal-pilot-dev-short", "opal-pilot-write-tech"):
        "opal-pilot-dev-short가 기획 문서 세트 작업은 opal-pilot-write-tech를 "
        "쓰라고 사용자에게 라우팅 안내.",
    ("opal-pilot-dev-wireframe", "opal-pilot-dev"):
        "opal-pilot-dev-wireframe이 기존 프로젝트 기반 UI 작업은 opal-pilot-dev "
        "(또는 opal-pilot-dev-short)에서 수행하라고 라우팅 안내.",
    ("opal-pilot-gc", "opal-pilot-dev-short"):
        "opal-pilot-gc(진단 전담)가 auto_fixable 이슈 발견 시 수정 반영을 "
        "opal-pilot-dev-short로 체인하도록 명시.",
    ("opal-pilot-project", "opal-pilot-dev-short"):
        "opal-pilot-project(범용 오케스트레이터)가 코드 개발 태스크는 "
        "opal-pilot-dev-short를 쓰라고 라우팅 안내.",
    ("opal-pilot-project", "opal-pilot-write-tech"):
        "opal-pilot-project가 기획 산출물 세트는 opal-pilot-write-tech를 쓰라고 "
        "라우팅 안내.",
    ("opal-pilot-project-dev", "opal-pilot-dev"):
        "opal-pilot-project-dev(상위 프로젝트 오케스트레이터)의 스킬 탐색 경로 "
        "목록이 하위 실행 파일럿 opal-pilot-dev를 열거.",
    ("opal-pilot-project-dev", "opal-pilot-dev-short"):
        "opal-pilot-project-dev의 스킬 탐색 경로 목록이 하위 실행 파일럿 "
        "opal-pilot-dev-short를 열거.",
    ("opal-pilot-project-dev", "opal-pilot-dev-wireframe"):
        "opal-pilot-project-dev의 스킬 탐색 경로 목록이 하위 실행 파일럿 "
        "opal-pilot-dev-wireframe을 열거.",
    ("opal-pilot-project-dev", "opal-pilot-write-tech"):
        "opal-pilot-project-dev의 스킬 탐색 경로 목록이 하위 실행 파일럿 "
        "opal-pilot-write-tech를 열거.",
}


# ─────────────────────────────────────────────────────────────────────────────
# 공용 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def _load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def _registry_pilot_entries() -> list[dict]:
    return _load_registry()["groups"]["opal-pilot"]


def _pipeline_json_path(pilot_dir: Path) -> Path:
    return pilot_dir / "references" / "pipeline.json"


def _has_own_pipeline_json(name: str) -> bool:
    return name not in PIPELINE_JSON_EXEMPT


def _run_spec_validate(path: Path) -> tuple[int, dict | None, str, str]:
    """state-tool spec-validate <path> 공개 CLI 실호출 (내부 API import 금지, 검사 3 요건)."""
    completed = subprocess.run(
        [sys.executable, str(STATE_TOOL_PATH), "spec-validate", str(path)],
        capture_output=True, text=True, check=False,
    )
    try:
        data = json.loads(completed.stdout)
    except json.JSONDecodeError:
        data = None
    return completed.returncode, data, completed.stdout, completed.stderr


_MENTION_CACHE: dict[str, str] = {}


def _skill_md_text(pilot_dir: Path) -> str:
    key = str(pilot_dir)
    if key not in _MENTION_CACHE:
        _MENTION_CACHE[key] = (pilot_dir / "SKILL.md").read_text(encoding="utf-8")
    return _MENTION_CACHE[key]


def _mentions(text: str, name: str) -> bool:
    """text가 파일럿명 name을 온전한 토큰으로 언급하는지 판정.

    단순 `name in text`는 오탐한다 — 예: "opal-pilot-project"는
    "opal-pilot-project-build"의 접두 부분 문자열이라 서로 다른 파일럿인데도
    포함 관계가 성립해버린다. 하이픈을 단어 구성 문자로 취급하는 경계 검사로
    이 오탐을 막는다.
    """
    pattern = re.compile(r"(?<![\w-])" + re.escape(name) + r"(?![\w-])")
    return bool(pattern.search(text))


# 파이프라인 규격을 갖는 파일럿(검사 1 예외 제외) — 여러 테스트가 공유하는 파생 목록.
PILOTS_WITH_PIPELINE = {
    name: path for name, path in PILOTS.items() if _has_own_pipeline_json(name)
}


# ═════════════════════════════════════════════════════════════════════════════
# 0. PilotDiscoveryTest — 스캔 메커니즘 자체의 건전성
# ═════════════════════════════════════════════════════════════════════════════

class PilotDiscoveryTest(unittest.TestCase):
    """discover_pilots()가 실제로 디렉토리 스캔으로 목록을 얻는지 확인한다.

    개수를 단언하지 않는다(W-49 지시 — 파일럿 추가 시 개수 단언은 무의미하게 깨진다).
    """

    def test_scan_finds_directories_matching_glob_pattern(self):
        expected = {
            p.name for p in SKILLS_DIR.iterdir()
            if p.is_dir() and p.name.startswith("opal-pilot-")
        }
        self.assertEqual(
            set(PILOTS.keys()), expected,
            "discover_pilots()의 스캔 결과가 opal/skills 디렉토리 실제 내용과 다르다 — "
            "글롭 패턴이나 필터 조건이 어긋났을 수 있다.",
        )

    def test_scan_result_is_nonempty(self):
        self.assertTrue(PILOTS, "opal/skills에서 opal-pilot-* 디렉토리를 하나도 찾지 못했다 — "
                                 "SKILLS_DIR 경로 계산이 어긋났을 가능성이 크다.")

    def test_scan_does_not_hardcode_names(self):
        """discover_pilots()의 반환값이 이 모듈 소스 안의 어떤 리터럴 목록과도 동일한
        객체가 아니라 실제 파일시스템 조회 결과임을 확인 — 글롭 조회를 우회해 상수
        리스트를 반환하도록 되돌리는 회귀를 잡는다."""
        rescanned = discover_pilots()
        self.assertEqual(rescanned, PILOTS)
        self.assertIsNot(
            rescanned, PILOTS,
            "매 호출이 새 dict를 반환해야 한다 — 캐시된 하드코딩 상수를 그대로 리턴하면 안 된다.",
        )


# ═════════════════════════════════════════════════════════════════════════════
# 1. RequiredFilesTest — SKILL.md · references/pipeline.json 존재
# ═════════════════════════════════════════════════════════════════════════════

class RequiredFilesTest(unittest.TestCase):
    def test_skill_md_exists_for_every_discovered_pilot(self):
        for name, path in PILOTS.items():
            with self.subTest(pilot=name):
                skill_md = path / "SKILL.md"
                self.assertTrue(
                    skill_md.exists(),
                    f"{name}: SKILL.md 없음 (경로: {skill_md}) — 모든 파일럿은 SKILL.md를 가져야 한다.",
                )

    def test_pipeline_json_exists_or_is_documented_exempt(self):
        for name, path in PILOTS.items():
            with self.subTest(pilot=name):
                pipeline_json = _pipeline_json_path(path)
                if name in PIPELINE_JSON_EXEMPT:
                    self.assertFalse(
                        pipeline_json.exists(),
                        f"{name}: PIPELINE_JSON_EXEMPT에 등재돼 있지만 실제로는 "
                        f"references/pipeline.json이 존재한다 — 예외 목록이 낡았다. "
                        f"이 파일럿을 PIPELINE_JSON_EXEMPT에서 제거하라.",
                    )
                    continue
                self.assertTrue(
                    pipeline_json.exists(),
                    f"{name}: references/pipeline.json 없음 (경로: {pipeline_json}) — "
                    f"신규 파일럿이면 pipeline.json을 추가하거나, 의도된 예외(예: 다른 "
                    f"파일럿의 라우팅 스텁)라면 PIPELINE_JSON_EXEMPT에 근거와 함께 등록하라.",
                )

    def test_pipeline_json_exempt_entries_are_still_discovered_pilots(self):
        """PIPELINE_JSON_EXEMPT에 등재된 이름이 실제로 스캔되는 파일럿인지 확인 —
        디렉토리가 삭제·개명됐는데 예외 목록만 남는 방치를 막는다."""
        for name in PIPELINE_JSON_EXEMPT:
            self.assertIn(
                name, PILOTS,
                f"PIPELINE_JSON_EXEMPT에 등재된 '{name}'이 opal/skills에 더 이상 존재하지 "
                f"않는다 — 방치된 예외 항목이니 제거하라.",
            )


# ═════════════════════════════════════════════════════════════════════════════
# 2. RegistryRegistrationTest — opal-skills-registry.json 등재 + alias 유일성
# ═════════════════════════════════════════════════════════════════════════════

class RegistryRegistrationTest(unittest.TestCase):
    def setUp(self):
        self.entries = _registry_pilot_entries()
        self.entry_by_name = {e.get("name"): e for e in self.entries}

    def test_every_discovered_pilot_is_registered(self):
        for name in PILOTS:
            with self.subTest(pilot=name):
                self.assertIn(
                    name, self.entry_by_name,
                    f"{name}: opal-skills-registry.json의 opal-pilot 그룹에 등재되지 "
                    f"않았다 — 사용자가 트리거 문구로 이 파일럿을 찾을 수 없다. "
                    f"registry에 {{name, alias, description, triggers, paths, domain, "
                    f"pipeline}} 항목을 추가하라.",
                )

    def test_pilot_aliases_are_pairwise_unique(self):
        aliases = [e.get("alias") for e in self.entries]
        seen: dict[str, str] = {}
        dupes: list[str] = []
        for entry in self.entries:
            alias = entry.get("alias")
            name = entry.get("name")
            if alias in seen and seen[alias] != name:
                dupes.append(f"alias '{alias}' used by both '{seen[alias]}' and '{name}'")
            else:
                seen[alias] = name
        self.assertEqual(
            len(aliases), len(set(aliases)),
            f"opal-pilot 그룹 alias가 중복된다 — 충돌 목록: {dupes or aliases}",
        )

    def test_pipeline_json_skill_field_matches_registry_alias(self):
        """pipeline.json의 최상위 skill 값과 registry alias가 어긋나면, 실행되는 CLI
        스킬(alias)과 spec-validate가 검증하는 skill 값이 서로 다른 파일럿을 가리키게
        된다 — 조용한 불일치를 잡는다."""
        for name, path in PILOTS_WITH_PIPELINE.items():
            with self.subTest(pilot=name):
                entry = self.entry_by_name.get(name)
                if entry is None:
                    continue  # 위 test_every_discovered_pilot_is_registered가 이미 보고
                spec = json.loads(_pipeline_json_path(path).read_text(encoding="utf-8"))
                self.assertEqual(
                    spec.get("skill"), entry.get("alias"),
                    f"{name}: pipeline.json skill='{spec.get('skill')}' != "
                    f"registry alias='{entry.get('alias')}' — 둘 중 하나가 최신화 "
                    f"누락됐다.",
                )


# ═════════════════════════════════════════════════════════════════════════════
# 3. PipelineSpecValidateTest — 공개 CLI `state-tool spec-validate` 통과
# ═════════════════════════════════════════════════════════════════════════════

class PipelineSpecValidateTest(unittest.TestCase):
    """공개 CLI만 사용한다(내부 API import 금지, W-49 검사 3 요건)."""

    def test_every_pilot_pipeline_json_passes_spec_validate_cli(self):
        for name, path in PILOTS_WITH_PIPELINE.items():
            with self.subTest(pilot=name):
                spec_path = _pipeline_json_path(path)
                code, data, stdout, stderr = _run_spec_validate(spec_path)
                self.assertEqual(
                    code, 0,
                    f"{name}: state-tool spec-validate가 exit {code}로 실패 "
                    f"(경로: {spec_path})\nstdout={stdout!r}\nstderr={stderr!r}",
                )
                self.assertIsNotNone(data, f"{name}: spec-validate stdout이 JSON이 아니다: {stdout!r}")
                self.assertTrue(
                    data.get("ok"),
                    f"{name}: spec-validate ok=false — violations={data.get('violations')}",
                )
                self.assertEqual(
                    data.get("violations_count"), 0,
                    f"{name}: violations_count != 0 — {data.get('violations')}",
                )


# ═════════════════════════════════════════════════════════════════════════════
# 4. EnumConsistencyTest — skill enum(2군데) · STAGE_ENUM 정합
# ═════════════════════════════════════════════════════════════════════════════

def _argparse_init_skill_choices() -> set[str]:
    """state_tool.py argparse `init --skill` choices를 build_parser()로 직접 조회한다
    (공개 함수 호출 — regex 파싱보다 견고함)."""
    parser = ST.build_parser()
    command_action = next(a for a in parser._actions if a.dest == "command")
    init_parser = command_action.choices["init"]
    skill_action = next(a for a in init_parser._actions if a.dest == "skill")
    return set(skill_action.choices)


_LOCAL_SKILL_ENUM_RE = re.compile(r"skill_enum\s*=\s*\[([^\]]*)\]")


def _local_skill_enum_in_validate_pipeline_spec() -> set[str]:
    """validate_pipeline_spec() 내부 지역 skill_enum 리터럴을 소스에서 추출한다.

    이 값은 함수 지역 변수라 import만으로는 얻을 수 없다 — argparse choices와
    물리적으로 분리된 두 번째 SSOT-아닌 목록임을 그대로 드러내기 위해 소스 리터럴을
    직접 읽는다(과거 실제로 이 두 목록 중 하나만 갱신돼 파이프라인이 막힌 사고가 있었다).
    """
    source = STATE_TOOL_PATH.read_text(encoding="utf-8")
    match = _LOCAL_SKILL_ENUM_RE.search(source)
    if not match:
        raise AssertionError(
            "state_tool.py의 validate_pipeline_spec() 내부에서 'skill_enum = [...]' "
            "리터럴을 찾지 못했다 — 소스 구조가 바뀌었다. 이 정규식(_LOCAL_SKILL_ENUM_RE, "
            "opal/tools/state-tool/tests/test_pilot_shared_contract.py)을 새 형태에 맞게 갱신하라."
        )
    return set(json.loads("[" + match.group(1) + "]"))


class EnumConsistencyTest(unittest.TestCase):
    """state_tool.py의 skill 목록은 argparse `--skill` choices와
    validate_pipeline_spec() 내부 지역 skill_enum 두 군데에 물리적으로 중복 존재한다
    (SSOT 아님) — 양쪽 모두 검사한다(W-49 명시 요건)."""

    @classmethod
    def setUpClass(cls):
        cls.argparse_choices = _argparse_init_skill_choices()
        cls.local_skill_enum = _local_skill_enum_in_validate_pipeline_spec()
        cls.registry_aliases = {
            e.get("name"): e.get("alias") for e in _registry_pilot_entries()
        }

    def test_argparse_and_local_skill_enum_are_identical_sets(self):
        """두 목록이 서로 다르면 '한쪽만 갱신' 사고가 재발한 것이다 — 어느 쪽에
        무엇이 빠졌는지 정확히 보고한다."""
        only_in_argparse = self.argparse_choices - self.local_skill_enum
        only_in_local = self.local_skill_enum - self.argparse_choices
        self.assertEqual(
            self.argparse_choices, self.local_skill_enum,
            "state_tool.py의 두 skill 목록이 서로 다르다 — "
            f"argparse에만 있음: {sorted(only_in_argparse) or '없음'}, "
            f"validate_pipeline_spec() 지역 skill_enum에만 있음: {sorted(only_in_local) or '없음'}. "
            "두 위치(1. init 서브파서 --skill choices, 2. validate_pipeline_spec() 내부 "
            "skill_enum 리터럴) 모두 동일하게 갱신하라.",
        )

    def test_every_registered_pilot_alias_is_in_both_skill_enums(self):
        for name, alias in self.registry_aliases.items():
            with self.subTest(pilot=name, alias=alias):
                self.assertIn(
                    alias, self.argparse_choices,
                    f"{name}: registry alias '{alias}'가 state_tool.py argparse "
                    f"`init --skill` choices에 없다 — state-tool init --skill {alias}가 "
                    f"거부된다(exit 2). state_tool.py p_init.add_argument('--skill', ...) "
                    f"choices에 '{alias}'를 추가하라.",
                )
                self.assertIn(
                    alias, self.local_skill_enum,
                    f"{name}: registry alias '{alias}'가 validate_pipeline_spec() 내부 "
                    f"skill_enum에 없다 — pipeline.json skill='{alias}'가 spec_skill_invalid로 "
                    f"거부된다. state_tool.py validate_pipeline_spec() 내부 skill_enum 리스트에 "
                    f"'{alias}'를 추가하라.",
                )

    def test_every_pilot_pipeline_json_stage_values_are_in_stage_enum(self):
        for name, path in PILOTS_WITH_PIPELINE.items():
            spec = json.loads(_pipeline_json_path(path).read_text(encoding="utf-8"))
            stages = spec.get("meta", {}).get("stages", [])
            self.assertTrue(stages, f"{name}: pipeline.json meta.stages가 비어 있다.")
            for stage in stages:
                with self.subTest(pilot=name, stage=stage):
                    self.assertIn(
                        stage, ST.STAGE_ENUM,
                        f"{name}: pipeline.json meta.stages의 '{stage}'가 state_tool.py "
                        f"STAGE_ENUM에 없다 — 이 stage를 쓰는 task_steps 행이 add-row/init "
                        f"단계에서 invalid_stage_enum으로 거부된다. STAGE_ENUM 리스트에 "
                        f"'{stage}'를 추가하라(additive-only).",
                    )
            # task_steps[].stage도 meta.stages 부분집합이어야 하지만 그 정합은
            # validate_pipeline_spec()의 기존 책임(spec_stage_invalid)이라 여기서는
            # meta.stages 자체의 STAGE_ENUM 소속만 이 테스트의 책임으로 검사한다.


# ═════════════════════════════════════════════════════════════════════════════
# 5. MutualIsolationTest — SKILL.md 상호참조 (허용목록 기반, 위 docstring 참조)
# ═════════════════════════════════════════════════════════════════════════════

class MutualIsolationTest(unittest.TestCase):
    def test_no_undocumented_cross_pilot_reference_in_skill_md(self):
        undocumented: list[str] = []
        for name, path in PILOTS.items():
            text = _skill_md_text(path)
            for other_name in PILOTS:
                if other_name == name:
                    continue
                if _mentions(text, other_name) and (name, other_name) not in CROSS_REFERENCE_ALLOWLIST:
                    undocumented.append(f"{name} -> {other_name}")
        self.assertEqual(
            undocumented, [],
            "문서화되지 않은 파일럿 간 SKILL.md 참조가 발견됐다: "
            f"{undocumented}. 의도한 라우팅/위임이면 CROSS_REFERENCE_ALLOWLIST에 근거와 "
            "함께 추가하고, 의도치 않은 결합이면 SKILL.md에서 해당 참조를 제거하라.",
        )

    def test_allowlist_entries_reference_currently_discovered_pilots(self):
        """CROSS_REFERENCE_ALLOWLIST 항목이 가리키는 두 이름 모두 실제로 스캔되는
        파일럿인지 확인 — 파일럿이 삭제·개명됐는데 허용목록만 남는 방치를 막는다."""
        for (src, dst) in CROSS_REFERENCE_ALLOWLIST:
            with self.subTest(pair=(src, dst)):
                self.assertIn(src, PILOTS, f"허용목록의 '{src}'가 더 이상 존재하지 않는 파일럿이다.")
                self.assertIn(dst, PILOTS, f"허용목록의 '{dst}'가 더 이상 존재하지 않는 파일럿이다.")

    def test_allowlist_entries_still_actually_mentioned(self):
        """허용목록 항목이 실제로는 더 이상 참조되지 않는데 방치돼 있으면, 다음에 그
        참조가 부활해도(예: 되돌림 커밋) 이 가드가 못 잡는 사각지대가 생긴다."""
        stale: list[str] = []
        for (src, dst) in CROSS_REFERENCE_ALLOWLIST:
            if src not in PILOTS:
                continue  # 위 테스트가 이미 보고
            text = _skill_md_text(PILOTS[src])
            if not _mentions(text, dst):
                stale.append(f"{src} -> {dst}")
        self.assertEqual(
            stale, [],
            f"CROSS_REFERENCE_ALLOWLIST 항목 중 실제 SKILL.md에서 더 이상 참조되지 "
            f"않는 항목: {stale}. 허용목록에서 제거하라(방치된 허용목록은 향후 다른 "
            f"방향의 실수 참조를 가려버릴 수 있다).",
        )


# ═════════════════════════════════════════════════════════════════════════════
# 6. RegistryIntegrityTest — JSON 문법 + alias 중복 0 + 필수 필드 보유
# ═════════════════════════════════════════════════════════════════════════════
# 기준선(baseline) 설계 메모:
# 원 요구는 "alias 집합에서 아무도 사라지지 않았는가"를 git 기준판과 대조하라는 것이었다.
# 이 저장소에는 CI 워크플로 정의가 없고(.github/workflows 등 부재 확인), main/HEAD~N
# 참조가 CI 체크아웃 방식(얕은 클론·단일 브랜치 클론)에 따라 항상 존재한다는 보장이
# 없다 — git ref 가용성에 의존하는 검사는 "시간이 지나도 안 깨지는 방식"이라는 요건과
# 충돌한다. W-49 지시가 명시적으로 허용한 폴백에 따라, 이 검사는 "현재 판 내부
# 일관성"(alias 중복 0건 + 모든 항목이 필수 필드 보유)으로 축소한다.

REQUIRED_REGISTRY_FIELDS = ("name", "alias", "description", "triggers", "paths", "domain", "pipeline")


class RegistryIntegrityTest(unittest.TestCase):
    def test_registry_file_is_valid_json(self):
        try:
            json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            self.fail(f"opal-skills-registry.json이 유효한 JSON이 아니다: {exc}")

    def test_pilot_group_has_zero_duplicate_aliases(self):
        entries = _registry_pilot_entries()
        aliases = [e.get("alias") for e in entries]
        self.assertEqual(
            len(aliases), len(set(aliases)),
            f"opal-pilot 그룹 alias 중복 발견 — 전체 목록: {aliases}",
        )

    def test_every_pilot_entry_has_required_fields(self):
        for entry in _registry_pilot_entries():
            name = entry.get("name", "<name 없음>")
            with self.subTest(pilot=name):
                missing = [f for f in REQUIRED_REGISTRY_FIELDS if f not in entry]
                self.assertEqual(
                    missing, [],
                    f"{name}: registry 항목에 필수 필드 누락 — {missing} "
                    f"(필수 필드: {REQUIRED_REGISTRY_FIELDS})",
                )


# ═════════════════════════════════════════════════════════════════════════════
# 7. FaultIsolationTest — 파일럿 1종 손상이 나머지에 전파되지 않는가
# ═════════════════════════════════════════════════════════════════════════════

class FaultIsolationTest(unittest.TestCase):
    """원본 파일은 절대 수정하지 않는다 — 손상시킬 파일럿의 pipeline.json만 임시
    디렉토리로 복사한 뒤 그 복사본을 깨뜨리고, 나머지 파일럿은 저장소 원본 경로를
    그대로(읽기만) spec-validate한다."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp(prefix="w49-fault-isolation-"))

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_corrupting_one_pilot_copy_does_not_affect_others(self):
        pilots_with_pipeline = sorted(PILOTS_WITH_PIPELINE)
        if len(pilots_with_pipeline) < 2:
            self.skipTest(
                "pipeline.json을 가진 파일럿이 2종 미만이라 결함 격리를 검증할 수 없다 "
                "(신규 파일럿 추가로 재활성화될 수 있는 의도된 사전조건 skip)."
            )

        # 이름순 정렬 첫 파일럿을 손상 대상으로 선택 — 특정 파일럿명을 하드코딩하지
        # 않기 위해 스캔 결과에서 결정론적으로 고른다.
        victim_name = pilots_with_pipeline[0]
        victim_original = _pipeline_json_path(PILOTS_WITH_PIPELINE[victim_name])
        corrupted_copy = self.tmpdir / "corrupted-pipeline.json"
        corrupted_copy.write_text("{ this is not valid json", encoding="utf-8")

        # 원본은 절대 건드리지 않았음을 명시적으로 재확인한다.
        original_bytes_before = victim_original.read_bytes()

        code, data, stdout, stderr = _run_spec_validate(corrupted_copy)
        self.assertEqual(
            code, 1,
            f"{victim_name} 손상 복사본은 exit 1이어야 한다 (실제: {code})\n{stdout!r}",
        )
        self.assertIsNotNone(data, f"손상 복사본 spec-validate stdout이 JSON이 아니다: {stdout!r}")
        self.assertFalse(data.get("ok"), f"손상 복사본인데 ok=true: {data}")
        self.assertEqual(
            data.get("error"), "spec_invalid_json",
            f"손상 복사본의 에러 코드가 spec_invalid_json이 아니다: {data}",
        )

        self.assertEqual(
            victim_original.read_bytes(), original_bytes_before,
            f"{victim_name}의 실제 원본 pipeline.json이 이 테스트 도중 변경됐다 — "
            f"원본 파일 절대 수정 금지 위반.",
        )

        for other_name in pilots_with_pipeline:
            if other_name == victim_name:
                continue
            with self.subTest(pilot=other_name):
                other_path = _pipeline_json_path(PILOTS_WITH_PIPELINE[other_name])
                o_code, o_data, o_stdout, o_stderr = _run_spec_validate(other_path)
                self.assertEqual(
                    o_code, 0,
                    f"{victim_name} 손상과 무관하게 {other_name}은 spec-validate ok여야 "
                    f"하는데 exit {o_code}로 실패했다 — 파일럿 간 격리가 깨졌다.\n"
                    f"{o_stdout!r}",
                )
                self.assertTrue(
                    o_data and o_data.get("ok"),
                    f"{victim_name} 손상과 무관하게 {other_name}은 ok=true여야 하는데 "
                    f"{o_data}였다 — 파일럿 간 격리가 깨졌다.",
                )


if __name__ == "__main__":
    unittest.main()
