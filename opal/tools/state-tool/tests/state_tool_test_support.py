"""
@header {
  "module": "state_tool_test_support",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "분리된 state-tool 테스트 모듈이 공유하는 상수·fixture·helper·base class. pytest 수집 대상 Test* 클래스는 포함하지 않는다.",
  "exports": ["BaseTestCase", "_T093Base", "make_args"]
}
"""

# TASK T-11: 표준 라이브러리만 import
import argparse
import ast
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch, MagicMock

# state_tool.py를 직접 import (PYTHONPATH 조정)
_TOOL_DIR = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(_TOOL_DIR))
import state_tool as ST
import state_tool_parts.base as ST_BASE  # 시각·모듈 로더 주입점(patch 대상)

# 056: TestOpplSkillInit용 — run.sh 공개 인터페이스 subprocess 실호출 (mock 금지, red-first.md §4)
_RUN_SH = _TOOL_DIR / "run.sh"


def _run094(args_list):
    """094: run.sh 공개 인터페이스 subprocess 실호출 → (returncode, stdout_str, stderr_str, parsed_json).
    [MUST] red-first.md §4: 공개 인터페이스(stdout/exit code)만 관찰 — mock/patch/MagicMock 금지.
    STATE.md 저널화(094) RED 테스트 전용 — TestJournalResilience/TestLegacyCoexistence/
    TestShowAsQueryStandard 및 기존 클래스 추가분(S-1~S-32)이 공유한다."""
    cmd = ["bash", str(_RUN_SH)] + args_list
    result = subprocess.run(cmd, capture_output=True, text=True)
    stdout = result.stdout.strip()
    try:
        data = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        data = {"_raw": stdout}
    return result.returncode, stdout, result.stderr, data


# 094: opd pipeline.json 실 스펙 경로 — TEST-SCENARIO.md §2.1 "pipeline 스펙" 실 파일 자산.
# task.task_md 등 gate 필드 없는 순수 행이 다수라 mark/advance/block 회귀 시나리오에 적합하다.
_OPD_REAL_PIPELINE_JSON = _TOOL_DIR.parent.parent / "skills" / "opal-pilot-dev" / "references" / "pipeline.json"


def _extract_md_section(md, heading):
    """094: `## {heading}` 섹션 본문(다음 `## ` 헤딩 직전까지)을 반환. 없으면 "".
    파이프라인 현황판 표와 의사결정 로그 표가 동일한 '| N | ... |' 행 형태를
    공유하므로, 행 수 계산은 반드시 이 헬퍼로 섹션을 먼저 격리한 뒤 수행한다
    (그렇지 않으면 파이프라인 표 행까지 오카운트된다)."""
    m = re.search(rf"^## {re.escape(heading)}\n", md, re.MULTILINE)
    if not m:
        return ""
    start = m.end()
    nxt = re.search(r"^## ", md[start:], re.MULTILINE)
    end = start + nxt.start() if nxt else len(md)
    return md[start:end]


def _decision_log_row_numbers(md):
    """094: '## 의사결정 로그' 표의 '#' 컬럼 값 목록을 등장 순서대로 반환."""
    section = _extract_md_section(md, "의사결정 로그")
    return re.findall(r"^\|\s*(\d+)\s*\|", section, re.MULTILINE)


def _find_repo_task_dir(repo_root: pathlib.Path, prefix: str) -> pathlib.Path:
    """109 — 태스크 폴더 위치(`tasks/` 직속 vs `tasks/backup/` 아래)에 내성인
    접두사 탐색. `tasks/{prefix}*`·`tasks/backup/{prefix}*` 2개 글롭(1-depth,
    `rglob` 금지)을 합쳐 정확히 1건일 때만 반환한다. 0건·2건 이상은 실패
    (`self.fail()` 아님 — 모듈 레벨 헬퍼이므로 `AssertionError`를 직접 던져
    호출측 TestCase의 실패로 전파한다). [MUST] 대상 부재를 skipTest로
    강등하지 않는다 — 위치 이동 검증이 이 헬퍼의 존재 이유이며, 조용한 skip은
    검증 무력화다."""
    candidates = sorted((repo_root / "tasks").glob(f"{prefix}*"))
    candidates += sorted((repo_root / "tasks" / "backup").glob(f"{prefix}*"))
    if len(candidates) != 1:
        raise AssertionError(
            f"[FIX-PIN] _find_repo_task_dir(prefix={prefix!r}) 매칭 {len(candidates)}건 "
            f"(정확히 1건 기대). 검색 경로: "
            f"{repo_root / 'tasks' / (prefix + '*')}, "
            f"{repo_root / 'tasks' / 'backup' / (prefix + '*')}. 발견: {candidates}. "
            f"이 단언은 접두사 매칭 1건 고정에 대한 것이다 — 대상 폴더가 삭제됐거나 "
            f"동일 접두사가 중복 생성됐다면 신 스키마 실파일로 대체 fixture를 선정해야 한다."
        )
    return candidates[0]

# ─────────────────────────────────────────────────────────────────────────────
# 테스트 공통 픽스처 / 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

SAMPLE_ROWS_SPEC = json.dumps([
    {"stage": "TASK",    "item": "작업"},
    {"stage": "TASK",    "item": "TASK.md 생성"},
    {"stage": "TASK",    "item": "사용자 확인"},
    {"stage": "PLAN",    "item": "작업"},
    {"stage": "PLAN",    "item": "PLAN.md 생성"},
    {"stage": "PLAN",    "item": "QA Gate"},
    {"stage": "PLAN",    "item": "QA-PLAN.md 생성"},
    {"stage": "PLAN",    "item": "State Gate"},
    {"stage": "PLAN",    "item": "PM Gate"},
    {"stage": "PLAN",    "item": "State Gate"},
    {"stage": "PLAN",    "item": "사용자 확인"},
    {"stage": "EXECUTE", "item": "작업"},
    {"stage": "EXECUTE", "item": "QA Gate"},
    {"stage": "EXECUTE", "item": "QA-EXECUTE.md 생성"},
    {"stage": "EXECUTE", "item": "State Gate"},
    {"stage": "EXECUTE", "item": "PM Gate"},
    {"stage": "EXECUTE", "item": "State Gate"},
    {"stage": "EXECUTE", "item": "사용자 확인"},
    {"stage": "CLOSE",   "item": "DONE.md 생성"},
    {"stage": "CLOSE",   "item": "State Gate"},
])

GATE_ROWS_SPEC = json.dumps([
    {"stage": "PLAN", "item": "작업"},
    {"stage": "PLAN", "item": "QA Gate"},
    {"stage": "PLAN", "item": "State Gate"},
    {"stage": "PLAN", "item": "PM Gate"},
    {"stage": "PLAN", "item": "State Gate"},
    {"stage": "PLAN", "item": "사용자 확인"},
    {"stage": "CLOSE", "item": "DONE.md 생성"},
    {"stage": "CLOSE", "item": "State Gate"},
])

SIMPLE_ROWS_SPEC = json.dumps([
    {"stage": "TASK",    "item": "작업"},
    {"stage": "PLAN",    "item": "작업"},
    {"stage": "EXECUTE", "item": "작업"},
    {"stage": "CLOSE",   "item": "State Gate"},
])




def _mock_now():
    """date.js 호출을 모킹하는 패치 컨텍스트."""
    return patch.object(ST_BASE, "get_kst_datetime", return_value="2026-05-01 23:00")


def make_args(**kwargs):
    """argparse Namespace 유사 객체 생성 헬퍼."""
    defaults = {
        "task_path": None,
        "skill": "opp",
        "mode": "interactive",
        "task_title": None,
        "next_action": None,
        "rows_spec": None,
        "rows_from": None,
        "rows_acts": None,
        "force": False,
        "note": None,
        "import_existing": False,
        "format": "md",
        "row": None,
        "done": True,
        "as_worker": False,
        "worker_stage": None,
        "step": None,
        "owner": None,
        "auto_pass": False,
        "reason": None,
        "after": None,
        "stage": None,
        "item": None,
        "set": None,
        "start": None,
        # 005: clarification-check 플래그 기본값 (AttributeError 방지)
        "clarification_check": False,
        "task_md": None,
        # 070: task-step 키 주소 체계 신규 플래그 기본값 (PLAN §3.3.2/§3.7.2) —
        # GREEN에서 resolve_row_index가 args.task_step/args.task_step_id를 참조하게
        # 되므로, 기존 테스트(이 값들을 지정하지 않는 호출)가 AttributeError 없이
        # 통과하도록 지금 defaults에 추가한다(005 선례와 동일한 유일 허용 접점).
        "task_step": None,
        "task_step_id": None,
        "action_step": None,  # dest="step" 공유 별칭(§3.3.2) — 미사용 시 무해
        "key": None,
        "after_task_step": None,
        "after_task_step_id": None,
    }
    defaults.update(kwargs)
    ns = types.SimpleNamespace(**defaults)
    return ns


