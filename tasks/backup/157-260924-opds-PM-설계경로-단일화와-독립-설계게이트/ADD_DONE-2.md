# ADD_DONE-2: design-decision activity 사건 data 형식 수정

| 필드 | 내용 |
|------|------|
| 추가작업 번호 | ADD-2 |
| 일시 | 2026-09-25 (완료 2026-09-25 09:13 KST) |
| 사유 | opd 비교 실험의 PM 경로 세션에서 run-log pending 32건과 `log-event` 거부가 발생했다. 첫 막힌 사건은 `design-decision --scope detail`의 PM activity 사건으로, `data`가 문자열 `"decision"`이었다. 계약은 `{"kind": "decision"}` 객체라 기록 코어가 거부했고, drain이 첫 실패에서 멈춰 이후 사건이 모두 적체됐다. S-8 테스트가 run-log 반영을 단언하지 않아 TEST에서 놓쳤다. |
| 변경 내용 | `cmd_design_decision` detail 분기가 `_build_pm_activity_event`에 `kind={"kind": "decision"}`을 넘기도록 수정(+2/-1). external 분기는 state.changed 사건이라 무관. |
| 변경 파일 | `opal/tools/state-tool/state_tool.py`, `opal/tools/state-tool/tests/test_design_gate.py` |
| 검증 결과 | RED: 신규 `test_add2_design_decision_detail_commits_activity`가 pending 1건·`data: 'decision'`로 실패(`run/test-evidence/add2-red.txt`). GREEN: 19 passed, state-tool 신규 실패 0(기존 TestT138W9 3건만). install exit 0, 설치본 state_tool.py 소스와 일치. 홈 스캔 `find` 정지는 감시 로직이 이 install 하위 프로세스만 종료. |
