#!/usr/bin/env python3
"""
@header {
  "module": "opal_agent",
  "layer": "util",
  "domain": "opal-workspace",
  "description": "멀티 provider 서브에이전트 호출 라이브러리 + CLI, OPAL session event 판정 공개 함수, 공용 attempt runtime(process group 생성·독립 watchdog·PGID 회수·attempt record·재부착/고아 판정)",
  "exports": ["call_agent", "resolve_session_event", "AgentConfig", "AgentResult", "PROVIDERS", "OpalAgentError", "ClaudeNotFoundError", "OpalAgentTimeout", "AttemptRecorder", "attempt_run_root", "load_attempt_records", "classify_attempt", "reconcile_attempts", "STREAM_EPILOGUE_ALLOWLIST", "RUN_ROOT_ENV"],
  "task": "059, 067, 113, 132"
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
  - 공용 attempt runtime — 자식을 새 process group 리더로 띄우고(start_new_session),
    stdout 수신과 분리된 독립 watchdog이 deadline을 집행하며 PGID 전체를 회수한다.
    `OPAL_AGENT_RUN_ROOT`가 주어지면 attempt record를 원자 저장하고,
    reconcile_attempts()가 재시작 시 재부착/고아 판정 진입점을 제공한다.

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

"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


# ─── 예외 ────────────────────────────────────────────────────

class OpalAgentError(Exception):
    """opal-agent 공통 예외 베이스."""


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
            data = _last_stream_result(stdout, self.name)
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


# stream terminal framing — result 이벤트 뒤에 와도 "작업이 끝났음"을 뒤집지 않는
# 후행(epilogue) 이벤트 allowlist. 이 집합 밖의 이벤트가 마지막 result 뒤에 남으면
# 미종료 작업이 있다는 뜻이므로 성공으로 판정하지 않는다(S-3).
STREAM_EPILOGUE_ALLOWLIST: frozenset[str] = frozenset({
    "background_tasks_changed",
    "task_updated",
})


def _last_stream_result(stdout: str, provider: str) -> dict[str, Any]:
    """stream-json(JSONL) 출력에서 **마지막 result 이벤트**를 채택한다.

    terminal framing 규칙(S-3):
      1. result 이벤트가 여러 번 오면 마지막 것만 채택한다.
      2. 채택된 result 뒤에는 `STREAM_EPILOGUE_ALLOWLIST` 이벤트만 허용한다.
      3. result가 하나도 없거나 allowlist 밖 이벤트가 뒤에 남으면 명시 에러다.

    "마지막 줄이 곧 result"라는 이전 가정은 provider가 result 이후에도 무해한
    epilogue 이벤트를 흘리면 성공을 실패로 오판했고, 반대로 미종료 작업 이벤트를
    구분할 수단이 없었다. allowlist를 명시해 두 오판을 동시에 닫는다.
    """
    events: list[tuple[str, dict[str, Any] | None]] = []
    for raw in stdout.splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            data = None
        events.append((line, data if isinstance(data, dict) else None))

    if not events:
        raise OpalAgentError(f"{provider} stream-json 출력이 비어 있습니다.")

    last_idx = -1
    for idx, (_line, data) in enumerate(events):
        if data is not None and data.get("type") == "result":
            last_idx = idx
    if last_idx < 0:
        raise OpalAgentError(
            f"{provider} stream-json 출력에 result 이벤트가 없습니다: "
            f"{events[-1][0][:500]}"
        )

    for line, data in events[last_idx + 1:]:
        if data is None or data.get("type") not in STREAM_EPILOGUE_ALLOWLIST:
            raise OpalAgentError(
                f"{provider} stream-json의 result 이후에 미종료 이벤트가 남았습니다: "
                f"{line[:500]}"
            )

    return events[last_idx][1]      # type: ignore[return-value]


# ─── 공용 attempt runtime ─────────────────────────────────────
#
# OPPL·OPPB 공용 계약(TASK 132 W-1). 세 가지를 provider 무관하게 보장한다.
#   (1) provider 자식을 항상 **새 process group(session) 리더**로 띄운다.
#   (2) stdout 수신과 **분리된 독립 watchdog**이 deadline을 집행하고, 종료 시
#       자식 1개가 아니라 **PGID 전체**를 회수해 손자 고아를 0으로 만든다.
#   (3) `OPAL_AGENT_RUN_ROOT`가 주어지면 attempt record를 run root에 원자 저장한다.
#
# attempt record는 `.result.json`·`.events.jsonl`·`.err.log`·`.exitcode` 4종을
# 대체하지 않는 **추가** 산출물이다(PLAN D6). 환경변수가 없으면 아무것도 쓰지
# 않아 기존 OPPL 호출 경로의 바이트 출력이 그대로 유지된다.

RUN_ROOT_ENV = "OPAL_AGENT_RUN_ROOT"
ATTEMPT_SUBDIR = "attempts"

# watchdog이 deadline과 무관하게 record를 갱신하는 주기(초).
ATTEMPT_HEARTBEAT_INTERVAL = 1.0
# heartbeat가 이보다 오래 멈추면 소유 opal-agent가 죽은 것으로 본다(초).
ATTEMPT_STALE_AFTER = 60.0
# SIGTERM으로 PGID를 회수한 뒤 SIGKILL까지 주는 유예(초).
ATTEMPT_TERM_GRACE = 2.0

EXIT_REASON_RUNNING = "running"
EXIT_REASON_COMPLETED = "completed"
EXIT_REASON_TIMEOUT = "timeout"
EXIT_REASON_FAILED = "failed"
EXIT_REASON_ORPHAN_REAPED = "orphan_reaped"

_TERMINAL_EXIT_REASONS = frozenset({
    EXIT_REASON_COMPLETED, EXIT_REASON_TIMEOUT,
    EXIT_REASON_FAILED, EXIT_REASON_ORPHAN_REAPED,
})


def attempt_run_root() -> str | None:
    """`OPAL_AGENT_RUN_ROOT`가 지정되어 있으면 그 경로, 아니면 None.

    D6 (b)가 CLI 플래그 집합을 동결했으므로 run root는 환경변수로만 받는다.
    """
    raw = (os.environ.get(RUN_ROOT_ENV) or "").strip()
    return raw or None


def _now() -> float:
    return time.time()


def _failure_fingerprint(provider: str, kind: str, message: str) -> str:
    """같은 실패가 같은 지문을 갖도록 숫자·경로 변동분을 지운 안정 해시."""
    head = (message or "").strip().splitlines()
    normalized = "".join(
        "#" if ch.isdigit() else ch for ch in (head[0] if head else "")
    )
    seed = f"{provider}|{kind}|{normalized}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


def _process_alive(pid: int | None) -> bool:
    if not pid or pid <= 0:
        return False
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _group_alive(pgid: int | None) -> bool:
    if not pgid or pgid <= 0:
        return False
    try:
        os.killpg(int(pgid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _signal_group(pgid: int | None, sig: int) -> bool:
    """PGID 전체에 시그널을 보낸다. 자기 자신의 group은 절대 건드리지 않는다."""
    if not pgid or pgid <= 0 or int(pgid) == os.getpgrp():
        return False
    try:
        os.killpg(int(pgid), sig)
    except (ProcessLookupError, PermissionError, OSError):
        return False
    return True


class AttemptRecorder:
    """attempt record 원자 writer.

    run root 하위 `attempts/<attempt_id>.json` 하나만 소유하고, 매 갱신마다
    같은 디렉토리의 `.tmp`에 쓴 뒤 `os.replace`로 교체한다(원자 저장).
    """

    def __init__(self, run_root: str, provider: str, timeout: int) -> None:
        self.run_root = run_root
        self.dir = os.path.join(run_root, ATTEMPT_SUBDIR)
        self.attempt_id = uuid.uuid4().hex
        self.path = os.path.join(self.dir, f"{self.attempt_id}.json")
        self._lock = threading.Lock()
        self._started = time.monotonic()
        self._warned = False
        now = _now()
        self._data: dict[str, Any] = {
            "attempt_id": self.attempt_id,
            "pid": None,
            "pgid": None,
            "exit_reason": EXIT_REASON_RUNNING,
            "provider": provider,
            "owner_pid": os.getpid(),
            "timeout_s": timeout,
            "started_at": now,
            "heartbeat_at": now,
            "finished_at": None,
            "exit_code": None,
            "cost_usd": None,
            "duration_ms": None,
            "failure_fingerprint": None,
        }

    @classmethod
    def create(cls, config: AgentConfig) -> "AttemptRecorder | None":
        run_root = attempt_run_root()
        if not run_root:
            return None
        return cls(run_root, config.provider, config.timeout)

    # 내부 ---------------------------------------------------------------

    def _write_locked(self) -> None:
        tmp = f"{self.path}.tmp"
        try:
            os.makedirs(self.dir, exist_ok=True)
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(self._data, fh, ensure_ascii=False, indent=2,
                          default=str)
                fh.write("\n")
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, self.path)
        except OSError as exc:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            if not self._warned:
                self._warned = True
                print(
                    f"[opal-agent 경고] attempt record 기록 실패({self.path}): {exc}",
                    file=sys.stderr,
                )

    def _update(self, **fields: Any) -> None:
        with self._lock:
            self._data.update(fields)
            self._data["heartbeat_at"] = _now()
            self._write_locked()

    # 공개 ---------------------------------------------------------------

    def attach(self, pid: int, pgid: int) -> None:
        """자식 생성 직후 PID·PGID를 기록한다(재부착·고아 판정의 근거)."""
        self._update(pid=int(pid), pgid=int(pgid))

    def heartbeat(self) -> None:
        self._update()

    def finish(
        self,
        exit_reason: str,
        *,
        exit_code: int | None = None,
        result: "AgentResult | None" = None,
        error: BaseException | None = None,
    ) -> None:
        fields: dict[str, Any] = {
            "exit_reason": exit_reason,
            "finished_at": _now(),
            "exit_code": exit_code,
            "duration_ms": int((time.monotonic() - self._started) * 1000),
        }
        if result is not None:
            fields["cost_usd"] = result.cost_usd
            if result.duration_ms is not None:
                fields["duration_ms"] = result.duration_ms
        if error is not None:
            fields["failure_fingerprint"] = _failure_fingerprint(
                self._data.get("provider", ""),
                type(error).__name__,
                str(error),
            )
        elif exit_reason == EXIT_REASON_TIMEOUT:
            fields["failure_fingerprint"] = _failure_fingerprint(
                self._data.get("provider", ""), "timeout",
                f"deadline {self._data.get('timeout_s')}s",
            )
        self._update(**fields)


class _AttemptGuard:
    """stdout 수신과 분리된 독립 watchdog + PGID 전체 회수.

    `subprocess.run(timeout=...)`이나 stdout 루프 안의 deadline 검사와 달리,
    자식이 한 줄도 내보내지 않아도 deadline이 집행된다. 회수 대상은 직계 자식이
    아니라 자식이 리더인 process group 전체다.
    """

    def __init__(self, proc: subprocess.Popen, timeout: int,
                 recorder: AttemptRecorder | None = None) -> None:
        self.proc = proc
        self.timeout = timeout
        self.recorder = recorder
        self.pgid = self._resolve_pgid(proc)
        self.expired = False
        self._stop = threading.Event()
        self._thread = threading.Thread(
            target=self._watch, name="opal-agent-watchdog", daemon=True,
        )

    @staticmethod
    def _resolve_pgid(proc: subprocess.Popen) -> int:
        # start_new_session=True이므로 PGID == 자식 PID가 계약이다.
        # 자식이 이미 종료했으면 getpgid가 실패하므로 PID로 폴백한다.
        try:
            return os.getpgid(proc.pid)
        except (ProcessLookupError, PermissionError, OSError):
            return proc.pid

    def start(self) -> "_AttemptGuard":
        if self.recorder is not None:
            self.recorder.attach(self.proc.pid, self.pgid)
        self._thread.start()
        return self

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=ATTEMPT_TERM_GRACE + 5.0)

    def reclaim(self) -> None:
        """PGID 전체를 SIGTERM → (유예) → SIGKILL로 회수한다."""
        _signal_group(self.pgid, signal.SIGTERM)
        deadline = time.monotonic() + ATTEMPT_TERM_GRACE
        while time.monotonic() < deadline:
            if self.proc.poll() is not None:
                break
            time.sleep(0.05)
        # 자식이 죽어도 손자가 group에 남아 있을 수 있다 — 항상 한 번 더 쓸어낸다.
        _signal_group(self.pgid, signal.SIGKILL)
        if self.proc.poll() is None:
            try:
                self.proc.kill()
            except OSError:
                pass

    def _watch(self) -> None:
        deadline = time.monotonic() + self.timeout
        while not self._stop.is_set():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                self.expired = True
                self.reclaim()
                return
            if self.recorder is not None:
                self.recorder.heartbeat()
            self._stop.wait(min(remaining, ATTEMPT_HEARTBEAT_INTERVAL))


# ─── 재부착 / 고아 판정 (Supervisor 진입점) ───────────────────

def load_attempt_records(run_root: str) -> list[dict[str, Any]]:
    """run root에 저장된 attempt record를 전부 읽는다(손상 파일은 건너뛴다)."""
    directory = os.path.join(run_root, ATTEMPT_SUBDIR)
    records: list[dict[str, Any]] = []
    try:
        names = sorted(os.listdir(directory))
    except OSError:
        return records
    for name in names:
        if not name.endswith(".json"):
            continue
        path = os.path.join(directory, name)
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict):
            data["_path"] = path
            records.append(data)
    return records


def classify_attempt(
    record: dict[str, Any], *, now: float | None = None,
    stale_after: float = ATTEMPT_STALE_AFTER,
) -> str:
    """attempt 하나를 재시작 관점에서 분류한다.

    반환값:
      `finished`      — 종료 사유가 확정된 record. 할 일 없음.
      `reattachable`  — process group이 살아 있고 heartbeat가 신선하다.
                        소유 opal-agent가 아직 살아 있으므로 재부착 대상이다.
      `orphan`        — process group은 살아 있는데 heartbeat가 끊겼다.
                        소유자가 죽은 고아이므로 회수 대상이다.
      `abandoned`     — process가 이미 사라졌는데 record가 확정되지 않았다.
    """
    if record.get("exit_reason") in _TERMINAL_EXIT_REASONS:
        return "finished"
    pgid = record.get("pgid")
    pid = record.get("pid")
    alive = _group_alive(pgid) or _process_alive(pid)
    if not alive:
        return "abandoned"
    reference = _now() if now is None else now
    heartbeat = record.get("heartbeat_at") or record.get("started_at") or 0.0
    owner_alive = _process_alive(record.get("owner_pid"))
    if owner_alive and (reference - float(heartbeat)) <= stale_after:
        return "reattachable"
    return "orphan"


def reconcile_attempts(
    run_root: str, *, reap: bool = False,
    stale_after: float = ATTEMPT_STALE_AFTER,
) -> dict[str, list[dict[str, Any]]]:
    """재시작 시 attempt 재부착/고아 정리를 판정하는 공개 진입점.

    `reap=True`이면 `orphan`으로 판정된 attempt의 PGID 전체를 회수하고 record를
    `orphan_reaped`로 확정한다. `reattachable` attempt는 절대 건드리지 않는다.
    """
    buckets: dict[str, list[dict[str, Any]]] = {
        "finished": [], "reattachable": [], "orphan": [], "abandoned": [],
    }
    for record in load_attempt_records(run_root):
        verdict = classify_attempt(record, stale_after=stale_after)
        buckets[verdict].append(record)
        if verdict == "orphan" and reap:
            _reap_orphan(record)
    return buckets


def _reap_orphan(record: dict[str, Any]) -> None:
    pgid = record.get("pgid")
    _signal_group(pgid, signal.SIGTERM)
    deadline = time.monotonic() + ATTEMPT_TERM_GRACE
    while time.monotonic() < deadline and _group_alive(pgid):
        time.sleep(0.05)
    _signal_group(pgid, signal.SIGKILL)
    record["exit_reason"] = EXIT_REASON_ORPHAN_REAPED
    record["finished_at"] = _now()
    path = record.get("_path")
    if not path:
        return
    payload = {k: v for k, v in record.items() if k != "_path"}
    tmp = f"{path}.tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2, default=str)
            fh.write("\n")
        os.replace(tmp, path)
    except OSError:
        try:
            os.unlink(tmp)
        except OSError:
            pass


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
) -> AgentResult:
    """
    지정한 provider CLI를 서브에이전트로 1회 실행하고 결과를 반환한다.

    다중 턴이 필요하면 반환된 AgentResult.session_id를 다음 호출의
    session_id로 넘겨 대화를 이어간다.

    예외:
      ClaudeNotFoundError — provider CLI 미설치(PATH 부재)
      OpalAgentTimeout    — timeout 초과
      OpalAgentError      — 비정상 종료 / 파싱 실패 / 알 수 없는 provider 등

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
    )
    return _run(config)


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

    recorder = AttemptRecorder.create(config)

    if config.output_format == "stream-json":
        try:
            return _run_stream(config, adapter, inv, env, recorder)
        finally:
            for path in inv.tempfiles:
                try:
                    os.unlink(path)
                except OSError:
                    pass

    # start_new_session=True로 자식을 새 process group 리더로 띄운다. deadline은
    # subprocess.run의 timeout이 아니라 독립 watchdog이 집행하고, 회수 대상은
    # 직계 자식이 아니라 PGID 전체다(손자 고아 0).
    proc = subprocess.Popen(
        inv.cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=config.cwd,
        env=env,
        start_new_session=True,
    )
    guard = _AttemptGuard(proc, config.timeout, recorder).start()
    try:
        stdout, stderr = proc.communicate()
    finally:
        guard.stop()
        for path in inv.tempfiles:
            try:
                os.unlink(path)
            except OSError:
                pass

    if guard.expired:
        if recorder is not None:
            recorder.finish(EXIT_REASON_TIMEOUT, exit_code=proc.returncode)
        raise OpalAgentTimeout(
            f"{config.provider} 실행이 {config.timeout}초를 초과했습니다."
        )

    if proc.returncode != 0:
        error = OpalAgentError(
            f"{config.provider} 비정상 종료 (exit {proc.returncode})\n"
            f"stderr: {(stderr or '').strip()}"
        )
        if recorder is not None:
            recorder.finish(EXIT_REASON_FAILED, exit_code=proc.returncode,
                            error=error)
        raise error

    return _finalize(config, adapter, stdout, proc.returncode, recorder)


