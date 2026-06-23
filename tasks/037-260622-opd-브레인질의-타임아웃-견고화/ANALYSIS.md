# ANALYSIS: OPAL Console 브레인 질의 — fetch 타임아웃·ready 사각지대 견고화

> 작성일: 2026-06-22
> 입력: TASK.md
> 출력: ANALYSIS.md

---

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | brain 라우터 | `dashboard/backend/routers/brain.py` | POST /api/brain/query 현재 구조·동기 블로킹 진단 |
| D-2 | 소스 | BrainSession 상태기계 | `dashboard/backend/adapters/brain_session.py` | COLD_TIMEOUT_S·ask·_cold_and_ask 블로킹 경로 |
| D-3 | 소스 | opbr 어댑터 | `dashboard/backend/adapters/opbr_adapter.py` | subprocess.run 동기 블로킹 + timeout 값 |
| D-4 | 소스 | Pydantic 스키마 | `dashboard/backend/models.py` | BrainQueryRequest·BrainQueryResponse 계약 |
| D-5 | 소스 | FE 브레인 페이지 | `dashboard/frontend/src/pages/brain/BrainPage.tsx` | handleSubmit 흐름·status 폴링 멈춤 지점 |
| D-6 | 소스 | FE API 클라이언트 | `dashboard/frontend/src/lib/api.ts` | apiClient fetch 래퍼 — AbortController 부재 |
| D-7 | 설계 | 036 PLAN | `tasks/036-260622-opd-브레인질의-콘솔연동/PLAN.md` | prime-on-intent 패턴·세션 상태기계 설계 근거 |
| D-8 | 설계 | 036 ANALYSIS | `tasks/036-260622-opd-브레인질의-콘솔연동/ANALYSIS.md` | 기존 설계 의도 |
| D-9 | 설계 | 아키텍처 문서 | `docs/ARCHITECTURE.md §OPAL Console` | backend 무상태 원칙·배포 경계 |
| D-10 | 설계 | 컨벤션 | `docs/CONVENTIONS.md §구현 규칙` | 배포 경계·@header 규칙 |
| D-11 | 소스 | BE 테스트 (Phase 2) | `dashboard/backend/tests/test_brain.py` | 현재 테스트 커버리지 파악 |
| D-12 | 소스 | BE 테스트 (스파이크) | `dashboard/backend/tests/test_brain_spike.py` | 스파이크 테스트 커버리지 |

> 인용 형식: `경로:줄번호` 또는 `docs/문서명 §섹션`. (citation-rules.md §2)

---

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `dashboard/backend/routers/brain.py` | POST /api/brain/query 동기 블로킹 핸들러 | 필요 (R-1: 비동기 잡 엔드포인트 전환) | `brain.py:202-251` |
| `dashboard/backend/adapters/brain_session.py` | ConversationBrainSession.ask — 동기 블로킹 경로 + 상태기계 | 필요 (R-1: 잡 상태 관리, R-2: 콜드 폴백 처리) | `brain_session.py:229-346` |
| `dashboard/backend/adapters/opbr_adapter.py` | subprocess.run 동기 블로킹 실행 — 타임아웃 값 보유 | 변경 불필요 (상위 계층에서 비동기 래핑) | `opbr_adapter.py:150-165` |
| `dashboard/backend/models.py` | Pydantic 스키마 — BrainQueryRequest/Response | 필요 (R-1: job_id 기반 응답 스키마 추가) | `models.py:1-100` |
| `dashboard/frontend/src/pages/brain/BrainPage.tsx` | handleSubmit→queryMutation + status 폴링 | 필요 (R-1: 잡 폴링 전환, R-3: 타임아웃 가드) | `BrainPage.tsx:576-593` |
| `dashboard/frontend/src/lib/api.ts` | fetch 래퍼 — AbortController 부재 | 필요 (R-3: 타임아웃 가드 추가) | `api.ts:19-33` |
| `dashboard/backend/tests/test_brain.py` | 현재 100개 단위 테스트 | 필요 (R-1·R-2 신규 시나리오 추가) | `test_brain.py:1-2004` |
| `dashboard/backend/tests/test_brain_spike.py` | 스파이크 18개 테스트 | 변경 불필요 (기존 유지, 회귀 0 보장) | `test_brain_spike.py:1-80` |
| `dashboard/frontend/src/pages/brain/brain-storage.test.ts` | localStorage 헬퍼 637줄 테스트 | 필요 (잡 폴링 흐름 신규 시나리오) | - |
| `dashboard/frontend/src/pages/brain/brain-status.test.ts` | status 폴링 259줄 테스트 | 필요 (잡 결과 폴링·멈춤 조건 추가) | - |
| `dashboard/frontend/src/pages/brain/brain-new-conversation-prime.test.ts` | 새 대화·prime 348줄 테스트 | 필요 (비동기 잡 제출 후 폴링 시나리오) | - |

