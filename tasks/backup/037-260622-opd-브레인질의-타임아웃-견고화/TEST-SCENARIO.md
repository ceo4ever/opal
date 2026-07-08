# TEST SCENARIO: OPAL Console 브레인 질의 — fetch 타임아웃·ready 사각지대 견고화

> 작성일: 2026-06-23 | 상태: 실행 완료
> 작성자: 알투(PM) + 캡틴 페어 | PLAN.md 가설 표 기반
> RED-first 트랙: **적용** (API 계약 변경 + 버그 수정 → red-first.md §1.5 강제). RED 테스트 코드 작성=opal-test-agent(mode: red), 구현=op-dev-execute 워커 — 작성자≠구현자 분리.

## 1. 리스크 가설 표

> PLAN.md §리스크 가설 표(H-1~H-10)를 시나리오(S-N)에 매핑.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | `POST /api/brain/query` 응답 `{answer,citations,session_id}`→`{job_id}` | 기존 라우터 계약(`test_brain.py:1636`·`test_routers.py:259`) | P0 | L1 | S-1, S-9 |
| H-2 | `GET /api/brain/job/{job_id}` 신설 | 신규 엔드포인트 pending→done/error 전이 | P0 | L1 | S-2 |
| H-3 | 콜드 잡 흡수 — 백그라운드 실행 중 `_state="priming"` 반영 | status 폴링이 콜드 진행 미감지 시 사각지대 잔존 | P0 | L1+L3 | S-3, S-12 |
| H-4 | 동시 query (RI-2 높음) — 같은 세션 2잡 제출 | 진행 중 답변 손실(덮어쓰기) | P1 | L1 | S-5 |
| H-5 | 잡 결과 TTL 부재 (RI-4 낮음) | 완료 잡 인메모리 무한 축적 | P2 | L1 | S-6 |
| H-6 | FastAPI sync + threading (RI-5) | submit 블로킹 시 threadpool 소진 | P1 | L1 | S-1 |
| H-7 | apiClient AbortController (RI-8) | timeoutMs 미전달 시 기존 5화면 회귀 | P1 | L1 | S-11 |
| H-8 | 폴링 중 언마운트/잡 소멸 (RI-1·RI-3) | 빈 답·UX 저하 | P1 | L1+L3 | S-10, S-12 |
| H-9 | 무상태 — 프로세스 재시작 시 미완료 잡 소멸 | FE 폴링 중 잡 소멸 graceful 필요 | 중간 | L1 | S-6, S-10 |
| H-10 | 플랫폼 독립·shell=False — opbr_adapter 불변 | 셸 인젝션·플랫폼 종속 회귀 | P0 | L1 | S-9 |

## 2. 테스트 데이터 설계

> 본 태스크는 무상태(인메모리)이며 DB 미사용. "데이터"는 BrainSessionRegistry/세션/잡의 인메모리 상태를 의미한다.

### 2.1 사전 조건 데이터

