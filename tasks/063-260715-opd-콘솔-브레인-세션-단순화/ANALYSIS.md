# ANALYSIS: 콘솔 프로젝트 브레인 — 휘발성 단일 세션 + 진입/새대화 즉시 워밍

> 작성일: 2026-07-15
> 입력: TASK.md
> 출력: ANALYSIS.md

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | BrainPage(FE) | `dashboard/frontend/src/pages/brain/BrainPage.tsx` | 멀티대화관리·localStorage 이력 제거 대상 식별 |
| D-2 | 소스 | brain_session(BE) | `dashboard/backend/adapters/brain_session.py` | 세션 계층·프라임 풀·pool_size 분석 |
| D-3 | 소스 | brain 라우터(BE) | `dashboard/backend/routers/brain.py` | 엔드포인트 정리 범위 판단 |
| D-4 | 소스 | opbr 어댑터(BE) | `dashboard/backend/adapters/opbr_adapter.py` | claude 호출 계약(resume/session-id) 확인 |
| D-5 | 설계 | 아키텍처 | `docs/ARCHITECTURE.md` | 콘솔 구조·배포 모델·2-tier 부트스트랩 |
| D-6 | 기획 | 프로젝트 정의 | `docs/PROJECT.md` | 콘솔 컴포넌트·화면·배포 경계 |

---

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| BrainPage.tsx | 멀티대화 UI + localStorage | ✅ 제거/단순화 | 111(STORAGE_KEY), 125-133(save), 254-278(filterConversationsByProject), 438-443(allConversations), 658-682(handleNewConversation), 771-814(aside) |
| brain_session.py | 대화별 세션 레지스트리 | ⚠️ 유지 | 60-495(ConversationBrainSession), 499-720(BrainSessionRegistry) |
| brain.py | 5개 엔드포인트 | ⚠️ 선별 유지 | 91-115(auth), 120-153(status), 158-197(prime), 210-258(query), 263-297(job) |
| opbr_adapter.py | claude 호출 계약 | ⚠️ 유지 불변 | 93-227(prime_and_ask), 133([ASSISTANT] 마커) |

### 1.2 아키텍처 패턴

**FE 멀티대화 관리**: BrainConversation[] 배열 (localStorage) → filterConversationsByProject로 프로젝트별 필터링 (D-1:254-259)

**BE 세션 격리**: 각 session_id마다 ConversationBrainSession 인스턴스 독립 관리 (D-2:60-495). 하나의 세션이 cold/warm 경로 모두 지원.

**공유 계약**: FE가 생성한 session_id(UUID) → BE가 reception-only로 사용. BE가 별도 claude_session_id 발급.

### 1.3 의존성 맵

```
FE: BrainPage.tsx
  ├─ api-client (HTTP)
  └─ TanStack Query (폴링·캐시)

BE: routers/brain.py
  ├─ brain_session_registry (세션)
  ├─ opbr_adapter (claude 호출)
  └─ config (프로젝트 스캔)

BE: brain_session.py
  └─ opbr_adapter (prime_and_ask)

localStorage: STORAGE_KEY "opal-console:brain:conversations" (D-1:111)
  ├─ loadConversations (D-1:113-123)
  └─ saveConversations (D-1:125-133)
```

### 1.4 테스트 현황

FE/BE 테스트 파일 존재 (경로: `dashboard/frontend/src/pages/brain/*.test.ts`, `dashboard/backend/tests/test_brain*.py`) — 분석 범위 외, PLAN에서 갱신 대상.

---

## 2. 영향 범위

### 2.1 R-1 단일 대화창 — 멀티 관리 UI 제거

**제거 대상**:
- `BrainPage.tsx` 좌측 aside (771-814): ConversationView 컴포넌트 + 대화 목록
- `filterConversationsByProject()` (254-259): 프로젝트별 필터링
- `handleSelectConversation()` (684-700): 대화 선택 핸들러
- `ConversationView` 컴포넌트 (384-422)

**영향**: `activeConvId` 상태는 유지하되, mount 시 null → 새 conversation 자동 생성으로 전환.

### 2.2 R-2 이력 비영속 — localStorage 제거

**제거 대상**:
- `STORAGE_KEY` (111)
- `loadConversations()` (113-123)
- `saveConversations()` (125-133)
- 모든 호출: handleSubmit (649), handleNewConversation (667), jobData useEffect (622)

**영향**: turns 배열 메모리만 유지 → 새로고침/재오픈 시 백지.

### 2.3 R-3 오픈마다 새 세션

**FE**: mount 시 `makeNewConversation(project)` → 새 session_id + 즉시 prime (569-576)

**BE**: `_get_or_create()` (526-554) → 신규 세션 생성 → pool checkout → `adopt_warm_handle()` (245-266) 호출로 즉시 웜.

### 2.4 R-4 세션 내 멀티턴 (유지)

**유지 대상**: `ask()` 콜드/웜 분기 (D-2:269-304), `--resume` 경로 (D-4:149-154), warm_ask에서 turn_count++ (D-2:376-389).

### 2.5 R-5 "새 대화" 버튼

**현재**: handleNewConversation (658-682) — 새 conversation + prime

**변경**: localStorage 저장 제거, "새 대화" 버튼 위치 이동 (좌측→하단 폼).

### 2.6 R-6 프라임 풀 여유

**조정**: DEFAULT_POOL_SIZE (46) 1→? (PLAN에서 결정). prewarm/checkout_warm_handle 흐름 (558-616) 유지.

### 2.7 R-7 세션 계층 정리

