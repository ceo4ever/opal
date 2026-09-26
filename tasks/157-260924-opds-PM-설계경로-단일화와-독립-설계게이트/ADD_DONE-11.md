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
| 보완 2 | Orca 브라우저 E2E(orca CLI tab/snapshot/click/eval/screenshot): Orca는 페이지가 시작한 file:// → 다른 file:// 이동(링크·location.assign·팝업)을 차단하고, window.open에 표시되지 않는 창 객체를 반환하며 UA가 일반 Chrome과 같아 감지 불가. 조치: '새 탭 열기 ↗'(target=_blank, Chrome 새 탭 확인)를 유지하고, 모든 뷰어에서 동작하는 '상세 펼치기'(과거 실행 상세를 같은 페이지 행 아래에 펼침)와 '링크 복사' 버튼 추가. 검증: 헤드리스 Chrome 실제 클릭 시 원래 탭 유지 + 새 탭 열림, Orca에서 상세 펼치기 동작(스크린샷)·링크 복사 동작. |
| 보완 3 | 캡틴 지시: 이력의 'backup 위치' 링크 삭제. 아카이브(tasks/ → tasks/backup/)로 경로가 바뀌는 문제는 링크를 두 개 두는 대신 기록(record, run 자동 기록 포함) 끝에 모든 기록 report.html을 다시 만드는 refresh_all로 처리 — 이력은 매번 record.json을 다시 찾아 모으므로 링크가 현재 위치로 고쳐진다. report_alt_path 제거. 검증: 데모 프로젝트에서 기록 하나를 backup/으로 옮기자 다른 대시보드 링크가 MISSING, 새 기록 후 ../backup/… 로 고쳐져 exists. |
