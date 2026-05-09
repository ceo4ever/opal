# TASK 109 — @header 표준 + code-scan 통합 워크플로우

**적용 스킬**: opal-pilot-project (opp)  
**생성일**: 2026-04-11  
**상태**: TASK

---

## 1. 배경

코드 파일 분석/설계 시 파일 전체를 Read하는 토큰 낭비를 줄이기 위해, 각 파일 상단에 `@header` 메타블록을 정의하고 code-scan.js로 빠르게 구조를 파악한 뒤 필요한 파일만 선택적으로 Read하는 워크플로우를 도입한다.

워커(LLM)가 EXECUTE 시 파일을 생성/수정하면서 @header를 직접 작성한다. 별도 도구 없이 하네스 규칙 + 템플릿만으로 운영한다.

---

## 2. 요구사항

### 2-1. @header 포맷 표준 문서 (신규)

- [x] `opal/core/references/header-standard.md` 작성
- [x] 필드 정의: `module`(필수), `layer`(필수), `domain`(필수), `description`(필수), `exports`(필수), `depends`(선택), `note`(선택)
- [x] `exports` 통합 필드 — layer에 따라 담는 내용이 달라짐 (router/controller → API 엔드포인트, service/util → 함수명, page/component → 컴포넌트명)
- [x] 언어별 주석 포맷 예시 (Python/Vue/TypeScript/Kotlin/Swift)
- [x] 삽입 위치: 파일 최상단 (shebang 다음, 없으면 첫 줄)

### 2-2. opal-harness.md — EXECUTE @header 규칙 추가

- [x] `opal/core/references/opal-harness.md` EXECUTE 단계에 @header 규칙 추가
  - 파일 생성 시: @header 없으면 템플릿 기준으로 신규 작성
  - 파일 수정 시: @header 있으면 변경된 필드만 갱신
  - code-scan 지원 확장자 파일에만 적용 (`.py .js .ts .vue .jsx .tsx .svelte .kt .kts .java .swift`)
  - 워커가 언어에 맞는 주석 문법으로 직접 작성 (별도 도구 없음)

### 2-3. opal-pm.md — PM 관리 의무 추가

- [x] `opal/core/references/opal-pm.md` PM Gate 체크 항목 추가
  - 신규 domain/scope가 `code-scan.json`에 반영되어 있는가
- [x] PM의 code-scan.json 관리 의무 섹션 추가
  - code-scan 사용 시점에 `code-scan.json` 없으면 PM이 생성
  - 갱신 트리거: 신규 도메인/폴더 추가, 대규모 리팩토링

### 2-4. tools.md — code-scan PM 관리 항목 보완

- [x] `opal/core/references/tools.md` code-scan 항목에 PM 관리 방안 추가

### 2-5. op-task-execute/SKILL.md — @header 작성 규칙 추가

- [ ] `opal/skills/op-task-execute/SKILL.md` — header-standard.md Read 지시 + @header 작성 체크리스트 추가

### 2-6. op-dev-execute/SKILL.md — @header 작성 규칙 추가

- [ ] `opal/skills/op-dev-execute/SKILL.md` — 동일

### 2-7. code-scan.js — exports 커맨드 추가

- [ ] `opal/tools/code-scan/code-scan.js` — `exports <keyword>` 커맨드 추가
  - exports 필드만 대상으로 키워드 검색
  - `search`와 달리 exports 필드 전용으로 노이즈 없는 정확한 검색
  - 사용 예: `code-scan exports "issueToken"`, `code-scan exports "GET /users"`

### 2-8. opal/core/AGENT.md — 알투(비서) code-scan 활용 규칙 추가

- [ ] `opal/core/AGENT.md` — 알투 비서 모드에서 code-scan 활용 규칙 추가
  - 구조 파악 시: `code-scan scan <dir>` 또는 `code-scan domain/layer` 로 전체 개요 먼저 파악
  - 파일 탐색 시: `code-scan search <keyword>` / `code-scan exports <keyword>` 로 관련 파일 식별 후 선택적 Read
  - 캡틴 질문 응답 시: 전체 파일 Read 전에 code-scan으로 범위를 좁혀 응답
  - 적용 조건: `.opal/code-scan.json`이 존재하는 프로젝트에서만 활용

---

## 3. 범위 외

- header-gen.js 별도 툴 없음 (워커가 직접 작성)
- 기존 프로젝트 파일에 @header 일괄 적용 없음 (새 작업부터 적용)
- code-scan.json 프로젝트별 생성 없음 (PM이 필요 시점에 생성)
