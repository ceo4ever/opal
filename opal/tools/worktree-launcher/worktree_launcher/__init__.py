"""
@header {
  "module": "worktree_launcher",
  "layer": "util",
  "domain": "opal-workspace",
  "description": "worktree-launcher 파이썬 패키지 루트. 허브에서 워크트리 실행 세션을 띄우는 lifecycle 코어(launcher_core)의 import 경계만 제공하며 어떤 시스템 상태도 읽지 않는다. `worktree-launcher`는 하이픈 디렉터리라 패키지명이 될 수 없어 `worktree_launcher/` 하위 패키지를 둔다(ownership-tool D-19와 같은 배치). 터미널 adapter(`adapters/`)는 후속 Work item이 채운다.",
  "exports": ["__version__"],
  "depends": []
}
"""

__version__ = "0.1.0"
