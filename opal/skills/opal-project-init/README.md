# opal-project-init

프로젝트 문서 및 AI 지시 파일을 자동 생성하는 OPAL 스킬.

## 개요

신규 또는 기존 프로젝트에서 인터뷰(또는 코드 자동 분석)를 통해 프로젝트 정보를 수집하고, 구조화된 문서를 자동 생성합니다.

- **신규 프로젝트**: 인터뷰 → context7 조회 → 템플릿 치환 → 파일 생성
- **기존 프로젝트**: 코드 자동 분석 → 확인/보정 인터뷰 → context7 조회 → 템플릿 필터링 → 파일 생성/병합
- docs/ 하위에 서버/클라이언트 가이드 문서 생성
- LLM 플랫폼별 AI 지시 파일 생성 (CLAUDE.md, GEMINI.md, .cursorrules)
- context7 MCP로 최신 라이브러리 버전/설정 반영

## 트리거

- "프로젝트 초기 셋팅"
- "프로젝트 스캐폴드"
- "프로젝트 시작"
- "새 프로젝트 문서 만들어줘"
- "프로젝트 문서 생성"
- "기존 프로젝트 문서화"
- "프로젝트 문서 만들어줘"
- "docs 생성"
- "프로젝트에 문서 추가"

## 모드

### 신규 프로젝트 모드 (기본)

처음부터 인터뷰를 진행하여 모든 프로젝트 정보를 수집합니다.

1. **Step 0**: 모드 선택 (소스 코드 존재 여부 자동 판별)
2. **Step 1~3**: 프로젝트 유형, 기본 정보, 특별 기능 인터뷰
3. **Step 4**: context7 MCP로 최신 기술 정보 조회
4. **Step 5**: 플레이스홀더 매핑표 작성 및 확인
5. **Step 6~7**: 템플릿 결정 및 적용
6. **Step 8**: 완료 보고

### 기존 프로젝트 모드

이미 코드가 있는 프로젝트에서 docs/ 문서와 AI 지시 파일을 추가합니다.

1. **Step 0**: 모드 선택 (소스 코드가 있으면 기존 모드 제안)
2. **Step 0-A**: 코드 자동 분석
   - `package.json`, `pyproject.toml`, `go.mod` 등에서 기술 스택 추론
   - `.env`, `docker-compose.yml`에서 포트/DB 정보 추출
   - `README.md`, `CLAUDE.md`, `.cursorrules`, `GEMINI.md`에서 기존 설정 파악
   - `docs/` 기존 문서 목록 확인 (중복 방지)
3. **Step 0-B**: 확인/보정 인터뷰 (분석 결과를 보여주고 수정만 요청)
4. **Step 4~8**: 신규 모드와 동일 (context7 조회, 매핑, 템플릿 적용, 완료 보고)

**기존 모드 특별 동작**:

- **템플릿 필터링**: 기술 스택과 불일치하는 템플릿 자동 제외 (예: Python이 아니면 UV_SETUP.md 제외)
- **기존 docs 보존**: `docs/` 에 이미 존재하는 파일은 건너뛰고 없는 파일만 생성
- **CLAUDE.md 병합**: OPAL 마커(`# === OPAL START ===`) 기반 병합 -- 부트스트래퍼 갱신 + 기존 사용자 내용 보존
- **GEMINI.md / .cursorrules 병합**: 기존 내용 끝에 구분선 + 새 내용 추가 (수동 정리 안내)
- **백업**: 기존 파일 수정 전에 `.bak` 백업 자동 생성

## 인터뷰 흐름

### Round 0: 프로젝트 유형 (신규 모드)
- web / ai-agent / data / custom

### Round 1: 기본 정보 (4개 질문, 신규 모드)
- 프로젝트명 (영어/한글/설명)
- 기술 스택 (백엔드/프론트엔드/DB)
- 포트 및 도메인
- 아키텍처 (단일/멀티 도메인)

### Round 2: 특별 기능 (신규 모드)
- 채팅/메시징, SQLite 로컬 개발, 인증/권한

### 확인/보정 인터뷰 (기존 모드)
- 자동 분석 결과를 한눈에 보여주고, 수정이 필요한 항목만 입력받음

## 생성 결과

