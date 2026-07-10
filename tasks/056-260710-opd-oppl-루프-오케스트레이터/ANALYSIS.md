# ANALYSIS: opal-pilot-project-loop (oppl) 루프 기반 오케스트레이터 신설

> 작성일: 2026-07-10
> 입력: TASK.md, SPEC.html, REQUEST-DRAFT.md
> 출력: ANALYSIS.md

---

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| 1 | 설계 | SPEC (확정본) | tasks/056-260710-opd-oppl-루프-오케스트레이터/SPEC.html | 루프 제어구조, 워크플로우, 검증 3-tier, 신규자산 확정 |
| 2 | 설계 | TASK.md (명확화결과) | tasks/056-260710-opd-oppl-루프-오케스트레이터/TASK.md | oppl 목표, 범위, 제약, 명확화 4요소 |
| 3 | 설계 | REQUEST-DRAFT.md | tasks/056-260710-opd-oppl-루프-오케스트레이터/REQUEST-DRAFT.md | 스킬 생성 요청서 초안, 에이전트 구성표 |
| 4 | 기획 | docs/PROJECT.md | docs/PROJECT.md | 프로젝트 정의, 주요 컴포넌트, 네이밍 규칙 |
| 5 | 설계 | docs/ARCHITECTURE.md | docs/ARCHITECTURE.md | 컴포넌트 표준, 2-레이어 모델, 배포 경로, 하네스 정의 |
| 6 | 기획 | .opal/AGENT.md | .opal/AGENT.md | PM 검토 기준, Guards, 금지사항 (직접 편집 금지 등) |
| 7 | 설계 | oppd SKILL.md | opal/skills/opal-pilot-project-dev/SKILL.md | 선형 Phase 오케스트레이터, Phase 기반 상태 관리, 액션 기반 실행 |
| 8 | 설계 | opsdd SKILL.md | opal/skills/opal-pilot-sdd/SKILL.md | 6단계 파이프라인, EXECUTE-LOOP, ACT 단위 실행 |
| 9 | 설계 | opd SKILL.md | opal/skills/opal-pilot-dev/SKILL.md | Full Task, 5단계(ANALYSIS~CLOSE), 하네스 3-way 모드 |
| 10 | 소스 | state-tool README | opal/tools/state-tool/README.md | STATE.json SSOT, 9개 서브명령 CLI 패턴, worker-stage 게이트 |
| 11 | 소스 | test-tool README | opal/tools/test-tool/README.md | test-tool 4개 서브명령 (resolve/check/unit/integration), RED-first, stop-on-fail |
| 12 | 설계 | citation-rules.md | opal/core/references/harness/citation-rules.md | 근거 인용 규칙, MUST 토큰, 개발 트랙 매트릭스 |

