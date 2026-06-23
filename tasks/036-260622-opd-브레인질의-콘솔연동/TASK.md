# TASK: OPAL Console 프로젝트 브레인 질의 메뉴 (Phase 1 MVP)

> 작성일: 2026-06-22 | 작업 유형: 신규 | 적용 스킬: opd | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

OPAL Console(읽기전용 대시보드)에 "프로젝트 브레인" 메뉴를 신설하여, 웹 화면에서 brain 지식을 질의하고 근거 인용이 포함된 답변을 받는다. Phase 1은 인증(Claude 로그인) 체크 + 단일 질의/답변(인용 포함)까지를 범위로 한다.

## 배경

OPAL Console은 현재 5개 메뉴(대시보드/프로젝트/태스크/메모리/환경)를 가진 **읽기 전용** 대시보드다(HTTP GET-only, LLM 호출 코드 전무). 캡틴은 brain 지식을 Claude Code 세션 밖(웹)에서 직접 질의·답변·이력확인·재질문하고, 질의 시 Claude 로그인→토큰 흐름으로 LLM을 연동하길 원한다. 이는 Console의 읽기전용 전제를 깨는 첫 기능이므로 경계 격리가 핵심이다.

## 배경 분석 (대화에서 도출)

탐색 워커 2기로 확인한 현황:

- **Console FE**: React 19 + React Router v7 + TanStack Query + Zustand + shadcn/ui. 메뉴 추가 = 3지점(`router.tsx` 라우트 + `AppShell.tsx` NAV_ITEMS + `pages/{name}/{Name}Page.tsx`). API 클라이언트는 `lib/api.ts`의 fetch 래퍼(`http://127.0.0.1:7823`).
- **Console BE**: FastAPI(127.0.0.1:7823), `main.py:45`에서 **GET 메서드만 허용**. 라우터 추가 = 4지점(`routers/*.py` + `models.py` 스키마 + `main.py` include_router + 필요시 `adapters/`). CLI 어댑터는 `adapters/base.py:run_tool()`로 read-only CLI만 호출. **LLM/외부 API 호출 코드 전무**(grep 확인).
- **brain query**: 현재 `//opbr ask`는 Claude Code 세션(=알투 자신)이 합성한다. `brain-tool search`(CLI, 결정론적)는 후보 목록만 반환(page·title·type·score·snippet, **본문 미포함**) → 세션이 선택 페이지를 Read → in-context 합성. 웹은 세션 밖이므로 **backend가 Anthropic SDK로 직접 합성**해야 한다.
- **이력/대화 맥락**: brain `log.md`는 질의 요약·생성 페이지명만 기록(본문·맥락 미보관). 멀티턴/이력조회 기능은 현재 미구현 → Phase 2 신설 대상.
- **인증**: Anthropic 공식 SDK는 `ANTHROPIC_API_KEY` → `AUTH_TOKEN` → **`ant auth login` OAuth 프로필** 순으로 자격증명을 자동 해석·갱신. 캡틴의 "로그인 체크→로그인→토큰" 구상과 일치.

## 확정된 설계 방향 (대화에서 합의)

캡틴 승인(AskUserQuestion 3건):

