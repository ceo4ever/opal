#!/bin/bash
# usage: section_wrapper.sh <run_tag> <id[,id...]>   - 켬 프로브 전용. 호출을 section-calls.jsonl에 기록하고 loader section 실행.
TAG="$1"; IDS="$2"
D="$(cd "$(dirname "$0")" && pwd)"
R=/Volumes/Data/AiStudio/workspace/opal/.opal-worktrees/task_177
OUT=$("$HOME/.opal/.venv/bin/python3" "$R/opal/tools/event-loader/event_loader.py" section --receipt "$D/results/receipt-stage.design-on.json" --id "$IDS" --source-root "$R" --project-root "$R" 2>&1)
RC=$?
python3 - "$TAG" "$IDS" "$RC" "${#OUT}" <<'P' >> "$D/results/section-calls.jsonl"
import json,sys,time
print(json.dumps({"ts":time.strftime("%FT%TZ",time.gmtime()),"run_tag":sys.argv[1],"ids":sys.argv[2],"rc":int(sys.argv[3]),"out_chars":int(sys.argv[4])}))
P
echo "$OUT"
exit $RC
