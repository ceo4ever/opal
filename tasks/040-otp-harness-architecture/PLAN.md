# PLAN: OPAL Harness Architecture -- opal-harness.md 생성 + otp 슬림화

> 작성일: 2026-03-28
> 입력: TASK.md, ANALYSIS.md
> 출력: PLAN.md

## 1. 코드 분석

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `opal/core/references/opal-harness.md` | Harness 공통 참조 문서 (신규) | 신규 생성 |
| `skills/otp-dev/SKILL.md` (264줄) | Full Task 오케스트레이터 | 수정 (슬림화) |
| `skills/otp-dev-short/SKILL.md` (234줄) | Short Task 오케스트레이터 | 수정 (슬림화) |
| `skills/otp-wf/SKILL.md` (188줄) | Wireframe UI 오케스트레이터 | 수정 (슬림화) |
| `skills/otp-write/SKILL.md` (162줄) | 범용 문서 작성 오케스트레이터 | 수정 (슬림화) |
| `skills/otp-write-tech/SKILL.md` (131줄) | 서비스 기획 산출물 네트워크 오케스트레이터 | 수정 (슬림화) |
| `install-mac.sh` | 배포 스크립트 | 수정 (opal-harness.md 배포 추가) |

### 현재 구현

5개 otp의 복제 코드를 정확히 대조 분석한 결과:

**완전 동일 (100% 복제) -- 5개 otp 공통**:
- `구현 금지 원칙` (3줄): 승인 전 코드 작성/파일 생성/수정 금지. 5개 otp 모두 동일 문구
- `Git 사전 점검` (3줄): git status 확인 + 클린/커밋 분기. otp-write-tech는 명시적 섹션 없으나 동일 행동
- `커밋 규칙` (1줄): 사용자 명시 요청 시에만 커밋. 5개 모두 동일
- `프로젝트 메모리 동기화` (2줄): .opal/MEMORY.md 히스토리 갱신. 5개 모두 동일
- `게이트 체크포인트 응답 패턴` (3줄 테이블): 확인/피드백/중단 3단계. 5개 모두 동일 패턴

**구조 동일 + 도메인값만 다름 (85-95% 복제)**:
- `STATE.md 관리` (20-30줄): 템플릿 구조 동일, 모드명/단계명/산출물 목록만 다름
- `STEP 1: TASK` (7줄): dtp-task Read + STATE.md 생성 + 사용자 보고. 도메인별 추가 확인 필드만 다름
- `스킬 탐색 경로` (4줄): 프로젝트 → 글로벌 2단계 탐색. 동일

**도메인별 차이 (남겨야 할 부분)**:
- 파이프라인 정의: 각 otp의 STEP 수/이름/순서가 다름
- 워커 디스패치: model, 스킬, 프롬프트가 각 STEP마다 다름
- 도메인 고유 규칙: 에스컬레이션(short), 입력물 분기(wf), 소스 조사 분기(write), 모드 3가지(write-tech)

### 영향 범위

