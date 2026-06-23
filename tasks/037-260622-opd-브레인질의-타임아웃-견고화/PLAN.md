# PLAN: OPAL Console 브레인 질의 — fetch 타임아웃·ready 사각지대 견고화

> 작성일: 2026-06-23 | 입력: TASK.md, ANALYSIS.md
> 모드: Multi-Feature
> RED-first 트랙: **적용** (동작검증 대상 — 자동 잡 제출/폴링 분기·콜드 흡수·타임아웃 가드. 작성자≠구현자 분리)

## 1. 태스크 개요 + 기능 리스트업

### 1.0 참조 문서 (인라인 단축 참조용)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | brain 라우터 | `dashboard/backend/routers/brain.py` | POST /query 동기 핸들러·prime-on-intent 청사진 |
| D-2 | 소스 | BrainSession 상태기계 | `dashboard/backend/adapters/brain_session.py` | ask/_cold_and_ask 블로킹·잡 상태 저장 위치 |
| D-3 | 소스 | opbr 어댑터 | `dashboard/backend/adapters/opbr_adapter.py` | subprocess.run·shell=False·timeout |
| D-4 | 소스 | Pydantic 스키마 | `dashboard/backend/models.py` | BrainQueryRequest/Response·신규 BrainJobResponse |
| D-5 | 소스 | FE 브레인 페이지 | `dashboard/frontend/src/pages/brain/BrainPage.tsx` | queryMutation·status 폴링·pending 턴 렌더 |
| D-6 | 소스 | FE API 클라이언트 | `dashboard/frontend/src/lib/api.ts` | apiClient fetch 래퍼·AbortController 부재 |
| D-7 | 소스 | BE 라우터 계약 테스트 | `dashboard/backend/tests/test_routers.py` | brain 엔드포인트 존재 검증(계약 파괴 평가) |
| D-8 | 소스 | BE brain 테스트 | `dashboard/backend/tests/test_brain.py` | query 응답 스키마 테스트(계약 파괴 평가) |
| D-9 | 설계 | OPAL Console 아키텍처 | `docs/ARCHITECTURE.md` §OPAL Console | 데몬 무상태·읽기전용·prime-on-intent |
| D-10 | 설계 | 컨벤션 | `docs/CONVENTIONS.md` §@header/Citation/배포 경계 | 구현 규칙·배포 경계 |
| D-11 | 설계 | 037 ANALYSIS | `tasks/037-260622-opd-브레인질의-타임아웃-견고화/ANALYSIS.md` | 근본원인·옵션 트레이드오프(부록 A/B) |

### 1.1 요약

브레인 질의(`POST /api/brain/query`)가 콜드(≈69초)·웜(≈20초) 어느 경로든 동기 블로킹하여 브라우저 fetch 타임아웃(Safari ≈60초)에 끊기는 구조적 결함을 제거한다. query를 **비동기 잡 제출 + 결과 폴링** 패턴(이미 검증된 prime-on-intent 청사진 재사용, → D-1 `brain.py:152-197`)으로 전환하여 콜드 블로킹을 백그라운드 스레드로 옮긴다. ready 사각지대(인라인 콜드 폴백)는 잡 흡수로 자연 해소되고, apiClient에는 안전망으로 AbortController 타임아웃 가드를 추가한다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | BE 비동기 잡 계약 (스키마+엔드포인트+잡 상태) — query를 job_id 제출로 전환, GET /job/{id} 신설, 콜드 잡 흡수 | R-1, R-2 | P0 | 없음 |
| F-002 | FE 잡 폴링 전환 — queryMutation이 job_id 수신 후 별도 잡 폴링 useQuery로 done 시 답변 렌더 | R-1, R-2 | P0 | F-001 (계약 동결) |
| F-003 | apiClient 타임아웃 가드 — 선택적 timeoutMs + AbortError→사용자 친화 메시지 | R-3 | P1 | 없음 |
| F-004 | 라이브 동작검증 — 콜드 질의·세션소실 복구·타임아웃 표시 L3 협업 검증 | R-4 | P0 | F-001, F-002, F-003 |

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 (BE 잡 계약) ──┬─→ F-002 (FE 잡 폴링) ──┐
                     │                          ├─→ F-004 (라이브 검증 L3)
