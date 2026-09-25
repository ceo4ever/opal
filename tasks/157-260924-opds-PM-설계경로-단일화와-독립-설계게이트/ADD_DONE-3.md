# ADD_DONE-3: Findings 코드 표기를 경로로 오인하는 결정론 검사 수정

| 필드 | 내용 |
|------|------|
| 추가작업 번호 | ADD-3 |
| 일시 | 2026-09-26 (완료 2026-09-26 00:12 KST) |
| 사유 | opd 비교 실험 PM 경로 세션의 설계 게이트 1회차가 PLAN Findings 안의 코드 표기 `os.replace`를 파일 경로로 읽어 `regression target listed as change`·`finding not in work items`로 실패했다. 오탐으로 반복 상한 3회 중 1회를 소모했다. |
| 변경 내용 | Findings 백틱 토큰은 `/`를 포함하거나 마지막 확장자가 알려진 파일 확장자(py md json js ts tsx jsx yaml yml toml sh txt csv html css sql cfg ini)일 때만 경로로 판정한다. 기존 경로 판정과 안전 토큰 검사는 유지. design-gate.md 결정론 검사 설명과 plan-guide PM 경로 Findings 규칙에 기준 한 줄 추가. |
| 변경 파일 | `opal/tools/state-tool/state_tool.py`, `opal/tools/state-tool/tests/test_design_gate.py`, `opal/core/references/harness/design-gate.md`, `opal/skills/op-dev-plan/references/plan-guide.md` |
| 검증 결과 | RED: 신규 `test_add3_findings_code_token_not_treated_as_path` (a) 오탐 실패, (b)(c) 기존 판정 유지 통과(`run/test-evidence/add3-red.txt`). GREEN: 20 passed, state-tool 신규 실패 0(기존 TestT138W9 3건만). 비교 실험의 실제 PLAN 재파싱 시 `os.replace` 제외, 실제 경로만 추출. install exit 0, 소스·설치본 일치. |
