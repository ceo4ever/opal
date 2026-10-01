# ADD_DONE-7: opal-skill-tester Pilot별 판정 프로필과 opsdd 스모크 시나리오

| 필드 | 내용 |
|------|------|
| 추가작업 번호 | ADD-7 |
| 일시 | 2026-09-26 (완료 2026-09-26 10:01 KST) |
| 사유 | 캡틴 요청 `//ost opsdd 스킬 테스트` — 카탈로그에 opsdd 시나리오가 없고, 실행기 준수 판정이 opd 계열(`execute.implement`·`test.pm_gate`·`test-scenario.json`)을 전제해 opsdd 결과를 오판할 수 있었다. 인터뷰 결과 "시나리오+실행기 보완, 스모크 모드" 선택. |
| 변경 내용 | 실행기에 `PROFILES`(opd·opds·opsdd)를 두어 게이트 증거 행과 단계 이정표를 Pilot별로 판정. 프로필 없는 Pilot은 "판정 프로필 없음"으로 불합격. 체크포인트 커밋은 worktree 태스크에만 요구(허브 작업본은 규칙상 무커밋). `run`은 변형이 시나리오 `target_pilots` 밖이면 `variant_not_targeted`로 거부, `validate`는 `target_pilots` 필수 검사. 시나리오 `smoke-opsdd-low-stock`(기본 변형 `//opsdd --agentic`, low-stock 명령, 숨은 테스트 3건) 추가. metrics.md·scenario-spec.md 갱신. |
| 변경 파일 | `opal/skills/opal-skill-tester/scripts/skill_tester.py`, `opal/skills/opal-skill-tester/references/metrics.md`, `opal/skills/opal-skill-tester/references/scenario-spec.md`, `opal/skills/opal-skill-tester/scenarios/smoke-opsdd-low-stock/**` |
| 검증 결과 | validate 4/4 통과, 새 숨은 테스트는 기반 원본에서 기능 2건 실패·기존 테스트 통과, `//opd` 변형은 `variant_not_targeted` 거부, 기존 스모크 결과 재판정 정상(profile=opds). opsdd 실제 실행은 캡틴 최종 확인 후 수행. |