F-003 (apiClient 가드) ──────────────────────────┘
```

- F-001 계약(스키마·엔드포인트)이 동결되어야 F-002 폴링 구현이 가능 → **계약 선행, BE·FE 부분 병렬**.
- F-003은 F-001/F-002와 파일이 겹치지 않아 독립 병렬 가능.

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 된다. RI-N(ANALYSIS §5)을 시나리오 기반 H-N으로 전개.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-001 `POST /api/brain/query` 응답 변경 (`{answer,citations,session_id}` → `{job_id}`) | 기존 라우터 계약 — `test_query_returns_answer_citations_session_id`(`test_brain.py:1655-1659`)·`test_brain_endpoints_exist`(`test_routers.py:259-287`) | P0 | L1(단위, 계약 재작성) | TS-001, TS-009 |
| H-2 | F-001 `GET /api/brain/job/{job_id}` 신설 | 신규 엔드포인트 — pending→done/error 전이 정확성 | P0 | L1(단위 상태 전이) | TS-002 |
| H-3 | F-001 콜드 잡 흡수 — `_cold_and_ask`가 백그라운드 스레드 실행 중 `_state="priming"` 반영(`brain_session.py:299-301`) | status 폴링이 콜드 진행을 감지 못 하면 사각지대 잔존 | P0 | L1(단위 priming 반영) + L3(세션소실 복구) | TS-003, TS-004 |
| H-4 | F-001 동시 query (RI-2 높음) — 같은 session에 2잡 제출 시 이전 잡 덮어쓰기 (`brain_session.py:244-256` lock 해제 후 blocking) | 진행 중 답변 손실 | P1 | L1(단위 — 진행 중 잡 있으면 기존 job_id 반환/신규 거부) | TS-005 |
| H-5 | F-001 잡 결과 TTL 부재 (RI-4 낮음) — 완료 잡 인메모리 무한 축적 | 장시간 운영 메모리 누수 | P2 | L1(단위 — done 폴링 수신 후 제거) | TS-006 |
| H-6 | F-001 FastAPI sync endpoint + threading (RI-5 중간) — 백그라운드 스레드와 threadpool Lock 경쟁 | threadpool 소진 가능 | P1 | L1(단위 — 즉시 반환·블로킹 없음, prime 패턴 재사용 검증) | TS-001 |
| H-7 | F-003 apiClient AbortController 추가 (RI-8 중간) — 기본 타임아웃이 짧으면 기존 5화면 회귀 | 느린 네트워크 오작동 | P1 | L1(FE 단위 — timeoutMs 미전달 시 동작 불변) | TS-008 |
| H-8 | F-002 폴링 중 언마운트/데몬 재시작 (RI-1·RI-3 중간) — useQuery 정지 시 답변 손실·pending 잔존 | 빈 답·UX 저하 | P1 | L1(FE 단위) + L3(라이브) | TS-007, TS-010 |
| H-9 | F-001 무상태 원칙 (RI-1) — 잡 결과 인메모리만, 프로세스 재시작 시 미완료 잡 소멸 | FE가 폴링 중 404/소멸 graceful 처리 필요 | 중간 | L1(BE — DB/파일 영속 0) + L1(FE — 잡 소멸 시 graceful) | TS-006, TS-010 |
| H-10 | F-001 플랫폼 독립·shell=False (RI-6 높음) — opbr_adapter subprocess 래핑 불변(`opbr_adapter.py:153-158`) | 셸 인젝션·플랫폼 종속 회귀 | P0 | L1(회귀 — adapter 미변경 확인) | TS-009 |

---

## 2. 기능별 분석

### F-001: BE 비동기 잡 계약

#### 2.1.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `dashboard/backend/models.py` | `BrainJobResponse` 신규 스키마 + `BrainQueryResponse` job_id 전환 | 수정 |
| BE | `dashboard/backend/routers/brain.py` | `POST /query` job_id 제출 전환 + `GET /job/{id}` 신설 | 수정 |
| BE | `dashboard/backend/adapters/brain_session.py` | `_current_job` 잡 상태 관리 + 백그라운드 ask 래핑 | 수정 |
| BE | `dashboard/backend/adapters/opbr_adapter.py` | subprocess 래핑 — **변경 불필요** (상위 래핑) | 불변 |
| BE | `dashboard/backend/tests/test_brain.py` | R-1·R-2 신규 단위 + 기존 query 계약 테스트 재작성 | 수정 |
| BE | `dashboard/backend/tests/test_routers.py` | `test_brain_endpoints_exist` 잡 엔드포인트 반영 | 수정 |

#### 2.1.2 현재 구현 (ANALYSIS 참조)
- `post_brain_query`는 FastAPI sync endpoint로 threadpool 실행, `brain_session_registry.ask`를 동기 호출 후 `{answer,citations,session_id}` 반환 (`brain.py:202-251`).
- `ConversationBrainSession.ask`는 lock으로 리셋 판정 후 lock 밖에서 blocking 질의 — 콜드는 `_cold_and_ask`(최대 180초), 웜은 `_warm_ask`(최대 60초) (`brain_session.py:229-256`).
- `_cold_and_ask` 초입에 `_state="priming"` 전이가 이미 존재 (`brain_session.py:299-301`) → 콜드 잡 흡수 시 status 폴링이 이를 감지.
- prime-on-intent: `threading.Thread(daemon=True)` 즉시 반환 패턴이 이미 구현 (`brain.py:182-188`, `_prime_background:192-197`) → query 비동기화의 청사진.

#### 2.1.3 영향 범위
- 상위 호출자: `post_brain_query`(라우터). 응답 스키마 변경 → 계약 파괴 → 테스트 재작성 의무(H-1).
- 하위 피호출자: `opbr_adapter.prime_and_ask` 불변(H-10).
- 공유 상태: `brain_session_registry` 싱글턴(`brain_session.py:459`), 세션별 `_lock`.
- 관련 테스트: `test_brain.py:1634-1814`(query 클래스), `test_routers.py:259-287`.

---

### F-002: FE 잡 폴링 전환

#### 2.2.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| FE | `dashboard/frontend/src/pages/brain/BrainPage.tsx` | queryMutation→job_id 제출 + 잡 폴링 useQuery + done 렌더 | 수정 |
| FE | `dashboard/frontend/src/pages/brain/brain-status.test.ts` 또는 신규 잡 폴링 테스트 | 잡 폴링 done 전환·answer 렌더 시나리오 | 수정/신규 |
| FE | `dashboard/frontend/src/pages/brain/brain-new-conversation-prime.test.ts` | 비동기 잡 제출 후 폴링 흐름 | 수정 |

#### 2.2.2 현재 구현 (ANALYSIS 참조)
- `queryMutation`(`BrainPage.tsx:527-566`): mutationFn이 `apiClient<BrainQueryResponse>("/api/brain/query", POST)` 호출, onSuccess에서 `resolvePendingTurn(..., {status:"done", answer, citations})` + `saveConversations`, onError에서 `resolvePendingTurn(..., {status:"error", errorMsg})`.
- status 폴링 useQuery(`BrainPage.tsx:468-490`): queryKey `["brain-status", project, activeSessionId]`, refetchInterval은 `ready|error`에서 false(`BrainPage.tsx:482-487`).
- `handleSubmit`(`BrainPage.tsx:576-593`): `capturedConvIdRef` 캡처 → `addPendingTurn` → `queryMutation.mutate`. 가드에 `queryMutation.isPending` 포함(`BrainPage.tsx:579`).
- pending 턴 렌더: `turn.status==="pending"` Skeleton + Loader2 "답변 대기中…"(`BrainPage.tsx:319-328`), error는 `turn.errorMsg`(`BrainPage.tsx:330-334`).
- 입력폼 비활성화: Textarea(`BrainPage.tsx:898`)·제출 버튼(`BrainPage.tsx:931`)이 `queryMutation.isPending`로 disabled → **같은 대화 동시질의 사실상 차단**(RI-2 완화 근거).

#### 2.2.3 영향 범위
- 상위: BrainPage 렌더 트리. 잡 폴링 상태 추가로 `isPending` 의미가 "잡 진행 중"으로 확장(제출 + 폴링 done 전까지).
- 하위: `apiClient`(F-003 가드 적용), `resolvePendingTurn`/`saveConversations` localStorage 헬퍼(`BrainPage.tsx:159-195, 105-113`) — 계약 불변.
- 공유 상태: localStorage pending 턴(RI-3 언마운트 위험).

---

### F-003: apiClient 타임아웃 가드

#### 2.3.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| FE | `dashboard/frontend/src/lib/api.ts` | `timeoutMs` 옵션 + AbortController + AbortError→메시지 변환 | 수정 |
| FE | 신규 또는 기존 FE 테스트 | timeoutMs 초과 → 명시적 에러 메시지 | 신규/수정 |

#### 2.3.2 현재 구현 (ANALYSIS 참조)
- `apiClient<T>(path, options?)`(`api.ts:19-33`): 순수 fetch 래퍼, AbortController 없음. 모든 화면 호출이 경유(`api.ts:7` exports).
- 글로벌 queryClient: `staleTime/refetchInterval 30s, retry 1`(`api.ts:41-50`).

#### 2.3.3 영향 범위
- 상위: 모든 Console 화면 호출(5화면 GET + brain). `timeoutMs` 미전달 시 동작 불변(옵션 A)이므로 회귀 0(H-7).
- 하위: `fetch`. abort 시 `DOMException: AbortError` 발생 → 변환 필요.

---

### F-004: 라이브 동작검증

#### 2.4.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | (검증 전용, 코드 변경 없음) | L3 [SUPERVISOR] 협업 라이브 시나리오 | 없음 |

#### 2.4.2 현재 구현
- TEST-SCENARIO.md에서 L3 시나리오로 전개(opal-pilot-dev STEP 3.5 PM 작성). 라이브 화면에서 Q1 빈답 재현 확인 + R-1~R-3 적용 후 콜드 질의·세션소실 복구·타임아웃 표시 동작검증.

#### 2.4.3 영향 범위
- 코드 변경 없음. F-001~F-003 완료 후 배포(install 재배포 — 캡틴 직접, RI-7) 후 수행.

---

## 3. 기능별 설계

### F-001: BE 비동기 잡 계약

#### 3.1.1 파일 변경 계획

**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| (없음) | - | - | 신규 파일 없음 — 잡 상태는 기존 `ConversationBrainSession` 내부 확장(옵션 A) | (→ D-11 부록 A) |

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `dashboard/backend/models.py` | BE | `BrainJobResponse` 추가, `POST /query` 응답을 `BrainJobSubmitResponse`(job_id) 신설 | (→ D-4 `models.py:187-199`) |
| 2 | `dashboard/backend/adapters/brain_session.py` | BE | `_current_job` 필드 + `submit_job`/`get_job`/`_run_job_background` 메서드, Registry 위임 | (→ D-2 `brain_session.py:83-89`, `:229-256`) |
| 3 | `dashboard/backend/routers/brain.py` | BE | `POST /query` job 제출 전환, `GET /job/{job_id}` 신설 | (→ D-1 `brain.py:182-197`, `:202-251`) |
| 4 | `dashboard/backend/tests/test_brain.py` | BE | query 계약 테스트 재작성 + R-1·R-2·H-4·H-5 신규 | (→ D-8 `test_brain.py:1636-1660`) |
| 5 | `dashboard/backend/tests/test_routers.py` | BE | `test_brain_endpoints_exist` 잡 엔드포인트 반영 | (→ D-7 `test_routers.py:259-287`) |

#### 3.1.2 API·데이터 모델·설계

**잡 상태 저장 위치 — 결정: 옵션 A (`ConversationBrainSession._current_job`)** (→ D-11 부록 A)

근거: 단일 사용자 로컬 데몬이고, FE가 질의 중 입력폼을 `queryMutation.isPending`으로 비활성화하므로(`BrainPage.tsx:898,931`) 같은 대화 동시질의가 사실상 차단된다. 별도 JobRegistry(옵션 B)는 동시 질의 지원·미래 확장 시에만 정당화되며 현 규모에 과설계. 세션 1:1 잡 매핑이 최소 변경.

> [MUST] `dashboard/backend/adapters/brain_session.py:6`: "backend 무상태 원칙 — Q&A 내용 저장 안 함. 세션 핸들만(휘발성 프로세스 상태) 보유, DB·파일 영속 금지." — `_current_job`은 인메모리 dict, 프로세스 재시작 시 소멸. DB/파일 영속 금지(H-9).

**RI-2(동시 query 덮어쓰기, 높음) 방어 설계** (→ D-11 §5 RI-2):

진행 중 잡이 있으면(`_current_job["status"]=="pending"`) **신규 제출을 거부하지 않고 기존 job_id를 반환**한다(idempotent). 이렇게 하면 FE의 `isPending` disable이 1차 방어, BE의 기존 job_id 반환이 2차 방어로 이중화되어 진행 중 답변 손실(H-4)을 막는다.

**`ConversationBrainSession` 확장 설계** (`brain_session.py:83-89` 필드, `:229-256` ask):

```
# 신규 필드 (__init__)
self._current_job: dict | None = None
# 잡 dict 형태: {"job_id": str, "status": "pending"|"done"|"error",
#               "answer": str, "citations": list, "error_msg": str}

