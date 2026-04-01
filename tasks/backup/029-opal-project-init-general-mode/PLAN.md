# PLAN: opal-project-init 일반/개발 프로젝트 분기 + PM 공통 인터뷰

> 작성일: 2026-03-21 | 모드: Short Task | 참조: TASK.md

---

## 1. 코드 분석

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `skills/opal-project-init/SKILL.md` | 스킬 실행 프로세스 정의 (Step 0~8) | Y — Step 0 재구성 + PM 인터뷰 섹션 신규 추가 |
| `skills/opal-project-init/scripts/apply.js` | config.json 기반 템플릿 적용 Node.js 스크립트 | Y — `scope` 필드 지원, [1/4]~[4/4] 조건부 스킵 |
| `skills/opal-project-init/templates/common/opal/AGENT.md` | .opal/AGENT.md PM 프로필 템플릿 | Y — 새 플레이스홀더 3개 추가 |

### 현재 구현

**SKILL.md Step 흐름**

```
Step 0: 모드 선택 (소스코드 존재 → 신규/기존 자동 판별)
        ├── 신규: Step 1(유형) → Step 2(기본정보) → Step 3(특별기능) → Step 4~8
        └── 기존: Step 0-A(자동분석) → Step 0-B(확인/보정) → Step 4~8
```

- Step 0은 현재 "신규/기존" 2분기만 존재. "일반/개발" 분기 없음.
- PM 인터뷰 항목(페르소나, 의사결정 원칙, Phase) 없음.
- AGENT.md 템플릿의 페르소나/의사결정/Phase 섹션은 중괄호 설명 문구만 있고 플레이스홀더 아님.

**apply.js 주요 구조**

- config.json에서 `projectRoot`, `projectType`, `mode`, `placeholders`, `optional`, `excludeTemplates` 읽음
- `scope` 필드 없음 → [1/4]~[4/4] 항상 실행
- [5/5] .opal/ 파일은 마지막에 항상 실행
- `processFile`의 "docs" 타입: existing 모드에서 기존 파일 건너뛰기

**AGENT.md 템플릿 현재 플레이스홀더**

```
{{PROJECT_NAME}}, {{PROJECT_DESCRIPTION}}, {{TECH_STACK_BACKEND}},
{{TECH_STACK_FRONTEND}}, {{DB_TYPE}}, {{DOMAIN_NAME}}, {{CURRENT_DATE}}
```

- 페르소나/의사결정/Phase 섹션: `{이 프로젝트에서...}` 형태의 설명 문구만 존재
  - `{{PERSONA}}`, `{{DECISION_PRINCIPLES}}`, `{{CURRENT_PHASE}}` 플레이스홀더 없음

### 영향 범위

- **호출자**: 사용자 → SKILL.md Step 흐름 → apply.js → AGENT.md 템플릿
- **SKILL.md 변경** → apply.js config.json 형식 계약에 영향 (`scope` 신규 필드)
- **apply.js 변경** → config.json `scope` 필드 추가로 하위 호환성 유지 필요 (기존 config.json에 `scope` 없으면 `"full"` 기본값)
- **AGENT.md 템플릿 변경** → 일반 프로젝트에서는 `{{TECH_STACK_BACKEND}}` 등 개발 전용 플레이스홀더가 남음. 일반 모드에서는 placeholders에 빈 값 또는 `"N/A"`로 주입해야 함.
- **관련 테스트**: 없음 (스크립트 직접 실행 방식)

---

## 2. 구현 계획

### 변경 파일

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `skills/opal-project-init/SKILL.md` | Step 0 전면 재구성: 일반/개발 최우선 분기 + PM 공통 인터뷰(Step 0-PM) 신규 추가 |
| 2 | `skills/opal-project-init/scripts/apply.js` | `scope` 필드 파싱 추가, [1/4]~[4/4] 조건부 실행 로직 추가 |
| 3 | `skills/opal-project-init/templates/common/opal/AGENT.md` | `{{PERSONA}}`, `{{DECISION_PRINCIPLES}}`, `{{CURRENT_PHASE}}` 플레이스홀더 삽입 |

### 핵심 설계

#### SKILL.md Step 재구성

새로운 Step 0 흐름:

```
Step 0: 프로젝트 카테고리 선택
        │
   ┌────┴────────┐
  일반           개발
  (scope=opal-only) (scope=full)
   ↓               ↓
  Step 0-PM       Step 0-PM
  (PM 공통 인터뷰)  (PM 공통 인터뷰)
   ↓               ↓
  Step 7          Step 0-DEV
  (apply.js,      (신규/기존 분기)
   scope=opal-only) ↓
   ↓               Step 1~6 (개발 전용)
  Step 8           ↓
  (완료 보고)      Step 7~8
```

**Step 0: 프로젝트 카테고리** — 신규 삽입

