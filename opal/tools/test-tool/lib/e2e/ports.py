"""
@header {
  "module": "ports",
  "layer": "util",
  "domain": "opal-tools",
  "description": "T01 최소 포트 확보 — find_free_port로 bind 가능한 127.0.0.1 포트 1건을 확보한다. 이 모듈이 포트 확보의 유일한 진입점이며 lib.e2e.runtime은 이 함수를 호출하지 않는다(D-11 — 포트 확보 책임은 호출자에게 있다). allocator lock·lease record·stale 회수·worktree 동시성(§A.7, C-LEASE-1/2, MV-36)은 T03 소유이며 이 모듈에 stub조차 두지 않는다(D-7).",
  "exports": ["MAX_PORT_ATTEMPTS", "find_free_port"]
}
"""

from __future__ import annotations

import socket

MAX_PORT_ATTEMPTS = 5


def find_free_port(host: str = "127.0.0.1") -> int:
    """host에 bind 가능한 임시 포트 1건을 확보해 반환한다.

    확보 이후 실제 기동 전까지 다른 프로세스가 같은 포트를 선점할 수 있는 TOCTOU 창은
    닫지 않는다(H-5) — strict-port 기동 실패를 신호로 호출자가 MAX_PORT_ATTEMPTS회까지
    재확보하는 것으로 완화한다. 창을 닫는 allocator lock은 T03 소유다.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return sock.getsockname()[1]
