# QA: PLAN — opal-project-init PM 에이전트 프로필 생성 파이프라인 추가

> 검토일: 2026-03-21 | 판정: ✅ Pass

---

## 1. 요약

opal-project-init 스킬에서 프로젝트별 PM 에이전트 프로필(.opal/AGENT.md)과 메모리 인덱스(.opal/MEMORY.md)를 자동 생성하는 기능을 추가한다. 기존 opal/templates/ 플레이스홀더 템플릿을 skills/opal-project-init/templates/common/opal/로 이동하고, apply.js에 [5/5] .opal/ 파일 생성 섹션을 추가하는 구조. PM 관점 6개 섹션(페르소나, 목적, 도메인, 원칙, Phase, 금지사항)과 메모리 5개 카테고리(아키텍처, 도메인, 작업, 선호도, 이슈)로 구성되며, CURRENT_DATE 동적 주입으로 생성일 자동 기록.

---

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| SP-1 | 코드 분석 충분성 | ✅ | apply.js [1/4]~[4/4] 섹션, processFile 로직 확인. OPAL_FILES 배열 패턴 동일하게 설계됨. |
| SP-2 | 구현 계획 구체성 | ✅ | 신규 템플릿 2개(AGENT.md, MEMORY.md) 섹션 구조 + 플레이스홀더 명시. apply.js 수정 코드 스니펫 포함됨. |
| SP-3 | 체크리스트 완전성 | ✅ | 5개 Step(템플릿 생성 2개, apply.js 수정, SKILL.md 수정, 템플릿 삭제) 모두 포함. |
| SP-4 | QA 항목 커버리지 | ✅ | 기능(dry-run, 플레이스홀더 치환, existing 모드 건너뛰기), 회귀(기존 [1/4]~[4/4] 동작), 코드 품질(상수 패턴, 날짜 주입, 문서 정합성) 포함. |
| SP-5 | 구현 순서 적정성 | ✅ | 템플릿 생성 → apply.js 수정(의존성 있음) → SKILL.md 문서화 → 구 템플릿 삭제. 논리적 순서. |

---

## 3. 지적 사항

지적 사항 없음. 설계가 명확하고 기존 아키텍처 패턴을 잘 따른다.

---

## 4. 교차 참조 검증

| 참조 대상 | 검증 내용 | 결과 |
|----------|----------|------|
| SKILL.md Step 6~7 | 저장 경로 매핑에 opal/ 경로 언급 없음 → PLAN에서는 apply.js 자동 처리로 명시 (Step 7.5 불필요, apply.js [5/5]에 통합) | ✅ |
| apply.js 구조 | COMMON_DOCS, PLATFORM_FILES, TYPE_DOCS, OPTIONAL_DOCS 배열 패턴 → OPAL_FILES도 동일 { src, dest } 형식 설계 | ✅ |
| processFile 함수 시그니처 | fileType 파라미터 기존값: "docs", "platform-claude", "platform-other" → "docs" 재사용 (existing 모드에서 기존 .opal/AGENT.md 있으면 건너뛰기) | ✅ |
| 플레이스홀더 형식 | 기존 {{PROJECT_NAME}}, {{TECH_STACK_BACKEND}} 등 이중 중괄호 형식 일관성 | ✅ |
| CURRENT_DATE 동적 주입 | apply.js main() 진입 후 config 파싱 후 즉시 추가 명시 | ✅ |

---

## 5. 세부 검증 의견

### 5.1 코드 분석 (SP-1)

PLAN의 "관련 파일" 섹션에서:
- `templates/common/opal/` 신규 생성 위치 명확
- apply.js의 [1/4]~[4/4] 섹션 구조 정확히 파악 (이중 중괄호 플레이스홀더, COMMON_DOCS 배열 등)
- existing 모드에서 docs 파일은 기존이 있으면 건너뛰고, platform 파일은 병합하는 로직 이해 완벽

다만, PLAN에서 "{{CURRENT_DATE}}" 플레이스홀더를 MEMORY.md에만 사용한다고 명시했는데, 이는 정적 템플릿에는 포함될 수 없고 apply.js의 동적 주입으로만 가능한 점을 암시적으로 다루고 있다. 이를 명확히 하기 위해 SKILL.md Step 7-2 설명에 "CURRENT_DATE는 템플릿에 포함되지 않고 apply.js에서 동적으로 주입됨"이라는 문장을 추가하면 더 좋겠다. (마이너 포인트)