### 1.2 현재 query 흐름 전체 추적 (동기 블로킹 경로)

```
FE: handleSubmit (BrainPage.tsx:576-593)
  └─ queryMutation.mutate({ question, session_id })   (BrainPage.tsx:592)
       └─ apiClient<BrainQueryResponse>("/api/brain/query", { method:"POST", ... })
            [fetch — AbortController 없음(api.ts:19-33), 브라우저 기본 타임아웃에 노출]
                                        ↓ HTTP
BE: post_brain_query (brain.py:202-251) [FastAPI sync endpoint, threadpool 실행]
  └─ brain_session_registry.ask(session_id, question, project_path)  (brain.py:229-233)
       └─ BrainSessionRegistry.ask → ConversationBrainSession.ask (brain_session.py:405-416)
            └─ ConversationBrainSession.ask (brain_session.py:229-256)
                 ├─ [_claude_session_id IS NOT None] → _warm_ask(question, claude_session_id)
                 │    └─ opbr_adapter.prime_and_ask(cold=False, timeout=WARM_TIMEOUT_S=60)
                 │         └─ subprocess.run(cmd, timeout=60.0, shell=False)  ← 최대 60초 블로킹
                 └─ [_claude_session_id IS None] → _cold_and_ask(question)       ← 사각지대 진입점
                      └─ _cold_prime_with_retry(timeout=COLD_TIMEOUT_S=180)
                           └─ opbr_adapter.prime_and_ask(cold=True, timeout=180.0)
                                └─ subprocess.run(cmd, timeout=180.0, shell=False) ← 최대 180초 블로킹
```

**블로킹 지점 및 타임아웃 값**:

| 경로 | 파일:줄 | 타임아웃 값 | 실측 지연 |
|------|---------|-----------|----------|
| `COLD_TIMEOUT_S` 상수 | `brain_session.py:34` | 180.0초 | 실측 69초 (TASK.md §배경) |
| `WARM_TIMEOUT_S` 상수 | `brain_session.py:35` | 60.0초 | 실측 19.8초 (TASK.md §배경) |
| `subprocess.run(timeout=timeout)` (콜드) | `opbr_adapter.py:152-165` | 180.0초 전달됨 | 최대 180초 |
| `subprocess.run(timeout=timeout)` (웜) | `opbr_adapter.py:152-165` | 60.0초 전달됨 | 최대 60초 |
| `apiClient` (FE fetch) | `api.ts:23-26` | 없음 (브라우저 기본, Safari ≈60초) | 브라우저 컷오프 발생 |

**핵심 문제**: `post_brain_query`는 FastAPI sync endpoint로 threadpool에서 실행된다. `subprocess.run`이 동기 블로킹하는 동안 HTTP 커넥션이 유지된다. 브라우저(특히 Safari)의 기본 fetch 타임아웃 ≈60초가 콜드 질의(≥69초)를 끊는다 (`TASK.md:25-27`).

### 1.3 아키텍처 패턴

