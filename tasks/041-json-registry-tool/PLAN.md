# PLAN: OPAL JSON 레지스트리 + 파싱 도구 개발

> 작성일: 2026-03-28
> 입력: TASK.md
> 출력: PLAN.md

## 1. 코드 분석

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `opal/core/references/skills.md` | 현재 스킬 레지스트리 (마크다운) | 아니오 (유지) |
| `opal/core/references/skill-guide.md` | 스킬 브리핑 가이드 | 아니오 (유지) |
| `scripts/install-mac.sh` | 프레임워크 설치 스크립트 | 예 (node 체크 + tools 배포 추가) |
| `opal/core/AGENT.md` | 에이전트 핵심 정의 | 아니오 (향후 연동 대상, 이번엔 변경 없음) |

### 현재 구현

**스킬 레지스트리 (skills.md)**:
- 마크다운 테이블 3개 섹션: 프레임워크 스킬 (18개), OPAL 전용 스킬 (5개), 커뮤니티 스킬 (31개)
- 트리거는 텍스트로 기술 (정규식 아님). LLM이 "읽고 해석"하여 매칭
- 탐색 경로는 프로즈 텍스트로 기술: `{프로젝트}/.opal/skills/{skill}/SKILL.md` → `~/.opal/skills/{skill}/SKILL.md`
- 기술 스택별 추천 스킬 매핑 테이블도 포함

**설치 스크립트 (install-mac.sh)**:
- Bash 스크립트, `set -euo pipefail` 사용
- `detect_framework_root()` → `install_opal()` → `install_mcp()` 순서
- `install_dir()` 함수로 디렉토리 복사 (신규/덮어쓰기)
- 현재 `opal/tools/` 디렉토리는 존재하지 않음 — 신규 생성 필요
- Node.js 체크 로직 없음

**JSON 전환 대상 스킬 목록** (skills.md에서 추출, 커뮤니티 제외):

프레임워크 스킬 (18개):

| 스킬명 | 약어 | 트리거 | 유형 |
|--------|------|--------|------|
| otp-dev | otpd | "otp-dev", "otpd", Full Task 명시 요청 | otp |
| otp-dev-short | otpds | "otp-dev-short", "otpds", 코드 변경 기본 진입점 | otp |
| otp-wf | otpwf | "otp-wf", "otpwf" | otp |
| otp-write | otpw | "otp-write", "otpw", "문서 작성", "보고서", "가이드", "기획서", "명세서", "설계서", "정책서", "PRD 작성" | otp |
| otp-write-tech | otpwt | "otp-write-tech", "otpwt", "기획 문서 세트", "기술 산출물 작성", "기획 문서 검토", "기획 문서 최신화" | otp |
| dtp-task | — | 오케스트레이터 디스패치 전용 | dtp |
| dtp-analysis | — | 오케스트레이터 디스패치 전용 | dtp |
| dtp-plan | — | 오케스트레이터 디스패치 전용 | dtp |
| dtp-todo | — | 오케스트레이터 디스패치 전용 | dtp |
| dtp-test-scenario | — | 오케스트레이터 디스패치 전용 | dtp |
| dtp-execute | — | 오케스트레이터 디스패치 전용 | dtp |
| dtp-wireframe | — | 오케스트레이터 디스패치 전용 | dtp |
| dtp-qa | — | 오케스트레이터 디스패치 전용 | dtp |
| api-analyzer | — | "API 분석", "API 명세서", "API 검토", "외부 API 조사" | standalone |
| interview | — | "검토해줘", "확인해줘", "궁금한 거 물어봐" | standalone |
| wireframe-builder | — | "와이어프레임", "화면 설계", "UI 설계", "화면 구조", "화면 도출" | standalone |
| ui-designer | — | "UI 구현", "UI 만들어줘", "화면 구현", "wireframe 구현", "프로토타입" | standalone |
| web-to-markdown | — | "URL 읽어줘", "사이트 내용 정리", "웹 페이지 마크다운" | standalone |

OPAL 전용 스킬 (5개):

| 스킬명 | 약어 | 트리거 | 유형 |
|--------|------|--------|------|
| opal-onboarding | — | 자동 (identity.md 없을 때) | opal |
| opal-project-init | opi | "opal-project-init", "opi", "프로젝트 초기 셋팅", "프로젝트 시작" | opal |
| opal-project-dev-pilot | opdp | "opal-project-dev-pilot", "opdp", "프로젝트 개발 시작", "PRD 작성" | opal |
| opal-orchestrator | — | 자동 (.opal/AGENT.md 있을 때) | opal |
| opal-skill-manager | — | "스킬 검색", "스킬 찾아줘", "스킬 설치해줘", "설치된 스킬", "스킬 삭제" | opal |

