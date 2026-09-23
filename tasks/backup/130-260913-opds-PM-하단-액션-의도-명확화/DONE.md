# DONE: PM 하단 액션 의도 명확화

## 결과

PM 결과 보고의 하단 액션을 행동 주체와 사용자 입력 필요 여부가 드러나는 두 형태로 교체했다.
`▶ PM 다음 작업`은 PM이 사용자 입력 없이 계속 수행할 행동만 표시하고, `▶️ 사용자 결정 필요`는
PM이 멈추고 사용자 답변을 기다리는 단일 질문만 표시한다. 두 형태는 한 보고에서 함께 사용할 수
없다.

사용자 결정 요청은 결정할 한 가지, 선택지 또는 답변 범위, PM 권고, 권고 이유와 주요 영향,
답변 후 다음 작업을 본문에 제시하고 물음표로 끝나는 질문 하나로 닫도록 했다. PLAN·EXECUTE·CLOSE
사용자 게이트 예시도 같은 의미를 소비하도록 바꿨다.

기존 보고의 판단·비중복·확정/추정 분리 원칙과 게이트의 단계별 정보, 승인·상태 전이 계약은
유지했다. `opal/core/AGENT.md`에는 보고 형식을 다시 넣지 않았고 `~/.opal/` 배포본도 변경하지 않았다.

## 변경 파일

- `opal/core/references/opal-pm.md`
- `opal/core/references/opal-harness-semi-agentic.md`
- `tasks/130-260913-opds-PM-하단-액션-의도-명확화/TASK.md`
- `tasks/130-260913-opds-PM-하단-액션-의도-명확화/PLAN.md`
- `tasks/130-260913-opds-PM-하단-액션-의도-명확화/TEST-SCENARIO.md`
- `tasks/130-260913-opds-PM-하단-액션-의도-명확화/test-scenario.json`
- `tasks/130-260913-opds-PM-하단-액션-의도-명확화/AGENTIC-LOG.md`

## 검증

- `test-tool scenario-status` — 8개 시나리오 전부 PASS, FAIL·BLOCKED 0건
- 독립 보고 재현 — 일반 보고 2건과 PLAN·EXECUTE·CLOSE 게이트 3건, 총 5건의 `actor`와
  `input_required`가 전건 하나로 판별됨
- `state-tool verify --plan-contract-check` — PASS
- `state-tool verify --code-scan-citation-check` — PASS
- `state-tool validate` — 위반 0건
- `git diff --check` — PASS
- `opal-pm.md` §8 — 35줄 상한 충족
- `opal-harness-semi-agentic.md` §10 예시 — `▶️ 다음 진행 사항입니다.` 0건
- `opal/core/AGENT.md` — 변경 없음, 새 하단 채널 문안 0건
- 배포본 SHA-256 — 구현 전 기준선과 동일

## 회고적 학습 후보

.opal/brain/pages/concept/action-footer-encodes-actor-and-input-requirement.md

## 참고

- 소스 변경은 `feat/OP-TASK-130` 브랜치에 커밋하며, 허브에는 병합하지 않았다.
- 전역 설치·배포는 범위 밖이라 수행하지 않았다.