- **prime-on-intent**: `POST /api/brain/prime` → `threading.Thread`로 백그라운드 콜드 프라임 트리거 → 즉시 반환 → FE가 `GET /api/brain/status` 2초 간격 폴링 (`brain.py:152-197`, `BrainPage.tsx:467-490`).
- **상태기계 (BrainState)**: `idle|priming|ready|error` — `ConversationBrainSession._state` (`brain_session.py:38`).
- **무상태 원칙**: Q&A 내용 저장 없음, 세션 핸들만 인메모리 보유, DB/파일 영속 금지 (`brain_session.py:6` @header).
- **대화별 session_id 격리**: FE가 `crypto.randomUUID()`로 conversation_id 발급 → BE가 별도 claude 핸들(uuid4)을 발급하여 레지스트리 키와 분리 (`brain_session.py:54-58`).
- **구독 CLI 경유**: `claude -p '//opbr query --read-only ...'` subprocess, `shell=False`, anthropic SDK/API키 금지 (`opbr_adapter.py:20-22`).

### 1.4 prime-on-intent 패턴 — query에 적용 가능성 분석 (R-1 설계 표면)

기존 `POST /api/brain/prime` 패턴 (`brain.py:152-197`):
1. 요청 수신 → `threading.Thread(target=_prime_background, args=(sid, project_path), daemon=True)` 생성
2. 스레드 기동 → **즉시** `BrainPrimeResponse(priming=True)` 반환
3. 백그라운드 스레드: `brain_session_registry.prime(session_id, project_path)` 호출
4. FE: `GET /api/brain/status` 폴링 → `state=priming` 동안 2초 간격 → `ready|error`에서 멈춤 (`BrainPage.tsx:482-487`)

**동일 패턴을 query에 적용 가능성**: 구조적으로 동일하다. 차이는 prime은 결과값(answer)이 없고 query는 answer를 결과로 반환해야 한다는 점이다. 잡 결과 저장소가 추가로 필요하다.

**잡 상태 저장 옵션**:

| 옵션 | 위치 | 장단점 |
|------|------|--------|
| A. `ConversationBrainSession` 내부 확장 | `brain_session.py`의 `ConversationBrainSession`에 `_current_job: dict | None` 필드 추가 | 세션과 잡이 1:1 대응, 추가 클래스 없음. 동시 질의 시 후속 잡이 이전 잡을 덮어쓸 위험 |
| B. 별도 JobRegistry | `brain_session.py` 또는 신규 파일에 `job_id → {status, result}` dict | 세션과 잡 분리, job_id로 FE 추적 단순화. 클래스 추가 |
| C. `BrainSessionRegistry`에 session 레벨 잡 큐 | session 내부에 `deque` 잡 큐 | 다중 잡 지원 가능. 복잡도 증가 |

**무상태 원칙 충족**: 인메모리 dict → 프로세스 재시작 시 소멸. DB/파일 영속 없음 → 원칙 충족 가능 (모든 옵션 공통, `brain_session.py:6` @header `[MUST] backend 무상태 원칙`).

**기존 status 상태기계와 충돌·재사용 여부**:
- `state=idle|priming|ready|error`는 세션 워밍 상태를 나타낸다 (`brain_session.py:38`). 잡 결과 폴링과는 관심사가 다르다.
- 잡 상태(`pending|done|error`)는 세션 상태(`ready`)와 독립이므로 **별도 필드/엔드포인트** 권장.
- status 엔드포인트에 `job_status`, `job_answer`, `job_citations` 필드를 추가하면 엔드포인트 수를 줄일 수 있으나 결합도가 높아진다(부록 B 참조).

### 1.5 R-2 ready 사각지대 — 블로킹 경로 정확한 인용

콜드 폴백 진입 조건 코드 (`brain_session.py:251-253`):
```python
if current_claude_sid is None:
    # 콜드 프라임 후 질의
    return self._cold_and_ask(question)
```