def _finalize(
    config: AgentConfig, adapter: ProviderAdapter, stdout: str,
    exit_code: int | None, recorder: AttemptRecorder | None,
) -> AgentResult:
    """파싱 결과와 종료 사유를 attempt record에 확정한다."""
    try:
        result = adapter.parse_result(config, stdout)
    except OpalAgentError as exc:
        if recorder is not None:
            recorder.finish(EXIT_REASON_FAILED, exit_code=exit_code, error=exc)
        raise
    if recorder is not None:
        recorder.finish(EXIT_REASON_COMPLETED, exit_code=exit_code,
                        result=result)
    return result


def _run_stream(
    config: AgentConfig, adapter: ProviderAdapter, inv: Invocation,
    env: dict[str, str] | None, recorder: AttemptRecorder | None = None,
) -> AgentResult:
    """stream-json 전용 실행 경로 — Popen으로 증분 소비하며 자기 stdout으로
    line-buffered passthrough한다(H-4). stderr는 상속(호출측 셸 `2>` 캡처).

    deadline은 stdout 줄 수신 루프가 아니라 `_AttemptGuard`의 독립 watchdog이
    집행한다 — 자식이 한 줄도 내보내지 않아도 timeout이 발화한다(S-2).
    """
    proc = subprocess.Popen(
        inv.cmd,
        stdout=subprocess.PIPE,
        stderr=None,
        text=True,
        bufsize=1,
        cwd=config.cwd,
        env=env,
        start_new_session=True,
    )
    guard = _AttemptGuard(proc, config.timeout, recorder).start()
    lines: list[str] = []
    try:
        for line in proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            lines.append(line)
        proc.wait()
    finally:
        if proc.stdout:
            proc.stdout.close()
        guard.stop()

    if guard.expired:
        if recorder is not None:
            recorder.finish(EXIT_REASON_TIMEOUT, exit_code=proc.returncode)
        raise OpalAgentTimeout(
            f"{config.provider} stream 실행이 {config.timeout}초를 초과했습니다."
        )

    if proc.returncode != 0:
        error = OpalAgentError(
            f"{config.provider} stream 비정상 종료 (exit {proc.returncode})"
        )
        if recorder is not None:
            recorder.finish(EXIT_REASON_FAILED, exit_code=proc.returncode,
                            error=error)
        raise error

    return _finalize(config, adapter, "".join(lines), proc.returncode, recorder)


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
