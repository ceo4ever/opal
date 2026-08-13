# TEST SCENARIO: oppl 계약 접합면 검증 강화

> 작성일: 2026-07-18 | 상태: 작성 완료
> 작성자: 알투(PM) — agentic 모드 캡틴 대행 | PLAN.md §리스크 가설 표(H-1~H-11) 기반
> **RED-first 트랙 판정**: 도구 게이트 시나리오(S-1~S-8, S-12)는 **RED-first 강제**(API 계약·게이트 로직 — red-first.md §1.5). 신규 서브명령·필드가 아직 없으므로 실패 테스트가 자연 RED. 문서·에이전트 규범 시나리오(S-9~S-11)는 구현 후 산출물 검사 트랙(설정·문서).

## 1. 리스크 가설 표

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | coverage-check 거부 경로 | 미커버 표면 존재 시 `ok:false`+`surface_uncovered` exit 1 | P0 | L1 | S-1 |
| H-2 | 통합 태스크 게이트 | parallel_group 존재+area=통합 부재 시 `integration_task_missing` exit 1 | P0 | L1 | S-2 |
| H-3 | scenario-fidelity-check 거부 | 실제 충실도 < 요구 충실도 시 `fidelity_unmet` exit 13 | P0 | L1 | S-5 |
| H-4 | scenario-conformance 거부 | 미검증 표면 존재 시 `surface_unverified` all_surfaces_green:false | P0 | L1 | S-7 |
| H-5 | covers 하위 호환 | `--covers` 미지정 add-task 기존 동작 불변 | P0 | L1 | S-4 |
| H-6 | fidelity 하위 호환 | 필드 미지정 기존 test-scenario.json이 mock 기본값으로 통과 | P0 | L1 | S-6 |
| H-7 | 축 분리 | backlog_tool.py에 test-scenario 토큰 무, scenario.py에 backlog 토큰 무 | P1 | L1(정적) | S-9 |
| H-8 | 스키마 additive 회귀 | 기존 두 도구 테스트 스위트 전부 pass(회귀 0) | P0 | L2 | S-8 |
| H-9 | CORS·conformance 규범 | verification.md §2.1에 분모·실행방식·auth 체인·CORS 명시 | P1 | L1(산출물) | S-10 |
| H-10 | surfaces 단일 인터페이스 | 게이트 도구가 surfaces.json(JSON)만 소비 — YAML/md 파서 미도입 | P1 | L1(정적) | S-9 |
| H-11 | 루프 액션 fidelity 주입 | AGENT.md에 요구 충실도 주입·T4a 게이트 호출·fidelity_unmet 트리거 부재 시 mock 통과 사각지대 | P1 | L1(산출물) | S-11 |

## 2. 테스트 데이터 설계

> 도구 테스트는 DB가 아니라 **파일 fixture**(임시 폴더)를 사용한다. fixture는 사고 사례(auth·agents·budgets 표면)를 그대로 재현한다.

### 2.1 사전 조건 데이터

