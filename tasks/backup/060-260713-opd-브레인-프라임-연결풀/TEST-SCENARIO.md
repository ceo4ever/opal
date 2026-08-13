# TEST SCENARIO: OPAL Console 브레인 프라임 연결 풀 — 지정 프로젝트 선프라임 + 새 대화 웜 핸들 배정

> 작성일: 2026-07-14 | 상태: 작성 완료
> 작성자: 알투(PM) + 캡틴 페어 | PLAN.md 가설 표 기반
> **RED-first 트랙: 적용(강제)** — 변경 영역이 비즈니스 로직(동시성 풀·세션 상태기계)이므로 `harness/red-first.md` §1.5 강제 기준에 해당. RED 테스트 코드 작성은 opal-test-agent(mode: red)가 EXECUTE(GREEN) 진입 전 수행하고, `state-tool verify --red-check`로 RED 증거를 게이트한다.
> **claude CLI 경계 규칙**: 모든 L1/L2 자동 시나리오는 claude CLI 실호출 0회 원칙(`test_brain.py:6` @header H-8 — 구독 소모 금지)에 따라 `prime_and_ask` 경계를 테스트 대역(fixture 계층)으로 격리한다. 실연동(실 claude 프라임·resume)은 S-12(실기동)에서 검증한다 — 헌법 §4 "Don't fake it"은 S-12가 담보.

## 1. 리스크 가설 표

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | F-002 리필 스레드 | 풀 락 보유 중 subprocess 호출 시 후속 체크아웃 전면 블로킹 | P0 | L2 | S-8 |
| H-2 | F-002/F-004 락 계층 | 레지스트리 락 보유 중 세션 락 획득 → 무중첩 불변 위반 교착 | P0 | L2 | S-8 |
| H-3 | F-002 세마포어 | 동시 프라임 상한 미강제 → 구독 사용량 급증 | P1 | L2 | S-4 |
| H-4 | F-001 타입 가드 | `prewarm_projects` 비-list 값 → 하위 순회 런타임 오류 | P1 | L1 | S-1 |
| H-5 | F-004 웜 핸들 stale | 오래된 풀 핸들 resume 실패 → 첫 질의 오류 | P1 | L1 | S-6 |
| H-6 | F-003 lifespan 블로킹 | lifespan 본문 동기 프라임 → 서버 기동 지연 | P1 | L2+L3 | S-9, S-12 |
| H-7 | F-002/F-004 테스트 픽스처 | 풀 상태 미클리어 → 테스트 간 상태 누적 플레이키 | P2 | L2 | S-11 |
| H-8 | 문서 | ARCHITECTURE.md §OPAL Console 풀 개념 미반영 → 문서-구현 불일치 | P2 | L3 | S-13 |

## 2. 테스트 데이터 설계

> DB 없음 — 대상 상태는 전부 인메모리(레지스트리·풀)와 설정 파일이다. "테이블" 열은 인메모리 구조/파일로 대체한다.

### 2.1 사전 조건 데이터

