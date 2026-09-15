"""
@header {
  "module": "redaction",
  "layer": "util",
  "domain": "opal-tools",
  "description": "T05 증적 마스킹 — Authorization·Cookie·Set-Cookie 헤더와 URL query 비밀값을 저장 직전에 마스킹하고 §A.12 redaction 결과(artifact_path·redacted_fields·redaction_failed)를 반환한다. 저장 자체는 하지 않는다 — 호출자는 lib/e2e/evidence.py 단일 관문뿐이다.",
  "exports": ["MASK", "RedactionError", "RedactionResult", "redact_headers", "redact_url", "redact_text", "redact_value"]
}

lib.e2e.redaction — CONTRACT.md §A.12 대상 정의(`Authorization`·`Cookie`·`Set-Cookie`
헤더, URL query 비밀값, HAR 포함)의 순수 변환 층이다. 이 모듈은 파일을 쓰지 않고
디렉터리를 만들지 않는다. 마스킹 실패는 예외(`RedactionError`)로만 알리며 원문을
반환하는 폴백을 두지 않는다 — TASK.md C-6 "실패 시 원문을 남기지 않고 infra_error".
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Tuple

# 마스킹 치환 문자열. 원문 길이를 암시하지 않도록 고정 폭을 쓰지 않는다.
MASK = "[REDACTED]"

# CONTRACT.md §A.12 "대상" — 헤더 이름은 대소문자를 구분하지 않는다.
SECRET_HEADER_NAMES = frozenset(
    {
        "authorization",
        "proxy-authorization",
        "cookie",
        "set-cookie",
        "x-api-key",
        "x-auth-token",
    }
)

# URL query·폼 필드 중 비밀값으로 간주하는 키. 값 판정을 내용 추정이 아니라 키 이름
# 목록으로 고정한다 — 추정 마스킹은 재현 불가능한 증적을 만든다.
SECRET_QUERY_KEYS = frozenset(
    {
        "api_key",
        "apikey",
        "access_token",
        "refresh_token",
        "id_token",
        "token",
        "secret",
        "client_secret",
        "password",
        "passwd",
        "pwd",
        "sig",
        "signature",
        "session",
        "sessionid",
        "sid",
        "auth",
        "key",
    }
)

_QUERY_PATTERN = re.compile(
    r"(?i)(?P<sep>[?&;]|\A)(?P<key>" + "|".join(sorted(SECRET_QUERY_KEYS)) + r")=(?P<value>[^&\s;\"']*)"
)

_HEADER_LINE_PATTERN = re.compile(
    r"(?im)^(?P<indent>[ \t>]*)(?P<name>" + "|".join(sorted(SECRET_HEADER_NAMES)) + r")(?P<sep>\s*:\s*)(?P<value>.*)$"
)

_JSON_FIELD_PATTERN = re.compile(
    r"(?i)(?P<key>\"(?:" + "|".join(sorted(SECRET_HEADER_NAMES)) + r")\"\s*:\s*)\"(?P<value>[^\"]*)\""
)

_BEARER_PATTERN = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/\-]+=*")


class RedactionError(Exception):
    """마스킹을 끝까지 수행하지 못했다. 호출자는 원문을 저장하지 않고 중단한다."""

    def __init__(self, detail_code: str, detail: str = ""):
        super().__init__(detail or detail_code)
        self.detail_code = detail_code
        self.detail = detail or detail_code


@dataclass
class RedactionResult:
    """CONTRACT.md §A.12 redaction 결과 레코드."""

    artifact_path: str
    redacted_fields: List[str] = field(default_factory=list)
    redaction_failed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_path": self.artifact_path,
            "redacted_fields": sorted(set(self.redacted_fields)),
            "redaction_failed": self.redaction_failed,
        }


def is_secret_header(name: Any) -> bool:
    return isinstance(name, str) and name.strip().lower() in SECRET_HEADER_NAMES


def redact_headers(headers: Mapping[str, Any], *, path: str = "headers") -> Tuple[Dict[str, Any], List[str]]:
    """헤더 매핑의 비밀 헤더 값을 MASK로 치환한다. 키는 원문 그대로 남긴다."""
    if not isinstance(headers, Mapping):
        raise RedactionError("redaction_input_invalid", f"{path} is not a mapping: {type(headers).__name__}")
    out: Dict[str, Any] = {}
    touched: List[str] = []
    for key, value in headers.items():
        if is_secret_header(key):
            out[key] = MASK
            touched.append(f"{path}.{key}")
            continue
        redacted_value, sub = redact_value(value, path=f"{path}.{key}")
        out[key] = redacted_value
        touched.extend(sub)
    return out, touched


def redact_url(url: Any, *, path: str = "url") -> Tuple[Any, List[str]]:
    """URL query의 비밀 키 값을 MASK로 치환한다."""
    if url is None:
        return None, []
    if not isinstance(url, str):
        raise RedactionError("redaction_input_invalid", f"{path} is not a string: {type(url).__name__}")
    touched: List[str] = []

    def _sub(match: "re.Match[str]") -> str:
        if not match.group("value"):
            return match.group(0)
        touched.append(f"{path}?{match.group('key')}")
        return f"{match.group('sep')}{match.group('key')}={MASK}"

    return _QUERY_PATTERN.sub(_sub, url), touched


def redact_text(text: Any, *, path: str = "text") -> Tuple[str, List[str]]:
    """로그·HAR·스냅샷 등 자유 텍스트에서 비밀 헤더 줄과 query 비밀값을 마스킹한다."""
    if text is None:
        return "", []
    if not isinstance(text, str):
        raise RedactionError("redaction_input_invalid", f"{path} is not a string: {type(text).__name__}")
    touched: List[str] = []

    def _header_sub(match: "re.Match[str]") -> str:
        if not match.group("value").strip():
            return match.group(0)
        touched.append(f"{path}:{match.group('name').lower()}")
        return f"{match.group('indent')}{match.group('name')}{match.group('sep')}{MASK}"

    def _json_sub(match: "re.Match[str]") -> str:
        touched.append(f"{path}:{match.group('key')}")
        return f'{match.group("key")}"{MASK}"'

    def _query_sub(match: "re.Match[str]") -> str:
        if not match.group("value"):
            return match.group(0)
        touched.append(f"{path}?{match.group('key')}")
        return f"{match.group('sep')}{match.group('key')}={MASK}"

    def _bearer_sub(match: "re.Match[str]") -> str:
        touched.append(f"{path}:bearer")
        return f"Bearer {MASK}"

    redacted = _JSON_FIELD_PATTERN.sub(_json_sub, text)
    redacted = _HEADER_LINE_PATTERN.sub(_header_sub, redacted)
    redacted = _QUERY_PATTERN.sub(_query_sub, redacted)
    redacted = _BEARER_PATTERN.sub(_bearer_sub, redacted)
    return redacted, touched


def redact_value(value: Any, *, path: str = "$") -> Tuple[Any, List[str]]:
    """임의 JSON 값을 재귀 마스킹한다.

    - 비밀 헤더 이름과 같은 key는 값 전체를 MASK로 바꾼다(중첩 깊이 무관).
    - `url`·`href`·`location` key의 문자열 값은 query 마스킹을 적용한다.
    - 그 밖의 문자열은 `redact_text`와 같은 패턴 마스킹을 적용한다.
    """
    if isinstance(value, Mapping):
        out: Dict[Any, Any] = {}
        touched: List[str] = []
        for key, item in value.items():
            child_path = f"{path}.{key}"
            if is_secret_header(key):
                out[key] = MASK
                touched.append(child_path)
                continue
            if isinstance(key, str) and key.strip().lower() in {"url", "href", "location", "request_url"}:
                redacted, sub = redact_url(item, path=child_path) if isinstance(item, str) else redact_value(item, path=child_path)
                out[key] = redacted
                touched.extend(sub)
                continue
            if isinstance(key, str) and key.strip().lower() in SECRET_QUERY_KEYS and not isinstance(item, (Mapping, list, tuple)):
                out[key] = MASK
                touched.append(child_path)
                continue
            redacted, sub = redact_value(item, path=child_path)
            out[key] = redacted
            touched.extend(sub)
        return out, touched
    if isinstance(value, (list, tuple)):
        out_list: List[Any] = []
        touched = []
        for index, item in enumerate(value):
            redacted, sub = redact_value(item, path=f"{path}[{index}]")
            out_list.append(redacted)
            touched.extend(sub)
        return out_list, touched
    if isinstance(value, str):
        return redact_text(value, path=path)
    if isinstance(value, (int, float, bool)) or value is None:
        return value, []
    # 직렬화 가능성을 보장하지 못하는 값은 저장 전에 막는다 — 조용히 str()로 흘리면
    # 마스킹되지 않은 repr이 증적에 남을 수 있다.
    raise RedactionError("redaction_unsupported_type", f"{path} has unsupported type {type(value).__name__}")