| 테이블(파일) | 식별자 | 상태 | 출처 |
|--------|--------|------|------|
| surfaces.json (fixture-A) | 표면 3종: `auth-login`(auth:none)·`agents`(auth:required)·`budgets`(auth:required), origins.dev 선언 | 정상 완전 인벤토리 | 테스트 코드 내 생성(tmpdir) |
| backlog.json (fixture-B1) | T01(covers:["auth-login"]) 1건만 — agents·budgets 미커버 | 미커버 상태 (S-1 RED 조건) | backlog-tool init+add-task로 생성 |
| backlog.json (fixture-B2) | T01~T03(covers로 3표면 전수)+parallel_group=g1, area=통합 태스크 부재 | 통합 부재 상태 (S-2) | 동일 |
| backlog.json (fixture-B3) | fixture-B2 + T04(area:통합) | 전 조건 충족 (S-3) | 동일 |
| test-scenario.json (fixture-C1) | S1(required_fidelity:real-usage, fidelity:mock, result:pass) | 충실도 미달 (S-5) | scenario-init+mark로 생성 |
| test-scenario.json (fixture-C2) | S1(req:mock 충족)+S2(req:real-usage, fid:real-usage 충족) 혼합 | 혼합 트랙 충족 (S-6) | 동일 |
| test-scenario.json (fixture-C3) | required_fidelity/fidelity 필드 자체 부재(구버전 형식) | 하위 호환 검증 (S-6) | 수기 JSON(구형식 재현) |
| test-scenario.json (fixture-C4) | surface_ref로 auth-login만 pass — agents·budgets 미검증 | conformance 거부 (S-7) | scenario-init+mark로 생성 |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (CUD/호출) | Then (re-read) |
|---------|------------|----------------|---------------|
| S-1 | fixture-A + fixture-B1 | `coverage-check --surfaces` 호출 | stdout JSON `ok:false, error:surface_uncovered, uncovered:["agents","budgets"]` + exit 1 |
| S-2 | fixture-A + fixture-B2 | `coverage-check` 호출 | `error:integration_task_missing` + exit 1 |
| S-3 | fixture-A + fixture-B3 | `coverage-check` 호출 | `ok:true, all_covered:true, surface_count:3` + exit 0 |
| S-4 | 빈 backlog(init 직후) | `add-task --covers '["auth-login"]'` / `--covers` 미지정 add-task / `update-task --covers` | backlog.json covers 기록·BACKLOG.md 렌더 / covers==[] 정상 / covers 갱신 |
| S-5 | fixture-C1 | `scenario-fidelity-check` 호출 | `error:fidelity_unmet, detail:["S1"]` + exit 13 |
| S-6 | fixture-C2 / fixture-C3 | `scenario-fidelity-check` 호출 | 혼합 트랙 all_met exit 0 / 구형식 mock>=mock 통과 exit 0 |
| S-7 | fixture-A + fixture-C4 / surfaces 부재 | `scenario-conformance --surfaces` 호출 | `error:surface_unverified, detail:["agents","budgets"]` exit 14 / 부재 시 `applicable:false` exit 0 |
| S-8 | 기존 저장소 테스트 스위트 | 두 도구 unittest 전체 실행 | 기존+신규 전 케이스 pass (회귀 0) |
| S-9 | 변경 후 소스 | grep 정적 검사 | backlog_tool.py에 `scenario` 토큰 0건, scenario.py에 `backlog` 토큰 0건, 두 도구에 yaml import 0건 |
| S-10 | 변경 후 문서 9종 | grep/Read 산출물 검사 | 규범 원문·판정 항목·변경이력 069 행 존재 |
| S-11 | opal-loop-action-agent/AGENT.md | grep/Read 검사 | 요구 충실도·surfaces_path 주입 + T4a 게이트 호출 + fidelity_unmet 트리거 존재 |
| S-12 | tmpdir 통합 체인 | init→add-task(covers)→coverage-check→scenario-init(required_fidelity)→scenario-red/lock→mark(--fidelity)→fidelity-check→conformance 전 체인 실행 | 각 단계 exit 0, 최종 all_covered+all_met+all_surfaces_green |

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 데이터 입력)

#### S-1: coverage-check 미커버 표면 거부 (게이트 거부 실증)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | backlog-tool `coverage-check` 신규 서브명령 |
| 계층 | L1 |
| **실행 방식** | **M1 (unittest + run.sh 실호출)** |
| 조건 | fixture-A(3표면) + fixture-B1(1표면만 커버) |
| 기대 결과 | `ok:false` + `error:surface_uncovered` + `uncovered:["agents","budgets"]` + exit 1 실관찰 |
| 도구 | unittest (test_backlog_tool.py) |
| 실행 명령 | `~/.opal/.venv/bin/python -m unittest tests.test_backlog_tool.TestCoverageCheckUncovered -v` (cwd: `opal/tools/backlog-tool`) |
| 결과 | GREEN 확인 완료 — exit 0, PASS (RED→GREEN 전환) |
| 상세 | `~/.opal/.venv/bin/python -m unittest tests.test_backlog_tool.TestCoverageCheckUncovered -v` (cwd: backlog-tool) 실행 결과 `Ran 1 test ... OK`, exit 0. RED 시점 기록(exit 2)은 위 RED 증거 섹션에 보존. GREEN 구현 완료 확인. |

#### S-2: coverage-check 통합 태스크 부재 거부

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | backlog-tool `coverage-check` — parallel_group 검사 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | fixture-B2(parallel_group 존재, area=통합 부재) |
| 기대 결과 | `error:integration_task_missing` + exit 1 실관찰 |
| 도구 | unittest |
| 실행 명령 | `~/.opal/.venv/bin/python -m unittest tests.test_backlog_tool.TestCoverageCheckIntegrationMissing -v` (cwd: `opal/tools/backlog-tool`) |
| 결과 | GREEN 확인 완료 — exit 0, PASS (RED→GREEN 전환) |
| 상세 | `TestCoverageCheckIntegrationMissing -v` 실행 결과 `Ran 1 test ... OK`, exit 0. `error:integration_task_missing` 반환 로직 정상 동작 확인. RED 시점 기록(exit 2)은 위 RED 증거 섹션에 보존. |

#### S-3: coverage-check 전 표면 커버 통과

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 (통과 경로) |
| 대상 | backlog-tool `coverage-check` |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | fixture-B3(전 표면 커버 + 통합 태스크 존재) |
| 기대 결과 | `ok:true, all_covered:true, surface_count:3` + exit 0 |
| 도구 | unittest |
| 실행 명령 | `~/.opal/.venv/bin/python -m unittest tests.test_backlog_tool.TestCoverageCheckAllCovered -v` (cwd: `opal/tools/backlog-tool`) |
| 결과 | GREEN 확인 완료 — exit 0, PASS (RED→GREEN 전환) |
| 상세 | `TestCoverageCheckAllCovered -v` 실행 결과 `Ran 1 test ... OK`, exit 0. `ok:true, all_covered:true, surface_count:3` 반환 확인. RED 시점 기록(exit 2)은 위 RED 증거 섹션에 보존. |