### 영향 범위

- `install-mac.sh`에 `opal/tools/` 배포 로직 추가 필요 → 기존 `install_opal()` 함수 내에 추가
- 현재 `AGENT.md`의 쌍슬래시 커맨드 처리는 skills.md를 참조 — 향후 JSON 도구 호출로 전환 가능하지만 이번 범위에서는 JSON 도구를 "만들기만" 함
- `opal/tools/`는 `~/.opal/tools/`로 배포될 예정

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| 1 | `opal/tools/opal-skills-registry.json` | 스킬 메타데이터 레지스트리 (SSOT) |
| 2 | `opal/tools/skill-registry.js` | Node.js CLI 파싱 도구 (match/get/list/validate) |
| 3 | `opal/tools/check-env.js` | Node.js 환경 체크 도구 |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 4 | `scripts/install-mac.sh` | `opal/tools/` → `~/.opal/tools/` 배포 로직 추가 + check-env.js 호출 |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | JSON 레지스트리 스키마 설계 + 데이터 작성 | `opal/tools/opal-skills-registry.json` | 보통 |
| 2 | CLI 파싱 도구 구현 | `opal/tools/skill-registry.js` | 보통 |
| 3 | 환경 체크 도구 구현 | `opal/tools/check-env.js` | 쉬움 |
| 4 | 설치 스크립트 수정 | `scripts/install-mac.sh` | 쉬움 |

### 핵심 설계

#### 1. JSON 스키마 (`opal-skills-registry.json`)

```json
{
  "$schema": "opal-skills-registry-v1",
  "version": "1.0.0",
  "updated_at": "2026-03-28",
  "skills": [
    {
      "name": "otp-dev",
      "type": "otp",
      "alias": "otpd",
      "description": "Full Task 오케스트레이터",
      "triggers": ["^otp-dev$", "^otpd$", "(?i)full\\s*task"],
      "paths": [
        "{project}/.opal/skills/otp-dev/SKILL.md",
        "~/.opal/skills/otp-dev/SKILL.md"
      ],
      "domain": "dev",
      "dispatched_by": null,
      "pipeline": "TASK → ANALYSIS → PLAN+TEST-SCENARIO → TODO → EXECUTE"
    }
  ]
}
```

**유형별 스키마 필드**:

| 유형 | 공통 필드 | 고유 필드 |
|------|----------|----------|
| otp | name, type, alias, description, triggers, paths | domain, pipeline |
| dtp | name, type, alias, description, triggers, paths | stage, dispatched_by |
| standalone | name, type, alias, description, triggers, paths | (없음) |
| opal | name, type, alias, description, triggers, paths | auto_trigger |

**공통 필드**:
- `name`: string — 스킬 정식명
- `type`: "otp" | "dtp" | "standalone" | "opal" — 스킬 유형
- `alias`: string | null — 약어 (없으면 null)
- `description`: string — 한 줄 설명
- `triggers`: string[] — 정규식 패턴 배열. 사용자 입력과 매칭
- `paths`: string[] — SKILL.md 탐색 경로 (우선순위 순서)

**otp 고유 필드**:
- `domain`: "dev" | "wf" | "write" | "write-tech" — 도메인
- `pipeline`: string — 파이프라인 단계 요약

**dtp 고유 필드**:
- `stage`: string — 담당 단계명 (예: "TASK", "PLAN", "EXECUTE")
- `dispatched_by`: string[] — 이 스킬을 디스패치하는 오케스트레이터 목록

**opal 고유 필드**:
- `auto_trigger`: string | null — 자동 실행 조건 (예: "identity.md 없을 때")

**triggers 정규식 설계 원칙**:
- otp 스킬: `^정식명$`, `^약어$`, 자연어 패턴 (예: `(?i)full\s*task`)
- dtp 스킬: `^정식명$` 만 (디스패치 전용이므로 자연어 불필요)
- standalone 스킬: `^정식명$` + 자연어 키워드 패턴
- opal 스킬: `^정식명$`, `^약어$` + 자연어 패턴

#### 2. CLI 도구 (`skill-registry.js`)

```
사용법:
  node skill-registry.js match <input>      사용자 입력에서 스킬 매칭
  node skill-registry.js get <name>         스킬명으로 메타데이터 조회
  node skill-registry.js list [options]     스킬 목록 조회
  node skill-registry.js validate           레지스트리 검증
```