- **install-mac.sh**: `opal/core/references/` 디렉토리의 파일을 `~/.opal/references/`로 복사하는 기존 로직이 있으므로, opal-harness.md를 해당 디렉토리에 넣으면 자동 배포됨. 배포 로직 확인 필요
- **dtp-* 단계 스킬**: 변경 없음. 하네스는 otp 레이어만 영향
- **에이전트**: 변경 없음
- **opal-doc-standard.md**: 변경 없음. opal-harness.md는 이것과 병렬 참조 문서

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| 1 | `opal/core/references/opal-harness.md` | Harness 공통 참조 문서 (~150줄) |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 2 | `skills/otp-dev/SKILL.md` | 복제 코드 제거 + harness 참조로 교체 (264줄 -> ~100줄) |
| 3 | `skills/otp-dev-short/SKILL.md` | 복제 코드 제거 + harness 참조로 교체 (234줄 -> ~90줄) |
| 4 | `skills/otp-wf/SKILL.md` | 복제 코드 제거 + harness 참조로 교체 (188줄 -> ~80줄) |
| 5 | `skills/otp-write/SKILL.md` | 복제 코드 제거 + harness 참조로 교체 (162줄 -> ~60줄) |
| 6 | `skills/otp-write-tech/SKILL.md` | 복제 코드 제거 + harness 참조로 교체 (131줄 -> ~70줄) |
| 7 | `install-mac.sh` | opal-harness.md 배포 경로 확인/추가 (필요 시) |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | opal-harness.md 신규 생성 | `opal/core/references/opal-harness.md` | 보통 |
| 2 | otp-dev 슬림화 | `skills/otp-dev/SKILL.md` | 보통 |
| 3 | otp-dev-short 슬림화 | `skills/otp-dev-short/SKILL.md` | 쉬움 |
| 4 | otp-wf 슬림화 | `skills/otp-wf/SKILL.md` | 쉬움 |
| 5 | otp-write 슬림화 | `skills/otp-write/SKILL.md` | 쉬움 |
| 6 | otp-write-tech 슬림화 | `skills/otp-write-tech/SKILL.md` | 쉬움 |
| 7 | install-mac.sh 배포 확인 | `install-mac.sh` | 쉬움 |

> **순서 근거**: opal-harness.md가 먼저 완성되어야 5개 otp가 참조할 수 있다. otp-dev를 2순위로 두는 이유는 가장 크고 복잡하여 슬림화 패턴의 기준이 되기 때문. 나머지 otp는 otp-dev 패턴을 따라 적용.

### 핵심 설계

#### opal-harness.md 구조 설계 (~150줄)

```markdown
# OPAL Harness -- 오케스트레이터 공통 인프라

> otp-* 오케스트레이터가 공유하는 프로세스 규칙.
> 각 otp SKILL.md 상단에서 이 문서를 Read하고, 도메인 고유 부분만 직접 정의한다.

## 1. Guards (제약)

### 구현 금지 원칙 (최우선 규칙)
사용자가 명시적으로 "승인", "진행해", "구현해" 등의 실행 허가를 내릴 때까지
코드를 작성하거나 파일을 생성/수정하지 않는다.

- 허용: 산출물 문서(.md) 작성, QA 에이전트 호출, 코드베이스 읽기/분석, 웹 검색
- 금지 (승인 전): 소스 코드 파일 생성/수정, 패키지 설치, DB 스키마 변경, 설정 파일 수정

### Git 사전 점검
태스크 시작 전 `git status`를 확인한다:
- 클린 상태: 진행
- 커밋되지 않은 변경: 사용자에게 커밋/스태시를 제안한 후 진행

### 커밋 규칙
커밋은 사용자가 명시적으로 요청할 때만 수행한다.
EXECUTE 완료, DONE.md 생성, 테스트 통과 후에도 자동으로 커밋하지 않는다.

## 2. Gates (체크포인트)

### 단계 게이트
각 단계 완료 시 사용자에게 보고하고 승인을 받는다.

| 응답 | 동작 |
|------|------|
| "확인", "다음", "승인" | 다음 단계 진행 |
| 피드백/수정 요청 | 현재 단계 수정 후 재보고 |
| "중단", "보류" | 산출물 저장 후 대기 |

### QA Gate
단계 완료 후 dtp-qa 워커를 호출하여 산출물을 검증한다.
- dtp-qa 탐색: {프로젝트}/.opal/skills/dtp-qa/SKILL.md -> ~/.opal/skills/dtp-qa/SKILL.md

### PM Gate
.opal/AGENT.md가 존재하면 PM 검토 기준으로 산출물을 검토한다.
상세: 글로벌 AGENT.md "PM 컨텍스트 로드 > PM 검토 게이트".
AGENT.md 미존재 시 스킵.

## 3. State (상태 관리)

### STATE.md 기본 구조
오케스트레이터 전용. 단계 스킬은 STATE.md를 갱신하지 않는다 (EXECUTE Step 진행 제외).

| 이벤트 | 갱신 주체 | 내용 |
|--------|----------|------|
| TASK 완료 | 오케스트레이터 | STATE.md 초기 생성 |
| 단계 시작 | 오케스트레이터 | 단계, 상태: 진행 중 |
| 단계 완료 | 오케스트레이터 | 완료 산출물 갱신, 상태: 대기 중 |
| EXECUTE Step 완료 | 워커 | 진행: Step N/M 완료 |
| 블로커 | 워커 | 상태: 블로커 + 블로커 섹션 |
| 완료 | 오케스트레이터 | 상태: 완료 |

### STATE.md 공통 템플릿
각 otp는 이 템플릿의 {모드}, {단계 목록}, {산출물 목록}을 도메인에 맞게 치환한다.

{템플릿 본문: 모드/단계/진행/상태 + 완료 산출물 + 의사결정 로그 + 블로커 + 다음 액션}

### 세션 복원
새 세션에서 tasks/{NNN}-{name}/STATE.md가 존재하면 Read하여 정확한 지점에서 재개한다.

## 4. TASK 공통 프로세스

오케스트레이터가 직접 수행한다 (워커 디스패치 없음).

1. dtp-task/SKILL.md를 Read한다
   - 탐색: {프로젝트}/.opal/skills/dtp-task/SKILL.md -> ~/.opal/skills/dtp-task/SKILL.md
2. 스킬 프로세스를 따라 TASK.md를 작성한다
3. STATE.md를 생성한다
4. 사용자에게 보고하고 다음 단계 승인을 받는다

> 도메인별 추가 확인 필드(문서 유형, 출력 모드 등)는 각 otp SKILL.md에서 정의.

## 5. Observability (관측)

### 스킬 탐색 경로
모든 단계 스킬:
1. {프로젝트}/.opal/skills/dtp-{stage}/SKILL.md
2. ~/.opal/skills/dtp-{stage}/SKILL.md

에이전트:
1. {프로젝트}/.opal/agents/{agent-name}/AGENT.md
2. ~/.opal/agents/{agent-name}/AGENT.md

### 프로젝트 메모리 동기화
{프로젝트}/.opal/MEMORY.md가 존재하면, 단계 완료 시 작업 히스토리를 갱신한다:
- 단계 완료: 단계 컬럼 -> {단계} -> {다음} 대기
- DONE.md 생성: 단계 컬럼 -> 완료 (커밋해시)
```

