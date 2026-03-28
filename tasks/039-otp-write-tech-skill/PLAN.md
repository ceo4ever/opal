# PLAN: otp-write-tech 기술 산출물 네트워크 오케스트레이터

> 작성일: 2026-03-28
> 입력: TASK.md, ANALYSIS.md
> 출력: PLAN.md

## 1. 코드 분석

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| skills/otp-write/SKILL.md | 단일 문서 오케스트레이터 (PLAN+WRITE 패턴 재활용 대상) | 아니오 |
| skills/otp-dev/SKILL.md | Full Task 오케스트레이터 (STATE.md 패턴 참조) | 아니오 |
| skills/otp-dev-short/SKILL.md | Short Task 오케스트레이터 (게이트 패턴 참조) | 아니오 |
| opal/core/references/opal-doc-standard.md | 문서 표준 (버전, 헤더, 언어 규칙) | 아니오 |
| ~/.opal/references/skills.md | 스킬 레지스트리 | 예 (등록) |
| ~/.opal/references/skill-guide.md | 스킬 퀵 가이드 | 예 (등록) |

### 현재 구현

**오케스트레이터 공통 패턴** (otp-dev, otp-dev-short, otp-write 공통):
- YAML frontmatter: `name`, `description` (트리거 키워드 포함)
- STATE.md로 진행 상태 추적
- 게이트 체크포인트: 단계 완료 시 사용자 보고 + 승인 대기
- 프로젝트 메모리 동기화 (MEMORY.md 존재 시)
- 스킬 탐색 경로: 프로젝트 로컬 -> 글로벌

**otp-write 파이프라인** (162줄):
```
dtp-task -> 소스 조사 + 목차 설계 -> [QA] -> 검토/승인
  -> 섹션별 작성 -> opal-doc-standard 적용 -> 완료
```
- STEP 1 (TASK): 직접 수행 (dtp-task 호출)
- STEP 2 (PLAN): 직접 수행 (소스 조사 + 목차 설계)
- STEP 3 (WRITE): 직접 수행 (섹션별 순차 작성)

**otp-dev STATE.md 패턴**: 단계별 상태 + 완료 산출물 테이블 + 의사결정 로그 + 블로커

### 영향 범위

- 기존 오케스트레이터(otp-write, otp-dev, otp-dev-short)는 변경 없음
- otp-write-tech는 otp-write의 PLAN+WRITE 패턴을 **호출**하여 재활용 (코드 변경 없이 참조)
- skills.md, skill-guide.md에 등록 추가

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| 1 | skills/otp-write-tech/SKILL.md | 오케스트레이터 본체 (200줄 이내) |
| 2 | skills/otp-write-tech/references/network-guide.md | 논리적 연결 관리 상세 가이드 |
| 3 | skills/otp-write-tech/references/consistency-rules.md | 정합성 검증 체크리스트 |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 4 | ~/.opal/references/skills.md | otp-write-tech 행 추가 (프레임워크 스킬 테이블) |
| 5 | ~/.opal/references/skill-guide.md | otp-write-tech 행 추가 (스킬 목록 테이블) |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | 논리적 연결 관리 가이드 작성 | references/network-guide.md | 보통 |
| 2 | 정합성 검증 규칙 작성 | references/consistency-rules.md | 보통 |
| 3 | SKILL.md 본체 작성 | SKILL.md | 높음 |
| 4 | skills.md 레지스트리 등록 | skills.md | 쉬움 |
| 5 | skill-guide.md 가이드 등록 | skill-guide.md | 쉬움 |

> 의존성: references를 먼저 작성해야 SKILL.md에서 정확한 파일명과 역할을 참조할 수 있다.

### 핵심 설계

#### SKILL.md 구조 (200줄 이내)

```
---
name: otp-write-tech
description: |
  **기술 산출물 네트워크 오케스트레이터**. 서비스 기획의 기술 산출물을 논리적 네트워크로 관리한다.
  반드시 이 스킬을 사용해야 하는 상황: "otp-write-tech", "otpwt", "기획 문서 세트 작성", "기술 산출물 작성".
  단일 독립 문서는 otp-write, 코드 구현은 otp-dev/otp-dev-short, 와이어프레임은 otp-wf.
---
```

**파이프라인:**
```
TASK -> 네트워크 초기화 -> 산출물별 PLAN+WRITE (otp-write 재활용)
  -> 정합성 검증 -> [다음 산출물 반복] -> 완료
```

**STEP 구성:**

