# TASK: 콘솔 프로젝트 브레인 — 휘발성 단일 세션 + 진입/새대화 즉시 워밍

> 작성일: 2026-07-15 | 작업 유형: 개선 | 적용 스킬: opd | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

콘솔 프로젝트 브레인을 "멀티 대화 관리 + 이력 영속(localStorage)" 구조에서 **"휘발성 단일 세션 + 진입/새대화 시 즉시 워밍"** 구조로 단순화한다. 여러 대화 스레드 관리 UI와 이력 저장을 제거하고, 세션 수명을 "메뉴 오픈 ~ (재오픈 또는 새 대화)"로 통일하되, 프라임 풀 여유로 첫 질문부터 빠르게 응답한다.

## 배경

캡틴의 최초 문제 제기는 "콘솔 브레인 대화가 브라우저 콘솔에 쌓여 다른 브라우저에서 열면 새로운 것이라 공유가 안 된다"였다. 원인 진단 결과, 대화 이력이 브라우저 `localStorage`에만 저장(`BrainPage.tsx:111` — `opal-console:brain:conversations`)되어 브라우저·기기별로 격리되기 때문이었다.

논의 과정에서 방향이 두 번 전환되었다:
1. (검토·폐기) 이력을 서버(`~/.opal/console/`)로 영속화 → 캡틴은 오히려 **매번 백지**를 선호.
2. (검토·폐기) one-shot 전환(세션 제거) → 캡틴의 "진입마다 빠르게" 요구와 **모순**(one-shot은 매번 콜드라 느림).
3. (확정) **휘발성 단일 세션 + 진입/새대화 즉시 워밍** — 이력·멀티대화관리는 걷어내되, 세션 계층(prime/resume/멀티턴)은 "빠름"을 위해 유지.

무거움의 실체는 두 축으로 분리된다: (A) 멀티 대화 관리 + 이력 영속(제거 대상), (B) 세션 웜 유지 인프라(유지 대상 — 빠름의 근거). 이 태스크는 (A)만 제거하고 (B)는 유지·조정한다.

## 배경 분석 (대화에서 도출)

현재 콘솔 브레인 구조 (읽기 분석 결과):

| 계층 | 현재 상태 | 근거 |
|------|----------|------|
| 대화 이력 | 브라우저 `localStorage` 단일 키에만 저장. 최대 50개 대화 배열. 프로젝트별 필터링 | `BrainPage.tsx:111,125-133`, `filterConversationsByProject` |
| 멀티 대화 UI | 좌측 사이드바에 대화 목록, 대화 선택·"새 대화" 다중 생성, 활성 대화 전환 | `BrainPage.tsx:771-814` (aside), `handleNewConversation`/`handleSelectConversation` |
| 세션 정체성 | 2-ID 분리: `session_id`(FE UUID, 대화 정체성) vs `_claude_session_id`(BE 발급, claude CLI 핸들) | `brain_session.py:67-72` |
| BE 세션 저장 | in-memory only. `[MUST] backend 무상태 — Q&A·세션 파일 영속 금지`. 서버 재시작 시 소멸 | `brain_session.py` @header |
| 멀티턴 | `--resume <claude_session_id>`로 웜 재개 → 대화 컨텍스트 유지 | `opbr_adapter.py:149-154` |
| 5트리거 리셋 | ⓐ서버재시작 ⓑturn≥20 ⓒ유휴30분 ⓓ크래시 ⓔ수동 | `brain_session.py:38-39,272-278` |
| 프라임 풀 | `DEFAULT_POOL_SIZE=1`(프로젝트당 1개). prewarm/checkout/adopt (060) | `brain_session.py:46,558-616` |
| 레이턴시 실측 | 웜 ~9.6s / 콜드 ~26~69s (060·037 히스토리) | MEMORY 히스토리, `follow-up-brain-query-lite.md` |

세션 관련 코드 규모: `brain_session.py` 719줄 + `routers/brain.py` 297줄 + FE 세션로직 ~127줄.

## 확정된 설계 방향 (대화에서 합의)

캡틴이 최종 확정한 5가지 요구:

