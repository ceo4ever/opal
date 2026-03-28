# ANALYSIS: otp-write 범용 문서 작성 오케스트레이터 개발

> 작성일: 2026-03-28
> 입력: TASK.md
> 출력: ANALYSIS.md

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| skills/otp-dev-short/SKILL.md | 3단계 오케스트레이터 구조 (참조 템플릿) | 아니오 |
| skills/otp-dev/SKILL.md | Full Task 오케스트레이터 구조 (참조 템플릿) | 아니오 |
| skills/doc-writer/SKILL.md | 현재 doc-writer (72줄, 삭제 → opal-doc-standard 통합) | 삭제 |
| skills/version-mgr/SKILL.md | 현재 version-mgr (75줄, 삭제 → opal-doc-standard 통합) | 삭제 |
| skills/opal-skill-creator/SKILL.md | version-mgr + doc-writer 참조 (18줄, 19줄) | 예 (참조 대체) |
| skills/opal-agent-creator/SKILL.md | version-mgr + doc-writer 참조 (18줄, 20줄) | 예 (참조 대체) |
| skills/dtp-test-scenario/SKILL.md | version-mgr 참조 | 예 (참조 대체) |
| skills/dtp-analysis/SKILL.md | version-mgr 참조 (132줄) | 예 (참조 대체) |
| skills/wireframe-builder/SKILL.md | version-mgr 참조 (80줄) | 예 (참조 대체) |
| skills/dtp-analysis/references/tech-context-guide.md | version-mgr + doc-writer 나열 (81줄) | 예 (참조 대체) |
| skills/dtp-todo/references/execute-plan-guide.md | version-mgr 카탈로그 (66줄) | 예 (참조 대체) |
| skills/dev-task-pilot/references/execute-plan-guide.md | version-mgr 카탈로그 (66줄) | 예 (참조 대체) |
| CLAUDE.md | 소스 구조 + 의존 관계 (162~172줄) | 예 (구조 업데이트) |
| opal/core/references/skills.md | 스킬 레지스트리 소스 (24, 26줄) | 예 (스킬 제거/등록) |

### 1.2 아키텍처 패턴

**오케스트레이터 패턴 분석** (otp-dev, otp-dev-short 참조):
- 단계별 워커 디스패치 구조 (dtp-{stage} 워커 호출)
- 각 단계 완료 시 QA 에이전트 호출 후 PM 검토
- 단계별 산출물(.md 파일) 생성
- 사용자 승인 게이트를 통한 단계 진행
- STATE.md 관리로 작업 추적

**문서 작성 스킬 참조**:
- doc-writer: 표준 템플릿(헤더, 섹션, 변경이력)과 언어 규칙만 정의
- version-mgr: 버전 넘버링(Major/Minor) + 파일 관리(이전 버전 보존)
- doc-coauthoring (커뮤니티): Context Gathering → Refinement & Structure → Reader Testing 3단계

**파이프라인 설계 원칙**:
- otp-dev-short 모델: 3단계 파이프라인(TASK → PLAN → EXECUTE)
- otp-dev 모델: 4단계 파이프라인(TASK → ANALYSIS → PLAN+TEST-SCENARIO → EXECUTE)
- otp-write는 문서 전용이므로 EXECUTE가 WRITE로 변경됨 (코드 작성 아님)

### 1.3 의존성 맵

**신규 스킬(otp-write) 의존성**:
```
otp-write
  ├── dtp-task (직접 호출: STEP 1)
  │    └── dtp-task/personas/service-planner.md
  ├── opal-doc-standard.md (직접 참조: STEP 2 검토 시)
  ├── dtp-qa (간접 호출: PLAN 검토, 선택)
  └── dtp-execute 유사 구조 참조 (STEP 3 작성)
```

**통합 대상(삭제 예정)의 의존성**:
- doc-writer 참조 스킬: opal-skill-creator, opal-agent-creator, dtp-analysis/tech-context-guide.md
- version-mgr 참조 스킬: opal-skill-creator, opal-agent-creator, dtp-test-scenario, dtp-analysis, wireframe-builder, dtp-analysis/tech-context-guide.md, dtp-todo/execute-plan-guide.md, dev-task-pilot/execute-plan-guide.md

