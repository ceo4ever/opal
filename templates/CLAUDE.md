# CLAUDE.md 템플릿

> **사용법**: 이 파일은 참조용 템플릿이다. 기존 프로젝트에 CLAUDE.md가 있으면 아래 섹션 중 누락된 것만 골라서 기존 파일에 추가한다. 새 프로젝트라면 이 파일을 통째로 복사한 후 `{PLACEHOLDER}`를 교체한다.
>
> - **필수 섹션**: Project Overview, Language Convention, Tech Stack, Code Conventions
> - **권장 섹션**: Architecture
> - **기본값 있음** (생략 가능): 문서 표준, 버전 관리 규칙, 개발 워크플로우, 산출물 구조

---

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

{PROJECT_DESCRIPTION}

### 핵심 목표

- {GOAL_1}
- {GOAL_2}
- {GOAL_3}

## Language Convention

- **문서 본문**: {DOCUMENT_LANGUAGE} (예: 한국어, English)
- **코드/변수/필드명**: {CODE_LANGUAGE} (예: English)
- **파일/폴더 명명**: {NAMING_CONVENTION} (예: kebab-case, camelCase)

## Tech Stack

| 구분 | 기술 | 버전 |
|------|------|------|
| Language | {LANGUAGE} | {VERSION} |
| Framework | {FRAMEWORK} | {VERSION} |
| Database | {DATABASE} | {VERSION} |
| Build Tool | {BUILD_TOOL} | {VERSION} |
| Test Framework | {TEST_FRAMEWORK} | {VERSION} |
| Package Manager | {PACKAGE_MANAGER} | {VERSION} |

## Architecture

### 소스 구조

```
{PROJECT_ROOT}/
├── {SRC_DIR}/              ← 소스 코드
│   ├── {MODULE_1}/
│   ├── {MODULE_2}/
│   └── {MODULE_3}/
├── {TEST_DIR}/             ← 테스트
├── {CONFIG_DIR}/           ← 설정 파일
└── {DOCS_DIR}/             ← 문서
```

### 주요 설계 결정

- {ARCHITECTURE_DECISION_1}
- {ARCHITECTURE_DECISION_2}

## Code Conventions

### 코드 스타일

- 들여쓰기: {INDENT_STYLE} (예: 2 spaces, 4 spaces, tabs)
- 줄 길이: {MAX_LINE_LENGTH}자
- 문자열: {STRING_STYLE} (예: single quotes, double quotes)

### 네이밍 규칙

| 대상 | 규칙 | 예시 |
|------|------|------|
| 변수/함수 | {VARIABLE_NAMING} | {VARIABLE_EXAMPLE} |
| 클래스/타입 | {CLASS_NAMING} | {CLASS_EXAMPLE} |
| 상수 | {CONSTANT_NAMING} | {CONSTANT_EXAMPLE} |
| 파일명 | {FILE_NAMING} | {FILE_EXAMPLE} |

### 코드 품질 도구

```bash
# 린트
{LINT_COMMAND}

# 포맷팅
{FORMAT_COMMAND}

# 타입 체크
{TYPE_CHECK_COMMAND}

# 테스트
{TEST_COMMAND}
```

### 금지 패턴

- {ANTI_PATTERN_1}
- {ANTI_PATTERN_2}

## 문서 표준

모든 기술 문서 헤더:

```markdown
# [제목]

> 작성일: YYYY-MM-DD | 작성자: [작성자] | 버전: v{X.Y}
```

하단 변경이력 테이블:

```markdown
| 버전 | 날짜 | 작성자 | 변경내용 |
|------|------|--------|---------|
```

## 버전 관리 규칙

- `v{Major}.{Minor}` 형식
- **Major**: 구조적 변경 (섹션 추가/삭제, 엔티티 신규, 아키텍처 변경)
- **Minor**: 내용 수정 (보강, 오류 수정, 세부 조정)
- 기존 파일 덮어쓰기 금지 — 항상 새 버전 파일 생성
- 이전 버전의 변경이력을 새 버전에 전부 계승

## 개발 워크플로우

### 구현 금지 원칙

사용자의 명시적 승인 전까지 코드 생성/수정을 하지 않는다. task-flow 스킬의 5단계 파이프라인을 따른다:

```
TASK → RESEARCH → PLAN → TODO → EXECUTE
```

각 단계 산출물 작성 후 QA 에이전트가 1차 검토를 수행한 뒤 사용자에게 보고한다.

## 산출물 구조

```
tasks/{NNN}-{kebab-case-task-name}/
├── TASK.md           작업 정의서
├── QA-TASK.md        TASK QA 리뷰
├── RESEARCH.md       분석 결과
├── QA-RESEARCH.md    RESEARCH QA 리뷰
├── PLAN.md           구현 계획
├── QA-PLAN.md        PLAN QA 리뷰
├── TODO.md           실행 체크리스트
├── QA-TODO.md        TODO QA 리뷰
├── QA-EXECUTE.md     EXECUTE QA 리뷰
└── TEST-REPORT.md    테스트 리포트 (복잡 모드)
```

태스크 폴더명에 3자리 순번을 접두사로 붙인다 (예: `001-user-auth-implementation`).

## 단계 완료 보고 형식

```
[{단계명}] 완료 보고

산출물: tasks/{NNN}-{태스크명}/{단계}.md
QA 리뷰: tasks/{NNN}-{태스크명}/QA-{단계}.md

[QA 요약]
- 검증 항목 {N}개 중 {통과}개 Pass, {경고}개 Warning
- {주요 지적 사항 요약}
- 판정: {Pass / Needs Revision}

다음 단계로 넘어갈까요?
```
