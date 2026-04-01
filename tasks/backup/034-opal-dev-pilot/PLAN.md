# PLAN: opal-project-dev-pilot 스킬 개발

> 작성일: 2026-03-27
> 입력: TASK.md
> 출력: PLAN.md

## 1. 코드 분석

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `skills/opal-project-init/SKILL.md` | opi 스킬 — 완료 후 opdp 자동 호출 연동 | ✅ 명칭 교체 |
| `opal/core/references/skills.md` | 스킬 레지스트리 | ✅ opdp 항목 추가 |
| `opal/core/references/skill-guide.md` | 스킬 퀵 가이드 | ✅ opdp 항목 추가 |
| `opal/core/AGENT.md` | 글로벌 에이전트 — PM 역할 정의 | 참조만 |
| `skills/otp-dev/SKILL.md` | Full Task — Phase 4에서 호출 | 참조만 |
| `skills/otp-dev-short/SKILL.md` | Short Task — Phase 4에서 호출 | 참조만 |
| `skills/otp-wf/SKILL.md` | Wireframe — Phase 4에서 호출 | 참조만 |

### 현재 구현

**opi → opdp 연동 현황**:
- opi SKILL.md Phase 4에서 `opal-dev-builder`를 참조 (구 명칭)
- 미존재 시 otp-dev로 폴백하도록 되어 있음
- `opal-project-dev-pilot` (약식 `//opdp`)으로 명칭 변경 필요

**PM 검수 패턴**:
- `opal/core/AGENT.md`의 "PM 검토 게이트"에 표준 검토 절차 정의됨
- 검토: 참조 문서 전달 → PM 기준 체크 → 정합성 → 금지사항
- 판정: Pass → 소유자 보고, Fail → 재지시 (최대 1회)

**스킬 배포 구조**:
- OPAL 전용 스킬: `opal/skills/` → `~/.opal/skills/`로 배포
- opdp는 `opal/skills/opal-project-dev-pilot/`에 위치

**호출 시나리오**:
1. opi → opdp 자동 연결: `//opi 번역 웹앱 만들어줘` → 셋업 → opdp 자동 호출
2. opdp 단독 호출 (opi 완료된 프로젝트): `//opdp PRD 작성해줘` → docs/PROJECT.md 읽고 바로 시작
3. opdp 단독 호출 (opi 미완료): `//opdp` → docs/PROJECT.md 없음 감지 → "//opi 먼저 할까요?" 안내

### 영향 범위

- opi SKILL.md: 명칭 교체 + 자동 호출 로직 갱신
- 레지스트리 2개: skills.md, skill-guide.md 갱신
- install-mac.sh: `opal/skills/` 순회 배포로 자동 포함 (별도 수정 불필요)

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| N1 | `opal/skills/opal-project-dev-pilot/SKILL.md` | opdp 스킬 본체 — 4 Phase 파이프라인 |
| N2 | `opal/skills/opal-project-dev-pilot/references/prd-guide.md` | PRD 작성 가이드 |
| N3 | `opal/skills/opal-project-dev-pilot/references/trd-guide.md` | TRD 작성 가이드 |
| N4 | `opal/skills/opal-project-dev-pilot/references/roadmap-guide.md` | 로드맵 수립 가이드 |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| M1 | `skills/opal-project-init/SKILL.md` | `opal-dev-builder` → `opal-project-dev-pilot` 명칭 교체, `//opdp` 약식 반영 |
| M2 | `opal/core/references/skills.md` | OPAL 전용 스킬 섹션에 opdp 항목 추가 |
| M3 | `opal/core/references/skill-guide.md` | 스킬 테이블에 opdp 행 추가 |

### 구현 순서

| 순서 | 작업 | 파일 | 난이도 |
|------|------|------|--------|
| 1 | SKILL.md 작성 | N1 | 높음 |
| 2 | PRD 가이드 | N2 | 보통 |
| 3 | TRD 가이드 | N3 | 보통 |
| 4 | 로드맵 가이드 | N4 | 보통 |
| 5 | opi 연동 수정 | M1 | 쉬움 |
| 6 | 레지스트리 등록 | M2, M3 | 쉬움 |

---

### 핵심 설계

#### N1: SKILL.md 구조

```yaml
---
name: opal-project-dev-pilot
description: |
  개발 프로젝트 전체 라이프사이클 관리 스킬. opi가 셋업한 프로젝트에서
  PRD/TRD 작성 → 로드맵 수립 → 태스크 순차 실행까지 관리한다.
  모든 산출물은 PM 검수 → 캡틴 확정 순서를 거친다.
  opi 없이 단독 호출도 가능 (docs/PROJECT.md 존재 시).
triggers:
  - "opal-project-dev-pilot"
  - "opdp"
  - "프로젝트 개발 시작"
  - "PRD 작성"
  - "개발 계획"
version: 1.0.0
---
```