`_cold_and_ask` (`brain_session.py:293-323`) → `_cold_prime_with_retry(question, timeout=COLD_TIMEOUT_S=180)` (`brain_session.py:304`) → `opbr_adapter.prime_and_ask(cold=True, timeout=180.0)` → `subprocess.run(timeout=180.0)` (`opbr_adapter.py:152-165`) ← **최대 180초 동기 블로킹**.

**발생 조건** (`brain_session.py:83` `_claude_session_id: str | None = None` 초기값):
1. 서버 재시작 후 세션 소멸 → FE는 "연동됨" 배지 유지 → 질의 시 콜드 폴백
2. `_should_reset()` 판정 후 `_clear_state()` 호출로 `_claude_session_id = None` (`brain_session.py:174-181`)
3. prime이 완료되지 않은 상태에서 FE가 status 폴링을 멈추고 질의 시도

**status 폴링 멈춤 지점** (`BrainPage.tsx:482-487`):
```typescript
refetchInterval: (query) => {
  const state = query.state.data?.state;
  // ready 또는 error 상태면 폴링 중단
  if (state === "ready" || state === "error") return false;
  return 2_000;
},
```
→ `state==="ready"` 도달 후 폴링 중단. 이후 데몬 재시작 등으로 BE 세션 소멸 시 FE는 "연동됨" 배지를 계속 표시하며, 질의 시 BE는 `_cold_and_ask`로 인라인 콜드 폴백(≥69초 블로킹).

**R-1 비동기 전환이 R-2를 흡수하는지 판단**:

R-1에서 query를 비동기 잡으로 전환하면, `_cold_and_ask`가 백그라운드 스레드에서 실행된다. 브라우저 fetch 타임아웃 문제는 해소된다(즉시 job_id 반환). 단:

- **흡수 조건**: FE 잡 폴링이 콜드 완료(≥69초)까지 대기 가능한 설계여야 한다. 잡 폴링 자체의 fetch 요청은 짧게 반환되므로 타임아웃 문제가 없다.
- **세션 상태 반영 필요**: 콜드 잡 실행 중 `_state`를 `priming`으로 설정하면 기존 status 폴링이 이를 감지해 사용자에게 "연동 중" 상태를 표시한다. `_cold_and_ask` 초입에 `self._state = "priming"` 전이가 이미 구현되어 있다 (`brain_session.py:299-301`).
- **별도 "재프라임 신호 반환" 분기 불필요**: R-1 비동기 전환만으로 60초+ 블로킹 없이 콜드 잡이 백그라운드에서 완료된다. **R-2는 R-1에 통합 설계로 충족 가능**.

**결론**: R-1 비동기 전환으로 R-2의 브라우저 블로킹 문제는 **흡수 가능**. PLAN 단계에서 R-1·R-2를 통합 설계한다.

### 1.6 R-3 apiClient 타임아웃 영향 범위

`apiClient` (`api.ts:19-33`) 현재 구현: 순수 `fetch` 래퍼, `AbortController` 없음. **모든 Console 화면 호출이 이 함수를 경유한다** (`api.ts:6` @header `exports: ["apiClient", "queryClient", "API_BASE_URL"]`).

AbortController 추가 방법별 영향:

| 방법 | 기존 호출 회귀 위험 | 구현 복잡도 |
|------|-------------------|-----------|
| A. 선택적 `timeoutMs` 파라미터 (`options?: RequestInit & { timeoutMs?: number }`) | 없음 (미전달 시 동작 불변) | 낮음 |
| B. 글로벌 기본 타임아웃(예: 30초) | 낮음 (30초 이내 응답이면 영향 없음) | 낮음 |
| C. 브레인 전용 `apiClientWithTimeout` 분리 | 없음 | 중간 |

**R-1 전환 후 타임아웃 임계 변화**: R-1 비동기 전환 후 `POST /api/brain/query`는 즉시 job_id를 반환하므로 브라우저 타임아웃 위험이 제거된다. 잡 폴링(`GET /api/brain/job/{job_id}`)도 짧은 조회이므로 30초 기본값으로 충분하다. **R-3의 긴급도는 R-1 이후 낮아지나**, Safari `TypeError: Load failed` 에러 메시지를 사용자 친화적으로 교체하는 것은 독립적 가치가 있다.

