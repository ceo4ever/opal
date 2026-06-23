# TEST SCENARIO: 테스트 수행 도구 체계 — FE/BE 2단계 재정의 + 신규 test-tool

> 작성일: 2026-06-23 | 상태: 작성 완료
> 작성자: 알투(PM) + 캡틴 페어 | PLAN.md §리스크 가설 표(H-1~H-11) 기반
> RED-first 트랙: **ON** (test-tool = 도구 로직, self-confirming 고위험 — red-first.md §1.5). 작성자(opal-test-agent red) ≠ 구현자(opal-be-agent).

## 1. 리스크 가설 표

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | F-003 `test-tool resolve` | resolution_order 해석 오류 → 잘못된 tier×scope 도구셋 JSON | P0 | L1 | S-1, S-2 |
| H-2 | F-003 `test-tool unit` | lint→build→unit stop-on-fail 위반(중간 실패에도 진행) → FAIL 은폐 | P0 | L1 | S-3, S-4 |
| H-3 | F-003 `integration` cmux 에러코드 소비 | 폴백 4종/에스컬레이션 5종 오분기 → URL·네트워크 오류를 playwright 우회(헌법 위반) | P0 | L1 | S-5, S-6, S-7 |
| H-4 | F-003 `integration` mode A | open→navigate→close 격리 위반 → 사용자 surface(B/C) 재사용·미정리 | P0 | L1 + L3 | S-8, S-15 |
| H-5 | F-003 `test-tool check` | required 차단 / optional skip 게이트 오류 | P1 | L1 | S-9 |
| H-6 | F-001 yaml/schema 2단계 구조 | 1.0 카테고리 구조 → 2.0 tiers 호환 깨짐 → resolve 파싱 실패 | P1 | L1/L2 | S-2, S-10 |
| H-7 | F-001 dtp-* 7줄 현행화 | 고아 참조 잔존 → R-2 미해소(재고아화) | P1 | L1 | S-11 |
| H-8 | F-004 도구 결정 이중규정 통합 | L107·L131-142를 resolve 단일 SSOT로 통합 실패 → 4단계 탐지 외부 잔존 | P1 | L1 | S-12 |
| H-9 | F-005 E2E 순서 교정 | AGENT.md L161 역순 미교정 → 6문서 우선순위 모순 | P1 | L1 | S-13 |
| H-10 | F-006 L계층 ↔ 2단계 축 충돌 | 3축(L1~L4/L1~L3/단위·통합) 혼동 → L번호 오해석 | P2 | L1 | S-14 |
| H-11 | F-001/F-006/F-007 한도 복제 | 루프 한도 수치 직접 기재 → harness §1 SSOT 이중화 | P2 | L1 | S-14 |

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

> DB 없음 — fixture 파일/스텁이 사전 조건. 모든 fixture는 테스트 코드가 임시 생성(tmp_path) 또는 tests/fixtures/에 둔다.

