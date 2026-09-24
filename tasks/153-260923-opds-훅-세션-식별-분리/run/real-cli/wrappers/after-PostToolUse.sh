#!/bin/sh
set -eu
STDIN_DATA=$(cat)
N=0
while [ -f "/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_153/tasks/153-260923-opds-훅-세션-식별-분리/run/real-cli/payloads/after-PostToolUse-${N}.json" ]; do N=$((N+1)); done
printf '%s' "$STDIN_DATA" > "/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_153/tasks/153-260923-opds-훅-세션-식별-분리/run/real-cli/payloads/after-PostToolUse-${N}.json"
printf '%s' "$STDIN_DATA" | exec "/Users/iskang/.opal/.venv/bin/python" "/var/folders/fc/w424kvjn3mxfk6nyzkw_8b740000gn/T/verify-real-cli-after-lw5cb292/deployment-after/ownership_tool/heartbeat_hook.py"
