# ADD_DONE-5: opal-skill-tester 신설

| 필드 | 내용 |
|------|------|
| 추가작업 번호 | ADD-5 |
| 일시 | 2026-09-26 (완료 2026-09-26 09:33 KST) |
| 사유 | 캡틴 지시: 모의 태스크로 스킬을 반복 검증할 수 있게, 시나리오를 추가·선택하고 단일 실행을 기본으로 비교도 할 수 있는 스킬을 `//opal-skill-creator`로 만들어 157 작업본에서 함께 merge. 157 비교 실험에서 단위 테스트를 통과한 결함 3건이 실제 실행에서만 드러난 것이 근거. |
| 변경 내용 | `opal/skills/opal-skill-tester/` 신설 — SKILL.md(절차·모드·판정), references/metrics.md(Pilot 지표 4범주: 결과·준수=합격 조건, 효율·재작업=기준 대비 경고, 판단 지점), references/scenario-spec.md(시나리오 규격), scripts/skill_tester.py(list/validate/run/report, 단일·비교·반복, 격리 저장소·타임아웃), scenarios/(공유 기반 `_bases/stockctl`, smoke-version-flag·function-stockctl-multiloc·judgment-negative-stock). 기반 저장소의 `.opal`·`.gitignore`는 `_opal`·`_gitignore`로 보관해 프로젝트 오인을 막는다. 소스 레지스트리(`opal-skills-registry.json` 3.21.0, alias ost)와 `docs/PROJECT.md` 등록. |
| 변경 파일 | `opal/skills/opal-skill-tester/**`, `opal/core/references/opal-skills-registry.json`, `docs/PROJECT.md` |
| 검증 결과 | validate --all 통과. 157 비교 실험 결과 재생 보고서가 수동 분석에서 찾은 결함 2건(worker 경로 커밋 0, PM 경로 run-log 적체와 첫 적체 사건)을 자동 검출. 숨은 테스트는 기반 원본에서 기능 테스트 실패 확인. 설치본 실측: `run smoke-version-flag`(기본 `//opds`) **PASS** — 숨은 테스트 2/2, 완료·상태검증·run-log 적체 0·게이트 증거·커밋 4, 19.0분·$9.72, 설계 게이트 2회(1회차 evaluator executability rewrite). 레지스트리 get·validate·match 정상, @header 신규 결손 0. |
