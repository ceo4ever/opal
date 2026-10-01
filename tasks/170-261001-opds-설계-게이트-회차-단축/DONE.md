# DONE: 설계 게이트 회차 단축

## 결과

PM 경로(`coordinator` 신규 opd/opds) 설계 게이트의 회차 소비 구조를 바꿨다. 결정론 검사(값싸고 빠름)와 evaluator 판정(비싸고 느림, 회차 소비) 두 티어를 분리해, evaluator를 부르기 전에 `state-tool verify --design-gate-check`로 결정론 ①~⑦ 전체와 decision_clarity 유보 어휘 후보를 회차·상태 소비 없이 미리 점검할 수 있게 했다. evaluator의 `design-rubric` 판정 자체(설계 4축·시나리오 3축·pass 조건·반복 상한 3회)는 바꾸지 않았다.

- `verify --design-gate-check`: 기존 `_design_gate_deterministic_check`를 그대로 재사용하고, 신규 `_decision_clarity_lint`로 "추후 결정"·"적절히"·"필요시" 등 고정 패턴 12개를 펜스 코드/인라인 코드 제외 산문에서만 스캔해 후보 위치만 반환한다(판정 아님, 그 자체로 unmet을 만들지 않음).
- PM 경로 절차(`opal-pilot-dev/SKILL.md`)에 이 사전점검 실행과 decision_clarity 자가점검 기준, "새 메커니즘은 같은 회차에 TEST-SCENARIO도 갱신" 규칙을 명문화했다.
- evaluator(`opal-evaluator-agent`)의 `design-rubric` 결과 계약에 `previous_gaps`(직전 유효 회차 gaps) 입력과 `resolved_gaps`(전건 resolved/unresolved 보고) 출력을 추가해, 다음 회차가 이전 지적의 해소 여부를 명시적으로 보고하게 했다. `op-scenario-gate` SKILL이 `previous_gaps` 조회·전달과 `resolved_gaps` id-완전성 검증(불일치 시 `input_error`)을 수행한다.
- gaps 항목 포맷을 `{axis}-{n}: {위치} — {남은 선택}`으로 의무화했다(design·scenario 공통, 정규식 `^[\w_]+-\d+: .+ — .+`).
- evaluator model·effort 평가 세트(8사례: pass 3 + 합성 결함 5) 측정 결과, baseline(effort 미지정)이 xhigh 대비 결함 탐지력은 동일하면서 6배 빠르고 이미 승인된 설계를 불필요하게 재심사하지 않았다 — baseline 유지를 캡틴이 결정했다. `effort: default` 센티넬을 frontmatter에 명시해 "조정 가능한 설정값, 현재는 기본값"임을 소스에 남겼다(install-mac.sh의 미정의 effort 값 omit 정책으로 배포본에는 영향 없음).

**유지된 기존 동작**: 설계 4축·시나리오 3축 판정 기준, 반복 상한 3회와 `reset --owner user` 전용 해제 정책, 기존 5개 `verify` 게이트 플래그, evaluator의 Phase 1~3(Base 루브릭·CONTRACT 병합)과 다른 4개 phase(design-review/spec-review/drift-recheck/scenario-rubric/acceptance)는 전부 무변경.

