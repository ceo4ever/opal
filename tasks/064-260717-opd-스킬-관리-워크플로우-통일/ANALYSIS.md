# ANALYSIS: 커뮤니티 스킬 관리 워크플로우 분석

> 작성일: 2026-07-17
> 입력: TASK.md
> 출력: ANALYSIS.md

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | skill-registry.js | `opal/tools/skill-registry/skill-registry.js` | D1·D2 판정·매칭 로직 분석 대상 |
| D-2 | 설계 | skill-commands.md | `opal/core/references/harness/skill-commands.md` | D3 미설치 분기 부재 확인 |
| D-3 | 소스 | opal-skill-manager SKILL.md | `opal/skills/opal-skill-manager/SKILL.md` | D4 설치 명령 및 §6 분석 |
| D-4 | 설계 | community-skills-registry.json | `opal/core/references/community-skills-registry.json` | v2.1 스키마 · 32개 항목 검증 |
| D-5 | 소스 | install-mac.sh | `scripts/install-mac.sh:1033-1366` | F-6 registry 배포 경로 · community-skills 보존 정책 |
| D-6 | 소스 | install/windows.ps1 | `scripts/install/windows.ps1:84-557` | F-6 Windows 동등 배포 로직 |
| D-7 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 파일/폴더 네이밍 규칙 |
| D-8 | 소스 | test-validate.js | `opal/tools/skill-registry/tests/test-validate.js` | 테스트 현황 및 커버리지 분석 |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §2 참조.
> 유형: `기획` / `설계` / `소스` / `외부` 중 택1.

---

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/tools/skill-registry/skill-registry.js` | 스킬 판정·매칭 로직, community 경로 계산 | 예 (D1·D2 해소) | 76-78, 129-135, 212 |
| `opal/core/references/harness/skill-commands.md` | `//` 커맨드 호출 절차 명세 | 예 (D3 SSOT 이관) | 1-44 (미설치 분기 부재) |
| `opal/skills/opal-skill-manager/SKILL.md` | 스킬 검색·설치·관리 워크플로우 | 예 (D4 절차 재작성) | 2-127, §6 (144-152) |
| `opal/core/references/community-skills-registry.json` | 커뮤니티 스킬 메타데이터 | 예 (schema_notes 갱신) | 1-54 |
| `scripts/install-mac.sh` | macOS 설치 스크립트 | 예 (registry 배포 보존 규칙 명시) | 1033, 1352-1366 |
| `scripts/install/windows.ps1` | Windows 설치 스크립트 | 예 (registry 배포 보존 규칙 명시) | 432-433, 551-557 |
| `docs/ARCHITECTURE.md` | 시스템 아키텍처 문서 (npx 언급) | 예 (F-4 제거) | 178, 226 |
| `opal/tools/skill-registry/tests/test-validate.js` | 스킬 레지스트리 단위 테스트 | 아니오 (변경 영향 분석만) | 전체 |

> 근거: `파일:N-M` 포맷.

### 1.2 아키텍처 패턴

#### (1) 스킬 설치 레이아웃

**현재 상태**:
- **Flat 1-depth**: `~/.opal/community-skills/{skillname}/SKILL.md` — 31개 (anthropics/docx → docx/, pdf/, 등)
- **Vendor 중첩**: `~/.opal/community-skills/{vendor}/{skillname}/SKILL.md` — 1개 (obra/brainstorming만)

**Registry 정의**:
- **스킬명 형식**: `{vendor}/{skillname}` (예: `anthropics/pdf`, `obra/brainstorming`) — 32개 항목

**불일치**:
- Flat 31개는 registry 항목 이름(`anthropics/pdf`)과 실제 경로(`~/.opal/community-skills/pdf/`)가 일치하지 않음
- `skill-registry.js:76` `getCommunitySkillPath()` 구현이 `~/.opal/community-skills/{skillName}` 직결 방식 → 인자가 `anthropics/pdf`면 `anthropics/pdf/SKILL.md` 경로 기대
- **근거**: `opal/tools/skill-registry/skill-registry.js:75-77` 함수와 실제 디렉토리 구조 검증 실측

#### (2) 스킬 판정 로직 (3단계 매칭)

1. **matchByAlias()**: 정식명(name) 또는 alias 필드 정확 비교 (`opal/tools/skill-registry/skill-registry.js:129-135`)
2. **matchByTriggers()**: triggers 패턴 정규식 매칭 (fallback) (`skill-registry.js:137-165`)
3. **cleanInput** 폴백: 별도 텍스트 추출 후 재매칭 (`skill-registry.js:200-203`)

