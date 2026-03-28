# PLAN: otp-write 범용 문서 작성 오케스트레이터 개발

> 작성일: 2026-03-29
> 입력: TASK.md, ANALYSIS.md
> 출력: PLAN.md

## 1. 코드 분석

ANALYSIS.md의 분석 결과를 기반으로 요약한다.

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| skills/otp-dev-short/SKILL.md | 3단계 오케스트레이터 구조 참조 템플릿 | 아니오 |
| skills/doc-writer/SKILL.md | 현재 doc-writer (72줄) | 삭제 |
| skills/version-mgr/SKILL.md | 현재 version-mgr (75줄) | 삭제 |
| skills/opal-skill-creator/SKILL.md | version-mgr + doc-writer 의존 테이블 (18~19줄) | 예 |
| skills/opal-agent-creator/SKILL.md | version-mgr + doc-writer 의존 테이블 (20~21줄) | 예 |
| skills/dtp-test-scenario/SKILL.md | version-mgr 참조 (118줄) | 예 |
| skills/dtp-analysis/SKILL.md | version-mgr 참조 (132줄) | 예 |
| skills/wireframe-builder/SKILL.md | version-mgr 참조 (80줄) | 예 |
| skills/dtp-analysis/references/tech-context-guide.md | version-mgr + doc-writer 나열 (81줄) | 예 |
| skills/dtp-todo/references/execute-plan-guide.md | version-mgr + doc-writer 카탈로그 (66~70줄) | 예 |
| skills/dev-task-pilot/references/execute-plan-guide.md | version-mgr + doc-writer 카탈로그 (66~69줄) | 예 |
| CLAUDE.md | 소스 구조 + 의존 관계 | 예 |
| opal/core/references/skills.md | 스킬 레지스트리 (24, 26줄) | 예 |
| opal/core/references/skill-guide.md | 스킬 퀵 가이드 | 예 |

### 현재 구현

**doc-writer (72줄)**: 언어 규칙, 문서 헤더 템플릿(`# [제목]` + 메타 헤더), 문서 유형별 필수 섹션 테이블(분석서/명세서/정책서/설계서/계획서), 테이블 작성 규칙, 작업 보고 규칙을 정의. 다른 스킬이 문서 산출물 작성 시 이 스킬의 규칙을 참조한다.

**version-mgr (75줄)**: `v{Major}.{Minor}` 넘버링(구조적=Major, 내용=Minor), 파일 관리 4단계(확인→새 파일 생성→변경이력→헤더 갱신), 변경이력 테이블 형식, HTML/바이너리 파일 버전 관리. 기존 파일 덮어쓰기 금지 원칙.

**otp-dev-short (235줄)**: TASK → PLAN+TEST-SCENARIO → EXECUTE 3단계 파이프라인. 워커 디스패치 구조, STATE.md 관리, 에스컬레이션 규칙, 게이트 체크포인트, 커밋 규칙 포함.

### 영향 범위

