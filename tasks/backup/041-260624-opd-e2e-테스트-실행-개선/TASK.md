# TASK: E2E 테스트 실행 개선 — test-tool playwright 폴백 + TEST-SCENARIO 배선 + OPAL_TEST_TOOLS_GLOBAL 등록

> 작성일: 2026-06-24 | 작업 유형: 개선 | 적용 스킬: opd | 모드: agentic

## 작업 목표

test-tool을 배포한 이후에도 다른 프로젝트의 TEST 단계에서 E2E 테스트가 실행되지 않는 3가지 구조적 원인을 모두 해소한다.

## 배경

태스크 039에서 test-tool(4서브명령)을 구축하고 배포했지만, 다른 프로젝트 적용 후 E2E가 미실행됨을 확인. 원인은 단일 코드 결함이 아니라 파이프라인 3개 지점의 연쇄 누락임.

## 배경 분석 (대화에서 도출)

**원인 1 — TEST-SCENARIO.md에 M2 시나리오 부재 (가장 흔한 원인)**
- `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md:91` 조합표 기준 L1×M2 = `—` (불가)
- 변경 영역이 DB 스키마·비즈니스 로직이면 M2 배제됨 → `test-tool integration` 자체가 호출 안 됨
- test-scenario SKILL.md line 181에 `test_mode` 파라미터 미주입 → opal-test-agent 기본값 `e2e` 사용 중이나 M2 시나리오 없으면 무효

**원인 2 — playwright fallback이 stub**
- `opal/tools/test-tool/lib/e2e_adapter.py:119-132` `_run_playwright_fallback` docstring: *"실제 playwright 호출은 구현 범위 밖"*
- cmux 미가용(tmux 비진입·cmux 미설치) → `FALLBACK_CODES` 반환 → ok:true지만 playwright 미실행

**원인 3 — OPAL_TEST_TOOLS_GLOBAL 미설정**
- `opal/tools/test-tool/lib/resolver.py:192-196`: env var 없으면 글로벌 템플릿 탐색 건너뜀
- `scripts/install-mac.sh`에 OPAL_TEST_TOOLS_GLOBAL shell rc 등록 코드 없음
- `~/.opal/templates/test-tools.yaml`이 배포됐어도 env var 미설정이면 항상 inference fallback

## 확정된 설계 방향 (대화에서 합의)

1. **TEST-SCENARIO 개선**: test-tool 사용 명시 강화 — L1/L2 단계별 도구 결정 기준을 test-tool resolve 결과로 확정; M2 트리거 기준을 명확화 (FE 변경 포함 시 M2 의무 포함으로 격상)
2. **playwright fallback (B안)**: `_run_playwright_fallback`이 결정 반환 시 opal-test-agent가 playwright MCP를 직접 호출하도록 배선 — `e2e_adapter.py` 반환값에 `mcp_action` 필드 추가 + `opal-test-agent/AGENT.md` M2 playwright MCP 호출 절차 명시
3. **OPAL_TEST_TOOLS_GLOBAL**: `scripts/install-mac.sh`에 shell rc(`.zshrc`/`.bash_profile`) 등록 코드 추가

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | E2E 테스트가 TEST 단계에서 실제로 실행되도록 3개 지점 수정 | - | - |
| 범위 | op-dev-test-scenario SKILL.md + test-scenario-guide.md + e2e_adapter.py + opal-test-agent AGENT.md + install-mac.sh (5파일) | - | - |
| 제약 | `~/.opal/` 직접 편집 금지(소스→install 배포); 헌법 §2 Simplicity(최소 변경); 플랫폼 독립성(cmux 분기는 에러코드 소비로만) | - | - |
| 완료기준 | ①test-scenario-guide.md M2 트리거 기준 테이블 갱신 확인 ②e2e_adapter.py fallback 시 mcp_action 필드 반환 ③AGENT.md playwright MCP 호출 절차 명시 ④install-mac.sh OPAL_TEST_TOOLS_GLOBAL 등록 코드 존재 |

## 요구사항

- [ ] **F-001** `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` — M2 트리거 기준 명확화: FE 관련 변경(FE 화면·컴포넌트·인증·외부 API) 포함 시 L2/M2 의무 포함 명시; L1×M2 제한 사유 설명 추가
  - **어디에**: `test-scenario-guide.md` §Step 3-b 실행 방식 결정 + 변경 영역 매핑 표
  - **왜**: 워커가 M2 작성 기준을 명확히 알지 못해 누락 (→ 원인 1)
  - **AC**: 변경 영역 매핑 표에 M2 의무 열(FE 포함 시 필수) 존재 + L1×M2 불가 이유 1줄 주석 존재

