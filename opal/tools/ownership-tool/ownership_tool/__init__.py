"""
@header {
  "module": "ownership_tool",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "ownership-tool 파이썬 패키지 루트(D-19). 하위 모듈 구성은 `ownership_tool/` 디렉터리가 SSOT이며 이 파일은 그 import 경계만 제공한다. 어떤 시스템 상태도 읽지 않고 하위 모듈을 재노출하지도 않는다 — 소비자는 `from ownership_tool import <module>`로 직접 import한다.",
  "exports": ["__version__"],
  "depends": []
}
"""

__version__ = "0.1.0"
