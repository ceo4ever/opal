---
name: op-dev-analysis
description: |
  **코드베이스 분석 및 기술 컨텍스트 수집 단계 스킬**. TASK.md를 기반으로 기존 코드를 분석하고, 기술 스택을 식별하여 추천 스킬/MCP를 매핑한다.
  반드시 이 스킬을 사용해야 하는 상황: 오케스트레이터(opal-pilot-dev)가 ANALYSIS 단계를 디스패치할 때.
  필수 입력: TASK.md. 선택 입력: 프로젝트 docs/. 보장 출력: ANALYSIS.md.
---

# op-dev-analysis — 코드베이스 분석 및 기술 컨텍스트 수집

## 실행 컨텍스트

- **호출자**: 오케스트레이터(opal-pilot-dev)가 ANALYSIS 단계를 디스패치
- **실행 주체**: 워커 에이전트 (opal-task-agent)
- **입력**: `tasks/{NNN}-{태스크명}/TASK.md`
- **출력**: `tasks/{NNN}-{태스크명}/ANALYSIS.md`

## 페르소나

```
Read ~/.opal/skills/op-dev-analysis/personas/application-architect.md
```

페르소나 파일이 없으면 다음 역할을 따른다:
- 시니어 애플리케이션 아키텍트
- 기존 코드의 구조와 패턴을 존중하되, 개선 기회를 식별한다
- 추측 대신 코드 근거를 제시한다

## 프로세스

### Step 1. 기술 컨텍스트 로딩

```
Read ~/.opal/skills/op-dev-analysis/references/tech-context-guide.md
```

가이드에 따라 프로젝트 문서, 기술 스택, 추천 스킬/MCP를 수집한다.

### Step 2. 코드베이스 분석

```
Read ~/.opal/skills/op-dev-analysis/references/analysis-guide.md
```

가이드에 따라 TASK.md 요구사항 기반으로 기존 코드를 분석한다.

### Step 3. ANALYSIS.md 작성

분석 결과를 아래 통일 형식으로 작성한다.

## 활용 MCP

| MCP | 용도 | 사용 시점 |
|-----|------|----------|
| context7 | `resolve-library-id` → `get-library-docs` | 외부 라이브러리 API 조사 시 |
| WebSearch | 공식 문서/릴리스 노트 검색 | context7에 없는 라이브러리, 최신 변경사항 확인 시 |

## ANALYSIS.md 통일 형식

```markdown
# ANALYSIS: {제목}

> 작성일: YYYY-MM-DD
> 입력: TASK.md
> 출력: ANALYSIS.md

## 1. 기존 코드 분석

### 1.1 관련 파일 목록
| 파일 | 역할 | 변경 필요 |
|------|------|----------|

### 1.2 아키텍처 패턴
- 현재 사용 중인 패턴/규약

### 1.3 의존성 맵
- 모듈 간 호출 관계, import 그래프

### 1.4 테스트 현황
- 기존 테스트 유무, 커버리지 수준

## 2. 외부 조사 결과 (해당 시)

### 2.1 라이브러리/API 조사
- context7 또는 WebSearch로 확인한 내용

### 2.2 버전 호환성
- 주요 의존성 버전 제약

## 3. 영향 범위

### 3.1 직접 영향
- 변경 대상 파일/모듈

### 3.2 간접 영향
- 변경에 의해 영향받는 소비자/호출자

### 3.3 영향 범위 요약
- [ ] DB 스키마 변경
- [ ] API 인터페이스 변경
- [ ] 설정/환경변수 변경
- [ ] 빌드/배포 파이프라인 변경

## 4. 핵심 발견 사항
- 분석을 통해 도출된 주요 인사이트 (3~5개)

## 5. 제약/리스크
| 항목 | 설명 | 심각도 |
|------|------|--------|

## 6. 기술 컨텍스트

### 6.1 기술 스택
| 카테고리 | 기술 | 버전 |
|----------|------|------|

### 6.2 추천 스킬
| 스킬 | 용도 |
|------|------|

### 6.3 추천 MCP
| MCP | 용도 |
|-----|------|
```

## 저장 경로

```
tasks/{NNN}-{태스크명}/ANALYSIS.md
```

기존 ANALYSIS.md가 있으면 opal-doc-standard 규칙에 따라 버전 관리한다.

## 분석 품질 체크리스트

ANALYSIS.md 작성 후 자체 검증한다:

- [ ] TASK.md의 모든 요구사항이 분석에 반영되었는가
- [ ] 관련 파일 목록이 Glob/Grep으로 실제 확인되었는가 (추측 금지)
- [ ] 의존성 맵이 import/require 기반으로 작성되었는가
- [ ] 영향 범위가 직접+간접 모두 식별되었는가
- [ ] 기술 스택이 실제 설정 파일에서 추출되었는가
- [ ] 외부 조사가 필요한 항목은 context7/WebSearch를 사용했는가
- [ ] 제약/리스크가 구체적 근거와 함께 기술되었는가

## 완료 후 동작

워커는 QA를 직접 호출하지 않는다. ANALYSIS.md 작성이 완료되면 결과를 오케스트레이터에 반환한다. 오케스트레이터가 QA 단계 실행 여부를 결정한다.

**반환 형식**:
```
ANALYSIS 완료: tasks/{NNN}-{태스크명}/ANALYSIS.md
```
