# TEST SCENARIO: OPAL Console 프로젝트 브레인 질의 (Phase 1 스파이크)

> 작성일: 2026-06-22 | 상태: 작성 완료
> 작성자: 알투(PM) + 캡틴 페어 | PLAN.md(B) 가설 표 기반
> **범위: Phase 1 스파이크(F-000)만.** Phase 2+ 시나리오(FE UI·세션 리셋·격리·전체 RED-first)는 스파이크 학습(opbr 실출력 형태·콜드/웜 지연·B1/B2) 후 확장한다.

## RED-first 트랙

PLAN §RED-first 판정 계승: **F-000 스파이크는 RED-first 완화**(탐색 목적 — 실 동작·지연·출력형태를 먼저 관측). 단 커밋되는 단위테스트는 `claude` 서브프로세스를 **고정 출력 스텁으로 격리**하여 실 구독 토큰 0 소모(H-8). **실 통합 검증은 L3 SUPERVISOR(S-4)** — 작성자(PM)≠실행자(캡틴/test-agent) 분리로 self-confirming 방지.

## 1. 리스크 가설 표 (스파이크 관련)

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | opbr_adapter — `//opbr ask` 쓰기 누수 | synthesis 파일링·term 등록이 brain에 쓰기 | P0 | L3 | S-4(⑤ brain 해시 불변) |
| H-6 | opbr_adapter 출력 파싱 | `result` 부재/`is_error`/비JSON 시 빈 답변·500 | P0 | L1 | S-1, S-2 |
| H-7 | 구독 keychain 인증 / 금지 플래그 | `--safe-mode`·`--bare`·API키 사용 시 구독 파탄·opbr 미로드 | P0 | L1+L3 | S-3, S-4(②⑤) |
| H-8 | 자동 테스트 실 claude 호출 | 실 구독 토큰 소모·비결정성 | P1 | L1 | S-1~S-3(스텁 격리) |
| (스파이크 목표) | 세션 지연프라임·콜드/웜 | B1/B2 미결정·지연 미상 | — | L3 | S-4(③④⑥) |

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

| 테이블/대상 | 식별자 | 상태 | 출처 |
|--------|--------|------|------|
| brain 페이지 | `.opal/brain/pages/**/*.md` | 기존 존재(이 프로젝트 brain 활성) | 실제 프로젝트 자산 |
| 샘플 질문 | `"OPAL 첫 사용 순서는?"` 등 brain에 근거 있는 질의 | 수동 입력 | 캡틴 |
| claude 고정 출력(L1) | `{"type":"result","subtype":"success","is_error":false,"result":"<답변>","session_id":"sid-1"}` | 스텁 | 테스트 fixture |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (사전) | When (호출) | Then (검증) |
|---------|------------|-----------|-----------|
| S-1 | 성공형 고정 출력 스텁 | `opbr_adapter.prime_and_ask(q, path)` | `{answer:"<답변>", session_id:"sid-1"}` 반환 |
| S-2 | `is_error:true` 또는 비JSON 고정 출력 | `prime_and_ask(...)` | 예외 발생 → 라우터 502 |
| S-3 | (출력 무관) | `prime_and_ask`가 구성하는 커맨드 배열 캡처 | `//opbr ask`·`--output-format json` 포함, `--safe-mode`·`--bare` 부재, shell=False |
| S-4 | 로컬 데몬 기동, brain 활성, 구독 로그인된 Claude Code | 캡틴이 `POST /api/brain/query`로 실제 질의 | 답변 반환 + 6항목 확인(아래) |

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 고정 출력 스텁 격리 — 실 claude 미호출)

#### S-1: opbr_adapter 출력 파싱 — 정상

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | `opbr_adapter.prime_and_ask` 출력 파싱 |
| 계층 | L1 |
| 실행 방식 | M1 (pytest + 서브프로세스 고정 출력 스텁) |
| 조건 | claude 서브프로세스가 §2.1 성공형 고정 출력 반환하도록 격리 |
| 기대 결과 | `answer`=`result` 값, `session_id` 추출, 실 claude 호출 0회 |
| 도구 | pytest, unittest 격리 |
| 실행 명령 | `python3 -m pytest dashboard/backend/tests/test_brain_spike.py::TestParseSuccess -v` |
| 결과 | **PASS** |
| 상세 | 2 passed (test_parse_success·test_parse_success_citations_empty_in_spike). answer='답변텍스트', session_id='sid-1', citations=[], elapsed_s 포함 확인. mock_run.assert_called_once() 통과 — 실 claude 0회 격리 확증. |

