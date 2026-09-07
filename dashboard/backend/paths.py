"""
@header {
  "module": "paths",
  "layer": "config",
  "domain": "console",
  "description": "허브 고정 데이터 참조 경로를 허브 루트로 해석하는 순수 문자열 함수 hub_root() 하나만 제공한다. 파일시스템·환경변수·cwd()에 접근하지 않고 표준 라이브러리만 쓰므로 존재하지 않는 합성 경로에도 적용된다. 판정 규칙의 원문은 이 모듈이 소유하지 않고 opal/core/references/opal-harness.md §2.5 (4)가 소유하며, 실행 가능한 대조 기준은 3런타임(console BE·brain-tool·code-scan)이 공유하는 골든 케이스 표 opal/core/references/hub-root-cases.json(C-1~C-7)이다.",
  "exports": ["hub_root"],
  "depends": []
}
"""
from __future__ import annotations

# 판정 규칙: opal/core/references/opal-harness.md §2.5 (4)
_WORKTREES_SEGMENT = ".opal-worktrees"
_SEP = "/"


def hub_root(path: str) -> str:
    segments = path.split(_SEP)
    try:
        index = segments.index(_WORKTREES_SEGMENT)
    except ValueError:
        return path

    parent = _SEP.join(segments[:index])
    if parent:
        return parent
    # 세그먼트가 경로의 첫 성분인 경우: 절대 경로면 루트("/"), 상대 경로면 현재 위치(".")가 부모다.
    return _SEP if path.startswith(_SEP) else "."
