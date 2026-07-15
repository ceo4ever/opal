# PLAN: 콘솔 프로젝트 브레인 — 휘발성 단일 세션 + 진입/새대화 즉시 워밍

> 작성일: 2026-07-15 | 입력: TASK.md, ANALYSIS.md
> 모드: Multi-Feature | 실행 모드: 복잡

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

콘솔 프로젝트 브레인을 "멀티 대화 관리 + localStorage 이력 영속" 구조에서 **"휘발성 단일 세션 + 진입/새대화 즉시 워밍"** 구조로 단순화한다. FE는 멀티대화 UI·localStorage 이력을 걷어내 단일 대화창으로 좁히고, mount·"새 대화"마다 새 세션을 발급한다. 세션 계층(prime/resume/status·job 폴링/멀티턴)과 프라임 풀 인프라는 "빠름"의 근거이므로 유지하되, 연속 새대화에도 콜드 폴백이 없도록 프라임 풀을 pool_size=2로 상향한다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | FE 단일 대화창 + 이력 비영속 | R-1, R-2 | P0 | 없음 |
| F-002 | FE 세션 수명 (오픈마다 새 세션 · 멀티턴 · "새 대화") | R-3, R-4, R-5 | P0 | F-001 |
| F-003 | BE 프라임 풀 여유 (pool_size 상향 + 풀 충전) | R-6 | P0 | 없음 |
| F-004 | 세션 계층 정리 (죽은 코드 제거 · 유지 대상 회귀 방지) | R-7 | P1 | F-001, F-002 |

**R 커버리지 대조**: R-1→F-001 · R-2→F-001 · R-3→F-002 · R-4→F-002 · R-5→F-002 · R-6→F-003 · R-7→F-004. TASK.md §요구사항 R-1~R-7 전건 커버.

### 1.3 기능 의존 그래프 (ASCII)

```
F-003 (BE 풀)  ── 독립, FE와 병렬 가능
                              ┌─ F-004 (정리)
F-001 (단일창·비영속) ─ F-002 (세션 수명) ─┘
```

- F-003(BE)은 FE 기능과 파일이 겹치지 않아 병렬 가능.
- F-001 → F-002는 동일 파일(BrainPage.tsx)의 상태모델 → 세션수명 순차.
- F-004(정리·회귀검증)는 F-001·F-002·F-003 완료 후 통합 확인.

### 1.4 핵심 제약 인용 ([MUST])

TASK.md §제약 및 `docs/CONVENTIONS.md`에서 이번 설계에 직접 영향을 주는 강제 규칙을 원문 인용한다 (citation-rules §2.4).

- [MUST] `tasks/063-260715-opd-콘솔-브레인-세션-단순화/TASK.md` §제약: "세션 계층(prime/resume/status폴링/잡폴링/멀티턴)은 제거하지 않는다."
- [MUST] `dashboard/backend/adapters/brain_session.py:6` @header: "backend 무상태 원칙 — Q&A 내용 저장 안 함. 세션 핸들만(휘발성 프로세스 상태) 보유, DB·파일 영속 금지."
- [MUST] `tasks/063-260715-opd-콘솔-브레인-세션-단순화/TASK.md` §제약: "062 //opbr query의 content-driven 6단계 워크플로우는 멀티턴 전제라 그대로 유지한다."
- [MUST] `tasks/063-260715-opd-콘솔-브레인-세션-단순화/TASK.md` §제약: "059 `[ASSISTANT]` 마커 캡 + `--session-id`/`--resume` claude 호출 계약 불변."
- [MUST] `docs/CONVENTIONS.md` §구현 규칙 배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `agents/`, ...)에서 수행한다. 변경 후 `./scripts/install-mac.sh`로 재배포하여 검증한다." (본 태스크는 `dashboard/` 소스 수정 후 install)
- [MUST] `docs/CONVENTIONS.md` §구현 규칙 @header: "코드 파일을 생성·수정할 때 파일 상단에 @header 블록을 작성한다." (BrainPage.tsx·brain_session.py @header 갱신 의무)
- [MUST] `dashboard/backend/routers/brain.py:6` @header: "LLM 호출은 이 라우터에만 격리." (FE/설정 등 어느 경로도 새 LLM 호출 추가 금지)

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 된다. ANALYSIS §4.1 유지 대상 회귀 위험(prime/resume·멀티턴·status/job·프라임풀·5트리거리셋·[ASSISTANT]·062)을 검증 가능한 가설로 전환한다.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-003 `prewarm()` 풀 충전 (`brain_session.py:558-571`) | pool_size만 올리고 충전 로직 미수정 시 풀이 1개까지만 참 → 연속 새대화 2회째 콜드 폴백 (R-6 미충족) | P0 | L2 (풀 상태 통합, subprocess mock) | S 후보: pool_size=2에서 연속 checkout 2회가 모두 웜 핸들 반환 |
| H-2 | F-003 락 순서 (`brain_session.py:551-553, 611-616`) | `need=pool_size-have`만큼 다중 스레드 기동 시 `_pool_lock`/`_lock` 순서 위반 → 데드락/레이스 | P0 | L2 (동시성 통합) | S 후보: 동시 prewarm+checkout 반복 시 데드락·중복배정 없음 |
| H-3 | F-003 세마포어 (`brain_session.py:524, 582`) | pool_size=2 충전이 `DEFAULT_MAX_CONCURRENT_PRIME=2` 상한 초과 프로세스 기동 | P1 | L2 (동시 프라임 카운트) | S 후보: 동시 prime subprocess ≤ 2 |
| H-4 | F-002 멀티턴 resume (`BrainPage.tsx` 세션수명 + `brain_session.py:373-394`) | turns[] 리팩터 후 같은 세션 2턴+ 질의가 `--resume` 웜 경로/turn_count++ 유지 실패 → 이어묻기 단절 | P0 | L1 (FE 단위) + L3 (E2E 멀티턴) | S 후보: 동일 세션 2턴 질의 시 이전 맥락 이어짐 |
| H-5 | F-002 mount 새 세션 (`BrainPage.tsx` sessionId 초기화) | 재mount마다 새 session_id + 자동 prime 트리거 실패 → 콜드/미프라임 | P1 | L1 (FE 단위) + L3 (E2E) | S 후보: 메뉴 재진입마다 새 session_id·prime 발생 |
| H-6 | F-002 "새 대화" 세션 전환 가드 (`BrainPage.tsx` capturedSessionId) | pending 잡 진행 중 "새 대화" 클릭 시 이전 답변이 새 세션 turns에 오귀속 | P1 | L1 (FE 단위) | S 후보: pending 중 새 대화 → 이후 done 응답이 이전 세션에 귀속(새 세션 오염 없음) |
| H-7 | F-001 localStorage 제거 (`BrainPage.tsx:111-133, 438-440`) | 잔존 save/load 호출로 런타임 참조 오류 또는 이력 재기록 | P2 | L1 (FE 단위·정적) | S 후보: 재로드 후 turns 빈 상태 + localStorage 브레인 키 미기록 |
| H-8 | F-001/F-002 status·job 폴링 (`BrainPage.tsx:539-609`) | sessionId 상시 non-null화 후 폴링 enabled/queryKey·job 귀속 회귀 | P1 | L1 (FE 단위) | S 후보: ready 전이 감지·잡 done 수신 정상 |
| H-9 | 불변 계약 `opbr_adapter.py:129-154` | `[ASSISTANT]` 첫 줄 마커 + `--session-id`(cold)/`--resume`(warm) 플래그 계약 훼손 (059) | P0 | L1 (정적 diff 검사) | S 후보: opbr_adapter.py 무변경 확인 (prompt·cmd 배열 불변) |
| H-10 | 불변 계약 062 워크플로우 | //opbr query 답변 생성 6단계 경로 변경 | P1 | L3 (답변 품질 회귀) | S 후보: 동일 질의 답변·인용 정상 산출 |
| H-11 | 유지 대상 5트리거 리셋 (`brain_session.py:169-199, 373-394`) | turn≥20·유휴30분·크래시 투명 재프라임 등 리셋 로직 회귀 | P2 | L1 (BE 단위) | S 후보: turn≥max_turns 시 콜드 재프라임 |
| H-12 | 무상태 원칙 (`brain_session.py:6` @header) | 정리·리팩터 중 파일/DB 영속 신규 도입 | P0 | 정적 리뷰 | S 후보: 새 파일 쓰기·DB 접근 코드 부재 확인 |