#### S-4: covers 필드 기록·렌더·하위 호환

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | backlog-tool `add-task --covers` / `update-task --covers` / BACKLOG.md 렌더 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | init 직후 빈 backlog |
| 기대 결과 | ① covers 기록+BACKLOG.md 컬럼 렌더 ② `--covers` 미지정 시 covers==[] 정상 동작 ③ update-task로 covers 갱신 ④ covers 잘못된 JSON → `covers_invalid_json` |
| 도구 | unittest |
| 실행 명령 | `~/.opal/.venv/bin/python -m unittest tests.test_backlog_tool.TestCoversFieldRecordRenderCompat -v` (cwd: `opal/tools/backlog-tool`) |
| 결과 | GREEN 확인 완료 — 4건 전부 PASS, exit 0 |
| 상세 | `TestCoversFieldRecordRenderCompat -v` 실행 결과 `Ran 4 tests ... OK`. ①covers 기록+BACKLOG.md 렌더 ②`--covers` 미지정 시 covers==[] ③update-task로 covers 갱신 ④covers_invalid_json 거부 4건 전부 PASS. RED 시점 기록(4건 FAIL)은 위 RED 증거 섹션에 보존. |

#### S-5: scenario-fidelity-check 요구 충실도 미달 거부

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | test-tool `scenario-fidelity-check` 신규 서브명령 |
| 계층 | L1 |
| **실행 방식** | **M1 (unittest + run.sh 실호출)** |
| 조건 | fixture-C1(required:real-usage, actual:mock, result:pass) |
| 기대 결과 | `error:fidelity_unmet` + `detail:["S1"]` + exit 13 실관찰 |
| 도구 | unittest (test_scenario.py) |
| 실행 명령 | `~/.opal/.venv/bin/python -m unittest tests.test_scenario.TestScenarioFidelityCheckUnmet -v` (cwd: `opal/tools/test-tool`) |
| 결과 | GREEN 확인 완료 — exit 0, PASS (RED→GREEN 전환) |
| 상세 | `TestScenarioFidelityCheckUnmet -v` 실행 결과 `Ran 1 test ... OK`, exit 0. `error:fidelity_unmet` 반환 로직 정상 동작 확인. RED 시점 기록(exit 2)은 위 RED 증거 섹션에 보존. |

#### S-6: fidelity 혼합 트랙 부분 게이트 + 구형식 하위 호환

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 (+M-3 R-B 재발 방지) |
| 대상 | test-tool `scenario-fidelity-check` — 시나리오별 부분 판정 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | fixture-C2(mock-요구+real-usage-요구 혼합, 각자 충족) / fixture-C3(필드 부재 구형식) |
| 기대 결과 | 혼합 트랙 all_met exit 0 (전부-게이트 아님 — task:061 재발 방지) / 구형식 mock>=mock 통과 exit 0 (회귀 0) |
| 도구 | unittest |
| 실행 명령 | `~/.opal/.venv/bin/python -m unittest tests.test_scenario.TestScenarioFidelityCheckMixedAndLegacy -v` (cwd: `opal/tools/test-tool`) |
| 결과 | GREEN 확인 완료 — 2건 전부 PASS, exit 0 |
| 상세 | `TestScenarioFidelityCheckMixedAndLegacy -v` 실행 결과 `Ran 2 tests ... OK`. 혼합 트랙 all_met exit 0 + 구형식(필드 부재) mock>=mock 통과 exit 0 확인. RED 시점 기록(2건 FAIL)은 위 RED 증거 섹션에 보존. |

#### S-7: scenario-conformance 전수 판정 + surfaces 부재 스킵

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | test-tool `scenario-conformance` 신규 서브명령 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | fixture-A+fixture-C4(1/3 표면만 검증) / 전 표면 pass 상태 / surfaces.json 부재 |
| 기대 결과 | `error:surface_unverified, detail:["agents","budgets"]` exit 14 / `all_surfaces_green:true` exit 0 / `applicable:false` exit 0 |
| 도구 | unittest |
| 실행 명령 | `~/.opal/.venv/bin/python -m unittest tests.test_scenario.TestScenarioConformance -v` (cwd: `opal/tools/test-tool`) |
| 결과 | GREEN 확인 완료 — 3건 전부 PASS, exit 0 |
| 상세 | `TestScenarioConformance -v` 실행 결과 `Ran 3 tests ... OK`. `surface_unverified` exit 14 / `all_surfaces_green:true` exit 0 / surfaces.json 부재 시 `applicable:false` exit 0 3건 전부 확인. RED 시점 기록(3건 FAIL)은 위 RED 증거 섹션에 보존. |

