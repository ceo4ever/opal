---
template: sdlc-v2
---
# PLAN: PM 하단 액션 의도 명확화

> 입력: [TASK.md](TASK.md) — ANALYSIS 없음(Short profile). `code-scan search '보고|승인|질문|다음' --json` 결과 하단 액션을 렌더링하는 실행 코드는 식별하지 않았고, 재사용 가능한 질문 계약은 `opal/skills/opal-self-pm/references/question-loop.md` §1이다.

## Approach

공통 하단 액션 계약의 SSOT는 `opal/core/references/opal-pm.md` §8에 둔다. 이 절은 이미 PM 보고 형식을 소유하고, Phase B 로드라 비서 tier에 적용되지 않으며, 현재도 `▶ 다음`과 `▶️ 승인 요청`의 배타성을 갖고 있다. 이번 변경은 새 대규모 보고 형식을 만들지 않고 §8의 하단 액션 조와 템플릿 하단만 교체한다. 근거: `opal/core/references/opal-pm.md:106`, `opal/core/references/opal-pm.md:108`, `opal/core/references/opal-pm.md:112`, `opal/core/references/opal-pm.md:133`

게이트 문서인 `opal/core/references/opal-harness-semi-agentic.md` §10은 단계별 5요소 표와 승인·상태 전이 규칙을 유지하고, 하단 액션의 의미만 `opal-pm.md` §8을 참조한다. 예시 3건의 하단 문안은 공통 채널을 실물로 보여 주도록 바꾸되 별도 정의 표를 만들지 않는다. 현재 예시는 `▶️ 다음 진행 사항입니다.`로 닫혀 있어 사용자가 답해야 하는지 즉시 구분하기 어렵다. 근거: `opal/core/references/opal-harness-semi-agentic.md:126`, `opal/core/references/opal-harness-semi-agentic.md:160`, `opal/core/references/opal-harness-semi-agentic.md:202`, `opal/core/references/opal-harness-semi-agentic.md:242`

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| D-1. 공통 하단 액션 SSOT | [MUST] `opal/core/references/opal-doc-standard.md` §2: "같은 사실은 한 곳에만 쓰고 다른 문서는 경로와 필요한 구간을 참조한다." 하단 액션의 의미와 행동 주체는 `opal/core/references/opal-pm.md` §8만 소유한다. `opal-harness-semi-agentic.md` §10은 `opal-pm.md` §8을 참조하고, 자체 채널 정의를 만들지 않는다. | TASK가 하단 액션 규범 1곳과 게이트 참조를 요구한다. 근거: `tasks/130-260913-opds-PM-하단-액션-의도-명확화/TASK.md:22`, `tasks/130-260913-opds-PM-하단-액션-의도-명확화/TASK.md:34` |
| D-2. 정확한 두 채널 문안 | §8의 하단 채널은 둘 중 하나만 사용한다. `▶ PM 다음 작업: {입력 불필요한 PM 행동 1문장}`은 사용자 입력이 필요 없고 행동 주체가 PM이다. `▶️ 사용자 결정 필요: {한 가지 질문?}`은 PM이 멈추고 사용자 답변을 기다리며 행동 주체가 사용자다. | 기존 `다음` 표지가 PM 행동과 사용자 승인을 모두 뜻하는 문제가 TASK의 핵심이다. 근거: `tasks/130-260913-opds-PM-하단-액션-의도-명확화/TASK.md:8`, `tasks/130-260913-opds-PM-하단-액션-의도-명확화/TASK.md:12`, `tasks/130-260913-opds-PM-하단-액션-의도-명확화/TASK.md:31` |
| D-3. 사용자 결정 요청 구성 | `▶️ 사용자 결정 필요`는 결정할 한 가지, 선택지 또는 답변 범위, PM 권고, 권고 이유와 주요 영향, 답변 후 다음 작업, 한 개의 명시적 질문을 포함한다. 세부 5요소 이름은 `question-loop.md` §1을 재사용하고, §8은 하단 채널 의미와 명시적 질문 1개만 추가로 못박는다. | 질문 1개 5요소가 이미 존재한다. 이를 복제하지 않고 소비해야 중복 정의가 생기지 않는다. 근거: `opal/skills/opal-self-pm/references/question-loop.md:17`, `opal/skills/opal-self-pm/references/question-loop.md:21`, `opal/skills/opal-self-pm/references/question-loop.md:25`, `tasks/130-260913-opds-PM-하단-액션-의도-명확화/TASK.md:32` |
| D-4. §8 교체 방식 | [MUST] `tasks/130-260913-opds-PM-하단-액션-의도-명확화/TASK.md` §Constraints: "`opal/core/references/opal-pm.md`의 보고 형식 절은 기존 35줄 상한과 문장 추가 대신 기존 조 교체 원칙을 지켜야 한다." EXECUTE는 §8 본문을 교체하고, 교체 후 `## 8. 보고 형식`부터 다음 `---` 직전까지 35줄 이하로 유지한다. | 현재 §8도 "위반 사례가 나오면 문장을 추가하지 않고 기존 조를 교체한다"를 요구한다. 근거: `opal/core/references/opal-pm.md:139`, `tasks/130-260913-opds-PM-하단-액션-의도-명확화/TASK.md:25` |
| D-5. 게이트 예시 접합 | `opal-harness-semi-agentic.md` §10.1, §10.2, §10.3의 단계별 5요소 표는 유지한다. 각 예시의 하단 `▶️ 다음 진행 사항입니다.` 블록만 `▶️ 사용자 결정 필요: ...?` 형식으로 바꾸고, 결정 대상·선택지 또는 답변 범위·PM 권고·이유와 주요 영향·답변 후 다음 작업을 예시로 채운다. | 예시는 산문 규칙보다 강하게 실행을 유도하므로 틀린 예시를 먼저 고쳐야 한다. 근거: `.opal/brain/pages/concept/template-precedence-over-prose-norms.md:45`, `.opal/brain/pages/concept/template-precedence-over-prose-norms.md:60`, `tasks/130-260913-opds-PM-하단-액션-의도-명확화/TASK.md:33` |
| D-6. AGENT.md 비접촉 | `opal/core/AGENT.md`에는 보고 형식 본문, 하단 액션 템플릿, 채널 정의를 추가하지 않는다. 회귀 검증은 `opal/core/AGENT.md`에서 `### 보고 형식`, `▶ PM 다음 작업`, `▶️ 사용자 결정 필요`가 0건임을 확인한다. | 태스크 108이 Phase A 상시 로드 보고 형식 177줄을 제거했고 대체 규범을 두지 않았다. 이번 규범은 PM 전용 §8에만 둔다. 근거: `tasks/108-260906-opds-보고형식-전면제거/DONE.md:8`, `tasks/108-260906-opds-보고형식-전면제거/DONE.md:21`, `tasks/130-260913-opds-PM-하단-액션-의도-명확화/TASK.md:24`, `tasks/130-260913-opds-PM-하단-액션-의도-명확화/TASK.md:36` |
| D-7. 배포 경계 | EXECUTE는 프로젝트 소스만 수정한다. `~/.opal/` 배포본 수정, install, 배포 검증은 별도 승인 전까지 범위 밖이다. | [MUST] `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `scripts/`)에서 수행한다." TASK도 전역 설치·배포를 제외한다. 근거: `docs/CONVENTIONS.md:254`, `tasks/130-260913-opds-PM-하단-액션-의도-명확화/TASK.md:18`, `tasks/130-260913-opds-PM-하단-액션-의도-명확화/TASK.md:27` |
| D-8. 변경이력 미작성 | 이번 소스 문서 변경에 수기 `변경이력` 행을 추가하지 않는다. 기존 변경이력 절이 있는 파일을 건드리더라도 새 누적 이력 행을 만들지 않는다. | [MUST] `opal/core/references/opal-doc-standard.md` §5: "git으로 관리되는 프로젝트 산출물에는 `변경이력`, `Changelog`, `history`, `revisions` 등 이름과 무관하게 수기 누적 이력 절을 만들지 않는다." 근거: `opal/core/references/opal-doc-standard.md:63`, `opal/core/references/opal-doc-standard.md:65` |
| D-9. 검증 주체 경계 | 기본 actor=worker이므로 EXECUTE의 W-3은 `opal-task-agent`가 수행하는 결정론 정적/self-check로 한정한다. AC-5의 실제 독립 보고 재현 검증은 TEST-SCENARIO가 시나리오를 정의하고 `opal-test-agent`가 별도 TEST 단계에서 수행한다. | 구현 워커가 자기 산출 보고를 독립 재현하면 자기충족 위험이 생긴다. PLAN은 EXECUTE 입력과 TEST 경계를 분리해야 한다. 근거: `tasks/130-260913-opds-PM-하단-액션-의도-명확화/TASK.md:35`, `docs/PROJECT.md` §주요 컴포넌트 (Dev 파이프라인) |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. 공통 하단 액션 계약 교체 | opal-task-agent | `opal/core/references/opal-pm.md` | §8 본문을 35줄 이하로 교체한다. 하단 채널명을 D-2의 정확한 두 문안으로 바꾸고, `▶ PM 다음 작업`은 입력 불필요·PM 행동, `▶️ 사용자 결정 필요`는 입력 필요·사용자 행동으로 정의한다. 사용자 결정 요청은 D-3 구성 요소와 명시적 질문 1개를 요구하고 `question-loop.md` §1을 참조한다. 기존 "판단을 낸다", "항목끼리 겹치지 않는다", "확정과 추정을 섞지 않는다", 터미널 미렌더 금지, 35줄 상한 원칙은 유지하되 중복되는 문장은 교체한다. | 없음 | P1 | AC-1, AC-2, AC-4, C-1, C-2, C-3, C-4 |
| W-2. 사용자 게이트 예시 접합 | opal-task-agent | `opal/core/references/opal-harness-semi-agentic.md` | §10 서두에 "하단 액션의 의미는 `opal-pm.md` §8을 따른다"는 포인터를 추가하고, 채널 의미·필드 정의는 복제하지 않는다. §10.1 PLAN, §10.2 EXECUTE, §10.3 CLOSE 예시의 하단 `▶️ 다음 진행 사항입니다.` 블록을 각각 `▶️ 사용자 결정 필요: EXECUTE를 시작할까요?`, `▶️ 사용자 결정 필요: CLOSE로 진입할까요?`, `▶️ 사용자 결정 필요: DONE.md를 생성하고 태스크를 종료할까요?` 형식으로 교체한다. 각 예시는 결정 대상, 선택지 또는 답변 범위, PM 권고, 이유와 주요 영향, 답변 후 다음 작업을 포함한다. 5요소 표·모드 경계·자동 승인 불가 구간·CLOSE 승인 절차는 수정하지 않는다. | W-1 | P2 | AC-3, AC-4, C-1, C-2, C-5 |
| W-3. 정적 회귀 self-check | opal-task-agent | 검증 명령(소스 비변경) | 구현 워커가 자기 산출물에 대해 결정론 정적 검사를 수행한다. `opal/core/AGENT.md`에 보고 형식 본문이 없는지, `opal-harness-semi-agentic.md` §10 예시에 `▶️ 다음 진행 사항입니다.`가 0건인지, `opal-pm.md` §8이 35줄 이하인지, `~/.opal/` 경로 변경이 없었는지 확인한다. 마지막으로 `state-tool verify <task-folder> --plan-contract-check`와 `--code-scan-citation-check`를 실행한다. 실제 독립 보고 재현 검증은 이 W에서 수행하지 않고 TEST-SCENARIO와 `opal-test-agent`에 인계한다. | W-1, W-2 | P3 | AC-5, AC-6, C-3, C-4, C-5, C-6 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. 결정 요청 필드를 §8에 추가하면서 35줄 상한을 넘길 수 있다 | `opal-pm.md` §8의 증식 방어 계약 | 보고 규범이 다시 커지고 C-4 위반이 된다 | W-1은 문장 추가가 아니라 조 교체로 수행하고, W-3에서 §8 줄 수를 측정한다. 숫자·분량 값은 템플릿 주석 또는 `question-loop.md` 참조가 소유하게 한다. |
| H-2. 게이트 문서가 새 채널 정의를 복제할 수 있다 | 하단 액션 SSOT 단일성 | 일반 PM 보고와 게이트 보고가 다시 갈라진다 | W-2는 §10 서두에 포인터만 두고, 예시는 `opal-pm.md` §8 소비 사례로만 둔다. 별도 채널 표나 "게이트 전용 의미" 문장을 만들지 않는다. |
| H-3. 예시의 낡은 `다음 진행 사항` 문안이 남을 수 있다 | 사용자가 승인 요청을 PM 다음 작업으로 오해하지 않아야 하는 계약 | AC-3·AC-5 실패 | W-2가 예시 3건을 모두 바꾸고, W-3에서 §10 예시 구간을 대상으로 `▶️ 다음 진행 사항입니다.` 0건을 확인한다. 변경이력의 과거 문장은 판정 대상에서 제외한다. |
| H-4. `opal/core/AGENT.md`에 편의상 채널 문안을 넣고 싶은 유혹이 생긴다 | Phase A 상시 로드 코어 경량화와 TASK C-3 | 태스크 108의 제거 효과가 되돌아간다 | W-1의 SSOT를 PM 전용 §8로 한정하고, W-3에서 `opal/core/AGENT.md`에 새 채널 문안과 `### 보고 형식`이 없는지 확인한다. |
| H-5. 독립 보고 재현을 구현 워커가 수행하면 자기충족 검증이 될 수 있다 | AC-5의 판별력 | 실제 보고에서 사용자가 해야 할 행동이 여전히 애매할 수 있다 | W-3은 정적/self-check만 수행한다. 독립 샘플과 실제 게이트 예시 판별은 TEST-SCENARIO가 시나리오로 정의하고 `opal-test-agent`가 수행한다. |