class BaseTestCase(unittest.TestCase):
    """임시 디렉토리 + date.js 모킹 공통 베이스.
    [MUST] AGENT.md §확정 기준 #2: tempfile.mkdtemp() 사용, ~/ .opal/ 수정 금지.
    """

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())
        self.task_path = self.tmpdir / "134-260501-test"
        self.task_path.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _call_cmd(self, fn, args, expect_ok=True):
        """명령 함수 호출 → (exit_code, result_dict) 반환.
        ok()는 SystemExit를 발생시키지 않고 print만 하므로 stdout을 캡처.
        err()는 SystemExit를 발생시키므로 둘 다 처리.
        """
        import io
        from contextlib import redirect_stdout
        out = io.StringIO()
        exit_code = 0
        with redirect_stdout(out):
            try:
                fn(args)
            except SystemExit as e:
                exit_code = e.code
        output = out.getvalue().strip()
        result = json.loads(output) if output else {}
        return exit_code, result

    def _init(self, rows_spec=SIMPLE_ROWS_SPEC, mode="interactive", force=False,
               note=None, import_existing=False, next_action=None, task_title=None):
        """기본 init 헬퍼."""
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                skill="opp", mode=mode,
                rows_spec=rows_spec,
                force=force, note=note,
                import_existing=import_existing,
                next_action=next_action,
                task_title=task_title,
            )
            exit_code, result = self._call_cmd(ST.cmd_init, args)
            self.assertEqual(exit_code, 0, f"init failed: {result}")

    def _state(self):
        return json.loads((self.task_path / "state.json").read_text())

    def _md(self):
        return (self.task_path / "STATE.md").read_text()

    def _mark(self, row_id, note=None, as_worker=False, worker_stage=None,
               auto_pass=False, owner=None, force=False, step=None):
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                row=row_id, done=True,
                note=note, as_worker=as_worker,
                worker_stage=worker_stage,
                auto_pass=auto_pass, owner=owner,
                force=force, step=step,
            )
            exit_code, _ = self._call_cmd(ST.cmd_mark, args)
            return exit_code

    def _advance(self, row_id, note=None):
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                row=row_id, note=note,
            )
            exit_code, _ = self._call_cmd(ST.cmd_advance, args)
            return exit_code

    def _block(self, row_id, reason="test reason"):
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                row=row_id, reason=reason,
            )
            exit_code, _ = self._call_cmd(ST.cmd_block, args)
            return exit_code

    def _add_row(self, after, stage, item, note=None):
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                after=after, stage=stage, item=item, note=note,
            )
            exit_code, _ = self._call_cmd(ST.cmd_add_row, args)
            return exit_code

    def _status_set(self, to_status, note=None):
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                set=to_status, note=note,
            )
            exit_code, _ = self._call_cmd(ST.cmd_status, args)
            return exit_code

    def _validate(self):
        args = make_args(task_path=str(self.task_path))
        _, result = self._call_cmd(ST.cmd_validate, args)
        return result


# ═════════════════════════════════════════════════════════════════════════════
# A. 9개 명령 Happy Path (§3 Step 2 "C. 9개 명령 happy path")
# ═════════════════════════════════════════════════════════════════════════════



















# ═════════════════════════════════════════════════════════════════════════════
# B. 23종 에러 코드 (PLAN §2.18 E-1) — cross-ref: 함수명에 에러 코드 명시
# ═════════════════════════════════════════════════════════════════════════════



# ═════════════════════════════════════════════════════════════════════════════
# C. G-5~G-15 심층 시나리오 (PLAN §3 Step 2)
# ═════════════════════════════════════════════════════════════════════════════











# ═════════════════════════════════════════════════════════════════════════════
# D. 기본 시나리오 (PLAN §3 Step 2 "A. 기본 시나리오")
# ═════════════════════════════════════════════════════════════════════════════



# [T094 삭제·D-2/R-3] TestImportPreservesKeys 클래스 전체(5건: test_force_import_preserves_all_keys,
# test_import_with_pipeline_json_restores_keys, test_import_no_key_source_keyless_with_warning,
# test_preserved_keys_keep_schema_version_1_1, test_duplicate_stage_item_ordered_consumption) —
# 074가 도입한 `--import-existing` key 재접합 로직(`parse_existing_state_md`/
# `_key_source_index`/`_reattach_import_keys`)이 094 D-2로 전부 삭제되어 이 클래스가
# 검증하던 기능 자체가 소멸했다. 대체 회귀 커버리지는
# `TestInit.test_s9_import_existing_removed_rejected`(호출 시 즉시 거부)가 담당한다.

# ═════════════════════════════════════════════════════════════════════════════
# E. 자유 텍스트 영역 보존 (PLAN §3 Step 2 마지막 항목)
# ═════════════════════════════════════════════════════════════════════════════



# ═════════════════════════════════════════════════════════════════════════════
# 072: TestNextActionAutoDerive — STATE.md "다음 액션" 자동 파생 RED-first
# (TEST-SCENARIO.md S-1~S-4, S-6, S-7 / red-first.md §2,§4 — 작성자≠구현자,
#  공개 인터페이스(CLI 서브명령 호출 → state.json/STATE.md 관측)로만 검증)
# ═════════════════════════════════════════════════════════════════════════════



# ═════════════════════════════════════════════════════════════════════════════
# F. C-1~C-6 충돌/종속 관계 (PLAN §2.19.10)
# ═════════════════════════════════════════════════════════════════════════════



# ═════════════════════════════════════════════════════════════════════════════
# G. rows-from SKILL.md 파싱 (PLAN §2.20.2)
# ═════════════════════════════════════════════════════════════════════════════



# ═════════════════════════════════════════════════════════════════════════════
# H. ERROR_CODES 상수 완전성 검증
# ═════════════════════════════════════════════════════════════════════════════



# ═════════════════════════════════════════════════════════════════════════════
# I-0. verify 명령 — 헌법 §4 동작 증거 강제 게이트 (PLAN 013)
# ═════════════════════════════════════════════════════════════════════════════



# ═════════════════════════════════════════════════════════════════════════════
# I. 추가 시나리오: add-row schema validate 통과 (PLAN §2.12 G-9 단계 6)
# ═════════════════════════════════════════════════════════════════════════════



# ═════════════════════════════════════════════════════════════════════════════
# J. Stage-Transition Guard (PLAN §M-A stage-transition guard)
# ═════════════════════════════════════════════════════════════════════════════



# ═════════════════════════════════════════════════════════════════════════════
# K. 014 Phase 4 — 새 표준 행 구조 (QA Gate/State Gate 행 없음) 정합
# ═════════════════════════════════════════════════════════════════════════════

# opds 새 10행 표준 구조 (Phase 2에서 확정 — QA Gate/State Gate 행 없음).
# Gate는 "PM Gate"와 "사용자 확인"만 남고, State Gate는 stage-transition guard로 이전,
# QA Gate는 PM Gate로 통합, CLOSE 마지막 행은 "DONE.md 생성".
NEW_OPDS_ROWS_SPEC = json.dumps([
    {"stage": "TASK",    "item": "작업"},
    {"stage": "TASK",    "item": "사용자 확인"},
    {"stage": "PLAN",    "item": "작업"},
    {"stage": "PLAN",    "item": "PM Gate"},
    {"stage": "PLAN",    "item": "사용자 확인"},
    {"stage": "EXECUTE", "item": "작업"},
    {"stage": "TEST",    "item": "작업"},
    {"stage": "TEST",    "item": "PM Gate"},
    {"stage": "TEST",    "item": "사용자 확인"},
    {"stage": "CLOSE",   "item": "DONE.md 생성"},
])








# ═════════════════════════════════════════════════════════════════════════════
# K. RED-first TDD 트랙 — RED 게이트·테스트 불변성 단위 테스트 (PLAN 016)
# ═════════════════════════════════════════════════════════════════════════════



# ═════════════════════════════════════════════════════════════════════════════
# [T017] 다중 Step EXECUTE 행 조기 done 가드
# ═════════════════════════════════════════════════════════════════════════════



# ═════════════════════════════════════════════════════════════════════════════
# K. 명확화 게이트 (PLAN 005) — RED-first TDD 트랙
#    verify --clarification-check 직접 호출 케이스 ①~⑥
#    자동 훅(cmd_mark/cmd_advance) 케이스 ⑦~⑨
#    회귀 보호 케이스 ⑩
# ═════════════════════════════════════════════════════════════════════════════

# ── TASK.md 픽스처 콘텐츠 상수 ───────────────────────────────────────────────

_TASK_MD_ALL_FILLED = """\
# TASK: 테스트 태스크

## 명확화 결과

| 요소 | 확정값 | 미확정 | 의존 사실 |
|------|--------|--------|----------|
| 목표 | 테스트 목표 확정 | - | - |
| 범위 | 포함·제외 확정 | - | - |
| 제약 | 기술 제약 확정 | - | - |
| 완료기준 | 검증 가능 기준 확정 | - | - |
"""

_TASK_MD_ONE_BLANK = """\
# TASK: 테스트 태스크

## 명확화 결과

| 요소 | 확정값 | 미확정 | 의존 사실 |
|------|--------|--------|----------|
| 목표 | 테스트 목표 확정 | - | - |
| 범위 |  | - | - |
| 제약 | 기술 제약 확정 | - | - |
| 완료기준 | 검증 가능 기준 확정 | - | - |
"""

_TASK_MD_ONE_TBD = """\
# TASK: 테스트 태스크

## 명확화 결과

| 요소 | 확정값 | 미확정 | 의존 사실 |
|------|--------|--------|----------|
| 목표 | 테스트 목표 확정 | - | - |
| 범위 | TBD | - | - |
| 제약 | 기술 제약 확정 | - | - |
| 완료기준 | 검증 가능 기준 확정 | - | - |
"""