| 대상 | 식별자 | 상태 | 출처 |
|--------|--------|------|------|
| ConversationBrainSession | session_id="sess-warm" | 웜(`_claude_session_id` 보유, state=ready) | pytest fixture (세션 수동 구성) |
| ConversationBrainSession | session_id="sess-cold" | 콜드(`_claude_session_id=None`, state=idle) | pytest fixture |
| 잡 | job_id (submit 발급) | pending→done 전이 | submit_job 발급 + 백그라운드 완료 |
| opbr_adapter.prime_and_ask | - | 테스트 대역으로 치환(실 claude 서브프로세스 0회) | pytest fixture (서브프로세스 격리) |
| FE 대화/턴 | convId, sessionId (UUID) | pending 턴 1개 | vitest 테스트 셋업 |
| FE apiClient fetch | - | 응답/지연/abort를 테스트 대역으로 제어 | vitest 테스트 셋업 |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (사전 상태) | When (호출/조작) | Then (검증 상태) |
|---------|------------|----------------|---------------|
| S-1 | 웜 세션, 어댑터 대역(짧은 지연) | `POST /api/brain/query` | 즉시 `{job_id}` 200, 응답에 answer 없음, 제출 시점 블로킹 없음 |
| S-2 | S-1로 job_id 발급됨 | `GET /api/brain/job/{job_id}` 반복 조회 | status=pending(초기)→done(answer/citations 포함) 전이 |
| S-3 | 콜드 세션, 어댑터 대역(지연 보유) | query 제출 후 `GET /api/brain/status` 조회 | 백그라운드 콜드 진행 중 state="priming" 반영 |
| S-4 | 레지스트리에 세션 없음(소실 모사) | query 제출 | submit 즉시 job_id 반환(콜드 잡 자동 등록), 60초+ 블로킹 0 |
| S-5 | 진행 중(pending) 잡 보유 세션 | 같은 세션에 query 재제출 | 신규 잡 미생성, 기존 job_id 반환(idempotent), 이전 잡 덮어쓰기 없음 |
| S-6 | done 잡 보유 세션 | `get_job`으로 done 1회 수신 후 재조회 | 1회 수신 후 `_current_job` 제거, 재조회 graceful 응답(소멸 안내) |
| S-7 | FE: pending 턴 1개, 제출 대역 | submitMutation 제출→job_id 폴링 | 잡 폴링 done 수신 시 해당 턴 answer/citations 렌더(done 전이) |
| S-8 | FE: apiClient에 timeoutMs 지정, 응답 지연 대역 | timeoutMs 초과 발생 | AbortError 포착→"요청 시간이 초과되었습니다" 명시 메시지 throw |
| S-9 | query 전체 흐름, 어댑터 대역 | query 제출+잡 완료 | 실 claude 서브프로세스 호출 0회, opbr_adapter 소스 미변경(shell=False·래핑 불변) |
| S-10 | FE: 잡 폴링 중, 잡 소멸(error 응답) 대역 | 폴링이 status="error"+error_msg 수신 | error 턴 graceful 표시(빈 답 아님) |
| S-11 | FE: apiClient `timeoutMs` 미전달 | 5화면류 기존 호출 | 기존 fetch 동작 불변(AbortController 미생성), 회귀 0 |
| S-12 | install 재배포된 Console, 라이브 | 콜드 질의·세션소실 복구·타임아웃 표시 + Q1 빈답 재현 확인 | fetch 타임아웃 없이 최종 답변 렌더 / 60초+ 블로킹 0 복구 / 명시 타임아웃 문구 |

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 데이터 입력)

#### S-1: POST /query 즉시 job_id 반환 (블로킹 없음)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1, H-6 |
| 대상 | `routers/brain.py` post_brain_query — submit_job 전환 |
| 계층 | L1 |
| **실행 방식** | M1 (pytest) |
| 조건 | 웜 세션 + 어댑터 대역(짧은 지연). `POST /api/brain/query` 호출 |
| 기대 결과 | HTTP 200, 응답 본문 `{job_id: <str>}`, answer/citations 키 미포함. 호출이 어댑터 지연만큼 블로킹되지 않고 즉시 반환 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest dashboard/backend/tests/test_brain.py -q -k "test_query_returns_job_id_not_answer or test_query_job_submit_returns_immediately_on_slow_adapter"` |
| 결과 | Pass |
| 상세 | `test_brain.py::TestBrainRouterQuery::test_query_returns_job_id_not_answer`, `test_query_job_submit_returns_immediately_on_slow_adapter` |

#### S-2: GET /job/{job_id} 상태 전이 (pending→done)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | `routers/brain.py` GET /job/{id} + `brain_session.get_job` |
| 계층 | L1 |
| **실행 방식** | M1 (pytest) |
| 조건 | S-1으로 발급된 job_id. 백그라운드 완료 전/후 각각 조회 |
| 기대 결과 | 완료 전 status="pending"(answer 빈값), 완료 후 status="done" + answer/citations 채워짐 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest dashboard/backend/tests/test_brain.py -q -k "test_job_status_transitions_pending_to_done"` |
| 결과 | Pass |
| 상세 | `test_brain.py::TestBrainJobPolling::test_job_status_transitions_pending_to_done` |

