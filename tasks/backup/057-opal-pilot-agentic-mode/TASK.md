# TASK: opal-pilot agentic mode 추가

> 작성일: 2026-03-31 | 작업 유형: 신규
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

opd, opds, opp, oppd 4개 오케스트레이터에 **agentic mode**를 추가한다. agentic mode에서는 PM이 사용자를 대행하여 단계 게이트를 자율 통과하고, 꼼꼼한 검토를 통해 태스크를 100% 완수할 때까지 루핑·모니터링한다.

## 배경

현재 모든 opal-pilot 오케스트레이터는 각 단계 완료 시 **사용자 게이트**를 거친다 (하네스 §2 Gates). 간단한 작업이나 신뢰할 수 있는 파이프라인에서도 매 단계마다 사용자 승인을 기다려야 하므로, 자율 실행이 필요한 상황에서 비효율적이다.

agentic mode는 PM이 사용자 역할을 대행하여:
- 단계 게이트에서 PM이 직접 승인/재지시 판단
- QA Gate + PM Gate를 강화 검토로 수행
- 100% 완수까지 자율 루핑
- 크리티컬 블로커만 사용자에게 에스컬레이션

## 요구사항

- [ ] 하네스(opal-harness.md)에 agentic mode 공통 규칙 정의
- [ ] opd(opal-pilot-dev) SKILL.md에 agentic mode 섹션 추가
- [ ] opds(opal-pilot-dev-short) SKILL.md에 agentic mode 섹션 추가
- [ ] opp(opal-pilot-project) SKILL.md에 agentic mode 섹션 추가
- [ ] oppd(opal-pilot-project-dev) SKILL.md에 agentic mode 섹션 추가
- [ ] agentic mode 활성화 방법 정의 (호출 시 옵션 또는 사용자 지시)
- [ ] PM 자율 검토 기준 및 루핑 한도 정의
- [ ] 에스컬레이션 조건 명확화 (PM이 사용자에게 올리는 기준)

## 제약 조건

- 하네스 기존 규칙(Guards, Gates)과 충돌하지 않아야 한다
- 기본 모드(interactive)는 변경 없이 유지 — agentic은 opt-in
- `구현 금지 원칙`과 `커밋 규칙`은 agentic mode에서도 유지 (코드 실행은 사용자 승인 후, 커밋은 사용자 요청 시)
- oppd는 이미 Phase 3에서 opal-task-action-agent를 사용하므로, Phase 1~2 게이트만 agentic 적용

## 기술 스택

- Markdown (SKILL.md, opal-harness.md)

## 관련 문서

- `~/.opal/references/opal-harness.md` — 하네스 공통 인프라
- `~/.opal/skills/opal-pilot-dev/SKILL.md` — opd
- `~/.opal/skills/opal-pilot-dev-short/SKILL.md` — opds
- `~/.opal/skills/opal-pilot-project/SKILL.md` — opp
- `~/.opal/skills/opal-pilot-project-dev/SKILL.md` — oppd
- `.opal/AGENT.md` — PM 검토 기준
