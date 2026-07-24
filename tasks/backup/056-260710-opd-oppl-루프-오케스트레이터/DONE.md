# DONE: opal-pilot-project-loop(oppl) 루프 기반 오케스트레이터 신설

> 완료일: 2026-07-10 17:38 | 스킬: opd (Full Task) | 모드: agentic | 승인: 캡틴 (CLOSE 진입 승인 발화)

## 요약

oppd의 후계 후보로, 선형 Phase가 아닌 **종료조건 있는 2-루프 수렴 구조**(설계 루프 D1~D7 / 실행 루프 L0~L✓)로 규모 있는 프로젝트를 완주시키는 오케스트레이터 `opal-pilot-project-loop`(alias `oppl`)를 신설했다. 검증은 **Evaluator(구현 전 명세 심판) + test-agent(구현 후 동작 검증)** 2원화, 상태는 **3-SSOT tool-gated JSON**(backlog/state/test-scenario)으로 축 분리했다. oppd는 병행 유지(deprecate는 검증 후 별도 판단).

## 완료기준 달성 (TASK.md §명확화 결과)

| # | 완료기준 | 결과 |
|---|---------|------|
| ① | 7개 자산 생성 + 레지스트리 등록 + install 반영 | ✅ oppl SKILL(561줄)·evaluator AGENT·backlog-tool·references 4종 + skills-registry 3.8.0·agents.md v2.0 + install 배포·어댑터 검증 (S-071) |
| ② | 신규 도구 단위/통합 테스트 GREEN | ✅ RED 33케이스 → 전건 GREEN, 통합 재실행 279케이스 신규 회귀 0 (기지 환경성 실패 2건 불변) |
| ③ | oppl 드라이런 1회 동작 검증 evidence | ✅ 설계 루프(CONTRACT→evaluator verdict:pass)→실행 루프 1태스크 완주. H-9 순서·H-4 readonly·H-7 무진전 가드 evidence — `dryrun/DRYRUN-LOG.md` |
| ④ | 변경이력·@header 규칙 준수 | ✅ 컨벤션 진단 fix 1루프 후 Critical/High/Medium 0 (GC-CONVENTION-260710-1709.md) |

## 산출물

**신규 (7)**
- `opal/skills/opal-pilot-project-loop/SKILL.md` — 2-루프 엔진, 3-way 모드 승계(semi-agentic 기본), 종료조건 5종, CLOSE auto-pass 거부
- `opal/skills/opal-pilot-project-loop/references/{loop-control, contract, journey-flow, verification}.md`
- `opal/agents/opal-evaluator-agent/AGENT.md` — checker 패턴 B, verdict-only·readonly, CONTRACT 루브릭절 심판
- `opal/tools/backlog-tool/` — backlog.json SSOT CLI (6서브명령, fcntl 락, BACKLOG.md 자동 렌더)

**확장/수정 (주요)**
- `opal/tools/test-tool/` — scenario-init/lock/mark/status 4서브명령 (RED-first 동결 게이트, lib/scenario.py 격리)
- `opal/tools/state-tool/` — `--skill` enum에 oppl 추가 (스키마 동기)
- `opal/core/references/opal-skills-registry.json`(3.8.0) · `agents.md`(v2.0) · `opal-harness.md`(§9 도구 표 v6.0)
- `scripts/install-mac.sh`(backlog-tool chmod) · `docs/PROJECT.md` · `docs/ARCHITECTURE.md` · `docs/CONVENTIONS.md`(약어 oppl)

**테스트**: `opal/tools/backlog-tool/tests/test_backlog_tool.py`(18케이스) · `opal/tools/test-tool/tests/test_scenario.py`(13케이스) · `state-tool/tests/test_state_tool.py` TestOpplSkillInit(2케이스) — RED-first(작성자≠구현자)

## 검증 기록

- TEST-SCENARIO.md §7 판정: **All Pass** (시나리오 18건, L1 12/L2 6)
- 드라이런: `dryrun/` (PRD·TRD·CONTRACT·QA-SPEC·DRYRUN-LOG·hello-cli 구현)
- 전 과정 추적: `AGENTIC-LOG.md` — 게이트 11회(Pass 9/Fail 2 각 1루프 해소), PM 의사결정 5건, 에스컬레이션 0건

## 후속 과제 (056 범위 외 — 기록)

1. **test-tool `scenario-red` 서브명령** — red_confirmed를 RED 증거와 함께 tool-gated로 갱신하는 경로 부재(현재 init 시드 우회). enforce-don't-advise 보강.
2. **state-tool `state.schema.json` mode enum** — `semi-agentic` 누락(기존 드리프트, CLI는 수용).
3. **backlog-tool 수용기준 수정 서브명령** — evaluator 지적 반영 시 태스크 재등록 외 경로 없음.
4. `test_state_tool.py:33` unused mock import(기존 코드) 정리.
5. 커밋 + oppl 실전 프로젝트 1회 적용 검증 → oppd deprecate 판단.
