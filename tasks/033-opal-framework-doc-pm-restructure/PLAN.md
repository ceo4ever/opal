# PLAN: OPAL 프레임워크 문서 구조 + PM 역할 재설계

> 작성일: 2026-03-27
> 입력: TASK.md
> 출력: PLAN.md

## 1. 코드 분석

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `opal/core/AGENT.md` | 글로벌 에이전트 정의 (부트스트랩 절차) | ✅ R5, R8 |
| `skills/opal-project-init/SKILL.md` | opi 스킬 정의 (~6000줄) | ✅ R7 (전면 재설계) |
| `skills/opal-project-init/templates/common/opal/AGENT.md` | 프로젝트 PM 프로필 템플릿 | ✅ R4 (삭제 → 작성 가이드로 대체) |
| `skills/opal-project-init/templates/common/platform/CLAUDE.md` | CLAUDE.md 템플릿 | ✅ R1 (경량화) |
| `skills/opal-project-init/templates/common/platform/GEMINI.md` | GEMINI.md 템플릿 | ✅ R1 (경량화) |
| `skills/opal-project-init/templates/common/platform/.cursorrules` | .cursorrules 템플릿 | ✅ R1 (경량화) |
| `skills/opal-project-init/templates/common/docs/*` | docs 템플릿 (INDEX.md, server/*, client/*) | ✅ (삭제 → 작성 가이드로 대체) |
| `skills/opal-project-init/templates/web/` | web 프로젝트 추가 템플릿 | ✅ (삭제) |
| `skills/opal-project-init/templates/ai-agent/` | ai-agent 프로젝트 추가 템플릿 | ✅ (삭제) |
| `skills/opal-project-init/templates/optional/` | 조건부 템플릿 (SQLITE, CHAT) | ✅ (삭제) |
| `skills/opal-project-init/scripts/apply.js` | 템플릿 적용 스크립트 | ✅ R7 (역할 축소) |
| `skills/otp-dev/SKILL.md` | Full Task 오케스트레이터 | ✅ R6 |
| `skills/otp-dev-short/SKILL.md` | Short Task 오케스트레이터 | ✅ R6 |

### 현재 구현

**글로벌 AGENT.md (opal/core/AGENT.md)**:
- 부트스트랩 7단계: identity.md 로드 → 레지스트리 Read → 부트스트래퍼 삽입 → 메모리 브리핑 → 스킬 가이드 브리핑
- `{프로젝트}/.opal/AGENT.md` 존재 여부만 확인 → 내용 로드 없음
- PM 학습 루프 없음

**opi 스킬 (opal-project-init/SKILL.md)**:
- 고정 인터뷰 5개 질문 → 플레이스홀더 매핑 → apply.js로 템플릿 치환
- 일반 프로젝트: .opal/만 생성 (docs/ 미생성)
- 개발 프로젝트: docs/server/* 6개 + docs/client/* 6개 + platform/ 3개 + .opal/ 2개
- 기존 모드: 파일 있으면 건너뛰기 (업데이트 불가)

**플랫폼 템플릿 (CLAUDE.md/GEMINI.md/.cursorrules)**:
- OPAL 부트스트래퍼 + 프로젝트 정보 + 기술 스택 + docs/ 참조 + 코드 컨벤션 + 개발 환경 (~50줄)
- 3개 파일이 거의 동일한 내용 중복

**otp 오케스트레이터 (otp-dev, otp-dev-short)**:
- 워커에게 `CLAUDE.md`를 프로젝트 컨벤션으로 전달
- PM 검토 게이트 없음

### 영향 범위

- **부트스트랩 절차**: 글로벌 AGENT.md 변경 → 모든 프로젝트 세션 시작 행동 변경
- **opi 스킬 변경**: 새 프로젝트 초기화 구조 변경 (기존 프로젝트는 수동 마이그레이션)
- **otp 파이프라인**: PM 검토 게이트 추가 + 디스패치 프롬프트에서 docs/ 참조로 전환
- **install-mac.sh**: opal/core/AGENT.md → ~/.opal/AGENT.md 재배포 필요

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| N1 | `skills/opal-project-init/references/docs-guide.md` | docs 문서 작성 가이드 — 알투가 문서 작성 시 참조하는 구조/내용 지침 |
| N2 | `skills/opal-project-init/references/agent-guide.md` | AGENT.md 작성 가이드 — PM 전문 역할, 검토 기준, 업무 지침 작성 지침 |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| M1 | `templates/common/platform/CLAUDE.md` | 경량화: 부트스트래퍼만 (R1) |
| M2 | `templates/common/platform/GEMINI.md` | 경량화: 부트스트래퍼만 (R1) |
| M3 | `templates/common/platform/.cursorrules` | 경량화: 부트스트래퍼만 (R1) |
| M4 | `templates/common/opal/AGENT.md` | 삭제 — 작성 가이드(N2)로 대체 (R4) |
| M5 | `opal/core/AGENT.md` | PM 컨텍스트 로드 + PM 학습 루프 추가 (R5, R8) |
| M6 | `skills/otp-dev/SKILL.md` | PM 검토 게이트 + 디스패치 변경 (R6) |
| M7 | `skills/otp-dev-short/SKILL.md` | PM 검토 게이트 + 디스패치 변경 (R6) |
| M8 | `skills/opal-project-init/SKILL.md` | 전면 재설계 (R7) |
| M9 | `skills/opal-project-init/scripts/apply.js` | 역할 축소: PLATFORM_FILES만 (R7) |

#### 삭제

| # | 파일/디렉토리 | 이유 |
|---|-------------|------|
| D1 | `templates/common/docs/*` | 알투 직접 작성으로 전환 |
| D2 | `templates/common/opal/AGENT.md` | 알투 직접 작성으로 전환 |
| D3 | `templates/common/opal/MEMORY.md` | 알투 직접 작성으로 전환 |
| D4 | `templates/web/` | 알투 직접 작성으로 전환 |
| D5 | `templates/ai-agent/` | 알투 직접 작성으로 전환 |
| D6 | `templates/optional/` | 알투 직접 작성으로 전환 |

### 구현 순서

| 순서 | 작업 | 파일 | 난이도 |
|------|------|------|--------|
| 1 | 플랫폼 템플릿 경량화 | M1, M2, M3 | 쉬움 |
| 2 | apply.js 역할 축소 | M9 | 보통 |
| 3 | 기존 템플릿 삭제 | D1~D6 | 쉬움 |
| 4 | docs 작성 가이드 생성 | N1 | 보통 |
| 5 | AGENT.md 작성 가이드 생성 | N2 | 보통 |
| 6 | opi SKILL.md 전면 재설계 | M8 | 어려움 |
| 7 | 글로벌 AGENT.md 변경 | M5 | 보통 |
| 8 | otp-dev PM 검토 게이트 + 디스패치 변경 | M6 | 보통 |
| 9 | otp-dev-short PM 검토 게이트 + 디스패치 변경 | M7 | 보통 |

---

### 핵심 설계

#### 설계 원칙: 프로젝트 = WHAT/WHY, 스킬 = HOW

opi는 프로젝트의 WHAT(무엇을)과 WHY(왜)를 정의하고, 그 위에서 다양한 스킬(otp-dev, otp-doc 등)이 HOW를 수행한다. opi가 만든 프로젝트 환경(docs/, .opal/)은 모든 스킬의 컨텍스트가 된다.

---

#### N1: docs 작성 가이드 (references/docs-guide.md)

알투가 문서를 직접 작성할 때 참조하는 구조 지침. 템플릿이 아닌 가이드.

**docs/PROJECT.md — 프로젝트 정의 (모든 프로젝트 필수)**

```markdown
# {프로젝트명}

> {한 줄 설명}

## 프로젝트 개요

| 항목 | 값 |
|------|-----|
| 프로젝트명 | |
| 도메인 | |
| 현재 Phase | |

## 프로젝트 원칙

{핵심 원칙 — 캡틴과 대화에서 도출}

## 프로젝트 기준

{품질, 우선순위, 의사결정 기준}

## 기술 스택 (개발 프로젝트만)

| 레이어 | 기술 |
|--------|------|

## 프로젝트 문서

| 문서 | 설명 | 용도 | 참조 시점 |
|------|------|------|----------|
| `.opal/AGENT.md` | PM 프로필 | PM 역할 및 검토 기준 | 부트스트랩 시 자동 |
```

- **프로젝트 문서 테이블**: 프로젝트 허브. 모든 문서의 레지스트리.
- **문서 등록 프로토콜**: 새 문서 생성 시 캡틴에게 용도 인터뷰 → 승인 시 테이블에 등록.
  등록되지 않은 문서는 다른 스킬이 참조하지 않음.

**docs/ARCHITECTURE.md — 아키텍처 (개발 프로젝트)**

```
- 시스템 구성 (서버, 클라이언트, DB, 외부 서비스 관계)
- 기술 스택 상세 (버전, 선택 이유)
- 개발 환경 (포트, URL, 설정)
- 디렉토리 구조
```

**docs/CONVENTIONS.md — 코드 컨벤션 (개발 프로젝트)**

```
- 네이밍 규칙 (변수, 함수, 파일, 디렉토리)
- 파일 구조 (디렉토리 레이아웃)
- 브랜치 전략
- 커밋 규칙
```

**docs/BACKEND.md — 서버 가이드 (BE 있을 때)**

```
- 서버 구조 (레이어, 디렉토리)
- 환경 설정 (환경 변수)
- 도메인 패턴 (Controller-Service-Repository 등)
- 새 기능 추가 가이드
- 패키지 관리
```

**docs/FRONTEND.md — 클라이언트 가이드 (FE 있을 때)**

```
- 클라이언트 구조 (라우팅, 디렉토리)
- 아키텍처 원칙 (상태 관리, 컴포넌트 분리)
- 환경 설정
- API 연동
- 트러블슈팅
```

**문서는 모두 알투가 프로젝트 분석 후 직접 작성한다. 플레이스홀더 치환이 아님.**

---

#### N2: AGENT.md 작성 가이드 (references/agent-guide.md)

```markdown
# {프로젝트명} PM 프로필

> 프로젝트: {프로젝트명} | 생성일: YYYY-MM-DD

이 파일은 알투의 PM 역할을 정의한다. 프로젝트 정보는 docs/PROJECT.md를 참조한다.

## PM 전문 역할

{이 프로젝트에서 어떤 전문가 관점으로 검토하는가}
예: "AI 프레임워크 설계 전문가 — 재사용성, 플랫폼 독립성 관점"
예: "이커머스 도메인 전문가 — 결제 안전성, 재고 정합성 관점"

## PM 검토 기준

### 필수 검토
- [ ] TASK.md 요구사항과 결과물 일치
- [ ] 프로젝트 컨벤션 준수 (docs/CONVENTIONS.md)
- [ ] 금지사항 위반 여부
- [ ] 관련 참조 문서가 워커에게 전달되었는가

### 도메인 검토
- [ ] {PM 전문 역할에서 도출된 검토 항목}

## 업무 수행 지침

### 참조 문서 전달 의무
작업 지시 시 docs/PROJECT.md의 "프로젝트 문서" 테이블을 확인하고,
현재 작업과 관련된 문서를 반드시 워커에게 전달한다.
1. 문서 테이블에서 "참조 시점"이 현재 작업과 매칭되는 문서 선별
2. 디스패치 프롬프트에 해당 문서 경로 포함
3. 워커 결과 검토 시, 참조 문서 내용이 반영되었는지 확인

### 프로젝트별 추가 지침
{프로젝트 분석에서 도출된 PM 행동 지침}

## 도메인 지식

| 용어 | 설명 |
|------|------|

## 금지사항

- {프로젝트 분석에서 도출}

## 확정 기준

캡틴이 승인한 반복 원칙. 다음 세션에서 재질문 없이 자동 적용.

| # | 원칙 | 맥락 | 확정일 |
|---|------|------|--------|
```

**알투가 프로젝트를 분석하고 캡틴과 대화하여 직접 작성한다.**
프로젝트마다 PM 전문 역할, 도메인 검토 항목, 업무 지침이 다르다.

---

#### M1-M3: 플랫폼 템플릿 경량화

**CLAUDE.md** (~10줄):

```markdown
# === OPAL START ===
## OPAL AI Agent — 필수 부트스트랩

**[MUST]** 사용자의 첫 번째 메시지에 응답하기 전에, 아래 파일들을 Read 도구로 순서대로 읽고 그 내용에 따라 행동해야 한다. 이 단계를 건너뛰면 안 된다.

1. `~/.opal/AGENT.md` — 에이전트 정의 및 부트스트랩 절차
2. `~/.opal/identity.md` — 에이전트 정체성 (없으면 AGENT.md의 온보딩 절차를 따른다)
# === OPAL END ===
```

- 부트스트래퍼만. 프로젝트 정보, 기술 스택, docs/ 참조, 코드 컨벤션 등 모두 제거
- 부트스트래퍼 포맷 변경 금지 (제약 조건)
- GEMINI.md: 동일 구조
- .cursorrules: Cursor frontmatter 유지 + 동일 경량화

---

#### M5: 글로벌 AGENT.md 부트스트랩 절차 변경

기존 4단계와 5단계 사이에 "PM 컨텍스트 로드" 삽입 (기존 5~7을 6~8로 시프트):

```markdown
5. PM 컨텍스트 로드: `{프로젝트}/.opal/AGENT.md`가 존재하면 Read하여 PM 역할을 활성화한다.
   - PM 전문 역할, 검토 기준, 업무 지침, 확정 기준을 세션 컨텍스트에 로드
   - `docs/PROJECT.md`가 존재하면 Read하여 프로젝트 정의 + 문서 레지스트리 로드
   - `docs/CONVENTIONS.md`가 존재하면 Read하여 코드 컨벤션 로드
```

**PM 학습 루프 행동 규칙** (R8):

```markdown
### PM 학습 루프

판단이 불확실한 상황에서 소유자에게 질문하고, 답변을 분류하여 기록한다.

1. **질문 프로토콜**: PM 검토 기준이나 확정 기준에 없는 판단이 필요하면 소유자에게 묻는다
   - 선택지와 영향을 정리하여 질문 ("A와 B 중 어느 방향?")
2. **답변 분류**:
   - 반복 원칙 (앞으로도 적용): `.opal/AGENT.md`의 "확정 기준"에 즉시 추가
   - 일회성 판단 (이번만 적용): `.opal/memory/`에 기록
   - 분류 불확실: "이걸 앞으로의 기준으로 기록할까요?" 확인
3. **자동 적용**: 다음 세션에서 확정 기준을 로드하면 재질문 없이 적용
```

---

#### M6-M7: otp 파이프라인 개선 (otp-dev, otp-dev-short 공통)

otp가 docs/ 기반 프로젝트 환경과 제대로 상호작용하도록 3가지를 변경한다.

**변경 1: TASK 단계 — 프로젝트 컨텍스트 반영**

오케스트레이터가 TASK.md를 직접 작성하는 단계에서, 프로젝트 환경을 참조한다.

```
기존:
  사용자 요청만으로 TASK.md 작성

변경:
  1. docs/PROJECT.md Read — 프로젝트 원칙/기준 확인
  2. .opal/AGENT.md Read — PM 검토 기준/금지사항 확인
  3. TASK.md 작성 시 프로젝트 원칙에 부합하는지 검토
     예: "소상공인이 5분 안에 사용" 원칙 → TASK에 UX 제약 반영
```

**변경 2: 디스패치 프롬프트 — docs/ 참조로 전환**

```
기존:
  **프로젝트 컨벤션**: {CLAUDE.md 경로}

변경:
  **프로젝트 문서**:
  - `docs/PROJECT.md` (필수)
  - `docs/CONVENTIONS.md` (있으면)
  - {PROJECT.md 문서 테이블에서 "참조 시점"이 현재 작업과 매칭되는 문서}

  **docs/ 미존재 시**: CLAUDE.md 폴백 (하위 호환)
```

알투(PM)가 PROJECT.md의 문서 테이블을 읽고 현재 작업에 관련된 문서를 선별.
예:
- "로그인 기능 개발" → PRD.md(항상) + ARCHITECTURE.md + BACKEND.md
- "화면 디자인 변경" → PRD.md(항상) + FRONTEND.md

**변경 3: PM 검토 게이트 — 워커 완료 후 삽입**

```
워커 완료 → QA 워커 호출 → PM 검토 → 사용자 보고
```

검토 절차:
1. 관련 참조 문서가 워커에게 전달되었는가
2. PM 검토 기준 체크리스트 평가 (.opal/AGENT.md)
3. TASK.md 요구사항과 산출물 정합성
4. 참조 문서 내용이 산출물에 반영되었는가
5. 프로젝트 원칙/기준에 부합하는가 (docs/PROJECT.md)
6. 금지사항 위반 여부

판정:
- **Pass**: 사용자에게 보고
- **Fail**: 워커에게 재지시 (최대 1회) → 재검토 → 보고
  - 재지시 시: "PM 검토 결과: {미달 항목} → {수정 방향}"
- **.opal/AGENT.md 미존재 시**: 게이트 스킵 (하위 호환)

**변경 4: 완료 시 문서 등록 확인**

EXECUTE 완료 후, 새 문서가 생성된 경우 (docs/ 하위):
1. 캡틴에게 확인: "새 문서가 생성되었습니다. 프로젝트 문서로 등록할까요?"
2. 캡틴 승인 시 → PROJECT.md 문서 테이블에 등록 (용도 인터뷰)
3. otp-doc 등 문서 전용 스킬에서도 동일 프로토콜 적용

---

#### M8: opi SKILL.md 전면 재설계

기존 "고정 인터뷰 → 플레이스홀더 치환"을 **"분석 → 작성 → 검토"**로 전환.

**초기화 모드 (.opal/AGENT.md 미존재)**:

```
Phase 1: 프로젝트 이해
  1. 프로젝트 소스 분석
     - 코드: package.json, pyproject.toml, go.mod 등
     - 기존 문서: README.md, CLAUDE.md 등
     - 디렉토리 구조: src/, app/, server/, client/ 등
  2. 캡틴과 대화 (자연스러운 탐색)
     - 프로젝트가 무엇인지, 어떤 도메인인지
     - 현재 어느 단계인지
     - PM으로서 어떤 전문가 관점이 필요한지
     - 캡틴이 요청한 추가 문서가 있는지 (PRD 등)
  3. 프로젝트 카테고리 판별: 일반 / 개발

Phase 2: 공통 문서 작성 + 검토
  1. docs/PROJECT.md 초안 작성 (개요, 원칙, 기준, 문서 테이블)
  2. .opal/AGENT.md 초안 작성 (PM 전문 역할, 검토 기준, 업무 지침)
  3. .opal/MEMORY.md 생성 (빈 인덱스)
  4. 캡틴이 요청한 문서가 있으면 작성 (PRD 등)
     → 용도 인터뷰 → PROJECT.md 문서 테이블에 등록
  5. 캡틴에게 초안 제시 → 피드백 → 반영

Phase 3: 개발 문서 (개발 프로젝트만)
  1. 추가 분석 (기술 스택 상세, 아키텍처, 코드 구조)
  2. 필요 시 캡틴에게 추가 질문 (기술적 결정사항)
  3. docs-guide.md (N1) 참조하여 문서 작성:
     - docs/ARCHITECTURE.md (아키텍처, 기술 스택, 개발 환경)
     - docs/CONVENTIONS.md (코드 컨벤션)
     - docs/BACKEND.md (BE 있을 때)
     - docs/FRONTEND.md (FE 있을 때)
  4. 각 문서를 PROJECT.md 문서 테이블에 등록
  5. 캡틴에게 초안 제시 → 피드백 → 반영

Phase 4: 플랫폼 파일 생성 + 완료
  1. apply.js로 CLAUDE.md, GEMINI.md, .cursorrules 생성 (부트스트래퍼만)
  2. 완료 보고
```

**최신화 모드 (.opal/AGENT.md 존재)**:

```
Phase 1: 현재 상태 분석
  1. 기존 .opal/AGENT.md Read
  2. 기존 docs/ 전체 Read
  3. PROJECT.md의 문서 테이블 확인 — 등록된 문서 목록 파악

Phase 2: 프로젝트 유형별 분석

  [개발 프로젝트]
  1. 현재 코드베이스 분석
  2. 변경점 감지: 기술 스택 변경, 새 모듈 추가, Phase 진행 등
  3. 개발 문서 내용과 실제 코드 비교

  [일반/문서 프로젝트]
  1. docs/ 하위 문서 전체 스캔
  2. 문서 정리 상태 점검:
     - 문서 테이블에 미등록 문서가 있는가
     - 등록된 문서 중 삭제/이동된 것이 있는가
     - 설명/용도가 비어있거나 오래된 것이 있는가

Phase 3: 변경 사항 정리 + 검토
  1. 캡틴에게 보고:
     [개발] "기술 스택 변경됨", "새 API 추가됨" 등
     [일반] "미등록 문서 3개 발견", "삭제된 문서 1개" 등
  2. 갱신/등록할 문서와 내용 제안
  3. 미등록 문서 → 캡틴에게 용도 인터뷰 → 등록 여부 결정
  4. 캡틴 승인 → 해당 문서만 업데이트

Phase 4: 플랫폼 파일 갱신 (필요 시)
  1. 부트스트래퍼 최신 여부 확인 → 필요 시 갱신
```

---

#### M9: apply.js 역할 축소

```javascript
// 플랫폼 파일만 처리
const PLATFORM_FILES = [
  { src: "platform/CLAUDE.md", dest: "CLAUDE.md" },
  { src: "platform/GEMINI.md", dest: "GEMINI.md" },
  { src: "platform/.cursorrules", dest: ".cursorrules" },
];
```

- 기존 COMMON_DOCS (server/*, client/*), OPAL_FILES 제거 → 알투가 직접 작성
- PLATFORM_FILES만 유지 (부트스트래퍼 삽입은 정형 작업)
- 기존 CLAUDE.md 병합 로직(OPAL 마커 기반)은 유지

---

### 의존성 및 환경 변경

- 추가 패키지: 없음
- 환경 변경: 없음
- install-mac.sh: opal/core/AGENT.md → ~/.opal/AGENT.md 재배포 필요

### 테스트 전략

1. **apply.js**: 경량화된 PLATFORM_FILES만 정상 생성되는지 확인
2. **OPAL 마커 병합**: 기존 CLAUDE.md에 OPAL 마커가 있을 때 병합이 깨지지 않는지 확인
3. **수동 리뷰**: 각 산출물 문서의 구조와 내용 일관성 확인
4. **시나리오 검증**: opi 초기화 모드 / 최신화 모드 시뮬레이션

---

## 3. 실행 체크리스트

- [ ] Step 1: 플랫폼 템플릿 경량화 -- `templates/common/platform/CLAUDE.md`, `GEMINI.md`, `.cursorrules` -- 부트스트래퍼만 남기기
- [ ] Step 2: apply.js 역할 축소 -- `scripts/apply.js` -- PLATFORM_FILES만 유지
- [ ] Step 3: 기존 템플릿 삭제 -- `templates/common/docs/`, `templates/common/opal/`, `templates/web/`, `templates/ai-agent/`, `templates/optional/` -- 알투 직접 작성으로 전환
- [ ] Step 4: docs 작성 가이드 생성 -- `references/docs-guide.md` -- PROJECT.md, ARCHITECTURE.md, CONVENTIONS.md, BACKEND.md, FRONTEND.md 구조 지침
- [ ] Step 5: AGENT.md 작성 가이드 생성 -- `references/agent-guide.md` -- PM 전문 역할, 검토 기준, 업무 지침, 확정 기준 구조 지침
- [ ] Step 6: opi SKILL.md 전면 재설계 -- `SKILL.md` -- 초기화/최신화 모드, 분석→작성→검토 프로세스, 문서 등록 프로토콜
- [ ] Step 7: 글로벌 AGENT.md 변경 -- `opal/core/AGENT.md` -- PM 컨텍스트 로드 절차 + PM 학습 루프 규칙
- [ ] Step 8: otp-dev 변경 -- `skills/otp-dev/SKILL.md` -- 디스패치 docs/ 참조 + PM 검토 게이트
- [ ] Step 9: otp-dev-short 변경 -- `skills/otp-dev-short/SKILL.md` -- 디스패치 docs/ 참조 + PM 검토 게이트

## 4. QA 체크리스트

### 기능 테스트
- [ ] R1: 플랫폼 템플릿이 OPAL 부트스트래퍼만 포함하는가
- [ ] R2: docs-guide.md에 PROJECT.md 구조 (개요, 원칙, 기준, 문서 테이블) 지침이 있는가
- [ ] R3: docs-guide.md에 ARCHITECTURE/CONVENTIONS/BACKEND/FRONTEND 구조 지침이 있는가
- [ ] R4: agent-guide.md에 PM 전문 역할, 검토 기준, 업무 지침(참조 문서 전달 의무), 확정 기준이 있는가
- [ ] R5: 글로벌 AGENT.md에 PM 컨텍스트 로드 절차 (AGENT.md + PROJECT.md + CONVENTIONS.md Read)가 있는가
- [ ] R6: otp-dev, otp-dev-short에 디스패치 docs/ 참조 + PM 검토 게이트가 있는가
- [ ] R7: opi SKILL.md에 초기화/최신화 모드가 있는가
- [ ] R7: opi 초기화 모드에 분석→대화→작성→검토 프로세스가 있는가
- [ ] R7: opi 최신화 모드에 개발/일반 프로젝트별 분석이 있는가
- [ ] R7: 문서 등록 프로토콜 (용도 인터뷰 → PROJECT.md 테이블 등록)이 있는가
- [ ] R8: 글로벌 AGENT.md에 PM 학습 루프 규칙이 있는가
- [ ] R8: agent-guide.md에 확정 기준 섹션이 있는가

### 회귀 테스트
- [ ] OPAL 부트스트래퍼 포맷 변경되지 않았는가
- [ ] .opal/MEMORY.md 구조 유지되는가
- [ ] otp 기본 흐름(TASK→PLAN→TEST-SCENARIO→EXECUTE) 유지되는가
- [ ] 스킬 자체 페르소나(dtp-*/personas/) 변경되지 않았는가
- [ ] apply.js PLATFORM_FILES 정상 동작하는가
- [ ] 기존 CLAUDE.md 병합 로직(OPAL 마커) 정상인가
- [ ] .opal/AGENT.md 미존재 시 PM 검토 게이트 스킵되는가 (하위 호환)
- [ ] docs/ 미존재 시 CLAUDE.md 폴백되는가 (하위 호환)

