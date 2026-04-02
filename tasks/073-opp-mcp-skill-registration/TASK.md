# TASK: OPAL 스킬 MCP 사전 확인 메커니즘 추가

> 작성일: 2026-04-02 | 작업 유형: 개선 | 적용 스킬: opp | 모드: interactive
> 입력: 캡틴 피드백 (wtm 실행 중 Playwright MCP 미등록으로 런타임 실패 — 스킬 호출 전 사전 확인 없음)
> 출력: mcps.md 수정, web-to-markdown/SKILL.md 수정, (필요 시) opal-harness.md 수정

## 작업 목표

MCP 의존성이 있는 스킬 호출 시, 실행 전에 필요한 MCP가 등록되어 있는지 확인하고 미등록 시 즉시 안내하는 메커니즘을 추가한다.

## 배경

wtm 스킬(`//wtm browser http://...`)을 호출했을 때, Playwright MCP가 미등록 상태임을 스킬 실행 도중에야 발견했다. 현재 OPAL 부트스트랩은 `mcps.md`를 "MCP 사용 요청 시" Lazy 로드하지만, 스킬 실행 전 MCP 가용성을 사전 체크하는 규칙이 없다.

MCP 의존 스킬이 늘어날수록 동일 문제가 반복된다.

## 설계 방향

스킬 선언 + 중앙 등록 가이드 조합:
1. **스킬 SKILL.md**: `required_mcps` 섹션에 필요한 MCP 명시
2. **mcps.md**: 스킬↔MCP 매핑 테이블 + MCP 등록 가이드 추가
3. **하네스 또는 AGENT.md**: 스킬 호출 전 `required_mcps` 확인 규칙 추가

## 요구사항

### T1. mcps.md — 스킬↔MCP 매핑 테이블 + 등록 가이드 추가

- [ ] 현재 `mcps.md` 내용 파악
- [ ] "스킬 MCP 의존성" 테이블 추가: 스킬명 | 필요 MCP | 용도 | 미등록 시 동작
- [ ] Playwright MCP 항목 추가 (wtm 스킬 대상)
- [ ] MCP 등록 방법 가이드 추가 (settings.json 예시 포함)

### T2. web-to-markdown/SKILL.md — required_mcps 섹션 추가

- [ ] `## 의존성` 섹션 상단에 `### 필수 MCP` 서브섹션 추가
- [ ] browser 모드 / Phase 2 진입 전 Playwright MCP 등록 여부 확인 절차 명시
- [ ] 미확인 시 즉시 안내 후 중단 (기존 "Playwright MCP 미등록 시" 안내와 통합)

### T3. AGENT.md Lazy 트리거 — MCP 확인 시점 보강

- [ ] Lazy 트리거 테이블의 "MCP 사용 요청" 조건 검토
- [ ] 필요 시: "MCP 의존 스킬 호출 시 → mcps.md 로드 + 가용성 확인" 규칙 추가 또는 기존 조건 구체화

## 제약 조건

- MCP 가용성 확인은 **스킬 실행 전**(Phase 진입 전)에 수행한다.
- 확인 방법: ToolSearch 또는 세션 컨텍스트에서 MCP 도구 존재 여부 판단.
- 하네스 변경이 필요하면 범위를 최소화한다 (모든 오케스트레이터에 영향).

## 관련 문서

- `~/.opal/references/mcps.md`
- `skills/web-to-markdown/SKILL.md`
- `~/.opal/AGENT.md` (Lazy 트리거 테이블)
- `opal/core/references/opal-harness.md`
