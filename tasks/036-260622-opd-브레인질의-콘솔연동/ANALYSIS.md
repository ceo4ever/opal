# ANALYSIS — OPAL Console 브레인 질의 메뉴 (Task 036)

> 작성일: 2026-06-22 | 단계: op-dev-analysis | 스킬: opd (Full Task)
> 인용 형식: `{경로}:{라인}` 또는 `docs/문서명 §섹션`

---

## 1. R1 ~ R5 요구사항별 변경 지점

### R1 — FE 메뉴 (프로젝트 브레인 6번째 네비 추가)

| 파일 | 위치 | 변경 내용 |
|------|------|----------|
| `dashboard/frontend/src/router.tsx` | L20~33 `createBrowserRouter` children 배열 | `/brain` 라우트 항목 추가: `{ path: "brain", element: <BrainPage /> }` |
| `dashboard/frontend/src/components/app-shell/AppShell.tsx` | L73~79 `NAV_ITEMS` 배열 | 6번째 항목 추가: `{ to: "/brain", label: "프로젝트 브레인", icon: <적절한 lucide 아이콘> }` |
| `dashboard/frontend/src/pages/brain/BrainPage.tsx` | 신규 파일 | BrainPage 컴포넌트 — 인증 상태 조회 + 질의 UI 렌더 (R4와 동일 파일) |

**참조**: `dashboard/frontend/src/router.tsx:20-33` (현재 5개 children 구조), `dashboard/frontend/src/components/app-shell/AppShell.tsx:73-79` (NAV_ITEMS 배열, 현재 5개 항목)

**주의**: AppShell.tsx L65 주석 `/** 5개 네비 항목 (C-11: 브레인 제외) */`도 함께 갱신 필요.

---

### R2 — BE 인증 상태 API (`GET /api/brain/auth`)

| 파일 | 위치 | 변경 내용 |
|------|------|----------|
| `dashboard/backend/routers/brain.py` | 신규 파일 | `GET /api/brain/auth` 엔드포인트. 자격증명 존재 여부 경량 체크 → `{authenticated: bool, message: str}` 반환 |
| `dashboard/backend/models.py` | L198 (끝) 이후 | `BrainAuthResponse`, `BrainQueryRequest`, `BrainQueryResponse`, `CitationItem` Pydantic 스키마 추가 |
| `dashboard/backend/main.py` | L21 imports + L51~55 router 등록 블록 | `brain` 라우터 import + `app.include_router(brain.router)` 추가 |
| `dashboard/backend/adapters/auth_adapter.py` | 신규 파일 | 인증 상태 확인 어댑터 — 자격증명 존재 경량 체크 로직 캡슐화 |

**CORS 완화 필요**: `main.py:45` 현재 `allow_methods=["GET"]`. R3의 POST를 허용하기 위해 섹션 2에서 별도 기술.

---

### R3 — BE 질의 API (`POST /api/brain/query`)

| 파일 | 위치 | 변경 내용 |
|------|------|----------|
| `dashboard/backend/routers/brain.py` | R2 파일에 추가 | `POST /api/brain/query` — 질의 수신 → search → 페이지 Read → SDK 합성 → `{answer, citations[]}` 반환 |
| `dashboard/backend/adapters/brain_adapter.py` | 신규 파일 | brain-tool search CLI 호출(run_tool 패턴) + 결과 페이지 본문 읽기. LLM 합성은 llm_adapter에 위임 |
| `dashboard/backend/adapters/llm_adapter.py` | 신규 파일 | Anthropic SDK 합성 로직 캡슐화 — `claude-opus-4-8`, `max_tokens=4096`, 비스트리밍 |
| `dashboard/backend/models.py` | 위 R2와 동일 | `BrainQueryRequest`, `BrainQueryResponse`, `CitationItem` |

---

### R4 — FE 질의 UI (`BrainPage.tsx`)