- **참조 의존**: 6개 스킬 SKILL.md + 2개 가이드 파일이 version-mgr/doc-writer를 참조 중
- **레지스트리**: skills.md에 doc-writer(24줄), version-mgr(26줄) 등록 중
- **CLAUDE.md**: 소스 구조(64, 69줄)와 의존 관계(162~163줄)에 doc-writer/version-mgr 기재

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| 1 | skills/otp-write/SKILL.md | 범용 문서 작성 오케스트레이터 (200줄 이내) |
| 2 | opal/core/references/opal-doc-standard.md | doc-writer + version-mgr 통합 참조 문서 (120줄 이내) |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 3 | skills/opal-skill-creator/SKILL.md | 의존 테이블: version-mgr + doc-writer → opal-doc-standard |
| 4 | skills/opal-agent-creator/SKILL.md | 의존 테이블: version-mgr + doc-writer → opal-doc-standard |
| 5 | skills/dtp-test-scenario/SKILL.md | 118줄: version-mgr → opal-doc-standard |
| 6 | skills/dtp-analysis/SKILL.md | 132줄: version-mgr → opal-doc-standard |
| 7 | skills/wireframe-builder/SKILL.md | 80줄: version-mgr → opal-doc-standard |
| 8 | skills/dtp-analysis/references/tech-context-guide.md | 81줄: 범용 스킬 나열에서 version-mgr, doc-writer → opal-doc-standard |
| 9 | skills/dtp-todo/references/execute-plan-guide.md | 67, 70줄: 카탈로그에서 doc-writer, version-mgr → opal-doc-standard |
| 10 | skills/dev-task-pilot/references/execute-plan-guide.md | 66, 69줄: 카탈로그에서 doc-writer, version-mgr → opal-doc-standard |
| 11 | CLAUDE.md | 소스 구조: doc-writer/version-mgr 삭제, otp-write 추가. 의존 관계: doc-writer/version-mgr → opal-doc-standard |
| 12 | opal/core/references/skills.md | doc-writer/version-mgr 삭제, otp-write 등록 |
| 13 | opal/core/references/skill-guide.md | otp-write 행 추가 |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| 14 | skills/doc-writer/SKILL.md | opal-doc-standard.md로 통합 |
| 15 | skills/version-mgr/SKILL.md | opal-doc-standard.md로 통합 |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | opal-doc-standard.md 신규 생성 | opal/core/references/opal-doc-standard.md | 보통 |
| 2 | otp-write/SKILL.md 신규 생성 | skills/otp-write/SKILL.md | 높음 |
| 3 | 참조 대체 — 스킬 SKILL.md (5개) | opal-skill-creator, opal-agent-creator, dtp-test-scenario, dtp-analysis, wireframe-builder | 쉬움 |
| 4 | 참조 대체 — 가이드 파일 (3개) | tech-context-guide.md, execute-plan-guide.md x2 | 쉬움 |
| 5 | CLAUDE.md 업데이트 | CLAUDE.md | 보통 |
| 6 | 레지스트리 업데이트 | skills.md, skill-guide.md | 쉬움 |
| 7 | 기존 스킬 디렉토리 삭제 | skills/doc-writer/, skills/version-mgr/ | 쉬움 |

**의존성**: 1번(opal-doc-standard)이 완료되어야 3~4번(참조 대체)에서 정확한 참조 경로를 기술할 수 있다. 2번(otp-write)은 1번과 독립적으로 작성 가능하나, opal-doc-standard를 참조하므로 1번 이후가 자연스럽다. 7번(삭제)은 모든 참조 대체 완료 후 마지막에 수행한다.

### 핵심 설계

#### opal-doc-standard.md (120줄 이내)

doc-writer와 version-mgr의 핵심을 통합한 참조 전용 문서. 사용자 트리거 없음, 레지스트리 미등록.

**구조**:
```
# OPAL 문서 표준 (opal-doc-standard)
> 참조 전용 — 다른 스킬이 문서 산출물 작성/수정 시 이 규칙을 따른다.

## 1. 언어 규칙
- 프로젝트 CLAUDE.md/컨벤션 우선
- 기본: 본문 한국어, 코드/변수/필드명 영어

## 2. 문서 헤더 템플릿
# [문서 제목]
> 작성일: YYYY-MM-DD | 작성자: [작성자명] | 버전: v{X.Y}

## 3. 문서 유형별 필수 섹션
(분석서/명세서/정책서/설계서/계획서 테이블 — doc-writer 계승)

## 4. 테이블 작성 규칙
(doc-writer 계승)

## 5. 버전 넘버링 규칙
### v{Major}.{Minor}
- Major: 구조적 변경 (섹션 추가/삭제, 아키텍처 변경)
- Minor: 내용 수정 (보강, 오류 수정)

## 6. 파일 관리 프로세스
### 신규 산출물: 새 파일 생성, v1.0
### 기존 산출물 수정: 변경 범위 → Major/Minor → 새 파일 or 직접 Edit
- Major: 새 파일 생성 (이전 버전 보존)
- Minor: 기존 파일 직접 Edit (파일명 유지)

## 7. 변경이력 테이블 형식
(version-mgr 계승)

## 8. HTML/바이너리 파일 버전 관리
(version-mgr 계승)

## 9. 작업 보고 규칙
(doc-writer 계승)
```

