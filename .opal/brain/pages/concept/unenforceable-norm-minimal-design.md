---
type: concept
title: 집행 불가 규범의 최소 설계 — 템플릿이 상한을 소유하고 절 길이가 잠근다
tags:
- norm-design
- reporting
- enforcement
- governance
sources:
- doc:opal/core/references/opal-pm.md
related:
- report-norm-topology-10-types
- norm-proliferation-spiral-without-enforcement
- template-precedence-over-prose-norms
- lean-core-relocation-benefit-precondition
created: '2026-09-08'
updated: '2026-09-08'
status: draft
---
## 개요

집행 도구를 붙일 수 없는 규범은 「산문은 유도되지 않는다」와 「템플릿도 결국 불어난다」 사이에 갇힌다. 보고 규범을 다시 세우면서 이 두 축적 지식이 정면으로 충돌했고, 해소책은 **조문에서 숫자를 빼 템플릿 주석에 몰아주고, 절 길이 상한을 규범 자신에 박는 것**이었다(`opal/core/references/opal-pm.md:100-133`).

## 결정 배경 (WHY)

- 보고 규범은 에이전트의 **응답 텍스트**에 걸리는 규범이라 검사 도구를 붙일 수 없다. 응답은 저장소의 파일이 아니어서 lint·validate 같은 결정론적 판정 대상이 되지 못한다. 따라서 「집행 수단이 없으면 폐지·축소를 검토하라」는 기존 판단(`[[norm-proliferation-spiral-without-enforcement]]`)이 그대로 적용되는데, 폐지는 이미 한 번 했고 무규범 3유형이 남아 있었다(`[[report-norm-topology-10-types]]`).
- 두 축적 지식이 서로를 막았다. 산문 원칙은 대조 실험에서 준수율 0으로 나왔으므로 원칙을 늘리는 길이 막혔고(`[[template-precedence-over-prose-norms]]`), 템플릿은 이기지만 이전 보고 규범이 열세 달 만에 177줄까지 불어난 전례가 있어 템플릿을 키우는 길도 막혔다.
- 규범을 기계가 읽을 수 있는 구조화 형식으로 적으면 증식을 막을 수 있다는 가설을 검토했으나 기각했다. 근거는 세 가지다. 첫째, 집행 도구가 없으면 그 형식을 읽는 주체가 작성자 본인뿐이어서 「세 항목 이내」라는 문장과 유도력이 같다. 둘째, 구조화 블록 **옆에** 산문 조항을 덧붙이는 것을 그 형식이 막지 못하며, 이전 보고 규범이 표를 두고도 표 밖에 필수 문단을 계속 붙여 불어난 방식이 정확히 그것이었다. 셋째, 같은 수치가 템플릿 주석과 구조화 블록 양쪽에 적히면 두 값이 갈라진다 — 이 프로젝트가 규정과 도구 사이에서 반복해 겪은 실패 유형이다.

## 결정 내용

- **수치의 단독 소유자는 템플릿 주석이다.** 조문은 「항목끼리 겹치지 않는다」처럼 셀 수 없는 규칙만 갖고, 항목 개수·불릿 개수 같은 셀 수 있는 값은 템플릿 안 화살표 주석에만 적는다(`opal/core/references/opal-pm.md:111`). 값을 두 곳에 적지 않으므로 갈라질 자리가 사라진다.
- **증식 방어는 절 길이 상한 한 줄이 담당한다.** 「이 절은 서른다섯 줄을 넘기지 않는다. 위반 사례가 나오면 문장을 추가하지 않고 기존 조를 교체한다」를 규범 본문에 넣었다(`opal/core/references/opal-pm.md:133`). 위반 사례가 발견됐을 때 취할 수 있는 행동을 문장 추가가 아니라 조 교체로 못박는 것이 핵심이며, 신설 시점 실측은 서른네 줄로 여유가 한 줄이다.
- **적용 범위 축소가 상시 로드 비용을 0으로 만든다.** 규범을 프로젝트 매니저 응답으로 한정하고 매니저 전용 참조 문서에 두면, 부트스트랩 두 번째 단계에서만 로드되므로 모든 세션이 읽는 코어의 분량이 늘지 않는다(`opal/core/references/opal-pm.md:102`). 「전 계층 공통 규범은 분리해도 이익이 0」이라는 기존 판정(`[[lean-core-relocation-benefit-precondition]]`)은 범위를 줄이지 않은 전제에서 나온 것이므로, 범위 자체를 좁히면 그 전제가 성립하지 않는다.

## 영향 범위

- 집행 도구를 붙일 수 없는 규범을 신설·개정할 때 적용한다 — 보고 형식 외에도 대화 태도·질문 방식처럼 산출물이 파일로 남지 않는 규범이 여기 해당한다.
- 「셀 수 있는 값은 한 곳에만」과 「절 길이 상한을 규범 자신에 박는다」는 두 장치는 독립적으로 쓸 수 있다. 전자는 값이 갈라지는 것을, 후자는 조항이 늘어나는 것을 막는다.
- 규범 준수 여부는 여전히 기계 판정이 불가능하므로, 이 설계는 증식 속도를 늦출 뿐 준수를 보장하지 않는다. 실사용 관찰로 상한 수치를 조정하는 것이 유일한 환류 경로다.

## 관련 페이지

- [[report-norm-topology-10-types]]
- [[norm-proliferation-spiral-without-enforcement]]
- [[template-precedence-over-prose-norms]]
- [[lean-core-relocation-benefit-precondition]]