**다른 화면 회귀 위험**: 기존 5개 화면(dashboard/projects/tasks/memory/doctor)은 모두 GET-only 경량 응답이므로 30초 기본 타임아웃으로 회귀 없음. 단, AbortController abort 시 `DOMException: AbortError`가 발생하므로 onError 핸들러에서 이를 포착해 사용자 친화 메시지로 변환해야 한다.

### 1.7 의존성 맵

```
BrainPage.tsx (BrainPage.tsx:1-943)
  ├─ apiClient (api.ts:19-33)              ← 변경 대상 (R-3)
  ├─ useQuery ["brain-auth"]               → GET /api/brain/auth
  ├─ useMutation (primeMutation)           → POST /api/brain/prime
  ├─ useQuery ["brain-status", ...]        → GET /api/brain/status [폴링, 멈춤: BrainPage.tsx:482-487]
  └─ useMutation (queryMutation)           → POST /api/brain/query  ← 변경 대상 (R-1)
                                               (R-1 이후 → job_id 반환 + 잡 폴링 useQuery 추가)

BE brain.py (brain.py:202-251)
  ├─ brain_session_registry (brain_session.py:459)   ← 변경 대상 (R-1·R-2)
  │    └─ ConversationBrainSession (brain_session.py:47-353)
  │         └─ opbr_adapter.prime_and_ask (opbr_adapter.py:90-201)   ← 변경 불필요
  └─ models.py (BrainQueryRequest/Response)          ← 변경 대상 (R-1: job_id 스키마)
```

### 1.8 테스트 현황

**BE**:
- `test_brain.py`: **100개** 테스트 (`test_brain.py:1-2004`) — opbr_adapter 명령 검증·CWD·cold/warm 분기·ConversationBrainSession 상태기계·BrainSessionRegistry 대화 격리·session_id handle 분리·라우터 prime/query/status/error 검증. **모두 mock 기반, 실 claude 호출 0회** (`test_brain.py:6` @header `[MUST] 서브프로세스 전부 mock`).
- `test_brain_spike.py`: **18개** 테스트 (`test_brain_spike.py:1-80`) — 스파이크 출력 파싱·is_error·비JSON·커맨드 플래그 검증.
- **미커버 영역**: 비동기 잡 제출/폴링, 잡 상태 TTL, 콜드 잡 실행 중 `session_state=priming` 반영, 타임아웃 분기, 동시 잡 제출 격리.

**FE**:
- `brain-storage.test.ts`: **637줄** — localStorage 헬퍼(addPendingTurn/resolvePendingTurn/appendTurn 등)
- `brain-status.test.ts`: **259줄** — status 폴링 동작
- `brain-new-conversation-prime.test.ts`: **348줄** — 새 대화·prime 트리거
- **미커버 영역**: 비동기 잡 제출 흐름, 잡 폴링 done 전환 시 answer 렌더, apiClient 타임아웃 에러 메시지.

**RED-first 추가 후보**:

| 테스트 후보 | 레이어 | 근거 요구사항 |
|-------------|--------|-------------|
| `POST /api/brain/query` → 즉시 `{job_id}` 반환 (블로킹 없음) | L1 BE | R-1 |
| `GET /api/brain/job/{job_id}` → `pending` → `done` 전환 | L1 BE | R-1 |
| 콜드 잡 실행 중 `session_state=priming` 반영 | L1 BE | R-2 |
| 세션 소실 후 질의 → 콜드 잡 자동 등록, 60초+ 블로킹 없음 | L1 BE | R-2 |
| apiClient `timeoutMs` 초과 → AbortError, 명시적 에러 메시지 | L1 FE | R-3 |
| queryMutation FE 잡 제출 후 job_id 폴링 흐름 | L1 FE | R-1 |
| 잡 폴링 done 전환 시 answer 렌더 | L1 FE | R-1 |
| 동시 query 2회 → 두 번째가 첫 번째 잡 덮어쓰지 않음 | L1 BE | R-6 리스크 |

