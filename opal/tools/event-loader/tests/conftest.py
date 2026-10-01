"""
@header {
  "module": "conftest",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "event-loader 테스트가 운영 원장(~/.opal/state)을 오염시키지 않도록 OPAL_EVENT_LOADER_LEDGER를 임시 파일로 고정",
  "exports": [],
  "depends": []
}
"""

from __future__ import annotations

import atexit
import os
import shutil
import tempfile
from pathlib import Path

_LEDGER_DIR = tempfile.mkdtemp(prefix="opal-event-loader-test-ledger-")
atexit.register(shutil.rmtree, _LEDGER_DIR, ignore_errors=True)
os.environ["OPAL_EVENT_LOADER_LEDGER"] = str(Path(_LEDGER_DIR) / "legacy-dispatch.jsonl")
