# PLAN: opal-project-init 기존 프로젝트 지원 (모드 분기)

> 작성일: 2026-03-21 | 모드: Short Task | 참조: TASK.md

## 1. 코드 분석

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `skills/opal-project-init/SKILL.md` | 스킬 정의 (8단계 프로세스) | O - 모드 분기 추가 |
| `skills/opal-project-init/scripts/apply.js` | 템플릿 적용 Node.js 스크립트 | O - --mode existing 추가 |
| `skills/opal-project-init/README.md` | 스킬 사용 문서 | O - 기존 프로젝트 모드 문서화 |
| `skills/opal-project-init/templates/common/platform/CLAUDE.md` | CLAUDE.md 템플릿 | X - 수정 불필요 |
| `skills/opal-project-init/templates/**/*` | 전체 템플릿 (20개) | X - 수정 불필요 |

### 현재 구현

**SKILL.md (8단계 플로우)**:
1. Step 1: 프로젝트 유형 인터뷰 (Round 0) -- web/ai-agent/data/custom
2. Step 2: 기본 정보 인터뷰 (Round 1) -- 프로젝트명, 기술 스택, 포트, 아키텍처
3. Step 3: 특별 기능 인터뷰 (Round 2) -- 채팅, SQLite, 인증
4. Step 4: context7 MCP 조회 -- 최신 라이브러리 버전 확인
5. Step 5: 플레이스홀더 매핑표 작성 -- 인터뷰 + context7 결과 합산
6. Step 6: 포함할 템플릿 결정 -- 유형/기능별 필터링
7. Step 7: 템플릿 적용 (apply.js) -- config.json 생성 후 스크립트 실행
8. Step 8: 완료 보고

모든 단계가 **신규 프로젝트 전제** -- 사용자에게 모든 정보를 처음부터 질문하고, 기존 코드 분석 없음.

**apply.js (212줄)**:
- CLI: `--config config.json [--dry-run]`
- 입력: `config.json` (projectRoot, projectType, placeholders, optional)
- 처리: 4단계 순차 적용 (common docs -> platform files -> type docs -> optional docs)
- `replacePlaceholders()`: `{{KEY}}` 패턴을 정규식으로 치환
- `processFile()`: 템플릿 읽기 -> 치환 -> 쓰기 (기존 파일 체크 없이 바로 덮어쓰기)
- 결과: `.opal-project-init-result.json` 저장
- **기존 파일 병합 로직 없음** -- 현재는 무조건 덮어쓰기

**CLAUDE.md 템플릿**: `# === OPAL START ===` ~ `# === OPAL END ===` 마커로 OPAL 부트스트래퍼 구간 식별 가능.

### 영향 범위

- **호출자**: OPAL AGENT.md의 `project-init` 스킬 호출 -> SKILL.md의 프로세스를 AI가 따라감
- **피호출자**: apply.js (SKILL.md Step 7에서 호출), context7 MCP (Step 4)
- **공유 데이터**: config.json (SKILL.md가 생성, apply.js가 소비), 템플릿 디렉토리 (읽기 전용)
- **참조 레지스트리**: `opal/core/references/skills.md`에 트리거 목록 등록 -- 트리거 추가 시 갱신 필요

## 2. 구현 계획

### 변경 파일

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `skills/opal-project-init/SKILL.md` | Step 0 모드 분기 추가, 기존 모드 자동 분석 단계 추가, 인터뷰 확인/보정 모드, 템플릿 필터링 로직, 트리거 확장 |
| 2 | `skills/opal-project-init/scripts/apply.js` | `--mode existing` 옵션, 기존 파일 백업(.bak), CLAUDE.md 병합 로직, GEMINI.md/.cursorrules 병합 로직 |
| 3 | `skills/opal-project-init/README.md` | 기존 프로젝트 모드 설명 추가, 트리거 목록 갱신 |

### 핵심 설계

#### 2.1 SKILL.md -- 모드 분기 및 기존 프로젝트 플로우

**Step 0 (신규 추가): 모드 선택**

```markdown
### Step 0: 모드 선택

프로젝트 루트에 소스 코드가 존재하는지 확인한다.
- package.json, pyproject.toml, go.mod, Cargo.toml 등 존재 여부를 Glob으로 확인
- 소스 코드가 있으면 "기존 프로젝트" 모드를 제안, 없으면 "신규 프로젝트" 진행

[모드 선택]
  1. 신규 프로젝트 — 처음부터 인터뷰 (기존 Step 1~8 동일)
  2. 기존 프로젝트 — 코드 자동 분석 → 확인/보정 인터뷰
```