**모듈 구조** (단일 파일, 내부 함수 분리):

```javascript
// === 데이터 로딩 ===
function loadRegistry()
// fs.readFileSync로 opal-skills-registry.json 로드
// 반환: { skills: [...] }
// JSON 위치: 같은 디렉토리의 opal-skills-registry.json (path.join(__dirname, ...))

// === match 명령 ===
function extractAlias(input)
// 입력에서 // 뒤의 약어 추출 (위치 무관)
// 정규식: /\/\/(\S+)/ — 입력 전체에서 //를 찾아 뒤의 공백 아닌 문자열 추출
// 반환: { alias: string, cleanInput: string } 또는 { alias: null, cleanInput: string }

function matchByAlias(skills, alias)
// skills 배열에서 alias 또는 name이 정확 일치하는 스킬 반환
// 반환: skill 객체 또는 null

function matchByTriggers(skills, input)
// skills 배열의 triggers 정규식을 순회하며 input과 매칭
// 매칭 시 첫 번째 매칭 스킬 반환
// 반환: skill 객체 또는 null

function match(input)
// 1. extractAlias(input) → alias 있으면 matchByAlias
// 2. alias 없으면 matchByTriggers
// 출력: JSON { found: true, name, type, alias, path, domain } 또는 { found: false, input }

// === get 명령 ===
function get(name)
// name으로 스킬 메타데이터 전체 반환
// 출력: JSON (스킬 객체 전체)

// === list 명령 ===
function list(options)
// options: { type?, domain? }
// 필터링된 스킬 목록 반환
// --type=otp, --domain=dev 등
// 출력: JSON 배열

// === validate 명령 ===
function validate()
// 1. JSON 구조 검증 (필수 필드 존재)
// 2. 정규식 컴파일 테스트 (모든 triggers의 new RegExp() 성공)
// 3. 경로 존재 확인 (~ 확장 후 fs.existsSync)
// 4. alias 중복 검증
// 5. name 중복 검증
// 출력: JSON { valid: true, errors: [], warnings: [] }

// === CLI 라우터 ===
// process.argv 파싱하여 명령 분기
// 출력은 항상 JSON.stringify (다른 도구에서 파싱 가능)
```

**match 동작 흐름**:
```
입력: "로그인 버그 //otpds"
  1. extractAlias → { alias: "otpds", cleanInput: "로그인 버그" }
  2. matchByAlias(skills, "otpds") → otp-dev-short
  3. 반환: { found: true, name: "otp-dev-short", path: "~/.opal/skills/otp-dev-short/SKILL.md", ... }

입력: "//otpds 로그인 버그"
  1. extractAlias → { alias: "otpds", cleanInput: "로그인 버그" }
  2. matchByAlias → otp-dev-short
  3. 동일 결과

입력: "로그인 버그 수정해줘"
  1. extractAlias → { alias: null, cleanInput: "로그인 버그 수정해줘" }
  2. matchByTriggers → 매칭 없음 (개발 작업은 기본 otpds지만 자연어 폴백은 별도 정책)
  3. 반환: { found: false, input: "로그인 버그 수정해줘" }

입력: "API 분석해줘"
  1. extractAlias → { alias: null }
  2. matchByTriggers → api-analyzer의 trigger "(?i)API\\s*(분석|명세서|검토)" 매칭
  3. 반환: { found: true, name: "api-analyzer", ... }
```

**출력 형식 (모든 명령 공통)**:
- stdout에 JSON 출력 (UTF-8)
- 성공 시 exit code 0
- 실패 시 exit code 1 + stderr에 에러 메시지

#### 3. 환경 체크 (`check-env.js`)

```javascript
// Node.js 버전 체크 (최소 v18 — fs, path, process 내장 모듈 안정화)
// 출력: JSON { node: true, version: "v20.x.x" } 또는 { node: false, error: "..." }
// exit code: 0 (성공) / 1 (실패)
```

이 파일은 단독 실행도 가능하고, `install-mac.sh`에서도 호출한다.

#### 4. 설치 스크립트 수정 (`install-mac.sh`)

`install_opal()` 함수 내에 tools 배포 단계 추가:

```bash
# ── 도구 (opal/tools/ → ~/.opal/tools/) ──
install_dir "$opal_dir/tools" "$opal_home/tools" "OPAL 도구"
```

`install_opal()` 함수 시작 부근의 `clean_dirs` 배열에 `"tools"` 추가:

