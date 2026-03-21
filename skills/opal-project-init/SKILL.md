---
name: opal-project-init
description: |
  프로젝트 문서 템플릿 자동 생성 스킬. 신규 프로젝트는 인터뷰를 통해, 기존 프로젝트는
  코드 자동 분석 + 확인/보정 인터뷰를 통해 프로젝트 정보를 수집하고, context7 MCP로
  최신 기술 문서를 조회한 뒤, 플레이스홀더 기반 템플릿에 치환하여 docs/ 문서와
  LLM 플랫폼별 AI 지시 파일(CLAUDE.md, GEMINI.md, .cursorrules)을 생성한다.
triggers:
  - "프로젝트 초기 셋팅"
  - "프로젝트 스캐폴드"
  - "프로젝트 시작"
  - "새 프로젝트 문서 만들어줘"
  - "프로젝트 문서 생성"
  - "기존 프로젝트 문서화"
  - "프로젝트 문서 만들어줘"
  - "docs 생성"
  - "프로젝트에 문서 추가"
version: 1.1.0
---

# opal-project-init

프로젝트 문서 및 AI 지시 파일을 자동 생성하는 스킬.

## 개요

**두 가지 모드**를 지원한다:

- **신규 프로젝트 모드** (new): 인터뷰 → context7 조회 → 템플릿 치환 → 파일 생성
- **기존 프로젝트 모드** (existing): 코드 자동 분석 → 확인/보정 인터뷰 → context7 조회 → 템플릿 필터링 → 파일 생성/병합

AI 에이전트가 직접 실행하며, 외부 템플릿 엔진(Jinja2 등)을 사용하지 않는다.

## 템플릿 위치

```
~/.opal/skills/opal-project-init/templates/
├── common/          # 공통 (모든 유형)
│   ├── docs/        # INDEX.md, server/*, client/*
│   └── platform/    # CLAUDE.md, GEMINI.md, .cursorrules
├── web/             # 웹 프로젝트 추가
├── ai-agent/        # AI 에이전트 프로젝트 추가
└── optional/        # 조건부 (SQLITE_SETUP, CHAT_UI_GUIDE)
```

---

## 실행 프로세스

### Step 0: 모드 선택

프로젝트 루트에 소스 코드가 존재하는지 확인하여 모드를 판별한다.

**자동 판별 기준**: 아래 파일 중 하나라도 존재하면 "기존 프로젝트"를 제안한다.
- `package.json`, `pyproject.toml`, `requirements.txt`
- `go.mod`, `Cargo.toml`, `pom.xml`, `build.gradle`
- `src/`, `app/`, `server/`, `client/` 디렉토리

```
[모드 선택]

프로젝트 루트를 분석한 결과, {소스 코드 존재/미존재} 상태입니다.

어떤 모드로 진행할까요?
  1. 신규 프로젝트 — 처음부터 인터뷰 시작 (Step 1~8)
  2. 기존 프로젝트 — 코드 자동 분석 후 확인/보정 인터뷰 (Step 0-A → Step 4~8)
```

- **신규 프로젝트** 선택 시: 기존 Step 1~8 그대로 진행
- **기존 프로젝트** 선택 시: Step 0-A(자동 분석) → Step 0-B(확인/보정 인터뷰) → Step 4~8 진행

---

### Step 0-A: 자동 분석 (기존 프로젝트 모드 전용)

기존 프로젝트 모드에서만 실행한다. 코드와 설정 파일을 스캔하여 플레이스홀더를 자동 추론한다.

**소스 코드 분석**:

| 분석 대상 | 추출 정보 |
|----------|----------|
| `package.json` | name → `PROJECT_NAME`, description → `PROJECT_DESCRIPTION`, dependencies로 프론트엔드 스택 추론 (next → Next.js, react → React, vue → Vue.js) |
| `pyproject.toml` / `requirements.txt` | 백엔드 스택 추론 (fastapi → Python/FastAPI, django → Python/Django, flask → Python/Flask) |
| `go.mod` | 백엔드 스택 추론 (Go) |
| `Cargo.toml` | 백엔드 스택 추론 (Rust) |
| 디렉토리 구조 | `src/`, `app/`, `server/`, `client/` 등으로 프로젝트 유형 추론 (web/ai-agent/data/custom) |
| `.env`, `docker-compose.yml` | `SERVER_PORT`, `CLIENT_PORT` 추출 (PORT, SERVER_PORT, CLIENT_PORT, NEXT_PUBLIC_PORT 등) |
| DB 관련 env 또는 의존성 | `DB_TYPE` 추론 (mysql, postgresql, sqlite, mongodb 등) |

