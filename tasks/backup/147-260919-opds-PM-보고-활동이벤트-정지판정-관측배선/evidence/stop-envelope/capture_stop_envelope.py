"""
@header
- layer: util
- role: W-2 일회성 Stop 봉투 캡처 훅 — stdin 전문을 1회 파일로 적재한다
- owner: tasks/147-260919-opds-PM-보고-활동이벤트-정지판정-관측배선
- contract: 어떤 경우에도 stdout/stderr 무출력, exit 0. 이미 캡처본이 있으면 덮어쓰지 않는다
- note: `.claude/settings.local.json`의 hooks.Stop에 임시 등록해 1회 캡처한 뒤 원복하는 용도다
"""

import json
import os
import platform
import sys
import time

_DEFAULT_OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".stop-envelope.raw.json")


def main() -> int:
    try:
        out_path = os.environ.get("OPAL_W2_CAPTURE_PATH") or _DEFAULT_OUT
        if os.path.exists(out_path):
            return 0
        raw = sys.stdin.read()
        try:
            envelope = json.loads(raw)
        except Exception:
            envelope = {"_unparsed_stdin_len": len(raw)}
        record = {
            "captured_at_epoch": time.time(),
            "captured_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "platform": platform.platform(),
            "platform_system": platform.system(),
            "envelope": envelope,
        }
        tmp_path = out_path + ".tmp"
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(tmp_path, "w", encoding="utf-8") as fh:
            json.dump(record, fh, ensure_ascii=False, indent=2, sort_keys=True)
        os.replace(tmp_path, out_path)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