```bash
local clean_dirs=("skills" "agents" "references" "community-skills" "templates" "tools")
```

Node.js 체크는 `check-env.js` 실행으로 수행:

```bash
# ── Node.js 환경 체크 ──
if command -v node &>/dev/null; then
    local node_check
    node_check="$(node "$opal_dir/tools/check-env.js" 2>/dev/null)" || true
    if echo "$node_check" | /usr/bin/python3 -c "import json,sys; d=json.load(sys.stdin); sys.exit(0 if d.get('node') else 1)" 2>/dev/null; then
        success "Node.js 환경 확인: $(node --version)"
    else
        warn "Node.js 버전이 낮습니다. v18 이상 권장"
    fi
else
    warn "Node.js가 설치되어 있지 않습니다. opal/tools/ 기능이 제한됩니다"
    info "설치: https://nodejs.org/ 또는 brew install node"
fi
```

### 의존성 및 환경 변경

- **추가 패키지 없음** — Node.js 내장 모듈만 사용 (`fs`, `path`, `process`)
- **Node.js 최소 v18** — 안정적인 내장 모듈 지원
- **새 디렉토리**: `opal/tools/` (소스), `~/.opal/tools/` (배포)

### 테스트 전략

| 테스트 | 방법 | 성공 기준 |
|--------|------|----------|
| JSON 유효성 | `node -e "JSON.parse(require('fs').readFileSync('opal-skills-registry.json','utf8'))"` | 파싱 에러 없음 |
| match (약어, 앞) | `node skill-registry.js match "//otpds 로그인"` | `found: true, name: "otp-dev-short"` |
| match (약어, 뒤) | `node skill-registry.js match "로그인 //otpds"` | `found: true, name: "otp-dev-short"` |
| match (약어, 중간) | `node skill-registry.js match "로그인 //otpds 수정"` | `found: true, name: "otp-dev-short"` |
| match (자연어) | `node skill-registry.js match "API 분석해줘"` | `found: true, name: "api-analyzer"` |
| match (미매칭) | `node skill-registry.js match "오늘 날씨"` | `found: false` |
| get (존재) | `node skill-registry.js get otp-dev` | 스킬 메타데이터 전체 출력 |
| get (미존재) | `node skill-registry.js get nonexistent` | 에러 메시지 |
| list (전체) | `node skill-registry.js list` | 전체 스킬 목록 |
| list (필터) | `node skill-registry.js list --type=otp` | otp 유형만 출력 |
| validate | `node skill-registry.js validate` | `valid: true` |
| check-env | `node check-env.js` | `node: true, version: "v2x.x.x"` |
| install 배포 | `./scripts/install-mac.sh` 실행 후 `~/.opal/tools/` 확인 | 3개 파일 존재 |

## 3. 실행 체크리스트

> 총 4개 Step | 실행 모드: 단순

### Step 1: JSON 레지스트리 작성
- [ ] 완료
- **파일**: `opal/tools/opal-skills-registry.json`
- **작업 내용**:
  - `opal/tools/` 디렉토리 생성
  - 스키마 버전/메타 헤더 작성
  - 프레임워크 스킬 18개 + OPAL 전용 스킬 5개 = 총 23개 스킬 데이터 작성
  - 각 스킬의 triggers 정규식 작성 (otp: 정식명+약어+자연어, dtp: 정식명만, standalone: 정식명+자연어, opal: 정식명+약어+자연어/자동조건)
  - paths 배열에 `{project}` 프리픽스 경로 → `~/.opal` 경로 순서로 기재
  - 유형별 고유 필드 (domain, pipeline, stage, dispatched_by, auto_trigger) 기재
- **완료 기준**: `node -e "const d=JSON.parse(require('fs').readFileSync('opal/tools/opal-skills-registry.json','utf8')); console.log(d.skills.length)"` → 23 출력
- **테스트**: JSON.parse 성공 + skills.length === 23
- **실행 방법**: direct
- **의존**: 없음

### Step 2: CLI 파싱 도구 구현
- [ ] 완료
- **파일**: `opal/tools/skill-registry.js`
- **작업 내용**:
  - `loadRegistry()` — 같은 디렉토리의 JSON 로드
  - `extractAlias(input)` — `//` 뒤 약어 추출 (위치 무관)
  - `matchByAlias(skills, alias)` — alias/name 정확 매칭
  - `matchByTriggers(skills, input)` — triggers 정규식 순회 매칭
  - `match(input)` — extractAlias → matchByAlias / matchByTriggers 순서
  - `get(name)` — 스킬 메타데이터 조회
  - `list(options)` — type/domain 필터링
  - `validate()` — JSON 구조 + 정규식 컴파일 + 경로 존재 + alias/name 중복 검증
  - CLI 라우터 (process.argv 파싱)
  - 모든 출력은 JSON.stringify (stdout)
  - 에러는 stderr + exit code 1
