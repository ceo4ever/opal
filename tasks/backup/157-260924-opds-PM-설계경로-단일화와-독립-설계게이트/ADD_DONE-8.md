# ADD_DONE-8: opal-skill-tester 결과 tasks/ 기록과 약어 opst 변경

| 필드 | 내용 |
|------|------|
| 추가작업 번호 | ADD-8 |
| 일시 | 2026-09-26 (완료 2026-09-26 13:07 KST) |
| 사유 | 캡틴 지시: 테스트 결과를 `tasks/`에 채번 없이 `YYMMDD-{스킬명}-{태스크 제목}` 폴더로 기록하고, 작업 중 태스크가 있으면 그 폴더 아래에 둔다. 약어 ost를 opst로 변경. |
| 변경 내용 | 실행기에 `record` 명령과 run 종료 시 자동 기록 추가. 폴더명 `YYMMDD-opst-{대상 스킬}-{모드}-{시나리오 제목}`(`{스킬명}`은 기존 태스크 폴더 규칙대로 작업 수행 스킬 약어 opst로 해석). 위치: `--task-dir` 지정 시 `<태스크>/skill-tests/`, 미지정 시 진행 중 태스크가 정확히 하나면 그 아래, 아니면 `tasks/` 바로 아래. 기록 내용: REPORT.md·metrics.json·실행별 run/result/REQUEST·모의 태스크 핵심 산출물 사본·SOURCE.md. 모의 저장소는 중첩 git·가짜 .opal 프로젝트 방지를 위해 복사하지 않는다. 레지스트리 alias·트리거(미merge 3.21.0 항목 제자리 수정)·SKILL.md·README·PROJECT.md의 약어를 opst로 변경. opsdd 시나리오 제목에서 중복 "(opsdd)" 제거. |
| 변경 파일 | `opal/skills/opal-skill-tester/{SKILL.md,README.md,scripts/skill_tester.py,scenarios/smoke-opsdd-low-stock/scenario.json}`, `opal/core/references/opal-skills-registry.json`, `docs/PROJECT.md`, `tasks/157-…/skill-tests/**` |
| 검증 결과 | 기존 두 실행(opds·opsdd 스모크)을 `record --task-dir`로 157 아래 `skill-tests/260926-opst-opds-스모크-version-옵션-추가`·`260926-opst-opsdd-스모크-low-stock-명령-추가`에 기록(192KB, 모의 저장소 제외). 실행기 구문 검사, 레지스트리 JSON 유효, `ost` 잔존 0. |
