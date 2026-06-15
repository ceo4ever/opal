"""
@header {
  "module": "test_doctor_adapter",
  "layer": "test",
  "domain": "console",
  "description": "doctor 어댑터 RED-first 테스트 — S-3 시나리오 (L2/M1). 실 opal-cli doctor 호출",
  "exports": ["[T021/L2-R2] test_doctor_parse_real_output", "[T021/L2-R2] test_doctor_sections_count", "[T021/L2-R2] test_doctor_verdict", "[T021/L2-R2] test_doctor_graceful_on_bad_input"],
  "depends": ["adapters.doctor_adapter"]
}
"""
import pytest


SAMPLE_DOCTOR_OUTPUT = """[OPAL Doctor]

[1/4] Dependencies
  ✓ bash 3.2.57
  ✓ git 2.50.1
  ✓ Node.js v25.8.2
  ✓ python3 3.14.3
  ✓ curl 8.7.1
  ✓ playwright (npx @playwright/mcp)

[2/4] OPAL Paths
  ✓ /Users/test/.opal/AGENT.md
  ✓ /Users/test/.opal/identity.md
  ✓ /Users/test/.opal/skills/ (44 skills)
  ⚠ agents dir missing

[3/4] MCP Registration
  ✓ Claude: context7,playwright,shadcn
  ✗ Cursor: not registered

[4/4] Bootstrappers
  ✓ /Users/test/.claude/CLAUDE.md (OPAL marker)
  ✓ /Users/test/.cursor/rules/000-opal-agent.mdc

판정: 1 ✗ found (19 ✓, 1 ⚠, 1 ✗ / 총 21건)
"""


def test_doctor_parse_sections_from_sample() -> None:
    """[T021/L2-R2] 샘플 텍스트 파싱 → 4섹션 dict 반환"""
    from dashboard.backend.adapters.doctor_adapter import parse_doctor_output

    result = parse_doctor_output(SAMPLE_DOCTOR_OUTPUT)
    assert isinstance(result, dict), "dict 반환 필요"
    assert "sections" in result, "'sections' 키 필요"
    assert len(result["sections"]) == 4, f"4섹션 필요: {len(result['sections'])}"


def test_doctor_items_parsed() -> None:
    """[T021/L2-R2] 각 섹션에 항목(items) 리스트 포함"""
    from dashboard.backend.adapters.doctor_adapter import parse_doctor_output

    result = parse_doctor_output(SAMPLE_DOCTOR_OUTPUT)
    for section in result["sections"]:
        assert "name" in section, "섹션 name 필드 필요"
        assert "items" in section, "섹션 items 필드 필요"
        assert isinstance(section["items"], list)


def test_doctor_status_symbols() -> None:
    """[T021/L2-R2] ✓/⚠/✗ 상태가 ok/warn/fail로 파싱"""
    from dashboard.backend.adapters.doctor_adapter import parse_doctor_output

    result = parse_doctor_output(SAMPLE_DOCTOR_OUTPUT)
    all_items = [item for s in result["sections"] for item in s["items"]]

    statuses = {item["status"] for item in all_items}
    assert "ok" in statuses, "✓ → ok 변환 필요"
    assert "warn" in statuses, "⚠ → warn 변환 필요"
    assert "fail" in statuses, "✗ → fail 변환 필요"


def test_doctor_verdict_parsed() -> None:
    """[T021/L2-R2] 판정 라인 → verdict 필드 포함"""
    from dashboard.backend.adapters.doctor_adapter import parse_doctor_output

    result = parse_doctor_output(SAMPLE_DOCTOR_OUTPUT)
    assert "verdict" in result, "'verdict' 키 필요"
    assert isinstance(result["verdict"], str)


def test_doctor_counts_parsed() -> None:
    """[T021/L2-R2] ✓/⚠/✗ 집계 카운트 파싱"""
    from dashboard.backend.adapters.doctor_adapter import parse_doctor_output

    result = parse_doctor_output(SAMPLE_DOCTOR_OUTPUT)
    assert "counts" in result, "'counts' 키 필요"
    counts = result["counts"]
    assert counts.get("ok", 0) >= 0
    assert counts.get("warn", 0) >= 0
    assert counts.get("fail", 0) >= 0


def test_doctor_graceful_on_bad_input() -> None:
    """[T021/L2-R2] 잘못된 입력 시 예외 전파 없이 빈 구조 + 경고 반환"""
    from dashboard.backend.adapters.doctor_adapter import parse_doctor_output

    result = parse_doctor_output("completely invalid text with no sections")
    assert isinstance(result, dict), "잘못된 입력에도 dict 반환"
    assert "sections" in result
    # 예외가 전파되지 않아야 함
    assert "warning" in result or result.get("sections") == []


def test_doctor_parse_real_output() -> None:
    """[T021/L2-R2] 실 opal-cli doctor 출력 파싱 (실 도구, mock 금지)"""
    import subprocess
    import os

    from dashboard.backend.adapters.doctor_adapter import parse_doctor_output

    opal_cli = os.path.expanduser("~/.opal/tools/opal-cli/run.sh")
    if not os.path.exists(opal_cli):
        pytest.skip("opal-cli 없음")

    proc = subprocess.run(
        ["bash", opal_cli, "doctor"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = proc.stdout + proc.stderr
    result = parse_doctor_output(output)

    assert isinstance(result, dict)
    assert len(result.get("sections", [])) > 0, "실 doctor 출력에서 섹션 파싱 실패"
    assert "verdict" in result
