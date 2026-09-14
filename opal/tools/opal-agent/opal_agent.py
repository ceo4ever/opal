#!/usr/bin/env python3
"""
@header {
  "module": "opal_agent",
  "layer": "util",
  "domain": "opal-workspace",
  "description": "멀티 provider 서브에이전트 호출 라이브러리 + CLI, OPAL session event 판정 공개 함수, attempt 실행 원시 기능(process group watchdog·stream terminal framing·attempt 산출물 소유)",
  "exports": ["call_agent", "resolve_session_event", "analyze_stream", "AgentConfig", "AgentResult", "StreamVerdict", "PROVIDERS", "EXIT_CLASSES", "EPILOGUE_ALLOWLIST", "OpalAgentError", "ClaudeNotFoundError", "OpalAgentTimeout"],
  "task": "059, 067, 113, 131"
}

opal/tools/opal-agent/opal_agent.py — 멀티 provider 서브에이전트 호출 라이브러리 + CLI

OPAL 프레임워크의 스킬·오케스트레이터가 여러 LLM CLI(claude / gemini / codex /
grok)를 비대화형(headless) 서브에이전트로 프로그래밍적·CLI로 호출하기 위한
단일 모듈. 무의존성(Python 3.10+ 표준 라이브러리만).

핵심 설계:
  - provider 어댑터 계층 — 공통 API(call_agent) 뒤에 provider별 어댑터가
    build_invocation() / parse_result()를 구현
  - 단발(single-shot) 기본 + session_id로 resume 이어가기(다중 턴)
  - JSON 출력 우선 → provider별 파싱 격리, stream-json 확장 여지 유지
  - 표준 에이전트 구성: prompt · system_prompt · allowed_tools · model · cwd · timeout

지원 provider(공식 CLI 문서 기준, 2026-07 확인):
  claude  claude -p            --append-system-prompt(추가)   --output-format json  --resume
  gemini  gemini -p            GEMINI_SYSTEM_MD env(교체)     --output-format json  --resume
  codex   codex exec           config model_instructions(교체) --json(JSONL)        exec resume <id>
  grok    grok -p (xAI Build)  --system-prompt-override(교체) --output-format json  --resume
  cursor  cursor-agent -p      (플래그 없음 → 프롬프트 접붙임)  --output-format json  --resume
  antigravity  agy -p          (플래그 없음 → 프롬프트 접붙임)  (JSON 없음, text-only)  --conversation

검증 상태:
  - claude/codex/antigravity: 엔드투엔드 실행 검증됨
  - gemini/cursor: 명령 조립 검증(실측 --help). 실행은 인증 필요 → 미검증
  - grok: 공식 문서 기반, CLI 미설치. JSON 세부 스키마 미명시 부분은 방어적 파싱
  - antigravity(agy): text-only 2급 — JSON 없음, session_id·cost 확보 불가,
    출력에 에이전트 chrome 섞일 수 있음(README caveat 참조)

주요 caveat:
  - 시스템 프롬프트 의미: claude만 '추가(append)', 나머지는 '교체(replace)'.
  - codex는 JSONL 스트림 + resume가 별도 서브커맨드(`codex exec resume`)이며,
    resume와 --json 병용에 알려진 이슈가 있다.
  - 부트스트랩 마커 3-way: on(마커 없음) / assistant([ASSISTANT] 첫 줄) /
    off([WORKER] 첫 줄). 최종 session event는 resolve_session_event()가 판정한다.
  - cold session id(new_session_id → claude --session-id)는 claude 전용
    (supports_session_assign). session_id(warm --resume)와 상호 배타 — _run이 검증.

attempt 실행 원시 기능(131):
  - 루트 프로세스를 항상 별도 process group(start_new_session)으로 띄우고,
    stdout read loop와 독립된 monotonic watchdog 스레드가 hard timeout과
    (stream 전용) heartbeat timeout을 감시한다. 만료 시 PGID 전체에
    SIGTERM → terminate_grace_sec → SIGKILL을 보내고, PGID 소멸을 확인한
    뒤에만 timed_out을 확정한다.
  - run_dir·phase(+attempt)가 주어지면 opal-agent가 attempt 산출물의 단일
    writer가 된다. 세 인자가 모두 없으면 기존 stdout passthrough 동작 그대로다.
  - stream 판정은 analyze_stream()이 소유한다 — 마지막 유효 result가 terminal
    candidate이고, 그 앞 result는 같은 session_id + 단조 증가 result_index일
    때만 선행 turn으로 인정한다. 이 도구는 phase 의미론(round·수렴·백로그)을
    모르며, 호출자가 준 timeout·출력 경로·mode만 안다.

"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


# ─── 예외 ────────────────────────────────────────────────────

class OpalAgentError(Exception):
    """opal-agent 공통 예외 베이스.

    ``code``는 호출자가 문자열 매칭 없이 실패 사유를 분기할 수 있게 하는
    안정적 식별자다(예: ``timeout_limit_exceeded``, ``output_format_invalid``).
    """

    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        self.code = code


class ClaudeNotFoundError(OpalAgentError):
    """provider CLI 실행 파일을 PATH에서 찾지 못함."""


class OpalAgentTimeout(OpalAgentError):
    """CLI 실행이 timeout을 초과함."""


# ─── 구성/결과 데이터 구조 ────────────────────────────────────

@dataclass
class AgentConfig:
    """서브에이전트 호출에 전달할 표준 에이전트 구성."""

    prompt: str                                   # 필수 — 에이전트에게 줄 지시
    provider: str = "claude"                      # claude | gemini | codex | grok | cursor | antigravity
    system_prompt: str | None = None              # 역할 부여 (provider별 매핑)
    allowed_tools: list[str] | None = None        # 도구 화이트리스트 (provider별 매핑)
    model: str | None = None                      # 모델명
    effort: str | None = None                     # 추론 강도 (claude/codex/grok만 지원)
    cwd: str | None = None                        # subprocess 작업 디렉토리
    timeout: int = 300                            # 초, 초과 시 OpalAgentTimeout
    session_id: str | None = None                 # resume 이어가기 (warm)
    new_session_id: str | None = None             # cold 세션 지정(caller-supplied). claude만 지원(--session-id). session_id와 상호 배타
    output_format: str = "json"                   # "json" | "text" | "stream-json"
    bin: str | None = None                        # CLI 바이너리 오버라이드 (기본: provider별)
    opal_bootstrap: str = "on"                    # "on"(무마커) | "assistant"([ASSISTANT]) | "off"([WORKER])
    # ── attempt 실행 원시 기능(131) ──
    # run_dir + phase가 함께 주어질 때만 opal-agent가 산출물 writer가 된다.
    # 셋 다 없으면 기존 stdout passthrough 동작이 그대로 유지된다(C-8).
    run_dir: str | None = None                    # attempt 산출물 디렉토리
    phase: str | None = None                      # 산출물 파일명 접두 문자열(의미론은 호출자 소유)
    attempt: str | None = None                    # 재시도 접미 (예: "a2")
    heartbeat_timeout_sec: int | None = None      # stream 전용 — 무출력 허용 상한(D10)
    terminate_grace_sec: int = 5                  # SIGTERM 후 SIGKILL까지 유예
    max_timeout_sec: int | None = None            # 전역 hard timeout 상한
    phase_timeout_limit_sec: int | None = None    # 호출자가 계산한 phase별 상한


@dataclass
class AgentResult:
    """call_agent 반환 값 — 응답 텍스트 + 메타데이터."""

    text: str                                     # 최종 응답 텍스트
    provider: str = "claude"
    session_id: str | None = None                 # resume용 (지원/확보 가능 시)
    is_error: bool = False
    cost_usd: float | None = None                 # 비용(USD) — 제공하는 provider만
    duration_ms: int | None = None
    raw: Any = field(default_factory=dict)        # 원본 출력 (dict 또는 이벤트 목록)


@dataclass
class Invocation:
    """어댑터가 조립한 실제 실행 사양."""

    cmd: list[str]                                # 실행할 인자 배열
    env: dict[str, str] = field(default_factory=dict)   # os.environ에 병합할 오버라이드
    tempfiles: list[str] = field(default_factory=list)  # 실행 후 정리할 임시 파일


# ─── stream terminal framing 판정 ─────────────────────────────

# attempt 종료 분류(D9). 호출자는 이 6종 밖의 값을 받지 않는다.
EXIT_CLASSES = (
    "ok",                       # terminal result가 성공
    "impl_failure",             # 에이전트 구현/실행 실패
    "api_error",                # provider API 측 실패(429 등) — 재시도 대상이 다름
    "timed_out",                # hard/heartbeat timeout으로 회수됨
    "output_format_invalid",    # 확장자와 실제 직렬화 불일치(1행 1객체 위반 포함)
    "framing_error",            # terminal 앞뒤 프레이밍 계약 위반
)

# terminal candidate 뒤에 허용되는 epilogue — `type`이 아니라 `subtype` 기준이다
# (실측 형태: {"type":"system","subtype":"background_tasks_changed"| ...}).
EPILOGUE_ALLOWLIST = (
    "background_tasks_changed",
    "task_updated",
    "task_notification",
)

# 자식 작업이 닫혔다고 인정하는 상태값.
_CHILD_TERMINAL_STATUSES = frozenset(
    {"completed", "killed", "stopped", "failed", "cancelled"}
)


@dataclass
class StreamVerdict:
    """stream-json 전체를 읽어 만든 단일 판정 결과."""

    status: str                                   # "done" | "running" | "error"
    exit_class: str                               # EXIT_CLASSES 중 하나
    terminal: dict | None = None                  # terminal candidate result 이벤트
    cost_used: float | None = None                # terminal candidate의 total_cost_usd(합산 아님, C-10)
    origin: Any = None                            # 진단 전용 — 판정 분기에 쓰지 않는다(D5)
    unterminated_children: list[str] = field(default_factory=list)


def _loads_event(line: str) -> dict | None:
    """JSONL 한 줄을 이벤트 dict로 읽는다. 실패하면 None."""
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        return None
    return event if isinstance(event, dict) else None


def _parse_jsonl(stdout: str) -> tuple[list[dict], bool]:
    """1행 1객체 계약으로 stdout을 읽는다. 반환: (이벤트 목록, 계약 위반 여부).

    한 사건이 여러 물리 행에 걸치면 첫 조각에서 파싱이 깨지므로 위반으로 본다.
    """
    events: list[dict] = []
    for raw in stdout.splitlines():
        line = raw.strip()
        if not line:
            continue
        event = _loads_event(line)
        if event is None:
            return events, True
        events.append(event)
    return events, False


def _is_ascending(earlier: Any, later: Any) -> bool:
    """선행 turn 판정용 단조 증가 검사 — 둘 중 하나라도 없으면 인정하지 않는다."""
    return isinstance(earlier, int) and isinstance(later, int) and earlier < later


def _reduce_children(events: list[dict]) -> list[str]:
    """이벤트를 순서대로 reduce해 stream 종료 시점의 미종료 자식 task를 남긴다.

    중간에 실행 중 task가 있어도 뒤 사건에서 닫히면(빈 task 집합 또는
    completed/killed/stopped) 허용한다(제안서 §7.2-4).
    """
    open_ids: set[str] = set()
    closed: set[str] = set()
    for event in events:
        subtype = event.get("subtype")
        if subtype == "background_tasks_changed":
            listed = {t.get("task_id") for t in event.get("tasks") or []}
            open_ids = {tid for tid in listed if tid not in closed}
        elif subtype in ("task_updated", "task_notification"):
            patch = event.get("patch") or {}
            status = event.get("status") or patch.get("status")
            if status in _CHILD_TERMINAL_STATUSES:
                task_id = event.get("task_id")
                closed.add(task_id)
                open_ids.discard(task_id)
    return sorted(tid for tid in open_ids if tid)


def _classify_terminal(event: dict) -> str:
    """terminal candidate의 terminal_reason·api_error_status로 exit_class를 정한다(D9)."""
    if not event.get("is_error"):
        return "ok"
    if event.get("terminal_reason") == "api_error" or event.get("api_error_status") is not None:
        return "api_error"
    return "impl_failure"


def analyze_stream(stdout: str) -> StreamVerdict:
    """stream-json 출력 전체를 terminal framing 계약으로 판정한다(제안서 §7.2).

    1. 마지막 유효 result가 terminal candidate다 — 마지막 물리 줄이 아니다.
    2. 그 앞 result는 같은 session_id이고 result_index가 단조 증가할 때만
       선행 turn으로 인정한다. 하나라도 깨지면 error다.
    3. candidate 뒤에는 EPILOGUE_ALLOWLIST의 subtype만 허용한다.
    4. epilogue reduce 후 종료 시점 미종료 자식이 0이어야 한다.

    ``origin``은 판정에 쓰지 않고 진단 값으로만 싣는다(D5).
    """
    events, malformed = _parse_jsonl(stdout)
    if malformed:
        return StreamVerdict(status="error", exit_class="output_format_invalid")

    results = [e for e in events if e.get("type") == "result"]
    children = _reduce_children(events)

    # 진단 값 수집 — 분기 조건이 아니라 대입으로만 다룬다(D5).
    diagnostic = None
    for event in results:
        diagnostic = event.get("origin") or diagnostic

    if not results:
        return StreamVerdict(
            status="running", exit_class="ok",
            origin=diagnostic, unterminated_children=children,
        )

    terminal = results[-1]
    terminal_pos = max(i for i, e in enumerate(events) if e.get("type") == "result")
    session = terminal.get("session_id")
    indices = [e.get("result_index") for e in results]

    turns_ok = (
        all(e.get("session_id") == session for e in results)
        and all(_is_ascending(a, b) for a, b in zip(indices, indices[1:]))
    )
    framing_ok = all(
        e.get("type") == "system" and e.get("subtype") in EPILOGUE_ALLOWLIST
        for e in events[terminal_pos + 1:]
    )

    verdict = StreamVerdict(
        status="error", exit_class="framing_error",
        terminal=terminal, cost_used=terminal.get("total_cost_usd"),
        origin=diagnostic, unterminated_children=children,
    )
    if not turns_ok or not framing_ok or children:
        return verdict

    verdict.exit_class = _classify_terminal(terminal)
    verdict.status = "error" if verdict.exit_class != "ok" else "done"
    return verdict


# ─── provider 어댑터 ──────────────────────────────────────────

# opal-agent CLI 옵션 ↔ 첫 줄 마커 어댑터. setting의 bootstrap:off와는 별개다.
_BOOTSTRAP_MARKERS = {"off": "[WORKER]", "assistant": "[ASSISTANT]"}


def resolve_session_event(
    prompt: str,
    bootstrap_enabled: bool,
    project_detected: bool,
) -> str:
    """설정·첫 줄 marker·프로젝트 감지를 표준 session event로 해석한다.

    우선순위는 disabled > worker > assistant > project > general assistant다.
    ``bootstrap_enabled=False``는 설정 게이트가 이미 ``bootstrap: off``를
    확정했다는 뜻이며, marker보다 먼저 순수 ``session.disabled``로 판정한다.
    """
    if not bootstrap_enabled:
        return "session.disabled"

    lines = prompt.splitlines()
    first_line = lines[0] if lines else ""
    if first_line == "[WORKER]":
        return "session.worker"
    if first_line == "[ASSISTANT]":
        return "session.assistant"
    if project_detected:
        return "session.project"
    return "session.assistant"


class ProviderAdapter(ABC):
    """provider별 CLI 인자 조립 + 출력 파싱 인터페이스."""

    name: str = ""
    default_bin: str = ""
    supports_resume: bool = False
    supports_effort: bool = False     # effort(추론 강도) 플래그 지원 여부
    supports_session_assign: bool = False   # cold --session-id(caller-supplied) 지원 여부
    supports_stream: bool = False     # output_format="stream-json" 지원 여부(claude만 True)

    @abstractmethod
    def build_invocation(self, config: AgentConfig, resolved_bin: str) -> Invocation:
        ...

    @abstractmethod
    def parse_result(self, config: AgentConfig, stdout: str) -> AgentResult:
        ...

    # 공통 헬퍼 — 시스템 프롬프트를 임시 .md 파일로 기록(파일 기반 provider용).
    @staticmethod
    def _write_temp_prompt(text: str) -> str:
        fd, path = tempfile.mkstemp(suffix=".md", prefix="opal-agent-sys-")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    # 공통 헬퍼 — opal_bootstrap 값에 따라 프롬프트 첫 줄에 부트스트랩 스킵 마커를
    # 붙인다. OPAL 부트스트랩 게이트가 첫 줄 마커를 보고 스킵 범위를 판단한다.
    # (반드시 최종 프롬프트의 최외곽에 적용 — 마커가 첫 줄이어야 함)
    @staticmethod
    def _mark(prompt: str, config: AgentConfig) -> str:
        marker = _BOOTSTRAP_MARKERS.get(config.opal_bootstrap)   # "on" → None
        return f"{marker}\n{prompt}" if marker else prompt


class ClaudeAdapter(ProviderAdapter):
    """Anthropic Claude Code CLI (`claude -p`)."""

    name = "claude"
    default_bin = "claude"
    supports_resume = True
    supports_effort = True
    supports_session_assign = True
    supports_stream = True

    def build_invocation(self, config: AgentConfig, resolved_bin: str) -> Invocation:
        cmd = [resolved_bin, "-p", self._mark(config.prompt, config),
               "--output-format", config.output_format]
        if config.output_format == "stream-json":
            # --verbose 누락 시 claude CLI가 exit 1(사용법 에러) — 항상 자동 부착(H-2).
            cmd += ["--verbose"]
        if config.model:
            cmd += ["--model", config.model]
        if config.effort:
            # 레벨: low | medium | high | xhigh | max (claude --help 실측)
            cmd += ["--effort", config.effort]
        if config.system_prompt:
            # claude는 기본 시스템 프롬프트에 '추가(append)'한다.
            cmd += ["--append-system-prompt", config.system_prompt]
        if config.allowed_tools:
            cmd += ["--allowedTools", ",".join(config.allowed_tools)]
        if config.new_session_id:
            cmd += ["--session-id", config.new_session_id]    # cold prime
        elif config.session_id:
            cmd += ["--resume", config.session_id]             # warm resume
        return Invocation(cmd=cmd)

    def parse_result(self, config: AgentConfig, stdout: str) -> AgentResult:
        if config.output_format == "text":
            return AgentResult(text=stdout.strip(), provider=self.name)
        if config.output_format == "stream-json":
            data = _terminal_event(analyze_stream(stdout), self.name)
            return AgentResult(
                text=data.get("result", ""),
                provider=self.name,
                session_id=data.get("session_id"),
                is_error=bool(data.get("is_error", False)),
                cost_usd=data.get("total_cost_usd"),
                duration_ms=data.get("duration_ms"),
                raw=data,
            )
        data = _loads(stdout, self.name)
        return AgentResult(
            text=data.get("result", ""),
            provider=self.name,
            session_id=data.get("session_id"),
            is_error=bool(data.get("is_error", False)),
            cost_usd=data.get("total_cost_usd"),
            duration_ms=data.get("duration_ms"),
            raw=data,
        )


class GeminiAdapter(ProviderAdapter):
    """Google Gemini CLI (`gemini -p`)."""

    name = "gemini"
    default_bin = "gemini"
    supports_resume = True

    def build_invocation(self, config: AgentConfig, resolved_bin: str) -> Invocation:
        cmd = [resolved_bin, "-p", self._mark(config.prompt, config),
               "--output-format", config.output_format]
        env: dict[str, str] = {}
        tempfiles: list[str] = []
        if config.model:
            cmd += ["--model", config.model]
        if config.system_prompt:
            # gemini는 전용 플래그가 없다. GEMINI_SYSTEM_MD env로 시스템 프롬프트를
            # '교체(replace)'한다 — 임시 파일에 기록 후 경로를 넘긴다.
            path = self._write_temp_prompt(config.system_prompt)
            tempfiles.append(path)
            env["GEMINI_SYSTEM_MD"] = path
        # 비대화형에서는 도구 승인 프롬프트가 없으므로 자동 승인이 필요하다.
        if config.allowed_tools is not None:
            cmd += ["--approval-mode", "yolo"]
        if config.session_id:
            cmd += ["--resume", config.session_id]
        return Invocation(cmd=cmd, env=env, tempfiles=tempfiles)

    def parse_result(self, config: AgentConfig, stdout: str) -> AgentResult:
        if config.output_format == "text":
            return AgentResult(text=stdout.strip(), provider=self.name)
        data = _loads(stdout, self.name)
        # 공식 스키마: response(텍스트) / stats(토큰·지연) / error(선택).
        # session_id·cost 필드는 문서 미명시 → 방어적으로 None 허용.
        err = data.get("error")
        return AgentResult(
            text=data.get("response", ""),
            provider=self.name,
            session_id=data.get("session_id") or data.get("sessionId"),
            is_error=bool(err),
            cost_usd=None,
            duration_ms=None,
            raw=data,
        )


class CodexAdapter(ProviderAdapter):
    """OpenAI Codex CLI (`codex exec`)."""

    name = "codex"
    default_bin = "codex"
    supports_resume = True
    supports_effort = True

    def build_invocation(self, config: AgentConfig, resolved_bin: str) -> Invocation:
        tempfiles: list[str] = []
        is_resume = bool(config.session_id)
        # resume는 별도 서브커맨드이며 플래그 수용이 다르다(v0.133 확인):
        #   codex exec resume <id> <prompt>  — --sandbox 불가(원 세션에서 상속)
        #   codex exec <prompt>              — --sandbox 지정
        if is_resume:
            cmd = [resolved_bin, "exec", "resume", config.session_id,
                   self._mark(config.prompt, config)]
        else:
            cmd = [resolved_bin, "exec", self._mark(config.prompt, config)]

        if config.model:
            cmd += ["--model", config.model]
        if config.effort:
            # codex는 effort 전용 플래그가 없다 — config 오버라이드로 지정(실측 통과).
            cmd += ["-c", f"model_reasoning_effort={config.effort}"]
        if config.system_prompt:
            # codex는 인라인 시스템 프롬프트 플래그가 없다. config의
            # model_instructions_file(내장 지시 '교체')을 임시 파일로 지정한다.
            path = self._write_temp_prompt(config.system_prompt)
            tempfiles.append(path)
            cmd += ["-c", f"model_instructions_file={path}"]
        # codex exec는 기본이 비대화형(승인 프롬프트 없음)이라 sandbox로만 제어한다.
        # (--ask-for-approval는 대화형 전용 — exec에는 없음)
        if not is_resume:
            cmd += ["--sandbox", "workspace-write"]
        cmd += ["--skip-git-repo-check"]     # git 리포 밖에서도 실행 (양쪽 모두 지원)
        if config.output_format == "json":
            cmd += ["--json"]
        return Invocation(cmd=cmd, tempfiles=tempfiles)

    def parse_result(self, config: AgentConfig, stdout: str) -> AgentResult:
        if config.output_format == "text":
            return AgentResult(text=stdout.strip(), provider=self.name)
        # codex --json은 JSONL(개행 구분 이벤트 스트림)이다.
        events: list[dict[str, Any]] = []
        last_text = ""
        session_id: str | None = None
        usage: Any = None
        is_error = False
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            events.append(obj)
            if isinstance(obj, dict):
                if obj.get("thread_id"):
                    session_id = obj["thread_id"]
                item = obj.get("item")
                if isinstance(item, dict) and item.get("text"):
                    last_text = item["text"]
                elif obj.get("text"):
                    last_text = obj["text"]
                if "usage" in obj:
                    usage = obj["usage"]
                if obj.get("type") in ("turn.failed", "error"):
                    is_error = True
        if not events:
            raise OpalAgentError(
                f"codex --json 출력 파싱 실패(이벤트 없음). 원본: {stdout[:500]}"
            )
        return AgentResult(
            text=last_text,
            provider=self.name,
            session_id=session_id,
            is_error=is_error,
            cost_usd=None,
            duration_ms=None,
            raw={"events": events, "usage": usage},
        )


class GrokAdapter(ProviderAdapter):
    """xAI Grok Build CLI (`grok -p`)."""

    name = "grok"
    default_bin = "grok"
    supports_resume = True
    supports_effort = True

    def build_invocation(self, config: AgentConfig, resolved_bin: str) -> Invocation:
        # grok은 json 대신 plain을 쓴다 — text 요청은 plain으로 매핑.
        fmt = "json" if config.output_format == "json" else "plain"
        cmd = [resolved_bin, "-p", self._mark(config.prompt, config),
               "--output-format", fmt]
        if config.model:
            cmd += ["--model", config.model]
        if config.effort:
            # grok --effort <level> (공식 문서 기준, CLI 미설치로 미검증)
            cmd += ["--effort", config.effort]
        if config.system_prompt:
            # grok은 시스템 프롬프트를 '교체(override)'한다.
            cmd += ["--system-prompt-override", config.system_prompt]
        if config.allowed_tools:
            cmd += ["--tools", ",".join(config.allowed_tools)]
        if config.session_id:
            cmd += ["--resume", config.session_id]
        return Invocation(cmd=cmd)

    def parse_result(self, config: AgentConfig, stdout: str) -> AgentResult:
        if config.output_format == "text":
            return AgentResult(text=stdout.strip(), provider=self.name)
        data = _loads(stdout, self.name)
        # 공식 문서에 JSON 스키마 미명시 → 널리 쓰이는 필드명을 방어적으로 탐색.
        text = (data.get("result") or data.get("response")
                or data.get("text") or data.get("content") or "")
        return AgentResult(
            text=text,
            provider=self.name,
            session_id=(data.get("session_id") or data.get("sessionId")
                        or data.get("session")),
            is_error=bool(data.get("is_error", False)),
            cost_usd=data.get("total_cost_usd") or data.get("cost_usd"),
            duration_ms=data.get("duration_ms"),
            raw=data,
        )


class CursorAdapter(ProviderAdapter):
    """Cursor CLI 에이전트 (`cursor-agent -p`)."""

    name = "cursor"
    default_bin = "cursor-agent"     # 일부 배포는 `agent`로도 노출 — 필요 시 --bin 오버라이드
    supports_resume = True

    def build_invocation(self, config: AgentConfig, resolved_bin: str) -> Invocation:
        # cursor는 시스템 프롬프트 CLI 플래그가 없다(.cursor/rules·AGENTS.md·CLAUDE.md
        # 파일 기반). 임의 경로 주입 수단이 없어, best-effort로 프롬프트 앞에 역할을
        # 접붙인다(진짜 시스템 프롬프트 아님 — README caveat 참조).
        prompt = config.prompt
        if config.system_prompt:
            prompt = f"{config.system_prompt}\n\n---\n\n{config.prompt}"
        prompt = self._mark(prompt, config)     # [WORKER] 마커는 최외곽(첫 줄)
        # -p(--print)는 기본적으로 write·bash 포함 모든 도구 접근을 갖는다.
        cmd = [resolved_bin, "-p", prompt, "--output-format", config.output_format]
        if config.model:
            cmd += ["--model", config.model]
        if config.allowed_tools is not None:
            cmd += ["--force"]     # 명시적 거부 외 명령 자동 승인(비대화형 자동 실행)
        if config.session_id:
            cmd += ["--resume", config.session_id]
        return Invocation(cmd=cmd)

    def parse_result(self, config: AgentConfig, stdout: str) -> AgentResult:
        if config.output_format == "text":
            return AgentResult(text=stdout.strip(), provider=self.name)
        # cursor JSON 스키마는 claude와 유사: result/session_id/is_error/duration_ms.
        # (비용·토큰 필드는 미제공)
        data = _loads(stdout, self.name)
        return AgentResult(
            text=data.get("result", ""),
            provider=self.name,
            session_id=data.get("session_id"),
            is_error=bool(data.get("is_error", False)),
            cost_usd=None,
            duration_ms=data.get("duration_ms"),
            raw=data,
        )


class AntigravityAdapter(ProviderAdapter):
    """
    Google Antigravity CLI (`agy -p`) — 2급(text-only) 어댑터.

    실측(agy v1.1.1) 제약:
      - JSON/구조화 출력 플래그가 없다 → 텍스트만. session_id·cost 확보 불가.
      - resume는 --conversation <ID>인데 ID를 출력에서 얻을 수단이 없다
        (JSON 없음). --continue(최근 대화)만 실질적. session_id 지정 시
        --conversation로 넘기되 자동 캡처는 불가.
      - 출력에 에이전트 chrome(부트스트랩 로그·에이전트명 접두)이 섞일 수 있다.
    """

    name = "antigravity"
    default_bin = "agy"
    supports_resume = True

    def build_invocation(self, config: AgentConfig, resolved_bin: str) -> Invocation:
        # 시스템 프롬프트 전용 플래그가 없어 프롬프트에 접붙인다(best-effort).
        prompt = config.prompt
        if config.system_prompt:
            prompt = f"{config.system_prompt}\n\n---\n\n{config.prompt}"
        prompt = self._mark(prompt, config)     # [WORKER] 마커는 최외곽(첫 줄)
        cmd = [resolved_bin, "-p", prompt,
               # agy 내부 print 타임아웃이 우리 subprocess 타임아웃보다 먼저
               # 끊지 않도록 맞춘다.
               "--print-timeout", f"{config.timeout}s"]
        if config.model:
            cmd += ["--model", config.model]
        if config.allowed_tools is not None:
            cmd += ["--dangerously-skip-permissions"]     # 비대화형 자동 승인
        if config.session_id:
            cmd += ["--conversation", config.session_id]
        return Invocation(cmd=cmd)

    def parse_result(self, config: AgentConfig, stdout: str) -> AgentResult:
        # JSON 출력이 없어 항상 텍스트로 취급. 순수 답변만 분리할 구조적 수단이
        # 없으므로 전체 stdout을 반환한다(에이전트 chrome 포함 가능).
        text = stdout.strip()
        return AgentResult(
            text=text,
            provider=self.name,
            session_id=None,     # 텍스트 출력이라 자동 캡처 불가
            is_error=False,
            cost_usd=None,
            duration_ms=None,
            raw={"text": text, "provider": self.name},
        )


_ADAPTERS: dict[str, ProviderAdapter] = {
    a.name: a for a in (
        ClaudeAdapter(), GeminiAdapter(), CodexAdapter(), GrokAdapter(),
        CursorAdapter(), AntigravityAdapter(),
    )
}
PROVIDERS = tuple(_ADAPTERS.keys())


def _loads(stdout: str, provider: str) -> dict[str, Any]:
    """단일 JSON 객체 파싱(방어적)."""
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise OpalAgentError(
            f"{provider} JSON 출력 파싱 실패: {exc}\n원본: {stdout[:500]}"
        ) from exc
    if not isinstance(data, dict):
        raise OpalAgentError(
            f"{provider} JSON 출력이 객체가 아닙니다: {type(data).__name__}"
        )
    return data


def _terminal_event(verdict: StreamVerdict, provider: str) -> dict[str, Any]:
    """판정 결과에서 terminal candidate를 꺼낸다. 소비할 수 없으면 명시 에러.

    마지막 물리 줄이 아니라 마지막 유효 result를 쓴다(제안서 §7.2-1).
    """
    if verdict.exit_class == "output_format_invalid":
        raise OpalAgentError(
            f"{provider} stream-json이 1행 1객체 직렬화 계약을 위반했습니다.",
            code="output_format_invalid",
        )
    if verdict.terminal is None:
        raise OpalAgentError(
            f"{provider} stream-json 출력에 소비할 result 이벤트가 없습니다.",
            code="framing_error",
        )
    return verdict.terminal


# ─── 공개 API ─────────────────────────────────────────────────

def call_agent(
    prompt: str,
    *,
    provider: str = "claude",
    system_prompt: str | None = None,
    allowed_tools: list[str] | None = None,
    model: str | None = None,
    effort: str | None = None,
    cwd: str | None = None,
    timeout: int = 300,
    session_id: str | None = None,
    new_session_id: str | None = None,
    output_format: str = "json",
    bin: str | None = None,
    opal_bootstrap: str = "on",
    run_dir: str | None = None,
    phase: str | None = None,
    attempt: str | None = None,
    heartbeat_timeout_sec: int | None = None,
    terminate_grace_sec: int = 5,
    max_timeout_sec: int | None = None,
    phase_timeout_limit_sec: int | None = None,
) -> AgentResult:
    """
    지정한 provider CLI를 서브에이전트로 1회 실행하고 결과를 반환한다.

    다중 턴이 필요하면 반환된 AgentResult.session_id를 다음 호출의
    session_id로 넘겨 대화를 이어간다.

    run_dir와 phase를 함께 주면 opal-agent가 attempt 산출물(`<phase>[.aN].*`)의
    단일 writer가 된다. 둘 다 없으면 기존 stdout passthrough 동작 그대로다.

    예외:
      ClaudeNotFoundError — provider CLI 미설치(PATH 부재)
      OpalAgentTimeout    — hard timeout 또는 (stream 전용) heartbeat timeout
      OpalAgentError      — 비정상 종료 / 파싱 실패 / 알 수 없는 provider /
                            timeout_limit_exceeded / output_format_invalid 등

    주의: JSON의 is_error=true는 예외를 던지지 않고 결과에 담아 반환한다.
    """
    if provider not in _ADAPTERS:
        raise OpalAgentError(
            f"알 수 없는 provider: {provider!r}. 지원: {', '.join(PROVIDERS)}"
        )
    config = AgentConfig(
        prompt=prompt,
        provider=provider,
        system_prompt=system_prompt,
        allowed_tools=allowed_tools,
        model=model,
        effort=effort,
        cwd=cwd,
        timeout=timeout,
        session_id=session_id,
        new_session_id=new_session_id,
        output_format=output_format,
        bin=bin,
        opal_bootstrap=opal_bootstrap,
        run_dir=run_dir,
        phase=phase,
        attempt=attempt,
        heartbeat_timeout_sec=heartbeat_timeout_sec,
        terminate_grace_sec=terminate_grace_sec,
        max_timeout_sec=max_timeout_sec,
        phase_timeout_limit_sec=phase_timeout_limit_sec,
    )
    return _run(config)


# ─── process group watchdog · attempt 산출물 소유 ──────────────

_WATCHDOG_TICK_SEC = 0.05
_PGID_REAP_TIMEOUT_SEC = 10.0


def _killpg(pgid: int, sig: int) -> None:
    """process group 전체에 시그널을 보낸다. 이미 소멸했으면 무시한다."""
    try:
        os.killpg(pgid, sig)
    except (ProcessLookupError, PermissionError, OSError):
        pass


def _pgid_alive(pgid: int) -> bool:
    """PGID 생존 여부 — 소멸은 ProcessLookupError로만 확정한다."""
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _await_pgid_gone(pgid: int, timeout: float) -> bool:
    """PGID 소멸을 확인한다. timed_out 확정 전에 반드시 통과해야 한다(제안서 §7.1)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not _pgid_alive(pgid):
            return True
        time.sleep(_WATCHDOG_TICK_SEC)
    return not _pgid_alive(pgid)


