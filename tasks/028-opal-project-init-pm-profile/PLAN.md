# PLAN: opal-project-init PM 에이전트 프로필 생성 파이프라인 추가

> 작성일: 2026-03-21 | 모드: Short Task | 참조: TASK.md

---

## 1. 코드 분석

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `opal/templates/project-agent.md` | 기존 project-agent 플레이스홀더 템플릿 (빈 섹션들) | 이동 후 삭제 |
| `opal/templates/memory-index.md` | 기존 memory-index 플레이스홀더 템플릿 (빈 테이블) | 이동 후 삭제 |
| `skills/opal-project-init/templates/common/` | 신규 opal/ 서브디렉토리 추가 대상 | 신규 생성 |
| `skills/opal-project-init/SKILL.md` | 메인 스킬 정의 — Step 7 뒤에 Step 7.5 추가 | 수정 |
| `skills/opal-project-init/scripts/apply.js` | 템플릿 적용 스크립트 — opal/ 처리 로직 추가 | 수정 |

### 현재 구현

**opal/templates/project-agent.md** (현재 상태):
- 섹션: 프로젝트 개요, 프로젝트 규칙(코드 컨벤션/브랜치/테스트/기타), 작업 수행 규칙, 주의사항
- 플레이스홀더: `{프로젝트명}`, `{프로젝트 설명}`, `{스택}` 등 — `{{PLACEHOLDER}}` 이중 중괄호 형식이 아님
- PM 역할 관점 섹션 없음 (페르소나, 도메인 지식, 의사결정 원칙 등)

**opal/templates/memory-index.md** (현재 상태):
- 섹션: 메모리 목록 테이블(파일/설명), 작업 히스토리 테이블(작업/결과/날짜)
- 카테고리 구분 없이 단순 평면 구조

**apply.js 핵심 흐름**:
1. `TEMPLATES_DIR = path.resolve(__dirname, "..", "templates")` — 템플릿 루트
2. `COMMON_DOCS` 배열에 처리할 docs 상대 경로 목록 명시
3. `PLATFORM_FILES` 배열에 플랫폼 파일(CLAUDE.md 등) 명시
4. `processFile(src, dest, placeholders, dryRun, mode, fileType)` — 개별 파일 치환/생성
5. `replacePlaceholders(content, placeholders)` — `{{KEY}}` → 값 치환
6. 섹션 [1/4]~[4/4]로 나뉜 실행 순서

**apply.js 저장 경로 매핑** (현재):
- `templates/common/docs/{파일}` → `{projectRoot}/docs/{파일}`
- `templates/common/platform/{파일}` → `{projectRoot}/{파일}`

**opal-project-init SKILL.md Step 흐름**:
- Step 0(모드선택) → Step 0-A(자동분석) → Step 0-B(확인인터뷰) → Step 1~3(신규인터뷰) → Step 4(context7) → Step 5(매핑표) → Step 6(템플릿결정) → Step 7(apply.js 실행) → Step 8(완료보고)

**OPAL 오케스트레이터 연동 흐름**:
- `~/.opal/AGENT.md`: `.opal/AGENT.md` 존재 시 → `opal-orchestrator/SKILL.md` 로드 → 오케스트레이터 모드
- `.opal/AGENT.md`는 알투의 프로젝트 진입 트리거

### 영향 범위

**호출자/피호출자**:
- `SKILL.md` Step 7이 `apply.js`를 호출 (`node ~/.opal/skills/opal-project-init/scripts/apply.js --config {config.json}`)
- `apply.js`가 `templates/` 하위 파일들을 읽어 `{projectRoot}/`에 생성
- 신규 Step 7.5는 `apply.js` 실행 완료 후, `.opal/` 디렉토리 생성 로직을 추가

**config.json 의존성**:
- 현재 `placeholders` 객체에 `PROJECT_NAME`, `PROJECT_DESCRIPTION` 등이 있고, 신규 `project-agent.md` 템플릿이 이를 활용할 수 있음
- `PROJECT_TYPE`, `TECH_STACK_BACKEND`, `TECH_STACK_FRONTEND` 등도 PM 프로필에 포함 가능

