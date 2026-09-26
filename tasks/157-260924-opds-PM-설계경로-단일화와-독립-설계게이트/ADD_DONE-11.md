# ADD_DONE-11: opst 보고서 수행 시간 표기를 최종 수행 시간으로 통일

| 필드 | 내용 |
|------|------|
| 추가작업 번호 | ADD-11 |
| 일시 | 2026-09-26 (완료 2026-09-26 15:32 KST) |
| 사유 | 캡틴 지시: 보고서의 "벽시계"를 "최종 수행 시간"으로 변경. `wall_min`은 테스트 세션 시작부터 종료까지 실제 경과 시간(TASK~CLOSE 전 과정)이므로 의미가 같다. |
| 변경 내용 | 같은 지표(`wall_min`)를 가리키던 "벽시계"(전체 지표)·"전체 소요"(비교·변화율·이력 추세)·"세션 전체"(단계 막대 제목)·REPORT.md "분" 열을 모두 "최종 수행 시간"으로 통일. 추세 경고 문구의 원시 키(`wall_min` 등)를 한글 라벨로 바꾸고 "기준"을 "최근 중앙값"으로 표기. 재판정 시 이력에 자기 자신과 이후 기록이 섞여 중앙값이 틀어지던 결함 수정(자기 source·실행 종료 이후 기록 제외). metrics.md 정의 문구 갱신. |
| 변경 파일 | `opal/skills/opal-skill-tester/{scripts/skill_tester.py,scripts/report_html.py,references/metrics.md}`, `tasks/157-…/skill-tests/**` |
| 검증 결과 | 기록 4건 재판정·refresh. opd 2차 경고가 "게이트 반복 최근 중앙값 1 → 3"으로 정상(수정 전 자기 포함으로 2.0). report.html에 "벽시계"·"전체 소요" 잔존 0. |
| 보완 | 이력 표 "소요(분)" 열도 "최종 수행 시간(분)"으로 통일. 캡틴 제보: Orca 내장 브라우저가 팝업을 지원하지 않아 이력 "열기" 링크(target=_blank)가 동작하지 않음 → 새 탭을 먼저 시도하고 window.open이 막히면 같은 탭으로 이동하도록 보완. 헤드리스 Chrome에서 정상(새 탭)·팝업 차단(같은 탭 이동) 두 경우 확인. |
| 보완 2 | Orca 브라우저 E2E(orca CLI tab/snapshot/click/eval): Orca는 window.open에 표시되지 않는 창 객체를 반환해 팝업 차단 감지 불가, UA도 일반 Chrome과 동일. 또한 페이지가 시작한 file:// → 다른 file:// 이동(링크·location.assign)을 차단(about:blank 이동은 허용, orca goto·tab create는 허용). 조치: 링크를 같은 탭 기본(일반 브라우저는 Cmd/Ctrl+클릭 새 탭)으로 바꾸고 '링크 복사' 버튼 추가 — Orca에서 복사 동작 확인(클립보드에 대상 file:// URL). Orca 안에서 링크 클릭 이동은 뷰어 정책상 불가로 남음. |