**적용 경계**: 이번 변경은 PM 경로(`plan.design_gate` 행이 있는 opd/opds `coordinator` 신규 태스크)에만 적용된다. 범위 밖으로 결정된 "evaluator 디스패치 scope 병렬 분리"는 시도했으나 3회 전부 rewrite로 반복 상한에 도달해 철회했다 — 후속 태스크로 재검토한다(AGENTIC-LOG #9, §범위 밖 제안).

## 변경 파일

- `opal/tools/state-tool/state_tool.py` — `verify --design-gate-check` 플래그, `_decision_clarity_lint()`
- `opal/skills/opal-pilot-dev/SKILL.md` — PM 경로 절차에 사전점검·decision_clarity 자가점검·TEST-SCENARIO 동시 갱신 규칙 추가
- `opal/core/references/harness/design-gate.md` — `verify --design-gate-check`가 같은 결정론 검사를 회차 비소비로 재사용함을 명시
- `opal/skills/op-dev-plan/references/plan-guide.md`, `opal/skills/op-dev-test-scenario/SKILL.md` — 교차 참조 1문장씩 추가
- `opal/agents/opal-evaluator-agent/AGENT.md` — `previous_gaps` 입력, gaps 포맷 규약, `resolved_gaps` 완전성 요건·출력 필드, `effort: default` 추가
- `opal/skills/op-scenario-gate/SKILL.md` — `previous_gaps` 조회·전달, `resolved_gaps` id-완전성 검증(`input_error`)
- `tasks/170-261001-opds-설계-게이트-회차-단축/run/EVAL-RESULT.md` — evaluator model·effort 평가 세트 측정 결과(신규)

## 검증

- `state-tool verify --design-gate-check`: 결정론 실패 재현 fixture로 `uncovered requirement AC-2` 동일 재현, 회차·상태 불변 확인(S-1)
- `opal-test-agent` 디스패치로 S-1~S-12(S-2b 포함, 13건) 실행 — `test-scenario.json` 13/13 PASS
- S-6(previous_gaps→resolved_gaps 왕복)은 워커 디스패치 불가 정책(PLAN Decisions)에 따라 PM이 직접 전용 fixture 태스크에서 2회차 실제 round-trip 수행 — resolved_gaps id 집합이 previous_gaps id 집합과 정확히 일치, gaps 포맷 정규식 전건 통과 확인
- S-9(evaluator model·effort 평가): 8사례×2후보(baseline/xhigh) 16회 실제 디스패치, baseline 8/8 verdict 일치·결함 누락 0·평균 52초 vs xhigh 6/8 일치·결함 누락 0·평균 320초
- S-12(C-4, 태스크 168과의 비충돌): 실제 `main` merge(커밋 `9ac1a453`) 완료로 확인, conflict marker 없음
- 전체 회귀: `/Users/lucas/.opal/.venv/bin/python -m pytest opal/tools/state-tool/tests/` 629 passed / 3 skipped / 2 failed — 실패 2건은 `CLAUDE_CODE_SESSION_ID`가 항상 설정되는 실제 세션 환경 특성이며, `git diff main...feat/OP-TASK-170`에서 session_id 관련 코드는 diff 0줄로 이번 변경과 무관함을 확인
- 컨벤션 최종 1회(`opal-convention-checker`): Critical/High 0, Medium 3(docstring 라우트 수 정정·json.load 예외 처리 통일·exports 등재 누락) — 즉시 반영 후 관련 회귀(test_design_gate.py·test_state_tool_verification_gates.py 130 passed) 재확인

## 회고적 학습 후보

.opal/brain/pages/concept/design-gate-deterministic-pretier-separation.md
.opal/brain/pages/concept/design-gate-gaps-resolution-roundtrip.md
.opal/brain/pages/entity/state-tool.md
.opal/brain/pages/entity/op-scenario-gate-skill.md
.opal/brain/pages/concept/skill-opal-pilot-dev.md
.opal/brain/pages/entity/opal-evaluator-agent.md

## 참고

- 범위 밖으로 결정된 "evaluator 디스패치 scope 병렬 분리"는 후속 태스크 후보로 남아있다(PLAN.md §범위 밖 제안, AGENTIC-LOG #9).
- 캡틴이 이후 "모든 에이전트에 `effort: default` 일괄 적용"을 요청했으나 이번 태스크 범위(opal-evaluator-agent 단일)를 벗어나 별도 후속 작업으로 미뤘다.
- baseline이 "effort 미지정"이 아니라 PM 세션의 effort 상속으로 사실상 특정 값이었을 가능성이 남아있다(H-3, EVAL-RESULT.md 결론 참조) — 세션 상속 여부 자체는 이번 측정으로 확정하지 못했다.