#### otp-write/SKILL.md (200줄 이내)

otp-dev-short의 3단계 파이프라인을 기반으로, EXECUTE를 WRITE로 대체한 문서 전용 오케스트레이터.

**핵심 차이점 (vs otp-dev-short)**:
- 워커 디스패치 없음 — 오케스트레이터가 3단계 모두 직접 수행
- STEP 3이 WRITE (문서 섹션별 작성) — EXECUTE(코드 작성)가 아님
- TEST-SCENARIO 없음 — 코드 변경이 없으므로
- execution-plan.json 없음 — FE/BE 작업이 없으므로
- 문서 유형별 소스 조사 분기 (STEP 2에서)

**구조**:
```yaml
---
name: otp-write
description: |
  **범용 문서 작성 오케스트레이터**. 코드 변경 없이 단일 문서를 체계적으로 작성하는 3단계 파이프라인.
  반드시 이 스킬을 사용해야 하는 상황: "otp-write", "otpw", 문서/보고서/가이드/기획서/제안서 작성 요청 시.
  코드 구현이 수반되면 otp-dev/otp-dev-short, 프로젝트 파일럿은 opdp, API 분석은 api-analyzer.
---
```

```
# 범용 문서 작성 오케스트레이터

## 구현 금지 원칙 (최우선 규칙)
(otp-dev-short 계승 — 사용자 승인 전 코드 작성 금지)

## 파이프라인
dtp-task → 소스 조사 + 목차 설계 → [QA] → 사용자 검토
  → 섹션별 작성 → opal-doc-standard 적용 → 사용자 검토 → DONE.md

## 커버 범위
### 가능한 문서 유형
(TASK.md의 otp-write 커버 범위 반영)
### otp-write가 아닌 것
(코드=otp-dev, 프로젝트 파일럿=opdp, 와이어프레임=otp-wf, API=api-analyzer)

## STEP 1: TASK (직접 수행)
1. dtp-task/SKILL.md Read
2. 스킬 프로세스에 따라 TASK.md 작성 (문서 유형/대상/범위/출력 형식 정의)
3. STATE.md 생성
4. 사용자 보고

## STEP 2: PLAN (직접 수행 + QA 선택)
### 소스 조사 (문서 유형별 분기)
| 문서 유형 | 소스 조사 방식 |
|-----------|-------------|
| 기술 산출물 (설계서, 명세서 등) | Glob/Grep/Read로 코드 분석 |
| 보고서 | 코드 분석 + WebSearch로 외부 정보 |
| 가이드/매뉴얼 | 코드 분석 + 기존 문서 참조 |
| 기획/제안 | WebSearch + interview 스킬 활용 |
| 내부 커뮤니케이션 | 기존 문서/데이터 참조 |

### 목차 + 구조 설계
- opal-doc-standard.md 참조하여 문서 헤더, 유형별 필수 섹션 반영
- 목차와 각 섹션별 핵심 내용 개요 정의

### QA (선택)
dtp-qa 워커 호출 (복잡한 문서일 경우)

### 사용자 검토 게이트
목차/구조를 사용자에게 제시, 승인 시 STEP 3 진행

## STEP 3: WRITE (직접 수행)
1. 섹션별 순차 작성
2. opal-doc-standard 규칙 적용 (언어, 헤더, 테이블, 버전)
3. 출력 형식 처리:
   - .md: 기본 출력
   - .docx: anthropics/docx 커뮤니티 스킬 연동
   - .pdf: anthropics/pdf 커뮤니티 스킬 연동
4. 사용자 검토 게이트 (완성본 제시)
5. DONE.md 생성

## 커밋 규칙
사용자 명시 요청 시에만 수행

## STATE.md 관리
(otp-dev-short 동일 구조, 단계명만 TASK/PLAN/WRITE로 변경)

## 스킬 탐색 경로
dtp-task: {프로젝트}/.opal/skills/dtp-task/SKILL.md → ~/.opal/skills/dtp-task/SKILL.md
dtp-qa: {프로젝트}/.opal/skills/dtp-qa/SKILL.md → ~/.opal/skills/dtp-qa/SKILL.md

## 게이트 체크포인트
각 단계 완료 시 사용자 보고 + 승인 대기

## 변경이력
| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-03-29 | 초기 작성 |
```