**새 참조(opal-doc-standard 대체)**:
- 6개 스킬 SKILL.md 파일의 의존 테이블 수정
- 2개 가이드 파일의 스킬 카탈로그 업데이트
- CLAUDE.md 의존 관계 섹션 업데이트
- skills.md 레지스트리 업데이트 (삭제/등록)

### 1.4 테스트 현황

- OPAL 프레임워크는 현재 문서 기반 검증(dtp-qa 에이전트)만 사용
- 단위 테스트/통합 테스트는 코드 변경이 수반되는 작업(otp-dev)에만 적용됨
- otp-write는 문서 산출물이므로 dtp-qa 검증 중심

## 2. 외부 조사 결과

### 2.1 라이브러리/API 조사

- 신규 외부 의존성 없음. OPAL 프레임워크 내부 컴포넌트만 조합
- 기존 dtp-task, dtp-qa, 오케스트레이터 구조 재활용

### 2.2 버전 호환성

- otp-dev-short: v1.2 (2026-03-28 업데이트, TEST-SCENARIO 문서 전용 스킵 조건 추가)
- otp-dev: Full Task 파이프라인 모델
- dtp-task, dtp-qa: 기존 스킬 재사용 (수정 없음)

## 3. 영향 범위

### 3.1 직접 영향

**신규 생성**:
- otp-write/SKILL.md (200줄 이내)
- ~/.opal/references/opal-doc-standard.md (120줄 이내)

**삭제**:
- skills/doc-writer/SKILL.md (72줄)
- skills/version-mgr/SKILL.md (75줄)

**수정 대상 (6개 스킬 SKILL.md)**:
- opal-skill-creator/SKILL.md: Line 18, 19 (의존 테이블)
- opal-agent-creator/SKILL.md: Line 20, 21 (의존 테이블)
- dtp-test-scenario/SKILL.md: version-mgr 참조 제거/대체
- dtp-analysis/SKILL.md: version-mgr 참조 (132줄)
- wireframe-builder/SKILL.md: version-mgr 참조 (80줄)

**수정 대상 (2개 참조 가이드)**:
- dtp-analysis/references/tech-context-guide.md: 범용 스킬 나열 (81줄)
- dtp-todo/references/execute-plan-guide.md: 스킬 카탈로그 (66~70줄)
- dev-task-pilot/references/execute-plan-guide.md: 스킬 카탈로그 (66~70줄)

**수정 대상 (문서)**:
- CLAUDE.md: 의존 관계 섹션 (162~172줄) + 소스 구조 테이블
- opal/core/references/skills.md: 레지스트리 (24, 26줄 + 등록)

### 3.2 간접 영향

**스킬 호출 경로**:
- opal-skill-creator 사용자: doc-writer → opal-doc-standard 학습 필요 없음 (동일 규칙)
- opal-agent-creator 사용자: version-mgr → opal-doc-standard 학습 필요 없음 (동일 규칙)

**뿐만 아니라 프로젝트 전체**:
- 모든 .md 파일 생성 스킬이 opal-doc-standard 참조 (doc-writer 대체)
- 모든 산출물 수정 작업이 opal-doc-standard 버전 규칙 준수 (version-mgr 대체)

**설치 및 배포**:
- install-mac.sh: 신규 스킬(otp-write) 배포, 삭제 스킬 제거
- ~/.opal/references/opal-doc-standard.md: 신규 참조 파일 배포

### 3.3 영향 범위 요약

- [x] DB 스키마 변경: 없음
- [x] API 인터페이스 변경: 없음 (사용자 진입점은 "otp-write" 트리거로 동일)
- [x] 설정/환경변수 변경: 없음
- [x] 빌드/배포 파이프라인 변경: install-mac.sh 업데이트 필요
- [x] 공유 라이브러리 변경: OPAL 프레임워크 스킬 레지스트리 변경 (다른 프로젝트 영향 가능)

## 4. 핵심 발견 사항

1. **doc-writer vs version-mgr 통합 타당성**: 두 스킬 모두 문서 표준(언어 규칙, 템플릿, 버전 관리)을 정의하며, 다른 스킬들이 공통으로 참조한다. opal-doc-standard로 통합 시 일관성 강화 + 유지보수 단순화.