| fixture | 식별자 | 상태 | 출처 |
|--------|--------|------|------|
| project test-tools.yaml | `tiers.unit.fe`·`tiers.integration.e2e` 포함 v2.0 | 유효 YAML | fixture (tmp_path) |
| global template | `~/.opal/templates/test-tools.yaml` 형태 | 유효 YAML | fixture (tmp_path) |
| yaml 부재 디렉토리 | test-tools.yaml 없음 + package.json 존재 | 추론 폴백 대상 | fixture (tmp_path) |
| 의도적 lint 실패 소스 | lint 위반 1건 포함 | stop-on-fail 트리거 | fixture (tmp_path) |
| cmux-tool 스텁 | error 코드 주입(폴백 4종/에스컬레이션 5종 각각) | 결정론적 JSON 반환 | fixture (stub script) |
| 실 cmux 환경 | `CMUX_SURFACE_ID` 설정된 macOS cmux 세션 | 가용(실측 2026-06-23) | 캡틴 환경 (S-15) |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (호출) | Then (re-read) |
|---------|------------|------------|---------------|
| S-1 | project yaml fixture | `run.sh resolve --project-root <fix>` | JSON에 `tiers.unit.fe/be`·`tiers.integration.e2e` 키 |
| S-2 | project + global fixture | `run.sh resolve` | project 값이 global 우선; yaml 부재 시 추론 폴백 source |
| S-3 | 의도적 lint 실패 fixture | `run.sh unit --scope be` | `layers[lint].status=fail`, build/unit 미실행, `stopped_at=lint`, exit≠0 |
| S-4 | 정상 fixture | `run.sh unit --scope fe` | `layers` 순서 lint→build→unit; 실행 명령에 watch 플래그 없음 |
| S-5 | required 미설치 + optional 미설치 fixture | `run.sh check --tier unit` | required→`blocked=true` exit≠0; optional→skip exit 0 |
| S-6 | cmux 스텁(`not_in_cmux`/`cmux_not_installed`/`surface_parse_failed`/`open_failed`) | `run.sh integration` | `e2e.driver=playwright`, `fallback_reason` 기록 |
| S-7 | cmux 스텁(`usage`/`invalid_surface`/`goto_failed`/`wait_failed`/`eval_failed`) | `run.sh integration` | `escalate=true`, playwright 폴백 안 함, exit=escalation(7) |
| S-8 | cmux 스텁(정상) | `run.sh integration --url <sut>` | 호출 시퀀스 open→navigate→…→close(mode A); `--surface` 미전달 |
| S-9 | required/optional fixture | `run.sh check` | results[].required 플래그 정확 |
| S-10 | v2.0 template fixture | `resolve` 왕복 파싱 | 파싱 성공 + tiers 키 보존 |
| S-11 | 변경 후 소스트리 | `grep -rn "dtp-agent\|dtp-test" opal/` | 잔존 0건 |
| S-12~S-14 | 변경 후 문서 | grep/Read 산출물 검사 | §3 각 기대 결과 |
| S-15 | 실 cmux 세션 + SUT URL | 캡틴이 `run.sh integration --url <localhost>` | cmux browser 신규 열림→이동→닫힘 시각 확인 |

## 3. 검증 시나리오

### L1. 기능 단위 (자동, RED-first 테스트 도구)

#### S-1: resolve가 tiers 도구셋 JSON 반환

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | `test-tool resolve` — test-tools.yaml 읽어 tier×scope 도구셋 반환 (실 소비자 = R-2 해소) |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구 — pytest)** |
| 조건 | project test-tools.yaml fixture(v2.0 tiers 구조) |
| 기대 결과 | exit 0 + JSON에 `tiers.unit.fe`·`tiers.unit.be`·`tiers.integration.e2e` 키 존재 |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/test-tool/tests/test_test_tool.py::TestResolve::test_resolve_returns_tier_toolset_json -v` |
| 결과 | **Pass** |
| 상세 | `PASSED` (exit 0). tiers.unit.fe, tiers.unit.be, tiers.integration.e2e 키 존재 확인. stdout 증거: `11 passed, 9 subtests passed in 4.70s` |

#### S-2: resolve resolution_order — project > global > 추론 폴백

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1, H-6, H-8 |
| 대상 | resolution_order(project→global→pyproject/package.json 추론) |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구 — pytest)** |
| 조건 | (a) project+global fixture 공존 (b) yaml 부재 + package.json 존재 |
| 기대 결과 | (a) project 값 채택 + `source=project` (b) `source=infer` 추론 폴백 (4단계 탐지가 도구 내부 폴백으로 흡수됨 입증) |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/test-tool/tests/test_test_tool.py::TestResolve -v` (test_resolve_order_project_over_global + test_resolve_infer_fallback_when_no_yaml) |
| 결과 | **Pass** |
| 상세 | (a) `test_resolve_order_project_over_global PASSED` — source=project, eslint 채택 확인. (b) `test_resolve_infer_fallback_when_no_yaml PASSED` — source=infer 확인. exit 0. |