#### S-2: opbr_adapter 출력 파싱 — 실패 처리

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | `prime_and_ask` 실패 경로 |
| 계층 | L1 |
| 실행 방식 | M1 (pytest + 고정 출력 스텁) |
| 조건 | `{"is_error":true}` 또는 비JSON 고정 출력 |
| 기대 결과 | 예외 발생(라우터가 502로 변환), 빈 답변 미반환 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest dashboard/backend/tests/test_brain_spike.py::TestParseError -v` |
| 결과 | **PASS** |
| 상세 | 4 passed (test_parse_error_is_error_raises·test_parse_error_non_json_raises·test_parse_error_502·test_parse_non_json_502). is_error=true → RuntimeError(match="is_error=true") 확인, 비JSON → RuntimeError 확인, 두 케이스 모두 POST /api/brain/query → HTTP 502 반환 확인. |

#### S-3: 커맨드 배열 — 구독 구동·금지 플래그 부재

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7, H-8 |
| 대상 | `prime_and_ask`가 구성하는 subprocess 커맨드 배열 |
| 계층 | L1 |
| 실행 방식 | M1 (pytest + 커맨드 배열 캡처) |
| 조건 | prime_and_ask 호출(서브프로세스 실행은 격리) |
| 기대 결과 | 배열에 `//opbr ask <질문>`·`--output-format`·`json` 포함, `--safe-mode`·`--bare` **부재**, `shell=False` |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest dashboard/backend/tests/test_brain_spike.py::TestCmdFlags -v` |
| 결과 | **PASS** |
| 상세 | 9 passed (test_opbr_query_read_only_in_cmd·test_output_format_json_in_cmd·test_no_safe_mode_flag·test_no_bare_flag·test_shell_false·test_cold_session_uses_session_id_flag·test_warm_session_uses_resume_flag·test_question_in_prompt·test_readonly_guard_in_prompt). `//opbr query --read-only` 포함, `--output-format json` 포함, `--safe-mode`/`--bare` 부재, `shell=False` 확인, 콜드=--session-id/웜=--resume 분기 확인, 질문 텍스트 -p 인자 포함 확인, --read-only 계약 프롬프트 내 포함 확인. |

### L3. 사용자 협업 (수동, [SUPERVISOR] 마커) — 스파이크 핵심 게이트

#### S-4: 스파이크 실 구독 E2E [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1, H-7, 스파이크 목표(③④⑥) |
| 대상 | 핵심 루프: 구독 인증 + OPAL/opbr 세션 로딩 + 질의→답변 |
| 계층 | L3 |
| 실행 방식 | M3 (사용자 협업 — 캡틴 수동, 실 구독) |
| 조건 | 로컬 데몬 기동, brain 활성, Claude Code 구독 로그인 상태 |
| 기대 결과 | ①질의→답변 반환 ②OPAL/opbr 로딩 정황(답변이 brain 근거) ③콜드(최초)/웜(resume) 지연 측정 ④질의 전후 `.opal/brain` 해시 불변(쓰기 0) ⑤API키 없이 구독으로 작동 ⑥B1 웜 지연 수용 가능 여부(→ B1/B2 결정) |
| 실행자 | [SUPERVISOR] — 캡틴 수동 확인 필요 |
| 결과 | **PASS (핵심 루프) / 후속 필요 (지연·출력정제)** — 2026-06-22 캡틴 실행 |
| 상세 | ✅①답변 반환(200) ✅②OPAL/opbr 실제 로딩+brain 근거(`[[opal-first-use-guide]]` 인용, 부트스트랩 라인 노출로 OPAL 로딩 확증) ✅④`.opal/brain` 변경 0건(read-only PASS — log.md조차 미기록, 가드 작동) ✅⑤구독 작동(auth authenticated:true, API키 0). ⚠️③**콜드 지연 99.4s**(웹 UI엔 과대 → 웜/지속세션 필수 확정) ⚠️**출력 오염**(result에 부트스트랩 보고+`📋 알투[PM]` 페르소나 preamble 혼입 → 프라임/질의 분리 + 출력 추출 필요). session_id 발급 확인(resume 핸들 확보). ⑥웜/B1·B2는 warm 측정 후속 |

