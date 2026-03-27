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

# opal-project-dev-pilot

개발 프로젝트의 전체 라이프사이클을 4 Phase 파이프라인으로 관리하는 스킬.
PRD → TRD → 로드맵 → 태스크 순차 실행까지, PM 검수와 캡틴 확정을 거치며 체계적으로 진행한다.

## 설계 원칙

- **PM이 직접 작성한다**: 모든 산출물(PRD, TRD, ROADMAP)은 알투가 PM으로서 직접 작성한다. 플레이스홀더 치환이 아니다.
- **PM 검수 → 캡틴 확정**: 초안 작성 → PM 자체 검수(가이드 체크리스트 1:1 대조) → 미달 시 재작성(최대 1회) → 통과 → 캡틴 검토 요청. 캡틴은 PM이 통과시킨 결과물만 검토한다.
- **세션 독립**: STATE.md 기반으로 어느 세션에서든 정확한 지점에서 재개한다.
- **참조 가이드 필수 Read**: 각 Phase 시작 전 해당 가이드를 반드시 Read한다.

---

## 사전 조건 체크

`//opdp` 호출 시 프로젝트 루트의 `docs/PROJECT.md` 존재 여부를 확인한다.

| 조건 | 동작 |
|------|------|
| `docs/PROJECT.md` 존재 | Phase 1 시작 |
| `docs/PROJECT.md` 미존재 | opi 자동 실행 → 완료 후 opdp 복귀 |

**opi 자동 실행 시**:

1. 캡틴의 원래 요청을 보존한다.
2. `~/.opal/skills/opal-project-init/SKILL.md`를 Read하여 opi를 실행한다.
3. opi 완료 즉시, 보존한 원래 요청으로 opdp Phase 1을 시작한다.

---

## 태스크 생성

사전 조건 체크 통과 후, opdp 전용 태스크 폴더를 생성한다.

```
tasks/{NNN}-opdp-{프로젝트명}/
├── TASK.md       ← 전체 그림 (목표, 참조 문서, 절차)
├── STATE.md      ← 진행 상황 추적
└── DONE.md       ← 완료 시 랩업
```

`{NNN}`: 기존 `tasks/` 폴더의 최대 번호 + 1로 자동 채번.

### TASK.md 작성

```markdown
# TASK: {프로젝트명} 개발 파일럿

> 작성일: YYYY-MM-DD | 스킬: //opdp

## 목표

{캡틴의 원래 요청}

## 참조 문서

| 문서 | 용도 | 읽는 시점 |
|------|------|----------|
| docs/PROJECT.md | 프로젝트 정의, 원칙 | 전체 |
| docs/ARCHITECTURE.md | 기술 스택 | Phase 1~3 |
| docs/CONVENTIONS.md | 코드 컨벤션 | Phase 4 |
| .opal/AGENT.md | PM 검토 기준 | 전체 |

## 절차

| Phase | 산출물 | 설명 |
|-------|--------|------|
| 1 | docs/PRD.md | 제품 요구사항 정의 |
| 2 | docs/TRD.md | 기술 요구사항 정의 |
| 3 | docs/ROADMAP.md | 태스크 분할 + 로드맵 |
| 4 | tasks/{N}~{M} | 태스크 순차 실행 |
```

### STATE.md 초기 생성

아래 "STATE.md 관리" 섹션의 템플릿으로 생성한다.

---

## 세션 복원

새 세션에서 `//opdp` 호출 시:

1. `tasks/` 하위에 `*-opdp-*` 패턴의 폴더가 있는지 확인한다.
2. **존재하면**: STATE.md Read → 현재 Phase와 상태를 파악 → 정확한 지점에서 재개.
3. **미존재**: 사전 조건 체크부터 시작한다.

---

## 파이프라인