```
[프로젝트 카테고리 선택]

프로젝트 루트를 분석한 결과, {소스 코드 존재/미존재} 상태입니다.

프로젝트 유형을 선택하세요:
  1. 일반 프로젝트 — 비개발 (기획, 문서, 프레임워크 등) → .opal/만 생성
  2. 개발 프로젝트 — 소스코드 있는 개발 프로젝트 → docs + platform + .opal/ 생성

(소스 코드 미존재 시 1번 기본 제안, 존재 시 2번 기본 제안)
```

**Step 0-PM: PM 공통 인터뷰** — 신규 삽입 (일반/개발 공통)

```
[PM 공통 인터뷰]

Q1. 프로젝트명
  - 영어명 (디렉토리·코드용):
  - 한글명 (문서 제목용):
  - 한 줄 설명:

Q2. 도메인/분야
  - 이 프로젝트가 속한 도메인 또는 분야 (예: 광고, 이커머스, AI 프레임워크):

Q3. 페르소나
  - 이 프로젝트에서 어떤 관점으로 사고해야 하는가?
  - (예: "광고 성과 데이터 정합성 최우선", "사용자 경험 중심", "재사용성과 확장성 우선")

Q4. 의사결정 원칙
  - 트레이드오프 상황에서 우선할 원칙 1~3가지
  - (예: "데이터 정합성 > UI 미관", "코드 가독성 > 성능 최적화")

Q5. 현재 Phase
  - 현재 진행 중인 Phase (예: "Phase 1: 데이터 파이프라인 구축")
  - 다음 Phase (예: "Phase 2: 대시보드 구현")
```

**Step 0-DEV** (기존 Step 0 역할, 개발 프로젝트 전용으로 이름 변경):

- 기존 Step 0의 신규/기존 분기 로직을 그대로 유지
- 신규 개발: Step 1~3 → Step 4~8
- 기존 개발: Step 0-A → Step 0-B → Step 4~8

**일반 프로젝트 흐름 (Step 7 직행)**:

- PM 공통 인터뷰 결과로 placeholders 구성
- 개발 전용 플레이스홀더(`TECH_STACK_BACKEND`, `TECH_STACK_FRONTEND`, `DB_TYPE` 등)는 `"N/A"` 주입
- `scope: "opal-only"` 설정
- Step 7(apply.js 실행) → Step 8(완료 보고) 직행

**Step 8 완료 보고** — 일반 프로젝트용 메시지 추가:

```
opal-project-init 완료 (일반 프로젝트)

프로젝트: {PROJECT_NAME}
카테고리: 일반 프로젝트

생성된 파일:
- .opal/AGENT.md (PM 프로필)
- .opal/MEMORY.md (메모리 인덱스)

다음 단계:
1. .opal/AGENT.md에서 도메인 지식, 금지사항, 프로젝트 규칙 커스터마이징
```

#### apply.js scope 필드

**config.json 스키마 확장**:

```json
{
  "projectRoot": "...",
  "projectType": "custom",
  "mode": "new",
  "scope": "opal-only",          // 신규 필드: "full" (기본) | "opal-only"
  "placeholders": { ... },
  "optional": { ... },
  "excludeTemplates": []
}
```

**main() 변경 포인트**:

```js
// scope 결정: config > 기본값 "full"
const scope = config.scope || "full";

if (scope !== "full" && scope !== "opal-only") {
  console.error(`설정 오류: scope는 "full" 또는 "opal-only"이어야 합니다`);
  process.exit(1);
}

// scope: "opal-only" 시 [1/4]~[4/4] 스킵
if (scope === "full") {
  // [1/4] 공통 문서
  // [2/4] 플랫폼 파일
  // [3/4] 유형별 추가
  // [4/4] 조건부 문서
} else {
  console.log("[1/4]~[4/4] 스킵 (scope=opal-only)");
}

// [5/5] .opal/ 파일 — 항상 실행
```

결과 JSON에도 `scope` 필드 추가:

```js
const result = {
  status: "success",
  projectRoot: absRoot,
  projectType,
  mode,
  scope,          // 신규
  filesCreated: createdFiles.length,
  ...
};
```

헤더 출력에도 `scope` 추가:

```js
console.log(`  scope: ${scope}`);
```

#### AGENT.md 템플릿 플레이스홀더 변경

현재 페르소나 섹션:
```markdown
- 사고 방식: {이 프로젝트에서 중요한 판단 관점을 기술 — 예: ...}
```

변경 후:
```markdown
- 사고 방식: {{PERSONA}}
```

현재 의사결정 원칙 섹션:
```markdown
- {원칙 1 — 예: "데이터 정합성 > UI 미관"}
- {원칙 2 — 예: "성능 최적화보다 코드 가독성 우선"}
- {원칙 3}
```

변경 후:
```markdown
{{DECISION_PRINCIPLES}}
```

현재 현재 Phase 섹션:
```markdown
- **현재**: {진행 중인 Phase — 예: "Phase 1: 데이터 파이프라인 + 대시보드"}
- **다음**: {다음 Phase — 예: "Phase 2: 키워드 성과 분석"}
- **완료**: {완료된 Phase}
```

