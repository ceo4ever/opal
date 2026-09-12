"""
@header {
  "module": "test_adapters",
  "layer": "test",
  "domain": "console",
  "description": "도구 어댑터 RED-first 테스트 — S-2 시나리오 (L1+L2/M1). 실 도구 호출, mock 대체 금지",
  "exports": ["[T021/L1-R2] test_run_tool_ok", "[T021/L1-R2] test_run_tool_exit_nonzero", "[T021/L1-R2] test_run_tool_timeout", "[T021/L1-R2] test_run_tool_ok_false", "[T021/L1-R2] test_state_adapter_real_tool"],
  "depends": ["adapters.base", "adapters.state_adapter", "adapters.scan_adapter", "adapters.skill_adapter"]
}
"""
import os
import pytest
from pathlib import Path


def _find_repo_task_dir(repo_root: Path, prefix: str) -> Path:
    """109 — 태스크 폴더 위치(`tasks/` 직속 vs `tasks/backup/` 아래)에 내성인
    접두사 탐색. `tasks/{prefix}*`·`tasks/backup/{prefix}*` 2개 글롭(1-depth,
    `rglob` 금지)을 합쳐 정확히 1건일 때만 반환한다. 0건·2건 이상은 skip이 아닌
    실패(AssertionError)로 드러낸다 — 선례: opal/tools/state-tool/tests/test_state_tool.py
    의 동명 모듈 레벨 헬퍼."""
    candidates = sorted((repo_root / "tasks").glob(f"{prefix}*"))
    candidates += sorted((repo_root / "tasks" / "backup").glob(f"{prefix}*"))
    if len(candidates) != 1:
        raise AssertionError(
            f"[FIX-PIN] _find_repo_task_dir(prefix={prefix!r}) 매칭 {len(candidates)}건 "
            f"(정확히 1건 기대). 검색 경로: "
            f"{repo_root / 'tasks' / (prefix + '*')}, "
            f"{repo_root / 'tasks' / 'backup' / (prefix + '*')}. 발견: {candidates}."
        )
    return candidates[0]


# ─── base.py — ToolError 3종 구분 ─────────────────────────────
def test_run_tool_ok() -> None:
    """[T021/L1-R2] 정상 커맨드 → dict 반환"""
    from dashboard.backend.adapters.base import run_tool

    result = run_tool(["echo", '{"ok": true, "value": 42}'])
    # echo 출력은 JSON 파싱 가능한 형태
    assert isinstance(result, (dict, str, list))


def test_run_tool_exit_nonzero() -> None:
    """[T021/L1-R2] exit≠0 → ToolError(kind='exit_error') 발생"""
    from dashboard.backend.adapters.base import run_tool, ToolError

    with pytest.raises(ToolError) as exc_info:
        run_tool(["bash", "-c", "exit 1"])
    assert exc_info.value.kind in ("exit_error",), f"kind={exc_info.value.kind}"


def test_run_tool_timeout() -> None:
    """[T021/L1-R2] timeout 초과 → ToolError(kind='timeout') 발생"""
    from dashboard.backend.adapters.base import run_tool, ToolError

    with pytest.raises(ToolError) as exc_info:
        run_tool(["sleep", "10"], timeout=0.01)
    assert exc_info.value.kind in ("timeout",), f"kind={exc_info.value.kind}"


def test_run_tool_ok_false() -> None:
    """[T021/L1-R2] JSON 응답에 ok:false → ToolError(kind='tool_error') 발생"""
    from dashboard.backend.adapters.base import run_tool, ToolError

    with pytest.raises(ToolError) as exc_info:
        run_tool(["bash", "-c", 'echo \'{"ok":false,"error":"not found"}\''])
    assert exc_info.value.kind in ("tool_error",), f"kind={exc_info.value.kind}"


def test_tool_error_kinds_are_distinct() -> None:
    """[T021/L1-R2] 3종 에러가 서로 다른 kind 값을 가짐"""
    from dashboard.backend.adapters.base import run_tool, ToolError

    kinds: list[str] = []

    # exit_error
    try:
        run_tool(["bash", "-c", "exit 2"])
    except ToolError as e:
        kinds.append(e.kind)

    # timeout
    try:
        run_tool(["sleep", "10"], timeout=0.01)
    except ToolError as e:
        kinds.append(e.kind)

    # tool_error (ok:false)
    try:
        run_tool(["bash", "-c", 'echo \'{"ok":false}\''])
    except ToolError as e:
        kinds.append(e.kind)

    assert len(set(kinds)) == 3, f"3종 kind가 모두 달라야 함: {kinds}"


def test_state_adapter_real_tool() -> None:
    """[T021/L1-R2] 실 state-tool 호출 → dict 반환 (실 도구, mock 금지)"""
    from dashboard.backend.adapters.state_adapter import get_state

    # 118: 자기위치 계산 — 이 테스트가 사는 작업본이 기준 루트다(허브 수렴 없음).
    repo_root = Path(__file__).resolve().parents[3]
    task_dir = str(_find_repo_task_dir(repo_root, "021-"))

    result = get_state(task_dir)
    assert isinstance(result, dict), f"dict 반환 필요: {type(result)}"
    # state-tool show --format json 결과에 ok:true 및 data 포함
    assert result.get("ok") is True or "data" in result or "task_id" in result


def test_skill_adapter_list() -> None:
    """[T021/L1-R2] skill-registry list → 리스트 반환 (실 도구)"""
    from dashboard.backend.adapters.skill_adapter import list_skills

    result = list_skills()
    assert isinstance(result, list), f"list 반환 필요: {type(result)}"