**H-1 상세 (설계 근거 — R-6 핵심)**: 현재 `prewarm()`은 `have < pool_size`일 때 `_pool_inflight += 1` 후 스레드를 **정확히 1개만** 기동한다 (`brain_session.py:566-571`). `_prewarm_targets`(`main.py:43-46`)·`checkout_warm_handle`(`brain_session.py:611-616`)는 각각 `prewarm()`을 프로젝트당 1회만 호출한다. 따라서 `DEFAULT_POOL_SIZE`를 2로 올려도 단일 트리거로는 풀이 최대 1까지만 차고, 연속 새대화 2회째는 여전히 콜드 폴백된다. R-6 AC("연속 새대화 N회에도 콜드 폴백 없이 ready")를 충족하려면 상수 상향과 함께 `prewarm()`이 `need = pool_size - have`만큼 충전하도록 수정해야 한다 (§3 F-003).

---

## 2. 기능별 분석

### F-001: FE 단일 대화창 + 이력 비영속

#### 2.1.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| FE | `dashboard/frontend/src/pages/brain/BrainPage.tsx` | 브레인 화면 — 멀티대화 UI·localStorage 이력 | 수정 |
| FE | `dashboard/frontend/src/pages/brain/brain-storage.test.ts` | localStorage·멀티대화 헬퍼 단위 테스트 | 수정(대폭 재작성) |

#### 2.1.2 현재 구현
- localStorage 이력: `STORAGE_KEY = "opal-console:brain:conversations"`(`BrainPage.tsx:111`), `loadConversations`/`saveConversations`(`:113-133`).
- 멀티대화 모델: `BrainConversation[]` 배열 상태 `allConversations`(`:438-440`), 프로젝트 필터 `filterConversationsByProject`(`:254-259`), 활성 대화 `activeConvId`/`activeConv`(`:445-451`).
- 좌측 대화목록 aside + `ConversationView`(`:384-422`, `:771-814`), 대화 선택 `handleSelectConversation`(`:684-700`).
- 낙관적 턴 헬퍼는 `BrainConversation[]` 기준으로 conversationId·capturedConvId를 받아 동작: `addPendingTurn`(`:140-173`), `resolvePendingTurn`(`:179-215`).

#### 2.1.3 영향 범위
- 상위 의존: `BrainPage` 컴포넌트 전체가 `allConversations`/`activeConv`에 결합 — 상태모델 교체 시 렌더·핸들러 동반 수정(F-002와 동일 파일).
- 공유 계약: `session_id`는 BE `POST /prime`·`GET /status`·`POST /query`·`GET /job` 페이로드 키 — FE가 계속 발급·전달해야 하므로 필드명 불변(`brain.py:79-86` `_require_session_id`).
- 관련 테스트: `brain-storage.test.ts`(loadConversations/saveConversations/filterConversationsByProject/makeNewConversation/appendTurnToConversation 대상 — 제거 심볼 참조), `brain-new-conversation-prime.test.ts`(makeNewConversation 참조).

### F-002: FE 세션 수명 (오픈마다 새 세션 · 멀티턴 · "새 대화")

#### 2.2.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| FE | `dashboard/frontend/src/pages/brain/BrainPage.tsx` | 세션 발급·prime·폴링·핸들러 | 수정 |
| FE | `dashboard/frontend/src/pages/brain/brain-new-conversation-prime.test.ts` | 새대화→프라임·세션 페이로드 테스트 | 수정 |

#### 2.2.2 현재 구현
- 활성 세션 발급: `makeNewConversation(project)`이 conv id + session_id 2개 UUID 발급(`:262-272`). mount 시 `activeConvId` 초기화는 저장된 대화 복원(`:445-448`) — 재진입 시 새 세션이 아님.
- prime 트리거: `primedSessionRef`로 중복 방지하며 `POST /prime`(`:569-576`), idle 감지 재프라임(`:579-584`).
- 멀티턴: 같은 session_id로 `POST /query` → BE `_warm_ask`가 `--resume`(`:373-389`) — FE는 session_id만 유지하면 됨.
- "새 대화": `handleNewConversation`(`:658-682`) — 새 conv 생성 + localStorage 저장 + prime. 하단 폼 버튼(`:994-1004`)과 좌측 aside +버튼(`:776-785`) 2곳에서 호출.
- 오귀속 가드: 제출 시점 `capturedConvIdRef`로 convId 캡처(`:462, 645`), 잡 done/error를 캡처 convId에 귀속(`:617-624`).

#### 2.2.3 영향 범위
- BE 계약 불변: `_get_or_create`가 미등록 session_id를 신규 세션으로 생성하며 풀 웜 핸들을 이식(`brain_session.py:526-554`). FE가 새 session_id를 보내면 mount·새대화마다 자동으로 새 세션이 웜 배정된다 — R-3/R-5의 BE 측 근거.
- 공유 상태: status/job 폴링 queryKey에 `activeSessionId` 포함(`:545, 596`) — 세션 교체 시 자동 재폴링. 단일 세션화 후 `sessionId`로 치환.

### F-003: BE 프라임 풀 여유

#### 2.3.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `dashboard/backend/adapters/brain_session.py` | pool_size 상수 + prewarm 충전 로직 | 수정 |
| BE | `dashboard/backend/tests/test_brain.py` | 풀·세션 회귀 + pool_size 충전 테스트 | 수정(보강) |

