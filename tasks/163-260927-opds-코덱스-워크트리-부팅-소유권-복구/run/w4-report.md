# W-4 실행 보고

- Codex launcher 기본 argv와 shipped setting default를 `codex --no-daemon "{utterance}"`로 변경했다.
- macOS와 Windows 설치 이관은 이전 기본값 `codex "{utterance}"`과 정확히 일치할 때만 새 기본값으로 바꾼다. 사용자 argv는 보존한다. launcher 블록이 없는 기존 설정에는 기본 블록을 seed한다.
- 양 설치 스크립트는 고정 버전을 가정하지 않고 `codex --help`에 `--no-daemon`이 표시되는지 확인하도록 안내한다.
- 검증: `/Users/iskang/.opal/.venv/bin/python -m pytest -q opal/tools/worktree-launcher/tests/test_settings.py` (22 passed), `bash -n scripts/install-mac.sh`, JSON parse, `git diff --check` 통과. `scripts/tests/test_agent_adapter_fields.sh`의 신규 TS-028은 통과했다. 기존 TS-025·TS-026은 Claude Stop hooks 관련 source 계약 누락으로 실패하며 W-4 변경과 무관하다.