- **완료 기준**: 위 테스트 전략의 match/get/list/validate 테스트 전부 통과
- **테스트**: `node opal/tools/skill-registry.js match "//otpds 로그인"` → `found: true`
- **실행 방법**: direct
- **의존**: Step 1

### Step 3: 환경 체크 도구 구현
- [ ] 완료
- **파일**: `opal/tools/check-env.js`
- **작업 내용**:
  - Node.js 버전 확인 (process.version 파싱)
  - 최소 v18 체크
  - JSON 출력 (`{ node: true/false, version: "..." }`)
  - exit code 0/1
- **완료 기준**: `node opal/tools/check-env.js` → `{ "node": true, "version": "v2x.x.x" }` 출력
- **테스트**: 직접 실행하여 출력 확인
- **실행 방법**: direct
- **의존**: 없음

### Step 4: 설치 스크립트 수정
- [ ] 완료
- **파일**: `scripts/install-mac.sh`
- **작업 내용**:
  - `clean_dirs` 배열에 `"tools"` 추가
  - `install_opal()` 함수 내에 `opal/tools/` → `~/.opal/tools/` 배포 단계 추가 (커뮤니티 스킬 배포 전에 배치)
  - Node.js 체크 로직 추가 (`command -v node` + `check-env.js` 실행)
  - `print_summary()` 함수에 tools 경로 표시 추가
- **완료 기준**: `./scripts/install-mac.sh` 실행 후 `~/.opal/tools/` 에 3개 파일 존재
- **테스트**: install 실행 후 `ls ~/.opal/tools/` → `check-env.js`, `opal-skills-registry.json`, `skill-registry.js`
- **실행 방법**: direct
- **의존**: Step 1, 2, 3

## 4. QA 체크리스트

### 기능 테스트
- [ ] match: `//약어` 위치 무관 파싱 (앞, 중간, 뒤)
- [ ] match: alias로 정확 매칭
- [ ] match: name으로 정확 매칭
- [ ] match: 자연어 triggers 정규식 매칭
- [ ] match: 미매칭 시 `found: false` 반환
- [ ] get: 존재하는 스킬 조회
- [ ] get: 미존재 스킬 에러 처리
- [ ] list: 전체 목록 출력
- [ ] list: --type 필터
- [ ] list: --domain 필터
- [ ] validate: 정상 JSON에서 `valid: true`
- [ ] validate: 정규식 컴파일 검증
- [ ] validate: alias/name 중복 검증
- [ ] check-env: 정상 Node.js 환경에서 `node: true`
- [ ] install-mac.sh: tools 디렉토리 정상 배포

### 회귀 테스트
- [ ] install-mac.sh 기존 skills/agents/references 배포 정상 동작
- [ ] install-mac.sh 기존 MCP 설정 정상 동작
- [ ] skills.md 내용 변경 없음 (유지 확인)
- [ ] skill-guide.md 내용 변경 없음 (유지 확인)

### 코드 품질
- [ ] Node.js 외부 패키지 사용 없음 (내장 모듈만)
- [ ] JSON 출력 형식 일관성 (모든 명령이 JSON 반환)
- [ ] 에러 처리: stderr 출력 + exit code 1
- [ ] UTF-8 한글 처리 정상
- [ ] `#!/usr/bin/env node` shebang 포함

### 보안
- [ ] .env, 인증 파일이 .gitignore에 포함되어 있는가
- [ ] 코드에 하드코딩된 토큰/시크릿이 없는가
- [ ] JSON에 민감 정보가 없는가 (경로 템플릿만 포함)

## 5. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 4개 | 단순 |
| 변경 파일 수 | 4개 (신규 3 + 수정 1) | 복잡 |
| 모듈 범위 | 단일 (opal/tools/) + install 스크립트 | 단순 |
| 작업 유형 | 신규 개발 | 복잡 |
| 외부 의존성 | 없음 | 단순 |
| **실행 모드** | **단순** | 변경 파일 4개와 신규 개발이 복잡 기준이나, Step 간 의존이 단순 직선이고 모듈이 단일(tools/)이며 모든 작업이 한 명이 순차 수행 가능하므로 **단순** 적용 |