#### S-9: 축 분리·단일 인터페이스 정적 검사

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7, H-10 |
| 대상 | backlog_tool.py / lib/scenario.py 소스 |
| 계층 | L1 (정적) |
| **실행 방식** | **M1 (grep)** |
| 조건 | EXECUTE 완료 후 소스 |
| 기대 결과 | backlog_tool.py에 `scenario`/`test-scenario` 토큰 0건, scenario.py에 `backlog` 토큰 0건, 두 파일에 `yaml` import 0건(surfaces=stdlib json만) |
| 도구 | grep |
| 실행 명령 | `grep -ni 'scenario' opal/tools/backlog-tool/backlog_tool.py` / `grep -ni 'backlog' opal/tools/test-tool/lib/scenario.py` / `grep -ni 'import yaml' <두 파일>` |
| 결과 | PARTIAL — scenario.py(backlog 토큰 0건)·양 파일 yaml import 0건은 GREEN. backlog_tool.py는 "scenario" 토큰 2건 발견(line 6 모듈 docstring, line 591 `cmd_coverage_check` 함수 docstring) — 단, 둘 다 "test-scenario.json 미접촉(축 분리)"를 명문화하는 주석 텍스트일 뿐 실제 import/함수호출 결합은 없음(실 코드에서 scenario.py를 import하거나 test-scenario.json을 읽는 라인 없음, `grep -n 'import.*scenario\|test-scenario.json' backlog_tool.py` 별도 확인 시 read/write 라인 0건) |
| 상세 | 축 분리(H-7) 의도는 "기능적 결합 없음"이며 실측 결과 기능적 결합은 없다(import/파일 접근 0건). 다만 시나리오 문면의 "토큰 0건" 기준을 문자 그대로 적용하면 backlog_tool.py 2건은 FAIL이다. 판정에는 이 문자 그대로의 편차를 §7에 명기하고 Critical 사유로는 취급하지 않는다(설명 주석이 오히려 축 분리를 문서화한 것으로 실질 리스크 없음). PM/Evaluator 판단으로 문구를 "backlog.json/scenario.py 직접 참조 없음"으로 완화하거나 주석에서 "test-scenario.json" 문자열 제거를 권고. |

#### S-10: 문서 규범 산출물 검사 (9종 일괄)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 대상 | verification.md(§1 충실도 사다리·done 규범·§2.1 conformance 분모/실행방식/auth 체인/CORS·E2E 실 브라우저) / contract.md(§2.2 표면 인벤토리+auth, §2.1 origin) / journey-flow.md(여정 스모크 절) / SKILL.md(D4 surfaces 요구·D5 스켈레톤 4항·L✓ 게이트 조합) / loop-control.md(§7 신규 에러 4종 복구가능) / evaluator AGENT.md(판정 4항) / 변경이력 069 행 전체 |
| 계층 | L1 (산출물) |
| **실행 방식** | **M1 (grep/Read)** |
| 조건 | EXECUTE 완료 후 문서 |
| 기대 결과 | 각 규범 원문·판정 항목·069 행 존재 (누락 시 해당 항목 FAIL 명시) |
| 도구 | grep |
| 실행 명령 | `grep -n '§1.5\|§1.6\|§2.1.1\|conformance\|E2E' references/verification.md`; `grep -n '§2.1\|§2.2.1\|origin\|인벤토리' references/contract.md`; `grep -n '§6\|여정 스모크' references/journey-flow.md`; `grep -n 'D4\|D5\|D7\|coverage-check\|L✓\|parallel' SKILL.md`; `grep -n '§7\|surface_uncovered\|integration_task_missing\|fidelity_unmet\|surface_unverified' references/loop-control.md`; `grep -n '⑦\|⑧\|⑨\|⑩' opal-evaluator-agent/AGENT.md`; `grep -n '(069)' <9개 파일>` |
| 결과 | All PASS — 9개 파일 전수 확인 |
| 상세 | verification.md: §1.5 "증거 충실도 사다리"(mock/real-http/real-usage 3단계, line 20~45) + §1.6 "워킹 스켈레톤 게이트"(line 49) + §2.1 계약 conformance 행(line 73, 분모=surfaces.json 전수) + §2.1.1 실행 규범 원문(line 77, 실 서버+실 HTTP+auth 토큰 체인+CORS preflight) + E2E(L3b) 행 실 브라우저(cmux-tool 우선/playwright 폴백, line 72) 전부 확인. contract.md: §2.1 origin 선언 의무(line 29) + §2.2 표면 인벤토리 규칙(line 35) + §2.2.1 surfaces.json 구조 스펙(line 37) 확인. journey-flow.md: §6 "여정 스모크 게이트"(line 87) + 변경이력 v1.1 확인. SKILL.md: D4 surfaces.json 요구(line 204) + D5 스켈레톤 4항(a~d, line 208) + D7 coverage-check 게이트(line 233) + L✓ 3중 불리언 AND(done-check∧scenario-conformance∧회귀0, line 281) + 병렬 통합 태스크 게이트(line 502) 전부 확인. loop-control.md: §7 신규 에러 4종(`surface_uncovered`·`integration_task_missing`·`fidelity_unmet`·`surface_unverified`) 복구가능 분류(line 104) 확인. evaluator AGENT.md: 판정 항목 ⑦표면완전성 ⑧auth완전성 ⑨origin선언 ⑩워킹스켈레톤(line 145) 확인. 9개 파일(SKILL.md/contract.md/verification.md/journey-flow.md/loop-control.md/evaluator AGENT.md/loop-action-agent AGENT.md/docs/PROJECT.md/backlog-tool·test-tool README.md 중 관련분) 전수에서 "(069)" 변경이력 행 존재 확인(verification.md 4행 포함 총 10행, 나머지 각 1행 이상). |