#### S-3: unit stop-on-fail — lint 실패 시 build/unit 미실행

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | `test-tool unit` 계층 stop-on-fail (FAIL 은폐 방지) |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구 — pytest)** |
| 조건 | 의도적 lint 실패 fixture (eslint stub이 exit 1 반환) |
| 기대 결과 | `layers[lint].status=fail`, build/unit 계층 미실행(skip 또는 부재), `stopped_at=lint`, exit≠0 |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/test-tool/tests/test_test_tool.py::TestUnit::test_unit_stop_on_fail_lint_blocks_build -v` |
| 결과 | **Pass** |
| 상세 | `PASSED` (exit 0). layers[lint].status=fail, stopped_at=lint, build/unit 미실행 확인. |

#### S-4: unit 계층 순서 lint→build→unit + 단발(watch 금지)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | unit 계층 순서 + watch 모드 금지 (verification-loop §2 [MUST] `:60`) |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구 — pytest)** |
| 조건 | 정상 통과 fixture |
| 기대 결과 | JSON `layers` 순서가 lint→build/type→unit; 실행 명령 문자열에 watch 플래그(`--watch`/`-w`) 없음 |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/test-tool/tests/test_test_tool.py::TestUnit::test_unit_layer_order_lint_build_unit opal/tools/test-tool/tests/test_test_tool.py::TestUnit::test_unit_no_watch_mode -v` |
| 결과 | **Pass** |
| 상세 | 두 테스트 모두 `PASSED`. layers 순서 lint→typecheck→unit 확인, watch 플래그(`--watch`/`-w`) 미포함 확인. |

#### S-5: check — required 차단 / optional skip

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | `test-tool check` required/optional 게이트 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구 — pytest)** |
| 조건 | required 도구 미설치 + optional 도구 미설치 fixture |
| 기대 결과 | required 미설치 → `blocked=true` + exit≠0; optional 미설치 → 해당 `installed=false` + `blocked=false` + exit 0 |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/test-tool/tests/test_test_tool.py::TestCheck::test_check_required_blocks_optional_skips -v` |
| 결과 | **Pass** |
| 상세 | `PASSED`. required 미설치→blocked=true exit≠0, optional 미설치→blocked=false exit 0 확인. |

#### S-6: integration cmux 폴백 4종 → playwright

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | cmux-tool 폴백 트리거 4종(`not_in_cmux`/`cmux_not_installed`/`surface_parse_failed`/`open_failed`) → playwright 전환 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구 — pytest, cmux-tool 스텁 주입)** |
| 조건 | cmux-tool 스텁이 폴백 4종 각각 반환 (PATH 주입 방식 — mock/patch 미사용) |
| 기대 결과 | 4종 모두 `e2e.driver=playwright` + `fallback_reason`에 해당 코드 기록 |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/test-tool/tests/test_test_tool.py::TestIntegrationCmuxFallback::test_integration_cmux_fallback_4codes -v` |
| 결과 | **Pass** |
| 상세 | `PASSED` (9 subtests passed). 폴백 4종(not_in_cmux/cmux_not_installed/surface_parse_failed/open_failed) 전부 e2e.driver=playwright + fallback_reason 확인. |