---

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/skills/opal-pilot-project-dev/SKILL.md` | 선형 Phase 오케스트레이터 (oppd) — 대체 대상 | 참고만, 미변경 | TASK.md §완료기준 — "oppd 병행 유지" |
| `opal/skills/opal-pilot-sdd/SKILL.md` | 6단계 SDD 오케스트레이터 (opsdd) — 루프 학습 | 참고만, 미변경 | SPEC.html §3 EXECUTE-LOOP 패턴 |
| `opal/skills/opal-pilot-dev/SKILL.md` | Full Task (opd) — 하네스 3-way 승계 | 참고만, 미변경 | REQUEST-DRAFT.md:186 — opal-harness.md 승계 |
| `opal/tools/state-tool/run.sh` | STATE.json SSOT 관리 도구 | 재사용 (확장 선택사항) | SPEC.html §2 "state-tool 재사용" |
| `opal/tools/test-tool/run.sh` | 테스트 단계별 도구 실행 | 확장 필요 (scenario-* 서브명령) | SPEC.html:401-402 "test-tool 확장(scenario-*)" |
| `opal/tools/brain-tool/run.sh` | 프로젝트 지식 위키 도구 | 참고 (패턴) | docs/PROJECT.md §주요 컴포넌트 |
| `opal/agents/opal-convention-checker/AGENT.md` | 컨벤션 체크 (checker 패턴 B) | 패턴 학습, 미변경 | SPEC.html §6 "패턴 B, checker 선례" |
| `opal/agents/opal-security-checker/AGENT.md` | 보안 체크 (checker 패턴 B) | 패턴 학습, 미변경 | docs/ARCHITECTURE.md §에이전트 — security-checker |
| `opal/core/references/opal-skills-registry.json` | 스킬 레지스트리 | 신규 oppl 등록 필수 | TASK.md §완료기준① |
| `opal/core/references/agents.md` | 에이전트 레지스트리 | 신규 evaluator 등록 필수 | SPEC.html §6 "opal-evaluator-agent" |
| `scripts/install-mac.sh` | 배포 스크립트 | 반영 필수 (oppl 포함) | .opal/AGENT.md — install 배포 원칙 |

### 1.2 아키텍처 패턴

**oppd (opal-pilot-project-dev) — 선형 Phase 오케스트레이터**
- 구조: 3 Phase (1-PLAN → 2-WBS → 3-EXECUTE), Phase 기반 상태 (비표준 행)
- 에이전트: planning-agent + task-action-agent, PM 조율
- oppl 재사용: STATE 기본 구조, 하네스 3-way 모드

**opsdd (opal-pilot-sdd) — SDD 기반 오케스트레이터**
- 구조: 6 Phase (SPEC → VERIFY → PLAN → DESIGN → EXECUTE-LOOP → VERIFY → CLOSE)
- 특성: EXECUTE-LOOP에서 opal-sdd-action-agent 단일 디스패치
- oppl 재사용: RED-first 테스트 패턴, ACT 단위 실행 아이디어

**opd (opal-pilot-dev) — Full Task (5단계)**
- 구조: TASK → ANALYSIS → PLAN → TEST-SCENARIO → EXECUTE
- 하네스: 3-way 모드(semi-agentic 기본) 완전 지원 **← oppl이 그대로 승계**
- oppl 재사용: 5단계 패턴, citation-rules.md 적용 동일

### 1.3 의존성 맵

```
oppl (신규)
  ├─ oppd ← Phase 기반 상태관리, 액션 단위 실행 아키텍처
  ├─ opsdd ← EXECUTE-LOOP 패턴, RED-first 테스트
  ├─ opd ← **하네스 3-way 모드 그대로 승계**, citation-rules 동일
  ├─ state-tool ← STATE.json SSOT (루프 회전 추적 약간 확장)
  ├─ test-tool ← scenario-* 서브명령 신규 추가
  ├─ opal-evaluator-agent (신규) ← checker 패턴 B(convention-checker 선례)
  └─ planning-agent, plan-agent, test-agent ← 디스패치 대상으로 재사용