**LLM 플랫폼 파일 분석**:

| 분석 대상 | 추출 정보 |
|----------|----------|
| `README.md` | 프로젝트 설명, 기술 스택, 설치 방법 → `PROJECT_NAME`, `PROJECT_DESCRIPTION` 보정 |
| `CLAUDE.md` | 기존 코드 컨벤션, 아키텍처 규칙 파악 → 새 문서에 기존 규칙 반영. OPAL 마커(`# === OPAL START ===`) 존재 여부 확인 |
| `.cursorrules` | 기존 Cursor 규칙 파악 → 병합 시 보존 |
| `GEMINI.md` | 기존 Gemini 설정 파악 → 병합 시 보존 |
| `docs/` 디렉토리 | 기존 문서 구조 파악 → 이미 존재하는 문서는 생성하지 않음 |

**자동 추론 결과 → 플레이스홀더 매핑**:

| 분석 소스 | 추론 대상 |
|----------|----------|
| package.json name | `PROJECT_NAME` |
| package.json description | `PROJECT_DESCRIPTION` |
| package.json dependencies에 next 포함 | `TECH_STACK_FRONTEND` = "Next.js" |
| package.json dependencies에 react만 | `TECH_STACK_FRONTEND` = "React" |
| pyproject.toml에 fastapi 포함 | `TECH_STACK_BACKEND` = "Python/FastAPI" |
| pyproject.toml에 django 포함 | `TECH_STACK_BACKEND` = "Python/Django" |
| .env의 PORT, SERVER_PORT | `SERVER_PORT` |
| .env의 CLIENT_PORT, NEXT_PUBLIC_PORT | `CLIENT_PORT` |
| DB 관련 env 또는 의존성 | `DB_TYPE` |
| README.md 제목/설명 | `PROJECT_NAME`, `PROJECT_DESCRIPTION` 보정 |
| CLAUDE.md 컨벤션 섹션 | 새 문서 생성 시 기존 규칙 참조 |
| .cursorrules 내용 | 병합 시 기존 규칙 보존 |
| docs/ 기존 파일 목록 | 중복 파일 생성 방지 (이미 있으면 스킵) |

---

### Step 0-B: 확인/보정 인터뷰 (기존 프로젝트 모드 전용)

자동 분석 결과를 사용자에게 보여주고 확인/보정을 요청한다. 기존 Step 1~3의 인터뷰를 대체한다.

```
[자동 분석 결과 확인]

아래는 프로젝트 코드를 분석한 결과입니다. 수정이 필요한 항목만 알려주세요.

- 프로젝트명: {분석된 영어명} (한글명을 입력해주세요)
- 한 줄 설명: {분석된 설명 또는 "입력해주세요"}
- 기술 스택: {분석된 백엔드} + {분석된 프론트엔드} + {분석된 DB}
- 포트: 백엔드 {분석된 포트 또는 8000} / 프론트엔드 {분석된 포트 또는 3000}
- 유형: {추론된 유형} ({추론 근거})
- 도메인명: {추론된 주요 모듈명 또는 "입력해주세요"}
- 아키텍처: {단일/멀티 도메인}

특별 기능:
  [ ] 채팅/메시징 기능     → CHAT_UI_GUIDE.md 생성
  [ ] SQLite 로컬 개발     → SQLITE_SETUP.md 생성
  [ ] 인증/권한 관리       → 관련 섹션 포함

수정할 항목이 있으면 알려주세요. 없으면 "확인"이라고 답해주세요.
```

사용자가 "확인"하면 분석 결과로 진행, 수정 사항이 있으면 반영한 뒤 진행한다.

> 확인/보정 인터뷰 완료 후 Step 4(context7 조회)로 이동한다. Step 1~3은 건너뛴다.

---

### Step 1: 프로젝트 유형 인터뷰 (Round 0) — 신규 모드 전용

사용자에게 프로젝트 유형을 묻는다. 이 선택에 따라 후속 질문과 포함 템플릿이 달라진다.

```
[Round 0 — 프로젝트 유형 선택]

어떤 유형의 프로젝트인가요?
  1. web        — 웹 애플리케이션 (CRUD, 대시보드 등)
  2. ai-agent   — AI 에이전트 시스템 (LangChain, 멀티에이전트 등)
  3. data       — 데이터 분석/파이프라인
  4. custom     — 직접 정의 (공통 템플릿만 생성)
```