| 파일 | 위치 | 변경 내용 |
|------|------|----------|
| `dashboard/frontend/src/pages/brain/BrainPage.tsx` | 신규 파일 | 인증 상태 조회(`useQuery GET /api/brain/auth`) + 미인증 시 안내 렌더 + 질의 입력폼 + 답변/인용 렌더 |

**패턴**: `apiClient<T>(path, options)` (`dashboard/frontend/src/lib/api.ts:19`) 재사용. POST는 `options: { method: "POST", body: JSON.stringify(...) }` 형태. TanStack Query `useMutation` 사용 권장(질의는 사이드이펙트 있는 단발 요청).

---

### R5 — 읽기전용 격리

| 파일 | 위치 | 변경 내용 |
|------|------|----------|
| `dashboard/backend/main.py` | L41~47 `CORSMiddleware` 설정 | `allow_methods` 완화 전략 — 섹션 2 참조 |
| `dashboard/backend/routers/brain.py` | 라우터 전체 | POST 메서드를 이 라우터에만 한정, 기존 5개 라우터는 GET만 유지 |

---

## 2. CORS `allow_methods` 완화: brain 라우터 POST 허용 + 기존 5라우터 GET-only 보존

### 현황

`dashboard/backend/main.py:45`에 `allow_methods=["GET"]`으로 전역 설정되어 있다. CORS 미들웨어는 FastAPI 앱 전체에 적용되므로, 이 값을 `["GET", "POST"]`로 바꾸면 **모든 라우터**에서 POST 요청의 CORS preflight를 허용하게 된다.

### 문제와 해결 방향

CORS `allow_methods`는 브라우저의 preflight(OPTIONS) 허용 여부만 제어한다. 실제 라우터가 POST 핸들러를 등록하지 않으면 FastAPI는 405 Method Not Allowed를 반환한다. 따라서:

- **CORS 미들웨어**: `allow_methods=["GET", "POST"]`로 완화
- **기존 5개 라우터** (`dashboard`, `projects`, `tasks`, `memory`, `doctor`): POST/PUT/DELETE 핸들러 **미등록** 상태 유지 → 실질적 POST 접근 불가

**기존 라우터 GET-only 검증 결과**:

```
grep -rn "@router.post|@router.put|@router.delete" dashboard/backend/routers/
결과: 0건 — 5개 라우터 모두 @router.get만 사용 (실측 확인)
```

### 구현 방법

`main.py:45` 변경:

```python
# 변경 전
allow_methods=["GET"],     # 읽기 전용 — GET만 허용

# 변경 후
allow_methods=["GET", "POST"],  # brain 질의 POST 추가 — 기존 5라우터는 GET 핸들러만 등록되어 실질적 read-only 유지
```

`@header`의 description과 depends 필드도 brain 라우터 포함으로 갱신.

---

## 3. Backend Brain Query 데이터 흐름

```
POST /api/brain/query {question, project}
  │
  ▼ [routers/brain.py]
  ├─ 1. 인증 확인: auth_adapter.check_auth() → 미인증 시 401
  ├─ 2. brain 경로 결정: project 파라미터 → {project}/.opal/brain/
  │
  ├─ 3. brain_adapter.search(question, brain_path)
  │      [adapters/brain_adapter.py]
  │      run_tool(["bash", BRAIN_TOOL, "search", question,
  │               "--brain-path", brain_path, "--limit", "5"])
  │      → {ok:true, matches:[{page, title, type, score, snippet}]}
  │      ← 상위 N개 page 절대경로 목록 반환
  │
  ├─ 4. 후보 페이지 본문 읽기: brain_adapter.read_pages(page_paths)
  │      [adapters/brain_adapter.py]
  │      pathlib.Path(page_path).read_text(encoding="utf-8")
  │      → List[{path, content}] (상위 3~5개 페이지)
  │
  ├─ 5. llm_adapter.synthesize(question, pages)
  │      [adapters/llm_adapter.py]
  │      client = anthropic.Anthropic()  # 자격증명 자동 해석
  │      client.messages.create(
  │        model="claude-opus-4-8",
  │        max_tokens=4096,
  │        system=<RAG 시스템 프롬프트>,
  │        messages=[{"role":"user","content": f"질문: {question}\n\n컨텍스트:\n{pages_text}"}]
  │      )
  │      → {answer: str, citations: List[str]}
  │
  └─ 6. BrainQueryResponse 반환: {answer, citations[]}
```

