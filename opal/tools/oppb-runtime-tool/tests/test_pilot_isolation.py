"""
@header {
  "module": "test_pilot_isolation",
  "layer": "test",
  "domain": "oppb-runtime",
  "description": "OPAL 태스크 132 W-35 — OPPB 도입 전후로 기존 파일럿(opal-pilot-dev/opal-pilot-project-loop/opal-pilot-sdd)과 공유 인프라가 '태스크 132가 무엇을 바꿨는가' 귀속 축에서 무변경임을 기계 단언하고, OPPB 런타임 결함이 공유 CLI(state-tool)의 기존 경로로 전파되지 않는 복구 계약을 실증한다. AC-18·AC-19·C-2 대상. opal/tools/state-tool/tests/test_pilot_shared_contract.py(W-49)의 상시 가드(레지스트리 alias 중복·필수 필드, spec-validate, enum 정합, 결함 격리 — 11종 파일럿 전체 스캔 기반)와는 검사 축이 다르다: W-49는 '지금 이 순간 공유 인프라 계약이 성립하는가'를 매번 재검증하는 회귀 가드이고, 이 파일은 'baseline(6ae6125, 태스크 132 W-3 변경 직전 마지막 커밋) 대비 태스크 132가 기존 3종 파일럿·공유 인프라를 실제로 건드렸는가'를 git 이력으로 귀속하는 1회성 검증이다. baseline은 처음 81d890d(132 W-3 변경이 태그 없이 이미 섞여 들어간 커밋)로 잡았다가 이 파일 작성 중 발견해 그 부모로 정정했다(아래 BASELINE_COMMIT 주석 참조). git 없이는 귀속을 볼 수 없으므로 git·기준 커밋 불가용 시 조용히 통과하지 않고 pytest.skip으로 명시한다. mock 금지 — 실제 git 이력·실제 파일만 사용한다.",
  "exports": [
    "AttributionTest", "RegistryAgentRemovalTest", "SharedInfraAdditiveTest",
    "RecoveryContractTest"
  ],
  "depends": ["opal/tools/state-tool/state_tool.py", "opal/core/references/opal-skills-registry.json"]
}

## W-49와의 역할 분담 (중복 금지 — 디스패치 지시 그대로 기록)

W-49(`test_pilot_shared_contract.py`)가 이미 다음을 상시 가드로 커버한다 — 이 파일은
아래 항목을 복제하지 않는다:

- 레지스트리 alias 쌍별 유일성, 필수 필드 보유(RegistryIntegrityTest)
- `state-tool spec-validate` CLI로 각 파일럿 pipeline.json 통과 여부(PipelineSpecValidateTest)
- state_tool.py의 skill enum 2군데(argparse choices / validate_pipeline_spec 지역
  skill_enum) 상호 정합, STAGE_ENUM과 각 pipeline.json stage 값 정합(EnumConsistencyTest)
- pipeline.json 1건을 손상시켜 다른 파일럿의 spec-validate가 영향받지 않는지
  (FaultIsolationTest — "결함 격리", 스펙 데이터 손상 축)

이 파일이 보는 축(W-35 전용, 디스패치 지시 원문):

1. **변경 귀속** — 기존 3종 파일럿(opd/oppl/opsdd) 파일을 baseline 이후 어떤 태스크가
   건드렸는지, 그중 태스크 132 소유 커밋이 0건인지(AttributionTest).
2. **항목 제거 0건** — 레지스트리·agents.md 항목 집합이 baseline의 상위집합인지
   (RegistryAgentRemovalTest).
3. **공유 인프라 5접점의 additive 성질** — 기존 내용이 지워지지 않았는지
   (SharedInfraAdditiveTest).
4. **복구 계약** — OPPB *런타임 코드*가 깨졌을 때 공유 CLI의 OPPD 경로가 영향받지
   않는지, 그 구조적 근거인 "OPPB 모듈을 import하는 외부 코드 0건"(RecoveryContractTest).
   W-49의 FaultIsolationTest는 "pipeline.json *스펙 데이터*가 깨졌을 때" 축이라 겹치지
   않는다 — 대상 결함의 종류(런타임 코드 vs 스펙 데이터)가 다르다.
"""

from __future__ import annotations

