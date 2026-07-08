# DONE: 테스트 수행 도구 체계 — FE/BE 2단계(단위·통합) 재정의 + 신규 test-tool

> 완료일: 2026-06-23 | 스킬: //opd (semi-agentic) | 태스크: 039

## 1. 작업 요약

테스트 수행 도구 체계를 **단위 테스트(EXECUTE 단계) / 통합 테스트(TEST 단계) 2단계**로 재정의하고, FE/BE 단계별 도구를 명시적으로 못박았다. 핵심은 산문 지시를 **신규 `test-tool`(결정론적 집행기)**로 대체한 것 — test-tools.yaml을 도구가 읽어(resolve) 단계별 도구를 실행·판정하고, E2E는 cmux-tool 에러코드를 소비해 cmux 1순위→playwright 폴백을 집행한다 (헌법 "Enforce, don't just advise").

## 2. 캡틴 확정 설계 (대화 중 확정)

| # | 결정 | 비고 |
|---|------|------|
| A | 2단계×파이프라인 매핑: 단위=EXECUTE / 통합=TEST | 현행 L계층 흡수 |
| B | FE/BE×2단계 도구 매트릭스 | lint·typecheck·unit / api_db·e2e·supervisor |
| C | E2E 우선순위 = **cmux 1순위 → playwright 폴백** | 캡틴 정정 |
| D | PASS-or-fix 루프 강제 | 한도 SSOT=harness §1 |
| E | 단일 `test-tool` + 4서브명령(resolve/check/unit/integration) | state-tool/cmux-tool 패턴 |
| E-1 | cmux 가용성 = cmux-tool 4-gate 에러코드 소비(직접 재구현 금지) | "대충 체크 금지" |
| E-2 | E2E 실행 = mode A(매 테스트 신규 open→close), 사용자 surface 재사용 금지 | 격리·재현성 |

## 3. 변경 파일 (13개)

### 신규 — `opal/tools/test-tool/`
- `run.sh` — VENV_PYTHON 위임 디스패처 (state-tool 패턴)
- `test_tool.py` — argparse 4서브명령 라우터 + ERROR_CODES 카탈로그 + JSON 출력
- `lib/resolver.py` — test-tools.yaml resolution_order(project→global→추론) 해석. `OPAL_TEST_TOOLS_GLOBAL` env 지원
- `lib/runner.py` — unit 계층 stop-on-fail(lint→build/type→unit, 단발) + check required/optional 게이트
- `lib/e2e_adapter.py` — cmux-tool subprocess 호출→에러코드 소비→폴백/에스컬레이션. 기본 `~/.opal/tools/cmux-tool/run.sh`, `OPAL_CMUX_TOOL_CMD` env 오버라이드. mode A
- `lib/__init__.py`, `README.md`, `tests/test_test_tool.py` (11 RED-first 테스트)

### 수정
- `opal/core/references/test-tools-schema.yaml`, `opal/templates/test-tools.yaml` — v2.0 `tiers`(단위/통합) 구조 + FE/BE 매트릭스 + dtp-* 7줄 현행화
- `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` — 도구 결정 `test-tool resolve` 단일 SSOT(4단계 탐지=내부 폴백) + 2단계 명명 + E2E cmux 1순위(L72/L83/L85)
- `opal/agents/opal-test-agent/AGENT.md` — E2E cmux 1순위 역전 교정 + M2=`test-tool integration` 배선 + 2단계 체계
- `opal/agents/opal-test-agent/personas/test-engineer.md` — FE 접근성=jest-axe·BE 실DB 도구 매핑 + lint=단위(EXECUTE) 위상
- `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` — 3축 명명 매핑 표(L계층/검증깊이/2단계) + 한도 수치 미복제
- `opal/core/references/tools.md`, `opal/core/references/opal-harness.md` §9 — test-tool 등록

## 4. 검증 결과 (All Pass 15/15)

- **test-tool pytest 11/11 PASS** (PM 독립 재현)
- dtp-* grep 0건(R-2 해소), E2E 순서 전역 정합, 3축 매핑·레지스트리 등록 확인
- **S-15 실 cmux 라운드트립** (캡틴 입회): naver→surface:39, localhost:3000(HTTP200)→surface:40, 양쪽 `driver=cmux·status=pass`

### 🐛 S-15가 포착한 진짜 결함 (fix 루프 1회)
- e2e_adapter가 cmux-tool을 PATH 명령 `"cmux-tool"`로 호출 → 항상 `cmux_not_installed` 오분류 → playwright 폴백. **스텁 테스트(S-6~S-8)가 동일 오가정으로 결함을 가림** — 실 cmux 검증(S-15)만이 포착.
- 해결: 테스트 작성자(opal-test-agent)가 `OPAL_CMUX_TOOL_CMD` env 방식으로 RED 교정 → 구현자(opal-be-agent)가 e2e_adapter 호출 경로 교정(기본 `~/.opal/tools/cmux-tool/run.sh`) → 11/11 GREEN → S-15 재검증 driver=cmux.
- **교훈**: 외부 도구 경계는 스텁만으로 불충분 — 실 연동 검증(L3 [SUPERVISOR])이 통합 결함을 잡는다. 캡틴의 "대충 체크 금지" 지시가 적중.

## 5. Known Issue / 잔여

- ⚠️ **배포 미발효**: test-tool 소스(`opal/tools/test-tool/`)만 존재, `~/.opal/`에 미배포. resolve의 글로벌 v2.0 인식도 미발효 → 현재 `OPAL_TEST_TOOLS_GLOBAL` 우회. **install 재배포 필요**(캡틴 직접).
- ruff 경고 2건(비차단, runner.py 등 unused import).
- state-tool 선행 실패 1건(`test_verify_passes_own_test_scenario_md`) — 039 무관(git상 state-tool 무변경).

## 6. 후속 태스크 후보

1. **install 재배포** — test-tool 배포 + test-tools.yaml v2.0 글로벌 발효 (캡틴 직접)
2. **R-6 별건** — `op-dev-execute` Step 3-S의 L2 통합시나리오 TEST 귀속 이동(통합=TEST 완전 배선). 범위 편입 시 PM 에스컬레이션
3. ruff 경고 정리

## 7. 커밋

미커밋 — 캡틴 지시 대기 (커밋 규칙: 명시 요청 시에만).
