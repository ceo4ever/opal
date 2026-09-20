---
template: sdlc-v2
---
# TEST-SCENARIO: SDLC 템플릿과 하네스 수행 기준 개편

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM(PLAN 작성 워커와 분리)

## Setup

- 환경: 이 저장소의 `opal/` 원본과 Python 테스트 환경. 결정론 검사는 임시 태스크 폴더에서 수행한다.
- 설치 경계: S-1~S-8의 소스 검증이 통과한 뒤에만 정식 설치를 수행한다. 설치 검증 전에는 `~/.opal`을 변경하지 않는다.
- 실제 사례: 기존 MAMS 태스크는 S-10에서 읽기 전용으로 비교한다. S-11의 실제 개발 대상은 별도로 확정한다.
- 작성·검증 책임: 일반 opd에서는 구현 담당자와 독립 test-agent를 분리한다. 이번 하네스 개편은 사용자의 직접 수행 지시에 따라 PM이 실행하되, 공개 CLI 테스트와 Git 기준본 RED 재실행으로 자기확인을 제한한다.
- 대역 사용과 한계: 임시 Markdown과 JSON fixture는 파서 실패 경계를 검증한다. 설치본 opd와 실제 프로젝트 사이클 증거를 대신하지 않는다.
- 상태 기록: 단계·승인은 `state.json`, 시나리오별 PASS/FAIL/BLOCKED와 증거는 `test-scenario.json`이 소유한다. TEST-SCENARIO는 실행 전 검증 기준만 유지한다.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1, AC-3, C-2, C-4, H-1 | 첫 YAML frontmatter가 `template: sdlc-v2`이고 TASK 필수 5개 절이 채워짐 | TASK 계약 검사와 신규 문서 생성 지시 실행 | 신규 형식으로 판정되고 구형 절·중복 표 없이 다음 단계 입력으로 인정됨 | `python -m pytest opal/tools/state-tool/tests/test_state_tool.py` 및 정적 계약 검사 | 구현 전 RED, 구현 후 |
| S-2 | AC-2, AC-3, C-1, C-4, H-1 | sdlc-v2 TASK에서 필수 5개 절을 각각 하나씩 제거하거나 비움 | TASK 계약 검사 실행 | 모든 누락 입력이 비0 종료되고 누락 절을 식별함. skip·PASS 처리 없음 | `python -m pytest opal/tools/state-tool/tests/test_state_tool.py` 매개변수 단위 테스트 | 구현 전 RED, 구현 후 |
| S-3 | AC-3, C-4, H-1 | 정상·필수 누락 legacy TASK와 기존 legacy PLAN 준비 | 기존 명확화 검사와 재개 경로 실행 | 기존 정상 문서는 기존 판정으로 통과하고, 기존 누락 문서는 기존 오류로 거부되며 새 메타데이터를 요구하지 않음 | `python -m pytest opal/tools/state-tool/tests/test_state_tool.py` 회귀 테스트 | 구현 후 |
| S-4 | AC-2, AC-3, C-1, C-4, H-2 | 정상 Work items와 필수 열 누락·중복 W-ID·미확인 선행 W·순환·실행 그룹 역행·같은 그룹 파일 충돌·빈 변경 내용·알 수 없는 AC/C 참조 fixture 준비 | `verify --plan-contract-check` 실행 | 정상 입력만 통과하고 각 잘못된 계약은 원인을 포함해 거부됨. legacy PLAN은 정해진 사유로 skip됨 | `python -m pytest opal/tools/state-tool/tests/test_state_tool.py` 결정론 테스트 | 구현 전 RED, 구현 후 |
| S-5 | AC-3, C-4, H-2 | sdlc-v2 Work items와 legacy §4.2가 각각 코드 파일을 가리킴 | code-scan 인용 검사와 execute 입력 추출 실행 | 신규 문서는 Work items를 우선 사용하고 legacy 문서는 §4.2 폴백을 사용함. 둘 다 대상 파일·인용 누락을 동일 기준으로 판정함 | state-tool·execute 회귀 테스트 | 구현 전 RED, 구현 후 |
| S-6 | AC-2, AC-3, C-3, C-4, H-3, H-4 | TASK에 AC/C, PLAN에 H/W, TEST-SCENARIO에 대응 S가 모두 존재 | `scenario-coverage-build` 후 기존 `scenario-coverage-check` 실행 | AC/C는 requirements, H는 hypotheses, S 연결은 covers 필드로 정확히 변환됨. W는 features에 들어가지 않고 전체 커버리지가 통과함 | `python -m pytest opal/tools/test-tool/tests/test_scenario.py` 결정론 테스트 | 구현 전 RED, 구현 후 |
| S-7 | AC-2, AC-3, C-1, C-3, C-4, H-3 | 필수 AC/C 추출 실패·알 수 없는 참조·시나리오 0건·일부 AC/C/H 미연결 fixture 준비 | build와 coverage check 실행 | build 입력 오류 또는 coverage 누락으로 비0 종료하며 빈 분모가 통과하지 않음 | `python -m pytest opal/tools/test-tool/tests/test_scenario.py` 부정·경계 테스트 | 구현 전 RED, 구현 후 |
| S-8 | AC-1, AC-3, C-1, C-2, C-3, H-5 | 네 문서 스킬과 opd pipeline을 새 계약으로 변경 | 작은 태스크를 TASK→ANALYSIS→PLAN→TEST-SCENARIO까지 dry run | 네 문서가 승인 템플릿 절만 사용하고 상태를 본문에 복제하지 않음. RED 선행·독립 평가·실제 연동 한계가 유지됨 | 임시 태스크 source dry run 및 구형 절명·상태 중복 검색 | 구현 후 |
| S-9 | AC-3, C-3, C-5, H-5, H-6 | S-1~S-8 통과 및 정식 설치 준비 | 원본 설치 후 관련 source/installed 파일 비교, 설치본 opd dry run | 변경 대상 파일이 설치본과 일치하고 신규 경로가 동작함. legacy 재개 회귀도 통과함 | `OPAL_AUTO_INSTALL=1 ./scripts/install-mac.sh` 후 비교와 설치본 dry run | 설치 후 |
| S-10 | AC-4, C-3, C-6 | MAMS 178 원본 요구·시나리오와 회고 대입본 준비 | 요구 결과·제약·핵심 검증을 ID별로 대조 | 원본 필수 요구와 핵심 검증의 누락이 0건이거나, 미확인은 명시되어 완료 판정에서 제외됨 | MAMS 원본 읽기 전용 독립 검토 | 구현 후 |
| S-11 | AC-5, C-3, C-6, H-7 | 설치본 검증 완료 및 신규 MAMS 또는 동등 실제 태스크 확정 | 새 opd로 한 사이클을 수행하고 단계별 시각·대기·재작업을 기록 | 작업시간과 전체 경과시간이 분리되고 120분 달성 여부가 실측으로 판정됨. 범위 축소·검증 생략은 성공으로 처리되지 않음 | 실제 프로젝트·벽시계 측정 | 배포 후 |
| S-12 | AC-3, C-4, H-8 | 동일한 opd pipeline을 기본값·interactive·semi-agentic·agentic으로 각각 초기화하고 다중 모드 플래그 충돌 입력 준비 | 초기 모드값, 단계 전이, 사용자 확인·자동 승인·CLOSE 경계를 실행 | 기본값은 semi-agentic이고 세 모드의 기존 승인 규칙이 유지됨. 충돌 플래그는 기존 계약대로 거부됨 | state-tool 모드별 회귀 테스트 | 구현 후 |
| S-13 | AC-6, C-2, C-7, H-9 | MAMS `docs/PROJECT.md`와 최근 태스크의 문서 갱신 사례에 `100.기획/`, `200.개발/`, `900.문서/`, `docs/*` 레지스트리와 네이밍 규칙이 존재함 | PM 디스패치·analysis·plan·execute·test 참조 문서를 신규 경로 기준으로 검색하고 MAMS식 문서 선별·갱신 사례를 대입 | 신규 경로는 `docs/PROJECT.md` 우선, 참조 시점·도메인·네이밍 규칙 기반 선별, 구현 후 갱신 후보 판단을 요구함. 고정 docs 전량 로드와 `PLAN.md §4.2`/F 전제는 legacy 또는 비대상 pilot로 한정됨 | `rg` 기반 잔재 검사, MAMS 읽기 전용 사례 검토, 관련 참조 문서 diff 리뷰 | 구현 후 |
| S-14 | AC-7, C-2, C-8, H-10 | opd가 읽는 skill/reference/agent 문서와 PM dispatch 템플릿 준비 | 고정 “활용 스킬/MCP” 목록, 중복 실행 절차, 실제 주입 capability 소비 경로를 정적·행동 대조 | 단순 capability 카탈로그는 0건이고 PM dispatch가 실제 제공 가능한 capability와 용도를 주입함. 워커는 주입 목록만 소비하며, state-tool·test-tool·evaluator 같은 구조적 호출은 workflow에 남아 있음 | `rg` 정적 감사 + 임시 dispatch 프롬프트 계약 검토 | 구현 후 |
| S-15 | AC-8, C-2, C-9, H-11 | 문서 변경이력 정책과 기존 문서가 함께 존재함 | `opal-doc-standard.md`와 이번 diff 범위를 검토 | 표준은 수기 변경이력 기본 미생성을 명시하고 자체 변경이력 절이 없음. 다른 문서의 기존 이력 일괄 삭제나 installer 정책 변경은 이번 diff에 없음 | 정적 문서 검토 + 변경 파일 목록 대조 | 구현 후 |
| S-16 | AC-9, C-2, C-4, H-12 | 두 스킬 삭제와 활성 레지스트리·안내 정리 완료 | 폴더 존재 검사, 활성 소스 검색, registry JSON parse와 validate 실행 | 두 폴더가 없고 활성 source에 호출·모델·alias 등록이 남지 않음. registry validate는 dangling/unregistered 0건이며 과거 tasks·brain 기록은 보존됨 | `test ! -d`, `rg` 범위 검색, `python3 -m json.tool`, `node opal/tools/skill-registry/skill-registry.js validate` | 구현 후 |
| S-17 | AC-1, AC-2, AC-3, C-1, C-3, C-4, H-2, H-5 | opds SKILL과 pipeline 11행 준비 | pipeline JSON parse·행 identity 비교·임시 opds state init, 본문과 gate 체크리스트 정적 대조 | 기존 11개 id/key/stage/item과 모드 경계는 유지되고 PLAN Gate는 Work items·AC/C/H·scenario gate를, TEST Gate는 test-scenario.json을 요구함. worker duration과 최신 add-row 인자가 본문에 존재함 | JSON/row 비교, state-tool opds fixture 회귀, `rg` 정적 감사 | 구현 후 |
| S-18 | AC-2, AC-3, C-3, C-4, H-5 | 구현 전 RED 행과 구현 후 검증 행이 함께 있고 초기 test-scenario 상태가 없음 | `scenario-init`으로 RED 대상을 표시하고 잠금 실패 확인, 필수 행만 `scenario-red` 기록 후 재잠금, BLOCKED 결과 기록과 status 조회 | 잠금은 `red_required: true` 미확인 행만 식별하고 비대상 행을 요구하지 않음. 기존 필드 미지정 입력은 전부 RED 대상으로 유지됨. `scenario-mark`가 BLOCKED를 기록하고 status가 필수 RED 진행과 BLOCKED 수를 반환함 | `python -m pytest opal/tools/test-tool/tests/test_scenario.py` 공개 CLI 회귀 테스트 | 구현 전 RED, 구현 후 |
