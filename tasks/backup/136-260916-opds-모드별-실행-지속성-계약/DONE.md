# DONE: 모드별 실행 지속성 계약

## 결과

`interactive`, `semi-agentic`, `agentic` 모드가 공통 전이 어휘(`continue`, `await_user`, `blocked`, `complete`)와 구조화된 `transition_action`·`report_type`·`next_action`을 사용하도록 실행 지속성 계약을 통합했다. 진행 보고와 사용자 결정 요청을 분리했으며, agentic 실행은 실제 차단 조건과 CLOSE 승인 경계를 제외하면 다음 단계로 계속 진행한다.

모든 Pilot pipeline에 명시적인 CLOSE 꼬리 단계를 추가해 `close.final` 이후에만 완료되도록 했고, 기존 단일 CLOSE 행 태스크는 레거시 재개 경로로 보존했다. Claude Stop hook은 활성 태스크의 다음 전이가 `continue`일 때 조기 종료를 차단하며, macOS·Windows 설치 경로가 사용자 hook 설정을 보존하면서 이를 병합한다.

## 변경 파일

- `docs/ARCHITECTURE.md`
- `docs/CONVENTIONS.md`
- `docs/PROJECT.md`
- `opal/core/hooks/claude-hooks.json`
- `opal/core/references/harness/modes.md`
- `opal/core/references/harness/state.md`
- `opal/core/references/harness/task-process.md`
- `opal/core/references/opal-harness-agentic.md`
- `opal/core/references/opal-harness-interactive.md`
- `opal/core/references/opal-harness-semi-agentic.md`
- `opal/skills/opal-pilot-data-design/SKILL.md`
- `opal/skills/opal-pilot-data-design/references/pipeline.json`
- `opal/skills/opal-pilot-dev-short/SKILL.md`
- `opal/skills/opal-pilot-dev-wireframe/SKILL.md`
- `opal/skills/opal-pilot-dev-wireframe/references/pipeline.json`
- `opal/skills/opal-pilot-dev/SKILL.md`
- `opal/skills/opal-pilot-dev/references/pipeline-short.json`
- `opal/skills/opal-pilot-dev/references/pipeline.json`
- `opal/skills/opal-pilot-dev/references/track-escalation.md`
- `opal/skills/opal-pilot-dev/references/track-routing.md`
- `opal/skills/opal-pilot-gc/SKILL.md`
- `opal/skills/opal-pilot-gc/references/pipeline.json`
- `opal/skills/opal-pilot-project-dev/SKILL.md`
- `opal/skills/opal-pilot-project-dev/references/pipeline.json`
- `opal/skills/opal-pilot-project-loop/SKILL.md`
- `opal/skills/opal-pilot-project-loop/references/pipeline.json`
- `opal/skills/opal-pilot-project/SKILL.md`
- `opal/skills/opal-pilot-project/references/pipeline.json`
- `opal/skills/opal-pilot-sdd/SKILL.md`
- `opal/skills/opal-pilot-sdd/references/pipeline.json`
- `opal/skills/opal-pilot-write-tech/SKILL.md`
- `opal/skills/opal-pilot-write-tech/references/pipeline.json`
- `opal/tools/state-tool/README.md`
- `opal/tools/state-tool/schema/state.schema.json`
- `opal/tools/state-tool/state_tool.py`
- `opal/tools/state-tool/tests/test_mode_transition_contract.py`
- `opal/tools/state-tool/tests/test_state_tool.py`
- `scripts/install/windows.ps1`
- `scripts/tests/task134_mode_persistence_contract.py`
- `scripts/tests/task136_mode_transition_contract.py`
- `scripts/tests/test_agent_adapter_fields.sh`
- `scripts/tests/test_archive_contents.sh`
- `tasks/136-260916-opds-모드별-실행-지속성-계약/`

## 검증

- `test-scenario.json`: S-1~S-7 모두 PASS, FAIL/BLOCKED 0건
- `python3 opal/tools/state-tool/tests/test_state_tool.py`: 385 passed, 3 skipped
- `python3 opal/tools/state-tool/tests/test_mode_transition_contract.py -v`: 5 passed
- `python3 scripts/tests/task134_mode_persistence_contract.py`: 5 passed
- `python3 scripts/tests/task136_mode_transition_contract.py -v`: 3 passed
- `scripts/tests/test_agent_adapter_fields.sh`: PASS 18, FAIL 0
- `scripts/tests/test_archive_contents.sh`: PASS 12, FAIL 0
- 10개 Pilot pipeline `spec-validate`: 모두 `ok=true`, violation 0건
- `code-scan validate --changed ... --json`: 커버리지 100%, 차단 위반 0건
- 독립 컨벤션 재검사: Critical/High/Medium 0건, 기존 헤더 이력 관련 Low advisory 1건
- `py_compile`, `bash -n`, `jq empty`, `git diff --check`: 모두 통과
- `brain-tool add-page/index/log`: `pages/concept/mode-aware-execution-continuity-contract.md` ingest 완료

## 회고적 학습 후보

.opal/brain/pages/concept/mode-aware-execution-continuity-contract.md

## 참고

- PowerShell 런타임이 없어 Windows 스크립트 직접 실행은 생략했으며, source contract 및 archive/install 경계 테스트로 검증했다.
- 소스·태스크 변경의 사용자 커밋과 merge는 수행하지 않았다. CLOSE의 필수 `worktree-tool finalize`가 brain 귀속 전용 커밋 `54fb7b8`을 생성했으며, worktree는 나머지 변경 커밋과 사용자 merge를 기다린다.