**관련 파일 중 변경 없는 것**:
- `opal/core/`, `opal/bootstrapper/`, `opal/skills/opal-orchestrator/` — 변경 불필요
- `~/.opal/AGENT.md` 로직은 `.opal/AGENT.md` 존재만 확인하므로 파일 내용 형식 무관

---

## 2. 구현 계획

### 변경 파일

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `skills/opal-project-init/templates/common/opal/AGENT.md` | 신규 생성 — PM 역할 관점 project-agent 템플릿 (이중 중괄호 플레이스홀더, 6개 섹션) |
| 2 | `skills/opal-project-init/templates/common/opal/MEMORY.md` | 신규 생성 — 카테고리 구조화 memory-index 템플릿 (5개 카테고리) |
| 3 | `skills/opal-project-init/scripts/apply.js` | 수정 — `[5/5] .opal/ 파일 생성` 섹션 추가 (OPAL_FILES 배열 + 처리 로직) |
| 4 | `skills/opal-project-init/SKILL.md` | 수정 — Step 7과 Step 8 사이에 Step 7.5 추가, Step 8 완료 보고에 .opal/ 항목 추가 |
| 5 | `opal/templates/project-agent.md` | 삭제 — 이동 완료 후 제거 |
| 6 | `opal/templates/memory-index.md` | 삭제 — 이동 완료 후 제거 |

### 핵심 설계

**템플릿 1: `common/opal/AGENT.md`**

플레이스홀더: `{{PROJECT_NAME}}`, `{{PROJECT_DESCRIPTION}}`, `{{TECH_STACK_BACKEND}}`, `{{TECH_STACK_FRONTEND}}`, `{{DB_TYPE}}`, `{{DOMAIN_NAME}}` (기존 매핑표에서 자동 치환)

섹션 구조:
```markdown
# {{PROJECT_NAME}} PM 에이전트

## 페르소나
(알투가 이 프로젝트에서 어떤 관점으로 사고할지)

## 프로젝트 목적
(왜 이 프로젝트가 존재하는지 — 비즈니스/기술 목적)

## 도메인 지식
(이 분야의 핵심 개념/용어 — 초기에는 플레이스홀더, 사용자가 채움)

## 의사결정 원칙
(트레이드오프 시 어떤 쪽을 선택할지 — 프로젝트 특화 원칙)

## 현재 Phase
(지금 어디까지 왔고 다음은 뭔지)

## 금지사항
(이 프로젝트에서 절대 하면 안 되는 것)
```

**템플릿 2: `common/opal/MEMORY.md`**

섹션 구조 (5개 카테고리, 각각 마크다운 테이블):
```markdown
# {{PROJECT_NAME}} Memory Index

> 최종 갱신: {{CURRENT_DATE}}

## architecture_decisions
왜 이 기술/설계를 선택했는지 — 아키텍처 결정 로그

## domain_knowledge
대화하면서 쌓인 도메인 지식 — 용어, 규칙, 비즈니스 로직

## work_history
최근 작업 이력 (10개 FIFO)

## preferences
이 프로젝트에서 캡틴이 선호하는 방식

## issues
반복되는 이슈와 해결법
```

**apply.js 수정 설계**:

```javascript
// 추가할 상수
const OPAL_FILES = [
  { src: "opal/AGENT.md", dest: ".opal/AGENT.md" },
  { src: "opal/MEMORY.md", dest: ".opal/MEMORY.md" },
];

// main() 내 [5/5] 섹션 추가
console.log("\n[5/5] .opal/ 파일 생성");
for (const { src, dest } of OPAL_FILES) {
  const srcPath = path.join(TEMPLATES_DIR, "common", src);
  const destPath = path.join(absRoot, dest);
  // existing 모드에서도 .opal/AGENT.md가 없으면 생성
  // 있으면 건너뛰기 (사용자 커스터마이징 보존)
  const f = processFile(srcPath, destPath, placeholders, dryRun, mode, "docs");
  if (f) createdFiles.push(f);
}
```