```

### 1.4 테스트 현황

| 대상 | 테스트 | 수행 필요 |
|------|--------|---------|
| oppl 스킬 | 단위/통합 | YES (신규) |
| backlog-tool | 단위 | YES (신규) |
| test-tool 확장 | 통합 | YES (확장) |
| opal-evaluator-agent | 통합 | YES (신규) |
| oppl 드라이런 | E2E | YES (설계 루프 → 실행 루프 1태스크) |

---

## 2. 외부 조사 결과

### 2.1 루프 엔지니어링 설계 근거

REQUEST-DRAFT.md §3에 따라 Anthropic, Data Science Dojo, MindStudio의 orchestrator-workers, evaluator-optimizer, 루프 종료 제어 패턴 활용.

### 2.2 OPAL 내부 검증 3-tier 패턴

① 결정론(code): test-tool L1~L3
② 루브릭(LLM): opal-evaluator-agent  
③ 사람(human): User Gate

근거: SPEC.html §4 "검증 3-tier + 기준 항목"

---

## 3. 영향 범위

### 3.1 직접 영향

**신규 생성** (7개 자산):
1. `opal/skills/opal-pilot-project-loop/SKILL.md` — oppl 오케스트레이터
2. `opal/agents/opal-evaluator-agent/AGENT.md` — 전담 평가 에이전트
3. `opal/tools/backlog-tool/run.sh` — 백로그 관리 도구 (JSON SSOT)
4. `opal/skills/opal-pilot-project-loop/references/` — 4개 참조 문서
5. `opal/core/references/opal-skills-registry.json` — oppl 등록
6. `opal/core/references/agents.md` — opal-evaluator-agent 등록
7. `scripts/install-mac.sh` — oppl + backlog-tool 배포 반영

**확장 필요**:
- `opal/tools/test-tool/run.sh` — scenario-init, scenario-lock, scenario-mark, scenario-status

### 3.2 간접 영향

기존 컴포넌트는 변경 없음 (재사용만). oppd/opsdd/opd는 병행 유지.

### 3.3 영향 범위 요약

- [ ] DB 스키마 변경
- [ ] API 인터페이스 변경
- [ ] 설정/환경변수 변경
- [x] 빌드/배포 파이프라인 변경 — install-mac.sh
- [x] 레지스트리 변경 — opal-skills-registry.json, agents.md (opal/core/references/)
- [x] 문서 추가 — docs/PROJECT.md 컴포넌트 테이블

---

## 4. 핵심 발견 사항

1. **2-루프 수렴 구조 확정** — 설계 루프(D1~D7) / 실행 루프(L0~L∞) 근거: SPEC.html §3

2. **검증 2원화** — Evaluator(구현 전) + test-agent(구현 후) 근거: SPEC.html §4, checker 패턴 B

3. **3-SSOT tool-gated 아키텍처** — backlog.json / state.json / test-scenario.json 근거: SPEC.html §2

4. **기존 컴포넌트 재사용 극대화** — Evaluator 외 신규 에이전트 금지 근거: TASK.md §명확화①

5. **하네스 3-way 모드 승계** — opd 모드 그대로 적용 근거: opd SKILL.md:24-30

---

## 5. 제약/리스크

| 항목 | 심각도 | 근거 |
|------|--------|------|
| backlog-tool JSON 스키마 설계 필수 | HIGH | SPEC.html:401 |
| test-tool scenario-* 설계 필수 | HIGH | SPEC.html:402 |
| opal-evaluator-agent 루브릭 설계 필수 | HIGH | SPEC.html §4 |
| CONTRACT 산출물 작성 규칙 필수 | MEDIUM | SPEC.html:145 |
| STATE.json 루프 추적 확장 | MEDIUM | SPEC.html:154 |
| oppd deprecate 시점 정책 필요 | MEDIUM | TASK.md §완료기준⑤ |

---

## 6. 기술 컨텍스트

### 6.1 기술 스택

| 카테고리 | 기술 |
|----------|------|
| 언어 | Markdown, YAML, Bash |
| 프레임워크 | OPAL 프레임워크, state-tool, test-tool |
| 런타임 | Node.js (선택), Python 3.8+ (선택) |

### 6.2 추천 스킬

| 스킬 | 용도 |
|------|------|
| op-dev-analysis | 기존 컴포넌트 분석 |
| op-dev-plan | 설계 루프 패턴 |
| op-dev-test-scenario | RED-first 패턴 |
| opal-skill-creator | SKILL.md 자동 생성 |

### 6.3 추천 MCP

| MCP | 용도 |
|-----|------|
| context7 | 하네스/reference 문서 조회 |
| sequential-thinking | 루프 제어 로직 설계 |

---

## 7. 재사용 대상 컴포넌트 (확정)

**에이전트**: opal-planning-agent, opal-plan-agent, opal-be/fe/db-agent, opal-test-agent, convention/security-checker

**도구**: state-tool, test-tool, brain-tool(선택)

---

## 8. 신규 생성 필요 컴포넌트 (확정)

**에이전트**: opal-evaluator-agent (패턴 B, readonly verdict-only)

**스킬**: opal-pilot-project-loop (alias: oppl)

**도구**: backlog-tool + test-tool scenario-* 확장

**참조**: loop-control, contract-evaluator, journey-flow, verification 가이드

---

## 9. MUST 제약

[MUST] `~/.opal/` 직접 편집 금지 — `opal/` 소스에서만 작성 후 install 배포

[MUST] 기존 컴포넌트 재사용 — Evaluator 외 신규 에이전트 금지

[MUST] 3-SSOT tool-gated — BACKLOG.md/STATE.md 손편집 금지

[MUST] 헌법 준수 — 생성자≠평가자, enforce-don't-advise, done=verified