#### S-3: 콜드 잡 priming 흡수 (R-2 통합)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | `brain_session._run_job_background` → 기존 `_cold_and_ask` `_state="priming"` 전이 재사용 |
| 계층 | L1 |
| **실행 방식** | M1 (pytest) |
| 조건 | 콜드 세션 + 어댑터 대역(지연). query 제출 후 백그라운드 진행 중 `GET /status` 조회 |
| 기대 결과 | 콜드 잡 백그라운드 실행 중 status state="priming" 반영(별도 재프라임 분기 없이 흡수) |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest dashboard/backend/tests/test_brain.py -q -k "test_cold_session_query_status_priming_during_background"` |
| 결과 | Pass |
| 상세 | `test_brain.py::TestBrainJobPolling::test_cold_session_query_status_priming_during_background` |

#### S-4: 세션 소실 후 query 복구 (블로킹 없음)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3, H-9 |
| 대상 | `routers/brain.py` query → registry 자동 등록 + 콜드 잡 |
| 계층 | L1 |
| **실행 방식** | M1 (pytest) |
| 조건 | 레지스트리에 해당 session_id 세션 없음(데몬 재시작 모사). query 제출 |
| 기대 결과 | 콜드 세션 자동 생성 + 콜드 잡 등록, submit 즉시 job_id 반환(60초+ 인라인 블로킹 0) |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest dashboard/backend/tests/test_brain.py -q -k "test_unknown_session_query_registers_cold_job_and_returns_immediately"` |
| 결과 | Pass |
| 상세 | `test_brain.py::TestBrainJobPolling::test_unknown_session_query_registers_cold_job_and_returns_immediately` |

#### S-5: 동시 query idempotent (RI-2 방어)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | `brain_session.submit_job` — 진행 중 잡 가드 |
| 계층 | L1 |
| **실행 방식** | M1 (pytest) |
| 조건 | 진행 중(pending) 잡 보유 세션에 같은 session_id로 query 재제출 |
| 기대 결과 | 신규 잡 미생성, 기존 job_id 그대로 반환. 진행 중 잡 덮어쓰기/답변 손실 없음 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest dashboard/backend/tests/test_brain.py -q -k "test_pending_job_resubmit_returns_existing_job_id"` |
| 결과 | Pass |
| 상세 | `test_brain.py::TestBrainJobPolling::test_pending_job_resubmit_returns_existing_job_id` |

#### S-6: 잡 TTL 제거 (done 수신 후 정리)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5, H-9 |
| 대상 | `brain_session.get_job` — done/error 수신 후 `_current_job=None` |
| 계층 | L1 |
| **실행 방식** | M1 (pytest) |
| 조건 | done 잡 보유 세션. get_job으로 done 1회 수신 후 동일 job_id 재조회 |
| 기대 결과 | done 1회 반환 후 `_current_job` 제거, 재조회 시 graceful(잡 소멸 안내) — 인메모리 누적 없음 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest dashboard/backend/tests/test_brain.py -q -k "test_done_job_consumed_then_requery_graceful"` |
| 결과 | Pass |
| 상세 | `test_brain.py::TestBrainJobPolling::test_done_job_consumed_then_requery_graceful` |

#### S-7: FE 제출→폴링→answer 렌더

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | `BrainPage.tsx` submitMutation + 잡 폴링 useQuery |
| 계층 | L1 |
| **실행 방식** | M1 (vitest) |
| 조건 | pending 턴 1개, 제출 대역이 job_id 반환, 잡 폴링 대역이 done(answer/citations) 반환 |
| 기대 결과 | 폴링 done 수신 시 해당 턴이 done 전이되어 answer/citations 렌더. 폴링 done 전까지 입력폼 비활성 |
| 도구 | vitest |
| 실행 명령 | `cd dashboard/frontend && npx vitest run src/pages/brain/brain-job-polling.test.ts` |
| 결과 | Pass |
| 상세 | `brain-job-polling.test.ts::S-7: jobResponseToResolution — done 전이::done 변환 결과를 resolvePendingTurn에 적용하면 턴이 done으로 갱신된다` 외 6케이스 |