**사전 조건 체크**:

```
//opdp 호출 시:
  docs/PROJECT.md 존재?
    YES → Phase 1 시작
    NO  → "프로젝트 셋업이 안 되어 있습니다. //opi 먼저 실행할까요?" 안내
```

**4 Phase 파이프라인**:

```
Phase 1: PRD 작성
  참조: prd-guide.md Read
  캡틴 대화 + 프로젝트 분석 → PRD 초안
  → PM 검수 (가이드 체크리스트 1:1 대조)
  → 미달 시 자체 재작성 (최대 1회)
  → PM 통과 → 캡틴 검토 요청
  → 캡틴 확정 → docs/PRD.md 생성 + PROJECT.md 문서 테이블 등록

Phase 2: TRD 작성
  참조: trd-guide.md Read
  PRD 기반 → TRD 초안
  → PM 검수 (PRD 정합성 + 기술 실현 가능성)
  → 미달 시 자체 재작성 (최대 1회)
  → PM 통과 → 캡틴 검토 요청
  → 캡틴 확정 → docs/TRD.md 생성 + PROJECT.md 문서 테이블 등록

Phase 3: 로드맵 수립
  참조: roadmap-guide.md Read
  PRD/TRD 기반 태스크 분할
  → PM 검수 (분할 적절성, 누락, 의존성)
  → PM 통과 → 캡틴 검토 요청
  → 캡틴 확정 → docs/ROADMAP.md 생성 + PROJECT.md 문서 테이블 등록

Phase 4: 태스크 순차 실행
  로드맵 순서대로 otp 스킬 호출
  → 각 태스크 완료 시 PM 검수 → 다음 태스크
  → 캡틴에게 태스크 완료 보고
  → 전체 완료 보고
```

**PM 검수 흐름 (각 Phase 공통)**:

```
산출물 작성 (알투가 직접)
  │
  ▼
PM 자체 검수
  │  참조 가이드의 체크리스트를 1:1 대조
  │  .opal/AGENT.md 검토 기준 적용
  │  참조 문서(docs/) 정합성 확인
  │
  ├─ 미달 → 자체 재작성 (최대 1회)
  │
  └─ 통과 → 캡틴 검토 요청
              │
              ├─ 캡틴 피드백 → 반영 → 재검수
              └─ 캡틴 확정 → 다음 Phase
```

캡틴은 PM이 통과시킨 결과물만 검토한다. 품질이 낮은 초안이 캡틴에게 올라가지 않는다.

**Phase 4 태스크 실행 전략**:

각 태스크에 적합한 otp 스킬을 자동 판단:

| 조건 | 스킬 |
|------|------|
| 코드 변경 10+ 파일, 다중 모듈 | `//otpd` (Full Task) |
| 코드 변경 <10 파일, 단일 모듈 | `//otpds` (Short Task) |
| 와이어프레임 + UI 구현 | `//otpwf` (Wireframe) |

**STATE.md 관리**:

opdp 전용 STATE.md를 `.opal/opdp-state.md`로 관리. 개별 태스크 STATE.md와 분리.

```markdown
# OPDP STATE: {프로젝트명}

> 최종 갱신: YYYY-MM-DD HH:mm

## 현재 Phase
- Phase: {1-PRD / 2-TRD / 3-ROADMAP / 4-EXECUTE}
- 상태: {진행 중 / PM 검수 / 캡틴 검토 대기 / 완료}

## Phase 진행 현황
| Phase | 산출물 | 상태 |
|-------|--------|------|
| 1-PRD | docs/PRD.md | {미시작 / 작성 중 / PM 검수 / 캡틴 검토 / 확정} |
| 2-TRD | docs/TRD.md | {미시작 / 작성 중 / PM 검수 / 캡틴 검토 / 확정} |
| 3-ROADMAP | docs/ROADMAP.md | {미시작 / 작성 중 / PM 검수 / 캡틴 검토 / 확정} |
| 4-EXECUTE | tasks/ | {미시작 / T{N}/{M} 진행 중 / 완료} |

## 로드맵 (Phase 3 확정 후)
| # | 태스크 | 스킬 | 상태 |
|---|--------|------|------|

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|
```

세션 복원: 새 세션에서 `.opal/opdp-state.md` 존재 시 Read → 정확한 지점에서 재개.

---

#### N2: PRD 가이드 (references/prd-guide.md)

