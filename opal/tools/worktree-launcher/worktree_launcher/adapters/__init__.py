"""
@header {
  "module": "worktree_launcher.adapters",
  "layer": "util",
  "domain": "opal-workspace",
  "description": "터미널 adapter 패키지 경계. 각 adapter 모듈은 `launch(worktree_root, command)` 한 번으로 터미널 기동과 handoff prompt 제출을 수행하고 launch·prompt receipt의 원천 필드를 한 dict로 돌려준다(launcher_core가 기대하는 단일 seam). 이 __init__은 어떤 adapter도 import하지 않는다 — 호출자가 쓰려는 adapter만 명시 import해 OS·터미널 종류 추측을 만들지 않는다.",
  "exports": [],
  "depends": []
}
"""
