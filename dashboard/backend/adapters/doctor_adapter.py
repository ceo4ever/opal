"""
@header {
  "module": "adapters.doctor_adapter",
  "layer": "service",
  "domain": "console",
  "description": "opal-cli doctor 텍스트 출력 파싱. 4섹션/항목/✓⚠✗ 상태/집계/판정을 구조화 dict로 변환. 파싱 실패 시 graceful 폴백(H-2)",
  "exports": ["parse_doctor_output", "get_doctor"],
  "depends": ["adapters.base"]
}
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from dashboard.backend.adapters.base import ToolError


# opal-cli 경로
OPAL_CLI = str(Path.home() / ".opal" / "tools" / "opal-cli" / "run.sh")

# 섹션 헤더 패턴: [N/4] Section Name
_SECTION_RE = re.compile(r"^\[(\d+)/(\d+)\]\s+(.+)$")

# 항목 패턴: "  ✓/⚠/✗ 내용"
_ITEM_RE = re.compile(r"^\s+([✓⚠✗])\s+(.+)$")

# 판정 패턴: "판정: All Pass (N ✓, N ⚠, N ✗ / 총 N건)"
_VERDICT_RE = re.compile(r"판정:\s*(.+)")

# 집계 패턴: "(N ✓, N ⚠, N ✗"
_COUNTS_RE = re.compile(r"\((\d+)\s*✓[,，]\s*(\d+)\s*⚠[,，]\s*(\d+)\s*✗")

_STATUS_MAP = {"✓": "ok", "⚠": "warn", "✗": "fail"}


def parse_doctor_output(text: str) -> dict:
    """opal-cli doctor 텍스트 출력 → 구조화 dict.

    Returns:
        {
            "sections": [
                {
                    "name": str,
                    "index": int,
                    "items": [{"status": "ok"|"warn"|"fail", "message": str}]
                },
                ...
            ],
            "verdict": str,        # 판정 라인 원문
            "counts": {
                "ok": int,
                "warn": int,
                "fail": int,
                "total": int
            }
        }

    파싱 실패 시 예외 전파 없이 빈 구조 + "warning" 필드 반환 (graceful, H-2).
    """
    try:
        return _parse(text)
    except Exception as exc:
        return {
            "sections": [],
            "verdict": "",
            "counts": {"ok": 0, "warn": 0, "fail": 0, "total": 0},
            "warning": f"doctor 텍스트 파싱 실패: {exc}",
        }


def _parse(text: str) -> dict:
    sections: list[dict] = []
    current_section: dict | None = None
    verdict = ""
    counts: dict[str, int] = {"ok": 0, "warn": 0, "fail": 0, "total": 0}

    for line in text.splitlines():
        # 섹션 헤더
        m = _SECTION_RE.match(line)
        if m:
            current_section = {
                "index": int(m.group(1)),
                "total_sections": int(m.group(2)),
                "name": m.group(3).strip(),
                "items": [],
            }
            sections.append(current_section)
            continue

        # 항목
        m = _ITEM_RE.match(line)
        if m and current_section is not None:
            symbol = m.group(1)
            message = m.group(2).strip()
            status = _STATUS_MAP.get(symbol, "unknown")
            current_section["items"].append({"status": status, "message": message})
            continue

        # 판정 라인
        m = _VERDICT_RE.search(line)
        if m:
            verdict = m.group(1).strip()
            # 집계 파싱
            cm = _COUNTS_RE.search(verdict)
            if cm:
                ok = int(cm.group(1))
                warn = int(cm.group(2))
                fail = int(cm.group(3))
                counts = {
                    "ok": ok,
                    "warn": warn,
                    "fail": fail,
                    "total": ok + warn + fail,
                }

    # 섹션에서 집계가 없으면 항목 수로 재계산
    if counts["total"] == 0 and sections:
        ok = sum(
            1 for s in sections for it in s["items"] if it["status"] == "ok"
        )
        warn = sum(
            1 for s in sections for it in s["items"] if it["status"] == "warn"
        )
        fail = sum(
            1 for s in sections for it in s["items"] if it["status"] == "fail"
        )
        counts = {"ok": ok, "warn": warn, "fail": fail, "total": ok + warn + fail}

    return {
        "sections": sections,
        "verdict": verdict,
        "counts": counts,
    }


def get_doctor() -> dict:
    """opal-cli doctor 실행 → parse_doctor_output 결과 반환.

    Raises:
        ToolError: 실행 실패(타임아웃·exit≠0)
    """
    if not os.path.exists(OPAL_CLI):
        raise ToolError(
            f"opal-cli not found: {OPAL_CLI}",
            kind="exit_error",
            details={"path": OPAL_CLI},
        )

    try:
        proc = subprocess.run(
            ["bash", OPAL_CLI, "doctor"],
            capture_output=True,
            text=True,
            timeout=30.0,
        )
    except subprocess.TimeoutExpired as exc:
        raise ToolError(
            "opal-cli doctor timeout",
            kind="timeout",
            details={"timeout": 30.0},
        ) from exc

    # doctor exit code 1 = fail 있음 (정상 출력 포함) — exit≠0이라도 텍스트 파싱 시도
    output = proc.stdout + proc.stderr
    return parse_doctor_output(output)