_TASK_MD_NO_SECTION = """\
# TASK: 테스트 태스크

## 요구사항

내용 없음
"""

_TASK_MD_NA_VALUE = """\
# TASK: 테스트 태스크

## 명확화 결과

| 요소 | 확정값 | 미확정 | 의존 사실 |
|------|--------|--------|----------|
| 목표 | 테스트 목표 확정 | - | - |
| 범위 | N/A: 단일 파일 수정이므로 범위 제한 없음 | - | - |
| 제약 | 기술 제약 확정 | - | - |
| 완료기준 | 검증 가능 기준 확정 | - | - |
"""

_TASK_MD_ONE_MISSING_ELEMENT = """\
# TASK: 테스트 태스크

## 명확화 결과

| 요소 | 확정값 | 미확정 | 의존 사실 |
|------|--------|--------|----------|
| 목표 | 테스트 목표 확정 | - | - |
| 범위 | 포함·제외 확정 | - | - |
| 제약 | 기술 제약 확정 | - | - |
"""




# ═════════════════════════════════════════════════════════════════════════════
# T098 — verify --evidence-check 근거 등급·확정판정 RED 테스트 (PLAN 098 §3.3.2, Step 4)
# ═════════════════════════════════════════════════════════════════════════════





# ═════════════════════════════════════════════════════════════════════════════
# 056: TestOpplSkillInit — state-tool oppl init 실호출 RED-first (S-020, H-1)
# ═════════════════════════════════════════════════════════════════════════════



# ═════════════════════════════════════════════════════════════════════════════
# [T056/ADD2] TestSchemaModeEnumSemiAgentic — schema.json mode enum 드리프트 회귀 방지
# ═════════════════════════════════════════════════════════════════════════════




# ═════════════════════════════════════════════════════════════════════════════
# 070: task-step 키 주소 체계 도입 1차 — RED-first 신규 테스트 9종
# PLAN 070 §3.7.2 클래스 설계 / TEST-SCENARIO 070 S-1~S-14
# [MUST] red-first.md §2/§3: 작성자(opal-test-agent mode:red) ≠ 구현자(op-dev-execute),
# 테스트 불변성(GREEN/fix 루핑 중 이 파일 수정 금지). 아래는 spec-validate/task-step
# 주소/--action-step/add-row --key/opdd enum/그룹 A pipeline.json 등 미구현 기능을
# 검증하므로, GREEN(PLAN §4 Step 1~9) 이전에는 FAIL/ERROR가 정상이다(RED 증거).
# ═════════════════════════════════════════════════════════════════════════════

_SCHEMA_DIR = _TOOL_DIR / "schema"


def _call070(fn, args):
    """cmd_* 함수 직접 호출 → (exit_code, result_dict).
    BaseTestCase._call_cmd와 동일 계약이나, BaseTestCase를 상속하지 않는 신규
    unittest.TestCase 클래스에서도 쓰기 위한 독립 헬퍼(신규 코드, 기존 미변경)."""
    import io
    from contextlib import redirect_stdout
    out = io.StringIO()
    exit_code = 0
    with redirect_stdout(out):
        try:
            fn(args)
        except SystemExit as e:
            exit_code = e.code
    output = out.getvalue().strip()
    result = json.loads(output) if output else {}
    return exit_code, result


def _run070(args_list):
    """run.sh subprocess 실호출 → (returncode, stdout_str, stderr_str, parsed_json).
    [MUST] red-first.md §4: mock/patch 금지 — 공개 인터페이스(stdout/stderr/exit code)만 관찰.
    """
    cmd = ["bash", str(_RUN_SH)] + args_list
    result = subprocess.run(cmd, capture_output=True, text=True)
    stdout = result.stdout.strip()
    try:
        data = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        data = {"_raw": stdout}
    return result.returncode, stdout, result.stderr, data


def _deepcopy_json(obj):
    """표준 라이브러리만(T-11) — json 왕복으로 딥카피(copy 모듈 불요)."""
    return json.loads(json.dumps(obj))


# ── PLAN 070 §3.6.2 그룹 A pipeline.json 스펙 전문(全文) 인용 — RED 임시 픽스처 ─────
# 그룹 A 4종 실파일(opal/skills/opal-pilot-*/references/pipeline.json)은 GREEN(Step 8)
# 에서 생성된다. RED 단계에서는 PLAN 인용 전문을 그대로 임시 파일로 만들어 사용한다.

_OPP_PIPELINE_SPEC = json.loads("""
{
  "spec_version": "1.0",
  "skill": "opp",
  "meta": { "mode_label": "Project Task", "stages": ["TASK", "PLAN", "EXECUTE", "CLOSE"] },
  "task_steps": [
    { "id": 1, "key": "task.task_md",        "stage": "TASK",    "item": "작업" },
    { "id": 2, "key": "task.user_confirm",   "stage": "TASK",    "item": "사용자 확인" },
    { "id": 3, "key": "plan.plan_md",        "stage": "PLAN",    "item": "작업" },
    { "id": 4, "key": "plan.pm_gate",        "stage": "PLAN",    "item": "PM Gate" },
    { "id": 5, "key": "plan.user_confirm",   "stage": "PLAN",    "item": "사용자 확인" },
    { "id": 6, "key": "execute.implement",   "stage": "EXECUTE", "item": "작업" },
    { "id": 7, "key": "execute.pm_gate",     "stage": "EXECUTE", "item": "PM Gate" },
    { "id": 8, "key": "execute.user_confirm","stage": "EXECUTE", "item": "사용자 확인" },
    { "id": 9, "key": "close.done_md",       "stage": "CLOSE",   "item": "DONE.md 생성" }
  ],
  "pm_gate": [
    { "stage": "PLAN",    "artifacts": ["TASK.md", "PLAN.md"], "checklist": ["TASK.md 요구사항", "PLAN.md §3", "PLAN.md §4"] },
    { "stage": "EXECUTE", "artifacts": ["GC-CONVENTION-*.md"], "checklist": ["PLAN.md §3 실행 체크리스트", "컨벤션 자동 진단"] }
  ]
}
""")

_OPD_PIPELINE_SPEC = json.loads("""
{
  "spec_version": "1.0",
  "skill": "opd",
  "meta": { "mode_label": "Full Task", "stages": ["TASK", "ANALYSIS", "PLAN", "TEST-SCENARIO", "EXECUTE", "TEST", "CLOSE"] },
  "task_steps": [
    { "id": 1,  "key": "task.task_md",                 "stage": "TASK",          "item": "작업" },
    { "id": 2,  "key": "task.user_confirm",            "stage": "TASK",          "item": "사용자 확인" },
    { "id": 3,  "key": "analysis.analysis_md",         "stage": "ANALYSIS",      "item": "작업" },
    { "id": 4,  "key": "analysis.pm_gate",             "stage": "ANALYSIS",      "item": "PM Gate" },
    { "id": 5,  "key": "analysis.user_confirm",        "stage": "ANALYSIS",      "item": "사용자 확인" },
    { "id": 6,  "key": "plan.plan_md",                 "stage": "PLAN",          "item": "작업" },
    { "id": 7,  "key": "plan.pm_gate",                 "stage": "PLAN",          "item": "PM Gate" },
    { "id": 8,  "key": "plan.user_confirm",            "stage": "PLAN",          "item": "사용자 확인" },
    { "id": 9,  "key": "test_scenario.test_scenario_md","stage": "TEST-SCENARIO","item": "작업" },
    { "id": 10, "key": "test_scenario.user_confirm",   "stage": "TEST-SCENARIO", "item": "사용자 확인" },
    { "id": 11, "key": "execute.implement",            "stage": "EXECUTE",       "item": "작업" },
    { "id": 12, "key": "test.run_tests",               "stage": "TEST",          "item": "작업" },
    { "id": 13, "key": "test.pm_gate",                 "stage": "TEST",          "item": "PM Gate" },
    { "id": 14, "key": "test.user_confirm",            "stage": "TEST",          "item": "사용자 확인" },
    { "id": 15, "key": "close.done_md",                "stage": "CLOSE",         "item": "DONE.md 생성" }
  ],
  "pm_gate": [
    { "stage": "ANALYSIS",      "artifacts": ["ANALYSIS.md"], "checklist": ["-"] },
    { "stage": "PLAN",          "artifacts": ["TASK.md", "PLAN.md"], "checklist": ["TASK.md 요구사항", "PLAN.md §4.2", "PLAN.md §5", "PLAN.md §리스크 가설 표"] },
    { "stage": "TEST-SCENARIO", "artifacts": ["TEST-SCENARIO.md"], "checklist": ["mock 부재(grep)", "사전 조건 데이터 채워짐", "Given/When/Then 3필드", "가설↔시나리오 매핑 완전", "L1/L2/L3 계층 명시", "L3 [SUPERVISOR] 마커", "실행 방식(M1/M2/M3) 명시"] },
    { "stage": "TEST",          "artifacts": ["TEST-SCENARIO.md", "GC-CONVENTION-*.md"], "checklist": ["시나리오 결과/코드품질/보안/회귀", "컨벤션 자동 진단 PASS"] }
  ]
}
""")

