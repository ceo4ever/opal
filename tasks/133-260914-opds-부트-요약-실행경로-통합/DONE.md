# DONE: 부트 요약 실행 경로 통합

## 결과

프로젝트 부트 요약이 허브 `tasks/*`의 직접 수행 태스크와 worktree registry가 발급한 canonical `task_path`의 태스크를 함께 조회하도록 변경됐다. 후보는 진행 중·차단 상태만 최신순으로 최대 3건 표시하며, 나머지는 `other_count`와 `그 외 N건`으로 요약한다. registry 손상·경로 불일치·중복·모호성은 임의 경로 선택 없이 bounded anomaly로 분리한다.

기존 direct 태스크 조회, 입력 파일 read-only 경계, JSON·Markdown UTF-8 1,024바이트 상한은 유지됐다.

## 변경 파일

- `opal/tools/state-tool/state_tool.py`
- `opal/tools/state-tool/tests/test_state_tool.py`
- `opal/tools/state-tool/README.md`
- `opal/tools/event-loader/event_loader.py`
- `opal/tools/event-loader/tests/test_event_loader_extended.py`
- `opal/tools/event-loader/README.md`
- `tasks/133-260914-opds-부트-요약-실행경로-통합/TASK.md`
- `tasks/133-260914-opds-부트-요약-실행경로-통합/PLAN.md`
- `tasks/133-260914-opds-부트-요약-실행경로-통합/TEST-SCENARIO.md`
- `tasks/133-260914-opds-부트-요약-실행경로-통합/test-scenario.json`
- `tasks/133-260914-opds-부트-요약-실행경로-통합/GC-CONVENTION-2026-09-15T10-28.md`
- `tasks/133-260914-opds-부트-요약-실행경로-통합/gc-findings-convention-2026-09-15T10-28.json`

## 검증

- state-tool 전체 테스트: 414 PASS, 3 skip
- event-loader 전체 테스트: 17 PASS
- worktree-tool 회귀 테스트: 118 PASS
- TEST 시나리오: 8/8 PASS, FAIL·BLOCKED 0건
- 실제 허브 source→installed 동치: `boot-summary` 정규화 출력 동일, `project-brief` 바이트 동일
- 실제 허브 후보: 전체 7건, 공개 3건 + `other_count` 4건, anomaly 0건
- 출력 상한: `boot-summary` 421바이트, `project-brief` 564바이트
- state·registry·MEMORY 입력 SHA-256 불변
- 컨벤션 검사: Critical 0건, High 0건, blocking finding 0건
- `git diff --check`: PASS
- `state-tool validate`: 위반 0건
- 최신 `main` 통합 회귀: state-tool 414 PASS(3 skip), event-loader 17 PASS, worktree-tool 118 PASS
- 최신 `main` 실허브 통합 출력: `boot-summary` 542바이트, `project-brief` 649바이트, 복수 후보별 `mode/mode_source` 유지

## 회고적 학습 후보

.opal/brain/pages/concept/session-project-action-needed-briefing.md

## 참고

Task 134의 모드 지속성 변경과 Task 133의 다중 실행 경로 요약을 `main`에서 함께 검증했다. 설치본은 작업트리 snapshot이므로 `main` merge 완료 후 installer 재실행과 최종 source→installed 동치 확인이 필요하다.
