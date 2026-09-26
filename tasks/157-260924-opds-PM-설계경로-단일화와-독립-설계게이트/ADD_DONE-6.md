# ADD_DONE-6: opal-skill-tester 인터뷰 절차

| 필드 | 내용 |
|------|------|
| 추가작업 번호 | ADD-6 |
| 일시 | 2026-09-26 (완료 2026-09-26 09:40 KST) |
| 사유 | 캡틴 지시: `//ost opds 스킬 테스트 해줘`처럼 조건이 빠진 요청은 모드·시나리오 등을 사용자 인터뷰로 정한 뒤 진행. 기존 SKILL.md는 "목적에 맞는 모드를 권한다"까지만 정해져 있어 질문 방식이 실행마다 달라질 수 있었다. |
| 변경 내용 | SKILL.md 절차를 4단계(인터뷰 → 최종 확인 → 사전 점검·실행 → 보고)로 재구성. 요청에 없는 항목(대상 스킬·단일/비교·모드·시나리오·반복)만 선택지형으로 묻고 권장안을 첫 선택지로 두며 최대 2라운드로 끝낸다. 실행 전에는 시나리오·세션 수·예상 시간과 비용 요약을 항상 한 번 확인받는다. 대상 스킬 시나리오가 없으면 실행하지 않고 시나리오 추가를 묻는다. 보고 후 기준 결과가 없으면 저장 여부를 묻고, 이를 위해 실행기 `report --save-baseline` 추가. README에 대화형 사용 방식 반영. |
| 변경 파일 | `opal/skills/opal-skill-tester/SKILL.md`, `opal/skills/opal-skill-tester/README.md`, `opal/skills/opal-skill-tester/scripts/skill_tester.py` |
| 검증 결과 | 실행기 구문 검사 통과, 스모크 실행 폴더로 `report` 재생성 정상(baseline_saved=false). SKILL.md 93줄. |