import ast
import json
import os
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
STATE_TOOL_PATH = REPO_ROOT / "opal" / "tools" / "state-tool" / "state_tool.py"
REGISTRY_PATH = REPO_ROOT / "opal" / "core" / "references" / "opal-skills-registry.json"
AGENTS_MD_PATH = REPO_ROOT / "opal" / "core" / "references" / "agents.md"
ACTOR_MD_PATH = REPO_ROOT / "opal" / "core" / "references" / "harness" / "actor.md"
EVALUATOR_AGENT_MD_PATH = REPO_ROOT / "opal" / "agents" / "opal-evaluator-agent" / "AGENT.md"
SCENARIO_GATE_SKILL_MD_PATH = REPO_ROOT / "opal" / "skills" / "op-scenario-gate" / "SKILL.md"
OPPB_TOOL_DIR = REPO_ROOT / "opal" / "tools" / "oppb-runtime-tool"

# git-relative(POSIX, 슬래시) 경로 — git show/log는 OS 경로 구분자가 아니라 이 형식을 요구한다.
REGISTRY_REL = "opal/core/references/opal-skills-registry.json"
AGENTS_MD_REL = "opal/core/references/agents.md"

# 검사 1 대상 — 기존 3종 파일럿(W-35 디스패치 지시가 명시한 고정 목록).
# W-49의 discover_pilots()처럼 opal/skills/opal-pilot-* 전체를 동적 스캔하지 않는다 —
# 이 검사는 "이 3종을 태스크 132가 건드리지 않았는가"라는 고정 귀속 질문이며, 신규
# 파일럿(oppb 포함)을 대상에 넣으면 질문 자체가 성립하지 않는다(oppb는 132가 신설한
# 파일럿이라 132 소유 커밋이 반드시 있다).
EXISTING_PILOT_REL_DIRS = (
    "opal/skills/opal-pilot-dev",
    "opal/skills/opal-pilot-project-loop",
    "opal/skills/opal-pilot-sdd",
)

# ─────────────────────────────────────────────────────────────────────────────
# 기준 커밋 — 왜 6ae6125이고, 왜 81d890d가 아닌가
# ─────────────────────────────────────────────────────────────────────────────
# 이 상수는 처음에 81d890d("feat(opal-agent): 공용 attempt runtime")로 잡았었다 —
# 81d890d가 "(132)"/"oppb" 태그 붙은 최초 커밋(74d3766, "test(oppb): G2~G4 RED 스위트
# 선작성")의 직접 부모라서였다. 하지만 이 파일 작성 중 실측으로 81d890d "자신의 트리"에
# 이미 state_tool.py의 STAGE_ENUM(P0~P5)·skill_enum/argparse choices의 "oppb" 항목이
# 들어 있음을 발견했다(git diff 81d890d^ 81d890d -- opal/tools/state-tool/state_tool.py
# 확인 — 커밋 메시지는 무관해 보이지만 실제 diff에 "# 132 W-3" 주석과 함께 그 추가가
# 섞여 커밋돼 있다, 태그 누락된 132 변경). 그 상태에서 검사 3(SharedInfraAdditiveTest)의
# enum 비교는 baseline == 현재(둘 다 이미 oppb 포함)라 "삭제 0"은 참이지만 "132가
# 실제로 무엇을 추가했는가"는 전혀 관측하지 못했다 — additive 성질을 증명하려던 검사가
# 공집합 비교로 무력화된 것이다.
#
# PM이 이 발견을 확인하고 기준을 81d890d의 부모 6ae6125("docs(oppl): Pilot 독립 관계
# 명시와 사용 기준 추가", 2026-09-14 13:10:48 — 132 W-3 변경이 아직 없는 마지막 지점)로
# 재확정했다. 이 파일 작성 중 재측정(ast.literal_eval 기반, 아래 SharedInfraAdditiveTest
# 참조):
#   skill_enum(지역)  : 10 → 11 | 삭제 0 | 추가 {'oppb'}
#   argparse choices  : 10 → 11 | 삭제 0 | 추가 {'oppb'}
#   STAGE_ENUM        : 20 → 26 | 삭제 0 | 추가 {'P0','P1','P2','P3','P4','P5'}
# 이제 additive 성질이 실제로 관측된다 — 검사 3은 "삭제 0"뿐 아니라 "추가 집합이
# 비어 있지 않음"도 단언해 baseline을 다시 잘못 잡는 회귀를 잡는다.
BASELINE_COMMIT = "6ae6125c35ebd0c61380575e8064dd202e9e7a66"