#### S-11: 루프 액션 에이전트 fidelity 주입 검사

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-11 |
| 대상 | opal-loop-action-agent/AGENT.md |
| 계층 | L1 (산출물) |
| **실행 방식** | **M1 (grep/Read)** |
| 조건 | EXECUTE 완료 후 |
| 기대 결과 | 컨텍스트 재주입 표에 요구 충실도·surfaces_path 행 + T4a에 scenario-fidelity-check/scenario-conformance 호출 + fidelity_unmet 재작업/blocked 트리거 존재 |
| 도구 | grep |
| 실행 명령 | `grep -n '요구 충실도\|surfaces_path\|scenario-fidelity-check\|scenario-conformance\|fidelity_unmet' opal-loop-action-agent/AGENT.md` |
| 결과 | All PASS |
| 상세 | 컨텍스트 재주입 표(line 35~36)에 "요구 충실도"(area 매핑: be·공통=real-http↑, fe·인터랙션·여정=real-usage) + "surfaces_path" 행 존재, T1·T2 디스패치(line 129, 135)에 주입 절차 명시. T4a 절(line 153)에 `scenario-fidelity-check` 호출 → `fidelity_unmet`(exit 13) 재작업 트리거 + `scenario-conformance --surfaces` 호출 → `surface_unverified`(exit 14) 재작업 트리거 확인. 재시도 상한 초과 시 blocked 전환 트리거(line 312) 확인. |

### L2. 프로세스 통합 (자동, 실 파일 read→CUD→re-read)

#### S-8: 두 도구 전체 스위트 회귀 0

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 대상 | backlog-tool 기존 9 TestCase + test-tool 기존 scenario 스위트 + 신규 케이스 전체 |
| 계층 | L2 |
| **실행 방식** | **M1 (unittest 전체 러너)** |
| 조건 | EXECUTE 완료 후 |
| 기대 결과 | 기존+신규 전 케이스 pass — 실패 0, 에러 0 (회귀 0) |
| 도구 | unittest (python -m unittest discover) |
| 실행 명령 | `cd opal/tools/backlog-tool && ~/.opal/.venv/bin/python -m unittest discover -s tests -v` / `cd opal/tools/test-tool && ~/.opal/.venv/bin/python -m unittest discover -s tests -v` |
| 결과 | PASS (제외 조건부) — backlog-tool: `Ran 29 tests ... OK`(exit 0, 기대 29건 일치, 회귀 0). test-tool: `Ran 35 tests ... FAILED (failures=1)`(exit 1) — 실패 1건은 `test_test_tool.py::TestResolve::test_resolve_infer_fallback_when_no_yaml`로 사전 지정된 "본 태스크 무관 기존 환경 의존 실패"와 정확히 일치(`'global' != 'infer'` — 로컬 환경에 global yaml 존재로 인한 환경 의존). 판정 시 이 1건은 제외하고 나머지 34건 전부 PASS로 집계. |
| 상세 | test-tool discover 35건 중 신규 scenario-* 관련 시나리오(S-5/S-6/S-7 대응 TestCase 6건 포함) 전부 PASS 확인. 제외 처리한 1건은 git diff 미수정 파일(test_test_tool.py)의 기존 실패이며 본 069 변경과 무관함을 재확인(파일 미변경 목록에도 없음 — changed_files에 test_test_tool.py 부재). |