_OPDS_PIPELINE_SPEC = json.loads("""
{
  "spec_version": "1.0",
  "skill": "opds",
  "meta": { "mode_label": "Short Task", "stages": ["TASK", "PLAN", "EXECUTE", "TEST", "CLOSE"] },
  "task_steps": [
    { "id": 1,  "key": "task.task_md",         "stage": "TASK",    "item": "작업" },
    { "id": 2,  "key": "task.user_confirm",    "stage": "TASK",    "item": "사용자 확인" },
    { "id": 3,  "key": "plan.plan_md",         "stage": "PLAN",    "item": "작업" },
    { "id": 4,  "key": "plan.pm_gate",         "stage": "PLAN",    "item": "PM Gate" },
    { "id": 5,  "key": "plan.user_confirm",    "stage": "PLAN",    "item": "사용자 확인" },
    { "id": 6,  "key": "execute.implement",    "stage": "EXECUTE", "item": "작업" },
    { "id": 7,  "key": "test.run_tests",       "stage": "TEST",    "item": "작업" },
    { "id": 8,  "key": "test.pm_gate",         "stage": "TEST",    "item": "PM Gate" },
    { "id": 9,  "key": "test.user_confirm",    "stage": "TEST",    "item": "사용자 확인" },
    { "id": 10, "key": "close.done_md",        "stage": "CLOSE",   "item": "DONE.md 생성" }
  ],
  "pm_gate": [
    { "stage": "PLAN", "artifacts": ["TASK.md", "PLAN.md", "TEST-SCENARIO.md"], "checklist": ["TASK.md 요구사항", "PLAN.md §4.2", "PLAN.md §5", "TEST-SCENARIO.md 시나리오 목록/보안/설계 피드백"] },
    { "stage": "TEST", "artifacts": ["TEST-SCENARIO.md", "GC-CONVENTION-*.md"], "checklist": ["시나리오 결과/코드품질/보안/회귀", "컨벤션 자동 진단 PASS"] }
  ]
}
""")

_OPDW_PIPELINE_SPEC = json.loads("""
{
  "spec_version": "1.0",
  "skill": "opdw",
  "meta": { "mode_label": "Wireframe UI", "stages": ["TASK", "WIREFRAME", "EXECUTE", "CLOSE"] },
  "task_steps": [
    { "id": 1, "key": "task.task_md",           "stage": "TASK",      "item": "작업" },
    { "id": 2, "key": "task.user_confirm",      "stage": "TASK",      "item": "사용자 확인" },
    { "id": 3, "key": "wireframe.wireframe_md",  "stage": "WIREFRAME", "item": "작업",        "conditional": true },
    { "id": 4, "key": "wireframe.pm_gate",       "stage": "WIREFRAME", "item": "PM Gate",     "conditional": true },
    { "id": 5, "key": "wireframe.user_confirm",  "stage": "WIREFRAME", "item": "사용자 확인", "conditional": true },
    { "id": 6, "key": "execute.implement",       "stage": "EXECUTE",   "item": "작업" },
    { "id": 7, "key": "execute.pm_gate",         "stage": "EXECUTE",   "item": "PM Gate" },
    { "id": 8, "key": "execute.user_confirm",    "stage": "EXECUTE",   "item": "사용자 확인" },
    { "id": 9, "key": "close.done_md",           "stage": "CLOSE",     "item": "DONE.md 생성" }
  ],
  "pm_gate": [
    { "stage": "WIREFRAME", "artifacts": ["TASK.md", "wireframe.md"], "checklist": ["TASK.md 요구사항", "wireframe.md 화면 목록", "op-dev-qa 와이어프레임 검증 기준"] },
    { "stage": "EXECUTE",   "artifacts": ["changed_files", "GC-CONVENTION-*.md"], "checklist": ["빌드/린트 결과", "wireframe↔코드 대조", "컨벤션 자동 진단"] }
  ]
}
""")

# (skill, 픽스처 스펙, 픽스처 행 수, 실파일 행 수, 실파일 스킬 디렉토리, 실파일명)
# - 픽스처 행 수: PLAN 070 §3.6.2 전문 인용 시점의 고정값. 실파일이 진화해도 바꾸지 않는다.
# - 실파일 행 수: 현행 pipeline.json 기준. 파이프라인 행 추가/삭제 시 함께 갱신한다.
#   073(opd `test_scenario.scenario_gate`)·075(opds `plan.scenario_gate`) 목표-커버 게이트 행
#   추가로 두 값이 분기했다.
_GROUP_A_SPECS = [
    ("opp",  _OPP_PIPELINE_SPEC,  9,  14, "opal-pilot-project", "pipeline.json"),
    ("opd",  _OPD_PIPELINE_SPEC,  15, 21, "opal-pilot-dev", "pipeline.json"),
    ("opds", _OPDS_PIPELINE_SPEC, 10, 16, "opal-pilot-dev", "pipeline-short.json"),
    ("opdw", _OPDW_PIPELINE_SPEC, 9,  14, "opal-pilot-dev-wireframe", "pipeline.json"),
]


# ═════════════════════════════════════════════════════════════════════════════
# 1. TestPipelineSpecValidate — F-001 spec-validate (TEST-SCENARIO S-7)
# ═════════════════════════════════════════════════════════════════════════════



# ═════════════════════════════════════════════════════════════════════════════
# 2. TestPipelineJsonInit — F-002 json 로딩·key 영속 (TEST-SCENARIO S-1)
# ═════════════════════════════════════════════════════════════════════════════



# ═════════════════════════════════════════════════════════════════════════════
# 3. TestStateSchema11Compat — F-002 state.schema.json 1.1 병행 (TEST-SCENARIO S-4)
# ═════════════════════════════════════════════════════════════════════════════



# ═════════════════════════════════════════════════════════════════════════════
# 4. TestTaskStepAddressing — F-003 3주소·conflict (TEST-SCENARIO S-2,S-3,S-10,S-11,S-13)
# ═════════════════════════════════════════════════════════════════════════════



# ═════════════════════════════════════════════════════════════════════════════
# 5. TestActionStepRename — F-003 --action-step 별칭 (TEST-SCENARIO S-9)
# ═════════════════════════════════════════════════════════════════════════════



# ═════════════════════════════════════════════════════════════════════════════
# 6. TestAddRowKey — F-004 --key 지원·자동 생성 (TEST-SCENARIO S-5, S-6)
# ═════════════════════════════════════════════════════════════════════════════



# ═════════════════════════════════════════════════════════════════════════════
# 7. TestOpddEnumDrift — F-005 opdd 드리프트 정정 (TEST-SCENARIO S-8)
# ═════════════════════════════════════════════════════════════════════════════



# ═════════════════════════════════════════════════════════════════════════════
# 8. TestGroupAPipelineSpecs — F-006 그룹 A 4종 실증 (TEST-SCENARIO S-1)
# ═════════════════════════════════════════════════════════════════════════════



# ═════════════════════════════════════════════════════════════════════════════
# 9. TestBackwardCompatAliases — 전역 --row/--step/.md 회귀 (TEST-SCENARIO S-12)
# ═════════════════════════════════════════════════════════════════════════════



# ═════════════════════════════════════════════════════════════════════════════
# 076: TestTodoMirror — build_todo_mirror 파생 규칙 + ok() 페이로드 + 영속 경계
# (PLAN §3.1.5 TS-001~TS-007). 표준 라이브러리만, 실 파일 I/O + date.js 모킹.
# ═════════════════════════════════════════════════════════════════════════════



# ═════════════════════════════════════════════════════════════════════════════
# 088: TestCloseHistoryLink — CLOSE 마지막 행 mark → 메모리 히스토리 자동 연결
# (PLAN 088 §3 Step 1 TS-1~TS-7 / TASK R-1~R-5).
# [MUST] red-first.md §4: 공개 인터페이스(cmd_mark 호출 + ok() stdout 페이로드 +
#   실 MEMORY.json 파일 내용)로만 검증한다. 내부 함수 mock 금지 — 실패 주입은
#   파일 시스템 레벨 블랙박스 결함 주입으로만 수행한다.
# ═════════════════════════════════════════════════════════════════════════════

# 태스크 폴더명 → title 파생 규칙 검증용 고정 픽스처 (PLAN 088 §2.6)
#   088-260811-opp-테스트-태스크 → "088 테스트 태스크"
_HL_TASK_DIR       = "088-260811-opp-테스트-태스크"
_HL_EXPECTED_TITLE = "088 테스트 태스크"
_HL_EXPECTED_PATH  = f"tasks/{_HL_TASK_DIR}/"
_HL_STAGE_DONE     = "완료"
_HL_RESULT_PLACEHOLDER = "(PM 보강 대기)"

# memory.schema.json 유효 최소 문서 (version/last_task_number/memories/history 필수)
_HL_EMPTY_MEMORY_DOC = {
    "version": 1,
    "last_task_number": 0,
    "memories": [],
    "history": [],
}