def submit_job(self, question: str) -> str:
    """잡 제출. 진행 중 잡 있으면 기존 job_id 반환(RI-2 방어). 없으면 새 job_id 발급 +
    백그라운드 스레드로 self.ask(question) 실행 후 _current_job에 결과 적재. 즉시 job_id 반환."""
    # with self._lock: 진행 중(pending) 잡이면 기존 job_id 반환
    # 새 job_id = uuid4, _current_job = {status:"pending", ...}
    # threading.Thread(target=self._run_job_background, args=(job_id, question), daemon=True).start()
    # return job_id

def _run_job_background(self, job_id: str, question: str) -> None:
    """백그라운드: self.ask(question) 실행 (콜드/웜 분기 내장). 결과/에러를 _current_job에 적재.
    job_id 불일치 시(덮어쓰기됨) 무시."""

def get_job(self, job_id: str) -> dict | None:
    """job_id 일치 시 잡 스냅샷 반환. status=="done"|"error" 수신 후 _current_job 제거(TTL, RI-4).
    불일치/없음 시 None(FE graceful 404 처리, H-9)."""
```

- `ask`(`brain_session.py:229`)는 **불변** — `submit_job`이 백그라운드 스레드에서 기존 `ask`를 그대로 호출하므로 콜드/웜 분기·5트리거 리셋·`_cold_and_ask`의 `_state="priming"` 전이(`brain_session.py:299-301`)가 모두 재사용된다. **R-2는 R-1에 통합 흡수** — 별도 재프라임 신호 분기 불필요 (→ D-11 §1.5).
- TTL 정책(RI-4, H-5): **done/error 잡을 폴링으로 수신한 직후 `get_job`이 `_current_job=None`으로 제거**. 세션당 잡 1개 + 수신 후 제거 → 무한 축적 방지. 시간/개수 상한 별도 도입 안 함(단일 사용자 데몬 규모, 과설계 금지).

**`BrainSessionRegistry` 위임 메서드** (`brain_session.py:393-416` 패턴):
```
def submit_job(self, session_id, question, project_path) -> str:  # _get_or_create 후 session.submit_job
def get_job(self, session_id, job_id) -> dict | None:             # 세션 없으면 None
```

**Pydantic 스키마** (`models.py` — D-4):

```
class BrainJobSubmitResponse(BaseModel):   # POST /query 신규 응답
    job_id: str