#### 2.3.2 현재 구현
- 상수: `DEFAULT_POOL_SIZE=1`(`:46`), `DEFAULT_MAX_CONCURRENT_PRIME=2`(`:47`).
- 충전: `prewarm(project_path)` — `have = len(pool)+inflight`가 `pool_size` 미만이면 `inflight+=1` 후 daemon 스레드 **1개** 기동(`:558-571`). `_prime_into_pool`은 세마포어 하에서 subprocess 후 append하고 **재트리거하지 않음**(`:573-596`).
- 체크아웃: `checkout_warm_handle`가 pop 성공 시에만 `prewarm()` 1회 호출(`:598-616`). 풀 empty면 리필 트리거 안 함(콜드 폴백).
- 트리거 진입: 기동 lifespan(`main.py:57-63`) — `prewarm_projects`(opt-in) 프로젝트당 1회; 설정 토글(`routers/config.py:102`) 1회.

#### 2.3.3 영향 범위
- **핵심 발견(H-1)**: 단일 trigger당 최대 +1 핸들이므로 pool_size만 올려도 풀은 1까지만 참. 충전 로직 수정 필수.
- 세마포어(`_prime_semaphore`, `:524`)가 전역 동시 프라임 상한 — 충전 스레드 다중 기동해도 실제 동시 subprocess는 상한 이하로 직렬화(H-3 보호).
- opt-in 의존: 풀은 `prewarm_projects` 등재 프로젝트에만 적재된다(060 모델). 미등재 프로젝트는 매 세션 콜드 → R-6 웜 효과는 "프라임 풀 토글 ON(설정 화면)" 프로젝트에 한정(§9 R-63, 범위 유지).

### F-004: 세션 계층 정리 (죽은 코드 제거 · 유지 대상 회귀 방지)

#### 2.4.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `dashboard/backend/routers/brain.py` | 5 엔드포인트 — 폐기 필드 정리 | 수정(소폭) |
| FE | `dashboard/frontend/src/pages/brain/BrainPage.tsx` | 제거 심볼 잔재 정리 | 수정(F-001/002에 통합) |
| 공통 | `dashboard/backend/adapters/opbr_adapter.py` | 호출 계약 — **불변 확인만** | 무변경 |

#### 2.4.2 현재 구현
- BE 엔드포인트 5종(auth/status/prime/query/job) 모두 단일 session_id 설계로 이미 멀티대화 미전제 → ANALYSIS §2.7 판정대로 **삭제 대상 없음**.
- 폐기 잔재: `POST /query`가 `new_conversation` 필드를 "호환 목적 수신하되 무시"로 문서화(`brain.py:221, 237-238`). `BrainQueryRequest`에 필드가 남아 있는지 확인 후, FE가 더 이상 보내지 않으므로 정리 여부 판단.
- FE 제거 심볼: F-001에서 제거되는 `loadConversations`/`saveConversations`/`filterConversationsByProject`/`makeNewConversation`/`appendTurnToConversation`/`ConversationView`/`BrainConversation` — @header exports/depends 목록도 동반 정리.

#### 2.4.3 영향 범위
- 유지 대상 회귀 위험(ANALYSIS §4.1): prime/resume·멀티턴·status/job·프라임풀 리필·5트리거리셋·[ASSISTANT] 마커·062 — 정리가 이들을 건드리지 않음을 검증(H-9~H-12).

---

## 3. 기능별 설계

> 각 설계 결정에 인라인 인용(`(→ D-N §N)` 또는 `경로:줄번호`)을 병기한다. citation-rules §2 준수.

### F-001: FE 단일 대화창 + 이력 비영속

#### 3.1.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `BrainPage.tsx` | FE | 타입·헬퍼 계층: `BrainConversation`·`STORAGE_KEY`·`loadConversations`·`saveConversations`·`filterConversationsByProject`·`makeNewConversation`·`appendTurnToConversation`·`ConversationView` 제거. `addPendingTurn`/`resolvePendingTurn`을 `BrainTurn[]` 기반으로 리팩터. @header description·exports 갱신 | `BrainPage.tsx:89-278`, `:384-422` |
| 2 | `BrainPage.tsx` | FE | 컴포넌트 계층: `allConversations`/`activeConvId`/`activeConv` 상태 제거 → `turns: BrainTurn[]` 단일 상태. 좌측 aside(`:771-814`)·`handleSelectConversation`·프로젝트전환 conv 재설정 effect(`:495-506`) 제거. 단일 컬럼 전체폭 레이아웃 | `BrainPage.tsx:438-506, 769-814` |
| 3 | `brain-storage.test.ts` | FE | 제거 심볼 대상 테스트 삭제, `addPendingTurn`/`resolvePendingTurn` turns 기반 시그니처로 갱신 | `brain-storage.test.ts:13-24, 71-` |

#### 3.1.2 API·데이터 모델·화면 설계

**데이터 모델 변경** (FE 인메모리 전용 — localStorage·파일 영속 없음, R-2)

- 유지: `BrainTurn { q, a, citations, ts, status, errorMsg? }`(`BrainPage.tsx:90-97`), `CitationItem`(`:56-61`), `BrainJobResponse`(`:64-70`).
- 제거: `BrainConversation`(`:99-105`) — 배열·프로젝트필터·created_at 불필요.
- 헬퍼 시그니처 리팩터 (단일 turns 배열 기준):
  - `addPendingTurn(turns: BrainTurn[], question: string): BrainTurn[]` — pending 턴 1개 append (conversationId·sessionId·project 인자 제거).
  - `resolvePendingTurn(turns: BrainTurn[], resolution): BrainTurn[]` — 마지막 pending 턴을 done/error로 갱신 (capturedConvId 인자 제거 — 세션 오귀속 가드는 F-002의 capturedSessionId로 이동).
  - `[MUST]` 유지: `jobResponseToResolution`·`jobPollingInterval`(`:72-87`) 시그니처 불변 — brain-job-polling.test.ts 회귀 방지.

**화면 설계**

##### 화면: 프로젝트 브레인 (단일 대화창)
- **ID**: FE-1
- **유형**: detail
- **action**: modify
- **경로**: `/brain` (기존 라우트 불변)
- **파일**: `dashboard/frontend/src/pages/brain/BrainPage.tsx`
- **shadcn 컴포넌트**: Card, Textarea, Button, Alert, Badge, Skeleton, Accordion (모두 기존 사용분 — 신규 추가 없음)
- **UI 작업**:
  - 좌측 대화목록 `aside`(`:771-814`) 및 `ConversationView` 제거 → 대화 본문이 전체 폭(`flex-1`) 사용 (M-2 확정).
  - 헤더: 제목을 "프로젝트 브레인" 고정 + 기존 연동 상태 배지(priming/ready/error/idle, `:829-891`) 유지.
  - 빈 상태 카드에 R-2 경량 안내 1줄 추가: "이 대화는 저장되지 않아요 — 새로고침하거나 다시 열면 처음부터 시작합니다." (배너 금지, `:910-921` 빈 상태 영역, M-4 확정).
  - turns 아코디온 렌더(`:924-947`) 유지 — `activeConv.turns` → `turns`로 소스 치환.