> **설계 포인트**: STATE.md 템플릿은 공통 구조만 정의하고, 각 otp가 도메인 치환값(모드명, 단계 목록, 산출물 목록)을 명시하는 방식. 템플릿 전체를 하네스에 넣되, 치환 필드를 `{모드}`, `{단계 목록}` 형태로 표기.

#### otp-dev 슬림화 설계 (~100줄)

**제거 대상** (harness 참조로 교체):
- `구현 금지 원칙` 섹션 전체 (12-17줄) -> "opal-harness.md Guards 참조"
- `Git 사전 점검` 섹션 전체 (20-25줄) -> "opal-harness.md Guards 참조"
- `커밋 규칙` 섹션 (168-169줄) -> "opal-harness.md Guards 참조"
- `STATE.md 관리` 섹션 전체 (176-218줄, 템플릿 포함) -> "opal-harness.md State 참조" + 도메인 치환값만 기재
- `프로젝트 메모리 동기화` 섹션 (226-231줄) -> "opal-harness.md Observability 참조"
- `스킬 탐색 경로` 섹션 (234-239줄) -> "opal-harness.md Observability 참조"
- `게이트 체크포인트` 섹션 (246-254줄, 응답 패턴 테이블) -> "opal-harness.md Gates 참조"
- `STEP 1: TASK` 섹션 대부분 (39-53줄) -> "opal-harness.md TASK 참조"