class BrainJobResponse(BaseModel):          # GET /job/{job_id} 응답
    job_id: str
    status: str            # "pending" | "done" | "error"
    answer: str = ""
    citations: list[CitationItem] = []
    error_msg: str = ""
```

> [MUST] `dashboard/backend/models.py:195-199`: "class BrainQueryResponse(BaseModel): answer: str; citations: list[CitationItem]=[]; session_id: str=''" — 기존 `BrainQueryResponse`는 **잡 폴링 done 응답 의미로 흡수하거나 deprecate**. 신규 `POST /query` 응답은 `BrainJobSubmitResponse`로 교체 → 계약 파괴(H-1).

**신규 엔드포인트 계약 — 결정: 별도 `GET /api/brain/job/{job_id}`** (→ D-11 §3 결정 3):

```
POST /api/brain/query  (변경)
  요청: BrainQueryRequest (불변 — question, project, session_id, new_conversation)
  응답: BrainJobSubmitResponse { job_id }   ← 즉시 반환, 블로킹 없음(H-6)
  에러: 400(project/session_id) 불변

GET  /api/brain/job/{job_id}?project=<경로>&session_id=<id>  (신설)
  응답: BrainJobResponse { job_id, status, answer, citations, error_msg }
  status=pending: 진행 중 / done: 완료 / error: 실패(error_msg)
  job_id 미존재(소멸/오타): status="error" + error_msg="잡을 찾을 수 없습니다(세션이 재시작되었을 수 있습니다)" (H-9 graceful)
  400: project/session_id 빈값 (기존 _require_* 헬퍼 재사용, brain.py:55-80)
```

**계약 파괴 영향 평가(H-1)**: `POST /query` 응답이 `{answer,...}` → `{job_id}`로 바뀌면:
- `test_brain.py:1655-1659` `test_query_returns_answer_citations_session_id`: 응답에서 `answer`/`citations` 단정 → **재작성** (job_id 반환 + 별도 get_job 폴링 단정으로 분리).
- `test_routers.py:278-280` `test_brain_endpoints_exist`: `POST /query` body 누락 422 단정은 유지. `GET /job/{id}` 존재 검증 추가.
- `test_query_502_on_runtime_error`(`:1689`)·`test_query_a_and_b_session_isolation`(`:1726`): 동기 응답 단정 → 잡 폴링 done 단정으로 재작성. RuntimeError는 잡 status="error"로 흡수.

**FastAPI sync + threading(H-6, RI-5)**: prime이 동일 패턴(`brain.py:182-188`)으로 검증됨. `submit_job`은 즉시 job_id 반환 → threadpool 스레드를 점유하지 않음. 백그라운드 스레드는 daemon=True. 세션 `_lock`은 기존 `ask`가 blocking call 전에 해제하므로(`brain_session.py:244-256`) threadpool 소진 위험 없음.

> [MUST] `dashboard/backend/adapters/opbr_adapter.py:158`: "shell=False — 셸 인젝션 방지 (H-13)" — opbr_adapter는 **변경하지 않는다**. 상위 계층(brain_session)에서만 비동기 래핑(H-10, RI-6). anthropic SDK·`--safe-mode`·API키 금지.

#### 3.1.3 환경 변경
해당 없음.

#### 3.1.4 배치/마이그레이션
해당 없음 (무상태, 인메모리만).

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 | 기능(L1 BE) | `POST /query` → 즉시 `{job_id}` 200, 블로킹 없음, 응답에 answer 없음 |
| TS-002 | R-1 | 기능(L1 BE) | `GET /job/{job_id}` → pending(초기) → done(answer/citations 포함) 전이 |
| TS-003 | R-2 | 기능(L1 BE) | 콜드 잡 실행 중 `GET /status` state="priming" 반영(_cold_and_ask 흡수) |
| TS-004 | R-2 | 기능(L1 BE) | 세션 소실(레지스트리 비움) 후 query → 콜드 잡 자동 등록, submit 즉시 반환(60초+ 블로킹 0) |
| TS-005 | R-1(RI-2) | 기능(L1 BE) | 동일 session 진행 중 잡 있을 때 재제출 → 기존 job_id 반환(덮어쓰기 없음) |
| TS-006 | R-1(RI-4) | 기능(L1 BE) | done 잡 `get_job` 수신 후 `_current_job` 제거 → 재조회 시 graceful 응답 |
| TS-009 | 제약 | 회귀(L1 BE) | query 시 실 claude/subprocess 호출 0회(mock), opbr_adapter 미변경 확인 |

---

### F-002: FE 잡 폴링 전환

#### 3.2.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `dashboard/frontend/src/pages/brain/BrainPage.tsx` | FE | queryMutation→job_id 제출, 잡 폴링 useQuery 추가, done 시 resolvePendingTurn, 폴링 진행 중 isPending 의미 확장 | (→ D-5 `BrainPage.tsx:527-566`, `:468-490`) |
| 2 | FE brain 테스트 (status/new-conversation-prime) | FE | 잡 제출→폴링 done→answer 렌더 시나리오 | (→ D-5) |

#### 3.2.2 API·화면 설계

**잡 폴링 방식 — 결정: 분리 (별도 `["brain-job", job_id]` useQuery)** (→ D-11 부록 B):

근거: 관심사 분리 — status 폴링(세션 워밍 상태 `["brain-status", project, activeSessionId]`, `BrainPage.tsx:468-490`)과 잡 폴링(질의 결과 생명주기)은 독립 관심사다. 통합(status 엔드포인트에 job 필드 추가)은 엔드포인트 수는 줄지만 세션 상태기계와 잡 생명주기를 결합하여 모델·전이 복잡도를 키운다. 분리 방식의 FE 상태관리 복잡도 증가(상태 2개)는 TanStack Query가 query key별 캐시·라이프사이클을 자동 관리하므로 수용 가능하다.

**FE 흐름 재설계**:
```
handleSubmit (BrainPage.tsx:576-593, 거의 불변)
  ├─ capturedConvIdRef = activeConvId
  ├─ addPendingTurn → saveConversations  (불변)
  └─ submitMutation.mutate({question, session_id})  (← queryMutation 대체)
        mutationFn: apiClient<BrainJobSubmitResponse>("/api/brain/query", POST)  ← {job_id} 수신
        onSuccess: setActiveJobId(job_id)   ← 잡 폴링 트리거

