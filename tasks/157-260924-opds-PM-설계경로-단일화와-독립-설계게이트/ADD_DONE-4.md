# ADD_DONE-4: evaluator AGENT.md 기존 입력 행 원문 복원

| 필드 | 내용 |
|------|------|
| 추가작업 번호 | ADD-4 |
| 일시 | 2026-09-26 (완료 2026-09-26 09:14 KST) |
| 사유 | `opal-skill-tester` 등록 후 회귀를 넓게 돌리다 `oppb-runtime-tool/tests/test_pilot_isolation.py::test_evaluator_agent_existing_four_phases_survive` 실패를 발견했다. W-4가 evaluator AGENT.md 입력 표의 기존 `iteration`·`scenario_source` 행 문구를 고쳐 baseline 원문 보존 계약을 어겼다. 157 TEST S-11의 회귀 범위에 oppb-runtime-tool을 넣지 않아 누락됐다. |
| 변경 내용 | 두 행을 원문으로 복원하고 design-rubric용 `iteration (design-rubric)`·`scenario_source (design-rubric)` 행을 별도로 추가. design-rubric 본문·계약 필드는 불변. |
| 변경 파일 | `opal/agents/opal-evaluator-agent/AGENT.md` |
| 검증 결과 | `test_pilot_isolation.py` 13 passed, `test_design_gate.py` 20 passed. 도구 테스트 전체 재점검: 남은 실패(run-log-tool 2, tool-scan 5, state-tool TestT138W9 3과 이를 포함하는 run-log-tool 메타 테스트)는 허브 main에서 동일 재현되는 기존 결함. install exit 0. |