#### S-7: integration cmux 에스컬레이션 5종 → 폴백 금지

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | 에스컬레이션 5종(`usage`/`invalid_surface`/`goto_failed`/`wait_failed`/`eval_failed`) → 폴백 금지 (헌법: URL·네트워크·명령 오류를 playwright로 우회 금지) |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구 — pytest, cmux-tool 스텁 주입)** |
| 조건 | cmux-tool 스텁이 에스컬레이션 5종 각각 반환 (PATH 주입 방식 — mock/patch 미사용) |
| 기대 결과 | 5종 모두 `escalate=true`, `e2e.driver` ≠ playwright(폴백 안 함), exit=escalation(7) |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/test-tool/tests/test_test_tool.py::TestIntegrationCmuxEscalate::test_integration_cmux_escalate_5codes -v` |
| 결과 | **Pass** |
| 상세 | `PASSED`. 에스컬레이션 5종(usage/invalid_surface/goto_failed/wait_failed/eval_failed) 전부 escalate=true, e2e.driver≠playwright, exit=7 확인. |

#### S-8: integration mode A — open→close 격리 시퀀스

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | mode A 격리 호출 시퀀스 (사용자 surface B/C 재사용 금지) |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구 — pytest, cmux-tool 스텁 주입)** |
| 조건 | cmux-tool 스텁(call log 기록, 정상 응답) + SUT URL |
| 기대 결과 | cmux-tool 호출 시퀀스 open→navigate→(스텝)→close; `--surface` 인자 미전달(신규 surface 강제) |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/test-tool/tests/test_test_tool.py::TestIntegrationModeA::test_integration_mode_a_open_close -v` |
| 결과 | **Pass** |
| 상세 | `PASSED`. cmux-tool 호출 시퀀스 open→navigate→close 확인. --surface 미전달(신규 surface 강제) 확인. exit 0 또는 6 이내. |

#### S-9: error 값이 ERROR_CODES 카탈로그 키와 일치

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3, H-5 |
| 대상 | 모든 에러 응답의 `error` 값이 ERROR_CODES 카탈로그에 정의됨 (state-tool 패턴) |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구 — pytest)** |
| 조건 | 각 서브명령 에러 경로 트리거 |
| 기대 결과 | 반환 JSON의 `error` 값이 카탈로그 키 집합에 포함 |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/test-tool/tests/test_test_tool.py::TestErrorCodesInCatalog::test_error_codes_in_catalog -v` |
| 결과 | **Pass** |
| 상세 | `PASSED`. resolve(yaml_parse_failed), check(required_missing), integration(escalation) — 3경로 모두 error 값이 EXPECTED_ERROR_CATALOG 키에 포함 확인. |

### L2. 프로세스 통합 (자동, 실 파일 왕복)

#### S-10: template v2.0 → resolve 왕복 파싱

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | 재구조화된 template(v2.0 tiers)을 resolve가 파싱 (스키마-구현 정합) |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구 — pytest, 실 template 파일)** |
| 조건 | 변경된 `opal/templates/test-tools.yaml`(실 파일) |
| 기대 결과 | resolve 파싱 성공 + tiers 키 보존 + 유효 YAML(파싱 예외 없음) |
| 도구 | pytest + python resolver |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/test-tool/tests/test_test_tool.py::TestResolve -v` + 실 template 직접 resolver 호출 |
| 결과 | **Pass** |
| 상세 | pytest TestResolve 3/3 PASSED (0.25s). 실 template(`opal/templates/test-tools.yaml`) 직접 파싱: `source=project`, `tiers.unit`, `tiers.integration` 키 보존, `ok=True`. 파싱 예외 없음. |

#### S-11: dtp-* 고아 참조 잔존 0건

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | dtp-agent/dtp-test 현행화 (R-2 해소) |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구 — grep)** |
| 조건 | F-001 변경 후 소스트리 |
| 기대 결과 | `grep -rn "dtp-agent\|dtp-test" opal/` 잔존 0건 |
| 도구 | grep |
| 실행 명령 | `grep -rn "dtp-agent\|dtp-test" opal/` |
| 결과 | **Pass** |
| 상세 | 출력 없음(잔존 0건). `dtp-agent`, `dtp-test` 키워드가 `opal/` 트리 전체에서 미발견. R-2 해소 확인. |

#### S-12: test-scenario-guide 도구 결정 단일 SSOT

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 대상 | L107·L131-142 → `test-tool resolve` 단일 호출 통합, 4단계 탐지=도구 내부 폴백 재기술 |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구 — grep/Read 산출물 검사)** |
| 조건 | F-004 변경 후 test-scenario-guide.md |
| 기대 결과 | "test-tool resolve" 호출 문구 존재 + 4단계 탐지가 "resolve 내부 폴백"으로 기술 + 이중규정(독립 yaml 참조) 제거 |
| 도구 | grep/Read |
| 실행 명령 | `grep -n "test-tool resolve\|resolve 내부 폴백\|4단계 탐지" opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` |
| 결과 | **Pass** |
| 상세 | L114: `test-tool resolve` 호출 문구 존재. L140: `[MUST] test-tool resolve`를 단일 SSOT 호출로 통합. L142: "기존 4단계 탐지 … `test-tool resolve` **내부 추론 폴백**으로 흡수됨 — 가이드에서 별도 집행하지 않는다." 명시. 이중규정 제거 확인. |