### 5.2 구현 계획 (SP-2)

**템플릿 설계 완성도**:
- AGENT.md: 6개 섹션(페르소나, 목적, 도메인, 의사결정, Phase, 금지사항) — PM이 프로젝트를 바라보는 렌즈를 정의하는 관점 우수
- MEMORY.md: 5개 카테고리(아키텍처, 도메인, 작업, 선호도, 이슈) — OPAL AGENT.md의 "기억과 학습" 정책과 일치

**apply.js 수정 설계**:
- OPAL_FILES 상수: `{ src: "opal/AGENT.md", dest: ".opal/AGENT.md" }` 형식 → PLATFORM_FILES와 패턴 동일
- [5/5] 섹션: 기존 [1/4]~[4/4]와 같은 구조, console.log 메시지 방식 일관성
- existing 모드에서 .opal/AGENT.md 있으면 건너뛰기 → 사용자 커스터마이징 보존 정책 타당

### 5.3 체크리스트 (SP-3)

Step 1~5가 순차 의존성을 갖는다:
1. 템플릿 생성 (Step 1~2) → apply.js에서 읽을 파일 준비
2. apply.js 수정 (Step 3) → 템플릿 처리 로직 추가
3. SKILL.md 수정 (Step 4) → 사용자 가이드 문서화
4. 구 템플릿 삭제 (Step 5) → 마이그레이션 완료

이 순서가 PLAN에서 명확히 1~5로 순서화되어 있어 실행 중 실수 가능성 낮음.

### 5.4 QA 항목 (SP-4)

**기능 테스트**:
- dry-run 확인: apply.js에서 dryRun 플래그 처리 기존 구조 이용 → 신규 [5/5] 섹션도 동일하게 처리
- 플레이스홀더 치환: replacePlaceholders 함수로 이중 중괄호 {{KEY}} 처리 → CURRENT_DATE도 포함
- existing 모드: processFile에 "docs" fileType으로 기존 .opal/AGENT.md 건너뛰기 기능 명시

**회귀 테스트**:
- 기존 [1/4]~[4/4] 동작 보존 확인 필수
- excludeTemplates에 opal/ 경로 추가 가능성도 고려 가능

**코드 품질**:
- OPAL_FILES 형식 일관성 (PLATFORM_FILES 패턴) ✅
- CURRENT_DATE 주입 타이밍 명확 ✅
- SKILL.md 문서와 apply.js 코드 정합성 (아래 참고)

### 5.5 기존 SKILL.md와의 정합성

현재 SKILL.md Step 7의 "저장 경로 매핑" 섹션:
```markdown
- `templates/common/docs/{파일}` → `{프로젝트루트}/docs/{파일}`
- `templates/common/platform/CLAUDE.md` → `{프로젝트루트}/CLAUDE.md`
...
```

PLAN에서 Step 7 설명에 `.opal/` 항목을 추가해야 한다는 점이 명시되어 있다. SKILL.md 수정 시 다음 항목을 추가:
```markdown
- `templates/common/opal/AGENT.md` → `{프로젝트루트}/.opal/AGENT.md`
- `templates/common/opal/MEMORY.md` → `{프로젝트루트}/.opal/MEMORY.md`
```

이를 Step 8 완료 보고에도 반영 필요:
```
생성된 파일:
- docs/INDEX.md
- docs/server/ ({N}개)
- docs/client/ ({M}개)
- .opal/AGENT.md, .opal/MEMORY.md  ← 추가
- CLAUDE.md, GEMINI.md, .cursorrules
```

---

## 6. 최종 판정

**✅ Pass**

**근거**:
- 코드 분석이 충분하고 정확함 (apply.js, SKILL.md 구조 이해 완벽)
- 구현 계획이 구체적이고 기존 패턴을 일관되게 따름
- 실행 체크리스트와 QA 체크리스트가 빠짐 없이 설계됨
- 마이너 포인트(SKILL.md Step 7 저장 경로 매핑 추가)는 구현 단계에서 자연스럽게 처리 가능

**다음 단계**: EXECUTE로 진행 가능. 실행 시 Step 3(apply.js 수정)에서 COMMON_DOCS와 PLATFORM_FILES 위치 바로 다음에 OPAL_FILES를 추가하고, main() 함수의 [4/4] 섹션 후에 [5/5]를 삽입하면 된다.