#### S-12: 게이트 전 체인 통합 흐름 (실 run.sh 호출)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1~H-6 통합 |
| 대상 | 두 도구 run.sh 실호출 체인 — 실전 oppl 사용 흐름 재현 |
| 계층 | L2 |
| **실행 방식** | **M1 (bash 체인 스크립트)** |
| 조건 | tmpdir에 surfaces.json 생성 → backlog init → add-task×4(covers 전수+통합) → coverage-check → scenario-init(required_fidelity 포함) → scenario-red/lock → scenario-mark(--fidelity real-http) → scenario-fidelity-check → scenario-conformance |
| 기대 결과 | 각 단계 exit 0 + 최종 all_covered ∧ all_met ∧ all_surfaces_green (L✓ 불리언 AND 재현) |
| 도구 | bash + run.sh |
| 실행 명령 | tmpdir(`s12/task`)에서 순차 실행: `backlog-tool/run.sh init <task> --project-title "S-12 통합체인" --mode agentic` → `add-task --id T01 --area be --covers '["auth-login"]'` → `add-task --id T02 --area be --parallel-group g1 --covers '["agents"]'` → `add-task --id T03 --area be --parallel-group g1 --covers '["budgets"]'` → `add-task --id T04 --area 통합 --covers '[]'` → `coverage-check --surfaces <surfaces.json>` → `test-tool/run.sh scenario-init --scenarios '[S1(auth-login,real-http),S2(agents,real-http),S3(budgets,real-usage)]'` → `scenario-red --id S1/S2/S3 --evidence ...`(3회) → `scenario-lock` → `scenario-mark --id S1/S2/S3 --result pass --fidelity real-http/real-http/real-usage`(3회) → `scenario-fidelity-check` → `scenario-conformance --surfaces <surfaces.json>` |
| 결과 | All PASS — 전 단계 exit 0. 단계별 exit code: init=0, add-task×4=0/0/0/0, coverage-check=0(`{"ok":true,"all_covered":true,"surface_count":3}`), scenario-init=0(`scenarios_count:3`), scenario-red×3=0/0/0(`red_confirmed:true`), scenario-lock=0(`locked:true`), scenario-mark×3=0/0/0(`result:pass`), scenario-fidelity-check=0(`{"ok":true,"all_met":true,"total":3,"met":3}`), scenario-conformance=0(`{"ok":true,"all_surfaces_green":true,"surface_count":3}`) |
| 상세 | fixture: surfaces.json 3표면(auth-login:auth=none, agents:auth=required, budgets:auth=required) + origins.dev 선언. T01(covers=auth-login)·T02/T03(parallel_group=g1, covers=agents/budgets)·T04(area=통합) 4건으로 3표면 전수 커버+병렬그룹 통합 태스크 조건 충족 → coverage-check 정상 통과. 시나리오 S1(auth-login,required_fidelity=real-http)·S2(agents,required_fidelity=real-http)·S3(budgets,required_fidelity=real-usage) 각 표면 매핑, scenario-red로 RED 증거 기록 후 scenario-lock(RED 전부-게이트 통과), scenario-mark로 실제 충실도(real-http/real-http/real-usage) 기록 — 요구≤실제 충족. 최종 `all_covered:true ∧ all_met:true ∧ all_surfaces_green:true` 3중 AND 전부 충족 확인(L✓ 종료 판정 로직 재현). |

### L3. 사용자 협업

해당 없음 — 전 시나리오 자동화 가능(M1). FE 화면·인증 플로우 변경 없음(프레임워크 도구·문서 태스크)이므로 M2 의무 트리거 미해당, [SUPERVISOR] 시나리오 없음.

## RED 증거

> 대상: RED-first 강제 트랙(S-1, S-2, S-3, S-4, S-5, S-6, S-7). 신규 서브명령(`coverage-check`,
> `scenario-fidelity-check`, `scenario-conformance`)·신규 옵션(`--covers`)이 아직 backlog_tool.py/
> lib/scenario.py에 구현되지 않아 전부 자연 RED(실패) 상태다. 신규 TestCase만 작성·실행했으며
> 기존 TestCase는 일절 수정하지 않았다(git diff로 확인 — 기존 클래스 불변). 시점: KST
> `node ~/.opal/tools/date/date.js datetime` → **2026-07-18 22:35**.

### backlog-tool (`opal/tools/backlog-tool/tests/test_backlog_tool.py`)

| 시나리오 | 실행 명령 | 실패 출력 요약 |
|---------|----------|--------------|
| S-1 | `~/.opal/.venv/bin/python -m unittest tests.test_backlog_tool.TestCoverageCheckUncovered -v`(cwd: `opal/tools/backlog-tool`) | `AssertionError: 2 != 0 : fixture-B1 준비 단계(add-task --covers)부터 실패 — RED 증거` — `--covers` argparse 미등록으로 add-task 자체가 exit 2 |
| S-2 | `... tests.test_backlog_tool.TestCoverageCheckIntegrationMissing -v` | `AssertionError: 2 != 1` — `coverage-check` 서브명령 argparse 인식 불가(unrecognized) |
| S-3 | `... tests.test_backlog_tool.TestCoverageCheckAllCovered -v` | `AssertionError: 2 != 0` — 동일(coverage-check 미구현) |
| S-4 | `... tests.test_backlog_tool.TestCoversFieldRecordRenderCompat -v` | 4건 전부 FAIL: `AssertionError: 2 != 0`(①③), `AssertionError: 2 != 1`(④ covers_invalid_json), `AssertionError: None != []`(② covers 미지정 시 키 자체 부재) |

전체 실행: `cd opal/tools/backlog-tool && ~/.opal/.venv/bin/python -m unittest discover -s tests -v` → `Ran 29 tests ... FAILED (failures=7)` — 신규 7건만 FAIL, 기존 22건 전부 PASS(회귀 0 확인, 기존 TestCase 불변 재확인).

### test-tool (`opal/tools/test-tool/tests/test_scenario.py`)