# 태스크 132 소유 커밋 식별 기준 — 커밋 메시지(subject)에 "(132)" 또는 대소문자 무관
# "oppb"가 나타나면 132 소유로 간주한다. 이 브랜치의 실측(6ae6125..HEAD 중 "(132)"|
# "oppb" 매치 8건 — e21029e/186fb1c/0862d1a/c25f627/a72cc47/1d2ff1d/9d7dbc6/74d3766, baseline을
# 81d890d에서 6ae6125로 정정해도 매치 건수는 동일하다: 81d890d 자신은 이 패턴에 매치되지
# 않는 커밋 메시지라 범위를 한 커밋 넓혀도 새로 잡히지 않는다)이 전부 실제 태스크 132
# 작업(TASK 캡슐·G2~G5 게이트·oppb RED 스위트)과 일치해 이 기준을 그대로 쓴다.
#
# 오탐(false positive) 가능성: 다른 태스크가 커밋 메시지 본문에 우연히 "oppb"라는
# 문자열을 언급하면(예: "oppb와의 경계를 문서화") 132 소유가 아닌데도 매치된다 —
# 이 브랜치에서는 실측상 발생하지 않았다(8건 전부 실제 132 작업).
# 누락(false negative) 가능성: 위 BASELINE_COMMIT 주석에서 확인했듯, 태그를 빠뜨린 채
# 132 변경분을 실은 커밋(81d890d 자체가 그 예 — 그래서 baseline에서 제외했다)이
# 존재할 수 있다 — 커밋 메시지 문자열 매칭은 그런 사례를 잡지 못한다. 이 검사가
# "0건"을 보고해도 "메시지에 태그가 없는 132 기원 변경이 절대 없다"는 완전한 보증은
# 아니다 — 81d890d 자체가 baseline 범위 밖(6ae6125..HEAD)에 있어 이 검사의 대상도
# 아니라는 점도 유의한다.
TASK_132_COMMIT_PATTERN = re.compile(r"\(132\)|oppb", re.IGNORECASE)


# ─────────────────────────────────────────────────────────────────────────────
# git 가용성 게이트 — 조용히 건너뛰지 않는다(W-35 명시 요건)
# ─────────────────────────────────────────────────────────────────────────────