2. **otp-write는 문서 작성 전용 오케스트레이터**: 코드 변경을 동반하지 않으므로 otp-dev-short의 TEST-SCENARIO를 WRITE로 대체 가능. EXECUTE 단계는 문서 섹션별 작성 + 사용자 검토로 구성.

3. **3단계 파이프라인 차용 가능**: otp-dev-short의 TASK → PLAN → EXECUTE 구조를 활용. otp-write는 TASK → PLAN(소스조사+목차) → WRITE(실제작성) 3단계로 매핑 가능.

4. **문서 유형별 소스 조사 분기**: 기술 문서는 코드 분석, 비기술 문서는 웹 조사/인터뷰/기존 문서 참조로 다른 조사 방식 필요 (PLAN 단계에서 분기).

5. **오케스트레이터 직접 실행 원칙 준수**: 문서 작성은 사용자와 대화형 협업이 핵심이므로, otp-write는 워커 디스패치 없이 오케스트레이터가 직접 TASK/PLAN/WRITE를 수행 (dtp-task 스킬만 활용).

## 5. 제약/리스크

| 항목 | 설명 | 심각도 |
|------|------|--------|
| 참조 대체 범위 | 6개 스킬 + 2개 가이드 파일 + 메인 문서 수정. 누락 시 빌드 실패 위험 | 높음 |
| 레지스트리 동기화 | skills.md에서 doc-writer/version-mgr 제거, otp-write 등록 시 불일치 가능성 | 중간 |
| 역호환성 | opal-doc-standard.md 구조가 doc-writer/version-mgr와 100% 동일해야 기존 스킬이 정상 작동 | 높음 |
| 테스트 커버리지 | otp-write 자체는 문서이므로 dtp-qa 검증만 가능. 실제 사용 시 사용자 피드백 필요 | 중간 |
| install-mac.sh 업데이트 | 배포 스크립트에서 doc-writer/version-mgr 제거, otp-write 추가, opal-doc-standard.md 배포 | 중간 |

## 6. 기술 컨텍스트

### 6.1 기술 스택

| 카테고리 | 기술 | 버전 |
|----------|------|------|
| 문서 형식 | Markdown (.md) | - |
| 오케스트레이터 | otp-dev-short | v1.2 |
| 단계 스킬 | dtp-task | v1.0+ |
| QA 검증 | dtp-qa | v1.0+ |
| 프레임워크 | OPAL | v1.0+ |

### 6.2 추천 스킬

| 스킬 | 용도 |
|------|------|
| dtp-task | otp-write STEP 1에서 문서 유형/대상/범위 정의 |
| dtp-qa | PLAN 검토 게이트 (선택) |
| interview | 요구사항 불명확 시 보완 (STEP 2에서) |
| api-analyzer | 기술 문서(API 명세서) 작성 시 연동 |
| wireframe-builder | UI 관련 기획 문서 작성 시 연동 |

### 6.3 추천 MCP

| MCP | 용도 |
|-----|------|
| context7 | 외부 라이브러리 문서 조회 (기술 문서 작성 시) |
| WebSearch | 공식 문서/릴리스 노트 검색 (최신 정보 확인) |

## 7. 신규 스킬(otp-write) 설계 개요

### 프로세스 (3단계)

```
STEP 1: TASK (오케스트레이터 직접 실행)
  → dtp-task 활용하여 문서 유형/대상/범위/출력 형식 정의
  → STATE.md 생성

STEP 2: PLAN (오케스트레이터 직접 실행 + QA 검토)
  → 문서 유형별 소스 조사 (코드/웹/인터뷰/기존 문서)
  → 목차 + 구조 설계
  → [QA] dtp-qa 워커 호출 (선택)
  → [PM 검토] .opal/AGENT.md 기반

STEP 3: WRITE (오케스트레이터 직접 실행)
  → 섹션별 작성
  → doc-writer 베이스 적용 (언어 규칙, 템플릿)
  → version-mgr 규칙 적용 (버전 관리)
  → 사용자 검토 게이트
  → DONE.md 생성
```

### 주요 특징

- 워커 디스패치 없음 (문서 작성은 사용자와 협업 중심)
- 문서 유형별 소스 조사 방식 분기 (기술/비기술 분리)
- 사용자 검토 게이트 포함
- 커밋은 명시 요청 시만 수행
- 200줄 이내 유지