#### S-13: 6문서 E2E 우선순위 cmux 1순위 일관

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 대상 | AGENT.md L161 역순 교정 + 문서 간 cmux 1순위→playwright 폴백 일관 |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구 — grep 산출물 검사)** |
| 조건 | F-004·F-005 변경 후 |
| 기대 결과 | AGENT.md·test-scenario-guide에서 cmux가 playwright보다 먼저(1순위) 표기; "playwright/cmux" 역순 잔존 0건 |
| 도구 | grep |
| 실행 명령 | `grep -rn "playwright/cmux\|playwright / cmux" opal/skills/op-dev-test-scenario/ opal/agents/opal-test-agent/` |
| 결과 | **Pass** |
| 상세 | 역순("playwright/cmux") 잔존 0건. AGENT.md L45·L170·L185: `cmux 1순위→playwright 폴백` 정순 표기. test-scenario-guide.md L72·L83·L85: `cmux 1순위 → playwright 폴백` 정순. "playwright/cmux" 역순 완전 제거 확인. |

#### S-14: verification-loop 3축 매핑 표 + 한도 미복제 + 레지스트리 등록

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10, H-11 |
| 대상 | 3축(L계층/검증깊이/2단계) 매핑 표 1곳 정의 + 한도 수치 신규 복제 없음(harness §1 포인터) + tools.md/harness §9 test-tool 등록 |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구 — grep/Read 산출물 검사)** |
| 조건 | F-006·F-007 변경 후 |
| 기대 결과 | verification-loop에 3축 매핑 표 존재 + 한도 수치(2/3/1) 신규 기재 없음(포인터만) + tools.md `## test-tool` 섹션 + harness §9 test-tool 행 존재 |
| 도구 | grep/Read |
| 실행 명령 | `grep -n "3축 명명 매핑" verification-loop-guide.md` + `grep -n "## test-tool" tools.md` + `grep -n "test-tool" opal-harness.md` |
| 결과 | **Pass** |
| 상세 | (1) 3축 매핑 표: verification-loop-guide.md L62 `### 3축 명명 매핑 (혼동 금지)` + L66 SSOT 표 확인. (2) 한도 수치 신규 복제 없음: §7 정합성 표의 2/3/1 수치는 R-2 이전 기존 기재이며 R-5(039) 추가분에서 신규 복제 없음. `harness §1 참조` 포인터 명시(L341·L344·L545). (3) tools.md L416 `## test-tool` 섹션 존재 + L425 루프 한도 harness §1 포인터 방식(수치 미복제). (4) opal-harness.md L245 §9 `test-tool` 행 존재(v5.7 추가). |

### L3. 사용자 협업 (수동, [SUPERVISOR] 마커)