---

## 2. 외부 조사 결과

### 2.1 라이브러리/API 조사

해당 태스크는 기존 라이브러리 패턴(FastAPI, TanStack Query) 범위 내 구현이므로 외부 조사 불필요. 관련 확인 사항:

- **FastAPI `BackgroundTasks`**: FastAPI 내장 백그라운드 잡. `threading.Thread`와 비교 시 오류 처리 방식만 다름. prime에서 이미 `threading.Thread`를 사용 중 (`brain.py:182-188`) → 일관성 측면에서 동일 패턴 선택 권고.
- **TanStack Query `refetchInterval`**: 이미 status 폴링에서 사용 중 (`BrainPage.tsx:482-487`). 잡 폴링도 동일 패턴 적용 가능.

### 2.2 버전 호환성

| 카테고리 | 기술 | 버전 |
|----------|------|------|
| FE 언어 | TypeScript | ~6.0.2 |
| FE 프레임워크 | React | ^19.2.6 |
| FE 상태 관리 | TanStack Query | ^5.101.0 |
| FE 빌드 | Vite | ^8.0.12 |
| FE 테스트 | Vitest | ^4.1.9 |
| FE UI | Tailwind CSS + shadcn/ui | ^4.3.1 / ^4.11.0 |
| BE 언어 | Python | 3.x (OPAL .venv) |
| BE 프레임워크 | FastAPI | >=0.110.0 |
| 외부 도구 | Claude Code CLI (`claude -p`) | v2.1.185 실측 (`PLAN.md §2.0.2`) |

---

## 3. 영향 범위

### 3.1 직접 영향

| 파일 | 변경 유형 | 내용 |
|------|----------|------|
| `dashboard/backend/routers/brain.py` | 수정 | `POST /api/brain/query`: 즉시 job_id 반환 + 잡 등록. `GET /api/brain/job/{job_id}` 신규 엔드포인트 추가 |
| `dashboard/backend/adapters/brain_session.py` | 수정 | 잡 상태 관리 로직 추가 (옵션 A: ConversationBrainSession 내부 `_current_job`, 또는 옵션 B: 별도 JobRegistry). COLD_TIMEOUT_S·WARM_TIMEOUT_S 불변 |
| `dashboard/backend/models.py` | 수정 | `BrainJobResponse`(job_id, status, answer, citations, error_msg) 스키마 추가 |
| `dashboard/frontend/src/lib/api.ts` | 수정 | AbortController 기반 타임아웃 가드 추가 (옵션 A 권고: 선택적 `timeoutMs`) |
| `dashboard/frontend/src/pages/brain/BrainPage.tsx` | 수정 | queryMutation: job_id 수신 후 잡 폴링 useQuery 추가. 폴링 done 시 answer 렌더. 타임아웃 에러 메시지 표시 |
| `dashboard/backend/tests/test_brain.py` | 수정 | R-1·R-2 신규 단위 테스트 추가 |
| FE brain 테스트 파일들 | 수정 | R-1·R-3 신규 시나리오 추가 |

### 3.2 간접 영향

- `dashboard/backend/main.py`: 신규 `GET /api/brain/job/{job_id}` 엔드포인트는 brain.py 라우터에 등록되므로 main.py 변경 불필요할 가능성 높음.
- `dashboard/backend/tests/test_routers.py`: brain 라우터 엔드포인트 목록 변경 시 갱신 필요.
- **기존 5개 화면**: apiClient에 선택적 timeoutMs 추가 시 기존 호출자 파라미터 미전달 → 동작 불변.
- **배포**: `~/.opal/` 직접 편집 금지. 소스(`dashboard/`) 수정 후 `install-mac.sh` 재배포. (`docs/CONVENTIONS.md §배포 경계`)

### 3.3 영향 범위 요약