**BE 엔드포인트 판정**: 5개 모두 필수 유지.
- auth (91-115): 인증 체크
- status (120-153): prime 완료 감지
- prime (158-197): 워밍 트리거
- query (210-258): 핵심 기능
- job (263-297): 결과 수신

**삭제 대상**: 없음. (FE R-1은 UI만 제거, BE 로직은 단일 session_id 설계로 이미 멀티대화 미지원)

---

## 3. 핵심 발견 사항

**F-1**: R-1 "단일 대화창"로 BrainConversation[] 오버헤드 제거 → currentTurns: BrainTurn[]로 단순화 (D-1:438-443, 496-506)

**F-2**: FE makeNewConversation에서 id + session_id 이중 발급 → 불필요 가능성 (D-1:262-272). PLAN에서 검토.

**F-3**: R-3 mount마다 새 session_id + pool 자동 웜 이식 메커니즘 (D-2:526-554, 245-266, 598-616).

**F-4**: opbr_adapter [ASSISTANT] 마커는 headless 호출을 비서 tier로 캡하여 PM tier 승격 방지 (D-4:105-107, 133). 계약 유지 필수.

**F-5**: _cold_prime_with_retry 매 호출마다 새 uuid4 발급 → 충돌 방지 (D-2:306-339).

**F-6**: 비동기 잡 폴링 단일 슬롯 설계 (_current_job 1개) — R-1 후 문제 자체 해소 (D-1:612-630).

---

## 4. 제약/리스크

### 4.1 유지 대상 회귀 위험

| 항목 | 제약 | 근거 |
|------|------|------|
| **prime/resume** | 콜드(--session-id) + 웜(--resume) 분기 유지 | D-2:269-304, D-4:149-154. "빠름" 근거. |
| **멀티턴** | turn_count++ + 웜 재개 로직 불변 | D-2:376-389. 이어묻기 기초. |
| **status/job 폴링** | GET /api/brain/status, GET /api/brain/job 유지 | D-3:120-153, 263-297. 진입/워밍 감지·결과 수신 필수. |
| **프라임 풀 리필** | 락 미보유 subprocess + 재획득 (R1 H-1) | D-2:573-596. 동시성 보호. |
| **5트리거 리셋** | 서버재시작/turn≥20/유휴30분/크래시/수동 모두 유지 | D-2:169-199. 세션 누적 상한. |
| **[ASSISTANT] 마커** | headless tier 캡 유지 | D-4:105-107, D-5:66. PM tier 오염 방지. |
| **062 6단계 워크플로우** | opbr query 답변 생성 불변 | TASK.md 제약. 멀티턴 전제. |

### 4.2 식별된 리스크

| # | 리스크 | 영향 | 심각도 | 근거 |
|---|--------|------|--------|------|
| R-1 | R-1 제거로 대화 목록 UI 소실 | turns 확인 경로 재설계 필요 | 중 | D-1:384-422 |
| R-2 | localStorage 제거 후 새로고침 시 손실 | 의도된 동작이나 안내 필요 | 중 | D-1:111, 438-440 |
| R-3 | mount마다 새 세션 → 문맥 단절 | 장시간 대화 후 손실 가능 | 중 | 의도된 동작 |
| R-5 | "새 대화" 버튼 위치 이동 | 발견성 감소 가능 | 저 | D-1:781-785 |
| R-6 | pool_size 상향 시 리소스 비용 증가 | 네트워크·API 비용 검토 필요 | 중 | D-2:46-47 |

---

## 5. 기술 컨텍스트

### 5.1 기술 스택

| 카테고리 | 기술 | 버전 |
|----------|------|------|
| FE 언어 | TypeScript | 5.x |
| FE 프레임워크 | React | 19.x |
| FE 빌드 | Vite | 최신 |
| FE UI | shadcn/ui + Tailwind | 최신 |
| FE 상태 | TanStack Query | 5.x |
| BE 언어 | Python | 3.10+ |
| BE 프레임워크 | FastAPI | 0.100+ |
| BE 서버 | uvicorn | 0.20+ |
| BE 동시성 | threading (stdlib) | 내장 |
| CLI 호출 | subprocess (stdlib) | 내장 |
| 외부 CLI | claude (Claude Code CLI) | v1.0+ |

### 5.2 추천 스킬

| 스킬 | 용도 |
|------|------|
| op-dev-plan | PLAN 단계 설계 |
| opal-fe-agent | EXECUTE 단계 FE 구현 |
| opal-be-agent | EXECUTE 단계 BE 구현 |

### 5.3 추천 MCP

| MCP | 용도 |
|-----|------|
| (신규 외부 의존 없음) | 코드 분석·설계만으로 충분 |

---

## 6. PLAN에서 결정할 미확정 사항

1. **pool_size 최종 수치** — 현재 1, 후보 2~3
2. **R-1 화면 레이아웃** — 좌측 사이드바 제거 후 공간 활용
3. **"새 대화" 버튼 위치·스타일** — 발견성 보장
4. **R-2 사용자 안내 메시지** — turns 손실 명시
5. **테스트 전략** — 기존 테스트 갱신 vs 신규 추가
6. **배포 순서** — FE + BE 동시 vs 단계적

---

## 변경이력

| 버전 | 작성일 | 변경 내용 |
|------|--------|----------|
| v1.0 | 2026-07-15 | 초기 작성 — R-1~R-7 요구사항 코드 기반 분석 + 영향 범위 매핑 + 핵심 발견 6개 + 회귀 리스크 정리 |