**기존 모드 전용 단계 (Step 0-A: 자동 분석)**

코드를 스캔하여 플레이스홀더를 자동 추론:

**소스 코드 분석**:
- `package.json`: name, dependencies (프론트엔드 스택 추론)
- `pyproject.toml` / `requirements.txt`: 백엔드 스택 추론
- `go.mod` / `Cargo.toml`: 기타 백엔드 추론
- 디렉토리 구조: `src/`, `app/`, `server/`, `client/` 등으로 프로젝트 유형 추론
- 포트 번호: `.env`, `docker-compose.yml`, 설정 파일에서 추출

**LLM 플랫폼 파일 분석**:
- `README.md`: 프로젝트 설명, 기술 스택, 설치 방법 추출 → `PROJECT_NAME`, `PROJECT_DESCRIPTION` 보정
- `CLAUDE.md`: 기존 코드 컨벤션, 아키텍처 규칙 파악 → 새 문서 생성 시 기존 규칙 반영, OPAL 마커 존재 여부 확인
- `.cursorrules`: 기존 Cursor 규칙 파악 → 병합 시 충돌 방지
- `GEMINI.md`: 기존 Gemini 설정 파악 → 병합 시 충돌 방지
- `docs/` 디렉토리: 기존 문서 구조 파악 → 이미 존재하는 문서는 생성하지 않음

**자동 추론 결과 -> 플레이스홀더 매핑**:

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

**기존 모드 인터뷰 (확인/보정형)**

기존 Step 1~3의 질문을 자동 분석 결과로 미리 채운 뒤, 사용자에게 확인만 요청:

```
[자동 분석 결과 확인]

아래는 프로젝트 코드를 분석한 결과입니다. 수정이 필요한 항목만 알려주세요.

- 프로젝트명: my-project (영어) / (한글명을 입력해주세요)
- 기술 스택: Python/FastAPI + Next.js + PostgreSQL
- 포트: 백엔드 8000 / 프론트엔드 3000
- 유형: web (멀티 도메인)
- 한 줄 설명: (입력해주세요)

수정할 항목이 있으면 알려주세요. 없으면 "확인"이라고 답해주세요.
```

**템플릿 필터링 (기존 모드 전용)**

기술 스택 불일치 시 특정 템플릿을 자동 제외:
- 백엔드가 Python 계열이 아니면: `UV_SETUP.md` 제외
- 프론트엔드가 없으면: `docs/client/**` 전체 제외
- 백엔드가 없으면: `docs/server/**` 전체 제외
- DB가 SQLite를 포함하지 않으면: `SQLITE_SETUP.md` 제외

**트리거 확장**:
기존 triggers에 추가:
- "기존 프로젝트 문서화"
- "프로젝트 문서 만들어줘"
- "docs 생성"
- "프로젝트에 문서 추가"

#### 2.2 apply.js -- 기존 파일 병합 로직

**새 CLI 옵션**:
```
node apply.js --config config.json [--mode existing] [--dry-run]
```

**config.json 확장**:
```json
{
  "mode": "new",           // "new" (기본) | "existing"
  "excludeTemplates": [],  // 기존 모드에서 제외할 템플릿 상대 경로 목록
  ...기존 필드
}
```

**기존 파일 처리 로직 (`--mode existing` 시)**:

1. **백업**: 기존 파일이 존재하면 `.bak` 확장자로 백업 생성 (예: `CLAUDE.md` -> `CLAUDE.md.bak`)

2. **CLAUDE.md 병합**:
   - 기존 파일에서 `# === OPAL START ===` ~ `# === OPAL END ===` 구간 추출
   - 기존 파일의 OPAL 구간 이후 사용자 내용 추출
   - 템플릿의 OPAL 구간 + 템플릿의 프로젝트 섹션 + 기존 사용자 내용을 병합
   - 병합 순서: OPAL 부트스트래퍼(템플릿) -> 프로젝트 정보(템플릿 치환) -> 기존 사용자 내용(원본 보존)

3. **GEMINI.md / .cursorrules 병합**:
   - 기존 파일이 있으면 백업 후, 기존 내용 끝에 구분선(`---`) + 새 내용 추가
   - 사용자에게 수동 정리 안내

4. **일반 docs 파일**: 기존 파일이 있으면 건너뛰기 (덮어쓰지 않음), 없는 파일만 생성