**문제점**:
- `matchByAlias()` 구현(`skill-registry.js:129-135`)이 basename 매칭 미지원
- 예: `//pdf 문서 만들어줘` → alias 매칭 실패(anthropics/pdf ≠ pdf) → triggers 매칭 시도 → 성공(정규식) → found:true
- 하지만 `installed: false` 반환 (경로 계산 오류로 인함)

#### (3) Community 스킬 설치 여부 동적 계산

**구현**(`skill-registry.js:206-227`):
```javascript
const skillPath = getCommunitySkillPath(skill.name);
const installed = fs.existsSync(skillPath);  // D1 불일치로 인해 false 반환
```

**결과**: 31개 flat 디렉토리 모두 `installed: false`로 오판

**근거**: `opal/tools/skill-registry/skill-registry.js:208-209` + 실제 파일 존재 검증

### 1.3 의존성 맵

#### skill-registry.js 소비처 (역방향 추적)

| 소비 위치 | 호출 방식 | 용도 |
|-----------|----------|------|
| `opal/core/references/harness/skill-commands.md` | `match "{입력}"` | `//` 커맨드 스킬 검색 (매칭 실행) |
| `opal/skills/opal-skill-manager/SKILL.md` | `match "{검색어}"` | 검색·설치 단계 기존 설치 여부 확인 |
| `.opal/AGENT.md`(배포본) | 숨김 호출 | `//` 입력 시 자동 실행(오케스트레이터 흐름) |

#### 변경에 따른 영향 범위

**직접 영향**:
- `getCommunitySkillPath()` 함수 시그니처 변경 → 모든 호출처에서 경로 계산 방식 변경 인식 필요
- `matchByAlias()` 반환값 변경 → basename 충돌 시 응답 형식 변경(목록 vs 단일 선택) 가능

**간접 영향**:
- skill-commands.md의 미설치 분기 추가 → `.opal/AGENT.md` 동의 prompt 절차 변경 (사용자 보이는 부분)
- opal-skill-manager SKILL.md §6 변경 → `//skill-manager` 호출 시 사용자 경험 변경

### 1.4 테스트 현황

**테스트 파일**: `opal/tools/skill-registry/tests/test-validate.js`

**실행 방법**:
```bash
node opal/tools/skill-registry/tests/test-validate.js
```

**현황**:
- **RED-first** 트랙 (태스크 029, opal-test-agent mode:red 작성)
- **5개 테스트 케이스**:

| TC# | 케이스 | 상태 | 기대값 |
|-----|--------|------|--------|
| TC1 | Clean fixture 정합 | GREEN (현행 통과) | exit 0, valid:true, errors 0 |
| TC2 | Dangling 폴더 감지 | RED (현행 미감지 → 구현 후 GREEN) | exit 1, errors 포함 "dangling" |
| TC3 | Unregistered 폴더 감지 | RED (현행 미감지 → 구현 후 GREEN) | exit 1, errors 포함 "unregistered" |
| TC4 | Deploy 환경 false positive 0 | GREEN (현행 통과) | exit 0, unregistered 오판 없음 |
| TC5 | Standalone skills/ 폴더 처리 | GREEN (현행 통과) | exit 0, 오판 없음 |

**근거**: `opal/tools/skill-registry/tests/test-validate.js:154-315`

> 참고: 이 테스트는 `validate` 커맨드만 커버한다. `match`/`get`/`list` 및 `getCommunitySkillPath`/`matchByAlias` 변경에 대한 직접 테스트는 부재 — F-1·F-2 구현 시 신규 테스트 추가가 필요하다.

---

## 2. 외부 조사 결과

### 2.1 npx skills CLI 실제 동작 검증