| STEP | 이름 | 수행 방식 | 핵심 내용 |
|------|------|----------|----------|
| 1 | TASK | 직접 수행 | dtp-task 호출 + 필요 산출물 목록 + 순서 결정. STATE.md 생성 (네트워크 상태 포함) |
| 2 | 산출물 작성 (반복) | 직접 수행 | 산출물별 otp-write STEP2(PLAN) + STEP3(WRITE) 패턴 재활용. 연결 문서 자동 Read + 참조. 게이트 체크포인트 (산출물마다 사용자 확인) |
| 3 | 정합성 검증 | 직접 수행 | 네트워크 전체 정합성 체크 (consistency-rules.md 기반). 불일치 발견 시 연쇄 업데이트 제안. 사용자 승인 후 수정 |
| 4 | 완료 | 직접 수행 | DONE.md 생성 + STATE.md 갱신 |

**모드 분기:**

| 모드 | 진입 조건 | 동작 |
|------|----------|------|
| 작성 모드 (기본) | 새 산출물 작성 | 연결 문서 탐색 + Read -> PLAN -> WRITE |
| 수정 모드 | 기존 산출물 수정 요청 | 영향 분석 (network-guide.md 기반) -> 수정 -> 연쇄 업데이트 제안 |

**네트워크 정의 (SKILL.md에 인라인):**

```
필수 산출물 (순서 체인):
  PRD -> TRD -> 서비스 정책서 -> IA(기능 포함)

선택 산출물:
  기능도(->IA), 순서도(->IA), 운영 정책서(->서비스정책서,IA), 서비스 매뉴얼(->IA,운영정책서)

연결 규칙:
  - 순서 체인은 기본 흐름이지 강제가 아님
  - 어떤 산출물이든 먼저 작성 가능
  - 작성 시: 연결 문서가 존재하면 Read하여 참고
  - 수정 시: 연결 문서 영향 분석 -> 연쇄 업데이트 제안
```

**STATE.md 확장 (네트워크 상태 추적):**

기존 STATE.md 패턴에 "네트워크 상태" 섹션 추가:
```markdown
## 네트워크 상태
| 산출물 | 상태 | 버전 | 경로 | 연결 문서 |
|--------|------|------|------|----------|
| PRD | 작성됨 | v1.0 | docs/PRD_v1.0.md | TRD, 서비스정책서, IA |
| TRD | 미작성 | - | - | PRD, IA |
```

**IA 형식 처리:**
- .xlsx 추천: anthropics/xlsx 커뮤니티 스킬 Read 후 연동
- .md 폴백: 사용자가 .xlsx 불필요 시 마크다운으로 작성

**otp-write 재활용 방식:**
- otp-write의 STEP2(PLAN) + STEP3(WRITE) 패턴을 otp-write-tech가 **직접 수행**
- otp-write를 서브 스킬로 호출하는 것이 아니라, 동일한 패턴(소스 조사 -> 목차 설계 -> 섹션별 작성)을 otp-write-tech 내에서 반복 적용
- 이유: otp-write는 TASK부터 시작하는 독립 파이프라인이므로, 중간 단계만 추출 재활용

#### network-guide.md 구조

| 섹션 | 내용 |
|------|------|
| 산출물 정의 | 필수 4종 + 선택 4종의 상세 설명, 목적, 구성 |
| 논리적 연결 맵 | 산출물 간 연결 관계 상세 (방향성, 참조 항목) |
| 작성 시 연결 활용 | 연결 문서 Read + 참조 범위 (어떤 섹션을 어떻게 참고하는지) |
| 수정 시 영향 분석 | 수정 유형별 영향 범위, 연쇄 업데이트 판단 기준 |
| IA 형식 가이드 | .xlsx 작성 시 시트 구성, 컬럼 정의, anthropics/xlsx 연동 |

#### consistency-rules.md 구조

| 섹션 | 내용 |
|------|------|
| 용어 일관성 | 동일 개념의 용어가 문서 간 통일되어야 함 |
| 범위 일관성 | PRD 범위 = TRD 범위 = IA 기능 범위 |
| 기능 목록 일관성 | PRD 요구사항 -> IA 기능 매핑 누락 없는지 |
| 정책 일관성 | 서비스 정책서 규칙이 IA/TRD에 반영되었는지 |
| 검증 체크리스트 | 각 산출물 쌍별 검증 항목 (PRD-TRD, PRD-IA, TRD-IA 등) |

### 의존성 및 환경 변경

- 추가 패키지: 없음
- 환경 설정 변경: 없음
- 참조 스킬: opal-doc-standard.md (문서 표준), anthropics/xlsx (IA 작성, 선택)
- **참조하지 않는 스킬**: version-mgr (삭제됨), doc-writer (삭제됨) -- opal-doc-standard.md로 통합됨

### 테스트 전략

문서 전용 작업이므로 execution-plan.json은 생성하지 않음.