### 각 단계 책임 모듈

| 단계 | 모듈 | 책임 |
|------|------|------|
| 라우팅/인증/조립 | `routers/brain.py` | 요청 수신, 인증 게이트, 어댑터 오케스트레이션, 응답 직렬화 |
| brain 검색 | `adapters/brain_adapter.py` | brain-tool search CLI 호출(run_tool 패턴), 페이지 본문 파일 Read |
| LLM 합성 | `adapters/llm_adapter.py` | Anthropic SDK 호출, RAG 프롬프트 구성, citations 추출 |
| 인증 상태 | `adapters/auth_adapter.py` | 자격증명 존재 경량 체크 |

**brain-tool CLI 호출 패턴** (`adapters/base.py:run_tool` 기존 패턴 재사용):

```python
BRAIN_TOOL = str(Path.home() / ".opal" / "tools" / "brain-tool" / "run.sh")
run_tool(["bash", BRAIN_TOOL, "search", question, "--brain-path", brain_path, "--limit", "5"])
```

`brain-tool search` 출력 스키마 (`brain_tool.py:682-686`):

```json
{
  "ok": true,
  "command": "search",
  "query": "...",
  "matches": [
    {"page": "/abs/path/to/page.md", "title": "...", "type": "concept", "score": 0.8, "snippet": "..."}
  ],
  "total": 12
}
```

`page` 필드는 절대경로. 후보 상위 3~5개 선택 후 `Path(page).read_text()` 로 본문 로드. `.opal/brain/pages/` 하위 `.md` 파일이 대상 (`brain-tool/brain_tool.py:682`).

---

## 4. 인증 상태 확인 방법 — 트레이드오프 및 권고

### 자격증명 해석 순서 (Anthropic SDK 공식)

`Anthropic()` 인스턴스 생성 시 자동 해석 순서:
1. `ANTHROPIC_API_KEY` 환경변수
2. `ANTHROPIC_AUTH_TOKEN` 환경변수
3. `~/.config/anthropic/` OAuth 프로필 (`ant auth login` 저장 위치)

**실측**: `~/.config/anthropic/` 미존재, `ant` CLI 미설치.

### (a) 경량 체크 — 자격증명 존재 여부만 확인 (네트워크 비용 없음)

```python
import os
from pathlib import Path

def check_auth_lightweight() -> dict:
    # 1. 환경변수 체크
    if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        return {"authenticated": True, "source": "env"}
    # 2. OAuth 프로필 체크
    profile_dir = Path.home() / ".config" / "anthropic"
    if profile_dir.exists() and any(profile_dir.iterdir()):
        return {"authenticated": True, "source": "oauth_profile"}
    return {"authenticated": False, "source": None}
```

장점: 네트워크 호출 없음, 즉시 응답
단점: 자격증명이 존재해도 만료/무효일 수 있음 (유효성 미보장)

### (b) 실호출 체크 — cheap API 호출로 인증 검증

```python
import anthropic

def check_auth_live() -> dict:
    try:
        client = anthropic.Anthropic()
        client.models.retrieve("claude-opus-4-8")
        return {"authenticated": True}
    except anthropic.AuthenticationError:        # 401
        return {"authenticated": False, "error": "invalid_credentials"}
    except anthropic.APIConnectionError:
        return {"authenticated": False, "error": "connection_failed"}
```

장점: 실제 유효성 확인
단점: 네트워크 호출 + 지연, 불필요한 API 요금, 네트워크 오류 시 false negative

### 권고

PLAN이 택1하도록 권고:

**Phase 1 MVP 관점에서 (a) 경량 체크 권장**. 이유:
- `GET /api/brain/auth`는 UI 렌더 시 자주 호출 → 네트워크 비용 없는 경량 체크가 UX 유리
- 실제 유효성은 `POST /api/brain/query` 호출 시 `anthropic.AuthenticationError` 캐치로 자연스럽게 검증
- "자격증명 없음" 탐지만으로 미인증 안내 목적 충족

### 미인증 UX 안내 (두 경로)

`authenticated: false` 응답 시 FE 표시:

```
Claude API 자격증명이 설정되지 않았습니다.
다음 중 하나로 설정하세요:

① 환경변수 설정 (권장 — 가장 단순)
   export ANTHROPIC_API_KEY="sk-ant-..."

② Anthropic CLI 설치 후 로그인
   brew install anthropics/tap/ant
   ant auth login
```

실측 제약: `ant` CLI 미설치, `~/.config/anthropic/` 미존재. 환경변수가 가장 신뢰할 수 있는 방법.

---

## 5. Anthropic SDK 의존성 추가 위치

### 탐색 결과

```
dashboard/backend/         requirements.txt 없음 (실측)
dashboard/                 requirements.txt 없음 (실측)
opal/tools/requirements.txt  존재 — 통합 관리 파일 (유일한 위치)
```

`docs/ARCHITECTURE.md:194` §Python 의존성 참조: `opal/tools/requirements.txt → ~/.opal/.venv/` 로 install-mac.sh가 관리.

### 현황 — 추가 조치 불필요

`opal/tools/requirements.txt:22`:
```
anthropic>=0.39.0
```

배포된 venv에 `anthropic==0.88.0` 이미 설치 확인. 의존성 추가 불필요.

PLAN/EXECUTE에서 확인 필요한 사항: backend가 `~/.opal/.venv/bin/python`으로 실행되는지 검증 (install 배포 시 venv 공유 구조 확인).

### Import 패턴

```python
import anthropic

client = anthropic.Anthropic()  # 자격증명 자동 해석 (env → ~/.config/anthropic/)
response = client.messages.create(
    model="claude-opus-4-8",
    max_tokens=4096,
    system="...",
    messages=[{"role": "user", "content": user_content}]
)
answer = response.content[0].text
```

예외 클래스 (정확한 명칭):
```python
except anthropic.AuthenticationError    # 401 자격증명 무효
except anthropic.APIConnectionError     # 네트워크 오류
except anthropic.APIStatusError as e    # 그 외 4xx/5xx (e.status_code, e.message)
```

---

## 6. 리스크 표

| # | 리스크 | 심각도 | 원인 | 대응 |
|---|--------|--------|------|------|
| R-1 | **읽기전용 경계 누수** — 기존 5개 라우터에 POST 핸들러가 우발적으로 추가될 경우 | 높음 | CORS allow_methods POST 완화 후 실수로 다른 라우터에 POST 핸들러 등록 | brain 라우터에만 POST 핸들러 등록. 기존 라우터에 GET-only 주석 명시. TEST에서 기존 라우터 POST 405 검증 포함 |
| R-2 | **인증 미설정** — ant 미설치 + API 키 미설정 환경 | 높음 | ant CLI 미설치(실측), ~/.config/anthropic/ 미존재(실측) | GET /api/brain/auth 응답에 두 가지 설정 방법 명시. FE 미인증 안내 렌더 |
| R-3 | **데몬 환경 자격증명 접근** — HOME/~/.config 미접근 | 중간 | 배포 데몬이 다른 사용자 또는 제한 환경에서 실행 시 ~/.config/anthropic/ 경로 불일치 | ANTHROPIC_API_KEY 환경변수 우선 안내. Path.home() 사용으로 HOME 기준 동적 해석 |
| R-4 | **brain 페이지 부재** — brain 미초기화 또는 검색 결과 0건 | 중간 | //opbr init 미실행 프로젝트에서 질의 시 brain-tool이 brain_not_initialized 에러 | ToolError 캐치 후 적절한 응답 반환. FE에서 "브레인이 초기화되지 않았습니다" 안내 |
| R-5 | **LLM 지연** — claude-opus-4-8 응답 지연으로 사용자 대기 | 낮음 | RAG 합성 보통 2~10초. 비스트리밍 blocking call | LLM 호출 timeout 60초 설정(run_tool 기본 10초와 별도). FE 로딩 스피너. Phase 2 스트리밍 검토 |
| R-6 | **brain search timeout** — 대용량 brain에서 search 지연 | 낮음 | run_tool 기본 timeout=10초. brain이 클 경우 초과 | brain_adapter search timeout 30초 상향 |
| R-7 | **배포 경계 위반** — ~/.opal/dashboard-server/ 직접 편집 | 높음 | 직접 배포본 수정 시 install 재배포 후 소실 | dashboard/ 소스만 수정. install 재배포는 캡틴 직접 수행. CONVENTIONS.md §배포 경계 준수 |