# ═════════════════════════════════════════════════════════════════════════════
# T118 RED: TestS9CloseMarkNoImmediateMemoryAppend / TestS10FinalizeAttribution
# (118-260912-opd-워크트리-태스크-소유권-루트분리 TEST-SCENARIO.md S-9/S-10,
#  PLAN D-4/D-4b, AC-4/H-1/C-4).
# [MUST] red-first.md §2/§4: 공개 인터페이스(cmd_mark 직접 호출 + 실 파일 상태,
# 또는 run.sh subprocess stdout/exit code)로만 검증한다. 내부 private 함수·구현
# 결합 검증 금지. 작성자(opal-test-agent red mode, 118 W-EX/RED-B)와 구현자
# (opal-task-agent, PLAN W-4)를 분리한다 — 이 파일은 테스트만 추가하며
# state_tool.py는 건드리지 않는다. GREEN 구현 전까지 아래는 전부 실패해야
# 정상이다(완화·삭제 금지).
# ═════════════════════════════════════════════════════════════════════════════

_S9_TASK_DIR = "118-260912-opd-close-무변경"

_S9_CLOSE_ROWS_SPEC = json.dumps([
    {"stage": "TASK",  "item": "사용자 확인"},
    {"stage": "CLOSE", "item": "DONE.md 생성"},
])




_S10_TASK_DIR = "119-260913-opd-테스트-귀속"
_S10_EXPECTED_TITLE = "119 테스트 귀속"
_S10_EXPECTED_PATH = f"tasks/{_S10_TASK_DIR}/"




# ═════════════════════════════════════════════════════════════════════════════
# 091 F-004: TestTaskStepGate — 게이트 집행 배선 (TEST-SCENARIO S-10~S-17)
# [MUST] red-first.md §2/§4: 작성자(opal-test-agent mode:red) ≠ 구현자(opal-be-agent,
# Step 8). check_gate_artifacts()/build_gate_payload()/_is_safe_artifact_token()은
# 아직 state_tool.py에 없고, build_rows_from_pipeline_json()도 아직 gate를 rows[]로
# 전파하지 않는다(§3.4.2 (5) 1줄 미착수). 따라서 real pipeline.json으로 init해도
# row에 "gate" 키가 실리지 않는다 — 아래 _inject_gate()는 Step 8 GREEN이 만들 결과
# ("전파된 뒤의 row 모습")를 실 pipeline.json의 실제 gate 정의값 그대로 미리
# state.json에 반영하는 fixture 준비 절차다(비mock — 실 JSON 파일 read/write일 뿐,
# state_tool.py의 어떤 함수도 patch하지 않는다). 현재 cmd_mark에는 가드 자체가 없으므로
# artifacts 미충족에도 ok:true가 나오는 것이 RED 증거다.
# ═════════════════════════════════════════════════════════════════════════════



# ═════════════════════════════════════════════════════════════════════════════
# 092(RED-first, mode:red): TestWorktreeFlag 신설 — `state-tool init --worktree <path>`
# TEST-SCENARIO.md S-1(H-1)·S-2(H-1,H-11) — worktree-tool 축 신설의 state-tool 측 계약.
# 작성자(opal-test-agent)≠구현자(EXECUTE 워커) — red-first.md §2. 현재 state_tool.py의
# cmd_init/argparse에는 --worktree 처리가 전혀 없으므로(F-005 GREEN 이전), '지정 시
# 키 존재 + 값이 전달한 절대경로와 문자열 동일'(S-1②, G-3 반영)과 'worktree 키 유무만
# 차이나야 한다'(S-2)는 단언이 실패하는 것이 RED 증거다. 공개 인터페이스(ST.cmd_init/
# ST.cmd_show 직접 호출 + 실 state.json/STATE.md 파일 내용)로만 검증 — 기존 BaseTestCase
# 관행과 동일하게 mock/patch 없음. 기존 테스트 케이스는 일절 수정하지 않았다(파일 끝 append).
# ═════════════════════════════════════════════════════════════════════════════



# ═════════════════════════════════════════════════════════════════════════════
# 094 RED-first 신설 — TestJournalResilience (TEST-SCENARIO.md S-4, S-5, S-30, S-32)
# PLAN §3.1.2 (2)(3) ensure_journal_skeleton/fail-open sync_state_md, §3.5.2
# [MUST] red-first.md §2/§4: 작성자(opal-test-agent mode:red) ≠ 구현자(opal-be-agent),
# 공개 인터페이스(run.sh subprocess, stdout JSON + exit code) + 실 파일 내용으로만
# 검증 — mock/patch/MagicMock 금지. 파일 권한 조작(os.chmod)은 실 환경 조작이므로 허용.
# ═════════════════════════════════════════════════════════════════════════════

def _corrupt_decision_log_table_header(md):
    """094: '## 의사결정 로그' 표 헤더행+구분행만 제거해 손상 저널을 만든다
    (헤딩 텍스트와 본문 나머지는 그대로 보존 — S-30 fixture)."""
    return re.sub(
        r"(## 의사결정 로그\n)\| # \| 시점 \| 결정 \| 근거 \|\n\|[-| ]+\|\n",
        r"\1",
        md,
    )




# ═════════════════════════════════════════════════════════════════════════════
# 094 RED-first 신설 — TestLegacyCoexistence (TEST-SCENARIO.md S-29, S-11)
# PLAN §3.2.2 (4) 함수 생사 판정 / §3.3.2 (1)(2) show 렌더 원천 단일화·배너, D-4
# [MUST] 레거시 원본 tasks/093-*는 절대 직접 조작하지 않는다 — 반드시 tmp_path
# 사본을 조작한다(TASK.md 확정 방향 §4 소급 변경 금지). mock/patch 금지.
# ═════════════════════════════════════════════════════════════════════════════

# TEST-SCENARIO.md §2.1 "레거시 STATE.md" 실 파일 자산 — 메인 저장소 경로(워크트리에는
# tasks/ 디렉토리가 포함되지 않으므로 절대경로로 직접 참조한다).
_LEGACY_093_TASK_DIR = pathlib.Path(
    "/Volumes/Data/AiStudio/workspace/opal/tasks/093-260815-opd-사용자확인행-자동승인-일원화"
)


def _extract_marker_region(md):
    """094: PIPELINE_MARKER_START~END(마커 포함) 구간 원문을 반환. 없으면 None."""
    start = md.find(ST.PIPELINE_MARKER_START)
    end = md.find(ST.PIPELINE_MARKER_END)
    if start == -1 or end == -1:
        return None
    return md[start:end + len(ST.PIPELINE_MARKER_END)]


def _extract_current_status_region(md):
    """094: '## 현재 상태' 섹션(헤딩 + '- ' 라인들) 원문을 반환. 없으면 None."""
    m = re.search(r"## 현재 상태\n(?:- [^\n]+\n){1,6}", md)
    return m.group(0) if m else None




# ═════════════════════════════════════════════════════════════════════════════
# 094 RED-first 신설 — TestShowAsQueryStandard (TEST-SCENARIO.md S-10, S-24, S-25)
# PLAN §3.3.2 (1)(2)(3) cmd_show 3분기 재설계 — 렌더 원천 단일화·배너 극성 반전
# [MUST] mock/patch 금지. 신규 저널(마커 없음) 픽스처는 현재 코드가 마커를 항상
# 생성하므로, init 후 마커 구간을 제거해 "D-1 완전 제거 후" 형태를 모사한다.
# ═════════════════════════════════════════════════════════════════════════════

# 093 (RED-first, mode:red) — 파이프라인 사용자 확인 행 자동 승인 경로 일원화
#   TEST-SCENARIO.md S-1~S-18 / S-24~S-26 (S-19 전체 스위트·S-20~S-22 문서·S-23 L3 제외)
#   PLAN §3 F-001~F-006 시그니처·계약을 그대로 신뢰해 작성한 실패 테스트다.
#
# [MUST] red-first.md §2 작성자≠구현자 — 본 블록은 테스트만 추가하며 state_tool.py를
#        수정하지 않는다. 기존 케이스도 수정·삭제하지 않는다(순수 additive).
# [MUST] red-first.md §4 / 헌법 §4 "Don't fake it" — mock/patch/MagicMock 미사용.
#        worktree run.sh subprocess 실호출 + 실 pipeline.json + 실 state.json 파일
#        내용(공개 인터페이스: exit code / stdout JSON / 파일 상태)으로만 검증한다.
#        시각도 실 date.js를 통과한 실제 KST 값을 쓴다(고정 모킹 없음).
# ═════════════════════════════════════════════════════════════════════════════

_REPO_ROOT_093 = _TOOL_DIR.parent.parent.parent
_SRC_093 = _TOOL_DIR / "state_tool.py"


def _read_state_tool_source():
    """현재 state-tool 소스 텍스트 — state_tool.py 뒤에 state_tool_parts/*.py를 파일명 오름차순으로 잇는다."""
    paths = [_SRC_093, *sorted((_TOOL_DIR / "state_tool_parts").glob("*.py"))]
    return "\n".join(p.read_text(encoding="utf-8") for p in paths)


def _read_head_state_tool_source():
    """HEAD 시점 state-tool 소스 텍스트 — HEAD의 state_tool.py 뒤에 HEAD의 state_tool_parts/*.py를 잇는다."""
    def _show(rel):
        return subprocess.run(["git", "show", f"HEAD:./{rel}"], cwd=str(_TOOL_DIR),
                              capture_output=True, text=True).stdout
    listed = subprocess.run(["git", "ls-tree", "--name-only", "HEAD", "state_tool_parts/"],
                            cwd=str(_TOOL_DIR), capture_output=True, text=True).stdout.split()
    parts = sorted(n for n in listed if n.endswith(".py"))
    return "\n".join([_show("state_tool.py"), *(_show(n) for n in parts)])
