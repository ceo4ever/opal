# DONE: SDLC 템플릿·하네스 개편

## Outcome

- 신규 개발 태스크는 `template: sdlc-v2`로 TASK → ANALYSIS → PLAN → TEST-SCENARIO를 작성한다.
- 단계·승인은 `state.json`, 시나리오 결과·증거는 `test-tool`이 관리하는 `test-scenario.json`이 소유한다.
- PLAN `Work items`가 담당·변경 대상·선행 관계·실행 그룹·완료 기준 연결을 정의하며, 동일 그룹의 독립 작업을 병렬 디스패치할 수 있다.
- 프로젝트 지식과 code map을 먼저 확인한 뒤 `docs/PROJECT.md` 레지스트리에서 관련 기획·설계·개발 문서를 선별하도록 분석·디스패치 계약을 정리했다.
- 고정 “활용 스킬/MCP” 카탈로그를 제거하고 PM이 런타임에서 실제 제공 가능한 capability와 용도를 주입하도록 변경했다.
- `op-dev-todo`, `opal-next`를 삭제하고 활성 레지스트리·안내·모델 표를 정리했다.
- opd와 opds의 기존 진행 모드, 사용자 승인 경계, CLOSE 규칙은 유지했다.

## Verification

- state-tool 회귀: 396 passed, 3 skipped, 111 subtests passed
- test-tool 회귀: 42 passed
- sdlc-v2 coverage: requirements 18, hypotheses 12, scenarios 18, all covered
- RED gate: required 7, confirmed 7, scenario spec locked
- 결과: 17 PASS, 0 FAIL, 1 BLOCKED
- skill registry: valid, 85 skills, errors 0, unregistered 0
- opds pipeline: 기존 11개 행 identity 유지, 설치본 semi-agentic init 11행 확인
- 정식 설치: `OPAL_AUTO_INSTALL=1 ./scripts/install-mac.sh` 성공, OPAL Console health 정상
- source/installed 비교: 관련 pilot·agent·reference·tool 본문 일치
- project brain: sdlc-v2 계약 1페이지 추가, 관련 7페이지 갱신, 폐기된 선작성·구형 시나리오·삭제 스킬 5페이지 stale 처리

## Deferred validation

실제 프로젝트 한 사이클이 120분 이내인지에 대한 측정은 수행하지 않았다. 사용자가 설치본을 직접
테스트한 뒤 별도 요청하기로 결정했으므로 `test-scenario.json`의 S-11은 `BLOCKED` 증거로 보존한다.
이번 태스크는 2시간 달성을 주장하지 않으며, 후속 검증에서는 시작·종료 시각과 사용자 대기·외부 대기·
설치 및 환경 오류·재작업 시간을 분리해 기록한다.

## Artifacts

- `TASK.md`, `ANALYSIS.md`, `PLAN.md`, `TEST-SCENARIO.md`
- `state.json`, `test-scenario.json`, `.scenario-coverage-input.json`, `.scenario-gate-history.json`
- `templates/`의 신규 템플릿과 MAMS 178 대입 검토