> `processFile`의 `"docs"` 타입은 existing 모드에서 기존 파일이 있으면 건너뛴다. 이 동작이 `.opal/` 파일에도 적합하다 — 사용자가 커스터마이징한 PM 프로필을 덮어쓰면 안 되기 때문이다.

**SKILL.md Step 7.5 설계**:

apply.js가 자동 처리하므로 Step 7.5는 SKILL.md에서 apply.js 실행으로 통합된다. 별도 수동 단계가 필요 없고, Step 7 설명에 `.opal/` 처리 내용을 명시하는 방식으로 문서화한다.

실제 구현은:
- `[5/5] .opal/ 파일 생성` 섹션을 apply.js에 추가
- SKILL.md의 Step 7 설명과 Step 8 완료 보고에 `.opal/AGENT.md`, `.opal/MEMORY.md` 항목 추가

**`{{CURRENT_DATE}}` 플레이스홀더**:

MEMORY.md에 생성 날짜를 삽입하기 위해 apply.js에서 `CURRENT_DATE`를 동적으로 placeholders에 추가한다:
```javascript
placeholders["CURRENT_DATE"] = new Date().toISOString().split("T")[0];
```

---

## 3. 실행 체크리스트

- [x] Step 1: 신규 템플릿 생성 — `skills/opal-project-init/templates/common/opal/AGENT.md` — PM 역할 관점 6개 섹션 + 이중 중괄호 플레이스홀더
- [x] Step 2: 신규 템플릿 생성 — `skills/opal-project-init/templates/common/opal/MEMORY.md` — 5개 카테고리 구조화 + `{{CURRENT_DATE}}` 플레이스홀더
- [x] Step 3: apply.js 수정 — `OPAL_FILES` 상수 추가 + `[5/5] .opal/ 파일 생성` 섹션 추가 + `CURRENT_DATE` 동적 주입
- [x] Step 4: SKILL.md 수정 — Step 7 설명에 `.opal/` 처리 명시 + Step 8 완료 보고에 `.opal/` 항목 추가
- [x] Step 5: 구 템플릿 삭제 — `opal/templates/project-agent.md`, `opal/templates/memory-index.md`

---

## 4. QA 체크리스트

### 기능 테스트

- [x] `apply.js --dry-run` 실행 시 `.opal/AGENT.md`, `.opal/MEMORY.md`가 DRY-RUN 출력에 포함되는가
- [x] `apply.js` 실행(new 모드) 후 `{projectRoot}/.opal/AGENT.md`, `{projectRoot}/.opal/MEMORY.md`가 생성되는가
- [x] 생성된 `AGENT.md`에서 `{{PROJECT_NAME}}` 등 플레이스홀더가 실제 값으로 치환되었는가
- [x] 생성된 `MEMORY.md`에서 `{{CURRENT_DATE}}`가 실행 날짜로 치환되었는가
- [x] existing 모드에서 `.opal/AGENT.md`가 이미 있을 때 덮어쓰지 않고 건너뛰는가

### 회귀 테스트

- [x] 기존 `[1/4]~[4/4]` 섹션 동작이 그대로인가 (공통 docs, 플랫폼 파일, 유형별, 조건부)
- [x] `excludeTemplates`에 `opal/AGENT.md`를 넣으면 생성이 스킵되는가 <!-- excludeTemplates 로직은 isExcluded로 동일하게 적용됨, 코드 확인 완료 -->
- [x] `opal/templates/` 삭제 후 해당 경로를 참조하는 코드가 없는가 (태스크 산출물에서만 참조)

### 코드 품질

- [x] `OPAL_FILES` 상수는 `PLATFORM_FILES` 패턴과 동일한 형식(`{ src, dest }`)을 따르는가
- [x] `CURRENT_DATE` 주입이 `main()` 진입 직후(config 파싱 후)에 수행되는가
- [x] SKILL.md의 Step 설명이 실제 apply.js 동작과 일치하는가 (문서-코드 정합성)