_OPD_PIPELINE_093 = (_REPO_ROOT_093 / "opal" / "skills" / "opal-pilot-dev"
                     / "references" / "pipeline.json")


def _t093_json(obj):
    return json.dumps(obj, ensure_ascii=False)


def _t093_pipeline_spec(skill, stages, steps):
    """070/091 pipeline.json 스펙 포맷 픽스처 (validate_pipeline_spec 통과 형태)."""
    return {
        "spec_version": "1.0",
        "skill": skill,
        "meta": {"mode_label": "T093 fixture", "stages": stages},
        "task_steps": steps,
    }


# 경계 불변 회귀표 표 A(B-1~B-9) 공용 픽스처 — PLAN §3.3.2 (3)
_T093_B_SPEC = _t093_json([
    {"stage": "TASK",    "item": "작업"},            # row 1
    {"stage": "TASK",    "item": "사용자 확인"},      # row 2 — MODE_BOUNDARY_STAGES
    {"stage": "EXECUTE", "item": "작업"},            # row 3
    {"stage": "EXECUTE", "item": "사용자 확인"},      # row 4 — 경계 밖 일반 stage
    {"stage": "CLOSE",   "item": "DONE.md 생성"},    # row 5 — CLOSE 첫 행
])

# 경계 불변 회귀표 표 B(V-1~V-9) 공용 픽스처 — CLOSE 첫 행이 사용자 확인 행이 아니게 두어
# check_close_gate와 무관하게 validate 축만 관찰한다.
_T093_V_SPEC = _t093_json([
    {"stage": "TASK",    "item": "사용자 확인"},      # row 1
    {"stage": "EXECUTE", "item": "사용자 확인"},      # row 2
    {"stage": "CLOSE",   "item": "DONE.md 생성"},    # row 3
    {"stage": "CLOSE",   "item": "사용자 확인"},      # row 4
])


class _T093Base(unittest.TestCase):
    """093 공통 베이스 — tmp 작업 폴더 + worktree run.sh subprocess 실호출.

    [MUST] AGENT.md §확정 기준 #2 — tempfile.mkdtemp() 밖(레포/~/.opal)을 쓰지 않는다.
    tmp 경로에는 .opal/MEMORY.json이 없으므로 CLOSE 마지막 행 mark의
    link_memory_history()는 skipped로 무해하게 끝난다(실 메모리 파일 미오염).
    """

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # ── 픽스처 ────────────────────────────────────────────────────────────
    def _task_dir(self, name):
        d = self.tmpdir / name
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _init(self, task_dir, mode, *, rows_spec=None, rows_from=None, skill="opd",
              run_log_mode=None):
        argv = ["init", str(task_dir), "--skill", skill, "--mode", mode]
        if rows_spec is not None:
            argv += ["--rows-spec", rows_spec]
        if rows_from is not None:
            argv += ["--rows-from", str(rows_from)]
        if run_log_mode is not None:
            argv += ["--run-log-mode", run_log_mode]
        code, stdout, stderr, data = _run070(argv)
        self.assertEqual(code, 0, f"init 실패(mode={mode}): {stdout!r} / {stderr!r}")
        return data

    def _init_b(self, mode, name=None):
        d = self._task_dir(name or f"b-{mode}")
        self._init(d, mode, rows_spec=_T093_B_SPEC)
        return d

    # ── 관찰 ──────────────────────────────────────────────────────────────
    def _state_of(self, task_dir):
        return json.loads((task_dir / "state.json").read_text(encoding="utf-8"))

    def _row(self, task_dir, row_id):
        for r in self._state_of(task_dir)["rows"]:
            if r["row_id"] == row_id:
                return r
        self.fail(f"row {row_id} 없음 (task_dir={task_dir})")

    # ── 호출 ──────────────────────────────────────────────────────────────
    def _mark(self, task_dir, row_id, *extra):
        return _run070(["mark", str(task_dir), "--row", str(row_id), "--done", *extra])

    def _mark_key(self, task_dir, key, *extra):
        return _run070(["mark", str(task_dir), "--task-step", key, "--done", *extra])

    def _advance(self, task_dir, row_id, *extra):
        return _run070(["advance", str(task_dir), "--row", str(row_id), *extra])

    def _advance_key(self, task_dir, key, *extra):
        return _run070(["advance", str(task_dir), "--task-step", key, *extra])

    def _validate(self, task_dir):
        return _run070(["validate", str(task_dir)])

    def _assert_ok(self, result, label):
        code, stdout, stderr, data = result
        self.assertEqual(code, 0, f"{label} exit!=0 (stdout={stdout!r} stderr={stderr!r})")
        return data


# ─────────────────────────────────────────────────────────────────────────────
# S-2 / S-3 / S-4 — F-001 auto-na 제거 + 전 모드 pending 초기화
# ─────────────────────────────────────────────────────────────────────────────



# ─────────────────────────────────────────────────────────────────────────────
# S-1 / S-5 / S-13 / S-26 — F-002 자동 승인 훅 (긍정 경로)
# ─────────────────────────────────────────────────────────────────────────────



# ─────────────────────────────────────────────────────────────────────────────
# S-6 / S-7 / S-8 / S-9 / S-12 / S-14 / S-24 — 경계·부정 경로
# ─────────────────────────────────────────────────────────────────────────────



# ─────────────────────────────────────────────────────────────────────────────
# S-10 / S-11 — H-8 훅 × 후속 가드 순서 (파일 오염·응답 오염 배제)
# ─────────────────────────────────────────────────────────────────────────────



# ─────────────────────────────────────────────────────────────────────────────
# S-15 / S-16 — F-005 mark 멱등성
# ─────────────────────────────────────────────────────────────────────────────



# ─────────────────────────────────────────────────────────────────────────────
# S-17 — F-006 (a) 기존 na 보유 실파일 하위호환
# ─────────────────────────────────────────────────────────────────────────────



# ─────────────────────────────────────────────────────────────────────────────
# S-25 — F-003 구조적 단일화 (행동 불변만으로는 복붙 통과)
# ─────────────────────────────────────────────────────────────────────────────



# ═════════════════════════════════════════════════════════════════════════════
# 094 R-11(RED-first, mode:red): agentic 승인 계약 정합
# TestR11ModeBoundary / TestR11CloseGateFallback / TestR11DerivedSignals / TestR11Invariants
# (TEST-SCENARIO.md S-34~S-37, S-40 / R-11-요청서.md §2 G-1~G-3, §7)
#
# [MUST] red-first.md §4 / 헌법 §4 "Don't fake it" — mock/patch/MagicMock 미사용.
#        _T093Base(worktree run.sh subprocess 실호출 + 실 pipeline.json/state.json 파일
#        상태)를 그대로 재사용한다 — 신규 헬퍼 신설 없음(헌법 §2 중복 구현 금지).
#        구현 대상 state_tool.py는 이 RED 단계에서 무변경(작성자≠구현자, 다음 Step이
#        can_auto_approve_user_confirmation() 단일 판정 함수를 재사용해 배선한다).
# ═════════════════════════════════════════════════════════════════════════════

# 실 opdd pipeline.json — G-1 모드 경계 상수 검증 대상(_REPO_ROOT_093 재사용, R-10 무관 —
# 워크트리에도 opal/skills/가 존재하므로 허브 탐색 헬퍼 불요, TASK.md R-10 범위 밖)
_OPDD_REAL_PIPELINE = (_REPO_ROOT_093 / "opal" / "skills" / "opal-pilot-data-design"
                       / "references" / "pipeline.json")




# 실 opgc pipeline.json — G-2 CLOSE 게이트 폴백 검증 대상(확인 행 0개 파이프라인)
_OPGC_REAL_PIPELINE = (_REPO_ROOT_093 / "opal" / "skills" / "opal-pilot-gc"
                       / "references" / "pipeline.json")






def _error_codes_key_set_from_source(source_text):
    """[Step 3-c] state_tool.py 소스 텍스트에서 `ERROR_CODES = {...}` 대입문을 AST로
    찾아 `ast.literal_eval`로 안전하게 평가한 뒤 키 집합만 반환한다(코드 실행 없음).
    대입문을 찾지 못하면 None."""
    tree = ast.parse(source_text)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == "ERROR_CODES" for t in node.targets):
            continue
        value = ast.literal_eval(node.value)
        return set(value.keys())
    return None




# ═════════════════════════════════════════════════════════════════════════════
# 098 ADD-2 RED-first — 배포 경로 루트 파생 결함 (mode:red)
# [MUST] red-first.md §2 작성자≠구현자 — 본 블록은 테스트만 추가하며 state_tool.py를
#        수정하지 않는다(Read 전용). 기존 케이스도 수정·삭제하지 않는다(순수 additive).
# [MUST] 헌법 §4 "Don't fake it" — mock/patch/MagicMock 미사용. 합성 픽스처가 아니라
#        저장소 실파일(본 태스크 TASK.md) + `state_tool.py` 임시 사본 subprocess
#        실행(공개 CLI `verify --evidence-check` stdout JSON)으로만 검증한다.
# ═════════════════════════════════════════════════════════════════════════════



