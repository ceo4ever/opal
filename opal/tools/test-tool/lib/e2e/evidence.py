"""
@header {
  "module": "evidence",
  "layer": "util",
  "domain": "opal-tools",
  "description": "T05 증적 단일 관문 — 모든 증적 쓰기가 이 모듈을 거치고, 저장 직전 반드시 lib/e2e/redaction.py를 통과한다(CONTRACT.md §A.12). 공통 필수 증적 5종(metadata·server_log·action_log·assertion_evidence·cleanup)의 경로를 소유하고, 마스킹·저장 실패 시 부분 파일을 남기지 않고 EvidenceError를 올려 run을 infra_error로 끝내게 한다.",
  "exports": ["COMMON_REQUIRED_EVIDENCE", "EVIDENCE_PATHS", "EvidenceError", "EvidenceWriter", "canonical_kind"]
}

lib.e2e.evidence — CONTRACT.md §A.12 단일 관문. 산출물은 `$OPAL_E2E_ARTIFACT_DIR`
하위에만 쓴다(TASK.md C-5, §C.6). 저장은 같은 디렉터리의 임시 파일에 쓴 뒤 원자적으로
교체하며, 어느 단계에서 실패하든 임시 파일을 지우고 예외를 올린다 — 원문이나 반쪽
증적이 디스크에 남는 경로를 두지 않는다(TASK.md C-6).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from lib.e2e import redaction as e2e_redaction

# CONTRACT.md §A.1/§A.4/§A.5/§A.6 공통 필수 증적 5종의 정식 이름.
COMMON_REQUIRED_EVIDENCE = (
    "metadata",
    "server_log",
    "action_log",
    "assertion_evidence",
    "cleanup",
)

# 증적 종류 → artifact 상대 경로 고정 매핑(TRD.md TD-10).
EVIDENCE_PATHS: Dict[str, str] = {
    "metadata": "run.json",
    "server_log": "server/backend.log",
    "action_log": "actions.jsonl",
    "assertion_evidence": "assertions.json",
    "cleanup": "cleanup.json",
    "journal": "journal.json",
    "owned": "owned.json",
    "probe": "probe.json",
    "redaction": "redaction.json",
}

# 시나리오가 쓰는 축약 표기를 정식 이름으로 모은다. 시나리오 파일은 동결돼 있으므로
# (test-scenario.json locked) 어휘 차이는 여기서 흡수하고 계약 이름을 하나로 유지한다.
_KIND_ALIASES: Dict[str, str] = {
    "assertions": "assertion_evidence",
    "assertion": "assertion_evidence",
    "actions": "action_log",
    "run_json": "metadata",
    "server_logs": "server_log",
}


def canonical_kind(name: str) -> str:
    """시나리오 표기를 §A.1 정식 증적 이름으로 정규화한다."""
    return _KIND_ALIASES.get(str(name), str(name))


class EvidenceError(Exception):
    """증적 마스킹·저장 실패. run은 전환 없이 `infra_error`로 끝난다(§C.7)."""

    def __init__(self, detail_code: str, detail: str = ""):
        super().__init__(detail or detail_code)
        self.detail_code = detail_code
        self.detail = detail or detail_code


class EvidenceWriter:
    """artifact 디렉터리 1개에 대한 증적 쓰기 관문.

    `observed()`는 실제로 내용을 채운 증적 종류만 돌려준다 — 파일이 존재한다는 사실만으로
    증적을 관측했다고 올리지 않는다(빈 파일로 pass 게이트를 통과시키지 않기 위함).
    """

    def __init__(self, artifact_dir: str, run_id: str):
        self.artifact_dir = Path(artifact_dir)
        self.run_id = run_id
        self._written: List[Path] = []
        self._observed: List[str] = []
        self._redaction_log: List[Dict[str, Any]] = []

    # ── 공개 쓰기 API ────────────────────────────────────────────────────────
    def write_json(self, rel_path: str, payload: Any, *, kind: Optional[str] = None, observed: bool = True) -> str:
        redacted, fields = self._redact(payload, rel_path)
        try:
            text = json.dumps(redacted, ensure_ascii=False, indent=2) + "\n"
        except (TypeError, ValueError) as exc:
            raise EvidenceError("evidence_serialize_failed", f"{rel_path}: {exc}") from exc
        return self._commit(rel_path, text, kind=kind, fields=fields, observed=observed)

    def write_jsonl(self, rel_path: str, rows: Iterable[Any], *, kind: Optional[str] = None, observed: bool = True) -> str:
        lines: List[str] = []
        fields: List[str] = []
        for index, row in enumerate(rows):
            redacted, sub = self._redact(row, f"{rel_path}[{index}]")
            fields.extend(sub)
            try:
                lines.append(json.dumps(redacted, ensure_ascii=False))
            except (TypeError, ValueError) as exc:
                raise EvidenceError("evidence_serialize_failed", f"{rel_path}[{index}]: {exc}") from exc
        text = "".join(line + "\n" for line in lines)
        return self._commit(rel_path, text, kind=kind, fields=fields, observed=observed and bool(lines))

    def write_text(self, rel_path: str, text: Any, *, kind: Optional[str] = None, observed: bool = True) -> str:
        try:
            redacted, fields = e2e_redaction.redact_text(text, path=rel_path)
        except e2e_redaction.RedactionError as exc:
            raise EvidenceError("evidence_redaction_failed", f"{rel_path}: {exc.detail}") from exc
        return self._commit(rel_path, redacted, kind=kind, fields=fields, observed=observed)

    def seal_server_log(self, raw_path: str, *, rel_path: Optional[str] = None) -> Optional[str]:
        """SUT가 직접 쓴 stdout 로그를 읽어 마스킹본으로 교체한다.

        프로세스의 stdout은 실행 중 관문을 거칠 수 없으므로, 회수 직후 같은 경로를
        마스킹본으로 덮어써 **디스크에 남는 증적**은 반드시 관문을 통과하게 한다.
        """
        source = Path(raw_path)
        if not source.is_file():
            return None
        target = rel_path or os.path.relpath(str(source), str(self.artifact_dir))
        try:
            raw = source.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise EvidenceError("evidence_read_failed", f"{target}: {exc}") from exc
        return self.write_text(target, raw, kind="server_log")

    # ── 조회 ─────────────────────────────────────────────────────────────────
    def observed(self, required: Iterable[str] = ()) -> List[str]:
        """관측된 증적 이름 목록. 시나리오가 쓴 표기를 그대로 되돌려준다."""
        canonical = set(self._observed)
        names = set()
        for item in required:
            if canonical_kind(item) in canonical:
                names.add(str(item))
        covered = {canonical_kind(item) for item in required}
        names |= {item for item in canonical if item not in covered}
        return sorted(names)

    def redaction_records(self) -> List[Dict[str, Any]]:
        return list(self._redaction_log)

    def written_paths(self) -> List[str]:
        return [str(path) for path in self._written]

    def purge(self) -> None:
        """이 관문이 쓴 파일을 전부 제거한다 — 실패 run이 부분 증적을 남기지 않게 한다."""
        for path in reversed(self._written):
            try:
                path.unlink()
            except OSError:
                pass
        self._written = []
        self._observed = []

    # ── 내부 ─────────────────────────────────────────────────────────────────
    def _redact(self, payload: Any, rel_path: str):
        try:
            return e2e_redaction.redact_value(payload, path=rel_path)
        except e2e_redaction.RedactionError as exc:
            raise EvidenceError("evidence_redaction_failed", f"{rel_path}: {exc.detail}") from exc

    def _commit(self, rel_path: str, text: str, *, kind: Optional[str], fields: List[str], observed: bool) -> str:
        target = self.artifact_dir / rel_path
        tmp = target.with_name(target.name + ".partial")
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp.write_text(text, encoding="utf-8")
            os.replace(str(tmp), str(target))
        except OSError as exc:
            try:
                tmp.unlink()
            except OSError:
                pass
            raise EvidenceError("evidence_write_failed", f"{rel_path}: {exc}") from exc

        if target not in self._written:
            self._written.append(target)
        self._redaction_log.append(
            e2e_redaction.RedactionResult(
                artifact_path=rel_path,
                redacted_fields=sorted(set(fields)),
                redaction_failed=False,
            ).to_dict()
        )
        if kind and observed:
            canonical = canonical_kind(kind)
            if canonical not in self._observed:
                self._observed.append(canonical)
        return str(target)