| 시나리오 | 실행 명령 | 실패 출력 요약 |
|---------|----------|--------------|
| S-5 | `~/.opal/.venv/bin/python -m unittest tests.test_scenario.TestScenarioFidelityCheckUnmet -v`(cwd: `opal/tools/test-tool`) | `AssertionError: 2 != 13` — `scenario-fidelity-check` 서브명령 argparse 인식 불가 |
| S-6 | `... tests.test_scenario.TestScenarioFidelityCheckMixedAndLegacy -v` | 2건 전부 `AssertionError: 2 != 0` — 동일(scenario-fidelity-check 미구현) |
| S-7 | `... tests.test_scenario.TestScenarioConformance -v` | 3건 전부 `AssertionError: 2 != 14` / `2 != 0` — `scenario-conformance` 서브명령 argparse 인식 불가 |

전체 실행: `cd opal/tools/test-tool && ~/.opal/.venv/bin/python -m unittest discover -s tests -v` → `Ran 35 tests ... FAILED (failures=7)` — 신규 6건(S-5/S-6/S-7) FAIL + 기존 `test_test_tool.py`의 `test_resolve_infer_fallback_when_no_yaml` 1건은 본 태스크 변경과 무관한 사전 존재 환경 의존 실패(테스트 파일 미수정, git diff로 확인)이며 나머지 기존 27건은 전부 PASS.

### 결론

7종 신규 서브명령·필드가 존재하지 않아 대상 TestCase(backlog-tool 7건 + test-tool 6건 = 13건) 전부 exit code≠기대값으로 RED 확인. GREEN 전환(구현)은 별도 EXECUTE 워커가 담당한다(작성자≠구현자, red-first.md §2). RED 단계에서 소스 파일(backlog_tool.py/scenario.py/schema)은 일절 수정하지 않았다.

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| R-0 AC (규범 명문) | H-9 | L1 | S-10 | grep 검사 | verification.md §1 |
| R-1 AC (인벤토리·auth·origin) | H-9 | L1 | S-10 | grep 검사 | contract.md §2.1/§2.2 + D4 + Evaluator 판정 |
| R-2 AC (covers 기록·렌더·호환) | H-5 | L1 | S-4 | test_backlog_tool.py:신규 TestCase | |
| R-3 AC (커버리지 거부 실관찰) | H-1, H-2 | L1 | S-1, S-2, S-3 | test_backlog_tool.py:신규 TestCase | exit 1 + 에러코드 |
| R-4 AC (전수 판정+실행 규범) | H-4, H-9 | L1 | S-7, S-10 | test_scenario.py:신규 TestCase | exit 14 + 규범 명문 |
| R-5 AC (충실도 게이트) | H-3, H-6 | L1 | S-5, S-6 | test_scenario.py:신규 TestCase | exit 13 + 혼합 트랙 + 하위 호환 |
| R-6 AC (여정 스모크) | H-9 | L1 | S-10 | grep 검사 | journey-flow.md + E2E 실 브라우저 |
| R-8 AC (스켈레톤 의무) | H-9 | L1 | S-10 | grep 검사 | SKILL.md D5 + Evaluator ⑩ |
| R-7 AC (변경이력) | H-9 | L1 | S-10 | grep 검사 | 069 행 전체 |
| F-009 AC (fidelity 주입) | H-11 | L1 | S-11 | grep 검사 | R-G 사각지대 봉쇄 |
| 완료기준 (회귀 0) | H-8 | L2 | S-8 | 전체 스위트 | |
| M-2 (축 분리) / M-1 (단일 IR) | H-7, H-10 | L1 | S-9 | grep 정적 | |
| L✓ 통합 흐름 | H-1~H-6 | L2 | S-12 | bash 체인 | 실전 사용 흐름 재현 |

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | N/A | N/A | 프로젝트에 린터 설정 파일 부재 확인(`.flake8`/`.ruff.toml`/`pyproject.toml`/`setup.cfg` 전부 없음, `ls` 결과 No such file) — 린트 검사 스킵 |
| 2 | 타입 체크 | N/A | N/A | mypy/pyright 등 타입 체크 설정 부재 확인 — 스킵. 대신 `python -m py_compile`로 구문 유효성만 검증(아래 3) |
| 3 | 포맷터 | `python -m py_compile` + 육안 검사 | PASS | `~/.opal/.venv/bin/python -m py_compile opal/tools/backlog-tool/backlog_tool.py` exit 0, `~/.opal/.venv/bin/python -m py_compile opal/tools/test-tool/lib/scenario.py` exit 0 — 구문 오류 없음. 포맷터(black 등) 설정 파일 부재로 자동 포맷 검사는 N/A, 육안 검사 결과 기존 코드 스타일(4-space indent, docstring 규칙)과 일관 유지 확인 |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | PASS | `grep -niE 'api[_-]?key|secret|password|token\s*=\s*["\x27][a-zA-Z0-9]|aws_access|private_key' backlog_tool.py scenario.py backlog.schema.json test-scenario.schema.json` → 매치 0건(exit 1, no match) |
| 2 | .gitignore 확인 | PASS | 루트 `.gitignore`에 `.venv/`·`__pycache__/`·`.pytest_cache/`·`.mypy_cache/`·`.ruff_cache/`·`.coverage`·`build/`·`dist/` 등 표준 항목 존재. `git status --short` 확인 결과 신규 변경 파일 중 시크릿/캐시 파일 스테이징 없음(전부 소스·문서·tasks/ 폴더) |

