---
type: concept
title: 보고 규범 지형 — 10유형과 소유 문서 매핑
tags:
- reporting
- agent-md
- norm-ownership
- minimal-guide
- task-108
sources:
- task:108
- doc:opal/core/references/opal-pm.md
related:
- unenforceable-norm-minimal-design
- agent-md-digest-pattern
- lean-core-relocation-benefit-precondition
- norm-proliferation-spiral-without-enforcement
- template-precedence-over-prose-norms
created: '2026-09-06'
updated: '2026-09-08'
status: draft
---
## 개요

OPAL의 "보고"는 하나의 규범이 아니라 **발화 계기가 다른 10유형**이며, 유형마다 소유 문서가 다르다. 태스크 108(`opal/core/AGENT.md` §보고 형식 전면 제거) 시점에 이 지형을 전수 대조한 결과, 제거 대상 절이 실제로 단독 소유하던 것은 3유형뿐이었고 나머지 7유형은 별도 문서가 이미 소유하고 있었다. 무규범으로 남았던 그 3유형은 이후 프로젝트 매니저 참조 문서에 최소 규범을 신설하면서 닫혔다(`opal/core/references/opal-pm.md:100-133`).

## 결정 배경 (WHY)

- (근거: task:108 TASK.md §배경 분석 「보고 유형 10종의 소유자 대조」) 제거 범위를 정할 때 "§보고 형식을 지우면 보고 규범이 통째로 사라지는가"가 쟁점이었다. 전수 대조 없이는 과대 추정(전부 사라진다) 또는 과소 추정(아무 영향 없다) 어느 쪽으로도 빠질 수 있었다.
- (근거: task:108 DONE.md §3) 대조 결과 §보고 형식이 단독 소유하던 유형은 3종이고, 게이트 3종 보고·세션 첫 응답·관측·검토·에스컬레이션·완료 보고는 각각 다른 문서가 소유하고 있었다. 즉 "보고 규범"이라는 단일 실체는 애초에 없었다.
- (근거: task:108 DONE.md §3 「대체 없이 소멸한 것 3종」) 다만 소유 문서가 있는 7유형과 달리, 소멸 3종 중 **승인 채널**(`AskUserQuestion` 호출 규범)은 헌법 §1의 "ask before choosing"이라는 지향만 남고 "어떻게 묻는가"의 규정이 프레임워크 전체에서 0건이 됐다.

## 결정 내용

보고 유형과 소유 문서의 매핑은 다음과 같다.

| 유형 | 발화 계기 | 소유 문서 | 현행 |
|------|----------|----------|------|
| 세션 개시 브리핑 | 세션 첫 응답 | `opal-pm.md` §15 | 존치 |
| **질의 응답·분석** | 사용자가 물었다 | `opal-pm.md` §8 | **신설로 닫힘** |
| 명확화 질문 | 요청이 모호하다 | `PRINCIPLES.md` §1 + 명확화 게이트 | 존치 |
| **제안·경보** | 요청 없이 위험·개선을 발견 | `opal-pm.md` §8 | **신설로 닫힘** |
| 진행 중 관측 | 워커 디스패치 전후·단계 전환 | `harness/observability.md` | 존치 |
| 게이트 보고 3종 | PLAN·EXECUTE·CLOSE 전환 | `opal-harness-semi-agentic.md` §10 | 존치 |
| 워커 결과 검토 | PM Gate 직후 | `harness/pm-review-gate.md` | 존치 |
| 실패·에스컬레이션 | 루프 한도 초과·블로커 | `opal-harness.md` §1 + `opal-harness-agentic.md` §6 | 존치 |
| 완료 보고 | 태스크 종료 | `semi-agentic` §10.3 + `agentic` §9 | 존치 |
| **정정** | 앞서 말한 것이 틀렸다 | `opal-pm.md` §8 | **신설로 닫힘** |

**설계 함의 — 규범은 유형별로 발동 조건이 다르다.** 108에서 검토된 4조 최소안을 유형에 대입하면 전 유형 공통은 1조뿐이었다.

| 후보 조항 | 발동 유형 | 비발동 유형 |
|----------|----------|-----------|
| 확정/추정 분리 | 질의 응답·검토·실패·완료 | 브리핑·명확화·관측 (사실 주장이 거의 없다) |
| 끝은 액션 | 질의 응답·관측·게이트·검토 | **완료 보고** — 다음 액션이 없는 것이 정답이다 |
| 묻고 멈춘다 | 명확화·제안·게이트·실패 | 관측·완료·정정 |
| 터미널 렌더 제약 | **전 유형** | 없음 |

§보고 형식이 177줄까지 비대해진 구조적 원인이 여기 있다 — 유형별 분기를 "넣는 조건"이라는 산문 조건절로 처리하려다 조건이 증식했다.

**신설 규범이 이 분기 문제를 처리한 방법은 조건절이 아니라 적용 범위 배제였다.** 위 표에서 유일한 예외로 지목됐던 완료 보고는 게이트 3종에 속하고, 신설 규범은 게이트 3종과 세션 첫 응답을 서두 한 줄로 적용 대상에서 제외한다(`opal/core/references/opal-pm.md:102`). 예외를 조문 안에 조건절로 담지 않고 범위 밖으로 밀어냄으로써, 「응답은 하단 액션 하나로 닫는다」는 조항이 예외 없이 성립한다.

## 영향 범위

- 보고 관련 규범을 신설·수정할 때는 먼저 이 표에서 대상 유형과 기존 소유자를 확인한다. 소유자가 있는 유형에 규범을 추가하면 두 문서가 갈라진다.
- 무규범 3유형은 닫혔으나 **적용 계층은 프로젝트 매니저로 한정된다** — 신설 규범이 매니저 전용 참조 문서에 있어 부트스트랩 두 번째 단계에서만 로드되므로, 비서 계층 응답은 여전히 이 3유형에 대해 무규범이다.
- 소멸 3종 중 승인 채널은 신설 규범의 템플릿 하단에 「선택지가 둘 이상이면 도구로 묻는다」 한 줄로만 복원됐다. 후보 개수에 따른 채널 분기 규칙은 증식 진원지로 판정되어 되살리지 않았다(`[[unenforceable-norm-minimal-design]]`).

## 관련 페이지

- [[unenforceable-norm-minimal-design]]
- [[agent-md-digest-pattern]]
- [[lean-core-relocation-benefit-precondition]]
- [[norm-proliferation-spiral-without-enforcement]]
- [[template-precedence-over-prose-norms]]
