# ADD_DONE-1: evaluator 결과 재사용 차단

| 필드 | 내용 |
|------|------|
| 추가작업 번호 | ADD-1 |
| 일시 | 2026-09-25 (완료 2026-09-25 08:06 KST) |
| 사유 | 모의 태스크 M4에서 1회차 evaluator pass 결과 JSON을 PLAN 수정 뒤 2회차 기록에 그대로 넣어도 `design-gate record`가 pass로 수용했다. 기록 도구가 결과가 현재 문서의 판정인지 대조하지 않아, 검증되지 않은 설계가 EXECUTE에 들어갈 수 있었다. |
| 변경 내용 | `design-gate start` 응답의 `bundle_hash`를 op-scenario-gate가 evaluator 입력 `input_bundle_hash`로 전달하고, evaluator `design-rubric`은 결과 최상위에 `input_bundle_hash`·`iteration`을 그대로 반환한다. `record`는 pass·rewrite일 때 두 값이 현재 열린 시도와 다르거나 없으면 `design_gate_result_stale`로 거부하고 상태를 바꾸지 않는다(input_error 제외). 검사 순서: 열린 시도·회차 → 문서 묶음 변경 → stale → 축 필수 → pass 재계산. |
| 변경 파일 | `opal/tools/state-tool/state_tool.py`, `opal/tools/state-tool/README.md`, `opal/tools/state-tool/tests/test_design_gate.py`, `opal/core/references/harness/design-gate.md`, `opal/skills/op-scenario-gate/SKILL.md`, `opal/agents/opal-evaluator-agent/AGENT.md` |
| 검증 결과 | RED: 신규 `test_add1_stale_evaluator_result_rejected` 실패 관찰(기존 17건 pass, `run/test-evidence/add1-red.txt`). GREEN: `test_design_gate.py` 18 passed, state-tool·start_resolution·event-loader 합계 65 passed, state-tool 전체에서 신규 실패 0(기존 TestT138W9 세션 env 3건만), event-loader static-check ok. 모의 재현: 1회차 결과를 2회차에 재사용하면 `design_gate_result_stale`. install exit 0, 소스·설치본 sha256 일치(op-scenario-gate SKILL.md는 install의 변경이력 절 제거 변환만 차이). install의 콘솔 스캔 `find`가 다시 정지해 이 세션 소유 프로세스만 종료했고 worktree `dashboard/frontend/dist`를 정리했다. |