→ 선택값을 `PROJECT_TYPE` 변수에 저장

---

### Step 2: 기본 정보 인터뷰 (Round 1) — 신규 모드 전용

4개 질문을 한 번에 제시한다.

```
[Round 1 — 프로젝트 기본 정보]

Q1. 프로젝트명
  - 영어명 (디렉토리·코드용, 예: my-project):
  - 한글명 (문서 제목용, 예: 나의 프로젝트):
  - 한 줄 설명:

Q2. 기술 스택
  백엔드 (선택 또는 직접 입력):
    1. Python/FastAPI   2. Node.js/Express   3. Go/Gin   4. 직접 입력
  프론트엔드 (선택 또는 직접 입력):
    1. Next.js   2. React   3. Vue.js   4. 직접 입력
  데이터베이스 (선택 또는 직접 입력):
    1. MySQL   2. PostgreSQL   3. SQLite   4. MySQL+SQLite(로컬)   5. 직접 입력

Q3. 포트 및 도메인
  - 백엔드 포트 (기본: 8000):
  - 프론트엔드 포트 (기본: 3000):
  - 주요 도메인명 (서비스 모듈 단위, 예: aic, user, product):

Q4. 아키텍처
  도메인 구조:
    1. 단일 도메인
    2. 멀티 도메인
```

---

### Step 3: 특별 기능 인터뷰 (Round 2) — 신규 모드 전용

```
[Round 2 — 특별 기능 선택 (복수 선택 가능)]

포함할 기능 및 문서를 선택하세요:
  [ ] 채팅/메시징 기능     → CHAT_UI_GUIDE.md 생성
  [ ] SQLite 로컬 개발     → SQLITE_SETUP.md 생성
  [ ] 인증/권한 관리       → 관련 섹션 포함
```

> DB에서 "MySQL+SQLite(로컬)"을 선택했으면 SQLite는 자동 포함

---

### Step 4: context7 MCP 기술 정보 조회

인터뷰 완료 후, 선택한 기술 스택에 대해 context7 MCP로 최신 정보를 조회한다.

**조회 절차**:
1. `mcp__context7__resolve-library-id({라이브러리명})` → library_id 획득
2. `mcp__context7__query-docs(library_id, {조회 토픽})` → 최신 정보

**기술 스택별 조회 대상**:

| 선택한 스택 | resolve 인자 | query 토픽 |
|------------|-------------|-----------|
| Python/FastAPI | `"fastapi"` | "latest version, uvicorn configuration" |
| Node.js/Express | `"express"` | "latest version, middleware setup" |
| Next.js | `"nextjs"` | "latest version, app router configuration" |
| React | `"react"` | "latest version, recommended setup" |
| SQLAlchemy (Python+DB) | `"sqlalchemy"` | "async configuration, latest patterns" |
| Tailwind CSS | `"tailwindcss"` | "v4 configuration" |
| Zustand | `"zustand"` | "latest patterns, store setup" |

**반영 방법**:
- `TECH_STACK_BACKEND`에 조회된 최신 버전 반영 (예: "Python 3.12, FastAPI 0.115+")
- `TECH_STACK_FRONTEND`에 조회된 최신 버전 반영 (예: "Next.js 15, TypeScript 5.x")
- 구버전/deprecated 설정 사용 방지

**context7 사용 불가 시**: 인터뷰에서 수집한 정보만으로 진행 (폴백)

---

### Step 5: 플레이스홀더 매핑표 작성

인터뷰 결과 + context7 조회 결과를 합산하여 매핑표를 만든다.

```markdown
## 플레이스홀더 매핑

| 플레이스홀더 | 값 |
|------------|-----|
| {{PROJECT_NAME}} | {사용자 입력 영어명} |
| {{PROJECT_DESCRIPTION}} | {사용자 입력 설명} |
| {{DOMAIN_NAME}} | {사용자 입력 도메인명} |
| {{SERVER_PORT}} | {사용자 입력 또는 기본값 8000} |
| {{CLIENT_PORT}} | {사용자 입력 또는 기본값 3000} |
| {{DB_TYPE}} | {선택값} |
| {{API_URL_LOCAL}} | http://localhost:{SERVER_PORT} |
| {{TECH_STACK_BACKEND}} | {스택 + context7 최신 버전} |
| {{TECH_STACK_FRONTEND}} | {스택 + context7 최신 버전} |
| {{SQLITE_DB_PATH}} | {조건부: DB에 sqlite 포함 시} |
| {{DOMAIN_EXAMPLES}} | {조건부: 멀티도메인 시} |
| {{CHAT_API_ENDPOINT}} | {조건부: 채팅 기능 선택 시} |
```