#### S-15: 실 cmux browser mode A 라운드트립 시각 확인 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | `test-tool integration`이 실 cmux 환경에서 browser를 신규로 열고→이동→닫는지(mode A 격리) 실제 동작 |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업). M2(cmux 자동화) 시도 가능 시 병기 — 단 시각 확인은 캡틴** |
| 조건 | 실 cmux 세션(`CMUX_SURFACE_ID` 설정, macOS) + 가동 중인 SUT URL(localhost) |
| 기대 결과 | cmux browser 신규 surface가 열림 → SUT로 navigate → 테스트 후 해당 surface가 close됨(캡틴 작업 surface 미훼손). JSON `e2e.driver=cmux`, `status=pass` |
| 실행자 | [SUPERVISOR] — 캡틴 수동 확인 (PM이 캡틴 입회 하에 실행, naver URL) |
| 결과 | **PASS (캡틴 입회 실검증)** |
| 상세 | `OPAL_TEST_TOOLS_GLOBAL=opal/templates/test-tools.yaml bash opal/tools/test-tool/run.sh integration --url https://www.naver.com` → `{"ok":true,"e2e":{"driver":"cmux","status":"pass","url":"https://www.naver.com","surface":"surface:39"}}` exit 0. **driver=cmux (playwright 폴백 아님)**, 신규 surface:39 생성. ⚠️ **이 실검증이 진짜 결함을 잡음**: 최초 실행 시 `driver=playwright, fallback_reason=cmux_not_installed`로 잘못 폴백 → 근본원인 e2e_adapter가 cmux-tool을 PATH 명령 `"cmux-tool"`로 호출(OPAL cmux-tool은 `~/.opal/tools/cmux-tool/run.sh`로 호출해야 함). 스텁 테스트(S-6~S-8)가 이 결함을 가렸음(테스트·구현 동일 오가정). fix 루프: 테스트 작성자가 `OPAL_CMUX_TOOL_CMD` env 방식으로 RED 교정(4 FAIL) → 구현자가 e2e_adapter 경로 해석 교정(기본 `~/.opal/tools/cmux-tool/run.sh` + env 오버라이드) → 11/11 GREEN → S-15 재검증 driver=cmux PASS. **2개 SUT 확인**: (a) 외부 naver → surface:39, (b) 로컬 `http://localhost:3000`(HTTP 200 가동중) → surface:40 — 양쪽 모두 driver=cmux·status=pass. |

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| 완료기준② R7 | H-1 | L1 | S-1, S-2 | `opal/tools/test-tool/tests/test_test_tool.py`:`[T039/L1-resolve]` | resolve 실 소비자 |
| 완료기준① R7 | H-2 | L1 | S-3, S-4 | `…test_test_tool.py`:`[T039/L1-unit]` | stop-on-fail·단발 |
| 완료기준③ R7 | H-3 | L1 | S-6, S-7, S-9 | `…test_test_tool.py`:`[T039/L1-integration]` | cmux 폴백/에스컬레이션 |
| 완료기준① R7 | H-4 | L1 | S-8 | `…test_test_tool.py`:`[T039/L1-modeA]` | mode A 시퀀스 |
| 완료기준① R7 | H-5 | L1 | S-5, S-9 | `…test_test_tool.py`:`[T039/L1-check]` | required 게이트 |
| 완료기준④ R1 | H-6 | L2 | S-10 | `…test_test_tool.py`:`[T039/L2-schema]` | v2.0 왕복 |
| 완료기준⑥ R2 | H-7 | L2 | S-11 | (grep 검증) | dtp-* 0건 |
| 완료기준⑤ R3,R8 | H-8 | L2 | S-12 | (산출물 검사) | resolve 단일 SSOT |
| 완료기준⑤ R6 | H-9 | L2 | S-13 | (산출물 검사) | E2E 순서 일관 |
| 완료기준⑤⑦ R5,R8 | H-10, H-11 | L2 | S-14 | (산출물 검사) | 3축·한도·등록 |
| 완료기준③ R7 | H-4 | L3 | S-15 | [SUPERVISOR] | 실 cmux 라운드트립 |