잡 폴링 useQuery (신규):
  queryKey: ["brain-job", project, activeSessionId, activeJobId]
  enabled: activeJobId !== null
  queryFn: apiClient<BrainJobResponse>("/api/brain/job/{jobId}?project=&session_id=", {timeoutMs})
  refetchInterval: (q) => { const s = q.state.data?.status;
                            return (s==="done"||s==="error") ? false : 2_000; }  ← status 폴링 패턴(BrainPage.tsx:482-487) 재사용
  onSuccess/effect:
    status==="done"  → resolvePendingTurn(convId,{status:"done",answer,citations}) + saveConversations + setActiveJobId(null) + clear question
    status==="error" → resolvePendingTurn(convId,{status:"error",errorMsg}) + saveConversations + setActiveJobId(null)
```

- **isPending 의미 확장**: 입력폼 disable(`BrainPage.tsx:898,931`)은 `submitMutation.isPending || activeJobId !== null`로 변경 → 잡 폴링 done 전까지 폼 비활성 유지(RI-2 1차 방어 보존).
- **pending 턴 렌더**: `turn.status==="pending"` Skeleton(`BrainPage.tsx:319-328`) 불변 — 잡 폴링 done 시 resolvePendingTurn으로 done 전이.
- **graceful(H-8, H-9)**: 잡 폴링이 job_id 소멸(status="error" + error_msg)을 수신하면 error 턴으로 표시. 언마운트 시 잔존 pending은 기존 동작 유지(RI-3 — 본 태스크 범위는 폴링 전환, 언마운트 영속화는 제외).
- **타임아웃 가드**: 잡 폴링·제출 호출에 F-003의 `timeoutMs`(권고 30초) 적용.

##### 화면: 프로젝트 브레인 질의 (잡 폴링)
- **ID**: FE-1
- **유형**: detail
- **action**: modify
- **경로**: `/brain` (기존)
- **파일**: `dashboard/frontend/src/pages/brain/BrainPage.tsx`
- **shadcn 컴포넌트**: Skeleton, Button, Textarea, (Loader2/AlertCircle 아이콘) — 기존 재사용, 신규 없음
- **UI 작업**: queryMutation을 submitMutation(job_id 제출)+잡 폴링 useQuery로 분리. pending 턴 Skeleton·error 표시는 기존 컴포넌트(`BrainPage.tsx:319-334`) 재사용. 신규 컴포넌트 없음
- **API 연동**: `POST /api/brain/query`(job_id 수신) → `GET /api/brain/job/{job_id}` 2초 폴링 → done 시 answer/citations 렌더

#### 3.2.3 환경 변경
해당 없음.

#### 3.2.4 배치/마이그레이션
해당 없음.

#### 3.2.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-007 | R-1 | 기능(L1 FE) | submitMutation 제출 → job_id 수신 → 잡 폴링 useQuery 기동 → done 시 answer 턴 렌더 |
| TS-010 | R-1/R-2(H-8/H-9) | 기능(L1 FE) | 잡 폴링이 status="error"(job 소멸) 수신 → error 턴 graceful 표시 |

---

### F-003: apiClient 타임아웃 가드

#### 3.3.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `dashboard/frontend/src/lib/api.ts` | FE | `options?: RequestInit & {timeoutMs?: number}` + AbortController + AbortError→메시지 변환 | (→ D-6 `api.ts:19-33`) |
| 2 | FE 테스트 | FE | timeoutMs 초과 → 명시적 에러 메시지 단정 | (→ D-6) |

#### 3.3.2 API 설계

**타임아웃 방식 — 결정: 옵션 A (선택적 `timeoutMs` 파라미터)** (→ D-11 §1.6 옵션 A):

근거: 기존 호출 회귀 위험 0 — `timeoutMs` 미전달 시 동작 불변(H-7, RI-8). 글로벌 기본 타임아웃(옵션 B)은 느린 네트워크에서 5화면 회귀 가능성이 있어 회피.

```
export async function apiClient<T>(
  path: string,
  options?: RequestInit & { timeoutMs?: number },
): Promise<T> {
  const { timeoutMs, ...rest } = options ?? {};
  const controller = timeoutMs ? new AbortController() : undefined;
  const timer = timeoutMs ? setTimeout(() => controller!.abort(), timeoutMs) : undefined;
  try {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      headers: { "Content-Type": "application/json" },
      signal: controller?.signal,
      ...rest,
    });
    if (!res.ok) throw new Error(`API error ${res.status}: ${res.statusText} (${path})`);
    return res.json() as Promise<T>;
  } catch (e) {
    // AbortError → 사용자 친화 메시지 변환 (변환 위치: apiClient 내부 catch)
    if (e instanceof DOMException && e.name === "AbortError") {
      throw new Error(`요청 시간이 초과되었습니다 (${timeoutMs}ms). 잠시 후 다시 시도해주세요. (${path})`);
    }
    throw e;
  } finally {
    if (timer) clearTimeout(timer);
  }
}
```

- **AbortError→메시지 변환 위치(결정)**: `apiClient` 내부 catch. 이렇게 하면 호출자(BrainPage onError·잡 폴링)는 `error.message`를 그대로 표시하면 되고, Safari `TypeError: Load failed` 대신 명시적 문구가 전달된다. 호출자 측 추가 분기 불필요(DRY).
- `timeoutMs` 미전달 시 controller/timer 미생성 → 기존 경로 완전 불변(H-7).

#### 3.3.3 환경 변경
해당 없음.

#### 3.3.4 배치/마이그레이션
해당 없음.

#### 3.3.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-008 | R-3 | 기능(L1 FE) | timeoutMs 초과 → AbortError 포착 → "요청 시간이 초과되었습니다" 명시 메시지 throw |
| TS-011 | R-3 | 회귀(L1 FE) | timeoutMs 미전달 시 기존 fetch 동작 불변(5화면 회귀 0) |

---

### F-004: 라이브 동작검증

#### 3.4.1 파일 변경 계획
코드 변경 없음 — TEST-SCENARIO.md L3 시나리오로 전개(PM 작성).

#### 3.4.2 설계
- 사전: install 재배포(캡틴 직접, RI-7) 후 Console 기동.
- 검증: ①콜드 질의(≥69초)가 fetch 타임아웃 없이 최종 답변 렌더 ②세션 소실 모사(데몬 재시작) 후 질의 60초+ 블로킹 없이 복구 ③apiClient 타임아웃 시 명시 에러 문구 표시. ④Q1 빈답/pending 잔존 재현 여부 1회 확인.

#### 3.4.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-012 | R-4 | 통합(L3 라이브) | 콜드 질의·세션소실 복구·타임아웃 표시 [SUPERVISOR] 협업 PASS + Q1 경위 확인 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)
| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001 | 1, 2, 3 | opal-be-agent | 순차 | BE 잡 계약 — 스키마→세션→라우터 동일 모듈 순차. **계약 동결 선행** |
| 1 | F-003 | 5 | opal-fe-agent | F-001과 병렬 | apiClient 독립 파일, F-001 의존 없음 |
| 2 | F-001 | 4 | opal-be-agent | Phase1 후 | BE 테스트 (구현 후 RED-first 재작성) |
| 2 | F-002 | 6 | opal-fe-agent | Phase1(F-001 계약) 후 | FE 잡 폴링 — job 엔드포인트 의존 |
| 3 | 문서 | 7 | PM 직접 | Phase1·2 후 | ARCHITECTURE.md 엔드포인트 갱신 |
| 4 | F-004 | 8 | (검증) | 전체 후 | L3 라이브 — install 재배포(캡틴) 후 |

### 4.2 실행 체크리스트
> 총 8개 Step | Phase 4개 | 실행 모드: **복잡**

#### Step 1: BE 잡 스키마 추가
- [ ] 완료
- **소속 기능**: F-001
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `dashboard/backend/models.py`
- **작업 내용**: `BrainJobSubmitResponse{job_id}` 신규 추가, `BrainJobResponse{job_id, status, answer, citations, error_msg}` 신규 추가. @header exports 갱신. 기존 `BrainQueryResponse`는 보존(하위호환). (→ D-4 `models.py:187-199`)
- **완료 기준**: 두 스키마가 import 가능하고 Pydantic 검증 통과. @header exports에 반영.
- **테스트**: TS-001, TS-002 (스키마 사용처 검증)
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: BE 잡 상태 관리 (brain_session)
- [ ] 완료
- **소속 기능**: F-001
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `dashboard/backend/adapters/brain_session.py`
- **작업 내용**: `ConversationBrainSession`에 `_current_job` 필드 + `submit_job`/`_run_job_background`/`get_job` 추가(옵션 A). 진행 중 잡 있으면 기존 job_id 반환(RI-2). done/error 수신 후 `get_job`이 `_current_job=None` 제거(RI-4). `BrainSessionRegistry`에 `submit_job`/`get_job` 위임. **`ask`/`_cold_and_ask`/`opbr_adapter` 불변**(콜드/웜·priming 전이 재사용). @header 갱신 + 변경이력. (→ D-2 `brain_session.py:83-89, 229-256, 299-301, 393-416`)
- **완료 기준**: submit_job 즉시 job_id 반환(블로킹 0), 백그라운드 ask 결과가 _current_job 적재, get_job done 후 제거. 무상태(인메모리만). [MUST] `brain_session.py:6` 무상태 원칙 준수.
- **테스트**: TS-002, TS-003, TS-004, TS-005, TS-006
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 3: BE 라우터 전환 (brain.py)
- [ ] 완료
- **소속 기능**: F-001
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `dashboard/backend/routers/brain.py`
- **작업 내용**: `POST /api/brain/query`를 `brain_session_registry.submit_job` 호출 → `BrainJobSubmitResponse{job_id}` 즉시 반환으로 전환. `GET /api/brain/job/{job_id}` 신설(project·session_id query 필수, `_require_*` 헬퍼 재사용, get_job → BrainJobResponse, 미존재 시 status=error graceful). 400/502 에러 처리는 잡 흡수에 맞게 조정(RuntimeError→잡 status=error). @header exports 갱신 + 변경이력. (→ D-1 `brain.py:55-80, 182-197, 202-251`)
- **완료 기준**: POST /query 즉시 job_id 반환, GET /job/{id} pending→done/error 전이. prime 패턴과 일관(threading 즉시반환). opbr_adapter 미호출 회귀 0.
- **테스트**: TS-001, TS-002, TS-004, TS-009
- **실행 방법**: sub-agent
- **의존**: Step 2

#### Step 4: BE 테스트 재작성·추가 (RED-first 반영)
- [ ] 완료
- **소속 기능**: F-001
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `dashboard/backend/tests/test_brain.py`, `dashboard/backend/tests/test_routers.py`
- **작업 내용**: 계약 파괴 테스트 재작성 — `test_query_returns_answer_citations_session_id`(`test_brain.py:1636`)를 job_id 제출+get_job 폴링 done 단정으로 분리. `test_query_502_on_runtime_error`·`test_query_a_and_b_session_isolation`을 잡 흐름으로 재작성. 신규: 즉시 job_id 반환/get_job 전이/콜드 priming 반영/세션소실 복구/동시 잡 idempotent/TTL 제거/실 claude 0회. `test_routers.py:259` `test_brain_endpoints_exist`에 GET /job/{id} 추가. [MUST] 모든 subprocess mock. @header 갱신. (→ D-8 `test_brain.py:1634-1814`, D-7 `test_routers.py:259-287`)
- **완료 기준**: 신규/변경 pytest 전부 PASS + 기존 회귀 0. 실 claude 호출 0회.
- **테스트**: TS-001~TS-006, TS-009
- **실행 방법**: sub-agent
- **의존**: Step 3

#### Step 5: FE apiClient 타임아웃 가드
- [ ] 완료
- **소속 기능**: F-003
- **영역**: FE
- **agent**: opal-fe-agent
- **파일**: `dashboard/frontend/src/lib/api.ts`, 관련 FE 테스트
- **작업 내용**: `apiClient`에 `options?: RequestInit & {timeoutMs?: number}` + AbortController + AbortError→"요청 시간이 초과되었습니다" 메시지 변환(apiClient 내부 catch). 미전달 시 동작 불변. timeoutMs 초과 에러 메시지 + 회귀 0 테스트 추가. @header 갱신. (→ D-6 `api.ts:19-33`)
- **완료 기준**: timeoutMs 초과 시 명시 메시지 throw, 미전달 시 5화면 회귀 0. vitest PASS.
- **테스트**: TS-008, TS-011
- **실행 방법**: sub-agent
- **의존**: 없음 (F-001과 병렬)

#### Step 6: FE 잡 폴링 전환 (BrainPage)
- [ ] 완료
- **소속 기능**: F-002
- **영역**: FE
- **agent**: opal-fe-agent
- **파일**: `dashboard/frontend/src/pages/brain/BrainPage.tsx`, FE brain 테스트
- **작업 내용**: `queryMutation`(`BrainPage.tsx:527-566`)을 submitMutation(job_id 제출)으로 전환, 별도 잡 폴링 useQuery(`["brain-job", project, activeSessionId, activeJobId]`) 추가(refetchInterval은 status 폴링 패턴 `BrainPage.tsx:482-487` 재사용). done→resolvePendingTurn(done)/error→resolvePendingTurn(error). isPending disable을 `submitMutation.isPending || activeJobId!==null`로 확장(`BrainPage.tsx:898,931`). 잡/제출 호출에 timeoutMs(30s) 적용. job 소멸 graceful. @header 갱신. (→ D-5 `BrainPage.tsx:319-334, 468-490, 527-593`)
- **완료 기준**: 제출→폴링 done→answer 렌더, job 소멸 graceful error. 폴링 done 전까지 폼 비활성. vitest PASS.
- **테스트**: TS-007, TS-010
- **실행 방법**: sub-agent
- **의존**: Step 3 (job 엔드포인트 계약), Step 5 (timeoutMs 활용 — soft)

#### Step 7: docs/ARCHITECTURE.md 갱신
- [ ] 완료
- **소속 기능**: F-001
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/ARCHITECTURE.md` §OPAL Console
- **작업 내용**: 엔드포인트 표(`ARCHITECTURE.md:245`)에 `GET /api/brain/job/{job_id}` 추가, `POST /api/brain/query`를 "비동기 잡 제출(job_id 반환)"로 갱신. 세션 행(`:244`)에 비동기 잡 패턴 한 줄 반영. 변경이력 행 추가. (→ D-9 `ARCHITECTURE.md:236-246`)
- **완료 기준**: 엔드포인트·패턴 설명이 구현과 일치. 변경이력 기록.
- **테스트**: 문서 검토 (PM Gate)
- **실행 방법**: direct
- **의존**: Step 3, Step 6

