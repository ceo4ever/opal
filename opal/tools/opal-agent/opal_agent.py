#!/usr/bin/env python3
"""
@header {
  "module": "opal_agent",
  "layer": "util",
  "domain": "opal-workspace",
  "description": "멀티 provider 서브에이전트 호출 라이브러리 + CLI — claude/gemini/codex/grok 등 여러 LLM CLI를 비대화형 서브에이전트로 호출하는 단일 모듈",
  "exports": ["call_agent", "AgentConfig", "AgentResult", "PROVIDERS", "OpalAgentError", "ClaudeNotFoundError", "OpalAgentTimeout"]
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
  - 부트스트랩 마커 3-way: on(마커 없음·풀 부트스트랩) / assistant([ASSISTANT]
    첫 줄 — 비서 tier(Phase A)만, PM 승격 억제) / off([WORKER] 첫 줄 — 전부 스킵).
  - cold session id(new_session_id → claude --session-id)는 claude 전용
    (supports_session_assign). session_id(warm --resume)와 상호 배타 — _run이 검증.

변경이력:
  v1.0 2026-07-12 초기 구현 — claude 전용 call_agent + AgentConfig/AgentResult + CLI
  v2.0 2026-07-12 멀티 provider 어댑터 계층 — gemini/codex/grok 추가
  v2.1 2026-07-12 cursor provider 추가 + ProviderAdapter ABC화. Antigravity 보류
  v2.2 2026-07-12 antigravity(agy) provider 추가 — text-only 2급(실측 반영)
  v2.3 2026-07-12 effort(추론 강도) 지원 — claude/codex/grok, 미지원 provider 경고
  v2.4 2026-07-12 --opal-bootstrap on|off — off면 [WORKER] 첫 줄 마커로 부트스트랩
                  스킵(진입점 게이트 배선과 연동). env 방식 폐기(043 회귀 회피)
  v2.5 2026-07-13 15:25 --opal-bootstrap 3-way — assistant([ASSISTANT] 비서 tier 캡) 추가
                  + caller-supplied cold session id(claude --session-id, new_session_id) (059)
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
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
    output_format: str = "json"                   # "json" | "text"
    bin: str | None = None                        # CLI 바이너리 오버라이드 (기본: provider별)
    opal_bootstrap: str = "on"                    # "on"(풀 부트스트랩) | "assistant"([ASSISTANT] Phase A만) | "off"([WORKER] 전부 스킵)


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

# 부트스트랩 스킵 사다리 ↔ 첫 줄 마커 1:1 대응 (core AGENT.md:9 3단 사다리)
_BOOTSTRAP_MARKERS = {"off": "[WORKER]", "assistant": "[ASSISTANT]"}


class ProviderAdapter(ABC):
    """provider별 CLI 인자 조립 + 출력 파싱 인터페이스."""

    name: str = ""
    default_bin: str = ""
    supports_resume: bool = False
    supports_effort: bool = False     # effort(추론 강도) 플래그 지원 여부
    supports_session_assign: bool = False   # cold --session-id(caller-supplied) 지원 여부

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

    def build_invocation(self, config: AgentConfig, resolved_bin: str) -> Invocation:
        cmd = [resolved_bin, "-p", self._mark(config.prompt, config),
               "--output-format", config.output_format]
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

    bin_name = config.bin or adapter.default_bin

    resolved = shutil.which(bin_name)
    if resolved is None:
        raise ClaudeNotFoundError(
            f"`{bin_name}` 실행 파일을 PATH에서 찾을 수 없습니다. "
            f"{config.provider} CLI가 설치되어 있는지 확인하세요."
        )

    inv = adapter.build_invocation(config, resolved)
    # opal_bootstrap=off면 각 어댑터가 프롬프트 첫 줄에 [WORKER] 마커를 붙여
    # OPAL 부트스트랩을 스킵한다(env가 아니라 진입점 게이트가 마커를 읽음).
    env = {**os.environ, **inv.env} if inv.env else None

    try:
        proc = subprocess.run(
            inv.cmd,
            capture_output=True,
            text=True,
            cwd=config.cwd,
            env=env,
            timeout=config.timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise OpalAgentTimeout(
            f"{config.provider} 실행이 {config.timeout}초를 초과했습니다."
        ) from exc
    finally:
        for path in inv.tempfiles:
            try:
                os.unlink(path)
            except OSError:
                pass

    if proc.returncode != 0:
        raise OpalAgentError(
            f"{config.provider} 비정상 종료 (exit {proc.returncode})\n"
            f"stderr: {proc.stderr.strip()}"
        )

    return adapter.parse_result(config, proc.stdout)


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
        help="서브에이전트 OPAL 부트스트랩 (기본 on). "
             "assistant=[ASSISTANT] 첫 줄(비서 tier·Phase A만) / off=[WORKER] 첫 줄(전부 스킵)",
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

    try:
        # 라이브러리는 항상 JSON으로 실행해 session_id·메타를 확보한다.
        # CLI 표시(display)는 그 결과를 어떻게 보여줄지의 별개 선택.
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
            output_format="json",
            bin=args.bin,
            opal_bootstrap=args.opal_bootstrap,
        )
    except OpalAgentError as exc:
        print(f"[opal-agent 오류] {exc}", file=sys.stderr)
        return 2

    if args.display == "json":
        json.dump(result.raw, sys.stdout, ensure_ascii=False, indent=2, default=str)
        sys.stdout.write("\n")
    else:
        print(result.text)

    return 1 if result.is_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