**유지 대상** (도메인 고유):
- YAML frontmatter (트리거: otp-dev, otpd)
- Harness 참조 선언 + 모드 지정 (Full: TASK -> ANALYSIS -> PLAN+TEST-SCENARIO -> EXECUTE)
- STEP 1에서 도메인 추가 확인 없음 -> TASK 참조만으로 충분
- STEP 2: ANALYSIS (워커 디스패치 프롬프트, model: haiku, QA+PM Gate)
- STEP 3: PLAN + TEST-SCENARIO (워커 디스패치, model: opus, TEST-SCENARIO 스킵 조건, 연속 디스패치)
- STEP 4: EXECUTE (워커 디스패치, model: sonnet, execution-plan.json 기반 FE/BE 병렬, EXECUTE 완료 후 흐름)
- STATE.md 도메인 치환값 (모드: Full Task, 단계: TASK/ANALYSIS/PLAN+TEST-SCENARIO/EXECUTE, 산출물: TASK.md/ANALYSIS.md/PLAN.md/TEST-SCENARIO.md/QA-*.md/DONE.md)
- 변경이력

**After 구조**:
```markdown
---
name: otp-dev
description: ...
---
# Full Task 오케스트레이터

## Harness
`~/.opal/references/opal-harness.md`를 Read한다.
- 모드: Full Task
- 파이프라인: TASK -> ANALYSIS -> PLAN+TEST-SCENARIO -> EXECUTE

## STEP 1: TASK
opal-harness.md "TASK 공통 프로세스" 참조.

## STEP 2: ANALYSIS (도메인 고유)
{워커 디스패치, model, QA+PM Gate}

## STEP 3: PLAN + TEST-SCENARIO (도메인 고유)
{PLAN 디스패치, TEST-SCENARIO 스킵 조건, 연속 디스패치}

## STEP 4: EXECUTE (도메인 고유)
{워커 디스패치, FE/BE 병렬, EXECUTE 완료 후 흐름}

## STATE.md 도메인 설정
- 모드: Full Task
- 단계: TASK / ANALYSIS / PLAN+TEST-SCENARIO / EXECUTE
- 산출물: TASK.md, ANALYSIS.md, PLAN.md, TEST-SCENARIO.md, QA-*.md, DONE.md

## 변경이력
```

#### otp-dev-short 슬림화 설계 (~90줄)

**제거 대상**: otp-dev와 동일한 복제 섹션 제거. 추가로 `STATE.md 관리`에서 "otp-dev와 동일"이라고 쓴 부분도 harness 참조로 교체.

**유지 대상** (도메인 고유):
- YAML frontmatter (트리거: otp-dev-short, otpds)
- Harness 참조 + 모드: Short Task (TASK -> PLAN+TEST-SCENARIO -> EXECUTE)
- STEP 1: TASK 참조만
- STEP 2: PLAN + TEST-SCENARIO (ANALYSIS.md 미전달 주의문, 워커 디스패치, TEST-SCENARIO 스킵/연속)
- STEP 3: EXECUTE (워커 디스패치, EXECUTE 완료 후 흐름)
- **에스컬레이션 규칙** (Short 전용 -- 반드시 유지)
- STATE.md 도메인 치환값
- 변경이력

#### otp-wf 슬림화 설계 (~80줄)

**제거 대상**: Guards, Gates, State 템플릿 전체, Observability (탐색 경로, 메모리 동기화)

**유지 대상** (도메인 고유):
- YAML frontmatter (트리거: otp-wf, otpwf)
- Harness 참조 + 모드: Wireframe UI (TASK -> WIREFRAME -> EXECUTE)
- **입력물에 따른 분기** (wireframe.md 존재/정책서/이미지/구두 요청)
- STEP 1: TASK (Wireframe 특화 -- 출력 모드: 프로토/프로덕션, 입력물 분류)
- STEP 2: WIREFRAME (워커 디스패치, wireframe.md 존재 시 스킵)
- STEP 3: EXECUTE (UI 구현, ui-designer 모드 분기)
- STATE.md 도메인 치환값
- 변경이력

#### otp-write 슬림화 설계 (~60줄)

**제거 대상**: Guards(구현 금지는 있지만 동일), Gates, State 템플릿, Observability

