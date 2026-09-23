# BASELINE (EXECUTE 진입 전 측정)

- 측정 시각: 2026-09-16 23:30 KST
- 작업본 HEAD: e0d52e1 (feat/OP-TASK-137)
- 인터프리터: /Users/iskang/.opal/.venv/bin/python (OPAL 테스트 인터프리터 게이트 준수)

## 3스위트 전건 (S-11 기준선)
```
E   AssertionError: {'tas[74 chars]: '1.2', 'created_at': '<S-9 wallclock normali[659 chars] []}} != {'tas[74 chars]: '1.0', 'created_at': '<S-9 wallclock normali[425 chars] 진입'}
E   Diff is 1185 characters long. Set self.maxDiff to None to see it. : S-9(1-1) HEAD 대비 state.json 불일치(벽시계 필드 정규화 후에도 남는 차이) — HEAD={'task_id': 'task-s9-1-1', 'skill': 'oppl', 'mode': 'agentic', 'schema_version': '1.2', 'created_at': '<S-9 wallclock normalized>', 'updated_at': '<S-9 wallclock normalized>', 'current_status': 'in_progress', 'rows': [{'row_id': 1, 'stage': 'EXECUTE', 'item': '구현 A', 'status': 'done', 'status_label': '✅', 'timestamp': '<S-9 wallclock normalized>', 'owner': 'PM', 'note': None}, {'row_id': 2, 'stage': 'EXECUTE', 'item': '구현 B', 'status': 'pending', 'status_label': '⬜', 'timestamp': None, 'owner': 'PM', 'note': None}], 'next_action': 'EXECUTE 구현 B 진입', 'run_log': {'contract_version': '1.0', 'mode': 'shadow', 'completion_profile': 'cooperative', 'completion_profile_receipt': None, 'active_run_id': 'run_ab8b0d53-8172-467f-8ae1-8a1720b2921b', 'status': 'active', 'pending_events': []}} 현재본={'task_id': 'task-s9-1-1', 'skill': 'oppl', 'mode': 'agentic', 'schema_version': '1.0', 'created_at': '<S-9 wallclock normalized>', 'updated_at': '<S-9 wallclock normalized>', 'current_status': 'in_progress', 'rows': [{'row_id': 1, 'stage': 'EXECUTE', 'item': '구현 A', 'status': 'done', 'status_label': '✅', 'timestamp': '<S-9 wallclock normalized>', 'owner': 'PM', 'note': None}, {'row_id': 2, 'stage': 'EXECUTE', 'item': '구현 B', 'status': 'pending', 'status_label': '⬜', 'timestamp': None, 'owner': 'PM', 'note': None}], 'next_action': 'EXECUTE 구현 B 진입'}
=========================== short test summary info ============================
FAILED opal/tools/state-tool/tests/test_state_tool_run_log.py::TestOffModeInitByteIdentical::test_run_log_mode_off_init_matches_head_unflagged_byte_for_byte
FAILED opal/tools/state-tool/tests/test_state_tool_run_log.py::TestExistingRegressionBaseline::test_existing_suite_matches_baseline_and_frozen_files_untouched
FAILED opal/tools/state-tool/tests/test_state_tool_run_log.py::TestOffModeDurationPathByteIdentical::test_schema_1_0_mark_advance_match_head
FAILED opal/tools/state-tool/tests/test_state_tool_run_log.py::TestOffModeDurationPathByteIdentical::test_schema_1_1_mark_advance_match_head
4 failed, 489 passed, 3 skipped, 120 subtests passed in 303.93s (0:05:03)
```

## 배포본 sha256 (S-13 기준선)
```
bcc6f6ca3f95ac5a352f22b551fc626db5d2ac4e95a0c91401a66478b91845e4  /Users/iskang/.opal/tools/run-log-tool/run_log_core.py
05d3a1eef40c396261bcddf753ac5940ca7d63df2cb79f0dd96cc9466598386b  /Users/iskang/.opal/tools/state-tool/state_tool.py
```