- **API 연동**: 변경 없음 — 기존 auth/status/prime/query/job 계약 유지. session_id 키 불변.

#### 3.1.3 환경 변경
해당 없음 (신규 패키지·설정 없음).

#### 3.1.4 배치/마이그레이션
해당 없음. (localStorage 기존 키 `opal-console:brain:conversations`는 더 이상 읽지 않으므로 자연 방치 — 제거 스크립트 불요, 무해)

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 AC (사이드바 DOM 부재) | 기능 테스트 | 렌더 결과에 대화목록 aside·ConversationView 없음, 단일 컬럼 |
| TS-002 | R-1 AC (멀티관리 심볼 제거) | 산출물 검사 | `loadConversations`/`filterConversationsByProject`/`makeNewConversation`/`appendTurnToConversation`/`BrainConversation` 심볼 부재 |
| TS-003 | R-2 AC (localStorage 미기록) | 기능 테스트 | 질의·응답 후 `localStorage`에 브레인 대화 키 미기록 (H-7) |
| TS-004 | R-2 AC (재오픈 백지) | 기능 테스트 | 재mount 시 turns 빈 배열 |
| TS-005 | R-2 AC (안내 문구) | 산출물 검사 | 빈 상태에 비영속 안내 1줄 존재 |

### F-002: FE 세션 수명 (오픈마다 새 세션 · 멀티턴 · "새 대화")

#### 3.2.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `BrainPage.tsx` | FE | `sessionId` 단일 상태 도입(`useState(()=>crypto.randomUUID())` — mount마다 새 세션, R-3). prime effect·status/job 폴링을 `sessionId` 기준으로 치환. `capturedSessionIdRef`로 세션 오귀속 가드 | `BrainPage.tsx:445-462, 539-609` |
| 2 | `BrainPage.tsx` | FE | `handleNewSession`(구 `handleNewConversation`): turns 초기화 + 새 sessionId 발급 + mutation/job 리셋 + 새 세션 prime (R-5). 하단 폼 버튼만 유지·주버튼화, aside +버튼 제거(M-3) | `BrainPage.tsx:658-682, 994-1004` |
| 3 | `BrainPage.tsx` | FE | `handleSubmit`: 제출 시 `capturedSessionIdRef.current = sessionId` 캡처. 잡 done/error 시 현재 sessionId≠캡처면 폐기(H-6) | `BrainPage.tsx:639-656, 611-630` |
| 4 | `brain-new-conversation-prime.test.ts` | FE | `makeNewConversation` 참조를 `makeSessionId` 또는 인라인으로 갱신, prime/query 페이로드(session_id 포함) 테스트 유지 | `brain-new-conversation-prime.test.ts:14, 76-` |

#### 3.2.2 API·데이터 모델·화면 설계

**세션 수명 상태기계 (FE)**

- 세션 발급: `const [sessionId, setSessionId] = useState<string>(() => crypto.randomUUID())` — mount마다 1회 발급(R-3). 선택적 순수 헬퍼 `makeSessionId(): string { return crypto.randomUUID(); }`로 테스트 용이성 확보.
- 자동 prime: 기존 effect(`:569-576`)를 `sessionId` 의존으로 치환 — 인증+프로젝트+sessionId 조건에서 `POST /prime {project, session_id}` 1회. `primedSessionRef`로 중복 방지 유지. idle 재프라임 effect(`:579-584`) 유지.
- 멀티턴(R-4): FE는 동일 `sessionId`로 연속 `POST /query`만 보내면 BE가 `--resume` 웜 재개(`brain_session.py:298-304, 373-389`) — FE 추가 로직 없음. `[MUST]` opbr_adapter 호출 계약 불변(`opbr_adapter.py:148-154`).
- "새 대화"(R-5) `handleNewSession()`:
  1. `setTurns([])` — 내역 초기화
  2. `const next = makeSessionId(); setSessionId(next)` — 새 세션 발급
  3. `submitMutation.reset(); setActiveJobId(null); setQuestion("")` — 잡/입력 리셋
  4. `primedSessionRef.current = next; primeMutation.mutate({ session_id: next })` — 즉시 prime (웜 배정은 BE 풀이 담당)
  5. `queryClient.invalidateQueries({ queryKey: ["brain-status", project, next] })` — 상태 즉시 재폴링
  → 메뉴 재오픈과 동일 동작(초기화+새세션+즉시 ready 지향).
- 세션 오귀속 가드(H-6): 잡 done/error effect(`:612-630`)에서 `capturedSessionIdRef.current !== sessionId`이면 무시. pending 중 "새 대화" 클릭해도 이전 세션 답변이 새 세션 turns에 붙지 않음.
- 게이팅 단순화: `activeConvId === null` 조건(`:642, 976, 1009`) 제거 — sessionId는 상시 non-null. `canSubmit`(brain-status.test.ts) 계약(project+session_id)은 유지(H-8).

**화면 설계**

##### 화면: 프로젝트 브레인 — "새 대화" 액션
- **ID**: FE-2
- **유형**: detail
- **action**: modify
- **경로**: `/brain`
- **파일**: `dashboard/frontend/src/pages/brain/BrainPage.tsx`
- **shadcn 컴포넌트**: Button (기존)
- **UI 작업**: 하단 입력 폼의 "새 대화" 버튼(`:994-1004`) 유지·주버튼화(레이블 "새 대화" 유지 — 발견성). 좌측 aside 상단 + 아이콘 버튼(`:776-785`)은 aside와 함께 제거(M-3).
- **API 연동**: `POST /api/brain/prime {project, session_id}` (새 세션 즉시 프라임). 신규 엔드포인트 없음.

#### 3.2.3 환경 변경
해당 없음.

#### 3.2.4 배치/마이그레이션
해당 없음.

#### 3.2.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-006 | R-3 AC (재진입 새 session_id) | 기능 테스트 | 재mount마다 새 sessionId + 진입 직후 prime 호출 (H-5) |
| TS-007 | R-4 AC (멀티턴 이어짐) | 통합 테스트 | 동일 세션 2턴 질의 시 --resume 웜 경로·이전 맥락 유지 (H-4) |
| TS-008 | R-5 AC (새대화 초기화+새세션) | 기능 테스트 | "새 대화" 클릭 후 turns=[], 새 sessionId, prime 재호출, 곧 질의 가능 |
| TS-009 | R-5 (오귀속 가드) | 기능 테스트 | pending 중 새 대화 클릭 → 이후 done이 이전 세션 귀속, 새 세션 turns 미오염 (H-6) |
| TS-010 | R-4 (계약 불변) | 산출물 검사 | prime/query 페이로드에 session_id 포함, opbr_adapter.py 무변경 (H-9) |

### F-003: BE 프라임 풀 여유