1. **단일 대화창** — 여러 대화 스레드를 만들어 목록에서 고르는 멀티 관리 UI는 두지 않는다.
2. **휘발성 + 오픈마다 새 세션** — 메뉴 진입 때마다 새 세션으로 시작하고, 기존 대화 내역은 저장·표시하지 않는다(브라우저/기기 간 불일치는 이제 "버그"가 아니라 의도된 동작).
3. **세션 내 멀티턴 유지** — 한 번 오픈한 세션은 (재오픈 또는 "새 대화") 전까지 동일 세션에서 이어묻기가 가능하다.
4. **"새 대화" 버튼** — 수동으로 세션을 초기화한다. 동작은 메뉴 재오픈과 동일 = 내역 초기화 + 새 세션 발급 + 즉시 대화 가능.
5. **프라임 풀 여유** — 오픈/새대화 시 콜드로 떨어지지 않도록 웜 핸들을 즉시 배정할 수 있어야 한다(현재 pool_size=1은 연속 새대화에 부족).

## 명확화 결과

> TASK 4요소를 잠근다. 각 요소는 확정값 또는 명시적 "N/A: <사유>"로 채운다.

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | 콘솔 브레인을 "휘발성 단일 세션 + 진입/새대화 즉시 워밍" 구조로 단순화. 멀티대화관리·이력영속 제거, 세션 계층(prime/resume/멀티턴) 유지 | - | `BrainPage.tsx`, `brain_session.py`, `routers/brain.py` |
| 범위 | **포함**: FE 멀티대화관리 UI·localStorage 이력 제거, 단일 대화창, mount마다 새 세션, "새 대화" 버튼(초기화+새세션+즉시ready), BE 프라임 풀 pool_size 상향. **제외**: 이력 서버 영속화, one-shot 전환, 062 워크플로우 변경, 원격(타 기기) 세션 재연결 | pool_size 최종 수치는 PLAN에서 리소스↔응답성으로 확정 | `brain_session.py:46` |
| 제약 | 세션 계층(prime/resume/멀티턴) 유지. BE 무상태 원칙 유지(대화 파일 영속 금지). 062 6단계 워크플로우 불변. 배포 경계(프로젝트 소스 수정→install). 059 `[ASSISTANT]` 캡·`--session-id` 호출 방식 유지 | - | `brain_session.py` @header, PROJECT.md 배포 경계 |
| 완료기준 | ①메뉴 오픈 시 이력 없이 새 세션 즉시 대화 가능 ②세션 내 멀티턴 이어짐 ③"새 대화"=초기화+새세션+즉시ready ④연속 새대화에도 콜드 폴백 없이 웜 배정 ⑤재오픈/타 브라우저 시 백지(의도된 동작) | - | - |

## 요구사항

