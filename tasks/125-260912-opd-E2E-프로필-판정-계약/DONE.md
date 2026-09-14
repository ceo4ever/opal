# DONE: E2E profile·verdict 계약 도입

## 결과

`test-tool`에 E2E profile·verdict의 단일 계약 owner를 도입했다. 공개 표면에 따라
Browser·API·Hybrid·Collaborative·Manual profile을 판정하고, 실행 결과는 `pass`,
`fail`, `executor_unavailable`, `infra_error`, `blocked`의 final status와
`awaiting_human` operational status를 손실 없이 보존한다. Browser 후보 내부의
`provider_unavailable`은 다른 후보를 시도할 수 있는 경우에만 소비하고, 후보 소진 뒤에는
`executor_unavailable`로 확정한다.

시나리오 v2 계약은 executor, assertion의 expected/actual, required/observed evidence,
구조화 handoff 8필드를 검증한다. assertion 또는 필수 증적이 빠진 결과는 `pass`나
`real-usage`로 승격되지 않으며, 사람의 제출도 resume token과 구조화 verifier를 통과한
뒤에만 final status가 된다. 기존 v1 시나리오와 과거 cmux 결과는 명시적 legacy
normalizer로 읽되 신규 출력에서는 generic fallback/escalation 키를 만들지 않는다.

기존 project→global→infer 설정 우선순위, scenario-rubric의 별도 `escalate` 판정,
비E2E QA 계약은 유지했다. Runtime Manager, 실제 Browser/API/Human executor,
서버·포트·세션 수명주기와 Playwright 제거는 구현하지 않았다.

## 변경 파일

- `docs/ARCHITECTURE.md`
- `docs/PROJECT.md`
- `opal/agents/opal-loop-action-agent/AGENT.md`
- `opal/agents/opal-task-action-agent/AGENT.md`
- `opal/agents/opal-test-agent/AGENT.md`
- `opal/core/references/test-tools-schema.yaml`
- `opal/core/references/tools.md`
- `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md`
- `opal/skills/opal-pilot-dev-short/SKILL.md`
- `opal/skills/opal-pilot-dev/SKILL.md`
- `opal/skills/opal-pilot-project-dev/SKILL.md`
- `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md`
- `opal/skills/opal-pilot-project-loop/SKILL.md`
- `opal/skills/opal-pilot-project-loop/references/journey-flow.md`
- `opal/skills/opal-pilot-project-loop/references/verification.md`
- `opal/templates/test-tools.yaml`
- `opal/tools/test-tool/README.md`
- `opal/tools/test-tool/lib/e2e_adapter.py`
- `opal/tools/test-tool/lib/e2e_contract.py` (신설)
- `opal/tools/test-tool/lib/resolver.py`
- `opal/tools/test-tool/lib/scenario.py`
- `opal/tools/test-tool/schema/test-scenario.schema.json`
- `opal/tools/test-tool/test_tool.py`
- `opal/tools/test-tool/tests/test_e2e_contract.py` (신설)
- `opal/tools/test-tool/tests/test_scenario.py`
- `opal/tools/test-tool/tests/test_test_tool.py`
- `tasks/125-260912-opd-E2E-프로필-판정-계약/`

## 검증

- 소스 전체 단위 테스트: 84/84 통과
- fresh isolated copy 전체 단위 테스트: 84/84 통과
- 소스·격리본 핵심 파일 SHA-256: 6/6 일치
- 상태별 CLI exit: pass 0, fail 6, infra_error 7, executor_unavailable 18,
  blocked 19, awaiting_human 20 일치
- v2 루트 `task_id` 누락: exit 17, `scenario_contract_invalid` 확인
- TEST 시나리오: 11/11 PASS, FAIL/BLOCKED/awaiting_human 0건
- fidelity gate: 11/11 충족, conformance gate: 적용 대상 없음으로 정상 통과
- Python compile·YAML/JSON/Draft7 schema·`git diff --check`: 통과
- code-scan: 변경 Python 8개 coverage 100%, violation 0건
- 컨벤션 재검사: 신규·회귀 finding 0건, blocking regression 0건. HEAD에 동일한
  기존 finding 10건은 태스크 회귀와 분리

## 회고적 학습 후보

.opal/brain/pages/concept/e2e-profile-verdict-contract.md
.opal/brain/pages/entity/test-tool.md
.opal/brain/pages/concept/e2e-cmux-first-playwright-fallback.md

## 참고

- `docs/proposals/opal-e2e-harness.md`가 제시한 9개 독립 태스크 중 첫 번째 계약만
  구현했다. 나머지 범위가 남아 있으므로 제안서는 `검토` 상태로 유지하고 아카이브하지
  않았다.
- S-7의 `real-usage`는 구조화된 결정론 fixture에 대한 계약 검증이며 실제 Human
  executor 연동 증거가 아니다.
- 브랜치 `feat/OP-TASK-125`는 머지 대기 상태다. 커밋·머지와 worktree 제거는 소유자
  권한이므로 CLOSE에서 수행하지 않는다.