#### Step 8: 라이브 동작검증 (L3)
- [ ] 완료
- **소속 기능**: F-004
- **영역**: 공통
- **agent**: (검증 — opal-test-agent E2E 또는 PM+캡틴 협업)
- **파일**: (코드 변경 없음)
- **작업 내용**: install 재배포(캡틴 직접, RI-7) 후 Console 기동. 콜드 질의(≥69초) 타임아웃 없이 렌더 / 세션 소실 복구 60초+ 블로킹 0 / 타임아웃 명시 메시지 / Q1 빈답 재현 확인. (→ TASK.md R-4)
- **완료 기준**: TEST-SCENARIO 전 시나리오 PASS, 완료기준 ①②③ 동작검증.
- **테스트**: TS-012
- **실행 방법**: direct (L3 [SUPERVISOR] 협업)
- **의존**: Step 1~7

### 4.3 병렬/순차 판별 근거
| 관계 | 근거 |
|------|------|
| Step 1 → 2 → 3 | 동일/연쇄 모듈 — 스키마를 세션이, 세션을 라우터가 의존 |
| Step 1~4 (F-001) ∥ Step 5 (F-003) | apiClient는 BE와 독립 파일·무의존 → 병렬 |
| Step 3 → Step 6 | FE 잡 폴링이 `GET /job/{id}` 계약에 의존 (계약 동결 선행) |
| Step 5 → Step 6 | soft — timeoutMs 활용. 미완료 시 FE가 옵션 미전달로 진행 가능 |
| Step 4 (테스트) → Step 3 후 | RED-first: 구현(작성자)과 테스트(별도)를 분리, 구현 후 검증 |
| Step 7 → Step 3,6 후 | 문서는 구현 확정 후 |
| Step 8 → 전체 후 | 라이브는 배포 후 최종 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA
| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | POST /query 즉시 job_id 반환(블로킹 0) | TS-001 | 응답 `{job_id}` 200, answer 미포함, mock subprocess 호출 0 |
| F-001 | GET /job/{id} 상태 전이 | TS-002 | pending→done(answer/citations) 정확 전이 |
| F-001 | 콜드 잡 priming 흡수 | TS-003 | 콜드 잡 중 GET /status state="priming" |
| F-001 | 세션 소실 복구 | TS-004 | 소실 후 query submit 즉시 반환, 60초+ 블로킹 0 |
| F-001 | 동시 query idempotent | TS-005 | 진행 중 재제출 시 기존 job_id 반환 |
| F-001 | 잡 TTL 제거 | TS-006 | done 수신 후 _current_job 제거 graceful |
| F-002 | FE 제출→폴링→렌더 | TS-007 | job_id 폴링 done 시 answer 턴 렌더 |
| F-002 | job 소멸 graceful | TS-010 | status=error 수신 시 error 턴 표시 |
| F-003 | timeoutMs 초과 메시지 | TS-008 | AbortError→"요청 시간이 초과되었습니다" 명시 |
| F-003 | timeoutMs 미전달 불변 | TS-011 | 5화면 회귀 0 |
| F-004 | 라이브 콜드·복구·타임아웃 | TS-012 | L3 시나리오 PASS + Q1 확인 |