# ═════════════════════════════════════════════════════════════════════════════
# T100 — verify --evidence-check `## 확정된 설계 방향` 승계 파서 RED 테스트
#        (PLAN 100 §3.7.2 / §4.2 Step 10, TS-025~TS-030)
# ═════════════════════════════════════════════════════════════════════════════



# ═════════════════════════════════════════════════════════════════════════════
# 103 R-15 — 워커 소요 계측 필드 (`rows[].worker_duration_minutes`)
# 집계 기준 16/16-a/16-b: 소요를 캡틴/워커/PM 3계열로 분해하려면 워커 실행 시간이
# 행에 남아야 한다. 미기록 행은 축퇴 규칙에 따라 PM 계열로 전액 귀속되므로,
# **필드가 없는 기존 태스크의 수치가 종전과 항등**인 것이 이 블록의 핵심 계약이다.
# [MUST] red-first.md §4 — run.sh subprocess 공개 인터페이스(stdout/exit code)와
#   실 state.json 파일 내용으로만 관찰한다(mock/patch 없음). 기존 케이스 무수정.
# ═════════════════════════════════════════════════════════════════════════════

# TASK→ANALYSIS→EXECUTE 평이한 3행 — '사용자 확인' 행이 없어 자동 승인/CLOSE 게이트
# 축과 무관하게 워커 소요 축만 관찰한다.
_T103_SPEC = _t093_json([
    {"stage": "TASK",     "item": "작업"},              # row 1
    {"stage": "ANALYSIS", "item": "ANALYSIS.md"},       # row 2
    {"stage": "EXECUTE",  "item": "작업"},              # row 3
])

# 인자 미지정 mark 응답의 키 집합 — 6528행 S-13(gate 없는 행)과 동일한 계약.
# 103이 새 키를 무조건 싣지 않는다는 것(H-11)을 이 집합이 고정한다.
_T103_BASELINE_MARK_KEYS = {
    "ok", "command", "row_id", "stage", "item", "status",
    "timestamp", "owner", "auto_approved", "todo_mirror",
}




# ═════════════════════════════════════════════════════════════════════════════
# 103 R-21: 워커 소요 누락 경고 (`mark` stdout `warnings`)
# TestT103WorkerDurationWarning — 발생 / 미발생(오탐 방어) / 억제 3경로
#
# [MUST] 헌법 §4 "Don't fake it" — mock/patch 미사용. _T093Base(run.sh subprocess
#        실호출 + 실 state.json/STATE.md 파일 상태)만 사용한다.
# [MUST] 경고는 에러가 아니다 — exit 0 유지, 산출물 바이트 불변이 계약의 절반이다.
# ═════════════════════════════════════════════════════════════════════════════

# 워커 경로(prior_stage_only)를 태우려면 EXECUTE 행 앞의 TASK/ANALYSIS가 완료여야 한다.
_T103W_SPEC = _t093_json([
    {"stage": "TASK",     "item": "작업"},          # row 1
    {"stage": "ANALYSIS", "item": "ANALYSIS.md"},   # row 2
    {"stage": "EXECUTE",  "item": "Step 1"},        # row 3
    {"stage": "EXECUTE",  "item": "Step 2"},        # row 4
])

_T103W_TS_RE = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}(:\d{2})?")





# ═════════════════════════════════════════════════════════════════════════════
# 진입점
# ═════════════════════════════════════════════════════════════════════════════



# ─────────────────────────────────────────────────────────────────────────────
# 103 강제 2단 — CLOSE 차단 (침묵으로는 통과 못 한다)
# ─────────────────────────────────────────────────────────────────────────────



# ═════════════════════════════════════════════════════════════════════════════
# 106 Step 19 — code-scan 인용 게이트 **동작 케이스** 회귀 고정
#        (Step 15는 ERROR_CODES 종수 단언 6건만 정합시켰고 동작 케이스는 0건이었다.)
# [MUST] 헌법 §4 "Don't fake it" — 가짜 대체물·내부 함수 가로채기 없이 `_T093Base`의
#        run.sh subprocess 실호출 + 실 파일(state.json/STATE.md/PLAN.md/.opal) 상태로만
#        판정한다. 작성자(opal-test-agent)와 구현자(Step 18)는 분리된 주체다.
# ═════════════════════════════════════════════════════════════════════════════

# EXECUTE 행(row 3)의 직전 행을 PLAN으로 두어 005 명확화 훅의 발동 조건
# (직전 행 stage == TASK)에서 벗어나게 한다 — 관찰 축을 code-scan 게이트로 격리한다.
_T106_ROWS_SPEC = _t093_json([
    {"stage": "TASK",    "item": "작업"},            # row 1
    {"stage": "PLAN",    "item": "작업"},            # row 2
    {"stage": "EXECUTE", "item": "작업"},            # row 3 — EXECUTE 첫 행(게이트 발동점)
    {"stage": "CLOSE",   "item": "DONE.md 생성"},    # row 4
])

# 인용 0건 + code-scan 적용 확장자(.py) 대상 → 게이트 ⑦ 판정 대상.
# [MUST] 본문에 `_CODE_SCAN_CITATION_RES` 토큰 9종(domain/layer/depends/exports/
#        write_to/reason/coverage/counts/code-scan)이 단 1건도 없어야 "인용 0건"이다.
_T106_PLAN_CODE_NO_CITATION = (
    "# PLAN\n\n"
    "### 4.2 실행 체크리스트\n\n"
    "**Step 1**\n"
    "- **파일**: opal/tools/state-tool/state_tool.py\n"
)

# §4.2 대상이 `.md`뿐 → 게이트 ⑤ 적용 범위(doc_only_task)에서 조용히 이탈해야 한다.
_T106_PLAN_DOC_ONLY = (
    "# PLAN\n\n"
    "### 4.2 실행 체크리스트\n\n"
    "**Step 1**\n"
    "- **파일**: docs/PROJECT.md\n"
)

# 인용 존재(`code-scan` 토큰) + `.py` 대상 → 게이트 ⑦ 통과.
_T106_PLAN_CODE_WITH_CITATION = (
    "# PLAN\n\n"
    "code-scan 조회 결과를 인용한다.\n\n"
    "### 4.2 실행 체크리스트\n\n"
    "**Step 1**\n"
    "- **파일**: opal/tools/state-tool/state_tool.py\n"
)

_T106_NOTE = "긴급 우회 — 인용 없이 EXECUTE 진입"




# ═════════════════════════════════════════════════════════════════════════════
# 111 — sdlc-v2 TASK/PLAN 계약 검사
# ═════════════════════════════════════════════════════════════════════════════

_T111_TASK_OK = """---
template: sdlc-v2
---
# TASK: 신규 계약

## Problem
P-1. 현재 문서가 길다.

## Proposed outcome
짧은 산출물을 생성한다.

## Affected users and systems
PM, state-tool.

## Constraints
- C-1. 상태는 state.json만 소유한다.

## Acceptance criteria
- AC-1. 신규 TASK가 필수 5절로 통과한다.
"""

_T111_PLAN_OK = """---
template: sdlc-v2
---
# PLAN: 신규 계약

code-scan 조회 결과를 인용한다.

## Work items
| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. TASK 검사 | opal-be-agent | `opal/tools/state-tool/state_tool.py` | 신규 TASK 필수 절 검사 | 없음 | P1 | AC-1, C-1 |
| W-2. 문서 갱신 | opal-task-agent | `opal/tools/state-tool/README.md` | README 갱신 | W-1 | P2 | AC-1 |
"""




# ═════════════════════════════════════════════════════════════════════════════
# 111 W-1 — sdlc-v2 TASK/PLAN 계약 검사 + Work items code-scan 대상 인식
# ═════════════════════════════════════════════════════════════════════════════

_T111_ROWS_SPEC = _t093_json([
    {"stage": "TASK",    "item": "작업"},
    {"stage": "PLAN",    "item": "작업"},
    {"stage": "EXECUTE", "item": "작업"},
    {"stage": "CLOSE",   "item": "DONE.md 생성"},
])

_T111_TASK_V2 = """---
template: sdlc-v2
---
# TASK: fixture

## Problem

현재 계약이 중복된다.

## Proposed outcome

새 문서 계약을 결정론적으로 검증한다.

## Affected users and systems

PM, state-tool.

## Constraints

- C-1: legacy 동작은 유지한다.
- C-2: 검증을 생략하지 않는다.

## Acceptance criteria

- AC-1: TASK 필수 절 누락을 거부한다.
- AC-2: PLAN Work items 계약을 검사한다.
"""

_T111_PLAN_V2 = """---
template: sdlc-v2
---
# PLAN: fixture

code-scan 결과 domain 필드를 확인했다.

## Approach

새 계약을 검사한다.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| D-1 | Work items를 실행 입력으로 둔다. | 분석 근거 |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. TASK 검사 | opal-be-agent | `opal/tools/state-tool/state_tool.py` | sdlc-v2 TASK 필수 절을 검사한다. | 없음 | P1 | AC-1, C-1 |
| W-2. PLAN 검사 | opal-be-agent | `opal/tools/state-tool/tests/test_state_tool.py` | Work items 계약을 검사한다. | W-1 | P2 | AC-2, C-2 |
"""