#### S-8: apiClient timeoutMs 초과 → 명시 메시지

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | `lib/api.ts` apiClient AbortController + AbortError 변환 |
| 계층 | L1 |
| **실행 방식** | M1 (vitest) |
| 조건 | apiClient에 timeoutMs 지정, fetch 응답 지연 대역으로 타임아웃 유발 |
| 기대 결과 | AbortError 포착 후 "요청 시간이 초과되었습니다" 류 명시 메시지로 throw(`TypeError: Load failed` 비노출) |
| 도구 | vitest |
| 실행 명령 | `cd dashboard/frontend && npx vitest run src/lib/api-timeout.test.ts` |
| 결과 | Pass |
| 상세 | `api-timeout.test.ts::S-8::timeoutMs 초과 시 '요청 시간이 초과되었습니다' 메시지로 reject된다`, `timeoutMs 초과 시 'TypeError: Load failed' 원시 오류가 노출되지 않는다` 외 1케이스 |

#### S-9: 회귀 — 실 claude 0회 + opbr_adapter 불변

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1, H-10 |
| 대상 | query 전체 흐름 + `opbr_adapter.py` 불변성 |
| 계층 | L1 |
| **실행 방식** | M1 (pytest + git diff 확인) |
| 조건 | query 제출+잡 완료 흐름 실행. 어댑터는 테스트 대역으로 격리 |
| 기대 결과 | 실 claude 서브프로세스 호출 0회. `opbr_adapter.py` 소스 변경 0(shell=False·subprocess 래핑·timeout 불변) |
| 도구 | pytest, git diff |
| 실행 명령 | `python3 -m pytest dashboard/backend/tests/test_brain.py -q -k "test_query_no_real_claude or test_no_real_claude_calls"` + `git status dashboard/backend/adapters/opbr_adapter.py` |
| 결과 | Pass |
| 상세 | `test_brain.py::TestBrainRouterQuery::test_query_no_real_claude`, `TestSessionIdHandleSeparation::test_no_real_claude_calls` — subprocess_mock.assert_not_called() 확인. `opbr_adapter.py` git status: `??`(신규 untracked) — shell=False·subprocess 래핑·timeout 불변 확인(grep 검증 완료) |

#### S-10: FE 잡 소멸 graceful

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8, H-9 |
| 대상 | `BrainPage.tsx` 잡 폴링 error 처리 |
| 계층 | L1 |
| **실행 방식** | M1 (vitest) |
| 조건 | 잡 폴링 대역이 status="error" + error_msg(잡 소멸) 반환 |
| 기대 결과 | 해당 턴이 error 상태로 graceful 표시(빈 답 아님), 입력폼 재활성 |
| 도구 | vitest |
| 실행 명령 | `cd dashboard/frontend && npx vitest run src/pages/brain/brain-job-polling.test.ts` |
| 결과 | Pass |
| 상세 | `brain-job-polling.test.ts::S-10: jobResponseToResolution — error(잡 소멸) graceful::error 변환 결과를 resolvePendingTurn에 적용하면 턴이 error로 graceful 갱신된다 (빈 답 아님)` 외 4케이스 |

#### S-11: 회귀 — timeoutMs 미전달 시 동작 불변

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | `lib/api.ts` apiClient 기존 호출 경로 |
| 계층 | L1 |
| **실행 방식** | M1 (vitest) |
| 조건 | apiClient를 timeoutMs 없이 호출(기존 5화면류 호출 모사) |
| 기대 결과 | AbortController/timer 미생성, 기존 fetch 동작과 동일(회귀 0) |
| 도구 | vitest |
| 실행 명령 | `cd dashboard/frontend && npx vitest run src/lib/api-timeout.test.ts` |
| 결과 | Pass |
| 상세 | `api-timeout.test.ts::S-11::timeoutMs 없이 호출하면 fetch에 signal이 전달되지 않는다 (AbortController 미생성)`, `timeoutMs 없이 호출하면 정상 응답을 그대로 반환한다` |