| 테스트 종류 | 성공 기준 |
|------------|----------|
| SKILL.md 줄 수 | 200줄 이내 |
| 패턴 정합성 | 기존 오케스트레이터(otp-write, otp-dev) 패턴과 일관성 유지 |
| references 분리 | 상세 가이드가 references/에 분리되어 SKILL.md가 간결한지 |
| 레지스트리 등록 | skills.md + skill-guide.md에 정확히 등록되었는지 |
| 교차 참조 정확성 | 삭제된 스킬(version-mgr, doc-writer) 미참조 확인 |

---

## 3. 실행 체크리스트

- [ ] Step 1: network-guide.md 작성 -- `skills/otp-write-tech/references/network-guide.md` -- 산출물 정의 + 논리적 연결 맵 + 작성/수정 시 활용법 + IA 형식 가이드
- [ ] Step 2: consistency-rules.md 작성 -- `skills/otp-write-tech/references/consistency-rules.md` -- 용어/범위/기능/정책 일관성 규칙 + 산출물 쌍별 검증 체크리스트
- [ ] Step 3: SKILL.md 작성 -- `skills/otp-write-tech/SKILL.md` -- 200줄 이내, frontmatter + 파이프라인 + STEP 1~4 + 모드 분기 + 네트워크 정의 + STATE.md 확장 + 게이트 체크포인트
- [ ] Step 4: skills.md 등록 -- `~/.opal/references/skills.md` -- 프레임워크 스킬 테이블에 otp-write-tech 행 추가
- [ ] Step 5: skill-guide.md 등록 -- `~/.opal/references/skill-guide.md` -- 스킬 목록 테이블에 otp-write-tech 행 추가

---

## 4. QA 체크리스트

### 기능 테스트
- [ ] SKILL.md가 200줄 이내인가
- [ ] YAML frontmatter에 name, description이 올바르게 정의되었는가
- [ ] 파이프라인(TASK -> 네트워크 초기화 -> 산출물 PLAN+WRITE -> 정합성 검증 -> 완료)이 명확한가
- [ ] 작성 모드 / 수정 모드 분기가 정의되었는가
- [ ] otp-write의 PLAN+WRITE 패턴 재활용이 명확히 기술되었는가
- [ ] 네트워크 정의 (필수 4종 + 선택 4종, 연결 관계)가 포함되었는가
- [ ] STATE.md에 네트워크 상태 섹션이 추가되었는가
- [ ] IA .xlsx 형식 지원 (anthropics/xlsx 연동)이 기술되었는가
- [ ] 게이트 체크포인트 (산출물마다 사용자 확인)가 정의되었는가

### 회귀 테스트
- [ ] 기존 otp-write SKILL.md에 변경이 없는가
- [ ] 기존 otp-dev / otp-dev-short SKILL.md에 변경이 없는가
- [ ] skills.md의 기존 항목이 훼손되지 않았는가
- [ ] skill-guide.md의 기존 항목이 훼손되지 않았는가

### 코드 품질
- [ ] version-mgr, doc-writer를 참조하지 않는가 (삭제된 스킬)
- [ ] opal-doc-standard.md만 문서 표준으로 참조하는가
- [ ] 기존 오케스트레이터의 네이밍/구조 패턴과 일관성이 있는가 (frontmatter, STATE.md, 게이트 등)
- [ ] references/ 파일이 SKILL.md에서 정확한 상대경로로 참조되는가
- [ ] 스킬 탐색 경로가 표준 패턴을 따르는가 (프로젝트 로컬 -> 글로벌)

---

## 5. 기술 컨텍스트

### 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 문서 포맷 | Markdown (.md 기본) | opal-doc-standard |
| 스프레드시트 | .xlsx (IA 전용, 선택) | anthropics/xlsx |
| 오케스트레이터 패턴 | OPAL 스킬 프레임워크 | otp-write, otp-dev (패턴 참조) |

### 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| N/A | 문서 전용 작업으로 MCP 불필요 |

---

## 6. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| 200줄 초과 | SKILL.md 복잡도 증가 | 상세 가이드를 references/로 철저히 분리. 네트워크 정의는 인라인 최소화, 연결 맵 상세는 network-guide.md |
| otp-write 재활용 범위 모호 | 구현 시 패턴 오해 | SKILL.md에 "재활용 방식" 섹션을 명시하여, otp-write를 호출하는 것이 아니라 패턴을 직접 수행함을 명확히 기술 |
| 수정 모드의 영향 분석 복잡성 | 연쇄 업데이트 범위 과다 | consistency-rules.md에 "영향 수준"(직접/간접) 구분을 두어 합리적 범위 제한 |
| anthropics/xlsx 미설치 | IA .xlsx 생성 불가 | .md 폴백 명시. xlsx 미설치 시 마크다운 테이블로 IA 작성 |

---

변경이력:

| 버전 | 날짜 | 작성자 | 변경내용 |
|------|------|--------|---------|
| v1.0 | 2026-03-28 | R2 | 초기 작성 |