| 테이블(구조/파일) | 식별자 | 상태 | 출처 |
|--------|--------|------|------|
| tmp console.config.json | `prewarm_projects` 키 | 부재/빈배열/문자열/dict/정상배열 5variant | fixture (tmp_path JSON 파일) |
| BrainSessionRegistry._pool | `{project_path: [handle]}` | 시나리오별 0개 또는 1개 적재 | fixture (prewarm 대역 완료 상태) |
| BrainSessionRegistry._sessions | 신규 conversation_id (uuid4) | 미등록(새 대화) | fixture (빈 레지스트리) |
| project_path 디렉토리 | tmp 프로젝트 경로 | 존재하는 디렉토리 | fixture (tmp_path) |
| 실기동: ~/.opal/console.config.json | `prewarm_projects=["/Volumes/Data/AIStudio/workspace/ai-framework"]` | 지정 1건 | 수동 (S-12, 종료 후 원복) |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (CUD/호출) | Then (re-read) |
|---------|------------|----------------|---------------|
| S-1 | config JSON 5variant 파일 | `load_config()` 호출 | `prewarm_projects`가 각각 `[]`/`[]`/`[]`/`[]`/`["p1","p2"]` |
| S-2 | 빈 풀 + prewarm 대역 | `prewarm(p)` → 완료 대기 | `_pool[p]` 길이 1 |
| S-3 | 풀에 핸들 1개 | `checkout_warm_handle(p)` | 반환=핸들, `_pool[p]` 빈 리스트, 리필 스레드 기동됨 |
| S-4 | 프라임 대역에 동시 카운터 삽입 | prewarm N(≥4)건 동시 기동 | 관측 최대 동시 실행 ≤ 2 |
| S-5 | 풀에 핸들 1개 + 미등록 session_id | `submit_job`/`prime` 경유 `_get_or_create` | `status(sid).state == "ready"`, 첫 ask 인자 `cold=False`(resume) |
| S-6 | 웜 주입 세션 + resume 실패 대역(RuntimeError) | `ask(question)` | 투명 재프라임(cold=True 재호출)으로 answer 정상 반환 |
| S-7 | 빈 풀 + 미등록 session_id | `_get_or_create` 후 `ask` | state idle 유지 → 첫 ask `cold=True` (기존 콜드 동작 동일) |
| S-8 | 리필 진행 중(프라임 대역이 이벤트 대기로 지연) | 지연 중 `checkout_warm_handle`·`_get_or_create` 호출 | 즉시 반환(블로킹 없음)·타임아웃 내 완료(교착 없음) |
| S-9 | prewarm_projects 대역 설정(2건/0건) | `with TestClient(app):` 진입 | 2건: prewarm 프로젝트당 1회 호출·즉시 기동 / 0건: 0회 호출 |
| S-10 | 기존 test_brain.py 전체 + 신규 케이스 | `pytest dashboard/backend/tests/` 실행 | 기존 15클래스 포함 전체 GREEN (API 계약 회귀 0) |
| S-11 | 풀에 상태 잔류시킨 직전 테스트 | 다음 테스트에서 픽스처 초기화 확인 | `_pool`·`_pool_inflight` 빈 상태 |
| S-12 | 실기동: config에 본 프로젝트 지정 | 데몬 재기동 → 로그 확인 → 새 대화 첫 질의(API) | 선프라임 로그 + `ask WARM 경로` + elapsed 웜 수준, 대조군(빈 배열)은 COLD 경로 |
| S-13 | ARCHITECTURE.md §OPAL Console | Step 6 문서 갱신 후 리뷰 | 세션 행에 풀·prewarm_projects 기술 존재 |

## 3. 검증 시나리오

> 도구 결정: `test-tool resolve --stack py` → unit=pytest / lint=ruff / typecheck=mypy (source: global).
> 테스트 파일 배치: 모듈 미러링 — `dashboard/backend/tests/test_brain.py`(기존 파일에 케이스 추가), config는 `dashboard/backend/tests/test_config.py`(부재 시 신규 1파일). 케이스명 프리픽스 `[T060/L{계층}-{AC}]`.

### L1. 기능 단위 (자동, 실 데이터 입력)