변경 후:
```markdown
{{CURRENT_PHASE}}
```

**일반 프로젝트에서 개발 전용 플레이스홀더 처리**:

SKILL.md에서 일반 프로젝트 config 생성 시 다음 값 주입:
```json
"TECH_STACK_BACKEND": "N/A",
"TECH_STACK_FRONTEND": "N/A",
"DB_TYPE": "N/A",
"SERVER_PORT": "N/A",
"CLIENT_PORT": "N/A",
"API_URL_LOCAL": "N/A",
"DOMAIN_NAME": "{도메인/분야}"
```

헤더 줄(`스택: N/A + N/A | DB: N/A`)은 일반 프로젝트에서 어색하므로,
AGENT.md 템플릿의 헤더도 조건 없이 치환되도록 수정:

```markdown
> 생성일: {{CURRENT_DATE}} | 프로젝트: {{PROJECT_NAME}}
```

단, 기존 개발 프로젝트 AGENT.md와 이 템플릿을 공유하므로 헤더를 범용으로 변경한다.
개발 스택 정보는 헤더가 아니라 페르소나/프로젝트 목적 섹션에서 자연스럽게 표현된다.

---

## 3. 실행 체크리스트

- [x] **Step 1: AGENT.md 템플릿 수정** — `skills/opal-project-init/templates/common/opal/AGENT.md` — 헤더 범용화 + 3개 플레이스홀더(`{{PERSONA}}`, `{{DECISION_PRINCIPLES}}`, `{{CURRENT_PHASE}}`) 삽입
- [x] **Step 2: apply.js scope 필드 추가** — `skills/opal-project-init/scripts/apply.js` — `scope` 파싱, 유효성 검증, [1/4]~[4/4] 조건부 스킵, 결과 JSON에 `scope` 추가
- [x] **Step 3: SKILL.md Step 0 재구성** — `skills/opal-project-init/SKILL.md` — Step 0(카테고리 분기) + Step 0-PM(PM 공통 인터뷰) 신규 추가, 기존 Step 0 → Step 0-DEV 개명, 일반 프로젝트 흐름(→ Step 7) 추가, Step 7 config 생성 예시 업데이트, Step 8 완료 보고 일반 프로젝트 메시지 추가

---

## 4. QA 체크리스트

### 기능 테스트

- [ ] 일반 프로젝트 경로: `scope: "opal-only"` config로 apply.js 실행 시 [1/4]~[4/4] 로그가 출력되지 않고 `[5/5] .opal/` 파일만 생성됨
- [ ] 개발 프로젝트 경로: `scope: "full"` (또는 scope 미지정) config로 apply.js 실행 시 기존과 동일하게 [1/4]~[5/5] 모두 실행됨
- [ ] `scope` 미지정 시 기본값 `"full"` 적용 (하위 호환)
- [ ] `scope: "opal-only"` 결과 JSON에 `"scope": "opal-only"` 필드 포함
- [ ] AGENT.md에서 `{{PERSONA}}` → 인터뷰 입력값으로 치환됨
- [ ] AGENT.md에서 `{{DECISION_PRINCIPLES}}` → 인터뷰 입력값으로 치환됨
- [ ] AGENT.md에서 `{{CURRENT_PHASE}}` → 인터뷰 입력값으로 치환됨
- [ ] AGENT.md 헤더가 일반 프로젝트(TECH_STACK `"N/A"`)에서도 어색하지 않음
- [ ] SKILL.md Step 0-PM 인터뷰 항목 5가지(프로젝트명/설명, 도메인, 페르소나, 의사결정 원칙, Phase) 모두 포함

### 회귀 테스트

- [ ] 기존 개발 프로젝트 신규 모드 흐름(Step 1~8) 동작 변경 없음
- [ ] 기존 개발 프로젝트 기존 모드 흐름(Step 0-A → 0-B → 4~8) 동작 변경 없음
- [ ] apply.js: `scope` 필드 없는 기존 config.json 정상 처리 (기본값 `"full"`)
- [ ] apply.js: `--mode existing` CLI 옵션 및 `excludeTemplates` 동작 변경 없음
- [ ] AGENT.md 기존 플레이스홀더(`{{PROJECT_NAME}}`, `{{DOMAIN_NAME}}` 등) 정상 치환

### 코드 품질

- [ ] apply.js: `scope` 유효성 검증 코드 포함 (`"full"` | `"opal-only"` 외 값 → 오류 종료)
- [ ] apply.js: `scope: "opal-only"` 시 [1/4]~[4/4] 스킵 로그 출력 (운영자 가시성)
- [ ] SKILL.md: 일반 프로젝트의 config.json 예시에 `scope: "opal-only"` 명시
- [ ] SKILL.md: 개발 프로젝트의 config.json 예시에 `scope: "full"` 명시 (또는 기본값 설명)
- [ ] AGENT.md 템플릿: `{{PERSONA}}` 플레이스홀더 치환 미완료 시 알아보기 어렵지 않도록 기본 안내 문구 제거