#### 3.3.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `brain_session.py` | BE | `DEFAULT_POOL_SIZE` 1→2 (M-1 확정) | `brain_session.py:46` |
| 2 | `brain_session.py` | BE | `prewarm()`가 `need = pool_size - have`만큼 충전 스레드 기동하도록 수정 (H-1). 락 순서·세마포어 계약 유지 | `brain_session.py:558-571` |
| 3 | `brain_session.py` | BE | @header changelog·description(풀 크기·충전) 갱신 | `brain_session.py:6, 45-48` |
| 4 | `test_brain.py` | BE | pool_size=2 충전·연속 checkout 웜·세마포어 상한 회귀 테스트 보강 | `test_brain.py` |

#### 3.3.2 API·데이터 모델·화면 설계

**상수 변경 (M-1 확정)**
- `[MUST]` `DEFAULT_POOL_SIZE: int = 2` (기존 `brain_session.py:46` "= 1"). 근거: 로컬 단일 사용자 데몬에서 "오픈 1개 소비 + 새대화 즉시 1개 여유" 커버. checkout 시 백그라운드 리필로 연속 새대화 대부분 웜. 3은 매 프라임=claude 프로세스(토큰·CPU) 비용 대비 과함.
- `DEFAULT_MAX_CONCURRENT_PRIME: int = 2` **유지**(`:47`). 근거: pool_size=2 충전 시 최대 2 스레드가 동시에 세마포어를 취득 → 정확히 상한과 정렬(초과 없음, H-3). 별도 상향 불요.

**충전 로직 수정 (H-1 — R-6 핵심)**

현재(`brain_session.py:558-571`):
```python
def prewarm(self, project_path):
    with self._pool_lock:
        have = len(self._pool.get(project_path, [])) + self._pool_inflight.get(project_path, 0)
        if have >= self.pool_size:
            return
        self._pool_inflight[project_path] += 1        # +1 고정
    Thread(_prime_into_pool, ...).start()             # 스레드 1개 고정
```
목표(설계):
```python
def prewarm(self, project_path):
    with self._pool_lock:
        have = len(self._pool.get(project_path, [])) + self._pool_inflight.get(project_path, 0)
        need = self.pool_size - have                  # 부족분 계산
        if need <= 0:
            return
        self._pool_inflight[project_path] = self._pool_inflight.get(project_path, 0) + need
    for _ in range(need):                             # 부족분만큼 스레드 기동
        Thread(_prime_into_pool, args=(project_path,), daemon=True).start()
```
- 불변 유지: `_prime_into_pool`(`:573-596`)은 `_prime_semaphore` 하에서 subprocess 실행 후 락 재획득 append — 무변경. 세마포어가 실제 동시 subprocess를 상한(2) 이하로 직렬화(H-3).
- `[MUST]` 락 순서 계약(`brain_session.py:6` @header): "`_lock`→`_pool_lock` 방향만 허용, 역순·세션 `_lock` 중첩 금지." — 충전 스레드 다중 기동은 `_pool_lock`만 짧게 보유(비블로킹 구간)하고 subprocess는 락 밖에서 실행하므로 계약 유지(H-2).
- 폴백 불변: 풀 empty면 `checkout_warm_handle`이 None 반환 → 기존 콜드 경로(`_get_or_create` → `session.prime()`) 유지(회귀 없음).

#### 3.3.3 환경 변경
해당 없음 (상수·로직 변경만). `console.config.json` 스키마·`prewarm_projects` 계약 불변.

#### 3.3.4 배치/마이그레이션
해당 없음. 재배포(install) 후 데몬 재기동 시 새 pool_size 적용 — lifespan prewarm이 프로젝트당 2개까지 충전.

#### 3.3.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-011 | R-6 AC (연속 새대화 웜) | 통합 테스트 | pool_size=2에서 prewarm 후 연속 checkout 2회가 모두 웜 핸들 반환 (H-1) |
| TS-012 | R-6 (풀 충전 정확성) | 기능 테스트 | 단일 prewarm 호출로 풀이 pool_size(2)까지 충전됨 |
| TS-013 | R-6 (동시성 안전) | 통합 테스트 | 동시 prewarm+checkout 반복 시 데드락·중복배정 없음 (H-2) |
| TS-014 | R-6 (세마포어 상한) | 통합 테스트 | 동시 prime subprocess ≤ DEFAULT_MAX_CONCURRENT_PRIME (H-3) |
| TS-015 | R-6 (콜드 폴백) | 기능 테스트 | 풀 empty 시 checkout None → 콜드 경로 유지 (회귀 없음) |

### F-004: 세션 계층 정리

#### 3.4.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `brain.py` | BE | `POST /query` 폐기 `new_conversation` 잔재 정리 여부 확정 — `BrainQueryRequest` 필드 존재 시 제거 또는 주석 정리(FE 미전송 확인 후) | `brain.py:221, 237-238` |
| 2 | `BrainPage.tsx` | FE | @header exports/depends에서 제거 심볼 정리(F-001에 통합 수행) | `BrainPage.tsx:6-9` |
| 3 | `opbr_adapter.py` | 공통 | **무변경** — 계약 불변 확인만(diff 0) | `opbr_adapter.py:129-154` |

#### 3.4.2 API·데이터 모델·화면 설계

- BE 엔드포인트 5종 **전부 유지**(auth/status/prime/query/job) — ANALYSIS §2.7 판정 준수. 삭제 대상 없음.
- `new_conversation` 필드: `brain.py:237-238`이 "reset 트리거 안 함(폐기)"로 이미 무력화. FE가 페이로드에서 제거(brain-new-conversation-prime.test.ts:88 "new_conversation 필드 미포함" 이미 검증)하므로 BE 모델에서도 안전 제거 가능. `BrainQueryRequest` 정의 확인 후 결정(제거 시 하위호환 영향 없음 — FE 미전송).
- `[MUST]` 유지 대상 무회귀(`opbr_adapter.py:105-107, 133`): `[ASSISTANT]` 첫 줄 마커 + `--session-id`(cold)/`--resume`(warm) 계약 훼손 금지(059, H-9).

#### 3.4.3 환경 변경
해당 없음.

#### 3.4.4 배치/마이그레이션
해당 없음.

#### 3.4.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-016 | R-7 AC (죽은 코드 제거) | 산출물 검사 | 제거 심볼(FE 헬퍼·BrainConversation) 부재, `new_conversation` 잔재 정리 |
| TS-017 | R-7 AC (유지 대상 회귀 없음) | 회귀 테스트 | 5 엔드포인트·prime/resume·5트리거리셋·[ASSISTANT] 마커 정상 (H-9~H-11) |
| TS-018 | 무상태 원칙 | 산출물 검사 | 새 파일 쓰기·DB 접근 코드 부재 (H-12) |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-003 | 1 | opal-be-agent | FE와 병렬 | BE 단독 파일(brain_session.py) |
| 1 | F-001 | 2 | opal-fe-agent | BE와 병렬 | FE 타입·헬퍼 계층 |
| 2 | F-001·F-002 | 3 | opal-fe-agent | 순차(Step 2 후) | 동일 파일 컴포넌트 계층 |
| 3 | F-001·F-002·F-004 | 4 | opal-fe-agent | 순차(Step 3 후) | FE 테스트 갱신 |
| 3 | F-003·F-004 | 5 | opal-be-agent | Step 1 후 | BE 테스트 보강 + new_conversation 정리 |
| 4 | F-004 | 6 | PM 직접 | 코드 Step 후 | docs/ 갱신 |
| 4 | (배포) | 7 | PM 직접 | 전 코드 Step 후 | install 재배포 |