def _check_git_baseline_availability() -> tuple[bool, str]:
    try:
        top = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=15,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return False, f"git 실행 자체가 실패했다({exc!r}) — git 미가용 환경으로 판단해 이 스위트를 skip한다."
    if top.returncode != 0:
        return False, (
            f"'git rev-parse --show-toplevel'이 exit {top.returncode}로 실패했다 "
            f"(stderr={top.stderr.strip()!r}) — git 저장소가 아니거나 git 미가용."
        )
    try:
        cat = subprocess.run(
            ["git", "cat-file", "-e", f"{BASELINE_COMMIT}^{{commit}}"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=15,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return False, f"git cat-file 실행 실패({exc!r})."
    if cat.returncode != 0:
        return False, (
            f"기준 커밋 {BASELINE_COMMIT}을 이 클론에서 조회할 수 없다(exit {cat.returncode}, "
            f"stderr={cat.stderr.strip()!r}) — 얕은 클론(shallow clone)이거나 이 ref가 "
            f"페치되지 않은 환경일 수 있다. CI 워크플로가 없는 이 저장소에서는 이런 환경을 "
            f"배제할 수 없어(W-49와 동일 근거) skip한다."
        )
    return True, ""


_GIT_AVAILABLE, _GIT_SKIP_REASON = _check_git_baseline_availability()


def _git(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True)


def _git_show(commit: str, rel_path: str) -> str:
    completed = _git(["show", f"{commit}:{rel_path}"])
    if completed.returncode != 0:
        raise AssertionError(
            f"git show {commit}:{rel_path} 실패(exit {completed.returncode}): {completed.stderr}"
        )
    return completed.stdout


def _commits_touching_path(base_commit: str, rel_path: str) -> list[str]:
    """base_commit..HEAD 구간에서 rel_path를 건드린 커밋을 '<short-hash> <subject>' 형식으로.

    기본 git log 병합 단순화(단일 부모로 완전히 설명되는 병합은 숨김)를 그대로 쓴다 —
    사람이 `git log -- <path>`로 보는 것과 동일한 결과이며, 이 파일 작성 중 병합 커밋
    diff를 직접 대조해 단순화로 숨겨진 항목이 실제로는 이미 비-병합 커밋으로 잡혀
    있음을 확인했다(보고 (4)항 참조).
    """
    completed = _git(["log", "--oneline", f"{base_commit}..HEAD", "--", rel_path])
    if completed.returncode != 0:
        raise AssertionError(f"git log 실패(exit {completed.returncode}): {completed.stderr}")
    return [line for line in completed.stdout.splitlines() if line.strip()]


# ─────────────────────────────────────────────────────────────────────────────
# 텍스트 보존(additive) 판정 — 줄 단위 정확 일치/부분포함이 아니라 토큰 부분열
# ─────────────────────────────────────────────────────────────────────────────
# 실측(이 파일 작성 중): actor.md·evaluator AGENT.md의 132 변경은 "줄 끝에 새 줄만
# 추가"가 아니라 "기존 한 줄의 중간에 새 구가 삽입되고 마침표·괄호 등 종결 문자가
# 뒤로 밀리는" 편집이다(예: "...범위 경계)." → "...범위 경계 / `oppb` — ...)."). 이때
# 정확한 줄 일치도, 단순 substring 포함도 실패한다(종결 문자가 붙은 원문 토큰
# "경계)."가 현재 줄에서 더 이상 인접하지 않음). 그래서 "구두점을 별도 토큰으로 분리한
# 단어열 부분열(subsequence)" 판정을 쓴다 — 원문 각 단어가 순서를 유지한 채 현재 줄에
# 전부 나타나면 통과, 실제로 어떤 단어가 사라지면(부분열이 깨지면) 실패한다. 아래
# sanity: 단어를 실제로 지운 경우는 이 판정이 잡아낸다(모듈 자체 테스트로 SelfCheck에서
# 확인).

_TOKEN_RE = re.compile(r"[\w`/·\-]+|[^\s\w]", re.UNICODE)


def _tokenize(line: str) -> list[str]:
    return _TOKEN_RE.findall(line)


def _is_token_subsequence(needle: list[str], haystack: list[str]) -> bool:
    it = iter(haystack)
    return all(tok in it for tok in needle)


def _lines_content_preserved(base_text: str, current_text: str) -> list[str]:
    """base_text의 각 (공백 아닌) 줄이 current_text의 어느 한 줄에 토큰 부분열로
    보존돼 있는지 확인한다. 보존되지 않은 base 줄 목록을 반환(빈 리스트 = 전부 보존)."""
    base_lines = [l for l in base_text.splitlines() if l.strip()]
    current_lines = [l for l in current_text.splitlines() if l.strip()]
    current_token_lists = [_tokenize(cl) for cl in current_lines]
    missing = []
    for bl in base_lines:
        bt = _tokenize(bl)
        if any(_is_token_subsequence(bt, ct) for ct in current_token_lists):
            continue
        missing.append(bl)
    return missing


# ═════════════════════════════════════════════════════════════════════════════
# 0. SelfCheckTest — 위 판정 헬퍼 자체가 실제 삭제를 잡아내는지(오검출 방지)
# ═════════════════════════════════════════════════════════════════════════════

class SelfCheckTest(unittest.TestCase):
    """git 없이도 항상 실행 — 본 모듈의 판정 로직이 '진짜 삭제'를 통과시켜버리지
    않는지 자체 검증한다. 이 테스트가 깨지면 아래 모든 additive 판정을 신뢰할 수 없다."""

    def test_token_subsequence_accepts_middle_insertion(self):
        base = "목록 밖 Pilot이 --pm을 수신하면 조용히 무시하지 않는다."
        current = "목록 밖 Pilot이 --pm을 수신하면(oppb 제외) 조용히 무시하지 않는다."
        missing = _lines_content_preserved(base, current)
        self.assertEqual(missing, [], "중간 삽입 편집을 삭제로 오검출했다.")

    def test_token_subsequence_rejects_real_deletion(self):
        base = "opd, opds, opsdd 세 파일럿을 지원한다."
        current = "opd 파일럿을 지원한다."  # opds, opsdd 토큰이 실제로 사라짐
        missing = _lines_content_preserved(base, current)
        self.assertNotEqual(missing, [], "실제 삭제(opds·opsdd 소실)를 잡아내지 못했다 — 판정 로직 결함.")

    def test_token_subsequence_rejects_total_unrelated_replacement(self):
        base = "이 문서가 소유한다. 지원 범위를 넓히려면 별도 태스크가 필요하다."
        current = "전혀 관련 없는 새 문단."
        missing = _lines_content_preserved(base, current)
        self.assertEqual(len(missing), 1, "완전 무관한 교체를 보존으로 오검출했다.")


# ═════════════════════════════════════════════════════════════════════════════
# 1. AttributionTest — 검사 1: 기존 파일럿 파일의 변경 귀속
# ═════════════════════════════════════════════════════════════════════════════

@unittest.skipUnless(_GIT_AVAILABLE, _GIT_SKIP_REASON)
class AttributionTest(unittest.TestCase):
    """baseline..HEAD 구간에서 opd/oppl/opsdd 파일을 건드린 커밋 중 태스크 132 소유가
    0건임을 단언한다. 이 파일들은 실제로 변경돼 있다(태스크 131·133·136 소유) —
    "바이트 동일"이 아니라 "132가 안 건드렸다"만 확인한다."""

    def test_no_task132_commit_touched_existing_pilot_files(self):
        for rel_dir in EXISTING_PILOT_REL_DIRS:
            with self.subTest(pilot_dir=rel_dir):
                commits = _commits_touching_path(BASELINE_COMMIT, rel_dir)
                owned_by_132 = [
                    line for line in commits
                    if TASK_132_COMMIT_PATTERN.search(line.split(" ", 1)[1] if " " in line else line)
                ]
                self.assertEqual(
                    owned_by_132, [],
                    f"{rel_dir}: baseline({BASELINE_COMMIT[:7]}) 이후 태스크 132 소유로 "
                    f"보이는 커밋이 있다 — {owned_by_132}. 전체 변경 커밋: {commits}",
                )

    def test_existing_pilot_files_were_in_fact_touched_by_other_tasks(self):
        """대조군 — 이 파일들이 '아무도 안 건드렸다'가 아니라 '132만 안 건드렸다'임을
        확인한다. 커밋이 0건이면 baseline 선택이나 경로가 잘못됐을 가능성이 크다."""
        for rel_dir in EXISTING_PILOT_REL_DIRS:
            with self.subTest(pilot_dir=rel_dir):
                commits = _commits_touching_path(BASELINE_COMMIT, rel_dir)
                self.assertTrue(
                    commits,
                    f"{rel_dir}: baseline 이후 이 경로를 건드린 커밋이 0건이다 — PM 실측"
                    f"(131/133/136 소유)과 불일치한다. baseline 커밋({BASELINE_COMMIT}) 선택"
                    f"이나 경로가 잘못됐을 수 있다.",
                )


# ═════════════════════════════════════════════════════════════════════════════
# 2. RegistryAgentRemovalTest — 검사 2: 레지스트리·에이전트 항목 제거 0건
# ═════════════════════════════════════════════════════════════════════════════

def _registry_entry_identities(text: str) -> set[tuple[str, str | None]]:
    data = json.loads(text)
    identities: set[tuple[str, str | None]] = set()
    for group, entries in data.get("groups", {}).items():
        for entry in entries:
            identities.add((group, entry.get("name")))
    return identities


_HEADING_RE = re.compile(r"^#{1,6}\s+.+$")


def _markdown_headings(text: str) -> set[str]:
    return {line.strip() for line in text.splitlines() if _HEADING_RE.match(line)}


@unittest.skipUnless(_GIT_AVAILABLE, _GIT_SKIP_REASON)
class RegistryAgentRemovalTest(unittest.TestCase):
    """PM 실측: registry 항목 52 → 55(0건 소실, 3건 추가), agents.md 헤딩도 전건 생존
    + 신규 절 추가. baseline 집합이 현재 집합의 부분집합인지를 항목 identity로 확인한다."""

    def test_registry_entries_are_superset_of_baseline(self):
        base_ids = _registry_entry_identities(_git_show(BASELINE_COMMIT, REGISTRY_REL))
        current_ids = _registry_entry_identities(REGISTRY_PATH.read_text(encoding="utf-8"))
        missing = base_ids - current_ids
        self.assertEqual(
            missing, set(),
            f"opal-skills-registry.json에서 baseline 대비 사라진 항목(group, name): {missing}",
        )
        self.assertGreaterEqual(
            len(current_ids), len(base_ids),
            "현재 registry 항목 수가 baseline보다 적다 — 순수 추가만이어야 한다.",
        )

    def test_agents_md_headings_are_superset_of_baseline(self):
        base_headings = _markdown_headings(_git_show(BASELINE_COMMIT, AGENTS_MD_REL))
        current_headings = _markdown_headings(AGENTS_MD_PATH.read_text(encoding="utf-8"))
        missing = base_headings - current_headings
        self.assertEqual(
            missing, set(),
            f"agents.md에서 baseline 대비 사라진 헤딩: {missing}",
        )


# ═════════════════════════════════════════════════════════════════════════════
# 3. SharedInfraAdditiveTest — 검사 3: 공유 인프라 5(6)접점의 additive 성질
# ═════════════════════════════════════════════════════════════════════════════
# opal-skills-registry.json·agents.md는 위 검사 2가 이미 "항목 제거 0건"으로 이
# 성질을 확인했으므로 여기서 재확인하지 않는다(동일 성질, 동일 파일 — 진짜 중복은
# 피한다). 이 클래스는 나머지 4개 접점(state_tool.py enum 2종·argparse 1종,
# harness/actor.md, opal-evaluator-agent/AGENT.md의 기존 4개 phase 분기,
# op-scenario-gate/SKILL.md의 기존 OPPD(opd/opds/opsdd) 분기)을 본다.

_STAGE_ENUM_RE = re.compile(r"STAGE_ENUM\s*=\s*\[(.*?)\]", re.DOTALL)
_LOCAL_SKILL_ENUM_RE = re.compile(r"skill_enum\s*=\s*\[([^\]]*)\]")
_ARGPARSE_SKILL_CHOICES_RE = re.compile(
    r'"--skill",\s*required=True,\s*choices=\[([^\]]*)\]', re.DOTALL
)

# 기존 4개 phase(W-25 이전부터 있던 값) — evaluator AGENT.md 생존 확인 anchor.
EVALUATOR_EXISTING_PHASES = ("design-review", "spec-review", "drift-recheck", "scenario-rubric")

# op-scenario-gate SKILL.md의 기존 OPPD 계열 pilot 목록 선언 — 생존 확인 anchor.
SCENARIO_GATE_OPPD_PILOT_LINE = "`pilot`: `opd`, `opds`, `opsdd`"


def _extract_bracket_literal(source_text: str, pattern: re.Pattern, label: str) -> set[str]:
    match = pattern.search(source_text)
    if not match:
        raise AssertionError(
            f"{label} 리터럴을 소스에서 찾지 못했다 — 소스 구조가 바뀌었다면 이 정규식"
            f"(opal/tools/oppb-runtime-tool/tests/test_pilot_isolation.py)을 갱신하라."
        )
    return set(ast.literal_eval("[" + match.group(1) + "]"))


@unittest.skipUnless(_GIT_AVAILABLE, _GIT_SKIP_REASON)
class SharedInfraAdditiveTest(unittest.TestCase):
    def test_state_tool_enum_sets_are_supersets_of_baseline(self):
        """baseline(6ae6125) 재확정 근거(위 BASELINE_COMMIT 주석 참조): 81d890d를 쓰면
        132 W-3 변경이 이미 baseline 안에 들어가 있어 이 검사가 "삭제 0"만 참으로
        만들고 "추가 관측"은 통과시키지 못하는 공집합 비교로 무력화된다. 그래서 삭제
        0건뿐 아니라 **추가 집합이 실제로 비어 있지 않음**도 단언한다 — baseline을
        다시 잘못 잡아(예: OPPB 도입 이후 커밋으로 되돌리면) 이 검사가 무의미해지는
        회귀를 그 자리에서 잡는다. 기대 추가값은 PM 재측정과 이 파일 작성 중 실측이
        일치한 최소 하한이며, 이후 132가 값을 더 추가해도(하한의 상위집합이면) 통과한다."""
        base_source = _git_show(BASELINE_COMMIT, "opal/tools/state-tool/state_tool.py")
        current_source = STATE_TOOL_PATH.read_text(encoding="utf-8")
        checks = (
            ("STAGE_ENUM", _STAGE_ENUM_RE, {"P0", "P1", "P2", "P3", "P4", "P5"}),
            ("validate_pipeline_spec() 지역 skill_enum", _LOCAL_SKILL_ENUM_RE, {"oppb"}),
            ("init --skill argparse choices", _ARGPARSE_SKILL_CHOICES_RE, {"oppb"}),
        )
        for label, pattern, expected_min_added in checks:
            with self.subTest(target=label):
                base_values = _extract_bracket_literal(base_source, pattern, label)
                current_values = _extract_bracket_literal(current_source, pattern, label)
                missing = base_values - current_values
                added = current_values - base_values
                self.assertEqual(
                    missing, set(),
                    f"{label}: baseline 대비 사라진 값 {missing} — additive-only 위반.",
                )
                self.assertTrue(
                    added,
                    f"{label}: baseline({BASELINE_COMMIT[:7]}) 대비 추가된 값이 0건이다 — "
                    f"baseline이 이미 132 변경을 포함해 이 검사가 무의미해졌을 수 있다 "
                    f"(81d890d에서 겪은 것과 동일한 실패 유형).",
                )
                self.assertTrue(
                    expected_min_added.issubset(added),
                    f"{label}: 기대 최소 추가값 {expected_min_added}이 실제 추가값 {added}의 "
                    f"부분집합이 아니다 — PM 재측정(10→11 또는 20→26)과 불일치한다.",
                )

    def test_actor_md_existing_scope_boundary_preserved(self):
        base_text = _git_show(BASELINE_COMMIT, "opal/core/references/harness/actor.md")
        current_text = ACTOR_MD_PATH.read_text(encoding="utf-8")
        missing = _lines_content_preserved(base_text, current_text)
        self.assertEqual(
            missing, [],
            f"harness/actor.md에서 baseline 대비 사라진 내용: {missing}",
        )

    def test_evaluator_agent_existing_four_phases_survive(self):
        base_text = _git_show(BASELINE_COMMIT, "opal/agents/opal-evaluator-agent/AGENT.md")
        current_text = EVALUATOR_AGENT_MD_PATH.read_text(encoding="utf-8")
        missing = _lines_content_preserved(base_text, current_text)
        self.assertEqual(
            missing, [],
            f"opal-evaluator-agent/AGENT.md에서 baseline 대비 사라진 내용: {missing}",
        )
        for phase in EVALUATOR_EXISTING_PHASES:
            with self.subTest(phase=phase):
                self.assertIn(
                    f"`{phase}`", current_text,
                    f"기존 phase 분기 '{phase}'가 현재 AGENT.md에서 사라졌다.",
                )
                self.assertIn(
                    f"`{phase}`", base_text,
                    f"anchor phase '{phase}'가 baseline에도 없다 — anchor 목록 오류.",
                )

    def test_scenario_gate_skill_existing_oppd_branch_survives(self):
        base_text = _git_show(BASELINE_COMMIT, "opal/skills/op-scenario-gate/SKILL.md")
        current_text = SCENARIO_GATE_SKILL_MD_PATH.read_text(encoding="utf-8")
        missing = _lines_content_preserved(base_text, current_text)
        self.assertEqual(
            missing, [],
            f"op-scenario-gate/SKILL.md에서 baseline 대비 사라진 내용: {missing}",
        )
        self.assertIn(
            SCENARIO_GATE_OPPD_PILOT_LINE, base_text,
            "anchor 문자열이 baseline에 없다 — anchor 자체가 잘못됐다.",
        )
        self.assertIn(
            SCENARIO_GATE_OPPD_PILOT_LINE, current_text,
            "기존 OPPD 계열(opd/opds/opsdd) pilot 목록 선언이 현재 SKILL.md에서 사라졌다.",
        )


# ═════════════════════════════════════════════════════════════════════════════
# 4. RecoveryContractTest — 검사 4: 복구 계약(OPPB 런타임 결함의 비전파)
# ═════════════════════════════════════════════════════════════════════════════
# W-49의 FaultIsolationTest와 겹치지 않는 축: W-49는 "pipeline.json *스펙 데이터*가
# 손상됐을 때 다른 파일럿(스펙 데이터)의 spec-validate가 영향받지 않는가"를 본다.
# 이 클래스는 "OPPB *런타임 코드*(oppb_runtime_tool.py 등 .py 모듈)가 깨졌을 때
# 공유 CLI(state-tool)의 OPPD 경로가 영향받지 않는가"를 본다 — 결함의 종류(코드 vs
# 데이터)와 전파 매개(모듈 import vs 파일 읽기)가 다르다.

_PY_IMPORT_EXCLUDE_DIR_NAMES = {"__pycache__", ".venv", "venv", "node_modules", ".git"}


class RecoveryContractTest(unittest.TestCase):
    def test_no_external_python_import_of_oppb_runtime_modules(self):
        """OPPB 런타임 모듈(oppb-runtime-tool/*.py)을 그 디렉터리 밖의 어떤 .py 파일도
        import하지 않음을 정적으로 단언한다 — 이것이 "OPPB 런타임 결함이 전파될 수
        없다"는 구조적 근거다(PM 실측 확인 — 디스패치 지시가 명시한 유용한 검사)."""
        module_names = sorted(p.stem for p in OPPB_TOOL_DIR.glob("*.py"))
        self.assertTrue(module_names, "oppb-runtime-tool에 .py 모듈이 없다 — 경로가 어긋났다.")
        name_alt = "|".join(re.escape(m) for m in module_names)
        import_re = re.compile(
            rf"^\s*(?:import\s+(?:{name_alt})\b|from\s+(?:{name_alt})\s+import\b)",
            re.MULTILINE,
        )
        offenders: list[str] = []
        for py_file in REPO_ROOT.rglob("*.py"):
            if any(part in _PY_IMPORT_EXCLUDE_DIR_NAMES for part in py_file.parts):
                continue
            try:
                py_file.relative_to(OPPB_TOOL_DIR)
                continue  # oppb-runtime-tool 자기 자신(구현+테스트)은 대상에서 제외
            except ValueError:
                pass
            text = py_file.read_text(encoding="utf-8", errors="ignore")
            for match in import_re.finditer(text):
                offenders.append(f"{py_file.relative_to(REPO_ROOT)}: {match.group(0).strip()}")
        self.assertEqual(
            offenders, [],
            f"oppb-runtime-tool 밖에서 그 모듈을 import하는 코드가 발견됐다: {offenders}",
        )

    def test_oppd_spec_validate_unaffected_by_broken_oppb_runtime_copy(self):
        """OPPB 런타임 모듈의 '고장난 사본'을 만들어(실제 배포 파일은 절대 건드리지
        않음) 그 디렉터리를 PYTHONPATH 최우선에 둔 채로, 실제 opd(opal-pilot-dev)
        pipeline.json에 대해 공개 CLI `state-tool spec-validate`를 실행한다. 위 정적
        검사가 참이라면(0 external import) 이 고장이 state-tool 실행에 전혀 영향을
        주지 않아야 한다 — 그 사실을 실제 프로세스 실행으로 실증한다."""
        tmp_dir = tempfile.mkdtemp(prefix="w35-oppb-fault-injection-")
        try:
            broken_module = Path(tmp_dir) / "oppb_runtime_tool.py"
            broken_module.write_text(
                "def broken(:\n    이것은 유효한 파이썬이 아니다\n", encoding="utf-8"
            )

            # sanity — 고장 fixture 자체가 실제로 import 불가능한지 먼저 확인한다.
            # (그렇지 않으면 아래 본 검사가 "고장이 전파 안 됐다"를 잘못 증명하게 된다.)
            compile_probe = subprocess.run(
                [sys.executable, "-c",
                 f"import py_compile; py_compile.compile({str(broken_module)!r}, doraise=True)"],
                capture_output=True, text=True,
            )
            self.assertNotEqual(
                compile_probe.returncode, 0,
                "고장 fixture(oppb_runtime_tool.py 사본)가 실제로는 컴파일에 성공했다 — "
                "이 fixture로는 결함 주입을 실증할 수 없다.",
            )

            oppd_pipeline = (
                REPO_ROOT / "opal" / "skills" / "opal-pilot-dev" / "references" / "pipeline.json"
            )
            self.assertTrue(oppd_pipeline.exists(), f"실제 oppd pipeline.json 부재: {oppd_pipeline}")

            env = dict(os.environ)
            env["PYTHONPATH"] = tmp_dir + os.pathsep + env.get("PYTHONPATH", "")
            result = subprocess.run(
                [sys.executable, str(STATE_TOOL_PATH), "spec-validate", str(oppd_pipeline)],
                capture_output=True, text=True, env=env,
            )
            self.assertEqual(
                result.returncode, 0,
                f"OPPB 런타임 모듈 고장 사본이 PYTHONPATH에 있을 때 state-tool spec-validate "
                f"(oppd)가 exit {result.returncode}로 실패했다 — 복구 계약 위반.\n"
                f"stdout={result.stdout!r}\nstderr={result.stderr!r}",
            )
            try:
                data = json.loads(result.stdout)
            except json.JSONDecodeError:
                self.fail(f"spec-validate stdout이 JSON이 아니다: {result.stdout!r}")
            self.assertTrue(data.get("ok"), f"spec-validate ok=false: {data}")
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