_T111_PLAN_LEGACY = """# PLAN

### 4.2 실행 체크리스트

**Step 1**
- **파일**: opal/tools/state-tool/state_tool.py
"""




# ═════════════════════════════════════════════════════════════════════════════
# 122(RED-first, mode:red): TestActorFlag 신설 — `state-tool init --actor pm`
# TEST-SCENARIO.md S-1~S-4 (AC-1, AC-4, AC-14, C-3, H-1) — PLAN D-4 "actor는
# state.json 최상위 선택 키이며 미지정 시 키를 생성하지 않는다"의 state-tool 측 계약.
# 작성자(opal-test-agent, mode:red) ≠ 구현자(EXECUTE 워커) — red-first.md §2.
# 현재 state_tool.py의 argparse/cmd_init에는 --actor 처리가 전혀 없으므로(W-2 GREEN
# 이전), 아래 단언들이 실패하는 것이 RED 증거다. 092 TestWorktreeFlag(§`--worktree`
# 조건부 영속화, 동일 구현 패턴 — PLAN D-4 참조)의 구성을 그대로 답습한다: 공개
# 인터페이스(ST.cmd_init 직접 호출 + 실 state.json 파일 내용 + exit code/JSON)로만
# 검증하고 mock/patch는 date.js(_mock_now)에만 한정한다. 기존 테스트는 수정하지
# 않았다(파일 끝 append).
#
# S-1 기준 스냅샷: Task 136 CLOSE tail 반영 소스로
#   `state-tool init --skill opds --mode agentic --rows-from pipeline-short.json`
# 를 실행해 확보한 rows[] 16행을 fixtures/s1_baseline_rows.json에 그대로 보존했다
# (row_id/stage/item/key/status/status_label/timestamp/owner/note/gate — 실행마다
# 달라지는 top-level created_at/updated_at/task_id만 비교에서 제외한다).
# ═════════════════════════════════════════════════════════════════════════════

_OPDS_REAL_PIPELINE_SHORT_JSON = (
    _TOOL_DIR.parent.parent / "skills" / "opal-pilot-dev" / "references" / "pipeline-short.json"
)

_S1_BASELINE_ROWS_FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "s1_baseline_rows.json"



    # ── S-4: 신설 3건 + 기존 전건 회귀 0건은 `python3 -m pytest`(별도 프로세스)로
    #         AGENTIC-LOG/validation에 실제 실행 출력으로 기록한다(이 파일 자체가
    #         "기존 테스트"이므로 자기 자신을 이 클래스 안에서 재실행하지 않는다).


# ─────────────────────────────────────────────────────────────────────────────
# 138 W-9 — state-tool 허브 자동 claim 경계와 actor.session_id 채움
# (연결 AC/C: C-9, D-12, AC-12, AC-13, AC-27)
#
# 판정은 실 파일 상태(owner.json / state.json / run-log 조각)와 CLI 실호출
# 종료 코드·stderr만으로 한다(블랙박스). 내부 mock은 ownership-tool 적재 자체가
# 실패하는 환경(fail-safe 경계)을 재현할 다른 수단이 없는 1건에만 쓴다.
# ─────────────────────────────────────────────────────────────────────────────

_W9_ROWS_SPEC = json.dumps([
    {"stage": "TASK", "item": "작업"},
    {"stage": "PLAN", "item": "작업"},
    {"stage": "EXECUTE", "item": "작업"},
    {"stage": "CLOSE", "item": "State Gate"},
])






# ═════════════════════════════════════════════════════════════════════════════
# T132 — OPPB additive enum 확장 RED (PLAN 132 §Work items W-3 / TEST-SCENARIO S-6)
# ═════════════════════════════════════════════════════════════════════════════
#
# W-3은 `init --skill` choices에 "oppb"를, STAGE_ENUM에 "P0"~"P5"를 추가하는
# RED-first 테스트다. 두 제약 모두 argparse choices 레벨이라 subprocess 실호출로만
# 재현된다(TestOpddEnumDrift(070 R-8)·TestOpplSkillInit(056) 관례와 동일,
# red-first.md §4 — 직접 함수 호출은 argparse 파싱을 우회하므로 이 제약을 재현하지
# 못한다).
#
# S-6 원문은 `--rows-from <oppb pipeline.json>`을 쓰지만, 그 파일은 W-20(P9)
# 산출물이라 이 RED 시점에는 존재하지 않는다. `oppb-runtime-tool/tests/
# test_controller.py`의 MINIMAL_PROJECT_ROWS가 동일한 이유로 쓰는 것과 같은
# 우회를 적용한다 — `--rows-spec` 인라인 P0~P5 최소 행(스테이지당 1행)으로
# 대체한다. 이 클래스는 W-3 구현자와 다른 주체가 작성한 실패 테스트이며
# `state_tool.py`는 수정하지 않는다(harness/red-first.md §1.5-2).
#
# 전 전이는 `run.sh` 공개 CLI(subprocess) 호출로만 수행하고 state.json을 직접
# 편집하지 않는다(.opal/AGENT.md §업무 수행 지침).

_OPPB_P0_P5_ROWS_SPEC = json.dumps([
    {"stage": stage, "item": f"{stage} 프로젝트 단계"}
    for stage in ("P0", "P1", "P2", "P3", "P4", "P5")
])

# 기존 skill 회귀용 — 기존 STAGE_ENUM 값(TASK/ANALYSIS/PLAN/EXECUTE/CLOSE)만
# 사용한다. CLOSE 첫 행 진입은 check_close_gate(§2.16 G-13)가 직전 "사용자 확인"
# 행의 owner=user/status=done을 요구하므로(SAMPLE_ROWS_SPEC/GATE_ROWS_SPEC과
# 동일 관례) EXECUTE 뒤에 확인 행을 명시적으로 둔다.
_EXISTING_SKILL_REGRESSION_ROWS_SPEC = json.dumps([
    {"stage": "TASK",     "item": "작업"},
    {"stage": "ANALYSIS", "item": "분석"},
    {"stage": "PLAN",     "item": "계획"},
    {"stage": "EXECUTE",  "item": "실행"},
    {"stage": "EXECUTE",  "item": "사용자 확인"},
    {"stage": "CLOSE",    "item": "종료"},
])
_EXISTING_SKILL_REGRESSION_STAGES = ["TASK", "ANALYSIS", "PLAN", "EXECUTE", "EXECUTE", "CLOSE"]
_EXISTING_SKILL_REGRESSION_ROW_COUNT = len(_EXISTING_SKILL_REGRESSION_STAGES)
_EXISTING_SKILL_REGRESSION_CONFIRM_ROW_ID = 5  # "사용자 확인" 행 — mark 시 --owner user 필요




# ═════════════════════════════════════════════════════════════════════════════
# T132 W-3 보강 — validate_pipeline_spec() 로컬 skill_enum 누락 RED
# (PM 실측 결함 — state_tool_parts/guards.py:424 skill_enum에 "oppb" 미등록)
# ═════════════════════════════════════════════════════════════════════════════
#
# state_tool.py에는 skill 허용 목록이 두 곳에 있다: ① init --skill argparse
# choices(W-3이 "oppb" 추가, GREEN 완료) ② validate_pipeline_spec() 로컬 상수
# skill_enum(:1247, "oppb" 없음). W-20(P9)이 `oppb pipeline.json`을
# `state-tool init --skill oppb --rows-from`으로 왕복 검증할 때
# build_rows_from_pipeline_json(:1304) → validate_pipeline_spec(:1312)이
# spec_skill_invalid로 막는다. 위 TestT132OppbStageEnumExtension은
# `--rows-spec` 인라인을 써서 이 spec-validate 경로를 타지 않으므로(의도된
# 설계 — W-20 선행 의존 제거, 바꾸지 않음) 이 결함을 잡지 못한다. 이 클래스는
# `spec-validate` 공개 CLI(:2140 cmd_spec_validate → :2147
# validate_pipeline_spec)를 직접 겨냥한다.
#
# 이 클래스는 W-3 구현자와 다른 주체가 작성한 실패 테스트이며 state_tool.py는
# 수정하지 않는다(harness/red-first.md §1.5-2). 위
# TestT132OppbStageEnumExtension의 기존 6건은 건드리지 않는다(§1.5-5, 추가만).

_OPPB_MIN_PIPELINE_SPEC = json.loads("""
{
  "spec_version": "1.0",
  "skill": "oppb",
  "meta": { "mode_label": "Project Build Pilot", "stages": ["P0", "P1", "P2", "P3", "P4", "P5"] },
  "task_steps": [
    { "id": 1, "key": "p0.kickoff",  "stage": "P0", "item": "P0 작업" },
    { "id": 2, "key": "p1.discover", "stage": "P1", "item": "P1 작업" },
    { "id": 3, "key": "p2.design",   "stage": "P2", "item": "P2 작업" },
    { "id": 4, "key": "p3.build",    "stage": "P3", "item": "P3 작업" },
    { "id": 5, "key": "p4.verify",   "stage": "P4", "item": "P4 작업" },
    { "id": 6, "key": "p5.close",    "stage": "P5", "item": "P5 작업" }
  ]
}
""")




# 분리된 테스트 모듈의 기존 전역 참조를 보존한다. 단일 밑줄 helper도 의도적으로 공개한다.
__all__ = [name for name in globals() if not name.startswith("__")]