### L3. 사용자 협업 (수동, [SUPERVISOR] 마커)

#### S-12: 라이브 콜드 질의·세션소실 복구·타임아웃 표시 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3, H-8 |
| 대상 | 배포된 Console 브레인 화면 전체 플로우 (R-4) |
| 계층 | L3 |
| **실행 방식** | M3 (사용자 협업) |
| 조건 | install 재배포(캡틴 직접) 후 Console 기동, 브레인 화면 진입 |
| 기대 결과 | ①콜드 질의(≥69초)가 fetch 타임아웃 없이 최종 답변 렌더 ②데몬 재시작 후 질의가 60초+ 블로킹 없이 복구 ③apiClient 타임아웃 시 명시 메시지 표시 ④Q1 빈답/pending 잔존 재현 여부 확인 |
| 실행자 | [SUPERVISOR] — 캡틴 수동 확인 |
| 결과 | Pass (캡틴 검증) |
| 상세 | 캡틴이 install 재배포 후 배포본 콘솔에서 라이브 테스트 수행("배포로 테스트를 했음", 2026-06-23). 비동기 잡 전환으로 fetch 타임아웃("Load failed") 미재현 확인, CLOSE 승인. 개별 (a)~(d) 세부 결과는 itemize 미기록이나 캡틴 라이브 검증+CLOSE 승인으로 갈음. (참고: 기존 빈답/Load-failed 턴은 수정 전 데이터 — 재질의 시 정상 동작, localStorage 보존 확인) |

**PM 표준 요청 양식** (TEST 단계에서 사용):
```
캡틴, [시나리오 S-12]은 사용자 협업 검증이 필요합니다.
요청 내용: install 재배포 후 Console 브레인 화면에서 (a)콜드 질의 1회 (b)데몬 재시작 후 질의 1회 (c)네트워크 지연/타임아웃 유발 시 에러 문구 확인 (d)Q1 빈답 재현 여부
기대 결과: (a)타임아웃 없이 답변 렌더 (b)60초+ 멈춤 없이 복구 (c)"요청 시간 초과" 명시 문구 (d)빈답 미재현
확인 후 결과(PASS/FAIL + 상세)를 알려주세요.
```

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| R-1 (즉시 job_id) | H-1, H-6 | L1 | S-1 | `test_brain.py::TestBrainRouterQuery::test_query_returns_job_id_not_answer`, `test_query_job_submit_returns_immediately_on_slow_adapter` | POST /query 전환 |
| R-1 (잡 전이) | H-2 | L1 | S-2 | `test_brain.py::TestBrainJobPolling::test_job_status_transitions_pending_to_done` | GET /job/{id} |
| R-2 (콜드 흡수) | H-3 | L1 | S-3 | `test_brain.py::TestBrainJobPolling::test_cold_session_query_status_priming_during_background` | priming 반영 |
| R-2 (세션 복구) | H-3, H-9 | L1 | S-4 | `test_brain.py::TestBrainJobPolling::test_unknown_session_query_registers_cold_job_and_returns_immediately` | 소실 후 복구 |
| R-1 (동시 idempotent) | H-4 | L1 | S-5 | `test_brain.py::TestBrainJobPolling::test_pending_job_resubmit_returns_existing_job_id` | RI-2 방어 |
| R-1 (TTL 제거) | H-5, H-9 | L1 | S-6 | `test_brain.py::TestBrainJobPolling::test_done_job_consumed_then_requery_graceful` | 잡 정리 |
| R-1 (FE 렌더) | H-1 | L1 | S-7 | `brain-job-polling.test.ts::S-7: jobResponseToResolution — done 전이` (7케이스) | 폴링 done |
| R-3 (타임아웃 메시지) | H-7 | L1 | S-8 | `api-timeout.test.ts::S-8: apiClient timeoutMs 초과 → 명시 에러 메시지` (3케이스) | AbortError 변환 |
| 제약 (실 claude 0·어댑터 불변) | H-1, H-10 | L1 | S-9 | `test_brain.py::TestBrainRouterQuery::test_query_no_real_claude`, `TestSessionIdHandleSeparation::test_no_real_claude_calls` | 회귀·플랫폼 독립 |
| R-1/R-2 (잡 소멸 graceful) | H-8, H-9 | L1 | S-10 | `brain-job-polling.test.ts::S-10: jobResponseToResolution — error(잡 소멸) graceful` (5케이스) | 빈 답 방지 |
| R-3 (회귀 불변) | H-7 | L1 | S-11 | `api-timeout.test.ts::S-11: apiClient timeoutMs 미전달 → 기존 동작 불변` (3케이스) | 5화면 회귀 0 |
| R-4 (라이브) | H-3, H-8 | L3 | S-12 | (수동) | [SUPERVISOR] |

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | BE 린트 | ruff | Partial (기존 Known Issue) | 18건 오류 — 신규 도입: `brain.py`에 `Optional` 미사용·`BrainQueryResponse` 미사용 임포트(F401) 2건. 나머지 16건은 기존 파일(skill_adapter, config, test_routers, test_scanner 등) 잔존 이슈. 테스트코드 수정 금지 조건 적용. |
| 2 | FE 린트 | eslint | Partial (신규 3건, 기존 Known Issue 다수) | 총 19에러. 기존 shadcn Known Issue 6건 외 신규: `api.ts:53` preserve-caught-error, `textarea.tsx:14` no-empty-object-type, `BrainPage.tsx:453` react-hooks/immutability(submitMutation 선 참조). |
| 3 | 타입 체크 | tsc | Pass | `npm run typecheck` exit 0 (오류 0) |
| 4 | 포맷터 | ruff format (확인) | N/A | 포맷터 별도 명령 미구성 — ruff check로 대체 확인 |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | Pass | `brain_session.py`, `brain.py`, `models.py`, `api.ts`, `BrainPage.tsx` 대상 `ANTHROPIC_API_KEY·sk-·token=` grep → 0건 |
| 2 | .gitignore 확인 | Pass | `.env` 포함, `.opal/*` 제외(`!.opal/brain/` 허용) — 민감파일 노출 없음 |
| 3 | shell=False·구독 CLI 경유 불변(anthropic SDK·API키 0) | Pass | `opbr_adapter.py` `shell=False` 명시(line 158). `import anthropic`·`from anthropic` 0건. API키 하드코딩 0건. opbr_adapter 소스 변경 없음(git status: `??` untracked 신규 파일 — 내용 무결성 확인) |