```markdown
# PRD 작성 가이드

## 작성 전 준비
- docs/PROJECT.md Read → 프로젝트 목적/원칙/기준
- docs/ARCHITECTURE.md Read → 기술 스택/시스템 구성 (있으면)
- .opal/AGENT.md Read → PM 검토 기준

## PRD 구조
1. 개요 (목적, 범위, 대상 사용자)
2. 사용자 정의 (페르소나 — 역할, 목표, 어려움)
3. 기능 요구사항 (유저 스토리 형식 — As a/I want/So that + 수용 기준)
4. 화면 흐름 (주요 시나리오 — 텍스트 또는 다이어그램)
5. 비기능 요구사항 (성능, 보안, 접근성, 호환성)
6. 우선순위 매트릭스 (Must / Should / Could / Won't)
7. 제약 조건 (기술, 일정, 비용)

## PM 검수 체크리스트
- [ ] 모든 기능에 유저 스토리 + 수용 기준이 있는가
- [ ] 우선순위가 명확하고 Must가 과다하지 않은가
- [ ] 비기능 요구사항이 구체적 수치로 명시되었는가
- [ ] 프로젝트 원칙(PROJECT.md)과 부합하는가
- [ ] 기술 실현 가능성이 검토되었는가
```

---

#### N3: TRD 가이드 (references/trd-guide.md)

```markdown
# TRD 작성 가이드

## 작성 전 준비
- docs/PRD.md Read → 기능 요구사항
- docs/ARCHITECTURE.md Read → 기존 아키텍처
- docs/CONVENTIONS.md Read → 코드 컨벤션 (있으면)

## TRD 구조
1. 시스템 아키텍처 상세 (컴포넌트 다이어그램, 데이터 흐름)
2. API 설계 (엔드포인트, HTTP 메서드, 요청/응답 스키마)
3. 데이터 모델 (ERD, 테이블 스키마, 관계)
4. 성능 요구사항 (응답 시간, 동시 접속, 처리량)
5. 보안 요구사항 (인증, 인가, 데이터 보호, OWASP)
6. 외부 연동 (3rd party API, SDK, 인증 방식)
7. 기술적 제약/트레이드오프 (선택 근거)

## PM 검수 체크리스트
- [ ] PRD의 모든 Must/Should 기능이 기술적으로 커버되는가
- [ ] API 설계가 일관적이고 RESTful한가
- [ ] 데이터 모델이 기능 요구사항을 충족하는가
- [ ] 보안 요구사항이 OWASP Top 10을 고려했는가
- [ ] 외부 연동의 인증/에러 처리가 명시되었는가
```

---

#### N4: 로드맵 가이드 (references/roadmap-guide.md)

```markdown
# 로드맵 수립 가이드

## 작성 전 준비
- docs/PRD.md Read → 우선순위 매트릭스
- docs/TRD.md Read → 기술 의존성
- docs/ARCHITECTURE.md Read → 시스템 구조

## 태스크 분할 원칙
1. 독립 실행 가능한 단위로 분할
2. 의존성 방향: 하위 레이어 → 상위 레이어 (DB → API → UI)
3. 각 태스크에 적합한 otp 스킬 판단
4. Must 우선순위부터 배치
5. 하나의 태스크는 1~3일 분량이 적정

## 로드맵 구조 (docs/ROADMAP.md)
1. 개요
2. 태스크 목록 (번호, 제목, 설명, 스킬, 의존성, 우선순위)
3. 실행 순서 (의존성 기반)
4. 마일스톤 (MVP, Beta, Release 등)

## 스킬 판단 기준
| 조건 | 스킬 |
|------|------|
| 코드 변경 10+ 파일, 다중 모듈 | //otpd (Full Task) |
| 코드 변경 <10 파일, 단일 모듈 | //otpds (Short Task) |
| 와이어프레임 + UI 구현 | //otpwf (Wireframe) |

## PM 검수 체크리스트
- [ ] PRD의 모든 Must 기능이 태스크로 분할되었는가
- [ ] 의존성 순서가 올바른가 (하위 먼저)
- [ ] 각 태스크의 스킬 판단이 적절한가
- [ ] 태스크 크기가 적정한가 (너무 크거나 너무 작지 않은가)
- [ ] 마일스톤이 현실적인가
```

---

#### M1: opi SKILL.md 명칭 교체

`skills/opal-project-init/SKILL.md`에서:
- `opal-dev-builder` → `opal-project-dev-pilot`
- `//odp` → `//opdp`
- `> **참고**: opal-dev-builder 스킬은 별도 태스크(034)에서 개발 예정.` 주석 제거
- 폴백 로직 유지: `스킬 미존재 시 otp-dev로 폴백한다.`

#### M2-M3: 레지스트리 등록

**skills.md** — OPAL 전용 스킬 테이블에 추가:

```markdown
| opal-project-dev-pilot | "opal-project-dev-pilot", "opdp" — "프로젝트 개발 시작", "PRD 작성", "개발 계획" | `~/.opal/skills/opal-project-dev-pilot/SKILL.md` |
```

**skill-guide.md** — 스킬 테이블에 추가:

```markdown
| 개발 | opal-project-dev-pilot | //opal-project-dev-pilot / //opdp | PRD/TRD → 로드맵 → 태스크 순차 실행 | `//opdp` | opi 후속 |
```

---

### 의존성 및 환경 변경

- 추가 패키지: 없음
- 환경 변경: 없음
- install-mac.sh: `opal/skills/` 순회 배포로 자동 포함

### 테스트 전략

| 검증 항목 | 방법 |
|----------|------|
| SKILL.md YAML frontmatter 유효성 | 구조 검토 |
| 사전 조건 체크 (PROJECT.md 없을 때) | 시나리오 3 워크스루 |
| Phase 흐름 논리적 정합성 | 수동 워크스루 |
| opi → opdp 연동 흐름 | opi SKILL.md 확인 |
| 레지스트리 일관성 | skills.md ↔ skill-guide.md 교차 확인 |
| PM 검수 흐름 일관성 | AGENT.md 패턴과 대조 |
| 참조 가이드 경로 정합성 | SKILL.md에서 참조하는 경로 확인 |

---

## 3. 실행 체크리스트

- [ ] Step 1: SKILL.md 작성 -- `opal/skills/opal-project-dev-pilot/SKILL.md` -- YAML frontmatter + 사전 조건 체크 + 4 Phase 파이프라인 + PM 검수 흐름 + STATE.md 관리 + 세션 복원
- [ ] Step 2: PRD 가이드 -- `opal/skills/opal-project-dev-pilot/references/prd-guide.md` -- PRD 구조, PM 검수 체크리스트
- [ ] Step 3: TRD 가이드 -- `opal/skills/opal-project-dev-pilot/references/trd-guide.md` -- TRD 구조, PRD 정합성, PM 검수 체크리스트
- [ ] Step 4: 로드맵 가이드 -- `opal/skills/opal-project-dev-pilot/references/roadmap-guide.md` -- 태스크 분할 원칙, 스킬 판단, PM 검수 체크리스트
- [ ] Step 5: opi 연동 수정 -- `skills/opal-project-init/SKILL.md` -- 명칭 교체 (opal-project-dev-pilot / //opdp)
- [ ] Step 6: 레지스트리 등록 -- `opal/core/references/skills.md`, `skill-guide.md` -- opdp 항목 추가

## 4. QA 체크리스트

### 기능 테스트
- [ ] R1: SKILL.md에 YAML frontmatter, 트리거(`opdp`), 약식 명령어가 있는가
- [ ] R1: 사전 조건 체크 — docs/PROJECT.md 미존재 시 opi 안내가 있는가
- [ ] R2: Phase 1에 캡틴 대화 → PRD 초안 → PM 검수 → 캡틴 확정 → docs/PRD.md 흐름이 있는가
- [ ] R3: Phase 2에 PRD 기반 → TRD 초안 → PM 검수 → 캡틴 확정 → docs/TRD.md 흐름이 있는가
- [ ] R4: Phase 3에 태스크 분할 → PM 검수 → 캡틴 확정 → docs/ROADMAP.md 흐름이 있는가
- [ ] R5: Phase 4에 otp 호출 → PM 검수 → 다음 태스크 흐름이 있는가
- [ ] R6: 모든 Phase에서 PM 검수 → 캡틴 확정 순서가 지켜지는가
- [ ] R7: opi SKILL.md에서 opdp 자동 호출이 연동되는가

### 회귀 테스트
- [ ] opi 기존 초기화/최신화 모드 영향 없는가
- [ ] skills.md 기존 항목 유지되는가
- [ ] skill-guide.md 기존 테이블 유지되는가
- [ ] otp-dev, otp-dev-short, otp-wf 영향 없는가

### 코드 품질
- [ ] 한국어 본문 + 영어 기술 용어 컨벤션
- [ ] 파일/폴더 kebab-case
- [ ] 기존 OPAL 스킬과 일관된 구조
- [ ] 참조 가이드가 기존 가이드와 일관된 깊이/형식

## 5. 기술 컨텍스트

| 영역 | 기술 |
|------|------|
| 문서 | Markdown |
| 스킬 프레임워크 | OPAL SKILL.md 포맷 |

## 6. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| PRD/TRD 품질 편차 | 프로젝트 성패 | 참조 가이드 체크리스트로 일관성 확보 + PM 검수 강제 |
| 태스크 폭발 (많은 태스크) | 컨텍스트 한계 | STATE.md + ROADMAP.md 기반 세션 복원 |
| opi 미완료 상태에서 opdp 호출 | 컨텍스트 부족 | 사전 조건 체크 → opi 먼저 안내 |
| PM 자체 검수 객관성 한계 | 품질 저하 | 가이드 체크리스트 1:1 대조 형식 검수 + 캡틴 최종 확정 |