> **PM 표준 요청 양식 (S-15 [SUPERVISOR])**:
> ```
> 캡틴, [시나리오 S-15]는 사용자 협업 검증이 필요합니다.
> 요청 내용: 가동 중인 SUT(localhost) 대상으로 test-tool integration을 실행하여, cmux browser가 새 surface로 열리고→이동→테스트 후 닫히는지(캡틴 작업 surface 미훼손) 시각 확인.
> 기대 결과: 신규 surface 열림→navigate→close, JSON e2e.driver=cmux·status=pass.
> 확인 후 결과(PASS/FAIL + 상세)를 알려주세요.
> ```

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | ruff | Warning (비차단) | `F401 os imported but unused` — e2e_adapter.py:33, runner.py:21. `E402 Module level import not at top` — test_tool.py:37 (sys.path.insert 패턴, 의도적 배치). 모두 자동수정 가능 경고 수준, 기능에 영향 없음. |
| 2 | 타입 체크 | py_compile | Pass | 6개 Python 파일 전부 구문 오류 없음 (`python -m py_compile` OK). |
| 3 | 포맷터 | N/A | Skip | black/isort 미설치·미설정. py_compile 구문 검사로 대체. |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 (test-tool 코드) | Pass | `grep -rn "password\|passwd\|secret\|token\|api_key\|apikey" opal/tools/test-tool/ --include="*.py" --include="*.sh"` 0건. 하드코딩 시크릿 미발견. |
| 2 | .gitignore 확인 | Pass | 프로젝트 루트 `.gitignore` 존재. `.env`, `venv/`, `.venv/`, `__pycache__/`, `.playwright-mcp/` 등 민감 경로 포함 확인. |

## 7. 판정

**GREEN 단계 완료 (2026-06-23) — All Pass (S-15 포함 15/15, fix 루프 1회 후)**

> opal-test-agent(be mode)가 S-1~S-14 실행. S-15([SUPERVISOR])는 PM이 캡틴 입회 하에 실검증 → **PASS**(driver=cmux, surface:39). 단 S-15가 진짜 결함(e2e_adapter cmux 호출 경로)을 잡아 fix 루프 1회(테스트 OPAL_CMUX_TOOL_CMD 교정 → 구현 경로 교정 → 11/11 GREEN → S-15 재검증 driver=cmux) 수행.
>
> pytest 실행 결과: `11 passed, 9 subtests passed in 4.70s` (exit code 0)
> 테스트 파일: `opal/tools/test-tool/tests/test_test_tool.py`
> cmux-tool 스텁: `unittest.mock/patch` 미사용 — PATH 주입 방식의 실제 stub 쉘 스크립트 (헌법 §4 mock 금지 준수)
>
> **판정 근거**:
> - S-1~S-9 (L1 pytest 11함수): 전부 PASS (exit 0, 출력 증거 첨부)
> - S-10 (L2 template 왕복): PASS (실 template 파싱, tiers 키 보존 확인)
> - S-11 (L2 grep): PASS (dtp-* 잔존 0건)
> - S-12 (L2 산출물): PASS (test-tool resolve 단일 SSOT 확인)
> - S-13 (L2 산출물): PASS (playwright/cmux 역순 0건, cmux 1순위 일관)
> - S-14 (L2 산출물): PASS (3축 매핑 표 + 포인터 방식 + 레지스트리 등록)
> - S-15 (L3 [SUPERVISOR]): **PASS** — 캡틴 입회 실 cmux 검증, driver=cmux·surface:39 (fix 루프로 e2e_adapter cmux 호출 경로 결함 교정 후)
> - 코드 품질: py_compile PASS, ruff 경고 2건(비차단)
> - 보안: 하드코딩 시크릿 0건, .gitignore 정상
> - 회귀: state-tool 기존 196/197 PASS (1건은 경로 상이한 사전 조건 실패로 test-tool 변경과 무관)

### PM Gate 체크 (7대 강제 룰)

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 — cmux-tool "스텁"은 외부 도구 경계 대체(헌법 §4 mock 금지는 검증 대상 구현 목업화 금지이며, test-tool이 호출하는 외부 cmux-tool의 결정론적 에러코드 주입 스텁은 경계 격리로 허용). 검증 대상(test-tool 자체) 로직은 실제 실행
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전 (H-1~H-11 전부 시나리오 연결)
- [x] L1/L2/L3 계층 명시 (모든 시나리오)
- [x] L3 [SUPERVISOR] 마커 존재 + PM 요청 양식 첨부 (S-15)
- [x] 리스크 가설 표(§1) H-N ID와 시나리오 S-N 1:N 매핑 완전
- [x] 모든 시나리오에 실행 방식(M1/M2/M3) 명시 (계층 L과 함께 §3에 기재)