## Release and recovery

- 적용 순서: P1 W-1로 `opal-pm.md` §8의 공통 계약을 먼저 확정한 뒤, P2 W-2에서 게이트 예시를 그 계약에 접합하고, P3 W-3으로 구현 워커의 결정론 정적/self-check를 수행한다. 이후 TEST-SCENARIO가 실제 독립 보고 재현 시나리오를 정의하고, `opal-test-agent`가 TEST 단계에서 AC-5 판별력을 검증한다.
- 검증 범위: EXECUTE self-check는 `~/.opal/tools/state-tool/run.sh verify tasks/130-260913-opds-PM-하단-액션-의도-명확화 --plan-contract-check`, `~/.opal/tools/state-tool/run.sh verify tasks/130-260913-opds-PM-하단-액션-의도-명확화 --code-scan-citation-check`, §10 예시 구간의 `▶️ 다음 진행 사항입니다.` 0건, `opal/core/AGENT.md`의 보고 형식·채널 문안 0건, `opal-pm.md` §8 35줄 이하를 확인한다. 독립 보고 재현은 TEST 단계 검증 범위다.
- 실측 경계: EXECUTE에서는 정적 grep·줄 수·배포본 비접촉만 판정한다. 독립 샘플 2건과 게이트 예시 3건, 총 5건의 `actor`와 `input_required` 단일 판별은 TEST-SCENARIO/`opal-test-agent`가 수행하며, 한 건이라도 두 채널을 동시에 갖거나 질문 없이 사용자 결정을 요구하면 TEST 실패다.
- 실패 시: W-1 실패는 `opal-pm.md` §8만 직전 상태로 되돌리고 다시 교체한다. W-2 실패는 `opal-harness-semi-agentic.md` §10 예시 블록만 되돌린다. 이번 태스크는 배포본을 건드리지 않으므로 `~/.opal/` 복구 절차는 없다. 전역 install이 필요하면 소스 검증 후 별도 승인으로 진행한다.