### 5.2 회귀 테스트
- [ ] 기존 BE pytest 전부 PASS (test_brain.py 변경분 외 회귀 0, test_brain_spike.py 18개 불변)
- [ ] 기존 FE vitest 전부 PASS (brain-storage/status/prime 테스트)
- [ ] opbr_adapter 미변경 — subprocess 래핑·shell=False·timeout 불변 확인
- [ ] 5화면(dashboard/projects/tasks/memory/doctor) apiClient 회귀 0

### 5.3 코드/문서 품질
- [ ] 변경 BE/FE 파일 @header 갱신 (exports·description)
- [ ] 변경이력 행 추가 (docs/ARCHITECTURE.md, KST 일시·태스크 037 표기)
- [ ] citation(`파일:줄`) 규칙 준수
- [ ] 프로젝트 컨벤션 준수 (`docs/CONVENTIONS.md`)

### 5.4 보안
- [ ] [MUST] `opbr_adapter.py:158` shell=False 불변 — 셸 인젝션 방지(H-10)
- [ ] [MUST] anthropic SDK·`--safe-mode`·`ANTHROPIC_API_KEY` 미사용 — 구독 CLI 경유 유지
- [ ] [MUST] backend 무상태 — 잡 결과 DB/파일 영속 0 (인메모리 휘발만)
- [ ] 하드코딩 토큰/시크릿 없음
- [ ] [MUST] 배포 경계 — `~/.opal/` 직접편집 0, dashboard/ 소스 수정 후 install 재배포