**유지 대상** (도메인 고유):
- YAML frontmatter (트리거: otp-write, otpw, 문서 작성해줘 등)
- Harness 참조 + 모드: 문서 작성 (TASK -> PLAN -> WRITE)
- 커버 범위 (문서 유형 목록 -- otp-write의 정체성)
- STEP 1: TASK (추가 확인: 문서 유형, 대상 독자, 범위, 출력 형식)
- STEP 2: PLAN (소스 조사 유형별 분기 테이블, opal-doc-standard 참조, QA 선택)
- STEP 3: WRITE (섹션별 순차 작성, 출력 형식 처리)
- STATE.md 도메인 치환값
- 변경이력

#### otp-write-tech 슬림화 설계 (~70줄)

**제거 대상**: STATE.md 기본 구조(이벤트/갱신 테이블은 harness), 게이트 응답 패턴, 메모리 동기화

**유지 대상** (도메인 고유 -- 대부분이 고유):
- YAML frontmatter (트리거: otp-write-tech, otpwt 등)
- Harness 참조 + 모드: {작성/수정/분석} 3가지
- 설계 원칙 (문서가 인터페이스, PM 중심 관리 등)
- 커버 범위 (필수 4종, 선택 4종, 순서 체인)
- 산출물 저장 구조
- 4 Phase 파이프라인 (Phase 1~4 전체 -- 도메인 고유)
- STATE.md 네트워크 확장 (네트워크 상태 + 배치 계획 -- 도메인 고유 필드)
- 게이트 체크포인트 (Phase별 -- 기본 응답 패턴은 harness, Phase별 게이트 정의는 도메인 고유)
- 문서 표준, 참조 가이드
- 변경이력

> **설계 포인트**: otp-write-tech는 복제율이 53%로 가장 낮다. 하네스에서 가져오는 것은 Guards(구현 금지/커밋), Gates 기본 응답 패턴, State 기본 구조, Observability(메모리 동기화) 정도. Phase 파이프라인 자체가 완전히 도메인 고유이므로 슬림화 효과가 상대적으로 작다.

#### install-mac.sh 배포 확인

`opal/core/references/` 디렉토리의 파일은 install-mac.sh가 `~/.opal/references/`로 복사하는 기존 로직이 있다. opal-harness.md를 `opal/core/references/`에 배치하면 자동 배포된다. 배포 로직에 누락이 없는지 확인하고, 필요 시 명시적 복사 라인 추가.

### 의존성 및 환경 변경

- 추가 패키지: 없음
- 환경 설정 변경: 없음
- 기존 opal-doc-standard.md와 병렬 배치. 참조 충돌 없음

### 테스트 전략

이 태스크는 문서 전용 작업이므로 코드 테스트는 없다. 검증은 다음 방법으로 수행:

| 검증 항목 | 방법 |
|-----------|------|
| opal-harness.md 완결성 | 5개 otp의 모든 공통 코드가 하네스에 포함되었는지 대조 |
| otp 슬림화 정확성 | 각 otp에서 도메인 고유 부분만 남았는지 확인 |
| 참조 무결성 | 각 otp의 "harness 참조" 지시가 opal-harness.md의 실제 섹션명과 일치하는지 |
| 하위 호환 | 슬림화된 otp + harness Read 시 기존과 동일한 행동을 재현하는지 시뮬레이션 |
| 배포 경로 | install-mac.sh 실행 후 ~/.opal/references/opal-harness.md 존재 확인 |

## 3. 실행 체크리스트