## 6. 실행 아키텍처 (복잡 모드 시)

해당 없음 (단순 모드).

## 7. 기술 컨텍스트

### 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 런타임 | Node.js v18+ | 없음 (내장 모듈만) |
| 데이터 | JSON | 없음 |
| 설치 | Bash (install-mac.sh) | 없음 |

### 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| 없음 | 외부 라이브러리 미사용으로 MCP 조회 불필요 |

## 8. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| JSON과 skills.md 이중 관리 불일치 | 스킬 추가 시 한쪽만 업데이트할 수 있음 | validate 명령에 skills.md와 JSON 간 스킬 수 비교 경고 추가 검토 (향후) |
| 자연어 triggers 정규식 오매칭 | 의도하지 않은 스킬이 매칭될 수 있음 | 구체적 패턴 사용 + validate에서 triggers 겹침 검사 |
| Node.js 미설치 환경 | tools 기능 사용 불가 | check-env.js 경고 + install-mac.sh에서 안내 (기능 제한, 에러 아님) |
| Windows 경로 호환 | `~` 확장이 Windows에서 다름 | `os.homedir()` 사용 + `path.join()` 으로 OS 무관 경로 생성 |

---

## 9. 추가 변경 (캡틴 검토 반영)

### 9-1. JSON 그룹 구조 전환

플랫 배열을 그룹 구조로 변경:

```json
{
  "groups": {
    "otp": [ ...오케스트레이터... ],
    "dtp": [ ...단계 스킬... ],
    "standalone": [ ...독립 스킬... ],
    "opal": [ ...OPAL 전용... ]
  }
}
```

### 9-2. 커뮤니티 스킬 별도 JSON

커뮤니티는 설치/삭제로 동적 변경되므로 별도 파일로 분리:

```
opal/tools/skill-registry/
├── opal-skills-registry.json       ← 프레임워크 (고정, 소스 관리)
├── community-skills-registry.json   ← 커뮤니티 (동적, 설치/삭제 시 갱신)
└── skill-registry.js               ← 두 JSON 합쳐서 검색
```

커뮤니티 JSON 구조:
```json
{
  "groups": {
    "anthropics": [ ... ],
    "vercel-labs": [ ... ],
    "google-labs-code": [ ... ],
    "trailofbits": [ ... ],
    "getsentry": [ ... ],
    "openai": [ ... ]
  }
}
```

### 9-3. skill-registry.js 수정

- `loadRegistry()`: 두 JSON 파일을 로드하여 합쳐서 반환
- `list`: `--group=otp`, `--group=community`, `--group=community/anthropics` 지원
- community JSON이 없으면 프레임워크만으로 동작 (에러 아님)

### 9-4. skills.md 정리

- 프레임워크/OPAL 스킬 테이블 제거 (JSON이 SSOT)
- 커뮤니티 스킬 테이블 제거 (community JSON이 SSOT)
- 도구 사용법 섹션 추가 (match/get/list/validate CLI 명령어)
- **기술 스택별 추천 매핑 유지** (LLM 맥락 판단 필요)

### 9-5. skill-guide.md 삭제

- 부트스트랩에서 Read하지 않음 (도구가 대체)
- AGENT.md 7단계(스킬 가이드 브리핑) 제거
- 단계 번호 재조정 (기존 4→5, 5→6, 6→7)

### 9-6. AGENT.md 부트스트랩 변경

- 3단계: CLI 도구 존재 확인만 (list 호출 안 함, 컨텍스트 0줄)
- 사용자 요청 시 match/get 호출
- 상세 사용법 및 기술 스택별 추천: skills.md 참조 안내
- Node.js 미설치 시 폴백: skills.md Read
- 7단계(스킬 가이드 브리핑) 삭제

### 9-7. opal-skill-manager 업데이트

skill-manager가 `skills.md`를 직접 참조하던 5곳을 JSON 도구로 대체:

| 기능 | Before | After |
|------|--------|-------|
| 설치된 스킬 확인 | skills.md Read | `skill-registry.js match` |
| 설치 후 등록 | skills.md에 행 추가 | `community-skills-registry.json`에 추가 |
| 설치 목록 조회 | skills.md와 대조 | `skill-registry.js list --group=community` |
| 삭제 후 제거 | skills.md에서 행 삭제 | `community-skills-registry.json`에서 제거 |
| 스킬 인지 경로 | skills.md 참조 | `community-skills-registry.json` 참조 |
