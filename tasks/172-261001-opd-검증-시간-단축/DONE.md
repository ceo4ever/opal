# DONE: 검증 시간 단축 — 실호출 최소화·컨벤션 검사 경량화·판정 병렬화

## 결과

검증 단계(설계 게이트·TEST·컨벤션 검사)의 시간을 쓰는 곳을 모델 판단이 필요한 부분과 결정론으로 고정할 수 있는 부분으로 나눴다. 시나리오 18건 중 17건이 통과했고 1건(S-13)은 실패로 남았다. CLOSE 이후 추가작업 ADD-1~5(`ADD_DONE-1~4.md`)로 S-13 원인 분리, 도구 누락 방지, 평가자 세트 정비·재측정, evaluator effort `low` 변경을 수행했다.

**달라진 것**

- **실호출 한정(AC-1·AC-2).** 시나리오 가이드가 에이전트 실호출을 "모델 판단 자체가 수용 기준"인 경우로 한정하고 `[실호출 1회]` 표지와 1회 제한을 요구한다. evaluator는 기록된 결과 파일로 같은 계약을 증명할 수 있는 실호출 시나리오를 `cheaper_layer` 권고로 지적한다(S-12에서 실제 반환 확인).
- **이전 지적 조립 결정론화(AC-3).** `state-tool design-gate start` 응답이 `previous_gaps`·`previous_gaps_by_scope`·`previous_gaps_iteration`을 싣는다. PM의 회차별 추론이 사라졌다.
- **설계 판정 병렬 분리와 결합(AC-8).** evaluator `design-rubric`에 `scope`(design/scenario/all)를 추가하고 신규 `design-gate combine`이 두 부분 결과를 결정론 규칙으로 기존 단일 판정과 같은 형식으로 결합한다. `design-gate record`는 바뀌지 않았다. `op-scenario-gate` §6.1은 병렬 두 호출 + `combine` 절차다.
- **컨벤션 검사 경량화(AC-4·AC-5).** 신규 도구 `convention-precheck`가 기준 커밋(merge-base) 대비 변경 구간을 계산하고 기계 규칙 4종(@header, frontmatter 필수 키, 수기 변경이력 절, 네이밍)을 같은 finding 스키마로 판정한다. checker는 `base_ref`가 있으면 변경 구간만 읽는다. 162의 과거 High 2건이 재현된다.
- **model·effort 고정(AC-6·AC-7).** 평가 세트 측정 후 캡틴이 결정: `opal-convention-checker` = `standard`(sonnet) + `effort: low`, `opal-evaluator-agent` = `advanced`(opus) + `effort: medium`. 표시용 `effort: default`는 제거했고 `scripts/tests/test_agent_effort_policy.sh`가 재발을 막는다. 나머지 14개 에이전트는 effort 미선언(호출 세션 상속)을 유지한다. ADD-3·ADD-4 재측정(`run/EVAL-RESULT-4.md`·`run/EVAL-RESULT-5.md`) 뒤 캡틴 결정으로 `opal-evaluator-agent`는 `effort: low`로 변경했다(`ADD_DONE-4.md`).
- **TEST 병렬 판정(AC-9).** 실측 결과: 한 에이전트 안에서 독립 시나리오 명령의 동시 실행은 가능(순차 8.05초 → 병렬 2.01초), 여러 `opal-test-agent`의 동시 `scenario-mark`는 불가(5라운드 8프로세스에서 6건 유실, 파일 잠금 없음). `test-cycle.md`에 "병렬 그룹 실행" 절을 두고 다중 에이전트 병렬은 채택하지 않았다. 이번 TEST의 S-1~S-11이 이 절차로 실행됐다.

**유지한 것:** 설계 4축·시나리오 3축·pass 조건·반복 상한 3회·`reset --owner user`, `design-gate record`의 검사 순서와 기존 오류 코드, `gc-finding-schema.md`의 필드·판정표, `actor.md`의 독립 검증 경계.

## 변경 파일

- `docs/PROJECT.md`
- `opal/agents/opal-convention-checker/AGENT.md`
- `opal/agents/opal-evaluator-agent/AGENT.md`
- `opal/agents/opal-test-agent/AGENT.md`
- `opal/core/references/agents.md`
- `opal/core/references/harness/design-gate.md`
- `opal/core/references/harness/pm-review-gate.md`
- `opal/core/references/harness/test-cycle.md`
- `opal/core/references/tools.md`
- `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md`
- `opal/skills/op-gc-convention/SKILL.md`
- `opal/skills/op-scenario-gate/README.md`
- `opal/skills/op-scenario-gate/SKILL.md`
- `opal/skills/opal-pilot-dev/README.md`
- `opal/skills/opal-pilot-dev/SKILL.md`
- `opal/tools/convention-precheck/README.md`
- `opal/tools/convention-precheck/convention_precheck.py`
- `opal/tools/convention-precheck/run.sh`
- `opal/tools/convention-precheck/tests/test_convention_precheck.py`
- `opal/tools/state-tool/README.md`
- `opal/tools/state-tool/state_tool.py`
- `opal/tools/state-tool/tests/test_design_gate_parallel.py`
- `scripts/install-mac.sh`
- `scripts/tests/test_agent_effort_policy.sh`
- 태스크 산출물: `tasks/172-261001-opd-검증-시간-단축/` 아래 PLAN.md·TEST-SCENARIO.md·AGENTIC-LOG.md·run/ (EVAL-RESULT.md, PARALLEL-PROBE.md, DIAG-S13.md, eval/, test-evidence/)

## 검증