1. **인증/LLM = 각 사용자 Claude 구독으로 실제 opbr 스킬 구동** (캡틴 정정 2026-06-22, [[console-brain-subscription-auth]]). backend가 `claude -p "//opbr ask <질문>" --output-format json`(+세션 플래그)을 호출 → **OPAL 프레임워크·opbr 스킬이 로드되어** 실제 brain query(term-우선·후보선택·페이지 Read·인용 합성)를 수행하고 사용자 Claude Code 구독으로 실행. backend는 opbr를 재구현하지 않는 **얇은 프록시(DRY/SSOT)**. **종량제 API(키·`ANTHROPIC_API_KEY`·anthropic SDK·ant OAuth) 전면 폐기**, opbr를 끄는 `--safe-mode`도 사용 안 함. "로그인 체크=`claude` 가용·인증", "토큰=Keychain 자체 관리". 실측: claude v2.1.185.
2. **이력 저장 = 브라우저 localStorage** (캡틴 정정 2026-06-22, SQLite 폐기 — 과중). backend·brain **무변경(read-only 취지)** — FE가 Q&A를 클라이언트에 저장하고 화면이 거기서 읽어 표시·재질문. 질의 로그도 각자 브라우저에 남음. (Phase 2 — Phase 1 스파이크는 이력 없음)
3. **진행 = MVP 먼저 → 확장**. 본 태스크 = Phase 1(로그인 체크 + 단일 질의/답변+인용). Phase 2(이력 영속 SQLite + 재질문 멀티턴)는 Phase 1 완료·검증 후 별도 PLAN.
4. **읽기전용 격리 원칙**: POST + 외부 LLM 호출은 **브레인 질의 라우터 하나에만** 국한. 기존 5개 메뉴·어댑터의 read-only는 불변.
5. **관리형 지속 세션** (캡틴 2026-06-22): 데몬이 BrainSession을 관리 — **지연 프라임**(서버 재실행 시 핸들 폐기 → 다음 질의가 OPAL/opbr 1회 부팅) + **5트리거 리셋**(재실행·컨텍스트 임계·유휴 타임아웃·크래시·수동 "새 대화"). 매 질의 재부팅 회피·웜 유지. 방식 **B1(`--resume`) vs B2(상주 `stream-json` 프로세스)**는 Phase 1 스파이크 지연 실측으로 확정.
6. **단계화** (캡틴 2026-06-22): **Phase 1(스파이크)** = 구독 인증 + 질의 + OPAL/opbr 세션 로딩 → 답변 최소 E2E를 먼저 검증(캡틴 직접 1건). 통과 후 **Phase 2+** = FE 질의 UI·세션 리셋 정책·읽기전용 가드·격리·RED-first 테스트·docs.

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | Console에 "프로젝트 브레인" 메뉴 신설 + 인증 체크 + 질의→답변(인용 포함) E2E 동작 (Phase 1). 단계화: Phase 1=스파이크(인증+질의+세션→답변) 우선 | - | backend가 `claude -p "//opbr ask"`로 실제 opbr 스킬 구동(구독) |
| 범위 | 포함: FE 메뉴/라우트/질의 UI + **브라우저 localStorage 이력**(표시·재질문), BE 인증상태 API + 질의 API(POST, opbr 구동 합성, **무상태**), 관리형 지속 세션(지연프라임·5트리거 리셋). 진행: **Phase 1 스파이크 → 캡틴 검증 → Phase 2+ 나머지**. 제외: backend 영속(SQLite 폐기), brain 쓰기, API 키 방식 | - | 단계화·세션·localStorage 캡틴 승인 |
| 제약 | ① 읽기전용 위반(POST·LLM)은 brain 라우터에만 격리, 기존 5메뉴 read-only 불변 ② **LLM = 로컬 `claude -p "//opbr ask" --output-format json`로 실제 opbr 구동(구독). 종량제 API(키·anthropic SDK·ant OAuth) 금지, `--safe-mode`(opbr 미로드) 금지** ③ headless opbr는 brain에 쓰기 금지(질의 전용, synthesis 파일링·term 등록 차단) ④ 인증/LLM·세션은 어댑터 계층 격리(플랫폼 독립) ⑤ 소스(`dashboard/`) 수정 후 install 재배포 ⑥ `.opal/brain` 쓰기 없음 | - | 헌법 Core Stance·PROJECT.md 원칙·[[console-brain-subscription-auth]] |
| 완료기준 | 6번째 메뉴 노출 + 미인증 시 로그인 안내 + 인증 시 질의→답변+근거 인용 반환 + 로컬 데몬 기동 E2E 1건 PASS | - | TEST 단계 동적 검증 |

## 요구사항