#### 참조 대체 패턴

**스킬 SKILL.md 의존 테이블 (opal-skill-creator, opal-agent-creator)**:
- 기존 2행(version-mgr + doc-writer)을 1행(opal-doc-standard)으로 통합
- 역할: "문서 표준 + 버전 관리 규칙 참조"
- 탐색 경로: `~/.opal/references/opal-doc-standard.md`

**스킬 SKILL.md 본문 참조 (dtp-test-scenario, dtp-analysis, wireframe-builder)**:
- "version-mgr 규칙에 따라 버전 관리한다" → "opal-doc-standard 규칙에 따라 버전 관리한다"

**가이드 파일 카탈로그 (execute-plan-guide.md x2, tech-context-guide.md)**:
- doc-writer, version-mgr 행을 삭제하고 opal-doc-standard 1행으로 대체
- tech-context-guide.md: "범용 스킬" 나열에서 "version-mgr, doc-writer 등" → "opal-doc-standard 등"

**CLAUDE.md 소스 구조**:
- `doc-writer/` 행 삭제
- `version-mgr/` 행 삭제
- `otp-write/` 행 추가 (오케스트레이터 블록에, otp-wf 다음)

**CLAUDE.md 의존 관계**:
- `doc-writer → ...` 행 삭제
- `version-mgr → ...` 행 삭제
- `opal-doc-standard → 모든 문서 산출물의 표준 규칙 (doc-writer + version-mgr 통합)` 추가

**skills.md 레지스트리**:
- doc-writer 행 삭제 (24줄)
- version-mgr 행 삭제 (26줄)
- otp-write 행 추가: `| otp-write | "otp-write", "otpw" — 문서/보고서/가이드 작성 요청 시 | 범용 문서 작성 오케스트레이터 |`

**skill-guide.md**:
- 테이블에 otp-write 행 추가: `| 문서 | otp-write | //otp-write , //otpw | 문서/보고서/가이드 등 단일 문서 작성 | //otpw PRD 작성해줘 | |`

### 의존성 및 환경 변경

- 신규 패키지: 없음
- 환경 설정: 없음
- install-mac.sh: 이번 태스크 범위 제외 (별도 태스크)

### 테스트 전략

- **문서 전용 작업**: 코드 테스트 없음
- **검증 방법**: dtp-qa 에이전트로 산출물 검증
- **참조 정합성**: 모든 수정 파일에서 "version-mgr", "doc-writer" 문자열이 0건인지 Grep 확인
- **레지스트리 일관성**: skills.md에서 otp-write 등록 확인, doc-writer/version-mgr 미존재 확인

## 3. 실행 체크리스트

- [ ] Step 1: opal-doc-standard.md 생성 -- opal/core/references/opal-doc-standard.md -- doc-writer + version-mgr 핵심 내용 통합, 120줄 이내
- [ ] Step 2: otp-write/SKILL.md 생성 -- skills/otp-write/SKILL.md -- 3단계 오케스트레이터, otp-dev-short 구조 기반, 200줄 이내
- [ ] Step 3: 스킬 참조 대체 (5개) -- opal-skill-creator, opal-agent-creator, dtp-test-scenario, dtp-analysis, wireframe-builder -- version-mgr/doc-writer → opal-doc-standard
- [ ] Step 4: 가이드 참조 대체 (3개) -- tech-context-guide.md, execute-plan-guide.md x2 -- 카탈로그에서 doc-writer/version-mgr → opal-doc-standard
- [ ] Step 5: CLAUDE.md 업데이트 -- CLAUDE.md -- 소스 구조에서 doc-writer/version-mgr 삭제, otp-write 추가 + 의존 관계 업데이트
- [ ] Step 6: 레지스트리 업데이트 -- skills.md, skill-guide.md -- doc-writer/version-mgr 삭제, otp-write 등록
- [ ] Step 7: 기존 스킬 삭제 -- skills/doc-writer/, skills/version-mgr/ -- 디렉토리 삭제
- [ ] Step 8: 참조 정합성 검증 -- Grep으로 전체 프로젝트에서 "version-mgr", "doc-writer" 잔존 참조 확인 (ANALYSIS.md, TASK.md, PLAN.md 등 태스크 산출물 제외)