**조사 대상**: [vercel-labs/skills](https://github.com/vercel-labs/skills) — `npx skills add` 커맨드

**확인 항목**: 설치 경로 지정 옵션 존재 여부

**결과**:
- `npx skills add {owner/repo@skill}` 커맨드는 **경로 지정 옵션 미지원**
- 설치 위치:
  - **프로젝트 범위**: `./.claude/skills/{skill}/` + `skills-lock.json` 생성
  - **글로벌 범위** (`-g`): `~/.claude/skills/{skill}/`
  - **~/.opal/community-skills/ 불가**: 도달할 방법 없음

**근거**:
- TASK.md:24 "실측: 프로젝트 스코프 시 `./.claude/skills/pdf` + `skills-lock.json` 생성 확인"
- 실제 `npx skills --help` 출력에서 경로 옵션 미확인

**영향**: D4 확정 — `npx skills add`는 OPAL 워크플로우에 부적합, clone-copy 방식 전환 필수 (C-2)

### 2.2 Registry v2.1 스키마

**확인 사항**: commit_sha 필드, source_repo/license 메타데이터

**결과**:
- **스키마 버전**: v2.1 (`community-skills-registry.json:1-5`)
- **commit_sha**: 옵션 필드 (v2 호환 유지, 검증된 스킬만 작성 — schema_notes 명시)
- **현황**:
  - anthropics/* : commit_sha = null (아직 미작성)
  - obra/brainstorming : commit_sha = `d884ae04edebef577e82ff7c4e143debd0bbec99` (기기록)
  - 기타: 필드 자체 부재 또는 null

**근거**: `opal/core/references/community-skills-registry.json:1-54`

---

## 3. 영향 범위

### 3.1 직접 영향

**코드/설정 변경 대상**:
- `skill-registry.js:76-78` — getCommunitySkillPath() 재구현 (flat → vendor 중첩 경로 동시 지원)
- `skill-registry.js:129-135` — matchByAlias() 확장 (basename 매칭 추가)
- `skill-registry.js:212` — match 출력 install_command 필드 (npx → clone-copy 지시로 변경)
- `skill-commands.md` — 미설치 분기 신설 (별도 섹션)
- `opal-skill-manager/SKILL.md` — §2·§6 절차 재작성 (clone-copy 단일 방식)
- `install-mac.sh:1352-1366` — registry 배포 로직 명시 (사용자 데이터 보존 규칙)
- `windows.ps1:551-557` — 동일 Windows 어댑터
- `docs/ARCHITECTURE.md:178, 226` — npx 언급 제거

**데이터 마이그레이션**:
- Flat 31개 디렉토리 → vendor 중첩 구조 변환 (마이그레이션 실행 주체는 PLAN에서 결정)

### 3.2 간접 영향

**사용자 경험 변경**:
1. `//pdf` 입력 시:
   - 현재: found=true, installed=false (오판)
   - 변경 후: found=true, installed=true (정상)

2. `//pdf 문서 만들어줘` 입력 시:
   - 현재: found=true (triggers 폴백), cleanInput="문서 만들어줘"
   - 변경 후: found=true (basename alias 매칭), cleanInput="문서 만들어줘"

3. 미설치 커뮤니티 스킬 `//xxx` 호출:
   - 현재: "설치 안 됨" 처리 미정의 (skill-manager §6만 구현)
   - 변경 후: skill-commands.md에 정의된 동의→설치→실행 절차 표준화

**호출 체인 영향**:
- `.opal/AGENT.md` (배포본) → skill-commands.md 참조 → skill-manager 절차 호출
- 변경으로 인해 사용자가 보는 동의 prompt, 설치 메시지, 라이선스 경고 모두 통일

### 3.3 영향 범위 요약

- [ ] DB 스키마 변경 — **아니오**
- [x] API 인터페이스 변경 — **예** (match 출력 필드, install_command 형식)
- [ ] 설정/환경변수 변경 — **아니오**
- [ ] 빌드/배포 파이프라인 변경 — **아니오** (install 로직은 문서 명시만, 코드 불변 목표)
- [x] 공유 라이브러리 변경 — **예** (skill-registry.js 배포 → 모든 사용자 영향)

---

## 4. 핵심 발견 사항

### (1) 설치 레이아웃 "의도-실제" 불일치 (D1)

**의도**: vendor 중첩(`anthropics/pdf/`) — registry 스키마에 정의됨
**실제**: flat 구조(`pdf/`) — 31개 잔재, 1개만 의도대로 구현
**근거**:
- Registry: `opal/core/references/community-skills-registry.json:7-52` 32개 항목 모두 `{vendor}/{name}` 형식
- Filesystem: `~/.opal/community-skills/` ls 결과 — 32개 디렉토리 중 31개 flat, 1개만 `obra/brainstorming` 중첩
- TASK.md:21 "v2.0(태스크 142) '번들→fetch 전환' 이전 v1 번들 설치분(2026-05-10 타임스탬프)"

### (2) 경로 계산 함수의 경로 불일치 (D1 상세)

**함수**: `skill-registry.js:75-77` getCommunitySkillPath()
```javascript
function getCommunitySkillPath(skillName) {
  return path.join(os.homedir(), '.opal', 'community-skills', skillName, 'SKILL.md');
}
```

**문제**:
- 인자 `skillName` = `"anthropics/pdf"` 시 반환 경로 = `~/.opal/community-skills/anthropics/pdf/SKILL.md`
- 실제 파일 위치 = `~/.opal/community-skills/pdf/SKILL.md`
- 결과: `fs.existsSync()` 항상 false (31개 flat 디렉토리)

**근거**: 실제 파일 검증 `ls ~/.opal/community-skills/pdf/SKILL.md` 존재 vs `ls ~/.opal/community-skills/anthropics/pdf/SKILL.md` 미존재

### (3) Basename 매칭 부재 (D2)

**현상**:
- `//pdf` 입력 → alias 매칭 실패 → triggers 매칭 성공 (정규식으로 우연히 일치)
- `//pdf 문서 만들어줘` 입력 → alias 매칭 실패 → triggers는 cleanInput="문서 만들어줘" 기반

**근거**: `skill-registry.js:129-135` matchByAlias() 구현 — name/alias만 비교, basename 비교 없음

**결과**: Basename 충돌 시 명확한 우선순위 정책 필요 (복수 벤더 동일 스킬명 사례)

### (4) 미설치 스킬 처리 절차 문서 이원화 (D3)

**현황**:
- **skill-commands.md** (`//` 커맨드 호출 시 로드): 미설치 분기 **부재** — 1-44줄 전부 검토 완료, 쌍슬래시 포맷만 설명
- **opal-skill-manager/SKILL.md** (명시 호출 시만 로드): §6:127-152 미설치 매칭 시 자동 fetch 절차 **완전 기재**

**영향**:
- `//` 입력 시 미설치 스킬 응답 로직이 skill-manager 절차를 참조할 수 없음 (`.opal/AGENT.md` 스크립트는 skill-commands.md만 로드)
- SSOT 분산 → 중복 서술 → 관리 복잡도 증가

**근거**: `opal/core/references/harness/skill-commands.md` 전체 + `opal/skills/opal-skill-manager/SKILL.md:127-152` 비교

### (5) npx skills add 설치 방식 오류 (D4)

**명령어**: `npx skills add anthropics/skills@pdf`
**실제 설치 위치**:
- 프로젝트 범위: `./.claude/skills/pdf/`
- 글로벌: `~/.claude/skills/pdf/`

**기대 위치**: `~/.opal/community-skills/anthropics/pdf/` (OPAL 설정)

**경로 옵션**: 없음 (검증: `npx skills --help` 출력)

**근거**:
- TASK.md:24 "스크래치패드 실설치 실측 (`→ ./.claude/skills/pdf` + `skills-lock.json` 생성 확인)"
- `opal/skills/opal-skill-manager/SKILL.md:148` `npx skills add {source_repo}` 호출 + `:44` 설치 명령 테이블

### (6) Registry 배포 시 사용자 데이터 소실 위험 (F-6)

**배포 메커니즘**:
- **install-mac.sh:1362**: `cp -Rf "$ref_src"/. "$ref_dst"/` — 전체 참조 디렉토리 복사
- **windows.ps1:551-557**: 동등 PowerShell 커맨드

**보존 정책**:
- `~/.opal/community-skills/` 디렉토리 자체는 **보존** (clean_dirs에 미포함, install-mac.sh:1033-1034)
- 그러나 `~/.opal/references/community-skills-registry.json`은 **덮어쓰기** (참조 디렉토리 전체 복사 대상, references가 clean_dirs 포함)

**위험**: 사용자가 수동 설치한 스킬을 registry에 등록했으면, install 재실행 시 registry 항목 소실 가능

**완화 방안 필요**:
- Option A: registry merge 로직 (기존+배포본 결합)
- Option B: registry 파일 별도 보존 정책 (community-skills-registry.json을 clean_dirs 제외)
- Option C: 문서 명시 (사용자 설치분은 별도 파일 관리 또는 배포 후 수동 복구)

**근거**: `scripts/install-mac.sh:1033-1366` 주석 + 실제 cp 명령

### (7) Registry 항목 vs 파일 시스템 대조 (마이그레이션 대상 확정)

**Registry 항목**: 32개
- anthropics: 18개 / google-labs-code: 5개 / vercel-labs: 5개 / trailofbits: 1개 / getsentry: 1개 / openai: 1개 / obra: 1개

**파일 시스템**: 32개 디렉토리
- 31개 flat (docx, pdf, design-md, ... — basename 매칭)
- 1개 중첩 (obra/brainstorming)

**대조 결과** (basename 대조 실측):
- Flat 31개는 모두 registry 등재명과 basename 매칭됨 → **미등재 flat 디렉토리 0개** (142 D-4 보존 대상 없음, 전량 마이그레이션 가능)
- `obra/brainstorming`는 이미 vendor 중첩으로 정합
- registry에만 있고 flat에 없는 항목: `brainstorming` (obra 중첩으로 존재하므로 실제 누락 아님)

**정합 기준**:
- Flat 31개를 vendor 중첩으로 이동하면 registry 전수가 installed=true로 판정 (F-1 AC 충족)

**근거**: `ls ~/.opal/community-skills/` + `jq '.groups[]|.[].name'` basename 대조 실측

---

## 5. 제약/리스크

| # | 항목 | 설명 | 심각도 | 근거 |
|---|------|------|--------|------|
| R-1 | Flat 마이그레이션 실행 주체 미결정 | flat 31개 → vendor 중첩 이동 작업의 주체(스크립트/skill-manager/install) 미정 — 142 D-4 "사용자 데이터 보존" 제약과 정합성 검토 필수 | 중 | TASK.md:44 |
| R-2 | Basename 충돌 처리 미정의 | F-2에서 basename 매칭 추가 시, 복수 벤더가 동일 basename 가지면 단일 선택/목록 반환 중 어느 쪽인지 정책 필요 | 중 | TASK.md:57 |
| R-3 | Registry 사용자 데이터 소실 경로 | install 재실행 시 ~/.opal/references/community-skills-registry.json 덮어쓰기 → 사용자 수동 등록분 소실 가능 | 높음 | `scripts/install-mac.sh:1362`, TASK.md:72-73 |
| R-4 | Windows 어댑터 동등성 | windows.ps1의 참조 배포 로직이 install-mac.sh와 정확히 동일해야 하는데, 이 분석은 shell 중심 — Windows 세부 재검증 필요 | 중 | `scripts/install/windows.ps1:551-557` |
| R-5 | Npx CLI 향후 변경 가능성 | 외부 vercel-labs/skills CLI 의존성 — 경로 옵션 추가 시 D4 판정 무효화 가능 | 낮음 | [vercel-labs/skills](https://github.com/vercel-labs/skills) |
| R-6 | Commit SHA 관리 정책 부재 | F-4에서 clone 시점 commit_sha 기록하나, 업데이트 감지·비교 로직 미정의 | 중 | TASK.md:65 |

> 근거: `` `경로 §N` `` 또는 `` `경로:줄번호` `` 또는 `[사이트명](URL)` 또는 `-`.

---

## 6. 기술 컨텍스트

### 6.1 기술 스택

| 카테고리 | 기술 | 버전 |
|----------|------|------|
| 언어 | JavaScript (Node.js) | 내장 모듈만(fs, path, os) |
| 빌드/번들 | 없음 (CLI 단일 파일) | - |
| 런타임 | Node.js | 18+ (test: node:test 내장) |
| 테스트 | Node.js 내장 test 모듈 | 18+ |
| 마크다운 | 기획/설계 문서 언어 | - |
| 쉘 | install-mac.sh 설치 스크립트 | bash/zsh compatible |
| PowerShell | windows.ps1 설치 스크립트 | 5.0+ |

**근거**: `opal/tools/skill-registry/skill-registry.js:28-33` (require 문) + `opal/tools/skill-registry/tests/test-validate.js:24-29` (test 모듈)

### 6.2 추천 스킬

| 스킬 | 용도 |
|------|------|
| opal-skill-manager | 커뮤니티 스킬 검색·설치·관리 수동 실행 (검사/업데이트 포함) |
| op-dev-plan | 마이그레이션 실행 주체 결정 및 구현 계획 수립 |

### 6.3 추천 MCP

| MCP | 용도 |
|-----|------|
| 없음 | 외부 라이브러리 조회 불필요 (Node.js 내장 모듈만 사용) |

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-07-17 | op-dev-analysis SKILL.md 통일 형식으로 ANALYSIS 초안 작성 — D1~D4 실측 분석 + F-6 registry 배포 위험 분석 + 테스트 커버리지 현황 + 기술 스택 확인 + registry↔파일시스템 대조(미등재 flat 0개 확정) |