- [ ] Step 1: opal-harness.md 생성 -- `opal/core/references/opal-harness.md` -- 5개 otp에서 공통 코드 추출하여 Guards/Gates/State/TASK/Observability 5개 섹션 구성 (~150줄)
- [ ] Step 2: otp-dev 슬림화 -- `skills/otp-dev/SKILL.md` -- 복제 코드 제거, "opal-harness.md 참조" 교체, 도메인 고유 STEP만 유지 (264줄 -> ~100줄)
- [ ] Step 3: otp-dev-short 슬림화 -- `skills/otp-dev-short/SKILL.md` -- otp-dev 슬림화 패턴 적용, 에스컬레이션 규칙 유지 (234줄 -> ~90줄)
- [ ] Step 4: otp-wf 슬림화 -- `skills/otp-wf/SKILL.md` -- 입력물 분기 + Wireframe 특화 유지 (188줄 -> ~80줄)
- [ ] Step 5: otp-write 슬림화 -- `skills/otp-write/SKILL.md` -- 커버 범위 + 소스 조사 분기 유지 (162줄 -> ~60줄)
- [ ] Step 6: otp-write-tech 슬림화 -- `skills/otp-write-tech/SKILL.md` -- 4 Phase + 네트워크 확장 유지 (131줄 -> ~70줄)
- [ ] Step 7: install-mac.sh 배포 확인 -- `install-mac.sh` -- opal-harness.md가 ~/.opal/references/에 배포되는지 확인, 필요 시 추가

## 4. QA 체크리스트

### 기능 테스트
- [ ] opal-harness.md가 5개 otp의 공통 코드를 빠짐없이 포함하는가
- [ ] 각 otp 슬림화 후에도 도메인 고유 기능이 완전히 보존되는가
- [ ] otp-dev: ANALYSIS 워커 디스패치, TEST-SCENARIO 스킵 조건, FE/BE 병렬이 유지되는가
- [ ] otp-dev-short: 에스컬레이션 규칙, ANALYSIS.md 미전달 동작이 유지되는가
- [ ] otp-wf: 입력물 분기 4가지, Wireframe 특화 TASK, wireframe.md 존재 시 스킵이 유지되는가
- [ ] otp-write: 소스 조사 유형별 분기, opal-doc-standard 연동이 유지되는가
- [ ] otp-write-tech: 4 Phase 파이프라인, 3가지 모드, diagnosis.json, 네트워크 상태가 유지되는가

### 회귀 테스트
- [ ] 각 otp의 YAML frontmatter(name, description, 트리거)가 변경되지 않았는가
- [ ] 각 otp의 파이프라인 흐름(단계 순서, 워커 모델)이 변경되지 않았는가
- [ ] install-mac.sh 기존 배포 대상이 누락되지 않았는가

### 코드 품질
- [ ] opal-harness.md가 150줄 내외로 유지되는가 (300줄 초과 시 LLM 후반부 무시 리스크)
- [ ] 각 otp 슬림화 후 100줄 이내로 유지되는가
- [ ] harness 참조 지시문이 명확하고 일관된 형식을 사용하는가
- [ ] 전체 줄수 합계가 기존(979줄) 대비 45% 이상 감소하는가

## 5. 기술 컨텍스트

### 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 문서 포맷 | Markdown (SKILL.md, references/) | opal-doc-standard |
| 프레임워크 | OPAL v1.0+ | -- |
| 참조 패턴 | opal-doc-standard.md (검증된 성공 사례) | -- |

### 사용 MCP

해당 없음 (문서 전용 작업)

## 6. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| opal-harness.md가 150줄 초과 | LLM이 후반부 지시를 무시할 수 있음 | 섹션별 우선순위를 두어 Guards > Gates > State 순 배치. 최대 180줄 이내 제한 |
| 슬림화 시 도메인 고유 코드 오삭제 | 기존 동작 깨짐 | 각 otp의 Before/After를 대조 확인 (QA 체크리스트) |
| "harness 참조" 지시를 LLM이 Read 안 함 | 하네스 규칙 미적용 | 각 otp 상단 Harness 섹션에 "`Read` 의무"를 명시. "이 문서를 Read하지 않으면 Guards 위반" |
| install-mac.sh 배포 누락 | 사용자 환경에 opal-harness.md 없음 | Step 7에서 배포 경로 직접 테스트 |
| otp-write-tech의 낮은 슬림화 효과 (53%) | 기대 대비 줄수 감소 적음 | 허용. 도메인 고유 비중이 높은 것은 정상. 무리한 추출 금지 |