### 4.2 실행 체크리스트
> 총 7개 Step | Phase 4개 | 실행 모드: 복잡

#### Step 1: BE 프라임 풀 여유 — pool_size 상향 + 충전 로직 수정
- [ ] 완료
- **소속 기능**: F-003
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `dashboard/backend/adapters/brain_session.py`
- **작업 내용**: (1) `DEFAULT_POOL_SIZE` 1→2 (`:46`). (2) `prewarm()`(`:558-571`)을 `need = pool_size - have` 만큼 충전 스레드 기동하도록 수정 — `_pool_inflight += need`, `for _ in range(need)` 스레드 기동. (3) `_prime_into_pool`·`checkout_warm_handle`·락 순서·세마포어 계약 불변. (4) @header description(풀 크기·충전)·changelog 갱신.
- **완료 기준**: 단일 `prewarm()` 호출로 풀이 pool_size까지 충전(mock subprocess). 락 순서(`_lock`→`_pool_lock`) 위반 없음. 세마포어 상한 유지. 기존 checkout/adopt 경로 무회귀.
- **테스트**: TS-011, TS-012, TS-013, TS-014, TS-015
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: FE 타입·헬퍼 계층 단순화
- [ ] 완료
- **소속 기능**: F-001, F-004
- **영역**: FE
- **agent**: opal-fe-agent
- **파일**: `dashboard/frontend/src/pages/brain/BrainPage.tsx`
- **작업 내용**: `BrainConversation`·`STORAGE_KEY`·`loadConversations`·`saveConversations`·`filterConversationsByProject`·`makeNewConversation`·`appendTurnToConversation`·`ConversationView` 제거. `addPendingTurn(turns, question)`·`resolvePendingTurn(turns, resolution)`를 `BrainTurn[]` 기반으로 리팩터. `jobResponseToResolution`/`jobPollingInterval` 시그니처 불변. (선택)`makeSessionId()` 헬퍼 추가. @header exports·depends·description 갱신.
- **완료 기준**: 타입체크·빌드 통과, 제거 심볼 참조 0, 헬퍼 turns 기반 동작.
- **테스트**: TS-002, TS-016
- **실행 방법**: sub-agent
- **의존**: 없음 (Step 1과 병렬)

#### Step 3: FE 컴포넌트 계층 — 단일 세션·레이아웃·세션 수명
- [ ] 완료
- **소속 기능**: F-001, F-002
- **영역**: FE
- **agent**: opal-fe-agent
- **파일**: `dashboard/frontend/src/pages/brain/BrainPage.tsx`
- **작업 내용**: (1) 상태모델: `allConversations`/`activeConvId`/`activeConv` → `turns`+`sessionId(useState(()=>crypto.randomUUID()))`. (2) 좌측 aside·`handleSelectConversation`·프로젝트전환 conv 재설정 effect 제거, 단일 컬럼 전체폭. (3) prime effect·status/job 폴링을 `sessionId` 기준 치환. (4) `handleNewSession`(초기화+새세션+prime), 하단 폼 버튼 주버튼화·aside +버튼 제거. (5) `capturedSessionIdRef` 오귀속 가드. (6) R-2 경량 안내 1줄(빈 상태). (7) `activeConvId===null` 게이팅 제거.
- **완료 기준**: 사이드바 DOM 부재·단일 컬럼, 재mount 새 sessionId+prime, 멀티턴 resume 유지, "새 대화" 초기화+새세션, localStorage 미기록, 안내 문구 존재.
- **테스트**: TS-001, TS-003, TS-004, TS-005, TS-006, TS-007, TS-008, TS-009
- **실행 방법**: sub-agent
- **의존**: Step 2 (동일 파일 순차)

#### Step 4: FE 테스트 갱신·정리
- [ ] 완료
- **소속 기능**: F-001, F-002, F-004
- **영역**: FE
- **agent**: opal-fe-agent
- **파일**: `brain-storage.test.ts`, `brain-new-conversation-prime.test.ts` (brain-status.test.ts·brain-job-polling.test.ts는 회귀 확인만)
- **작업 내용**: `brain-storage.test.ts` — localStorage/멀티대화/filter/makeNewConversation/appendTurnToConversation 테스트 삭제, `addPendingTurn`/`resolvePendingTurn` turns 기반 시그니처로 재작성. `brain-new-conversation-prime.test.ts` — `makeNewConversation`→`makeSessionId`/인라인 치환, prime·query 페이로드(session_id) 테스트 유지, per-conv 독립성 테스트를 "새 대화=새 sessionId" 로 조정. `brain-status.test.ts`·`brain-job-polling.test.ts` 변경 없이 통과 확인.
- **완료 기준**: `npm test`(vitest) 전체 통과, 제거 심볼 import 0.
- **테스트**: TS-002, TS-010, TS-016 (단위 회귀)
- **실행 방법**: sub-agent
- **의존**: Step 3