이 매핑표를 사용자에게 보여주고 확인을 받는다.

---

### Step 6: 포함할 템플릿 파일 결정

프로젝트 유형과 선택한 기능에 따라 포함 파일을 확정한다.

#### 기존 프로젝트 모드 템플릿 필터링

기존 프로젝트 모드에서는 기술 스택과 불일치하는 템플릿을 자동 제외한다. 제외 대상은 config.json의 `excludeTemplates` 배열에 추가한다.

| 조건 | 제외 대상 |
|------|----------|
| 백엔드가 Python 계열이 아닌 경우 | `docs/server/UV_SETUP.md` |
| 프론트엔드가 없는 경우 | `docs/client/` 전체 (README.md, ARCHITECTURE.md, ENVIRONMENT.md, PROJECT_STRUCTURE.md, OPENAPI_GUIDE.md, COMMON_ISSUES.md) |
| 백엔드가 없는 경우 | `docs/server/` 전체 |
| DB가 SQLite를 포함하지 않는 경우 | `docs/server/SQLITE_SETUP.md` |

또한, `docs/` 디렉토리에 이미 존재하는 파일은 건너뛴다 (덮어쓰지 않음).

**항상 포함 (common/)**:
- `docs/INDEX.md`
- `docs/server/README.md`
- `docs/server/ENVIRONMENT.md`
- `docs/server/PROJECT_STRUCTURE.md`
- `docs/server/UV_SETUP.md` (백엔드가 Python 계열일 때)
- `docs/client/README.md`
- `docs/client/ARCHITECTURE.md`
- `docs/client/ENVIRONMENT.md`
- `docs/client/PROJECT_STRUCTURE.md`
- `docs/client/OPENAPI_GUIDE.md`
- `docs/client/COMMON_ISSUES.md`
- `platform/CLAUDE.md`
- `platform/GEMINI.md`
- `platform/.cursorrules`

**유형별 추가 포함**:

| 유형 | 추가 파일 | 소스 |
|------|----------|------|
| web | DOMAIN_GUIDE.md, HOW_TO_REQUEST_NEW_DOMAIN.md | `templates/web/` |
| ai-agent | DOMAIN_GUIDE.md, HOW_TO_REQUEST_NEW_DOMAIN.md | `templates/ai-agent/` |
| data | (공통만) | - |
| custom | (공통만) | - |

**조건부 포함 (optional/)**:

| 조건 | 파일 |
|------|------|
| DB에 sqlite 포함 또는 SQLite 로컬 개발 선택 | `SQLITE_SETUP.md` |
| 채팅/메시징 기능 선택 | `CHAT_UI_GUIDE.md` |
| 멀티 도메인 선택 | `HOW_TO_REQUEST_NEW_DOMAIN.md` (이미 web/ai-agent에 포함) |

---

### Step 7: 템플릿 적용 (Node.js 스크립트)

Step 5의 매핑표와 Step 6의 파일 목록을 config.json으로 만들어 `apply.js`를 실행한다.

**7-1. config.json 생성**

프로젝트 루트에 임시 config.json을 Write한다:

```json
{
  "projectRoot": "{프로젝트 절대 경로}",
  "projectType": "{Step 1에서 선택한 유형}",
  "mode": "new",
  "placeholders": {
    "PROJECT_NAME": "{Step 5 매핑표 값}",
    "PROJECT_DESCRIPTION": "...",
    "DOMAIN_NAME": "...",
    "SERVER_PORT": "...",
    "CLIENT_PORT": "...",
    "DB_TYPE": "...",
    "API_URL_LOCAL": "...",
    "TECH_STACK_BACKEND": "...",
    "TECH_STACK_FRONTEND": "..."
  },
  "optional": {
    "sqlite": false,
    "chat": false
  },
  "excludeTemplates": []
}
```

| 필드 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `mode` | `"new"` \| `"existing"` | `"new"` | 프로젝트 모드. 기존 프로젝트는 `"existing"` |
| `excludeTemplates` | `string[]` | `[]` | 기존 모드에서 제외할 템플릿 상대 경로 목록 (예: `["docs/server/UV_SETUP.md"]`) |
```

**7-2. 스크립트 실행**

```bash
# 신규 프로젝트 (기본값)
node ~/.opal/skills/opal-project-init/scripts/apply.js --config {config.json 경로}