5. **excludeTemplates 처리**: config.json의 excludeTemplates 목록에 있는 파일은 건너뛰기

**코드 변경 포인트 (apply.js)**:

```javascript
// main()에서 mode 파싱 추가
const modeIdx = args.indexOf("--mode");
const mode = modeIdx !== -1 ? args[modeIdx + 1] : "new";

// config.json에서 excludeTemplates 읽기
const { ..., excludeTemplates = [] } = config;

// 새 함수: backupFile(filePath)
function backupFile(filePath) {
  if (fs.existsSync(filePath)) {
    fs.copyFileSync(filePath, filePath + ".bak");
    console.log(`  BACKUP: ${filePath} -> ${filePath}.bak`);
  }
}

// 새 함수: mergeClaudeMd(existingPath, newContent)
function mergeClaudeMd(existingPath, newContent) {
  const existing = fs.readFileSync(existingPath, "utf-8");
  const opalStartMarker = "# === OPAL START ===";
  const opalEndMarker = "# === OPAL END ===";

  // 템플릿에서 OPAL 구간 + 프로젝트 섹션 추출
  // 기존 파일에서 OPAL 구간 외 사용자 내용 추출
  // 병합: 새 OPAL 구간 + 새 프로젝트 섹션 + 기존 사용자 내용
  ...
}

// processFile 분기: mode === "existing"이면 기존 파일 체크
function processFile(templatePath, destPath, placeholders, dryRun, mode) {
  // ... 기존 로직 ...
  if (mode === "existing" && fs.existsSync(destPath)) {
    // CLAUDE.md이면 mergeClaudeMd 호출
    // 그 외 platform 파일이면 append 병합
    // docs 파일이면 스킵
  }
}
```

#### 2.3 README.md -- 문서 갱신

- "개요" 섹션에 기존 프로젝트 지원 추가
- "트리거" 목록에 새 트리거 추가
- "기존 프로젝트 모드" 섹션 신규 추가 (자동 분석 설명, 인터뷰 차이점, 병합 로직 설명)
- FAQ에 기존 프로젝트 관련 항목 보강

## 3. 실행 체크리스트

- [x] Step 1: SKILL.md 수정 -- Step 0 모드 분기, 자동 분석 단계(Step 0-A), 확인/보정형 인터뷰, 템플릿 필터링 로직, 트리거 확장, config.json 스키마에 mode/excludeTemplates 추가
- [x] Step 2: apply.js 수정 -- `--mode existing` CLI 옵션, backupFile() 함수, mergeClaudeMd() 함수, processFile() mode 분기, excludeTemplates 필터링, 일반 docs 스킵 로직
- [x] Step 3: README.md 수정 -- 기존 프로젝트 모드 섹션 추가, 트리거 목록 갱신, FAQ 보강

## 4. QA 체크리스트

### 기능 테스트
- [x] SKILL.md에 Step 0 모드 분기가 명확히 정의되어 있는가
- [x] 자동 분석 대상 파일 목록(package.json, pyproject.toml 등)이 구체적인가
- [x] 확인/보정형 인터뷰 프롬프트가 사용자 친화적인가
- [x] 템플릿 필터링 규칙이 기술 스택별로 정확한가
- [x] apply.js에 `--mode existing`이 정상 동작하는가 (기존 파일 있는 경우 / 없는 경우)
- [x] CLAUDE.md 병합 시 OPAL 부트스트래퍼가 보존되는가
- [x] 백업 파일(.bak)이 정상 생성되는가
- [x] excludeTemplates 필터링이 동작하는가

### 회귀 테스트
- [x] 기존 신규 프로젝트 플로우(Step 1~8)가 변경 없이 동작하는가
- [x] apply.js에 `--mode` 옵션 없이 실행 시 기존과 동일하게 동작하는가 (기본값 "new")
- [x] config.json에 mode/excludeTemplates 없어도 기존 동작 보장되는가
- [x] 템플릿 파일(.md)은 수정되지 않았는가

### 코드 품질
- [x] apply.js의 새 함수(backupFile, mergeClaudeMd)에 에러 핸들링이 있는가
- [x] SKILL.md의 신규/기존 모드 프로세스가 명확히 분리되어 가독성이 좋은가
- [x] README.md가 양쪽 모드를 모두 설명하는가
- [x] 변경 범위가 `skills/opal-project-init/` 내로 한정되는가
