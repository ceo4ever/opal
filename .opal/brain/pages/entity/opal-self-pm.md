---
type: entity
title: opal-self-pm
module: <code-scan @header module>
layer: <code-scan @header layer>
domain: <code-scan @header domain>
exports: []
source_ref: '<코드 파일 경로 — 예: opal/tools/state-tool/state_tool.py>'
header_synced: <YYYY-MM-DD>
tags:
- skill
- operator
- pm
- task-122
sources:
- task:122
related:
- actor-axis-orthogonal-to-mode
- self-pm-tool
created: '2026-09-12'
updated: '2026-09-12'
status: active
---
## 개요

`opal-self-pm`(`//oppm`)은 소유자가 "대화하면서 직접 해달라"고 요청할 때 발동하는 대화형 PM 작업 루프다. 단계 파이프라인을 가진 Pilot이 아니라, `opal-brain`(`opbr`)과 같은 유형의 operator 스킬이다 — 질문 1개를 던지고 조회·정리를 반복해 작업 범위를 확정한 뒤, PM이 직접 조회·작성·수정·검증까지 수행하고, 완료 전 지식 영향을 전수 판정하고서야 종료한다(근거: task:122 PLAN.md D-13, `opal/skills/opal-self-pm/SKILL.md:1-14`).

## 책임 (WHAT)

- 진입 시 실행 기록 도구([[self-pm-tool]])에 `init`을 호출해 목표를 기록하고, 이후 모든 단계 전이를 그 도구로 남긴다(`opal/skills/opal-self-pm/SKILL.md:64-71`).
- 질문을 한 번에 하나씩만 던지며, 답변 후 조회·정리를 거쳐 결정을 누적한다(`opal/skills/opal-self-pm/SKILL.md:73-87`, 질문 5요소 구성은 `opal/skills/opal-self-pm/references/question-loop.md`가 소유).
- 파일·설정·데이터를 쓰기 전에 목표·범위·변경 대상·결정과 가정·검증 방법·예상 영향의 6항목 계약을 한 번에 제시하고 사용자 승인을 받는다 — 승인 없이는 어떤 쓰기도 시작하지 않는다(`opal/skills/opal-self-pm/SKILL.md:89-112`).
- 완료 직전 기획·설계·프로젝트 문서·CONVENTIONS·SECURITY·brain·memory·code-scan 8영역을 전부 판정하고, 각 영역을 "update" 또는 "no-op + 근거"로 닫는다(`opal/skills/opal-self-pm/SKILL.md:151-164`, 판정 기준은 `opal/skills/opal-self-pm/references/knowledge-sync.md`가 소유).
- 사용자가 최종 확인을 발화하기 전에는 "완료했습니다" 류의 종결 발화를 하지 않는다(`opal/skills/opal-self-pm/SKILL.md:166-171`).
- 독립 검증(보안·컨벤션·리포트)이 필요하면 `op-gc-security`·`op-gc-convention`·`op-gc-report` 3종을 호출만 하고 스스로 채점하지 않는다 — 생성자≠평가자 원칙 준수(`opal/skills/opal-self-pm/SKILL.md:130-136`).

## 설계 배경 (WHY)

- (근거: task:122 PLAN.md D-13) `opal-self-pm`은 Pilot이 아니라 `opal-brain`과 동일 유형으로 분류된다 — 둘 다 단계 파이프라인과 워커 디스패치를 갖지 않는다. 그래서 `state-tool init --skill` enum에는 추가하지 **않는다**. 파이프라인 state를 만들지 않는 스킬을 enum에 끼워 넣으면 `state.json`·`test-scenario.json`·`backlog.json` 3-SSOT 경계가 흐려지기 때문이다.
- (근거: task:122 PLAN.md D-13) alias `oppm`은 기존 alias 30여 종(`opp`·`oppd`·`oppl` 포함)과 충돌하지 않는다 — 레지스트리 `groups.opal`에 별도 항목으로 등재된다.
- (근거: task:122 PLAN.md D-2, `opal/skills/opal-self-pm/SKILL.md:31`) 독립 검증 경계와 GC 3종 호출 지점의 공유 계약은 이 스킬이 소유하지 않는다 — `harness/actor.md` §독립 검증 경계와 GC 호출 지점이 원문 SSOT이며, `opal-self-pm`은 호출 시점만 규정하고 원문을 복제하지 않는다.
- (근거: task:122 AGENTIC-LOG.md 엔트리 #32~#33) 초안에는 `## 변경이력` 표와 frontmatter `version`이 있었으나, `opal-doc-standard.md` §5의 "이름과 무관하게 수기 누적 이력 절 금지" 위반으로 PM이 재지시해 제거했다. `version` 필드는 레지스트리 스키마를 실측해 소비자가 없음을 확인한 뒤에야 삭제했다.

## 관계 (HOW)

- [[actor-axis-orthogonal-to-mode]] — 같은 태스크가 신설한 또 다른 실행 경로(`--pm` actor 축)와 대비되는 대안이다. `--pm`은 기존 Pilot 파이프라인(`opd`/`opds`)의 단계·상태·Gate를 유지한 채 실행 주체만 PM으로 바꾸는 반면, `//oppm`은 파이프라인 자체가 없는 별개의 대화형 루프다. 소유자는 이 둘과 기본 워커 실행(`//opd`·`//opds`) 사이에서 셋 중 하나를 고른다.
- [[self-pm-tool]] — `opal-self-pm`의 모든 단계 전이가 기록되는 전용 CLI. `opal-self-pm`은 이 도구를 통해서만 자기 실행 이력을 남기며, 3-SSOT(`state.json`·`test-scenario.json`·`backlog.json`)에는 접촉하지 않는다.
- `op-gc-security`·`op-gc-convention`·`op-gc-report` — 독립 검증이 필요할 때 호출만 하는 대상. 파라미터·finding 스키마는 각 스킬이 소유한다.

## 소스 커버리지

| 식별자 | 경로:줄번호 | 설명 |
|--------|-----------|------|
| `alias: oppm`, `triggers` | `opal/skills/opal-self-pm/SKILL.md:8-11` | 레지스트리 발동 표면 |
| 루프 단계 다이어그램 | `opal/skills/opal-self-pm/SKILL.md:37-60` | 진입→질문→계약→승인→작업→동기화→확인→종료 |
| `references/question-loop.md` | `opal/skills/opal-self-pm/references/question-loop.md` | 질문 5요소·시점별 조회 우선순위 |
| `references/knowledge-sync.md` | `opal/skills/opal-self-pm/references/knowledge-sync.md` | 8영역 판정 기준·무근거 생략 금지 |
| 레지스트리 등재 | `opal/core/references/opal-skills-registry.json`(`groups.opal`, v3.18.0) | Pilot이 아닌 operator 스킬로 등재 |