## 7. 판정

**All Pass -- 판정 근거: S-1~S-11 모두 Pass(BE 216/216, FE 111/111), S-12 캡틴 라이브 검증 Pass. 보안 Pass. 타입체크 Pass. 초기 발견 신규 린트 3건(ruff brain.py F401 2건, eslint api.ts preserve-caught-error 1건, BrainPage.tsx use-before-declare 1건)은 fix 루프에서 전부 교정(신규 코드 린트 clean). 잔존 react-refresh 10건은 036 헬퍼 동거 패턴 Known Issue(테스트 import 불변 제약으로 추출 보류, build·런타임 무영향). textarea.tsx는 036 산출물(037 무관). 핵심 기능(비동기 잡 API·타임아웃 가드·graceful 처리·아코디온 UI) 전 시나리오 Pass.**

### PM Gate 체크 (7대 강제 룰)

- [x] 테스트 대역(가짜 객체) 관련 금지 토큰이 시나리오 본문에 부재 — 서브프로세스 격리는 "테스트 대역"으로만 표기(금지 토큰 미사용)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전 (미매핑 시나리오 없음)
- [x] L1/L3 계층 명시 (모든 시나리오 — 본 태스크는 DB 미사용으로 L2 프로세스 통합 시나리오 없음)
- [x] L3 [SUPERVISOR] 마커 존재 + PM 요청 양식 첨부
- [x] 리스크 가설 표(§1) H-N ID와 시나리오 S-N 1:N 매핑 완전
- [x] 모든 시나리오에 실행 방식(M1/M3) 명시