- [ ] **R1 (FE 메뉴)**: Console에 "프로젝트 브레인" 6번째 메뉴를 추가한다. — 어디에: `dashboard/frontend/src/router.tsx`(라우트) + `components/app-shell/AppShell.tsx`(NAV_ITEMS) + `pages/brain/BrainPage.tsx`(신규). — 왜: 확정 방향 §본 태스크 범위. — AC: 사이드바에 "프로젝트 브레인" 항목이 노출되고, 클릭 시 `/brain` 라우트로 이동하여 BrainPage가 렌더된다.
- [ ] **R2 (BE 인증 상태 API)**: Claude Code 구독 로그인 상태를 반환하는 GET 엔드포인트를 추가한다. — 어디에: `dashboard/backend/routers/brain.py`(신규) + `models.py`(스키마) + `main.py`(등록). — 왜: 확정 방향 §1. — AC: `GET /api/brain/auth`가 `claude` CLI 가용·인증 여부(`authenticated: bool`)와 미인증/미설치 시 안내를 JSON으로 반환한다.
- [ ] **R3 (BE 질의 API)**: 질문을 받아 brain 검색→`claude` CLI 합성→답변+인용을 반환하는 POST 엔드포인트를 추가한다. — 어디에: `routers/brain.py` + 인증/LLM 어댑터(`adapters/`). — 왜: 확정 방향 §1·본 태스크 범위. — AC: `POST /api/brain/query {question, project}`가 `brain-tool search`로 후보를 얻어 상위 페이지를 Read하고 **로컬 `claude -p ... --output-format json`**(사용자 구독)으로 합성한 `{answer, citations[]}`를 반환한다. citations는 근거 brain 페이지 경로를 포함한다.
- [ ] **R4 (FE 질의 UI)**: 질문 입력→답변+인용 렌더, 미인증 시 로그인 안내. — 어디에: `pages/brain/BrainPage.tsx`. — 왜: 확정 방향 §본 태스크 범위. — AC: 미인증 시 "Claude 로그인 필요 + `ant auth login` 안내" 표시. 인증 시 질문 입력→제출→답변 본문과 근거 페이지 목록(인용)이 화면에 렌더된다.
- [ ] **R5 (읽기전용 격리)**: POST·외부 LLM 호출 능력을 brain 라우터에만 국한한다. — 어디에: `main.py` 메서드 제약 + `routers/brain.py`. — 왜: 확정 방향 §4. — AC: brain 라우터만 POST 허용되고 기존 5개 라우터/어댑터는 GET·read-only로 불변임을 코드로 확인 가능하다.

## 제약 조건

- 읽기전용 경계: POST·LLM 호출은 brain 질의 라우터에만 격리. 기존 dashboard/doctor/projects/tasks/memory 라우터·어댑터의 GET-only·read-only 불변.
- **LLM 합성 = 로컬 `claude` CLI(`claude -p ... --output-format json`)로 사용자 구독 실행. Anthropic API SDK·키·ant OAuth 일절 사용 금지** ([[console-brain-subscription-auth]]).
- 인증·LLM 연동은 어댑터 계층으로 격리(플랫폼 독립성 — PROJECT.md 원칙 §3). `claude` 미설치/미인증 시 graceful 안내.
- 배포 경계: `dashboard/` 소스만 수정. `~/.opal/dashboard-server/` 배포본 직접 편집 금지. 동작 발효는 install 재배포(L3, 캡틴 직접 수행).
- `.opal/brain` 쓰기 없음(Phase 1은 이력 저장 미수행).
- 데몬은 127.0.0.1 바인딩 유지(외부 노출 금지).

## 기술 스택

- FE: React 19, TypeScript, Vite, React Router v7, TanStack Query v5, Zustand v5, shadcn/ui
- BE: Python, FastAPI, uvicorn
- 신규 Python 의존성 없음 (LLM은 `claude` CLI 서브프로세스 호출 — anthropic SDK 불필요)
- 도구: `brain-tool`(CLI, 기존), **`claude` CLI v2.1.185(headless `-p`, 사용자 구독 인증)**

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | ARCHITECTURE.md §OPAL Console | `docs/ARCHITECTURE.md` | Console 구조·배포 모델 |
| D-2 | 설계 | PROJECT.md 프로젝트 구성 | `docs/PROJECT.md` | Console FE/BE 영역·전문 에이전트 매핑 |
| D-3 | 컨벤션 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 코드·배포 경계·플랫폼 분기 규칙 |
| D-4 | 설계 | opal-brain 설계 SSOT | `docs/proposals/opal-brain-design.md` | brain query 사상·search 인터페이스 |

## Phase 2 (본 태스크 제외 — 후속)

- 이력 영속: backend SQLite에 Q&A 대화 저장 + 이력 조회 API/UI
- 재질문: 멀티턴 대화(stateless API 히스토리 재전송)
- Phase 1 완료·검증 후 별도 PLAN으로 진행