#### Step 5: BE 테스트 보강 + new_conversation 잔재 정리
- [ ] 완료
- **소속 기능**: F-003, F-004
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `dashboard/backend/tests/test_brain.py`, `dashboard/backend/routers/brain.py`(+`models.py` 확인)
- **작업 내용**: (1) test_brain.py에 pool_size=2 충전·연속 checkout 웜·세마포어 상한·콜드 폴백 회귀 테스트 보강. (2) `BrainQueryRequest.new_conversation` 필드 존재·사용 여부 확인 후 안전 제거(FE 미전송 확인 시) 또는 폐기 주석 정리. (3) 기존 test_brain.py 회귀 통과 확인.
- **완료 기준**: `pytest dashboard/backend/tests/test_brain.py` 통과, 5 엔드포인트·prime/resume·5트리거리셋 회귀 없음.
- **테스트**: TS-011~TS-015, TS-017, TS-018
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 6: docs/ 갱신
- [ ] 완료
- **소속 기능**: F-004
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/ARCHITECTURE.md`
- **작업 내용**: §OPAL Console 프로젝트 브레인 절 — "이력" 행(`ARCHITECTURE.md:264`)을 localStorage 영속 → **휘발성 단일 세션(미영속)**으로 갱신, "프라임 연결 풀" 행(`:262`)의 풀 크기 1→2 + 충전 동작 반영, 세션 행(`:261`) 멀티대화 뉘앙스 정리. 변경이력 행 추가(Task 063).
- **완료 기준**: ARCHITECTURE.md가 휘발성 단일 세션·pool_size=2 현행 코드와 정합.
- **테스트**: 문서 검토 (PM Gate)
- **실행 방법**: direct
- **의존**: Step 1~5

#### Step 7: FE+BE 동시 재배포 (install)
- [ ] 완료
- **소속 기능**: (배포)
- **영역**: 환경
- **agent**: PM 직접
- **파일**: `./scripts/install-mac.sh` 실행 (dashboard/ 소스 → `~/.opal/dashboard-server/`)
- **작업 내용**: `[MUST]` 배포 경계 준수 — `~/.opal/` 직접 편집 금지, dashboard/ 소스 수정분을 install로 재배포(M-6 확정, FE+BE 동시). BE 변경이 pool_size 상수·충전 로직 수준이라 호환성 이슈 없음.
- **완료 기준**: install 성공, 데몬 재기동 후 브레인 화면 단일 세션·pool_size=2 반영.
- **테스트**: 배포 후 스모크 (TEST 단계 E2E)
- **실행 방법**: direct
- **의존**: Step 1~6

### 4.3 병렬/순차 판별 근거
| 관계 | 근거 |
|------|------|
| Step 1 ∥ Step 2 | BE(brain_session.py) ↔ FE(BrainPage.tsx) 독립 파일·독립 기능 |
| Step 2 → Step 3 | 동일 파일(BrainPage.tsx) 순차 수정 — 타입·헬퍼 → 컴포넌트 |
| Step 3 → Step 4 | 컴포넌트 확정 후 테스트 갱신 |
| Step 1 → Step 5 | pool 로직 확정 후 BE 테스트 보강 |
| Step 4·5 → Step 6 | 코드 확정 후 문서 정합 |
| Step 1~6 → Step 7 | 전 변경 완료 후 배포 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA
| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | 단일 대화창 렌더 (사이드바 부재) | TS-001 | aside·ConversationView DOM 없음, 단일 컬럼 |
| F-001 | 멀티관리·localStorage 심볼 제거 | TS-002 | 제거 심볼 참조 0, 빌드 통과 |
| F-001 | 이력 비영속 (재오픈 백지) | TS-003, TS-004 | localStorage 브레인 키 미기록, 재mount turns=[] |
| F-001 | 비영속 안내 문구 | TS-005 | 빈 상태에 안내 1줄 |
| F-002 | 오픈마다 새 세션 + 자동 prime | TS-006 | 재mount 새 sessionId·prime 호출 |
| F-002 | 세션 내 멀티턴 resume | TS-007, TS-010 | 2턴 이어짐, --resume 경로·계약 불변 |
| F-002 | "새 대화" 초기화+새세션+ready | TS-008 | turns=[], 새 sessionId, prime 재호출 |
| F-002 | 세션 전환 오귀속 가드 | TS-009 | pending 중 새 대화 → 새 세션 미오염 |
| F-003 | 풀 충전 pool_size까지 | TS-011, TS-012 | 단일 prewarm으로 풀 2개 충전 |
| F-003 | 연속 새대화 웜 배정 | TS-011 | 연속 checkout 2회 모두 웜 |
| F-003 | 동시성·세마포어 안전 | TS-013, TS-014 | 데드락·중복배정 없음, 동시 prime ≤2 |
| F-003 | 콜드 폴백 회귀 없음 | TS-015 | 풀 empty 시 콜드 경로 유지 |
| F-004 | 죽은 코드 제거 | TS-016 | 제거 심볼·new_conversation 잔재 정리 |
| F-004 | 유지 대상 무회귀 | TS-017 | 5 엔드포인트·리셋·마커 정상 |
| F-004 | 무상태 원칙 준수 | TS-018 | 파일/DB 영속 코드 부재 |

### 5.2 회귀 테스트
- [ ] `brain-status.test.ts`(canSubmit 게이팅) 무변경 통과 (H-8)
- [ ] `brain-job-polling.test.ts`(jobResponseToResolution·jobPollingInterval·resolvePendingTurn) 통과 (H-8)
- [ ] BE 5 엔드포인트(auth/status/prime/query/job) 계약·응답 스키마 불변
- [ ] prime/resume 콜드·웜 분기, 5트리거 리셋(turn≥20·유휴30분·크래시·수동) 유지 (H-11)
- [ ] `opbr_adapter.py` diff 0 — `[ASSISTANT]` 마커·`--session-id`/`--resume` 불변 (H-9)
- [ ] 062 //opbr query 6단계 워크플로우 답변·인용 정상 (H-10)

### 5.3 코드/문서 품질
- [ ] BrainPage.tsx·brain_session.py @header 갱신 (exports/depends/description/changelog)
- [ ] ARCHITECTURE.md §OPAL Console 현행 정합 (Step 6)
- [ ] 프로젝트 컨벤션 준수 (Python snake_case, FE camelCase, 파일 kebab/snake)
- [ ] 변경이력·changelog 일시(KST) 기록

### 5.4 보안
- [ ] `.env`·인증 파일 .gitignore 포함 확인 (변경 없음)
- [ ] 하드코딩 토큰/시크릿 없음
- [ ] LLM 호출 brain 라우터 격리 유지 — 설정·FE 등 신규 LLM 경로 추가 없음 (`brain.py:6` @header)
- [ ] subprocess `shell=False` 유지 (`opbr_adapter.py:174`, 셸 인젝션 방지 H-13)
- [ ] 데몬 127.0.0.1 바인딩 불변 (외부 노출 금지)

---

## 6. 복잡도 판별
| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 7개 | 복잡 |
| 변경 파일 수 | 6개 (BrainPage.tsx, brain_session.py, brain.py, test_brain.py, 2 FE 테스트, ARCHITECTURE.md) | 복잡 |
| 모듈 범위 | 다중 (FE + BE + 문서) | 복잡 |
| 작업 유형 | 대규모 개선(상태모델 리팩터 + 풀 로직 변경) | 복잡 |
| 외부 의존성 | 없음 (신규 패키지·API·도구 없음) | 단순 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지
```
Batch 1 (병렬):
  ├─ opal-be-agent  : Step 1 (brain_session.py 풀)
  └─ opal-fe-agent  : Step 2 (BrainPage.tsx 타입·헬퍼)
Batch 2 (순차):
  └─ opal-fe-agent  : Step 3 (BrainPage.tsx 컴포넌트)   ← Step 2 후
Batch 3 (병렬):
  ├─ opal-fe-agent  : Step 4 (FE 테스트)                 ← Step 3 후
  └─ opal-be-agent  : Step 5 (BE 테스트 + 정리)          ← Step 1 후
Batch 4 (순차):
  ├─ PM 직접        : Step 6 (docs/ARCHITECTURE.md)
  └─ PM 직접        : Step 7 (install 재배포)
