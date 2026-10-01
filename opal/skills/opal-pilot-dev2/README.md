# opal-pilot-dev2

AI-native SDLC 파일럿. intent·spec·plan부터 구현·독립 검증·리뷰·승인된 배포까지 하나의
생명주기로 연결하며, 아티팩트 결합 해시·범위·증거·역할 분리를 기계 게이트로 강제한다.

## 개요

- 6단계: **TASK**(intent) → **DESIGN**(spec) → **PLAN** → **EXECUTE**(구현) →
  **VERIFY**(독립 검증 + 리뷰) → **CLOSE**.
- 역할 분리: Coordinator가 intent/spec/plan과 조율을 맡고, Builder(구현)·Verifier(독립
  검증)·Reviewer(리뷰)는 각각 독립 에이전트로 호출된다 — 같은 워커가 구현과 검증·리뷰를
  겸하지 않는다.
- semi-agentic은 intent/spec/plan까지 사용자 검토를 거치고 이후 자율 진행하며,
  agentic은 정상 단계를 자율 진행하되 미결정 요구·외부 계약·고위험 승인·재시도 상한은
  사용자 대기로 넘긴다.
- 상태 변경은 `scripts/lifecycle.py` 도구로만 수행한다.

## 호출법

```
//opd2 {작업 요청}
```

기존 `opd` 요청이나 설명만 요청하는 작업에는 적용하지 않는다.

## 참조 문서

- `references/` — `execution.md`(mode/workspace 연결), `lifecycle.md`(생명주기 도구),
  `artifacts.md`(산출물 스키마), `risk-model.md`, `testing.md`, `governance.md`,
  `rollout.md`, `metrics.md`, `evals.md`(행동 평가), `validation.md`(검증 범위)
- `agents/` — `coordinator.md`, `builder.md`, `verifier.md`, `reviewer.md`: 단계별
  디스패치 계약. 해당 단계에서 실제 독립 에이전트를 호출하고 role 문서·아티팩트·소유
  파일·검증 명령을 전달한다.
- 전체 진입 절차는 `SKILL.md` §진입을 따른다.