- [ ] DB 스키마 변경 — 해당 없음 (무상태 원칙, 인메모리만)
- [x] API 인터페이스 변경 — `POST /api/brain/query` 응답 형식 변경(job_id), 신규 `GET /api/brain/job/{job_id}`
- [ ] 설정/환경변수 변경 — 해당 없음
- [ ] 빌드/배포 파이프라인 변경 — 해당 없음 (install 재배포는 기존과 동일)

---

## 4. 핵심 발견 사항

1. **R-1 비동기 전환이 R-2를 자연 흡수한다**: `_cold_and_ask` 블로킹이 백그라운드 스레드로 이동하면, FE는 즉시 job_id를 받고 폴링으로 완료를 기다린다. 콜드 잡 실행 중 `_state`를 `priming`으로 설정하는 코드가 `brain_session.py:299-301`에 이미 구현되어 있어, status 폴링이 이를 감지한다. **별도 "재프라임 신호 반환" 분기는 불필요**하며, PLAN 단계에서 R-1·R-2를 통합 설계한다.

2. **prime-on-intent 패턴이 재사용 가능한 청사진이다**: `brain.py:152-197`의 `POST /api/brain/prime` → `threading.Thread` 즉시 반환 패턴을 query에 그대로 적용 가능하다. 추가로 필요한 것은 잡 결과를 저장·조회하는 인메모리 저장소뿐이다. `ConversationBrainSession` 내부에 `_current_job` 필드를 두는 것(옵션 A)이 최소 변경이며 무상태 원칙에 위배되지 않는다.

3. **apiClient 타임아웃은 R-1 전환 후 긴급도가 낮아진다**: R-1 비동기 전환 후 `POST /api/brain/query`는 즉시 반환되므로 브라우저 타임아웃에 노출되지 않는다. 그러나 에러 메시지 명확화(Safari `TypeError: Load failed` → 사용자 친화 메시지)와 안전망으로 R-3 구현은 여전히 가치 있다. 선택적 `timeoutMs` 파라미터 방식(옵션 A)이 기존 호출 회귀 리스크가 0이므로 권장한다.

4. **동시 query 리스크**: `ConversationBrainSession._lock`이 `ask()` 내 blocking call 전에 해제된다 (`brain_session.py:244-256` — lock 해제 후 blocking call). R-1 비동기 전환 시 동시 query 요청이 같은 session에 두 잡을 등록할 수 있다. PLAN 단계에서 "세션당 잡 1개 제한" 또는 "큐잉" 정책을 결정해야 한다.

5. **status 폴링 주기·잡 폴링 통합 여부가 PLAN 결정 필요 항목이다**: 기존 status 폴링(`["brain-status", project, activeSessionId]`, `BrainPage.tsx:467-490`)은 세션 상태를 추적한다. 잡 폴링을 별도 query key(`["brain-job", job_id]`)로 운영하는 것이 관심사 분리에 유리하지만 FE 상태 관리가 복잡해진다. 통합 방식은 단순하지만 결합도가 높아진다 (부록 B 참조).

---

## 5. 제약/리스크