```
사전 조건 체크 → 태스크 생성 (TASK.md + STATE.md)
  → Phase 1: PRD 작성 → PM 검수 → 캡틴 확정 → docs/PRD.md
  → Phase 2: TRD 작성 → PM 검수 → 캡틴 확정 → docs/TRD.md
  → Phase 3: 로드맵 수립 → PM 검수 → 캡틴 확정 → docs/ROADMAP.md
  → Phase 4: 태스크 순차 실행 → 각 태스크 PM 검수 → 전체 완료
  → DONE.md 작성
```

---

## Phase 1: PRD 작성

제품 요구사항 정의서를 작성한다.

### 1-1. 사전 준비

다음 파일을 반드시 Read한다:

- `~/.opal/skills/opal-project-dev-pilot/references/prd-guide.md` — PRD 구조 및 체크리스트
- `docs/PROJECT.md` — 프로젝트 목적/원칙/기준
- `docs/ARCHITECTURE.md` — 기술 스택/시스템 구성 (있으면)
- `.opal/AGENT.md` — PM 검토 기준

### 1-2. PRD 초안 작성

캡틴 대화와 프로젝트 분석을 기반으로 PRD 초안을 작성한다.

- prd-guide.md의 구조를 따른다
- 기능 요구사항은 유저 스토리 형식(As a / I want / So that + 수용 기준)으로 작성한다
- 우선순위 매트릭스(Must / Should / Could / Won't)를 명확히 분류한다

### 1-3. PM 검수

알투가 PM으로서 자체 검수한다:

1. prd-guide.md의 PM 검수 체크리스트를 1:1 대조한다
2. `.opal/AGENT.md`의 검토 기준을 적용한다
3. `docs/PROJECT.md`와의 정합성을 확인한다
4. **미달 시**: 자체 재작성한다 (최대 1회)
5. **통과 시**: 캡틴 검토 요청으로 넘어간다

### 1-4. 캡틴 확정

```
---
[PRD] PM 검수 통과 — 캡틴 검토 요청

산출물: docs/PRD.md (초안)

{PRD 핵심 요약: 기능 수, Must 항목 수, 주요 사용자 등}

검토 후 확정 / 피드백을 알려주세요.
---
```

| 캡틴 응답 | 동작 |
|----------|------|
| 확정 / 승인 | 아래 후속 조치 수행 후 Phase 2 진행 |
| 피드백 | 피드백 반영 → PM 재검수 → 캡틴 재검토 |

### 1-5. 캡틴 확정 후 후속 조치 (필수)

**다음 Phase로 넘어가기 전에 반드시 수행한다. 아래 세 가지가 완료되어야만 다음 Phase로 진행할 수 있다.**

1. `docs/PROJECT.md`의 문서 테이블에 PRD.md를 등록한다 (설명, 용도, 참조 시점 포함)
2. `STATE.md`를 갱신한다 (1-PRD → 확정)
3. `.opal/MEMORY.md`의 작업 히스토리를 갱신한다 (`Phase 1(PRD) ✅ → Phase 2 대기`)

---

## Phase 2: TRD 작성

기술 요구사항 정의서를 작성한다.

### 2-1. 사전 준비

다음 파일을 반드시 Read한다:

- `~/.opal/skills/opal-project-dev-pilot/references/trd-guide.md` — TRD 구조 및 체크리스트
- `docs/PRD.md` — Phase 1에서 확정한 기능 요구사항
- `docs/ARCHITECTURE.md` — 기존 아키텍처 (있으면)
- `docs/CONVENTIONS.md` — 코드 컨벤션 (있으면)

### 2-2. TRD 초안 작성

PRD를 기반으로 기술 설계를 작성한다.

- trd-guide.md의 구조를 따른다
- PRD의 모든 Must/Should 기능이 기술적으로 커버되어야 한다
- API 설계, 데이터 모델, 보안 요구사항을 구체적으로 명시한다

### 2-3. PM 검수

1. trd-guide.md의 PM 검수 체크리스트를 1:1 대조한다
2. PRD 정합성을 확인한다 (모든 Must/Should 기능이 커버되는가)
3. 기술 실현 가능성을 검토한다
4. **미달 시**: 자체 재작성 (최대 1회)
5. **통과 시**: 캡틴 검토 요청

### 2-4. 캡틴 확정

```
---
[TRD] PM 검수 통과 — 캡틴 검토 요청

산출물: docs/TRD.md (초안)

{TRD 핵심 요약: 아키텍처 구성, API 수, 데이터 모델 수, 주요 기술 결정 등}

검토 후 확정 / 피드백을 알려주세요.
---
```

| 캡틴 응답 | 동작 |
|----------|------|
| 확정 / 승인 | 아래 후속 조치 수행 후 Phase 3 진행 |
| 피드백 | 피드백 반영 → PM 재검수 → 캡틴 재검토 |

### 2-5. 캡틴 확정 후 후속 조치 (필수)

**다음 Phase로 넘어가기 전에 반드시 수행한다. 아래 네 가지가 완료되어야만 다음 Phase로 진행할 수 있다.**

1. `docs/ARCHITECTURE.md`를 업데이트한다 (TRD에서 확정된 기술 스택 버전 반영)
2. `docs/PROJECT.md`의 문서 테이블에 TRD.md를 등록한다 (설명, 용도, 참조 시점 포함)
3. `STATE.md`를 갱신한다 (2-TRD → 확정)
4. `.opal/MEMORY.md`의 작업 히스토리를 갱신한다 (`Phase 2(TRD) ✅ → Phase 3 대기`)

---

## Phase 3: 로드맵 수립

태스크를 분할하고 실행 순서를 결정한다.

### 3-1. 사전 준비

다음 파일을 반드시 Read한다:

- `~/.opal/skills/opal-project-dev-pilot/references/roadmap-guide.md` — 로드맵 구조 및 체크리스트
- `docs/PRD.md` — 우선순위 매트릭스
- `docs/TRD.md` — 기술 의존성
- `docs/ARCHITECTURE.md` — 시스템 구조 (있으면)

### 3-2. 태스크 분할

PRD/TRD를 기반으로 태스크를 분할한다.

**분할 원칙**:
1. 독립 실행 가능한 단위로 분할한다
2. 의존성 방향: 하위 레이어 → 상위 레이어 (DB → API → UI)
3. Must 우선순위부터 배치한다
4. 하나의 태스크는 1~3일 분량이 적정하다
5. 각 태스크에 적합한 otp 스킬을 판단한다 (아래 스킬 판단 기준 참조)

**스킬 판단 기준**:

| 조건 | 스킬 |
|------|------|
| 코드 변경 10+ 파일, 다중 모듈 | `//otpd` (Full Task) |
| 코드 변경 <10 파일, 단일 모듈 | `//otpds` (Short Task) |
| 와이어프레임 + UI 구현 | `//otpwf` (Wireframe) |

### 3-3. PM 검수

1. roadmap-guide.md의 PM 검수 체크리스트를 1:1 대조한다
2. PRD의 모든 Must 기능이 태스크로 분할되었는지 확인한다
3. 의존성 순서가 올바른지 확인한다 (하위 먼저)
4. 각 태스크의 스킬 판단이 적절한지 확인한다
5. **미달 시**: 자체 재작성 (최대 1회)
6. **통과 시**: 캡틴 검토 요청

### 3-4. 캡틴 확정

```
---
[ROADMAP] PM 검수 통과 — 캡틴 검토 요청

산출물: docs/ROADMAP.md (초안)

{로드맵 요약: 총 태스크 수, 마일스톤, 예상 소요 등}

태스크 목록:
| # | 태스크 | 스킬 | 의존성 | 우선순위 |
|---|--------|------|--------|---------|
| ... | ... | ... | ... | ... |

검토 후 확정 / 피드백을 알려주세요.
---
```

| 캡틴 응답 | 동작 |
|----------|------|
| 확정 / 승인 | 아래 후속 조치 수행 후 Phase 4 진행 |
| 피드백 | 피드백 반영 → PM 재검수 → 캡틴 재검토 |

### 3-5. 캡틴 확정 후 후속 조치 (필수)

**다음 Phase로 넘어가기 전에 반드시 수행한다. 아래 세 가지가 완료되어야만 다음 Phase로 진행할 수 있다.**

1. `docs/PROJECT.md`의 문서 테이블에 ROADMAP.md를 등록한다 (설명, 용도, 참조 시점 포함)
2. `STATE.md`를 갱신한다 (3-ROADMAP → 확정, 로드맵 테이블 채움)
3. `.opal/MEMORY.md`의 작업 히스토리를 갱신한다 (`Phase 3(ROADMAP) ✅ → Phase 4 대기`)

---

## Phase 4: 태스크 순차 실행

로드맵 순서대로 otp 스킬을 호출하여 태스크를 실행한다.

### 4-1. 실행 루프

확정된 `docs/ROADMAP.md`의 태스크 순서대로 진행한다:

```
for each 태스크 in ROADMAP:
  1. 캡틴에게 태스크 시작 보고
  2. 스킬 판단에 따라 otp 호출:
     - //otpd  → Full Task 오케스트레이터
     - //otpds → Short Task 오케스트레이터
     - //otpwf → Wireframe 오케스트레이터
  3. otp 완료 → PM 검수 (완료 산출물 확인)
  4. 캡틴에게 태스크 완료 보고
  5. STATE.md 갱신 (해당 태스크 상태 업데이트)
  6. 다음 태스크로 이동
```

### 4-2. 태스크 시작 보고

```
---
[Phase 4] 태스크 {N}/{M} 시작

태스크: {태스크 제목}
스킬: {//otpd | //otpds | //otpwf}
설명: {태스크 설명}

진행합니다.
---
```

### 4-3. 태스크 완료 보고

```
---
[Phase 4] 태스크 {N}/{M} 완료

태스크: {태스크 제목}
결과: {완료 요약}

남은 태스크: {M-N}개
다음 태스크로 넘어갈까요?
---
```

| 캡틴 응답 | 동작 |
|----------|------|
| 확인 / 다음 | 다음 태스크 시작 |
| 피드백 / 수정 | 현재 태스크 수정 후 재보고 |
| 중단 / 보류 | STATE.md 저장 후 대기 |

### 4-4. 전체 완료 보고

모든 태스크 완료 시:

```
---
opdp 완료

프로젝트: {프로젝트명}

완료 산출물:
- docs/PRD.md (Phase 1)
- docs/TRD.md (Phase 2)
- docs/ROADMAP.md (Phase 3)
- {Phase 4 태스크 목록 및 결과}

전체 {M}개 태스크 완료.
---
```

---

## PM 검수 흐름 (각 Phase 공통)

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
              ├─ 캡틴 피드백 → 반영 → PM 재검수
              └─ 캡틴 확정 → 다음 Phase
```

캡틴은 PM이 통과시킨 결과물만 검토한다. 품질이 낮은 초안이 캡틴에게 올라가지 않는다.

---

## STATE.md 관리

`tasks/{NNN}-opdp-{프로젝트명}/STATE.md`에 관리한다. otp 태스크와 동일한 패턴.

### STATE.md 템플릿

```markdown
# STATE: {프로젝트명} 개발 파일럿

> 최종 갱신: YYYY-MM-DD HH:mm

## 현재 상태
- 스킬: //opdp
- Phase: {1-PRD / 2-TRD / 3-ROADMAP / 4-EXECUTE}
- 상태: {진행 중 / PM 검수 / 캡틴 검토 대기 / 완료}

## Phase 진행 현황
| Phase | 산출물 | 상태 |
|-------|--------|------|
| 1-PRD | docs/PRD.md | {미시작 / 작성 중 / PM 검수 / 캡틴 검토 / 확정} |
| 2-TRD | docs/TRD.md | {미시작 / 작성 중 / PM 검수 / 캡틴 검토 / 확정} |
| 3-ROADMAP | docs/ROADMAP.md | {미시작 / 작성 중 / PM 검수 / 캡틴 검토 / 확정} |
| 4-EXECUTE | - | {미시작 / T{N}/{M} 진행 중 / 완료} |

## 로드맵 (Phase 3 확정 후)
| # | 태스크 | 스킬 | tasks/ 경로 | 상태 |
|---|--------|------|-----------|------|

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|
```

### 갱신 타이밍

| 이벤트 | 갱신 내용 |
|--------|----------|
| Phase 시작 | 현재 Phase + 상태: 진행 중 |
| PM 검수 통과 | 상태: 캡틴 검토 대기 |
| 캡틴 확정 | Phase 상태: 확정, 다음 Phase로 전환 |
| Phase 4 태스크 시작 | 로드맵 테이블: 진행 중 + tasks/ 경로 기재 |
| Phase 4 태스크 완료 | 로드맵 테이블: 완료 |
| 전체 완료 | 4-EXECUTE 상태: 완료 |

## DONE.md 작성

모든 Phase 완료 후 DONE.md를 작성한다.

### DONE.md 템플릿

```markdown
# DONE: {프로젝트명} 개발 파일럿

> 완료일: YYYY-MM-DD | 스킬: //opdp

## 생성 문서

| 문서 | 확정일 |
|------|--------|
| docs/PRD.md | YYYY-MM-DD |
| docs/TRD.md | YYYY-MM-DD |
| docs/ROADMAP.md | YYYY-MM-DD |

## 실행 태스크

| # | 태스크 | 경로 | 스킬 | 결과 |
|---|--------|------|------|------|
| T1 | {제목} | tasks/{NNN}-... | //otpds | 완료 |
| T2 | {제목} | tasks/{NNN}-... | //otpds | 완료 |

## 프로젝트 요약

{전체 개발 과정 요약, 특이사항, 다음 단계}
```

---

## 문서 등록 프로토콜

각 Phase에서 산출물이 확정되면 `docs/PROJECT.md`의 프로젝트 문서 테이블에 등록한다.

| Phase | 산출물 | 등록 설명 |
|-------|--------|----------|
| 1 | `docs/PRD.md` | 제품 요구사항 정의서 |
| 2 | `docs/TRD.md` | 기술 요구사항 정의서 |
| 3 | `docs/ROADMAP.md` | 개발 로드맵 (태스크 분할 및 실행 순서) |

---

## 스킬 탐색 경로

opdp 내에서 참조하는 스킬 탐색:

**opi (사전 조건 미충족 시)**:
1. `{프로젝트}/.opal/skills/opal-project-init/SKILL.md`
2. `~/.opal/skills/opal-project-init/SKILL.md`

**otp (Phase 4 태스크 실행)**:
1. `{프로젝트}/.opal/skills/otp-dev/SKILL.md` (Full Task)
2. `~/.opal/skills/otp-dev/SKILL.md`
3. `{프로젝트}/.opal/skills/otp-dev-short/SKILL.md` (Short Task)
4. `~/.opal/skills/otp-dev-short/SKILL.md`
5. `{프로젝트}/.opal/skills/otp-wf/SKILL.md` (Wireframe)
6. `~/.opal/skills/otp-wf/SKILL.md`

---

## 프로젝트 메모리 동기화

`{프로젝트}/.opal/MEMORY.md`가 존재하면, Phase 전환 시 작업 히스토리를 갱신한다:

- Phase 완료: `단계` 컬럼 → `Phase {N} 확정 → Phase {N+1} 대기`
- 전체 완료: `단계` 컬럼 → `완료`

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-03-26 | 초기 작성 — 4 Phase 파이프라인 (PRD/TRD/ROADMAP/EXECUTE) |