class _Watchdog(threading.Thread):
    """stdout read loop와 독립된 monotonic timer.

    줄 도착과 무관하게 tick하므로 무출력 프로세스도 정확한 시점에 만료된다.
    만료 시 PGID 전체에 SIGTERM → terminate_grace_sec → SIGKILL을 보낸다.
    """

    def __init__(
        self, pgid: int, timeout_sec: float,
        heartbeat_timeout_sec: float | None, grace_sec: float,
    ):
        super().__init__(daemon=True)
        self._pgid = pgid
        self._deadline = time.monotonic() + timeout_sec
        self._heartbeat_timeout = heartbeat_timeout_sec
        self._grace = grace_sec
        self._last_beat = time.monotonic()
        self._cancel = threading.Event()
        self._reaped = threading.Event()
        self.reason: str | None = None          # None | "hard" | "heartbeat"
        self.beats = 0
        self.last_beat_at: float | None = None

    def beat(self) -> None:
        """stdout 한 줄이 도착했음을 알린다(stream 전용 heartbeat 갱신)."""
        self._last_beat = time.monotonic()
        self.last_beat_at = time.time()
        self.beats += 1

    def cancel(self) -> None:
        self._cancel.set()

    def mark_reaped(self) -> None:
        """루트 프로세스가 wait()로 회수됐음을 알린다.

        회수 전에는 좀비가 PGID를 살아 있게 만들어 grace 단축 판정이 불가능하다.
        """
        self._reaped.set()

    def run(self) -> None:
        while not self._cancel.wait(_WATCHDOG_TICK_SEC):
            now = time.monotonic()
            if now >= self._deadline:
                self._expire("hard")
                return
            limit = self._heartbeat_timeout
            if limit and now - self._last_beat >= limit:
                self._expire("heartbeat")
                return

    def _expire(self, reason: str) -> None:
        self.reason = reason
        _killpg(self._pgid, signal.SIGTERM)
        # grace는 cancel로 단축하지 않는다 — TERM에 응답하지 않는 손자를 기다린다.
        # 단, 루트 회수 후 PGID가 실제로 비었으면 더 기다리지 않는다.
        deadline = time.monotonic() + self._grace
        while time.monotonic() < deadline:
            if self._reaped.is_set() and not _pgid_alive(self._pgid):
                break
            time.sleep(_WATCHDOG_TICK_SEC)
        _killpg(self._pgid, signal.SIGKILL)