```
{프로젝트루트}/
├── CLAUDE.md              # Claude Code AI 지시 파일
├── GEMINI.md              # Gemini CLI AI 지시 파일
├── .cursorrules           # Cursor AI 규칙
└── docs/
    ├── INDEX.md           # 문서 인덱스
    ├── server/
    │   ├── README.md
    │   ├── ENVIRONMENT.md
    │   ├── PROJECT_STRUCTURE.md
    │   ├── DOMAIN_GUIDE.md      (web/ai-agent)
    │   ├── UV_SETUP.md          (Python)
    │   ├── SQLITE_SETUP.md      (조건부)
    │   └── HOW_TO_REQUEST_NEW_DOMAIN.md (web/ai-agent)
    └── client/
        ├── README.md
        ├── ARCHITECTURE.md
        ├── ENVIRONMENT.md
        ├── PROJECT_STRUCTURE.md
        ├── OPENAPI_GUIDE.md
        ├── COMMON_ISSUES.md
        └── CHAT_UI_GUIDE.md     (조건부)
```

## apply.js 사용법

```bash
# 신규 프로젝트 (기본)
node apply.js --config config.json

# 기존 프로젝트
node apply.js --config config.json --mode existing

# 미리보기
node apply.js --config config.json --dry-run
```

### config.json 형식

```json
{
  "projectRoot": "/path/to/project",
  "projectType": "web",
  "mode": "new",
  "placeholders": { "PROJECT_NAME": "my-project", ... },
  "optional": { "sqlite": false, "chat": false },
  "excludeTemplates": []
}
```

| 필드 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `projectRoot` | string | (필수) | 프로젝트 절대 경로 |
| `projectType` | string | `"custom"` | web / ai-agent / data / custom |
| `mode` | string | `"new"` | `"new"` 또는 `"existing"` |
| `placeholders` | object | `{}` | 플레이스홀더 키-값 매핑 |
| `optional` | object | `{}` | 조건부 문서 포함 여부 |
| `excludeTemplates` | string[] | `[]` | 기존 모드에서 제외할 템플릿 상대 경로 |

## 프로젝트 유형별 차이

| 유형 | 추가 문서 | 설명 |
|------|----------|------|
| web | DOMAIN_GUIDE (범용), HOW_TO_REQUEST | Controller-Service-Repository 패턴 |
| ai-agent | DOMAIN_GUIDE (에이전트), HOW_TO_REQUEST | Agent-Tool-Safety Level 패턴 |
| data | 공통만 | 데이터 분석/파이프라인 |
| custom | 공통만 | 사용자 정의 |

## 플레이스홀더

### 필수 (9개)
`{{PROJECT_NAME}}`, `{{PROJECT_DESCRIPTION}}`, `{{DOMAIN_NAME}}`, `{{SERVER_PORT}}`, `{{CLIENT_PORT}}`, `{{DB_TYPE}}`, `{{API_URL_LOCAL}}`, `{{TECH_STACK_BACKEND}}`, `{{TECH_STACK_FRONTEND}}`

### 조건부 (3개)
`{{SQLITE_DB_PATH}}`, `{{DOMAIN_EXAMPLES}}`, `{{CHAT_API_ENDPOINT}}`

## FAQ

### 기존 프로젝트에 적용할 수 있나요?
네. Step 0에서 "기존 프로젝트" 모드를 선택하면 코드를 자동 분석하고, 이미 있는 docs 파일은 건너뛰며, CLAUDE.md 등 플랫폼 파일은 기존 내용을 보존하면서 병합합니다.

### 기존 CLAUDE.md가 있으면 어떻게 되나요?
기존 모드에서는 `.bak` 백업 후 OPAL 마커 기반으로 병합합니다. OPAL 부트스트래퍼는 최신으로 갱신하고, 사용자가 직접 작성한 내용은 "기존 프로젝트 설정" 섹션에 보존합니다.

### 기존 모드에서 불필요한 문서가 생성되지 않나요?
기술 스택과 불일치하는 템플릿은 자동 제외됩니다. 예를 들어 Python을 사용하지 않으면 UV_SETUP.md가, 프론트엔드가 없으면 docs/client/ 전체가 제외됩니다.

### 기존 docs/ 파일이 덮어써지나요?
아니요. 기존 모드에서는 이미 존재하는 docs 파일은 건너뛰고, 없는 파일만 새로 생성합니다.

### 백업 파일은 어디에 생성되나요?
기존 모드에서 플랫폼 파일(CLAUDE.md, GEMINI.md, .cursorrules)이 이미 존재하면, 같은 위치에 `.bak` 확장자로 백업됩니다 (예: `CLAUDE.md.bak`).

### 템플릿을 커스터마이징하고 싶어요
`~/.opal/skills/opal-project-init/templates/` 아래 파일을 직접 수정하면 됩니다.

### 다시 실행하면 어떻게 되나요?
신규 모드에서는 기존 파일 덮어쓰기 전에 확인을 요청합니다. 기존 모드에서는 docs 파일은 건너뛰고 플랫폼 파일은 병합합니다.

### context7가 없는 환경에서도 동작하나요?
네. context7 조회에 실패하면 인터뷰에서 수집한 정보만으로 문서를 생성합니다.