## 4. QA 체크리스트

### 기능 테스트
- [ ] otp-write/SKILL.md가 200줄 이내인가
- [ ] opal-doc-standard.md가 120줄 이내인가
- [ ] otp-write 파이프라인이 3단계(TASK → PLAN → WRITE)로 구성되었는가
- [ ] otp-write가 워커 디스패치 없이 직접 수행하도록 설계되었는가
- [ ] opal-doc-standard가 doc-writer의 핵심 내용(언어 규칙, 헤더 템플릿, 유형별 필수 섹션, 테이블 규칙)을 포함하는가
- [ ] opal-doc-standard가 version-mgr의 핵심 내용(버전 넘버링, 파일 관리, 변경이력)을 포함하는가
- [ ] 참조 대체 대상 11개 파일 모두에서 version-mgr/doc-writer → opal-doc-standard 대체가 완료되었는가

### 회귀 테스트
- [ ] 프로젝트 전체에서 "version-mgr" 참조가 태스크 산출물 외에 0건인가 (Grep 검증)
- [ ] 프로젝트 전체에서 "doc-writer" 참조가 태스크 산출물 외에 0건인가 (Grep 검증)
- [ ] skills.md 레지스트리에 otp-write가 등록되었는가
- [ ] skills.md 레지스트리에서 doc-writer/version-mgr가 삭제되었는가
- [ ] skill-guide.md에 otp-write가 추가되었는가
- [ ] CLAUDE.md 소스 구조가 정확한가 (otp-write 추가, doc-writer/version-mgr 삭제)
- [ ] CLAUDE.md 의존 관계가 정확한가 (opal-doc-standard 추가, doc-writer/version-mgr 삭제)

### 코드 품질
- [ ] 모든 .md 파일이 프로젝트 언어 규칙을 따르는가 (본문 한국어, 코드/필드명 영어)
- [ ] otp-write SKILL.md의 YAML frontmatter에 name, description이 정의되어 있는가
- [ ] opal-doc-standard.md가 참조 전용으로 사용자 트리거가 없는가

## 5. 기술 컨텍스트

### 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 문서 형식 | Markdown (.md) | - |
| 오케스트레이터 참조 | otp-dev-short | 파이프라인 구조 차용 |
| 단계 스킬 | dtp-task | otp-write STEP 1 재활용 |
| QA | dtp-qa | PLAN 검토 (선택) |

### 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| - | 문서 전용 작업으로 MCP 조회 불필요 |

## 6. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| 참조 대체 누락 | 기존 스킬이 삭제된 doc-writer/version-mgr를 참조하여 오류 | Step 8에서 Grep으로 전수 검증 |
| opal-doc-standard가 기존 규칙과 불일치 | 기존 스킬이 의존하는 규칙이 변경되어 동작 불일치 | doc-writer/version-mgr 원문을 그대로 통합, 규칙 변경 없이 구조만 합침 |
| otp-write 줄 수 초과 | 200줄 제약 위반 | 커버 범위/STATE 템플릿 등 반복 구조를 간결하게 표현 |
| install-mac.sh 미반영 | 배포 시 otp-write 미포함, 삭제 스킬 잔존 | 별도 태스크로 분리됨 (TASK.md 제약조건) |