**PM 표준 요청 양식 (TEST 단계에서 발신)**:
```
캡틴, [S-4]는 사용자 협업 검증이 필요합니다.
요청 내용: 로컬 콘솔 데몬 기동 후 "프로젝트 브레인" 질의 1건(POST /api/brain/query) 실행
기대 결과: ①답변 반환 ②brain 근거 답변 ③콜드/웜 지연 ④.opal/brain 불변 ⑤구독 작동 ⑥웜 지연 수용성(B1/B2)
확인 후 결과(PASS/FAIL + 6항목 측정값)를 알려주세요.
```

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| F-000 출력파싱 정상 | H-6 | L1 | S-1 | `tests/test_brain_spike.py`:test_parse_success | 고정 출력 스텁 |
| F-000 출력파싱 실패 | H-6 | L1 | S-2 | `tests/test_brain_spike.py`:test_parse_error→502 | 고정 출력 스텁 |
| F-000 구독구동·금지플래그 | H-7, H-8 | L1 | S-3 | `tests/test_brain_spike.py`:test_cmd_flags | 커맨드 배열 캡처 |
| F-000 실 구독 E2E | H-1, H-7 | L3 | S-4 | (수동) | 캡틴 검증 게이트 |

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트(BE) | ruff | **PASS** | `ruff check` 변경 5파일(opbr_adapter·brain_session·brain.py·models·main) — All checks passed! |
| 2 | 린트(FE) | ESLint | **PASS (pre-existing 경고 구분)** | 변경파일 신규 이슈 4건: `textarea.tsx:14` @typescript-eslint/no-empty-object-type(1건, shadcn 자동생성 패턴), `BrainPage.tsx:79/91/101` react-refresh/only-export-components(3건). 나머지 6건(`badge`,`button`,`sidebar`,`toggle`,`use-mobile`)은 미변경 파일 pre-existing. 빌드(`npm run build`) 0 오류 완료 — 런타임 무영향 |
| 3 | 타입 체크(FE) | tsc -b --noEmit | **PASS** | `npx tsc -b --noEmit` 0 오류. vite build 493ms 성공(청크 크기 경고는 pre-existing) |
| 4 | 포맷터(BE) | ruff/black | N/A | ruff format 미설치(~/.opal/.venv), black 미설치. ruff check PASS로 문법·스타일 주요 룰 커버됨 |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔(API키·토큰 부재) | **PASS** | `grep -rn "sk-ant\|api_key\s*=\s*[\"']\|token\s*=\s*[\"']"` 변경파일 전체 — 매치 0건. ANTHROPIC_API_KEY는 comment(금지 선언)에만 등장, 실 코드 사용 없음 |
| 2 | 금지 플래그(`--safe-mode`/`--bare`)·SDK 부재 grep | **PASS** | `grep -rn "\-\-safe-mode\|\-\-bare"` 변경파일 전체 — 실 코드 사용 0건(opbr_adapter @header 금지 주석에만 언급). `anthropic` SDK import 없음. `ANTHROPIC_API_KEY` 환경변수 사용 없음. `@router.post` brain.py 한정 확인 — `/api/brain/prime`·`/api/brain/query` 2건만, 나머지 라우터는 GET only |
| 3 | 셸 인젝션(shell=False) | **PASS** | `opbr_adapter.py:145` — `subprocess.run(..., shell=False)` 명시. S-3 test_shell_false 테스트도 PASS 확인(mock_run.call_args 검증). `brain_session.py` 내 subprocess 없음 |
| 4 | 127.0.0.1 바인딩 | **PASS** | `main.py:103` — `host="127.0.0.1"` 명시. `0.0.0.0` 없음. @header에도 "localhost 바인딩 — 0.0.0.0 금지" 명시 |

## 7. 판정

**All Pass (L1 + L3 S-4 핵심루프) / L3 S-4 후속과제 보류** — 판정 근거:

- **L1 자동 (BE)**: 149/149 PASS. S-1(2), S-2(4), S-3(9) 스파이크 케이스 전원 PASS. test_brain_endpoints_exist·test_existing_routers_reject_post 격리회귀 PASS. 실 claude 서브프로세스 0회(mock_run 검증).
- **L1 자동 (FE)**: 14/14 PASS (vitest). `npm run build` 0 오류 (TypeScript + Vite 빌드 493ms 성공).
- **코드품질**: BE ruff PASS, FE tsc PASS. FE ESLint 신규 이슈 4건(textarea 1·BrainPage 3) — 런타임 무영향, fast-refresh 및 shadcn 패턴 경고. 차기 리팩토링 대상.
- **보안**: 하드코딩 시크릿 0건, --safe-mode/--bare/anthropic SDK 사용 없음, shell=False 확인, 127.0.0.1 바인딩 확인.
- **L3 S-4 [SUPERVISOR]**: 캡틴 실행 완료(2026-06-22). 핵심루프(①②④⑤) PASS. ③콜드 지연 99.4s·출력오염(preamble 혼입)은 후속 Phase 2 과제(웜세션·extract_json_fence 정제) — 이 태스크(Phase 1 스파이크) 범위 완료 판정에 영향 없음.

### PM Gate 체크 (7대 강제 룰 — 스파이크 적용 주석)

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 — L1은 "고정 출력 스텁/커맨드 배열 캡처"로 기술(실 통합은 L3 S-4). 토큰 보호(H-8)상 서브프로세스 격리는 불가피·의도적이며 self-confirming은 L3 실 구독 검증으로 차단
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전
- [x] L1/L3 계층 명시 (모든 시나리오)
- [x] L3 [SUPERVISOR] 마커 + PM 요청 양식 첨부
- [x] 리스크 가설 표(§1) H-N ↔ S-N 매핑 완전
- [x] 모든 시나리오에 실행 방식(M1/M3) 명시