@dataclass
class _AttemptSink:
    """opal-agent가 단일 writer로 소유하는 attempt 산출물 경로 묶음(D1)."""

    directory: pathlib.Path
    stem: str

    def path(self, ext: str) -> pathlib.Path:
        return self.directory / f"{self.stem}.{ext}"


def _attempt_sink(config: AgentConfig) -> _AttemptSink | None:
    """run_dir과 phase가 함께 주어질 때만 writer 소유권을 가진다.

    셋 다 없으면 None을 돌려 기존 stdout passthrough 경로를 그대로 쓴다(C-8).
    `phase`는 파일명 문자열일 뿐이며 opal-agent는 phase 목록도 의미론도 모른다.
    """
    if not config.run_dir or not config.phase:
        return None
    suffix = f".{config.attempt}" if config.attempt else ""
    directory = pathlib.Path(config.run_dir)
    directory.mkdir(parents=True, exist_ok=True)
    return _AttemptSink(directory=directory, stem=f"{config.phase}{suffix}")


def _atomic_write(path: pathlib.Path, text: str) -> None:
    """temp write · fsync · atomic rename으로 파일을 확정한다(제안서 §7.3)."""
    fd, tmp = tempfile.mkstemp(
        dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _enforce_timeout_limits(config: AgentConfig) -> None:
    """요청 timeout이 상한을 넘으면 프로세스를 만들기 전에 거부한다.

    상한값은 호출자가 인자로 전달한다 — opal-agent는 그 값이 어느 phase
    정책에서 왔는지 모른다.
    """
    limits = [
        ("phase_timeout_limit_sec", config.phase_timeout_limit_sec),
        ("max_timeout_sec", config.max_timeout_sec),
    ]
    for name, limit in limits:
        if limit is not None and config.timeout > limit:
            raise OpalAgentError(
                f"timeout_limit_exceeded: 요청 timeout {config.timeout}초가 "
                f"{name}={limit}초를 초과합니다.",
                code="timeout_limit_exceeded",
            )


def _process_group(proc: subprocess.Popen) -> int:
    """start_new_session으로 만든 루트 프로세스의 PGID."""
    try:
        return os.getpgid(proc.pid)
    except OSError:
        return proc.pid


def _fingerprint(config: AgentConfig, inv: Invocation, resolved_bin: str) -> dict:
    """attempt 시작 지문 — 프롬프트 원문 대신 argv 해시를 남긴다."""
    argv = json.dumps(inv.cmd, ensure_ascii=False)
    return {
        "provider": config.provider,
        "bin": resolved_bin,
        "cwd": config.cwd,
        "output_format": config.output_format,
        "argv_len": len(inv.cmd),
        "argv_sha256": hashlib.sha256(argv.encode("utf-8")).hexdigest(),
        "timeout_sec": config.timeout,
        "heartbeat_timeout_sec": config.heartbeat_timeout_sec,
        "terminate_grace_sec": config.terminate_grace_sec,
    }


def _run(config: AgentConfig) -> AgentResult:
    """AgentConfig로 subprocess를 실제 실행한다."""
    adapter = _ADAPTERS[config.provider]

    # cold(new_session_id)·warm(session_id) 상호배타 + 미지원 provider 경고는
    # adapter dispatch(및 shutil.which) 이전, 단일 chokepoint에서 검증한다.
    # 경고 배치가 effort 경고(main()에만 위치)와 비대칭인 이유: cold 드롭은
    # correctness-critical(호출자 registry에 미생성 세션 id가 남아 브레인 재개
    # 실패)이라 라이브러리·CLI 양 표면을 모두 커버해야 한다(§9 R-2).
    if config.new_session_id and config.session_id:
        raise OpalAgentError(
            "new_session_id(cold)와 session_id(warm resume)는 동시 지정할 수 없습니다."
        )
    if config.new_session_id and not adapter.supports_session_assign:
        print(
            f"[opal-agent 경고] provider '{config.provider}'는 caller-supplied "
            f"session id(--session-id)를 지원하지 않아 무시됩니다.",
            file=sys.stderr,
        )

    # stream-json 미지원 provider는 shutil.which(존재 여부)보다 먼저 명시 에러로
    # 차단한다 — 침묵 폴백 금지(H-3, S-3).
    if config.output_format == "stream-json" and not adapter.supports_stream:
        raise OpalAgentError(
            f"provider '{config.provider}'는 stream-json 실행 경로를 지원하지 않습니다."
        )

    # 상한 초과 요청은 프로세스를 만들기 전, 산출물을 만들기 전에 거부한다(S-6).
    _enforce_timeout_limits(config)

    bin_name = config.bin or adapter.default_bin

    resolved = shutil.which(bin_name)
    if resolved is None:
        raise ClaudeNotFoundError(
            f"`{bin_name}` 실행 파일을 PATH에서 찾을 수 없습니다. "
            f"{config.provider} CLI가 설치되어 있는지 확인하세요."
        )

    inv = adapter.build_invocation(config, resolved)
    # opal_bootstrap=off는 호환 CLI 옵션으로 [WORKER] marker를 붙인다.
    # setting bootstrap:off의 session.disabled와는 의미가 다르다.
    env = {**os.environ, **inv.env} if inv.env else None

    sink = _attempt_sink(config)
    try:
        return _execute(config, adapter, inv, env, sink, _fingerprint(config, inv, resolved))
    finally:
        for path in inv.tempfiles:
            try:
                os.unlink(path)
            except OSError:
                pass


def _consume_stream(
    proc: subprocess.Popen, dog: _Watchdog, pgid: int,
    events_handle: Any, passthrough: bool,
) -> tuple[str, bool]:
    """stream stdout을 증분 소비한다. 반환: (원문, 1행 1객체 위반 여부).

    sink가 있으면 events.jsonl에 줄 단위 append+flush로 쓴다 — 실행 중 증분
    관측이 목적이므로 atomic rename을 쓰지 않는다(H-4).
    """
    chunks: list[str] = []
    malformed = False
    for line in proc.stdout:
        dog.beat()
        chunks.append(line)
        if events_handle is not None:
            events_handle.write(line)
            events_handle.flush()
            stripped = line.strip()
            if stripped and _loads_event(stripped) is None:
                malformed = True
                break
        elif passthrough:
            sys.stdout.write(line)
            sys.stdout.flush()
    if malformed:
        _killpg(pgid, signal.SIGTERM)
    return "".join(chunks), malformed


def _execute(
    config: AgentConfig, adapter: ProviderAdapter, inv: Invocation,
    env: dict[str, str] | None, sink: _AttemptSink | None, fingerprint: dict,
) -> AgentResult:
    """두 mode 공통 실행 경로 — spawn → watchdog → 소비 → PGID 회수 → 산출물 확정.

    sink가 None이면 산출물을 만들지 않고 기존 동작(sync 캡처 / stream
    passthrough + stderr 상속)을 그대로 유지한다(C-8).
    """
    streaming = config.output_format == "stream-json"
    err_tmp: str | None = None
    err_handle = None
    events_handle = None

    if sink is not None:
        fd, err_tmp = tempfile.mkstemp(
            dir=str(sink.directory), prefix=f".{sink.stem}.err.", suffix=".tmp"
        )
        err_handle = os.fdopen(fd, "w", encoding="utf-8")
        stderr_target: Any = err_handle
        if streaming:
            events_handle = open(sink.path("events.jsonl"), "a", encoding="utf-8")
    elif streaming:
        stderr_target = None            # 기존 동작 — 호출측 셸 `2>`가 캡처
    else:
        stderr_target = subprocess.PIPE

    started_at = time.time()
    started = time.monotonic()
    # 두 경로 모두 별도 process group으로 띄운다 — 손자까지 회수 가능해야 한다.
    proc = subprocess.Popen(
        inv.cmd,
        stdout=subprocess.PIPE,
        stderr=stderr_target,
        text=True,
        bufsize=1,
        cwd=config.cwd,
        env=env,
        start_new_session=True,
    )
    pgid = _process_group(proc)
    heartbeat_timeout = config.heartbeat_timeout_sec if streaming else None
    dog = _Watchdog(pgid, config.timeout, heartbeat_timeout, config.terminate_grace_sec)
    dog.start()

    stdout_text = ""
    stderr_text = ""
    malformed = False
    try:
        if streaming:
            stdout_text, malformed = _consume_stream(
                proc, dog, pgid, events_handle, passthrough=sink is None
            )
            proc.wait()
        else:
            stdout_text, captured = proc.communicate()
            stderr_text = captured or ""
    finally:
        if proc.poll() is not None:
            dog.mark_reaped()
        dog.cancel()
        dog.join(timeout=config.terminate_grace_sec + _PGID_REAP_TIMEOUT_SEC)
        for handle in (events_handle, err_handle, proc.stdout):
            try:
                if handle is not None:
                    handle.close()
            except OSError:
                pass

    exit_code = proc.returncode
    timed_out = dog.reason is not None
    if timed_out:
        reclaimed = _await_pgid_gone(pgid, _PGID_REAP_TIMEOUT_SEC)
    else:
        reclaimed = not _pgid_alive(pgid)

    verdict: StreamVerdict | None = None
    result: AgentResult | None = None
    failure: OpalAgentError | None = None

    if timed_out:
        status, exit_class = "timed_out", "timed_out"
        failure = OpalAgentTimeout(_timeout_message(config, dog.reason), code="timed_out")
    elif malformed:
        status, exit_class = "error", "output_format_invalid"
        failure = OpalAgentError(
            f"{config.provider} stream-json이 1행 1객체 직렬화 계약을 "
            f"위반했습니다(output_format_invalid).",
            code="output_format_invalid",
        )
    elif exit_code != 0:
        status, exit_class = "error", "impl_failure"
        failure = OpalAgentError(_nonzero_exit_message(config, exit_code, stderr_text))
    else:
        status, exit_class = "done", "ok"
        if streaming:
            verdict = analyze_stream(stdout_text)
            status, exit_class = verdict.status, verdict.exit_class
        try:
            result = adapter.parse_result(config, stdout_text)
        except OpalAgentError as exc:
            status = "error"
            exit_class = exc.code or "framing_error"
            failure = exc

    if sink is not None:
        _finalize_sink(
            sink, config, stdout_text, err_tmp, exit_code,
            _attempt_record(
                config, fingerprint, proc.pid, pgid, started_at, started,
                streaming, dog, heartbeat_timeout, reclaimed, exit_code,
                status, exit_class, verdict,
            ),
        )

    if failure is not None:
        raise failure
    return result


def _timeout_message(config: AgentConfig, reason: str | None) -> str:
    if reason == "heartbeat":
        return (
            f"{config.provider} stream 무출력이 heartbeat "
            f"{config.heartbeat_timeout_sec}초를 초과했습니다."
        )
    if config.output_format == "stream-json":
        return f"{config.provider} stream 실행이 {config.timeout}초를 초과했습니다."
    return f"{config.provider} 실행이 {config.timeout}초를 초과했습니다."


def _nonzero_exit_message(config: AgentConfig, exit_code: int, stderr_text: str) -> str:
    if config.output_format == "stream-json":
        return f"{config.provider} stream 비정상 종료 (exit {exit_code})"
    return (
        f"{config.provider} 비정상 종료 (exit {exit_code})\n"
        f"stderr: {stderr_text.strip()}"
    )


def _attempt_record(
    config: AgentConfig, fingerprint: dict, pid: int, pgid: int,
    started_at: float, started: float, streaming: bool, dog: _Watchdog,
    heartbeat_timeout: int | None, reclaimed: bool, exit_code: int | None,
    status: str, exit_class: str, verdict: StreamVerdict | None,
) -> dict:
    """ledger가 경로로만 외래 참조하는 attempt record(D4)."""
    empty = StreamVerdict(status=status, exit_class=exit_class)
    observed = verdict or empty
    return {
        "phase": config.phase,
        "attempt": config.attempt,
        "mode": "stream" if streaming else "sync",
        "provider": config.provider,
        "status": status,
        "exit_class": exit_class,
        "pid": pid,
        "pgid": pgid,
        "pgid_reclaimed": reclaimed,
        "exit_code": exit_code,
        "timeout_reason": dog.reason,
        "started_at": started_at,
        "ended_at": time.time(),
        "duration_ms": int((time.monotonic() - started) * 1000),
        "fingerprint": fingerprint,
        "heartbeat": {
            "timeout_sec": heartbeat_timeout,
            "count": dog.beats,
            "last_at": dog.last_beat_at,
            "expired": dog.reason == "heartbeat",
        },
        "terminal": observed.terminal,
        "cost_used": observed.cost_used,
        "unterminated_children": observed.unterminated_children,
        "origin": observed.origin,
    }


def _finalize_sink(
    sink: _AttemptSink, config: AgentConfig, stdout_text: str,
    err_tmp: str | None, exit_code: int | None, record: dict,
) -> None:
    """err.log → result.json → exitcode → attempt.json 순으로 확정한다.

    `.exitcode`는 atomic rename이라 프로세스 생존 중에는 나타나지 않는다 —
    관측자는 그 부재를 `running`의 근거로 쓴다(S-23).
    """
    outputs: dict[str, str] = {}

    if err_tmp is not None:
        os.replace(err_tmp, sink.path("err.log"))
        outputs["err"] = str(sink.path("err.log"))

    if config.output_format == "stream-json":
        outputs["events"] = str(sink.path("events.jsonl"))
    elif config.output_format == "json":
        payload = _loads_event(stdout_text.strip())
        if payload is not None:
            _atomic_write(
                sink.path("result.json"),
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            )
            outputs["result"] = str(sink.path("result.json"))

    _atomic_write(sink.path("exitcode"), f"{exit_code}\n")
    outputs["exitcode"] = str(sink.path("exitcode"))

    record["outputs"] = outputs
    _atomic_write(
        sink.path("attempt.json"),
        json.dumps(record, ensure_ascii=False, indent=2, default=str) + "\n",
    )


# ─── CLI 진입점 ───────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="opal-agent",
        description="멀티 provider 서브에이전트 호출 (OPAL)",
    )
    parser.add_argument(
        "prompt", nargs="?",
        help="에이전트에게 줄 프롬프트. 생략 시 stdin에서 읽음.",
    )
    parser.add_argument(
        "--provider", choices=PROVIDERS, default="claude",
        help=f"LLM provider (기본: claude). 지원: {', '.join(PROVIDERS)}",
    )
    parser.add_argument("--system-prompt", help="에이전트 역할 부여")
    parser.add_argument("--model", help="사용할 모델")
    parser.add_argument(
        "--effort",
        help="추론 강도 (claude: low/medium/high/xhigh/max, codex/grok도 지원). "
             "gemini/cursor/antigravity는 미지원(모델명에 내장)",
    )
    parser.add_argument(
        "--allowed-tools",
        help="허용 도구 화이트리스트 (콤마 구분, 예: Bash,Edit,Read)",
    )
    parser.add_argument("--cwd", help="작업 디렉토리")
    parser.add_argument("--timeout", type=int, default=300, help="타임아웃(초), 기본 300")
    # --resume(dest=session_id)와 --session-id(dest=new_session_id)는 상호배타
    # — argparse 그룹으로 CLI 레벨 방어(SSOT는 _run()의 검증, 이건 이중 방어).
    sess = parser.add_mutually_exclusive_group()
    sess.add_argument("--resume", dest="session_id", help="이어갈 session_id (warm resume)")
    sess.add_argument(
        "--session-id", dest="new_session_id",
        help="신규(cold) 세션에 지정할 caller-supplied session id (claude만, 유효 UUID)",
    )
    parser.add_argument("--bin", help="CLI 바이너리 경로 오버라이드")
    # --run-dir + --phase를 함께 주면 opal-agent가 attempt 산출물의 단일 writer가
    # 된다. 셋 다 생략하면 기존 stdout passthrough 동작이 그대로다(C-8).
    parser.add_argument(
        "--run-dir", dest="run_dir",
        help="attempt 산출물 디렉토리. --phase와 함께 줘야 산출물을 소유한다 "
             "(<phase>[.aN].events.jsonl | .result.json | .err.log | .exitcode | .attempt.json)",
    )
    parser.add_argument(
        "--phase", help="산출물 파일명 접두 문자열. opal-agent는 phase 의미론을 모른다.",
    )
    parser.add_argument("--attempt", help="재시도 접미 (예: a2)")
    # watchdog 조절 인자. 상한값은 호출자가 계산해 넘긴다 — opal-agent는 phase별
    # 상한 표를 갖지 않는다. 넷 다 생략하면 기존 동작이 그대로다(C-8).
    parser.add_argument(
        "--heartbeat-timeout-sec", dest="heartbeat_timeout_sec", type=int,
        help="무출력 허용 상한(초). stream mode 전용 — sync에는 적용하지 않는다.",
    )
    parser.add_argument(
        "--terminate-grace-sec", dest="terminate_grace_sec", type=int, default=5,
        help="timeout 회수 시 SIGTERM 후 SIGKILL까지 유예(초, 기본 5)",
    )
    parser.add_argument(
        "--max-timeout-sec", dest="max_timeout_sec", type=int,
        help="전역 hard timeout 상한. --timeout이 넘으면 프로세스를 만들지 않고 거부한다.",
    )
    parser.add_argument(
        "--phase-timeout-limit-sec", dest="phase_timeout_limit_sec", type=int,
        help="호출자가 계산한 phase별 상한. --timeout이 넘으면 프로세스를 만들지 않고 거부한다.",
    )
    parser.add_argument(
        "--opal-bootstrap", choices=("on", "assistant", "off"), default="on",
        help="서브에이전트 OPAL marker (기본 on=무마커). "
             "assistant=[ASSISTANT] 첫 줄 / off=[WORKER] 첫 줄(전역 부트 스킵)",
    )

    fmt = parser.add_mutually_exclusive_group()
    fmt.add_argument(
        "--json", action="store_const", const="json", dest="display",
        help="원본 JSON 전체를 stdout에 출력 (session_id·메타 포함, 스킬 파싱용)",
    )
    fmt.add_argument(
        "--text", action="store_const", const="text", dest="display",
        help="응답 텍스트만 stdout에 출력 (기본, 사람용)",
    )
    fmt.add_argument(
        "--stream", action="store_const", const="stream", dest="display",
        help="stream-json 실행 — claude CLI가 각 줄을 실행 중 stdout에 그대로 "
             "passthrough(파일로 리다이렉트하면 증분 기록). --verbose 자동 부착. "
             "claude 전용(비지원 provider는 명시 에러)",
    )
    parser.set_defaults(display="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    prompt = args.prompt
    if prompt is None:
        prompt = sys.stdin.read()
    if not prompt.strip():
        parser.error("프롬프트가 비어 있습니다 (인자 또는 stdin으로 전달).")

    allowed = (
        [t.strip() for t in args.allowed_tools.split(",") if t.strip()]
        if args.allowed_tools else None
    )

    # effort 미지원 provider에 --effort를 주면 조용히 무시되지 않도록 경고한다.
    if args.effort and not _ADAPTERS[args.provider].supports_effort:
        print(
            f"[opal-agent 경고] provider '{args.provider}'는 --effort를 지원하지 않아 "
            f"무시됩니다. (모델명에 강도를 내장하세요)",
            file=sys.stderr,
        )

    # 라이브러리는 기본 JSON으로 실행해 session_id·메타를 확보한다.
    # display=="stream"만 stream-json 실행 경로(실행 중 passthrough)를 쓴다.
    output_format = "stream-json" if args.display == "stream" else "json"

    try:
        result = call_agent(
            prompt,
            provider=args.provider,
            system_prompt=args.system_prompt,
            allowed_tools=allowed,
            model=args.model,
            effort=args.effort,
            cwd=args.cwd,
            timeout=args.timeout,
            session_id=args.session_id,
            new_session_id=args.new_session_id,
            output_format=output_format,
            bin=args.bin,
            opal_bootstrap=args.opal_bootstrap,
            run_dir=args.run_dir,
            phase=args.phase,
            attempt=args.attempt,
            heartbeat_timeout_sec=args.heartbeat_timeout_sec,
            terminate_grace_sec=args.terminate_grace_sec,
            max_timeout_sec=args.max_timeout_sec,
            phase_timeout_limit_sec=args.phase_timeout_limit_sec,
        )
    except OpalAgentError as exc:
        print(f"[opal-agent 오류] {exc}", file=sys.stderr)
        return 2

    if args.display == "json":
        json.dump(result.raw, sys.stdout, ensure_ascii=False, indent=2, default=str)
        sys.stdout.write("\n")
    elif args.display == "stream":
        pass    # 실행 중 passthrough로 이미 출력 완료 — 별도 dump 없음
    else:
        print(result.text)

    return 1 if result.is_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
