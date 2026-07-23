# DONE: TEST-SCENARIO 목표-커버리지 루브릭 게이트 루프 (공유 컴포넌트, opd 선적용)

> 완료일: 2026-07-23 | 스킬: opd (agentic) | 소유자: 캡틴
> 상태: 완료·커밋 대기·배포 완료(캡틴 직접 install)

## 1. 목표와 결과

TEST-SCENARIO 단계를 "목표 달성 검증"으로 재정의하고, 루브릭 채점 기반 작은 수렴 루프(Producer → 커버리지 도구 게이트 → 독립 Evaluator 루브릭 채점 → 종료조건 → 재작성)를 **공유 컴포넌트**로 구현했다. 1차 opd 선적용 완료. 070 사건(핵심 목표가 라이브 미반영인 채 완료 처리)의 근본 원인 — 도출 엔진이 파괴 관점(H-N)만 쓰고 목표 달성(채택) 관점이 커버리지 게이트에 없던 것 — 을 tool-gated 게이트로 집행한다.

## 2. 요구사항 이행 (R-1~R-8)

| R-ID | 내용 | 결과 |
|------|------|------|
| R-1 | scenario-gate 규칙 SSOT 신설 | ✅ `opal/core/references/harness/scenario-gate.md` — 루브릭 6축·판정주체 분리·정규화 계약·종료조건 3종·tool-gated |
| R-2 | test-tool 커버리지 서브명령 확장 | ✅ `scenario-coverage-check`(exit 0/16/17) — R/F/H↔시나리오 매핑 결정론 판정, 신규 도구 아님(scenario.py 확장) |
| R-3 | evaluator scenario-rubric 모드 | ✅ opal-evaluator-agent에 phase 추가(2점 척도 ①⑤⑥·verdict 규칙·SCENARIO-GATE-{N}.md), 기존 3 phase additive 무변경 |
| R-4 | op-scenario-gate 단계 스킬 | ✅ 커버리지→평가자→종료조건 3종 루프 컨트롤, tool-gated·Producer≠Evaluator, 단일 호출 지점 |
| R-5 | opd STEP 3.5 접합 | ✅ pipeline.json `test_scenario.scenario_gate` 행 + SKILL 배선. 게이트 미통과 시 EXECUTE 진입 구조적 차단(stage_transition_violation) |
| R-6 | op-task AC 패턴 보강(상류) | ✅ 교체형 목표=잔존0·채택 기준 의무 + Bad/Good 예시 |
| R-7 | 단위 테스트(RED-first) | ✅ test_scenario.py 신규 8케이스, 회귀 0 (31 passed) |
| R-8 | 자기적용 실증 | ✅ 음성통제 FAIL(SCENARIO-GATE-1) + 정상수렴 PASS(SCENARIO-GATE-2, avg 1.67) 둘 다 실증 |

## 3. 검증 증거 (동작 기반)

- **RED→GREEN**: test_scenario.py 신규 5케이스 RED(exit 2)→GREEN, 전체 31 passed. PM이 python3로 직접 재실행 확인.
- **서브명령 실동작**: scenario-coverage-check exit 16(누락)/0(완전)/17(입력오류) 정확.
- **구조적 차단**: 임시 폴더에서 게이트 행 미완 시 `mark execute.implement` → `stage_transition_violation` 거부. state-tool 코드 무변경 흡수(spec-validate 0위반).
- **dogfooding(R-8)**: 목표 시나리오(S-7/S-8) 누락 → coverage exit 16 missing{R-8,F-008,H-7} → FAIL. 복원 → exit 0 AND evaluator verdict pass(goal2/adoption1/boundary2/avg1.67) → PASS. 070 결함을 실제로 차단함을 자기 자신으로 증명.
- **회귀**: test-tool 42 passed(사전 존재 flake `TestResolve` 1건 제외, 073 무관 git diff 확인).

## 4. 변경 파일 (changed_files)

**신규**
- `opal/core/references/harness/scenario-gate.md`
- `opal/skills/op-scenario-gate/SKILL.md`

**수정**
- `opal/core/references/opal-harness.md` (§1 루프 상한 행 + 변경이력 v6.6)
- `opal/skills/op-dev-test-scenario/SKILL.md` (scenario-gate 참조 + PM Gate 목표커버 항목 + v1.8)
- `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` (목적·Step 1 목표 관점 + v2.7)
- `opal/tools/test-tool/lib/scenario.py` (scenario-coverage-check + exit 16/17)
- `opal/tools/test-tool/tests/test_scenario.py` (신규 8케이스)
- `opal/agents/opal-evaluator-agent/AGENT.md` (scenario-rubric phase, additive + v1.2)
- `opal/skills/opal-pilot-dev/references/pipeline.json` (게이트 행 id 10, 16행)
- `opal/skills/opal-pilot-dev/SKILL.md` (STEP 3.5 배선 + 미러 표 16행 + v4.8)
- `opal/skills/op-task/SKILL.md` (교체형 목표 AC 패턴 + v2.3)
- `docs/PROJECT.md` (목표-커버 게이트 섹션 + 변경이력)

**태스크 산출물**: TASK.md·ANALYSIS.md·PLAN.md·TEST-SCENARIO.md·AGENTIC-LOG.md·SCENARIO-GATE-1.md·SCENARIO-GATE-2.md·DONE.md

## 5. 배포 상태

- 캡틴이 직접 install 실행 → `~/.opal/` 반영 완료(PM 검증: 신규 2파일·핵심 마커 전부 ✅).
- `opal-evaluator-agent` 서브에이전트 등록됨(`~/.claude/agents/opal-evaluator-agent.md`) — 배포 갭 해소. (현재 세션 Agent 목록은 재시작 후 반영)

## 6. 후속·미해결

- **074 (별도 태스크, 커밋·배포 완료)**: `state-tool --import-existing` task-step key 유실 결함 픽스. 073 세션 시작 시 발견 → 074가 처리·배포. PM 실증: key 16/16 보존 확인.
- **관측(비차단)**: S-5 — 게이트 통과의 "2증거(coverage exit0 + evaluator verdict pass)" 요구가 코드 강제가 아닌 **절차적(SKILL 지시)**. 기존 프레임워크 Guards와 동일 패턴이나, "enforce don't advise" 관점에서 코드-게이트화 여부는 후속 검토 후보(회고 기록).
- **확산(후속 태스크)**: op-scenario-gate를 oppl/opds/opsdd/oppd로 확산 — Step 2 pilot별 정규화 변환기만 추가하면 재사용(정규화 계약이 확장성 근거). 1차는 opd 선적용으로 한정.

## 7. agentic 대행 요약

- 게이트 판단 8회 전부 Pass(에스컬레이션 0). 상세: `AGENTIC-LOG.md`.
- PM 의사결정 2건(모드 전환·파라미터 잠금), 개선 발견 2건(--import-existing·evaluator 미등록 — 둘 다 해소).
- 워커 보고를 신뢰하지 않고 핵심 단계(pytest·서브명령·흡수 차단·dogfooding)를 PM이 직접 재실행 검증(헌법 §4 "verified behavior").