| 항목 | 설명 | 심각도 | 근거 |
|------|------|--------|------|
| RI-1 무상태 원칙 | 잡 결과를 인메모리에만 보관 — 프로세스 재시작 시 미완료 잡 결과 소멸. FE는 폴링 중 데몬 재시작을 graceful하게 처리해야 함 | 중간 | `brain_session.py:6` @header `[MUST] backend 무상태 원칙` |
| RI-2 동시 query 충돌 | 같은 session_id에 복수 잡 제출 시 이전 잡 결과 덮어쓰기 가능. threading.Lock이 ask() blocking call 전 해제됨 | 높음 | `brain_session.py:244-256` |
| RI-3 잡 폴링 중 언마운트 | FE 컴포넌트 언마운트 시 useQuery 정지 → 답변 손실. localStorage에 pending 턴 잔존 가능 | 중간 | `BrainPage.tsx:319-329` (pending 상태 Skeleton — 언마운트 시 미갱신) |
| RI-4 잡 결과 TTL 부재 | 완료 잡 결과가 인메모리에 무한 축적. 장시간 운영 시 메모리 누수 가능 | 낮음 | - |
| RI-5 FastAPI sync + threading 상호작용 | FastAPI sync endpoint는 threadpool 실행. 잡 백그라운드 스레드와 threadpool 스레드가 같은 Lock을 경쟁할 경우 threadpool 소진 가능 | 중간 | `brain.py:202` (sync endpoint decorator) |
| RI-6 플랫폼 독립성·shell=False 불변 | R-1 구현 시 subprocess 래핑 방식 변경 금지 — `shell=False` 유지, anthropic SDK·API키 절대 금지 | 높음 | `opbr_adapter.py:20-22`, `TASK.md:60` |
| RI-7 배포 경계 | `~/.opal/` 직접 편집 금지. 모든 변경은 `dashboard/` 소스 수정 후 install 재배포 | 높음 | `docs/CONVENTIONS.md §배포 경계` |
| RI-8 apiClient 타임아웃 기본값 | 글로벌 기본 타임아웃을 너무 짧게 설정하면 느린 네트워크에서 다른 화면 오작동 | 중간 | `api.ts:19-33` |

---

## 6. 기술 컨텍스트

### 6.1 기술 스택

| 카테고리 | 기술 | 버전 |
|----------|------|------|
| BE 언어 | Python | 3.x (OPAL .venv) |
| BE 프레임워크 | FastAPI | >=0.110.0 |
| BE 테스트 | pytest | OPAL .venv |
| FE 언어 | TypeScript | ~6.0.2 |
| FE 프레임워크 | React | ^19.2.6 |
| FE 상태 관리 | TanStack Query | ^5.101.0 |
| FE 빌드 | Vite | ^8.0.12 |
| FE 테스트 | Vitest | ^4.1.9 |
| FE UI | Tailwind CSS + shadcn/ui | ^4.3.1 / ^4.11.0 |
| 외부 도구 | Claude Code CLI | v2.1.185 실측 |

### 6.2 추천 스킬

| 스킬 | 용도 |
|------|------|
| op-dev-plan | BE/FE 구현 계획 + 잡 상태기계 설계 |
| op-dev-execute | BE 비동기 잡 라우터·FE 잡 폴링 구현 |
| op-dev-test-scenario | R-1~R-3 RED-first 테스트 시나리오 작성 |

### 6.3 추천 MCP

| MCP | 용도 |
|-----|------|
| context7 | TanStack Query v5 refetchInterval 잡 폴링 패턴 확인 (필요 시) |

---

## 부록 A — R-1 설계 옵션 트레이드오프 요약

| 옵션 | 잡 상태 위치 | 특징 | PLAN 권고 조건 |
|------|-----------|------|-------------|
| A (세션 내부) | `ConversationBrainSession._current_job: dict \| None` | 최소 변경, 세션 1:1 잡. 동시 질의 시 덮어쓰기 위험 | 단일 사용자 로컬 데몬, 동시 질의 제한 시 |
| B (별도 JobRegistry) | `job_id → {status, result}` dict | job_id 독립 추적, 여러 잡 병존 가능. 클래스 추가 | 동시 질의 지원 필요 시, 미래 확장 고려 시 |

## 부록 B — status 폴링 vs 잡 폴링 통합/분리 옵션

| 옵션 | 구현 | 장점 | 단점 |
|------|------|------|------|
| 분리 (권고) | status 폴링(`["brain-status", ...]`) + 잡 폴링(`["brain-job", job_id]`) 별도 useQuery | 관심사 분리, 세션 상태와 잡 결과 독립 | FE 상태 2개 관리 |
| 통합 | status 엔드포인트에 `job_status/answer/citations` 필드 추가 | 엔드포인트 수 감소 | 세션 상태기계와 잡 생명주기 결합, 모델 복잡화 |