- 시나리오 18건: 17 PASS, 1 FAIL(S-13). 원본은 `test-scenario.json`. 병렬 그룹(S-1~S-11)은 한 번의 Bash로 동시 실행했고 `test-clock`의 auto 구간은 `batch-1` 하나(98.9초)다.
- 최종 TEST Gate: 컨벤션 최종 검사(새 `base_ref` 흐름) PASS·finding 0건, 전체 회귀 `main` 대비 새 실패 0건(기존 실패는 `main`과 동일), 보안 Critical/High/Medium 없음(Low 4건 권고). 증거: `run/test-evidence/final-gate/`.
- 설계 게이트 3회차 pass(1·2회차 rewrite 후 반영).
- 측정(`run/EVAL-RESULT.md`): checker 4후보×10사례, evaluator 3후보×8사례(설계·시나리오 두 호출). 채택 판정과 소요는 보고서 참조. 최초 측정이 드러낸 사전 검사의 회귀 판정 거짓 양성(163 구간 High 6건)은 판정기를 기준·현재 양쪽에 같게 적용하도록 고쳐 재집계했고 최초 결과는 보존했다.

**미충족·한계(숨기지 않는다)**

- **S-13 실패.** 설치된 evaluator를 설계·시나리오 병렬 한 쌍으로 호출해 `pass-161`을 판정시켰더니 결합 verdict가 `fail`이었다(기대 `pass`). 진단 표본(단일 3회, 병렬 3쌍)은 모두 `fail`(같은 `decision_clarity` 축)이라 분리가 verdict를 바꾼다는 근거는 없지만, W-10 측정의 `pass`와 어긋나는 원인은 분리하지 못했다(`run/DIAG-S13.md`). 캡틴 결정으로 CLOSE 이후 후속 작업으로 넘긴다.
- **병렬 판정의 시간 이득 미확인.** 단일 호출 평균 96.1초, 병렬 쌍 벽시계 평균 91.8초로 단축이 확인되지 않았다. 설계 판정 호출 하나가 단일 호출 전체와 비슷하게 걸린다. 병렬 경로는 기본값으로 유지되며 이득은 `previous_gaps`·`combine`의 결정론화(시간과 무관)에 있다.
- **H-6 부분 확인.** Claude Code 공식 문서는 서브에이전트 `effort`가 호출 세션 effort보다 우선(override)한다는 규칙을 명문으로 적지 않는다("에이전트가 활성일 때만 적용", 생략 시 세션 상속까지만). 선언 값이 배포 파일에 존재함은 시험(S-17)으로 확인했다.
- **호출 방식 정정.** S-12·S-13과 W-10 측정은 raw `claude -p`로 수행했다. 정식 wrapper가 있으면 wrapper를 쓰는 규칙(`~/.opal/AGENT.md`)에 어긋나며, 캡틴 지시로 `opal-agent` CLI 기준으로 `test-cycle.md` §실호출 시나리오를 정정했다. 이미 얻은 증거는 유효한 것으로 보존했다.
- **설치본 불일치.** 배포(W-11) 이후에 `test-cycle.md`(실호출 절)가 바뀌었다. `~/.opal/references`의 사본은 다음 install 때 갱신된다.
- **구현 중 해석.** W-1 워커가 D-10 문구를 좁힌 4건(@header 규칙은 코드 확장자만·필수 5필드 검사는 추가 파일만·네이밍은 새 구성요소만·fingerprint 입력의 category에 세부 키 부가)을 구현 세부로 승인했다.
- 어댑터 시험 `test_agent_adapter_fields.sh`의 3건 실패는 `main`에서도 같은 기존 실패다.

## 회고적 학습 후보

.opal/brain/pages/entity/convention-precheck.md
.opal/brain/pages/concept/design-gate-scope-parallel-judgement-combine.md
.opal/brain/pages/concept/agent-effort-policy-inherit-by-default.md
.opal/brain/pages/concept/test-parallel-group-single-agent-only.md
.opal/brain/pages/concept/real-invocation-scenario-limit.md
.opal/brain/pages/entity/opal-evaluator-agent.md
.opal/brain/pages/entity/op-scenario-gate-skill.md
.opal/brain/pages/concept/design-gate-gaps-resolution-roundtrip.md
.opal/brain/pages/entity/state-tool.md
.opal/brain/pages/concept/evaluator-eval-set-label-fixture-measurement-lesson.md

## 참고

후속 작업(CLOSE 이후):

1. S-13의 기대 verdict가 W-10 측정과 TEST에서 어긋난 원인 분리(프롬프트, 정의 주입 방식, 표본 변동)와 시나리오 기준 재설계.
2. 병렬 판정의 시간 이득 확보 방안(설계 판정 호출이 느린 원인 분석, 설계 축을 더 나누는 안, 또는 기본값을 `scope: all`로 되돌리는 안).
3. `scenario-mark` 파일 잠금 도입과 `auto_seconds` 합집합화(다중 `opal-test-agent` 병렬의 전제).
4. 보안 Low 권고: 파일명 앞 `--` 처리, `.opal/code-scan.json` 필드 타입 검증.
5. (ADD-3·4에서 추가) 170 평가 세트 fixture 결손 보정 — `tasks/170-…/run/eval-set/pass-161·pass-163`이 참조하는 `REQUEST.md`를 세트에 포함하거나 `test_design_gate_parallel.py --make-fixture`가 참조 입력 파일을 함께 복사하도록 확장. clean 세트의 남은 지적(EVAL-RESULT-4 §6·EVAL-RESULT-5 §5, B2·B3 주제)의 재판정은 미수행.
6. (ADD-5에서 추가) 172 머지 후 install 필요 — 설치본 `~/.opal`은 2026-10-01 21:04 허브 main 기준 재설치 상태라 evaluator `effort: low` 선언이 미반영.
