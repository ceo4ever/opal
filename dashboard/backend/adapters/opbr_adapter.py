"""
@header {
  "module": "adapters.opbr_adapter",
  "layer": "service",
  "domain": "console",
  "description": "Phase 2 하드닝 + cwd 격리 + 대화별 session_id: claude -p '[ASSISTANT]\\n//opbr query --read-only <질의>' --output-format json 서브프로세스 구동. 프롬프트 첫 줄 [ASSISTANT] 마커로 headless 호출을 비서 tier(Phase A)로 캡 — PM tier(Phase B) 승격을 억제해 읽기전용 브레인 워커의 tier 오염을 방지한다. subprocess.run에 cwd=project_path 설정 → opbr/brain-tool이 해당 프로젝트의 .opal/brain을 검색(격리 보장). project_path 존재 검증(NotADirectoryError). 세션 핸들(cold=True→--session-id FE제공session_id / cold=False→--resume session_id) + JSON 코드펜스 추출(preamble 견고). session_id는 항상 호출자(BE)가 전달 — opbr_adapter가 uuid를 생성하지 않음. [MUST] --safe-mode·--bare·anthropic SDK·API 키 절대 금지. --allowedTools Bash,Read,Grep,Glob 단일 콤마값으로 주입(단일 인자 → 뒤 플래그 삼킴 방지). read-only 가드는 opbr --read-only 계약으로 보장(접미사 제거). backend는 얇은 프록시 — opbr이 brain 검색/페이지 Read/인용 전담(DRY).",
  "exports": ["prime_and_ask", "extract_json_fence"],
  "depends": []
}
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time


# [MUST] --safe-mode·--bare·anthropic SDK·ANTHROPIC_API_KEY 절대 사용 금지
# 구독 keychain 인증 유지 + OPAL/opbr 스킬 로드를 위해 기본 claude 바이너리 직접 구동
CLAUDE_BIN = "claude"


def extract_json_fence(result_text: str) -> dict:
    """claude --output-format json의 result 문자열에서 JSON 코드펜스를 추출한다.

    opbr가 출력하는 JSON 코드펜스 형식:
        ```json
        {"answer": "...", "citations": [...]}
        ```

    부트스트랩 preamble이 앞에 붙어도 펜스만 발췌한다(정규식).
    펜스가 없으면 result 전체를 answer로 폴백 + citations=[].

    Returns:
        dict with keys:
            answer: str      — brain 답변
            citations: list  — 인용 목록 (없으면 빈 리스트)

    Raises:
        RuntimeError: result_text가 None이거나 string이 아닌 경우
    """
    if not isinstance(result_text, str):
        raise RuntimeError(
            f"extract_json_fence: result_text must be str, got {type(result_text)}"
        )

    # 1차 시도: ```json ... ``` 펜스 추출 (preamble 무시)
    fence_pattern = re.compile(
        r"```json\s*\n(.*?)\n\s*```",
        re.DOTALL,
    )
    matches = fence_pattern.findall(result_text)

    if matches:
        # 마지막 펜스 우선 (preamble에 펜스가 섞여도 마지막이 실제 답변)
        fence_content = matches[-1].strip()
        try:
            parsed = json.loads(fence_content)
            answer = parsed.get("answer", "")
            citations = parsed.get("citations", [])
            if not isinstance(citations, list):
                citations = []
            return {"answer": answer, "citations": citations}
        except (json.JSONDecodeError, ValueError):
            pass  # 펜스 내 JSON 파싱 실패 → 폴백으로 넘어감

    # 2차 시도: 마지막 { ... } 블록 추출 (중첩 가능)
    # 가장 바깥의 { } 블록을 찾되 마지막 것 사용
    brace_pattern = re.compile(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", re.DOTALL)
    brace_matches = brace_pattern.findall(result_text)

    for candidate in reversed(brace_matches):
        try:
            parsed = json.loads(candidate)
            if "answer" in parsed or "citations" in parsed:
                answer = parsed.get("answer", "")
                citations = parsed.get("citations", [])
                if not isinstance(citations, list):
                    citations = []
                return {"answer": answer, "citations": citations}
        except (json.JSONDecodeError, ValueError):
            continue

    # 폴백: result_text 전체를 answer로 반환
    return {"answer": result_text, "citations": []}


def prime_and_ask(
    question: str,
    project_path: str,
    session_id: str,
    cold: bool,
    timeout: float = 180.0,
) -> dict:
    """B2 방식 opbr 질의 (Phase 2 하드닝 + 대화별 session_id):
       - 호출: //opbr query --read-only "<질의>" (--read-only 계약이 read-only를 보장)
       - cold=True: --session-id <session_id> 로 OPAL/opbr 최초 프라임 (FE 제공 session_id 사용)
       - cold=False: --resume <session_id> 로 기존 세션 재개

    prompt 첫 줄 [ASSISTANT] 마커로 headless 호출을 비서 tier(Phase A)로 캡 — 읽기전용
    브레인 워커가 PM tier(구현금지 가드·디스패치 의무·CLOSE 게이트)를 불필요 로드하는
    tier 오염을 방지한다 (opal/core/AGENT.md [ASSISTANT 규칙]).

    session_id는 항상 호출자(BE BrainSessionRegistry)가 전달한다.
    opbr_adapter는 uuid를 자체 생성하지 않는다.

    Args:
        question: 사용자 질문 (//opbr query --read-only에 전달)
        project_path: OPAL 프로젝트 절대 경로 (cwd 격리용)
        session_id: FE가 생성·전달한 대화 식별자. cold=True이면 --session-id, cold=False이면 --resume
        cold: True이면 콜드 프라임(--session-id), False이면 웜 재개(--resume)
        timeout: subprocess 타임아웃 (초). 콜드=180, 웜=60 권고

    Returns:
        dict with keys:
            answer: str       — opbr 답변 본문
            citations: list   — 인용 목록 [{page, title, type, score?}]
            session_id: str   — 세션 핸들 (B2 resume용)
            elapsed_s: float  — 소요 시간 (초)

    Raises:
        RuntimeError: is_error:true / result 부재 / 비JSON / subprocess 실패
    """
    # //opbr query --read-only 계약 사용 (read-only 가드 프롬프트 접미사 불필요)
    # [ASSISTANT] 첫 줄 마커: headless 호출을 비서 tier(Phase A)로 캡 —
    # cwd(project_path)에 .opal/AGENT.md가 있어도 PM tier(Phase B) 승격 억제 (opal/core/AGENT.md [ASSISTANT 규칙])
    # //opbr는 비서 tier `//` 능력으로 완주 (opal/core/AGENT.md:15)
    prompt = f'[ASSISTANT]\n//opbr query --read-only "{question}"'

    # 커맨드 배열 구성 — shell=False 보장 (H-13 셸 인젝션 방지)
    # --allowedTools: 콤마 구분 단일 인자 → 뒤따르는 -p 플래그를 삼키지 않음
    # 허용: Bash(brain-tool 실행), Read(페이지 조회), Grep/Glob(검색)
    # 미허용: Write·Edit·MultiEdit (read-only 방어 1겹)
    cmd: list[str] = [
        CLAUDE_BIN,
        "--allowedTools", "Bash,Read,Grep,Glob",
        "-p", prompt,
        "--output-format", "json",
    ]

    generated_session_id = session_id  # 항상 호출자 제공값 사용
    if cold:
        # 콜드 프라임: FE 제공 session_id로 --session-id 생성
        cmd += ["--session-id", session_id]
    else:
        # 웜 재개: FE 제공 session_id로 --resume
        cmd += ["--resume", session_id]

    # project_path 존재 검증 (빈 문자열이면 스킵 — 라우터가 400으로 사전 검증)
    if project_path and not os.path.isdir(project_path):
        raise NotADirectoryError(
            f"prime_and_ask: project_path가 존재하지 않거나 디렉토리가 아닙니다: {project_path!r}"
        )

    t0 = time.monotonic()

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,  # [MUST] shell=False — 셸 인젝션 방지 (H-13)
            cwd=project_path if project_path else None,  # 프로젝트 brain 격리
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"prime_and_ask timeout after {timeout}s"
        ) from exc

    elapsed_s = time.monotonic() - t0

    # 비JSON 출력 처리
    stdout = proc.stdout.strip()
    try:
        parsed = json.loads(stdout)
    except (json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError(
            f"prime_and_ask: non-JSON output from claude. "
            f"returncode={proc.returncode}, stderr={proc.stderr[:200]!r}"
        ) from exc

    # is_error 판정 (H-6)
    if parsed.get("is_error") is True:
        subtype = parsed.get("subtype", "unknown")
        raise RuntimeError(
            f"prime_and_ask: claude returned is_error=true, subtype={subtype}"
        )

    # result 필드 존재 확인
    if "result" not in parsed:
        raise RuntimeError(
            f"prime_and_ask: 'result' field missing in claude output. keys={list(parsed.keys())}"
        )

    # result에서 JSON 코드펜스 추출 (preamble 견고)
    result_text = parsed["result"]
    extracted = extract_json_fence(result_text)

    return {
        "answer": extracted["answer"],
        "citations": extracted["citations"],
        # claude가 반환하는 session_id를 우선 사용, 없으면 생성/입력값 폴백
        "session_id": parsed.get("session_id") or generated_session_id,
        "elapsed_s": elapsed_s,
    }
