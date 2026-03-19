# TASK: 테스트 도구 레지스트리 설계 및 TEST-SCENARIO 통합

> 작성일: 2026-03-19 | 작업 유형: 신규 개발

## 작업 목표

프로젝트별 테스트 도구를 선언적으로 관리하는 레지스트리(`.opal/test-tools.yaml`)를 설계하고, TEST-SCENARIO 작성 시점에 도구를 결정하도록 `test-scenario-guide.md`를 개선한다.

## 배경

현재 task-flow-test는 테스트 도구를 EXECUTE 완료 후 런타임에 즉석 결정한다. 이로 인해:
1. 테스트 시나리오 작성 시 어떤 도구로 테스트할지 명확하지 않음
2. 도구 미설치 여부를 테스트 실행 직전에야 발견
3. 프로젝트마다 가용 도구가 다른데 통합 관리 수단이 없음

## 요구사항

- [ ] `.opal/test-tools.yaml` 스키마 설계
  - 스택 무관 필수 도구 (gitleaks 등 보안 스캔)
  - 스택 선언 (`stack: typescript` 등)
  - 카테고리별 도구 정의 (unit, e2e, lint, typecheck, security 등)
  - 각 도구: name, purpose, check 명령, install 명령, required 여부
- [ ] `test-scenario-guide.md` 개선
  - TEST-SCENARIO 작성 시점(task-flow-agent)에 도구 필드도 결정하도록 변경
  - 도구 결정 기준: `.opal/test-tools.yaml` 레지스트리 참조
  - 시나리오별 테스트 유형 → 도구 선택 흐름 명시
- [ ] `task-flow-test` AGENT.md 개선
  - Step 1 환경 확인 시 `.opal/test-tools.yaml`을 참조하도록 연계
  - 도구 없을 시 자동 설치 흐름 구체화

## 제약 조건

- `.opal/test-tools.yaml`은 프로젝트 루트 기준 (글로벌 기본값 + 프로젝트 오버라이드 구조 고려)
- 기존 TEST-SCENARIO.md 템플릿의 구조는 최대한 유지 (하위 호환)
- 도구 자동 설치는 사용자 확인 후 수행 (무조건 자동 설치 금지)

## 관련 문서

- `skills/task-flow/references/test-scenario-guide.md`
- `agents/claude/task-flow-test/AGENT.md`
- (참고) 앞서 나눈 논의: 도구 결정을 TEST-SCENARIO 작성 시점으로 당기는 것