# 기존 프로젝트
node ~/.opal/skills/opal-project-init/scripts/apply.js --config {config.json 경로} --mode existing
```

> `--mode` CLI 옵션은 config.json의 `mode` 필드보다 우선한다. 둘 다 없으면 기본값 `"new"`.

스크립트가 자동으로:
- common/ 템플릿 → `{프로젝트루트}/docs/`
- platform/ 템플릿 → `{프로젝트루트}/CLAUDE.md`, `GEMINI.md`, `.cursorrules`
- {유형}/ 템플릿 → `{프로젝트루트}/docs/`
- optional/ 템플릿 → 조건에 따라 포함/제외
- opal/ 템플릿 → `{프로젝트루트}/.opal/AGENT.md`, `.opal/MEMORY.md` (PM 프로필)

**7-3. dry-run (미리보기)**

```bash
node ~/.opal/skills/opal-project-init/scripts/apply.js --config {config.json 경로} --dry-run
```

**7-4. 결과 확인**

실행 완료 후 `{프로젝트루트}/.opal-project-init-result.json`에 결과가 저장된다.

**폴백**: Node.js가 없는 환경에서는 AI가 직접 Read → 치환 → Write로 수행한다.

**저장 경로 매핑**:
- `templates/common/docs/{파일}` → `{프로젝트루트}/docs/{파일}`
- `templates/{유형}/docs/{파일}` → `{프로젝트루트}/docs/{파일}`
- `templates/optional/docs/{파일}` → `{프로젝트루트}/docs/{파일}`
- `templates/common/platform/CLAUDE.md` → `{프로젝트루트}/CLAUDE.md`
- `templates/common/platform/GEMINI.md` → `{프로젝트루트}/GEMINI.md`
- `templates/common/platform/.cursorrules` → `{프로젝트루트}/.cursorrules`
- `templates/common/opal/AGENT.md` → `{프로젝트루트}/.opal/AGENT.md`
- `templates/common/opal/MEMORY.md` → `{프로젝트루트}/.opal/MEMORY.md`

**기존 파일 처리**:

| 모드 | 파일 유형 | 동작 |
|------|----------|------|
| new | 모든 파일 | 기존 파일이 있으면 사용자에게 덮어쓰기 확인 |
| existing | `CLAUDE.md` | 기존 파일 `.bak` 백업 후, OPAL 마커 기반 병합 (부트스트래퍼 갱신 + 기존 사용자 내용 보존 + 새 프로젝트 섹션 추가) |
| existing | `GEMINI.md`, `.cursorrules` | 기존 파일 `.bak` 백업 후, 기존 내용 끝에 구분선(`---`) + 새 내용 추가. 사용자에게 수동 정리 안내 |
| existing | `docs/**` 파일 | 이미 존재하면 건너뛰기 (덮어쓰지 않음), 없는 파일만 새로 생성 |
| existing | `.opal/AGENT.md` | 이미 존재하면 건너뛰기 (PM 커스터마이징 보존), 없으면 새로 생성 |
| existing | `.opal/MEMORY.md` | 이미 존재하면 건너뛰기, 없으면 새로 생성 |
| existing | `excludeTemplates` 목록 | 해당 파일은 완전히 건너뛰기 |

---

### Step 8: 완료 보고

```
---
opal-project-init 완료

프로젝트: {PROJECT_NAME}
유형: {PROJECT_TYPE}
기술 스택: {TECH_STACK_BACKEND} + {TECH_STACK_FRONTEND}

생성된 파일:
- docs/INDEX.md
- docs/server/ ({N}개)
- docs/client/ ({M}개)
- CLAUDE.md, GEMINI.md, .cursorrules
- .opal/AGENT.md (PM 프로필)
- .opal/MEMORY.md (메모리 인덱스)

다음 단계:
1. .opal/AGENT.md에서 PM 프로필을 커스터마이징 (페르소나, 의사결정 원칙, 금지사항 등)
2. docs/INDEX.md에서 문서 구조 확인
3. CLAUDE.md의 컨벤션 섹션 검토 및 커스터마이징
4. docs/server/ENVIRONMENT.md를 참고하여 .env.local 설정
5. 개발 시작!
---
```
