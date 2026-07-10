# ADD_DONE-1: test-tool scenario-red 서브명령

| 필드 | 내용 |
|------|------|
| 추가작업 번호 | ADD-1 |
| 일시 | 2026-07-10 17:57 ~ 18:37 (KST) |
| 사유 | 056 드라이런 발견 설계 갭 — red_confirmed를 증거 없이 init 시드로 선언 가능(self-confirming 경로). enforce-don't-advise 보강 필요 (AGENTIC-LOG #19) |
| 변경 내용 | `scenario-red --task-path --id --evidence` 신설(red_confirmed + red_evidence·red_at 갱신, locked 후 거부 exit 12 `scenario_already_locked`, evidence 필수). scenario-init의 red_confirmed 시드는 강제 false + warning 응답으로 무력화(기존 호출자 비파괴 — 하드 거부 대신 선택, 근거: 기존 fixture는 디스크 직접 조작 방식이라 양쪽 다 안전하나 stale JSON 재사용 호출자 보호). oppl SKILL T2 흐름·verification.md·harness §9(9서브명령) 정합 |
| 변경 파일 | opal/tools/test-tool/{lib/scenario.py, schema/test-scenario.schema.json, README.md(v1.2), tests/test_scenario.py(+4)} · opal/skills/opal-pilot-project-loop/{SKILL.md(v1.1), references/verification.md(v1.1)} · opal/core/references/opal-harness.md(v6.1) |
| 검증 결과 | RED 3 failed → GREEN 17/17. 전체 test-tool 스위트 회귀 0(기지 환경성 실패 1건 불변). 통합 256 passed. install 재배포 후 배포본 `scenario-red -h` 정상 |