- [ ] **F-002** `opal/skills/op-dev-test-scenario/SKILL.md` — TEST-SCENARIO.md 작성 시 test-tool resolve 호출하여 도구 결정 명시 + FE 변경 감지 시 M2 시나리오 포함 체크리스트 항목 추가
  - **어디에**: SKILL.md §시나리오 작성 절차 / PM Gate 체크리스트
  - **왜**: 현재 M1/M2/M3 결정이 워커 임의 판단에 의존 (→ 원인 1)
  - **AC**: PM Gate 체크리스트에 "FE 변경 시 M2 시나리오 포함 여부 확인" 항목 존재

- [ ] **F-003** `opal/tools/test-tool/lib/e2e_adapter.py` — playwright fallback 반환값에 `mcp_action` 필드 추가: `{"driver":"playwright","status":"fallback","mcp_action":"browser_navigate","mcp_url":"<url>"}`
  - **어디에**: `_run_playwright_fallback` 함수 반환 dict
  - **왜**: opal-test-agent가 playwright MCP를 써야 함을 알 수 없음 (→ 원인 2)
  - **AC**: `_run_playwright_fallback` 반환 dict에 `mcp_action` 필드 존재 + pytest 통과

- [ ] **F-004** `opal/agents/opal-test-agent/AGENT.md` — M2 playwright MCP 실행 절차 명시: test-tool이 `driver:"playwright"` 반환 시 `mcp__playwright__browser_navigate` 등 playwright MCP로 직접 E2E 수행
  - **어디에**: AGENT.md §실행 방식 M2 처리 절차 (line 170-172 교체/보강)
  - **왜**: 현재 playwright fallback 수신 후 MCP 호출 절차 없음 (→ 원인 2)
  - **AC**: M2 섹션에 playwright MCP tool 사용 절차 및 시나리오별 browser_navigate/snapshot 사용 예시 존재

- [ ] **F-005** `scripts/install-mac.sh` — OPAL_TEST_TOOLS_GLOBAL 환경변수를 shell rc에 등록하는 코드 추가
  - **어디에**: `install_opal` 함수 또는 `install_opal_bin` 함수 내 shell rc 처리 블록
  - **왜**: env var 미설정으로 글로벌 템플릿이 항상 건너뛰어짐 (→ 원인 3)
  - **AC**: install-mac.sh 실행 후 `~/.zshrc`(또는 `.bash_profile`)에 `export OPAL_TEST_TOOLS_GLOBAL=~/.opal/templates/test-tools.yaml` 행 존재

## 제약 조건

- [MUST] `opal/core/references/opal-harness.md` §1: `~/.opal/` 직접 편집 금지 — 소스(`opal/`) 수정 후 install로 배포
- [MUST] `opal/core/references/PRINCIPLES.md` §2: 최소 변경 — 기존 동작 유지, 추가만
- [MUST] `opal/tools/test-tool/lib/e2e_adapter.py:6`: 플랫폼 독립성 — cmux 분기는 에러코드 소비로만
- [MUST] `opal/core/references/PRINCIPLES.md` §3: 인접 코드 개선 금지 — 명시된 5파일만 수정

## 기술 스택

- Python 3.x (test-tool, e2e_adapter.py)
- Bash (install-mac.sh)
- Markdown (SKILL.md, AGENT.md, test-scenario-guide.md)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | e2e_adapter.py | `opal/tools/test-tool/lib/e2e_adapter.py` | playwright fallback stub 수정 대상 |
| D-2 | 소스 | test-scenario-guide.md | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | M2 트리거 기준 수정 대상 |
| D-3 | 소스 | op-dev-test-scenario SKILL.md | `opal/skills/op-dev-test-scenario/SKILL.md` | TEST-SCENARIO 작성 절차 수정 대상 |
| D-4 | 소스 | opal-test-agent AGENT.md | `opal/agents/opal-test-agent/AGENT.md` | M2 playwright MCP 배선 대상 |
| D-5 | 소스 | install-mac.sh | `scripts/install-mac.sh` | OPAL_TEST_TOOLS_GLOBAL 등록 대상 |
| D-6 | 소스 | resolver.py | `opal/tools/test-tool/lib/resolver.py:192-196` | OPAL_TEST_TOOLS_GLOBAL 소비 위치 |
| D-7 | 소스 | opal-harness.md | `opal/core/references/opal-harness.md` | Guards + 배포 경계 제약 |
