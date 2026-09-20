# DONE: 부트스트랩 행동 필요 브리핑

## 결과

프로젝트 세션 부트스트랩에 최근 미완료 작업과 우선 검토 메모리를 조건부로 요약하는 기능을 추가했다. 기존 세션 분기와 빈 결과 동작은 유지하며, 상태→메모리 순서와 UTF-8 1024바이트 상한을 적용했다.

## 변경 파일

- `opal/tools/memory-tool/memory_tool.py`
- `opal/tools/memory-tool/tests/test_boot_brief.py`
- `opal/tools/memory-tool/README.md`
- `opal/tools/state-tool/state_tool.py`
- `opal/tools/state-tool/tests/test_state_tool.py`
- `opal/bootstrapper/claude-bootstrap.md`
- `opal/bootstrapper/codex-bootstrap.md`
- `opal/bootstrapper/cursor-bootstrap.mdc`
- `opal/bootstrapper/gemini-bootstrap.md`
- `opal/core/references/tools.md`
- `opal/core/references/opal-pm.md`
- `scripts/tests/task113_bootstrap_audit.py`

## 검증

- memory-tool boot brief 테스트: 4건 통과
- state-tool 테스트: 402건 통과, 3건 skip
- bootstrap audit: 통과
- opal-agent 이벤트 테스트: 6건 통과
- PLAN contract/code-scan citation: 통과
- `git diff --check`: 통과

## 참고

작업 worktree는 머지 대기 상태이며 자동 제거하지 않았다. 머지·PR 처리 후 worktree-tool로 회수할 수 있다.