#### S-1: config prewarm_projects 파싱·타입 가드

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | `config.load_config()` — `prewarm_projects` 5variant 파싱 (F-1 AC) |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | tmp_path에 JSON 5variant(키 부재/빈 배열/문자열/dict/정상 2경로+비str 원소 혼합) 생성, `CONFIG_PATH` 경계를 tmp로 격리 |
| 기대 결과 | 부재·빈·비-list → `[]`, 정상 배열 → str 원소만 로드. 예외 0건 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest dashboard/backend/tests/test_config.py -q` |
| 결과 | Pass |
| 상세 | 5 passed in 0.02s — 5variant(부재/빈배열/문자열/dict/정상배열) 전건 타입 가드 정상, 예외 0건 |

#### S-2: 풀 선프라임 적재

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1(정상 경로 전제) |
| 대상 | `BrainSessionRegistry.prewarm()`/`_prime_into_pool()` — 풀 적재 (F-2 AC(a)) |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | 빈 풀, `prime_and_ask` 경계 대역(session_id 반환). 스레드 join으로 완료 대기 |
| 기대 결과 | `_pool[project]` 길이 1, `_pool_inflight[project]` 0 복귀. pool_size 충족 상태에서 재호출 시 추가 프라임 0회(과잉 방지) |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest dashboard/backend/tests/test_brain.py::TestBrainPrimePool::test_prewarm_loads_pool_then_avoids_overfill -q` |
| 결과 | Pass |
| 상세 | 1 passed in 0.35s — `_pool[project]` 길이 1 적재 확인, pool_size 충족 상태 재호출 시 추가 프라임 0회(과잉 방지) 확인 |

#### S-3: 체크아웃 pop + 리필 트리거

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | `checkout_warm_handle()` — pop·리필 (F-2 AC(a)) |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | 풀에 핸들 1개 적재 상태 |
| 기대 결과 | 핸들 반환 + 풀 비워짐 + 리필(prewarm) 트리거 관측. 빈 풀 재호출 시 None |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest dashboard/backend/tests/test_brain.py::TestBrainPrimePool::test_checkout_pops_handle_and_triggers_refill dashboard/backend/tests/test_brain.py::TestBrainPrimePool::test_checkout_empty_pool_returns_none -q` |
| 결과 | Pass |
| 상세 | 2 passed in 0.19s — 핸들 반환+풀 비워짐+리필 트리거 관측, 빈 풀 재호출 시 None 확인 |

#### S-5: 새 대화 웜 주입 → ready + resume 경로

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5(정상 경로 전제) |
| 대상 | `_get_or_create()` 웜 주입 + `adopt_warm_handle()` + 첫 `ask()` resume (F-4 AC(a)) |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | 풀에 핸들 1개, 미등록 session_id로 prime/submit_job 진입 |
| 기대 결과 | 콜드 프라임 0회로 `status().state == "ready"`. 첫 ask의 `prime_and_ask` 호출 인자 `cold=False`·`session_id=주입 핸들` |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest dashboard/backend/tests/test_brain.py::TestBrainWarmInjection::test_new_session_ready_without_cold_prime dashboard/backend/tests/test_brain.py::TestBrainWarmInjection::test_new_session_first_ask_uses_resume_with_warm_handle -q` |
| 결과 | Pass |
| 상세 | 2 passed in 0.22s — 콜드 프라임 0회로 state=ready 확인, 첫 ask 호출 인자 cold=False·session_id=주입 핸들 확인 |

#### S-6: stale 웜 핸들 resume 실패 → 투명 재프라임

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | 웜 주입 세션의 `_warm_ask` 실패 → 기존 ⓓ 콜드 재시도 흡수 (F-4 AC(a)) |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | 웜 주입 세션, resume 호출 대역이 RuntimeError 1회 후 콜드 성공 |
| 기대 결과 | 호출자에 answer 정상 반환(투명), 세션에 새 콜드 핸들 커밋 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest dashboard/backend/tests/test_brain.py::TestBrainWarmInjection::test_warm_injected_resume_failure_transparent_reprime -q` |
| 결과 | Pass |
| 상세 | 1 passed in 0.19s — resume RuntimeError 후 투명 재프라임으로 answer 정상 반환, 세션에 새 콜드 핸들 커밋 확인 |

#### S-7: 풀 empty 콜드 폴백 (회귀)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1(폴백 경로) |
| 대상 | 빈 풀에서 새 대화 → 기존 콜드 경로 동일 (F-4 AC(b)) |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | 빈 풀 + 미등록 session_id |
| 기대 결과 | `_get_or_create` 후 state idle, 첫 ask `cold=True` — 기존 동작과 동일(회귀 0) |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest dashboard/backend/tests/test_brain.py::TestBrainWarmInjection::test_empty_pool_new_session_cold_fallback -q` |
| 결과 | Pass |
| 상세 | 1 passed in 0.22s — 빈 풀 새 대화 시 state=idle 유지, 첫 ask cold=True(기존 콜드 동작 동일) 확인 — 회귀 0 |

