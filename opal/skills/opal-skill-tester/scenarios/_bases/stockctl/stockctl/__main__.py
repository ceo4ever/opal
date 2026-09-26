"""
@header {
  "module": "stockctl.__main__",
  "layer": "api",
  "domain": "inventory",
  "description": "python -m stockctl 실행 진입점.",
  "exports": []
}
"""
import sys

from .cli import main

sys.exit(main())