```
**그룹핑 근거**: 파일 충돌 방지 — BrainPage.tsx 수정 Step(2,3,4의 소스분)은 동일 에이전트(opal-fe-agent)에 직렬 배치. brain_session.py·test_brain.py는 opal-be-agent. FE/BE는 파일 무겹침 → Batch 1 병렬.

### C-2. 스킬 요구사항
- FE: `op-dev-execute` + `vercel-labs/react-best-practices`(상태 최소화·불필요 리렌더 방지), `ui-designer`(단일 컬럼 detail 레이아웃) 참조. 기존 shadcn 컴포넌트 재사용 — 신규 스킬 갭 없음.
- BE: `op-dev-execute` + `trailofbits/modern-python`(threading·타입) 참조. 기존 풀 관용구(락 순서·세마포어) 준수.
- 갭 판별: 3개 이상 Step 공통 신규 패턴 없음 → 인라인 지침으로 충분(신규 스킬 불요).

### C-3. 도구 요구사항
- CLI: `npm test`(vitest, FE), `pytest`(BE), `./scripts/install-mac.sh`(배포). 신규 설치 없음.
- MCP: 불요 (신규 외부 라이브러리 API 없음 — context7/shadcn MCP 미사용).

### C-4. 테스트 전략 (opal-test-agent 실행 계획)
- **기능 테스트**: FE `vitest`(brain-*.test.ts) — TS-001~010, 016. BE `pytest dashboard/backend/tests/test_brain.py` — TS-011~015, 017, 018.
- **회귀 테스트**: FE 전체 vitest 스위트, BE `test_brain.py`+`test_brain_spike.py`. opbr_adapter.py diff 0 정적 확인.
- **통합/E2E**: 멀티턴 이어묻기(TS-007)·연속 새대화 웜(TS-011)·mount 새세션(TS-006)은 prewarm-enabled 프로젝트 대상 E2E(playwright)로 TEST 단계 검증.
- **코드 품질**: FE 타입체크(tsc)·lint, BE ruff.
- **보안**: 하드코딩 시크릿 스캔, 127.0.0.1 바인딩·shell=False·LLM 라우터 격리 확인.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| FE | React 19 + TypeScript 5 + Vite + Tailwind + shadcn/ui + TanStack Query 5 | vercel-labs/react-best-practices, ui-designer |
| BE | Python 3.10+ + FastAPI + uvicorn + threading/subprocess(stdlib) | trailofbits/modern-python |
| CLI | claude (Claude Code CLI) headless `-p` | (opbr_adapter 계약 불변) |

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| (미사용) | 신규 외부 라이브러리 API 없음 — 기존 코드 분석·설계로 충분 |

### 8.3 참조 문서 (설계 결정 근거)
| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | BrainPage(FE) | `dashboard/frontend/src/pages/brain/BrainPage.tsx` | 멀티대화·localStorage 제거, 단일 세션 설계 근거 |
| D-2 | 소스 | brain_session(BE) | `dashboard/backend/adapters/brain_session.py` | pool_size 상향·prewarm 충전 로직·락/세마포어 계약 |
| D-3 | 소스 | brain 라우터(BE) | `dashboard/backend/routers/brain.py` | 5 엔드포인트 유지·new_conversation 정리 |
| D-4 | 소스 | opbr 어댑터(BE) | `dashboard/backend/adapters/opbr_adapter.py` | [ASSISTANT]·--session-id/--resume 계약 불변 확인 |
| D-5 | 소스 | main lifespan(BE) | `dashboard/backend/main.py` | prewarm 트리거 진입점(프로젝트당 1회) — H-1 근거 |
| D-6 | 소스 | config 라우터(BE) | `dashboard/backend/routers/config.py` | prewarm 토글·풀 opt-in 모델 |
| D-7 | 설계 | 아키텍처 | `docs/ARCHITECTURE.md` §OPAL Console | 브레인 이력·프라임 풀 현행 서술(갱신 대상) |
| D-8 | 기획 | 프로젝트 정의 | `docs/PROJECT.md` §OPAL Console | 콘솔 화면·배포 경계 |
| D-9 | 설계 | 코드 컨벤션 | `docs/CONVENTIONS.md` | @header·배포 경계·네이밍 [MUST] |
| D-10 | 소스 | FE 테스트 | `dashboard/frontend/src/pages/brain/*.test.ts` | 테스트 갱신·유지 대상 판정 |
| D-11 | 참고 | 과거 태스크 060 | `tasks/060-260713-opd-브레인-프라임-연결풀/` | 프라임 풀(prewarm/checkout/adopt) 설계 SSOT |

---

## 9. 리스크 및 대응 (기능-리스크 연결)
| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-61 | pool_size만 상향하고 prewarm 충전 미수정 시 R-6 미충족(풀 최대 1) | F-003 | 높음 | prewarm `need=pool_size-have` 충전 필수 (§3 F-003, H-1). TS-011/012로 강제 검증 |
| R-62 | 충전 다중 스레드 기동 시 락 순서/세마포어 위반 | F-003 | 높음 | `_pool_lock` 짧게 보유·subprocess 락 밖, 세마포어 상한 유지 (H-2, H-3). TS-013/014 |
| R-63 | R-6 웜 효과가 prewarm-enabled(설정 토글 ON) 프로젝트에 한정 (060 opt-in 모델) | F-003 | 중 | 범위 유지(opt-in 모델 미변경 — 스코프 크립 금지). TEST는 prewarm-enabled 프로젝트로 수행. 미등재 프로젝트는 콜드 폴백(회귀 아님) — 완료기준④ 검증 전제로 명시 |
| R-64 | turns[] 리팩터 후 멀티턴 resume·오귀속 가드 회귀 | F-002 | 높음 | capturedSessionIdRef 가드(H-6), --resume 경로 FE 무변경(H-4). TS-007/009 |
| R-65 | 상태모델 교체 중 status/job 폴링 queryKey 회귀 | F-001/002 | 중 | sessionId 상시 non-null·queryKey 치환, brain-job-polling.test.ts 회귀 확인(H-8) |
| R-66 | 정리 중 유지 대상(엔드포인트·마커·062) 훼손 | F-004 | 높음 | opbr_adapter.py diff 0, 5 엔드포인트 유지, 회귀 스위트(H-9~H-11). TS-017 |
| R-67 | 배포 경계 위반(~/.opal 직접 편집) | (배포) | 중 | [MUST] dashboard/ 소스만 수정 후 install (M-6). Step 7 |
| R-68 | 용어 일관성 — FE `session_id`(페이로드) ↔ FE 내부 `sessionId`(camelCase) | F-002 | 저 | 페이로드 키는 `session_id` 유지(BE 계약), FE 변수만 camelCase — 직렬화 지점에서 명시 매핑. 불일치 아님(의도적 경계) |

> §7.1 영역 간 용어 검토: FE↔BE 공유 계약 필드는 `session_id`(스네이크, 페이로드)로 통일 유지 — FE 내부 변수 `sessionId`(camelCase)는 컨벤션상 정상이며 직렬화 시 `session_id`로 매핑(`BrainPage.tsx:469-473, 531-535`). 신규 용어 불일치 없음 — decision_required 에스컬레이션 대상 없음.
