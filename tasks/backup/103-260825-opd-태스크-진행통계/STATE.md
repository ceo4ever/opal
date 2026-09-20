# STATE: OPAL Console 태스크 진행 통계

> 최종 갱신: 2026-08-26 16:07:26
> 파이프라인 현황(rows/상태/다음 액션)의 SSOT는 `state.json`입니다.
> 조회: `~/.opal/tools/state-tool/run.sh show <task-path>`

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|
| 1 | 2026-08-25 20:42 | additional row inserted after row 13: stage=EXECUTE, item=3계열 분해 확장 (캡틴 지시), key=execute.three_series, new_row_id=14 | 캡틴 지시 2026-08-25 18:30 — 단계 소요를 총/PM/워커/사용자 4계열로 분해 |
| 2 | 2026-08-25 20:42 | additional row inserted after row 13: stage=TEST, item=3계열 재검증, key=test.three_series_verify, new_row_id=14 | 캡틴 지시 2026-08-25 18:30 — 단계 소요를 총/PM/워커/사용자 4계열로 분해 |
| 3 | 2026-08-25 21:52 | additional row inserted after row 14: stage=EXECUTE, item=시각 표기 YY-MM-DD HH:mm:ss (캡틴 지시), key=execute.timestamp_format, new_row_id=15 | 캡틴 지시 2026-08-25 21:55 — A-3·A-4 시각이 HH:MM만 표시해 날짜 경계가 사라짐(실측: 20:02 다음 행이 10:35로 역행처럼 보임). 표시 포맷을 YY-MM-DD HH:mm:ss로 교체 + 원천 초 기록 |
| 4 | 2026-08-25 23:40:22 | additional row inserted after row 16: stage=EXECUTE, item=차트 호버 툴팁 (캡틴 지시), key=execute.chart_tooltip, new_row_id=17 | 캡틴 지시 2026-08-25 23:40 — 차트에 마우스를 올리면 해당 지표를 표시. 단계·워크플로우 층 3계열 라벨(BE) + A-2·B-2·B-3 툴팁(FE) |
| 5 | 2026-08-26 10:36:50 | additional row inserted after row 17: stage=EXECUTE, item=워커 소요 기록 규범화 (캡틴 지시), key=execute.worker_duration_norm, new_row_id=18 | 캡틴 지시 2026-08-26 08:20 — 산문 3곳(opal-harness.md §3 · pm-review-gate.md 워커 완료 선언 · 동 표준 검토 항목/자가 진단) + 도구 경고 1곳(state_tool.py --as-worker 시 --worker-duration-minutes 누락 경고) |
| 6 | 2026-08-26 14:26:19 | additional row inserted after row 18: stage=EXECUTE, item=야간 시간대 보정 (캡틴 지시), key=execute.quiet_hours, new_row_id=19 | 캡틴 지시 2026-08-26 — 00~09시를 소요 계산에서 제외. setting.json 2층 머지로 시간대 변경 가능. 기본 켬. 실측 영향: opd 중앙 799->425(-47%), 101은 425 불변 |
| 7 | 2026-08-26 15:15:52 | additional row inserted after row 19: stage=EXECUTE, item=워커 기록 강제 2단 (캡틴 지시), key=execute.worker_enforce, new_row_id=20 | 캡틴 지시 2026-08-26 — '반드시 적용되게'. 산문·경고만으로는 우회됨(mams 173에서 15행 전건 미기록 실증). 조기 경고(워커 디스패치 규범 단계를 owner=PM으로 닫을 때) + CLOSE 차단(미선언 잔존 시 거부, --worker-duration-unknown 명시로만 통과) 2단 |

## 블로커
없음
