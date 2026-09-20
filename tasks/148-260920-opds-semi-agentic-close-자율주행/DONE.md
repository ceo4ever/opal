# DONE: semi-agentic 구현 이후 CLOSE 자율주행

## 결과

`state-tool`의 CLOSE 진입 판정을 공통 mode-aware 계약으로 통합했다. `semi-agentic`은 PLAN-equivalent 사용자 검토 뒤, `agentic`은 정상 전 구간에서 미해결 이슈가 없으면 CLOSE 직전 확인 행을 자동 승인하고 `close.final`까지 `progress_report + continue`로 진행한다. `interactive`와 invalid mode의 fail-closed 사용자 승인, 실제 blocker, 사람 전용 검증, 외부 Git·배포·worktree 권한 경계는 유지했다.

공통 하네스와 적용 대상 Pilot 문서를 새 계약으로 정합화했으며, 프로젝트 로컬 PM 프로필의 이전 “semi-agentic CLOSE 승인 필수” 기준도 승인된 새 정책으로 동기화했다. 기존 pipeline 행·`state.json` 스키마는 변경하지 않았다.

## 변경 파일

- `.opal/AGENT.md`
- `README.md`
- `docs/CONVENTIONS.md`
- `opal/core/references/harness/guards.md`
- `opal/core/references/harness/modes.md`
- `opal/core/references/harness/pm-review-gate.md`
- `opal/core/references/harness/state.md`
- `opal/core/references/opal-harness-agentic.md`
- `opal/core/references/opal-harness-interactive.md`
- `opal/core/references/opal-harness-semi-agentic.md`
- `opal/skills/opal-pilot-data-design/SKILL.md`
- `opal/skills/opal-pilot-dev-short/README.md`
- `opal/skills/opal-pilot-dev-short/SKILL.md`
- `opal/skills/opal-pilot-dev-wireframe/README.md`
- `opal/skills/opal-pilot-dev-wireframe/SKILL.md`
- `opal/skills/opal-pilot-dev/README.md`
- `opal/skills/opal-pilot-dev/SKILL.md`
- `opal/skills/opal-pilot-gc/SKILL.md`
- `opal/skills/opal-pilot-project-dev/SKILL.md`
- `opal/skills/opal-pilot-project-loop/SKILL.md`
- `opal/skills/opal-pilot-project/README.md`
- `opal/skills/opal-pilot-project/SKILL.md`
- `opal/skills/opal-pilot-sdd/README.md`
- `opal/skills/opal-pilot-sdd/SKILL.md`
- `opal/skills/opal-pilot-write-tech/SKILL.md`
- `opal/tools/state-tool/README.md`
- `opal/tools/state-tool/state_tool.py`
- `opal/tools/state-tool/tests/test_mode_resolution.py`
- `opal/tools/state-tool/tests/test_mode_transition_contract.py`
- `opal/tools/state-tool/tests/test_state_tool.py`
- `tasks/148-260920-opds-semi-agentic-close-자율주행/`

## 검증

- `test-scenario.json`: S-1~S-7 모두 PASS, FAIL/BLOCKED 0건
- state-tool 단위·전이 테스트: 447 passed, 3 skipped, failure 0건
- Pilot shared contract: 20/20 PASS
- 설치 대상 source↔`~/.opal` parity: 24/24 일치
- 설치본 공개 CLI matrix: 12/12 PASS — 3개 모드 × opds/opgc × `advance`/`mark`, 확인 행 유무와 `close.final` 포함
- 이 태스크의 실제 CLOSE 진입: TEST 사용자 확인 행 자동 승인 후 `continue/progress_report` 확인
- code-scan 변경분: 4/4 covered, 100%, `newly_uncovered` 0건
- 독립 컨벤션 진단: Critical/High/Medium 0건, 비차단 Low advisory 17건
- `state-tool validate`, PLAN contract, code-scan citation, `py_compile`, `git diff --check`: 모두 통과

## 회고적 학습 후보

.opal/brain/pages/concept/mode-aware-execution-continuity-contract.md

## 참고

- `scripts/install-mac.sh`는 관련 자산 배포와 frontend build 뒤 장시간 무출력 상태여서 종료했으나, 이번 태스크의 설치 대상 24개 parity와 설치본 CLI 동작을 별도로 전수·행렬 검증했다.
- 허브·기본 브랜치 commit/merge/push, rebase/reset/amend, worktree 제거는 수행하지 않았다.
