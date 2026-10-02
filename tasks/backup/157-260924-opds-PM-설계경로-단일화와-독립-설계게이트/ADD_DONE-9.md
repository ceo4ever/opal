# ADD_DONE-9: opal-skill-tester HTML 대시보드 보고서와 스킬별 이력 탭

| 필드 | 내용 |
|------|------|
| 추가작업 번호 | ADD-9 |
| 일시 | 2026-09-26 (완료 2026-09-26 13:38 KST) |
| 사유 | 캡틴 지시: 보고서를 HTML 대시보드로 비주얼하게 만들고, 단일 실행은 요약(A)+이력(C), 비교 실행은 비교(B)+이력(C)을 하나로 합쳐 탭별로 해당 스킬 테스트 이력을 본다. 과거 대시보드를 새 탭 링크로 열어 비교하고, 오래된 태스크가 `tasks/backup/`으로 아카이브되는 것을 고려한다. |
| 변경 내용 | `scripts/report_html.py` 신설 — 단일 실행 탭 `요약`·`이력: <변형>`, 비교 실행 탭 `비교`·`상세: <변형>`·`이력: <변형>`. 요약은 5축(완성도·속도·비용 효율·자기 교정력·자율성) 카드, 단계별 소요 막대·표(이력 중앙값 대비 개선/악화, 단계별 GATE·ERROR·FIX·DECISION), 자기 교정 기록, 전체 지표. 이력은 같은 변형·시나리오 추세 차트(최근 3회 중앙값 대비)와 같은 스킬 전 시나리오 기록 표, 과거 대시보드 새 탭 링크(현재 위치 + backup/원래 위치). URL `#탭id`로 탭 직접 열기. 실행기: 기록 폴더에 `record.json`·`report.html` 생성, `tasks/`·`tasks/backup/` 전체 `record.json`에서 이력 수집(`collect_history`), 아카이브 후 링크 갱신용 `refresh` 명령, 수집 지표 확장(단계별 소요·단계별 로그 수·교정 기록·결정 요청 수·실행 시점 프레임워크 지문). `baseline.json`·`--save-baseline` 제거(이력 중앙값으로 대체). SKILL.md·README·metrics.md·scenario-spec.md 갱신. |
| 변경 파일 | `opal/skills/opal-skill-tester/{SKILL.md,README.md,scripts/skill_tester.py,scripts/report_html.py,references/metrics.md,references/scenario-spec.md}`, `tasks/157-…/skill-tests/**` |
| 검증 결과 | 기존 기록 2건을 새 형식으로 재수집·backfill(프레임워크 지문은 도입 전 실행이라 "기록 없음"), `refresh` 2건 생성. 가상 이력 프로젝트(`tasks/` 3건 + `tasks/backup/` 1건 + 비교 1건)에서 `refresh` 5건, 요약·이력·비교 탭 스크린샷 확인(추세 -9% 개선 표시, backup 기록 링크 "원래 위치" 표시, 0% 변화 중립 표시). list·validate 정상, 구문 검사 통과. |