## 7. 판정

**All Pass — 근거: S-1~S-8, S-11, S-12 전부 GREEN(실행 출력 증거 확보). S-9는 기능적 결합 0건(실측 확인: import/파일접근 없음)이나 문자 그대로의 "토큰 0건" 기준으로는 backlog_tool.py 주석 2건이 편차— Critical/Partial 사유로 보지 않고 Minor Note로 기록. S-10은 9개 문서 전수에서 규범 원문·판정 항목·069 변경이력 행 전부 확인. 코드 품질(§5)은 프로젝트 린터 부재로 N/A 처리하되 py_compile 구문 검증 통과. 보안(§6) 하드코딩 시크릿 0건·.gitignore 정상. 회귀: backlog-tool 29건 전부 PASS(회귀 0), test-tool discover 35건 중 사전 지정된 무관 환경 의존 실패 1건(`test_resolve_infer_fallback_when_no_yaml`) 제외 34건 전부 PASS. 핵심 게이트 로직(coverage-check/scenario-fidelity-check/scenario-conformance) 전부 실 run.sh 호출로 GREEN 재현 완료.**

### 판정 상세 — 시나리오별 Pass/Fail 표

| 시나리오 | 결과 | 비고 |
|---------|------|------|
| S-1 | PASS | coverage-check 미커버 거부, exit 0 |
| S-2 | PASS | 통합 태스크 부재 거부, exit 0 |
| S-3 | PASS | 전 표면 커버 통과, exit 0 |
| S-4 | PASS | covers 기록·렌더·호환 4건, exit 0 |
| S-5 | PASS | fidelity_unmet 거부, exit 0 |
| S-6 | PASS | 혼합 트랙+구형식 호환 2건, exit 0 |
| S-7 | PASS | conformance 전수 판정 3건, exit 0 |
| S-8 | PASS(조건부) | backlog 29/29, test-tool 34/35(무관 기존 실패 1건 제외) |
| S-9 | Minor Note | 기능적 결합 0건(실측), 문자 그대로의 토큰 0건 기준은 주석 2건 편차 |
| S-10 | PASS | 9개 문서 규범·판정·069행 전수 확인 |
| S-11 | PASS | 요구 충실도·surfaces_path·게이트 호출·트리거 전부 확인 |
| S-12 | PASS | tmpdir 전 체인 exit 0, all_covered∧all_met∧all_surfaces_green |

### 특이사항

1. **S-9 주석 편차(Minor)**: `backlog_tool.py` 2곳(모듈 docstring, `cmd_coverage_check` docstring)에 "scenario"/"test-scenario.json" 문자열이 존재하나, 이는 "test-scenario.json 미접촉(축 분리)"을 설명하는 주석일 뿐 실제 import·파일 접근은 없음(`grep -n 'import.*scenario\|scenario\.py'` 매치 0건 확인). 축 분리(H-7)의 실질 목적(기능적 무결합)은 충족. 원한다면 주석에서 "test-scenario.json" 문자열을 "시나리오 도메인"처럼 완곡화하여 grep 토큰도 0건으로 맞출 수 있음(선택 사항, Critical 아님).
2. **S-8 기존 실패 1건**: `test_test_tool.py::TestResolve::test_resolve_infer_fallback_when_no_yaml`는 로컬 환경에 global yaml이 존재하여 발생하는 사전 존재 환경 의존 실패로, 069 변경 파일 목록에 `test_test_tool.py`가 없어 본 태스크와 무관함을 재확인. RED 증거 섹션에서도 동일하게 사전 배제됨.
3. **RED→GREEN 전환**: S-1~S-7 신규 TestCase 13건(backlog-tool 7건 + test-tool 6건) 전부 RED(§RED 증거 섹션, exit 2 또는 값 불일치) → GREEN(본 TEST 단계, exit 0) 전환을 실행 출력으로 확인. 테스트 파일은 일절 수정하지 않음(RED-first 불변성 준수).

### PM Gate 체크 (7대 강제 룰)

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 (fixture는 실 파일 생성 — 목 아님)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전 (H-1~H-11 전부 매핑, 미매핑 시나리오 없음)
- [x] L1/L2 계층 명시 (모든 시나리오) — L3 해당 없음(근거 §3 L3 절)
- [x] L3 [SUPERVISOR] 없음 — FE 변경 없음, M2 의무 트리거 미해당
- [x] §1 H-N ↔ S-N 1:N 매핑 완전
- [x] 모든 시나리오에 실행 방식(M1) 명시
- [x] FE 변경 없음 → M2 시나리오 의무 미해당