### 코드 품질
- [ ] 한국어 본문 + 영어 기술 용어 컨벤션
- [ ] 파일/폴더 명명 kebab-case
- [ ] apply.js 변경이 기존 호출 인터페이스와 하위 호환되는가

## 5. 기술 컨텍스트

### 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 문서 | Markdown | - |
| 스크립트 | JavaScript (Node.js) | - |
| 배포 | Shell (bash) | - |

### 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| - | 마크다운 문서 작업이므로 MCP 조회 불필요 |

## 6. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| 기존 프로젝트의 CLAUDE.md가 무거운 상태 유지 | 기존 사용자는 수동 마이그레이션 필요 | 별도 마이그레이션 태스크로 분리 |
| PM 검토 게이트가 파이프라인 속도를 늦출 수 있음 | 각 단계마다 추가 검토 시간 | 오케스트레이터 인라인 수행 (워커 디스패치 없음). AGENT.md 미존재 시 스킵 |
| PM 학습 루프의 원칙/일회성 분류가 모호할 수 있음 | 잘못 분류된 원칙이 확정 기준에 누적 | 분류 불확실 시 캡틴에게 확인. 확정 기준은 수동 삭제 가능 |
| 알투 직접 작성 품질이 템플릿보다 일관성이 낮을 수 있음 | 프로젝트마다 문서 구조가 달라질 수 있음 | docs-guide.md, agent-guide.md 작성 가이드로 구조 일관성 보장 |
| opi 최신화 시 기존 문서 손상 가능 | 캡틴이 수정한 내용이 덮어써질 수 있음 | 변경 제안 → 캡틴 승인 후에만 업데이트 (자동 덮어쓰기 금지) |