- [ ] **R-1 단일 대화창** — 좌측 대화 이력 사이드바, 대화 목록·선택, 다중 대화 배열(`BrainConversation[]`)·프로젝트 필터를 제거한다. 화면은 단일 대화창 하나만 렌더한다. (AC: 대화 목록 사이드바 DOM 부재, `loadConversations`/`filterConversationsByProject` 등 멀티관리 심볼이 UI 경로에서 제거됨)
- [ ] **R-2 이력 비영속** — `localStorage` 이력 저장/로드(`opal-console:brain:conversations`)를 제거한다. 새로고침·재오픈·타 브라우저 접속 시 대화가 백지로 시작된다. (AC: localStorage에 대화 키가 쓰이지 않음, 재오픈 시 turns 빈 상태)
- [ ] **R-3 오픈마다 새 세션** — 브레인 메뉴 mount 시 새 `session_id`를 발급하고 즉시 prime한다. (AC: 메뉴 재진입마다 새 session_id, 진입 직후 자동 prime 트리거)
- [ ] **R-4 세션 내 멀티턴 유지** — 한 세션(오픈~새대화/재오픈 전) 동안 연속 질문이 `--resume`으로 이어진다. (AC: 같은 세션에서 2턴 이상 질의 시 이전 맥락이 이어짐 — TEST에서 검증)
- [ ] **R-5 "새 대화" 버튼** — 클릭 시 현재 대화 내역 초기화 + 새 session_id 발급 + 즉시 대화 가능(웜). 메뉴 재오픈과 동일 동작. (AC: 클릭 후 turns 초기화, 새 session_id, 곧바로 질의 가능 상태로 전이)
- [ ] **R-6 프라임 풀 여유** — `DEFAULT_POOL_SIZE`를 상향하여 오픈/새대화 연속 시에도 웜 핸들 즉시 배정. 정확한 수치는 PLAN 확정. (AC: 연속 새대화 N회에도 콜드 폴백 없이 ready 전이 — TEST에서 검증)
- [ ] **R-7 세션 계층 정리** — R-1~R-2로 불필요해진 BE 엔드포인트/코드(멀티대화 전제 로직)를 식별해 정리하되, prime/resume/status/job/멀티턴은 유지한다. 정리 범위는 PLAN에서 확정. (AC: 죽은 코드 제거, 유지 대상 회귀 없음)
- [ ] **R-8 이탈 가드 (추가작업 — 캡틴 요구, 2026-07-15)** — 브레인 화면에서 진행 중 대화(`turns.length > 0`)가 있을 때, 세션이 소멸되는 이탈 경로에서 "화면을 나가면 대화 세션이 사라집니다. 나가시겠어요?" 확인 다이얼로그를 띄운다. 경로 4종: ①콘솔 메뉴 전환(React Router `useBlocker`) ②프로젝트 스위처 변경(`contextProject`) ③브라우저 새로고침·탭 닫기(`beforeunload`) ④"새 대화" 버튼 클릭(같은 화면 내 세션 교체 — 캡틴 추가 요구 2026-07-15). (AC: turns>0 + 각 경로 시도 시 확인 다이얼로그 노출 → "취소" 시 잔류·세션 유지, "확인/나가기" 시 진행(①②③은 이탈, ④는 `handleNewSession` 실행). turns=0이면 경고 없이 즉시 진행. ③은 브라우저 기본 다이얼로그 허용(커스텀 문구 불가). ④는 다른 3경로와 동일 `AlertDialog` 재사용)

## 제약 조건

- **세션 계층 유지**: prime·resume·status 폴링·잡 폴링·멀티턴은 "빠름·이어묻기"의 근거이므로 제거하지 않는다.
- **BE 무상태 원칙**: 대화 Q&A·세션 핸들의 파일/DB 영속을 새로 도입하지 않는다(`brain_session.py` @header [MUST]).
- **062 불변**: `//opbr query`의 content-driven 6단계 워크플로우는 멀티턴 전제라 그대로 유지한다.
- **배포 경계**: `~/.opal/` 직접 편집 금지. `dashboard/` 소스 수정 후 install로 재배포.
- **059 호출 방식 유지**: `[ASSISTANT]` 마커 캡 + `--session-id`/`--resume` claude 호출 계약 불변.
- **자원 상한**: pool_size 상향 시 동시 프라임 상한(`DEFAULT_MAX_CONCURRENT_PRIME`)·CPU/토큰 비용을 고려한다.

## 기술 스택

- **Console FE**: React, TypeScript, Vite, Tailwind, shadcn/ui, TanStack Query (`dashboard/frontend/`)
- **Console BE**: Python, FastAPI, uvicorn (`dashboard/backend/`)
- **브레인 질의**: claude CLI headless(`claude -p`), opbr 스킬, brain-tool

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | BrainPage(FE) | `dashboard/frontend/src/pages/brain/BrainPage.tsx` | 멀티대화관리·localStorage 이력 제거 대상 |
| D-2 | 소스 | brain_session(BE) | `dashboard/backend/adapters/brain_session.py` | 세션 계층·프라임 풀 pool_size 조정 대상 |
| D-3 | 소스 | brain 라우터(BE) | `dashboard/backend/routers/brain.py` | 엔드포인트 정리 범위 판단 |
| D-4 | 소스 | opbr 어댑터(BE) | `dashboard/backend/adapters/opbr_adapter.py` | claude 호출 계약(resume/session-id) 확인 |
| D-5 | 설계 | 아키텍처 | `docs/ARCHITECTURE.md` §OPAL Console | 콘솔 구조·배포 모델 |
| D-6 | 기획 | 프로젝트 정의 | `docs/PROJECT.md` §OPAL Console | 컴포넌트·화면·배포 경계 |
| D-7 | 참고 | 과거 태스크 | `tasks/060-260713-opd-브레인-프라임-연결풀/` | 프라임 풀(prewarm/checkout/adopt) 설계 SSOT |