### L2. 프로세스 통합 (자동, 동시성·기동 흐름)

#### S-4: 동시 프라임 상한(Semaphore) 강제

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | `_prime_semaphore` — 동시 프라임 ≤ 2 (F-2 AC(c)) |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + threading)** |
| 조건 | 프라임 경계 대역에 동시 실행 카운터+이벤트 지연 삽입, 서로 다른 프로젝트 4건 prewarm 동시 기동 |
| 기대 결과 | 관측된 최대 동시 실행 수 ≤ 2, 전 건 최종 완료 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest dashboard/backend/tests/test_brain.py::TestBrainPrimePool::test_prewarm_concurrent_limit_enforced -q` |
| 결과 | Pass |
| 상세 | 1 passed in 0.51s — 서로 다른 프로젝트 4건 동시 prewarm 기동, 관측 최대 동시 실행 ≤ 2 확인, 전 건 최종 완료 |

#### S-8: 락 무중첩 — 리필 중 비블로킹·동시 체크아웃 무중복

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1, H-2 |
| 대상 | 리필 subprocess 구간 락 미보유 + 체크아웃 직렬화 (F-2 AC(b)) |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + threading)** |
| 조건 | ① 프라임 대역이 이벤트 대기로 지연되는 동안 `checkout_warm_handle`·`_get_or_create` 호출 ② 풀 핸들 1개에 동시 체크아웃 2건 |
| 기대 결과 | ① 지연 중 호출이 즉시 반환(타임아웃 1s 내), 교착 0 ② 같은 핸들 중복 배정 0건(하나는 핸들, 하나는 None) |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest dashboard/backend/tests/test_brain.py::TestBrainPrimePool::test_checkout_non_blocking_during_refill dashboard/backend/tests/test_brain.py::TestBrainPrimePool::test_concurrent_checkout_no_duplicate_handle -q` |
| 결과 | Pass |
| 상세 | 2 passed in 0.19s — 리필 지연 중 checkout/_get_or_create 즉시 반환(교착 0) 확인, 동시 체크아웃 2건 시 핸들 중복 배정 0건(하나 핸들·하나 None) 확인 |

#### S-9: lifespan 기동 선프라임 — 트리거·비블로킹·0회

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | `main.lifespan` — prewarm_projects 순회 (F-3 AC) |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + TestClient lifespan)** |
| 조건 | `load_config` 경계 대역으로 prewarm_projects 2건/0건 주입, `with TestClient(app) as client:` 진입 |
| 기대 결과 | 2건: 프로젝트당 prewarm 1회 + 진입 즉시 완료(프라임 완료 대기 없음) / 0건: prewarm 0회 + `/health` 200 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest dashboard/backend/tests/test_brain.py::TestBrainLifespanPrewarm -q` |
| 결과 | Pass |
| 상세 | 3 passed in 0.25s — 2건: 프로젝트당 prewarm 1회 호출·진입 즉시 완료(비블로킹) 확인 / 0건: prewarm 0회·/health 200 확인 |

#### S-10: 브레인 API 계약·기존 스위트 회귀

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2(간접 — 무변경 검증), F-4 AC(c) |
| 대상 | `routers/brain.py` 무변경 — API 5종 요청/응답 스키마 불변 + 기존 테스트 전체 |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest 전체 스위트)** |
| 조건 | 신규 코드 반영 상태에서 `dashboard/backend/tests/` 전체 실행 |
| 기대 결과 | 기존 15개 클래스 포함 전체 GREEN — 실패 0·에러 0 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest dashboard/backend/tests/ -q` |
| 결과 | Pass |
| 상세 | 235 passed, 1 skipped in 13.37s — 실패 0·에러 0. skip 1건은 `test_adapters.py:88`(실 태스크 디렉토리 없음) — 환경 의존 사전 존재 skip, 본 변경과 무관 |

