---
type: entity
title: test-tool
tags: [tool, testing, pipeline]
sources: [task:039]
related: [state-tool, brain-tool, test-two-tier-system, e2e-cmux-first-playwright-fallback]
created: 2026-06-23
updated: 2026-06-23
status: active
---

## 개요

OPAL 파이프라인의 테스트 수행을 결정론적으로 집행하는 CLI 도구다. 종전에는 테스트 도구 선택·실행이 스킬·에이전트 산문 지시에 흩어져 있었는데, 이를 도구로 못박아 "조언이 아니라 집행한다"(헌법)는 원칙을 테스트 영역에 적용한다. 테스트 도구 레지스트리(test-tools.yaml)를 읽어 단계×영역(단위/통합 × FE/BE)별 도구셋을 해석하고, 해당 도구를 실행해 PASS/FAIL을 판정한다.

## 책임 (WHAT)

- **도구 해석(resolve)**: 프로젝트→글로벌→스택 추론 우선순위로 테스트 도구 레지스트리를 해석해, 단계×영역별 도구셋을 JSON으로 반환한다 (`opal/tools/test-tool/lib/resolver.py`).
- **설치 게이트(check)**: 필수 도구 미설치는 차단(exit≠0), 선택 도구 미설치는 skip으로 판정한다 (`opal/tools/test-tool/lib/runner.py`).
- **단위 검증(unit)**: lint→build/type→unit 순서로 한 계층 실패 시 다음 계층을 실행하지 않는 stop-on-fail 단발 실행을 수행한다. watch 모드를 쓰지 않는다 (`opal/tools/test-tool/lib/runner.py`).
- **통합 검증(integration)**: E2E를 외부 브라우저 도구로 위임하고, 실DB 기반 API 검증을 집행한다. mock을 금지한다 (`opal/tools/test-tool/lib/e2e_adapter.py`).
- 4개 서브명령(resolve/check/unit/integration) 모두 JSON `{ok, ...}`을 출력하고, 에러는 도구 내부 ERROR_CODES 카탈로그 키로만 표현한다 (`opal/tools/test-tool/test_tool.py`).

## 설계 배경 (WHY)

- **결정론적 집행으로의 대체**: 테스트 도구 선택·실행을 산문 지시에서 도구로 옮긴 이유는 누가 실행해도 일정한 판정이 나오게 하기 위함이다 — 하네스가 품질을 보장한다는 프로젝트 원칙과 정합한다 (근거: task:039 DONE§1).
- **기존 도구 패턴 답습**: 신규 도구를 처음부터 설계하지 않고 [[state-tool]]·cmux-tool의 검증된 골격(run.sh 디스패처 + .venv python 위임 + 에러코드 카탈로그 + JSON 출력)을 재사용했다. 표준화 우선 원칙과 학습 비용 절감을 위해서다 (근거: task:039 PLAN§3.3.2).
- **얇은 래퍼 원칙**: 러너(pytest/vitest/cmux 등)를 재구현하지 않고 레지스트리 해석→명령 실행→증거 반환만 담당한다. 단순성 우선(헌법 §2) (근거: task:039 PLAN§3.3.2).
- **루프 한도 비보유**: test-tool은 1회 실행·판정만 수행하고 PASS-or-fix 재시도 루프는 오케스트레이터가 책임진다. 한도 수치를 도구에 복제하지 않고 하네스 SSOT 포인터만 둔다 — 한도 이중화 방지 (근거: task:039 PLAN§3.3.2).
- **앱 기동 책임 비보유**: 통합 검증 시 앱(SUT) 기동은 도구 책임 밖이며, 가동 전제만 검사하고 미가동이면 에스컬레이션한다. 포트 관리·프로세스 라이프사이클은 도구 경계 밖이라는 판단 (근거: task:039 PLAN§3.3.3).

## 관계 (HOW)

- [[state-tool]] — run.sh + .venv python 위임, ERROR_CODES 카탈로그, JSON 출력 패턴을 복제한 동형 도구
- [[brain-tool]] — state-tool 패턴을 공유하는 또 다른 동형 결정론적 집행 도구
- [[test-two-tier-system]] — test-tool이 집행하는 단위/통합 2단계 체계의 개념 정의
- [[e2e-cmux-first-playwright-fallback]] — integration 서브명령의 E2E 어댑터가 따르는 폴백 전략
- cmux-tool — integration의 E2E 어댑터가 subprocess로 호출해 에러코드를 소비하는 외부 도구

## 소스 커버리지

| 식별자 | 경로 | 설명 |
|--------|------|------|
| run.sh | `opal/tools/test-tool/run.sh` | .venv python 위임 디스패처 (state-tool 패턴) |
| test_tool.py | `opal/tools/test-tool/test_tool.py` | argparse 4서브명령 라우터 + ERROR_CODES 카탈로그 + JSON 출력 |
| resolver.py | `opal/tools/test-tool/lib/resolver.py` | resolution_order(project→global→추론) 해석, `OPAL_TEST_TOOLS_GLOBAL` env 지원 |
| runner.py | `opal/tools/test-tool/lib/runner.py` | unit 계층 stop-on-fail + check required/optional 게이트 |
| e2e_adapter.py | `opal/tools/test-tool/lib/e2e_adapter.py` | cmux-tool subprocess 호출→에러코드 소비→폴백/에스컬레이션, `OPAL_CMUX_TOOL_CMD` env 오버라이드 |
| tests/test_test_tool.py | `opal/tools/test-tool/tests/test_test_tool.py` | 11개 RED-first 행위 계약 테스트 |