---

## 6. 복잡도 판별
| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 8개 | 복잡 |
| 변경 파일 수 | 6개 (models/brain_session/brain.py/test_brain/test_routers/api.ts/BrainPage + FE 테스트) | 복잡 |
| 모듈 범위 | 다중 (BE schema/service/router/test + FE client/page) | 복잡 |
| 작업 유형 | 결함 수정 + 아키텍처 전환(동기→비동기 잡) | 복잡 |
| 외부 의존성 | 없음 (기존 FastAPI·TanStack Query 패턴 내) | 단순 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지
```
Batch 1 (병렬):
  opal-be-agent  → Step 1 → Step 2 → Step 3 (동일 모듈 순차, 파일 충돌 방지)
  opal-fe-agent  → Step 5 (apiClient, 독립)

Batch 2:
  opal-be-agent  → Step 4 (BE 테스트, RED-first)
  opal-fe-agent  → Step 6 (BrainPage 잡 폴링 — Step 3 계약 의존)

Batch 3:
  PM 직접        → Step 7 (docs)

Batch 4:
  검증           → Step 8 (L3 라이브 — install 재배포 후)
```
- **파일 충돌 방지**: BE 4파일(models/brain_session/brain.py/tests)은 모두 opal-be-agent에 그룹핑. FE 2파일(api.ts/BrainPage)은 opal-fe-agent.
- **병렬 극대화**: F-001(BE)과 F-003(apiClient)은 무의존 → Batch 1 병렬.

### C-2. 스킬 요구사항
- 기존 스킬 충분: op-dev-execute(BE/FE 구현), op-dev-test-scenario(RED-first 시나리오), op-dev-test-agent(검증). 신규 스킬 갭 없음.

### C-3. 도구 요구사항
- CLI/MCP/패키지 신규 없음. 기존 pytest/vitest. context7는 TanStack Query v5 refetchInterval 확인 필요 시 선택적(이미 status 폴링에서 사용 중이라 불요 가능).

### C-4. 테스트 전략
- **기능(L1 BE)**: `pytest dashboard/backend/tests/test_brain.py test_routers.py` — TS-001~006, 009. 전부 mock(실 claude 0회).
- **기능(L1 FE)**: `vitest` brain 테스트 — TS-007, 008, 010, 011.
- **회귀**: 전체 pytest/vitest 스위트.
- **통합(L3)**: TS-012 라이브 — install 재배포(캡틴) 후 콜드/복구/타임아웃 [SUPERVISOR] 협업.
- **RED-first**: Step 4 BE 테스트·FE 테스트는 작성자≠구현자 분리(TEST-SCENARIO.md를 PM이 STEP 3.5에서 작성, op-dev-test-agent가 검증).

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| BE | Python, FastAPI, pytest | op-dev-execute, trailofbits/modern-python |
| FE | React 19, TypeScript, TanStack Query v5, Vite, Vitest, shadcn/ui | op-dev-execute, vercel-labs/react-best-practices |
| 외부 | Claude Code CLI(`claude -p`, 구독) — subprocess | (불변) |

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| context7 | 미사용 — TanStack Query refetchInterval 패턴은 기존 status 폴링(`BrainPage.tsx:482-487`)에서 검증됨. 신규 API 불필요 |

### 8.3 참조 문서 (설계 결정 근거)
| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | brain 라우터 | `dashboard/backend/routers/brain.py` | prime-on-intent 청사진·query 전환 |
| D-2 | 소스 | BrainSession | `dashboard/backend/adapters/brain_session.py` | 잡 상태 저장(옵션 A)·콜드 흡수 |
| D-3 | 소스 | opbr 어댑터 | `dashboard/backend/adapters/opbr_adapter.py` | shell=False·subprocess 불변 |
| D-4 | 소스 | 스키마 | `dashboard/backend/models.py` | BrainJobResponse 신설 |
| D-5 | 소스 | FE 브레인 페이지 | `dashboard/frontend/src/pages/brain/BrainPage.tsx` | 잡 폴링 전환 |
| D-6 | 소스 | FE API 클라이언트 | `dashboard/frontend/src/lib/api.ts` | timeoutMs 가드 |
| D-7 | 소스 | 라우터 계약 테스트 | `dashboard/backend/tests/test_routers.py` | 계약 파괴 평가 |
| D-8 | 소스 | brain 테스트 | `dashboard/backend/tests/test_brain.py` | 계약 파괴 평가 |
| D-9 | 설계 | Console 아키텍처 | `docs/ARCHITECTURE.md` §OPAL Console | 무상태·prime-on-intent |
| D-10 | 설계 | 컨벤션 | `docs/CONVENTIONS.md` | @header/citation/배포 경계 |
| D-11 | 설계 | 037 ANALYSIS | `tasks/037-260622-opd-브레인질의-타임아웃-견고화/ANALYSIS.md` | 옵션 트레이드오프 |

---

## 9. 리스크 및 대응 (기능-리스크 연결)
| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| RI-1 | 무상태 — 프로세스 재시작 시 미완료 잡 소멸 | F-001/F-002 | 중간 | 인메모리만, FE 폴링 job 소멸 graceful(status=error, H-9) |
| RI-2 | 동시 query 덮어쓰기 (높음) | F-001/F-002 | 높음 | FE isPending disable(1차) + BE 진행 중 잡 기존 job_id 반환(2차, H-4) |
| RI-3 | 폴링 중 언마운트 — pending 잔존 | F-002 | 중간 | 본 태스크 범위는 폴링 전환. 언마운트 영속화는 제외(기존 동작 유지) |
| RI-4 | 잡 TTL 부재 (낮음) | F-001 | 낮음 | done/error 수신 후 _current_job 제거(세션당 1잡, H-5) |
| RI-5 | FastAPI sync + threading | F-001 | 중간 | prime 동일 패턴 검증(`brain.py:182-188`), 즉시 반환·lock 해제 후 blocking(H-6) |
| RI-6 | 플랫폼 독립·shell=False (높음) | F-001 | 높음 | opbr_adapter 불변, 상위만 래핑(H-10) |
| RI-7 | 배포 경계 (높음) | F-004 | 높음 | `~/.opal/` 직접편집 금지, dashboard/ 수정 후 install(캡틴 직접) |
| RI-8 | apiClient 기본 타임아웃 회귀 | F-003 | 중간 | 옵션 A(선택적 timeoutMs) — 미전달 시 불변(H-7) |