> **BE API M2(Swagger) 면제 판단**: 이번 변경은 API 엔드포인트 신설·수정 0건(라우터 무변경 — PLAN §3.4.2)이므로 `test-scenario-guide.md` §Step 3-b BE API M2 의무 트리거 비해당. API 계약 불변은 S-10(전체 스위트)과 S-12(실기동)로 검증한다. FE 화면·인증/인가·외부 API 연동 변경도 0건 — M2 의무 트리거 비해당.

#### S-11: 픽스처 확장 — 풀 상태 오염 방지 (회귀)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | `reset_brain_registry` autouse 픽스처 확장 (`_pool`·`_pool_inflight` 클리어) |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | 풀에 상태를 남기는 테스트 직후 후속 테스트에서 풀 상태 검사 |
| 기대 결과 | 후속 테스트 시작 시 풀·inflight 빈 상태 — 실행 순서 무관 안정 통과 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest dashboard/backend/tests/test_brain.py::TestBrainPoolFixtureRegression -q` |
| 결과 | Pass |
| 상세 | 2 passed in 0.18s — 풀 상태 잔류시킨 직전 테스트 이후 후속 테스트에서 `_pool`·`_pool_inflight` 빈 상태 확인, 실행 순서 무관 안정 통과 |

### L3. 사용자 협업 (수동, [SUPERVISOR] 마커)

#### S-12: 실기동 검증 — 선프라임→새 대화 웜 배정 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 (+ F-5 AC — 실연동 검증) |
| 대상 | 실제 데몬 기동 → 선프라임 로그 → 새 대화 첫 질의 elapsed |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업 — 승인 게이트) + M2 병기 (승인 후 opal-test-agent가 PLAN §3.5.2 절차를 자동 수행)** |
| 조건 | `~/.opal/console.config.json` prewarm_projects에 본 프로젝트 지정 → 데몬 재기동. **주의: 실 claude 구독 호출 2~3회 소모 + 실행 중 콘솔 데몬 재기동 발생** |
| 기대 결과 | ① 선프라임 로그(`prewarm 완료 ... pool=1`) ② 새 대화 첫 질의 `ask WARM 경로` + elapsed 웜 수준(콜드 ~56s 대비 유의미 단축) ③ 대조군(빈 배열) 재기동 시 선프라임 0건 + `ask COLD 경로` ④ 종료 후 config 원복 |
| 실행자 | [SUPERVISOR] — 캡틴 승인 후 opal-test-agent 자동 수행 (구독 소모·데몬 재기동 승인 필요) |
| 결과 | Pass |
| 상세 | 프로젝트 소스(`--app-dir` ai-framework, `~/.opal/dashboard-server` 미사용)로 uvicorn 기동. ① 선프라임: `[brain] 기동 선프라임 대상 1개` 로그 확인 → 40s 후 `[brain] prewarm 완료 project=.../ai-framework pool=1` 확인(prime 자체 elapsed=37.1s, 구독 호출 1/3). ② 웜 배정: 새 uuid 첫 질의 → 로그 `[brain] ask WARM 경로 conv=b6ef2f02 (resume, 최대 60s)` + `job 완료 ... elapsed=9.6s`(구독 호출 2/3). ③ 대조군: config `prewarm_projects=[]`로 재기동 → 선프라임 로그 0건(`prewarm_projects 미지정 — 선프라임 생략`만 출력) 확인 → 새 uuid 질의 → 로그 `[brain] ask COLD 경로 conv=d86e70cc (콜드 프라임...)` + `job 완료 ... elapsed=26.7s`(구독 호출 3/3, 예산 3회 준수). 웜(9.6s) vs 콜드(26.7s) — 약 2.8배 단축, 유의미한 차이 확인. ④ 종료 후 `~/.opal/console.config.json` 원복(백업본 mv로 원본과 바이트 동일 복원) + 테스트 uvicorn 종료 + `opal-cli console start`로 원 배포 데몬(PID 재기동, `~/.opal/dashboard-server` 기준) 정상 복귀·`/health` 200 확인. Pass 기준 ①②③ 전건 충족. |

**PM 표준 요청 양식** (TEST 단계에서 사용):
```
캡틴, [시나리오 S-12]는 사용자 협업 검증이 필요합니다.
요청 내용: 실기동 검증 — console.config.json에 본 프로젝트를 prewarm 지정 후 데몬 재기동, 새 대화 첫 질의 1회 (claude 구독 호출 2~3회 소모 + 콘솔 데몬 재기동 수반)
기대 결과: 선프라임 완료 로그 + 새 대화 첫 질의가 웜(resume) 경로로 콜드 대비 유의미 단축
승인해주시면 opal-test-agent가 자동 수행하고 결과를 기록합니다.
```

#### S-13: ARCHITECTURE.md 문서 동기화 리뷰 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 대상 | `docs/ARCHITECTURE.md §OPAL Console` 세션 행 — 풀 구조·prewarm_projects 반영 여부 |
| 계층 | L3 |
| **실행 방식** | **M3 (문서 리뷰 — PM 갱신 후 캡틴 확인)** |
| 조건 | Step 6(PM 직접) 갱신 완료 상태 |
| 기대 결과 | 세션 행에 선프라임 풀·웜 배정·리필·동시 상한·config 키가 정확히 기술됨 |
| 실행자 | [SUPERVISOR] — CLOSE 보고 시 캡틴 확인 |
| 결과 | _{캡틴 확인 후 기록}_ |
| 상세 | _{캡틴 확인 후 기록}_ |

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| F-1 AC | H-4 | L1 | S-1 | `dashboard/backend/tests/test_config.py`:`[T060/L1-F1]` (신규 1파일) | 5variant 파싱 |
| F-2 AC (a) | H-1 | L1 | S-2, S-3 | `dashboard/backend/tests/test_brain.py`:`[T060/L1-F2a]` | 적재·pop·리필 |
| F-2 AC (b) | H-1, H-2 | L2 | S-8 | `test_brain.py`:`[T060/L2-F2b]` | 중복 배정 0·무교착 |
| F-2 AC (c) | H-3 | L2 | S-4 | `test_brain.py`:`[T060/L2-F2c]` | 동시 프라임 ≤ 2 |
| F-3 AC | H-6 | L2 | S-9 | `test_brain.py`:`[T060/L2-F3]` | lifespan 트리거·비블로킹 |
| F-4 AC (a) | H-5 | L1 | S-5, S-6 | `test_brain.py`:`[T060/L1-F4a]` | ready·resume·stale 흡수 |
| F-4 AC (b) | H-1 | L1 | S-7 | `test_brain.py`:`[T060/L1-F4b]` | 콜드 폴백 회귀 |
| F-4 AC (c) | H-2 | L2 | S-10 | `test_brain.py` 전체 + 기존 스위트 | 계약 불변·회귀 0 |
| (픽스처 회귀) | H-7 | L2 | S-11 | `test_brain.py`:`[T060/L2-H7]` | 상태 오염 방지 |
| F-5 AC | H-6 | L3 | S-12 | (실기동 — PLAN §3.5.2 절차) | [SUPERVISOR] 구독 소모 승인 |
| (문서) | H-8 | L3 | S-13 | (문서 리뷰) | [SUPERVISOR] CLOSE 확인 |

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | ruff (v0.15.17) | Pass(신규 위반 0) | `ruff check` changed_files 대상 3건 발견(config.py F401 `import os` 미사용, test_brain.py F841 `mock_run` 미사용, test_brain.py F541 f-string placeholder 없음) — 전건 baseline(변경 전 커밋) 대조 결과 T060 변경 이전부터 존재하던 기존 부채로 확인. 본 태스크가 신규로 유발한 린트 위반 0건 |
| 2 | 타입 체크 | mypy | 미설치(게이트 불가) | `mypy --version` → command not found. 프로젝트에 mypy 미설치 확인(`which mypy` 실패) — 타입 체크 게이트 수행 불가로 기록만 함 |
| 3 | 포맷터 | (프로젝트 미지정 — ruff format 확인) | 정보성(게이트 아님) | `ruff format --diff` 시 changed_files 5건 전부 리포맷 대상(주석 정렬 스타일 등) — baseline(변경 전 커밋)도 동일 4개 파일이 리포맷 대상으로 확인되어 프로젝트가 ruff format을 강제하지 않는 기존 상태. 본 태스크로 인한 신규 포맷 이슈 없음 |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | Pass | `grep -rniE "api[_-]?key\|secret\|token\s*=" config.py brain_session.py main.py test_brain.py test_config.py` → 매치 0건(exit 1) — 하드코딩 시크릿 없음 |
| 2 | .gitignore 확인 | Pass | `.env`, `venv/`, `.venv/`, `.opal/*`(단 `.opal/brain/` 예외) 등 민감/캐시 경로 이미 등재 확인. changed_files는 소스코드로 gitignore 대상 아님(정상) |
| 3 | API 키·SDK 미사용 (구독 claude -p만) | Pass(신규 위반 0) | `grep -rn "anthropic\|--safe-mode\|--bare\|ANTHROPIC_API_KEY" adapters/ main.py config.py` → 매치는 `opbr_adapter.py:6,23` 뿐이며 이는 코드가 아닌 **금지 규칙을 명시한 [MUST] 주석/헤더 문구**(실제 사용 아님). changed_files(brain_session.py·main.py·config.py)에는 매치 0건 — 신규 anthropic SDK·API 키·--safe-mode/--bare 사용 0건 확인 |

## 7. 판정

**L1/L2 All Pass (L3 [SUPERVISOR] 2건 대기) — S-1~S-11 전 시나리오 Pass(11/11), 코드 품질(ruff 신규 위반 0·mypy 미설치 게이트 불가·포맷터 신규 이슈 0), 보안(하드코딩 시크릿 0·gitignore 정상·anthropic SDK/API키/--safe-mode/--bare 신규 사용 0), 회귀(전체 스위트 235 passed·1 skipped(환경 의존 사전 skip, 무관)·0 failed) 전건 충족. S-12(실기동, claude 구독 호출 수반)·S-13(문서 리뷰)은 캡틴 승인/확인 대기 중으로 본 판정 범위(L1/L2)에서 제외.**

### PM Gate 체크 (7대 강제 룰)

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 (경계 격리는 "경계 대역"으로 기술 — 실연동은 S-12가 담보, 상단 claude CLI 경계 규칙 참조)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전 (미매핑 시나리오 없음)
- [x] L1/L2/L3 계층 명시 (모든 시나리오)
- [x] L3 [SUPERVISOR] 마커 존재 + PM 요청 양식 첨부 (S-12)
- [x] 리스크 가설 표(§1) H-N ↔ S-N 매핑 완전 (H-1~H-8 전건)
- [x] 모든 시나리오에 실행 방식(M1/M2/M3) 명시
- [x] FE 변경 시 M2 시나리오 포함 — **비해당** (FE·인증/인가·외부 API·엔드포인트 변경 0건, §3 S-10 아래 면제 판단 기재)