---

## 7. 참조 인용

| # | 참조 | 인용 위치 |
|---|------|----------|
| A-1 | Console 구조·배포 모델 | `docs/ARCHITECTURE.md §OPAL Console` (L217~243) |
| A-2 | FastAPI GET-only 설계 | `dashboard/backend/main.py:45` (`allow_methods=["GET"]`) |
| A-3 | 5개 라우터 GET-only 실증 | `dashboard/backend/routers/` 전체 grep @router.post → 0건 (실측) |
| A-4 | brain-tool search 출력 스키마 | `opal/tools/brain-tool/brain_tool.py:682-686` |
| A-5 | brain-tool --brain-path 기본값 | `opal/tools/brain-tool/brain_tool.py:1220` (`default="."`) |
| A-6 | brain-tool 배포 경로 | `~/.opal/tools/brain-tool/run.sh` (실측 확인) |
| A-7 | anthropic SDK 의존성 선언 | `opal/tools/requirements.txt:22` (`anthropic>=0.39.0`) |
| A-8 | anthropic SDK 설치 확인 | `~/.opal/.venv/` `anthropic==0.88.0` (실측) |
| A-9 | Python venv 배포 모델 | `docs/ARCHITECTURE.md:194` (`opal/tools/requirements.txt → ~/.opal/.venv/`) |
| A-10 | run_tool 패턴 | `dashboard/backend/adapters/base.py:31` |
| A-11 | 플랫폼 독립성 원칙 | `docs/PROJECT.md §프로젝트 원칙` §3 |
| A-12 | 배포 경계 원칙 | `docs/CONVENTIONS.md §배포 경계` |
| A-13 | 어댑터 패턴 참조 | `dashboard/backend/adapters/state_adapter.py` (구조 참조) |
| A-14 | FE API 클라이언트 패턴 | `dashboard/frontend/src/lib/api.ts:19` (`apiClient` 함수) |
| A-15 | brain pages 실제 경로 | `.opal/brain/pages/` (실측 확인 — entity/concept/flow/synthesis 하위 디렉토리) |

---

## 부록 — 신규·수정 파일 예측 목록

**신규 파일**:

| 파일 | 목적 |
|------|------|
| `dashboard/backend/routers/brain.py` | GET /api/brain/auth + POST /api/brain/query |
| `dashboard/backend/adapters/auth_adapter.py` | 자격증명 경량 체크 |
| `dashboard/backend/adapters/brain_adapter.py` | brain-tool search + 페이지 Read |
| `dashboard/backend/adapters/llm_adapter.py` | Anthropic SDK 합성 |
| `dashboard/frontend/src/pages/brain/BrainPage.tsx` | 브레인 질의 UI |

**수정 파일**:

| 파일 | 수정 내용 |
|------|----------|
| `dashboard/backend/main.py` | brain 라우터 등록 + allow_methods POST 추가 |
| `dashboard/backend/models.py` | Brain 관련 Pydantic 스키마 4종 추가 |
| `dashboard/frontend/src/router.tsx` | /brain 라우트 추가 |
| `dashboard/frontend/src/components/app-shell/AppShell.tsx` | NAV_ITEMS 6번째 항목 추가 + 주석 갱신 |
